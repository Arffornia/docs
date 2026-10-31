"""Pure helpers shared by sync_board.py and chantiers.py (standard library only, Python 3.9+).

A *chantier* is a parent issue in Arffornia/docs with the label `chantier`. Its body comes from
the issue form `.github/ISSUE_TEMPLATE/chantier.yml`, so every field is a `### Heading` section.
See docs/contributing/operating-model.md.
"""
import re

CHANTIER_LABEL = "chantier"
# Review state of a chantier, set with one label (agents and Brian can set labels over REST).
STATE_LABELS = {
    "chantier: review": "Pending",             # ready, waiting for Brian
    "chantier: approved": "Approved",          # Brian said yes: the orchestrator merges it
    "chantier: changes": "Changes requested",  # back to the agent
}
# Board "Lane" options, in pipeline order. The board is a projection of labels and links.
STAGES = ["Inbox", "Agent queue", "In flight", "Awaiting Brian", "Merging", "Done"]
DECISIONS = ["Drafting", "Pending", "Approved", "Changes requested", "Closed"]
AGENTS = ["Claude Code", "Codex", "OpenCode", "Copilot", "Human"]
RISKS = ["A", "B", "C"]  # A merge on green · B look at one thing · C needs a manual test
# Repos where "delete branch on merge" is off: stacked PRs must have their base branch deleted
# after each merge, so GitHub retargets the next PR to the default branch.
DELETE_BRANCH_REPOS = {"Arffornia/Nexus_Java", "Arffornia/Nexus_Logger", "Arffornia/Nexus_Saver"}

URL_RE = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/(pull|issues)/(\d+)")
CLOSES_RE = re.compile(r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+((?:[\w.-]+/[\w.-]+)?#\d+)")


def sections(body):
    """Split an issue-form body into {heading: text}. Headings are `### Name` lines."""
    out, name, buf = {}, None, []
    for line in (body or "").splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            if name is not None:
                out[name] = "\n".join(buf).strip()
            name, buf = m.group(1), []
        elif name is not None:
            buf.append(line)
    if name is not None:
        out[name] = "\n".join(buf).strip()
    return {k: ("" if v == "_No response_" else v) for k, v in out.items()}


def field(secs, *names):
    """First non-empty section among `names` (case-insensitive prefix match)."""
    for want in names:
        for k, v in secs.items():
            if k.lower().startswith(want.lower()) and v:
                return v
    return ""


def urls(text):
    """Ordered, de-duplicated (repo, kind, number) triples; kind is 'pull' or 'issues'."""
    seen, out = set(), []
    for repo, kind, num in URL_RE.findall(text or ""):
        key = (repo, kind, int(num))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def closes(body, repo):
    """Issues a PR body closes, as 'owner/repo#n' strings (same-repo refs get `repo`)."""
    out = []
    for ref in CLOSES_RE.findall(body or ""):
        r, n = ref.split("#")
        out.append(f"{r or repo}#{n}")
    return out


def parse_chantier(issue):
    """Turn a REST issue dict into the chantier record used by the board and the stack."""
    secs = sections(issue.get("body"))
    labels = [l["name"] if isinstance(l, dict) else l for l in issue.get("labels", [])]
    prs_text = field(secs, "Pull requests")
    prs = [u for u in urls(prs_text) if u[1] == "pull"]
    members = urls(issue.get("body"))
    order_txt = field(secs, "Stack order")
    order = float(order_txt) if re.fullmatch(r"\d+(\.\d+)?", order_txt.strip()) else None
    risk = field(secs, "Risk")[:1].upper()
    agent = field(secs, "Agent")
    decisions = field(secs, "Decisions")
    return {
        "number": issue["number"],
        "title": issue["title"],
        "url": issue["html_url"],
        "node_id": issue.get("node_id"),
        "open": issue.get("state") == "open",
        "created": issue.get("created_at", ""),
        "labels": labels,
        "summary_url": field(secs, "Summary page").split()[0] if field(secs, "Summary page") else "",
        "prs": prs,
        "members": members,
        "order": order,
        "risk": risk if risk in RISKS else "",
        "agent": agent if agent in AGENTS else "",
        "open_decisions": len(re.findall(r"^\s*[-*]\s+\[ \]", decisions, re.M)),
        "decided": len(re.findall(r"^\s*[-*]\s+\[[xX]\]", decisions, re.M)),
        "depends": [int(n) for n in re.findall(r"#(\d+)", field(secs, "Depends on"))],
    }


def decision(chantier):
    if not chantier["open"]:
        return "Closed"
    for label, value in STATE_LABELS.items():
        if label in chantier["labels"]:
            return value
    return "Drafting"


def chantier_stage(chantier):
    return {"Closed": "Done", "Pending": "Awaiting Brian", "Approved": "Merging"}.get(decision(chantier), "In flight")


def item_stage(is_pr, is_open, labels, has_open_pr=False, chantier=None):
    """Lane of a board item. Members of a chantier follow their chantier."""
    if not is_open:
        return "Done"
    if CHANTIER_LABEL in labels:
        return None  # chantiers are staged from their parsed record, see chantier_stage()
    if chantier is not None:
        return chantier_stage(chantier)
    if is_pr or has_open_pr:
        return "In flight"
    if "proposal" in labels or "needs-decision" in labels:
        return "Inbox"
    if "agent-ready" in labels:
        return "Agent queue"
    return "Inbox"


def stack(chantiers):
    """Brian's stack: open chantiers waiting for him, in the order to unstack them."""
    pending = [c for c in chantiers if c["open"] and decision(c) == "Pending"]
    return sorted(pending, key=lambda c: (c["order"] if c["order"] is not None else 1e9, c["created"], c["number"]))


def merge_plan(chantier):
    """Ordered merge steps for an approved chantier. Each step is a dict with the command."""
    steps = []
    prs = chantier["prs"]
    for i, (repo, _, num) in enumerate(prs):
        steps.append({"repo": repo, "number": num, "action": "merge",
                      "cmd": f"gh pr merge https://github.com/{repo}/pull/{num} --merge"})
        nxt = prs[i + 1] if i + 1 < len(prs) else None
        if repo in DELETE_BRANCH_REPOS and nxt and nxt[0] == repo:
            steps.append({"repo": repo, "number": num, "action": "delete-branch",
                          "cmd": f"gh api -X DELETE repos/{repo}/git/refs/heads/<head of #{num}>  # GitHub retargets #{nxt[2]}"})
    return steps

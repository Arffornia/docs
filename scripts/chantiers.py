#!/usr/bin/env python3
"""Brian's stack: the ordered list of chantiers waiting for review, and the merge plan of one.

REST only, so it works from an agent session as well as from Actions (GraphQL is not needed).
Auth: GH_TOKEN / GITHUB_TOKEN if set, otherwise the `gh` CLI.

  python3 scripts/chantiers.py                  # Brian's stack, in unstacking order (Markdown)
  python3 scripts/chantiers.py --all            # every open chantier, grouped by stage
  python3 scripts/chantiers.py --json           # same data as JSON (for pages and agents)
  python3 scripts/chantiers.py --wip            # review load per stage (limits only if WIP_* are set)
  python3 scripts/chantiers.py --merge-plan 12  # dry run: ordered merge steps of chantier #12
  python3 scripts/chantiers.py --merge-plan 12 --execute   # orchestrator only, after approval

`--execute` refuses unless the label `chantier: approved` was added by an approver
(APPROVERS, default TheGostsniperfr). Agents never merge on their own.
"""
import argparse, json, os, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chantier_lib as lib  # noqa: E402

REPO = os.environ.get("CHANTIER_REPO", "Arffornia/docs")
APPROVERS = set(os.environ.get("APPROVERS", "TheGostsniperfr").split(","))
# Soft review load, no hard cap (ADR-0008 amended 2026-10-31). A limit applies only when set.
WIP = {k: int(v) for k, v in (("In flight", os.environ.get("WIP_IN_FLIGHT", "")), ("Awaiting Brian", os.environ.get("WIP_REVIEW", ""))) if v.strip()}
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def api(path, method="GET", body=None):
    if TOKEN:
        req = urllib.request.Request(f"https://api.github.com/{path}", method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
        req.add_header("Authorization", f"Bearer {TOKEN}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    cmd = ["gh", "api", "-X", method, path]
    if body is not None:
        cmd += ["--input", "-"]
    out = subprocess.run(cmd, input=json.dumps(body) if body is not None else None,
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out) if out.strip() else None


def load(fixture=None):
    if fixture:
        with open(fixture) as f:
            issues = json.load(f)
    else:
        issues, page = [], 1
        while True:
            batch = api(f"repos/{REPO}/issues?labels={lib.CHANTIER_LABEL}&state=all&per_page=100&page={page}")
            issues += batch
            if len(batch) < 100:
                break
            page += 1
    out = []
    for it in issues:
        if "pull_request" in it:
            continue
        c = lib.parse_chantier(it)
        if c["open"] and not fixture:  # sub-issues are members too
            try:
                for sub in api(f"repos/{REPO}/issues/{c['number']}/sub_issues?per_page=100") or []:
                    key = (sub["repository_url"].split("/repos/")[1], "issues", sub["number"])
                    if key not in c["members"]:
                        c["members"].append(key)
            except Exception:
                pass
        out.append(c)
    return out


def pr_states(c, offline=False):
    rows = []
    for repo, _, num in c["prs"]:
        if offline:
            rows.append({"url": f"https://github.com/{repo}/pull/{num}", "state": "?"})
            continue
        try:
            p = api(f"repos/{repo}/pulls/{num}")
            state = "merged" if p.get("merged") else ("draft" if p.get("draft") else p["state"])
        except Exception:
            state = "unknown"
        rows.append({"url": f"https://github.com/{repo}/pull/{num}", "state": state})
    return rows


def line(i, c, prs):
    merged = sum(1 for p in prs if p["state"] == "merged")
    bits = [f"risk {c['risk'] or '?'}", f"{len(prs)} PRs" + (f" ({merged} merged)" if merged else ""),
            f"{c['open_decisions']} decisions open" if c["open_decisions"] else "no open decision"]
    page = f" · page: {c['summary_url']}" if c["summary_url"] else " · **no summary page**"
    return f"{i}. [{c['title']}]({c['url']}) — {' · '.join(bits)}{page}"


def wip(chantiers):
    counts = {s: 0 for s in lib.STAGES}
    for c in chantiers:
        counts[lib.chantier_stage(c)] += 1
    return counts


def approved_by(number):
    events = api(f"repos/{REPO}/issues/{number}/events?per_page=100") or []
    who = [e["actor"]["login"] for e in events if e.get("event") == "labeled"
           and e.get("label", {}).get("name") == "chantier: approved" and e.get("actor")]
    return who[-1] if who else None


def execute(c):
    by = approved_by(c["number"])
    if "chantier: approved" not in c["labels"] or by not in APPROVERS:
        sys.exit(f"refusing: #{c['number']} is not approved by {sorted(APPROVERS)} (label added by {by})")
    done = []
    for i, (repo, _, num) in enumerate(c["prs"]):
        p = api(f"repos/{repo}/pulls/{num}")
        if p.get("merged"):
            done.append(p["html_url"]); continue
        default = api(f"repos/{repo}")["default_branch"]
        for _ in range(18):  # wait up to 90 s for GitHub to retarget a stacked PR
            if p["base"]["ref"] == default:
                break
            time.sleep(5); p = api(f"repos/{repo}/pulls/{num}")
        if p["base"]["ref"] != default or p.get("draft") or p["state"] != "open":
            sys.exit(f"stop at {p['html_url']}: base={p['base']['ref']} draft={p.get('draft')} state={p['state']}")
        subprocess.run(["gh", "pr", "merge", p["html_url"], "--merge"], check=True)
        for _ in range(360):  # a merge queue may take a while; wait up to 30 min
            p = api(f"repos/{repo}/pulls/{num}")
            if p.get("merged"):
                break
            time.sleep(5)
        else:
            sys.exit(f"stop: {p['html_url']} did not merge within 30 minutes")
        done.append(p["html_url"])
        nxt = c["prs"][i + 1] if i + 1 < len(c["prs"]) else None
        if repo in lib.DELETE_BRANCH_REPOS and nxt and nxt[0] == repo and p["head"]["repo"]["full_name"] == repo:
            try:
                api(f"repos/{repo}/git/refs/heads/{p['head']['ref']}", method="DELETE")
            except Exception:
                pass  # already deleted
    api(f"repos/{REPO}/issues/{c['number']}/comments", "POST",
        {"body": "Merged in order:\n" + "\n".join(f"{n}. {u}" for n, u in enumerate(done, 1))})
    api(f"repos/{REPO}/issues/{c['number']}", "PATCH", {"state": "closed", "state_reason": "completed"})
    print("\n".join(done))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--wip", action="store_true")
    ap.add_argument("--merge-plan", type=int, metavar="N")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--fixture", help="read issues from a JSON file instead of the API (tests)")
    a = ap.parse_args()
    chantiers = load(a.fixture)
    offline = bool(a.fixture)

    if a.merge_plan:
        c = next((c for c in chantiers if c["number"] == a.merge_plan), None) or sys.exit(f"no chantier #{a.merge_plan}")
        if a.execute:
            return execute(c)
        print(f"# Merge plan for {c['title']} ({c['url']}) — decision: {lib.decision(c)}")
        for n, s in enumerate(lib.merge_plan(c), 1):
            print(f"{n}. {s['cmd']}")
        return
    if a.wip:
        counts = wip(chantiers)
        for s in ("In flight", "Awaiting Brian", "Merging"):
            limit = WIP.get(s)
            flag = "  OVER LIMIT" if limit is not None and counts[s] > limit else ""
            print(f"{s:15} {counts[s]}" + (f" / {limit}{flag}" if limit is not None else ""))
        return
    chosen = [c for c in chantiers if c["open"]] if a.all else lib.stack(chantiers)
    if a.json:
        for c in chosen:
            c["stage"], c["decision"], c["pr_states"] = lib.chantier_stage(c), lib.decision(c), pr_states(c, offline)
            c["members"] = [f"https://github.com/{r}/{k}/{n}" for r, k, n in c["members"]]
            c["prs"] = [f"https://github.com/{r}/pull/{n}" for r, _, n in c["prs"]]
        print(json.dumps(chosen, indent=2))
        return
    if a.all:
        for stage in ("Awaiting Brian", "Merging", "In flight"):
            group = [c for c in chosen if lib.chantier_stage(c) == stage]
            if group:
                print(f"\n## {stage}\n")
                for i, c in enumerate(sorted(group, key=lambda c: (c["order"] or 1e9, c["number"])), 1):
                    print(line(i, c, pr_states(c, offline)))
        return
    print(f"# Brian's stack — {len(chosen)} chantier(s) waiting\n")
    for i, c in enumerate(chosen, 1):
        print(line(i, c, pr_states(c, offline)))
    if not chosen:
        print("Nothing waiting. Agents: label a chantier `chantier: review` when all its PRs are green.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Keep the org board "Arffornia Roadmap" in sync with issues, pull requests and chantiers.

The board is a projection: labels, links and chantier issues are the source of truth, because
agents can set labels over REST from any session, while the board needs GraphQL.

- Creates the project if missing, the single-select fields Area, Priority, Lane, Decision,
  Agent, Risk, the text field Chantier and the number field Order, and the saved views
  (REST, API version 2026-03-10). A view that cannot be created is reported, not fatal.
- Adds open issues of the Arffornia repos (and Arffornia items of the infra repo). PRs are
  added according to BOARD_PRS: `all`, `unlinked` (default: only PRs that close no issue and
  belong to no chantier) or `none`. Bots are skipped.
- Area / Priority / Status are filled only while empty (manual edits win). Lane, Decision,
  Chantier, Order, Agent and Risk are managed: recomputed on every run (see chantier_lib.py).
- Optional cleanup, off by default: ARCHIVE_DONE_DAYS=N archives items closed at least N days
  ago; ARCHIVE_LINKED_PRS=1 archives PR items that close an issue or belong to a chantier.
- Writes the chantier review load to $GITHUB_STEP_SUMMARY; warns only when WIP_IN_FLIGHT /
  WIP_REVIEW are set (no hard cap by default).
- DRY_RUN=1 prints the mutations instead of sending them.

Env: GH_TOKEN (fine-grained token with org Projects read/write). Standard library only.
"""
import datetime, json, os, sys, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chantier_lib as lib  # noqa: E402

ORG = "Arffornia"
TITLE = os.environ.get("BOARD_TITLE", "Arffornia Roadmap")
CHANTIER_REPO = os.environ.get("CHANTIER_REPO", "Arffornia/docs")
EXTRA_REPOS = [("TheGostsniperfr/infra", "arffornia")]  # repo, required substring in title or labels
BOARD_PRS = os.environ.get("BOARD_PRS", "unlinked")
ARCHIVE_DONE_DAYS = int(os.environ.get("ARCHIVE_DONE_DAYS", "0") or 0)
ARCHIVE_LINKED_PRS = os.environ.get("ARCHIVE_LINKED_PRS", "0") == "1"
# Soft review load, no hard cap (ADR-0008 amended 2026-10-31). A limit applies only when set.
WIP = {k: int(v) for k, v in (("In flight", os.environ.get("WIP_IN_FLIGHT", "")), ("Awaiting Brian", os.environ.get("WIP_REVIEW", ""))) if v.strip()}
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
TOKEN = os.environ.get("GH_TOKEN") or sys.exit("GH_TOKEN is not set (org secret ADD_TO_PROJECT_PAT).")
AREAS = ["website", "launcher", "mod", "proxy", "provisioning", "libs", "infra", "ai", "docs"]
PRIORITIES = ["P0", "P1", "P2", "P3"]
REPO_AREA = {"Arffornia_Website": "website", "keycloak-theme-arffornia": "website", "Arffornia_Launcher_V.5.2": "launcher",
             "Arffornia_Mods": "mod", "Arffornia_Proxy": "proxy", "Arffornia_Provisioning": "provisioning",
             "Nexus_Mods": "libs", "Nexus_Java": "libs", "Nexus_Logger": "libs", "Nexus_Saver": "libs",
             "docs": "docs", "infra": "infra", "agent-kit": "ai"}
SELECTS = [("Area", AREAS, "BLUE"), ("Priority", PRIORITIES, "ORANGE"), ("Lane", lib.STAGES, "PURPLE"),
           ("Decision", lib.DECISIONS, "YELLOW"), ("Agent", lib.AGENTS, "GRAY"), ("Risk", lib.RISKS, "RED")]
SCALARS = [("Chantier", "TEXT"), ("Order", "NUMBER")]
# Saved views. Filters use field names in lower case; `no:chantier` hides the members of a chantier
# (only members carry the Chantier field, the chantier issue itself does not).
VIEWS = [
    {"name": "Brian's stack", "layout": "table", "filter": 'label:chantier lane:"Awaiting Brian"',
     "fields": ["Title", "Order", "Risk", "Decision", "Agent", "Area"], "sort": ("Order", "asc")},
    {"name": "Pipeline", "layout": "board", "filter": "no:chantier -lane:Done", "columns": "Lane",
     "fields": ["Title", "Priority", "Area", "Risk"]},
    {"name": "Agent queue", "layout": "table", "filter": 'lane:"Agent queue" no:chantier',
     "fields": ["Title", "Repository", "Priority", "Area", "Labels"], "sort": ("Priority", "asc")},
    {"name": "In flight", "layout": "table", "filter": 'lane:"In flight"', "group": "Repository",
     "fields": ["Title", "Chantier", "Agent", "Priority", "Linked pull requests"]},
    {"name": "Merging", "layout": "table", "filter": "label:chantier lane:Merging",
     "fields": ["Title", "Order", "Risk", "Agent"], "sort": ("Order", "asc")},
    {"name": "Inbox", "layout": "table", "filter": "lane:Inbox", "group": "Area",
     "fields": ["Title", "Repository", "Labels", "Priority"]},
]


def call(url, body=None, method=None, version="2022-11-28"):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", version)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return (json.loads(raw) if raw else None), r.headers
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="ignore")
            if e.code in (502, 503) or (e.code == 403 and "secondary" in text.lower()):
                time.sleep(5 * (attempt + 1)); continue
            raise RuntimeError(f"{e.code} {url}: {text[:300]}") from None
    raise RuntimeError(f"giving up on {url}")


def gql(query, **variables):
    data, _ = call("https://api.github.com/graphql", {"query": query, "variables": variables})
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=1))
    return data["data"]


def mutate(query, **variables):
    if DRY_RUN:
        print("dry-run:", query.split("{")[1].split("(")[0].strip(), {k: v for k, v in variables.items() if k != "p"})
        return None
    return gql(query, **variables)


def rest_pages(path):
    url = f"https://api.github.com/{path}{'&' if '?' in path else '?'}per_page=100"
    while url:
        data, headers = call(url)
        yield from data
        nxt = [p.split(";")[0].strip("<> ") for p in headers.get("Link", "").split(",") if 'rel="next"' in p]
        url = nxt[0] if nxt else None


def ensure_project():
    d = gql("""query($org:String!){ organization(login:$org){ id projectsV2(first:50){ nodes{ id title number url } } } }""", org=ORG)
    org = d["organization"]
    for p in org["projectsV2"]["nodes"]:
        if p["title"] == TITLE:
            return p
    p = gql("""mutation($owner:ID!,$title:String!){ createProjectV2(input:{ownerId:$owner,title:$title}){ projectV2{ id title number url } } }""",
            owner=org["id"], title=TITLE)["createProjectV2"]["projectV2"]
    print(f"created project {p['url']}")
    return p


def fields(pid):
    d = gql("""query($id:ID!){ node(id:$id){ ... on ProjectV2 { fields(first:50){ nodes{
        ... on ProjectV2FieldCommon { id databaseId name dataType }
        ... on ProjectV2SingleSelectField { options { id name } } } } } } }""", id=pid)
    return {f["name"]: f for f in d["node"]["fields"]["nodes"] if f}


def ensure_fields(pid):
    existing, created = fields(pid), False
    for name, options, color in SELECTS:
        if name not in existing:
            opts = [{"name": o, "color": color, "description": ""} for o in options]
            mutate("""mutation($p:ID!,$n:String!,$o:[ProjectV2SingleSelectFieldOptionInput!]){
                createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:$n,singleSelectOptions:$o}){ projectV2Field{ ... on ProjectV2SingleSelectField { id } } } }""",
                   p=pid, n=name, o=opts)
            print(f"created field {name}"); created = True
    for name, dtype in SCALARS:
        if name not in existing:
            mutate("""mutation($p:ID!,$n:String!,$t:ProjectV2CustomFieldType!){
                createProjectV2Field(input:{projectId:$p,dataType:$t,name:$n}){ projectV2Field{ ... on ProjectV2Field { id } } } }""",
                   p=pid, n=name, t=dtype)
            print(f"created field {name}"); created = True
    return fields(pid) if created and not DRY_RUN else existing


def view_body(v, fs):
    ids = [fs[k]["databaseId"] for k in v["fields"] if k in fs and fs[k].get("databaseId")]
    body = {"name": v["name"], "layout": v["layout"], "filter": v["filter"]}
    if ids:
        body["visible_fields"] = ids
    if v.get("sort") and v["sort"][0] in fs:
        body["sort_by"] = [[fs[v["sort"][0]]["databaseId"], v["sort"][1]]]
    if v.get("group") in fs:
        body["group_by"] = [fs[v["group"]]["databaseId"]]
    if v.get("columns") in fs:
        body["vertical_group_by"] = [fs[v["columns"]]["databaseId"]]
    return body


def ensure_views(project, fs):
    """Create missing saved views over REST. Returns the names it could not create."""
    have = gql("""query($id:ID!){ node(id:$id){ ... on ProjectV2 { views(first:50){ nodes{ name } } } } }""", id=project["id"])
    names = {v["name"] for v in have["node"]["views"]["nodes"]}
    failed = []
    for v in VIEWS:
        if v["name"] in names:
            continue
        body = view_body(v, fs)
        if DRY_RUN:
            print("dry-run: create view", body); continue
        try:
            call(f"https://api.github.com/orgs/{ORG}/projectsV2/{project['number']}/views", body, "POST", version="2026-03-10")
            print(f"created view {v['name']}")
        except Exception as e:  # views are a convenience: never fail the sync for them
            print(f"::warning::could not create view {v['name']!r} ({e}); create it by hand, see docs/contributing/operating-model.md")
            failed.append(v["name"])
    return failed


ITEMS_Q = """query($id:ID!,$c:String){ node(id:$id){ ... on ProjectV2 { items(first:100, after:$c){
    pageInfo{ hasNextPage endCursor }
    nodes{ id isArchived
      content{ ... on Issue{ id url state closedAt } ... on PullRequest{ id url state closedAt } }
      fieldValues(first:30){ nodes{
        ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
        ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
        ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } } } } } } } } }"""


def current_items(pid):
    items, cursor = {}, None
    while True:
        d = gql(ITEMS_Q, id=pid, c=cursor)["node"]["items"]
        for n in d["nodes"]:
            if n["content"] and not n["isArchived"]:
                vals = {}
                for v in n["fieldValues"]["nodes"]:
                    if v and v.get("field"):
                        vals[v["field"]["name"]] = v.get("name", v.get("text", v.get("number")))
                items[n["content"]["id"]] = {"item": n["id"], "vals": vals, **n["content"]}
        if not d["pageInfo"]["hasNextPage"]:
            return items
        cursor = d["pageInfo"]["endCursor"]


def option_id(field, name):
    return next((o["id"] for o in field.get("options", []) if o["name"].lower() == (name or "").lower()), None)


def set_value(pid, item, field, value):
    """Set a single-select (by option name), text or number value. None or "" clears it."""
    if value in (None, ""):
        mutate("""mutation($p:ID!,$i:ID!,$f:ID!){ clearProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f}){ projectV2Item{ id } } }""",
               p=pid, i=item, f=field["id"])
        return True
    if field.get("dataType") == "TEXT":
        v = {"text": str(value)}
    elif field.get("dataType") == "NUMBER":
        v = {"number": float(value)}
    else:
        oid = option_id(field, value)
        if not oid:
            return False
        v = {"singleSelectOptionId": oid}
    mutate("""mutation($p:ID!,$i:ID!,$f:ID!,$v:ProjectV2FieldValue!){ updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:$v}){ projectV2Item{ id } } }""",
           p=pid, i=item, f=field["id"], v=v)
    return True


def same(a, b):
    if a in (None, "") and b in (None, ""):
        return True
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        try:
            return float(a) == float(b)
        except (TypeError, ValueError):
            return False
    return str(a).lower() == str(b).lower()


def open_items():
    repos = [(r["full_name"], None) for r in rest_pages(f"orgs/{ORG}/repos?type=public") if not r["archived"] and not r["fork"]]
    for full, needle in repos + EXTRA_REPOS:
        for it in rest_pages(f"repos/{full}/issues?state=open"):
            labels = [l["name"] for l in it["labels"]]
            if needle and needle not in (it["title"] + " " + " ".join(labels)).lower():
                continue
            if it["user"]["login"].endswith("[bot]"):
                continue
            yield full, it, labels


def load_chantiers():
    out = []
    for it in rest_pages(f"repos/{CHANTIER_REPO}/issues?labels={lib.CHANTIER_LABEL}&state=all"):
        if "pull_request" in it:
            continue
        c = lib.parse_chantier(it)
        if c["open"]:
            try:
                for sub in rest_pages(f"repos/{CHANTIER_REPO}/issues/{c['number']}/sub_issues"):
                    key = (sub["repository_url"].split("/repos/")[1], "issues", sub["number"])
                    if key not in c["members"]:
                        c["members"].append(key)
            except Exception as e:
                print(f"::warning::sub-issues of chantier #{c['number']}: {e}")
        out.append(c)
    return out


def wanted(full, it, labels, chantiers, by_url, closed_by_pr):
    """Managed field values for one open item."""
    url, is_pr = it["html_url"], "pull_request" in it
    if lib.CHANTIER_LABEL in labels and full == CHANTIER_REPO:
        c = next((c for c in chantiers if c["url"] == url), None) or lib.parse_chantier(it)
        return {"Lane": lib.chantier_stage(c), "Decision": lib.decision(c), "Agent": c["agent"] or None,
                "Risk": c["risk"] or None, "Order": c["order"], "Chantier": None}
    chantier = by_url.get(url)
    stage = lib.item_stage(is_pr, True, labels, has_open_pr=f"{full}#{it['number']}" in closed_by_pr, chantier=chantier)
    return {"Lane": stage, "Chantier": f"#{chantier['number']} {chantier['title']}" if chantier else None}


def main():
    project = ensure_project()
    pid = project["id"]
    fs = ensure_fields(pid)
    failed_views = ensure_views(project, fs)
    status_f = fs.get("Status")
    have = current_items(pid)

    chantiers = load_chantiers()
    by_url = {}  # member URL -> chantier
    for c in chantiers:
        if c["open"]:
            for repo, kind, num in c["members"]:
                by_url.setdefault(f"https://github.com/{repo}/{kind}/{num}", c)

    open_list = list(open_items())
    closed_by_pr = set()
    for full, it, _ in open_list:
        if "pull_request" in it:
            closed_by_pr.update(lib.closes(it.get("body"), full))

    added = updated = archived = 0
    seen = set()
    for full, it, labels in open_list:
        repo = full.split("/")[1]
        node, is_pr = it["node_id"], "pull_request" in it
        linked = is_pr and (it["html_url"] in by_url or bool(lib.closes(it.get("body"), full)))
        if node in have:
            item, vals = have[node]["item"], have[node]["vals"]
        else:
            if is_pr and (BOARD_PRS == "none" or (BOARD_PRS == "unlinked" and linked)):
                continue
            res = mutate("""mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p,contentId:$c}){ item{ id } } }""", p=pid, c=node)
            added += 1
            if res is None:  # dry run
                continue
            item, vals = res["addProjectV2ItemById"]["item"]["id"], {}
        seen.add(node)
        if ARCHIVE_LINKED_PRS and linked:
            mutate("""mutation($p:ID!,$i:ID!){ archiveProjectV2Item(input:{projectId:$p,itemId:$i}){ item{ id } } }""", p=pid, i=item)
            archived += 1
            continue
        area = next((l.split(":", 1)[1].strip() for l in labels if l.startswith("area:")), REPO_AREA.get(repo))
        prio = next((l.split(":", 1)[1].strip() for l in labels if l.startswith("priority:")), None)
        status = "In Progress" if is_pr else "Todo"
        for name, value in (("Area", area), ("Priority", prio)):
            if fs.get(name) and value and not vals.get(name):
                updated += set_value(pid, item, fs[name], value)
        if status_f and not vals.get("Status"):
            updated += set_value(pid, item, status_f, status)
        for name, value in wanted(full, it, labels, chantiers, by_url, closed_by_pr).items():
            if fs.get(name) and not same(vals.get(name), value):
                updated += set_value(pid, item, fs[name], value)
        if not DRY_RUN:
            time.sleep(0.1)

    # Items on the board that are no longer open: Lane Done, archived after ARCHIVE_DONE_DAYS.
    now = datetime.datetime.now(datetime.timezone.utc)
    for node, h in have.items():
        if node in seen or h.get("state") == "OPEN":
            continue
        if fs.get("Lane") and not same(h["vals"].get("Lane"), "Done"):
            updated += set_value(pid, h["item"], fs["Lane"], "Done")
        closed = h.get("closedAt")
        if ARCHIVE_DONE_DAYS and closed:
            age = now - datetime.datetime.fromisoformat(closed.replace("Z", "+00:00"))
            if age.days >= ARCHIVE_DONE_DAYS:
                mutate("""mutation($p:ID!,$i:ID!){ archiveProjectV2Item(input:{projectId:$p,itemId:$i}){ item{ id } } }""", p=pid, i=h["item"])
                archived += 1

    counts = {s: 0 for s in lib.STAGES}
    for c in chantiers:
        counts[lib.chantier_stage(c)] += 1
    report = [f"## {TITLE}", "", f"{project['url']}: {added} added, {updated} field values set, {archived} archived.", "",
              "| Chantier lane | Count | Limit (optional) |", "|---|---|---|"]
    for s in ("In flight", "Awaiting Brian", "Merging"):
        lim = WIP.get(s)
        over = lim is not None and counts[s] > lim
        report.append(f"| {s} | {counts[s]} | {'' if lim is None else lim}{' **over**' if over else ''} |")
        if over:
            print(f"::warning::{counts[s]} chantiers in {s!r}, WIP limit {lim}")
    if failed_views:
        report += ["", "Views to create by hand: " + ", ".join(failed_views)]
    print("\n".join(report))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()

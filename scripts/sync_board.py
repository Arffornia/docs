#!/usr/bin/env python3
"""Keep the org board "Arffornia Roadmap" in sync with every open issue and pull request.

- Creates the project if it does not exist, plus the single-select fields Area and Priority.
- Adds every open issue and PR of the Arffornia repos (and Arffornia items of the infra repo).
- Fills Area / Priority from the `area: *` / `priority: P*` labels and Status (Todo for
  issues, In Progress for PRs) only when the field is still empty, so manual edits win.

Env: GH_TOKEN (fine-grained token with org Projects read/write). Standard library only.
"""
import json, os, sys, time, urllib.request, urllib.error

ORG = "Arffornia"
TITLE = os.environ.get("BOARD_TITLE", "Arffornia Roadmap")
EXTRA_REPOS = [("TheGostsniperfr/infra", "arffornia")]  # repo, required substring in title or labels
TOKEN = os.environ.get("GH_TOKEN") or sys.exit("GH_TOKEN is not set (org secret ADD_TO_PROJECT_PAT).")
AREAS = ["website", "launcher", "mod", "proxy", "provisioning", "libs", "infra", "ai", "docs"]
PRIORITIES = ["P0", "P1", "P2", "P3"]
REPO_AREA = {"Arffornia_Website": "website", "keycloak-theme-arffornia": "website", "Arffornia_Launcher_V.5.2": "launcher",
             "Arffornia_Mods": "mod", "Arffornia_Proxy": "proxy", "Arffornia_Provisioning": "provisioning",
             "Nexus_Mods": "libs", "Nexus_Java": "libs", "Nexus_Logger": "libs", "Nexus_Saver": "libs",
             "docs": "docs", "infra": "infra"}


def call(url, body=None, method=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r), r.headers
        except urllib.error.HTTPError as e:
            if e.code in (502, 503) or (e.code == 403 and "secondary" in e.read().decode(errors="ignore").lower()):
                time.sleep(5 * (attempt + 1)); continue
            raise
    raise RuntimeError(f"giving up on {url}")


def gql(query, **variables):
    data, _ = call("https://api.github.com/graphql", {"query": query, "variables": variables})
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=1))
    return data["data"]


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
        ... on ProjectV2FieldCommon { id name }
        ... on ProjectV2SingleSelectField { id name options { id name } } } } } } }""", id=pid)
    return {f["name"]: f for f in d["node"]["fields"]["nodes"] if f}


def ensure_select(pid, existing, name, options, color):
    if name in existing:
        return existing[name]
    opts = [{"name": o, "color": color, "description": ""} for o in options]
    gql("""mutation($p:ID!,$n:String!,$o:[ProjectV2SingleSelectFieldOptionInput!]){
        createProjectV2Field(input:{projectId:$p,dataType:SINGLE_SELECT,name:$n,singleSelectOptions:$o}){ projectV2Field{ ... on ProjectV2SingleSelectField { id } } } }""",
        p=pid, n=name, o=opts)
    print(f"created field {name}")
    return fields(pid)[name]


def current_items(pid):
    items, cursor = {}, None
    while True:
        d = gql("""query($id:ID!,$c:String){ node(id:$id){ ... on ProjectV2 { items(first:100, after:$c){
            pageInfo{ hasNextPage endCursor }
            nodes{ id content{ ... on Issue{ id } ... on PullRequest{ id } }
                   fieldValues(first:20){ nodes{ ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } } } } } } } } }""",
                id=pid, c=cursor)["node"]["items"]
        for n in d["nodes"]:
            if n["content"]:
                vals = {v["field"]["name"]: v["name"] for v in n["fieldValues"]["nodes"] if v and v.get("field")}
                items[n["content"]["id"]] = (n["id"], vals)
        if not d["pageInfo"]["hasNextPage"]:
            return items
        cursor = d["pageInfo"]["endCursor"]


def option_id(field, name):
    return next((o["id"] for o in field.get("options", []) if o["name"].lower() == (name or "").lower()), None)


def set_value(pid, item, field, name):
    oid = option_id(field, name)
    if not oid:
        return False
    gql("""mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){ updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){ projectV2Item{ id } } }""",
        p=pid, i=item, f=field["id"], o=oid)
    return True


def open_items():
    repos = [(r["full_name"], None) for r in rest_pages(f"orgs/{ORG}/repos?type=public") if not r["archived"] and not r["fork"]]
    for full, needle in repos + EXTRA_REPOS:
        for it in rest_pages(f"repos/{full}/issues?state=open"):
            labels = [l["name"] for l in it["labels"]]
            if needle and needle not in (it["title"] + " " + " ".join(labels)).lower():
                continue
            if it["user"]["login"].endswith("[bot]"):
                continue
            yield full.split("/")[1], it, labels


def main():
    project = ensure_project()
    pid = project["id"]
    fs = fields(pid)
    area_f = ensure_select(pid, fs, "Area", AREAS, "BLUE")
    prio_f = ensure_select(pid, fs, "Priority", PRIORITIES, "ORANGE")
    status_f = fields(pid).get("Status")
    have = current_items(pid)
    added = updated = 0
    for repo, it, labels in open_items():
        node = it["node_id"]
        if node in have:
            item, vals = have[node]
        else:
            item = gql("""mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p,contentId:$c}){ item{ id } } }""", p=pid, c=node)["addProjectV2ItemById"]["item"]["id"]
            vals = {}
            added += 1
        area = next((l.split(":", 1)[1].strip() for l in labels if l.startswith("area:")), REPO_AREA.get(repo))
        prio = next((l.split(":", 1)[1].strip() for l in labels if l.startswith("priority:")), None)
        status = "In Progress" if "pull_request" in it else "Todo"
        for field, value, name in ((area_f, area, "Area"), (prio_f, prio, "Priority"), (status_f, status, "Status")):
            if field and value and not vals.get(name):
                updated += set_value(pid, item, field, value)
        time.sleep(0.1)
    print(f"{project['url']}: {added} added, {updated} field values set, {len(have) + added} items on the board")


if __name__ == "__main__":
    main()

"""Offline test of sync_board.main() against a fake GitHub (GraphQL + REST)."""
import contextlib, importlib, io, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GH_TOKEN", "test")

CHANTIER_BODY = """### Summary page

https://claude.ai/artifact/EXAMPLE

### Pull requests in merge order

1. https://github.com/Arffornia/Nexus_Java/pull/7

### Risk

A — merge on green

### Agent

Codex

### Stack order

1
"""


def issue(repo, n, labels, body="", pr=False, user="TheGostsniperfr"):
    kind = "pull" if pr else "issues"
    it = {"number": n, "title": f"{repo} {n}", "html_url": f"https://github.com/{repo}/{kind}/{n}", "node_id": f"{repo}#{n}",
          "state": "open", "labels": [{"name": l} for l in labels], "body": body, "user": {"login": user},
          "created_at": "2026-10-29T00:00:00Z"}
    if pr:
        it["pull_request"] = {}
    return it


class FakeGitHub:
    def __init__(self):
        self.mutations, self.rest_posts = [], []
        self.field_names = ["Title", "Status", "Repository", "Labels"]
        self.items = [  # already on the board: an open issue and a merged PR
            {"id": "item-old-issue", "isArchived": False, "content": {"id": "Arffornia/Nexus_Java#4", "url": "u", "state": "OPEN", "closedAt": None},
             "fieldValues": {"nodes": []}},
            {"id": "item-merged", "isArchived": False, "content": {"id": "gone", "url": "u2", "state": "MERGED", "closedAt": "2026-01-01T00:00:00Z"},
             "fieldValues": {"nodes": []}},
        ]
        self.repo_issues = {
            "Arffornia/docs": [issue("Arffornia/docs", 9, ["chantier", "chantier: review"], CHANTIER_BODY)],
            "Arffornia/Nexus_Java": [issue("Arffornia/Nexus_Java", 4, ["agent-ready", "priority: P2", "area: libs"]),
                                     issue("Arffornia/Nexus_Java", 7, [], "Closes #4", pr=True),
                                     issue("Arffornia/Nexus_Java", 12, ["agent-ready"]),
                                     issue("Arffornia/Nexus_Java", 13, [], "no link", pr=True),
                                     issue("Arffornia/Nexus_Java", 14, [], "", pr=True, user="dependabot[bot]")],
            "TheGostsniperfr/infra": [issue("TheGostsniperfr/infra", 1, [], "")],
        }

    def fields(self):
        out = []
        for i, n in enumerate(self.field_names):
            f = {"id": f"F_{n}", "databaseId": 100 + i, "name": n, "dataType": "SINGLE_SELECT" if n in ("Status",) else "TEXT"}
            if n in ("Area", "Priority", "Lane", "Decision", "Agent", "Risk", "Status"):
                f["dataType"] = "SINGLE_SELECT"
                f["options"] = [{"id": f"O_{n}_{o}", "name": o} for o in self.options[n]]
            if n == "Order":
                f["dataType"] = "NUMBER"
            out.append(f)
        return out

    options = {"Status": ["Todo", "In Progress", "Done"]}

    def __call__(self, url, body=None, method=None, version="2022-11-28"):
        if url.endswith("/graphql"):
            q, v = body["query"], body["variables"]
            if "organization(login" in q:
                return {"data": {"organization": {"id": "ORG", "projectsV2": {"nodes": [
                    {"id": "P", "title": "Arffornia Roadmap", "number": 3, "url": "https://github.com/orgs/Arffornia/projects/3"}]}}}}, {}
            if "createProjectV2Field" in q:
                self.field_names.append(v["n"])
                if "o" in v:
                    self.options[v["n"]] = [o["name"] for o in v["o"]]
                return {"data": {}}, {}
            if "fields(first" in q:
                return {"data": {"node": {"fields": {"nodes": self.fields()}}}}, {}
            if "views(first" in q:
                return {"data": {"node": {"views": {"nodes": [{"name": "View 1"}]}}}}, {}
            if "items(first" in q:
                return {"data": {"node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": self.items}}}}, {}
            if q.strip().startswith("mutation"):
                self.mutations.append((q.split("{")[1].split("(")[0].strip(), v))
                if "addProjectV2ItemById" in q:
                    return {"data": {"addProjectV2ItemById": {"item": {"id": "item-" + v["c"]}}}}, {}
                return {"data": {}}, {}
            raise AssertionError(q)
        path = url.split("api.github.com/")[1]
        if method == "POST":
            self.rest_posts.append((path, body, version))
            return {}, {}
        if path.startswith("orgs/Arffornia/repos"):
            return [{"full_name": r, "archived": False, "fork": False} for r in self.repo_issues if r.startswith("Arffornia/")], {}
        if "/sub_issues" in path:
            return [], {}
        if "labels=chantier" in path:
            return self.repo_issues["Arffornia/docs"], {}
        repo = "/".join(path.split("/")[1:3])
        return self.repo_issues.get(repo, []), {}


class SyncBoard(unittest.TestCase):
    def run_sync(self, **env):
        for k, v in env.items():
            os.environ[k] = v
        try:
            sb = importlib.reload(importlib.import_module("sync_board"))
            fake = FakeGitHub()
            sb.call = fake
            sb.time.sleep = lambda s: None
            with contextlib.redirect_stdout(io.StringIO()):
                sb.main()
            return fake
        finally:
            for k in env:
                del os.environ[k]

    def values(self, fake, item):
        return [(v["f"], v["v"]) for m, v in fake.mutations if m == "updateProjectV2ItemFieldValue" and v["i"] == item]

    def test_fields_views_and_stages(self):
        fake = self.run_sync()
        for name in ("Lane", "Decision", "Agent", "Risk", "Chantier", "Order"):
            self.assertIn(name, fake.field_names)
        views = [b["name"] for p, b, ver in fake.rest_posts if p.endswith("/views")]
        self.assertEqual(views, ["Brian's stack", "Pipeline", "Agent queue", "In flight", "Merging", "Inbox"])
        self.assertTrue(all(ver == "2026-03-10" for _, _, ver in fake.rest_posts))
        added = [v["c"] for m, v in fake.mutations if m == "addProjectV2ItemById"]
        # linked PR #7 (closes #4, member of the chantier) and the bot PR stay off the board
        self.assertEqual(sorted(added), ["Arffornia/Nexus_Java#12", "Arffornia/Nexus_Java#13", "Arffornia/docs#9"])
        chantier = dict(self.values(fake, "item-Arffornia/docs#9"))
        self.assertEqual(chantier["F_Lane"], {"singleSelectOptionId": "O_Lane_Awaiting Brian"})
        self.assertEqual(chantier["F_Order"], {"number": 1.0})
        self.assertEqual(chantier["F_Risk"], {"singleSelectOptionId": "O_Risk_A"})
        self.assertEqual(dict(self.values(fake, "item-old-issue"))["F_Lane"], {"singleSelectOptionId": "O_Lane_In flight"})
        self.assertEqual(dict(self.values(fake, "item-Arffornia/Nexus_Java#12"))["F_Lane"], {"singleSelectOptionId": "O_Lane_Agent queue"})
        self.assertEqual(dict(self.values(fake, "item-merged"))["F_Lane"], {"singleSelectOptionId": "O_Lane_Done"})
        self.assertFalse([m for m, _ in fake.mutations if m == "archiveProjectV2Item"])

    def test_archiving_is_opt_in(self):
        fake = self.run_sync(ARCHIVE_DONE_DAYS="14")
        self.assertEqual([v["i"] for m, v in fake.mutations if m == "archiveProjectV2Item"], ["item-merged"])

    def test_dry_run_sends_no_mutation(self):
        fake = self.run_sync(DRY_RUN="1")
        self.assertEqual(fake.mutations, [])
        self.assertEqual(fake.rest_posts, [])


if __name__ == "__main__":
    unittest.main()

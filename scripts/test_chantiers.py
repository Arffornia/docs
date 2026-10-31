"""Offline tests for chantier_lib and chantiers.py: python3 -m unittest discover -s scripts"""
import json, os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chantier_lib as lib  # noqa: E402

BODY = """### Summary page

https://claude.ai/artifact/EXAMPLE

### What this chantier delivers

Nexus libraries: foundation, hardening, npm publish.

### Pull requests in merge order

1. https://github.com/Arffornia/Nexus_Java/pull/7 — foundation
2. https://github.com/Arffornia/Nexus_Java/pull/10
3. https://github.com/Arffornia/Nexus_Mods/pull/20

### Issues it closes

https://github.com/Arffornia/Nexus_Java/issues/4

### Decisions for Brian

- [ ] D1 · Add the NPM_TOKEN secret now? — default: yes
- [x] D2 · Keep 3 previous logs — default: yes

### Verified / not verified

make check on each repo.

### Risk

B — look at one thing

### Agent

Claude Code

### Stack order

2

### Depends on chantiers

#3
"""


def issue(number, labels, body=BODY, state="open", created="2026-10-29T10:00:00Z"):
    return {"number": number, "title": f"Chantier {number}", "html_url": f"https://github.com/Arffornia/docs/issues/{number}",
            "state": state, "created_at": created, "labels": [{"name": l} for l in labels], "body": body, "node_id": f"I_{number}"}


class Parse(unittest.TestCase):
    def test_sections_and_fields(self):
        c = lib.parse_chantier(issue(5, ["chantier", "chantier: review"]))
        self.assertEqual(c["summary_url"], "https://claude.ai/artifact/EXAMPLE")
        self.assertEqual([p[2] for p in c["prs"]], [7, 10, 20])
        self.assertEqual(c["order"], 2.0)
        self.assertEqual(c["risk"], "B")
        self.assertEqual(c["agent"], "Claude Code")
        self.assertEqual((c["open_decisions"], c["decided"]), (1, 1))
        self.assertEqual(c["depends"], [3])
        self.assertIn(("Arffornia/Nexus_Java", "issues", 4), c["members"])

    def test_no_response_is_empty(self):
        c = lib.parse_chantier(issue(6, ["chantier"], body="### Summary page\n\n_No response_\n\n### Risk\n\n_No response_"))
        self.assertEqual((c["summary_url"], c["risk"], c["order"]), ("", "", None))

    def test_closes(self):
        self.assertEqual(lib.closes("Closes #4, fixes Arffornia/Nexus_Mods#12", "Arffornia/Nexus_Java"),
                         ["Arffornia/Nexus_Java#4", "Arffornia/Nexus_Mods#12"])


class Stages(unittest.TestCase):
    def test_chantier_states(self):
        self.assertEqual(lib.chantier_stage(lib.parse_chantier(issue(1, ["chantier"]))), "In flight")
        self.assertEqual(lib.chantier_stage(lib.parse_chantier(issue(1, ["chantier", "chantier: review"]))), "Awaiting Brian")
        self.assertEqual(lib.chantier_stage(lib.parse_chantier(issue(1, ["chantier", "chantier: approved"]))), "Merging")
        self.assertEqual(lib.chantier_stage(lib.parse_chantier(issue(1, ["chantier"], state="closed"))), "Done")

    def test_items(self):
        self.assertEqual(lib.item_stage(False, True, ["agent-ready"]), "Agent queue")
        self.assertEqual(lib.item_stage(False, True, ["agent-ready"], has_open_pr=True), "In flight")
        self.assertEqual(lib.item_stage(False, True, ["needs-decision"]), "Inbox")
        self.assertEqual(lib.item_stage(True, True, []), "In flight")
        self.assertEqual(lib.item_stage(True, False, []), "Done")
        ch = lib.parse_chantier(issue(1, ["chantier", "chantier: review"]))
        self.assertEqual(lib.item_stage(True, True, [], chantier=ch), "Awaiting Brian")

    def test_stack_order(self):
        a = lib.parse_chantier(issue(1, ["chantier", "chantier: review"], body="### Stack order\n\n3"))
        b = lib.parse_chantier(issue(2, ["chantier", "chantier: review"], body="### Stack order\n\n1"))
        c = lib.parse_chantier(issue(3, ["chantier", "chantier: review"], body=""))
        d = lib.parse_chantier(issue(4, ["chantier"], body="### Stack order\n\n0"))
        self.assertEqual([x["number"] for x in lib.stack([a, b, c, d])], [2, 1, 3])


class MergePlan(unittest.TestCase):
    def test_nexus_branch_deletion_between_stacked_merges(self):
        steps = lib.merge_plan(lib.parse_chantier(issue(5, ["chantier", "chantier: approved"])))
        self.assertEqual([s["action"] for s in steps], ["merge", "delete-branch", "merge", "merge"])
        self.assertTrue(all("--merge" in s["cmd"] for s in steps if s["action"] == "merge"))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([issue(5, ["chantier", "chantier: review"]), issue(8, ["chantier"])], f)
        try:
            env = dict(os.environ, GH_TOKEN="unused")
            return subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "chantiers.py"), "--fixture", f.name, *args],
                                  capture_output=True, text=True, check=True, env=env).stdout
        finally:
            os.unlink(f.name)

    def test_stack(self):
        out = self.run_cli()
        self.assertIn("1 chantier(s) waiting", out)
        self.assertIn("https://claude.ai/artifact/EXAMPLE", out)

    def test_wip_and_plan(self):
        out = self.run_cli("--wip")
        self.assertIn("Awaiting Brian  1", out)
        self.assertNotIn("/ 5", out)   # no hard cap by default
        self.assertIn("gh pr merge https://github.com/Arffornia/Nexus_Java/pull/7 --merge", self.run_cli("--merge-plan", "5"))


if __name__ == "__main__":
    unittest.main()

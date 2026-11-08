import copy
import json
import pathlib
import unittest

import progression

SPEC = pathlib.Path(__file__).resolve().parent.parent / "docs" / "specs" / "017-progression-model"
CURRENT_TREE = SPEC / "current-tree-2026-07-31.json"

try:
    import jsonschema
except ImportError:  # CI installs it from requirements.txt; the stdlib-only tests still run without it.
    jsonschema = None


def converted():
    backup = json.loads(CURRENT_TREE.read_text(encoding="utf-8"))
    return progression.convert(backup, source=CURRENT_TREE.name)


def codes(findings, code):
    return [f for f in findings if f.code == code]


class ConvertCurrentTreeTest(unittest.TestCase):
    def setUp(self):
        self.model, self.findings = converted()

    def test_keeps_every_stage_graph_and_milestone(self):
        self.assertEqual((11, 12, 194), (len(self.model["stages"]), len(self.model["graphs"]), len(self.model["milestones"])))

    def test_drops_and_reports_the_dangling_links(self):
        self.assertEqual(43, len(codes(self.findings, "dangling_link")))

    def test_gives_every_milestone_a_unique_key(self):
        keys = [m["key"] for m in self.model["milestones"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_infers_the_mod_id_from_unlocked_items(self):
        mod_ids = {g["key"]: g["mod_id"] for g in self.model["graphs"]}
        self.assertEqual("mekanism", mod_ids["mekanism"])

    def test_milestones_with_requirements_are_validated_by_delivery(self):
        delivered = [m for m in self.model["milestones"] if m["validation"] and m["validation"]["type"] == "deliver"]
        self.assertEqual(28, len(delivered))


class LintTest(unittest.TestCase):
    def setUp(self):
        self.model, _ = converted()

    def test_reports_the_five_milestones_that_require_a_later_stage(self):
        self.assertEqual(5, len(codes(progression.lint(self.model), "requires_later_stage")))

    def test_reports_the_cross_graph_link_as_info(self):
        found = codes(progression.lint(self.model), "cross_graph")
        self.assertEqual(["info"], [f.severity for f in found])

    def test_detects_a_cycle(self):
        model = copy.deepcopy(self.model)
        first, second = model["milestones"][0], model["milestones"][1]
        second["stage"] = first["stage"]
        first["requires"] = [second["key"]]
        second["requires"] = [first["key"]]

        self.assertTrue(codes(progression.lint(model), "cycle"))

    def test_detects_an_unknown_requirement(self):
        model = copy.deepcopy(self.model)
        model["milestones"][0]["requires"] = ["nowhere/ghost"]

        self.assertTrue(codes(progression.lint(model), "unknown_requirement"))


@unittest.skipIf(jsonschema is None, "jsonschema not installed")
class SchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema = json.loads((SPEC / "progression-model.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        cls.validator = jsonschema.Draft202012Validator(schema)
        cls.model, _ = converted()

    def test_the_converted_current_tree_is_valid(self):
        self.assertEqual([], [e.message for e in self.validator.iter_errors(self.model)])

    def test_rejects_a_milestone_without_key(self):
        model = copy.deepcopy(self.model)
        del model["milestones"][0]["key"]

        self.assertFalse(self.validator.is_valid(model))

    def test_rejects_a_threshold_above_one(self):
        model = copy.deepcopy(self.model)
        model["stages"][0]["threshold"] = 1.5

        self.assertFalse(self.validator.is_valid(model))

    def test_rejects_an_unknown_validation_type(self):
        model = copy.deepcopy(self.model)
        model["milestones"][0]["validation"] = {"type": "pray", "items": ["minecraft:dirt"]}

        self.assertFalse(self.validator.is_valid(model))


if __name__ == "__main__":
    unittest.main()

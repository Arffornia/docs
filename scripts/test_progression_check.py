import json
import unittest

import progression_check as pc
from test_recipe_graph import CRAFTER, PRODUCT, graph, milestone


def full_model(*milestones, stages=3, threshold=0.8):
    return {
        "schema_version": 1, "version": 0, "status": "draft", "source": "fixture",
        "stages": [{"number": n, "threshold": threshold} for n in range(1, stages + 1)],
        "graphs": [{"key": k} for k in sorted({m["graph"] for m in milestones})],
        "milestones": [{**m, "description": {"en": "fixture"}} for m in milestones],
    }


def codes(doc, key):
    return [f["code"] for f in doc["milestones"][key]["findings"]]


class LintOnlyTest(unittest.TestCase):
    def test_marks_every_milestone_of_a_cycle_as_error(self):
        # Arrange
        m = full_model(milestone("m/a", 1, requires=["m/b"], deliver=["mod:ore"]),
                       milestone("m/b", 1, requires=["m/a"], deliver=["mod:ore"]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertEqual(("error", "error"), (doc["milestones"]["m/a"]["badge"], doc["milestones"]["m/b"]["badge"]))

    def test_skips_completability_when_the_requires_graph_has_a_cycle(self):
        # Arrange
        m = full_model(milestone("m/a", 1, requires=["m/b"]), milestone("m/b", 1, requires=["m/a"]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertEqual("skipped: cycle in the requires graph", doc["completability"])

    def test_gives_an_ok_badge_to_a_milestone_without_findings(self):
        # Arrange
        m = full_model(milestone("m/a", 1, deliver=["mod:ore"]))

        # Act
        doc = pc.build(m, None)

        # Assert
        self.assertEqual({"badge": "ok", "graph": "m", "stage": 1, "findings": []}, doc["milestones"]["m/a"])


class CompletabilityTest(unittest.TestCase):
    def test_a_delivery_that_needs_a_machine_gated_later_is_not_completable(self):
        # Arrange
        m = full_model(milestone("m/machine", 2, unlocks=[("mod:machine", ["mod:ore"], [])], deliver=["mod:ore"]),
                       milestone("m/use", 1, deliver=["mod:product"]))

        # Act
        doc = pc.build(m, graph([CRAFTER, PRODUCT]))

        # Assert
        self.assertIn("not_completable", codes(doc, "m/use"))

    def test_proposes_moving_the_milestone_to_the_stage_of_the_machine(self):
        # Arrange
        m = full_model(milestone("m/machine", 2, unlocks=[("mod:machine", ["mod:ore"], [])], deliver=["mod:ore"]),
                       milestone("m/use", 1, deliver=["mod:product"]))

        # Act
        found = next(f for f in pc.build(m, graph([CRAFTER, PRODUCT]))["milestones"]["m/use"]["findings"]
                     if f["code"] == "not_completable")

        # Assert
        self.assertEqual([{"action": "move_stage", "milestone": "m/use", "stage": 2}], found["fixes"])

    def test_a_backward_link_carries_its_structured_fix(self):
        # Arrange
        m = full_model(milestone("m/early", 1, requires=["m/late"], unlocks=[("mod:gear", ["mod:ore"], [])]),
                       milestone("m/late", 2, unlocks=[("mod:product", ["mod:gear"], [])]))

        # Act
        found = next(f for f in pc.build(m, graph([CRAFTER]))["milestones"]["m/early"]["findings"]
                     if f["code"] == "requires_later_stage")

        # Assert
        self.assertEqual([{"action": "reverse_requires", "milestone": "m/early", "requires": "m/late"}], found["fixes"])

    def test_a_sibling_dependency_is_a_warning_with_the_link_to_add(self):
        # Arrange
        m = full_model(milestone("m/gears", 1, unlocks=[("mod:gear", ["mod:ore"], [])], deliver=["mod:ore"]),
                       milestone("m/use", 1, deliver=["mod:gear"]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertEqual(("warning", [{"action": "add_requires", "milestone": "m/use", "requires": ["m/gears"],
                                       "verified": True}]),
                         (doc["milestones"]["m/use"]["badge"], doc["milestones"]["m/use"]["findings"][0]["fixes"]))

    def test_a_delivery_of_its_own_unlock_has_its_own_code(self):
        # Arrange
        m = full_model(milestone("m/a", 1, deliver=["mod:gear"], unlocks=[("mod:gear", ["mod:ore"], [])]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertEqual(["delivers_own_unlock"], codes(doc, "m/a"))

    def test_a_leak_proposes_banning_the_recipe_that_still_makes_the_item(self):
        # Arrange
        g = graph([CRAFTER, ("minecraft:crafting", ["mod:ore"], ["mod:gear"], "gear"),
                   ("minecraft:crafting", ["mod:ingot"], ["mod:gear"], "gear_alt")])
        m = full_model(milestone("m/a", 1, unlocks=[("mod:gear", ["mod:ore"], ["gear"])]))

        # Act
        leak = next(f for f in pc.build(m, g)["milestones"]["m/a"]["findings"] if f["code"] == "leak")

        # Assert
        self.assertEqual([{"action": "ban_recipe", "milestone": "m/a", "item": "mod:gear", "recipe": "gear_alt"}],
                         leak["fixes"])

    def test_an_unlock_that_needs_itself_is_never_craftable(self):
        # Arrange
        m = full_model(milestone("m/a", 1, unlocks=[("mod:gear", ["mod:gear"], [])]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertIn("never_craftable", codes(doc, "m/a"))

    def test_a_ban_of_a_recipe_missing_from_the_dump_is_a_warning(self):
        # Arrange
        m = full_model(milestone("m/a", 1, unlocks=[("mod:gear", ["mod:ore"], ["no_such_recipe"])]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertIn("unknown_ban", codes(doc, "m/a"))

    def test_a_stray_ban_next_to_a_real_one_is_only_info(self):
        # Arrange
        g = graph([CRAFTER, ("minecraft:crafting", ["mod:ore"], ["mod:gear"], "gear")])
        m = full_model(milestone("m/a", 1, unlocks=[("mod:gear", ["mod:ore"], ["gear", "mod:gear"])]))

        # Act
        ban = next(f for f in pc.build(m, g)["milestones"]["m/a"]["findings"] if f["code"] == "unknown_ban")

        # Assert
        self.assertEqual("info", ban["severity"])

    def test_an_item_missing_from_the_dump_is_an_error(self):
        # Arrange
        m = full_model(milestone("m/a", 1, deliver=["othermod:thing"]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertIn("unknown_item", codes(doc, "m/a"))

    def test_a_stage_below_its_threshold_is_an_error(self):
        # Arrange
        m = full_model(milestone("m/machine", 2, unlocks=[("mod:machine", ["mod:ore"], [])], deliver=["mod:ore"]),
                       milestone("m/use", 1, deliver=["mod:product"]))

        # Act
        doc = pc.build(m, graph([CRAFTER, PRODUCT]))

        # Assert
        self.assertEqual(["threshold_unreachable"], [f["code"] for f in doc["stages"]["1"]["findings"]])


    def test_a_milestone_with_nothing_to_deliver_counts_against_the_threshold(self):
        # Arrange
        m = full_model(milestone("m/a", 1, unlocks=[("mod:gear", ["mod:ore"], [])]))

        # Act
        doc = pc.build(m, graph([CRAFTER]))

        # Assert
        self.assertEqual(["threshold_unreachable"], [f["code"] for f in doc["stages"]["1"]["findings"]])

    def test_an_unlock_gated_later_is_a_warning_with_a_move_fix(self):
        # Arrange
        m = full_model(milestone("m/machine", 2, unlocks=[("mod:machine", ["mod:ore"], [])], deliver=["mod:ore"]),
                       milestone("m/use", 1, unlocks=[("mod:product", ["mod:machine"], [])], deliver=["mod:ore"]))

        # Act
        found = next(f for f in pc.build(m, graph([CRAFTER]))["milestones"]["m/use"]["findings"]
                     if f["code"] == "unlock_unusable")

        # Assert
        self.assertEqual(("warning", [{"action": "move_stage", "milestone": "m/use", "stage": 2}]),
                         (found["severity"], found["fixes"]))


class OutputTest(unittest.TestCase):
    def test_the_same_input_gives_the_same_bytes(self):
        # Arrange
        m = full_model(milestone("m/gears", 1, unlocks=[("mod:gear", ["mod:ore"], [])]),
                       milestone("m/use", 1, unlocks=[("mod:product", ["mod:gear"], [])]))

        # Act
        first, second = (json.dumps(pc.build(m, graph([CRAFTER]))) for _ in range(2))

        # Assert
        self.assertEqual(first, second)

    def test_declares_its_format(self):
        self.assertEqual(pc.FORMAT, pc.build(full_model(milestone("m/a", 1)), None)["format"])


if __name__ == "__main__":
    unittest.main()

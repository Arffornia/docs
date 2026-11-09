import json
import pathlib
import tempfile
import unittest

import recipe_graph as rg


PACK_ITEMS = ("mod:ore", "mod:ingot", "mod:machine", "mod:product", "mod:seed", "mod:fruit", "mod:crystal", "mod:gem",
              "mod:gear", "mod:controller", "mod:board")


def graph(recipes, machines=None, tags=None):
    """recipes: (type, [input ids], [output ids], recipe id). machines: type -> machine item id."""
    machines = machines or {}
    entries, index, alts, types, rows = [], {}, [], [], []

    def entry(id_):
        if id_ not in index:
            index[id_] = len(entries)
            entries.append([id_, rg.ITEM])
        return index[id_]

    def alt(ids):
        alts.append([entry(i) for i in ids])
        return len(alts) - 1

    for item in PACK_ITEMS:
        entry(item)
    type_idx = {}
    for rtype, inputs, outputs, rid in recipes:
        if rtype not in type_idx:
            type_idx[rtype] = len(types)
            types.append([rtype, [entry(machines[rtype])] if rtype in machines else [], "table"])
        rows.append([type_idx[rtype], [[alt(i if isinstance(i, list) else [i]), 1, rg.ITEM] for i in inputs],
                     [[alt([o]), 1, rg.ITEM] for o in outputs], rid])
    return {"entries": entries, "alts": alts, "types": types, "recipes": rows, "tags": tags or {}}


def milestone(key, stage, unlocks=(), requires=(), deliver=()):
    return {
        "key": key, "graph": key.split("/")[0], "stage": stage, "requires": list(requires),
        "validation": {"type": "deliver", "items": [{"item": i, "count": 1} for i in deliver]} if deliver else None,
        "unlocks": [{"item": item, "recipes_to_ban": list(ban),
                     "recipe": {"type": "arffornia:x", "ingredients": [{"item": i, "count": 1} for i in ingredients],
                                "result": [{"item": item, "count": 1}]}}
                    for item, ingredients, ban in unlocks],
    }


def model(*milestones):
    return {"milestones": list(milestones)}


CRAFTER = ("minecraft:crafting", ["mod:plank"], [rg.CRAFTER], "arffornia:crafter_block")


def statuses(report):
    return {m["key"]: m["status"] for m in report["milestones"]}


class ReachTest(unittest.TestCase):
    def test_items_without_a_recipe_are_world_resources(self):
        # Arrange
        pack = rg.Pack(graph([("minecraft:crafting", ["mod:log"], ["mod:plank"], "plank")]), model())

        # Act
        avail = pack.reach(frozenset())

        # Assert
        self.assertTrue(avail[pack.index[(rg.ITEM, "mod:plank")]])

    def test_a_machine_recipe_needs_its_machine(self):
        # Arrange
        g = graph([("mod:press", ["mod:ore"], ["mod:plate"], "plate"),
                   ("minecraft:crafting", ["mod:plate"], ["mod:press_block"], "press")],
                  machines={"mod:press": "mod:press_block"})
        pack = rg.Pack(g, model())

        # Act
        avail = pack.reach(frozenset())

        # Assert
        self.assertFalse(avail[pack.index[(rg.ITEM, "mod:plate")]])

    def test_a_gated_item_is_craftable_only_once_its_milestone_is_done(self):
        # Arrange
        g = graph([CRAFTER, ("minecraft:crafting", ["mod:ore"], ["mod:gear"], "gear")])
        pack = rg.Pack(g, model(milestone("m/gears", 1, unlocks=[("mod:gear", ["mod:ore"], ["gear"])])))
        gear = pack.index[(rg.ITEM, "mod:gear")]

        # Act
        before, after = pack.reach(frozenset()), pack.reach(frozenset({"m/gears"}))

        # Assert
        self.assertEqual((0, 1), (before[gear], after[gear]))


class CheckTest(unittest.TestCase):
    def test_reports_a_milestone_whose_unlock_needs_a_later_stage(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/machine", 2, unlocks=[("mod:machine", ["mod:ore"], [])]),
                  milestone("m/use", 1, unlocks=[("mod:product", ["mod:machine"], [])]))

        # Act
        report = rg.check(g, m)

        # Assert
        self.assertEqual("unreachable", statuses(report)["m/use"])

    def test_names_the_missing_item_and_the_milestone_that_unlocks_it(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/machine", 2, unlocks=[("mod:machine", ["mod:ore"], [])]),
                  milestone("m/use", 1, unlocks=[("mod:product", ["mod:machine"], [])]))

        # Act
        use = next(r for r in rg.check(g, m)["milestones"] if r["key"] == "m/use")

        # Assert
        self.assertEqual([{"item": "mod:machine", "reason": "gated", "unlocked_by": ["m/machine"]}],
                         use["blockers"]["mod:product"])

    def test_proposes_a_link_when_only_a_non_prerequisite_makes_it_completable(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/machine", 1, unlocks=[("mod:machine", ["mod:ore"], [])]),
                  milestone("m/use", 2, unlocks=[("mod:product", ["mod:machine"], [])]))

        # Act
        use = next(r for r in rg.check(g, m)["milestones"] if r["key"] == "m/use")

        # Assert
        self.assertEqual(("needs_link", ["m/machine"]), (use["status"], use["proposed_links"]))

    def test_a_delivery_must_be_reachable_before_the_milestone_is_done(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/self", 1, unlocks=[("mod:gem", ["mod:ore"], [])], deliver=["mod:gem"]))

        # Act
        report = rg.check(g, m)

        # Assert
        self.assertEqual("unreachable", statuses(report)["m/self"])

    def test_reverses_a_backward_link_when_the_later_milestone_needs_the_earlier_one(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/tier", 1, unlocks=[("mod:seed", ["mod:ore"], [])], requires=["m/late"]),
                  milestone("m/late", 2, unlocks=[("mod:fruit", ["mod:seed"], [])]))

        # Act
        backward = rg.check(g, m)["backward_links"]

        # Assert
        self.assertEqual("reverse it: `m/late` requires `m/tier`", backward[0]["fix"])

    def test_moves_the_prerequisite_down_when_the_earlier_milestone_needs_it(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/tier", 1, unlocks=[("mod:seed", ["mod:crystal"], [])], requires=["m/crystal"]),
                  milestone("m/crystal", 2, unlocks=[("mod:crystal", ["mod:ore"], [])]))

        # Act
        backward = rg.check(g, m)["backward_links"]

        # Assert
        self.assertEqual("move `m/crystal` to stage 1", backward[0]["fix"])

    def test_reports_a_gated_item_that_an_unbanned_recipe_still_makes(self):
        # Arrange
        g = graph([CRAFTER, ("minecraft:crafting", ["mod:ore"], ["mod:gear"], "gear"),
                   ("minecraft:crafting", ["mod:ingot"], ["mod:gear"], "gear_alt")])
        m = model(milestone("m/gears", 1, unlocks=[("mod:gear", ["mod:ore"], ["gear"])]))

        # Act
        leaks = rg.check(g, m)["leaks"]

        # Assert
        self.assertEqual([{"item": "mod:gear", "recipe": "gear_alt"}], leaks)

    def test_reports_an_unlock_whose_recipe_needs_itself(self):
        # Arrange
        g = graph([CRAFTER, ("minecraft:crafting", ["mod:controller"], ["mod:board"], "board")])
        m = model(milestone("m/line", 1, unlocks=[("mod:controller", ["mod:board"], [])]))

        # Act
        never = rg.check(g, m)["never_craftable"]

        # Assert
        self.assertEqual([{"item": "mod:controller", "unlocked_by": ["m/line"]}], never)


class ReviewRegressionTest(unittest.TestCase):
    def test_a_delivery_of_an_item_missing_from_the_pack_is_reported_not_raised(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/a", 1, unlocks=[("mod:gem", ["mod:ore"], [])]),
                  milestone("m/b", 2, unlocks=[("mod:fruit", ["mod:ore"], [])], deliver=["mod:not_there"]))

        # Act
        b = next(r for r in rg.check(g, m)["milestones"] if r["key"] == "m/b")

        # Assert
        self.assertEqual("not in the pack", b["blockers"]["mod:not_there"][0]["reason"])

    def test_never_proposes_a_link_to_a_descendant(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/a", 2, unlocks=[("mod:gem", ["mod:seed"], [])]),
                  milestone("m/b", 2, unlocks=[("mod:seed", ["mod:ore"], [])], requires=["m/a"]))

        # Act
        a = next(r for r in rg.check(g, m)["milestones"] if r["key"] == "m/a")

        # Assert
        self.assertEqual("unreachable", a["status"])

    def test_proposes_the_milestone_behind_an_alternate_route(self):
        # Arrange
        g = graph([CRAFTER, ("minecraft:crafting", ["mod:crystal"], ["mod:gear"], "gear_from_crystal")])
        m = model(milestone("m/z", 5, unlocks=[("mod:gear", ["mod:ore"], [])]),
                  milestone("m/b", 1, unlocks=[("mod:crystal", ["mod:ore"], [])]),
                  milestone("m/a", 2, unlocks=[("mod:product", ["mod:gear"], [])]))

        # Act
        a = next(r for r in rg.check(g, m)["milestones"] if r["key"] == "m/a")

        # Assert
        self.assertEqual((["m/b"], True), (a["proposed_links"], a["links_verified"]))

    def test_reverses_a_backward_link_even_when_the_later_milestone_stays_blocked(self):
        # Arrange
        g = graph([CRAFTER])
        m = model(milestone("m/tier", 1, unlocks=[("mod:seed", ["mod:ore"], [])], requires=["m/late"]),
                  milestone("m/late", 2, unlocks=[("mod:fruit", ["mod:seed", "mod:gem"], [])]),
                  milestone("m/gem", 3, unlocks=[("mod:gem", ["mod:ore"], [])]))

        # Act
        backward = rg.check(g, m)["backward_links"]

        # Assert
        self.assertEqual("reverse it: `m/late` requires `m/tier`", backward[0]["fix"])


class CompactTest(unittest.TestCase):
    def dump(self, recipes, items):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = pathlib.Path(temporary.name)
        (directory / "tags.json").write_text(json.dumps({"c:ingots/iron": ["minecraft:iron_ingot"]}))
        (directory / "items.jsonl").write_text("\n".join(json.dumps({"id": i, "mod": i.split(":")[0]}) for i in items))
        (directory / "recipes.jsonl").write_text("\n".join(json.dumps(r) for r in recipes))
        return directory

    def test_reads_machine_inputs_from_the_recipe_json(self):
        # Arrange
        recipe = {"id": "mekanism:enriching/x", "type": "mekanism:enriching", "serializer": "mekanism:enriching",
                  "ingredients": [], "json": {"input": {"tag": "c:ingots/iron", "count": 1},
                                              "output": {"id": "mod:dust", "count": 2}}}
        directory = self.dump([recipe], ["minecraft:iron_ingot", "mod:dust", "mekanism:enrichment_chamber"])

        # Act
        g = rg.compact(directory)

        # Assert
        ids = [e[0] for e in g["entries"]]
        _, inputs, outputs, _ = g["recipes"][0]
        self.assertEqual((["minecraft:iron_ingot"], ["mod:dust"], ["mekanism:enrichment_chamber"]),
                         ([ids[i] for i in g["alts"][inputs[0][0]]], [ids[i] for i in g["alts"][outputs[0][0]]],
                          [ids[i] for i in g["types"][0][1]]))

    def test_a_two_by_two_crafting_recipe_needs_no_crafting_table(self):
        # Arrange
        recipe = {"id": "mod:plank", "type": "minecraft:crafting", "serializer": "minecraft:crafting_shaped",
                  "ingredients": [["mod:log"]], "result": {"item": "mod:plank", "count": 4},
                  "json": {"pattern": ["#"]}}
        directory = self.dump([recipe], ["mod:log", "mod:plank", "minecraft:crafting_table"])

        # Act
        g = rg.compact(directory)

        # Assert
        self.assertEqual([rg.INVENTORY, []], g["types"][0][:2])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Recipe graph and milestone completability (spec 017, initiative #28). Stdlib only.

  python3 scripts/recipe_graph.py compact <dump-dir> -o graph.json
  python3 scripts/recipe_graph.py check <graph.json> <model.json> [--json out.json] [--markdown out.md]

`compact` reads the output of `/arffornia dump recipes` (recipes.jsonl, items.jsonl, tags.json)
and keeps, per recipe, its input slots (item, fluid or chemical alternatives), its outputs and the
machine that runs it. `check` replays a progression model (progression.py convert) on that graph:
for every milestone it computes what a player can make with the milestones done before it, and
reports what blocks it. The rules are in docs/specs/017-progression-model/completability.md.
Exit code 1 when a milestone is unreachable.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field, asdict

ITEM, FLUID, CHEMICAL = 0, 1, 2
CRAFTER = "arffornia:crafter_block"
INVENTORY = "minecraft:crafting_2x2"

# Recipe type -> the machine a player needs. None: no machine (hand, in-world, any tank).
# Types missing here fall back to a name match and are listed as "guessed" in the report.
MACHINES: dict[str, str | tuple[str, ...] | None] = {
    "minecraft:crafting": "minecraft:crafting_table", INVENTORY: None, "minecraft:smelting": "minecraft:furnace",
    "minecraft:blasting": "minecraft:blast_furnace", "minecraft:smoking": "minecraft:smoker",
    "minecraft:campfire_cooking": "minecraft:campfire", "minecraft:stonecutting": "minecraft:stonecutter",
    "minecraft:smithing": "minecraft:smithing_table",
    "mekanism:enriching": "mekanism:enrichment_chamber", "mekanism:crushing": "mekanism:crusher",
    "mekanism:injecting": "mekanism:chemical_injection_chamber", "mekanism:painting": "mekanism:painting_machine",
    "mekanism:sawing": "mekanism:precision_sawmill", "mekanism:pigment_extracting": "mekanism:pigment_extractor",
    "mekanism:combining": "mekanism:combiner", "mekanism:purifying": "mekanism:purification_chamber",
    "mekanism:compressing": "mekanism:osmium_compressor", "mekanism:metallurgic_infusing": "mekanism:metallurgic_infuser",
    "mekanism:oxidizing": "mekanism:chemical_oxidizer", "mekanism:dissolution": "mekanism:chemical_dissolution_chamber",
    "mekanism:chemical_infusing": "mekanism:chemical_infuser", "mekanism:separating": "mekanism:electrolytic_separator",
    "mekanism:reaction": "mekanism:pressurized_reaction_chamber", "mekanism:crystallizing": "mekanism:chemical_crystallizer",
    "mekanism:washing": "mekanism:chemical_washer", "mekanism:centrifuging": "mekanism:isotopic_centrifuge",
    "mekanism:activating": "mekanism:solar_neutron_activator", "mekanism:rotary": "mekanism:rotary_condensentrator",
    "mekanism:evaporating": "mekanism:thermal_evaporation_controller",
    "mekanism:nucleosynthesizing": "mekanism:antiprotonic_nucleosynthesizer", "mekanism:pigment_mixing": "mekanism:pigment_mixer",
    "mekanism:chemical_conversion": None,
    "create:cutting": "create:mechanical_saw", "create:milling": "create:millstone", "create:crushing": "create:crushing_wheel",
    "create:mixing": "create:mechanical_mixer", "create:pressing": "create:mechanical_press",
    "create:compacting": "create:mechanical_press", "create:deploying": "create:deployer", "create:filling": "create:spout",
    "create:emptying": "create:item_drain", "create:sandpaper_polishing": "create:sand_paper",
    "create:splashing": "create:encased_fan", "create:haunting": "create:encased_fan",
    "create:mechanical_crafting": "create:mechanical_crafter", "create:sequenced_assembly": "create:deployer",
    "create:item_application": None,
    "ae2:inscriber": "ae2:inscriber", "ae2:charger": "ae2:charger", "ae2:transform": None,
    "ae2:entropy": "ae2:entropy_manipulator", "ae2:matter_cannon": "ae2:matter_cannon",
    "enderio:alloy_smelting": ("enderio:alloy_smelter", "enderio:primitive_alloy_smelter"), "enderio:sag_milling": "enderio:sag_mill",
    "enderio:slicing": "enderio:slice_and_splice", "enderio:soul_binding": "enderio:soul_binder",
    "enderio:painting": "enderio:painting_machine", "enderio:vat_fermenting": "enderio:vat",
    "enderio:enchanting": "enderio:enchanter", "enderio:tank": "enderio:fluid_tank",
    "farmersdelight:cooking": "farmersdelight:cooking_pot", "farmersdelight:cutting": "farmersdelight:cutting_board",
    "integrateddynamics:squeezer": "integrateddynamics:squeezer",
    "integrateddynamics:mechanical_squeezer": "integrateddynamics:mechanical_squeezer",
    "industrialforegoing:fluid_extractor": "industrialforegoing:fluid_extractor",
    "industrialforegoing:laser_drill_ore": "industrialforegoing:ore_laser_base",
    "industrialforegoing:laser_drill_fluid": "industrialforegoing:fluid_laser_base",
    "industrialforegoing:crusher": None,
    "mysticalagriculture:infusion": "mysticalagriculture:infusion_altar",
    "mysticalagriculture:awakening": "mysticalagriculture:awakening_altar",
    "pneumaticcraft:pressure_chamber": "pneumaticcraft:pressure_chamber_valve",
    "pneumaticcraft:thermo_plant": "pneumaticcraft:thermopneumatic_processing_plant",
    "pneumaticcraft:explosion_crafting": None,
    "powah:energizing": "powah:energizing_orb",
    "immersiveengineering:metal_press": "immersiveengineering:metal_press",
    "immersiveengineering:blast_furnace": "immersiveengineering:blast_furnace",
    "evilcraft:blood_infuser": "evilcraft:blood_infuser",
    "apothic_enchanting:infusion": "minecraft:enchanting_table",
    "ars_nouveau:crush": None, "ars_nouveau:glyph": "ars_nouveau:scribes_table",
    "ars_nouveau:enchanting_apparatus": "ars_nouveau:enchanting_apparatus",
    "framedblocks:frame": "framedblocks:framing_saw",
    "occultism:crushing": None, "occultism:miner": "occultism:dimensional_mineshaft",
    "occultism:ritual": "occultism:golden_sacrificial_bowl",
    "railcraft:crushing": "railcraft:crusher",
    "mob_grinding_utils:solidify": "mob_grinding_utils:xpsolidifier",
    "occultism:spirit_fire": None, "occultism:spirit_trade": None, "stellaris:rocket_station": None,
    "cataclysm:weapon_fusion": "cataclysm:mechanical_fusion_anvil",
    "statues:loot_recipe": None, "null": None,
}

# Items that exist in the world (mined, grown, dropped) even when a recipe also makes them.
WORLD_TAGS = (
    "c:ores", "c:raw_materials", "minecraft:logs", "minecraft:leaves", "minecraft:saplings", "minecraft:flowers",
    "c:crops", "c:seeds", "c:mushrooms", "c:stones", "c:cobblestones", "c:sands", "c:gravels", "c:obsidians",
    "c:netherracks", "c:end_stones", "c:eggs", "c:strings", "c:bones", "c:feathers", "c:gunpowders",
    "c:ender_pearls", "c:rods/blaze", "minecraft:wool",
)
WORLD_ITEMS = (
    "minecraft:diamond", "minecraft:emerald", "minecraft:lapis_lazuli", "minecraft:redstone", "minecraft:coal",
    "minecraft:quartz", "minecraft:amethyst_shard", "minecraft:glowstone_dust", "minecraft:flint",
    "minecraft:clay_ball", "minecraft:leather", "minecraft:honeycomb", "minecraft:ink_sac", "minecraft:ghast_tear",
    "minecraft:slime_ball", "minecraft:nether_wart", "minecraft:prismarine_shard", "minecraft:prismarine_crystals",
    "minecraft:dirt", "minecraft:clay", "minecraft:ice", "minecraft:snowball", "minecraft:sugar_cane",
    "minecraft:bamboo", "minecraft:kelp", "minecraft:cactus", "minecraft:vine", "minecraft:ancient_debris",
    "minecraft:copper_ingot", "minecraft:iron_nugget", "minecraft:gold_nugget", "minecraft:rotten_flesh",
    "minecraft:spider_eye", "minecraft:magma_cream", "minecraft:shulker_shell", "minecraft:nether_star",
    "minecraft:dragon_breath", "minecraft:echo_shard", "minecraft:water_bucket", "minecraft:lava_bucket",
    "minecraft:milk_bucket", "minecraft:powder_snow_bucket",
    "ae2:sky_stone_block", "ae2:silicon_press", "ae2:logic_processor_press", "ae2:calculation_processor_press",
    "ae2:engineering_processor_press", "mysticalagriculture:prosperity_shard", "mysticalagriculture:inferium_essence",
    "enderio:grains_of_infinity",
)
# Sources that are not recipes: a block mined for its drop, a machine fed with anything.
EXTRA_SOURCES = (
    (("justdirethings:raw_celestigem_ore",), "justdirethings:celestigem"),
    (("justdirethings:raw_blazegold_ore",), "justdirethings:raw_blazegold"),
    (("justdirethings:raw_ferricore_ore",), "justdirethings:raw_ferricore"),
    (("justdirethings:raw_eclipsealloy_ore",), "justdirethings:raw_eclipsealloy"),
    (("justdirethings:raw_coal_t1_ore",), "justdirethings:coal_t1"),
    (("justdirethings:raw_coal_t2_ore",), "justdirethings:coal_t2"),
    (("justdirethings:raw_coal_t3_ore",), "justdirethings:coal_t3"),
    (("justdirethings:raw_coal_t4_ore",), "justdirethings:coal_t4"),
    (("justdirethings:time_crystal_budding_block",), "justdirethings:time_crystal"),
    (("ae2:condenser",), "ae2:matter_ball"),
    (("integrateddynamics:menril_leaves",), "integrateddynamics:menril_berries"),
    (("pneumaticcraft:empty_pcb", "pneumaticcraft:uv_light_box", "pneumaticcraft:etching_acid_bucket"),
     "pneumaticcraft:unassembled_pcb"),
)
NEVER_WORLD = re.compile(r"creative|spawn_egg|command_block|barrier|structure_block|structure_void|jigsaw"
                         r"|debug_stick|knowledge_book|^minecraft:light$")


def compact(dump: pathlib.Path) -> dict:
    tags = json.loads((dump / "tags.json").read_text(encoding="utf-8"))
    items = [json.loads(line) for line in (dump / "items.jsonl").open(encoding="utf-8")]
    item_ids = {i["id"] for i in items if i["id"] != "minecraft:air"}
    entries: list[list] = []
    index: dict[tuple[int, str], int] = {}

    def add(id_: str, kind: int) -> int:
        if (kind, id_) not in index:
            index[(kind, id_)] = len(entries)
            entries.append([id_, kind])
        return index[(kind, id_)]

    for i in items:
        if i["id"] != "minecraft:air":
            add(i["id"], ITEM)

    alts_tab: list[list[int]] = []
    alts_idx: dict[tuple, int] = {}

    def alts(lst):
        key = tuple(dict.fromkeys(lst))
        if not key:
            return None
        if key not in alts_idx:
            alts_idx[key] = len(alts_tab)
            alts_tab.append(list(key))
        return alts_idx[key]

    def known(lst):
        return [index[(ITEM, x)] for x in lst if isinstance(x, str) and (ITEM, x) in index]

    def itemset(d):
        if isinstance(d.get("tag"), str):
            return known(tags.get(d["tag"].lstrip("#"), []))
        if isinstance(d.get("item"), str):
            return [add(d["item"], ITEM)] if d["item"] in item_ids else []
        if isinstance(d.get("id"), str) and d["id"] in item_ids:
            return [add(d["id"], ITEM)]
        if isinstance(d.get("items"), list):
            return known(d["items"])
        if isinstance(d.get("Name"), str) and d["Name"] in item_ids:
            return [add(d["Name"], ITEM)]
        return []

    def stack(d):
        if isinstance(d.get("tag"), str) and "amount" in d and not tags.get(d["tag"].lstrip("#")):
            return (FLUID, [add("#" + d["tag"].lstrip("#"), FLUID)], d["amount"], None)
        if isinstance(d.get("children"), list):
            return (ITEM, [x for c in d["children"] if isinstance(c, dict) for x in (stack(c) or (0, []))[1]], 1, None)
        if isinstance(d.get("tag"), dict):
            return stack(d["tag"])
        if isinstance(d.get("item"), dict):
            s = stack(d["item"])
            return s and (s[0], s[1], d.get("count", s[2]), d.get("chance", s[3]))
        if isinstance(d.get("ingredient"), (dict, list)):
            s = slot(d["ingredient"])
            return s and (s[0], s[1], d.get("count", s[2]), d.get("chance", s[3]))
        if isinstance(d.get("output"), dict) and "chance" in d:
            s = stack(d["output"])
            return s and (s[0], s[1], s[2], d["chance"])
        chance = d.get("chance") if isinstance(d.get("chance"), (int, float)) else None
        for key, kind in (("fluid", FLUID), ("chemical", CHEMICAL), ("gas", CHEMICAL), ("infuse_type", CHEMICAL),
                          ("pigment", CHEMICAL), ("slurry", CHEMICAL)):
            value = d.get(key)
            if isinstance(value, str):
                if value == "minecraft:empty" or not d.get("amount", 1):
                    return None
                return (kind, [add(value, kind)], d.get("amount", 1000), chance)
        if d.get("type") == "fluid_stack" or ("amount" in d and isinstance(d.get("id"), str) and d["id"] not in item_ids):
            if isinstance(d.get("id"), str):
                return (FLUID, [add(d["id"], FLUID)], d.get("amount", 1000), chance)
        ids = itemset(d)
        if ids or "tag" in d or "item" in d or "id" in d:
            count = d.get("count", d.get("amount", 1))
            return (ITEM, ids, count if isinstance(count, int) else 1, chance)
        return None

    def slot(x):
        if isinstance(x, dict):
            return stack(x)
        if isinstance(x, list) and x and all(isinstance(e, dict) for e in x):
            parts = [p for p in (stack(e) for e in x) if p]
            return parts and (parts[0][0], [i for p in parts for i in p[1]], parts[0][2], parts[0][3])
        return None

    out_key = re.compile(r"result|output|secondar|product|byproduct", re.I)
    in_key = re.compile(r"input|ingredient|source|additive|catalyst|reagent|base|addition|template|key|fuel|tool", re.I)
    skip_key = re.compile(r"^(type|sequence|ritual_dummy|target|category|conditions|neoforge:conditions|components|entity.*|pattern)$")

    def walk(node, role, out, depth=0):
        if depth > 6:
            return
        if isinstance(node, dict):
            if (role and any(k in node for k in ("item", "tag", "fluid", "chemical", "gas", "children", "ingredient",
                                                 "infuse_type", "pigment", "slurry", "Name"))) or (role == "out" and "id" in node) \
                    or (role == "in" and isinstance(node.get("id"), str) and "amount" in node):
                s = stack(node)
                if s and (s[1] or role == "in"):
                    out[role].append(s)
                return
            for k, v in node.items():
                if skip_key.match(k):
                    continue
                if k == "catalyst" and isinstance(v, str) and v in item_ids:
                    out["in"].append((ITEM, [add(v, ITEM)], 1, None))
                    continue
                walk(v, "out" if out_key.search(k) else ("in" if in_key.search(k) else role), out, depth + 1)
        elif isinstance(node, list) and role:
            for e in node:
                if isinstance(e, list):
                    s = slot(e)
                    if s:
                        out[role].append(s)
                else:
                    walk(e, role, out, depth + 1)

    def enc(s):
        a = alts(s[1])
        if a is None:
            return None
        r = [a, s[2] if isinstance(s[2], int) else 1, s[0]]
        if isinstance(s[3], (int, float)) and s[3] < 1:
            r.append(round(s[3], 3))
        return r

    skip_type = re.compile(r"almostunified:client_recipe_tracker|crafting_special|crafting_decorated_pot|crafting_shulkerbox|crafting_transmute")
    grid = {"minecraft:crafting_shaped", "minecraft:crafting_shapeless"}
    types: list[str] = []
    type_idx: dict[str, int] = {}
    recipes = []
    for line in (dump / "recipes.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if skip_type.search(r["serializer"]) or skip_type.search(r["type"]):
            continue
        j = r.get("json") or {}
        if r["serializer"] in grid or (r["type"].startswith("minecraft:") and r["ingredients"]) or not j:
            ins = [(ITEM, known(s), 1, None) for s in r["ingredients"]]
            outs = []
        else:
            o = {"in": [], "out": []}
            walk(j, None, o)
            ins, outs = o["in"], o["out"]
            if not [s for s in ins if s[1]] and r["ingredients"]:
                ins = [(ITEM, known(s), 1, None) for s in r["ingredients"]]
        if not outs and r.get("result"):
            res_id = r["result"].get("item") or r["result"].get("id")
            outs = [(ITEM, [add(res_id, ITEM)] if res_id in item_ids else [], r["result"].get("count", 1), None)]
        goo_tier = j.get("tierRequirement")
        if r["type"].startswith("justdirethings:goospread") and f"justdirethings:gooblock_tier{goo_tier}" in item_ids:
            ins.append((ITEM, [add(f"justdirethings:gooblock_tier{goo_tier}", ITEM)], 1, None))
        in_e = [e for e in (enc(s) for s in ins) if e]
        out_e = [e for e in (enc(s) for s in outs) if e]
        if not out_e or not in_e:
            continue
        rtype = INVENTORY if _fits_inventory(r) else r["type"]
        if rtype not in type_idx:
            type_idx[rtype] = len(types)
            types.append(rtype)
        recipes.append([type_idx[rtype], in_e, out_e, r["id"]])

    type_rows = []
    sorted_items = sorted(item_ids)
    for t in types:
        if t in MACHINES:
            machine, source = MACHINES[t], "table"
        else:
            ns, _, path = t.partition(":")
            stem = path.split("/")[-1].replace("_", "")[:5]
            machine = next((i for i in sorted_items if i.startswith(ns + ":") and stem in i.split(":")[1].replace("_", "")), None)
            source = "guess" if machine else "none"
        machines = [m for m in ((machine,) if isinstance(machine, str) else machine or ()) if m in item_ids]
        if machine and not machines:
            source = "missing"
        type_rows.append([t, [index[(ITEM, m)] for m in machines], source])
    return {"entries": entries, "alts": alts_tab, "types": type_rows, "recipes": recipes, "tags": tags}


def _fits_inventory(recipe: dict) -> bool:
    if recipe["type"] != "minecraft:crafting":
        return False
    pattern = (recipe.get("json") or {}).get("pattern")
    if recipe["serializer"] == "minecraft:crafting_shaped" and isinstance(pattern, list):
        return len(pattern) <= 2 and max(map(len, pattern), default=0) <= 2
    if recipe["serializer"] == "minecraft:crafting_shapeless":
        return sum(1 for s in recipe["ingredients"] if s) <= 4
    return False


@dataclass
class Blocker:
    item: str
    reason: str
    unlocked_by: list[str] = field(default_factory=list)


@dataclass
class MilestoneResult:
    key: str
    graph: str
    stage: int
    status: str  # ok | needs_link | unreachable
    blockers: dict[str, list[Blocker]] = field(default_factory=dict)
    proposed_links: list[str] = field(default_factory=list)
    links_verified: bool = False


class Pack:
    def __init__(self, graph: dict, model: dict):
        self.ids = [e[0] for e in graph["entries"]]
        self.index = {(e[1], e[0]): i for i, e in enumerate(graph["entries"])}
        self.milestones = {m["key"]: m for m in model["milestones"]}
        self.unknown_items: set[str] = set()
        self.ancestors: dict[str, frozenset[str]] = ancestors(model)
        canon = self._merge_fluids(graph["entries"])
        alts = [[canon[x] for x in alternatives] for alternatives in graph["alts"]]
        tags = graph.get("tags", {})

        self.gated: dict[int, list[str]] = collections.defaultdict(list)
        banned: set[str] = set()
        for m in model["milestones"]:
            for delivered in (m.get("validation") or {}).get("items", []):
                if isinstance(delivered, dict):
                    self._item(delivered["item"])
            for unlock in m["unlocks"]:
                self.gated[self._item(unlock["item"])].append(m["key"])
                banned.update(unlock["recipes_to_ban"])

        self.slots: list[list[tuple[int, ...]]] = []
        self.outputs: list[list[int]] = []
        self.recipe_ids: list[str] = []
        self.owner: list[str | None] = []
        produced: set[int] = set()
        machines = [row[1] for row in graph["types"]]
        self.guessed_machines = sorted(row[0] for row in graph["types"] if row[2] == "guess")
        self.machineless_types = sorted(row[0] for row in graph["types"] if row[2] in ("none", "missing"))
        for type_idx, inputs, outputs, recipe_id in graph["recipes"]:
            outs = [i for o in outputs for i in alts[o[0]]]
            produced.update(outs)
            if recipe_id in banned:
                continue
            slots = [tuple(alts[s[0]]) for s in inputs]
            if machines[type_idx]:
                slots.append(tuple(machines[type_idx]))
            self._add_recipe(slots, outs, recipe_id, None)
        for i, id_ in list(enumerate(self.ids)):
            essence = (ITEM, id_[:-len("_seeds")] + "_essence")
            if id_.startswith("mysticalagriculture:") and id_.endswith("_seeds") and essence in self.index:
                self._add_recipe([(i,)], [self.index[essence]], f"grow:{id_}", None)
                produced.add(self.index[essence])
        for sources, product in EXTRA_SOURCES:
            if all((ITEM, x) in self.index for x in (*sources, product)):
                self._add_recipe([(self.index[(ITEM, x)],) for x in sources], [self.index[(ITEM, product)]],
                                 f"source:{sources[0]}", None)
                produced.add(self.index[(ITEM, product)])

        crafter = self._item(CRAFTER)
        for m in model["milestones"]:
            for unlock in m["unlocks"]:
                recipe = unlock.get("recipe")
                if not recipe:
                    continue
                slots = [self._ingredient(i["item"], tags) for i in recipe.get("ingredients") or [] if i]
                outs = [self._item(r["item"]) for r in recipe.get("result") or []] or [self._item(unlock["item"])]
                produced.update(outs)
                self._add_recipe(slots + [(crafter,)], outs, recipe.get("type", ""), m["key"])

        world = {i for i, id_ in enumerate(self.ids) if i not in produced}
        world |= {self.index[(ITEM, x)] for t in WORLD_TAGS for x in tags.get(t, []) if (ITEM, x) in self.index}
        world |= {self.index[(ITEM, x)] for x in WORLD_ITEMS if (ITEM, x) in self.index}
        self.world = sorted(i for i in world if i not in self.gated and not NEVER_WORLD.search(self.ids[i])
                            and self.ids[i] not in self.unknown_items)

        self.uses: list[list[tuple[int, int]]] = [[] for _ in self.ids]
        self.producers: list[list[int]] = [[] for _ in self.ids]
        self.slot_base: list[int] = []
        n = 0
        for r, slots in enumerate(self.slots):
            self.slot_base.append(n)
            for s, alternatives in enumerate(slots):
                for x in set(alternatives):
                    self.uses[x].append((r, n + s))
            n += len(slots)
            for x in set(self.outputs[r]):
                self.producers[x].append(r)
        self.n_slots = n
        self.banned_outputs = {x for x in range(len(self.ids)) if x in produced and not self.producers[x]}
        self._cache: dict[frozenset, bytearray] = {}

    def _merge_fluids(self, entries: list[list]) -> list[int]:
        """Fluids and chemicals are one node per id; a fluid tag joins the fluid of the same name."""
        canon = list(range(len(entries)))
        first: dict[str, int] = {}
        by_name: dict[str, int] = {}
        for i, (id_, kind) in enumerate(entries):
            if kind != ITEM and not id_.startswith("#"):
                canon[i] = first.setdefault(id_, i)
                by_name.setdefault(id_.rsplit("/", 1)[-1].split(":")[-1], canon[i])
        self.unresolved_fluid_tags = []
        for i, (id_, kind) in enumerate(entries):
            if id_.startswith("#"):
                name = id_.rsplit("/", 1)[-1].split(":")[-1]
                if name in by_name:
                    canon[i] = by_name[name]
                else:
                    self.unresolved_fluid_tags.append(id_)
        return canon

    def _item(self, id_: str) -> int:
        if (ITEM, id_) not in self.index:
            self.index[(ITEM, id_)] = len(self.ids)
            self.ids.append(id_)
            self.unknown_items.add(id_)
        return self.index[(ITEM, id_)]

    def _ingredient(self, id_: str, tags: dict) -> tuple[int, ...]:
        if id_.startswith("#"):
            members = tuple(self.index[(ITEM, x)] for x in tags.get(id_[1:], []) if (ITEM, x) in self.index)
            return members or (self._item(id_),)
        return (self._item(id_),)

    def _add_recipe(self, slots, outputs, recipe_id, owner):
        self.slots.append([s for s in slots if s])
        self.outputs.append(outputs)
        self.recipe_ids.append(recipe_id)
        self.owner.append(owner)

    def reach(self, done: frozenset[str]) -> bytearray:
        """Everything a player can hold when exactly the milestones in `done` are done."""
        if done in self._cache:
            return self._cache[done]
        enabled = bytearray(1 if o is None or o in done else 0 for o in self.owner)
        missing = [len(s) for s in self.slots]
        satisfied = bytearray(self.n_slots)
        avail = bytearray(len(self.ids))
        queue = list(self.world)
        while queue:
            x = queue.pop()
            if avail[x]:
                continue
            avail[x] = 1
            for r, s in self.uses[x]:
                if satisfied[s] or not enabled[r]:
                    continue
                satisfied[s] = 1
                missing[r] -= 1
                if missing[r] == 0:
                    queue.extend(self.outputs[r])
        self._cache[done] = avail
        return avail

    def blockers(self, item: int, avail: bytearray, done: frozenset[str]) -> list[int]:
        """A small set of items whose absence explains why `item` is out of reach (greedy, depth-limited)."""
        memo: dict[int, frozenset[int]] = {}

        def explain(x: int, stack: frozenset[int], depth: int) -> frozenset[int] | None:
            if avail[x]:
                return frozenset()
            if x in memo:
                return memo[x]
            if x in stack or depth > 8:
                return None
            if x in self.gated and not any(k in done for k in self.gated[x]):
                memo[x] = frozenset([x])
                return memo[x]
            best: frozenset[int] | None = None
            cut = False
            for r in self.producers[x][:40]:
                if self.owner[r] is not None and self.owner[r] not in done:
                    continue
                need: frozenset[int] = frozenset()
                for alternatives in self.slots[r]:
                    if any(avail[a] for a in alternatives):
                        continue
                    options = [o for o in (explain(a, stack | {x}, depth + 1) for a in alternatives[:8]) if o is not None]
                    if not options:
                        need, cut = None, True
                        break
                    need = need | min(options, key=len)
                    if best is not None and len(need) >= len(best):
                        break
                if need is not None and (best is None or len(need) < len(best)):
                    best = need
            if best is None:
                if cut:
                    return None
                best = frozenset([x])
            memo[x] = best
            return best

        return sorted(explain(item, frozenset(), 0) or [item])

    def describe(self, x: int, done: frozenset[str]) -> Blocker:
        if x in self.gated:
            unlockers = sorted(self.gated[x], key=lambda k: (self.milestones[k]["stage"], k))
            if not self.reach(frozenset(self.milestones))[x]:
                return Blocker(self.ids[x], "never craftable: its recipe loops back on itself or lacks a source")
            if any(k in done for k in unlockers):
                return Blocker(self.ids[x], "unlocked, but its Crafter recipe is out of reach")
            return Blocker(self.ids[x], "gated", unlockers)
        if self.ids[x] in self.unknown_items:
            return Blocker(self.ids[x], "not in the pack")
        if x in self.banned_outputs:
            return Blocker(self.ids[x], "no recipe left (all banned)")
        if not self.producers[x]:
            return Blocker(self.ids[x], "no recipe and not a world resource")
        return Blocker(self.ids[x], "no reachable recipe")

    def leak_recipe(self, x: int) -> str:
        avail = self.reach(frozenset())
        return next((self.recipe_ids[r] for r in self.producers[x]
                     if self.owner[r] is None and all(any(avail[a] for a in alt) for alt in self.slots[r])), "")


def ancestors(model: dict, skip: frozenset[tuple[str, str]] = frozenset()) -> dict[str, frozenset[str]]:
    """Transitive prerequisites of every milestone, ignoring the (child, parent) links in `skip`."""
    by_key = {m["key"]: m for m in model["milestones"]}
    memo: dict[str, frozenset[str]] = {}

    def visit(key: str, path: frozenset[str]) -> frozenset[str]:
        if key in memo:
            return memo[key]
        result: set[str] = set()
        for parent in by_key[key]["requires"]:
            if parent in path or parent == key:
                raise ValueError(f"cycle through {key} and {parent}; run progression.py lint first")
            if parent in by_key and (key, parent) not in skip:
                result |= {parent} | visit(parent, path | {key})
        memo[key] = frozenset(result)
        return memo[key]

    return {k: visit(k, frozenset()) for k in by_key}


def _missing(pack: Pack, items: list[int], done: frozenset[str]) -> dict[str, list[Blocker]]:
    avail = pack.reach(done)
    return {pack.ids[x]: [pack.describe(b, done) for b in pack.blockers(x, avail, done)] for x in items if not avail[x]}


def _blocked(pack: Pack, milestone: dict, done: frozenset[str]) -> dict[str, list[Blocker]]:
    """Deliveries must be reachable before the milestone is done, its unlocks right after."""
    key = milestone["key"]
    validation = milestone.get("validation") or {}
    deliver = [pack._item(i["item"]) for i in validation.get("items", []) if isinstance(i, dict)]
    unlocked = [pack._item(u["item"]) for u in milestone["unlocks"]]
    blocked = {**_missing(pack, deliver, done - {key}), **_missing(pack, unlocked, done | {key})}
    for x in deliver:
        if pack.ids[x] in blocked and key in pack.gated.get(x, []):
            blocked[pack.ids[x]] = [Blocker(pack.ids[x], "the milestone asks to deliver an item it unlocks itself")]
    return blocked


def check_milestone(pack: Pack, milestone: dict, strict: frozenset[str], relaxed: frozenset[str]) -> MilestoneResult:
    """`strict`: the milestone's own prerequisites. `relaxed`: every milestone a player may have done by then."""
    key, stage = milestone["key"], milestone["stage"]
    result = MilestoneResult(key, milestone["graph"], stage, "ok")
    strict_blockers = _blocked(pack, milestone, strict)
    if not strict_blockers:
        return result
    relaxed_blockers = _blocked(pack, milestone, relaxed)
    if relaxed_blockers:
        result.status, result.blockers = "unreachable", relaxed_blockers
        return result
    result.status, result.blockers = "needs_link", strict_blockers
    result.proposed_links, result.links_verified = propose_links(pack, milestone, strict, relaxed, strict_blockers)
    return result


def propose_links(pack: Pack, milestone: dict, strict: frozenset[str], relaxed: frozenset[str],
                  blockers: dict[str, list[Blocker]]) -> tuple[list[str], bool]:
    """Greedily adds milestones of `relaxed` until the strict check passes."""
    key, links, done = milestone["key"], [], strict
    for _ in range(8):
        if not blockers:
            return sorted(links), True
        named = sorted({k for found in blockers.values() for b in found for k in b.unlocked_by
                        if k in relaxed and k not in done and k != key},
                       key=lambda k: (pack.milestones[k]["stage"], k))
        options = named or sorted(relaxed - done, key=lambda k: (-pack.milestones[k]["stage"], k))
        best, best_blockers = None, blockers
        for candidate in options:
            trial = _blocked(pack, milestone, done | {candidate} | pack.ancestors[candidate])
            if len(trial) < len(best_blockers):
                best, best_blockers = candidate, trial
                if named:
                    break
        if best is None:
            return sorted(links), False
        links.append(best)
        done, blockers = done | {best} | pack.ancestors[best], best_blockers
    return sorted(links), not blockers


def check(graph: dict, model: dict) -> dict:
    pack = Pack(graph, model)
    anc = pack.ancestors
    descendants: dict[str, set[str]] = collections.defaultdict(set)
    for child, parents in anc.items():
        for parent in parents:
            descendants[parent].add(child)
    by_stage: dict[int, set[str]] = collections.defaultdict(set)
    for m in model["milestones"]:
        by_stage[m["stage"]].add(m["key"])

    def open_at(stage: int, key: str) -> frozenset[str]:
        """Milestones a player may have done when working on `key` at `stage`."""
        return frozenset(k for s, keys in by_stage.items() if s <= stage for k in keys
                         if k != key and k not in descendants[key])

    def run(m: dict, prerequisites: frozenset[str]) -> MilestoneResult:
        return check_milestone(pack, m, prerequisites, open_at(m["stage"], m["key"]) | prerequisites)

    results = {m["key"]: run(m, anc[m["key"]])
               for m in sorted(model["milestones"], key=lambda m: (m["stage"], m["graph"], m["key"]))}

    all_done, none_done = pack.reach(frozenset(pack.milestones)), pack.reach(frozenset())
    gated = sorted(pack.gated)
    leaks = [{"item": pack.ids[x], "recipe": pack.leak_recipe(x)} for x in gated if none_done[x]]
    never = [{"item": pack.ids[x], "unlocked_by": pack.gated[x]} for x in gated if not all_done[x]]

    backward = []
    for m in model["milestones"]:
        later = [p for p in m["requires"] if p in pack.milestones and pack.milestones[p]["stage"] > m["stage"]]
        if not later:
            continue
        skipped = ancestors(model, frozenset((m["key"], p) for p in later))[m["key"]]
        without = run(m, skipped)
        blocking = {k for found in without.blockers.values() for b in found for k in b.unlocked_by}
        for parent in later:
            parent_row = pack.milestones[parent]
            if parent not in blocking:
                own = anc[parent] - {m["key"]}
                unlockers = {k for found in _blocked(pack, parent_row, own).values() for b in found for k in b.unlocked_by}
                reverse = bool(unlockers & ({m["key"]} | skipped))
                fix = (f"reverse it: `{parent}` requires `{m['key']}`" if reverse else "drop the link")
            else:
                movable = all(pack.milestones[k]["stage"] <= m["stage"] for k in anc[parent])
                moved = run({**parent_row, "stage": m["stage"]}, anc[parent]) if movable else None
                fix = (f"move `{parent}` to stage {m['stage']}" if moved and moved.status != "unreachable"
                       else f"move `{m['key']}` to stage {parent_row['stage']}")
            backward.append({"milestone": m["key"], "stage": m["stage"], "requires": parent,
                             "requires_stage": parent_row["stage"], "needed": parent in blocking, "fix": fix})

    rows = list(results.values())
    return {
        "summary": {
            "milestones": len(rows),
            "ok": sum(r.status == "ok" for r in rows),
            "needs_link": sum(r.status == "needs_link" for r in rows),
            "unreachable": sum(r.status == "unreachable" for r in rows),
            "gated_items": len(gated),
            "leaks": len(leaks),
            "never_craftable": len(never),
            "world_items": len(pack.world),
            "items": len(pack.ids),
            "reachable_with_everything_done": sum(all_done),
            "unknown_items": len(pack.unknown_items),
        },
        "milestones": [asdict(r) for r in rows],
        "backward_links": backward,
        "leaks": leaks,
        "never_craftable": never,
        "unknown_items": sorted(pack.unknown_items),
        "unresolved_fluid_tags": sorted(pack.unresolved_fluid_tags),
        "guessed_machines": pack.guessed_machines,
        "types_without_machine": pack.machineless_types,
    }


def markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "| | Count |", "|---|---|",
        f"| Milestones checked | {s['milestones']} |",
        f"| Completable with their own prerequisites | {s['ok']} |",
        f"| Completable, but through a milestone that is not a prerequisite | {s['needs_link']} |",
        f"| Not completable with the stages open at that point | {s['unreachable']} |",
        f"| Gated items (unlocks) | {s['gated_items']} |",
        f"| Gated items a player can make with no milestone done (leaks) | {s['leaks']} |",
        f"| Gated items never craftable, even with every milestone done | {s['never_craftable']} |",
        "",
    ]
    if report["backward_links"]:
        lines += ["### Links to a later stage", "", "| Milestone (stage) | Requires (stage) | Needed by the recipes | Fix |",
                  "|---|---|---|---|"]
        for b in report["backward_links"]:
            lines.append(f"| `{b['milestone']}` ({b['stage']}) | `{b['requires']}` ({b['requires_stage']}) | "
                         f"{'yes' if b['needed'] else 'no'} | {b['fix']} |")
        lines.append("")
    rows = [m for m in report["milestones"] if m["status"] == "unreachable"]
    if rows:
        lines += ["### Not completable", "", "| Stage | Milestone | Item | Missing |", "|---|---|---|---|"]
        for m in rows:
            for item, blockers in sorted(m["blockers"].items()):
                lines.append(f"| {m['stage']} | `{m['key']}` | `{item}` | {_blockers(blockers)} |")
        lines.append("")
    rows = [m for m in report["milestones"] if m["status"] == "needs_link"]
    if rows:
        lines += ["### Missing links", "", "| Stage | Milestone | Should also require |", "|---|---|---|"]
        for m in rows:
            links = ", ".join(f"`{k}`" for k in m["proposed_links"]) or "none found"
            lines.append(f"| {m['stage']} | `{m['key']}` | {links}{'' if m['links_verified'] else ' (not enough)'} |")
        lines.append("")
    if report["never_craftable"]:
        lines += ["### Never craftable", "", "| Item | Unlocked by |", "|---|---|"]
        lines += [f"| `{n['item']}` | {', '.join(f'`{k}`' for k in n['unlocked_by'])} |" for n in report["never_craftable"]]
        lines.append("")
    if report["leaks"]:
        lines += ["### Leaks", "", "| Item | Recipe still active |", "|---|---|"]
        lines += [f"| `{n['item']}` | `{n['recipe']}` |" for n in report["leaks"]]
        lines.append("")
    return "\n".join(lines)


def _blockers(blockers: list[dict]) -> str:
    parts = []
    for b in blockers:
        if b["unlocked_by"]:
            parts.append(f"`{b['item']}` ({', '.join(b['unlocked_by'])})")
        else:
            parts.append(f"`{b['item']}` ({b['reason']})")
    return "<br>".join(parts)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    compact_cmd = sub.add_parser("compact")
    compact_cmd.add_argument("dump", type=pathlib.Path)
    compact_cmd.add_argument("-o", "--output", type=pathlib.Path, required=True)
    check_cmd = sub.add_parser("check")
    check_cmd.add_argument("graph", type=pathlib.Path)
    check_cmd.add_argument("model", type=pathlib.Path)
    check_cmd.add_argument("--json", type=pathlib.Path)
    check_cmd.add_argument("--markdown", type=pathlib.Path)
    args = parser.parse_args(argv)

    if args.command == "compact":
        graph = compact(args.dump)
        args.output.write_text(json.dumps(graph, separators=(",", ":")), encoding="utf-8")
        print(f"{len(graph['recipes'])} recipes, {len(graph['types'])} types, {len(graph['entries'])} entries")
        return 0

    report = check(json.loads(args.graph.read_text(encoding="utf-8")), json.loads(args.model.read_text(encoding="utf-8")))
    if args.json:
        args.json.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    text = markdown(report)
    if args.markdown:
        args.markdown.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if report["summary"]["unreachable"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

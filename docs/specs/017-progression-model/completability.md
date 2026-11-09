# Completability of the current tree (9 Nov 2026)

| | |
|---|---|
| **Status** | First pass of initiative [#28](https://github.com/Arffornia/docs/issues/28), for Brian's review |
| **Input** | Recipe dump of the pack (Provisioning `main`, 328 mods, [Mods#59](https://github.com/Arffornia/Arffornia_Mods/pull/59)) and [`current-tree-2026-07-31.json`](current-tree-2026-07-31.json) |
| **Tool** | [`scripts/recipe_graph.py`](https://github.com/Arffornia/docs/blob/main/scripts/recipe_graph.py), `make progression-check DUMP=<dir>` (about 2 minutes) |

The lint of [spec 017](spec.md) checks the shape of the tree. This check replays the tree on the
real recipes of the pack: for every milestone, can a player make what it unlocks with the stages
open at that point?

## Summary

- **111 of 194** milestones are completable with their own prerequisites only.
- **67** are completable, but only through a milestone of the same or an earlier stage that is not
  one of their prerequisites. With the 80 % rule a player can skip that milestone and get stuck.
  The tool proposes the missing link for each.
- **16** are not completable with the stages open at that point. The cause is one of: an unlock
  whose machine is gated at a later stage, a delivery of an item the milestone itself unlocks, or a
  Crafter recipe that is never craftable.
- **6** gated items are never craftable, even with every milestone done.
- **21** gated items leak: a recipe that was not banned still makes them with no milestone done
  (Oritech machines, Refined Storage disks and buses, iron ingot).
- The **5 backward links** of Green Thumb are layout mistakes, not recipe needs. The fix below
  removes all 5 and makes `green_thumb/tier_4` completable.

## Green Thumb: fix for the 5 backward links

The recipes say none of the 5 later-stage milestones is needed by the earlier one. The stage-6
milestones need `tier_4` instead: their seeds use essences that `tier_4` unlocks. The arrows were
drawn the wrong way.

| Link today | Proposal | Evidence |
|---|---|---|
| `tier_1` (stage 2) requires `infusion_crystal` (stage 3) | Move `infusion_crystal` to stage 2 and keep the link | The crystal is the gate of tier 1 in Mystical Agriculture (prudentium essence = inferium + crystal). The tool says the link can be dropped only because the `prudentium_essence` unlock captured the block uncraft recipe instead of the crystal recipe; fix that unlock too. `infusion_crystal` is completable at stage 2 (diamond, inferium, prosperity) |
| `tier_4` (5) requires `again_and_again` (6) | Reverse: `again_and_again` requires `tier_4` | Needs dark steel, lapis, ruby essences from `tier_4` seeds |
| `tier_4` (5) requires `powah` (6) | Reverse: `powah` requires `tier_4` | Needs electrum, osmium, sapphire essences from `tier_4` seeds |
| `tier_4` (5) requires `a_seed_refinded` (6) | Reverse, and add `where_theres_a_will_theres_a_way` | Needs glowstone and iron essences (`tier_3`, through `tier_4`) and obsidian essence |
| `tier_4` (5) requires `ender_io_2` (6) | Reverse, and add `ender_io` | Needs conductive, copper and redstone alloy essences from `ender_io` |
| (new) | `tier_4` requires `hostile_and_rabbit` | `tier_4` needs creeper essence |

Applied to a copy of the tree, these changes give 0 backward links and `tier_4`, `again_and_again`,
`powah` and `ender_io_2` move to "completable with their own prerequisites".

## Rules

| Rule | Choice |
|---|---|
| Recipe | Input slots (each a list of alternatives: items, fluids, chemicals) and outputs, read from the dump's codec JSON (same parser as the JEI site). Counts, energy and chances are ignored: one craft proves the path |
| Machine | A recipe type needs its machine item (table `MACHINES`). 2x2 crafting needs no table. 61 types are matched by name; the JSON report lists them as `guessed_machines` |
| Ban | `recipes_to_ban` of every unlock are removed for good |
| Unlock | Its Crafter recipe (`arffornia:crafter_block` plus the unlock ingredients) is active once its milestone is done |
| World resource | An item no recipe makes, plus natural tags (ores, raw materials, logs, crops, stones...) and a short list (diamond, redstone, buckets of water and lava, AE2 meteorite presses...). A gated item is never a world resource. Creative items and spawn eggs never are |
| Other sources | Growing a Mystical Agriculture seed gives its essence; a few block drops and machines that are not recipe types (JDT raw ores, AE2 condenser, PNC UV light box) |
| Fluids | Fluids and chemicals with the same id are one node. A fluid tag joins the fluid of the same name, otherwise it counts as a world resource (32 tags, listed in the JSON) |
| Milestone | Items to deliver must be reachable before the milestone is done, its unlocks right after |
| Strict check | Only the milestone's own prerequisites are done |
| Relaxed check | Every milestone of its stage and earlier stages is done (optimistic: ignores the 80 % threshold and the Noyau module) |
| Missing items | Greedy search for the smallest set of gated items that explains the failure (depth 8) |

Known gaps: loot, mob drops, villager and Amadron trades, rituals and multiblock formation are
not recipes. Some "never craftable" items may come from such a source (cyanite seeds need the
Extreme Reactors reprocessor multiblock). Each new source is one line in `EXTRA_SOURCES` or
`WORLD_ITEMS`.

## Decisions for Brian

1. Green Thumb: accept the 6 link changes above, and the `infusion_crystal` move to stage 2.
2. Missing links: add the proposed links, or accept that a milestone depends on a sibling the
   player may skip. The tool can apply them to a draft once you choose.
3. Leaks: ban the extra recipes listed below, or drop those items from the unlocks.
4. Self-deliveries: `ae2/aaas_automation_as_a_service` asks to deliver `ae2:interface` and
   `ae2:pattern_provider`, which it unlocks itself. Deliver something else or unlock them earlier.
5. World rule: confirm the list of world resources, or name the items you want gated.

## Results

Generated by `make progression-check`. The full JSON (blockers per item) is written next to the
Markdown in `/tmp`.

| | Count |
|---|---|
| Milestones checked | 194 |
| Completable with their own prerequisites | 111 |
| Completable, but through a milestone that is not a prerequisite | 67 |
| Not completable with the stages open at that point | 16 |
| Gated items (unlocks) | 701 |
| Gated items a player can make with no milestone done (leaks) | 21 |
| Gated items never craftable, even with every milestone done | 6 |

### Links to a later stage

| Milestone (stage) | Requires (stage) | Needed by the recipes | Fix |
|---|---|---|---|
| `green_thumb/tier_1` (2) | `green_thumb/infusion_crystal` (3) | no | drop the link |
| `green_thumb/tier_4` (5) | `green_thumb/again_and_again` (6) | no | reverse it: `green_thumb/again_and_again` requires `green_thumb/tier_4` |
| `green_thumb/tier_4` (5) | `green_thumb/a_seed_refinded` (6) | no | drop the link |
| `green_thumb/tier_4` (5) | `green_thumb/ender_io_2` (6) | no | drop the link |
| `green_thumb/tier_4` (5) | `green_thumb/powah` (6) | no | reverse it: `green_thumb/powah` requires `green_thumb/tier_4` |

### Not completable

| Stage | Milestone | Item | Missing |
|---|---|---|---|
| 1 | `ae2/ae2_my_first_homelab` | `ae2:energy_acceptor` | `ae2:energy_acceptor` (never craftable: its recipe loops back on itself or lacks a source) |
| 1 | `mekanism/mekanism_fundamentals` | `mekanism:pressurized_reaction_chamber` | `mekanism:basic_chemical_tank` (mekanism/mekanism_basic_tank) |
| 2 | `ae2/1k_storage` | `ae2:1k_crafting_storage` | `ae2:crafting_unit` (ae2/aaas_automation_as_a_service) |
| 2 | `mekanism/i_need_more_firepower_i` | `mekanism_lasers:basic_laser` | `mekanism:laser` (mekanism/mekanism_advanced_generator) |
| 2 | `mekanism/i_need_more_firepower_i` | `mekanism_lasers:basic_toggleable_laser` | `mekanism:laser` (mekanism/mekanism_advanced_generator) |
| 2 | `mekanism/i_need_more_firepower_i` | `mekanism_turrets:basic_laser_turret` | `mekanism:electric_bow` (mekanism/mekanism_advanced_tools) |
| 2 | `pneumatic_craft/compressor_i` | `pneumaticcraft:liquid_compressor` | `pneumaticcraft:small_tank` (pneumatic_craft/fluid_i) |
| 3 | `ae2/aaas_automation_as_a_service` | `ae2:interface` | `ae2:interface` (the milestone asks to deliver an item it unlocks itself) |
| 3 | `ae2/aaas_automation_as_a_service` | `ae2:pattern_provider` | `ae2:pattern_provider` (the milestone asks to deliver an item it unlocks itself) |
| 3 | `ae2/aaas_automation_as_a_service` | `appflux:flux_accessor` | `appflux:flux_accessor` (never craftable: its recipe loops back on itself or lacks a source) |
| 3 | `ae2/aaas_automation_as_a_service` | `extendedae:caner` | `extendedae:crystal_assembler` (ae2/crystal_technlogy_iii) |
| 3 | `ae2/crystal_technlogy_ii` | `advanced_ae:reaction_chamber` | `advanced_ae:reaction_chamber` (never craftable: its recipe loops back on itself or lacks a source) |
| 3 | `green_thumb/tier_2` | `mysticalagriculture:coral_seeds` | `mysticalagriculture:coral_seeds` (never craftable: its recipe loops back on itself or lacks a source) |
| 3 | `green_thumb/tier_2` | `mysticalagriculture:limestone_seeds` | `mysticalagriculture:limestone_seeds` (never craftable: its recipe loops back on itself or lacks a source) |
| 3 | `industrial_foregoing/generator_tier_ii_too_many_things_to_burn` | `industrialforegoing:mycelial_halitosis` | `industrialforegoing:fluid_laser_base` (industrial_foregoing/lazer_drill) |
| 3 | `industrial_foregoing/generator_tier_ii_too_many_things_to_burn` | `industrialforegoing:mycelial_meatallurgic` | `industrialforegoing:fluid_laser_base` (industrial_foregoing/lazer_drill) |
| 3 | `industrial_foregoing/generator_tier_ii_too_many_things_to_burn` | `industrialforegoing:mycelial_netherstar` | `industrialforegoing:fluid_laser_base` (industrial_foregoing/lazer_drill) |
| 3 | `mekanism/i_need_more_firepower_ii` | `mekanism_lasers:advanced_laser` | `mekanism:laser` (mekanism/mekanism_advanced_generator) |
| 3 | `mekanism/i_need_more_firepower_ii` | `mekanism_lasers:advanced_toggleable_laser` | `mekanism:laser` (mekanism/mekanism_advanced_generator) |
| 3 | `mekanism/mekanism_advanced_tools` | `mekanism:hdpe_elytra` | `oritech:atomic_forge_block` (oritech/forge_technology_ii)<br>`oritech:big_solar_panel_block` (oritech/generator_iii) |
| 3 | `mekanism/mekanism_advanced_tools` | `mekanism:meka_tool` | `mekanism:solar_neutron_activator` (mekanism/mekanism_advanced_generator) |
| 3 | `mekanism/mekanism_advanced_tools` | `mekanism:mekasuit_bodyarmor` | `mekanism:solar_neutron_activator` (mekanism/mekanism_advanced_generator) |
| 3 | `mekanism/mekanism_advanced_tools` | `mekanism:mekasuit_boots` | `mekanism:solar_neutron_activator` (mekanism/mekanism_advanced_generator) |
| 3 | `mekanism/mekanism_advanced_tools` | `mekanism:mekasuit_helmet` | `mekanism:solar_neutron_activator` (mekanism/mekanism_advanced_generator) |
| 3 | `mekanism/mekanism_advanced_tools` | `mekanism:mekasuit_pants` | `mekanism:solar_neutron_activator` (mekanism/mekanism_advanced_generator) |
| 3 | `refine_storage/stop_cutting_logs_to_make_a_crafting_table_every_100_blocks` | `refinedstorage:portable_grid` | `refinedstorage:controller` (ae2/advanced_automation_processing_ii) |
| 4 | `pneumatic_craft/heat_technology_i` | `pneumaticcraft:heat_pipe` | `pneumaticcraft:thermal_lagging` (pneumatic_craft/eco_heating_technology) |
| 4 | `pneumatic_craft/heat_technology_i` | `pneumaticcraft:thermostat_module` | `pneumaticcraft:thermal_lagging` (pneumatic_craft/eco_heating_technology) |
| 6 | `green_thumb/tier_5` | `mysticalagriculture:cyanite_seeds` | `mysticalagriculture:cyanite_seeds` (never craftable: its recipe loops back on itself or lacks a source) |
| 6 | `green_thumb/tier_5` | `mysticalagriculture:enderman_essence` | `mysticalagriculture:enderman_seeds` (green_thumb/tiny_hostile_creature) |
| 8 | `ae2/quantum_computer` | `advanced_ae:quantum_core` | `advanced_ae:quantum_storage_256` (ae2/256m_quantum_storage)<br>`advanced_ae:quantum_accelerator` (ae2/quantum_computer_stage_1) |
| 8 | `ae2/quantum_crafting` | `advanced_ae:quantum_crafter` | `advanced_ae:quantum_accelerator` (ae2/quantum_computer_stage_1) |

### Missing links

| Stage | Milestone | Should also require |
|---|---|---|
| 2 | `integrated_dynamic/energy_production` | `integrated_dynamic/energy_storage_tier_i` |
| 2 | `integrated_dynamic/produce_without_jumping_anymore_d` | `integrated_dynamic/energy_storage_tier_i` |
| 2 | `mekanism/mekanism_basic_tools` | `mekanism/mekanism_basic_tank` |
| 3 | `ae2/4k_storage` | `ae2/aaas_automation_as_a_service`, `ae2/energy_storage_i` |
| 3 | `industrial_foregoing/mob_production` | `industrial_foregoing/plastic_production` |
| 3 | `integrated_dynamic/exporter_technology` | `integrated_dynamic/interface_technology` |
| 3 | `integrated_dynamic/importer_technology` | `integrated_dynamic/interface_technology` |
| 3 | `integrated_dynamic/interface_technology` | `integrated_dynamic/energy_storage_tier_i` |
| 3 | `pneumatic_craft/pcb_technology` | `pneumatic_craft/fluid_i` |
| 3 | `refine_storage/4k_storage` | `mekanism/mekanism_fundamentals` |
| 4 | `ae2/16k_storage` | `ae2/aaas_automation_as_a_service`, `ae2/crystal_technlogy_i`, `ae2/energy_storage_i` |
| 4 | `ae2/advanced_automation_processing_i` | `ae2/crystal_technlogy_iii` |
| 4 | `ae2/bus_technology_i` | `ae2/crystal_technlogy_iii` |
| 4 | `ae2/energy_storage_iii` | `ae2/crystal_technlogy_iii` |
| 4 | `green_thumb/tier_3` | `green_thumb/creature_seeds` |
| 4 | `industrial_foregoing/enchantment_production` | `industrial_foregoing/plastic_production` |
| 4 | `industrial_foregoing/lazer_drill` | `industrial_foregoing/plastic_production` |
| 4 | `industrial_foregoing/potion_production` | `industrial_foregoing/plastic_production` |
| 4 | `integrated_dynamic/bot_technology` | `integrated_dynamic/interface_technology` |
| 4 | `integrated_dynamic/filtering_interface` | `integrated_dynamic/energy_storage_tier_i` |
| 4 | `mekanism/i_need_more_firepower_iii` | `mekanism/mekanism_advanced_generator`, `mekanism/mekanism_advanced_tools` |
| 4 | `mekanism/mekanism_advanced_generator` | `mekanism/mekanism_basic_energy`, `mekanism/mekanism_basic_tank` |
| 4 | `mekanism/mekanism_elite_cable` | `mekanism/mekanism_advanced_cable`, `mekanism/mekanism_fundamentals` |
| 4 | `mekanism/mekanism_elite_factory` | `mekanism/mekanism_advanced_factory`, `mekanism/mekanism_basic_factory`, `mekanism/mekanism_fundamentals`, `oritech/forge_technology_ii` |
| 4 | `pneumatic_craft/rafinery_technology` | `pneumatic_craft/fluid_i` |
| 4 | `refine_storage/16k_storage` | `mekanism/mekanism_fundamentals` |
| 5 | `ae2/64k_storage` | `ae2/aaas_automation_as_a_service`, `ae2/energy_storage_i` |
| 5 | `ae2/advanced_automation_processing_ii` | `ae2/crystal_technlogy_iii` |
| 5 | `green_thumb/tier_4` | `green_thumb/hostile_and_rabbit` |
| 5 | `mekanism/i_need_more_firepower_iv` | `mekanism/mekanism_advanced_generator`, `mekanism/mekanism_advanced_tools` |
| 5 | `mekanism/mekanism_do_the_mining_for_me` | `mekanism/mekanism_advanced_tools` |
| 5 | `mekanism/mekanism_ultimate_cable` | `mekanism/mekanism_advanced_cable`, `mekanism/mekanism_fundamentals` |
| 5 | `mekanism/mekanism_ultimate_factory` | `mekanism/mekanism_advanced_factory`, `mekanism/mekanism_basic_factory`, `mekanism/mekanism_fundamentals`, `oritech/forge_technology_ii` |
| 5 | `oritech/drone_technology` | `oritech/forge_technology_ii` |
| 5 | `oritech/forge_technology_iii` | `oritech/storage_technology_i` |
| 5 | `oritech/machine_core_iv` | `oritech/forge_technology_ii` |
| 5 | `pneumatic_craft/assembly_line_technology` | `pneumatic_craft/pressure_chamber_technology` |
| 5 | `pneumatic_craft/compressor_iii` | `pneumatic_craft/assembly_line_technology`, `pneumatic_craft/fluid_i`, `pneumatic_craft/heat_technology_ii`, `pneumatic_craft/pressure_chamber_technology` |
| 5 | `pneumatic_craft/drone_technology` | `pneumatic_craft/pressure_chamber_technology` |
| 5 | `pneumatic_craft/fluid_iii` | `pneumatic_craft/assembly_line_technology`, `pneumatic_craft/pressure_chamber_technology` |
| 5 | `pneumatic_craft/heat_technology_ii` | `pneumatic_craft/fluid_i` |
| 6 | `ae2/256k_storage` | `ae2/aaas_automation_as_a_service`, `ae2/energy_storage_i` |
| 6 | `green_thumb/a_seed_refinded` | `green_thumb/tier_3`, `green_thumb/where_theres_a_will_theres_a_way`, `mekanism/mekanism_fundamentals`, `oritech/forge_technology_ii` |
| 6 | `green_thumb/again_and_again` | `green_thumb/tier_3`, `green_thumb/tier_4` |
| 6 | `green_thumb/ender_io_2` | `green_thumb/ender_io`, `green_thumb/tier_3` |
| 6 | `green_thumb/powah` | `green_thumb/tier_3`, `green_thumb/tier_4` |
| 6 | `mekanism/mekanism_qio_storage` | `green_thumb/a_seed_refinded`, `mekanism/mekanism_fundamentals`, `oritech/forge_technology_ii` |
| 6 | `mekanism/more_ore` | `mekanism/i_need_more_firepower_i`, `mekanism/mekanism_advanced_tools`, `mekanism/mekanism_basic_tank` |
| 6 | `pneumatic_craft/armor_technology` | `pneumatic_craft/assembly_line_technology`, `pneumatic_craft/pressure_chamber_technology` |
| 6 | `pneumatic_craft/compressor_iv` | `pneumatic_craft/assembly_line_technology`, `pneumatic_craft/pressure_chamber_technology` |
| 6 | `pneumatic_craft/mob_spawner_technology` | `pneumatic_craft/pressure_chamber_technology` |
| 6 | `pneumatic_craft/programmable_drone_technology` | `pneumatic_craft/assembly_line_technology`, `pneumatic_craft/pressure_chamber_technology` |
| 6 | `refine_storage/strange_storage_technology` | `green_thumb/a_seed_refinded`, `mekanism/mekanism_fundamentals` |
| 7 | `ae2/1m_storage` | `ae2/advanced_automation_processing_ii`, `ae2/crystal_technlogy_iii`, `ae2/energy_storage_ii` |
| 7 | `ae2/high_density_automation_i` | `ae2/aaas_automation_as_a_service`, `ae2/ae2_my_first_homelab`, `ae2/crystal_technlogy_iii` |
| 7 | `ae2/high_density_automation_ii` | `ae2/aaas_automation_as_a_service`, `ae2/ae2_my_first_homelab`, `ae2/crystal_technlogy_iii`, `ae2/energy_storage_i` |
| 7 | `green_thumb/harvest_diamond` | `green_thumb/where_theres_a_will_theres_a_way` |
| 7 | `mekanism/mekanism_fusion_reactor` | `mekanism/mekanism_advanced_generator` |
| 7 | `oritech/machine_core_vi` | `oritech/forge_technology_ii` |
| 8 | `ae2/4m_storage` | `ae2/advanced_automation_processing_ii`, `ae2/crystal_technlogy_iii`, `ae2/energy_storage_ii` |
| 8 | `ae2/quantum_armor` | `ae2/ae2_my_first_homelab`, `ae2/crystal_technlogy_i` |
| 8 | `mekanism/mekanism_antimatter_generator` | `mekanism/mekanism_advanced_generator` |
| 9 | `ae2/16m_storage` | `ae2/advanced_automation_processing_ii`, `ae2/crystal_technlogy_iii`, `ae2/energy_storage_ii` |
| 9 | `ae2/quantum_computer_stage_1` | `ae2/aaas_automation_as_a_service`, `ae2/ae2_my_first_homelab`, `ae2/crystal_technlogy_i`, `ae2/crystal_technlogy_iii` |
| 10 | `ae2/64m_storage` | `ae2/advanced_automation_processing_ii`, `ae2/crystal_technlogy_i`, `ae2/crystal_technlogy_iii`, `ae2/energy_storage_ii` |
| 11 | `ae2/256m_quantum_storage` | `ae2/crystal_technlogy_i`, `ae2/quantum_computer` |
| 11 | `ae2/256m_storage` | `ae2/advanced_automation_processing_ii`, `ae2/crystal_technlogy_i`, `ae2/crystal_technlogy_iii`, `ae2/energy_storage_ii` |

### Never craftable

| Item | Unlocked by |
|---|---|
| `appflux:flux_accessor` | `ae2/aaas_automation_as_a_service` |
| `mysticalagriculture:coral_seeds` | `green_thumb/tier_2` |
| `mysticalagriculture:limestone_seeds` | `green_thumb/tier_2` |
| `mysticalagriculture:cyanite_seeds` | `green_thumb/tier_5` |
| `ae2:energy_acceptor` | `ae2/ae2_my_first_homelab` |
| `advanced_ae:reaction_chamber` | `ae2/crystal_technlogy_ii` |

### Leaks

| Item | Recipe still active |
|---|---|
| `minecraft:iron_ingot` | `forbidden_arcanus:clibano_combustion/iron_ingot_from_clibano_combustion` |
| `oritech:fluid_pipe` | `oritech:crafting/unframe_fluid` |
| `oritech:pulverizer_block` | `oritech:crafting/pulverizer` |
| `oritech:assembler_block` | `oritech:crafting/assembler` |
| `oritech:centrifuge_block` | `oritech:crafting/centrifugealt` |
| `oritech:powered_furnace_block` | `oritech:crafting/electricfurnace` |
| `oritech:pump_block` | `oritech:compat/enderio/crafting/pump` |
| `oritech:machine_core_2` | `oritech:crafting/core2alt` |
| `oritech:machine_core_3` | `oritech:crafting/core3` |
| `refinedstorage:pattern_grid` | `refinedstorage:pattern_grid` |
| `refinedstorage:importer` | `refinedstorage:coloring/gray_importer` |
| `refinedstorage:exporter` | `ftb:cleaning/refinedstorage/exporters` |
| `refinedstorage:1k_storage_disk` | `refinedstorage:1k_storage_disk_from_storage_housing` |
| `refinedstorage:4k_storage_disk` | `refinedstorage:4k_storage_disk_from_storage_housing` |
| `refinedstorage:16k_storage_disk` | `refinedstorage:16k_storage_disk_upgrade` |
| `refinedstorage:64k_storage_disk` | `refinedstorage:64k_storage_disk_upgrade` |
| `refinedstorage:64b_fluid_storage_disk` | `refinedstorage:64b_fluid_storage_disk_from_storage_housing` |
| `refinedstorage:256b_fluid_storage_disk` | `refinedstorage:256b_fluid_storage_disk_upgrade` |
| `refinedstorage:1024b_fluid_storage_disk` | `refinedstorage:1024b_fluid_storage_disk_upgrade` |
| `refinedstorage:4096b_fluid_storage_disk` | `refinedstorage:4096b_fluid_storage_disk_upgrade` |
| `refinedstorage_mekanism_integration:64b_chemical_storage_disk` | `refinedstorage_mekanism_integration:64b_chemical_storage_disk_from_storage_housing` |


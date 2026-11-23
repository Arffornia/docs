# Fix batch for the current tree (Nov 2026)

| | |
|---|---|
| **Status** | Proposal for Brian. Nothing is applied: the website data is unchanged |
| **Initiative** | [#28](https://github.com/Arffornia/docs/issues/28), progression graph tooling |
| **Input** | Live staging model (`https://staging.arffornia.com/api/progression/model`, version 1, 23 Nov 2026) and the recipe dump of 22 Nov 2026 (Provisioning `main`, 324 mods plus storage, 35,619 recipes) |
| **Tool** | `make progression-check DUMP=<dir> MODEL=<model.json>`, rules in [completability](completability.md), single-path rule of [ADR 0017](../../decisions/0017-milestones-complete-in-the-space-elevator.md) |

## How to use this page

Tick `[x]` in the **OK** column of each fix you accept, or write what you want instead, then
merge the change. An agent then applies the accepted rows in the editor as one draft and
publishes it after the check passes.

## Where the tree stands

The live model has 28 milestones with items to deliver. The other 166 have nothing: 158 still
hold an `obtain` validation that lists their own unlocks, which ADR 0017 retired, and 8 have
none. Under the single-path rule they can never be completed, so every stage is below its
threshold. Filling them is blocked on the [game design questions](#game-design-questions-that-block-generated-required-items).

| | Today | With every fix below |
|---|---|---|
| Milestones with deliveries completable with their own prerequisites | 19 of 28 | 28 of 28 |
| Completable only through a milestone they do not require | 5 | 0 |
| Not completable at their stage | 4 | 0 |
| Unlocks the player cannot make right after their milestone | 22 | 0 |
| Gated items a player makes with no milestone done (leaks) | 21 | 0 |
| Gated items never craftable | 6 | 3 (Mystical Agriculture seeds, rows G16 and G17) |
| Backward links (requires a later stage) | 5 | 0 |

The right column comes from applying all the rows to a local copy of the live model and
running the full check again. The rows work as a set: a few links (G12 to G14) only appear once
the Green Thumb arrows are reversed.

## Fixes by graph

Kinds: **requires** (add, remove, reverse a link), **stage** (move a milestone), **deliver**
(change required items), **unlock** (move or drop an unlock, fix its Crafter recipe), **ban**
(add recipes to `recipes_to_ban`).

### Green Thumb (Mystical Agriculture)

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| G1 | stage | Move `infusion_crystal` from stage 3 to 2, keep `tier_1` requires it | The crystal is the gate of tier 1 (prudentium essence = 4 inferium + crystal), so the link is right and the stage is wrong | [ ] |
| G2 | unlock | `tier_1`: Crafter recipe of `prudentium_essence` becomes 4 `inferium_essence` + `infusion_crystal` | The stored recipe is the uncraft of the prudentium block, which hides the need for the crystal | [ ] |
| G3 | requires | Reverse: `again_and_again` requires `tier_4` (was `tier_4` requires it) | It delivers dark steel, lapis and ruby essences, whose seeds `tier_4` unlocks | [ ] |
| G4 | requires | Reverse: `powah` requires `tier_4` | It delivers electrum, osmium and sapphire essences from `tier_4` seeds | [ ] |
| G5 | requires | Reverse: `a_seed_refinded` requires `tier_4` | It needs essences from `tier_4` seeds; `tier_4` needs nothing from it | [ ] |
| G6 | requires | Reverse: `ender_io_2` requires `tier_4` | Same: the arrow was drawn the wrong way | [ ] |
| G7 | requires | `tier_4` requires `hostile_and_rabbit` | `tier_4` needs creeper essence, whose seed `hostile_and_rabbit` unlocks | [ ] |
| G8 | requires | `tier_3` requires `creature_seeds` | Its deliveries need a seed that `creature_seeds` unlocks | [ ] |
| G9 | requires | `a_seed_refinded` requires `where_theres_a_will_theres_a_way` | It needs obsidian essence from that milestone | [ ] |
| G10 | requires | `ender_io_2` requires `ender_io` | It needs conductive, copper and redstone alloy essences from `ender_io` | [ ] |
| G11 | requires | `harvest_diamond` requires `where_theres_a_will_theres_a_way` | Its deliveries need a seed that milestone unlocks | [ ] |
| G12 | requires | `harvest_diamond` requires `again_and_again` | Appears after G3: it needs an essence `again_and_again` unlocks | [ ] |
| G13 | requires | `ender_io_cheated` requires `ender_io_2` | Appears after G6: it needs an essence `ender_io_2` unlocks | [ ] |
| G14 | requires | `the_prime_creature` requires `a_seed_refinded` | Appears after G5: it needs an essence `a_seed_refinded` unlocks | [ ] |
| G15 | deliver | `tier_5` delivers `imperium_essence` and `supremium_essence` only; drop `enderman_essence` and `refined_obsidian_essence` | Enderman seeds open at stage 7 (`tiny_hostile_creature`) and refined obsidian needs the Mekanism metallurgic infuser; both kept `tier_5` (stage 6) out of reach | [ ] |
| G16 | unlock | `tier_2`: decide on `coral_seeds` and `limestone_seeds`: drop the unlocks, or confirm in game where their agglomeratio comes from | No recipe in the dump makes them, even with every milestone done | [ ] |
| G17 | unlock | `tier_5`: keep `cyanite_seeds` and add the Extreme Reactors reprocessor as a known source in the tool | Cyanite comes from a multiblock, not a recipe, so the tool cannot see it | [ ] |

### AE2 and addons

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| A1 | deliver | `aaas_automation_as_a_service` delivers `ae2:logic_processor`, `ae2:calculation_processor`, `ae2:engineering_processor` instead of `ae2:interface`, `ae2:pattern_provider`, `extendedae:caner` | It unlocks the interface and pattern provider itself, and the caner needs the crystal assembler of stage 4; the three processors are made with its own prerequisites | [ ] |
| A2 | unlock | Move `ae2:1k_crafting_storage` from `1k_storage` (stage 2) to `aaas_automation_as_a_service` (stage 3) | Its recipe needs `ae2:crafting_unit`, which `aaas` unlocks | [ ] |
| A3 | unlock | `ae2_my_first_homelab`: Crafter recipe of `ae2:energy_acceptor` becomes AE2's `network/blocks/energy_energy_acceptor` | The stored recipe is the uncraft of the cable energy acceptor, a loop; this also makes `appflux:flux_accessor` and `advanced_ae:reaction_chamber` craftable | [ ] |
| A4 | stage | Move `quantum_crafting` from stage 8 to 9 and make it require `quantum_computer_stage_1` | The quantum crafter needs the quantum accelerator, unlocked at stage 9 | [ ] |
| A5 | unlock | Move `advanced_ae:quantum_core` from `quantum_computer` (stage 8) to `256m_quantum_storage` (stage 11) | Its recipe needs the 256M quantum storage (stage 11) and the accelerator (stage 9) | [ ] |
| A6 | unlock | Move `refinedstorage:controller`, `refinedstorage:disk_drive` and `refinedstorage:pattern_grid` from `ae2/advanced_automation_processing_ii` (stage 5) to `refine_storage/refine_storage_ae1_the_beginning_of_a_simple_storage` (stage 1) | Refined Storage items sit in an AE2 milestone, while the stage 1 to 3 Refined Storage milestones need the controller (portable grid) | [ ] |

### Mekanism

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| M1 | unlock | Move `mekanism:pressurized_reaction_chamber` from `mekanism_fundamentals` (stage 1) to `mekanism_basic_tank` (stage 2) | Its recipe needs the basic chemical tank, which `mekanism_basic_tank` unlocks | [ ] |
| M2 | unlock | Drop `minecraft:iron_ingot` from the unlocks of `mekanism_fundamentals` | A vanilla basic is not a keystone, and 37 other recipes in the dump (Create, Ender IO, Clibano...) still make it | [ ] |
| M3 | stage | Move `i_need_more_firepower_i` from stage 2 to 4; it requires `mekanism_advanced_generator` and `mekanism_advanced_tools` | Its lasers need `mekanism:laser` (stage 4) and its turret needs the electric bow (`mekanism_advanced_tools`) | [ ] |
| M4 | stage | Move `i_need_more_firepower_ii` from stage 3 to 4 | Its lasers need `mekanism:laser` (stage 4), and it follows M3 | [ ] |
| M5 | stage | Move `mekanism_advanced_tools` from stage 3 to 4; it requires `mekanism_advanced_generator` | The Meka-Tool and MekaSuit need the solar neutron activator, the HDPE elytra needs Oritech stage 4 machines | [ ] |

### Industrial Foregoing

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| I1 | unlock | Move `mycelial_halitosis`, `mycelial_meatallurgic` and `mycelial_netherstar` from `generator_tier_ii_too_many_things_to_burn` (stage 3) to `lazer_drill` (stage 4) | Their recipes need the fluid laser base that `lazer_drill` unlocks | [ ] |

### PneumaticCraft

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| P1 | unlock | Move `pneumaticcraft:liquid_compressor` from `compressor_i` (stage 2) to `fluid_i` (stage 3) | It needs the small tank that `fluid_i` unlocks | [ ] |
| P2 | unlock | Move `pneumaticcraft:thermal_lagging` from `eco_heating_technology` (stage 5) to `heat_technology_i` (stage 4) | The heat pipe and thermostat module of `heat_technology_i` need it, and `eco_heating_technology` already requires `heat_technology_i` | [ ] |

### Refined Storage

Each unlock bans only one of the recipes that make its item; the others leak.

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| R1 | unlock, ban | `pattern_grid` (after A6), `io_interractions` exporter and importer: the Crafter recipe becomes Refined Storage's own (grid + advanced processor + pattern; cable + construction or destruction core + improved processor), and every recipe of the item is banned (`refinedstorage:<item>`, the FTB cleaning recipe, the coloring recipe) | The stored recipe is the FTB "cleaning" recipe (white variant + wet sponge), so banning the rest makes the item never craftable | [ ] |
| R2 | ban | `1k_storage`: also ban `refinedstorage:1k_storage_disk_from_storage_housing`, `refinedstorage:64b_fluid_storage_disk_from_storage_housing`, `refinedstorage_mekanism_integration:64b_chemical_storage_disk_from_storage_housing` | The housing recipes make the disks with no milestone done | [ ] |
| R3 | ban | `4k_storage`: also ban `4k_storage_disk_from_storage_housing`, `4k_storage_disk_upgrade`, `256b_fluid_storage_disk_from_storage_housing`, `256b_fluid_storage_disk_upgrade` (namespace `refinedstorage`) | Same leak through housing and upgrade recipes | [ ] |
| R4 | ban | `16k_storage`: also ban `16k_storage_disk_from_storage_housing`, `16k_storage_disk_upgrade`, `1024b_fluid_storage_disk_from_storage_housing`, `1024b_fluid_storage_disk_upgrade` | Same | [ ] |
| R5 | ban | `64k_storage`: also ban `64k_storage_disk_from_storage_housing`, `64k_storage_disk_upgrade`, `4096b_fluid_storage_disk_from_storage_housing`, `4096b_fluid_storage_disk_upgrade` | Same | [ ] |

### Oritech

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| O1 | unlock, ban | `machine_i`: Crafter recipe of `centrifuge_block` becomes `oritech:crafting/centrifugealt` (bottles, copper, motors, iron blocks), and ban it too | The stored recipe needs processing units that the centrifuge itself makes; banning the alternate without this change makes 21 Oritech unlocks never craftable | [ ] |
| O2 | ban | `machine_i`: also ban `oritech:crafting/assembler` | Only `assembleralt` is banned | [ ] |
| O3 | ban | `machine_core_i`: also ban `oritech:crafting/core2alt`; `machine_core_ii`: also ban `oritech:crafting/core3` | Each core bans only one of its two recipes | [ ] |
| O4 | ban | `mining_technology`: also ban `oritech:crafting/electricfurnace` and `oritech:crafting/pulverizer` | Only the `alt` recipes are banned | [ ] |
| O5 | ban | `pipe_i`: also ban `oritech:crafting/unframe_fluid`, `oritech:crafting/unduct_fluid`, `oritech:compat/enderio/crafting/fluidpipe` and `oritech:compat/enderio/crafting/pump` | The uncraft and Ender IO compat recipes make the fluid pipe and pump with no milestone done | [ ] |

### Whole pack

| # | Kind | Fix | Reason | OK |
|---|---|---|---|---|
| X1 | deliver | Give the 166 milestones without deliveries their required items | Without them no milestone can be completed (ADR 0017); blocked on the questions below | [ ] |
| X2 | data | Clear the 158 retired `obtain` validations in the cleanup migration of ADR 0017 | They list the milestones' own unlocks and are ignored, but they read like real requirements in the editor | [ ] |
| X3 | ban | Remove the 100 item ids copied into `recipes_to_ban` next to the real recipe id | They ban nothing; the check reports them as `unknown_ban` (info) | [ ] |

## Game design questions that block generated required items

The direction (8 Nov): the Arffornia mod is the progression hub; a stage costs specific Arffornia
items made by assembly chains that take inputs from several mods; never the item a milestone
unlocks; no points or currency. To generate required items from recipes, the tool needs these
answers.

| # | Question | Recommendation | OK |
|---|---|---|---|
| Q1 | How do the 11 stages map to the Arffornia part families and machines of [spec 003](../003-machine-tier-plan.md) (10 tiers)? | Stage N = tier N-1 (stage 1 = Landfall), stages 10 and 11 share the Quantum tier. One new part family per stage, so the generator knows which components exist at each stage | [ ] |
| Q2 | What does a milestone deliver: Arffornia components only, or components plus an item of its own mod? | Both: one or two Arffornia components of its stage, plus one intermediate of its own mod made with the machines it requires (proves the player uses the mod). Never an item it unlocks | [ ] |
| Q3 | Which mods feed each component? | Each component recipe takes inputs from at least 2 mods open at the previous stage, at least one outside the milestone's graph, and uses machine outputs rather than raw resources. The generator picks them from the recipe graph and proves them with the same check | [ ] |
| Q4 | Where are component recipes defined and which machine makes them? | In the Arffornia datapack, run by the spec 003 machines (Constructor, Assembler, Foundry...), so the dump and the check see them like any other recipe. Do the machines themselves come from the Noyau module of the previous stage? Recommended yes | [ ] |
| Q5 | Milestone deliveries and the Noyau module: same items? | The module asks for the stage's flagship component in bulk (Satisfactory elevator phase); milestones ask for smaller counts of the stage's basic components | [ ] |
| Q6 | How do counts grow? | Start from a formula, about 4 times more per stage (16 at stage 1, about 16 million at stage 11 for the module), tuned in playtests on throughput, not set by hand per milestone | [ ] |
| Q7 | Magic branch: separate components or variants? | Same component, two recipes (tech chain and magic chain), as D4 of spec 017 allows; delivery lists stay single | [ ] |

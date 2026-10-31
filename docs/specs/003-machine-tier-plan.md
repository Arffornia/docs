# 003 · Machine tier plan (Satisfactory-inspired)

| | |
|---|---|
| **Status** | Proposal (footprints updated after Chantier 0: big, slow machines) |
| **Milestone** | M3 · Gameplay foundations (content lands progressively after M3) |
| **Repos** | Arffornia_Mods (machines, parts), Arffornia_Website (milestones, gates), Arffornia_Provisioning (KubeJS tweaks, mod list) |
| **Related** | Mods [#13](https://github.com/Arffornia/Arffornia_Mods/issues/13) (candidate mods) · [001](001-recipes-datapack.md) (gating) · [002](002-machine-framework.md) (machines) |

## Summary

A progression of **ten tiers**, each introducing one or two Arffornia production machines
and a family of intermediate parts, modelled on Satisfactory's chain
Smelter → Constructor → Assembler → Foundry → Refinery → Manufacturer → Blender →
Particle Accelerator → Converter/Quantum Encoder. Third-party mods enter the pack at the
tier where their power level fits, by making their key items need Arffornia parts or an
Arffornia machine. The goal is a 330-mod pack where no single mod skips the factory.
This is a **proposal**: names, numbers and placements are starting points for playtests.

## Goals

- Every tier asks for a **new machine, a new part family and more power**, like a
  Satisfactory tier.
- Each candidate mod has a clear entry tier and a short list of gated items.
- Overpowered mods (storage networks, infinite resources, huge generators) arrive late or
  are taxed in parts and power.
- Numbers live in data (recipes, `machine_stats` data map), so balance changes need no
  mod release.

## Non-goals

- Final balancing numbers. They need playtests on a preview server.
- Gating every item of 330 mods. Gate **keystones** (controllers, cores, tier-defining
  components); the rest follows through recipes that use them.
- Removing mods. That stays a pack-curation decision.

## Player experience

- Early game feels like vanilla + Create: hand-crafted Smelter and Constructor, first
  plates, rods and screws.
- Each Space Elevator delivery (phase) is a goal that consumes a lot of the newest parts
  and unlocks the next tier, as in Satisfactory, where the elevator phases gate tiers and
  milestones unlock buildings ([Satisfactory tiers](https://satisfactory.wiki.gg/wiki/Tiers),
  [milestones](https://satisfactory.wiki.gg/wiki/Milestones)).
- Mods appear as rewards: "Tier 3 unlocked: Mekanism basic machines, XNet, Modern Dynamics".
- Power is the pacing resource: a new machine is useless until the power plant grows.

## Design

### Arffornia part families (shared intermediates)

| Family | Examples | Made in | Used by |
|---|---|---|---|
| Basic | plates, rods, screws, wire, cable | Constructor | T0–T2 recipes, early mod gates |
| Structural | reinforced plate, frame, beam | Assembler | T2+ machines, storage mods |
| Alloy | steel, invar, electrum, bronze ingots (unified tags) | Foundry | T3+ |
| Motion | rotor, stator, motor | Assembler / Manufacturer | generators, Create, carts |
| Electronic | circuit, processor, computer | Assembler → Manufacturer | logistics, computers, AE2/RS |
| Chemical | plastic, rubber, acid, fuel (fluids + items) | Refinery / Blender | T5+ |
| Exotic | ender lens, void matter, quantum core | Particle Accelerator, Quantum Encoder | endgame keystones |

Parts use existing common tags (`c:plates/iron`, `c:ingots/steel`) where the pack already
has them; Almost Unified (in the pack) picks one output per tag. Arffornia adds only parts
with no common equivalent (frames, motors, circuits, exotic items).

### Tier table

Power is in FE/t. Proposed scale: **1 Satisfactory MW ≈ 10 FE/t**, then adjusted to the
pack's generators. Satisfactory figures are from the wiki building pages
([Assembler](https://satisfactory.wiki.gg/wiki/Assembler) 15 MW,
[Manufacturer](https://satisfactory.wiki.gg/wiki/Manufacturer) 55 MW,
[Blender](https://satisfactory.wiki.gg/wiki/Blender) 75 MW,
[Particle Accelerator](https://satisfactory.wiki.gg/wiki/Particle_Accelerator) 250–1500 MW variable,
[Quantum Encoder](https://satisfactory.wiki.gg/wiki/Quantum_Encoder) up to 2000 MW);
Constructor/Smelter (~4 MW), Foundry (~16 MW) and Refinery (~30 MW) are approximate.

| Tier | Theme | New Arffornia machine(s) | Shape | In → Out | FE/t | Power source expected |
|---|---|---|---|---|---|---|
| 0 | Landfall | **Smelter** (ore → ingot), **Constructor** (1 → 1) | 2×2×3 and 2×3×3 multiblocks | 1 → 1 | 40 | Create (water wheel + alternator addons) or a small burner (Arffornia "Biomass Burner" optional) |
| 1 | Workshop | — (more Constructor recipes, Space Elevator phase 1) | — | — | — | Solar Generation tier 1, Powah starter |
| 2 | Part Assembly | **Assembler** (2 → 1) | 3×5×3 multiblock | 2 → 1 | 150 | Powah basic, Solar Generation |
| 3 | Steel | **Foundry** (alloys) | 5×5×5 multiblock | 2 → 1 | 160 | Immersive Engineering diesel/steam, Powah |
| 4 | Logistics | **Packager** (fluid ↔ container), Assembler upgrades | 3×3×3 multiblock | 1 + fluid → 1 | 100 | same, more of it |
| 5 | Oil | **Refinery** (fluid chemistry) | 5×7×7 multiblock | item + fluid → item + fluid | 300 | IE diesel, Mekanism gas-burning, Oritech |
| 6 | Industry | **Manufacturer** (4 → 1) | 7×9×6 multiblock | 4 → 1 | 550 | Extreme Reactors (small), Mekanism generators |
| 7 | Control | **Blender** (2 items + 2 fluids → item + fluid) | 5×5×6 multiblock | mixed | 750 | Extreme Reactors, Powah advanced |
| 8 | Particles | **Particle Accelerator** ("Ender Collider") | ring, 15×15×5 minimum, grows with the track | 2 + fluid → 1 | 2,500–15,000 variable | Extreme Reactors turbines, Mekanism fission |
| 9 | Quantum | **Quantum Encoder**, **Converter** ("Void Converter": ore ↔ ore, exotic matter) | large multiblocks | 3 + fluid → 1 + fluid | up to 20,000 | fusion, large reactors |

Each tier ends with a Space Elevator phase that consumes the tier's flagship parts in bulk
(Satisfactory-style project parts, e.g. "Smart Plating", "Modular Engine" equivalents).

### Candidate mods (issue #13) by entry tier

All of them are in the server mod list except **Tom's Simple Storage** (only Tom's
Peripherals is present) — see D6.

| Mod | Score (#13) | Entry tier | Gated keystones (machine-only unless noted) | Why here |
|---|---|---|---|---|
| Construction Sticks | 15 | 0 | none (stage-locked in place) | building QoL, harmless |
| Create | 15 | 0 → 3 | Andesite casing (0, stage-locked), brass casing (3, needs Foundry alloy), mechanical crafter (4) | early power and motion; brass after steel |
| Solar Generation | 16 | 1 → 6 | panel tiers mapped 1, 2, 4, 6; each tier needs that tier's parts | linear, predictable power |
| Steve's Carts | 15 | 2 | cart assembler (structural parts) | fun logistics, mid power |
| Railcraft Reborn | 11 | 2 → 4 | rolling machine (2), steam/electric locomotives (4) | rail logistics; overlaps Create |
| ComputerCraft (CC: Tweaked) | 15 | 3 | computer (needs Arffornia circuit), turtle (4) | automation without game-breaking |
| Project Red | – | 3 | fabrication workbench and ICs (circuit family) | redstone logic, mid |
| Modern Dynamics | 12 | 3 | item/fluid pipes need plates/rods | basic logistics |
| Powah | 16 | 2 → 8 | energizing orb (2), reactor (6), nitro tier (8) | very strong late; tax energizing tiers |
| XNet | 19 | 4 | controller and connectors (electronic family) | strong logistics; after basic pipes |
| RFTools | 13 | 5 | builder and quarries (8), crafter (5), power cells (5) | builder/quarry skip mining: late |
| Mob Grinding Utils | 16 | 5 | mob masher, fan, absorption hopper | infinite drops: mid-late |
| Extreme Reactors | 17 | 6 → 8 | reactor controller (6), turbine controller (8) | huge FE; defines late power |
| Hostile Neural Networks | 16 | 6 | simulation chamber, loot fabricator | infinite mob loot: late |
| Extra Storage (AE2/RS addon) | 11 | 7 | high-tier disks | after the storage network tier |
| XyCraft | 18 | 3 → 7 | machines by its own tiers; tap into Foundry/Refinery parts | its own factory loop, fits theme |
| Stellaris | 15 | 8 → 9 | rocket tiers need Particle Accelerator / Quantum parts | space = endgame, matches the elevator |
| Tom's Simple Storage | 17 | 2 | storage terminal (structural parts) | early storage before AE2/RS; **not in pack** |

### Already-in-pack heavy hitters (balance targets)

| Mod | Risk | Proposal |
|---|---|---|
| Applied Energistics 2, Refined Storage | storage + autocrafting trivialise logistics | ME/RS controller at tier 6, autocrafting at tier 7; disks need electronic parts |
| Mekanism (+ Generators, Additions) | ore ×5, digital miner, teleporters | ore ×2/×3 at tiers 4/5, ×4/×5 at 7/8; digital miner tier 8; fission tier 8 |
| Industrial Foregoing, Mystical Agriculture | infinite resources | essences seeds by tier; laser drill tier 8 |
| Immersive Engineering | multiblocks overlap ours | keep as early heavy industry (tier 3–5); its steel competes with the Foundry, so route IE steel through the Foundry tag or make the coke oven feed the Foundry |
| Ender IO, Oritech, PneumaticCraft | full machine sets | entry at their natural tier; their basic machine casings need Arffornia frames |
| Mining Gadgets, Building Gadgets, Just Dire Things | skip mining/building | tier 5+ |

### Balancing principles

1. **One gate per keystone.** Gate the controller/core/casing, not every block.
2. **Parts tax, not walls.** A late mod item should cost Arffornia parts of its tier, so it
   is reachable only through the factory, not banned.
3. **Power is the throttle.** New tiers need more FE/t than the previous tier's typical
   generator gives; strong generators come one tier after the machines that need them.
4. **Machine-only for industrial items, stage-locked for basics** (spec 001 D4).
5. **No infinite resources before tier 5**; infinite = Mob Grinding, HNN, Mystical
   Agriculture high tiers, quarries.
6. **Unify first.** Almost Unified + common tags so ores and ingots from 330 mods collapse
   to one item; recipes use tags.
7. **Measure.** A datagen report lists, per tier, how many recipes and items unlock and
   the FE/t of each machine; a playtest preview server per tier change.
8. **Write it in data.** Gates in the website export, numbers in data maps, mod-specific
   tweaks in Provisioning KubeJS scripts (existing ones in `kubejs/server_scripts/02_mod_specific/`).

### Visual identity per tier

Accent colours for GUIs and machine trims (see [002](002-machine-framework.md) GUI kit):
tier 0–2 copper/orange, 3–4 steel/blue-grey, 5–6 industrial yellow, 7 teal, 8 violet,
9 white/cyan. Machines share a futuristic panel style (flat panels, light strips, vents)
rather than IE's rustic look. The final style comes from the art direction research in
[002](002-machine-framework.md#art-direction-research-next-step); Oritech's machines are the
in-pack quality bar.

## Testing

| Check | How |
|---|---|
| Every gated keystone has a recipe reachable at its tier | datagen/GameTest report walks recipes from tier-0 items and fails on unreachable keystones |
| No tier needs a machine from a later tier | same report, ordered by tier |
| Power budget per tier | report sums FE/t of a reference factory per tier vs the tier's reference generator |
| Mod gates load only when the mod is present | `neoforge:mod_loaded` on every mod-specific recipe; boot test without optional mods |
| Playtests | preview server per tier change ([ADR-0007](../decisions/0007-preview-environments.md)), scripted RCON checks |

## Migration from the current system

- Today's milestones and stages on the website stay; each gets a tier number and a
  stable `stage_key` (spec 001). The Crafter becomes the tier-0/1 universal machine for
  existing unlocks until each recipe is moved to its proper machine.
- Existing KubeJS removals in Provisioning (`recipe_removals.js`) that are progression
  gates move to the website export; unification removals stay in KubeJS.

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Number of tiers | (a) 10 (0–9, Satisfactory-like); (b) 6 compressed | **(a)**, with tiers 0–1 short |
| D2 | Machine names | (a) Satisfactory names (Constructor, Assembler…); (b) own names with Minecraft flavour (Fabricator, Assembly Bench, Ender Collider…) | **(b)** for identity, keep the role obvious; lang keys in en/fr |
| D3 | Power unit and scale | (a) FE with 1 MW ≈ 10 FE/t; (b) own unit | **(a)**: works with every generator and cable in the pack |
| D4 | Early power | (a) Create kinetic → FE; (b) an Arffornia burner; (c) both | **(c)**: a cheap burner for solo starts, Create for players who like it |
| D5 | Role of Immersive Engineering | (a) keep as tier 3–5 heavy industry beside ours; (b) reduce to parts provider | **(a)**, routed through shared tags so it feeds the Foundry |
| D6 | Tom's Simple Storage (score 17) is not in the pack | (a) add it (tier 2 storage); (b) drop it from #13 | **(a)** if a 1.21.1 NeoForge build exists, else (b) |
| D7 | Infinite resource mods | (a) gate at tier 5–6; (b) remove some | **(a)** first, decide after playtests |
| D8 | Meaning of the #13 score (x/19) | (a) priority; (b) target tier | Confirm; this plan assumes **priority** |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | Add tier numbers and stage keys to stages/milestones | Website | Each milestone has `tier` and `stage_key`; export includes them | S |
| 2 | Add tier-0 machines: Smelter and Constructor | Mods | Registered via `MachineType`; recipes in data; GUI; JEI; en/fr; GameTests | M |
| 3 | Add basic part family (plates, rods, screws, wire) with tags | Mods | Items + tags + Constructor recipes; Almost Unified config respects them | S |
| 4 | Add Assembler and structural/motion parts | Mods | Machine + parts + recipes; GameTests | M |
| 5 | Add Foundry multiblock and alloy recipes | Mods | Depends on 002 #10–12; forms; alloys via tags | M |
| 6 | Write per-mod gate lists for the 18 candidates (one sub-issue each) | Mods (#13) | Each sub-issue: NeoForge 1.21.1 availability, entry tier, keystone item ids, recipe changes | S each |
| 7 | Tier reachability and power-budget report | Mods | `runData` writes a report; CI fails on unreachable keystone or out-of-order tier | M |
| 8 | Move progression bans from `recipe_removals.js` into the website export | Provisioning + Website | Gates come from the export; KubeJS keeps unification only | S |
| 9 | Refinery, Packager, Manufacturer, Blender | Mods | One issue each, after 002 multiblocks; fluids supported | L each |
| 10 | Particle Accelerator, Quantum Encoder, Converter | Mods | One issue each; variable power profile supported by `RecipeProcessor` | L each |
| 11 | Tier art direction: accent palette, panel sprites, machine trims | Mods | Sprite sheet + palette committed; preview screen screenshots | M |

# 011 · Mod intake: bringing candidate mods into the progression

| | |
|---|---|
| **Status** | Draft: needs decisions |
| **Milestone** | M3 · Gameplay foundations (after spec 001 lands) |
| **Repos** | Arffornia_Provisioning (mod list, KubeJS), Arffornia_Website (gates), Arffornia_Mods (patches) |
| **Related** | Mods [#13](https://github.com/Arffornia/Arffornia_Mods/issues/13) (18 candidates) · [001](001-recipes-datapack.md) · [003](003-machine-tier-plan.md) (entry tiers) · the platform's compatibility pipeline (owned by the platform agent) |

## Summary

The 18 candidates of Mods #13 wait for the datapack recipe system (spec 001). **Seventeen
are already in the pack**; only Tom's Simple Storage is missing. For most of them,
"entering" means **gating their keystone items into the progression**, not adding a jar.
Each mod enters through **one content PR**. Spec 003 sets its tier and keystones. The PR
must pass the compatibility checks that the platform agent's pipeline runs. A skill also
proposes new mods, with care because the pack already has about 330.

## Content PR (one per mod)

| Part | Where | Content |
|---|---|---|
| Sub-issue | Mods #13 child | mod, version for NeoForge 1.21.1, entry tier, keystones, risks |
| Gates | website export (spec 001) | machine-only or stage-locked gates for the keystones, with the milestone |
| Recipe changes | KubeJS in Provisioning (`kubejs/server_scripts/02_mod_specific/<mod>.js`) | parts tax (spec 003), unification |
| Jar (only if new) | `config/*/modList.json` | CurseForge or Modrinth id, pinned file id, both server and launcher sides |
| Config | `config/*/storage/config/<mod>` | balance values (e.g. Powah generation) |
| Test guide | PR body | what changed, what to try in game, what to look at |

### Checks every content PR must pass

The platform agent owns the tooling. This list is what the game side requires:

1. **Version resolution**: the mod's declared dependencies resolve to the pack's
   versions; no duplicate mod ids; client/server sides correct.
2. **Boot**: a full-pack dedicated server reaches "Done" with the datapack and KubeJS
   scripts. It fails on any recipe parse error, unknown item or tag, or KubeJS error.
3. **Reachability report** (spec 003): every gated keystone is craftable at its tier, and no
   tier needs a later machine.
4. **Client boot** with the launcher's mod list (nightly harness, M2).
5. **Preview environment** with Brian's one-command start (ADR-0007), using the test guide.

Only one full-pack environment can run at a time (homelab limit), so content PRs queue
for it. Single-mod checks (1) run without the full pack.

### Patching incompatibilities

When two mods conflict, fix it in the lightest layer that works:

| Layer | Use for | Example |
|---|---|---|
| Config | numbers, toggles | lower a generator's output |
| KubeJS (server scripts) | recipes, tags, loot | remove a recipe that skips a tier |
| Datapack (spec 001) | gates, recipe overrides | stage-lock a keystone |
| **Arffornia patches mod** | code fixes and mixins | a crash between two mods, a missing capability |

The last layer follows what FTB does for its packs: the pack already ships **FTB XMod
Compat** and **FTB Pack Companion**, small pack-specific mods that carry cross-mod fixes.
Arffornia gets the same: an `arffornia-patches` module (separate jar, so a broken patch
can be removed without touching the main mod). Each patch has a test and a note "remove
when <mod> ≥ <version>".

### Proposing new mods (skill)

A `mod-scout` skill in the Arffornia agent-kit layer:

- Input: a need ("early-game logistics", "a fun endgame project") or a mod name.
- Checks: NeoForge 1.21.1 build exists; licence allows modpack use (CurseForge
  third-party distribution flag, or Modrinth); **overlap with the ~330 mods already in the
  pack** (refuses a mod that duplicates an existing role without a strong reason); size;
  update activity; known conflicts.
- Output: a one-page proposal with the entry tier and keystones, opened as a
  `needs-decision` issue. It never adds a mod by itself.
- Runs on demand only (token budget).

## Candidate list (from #13, entry tiers from spec 003)

| Mod | In pack | Entry tier | Keystones to gate |
|---|---|---|---|
| XNet | yes | 4 | controller, connectors |
| XyCraft | yes | 3 → 7 | its machine casings |
| Extreme Reactors | yes | 6 → 8 | reactor and turbine controllers |
| Tom's Simple Storage | **no** | 2 | storage terminal (needs a 1.21.1 NeoForge build) |
| Hostile Neural Networks | yes | 6 | simulation chamber, loot fabricator |
| Powah | yes | 2 → 8 | energizing orb, reactor, nitro tier |
| Mob Grinding Utils | yes | 5 | mob masher, fan |
| Solar Generation | yes | 1 → 6 | panels per tier |
| CC: Tweaked | yes | 3 | computer, turtle |
| Steve's Carts | yes | 2 | cart assembler |
| Construction Sticks | yes | 0 | none (stage-locked in place) |
| Create | yes | 0 → 3 | brass casing, mechanical crafter |
| Stellaris | yes | 8 → 9 | rocket tiers |
| RFTools | yes | 5 → 8 | builder, quarries, crafter |
| Modern Dynamics | yes | 3 | pipes |
| Extra Storage | yes | 7 | high-tier disks |
| Railcraft Reborn | yes | 2 → 4 | rolling machine, locomotives |
| Project Red | yes | 3 | fabrication workbench, ICs |

Order: one mod per content PR, lowest tier first, so each preview session tests a small,
playable step.

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Patch layer | (a) separate `arffornia-patches` jar; (b) patches inside the main mod | **(a)** |
| D2 | Mod scout | (a) skill on demand; (b) monthly automatic scan | **(a)** (token budget rule) |
| D3 | Tom's Simple Storage | (a) add if a NeoForge 1.21.1 build exists; (b) drop | **(a)** else (b) |
| D4 | Content PR granularity | (a) one mod per PR; (b) one tier per PR | **(a)**: smaller previews, easier revert |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | Content PR template and test-guide template | Provisioning | Template used by the first candidate PR | S |
| 2 | 18 sub-issues of #13 with tier and keystones | Mods | One issue each, `needs-decision` where the tier is unclear | S |
| 3 | `arffornia-patches` module skeleton | Mods | Builds a separate jar; one sample patch with a test | M |
| 4 | `mod-scout` skill | agent-kit | Produces a proposal issue for a sample request | S |

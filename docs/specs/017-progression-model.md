# 017 · Progression model: paliers, steps per mod, Noyau modules

| | |
|---|---|
| **Status** | Draft: needs decisions |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Website (store, API, editor), Arffornia_Mods (gating, detection, Noyau), docs (schema) |
| **Related** | Initiatives [#27](https://github.com/Arffornia/docs/issues/27) (game design), [#28](https://github.com/Arffornia/docs/issues/28) (graph tooling), [#29](https://github.com/Arffornia/docs/issues/29) (gating), [#32](https://github.com/Arffornia/docs/issues/32) (UI) · [001](001-recipes-datapack.md) · [003](003-machine-tier-plan.md) · Mods [#16](https://github.com/Arffornia/Arffornia_Mods/issues/16), [#18](https://github.com/Arffornia/Arffornia_Mods/issues/18) |

## Summary

One data model for the whole progression, read by the website editor and viewer, the in-game
UI, the mod's gating and the graph tool. It replaces stages and milestones with **paliers**
(global tiers) and **steps** (one unlockable part of one mod). A progression passes a palier
when it has done about 80 % of the palier's steps and built the palier's **Noyau module**. The
model is versioned: the editor works on a draft, a publish freezes a snapshot, and the datapack
and the game always run a known snapshot.

This spec is the root of phase 1: the UI framework, the gating prototype and the graph tool all
consume this model. Design decisions behind it: game design study v3
([docs#27](https://github.com/Arffornia/docs/issues/27)) and the decision on Mods #16.

## Goals

- One model and one JSON Schema shared by the website, the mod and the graph tool.
- A player always knows where they are: percentage per palier, next steps, next module.
- Mods are never unlocked whole: each mod is a **track** of steps spread over paliers by power.
- No points and no currency: paliers cost Arffornia items made by Arffornia chains.
- Hotfix without reconnect: publish a snapshot, reload, connected players get it (spec 001).
- Machine-checkable: the graph tool can prove every step is reachable at its palier.

## Non-goals

- The content itself: which steps exist and where they go. That is the graph tool's job (#28).
- The UI design. Initiative #32 builds the viewer and editor on this model.
- Machine recipes and the datapack format: spec 001 stays the reference.

## Player experience

- The graph shows paliers as bands. Each band shows `done / total` and a percentage, e.g.
  `Palier 3 · 14 / 18 · 78 %`, and the Noyau module of that palier with its delivery bar.
- A step is a card: mod icon, title, its key items, what it opens. Locked, available or done.
- Passing a palier: when the band reaches the threshold and the module is complete, the
  next palier opens for the whole progression (team or solo), with a toast for every member.
- Leftover steps of a passed palier stay available. They are optional, not lost.
- Pacing comes in waves: the editor shows each step's effort so long steps are mixed with short ones.

## Design

### Vocabulary

| Term | Meaning | Replaces |
|---|---|---|
| **Palier** | A global tier, numbered from 0. Has a threshold (default 0.8) and a Noyau module | `stages` |
| **Track** | The steps of one mod, or of one Arffornia branch (tech, magic) | `progression_graphs` categories |
| **Step** | One unlockable part of a track, placed on one palier. Has a stable key | `milestones` |
| **Gate** | What a step opens: recipes disabled, wrapped by an Arffornia ingredient, or stage-locked (spec 001) | `milestone_unlocks` |
| **Validation** | How a step is completed: obtain a key item, or deliver items | `milestone_requirements` |
| **Noyau module** | The palier's Arffornia build: a list of Arffornia items and counts to deliver to the Noyau | new |
| **Snapshot** | A published, immutable version of the whole model | new |

### Rules

1. A step belongs to exactly one track and one palier, and may require other steps (any track).
2. A step is **available** when its palier is open and its required steps are done.
3. A step is **done** when its validation is met by any member of the progression.
4. `palier_progress = done steps of the palier / steps of the palier`, counted raw (no weights).
5. Palier N+1 opens when `palier_progress(N) >= threshold(N)` **and** the module of N is complete.
6. Gates of a step apply from the moment the step is done, for the whole progression.
7. A step can only require steps on its palier or earlier. The graph tool and a schema check enforce it.

### Validation types

| Type | Done when | Detected by |
|---|---|---|
| `obtain` | A member obtains one of the key items or tags | A generated advancement with an `inventory_changed` criterion (works for every mod, no hooks) |
| `craft` | A member crafts one of the key items | Advancement `recipe_crafted`, or the machine output event for Arffornia machines |
| `deliver` | The listed items and counts were delivered to the Noyau or the Space Elevator | Arffornia block entity, idempotent per delivery |

`deliver` keeps today's milestone requirements working during the migration.

### Data model (website store)

| Table | Columns (main) |
|---|---|
| `model_snapshots` | `id`, `version` (int, increasing), `status` (`draft`/`published`/`archived`), `schema_version`, `published_at`, `published_by`, `notes` |
| `paliers` | `snapshot_id`, `number`, `name` (i18n JSON), `threshold` (decimal, default 0.8), `module` (JSON: `[{item, count}]`) |
| `tracks` | `snapshot_id`, `key` (e.g. `mekanism`), `name` (i18n), `mod_id` (nullable), `branch` (`tech`/`magic`/`neutral`), `icon_item` |
| `steps` | `snapshot_id`, `key` (e.g. `mekanism/ore_x3`), `track_key`, `palier_number`, `title` / `description` (i18n), `validation` (JSON), `gates` (JSON), `requires` (JSON list of step keys), `effort` (int, from the tool), `power` (JSON metrics, from the tool), `source` (`manual`/`tool`), `layout` (JSON x/y per view) |
| `progression_steps` | `progression_id`, `step_key`, `completed_at`, `completed_by` (player uuid), unique (`progression_id`, `step_key`) |
| `progression_paliers` | `progression_id`, `palier_number`, `opened_at` |
| `progression_deliveries` | `progression_id`, `palier_number`, `item`, `count` (bigint) |
| `progression_events` | append-only log: `step_completed`, `palier_opened`, `module_delivered`, with actor and time (feeds toasts, streaks, stats) |

Progression state stores **step keys**, never row ids, so a new snapshot does not break it. A
step removed in a later snapshot stays in history and stops counting.

### One schema, three consumers

- `progression-model.schema.json` (JSON Schema 2020-12) lives in the docs repo next to this spec
  and is vendored by the website, the mod (tests) and the graph tool.
- The website exports a snapshot as one JSON document that validates against it. The datapack of
  spec 001 is generated from the same snapshot: gates become recipe overrides, validations
  become advancements.
- CI in each repo validates fixtures against the schema, so a field change breaks the build, not the game.

### API

| Route | Who | Purpose |
|---|---|---|
| `GET /api/progression/model` (`?version=`) | public, ETag | The published snapshot as JSON. The UI and the mod cache it by version |
| `GET /api/progressions/{id}/state` | public | Done steps, open paliers, percentages, deliveries, next steps |
| `POST /api/progressions/{id}/events` | service `progression_editor` | `step_completed` / `module_delivered`, idempotent by (progression, step key) or delivery id |
| `GET/PUT /api/progression/drafts/{id}` | admin | Editor reads and writes a draft |
| `POST /api/progression/drafts/{id}/validate` | admin | Schema + rules 1–7 + reachability report from the graph tool when available |
| `POST /api/progression/drafts/{id}/publish` | admin | Freezes the draft as the next version, regenerates the datapack, the mod reloads on command (spec 001) |

The old `/stages`, `/milestones` and `/progression/*` routes stay until the mod and the
launcher move to the new ones, then are removed in one PR per client.

### In game

- The world is the runtime authority, the website the system of record (spec 001 unchanged):
  the mod keeps the progression's done steps and open paliers in `SavedData`, synced to members,
  and reports events to the API. A website outage never locks or unlocks anything.
- Detection never calls HTTP on a hot path: advancements fire, the mod records the step locally,
  then sends the event in the background with retry.
- Machines check the palier of the progression they were placed for (decision on Mods #18).

### Scale

The real size is measured by the phase 1 recipe extraction spike. Working assumption: 300+ mods,
a few thousand steps, a model JSON of a few MB. The model endpoint is cached by version and
compressed; the viewer loads one palier band at a time if needed.

## Testing

| Check | How |
|---|---|
| Schema | Fixtures valid and invalid, in every repo's CI |
| Rules 1–7 | Website unit tests on the validator; a step requiring a later palier fails |
| Idempotent events | Feature tests: replayed and reordered `step_completed` change nothing |
| Palier opening | Feature test: 79 % stays closed, 80 % plus module opens, team members all see it |
| Detection | Mod GameTests: obtaining a key item completes the step for the team; a non-member does not |
| Snapshot switch | Publish v2 while players are online: state kept, removed steps stop counting, no reconnect |
| Migration | The current prod tree converts with zero schema errors; a report lists what needs a human |

## Migration

1. Snapshot v1 is generated from today's data: stages → paliers, milestones → steps (track from
   the graph category, or `arffornia` when none), closure links → `requires`, requirements →
   `deliver` validation, unlocks → gates, recipes → Arffornia machine recipes (spec 001).
2. Each progression's `completed_milestones` becomes `progression_steps`; `max_stage_id` becomes
   the open paliers.
3. The AI skill of initiative #28 later rewrites v1 into the real per-mod tracks, as a draft that
   Brian reviews and publishes.

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Validation types | (a) obtain, craft and deliver; (b) deliver only, like today | **(a)**: obtaining or crafting a key item is how players discover a mod; deliver stays for the Noyau feel |
| D2 | Versioned snapshots with draft and publish | (a) yes; (b) edit live data as today | **(a)**: needed for tests, AI drafts, rollback and hot reload |
| D3 | Threshold per palier | (a) one global 0.8; (b) per palier, default 0.8 | **(b)**: lets early paliers ask 100 % of a short tutorial list |
| D4 | One Noyau, or one per branch | (a) one Noyau, each module may accept tech or magic variants; (b) a Noyau per branch | **(a)**: one goal per palier keeps teams together |
| D5 | Where the schema lives | (a) docs repo, vendored; (b) website repo | **(a)**: it is a contract between repos, like the specs |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | JSON Schema `progression-model.schema.json` with fixtures | docs | Valid and invalid fixtures; CI validates them | S |
| 2 | Store: snapshot, palier, track, step tables and models | Website | Migrations, factories, rules 1–7 validator with unit tests | M |
| 3 | Progression state tables and idempotent events endpoint | Website | Feature tests for replay, reorder, palier opening, team scope | M |
| 4 | Model and state read endpoints with ETag | Website | Contract tests; snapshot JSON validates against the schema | S |
| 5 | Draft, validate and publish endpoints | Website | Publish freezes a version and triggers the datapack build (spec 001 task) | M |
| 6 | Migration command from stages and milestones to snapshot v1 | Website | Prod copy converts with zero schema errors; report of manual items | M |
| 7 | Mod: step store, advancement-based detection, event sender with retry | Mods | GameTests for obtain and craft, team scope, offline API | L |
| 8 | Mod: palier check for machine formation and gates | Mods | GameTest: a machine of palier N+1 does not form at N | S |

# 017 · Progression model: stages, milestones per mod graph, Noyau modules

| | |
|---|---|
| **Status** | Accepted (Brian, 8 Nov 2026) |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Website (store, API, editor), Arffornia_Mods (gating, Space Elevator, Noyau), docs (schema) |
| **Amended** | 23 Nov 2026: one completion path, the Space Elevator ([ADR 0017](../../decisions/0017-milestones-complete-in-the-space-elevator.md)) |
| **Related** | Initiatives [#27](https://github.com/Arffornia/docs/issues/27) (game design), [#28](https://github.com/Arffornia/docs/issues/28) (graph tooling), [#29](https://github.com/Arffornia/docs/issues/29) (gating), [#32](https://github.com/Arffornia/docs/issues/32) (UI) · [001](../001-recipes-datapack.md) · [003](../003-machine-tier-plan.md) · Mods [#16](https://github.com/Arffornia/Arffornia_Mods/issues/16), [#18](https://github.com/Arffornia/Arffornia_Mods/issues/18) |

## Summary

Brian's progression already has the right shape: **stages** (global tiers, as in Satisfactory),
**milestones** spread over the stages, and **one graph per mod** (Mekanism, AE2, Create...). This
spec keeps those names and those tables, and adds what the game design study decided:

- A progression passes a stage when it has done about **80 % of the stage's milestones**, counted
  raw, and built the stage's **Noyau module**.
- Each milestone lists the items to **deliver** in the Space Elevator and what it **gates**. Delivery
  is the only way to complete it ([ADR 0017](../../decisions/0017-milestones-complete-in-the-space-elevator.md)).
- The model is **versioned**: the editor works on a draft, a publish freezes a numbered snapshot,
  and the datapack and the game always run a known snapshot.
- One **JSON Schema** is shared by the website, the mod and the graph tool.

This spec is the root of phase 1: the UI framework, the gating prototype and the graph tool all
read this model.

## Goals

- Keep Brian's vocabulary and his current tree; extend, do not replace.
- A player always knows where they are: percentage per stage, next milestones, next module.
- Mods are never unlocked whole: each mod graph spreads its milestones over stages by power.
- No points and no currency: stages cost Arffornia items made by Arffornia chains.
- Hotfix without reconnect: publish a snapshot, reload, connected players get it (spec 001).
- Machine-checkable: the graph tool proves every milestone is reachable at its stage.

## Non-goals

- The content itself. The graph tool (#28) proposes it, Brian decides.
- The UI design. Initiative #32 builds the viewer and editor on this model.
- Machine recipes and the datapack format: spec 001 stays the reference.

## The current tree (31 Jul 2026 backup)

The latest export, [`current-tree-2026-07-31.json`](current-tree-2026-07-31.json), is the first
fixture of every test. It is **an example of the intent, not a target**: Brian built it during
development, it was never played, and the v2 graph is free to do better. It shows the kind of
milestones he wants and how mods spread over stages. What it contains:

| | Count |
|---|---|
| Stages | 11 |
| Graphs (one per mod) | 12: Mekanism, AE2, Oritech, Integrated Dynamics, Pneumatic Craft, Refined Storage, Industrial Foregoing, Green thumb, Just Dire Things, Create, EnderIO, Pneumatic Tool |
| Milestones | 194 |
| Unlocks (gated items) | 701, each with a Crafter recipe; 802 original recipes banned |
| Requirements (items to deliver) | 76, on 28 milestones |
| Links | 240 |

How the milestones spread (graph × stage) shows the intent: AE2 runs from stage 1 to 11, Mekanism
stops at 8, Industrial Foregoing at 4, Create and EnderIO only have their first milestone. This is
exactly the "a powerful mod spreads over many stages" rule.

What a first lint finds, before any tool exists:

| Finding | Count | Example |
|---|---|---|
| Links to a deleted milestone | 43 | closure rows whose milestone no longer exists |
| A milestone requires one from a **later** stage | 5 | Green thumb: *Tier 1* (stage 2) requires *Infusion Crystal* (stage 3); *Tier 4* (stage 5) requires four stage-6 milestones |
| Cross-graph link | 1 | Pneumatic Craft *Tube Technology I* (stage 2) requires Pneumatic Tool *Pneumatic Tool I* (stage 1): allowed, listed for review |
| Milestones with the placeholder description | 193 | "A new adventure begins..." |
| Stages with placeholder names | 3 | stage 1 "Cedrick Veum" (seed data) |

These are the cases the static checks of #28 must catch. Run them with `make progression-lint`:
[`scripts/progression.py`](https://github.com/Arffornia/docs/blob/main/scripts/progression.py)
converts the backup into a snapshot that follows
[`progression-model.schema.json`](progression-model.schema.json), then lints it. Today it reports
43 dangling links (dropped), 5 `requires_later_stage` errors, 166 milestones with nothing to
deliver (`no_validation`, ADR 0017), and 1 cross-graph link.

The recipe-level check goes further: it replays the tree on the full recipe dump of the pack and
says, per milestone, whether the stages open at that point can make what it unlocks. Results and
rules: [Completability of the current tree](completability.md) (`make progression-check DUMP=<dir>`).

## Player experience

- The graph shows stages as bands. Each band shows `done / total` and a percentage, e.g.
  `Stage 3 · 14 / 18 · 78 %`, and the Noyau module of that stage with its delivery bar.
- A milestone card: mod icon, title, how to deliver, what it unlocks. Locked, available or done.
- Passing a stage: when the band reaches the threshold and the module is complete, the next stage
  opens for the whole progression (team or solo), with a toast for every member.
- Leftover milestones of a passed stage stay available. They are optional, not lost.
- Pacing comes in waves: the editor shows each milestone's effort so long ones mix with short ones.

## Design

### Vocabulary (unchanged names, new meaning in bold)

| Term | Meaning | Table |
|---|---|---|
| **Stage** | A global tier, numbered from 1. **Has a threshold (default 0.8) and a Noyau module** | `stages` |
| **Graph** | The milestones of one mod, or of one Arffornia branch (tech, magic). **Knows its mod id and branch** | `progression_graphs` |
| **Milestone** | One unlockable part of a graph, placed on one stage. **Has a stable key** | `milestones` |
| **Link** | "This milestone requires that one" | `milestone_closure` |
| **Unlock** | What a milestone opens: recipes disabled, wrapped by an Arffornia ingredient, or locked (spec 001) | `milestone_unlocks` |
| **Requirement** | Items to deliver in the Space Elevator to complete the milestone | `milestone_requirements` |
| **Noyau module** | New: the stage's Arffornia build, a list of Arffornia items and counts | `stages.module` |
| **Snapshot** | New: a published, immutable version of the whole model | `model_snapshots` |

### Rules

1. A milestone belongs to one graph and one stage, and may require other milestones of any graph.
2. A milestone can only require milestones on its stage or an earlier one.
3. A milestone is **available** when its stage is open and its required milestones are done.
4. A milestone is **done** when a member of the progression targets it and delivers its requirements
   in the Space Elevator. Nothing else completes it (ADR 0017).
5. `stage_progress = done milestones of the stage / milestones of the stage`, counted raw.
6. Stage N+1 opens when `stage_progress(N) >= threshold(N)` **and** the module of N is complete.
7. Unlocks of a milestone apply from the moment it is done, for the whole progression.
8. Module deliveries count only for the module of the highest open stage, the one whose delivery
   opens the next stage; the server rejects any other (`stage_not_current`). By design a module needs
   items and machines unlocked at its own stage, as in Satisfactory, so delivering ahead is impossible
   in normal play; the rule is a safety net against bugs and tampered clients (Brian, 21 Nov 2026).
   The graph tool ([#28](https://github.com/Arffornia/docs/issues/28)) must prove that each stage's
   module cannot be crafted before that stage opens.

### How a milestone is completed

One path only, as with Satisfactory's Space Elevator (Brian, 23 Nov 2026,
[ADR 0017](../../decisions/0017-milestones-complete-in-the-space-elevator.md)):

1. A member selects an **available** milestone (rule 3) as the progression's target.
2. They deposit its requirements in the Space Elevator. The delivery completes it.

Owning or crafting an item before never counts, and neither does producing what the milestone
unlocks. A milestone without requirements cannot be completed by players; the validator warns
(`no_validation`). The admin command `/arffornia progression add <player> <id>` stays and obeys
rule 3. In the snapshot, `validation` is `{"type": "deliver", "items": [...]}` or `null`.

Until 23 Nov 2026 this section also listed `obtain` and `craft` validations, detected through one
hidden advancement per milestone in the generated datapack. That detection is removed.

### Data model (website store)

Existing tables gain columns; only the snapshot and state tables are new.

**As built (Website#149, 21 Nov 2026).** The editable tables are the one working draft, and a
published snapshot is a frozen JSON document in `model_snapshots` (`document`, `etag` = its sha256),
instead of a `snapshot_id` on every row: no copy of the tree per version, and the editor keeps
working on the same tables. Rolling back is a `PUT` of an old snapshot into the draft, then a publish.
`progression_events` also stores `snapshot_version`. Spec 019 added `progressions.is_public` (default
true) and `player_playtime` (one row per player and day).

| Table | Change |
|---|---|
| `model_snapshots` | new: `version`, `status` (`draft`/`published`/`archived`), `schema_version`, `published_at`, `published_by`, `notes` |
| `stages` | + `snapshot_id`, `threshold` (decimal, default 0.8), `module` (JSON `[{item, count}]`), `name` and `description` become i18n |
| `progression_graphs` | + `snapshot_id`, `key` (e.g. `mekanism`), `mod_id` (nullable), `branch` (`tech`/`magic`/`neutral`) |
| `milestones` | + `snapshot_id`, `key` (e.g. `mekanism/ore_x3`), `validation` (JSON, unused since ADR 0017: deliveries come from `milestone_requirements`), `effort` and `power` (from the tool), `source` (`manual`/`tool`); `x`, `y` stay |
| `milestone_closure`, `milestone_unlocks`, `milestone_requirements`, `recipes` | + `snapshot_id` through their milestone; unlock gains `gate_mode` (spec 001) |
| `progression_milestones` | new: `progression_id`, `milestone_key`, `completed_at`, `completed_by`, unique pair |
| `progression_deliveries` | new: `progression_id`, `stage_number`, `item`, `count` (bigint) |
| `progression_events` | new, append-only: `milestone_completed`, `stage_opened`, `module_delivered`, with actor and time |

Progression state stores **milestone keys**, never row ids, so a new snapshot does not break it. A
milestone removed in a later snapshot stays in history and stops counting.
`progressions.completed_milestones` and `max_stage_id` are migrated into the new tables.

### One schema, three consumers

- [`progression-model.schema.json`](progression-model.schema.json) (JSON Schema 2020-12) lives in this folder and is vendored by the
  website, the mod tests and the graph tool. The current tree, converted, is its first fixture.
- A snapshot may carry its viewer `layout` (`arffornia.progression-layout/1`): node positions, routed links and stage columns computed once (spec 018 §3), so the website and the game draw the same graph without laying it out.
- The website exports a snapshot as one JSON document. The datapack of spec 001 is generated from
  the same snapshot: unlocks become recipe overrides. It holds no advancements.

### API

| Route | Who | Purpose |
|---|---|---|
| `GET /api/progression/model` (`?version=`) | public, ETag | The published snapshot. The UI and the mod cache it by version |
| `GET /api/progressions/{id}/state` | public | Done milestones, open stages, percentages, deliveries, next milestones |
| `POST /api/progressions/{id}/events` | service `progression_editor` | `milestone_completed` / `module_delivered`, idempotent by (progression, key) or delivery id |
| `GET/PUT /api/progression/drafts/{id}` | admin | Editor reads and writes a draft; `{id}` is `current`, the one working draft |
| `POST /api/progression/drafts/{id}/validate` | admin | Schema, rules 1–7, reachability report from the graph tool when available |
| `POST /api/progression/drafts/{id}/publish` | admin | Freezes the next version, regenerates the datapack, the mod reloads on command (spec 001). Schema errors always block; rule errors block unless `accept_rule_errors` |
| `GET /api/players/{uuid}/progression/state` | public | State of the player's active progression |
| `PUT /api/progressions/{id}/visibility` | member, admin | Public or private (spec 019); a private state is shown to members, admins and the game server only |
| `POST /api/players/playtime` | service `progression_editor` | Daily playtime total per player (spec 019) |
| `GET /api/stats/progression` | admin | Progressions per stage, median time to open each stage, completion rate per milestone |

Events are sent as `{"events": [{"id", "type", "milestone" \| "stage" + "item" + "count", "occurred_at" (ms), "actor"}]}`,
at most 100 per call; the answer gives a status per event (`applied`, `duplicate`, `rejected` with a
reason) and the new state.

The current `/stages`, `/milestones` and `/progression/*` routes stay until the mod and the
launcher move to the new ones, then are removed in one PR per client.

### In game

- The world is the runtime authority, the website the system of record (spec 001 unchanged).
  The mod keeps done milestones and open stages in `SavedData`, synced to members, and sends
  events in the background with retry. A website outage never locks or unlocks anything.
- Machines check the stage of the progression they were placed for (decision on Mods #18).

## Testing

| Check | How |
|---|---|
| Schema | Valid and invalid fixtures, starting with the converted current tree, in every repo's CI |
| Rules | Validator unit tests; the 5 backward links of the current tree are reported |
| Idempotent events | Replayed and reordered `milestone_completed` change nothing |
| Stage opening | 79 % stays closed; 80 % plus module opens; all team members see it |
| Completion | Mod GameTests: delivering the target's requirements completes it for the team, not for others; owning or crafting an item completes nothing |
| Snapshot switch | Publish v2 with players online: state kept, removed milestones stop counting, no reconnect |
| Migration | The current tree converts with zero schema errors; a report lists what needs Brian |

## Migration

1. Snapshot v1 = today's data with the new columns: keys generated from graph and milestone
   names, `deliver` validation where requirements exist, none otherwise (Brian adds the items to
   deliver), threshold 0.8, empty modules.
2. Each progression's `completed_milestones` becomes `progression_milestones`.
3. The 43 dangling links are dropped and listed; the 5 backward links are reported for Brian.
4. The AI skill of #28 later works on drafts from v1: it reads Brian's graphs to learn the kind of
   milestones he wants, fixes, completes and extends them to the rest of the pack.

## Decisions

| # | Question | Decision |
|---|---|---|
| D1 | Validation types | deliver only, in the Space Elevator (Brian, 23 Nov 2026, ADR 0017). Was obtain, craft and deliver |
| D2 | Versioned snapshots with draft and publish | yes |
| D3 | Threshold | per stage, default 0.8, so early stages can ask 100 % of a short list |
| D4 | One Noyau or one per branch | one Noyau; a module may accept tech or magic variants |
| D5 | Where the schema lives | this docs folder, vendored by the other repos |
| D6 | Names | keep stage, milestone and graph (Brian, 8 Nov 2026); "palier" and "step" from the study are the same things |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | JSON Schema with fixtures, the current tree converted as the first one | docs | Done: `progression-model.schema.json`, tests in `scripts/test_progression.py` | S |
| 2 | Lint script on the current tree (rules 1–2, dangling links, cycles) | docs | Done: `make progression-lint` | S |
| 3 | Store: snapshot table and new columns | Website | Migrations, factories, rules validator with unit tests. Done in Website#149 | M |
| 4 | Progression state tables and idempotent events endpoint | Website | Feature tests for replay, reorder, stage opening, team scope. Done in Website#149 | M |
| 5 | Model and state read endpoints with ETag | Website | Contract tests; snapshot JSON validates against the schema. Done in Website#149 | S |
| 6 | Draft, validate and publish endpoints | Website | Publish freezes a version and triggers the datapack build. Done in Website#149, except the datapack: it is still built from the live tables, keyed by row id (needs a mod change) | M |
| 7 | Migration command to snapshot v1 | Website | Current tree converts with zero schema errors; report of manual items. Done in Website#149: `php artisan progression:snapshot-v1 [--dry-run]`; on the 31 Jul tree it matches `progression.py convert` | M |
| 8 | Mod: milestone store, Space Elevator completion, event sender with retry | Mods | GameTests for delivery, team scope, offline API. Hidden-advancement detection shipped in Mods#79 and is removed (ADR 0017) | L |
| 9 | Mod: stage check for machine formation and unlocks | Mods | GameTest: a machine of stage N+1 does not form at N | S |

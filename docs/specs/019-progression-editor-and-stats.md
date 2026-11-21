# 019 · Progression editor, player view and statistics

| | |
|---|---|
| **Status** | Accepted (decisions by Brian, 21 Nov 2026) |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Website (editor, player view, stats, API), Arffornia_Mods (events, in-game editing commands), docs (graph tool) |
| **Related** | Initiatives [#28](https://github.com/Arffornia/docs/issues/28) (graph tool), [#32](https://github.com/Arffornia/docs/issues/32) (UI) · [017](017-progression-model/spec.md) (model, draft and publish) · [018](018-ui-framework.md) (one graph component, D2 web) |

## Summary

Spec 017 defines the progression model and spec 018 decided that the graph is one web component,
shown on the website and in game. This spec says **what the editor does** for admins and
moderators, what **players see on the website**, and which **statistics** the site shows.

The current editor on `/stages` is the starting point: every action it has today is kept. The new
editor adds draft and publish, bulk editing, recipe-aware pickers, inline checks from the graph tool,
and suggestions from that tool that Brian accepts or rejects.

## Goals

- Brian builds and fixes a full pack graph faster and with fewer mistakes than by hand today.
- Every change goes through a draft, is checked, and is published as a numbered snapshot (017).
- The graph tool of #28 proposes; the editor shows its proposals and its errors where they apply.
- A player sees their own progress tree on the website, the same component as in game.
- Admins see where players stall and what a publish changed.

## Non-goals

- The graph content itself: the graph tool proposes it, Brian decides (#28).
- The visual design of the component: spec 018 and the validated prototype v5.
- Real-time co-editing by several admins at once. One editor per draft is enough for now.

## The current editor (website `main`, 21 Nov 2026)

Page `/stages` (`public/js/stages.js`, `StagesController`), admin role, API under `auth:sanctum`.

| Area | What Brian has today | Kept in the new editor as |
|---|---|---|
| Graph list | Sidebar of graphs grouped by category, search on graph and category names, last graph remembered | Same, plus search on milestones and items (see "Search") |
| Graphs | Add, edit, delete a graph: name, icon, categories | Same, plus `key`, `mod_id`, `branch` from 017 |
| Stages | Add a stage: name, description, reward points; delete a stage | Same, plus threshold and Noyau module; reward points are removed (no points, 017) |
| Modes | View, add node, delete node, link, unlink by clicking a link, move by dragging | Same tools, plus multi-select and keyboard shortcuts |
| Milestone panel | Click a node: name, description, stage, reward points, unlocks and requirements with icons | Same panel, plus validation type, key items, effort, power, checks |
| Milestone edit | Edit, save, cancel: name, description, points, stage number | Same, inside the draft |
| Unlocks | Add, edit, delete: item id, display name, image path, recipes to ban, shop price | Same, with an item picker from the recipe dump; shop price removed (Q3) |
| Recipe of an unlock | Ingredients, results, energy, time | Same, with a recipe picker that shows the real recipe from the dump |
| Requirements | Add, edit, delete: item id, display name, image path, amount | Same, with the item picker |
| Data | Export and import the whole tree as JSON | Export and import a snapshot as JSON (017 schema) |
| View | Pan, reset view, resize to window | Pan, zoom, fit, minimap |
| In game | `/arffornia progression addunlock`, `setrequirements`, `moveitem`, migration batch of recipes | Kept: they write into the current draft instead of the live tree |

What is missing today: no draft, every click writes the live tree; no undo; no check that a recipe
exists or that a milestone is reachable; free-text item ids and image paths; one graph at a time; no
history of who changed what.

## Editor features

Priorities: **must** for the first release, **should** soon after, **could** later.

### Drafts and publishing (017)

| Feature | Priority | Notes |
|---|---|---|
| Open a draft from the published snapshot, edit, save | must | Nothing is live until publish |
| Validate: schema, rules 1 to 7, completability | must | Same checks as `make progression-lint` and `progression-check` |
| Publish with a note; the datapack is rebuilt (spec 001) | must | Refused while there are errors; warnings need a confirmation |
| Diff between two snapshots or draft vs published | must | Added, removed, moved milestones; changed unlocks and links; as a list and highlighted on the graph |
| Roll back: open a draft from any older snapshot | should | A new version, never a rewrite of history |
| Comments on a draft, on a milestone or on the whole draft | could | For a second reviewer; resolved before publish |

### Editing

| Feature | Priority | Notes |
|---|---|---|
| Undo and redo for every action, saved with the draft | must | |
| Multi-select with a box or Shift-click | must | |
| Bulk actions: move to another stage, delete, link to one milestone | must | |
| Drag a node to another stage band | must | Changes the stage, not only `x, y` |
| Keyboard shortcuts for the tools | should | One key per mode, Delete, Ctrl+Z |
| Copy and paste milestones, also between graphs | should | Keys are regenerated |
| Auto layout of a graph from the ELK template | must | The stored layout of 018 §3; manual moves stay possible |
| Several graphs side by side, cross-graph links visible | should | Links to other graphs are drawn as stubs with the graph name |

### Items and recipes

| Feature | Priority | Notes |
|---|---|---|
| Item picker from the recipe dump: search by name, id, mod, tag | must | 3D icons from the icon pipeline; no more free-text item ids or image paths |
| Recipe picker: every recipe that makes an item, with its machine | must | Pick the recipes to ban or to wrap instead of typing ids |
| Show what an unlock really blocks: recipes affected, items no longer craftable | should | From the dump |
| Warn when an unlock bans an item another milestone needs | must | Part of the inline checks |

### Inline checks from the graph tool (#28)

| Feature | Priority | Notes |
|---|---|---|
| Badge on each node: ok, warning, error | must | Errors: not reachable at its stage, backward link, missing recipe |
| Panel with the reason and the proposed fix | must | Today's `completability.md` columns, per node |
| Re-run on save, a few seconds on the full pack | must | Runs on the server from the latest recipe dump |
| Re-run when the pack changes a mod | should | The dump version is shown in the editor |

### Suggestions from the graph tool

| Feature | Priority | Notes |
|---|---|---|
| Tool proposals shown as ghost nodes and ghost links | should | New milestones, moved stages, missing links |
| Accept or reject one by one or in bulk, with a reason | should | Rejections are kept so the tool does not propose them again |
| Filter by kind of proposal and by graph | could | |

### Pacing overlays

| Feature | Priority | Notes |
|---|---|---|
| Effort and power on each node, colour scale | should | From the tool (017 `effort`, `power`) |
| Effort curve across stages, flags long flat stretches | should | The "waves" rule of #28 |
| Stage summary: milestones per stage, per graph, threshold reachable | must | A stage where 80 % is not reachable is an error |

### Search and history

| Feature | Priority | Notes |
|---|---|---|
| Search milestones, items, unlocks across all graphs; jump to the node | must | |
| "Where is this item used": unlocks, requirements, key items | must | |
| Audit log: who changed what, when, in which draft | must | Kept with the draft and the snapshot |

### Moderation of player progressions

| Feature | Priority | Notes |
|---|---|---|
| Look up a player or team progression | must | Same view as the player's |
| Grant or revoke a milestone, with a reason | must | Written as an event with the moderator as actor |
| Reset a progression or one stage, with a reason and a confirmation | must | |
| Open a stage by hand, with a reason | should | For a stuck player after a bad publish |
| Per-progression history of events and moderator actions | must | |

Moderation needs a role. `progression_editor` stays the game server's service role; there are no human
moderators yet, so only admins moderate for now; a dedicated role is deferred (Q2).

## Player view on the website

| Feature | Priority | Notes |
|---|---|---|
| My progress tree: same component as in game, read-only | must | `/stages/{player}` today; same states done, available, locked |
| Stage header: `done / total`, percentage, Noyau module and its delivery bar | must | 017 player experience |
| Next milestones: what I can do now | must | Available milestones sorted by stage |
| Team view: who did what | should | `completed_by` |
| Public or private progress, chosen by the player | should | Public by default (Q4) |
| Compare with a friend or the server average | could | |

## Statistics

### Player side

| Stat | Data in 017 | Missing |
|---|---|---|
| My progress per stage and overall | `progression_milestones`, stages | none |
| Time spent per stage | `progression_events` `stage_opened` times | none, derived |
| Playtime per stage | none | play sessions or playtime per player |
| Team: milestones per member | `completed_by` | none |
| My rank on the server | progressions | none, derived |

### Admin side

| Stat | Data in 017 | Missing |
|---|---|---|
| Players and teams per stage | open stages per progression | none |
| Funnel: share of progressions that reach each stage | `stage_opened` events | none |
| Milestones where players stall: available for long, rarely done | `completed_at` | `available_at` per progression and milestone, or derived from prerequisites and `stage_opened` |
| Completion time per milestone and per stage, distributions | event times | playtime for a fair measure, otherwise wall-clock only |
| Effect of a publish: before and after on the stats above | snapshot `published_at` | `snapshot_version` on every event |
| Activity: milestones done per day | events | none |
| Moderation actions per moderator | none | moderator actions as events with a reason |

Additions to 017 needed for the above:

| Addition | Where | Why |
|---|---|---|
| `snapshot_version` on `progression_events` | Website | Compare stats before and after a publish |
| Moderator events `milestone_granted`, `milestone_revoked`, `progression_reset`, `stage_forced`, with reason | Website | Audit and moderation |
| Play sessions or daily playtime per player | Mods, Website | Playtime per stage; the mod already reports the first connection of the day (rewards streak) |
| Stats computed in the background and cached | Website | No heavy queries on page load |

## API

On top of the routes of 017.

| Route | Who | Purpose |
|---|---|---|
| `GET /api/progression/drafts/{id}/diff?against=` | admin | Diff with a snapshot or the published version |
| `GET /api/progression/drafts/{id}/checks` | admin | Per-milestone results of the graph tool |
| `GET /api/progression/drafts/{id}/suggestions`, `POST .../suggestions/{sid}/accept`, `.../reject` | admin | Tool proposals |
| `GET /api/progression/drafts/{id}/history` | admin | Audit log of the draft |
| `GET /api/recipe-dump/items?q=`, `/recipes?item=` | admin | Pickers, from the latest dump |
| `POST /api/progressions/{id}/moderation` | moderator | Grant, revoke, reset, force a stage, with a reason |
| `GET /api/stats/progression` (`?from=&to=&snapshot=`) | admin | Admin stats |
| `GET /api/progressions/{id}/stats` | public or owner | Player stats, respects the privacy setting |

The current admin routes (`graphs`, `stages`, `milestones`, `milestone-closures`, `unlocks`,
`requirements`) are replaced by the draft API and removed with the old editor.

## Testing

| Check | How |
|---|---|
| Every action of the current editor exists in the new one | Feature checklist from the table above, one Playwright test per action |
| Undo and redo | Unit tests on the draft history |
| Publish refused on errors | Feature test with a draft that breaks rule 2 |
| Diff | Fixture snapshots v1 and v2 with known changes |
| Moderation | Grant, revoke, reset write events with actor and reason; a player cannot call them |
| Stats | Seeded events give known funnel and stall numbers |
| Player view | Screenshot test shared with the in-game component (018) |

## Decisions

| # | Question | Decision (Brian, 21 Nov 2026) |
|---|---|---|
| Q1 | Where does the editor live: the website admin, or a separate admin app | **The website admin**: same login, same component library (018 D4) |
| Q2 | Who may moderate progressions | **Deferred**: no moderators yet, admins only. Add a `progression_moderator` role when the first moderator joins |
| Q3 | Does an unlock still have a shop price | **Removed**: no currency in the gating (docs#27) |
| Q4 | Player progress public by default | **Public**, with a switch to private |
| Q5 | Playtime tracking for stats | **Yes**, one daily playtime row per player sent by the mod; otherwise stats use wall-clock time |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | Editor shell on the 018 graph component: modes, pan, zoom, panel | Website | Every current action works on a draft | M |
| 2 | Draft history, undo and redo, audit log | Website | Tests for undo, redo and log entries | M |
| 3 | Validate, diff and publish screens | Website | Publish refused on errors; diff fixture passes | M |
| 4 | Item and recipe pickers from the dump, 3D icons | Website, Mods | No free-text item ids left | M |
| 5 | Inline checks from the graph tool | Website, docs | Badges match `progression-check` on the current tree | M |
| 6 | Bulk edit, multi-select, auto layout | Website | Playwright tests for bulk move and link | M |
| 7 | Player progress page with the shared component | Website | Screenshot test; privacy switch | S |
| 8 | Moderation actions and role | Website | Feature tests, events with reason | S |
| 9 | Event additions for stats, playtime from the mod | Website, Mods | `snapshot_version` on events; daily playtime rows | S |
| 10 | Admin and player stats pages | Website | Seeded numbers shown correctly | M |
| 11 | Tool suggestions, accept and reject | Website, docs | Rejected proposals are not proposed again | M |
| 12 | Pacing overlays and effort curve | Website | Flat stretches flagged on a fixture | S |

Order: 1 to 3 first, they replace today's editor. Then 4, 5 and 7. Stats and suggestions last,
once players and the graph tool produce data.

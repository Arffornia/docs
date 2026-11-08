# Chantiers

The large workstreams of Arffornia. Each one is an issue labelled
[`initiative`](https://github.com/Arffornia/docs/issues?q=is%3Aissue+label%3Ainitiative) in this repo.
It lists its issues in every repo. This page is the index. Keep it in sync when an initiative opens or closes.

Not to be confused with a review **chantier** ([ADR-0008](decisions/0008-chantiers-and-board-projection.md)):
that one is a batch of PRs that Brian approves at once. An initiative holds many of them over time.

| Initiative | In one line | Status |
|---|---|---|
| [Game design: Arffornia as the progression mod](https://github.com/Arffornia/docs/issues/27) | The mod becomes the hub of the pack: stages of milestones per mod graph, Noyau modules built by Arffornia chains that consume several mods | direction decided |
| [Progression graph tooling](https://github.com/Arffornia/docs/issues/28) | Extract every recipe, generate the graph, prove each milestone is reachable, AI skill on top of static checks | not started |
| [Gating engine](https://github.com/Arffornia/docs/issues/29) | Synced stages, machines bound to a progression, recipes as a datapack with hot reload | decisions taken |
| [Machines and multiblocks](https://github.com/Arffornia/docs/issues/30) | Machine framework, fixed and variable multiblocks with hologram, 3D pipeline, first Smelter | 3D pipeline running |
| [Unified guide and wiki](https://github.com/Arffornia/docs/issues/31) | One source for the in-game book and the website wiki, multiblocks layer by layer | not started |
| [UI framework and shared identity](https://github.com/Arffornia/docs/issues/32) | Premium-grade in-game UIs, graph editor and viewer rework with tests, same look on site and launcher | not started |
| [Rewards and engagement](https://github.com/Arffornia/docs/issues/33) | Typed rewards over an API, kits, ranks, lucky boxes, daily streaks | decisions taken |
| [Cosmetics and pets](https://github.com/Arffornia/docs/issues/34) | Own hats, clothes and pets from a 3D pipeline | not started |
| [Platform and ops](https://github.com/Arffornia/docs/issues/35) | Prod release, observability, security fixes, test environments | in progress |

## Order of work (decided 2026-11-08)

Specify and prove first, build second, generate the graph last, so nothing is redone.

| Phase | Work | Initiatives | Depends on |
|---|---|---|---|
| 1 · Specs and proofs | Progression model and its API ([spec 017](specs/017-progression-model/spec.md)) | #29, #28 | game design decisions |
| | UI framework spec and an in-game web UI prototype (performance, macOS, Linux) | #32 | spec 017 for the graph data |
| | Gating prototype in the mod: ingredient gate, crafting lock, datapack and hot reload | #29 | spec 017, spec 001 |
| | Recipe extraction spike: measure the real size of the graph | #28 | none |
| 2 · Build | UI framework, then the graph viewer and editor, same on the website and in game, with tests | #32 | phase 1 |
| | Gating engine and the new progression API | #29 | phase 1 |
| | Machine framework and multiblocks, first Smelter | #30 | gating prototype |
| 3 · Discovery | Full recipe extraction, lint and proofs, AI skill that turns the current tree into per-mod tracks | #28 | phase 2 |

Independent at any time: concept rounds for machines (3D pipeline), rewards (#33), cosmetics (#34), platform (#35).

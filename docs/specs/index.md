# Specs

Design specs prepare features before implementation. A spec says what to build, how, how to
test it, and which choices the maintainer must make first. Once its **Decisions needed**
are answered, its tasks become `agent-ready` issues.

| # | Spec | Milestone | Status | Blocks on |
|---|---|---|---|---|
| [001](001-recipes-datapack.md) | Machine recipes as a datapack, with stage gating | M3 | Draft: needs decisions | D1–D6 in the spec ([#14](https://github.com/Arffornia/Arffornia_Mods/issues/14), [#16](https://github.com/Arffornia/Arffornia_Mods/issues/16), [#18](https://github.com/Arffornia/Arffornia_Mods/issues/18)) |
| [002](002-machine-framework.md) | Machine framework and multiblocks | M3 | Draft: needs decisions | D1–D7 in the spec ([#17](https://github.com/Arffornia/Arffornia_Mods/issues/17)) |
| [003](003-machine-tier-plan.md) | Machine tier plan (Satisfactory-inspired) | M3 | Proposal | D1–D8 in the spec ([#13](https://github.com/Arffornia/Arffornia_Mods/issues/13)) |

Order: 001 and 002 can start in parallel once decided. 003 feeds content (machines, parts,
gates) into both and can be refined while they are built.

## Status values

| Status | Meaning |
|---|---|
| Draft: needs decisions | Design is complete; the maintainer must answer the decisions. |
| Proposal | A content plan with options; expected to change with playtests. |
| Accepted | Decisions answered; tasks are open as issues. |
| Implemented | Shipped; the spec is kept as a record. |

## Writing a spec

Sections: Summary, Goals / non-goals, Player experience, Design, Testing, Migration,
Decisions needed (each with a recommendation), Work breakdown (issue-sized tasks with
acceptance criteria and effort). Keep it short, link code and sources, no long quotes.
A decision that changes the architecture also gets an [ADR](../decisions/index.md).

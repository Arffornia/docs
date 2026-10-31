# Specs

Design specs prepare features before implementation. A spec says what to build, how, how to
test it, and which choices the maintainer must make first. Once its **Decisions needed**
are answered, its tasks become `agent-ready` issues.

| # | Spec | Milestone | Status | Blocks on |
|---|---|---|---|---|
| [001](001-recipes-datapack.md) | Machine recipes as a datapack, with stage gating | M3 | Accepted with open points | D3a, D3b, D7 ([#14](https://github.com/Arffornia/Arffornia_Mods/issues/14), [#16](https://github.com/Arffornia/Arffornia_Mods/issues/16), [#18](https://github.com/Arffornia/Arffornia_Mods/issues/18)) |
| [002](002-machine-framework.md) | Machine framework and multiblocks | M3 | Accepted direction | D2–D9, art direction research ([#17](https://github.com/Arffornia/Arffornia_Mods/issues/17)) |
| [003](003-machine-tier-plan.md) | Machine tier plan (Satisfactory-inspired) | M3 | Proposal | D1–D8 in the spec ([#13](https://github.com/Arffornia/Arffornia_Mods/issues/13)) |
| [007](007-loading-and-title-screen.md) | Loading screen and title screen (animated factory, previews) | M3 | Draft: needs decisions | D1–D8 in the spec |
| [008](008-economy-and-rewards.md) | Economy, shop and rewards | M3 | Draft: needs decisions | D1–D7 (starting money default 500) |
| [009](009-ranks-roles-permissions.md) | Ranks, roles, cosmetics and permissions | M3 | Draft: needs decisions | D1–D6 |
| [010](010-vote-sites.md) | Vote sites | M3 | Draft: needs decisions | D1–D5 |
| [011](011-mod-intake.md) | Mod intake for the 18 candidates | M3 | Draft: needs decisions | D1–D4, after 001 |
| [012](012-legal-compliance.md) | Legal and compliance | M1/M3 | Audit done, disclaimers shipped | D1–D6 |
| [013](013-arffornia-id.md) | Arffornia ID: identity, passkeys and the login experience | Platform | Draft: needs decisions | D1–D7 |
| [014](014-modpack-lockfile-and-compatibility.md) | Modpack lockfile and mod-compatibility pipeline | Platform | Draft: needs decisions | D1–D5 |
| [015](015-launcher-play-speed.md) | Launcher speed, from Play to the game window | Platform | Draft: needs decisions | D1–D4 |

Specs 004–006 are in an open PR ([#1](https://github.com/Arffornia/docs/pull/1)).

Order: 001 and 002 can start in parallel once decided. 003 feeds content (machines, parts,
gates) into both and can be refined while they are built. 007 is client-only and independent;
its machine art follows 003 and the model pipeline of spec 005.

## Status values

| Status | Meaning |
|---|---|
| Draft: needs decisions | Design is complete; the maintainer must answer the decisions. |
| Proposal | A content plan with options; expected to change with playtests. |
| Accepted | Decisions answered; tasks are open as issues. |
| Accepted with open points / Accepted direction | The direction is decided; a few listed decisions keep their default until Brian answers. |
| Implemented | Shipped; the spec is kept as a record. |

## Writing a spec

Sections: Summary, Goals / non-goals, Player experience, Design, Testing, Migration,
Decisions needed (each with a recommendation), Work breakdown (issue-sized tasks with
acceptance criteria and effort). Keep it short, link code and sources, no long quotes.
A decision that changes the architecture also gets an [ADR](../decisions/index.md).

**No paid solutions.** Specs choose only free options: free tiers, open source, self-hosted.
The only exceptions are a DNS name, or a few euros over a long period (Brian, 31 Oct 2026).

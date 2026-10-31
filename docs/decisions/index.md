# Architecture decisions

Decisions are recorded as short ADRs (context → decision → consequences). An accepted ADR is
the rule until a newer ADR supersedes it. Proposed ADRs wait for the maintainer.

| # | Title | Status |
|---|---|---|
| [0001](0001-record-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-english-codebase-bilingual-players.md) | English codebase, bilingual players (EN/FR) | Accepted |
| [0003](0003-keep-owner-libraries.md) | Keep and improve the owner's libraries | Accepted |
| [0004](0004-github-issues-as-tracker.md) | GitHub issues and an org Project as the tracker | Proposed |
| [0005](0005-docs-as-code.md) | Docs as code: MkDocs site and Noodle diagrams | Proposed |
| [0006](0006-recipes-as-datapack.md) | Deliver custom recipes as a generated datapack | Accepted |
| [0007](0007-preview-environments.md) | Per-PR preview environments on the cluster | Proposed |
| [0010](0010-two-identity-planes.md) | Two identity planes: players on the website, staff on Arffornia ID | Proposed |
| [0011](0011-keep-laravel-add-outbox-events.md) | Keep Laravel; add an outbox event feed, not a message broker | Proposed |
| [0012](0012-modpack-lockfile.md) | Keep Provisioning; add a generated lockfile and a compatibility gate | Proposed |
| [0013](0013-localize-per-player.md) | Player-facing messages are localized per player, at the last moment | Proposed |
| [0014](0014-free-signing-and-updates.md) | Free code signing and auto-update for the launcher | Proposed |

0008 and 0009 are taken by open PRs ([#4](https://github.com/Arffornia/docs/pull/4),
[#5](https://github.com/Arffornia/docs/pull/5)).

Template: copy [`template.md`](template.md), take the next number, open a PR.

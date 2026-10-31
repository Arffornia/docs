# 009 · Ranks, roles, cosmetics and permissions (the "lore")

| | |
|---|---|
| **Status** | Draft: needs decisions |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Provisioning (LuckPerms config), Arffornia_Mods (rank-up, display), Arffornia_Website (roles, profile), infra (Keycloak groups) |
| **Related** | [008](008-economy-and-rewards.md) (cosmetics in the shop) · [002](002-machine-framework.md) (force-loaded chunks for factories) · [012](012-legal-compliance.md) (EULA) |

## Summary

Arffornia already has the start of a lore in LuckPerms (`config/server/storage/config/luckperms/db-export.json.gz`):
a default rank **Aspirant** and two paths of four ranks, one industrial, one arcane, that
grant claims, force-loaded chunks, homes, kits and `/feed` / `/craft`. Nothing assigns
them yet, the names are French literals, and the website has its own unrelated `role` and
`grade` columns. This spec turns that into one coherent system with four separate
axes: **staff roles**, **earned ranks**, **cosmetics** and **team roles**. **Nothing that
helps gameplay is ever sold.**

## Today

| Rank (weight) | Path | Claims | Force-loaded | Homes | Extras |
|---|---|---|---|---|---|
| Aspirant (10, default) | — | 10 | 0 | 1 | daily kit |
| Artisan / Apprenti-Sorcier (20) | tech / arcane | 30 | 1 | 2 | path kit |
| Ingénieur / Mage (30) | tech / arcane | 80 | 5 | 5 | `/craft` |
| Architecte / Archimage (40) | tech / arcane | 150 | 10 | 8 | `/feed` |
| Maître d'Atelier / Éminence (50) | tech / arcane | 500 | 15 | 13 | — |

Website: `users.role` is a comma list of API roles (`admin`, `team_editor`,
`progression_editor`, `nuvotifier_service`…), `users.grade` is always `citizen`.
LuckPerms stores its data in the shared PostgreSQL for both the game server and Velocity.

## Design

### Axis 1 · Staff roles (permissions, never earned or bought)

| LuckPerms group | Website role | Can |
|---|---|---|
| `staff.helper` | — | mute, warn, see reports |
| `staff.moderator` | `moderator` | kick, temp-ban, inspect claims, rollback tools |
| `staff.builder` | — | creative world, WorldEdit in build areas |
| `staff.admin` | `admin` | everything in game except server files |
| `staff.owner` | `admin` | Brian |

- Staff groups live on a separate LuckPerms **track** (`staff`) from player ranks, so
  promotion on one never touches the other.
- Source of truth: **Keycloak groups** (`arffornia-staff-*`) for people, synced to
  LuckPerms and to website roles by a small job (D3). Service roles (`nuvotifier_service`…)
  stay website-only.
- Staff show a discreet `[Staff]` badge, never a gameplay perk.

### Axis 2 · Earned ranks (progression, the lore)

- The rank follows the **team's factory tier** (spec 003): Aspirant (tier 0), then one
  rank every two tiers, up to the fifth rank at tier 8.
- **Path**: at tier 1 the player picks a flavour, *Voie de l'Atelier* (industrial) or *Voie
  des Arcanes* (arcane), which gives the existing names. Both paths have the **same
  perks**; the path is identity, not power (D1). Changing path costs Arffs (spec 008).
- The mod promotes automatically on tier unlock through the LuckPerms API (soft dependency;
  falls back to logging if LuckPerms is absent), and announces it in chat.
- Perks scale for **big factories**, since they need force-loaded chunks to run while the
  team is away (spec 002 chunk rules):

| Rank | Tier | Claims | Force-loaded | Homes | Kit |
|---|---|---|---|---|---|
| Aspirant | 0 | 16 | 0 | 2 | starter (once) |
| Artisan / Apprenti-Sorcier | 1 | 36 | 4 | 3 | — |
| Ingénieur / Mage | 3 | 80 | 9 | 5 | — |
| Architecte / Archimage | 5 | 150 | 16 | 8 | — |
| Maître d'Atelier / Éminence | 8 | 300 | 25 | 12 | — |

  Numbers are starting values. Claims and force-loads are **per player and pooled by FTB
  Chunks in a team** (its party limit mode set to sum; to verify in the FTB Chunks config), so a team of four Ingénieurs can keep a large factory running.
  Remove `/feed`, `/craft` and daily kits from ranks: they bypass the progression.
- Display: LuckPerms holds **keys**, not text (`meta.arffornia.rank = artisan`); the mod and
  the chat formatter (Better Forge Chat Reborn) render the localized name, en/fr
  (ADR-0002). The current French-literal prefixes become lang keys.

### Axis 3 · Cosmetics (earned or bought with Arffs)

- Pets, particles, chat colours, titles, hats, team banner. Each one is a LuckPerms
  permission node `arffornia.cosmetic.<kind>.<id>`, granted by rewards or the shop
  (spec 008).
- One **Cosmetics** screen in game (and the profile on the website) lists owned and
  available cosmetics, with how to get each one.
- Event cosmetics (Halloween, Christmas…) are time-limited to obtain, kept forever.
- **No capes or cape look-alikes** (Usage Guidelines). No paid cosmetics (Brian's rule).

### Axis 4 · Team roles

FTB Teams roles (owner, officer, member) are the only team roles. The owner rebinds
machines (spec 002 D4) and manages the team banner. No LuckPerms groups for teams.

### Paid vs earned

| Thing | Earned by playing | Arffs shop | Real money |
|---|---|---|---|
| Ranks and their perks | yes | no | **never** (gameplay advantage, Usage Guidelines) |
| Cosmetics | yes (votes, events, milestones) | yes | never (Brian's rule; allowed by Mojang, but not wanted) |
| Server access | free | — | never |

### Permissions hygiene

- Every Arffornia permission node is declared through NeoForge's `PermissionGatherEvent`
  (already done for `command.claim_reward.others` and `command.progression.manage`), so
  LuckPerms shows them with auto-completion.
- `/lp` web editor links are staff-only. A weekly LuckPerms export is kept in Provisioning
  (git history of permission changes, D4).
- Default op level 0 for everyone; staff get permissions through groups, never `/op`.

## Testing

| Test | Kind |
|---|---|
| Tier unlock → LuckPerms parent set, chat announcement, localized name in en and fr | GameTest with a fake LuckPerms API |
| Path choice is one-time, change costs Arffs | GameTest + website feature test |
| Staff track and rank track are independent | LuckPerms config test in Provisioning CI (load the export, check tracks) |
| No rank grants a node outside the allow-list (claims, force-load, homes) | Provisioning CI check |

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Two paths | (a) flavour only, same perks; (b) real separate progressions (magic milestones) | **(a)**; (b) needs a magic progression that does not exist |
| D2 | Rank driver | (a) team factory tier; (b) playtime; (c) personal milestones | **(a)**: one progression, no AFK farming |
| D3 | Staff source of truth | (a) Keycloak groups synced to LuckPerms and website; (b) set by hand in both | **(a)** once Keycloak work lands; (b) until then |
| D4 | LuckPerms changes in git | (a) weekly export committed by a job; (b) no | **(a)**, only when something changed (token budget rule) |
| D5 | Remove `/feed`, `/craft`, daily kits from ranks | (a) remove; (b) keep | **(a)** |
| D6 | Rank names | (a) keep the French names, add English ones; (b) new names | **(a)**, e.g. Aspirant/Aspirant, Artisan/Artisan, Ingénieur/Engineer, Architecte/Architect, Maître d'Atelier/Workshop Master |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | LuckPerms layout: `staff` and `rank` tracks, new perks, keys instead of literal prefixes | Provisioning | Export loads; CI check of tracks and allow-list | S |
| 2 | Auto rank-up on tier unlock via the LuckPerms API, path choice screen | Mods | GameTests above; en/fr | M |
| 3 | Localized rank display in chat and tab list | Mods + Provisioning | Better Forge Chat format uses the rendered name | S |
| 4 | Cosmetics screen and permission-node grants | Mods | Lists owned/available; grants from rewards work | M |
| 5 | Website profile: rank, path, cosmetics | Website | Profile shows them en/fr | S |
| 6 | Keycloak group → LuckPerms/website staff sync | infra + Website | A group change reaches both within 5 min | M |

# 008 · Economy, shop and rewards

| | |
|---|---|
| **Status** | Draft: needs decisions |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Website (money, shop, votes), Arffornia_Mods (reward delivery, in-game sources), Arffornia_Proxy (votes) |
| **Related** | Website [#55](https://github.com/Arffornia/Arffornia_Website/issues/55) (starting money), [#89](https://github.com/Arffornia/Arffornia_Website/pull/89) (`STARTING_MONEY`), [#90](https://github.com/Arffornia/Arffornia_Website/pull/90) (atomic purchases), [#25](https://github.com/Arffornia/Arffornia_Website/pull/25) (PayPal, to close) · [009](009-ranks-roles-permissions.md) · [010](010-vote-sites.md) · [012](012-legal-compliance.md) · the platform's event-system ADR (pending) |

## Summary

No economy design exists yet. Today: `users.money` is a `float`, new accounts get 100,000
(a leftover test value, `UserRepository.php:92`), and PR #89 makes it configurable with a
default of 0. The website shop sells items for that money. Votes grant a hard-coded
diamond. This spec defines one **virtual currency, earned only by playing**, with clear
sources, sinks and prices. New players get a **small starting amount: 500**.

## Goals

- One currency, earned by playing, voting and progressing. **Never bought with real
  money**: Brian refuses paid services, and the Minecraft Usage Guidelines forbid
  selling gameplay advantages (spec [012](012-legal-compliance.md)).
- Faucets and sinks are balanced and **measured**, so inflation is visible before it hurts.
- Rewards are **structured data** (currency, item bundle, cosmetic), never raw console
  commands (security finding in the mod audit).
- Every reward reaches the player exactly once, even if they are offline, have a full
  inventory, or the website is down.

## Non-goals

- Real-money payments, donations or a paid store. If that ever changes, it needs a new ADR
  and the EULA review in spec 012.
- A player-run market or auction house (later, D6).
- The transport between website and game (event bus or polling): owned by the
  platform's event-system ADR. This spec states only the gameplay requirements it must
  meet.

## Design

### The currency

| Item | Proposal |
|---|---|
| Name | **Arffs** (symbol ⟁ in UI), en/fr same word (D1) |
| Storage | `users.money` becomes `BIGINT` whole units (no `float`: rounding errors and comparisons are unsafe for money) |
| Ledger | new `money_ledger` table: user, delta, reason (`vote`, `milestone`, `shop`, `admin`…), reference id, timestamp. The balance is the sum, cached in `users.money`; every change goes through one service in a transaction |
| Scope | per player (not per team): the shop sells personal cosmetics; team rewards are split (below) |
| Value | no real-world value, not transferable outside Arffornia, not convertible (Usage Guidelines) |

### Starting amount

**Default: 500 Arffs** (D2). Enough for one or two small cosmetics on day one, so the shop
makes sense immediately, while a week of normal play earns several times that. Set by
`STARTING_MONEY` (PR #89 already adds it).

### Sources (faucets)

| Source | Amount (start values) | Limits |
|---|---|---|
| Vote on a listed site ([010](010-vote-sites.md)) | 100 per vote | site cooldown; vote streak bonus +10 % per consecutive day, capped at +50 % |
| Daily login | 50 | once per calendar day (Europe/Paris), streak via the existing `day_streak` column |
| Milestone completed (team) | 300 × tier, split equally between the members online in the last 7 days | once per team per milestone |
| Space Elevator phase delivered (team) | 2,000 × phase, split as above | once per team per phase |
| Monthly top voters | 1st 3,000 · 2nd 2,000 · 3rd 1,000 + a cosmetic title | month end |
| Events (seasonal, from the MOTD calendar) | set per event | admin-defined |

### Sinks

| Sink | Price range | Notes |
|---|---|---|
| Cosmetics: pets, particles, chat colours, titles, hats | 500–15,000 | never capes (Usage Guidelines) |
| Team banner and team name colour | 2,000 | team cosmetic |
| Rank path change (tech ↔ arcane, spec 009) | 5,000 | flavour only |
| Convenience that is **not** an advantage over others: extra `/home` slot, waystone renaming | 1,000–3,000 | in-game currency only, earnable by everyone |
| Event tickets (seasonal) | set per event | |

Rule for every new shop item: **"Could a player who never voted get it by playing?"** If
not, it does not go in the shop.

### Rewards (gameplay side)

A reward is a typed record, created by the website (vote, purchase, milestone, admin) and
delivered by the mod:

```json
{"id": "rw_01J…", "user": "<uuid>", "source": "vote:top-serveurs",
 "grants": [
   {"type": "currency", "amount": 100},
   {"type": "items", "items": [{"id": "minecraft:diamond", "count": 1}]},
   {"type": "cosmetic", "key": "arffornia:pet/kitten"},
   {"type": "title", "key": "arffornia:title/top_voter_2026_10"}
 ]}
```

| Requirement | Detail |
|---|---|
| Exactly once | the mod claims by reward id; the website marks it claimed in the same transaction; replays are ignored |
| Offline players | rewards wait; on join a toast says "3 rewards waiting · /rewards" |
| Full inventory | items go to a **reward mailbox** screen (`/rewards`), taken when there is room; nothing is dropped on the ground |
| Latency | under 5 s when the player is online (vote → toast) |
| Outage | website down: nothing is lost, delivery resumes; game server down: same |
| Cosmetics | granted as LuckPerms permission nodes (`arffornia.cosmetic.pet.kitten`), so every cosmetic mod reads one source (spec 009) |
| No commands | the current `pending_rewards.commands` (console strings) is replaced; an allow-list stays only during migration |
| Audit | every grant is in the ledger and visible on the player's website profile |

**Claim API or event system?** The platform agent's ADR owns that choice. The gameplay
side works with either one. The default is to **claim on join and every 60 s** over the
authenticated API, which meets every row above except the 5 s latency. An event push
(if the ADR adopts one) only improves latency. Nothing in the reward model depends on
the transport.

### Shop

- Items get a `type` (`cosmetic`, `convenience`, `team`), structured `grants` (above),
  en/fr name and description (ADR-0009), and an optional stock or end date for events.
- Purchase is atomic (PR #90) and writes the ledger.
- Every price and every item is public before a player joins (Usage Guidelines rule on
  publishing prices).
- `real_price` / `promo_price` are renamed `price` / `sale_price`: there is no "real"
  money.

### Health metrics

The website exports, and the monitoring stack graphs: total Arffs in circulation, daily
faucet vs sink, median and p90 balance, shop sales per item. Alert when the daily faucet
is more than twice the daily sink for 14 days (inflation).

## Testing

| Test | Kind |
|---|---|
| Ledger: concurrent grants and purchases keep `sum(ledger) == users.money` | Website feature test with parallel requests |
| Starting money from `STARTING_MONEY`, default 500 | feature test (extends PR #89's test) |
| Reward claimed twice → granted once | Website + mod GameTest with the in-memory backend |
| Full inventory → mailbox, nothing dropped | GameTest |
| Vote streak bonus caps at +50 % | unit |
| Monthly top voters job | feature test with a fixed clock |

## Migration

1. `money` float → bigint (round down), create the ledger with one "opening balance" row
   per user. Decide what to do with the 100,000 test balances (D3).
2. Ship structured rewards beside `commands`; the mod handles both; then remove `commands`.
3. Close PR #25 (PayPal coin purchase).

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Currency name | (a) Arffs; (b) Crédits; (c) another name | **(a)** |
| D2 | Starting amount | (a) 0; (b) **500**; (c) 1,000 | **(b) 500**: small, but the shop is usable on day one |
| D3 | Existing 100,000 test balances | (a) reset everyone to the starting amount; (b) keep | **(a)** before the public opening; the server has only test accounts |
| D4 | Currency scope | (a) per player; (b) per team | **(a)**; team rewards are split between active members |
| D5 | Player-to-player `/pay` | (a) no; (b) yes with a daily cap | **(a)** at launch (simpler to keep fair), revisit with D6 |
| D6 | Player market / auction house | (a) later spec; (b) never | **(a)** |
| D7 | Real money | (a) none, ever; (b) cosmetic-only donations later | **(a)**, per Brian; (b) would need a new ADR and the EULA rules in 012 |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | Money as bigint + ledger service | Website | All money changes go through the service; invariant test | M |
| 2 | Starting money default 500 (after PR #89) | Website | Config default 500; test | S |
| 3 | Structured rewards model and claim API (idempotent) | Website | Reward ids; claim once; feature tests | M |
| 4 | Reward delivery, toast and `/rewards` mailbox | Mods | GameTests: offline, full inventory, replay | M |
| 5 | Faucets: vote amount + streak, daily login, milestone and elevator rewards | Website + Mods | Amounts from config; tests | M |
| 6 | Shop item types, en/fr, grants, rename price columns | Website | Migration; admin form; public price list | M |
| 7 | Economy metrics endpoint + dashboard + inflation alert | Website + infra | Metrics exported; alert rule | S |
| 8 | Close PR #25 (PayPal) | Website | Closed with a link to this spec | S |

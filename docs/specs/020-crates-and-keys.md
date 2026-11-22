# 020 · Crates and keys

| | |
|---|---|
| **Status** | Accepted (decisions by Brian, 22 Nov 2026) |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Mods (key item, crate block, opening, calendar screen), Arffornia_Website (reward type, streak calendar API, profile), docs |
| **Related** | [008](008-economy-and-rewards.md) (rewards, shop, currency) · [010](010-vote-sites.md) (vote rewards) · [018](018-ui-framework.md) (native screens vs web UI) |

## Summary

Today a daily streak reward is a `lucky_box` entry: when the player runs
`/arffornia shop claim_reward`, the mod rolls a loot table and puts the loot straight into the
inventory. It works, but nothing shows what was won, why, or what comes next.

This spec turns rewards into **keys** and **crates**. A reward gives a key. The player opens it on
a crate at spawn, in a shop area that also holds the other crates (vote, kit, legendary). The
crate shows the loot it can give, and the streak crate shows **the week's calendar**: where the
player stands in the streak and what each day gives.

## Goals

- A reward is visible and has a moment: the player walks to a crate, uses the key, and sees the
  roll.
- The player knows what is coming: the current streak day, the reward of each day of the week,
  and the odds of each crate.
- One system for every crate: streak, vote, kit, legendary, event. A new crate is data, not code.
- Delivery stays exactly-once: the key is the reward, and opening is a local, server-side action.

## Non-goals

- Real money. Keys are never sold for real money (008 D7). Shop keys cost in-game currency only.
- Player trading of keys at launch (see D1).
- The spawn build itself. This spec gives the build team a list of blocks and their placement
  rules, not a map.

## Current state (22 Nov 2026)

| Piece | Where | What it does |
|---|---|---|
| Streak record | Website `POST /api/rewards/day-streak`, `users.day_streak`, `users.last_streak_date` | First join of the day (Europe/Paris) increments the streak, a missed day resets it to 1, and creates a `pending_rewards` row with `source = streak` |
| Streak contents | `config/rewards.php` `streak.tiers` | Days 1–7: one `lucky_box arffornia:streak`, then 2, 3 and 4 boxes from days 8, 15 and 22 |
| Reward types | `App\Rewards\RewardCatalog` | `item`, `permission`, `rank`, `lucky_box` |
| Delivery | Mod `RewardHandler`, `RewardDelivery` | Claim by id with an idempotency key, then deliver; a `lucky_box` rolls `data/<ns>/loot_table/lucky_box/<path>.json` into the inventory |
| Join notice | Mod `RewardHandler.onPlayerJoined` | Chat lines and, since Mods#75, a screen title with the streak day and the claim command |

## Design

### Keys

- A new item `arffornia:crate_key`. Its data component holds the crate id
  (`arffornia:streak`, `arffornia:vote`, `arffornia:kit/starter`...). The model and name come from
  the crate definition, so each crate's key looks different from one item.
- A new reward type on the website, `key`:
  `{"type": "key", "crate": "arffornia:streak", "count": 1}`. The mod delivers it like an
  `item` entry. Claims, exactly-once delivery, full inventory and outages work as they do today.
- Keys are **bound to the player** who received them (D1). A bound key shows its owner in the
  tooltip, and a crate refuses another player's key.
- `lucky_box` stays as a type for rewards that should not need a crate, such as admin gifts. The
  streak, vote and shop rewards move to `key`.

### Crates

- A crate is data: `data/<ns>/arffornia/crate/<id>.json` in the mod or a datapack:

  ```json
  {
    "name": {"translate": "crate.arffornia.streak"},
    "loot_table": "arffornia:crate/streak",
    "key_model": "arffornia:item/key_streak",
    "preview": "loot_table",
    "calendar": "streak"
  }
  ```

- A **crate block** `arffornia:crate`, with a block entity that names the crate id. Only admins
  can place, break or change it. It has no inventory.
- **Opening:** the player right-clicks the crate with a matching key. The server checks the
  key and the owner, rolls the loot table, and checks that **the whole roll fits** in the free
  inventory room. Only then does it consume one key. If it does not fit, nothing is consumed and the
  player reads "Your inventory is full: free N slots". Everything happens on the server, so a client
  cannot choose the result.
- **Animation:** see "Opening sequence" below. A rare roll is announced to the whole server (D6).
- **Preview:** right-click without a key, or sneak + right-click, opens a native screen with every
  possible item and its odds, computed from the loot table weights (D4).

### Opening sequence

The result is rolled and the key consumed **before** the show starts: the animation only reveals it.
The loot goes into the inventory at the end of the sequence. If the player leaves or dies
during the sequence, the loot is given right away, or on the next join if they left. Nothing drops.

| Time | What the player sees and hears |
|---|---|
| 0.0 s | The key flies from the hand into the lock, turns, a heavy click. The crate shakes and its seams glow in the crate's colour |
| 0.5 s | Charge: glyph particles spiral into the crate, a light beam rises from it, a note rises in pitch. The beam is white for common crates, blue, purple, then gold for the legendary crate |
| 1.5 s | Roulette: the lid lifts and the crate's possible items cycle above it as 3D items, fast at first, then slowing down with a tick on each change, like a slot machine. It lasts about 3 s |
| 4.5 s | Reveal: the roulette stops on the item, the lid bursts open, and a firework burst fires in the rarity colour. The item grows and floats over the crate with its name and count |
| 5.5 s | The item flies into the player with the pickup sound. A line in the chat records it |

Rare and legendary rolls add more:

- **Rare:** a coloured shockwave ring on the ground and a deeper sound.
- **Legendary:** the beam turns gold and goes up to the sky, totem particles fall, a thunder
  sound plays with no lightning, and the opener gets a screen title. The whole server gets a chat
  line with the item, and hovering it shows the item (D6).

Other details:

- Other players near the crate see the whole sequence, which makes the spawn feel alive.
- Sneak + right-click while the roulette turns skips to the reveal, for players who open many
  keys.
- A crate runs one sequence at a time. A second player gets "This crate is busy" until it ends,
  about 6 s. The spawn has several crates of each kind if crowds become a problem.
- The client side is a block entity renderer and a particle preset in the mod. The server sends
  one packet with the roulette items, the result and the rarity, so every viewer sees the same show.

### Inventory room, for every reward

The rule applies to keys, crates and shop items: **a reward is given only when all of it fits in
the inventory, and nothing is ever dropped.**

- On join, keys go straight into the inventory when they fit (D5). What does not fit stays
  pending, and the player reads "Your inventory is full: free N slots, then use
  /arffornia shop claim_reward".
- `/arffornia shop claim_reward` with a full inventory gives nothing and says how many slots to
  free. Rewards that fit are given, and the rest wait.
- **Change from today:** `RewardPlanner` gives a reward larger than the whole inventory (36
  slots) when the inventory is empty, and the overflow drops at the player's feet. That is
  removed. The website refuses to create a reward that needs more than 36 slots, checked by
  `RewardCatalog`. The mod keeps such a reward pending and logs it, and never drops any of it.
- A `lucky_box` roll is checked like a crate roll: roll first, check that it fits, then
  claim.

### Streak calendar

- The streak crate's screen has a **week strip**: seven days, today highlighted, past days of the
  current streak ticked, and each day's reward shown (one key, two keys, a bonus key on day 7).
  It also shows the current streak and the best streak.
- It reads `GET /api/players/{uuid}/rewards/streak`:
  `{day_streak, best_streak, last_streak_date, today_claimed, week: [{day, contents}]}`. The week
  comes from `config/rewards.php`, so the calendar and the actual reward cannot disagree.
- The same data is shown on the player's website profile (019, player view).
- The streak rewards move from 7-day tiers to a **weekly cycle** (D3). For example, days 1–6 give
  one streak key and day 7 gives a streak key plus a vote key. A month of streak (day 28) gives a
  legendary key.

### Shop area at spawn

- One place for every crate: streak, vote, kit crates and the legendary crate. The site's shop
  page lists the same crates with their previews, so a player can see a crate's contents before
  buying its key.
- Until the spawn is built, the crates stand at the test spawn of the slot and the staging
  world, placed by an admin command (`/arffornia crate place <id>`).

### Join notice

The join title (Mods#75) changes to say what to do: "Day 4 · a key is waiting", with the subtitle
"Claim it with /arffornia shop claim_reward, open it at spawn". Once claiming happens on join
(D5), the subtitle becomes "Open it at the crates, at spawn".

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Can keys be given or traded | (a) bound to the player; (b) tradeable; (c) bound for streak and vote, tradeable for shop keys | **Decided (a)** (Brian, 22 Nov) at launch: no key market and no alt farming. Revisit with 008 D6 (player market) |
| D2 | Where keys can be opened | (a) only at a crate block; (b) at a crate, or anywhere with a "key menu" | **Decided (a)** (Brian, 22 Nov): going to the crates is the point. Admins place a crate on test worlds until the spawn exists |
| D3 | Streak cycle | (a) keep today's tiers (more boxes every 7 days); (b) weekly cycle with a day-7 bonus and a day-28 legendary key | **Decided (b)** (Brian, 22 Nov): it is what the calendar shows best |
| D4 | Show odds | (a) yes, exact percentages; (b) only the list of items | **Decided (a)** (Brian, 22 Nov): honest, and keys bought with currency are close to the paid loot boxes the Usage Guidelines care about |
| D5 | Claim keys on join automatically | (a) yes, keys go straight into the inventory on join; (b) keep `/arffornia shop claim_reward` | **Decided (a)** (Brian, 22 Nov): on join when they fit, otherwise with the command once there is room; never dropped (see "Inventory room") |
| D6 | Announce rare rolls to the server | (a) yes, items marked rare in the crate file; (b) no | **Decided (a)** (Brian, 22 Nov) |
| D7 | Opening animation | (a) native in-world; (b) a GUI roulette | **Decided (a)** (Brian, 22 Nov): the "Opening sequence" above |

## Testing

| What | How |
|---|---|
| A key reward is delivered once | Mod GameTest, the same pattern as `RewardDeliveryGameTests` |
| A crate consumes exactly one key and gives the loot | GameTest: key in hand, use the crate, assert one key less and the loot in the inventory |
| Full inventory keeps the key | GameTest |
| A reward that does not fit stays pending, nothing is dropped | GameTest, including a reward of more than 36 slots |
| The website refuses a reward over 36 slots | Website unit test on `RewardCatalog` |
| Leaving during the opening sequence still gives the loot | GameTest |
| Another player's key is refused | GameTest |
| Odds in the preview match the loot table | Unit test on the odds calculation, with a fixture loot table |
| Calendar API shape and week contents | Website feature test, from `config/rewards.php` |
| Streak cycle (D3) | Website unit test: days 1, 7, 8, 28, and a missed day |

## Migration

- Pending `lucky_box` streak rewards stay valid and are delivered as today.
- Once the mod with keys is on a server, the website creates `key` entries for new streak rewards.
  A config flag switches between the two, so the website can go first.

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | `key` reward type and streak calendar API | Website | Feature tests; config flag `rewards.streak.as_keys` | S |
| 2 | `crate_key` item and crate definitions | Mods | Keys delivered by a claim, bound to the player, model per crate | M |
| 3 | Crate block: opening and refusals | Mods | GameTests above | M |
| 4 | Opening sequence, rare roll announcement | Mods | Seen on the slot by Brian; skip and busy work | M |
| 4b | No drop: remove the 36-slot overflow, 36-slot limit on the website | Mods, Website | Tests above | S |
| 5 | Preview and streak calendar screens | Mods | Odds match the loot table; calendar matches the API | M |
| 6 | Weekly streak cycle (D3), auto-claim of keys on join (D5) | Website, Mods | Tests above | S |
| 7 | Shop page lists crates with previews | Website | Screenshot test | S |
| 8 | Crates at spawn | Build | Placed by an admin on the real spawn | — |

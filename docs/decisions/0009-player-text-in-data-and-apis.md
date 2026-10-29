---
status: proposed
date: 2026-10-29
---

# 0009 · Player-visible text in data and APIs

## Context
[ADR-0002](0002-english-codebase-bilingual-players.md) made every UI string bilingual, and the
website, launcher and mod now pass it (Website #101, Launcher #67, Mods #50). Text that arrives as
**data** was left out: database rows served by the API (news, shop items, milestones, item names),
JSON and scripts shipped by Provisioning (shader badges, KubeJS tooltips, Discord presence), and the
messages in API responses. An audit found 63 such fields or call sites: English or French depending
on who typed them, and nothing to switch the language. Two things already work and set the
direction: Provisioning's `featuredShaders.json` stores `{ "fr": ..., "en": ... }` objects that the launcher
resolves, and [Arffornia_Website#100](https://github.com/Arffornia/Arffornia_Website/issues/100) recommends JSON columns with `spatie/laravel-translatable` for database
content while keeping the API contract with the mod unchanged.

## Decision (proposed)
Classify every piece of player-visible data, then apply the rule for its class.

| Class | Examples | Rule |
|---|---|---|
| **Fixed vocabulary** known at build time | tooltips, status labels, graph categories, reward announcements | Data carries a **translation key** (or a stable code); each client resolves it from its own lang files (mod `en_us`/`fr_fr`, launcher vue-i18n, Laravel `lang/`, KubeJS `assets/<ns>/lang/`). |
| **Free-form editorial content** | news, shop items, milestone names and descriptions, shader blurbs | Stored as a **localized object** `{ "en": "...", "fr": "..." }` (JSON file field, or JSON column via `spatie/laravel-translatable`, see #100). |
| **Minecraft items** | milestone unlocks and requirements | The client shows the item's own translated name from its id; a stored display name is only a fallback for unknown items. |
| **Names** | players, teams, mods, the server brand | Not translated. |
| **Status and errors** | API JSON `message`/`error` | Text from `lang/<locale>/api.php`, keyed by a stable id that clients may map to their own text (a `code` field, added when the first client needs it). |

**Locale negotiation (API).** `?locale=` (explicit, cache-friendly) > `locale` cookie (website pages
calling the API) > `Accept-Language` > `en`. The response says which one it used in
`Content-Language` and varies on `Accept-Language`. Responses keep their shape: a translated field
is still a plain string, already resolved (the mod contract does not change, as #100 asks). An
editor endpoint can later return the full objects behind an explicit parameter.

**Fallback.** Requested locale > `en` > first non-empty value. Blank strings count as missing. This
matches #100, where existing French text moves into the `fr` slot and English falls back to it until
someone translates it.

**Clients.**
- *Mod*: requests made for a player carry that player's game language (`fr_fr` → `fr-FR`); the server
  uses the player's client information. Packets carry `Component`s, translatable when the text is a
  key (protocol 1.1, Mods #50), literal only for resolved API strings and names.
- *Launcher*: sends its UI language (not the OS one Chromium would send) and resolves localized
  objects with one shared helper.
- *Website*: pages use their locale; API calls from pages inherit it through the cookie.

**Single-language surfaces.** The server-list MOTD (the ping has no client locale), Discord channels
and bot status are one language each, chosen per surface and written in the config.

**Guards.** Each repo fails its `make check` on new hardcoded player text in data: the website lint
flags literal API messages, the Provisioning test flags plain-string text fields and literal KubeJS
text, the mod test flags raw API item names, the launcher test checks every localized object resolves
in both languages.

## Consequences
- One answer to "where does this text get translated?": the client for keys and items, the source
  data for free-form content, the API for messages.
- English API text stays byte-identical for clients that send no locale (the mod and proxy use
  Java's `HttpClient`, which sends no `Accept-Language`).
- Content editors must enter two languages for editorial content; English may lag behind (fallback).
- Item display names stored by the mod in the database stop being the source of truth.
- Work that follows: #100 (migrations and admin forms), graph categories as keys, a purchase
  announcement in the mod instead of `say` text in shop rewards, a `code` field in API errors.

## Alternatives considered
- **Everything as keys, translations in client lang files**: impossible for content written by
  staff after release (news, shop) without shipping a client update.
- **Server-rendered text only (API decides, clients never translate)**: the mod and launcher already
  have lang files for UI and items; going through the API for those would add latency and offline gaps.
- **Separate rows or tables per locale**: see #100 options 2 and 3; more joins, and IDs referenced by
  the mod would split.
- **Pinning the API to English** (the first step of #101): fine for messages nobody reads, wrong once
  the API serves translated content.

## Open decisions (defaults proposed)
1. Honour `Accept-Language` on the API, not only `?locale=`. **Default: yes.**
2. Fallback order requested > `en` > any. **Default: yes.**
3. Language of single-language surfaces. **Default: MOTD brand-only; Discord in French.**
4. Shop rewards that announce something: **default: the mod sends a translatable
   `chat.arffornia.shop.*` announcement chosen by a reward type; no `say`/`tellraw` in the allow-list
   (Mods #42).**
5. Item display names in the database: **default: fallback only; the website keeps showing them until it
   has an item-name source.**
6. Graph categories: **default: store keys (`magic`, `tech`), translate in each client.**
7. Add a `code` field to API error bodies: **default: yes, in one PR after the API contract tests
   (Website #95) merge, since two of them assert exact bodies.**

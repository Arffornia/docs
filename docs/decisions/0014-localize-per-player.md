---
status: proposed
date: 2026-10-31
---

# 0014 · Player-facing messages are localized per player, at the last moment

## Context
Brian asked why shop announcements are "translated by the mod" instead of the website. One
in-game announcement reaches every online player, and each player's game can be in a
different language. The website sends **one** message to **one** server; it does not know who is
online or which language each client uses. The server does know: NeoForge exposes each
player's client language (`ServerPlayer#clientInformation().language()`), and a
`Component.translatable(key, args)` is rendered by **each client** in its own language.

## Decision (proposed)
- **Fixed events** (a purchase, a vote, a milestone, "pending rewards"): the website or the
  outbox event (ADR 0012) carries a **key and arguments**, for example
  `{"key":"chat.arffornia.shop.bought","args":{"player":"Notch","item":"shop.item.42"}}`.
  The mod sends `Component.translatable(...)`. Each client renders it from the mod's
  `en_us.json` / `fr_fr.json`, which ship with the mod on every client.
- **Free text written by admins** (news, custom announcements): the website stores it in **EN
  and FR** (spatie/laravel-translatable JSON columns, already chosen) and sends both,
  `{"text":{"en":"…","fr":"…"}}`. The mod sends each player the version for their client
  language, and falls back to EN.
- **No `say` / `tellraw` with baked-in text** in reward commands for anything players read. Reward
  commands only *give*. The announcement is a separate, translatable event.
- **Single-language surfaces** (the server list MOTD, Discord) follow their own rule. The MOTD
  plugin guesses the language from players who recently joined from the same address
  ([Arffornia_Proxy#16](https://github.com/Arffornia/Arffornia_Proxy/pull/16)).

## Consequences
- The website still owns the words (keys + translations, or both texts). The mod only
  *chooses* per reader. "Translated by the mod" really means "picked per player by the mod".
- New fixed-event keys need a mod release (lang files). Free text does not.
- A player who changes language mid-session gets new messages in the new language.

## Alternatives considered
- **The website translates and sends one string:** every player gets one language. That was the old
  French `say` rewards.
- **The website sends one string per player:** the website would need the online player list
  and their languages. That duplicates server state and races with joins and leaves.
- **Send both languages to everyone:** noisy chat.

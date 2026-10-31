---
status: proposed
date: 2026-10-31
---

# 0012 · Keep Laravel; add an outbox event feed, not a message broker

## Context
- The website (Laravel 13, PHP 8.5 since [#103](https://github.com/Arffornia/Arffornia_Website/pull/103))
  is the site and also the API and source of truth for players, progression, shop and votes.
- Brian asked whether a lighter, more modern stack (Go, Rust, TS/Bun, Elixir) should replace it,
  and whether rewards, votes, progression and announcements need "a real event system".
- Today the flow is pull-based:
  - the mod checks pending shop rewards when a player joins, and the player types `/arffornia shop claim_reward`;
  - votes go through NuVotifier → the proxy plugin → `POST /api/vote/nuvotifier`;
  - there is no push from the website to the game.
- The load is a single modded server with tens of concurrent players, a few events per minute
  at most. The queue driver is `database`, and there is no Redis.

## Decision (proposed)
1. **Keep Laravel.** A rewrite would redo ~140 tests, the admin panel, the i18n work just
   done and the Microsoft/Minecraft login, for a load PHP already handles easily. If
   throughput ever matters, **Laravel Octane on FrankenPHP** (free, MIT) keeps the app in
   memory without a rewrite. New, separate services, if any, may use Go or TypeScript.
2. **Add a transactional outbox, not a broker.**
   - Each domain change (purchase, vote, milestone reached, announcement published) inserts a row into
     `events(id bigserial, type, payload jsonb, created_at)` **in the same DB
     transaction**.
   - Consumers read `GET /api/events?after=<id>` with a service-account token. It is a
     long-poll: it holds up to 25 s and returns as soon as rows exist, woken by Postgres
     `LISTEN/NOTIFY` or by a 1 s re-query.
   - Each consumer stores its last id, so delivery is at least once and handlers are idempotent per event id.
3. **The first consumer is the mod.** Purchases and votes are announced and delivered
   while the player is online (no rejoin, no claim command needed). The claim command stays as
   a fallback.
4. **Revisit with NATS JetStream** (Apache-2.0, a single ~20 MB binary) only if one of these is true:
   - there are 3 or more independent consumers;
   - fan-out across several game servers (Arcane, Nexus) needs replay and filtering;
   - the website itself needs real-time pushes to browsers (or use Laravel Reverb for that).

## Consequences
- Real-time rewards and announcements at the cost of one table, one endpoint and one
  consumer loop in the mod. Nothing new to deploy or back up.
- Events are durable in Postgres (WAL-G backups already cover them) and can be replayed for
  debugging.
- The long-poll holds one PHP-FPM worker per consumer. That is fine for 1–3 consumers, and
  Octane removes the limit.

## Alternatives considered
- **Rewrite in Go, Rust, Bun or Elixir:** more speed than needed. It costs months and the tested
  behaviour, for no player-visible gain.
- **Redis Streams:** adds Redis (stateful, another backup) for a few events a minute.
- **NATS JetStream now:** the best broker for this size if one is needed, but premature with one consumer.
- **Postgres LISTEN/NOTIFY alone:** not durable (a missed notification is lost). Here it is only
  used to wake the long-poll, and the outbox table is the source of truth.
- **Webhooks from the website to the mod:** the game server would need an inbound HTTP port
  and retries. The feed reverses the direction and works behind NAT.

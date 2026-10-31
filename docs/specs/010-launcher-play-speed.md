---
status: Draft: needs decisions
date: 2026-10-31
---

# 010 · Launcher speed, from the Play click to the game window

## Summary

Every *Play* click does all the work again, mostly one item at a time. On a warm install
(nothing changed since the last launch), the launcher still:

1. resolves ~330 mod descriptions online (CurseForge through `api.curse.tools`, Modrinth, GitHub),
   8 at a time once [Nexus_Mods#24](https://github.com/Arffornia/Nexus_Mods/pull/24) lands, and 1 at a time before that;
2. fetches the external-files index and hashes ~360 config files;
3. hashes **every mod jar** (`updateMods(checkHash=true)`), **one at a time**;
4. lets MCLC SHA-1 **every asset object** (~4,000 files) and fetch libraries over **2 sockets**.

The target: **a warm launch makes 2 small HTTP requests and hashes nothing it hashed
before.** A cold install should be limited by bandwidth, not by request latency.

## Code path today (profiled by reading the code, 2026-10-31)

| Step | Where | Work on a warm launch | Notes |
|---|---|---|---|
| 1. Auth | `msAuthManager` | refresh token | not awaited before launch ([#40](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/40)) |
| 2. Java | Nexus_Java `isJavaInstalled()` | stat | fine |
| 3. NeoForge installer | `neoforgeDownloader.js` | stat (no hash: [#38](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/38)) | fine |
| 4. Mod list | Nexus_Mods `loadModsFromJsonUrl` | **~330 API calls** | the main warm-launch cost; quotas (below) |
| 5. External files | `loadExternalFilesFromJsonUrl` | 1 call + a `ModFile` per entry | |
| 6. Sync | `updateMods(true, true)` | **sequential** SHA-1/MD5 of ~690 files (~1–2 GB of jars) | CPU and disk bound |
| 7. MCLC | `handler.js` | SHA-1 of ~4,000 assets (`Promise.all`), unawaited library check, `maxSockets: 2` | [#79](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/79) |
| 8. Forge processors | ForgeWrapper | skipped when already installed | |
| 9. JVM start | game | 30–90 s of mod loading | outside the launcher; see "In game" below |

Installer size: each release packed a second copy of Electron into `app.asar`. Fixed in
[#78](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/78) (asar 333 → 34 MB). This
halves the first download and every self-update.

## Optimisations, by gain per effort

| # | Change | Gain | Effort | Where |
|---|---|---|---|---|
| O1 | **Lockfile** (spec 009): the launcher downloads one `modList.lock.json` (with an ETag) instead of resolving 330 entries | removes step 4 entirely; no API quota use by players | M | Provisioning, Nexus_Mods |
| O2 | **Conditional fetch**: `If-None-Match` / `If-Modified-Since` on the lock and index; a 304 means nothing changed, so skip to step 7 | warm launch in ~2 requests | S | Nexus_Mods |
| O3 | **Hash cache**: store `{path → size, mtimeNs, sha1}` in `.arffornia/hashcache.json`; re-hash only when size or mtime changed | step 6 drops from minutes on HDDs to milliseconds | S | Nexus_Mods |
| O4 | **Parallel downloads + hashing**: a bounded pool (6–8 downloads, `os.cpus()` hash workers in `worker_threads`); verify the hash *while streaming* | cold install limited by bandwidth | M | Nexus_Mods |
| O5 | **MCLC tuning**: `overrides.maxSockets = 16`; skip the asset re-hash when a verified stamp (asset index sha1 + count + total size) matches; await the library check (patch) | step 7 from seconds to near zero on warm | S | launcher (+ patch) |
| O6 | **Prefetch in the background**: after login, while the player looks at the home page, run steps 2–7 with low priority, so *Play* only starts the JVM | perceived launch ≈ JVM start | M | launcher |
| O7 | **Delta updates of the pack**: the lock diff tells exactly which files changed, so only those are downloaded. Old jars are kept until the new ones verify (atomic swap) | update = changed bytes only | S (after O1) | Nexus_Mods |
| O8 | **Launcher self-update deltas**: electron-builder already publishes `.blockmap` files; keep the NSIS differential download working (unsigned is fine on Windows) | smaller launcher updates | – | already there |
| O9 | **"Repair game files"** button: a full re-hash on demand, since normal launches trust the cache | safety net for O3/O5 | S | launcher |
| O10 | **Progress you can trust**: one progress bar over bytes, not files; show "Up to date, starting…" on warm launches | perceived speed | S | launcher |

### CDN-free tricks

- **Point at the original CDNs, not at us.** The lock stores the final `edge.forgecdn.net`,
  `cdn.modrinth.com` and GitHub release URLs. The homelab never serves jars, and those hosts are free and fast.
- **One mirror as fallback, not primary:** if a file 404s upstream, fall back to a copy in the
  in-cluster Garage S3 that the CI boot test already downloaded (optional, D3).
- **Compression:** the lock and the index are small JSON, so gzip them (GitHub raw already
  does). Jars are already compressed.
- **HTTP keep-alive and HTTP/2:** one agent with keep-alive per host (axios + `http.Agent({keepAlive:true})`).

### API quotas

- **Modrinth:** a per-IP rate limit (documented as 300 requests per minute; the docs page
  could not be re-opened from the agent sandbox on 2026-10-31) and a required unique
  `User-Agent` ([docs.modrinth.com](https://docs.modrinth.com/docs/getting-started/)).
  `api.modrinth.com/v2/versions_files` resolves many hashes in **one** call, which helps the
  lock generator.
- **CurseForge:** the official API needs a key (free, from the CurseForge for Studios console). `api.curse.tools`
  is a community proxy with no SLA. After O1, **only CI** calls these APIs. Players never do,
  so quotas stop being a player problem.
- **GitHub:** unauthenticated REST is 60 requests/hour/IP. Release *downloads* are not rate
  limited the same way, but the API lookups (`api.github.com/repos/.../releases/tags/...`) are.
  The lock removes them too.

### In game (after the JVM starts)

Not the launcher's code, but players feel it as "Play is slow":

- Default JVM flags for a 330-mod pack: `-XX:+UseZGC -XX:+ZGenerational` on Java 21, or
  well-tuned G1. The RAM setting is ignored today ([#41](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/41)).
- Startup mods to evaluate through the spec 009 pipeline: ModernFix (dynamic resources,
  faster launch), FerriteCore (memory). Check whether they are already in the pack before
  proposing them.

## Measurement first

Add `performance.mark` timings per step, written to the launcher log, plus a summary line:
`launch: auth 0.4s, java 0.0s, mods 41.2s (330 lookups), sync 18.7s (690 files hashed),
mclc 9.1s, jvm 63s`. Measure on Windows HDD, Windows SSD and Linux before and after each
change. Without those numbers, no optimisation PR merges.

## Decisions needed

| # | Decision | Options | Default |
|---|---|---|---|
| D1 | Order | O1+O2+O3 first / MCLC first / everything at once | **O3 + O5 first (small, local), then O1 + O2 with spec 009** |
| D2 | Background prefetch (O6) | on by default / opt-in / no | **On, paused while a game runs** |
| D3 | Fallback mirror in Garage S3 | yes / no | **No for now** (homelab not 24/7) |
| D4 | MCLC fixes | upstream PR + `patch-package` meanwhile / fork | **Upstream PR + `patch-package`** |

## Work breakdown

| Task | Repo | Effort |
|---|---|---|
| Launch timing marks + summary log line | launcher | S |
| Hash cache (O3) + "Repair game files" (O9) | Nexus_Mods, launcher | S |
| MCLC `maxSockets`, asset stamp, awaited library check (O5) | launcher | S ([#79](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/79)) |
| Conditional fetch (O2) | Nexus_Mods | S |
| Lockfile consumer (O1) + delta/atomic swap (O7) | Nexus_Mods | M (with spec 009) |
| Parallel downloads + streaming hash (O4) | Nexus_Mods | M |
| Background prefetch (O6) + byte-based progress (O10) | launcher | M |
| Installer size fix | launcher | done: [#78](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/78) |

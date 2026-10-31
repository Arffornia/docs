---
status: proposed
date: 2026-10-31
---

# 0013 · Keep Provisioning and Nexus_Mods; add a generated lockfile and a compatibility gate

## Context
- Provisioning is git-versioned (good) but resolves ~330 mod descriptions online on every
  server boot and every launcher *Play*, uses `tag: latest` for the owner's jars, and has no
  compatibility check before production.
- packwiz and `.mrpack` exist as standard formats. FTB fixes incompatibilities with configs,
  data scripts, a pack companion mod and upstream fixes.

## Decision (proposed)
- Keep `modList.json` + `storage/` + Nexus_Mods (ADR 0003).
- CI generates `modList.lock.json`: final URLs, sizes, sha1 and sha512, mod ids, sides and
  dependencies, with GitHub-release entries pinned to versioned tags. Servers and the launcher
  read the lock and make no API calls at run time.
- Every Provisioning PR passes a compatibility pipeline: resolve, static checks, a server boot
  test, and a diff comment. Code-level fixes go in a small `arffornia-patches` mixin jar.
- `.mrpack` is exported from the lock as a release asset, for players on other launchers.
- Details: [spec 014](../specs/014-modpack-lockfile-and-compatibility.md).

## Consequences
- Reproducible packs, faster boots and launches, and API quotas used by CI only.
- One more generated file per kind, and the CI job must stay green to merge.

## Alternatives considered
- **packwiz:** a good format, but it would replace Nexus_Mods, and its upstream has slowed.
- **mrpack as the source format:** CurseForge entries would lose their ids, and the format
  adds little over a lock generated from our own list.
- **Keep as is:** no reproducibility and no gate; the CC: Tweaked double install shows the risk.

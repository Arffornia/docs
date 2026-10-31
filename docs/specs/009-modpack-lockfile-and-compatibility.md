---
status: Draft: needs decisions
date: 2026-10-31
---

# 009 · Modpack lockfile and mod-compatibility pipeline

## Summary

Provisioning works, and git versioning is its strength. Keep it. Three things make it
artisanal:

1. **Nothing is resolved ahead of time.** Every server boot and every *Play* click asks CurseForge
   (through the third-party `api.curse.tools`), Modrinth and GitHub for ~330 file
   descriptions before downloading anything.
2. **`tag: latest` and `main` are production.** The same commit can install different jars
   on two days.
3. **There is no compatibility gate.** A new mod is added by hand, and the first time anyone
   learns that it crashes the pack is the next boot.

Proposal: keep `modList.json` + `storage/` + Nexus_Mods (an owner library, [ADR 0003](../decisions/0003-keep-owner-libraries.md)).
Add a **generated lockfile** and a **compatibility pipeline** in CI, and export **`.mrpack`**
for interop. Do not migrate to packwiz. See [ADR 0012](../decisions/0012-modpack-lockfile.md).

## Options evaluated (2026-10-31)

| Option | What it is | Pros | Cons for Arffornia |
|---|---|---|---|
| **Keep as is** | `modList.json` (CF/MR/GH ids) + `storage/` + bot-generated `index.json` | works, git-native, owner library | no lock, 330 API calls per run, no gate |
| **packwiz** | Go CLI, one TOML per mod + `index.toml` with hashes, `packwiz-installer` bootstrap ([repo](https://github.com/packwiz/packwiz), MIT) | git-friendly, hashes, exports `.mrpack` and CF zip | would replace Nexus_Mods (against ADR 0003); upstream activity slowed (last push 2025-01 per [ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fpackwiz%2Fpackwiz)); CF files with third-party downloads disabled need manual handling; Java bootstrap on clients |
| **`.mrpack`** (Modrinth pack format) | zip with `modrinth.index.json` (path, sha1+sha512, size, download URLs, client/server env) + `overrides/` | a **lockfile format**, importable by Prism, ATLauncher and the Modrinth app | Modrinth-hosted packs only allow some download hosts; fine for self-hosting |
| **CurseForge manifest zip** | `manifest.json` (projectID/fileID) + overrides | CF app import | ids only, no hashes; still needs the CF API |
| **Prism / MultiMC instance export** | instance zip | players who prefer Prism | not a source format |
| **Lockfile in our format** (proposed) | CI resolves `modList.json` → `modList.lock.json` with final URL, size, sha1/sha512, mod id, version, side, dependencies | zero API calls at run time, reproducible, diffable in PRs, same library | one CI job and a Nexus_Mods reader to write |

**Recommendation:** add the lockfile and keep everything else. Export `.mrpack` from the lock as
a release asset for players who use other launchers.

## Design

### 1. Lockfile

```jsonc
// config/server/modList.lock.json (generated, committed by CI on the PR branch)
{
  "schema": 1,
  "minecraft": "1.21.1", "loader": "neoforge", "loaderVersion": "21.1.172",
  "generatedFrom": "modList.json@<sha256>",
  "files": [
    { "path": "mods/appliedenergistics2-19.2.17.jar",
      "source": { "curseforge": { "projectId": 223794, "fileId": 6488853 } },
      "url": "https://edge.forgecdn.net/files/6488/853/appliedenergistics2-19.2.17.jar",
      "size": 8123456, "sha1": "…", "sha512": "…",
      "modId": "ae2", "version": "19.2.17", "side": "both",
      "requires": ["guideme"], "breaks": [] }
  ]
}
```

- `github-releases` entries are locked to a **tag and asset digest**, never `latest`.
  Arffornia_Mods and Arffornia_Proxy publish versioned tags. A PR that bumps the tag is the
  release mechanism.
- Nexus_Mods gets `loadModsFromLock(url)`. It makes no metadata calls, verifies hashes after
  download, and deletes nothing whose entry failed (already in Nexus_Mods #21).
- The config-updater and the launcher read the lock. The old path stays as a fallback for one
  release.
- A **server ⊂ launcher** check uses `side` to replace the hand-kept duplicate lists.

### 2. Compatibility pipeline (CI on every Provisioning PR)

| Stage | Cost | What it catches |
|---|---|---|
| **Resolve** | seconds | unknown ids, wrong MC/loader version (`gameVersions`), files removed upstream |
| **Static** | seconds | duplicate mod ids (CC: Tweaked is installed twice today), missing required dependencies, declared `incompatible` / `breaks` ranges from `neoforge.mods.toml`, client-only mods on the server, a mixin config targeting a class another mod also overwrites (a warning) |
| **License / distribution** | seconds | CF "third-party distribution disabled" files, licenses that forbid redistribution |
| **Boot test (server)** | ~5–10 min, ~8 GiB | `itzg/minecraft-server` in Docker with the lock and a fixed seed, wait for `Done (`, run `/forge mods`, fail on `ERROR`, mixin apply failures, missing registries or crash reports. Keep `latest.log` as an artifact |
| **Boot test (client, nightly)** | ~10 min | headless client to the title screen under xvfb, the same log rules (see the in-game testing spec) |
| **Diff report** | seconds | a PR comment with added, removed and updated mods, new dependencies, the size delta and boot time vs `main` |

Resource rule: one full-pack environment at a time. The boot test runs on GitHub-hosted
runners (free for public repos, 16 GiB RAM on `ubuntu-latest`) or on the homelab runner when it
is up, never both.

### 3. Patching incompatibilities (what FTB does)

FTB packs combine four layers. Arffornia should use the same order, cheapest first:

1. **Config:** `defaultconfigs/`, mod configs and the server `.toml` files (already in `storage/`).
2. **Data:** KubeJS or datapacks for recipes, tags and loot, plus unification of duplicate ores
   (AlmostUnified-style). This is already used. The recipes datapack is ADR 0006.
3. **A pack companion mod:** FTB ships *FTB Pack Companion* (`ftbpc`, all rights reserved,
   already in this pack) and per-pack companions for fixes that need code. Arffornia's
   equivalent is a small **`arffornia-patches`** module (Mixins, `@Pseudo` and
   conditional mixins keyed on the target mod's version through a mixin config plugin). It is
   versioned with the pack and every patch is linked to an issue.
4. **Upstream:** open an issue or PR on the broken mod, and remove the local patch once a
   fixed version is locked.

### 4. "Propose a mod" skill (agent-kit, Arffornia layer)

With 330 mods, the default answer is **no**. The skill (`mod-proposal`) makes an agent:

1. Check **overlap**: search the lock for mods with the same role (storage, energy, ores,
   machines, maps). If one exists, explain why the new mod is better or stop.
2. Check **fit**: 1.21.1 NeoForge build, still maintained (last file < 6 months), license
   allows redistribution, client/server side, RAM and TPS reputation.
3. Check **design fit**: does it support Arffornia's progression (stage gating, the
   Satisfactory-style machines in specs 002/003), or bypass it?
4. Run the pipeline: open a Provisioning PR with the lock change only, and read the boot test.
5. Write a **proposal card** for Brian's review stack: what it adds for players,
   overlap, cost (size, boot-time delta, RAM), risks, and a recommendation (add / skip /
   replace X). Brian never sees a mod proposal without a green boot test.

## Testing

- Unit: lock generator with recorded API fixtures, plus static rules with synthetic `mods.toml` files.
- Pipeline: a fixture PR that adds a known-incompatible pair must fail.
- Nexus_Mods: `loadModsFromLock` offline tests, hash mismatch → failure, no deletion.

## Migration

1. The lock generator runs in CI and writes `modList.lock.json` next to `modList.json` (no consumer yet).
2. Nexus_Mods reads the lock behind an option, and the config-updater switches first (servers).
3. The launcher switches. Old launchers keep reading `modList.json` for one release.
4. Pin `github-releases` tags, and stop `latest`.

## Decisions needed

| # | Decision | Options | Default |
|---|---|---|---|
| D1 | Pack format | own lockfile / packwiz / mrpack as source | **Own lockfile + mrpack export** |
| D2 | Boot test runner | GitHub-hosted / homelab self-hosted / both | **GitHub-hosted** (free, no homelab dependency) |
| D3 | CurseForge API | keep `api.curse.tools` / official CF API key (free, needs an account) | **Official key in CI only**; clients read the lock and need no API |
| D4 | Patch module | part of Arffornia_Mods / separate `arffornia-patches` jar | **Separate jar** (ships with the pack, not with gameplay) |
| D5 | mrpack release asset | yes / no | **Yes** |

## Work breakdown

| Task | Repo | Effort |
|---|---|---|
| Lock generator + CI job + schema test | Provisioning | M |
| `loadModsFromLock` with hash verification | Nexus_Mods | M |
| Static compatibility rules (dupes, deps, breaks, side) | Provisioning | M |
| Server boot test job + diff comment | Provisioning | M |
| Pin GitHub-release tags (mod, proxy) | Provisioning, Mods, Proxy | S |
| mrpack export as a release asset | Provisioning | S |
| `arffornia-patches` scaffold + first patch | new repo or Mods | M |
| `mod-proposal` skill | agent-kit | S |

# Nexus libraries

Small TypeScript libraries written for Arffornia and published on npm under `@arffornia/`.
They are a deliberate choice: improved, never replaced ([ADR-0003](../decisions/0003-keep-owner-libraries.md)).

| Library | Job | Used by |
|---|---|---|
| [Nexus_Mods](https://github.com/Arffornia/Nexus_Mods) | resolve a mod list (CurseForge, Modrinth, GitHub), download, verify, remove unlisted files; generate file indexes | launcher, config-updater |
| [Nexus_Java](https://github.com/Arffornia/Nexus_Java) | find and install a Java runtime (Azul Zulu) for the player's OS and architecture | launcher |
| [Nexus_Logger](https://github.com/Arffornia/Nexus_Logger) | file + console logger | launcher |
| [Nexus_Saver](https://github.com/Arffornia/Nexus_Saver) | key/value settings file | launcher |

## Standards for the libraries

- Runtime dependencies declared as `dependencies` (not dev).
- Lockfile committed, CI on Node 22 with offline unit tests; live network tests nightly.
- Published from CI on tag with npm provenance; the repo version matches npm.
- Downloads are verified after writing (temp file → hash → rename), failures are reported,
  never silently turned into deletions.

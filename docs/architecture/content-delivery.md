# Content delivery

![Content delivery](../assets/diagrams/content-delivery.light.png#only-light)
![Content delivery](../assets/diagrams/content-delivery.dark.png#only-dark)

1. A change to `config/{server,proxy,launcher}/` is pushed to `Arffornia_Provisioning` `main`.
2. A workflow regenerates `index.json` (SHA-1 of every stored file) and commits it.
3. **Servers:** at pod start the `config-updater` init container runs Nexus_Mods: it resolves
   every mod (CurseForge through `api.curse.tools`, Modrinth, GitHub releases), downloads what
   changed, copies stored files and removes what is no longer listed. The server image then
   fills `${CFG_*}` placeholders from Secrets.
4. **Players:** the launcher runs the same library against `config/launcher/` before each launch,
   and installs Java (Azul) and NeoForge if needed.

!!! warning
    There is no release channel: a merge to `main` reaches every server and player. Mod and
    proxy jars are pulled from their latest GitHub release.

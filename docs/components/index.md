# Components

| Component | Repo | Stack | Runs on |
|---|---|---|---|
| [Website](website.md) | Arffornia_Website | Laravel 12, PHP 8.2, Vite | cluster (nginx + php-fpm) |
| [Launcher](launcher.md) | Arffornia_Launcher_V.5.2 | Electron, Vue 3 | players' PCs |
| [Mod](mod.md) | Arffornia_Mods | NeoForge 1.21.1, Java 21 | game server and clients |
| [Proxy plugin](proxy.md) | Arffornia_Proxy | Velocity, Java 17 | proxy pod |
| [Provisioning](provisioning.md) | Arffornia_Provisioning | TypeScript, Docker | init containers |
| [Nexus libraries](nexus-libs.md) | Nexus_Mods, Nexus_Java, Nexus_Logger, Nexus_Saver | TypeScript | launcher, config-updater |
| [Infrastructure](infra.md) | TheGostsniperfr/infra | Kubernetes, Argo CD, Vault | homelab |

Also in the org: `keycloak-theme-arffornia` (login theme), `minecraft-server-charts` (fork of
the itzg charts, kept for one fix to the proxy chart), `minecraft-oauth` (fork), and archived
launchers and website from earlier versions. `Arffornia_Bootstrap` is no longer used.

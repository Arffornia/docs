# Glossary

| Term | Meaning |
|---|---|
| **Arcane** | The live game server (Kubernetes overlay `arcane`). |
| **Nexus** | A second server overlay, currently disabled. Also the prefix of the owner's libraries (Nexus_Mods, Nexus_Java…). |
| **Milestone** | A node of the progression graph. Completing it unlocks items or recipes. |
| **Stage** | A group of milestones; a tier of the progression. |
| **Unlock** | An item gated by a milestone. Its normal recipe is removed and it is made in an Arffornia machine. |
| **Space Elevator** | Two-block structure where players deliver items to complete a milestone. |
| **Crafter** | The first Arffornia machine: a powered 3×3 crafter for unlocked recipes. |
| **Progression** | A progression record (per player or team) holding completed milestones and the current target. |
| **Modpack / mod list** | `modList.json` in Provisioning: the mods servers and launchers install. |
| **config-updater** | Init container that syncs mods and config into a server or proxy volume at start. |
| **Preview environment** | Planned: a temporary server deployed from a pull request for testing. |
| **Service account** | Credentials a game component uses to call the website API (Sanctum token). |
| **NuVotifier** | Protocol and plugin that receives votes from server-listing sites. |
| **FE** | Forge Energy, the energy unit machines consume. |
| **GameTest** | Minecraft's built-in automated test framework, run headless with `runGameTestServer`. |
| **ADR** | Architecture Decision Record, see [Decisions](decisions/index.md). |
| **Agent-ready** | Issue label: scoped with acceptance criteria, an AI agent may implement it. |

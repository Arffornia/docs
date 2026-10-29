# Mod

**Repo:** [Arffornia_Mods](https://github.com/Arffornia/Arffornia_Mods) ·
**Stack:** NeoForge 21.1 for Minecraft 1.21.1, ModDevGradle, Java 21

The `arffornia` mod runs on the server and on clients. It adds the progression system that
balances a large modpack: a graph of **milestones** grouped into **stages**, in the spirit of
Satisfactory. Items "unlocked" by a milestone lose their normal recipe and can only be made
in Arffornia machines once the milestone is reached.

| Feature | What it does |
|---|---|
| Progression graph | screen on `G`, target milestone in the HUD |
| Space Elevator | 2-block structure; deliver the items, launch, complete the milestone |
| Crafter | 2-block FE machine running the custom recipes unlocked by milestones |
| Recipe banning | removes the original recipes of unlocked items |
| Shop rewards | `/arffornia shop claim_reward` delivers purchases from the website |
| Teams | FTB Teams membership synced to the website |
| JEI | Crafter recipes shown in JEI |

## Talks to

- **Website API** (`https://arffornia.com/api`): public reads (profiles, progression,
  recipes) from server *and* clients; authenticated writes from the server with a service
  account (Sanctum token).
- **Website Postgres**, directly from the server, for shop rewards (to be replaced by API
  calls — see issues).

## Develop

```bash
./gradlew build                 # ~8 min the first time
./gradlew runClient             # dev client
./gradlew runGameTestServer     # headless tests (suite being added)
make check
```

## Direction

- Recipes as a generated datapack with a real recipe type ([ADR-0006](../decisions/0006-recipes-as-datapack.md)).
- A machine framework (slot layouts, side config, recipe processor) so new machines are data
  plus a model, then Immersive-Engineering-style multiblocks with a futuristic look.
- English and French lang files for every string.

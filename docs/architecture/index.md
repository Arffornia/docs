# Architecture

One model, several views. Each diagram answers one question and is generated with
[Noodle](../contributing/diagrams.md) from `architecture/arffornia/`.

| View | Question |
|---|---|
| [Runtime](runtime.md) | How do players, browsers and vote sites reach Arffornia, and what talks to what? |
| [Content delivery](content-delivery.md) | How do mods and config files reach servers and players? |
| [Flows](flows.md) | What happens when a player logs in and joins, and when a vote turns into a reward? |
| [Tech stack](tech-stack.md) | What is the platform built with? |
| [Repositories](repositories.md) | Where do I commit to change X? |
| [Preview environments](previews.md) | How will each pull request get its own test server? (planned) |

## Key properties

- **The website is the hub.** It owns players, progression, shop and votes; the mod, the
  proxy plugin and the launcher all call its API.
- **Provisioning `main` is production.** Servers resync mods and configs at every start,
  launchers at every launch.
- **GitOps.** Argo CD deploys `HEAD` of the infra repo with auto-sync.
- **Secrets** come from Vault at deploy time; git holds `${CFG_*}` placeholders only.

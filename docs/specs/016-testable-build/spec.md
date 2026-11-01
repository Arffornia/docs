---
status: "Draft: needs decisions"
date: 2026-11-01
---

# 016 · Testable build: beta launcher, staging, `playtest up <pr>`

| | |
|---|---|
| **Goal** | Brian clicks a link or runs one command, and tests what agents built, this week. |
| **Repos** | Arffornia_Launcher_V.5.2, Arffornia_Mods, Arffornia_Provisioning, Arffornia_Website, Arffornia_Playtest, TheGostsniperfr/infra, docs |
| **Phases** | 1. Beta launcher · 2. Staging · 3. Real `playtest up <pr>` · 4. UI round 4 into code |
| **Replaces** | [ADR-0007](../../decisions/0007-preview-environments.md) (proposed, a server per PR) by fixed, capped slots. ADR-0016 is written once D4 to D6 are answered. |

## Summary

Agents merged more than a hundred PRs in a week. Almost none of it is visible to Brian.

| What | State on 2026-11-01 | Why it is invisible |
|---|---|---|
| Launcher | Last release v0.1.15 (2026-07-31); 49 commits on `main` since | Releases need a tag; no beta build exists |
| Arffornia mod | Last release v1.0.25 (2026-07-31); 48 commits on `main` since | Same; prod resolves the `latest` release |
| Website | Prod runs the `latest` image (built on every `main` push), `pullPolicy: Always` | Merged code reaches prod at the next restart, with no staging before it |
| Modpack | Prod server and every launcher read Provisioning `main` over raw GitHub | Every merge is live at the next restart or Play click, with no staging |
| Class-C PRs | 13 held with `needs-playtest`, plus Provisioning #42 and infra #44 (draft) | No environment where Brian can try them |
| Playtest kit | [Arffornia_Playtest](https://github.com/Arffornia/Arffornia_Playtest): `guide` and `report` work, `up` is dry-run only | No cluster target, no beta client |

This spec is the shortest path to "Brian clicks and tests". Each phase works on its own.

1. **Beta launcher.** Every push to `main` builds a side-by-side "Arffornia Launcher Beta" for
   Windows, Linux (AppImage, runnable on NixOS) and macOS (unsigned). Normal players never
   receive it.
2. **Staging.** `staging.arffornia.com` runs the website from `main` with its own database.
   One **test slot** server runs the pack from `main` with the mod from `main`.
3. **`playtest up <pr>`.** A small file in Arffornia_Playtest asks Argo CD for an environment
   built from the PR's images: a website slot (`pr1`–`pr3.arffornia.com`) or the test slot. It
   has a TTL and a hard resource cap. A playtest card on the review stack lists the URLs, with
   a 10-minute checklist per PR. Brian's OK on the card approves the PR.
4. **UI round 4.** The order for turning the approved title screen, loading screen and early
   window into mod and launcher code, each tested through phases 1 to 3.

## Goals / non-goals

**Goals**
- Brian tests merged work and held PRs from a link, on NixOS and Windows, with no local build.
- Normal players never get a beta launcher, a staging pack or a PR build. Nothing changes
  for them in this chantier.
- Ephemeral environments are capped by quota and by TTL. They sleep with the homelab, and
  they never reach prod data.
- Mac players can run the game. The Mac beta is built and smoke-tested in CI. Brian has no
  Mac yet.
- Only free tools: GitHub-hosted runners (public repos), GHCR, GitHub releases, Argo CD,
  Kyverno and the cluster that already exists.

**Non-goals**
- The agent that plays the game (probe mod, [agent spec](https://github.com/Arffornia/Arffornia_Playtest/blob/main/docs/agent-spec.md)).
  It plugs in later, and its verdict stays advisory, per Brian's answer.
- Code signing ([ADR-0015](../../decisions/0015-free-signing-and-updates.md) covers it). The beta is unsigned.
- Pinning prod to promoted versions (D11). It is proposed here, but not built in this chantier.
- A server per PR for the full pack. There is one test slot (Brian's resource rule).

## Player experience

Normal players see nothing new. The prod launcher keeps updating from GitHub `releases/latest`,
which never returns a pre-release.

Brian, after phase 1:
1. He opens the `beta` pre-release on the launcher repo and downloads the file for his OS.
   On NixOS he runs the copy-prompt instead.
2. "Arffornia Launcher Beta" installs next to the normal launcher. It has its own name and
   icon badge, its own data folder (`.Arffornia_beta/`), and updates only from the `beta` channel.
3. In Settings → **Environment**, he picks **Production**, **Staging** or **Test slot**. Each
   choice has its own game folder, mod list, website API and server.

After phase 3, the review stack shows a **Playtest** card with one row per PR:
*Open* (the URL, or "Beta launcher → Test slot"), the 10-minute checklist, and **OK / KO + notes**.

## Design

### Phase 1 · Beta launcher from `main`

**Build.** A new `beta.yml` workflow in the launcher repo:

| Trigger | What it does |
|---|---|
| push to `main` (D2) | Matrix `ubuntu-latest`, `windows-latest`, `macos-latest`. Version `<next patch>-beta.<run>` (for example `0.1.16-beta.12`). Uploads Actions artifacts (30 days) and replaces the assets of the rolling **`beta`** pre-release (`gh release upload --clobber`, `GITHUB_TOKEN` with `contents: write`). Release notes carry the commit SHA and the list of PRs since the last stable release. Adds `SHA256SUMS`. |
| `pull_request` | The same beta flavour, as **artifacts only**, named `launcher-pr-<n>`. This is how the launcher's class-C PRs are tested (phase 3). |
| `workflow_dispatch` | A manual rebuild. |

**What makes it a beta.** One build-time constant, `ARFFORNIA_CHANNEL=beta`, injected with a Vite
`define`. Everything else follows from it:

| | Prod build (unchanged) | Beta build |
|---|---|---|
| App id / name | as today | `fr.arffornia.launcher.beta` / "Arffornia Launcher Beta" (`-c.appId`, `-c.productName`) |
| Data folder | `.Arffornia_V.5.2` | `.Arffornia_beta/<env>`; on macOS, under `~/Library/Application Support/Arffornia/` |
| Updater | GitHub provider, `releases/latest` | generic provider `…/releases/download/beta`, channel `beta` (`beta.yml`, `beta-linux.yml`, `beta-mac.yml`) |
| Environment picker | hidden, Production only | Production / Staging (phase 2) / Test slot (phase 2) |
| Join on Play | as today | `quickPlay` to the environment's server when it is not Production |

**Guards, so the beta never reaches players.**
- `release.yml` ignores pre-release tags (`tags: ['v*.*.*', '!v*-*']`). A rolling `beta` tag
  does not match the pattern either.
- Releases are published with `GITHUB_TOKEN` instead of the `GH_TOKEN` PAT, as ADR-0015 says.
- After every publish, a step checks that `releases/latest` is still the newest **stable** tag.
  If it is not, the step fails the run and opens an issue.
- Unit tests check two things: a build without the constant has no `channel` and no
  `allowPrerelease`; a beta build never points at the GitHub provider.
- The website and README link only `releases/latest`.

**Platforms.**

| OS | File | Brian's path |
|---|---|---|
| Windows | NSIS `Setup.exe` (x64) | Download, then SmartScreen → *More info* → *Run anyway* (unsigned) |
| Linux / NixOS | `AppImage` | `appimage-run` (copy-prompt below). A `.#beta` flake output comes later (D3) |
| macOS | `dmg` + `zip`, **separate arm64 and x64 files** (Brian's answer) | Built and smoke-tested on the `macos-latest` runner (the `check-macos` job already does it). No auto-update on macOS (ADR-0015). Not hand-tested until Brian has a Mac |

**Mac players.** The beta shows what `main` pins. Mac players also need
[Nexus_Java #9](https://github.com/Arffornia/Nexus_Java/pull/9) (Java path on macOS), a Nexus_Java
release after 1.0.5, and the launcher dependency bump. The phase 1 PR lists this as a blocker
for "Mac works", not for the beta.

### Phase 2 · Staging website and test slot from `main`

All of it is GitOps in `TheGostsniperfr/infra`. Argo CD syncs it; Vault values come only from
Terraform, which runs on Brian's machine.

| Piece | Where | Content | Cap |
|---|---|---|---|
| `arffornia-staging` namespace | infra `k8s/config/arffornia/staging` | Website chart from `main`, image tag `main` (a new tag pushed next to `latest`). In-namespace Postgres on `emptyDir` with a post-sync Job: `migrate --force` + `db:seed --class=E2ESeeder` (D8). `APP_ENV=staging`. Own `APP_KEY` and service user. No prod secret. | quota 1 CPU / 2 GiB limits, 0 LoadBalancer |
| `staging.arffornia.com` | `dns.tf` CNAME (DNS-only or proxied, like `@`) + `secure-route` | The website; `/pack/` serves the staging mod list (below) | – |
| `arffornia-slot` namespace | infra `k8s/config/arffornia/slot` | The **test slot**: the existing server base (`itzg/minecraft-server` + config-updater), `online-mode=true`, a whitelist (Brian + testers), `emptyDir` world. `CFG_API_BASE_URL` points at **staging**, never at prod. By default it runs `main` (that is the staging server). In phase 3 a PR can take it over. | quota 4 CPU / 17 GiB limits, 1 server pod; `OffhoursSchedule` 03:00–07:00 like prod |
| `test.arffornia.com:25566` | DNS-only A record + a MetalLB `LoadBalancer` defined in infra (not by a PR) + a router port forward (D12) | Minecraft for the slot | – |
| **pack-files** | Arffornia_Playtest `envfiles/` → image `ghcr.io/arffornia/playtest-envfiles` | A small nginx. It serves `config/{server,launcher}/modList.json` rewritten so that the `Arffornia_Mods` entry uses tag `edge` (or `pr-<n>`) instead of `latest`, and proxies every other path to raw GitHub at the chosen Provisioning ref. The config-updater (`BASE_URL`) and the beta launcher (mod list + external files URL) read it. **No change** to Nexus_Mods or the config-updater. | 64 MiB |
| `edge` mod build | Arffornia_Mods `build.yml` | On every push to `main`, refresh the rolling **`edge`** pre-release (`arffornia.jar`). Prod is unaffected: it asks for `latest`, which skips pre-releases. | – |
| Policies | infra `k8s/config/kyverno` | For namespaces labelled `arffornia.com/env`: generate a `LimitRange` and a default-deny `NetworkPolicy`. Egress is allowed to DNS, the internet, its own namespace, and from the slot to `arffornia-staging`; **never** to prod namespaces or to Vault. Images are restricted to `ghcr.io/arffornia/*`, `itzg/*` and `postgres`. | – |

The beta launcher's **Staging** and **Test slot** environments use the same server and pack:
API `https://staging.arffornia.com/api/`, mod list `https://staging.arffornia.com/pack/…`, and
server `test.arffornia.com:25566`. The two names are kept apart because, in phase 3, Test slot
follows the PR that holds the slot.

**Mod release.** After staging is green, Brian tags `Arffornia_Mods` v1.0.26 (agents never tag).
[Mods #49](https://github.com/Arffornia/Arffornia_Mods/pull/49) and
[Provisioning #35](https://github.com/Arffornia/Arffornia_Provisioning/pull/35) ship with it. They
are first tested together on the slot, as a two-PR environment (phase 3), then merged and tagged
in one quiet window.

**Prod today follows `main`** (website image `latest`, pack from raw `main`). Staging alone does
not change that. D11 asks whether to pin prod to promoted versions in a follow-up.

### Phase 3 · `playtest up <pr>`: ephemeral environments on fixed slots

**Fixed slots, not one environment per PR.** Fixed hostnames need no new wildcard certificate
(`*.arffornia.com` is already on the shared gateway). They let a test Microsoft app register its
redirect URIs once (D7), and they make the cap plain.

| Slot | Hostname | Runs | Cap per env | Max at once |
|---|---|---|---|---|
| `pr1`, `pr2`, `pr3` | `pr<k>.arffornia.com` | a Website PR: the **PR's chart and images**, its own Postgres, seeded | 0.5 CPU / 768 MiB | 3 |
| `slot` | `test.arffornia.com:25566`, files on `test.arffornia.com/pack/` | one or more pack PRs: Provisioning ref + Mods `pr-<n>` jar + Proxy PR (optional) | 4 CPU / 16 GiB | 1 (Brian's rule: one full pack at a time) |

**How an environment is requested (D4).** Each slot is one file on the `envs` branch of
Arffornia_Playtest, `envs/<slot>.yaml`:

```yaml
slot: pr2
kind: website            # website | pack
prs: [Arffornia/Arffornia_Website#115]
head: 3f9c2e1            # PR head SHA when requested
requestedBy: TheGostsniperfr
expires: 2026-11-04T20:00:00Z
```

- An Argo CD `ApplicationSet` (git file generator, on a public repo, so no token) makes one
  `Application` per file. Its dedicated `AppProject` `playtest` allows only the
  `arffornia-previews` and `arffornia-slot` namespaces, no cluster-scoped objects, no
  `VaultSecret` and no `LoadBalancer`. The namespace `ResourceQuota` is the hard cap: an
  extra environment stays `Pending` and never starts.
- Website slot: the source is the website chart **at the PR head**, which is how
  [#86](https://github.com/Arffornia/Arffornia_Website/pull/86) gets tested. The images are
  `pr-<n>`, plus Postgres and the seed Job from an infra path, so they work with any chart version.
- Pack slot: the config-updater gets `BASE_URL=https://test.arffornia.com/pack/`. pack-files
  points at the Provisioning PR branch and rewrites the mod to `pr-<n>`.
- **Writes** go through the contents API, as normal commits on `envs`, so there is no force-push.
  Brian's `gh` or an agent can write. An agent prepares the environment before Brian, so the
  card's link already works when he opens it.

**Builds a PR must publish (agents add them):**

| Repo | On `pull_request` (same-repo branches only, never forks) |
|---|---|
| Website | Push `ghcr.io/arffornia/{arffornia_website,nginx_arffornia_website}:pr-<n>` and `:pr-<n>-<sha7>` (today PR images are built but not pushed) |
| Mods | Upload `arffornia.jar` to pre-release `pr-<n>` (deleted when the PR closes) |
| Launcher | Beta-flavour artifacts `launcher-pr-<n>` (phase 1) |
| Provisioning | Nothing: the branch is the bundle |

**TTL (D6).** `expires` defaults to 48 h. A scheduled workflow in Arffornia_Playtest
(`reap.yml`, every 3 h, free on a public repo) deletes expired files and files whose PR is
closed or merged, then comments on the PR. Argo CD prunes the app. Nightly sleep
(`OffhoursSchedule`) and the homelab being off both stop environments without losing the request.

**The CLI** (`kit/playtest.mjs`, already installable with Nix or npm):

| Command | Does |
|---|---|
| `playtest up <pr…> [--slot pr2] [--ttl 24h]` | Picks the kind from the repo. Checks that CI is green on the head and that the images or jar exist. Takes a free slot (or the `slot`) and writes the env file. Waits until the URL answers (website `/` 200, server through `api.mcstatus.io`), prints the URL and the 10-minute checklist, and opens the browser or says "Beta launcher → Test slot". If the cluster is off, it says so and offers `--local`, today's local light environment. |
| `playtest status` | Slots, who holds them, expiry, health |
| `playtest extend <slot> 24h` · `playtest down <slot>` | Moves `expires` · deletes the file |
| `playtest report <pr> --verdict ok\|ko --notes …` | Exists today. It also writes the answer in the review-stack format |

The game client always runs on Brian's machine. Cluster for the server and website, local for
the client: that is D14.

**How class-C PRs get approved through it (D9).**
1. An agent rebases the stack: it merges `main` into the PR, never force-pushes.
   [#101](https://github.com/Arffornia/Arffornia_Website/pull/101) conflicts today, and a
   conflicting PR gets no `pull_request` build.
2. The agent runs the deterministic checks against the environment: website Playwright
   (`e2e/`) on the preview URL; for the pack, server boot, a log scan and the GameTests. It
   posts the result on the PR. This step is advisory.
3. The agent writes a **Playtest card** to the review stack: one row per PR, with its URL,
   checklist and OK/KO.
4. Brian follows the checklist, about 10 minutes per row, and answers OK or KO with notes.
5. On OK, an agent removes `needs-playtest` and merges in stack order (merge commits, `sha`
   pinned), then frees the slot. On KO, the notes go on the PR as a fix task.

**Batches (D10).** Testing the five launcher PRs one by one costs 50 minutes. One
**candidate build** has all five merged on top of `main`, and is tested once. If it is OK, the
five PRs merge. If it is KO, the agent bisects with the per-PR artifacts. The website stack works
the same way: the tip [#115](https://github.com/Arffornia/Arffornia_Website/pull/115) carries
#101, #110, #113 and #115.

### 10-minute checklists, per PR

Each line is something only a human can judge, or a check worth doing once by hand. Agents
check everything else beforehand.

**Session A: launcher candidate (Windows first, then Linux), beta artifact `launcher-candidate`**

| PR | Check (≈2 min each) |
|---|---|
| [#55](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/55) renderer isolation | Home, Settings, Shaders, Highlight and Notifications all load; the progress bar moves during Play; no blank page after going back and forth 3 times |
| [#58](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/58) encrypted credentials | Log in, quit, reopen: still logged in. Change the language and the RAM, restart: both kept. An old install upgraded: no forced re-login |
| [#59](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/59) Electron 45 | Play reaches the Minecraft title screen; the skin viewer renders; the window resizes and minimizes normally |
| [#64](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/64) strict CSP | Shop images, Modrinth icons, avatar and skin all show; server status shows. In Beta → Staging, the staging API works (its host must be in `connect-src`) |
| [#65](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/65) E2E suite | Nothing by hand: CI is green on the candidate. Glance at the report |

**Session B: website stack, slot `pr1` = #115 (carries #101, #110, #113, #115)**

| PR | Check |
|---|---|
| [#101](https://github.com/Arffornia/Arffornia_Website/pull/101) EN/FR | Switch EN↔FR in the header on 4 pages; the choice survives a reload; no raw `messages.*` keys; the French reads naturally |
| [#110](https://github.com/Arffornia/Arffornia_Website/pull/110) disclaimer | Footer shows "NOT AN OFFICIAL MINECRAFT PRODUCT…" in both languages, readable but not shouting |
| [#113](https://github.com/Arffornia/Arffornia_Website/pull/113) legal pages | `/legal`, `/privacy`, `/terms`: publisher TheGostsniperfr and arffornia@gmail.com are right; nothing you would not sign |
| [#115](https://github.com/Arffornia/Arffornia_Website/pull/115) FAQ | `/faq` "Can I play on a Mac?": the steps match what you expect a player to do |

**Session C: website slots `pr2`, `pr3`**

| PR | Check |
|---|---|
| [#102](https://github.com/Arffornia/Arffornia_Website/pull/102) API locale | In the beta launcher on Staging, switch to FR: shop and error messages come back in French |
| [#103](https://github.com/Arffornia/Arffornia_Website/pull/103) Laravel 13 / PHP 8.5 | Click through home, shop, stages, profile and admin; no 500; the page speed feels the same |
| [#86](https://github.com/Arffornia/Arffornia_Website/pull/86) chart hardening | The agent redeploys the slot twice; the seeded data is still there (migrations no longer wipe). Item textures and avatars load (non-root pod) |
| [#91](https://github.com/Arffornia/Arffornia_Website/pull/91) OAuth state | Needs D7. Log in with Microsoft on `pr1`: it works. Open the callback URL a second time: you get "Authentication failed" and no crash |

**Session D: test slot (beta launcher → Test slot)**

| PR | Check |
|---|---|
| [Provisioning #42](https://github.com/Arffornia/Arffornia_Provisioning/pull/42) jar removal | Join `test.arffornia.com:25566`; ComputerCraft computers still work; no FTB Auxilium or RGP; nothing in the log about the removed mods |
| [Mods #49](https://github.com/Arffornia/Arffornia_Mods/pull/49) + [Provisioning #35](https://github.com/Arffornia/Arffornia_Provisioning/pull/35) (together) | The server boots with the split config; shop, rewards and progression answer (the staging API); no secret in the client config folder |
| [infra #44](https://github.com/TheGostsniperfr/infra/pull/44) NetworkPolicies (draft) | Not a slot test: an agent applies it to `arffornia-staging` and `arffornia-slot` first. Brian checks staging still works, then the PR leaves draft |

### Phase 4 · UI round 4 into code (after phases 1–3)

The specs are in [spec 007](../007-loading-and-title-screen.md), round 4
([docs #24](https://github.com/Arffornia/docs/pull/24)), with Brian's tweaks. Order, lowest risk
and most visible first:

| # | Deliverable | Repo | Why this order | Tested through |
|---|---|---|---|---|
| 4a | **Title screen** (Honeycomb, launcher palette, extruded tiles, MOTD splash from the server-list ping, smaller per Brian, crafting-table logo left of the wordmark, spatial keyboard navigation) | Arffornia_Mods (client package) | Pure client, no FML internals, visible at every launch; light env works | `runClient` locally, then beta → Test slot with the `pr-<n>` jar |
| 4b | **Loading screen** (Night Shift kept, the crafting-table logo instead of the current one, "Did you know?" tip cards with machine close-ups as pre-rendered sprites from Arffornia_Assets) | Arffornia_Mods | Replaces the Mojang overlay only; reuses 4a's palette and font | same |
| 4c | **Early window** (`arffornia-earlywindow.jar`, SERVICE layer, assembly line at 20 fps from the 480×288 sheet, logo left of the title, last cached MOTD or tagline) + `fml.toml` | Arffornia_Mods subproject + Arffornia_Provisioning | Highest risk: reflection into FML; a crash here means no game. Stock fallback on any exception; `earlyWindowControl=false` still boots | `:earlywindow:visualTest` under Xvfb, then beta → Test slot on Windows, Linux and the macOS runner (GL 3.2 core) |
| 4d | Remove FancyMenu and Drippy and their copied art | Arffornia_Provisioning | Only after 4a–4c are OK in a release | Test slot |
| 4e | Launcher splash (L1), optional | Launcher | Needs Electron 45 (#59) first | beta |

Each step is its own PR, tested in a playtest session, and released with the next mod tag.
The machine close-ups use the old mocks until the art direction is done; the tip copy is checked
against the tier plan.

## Testing

| Phase | Automated | By hand (Brian) |
|---|---|---|
| 1 | `beta.yml` green on 3 OS; macOS launch smoke (exists); guard: `releases/latest` = stable; unit tests on the channel config | Install the beta next to the normal launcher on Windows and NixOS; Play reaches the title screen on Production |
| 2 | Argo apps healthy; staging Playwright run; slot boot + log scan; network policy test (from the slot, prod website and Vault are unreachable) | Open `staging.arffornia.com`; beta → Staging, join the slot |
| 3 | `playtest up --dry-run` unit tests; the reaper on a fake expired file; a 4th website env stays `Pending` | One session from the checklists |
| 4 | Spec 007's visual tests and harness | Spec 007's manual checklist |

## Migration

Nothing changes for players. Prod Argo apps, prod values and the prod launcher stay as they are.
The only prod-adjacent edits are new DNS names, a router port (D12) and a new image tag `main`
next to `latest`. ADR-0007 is superseded by ADR-0016 once D4–D6 are answered.

## Decisions needed (defaults in bold)

| # | Question | Options | Why the default |
|---|---|---|---|
| D1 | Where beta builds live | **Rolling `beta` pre-release in the launcher repo + per-build artifacts** / a separate `Arffornia_Launcher_Beta` repo (needs a PAT secret) / artifacts only | One click for Brian, no new secret; the guard step protects players |
| D2 | When a beta is built | **Every push to `main`** / nightly if `main` changed / by hand | Free runners on a public repo; always fresh |
| D3 | Beta on NixOS | **`appimage-run` now, a `.#beta` flake output later** / flake output now | Works today with no packaging work |
| D4 | How an environment is requested | **A file per slot in Arffornia_Playtest `envs`, TTL enforced there** / PR labels + Argo PR generator (ADR-0007) | One repo, no GitHub token in the cluster, the TTL needs no cross-repo token |
| D5 | Capacity | **3 website slots (768 MiB each) + 1 pack slot (16 GiB)** / 1 + 1 | Website envs are cheap; one full pack at a time is Brian's rule |
| D6 | TTL | **48 h, extendable, sleeps 03:00–07:00** / 24 h / until the PR closes | Evening-and-weekend batches |
| D7 | Microsoft login on staging and PR slots | **A separate free "Arffornia Test" app, redirect URIs for `staging`, `pr1`–`pr3`; secret in Vault through Terraform** / no Microsoft login off prod (#91 then waits for prod) | #91 can't be tested otherwise; prod secrets stay in prod |
| D8 | Staging data | **Seed data only (E2ESeeder)** / an anonymised copy of prod (later) | No personal data off prod (spec 012) |
| D9 | What approves a playtested PR | **Your OK on the playtest card** / a `playtest report --verdict ok` comment from your account / both | The card is where you already answer |
| D10 | Launcher and website class-C PRs | **Test as one candidate build or stack tip; bisect only on KO** / one by one | 10 minutes instead of 50 |
| D11 | Prod follows `main` (website `latest`, pack from raw `main`) | **Keep for now; pin prod to promoted versions in a follow-up chantier** / pin now | Pinning changes prod and old launchers; staging first |
| D12 | How the client reaches the test slot | **`test.arffornia.com:25566` on its own port (online mode, whitelist; one router forward)** / a Velocity forced host on the prod proxy | The prod forwarding secret never enters a namespace that runs PR code |
| D13 | UI round 4 order | **Title → loading → early window → remove FancyMenu/Drippy** / early window first | Lowest risk and most visible first |
| D14 | Where `playtest up` runs things | **Cluster for the server and website, your machine for the game client; `--local` when the cluster is off** / your machine for everything (your answer of 31 Oct) | You asked for a URL to click; local stays one flag away |
| D15 | Mac beta | **Build arm64 + x64 unsigned, CI smoke only until you have a Mac** / skip Mac | A Mac player must be able to run the game; CI is the only Mac for now |

## Work breakdown

| # | Task | Repo | Effort | Acceptance |
|---|---|---|---|---|
| 1.1 | `beta.yml`, the channel constant, beta app id and data folder, generic updater, environment picker (Production only) | Launcher | M | Beta installs side by side on Windows and Linux; prod build unchanged (tests) |
| 1.2 | `release.yml` guard: ignore `v*-*`, `GITHUB_TOKEN`, check that `releases/latest` is stable | Launcher | S | A test tag `v0.0.0-beta.0` builds no release |
| 1.3 | PR artifacts `launcher-pr-<n>` and the `launcher-candidate` job (D10) | Launcher | S | Artifacts on #55–#65 |
| 1.4 | Beta section in README + Playtest README; the NixOS copy-prompt | Launcher, Playtest | S | – |
| 2.1 | `arffornia-staging`, `arffornia-slot`, AppProject, Kyverno policies, quotas, offhours | infra | M | Apps healthy; isolation test passes |
| 2.2 | DNS `staging`, `pr1`–`pr3`, `test`; Vault roles, policies and staging secrets (Terraform, `random_password`) | infra `terraform` | S | `terraform plan` shows only additions |
| 2.3 | pack-files image | Playtest | S | The rewritten mod list is served; other paths proxied |
| 2.4 | `edge` pre-release on `main` | Mods | S | `releases/latest` unchanged |
| 2.5 | Image tag `main` | Website | S | – |
| 2.6 | Beta environments Staging and Test slot; their hosts in CSP and the IPC allow-list | Launcher | S | Beta joins the slot |
| 3.1 | PR images `pr-<n>` (website), `pr-<n>` jar (mods), deleted when the PR closes | Website, Mods | S | – |
| 3.2 | `ApplicationSet` + per-kind templates (website slot, pack slot) | infra | M | Writing `envs/pr1.yaml` brings up `pr1.arffornia.com` |
| 3.3 | `playtest up/status/extend/down`, the reaper workflow | Playtest | M | CLI tests; expired file removed |
| 3.4 | Playtest card generator (review-stack JSON) + agent pre-checks | Playtest, agent-kit skill `playtest-kit` | M | A card with sessions A–D |
| 4a–4e | UI round 4, in order | Mods, Provisioning, Launcher | L in total (M each) | Spec 007 checklists |

**Effort by phase:** 1 = **M** (about 1–2 agent days, no cluster needed) · 2 = **M** (needs the
cluster on and one `terraform apply`) · 3 = **L** (3–4 agent days) · 4 = **L** (a week or more,
after D13).

**This week, if approved on Monday:** phase 1 Monday–Tuesday. Phase 2 Tuesday–Wednesday, when
the homelab is up. Phase 3 Wednesday–Friday. The first playtest session (A, with the beta
launcher) can run before phase 3, from the PR artifacts.

## What Brian does

| Phase | Action | Time |
|---|---|---|
| all | Answer the decisions on the review-stack card | 5 min |
| 1 | Install the beta on Windows (download, SmartScreen *Run anyway*) and on NixOS (prompt P1) | 5 min |
| 2 | Turn the homelab on. Run prompt P2 (Terraform) once the infra PR is merged. Add the router forward TCP 25566 (D12). With D7: create the test Microsoft app (prompt P3). Tag Mods v1.0.26 after staging is OK (prompt P4) | 20 min |
| 3 | Install the CLI (`nix profile install github:Arffornia/Arffornia_Playtest`), then use the playtest card | 10 min per PR, less in batches |
| 4 | Playtest sessions as each screen lands | – |

### Copy-prompts for Claude Code on Brian's machine

**P1 · Run the beta on NixOS**
```text
Task from my Arffornia review stack: run the Arffornia Launcher Beta on this NixOS machine.
Download the AppImage and SHA256SUMS from the "beta" pre-release with:
gh release download beta --repo Arffornia/Arffornia_Launcher_V.5.2 --pattern '*.AppImage' --pattern SHA256SUMS --dir ~/Downloads/arffornia-beta --clobber
Check the hash with sha256sum -c --ignore-missing, then start it with
nix run nixpkgs#appimage-run -- ~/Downloads/arffornia-beta/*.AppImage
Tell me the version shown in Settings and whether Play reaches the Minecraft title screen.
Rules: never force-push, never print secrets, ask me before anything destructive. Summarise in French.
```

**P2 · Terraform for staging and slots (after the infra PR is merged)**
```text
Task from my Arffornia review stack: apply the Terraform for spec 016 (staging + test slots).
In my clone of TheGostsniperfr/infra: git pull, cd terraform, then run terraform plan with the
sops-managed backend and tfvars, as terraform/Readme.md says. Never print the backend env or the tfvars.
Show me the plan summary: it must only ADD the DNS records staging, pr1, pr2, pr3, test, and the
Vault policies, roles and secrets for arffornia-staging and arffornia-slot. Stop if it changes or
destroys anything else. Apply only after I say yes, then write "Applied on <date>" in the PR.
Rules: Vault only through Terraform, never force-push, never print secrets. Summarise in French.
```

**P3 · Test Microsoft app for login on staging and PR slots (D7)**
```text
Task from my Arffornia review stack: create a separate Microsoft app for test logins.
If the az CLI is not logged in, guide me through the Azure portal instead (App registrations → New).
Name "Arffornia Test", personal Microsoft accounts, web redirect URIs: the website's Microsoft
callback path (read it from Arffornia_Website config/app.php azure.oauth.redirect_uri usage) on
https://staging.arffornia.com, https://pr1.arffornia.com, https://pr2.arffornia.com, https://pr3.arffornia.com.
Create a client secret and put the client id and secret ONLY into the sops tfvars of
TheGostsniperfr/infra terraform as the staging values, then run prompt P2's plan again.
Rules: never print the secret, never commit it in clear, ask before applying. Summarise in French.
```

**P4 · Mod release after staging is OK**
```text
Task from my Arffornia review stack: release the Arffornia mod v1.0.26.
First check that Arffornia_Mods #49 and Arffornia_Provisioning #35 are merged (the agents merge them in one window)
and that main is green: gh pr view 49 --repo Arffornia/Arffornia_Mods; gh pr view 35 --repo Arffornia/Arffornia_Provisioning.
Then in my clone of Arffornia/Arffornia_Mods: git pull, git tag -a v1.0.26 -m "v1.0.26", git push origin v1.0.26.
Watch the build workflow and give me the release URL.
Rules: never force-push, never print secrets, ask me before anything destructive. Summarise in French.
```

## Risks

| Risk | Phase | Mitigation |
|---|---|---|
| A beta reaches players through `releases/latest` | 1 | Pre-release only, a rolling non-semver tag, `release.yml` ignores `v*-*`, guard step after each publish, distinct app id |
| The beta overwrites Brian's normal game folder | 1 | Data in `.Arffornia_beta/<env>`; Windows and Linux paths are relative to the working directory today, so the beta sets an absolute path |
| Two builder configs (`package.json` `build` and `electron-builder.yml`) disagree | 1 | 1.1 checks which one electron-builder uses and removes the stale one in its own PR |
| Mac: unsigned, no auto-update, no hand test; the Java path fix is not released | 1 | CI smoke on arm64; Nexus_Java #9 → release → bump listed as the blocker |
| A PR environment touches prod data or secrets | 2–3 | Separate namespaces, no `VaultSecret` in PR namespaces, egress to prod namespaces and Vault denied, slot API = staging, own port instead of the prod proxy secret (D12) |
| Resources: a full pack per PR would exhaust the homelab | 3 | One pack slot; quota makes an extra env `Pending`; TTL; nightly sleep |
| Homelab off when Brian wants to test | 2–3 | The CLI says so and offers `--local`; launcher sessions need no cluster |
| `*.arffornia.com` routes from new namespaces need the gateway label | 2 | Label set by infra on the fixed namespaces only |
| Conflicting PRs get no merge-ref build (#101 today) | 3 | Agents merge `main` in first; the card shows "not buildable" instead of a dead link |
| Prod keeps following `main` | – | Out of scope; D11 |
| Phase 4 early window crashes the client on some GPUs | 4 | Stock fallback on any exception, `earlyWindowControl=false`, tested on 3 OS before release |

## Sources

- Launcher: `.github/workflows/release.yml`, `package.json` `build`, `src/main/index.js` (updater), `src/main/launcherSettings.js`, `src/main/dataDir.js`.
- Infra: `k8s/config/arffornia/{website,server}`, `k8s/config/gateway-infra`, `terraform/dns.tf`.
- Provisioning: `src/configUpdater.ts` (`BASE_URL`), `config/*/modList.json` (`Arffornia_Mods` tag `latest`).
- Playtest kit: [kit spec](https://github.com/Arffornia/Arffornia_Playtest/blob/main/docs/kit-spec.md); tech watch card 02 (agent playtesting).
- electron-updater channels and providers: <https://www.electron.build/docs/features/auto-update>.

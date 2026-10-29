# Development setup

Every repo builds on **Linux x86_64, Linux arm64 and macOS on Apple Silicon** with the same
commands (`make check`, `make test`, `make build`; see each repo's `AGENTS.md`).

## What each repo needs

| Repo | Tools | Nix shell |
|---|---|---|
| Launcher, Nexus_Java/Logger/Saver/Mods, Provisioning, keycloak theme | Node.js 22 | `node` |
| Arffornia_Mods, Arffornia_Proxy | JDK 21 (Gradle comes from `./gradlew`) | `java` |
| Arffornia_Website | PHP 8.3 + Composer, Node.js 22, Docker for the full stack | `php` |
| docs (this site) | Python 3.13 (`pip install -r requirements.txt`), Go (Noodle), draw.io desktop | `docs` |
| infra | kubectl, kustomize, helm, kubeconform | `infra` |

## Option A: Nix (Linux, NixOS, macOS)

The docs repo has a `flake.nix` with one shell per row above, for `x86_64-linux`, `aarch64-linux`
and `aarch64-darwin`. From any clone:

```bash
nix develop github:Arffornia/docs#node      # or #java, #php, #docs, #infra, #default (all)
```

With [direnv](https://direnv.net/), put `use flake github:Arffornia/docs#node` in a local `.envrc`.
The flake pins nixpkgs `nixos-26.05`; `nix flake update` in the docs repo bumps it.

On **NixOS**, the Electron binary that npm downloads and Playwright's browsers are not NixOS
binaries: run the launcher inside its `electron_env.nix` (`nix-shell electron_env.nix`).

## Option B: Homebrew (macOS)

```bash
brew install node@22 openjdk@21 php@8.3 composer python@3.13 go \
  kubectl kustomize helm kubeconform shellcheck actionlint
brew install --cask drawio            # for `make diagrams` in the docs repo
brew install --cask orbstack          # or Docker Desktop, for the website's docker compose
```

Follow the `brew info` hints to put `node@22`, `openjdk@21` and `php@8.3` on your `PATH`.
Noodle: `go install github.com/TheGostsniperfr/Noodle/cmd/noodle@main`.

## Develop on macOS

Apple Silicon is a first-class platform: nothing runs under Rosetta.

- **Shell scripts and Makefiles.** macOS ships bash 3.2 and BSD `sed`, `grep`, `date`. Write
  scripts for that: `#!/usr/bin/env bash`, no associative arrays, `mapfile` or `${x,,}`; no
  `sed -i` without a suffix (`sed -i.bak … && rm *.bak` works on both), no `grep -P`,
  `readlink -f`, `realpath -m`, `date -d`, `xargs -r` or `stat -c`. Run `shellcheck` on them.
- **Launcher.** `npm ci && npm run dev` runs natively. `npm run build:mac` packages ad-hoc signed
  arm64 and x64 apps. On macOS the launcher keeps the game, Java and settings in
  `~/Library/Application Support/Arffornia/` and downloads an `aarch64` Azul JRE. The released app is
  not notarized: allow it once in System Settings → Privacy & Security → "Open Anyway".
- **Mod.** `make run-client` works natively (arm64 LWJGL natives; ModDevGradle adds
  `-XstartOnFirstThread` on macOS). Gradle finds JDK 21 on your machine or downloads one through
  the foojay toolchain resolver.
- **Website.** The images in `docker-compose-dev.yaml` (php, node, nginx, postgres) are
  multi-arch, so the stack runs natively. A local Postgres on port 5432 conflicts with the `db`
  service: stop it first. The published `ghcr.io/arffornia/*` images are amd64 only; OrbStack and
  Docker Desktop run them through Rosetta.
- **Docs.** `make diagrams` finds draw.io in `/Applications` (no `xvfb-run` needed on a Mac).
- **Playwright** (website and launcher E2E): `npx playwright install chromium`
  (`--with-deps` is only needed on Linux).
- **Case-insensitive file system.** APFS ignores case by default: two files whose names differ
  only by case collide. Keep names unique ignoring case.

CI checks this: the launcher and the Nexus libraries run a `check-macos` job on `macos-latest`
(Apple Silicon), and the launcher job also packages the app and starts it. The mod and proxy builds
are plain JVM builds and run on Linux only.

# Standards

Short on purpose. If a rule is missing, follow what the code around you does and say so in the PR.

## Every repo has

| File | Purpose |
|---|---|
| `README.md` | what it is, where it fits, quickstart, configuration, release |
| `AGENTS.md` (+ `CLAUDE.md` → `@AGENTS.md`) | map, commands, rules, gotchas, for agents and newcomers |
| `Makefile` | `make check` = lint + typecheck + tests + build; `test`, `build`, `lint` |
| `.github/workflows/ci.yml` | `make check` on every PR and on `main` |
| `.github/dependabot.yml` | weekly, grouped updates |
| `.editorconfig` | consistent whitespace |

Community files (CONTRIBUTING, SECURITY, code of conduct, issue and PR templates) come from
the org-wide `Arffornia/.github` repo unless a repo needs its own.

## Code

- **Language**: English everywhere; player text through i18n in EN and FR.
- **Errors**: never swallow a failure that changes what players or servers get. Fail loudly,
  exit non-zero, log the reason.
- **Network**: every HTTP call has a timeout; retries are bounded with backoff.
- **Downloads**: write to a temp file, verify the published hash, then rename.
- **Paths**: never join an untrusted name onto a directory without confining it.
- **Secrets**: placeholders in git, values from Vault at deploy time; nothing sensitive in logs.

## Tests

| Stack | Unit | End to end |
|---|---|---|
| Laravel website | PHPUnit / Pest, sqlite in memory | Playwright on critical journeys |
| Electron launcher | Vitest (main + stores) | Playwright for Electron, mocked APIs, under xvfb |
| NeoForge mod | JUnit (+ junit-fml) | GameTests via `runGameTestServer`; nightly client check with screenshots |
| Velocity plugin | JUnit with a stub HTTP server | manual smoke with `run-velocity` |
| TypeScript libs | Jest/Vitest, offline (mocked HTTP) | live tests nightly only |
| Infra | `kustomize build` + `kubeconform` + `helm lint` | preview environments ([planned](../architecture/previews.md)) |

PR CI is offline-safe. Tests that need the internet run nightly.

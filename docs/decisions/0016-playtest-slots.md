---
status: accepted
date: 2026-11-01
supersedes: "0007"
---

# 0016 · Test PRs on fixed, capped slots requested by a file

## Context
[ADR-0007](0007-preview-environments.md) proposed a server per PR, created by an Argo CD
pull-request generator from a `preview` label. [Spec 016](../specs/016-testable-build/spec.md)
needed something Brian can use this week, on a homelab that sleeps at night and runs one full
pack at a time. Brian answered D4–D6 on the review stack (2026-11-01) with the defaults: one
file per slot in Arffornia_Playtest, 3 website slots and 1 pack slot, and 48 h extendable.

## Decision
A PR is tested on one of four **fixed slots**, requested by **one file per slot** on the `envs`
branch of [Arffornia_Playtest](https://github.com/Arffornia/Arffornia_Playtest), and deployed by
two Argo CD ApplicationSets in TheGostsniperfr/infra.

| Slot | Address | Runs | Cap |
|---|---|---|---|
| `pr1`–`pr3` | `pr<k>.arffornia.com` | One Website PR: its own chart at the PR head, its `pr-<n>-<sha7>` images, and a seeded Postgres | 0.5 CPU / 768 MiB reserved |
| `slot` | `test.arffornia.com:25566` | The pack: a Provisioning ref and an Arffornia mod tag (`edge` or `pr-<n>`). With no file it runs `main`, and it is the staging server | 4 CPU / 16 GiB |

- **Requests.** The `playtest` CLI writes the files (`up`, `extend`, `down`). Writes are normal
  commits on `envs`, checked against the blob SHA read before; there is never a force-push. The
  CLI uses the contents API, or plain git with fast-forward-only pushes where REST writes are
  refused. `--via-pr` opens a PR into `envs` instead. The CLI and the reaper validate every
  file against one contract (`kit/lib/slots.mjs`).
- **TTL.** 48 h by default, extendable, 7 days at most. A scheduled workflow every 3 h deletes
  files that expired, whose PR closed, or that are invalid. Slots sleep 03:00–07:00 like prod.
- **Isolation.**
  - The `playtest` AppProject allows only the four slot namespaces and an allow-list of
    namespaced kinds. It allows no cluster-scoped object and no VaultSecret, NetworkPolicy,
    quota, RBAC, Argo or Kyverno object.
  - Each slot has its own namespace and ResourceQuota, which is the hard cap.
  - Kyverno generates default-deny NetworkPolicies and a LimitRange. It also pins, per
    namespace, the images, the hostname, the Vault role and paths, and the Service types.
- **No prod data or secret.** Staging and the slots use seed data (`E2ESeeder`) and their own
  Vault paths, written by Terraform. The test server reaches the website API and the database
  of staging only.
- **The pack trick.** A small nginx, pack-files, serves the Provisioning ref with the mod
  retagged. A per-namespace profile rewrites the prod-only config lines (API URL, database host,
  LuckPerms storage, forwarding) and recomputes their hashes. Nexus_Mods and the config-updater
  don't change.

## Consequences
- Brian opens a URL, or the beta launcher's Test slot. An agent can prepare a slot before he
  opens the playtest card.
- Fixed hostnames need no new certificate, and a test Microsoft app registers its redirect
  URIs once.
- Only one pack PR, or one pack PR pair, can be tested at a time, and a 4th website PR waits for
  a free slot. Both are deliberate.
- Deviations from the spec's sketch, with their reasons:
  - one namespace per website slot instead of a shared `arffornia-previews`: an exact quota per
    slot, no name clashes between PR charts, and isolation between slots;
  - Postgres on a 1 GiB Longhorn volume instead of emptyDir, so the night's sleep keeps the seed;
  - website slots get their APP_KEY and DB password from a throwaway Vault path through an
    infra-owned VaultSecret, because no literal secret may be committed.
- Prod still follows `main`; pinning it is D11, a follow-up chantier.

## Alternatives considered
- One environment per PR (ADR-0007): unbounded, needs a wildcard certificate per PR and a GitHub
  token in the cluster, and a full pack per PR exceeds the homelab.
- PR labels and the Argo pull-request generator: needs a token, and the TTL then lives in two
  places.
- Brian's machine for everything (his 31 Oct answer): kept as `playtest up --local`, for when
  the cluster is off.

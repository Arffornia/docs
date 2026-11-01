---
status: superseded   # by 0016 (fixed playtest slots), 2026-11-01
date: 2026-10-29
---

# 0007 · Per-PR preview environments on the cluster

## Context
Features should arrive at the maintainer already tested in game. Several features are
developed in parallel, each needing its own Minecraft server.

## Decision (proposed)
- A PR labelled `preview` publishes an immutable **preview bundle** (built jars, regenerated
  index) and an Argo CD `ApplicationSet` (pull-request generator) deploys
  `arffornia-pr-<repo>-<n>` from a small local Helm chart wrapping the existing server base.
- Guardrails first: per-namespace secret isolation, a dedicated `AppProject` that denies
  `VaultSecret`, cluster-scoped objects and `LoadBalancer` services, a quota, a default-deny
  `NetworkPolicy`, an in-namespace Postgres, and a maximum lifetime.
- A test `Job` runs GameTests and scripted RCON checks and posts results on the PR; agents
  never need cluster credentials.

## Consequences
- Prerequisites: secret isolation, `url` sources and overrides in Nexus_Mods, cluster
  capacity (a full pack needs 8–16 GiB per server).
- See [Preview environments](../architecture/previews.md).

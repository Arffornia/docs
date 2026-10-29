# Preview environments (planned)

![Preview environments, proposed](../assets/diagrams/previews.light.png#only-light)
![Preview environments, proposed](../assets/diagrams/previews.dark.png#only-dark)

Status: **proposed** in [ADR-0007](../decisions/0007-preview-environments.md), milestone M3.

1. A pull request labelled `preview` builds a **preview bundle** (jars + regenerated index) and
   stores it at an immutable location.
2. An Argo CD **ApplicationSet** with a pull-request generator creates `arffornia-pr-<repo>-<n>`
   from a small Helm chart that wraps the current server base, pointing the config-updater at
   the bundle.
3. Guardrails: a dedicated AppProject (no VaultSecret, no cluster-scoped objects, no
   LoadBalancer), a quota, default-deny network policies, an in-namespace Postgres, a lifetime cap.
4. A test Job waits for the server, runs GameTests and scripted RCON commands, scans logs and
   posts the results on the PR. Testers reach the server through `mc-router` by hostname.
5. Closing the PR deletes the namespace.

Prerequisites: per-namespace secret isolation, `url` sources and overrides in Nexus_Mods,
enough cluster memory (a full pack needs 8–16 GiB per server).

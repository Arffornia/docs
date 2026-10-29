# Infrastructure

**Repo:** [TheGostsniperfr/infra](https://github.com/TheGostsniperfr/infra) (the maintainer's
homelab; Arffornia lives under `k8s/config/arffornia` and `k8s/apps/arffornia`).

| Piece | Choice |
|---|---|
| GitOps | Argo CD app-of-apps, auto-sync with prune and self-heal on `HEAD` |
| Packaging | Kustomize overlays with Helm charts (itzg `minecraft`, forked `minecraft-proxy`) |
| Game server | `itzg/minecraft-server`, NeoForge 1.21.1, overlay **arcane** (live) and **nexus** (disabled) |
| Proxy | Velocity on a MetalLB LoadBalancer; NuVotifier port for votes |
| Website | nginx + php-fpm behind Envoy Gateway (`arffornia.com` is DNS-only; `map`, `vault`, `argocd` go through Cloudflare) |
| Map | BlueMap web (`map.arffornia.com`) reading the arcane live server |
| Data | Zalando Postgres (WAL-G to in-cluster S3), Longhorn volumes, SMB NAS for world backups |
| Secrets | Vault + vault-secrets-operator (`VaultSecret` CRs), values provisioned with Terraform |
| Observability | kube-prometheus-stack, ServiceMonitor on the server, Alertmanager → Discord |
| Cost | off-hours guard sleeps servers at night |

## Render and check the manifests

```bash
kustomize build --enable-helm --load-restrictor=LoadRestrictionsNone \
  k8s/config/arffornia/server/overlays/arcane > arcane.yaml
noodle discover k8s arcane.yaml -o architecture/arffornia/discovered/k8s-arcane.yaml
```

## Known gaps (October 2026 audit)

Website debug mode in production, no per-namespace secret isolation, no NetworkPolicies,
unpinned images, on-site-only backups, no PR validation of manifests. Tracked as issues.

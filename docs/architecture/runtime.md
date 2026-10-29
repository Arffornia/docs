# Runtime

![Runtime topology](../assets/diagrams/runtime.light.png#only-light)
![Runtime topology](../assets/diagrams/runtime.dark.png#only-dark)

| Entry | Path |
|---|---|
| Players | router → MetalLB → **Velocity proxy** (modern forwarding) → **arcane** server |
| Browsers | `arffornia.com` is DNS-only: router → **Envoy Gateway** → website (nginx + php-fpm). `map.arffornia.com` goes through Cloudflare → Envoy → BlueMap web, which reads tiles from the NAS and proxies the arcane live map |
| Vote sites | MetalLB → NuVotifier on the proxy → Arffornia plugin → website API |

Background work: Argo CD syncs manifests, vault-secrets-operator turns Vault paths into Secrets,
a backup sidecar archives the world to the NAS every day, Prometheus scrapes the server and
Alertmanager notifies Discord, the off-hours guard sleeps servers at night.

Gaps found in the code are marked `Gx` on the diagram: the website is not behind Cloudflare,
the game server writes the website database directly, server and proxy reach the API through
the public hostname (a hairpin through the router), one Vault role for every namespace, no
network policies yet, a committed credential. Each one is tracked as an issue.

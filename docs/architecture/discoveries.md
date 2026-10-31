# Discoveries log

Small oddities that agents find on the way. Each one gets a ticket, so nothing gets lost, and
Brian can skim the list instead of reading reports. Add a row when you find something, and
update **Status** when the ticket closes. Security issues that are not fixed yet use neutral
wording here, as in public issues.

| Date | Area | Found | Why it matters | Ticket | Status |
|---|---|---|---|---|---|
| 2026-10-31 | Keycloak theme | Login copy said "3-Istor Cloud Platform", the theme was named `keycloak-theme-kube-lab`, and the favicon was the Vite logo | Branding copied from another project | [theme#18](https://github.com/Arffornia/keycloak-theme-arffornia/issues/18) → [theme#29](https://github.com/Arffornia/keycloak-theme-arffornia/pull/29), [infra#57](https://github.com/TheGostsniperfr/infra/pull/57) | PR open |
| 2026-10-31 | Keycloak realm | WebAuthn policy still `Example` / `keycloak.example.com` | Passkeys cannot work until it is fixed | [infra#60](https://github.com/TheGostsniperfr/infra/issues/60) | open |
| 2026-10-31 | Keycloak realm | Kerberos (SPNEGO) step in the browser flow, with no Kerberos server | Dead step, confusing flow | [infra#60](https://github.com/TheGostsniperfr/infra/issues/60) | open |
| 2026-10-31 | Keycloak realm | Forced password change every 365 days | Against current NIST guidance; passkeys make it moot | [infra#60](https://github.com/TheGostsniperfr/infra/issues/60) | needs decision |
| 2026-10-31 | Keycloak deploy | `KC_PROXY` (removed in 26), `KEYCLOAK_ADMIN` (deprecated), no `--optimized` start | Slow boot on an on-demand cluster, options silently ignored | [infra#61](https://github.com/TheGostsniperfr/infra/issues/61) | open |
| 2026-10-31 | Keycloak theme | The image copies both theme JARs (KC 22–25 and KC 26+) into `/providers` | Duplicate theme names in one Keycloak | [theme#31](https://github.com/Arffornia/keycloak-theme-arffornia/issues/31) | open |
| 2026-10-31 | Proxy | The proxy Service uses the default `externalTrafficPolicy: Cluster` | Velocity may see node IPs instead of player IPs (bans, throttling, MOTD language) | [infra#62](https://github.com/TheGostsniperfr/infra/issues/62) | to check |
| 2026-10-31 | Infra | Terraform state on AWS S3 + DynamoDB | A paid service under the no-paid rule (probably cents) | [infra#63](https://github.com/TheGostsniperfr/infra/issues/63) | needs decision |
| 2026-10-31 | Launcher | `build.files` packs electron-builder's `dist/` into `app.asar`: every installer carries a second Electron (asar 333 MB → 34 MB) | Installers and updates about twice as big | [launcher#77](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/77) → [launcher#78](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/78) | PR open |
| 2026-10-31 | Launcher | MCLC never awaits its library hash check, re-hashes ~4,000 assets per launch, and downloads over 2 sockets | Corrupt libraries never repaired; slow Play | [launcher#79](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/79) | open |
| 2026-10-31 | Launcher | NixOS users need "open with AppImage runner"; no menu entry | Brian's own desktop | [launcher#75](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/75) → [launcher#76](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/76) | PR open |
| 2026-10-31 | Proxy | The server-list MOTD was a fixed "Arffornia Network!" | No seasonal or fun lines; no way to edit it in git | [proxy#15](https://github.com/Arffornia/Arffornia_Proxy/issues/15) → [proxy#16](https://github.com/Arffornia/Arffornia_Proxy/pull/16), [provisioning#39](https://github.com/Arffornia/Arffornia_Provisioning/pull/39) | PR open |
| 2026-10-31 | Proxy plugin | The plugin disables itself entirely when the vote config is missing | Any future feature (the MOTD) would vanish with it; the MOTD now registers first | [proxy#16](https://github.com/Arffornia/Arffornia_Proxy/pull/16) | PR open |
| 2026-10-31 | Mod / website | Shop rewards are only noticed at join or through `/arffornia shop claim_reward`; there is no push | Purchases feel delayed | [ADR 0012](../decisions/0012-keep-laravel-add-outbox-events.md) | proposal |

Older findings live in the audits and in each repo's issues. This log starts with the wave 4
research (2026-10-31).

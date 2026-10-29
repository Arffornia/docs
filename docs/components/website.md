# Website

**Repo:** [Arffornia_Website](https://github.com/Arffornia/Arffornia_Website) ·
**Stack:** Laravel 12, PHP, Vite, Postgres, Sanctum

The public site (home, news, rules, profiles, shop, votes, progression graph) **and the central
API**: the source of truth for players, progression, teams, shop and votes. It runs as one pod
with php-fpm and nginx, deployed by the `charts/arffornia-website` Helm chart through Argo CD.

## Authentication

| Who | How |
|---|---|
| Players (browser) | Microsoft → Xbox Live → Minecraft profile, via the `arffornia/minecraft-oauth` package; Laravel session |
| Browser JavaScript | `POST /api/auth/token/session` → Sanctum token |
| Game services (mod, proxy) | `POST /api/auth/token/svc` with `client_id`/`client_secret` → Sanctum token |

Authorization uses roles: `user`, `admin`, `progression_editor`, `user_editor`, `team_editor`,
`nuvotifier_service`. The mod's service account has the three editor roles; the proxy's has
`nuvotifier_service`.

## API consumers

| Caller | Endpoints |
|---|---|
| Launcher | public reads: profiles, vote and point rankings, shop lists, launcher images |
| Mod (server and clients) | public reads: profile by UUID, progression, stages, milestones, recipes; service writes: progression, teams, players, unlock capture, migration |
| Proxy plugin | `POST /api/vote/nuvotifier` |
| Site JavaScript | shop item, stages editor (admin) |

The mod also reads the `pending_rewards` table **directly in Postgres** to deliver shop and vote
rewards, so that table's schema is a contract between the two repos (an API is proposed).

## Develop

```bash
composer install && npm ci
cp .env.example .env && php artisan key:generate
php artisan migrate --seed
npm run dev & php artisan serve
make check
```

`keycloak-theme-arffornia` is unrelated to player login: it is the login theme of the infra
Keycloak realm (Argo CD, Vault…).

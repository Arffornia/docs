---
status: Draft: needs decisions
date: 2026-10-31
---

# 013 · Arffornia ID: identity, passkeys and the login experience

## Summary

Arffornia has **two identity planes**, and this spec keeps them separate:

| Plane | Who | Today | Proposed |
|---|---|---|---|
| **Players** | everyone who plays | Website login with Microsoft → Xbox Live → Minecraft profile (`arffornia/minecraft-oauth`), Laravel session | Same, plus **passkeys** for returning players and an account page that shows the linked Minecraft profile |
| **Staff / infra** | Brian, future admins | Keycloak 26.5 realm `arffornia` ("Arffornia ID") for Argo CD, Vault, Longhorn, Adminer; password + mandatory TOTP | Keycloak kept for now, with **passkeys first**, Google / Microsoft sign-in for staff, a bilingual animated theme, and an optimized start. A replacement spike (Pocket ID or Kanidm) runs before any migration |

Why not one identity provider for both? Only a Microsoft login can prove that someone owns
Minecraft. Every IdP would have to run the Xbox Live → XSTS → Minecraft profile chain in a
custom extension. The website already does it and players never see a second login page.
A shared IdP would add a hop and a failure point for no visible gain. See
[ADR 0011](../decisions/0011-two-identity-planes.md).

## Goals / non-goals

**Goals**

- A login page that looks like Arffornia: crafting-table identity, EN/FR, light and dark,
  with motion, and good accessibility (reduced motion, contrast, keyboard).
- Passkeys (WebAuthn, discoverable credentials) as the main staff login. Players can use them as a
  shortcut once their Microsoft account is linked.
- Google and Microsoft sign-in for staff, with account linking by verified email and no
  silent auto-merge.
- Clear recommended flows (below) that are versioned in Terraform.
- Light operations: start from an optimized build, pin versions, measure RAM and boot time.

**Non-goals**

- Moving player login into Keycloak.
- Paid services. Everything here is open source and self-hosted (rule: no paid solutions,
  see [Standards](../contributing/standards.md)).

## Facts (checked 2026-10-31)

- Keycloak **26.4** (2025-09) made passkeys a supported feature. Conditional UI (autofill) and the
  modal flow work in the default browser flow. A new *Conditional – credential* step skips
  2FA when a passkey was used. It is **off by default** and turned on in the *WebAuthn
  Passwordless Policy* ([keycloak.org, 2025-09-16](https://www.keycloak.org/2025/09/passkeys-support-26-4)).
  The cluster runs 26.5.5.
- The realm's WebAuthn policy still has the placeholders `Example` / `keycloak.example.com`,
  and the browser flow has a Kerberos step with no Kerberos server
  ([infra#60](https://github.com/TheGostsniperfr/infra/issues/60)).
- Keycloak starts with `kc.sh start` without `--optimized`, so it rebuilds on every boot. It
  also still uses the removed `KC_PROXY` and the deprecated `KEYCLOAK_ADMIN`
  ([infra#61](https://github.com/TheGostsniperfr/infra/issues/61)). Requests are 512 MiB, the limit 1 GiB.
- The theme is Keycloakify 11 + shadcn. The rename and the Arffornia copy are in
  [keycloak-theme-arffornia#29](https://github.com/Arffornia/keycloak-theme-arffornia/pull/29).

## Player experience (players plane, website)

1. **First visit:** "Sign in with Microsoft". The website checks Minecraft ownership and shows
   "Linked to Minecraft: *Notch* (UUID …)" with the skin head on the account page.
2. After that first login, the website offers **"Add a passkey for one-tap sign-in"**
   (WebAuthn via the free `spatie/laravel-passkeys`, or `laragear/webauthn`). From then on,
   "Sign in with a passkey" logs the player in without the Microsoft redirect.
3. **Ownership stays fresh:** the website re-checks the Minecraft profile with the Microsoft
   refresh token at most once a week, or on the next Microsoft login. A passkey never
   *creates* an account; only Microsoft does.
4. **The launcher is unchanged:** it needs a Microsoft token to start the game anyway.

## Staff experience (Arffornia ID, Keycloak)

### Recommended authentication flows (Terraform)

| Flow | Steps | Notes |
|---|---|---|
| **Browser (default)** | cookie → identity-provider redirector → *username + passkey* form (conditional UI) → if the password path was used: OTP **or** passkey as second factor | Uses the built-in 26.4+ passkey steps; replaces `Browser-Arffornia-Login-v4`'s mandatory OTP |
| **First broker login** (Google / Microsoft) | *Detect existing user* by verified email → *Confirm link* screen → *Verify existing account by re-authentication* (passkey or password+OTP) | Never auto-link on email alone; Google emails are verified, Microsoft personal emails are checked |
| **Registration** | Off (invite-only). Admins create users in Terraform; required actions: *Register passkey* (`webauthn-register-passwordless`), *Update profile* | `registration_allowed = false` stays |
| **Reset credentials** | Email link → *Register a new passkey* or set password + OTP | Needs SMTP: use the free tier of an existing mail provider, or skip reset and let an admin re-issue |
| **Step-up** | Vault and Argo CD admin roles need a passkey login within 15 minutes (`acr` level 2, *Conditional – level of authentication*) | Keeps day-to-day SSO convenient |
| **Role gate** | Keep the existing "deny if no `openid_client_access`" sub-flow | Already in Terraform |

Identity providers: **Google** (OIDC, free Google Cloud OAuth client) and **Microsoft**
(Entra ID app *personal + work accounts*, free; it can reuse Brian's existing app
registration with a new redirect URI). There is no GitHub provider unless asked.

Session policy: SSO idle 10 h / max 24 h (unchanged), remember-me on, brute-force
detection on (unchanged).

### The login page ("impress me")

The design follows the Arffornia language already used by the launcher, website and docs:
the crafting table, a deep-orange and amber accent, and a dark default.

1. **Scene:** a slow isometric "crafting grid" background. 3×3 tiles light up in sequence, as
   if a recipe were being placed, and a soft glow sits behind the card. It is pure CSS/SVG,
   under 30 KB, GPU transforms only, and paused with `prefers-reduced-motion`.
2. **Card:** glass panel, crafting-table logo. On success the logo "crafts": the 9 slots fill,
   then a short pop before the redirect (300 ms, skippable).
3. **Passkey first:** a single field with autocomplete `username webauthn` (conditional UI).
   The primary button is "Sign in with a passkey". Password and the identity providers sit
   below a divider.
4. **Language:** an EN/FR switch in the corner, remembered by Keycloak's locale cookie.
   Every string goes through `i18n.ts`. FR uses French typography (space before `?` `!` `:`).
5. **States designed:** errors shake the card once, with a message in plain words.
   *Passkey not found on this device* offers "use another device (QR)". Loading states use
   skeletons, not spinners.
6. **Same look for every Keycloak page:** OTP, required actions, the "link your account"
   confirmation, info and error pages, plus the email templates (the `email` theme type in
   Keycloakify).
7. **Proof:** Storybook stories for each page in EN and FR, light and dark, and Playwright
   screenshots in CI ([theme#22](https://github.com/Arffornia/keycloak-theme-arffornia/issues/22)).
   Brian reviews a recorded GIF before it ships.

Three visual directions should be mocked before building, as with the
[loading-screen spec](index.md): **A** crafting grid (above), **B** hexagon mosaic (Brian
liked an old title-screen mod with hex tiles), **C** a quiet minimal card with a
3D-rendered crafting table from the shared 3D-assets repo.

### Operations

- Build a custom image `ghcr.io/arffornia/keycloak` with `kc.sh build` (theme JAR, `db=postgres`,
  health, metrics), and run `start --optimized`. Measure boot time and RSS before and after.
- Set the heap explicitly (`JAVA_OPTS_KC_HEAP="-XX:MaxRAMPercentage=70"`) under the 1 GiB limit.
- Pin the theme image by version, not `latest` ([theme#20](https://github.com/Arffornia/keycloak-theme-arffornia/issues/20)).
- Back up the realm via Terraform (config) and Postgres WAL-G (users, credentials). Both exist.

## Is replacing Keycloak worth it?

The realm serves **two staff users and four admin apps**. Keycloak is the most complete
option but also the heaviest. Lighter options (checked 2026-10-31, sources linked):

| Option | Language | Footprint (project docs, idle) | Passkeys | Google / MS sign-in | Fit for Arffornia staff SSO | Migration effort |
|---|---|---|---|---|---|---|
| **Keycloak 26.5** (today) | Java | ~0.5–1 GiB; boot 20–60 s without `--optimized` | Yes (26.4+) | Yes | Complete, Terraform provider, already themed | None |
| **Pocket ID** v2 | Go | tens of MB, single binary + SQLite | Passkey-only by design | No upstream IdPs | Very good for 1–5 admins; no password at all | S: 4 OIDC clients, groups claim |
| **Kanidm** | Rust | tens of MB | Yes, passkey-first | No upstream social login | Very good; also LDAP/RADIUS/SSH; opinionated | M: CLI-driven, no Terraform provider in tree |
| **Authelia** 4.39 | Go | ~30 MB | Yes (4.39) | No upstream IdPs | Good as forward-auth + OIDC (OpenID Certified) | M: YAML config, file or LDAP users |
| **Rauthy** 0.37 | Rust | ~35–65 MB ([README](https://github.com/sebadob/rauthy)) | Yes | Yes (upstream providers) | Good; per-client themes; audited (Radically Open Security) | M |
| **Zitadel** | Go | ~150–300 MB + Postgres | Yes | Yes | Full CIAM, multi-tenant, AGPL; heavy for 2 users | L |
| **Authentik** 2025.10+ | Python/Go | ~0.5–1 GiB (Redis removed, [2025-11](https://goauthentik.io/blog/2025-11-13-we-removed-redis/)) | Yes | Yes | Complete, flow designer; not lighter than Keycloak | L |
| **Ory Kratos + Hydra** | Go | small | Yes | Yes | Headless: you build every UI page; two services | L |
| **Logto** / **Casdoor** | TS / Go | ~200 MB / ~100 MB | Yes | Yes | CIAM-oriented; more product than needed | M–L |

Footprints are orders of magnitude from each project's documentation and community reports.
They were not measured here; the spike below measures them.

**Verdict.**

- **Not justified now.** Keycloak costs about 1 GiB on a 50 GiB homelab, and it is the only
  option that already covers passkeys, social login, step-up and Terraform for every app.
  The visible pain is **boot time**, which the optimized image fixes.
- **Justified later** if staff SSO stays tiny and Brian wants zero passwords. Then **Pocket ID**
  is the lightest drop-in: it is OIDC-only and supports Argo CD, Vault and oauth2-proxy.
  Its trade-off is no Google/Microsoft upstream, which a passkey-only setup does not need.
  **Rauthy** is the light option that keeps upstream providers.
- **Spike before deciding:** run Pocket ID next to Keycloak for one app (Adminer via
  oauth2-proxy) for two weeks, and measure RAM, boot time and friction (effort S).

## Testing

- Theme: Storybook + Playwright screenshots (EN/FR × light/dark) on every PR, and a
  `keycloakify start-keycloak` smoke test that logs in with a virtual authenticator (Chrome
  DevTools WebAuthn) to cover the passkey path.
- Flows: `terraform plan` in CI on the infra repo. An end-to-end login of the test realm
  through Playwright with a virtual authenticator.
- Website passkeys: a Laravel feature test with a WebAuthn fixture, plus Playwright with a
  virtual authenticator.

## Decisions needed

| # | Decision | Options | Default |
|---|---|---|---|
| D1 | Identity planes | two planes (players on the website, staff on the IdP) / one IdP for everything | **Two planes** (ADR 0011) |
| D2 | Staff IdP | keep Keycloak + optimize / spike Pocket ID / spike Rauthy | **Keep Keycloak + optimize, Pocket ID spike** |
| D3 | Staff second factor | passkey only / passkey or OTP / OTP mandatory (today) | **Passkey, OTP as fallback** |
| D4 | Staff social login | Google + Microsoft / Microsoft only / none | **Google + Microsoft, with linking confirmation** |
| D5 | Player passkeys on the website | yes, after the first Microsoft login / no | **Yes** |
| D6 | Theme direction | A crafting grid / B hex mosaic / C minimal + 3D | **Mock all three, Brian picks** |
| D7 | Password reset by email | set up free SMTP / admin re-issue only | **Admin re-issue** (2 users) |

## Work breakdown

| Task | Repo | Effort | Ready |
|---|---|---|---|
| Rename theme and branding | keycloak-theme | S | done: [#29](https://github.com/Arffornia/keycloak-theme-arffornia/pull/29) + [infra#57](https://github.com/TheGostsniperfr/infra/pull/57) |
| Realm leftovers (WebAuthn RP, Kerberos, password expiry) | infra | S | [infra#60](https://github.com/TheGostsniperfr/infra/issues/60) |
| Optimized Keycloak image + current options | infra | M | [infra#61](https://github.com/TheGostsniperfr/infra/issues/61) |
| Ship only the KC 26 theme JAR | keycloak-theme | S | [theme#31](https://github.com/Arffornia/keycloak-theme-arffornia/issues/31) |
| Passkey-first browser flow + step-up (Terraform) | infra | M | after D3 |
| Google / Microsoft brokers + first-broker-login flow | infra | M | after D4 |
| Theme v2: three mock directions, then the chosen one | keycloak-theme | L | after D6 |
| Storybook + Playwright + virtual authenticator | keycloak-theme | M | [theme#22](https://github.com/Arffornia/keycloak-theme-arffornia/issues/22) |
| Website passkeys + "linked Minecraft profile" card | website | M | after D5 |
| Pocket ID spike (one app, two weeks) | infra | S | after D2 |

## Skills to add (agent-kit, Arffornia layer)

- **`keycloak-theme`**: how the Keycloakify theme is built (ejecting pages, `i18n.ts`,
  stories, the two-name rename trick, JAR targets) and the house look (tokens, motion rules,
  reduced motion).
- **`keycloak-ops`**: an optimized image, upgrading Keycloak, `terraform plan` on the realm, rotating
  client secrets, reading the event log, and what to check after an upgrade.
- **`auth-flows`**: the recommended flows above as a checklist, with a rule that every flow change
  ships with a Playwright login test.

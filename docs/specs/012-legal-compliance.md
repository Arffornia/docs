# 012 · Legal and compliance

| | |
|---|---|
| **Status** | Audit done; spec needs decisions; disclaimers implemented |
| **Milestone** | M1 · Foundation (disclaimers, licences, privacy basics), M3 (shop terms) |
| **Repos** | all public repos; Website and Launcher first |
| **Related** | [ADR-0010](../decisions/0010-open-source-licences.md) (licences) · [008](008-economy-and-rewards.md) (economy) · [009](009-ranks-roles-permissions.md) (ranks) · [010](010-vote-sites.md) (votes) · spec 007 (loading/title screen, docs PR #7) |

!!! note "Not legal advice"
    This page is an engineering audit against public rules (Mojang's Usage Guidelines and
    EULA, GDPR and the French CNIL/LCEN rules, mod licences). It lists what to fix and the
    safe defaults. For anything with money or a registration, check the current official text.

## Summary

Arffornia never had a legal pass. The main gaps are these. There is no "not official
Minecraft" disclaimer anywhere. The repos have no licence, or MIT under a nickname. The
website has no legal notice (mentions légales), no privacy policy and no terms. Three jars
committed in Provisioning are redistributed, and two of them are FTB leftovers, one an
analytics mod. The website loads third-party resources (Google Fonts, minotar,
mineskin) that send visitors' IPs abroad. The fixes are mostly text and small changes.
None of them needs money.

## Audit

| # | Area | Finding | Evidence | Severity | Fix |
|---|---|---|---|---|---|
| 1 | Mojang Usage Guidelines | No "NOT AN OFFICIAL MINECRAFT [PRODUCT/SERVICE]. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT." on the website, launcher, docs, READMEs, vote listings | grep of all repos | High | **Done**, see PRs below; vote listings and Discord at registration |
| 2 | Brand use | "Arffornia" is the primary name; "Minecraft" appears only as a description. Compliant | site, launcher | OK | keep "Minecraft" secondary ("a modded Minecraft server") |
| 3 | Logo | `Crafting_Table.png` is an original drawing that evokes the vanilla crafting table. Fine for a fan project; weak for a trademark because it borrows Mojang's design | `public/images/Crafting_Table.png` | Low | Brian confirms provenance; an original mark from the art-direction work before any trademark filing (D5) |
| 4 | Monetisation | PR #25 adds PayPal to buy currency with real money; ranks grant claims, force-loads, homes, kits (gameplay advantages) | Website #25, LuckPerms export | High if merged | close #25; no real money (spec 008); ranks earned only (spec 009) |
| 5 | Loading/title screen | the vanilla "Copyright Mojang AB. Do not distribute!" line must stay visible on any custom title screen (FancyMenu) | spec 007 | Medium | requirement added to spec 007 review |
| 6 | Our licences | Website, Mods (`All Rights Reserved`), Proxy, keycloak-theme, docs, agent-kit had none; Provisioning, Launcher, Nexus_* are MIT under "TheGostsniperfr" / "The_Gost_sniper" | GitHub licence API | Medium | **PRs open** (ADR-0010) |
| 7 | Mod redistribution | Provisioning commits and serves 3 jars: **FTB Auxilium** (All Rights Reserved, FTB's stats/analytics mod), **Rocket Game Platform client** (MIT, FTB Worlds promotion), **CC: Tweaked** (ComputerCraft Public License; also listed from Modrinth, so duplicated) | `config/{server,launcher}/storage/mods/*.jar` | High (ARR redistribution + telemetry) | remove all three (D1); CC: Tweaked keeps coming from Modrinth |
| 8 | CurseForge downloads | the launcher fetches download URLs through `api.curse.tools`, an unofficial proxy, not the official API with a key; mods whose authors disabled third-party distribution have no download URL | `Nexus_Mods/src/api/CurseforgeAPI.ts` | Medium | official API with a key (already agreed, Nexus_Mods #18); on a null URL, stop with a clear message, never mirror the jar |
| 9 | Pack visuals | FancyMenu config ships DireWolf20/FTB visuals (ARR assets of another pack) | earlier audit, agreed by Brian | Medium | replace with Arffornia art (title-screen chantier) |
| 10 | Legal notice | no "mentions légales" page (mandatory for a French website, LCEN art. 6) | website routes | High | `/legal` page (D2 for the identity details) |
| 11 | Privacy policy | none; personal data collected (below) | website | High | `/privacy` page |
| 12 | Terms | no terms of use (CGU); no terms of sale needed while nothing is sold for money | website | Medium | `/terms` page with rules, virtual currency, accounts, moderation |
| 13 | Cookies | `laravel_session`, `XSRF-TOKEN` (strictly necessary), `locale` (language chosen by the user, exempt as an interface preference per CNIL guidelines); no analytics | i18n PR #101 | OK | no banner needed; list them in the privacy policy (D3) |
| 14 | Third-party requests | Google Fonts (`stages.css` `@import`), `minotar.net` avatars, `mineskin.eu` skins, Discord widget API, `dipped.dev` logo, forgecdn/modrinth icons: each sends the visitor's IP to a third party, without consent | `public/css/pages/stages.css:24`, `layout.blade.php`, `skinviewer.js` | Medium | self-host the font and icons; proxy and cache avatars/skins through the website |
| 15 | IP retention | `votes.ip_address` and `sessions.ip_address` kept forever | migrations | Medium | votes 30 days, sessions per Laravel GC; nginx and game logs 30 days |
| 16 | Public map | BlueMap at `map.arffornia.com` can show live player positions | infra | Low | hide players by default or make it opt-in (D4) |
| 17 | Trademark | "Arffornia" not registered | — | Low | free availability search now; registration only if Brian wants it (D5) |
| 18 | Minors | Minecraft is all-ages; the server must stay suitable for all ages (Usage Guidelines); GDPR: France sets digital consent at 15, but our processing rests on the terms (account) and legitimate interest, not consent | — | Info | rules page + moderation; no consent-based processing |

## Personal data inventory (for the privacy policy)

| Data | Where | Purpose | Legal basis | Retention |
|---|---|---|---|---|
| Minecraft UUID, username, Microsoft sign-in result | website `users`, Keycloak | account, game link | contract (terms) | until account deletion; inactive 3 years → deletion notice |
| Money, purchases, rewards, votes count, progression, team | website DB | game features | contract | account lifetime |
| IP address (votes) | `votes` | vote fraud check | legitimate interest | 30 days |
| IP + user agent (sessions) | `sessions` | security, login | legitimate interest | session lifetime |
| IP (web and game logs) | nginx, server `latest.log`, Velocity | security, abuse | legitimate interest | 30 days |
| Chat messages | game logs, Discord bridge | moderation | legitimate interest | 30 days in logs |
| Positions | BlueMap | public map | consent (if opt-in) or none (hidden) | live only |
| Launcher tokens | player's own computer (encrypted, launcher PR) | sign-in | contract | local, user-controlled |

Rights: access, rectification, deletion, objection. Contact: an email address on the
legal page. Deletion: a "Delete my account" button on the profile (work item). No
transfers outside the EU from Arffornia's own systems once item 14 is fixed. Microsoft
sign-in is Microsoft's processing, under its own policy.

## Pages to write (website)

| Page | Content | en/fr |
|---|---|---|
| `/legal` (mentions légales) | publisher (D2), publication director, host (self-hosted: Brian; DNS registrar named), contact email, the Mojang disclaimer, trademark notice "Minecraft is a trademark of Mojang AB" | yes |
| `/privacy` | inventory above, rights, contact, cookies list, retention | yes |
| `/terms` (CGU) | who can play, account rules, server rules (link to `/reglement`), virtual currency has no real value and is not refundable or transferable, moderation and bans, liability limits, changes to the terms | yes |
| `/credits` | Mojang credit; every mod with author, licence and link (generated from the mod lists), fonts and icons with their licences; Arffornia art under CC BY 4.0 | yes |

All four go in the footer next to the disclaimer.

## Implemented now (clear-cut)

| PR | What |
|---|---|
| https://github.com/Arffornia/Arffornia_Website/pull/110 | Footer disclaimer, en/fr, with a test (stacked on the i18n PR #101) |
| https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/74 | Disclaimer in Settings, en/fr (stacked on the i18n PR #67) |
| https://github.com/Arffornia/docs/pull/8 | Docs licence + disclaimer in the site footer |
| Licence PRs (ADR-0010) | Website #109, Mods #54, Proxy #14, keycloak-theme #30, agent-kit #4, docs #8; each README also carries the disclaimer |

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Committed jars (FTB Auxilium, Rocket Game Platform client, CC: Tweaked duplicate) | (a) remove all three; (b) keep CC: Tweaked jar, drop the Modrinth entry | **(a)**: two are FTB leftovers (analytics and FTB Worlds promotion), one is a duplicate |
| D2 | Publisher identity on `/legal` | (a) Brian's name + contact email (French law for a non-professional allows keeping the postal address with the host only); (b) a nickname with full identity given to the host | **(a)** name + email; check the current LCEN wording before publishing |
| D3 | Cookie banner | (a) none, list cookies in the privacy policy; (b) a banner anyway | **(a)**: only exempt cookies, as long as no analytics are added |
| D4 | BlueMap players | (a) hidden by default, `/map show` opt-in; (b) visible to all | **(a)** |
| D5 | "Arffornia" trademark | (a) free availability search only (INPI, EUIPO, WIPO databases); (b) file at INPI (about 190 € for one class for 10 years, to confirm) | **(a)** now; (b) only with an original logo and if Brian wants it (about 19 €/year, inside the "few euros over a long period" exception) |
| D6 | Third-party assets on the site | (a) self-host fonts/icons, proxy avatars and skins with a cache; (b) keep direct calls and add a consent banner | **(a)** |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | Legal pages `/legal`, `/privacy`, `/terms`, `/credits` (en/fr) + footer links | Website | Pages render in both locales; linked from every page | M |
| 2 | Generated mod credits from the mod lists | Provisioning + Website | Credits page lists every mod with author, licence, link | M |
| 3 | Self-host Montserrat and icons; avatar/skin proxy with cache | Website | No third-party request on page load (Playwright check) | M |
| 4 | Retention jobs: vote IPs 30 days, log rotation 30 days | Website + infra | Scheduled; tests with a fixed clock | S |
| 5 | Account deletion button | Website | Deletes or anonymises user data; keeps ledger totals anonymised | M |
| 6 | Remove the three committed jars (D1) | Provisioning | Full-pack boot passes without them | S |
| 7 | Official CurseForge API, refuse null download URLs | Nexus_Mods + Launcher | No `api.curse.tools`; clear error for non-distributable mods | S (decided in Nexus_Mods #18) |
| 8 | Title screen keeps the Mojang copyright line | Provisioning (FancyMenu) | Visible in the title-screen screenshot test | S |
| 9 | BlueMap hidden players (D4) | Provisioning | Players not shown unless opted in | S |
| 10 | Close Website PR #25 (PayPal) | Website | Closed with a link to spec 008 | S |

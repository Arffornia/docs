---
status: proposed
date: 2026-10-31
---

# 0011 · Two identity planes: players on the website, staff on Arffornia ID

## Context
- Players sign in on the website with Microsoft. The website then checks Minecraft ownership
  through Xbox Live and XSTS (`arffornia/minecraft-oauth`).
- Keycloak ("Arffornia ID") protects only the infra apps (Argo CD, Vault, Longhorn, Adminer),
  and it has 2 users.
- Brian asked for passkeys, Google / Microsoft login, Minecraft account linking and a better
  login page. He also asked whether a lighter IdP should replace Keycloak.

## Decision (proposed)
- **Players:** the website stays the identity provider. Microsoft remains the only way to
  *create* a player account, because it is the only proof of Minecraft ownership. Passkeys are
  added as a fast way back in.
- **Staff:** keep Keycloak for now. Make it passkey-first, add Google and Microsoft brokers
  with explicit account linking, apply the Arffornia theme, and start it from an optimized
  build. Run a Pocket ID spike before considering a replacement.
- Details, flows and the comparison of alternatives are in [spec 013](../specs/013-arffornia-id.md).

## Consequences
- No Keycloak extension for the Xbox/Minecraft chain, and no extra redirect for players.
- Two login UIs to keep consistent: the website and the Keycloak theme share the design
  tokens.
- Replacing the staff IdP later stays cheap, because only 4 OIDC clients depend on it.

## Alternatives considered
- **One IdP for players and staff** (Keycloak or Zitadel with a custom Minecraft linking
  step): a central account, but a Java SPI or Actions code to maintain, and every player
  login gets slower. Not worth it at this scale.
- **Replace Keycloak now with Pocket ID / Kanidm / Rauthy**: lighter, but the boot-time pain
  has a cheaper fix (`--optimized`). Kept as a measured spike.

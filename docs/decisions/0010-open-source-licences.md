---
status: proposed
date: 2026-10-31
supersedes: ~
---

# 0010 · MIT for code, CC BY 4.0 for art and docs

## Context
Brian wants Arffornia to be open source, with one condition: reusers must credit the
original author, Brian Perret, and the Arffornia project (Chantier 0, licence decision).
Before this, the Website, Mods (`All Rights Reserved`), Proxy, keycloak-theme, docs and
agent-kit repos had no licence; Provisioning, the Launcher and the Nexus libraries are MIT
under the nicknames "TheGostsniperfr" / "The_Gost_sniper".

## Decision
- **Code: MIT**, copyright line `Copyright (c) 2024-2026 Brian Perret and Arffornia
  contributors`. MIT requires that this notice and the licence text stay in every copy or
  substantial portion, so the credit travels with the code.
- **Original art (textures, models, images, sounds) and documentation: CC BY 4.0.**
  Anyone may share and adapt it, commercially too, if they **give credit** ("by Brian
  Perret and Arffornia contributors"), **link the licence**, and **say what they changed**,
  without implying endorsement. The licence file of each repo lists the covered folders and
  the third-party material it does not cover (Minecraft textures, mod logos, template
  icons).
- Contributors keep their copyright and license their contributions under the same terms
  (inbound = outbound, stated in CONTRIBUTING).
- Every licence file and README carries the Mojang "NOT AN OFFICIAL MINECRAFT PRODUCT…"
  disclaimer.

## Consequences
- Each repo gets `LICENSE` (MIT) and, when it has art or docs, `LICENSE-ASSETS` or
  `LICENSE-DOCS` (CC BY 4.0). PRs: Website #109, Mods #54, Proxy #14, keycloak-theme #30,
  docs #8, agent-kit #4.
- The mod's `mod_license` shows "MIT (code), CC BY 4.0 (art assets)" in the mod list
  screen.
- Repos already under MIT keep it; aligning their copyright line to "Brian Perret and
  Arffornia contributors" is optional (one-line PRs, D1 below).
- MIT's credit lives in source and binary notices, not in a visible UI. If Brian later
  wants credit that must appear in derived products' notices, Apache-2.0 with a `NOTICE`
  file is the stronger option.

## Alternatives considered
- Apache-2.0 for code: stronger attribution (`NOTICE`) and a patent grant, but longer and
  heavier for a small project. Kept as the fallback.
- GPL/MPL: force derived code to stay open; Brian asked for credit, not copyleft.
- CC BY-SA or BY-NC for art: share-alike or no commercial use limit reuse more than asked.
- No licence: "all rights reserved" by default, so nobody may legally reuse anything.

## Open point
- D1: harmonise the copyright line of the existing MIT repos (Provisioning, Launcher,
  Nexus_Java, Nexus_Logger, Nexus_Mods, Nexus_Saver)? Default: yes, in the next foundation
  touch of each repo. Bootstrap and minecraft-oauth have no licence and were not reachable
  from this session; they get the same treatment.

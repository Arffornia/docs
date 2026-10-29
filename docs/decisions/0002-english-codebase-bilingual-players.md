---
status: accepted
date: 2026-10-29
---

# 0002 · English codebase, bilingual players (EN/FR)

## Context
The project started in French. Code, comments and docs now mix French and English, while
players speak French or English.

## Decision
- Code, comments, commit messages, issues, PRs and docs are **English**.
- Everything a player sees goes through i18n with **English and French** at minimum:
  `vue-i18n` locales in the launcher, Laravel lang files on the website, `en_us.json` and
  `fr_fr.json` in the mod. No user-visible literal outside locale files.
- Layouts must hold both languages (French strings are often ~20 % longer).

## Consequences
- Lint rules flag bare strings where tooling allows (`vue/no-bare-strings-in-template`,
  a lang-key test in the mod).
- UI checks render screens in both languages.

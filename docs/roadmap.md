# Roadmap

The live view is the org board **Arffornia Roadmap** on GitHub. This page gives the direction.

## M1 · Foundation & security

Bring every repo to a state where people and agents can work safely.

- [ ] Every repo: README, AGENTS.md, `make check`, CI on pull requests, Dependabot
- [ ] Fix the audit's P0/P1 issues: launcher hardening, token handling, server-side packet checks,
      reward command execution, website debug mode, mods silently removed on sync failures
- [ ] Rotate exposed credentials
- [ ] Docs site with architecture diagrams and ADRs
- [ ] Shared labels, milestones and the org board

## M2 · Tests & CI

- [ ] Unit tests in every repo, offline in CI
- [ ] Mod GameTests in CI; launcher E2E with Playwright; website E2E on critical journeys
- [ ] Signed launcher releases; reproducible images and pinned dependencies
- [ ] Pack boot test: the full modpack starts in CI
- [ ] Off-site backups with a tested restore

## M3 · Gameplay foundations

- [ ] Recipes as a generated datapack with a real recipe type ([ADR-0006](decisions/0006-recipes-as-datapack.md))
- [ ] Machine framework, then the first new machines
- [ ] Immersive-Engineering-style multiblocks with a futuristic, Satisfactory-like look
- [ ] Per-PR preview servers and in-game automated playtests ([ADR-0007](decisions/0007-preview-environments.md))
- [ ] Bilingual (EN/FR) website, launcher and mod
- [ ] In-game GUI design system for polished interfaces

## Later

Integrate the candidate mods into the progression, rankings and seasons, voice and AI
experiments ("Minecraft x AI"), and a richer launcher. Ideas start as `proposal` issues.

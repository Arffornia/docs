---
status: accepted
date: 2026-10-29
---

# 0006 · Deliver custom recipes as a generated datapack

## Context
Custom recipes live in the website database as flat 3×3 lists. The server and every client
fetch them over HTTP into separate caches; JEI can show nothing if the client fetch is late;
if the API is down at load, no recipe is banned. Recipes are captured by flattening existing
ones, which drops tags, components and leftovers.

## Decision
- The mod registers a real `RecipeType`/`RecipeSerializer` (`SizedIngredient`, results,
  energy, time, a stable `stage` key such as `arffornia:stage2/steel`).
- The website stays the editor and exports a **datapack**: machine recipes plus overrides
  that disable banned recipes with the `neoforge:false` condition.
- The provisioning step drops the datapack into the world; Minecraft syncs recipes to
  clients and JEI reads them from the `RecipeManager`.
- Player stages become a data attachment synced to the client; machines check stages
  without HTTP.

## Consequences
- No client HTTP for recipes, no fail-open, recipes are reviewable files, CI can boot a
  GameTest server against them.
- Gating is chosen **per recipe**: machine-only (original disabled, machine recipe added) or
  stage-locked in place (wrapper recipe + crafting-player mixin). JEI keeps showing every
  recipe with its tier, milestone and machine.
- The website stays the easy editor; "Publish" applies to the live server with `/reload`, and
  a Provisioning snapshot PR keeps the git history (spec 001).
- Accepted by Brian in Chantier 0 (31 Oct 2026).

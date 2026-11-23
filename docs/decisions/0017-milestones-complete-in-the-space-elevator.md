---
status: accepted
date: 2026-11-23
supersedes: ~
---

# 0017 · Milestones complete in the Space Elevator only

## Context
Spec 017 had three validations: `obtain`, `craft` and `deliver`. Obtain and craft were detected
through one hidden advancement per milestone (`arffornia:milestone/<key>`) in the datapack built
from a snapshot, with the triggers `minecraft:inventory_changed` and `arffornia:item_crafted`
(Website#169, #171; Mods#79). A milestone without a stored validation was completed by obtaining
what it unlocks. Players could complete milestones by accident, without choosing them, and two
paths to one result made the game harder to read and to test.

## Decision
A milestone is completed through one path only, as with Satisfactory's Space Elevator (Brian,
23 Nov 2026, final):

1. The player selects (targets) an available milestone (spec 017 rule 3).
2. They deposit its required items in the Space Elevator.

Owning or crafting an item before never counts, nor does producing what the milestone unlocks.
The admin command `/arffornia progression add <player> <id>` stays and obeys the same
availability rule.

## Consequences
- The snapshot schema keeps `validation` with the single type `deliver`, or `null`. `obtain` and
  `craft` are invalid.
- The datapack holds recipes and bans only; the hidden milestone advancements and their detection
  in the mod are removed.
- Every milestone needs requirements. The current tree has 166 without any; the validator warns
  (`no_validation`) until Brian adds them.
- `milestones.validation` in the website store is no longer read or written. It stays until a
  cleanup migration removes it.
- Snapshots published before this ADR may hold `obtain` or `craft`; the website ignores them.

## Alternatives considered
- Keep obtain and craft beside delivery: completions by accident, two paths to test.
- Detect obtain or craft only for the targeted milestone: still completes without the elevator,
  and keeps the advancement machinery for little gain.

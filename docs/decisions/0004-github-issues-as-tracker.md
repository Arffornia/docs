---
status: proposed
date: 2026-10-29
---

# 0004 · GitHub issues and an org Project as the tracker

## Context
Tasks lived in a Notion board: 8 real tasks, none with a priority or description, last
touched in July 2026. The goal is now agent-driven work and outside contributors, both of
which live on GitHub.

## Decision
- Every task is an issue in the repo it changes, with the shared labels
  (`type:*`, `area:*`, `priority:P0–P3`, `effort:S/M/L`, `agent-ready`, `needs-decision`,
  `proposal`) and a milestone (`M1 · Foundation & security`, `M2 · Tests & CI`,
  `M3 · Gameplay foundations`).
- One organisation Project, **Arffornia Roadmap**, shows all repos as a board grouped by
  status, with views per area and per priority.
- Notion keeps long-form ideation only (game ideas, infra study notes).

## Consequences
- An issue with `agent-ready` has acceptance criteria and no open design question: an AI
  agent may take it. `needs-decision` blocks until the maintainer answers in the issue.
- Ideas from agents arrive as `proposal` issues; only the maintainer promotes them.

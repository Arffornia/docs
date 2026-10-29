---
status: accepted
date: 2026-10-29
---

# 0001 · Record architecture decisions

## Context
Arffornia has been built by one person for about ten years. Decisions live in his head, so
new contributors and AI agents cannot tell a deliberate choice from an accident.

## Decision
Record every decision that shapes more than one component, or that someone may want to
undo later, as an ADR in this site. ADRs are short and use the [template](template.md).

## Consequences
- Agents read accepted ADRs before working and must not contradict them; a change of mind
  is a new ADR that `supersedes` the old one.
- Reviews can point to an ADR instead of re-arguing.

# Working with AI agents

Most routine work on Arffornia is done by AI agents (Claude Code) and reviewed by the
maintainer. The same rules apply to people and agents; agents just follow them more literally.

## The loop

The maintainer's workflow (adopted 2026-10-31; generic version in
[agent-playbook `runbook/WORKFLOW.md`](https://github.com/TheGostsniperfr/agent-playbook/blob/main/runbook/WORKFLOW.md)):

1. **Agents propose chantiers** (or the maintainer writes an issue and labels it `agent-ready`).
2. **Agents write the spec** for a new chantier: a spec or research page plus decisions, each
   with a recommended default and a plain-words "why". The maintainer validates or challenges it.
   Only work the maintainer asked for explicitly, or clear-cut fixes, skip this step.
3. **Agents implement and open the PRs themselves**: branch, tests, `make check`, then a pull
   request that says how it was tested and what a human should try.
4. **Agents run the end-of-task review** in their own session (no AI review in CI).
5. **Anything that needs a human goes to the review stack**: decisions, high-risk points,
   manual tests with a guide. Reports stay high level; evidence stays in the PRs.
6. **The maintainer validates the chantier** ([operating model](operating-model.md)).
7. **Agents merge and deploy** it, in order, through the orchestrator's merge plan. They never
   merge anything outside an approved chantier.

No paid services: free tiers, open source and self-hosted tools only.

## What agents may and may not do

| May | May not |
|---|---|
| Open issues, branches and pull requests | Merge, tag, release, delete branches (only the orchestrator, after approval) |
| Open chantiers and add `chantier: review` | Add `chantier: approved` to their own work |
| Run builds and tests, install dev dependencies | Read or write secrets, change repo settings |
| Propose ideas as `proposal` issues | Implement `needs-decision` issues |
| Improve the Nexus libraries | Replace them with third-party packages |

## Where agents find context

- `AGENTS.md` in each repo: commands, layout, rules, gotchas.
- This site: architecture, components, ADRs, standards.
- The Noodle model in `architecture/arffornia/` for "what talks to what".

## Writing a good agent-ready issue

- One outcome per issue, with a checklist of acceptance criteria.
- Evidence: file paths and lines, logs, screenshots.
- Any design choice already made (or link the ADR).
- What "tested" means here: a unit test, a GameTest, a screen to check in EN and FR.

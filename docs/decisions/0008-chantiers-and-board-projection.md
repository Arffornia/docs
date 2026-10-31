---
status: proposed
date: 2026-10-29
supersedes: ~      # amends 0004 (board layout and merge rule)
---

# 0008 · Chantiers are the unit of review; the board is a projection of labels

## Context
- Agents now do most of the work. On 2026-10-29 the org board held about 230 rows: 144 issues
  and 91 PRs, 68 of the issues duplicated by the PR that closes them, 34 `needs-decision`
  issues mixed with ready work, and most rows in two Status columns.
- One wave of agent work produced 71 PRs in 11 repos. The merge order and the decisions were
  written in a chat report and several artifacts; the maintainer could not find them again.
- The maintainer wants to validate a group of PRs from one page and stop merging by hand.
- Agent sessions can use repository-scoped REST only: no GraphQL, no org-level REST. Project
  fields can only be written from Actions with the org token.
- Practice elsewhere (sources below): review is the bottleneck once agents write code
  (CMU 2026, Semgrep 2026); humans should review intent, risk and decisions, routine changes
  should flow (Semgrep, Osmani); a human stays accountable and agents never self-approve
  (Linear AIG, GitHub Copilot: the requester's approval does not count); work in parallel is
  capped by a WIP limit sized to review capacity (Osmani: 4 to 5 background agents per person).

## Decision
- A **chantier** is a parent issue in `Arffornia/docs` (label `chantier`, issue form
  `chantier.yml`) that lists PRs in merge order, the issues they close, decisions with
  defaults, what was and was not verified, a risk class (A/B/C), the agent, a stack order and a
  link to a summary page. It is the only thing the maintainer reviews.
- Review state is a label: `chantier: review` → `chantier: approved` or `chantier: changes`.
- The board is recomputed from labels and links by `scripts/sync_board.py`: fields Lane,
  Decision, Chantier, Order, Agent, Risk; views Brian's stack, Pipeline, Agent queue, In flight,
  Merging, Inbox. PRs that close an issue or belong to a chantier are not added as rows.
- No hard WIP limit (amended 2026-10-31: the maintainer reviews in evening and weekend
  batches). `chantiers.py --wip` and the board sync report a soft review load; limits apply
  only if `WIP_IN_FLIGHT` / `WIP_REVIEW` are set.
- After approval by the maintainer, an orchestrator merges the PRs in order with merge commits
  (`scripts/chantiers.py --merge-plan N --execute`), deleting stacked base branches in the
  repos where GitHub does not, then closes the chantier. Agents never merge on their own.
- Proposals stay in the Inbox lane and never expire (amended 2026-10-31); after 30 days without
  activity they are dormant and the weekly brief resurfaces them.

## Consequences
- The maintainer's queue is one ordered list of pages; one decision per chantier, defaults
  pre-filled.
- Agents must write a chantier and its summary page at the end of the work; a PR alone is not
  "done".
- The board can be rebuilt at any time from GitHub data; nobody drags cards.
- Cost: one more issue per batch of work, and a Projects token in Actions (already there).
- Not covered yet: auto-merge of risk-A chantiers without review (possible later, once the
  escaped-defect rate is known), and a merge queue (only for public org repos, and it does not
  take stacked PRs that target another branch).

## Alternatives considered
- **Keep one row per issue and PR**: what failed; duplicates and no grouping.
- **GitHub sub-issues only**: PRs cannot be sub-issues, and sub-issues must have the same
  owner (the infra repo is personal), so the chantier body still has to list PRs.
- **Graphite or GitHub stacked PRs**: helpful for stacks inside one repo, not for a review
  unit that spans repos; GitHub's version was a waitlisted preview (2026-04).
- **Linear or another tracker with agent delegation**: good agent UX, but a second source of
  truth next to GitHub, which ADR-0004 chose.
- **AI review bot in CI**: rejected by the maintainer (no API key in GitHub); review happens in
  the agent's session at the end of the task.

## Sources
- Anthropic, Effective harnesses for long-running agents, 2025-11-26 — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, Claude Code best practices (worktrees, writer/reviewer split, /batch) — https://code.claude.com/docs/en/best-practices
- Linear, Agent Interaction Guidelines, 2025-07-30 — https://linear.app/developers/aig
- GitHub, Review Copilot PRs — https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/review-copilot-prs
- GitHub, Agent HQ, 2025-10-28 — https://sdtimes.com/ai/github-unveils-agent-hq-the-next-evolution-of-its-platform-that-focuses-on-agent-based-development/
- Addy Osmani, Your AI coding agents need a manager, 2026-01-08 — https://addyosmani.com/blog/coding-agents-manager/
- Agarwal et al. (CMU), 3100 Opinions on Code Review in an AI World, 2026-07-08 — https://www.alphaxiv.org/abs/2607.07980.md
- Semgrep, The end is nigh for code review, 2026-10-09 — https://semgrep.dev/blog/2026/end-is-nigh-for-code-review
- Basecamp, Shape Up, the betting table — https://basecamp.com/shapeup/2.2-chapter-08
- GitHub REST: project views (create) — https://docs.github.com/en/rest/projects/views ; sub-issues — https://docs.github.com/en/rest/issues/sub-issues
- GitHub, Managing a merge queue — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- InfoQ, GitHub stacked PRs preview, 2026-04-29 — https://infoq.com/news/2026/04/github-stacked-prs

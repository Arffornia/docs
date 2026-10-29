# Working with AI agents

Most routine work on Arffornia is done by AI agents (Claude Code) and reviewed by the
maintainer. The same rules apply to people and agents; agents just follow them more literally.

## The loop

1. The maintainer writes or approves an issue and labels it `agent-ready`.
2. An agent reads the repo's `AGENTS.md`, the issue and the relevant ADRs.
3. It branches, implements, adds tests, runs `make check`, and opens a pull request that says
   how it was tested and what a human should try.
4. The maintainer reviews, asks for changes in the PR, and merges. Agents never merge.

## What agents may and may not do

| May | May not |
|---|---|
| Open issues, branches and pull requests | Merge, tag, release, delete branches |
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

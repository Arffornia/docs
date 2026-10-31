# Contributing

Arffornia is maintained by one person with help from AI agents. Contributions are welcome:
bug reports, fixes, tests, docs, translations.

## Start here

1. Read the [architecture overview](../architecture/index.md) and the page of the
   [component](../components/index.md) you want to touch.
2. Pick an issue labelled `good first issue` or `agent-ready`, or open one first for anything
   that changes behaviour.
3. Each repo has an `AGENTS.md` with its commands, map and rules. It is written for AI agents
   and works just as well for humans.
4. Run `make check` before you open a pull request.

## Ground rules

- English in code and docs; player-facing text in English **and** French ([ADR-0002](../decisions/0002-english-codebase-bilingual-players.md)).
- The Nexus libraries are improved, never replaced ([ADR-0003](../decisions/0003-keep-owner-libraries.md)).
- No secrets in git. Configuration uses placeholders (`${CFG_*}`) filled at deploy time.
- Security issues: use **Report a vulnerability** on the repo, never a public issue.

Next: [workflow](workflow.md) · [operating model](operating-model.md) · [standards](standards.md) · [AI agents](ai-agents.md) · [diagrams](diagrams.md)

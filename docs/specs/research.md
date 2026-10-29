# Tooling research specs

Research specs for the tooling that lets AI agents build **and test** Minecraft content for
Arffornia before handing it to the maintainer. Each spec compares options found on the web
(checked on 2026-10-29), recommends one, and splits the work into issue-sized tasks. They are
proposals: decisions go into ADRs.

| # | Spec | Recommends |
|---|---|---|
| [004](004-in-game-e2e-testing.md) | In-game end-to-end testing | GameTests on every PR; a dev-only client test-harness mod under Xvfb + llvmpipe with EN/FR and GUI-scale screenshots; an MCP wrapper over Gradle and RCON |
| [005](005-3d-model-pipeline.md) | 3D model pipeline | `.bbmodel` sources edited by agents through the headless Blockbench MCP; Java block JSON for static parts, GeckoLib for animated ones; headless turntables and a PR gallery |
| [006](006-gui-design-system.md) | GUI design system | Native screens built with LDLib2 (XML + CSS-like stylesheets) themed from design tokens shared with the website; strict i18n with overflow checks; web layer only later |

Related: [ADR-0002](../decisions/0002-english-codebase-bilingual-players.md) (bilingual
players), [ADR-0007](../decisions/0007-preview-environments.md) (preview environments).

# AGENTS.md — Arffornia docs

Project-wide documentation site (MkDocs Material) and the Noodle architecture model.

## Commands
- `make check` — Noodle lint of every view + `mkdocs build --strict` (CI runs this)
- `make serve` — local preview
- `make diagrams` — render all views, dark and light, PNG + editable SVG (needs draw.io;
  headless: `xvfb-run drawio --no-sandbox --use-angle=swiftshader --enable-unsafe-swiftshader`)
- `make discover INFRA=../infra` — regenerate `architecture/arffornia/discovered/` from the infra repo

## Map
- `docs/index.md` home · `docs/architecture/` diagram pages · `docs/components/` one page per repo
- `docs/contributing/` workflow, standards, AI agents, diagrams · `docs/decisions/` ADRs
- `architecture/arffornia/` Noodle system: `model.yaml`, `views/`, `layouts/`, `discovered/`

## Rules
- English only. Concise: short sentences, tables over prose, no marketing.
- Diagrams follow the Noodle skill (TheGostsniperfr/Noodle `skills/noodle-diagram`). Never
  hand-edit `.drawio` exports; change the YAML and re-render.
- A page states facts from code; when docs and code disagree, fix the doc or open an issue.
- New decisions: copy `docs/decisions/template.md`, next number, add it to the index.
- Accepted ADRs are rules; do not contradict them without a superseding ADR.

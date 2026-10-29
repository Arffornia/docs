---
status: proposed
date: 2026-10-29
---

# 0005 · Docs as code: MkDocs site and Noodle diagrams

## Context
Each repo had at most a short README; the ecosystem was never described as a whole.

## Decision
- Project-wide docs live in `Arffornia/docs`, built with MkDocs Material and published to
  GitHub Pages. Repo-specific docs stay in each repo (`README.md`, `AGENTS.md`).
- Architecture diagrams are generated with [Noodle](https://github.com/TheGostsniperfr/Noodle)
  from `architecture/arffornia/` (one model, several views). CI lints them; PNG and SVG
  exports are committed for both themes.
- Kubernetes facts come from `noodle discover k8s` on the rendered `infra` manifests, so the
  diagrams can be checked against what is deployed.

## Consequences
- A change that adds or removes a component updates the model in the same PR.
- Mermaid is allowed for small, local sketches inside a component page.

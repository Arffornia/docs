# Diagrams

Architecture diagrams are generated with [Noodle](https://github.com/TheGostsniperfr/Noodle),
not drawn by hand ([ADR-0005](../decisions/0005-docs-as-code.md)).

```
architecture/arffornia/
  model.yaml        what exists: elements, connections, references
  views/<id>.yaml   what one diagram shows
  layouts/<id>.yaml where a topology view is drawn
  discovered/       fragments from `noodle discover k8s` (generated)
docs/assets/diagrams/<view>.{dark,light}.{png,svg}   exports used by this site
```

## Change a diagram

```bash
S=architecture/arffornia; V=runtime
noodle render $S -view $V                 # check + lint, fix every finding
make diagrams                             # renders every view, both themes, PNG + SVG
```

`make diagrams` needs draw.io desktop for the PNG/SVG export. Headless:
`xvfb-run drawio --no-sandbox --use-angle=swiftshader --enable-unsafe-swiftshader -x …`.

## Check against reality

```bash
make discover   # kustomize build the infra overlays, then noodle discover k8s → discovered/
```

Model elements carry `matches` pointing to discovered IDs. When a discovered workload has no
model element, or a modelled connection has no evidence, open an issue or fix the model.

## House rules

From the Noodle skill: one question per diagram, arrows go from the client to the listening
server, requests only, numbered steps are the request path, letters are background work,
planned things are hatched with a target.

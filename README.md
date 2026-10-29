# Arffornia docs

Source of **https://arffornia.github.io/docs/**: architecture, components, decisions and the
contribution guide for the Arffornia ecosystem.

```bash
pip install -r requirements.txt
make serve        # preview on http://127.0.0.1:8000
make check        # lint diagrams + strict build (what CI runs)
make diagrams     # re-render diagrams (needs noodle and draw.io)
make discover INFRA=../infra   # refresh Kubernetes facts for the diagrams
```

- Pages: `docs/` (Markdown, MkDocs Material).
- Diagrams: `architecture/arffornia/` (Noodle model, views, layouts), exports in
  `docs/assets/diagrams/`.
- Decisions: `docs/decisions/` (ADRs).

Published by `.github/workflows/pages.yml` on every push to `main`
(enable Pages → Source: GitHub Actions in the repo settings).

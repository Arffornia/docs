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
- `flake.nix`: Nix dev shells for every Arffornia repo (Linux x86_64/arm64, Apple Silicon), e.g.
  `nix develop github:Arffornia/docs#node`. See `docs/contributing/dev-setup.md`.

Published by `.github/workflows/pages.yml` on every push to `main`
(enable Pages → Source: GitHub Actions in the repo settings).

## License

Documentation text and diagrams: [CC BY 4.0](LICENSE-DOCS). Scripts and configuration: [MIT](LICENSE).
Both: © Brian Perret and Arffornia contributors.

NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.

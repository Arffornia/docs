---
status: accepted
date: 2026-10-29
---

# 0003 · Keep and improve the owner's libraries

## Context
The launcher and the provisioning service rely on libraries written for Arffornia:
`@arffornia/nexus_java` (Java runtime install), `nexus_logger`, `nexus_saver` (settings
store) and `nexus_mods` (mod and file sync). Off-the-shelf packages exist for some of these
jobs. The maintainer knows these libraries end to end and wants to keep that control.

## Decision
The Nexus libraries stay. Fix, test and extend them; do not replace them with third-party
packages. A proposal to replace one needs a new ADR approved by the maintainer.

## Consequences
- Library issues (missing runtime dependency, no hash check after download, failures that
  delete mods) are fixed in the library, with tests, and released to npm.
- Libraries get the same standards as apps: lockfile, CI, offline unit tests, provenance.

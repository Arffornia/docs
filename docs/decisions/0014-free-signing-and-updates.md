---
status: proposed
date: 2026-10-31
supersedes: ~
---

# 0014 · Free code signing and auto-update for the launcher

## Context
- Brian's rule is no paid services (exceptions: a DNS name, or a few euros over a long period).
  This rules out the Apple Developer Program (99 USD/year), paid OV/EV certificates and Azure
  Trusted Signing.
- **Windows:** unsigned NSIS builds trigger SmartScreen ("Windows protected your PC"), and
  electron-updater cannot verify the publisher.
- **macOS:** the build is ad-hoc signed ([#72](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/72)).
  Electron's `autoUpdater` (Squirrel.Mac) requires a signed app: "Your application must be
  signed for automatic updates on macOS. This is a requirement of Squirrel.Mac"
  ([electronjs.org](https://electronjs.org/docs/api/auto-updater), checked 2026-10-31).
  electron-builder says the same ([electron.build](https://www.electron.build/docs/features/auto-update)).
  Squirrel.Mac also checks that the new bundle satisfies the *designated requirement* of the
  running one. An ad-hoc signature's requirement is its own code hash, so every new build
  fails that check ("code failed to satisfy specified code requirement(s)",
  [electron-builder#2399](https://github.com/electron-userland/electron-builder/issues/2399)).
  So **the standard Mac auto-update cannot work without a Developer ID.** Reading the code
  shows this; it has not been tried on a real Mac.

## Decision (proposed)
1. **Windows: apply to the SignPath Foundation** (free code signing for open-source projects,
   [signpath.org/terms](https://signpath.org/terms)). The launcher qualifies on paper:
   - MIT license, released, maintained;
   - built in GitHub Actions from its own source.

   Obligations:
   - MFA for the team;
   - a manual approval per release;
   - product name and version metadata in the binaries;
   - a "Code signing policy" section on the download page (credits SignPath, lists roles and adds a privacy line);
   - an uninstaller (NSIS has one).

   The certificate names *SignPath Foundation* as the publisher. While approval is pending,
   ship unsigned. SmartScreen reputation then builds per file hash.
2. **Windows, optional second channel:** the **Microsoft Store**. Registration has been free for
   individual developers since 2025-09-10. Microsoft signs and hosts MSIX packages and delivers
   updates ([Windows blog](https://blogs.windows.com/windowsdeveloper/2025/09/10/free-developer-registration-for-individual-developers-on-microsoft-store/)).
   This needs ID verification (a government ID and a selfie). Store builds disable
   electron-updater.
3. **macOS: "update available" flow instead of Squirrel.** Use electron-updater with
   `autoDownload = false` on macOS, and only `checkForUpdates()`. When a newer version
   exists, show a localized banner, "Version X is available — Download". The button
   opens the `.dmg` from the GitHub release. The player drags the app to Applications, as
   on first install. This is free and works today.
4. **macOS, optional later (needs a decision): in-app self-replace.**
   - The launcher downloads the release `.zip` and checks its sha512 against `latest-mac.yml`.
   - It unpacks with `ditto` to a temporary folder, swaps the `.app` bundle, and relaunches.
   - Files downloaded by the app itself get no quarantine flag, so Gatekeeper does not prompt again.
   - Trust then rests on HTTPS plus the hash in a file on the same GitHub release. That is the same
     trust as the Linux AppImage updater today, but weaker than a signature.
   - Prototype it behind a flag and test it on Brian's Mac.
5. **Linux:** the AppImage keeps electron-updater (no signing needed). Nix users update with
   `nix flake update` ([#76](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/pull/76)).
6. **Integrity, all platforms:** publish `SHA256SUMS` and a GitHub artifact attestation
   (`actions/attest-build-provenance`, free) for every release asset. Use `GITHUB_TOKEN`
   instead of a personal PAT in the release workflow.

## Consequences
- Windows players lose the SmartScreen warning once SignPath approves. Mac players get one
  click to update instead of silent updates.
- A visible "Code signing policy" page joins the website or the docs.
- If Brian ever buys a Developer ID, step 3 is replaced by standard Squirrel updates without
  other changes.

## Alternatives considered
- **Apple Developer ID:** declined (paid).
- **Paid OV/EV certificates, Azure Trusted Signing:** declined (paid).
- **Self-signed Windows certificate:** no SmartScreen benefit, and users would have to trust a root.
- **A Homebrew tap:** easy to publish, but it does not remove the Gatekeeper prompt or provide updates
  inside the app, so it does not solve the problem.

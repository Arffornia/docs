# 018 · Stage band prototype: numbers for D2

| | |
|---|---|
| **Status** | Input for D2 (work item 6). D2 decided 21 Nov 2026: (a), see the [spec](../018-ui-framework.md). |
| **Date** | 9 Nov 2026 |
| **Code** | [Arffornia_Mods#60](https://github.com/Arffornia/Arffornia_Mods/pull/60) (draft, not for main) |
| **Spec** | [018 UI framework](../018-ui-framework.md), work items 4 and 5 |

## What was built

One stage band of the progression graph, drawn in game twice from **one snapshot**
(`band.json`: positions, link paths and stage columns computed once by the web template's ELK
layout; the client never lays out):

- **Band**: Mekanism, stages 1 to 4 of the spec 017 fixture (20 milestones), player at stage 3, so
  all three states show: done, available, locked. Header with the stage and the orbital elevator, as
  Brian asked (not the HUD).
- **Native (D2 b)**: LDLib2 screen. Header and nodes are LDLib2 elements styled by an LSS stylesheet
  from the tokens; links, arrows, glow and dashed frames are drawn in Java; `GraphView` gives pan
  and zoom; item icons go through the normal item renderer.
- **Web (D2 a)**: WebGUI 2.0.0. One browser starts with the client and loads the band page
  off-screen at 1 fps. Opening the screen raises it to 60 fps and draws its texture. The page is the
  validated web template, fed by the same snapshot.

## Screenshots

Same band, same window (1280 × 720, GUI scale 3), full pack, in a world.

| Web template in Chrome (reference) | In game, web (WebGUI) | In game, native (LDLib2) |
|---|---|---|
| ![Web reference](band-web-chrome.webp) | ![In game, web](band-ingame-web.webp) | ![In game, native](band-ingame-native.webp) |

Detail at 2×, top to bottom: Chrome, in-game web, in-game native.

![Zoomed comparison](band-zoom-compare.webp)

| Pixel difference against the Chrome reference (normalised RMSE) | Value |
|---|---|
| In-game web | 3.9 % (mostly the glow animation phase) |
| In-game native | 9.1 % |

## Numbers

Full pack (333 mods), NeoForge 21.1.172, singleplayer world, 1280 × 720, GUI scale 3, `-Xmx10G`.
Machine: Ryzen 9 9900X, 32 GB, NixOS, **Xvfb with Mesa llvmpipe (software OpenGL)**. Run A: pack
with LDLib2, without WebGUI. Run B: pack with LDLib2 and WebGUI. Raw data:
[run A](bench-run-a.json), [run B](bench-run-b.json).

| Measure | Native (LDLib2) | Web (WebGUI, kept warm) |
|---|---|---|
| Build the screen on open (warm, 5 opens) | 5 to 13 ms | 0.8 to 1.4 ms |
| Build the screen, first open of the session | 81 ms | 1.4 ms |
| Open to first drawn frame | 144 to 154 ms (first: 328 ms) | 135 to 150 ms |
| Render-thread time per frame inside the screen | 2.8 ms mean, 3.1 ms p95 | 0.17 ms mean, 0.21 ms p95 (texture upload included) |
| Frame interval with the screen open (no screen: 142.7 ms) | 147.4 ms | 145.8 ms |
| CPU of the browser processes, screen open (page animating) | none | 15 % of one core |
| CPU of the browser processes, screen closed (warm, 1 fps) | none | 0 % |
| Memory of the browser processes (7 helpers) | none | 190 MB PSS (556 to 600 MB RSS) |
| Whole client, run B minus run A (PSS, in world, idle) | n/a | +272 MB (13 930 vs 13 658 MB) |
| Pack load to world (run A without WebGUI, run B with it) | 132 s | 126 to 134 s, no measurable difference |
| Browser ready / page loaded after client setup | n/a | 11 to 25 ms / 157 to 265 ms |
| First-launch download | none | 135 MB (Linux x64), unpacked 334 MB |

How to read them:

- **Software rendering hides frame cost.** At 7 fps under llvmpipe, open time is one frame interval
  for both, and frame intervals differ by less than the noise. The comparable numbers are the
  render-thread time inside the screen (native 2.8 ms, web 0.17 ms) and the browser's own CPU
  (15 % of a core while visible). On a real GPU the native cost should drop; it has not been measured.
- **Memory**: the helper processes are measured exactly (190 MB PSS). The browser process itself
  lives inside the JVM, so the whole-client delta (+272 MB) includes heap noise of about ±100 MB
  between runs. One run each.
- **WebGUI defaults add a second browser**: on join it opens a demo HUD page (`autoHudOnJoin`, and a
  web main menu). Arffornia would turn both off in `config/webgui/server.json`; with the HUD on,
  the client used +434 MB.

## Platform notes

| Topic | Finding |
|---|---|
| Browser runtime | WebGUI 2.0.0 no longer uses MCEF: it ships its own JCEF, **Chromium 135.0.7049.85** (CEF 135.0.20), not MCEF's Chromium 116 |
| Where it downloads from | Maven Central, `me/friwi/jcef-natives-<platform>/jcef-ca49ada+cef-135.0.20+ge7de5c3+chromium-135.0.7049.85/`; sizes 135 MB (Linux x64), 141 MB (Windows x64), 129 / 120 MB (macOS x64 / arm64). Not CinemaMod's server. No mirror setting |
| Where it looks for it | `$WMC_RUNTIME_DIR/135.0.20/<platform>/`, else `~/.wmc/runtime/…` (Windows: `%LOCALAPPDATA%\wmc\runtime\…`). A folder counts as installed when it holds a `.wmc-complete` file |
| Launcher pre-placement (work item 5b) | **Works**: an unpacked runtime copied to a fresh folder with its `.wmc-complete` marker, `WMC_RUNTIME_DIR` pointing to it: no download, browser ready before client setup ends |
| MCEF itself (for reference) | MCEF 2.1.6 (Oct 2024) downloads from `mcef-download.cinemamod.com` (mirror via `mcef.properties`, folder via `mcef.libraries.path`). Not tested, WebGUI no longer needs it |
| NixOS | Fails out of the box (`libcef.so: libnss3.so: cannot open shared object file`). **Works** when the game is started with nss, nspr, dbus, at-spi2-core, cups, libgbm, libdrm, expat, libxkbcommon, pango, cairo, glib, systemd (libudev), alsa-lib, the X libraries (libx11, libxext, libxcb, libxcomposite, libxdamage, libxfixes, libxrandr) and the JDK's own `lib/` (`libjawt.so`) on `LD_LIBRARY_PATH`. glibc version was not the problem |
| Helper crashes | A Chromium utility helper (`unzip.mojom.Unzipper`) aborted on `__stack_chk_fail` in a loop in one minimal-pack session; the band kept working. Cause not found |
| Windows, macOS | Not tested (no machine in this session) |
| LDLib2 and our NeoForge | **2.2.2 (Feb 2026) is the last LDLib2 build that accepts NeoForge 21.1.172**; 2.2.3 to 2.2.46 (current) require NeoForge ≥ 21.1.216. Native means a NeoForge bump of the pack or staying on an old LDLib2. 2.2.2 ran in the full pack next to KotlinForForge 5.8.0 without errors |
| FancyMenu | The pack draws FancyMenu's customisation bar over every screen (`show_customization_overlay = true`); turned off for the screenshots. Worth checking in the shipped config |

## What each renderer costs

| | Native (LDLib2) | Web (WebGUI) |
|---|---|---|
| Fidelity to the website | Close, not identical: see below | Identical: it is the same page |
| Text | Minecraft's glyph pipeline: no anti-aliasing, so text under about 9 px is unreadable (node captions at fit zoom). Needs one font definition per pixel size and GUI scale | Browser text, as on the website |
| Locked icons | No greyscale: the item renderer ignores tint, a veil stands in for the 40 % opacity. Greyscale needs a shader | Greyscale and opacity from CSS |
| Item icons | Live item renderer: any item, no icon export | Pre-rendered PNG icons (the website's icon atlas) |
| Hover, tooltips, pan and zoom | Built in (LDLib2 events, `GraphView`) | Built in the page; mouse and keyboard forwarding to the page is not wired in this prototype |
| Code for one band | about 360 lines of Java and 50 lines of LSS, a second renderer to keep in step | about 120 lines of Java; the page is the website component |
| Runtime cost | 2.8 ms render-thread time per frame while open, nothing while closed | 190 MB of helper processes plus the in-JVM browser, all session; 15 % of a core while open, idle when closed |
| Install cost | none | 135 MB per platform, hosted and installed by the launcher; NixOS needs the libraries above |

## For the decision

Spec 018 said (a) wins "if its memory and frame cost stay small". Measured here:

- **For (a)**: same pixels as the website, almost no render-thread cost, opens as fast as native
  once warm, launcher pre-placement works, current Chromium. One renderer instead of two.
- **Against (a)**: about 190 MB of helper processes (+272 MB measured for the whole client), a
  15 % core while the page animates, a 135 MB download per platform, NixOS and possibly other Linux
  setups need system libraries, Windows and macOS unverified.
- **For (b)**: no download, no extra processes, live item rendering, works on any platform the
  game runs on.
- **Against (b)**: a second renderer that is visibly not the website (small text, greyscale,
  glow), more code per screen, and current LDLib2 requires a NeoForge upgrade.
- **(c)** (native graph, web later for wiki and shop) keeps (b)'s costs for the graph and adds (a)'s
  for the content screens.

## To verify by hand before deciding

- ~~Both screens on a real GPU, at 60 fps or more~~: done on 21 Nov 2026, see below. A mid-range player
  PC is still to be measured.
- Windows and macOS: WebGUI starts, antivirus does not flag `jcef_helper`, the pre-placed runtime is
  picked up.
- Memory on an 8 GB player machine with the full pack.
- GUI scales 2 and 4, and a 1080p window: native text sharpness.
- Clicking and scrolling in the web screen: wired on 21 Nov 2026, not yet checked by hand.

## Real GPU (21 Nov 2026)

Spec 018 work item 6b. Same band, same full pack (333 mods, NeoForge 21.1.172, `-Xmx10G`), on a real
display this time: RTX 5080 (NVIDIA 595.71.05) through Xwayland, Ryzen 9 9900X, NixOS. Vsync off, frame
cap 260, GUI scale 3, a new peaceful creative world. Run A: pack with LDLib2, without WebGUI. Run B: pack
with both. The WebGUI demo HUD and web main menu were off. Raw data:
[bench-gpu-2026-11-21.json](bench-gpu-2026-11-21.json). Scripts: `tools/stage-band/bench` in
[Mods#60](https://github.com/Arffornia/Arffornia_Mods/pull/60).

| In game, native (LDLib2), real GPU | In game, web (WebGUI), real GPU |
|---|---|
| ![Native on a real GPU](band-gpu-native.webp) | ![Web on a real GPU](band-gpu-web.webp) |

| Measure (mean, p95 in brackets) | 1280 × 720 | 1920 × 1080 |
|---|---|---|
| Frame time, no screen open (run A / run B) | 4.4 / 3.4 ms | 2.5 / 3.4 ms |
| Frame time, native screen open (run A / run B) | 7.4 / 8.5 ms | 5.0 / 5.5 ms |
| Render-thread time inside the native screen | 2.4 to 3.0 ms (3.8 to 5.2) | 1.8 to 1.9 ms (2.9 to 3.1) |
| Frame time, web screen open at 60 / 30 / 15 fps | 3.2 to 5.0 / 2.9 / 2.2 ms | 2.1 to 2.8 / 2.0 / 2.2 ms |
| Render-thread time inside the web screen | 0.02 to 0.09 ms (0.03 to 0.25) | 0.02 to 0.07 ms (0.03 to 0.33) |
| Open to first frame, warm (first open of the session) | native 16 to 45 ms, one 173 ms (144 to 272), web 3 to 5 ms (12 to 22) | native 15 to 26 ms (124 to 145), web 3 to 5 ms (3 to 20) |
| Browser CPU, screen open at 60 / 30 / 15 fps (one core) | 19 to 21 % / 10 % / 5 % | 16 to 20 % / 10 % / 5 % |
| Browser CPU, screen closed (warm, 1 fps) | 0.3 to 0.7 % | 0.4 to 1.0 % |
| Browser helper processes (7 or 8), PSS | 89 to 182 MB | 103 to 151 MB |
| Whole client in world, idle, PSS (run A / run B) | 13 230 to 13 273 / 13 278 to 13 413 MB | 13 086 / 13 278 to 13 358 MB |

How to read them:

- **The web screen costs no frame time.** With it open, frames take as long as with no screen at all;
  copying the browser texture takes under 0.1 ms. The native screen adds 2 to 3 ms of render thread per
  frame: a third of the budget at 144 Hz.
- **Browser CPU follows the page's frame rate.** WebGUI starts Chromium with `--disable-gpu` and
  `--disable-gpu-compositing`, so the page is painted on the CPU whatever the graphics card. The band's
  glow animation keeps it painting. 30 fps halves the cost, 15 fps quarters it; a page with nothing
  moving paints nothing.
- **Memory.** The helpers take 90 to 180 MB PSS and shrink after a few minutes. The whole client grows
  by 50 to 270 MB depending on the run, 1 to 2 % of 13.2 GB; heap noise between runs is of the same size.
- **Hidden when closed.** The JCEF bundled with WebGUI 2.0 does not expose `WasHidden`. Dropping the
  page to 1 fps on close already brings the browser to under 1 % of a core, so nothing more is needed.
- **Input.** Mouse moves, buttons and the wheel are forwarded to the page. Hover and click on the
  band are not checked by hand yet.

**Verdict: D2 (a) holds; the (c) fallback does not trigger.** Content screens run at 30 fps when the
page animates and 15 fps or less when it is static; the browser drops to 1 fps when the screen closes.

### Windows, to check later

- WebGUI starts, and finds the runtime the launcher pre-placed (`WMC_RUNTIME_DIR`, default
  `%LOCALAPPDATA%\wmc\runtime`) without downloading.
- Windows Defender and common antivirus do not flag or slow `jcef_helper.exe`.
- The same bench (`benchweb:60,30,15`, 720p and 1080p): frame time and browser CPU.
- Mouse and wheel positions with Windows display scaling at 125 % and 150 %.
- Minimising the game window and alt-tab with the web screen open.

## Alternatives looked at after the report

Asked on 21 Nov 2026: do lighter engines exist, and what do other mods do?

- Most mods draw their screens natively with HTML/CSS-like toolkits (Elementa, owo-ui, ModernUI,
  LabyMod LSS, LDLib2). Mods that embed a real Chromium (WebDisplays, WebGUI, LiquidBounce, Graphene)
  all pay the same 150 to 200 MB floor, which tuning does not remove.
- Ultralight (WebKit fork) uses 5 to 10 times less memory by its vendor's numbers, but it is
  proprietary, its free tier has no JS JIT and caps at 60 fps, and its Java bindings are archived
  or pre-release. RmlUi (MIT, C++) has no JS and needs our own binding. Blitz and Servo are too young.
- CEF tuning cuts CPU, not memory: a capped windowless frame rate, one browser and one origin for
  every screen, the browser hidden when the screen closes. Single-process mode is not supported.

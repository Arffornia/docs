# 018 · UI framework and one visual identity for game, website and launcher

| | |
|---|---|
| **Status** | Accepted with open points (D1 decided 8 Nov 2026; D2 after the prototype) |
| **Milestone** | M3 · Gameplay foundations |
| **Repos** | Arffornia_Assets (tokens), Arffornia_Mods (in-game UI), Arffornia_Website, Arffornia_Launcher_V.5.2, keycloak-theme-arffornia |
| **Related** | Initiative [#32](https://github.com/Arffornia/docs/issues/32) · [007](007-loading-and-title-screen.md) (title screen, D9 web menus) · [017](017-progression-model/spec.md) (the graph data) · Launcher [#89](https://github.com/Arffornia/Arffornia_Launcher_V.5.2/issues/89) |

## Summary

Brian wants premium-server interfaces: rich, consistent, and the **same progression graph on the
website and in game**, so players never feel they changed product. Today each surface has its own
look and the in-game screens are hand-drawn Java. This spec chooses:

1. **One set of design tokens** (colours, type, spacing, radii, motion) in Arffornia_Assets, generated
   into CSS for the web surfaces and into a Java/stylesheet file for the mod.
2. **The in-game UI technology**, after a state of the art of what exists for NeoForge 1.21.1.
3. **How the graph stays identical** on both sides.

Phase 1 ends with a prototype: one stage band of the current tree (spec 017 fixture) drawn in game
and on the web from the same model and the same tokens.

## What exists today

### Two identities

| Surface | Palette | Type | Source |
|---|---|---|---|
| Launcher | plum `#261d31` / `#3d2f4e`, near-black `#09070a`, lavender `#b3a7c2` / `#d1c4e9`, orange **`#ff7300`** | Montserrat | `Arffornia_Launcher_V.5.2/src` |
| Website | orange **`#ff7300`** on white and black, greys | Montserrat | `Arffornia_Website/resources/css/app.css` |
| In-game title screen (007, decided round 3) | the launcher's: plum, lavender, `#ff7300` | Montserrat, Chakra Petch wordmark | `Arffornia_Assets/ui/directions/g-honeycomb-r4.html` |
| Keycloak login | slate `#1f2830` / `#2a3640`, orange **`#e0703c`**, teal `#0f8f86` / `#2fd1c1` | Instrument Sans, Barlow Condensed, Chakra Petch, Monocraft | `keycloak-theme-arffornia/src/login/arffornia.css` |
| GitHub profile, docs site | orange `#e0703c`, teal `#4fd1c5` / `#0f8f86`, slate | — | `Arffornia/docs` `profile/`, `mkdocs.yml` |
| Machines (in the world) | gunmetal, signal-orange panels, amber heat, cyan power | — | `Arffornia_Assets/docs/DA.md`, machine skill |

Player-facing surfaces split in two: launcher, website and title screen share plum and `#ff7300`;
the login page, the only other one players see, uses the slate and `#e0703c` set built for the tools.
Two oranges 15 % apart read as a mistake when they sit next to each other (login → launcher).

### In-game UI code

The mod draws its screens by hand (`client/screen/`: `ProgressionGraphScreen`, `CrafterScreen`,
`SpaceElevatorScreen`). The graph screen and the website graph were built separately and drift (Brian: "ça marche,
mais ça marchouille", small bugs, no tests).

## State of the art (NeoForge 1.21.1, November 2026)

| Option | How | Strong | Weak |
|---|---|---|---|
| **Embedded Chromium**: [MCEF](https://modrinth.com/mod/mcef) + [WebGUI](https://modrinth.com/project/webgui) | A real browser draws HTML/CSS/JS into a texture; WebGUI makes full screens and HUD overlays from it | Same code as the website. Any web library (graph renderers, charts, animations). Paladium replaced its native menus this way ([former lead web developer](https://mathislebonniec.fr/projects/paladium)) | Downloads ~150 MB of Chromium on first launch from CinemaMod's server, which must be reachable. Chromium 116 (old). Antivirus false positives reported. macOS 11+, Linux glibc ≥ 2.31 (some builds 2.32); NixOS needs testing. Memory per client. No native item slots: inventories stay native |
| **Native, declarative**: [LDLib2](https://github.com/Low-Drag-MC/LDLib2) | XML layouts, LSS stylesheets (CSS-like), Taffy flexbox/grid layout, data binding, HUD overlays, an in-game UI debugger (F3) | Native speed, opens instantly, item slots and fluids, used by big mods (GregTech CEu authors). LGPL-3.0 | Java side only: the web graph is a second renderer |
| **Native, HTML-like**: [TesseraUI](https://modrinth.com/mod/tesseraui) | HTML templates and CSS parsed at runtime into native widgets; flexbox, grid, CSS variables, transitions, `{{ }}` / `v-for` / `v-if` binding, item slots, hot reload | Closest to web authoring without a browser. LGPL-3.0 | Young, one maintainer: higher abandonment risk. No JavaScript, so no web graph library |
| **owo-ui** (owo-lib, already in the pack) | Code-first and XML components | Already installed | Fabric-first design, smaller NeoForge use |
| **Hand-written Java** (today) | `GuiGraphics` calls | No dependency | Slow to build, no styling system, the source of today's drift |

Vanilla-client servers (no mods) use resource-pack tricks: custom font glyphs and core shaders. We
ship a mod, so we do not need them.

## Design

### 1 · Tokens: one source, generated everywhere

- `Arffornia_Assets/ui/tokens/arffornia.tokens.json` in the
  [W3C Design Tokens](https://www.designtokens.org/) format: colours (light and dark), type families
  and scale, spacing, radii, shadows, motion durations, tier accents (spec 003 bands).
- A small generator writes `tokens.css` (CSS custom properties) for the website, the launcher and
  the Keycloak theme, and `ArfTokens.java` + `arffornia.lss` for the mod. CI fails if a generated
  file is out of date.
- Fonts ship once from `Arffornia_Assets/ui/fonts` (all OFL), as woff2 for the web and as a
  resource-pack font for the game.

### 2 · In-game UI: native by default, web only where it pays

| Screen | Technology | Why |
|---|---|---|
| Machine GUIs, inventories, HUD, Noyau, Space Elevator | Native (LDLib2) | Item slots, instant open, no download |
| Title and loading screens | Native (spec 007) | Must open before anything else; the early window cannot host a browser |
| Progression graph, wiki pages, shop, news | **Decision D2** | Content screens, where "same as the website" matters most |

### 3 · One graph, two renderers that cannot drift

Whichever technology draws it, the graph is **computed once**:

- The layout (x, y of every milestone, stage bands) lives in the model (spec 017, `layout`), produced
  by the website editor or the graph tool, never recomputed by a client.
- Both renderers take the same snapshot JSON, the same tokens and the same icon atlas.
- A **visual regression test** renders the same stage band on both sides and compares screenshots
  (Playwright on the web; in game, a headless client screenshot harness like the one spec 007 built for
the early window).

With MCEF (D2 a), the in-game graph *is* the website component in a browser; with native (D2 b) it is
a second, thin renderer kept honest by the shared layout and the visual test.

### MCEF without the waiting (Brian, 8 Nov 2026)

The two costs that made MCEF look slow are avoidable:

- **No in-game download.** The launcher installs the Chromium binaries with the pack, hosted by
  Arffornia (provisioning files or GitHub releases), so the game never fetches them from
  CinemaMod's server. Players download them once, like any other pack file.
- **Instant screens.** The mod starts one browser when the client starts and keeps the graph, wiki
  and shop pages loaded off-screen. Opening a screen only shows a page that is already rendered.
  Paladium's menus open instantly, which is consistent with this approach.

What still has to be measured: memory of the resident browser on top of the full pack, frame time
while a page animates, and support on NixOS, macOS and Windows.

## Prototype (end of phase 1)

1. Tokens file and generator; website and Keycloak switched to the generated CSS (no visual change
   beyond the chosen palette).
2. One stage band of the current tree, from the spec 017 fixture:
   - web: a small TypeScript component, Playwright screenshot;
   - game: the chosen D2 technology, client screenshot.
3. Measured and written down: open time, memory, frame time with the full pack, first-launch download,
   NixOS, Windows and macOS behaviour.

## Decisions needed

| # | Question | Options | Recommendation |
|---|---|---|---|
| D1 | One player-facing identity | (a) the launcher's: plum, lavender, `#ff7300`, Montserrat + Chakra Petch for display, teal as the second accent; Keycloak moves to it; tools (GitHub, docs) keep slate and `#e0703c` | **Decided (Brian, 8 Nov 2026): (a)** |
| D2 | Graph, wiki, shop in game | (a) web through MCEF/WebGUI, the website's own component, Chromium installed by the launcher and kept warm; (b) native LDLib2 renderer from the shared layout; (c) native first, MCEF later for wiki and shop only | **Prototype both (a) and (b) on one stage band, then decide on numbers.** With the launcher prefetch and a warm browser, (a) is instant too; it wins if its memory and frame cost stay small, because it is one renderer instead of two |
| D3 | Native library | (a) LDLib2; (b) TesseraUI; (c) owo-ui | **(a)**: maintained by a large mod team, stylesheets + data binding + debugger, NeoForge 1.21.1 |
| D4 | Website front-end for the graph and editor | (a) a TypeScript component library shared by the website and the launcher (Vue, as the launcher); (b) Blade + vanilla JS as today | **(a)**: the launcher already uses Vue; one component library for the graph, the shop cards and the wiki |

## Work breakdown

| # | Title | Repo | Acceptance criteria | Effort |
|---|---|---|---|---|
| 1 | Tokens file and generator (CSS, Java, LSS) | Assets | Generated files checked in CI; light and dark | S |
| 2 | Website and Keycloak on the generated tokens | Website, keycloak theme | Visual diff only where D1 changes colours | S |
| 3 | Web stage-band component from the 017 snapshot | Website (or a shared UI package) | Playwright screenshot test | M |
| 4 | In-game stage band, native (LDLib2) | Mods | Client screenshot test; open time and frame time measured | M |
| 5 | In-game stage band, MCEF/WebGUI, browser kept warm | Mods | Same screenshot; open time, memory, frame time, NixOS/macOS/Windows notes | M |
| 5b | Launcher installs the Chromium binaries with the pack | Launcher, Provisioning | No download at game start; binaries hosted by Arffornia | S |
| 6 | Report and D2 decision | docs | Numbers from 4 and 5, Brian's pick | S |
| 7 | Launcher on the generated tokens | Launcher | Part of #89 | S |

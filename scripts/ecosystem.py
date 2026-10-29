#!/usr/bin/env python3
"""Render the Arffornia ecosystem map (profile/ecosystem.{light,dark}.svg).

A hub (the Arffornia brand) framed by three compartments of projects, standing on MaaS,
the platform that hosts them. Everything is driven by the data below: add a project to
PROJECTS (and, if needed, a group to GROUPS) and run

    python3 scripts/ecosystem.py profile && cp profile/ecosystem.*.svg docs/assets/

Text is shaped with HarfBuzz (kerning) and converted to paths with fontTools, because GitHub
strips external fonts from SVG images. Fonts (OFL, in profile/fonts): Archivo for text,
JetBrains Mono for repository names, Chakra Petch for the wordmark (same as the banner).
Requires: pip install fonttools uharfbuzz
"""
import os, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

# --------------------------------------------------------------------------- content
ORG = "Arffornia"  # repos written without an owner live in this organisation

# slot: "top" (row above the hub), "left" or "right" (columns beside the hub)
GROUPS = {
    "play": dict(label="Play", tag="what players touch", slot="top"),
    "game": dict(label="Game", tag="the modded server", slot="left"),
    "tools": dict(label="Toolkit", tag="built from scratch", slot="right"),
}

# (group, display name, repo(s), one-line benefit[, chips])
PROJECTS = [
    ("play", "Arffornia Launcher", "Arffornia_Launcher_V.5.2", "Microsoft login, Java, modpack and shaders in one click"),
    ("play", "Arffornia Website", "Arffornia_Website", "Accounts, shop, votes, progression editor and public API"),
    ("play", "Keycloak theme", "keycloak-theme-arffornia", "The sign-in pages, in Arffornia colours"),
    ("game", "Arffornia Mod", "Arffornia_Mods", "Progression graph, Space Elevator, Crafter, machines to come"),
    ("game", "Arffornia Provisioning", "Arffornia_Provisioning", "Around 330 mods, defined once and kept up to date"),
    ("game", "Arffornia Proxy", "Arffornia_Proxy", "Votes from server lists, rewarded in game"),
    ("tools", "Nexus libraries", "Nexus_*", "The launcher's TypeScript stack", ["Mods", "Java", "Logger", "Saver"]),
    ("tools", "Arffornia Docs + Noodle", "docs · TheGostsniperfr/Noodle", "Architecture docs, with diagrams written as code"),
    ("tools", "Agent Kit", "agent-kit", "The AI agent harness the project is built with"),
]

HUB = dict(lines=["One account.", "One modpack.", "One network."], foot="Modded Minecraft · NeoForge 1.21.1")

# MaaS: the platform every project above runs on. (benefit, planned)
MAAS = dict(kicker="MaaS", name="Minecraft as a Service", repo="TheGostsniperfr/infra",
            pitch="Provision a Minecraft server in a few clicks.",
            points=[("One address for every server", False), ("The whole network declared in Git", False),
                    ("A preview server for every change", True)])

# --------------------------------------------------------------------------- design tokens
THEMES = {
    "light": dict(
        canvas="#f3f5f6", card="#ffffff", line="#dbe2e6", grid="#efd6c6",
        ink="#141b20", body="#3b4852", muted="#5f6d77",
        hub="#fbeee6", hub_ink="#8f3b14", brand=("#c25a24", "#8f3b14"),
        accent={"play": "#c25a24", "game": "#0e7a72", "tools": "#46596a"},
        accent_txt={"play": "#a8461a", "game": "#0e7a72", "tools": "#46596a"},
        chip="#eef2f4", chip_ink="#3b4852",
        base="#172026", base_line="#2a3741", on_base="#eef2f4", on_base_muted="#a9b6be", ember="#f0874a"),
    "dark": dict(
        canvas="#0e1418", card="#151d23", line="#26323b", grid="#3a2a20",
        ink="#e8edf0", body="#b3c0c8", muted="#8d9ca6",
        hub="#1d1915", hub_ink="#f0a070", brand=("#f39a5f", "#e0703c"),
        accent={"play": "#e0703c", "game": "#3fb7ab", "tools": "#8ea3b4"},
        accent_txt={"play": "#f0915a", "game": "#4fc4b8", "tools": "#9fb2c2"},
        chip="#1e2830", chip_ink="#b3c0c8",
        base="#e8edf0", base_line="#cdd6dc", on_base="#141b20", on_base_muted="#4f5d67", ember="#b04d1c"),
}

# grid: 1080 wide, 40 margin, 20 gutter
W, M, G = 1080, 40, 20
COL = (W - 2 * M - 2 * G) / 3
PAD = 24

# --------------------------------------------------------------------------- typography
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile", "fonts")
FACES = {"display": "Archivo-SemiExpandedBold.ttf", "semi": "Archivo-SemiExpandedSemiBold.ttf",
         "medium": "Archivo-Medium.ttf", "text": "Archivo-Regular.ttf",
         "mono": "JetBrainsMono-Regular.ttf", "monomed": "JetBrainsMono-Medium.ttf", "brand": "ChakraPetch-Bold.ttf"}
_fonts = {}


def _font(face):
    if face not in _fonts:
        path = os.path.join(FONT_DIR, FACES[face]); tt = TTFont(path)
        _fonts[face] = (hb.Font(hb.Face(hb.Blob.from_file_path(path))), tt.getGlyphSet(), tt["head"].unitsPerEm, tt.getGlyphOrder())
    return _fonts[face]


def _shape(txt, face, size, tracking):
    hbf, _, upm, order = _font(face)
    buf = hb.Buffer(); buf.add_str(txt); buf.guess_segment_properties()
    hb.shape(hbf, buf, {"kern": True, "liga": True})
    s = size / upm; out = []; x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((order[info.codepoint], x + pos.x_offset * s, -pos.y_offset * s))
        x += pos.x_advance * s + tracking
    return out, s, (x - tracking if out else 0.0)


def width(txt, face, size, tracking=0.0):
    return _shape(txt, face, size, tracking)[2]


_defs = {}  # (face, glyph) -> (id, path in font units); emitted once in <defs>, reused with <use>


def _glyph(face, name):
    key = (face, name)
    if key not in _defs:
        gs = _font(face)[1]; pen = SVGPathPen(gs, ntos=lambda v: str(round(v)))
        gs[name].draw(pen)
        _defs[key] = (f"g{len(_defs)}", pen.getCommands())
    return _defs[key][0]


def text(txt, face, size, x, y, fill, anchor="start", tracking=0.0):
    """Text as reused glyph outlines (paths), baseline at y."""
    glyphs, s, w = _shape(txt, face, size, tracking)
    x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
    gs = _font(face)[1]; uses = []
    for name, gx, gy in glyphs:
        if not gs[name].width or name in ("space", "uni00A0"):
            continue
        uses.append(f'<use href="#{_glyph(face, name)}" transform="translate({x + gx:.1f} {y + gy:.1f}) scale({s:.5f} -{s:.5f})"/>')
    return f'<g fill="{fill}">{"".join(uses)}</g>'


def glyph_defs():
    return "<defs>" + "".join(f'<path id="{i}" d="{d}"/>' for i, d in _defs.values()) + "</defs>"


def wrap(txt, face, size, maxw):
    lines, cur = [], ""
    for word in txt.split():
        t = f"{cur} {word}".strip()
        if cur and width(t, face, size) > maxw:
            lines.append(cur); cur = word
        else:
            cur = t
    return lines + ([cur] if cur else [])


# --------------------------------------------------------------------------- components
NAME, REPO, BODY, LH = 22, 14.5, 17, 23  # type scale


def group_label(c, key, x, y):
    g = GROUPS[key]; lab = g["label"].upper()
    lw = width(lab, "monomed", 14, 2.4)
    return (f'<rect x="{x}" y="{y - 10}" width="10" height="10" rx="1" fill="{c["accent"][key]}"/>'
            + text(lab, "monomed", 14, x + 20, y, c["ink"], tracking=2.4)
            + text(g["tag"], "text", 16, x + 20 + lw + 12, y, c["muted"]))


def card_height(p, w):
    lines = len(wrap(p[3], "text", BODY, w - 2 * PAD))
    return 92 + lines * LH + (40 if len(p) > 4 else 0) + 12


def card(c, p, x, y, w, h):
    key, name, repo, blurb = p[:4]
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c["card"]}" stroke="{c["line"]}"/>',
         f'<rect x="{x + PAD}" y="{y}" width="24" height="3" fill="{c["accent"][key]}"/>',
         text(name, "display", min(NAME, NAME * (w - 2 * PAD) / width(name, "display", NAME)), x + PAD, y + 44, c["ink"]),
         text(repo, "mono", REPO, x + PAD, y + 70, c["accent_txt"][key])]
    ty = y + 104
    for ln in wrap(blurb, "text", BODY, w - 2 * PAD):
        o.append(text(ln, "text", BODY, x + PAD, ty, c["body"])); ty += LH
    if len(p) > 4:
        cx = x + PAD; cy = ty - 6
        for chip in p[4]:
            cw = width(chip, "monomed", 13.5) + 20
            o.append(f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="26" rx="6" fill="{c["chip"]}"/>')
            o.append(text(chip, "monomed", 13.5, cx + 10, cy + 18, c["chip_ink"]))
            cx += cw + 8
    return "".join(o)


def iso_grid(c, x, y, w, h, step=32):
    """Faint isometric grid (the banner's motif), clipped to the hub."""
    d = []; k = 0.57735  # tan(30)
    for i in range(-int(h / k / step) - 2, int(w / step) + 2):
        x0 = x + i * step
        d.append(f"M{x0:.1f} {y}l{h / k:.1f} {h:.1f}")
    for i in range(0, int((w + h / k) / step) + 2):
        x0 = x + i * step
        d.append(f"M{x0:.1f} {y}l{-h / k:.1f} {h:.1f}")
    return (f'<defs><clipPath id="hubclip"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16"/></clipPath>'
            f'<radialGradient id="fade" cx=".5" cy=".42" r=".75"><stop offset=".25" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#fff"/></radialGradient>'
            f'<mask id="hubmask"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#fade)"/></mask></defs>'
            f'<g clip-path="url(#hubclip)"><path d="{"".join(d)}" stroke="{c["grid"]}" stroke-width="1" mask="url(#hubmask)"/></g>')


def hub(c, x, y, w, h):
    cx = x + w / 2
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{c["hub"]}"/>', iso_grid(c, x, y, w, h),
         f'<defs><linearGradient id="brand" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c["brand"][0]}"/>'
         f'<stop offset="1" stop-color="{c["brand"][1]}"/></linearGradient></defs>']
    n = len(HUB["lines"]); block = 30 + 20 + 38 + (n - 1) * 30  # cap height .. last baseline
    ty = y + (h - 40 - block) / 2 + 30
    o.append(text("ARFFORNIA", "brand", 42, cx, ty, "url(#brand)", anchor="middle", tracking=2))
    ty += 20
    o.append(f'<rect x="{cx - 16}" y="{ty}" width="32" height="2" fill="{c["brand"][0]}"/>')
    for i, ln in enumerate(HUB["lines"]):
        o.append(text(ln, "semi", 19, cx, ty + 38 + i * 30, c["hub_ink"], anchor="middle"))
    o.append(text(HUB["foot"], "mono", 13, cx, y + h - 24, c["muted"], anchor="middle"))
    return "".join(o)


def maas(c, x, y, w):
    h = 200; o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{c["base"]}"/>']
    lx = x + 36
    o.append(text(MAAS["kicker"], "display", 56, lx, y + 76, c["ember"]))
    o.append(text(MAAS["name"], "display", 24, lx, y + 112, c["on_base"]))
    o.append(text(MAAS["pitch"], "text", 18, lx, y + 140, c["on_base_muted"]))
    o.append(text(MAAS["repo"], "mono", REPO, lx, y + h - 28, c["ember"]))
    px = x + w / 2 + 40; pw = x + w - 36 - px
    n = len(MAAS["points"]); rh = (h - 48) / n
    for i, (pt, planned) in enumerate(MAAS["points"]):
        ry = y + 24 + i * rh
        if i: o.append(f'<path d="M{px} {ry:.1f}h{pw:.1f}" stroke="{c["base_line"]}"/>')
        by = ry + rh / 2
        o.append(f'<rect x="{px + 1}" y="{by - 6:.1f}" width="10" height="10" rx="1" '
                 + (f'fill="none" stroke="{c["ember"]}" stroke-width="2"/>' if planned else f'fill="{c["ember"]}"/>'))
        o.append(text(pt, "medium", 18, px + 26, by + 5, c["on_base"]))
        if planned:
            o.append(text("PLANNED", "mono", 12, px + pw, by + 4, c["on_base_muted"], anchor="end", tracking=1.6))
    return "".join(o), h


def build(theme):
    c = THEMES[theme]; o = []; _defs.clear()
    by_slot = {s: [p for p in PROJECTS if GROUPS[p[0]]["slot"] == s] for s in ("top", "left", "right")}
    key_of = {s: next(k for k, g in GROUPS.items() if g["slot"] == s) for s in ("top", "left", "right")}
    y = M + 22
    # top row: cards share the full width
    top = by_slot["top"]; tw = (W - 2 * M - (len(top) - 1) * G) / len(top)
    o.append(group_label(c, key_of["top"], M, y)); y += 20
    th = max(card_height(p, tw) for p in top)
    for i, p in enumerate(top):
        o.append(card(c, p, M + i * (tw + G), y, tw, th))
    y += th + 44
    # middle: left column, hub, right column
    o.append(group_label(c, key_of["left"], M, y)); o.append(group_label(c, key_of["right"], M + 2 * (COL + G), y))
    y += 20
    ch = max(card_height(p, COL) for p in by_slot["left"] + by_slot["right"])
    stack = max(len(by_slot["left"]), len(by_slot["right"])) * (ch + 16) - 16
    for col, slot in ((0, "left"), (2, "right")):
        for j, p in enumerate(by_slot[slot]):
            o.append(card(c, p, M + col * (COL + G), y + j * (ch + 16), COL, ch))
    o.append(hub(c, M + COL + G, y - 32, COL, stack + 32))  # hub reaches up to the label line
    y += stack + 20
    band, bh = maas(c, M, y, W - 2 * M)
    o.append(band); y += bh + 20
    o.append(text(f"Repositories on github.com/{ORG} unless an owner is shown", "text", 14, M, y + 8, c["muted"]))
    H = int(y + 8 + M - 8)
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="The Arffornia ecosystem: Play (launcher, website, sign-in theme), Game (mod, provisioning, proxy) '
            f'and Toolkit (Nexus libraries, docs and Noodle, agent kit), all running on MaaS, Minecraft as a Service.">'
            f'<rect width="{W}" height="{H}" rx="20" fill="{c["canvas"]}"/>')
    return head + glyph_defs() + "".join(o) + "</svg>"


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "profile"
    for t in THEMES:
        with open(os.path.join(out, f"ecosystem.{t}.svg"), "w") as f:
            f.write(build(t))
    print("ok")

#!/usr/bin/env python3
"""Render the Arffornia ecosystem map (profile/ecosystem.{light,dark}.svg).

The Arffornia hub, fed by three groups of projects (Play above, Game left, Toolkit right),
standing on MaaS, the platform it runs on. Everything is driven by the data below: add a
project to PROJECTS (and, if needed, a group to GROUPS) and run

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

# slot: "top" (row above the hub), "left" (full cards beside the hub), "right" (compact list)
GROUPS = {
    "play": dict(label="Play", tag="what players use", slot="top"),
    "game": dict(label="Game", tag="the server itself", slot="left"),
    "tools": dict(label="Toolkit", tag="how it's built", slot="right"),
}

# (group, title, repo slugs, one short line; **bold** marks a figure)
PROJECTS = [
    ("play", "Launcher", ["Arffornia_Launcher_V.5.2"], "Sign in, install, play."),
    ("play", "Website", ["Arffornia_Website"], "Accounts, shop, votes, public API"),
    ("play", "Sign-in", ["keycloak-theme-arffornia"], "Arffornia account pages"),
    ("game", "Mod", ["Arffornia_Mods"], "Milestones, machines and the Space Elevator"),
    ("game", "Provisioning", ["Arffornia_Provisioning"], "**330 mods,** declared once, always current"),
    ("game", "Votes", ["Arffornia_Proxy"], "Server-list votes, rewarded in game"),
    ("tools", "Nexus libraries", ["Nexus_*"], "The launcher's TypeScript libraries"),
    ("tools", "Docs + Noodle", ["docs", "TheGostsniperfr/Noodle"], "Architecture, diagrams as code"),
    ("tools", "Agent Kit", ["agent-kit"], "The AI tooling behind the codebase"),
]

HUB = dict(line="A Satisfactory-style modded server.")

# MaaS: the platform the whole network runs on. (benefit, planned)
MAAS = dict(word="MaaS", name="Minecraft as a Service", repo="TheGostsniperfr/infra",
            pitch="Provision a Minecraft server in a few clicks.",
            points=[("NeoForge 1.21.1 servers, on demand", False), ("The whole network declared in Git", False),
                    ("A preview server for every change", True)])

FOOTER = f"Repos under github.com/{ORG} unless noted"

# --------------------------------------------------------------------------- design tokens
# Orange and teal come from the banner (profile_banner.py); text shades are darkened for AA.
THEMES = {
    "light": dict(
        canvas="#f3f5f6", card="#ffffff", line="#d5dde2", panel="#e9edf0", panel_line="#d5dde2",
        ink="#141b20", body="#3b4852", muted="#5f6d77", verb="#5f6d77",
        hub="#f7f8fa", hub_line="#d5dde2", grid="#46606f", grid_o=".10", hub_ink="#374151",
        brand=("#c25a24", "#8f3b14"),
        accent={"play": "#c25a24", "game": "#0f8f86", "tools": "#46596a"},
        accent_txt={"play": "#a8461a", "game": "#0b746c", "tools": "#46596a"},
        cube=("#e8874e", "#b4572a", "#86391a"), block=("#e6ecf0", "#c9d3d9", "#adbac3"),
        base="#172026", lip="#0f1419", lip_edge="none", base_line="#2a3741",
        on_base="#eef2f4", on_base_muted="#a9b6be", ember="#f0874a", spine="#c25a24"),
    "dark": dict(
        canvas="#0e1418", card="#151d23", line="#2a323c", panel="#121a20", panel_line="#2a323c",
        ink="#e8edf0", body="#b3c0c8", muted="#8d9ca6", verb="#8d9ca6",
        hub="#11161c", hub_line="#2a323c", grid="#8fb4c8", grid_o=".09", hub_ink="#d4dce1",
        brand=("#f39a5f", "#e0703c"),
        accent={"play": "#e0703c", "game": "#4fd1c5", "tools": "#8ea3b4"},
        accent_txt={"play": "#f0915a", "game": "#4fd1c5", "tools": "#9fb2c2"},
        cube=("#f09a62", "#c4622f", "#8f421c"), block=("#3d4d58", "#2b3943", "#1f2a31"),
        base="#0a0d12", lip="#151c23", lip_edge="#f0894a", base_line="#1f2830",
        on_base="#e5e7eb", on_base_muted="#a9b6be", ember="#f0894a", spine="#e0703c"),
}

# Grid (viewBox units; 1 unit = 0.74 px at README width, 0.32 px on a 360 px phone).
W, M = 1120, 30
GUT = 32                     # between the hub and the side columns
SIDE = 300                   # side column width
HUBW = W - 2 * M - 2 * SIDE - 2 * GUT
PAD = 20                     # card padding
# Type scale, sized so a 360 px phone still gets 7 to 10 px text.
TITLE, SLUG, BODY, LH, LABEL = 30, 18, 22, 30, 16

# --------------------------------------------------------------------------- typography
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile", "fonts")
FACES = {"display": "Archivo-SemiExpandedBold.ttf", "semi": "Archivo-SemiExpandedSemiBold.ttf",
         "medium": "Archivo-Medium.ttf", "text": "Archivo-Regular.ttf",
         "mono": "JetBrainsMono-Regular.ttf", "monomed": "JetBrainsMono-Medium.ttf", "brand": "ChakraPetch-Bold.ttf", "brandmed": "ChakraPetch-Medium.ttf"}
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
def _words(txt):
    """Split '**bold** rest' into (word, face) pairs."""
    out, bold = [], False
    for w in txt.split():
        start = w.startswith("**"); w = w[2:] if start else w
        bold = bold or start
        end = w.endswith("**"); w = w[:-2] if end else w
        out.append((w, "display" if bold else "text"))
        if end: bold = False
    return out


def rich_lines(txt, size, maxw):
    """Wrap into as few lines as fit, then balance them so no line is a lone word."""
    sp = width("a a", "text", size) - width("aa", "text", size)
    words = [(w, f, width(w, f, size)) for w, f in _words(txt)]
    lw = lambda ws: sum(x[2] for x in ws) + sp * (len(ws) - 1)
    if lw(words) <= maxw:
        return [words], sp
    best = None
    for i in range(1, len(words)):  # best two-line split: both fit, widest line smallest
        a, b = words[:i], words[i:]
        if lw(a) <= maxw and lw(b) <= maxw and (best is None or max(lw(a), lw(b)) < best[0]):
            best = (max(lw(a), lw(b)), [a, b])
    if best:
        return best[1], sp
    lines, cur = [], []
    for wd in words:
        if cur and lw(cur + [wd]) > maxw:
            lines.append(cur); cur = []
        cur.append(wd)
    return lines + [cur], sp


def rich(txt, size, x, y, maxw, fill, strong):
    lines, sp = rich_lines(txt, size, maxw); o = []
    for i, ln in enumerate(lines):
        cx = x
        for w, f, ww in ln:
            o.append(text(w, f, size, cx, y + i * LH, strong if f == "display" else fill)); cx += ww + sp
    return "".join(o), len(lines)


def fit(txt, face, size, maxw):
    return min(size, size * maxw / width(txt, face, size))


def diamond(x, y, fill, r=5.7):
    return f'<rect x="{x - r / 2:.1f}" y="{y - r / 2:.1f}" width="{r:.1f}" height="{r:.1f}" transform="rotate(45 {x:.1f} {y:.1f})" fill="{fill}"/>'


def group_label(c, key, x, y):
    g = GROUPS[key]; lab = g["label"].upper(); tr = LABEL * .12
    lw = width(lab, "brand", LABEL, tr)
    return (f'<rect x="{x}" y="{y - 11}" width="11" height="11" rx="1" fill="{c["accent"][key]}"/>'
            + text(lab, "brand", LABEL, x + 21, y, c["ink"], tracking=tr)
            + text(g["tag"], "text", LABEL, x + 21 + lw + 12, y, c["muted"]))


def card_height(p, w):
    return 142 + LH * (len(rich_lines(p[3], BODY, w - 2 * PAD)[0]) - 1)


def card(c, p, x, y, w, h, strong=False):
    key, title, slugs, line = p
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{c["card"]}" stroke="{c["line"]}"/>']
    if strong:  # the game itself gets an inner left edge in its colour
        o.append(f'<rect x="{x + 1}" y="{y + 14}" width="3" height="{h - 28}" rx="1.5" fill="{c["accent"][key]}"/>')
    o.append(text(title, "display", fit(title, "display", TITLE, w - 2 * PAD), x + PAD, y + 50, c["ink"]))
    o.append(text(" · ".join(slugs), "mono", fit(" · ".join(slugs), "mono", SLUG, w - 2 * PAD), x + PAD, y + 80, c["accent_txt"][key]))
    o.append(rich(line, BODY, x + PAD, y + 116, w - 2 * PAD, c["body"], c["ink"])[0])
    return "".join(o)


def compact_panel(c, items, x, y, w, h):
    """Toolkit: no cards, on a recessed panel; title, repos and one muted line per item."""
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{c["panel"]}"/>']
    rh = h / len(items)
    for i, (key, title, slugs, line) in enumerate(items):
        ry = y + i * rh
        if i: o.append(f'<path d="M{x + PAD} {ry:.1f}h{w - 2 * PAD}" stroke="{c["panel_line"]}"/>')
        n = len(rich_lines(line, BODY - 2, w - 2 * PAD)[0])
        block = 20 + 28 * len(slugs) + 12 + 26 * n
        by = ry + (rh - block) / 2 + 20
        o.append(text(title, "semi", fit(title, "semi", 26, w - 2 * PAD), x + PAD, by, c["body"]))
        for j, sl in enumerate(slugs):
            o.append(text(sl, "mono", fit(sl, "mono", SLUG, w - 2 * PAD), x + PAD, by + 28 + j * 26, c["accent_txt"][key]))
        ly = by + 28 * len(slugs) + 34
        lines, sp = rich_lines(line, BODY - 2, w - 2 * PAD)
        for k, ln in enumerate(lines):
            o.append(text(" ".join(t[0] for t in ln), "text", BODY - 2, x + PAD, ly + k * 26, c["muted"]))
    return "".join(o)


def crafter(theme, cx, top, height):
    """The Arffornia logo: the crafter machine from the banner, same geometry and colours,
    reused from profile_banner.py and scaled into place. Its window glows and its vents blink
    like on the banner (CSS, stopped under prefers-reduced-motion)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import profile_banner as pb
    b = pb.THEMES[theme]
    parts = [pb.box(-1.2, -.6, 0, 3.4, 3.2, 2.6, b["m_top"], b["m_left"], b["m_right"]),
             pb.box(-.4, .2, 2.6, 1.8, 1.6, .5, b["m_top"], b["m_left"], b["m_right"])]
    hx, hy = pb.iso(.5, 2.6, 1.4)
    parts.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="70" fill="url(#crafthalo)" class="glow"/>')
    parts.append(pb.poly([pb.iso(-.6, 2.6, .8), pb.iso(1.6, 2.6, .8), pb.iso(1.6, 2.6, 2.0), pb.iso(-.6, 2.6, 2.0)], b["glow"], 'class="glow"'))
    for k in range(3):
        vx, vy = pb.iso(2.2, -.2 + k * .7, 1.8)
        parts.append(f'<rect x="{vx - 3:.1f}" y="{vy:.1f}" width="6" height="14" rx="2" fill="{b["teal"]}" class="beacon" style="animation-delay:{k * .4:.1f}s"/>')
    pts = [pb.iso(a, bb, z) for a in (-1.2, 2.2) for bb in (-.6, 2.6) for z in (0, 3.1)]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    sc = height / (y1 - y0)
    tx, ty = cx - (x0 + x1) / 2 * sc, top - y0 * sc
    return (f'<defs><radialGradient id="crafthalo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{b["glow"]}" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="{b["glow"]}" stop-opacity="0"/></radialGradient></defs>'
            f'<g transform="translate({tx:.1f} {ty:.1f}) scale({sc:.4f})">{"".join(parts)}</g>')


def hub(c, theme, x, y, w, h):
    cx = x + w / 2; o = []
    # the banner's isometric floor grid, fading out behind the wordmark
    d = []; step = 34; t = 0.57735
    for i in range(-int(h / t / step) - 2, int(w / step) + 2):
        d.append(f"M{x + i * step:.1f} {y}l{h / t:.1f} {h:.1f}")
    for i in range(0, int((w + h / t) / step) + 2):
        d.append(f"M{x + i * step:.1f} {y}l{-h / t:.1f} {h:.1f}")
    o.append(f'<defs><clipPath id="hubclip"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16"/></clipPath>'
             f'<radialGradient id="fade" cx=".5" cy=".5" r=".7"><stop offset=".3" stop-color="#fff" stop-opacity=".25"/>'
             f'<stop offset="1" stop-color="#fff"/></radialGradient>'
             f'<mask id="hubmask"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#fade)"/></mask>'
             f'<linearGradient id="brand" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c["brand"][0]}"/>'
             f'<stop offset="1" stop-color="{c["brand"][1]}"/></linearGradient></defs>')
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{c["hub"]}" stroke="{c["hub_line"]}"/>')
    o.append(f'<g clip-path="url(#hubclip)"><path d="{"".join(d)}" stroke="{c["grid"]}" stroke-opacity="{c["grid_o"]}" '
             f'stroke-width="1" fill="none" mask="url(#hubmask)"/></g>')
    # content block: crafter logo (150) + 30 + wordmark cap (46) + 22 + rule + 40 + line
    block = 150 + 30 + 46 + 22 + 40
    top = y + (h - block) / 2
    o.append(crafter(theme, cx, top, 150))
    wy = top + 150 + 30 + 46
    o.append(text("ARFFORNIA", "brand", fit("ARFFORNIA", "brand", 64, w - 40), cx, wy, "url(#brand)", anchor="middle", tracking=1.5))
    o.append(f'<rect x="{cx - 16}" y="{wy + 20}" width="32" height="2" fill="{c["brand"][0]}"/>')
    o.append(text(HUB["line"], "medium", fit(HUB["line"], "medium", BODY, w - 40), cx, wy + 22 + 40, c["hub_ink"], anchor="middle"))
    return "".join(o)


def maas(c, x, y, w):
    h, e = 214, 10  # height, isometric edge depth
    o = [f'<rect x="{x}" y="{y + e}" width="{w - e}" height="{h - e}" fill="{c["base"]}"/>',
         f'<polygon points="{x},{y + e} {x + e},{y} {x + w},{y} {x + w - e},{y + e}" fill="{c["lip"]}"/>',
         f'<polygon points="{x + w - e},{y + e} {x + w},{y} {x + w},{y + h - e} {x + w - e},{y + h}" fill="{c["lip"]}"/>']
    if c["lip_edge"] != "none":
        o.append(f'<path d="M{x} {y + e}h{w - e}" stroke="{c["lip_edge"]}" stroke-opacity=".7"/>')
    lx = x + 36
    o.append(text(MAAS["word"], "display", 56, lx, y + 84, c["ember"]))
    ww = width(MAAS["word"], "display", 56)
    o.append(text(MAAS["name"], "display", 26, lx + ww + 18, y + 84, c["on_base"]))
    o.append(text(MAAS["pitch"], "text", BODY, lx, y + 126, c["on_base_muted"]))
    o.append(text(MAAS["repo"], "mono", SLUG, lx, y + h - 34, c["ember"]))
    px = x + w * .56; pw = x + w - e - 36 - px
    n = len(MAAS["points"]); top = y + e + 22; rh = (h - e - 44) / n
    for i, (pt, planned) in enumerate(MAAS["points"]):
        ry = top + i * rh
        if i: o.append(f'<path d="M{px:.1f} {ry:.1f}h{pw:.1f}" stroke="{c["base_line"]}"/>')
        by = ry + rh / 2
        o.append(f'<rect x="{px + 1:.1f}" y="{by - 6:.1f}" width="11" height="11" rx="1" '
                 + (f'fill="none" stroke="{c["ember"]}" stroke-width="2"/>' if planned else f'fill="{c["ember"]}"/>'))
        o.append(text(pt, "medium", fit(pt, "medium", BODY, pw - 28 - (90 if planned else 0)), px + 28, by + 7, c["on_base"]))
        if planned:
            o.append(text("PLANNED", "mono", 14, px + pw, by + 5, c["on_base_muted"], anchor="end", tracking=1.6))
    return "".join(o), h


def connector(c, x1, y1, x2, y2, color, width_=2, start=True):
    o = [f'<path d="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}" stroke="{color}" stroke-width="{width_}"/>']
    if start: o.append(diamond(x1, y1, color))
    o.append(diamond(x2, y2, color))
    return "".join(o)


def build(theme):
    c = THEMES[theme]; o = []; _defs.clear()
    slot = {s: [p for p in PROJECTS if GROUPS[p[0]]["slot"] == s] for s in ("top", "left", "right")}
    key_of = {s: next(k for k, g in GROUPS.items() if g["slot"] == s) for s in ("top", "left", "right")}
    cols = [(M, SIDE), (M + SIDE + GUT, HUBW), (M + SIDE + GUT + HUBW + GUT, SIDE)]
    hub_x, hub_cx = cols[1][0], cols[1][0] + HUBW / 2

    y = M + 26
    o.append(group_label(c, key_of["top"], M, y)); y += 18
    top = slot["top"]
    if len(top) == 3:  # three player tools sit on the three columns
        boxes = cols
    else:
        tw = (W - 2 * M - (len(top) - 1) * GUT) / len(top); boxes = [(M + i * (tw + GUT), tw) for i in range(len(top))]
    th = max(card_height(p, bw) for p, (bx, bw) in zip(top, boxes))
    for p, (bx, bw) in zip(top, boxes):
        o.append(card(c, p, bx, y, bw, th))
    play_bottom = y + th
    y = play_bottom + 64
    o.append(group_label(c, key_of["left"], M, y)); o.append(group_label(c, key_of["right"], cols[2][0], y))
    y += 18
    ch = max(card_height(p, SIDE) for p in slot["left"])
    stack = len(slot["left"]) * (ch + 16) - 16
    for j, p in enumerate(slot["left"]):
        o.append(card(c, p, M, y + j * (ch + 16), SIDE, ch, strong=True))
    o.append(compact_panel(c, slot["right"], cols[2][0], y, SIDE, stack))
    spine = 72  # room under the hub for the "runs on" connector
    hub_h = stack + 8 - spine
    o.append(hub(c, theme, hub_x, y, HUBW, hub_h))

    # connectors: each group plugs into the hub, the hub plugs into MaaS
    mid = y + (len(slot["left"]) // 2) * (ch + 16) + ch / 2
    mid = min(mid, y + hub_h - 40)
    o.append(connector(c, hub_cx, play_bottom, hub_cx, y, c["accent"][key_of["top"]]))
    o.append(text("plays on", "mono", LABEL, hub_cx + 14, (play_bottom + y) / 2 + 5, c["verb"]))
    o.append(connector(c, M + SIDE, mid, hub_x, mid, c["accent"][key_of["left"]], start=False))
    o.append(connector(c, cols[2][0], mid, hub_x + HUBW, mid, c["accent"][key_of["right"]], start=False))
    base_y = y + stack + 8
    o.append(f'<path d="M{hub_cx} {y + hub_h}V{base_y}" stroke="{c["spine"]}" stroke-width="3"/>')
    o.append(f'<path class="belt" d="M{hub_cx} {y + hub_h}V{base_y}" stroke="{c["canvas"]}" stroke-width="1" stroke-dasharray="3 9"/>')
    o.append(diamond(hub_cx, y + hub_h, c["spine"], 8) + diamond(hub_cx, base_y - 1, c["spine"], 8))
    o.append(text("runs on", "mono", LABEL, hub_cx + 14, y + hub_h + spine / 2 + 6, c["verb"]))

    band, bh = maas(c, M, base_y, W - 2 * M)
    o.append(band)
    yb = base_y + bh + 34
    o.append(text(FOOTER, "text", LABEL, M, yb, c["muted"]))
    H = int(yb + M - 6)
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="The Arffornia ecosystem. Play: launcher, website, sign-in pages. Game: mod, provisioning, votes. '
            f'Toolkit: Nexus libraries, docs and Noodle, agent kit. All of it runs on MaaS, Minecraft as a Service.">'
            f'<style>@keyframes belt {{ to {{ stroke-dashoffset: -24 }} }} .belt {{ animation: belt 1.6s linear infinite }} '
            f'@keyframes pulse {{ 0%,100% {{ opacity: .45 }} 50% {{ opacity: 1 }} }} .glow {{ animation: pulse 2.4s ease-in-out infinite }} '
            f'@keyframes blink {{ 0%,70%,100% {{ opacity: .2 }} 80% {{ opacity: 1 }} }} .beacon {{ animation: blink 2s linear infinite }} '
            f'@media (prefers-reduced-motion: reduce) {{ .belt, .glow, .beacon {{ animation: none }} }}</style>'
            f'<rect width="{W}" height="{H}" rx="24" fill="{c["canvas"]}"/>')
    return head + glyph_defs() + "".join(o) + "</svg>"


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "profile"
    for t in THEMES:
        with open(os.path.join(out, f"ecosystem.{t}.svg"), "w") as f:
            f.write(build(t))
    print("ok")

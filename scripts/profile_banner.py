#!/usr/bin/env python3
"""Generate the Arffornia org profile banner (dark + light), an animated, self-contained SVG.

Text is converted to paths (Chakra Petch, OFL) so it renders identically everywhere;
animation is pure CSS and stops under prefers-reduced-motion. No scripts, no external refs.
"""
import math, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

import os
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile", "fonts")
W, H = 1280, 400
FONTS = {"bold": TTFont(FONT_DIR + "/ChakraPetch-Bold.ttf"), "medium": TTFont(FONT_DIR + "/ChakraPetch-Medium.ttf")}

THEMES = {
    "dark": dict(bg1="#0b1115", bg2="#131c22", grid="#8fb4c8", grid_o=".07", ink="#e6ecef", muted="#8da0ab",
                 t1="#ffb36b", t2="#e0703c", belt="#26333c", belt_edge="#3b4b56", stripe="#33424c",
                 m_top="#3d4d58", m_left="#2b3943", m_right="#1f2a31", glow="#ffb547", teal="#4fd1c5",
                 cube=("#f09a62", "#c4622f", "#8f421c"), tower="#3b4a55", tower2="#2a363f", node_off="#2a3741", line_off="#2c3a44"),
    "light": dict(bg1="#f5f7f8", bg2="#e7ecef", grid="#46606f", grid_o=".08", ink="#172026", muted="#5a6a74",
                  t1="#c25a24", t2="#8f3b14", belt="#c3ced5", belt_edge="#a5b3bc", stripe="#b2bfc7",
                  m_top="#e6ecf0", m_left="#c9d3d9", m_right="#adbac3", glow="#e08a1e", teal="#0f8f86",
                  cube=("#e8874e", "#b4572a", "#86391a"), tower="#9eadb7", tower2="#8798a3", node_off="#cdd6dc", line_off="#c2ccd2"),
}


def text_path(txt, font, size, x, y, tracking=0.0):
    """Return an SVG path 'd' for txt with baseline at (x, y); also returns advance width."""
    f = FONTS[font]; gs = f.getGlyphSet(); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
    s = size / upm; pen = SVGPathPen(gs); cx = 0.0
    for ch in txt:
        g = cmap.get(ord(ch))
        if g is None:
            cx += size * 0.3; continue
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x + cx, y)))
        cx += gs[g].width * s + tracking
    return pen.getCommands(), cx - tracking


def iso(x, y, z=0, ox=930, oy=246, k=26):
    """Isometric projection of grid units to canvas pixels."""
    return (ox + (x - y) * k * math.cos(math.radians(30)), oy + (x + y) * k * math.sin(math.radians(30)) - z * k)


def poly(points, fill, extra=""):
    return f'<polygon points="{" ".join(f"{px:.1f},{py:.1f}" for px, py in points)}" fill="{fill}" {extra}/>'


def box(x, y, z, dx, dy, dz, top, left, right, extra=""):
    p = lambda a, b, c: iso(x + a, y + b, z + c)
    t = poly([p(0, 0, dz), p(dx, 0, dz), p(dx, dy, dz), p(0, dy, dz)], top, extra)
    l = poly([p(0, dy, 0), p(dx, dy, 0), p(dx, dy, dz), p(0, dy, dz)], left, extra)
    r = poly([p(dx, 0, 0), p(dx, dy, 0), p(dx, dy, dz), p(dx, 0, dz)], right, extra)
    return l + r + t


def build(theme):
    c = THEMES[theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Arffornia: a modded Minecraft server built around Satisfactory-style progression">']
    out.append(f"""<style>
RIDE_KEYFRAMES@keyframes rise {{ 0% {{ transform: translateY(0); opacity: 0 }} 10% {{ opacity: 1 }} 80% {{ opacity: 1 }} 100% {{ transform: translateY(-150px); opacity: 0 }} }}
@keyframes pulse {{ 0%,100% {{ opacity: .45 }} 50% {{ opacity: 1 }} }}
@keyframes blink {{ 0%,70%,100% {{ opacity: .2 }} 80% {{ opacity: 1 }} }}
@keyframes node {{ 0%,8% {{ fill: {c['node_off']} }} 14%,86% {{ fill: {c['teal']} }} 96%,100% {{ fill: {c['node_off']} }} }}
@keyframes edge {{ 0%,8% {{ stroke-dashoffset: 100 }} 16%,86% {{ stroke-dashoffset: 0 }} 96%,100% {{ stroke-dashoffset: 100 }} }}
.item {{ animation: ride-in 6s linear infinite }} .part {{ animation: ride-out 6s linear infinite }}
.cap {{ animation: rise 5s ease-in infinite }}
.glow {{ animation: pulse 2.4s ease-in-out infinite }}
.beacon {{ animation: blink 2s linear infinite }}
.n {{ animation: node 10s ease-in-out infinite }}
.e {{ stroke-dasharray: 100; stroke-dashoffset: 100; animation: edge 10s ease-in-out infinite }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important }} .n {{ fill: {c['teal']} }} .e {{ stroke-dashoffset: 0 }} }}
</style>""")
    out.append(f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/></linearGradient>
<linearGradient id="title" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c['t1']}"/><stop offset="1" stop-color="{c['t2']}"/></linearGradient>
<radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{c['glow']}" stop-opacity=".55"/><stop offset="1" stop-color="{c['glow']}" stop-opacity="0"/></radialGradient>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>""")
    out.append(f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="url(#bg)"/>')
    # isometric grid
    g = []
    for i in range(-14, 15):
        a, b = iso(i, -14), iso(i, 14); g.append(f"M{a[0]:.0f} {a[1]:.0f}L{b[0]:.0f} {b[1]:.0f}")
        a, b = iso(-14, i), iso(14, i); g.append(f"M{a[0]:.0f} {a[1]:.0f}L{b[0]:.0f} {b[1]:.0f}")
    out.append(f'<path d="{"".join(g)}" stroke="{c["grid"]}" stroke-opacity="{c["grid_o"]}" stroke-width="1" fill="none"/>')

    # ---- scene (right side) ----
    # input belt along +x from (-7,1) to (-1,1), machine at (-1..2), output belt along +x to the tower at (5,1)
    belt = lambda x0, x1: poly([iso(x0, 0.6, .35), iso(x1, 0.6, .35), iso(x1, 1.6, .35), iso(x0, 1.6, .35)], c["belt"], f'stroke="{c["belt_edge"]}" stroke-width="1"')
    out.append(box(-5.6, .6, 0, 4.6, 1, .35, c["belt"], c["belt_edge"], c["belt_edge"]))
    out.append(box(2.2, .6, 0, 3.2, 1, .35, c["belt"], c["belt_edge"], c["belt_edge"]))
    out.append(belt(-5.6, -1)); out.append(belt(2.2, 5.4))
    stripes = []
    for k in range(10):
        x = -5.4 + k * .5
        a, b = iso(x, .6, .35), iso(x, 1.6, .35); stripes.append(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}")
    for k in range(6):
        x = 2.4 + k * .5
        a, b = iso(x, .6, .35), iso(x, 1.6, .35); stripes.append(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}")
    out.append(f'<path d="{"".join(stripes)}" stroke="{c["stripe"]}" stroke-width="2"/>')
    # items riding the input belt (raw ore cubes) and the output belt (refined parts)
    start, end = iso(-5.5, .85, .35), iso(-1.4, .85, .35)
    dx, dy = end[0] - start[0], end[1] - start[1]
    for i in range(4):
        cube = box(-5.5, .85, .35, .5, .5, .5, c["cube"][0], c["cube"][1], c["cube"][2])
        out.append(f'<g class="item" style="animation-delay:{-i * 1.5:.1f}s">{cube}</g>')
    start2, end2 = iso(2.3, .85, .35), iso(4.6, .85, .35)
    dx2, dy2 = end2[0] - start2[0], end2[1] - start2[1]
    for i in range(2):
        part = box(2.3, .95, .35, .35, .35, .35, c["teal"], c["m_left"], c["m_right"])
        out.append(f'<g class="part" style="animation-delay:{-i * 3:.1f}s">{part}</g>')
    # machine
    out.append(box(-1.2, -.6, 0, 3.4, 3.2, 2.6, c["m_top"], c["m_left"], c["m_right"]))
    out.append(box(-.4, .2, 2.6, 1.8, 1.6, .5, c["m_top"], c["m_left"], c["m_right"]))  # top housing
    wx = [iso(-.6, 2.6, .8), iso(1.6, 2.6, .8), iso(1.6, 2.6, 2.0), iso(-.6, 2.6, 2.0)]
    out.append(poly(wx, c["glow"], 'class="glow"'))
    hc = iso(.5, 2.6, 1.4)
    out.append(f'<circle cx="{hc[0]:.1f}" cy="{hc[1]:.1f}" r="70" fill="url(#halo)" class="glow"/>')
    vents = "".join(f'<rect x="{iso(2.2, -.2 + k * .7, 1.8)[0] - 3:.1f}" y="{iso(2.2, -.2 + k * .7, 1.8)[1]:.1f}" width="6" height="14" rx="2" fill="{c["teal"]}" class="beacon" style="animation-delay:{k * .4:.1f}s"/>' for k in range(3))
    out.append(vents)
    # space elevator tower at (5.6, 1)
    out.append(box(5.4, .3, 0, 1.6, 1.6, .5, c["m_top"], c["m_left"], c["m_right"]))
    base = iso(6.2, 1.1, .5)
    tw = 30; th = 190
    out.append(f'<rect x="{base[0] - tw / 2:.1f}" y="{base[1] - th:.1f}" width="{tw}" height="{th}" fill="{c["tower2"]}"/>')
    out.append(f'<rect x="{base[0] - tw / 2:.1f}" y="{base[1] - th:.1f}" width="{tw / 2}" height="{th}" fill="{c["tower"]}"/>')
    rungs = "".join(f"M{base[0] - tw / 2:.1f} {base[1] - th + k * 19:.1f}h{tw}" for k in range(1, 10))
    out.append(f'<path d="{rungs}" stroke="{c["belt_edge"]}" stroke-width="1.5"/>')
    out.append(f'<rect x="{base[0] - 9:.1f}" y="{base[1] - 34:.1f}" width="18" height="24" rx="4" fill="{c["glow"]}" class="cap"/>')
    out.append(f'<circle cx="{base[0]:.1f}" cy="{base[1] - th - 8:.1f}" r="6" fill="{c["glow"]}" class="beacon"/>')

    # progression graph above the scene
    nodes = [(760, 92), (836, 60), (912, 98), (988, 62), (1066, 96), (1140, 58)]
    links = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 2), (2, 4)]
    step = 10 / (len(nodes) + 1)
    for i, (a, b) in enumerate(links):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        delay = min(a, b) * step * .62
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c["line_off"]}" stroke-width="3"/>')
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c["teal"]}" stroke-width="3" pathLength="100" class="e" style="animation-delay:{delay:.2f}s"/>')
    for i, (x, y) in enumerate(nodes):
        out.append(f'<rect x="{x - 11}" y="{y - 11}" width="22" height="22" rx="5" transform="rotate(45 {x} {y})" class="n" style="animation-delay:{i * step * .62:.2f}s" fill="{c["node_off"]}" stroke="{c["bg2"]}" stroke-width="3"/>')

    # ---- text (left side) ----
    d, _ = text_path("MODDED MINECRAFT  ·  NEOFORGE 1.21.1", "medium", 16, 64, 128, tracking=2.4)
    out.append(f'<path d="{d}" fill="{c["t1"]}"/>')
    d, w = text_path("ARFFORNIA", "bold", 104, 58, 228, tracking=4)
    out.append(f'<path d="{d}" fill="url(#title)"/>')
    d, _ = text_path("Progression that keeps every mod worth playing.", "medium", 25, 64, 282)
    out.append(f'<path d="{d}" fill="{c["ink"]}"/>')
    d, _ = text_path("Server · launcher · website · mods · Kubernetes", "medium", 18, 64, 322, tracking=.6)
    out.append(f'<path d="{d}" fill="{c["muted"]}"/>')
    out.append("</g></svg>")
    kf = lambda name, x, y: f"@keyframes {name} {{ 0% {{ transform: translate(0px,0px); opacity: 0 }} 8% {{ opacity: 1 }} 88% {{ opacity: 1 }} 100% {{ transform: translate({x:.1f}px,{y:.1f}px); opacity: 0 }} }}\n"
    return "\n".join(out).replace("RIDE_KEYFRAMES", kf("ride-in", dx, dy) + kf("ride-out", dx2, dy2))


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    for t in THEMES:
        with open(f"{outdir}/banner.{t}.svg", "w") as f:
            f.write(build(t))
    print("ok")

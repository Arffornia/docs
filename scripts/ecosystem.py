#!/usr/bin/env python3
"""Render the Arffornia ecosystem wheel (profile/ecosystem.{dark,light}.svg).

Three cores (Play, Build, Run), nine capabilities, and every building block around them,
inside a slowly turning cog. Text is converted to paths (Chakra Petch) like the banner.
Edit ECOSYSTEM below to add or move a block, then run: python3 scripts/ecosystem.py profile
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile_banner import text_path, FONTS

# core -> capabilities -> (blocks; a trailing "*" marks a planned block)
ECOSYSTEM = [
    ("PLAY", "player journey", [
        ("Launcher", "rocket", ["Electron launcher", "Microsoft login", "Modpack sync", "Shader browser"]),
        ("Website", "globe", ["Accounts & profiles", "Shop", "Progression editor", "Public API"]),
        ("Community", "chat", ["Votes & rewards", "Discord bridge", "Live map", "Rankings*"]),
    ]),
    ("BUILD", "the game", [
        ("Mod", "gear", ["Progression graph", "Space Elevator", "Crafter", "Machines*"]),
        ("Modpack", "box", ["~330 mods", "Provisioning", "Config updater", "Datapack recipes*"]),
        ("Libraries", "puzzle", ["Nexus Mods", "Nexus Java", "Nexus Logger", "Nexus Saver"]),
    ]),
    ("RUN", "the platform", [
        ("Infrastructure", "server", ["NeoForge servers", "Velocity proxy", "Kubernetes", "Argo CD GitOps"]),
        ("Data & trust", "shield", ["Postgres", "Vault secrets", "Backups", "Monitoring"]),
        ("Engineering", "spark", ["Docs & Noodle", "AI agent kit", "CI & tests", "Preview servers*"]),
    ]),
]

THEMES = {
    "dark": dict(bg="#0b1115", ring="#121b21", panel="#151f26", edge="#22303a", ink="#e6ecef", muted="#8da0ab",
                 hub="#0f171c", hub_ink="#ffb36b", cog="#1b262e", planned="#6f838f",
                 cores=["#e0703c", "#2bb3a6", "#5b7cfa"], tints=["#3a2216", "#123532", "#1c2547"]),
    "light": dict(bg="#f5f7f8", ring="#e9eef1", panel="#ffffff", edge="#d3dbe0", ink="#172026", muted="#5a6a74",
                  hub="#ffffff", hub_ink="#b4572a", cog="#dfe6ea", planned="#8a98a1",
                  cores=["#c25a24", "#0f8f86", "#3e5fd8"], tints=["#f8e2d6", "#d6f0ed", "#dfe6fd"]),
}

S = 1200; C = S / 2
R_HUB, R_CORE, R_CAP, R_ITEM, R_COG = 96, 214, 338, 520, 548


def pol(r, a):
    a = math.radians(a - 90)
    return C + r * math.cos(a), C + r * math.sin(a)


def sector(r1, r2, a1, a2, gap=0.0):
    """Annular sector path from angle a1 to a2 (degrees, 0 = top, clockwise)."""
    a1 += gap; a2 -= gap
    large = 1 if a2 - a1 > 180 else 0
    p1, p2, p3, p4 = pol(r2, a1), pol(r2, a2), pol(r1, a2), pol(r1, a1)
    return (f"M{p1[0]:.1f} {p1[1]:.1f} A{r2} {r2} 0 {large} 1 {p2[0]:.1f} {p2[1]:.1f} "
            f"L{p3[0]:.1f} {p3[1]:.1f} A{r1} {r1} 0 {large} 0 {p4[0]:.1f} {p4[1]:.1f}Z")


def text_width(txt, font, size, tracking=0.0):
    f = FONTS[font]; gs = f.getGlyphSet(); cmap = f.getBestCmap(); s = size / f["head"].unitsPerEm
    return sum(gs[cmap[ord(ch)]].width * s + tracking for ch in txt if ord(ch) in cmap) - tracking


def centered(txt, font, size, x, y, fill, tracking=0.0, extra=""):
    w = text_width(txt, font, size, tracking)
    d, _ = text_path(txt, font, size, x - w / 2, y, tracking)
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def icon(name, x, y, color, s=1.0):
    """Small line icons drawn on a 28 px grid centred on (x, y)."""
    st = f'fill="none" stroke="{color}" stroke-width="{2.4 * s:.1f}" stroke-linecap="round" stroke-linejoin="round"'
    t = f'transform="translate({x - 14 * s:.1f} {y - 14 * s:.1f}) scale({s})"'
    shapes = {
        "rocket": '<path d="M14 2c5 4 7 10 5 17h-10C7 12 9 6 14 2z"/><circle cx="14" cy="11" r="2.4"/><path d="M9 19l-4 5 6-1M19 19l4 5-6-1M12 23l2 4 2-4"/>',
        "globe": '<circle cx="14" cy="14" r="11"/><path d="M3 14h22M14 3c4 4 4 18 0 22M14 3c-4 4-4 18 0 22"/>',
        "chat": '<path d="M4 6h20v13H12l-6 5v-5H4z"/><path d="M9 12h10M9 16h6"/>',
        "gear": '<circle cx="14" cy="14" r="4"/><path d="M14 2v4M14 22v4M2 14h4M22 14h4M5.5 5.5l2.8 2.8M19.7 19.7l2.8 2.8M5.5 22.5l2.8-2.8M19.7 8.3l2.8-2.8"/><circle cx="14" cy="14" r="8.5"/>',
        "box": '<path d="M14 3l10 5v12l-10 5-10-5V8z"/><path d="M4 8l10 5 10-5M14 13v12"/>',
        "puzzle": '<path d="M5 9h5a3 3 0 1 1 6 0h5v5a3 3 0 1 0 0 6v4H5v-5a3 3 0 1 1 0-6z"/>',
        "server": '<rect x="4" y="4" width="20" height="8" rx="2"/><rect x="4" y="16" width="20" height="8" rx="2"/><path d="M8 8h2M8 20h2"/>',
        "shield": '<path d="M14 3l9 4v6c0 6-4 10-9 12-5-2-9-6-9-12V7z"/><path d="M10 14l3 3 5-6"/>',
        "spark": '<path d="M14 3v6M14 19v6M3 14h6M19 14h6M7 7l3 3M18 18l3 3M7 21l3-3M18 10l3-3"/><circle cx="14" cy="14" r="2.5"/>',
    }
    return f'<g {t} {st}>{shapes[name]}</g>'


def build(theme):
    c = THEMES[theme]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}" role="img" '
         f'aria-label="The Arffornia ecosystem: Play, Build and Run, nine capabilities and their building blocks">',
         f"""<style>
@keyframes turn {{ to {{ transform: rotate(360deg) }} }}
@keyframes glow {{ 0%,100% {{ opacity: .55 }} 50% {{ opacity: 1 }} }}
.cog {{ transform-origin: {C}px {C}px; animation: turn 120s linear infinite }}
.pulse {{ animation: glow 3.2s ease-in-out infinite }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important }} }}
</style>""",
         f'<rect width="{S}" height="{S}" rx="28" fill="{c["bg"]}"/>']
    # cog teeth
    teeth = []
    for i in range(72):
        a = i * 5
        teeth.append(sector(R_COG - 16, R_COG + 8, a - 1.3, a + 1.3))
    o.append(f'<g class="cog"><circle cx="{C}" cy="{C}" r="{R_COG - 14}" fill="{c["cog"]}"/><path d="{"".join(teeth)}" fill="{c["cog"]}"/></g>')
    o.append(f'<circle cx="{C}" cy="{C}" r="{R_ITEM}" fill="{c["ring"]}"/>')

    n_cap = sum(len(caps) for _, _, caps in ECOSYSTEM); span = 360 / n_cap
    start = -span * 1.5  # centre the PLAY core on top
    k = 0
    for ci, (core, sub, caps) in enumerate(ECOSYSTEM):
        col, tint = c["cores"][ci], c["tints"][ci]
        a_core1, a_core2 = start + k * span, start + (k + len(caps)) * span
        o.append(f'<path d="{sector(R_HUB + 6, R_CORE, a_core1, a_core2, 0.8)}" fill="{col}"/>')
        mid = (a_core1 + a_core2) / 2; x, y = pol((R_HUB + R_CORE) / 2 + 12, mid)
        o.append(centered(core, "bold", 30, x, y + 4, "#ffffff", tracking=3))
        o.append(centered(sub, "medium", 13, x, y + 26, "#ffffff", extra='fill-opacity=".85"'))
        for name, ic, items in caps:
            a1, a2 = start + k * span, start + (k + 1) * span; am = (a1 + a2) / 2
            o.append(f'<path d="{sector(R_CORE + 6, R_CAP, a1, a2, 0.6)}" fill="{tint}"/>')
            o.append(f'<path d="{sector(R_CAP - 5, R_CAP, a1, a2, 0.6)}" fill="{col}" class="pulse" style="animation-delay:{k * .35:.2f}s"/>')
            ix, iy = pol((R_CORE + R_CAP) / 2 + 10, am)
            o.append(icon(ic, ix, iy - 16, col, 1.15))
            o.append(centered(name, "bold", 17, ix, iy + 22, c["ink"]))
            o.append(f'<path d="{sector(R_CAP + 6, R_ITEM - 6, a1, a2, 0.5)}" fill="{c["panel"]}" stroke="{c["edge"]}"/>')
            # blocks stacked around the outer segment's centre
            rx, ry = pol((R_CAP + R_ITEM) / 2 + 4, am)
            lh = 25; top = ry - (len(items) - 1) * lh / 2
            for j, it in enumerate(items):
                planned = it.endswith("*"); label = it.rstrip("*")
                yy = top + j * lh + 6
                o.append(centered(label, "medium", 16, rx, yy, c["planned"] if planned else c["ink"]))
                if planned:
                    w = text_width(label, "medium", 16)
                    o.append(f'<line x1="{rx - w / 2:.1f}" y1="{yy + 5:.1f}" x2="{rx + w / 2:.1f}" y2="{yy + 5:.1f}" stroke="{c["planned"]}" stroke-dasharray="3 3"/>')
            k += 1
    # hub
    o.append(f'<circle cx="{C}" cy="{C}" r="{R_HUB}" fill="{c["hub"]}" stroke="{c["edge"]}" stroke-width="2"/>')
    o.append(centered("ARFFORNIA", "bold", 22, C, C - 2, c["hub_ink"], tracking=2))
    o.append(centered("ecosystem", "medium", 13, C, C + 20, c["muted"], tracking=1.5))
    # legend
    o.append(centered("dashed = planned", "medium", 13, C, S - 18, c["muted"], tracking=.5))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "profile"
    for t in THEMES:
        with open(os.path.join(out, f"ecosystem.{t}.svg"), "w") as f:
            f.write(build(t))
    print("ok")

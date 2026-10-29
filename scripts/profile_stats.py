#!/usr/bin/env python3
"""Render the live numbers card of the org profile (profile/stats.{dark,light}.svg).

Public data only: GitHub REST + the Provisioning mod list. Run daily by .github/workflows/profile.yml.
Env: GITHUB_TOKEN (optional locally, raises rate limits). Needs fonttools.
"""
import datetime as dt, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile_banner import text_path  # same font and path conversion as the banner

ORG = "Arffornia"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "arffornia-profile"})
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def search(q):
    return get("https://api.github.com/search/issues?per_page=1&q=" + urllib.request.quote(q))["total_count"]


def latest(repo):
    try:
        return get(f"https://api.github.com/repos/{ORG}/{repo}/releases/latest")["tag_name"]
    except Exception:
        return "–"


def collect():
    mods = get("https://raw.githubusercontent.com/Arffornia/Arffornia_Provisioning/main/config/launcher/modList.json")["mods"]
    repos = [r for r in get(f"https://api.github.com/orgs/{ORG}/repos?per_page=100&type=public") if not r["archived"]]
    since = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    return {
        "metrics": [
            (str(sum(len(v) for v in mods.values())), "MODS IN THE PACK"),
            (str(len(repos)), "ACTIVE REPOSITORIES"),
            (str(search(f"org:{ORG} is:issue is:open")), "OPEN ISSUES"),
            (str(search(f"org:{ORG} is:issue is:open label:agent-ready")), "READY TO PICK UP"),
            (str(search(f"org:{ORG} is:pr is:merged merged:>={since}")), "PRS MERGED · 30 DAYS"),
        ],
        "footer": f"Launcher {latest('Arffornia_Launcher_V.5.2')}  ·  Mod {latest('Arffornia_Mods')}  ·  Minecraft 1.21.1  ·  updated {dt.date.today().isoformat()}",
    }


THEMES = {
    "dark": dict(bg1="#0b1115", bg2="#131c22", tile="#151f25", edge="#24323b", num="#ffb36b", label="#8da0ab", foot="#6f838f", accent="#4fd1c5"),
    "light": dict(bg1="#f5f7f8", bg2="#e7ecef", tile="#ffffff", edge="#d3dbe0", num="#b4572a", label="#5a6a74", foot="#6b7b85", accent="#0f8f86"),
}


def render(data, theme):
    c = THEMES[theme]; W, H = 1280, 210
    n = len(data["metrics"]); gap = 16; pad = 32; tw = (W - 2 * pad - gap * (n - 1)) / n
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Arffornia in numbers">',
           f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg2"]}"/></linearGradient></defs>',
           f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>']
    for i, (value, label) in enumerate(data["metrics"]):
        x = pad + i * (tw + gap)
        out.append(f'<rect x="{x:.1f}" y="28" width="{tw:.1f}" height="118" rx="12" fill="{c["tile"]}" stroke="{c["edge"]}"/>')
        out.append(f'<rect x="{x + 20:.1f}" y="46" width="22" height="4" rx="2" fill="{c["accent"]}"/>')
        d, _ = text_path(value, "bold", 46, x + 18, 106)
        out.append(f'<path d="{d}" fill="{c["num"]}"/>')
        d, _ = text_path(label, "medium", 12.5, x + 20, 130, tracking=1.6)
        out.append(f'<path d="{d}" fill="{c["label"]}"/>')
    d, _ = text_path(data["footer"], "medium", 14, pad, 182, tracking=.4)
    out.append(f'<path d="{d}" fill="{c["foot"]}"/></svg>')
    return "\n".join(out)


if __name__ == "__main__":
    data = collect()
    for t in THEMES:
        with open(os.path.join(OUT, f"stats.{t}.svg"), "w") as f:
            f.write(render(data, t))
    print(json.dumps(data))

#!/usr/bin/env python3
"""Render preview stills and clips from the HTML previews (deterministic frames).

usage: render.py still <view> <t> <out.png> [--lang fr] [--size 1920x1080]
       render.py clip  <view> <seconds> <out.mp4> [--fps 30] [--lang fr] [--size 1280x720] [--gif out.gif]
Frames are drawn with window.renderFrame(t), captured as PNG, encoded with ffmpeg (H.264, -preset veryfast).
"""
import argparse, os, pathlib, shutil, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent

def page_for(p, view, lang, w, h, scale=1):
    b = p.chromium.launch(args=["--font-render-hinting=none"])
    pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
    pg.goto(f"file://{HERE}/{view}.html?record=1&lang={lang}")
    pg.wait_for_function("window.READY !== undefined")
    pg.evaluate("window.READY")
    return b, pg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["still", "clip"])
    ap.add_argument("view"); ap.add_argument("time", type=float); ap.add_argument("out")
    ap.add_argument("--lang", default="en"); ap.add_argument("--size", default="1280x720")
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--gif"); ap.add_argument("--scale", type=float, default=1); ap.add_argument("--keys", action="store_true")
    a = ap.parse_args()
    w, h = map(int, a.size.split("x"))
    with sync_playwright() as p:
        b, pg = page_for(p, a.view, a.lang + ("&keys=1" if a.keys else ""), w, h, a.scale)
        if a.mode == "still":
            pg.evaluate(f"window.renderFrame({a.time})")
            pg.screenshot(path=a.out)
            b.close(); return
        # stream PNG frames into ffmpeg (no frames on disk)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(a.fps), "-c:v", "png", "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out],
                              stdin=subprocess.PIPE)
        n = int(round(a.time * a.fps))
        for i in range(n):
            t = a.start + i / a.fps
            pg.evaluate(f"window.renderFrame({t})")
            ff.stdin.write(pg.screenshot(type="png"))
            if i % 60 == 0: print(f"{a.view}: frame {i}/{n}", file=sys.stderr, flush=True)
        b.close()
    ff.stdin.close()
    if ff.wait() != 0: sys.exit("ffmpeg failed")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="arf-pal-"))
    if a.gif:
        pal = tmp / "pal.png"
        vf = "fps=15,scale=720:-1:flags=lanczos"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.out, "-vf", f"{vf},palettegen=stats_mode=diff", str(pal)], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.out, "-i", str(pal), "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=sierra2_4a", a.gif], check=True)
    shutil.rmtree(tmp)

if __name__ == "__main__":
    main()

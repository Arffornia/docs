#!/usr/bin/env python3
"""Compare a screenshot against an approved baseline.

usage: shotdiff.py ACTUAL BASELINE [--diff out.png] [--mask masks.json] [--pixel-tol 24] [--max-ratio 0.005]

- A pixel differs when any RGB channel differs by more than --pixel-tol (0-255). Small tolerance absorbs
  Mesa/llvmpipe rounding; it does not hide layout or colour changes.
- The image fails when more than --max-ratio of the unmasked pixels differ.
- masks.json: {"<baseline file name>": [[x, y, w, h], ...]} rectangles to ignore (clocks, memory text, CPU).
- Writes a diff image (baseline dimmed, differing pixels in red, masks in blue) when --diff is set.
Exit codes: 0 pass, 1 fail, 2 size mismatch or missing file.
"""
import argparse, json, pathlib, sys

import numpy as np
from PIL import Image


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("actual"); ap.add_argument("baseline")
    ap.add_argument("--diff"); ap.add_argument("--mask")
    ap.add_argument("--pixel-tol", type=int, default=24)
    ap.add_argument("--max-ratio", type=float, default=0.005)
    a = ap.parse_args()
    try:
        act = np.asarray(Image.open(a.actual).convert("RGB"), dtype=np.int16)
        base = np.asarray(Image.open(a.baseline).convert("RGB"), dtype=np.int16)
    except FileNotFoundError as e:
        print(f"MISSING {e.filename}"); return 2
    if act.shape != base.shape:
        print(f"SIZE MISMATCH actual={act.shape[1]}x{act.shape[0]} baseline={base.shape[1]}x{base.shape[0]}"); return 2
    keep = np.ones(act.shape[:2], dtype=bool)
    if a.mask:
        for x, y, w, h in json.loads(pathlib.Path(a.mask).read_text()).get(pathlib.Path(a.baseline).name, []):
            keep[y:y + h, x:x + w] = False
    diff = (np.abs(act - base).max(axis=2) > a.pixel_tol) & keep
    ratio = diff.sum() / max(1, keep.sum())
    ok = ratio <= a.max_ratio
    if a.diff:
        out = (base * 0.35).astype(np.uint8)
        out[~keep] = (out[~keep] * 0.5 + np.array([40, 80, 200]) * 0.5).astype(np.uint8)
        out[diff] = [255, 40, 40]
        Image.fromarray(out).save(a.diff)
    print(f"{'PASS' if ok else 'FAIL'} {pathlib.Path(a.actual).name}: {ratio * 100:.3f}% pixels differ (limit {a.max_ratio * 100:.3f}%)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

# Screen test harness: feasibility probes

Probes run on 2026-10-29 for [spec 007](../../007-loading-and-title-screen.md). They need Java 21,
`xvfb-run`, Mesa (llvmpipe) and ffmpeg, and take their jars from the Gradle cache of any
NeoForge 21.1 project (`~/.gradle/caches/modules-2`). Nothing here is shipped.

| File | What it proves | Run |
|---|---|---|
| `EarlyWindowProbe.java` + `probe.sh` | GLFW + OpenGL core works headless; offscreen framebuffer → `glReadPixels` → PNG; asserts `GL_RENDERER` contains `llvmpipe` and checks one pixel | `sh probe.sh out.png` |
| `FmlEarlyWindowShot.java` + `fml-shot.sh` | Drives FML 4.0.39's real `DisplayWindow` (NeoForge 21.1.x early window) without Minecraft, feeds fake mod progress, grabs the screen at T seconds with `ffmpeg -f x11grab` | `sh fml-shot.sh out.png 4` |
| `shotdiff.py` | Baseline comparison with per-channel tolerance, a max-differing-pixels ratio, rectangle masks and a diff image | `python3 shotdiff.py actual.png baseline.png --diff d.png --mask masks.json` |

Results:

| Run | Result |
|---|---|
| `probe.sh` | `GL_RENDERER=llvmpipe (LLVM 20.1.2, 256 bits)`, `GL_VERSION=4.5 (Core Profile) Mesa 25.2.8`, 40 frames, 3.69 ms/frame, pixel check OK |
| `fml-shot.sh … 4` | Stock early window captured (`fml-early-window.png`), 117 ticks in 6 s |
| `shotdiff.py` probe vs probe | 0.000 % differ, PASS |
| `shotdiff.py` probe vs probe + 200-px defect | 0.049 % differ, FAIL (limit 0.01 %) |
| `shotdiff.py` stock FML run 1 vs run 2 | 0.593 % (0.622 % with masks), FAIL: the fox frame follows the wall clock (`fml-diff-masked.png`), so our provider must expose a frozen test clock |

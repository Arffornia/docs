#!/bin/sh
# Headless early-window probe: GLFW + GL 3.2 core under Xvfb with Mesa llvmpipe, framebuffer -> PNG.
# Usage: sh probe.sh [out.png]   (needs Java 21, xvfb-run, Mesa; LWJGL 3.3.3 jars from the Gradle cache)
set -eu
OUT="${1:-early-window-probe.png}"
DIR="$(cd "$(dirname "$0")" && pwd)"
G="${GRADLE_USER_HOME:-$HOME/.gradle}/caches/modules-2/files-2.1/org.lwjgl"
CP=""
for a in lwjgl lwjgl-glfw lwjgl-opengl lwjgl-stb; do
  for j in "$G/$a/3.3.3"/*/"$a-3.3.3.jar" "$G/$a/3.3.3"/*/"$a-3.3.3-natives-linux.jar"; do CP="$CP:$j"; done
done
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
exec xvfb-run -a -s "-screen 0 1280x720x24 -nocursor" java -cp "${CP#:}" "$DIR/EarlyWindowProbe.java" "$OUT"

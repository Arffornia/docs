#!/bin/sh
# Launch FML's real early window under Xvfb, grab the screen at T seconds with ffmpeg x11grab.
# Usage: sh fml-shot.sh out.png [T=4]
set -eu
OUT="${1:-fml-early-window.png}"; T="${2:-4}"
DIR="$(cd "$(dirname "$0")" && pwd)"; C="${GRADLE_USER_HOME:-$HOME/.gradle}/caches/modules-2/files-2.1"
CP=""
add() { for j in $1; do [ -f "$j" ] && CP="$CP:$j"; done; }
add "$C/net.neoforged.fancymodloader/loader/4.0.39/*/loader-4.0.39.jar"
add "$C/net.neoforged.fancymodloader/earlydisplay/4.0.39/*/earlydisplay-4.0.39.jar"
for a in lwjgl lwjgl-glfw lwjgl-opengl lwjgl-stb lwjgl-tinyfd; do add "$C/org.lwjgl/$a/3.3.3/*/$a-3.3.3.jar"; add "$C/org.lwjgl/$a/3.3.3/*/$a-3.3.3-natives-linux.jar"; done
add "$C/org.slf4j/slf4j-api/2.0.9/*/slf4j-api-2.0.9.jar"
add "$C/net.sf.jopt-simple/jopt-simple/5.0.4/*/jopt-simple-5.0.4.jar"
add "$C/com.electronwill.night-config/core/3.8.2/*/core-3.8.2.jar"; add "$C/com.electronwill.night-config/toml/3.8.2/*/toml-3.8.2.jar"
add "$C/org.apache.logging.log4j/log4j-api/2.22.1/*/log4j-api-2.22.1.jar"; add "$C/org.apache.logging.log4j/log4j-core/2.22.1/*/log4j-core-2.22.1.jar"
add "$C/cpw.mods/modlauncher/11.0.4/*/modlauncher-11.0.4.jar"; add "$C/cpw.mods/securejarhandler/3.0.8/*/securejarhandler-3.0.8.jar"
add "$C/org.apache.maven/maven-artifact/3.8.5/*/maven-artifact-3.8.5.jar"; add "$C/com.mojang/logging/1.2.7/*/logging-1.2.7.jar"; add "$C/com.google.guava/guava/32.1.2-jre/*/guava-32.1.2-jre.jar"
export LIBGL_ALWAYS_SOFTWARE=1
WORK="$(mktemp -d)"
xvfb-run -a -s "-screen 0 854x480x24 -nocursor" sh -c "
  java -cp '${CP#:}' '$DIR/FmlEarlyWindowShot.java' '$WORK/game' $((T + 2)) > '$WORK/log.txt' 2>&1 &
  JP=\$!
  i=0; while ! grep -q EARLY_WINDOW_SHOWN '$WORK/log.txt' 2>/dev/null; do sleep 0.2; i=\$((i+1)); [ \$i -gt 150 ] && break; done
  sleep $T
  ffmpeg -loglevel error -y -f x11grab -draw_mouse 0 -video_size 854x480 -i \"\$DISPLAY\" -frames:v 1 '$OUT'
  wait \$JP
"
grep -E "GL info|EARLY_WINDOW_SHOWN|DONE|Exception|Error" "$WORK/log.txt" | head -20
rm -rf "$WORK"

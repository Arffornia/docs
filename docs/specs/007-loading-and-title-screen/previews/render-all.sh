#!/bin/sh
# Renders every preview still and clip. Usage: sh render-all.sh  (from mc-screens/)
set -e
cd "$(dirname "$0")"; [ -d src ] && cd src
O="${OUT:-../out}"; mkdir -p "$O"
for spec in "loading-a 6.2 en" "loading-a 10.6 fr" "loading-b 6.2 en" "loading-b 10.6 fr" "title-a 3.6 en" "title-a 3.6 fr" "title-b 3.6 en" "title-b 7.4 fr"; do
  set -- $spec
  python3 render.py still "$1" "$2" "$O/$1.$3.png" --lang "$3" --scale 1.5
done
python3 render.py still loading-a 6.2 "$O/loading-a.keys.png" --scale 1.5 --keys
python3 render.py clip loading-a 14 "$O/loading-a.en.mp4" --gif "$O/loading-a.en.gif"
python3 render.py clip loading-b 14 "$O/loading-b.en.mp4" --gif "$O/loading-b.en.gif"
python3 render.py clip title-a 10.5 "$O/title-a.en.mp4" --gif "$O/title-a.en.gif"
python3 render.py clip title-b 10.5 "$O/title-b.en.mp4" --gif "$O/title-b.en.gif"
python3 render.py clip loading-a 14 "$O/loading-a.fr.mp4" --lang fr
python3 render.py clip title-a 10.5 "$O/title-a.fr.mp4" --lang fr
python3 render.py clip loading-a 14 "$O/loading-a.en.20fps.mp4" --fps 20

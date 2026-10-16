#!/bin/sh
# Record every CAM command scene, one FreeCAD start per scene (see cam_rec.py).
#   HOME=<throw-away home> FREECAD=<freecad> OUT=<dir> sh tools/gifs/cam_rec.sh [scene ...]
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
SCENES=${*:-$(grep -o '^@scene("[A-Za-z_0-9]*")' "$HERE/cam_rec.py" | sed 's/@scene("\(.*\)")/\1/')}
for s in $SCENES; do
    WT_OUT="$OUT" WT_ONLY="$s" timeout 300 xvfb-run -a -s "-screen 0 1920x1200x24" \
        "$FREECAD" "$HERE/cam_rec.py" >"$OUT/$s.log" 2>&1
    grep -q "^OK $s" "$OUT/rec_log.txt" 2>/dev/null && echo "OK   $s" || echo "FAIL $s"
done

#!/bin/sh
# SPDX-License-Identifier: LGPL-2.1-or-later
# Run tests/freecad_gui_test.py in a real FreeCAD, one CAM dialog per FreeCAD start.
#
#   FREECAD=/path/to/bin/freecad OUT=/tmp/wt sh tests/run_freecad_tests.sh
#
# One dialog per process: opening and closing many CAM dialogs from a script in one
# session crashed FreeCAD 26.3 even WITHOUT WikiTips installed (control run, 2026-10-16).
set -u
FREECAD=${FREECAD:-freecad}
OUT=${OUT:-/tmp/wikitips-test}
HERE=$(cd "$(dirname "$0")" && pwd)
rm -rf "$OUT"
mkdir -p "$OUT"
status=0

run() {  # name, extra env assignments...
    name=$1; shift
    script=freecad_gui_test.py
    [ "$name" = errors ] && script=freecad_error_test.py
    [ "$name" = knurl ] && script=freecad_knurl_test.py
    env "$@" WT_OUT="$OUT/$name" xvfb-run -a -s "-screen 0 1920x1200x24" \
        "$FREECAD" "$HERE/$script" > "$OUT/$name.log" 2>&1
    code=$?
    result=$(grep RESULT "$OUT/$name/result.txt" 2>/dev/null || echo "RESULT: no result")
    echo "$name: exit=$code $result"
    case "$code $result" in
        "0 RESULT: PASS") ;;
        *) status=1 ;;
    esac
}

run toolbars WT_CAM_OPS=
run errors
run knurl
for op in CAM_Profile: CAM_Pocket_Shape:Face6 CAM_MillFacing:Face6 CAM_Adaptive:Face6 CAM_Drilling:Face7 \
          CAM_DressupDogbone: CAM_DressupTag: CAM_DressupLeadInOut: CAM_DressupPathBoundary: \
          CAM_DressupDragKnife: CAM_DressupAxisMap:; do
    run "${op%%:*}" WT_SKIP_WB=1 WT_CAM_OPS="$op"
done
for op in PartDesign_Pad PartDesign_Pocket PartDesign_Revolution PartDesign_Hole PartDesign_Fillet \
          PartDesign_Chamfer PartDesign_Thickness PartDesign_AdditiveHelix PartDesign_LinearPattern \
          PartDesign_PolarPattern; do
    run "$op" WT_SKIP_WB=1 WT_CAM_OPS= WT_PD_OPS="$op"
done
[ $status -eq 0 ] && echo "ALL PASS" || echo "SOME FAILED (see $OUT)"
exit $status

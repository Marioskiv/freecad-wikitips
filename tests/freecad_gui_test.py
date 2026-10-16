# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test WikiTips inside a REAL FreeCAD (not the mock in run_popup_test.py).

Run with the addon installed in the user Mod folder, e.g. on Linux:

    WT_OUT=/tmp/wt xvfb-run -a freecad tests/freecad_gui_test.py

For every visible toolbar button of the main workbenches it records which
command WikiTips resolves, sends a real ToolTip event to selected buttons and
saves the popups as PNG. Results: $WT_OUT/result.txt (+ pop_*.png, win_*.png).
Lines starting with "NO ENTRY" are buttons without a popup.
"""
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("WT_OUT", os.path.join(os.path.expanduser("~"), "wikitips-test"))
os.makedirs(OUT, exist_ok=True)

WORKBENCHES = ["SketcherWorkbench", "PartDesignWorkbench", "PartWorkbench", "CAMWorkbench"]
POPUPS = {  # button (defaultAction objectName) -> expected command
    "Sketcher_CompCreateArc": None, "Sketcher_CompCreateRectangles": None,
    "Sketcher_CompDimensionTools": None, "Sketcher_CompExternal": "Sketcher_Projection",
    "PartDesign_Pad": "PartDesign_Pad", "PartDesign_Pocket": "PartDesign_Pocket",
    "PartDesign_CompPrimitiveAdditive": None, "PartDesign_SubShapeBinder": "PartDesign_SubShapeBinder",
    "Part_Boolean": "Part_Boolean", "Part_CompOffset": "Part_Offset",
    "Part_CompCompoundTools": "Part_Compound", "Part_CompJoinFeatures": None,
    "CAM_Profile": "CAM_Profile", "CAM_Pocket_Shape": "CAM_Pocket_Shape",
    "CAM_DrillingTools": "CAM_Drilling", "CAM_PostTools": "CAM_Post",
    "CAM_SimTools": None, "CAM_EngraveTools": "CAM_Engrave",
}
IGNORE = {"", "WikiTips_Toggle", "OBTN Overlay", "OBTN Float", "OBTN Close", "OBTN Transparent", "OBTN AutoMode"}  # dock overlay buttons

log = open(os.path.join(OUT, "result.txt"), "w", encoding="utf-8")


def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n")
    log.flush()


def pump(ms):
    t = QtCore.QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)


def hover(wikitips, button):
    """Move the real cursor onto the button and send the ToolTip event Qt would send."""
    center = button.rect().center()
    gpos = button.mapToGlobal(center)
    QtGui.QCursor.setPos(gpos)
    pump(50)
    ev = QtGui.QHelpEvent(QtCore.QEvent.Type.ToolTip, center, gpos)
    QtWidgets.QApplication.sendEvent(button, ev)
    pump(400)
    pop = wikitips._FILTER.popup
    return pop if (pop.isVisible() and pop._owner is button) else None


def run():
    failures = 0
    try:
        import wikitips
        P("WikiTips loaded:", wikitips._FILTER is not None, "entries:", len(wikitips.data()))
        mw = Gui.getMainWindow()
        mw.resize(1600, 1000)
        for wb in WORKBENCHES:
            Gui.activateWorkbench(wb)
            if wb == "SketcherWorkbench":  # sketcher toolbars only show in edit mode
                doc = App.newDocument("WikiTipsTest")
                sk = doc.addObject("Sketcher::SketchObject", "Sketch")
                doc.recompute()
                Gui.ActiveDocument.setEdit(sk.Name)
            pump(2600)  # the addon scans for new buttons every 2 s
            seen, total, missing = set(), 0, []
            for b in mw.findChildren(QtWidgets.QToolButton):
                a = b.defaultAction()
                if a is None or not b.isVisible() or id(b) in seen:
                    continue
                seen.add(id(b))
                name = wikitips.action_name(a)
                if name in IGNORE:
                    continue
                total += 1
                key = wikitips.command_name(a, b)
                if not key:
                    missing.append(name)
                if a.objectName() in POPUPS:
                    pop = hover(wikitips, b)
                    want = POPUPS[a.objectName()]
                    ok = pop is not None and (want is None or key == want)
                    failures += not ok
                    P("  %-4s %-34s -> %-28s popup=%s %s" % ("OK" if ok else "FAIL", a.objectName(), key,
                      "%dx%d" % (pop.width(), pop.height()) if pop else "none",
                      "" if ok or want is None else "(expected %s)" % want))
                    if pop:
                        pop.grab().save(os.path.join(OUT, "pop_%s.png" % a.objectName()))
                        pop.dismiss()
            P("== %s: %d buttons, %d without entry" % (wb, total, len(missing)))
            for m in missing:
                P("   NO ENTRY", m)
            mw.grab().save(os.path.join(OUT, "win_%s.png" % wb))
            if wb == "SketcherWorkbench":
                Gui.ActiveDocument.resetEdit()
        P("RESULT:", "PASS" if failures == 0 else "%d FAILURES" % failures)
    except Exception:
        P("EXCEPTION", traceback.format_exc())
    finally:
        log.close()
        QtCore.QTimer.singleShot(200, lambda: os._exit(0))


QtCore.QTimer.singleShot(4000, run)

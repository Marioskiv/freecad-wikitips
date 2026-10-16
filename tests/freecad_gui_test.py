# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test WikiTips inside a REAL FreeCAD (not the mock in run_popup_test.py).

Run with the addon installed in the user Mod folder, e.g. on Linux:

    WT_OUT=/tmp/wt xvfb-run -a freecad tests/freecad_gui_test.py
    FREECAD=<fc>/bin/freecad sh tests/run_freecad_tests.sh      # everything, one dialog per start

For every visible toolbar button of the main workbenches it records which
command WikiTips resolves, sends a real ToolTip event to selected buttons and
saves the popups as PNG. Then it opens CAM operation dialogs and hovers every
field that has Greek help (content/fields_el.json).
Results: $WT_OUT/result.txt (+ pop_*.png, field_*.png, win_*.png).
Lines starting with "NO ENTRY" are buttons without a popup.
"""
import faulthandler
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
_fault = open(os.path.join(OUT, "crash.txt"), "w")   # Python stack if FreeCAD crashes
faulthandler.enable(_fault, all_threads=True)


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


# one CAM dialog per FreeCAD start is reliable (see run_freecad_tests.sh); WT_CAM_OPS= skips CAM
CAM_OPS = [x for x in os.environ.get("WT_CAM_OPS", "CAM_Profile:").split(",") if x]


def show_tab_of(w):
    """Bring the tab page that contains widget w to the front."""
    child, p = w, w.parentWidget()
    while p is not None:
        if isinstance(p, QtWidgets.QStackedWidget) and isinstance(p.parentWidget(), QtWidgets.QTabWidget):
            p.parentWidget().setCurrentWidget(child)
        child, p = p, p.parentWidget()


def rest_on(wikitips, w):
    """Put the real cursor on a field and wait like a user would (the addon polls)."""
    QtGui.QCursor.setPos(w.mapToGlobal(w.rect().center()))
    pump(wikitips.REST_MS + 500)
    pop = wikitips._FILTER.popup
    return pop if (pop.isVisible() and pop._rect is not None) else None


def hover_fields(wikitips, mw, cmd):
    """Rest the mouse on every field of the open dialog that has help. Runs in its own
    scope so no Python wrapper of a dialog widget outlives the dialog."""
    failures = 0
    op = wikitips.current_op()
    names = sorted(wikitips._field_names())
    found, ok_n, shots = 0, 0, 0
    for n in names:
        for w in mw.findChildren(QtWidgets.QWidget, n):
            found += 1
            show_tab_of(w)
            pump(80)
            if not w.isVisible() or w.width() < 4:
                continue
            pop = rest_on(wikitips, w)
            if pop is None:
                failures += 1
                P("  FAIL %s %s: no popup" % (cmd, n))
                continue
            ok_n += 1
            if shots < 3 or n in ("stepDown", "clearingPattern", "cutMode", "cutSide", "peckEnabled", "stepOver"):
                pop.grab().save(os.path.join(OUT, "field_%s_%s.png" % (cmd, n)))
                shots += 1
            QtGui.QCursor.setPos(10, 10)   # move away: popup must close
            pump(400)
            if pop.isVisible():
                failures += 1
                P("  FAIL %s %s: popup stayed open" % (cmd, n))
    P("== %s (op=%s): %d fields with help, %d popups OK" % (cmd, op, found, ok_n))
    if found == 0:
        failures += 1
        P("  FAIL %s: dialog did not open or no fields found" % cmd)
    return failures


def close_dialog():
    """Close the task dialog the way the Cancel button does (programmatic
    resetEdit/closeDialog left CAM in a bad state even without WikiTips)."""
    dlg = Gui.Control.activeTaskDialog()
    if dlg is not None and hasattr(dlg, "reject"):
        dlg.reject()
    elif Gui.Control.activeDialog():
        Gui.Control.closeDialog()


def cam_fields(wikitips):
    """Open CAM operation dialogs and hover every field that has Greek help."""
    failures = 0
    Gui.activateWorkbench("CAMWorkbench")
    doc = App.newDocument("WikiTipsCAM")
    box = doc.addObject("Part::Box", "Box")
    box.Length, box.Width, box.Height = 60, 40, 15
    cyl = doc.addObject("Part::Cylinder", "Cyl")
    cyl.Radius, cyl.Height = 3, 20
    cyl.Placement.Base = App.Vector(30, 20, -2)
    cut = doc.addObject("Part::Cut", "Part")
    cut.Base, cut.Tool = box, cyl
    doc.recompute()
    import Path.Main.Gui.Job as JobGui
    job = JobGui.Create([cut], None, False)
    doc.recompute()
    pump(1500)
    model = job.Model.Group[0]
    mw = Gui.getMainWindow()
    for spec in CAM_OPS:
        cmd, face = (spec.split(":") + [""])[:2]
        Gui.Selection.clearSelection()
        if face:
            Gui.Selection.addSelection(model, face)
        else:
            Gui.Selection.addSelection(model)
        Gui.runCommand(cmd)
        pump(2800)   # dialog opens, then the 2 s scan finds its fields
        failures += hover_fields(wikitips, mw, cmd)   # keeps no Python wrappers of the dialog
        pump(300)
        close_dialog()
        pump(1500)
    return failures


def run():
    failures = 0
    try:
        import wikitips
        P("WikiTips loaded:", wikitips._FILTER is not None, "entries:", len(wikitips.data()))
        mw = Gui.getMainWindow()
        mw.resize(1600, 1000)
        for wb in ([] if os.environ.get("WT_SKIP_WB") else WORKBENCHES):
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
        if CAM_OPS:
            failures += cam_fields(wikitips)
        P("RESULT:", "PASS" if failures == 0 else "%d FAILURES" % failures)
    except Exception:
        P("EXCEPTION", traceback.format_exc())
    finally:
        log.close()
        QtCore.QTimer.singleShot(200, lambda: os._exit(0))


QtCore.QTimer.singleShot(4000, run)

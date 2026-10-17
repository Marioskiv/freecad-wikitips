# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test WikiTips "Σκαρίφημα σε κύλινδρο" (wrap) inside a REAL FreeCAD.

    WT_OUT=/tmp/wt xvfb-run -a freecad tests/freecad_wrap_test.py

Clicks a cylinder, presses the button, checks the tangent sketch opens there,
writes text and a circle in it, closes it and checks the wrapped result for
the three modes; also a wrong selection and save + reopen.
Results: $WT_OUT/result.txt (+ wrap_*.png).
"""
import faulthandler
import math
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from PySide import QtCore, QtWidgets

OUT = os.environ.get("WT_OUT", os.path.join(os.path.expanduser("~"), "wikitips-test"))
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, "result.txt"), "w", encoding="utf-8")
_fault = open(os.path.join(OUT, "crash.txt"), "w")
faulthandler.enable(_fault, all_threads=True)
V = App.Vector
failures = 0
FONT = next((f for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                         "C:/Windows/Fonts/arialbd.ttf") if os.path.isfile(f)), "")


def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n")
    log.flush()


def check(ok, what):
    global failures
    if not ok:
        failures += 1
    P("OK  " if ok else "FAIL", what)


def pump(ms):
    t = QtCore.QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)


def shot(name, fit=True):
    if fit:
        Gui.SendMsgToActiveView("ViewFit")
    pump(300)
    Gui.getMainWindow().grab().save(os.path.join(OUT, "wrap_%s.png" % name))


def run():
    import wikitips_errors as we
    import wikitips_knurl as wk
    import wikitips_wrap as ww
    mw = Gui.getMainWindow()
    mw.resize(1600, 1000)
    Gui.activateWorkbench("PartDesignWorkbench")
    pump(1500)
    check(we.find_button("WikiTips_Wrap")[0] is not None, "Wrap button on the WikiTips toolbar")

    doc = App.newDocument("Wrap")
    b = doc.addObject("PartDesign::Body", "Body")
    s = b.newObject("Sketcher::SketchObject", "Sketch")
    s.AttachmentSupport = [(b.Origin.OriginFeatures[3], "")]
    s.MapMode = "FlatFace"
    s.addGeometry(Part.Circle(V(0, 0, 0), V(0, 0, 1), 12))
    pad = b.newObject("PartDesign::Pad", "Pad")
    pad.Profile = s
    pad.Length = 30
    doc.recompute()
    Gui.activeView().viewIsometric()
    pump(400)
    names = ["Face%d" % (i + 1) for i in range(len(pad.Shape.Faces))]
    side = next(n for n, f in zip(names, pad.Shape.Faces) if wk.cylinder_of(f))
    top = next(n for n, f in zip(names, pad.Shape.Faces) if not wk.cylinder_of(f))

    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, "Pad", top, 0, 0, 30)
    Gui.runCommand("WikiTips_Wrap")
    pump(600)
    c = we._EXPLAINER.card
    check(c is not None and c.isVisible() and "κύλινδρο" in c.title.text(), "flat face: Greek card")
    check(doc.getObject("Wrap") is None, "flat face: nothing created")
    if c is not None:
        c.dismiss()

    # click on the side, 12 mm radius, at 45° and 15 mm high
    px, py = 12 * math.cos(math.radians(45)), 12 * math.sin(math.radians(45))
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, "Pad", side, px, py, 15)
    Gui.runCommand("WikiTips_Wrap")
    pump(1500)
    w, sk = doc.getObject("Wrap"), doc.getObject("WrapSketch")
    check(w is not None and sk is not None and w.TypeId == "PartDesign::FeaturePython", "Wrap + sketch in the Body")
    if w is None or sk is None:
        return
    vp = Gui.ActiveDocument.getInEdit()
    check(vp is not None and vp.Object == sk, "the sketch opens for drawing")
    o = sk.Placement.Base
    check(abs(math.hypot(o.x, o.y) - 12) < 1e-6 and abs(o.z - 15) < 1e-6 and
          abs(math.degrees(math.atan2(o.y, o.x)) - 45) < 1e-6, "sketch touches the cylinder where clicked (%s)" % o)
    check(len(sk.Geometry) == 4 and all(sk.getConstruction(i) for i in range(4)), "construction frame of the unrolled surface")
    shot("sketch_open", fit=False)

    # draw: text "CNC" and a circle, as the user would
    h = sk.addGeometry(Part.LineSegment(V(-10, -3, 0), V(10, -3, 0)), True)
    if FONT:
        sk.addConstraint(Sketcher.Constraint("Text", [h, 0], "CNC", FONT, False))
        sk.setTextAndFont(len(sk.Constraints) - 1, "CNC", FONT, False, False)
    sk.addGeometry(Part.Circle(V(16, 0, 0), V(0, 0, 1), 2))
    doc.recompute()
    pump(500)
    Gui.ActiveDocument.resetEdit()
    pump(800)
    doc.recompute()
    pump(1600)
    base = pad.Shape.Volume
    check("Invalid" not in w.State and w.Shape.isValid() and len(w.Shape.Solids) == 1,
          "engraved text + circle: one valid solid (%s)" % w.getStatusString())
    check(w.Shape.Volume < base - 5, "material cut %.1f mm³" % (base - w.Shape.Volume))
    check(b.Tip == w, "Wrap is the Tip")
    Gui.Selection.clearSelection()
    sk.ViewObject.Visibility = False
    shot("engrave")
    w.Mode = "Ανάγλυφο"
    doc.recompute()
    check(w.Shape.isValid() and w.Shape.Volume > base + 5, "raised: material added %.1f mm³" % (w.Shape.Volume - base))
    shot("raised")
    w.Mode = "Μέχρι τον άξονα"
    doc.recompute()
    check(w.Shape.isValid() and w.Shape.Volume < base - 50, "down to the axis")
    w.Mode = "Χάραξη"
    doc.recompute()

    path = os.path.join(OUT, "wrap.FCStd")
    doc.saveAs(path)
    App.closeDocument(doc.Name)
    pump(500)
    d2 = App.openDocument(path)
    pump(800)
    w = d2.getObject("Wrap")
    check(w is not None and isinstance(w.Proxy, ww.Wrap) and isinstance(w.ViewObject.Proxy, ww.ViewProviderWrap),
          "reopened file keeps the Wrap")
    d2.getObject("Pad").Length = 40      # an edit upstream: the wrap follows
    d2.recompute()
    check("Invalid" not in w.State and w.Shape.isValid(), "Wrap recomputes after an upstream edit")


try:
    run()
except Exception:
    failures += 1
    P("FAIL exception:\n" + traceback.format_exc())
P("RESULT:", "PASS" if failures == 0 else "%d FAILURES" % failures)
log.close()
os._exit(0)

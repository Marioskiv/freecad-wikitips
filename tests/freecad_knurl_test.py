# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test the WikiTips Knurl tool inside a REAL FreeCAD.

    WT_OUT=/tmp/wt xvfb-run -a freecad tests/freecad_knurl_test.py

Pads a circle in a Body, selects its side, presses the Knurl button, checks the
Greek panel and the fast preview, presses OK and checks the real teeth (one
valid solid, material removed). Also: a wrong selection gives the Greek card,
a Part cylinder works, the file saves and opens again.
Results: $WT_OUT/result.txt (+ knurl_*.png).
"""
import faulthandler
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtWidgets

OUT = os.environ.get("WT_OUT", os.path.join(os.path.expanduser("~"), "wikitips-test"))
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, "result.txt"), "w", encoding="utf-8")
_fault = open(os.path.join(OUT, "crash.txt"), "w")
faulthandler.enable(_fault, all_threads=True)
V = App.Vector
failures = 0


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


def shot(name):
    Gui.SendMsgToActiveView("ViewFit")
    pump(300)
    Gui.getMainWindow().grab().save(os.path.join(OUT, "knurl_%s.png" % name))


def run():
    import wikitips_knurl as wk
    import wikitips_errors as we
    mw = Gui.getMainWindow()
    mw.resize(1600, 1000)
    Gui.activateWorkbench("PartDesignWorkbench")
    pump(1500)
    btn, _ = we.find_button("WikiTips_Knurl")
    check(btn is not None, "Knurl button on the WikiTips toolbar")

    doc = App.newDocument("Knurl")
    b = doc.addObject("PartDesign::Body", "Body")
    s = b.newObject("Sketcher::SketchObject", "Sketch")
    s.AttachmentSupport = [(b.Origin.OriginFeatures[3], "")]
    s.MapMode = "FlatFace"
    s.addGeometry(Part.Circle(V(0, 0, 0), V(0, 0, 1), 10))
    pad = b.newObject("PartDesign::Pad", "Pad")
    pad.Profile = s
    pad.Length = 30
    doc.recompute()
    Gui.activeView().viewIsometric()
    pump(500)
    faces = {n: f for n, f in ((("Face%d" % (i + 1)), f) for i, f in enumerate(pad.Shape.Faces))}
    side = next(n for n, f in faces.items() if wk.cylinder_of(f))
    flat = next(n for n, f in faces.items() if not wk.cylinder_of(f))

    # wrong selection: a flat face -> Greek card, nothing created
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, "Pad", flat)
    Gui.runCommand("WikiTips_Knurl")
    pump(600)
    c = we._EXPLAINER.card
    check(c is not None and c.isVisible() and "κύλινδρο" in c.title.text(), "flat face: Greek card")
    check(doc.getObject("Knurl") is None, "flat face: nothing created")
    if c is not None:
        c.dismiss()

    # the right selection
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, "Pad", side)
    Gui.runCommand("WikiTips_Knurl")
    pump(1500)
    k = doc.getObject("Knurl")
    check(k is not None and k.TypeId == "PartDesign::FeaturePython", "Knurl feature in the Body")
    check(bool(Gui.Control.activeDialog()) and wk._PANEL is not None, "Greek panel open")
    if k is None or wk._PANEL is None:
        return
    check(abs(k.Pitch.Value - 1.0) < 1e-9, "default pitch for D20 = 1.0 mm (got %s)" % k.Pitch)
    check(k.Kind == "Ελαφρύ" and len(k.Shape.Edges) > 100, "fast preview with lines while editing")
    shot("preview")
    panel = wk._PANEL
    panel.start.setValue(5)
    panel.end.setValue(5)
    pump(500)
    t = time.time()
    panel.accept()
    pump(800)
    P("     real teeth in %.1f s" % (time.time() - t))
    check(not Gui.Control.activeDialog(), "panel closed")
    sh = k.Shape
    check(k.Kind == "Πραγματικό" and "Invalid" not in k.State, "real knurl computed (%s)" % k.getStatusString())
    check(sh.isValid() and len(sh.Solids) == 1, "one valid solid")
    removed = pad.Shape.Volume - sh.Volume
    check(200 < removed < 600, "material removed %.1f mm³" % removed)
    check(b.Tip == k, "Knurl is the Tip of the Body")
    Gui.Selection.clearSelection()
    shot("real")
    for o in (pad,):
        o.ViewObject.Visibility = False
    # a Pocket after the knurl still works (it is a normal Body feature)
    s2 = b.newObject("Sketcher::SketchObject", "Sketch001")
    s2.AttachmentSupport = [(b.Origin.OriginFeatures[3], "")]
    s2.MapMode = "FlatFace"
    s2.addGeometry(Part.Circle(V(0, 0, 0), V(0, 0, 1), 4))
    q = b.newObject("PartDesign::Pocket", "Pocket")
    q.Profile = s2
    q.Type = 1
    q.Reversed = True
    doc.recompute()
    check("Invalid" not in q.State and q.Shape.isValid(), "Pocket after the Knurl")
    shot("pocket_after")

    # Part workbench cylinder, lying along X
    cyl = doc.addObject("Part::Cylinder", "Cylinder")
    cyl.Radius, cyl.Height = 6, 25
    cyl.Placement = App.Placement(V(40, 0, 0), App.Rotation(V(0, 1, 0), 90))
    doc.recompute()
    face = next(f for f in cyl.Shape.Faces if wk.cylinder_of(f))
    k2 = wk.make_knurl(cyl, face)
    k2.Pattern = "Ίσιο"
    doc.recompute()
    check(k2.TypeId == "Part::FeaturePython" and k2.Shape.isValid() and cyl.Shape.Volume - k2.Shape.Volume > 50,
          "straight knurl on a Part cylinder")

    # save and open again
    path = os.path.join(OUT, "knurl.FCStd")
    doc.saveAs(path)
    App.closeDocument(doc.Name)
    pump(500)
    d2 = App.openDocument(path)
    pump(800)
    k = d2.getObject("Knurl")
    check(k is not None and isinstance(k.Proxy, wk.Knurl) and isinstance(k.ViewObject.Proxy, wk.ViewProviderKnurl),
          "reopened file keeps the Knurl (object + icon)")
    d2.recompute()
    check("Invalid" not in k.State and k.Shape.isValid(), "reopened Knurl recomputes")


try:
    run()
except Exception:
    failures += 1
    P("FAIL exception:\n" + traceback.format_exc())
P("RESULT:", "PASS" if failures == 0 else "%d FAILURES" % failures)
log.close()
os._exit(0)

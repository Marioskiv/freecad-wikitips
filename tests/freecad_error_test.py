# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test the error explainer and "show me where" inside a REAL FreeCAD.

    WT_OUT=/tmp/wt xvfb-run -a freecad tests/freecad_error_test.py

Makes the usual beginner mistakes (open sketch, conflicting constraints, a
Pocket that misses, a Body split in two, a CAM height error in the Report
view), checks that the Greek card says the right thing, clicks a command link
and checks that the real button gets outlined. Results: $WT_OUT/result.txt
(+ err_*.png screenshots).
"""
import faulthandler
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

# messages seen in FreeCAD 26.3 (probe 2026-10-17) or taken from its source -> rule id
MESSAGES = [
    ("Wire is not closed.", "PartDesign::Pad", "open_wire"),
    ("Sketch with conflicting constraints\nRemove at least one of the following conflicting constraints:1\n, 2\n",
     "Sketcher::SketchObject", "conflicting"),
    ("Sketch with redundant constraints\nRemove the following redundant constraint:\n2\n\n",
     "Sketcher::SketchObject", "redundant"),
    ("Revolve axis intersects the sketch", "PartDesign::Revolution", "revolve_axis"),
    ("Cannot create a pad with a total length of zero.", "PartDesign::Pad", "zero_length"),
    ("Hole error: Finding axis failed", "PartDesign::Hole", "hole_axis"),
    ("Hole error: Hole cut depth must be less than hole depth", "PartDesign::Hole", "hole_values"),
    ("Linked object is not a Part object", "Part::Cut", "missing_link"),
    ("AttachEngine3D: subshape not found Pad.Face99", "Sketcher::SketchObject", "attach"),
    ("Result has multiple solids: enable 'Allow Compound' in the active body.", "PartDesign::Pad", "multi_solid"),
    ("Resulting shape is not a solid", "PartDesign::Pocket", "not_solid"),
    ("Error: There is nothing to subtract", "PartDesign::Pocket", "nothing_to_cut"),
    ("Failed to create chamfer", "PartDesign::Chamfer", "fillet"),
    ("BRep_API: command not done", "PartDesign::Fillet", "fillet"),
    ("Loft: Failed to create shell", "PartDesign::AdditiveLoft", "loft_pipe"),
    ("Error: Thread could not be built", "PartDesign::Hole", "thread"),
    ("No features selected to be patterned.", "PartDesign::LinearPattern", "pattern"),
    ("Creation failed because direction is orthogonal to sketch's normal vector", "PartDesign::Pad", "direction"),
    ("Error: pitch too small!", "PartDesign::AdditiveHelix", "zero_length"),
    ("Something nobody has seen", "PartDesign::Pad", "_generic"),
]
LOG_LINES = [
    ("Profile: Start depth is above safe height", "cam_heights"),
    ("No Tool Controller selected.", "cam_tool"),
    ("No depth to cut for: Pocket\n", "cam_depth"),
    ("No valid faces or edges found in base geometry.", "cam_geometry"),
    ("Recompute failed! Please check report view.", None),
    ("Wire is not closed.", None),   # document errors are explained from the object, not the log
]


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


def rect(x0, y0, x1, y1):
    p = [V(x0, y0, 0), V(x1, y0, 0), V(x1, y1, 0), V(x0, y1, 0)]
    return [Part.LineSegment(p[i], p[(i + 1) % 4]) for i in range(4)]


def body(doc):
    return doc.addObject("PartDesign::Body", "Body")


def sketch(b, geos):
    s = b.newObject("Sketcher::SketchObject", "Sketch")
    s.AttachmentSupport = [(b.Origin.OriginFeatures[3], "")]
    s.MapMode = "FlatFace"
    for g in geos:
        s.addGeometry(g)
    return s


def pad(b, s, length=5, name="Pad"):
    p = b.newObject("PartDesign::Pad", name)
    p.Profile = s
    p.Length = length
    return p


def card():
    import wikitips_errors
    return wikitips_errors._EXPLAINER.card


def shown(title_part, what, shot):
    c = card()
    ok = c is not None and c.isVisible() and title_part in c.title.text()
    check(ok, "%s: card '%s' (got %r)" % (what, title_part, c.title.text() if c is not None and c.isVisible() else None))
    if ok:
        Gui.getMainWindow().grab().save(os.path.join(OUT, "err_%s.png" % shot))
        c.grab().save(os.path.join(OUT, "card_%s.png" % shot))
    return ok


def run():
    import wikitips_errors as we
    mw = Gui.getMainWindow()
    mw.resize(1600, 1000)
    Gui.activateWorkbench("CAMWorkbench")   # registers the CAM commands linked in the CAM rules
    pump(1500)
    Gui.activateWorkbench("PartDesignWorkbench")
    pump(1500)

    # 1) rules: every known message gets the right Greek explanation
    for msg, typ, want in MESSAGES:
        r = we.explain(msg, typ)
        check(r is not None and r["id"] == want, "rule %-14s <- %r (got %s)" % (want, msg[:50], r and r["id"]))
    for line, want in LOG_LINES:
        r = we.explain(line, src="log")
        check((r["id"] if r else None) == want, "log rule %s <- %r" % (want, line))
    check(we.constraint_numbers(MESSAGES[1][0]) == ["1", "2"], "constraint numbers 1, 2")
    import re
    for r in we.rules():   # every command link in the steps must exist
        for cmd in re.findall(r"\{([A-Za-z]+_[A-Za-z0-9_]+)\}", " ".join(r.get("fix", []))):
            check(Gui.Command.get(cmd) is not None, "command exists: %s (rule %s)" % (cmd, r["id"]))
        if r.get("i"):
            check(os.path.isfile(os.path.join(we.wt.CONTENT_IMG_DIR, r["i"])), "image exists: %s" % r["i"])

    # 2) open sketch -> Pad turns red -> card
    doc = App.newDocument("OpenPad")
    b = body(doc)
    s = sketch(b, rect(0, 0, 10, 10)[:3])
    pad(b, s)
    doc.recompute()
    pump(1600)
    if shown("δεν είναι κλειστό", "open sketch", "open_wire"):
        c = card()
        check("Pad" in c.where.text(), "card names the red feature (%r)" % c.where.text())
        check("cmd:Sketcher_ValidateSketch" in c.text.text(), "card links Validate sketch")
        # a Sketcher button outside a sketch: the card explains where it is
        c._link("cmd:Sketcher_CreateCircle")
        pump(300)
        check("σκαρίφημα" in c.note.text(), "show me where, hidden button: hint %r" % c.note.text())
        # 3) show me where: the Pad button gets an amber outline
        btn, _ = we.find_button("PartDesign_Pad")
        check(btn is not None, "find_button PartDesign_Pad")
        c._link("cmd:PartDesign_Pad")
        pump(250)
        outs = [w for w in mw.findChildren(QtWidgets.QWidget) if isinstance(w, we.Outline) and w.isVisible()]
        if btn is not None and outs:
            g = outs[0].geometry()
            centre = btn.mapTo(mw, btn.rect().center())
            check(g.contains(centre), "outline around the Pad button")
            mw.grab().save(os.path.join(OUT, "err_show_me.png"))
        else:
            check(False, "outline visible")
        pump(3200)
        check(not any(isinstance(w, we.Outline) and w.isVisible() for w in mw.findChildren(QtWidgets.QWidget)),
              "outline goes away by itself")
    # fixing the sketch hides the card
    s.addGeometry(rect(0, 0, 10, 10)[3])
    doc.recompute()
    pump(1600)
    check(not card().isVisible(), "card hides when the error is fixed")
    App.closeDocument(doc.Name)

    # 4) conflicting constraints, with their numbers
    doc = App.newDocument("OverCons")
    b = body(doc)
    s = sketch(b, rect(0, 0, 10, 10))
    s.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 10))
    s.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 12))
    doc.recompute()
    pump(1600)
    if shown("συγκρούονται", "conflicting constraints", "conflicting"):
        check("1, 2" in card().text.text(), "card shows constraint numbers")
        # closing the card: the same error does not come back
        card().close_btn.click()
        pump(200)
        doc.recompute()
        pump(1600)
        check(not card().isVisible(), "closed card stays closed for the same error")
    App.closeDocument(doc.Name)

    # 5) a Pocket that misses the solid: no error from FreeCAD, but nothing changed
    doc = App.newDocument("PocketMiss")
    b = body(doc)
    pad(b, sketch(b, rect(0, 0, 10, 10)))
    doc.recompute()
    pump(1200)
    q = b.newObject("PartDesign::Pocket", "Pocket")
    q.Profile = sketch(b, rect(30, 0, 40, 10))
    q.Length = 5
    doc.recompute()
    pump(1600)
    shown("δεν άλλαξε τίποτα", "pocket that misses", "nochange")
    App.closeDocument(doc.Name)

    # 6) a second Pad that does not touch the first: the Body splits in two
    doc = App.newDocument("TwoSolids")
    b = body(doc)
    pad(b, sketch(b, rect(0, 0, 10, 10)))
    doc.recompute()
    pump(1200)
    pad(b, sketch(b, rect(30, 0, 40, 10)), name="Pad001")
    doc.recompute()
    pump(1600)
    shown("χωρίστηκε σε 2", "body split in two", "split")
    App.closeDocument(doc.Name)
    pump(800)

    # 7) CAM error in the Report view
    App.Console.PrintError("Profile: Start depth is above safe height\n")
    pump(2500)
    if shown("ύψη", "CAM error in the Report view", "cam_heights"):
        check(not card().image.isHidden(), "CAM card shows the heights animation")

    # 8) switched off: no card
    we.wt.params().SetBool("ExplainErrors", False)
    pump(1000)
    check(not card().isVisible(), "ExplainErrors off hides the card")
    we.wt.params().SetBool("ExplainErrors", True)


try:
    run()
except Exception:
    failures += 1
    P("FAIL exception:\n" + traceback.format_exc())
P("RESULT:", "PASS" if failures == 0 else "%d FAILURES" % failures)
log.close()
os._exit(0)

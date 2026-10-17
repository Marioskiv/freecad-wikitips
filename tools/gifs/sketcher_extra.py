# SPDX-License-Identifier: LGPL-2.1-or-later
"""Sketcher scenes for the buttons that still showed the English wiki text (2026-10-17).

    QT_SCALE_FACTOR=1.5 WT_OUT=<dir> [WT_ONLY=...] xvfb-run -a freecad tools/gifs/sketcher_extra.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/sketcher

Same recorder as sketcher_rec.py / sketcher_more.py (it registers all their scenes too).
Where the button only changes what is shown, the real command is run (Gui.runCommand) so
the picture is what FreeCAD 26.3 really draws.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App  # noqa: E402
import FreeCADGui as Gui  # noqa: E402
import Part  # noqa: E402
import Sketcher  # noqa: E402

import sketcher_more as M  # noqa: E402  (registers the other scenes and starts the run timer)
from sketcher_rec import Rec, pump, rubber, scene  # noqa: E402

V = App.Vector
C = Sketcher.Constraint
GEN = "User parameter:BaseApp/Preferences/Mod/Sketcher/General"


def run_cmd(name):
    Gui.runCommand(name, 0)
    pump(300)


def select(r, subs):
    for s in subs:
        Gui.Selection.addSelection(r.doc.Name, r.sk.Name, s)


def bspline_info(name, param, text, weights=False):
    """Visual helper toggles for B-splines: off at the start, the button turns it on."""
    @scene(name)
    def _s():
        g = App.ParamGet(GEN)
        old = g.GetBool(param, False)
        g.SetBool(param, False)
        r = Rec(name, center=(20, 10), height=44)
        b = M.bspline(r, [(2, 2), (8, 18), (16, 4), (24, 20), (30, 4), (38, 16)])[0]
        if weights:
            r.doc.recompute()
        r.edit()
        r.apply(lambda: run_cmd(name), 1, text, 2200)
        r.save()
        g.SetBool(param, old)
    return _s


bspline_info("Sketcher_BSplinePolygon", "BSplineControlPolygonVisible", "Φαίνεται το πολύγωνο ελέγχου")
bspline_info("Sketcher_BSplineComb", "BSplineCombVisible", "Χτένα καμπυλότητας: μακριά δόντια = απότομη στροφή")
bspline_info("Sketcher_BSplineDegree", "BSplineDegreeVisible", "Φαίνεται ο βαθμός της καμπύλης")
bspline_info("Sketcher_BSplinePoleWeight", "BSplinePoleWeightVisible", "Φαίνεται το βάρος κάθε σημείου ελέγχου")
bspline_info("Sketcher_BSplineKnotMultiplicity", "BSplineKnotMultiplicityVisible",
             "Φαίνεται η πολλαπλότητα κάθε κόμβου")


@scene("Sketcher_ArcOverlay")
def s_arc_overlay():
    g = App.ParamGet(GEN)
    old = g.GetBool("ArcCircleHelperVisible", False)
    g.SetBool("ArcCircleHelperVisible", False)
    r = Rec("Sketcher_ArcOverlay", center=(20, 10), height=44)
    r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(20, 8, 0), V(0, 0, 1), 10), 0.2, 2.6))
    r.line((2, -2), (38, -2))
    r.edit()
    r.apply(lambda: run_cmd("Sketcher_ArcOverlay"), 1, "Φαίνεται ο κύκλος πίσω από κάθε τόξο", 2400)
    r.save()
    g.SetBool("ArcCircleHelperVisible", old)


@scene("Sketcher_Grid")
def s_grid():
    r = Rec("Sketcher_Grid", center=(20, 10), height=44, tool_first=False)
    r.rect(6, 2, 34, 18)
    r.edit()

    # 26.3: no toolbar button any more, it is in the sketch's task panel
    r.cap(1, "Πλέγμα: ανοιχτό")
    r.hold(900)
    r.apply(lambda: run_cmd("Sketcher_Grid"), 2, "Πλέγμα: κλειστό (ξανά: ανοίγει)", 2200)
    r.save()


@scene("Sketcher_Snap")
def s_snap():
    r = Rec("Sketcher_Snap", center=(20, 10), height=44, tool_first=False)
    r.edit()
    r.cap(1, "Με κούμπωμα στο πλέγμα, τα κλικ πέφτουν σε κόμβους")
    step = 10.0

    def snapped(x, y):
        return [r.line((0, 0), (round(x / step) * step, round(y / step) * step))]
    r.click(0, 0)
    rubber(r, snapped, [(4, 3), (31, 17)], 8)
    M.done(r, 2, "Το άκρο κάθεται ακριβώς σε κόμβο του πλέγματος")
    r.save()


@scene("Sketcher_RenderingOrder")
def s_order():
    g = App.ParamGet(GEN)
    old = (g.GetInt("TopRenderGeometryId", 1), g.GetInt("MidRenderGeometryId", 2))
    g.SetInt("TopRenderGeometryId", 1)       # 1 normal, 2 construction, 3 external
    g.SetInt("MidRenderGeometryId", 2)
    r = Rec("Sketcher_RenderingOrder", center=(20, 10), height=30, tool_first=False)
    r.line((4, 10), (36, 10))
    r.line((4, 10), (36, 10), construction=True)
    r.edit()
    r.events.append({"t": "panel", "title": "Σειρά σχεδίασης", "mono": False, "pos": "left",
                     "lines": ["Κανονική (μαύρη)", "Βοηθητική (μπλε)", "Εξωτερική"]})
    r.cap(1, "Σύρε στην κορυφή ό,τι θες μπροστά")
    r.events.append({"t": "pick", "row": 1})
    r.hold(1200)
    r.events.append({"t": "panel"})

    def swap():
        g.SetInt("TopRenderGeometryId", 2)
        g.SetInt("MidRenderGeometryId", 1)
        pump(300)
    r.apply(swap, 2, "Τώρα μπροστά φαίνεται η μπλε", 2200)
    r.save()
    g.SetInt("TopRenderGeometryId", old[0])
    g.SetInt("MidRenderGeometryId", old[1])


@scene("Sketcher_CancelSketch")
def s_cancel():
    r = Rec("Sketcher_CancelSketch", center=(20, 10), height=44, tool_first=False)
    r.rect(6, 2, 34, 18)
    r.edit()
    r.cap(1, "Έκανες αλλαγές που δεν θες")
    c = r.circle((20, 10), 5)
    r.img(blend=True)
    r.hold(900)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.apply(lambda: r.sk.delGeometry(c), 3, "Βγαίνει χωρίς να κρατήσει τις αλλαγές", 2200)
    r.save()


@scene("Sketcher_StopOperation")
def s_stop():
    r = Rec("Sketcher_StopOperation", center=(20, 10), height=44, tool_first=False)
    r.edit()
    r.cap(1, "Ένα εργαλείο σχεδίασης δουλεύει ακόμα")
    r.click(4, 4)
    ids = rubber(r, lambda x, y: [r.line((4, 4), (x, y))], [(10, 8), (30, 14)], 5)
    r.cap(2, "Πάτα το κουμπί (ή Esc)")
    r.press()

    def stop():
        for g in sorted(ids, reverse=True):
            r.sk.delGeometry(g)
    r.apply(stop, 3, "Το εργαλείο σταμάτησε, ο κέρσορας είναι πάλι βελάκι", 2000)
    r.save()


def copy_like(name, clone, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(22, 10), height=48, tool_first=False)
        c = r.circle((8, 10), 4)
        a = r.sk.addConstraint(C("Radius", c, 4))
        r.edit()
        r.cap(1, "Επίλεξε τη γεωμετρία")
        r.click(12, 10, "Edge%d" % (c + 1))
        r.cap(2, "Πάτα το κουμπί")
        r.press()
        r.cap(3, "Κλικ στο νέο σημείο")
        r.click(30, 10)
        r.apply(lambda: r.sk.addCopy([c], V(22, 0, 0), clone), 4, text, 2200)
        r.save()
        del a
    return _s


copy_like("Sketcher_Copy", False, "Αντίγραφο, ανεξάρτητο από το αρχικό")
copy_like("Sketcher_Clone", True, "Κλώνος: ίσος με το αρχικό (αλλάζει μαζί του)")


@scene("Sketcher_Move")
def s_move():
    r = Rec("Sketcher_Move", center=(22, 10), height=48, tool_first=False)
    c = r.circle((8, 10), 4)
    r.edit()
    r.cap(1, "Επίλεξε τη γεωμετρία")
    r.click(12, 10, "Edge%d" % (c + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.cap(3, "Κλικ στη νέα θέση")
    r.click(30, 10)
    r.apply(lambda: r.sk.addMove([c], V(22, 0, 0)), 4, "Μετακινήθηκε (με τους περιορισμούς του)", 2000)
    r.save()


@scene("Sketcher_RectangularArray")
def s_array():
    r = Rec("Sketcher_RectangularArray", center=(20, 6), height=50, tool_first=False)
    c = r.circle((5, 16), 2.5)
    r.edit()
    r.cap(1, "Επίλεξε τη γεωμετρία")
    r.click(7.5, 16, "Edge%d" % (c + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.events.append({"t": "panel", "title": "Ορθογώνια διάταξη", "mono": False,
                     "lines": ["Στήλες: 4", "Γραμμές: 3", "Ίσες αποστάσεις ✓"]})
    r.cap(3, "Γράψε στήλες και γραμμές")
    r.hold(1500)
    r.events.append({"t": "panel"})
    r.cap(4, "Κλικ: η απόσταση ως τη 2η στήλη")
    r.click(15, 16)
    r.apply(lambda: r.sk.addRectangularArray([c], V(10, 0, 0), False, 4, 3, False, 1.0), 5,
            "4 × 3 αντίγραφα σε πλέγμα", 2200)
    r.save()


@scene("Sketcher_ConstrainCoincident")
def s_coincident():
    r = Rec("Sketcher_ConstrainCoincident", center=(20, 10), height=44)
    a = r.line((4, 4), (18, 14))
    b = r.line((22, 12), (36, 4))
    r.edit()
    r.cap(1, "Κλικ στο άκρο της 1ης")
    r.click(18, 14)
    r.cap(2, "Κλικ στο άκρο της 2ης")
    r.click(22, 12)
    r.apply(lambda: r.sk.addConstraint(C("Coincident", a, 2, b, 1)), 3, "Τα δύο σημεία έγιναν ένα")
    r.save()


@scene("Sketcher_ConstrainPointOnObject")
def s_point_on():
    r = Rec("Sketcher_ConstrainPointOnObject", center=(20, 10), height=44)
    a = r.line((2, 4), (38, 4))
    b = r.line((14, 18), (24, 10))
    r.edit()
    r.cap(1, "Κλικ σε σημείο")
    r.click(24, 10)
    r.cap(2, "Κλικ στη γραμμή")
    r.click(32, 4)
    r.apply(lambda: r.sk.addConstraint(C("PointOnObject", b, 2, a)), 3, "Το σημείο κάθεται πάνω στη γραμμή")
    r.save()


@scene("Sketcher_ConstrainSnellsLaw")
def s_snell():
    r = Rec("Sketcher_ConstrainSnellsLaw", center=(20, 10), height=48, tool_first=False)
    iface = r.line((0, 10), (40, 10), construction=True)
    a = r.line((6, 22), (18, 10))
    b = r.line((21, 10), (30, -2))
    r.edit()
    r.cap(1, "Κλικ: άκρο της 1ης ακτίνας")
    r.click(18, 10, "Vertex%d" % (2 * a + 2))
    r.cap(2, "Κλικ: άκρο της 2ης ακτίνας")
    r.click(21, 10, "Vertex%d" % (2 * b + 1))
    r.cap(3, "Κλικ: η επιφάνεια (γραμμή)")
    r.click(36, 10, "Edge%d" % (iface + 1))
    r.cap(4, "Πάτα το κουμπί, γράψε n2/n1")
    r.press()
    r.apply(lambda: r.sk.addConstraint(C("SnellsLaw", a, 2, b, 1, iface, 1.5)), 5,
            "Η 2η ακτίνα «σπάει» σωστά (διάθλαση)", 2200)
    r.save()


def delete_all(name, fn, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(20, 10), height=44, tool_first=False)
        ids = r.rect(6, 2, 34, 18)
        r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 28))
        r.sk.addConstraint(C("DistanceY", ids[1], 1, ids[1], 2, 16))
        r.edit()
        r.cap(1, "Πάτα το κουμπί")
        r.press()
        r.cap(2, "Ερώτηση: «Ναι»")
        r.hold(900)
        r.apply(lambda: fn(r.sk), 3, text, 2200)
        r.save()
    return _s


delete_all("Sketcher_DeleteAllConstraints", lambda s: s.deleteAllConstraints(),
           "Έφυγαν όλοι οι περιορισμοί, οι γραμμές μένουν")
delete_all("Sketcher_DeleteAllGeometry", lambda s: s.deleteAllGeometry(), "Άδειασε όλο το σκαρίφημα")


def select_cmd(name, build, text, sel_first=None):
    @scene(name)
    def _s():
        r = Rec(name, center=(20, 10), height=46, tool_first=False)
        build(r)
        r.edit()
        r.cap(1, "Πάτα το κουμπί")
        r.press()
        r.apply(lambda: (Gui.Selection.clearSelection(), run_cmd(name)), 2, text, 2400)
        r.save()
    return _s


def conflicting(r):
    ids = r.rect(6, 2, 34, 18)
    r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 28))
    r.sk.addConstraint(C("Distance", ids[0], 22))


def redundant(r):
    ids = r.rect(6, 2, 34, 18)
    r.sk.addConstraint(C("Horizontal", ids[0]))


def free(r):
    ids = r.rect(6, 2, 34, 18)
    r.sk.addConstraint(C("Coincident", ids[0], 1, -1, 1))
    r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 28))
    r.circle((40, 10), 3)


select_cmd("Sketcher_SelectConflictingConstraints", conflicting, "Επιλέχθηκαν οι περιορισμοί που συγκρούονται")
select_cmd("Sketcher_SelectRedundantConstraints", redundant, "Επιλέχθηκε ο περιορισμός που περισσεύει")
select_cmd("Sketcher_SelectElementsWithDoFs", free, "Επιλέχθηκαν όσα κουνιούνται ακόμα (λείπουν περιορισμοί)")
select_cmd("Sketcher_SelectHorizontalAxis", lambda r: r.rect(6, 2, 34, 18), "Επιλέχθηκε ο οριζόντιος άξονας (X)")
select_cmd("Sketcher_SelectVerticalAxis", lambda r: r.rect(6, 2, 34, 18), "Επιλέχθηκε ο κάθετος άξονας (Y)")
select_cmd("Sketcher_SelectOrigin", lambda r: r.rect(6, 2, 34, 18), "Επιλέχθηκε η αρχή (0,0)")


@scene("Sketcher_SwitchVirtualSpace")
def s_virtual():
    r = Rec("Sketcher_SwitchVirtualSpace", center=(20, 10), height=46, tool_first=False)
    ids = r.rect(6, 2, 34, 18)
    k = r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 28))
    r.edit()
    r.cap(1, "Επίλεξε τον περιορισμό")
    r.click(20, 0, "Constraint%d" % (k + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.apply(lambda: r.sk.setVirtualSpace(k, True), 3, "Κρύφτηκε (υπάρχει ακόμα, απλώς δεν φαίνεται)", 2200)
    r.save()


@scene("Sketcher_RestoreInternalAlignmentGeometry")
def s_internal():
    r = Rec("Sketcher_RestoreInternalAlignmentGeometry", center=(20, 10), height=44, tool_first=False)
    e = r.sk.addGeometry(Part.Ellipse(V(20, 10, 0), 14, 7))
    r.doc.recompute()
    r.sk.exposeInternalGeometry(e)
    r.doc.recompute()
    r.edit()
    r.cap(1, "Επίλεξε την έλλειψη")
    r.click(34, 10, "Edge%d" % (e + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.apply(lambda: r.sk.deleteUnusedInternalGeometry(e), 3, "Έφυγαν οι βοηθητικές γραμμές (άξονες, εστίες)")
    r.cap(4, "Ξανά: επιστρέφουν")
    r.press()
    r.apply(lambda: r.sk.exposeInternalGeometry(e), 4, "Ξανά: επιστρέφουν")
    r.save()


@scene("Sketcher_ChangeDimensionConstraint")
def s_edit_value():
    r = Rec("Sketcher_ChangeDimensionConstraint", center=(22, 10), height=46, tool_first=False)
    ids = r.rect(6, 2, 30, 18)
    k = r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 24))
    r.edit()
    r.cap(1, "Επίλεξε τη διάσταση")
    r.click(18, 0, "Constraint%d" % (k + 1))
    r.cap(2, "Πάτα το κουμπί, γράψε 32")
    r.press()
    r.apply(lambda: r.sk.setDatum(k, App.Units.Quantity("32 mm")), 3, "Η τιμή άλλαξε, το σχήμα ακολουθεί")
    r.save()


@scene("Sketcher_CopyClipboard")
def s_copy_clip():
    r = Rec("Sketcher_CopyClipboard", center=(20, 10), height=44, tool_first=False)
    c = r.circle((12, 10), 5)
    r.edit()
    r.cap(1, "Επίλεξε τη γεωμετρία")
    r.click(17, 10, "Edge%d" % (c + 1))
    r.cap(2, "Πάτα το κουμπί (Ctrl+C)")
    r.press()
    r.hold(700)
    r.apply(lambda: None, 3, "Αντιγράφηκε: Ctrl+V σε αυτό ή άλλο σκαρίφημα", 2200)
    r.save()


@scene("Sketcher_Cut")
def s_cut():
    r = Rec("Sketcher_Cut", center=(20, 10), height=44, tool_first=False)
    c = r.circle((12, 10), 5)
    r.rect(24, 4, 36, 16)
    r.edit()
    r.cap(1, "Επίλεξε τη γεωμετρία")
    r.click(17, 10, "Edge%d" % (c + 1))
    r.cap(2, "Πάτα το κουμπί (Ctrl+X)")
    r.press()
    r.apply(lambda: r.sk.delGeometry(c), 3, "Έφυγε από εδώ, περιμένει Ctrl+V")
    r.save()


@scene("Sketcher_Paste")
def s_paste():
    r = Rec("Sketcher_Paste", center=(20, 10), height=44)
    r.rect(24, 4, 36, 16)
    r.edit()
    r.apply(lambda: (r.circle((12, 10), 5), r.sk.addConstraint(C("Radius", len(r.sk.Geometry) - 1, 5))), 1,
            "Μπαίνει ό,τι αντέγραψες, στην ίδια θέση", 2200)
    r.save()


@scene("Sketcher_ProfilesHexagon1")
def s_hexagon():
    r = Rec("Sketcher_ProfilesHexagon1", center=(0, 0), height=110)
    r.edit()

    def make():
        from ProfileLib import Hexagon
        Hexagon.makeHexagonSimple(r.sk.Name)
    r.apply(make, 1, "Εξάγωνο με έτοιμους περιορισμούς (ίσες πλευρές, 120°)", 2400)
    r.save()


# --- outside edit mode: whole sketches ------------------------------------------------
def outside(r, iso=False):
    """Like Rec.edit() but the sketch is not opened: tools that work on whole sketches."""
    r.doc.recompute()
    pump(300)
    r.v = Gui.ActiveDocument.ActiveView
    r.v.setCameraType("Orthographic")
    if iso:
        r.v.viewIsometric()
        r.v.fitAll()
        cam = r.v.getCameraNode()
        cam.height.setValue(cam.height.getValue() * 1.6)
    else:
        r.v.viewTop()
        cam = r.v.getCameraNode()
        cam.position.setValue(r.center[0], r.center[1], 100)
        cam.height.setValue(r.height)
    pump(300)
    r.W, r.H = r.v.getSize()
    for o in r.doc.Objects:
        try:
            o.ViewObject.LineWidth = 4
            o.ViewObject.PointSize = 8
        except Exception:
            pass
    r.img()


def sketch_with(doc, name, build):
    s = doc.addObject("Sketcher::SketchObject", name)
    build(s)
    return s


@scene("Sketcher_MergeSketches")
def s_merge():
    r = Rec("Sketcher_MergeSketches", center=(20, 10), height=44, tool_first=False)
    r.circle((10, 10), 5)
    other = sketch_with(r.doc, "Other", lambda s: s.addGeometry(Part.Circle(V(30, 10, 0), V(0, 0, 1), 5)))
    outside(r)
    r.cap(1, "Επίλεξε 2 ή περισσότερα σκαριφήματα")
    r.click(15, 10)
    Gui.Selection.addSelection(r.doc.Name, r.sk.Name)
    r.click(35, 10)
    Gui.Selection.addSelection(r.doc.Name, other.Name)
    r.img()
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def merge():
        Gui.Selection.clearSelection()
        m = sketch_with(r.doc, "Merged", lambda s: (s.addGeometry(Part.Circle(V(10, 10, 0), V(0, 0, 1), 5)),
                                                    s.addGeometry(Part.Circle(V(30, 10, 0), V(0, 0, 1), 5))))
        r.sk.ViewObject.Visibility = other.ViewObject.Visibility = False
        m.ViewObject.LineWidth = 4
        m.ViewObject.LineColor = (0.06, 0.73, 0.51)
    r.apply(merge, 3, "Νέο σκαρίφημα με όλα μαζί (τα αρχικά κρύβονται)", 2400)
    r.save()


@scene("Sketcher_MirrorSketch")
def s_mirror_sketch():
    r = Rec("Sketcher_MirrorSketch", center=(0, 0), height=60, tool_first=False)
    r.line((4, 4), (20, 4))
    r.line((20, 4), (8, 18))
    r.line((8, 18), (4, 4))
    outside(r)
    r.cap(1, "Επίλεξε το σκαρίφημα")
    r.click(12, 4)
    Gui.Selection.addSelection(r.doc.Name, r.sk.Name)
    r.img()
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.events.append({"t": "panel", "title": "Καθρέφτισμα ως προς", "mono": False,
                     "lines": ["Άξονα X", "Άξονα Y", "Αρχή (0,0)"]})
    r.events.append({"t": "pick", "row": 1})
    r.hold(900)
    r.events.append({"t": "panel"})

    def mirror():
        Gui.Selection.clearSelection()
        m = sketch_with(r.doc, "Mirrored", lambda s: [s.addGeometry(Part.LineSegment(V(-a, b, 0), V(-c, d, 0)))
                                                      for a, b, c, d in ((4, 4, 20, 4), (20, 4, 8, 18), (8, 18, 4, 4))])
        m.ViewObject.LineWidth = 4
        m.ViewObject.LineColor = (0.06, 0.73, 0.51)
    r.apply(mirror, 3, "Νέο σκαρίφημα, καθρέφτης ως προς τον άξονα Y", 2400)
    r.save()


@scene("Sketcher_ReorientSketch")
def s_reorient():
    r = Rec("Sketcher_ReorientSketch", tool_first=False)
    r.rect(0, 0, 30, 20)
    outside(r, iso=True)
    r.cap(1, "Επίλεξε το σκαρίφημα")
    r.events.append({"t": "click"})
    Gui.Selection.addSelection(r.doc.Name, r.sk.Name)
    r.img()
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.events.append({"t": "panel", "title": "Επίπεδο", "mono": False, "lines": ["XY", "XZ", "YZ", "Απόσταση: 0 mm"]})
    r.events.append({"t": "pick", "row": 1})
    r.hold(900)
    r.events.append({"t": "panel"})

    def turn():
        Gui.Selection.clearSelection()
        r.sk.Placement = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), 90))
    r.apply(turn, 3, "Το σκαρίφημα πήγε στο επίπεδο XZ", 2400)
    r.save()

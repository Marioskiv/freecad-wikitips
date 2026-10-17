# SPDX-License-Identifier: LGPL-2.1-or-later
"""The rest of the Part Design / Part toolbars (and the 3D Sketcher buttons), recorded in a
REAL FreeCAD with the part_rec.py recorder.

    WT_OUT=<dir> WT_ONLY=PartDesign_Pad,... xvfb-run -a freecad tools/gifs/part_more.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/part

Pattern of every scene: what to select (clicks) → press the toolbar button → the result,
made with the same FreeCAD objects the command makes. Colours: part slate, sketch/profile
amber, the result indigo (part_rec.py).
"""
import math
import os
import sys

os.environ["WT_NO_AUTORUN"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App  # noqa: E402
import FreeCADGui as Gui  # noqa: E402
import Part  # noqa: E402
from PySide import QtCore  # noqa: E402

import part_rec as P  # noqa: E402
from part_rec import (BASE, RESULT, Rec, circle_geo, color, face_where, hide,  # noqa: E402
                      rect_geo, scene, sketch_on, top_face)

V = App.Vector
SK = (0.96, 0.62, 0.04)


def style_sketch(sk):
    try:
        sk.ViewObject.LineColor = SK
        sk.ViewObject.PointColor = SK
        sk.ViewObject.LineWidth = 5
        sk.ViewObject.Visibility = True
    except Exception:
        pass


def body_with(r, plate=True, name="Body"):
    body = r.doc.addObject("PartDesign::Body", name)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    pad = None
    if plate:
        sk = sketch_on(body, 0, rect_geo(-30, -20, 30, 20))
        pad = body.newObject("PartDesign::Pad", "Pad")
        pad.Profile, pad.Length = sk, 10
        sk.Visibility = False
    r.doc.recompute()
    color(body, BASE)
    return body, pad


def sk_on(body, plane, geo, z=0.0):
    sk = sketch_on(body, plane, geo)
    sk.AttachmentOffset = App.Placement(V(0, 0, z), App.Rotation())
    body.Document.recompute()
    style_sketch(sk)
    return sk


def recolor(body):
    color(body, BASE)


def refit(r, k=1.2):
    """Frame the result (it can be much bigger than what was there before the command)."""
    r.v.fitAll()
    cam = r.v.getCameraNode()
    cam.height.setValue(cam.height.getValue() * k)


# ---------------------------------------------------------------------------
# Part Design: sketch based features (click the sketch, press)
# ---------------------------------------------------------------------------
def sketch_feature(name, typ, plate, sk_args, props, click_at, text, zoom=1.1, axis=None, fit=False):
    @scene(name)
    def _s():
        r = Rec(name)
        body, pad = body_with(r, plate)
        sk = sk_on(body, *sk_args)
        r.view(zoom)
        r.cap(1, "Κλικ στο σκαρίφημα")
        r.click(click_at, sk)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            f = body.newObject("PartDesign::" + typ, typ)
            f.Profile = sk
            if axis:
                f.ReferenceAxis = (sk, [axis])
            for k, v in props.items():
                setattr(f, k, v)
            r.doc.recompute()
            sk.ViewObject.Visibility = False
            recolor(body)
            if fit:
                refit(r)
        r.apply(go, 3, text)
        r.save()
    return _s


sketch_feature("PartDesign_Pad", "Pad", False, (0, rect_geo(-20, -12, 20, 12)), {"Length": 15},
               (20, 0, 0), "Το σκαρίφημα σηκώθηκε σε στερεό", fit=True)
sketch_feature("PartDesign_Pocket", "Pocket", True, (0, circle_geo(0, 0, 9), 10), {"Length": 6},
               (9, 0, 10), "Τσέπη βάθους 6 mm")
sketch_feature("PartDesign_Revolution", "Revolution", False, (1, rect_geo(8, 0, 14, 20)), {"Angle": 360},
               (14, 0, 10), "Γύρισε 360° γύρω από τον άξονα", axis="V_Axis", fit=True)
@scene("PartDesign_Groove")
def s_groove():
    r = Rec("PartDesign_Groove")
    body, pad = body_with(r, False)
    cyl = body.newObject("PartDesign::AdditiveCylinder", "Cylinder")
    cyl.Radius, cyl.Height = 15, 30
    r.doc.recompute()
    recolor(body)
    sk = sk_on(body, 1, rect_geo(12, 12, 18, 18))
    r.view(1.2)
    r.cap(1, "Κλικ στο σκαρίφημα")
    r.click((18, 0, 15), sk)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        g = body.newObject("PartDesign::Groove", "Groove")
        g.Profile = sk
        g.ReferenceAxis = (sk, ["V_Axis"])
        g.Angle = 360
        r.doc.recompute()
        sk.ViewObject.Visibility = False
        recolor(body)
    r.apply(go, 3, "Αυλάκι γύρω-γύρω στον κύλινδρο")
    r.save()
sketch_feature("PartDesign_Hole", "Hole", True, (0, circle_geo(-15, 0, 3) + circle_geo(15, 0, 3), 10),
               {"DepthType": "ThroughAll"}, (-12, 0, 10), "Τρύπες σε κάθε κύκλο")


def helix_scene(name, typ, plate, text):
    @scene(name)
    def _s():
        r = Rec(name)
        body, pad = body_with(r, False)
        if plate:
            cyl = body.newObject("PartDesign::AdditiveCylinder", "Cyl")
            cyl.Radius, cyl.Height = 12, 30
            r.doc.recompute()
        sk = sk_on(body, 1, circle_geo(12 if plate else 14, 4, 2))
        r.view(1.2 if plate else 4.0)
        r.cap(1, "Κλικ στο σκαρίφημα")
        r.click((12 if plate else 16, 0, 4), sk)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            f = body.newObject("PartDesign::" + typ, typ)
            f.Profile = sk
            f.ReferenceAxis = (sk, ["V_Axis"])
            f.Pitch, f.Height = 6, 24
            r.doc.recompute()
            sk.ViewObject.Visibility = False
            recolor(body)
            r.v.fitAll()
        r.apply(go, 3, text)
        r.save()
    return _s


helix_scene("PartDesign_AdditiveHelix", "AdditiveHelix", False, "Το προφίλ ακολουθεί έλικα")
helix_scene("PartDesign_SubtractiveHelix", "SubtractiveHelix", True, "Σπείρωμα κομμένο στον κύλινδρο")


def loft_scene(name, typ, plate, text):
    @scene(name)
    def _s():
        r = Rec(name)
        body, pad = body_with(r, plate)
        z0 = 10 if plate else 0
        if plate:
            s1 = sk_on(body, 0, rect_geo(-12, -12, 12, 12), 10)
            s2 = sk_on(body, 0, circle_geo(0, 0, 5), 1)
        else:
            s1 = sk_on(body, 0, rect_geo(-12, -12, 12, 12), 0)
            s2 = sk_on(body, 0, circle_geo(0, 0, 6), 24)
        r.view(1.15)
        r.cap(1, "Κλικ στην 1η διατομή")
        r.click((12, 0, z0), s1)
        r.cap(2, "Πάτα το κουμπί · Add Section: 2η")
        r.press()
        r.click((6, 0, 24 if not plate else 1))

        def go():
            f = body.newObject("PartDesign::" + typ, typ)
            f.Profile = s1
            f.Sections = [s2]
            r.doc.recompute()
            s1.ViewObject.Visibility = s2.ViewObject.Visibility = False
            recolor(body)
        r.apply(go, 3, text)
        r.save()
    return _s


loft_scene("PartDesign_AdditiveLoft", "AdditiveLoft", False, "Ομαλή μετάβαση από τετράγωνο σε κύκλο")
loft_scene("PartDesign_SubtractiveLoft", "SubtractiveLoft", True, "Αφαιρέθηκε η μετάβαση")


def pipe_scene(name, typ, plate, text):
    @scene(name)
    def _s():
        r = Rec(name)
        body, pad = body_with(r, plate)
        z = 10 if plate else 0
        path = sk_on(body, 1, [Part.LineSegment(V(-25, z, 0), V(20, z, 0))])
        prof = sk_on(body, 2, circle_geo(0, z, 4))
        prof.AttachmentOffset = App.Placement(V(0, 0, -25), App.Rotation())
        r.doc.recompute()
        r.view(1.15)
        r.cap(1, "Κλικ στη διατομή (κύκλος)")
        r.click((-25, 4, z), prof)
        r.cap(2, "Πάτα το κουμπί · μετά η διαδρομή")
        r.press()
        r.click((0, 0, z), path)

        def go():
            f = body.newObject("PartDesign::" + typ, typ)
            f.Profile = prof
            f.Spine = (path, ["Edge1"])
            r.doc.recompute()
            prof.ViewObject.Visibility = path.ViewObject.Visibility = False
            recolor(body)
        r.apply(go, 3, text)
        r.save()
    return _s


pipe_scene("PartDesign_AdditivePipe", "AdditivePipe", False, "Ο κύκλος σύρθηκε στη διαδρομή")
pipe_scene("PartDesign_SubtractivePipe", "SubtractivePipe", True, "Κανάλι κατά μήκος της διαδρομής")


# ---------------------------------------------------------------------------
# Part Design primitives (press, the shape appears / is cut)
# ---------------------------------------------------------------------------
PRIMS = {"Box": {"Length": 20, "Width": 16, "Height": 12}, "Cylinder": {"Radius": 8, "Height": 18},
         "Sphere": {"Radius": 10}, "Cone": {"Radius1": 10, "Radius2": 3, "Height": 16},
         "Ellipsoid": {"Radius1": 6, "Radius2": 12, "Radius3": 8}, "Torus": {"Radius1": 12, "Radius2": 3},
         "Prism": {"Polygon": 6, "Circumradius": 9, "Height": 14},
         "Wedge": {"Xmin": 0, "Xmax": 20, "Ymin": 0, "Ymax": 14, "Zmin": 0, "Zmax": 12, "X2min": 6, "X2max": 14}}


def prim_scene(kind, sub):
    name = "PartDesign_%s%s" % ("Subtractive" if sub else "Additive", kind)

    @scene(name)
    def _s():
        r = Rec(name, tool_first=True)
        body, pad = body_with(r, sub)
        if not sub:
            pad = None
        r.view(1.2 if sub else 2.6)

        def go():
            f = body.newObject("PartDesign::%s%s" % ("Subtractive" if sub else "Additive", kind), kind)
            for k, v in PRIMS[kind].items():
                setattr(f, k, v)
            if sub:   # not attached: Placement decides where it cuts (from the top face down)
                f.Placement = App.Placement(V(0, 0, {"Sphere": 14, "Ellipsoid": 9, "Torus": 10}.get(kind, 4)),
                                            App.Rotation())
            r.doc.recompute()
            recolor(body)
            if not sub:
                r.v.fitAll()
        r.apply(go, 2, ("Αφαιρέθηκε από το σώμα" if sub else "Νέο σχήμα στο Body") + " · μέγεθος στο παράθυρο")
        r.save()
    return _s


for _k in PRIMS:
    prim_scene(_k, False)
    prim_scene(_k, True)


# ---------------------------------------------------------------------------
# Part Design dress-ups (click edges / faces, press)
# ---------------------------------------------------------------------------
def edges_at_top(obj):
    z = obj.Shape.BoundBox.ZMax
    return ["Edge%d" % (i + 1) for i, e in enumerate(obj.Shape.Edges)
            if abs(e.BoundBox.ZMin - z) < 1e-6 and abs(e.BoundBox.ZMax - z) < 1e-6]


def dressup_scene(name, typ, setup, text, zoom=1.0):
    @scene(name)
    def _s():
        r = Rec(name)
        body, pad = body_with(r, True)
        r.view(zoom)
        clicks, base, props = setup(pad)
        r.cap(1, "Κλικ σε ακμές ή έδρες" if typ in ("Fillet", "Chamfer") else "Κλικ στις έδρες")
        for i, (p, sub) in enumerate(clicks):
            r.click(p, pad, sub) if i == 0 else (r.move(p), r.events.append({"t": "click"}),
                                                 Gui.Selection.addSelection(r.doc.Name, pad.Name, sub), r.img())
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            f = body.newObject("PartDesign::" + typ, typ)
            f.Base = (pad, base)
            for k, v in props.items():
                setattr(f, k, v)
            r.doc.recompute()
            recolor(body)
        r.apply(go, 3, text)
        r.save()
    return _s


def top_edges_setup(radius_key, val):
    def setup(pad):
        def edge(test):
            return "Edge%d" % (1 + next(i for i, e in enumerate(pad.Shape.Edges)
                                        if abs(e.BoundBox.ZMin - 10) < 1e-6 and abs(e.BoundBox.ZMax - 10) < 1e-6
                                        and test(e.BoundBox)))
        front = edge(lambda b: abs(b.YMin + 20) < 1e-6 and abs(b.YMax + 20) < 1e-6)
        right = edge(lambda b: abs(b.XMin - 30) < 1e-6 and abs(b.XMax - 30) < 1e-6)
        return ([((0, -20, 10), front), ((30, 0, 10), right)], [front, right], {radius_key: val})
    return setup


dressup_scene("PartDesign_Fillet", "Fillet", top_edges_setup("Radius", 4), "Στρογγύλεψαν οι ακμές")
dressup_scene("PartDesign_Chamfer", "Chamfer", top_edges_setup("Size", 4), "Φάλτσο στις ακμές")


def top_face_setup(extra):
    def setup(pad):
        f = top_face(pad)
        return ([((0, 0, 10), f)], [f], extra)
    return setup


dressup_scene("PartDesign_Thickness", "Thickness", top_face_setup({"Value": 2, "Reversed": True}),
              "Άδειασε: τοιχώματα 2 mm, ανοιχτό πάνω")


@scene("PartDesign_Draft")
def s_draft():
    r = Rec("PartDesign_Draft")
    body, pad = body_with(r, True)
    r.view(1.0)
    sides = [i + 1 for i, f in enumerate(pad.Shape.Faces) if f.BoundBox.ZMax - f.BoundBox.ZMin > 1]
    r.cap(1, "Κλικ στις πλευρικές έδρες")
    r.click((0, -20, 5), pad, "Face%d" % sides[0])
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        d = body.newObject("PartDesign::Draft", "Draft")
        d.Base = (pad, ["Face%d" % i for i in sides])
        d.NeutralPlane = (pad, [face_where(pad, lambda f: f.BoundBox.ZMax < 1e-6)])
        d.Angle = 10
        r.doc.recompute()
        recolor(body)
    r.apply(go, 3, "Κλίση 10° για να βγαίνει από καλούπι")
    r.save()


@scene("PartDesign_Defeaturing")
def s_defeat():
    r = Rec("PartDesign_Defeaturing")
    body, pad = body_with(r, True)
    hs = sk_on(body, 0, circle_geo(10, 0, 6), 10)
    pk = body.newObject("PartDesign::Pocket", "Pocket")
    pk.Profile, pk.Type = hs, "ThroughAll"
    hs.ViewObject.Visibility = False
    r.doc.recompute()
    recolor(body)
    r.view(1.0)
    hf = face_where(pk, lambda f: f.Surface.__class__.__name__ == "Cylinder")
    r.cap(1, "Κλικ στο τοίχωμα της τρύπας")
    r.click((16, 0, 5), pk, hf)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        d = body.newObject("PartDesign::Defeaturing", "Defeaturing")
        d.Base = (pk, [hf])
        r.doc.recompute()
        recolor(body)
    r.apply(go, 3, "Η τρύπα σβήστηκε, το κενό έκλεισε")
    r.save()


@scene("PartDesign_MultiTransform")
def s_multi():
    r = Rec("PartDesign_MultiTransform")
    body, pad = body_with(r, True)
    hs = sk_on(body, 0, circle_geo(-22, -12, 3), 10)
    pk = body.newObject("PartDesign::Pocket", "Pocket")
    pk.Profile, pk.Type = hs, "ThroughAll"
    hs.ViewObject.Visibility = False
    r.doc.recompute()
    recolor(body)
    r.view(1.0)
    r.cap(1, "Κλικ στην τρύπα")
    r.click((-22, -9, 5), pk, face_where(pk, lambda f: f.Surface.__class__.__name__ == "Cylinder"))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        mt = body.newObject("PartDesign::MultiTransform", "MultiTransform")
        mt.Originals = [pk]
        lp = body.newObject("PartDesign::LinearPattern", "LinearPattern")
        lp.Direction = (hs, ["H_Axis"])
        lp.Length, lp.Occurrences = 44, 3
        m = body.newObject("PartDesign::Mirrored", "Mirrored")
        m.MirrorPlane = (hs, ["H_Axis"])
        mt.Transformations = [lp, m]
        body.Tip = mt                  # the sub-transformations must not become the tip
        r.doc.recompute()
        for x in (lp, m):
            x.ViewObject.Visibility = False
        mt.ViewObject.Visibility = True
        body.ViewObject.Visibility = True
        recolor(body)
    r.apply(go, 3, "Επανάληψη × 3 και καθρέφτης = 6 τρύπες")
    r.save()


# ---------------------------------------------------------------------------
# Body, sketches in 3D
# ---------------------------------------------------------------------------
@scene("PartDesign_Body")
def s_body():
    r = Rec("PartDesign_Body", tool_first=True)
    plate = r.doc.addObject("Part::Box", "Imported")
    plate.Length, plate.Width, plate.Height = 40, 30, 10
    color(plate, (0.70, 0.74, 0.80))
    r.view(1.4)

    def go():
        b = r.doc.addObject("PartDesign::Body", "Body")
        b.ViewObject.Visibility = True
        try:
            b.Origin.ViewObject.Visibility = True
        except Exception:
            pass
    r.apply(go, 2, "Νέο κενό Body (ενεργό): εδώ μπαίνουν σκαριφήματα")
    r.save()


@scene("PartDesign_NewSketch")
def s_newsketch():
    r = Rec("PartDesign_NewSketch")
    body, pad = body_with(r, True)
    r.view(1.0)
    f = top_face(pad)
    r.cap(1, "Κλικ στην πάνω έδρα")
    r.click((0, 0, 10), pad, f)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        sk = body.newObject("Sketcher::SketchObject", "Sketch")
        sk.AttachmentSupport = [(pad, f)]
        sk.MapMode = "FlatFace"
        sk.addGeometry(Part.Circle(V(0, 0, 0), V(0, 0, 1), 8))
        r.doc.recompute()
        style_sketch(sk)
    r.apply(go, 3, "Νέο σκαρίφημα πάνω στην έδρα")
    r.save()


@scene("Sketcher_NewSketch")
def s_sk_new():
    r = Rec("Sketcher_NewSketch")
    box = r.doc.addObject("Part::Box", "Box")
    box.Length, box.Width, box.Height = 40, 30, 10
    color(box, BASE)
    r.view(1.2)
    f = top_face(box)
    r.cap(1, "Κλικ στην έδρα (ή τίποτα: διαλέγεις επίπεδο)")
    r.click((20, 15, 10), box, f)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        sk = r.doc.addObject("Sketcher::SketchObject", "Sketch")
        sk.AttachmentSupport = [(box, f)]
        sk.MapMode = "FlatFace"
        sk.addGeometry(Part.Circle(V(20, 15, 0), V(0, 0, 1), 6))
        r.doc.recompute()
        style_sketch(sk)
    r.apply(go, 3, "Σκαρίφημα κολλημένο στην έδρα")
    r.save()


@scene("Sketcher_MapSketch")
def s_map():
    r = Rec("Sketcher_MapSketch")
    body, pad = body_with(r, True)
    sk = sk_on(body, 0, circle_geo(0, 0, 8), 0)
    r.view(1.0)
    f = face_where(pad, lambda fc: abs(fc.BoundBox.YMin + 20) < 1e-6 and abs(fc.BoundBox.YMax + 20) < 1e-6)
    r.cap(1, "Κλικ στην έδρα-στόχο")
    r.click((0, -20, 5), pad, f)
    r.cap(2, "Πάτα το κουμπί · διάλεξε το σκαρίφημα")
    r.press()

    def go():
        sk.AttachmentSupport = [(pad, f)]
        sk.MapMode = "FlatFace"
        sk.AttachmentOffset = App.Placement()
        sk.Geometry = []
        sk.addGeometry(Part.Circle(V(0, 0, 0), V(0, 0, 1), 4))
        r.doc.recompute()
        style_sketch(sk)
    r.apply(go, 3, "Το σκαρίφημα μεταφέρθηκε στην πλάγια έδρα")
    r.save()


@scene("Sketcher_EditSketch")
def s_edit():
    r = Rec("Sketcher_EditSketch")
    body, pad = body_with(r, True)
    sk = sk_on(body, 0, circle_geo(0, 0, 8) + rect_geo(-20, -12, 20, 12), 10)
    r.view(1.0)
    r.cap(1, "Κλικ στο σκαρίφημα (ή διπλό κλικ στο δέντρο)")
    r.click((8, 0, 10), sk)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    Gui.Selection.clearSelection()
    Gui.ActiveDocument.setEdit(sk.Name)
    P.pump(600)
    r.v.viewTop()
    r.v.fitAll()
    P.pump(300)
    r.cap(3, "Ανοίγει για αλλαγές, σε κάτοψη")
    r.img(blend=True)
    r.hold(1800)
    Gui.ActiveDocument.resetEdit()
    r.save()


@scene("Sketcher_LeaveSketch")
def s_leave():
    r = Rec("Sketcher_LeaveSketch", tool_first=False)
    body, pad = body_with(r, True)
    sk = sk_on(body, 0, circle_geo(0, 0, 8), 10)
    r.view(1.0)
    Gui.ActiveDocument.setEdit(sk.Name)
    P.pump(600)
    r.v.viewTop()
    r.v.fitAll()
    P.pump(300)
    r.img()
    r.cap(1, "Τελείωσες το σκαρίφημα: πάτα το κουμπί (ή Esc)")
    r.press()
    Gui.ActiveDocument.resetEdit()
    P.pump(500)
    r.v.viewIsometric()
    r.v.fitAll()
    P.pump(300)
    style_sketch(sk)
    r.cap(2, "Πίσω στο 3D")
    r.img(blend=True)
    r.hold(1800)
    r.save()


@scene("Sketcher_ViewSketch")
def s_viewsk():
    r = Rec("Sketcher_ViewSketch", tool_first=False)
    body, pad = body_with(r, True)
    sk = sk_on(body, 0, circle_geo(0, 0, 8), 10)
    Gui.ActiveDocument.setEdit(sk.Name)
    P.pump(600)
    r.view(1.0)
    r.cap(1, "Γύρισες την προβολή μέσα στο σκαρίφημα")
    r.press()
    r.v.viewTop()
    r.v.fitAll()
    P.pump(300)
    r.cap(2, "Ξανά κάθετα στο σκαρίφημα")
    r.img(blend=True)
    r.hold(1800)
    Gui.ActiveDocument.resetEdit()
    r.save()


@scene("Sketcher_ViewSection")
def s_section():
    r = Rec("Sketcher_ViewSection", tool_first=False)
    body, pad = body_with(r, False)
    box = sk_on(body, 0, rect_geo(-20, -15, 20, 15), 0)
    p2 = body.newObject("PartDesign::Pad", "Pad")
    p2.Profile, p2.Length, p2.SideType = box, 30, "Symmetric"
    box.ViewObject.Visibility = False
    sk = sk_on(body, 0, circle_geo(0, 0, 8), 0)
    r.doc.recompute()
    recolor(body)
    Gui.ActiveDocument.setEdit(sk.Name)
    P.pump(600)
    r.view(1.2)
    r.cap(1, "Το σκαρίφημα κρύβεται μέσα στο στερεό")
    r.press()
    Gui.runCommand("Sketcher_ViewSection")
    P.pump(500)
    r.cap(2, "Κόβεται προσωρινά ό,τι είναι μπροστά")
    r.img(blend=True)
    r.hold(1800)
    Gui.ActiveDocument.resetEdit()
    r.save()


def external_scene(name, kind, text):
    @scene(name)
    def _s():
        r = Rec(name, tool_first=False)
        body, pad = body_with(r, True)
        sk = sk_on(body, 0, [], 16 if kind == "projection" else 5)
        Gui.ActiveDocument.setEdit(sk.Name)
        P.pump(600)
        r.view(1.0)
        r.cap(1, "Μέσα στο σκαρίφημα: πάτα το κουμπί")
        r.press()
        e = "Edge%d" % (1 + next(i for i, ed in enumerate(pad.Shape.Edges)
                                 if abs(ed.BoundBox.ZMin - 10) < 1e-6 and abs(ed.BoundBox.ZMax - 10) < 1e-6
                                 and abs(ed.BoundBox.YMin + 20) < 1e-6 and abs(ed.BoundBox.YMax + 20) < 1e-6))
        r.cap(2, "Κλικ σε ακμή του στερεού" if kind == "projection" else "Κλικ στην πλαϊνή έδρα")
        r.click((0, -20, 10) if kind == "projection" else (0, -20, 5))

        def go():
            if kind == "intersection":
                side = face_where(pad, lambda f: abs(f.BoundBox.YMin + 20) < 1e-6 and abs(f.BoundBox.YMax + 20) < 1e-6)
                sk.addExternal(pad.Name, side, False, True)
            else:
                sk.addExternal(pad.Name, e)
            r.doc.recompute()
        r.apply(go, 3, text)
        Gui.ActiveDocument.resetEdit()
        r.save()
    return _s


external_scene("Sketcher_Projection", "projection", "Η ακμή μπήκε στο σκαρίφημα (μοβ)")
external_scene("Sketcher_Intersection", "intersection", "Η τομή μπήκε στο σκαρίφημα (μοβ)")


@scene("Sketcher_ValidateSketch")
def s_validate():
    r = Rec("Sketcher_ValidateSketch")
    body, pad = body_with(r, False)
    pts = [V(-15, -10, 0), V(15, -10, 0), V(15, 10, 0), V(-15, 10, 0)]
    geo = [Part.LineSegment(pts[i], pts[(i + 1) % 4]) for i in range(3)]
    geo.append(Part.LineSegment(V(-15, 10, 0), V(-15, -9.95, 0)))     # almost closed
    sk = sk_on(body, 0, geo, 0)
    r.view(1.4)
    r.cap(1, "Κλικ στο σκαρίφημα (κλειστό, όχι σε edit)")
    r.click((15, 0, 0), sk)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.events.append({"t": "panel", "title": "Sketch validation", "mono": False,
                     "lines": ["Missing coincidences: 1", "→ Fix: τα άκρα ενώνονται"]})
    r.hold(1600)

    def go():
        import Sketcher
        sk.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1))
        r.doc.recompute()
        f = body.newObject("PartDesign::Pad", "Pad")
        f.Profile, f.Length = sk, 6
        r.doc.recompute()
        recolor(body)
    r.apply(go, 3, "Κλειστό περίγραμμα: τώρα κάνει Pad")
    r.save()


@scene("Part_CheckGeometry")
def s_check():
    r = Rec("Part_CheckGeometry")
    body, pad = body_with(r, True)
    r.view(1.0)
    r.cap(1, "Κλικ σε ΟΛΟ το αντικείμενο (στο δέντρο)")
    r.click((0, 0, 10), body)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.events.append({"t": "panel", "title": "Check geometry", "mono": False,
                     "lines": ["Body: έγκυρο στερεό ✓", "Shells: 1 · Faces: 6", "Χωρίς σφάλματα"]})
    r.cap(3, "Αναφορά: σωστό ή με λάθη")
    r.hold(2600)
    r.save()


# ---------------------------------------------------------------------------
# Part workbench
# ---------------------------------------------------------------------------
PART_PRIMS = {"Part_Box": ("Part::Box", {"Length": 20, "Width": 14, "Height": 10}, "Κουτί 10 mm στο (0,0,0)"),
              "Part_Cylinder": ("Part::Cylinder", {"Radius": 5, "Height": 10}, "Κύλινδρος R5 στο (0,0,0)"),
              "Part_Sphere": ("Part::Sphere", {"Radius": 5}, "Σφαίρα R5 με κέντρο το (0,0,0)"),
              "Part_Cone": ("Part::Cone", {"Radius1": 6, "Radius2": 2, "Height": 10}, "Κώνος (κομμένος στην κορυφή)"),
              "Part_Torus": ("Part::Torus", {"Radius1": 8, "Radius2": 2}, "Τόρος"),
              "Part_Tube": ("Part::Tube", {"OuterRadius": 8, "InnerRadius": 5, "Height": 12}, "Σωλήνας: εξωτ. και εσωτ. ακτίνα")}


def part_prim(name):
    typ, props, text = PART_PRIMS[name]

    @scene(name)
    def _s():
        r = Rec(name, tool_first=True)
        guide = r.doc.addObject("Part::Box", "Guide")      # gives the camera a size before the shape exists
        guide.Length, guide.Width, guide.Height = 24, 18, 14
        guide.Placement.Base = V(-6, -6, -1)
        r.doc.recompute()
        guide.ViewObject.Visibility = False
        r.view(1.6)

        def go():
            if typ == "Part::Tube":
                import BasicShapes.Shapes as BS
                o = r.doc.addObject("Part::Feature", "Tube")
                o.Shape = BS.makeTube(8, 5, 12)
            else:
                o = r.doc.addObject(typ, name[5:])
                for k, v in props.items():
                    setattr(o, k, v)
            r.doc.recompute()
            color(o, RESULT)
            refit(r, 1.7)
        r.apply(go, 2, text + " · μέγεθος: διπλό κλικ")
        r.save()
    return _s


for _n in PART_PRIMS:
    part_prim(_n)


@scene("Part_Primitives")
def s_prims():
    r = Rec("Part_Primitives", tool_first=True)
    g = r.doc.addObject("Part::Box", "Guide")
    g.Length, g.Width, g.Height = 30, 30, 30
    g.Placement.Base = V(-15, -15, 0)
    r.doc.recompute()
    g.ViewObject.Visibility = False
    r.view(1.3)
    r.events.append({"t": "panel", "title": "Primitives", "mono": False, "pos": "left",
                     "lines": ["Plane", "Box", "Cylinder", "Helix", "Spiral", "Wedge", "…"]})
    r.events.append({"t": "pick", "row": 3})
    r.events.append({"t": "panel", "title": None})

    def go():
        h = r.doc.addObject("Part::Helix", "Helix")
        h.Pitch, h.Height, h.Radius = 6, 24, 10
        r.doc.recompute()
        h.ViewObject.LineColor = RESULT
        h.ViewObject.LineWidth = 4
        refit(r, 1.4)
    r.apply(go, 3, "Διάλεξες σχήμα → μπαίνει στο έγγραφο (εδώ έλικα)")
    r.save()


def part_profile_scene(name, make_profile, op, text, zoom=1.2, click=(10, 0, 0), keep=False, fit=False):
    @scene(name)
    def _s():
        r = Rec(name)
        prof = make_profile(r)
        r.view(zoom)
        r.cap(1, "Κλικ στο σχήμα")
        r.click(click, prof)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            o = op(r, prof)
            r.doc.recompute()
            if o is not None:
                color(o, RESULT)
            if not keep:
                hide(prof)
            if fit:
                refit(r)
        r.apply(go, 3, text)
        r.save()
    return _s


def sk_part(r, geo, plane="XY"):
    sk = r.doc.addObject("Sketcher::SketchObject", "Sketch")
    if plane == "XZ":
        sk.Placement = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), 90))
    for g in geo:
        sk.addGeometry(g)
    r.doc.recompute()
    style_sketch(sk)
    return sk


def op_extrude(r, prof):
    o = r.doc.addObject("Part::Extrusion", "Extrude")
    o.Base, o.Dir, o.LengthFwd, o.Solid = prof, V(0, 0, 1), 12, True
    return o


def op_revolve(r, prof):
    o = r.doc.addObject("Part::Revolution", "Revolve")
    o.Source, o.Axis, o.Base, o.Angle, o.Solid = prof, V(0, 0, 1), V(0, 0, 0), 360, True
    return o


part_profile_scene("Part_Extrude", lambda r: sk_part(r, rect_geo(-10, -6, 10, 6)), op_extrude,
                   "Στερεό από το περίγραμμα (Create solid ✓)")
part_profile_scene("Part_Revolve", lambda r: sk_part(r, rect_geo(6, 0, 12, 14), "XZ"), op_revolve,
                   "Γύρισε 360° γύρω από τον Z", click=(12, 0, 7), fit=True)


def op_makeface(r, prof):
    o = r.doc.addObject("Part::Face", "Face")
    o.Sources = [prof]
    return o


part_profile_scene("Part_MakeFace", lambda r: sk_part(r, rect_geo(-12, -8, 12, 8) + circle_geo(0, 0, 4)),
                   op_makeface, "Επίπεδη έδρα · ο κύκλος έγινε τρύπα", click=(12, 0, 0))


def op_offset2d(r, prof):
    o = r.doc.addObject("Part::Offset2D", "Offset2D")
    o.Source, o.Value, o.Join = prof, 4, 0
    prof.ViewObject.Visibility = True
    return o


part_profile_scene("Part_Offset2D", lambda r: sk_part(r, rect_geo(-10, -6, 10, 6)), op_offset2d,
                   "Παράλληλο περίγραμμα 4 mm έξω", keep=True, fit=True)


def solid_scene(name, op, text, zoom=1.3, keep=False, click=(20, 0, 10), sub=""):
    @scene(name)
    def _s():
        r = Rec(name)
        box = r.doc.addObject("Part::Box", "Box")
        box.Length, box.Width, box.Height = 30, 20, 10
        box.Placement.Base = V(-15, -10, 0)
        r.doc.recompute()
        color(box, BASE)
        r.view(zoom)
        s = sub(box) if callable(sub) else sub
        r.cap(1, "Κλικ στο σχήμα" if not s else "Κλικ στην έδρα / ακμή")
        r.click(click, box, s)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            o = op(r, box, s)
            r.doc.recompute()
            if o is not None:
                color(o, RESULT)
            if not keep:
                hide(box)
        r.apply(go, 3, text)
        r.save()
    return _s


def op_mirror(r, box, s):
    o = r.doc.addObject("Part::Mirroring", "Mirror")
    o.Source, o.Normal, o.Base = box, V(1, 0, 0), V(18, 0, 0)
    return o


solid_scene("Part_Mirror", op_mirror, "Καθρέφτης ως προς επίπεδο", keep=True, zoom=1.9, click=(15, 0, 5))


def op_scale(r, box, s):
    o = r.doc.addObject("Part::Feature", "Scaled")
    o.Shape = box.Shape.copy().scale(1.6, V(0, 0, 0))
    return o


solid_scene("Part_Scale", op_scale, "×1,6 ως προς το (0,0,0)", zoom=1.8)


def op_fillet(r, box, s):
    o = r.doc.addObject("Part::Fillet", "Fillet")
    o.Base = box
    o.Edges = [(i + 1, 3.0, 3.0) for i, e in enumerate(box.Shape.Edges)
               if abs(e.BoundBox.ZMin - 10) < 1e-6 and abs(e.BoundBox.ZMax - 10) < 1e-6]
    return o


def op_chamfer(r, box, s):
    o = r.doc.addObject("Part::Chamfer", "Chamfer")
    o.Base = box
    o.Edges = [(i + 1, 3.0, 3.0) for i, e in enumerate(box.Shape.Edges)
               if abs(e.BoundBox.ZMin - 10) < 1e-6 and abs(e.BoundBox.ZMax - 10) < 1e-6]
    return o


def top_edge(box):
    return "Edge%d" % (1 + next(i for i, e in enumerate(box.Shape.Edges)
                                if abs(e.BoundBox.ZMin - 10) < 1e-6 and abs(e.BoundBox.ZMax - 10) < 1e-6))


solid_scene("Part_Fillet", op_fillet, "Στρογγύλεψαν οι πάνω ακμές", click=(0, -10, 10), sub=top_edge)
solid_scene("Part_Chamfer", op_chamfer, "Φάλτσο στις πάνω ακμές", click=(0, -10, 10), sub=top_edge)


def op_offset(r, box, s):
    o = r.doc.addObject("Part::Offset", "Offset")
    o.Source, o.Value, o.Join = box, 3, 0
    box.ViewObject.Visibility = True
    o.ViewObject.Transparency = 60
    return o


solid_scene("Part_Offset", op_offset, "Μεγαλύτερο αντίγραφο σε απόσταση 3 mm", keep=True, zoom=1.5)


def op_thickness(r, box, s):
    o = r.doc.addObject("Part::Thickness", "Thickness")
    o.Faces = (box, [s])
    o.Value = -2
    return o


solid_scene("Part_Thickness", op_thickness, "Άδειασε: τοιχώματα 2 mm", sub=lambda b: top_face(b), click=(0, 0, 10))


def op_sections(r, box, s):
    shapes = [box.Shape.slice(V(0, 0, 1), z) for z in (2, 5, 8)]
    o = r.doc.addObject("Part::Feature", "CrossSections")
    o.Shape = Part.makeCompound([w for ws in shapes for w in ws])
    o.ViewObject.LineColor = RESULT
    o.ViewObject.LineWidth = 4
    return None


solid_scene("Part_CrossSections", op_sections, "Τομές κάθε 3 mm, παράλληλες στο XY")


def op_color(r, box, s):
    vo = box.ViewObject
    n = len(box.Shape.Faces)
    k = int(s[4:]) - 1
    cols = [App.Material(DiffuseColor=BASE) for _ in range(n)]
    cols[k] = App.Material(DiffuseColor=(0.96, 0.62, 0.04))
    try:
        vo.ShapeAppearance = cols
    except Exception:
        vo.DiffuseColor = [BASE if i != k else (0.96, 0.62, 0.04) for i in range(n)]
    return None


solid_scene("Part_ColorPerFace", op_color, "Μόνο αυτή η έδρα πήρε χρώμα", keep=True, sub=lambda b: top_face(b),
            click=(0, 0, 10))


@scene("Part_Defeaturing")
def s_part_defeat():
    r = Rec("Part_Defeaturing")
    b = r.doc.addObject("Part::Feature", "Solid")
    b.Shape = Part.makeBox(30, 20, 10, V(-15, -10, 0)).cut(Part.makeCylinder(4, 10, V(5, 0, 0)))
    r.doc.recompute()
    color(b, BASE)
    r.view(1.3)
    hf = face_where(b, lambda f: f.Surface.__class__.__name__ == "Cylinder")
    r.cap(1, "Κλικ στο τοίχωμα της τρύπας")
    r.click((9, 0, 5), b, hf)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        o = r.doc.addObject("Part::Feature", "Defeatured")
        o.Shape = b.Shape.defeaturing([b.Shape.Faces[int(hf[4:]) - 1]])
        r.doc.recompute()
        hide(b)
        color(o, RESULT)
    r.apply(go, 3, "Η τρύπα έφυγε, το στερεό έκλεισε")
    r.save()


def two_profiles(r, z2=16, second=None):
    a = sk_part(r, rect_geo(-10, -10, 10, 10))
    b = sk_part(r, second or circle_geo(0, 0, 6))
    b.Placement.Base = V(0, 0, z2)
    r.doc.recompute()
    return a, b


@scene("Part_Loft")
def s_loft():
    r = Rec("Part_Loft")
    a, b = two_profiles(r)
    r.view(1.3)
    r.cap(1, "Βάλε τις διατομές στη λίστα, με τη σειρά")
    r.click((10, 0, 0), a)
    r.events.append({"t": "click"})
    r.click((6, 0, 16), b)
    r.cap(2, "Πάτα OK (Create solid ✓)")
    r.press()

    def go():
        o = r.doc.addObject("Part::Loft", "Loft")
        o.Sections, o.Solid = [a, b], True
        r.doc.recompute()
        color(o, RESULT)
        hide(a, b)
    r.apply(go, 3, "Μετάβαση από τετράγωνο σε κύκλο")
    r.save()


@scene("Part_RuledSurface")
def s_ruled():
    r = Rec("Part_RuledSurface")
    a = sk_part(r, [Part.LineSegment(V(-15, 0, 0), V(15, 0, 0))])
    b = sk_part(r, [Part.ArcOfCircle(Part.Circle(V(0, 0, 0), V(0, 0, 1), 15), 0, math.pi)])
    b.Placement.Base = V(0, 0, 14)
    r.doc.recompute()
    r.view(1.3)
    r.cap(1, "Κλικ στην 1η ακμή, Ctrl+κλικ στη 2η")
    r.click((0, 0, 0), a, "Edge1")
    r.click((0, 15, 14), b, "Edge1")
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        o = r.doc.addObject("Part::RuledSurface", "Ruled")
        o.Curve1, o.Curve2 = (a, ["Edge1"]), (b, ["Edge1"])
        r.doc.recompute()
        color(o, RESULT)
    r.apply(go, 3, "Επιφάνεια ανάμεσα στις δύο ακμές")
    r.save()


@scene("Part_Sweep")
def s_sweep():
    r = Rec("Part_Sweep")
    path = sk_part(r, [Part.LineSegment(V(0, 0, 0), V(0, 20, 0)),
                       Part.ArcOfCircle(Part.Circle(V(10, 20, 0), V(0, 0, 1), 10), math.pi / 2, math.pi)])
    path.Placement = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), 90))
    prof = sk_part(r, circle_geo(0, 0, 3))
    r.doc.recompute()
    r.view(1.3)
    r.cap(1, "Βάλε το προφίλ (κύκλο) στη λίστα")
    r.click((3, 0, 0), prof)
    r.cap(2, "Sweep Path: κλικ στη διαδρομή, μετά OK")
    r.press()
    r.click((0, 0, 10), path)

    def go():
        o = r.doc.addObject("Part::Sweep", "Sweep")
        o.Sections, o.Spine, o.Solid, o.Frenet = [prof], (path, ["Edge1", "Edge2"]), True, True
        r.doc.recompute()
        color(o, RESULT)
        hide(prof, path)
    r.apply(go, 3, "Ο κύκλος σύρθηκε στη διαδρομή")
    r.save()


@scene("Part_Builder")
def s_builder():
    r = Rec("Part_Builder")
    w = sk_part(r, rect_geo(-12, -8, 12, 8))
    r.view(1.3)
    r.cap(1, "Πάτα το κουμπί: διάλεξε «Face from edges»")
    r.press()
    r.cap(2, "Κλικ στις ακμές")
    for p in ((0, -8, 0), (12, 0, 0), (0, 8, 0), (-12, 0, 0)):
        r.click(p)

    def go():
        o = r.doc.addObject("Part::Feature", "Face")
        o.Shape = Part.Face(Part.Wire(w.Shape.Edges))
        r.doc.recompute()
        color(o, RESULT)
    r.apply(go, 3, "Έδρα από τις επιλεγμένες ακμές")
    r.save()


@scene("Part_Compound")
def s_compound():
    r = Rec("Part_Compound")
    a = r.doc.addObject("Part::Box", "Box")
    a.Length = a.Width = a.Height = 10
    b = r.doc.addObject("Part::Cylinder", "Cylinder")
    b.Radius, b.Height = 5, 10
    b.Placement.Base = V(22, 5, 0)
    r.doc.recompute()
    color(a, BASE)
    color(b, BASE)
    r.view(1.4)
    r.cap(1, "Κλικ στο 1ο, Ctrl+κλικ στο 2ο")
    r.click((5, 0, 10), a)
    r.click((22, 5, 10), b)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        o = r.doc.addObject("Part::Compound", "Compound")
        o.Links = [a, b]
        r.doc.recompute()
        color(o, RESULT)
    r.apply(go, 3, "Ένα αντικείμενο, τα κομμάτια ΔΕΝ ενώθηκαν")
    r.save()


@scene("Part_Boolean")
def s_boolean():
    r = Rec("Part_Boolean", tool_first=True)
    a, b = P.two_solids(r, "cyl")
    r.view(1.1)
    r.events.append({"t": "panel", "title": "Boolean Operation", "mono": False, "pos": "left",
                     "lines": ["Union", "Intersection", "Difference", "Section"]})
    r.cap(2, "Διάλεξε πράξη και τα δύο σχήματα")
    r.events.append({"t": "pick", "row": 2})
    r.events.append({"t": "panel", "title": None})

    def go():
        o = r.doc.addObject("Part::Cut", "Cut")
        o.Base, o.Tool = a, b
        r.doc.recompute()
        hide(a, b)
        color(o, BASE)
    r.apply(go, 3, "Difference: το 2ο αφαιρέθηκε από το 1ο")
    r.save()


@scene("Part_ProjectionOnSurface")
def s_proj():
    r = Rec("Part_ProjectionOnSurface")
    cyl = r.doc.addObject("Part::Cylinder", "Cylinder")
    cyl.Radius, cyl.Height = 15, 20
    cyl.Placement = App.Placement(V(0, 0, 0), App.Rotation(V(0, 1, 0), 90))
    star = sk_part(r, rect_geo(4, -4, 14, 4))
    star.Placement.Base = V(0, 0, 22)
    r.doc.recompute()
    color(cyl, BASE)
    r.view(1.2)
    side = face_where(cyl, lambda f: f.Surface.__class__.__name__ == "Cylinder")
    r.cap(1, "Πάτα το κουμπί · Select Projection Surface")
    r.press()
    r.click((9, 0, 15), cyl, side)
    r.cap(2, "Add Wire: κλικ στο σχήμα")
    r.click((14, 0, 22), star)

    def go():
        o = r.doc.addObject("Part::Feature", "Projection")
        o.Shape = cyl.Shape.Faces[int(side[4:]) - 1].project(star.Shape.Edges)
        r.doc.recompute()
        o.ViewObject.LineColor = (0.88, 0.11, 0.28)
        o.ViewObject.LineWidth = 5
        hide(star)
    r.apply(go, 3, "Το σχήμα «τυλίχτηκε» πάνω στην καμπύλη έδρα")
    r.save()


P.os.makedirs(P.OUT, exist_ok=True)
QtCore.QTimer.singleShot(3500, P.run)

# SPDX-License-Identifier: LGPL-2.1-or-later
"""More Sketcher scenes (the rest of the Sketcher toolbar), same recorder as sketcher_rec.py.

    WT_OUT=<dir> WT_ONLY=Sketcher_CreateLine,... xvfb-run -a freecad tools/gifs/sketcher_more.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/sketcher

Tool-first commands: press the button, then the clicks (the result is made with the
Sketcher API at the same points). Select-first commands (Rec(..., tool_first=False)):
clicks to select, then the button.
"""
import math
import os
import sys

os.environ["WT_NO_AUTORUN"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App  # noqa: E402
import FreeCADGui as Gui  # noqa: E402
import Part  # noqa: E402
import Sketcher  # noqa: E402
from PySide import QtCore  # noqa: E402

import sketcher_rec as R  # noqa: E402
from sketcher_rec import Rec, rubber, scene  # noqa: E402

V = App.Vector
C = Sketcher.Constraint


def done(r, n, text, ms=1700):
    r.cap(n, text)
    r.events.append({"t": "click"})
    r.hold(ms)


def polygon(r, c, p, n):
    """Regular polygon with centre c and first vertex p (like the Sketcher tool)."""
    ang0 = math.atan2(p[1] - c[1], p[0] - c[0])
    rad = math.hypot(p[0] - c[0], p[1] - c[1])
    pts = [(c[0] + rad * math.cos(ang0 + 2 * math.pi * k / n), c[1] + rad * math.sin(ang0 + 2 * math.pi * k / n))
           for k in range(n)]
    return [r.line(pts[k], pts[(k + 1) % n]) for k in range(n)]


def polygon_scene(name, n, title):
    @scene(name)
    def _s():
        r = Rec(name, center=(20, 10), height=44)
        r.edit()
        r.cap(1, "Κλικ στο κέντρο")
        r.click(20, 10)
        if n == 0:
            r.cap(1, "Γράψε το πλήθος των πλευρών (π.χ. 7)")
            r.hold(900)
        r.cap(2, "Πήγαινε σε μια κορυφή")
        k = n or 7
        rubber(r, lambda x, y: polygon(r, (20, 10), (x, y), k), [(26, 12), (33, 16)], 6)
        done(r, 3, "Κλικ: έτοιμο το %s" % title)
        r.save()
    return _s


for _n, _k, _t in (("Sketcher_CreateTriangle", 3, "τρίγωνο"), ("Sketcher_CreateSquare", 4, "τετράγωνο"),
                   ("Sketcher_CreatePentagon", 5, "πεντάγωνο"), ("Sketcher_CreateHexagon", 6, "εξάγωνο"),
                   ("Sketcher_CreateHeptagon", 7, "επτάγωνο"), ("Sketcher_CreateOctagon", 8, "οκτάγωνο"),
                   ("Sketcher_CreateRegularPolygon", 0, "πολύγωνο")):
    polygon_scene(_n, _k, _t)


@scene("Sketcher_CreatePoint")
def s_point():
    r = Rec("Sketcher_CreatePoint", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ όπου θες το σημείο")
    r.click(14, 8)
    r.apply(lambda: r.sk.addGeometry(Part.Point(V(14, 8, 0))), 1, "Έτοιμο το σημείο", 900)
    r.cap(2, "Συνεχίζει: κι άλλο κλικ")
    r.click(30, 15)
    r.apply(lambda: r.sk.addGeometry(Part.Point(V(30, 15, 0))), 2, "Δεύτερο σημείο · Esc για τέλος")
    r.save()


@scene("Sketcher_CreateLine")
def s_line():
    r = Rec("Sketcher_CreateLine", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στην αρχή")
    r.click(2, 2)
    r.cap(2, "Πήγαινε στο τέλος")
    rubber(r, lambda x, y: [r.line((2, 2), (x, y))], [(2, 2), (36, 18)], 7)
    done(r, 3, "Κλικ: έτοιμη η γραμμή")
    r.save()


@scene("Sketcher_Create3PointArc")
def s_arc3():
    r = Rec("Sketcher_Create3PointArc", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στην αρχή")
    r.click(4, 4)
    r.cap(2, "Κλικ στο τέλος")
    r.click(36, 4)
    r.cap(3, "Πήγαινε σε ένα σημείο του τόξου")
    rubber(r, lambda x, y: [r.sk.addGeometry(Part.Arc(V(4, 4, 0), V(x, y, 0), V(36, 4, 0)))],
           [(20, 8), (20, 18)], 6)
    done(r, 4, "Κλικ: τόξο από 3 σημεία")
    r.save()


@scene("Sketcher_Create3PointCircle")
def s_circle3():
    r = Rec("Sketcher_Create3PointCircle", center=(20, 10), height=44)
    pts = [(8, 6), (30, 4), (24, 20)]
    r.edit()
    for k, (x, y) in enumerate(pts[:2]):
        r.cap(k + 1, "Κλικ στο %dο σημείο" % (k + 1))
        r.click(x, y)
    r.cap(3, "Κλικ στο 3ο σημείο")
    r.click(*pts[2])
    r.apply(lambda: r.sk.addGeometry(Part.Circle(V(*pts[0], 0), V(*pts[1], 0), V(*pts[2], 0))), 4,
            "Ο κύκλος περνά και από τα 3")
    r.save()


def ellipse(c, major, minor):
    """Ellipse with centre c, major radius along +X, minor along +Y."""
    return Part.Ellipse(V(c[0] + major, c[1], 0), V(c[0], c[1] + minor, 0), V(c[0], c[1], 0))


@scene("Sketcher_CreateEllipseByCenter")
def s_ell_c():
    r = Rec("Sketcher_CreateEllipseByCenter", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο")
    r.click(20, 10)
    r.cap(2, "Κλικ στο άκρο του μεγάλου άξονα")
    r.click(36, 10)
    r.cap(3, "Πήγαινε για το πλάτος")
    rubber(r, lambda x, y: [r.sk.addGeometry(ellipse((20, 10), 16, max(1, y - 10)))], [(26, 12), (26, 18)], 5)
    done(r, 4, "Κλικ: έτοιμη η έλλειψη")
    r.save()


@scene("Sketcher_CreateEllipseBy3Points")
def s_ell_3():
    r = Rec("Sketcher_CreateEllipseBy3Points", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στο ένα άκρο του άξονα")
    r.click(4, 10)
    r.cap(2, "Κλικ στο άλλο άκρο")
    r.click(36, 10)
    r.cap(3, "Πήγαινε για το πλάτος")
    rubber(r, lambda x, y: [r.sk.addGeometry(ellipse((20, 10), 16, max(1, y - 10)))], [(20, 12), (20, 18)], 5)
    done(r, 4, "Κλικ: έτοιμη η έλλειψη")
    r.save()


@scene("Sketcher_CreateArcOfEllipse")
def s_arc_ell():
    r = Rec("Sketcher_CreateArcOfEllipse", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο")
    r.click(20, 8)
    r.cap(2, "Κλικ στο άκρο του άξονα")
    r.click(36, 8)
    r.cap(3, "Κλικ για πλάτος, αρχή και τέλος")
    r.click(20, 16)
    e = ellipse((20, 8), 16, 8)
    r.apply(lambda: r.sk.addGeometry(Part.ArcOfEllipse(e, 0.0, 2.6)), 4, "Τόξο έλλειψης")
    r.save()


@scene("Sketcher_CreateArcOfHyperbola")
def s_arc_hyp():
    r = Rec("Sketcher_CreateArcOfHyperbola", center=(20, 10), height=48)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο")
    r.click(6, 10)
    r.cap(2, "Κλικ: κορυφή και άνοιγμα")
    r.click(14, 10)
    r.cap(3, "Κλικ στην αρχή και στο τέλος")
    r.click(30, 22)
    h = Part.Hyperbola(V(14, 10, 0), V(6, 16, 0), V(6, 10, 0))
    r.apply(lambda: r.sk.addGeometry(Part.ArcOfHyperbola(h, -1.4, 1.4)), 4, "Τόξο υπερβολής")
    r.save()


@scene("Sketcher_CreateArcOfParabola")
def s_arc_par():
    r = Rec("Sketcher_CreateArcOfParabola", center=(20, 10), height=48)
    r.edit()
    r.cap(1, "Κλικ στην εστία")
    r.click(14, 10)
    r.cap(2, "Κλικ στην κορυφή")
    r.click(8, 10)
    r.cap(3, "Κλικ στην αρχή και στο τέλος")
    r.click(30, 22)
    pb = Part.Parabola()
    pb.Focal = 6
    pb.Center = V(8, 10, 0)
    r.apply(lambda: r.sk.addGeometry(Part.ArcOfParabola(pb, -14, 14)), 4, "Τόξο παραβολής")
    r.save()


@scene("Sketcher_CreateRectangle_Center")
def s_rect_c():
    r = Rec("Sketcher_CreateRectangle_Center", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο")
    r.click(20, 10)
    r.cap(2, "Πήγαινε σε μια γωνία")
    rubber(r, lambda x, y: r.rect(40 - x, 20 - y, x, y, hv=False), [(24, 12), (36, 19)], 6)
    done(r, 3, "Κλικ: κεντραρισμένο ορθογώνιο")
    r.save()


def oblong(r, x0, y0, x1, y1, rad):
    g = [r.line((x0 + rad, y0), (x1 - rad, y0)), r.line((x1, y0 + rad), (x1, y1 - rad)),
         r.line((x1 - rad, y1), (x0 + rad, y1)), r.line((x0, y1 - rad), (x0, y0 + rad))]
    for cx, cy, a0 in ((x1 - rad, y0 + rad, -90), (x1 - rad, y1 - rad, 0), (x0 + rad, y1 - rad, 90),
                       (x0 + rad, y0 + rad, 180)):
        g.append(r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(cx, cy, 0), V(0, 0, 1), rad),
                                                   math.radians(a0), math.radians(a0 + 90))))
    return g


@scene("Sketcher_CreateOblong")
def s_oblong():
    r = Rec("Sketcher_CreateOblong", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στην πρώτη γωνία")
    r.click(2, 0)
    r.cap(2, "Πήγαινε στην απέναντι γωνία")
    rubber(r, lambda x, y: oblong(r, 2, 0, x, y, 4), [(14, 10), (38, 22)], 6)
    done(r, 3, "Κλικ: στρογγυλεμένο ορθογώνιο")
    r.save()


def slot(r, a, b, rad):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    nx, ny = -math.sin(ang) * rad, math.cos(ang) * rad
    g = [r.line((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)), r.line((a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny))]
    g.append(r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(*b, 0), V(0, 0, 1), rad), ang - math.pi / 2, ang + math.pi / 2)))
    g.append(r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(*a, 0), V(0, 0, 1), rad), ang + math.pi / 2, ang + 3 * math.pi / 2)))
    return g


@scene("Sketcher_CreateSlot")
def s_slot():
    r = Rec("Sketcher_CreateSlot", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο του 1ου ημικυκλίου")
    r.click(6, 10)
    r.cap(2, "Πήγαινε στο κέντρο του 2ου")
    rubber(r, lambda x, y: slot(r, (6, 10), (x, y), 5), [(14, 12), (34, 12)], 6)
    done(r, 3, "Κλικ: έτοιμο το αυλάκι")
    r.save()


@scene("Sketcher_CreateArcSlot")
def s_arcslot():
    r = Rec("Sketcher_CreateArcSlot", center=(14, 12), height=44)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο")
    r.click(0, 0)
    r.cap(2, "Κλικ: ακτίνα και αρχή")
    r.click(22, 0)
    r.cap(3, "Γύρνα ως το τέλος")

    def make(x, y):
        a1 = max(0.2, math.atan2(y, x))
        g = []
        for rad in (18, 26):
            g.append(r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(0, 0, 0), V(0, 0, 1), rad), 0, a1)))
        for a, s0, s1 in ((0, math.pi, 2 * math.pi), (a1, a1, a1 + math.pi)):
            c = V(22 * math.cos(a), 22 * math.sin(a), 0)
            g.append(r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(c, V(0, 0, 1), 4), s0, s1)))
        return g
    rubber(r, make, [(20, 8), (8, 21)], 6)
    done(r, 4, "Κλικ: καμπύλο αυλάκι")
    r.save()


def bspline(r, pts, periodic=False, interp=False):
    vs = [V(x, y, 0) for x, y in pts]
    bs = Part.BSplineCurve()
    if interp:
        bs.interpolate(vs, PeriodicFlag=periodic)
    else:
        bs.buildFromPoles(vs, periodic)
    return [r.sk.addGeometry(bs)]


def bspline_scene(name, periodic, interp, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(20, 10), height=44)
        pts = [(2, 2), (12, 20), (24, 4), (36, 18)] if not periodic else [(6, 4), (20, 0), (34, 6), (30, 20), (10, 20)]
        r.edit()
        r.cap(1, "Κλικ σε κάθε σημείο" if interp else "Κλικ στα σημεία ελέγχου")
        for x, y in pts:
            r.click(x, y)
            if interp:
                Gui.Selection.clearSelection()
        r.apply(lambda: bspline(r, pts, periodic, interp), 2,
                ("Δεξί κλικ: " if not periodic else "Δεξί κλικ, κλείνει μόνη της: ") + text)
        r.save()
    return _s


bspline_scene("Sketcher_CreateBSpline", False, False, "η καμπύλη ακολουθεί τα σημεία")
bspline_scene("Sketcher_CreatePeriodicBSpline", True, False, "κλειστή καμπύλη")
bspline_scene("Sketcher_CreateBSplineByInterpolation", False, True, "περνά ΑΠΟ τα σημεία")
bspline_scene("Sketcher_CreatePeriodicBSplineByInterpolation", True, True, "κλειστή, από τα σημεία")


# ---------------------------------------------------------------------------
# constraints
# ---------------------------------------------------------------------------
def dim_scene(name, kind, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(22, 12), height=50)
        a = r.line((4, 4), (36, 20))
        r.edit()
        r.cap(1, "Κλικ στο ένα άκρο")
        r.click(4, 4, "Vertex1")
        r.cap(2, "Κλικ στο άλλο άκρο")
        r.click(36, 20, "Vertex2")
        val = {"DistanceX": 32, "DistanceY": 16, "Distance": round(math.hypot(32, 16), 2)}[kind]
        r.apply(lambda: r.sk.addConstraint(C(kind, a, 1, a, 2, val)), 3, text % val)
        r.save()
    return _s


dim_scene("Sketcher_ConstrainDistanceX", "DistanceX", "Οριζόντια απόσταση %s mm")
dim_scene("Sketcher_ConstrainDistanceY", "DistanceY", "Κάθετη απόσταση %s mm")
dim_scene("Sketcher_ConstrainDistance", "Distance", "Απόσταση %s mm (λοξά)")


def radius_scene(name, kinds, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(22, 10), height=46)
        c = r.circle((10, 10), 7)
        a = r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(34, 6, 0), V(0, 0, 1), 9), 0.3, 2.8))
        r.edit()
        r.cap(1, "Κλικ στον κύκλο")
        r.click(17, 10, "Edge%d" % (c + 1))
        r.apply(lambda: r.sk.addConstraint(C(kinds[0], c, 14 if kinds[0] == "Diameter" else 7)), 2, text[0], 1200)
        r.cap(3, "Κλικ στο τόξο")
        r.click(34 + 9 * math.cos(1.5), 6 + 9 * math.sin(1.5), "Edge%d" % (a + 1))
        r.apply(lambda: r.sk.addConstraint(C(kinds[1], a, 18 if kinds[1] == "Diameter" else 9)), 4, text[1])
        r.save()
    return _s


radius_scene("Sketcher_ConstrainRadiam", ("Diameter", "Radius"), ("Κύκλος: διάμετρος Ø14", "Τόξο: ακτίνα R9"))
radius_scene("Sketcher_ConstrainRadius", ("Radius", "Radius"), ("Ακτίνα R7", "Ακτίνα R9"))
radius_scene("Sketcher_ConstrainDiameter", ("Diameter", "Diameter"), ("Διάμετρος Ø14", "Διάμετρος Ø18"))


def hv_scene(name, kind, a, b, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(22, 12), height=50)
        g = r.line(a, b)
        r.edit()
        r.cap(1, "Κλικ στη γραμμή")
        r.click((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, "Edge%d" % (g + 1))
        r.apply(lambda: r.sk.addConstraint(C(kind, g)), 2, text)
        r.save()
    return _s


hv_scene("Sketcher_ConstrainHorizontal", "Horizontal", (4, 6), (38, 16), "Γίνεται οριζόντια")
hv_scene("Sketcher_ConstrainVertical", "Vertical", (14, 0), (26, 24), "Γίνεται κάθετη")


@scene("Sketcher_ConstrainBlock")
def s_block():
    r = Rec("Sketcher_ConstrainBlock", center=(20, 10), height=44)
    g = bspline(r, [(2, 2), (12, 20), (24, 4), (36, 18)])[0]
    r.edit()
    r.cap(1, "Κλικ στην καμπύλη")
    r.click(19, 10, "Edge%d" % (g + 1))
    r.apply(lambda: r.sk.addConstraint(C("Block", g)), 2, "Κλειδώνει όλη μαζί")
    r.save()


@scene("Sketcher_ToggleDrivingConstraint")
def s_driving():
    r = Rec("Sketcher_ToggleDrivingConstraint", center=(22, 10), height=46, tool_first=False)
    ids = r.rect(4, 0, 40, 20)
    r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 36))
    k = r.sk.addConstraint(C("DistanceY", ids[1], 1, ids[1], 2, 20))
    r.edit()
    r.cap(1, "Κλικ στη διάσταση")
    r.click(26, 14, "Constraint%d" % (k + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.apply(lambda: r.sk.setDriving(k, False), 3, "Μπλε: μόνο δείχνει, δεν κρατάει")
    r.save()


@scene("Sketcher_ToggleActiveConstraint")
def s_active():
    r = Rec("Sketcher_ToggleActiveConstraint", center=(22, 10), height=46, tool_first=False)
    ids = r.rect(4, 0, 40, 20)
    k = r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 36))
    r.edit()
    r.cap(1, "Κλικ στον περιορισμό")
    r.click(22, 10, "Constraint%d" % (k + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.apply(lambda: r.sk.setActive(k, False), 3, "Γκρι: ανενεργός, δεν σβήστηκε")
    r.save()


# ---------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------
@scene("Sketcher_CreateChamfer")
def s_chamfer():
    r = Rec("Sketcher_CreateChamfer", center=(20, 12), height=46)
    a = r.line((0, 0), (36, 0))
    b = r.line((36, 0), (36, 24))
    r.sk.addConstraint(C("Coincident", a, 2, b, 1))
    r.edit()
    r.cap(1, "Κλικ στη γωνία")
    r.click(36, 0, "Vertex2")
    r.apply(lambda: r.sk.fillet(a, 2, 8, True, False, True), 2, "Φάλτσο στη γωνία")
    r.save()


@scene("Sketcher_Split")
def s_split():
    r = Rec("Sketcher_Split", center=(20, 10), height=44)
    a = r.line((2, 10), (38, 10))
    r.edit()
    r.cap(1, "Κλικ πάνω στη γραμμή, όπου θα κοπεί")
    r.click(18, 10)
    r.apply(lambda: r.sk.split(a, V(18, 10, 0)), 2, "Δύο γραμμές, ενωμένες στο σημείο")
    r.save()


@scene("Sketcher_Extend")
def s_extend():
    r = Rec("Sketcher_Extend", center=(20, 10), height=44)
    a = r.line((2, 10), (16, 10))
    c = r.circle((30, 10), 6)
    r.edit()
    r.cap(1, "Κλικ στη γραμμή, κοντά στο άκρο")
    r.click(14, 10, "Edge%d" % (a + 1))
    r.cap(2, "Κλικ στον κύκλο-στόχο")
    r.click(30, 16, "Edge%d" % (c + 1))
    r.apply(lambda: r.sk.extend(a, 10, 2), 3, "Μακραίνει ως τον κύκλο")
    r.save()


@scene("Sketcher_CarbonCopy")
def s_carbon():
    r = Rec("Sketcher_CarbonCopy", center=(20, 10), height=48)
    other = r.doc.addObject("Sketcher::SketchObject", "Other")
    other.Placement.Base = V(0, 0, 0)
    o_ids = []
    p = [(24, 2), (40, 2), (40, 18), (24, 18)]
    for i in range(4):
        o_ids.append(other.addGeometry(Part.LineSegment(V(*p[i], 0), V(*p[(i + 1) % 4], 0))))
    other.addGeometry(Part.Circle(V(32, 10, 0), V(0, 0, 1), 4))
    r.doc.recompute()
    r.edit()
    r.cap(1, "Κλικ σε ακμή του ΑΛΛΟΥ σκαριφήματος")
    r.click(40, 10)

    def copy():
        other.ViewObject.Visibility = False
        r.sk.carbonCopy("Other", False)
    r.apply(copy, 2, "Αντιγράφηκε στο ανοιχτό σκαρίφημα")
    r.save()


def select_first(name, center, height, build, sel, press_text, result, apply_fn):
    @scene(name)
    def _s():
        r = Rec(name, center=center, height=height, tool_first=False)
        ids = build(r)
        r.edit()
        r.cap(1, "Επίλεξε τη γεωμετρία")
        for (x, y), sub in sel(ids):
            r.move(x, y)
            r.events.append({"t": "click"})
            Gui.Selection.addSelection(r.doc.Name, r.sk.Name, sub)
        r.img()
        r.cap(2, "Πάτα το κουμπί")
        r.press()
        for k, (n, (txt, fn)) in enumerate(zip(press_text, apply_fn(r, ids))):
            if n is not None:
                r.cap(3 + k, n)
                r.move(*txt)
                r.events.append({"t": "click"})
            r.apply(fn, 3 + k, result[k])
        r.save()
    return _s


def circle_and_line(r):
    return [r.circle((8, 10), 4), r.line((2, 2), (14, 2))]


select_first("Sketcher_Translate", (22, 10), 50, circle_and_line,
             lambda ids: [((12, 10), "Edge%d" % (ids[0] + 1)), ((8, 2), "Edge%d" % (ids[1] + 1))],
             ["Κλικ: από πού και πού"], ["Μετακινήθηκαν"],
             lambda r, ids: [((34, 10), lambda: r.sk.addMove(ids, V(24, 0, 0)))])

select_first("Sketcher_Rotate", (6, 6), 52, lambda r: [r.circle((20, 0), 3)],
             lambda ids: [((23, 0), "Edge%d" % (ids[0] + 1))],
             ["Κλικ στο κέντρο περιστροφής"], ["Αντίγραφα γύρω από το κέντρο"],
             lambda r, ids: [((0, 0), lambda: [r.sk.addGeometry(Part.Circle(
                 V(20 * math.cos(a), 20 * math.sin(a), 0), V(0, 0, 1), 3)) for a in (math.pi / 2, math.pi, 3 * math.pi / 2)])])

select_first("Sketcher_Scale", (20, 10), 48, lambda r: r.rect(4, 4, 14, 12, hv=False),
             lambda ids: [((9, 4), "Edge%d" % (ids[0] + 1)), ((14, 8), "Edge%d" % (ids[1] + 1)),
                          ((9, 12), "Edge%d" % (ids[2] + 1)), ((4, 8), "Edge%d" % (ids[3] + 1))],
             ["Κλικ στο σημείο βάσης"], ["Μεγάλωσε ×2"],
             lambda r, ids: [((4, 4), lambda: ([r.sk.delGeometry(g) for g in sorted(ids, reverse=True)],
                                               r.rect(4, 4, 24, 20, hv=False)))])

select_first("Sketcher_Offset", (20, 10), 48, lambda r: r.rect(10, 4, 30, 16, hv=False),
             lambda ids: [((20, 4), "Edge%d" % (ids[0] + 1)), ((30, 10), "Edge%d" % (ids[1] + 1)),
                          ((20, 16), "Edge%d" % (ids[2] + 1)), ((10, 10), "Edge%d" % (ids[3] + 1))],
             ["Πήγαινε προς τα έξω και κλικ"], ["Νέο περίγραμμα σε σταθερή απόσταση"],
             lambda r, ids: [((34, 10), lambda: oblong(r, 6, 0, 34, 20, 4))])

select_first("Sketcher_Symmetry", (20, 10), 48,
             lambda r: [r.line((20, -2), (20, 24), True), r.circle((10, 10), 4), r.line((4, 2), (14, 4))],
             lambda ids: [((14, 10), "Edge%d" % (ids[1] + 1)), ((9, 3), "Edge%d" % (ids[2] + 1))],
             ["Κλικ στη γραμμή συμμετρίας"], ["Καθρέφτης στην άλλη μεριά"],
             lambda r, ids: [((20, 20), lambda: (r.circle((30, 10), 4), r.line((36, 2), (26, 4))))])

select_first("Sketcher_RemoveAxesAlignment", (22, 10), 48, lambda r: r.rect(6, 2, 34, 18),
             lambda ids: [((20, 2), "Edge%d" % (ids[0] + 1)), ((34, 10), "Edge%d" % (ids[1] + 1)),
                          ((20, 18), "Edge%d" % (ids[2] + 1)), ((6, 10), "Edge%d" % (ids[3] + 1))],
             [None, "Τώρα μπορεί να γυρίσει"], ["Οριζ./κάθετα → παράλληλα/κάθετα μεταξύ τους", "Γυρίζει χωρίς να χαλάσει"],
             lambda r, ids: [(None, lambda: r.sk.removeAxesAlignment(ids)),
                             ((34, 18), lambda: r.sk.addConstraint(C("Angle", ids[0], math.radians(15))))])

select_first("Sketcher_BSplineConvertToNURBS", (20, 10), 44,
             lambda r: [r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(20, 2, 0), V(0, 0, 1), 14), 0.3, 2.8))],
             lambda ids: [((20, 16), "Edge%d" % (ids[0] + 1))],
             [None], ["Το τόξο έγινε B-spline (με σημεία ελέγχου)"],
             lambda r, ids: [(None, lambda: r.sk.convertToNURBS(ids[0]))])

select_first("Sketcher_BSplineIncreaseDegree", (20, 10), 44, lambda r: bspline(r, [(2, 2), (12, 20), (24, 4), (36, 18)]),
             lambda ids: [((19, 10), "Edge%d" % (ids[0] + 1))],
             [None], ["Βαθμός +1: πιο ευέλικτη"], lambda r, ids: [(None, lambda: r.sk.increaseBSplineDegree(ids[0]))])

def degree4(r):
    g = bspline(r, [(2, 2), (12, 20), (24, 4), (36, 18)])
    r.doc.recompute()
    r.sk.increaseBSplineDegree(g[0])
    return g


select_first("Sketcher_BSplineDecreaseDegree", (20, 10), 44, degree4,
             lambda ids: [((19, 10), "Edge%d" % (ids[0] + 1))],
             [None], ["Βαθμός −1"], lambda r, ids: [(None, lambda: r.sk.decreaseBSplineDegree(ids[0]))])

select_first("Sketcher_SelectConstraints", (22, 10), 46, lambda r: r.rect(4, 0, 40, 20),
             lambda ids: [((22, 0), "Edge%d" % (ids[0] + 1))],
             [None], ["Επιλέχθηκαν οι περιορισμοί της γραμμής"],
             lambda r, ids: [(None, lambda: [Gui.Selection.addSelection(r.doc.Name, r.sk.Name, "Constraint%d" % (k + 1))
                                             for k, c in enumerate(r.sk.Constraints)
                                             if c.First == ids[0] or c.Second == ids[0]])])

select_first("Sketcher_SelectElementsAssociatedWithConstraints", (22, 10), 46,
             lambda r: (lambda ids: ids + [r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 36))])(r.rect(4, 0, 40, 20)),
             lambda ids: [((22, 10), "Constraint%d" % (ids[-1] + 1))],
             [None], ["Επιλέχθηκε η γραμμή του περιορισμού"],
             lambda r, ids: [(None, lambda: Gui.Selection.addSelection(r.doc.Name, r.sk.Name, "Edge%d" % (ids[0] + 1)))])


@scene("Sketcher_JoinCurves")
def s_join():
    r = Rec("Sketcher_JoinCurves", center=(20, 10), height=44, tool_first=False)
    a = bspline(r, [(2, 2), (8, 18), (18, 10)])[0]
    b = bspline(r, [(18, 10), (28, 2), (38, 16)])[0]
    r.edit()
    r.cap(1, "Κλικ στο άκρο της 1ης")
    r.click(18, 10, "Vertex2")
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.apply(lambda: r.sk.join(a, 2, b, 1), 3, "Έγιναν μία καμπύλη")
    r.save()


@scene("Sketcher_BSplineInsertKnot")
def s_knot():
    r = Rec("Sketcher_BSplineInsertKnot", center=(20, 10), height=44, tool_first=False)
    g = bspline(r, [(2, 2), (12, 20), (24, 4), (36, 18)])[0]
    r.edit()
    r.cap(1, "Κλικ στην καμπύλη")
    r.click(19, 10, "Edge%d" % (g + 1))
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.cap(3, "Κλικ όπου θες τον κόμβο")
    r.click(28, 11)
    r.apply(lambda: r.sk.insertBSplineKnot(g, 0.6, 1), 3, "Νέος κόμβος: πιο πολλά σημεία ελέγχου")
    r.save()


def knot_mult(name, delta, text):
    @scene(name)
    def _s():
        r = Rec(name, center=(20, 10), height=44, tool_first=False)
        g = bspline(r, [(2, 2), (8, 18), (16, 4), (24, 20), (30, 4), (38, 16)])[0]
        r.doc.recompute()
        if delta < 0:
            r.sk.modifyBSplineKnotMultiplicity(g, 2, 1)
        knots = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Sketcher/General")
        knots.SetBool("BSplineKnotMultiplicityVisible", True)   # the numbers that change here
        r.edit()
        r.cap(1, "Κλικ σε κόμβο της καμπύλης")
        r.click(20, 12)
        r.cap(2, "Πάτα το κουμπί")
        r.press()
        r.apply(lambda: r.sk.modifyBSplineKnotMultiplicity(g, 2, delta), 3, text)
        r.save()
        knots.SetBool("BSplineKnotMultiplicityVisible", False)
    return _s


knot_mult("Sketcher_BSplineIncreaseKnotMultiplicity", 1, "Πιο «σκληρή» ένωση στον κόμβο")
knot_mult("Sketcher_BSplineDecreaseKnotMultiplicity", -1, "Πιο ομαλή ένωση στον κόμβο")


@scene("Sketcher_ConstrainGroup")
def s_group():
    r = Rec("Sketcher_ConstrainGroup", center=(22, 10), height=46, tool_first=False)
    ids = [r.circle((10, 10), 4), r.circle((24, 10), 4), r.line((4, 2), (30, 2))]
    r.edit()
    r.cap(1, "Επίλεξε τα στοιχεία")
    for (x, y), g in (((14, 10), ids[0]), ((28, 10), ids[1]), ((16, 2), ids[2])):
        r.move(x, y)
        r.events.append({"t": "click"})
        Gui.Selection.addSelection(r.doc.Name, r.sk.Name, "Edge%d" % (g + 1))
    r.img()
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    Gui.runCommand("Sketcher_ConstrainGroup")
    R.pump(500)
    r.cap(3, "Κινούνται σαν ένα κομμάτι")
    r.img(blend=True)
    r.hold(1800)
    r.save()


@scene("Sketcher_CreateText")
def s_text():
    r = Rec("Sketcher_CreateText", center=(20, 8), height=46)
    r.edit()
    r.cap(1, "Κλικ στην αρχή της βάσης")
    r.click(2, 2)
    r.cap(2, "Κλικ στο τέλος (πλάτος)")
    r.click(38, 2)
    r.cap(3, "Γράψε το κείμενο, OK")
    r.hold(700)
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    def make():   # what the tool does (DrawSketchHandlerText.h, FreeCAD 26.3)
        h = r.line((2, 2), (38, 2), construction=True)
        r.sk.addConstraint(Sketcher.Constraint("Text", [h, 0], "CNC", font, False))
        r.sk.setTextAndFont(len(r.sk.Constraints) - 1, "CNC", font, False, False)
    r.apply(make, 4, "Γράμματα-γεωμετρία μέσα στο σκαρίφημα")
    r.save()


R.os.makedirs(R.OUT, exist_ok=True)
QtCore.QTimer.singleShot(3500, R.run)

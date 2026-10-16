# SPDX-License-Identifier: LGPL-2.1-or-later
"""Record Sketcher scenes inside a REAL FreeCAD (step 1 of 2).

    WT_OUT=<dir> [WT_ONLY=name,name] xvfb-run -a freecad tools/gifs/sketcher_rec.py

For every scenario it saves PNG key frames of the 3D view (light theme set below)
and an events.json with the cursor path, clicks and the numbered Greek captions.
tools/gifs/sketcher_gifs.py turns that into the animated GIF (cursor, click rings,
step badges). Build-time tool only; it changes the FreeCAD user parameters of the
HOME it runs in, so run it with a throw-away HOME.
"""
import json
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from PySide import QtCore, QtWidgets

OUT = os.environ.get("WT_OUT", "/tmp/sketcher_rec")
ONLY = {x for x in os.environ.get("WT_ONLY", "").split(",") if x}
V = App.Vector

THEME = {   # modern light look; keys are FreeCAD View preferences (26.3)
    "BackgroundColor": "#F4F6FA", "SketchEdgeColor": "#1E293B", "SketchVertexColor": "#1E293B",
    "EditedEdgeColor": "#1E293B", "EditedVertexColor": "#1E293B", "FullyConstrainedColor": "#16A34A",
    "ConstructionColor": "#3B82F6", "ConstrainedIcoColor": "#E11D48", "ConstrainedDimColor": "#E11D48",
    "NonDrivingConstrDimColor": "#64748B", "CursorTextColor": "#2563EB", "CreateLineColor": "#94A3B8",
    "SelectionColor": "#10B981", "HighlightColor": "#F59E0B", "GridLineColor": "#EDF1F6",
}


def pump(ms=80):
    t = QtCore.QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.005)


def set_theme():
    pv = App.ParamGet("User parameter:BaseApp/Preferences/View")
    for k, v in THEME.items():
        pv.SetUnsigned(k, int(v[1:] + "FF", 16))
    pv.SetBool("ShowNaviCube", False)
    pv.SetBool("CornerCoordSystem", False)
    App.ParamGet("User parameter:BaseApp/Preferences/Mod/Sketcher/View").SetInt("MarkerSize", 9)


class Rec:
    """One scenario: a sketch in edit mode, a fixed camera and a list of events."""

    def __init__(self, name, center=(25, 10), height=70):
        self.name = name
        self.dir = os.path.join(OUT, name)
        os.makedirs(self.dir, exist_ok=True)
        self.doc = App.newDocument(name)
        self.sk = self.doc.addObject("Sketcher::SketchObject", "Sketch")
        self.events = []
        self.n = 0
        self.center, self.height = center, height

    # -- setup ---------------------------------------------------------------
    def edit(self):
        self.doc.recompute()
        try:   # thicker lines: the GIF is the view scaled down 2x
            self.sk.ViewObject.LineWidth = 4
            self.sk.ViewObject.PointSize = 8
        except Exception:
            pass
        Gui.ActiveDocument.setEdit(self.sk.Name)
        pump(600)
        self.v = Gui.ActiveDocument.ActiveView
        self.v.setCameraType("Orthographic")
        self.v.viewTop()
        cam = self.v.getCameraNode()
        cam.position.setValue(self.center[0], self.center[1], 100)
        cam.height.setValue(self.height)
        pump(300)
        self.W, self.H = self.v.getSize()
        self.img()   # the untouched scene: first frame of the GIF

    def line(self, a, b, construction=False):
        i = self.sk.addGeometry(Part.LineSegment(V(*a, 0), V(*b, 0)), construction)
        return i

    def circle(self, c, r):
        return self.sk.addGeometry(Part.Circle(V(*c, 0), V(0, 0, 1), r))

    def rect(self, x0, y0, x1, y1, hv=True):
        p = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        ids = [self.line(p[i], p[(i + 1) % 4]) for i in range(4)]
        for i in range(4):
            self.sk.addConstraint(Sketcher.Constraint("Coincident", ids[i], 2, ids[(i + 1) % 4], 1))
        if hv:
            for i, k in ((0, "Horizontal"), (2, "Horizontal"), (1, "Vertical"), (3, "Vertical")):
                self.sk.addConstraint(Sketcher.Constraint(k, ids[i]))
        return ids

    # -- recording -------------------------------------------------------------
    def px(self, x, y):
        """Model point (mm) -> pixel in the saved image (origin top-left)."""
        u, w = self.v.getPointOnViewport(V(x, y, 0))
        return [int(u), int(self.H - w)]

    def shot(self):
        self.doc.recompute()
        pump(150)
        f = "k%03d.png" % self.n
        self.n += 1
        self.v.saveImage(os.path.join(self.dir, f), self.W, self.H, THEME["BackgroundColor"])
        return f

    def img(self, blend=False):
        self.events.append({"t": "img", "f": self.shot(), "blend": blend})

    def cap(self, n, text):
        self.events.append({"t": "cap", "n": n, "text": text})

    def move(self, x, y, ms=500):
        self.events.append({"t": "move", "to": self.px(x, y), "ms": ms})

    def click(self, x, y, sub=None):
        """Move there, click; `sub` (Vertex1, Edge2, RootPoint, V_Axis...) gets selected."""
        self.move(x, y)
        self.events.append({"t": "click"})
        if sub:
            Gui.Selection.addSelection(self.doc.Name, self.sk.Name, sub)
            self.img()

    def hold(self, ms):
        self.events.append({"t": "hold", "ms": ms})

    def apply(self, fn, n, text, ms=1800):
        """The tool reacts: constraint added / geometry created. Morph to the result."""
        Gui.Selection.clearSelection()
        fn()
        self.cap(n, text)
        self.img(blend=True)
        self.hold(ms)

    def save(self, tool_px=None):
        meta = {"name": self.name, "size": [self.W, self.H], "events": self.events}
        with open(os.path.join(self.dir, "events.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        Gui.ActiveDocument.resetEdit()
        App.closeDocument(self.doc.Name)
        pump(300)


SCENES = {}


def scene(name):
    def deco(fn):
        SCENES[name] = fn
        return fn
    return deco


C = Sketcher.Constraint


# ---------------------------------------------------------------------------
# constraints (tool pressed first = "continue mode", then clicks)
# ---------------------------------------------------------------------------
@scene("Sketcher_ConstrainSymmetric")
def s_symmetric():
    r = Rec("Sketcher_ConstrainSymmetric", center=(8, 6), height=62)
    ids = r.rect(6, -6, 46, 18)
    r.sk.addConstraint(C("DistanceX", ids[0], 1, ids[0], 2, 40))
    r.sk.addConstraint(C("DistanceY", ids[1], 1, ids[1], 2, 24))
    r.edit()
    r.cap(0, "Ορθογώνιο εκτός κέντρου")
    r.hold(1200)
    r.cap(1, "Κλικ στη μία γωνία")
    r.click(6, -6, "Vertex1")
    r.cap(2, "Κλικ στην απέναντι γωνία")
    r.click(46, 18, "Vertex4")   # end of the 2nd line = top right corner
    r.cap(3, "ΤΕΛΕΥΤΑΙΟ κλικ: το κέντρο συμμετρίας")
    r.click(0, 0, "RootPoint")
    r.apply(lambda: r.sk.addConstraint(C("Symmetric", ids[0], 1, ids[1], 2, -1, 1)),
            4, "Κεντραρισμένο στην αρχή των αξόνων")
    r.save()


@scene("Sketcher_ConstrainHorVer")
def s_horver():
    r = Rec("Sketcher_ConstrainHorVer", center=(25, 12), height=55)
    a = r.line((2, 4), (44, 12))
    b = r.line((52, 0), (58, 30))
    r.edit()
    r.cap(0, "Δύο γραμμές λίγο στραβές")
    r.hold(1000)
    r.cap(1, "Κλικ στη γραμμή")
    r.click(23, 8, "Edge%d" % (a + 1))
    r.apply(lambda: r.sk.addConstraint(C("Horizontal", a)), 2, "Γίνεται οριζόντια", 1300)
    r.cap(3, "Κλικ στην άλλη γραμμή")
    r.click(55, 15, "Edge%d" % (b + 1))
    r.apply(lambda: r.sk.addConstraint(C("Vertical", b)), 4, "Γίνεται κάθετη")
    r.save()


@scene("Sketcher_ConstrainParallel")
def s_parallel():
    r = Rec("Sketcher_ConstrainParallel", center=(25, 12), height=55)
    a = r.line((0, 0), (40, 6))
    b = r.line((5, 22), (48, 34))
    r.sk.addConstraint(C("DistanceX", a, 1, a, 2, 40))
    r.edit()
    r.cap(1, "Κλικ στην πρώτη γραμμή")
    r.click(20, 3, "Edge%d" % (a + 1))
    r.cap(2, "Κλικ στη δεύτερη γραμμή")
    r.click(26, 28, "Edge%d" % (b + 1))
    r.apply(lambda: r.sk.addConstraint(C("Parallel", a, b)), 3, "Γίνονται παράλληλες")
    r.save()


@scene("Sketcher_ConstrainPerpendicular")
def s_perp():
    r = Rec("Sketcher_ConstrainPerpendicular", center=(24, 14), height=55)
    a = r.line((0, 0), (44, 0))
    b = r.line((20, 2), (34, 30))
    r.sk.addConstraint(C("Horizontal", a))
    r.sk.addConstraint(C("PointOnObject", b, 1, a))
    r.edit()
    r.cap(1, "Κλικ στην πρώτη γραμμή")
    r.click(8, 0, "Edge%d" % (a + 1))
    r.cap(2, "Κλικ στη δεύτερη γραμμή")
    r.click(27, 16, "Edge%d" % (b + 1))
    r.apply(lambda: r.sk.addConstraint(C("Perpendicular", a, b)), 3, "Γωνία 90° ανάμεσά τους")
    r.save()


@scene("Sketcher_ConstrainTangent")
def s_tangent():
    r = Rec("Sketcher_ConstrainTangent", center=(22, 12), height=55)
    a = r.line((-6, 0), (50, 0))
    c = r.circle((22, 18), 10)
    r.sk.addConstraint(C("Horizontal", a))
    r.edit()
    r.cap(1, "Κλικ στη γραμμή")
    r.click(2, 0, "Edge%d" % (a + 1))
    r.cap(2, "Κλικ στον κύκλο")
    r.click(32, 18, "Edge%d" % (c + 1))
    r.apply(lambda: r.sk.addConstraint(C("Tangent", a, c)), 3, "Ο κύκλος ακουμπά τη γραμμή")
    r.save()


@scene("Sketcher_ConstrainEqual")
def s_equal():
    r = Rec("Sketcher_ConstrainEqual", center=(25, 10), height=47)
    c1 = r.circle((8, 10), 9)
    c2 = r.circle((40, 10), 4)
    r.edit()
    r.cap(1, "Κλικ στον πρώτο κύκλο")
    r.click(17, 10, "Edge%d" % (c1 + 1))
    r.cap(2, "Κλικ στον δεύτερο κύκλο")
    r.click(44, 10, "Edge%d" % (c2 + 1))
    r.apply(lambda: r.sk.addConstraint(C("Equal", c1, c2)), 3, "Ίδια ακτίνα")
    r.save()


@scene("Sketcher_ConstrainCoincidentUnified")
def s_coincident():
    r = Rec("Sketcher_ConstrainCoincidentUnified", center=(24, 12), height=55)
    a = r.line((0, 0), (22, 4))
    b = r.line((28, 10), (46, 26))
    p = r.sk.addGeometry(Part.Point(V(14, 22, 0)))
    r.edit()
    r.cap(1, "Κλικ στο άκρο της πρώτης")
    r.click(22, 4, "Vertex2")
    r.cap(2, "Κλικ στο άκρο της δεύτερης")
    r.click(28, 10, "Vertex3")
    r.apply(lambda: r.sk.addConstraint(C("Coincident", a, 2, b, 1)), 3, "Τα δύο σημεία ενώνονται σε ένα", 1300)
    r.cap(4, "Σημείο και γραμμή:")
    r.click(14, 22, "Vertex5")
    r.click(36, 16, "Edge%d" % (b + 1))
    r.apply(lambda: r.sk.addConstraint(C("PointOnObject", p, 1, b)), 5, "Το σημείο πάει πάνω στη γραμμή")
    r.save()


@scene("Sketcher_ConstrainLock")
def s_lock():
    r = Rec("Sketcher_ConstrainLock", center=(18, 12), height=47)
    p = r.sk.addGeometry(Part.Point(V(30, 18, 0)))
    r.edit()
    r.cap(1, "Κλικ σε ένα σημείο")
    r.click(30, 18, "Vertex1")
    r.apply(lambda: (r.sk.addConstraint(C("DistanceX", -1, 1, p, 1, 30)),
                     r.sk.addConstraint(C("DistanceY", -1, 1, p, 1, 18))),
            2, "Κλειδώνει με δύο διαστάσεις")
    r.save()


@scene("Sketcher_Dimension")
def s_dimension():
    r = Rec("Sketcher_Dimension", center=(24, 12), height=55)
    a = r.line((0, 0), (42, 0))
    c = r.circle((30, 20), 7)
    r.sk.addConstraint(C("Horizontal", a))
    r.edit()
    r.cap(1, "Κλικ στη γραμμή: προτείνει μήκος")
    r.click(20, 0, "Edge%d" % (a + 1))
    r.cap(2, "Κλικ σε κενό σημείο")
    r.click(20, -8)
    r.apply(lambda: r.sk.addConstraint(C("Distance", a, 42)), 3, "Μήκος 42 mm", 1200)
    r.cap(4, "Κλικ στον κύκλο: διάμετρος")
    r.click(37, 20, "Edge%d" % (c + 1))
    r.click(46, 28)
    r.apply(lambda: r.sk.addConstraint(C("Diameter", c, 14)), 5, "Διάμετρος 14 mm (M = ακτίνα)")
    r.save()


@scene("Sketcher_ConstrainAngle")
def s_angle():
    r = Rec("Sketcher_ConstrainAngle", center=(22, 12), height=47)
    a = r.line((0, 0), (40, 0))
    b = r.line((0, 0), (30, 22))
    r.sk.addConstraint(C("Horizontal", a))
    r.sk.addConstraint(C("Coincident", a, 1, b, 1))
    r.edit()
    r.cap(1, "Κλικ στην πρώτη γραμμή")
    r.click(30, 0, "Edge%d" % (a + 1))
    r.cap(2, "Κλικ στη δεύτερη γραμμή")
    r.click(20, 14.7, "Edge%d" % (b + 1))
    r.apply(lambda: r.sk.addConstraint(C("Angle", a, b, 0.5235987756)), 3, "Γωνία 30° ανάμεσά τους")
    r.save()


# ---------------------------------------------------------------------------
# creation tools: geometry follows the cursor (rubber band), recorded frame by frame
# ---------------------------------------------------------------------------
def rubber(r, make, path, n=6, cap=None):
    """Temporary geometry made by make(x, y) while the cursor moves along `path`."""
    ids = []
    for i in range(1, n + 1):
        x = path[0][0] + (path[1][0] - path[0][0]) * i / n
        y = path[0][1] + (path[1][1] - path[0][1]) * i / n
        for g in sorted(ids, reverse=True):
            r.sk.delGeometry(g)
        ids = make(x, y)
        r.move(x, y, 110)
        r.img()
    return ids


@scene("Sketcher_CreateRectangle")
def s_rectangle():
    r = Rec("Sketcher_CreateRectangle", center=(22, 12), height=47)
    r.edit()
    r.cap(1, "Κλικ στην πρώτη γωνία")
    r.click(2, 0)
    r.cap(2, "Πήγαινε στην απέναντι γωνία")

    def make(x, y):
        return r.rect(2, 0, x, y, hv=False)
    ids = rubber(r, make, [(2, 0), (40, 24)], 7)
    for g in sorted(ids, reverse=True):
        r.sk.delGeometry(g)
    r.cap(3, "Κλικ: έτοιμο το ορθογώνιο")
    r.events.append({"t": "click"})
    r.apply(lambda: r.rect(2, 0, 40, 24), 3, "Κλικ: έτοιμο το ορθογώνιο")
    r.save()


@scene("Sketcher_CreateCircle")
def s_circle():
    r = Rec("Sketcher_CreateCircle", center=(20, 10), height=44)
    r.edit()
    r.cap(1, "Κλικ στο κέντρο")
    r.click(18, 10)
    r.cap(2, "Πήγαινε προς τα έξω (ακτίνα)")
    ids = rubber(r, lambda x, y: [r.circle((18, 10), max(0.5, ((x - 18) ** 2 + (y - 10) ** 2) ** 0.5))],
                 [(18, 10), (32, 16)], 7)
    r.cap(3, "Κλικ: έτοιμος ο κύκλος")
    r.events.append({"t": "click"})
    r.hold(1600)
    r.save()


@scene("Sketcher_CreatePolyline")
def s_polyline():
    r = Rec("Sketcher_CreatePolyline", center=(22, 12), height=47)
    r.edit()
    pts = [(0, 0), (40, 0), (40, 20), (12, 26), (0, 0)]
    r.cap(1, "Κλικ στο πρώτο σημείο")
    r.click(*pts[0])
    prev = None
    for k in range(1, len(pts)):
        r.cap(min(k + 1, 3), "Κλικ στο επόμενο σημείο" if k < len(pts) - 1 else "Κλικ στο πρώτο: κλειστό σχήμα")
        ids = rubber(r, lambda x, y, a=pts[k - 1]: [r.line(a, (x, y))], [pts[k - 1], pts[k]], 4)
        r.events.append({"t": "click"})
        if prev is not None:
            r.sk.addConstraint(C("Coincident", prev, 2, ids[0], 1))
        prev = ids[0]
    r.cap(4, "Δεξί κλικ ή Esc για τέλος")
    r.img()
    r.hold(1600)
    r.save()


@scene("Sketcher_CreateArc")
def s_arc():
    r = Rec("Sketcher_CreateArc", center=(20, 10), height=44)
    r.edit()
    import math
    c = (18, 4)
    R = 16
    r.cap(1, "Κλικ στο κέντρο")
    r.click(*c)
    r.cap(2, "Κλικ στην αρχή (ορίζει την ακτίνα)")
    r.click(c[0] + R, c[1])
    r.cap(3, "Γύρνα και κλικ στο τέλος")
    ids = []
    for i in range(1, 8):
        a = math.pi * 0.85 * i / 7
        for g in sorted(ids, reverse=True):
            r.sk.delGeometry(g)
        ids = [r.sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(*c, 0), V(0, 0, 1), R), 0.0, a))]
        r.move(c[0] + R * math.cos(a), c[1] + R * math.sin(a), 110)
        r.img()
    r.events.append({"t": "click"})
    r.hold(1600)
    r.save()


@scene("Sketcher_Trimming")
def s_trim():
    r = Rec("Sketcher_Trimming", center=(20, 10), height=44)
    a = r.line((-4, 10), (44, 10))
    c = r.circle((20, 10), 10)
    r.edit()
    r.cap(1, "Ποντίκι πάνω στο κομμάτι που περισσεύει")
    r.move(20, 10.2, 700)
    try:
        Gui.Selection.setPreselection(r.sk, "Edge%d" % (a + 1))
    except Exception:
        pass
    r.img()
    r.cap(2, "Κλικ: κόβεται ως τις τομές")
    r.events.append({"t": "click"})

    def trim():
        r.sk.delGeometry(a)
        r.line((-4, 10), (10, 10))
        r.line((30, 10), (44, 10))
    Gui.Selection.clearPreselection()
    r.apply(trim, 2, "Κλικ: κόβεται ως τις τομές")
    r.save()


@scene("Sketcher_CreateFillet")
def s_fillet():
    r = Rec("Sketcher_CreateFillet", center=(20, 10), height=44)
    a = r.line((0, 0), (36, 0))
    b = r.line((36, 0), (36, 26))
    r.sk.addConstraint(C("Coincident", a, 2, b, 1))
    r.edit()
    r.cap(1, "Κλικ στη γωνία")
    r.click(36, 0, "Vertex2")

    def fillet():
        r.sk.fillet(a, b, V(30, 0, 0), V(36, 6, 0), 8)
    r.apply(fillet, 2, "Η γωνία στρογγυλεύει")
    r.save()


@scene("Sketcher_ToggleConstruction")
def s_construction():
    r = Rec("Sketcher_ToggleConstruction", center=(20, 10), height=44)
    ids = r.rect(0, 0, 36, 22)
    d = r.line((0, 0), (36, 22))
    r.edit()
    r.cap(1, "Επίλεξε μια γραμμή βοηθό")
    r.click(18, 11, "Edge%d" % (d + 1))
    r.cap(2, "Πάτα το κουμπί Construction")
    r.hold(700)
    r.apply(lambda: r.sk.toggleConstruction(d), 3, "Μπλε = βοηθητική γραμμή")
    r.save()


def run():
    log = open(os.path.join(OUT, "rec_log.txt"), "w")
    try:
        set_theme()
        Gui.activateWorkbench("SketcherWorkbench")
        mw = Gui.getMainWindow()
        mw.resize(1098, 658)          # 3D view ~ 832 x 500 = 2 x the GIF size
        pump(500)
        for name, fn in SCENES.items():
            if ONLY and name not in ONLY:
                continue
            try:
                fn()
                log.write("OK %s\n" % name)
            except Exception:
                log.write("FAIL %s\n%s\n" % (name, traceback.format_exc()))
            log.flush()
    finally:
        log.close()
        QtCore.QTimer.singleShot(200, lambda: os._exit(0))


os.makedirs(OUT, exist_ok=True)
QtCore.QTimer.singleShot(3500, run)

# SPDX-License-Identifier: LGPL-2.1-or-later
"""Record the Part Design task-panel settings in a REAL FreeCAD, step 1 of 2.

    WT_OUT=<dir> [WT_ONLY=pad_type,...] xvfb-run -a freecad tools/gifs/pd_rec.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/pd

Each scene builds a small Body and changes ONE setting of a feature (Type, Sides,
Taper, Angle, Hole type...): FreeCAD recomputes the real result and we save a key
frame per value with a Greek caption. Same events.json format as part_rec.py.
Run with a throw-away HOME: it changes FreeCAD's view preferences.
"""
import json
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher  # noqa: F401  (registers Sketcher::SketchObject)
from PySide import QtCore, QtWidgets

try:
    from pivy import coin  # noqa: F401  (needed by View3DInventor.getCameraNode)
except ImportError:
    coin = None

OUT = os.environ.get("WT_OUT", "/tmp/pd_rec")
ONLY = {x for x in os.environ.get("WT_ONLY", "").split(",") if x}
V = App.Vector
# Sharp 3x GIFs (2026-10-17): record with QT_SCALE_FACTOR=1.5 (FreeCAD then draws fonts, markers
# and lines like on a 150 % screen and the view is 1248 x 750 pixels). WT_REC_SCALE renders the key
# frames even bigger than the view; sketcher_gifs.py works out the scale from the pictures.
REC_SCALE = float(os.environ.get("WT_REC_SCALE", "1"))
BG = "#F4F6FA"
BODY = (0.39, 0.40, 0.95)      # the result: indigo
SKETCH = (0.96, 0.62, 0.04)    # the sketch (profile): amber


def pump(ms=80):
    t = QtCore.QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.005)


def set_theme():
    pv = App.ParamGet("User parameter:BaseApp/Preferences/View")
    for k, v in {"BackgroundColor": BG, "SelectionColor": "#10B981", "HighlightColor": "#F59E0B"}.items():
        pv.SetUnsigned(k, int(v[1:] + "FF", 16))
    pv.SetBool("Simple", True)
    pv.SetBool("Gradient", False)
    pv.SetBool("ShowNaviCube", False)
    pv.SetBool("CornerCoordSystem", False)


class Rec:
    def __init__(self, name):
        self.name = name
        self.dir = os.path.join(OUT, name)
        os.makedirs(self.dir, exist_ok=True)
        self.doc = App.newDocument(name)
        self.body = self.doc.addObject("PartDesign::Body", "Body")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", self.body)
        self.events, self.n = [], 0

    def base(self, shape):
        """A ready-made solid as the Body's base feature (support for To first / Through all...)."""
        b = self.doc.addObject("Part::Feature", "Base")
        b.Shape = shape
        b.ViewObject.Visibility = False
        self.body.BaseFeature = b
        self.doc.recompute()

    def sketch(self, plane, geo, z=0.0):
        """Sketch on an origin plane (0 XY, 1 XZ, 2 YZ), optionally lifted by z along its normal."""
        sk = self.body.newObject("Sketcher::SketchObject", "Sketch")
        sk.AttachmentSupport = [(self.body.Origin.OriginFeatures[3 + plane], "")]
        sk.MapMode = "FlatFace"
        sk.AttachmentOffset = App.Placement(V(0, 0, z), App.Rotation())
        for g in geo:
            sk.addGeometry(g)
        self.doc.recompute()
        return sk

    def feature(self, typ, profile, **props):
        f = self.body.newObject("PartDesign::" + typ, typ)
        if profile is not None:
            f.Profile = profile
        for k, v in props.items():
            setattr(f, k, v)
        self.doc.recompute()
        return f

    def look(self, see_sketch=None, transparency=0):
        vo = self.body.ViewObject
        try:
            vo.ShapeAppearance = [App.Material(DiffuseColor=BODY)]
        except Exception:
            vo.ShapeColor = BODY
        vo.Transparency = transparency
        vo.LineColor = (0.12, 0.16, 0.23)
        vo.LineWidth = 2
        for o in self.doc.Objects:
            if o.TypeId == "Sketcher::SketchObject":
                o.ViewObject.Visibility = o is see_sketch
                o.ViewObject.LineColor = SKETCH
                o.ViewObject.LineWidth = 5
                try:
                    o.ViewObject.PointColor = SKETCH
                except Exception:
                    pass
        self.body.ViewObject.Visibility = True

    def view(self, zoom=1.0, orient="iso"):
        self.doc.recompute()
        Gui.Selection.clearSelection()
        pump(300)
        self.v = Gui.ActiveDocument.ActiveView
        self.v.setCameraType("Orthographic")
        {"iso": self.v.viewIsometric, "front": self.v.viewFront, "top": self.v.viewTop,
         "right": self.v.viewRight}[orient]()
        self.v.fitAll()
        cam = self.v.getCameraNode()
        cam.height.setValue(cam.height.getValue() * zoom)
        pump(300)
        self.W, self.H = self.v.getSize()

    def shot(self):
        self.doc.recompute()
        pump(200)
        f = "k%03d.png" % self.n
        self.n += 1
        self.v.saveImage(os.path.join(self.dir, f), int(round(self.W * REC_SCALE)), int(round(self.H * REC_SCALE)), BG)
        return f

    def state(self, text, ms=1700, blend=True):
        """Save the current result with its caption (no step number: it is a setting, not a click)."""
        self.events.append({"t": "cap", "n": 0, "text": text})
        first = self.n == 0
        self.events.append({"t": "img", "f": self.shot(), "blend": blend and not first})
        self.events.append({"t": "hold", "ms": ms})

    def save(self):
        meta = {"name": self.name, "size": [self.W, self.H], "scale": REC_SCALE, "icon": None, "cursor": False,
                "events": self.events}
        with open(os.path.join(self.dir, "events.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        App.closeDocument(self.doc.Name)
        pump(300)


SCENES = {}


def scene(name):
    def deco(fn):
        SCENES[name] = fn
        return fn
    return deco


def circle(x, y, r):
    return [Part.Circle(V(x, y, 0), V(0, 0, 1), r)]


def rect(x0, y0, x1, y1):
    p = [V(x0, y0, 0), V(x1, y0, 0), V(x1, y1, 0), V(x0, y1, 0)]
    return [Part.LineSegment(p[i], p[(i + 1) % 4]) for i in range(4)]


def plate(lx=60, ly=40, h=20):
    return Part.makeBox(lx, ly, h, V(-lx / 2, -ly / 2, 0))


# ---------------------------------------------------------------------------
@scene("pad_sides")
def s_pad_sides():
    r = Rec("pad_sides")
    sk = r.sketch(0, rect(-12, -8, 12, 8))
    pad = r.feature("Pad", sk, Length=20)
    r.look(see_sketch=sk, transparency=35)
    pad.SideType = "Two sides"
    pad.Length2 = 20
    r.doc.recompute()
    r.view(1.15)                                    # frame the largest state
    pad.SideType = "One side"
    r.state("One sided: προς τη μία μεριά (20 mm)")
    pad.SideType = "Two sides"
    pad.Length2 = 8
    r.state("Two sided: 20 mm πάνω + 8 mm κάτω")
    pad.SideType = "Symmetric"
    r.state("Symmetric: μισό-μισό γύρω από το σκαρίφημα", 2200)
    r.save()


def two_plates():
    """Two horizontal plates (z 20–25 and 40–45) held by a back wall: something to stop at."""
    s = Part.makeBox(60, 40, 5, V(-30, -20, 20)).fuse(Part.makeBox(60, 40, 5, V(-30, -20, 40)))
    s = s.fuse(Part.makeBox(60, 5, 25, V(-30, 15, 20)))
    return s.removeSplitter()


@scene("pad_type")
def s_pad_type():
    r = Rec("pad_type")
    r.base(two_plates())
    sk = r.sketch(0, circle(0, -5, 7))
    pad = r.feature("Pad", sk, Length=10)
    r.look(see_sketch=sk, transparency=45)
    r.view(1.2)
    r.state("Dimension: όσο γράφεις (10 mm)")
    pad.Type = "UpToFirst"
    r.state("To first: ως την πρώτη έδρα που συναντά")
    pad.Type = "UpToLast"
    r.state("To last: ως την τελευταία έδρα", 2200)
    r.save()


@scene("pocket_type")
def s_pocket_type():
    r = Rec("pocket_type")
    r.base(plate())
    sk = r.sketch(0, circle(0, 0, 8), z=20)
    pk = r.feature("Pocket", sk, Length=8)
    r.look(see_sketch=sk, transparency=45)
    r.view(1.1)
    r.state("Dimension: βάθος 8 mm")
    pk.Type = "ThroughAll"
    r.state("Through all: διαμπερές", 2200)
    r.save()


@scene("pad_taper")
def s_pad_taper():
    r = Rec("pad_taper")
    sk = r.sketch(0, rect(-12, -12, 12, 12))
    pad = r.feature("Pad", sk, Length=24)
    r.look(see_sketch=sk, transparency=20)
    pad.TaperAngle = 15
    r.doc.recompute()
    r.view(1.15, "front")
    pad.TaperAngle = 0
    r.state("Taper 0°: ίσια τοιχώματα")
    pad.TaperAngle = 15
    r.state("Taper +15°: φαρδαίνει")
    pad.TaperAngle = -15
    r.state("Taper −15°: στενεύει", 2200)
    r.save()


@scene("pad_reversed")
def s_pad_reversed():
    r = Rec("pad_reversed")
    sk = r.sketch(0, rect(-12, -8, 12, 8))
    pad = r.feature("Pad", sk, Length=15)
    r.look(see_sketch=sk, transparency=35)
    pad.Midplane = False
    pad.SideType = "Symmetric"
    pad.Length = 30
    r.doc.recompute()
    r.view(1.15)
    pad.SideType = "One side"
    pad.Length = 15
    r.state("Κανονικά: προς τα πάνω")
    pad.Reversed = True
    r.state("Reversed: προς την άλλη μεριά", 2200)
    r.save()


@scene("revolution_angle")
def s_revolution():
    r = Rec("revolution_angle")
    # profile on XZ, beside the vertical sketch axis
    sk = r.sketch(1, rect(10, 0, 16, 20))
    rev = r.feature("Revolution", sk, Angle=360)
    rev.ReferenceAxis = (sk, ["V_Axis"])
    r.doc.recompute()
    r.look(see_sketch=sk, transparency=20)
    r.view(1.1)
    for a in (90, 180, 270, 360):
        rev.Angle = a
        r.state("Γωνία %d° γύρω από τον άξονα" % a, 1300 if a < 360 else 2200)
    r.save()


def hole_scene(name, states, zoom=0.6, orient="iso"):
    r = Rec(name)
    r.base(plate(40, 30, 16))
    sk = r.sketch(0, circle(0, 0, 2.5), z=16)
    h = r.feature("Hole", sk)
    h.ThreadType = "ISOMetricProfile"
    r.doc.recompute()
    sizes = h.getEnumerationsOfProperty("ThreadSize")
    h.ThreadSize = next(x for x in sizes if x.split("x")[0] == "M5")
    h.DepthType = "ThroughAll"
    r.doc.recompute()
    r.look(transparency=55)
    r.view(zoom, orient)
    for fn, text in states:
        fn(h)
        r.state(text)
    r.save()


@scene("hole_type")
def s_hole_type():
    def clearance(h):
        h.Threaded = False

    def tap(h):
        h.Threaded = True
        h.ModelThread = False
        h.CosmeticThread = False

    def threaded(h):
        h.Threaded = True
        h.ModelThread = True
    hole_scene("hole_type", [(clearance, "Clearance M5: περνάει η βίδα (≈5,5 mm)"),
                             (tap, "Tap drill M5: τρυπάνι για κολαούζο (4,2 mm)"),
                             (threaded, "Threaded: σχεδιασμένο σπείρωμα")])


@scene("hole_cut")
def s_hole_cut():
    def none(h):
        h.HoleCutType = "None"

    def cbore(h):
        h.HoleCutType = "Counterbore"

    def csink(h):
        h.HoleCutType = "Countersink"
    hole_scene("hole_cut", [(none, "Χωρίς κεφαλή"), (cbore, "Counterbore: σκαλί για κεφαλή άλεν"),
                            (csink, "Countersink: κώνος για φρεζάτη βίδα")])


def block_with_edges(r, typ, **props):
    b = r.sketch(0, rect(-15, -10, 15, 10))
    pad = r.feature("Pad", b, Length=14)
    top = [i + 1 for i, e in enumerate(pad.Shape.Edges)
           if abs(e.BoundBox.ZMin - 14) < 1e-6 and abs(e.BoundBox.ZMax - 14) < 1e-6]
    f = r.body.newObject("PartDesign::" + typ, typ)
    f.Base = (pad, ["Edge%d" % i for i in top])
    for k, v in props.items():
        setattr(f, k, v)
    r.doc.recompute()
    return f


@scene("fillet_radius")
def s_fillet():
    r = Rec("fillet_radius")
    f = block_with_edges(r, "Fillet", Radius=1)
    r.look()
    r.view(1.0)
    for rad in (1, 3, 6):
        f.Radius = rad
        r.state("Radius %d mm" % rad, 1300 if rad < 6 else 2200)
    r.save()


@scene("chamfer_type")
def s_chamfer():
    r = Rec("chamfer_type")
    f = block_with_edges(r, "Chamfer", Size=4)
    r.look()
    r.view(0.9, "front")
    f.ChamferType = "Equal distance"
    f.Size = 5
    r.state("Equal distance: 5 και 5 mm")
    f.ChamferType = "Two distances"
    f.Size, f.Size2 = 8, 3
    r.state("Two distances: 8 και 3 mm")
    f.ChamferType = "Distance and Angle"
    f.Size, f.Angle = 6, 30
    r.state("Distance and angle: 6 mm, 30°", 2200)
    r.save()


@scene("thickness")
def s_thickness():
    r = Rec("thickness")
    sk = r.sketch(0, rect(-15, -10, 15, 10))
    pad = r.feature("Pad", sk, Length=16)
    top = [i + 1 for i, fc in enumerate(pad.Shape.Faces)
           if abs(fc.BoundBox.ZMin - 16) < 1e-6 and abs(fc.BoundBox.ZMax - 16) < 1e-6][0]
    t = r.body.newObject("PartDesign::Thickness", "Thickness")
    t.Base = (pad, ["Face%d" % top])
    t.Value = 2
    t.Reversed = False             # frame the outward (largest) state, then start inward
    r.doc.recompute()
    r.look()
    r.view(1.15)
    t.Reversed = True
    r.state("Πάχος 2 mm προς τα μέσα: η πάνω έδρα ανοίγει")
    t.Value = 4
    r.state("Πάχος 4 mm")
    t.Reversed = False
    t.Join = "Arc"
    r.state("Προς τα έξω, Join = Arc: στρογγυλές γωνίες")
    t.Join = "Intersection"
    r.state("Join = Intersection: κοφτερές γωνίες", 2200)
    r.save()


@scene("draft_angle")
def s_draft():
    r = Rec("draft_angle")
    sk = r.sketch(0, rect(-15, -10, 15, 10))
    pad = r.feature("Pad", sk, Length=16)
    sides = [i + 1 for i, fc in enumerate(pad.Shape.Faces)
             if fc.BoundBox.ZMax - fc.BoundBox.ZMin > 1]
    d = r.body.newObject("PartDesign::Draft", "Draft")
    d.Base = (pad, ["Face%d" % i for i in sides])
    d.NeutralPlane = (sk, [""])
    d.Angle = 0.1
    r.doc.recompute()
    r.look()
    r.view(1.1, "front")
    for a in (1, 8, 15):
        d.Angle = a
        r.state("Draft angle %d°" % a, 1300 if a < 15 else 2200)
    r.save()


@scene("helix")
def s_helix():
    r = Rec("helix")
    sk = r.sketch(1, circle(12, 0, 2))
    h = r.feature("AdditiveHelix", sk, Pitch=8, Height=24, Mode="pitch-height-angle")
    h.ReferenceAxis = (sk, ["V_Axis"])
    r.doc.recompute()
    r.look(see_sketch=sk)
    h.Height = 40
    r.doc.recompute()
    r.view(1.1, "front")
    h.Height = 24
    r.state("Pitch 8, Height 24: 3 στροφές")
    h.Pitch = 4
    r.state("Pitch 4: πιο πυκνά, 6 στροφές")
    h.Pitch, h.Height = 8, 40
    r.state("Height 40: ψηλότερη, 5 στροφές")
    h.Angle = 12
    r.state("Cone angle 12°: σαν κώνος", 2200)
    r.save()


def pattern_scene(name, typ, setup, states, zoom=1.0, orient="top"):
    r = Rec(name)
    r.base(Part.makeBox(90, 50, 6, V(-10, -25, 0)))
    sk = r.sketch(0, circle(0, 0, 4), z=6)
    hole = r.feature("Pocket", sk, Type="ThroughAll")
    p = r.body.newObject("PartDesign::" + typ, typ)
    p.Originals = [hole]
    setup(r, p, sk)
    r.doc.recompute()
    r.look()
    r.view(zoom, orient)
    for fn, text in states:
        fn(p)
        r.state(text)
    r.save()


@scene("linear_pattern")
def s_linear():
    def setup(r, p, sk):
        p.Direction = (sk, ["H_Axis"])
        p.Mode = "Extent"
        p.Length = 60
        p.Occurrences = 3

    def ext3(p):
        p.Mode, p.Length, p.Occurrences = "Extent", 60, 3

    def ext5(p):
        p.Occurrences = 5

    def spacing(p):
        p.Mode, p.Offset, p.Occurrences = "Spacing", 20, 3
    pattern_scene("linear_pattern", "LinearPattern", setup,
                  [(ext3, "Extent 60 mm, 3 τρύπες"), (ext5, "Extent 60 mm, 5 τρύπες: πιο πυκνά"),
                   (spacing, "Spacing 20 mm, 3 τρύπες")])


@scene("polar_pattern")
def s_polar():
    def setup(r, p, sk):
        p.Axis = (r.body.Origin.OriginFeatures[2], [""])     # Z axis

    def full(p):
        p.Mode, p.Angle, p.Occurrences = "Extent", 360, 6

    def half(p):
        p.Angle = 180

    def spacing(p):
        p.Mode, p.Offset, p.Occurrences = "Spacing", 30, 4

    def build():
        r = Rec("polar_pattern")
        r.base(Part.makeCylinder(30, 6))
        sk = r.sketch(0, circle(20, 0, 4), z=6)
        hole = r.feature("Pocket", sk, Type="ThroughAll")
        p = r.body.newObject("PartDesign::PolarPattern", "PolarPattern")
        p.Originals = [hole]
        setup(r, p, sk)
        full(p)
        r.doc.recompute()
        r.look()
        r.view(1.0, "top")
        r.state("Total angle 360°, 6 τρύπες")
        half(p)
        r.state("Total angle 180°: το 1ο στη 0°, το τελευταίο στις 180°")
        spacing(p)
        r.state("Angular spacing 30°, 4 τρύπες", 2200)
        r.save()
    build()


def run():
    log = open(os.path.join(OUT, "rec_log.txt"), "a")
    try:
        set_theme()
        Gui.activateWorkbench("PartDesignWorkbench")
        Gui.getMainWindow().resize(1098, 658)
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

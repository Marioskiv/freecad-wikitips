# SPDX-License-Identifier: LGPL-2.1-or-later
"""Record Part / PartDesign scenes inside a REAL FreeCAD (3D view), step 1 of 2.

    WT_OUT=<dir> [WT_ONLY=name,name] xvfb-run -a freecad tools/gifs/part_rec.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/part

Same events.json format as sketcher_rec.py, so sketcher_gifs.py composes the GIF
(cursor, click rings, real toolbar icon, numbered Greek steps). Run with a
throw-away HOME: it changes FreeCAD's view preferences.
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

try:
    from pivy import coin  # noqa: F401  (needed by View3DInventor.getCameraNode)
except ImportError:
    coin = None

OUT = os.environ.get("WT_OUT", "/tmp/part_rec")
ONLY = {x for x in os.environ.get("WT_ONLY", "").split(",") if x}
V = App.Vector
# Sharp 3x GIFs (2026-10-17): record with QT_SCALE_FACTOR=1.5 (FreeCAD then draws fonts, markers
# and lines like on a 150 % screen and the view is 1248 x 750 pixels). WT_REC_SCALE renders the key
# frames even bigger than the view; sketcher_gifs.py works out the scale from the pictures.
REC_SCALE = float(os.environ.get("WT_REC_SCALE", "1"))

BG = "#F4F6FA"
BASE = (0.58, 0.64, 0.74)      # main solid: slate blue
TOOLC = (0.96, 0.62, 0.04)     # the second object (tool): amber
RESULT = (0.39, 0.40, 0.95)    # what the command made: indigo


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
    pv.SetBool("Simple", True)          # plain background, no gradient
    pv.SetBool("Gradient", False)
    pv.SetBool("ShowNaviCube", False)
    pv.SetBool("CornerCoordSystem", False)


def color(obj, rgb, transparency=0):
    try:
        obj.ViewObject.ShapeColor = rgb
        obj.ViewObject.Transparency = transparency
        obj.ViewObject.LineColor = (0.12, 0.16, 0.23)
        obj.ViewObject.LineWidth = 2
    except Exception:
        pass


def sketch_on(body, plane_index, geo):
    """Sketch in `body` on its origin plane (0 XY, 1 XZ, 2 YZ) with the given geometry list."""
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = [(body.Origin.OriginFeatures[3 + plane_index], "")]
    sk.MapMode = "FlatFace"
    for g in geo:
        sk.addGeometry(g)
    return sk


def rect_geo(x0, y0, x1, y1):
    p = [V(x0, y0, 0), V(x1, y0, 0), V(x1, y1, 0), V(x0, y1, 0)]
    return [Part.LineSegment(p[i], p[(i + 1) % 4]) for i in range(4)]


def circle_geo(x, y, r):
    return [Part.Circle(V(x, y, 0), V(0, 0, 1), r)]


class Rec:
    def __init__(self, name, tool_first=False):
        self.name, self.tool_first = name, tool_first
        self.dir = os.path.join(OUT, name)
        os.makedirs(self.dir, exist_ok=True)
        self.doc = App.newDocument(name.replace(" ", "_"))
        self.events, self.n = [], 0
        self.icon = None
        try:
            act = Gui.Command.get(name).getAction()[0]
            if not act.icon().pixmap(64, 64).save(os.path.join(self.dir, "icon.png")):
                raise ValueError("no icon")
            self.icon = "icon.png"
        except Exception:
            # commands inside a dropdown group have no own action: use their icon resource
            try:
                from PySide import QtGui
                cmd = Gui.Command.get(name)
                pix = cmd.getInfo()["pixmap"] if cmd is not None else name   # e.g. sub-items of a group
                icons = [QtGui.QIcon(p) for p in (":/icons/%s.svg" % pix, ":/icons/%s.png" % pix, pix)]
                icons.append(Gui.getIcon(pix))        # BitmapFactory: finds the workbench icons too
                for ic in icons:
                    if ic is not None and not ic.isNull() and ic.pixmap(64, 64).save(os.path.join(self.dir, "icon.png")):
                        self.icon = "icon.png"
                        break
            except Exception:
                pass

    def view(self, zoom=1.0):
        self.doc.recompute()
        pump(300)
        self.v = Gui.ActiveDocument.ActiveView
        self.v.setCameraType("Orthographic")
        self.v.viewIsometric()
        self.v.fitAll()
        cam = self.v.getCameraNode()
        cam.height.setValue(cam.height.getValue() * zoom)
        pump(300)
        self.W, self.H = self.v.getSize()
        self.img()
        if self.tool_first:
            self.cap(1, "Πάτα το κουμπί")
            self.press()

    def px(self, p):
        u, w = self.v.getPointOnViewport(V(*p))
        return [int(u), int(self.H - w)]

    def shot(self):
        self.doc.recompute()
        pump(200)
        f = "k%03d.png" % self.n
        self.n += 1
        self.v.saveImage(os.path.join(self.dir, f), int(round(self.W * REC_SCALE)), int(round(self.H * REC_SCALE)), BG)
        return f

    def img(self, blend=False):
        self.events.append({"t": "img", "f": self.shot(), "blend": blend})

    def cap(self, n, text):
        self.events.append({"t": "cap", "n": n, "text": text})

    def press(self):
        self.events.append({"t": "press"})

    def move(self, p, ms=500):
        self.events.append({"t": "move", "to": self.px(p), "ms": ms})

    def click(self, p, obj=None, sub=""):
        self.move(p)
        self.events.append({"t": "click"})
        if obj is not None:
            Gui.Selection.addSelection(self.doc.Name, obj.Name, sub)
            self.img()

    def hold(self, ms):
        self.events.append({"t": "hold", "ms": ms})

    def apply(self, fn, n, text, ms=1800):
        Gui.Selection.clearSelection()
        fn()
        self.doc.recompute()
        self.cap(n, text)
        self.img(blend=True)
        self.hold(ms)

    def save(self):
        meta = {"name": self.name, "size": [self.W, self.H], "scale": REC_SCALE, "icon": self.icon, "events": self.events}
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


def hide(*objs):
    for o in objs:
        o.ViewObject.Visibility = False


# ---------------------------------------------------------------------------
# Part booleans: select first (Ctrl+click for the second), then the button
# ---------------------------------------------------------------------------
def two_solids(r, kind):
    d = r.doc
    a = d.addObject("Part::Box", "Box")
    a.Length, a.Width, a.Height = 40, 30, 14
    if kind == "cyl":
        b = d.addObject("Part::Cylinder", "Cylinder")
        b.Radius, b.Height = 8, 26
        b.Placement.Base = V(20, 15, -6)
    elif kind == "sphere":
        b = d.addObject("Part::Sphere", "Sphere")
        b.Radius = 17
        b.Placement.Base = V(32, 22, 12)
    else:
        b = d.addObject("Part::Box", "Box2")
        b.Length, b.Width, b.Height = 18, 18, 22
        b.Placement.Base = V(28, 18, 0)
    color(a, BASE)
    color(b, TOOLC)
    return a, b


def boolean_scene(name, kind, typ, cap1, cap2, result_cap, top_b):
    r = Rec(name)
    a, b = two_solids(r, kind)
    r.view(1.1)
    r.cap(1, cap1)
    r.click((8, 0, 14), a)
    r.cap(2, cap2)
    r.click(top_b, b)
    r.cap(3, "Πάτα το κουμπί")
    r.press()

    def go():
        o = r.doc.addObject(typ, "Result")
        if typ == "Part::MultiFuse" or typ == "Part::MultiCommon":
            o.Shapes = [a, b]
        else:
            o.Base, o.Tool = a, b
        r.doc.recompute()
        hide(a, b)
        color(o, BASE)
    r.apply(go, 4, result_cap)
    r.save()


@scene("Part_Cut")
def s_cut():
    boolean_scene("Part_Cut", "cyl", "Part::Cut", "Κλικ σε αυτό που ΚΡΑΤΑΣ",
                  "Ctrl+κλικ σε αυτό που ΑΦΑΙΡΕΙΣ", "Τρύπα: το 2ο αφαιρέθηκε από το 1ο", (20, 23, 20))


@scene("Part_Fuse")
def s_fuse():
    boolean_scene("Part_Fuse", "box", "Part::MultiFuse", "Κλικ στο πρώτο",
                  "Ctrl+κλικ στο δεύτερο", "Ένα ενιαίο στερεό", (37, 27, 22))


@scene("Part_Common")
def s_common():
    boolean_scene("Part_Common", "sphere", "Part::MultiCommon", "Κλικ στο πρώτο",
                  "Ctrl+κλικ στο δεύτερο", "Μένει μόνο το κοινό κομμάτι", (32, 22, 29))


@scene("Part_Section")
def s_section():
    r = Rec("Part_Section")
    a, b = two_solids(r, "cyl")
    r.view(1.1)
    r.cap(1, "Κλικ στο πρώτο")
    r.click((8, 0, 14), a)
    r.cap(2, "Ctrl+κλικ στο δεύτερο")
    r.click((20, 23, 20), b)
    r.cap(3, "Πάτα το κουμπί")
    r.press()

    def go():
        o = r.doc.addObject("Part::Section", "Section")
        o.Base, o.Tool = a, b
        r.doc.recompute()
        hide(a, b)
        o.ViewObject.LineColor = (0.88, 0.11, 0.28)
        o.ViewObject.LineWidth = 4
    r.apply(go, 4, "Μόνο οι γραμμές όπου τέμνονται")
    r.save()


# ---------------------------------------------------------------------------
# PartDesign
# ---------------------------------------------------------------------------
def plate_body(doc, with_hole=None, name="Body"):
    body = doc.addObject("PartDesign::Body", name)
    sk = sketch_on(body, 0, rect_geo(-30, -20, 30, 20))   # centred on the origin
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile, pad.Length = sk, 8
    sk.Visibility = False
    feat = pad
    if with_hole:
        hs = sketch_on(body, 0, circle_geo(*with_hole))
        hs.AttachmentOffset = App.Placement(V(0, 0, 8), App.Rotation())
        feat = body.newObject("PartDesign::Pocket", "Pocket")
        feat.Profile, feat.Length = hs, 20
        hs.Visibility = False
    doc.recompute()
    color(body, BASE)
    return body, feat


@scene("PartDesign_Mirrored")
def s_mirrored():
    r = Rec("PartDesign_Mirrored")
    body, pocket = plate_body(r.doc, with_hole=(-18, 0, 6))
    r.view(1.0)
    r.cap(1, "Κλικ στην τρύπα")
    r.click((-18, 6, 4), pocket, hole_face(pocket, -18, 0))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        m = body.newObject("PartDesign::Mirrored", "Mirrored")
        m.Originals = [pocket]
        m.MirrorPlane = (sketch_of(pocket), ["V_Axis"])
        r.doc.recompute()
        color(body, BASE)
    r.apply(go, 3, "Καθρέφτισμα στην άλλη μεριά")
    r.save()


def face_where(obj, test):
    """Name of the first face of obj's shape that passes test(face)."""
    for i, f in enumerate(obj.Shape.Faces):
        if test(f):
            return "Face%d" % (i + 1)
    return ""


def top_face(obj):
    zmax = obj.Shape.BoundBox.ZMax
    return face_where(obj, lambda f: abs(f.BoundBox.ZMin - zmax) < 1e-6 and abs(f.BoundBox.ZMax - zmax) < 1e-6)


def hole_face(obj, x, y):
    return face_where(obj, lambda f: f.Surface.__class__.__name__ == "Cylinder"
                      and abs(f.Surface.Center.x - x) < 0.5 and abs(f.Surface.Center.y - y) < 0.5)


def sketch_of(feat):
    return feat.Profile[0] if isinstance(feat.Profile, tuple) else feat.Profile


@scene("PartDesign_PolarPattern")
def s_polar():
    r = Rec("PartDesign_PolarPattern")
    body = r.doc.addObject("PartDesign::Body", "Body")
    sk = sketch_on(body, 0, circle_geo(0, 0, 30))
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile, pad.Length = sk, 8
    sk.Visibility = False
    hs = sketch_on(body, 0, circle_geo(20, 0, 4))
    hs.AttachmentOffset = App.Placement(V(0, 0, 8), App.Rotation())
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile, pocket.Length = hs, 20
    hs.Visibility = False
    r.doc.recompute()
    color(body, BASE)
    r.view(1.0)
    r.cap(1, "Κλικ στην τρύπα")
    r.click((20, 4, 4), pocket, hole_face(pocket, 20, 0))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        p = body.newObject("PartDesign::PolarPattern", "PolarPattern")
        p.Originals = [pocket]
        p.Axis = (hs, ["N_Axis"])
        p.Angle, p.Occurrences = 360, 6
        r.doc.recompute()
        color(body, BASE)
    r.apply(go, 3, "6 τρύπες γύρω από τον άξονα")
    r.save()


@scene("PartDesign_LinearPattern")
def s_linear():
    r = Rec("PartDesign_LinearPattern")
    body, pocket = plate_body(r.doc, with_hole=(-20, 0, 4))
    r.view(1.0)
    r.cap(1, "Κλικ στην τρύπα")
    r.click((-20, 4, 4), pocket, hole_face(pocket, -20, 0))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        p = body.newObject("PartDesign::LinearPattern", "LinearPattern")
        p.Originals = [pocket]
        p.Direction = (sketch_of(pocket), ["H_Axis"])
        p.Length, p.Occurrences = 40, 4
        r.doc.recompute()
        color(body, BASE)
    r.apply(go, 3, "4 τρύπες σε σειρά (σύνολο 40 mm)")
    r.save()


@scene("PartDesign_Boolean")
def s_pd_boolean():
    r = Rec("PartDesign_Boolean", tool_first=True)
    body, _ = plate_body(r.doc)
    tool = r.doc.addObject("PartDesign::Body", "Body001")
    sk = sketch_on(tool, 0, circle_geo(0, 0, 9))
    cyl = tool.newObject("PartDesign::Pad", "Pad001")
    cyl.Profile, cyl.Length = sk, 20
    sk.Visibility = False
    tool.Placement.Base = V(0, 0, -6)
    r.doc.recompute()
    color(tool, TOOLC)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    r.view(1.0)
    r.cap(2, "Add body → κλικ στο άλλο σώμα")
    r.click((0, 9, 14), tool)
    r.cap(3, "Τύπος: Cut → OK")
    r.hold(700)

    def go():
        b = body.newObject("PartDesign::Boolean", "Boolean")
        b.Type = "Cut"
        b.addObject(tool)
        r.doc.recompute()
        hide(tool)
        color(body, BASE)
    r.apply(go, 4, "Το άλλο σώμα αφαιρέθηκε")
    r.save()


@scene("PartDesign_Plane")
def s_plane():
    r = Rec("PartDesign_Plane", tool_first=True)
    body, pad = plate_body(r.doc)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    r.view(1.15)
    r.cap(2, "Κλικ στην πάνω έδρα")
    r.click((0, 0, 8), pad, top_face(pad))
    r.cap(3, "Attachment offset Z = 15 → OK")
    r.hold(700)

    def go():
        p = body.newObject("PartDesign::Plane", "DatumPlane")
        p.AttachmentSupport = [(pad, top_face(pad))]
        p.MapMode = "FlatFace"
        p.AttachmentOffset = App.Placement(V(0, 0, 15), App.Rotation())
        r.doc.recompute()
    r.apply(go, 4, "Βοηθητικό επίπεδο 15 mm πιο πάνω")
    r.save()


@scene("PartDesign_SubShapeBinder")
def s_binder():
    r = Rec("PartDesign_SubShapeBinder")
    a, _ = plate_body(r.doc, name="Body")
    b = r.doc.addObject("PartDesign::Body", "Body001")
    color(a, BASE, 0)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", b)
    r.view(1.15)
    r.cap(1, "Ενεργό το ΑΛΛΟ σώμα · κλικ σε έδρα")
    pad = r.doc.getObject("Pad")
    r.click((0, 0, 8), pad, top_face(pad))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        s = b.newObject("PartDesign::SubShapeBinder", "Binder")
        s.Support = [(pad, (top_face(pad),))]
        r.doc.recompute()
        s.Placement.Base = V(0, 0, 18)
        r.doc.recompute()
        color(s, RESULT)
    r.apply(go, 3, "Αντίγραφο-σύνδεσμος της έδρας στο άλλο σώμα")
    r.save()


@scene("PartDesign_Clone")
def s_clone():
    r = Rec("PartDesign_Clone")
    body, _ = plate_body(r.doc, with_hole=(0, 0, 8))
    r.view(1.6)
    r.cap(1, "Κλικ στο σώμα")
    r.click((-25, -20, 8), body)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():   # shown as a copy beside the original (what the user sees after moving it)
        c = r.doc.addObject("Part::Feature", "Clone")
        c.Shape = body.Shape.copy()
        c.Placement.Base = V(70, 0, 0)
        color(c, RESULT)
    r.apply(go, 3, "Αντίγραφο που ακολουθεί τις αλλαγές")
    r.save()


def run():
    log = open(os.path.join(OUT, "rec_log.txt"), "w")
    try:
        set_theme()
        Gui.activateWorkbench("PartWorkbench")         # loads the Part_* commands (icons)
        pump(300)
        Gui.activateWorkbench("PartDesignWorkbench")
        mw = Gui.getMainWindow()
        mw.resize(1098, 658)
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
if not os.environ.get("WT_NO_AUTORUN"):     # part_more.py imports this module and adds scenes
    QtCore.QTimer.singleShot(3500, run)

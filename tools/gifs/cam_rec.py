# SPDX-License-Identifier: LGPL-2.1-or-later
"""Record CAM toolbar commands inside a REAL FreeCAD (3D view), step 1 of 2.

    WT_OUT=<dir> WT_ONLY=CAM_Pocket_Shape xvfb-run -a freecad tools/gifs/cam_rec.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/camcmd

One scene per FreeCAD start (WT_ONLY): opening many CAM objects/dialogs in one
session is what crashes FreeCAD 26.3 (docs/notes/memory.md). tools/gifs/cam_rec.sh
loops over all scenes. Same events.json format as part_rec.py, plus "panel"
events (a card with real G-code / report lines drawn by the composer).
The operations are made with FreeCAD's own CAM Python API, so the toolpaths
are the real ones FreeCAD 26.3 computes.
"""
import json
import math
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtWidgets

try:
    from pivy import coin  # noqa: F401  (needed by View3DInventor.getCameraNode)
except ImportError:
    coin = None

OUT = os.environ.get("WT_OUT", "/tmp/cam_rec")
ONLY = {x for x in os.environ.get("WT_ONLY", "").split(",") if x}
V = App.Vector

BG = "#F4F6FA"
MODEL = (0.62, 0.68, 0.77)     # part: light slate
TOOLC = (0.20, 0.25, 0.33)     # cutter: graphite
PATHC = (0.31, 0.27, 0.90)     # toolpath: indigo
NEWC = (0.88, 0.11, 0.28)      # what the command changed: rose
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


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


def color(obj, rgb, transparency=0, lw=2):
    try:
        obj.ViewObject.ShapeColor = rgb
        obj.ViewObject.Transparency = transparency
        obj.ViewObject.LineColor = (0.12, 0.16, 0.23)
        obj.ViewObject.LineWidth = lw
    except Exception:
        pass


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------
def stadium(x0, x1, y, r, z0, h):
    s = Part.makeBox(x1 - x0, 2 * r, h, V(x0, y - r, z0))
    s = s.fuse(Part.makeCylinder(r, h, V(x0, y, z0))).fuse(Part.makeCylinder(r, h, V(x1, y, z0)))
    return s.removeSplitter()


def plate():
    """100x70x15 plate: square pocket (6 deep), a big hole, two small holes, a slot."""
    s = Part.makeBox(100, 70, 15)
    s = s.cut(Part.makeBox(34, 24, 6, V(10, 10, 9)))
    s = s.cut(Part.makeCylinder(8, 15, V(78, 46, 0)))
    s = s.cut(Part.makeCylinder(3, 15, V(62, 16, 0)))
    s = s.cut(Part.makeCylinder(3, 15, V(88, 16, 0)))
    s = s.cut(stadium(16, 40, 52, 4, 11, 4))
    return s.removeSplitter()


def bowl():
    s = Part.makeBox(80, 60, 20)
    s = s.cut(Part.makeSphere(26, V(40, 30, 38)))
    return s


def text_plate(doc, text="CNC"):
    import Draft
    s = Part.makeBox(90, 40, 10)
    ss = Draft.make_shapestring(String=text, FontFile=FONT, Size=22)
    ss.Placement.Base = V(10, 9, 10)
    doc.recompute()
    return s, ss


class Rec:
    def __init__(self, name, shape=None, tool=None):
        self.name = name
        self.dir = os.path.join(OUT, name)
        os.makedirs(self.dir, exist_ok=True)
        self.doc = App.newDocument(name.replace(" ", "_"))
        self.events, self.n = [], 0
        self.icon = None
        try:
            act = Gui.Command.get(name).getAction()[0]
            act.icon().pixmap(64, 64).save(os.path.join(self.dir, "icon.png"))
            self.icon = "icon.png"
        except Exception:
            pass
        self.part = self.doc.addObject("Part::Feature", "Part")
        self.part.Shape = shape if shape is not None else plate()
        self.doc.recompute()
        self.job = None
        self.cutter = None
        self.tooldia = 5.0

    # --- CAM objects ---------------------------------------------------------
    def make_job(self, extra=()):
        from Path.Main import Job as PathJob
        from Path.Main.Gui import Job as PathJobGui
        self.job = PathJob.Create("Job", [self.part] + list(extra), None)
        self.job.ViewObject.Proxy = PathJobGui.ViewProvider(self.job.ViewObject)
        self.doc.recompute()
        self.model = self.job.Model.Group[0]
        for m in self.job.Model.Group:
            color(m, MODEL)
            m.ViewObject.Visibility = True
        self.hide_tool_bodies()
        self.part.ViewObject.Visibility = False
        self.job.Stock.ViewObject.Visibility = False
        return self.job

    def hide_tool_bodies(self):
        """Tool bits bring a small PartDesign body (their shape): keep it out of the picture."""
        for o in self.doc.Objects:
            if o.TypeId.startswith(("PartDesign::", "Sketcher::", "App::Point")) and o.ViewObject:
                o.ViewObject.Visibility = False

    def tc(self, fctb, number=2):
        """Add a tool controller with one of FreeCAD's own sample tool bits."""
        from Path.Tool import Controller
        from Path.Tool.toolbit import ToolBit
        path = os.path.join(App.getHomePath(), "Mod", "CAM", "Tools", "Bit", fctb)
        tb = ToolBit.from_file(path)
        tool = tb.attach_to_doc(doc=self.doc)
        tool.ViewObject.Visibility = False
        c = Controller.Create("TC: " + tool.Label, tool=tool, toolNumber=number)
        self.job.Proxy.addToolController(c)
        self.hide_tool_bodies()
        return c

    def face(self, pred, obj=None):
        obj = obj or self.model
        for i, f in enumerate(obj.Shape.Faces):
            if pred(f):
                return "Face%d" % (i + 1)
        raise RuntimeError("face not found")

    def edge(self, pred, obj=None):
        obj = obj or self.model
        for i, e in enumerate(obj.Shape.Edges):
            if pred(e):
                return "Edge%d" % (i + 1)
        raise RuntimeError("edge not found")

    def op(self, module, base=None, **props):
        import importlib
        m = importlib.import_module("Path.Op." + module)
        o = m.Create(module)
        if base:
            o.Base = base
        for k, v in props.items():
            setattr(o, k, v)
        self.doc.recompute()
        self.attach_vp(o, module)
        self.style_path(o)
        return o

    def attach_vp(self, o, module):
        """The view provider the GUI command would attach (draws the path, icon in the tree)."""
        import importlib
        import Path.Op.Gui.Base as OpGui
        try:
            gm = importlib.import_module("Path.Op.Gui." + module)
            res = getattr(gm.Command, "res", None)
            o.ViewObject.Proxy = OpGui.ViewProvider(o.ViewObject, res)
            o.ViewObject.Visibility = True
        except Exception:
            traceback.print_exc()

    def style_path(self, o, rgb=PATHC):
        try:
            o.ViewObject.NormalColor = rgb
            o.ViewObject.LineWidth = 3
            o.ViewObject.ShowNodes = False
        except Exception:
            pass

    # --- view ---------------------------------------------------------------
    def view(self, zoom=1.0, top=False, press_first=False, cap="Πάτα το κουμπί", focus=None):
        self.doc.recompute()
        Gui.Selection.clearSelection()
        pump(300)
        self.v = Gui.ActiveDocument.ActiveView
        self.v.setCameraType("Orthographic")
        if top:
            self.v.viewTop()
        else:
            self.v.viewIsometric()
        self.v.fitAll()
        cam = self.v.getCameraNode()
        cam.height.setValue(cam.height.getValue() * zoom * 0.68)
        if focus is not None:      # slide the camera so `focus` is in the middle of the picture
            u, w = self.v.getPointOnViewport(V(*focus))
            W0, H0 = self.v.getSize()
            a = self.v.getPointOnFocalPlane(int(u), int(w))
            b = self.v.getPointOnFocalPlane(int(W0 / 2), int(H0 / 2))
            p = cam.position.getValue()
            d = a - b
            cam.position.setValue(p[0] + d.x, p[1] + d.y, p[2] + d.z)
        pump(300)
        self.W, self.H = self.v.getSize()
        if os.environ.get("WT_DEBUG"):
            with open(os.path.join(self.dir, "debug.txt"), "w") as f:
                for o in self.doc.Objects:
                    f.write("%s %s vis=%s\n" % (o.Name, o.TypeId, getattr(o.ViewObject, "Visibility", None)))
                f.write("size %s %s active=%s\n" % (self.W, self.H, Gui.ActiveDocument.Document.Name))
        self.img()
        if press_first:
            self.cap(1, cap)
            self.press()

    def px(self, p):
        u, w = self.v.getPointOnViewport(V(*p))
        return [int(u), int(self.H - w)]

    def shot(self):
        self.doc.recompute()
        pump(150)
        f = "k%03d.png" % self.n
        self.n += 1
        self.v.saveImage(os.path.join(self.dir, f), self.W, self.H, BG)
        return f

    def img(self, blend=False):
        self.events.append({"t": "img", "f": self.shot(), "blend": blend})

    def cap(self, n, text):
        self.events.append({"t": "cap", "n": n, "text": text})

    def press(self):
        self.events.append({"t": "press"})

    def move(self, p, ms=500):
        self.events.append({"t": "move", "to": self.px(p), "ms": ms})

    def click(self, p, obj=None, sub="", add=False):
        self.move(p)
        self.events.append({"t": "click"})
        if obj is not None:
            if not add:
                Gui.Selection.clearSelection()
            Gui.Selection.addSelection(self.doc.Name, obj.Name, sub)
            self.img()

    def see_through(self, t=45):
        """Part half transparent so the path inside pockets/holes can be seen."""
        for m in self.job.Model.Group:
            m.ViewObject.Transparency = t

    def hold(self, ms):
        self.events.append({"t": "hold", "ms": ms})

    def panel(self, title, lines, mono=True, pos="right"):
        self.events.append({"t": "panel", "title": title, "lines": lines, "mono": mono, "pos": pos})

    def tree_pick(self, ops=(), row=0, caption=None, n=1):
        """Small model tree (like FreeCAD's) and a click on one of its rows."""
        lines = ["Job"] + ["   " + o for o in ops] if ops else ["Job", "   Operations", "   Model", "   Tools"]
        self.panel("Μοντέλο (δέντρο)", lines, mono=False, pos="left")
        if caption:
            self.cap(n, caption)
        self.events.append({"t": "pick", "row": row})

    def panel_off(self):
        self.events.append({"t": "panel", "title": None})

    def apply(self, fn, n, text, ms=1500):
        Gui.Selection.clearSelection()
        res = fn()
        self.doc.recompute()
        self.cap(n, text)
        self.img(blend=True)
        self.hold(ms)
        return res

    # --- tool animation -----------------------------------------------------
    def points(self, o, step=2.0):
        """(point, command index) samples along the real toolpath."""
        import Path.Geom as PathGeom
        pts, cur = [], V(0, 0, 0)
        first = True
        for i, c in enumerate(o.Path.Commands):
            if c.Name not in ("G0", "G00", "G1", "G01", "G2", "G02", "G3", "G03"):
                continue
            p = c.Parameters
            end = V(p.get("X", cur.x), p.get("Y", cur.y), p.get("Z", cur.z))
            if first:
                cur, first = end, False
                continue
            try:
                e = PathGeom.edgeForCmd(c, cur)
            except Exception:
                e = None
            if e is not None and e.Length > 1e-6:
                n = max(1, int(e.Length / step))
                for k in range(1, n + 1):
                    pts.append((e.valueAt(e.FirstParameter + (e.LastParameter - e.FirstParameter) * k / n), i))
            cur = end
        return pts

    def run(self, o, frames=28, ms=90, show_path=True, tool=True, dia=None, length=22):
        """Animate the cutter along the real path; the path grows behind it."""
        pts = self.points(o)
        if not pts:
            return
        dia = dia or self.tool_dia(o)
        if tool and self.cutter is None:
            self.cutter = self.doc.addObject("Part::Feature", "Cutter")
            self.cutter.Shape = Part.makeCylinder(dia / 2, length)
            color(self.cutter, TOOLC, 0, 1)
        self.events.append({"t": "move", "to": [int(self.W * 0.93), int(self.H * 0.12)], "ms": 300})
        n = len(pts)
        for k in range(1, frames + 1):
            p, idx = pts[min(n - 1, int(round(k * (n - 1) / frames)))]
            if tool:
                self.cutter.Placement.Base = p
            if show_path:
                try:
                    o.ViewObject.StartIndex = 0
                    o.ViewObject.ShowCount = max(1, idx + 1)
                except Exception:
                    pass
            self.img()
            self.hold(ms)
        try:
            o.ViewObject.ShowCount = 0
        except Exception:
            pass
        if tool:
            self.cutter.ViewObject.Visibility = False
        self.img()

    def tool_dia(self, o):
        try:
            return float(o.ToolController.Tool.Diameter)
        except Exception:
            return 5.0

    def gcode(self, o, n=9):
        out = []
        for c in o.Path.Commands:
            if c.Name.startswith("("):
                continue
            s = c.Name
            for k in ("X", "Y", "Z", "I", "J", "K", "F", "Q", "R", "P"):
                if k in c.Parameters:
                    s += " %s%s" % (k, ("%.2f" % c.Parameters[k]).rstrip("0").rstrip("."))
            out.append(s)
            if len(out) >= n:
                break
        return out

    def save(self):
        if os.environ.get("WT_DEBUG"):
            with open(os.path.join(self.dir, "debug2.txt"), "w") as f:
                for o in self.doc.Objects:
                    f.write("%s %s vis=%s cmds=%s\n" % (o.Name, o.TypeId, getattr(o.ViewObject, "Visibility", None),
                            len(o.Path.Commands) if hasattr(o, "Path") else "-"))
        meta = {"name": self.name, "size": [self.W, self.H], "icon": self.icon, "events": self.events}
        with open(os.path.join(self.dir, "events.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)


SCENES = {}


def scene(name):
    def deco(fn):
        SCENES[name] = fn
        return fn
    return deco


def flat_at(z):
    return lambda f: f.Surface.__class__.__name__ == "Plane" and abs(f.BoundBox.ZMin - z) < 1e-6 \
        and abs(f.BoundBox.ZMax - z) < 1e-6


def top_face_pred(f):
    return flat_at(15)(f) and f.Area > 3000


def cyl_r(r):
    return lambda f: f.Surface.__class__.__name__ == "Cylinder" and abs(f.Surface.Radius - r) < 1e-6


# ---------------------------------------------------------------------------
# Project setup
# ---------------------------------------------------------------------------
@scene("CAM_Job")
def s_job():
    r = Rec("CAM_Job")
    color(r.part, MODEL)
    r.view(1.25)
    r.cap(1, "Κλικ στο κομμάτι")
    r.click((50, 35, 15), r.part)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        r.make_job()
        r.job.Stock.ViewObject.Visibility = True
        color(r.job.Stock, (0.96, 0.62, 0.04), 75, 2)
    r.apply(go, 3, "Job: κομμάτι + ακατέργαστο + εργαλείο", 2600)
    r.save()


def pocket_job(r):
    r.make_job()
    return r.op("PocketShape", [(r.model, (r.face(flat_at(9)),))])


@scene("CAM_Sanity")
def s_sanity():
    r = Rec("CAM_Sanity")
    pocket_job(r)
    r.view(1.25)
    r.tree_pick(caption="Κλικ στο Job (στο δέντρο)")
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.panel_off()
    tc = r.job.Tools.Group[0]
    sb = r.job.Stock.Shape.BoundBox
    r.cap(3, "Αναφορά για τον χειριστή")
    r.panel("Αναφορά ελέγχου (HTML)", [
        "Κομμάτι: %s" % r.part.Label,
        "Ακατέργαστο: %.0f × %.0f × %.0f mm" % (sb.XLength, sb.YLength, sb.ZLength),
        "Εργαλείο T%d: Ø%.0f mm" % (tc.ToolNumber, float(tc.Tool.Diameter)),
        "Εργασίες: %d" % len(r.job.Operations.Group),
        "⚠ Προειδοποιήσεις (Squawks)",
    ], mono=False)
    r.hold(3000)
    r.save()


def post_lines(r, n=9):
    """Real linuxcnc post output (Marios uses linuxcnc). Filename "-" = nothing written."""
    from Path.Post.scripts import linuxcnc_legacy_post as post
    text = post.export(r.job.Operations.Group, "-", "--no-show-editor --no-header --no-comments")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("(")]
    return lines[:n]


@scene("CAM_Post")
def s_post():
    r = Rec("CAM_Post")
    pocket_job(r)
    r.view(1.25)
    r.tree_pick(caption="Κλικ στο Job (στο δέντρο)")
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.panel_off()
    lines = post_lines(r)
    r.cap(3, "Αρχείο G-code για τη μηχανή")
    r.panel("job.ngc  ·  linuxcnc", lines)
    r.hold(3200)
    r.save()


# ---------------------------------------------------------------------------
# Tool commands
# ---------------------------------------------------------------------------
@scene("CAM_Inspect")
def s_inspect():
    r = Rec("CAM_Inspect")
    o = pocket_job(r)
    r.view(1.25)
    r.cap(1, "Κλικ σε μια εργασία")
    r.click((27, 22, 9), o)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.cap(3, "Οι εντολές της διαδρομής")
    r.panel("Inspect · " + o.Label, r.gcode(o))
    r.hold(3200)
    r.save()


@scene("CAM_SelectLoop")
def s_selectloop():
    r = Rec("CAM_SelectLoop")
    r.make_job()
    r.view(1.25)
    e = r.edge(lambda e: abs(e.BoundBox.ZMin - 15) < 1e-6 and abs(e.BoundBox.ZMax - 15) < 1e-6
               and abs(e.BoundBox.YMin - 10) < 1e-6 and e.BoundBox.XMin > 9 and e.BoundBox.XMax < 45)
    r.cap(1, "Κλικ σε ΜΙΑ ακμή")
    r.click((27, 10, 15), r.model, e)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    Gui.runCommand("CAM_SelectLoop")
    pump(300)
    r.cap(3, "Επιλέγεται όλος ο βρόχος")
    r.img(blend=True)
    r.hold(2400)
    r.save()


@scene("CAM_OpActiveToggle")
def s_toggle():
    r = Rec("CAM_OpActiveToggle")
    o = pocket_job(r)
    r.view(1.25)
    r.cap(1, "Κλικ σε μια εργασία")
    r.click((27, 22, 9), o)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        o.Active = False
    r.apply(go, 3, "Ανενεργή: δεν βγαίνει στο G-code", 2000)
    r.save()


@scene("CAM_SimulatorGL")
def s_sim():
    simulate(Rec("CAM_SimulatorGL"))


@scene("CAM_Simulator")
def s_sim_legacy():
    simulate(Rec("CAM_Simulator"))


def simulate(r):
    """Material removal shown with real booleans along the real path."""
    o = pocket_job(r)
    o.ViewObject.Visibility = False
    stock = r.doc.addObject("Part::Feature", "SimStock")
    sb = r.job.Stock.Shape
    stock.Shape = sb.copy()
    color(stock, (0.84, 0.87, 0.91))
    r.model.ViewObject.Visibility = False
    r.view(1.25, press_first=True)
    r.cap(2, "Το εργαλείο αφαιρεί υλικό")
    pts = [p for p, _ in r.points(o, step=2.0) if p.z < r.job.Stock.Shape.BoundBox.ZMax]
    rad = r.tool_dia(o) / 2
    cutter = r.doc.addObject("Part::Feature", "Cutter")
    cutter.Shape = Part.makeCylinder(rad, 22)
    color(cutter, TOOLC, 0, 1)
    cur = sb.copy()
    frames = 24
    last = 0
    r.events.append({"t": "move", "to": [int(r.W * 0.93), int(r.H * 0.12)], "ms": 300})
    for k in range(1, frames + 1):
        upto = int(round(k * (len(pts) - 1) / frames))
        tools = [Part.makeCylinder(rad, 30, p) for p in pts[last:upto + 1]]
        last = upto + 1
        if tools:                  # cut only what this frame removes: fast, incremental
            cur = cur.cut(tools)
            stock.Shape = cur
        cutter.Placement.Base = pts[upto]
        r.img()
        r.hold(110)
    cutter.ViewObject.Visibility = False
    r.cap(3, "Έλεγχος πριν κόψει η μηχανή")
    r.img()
    r.hold(2000)
    r.save()


@scene("CAM_ToolBitDock")
def s_tooldock():
    r = Rec("CAM_ToolBitDock")
    r.make_job()
    r.view(1.25, press_first=True)
    r.cap(2, "Διπλό κλικ σε εργαλείο")
    r.panel("Εργαλεία (βιβλιοθήκη)", ["5mm Endmill", "6mm Ball End", "60° V-Bit", "5mm Drill",
                                     "45° Chamfer"], mono=False)
    r.events.append({"t": "move", "to": [int(r.W * 0.80), int(r.H * 0.36)], "ms": 600})
    r.events.append({"t": "click"})
    r.events.append({"t": "click"})
    r.cap(3, "Νέος Tool Controller στο Job")
    r.panel("Job · Tools", ["TC: 5mm Endmill  (T1)", "TC: 6mm Ball End  (T2)"], mono=False)
    r.hold(2600)
    r.save()


# ---------------------------------------------------------------------------
# Operations: select geometry, press the button, the cutter runs the real path
# ---------------------------------------------------------------------------
def op_scene(name, module, pick, clicks, text, zoom=1.25, props=None, tc=None, shape=None,
             extra=None, frames=28, top=False, after=None, press_first=False, show_stock=False,
             focus=None):
    r = Rec(name, shape=shape)
    ext = extra(r) if extra else ()
    r.make_job(ext)
    if tc:
        c = r.tc(tc)
    r.view(zoom, top=top, focus=focus)
    base = pick(r)
    if press_first:            # this command ignores a selection made before it
        r.cap(1, "Πάτα το κουμπί")
        r.press()
    if clicks:
        r.cap(2 if press_first else 1, clicks)
        for i, (p, sub) in enumerate(base["clicks"]):
            r.click(p, base.get("obj", r.model), sub, add=i > 0)
    if not press_first:
        r.cap(2, "Πάτα το κουμπί")
        r.press()
    Gui.Selection.clearSelection()
    if show_stock:
        r.job.Stock.ViewObject.Visibility = True
        color(r.job.Stock, (0.96, 0.62, 0.04), 80, 1)
    props = dict(props or {})
    if tc:
        props["ToolController"] = c
    o = r.op(module, base["base"], **props)
    if after:
        after(r, o)
    r.see_through()
    o.ViewObject.ShowCount = 1
    r.cap(3, text)
    r.img(blend=True)
    r.run(o, frames=frames)
    r.hold(1600)
    r.save()
    return r, o


@scene("CAM_Profile")
def s_profile():
    def pick(r):
        f = r.face(top_face_pred)
        return {"clicks": [((50, 64, 15), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Profile", "Profile", pick, "Κλικ στην πάνω έδρα", "Κόβει γύρω-γύρω το περίγραμμα",
             zoom=1.3)


@scene("CAM_Pocket_Shape")
def s_pocket():
    def pick(r):
        f = r.face(flat_at(9))
        return {"clicks": [((27, 22, 9), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Pocket_Shape", "PocketShape", pick, "Κλικ στον πάτο της τσέπης",
             "Αδειάζει την τσέπη σε στρώσεις")


@scene("CAM_MillFacing")
def s_facing():
    op_scene("CAM_MillFacing", "MillFacing", lambda r: {"clicks": [], "base": None}, None,
             "Ισιώνει την πάνω πλευρά του ακατέργαστου", frames=32, press_first=True, show_stock=True)


@scene("CAM_Helix")
def s_helix():
    def pick(r):
        f = r.face(cyl_r(8))
        return {"clicks": [((78, 54, 8), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Helix", "Helix", pick, "Κλικ στο τοίχωμα της τρύπας",
             "Ελικοειδής κάθοδος · ανοίγει την τρύπα", zoom=0.6, frames=36, focus=(78, 46, 8))


@scene("CAM_Adaptive")
def s_adaptive():
    def pick(r):
        f = r.face(flat_at(9))
        return {"clicks": [((27, 22, 9), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Adaptive", "Adaptive", pick, "Κλικ στον πάτο της τσέπης",
             "Σταθερό φορτίο στο κοπτικό", frames=34)


@scene("CAM_Slot")
def s_slot():
    def pick(r):
        f = r.face(lambda f: flat_at(11)(f))
        return {"clicks": [((28, 52, 11), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Slot", "Slot", pick, "Κλικ στον πάτο του αυλακιού",
             "Ένα πέρασμα στη μέση του αυλακιού", zoom=0.6, focus=(28, 52, 11))


@scene("CAM_Drilling")
def s_drilling():
    def pick(r):
        fs = [i + 1 for i, f in enumerate(r.model.Shape.Faces) if cyl_r(3)(f)]
        return {"clicks": [((62, 19, 8), "Face%d" % fs[0]), ((88, 19, 8), "Face%d" % fs[1])],
                "base": [(r.model, tuple("Face%d" % i for i in fs))]}
    op_scene("CAM_Drilling", "Drilling", pick, "Έλεγξε / πρόσθεσε τρύπες",
             "Τρυπάει σε κάθε κέντρο", tc="5mm_Drill.fctb", frames=26, press_first=True,
             zoom=0.75, focus=(75, 20, 8))


@scene("CAM_ThreadMilling")
def s_thread():
    def pick(r):
        f = r.face(cyl_r(8))
        return {"clicks": [((78, 54, 8), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_ThreadMilling", "ThreadMilling", pick, "Κλικ στο τοίχωμα της τρύπας",
             "Κόβει σπείρωμα με ελικοειδή κίνηση", zoom=0.6, focus=(78, 46, 8), tc="5mm-thread-cutter.fctb",
             frames=36, props={"ThreadName": "M16", "MajorDiameter": 16.0, "MinorDiameter": 14.0,
                               "Pitch": 2.0})


def text_extra(r):
    _, ss = text_plate(r.doc)
    r.ss = ss
    ss.ViewObject.LineColor = (0.12, 0.16, 0.23)
    return [ss]


@scene("CAM_Engrave")
def s_engrave():
    def pick(r):
        ss = [m for m in r.job.Model.Group if "ShapeString" in m.Name or "ShapeString" in m.Label]
        obj = ss[0] if ss else r.ss
        return {"obj": obj, "clicks": [((22, 20, 10), "")], "base": [(obj, ("",))]}
    op_scene("CAM_Engrave", "Engrave", pick, "Κλικ στο κείμενο",
             "Χαράζει πάνω στις γραμμές", shape=Part.makeBox(90, 40, 10), extra=text_extra,
             tc="60degree_Vbit.fctb", zoom=1.0, top=False, frames=34)


@scene("CAM_Vcarve")
def s_vcarve():
    def pick(r):
        ss = [m for m in r.job.Model.Group if "ShapeString" in m.Name or "ShapeString" in m.Label]
        obj = ss[0] if ss else r.ss
        return {"obj": obj, "clicks": [((22, 20, 10), "")], "base": [(obj, ("",))]}
    op_scene("CAM_Vcarve", "Vcarve", pick, "Κλικ στο κείμενο",
             "V-κοπτικό: φαρδύ = βαθύτερα", shape=Part.makeBox(90, 40, 10), extra=text_extra,
             tc="60degree_Vbit.fctb", zoom=1.0, frames=34)


@scene("CAM_Deburr")
def s_deburr():
    def pick(r):
        f = r.face(top_face_pred)
        return {"clicks": [((50, 64, 15), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Deburr", "Deburr", pick, "Κλικ στην πάνω έδρα",
             "Φάλτσο στις ακμές (σπάει το γρέζι)", tc="45degree_chamfer.fctb", zoom=1.3)


@scene("CAM_Pocket3D")
def s_pocket3d():
    def pick(r):
        f = r.face(lambda f: f.Surface.__class__.__name__ == "Sphere")
        return {"clicks": [((40, 30, 14), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_Pocket3D", "Pocket", pick, "Κλικ στην καμπύλη επιφάνεια",
             "Ξεχοντρίζει τρισδιάστατη τσέπη", shape=bowl(), zoom=1.2, frames=34)


# ---------------------------------------------------------------------------
# Path modification: select an operation (its path), press, see the change
# ---------------------------------------------------------------------------
def outer_profile(r):
    f = r.face(top_face_pred)
    return r.op("Profile", [(r.model, (f,))])


def inner_profile(r):
    """Profile of the square pocket walls (inside): the case for dogbones/ramps."""
    f = r.face(flat_at(9))
    return r.op("Profile", [(r.model, (f,))], Side="Inside")


def dressup_scene(name, base_fn, make, text, zoom=1.25, click_at=(50, 0, 0), frames=30, run=True,
                  top=False):
    r = Rec(name)
    r.make_job()
    o = base_fn(r)
    r.view(zoom, top=top)
    r.cap(1, "Κλικ στη διαδρομή")
    r.click(click_at, o)
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    Gui.Selection.clearSelection()
    d = make(r, o)
    r.see_through()
    r.doc.recompute()
    r.style_path(d, NEWC)
    try:
        o.ViewObject.Visibility = False
    except Exception:
        pass
    r.cap(3, text)
    r.img(blend=True)
    if run:
        r.run(d, frames=frames)
    r.hold(1800)
    r.save()
    return r, d


def via_gui(cmd):
    """Run the real toolbar command on the current selection, then press OK."""
    def make(r, o):
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(r.doc.Name, o.Name)
        before = {x.Name for x in r.doc.Objects}
        Gui.runCommand(cmd)
        pump(800)
        dlg = Gui.Control.activeTaskDialog()
        if dlg is not None:
            dlg.accept()
            pump(500)
        new = [x for x in r.doc.Objects if x.Name not in before and hasattr(x, "Path")]
        r.doc.recompute()
        return new[-1]
    return make


@scene("CAM_DressupDogbone")
def s_dogbone():
    dressup_scene("CAM_DressupDogbone", inner_profile, via_gui("CAM_DressupDogbone"),
                  "Μικρές «τρύπες» στις εσωτερικές γωνίες", zoom=0.75, click_at=(27, 10, 9))


@scene("CAM_DressupTag")
def s_tag():
    dressup_scene("CAM_DressupTag", outer_profile, via_gui("CAM_DressupTag"),
                  "Γεφυράκια: το κομμάτι δεν φεύγει", zoom=1.3, click_at=(50, -2.5, 0))


@scene("CAM_DressupLeadInOut")
def s_leadinout():
    dressup_scene("CAM_DressupLeadInOut", outer_profile, via_gui("CAM_DressupLeadInOut"),
                  "Ομαλή είσοδος και έξοδος", zoom=1.3, click_at=(50, -2.5, 0))


@scene("CAM_DressupRampEntry")
def s_ramp():
    dressup_scene("CAM_DressupRampEntry", inner_profile, via_gui("CAM_DressupRampEntry"),
                  "Μπαίνει με ράμπα, όχι κάθετα", zoom=0.75, click_at=(27, 10, 9))


@scene("CAM_DressupPathBoundary")
def s_boundary():
    def make(r, o):
        d = via_gui("CAM_DressupPathBoundary")(r, o)
        try:
            d.Stock.Length, d.Stock.Width = 60, 70
            d.Stock.Height = 40
            d.Stock.Placement.Base = V(-5, -5, -5)
        except Exception:
            traceback.print_exc()
        return d
    dressup_scene("CAM_DressupPathBoundary", outer_profile, make,
                  "Κρατάει μόνο ό,τι είναι μέσα στο όριο", zoom=1.3, click_at=(50, -2.5, 0))


@scene("CAM_DressupDragKnife")
def s_dragknife():
    dressup_scene("CAM_DressupDragKnife", outer_profile, via_gui("CAM_DressupDragKnife"),
                  "Θηλιές στις γωνίες για το μαχαίρι", zoom=0.6, click_at=(50, -2.5, 0))


@scene("CAM_DressupMirror")
def s_mirror():
    def base(r):
        f = r.face(flat_at(9))
        return r.op("PocketShape", [(r.model, (f,))])
    dressup_scene("CAM_DressupMirror", base, via_gui("CAM_DressupMirror"),
                  "Καθρέφτης της διαδρομής", click_at=(27, 22, 9))


@scene("CAM_DressupArray")
def s_darray():
    def base(r):
        f = r.face(flat_at(9))
        return r.op("PocketShape", [(r.model, (f,))])

    def make(r, o):
        d = via_gui("CAM_DressupArray")(r, o)
        d.Type = "Linear1D"
        d.Copies = 2
        d.Offset = V(40, 0, 0)
        return d
    dressup_scene("CAM_DressupArray", base, make, "Επαναλαμβάνει τη διαδρομή", click_at=(27, 22, 9),
                  zoom=1.4)


@scene("CAM_Array")
def s_array():
    def base(r):
        f = r.face(flat_at(9))
        return r.op("PocketShape", [(r.model, (f,))])

    def make(r, o):
        d = via_gui("CAM_Array")(r, o)
        d.Type = "Linear1D"
        d.Copies = 2
        d.Offset = V(40, 0, 0)
        return d
    dressup_scene("CAM_Array", base, make, "Επαναλαμβάνει τη διαδρομή", click_at=(27, 22, 9),
                  zoom=1.4)


@scene("CAM_DressupPlungeMilling")
def s_plunge():
    def base(r):
        f = r.face(flat_at(9))
        return r.op("PocketShape", [(r.model, (f,))])
    dressup_scene("CAM_DressupPlungeMilling", base, via_gui("CAM_DressupPlungeMilling"),
                  "Κόβει με κάθετες βουτιές", click_at=(27, 22, 9), zoom=0.8)


def copy_scene(name, text, panel_after):
    r = Rec(name)
    o = pocket_job(r)
    r.view(1.25)
    r.tree_pick(ops=["Operations", "   " + o.Label], row=2, caption="Κλικ στην εργασία (στο δέντρο)")
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(r.doc.Name, o.Name)
    before = {x.Name for x in r.doc.Objects}
    Gui.runCommand(name)
    pump(800)
    dlg = Gui.Control.activeTaskDialog()
    if dlg is not None:
        dlg.accept()
        pump(400)
    new = [x for x in r.doc.Objects if x.Name not in before and hasattr(x, "Path")]
    r.cap(3, text)
    r.panel("Μοντέλο (δέντρο)", ["Job", "   Operations", "      " + o.Label] +
            ["      " + x.Label + panel_after for x in new], mono=False, pos="left")
    r.hold(3000)
    r.save()


@scene("CAM_OperationCopy")
def s_opcopy():
    copy_scene("CAM_OperationCopy", "Πλήρες αντίγραφο της εργασίας", "   ← νέο")


@scene("CAM_SimpleCopy")
def s_simplecopy():
    copy_scene("CAM_SimpleCopy", "Αντίγραφο μόνο της διαδρομής", "   ← σκέτη διαδρομή")


def run_all():
    log = open(os.path.join(OUT, "rec_log.txt"), "a")
    try:
        set_theme()
        Gui.activateWorkbench("PartWorkbench")
        pump(200)
        Gui.activateWorkbench("CAMWorkbench")
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


if os.environ.get("WT_LIST"):
    print(" ".join(SCENES))
    os._exit(0)
os.makedirs(OUT, exist_ok=True)
QtCore.QTimer.singleShot(3500, run_all)

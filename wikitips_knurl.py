# SPDX-License-Identifier: LGPL-2.1-or-later
"""WikiTips Knurl: knurling on a cylinder in one click.

Select the outer cylindrical face of a solid, press the Knurl button, pick the
pattern and the pitch. Two kinds:
  - "Πραγματικό": real V-shaped teeth cut into the solid (3D printing, renders);
  - "Ελαφρύ": only the groove lines on the surface (fast; for drawings, where
    knurling is drawn as crossed lines anyway).
Inside a Part Design Body it becomes a normal feature of the Body (it follows
the Tip like a Pocket); elsewhere a Part feature that cuts the selected solid.

The teeth are pyramids on a diamond grid (or straight V-grooves), built from
planar faces, so the boolean is fast and always valid (checked in FreeCAD 26.3:
D20 x L20, pitch 1 mm: about 10 s, one valid solid).
The cylinder is stored as numbers (axis, radius, start, length), not as a face
name, so renaming faces upstream ("topological naming") does not break it; on
every recompute the matching cylinder of the new base shape is looked up again.
"""

import math
import os

import FreeCAD as App
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "Resources", "WikiTipsKnurl.svg")
PATTERNS = ["Διαμάντι", "Ίσιο"]
KINDS = ["Πραγματικό", "Ελαφρύ"]
V = App.Vector


# --------------------------------------------------------------------------
# geometry (no GUI: also usable from FreeCADCmd and in tests)
# --------------------------------------------------------------------------
def cylinder_of(face):
    """(center, axis, radius, vmin, vmax) of a cylindrical face, or None."""
    s = getattr(face, "Surface", None)
    if s is None or s.TypeId != "Part::GeomCylinder":
        return None
    u0, u1, v0, v1 = face.ParameterRange
    return V(s.Center), V(s.Axis).normalize(), s.Radius, v0, v1


def is_outer(face):
    """True for the outside of a shaft, False for the inside of a hole."""
    c = cylinder_of(face)
    u0, u1, v0, v1 = face.ParameterRange
    u, v = (u0 + u1) / 2, (v0 + v1) / 2
    p = face.valueAt(u, v)
    n = face.normalAt(u, v)
    center, axis = c[0], c[1]
    radial = p - center
    radial = radial - axis * radial.dot(axis)
    return radial.dot(n) > 0


def depth_for(pitch, pattern, angle):
    """Depth of 90° teeth: half the groove spacing measured across the groove."""
    a = 0.0 if pattern == "Ίσιο" else angle
    return 0.5 * pitch * math.cos(math.radians(a))


def _grid(R, L, pitch, angle, straight):
    n = max(3, int(round(2 * math.pi * R / pitch)))
    if straight:
        return n, 1, L
    k = math.tan(math.radians(angle)) / R
    rows = max(1, int(round(L / (math.pi / n / k))))
    return n, rows, L / rows


def knurl_tool(R, L, pitch, angle, depth, straight=False):
    """The material a knurling removes from a cylinder of radius R, axis Z, from z=0 to L."""
    n, rows, dz = _grid(R, L, pitch, angle, straight)
    na = 2 * n
    dth = 2 * math.pi / n
    ro = R / math.cos(dth / 4) + 0.01     # outer prism just outside the cylinder

    def node(a, b):
        a %= na
        valley = (a % 2 == 0) if straight else ((a + b) % 2 == 0)
        r = R - depth if valley else R
        t = a * dth / 2
        return V(r * math.cos(t), r * math.sin(t), b * dz)

    def outer(a, b):
        t = (a % na) * dth / 2
        return V(ro * math.cos(t), ro * math.sin(t), b * dz)

    def tri(*p):
        return Part.Face(Part.makePolygon(list(p) + [p[0]]))

    faces = []
    for b in range(rows):
        for a in range(na):
            p00, p10, p11, p01 = node(a, b), node(a + 1, b), node(a + 1, b + 1), node(a, b + 1)
            if straight:
                faces.append(tri(p00, p10, p11, p01))
            elif (a + b) % 2 == 0:      # split along the line joining the two valleys
                faces += [tri(p00, p10, p11), tri(p00, p11, p01)]
            else:
                faces += [tri(p00, p10, p01), tri(p10, p11, p01)]
    for a in range(na):
        faces.append(tri(outer(a, 0), outer(a + 1, 0), outer(a + 1, rows), outer(a, rows)))
    for b in (0, rows):
        inner = Part.makePolygon([node(a, b) for a in range(na + 1)])
        out = Part.makePolygon([outer(a, b) for a in range(na + 1)])
        faces.append(Part.makeFace([out, inner], "Part::FaceMakerBullseye"))
    solid = Part.Solid(Part.Shell(faces))
    if solid.Volume < 0:
        solid.reverse()
    return solid


def knurl_lines(R, L, pitch, angle, straight=False):
    """Groove lines on the surface (helices or straight lines) for the light kind."""
    n, rows, dz = _grid(R, L, pitch, angle, straight)
    edges = []
    if straight:
        for i in range(n):
            t = 2 * math.pi * i / n
            p = V(R * math.cos(t), R * math.sin(t), 0)
            edges.append(Part.makeLine(p, p + V(0, 0, L)))
        return Part.makeCompound(edges)
    lead = 2 * math.pi * R / math.tan(math.radians(angle))   # axial length of one turn
    for left in (False, True):
        h = Part.makeHelix(lead, L, R, 0, left)
        for i in range(n):
            c = h.copy()
            c.rotate(V(), V(0, 0, 1), 360.0 * i / n)
            edges += c.Edges
    return Part.makeCompound(edges)


def placement_for(center, axis, start):
    rot = App.Rotation(V(0, 0, 1), axis)
    return App.Placement(center + axis * start, rot)


def find_cylinder(shape, center, axis, radius):
    """The outer cylinder of `shape` on the same axis line, closest in radius (after upstream edits)."""
    best = None
    for f in shape.Faces:
        c = cylinder_of(f)
        if c is None or abs(abs(c[1].dot(axis)) - 1) > 1e-6:
            continue
        d = c[0] - center
        if (d - axis * d.dot(axis)).Length > 1e-4 or not is_outer(f):
            continue
        if best is None or abs(c[2] - radius) < abs(best[2] - radius):
            best = c
    return best


# --------------------------------------------------------------------------
# the feature
# --------------------------------------------------------------------------
def _props(obj):
    add = obj.addProperty
    add("App::PropertyEnumeration", "Pattern", "Knurl", "Διαμάντι (σταυρωτό) ή Ίσιο (παράλληλο με τον άξονα)")
    obj.Pattern = PATTERNS
    add("App::PropertyEnumeration", "Kind", "Knurl", "Πραγματικό: κόβει δόντια. Ελαφρύ: μόνο γραμμές (για σχέδια)")
    obj.Kind = KINDS
    add("App::PropertyLength", "Pitch", "Knurl", "Βήμα: απόσταση ανάμεσα στα δόντια γύρω-γύρω")
    add("App::PropertyAngle", "Angle", "Knurl", "Γωνία των ραβδώσεων ως προς τον άξονα (συνήθως 30°)")
    add("App::PropertyLength", "Depth", "Knurl", "Βάθος δοντιού (0 = αυτόματο, δόντια 90°)")
    add("App::PropertyDistance", "StartMargin", "Knurl", "Απόσταση από την αρχή του κυλίνδρου")
    add("App::PropertyDistance", "EndMargin", "Knurl", "Απόσταση από το τέλος του κυλίνδρου")
    for name in ("AxisCenter", "AxisDirection"):
        add("App::PropertyVector", name, "Cylinder", "Ο κύλινδρος (αποθηκεύεται ως αριθμοί)")
    add("App::PropertyLength", "Radius", "Cylinder", "Ακτίνα του κυλίνδρου")
    add("App::PropertyFloat", "VMin", "Cylinder", "Αρχή κατά μήκος του άξονα")
    add("App::PropertyFloat", "VMax", "Cylinder", "Τέλος κατά μήκος του άξονα")
    for name in ("AxisCenter", "AxisDirection", "Radius", "VMin", "VMax"):
        obj.setEditorMode(name, 1)   # read only: set by the command
    obj.Pitch, obj.Angle = 1.0, 30.0


def _base_shape(obj):
    base = getattr(obj, "BaseFeature", None) or getattr(obj, "Base", None)
    return base.Shape if base is not None and not base.Shape.isNull() else None


class Knurl:
    def __init__(self, obj):
        obj.Proxy = self
        _props(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def execute(self, obj):
        base = _base_shape(obj)
        if base is None:
            raise RuntimeError("WikiTips Knurl: no base solid")
        axis = V(obj.AxisDirection).normalize()
        center = V(obj.AxisCenter)
        cyl = find_cylinder(base, center, axis, obj.Radius.Value) or (
            center, axis, obj.Radius.Value, obj.VMin, obj.VMax)
        center, axis, radius, vmin, vmax = cyl
        start = vmin + obj.StartMargin.Value
        length = (vmax - obj.EndMargin.Value) - start
        pitch = obj.Pitch.Value
        if length <= 0 or pitch <= 0:
            raise RuntimeError("WikiTips Knurl: length and pitch must be greater than zero")
        straight = obj.Pattern == "Ίσιο"
        depth = obj.Depth.Value or depth_for(pitch, obj.Pattern, obj.Angle.Value)
        depth = min(depth, radius * 0.5)
        pl = placement_for(center, axis, start)
        if obj.Kind == "Ελαφρύ":
            lines = knurl_lines(radius, length, pitch, obj.Angle.Value, straight)
            lines.Placement = pl
            result = Part.makeCompound([base, lines])
            tool = None
        else:
            tool = knurl_tool(radius, length, pitch, obj.Angle.Value, depth, straight)
            tool.Placement = pl
            result = base.cut(tool)
            if len(result.Solids) == 1:
                result = result.Solids[0]
        if hasattr(obj, "AddSubShape"):
            obj.AddSubShape = tool if tool is not None else Part.Shape()
        obj.Shape = result


def make_knurl(face_owner, face, doc=None):
    """Create the knurl feature for `face` of `face_owner` (a document object)."""
    doc = doc or face_owner.Document
    cyl = cylinder_of(face)
    if cyl is None:
        raise ValueError("not a cylinder")
    body = None
    for o in face_owner.InList:
        if o.TypeId == "PartDesign::Body":
            body = o
    if body is not None:
        # PartDesign::FeatureSubtractivePython / AdditivePython crash FreeCAD 26.3 when created with
        # the GUI up (even without WikiTips, checked 2026-10-17); the plain FeaturePython is fine
        obj = doc.addObject("PartDesign::FeaturePython", "Knurl")
        body.addObject(obj)
    else:
        obj = doc.addObject("Part::FeaturePython", "Knurl")
        obj.addProperty("App::PropertyLink", "Base", "Knurl", "Το στερεό που παίρνει knurling")
        obj.Base = face_owner
    Knurl(obj)
    center, axis, radius, vmin, vmax = cyl
    obj.AxisCenter, obj.AxisDirection, obj.Radius, obj.VMin, obj.VMax = center, axis, radius, vmin, vmax
    obj.Label = "Knurl"
    return obj


# --------------------------------------------------------------------------
# GUI: button, Greek task panel, view provider
# --------------------------------------------------------------------------
def default_pitch(diameter):
    """A usual knurl pitch for the diameter (ideas from DIN 82 tables; easy to change)."""
    for d, p in ((8, 0.6), (16, 0.8), (32, 1.0)):
        if diameter <= d:
            return p
    return 1.2


if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui

    try:
        from PySide import QtWidgets
    except ImportError:  # pragma: no cover
        QtWidgets = QtGui

    def _tell(title, text, steps):
        """Greek guidance in the WikiTips card (falls back to the status bar)."""
        try:
            import wikitips_errors
            wikitips_errors.tell(title, text, steps)
        except Exception:
            Gui.getMainWindow().statusBar().showMessage("WikiTips: %s. %s" % (title, text), 10000)

    def _selected_face():
        """(owner object, face) of the selected cylindrical face, or (None, reason)."""
        sel = Gui.Selection.getSelectionEx("", 0)   # resolve to the object that owns the face
        for s in sel:
            for name, sub in zip(s.SubElementNames, s.SubObjects):
                if not name.split(".")[-1].startswith("Face"):
                    continue
                owner = s.Object
                if owner.TypeId == "PartDesign::Body":
                    owner = owner.Tip
                if cylinder_of(sub) is None:
                    return None, "flat"
                if not is_outer(sub):
                    return None, "inner"
                return owner, sub
        return None, "none"

    class TaskKnurl:
        """Greek panel. While it is open the preview is the fast kind (lines)."""

        def __init__(self, obj):
            self.obj = obj
            self.kind = obj.Kind
            self.form = QtWidgets.QWidget()
            self.form.setWindowTitle("Knurl (ραβδώσεις)")
            lay = QtWidgets.QFormLayout(self.form)
            self.pattern = QtWidgets.QComboBox()
            self.pattern.addItems(PATTERNS)
            self.pattern.setCurrentText(obj.Pattern)
            self.kindbox = QtWidgets.QComboBox()
            self.kindbox.addItems(["Πραγματικό (κόβει δόντια)", "Ελαφρύ (μόνο γραμμές)"])
            self.kindbox.setCurrentIndex(KINDS.index(obj.Kind))
            self.pitch = self._spin(obj.Pitch.Value, 0.1, 10, " mm")
            self.angle = self._spin(obj.Angle.Value, 5, 60, "°")
            self.depth = self._spin(obj.Depth.Value, 0, 10, " mm")
            self.depth.setSpecialValueText("αυτόματο")
            self.start = self._spin(obj.StartMargin.Value, 0, 1000, " mm")
            self.end = self._spin(obj.EndMargin.Value, 0, 1000, " mm")
            rows = [("Μοτίβο", self.pattern, "Διαμάντι: σταυρωτές ραβδώσεις. Ίσιο: παράλληλες με τον άξονα."),
                    ("Είδος", self.kindbox, "Πραγματικό: για 3D εκτύπωση. Ελαφρύ: για σχέδια (γρήγορο)."),
                    ("Βήμα", self.pitch, "Απόσταση ανάμεσα στα δόντια. Μικρό = λεπτό knurling."),
                    ("Γωνία", self.angle, "Γωνία των ραβδώσεων ως προς τον άξονα. Συνήθως 30°."),
                    ("Βάθος", self.depth, "0 = αυτόματο (δόντια 90°)."),
                    ("Από την αρχή", self.start, "Πόσο μακριά από την αρχή του κυλίνδρου ξεκινάει."),
                    ("Από το τέλος", self.end, "Πόσο πριν από το τέλος σταματάει.")]
            for label, w, tip in rows:
                w.setToolTip(tip)
                lay.addRow(label, w)
            hint = QtWidgets.QLabel("Όσο είναι ανοιχτό το παράθυρο βλέπεις γρήγορη προεπισκόπηση με γραμμές. "
                                    "Τα πραγματικά δόντια υπολογίζονται με το OK (λίγα δευτερόλεπτα).")
            hint.setWordWrap(True)
            hint.setStyleSheet("color:gray")
            lay.addRow(hint)
            self.angle.setEnabled(obj.Pattern != "Ίσιο")
            for w in (self.pitch, self.angle, self.depth, self.start, self.end):
                w.valueChanged.connect(self.preview)
            self.pattern.currentIndexChanged.connect(self.preview)
            obj.Kind = "Ελαφρύ"
            self.preview()
            global _PANEL
            _PANEL = self     # for tests

        @staticmethod
        def _spin(value, lo, hi, suffix):
            s = QtWidgets.QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(2)
            s.setSingleStep(0.1 if hi <= 10 else 1)
            s.setSuffix(suffix)
            s.setValue(value)
            return s

        def apply(self):
            o = self.obj
            o.Pattern = self.pattern.currentText()
            o.Pitch, o.Angle, o.Depth = self.pitch.value(), self.angle.value(), self.depth.value()
            o.StartMargin, o.EndMargin = self.start.value(), self.end.value()
            self.angle.setEnabled(o.Pattern != "Ίσιο")

        def preview(self, *args):
            try:
                self.apply()
                self.obj.Document.recompute()
            except Exception:
                pass

        def accept(self):
            self.apply()
            self.obj.Kind = KINDS[self.kindbox.currentIndex()]
            QtWidgets.QApplication.setOverrideCursor(_cursor())
            Gui.getMainWindow().statusBar().showMessage("WikiTips: υπολογίζω το knurling…")
            QtWidgets.QApplication.processEvents()
            try:
                self.obj.Document.recompute()
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()
                Gui.getMainWindow().statusBar().clearMessage()
            Gui.ActiveDocument.resetEdit()
            return True

        def reject(self):
            self.obj.Kind = self.kind
            self.obj.Document.recompute()
            Gui.ActiveDocument.resetEdit()
            return True

    _PANEL = None

    def _cursor():
        import wikitips
        return QtGui.QCursor(wikitips._enum(QtCore.Qt, "WaitCursor", "CursorShape"))

    class ViewProviderKnurl:
        def __init__(self, vobj):
            vobj.Proxy = self

        def attach(self, vobj):
            self.Object = vobj.Object
            try:   # thousands of small tooth edges: thin grey lines instead of thick black ones
                vobj.LineWidth = 1.0
                vobj.LineColor = (0.35, 0.38, 0.42)
            except Exception:
                pass

        def getIcon(self):
            return ICON

        def claimChildren(self):
            base = getattr(self.Object, "Base", None)
            return [base] if base is not None else []

        def setEdit(self, vobj, mode=0):
            if mode != 0:
                return None
            Gui.Control.showDialog(TaskKnurl(vobj.Object))
            return True

        def unsetEdit(self, vobj, mode=0):
            Gui.Control.closeDialog()
            return True

        def doubleClicked(self, vobj):
            Gui.ActiveDocument.setEdit(vobj.Object.Name)
            return True

        def dumps(self):
            return None

        def loads(self, state):
            return None

    class KnurlCommand:
        def GetResources(self):
            return {"Pixmap": ICON, "MenuText": "Knurl (ραβδώσεις)",
                    "ToolTip": "Knurling σε κύλινδρο: διάλεξε την εξωτερική κυλινδρική επιφάνεια και πάτα το κουμπί."}

        def IsActive(self):
            return App.ActiveDocument is not None

        def Activated(self):
            owner, face = _selected_face()
            if owner is None:
                why = {"none": "Δεν έχεις διαλέξει επιφάνεια.",
                       "flat": "Η επιφάνεια που διάλεξες δεν είναι κυλινδρική.",
                       "inner": "Διάλεξες το εσωτερικό μιας τρύπας: το knurling γίνεται απ' έξω."}[face]
                _tell("Διάλεξε τον κύλινδρο", why,
                      ["Κάνε κλικ στην εξωτερική πλευρά του κυλίνδρου στο 3D (γίνεται πράσινη).",
                       "Μετά πάτα το κουμπί Knurl."])
                return
            doc = owner.Document
            doc.openTransaction("Knurl")
            obj = make_knurl(owner, face)
            obj.Pitch = default_pitch(2 * obj.Radius.Value)
            if obj.ViewObject is not None:
                ViewProviderKnurl(obj.ViewObject)
            if getattr(obj, "Base", None) is not None and obj.Base.ViewObject is not None:
                obj.Base.ViewObject.Visibility = False
            doc.commitTransaction()
            Gui.Selection.clearSelection()
            Gui.ActiveDocument.setEdit(obj.Name)

    def install():
        Gui.addCommand("WikiTips_Knurl", KnurlCommand())

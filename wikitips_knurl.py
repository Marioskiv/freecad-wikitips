# SPDX-License-Identifier: LGPL-2.1-or-later
"""WikiTips Knurl: knurling on a cylinder in one click.

Select the outer cylindrical face of a solid, press the Knurl button, pick the
pattern and the pitch. Two kinds:
  - "Πραγματικό": real V-shaped teeth cut into the solid (3D printing, renders);
  - "Ελαφρύ": the groove lines are only drawn on screen by the view provider; the
    solid is not changed, so later features never see them. (For a technical
    drawing, TechDraw's geometric hatch "Diamond" is the usual knurl symbol.)
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


def upwards(center, axis, vmin, vmax):
    """The same cylinder with its axis pointing "up" (world Z, else Y, else X).

    FreeCAD often gives the side of a Pad an axis pointing down (v from -L to 0);
    people mean "from the bottom" and want text the right way up.
    """
    for ref in (V(0, 0, 1), V(0, 1, 0), V(1, 0, 0)):
        d = axis.dot(ref)
        if abs(d) > 1e-9:
            if d < 0:
                return center, -axis, -vmax, -vmin
            break
    return center, axis, vmin, vmax


def depth_for(pitch, pattern, angle):
    """Depth of 90° teeth: half the groove spacing measured across the groove."""
    a = 0.0 if pattern == "Ίσιο" else angle
    return 0.5 * pitch * math.cos(math.radians(a))


def _angle(angle):
    """Helix angle kept between 5° and 60°: 0° divides by zero, near 90° gives endless rows."""
    return min(max(angle, 5.0), 60.0)


def _grid(R, L, pitch, angle, straight):
    angle = _angle(angle)
    n = max(3, int(round(2 * math.pi * R / pitch)))
    if straight:
        return n, 1, L
    k = math.tan(math.radians(angle)) / R
    rows = max(1, int(round(L / (math.pi / n / k))))
    return n, rows, L / rows


# Limits measured in FreeCAD 26.3 (2026-10-17). Direct build: ~0.3 ms and ~20 KB per tooth face
# (D50 x 40 mm, pitch 1 = 28 888 faces: 9 s, 640 MB; 59 136 faces: 19 s, 1.2 GB). The boolean
# fallback (band crossed by a hole or a flat) is ~4x slower and uses more memory.
MAX_FACES = 60000
MAX_FACES_BOOLEAN = 30000
LAST_METHOD = ""
PEAK_INSET = 0.002   # teeth tips 2 µm inside the cylinder: no tangent faces, boolean 3-5x faster


def face_count(R, L, pitch, angle, straight=False):
    """How many tooth faces a real knurl would have (to refuse ones that are too big)."""
    if R <= 0 or L <= 0 or pitch <= 0:
        return 0
    n, rows, dz = _grid(R, L, pitch, angle, straight)
    return 2 * n * rows * (1 if straight else 2)


def seconds_for(faces):
    return max(1, int(round(faces * 12.0 / 28888)))   # 9 s to build + ~3 s to show (measured)


def knurl_tool(R, L, pitch, angle, depth, straight=False):
    """The material a knurling removes from a cylinder of radius R, axis Z, from z=0 to L.

    Built as one triangle mesh turned into a solid (shared edges: much faster than
    joining thousands of separate faces).
    """
    n, rows, dz = _grid(R, L, pitch, angle, straight)
    na = 2 * n
    dth = 2 * math.pi / n
    ro = R / math.cos(dth / 4) + 0.01     # outer prism just outside the cylinder
    pts, index = [], {}

    def point(kind, a, b):
        a %= na
        key = (kind, a, b)
        if key not in index:
            if kind == "o":
                r = ro
            else:
                valley = (a % 2 == 0) if straight else ((a + b) % 2 == 0)
                r = R - depth if valley else R - PEAK_INSET
            t = a * dth / 2
            index[key] = len(pts)
            pts.append(V(r * math.cos(t), r * math.sin(t), b * dz))
        return index[key]

    def node(a, b):
        return point("n", a, b)

    def outer(a, b):
        return point("o", a, b)

    tris = []
    for b in range(rows):
        for a in range(na):
            p00, p10, p11, p01 = node(a, b), node(a + 1, b), node(a + 1, b + 1), node(a, b + 1)
            if straight or (a + b) % 2 == 0:   # split along the line joining the two valleys
                tris += [(p00, p10, p11), (p00, p11, p01)]
            else:
                tris += [(p00, p10, p01), (p10, p11, p01)]
    for a in range(na):
        tris += [(outer(a, 0), outer(a, rows), outer(a + 1, rows)), (outer(a, 0), outer(a + 1, rows), outer(a + 1, 0)),
                 (node(a, 0), outer(a, 0), outer(a + 1, 0)), (node(a, 0), outer(a + 1, 0), node(a + 1, 0)),
                 (node(a, rows), node(a + 1, rows), outer(a + 1, rows)),
                 (node(a, rows), outer(a + 1, rows), outer(a, rows))]
    mesh = Part.Shape()
    mesh.makeShapeFromMesh((pts, tris), 1e-7)
    solid = Part.Solid(mesh if mesh.ShapeType == "Shell" else Part.Shell(mesh.Faces))
    if solid.Volume < 0:
        solid.reverse()
    return solid


def direct_knurl(base, pl, R, L, pitch, angle, depth, straight=False):
    """Knurled solid built directly, without the slow boolean (4-8x faster).

    The band is the cylinder of radius R from pl.Base along pl's Z for a length L.
    Works when the band is a clean full ring of material (no hole, flat or slot
    crossing it): the part gets a plain groove (an analytic cut, instant), whose
    faces are replaced by the tooth triangles and two end faces, all sewn into
    one shell. Everything is built in the part's own coordinates (moving shapes
    back and forth left some faces behind, found in a Body test). Returns None
    when not possible; the caller then uses the boolean.
    Checked in FreeCAD 26.3: same volume as the boolean, valid solid, booleans
    with the result behave.
    """
    origin = V(pl.Base)
    axis = pl.Rotation.multVec(V(0, 0, 1))
    rin = R - depth - 0.05
    ring = Part.makeCylinder(R + 1, L, origin, axis).cut(Part.makeCylinder(rin, L, origin, axis))
    full = math.pi * (R * R - rin * rin) * L
    if abs(base.common(ring).Volume - full) > 1e-6 * full:
        return None                      # something crosses the band: use the boolean

    def along(p):
        return (p - origin).dot(axis)

    def radial(p):
        d = p - origin
        return (d - axis * d.dot(axis)).Length

    grooved = base.cut(ring)
    wall = math.pi * (R * R - rin * rin)
    # at each end the band either meets more material (a groove wall is left) or the end of
    # the part (the part's end face, now a disc of radius rin, must become the knurl outline)
    probe = R - depth / 2
    outside = {0.0: base.isInside(pl.multVec(V(probe, 0, -1e-3)), 1e-9, False),
               L: base.isInside(pl.multVec(V(probe, 0, L + 1e-3)), 1e-9, False)}
    keep, holes = [], {0.0: [], L: []}
    for f in grooved.Faces:
        srf, c = f.Surface, f.CenterOfMass
        z = along(c)
        if srf.TypeId == "Part::GeomCylinder" and abs(srf.Radius - rin) < 1e-7 and -1e-7 < z < L + 1e-7:
            continue                     # groove bottom
        if srf.TypeId == "Part::GeomPlane":
            end = 0.0 if abs(z) < 1e-7 else L if abs(z - L) < 1e-7 else None
            if end is not None and outside[end] and abs(f.Area - wall) < 1e-6 * wall:
                continue                 # groove wall
            if end is not None and not outside[end] and radial(c) < rin:
                holes[end] += [w for w in f.Wires if not w.isSame(f.OuterWire)]
                continue                 # the part's end face: replaced by the knurl outline
        keep.append(f)
    n, rows, dz = _grid(R, L, pitch, angle, straight)
    na = 2 * n
    dth = 2 * math.pi / n
    pts, index = [], {}

    def node(a, b):
        a %= na
        key = (a, b)
        if key not in index:
            valley = (a % 2 == 0) if straight else ((a + b) % 2 == 0)
            r = R - depth if valley else R - PEAK_INSET
            t = a * dth / 2
            index[key] = len(pts)
            pts.append(pl.multVec(V(r * math.cos(t), r * math.sin(t), b * dz)))
        return index[key]

    tris = []
    for b in range(rows):
        for a in range(na):
            p00, p10, p11, p01 = node(a, b), node(a + 1, b), node(a + 1, b + 1), node(a, b + 1)
            if straight or (a + b) % 2 == 0:
                tris += [(p00, p10, p11), (p00, p11, p01)]
            else:
                tris += [(p00, p10, p01), (p10, p11, p01)]
    teeth = Part.Shape()
    teeth.makeShapeFromMesh((pts, tris), 1e-7)
    ends = []
    for b, z in ((0, 0.0), (rows, L)):
        zig = Part.makePolygon([pts[node(a, b)] for a in range(na)] + [pts[node(0, b)]])
        if outside[z]:
            wires = [Part.Wire(Part.makeCircle(R, pl.multVec(V(0, 0, z)), axis)), zig]
        else:
            wires = [zig] + holes[z]
        ends += Part.makeFace(wires, "Part::FaceMakerBullseye").Faces
    # whole shapes go into the compound: no Python object per tooth face (that alone took 4 s)
    shell = Part.Compound([Part.Compound(keep), teeth, Part.Compound(ends)])
    shell.sewShape(1e-5)
    shells = shell.Shells
    if len(shells) != 1 or not shells[0].isClosed():
        return None
    solid = Part.Solid(shells[0])
    if solid.Volume < 0:
        solid.reverse()
    # cheap sanity instead of a full isValid() (5 s on 29k faces): the volume must lie between
    # the part with a plain groove and the untouched part, and the far ends must still be solid
    if not (grooved.Volume < solid.Volume < base.Volume):
        return None
    core = (R - depth) / 2
    checks = [pl.multVec(V(core, 0, L / 2))] + [pl.multVec(V(probe, 0, z)) for z, inside in
                                                ((-1e-3, outside[0.0]), (L + 1e-3, outside[L])) if inside]
    for pt in checks:
        if base.isInside(pt, 1e-9, False) and not solid.isInside(pt, 1e-9, False):
            return None                  # a defective solid: let the boolean do it
    return solid


def knurl_lines(R, L, pitch, angle, straight=False):
    """Groove lines on the surface (helices or straight lines) for the light kind."""
    n, rows, dz = _grid(R, L, pitch, angle, straight)
    edges = []
    step = max(1, -(-n // 360))   # at most 360 lines each way: a drawing needs no more
    if straight:
        for i in range(0, n, step):
            t = 2 * math.pi * i / n
            p = V(R * math.cos(t), R * math.sin(t), 0)
            edges.append(Part.makeLine(p, p + V(0, 0, L)))
        return Part.makeCompound(edges)
    lead = 2 * math.pi * R / math.tan(math.radians(_angle(angle)))   # axial length of one turn
    for left in (False, True):
        h = Part.makeHelix(lead, L, R, 0, left)
        for i in range(0, n, step):
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
    add("App::PropertyEnumeration", "Kind", "Knurl", "Πραγματικό: κόβει δόντια. Ελαφρύ: μόνο γραμμές στην οθόνη, το στερεό μένει ίδιο")
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


def layout(obj, base):
    """(center, axis, radius, start, length) of the knurled band, axis pointing up."""
    axis = V(obj.AxisDirection).normalize()
    center = V(obj.AxisCenter)
    cyl = find_cylinder(base, center, axis, obj.Radius.Value) or (
        center, axis, obj.Radius.Value, obj.VMin, obj.VMax)
    center, axis, radius, vmin, vmax = cyl
    center, axis, vmin, vmax = upwards(center, axis, vmin, vmax)   # margins count from the bottom
    start = vmin + obj.StartMargin.Value
    return center, axis, radius, start, (vmax - obj.EndMargin.Value) - start


def lines_for(obj):
    """The groove lines of a light knurl, in the same coordinates as obj.Shape (None if not light)."""
    if getattr(obj, "Kind", "") != "Ελαφρύ":
        return None
    base = _base_shape(obj)
    if base is None:
        return None
    center, axis, radius, start, length = layout(obj, base)
    if length <= 0 or obj.Pitch.Value <= 0:
        return None
    lines = knurl_lines(radius, length, obj.Pitch.Value, obj.Angle.Value, obj.Pattern == "Ίσιο")
    lines.Placement = placement_for(center, axis, start)
    return lines


def size_report(obj):
    """(faces of the real teeth, seconds, too big?) for the Greek panel; None if unknown."""
    try:
        base = _base_shape(obj)
        if base is None:
            return None
        center, axis, radius, start, length = layout(obj, base)
        faces = face_count(radius, length, obj.Pitch.Value, obj.Angle.Value, obj.Pattern == "Ίσιο")
        return faces, seconds_for(faces), faces > MAX_FACES
    except Exception:
        return None


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
        center, axis, radius, start, length = layout(obj, base)
        pitch = obj.Pitch.Value
        if length <= 0 or pitch <= 0:
            raise RuntimeError("WikiTips Knurl: length and pitch must be greater than zero")
        straight = obj.Pattern == "Ίσιο"
        depth = obj.Depth.Value or depth_for(pitch, obj.Pattern, obj.Angle.Value)
        depth = min(max(depth, 0.01), radius * 0.5)
        pl = placement_for(center, axis, start)
        if obj.Kind == "Ελαφρύ":
            # the solid stays as it is: the lines are only drawn by the view provider, so
            # later features (Pocket, Fillet...) never see them (checked: lines in the shape
            # made a Fillet after it fail)
            result = base.copy()
            tool = None
        else:
            faces = face_count(radius, length, pitch, obj.Angle.Value, straight)
            if faces > MAX_FACES:
                raise RuntimeError("WikiTips Knurl: too many teeth (%d faces, max %d)" % (faces, MAX_FACES))
            try:
                result = direct_knurl(base, pl, radius, length, pitch, obj.Angle.Value, depth, straight)
            except Exception:
                result = None
            global LAST_METHOD
            LAST_METHOD = "direct" if result is not None else "boolean"   # for tests and notes
            if result is not None:
                tool = None
            else:                         # band not clean (hole, flat...): the slower boolean
                if faces > MAX_FACES_BOOLEAN:
                    raise RuntimeError("WikiTips Knurl: too many teeth for a band with holes or flats "
                                       "(%d faces, max %d)" % (faces, MAX_FACES_BOOLEAN))
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
                    ("Είδος", self.kindbox, "Πραγματικό: για 3D εκτύπωση. Ελαφρύ: γραμμές μόνο στην οθόνη (γρήγορο). Για τεχνικό σχέδιο: TechDraw, γράμμωση «Diamond»."),
                    ("Βήμα", self.pitch, "Απόσταση ανάμεσα στα δόντια. Μικρό = λεπτό knurling."),
                    ("Γωνία", self.angle, "Γωνία των ραβδώσεων ως προς τον άξονα. Συνήθως 30°."),
                    ("Βάθος", self.depth, "0 = αυτόματο (δόντια 90°)."),
                    ("Από την αρχή", self.start, "Πόσο μακριά από την αρχή του κυλίνδρου ξεκινάει."),
                    ("Από το τέλος", self.end, "Πόσο πριν από το τέλος σταματάει.")]
            for label, w, tip in rows:
                w.setToolTip(tip)
                lay.addRow(label, w)
            self.size = QtWidgets.QLabel()
            self.size.setWordWrap(True)
            lay.addRow(self.size)
            hint = QtWidgets.QLabel("Όσο είναι ανοιχτό το παράθυρο βλέπεις γρήγορη προεπισκόπηση με γραμμές. "
                                    "Τα πραγματικά δόντια υπολογίζονται με το OK.")
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

        def show_size(self):
            """How big the real teeth will be, before anything heavy is computed."""
            rep = size_report(self.obj)
            if rep is None:
                self.size.setText("")
                return False
            faces, secs, too_big = rep
            if too_big:
                self.size.setStyleSheet("color:#B91C1C")
                self.size.setText("Πολύ μεγάλο για πραγματικά δόντια (%d επιφάνειες, όριο %d): θα "
                                  "βάραινε πολύ τον υπολογιστή. Μεγάλωσε το βήμα, μίκρυνε το μήκος, "
                                  "ή διάλεξε Ελαφρύ." % (faces, MAX_FACES))
            else:
                self.size.setStyleSheet("color:gray")
                self.size.setText("Πραγματικά δόντια: %d επιφάνειες, περίπου %d δευτερόλεπτα." % (faces, secs))
            return too_big

        def preview(self, *args):
            try:
                self.apply()
                self.show_size()
                self.obj.Document.recompute()
            except Exception:
                pass

        def accept(self):
            self.apply()
            if KINDS[self.kindbox.currentIndex()] == "Πραγματικό" and self.show_size():
                return False          # too big: the panel stays open, the red text says what to do
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
            self.lines = None
            try:   # thousands of small tooth edges: thin grey lines instead of thick black ones
                vobj.LineWidth = 1.0
                vobj.LineColor = (0.35, 0.38, 0.42)
            except Exception:
                pass
            try:   # the light kind: groove lines drawn on screen only (not part of the solid)
                from pivy import coin
                self.lines = coin.SoSeparator()
                col = coin.SoBaseColor()
                col.rgb = (0.12, 0.16, 0.22)
                style = coin.SoDrawStyle()
                style.lineWidth = 1.5
                self.coords = coin.SoCoordinate3()
                self.lineset = coin.SoLineSet()
                for n in (col, style, self.coords, self.lineset):
                    self.lines.addChild(n)
                vobj.RootNode.addChild(self.lines)
            except Exception:
                self.lines = None

        def updateData(self, obj, prop):
            if prop != "Shape" or getattr(self, "lines", None) is None:
                return
            try:
                pts, counts = [], []
                shape = lines_for(obj)
                if shape is not None:
                    inv = obj.Placement.inverse()
                    for e in shape.Edges:
                        ps = [inv.multVec(p) for p in e.discretize(Deflection=0.05)]
                        pts += [(p.x, p.y, p.z) for p in ps]
                        counts.append(len(ps))
                self.coords.point.setValues(0, len(pts), pts)
                self.coords.point.setNum(len(pts))
                self.lineset.numVertices.setValues(0, len(counts), counts)
                self.lineset.numVertices.setNum(len(counts))
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

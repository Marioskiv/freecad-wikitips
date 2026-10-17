# SPDX-License-Identifier: LGPL-2.1-or-later
"""Part Design and Part buttons that still showed the English wiki text (2026-10-17).

    QT_SCALE_FACTOR=1.5 WT_OUT=<dir> [WT_ONLY=...] xvfb-run -a freecad tools/gifs/part_extra.py
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/part

Same recorder as part_rec.py / part_more.py (registers their scenes too). Results are made
with the objects the commands make (BOPTools, CompoundTools, PartDesign datums...).
Tree operations (Set Tip, Move...) show a small model-tree card next to the 3D view.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App  # noqa: E402
import FreeCADGui as Gui  # noqa: E402
import Part  # noqa: E402

import part_more as M  # noqa: E402  (registers the other scenes and starts the run timer)
from part_rec import (BASE, RESULT, TOOLC, Rec, circle_geo, color, hide, plate_body,  # noqa: E402
                      scene, sketch_on, top_face)

V = App.Vector
GREEN = (0.06, 0.73, 0.51)
ROSE = (0.88, 0.11, 0.28)


def vertex_near(obj, p):
    best = min(range(len(obj.Shape.Vertexes)), key=lambda i: (obj.Shape.Vertexes[i].Point - V(*p)).Length)
    return "Vertex%d" % (best + 1)


def edge_near(obj, p):
    best = min(range(len(obj.Shape.Edges)),
               key=lambda i: obj.Shape.Edges[i].distToShape(Part.Vertex(V(*p)))[0])
    return "Edge%d" % (best + 1)


def tree(r, lines, sel=None, title="Δέντρο μοντέλου"):
    ev = {"t": "panel", "title": title, "mono": False, "pos": "left", "lines": lines}
    if sel is not None:
        ev["sel"] = sel
    r.events.append(ev)


def no_tree(r):
    r.events.append({"t": "panel"})


def marker(r, kind, a, b=None):
    """A clearly visible copy of a datum (FreeCAD draws datum points and lines very thin)."""
    m = r.doc.addObject("Part::Feature", "Mark")
    if kind == "point":
        m.Shape = Part.makeSphere(1.6, a)
    elif kind == "line":
        d = b - a
        m.Shape = Part.makeCylinder(0.6, d.Length * 1.6, a - d * 0.3, d)
    else:                                        # axes of a coordinate system at a, length b
        parts = []
        for ax, col in ((V(1, 0, 0), 0), (V(0, 1, 0), 1), (V(0, 0, 1), 2)):
            parts.append(Part.makeCylinder(0.6, b, a, ax))
        m.Shape = Part.makeCompound(parts)
    color(m, ROSE)
    return m


def datum_style(o, rgb=RESULT):
    try:
        o.ViewObject.ShapeColor = rgb
        o.ViewObject.LineColor = rgb
        o.ViewObject.PointColor = rgb
        o.ViewObject.LineWidth = 4
        o.ViewObject.PointSize = 12
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Part Design datums: select where it goes, press, the datum appears there
# ---------------------------------------------------------------------------
@scene("PartDesign_Point")
def s_pd_point():
    r = Rec("PartDesign_Point", tool_first=True)
    body, pad = plate_body(r.doc)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    r.view(1.15)
    corner = (30, 20, 8)
    r.cap(2, "Κλικ σε κορυφή (ή ακμή, έδρα)")
    r.click(corner, pad, vertex_near(pad, corner))

    def go():
        p = body.newObject("PartDesign::Point", "DatumPoint")
        p.AttachmentSupport = [(pad, vertex_near(pad, corner))]
        p.MapMode = "Vertex"
        r.doc.recompute()
        datum_style(p, ROSE)
        marker(r, "point", V(*corner))
    r.apply(go, 3, "Βοηθητικό σημείο, δεμένο εκεί")
    r.save()


@scene("PartDesign_Line")
def s_pd_line():
    r = Rec("PartDesign_Line", tool_first=True)
    body, pad = plate_body(r.doc)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    r.view(1.15)
    a, b = (30, -20, 8), (30, 20, 8)
    r.cap(2, "Κλικ σε 2 κορυφές (ή σε ακμή)")
    r.click(a, pad, vertex_near(pad, a))
    r.click(b, pad, vertex_near(pad, b))

    def go():
        ln = body.newObject("PartDesign::Line", "DatumLine")
        ln.AttachmentSupport = [(pad, vertex_near(pad, a)), (pad, vertex_near(pad, b))]
        ln.MapMode = "TwoPointLine"
        r.doc.recompute()
        datum_style(ln, ROSE)
        marker(r, "line", V(*a), V(*b))
    r.apply(go, 3, "Βοηθητική γραμμή (π.χ. άξονας για Revolution)")
    r.save()


@scene("PartDesign_CoordinateSystem")
def s_pd_lcs():
    r = Rec("PartDesign_CoordinateSystem", tool_first=True)
    body, pad = plate_body(r.doc)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    r.view(1.2)
    r.cap(2, "Κλικ στην πάνω έδρα")
    r.click((0, 0, 8), pad, top_face(pad))

    def go():
        c = body.newObject("PartDesign::CoordinateSystem", "LCS")
        c.AttachmentSupport = [(pad, top_face(pad))]
        c.MapMode = "FlatFace"
        r.doc.recompute()
        try:
            c.ViewObject.Zoom = 2.0
        except Exception:
            pass
    r.apply(go, 3, "Τοπικοί άξονες X, Y, Z πάνω στην έδρα")
    r.save()


@scene("PartDesign_ShapeBinder")
def s_pd_shapebinder():
    r = Rec("PartDesign_ShapeBinder")
    box = r.doc.addObject("Part::Box", "Box")
    box.Length, box.Width, box.Height = 30, 20, 12
    box.Placement.Base = V(-50, -10, 0)
    color(box, TOOLC)
    body, pad = plate_body(r.doc)
    Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
    r.view(1.3)
    r.cap(1, "Κλικ σε έδρα ΕΞΩ από το σώμα")
    r.click((-35, 0, 12), box, top_face(box))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        s = body.newObject("PartDesign::ShapeBinder", "ShapeBinder")
        s.Support = [(box, [top_face(box)])]
        r.doc.recompute()
        color(s, GREEN)
    r.apply(go, 3, "Αντίγραφο μέσα στο σώμα: χρησιμοποιείται χωρίς λάθη")
    r.save()


def gear_like(name, make, panel_lines, text):
    @scene(name)
    def _s():
        r = Rec(name, tool_first=True)
        body = r.doc.addObject("PartDesign::Body", "Body")
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
        g = make()
        r.doc.recompute()
        r.view(1.0)
        r.v.viewTop()
        r.v.fitAll()                      # frame the profile while it is shown, then hide it
        cam = r.v.getCameraNode()
        cam.height.setValue(cam.height.getValue() * 1.25)
        g.ViewObject.Visibility = False
        r.events = [e for e in r.events if e["t"] != "img"]
        r.img()
        r.cap(1, "Πάτα το κουμπί")
        r.press()
        r.events.append({"t": "panel", "title": "Παράμετροι", "mono": False, "lines": panel_lines})
        r.cap(2, "Γράψε τις τιμές, OK")
        r.hold(1400)
        r.events.append({"t": "panel"})

        def go():
            g.ViewObject.Visibility = True
            g.ViewObject.LineColor = (0.96, 0.62, 0.04)
            g.ViewObject.LineWidth = 4
        r.apply(go, 3, text, 2400)
        r.save()
    return _s


def _gear():
    import InvoluteGearFeature
    g = InvoluteGearFeature.makeInvoluteGear("InvoluteGear")
    g.NumberOfTeeth = 20
    return g


def _sprocket():
    import SprocketFeature
    s = SprocketFeature.makeSprocket("Sprocket")
    s.NumberOfTeeth = 18
    return s


gear_like("PartDesign_InvoluteGear", _gear, ["Δόντια: 20", "Modulus: 2.5 mm", "Γωνία πίεσης: 20°"],
          "Προφίλ γραναζιού: μετά Pad για πάχος")
gear_like("PartDesign_Sprocket", _sprocket, ["Δόντια: 18", "Αλυσίδα: ANSI 25 / ISO 606"],
          "Προφίλ γραναζιού αλυσίδας: μετά Pad")


@scene("PartDesign_WizardShaft")
def s_shaft():
    r = Rec("PartDesign_WizardShaft", tool_first=True)
    r.doc.addObject("PartDesign::Body", "Body")
    r.view(1.0)
    r.events.append({"t": "panel", "title": "Άξονας: τμήματα", "mono": True,
                     "lines": ["Μήκος  Διάμετρος", "  40       20", "  30       30", "  20       16"]})
    r.cap(2, "Γράψε μήκος και διάμετρο κάθε τμήματος")
    r.hold(1600)
    r.events.append({"t": "panel"})

    def go():
        z = 0
        for i, (length, d) in enumerate(((40, 20), (30, 30), (20, 16))):
            c = r.doc.addObject("Part::Cylinder", "Seg%d" % i)
            c.Radius, c.Height = d / 2.0, length
            c.Placement = App.Placement(V(z, 0, 0), App.Rotation(V(0, 1, 0), 90))
            color(c, RESULT)
            z += length
        r.doc.recompute()
        r.v.fitAll()
        cam = r.v.getCameraNode()
        cam.height.setValue(cam.height.getValue() * 1.4)
    r.apply(go, 3, "Ο άξονας χτίζεται από τον πίνακα", 2400)
    r.save()


@scene("PartDesign_MoveTip")
def s_tip():
    r = Rec("PartDesign_MoveTip")
    body, pocket = plate_body(r.doc, with_hole=(0, 0, 8))
    pad = r.doc.getObject("Pad")
    r.view(1.3)
    tree(r, ["Body", "  Pad", "  Pocket  ← άκρη (Tip)"])
    r.cap(1, "Δεξί κλικ στο Pad στο δέντρο")
    r.events.append({"t": "pick", "row": 1})
    r.cap(2, "«Set Tip»")
    r.hold(900)

    def go():
        body.Tip = pad
        r.doc.recompute()
        pad.ViewObject.Visibility = True
        pocket.ViewObject.Visibility = False
        color(body, BASE)
        tree(r, ["Body", "  Pad  ← άκρη (Tip)", "  Pocket (κρυμμένο)"], sel=1)
    r.apply(go, 3, "Το σώμα «σταματά» στο Pad", 2400)
    r.save()


@scene("PartDesign_MoveFeatureInTree")
def s_move_in_tree():
    r = Rec("PartDesign_MoveFeatureInTree")
    body, pocket = plate_body(r.doc, with_hole=(0, 0, 8))
    r.view(1.3)
    tree(r, ["Body", "  Pad", "  Fillet", "  Pocket"])
    r.cap(1, "Επίλεξε το Pocket, δεξί κλικ")
    r.events.append({"t": "pick", "row": 3})
    r.cap(2, "«Move Feature After…» → Pad → OK")
    r.hold(1000)
    r.apply(lambda: tree(r, ["Body", "  Pad", "  Pocket", "  Fillet"], sel=2), 3,
            "Νέα σειρά: το Pocket γίνεται πριν από το Fillet", 2400)
    r.save()


@scene("PartDesign_MoveFeature")
def s_move_feature():
    r = Rec("PartDesign_MoveFeature")
    body, pocket = plate_body(r.doc, with_hole=(0, 0, 8))
    r.view(1.3)
    tree(r, ["Body", "  Pad", "  Pocket", "Body001", "  Pad001"])
    r.cap(1, "Δεξί κλικ στο Pocket")
    r.events.append({"t": "pick", "row": 2})
    r.cap(2, "«Move Object To…» → Body001 → OK")
    r.hold(1000)
    r.apply(lambda: tree(r, ["Body", "  Pad", "Body001", "  Pad001", "  Pocket"], sel=4), 3,
            "Το Pocket πήγε στο άλλο σώμα (μετά την άκρη του)", 2400)
    r.save()


@scene("PartDesign_DuplicateSelection")
def s_duplicate():
    r = Rec("PartDesign_DuplicateSelection")
    body, pocket = plate_body(r.doc, with_hole=(-12, 0, 6))
    r.view(1.3)
    tree(r, ["Body", "  Pad", "  Pocket"])
    r.cap(1, "Επίλεξε το Pocket")
    r.events.append({"t": "pick", "row": 2})
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        hs = sketch_on(body, 0, circle_geo(12, 0, 6))
        hs.AttachmentOffset = App.Placement(V(0, 0, 8), App.Rotation())
        p2 = body.newObject("PartDesign::Pocket", "Pocket001")
        p2.Profile, p2.Length = hs, 20
        hs.Visibility = False
        r.doc.recompute()
        color(body, BASE)
        tree(r, ["Body", "  Pad", "  Pocket", "  Pocket001  ← αντίγραφο"], sel=3)
    r.apply(go, 3, "Αντίγραφο στο σώμα (εδώ μετακινημένο)", 2400)
    r.save()


# ---------------------------------------------------------------------------
# Part: split, join, compound, copies
# ---------------------------------------------------------------------------
def two(r, kind="box"):
    a = r.doc.addObject("Part::Box", "Box")
    a.Length, a.Width, a.Height = 30, 30, 20
    if kind == "sphere":
        b = r.doc.addObject("Part::Sphere", "Sphere")
        b.Radius = 14
        b.Placement.Base = V(30, 15, 10)
    else:
        b = r.doc.addObject("Part::Box", "Box001")
        b.Length, b.Width, b.Height = 30, 30, 20
        b.Placement.Base = V(15, 10, 8)
    color(a, BASE)
    color(b, TOOLC)
    return a, b


def pieces(r, shape, gap=12.0, colors=(BASE, TOOLC, RESULT, GREEN)):
    """Show the solids of a result a little apart, each in its own colour (as if exploded)."""
    sols = shape.Solids
    c = shape.BoundBox.Center
    for i, s in enumerate(sols):
        d = s.BoundBox.Center - c
        d = V(d.x, d.y, d.z)
        if d.Length > 1e-6:
            d.normalize()
        p = r.doc.addObject("Part::Feature", "Piece%d" % i)
        p.Shape = s.translated(d * gap)
        color(p, colors[i % len(colors)])
    return len(sols)


def split_scene(name, kind, make, text):
    @scene(name)
    def _s():
        r = Rec(name)
        a, b = two(r, kind)
        r.view(1.4)
        r.cap(1, "Επίλεξε τα στερεά (Ctrl+κλικ)")
        r.click((5, 0, 20), a)
        r.click((40, 20, 28) if kind == "box" else (30, 15, 24), b)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            res = make(r, a, b)
            r.doc.recompute()
            hide(a, b)
            shape = res.Shape
            res.ViewObject.Visibility = False
            pieces(r, shape)
        r.apply(go, 3, text, 2600)
        r.save()
    return _s


def _frag(r, a, b):
    import BOPTools.SplitFeatures as SF
    o = SF.makeBooleanFragments("BooleanFragments")
    o.Objects = [a, b]
    return o


def _xor(r, a, b):
    import BOPTools.SplitFeatures as SF
    o = SF.makeXOR("XOR")
    o.Objects = [a, b]
    return o


split_scene("Part_BooleanFragments", "sphere", _frag, "Όλα τα κομμάτια χωριστά (εδώ ανοιγμένα)")
split_scene("Part_XOR", "box", _xor, "Φεύγει μόνο το κοινό κομμάτι")


def slice_scene(name, explode, text):
    @scene(name)
    def _s():
        r = Rec(name)
        a = r.doc.addObject("Part::Box", "Box")
        a.Length, a.Width, a.Height = 40, 30, 20
        color(a, BASE)
        pl = r.doc.addObject("Part::Plane", "Plane")
        pl.Length, pl.Width = 60, 50
        pl.Placement = App.Placement(V(20, -10, -15), App.Rotation(V(0, 1, 0), -90))
        color(pl, TOOLC, 40)
        r.view(1.4)
        r.cap(1, "Κλικ στο στερεό, Ctrl+κλικ στο «μαχαίρι»")
        r.click((5, 0, 20), a)
        r.click((20, 15, 25), pl)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            import BOPTools.SplitFeatures as SF
            s = SF.makeSlice("Slice")
            s.Base, s.Tools, s.Mode = a, [pl], "Split"
            r.doc.recompute()
            hide(a, pl)
            shape = s.Shape
            s.ViewObject.Visibility = False
            pieces(r, shape, 10 if explode else 4)
        r.apply(go, 3, text, 2600)
        r.save()
    return _s


slice_scene("Part_Slice", False, "Κόπηκε σε κομμάτια, μέσα σε ένα αντικείμενο")
slice_scene("Part_SliceApart", True, "Κόπηκε σε ξεχωριστά αντικείμενα")


def pipes(r):
    def tube(name, ro, ri, h):
        t = r.doc.addObject("Part::Feature", name)
        t.Shape = Part.makeCylinder(ro, h).cut(Part.makeCylinder(ri, h))
        return t
    a = tube("Tube", 10, 8, 60)
    a.Placement = App.Placement(V(-30, 0, 0), App.Rotation(V(0, 1, 0), 90))
    b = tube("Tube001", 7, 5.5, 35)
    color(a, BASE)
    color(b, TOOLC)
    return a, b


def join_scene(name, make, text):
    @scene(name)
    def _s():
        r = Rec(name)
        a, b = pipes(r)
        r.doc.recompute()
        r.view(1.3)
        r.cap(1, "Κλικ στον 1ο σωλήνα, Ctrl+κλικ στον 2ο")
        r.click((-20, 0, 10), a)
        r.click((0, 7, 30), b)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            o = make(a, b)
            r.doc.recompute()
            hide(a, b)
            color(o, RESULT, 0)
            cut = r.doc.addObject("Part::Feature", "Half")
            cut.Shape = o.Shape.cut(Part.makeBox(80, 40, 80, V(-40, -40, -20)))   # half, to see inside
            o.ViewObject.Visibility = False
            color(cut, RESULT)
        r.apply(go, 3, text, 2600)
        r.save()
    return _s


def _connect(a, b):
    import BOPTools.JoinFeatures as JF
    o = JF.makeConnect("Connect")
    o.Objects = [a, b]
    return o


def _embed(a, b):
    import BOPTools.JoinFeatures as JF
    o = JF.makeEmbed("Embed")
    o.Base, o.Tool = a, b
    return o


def _cutout(a, b):
    import BOPTools.JoinFeatures as JF
    o = JF.makeCutout("Cutout")
    o.Base, o.Tool = a, b
    return o


join_scene("Part_JoinConnect", _connect, "Ένωση: τα εσωτερικά επικοινωνούν (μισό, για να φαίνεται)")
join_scene("Part_JoinEmbed", _embed, "Ο 2ος μπήκε μέσα στον 1ο (μισό, για να φαίνεται)")
join_scene("Part_JoinCutout", _cutout, "Τρύπα στον 1ο για να περάσει ο 2ος (μισό)")


@scene("Part_CompoundFilter")
def s_cfilter():
    r = Rec("Part_CompoundFilter")
    a, b = two(r, "sphere")
    import BOPTools.SplitFeatures as SF
    f = SF.makeBooleanFragments("BooleanFragments")
    f.Objects = [a, b]
    r.doc.recompute()
    hide(a, b)
    color(f, BASE)
    r.view(1.4)
    r.cap(1, "Κλικ στο σύνθετο αντικείμενο")
    r.click((5, 0, 20), f)
    r.cap(2, "Πάτα το κουμπί · Items = 0")
    r.press()

    def go():
        import CompoundTools.CompoundFilter as CF
        c = CF.makeCompoundFilter("CompoundFilter")
        c.Base = f
        c.FilterType = "specific items"
        c.items = "0"
        r.doc.recompute()
        f.ViewObject.Visibility = False
        color(c, RESULT)
    r.apply(go, 3, "Κράτησε μόνο το κομμάτι που διάλεξες", 2400)
    r.save()


@scene("Part_ExplodeCompound")
def s_explode():
    r = Rec("Part_ExplodeCompound")
    a, b = two(r, "sphere")
    import BOPTools.SplitFeatures as SF
    f = SF.makeBooleanFragments("BooleanFragments")
    f.Objects = [a, b]
    r.doc.recompute()
    hide(a, b)
    color(f, BASE)
    r.view(1.4)
    r.cap(1, "Κλικ στο σύνθετο αντικείμενο")
    r.click((5, 0, 20), f)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        shape = f.Shape
        f.ViewObject.Visibility = False
        pieces(r, shape, 10)
    r.apply(go, 3, "Κάθε κομμάτι γίνεται χωριστό αντικείμενο", 2400)
    r.save()


def copy_scene(name, text, transform=None, refine=False, solid=False):
    @scene(name)
    def _s():
        r = Rec(name)
        if refine:
            a = r.doc.addObject("Part::Feature", "Fused")
            b1 = Part.makeBox(20, 30, 15)
            b2 = Part.makeBox(20, 30, 15, V(20, 0, 0))
            a.Shape = b1.fuse(b2)
            a.ViewObject.LineWidth = 3
        else:
            a = r.doc.addObject("Part::Box", "Box")
            a.Length, a.Width, a.Height = 30, 20, 15
        color(a, BASE)
        r.doc.recompute()
        r.view(1.6 if not refine else 1.3)
        r.cap(1, "Κλικ στο αντικείμενο")
        r.click((10, 0, 15), a)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            c = r.doc.addObject("Part::Feature", name.split("_")[1])
            c.Shape = a.Shape.removeSplitter() if refine else a.Shape.copy()
            if transform:
                c.Placement.Base = V(*transform)
                M.refit(r, 1.25)
            else:
                a.ViewObject.Visibility = False
            color(c, RESULT)
            c.ViewObject.LineWidth = 3
        r.apply(go, 3, text, 2400)
        r.save()
    return _s


copy_scene("Part_SimpleCopy", "Απλό αντίγραφο (χωρίς ιστορικό), εδώ μετακινημένο", (40, 0, 0))
copy_scene("Part_TransformedCopy", "Αντίγραφο στη θέση που φαίνεται (και μέσα σε ομάδες)", (40, 0, 0))
copy_scene("Part_RefineShape", "Έφυγαν οι περιττές ακμές στη μέση", refine=True)


@scene("Part_ElementCopy")
def s_elcopy():
    r = Rec("Part_ElementCopy")
    a = r.doc.addObject("Part::Box", "Box")
    a.Length, a.Width, a.Height = 30, 20, 15
    color(a, BASE)
    r.view(1.6)
    r.cap(1, "Κλικ σε έδρα (ή ακμή, κορυφή)")
    r.click((15, 10, 15), a, top_face(a))
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        c = r.doc.addObject("Part::Feature", "Face")
        c.Shape = a.Shape.getElement(top_face(a)).copy()
        c.Placement.Base = V(0, 0, 14)
        color(c, RESULT)
    r.apply(go, 3, "Αντίγραφο μόνο της έδρας (εδώ σηκωμένο)", 2400)
    r.save()


@scene("Part_ReverseShape")
def s_reverse():
    r = Rec("Part_ReverseShape")
    a = r.doc.addObject("Part::Box", "Box")
    a.Length, a.Width, a.Height = 30, 20, 15
    color(a, BASE)
    r.view(1.6)
    r.cap(1, "Κλικ στο αντικείμενο")
    r.click((10, 0, 15), a)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        c = r.doc.addObject("Part::Feature", "Reversed")
        s = a.Shape.copy()
        s.reverse()
        c.Shape = s
        a.ViewObject.Visibility = False
        color(c, ROSE)
    r.apply(go, 3, "Αντίγραφο με γυρισμένες τις έδρες (μέσα-έξω)", 2400)
    r.save()


@scene("Part_MakeSolid")
def s_makesolid():
    r = Rec("Part_MakeSolid")
    a = r.doc.addObject("Part::Feature", "Shell")
    a.Shape = Part.makeBox(30, 20, 15).Shells[0]
    color(a, BASE, 50)
    r.view(1.6)
    r.cap(1, "Κλικ στο κέλυφος (π.χ. από mesh)")
    r.click((10, 0, 15), a)
    r.cap(2, "Πάτα το κουμπί")
    r.press()

    def go():
        c = r.doc.addObject("Part::Feature", "Solid")
        c.Shape = Part.Solid(a.Shape)
        a.ViewObject.Visibility = False
        color(c, RESULT)
    r.apply(go, 3, "Έγινε στερεό: δέχεται τρύπες, Pad, CAM", 2400)
    r.save()


@scene("Part_PointsFromMesh")
def s_points():
    r = Rec("Part_PointsFromMesh")
    a = r.doc.addObject("Part::Box", "Box")
    a.Length, a.Width, a.Height = 30, 20, 15
    color(a, BASE)
    r.view(1.6)
    r.cap(1, "Κλικ στο αντικείμενο")
    r.click((10, 0, 15), a)
    r.cap(2, "Πάτα το κουμπί · απόσταση σημείων")
    r.press()

    def go():
        pts = []
        for e in a.Shape.Edges:
            pts += e.discretize(Distance=3.0)
        c = r.doc.addObject("Part::Feature", "Points")
        c.Shape = Part.makeCompound([Part.Vertex(p) for p in pts])
        a.ViewObject.Visibility = False
        c.ViewObject.PointColor = ROSE
        c.ViewObject.PointSize = 6
    r.apply(go, 3, "Σημεία πάνω στο σχήμα, για σκαριφήματα και γραμμές", 2400)
    r.save()


# ---------------------------------------------------------------------------
# Part datums and attachment
# ---------------------------------------------------------------------------
def part_datum(name, typ, mode, sub_fn, click_at, text):
    @scene(name)
    def _s():
        r = Rec(name)
        a = r.doc.addObject("Part::Box", "Box")
        a.Length, a.Width, a.Height = 40, 30, 15
        color(a, BASE)
        r.doc.recompute()
        r.view(1.5)
        r.cap(1, "Κλικ εκεί που θα δεθεί")
        subs = sub_fn(a)
        for p, s in zip(click_at, subs):
            r.click(p, a, s)
        r.cap(2, "Πάτα το κουμπί")
        r.press()

        def go():
            d = r.doc.addObject(typ, "Datum")
            d.AttachmentSupport = [(a, s) for s in subs]
            d.MapMode = mode
            r.doc.recompute()
            datum_style(d, ROSE)
            pts = [a.Shape.getElement(s).Vertexes[0].Point for s in subs if s.startswith("Vertex")]
            if typ.endswith("Point"):
                marker(r, "point", pts[0])
            elif typ.endswith("Line"):
                marker(r, "line", pts[0], pts[1])
            elif "Coordinate" in typ:
                marker(r, "axes", V(20, 15, 15), 14)
            try:
                d.ViewObject.Zoom = 2.0
            except Exception:
                pass
        r.apply(go, 3, text, 2400)
        r.save()
    return _s


part_datum("Part_DatumPoint", "Part::DatumPoint", "Vertex", lambda a: [vertex_near(a, (40, 30, 15))],
           [(40, 30, 15)], "Βοηθητικό σημείο, ακολουθεί το αντικείμενο")
part_datum("Part_DatumLine", "Part::DatumLine", "TwoPointLine",
           lambda a: [vertex_near(a, (40, 0, 15)), vertex_near(a, (40, 30, 15))],
           [(40, 0, 15), (40, 30, 15)], "Βοηθητική γραμμή ανάμεσα στις 2 κορυφές")
part_datum("Part_DatumPlane", "Part::DatumPlane", "FlatFace", lambda a: [top_face(a)],
           [(20, 15, 15)], "Βοηθητικό επίπεδο πάνω στην έδρα")
part_datum("Part_CoordinateSystem", "Part::LocalCoordinateSystem", "FlatFace", lambda a: [top_face(a)],
           [(20, 15, 15)], "Τοπικοί άξονες πάνω στην έδρα")


@scene("Part_EditAttachment")
def s_attach():
    r = Rec("Part_EditAttachment")
    a = r.doc.addObject("Part::Box", "Box")
    a.Length, a.Width, a.Height = 40, 30, 15
    b = r.doc.addObject("Part::Cylinder", "Cylinder")
    b.Radius, b.Height = 5, 12
    b.Placement.Base = V(60, 15, 0)
    color(a, BASE)
    color(b, TOOLC)
    r.view(1.4)
    r.cap(1, "Κλικ στο αντικείμενο που θα δέσεις")
    r.click((60, 20, 12), b)
    r.cap(2, "Πάτα το κουμπί · κλικ στην έδρα-στήριγμα")
    r.press()
    r.click((20, 15, 15), a, top_face(a))

    def go():
        b.AttachmentSupport = [(a, top_face(a))]
        b.MapMode = "FlatFace"
        r.doc.recompute()
    r.apply(go, 3, "Δέθηκε στην έδρα: πάει όπου πάει το κουτί", 2400)
    r.save()


@scene("Part_SectionCut")
def s_sectioncut():
    r = Rec("Part_SectionCut", tool_first=True)
    a = r.doc.addObject("Part::Feature", "Part")
    a.Shape = Part.makeBox(40, 30, 20).cut(Part.makeCylinder(8, 20, V(20, 15, 0)))
    color(a, BASE)
    r.view(1.4)
    r.events.append({"t": "panel", "title": "Τομή", "mono": False, "lines": ["X ✓  θέση 20 mm", "Y", "Z"]})
    r.cap(2, "Διάλεξε άξονα και θέση")
    r.hold(1200)
    r.events.append({"t": "panel"})

    def go():
        c = r.doc.addObject("Part::Feature", "SectionCut")
        c.Shape = a.Shape.cut(Part.makeBox(30, 40, 30, V(20, -5, -5)))
        a.ViewObject.Visibility = False
        color(c, RESULT)
    r.apply(go, 3, "Μόνιμη τομή: βλέπεις μέσα (το αρχικό δεν αλλάζει)", 2400)
    r.save()


def selection_scene(name, sub_kind, text):
    @scene(name)
    def _s():
        r = Rec(name, tool_first=True)
        a = r.doc.addObject("Part::Box", "Box")
        a.Length, a.Width, a.Height = 40, 30, 15
        color(a, BASE)
        r.view(1.5)
        p = (40, 15, 15)
        sub = {"Vertex": vertex_near(a, (40, 30, 15)), "Edge": edge_near(a, p), "Face": top_face(a)}[sub_kind]
        at = {"Vertex": (40, 30, 15), "Edge": p, "Face": (20, 15, 15)}[sub_kind]
        r.cap(2, "Κλικ: πιάνει μόνο αυτό το είδος")
        r.click(at, a, sub)
        r.cap(3, text)
        r.hold(2000)
        r.save()
    return _s


selection_scene("Part_VertexSelection", "Vertex", "Επιλέγονται μόνο κορυφές")
selection_scene("Part_EdgeSelection", "Edge", "Επιλέγονται μόνο ακμές")
selection_scene("Part_FaceSelection", "Face", "Επιλέγονται μόνο έδρες")

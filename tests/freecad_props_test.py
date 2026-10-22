# SPDX-License-Identifier: LGPL-2.1-or-later
"""Property view help in a REAL FreeCAD: rest the mouse on rows of the Data and View tabs.

    WT_OUT=/tmp/wt xvfb-run -a freecad tests/freecad_props_test.py   (WikiTips installed in Mod)

For a Part box and a Part Design additive box: every row that has Greek help gets a popup with
that help (a 'Module::Type:Name' entry wins over 'Name'), FreeCAD's own English tooltip is hidden,
and moving away closes the popup. Results: $WT_OUT/result.txt (+ prop_*.png).
"""
import faulthandler
import os
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("WT_OUT", os.path.join(os.path.expanduser("~"), "wikitips-test"))
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, "result.txt"), "w", encoding="utf-8")
faulthandler.enable(open(os.path.join(OUT, "crash.txt"), "w"), all_threads=True)
fails = []


def P(*a):
    log.write(" ".join(str(x) for x in a) + "\n")
    log.flush()


def check(ok, what):
    P("%s %s" % ("ok  " if ok else "FAIL", what))
    if not ok:
        fails.append(what)


def pump(ms):
    t = QtCore.QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.01)


def editor(view):
    for t in Gui.getMainWindow().findChildren(QtWidgets.QTreeView):
        if t.metaObject().className().startswith("Gui::PropertyEditor") and \
                (("View" in t.objectName()) == view):
            return t
    return None


def rows(tree):
    """(property name, model index of column 0) for every property row."""
    m, out = tree.model(), []

    def walk(par):
        for r in range(m.rowCount(par)):
            ix = m.index(r, 0, par)
            tip = m.data(ix, 3) or ""
            if "Name: " in tip:
                out.append((tip.split("Name: ", 1)[1].split("\n", 1)[0], ix))
            else:
                walk(ix)
    walk(QtCore.QModelIndex())
    return out


def show_tab(tree):
    child, p = tree, tree.parentWidget()
    while p is not None:
        if isinstance(p, QtWidgets.QStackedWidget) and isinstance(p.parentWidget(), QtWidgets.QTabWidget):
            p.parentWidget().setCurrentWidget(child)
        child, p = p, p.parentWidget()


def hover_rows(wikitips, obj, view, want_overrides):
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(obj)
    pump(800)
    tree = editor(view)
    show_tab(tree)
    tree.expandAll()
    pump(300)
    help_rows = [(n, ix) for n, ix in rows(tree) if wikitips.property_entry(n, view)]
    check(help_rows, "%s %s tab: rows with Greek help found (%s)"
          % (obj.TypeId, "View" if view else "Data", [n for n, _ in help_rows]))
    for name, ix in help_rows:
        tree.scrollTo(ix)
        pump(100)
        r = tree.visualRect(ix)
        QtGui.QCursor.setPos(tree.viewport().mapToGlobal(r.center()))
        pump(wikitips.REST_MS + 600)
        pop = wikitips._FILTER.popup
        entry = wikitips.property_entry(name, view)
        ok = pop.isVisible() and pop.title.text() == entry["t"]
        check(ok, "%s: popup '%s'" % (name, pop.title.text() if pop.isVisible() else "none"))
        check(not QtWidgets.QToolTip.isVisible(), "%s: FreeCAD's English tooltip is hidden" % name)
        if pop.isVisible():
            pop.grab().save(os.path.join(OUT, "prop_%s_%s.png" % (obj.Name, name)))
        for key in want_overrides.get(name, []):
            check(entry is wikitips.properties().get(key), "%s: uses the entry '%s'" % (name, key))
    # away from the rows: the popup goes
    QtGui.QCursor.setPos(Gui.getMainWindow().mapToGlobal(QtCore.QPoint(800, 500)))
    pump(800)
    check(not wikitips._FILTER.popup.isVisible(), "popup closes when the mouse leaves the Property view")


def run():
    try:
        import wikitips
        P("WikiTips loaded:", wikitips._FILTER is not None, "properties:", len(wikitips.properties()))
        mw = Gui.getMainWindow()
        mw.resize(1600, 1000)
        Gui.activateWorkbench("PartDesignWorkbench")
        doc = App.newDocument("Props")
        box = doc.addObject("Part::Box", "Box")
        sph = doc.addObject("Part::Sphere", "Sphere")
        body = doc.addObject("PartDesign::Body", "Body")
        import Part
        sk = body.newObject("Sketcher::SketchObject", "Sketch")
        sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])   # XY plane
        sk.MapMode = "FlatFace"
        pts = [App.Vector(0, 0, 0), App.Vector(20, 0, 0), App.Vector(20, 10, 0), App.Vector(0, 10, 0)]
        for i in range(4):
            sk.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4]))
        pad = body.newObject("PartDesign::Pad", "Pad")
        pad.Profile = sk
        pad.Length = 5
        doc.recompute()
        Gui.SendMsgToActiveView("ViewFit")
        pump(1500)
        hover_rows(wikitips, box, False, {"Length": ["Part::Box:Length"]})
        hover_rows(wikitips, box, True, {})
        hover_rows(wikitips, sph, False, {"Angle1": ["Part::Sphere:Angle1"]})
        hover_rows(wikitips, pad, False, {"Length": ["PartDesign::Pad:Length"], "Type": ["Type"]})
        hover_rows(wikitips, sk, True, {})
        # CAM: Python objects whose names clash with Part's (Base, Direction, Length, Tool…)
        Gui.activateWorkbench("CAMWorkbench")
        pump(1000)
        from Path.Main import Job
        job = Job.Create("Job", [box])
        import Path.Op.Profile
        prof = Path.Op.Profile.Create("Profile", parentJob=job)
        doc.recompute()
        import Path.Dressup.Gui.LeadInOut as LIO
        lead = LIO.Create(prof)
        doc.recompute()
        tc = job.Tools.Group[0]
        bit = tc.Tool
        pump(500)
        hover_rows(wikitips, prof, False, {"Direction": ["Profile:Direction"], "Base": ["CAM:Base"],
                                           "Label": ["Label"]})
        hover_rows(wikitips, tc, False, {"Tool": ["Controller:Tool"]})
        hover_rows(wikitips, bit, False, {"Length": ["ToolBit:Length"], "Diameter": ["ToolBit:Diameter"]})
        hover_rows(wikitips, lead, False, {"Base": ["CAM:Base"]})
        # Draft: Python objects too (Length, Base, Closed… mean other things than in Part)
        Gui.activateWorkbench("DraftWorkbench")
        pump(1000)
        import Draft
        wire = Draft.make_wire([App.Vector(0, 0, 0), App.Vector(10, 0, 0), App.Vector(10, 10, 0)])
        rect = Draft.make_rectangle(10, 5)
        arr = Draft.make_ortho_array(sph, App.Vector(20, 0, 0), App.Vector(0, 20, 0), App.Vector(0, 0, 20), 2, 2, 1)
        dim = Draft.make_linear_dimension(App.Vector(0, 0, 0), App.Vector(10, 0, 0), App.Vector(5, 5, 0))
        doc.recompute()
        pump(500)
        hover_rows(wikitips, wire, False, {"Length": ["wire:Length"], "Closed": ["Draft:Closed"]})
        hover_rows(wikitips, rect, False, {"Height": ["rectangle:Height"], "MakeFace": ["Draft:MakeFace"]})
        hover_rows(wikitips, arr, False, {"Base": ["array:Base"]})
        hover_rows(wikitips, dim, True, {})
        # TechDraw: page, template, view of the box, dimension
        Gui.activateWorkbench("TechDrawWorkbench")
        pump(1000)
        page = doc.addObject("TechDraw::DrawPage", "Page")
        tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        tmpl.Template = App.getResourceDir() + "Mod/TechDraw/Templates/ISO/A4_Landscape_blank.svg"
        page.Template = tmpl
        tdv = doc.addObject("TechDraw::DrawViewPart", "View")
        page.addView(tdv)
        tdv.Source = [box]
        doc.recompute()
        tdd = doc.addObject("TechDraw::DrawViewDimension", "Dimension")
        tdd.Type = "DistanceX"
        tdd.References2D = [(tdv, "Edge0")]
        page.addView(tdd)
        doc.recompute()
        pump(800)
        hover_rows(wikitips, tdv, False, {"Scale": ["TechDraw:Scale"], "X": ["TechDraw:X"]})
        hover_rows(wikitips, page, False, {"Scale": ["TechDraw::DrawPage:Scale"]})
        hover_rows(wikitips, tdd, True, {})
        # every row of these objects has Greek help (App, Part, Part Design, Sketcher, CAM, Draft, TechDraw)
        for obj in (box, sph, pad, sk, job, job.Stock, prof, tc, bit, lead, wire, rect, arr, dim,
                    page, tmpl, tdv, tdd):
            for view in (False, True):
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(obj)
                pump(800)
                tree = editor(view)
                tree.expandAll()
                pump(200)
                missing = [n for n, _ in rows(tree) if not wikitips.property_entry(n, view)]
                check(not missing, "%s %s tab: every row has Greek help (missing %s)"
                      % (obj.TypeId, "View" if view else "Data", missing))
        mw.grab().save(os.path.join(OUT, "win_props.png"))
        P("RESULT:", "PASS" if not fails else "%d FAILURES" % len(fails))
    except Exception:
        P("EXCEPTION", traceback.format_exc())
        P("RESULT: EXCEPTION")
    finally:
        log.close()
        QtCore.QTimer.singleShot(200, lambda: os._exit(0))


QtCore.QTimer.singleShot(4000, run)

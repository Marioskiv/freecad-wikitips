# SPDX-License-Identifier: LGPL-2.1-or-later
"""CAM buttons that still showed the English wiki text (2026-10-17).

    QT_SCALE_FACTOR=1.5 HOME=<throw-away> FREECAD=<freecad> OUT=<dir> \\
        sh tools/gifs/cam_rec.sh <scene>      (with CAM_REC=tools/gifs/cam_extra.py)
    python3 tools/gifs/sketcher_gifs.py <dir> content/img/camcmd

Same recorder as cam_rec.py (it registers all its scenes too). The supplemental commands
(Comment, Stop, Fixture, Custom) only add lines to the G-code: the card shows those lines
next to the real linuxcnc output of a small job.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCADGui as Gui  # noqa: E402

import cam_rec as C  # noqa: E402  (registers the other scenes and starts the run timer)
from cam_rec import Rec, flat_at, op_scene, pocket_job, post_lines, scene  # noqa: E402


def gcode_card(name, title, extra_first, text, insert_at=3, extra_lines=()):
    @scene(name)
    def _s():
        r = Rec(name)
        pocket_job(r)
        r.view(1.25)
        r.tree_pick(caption="Κλικ στο Job (στο δέντρο)")
        r.cap(2, "Πάτα το κουμπί")
        r.press()
        r.panel_off()
        if extra_lines:
            r.cap(3, "Γράψε τι θες")
            r.panel(title, list(extra_lines), mono=True)
            r.hold(1500)
            r.panel_off()
        lines = post_lines(r, 8)
        lines = lines[:insert_at] + [extra_first + "   ←"] + lines[insert_at:]
        r.cap(4 if extra_lines else 3, text)
        r.panel("job.ngc  ·  linuxcnc", lines)
        r.hold(3200)
        r.save()
    return _s


gcode_card("CAM_Comment", "Σχόλιο", "(ΑΛΛΑΞΕ ΕΡΓΑΛΕΙΟ)", "Το σχόλιο μπαίνει στο G-code για τον χειριστή",
           extra_lines=["Comment: ΑΛΛΑΞΕ ΕΡΓΑΛΕΙΟ"])
gcode_card("CAM_Stop", "Stop", "M1", "M1: η μηχανή σταματά και περιμένει Start")
gcode_card("CAM_Fixture", "Fixture", "G54", "G54: ποιο μηδέν τεμαχίου θα χρησιμοποιηθεί",
           extra_lines=["Fixture: G54  (G54 … G59)"])
gcode_card("CAM_Custom", "Custom G-code", "M8", "Οι δικές σου γραμμές μπαίνουν όπως τις έγραψες",
           extra_lines=["M8      (ψυκτικό ON)", "G4 P2   (αναμονή 2 s)"])


@scene("CAM_MillFace")
def s_millface():
    def pick(r):
        f = r.face(C.top_face_pred)
        return {"clicks": [((50, 35, 15), f)], "base": [(r.model, (f,))]}
    op_scene("CAM_MillFace", "MillFace", pick, "Κλικ στην πάνω έδρα",
             "Φρεζάρει επίπεδα την πάνω επιφάνεια", show_stock=True)


@scene("CAM_Probe")
def s_probe():
    r = Rec("CAM_Probe")
    r.make_job()
    r.tc("probe.fctb", 1)                 # the probe needs its own tool controller
    r.view(1.25, press_first=True)
    o = r.op("Probe")
    try:
        o.PointCountX, o.PointCountY = 4, 3
    except Exception:
        pass
    r.doc.recompute()
    r.cap(2, "Πλέγμα σημείων πάνω στο ακατέργαστο")
    r.panel("Probe · G-code", r.gcode(o, 9))        # the real commands of the operation
    r.hold(3200)
    r.save()


@scene("CAM_ToolBitLibraryOpen")
def s_library():
    r = Rec("CAM_ToolBitLibraryOpen")
    r.make_job()
    r.view(1.25, press_first=True)
    r.cap(2, "Οι βιβλιοθήκες και τα κοπτικά τους")
    r.panel("Βιβλιοθήκη εργαλείων · Default", ["3.175mm Endmill", "5mm Endmill", "6mm Ball End",
                                               "6mm Bullnose", "60° V-Bit", "5mm Drill", "M8x1.25 Tap"],
            mono=False)
    r.hold(1800)
    r.cap(3, "Διπλό κλικ: αλλάζεις διάμετρο, δόντια, μήκος")
    r.panel("5mm Endmill", ["Διάμετρος: 5 mm", "Μήκος κοπής: 15 mm", "Δόντια: 2", "Υλικό: HSS"], mono=False)
    r.hold(2400)
    r.save()


@scene("CAM_ExportTemplate")
def s_template():
    r = Rec("CAM_ExportTemplate")
    pocket_job(r)
    r.view(1.25)
    r.tree_pick(caption="Κλικ στο Job (στο δέντρο)")
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.panel_off()
    r.cap(3, "Διάλεξε τι θα κρατήσει")
    r.panel("Export Template", ["✓ Post-processor", "✓ Ακατέργαστο (Stock)", "✓ Εργαλεία",
                                "✓ Ύψη και βάθη", "→ job_aluminio.json"], mono=False)
    r.hold(2000)
    r.cap(4, "Νέο Job: διάλεξε αυτό το πρότυπο")
    r.hold(1600)
    r.save()


@scene("CAM_ToolController")
def s_tc():
    r = Rec("CAM_ToolController")
    r.make_job()
    r.view(1.25)
    r.tree_pick(caption="Κλικ στο Job (στο δέντρο)")
    r.cap(2, "Πάτα το κουμπί, διάλεξε κοπτικό")
    r.press()
    r.panel_off()
    r.cap(3, "Νέος Tool Controller: κοπτικό + στροφές + πρόωση")
    r.panel("Job · Tools", ["TC: 5mm Endmill  (T1)", "TC: 6mm Ball End  (T2)  ←",
                            "   Στροφές: 18000", "   Πρόωση: 1000 mm/min"], mono=False)
    r.hold(2800)
    r.save()


@scene("CAM_Compound")
def s_compound():
    r = Rec("CAM_Compound")
    pocket_job(r)
    r.view(1.25)
    r.tree_pick(ops=["Operations", "      Pocket", "      Profile"], row=2,
                caption="Επίλεξε εργασίες (Ctrl+κλικ)")
    r.events.append({"t": "pick", "row": 3})
    r.cap(2, "Πάτα το κουμπί")
    r.press()
    r.panel_off()
    r.cap(3, "Μία ομάδα εργασιών που τρέχει μαζί")
    r.panel("Μοντέλο (δέντρο)", ["Job", "   Operations", "      Compound", "         Pocket",
                                 "         Profile"], mono=False, pos="left")
    r.hold(2600)
    r.save()

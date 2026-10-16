# WikiTips για το FreeCAD

Κράτα το ποντίκι πάνω σε ένα κουμπί της γραμμής εργαλείων και εμφανίζεται
παράθυρο με **εικόνα και σύντομη εξήγηση από το FreeCAD wiki**: τι κάνει η
εντολή, σε ποιο μενού βρίσκεται, τη συντόμευση και τα βασικά βήματα χρήσης.

- Δουλεύει χωρίς internet: όλα τα κείμενα και οι εικόνες είναι στο φάκελο `data`.
- Περίπου 1.290 εντολές (Sketcher, Part Design, Part, CAM, Std, Draft, TechDraw, FEM κ.ά.),
  οι 640 με εικόνα. Κείμενα από το wiki όπως ήταν στις 16/10/2026 (FreeCAD 1.1).
- Κουμπιά με βελάκι (π.χ. κύκλος/τόξο στο Sketcher): δείχνει την εντολή που φαίνεται εκείνη τη στιγμή.
- Ενεργοποίηση/απενεργοποίηση: κουμπί «WikiTips» στη γραμμή εργαλείων WikiTips.
- Εντολές χωρίς σελίδα στο wiki δείχνουν το κανονικό tooltip.

## Εγκατάσταση

1. Στο FreeCAD άνοιξε View → Panels → Python console και γράψε
   `print(App.getUserAppDataDir() + "Mod")` για να δεις πού είναι ο φάκελος `Mod`.
2. Αντέγραψε όλο αυτό το repository σε έναν φάκελο `Mod\WikiTips`
   (να υπάρχει `Mod\WikiTips\InitGui.py`).
3. Επανεκκίνηση του FreeCAD.

## Για προγραμματιστές

| Φάκελος | Περιεχόμενο |
|---|---|
| `InitGui.py`, `wikitips.py` | το addon (PySide, Qt5/Qt6) |
| `data/` | `commands.json` + σμικρυμένες εικόνες (παράγονται, μην τα αλλάζεις με το χέρι) |
| `tools/build_data.sh` | ξαναφτιάχνει το `data/` από το wiki (κατεβάζει ~2 GB) |
| `tests/run_popup_test.py` | δοκιμή χωρίς FreeCAD, με ψεύτικο παράθυρο (PySide6, offscreen) |
| `tests/freecad_gui_test.py` | δοκιμή μέσα σε πραγματικό FreeCAD (`xvfb-run -a freecad tests/freecad_gui_test.py`) |
| `docs/notes/` | σημειώσεις εργασίας και έρευνας (για τον Claude και για σένα) |

Δοκιμή:

```bash
pip install PySide6
QT_QPA_PLATFORM=offscreen python3 tests/run_popup_test.py tests/shim . tests/out
```

## Άδειες

- Κώδικας: LGPL-2.1-or-later (`LICENSE`).
- Κείμενα και εικόνες στο `data/`: από το FreeCAD wiki (https://wiki.freecad.org),
  μέσω https://github.com/Reqrefusion/FreeCAD-Documentation-html και
  https://github.com/FreeCAD/FreeCAD-documentation — άδεια CC-BY 3.0,
  © οι συντάκτες του FreeCAD wiki. Τα κείμενα έχουν συντομευτεί και οι εικόνες σμικρυνθεί.

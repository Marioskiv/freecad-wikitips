# Memory — read this before anything else

Short, durable facts for the next Claude session. Details live in the other notes; this file is the
"what must I not forget" list. Update it when a decision changes.

## Marios and how we work
- Answer in **Greek script**, simple words. He is not a programmer and does not know CAD/CAM well:
  explain *why*, not just *what*. He wants professional, carefully researched work.
- **Ask before** changing, copying or deleting any file, and before commit/push.
- **Workflow = Pull Requests** (decided 2026-10-16): every change goes on its own branch
  → PR → he reads it on GitHub and presses *Merge*. Never push to `main` directly.
- Repo: `Marioskiv/freecad-wikitips` (private). Created by Marios by hand on github.com because
  Claude's GitHub app cannot create repositories (403). Attach it with `add_repo` (push access).
- Scope: ONLY the WikiTips FreeCAD addon. His other projects (e.g. polar-cnc-converter) are separate.
- End of every session: update `docs/notes/` (session-log, status, findings) and this file.

## His setup
- Windows laptop, FreeCAD **26.3.0RC1** in `C:\Program Files\FreeCAD 26.3`, Python 3.13, Qt6.
  User Mod folder (to confirm with `print(App.getUserAppDataDir() + "Mod")`):
  probably `C:\Users\mario\AppData\Roaming\FreeCAD\v26-3\Mod` → addon goes in `Mod\WikiTips`.
- FreeCAD's Python has **no SSL** → no pip packages in the addon, ever.
- Uses Sketcher, Part Design, Part, CAM (post: linuxcnc), imports STEP from Fusion 360.

## What he wants from WikiTips (priority order, 2026-10-16)
1. **Animated GIFs** rather than still pictures ("GIF is better"); he also liked the static-diagram
   style. Greek captions inside the animation.
2. Help on the **unusual buttons** (Binders, Boolean, Clone, Datums, Compound/Explode, Section...).
3. Help **inside dialogs**: hover a field (CAM Depths/Heights, Step down, Stepover, Cut side,
   Pattern, stock to leave; Pad/Pocket options) → Greek explanation + small animation.
   CAM: Face, Pocket, Profile, Adaptive, Drilling, 3D Surface/Waterline.
4. Greek translations for Sketcher, Part Design, Part, CAM.
- Re-use existing material when the licence allows (FreeCAD wiki = CC-BY 3.0). Media from
  closed-source CAD/CAM (Fusion, SolidWorks...) is copyrighted → do NOT copy; make our own.
- Open question to ask him: which cutters (flat/ball/V-bit) and materials (wood/alu/plastic) he uses,
  so the examples match his work.

## How to test in a real FreeCAD from the cloud container
- github.com release downloads are blocked, **conda-forge is reachable**:
  get `micromamba` from `https://conda.anaconda.org/conda-forge/linux-64/micromamba-<ver>-0.tar.bz2`,
  then `micromamba create -p <dir>/fc -c conda-forge freecad=2026.09.16 python=3.13`
  (that build reports itself as **FreeCAD 26.3.0**, same as Marios). ~2.5 GB download.
- Install the addon in `$HOME/.local/share/FreeCAD/v26-3/Mod/WikiTips`, then
  `WT_OUT=<dir> xvfb-run -a <fc>/bin/freecad tests/freecad_gui_test.py` → `result.txt` must say PASS.
- Offline mock test: `QT_QPA_PLATFORM=offscreen <fc>/bin/python tests/run_popup_test.py tests/shim . <out>`
  (system PySide6 lacks libEGL; FreeCAD's own Python works).
- GIF prototypes: real FreeCAD scene → `ActiveView.saveImage()` frames → ffmpeg palette GIF (~70 KB),
  or Pillow-drawn diagrams with DejaVu fonts (Greek OK) (~200 KB). Prototype scripts are not in the
  repo yet (PR 2 will add the generator under `tools/`).

# Memory — read this before anything else

Short, durable facts for the next Claude session. Details live in the other notes; this file is the
"what must I not forget" list. Update it when a decision changes.

## Marios and how we work
- Answer in **Greek script**, simple words. He is not a programmer and does not know CAD/CAM well:
  explain *why*, not just *what*. He wants professional, carefully researched work.
- **Ask before** changing, copying or deleting any file, and before commit/push.
- **Workflow = Pull Requests** (decided 2026-10-16): every change goes on its own branch → PR.
  **Since 2026-10-16 Marios lets Claude merge the PRs into `main` himself** ("I don't know which
  to merge; you have my permission to put it on main"): merge only after the real-FreeCAD tests
  say ALL PASS, base every PR on `main`, merge in order. Still never push to `main` directly.

## Pending (do later, he asked to wait)
- CAM animations: **more colour contrast** (he likes the v4 look, but the stock/tool/paths need
  stronger contrast). Ideas: darker stock edge + darker tool, stronger path colour, darker labels.
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
- Re-use existing material when the licence allows (FreeCAD wiki = CC-BY 3.0). From other CAD/CAM
  (Fusion, SolidWorks, Onshape...) take only IDEAS of how they explain things and draw our own,
  in our own style (Marios, 2026-10-16: "ideas, not stealing, a slightly different style").
- Ideas adopted: Fusion-style per-field diagram with the active level in red; show the Fusion 360
  name of each CAM setting (he also uses Fusion); ⚠ warnings for beginner traps.
  Ideas for later: SolidWorks-style tooltip size setting (big+GIF / big / small); Onshape-style
  two stages (short line first, GIF after ~1.5 s).
- Style he liked: light background, wood-colour stock, blue-grey tool, red = the setting being
  explained, dark caption bar with a Greek sentence (tools/gifs/draw.py holds the palette).
  v2 palette (he asked "a bit more modern"): wood grain, metallic tools, soft shadows.
- The Claude app shows only the FIRST FRAME of a GIF: to show him animations, publish an HTML
  artifact with the GIFs embedded (gallery: https://claude.ai/artifact/UGYx8Sx1bjfUHiosRUoYjw).
- Accuracy: every help text needs a source in docs/notes/verification.md ("no errors" — Marios).
- Popup layout he liked (from MDJ Works screenshots): animation from the real app with cursor +
  click ring + numbered Greek step badge; then "what it does", "ΠΩΣ ΕΠΙΛΕΓΕΙΣ", "ΠΟΥ ΧΡΗΣΙΜΕΥΕΙ",
  💡 tip, shortcut badge. Implemented for commands in content/commands_el.json.
- PRs: base each PR on `main` (PR 2 once got merged into the PR 1 branch by mistake).
- He wants modern colours: palette v4 (draw.py) — NO wood-brown stock (he disliked it): light slate
  block, graphite tool with amber ring, indigo paths, rose = setting explained; light theme for the
  FreeCAD recordings (sketcher_rec.py THEME).
- FEWER WORDS (2026-10-16): "write less, let the mouse show the right way". Captions 2–5 words,
  popup = one sentence + the one trap (⚠) + "Χρήσιμο:" line. Sketcher GIFs start by clicking the
  real toolbar icon (tool-first), then the clicks; numbered step badges.
- Videos: YouTube is blocked here; ask him to upload the file (frames can then be extracted).
- Open question to ask him: which cutters (flat/ball/V-bit) and materials (wood/alu/plastic) he uses,
  so the examples match his work.

## Crash lesson (2026-10-16) — never forget
- Do NOT wrap short-lived widgets in Python: `mw.findChildren(QWidget)` over a CAM dialog, or event
  filters on dialog fields, left stale PySide wrappers and FreeCAD crashed when the dialog closed.
  Toolbar buttons only (children of QToolBar); dialog fields are found by polling
  `QApplication.widgetAt(cursor)` and the popup keeps only a screen rectangle.
- Opening/closing many CAM dialogs from one script crashes FreeCAD 26.3 even WITHOUT WikiTips
  (control run). Test one dialog per FreeCAD start: `tests/run_freecad_tests.sh`. Close dialogs
  like Cancel does: `Gui.Control.activeTaskDialog().reject()`.

## How to test in a real FreeCAD from the cloud container
- github.com release downloads are blocked, **conda-forge is reachable**:
  get `micromamba` from `https://conda.anaconda.org/conda-forge/linux-64/micromamba-<ver>-0.tar.bz2`,
  then `micromamba create -p <dir>/fc -c conda-forge freecad=2026.09.16 python=3.13`
  (that build reports itself as **FreeCAD 26.3.0**, same as Marios). ~2.5 GB download.
- Install the addon in `$HOME/.local/share/FreeCAD/v26-3/Mod/WikiTips` (copy wikitips.py, InitGui.py,
  package.xml, data, content, Resources), then
  `FREECAD=<fc>/bin/freecad OUT=<dir> sh tests/run_freecad_tests.sh` → must print ALL PASS.
- Offline mock test: `QT_QPA_PLATFORM=offscreen <fc>/bin/python tests/run_popup_test.py tests/shim . <out>`
  (system PySide6 lacks libEGL; FreeCAD's own Python works).
- GIF prototypes: real FreeCAD scene → `ActiveView.saveImage()` frames → ffmpeg palette GIF (~70 KB),
  or Pillow-drawn diagrams with DejaVu fonts (Greek OK). Generator for the CAM field GIFs:
  `python3 tools/gifs/cam_gifs.py content/img/cam [names...]` (needs Pillow + DejaVu, build time only).

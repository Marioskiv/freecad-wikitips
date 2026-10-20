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

## Error explainer wishes (2026-10-17)
- FreeCAD stays in English, but the error cards must be ONLY Greek (he asked 2026-10-17, after first
  wanting English + Greek). The English text appears only with the pref Mod/WikiTips ShowEnglish.
- "The more problems it solves the better": keep adding rules from REAL probed messages
  (tests/freecad_error_test.py lists them). He does NOT want a Greek search.

## What lives where (Marios, 2026-10-20) — read this
- **This repo = ONLY WikiTips**: hover help for FreeCAD's commands and the Greek error explanations.
  No tools inside. Open work: `pending.md`.
- **Knurl and "Σκαρίφημα σε κύλινδρο" (Wrap) LEFT WikiTips on 2026-10-20 (0.5.0)**: they are now
  "Knurling & Wrap" in `Marioskiv/polar-cnc-converter` (folder `cad/`, Part Design toolbar, MIT, notes in
  its `docs/notes/knurlwrap.md`). Do not bring them back here; WikiTips has no help or error rules for them.
- Everything for his XZC machine (web converter, Polar CNC addon, Knurling & Wrap) is in
  `polar-cnc-converter` (to be renamed); machine files in `cnc-manuals`; calibration in
  `linuxcnc-calibrations`; the cutter libraries will get their own repo. Never mix them.
- **No change without his clear "ναι"** (rule of 2026-10-20); only the notes may be updated freely.

## Durable facts (moved from "Pending" on 2026-10-20; open items are in pending.md)
- **Install through the Addon Manager (his question):** possible only if the repo is PUBLIC. Then:
  Addon Manager → ⚙ (Preferences) → Custom repositories → add
  `https://github.com/Marioskiv/freecad-wikitips`, branch `main` → WikiTips shows in the list,
  Install / Update like any addon (the manual copy in Mod must be removed first). A private repo
  cannot be used (no password support). Bump `package.xml` <version> on every release so the
  Addon Manager offers the update. Marios made the repo PUBLIC on 2026-10-17. Verified the same day
  in FreeCAD 26.3 (clean user folder): AddonInstaller with url + branch main downloads it into
  Mod/WikiTips, and after a restart the WikiTips toolbar loads (then with Knurl and Wrap; since 0.5.0
  they come with the polar-cnc-converter addon).
- **CAM tool library (2026-10-17; Marios asked 2026-10-20 for a SEPARATE repo for it, see pending.md):** Marios will buy YG-1 ALU-POWER carbide end mills (aluminium,
  heavy DIY machine, 1 and 2 flutes). Built from his catalog PDF (YG-1 "YE-AP25 EUROPE") and sent as
  a zip (not in this repo): 26 bits, E5E47 1F Ø2-12, E5E48 2F short Ø3-12, E5522 2F long Ø3-12,
  E5910 2F ball Ø6-12; Tools/Library/YG1_AluPower.fctl + Tools/Bit/*.fctb, loaded and checked in
  FreeCAD 26.3; Greek guide with the catalog's cutting data (aluminium, VDI 21-22) and DIY advice.
  Open: his spindle max RPM (feeds then = RPM x fz x flutes); trim the library to what he buys.
  26.3 facts: libraries import .fctl (bits from the sibling Bit folder), .fctb, YAML, Camotics
  JSON; LinuxCNC .tbl export only; NO Fusion 360 import (Better Tool Library addon did it,
  deprecated after 1.0.1). Feeds/speeds live in the Tool Controller, not in the bit.
  More libraries sent the same day (zips, not in this repo; all loaded and checked in 26.3):
  IZAR_Aluminio (85 bits: HSSE 4454 Autolock Ø2-20 = his own Ø5 is T5 / art. 44858, 4464, 4420,
  4410, 4411 from his IZAR_235.pdf p.241/242/245, plus carbide 9427/9429/9416/9417/9413/9414 from
  the Carbide Programme 2018); Stepcraft (3 single-flute bits converted from his Fusion .tools);
  Amana_Aluminio (the 34 "Aluminum Cutting" bits of Amana's Fusion library, inch → mm; Amana's file
  has 2 inconsistencies: 51470 flutes, 51408 cutting length). RobbJack: he said NOT to make it.
  A Fusion .tools file is a zip with tools.json (geometry DC/LCF/OAL/SFDM/NOF in the tool's unit,
  presets n / v_f / v_f_plunge); converting it to .fctb/.fctl is a few lines of Python.
  Clarkson: no catalog or library found; ask him for codes or a PDF.
- **CAM phase: DONE elsewhere.** The CAM addon he planned on 2026-10-17 (separate addon, his polar
  converter in FreeCAD CAM) was built in `polar-cnc-converter` (Polar CNC, 2.x, Oct 2026). Nothing of it
  belongs here.
- CAM animations: **more colour contrast** (he likes the v4 look, but the stock/tool/paths need
  stronger contrast). Ideas: darker stock edge + darker tool, stronger path colour, darker labels.
- Repo: `Marioskiv/freecad-wikitips` (public since 2026-10-17). Created by Marios by hand on github.com
  because Claude's GitHub app could not create repositories (403). Attach it with `add_repo` (push access).
- Scope: ONLY the WikiTips FreeCAD addon. His other projects (e.g. polar-cnc-converter) are separate.
- End of every session: update `docs/notes/` (session-log, status, findings, pending) and this file.

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

## Speed of the animations (2026-10-17)
- Marios: "a bit slower, but not too slow" → `draw.SLOWER = 1.3` multiplies every frame duration
  (all generators use draw.save_gif). Change only that number if he asks again.

## Recording lessons (all GIFs)
- ALWAYS record with QT_SCALE_FACTOR=1.5 and an xvfb screen of 2400x1600 (3x GIFs, 2026-10-17).
  Render with tools/gifs/sketcher_gifs.py (it detects the scale from the key frames).
- Check every new GIF on a contact sheet before using it; never show settings, checks or G-code
  that were not produced by FreeCAD itself (cards with invented content were removed).
- Commands inside drop-down groups have no QAction of their own: take the icon with
  Gui.getIcon(<pixmap name>) (done in all recorders).
- Click marks: sketcher_gifs.py draws an amber dot at every click until the next result (blend).
  Set "marks": false in events.json to disable; "cursor": false hides the mouse (pd_rec settings).
- Sketcher B-splines: turn off the curvature comb (Mod/Sketcher/General BSplineCombVisible) or the
  curve disappears under green hatching.
- Part Design settings: real recordings, one property change per frame (tools/gifs/pd_rec.py).
- Part Design primitives sit inside group commands: Gui.Command.get() returns None → take the icon
  with QIcon(":/icons/<name>.svg"). Subtractive primitives are not attached → move them with
  Placement. MultiTransform shows nothing unless body.Tip = it and the sub-transforms are hidden.
- Sketcher text geometry from Python: Sketcher.Constraint("Text", [geo, 0], text, font, False),
  then sketch.setTextAndFont(idx, text, font, False, False) (form from DrawSketchHandlerText.h).
- part_rec.py / sketcher_rec.py run a demo on import unless WT_NO_AUTORUN=1 is set.

## CAM recording lessons (2026-10-16, PR 7)
- Marios: "if 26.3 blocks you, use the stable 1.1". Not needed so far: everything worked in 26.3.
  Stay on 26.3 (his version) unless something really cannot be done there.
- 3D Surface / Waterline: `micromamba install -p <fc> -c conda-forge opencamlib` + the CAM
  preference EnableAdvancedOCLFeatures (CAM → Advanced → "Enable OCL dependent features").
  The "experimental features" flag is NOT needed for them (only for Planar/Rotary Surface).
- A Job with TWO tool controllers makes `Path.Op.X.Create()` open a modal "choose tool controller"
  dialog → the script hangs. Keep one TC per Job when scripting (cam_rec.py `tc()`).
- Profile with only the TOP face selected keeps Final Depth at the face height (cuts nothing);
  no selection = whole-model contour to the bottom. Ramp Entry refuses a zero HorizFeed.
- Use `faulthandler.dump_traceback_later` to see where a hung FreeCAD script waits.
- A selected path is drawn in the selection colour (green): clear the selection before a shot.
- Dressup GIFs show the original path light indigo ("πριν") and the dressed path rose ("μετά"),
  with a legend; rapids are light slate and the first rapid from the origin is hidden
  (CAM prefs DefaultRapidPathColor, HideFirstRapid).

## How to test in a real FreeCAD from the cloud container
- github.com release downloads are blocked, **conda-forge is reachable**:
  get `micromamba` from `https://conda.anaconda.org/conda-forge/linux-64/micromamba-<ver>-0.tar.bz2`,
  then `micromamba create -p <dir>/fc -c conda-forge freecad=2026.09.16 python=3.13`
  (that build reports itself as **FreeCAD 26.3.0**, same as Marios). ~2.5 GB download.
- Install the addon in `$HOME/.local/share/FreeCAD/v26-3/Mod/WikiTips` (copy wikitips.py, InitGui.py,
  package.xml, data, content, Resources), then
  `FREECAD=<fc>/bin/freecad OUT=<dir> sh tests/run_freecad_tests.sh` → must print ALL PASS.
  The suite includes the error explainer test (tests/freecad_error_test.py, run name "errors").
  Copy wikitips_errors.py too when installing (or symlink the whole repo as Mod/WikiTips).
- Offline mock test: `QT_QPA_PLATFORM=offscreen <fc>/bin/python tests/run_popup_test.py tests/shim . <out>`
  (system PySide6 lacks libEGL; FreeCAD's own Python works).
- GIF prototypes: real FreeCAD scene → `ActiveView.saveImage()` frames → ffmpeg palette GIF (~70 KB),
  or Pillow-drawn diagrams with DejaVu fonts (Greek OK). Generator for the CAM field GIFs:
  `python3 tools/gifs/cam_gifs.py content/img/cam [names...]` (needs Pillow + DejaVu, build time only).

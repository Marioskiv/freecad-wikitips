# Session log

## 2026-10-17: CAM dressups (PR 8)
- Marios: "more explanation for CAM, e.g. dressups, or better GIFs … check if you left something".
- Dressup command GIFs re-recorded: before (light indigo) vs after (rose) with a legend, quieter
  rapids, first rapid hidden. Found and fixed: the "before" path stayed selected (green).
- New: Greek help for every field of the dressup panels (47 entries) + 5 drawn GIFs
  (dogbone_style, tag_shape, lead_style, dragknife, boundary_inside). Test suite now opens six
  dressup panels (Dogbone opened with setEdit, the command itself does not open it): ALL PASS.
- Marios: "a bit slower, not too slow" → all GIFs regenerated 1.3× slower (draw.SLOWER).
- Audit: 128 toolbar commands of Sketcher / Part Design / Part still showed only the English
  wiki → next PR adds Greek for all of them.

## CAM toolbar commands (PR 7, 2026-10-16)
- Marios asked: "I want more for CAM: Inspect, SelectLoop, Helix, Adaptive, Slot, Engrave, Deburr,
  Vcarve, Pocket 3D, Surface, Axis Map … and all the others". Listed the real 26.3 CAM toolbars
  (Project Setup, Tool Commands, New Operations, Path Modification + dropdowns) → 38 commands.
- content/commands_el.json: Greek help for all of them (+ 3D Surface / Waterline, which appear only
  with OpenCamLib). Checked against the wiki or, where the wiki page is empty/wrong, the 26.3
  source (verification.md, new table). Found: wiki "CAM OperationCopy" redirects to the old linked
  "CAM Copy" — the 26.3 command makes an independent copy (source); CAM_MillFacing faces the
  stock top and takes no base geometry; Drilling ignores a selection made before the command.
- tools/gifs/cam_rec.py: records each command in a real FreeCAD 26.3 with the CAM Python API (real
  Job, real operations and dressups, real toolpaths; the cutter runs along the real path while the
  path grows). One scene per FreeCAD start (tools/gifs/cam_rec.sh), because many CAM objects in one
  session crash FreeCAD. Composer (sketcher_gifs.py) learned "panel" cards: real Inspect G-code,
  real linuxcnc post output (legacy linuxcnc post, filename "-", --no-show-editor), report/tool
  lists, and a small model tree where the cursor clicks the Job/operation.
- tools/gifs/cam_cmd_gifs.py: drawn GIFs for Surface, Waterline (no OpenCamLib here), Axis Map
  (4th axis), Z Correct (probe file).
- tests/check_content.py: every Greek entry has t/d and its picture.
- Installed OpenCamLib in the test FreeCAD → 3D Surface and Waterline recorded for real. Source
  check corrected the wiki: those buttons need OpenCamLib + "Enable OCL dependent features", not
  the experimental flag.
- Bug found and fixed in the addon: commands without a wiki page (CAM_MillFacing,
  CAM_OperationCopy) had no popup even with Greek help → `lookup()` now falls back to
  commands_el.json. Test POPUPS extended (MillFacing, OperationCopy, Helix, SelectLoop, dressups).
- Recording mistakes caught by looking at every GIF: top-face Profile (cut nothing), drag-knife on
  an already rounded contour (no corners), invisible tags/dogbones/lead-ins (now top/front close-ups),
  mirror outside the part, empty Boundary/Waterline/Ramp paths (fixed).
- Tests: tests/run_freecad_tests.sh ALL PASS, offline popup test OK, check_content OK.

## 2026-10-16 (Claude Code cloud session, second)
- Repo published: Marios created `Marioskiv/freecad-wikitips` (private) by hand; Claude pushed the
  v0.2.0 commit to `main`. Workflow agreed: PRs only.
- Installed FreeCAD 26.3.0 (conda-forge, Linux) in the cloud container and ran WikiTips in it for
  the first time in a real FreeCAD. Found: Python dropdown groups (Part offset/compound/join/split,
  CAM drilling/post/sim/engrave/dressup) and Undo/Redo showed no popup; long texts made popups up to
  690 px tall. Fixed on branch `fix/real-freecad-groups` (PR 1); added `tests/freecad_gui_test.py`
  (PASS) and `docs/notes/memory.md`.
- Researched GIF sources (see addon-research.md); made two prototypes Marios liked: PartDesign Pad
  (scripted FreeCAD frames) and CAM heights/depths (drawn diagram with Greek captions).
- Marios asked for: GIFs (preferred), help for unusual buttons, help on every dialog field (CAM
  depths/heights/stepover..., 3D ops), careful study, re-use of licensed material.
- PR 2 (branch feature/cam-field-help): Greek help + 25 animations for CAM dialog fields
  (heights/depths, step over, patterns, cut mode, cut side, compensation, passes, stock to leave,
  facing extensions, drilling peck/dwell/R/extra offset, adaptive helix, retract threshold).
  Found and fixed a crash risk (stale PySide wrappers of dialog widgets) by switching to polling;
  proved with a control run that scripted CAM dialog cycling crashes FreeCAD 26.3 by itself.
  Test suite: tests/run_freecad_tests.sh → ALL PASS.
- Research (web): Fusion help pages for heights, SolidWorks 2020 animated tooltips, Onshape
  two-stage tooltips → ideas recorded in memory.md. Marios: ideas only, our own drawings.
- Open: Marios has not installed it on Windows yet (needs the Mod path from the Python console);
  ask about his cutters and materials; Fusion names in fields_el.json are from Claude's knowledge
  (Fusion help pages checked only for the heights) — verify the rest if possible.
- Next (PR 3): GIFs for unusual Part/PartDesign buttons (Binders, Boolean, Clone, Datums...).
- Later the same day: Marios saw only still images in the Claude app (it shows the first frame);
  published a private gallery artifact so he can see them move. He asked for: more motion in
  pattern_angle / drill_extra_offset / peck_retract (done), slightly more modern colours (done:
  palette v2 in draw.py — wood grain, metallic tools, shadows, slate caption bar), deeper study
  of other CAD/CAM docs and no errors (docs/notes/verification.md). Corrections from the study:
  Step Down guidance (½·D to 1·D), plunge < ½ feed, removed unverified feed numbers, Step Over
  warning (>70–80 %), Min Travel wording, peck animation now shows the rapid back down (G83).
  Asked about Sketcher: not done yet → next PR.
- PR 2 was merged into the PR 1 branch (base not retargeted after PR 1 merged) → opened PR 3
  (same branch → main). LESSON: base every PR on main, or retarget before asking for Merge.
- Marios showed screenshots of MDJ Works help (Swedish): animation from the real app with cursor,
  numbered steps, "how to select" / "how to use" boxes, tip, shortcut badge. Built PR 4
  (feature/sketcher-help): that layout in our style + 17 Sketcher animations recorded in real
  FreeCAD + Greek texts checked against the wiki (Lock text corrected), CAM GIFs restyled
  (palette v3). Tests ALL PASS (1920x1200 and 1366x768 screens).
- YouTube is blocked in the container (no youtube.com/youtu.be); videos must be uploaded as files.
- Marios gave standing permission to merge PRs into main; PR 3 and PR 4 merged by Claude.
  Pending: more colour contrast in the CAM animations (later).
- PR 6: Part / Part Design unusual buttons (11 commands) with 3D recordings from real FreeCAD,
  short Greek texts checked against the wiki (Part Cut order, Linear Pattern Length = first→last).
  Tests ALL PASS; merged by Claude.
- Feedback round: "fewer words, the mouse should show the right way; CAM colours not nice (the
  brown wood)". Done on PR 4: palette v4 (slate block), all CAM captions shortened to 2–5 words,
  Sketcher GIFs now begin with the press of the real toolbar icon, popups cut to one sentence +
  ⚠ + "Χρήσιμο:" (Symmetric popup 714 → 464 px), English FreeCAD tooltip removed from field popups.
  Facts unchanged (verification.md still valid). Tests ALL PASS.

## 2026-10-11 → 2026-10-16 (Cowork, one long conversation)

Solved FreeCAD problems (details in `freecad-findings.md`):
- CAM Profile: warning "SetFromResult saved an open curve from a closed clipper path", then the hard
  failure with "combineHorizontalFaces: Zero working area", "failed to close some projection wire",
  "skipped 6 sub shapes during projection" — cause: selected geometry does not project to a closed
  XY wire. Advice given: select only a flat top/bottom face (or whole model), check orientation,
  Refine shape, or Profile a clean 2D section/pad.
- Step Down as a number of passes / percentage: use expressions, e.g. `(StartDepth - FinalDepth) / 4`,
  `(StartDepth - FinalDepth) * 0.25`, `ToolController.Tool.Diameter * 0.5`.
- Addon Manager could not install `tinydb`, `watchdog`, then `ezdxf`: FreeCAD's bundled Python has no
  `ssl` module. Workaround that WORKED for tinydb 4.9.0 + watchdog 6.0.0: download wheels in the
  browser, then
  `"C:\Program Files\FreeCAD 26.3\bin\python.exe" -m pip install --no-index --find-links "%USERPROFILE%\Downloads" <pkg>`.
  ezdxf (needs fonttools, pyparsing, typing_extensions, cp313 win_amd64 wheels): instructions given,
  result never reported back.
- Fusion → FreeCAD: export STEP. Import settings: untick "Import invisible objects", tick
  "Reduce number of objects". Then Part → Create a copy → Refine shape.
- Editing an imported solid in Part Design: select the solid with NO active body → Create Body →
  it becomes BaseFeature. Putting a copy into an existing body (Sub-Shape Binder / "independent
  copy") left "no solid to subtract from" on Pocket. He had made Body, Body001, Body002 while trying.
  The part was an HTD timing pulley ("vasi troxalion nema 23").

Research and build:
- Searched for a FreeCAD fork/addon with animated GIF/video help per button → none usable exists
  (see `addon-research.md`).
- Built the WikiTips addon (v0.1, then v0.2 after a review against FreeCAD source).
- Surveyed the whole official addon catalog for learning/UI/CAM helpers.
- Marios asked for this private repo with the files and these notes. Claude's environment could
  not create GitHub repos (session bound to pre-configured repos, no `add_repo`), so the repo was
  prepared as a git folder + zip for Marios to publish (GitHub Desktop → Publish → Private).

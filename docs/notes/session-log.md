# Session log

## 2026-10-17 (later): bigger popup picture on big screens
- Marios: picture quality "needs more checking, fix it". Checked: the GIF files themselves are sharp
  (1248 x 750); the real popup in FreeCAD 26.3 drew them only 536 px wide on a 1920 px screen at
  100 % (520 px at 125 %), so FreeCAD's own small text in them (dimension values) was hard to read.
- Now the popup width is 40 % of the screen's available width, between 440 and 820 px, and the
  picture is up to (width - 24) x 0.6 high: 742 px wide on 1920 @ 100 %, 735 real pixels on
  1920 @ 125 %, 1113 real pixels on 150 %; 1366 x 768 laptop 520 px. If the popup does not fit,
  first the examples/tip go, then the picture gets just as much lower as needed (min 170).
- Libraries sent today (IZAR, Stepcraft, Amana): see memory.md "CAM tool library".

## 2026-10-17: sharp GIFs + Greek help for ~110 more buttons (PR 22)
- Marios: GIFs still low resolution ("raise it a lot, don't skimp"); some buttons still showed the
  English wiki text and the blurry wiki picture ("check well and do them all").
- Cause of the blur: GIFs were 416 x 250 and Windows at 125-150 % stretched them (on his laptop the
  popup also shrank them to 170 px high, then the screen stretched that up again).
- Now: every GIF is 1248 x 750 (3x). Recordings are made with QT_SCALE_FACTOR=1.5, so FreeCAD draws
  fonts, markers and lines like on a 150 % screen (1248 x 750 view); the drawn CAM pictures are drawn
  at 6x and saved at 3x. The compositor (sketcher_gifs.py) works in layout pixels (832 wide) and
  scales to the picture (ScaledDraw). The popup draws each frame itself, smooth-scaled to the
  screen's real pixels (devicePixelRatio), shows it 416 px wide (562 on screens >= 1500 x 950) and
  only shrinks it when the popup cannot fit even after dropping the examples.
- All 238 old GIFs re-recorded/re-drawn at 3x (same scenes). New scenes: sketcher_extra.py (36),
  part_extra.py (36 Part Design + Part), cam_extra.py (10 CAM). Text-only (no GIF) where a picture
  could not be checked: CAM Quick Validate, Tapping, Flute, ToolBit files, experimental Area/Shape;
  Part Export/Import/selection filters...; PartDesign Migrate.
- 26.3 facts found: Sketcher Grid / Snap / Rendering Order are no longer toolbar buttons, they are in
  a settings menu of the sketch task panel ("snap to grid" is in the Grid settings).
  Sketcher Paste puts the copy at the SAME place (clipboard = Python script).
- Coverage (26.3 commands): Sketcher 122/140 (rest: drop-down groups), Part Design 38/43,
  Part 68/73, CAM 59/64 (rest: drop-down groups).
- content/img grew 18 MB -> ~50 MB (3x pictures).
- Marios asked about a ready CAM tool library: 26.3 ships "Default" with 15 sample bits; offered
  to build his own library file from a list of his real cutters (no code). Waiting for the list.
- Repo made PUBLIC by Marios; Addon Manager install verified (custom repository). In this Addon
  Manager version the custom repositories are in Edit → Preferences → Addon Manager (not the ⚙).

## 2026-10-17: Marios's first install on Windows - feedback round 1 (PR 20)
- Installed by hand in `C:\Users\mario\AppData\Roaming\FreeCAD\v26-3\Mod`: it works. His points:
  1. GIFs low resolution / not sharp -> NOT done yet (next: re-record at 2x, show with devicePixelRatio).
  2. The GIF flickered while the mouse moved over the button -> fixed: a new ToolTip event for the
     button that already shows the popup is swallowed (wikitips.py ButtonFilter).
  3. Knurl panel: Apply button wanted, OK only to finish -> done (Ok | Apply | Cancel). Changing a
     value shows fast lines, Apply computes the real teeth and the panel stays open, OK closes
     (computes only if a value changed after the last Apply), Cancel puts all values back.
  4. Cards at the bottom centre, not bottom left -> done (wikitips_errors.ErrorCard placement).
  5. Pitch 0.30 + depth 0.80 diamond took ~10 min and froze FreeCAD; depth 0.3 fast but sharp
     crests -> the depth was impossible (deeper than the teeth are high). Now: depth held between
     20 % and 100 % of the full height of the pitch (depth_for), default 75 %: teeth with a FLAT TOP
     like a real rolled knurl; sharp tips only when the full height is asked. The panel shows
     "auto / max" and says when a depth does not fit.
  6. Install like other addons? -> answer: the Addon Manager can add a custom repository only if it
     can download it without a password, i.e. the repo must be public (see memory.md).
- Speed of the flat-topped teeth: Part faces one by one + Part.Shell were slow (Shell runs
  BRepCheck on every face; D50 x 40, pitch 1 = 36k faces: 33 s, 1.6 GB; sewing a mesh: worse).
  New: the teeth (and the rest of the part, exported as it is) are written straight into
  OpenCASCADE BREP text (_Brep) and read back in one call: 36k faces 8.6 s / 410 MB; the boolean
  tool 3.3 s (was ~20 s). Same volume as the boolean in all 10 test cases, valid, a hole through
  the knurl afterwards works. Limits: 60 000 faces direct, 25 000 boolean (0.9 ms/face).
- Verified in real FreeCAD 26.3: knurl test PASS (Apply / OK / Cancel, depth clamp, pitch 0.3 with
  depth 0.8 in 4.6 s); full suite: see below.

## 2026-10-17: priorities and a separate CAM addon (notes)
- Marios: what matters now is that GIFs, error translations and knurling work correctly; we go on
  only when Claude is sure. CAM + 4th axis + polar converter: a SEPARATE addon later.
- Final check: fresh clone of main installed like the README says, full real-FreeCAD suite.

## 2026-10-17: knurl 4-8x faster, no boolean (PR 18)
- Marios: "find a way to make it very fast without crashes".
- Measured first: splitting the band into slices or cutting only the band slab was SLOWER (the
  cost is OCC's per-face work in the boolean, ~1 ms per tooth face, already run in parallel).
- New: direct_knurl() builds the result without a boolean on the teeth: the part gets a plain
  groove (analytic cut, instant), the groove faces are replaced by the tooth triangles (one mesh)
  and two end faces, and everything is sewn into one shell. Same volume as the boolean in every
  case tested (solid, tube, margins, band at the part's end, flange, rotated+moved part, straight
  and diamond); booleans with the result behave the same. When the band is crossed by a hole or
  a flat (checked with a cheap analytic common) it falls back to the boolean.
- First version moved the part to a local frame and back: some faces stayed behind (volume was
  right, the solid was not) - caught by the Body test (margins check); rewritten to work in the
  part's own coordinates, plus inside-point checks that return None (= boolean) on any defect.
- Speed: D20 x 30, pitch 1 in the GUI 10.8 s -> 4.6 s; D50 x 40, pitch 1: 80 s (morning) -> 34 s
  (audit) -> 9 s, 640 MB. Limits: 60 000 faces direct (19 s, 1.2 GB), 30 000 for the boolean.
- Cheap checks instead of isValid() (5 s on 29k faces) and no Python object per tooth face (4 s).

## 2026-10-17: full audit (code, GIFs, resources) (PR 17)
- Marios: check the whole project for mistakes, the GIFs too, whether anything can use too many
  resources or crash his PC (especially knurling), and research more helpful addons.
- Helper agents could not run (account spend limit), so the audit was done directly.
- KNURL (the big one): time and memory grow fast with size. Before: D50 x 40 mm, pitch 1 = 29k
  faces, 2 min, 1.3 GB; D50 pitch 0.6 did not finish in 15 min (would freeze a laptop). Now:
  tooth tips 2 µm inside the cylinder (no tangent faces: boolean 3-5x faster) and the tool is
  built as one mesh (shared edges): same case 34 s, 860 MB. Hard limit MAX_FACES = 30000:
  bigger knurls are refused at once (Greek card + red text in the panel with faces and seconds);
  the panel shows "N faces, about X seconds" before OK. Angle clamped 5-60°, depth >= 0.01,
  at most 360 lines each way for the light kind.
- Knurl light kind put its lines INTO the solid: a Fillet after it failed. Now the solid stays
  untouched and the lines are drawn by the view provider (pivy). For drawings: TechDraw hatch
  "Diamond" (FCPAT.pat) is the usual knurl symbol; texts changed accordingly.
- Error explainer: silent checks only on the 3 newest recomputed features and only shapes with
  <= 20000 faces (a full recompute of a big model must not cost seconds); patterns that change
  nothing get their own advice (_nochange_pattern).
- Idle cost of WikiTips measured in real FreeCAD: +0.09 s CPU per 30 s, +4 MB.
- GIF audit: automatic checks (frames, blank frames, size, duration) on all 237 + every GIF looked
  at (3 frames each, with its Greek text). Fixed: CAM_Simulator (legacy) showed the new
  simulator GIF; chipBreakEnabled (G73) showed full-retract pecking (G83); Adaptive:stepOver
  showed a zigzag 50% step; Revolution/Groove axis showed the angle GIF (all four images removed,
  texts kept); Part primitives recorded with non-default sizes (Box 20x14x10, Cylinder R5, Cone
  6/2...) re-recorded with FreeCAD's real defaults so one click gives what the GIF shows;
  Part_ProjectionOnSurface caption said "wrapped" (projection is not a wrap).

## 2026-10-17: CAM put on hold (notes only)
- Marios: nothing more for CAM now. Next phase: his polar-coordinate converter + easy CAM setup for
  polar and 4th-axis work. Written under "Pending" in memory.md so it is not forgotten.

## 2026-10-17: fix, text on a cylinder was upside down (PR 15)
- Found on the demo picture (the tests only measured volumes): FreeCAD gives the side of a Pad an
  axis pointing DOWN (v from -L to 0); the sketch took that as its Y, so text came out upside down
  and mirrored (left-handed frame). Fix: the sketch is always right-handed with Y up (world Z, else
  Y, else X) and Z out of the cylinder; Knurl margins also count from the bottom (upwards()).
- Tests now check where a drawing lands (a square at sketch (8, 5) must be cut 5 mm higher and
  8 mm along the surface) and that the Knurl margins start at the bottom.

## 2026-10-17: Knurl tool + drawing on a cylinder (PR 14)
- Marios: "make knurling on cylinders simple, without a planar workaround, or an icon that does it
  automatically" (for 3D printing, CNC 4th axis and drawings). No ready knurl tool exists for
  FreeCAD (searched: only macros for other programs; FCCamGroover cuts a cam groove).
- wikitips_knurl.py: button "Knurl (ραβδώσεις)" on the WikiTips toolbar. Select the outer cylindrical
  face, press it: Greek panel (pattern Διαμάντι/Ίσιο, kind Πραγματικό/Ελαφρύ, pitch, angle, depth,
  margins). While the panel is open the preview is fast lines; OK computes the real teeth.
- Real teeth: pyramids on a diamond grid built from planar faces (or straight V grooves) and one
  boolean cut: D20 x 20 mm, pitch 1: one valid solid in ~6-15 s. Light kind: helix lines only
  (drawings show knurling as crossed lines).
- In a Body it is a PartDesign::FeaturePython (follows the Tip; a Pocket after it works); on Part
  solids a Part::FeaturePython with Base. The cylinder is stored as numbers and found again on
  recompute, so upstream edits (longer Pad) are followed.
- FOUND: PartDesign::FeatureAdditivePython / FeatureSubtractivePython crash FreeCAD 26.3 when
  created with the GUI (even without WikiTips) → use PartDesign::FeaturePython.
- Test: tests/freecad_knurl_test.py ("knurl" in run_freecad_tests.sh).
- wikitips_wrap.py: button "Σκαρίφημα σε κύλινδρο". Click the cylinder where the drawing goes, press
  it: a flat sketch opens touching the cylinder there (X around, Y along the axis, dashed frame =
  the whole unrolled surface). Text, shapes, circles drawn in it are wrapped EXACTLY (B-spline poles
  mapped to angle = x/R, height = y) and become Χάραξη / Ανάγλυφο / Μέχρι τον άξονα (double-click
  the Wrap to change mode and depth). Also works across the cylinder seam. < 0.2 s.
- Test: tests/freecad_wrap_test.py ("wrap" in the suite): text "CNC" + circle, three modes,
  save + reopen, upstream Pad edit.
- Open: G-code for knurling on a 4th axis needs his machine setup (ask); GIFs for the two buttons.

## 2026-10-17: more errors explained, Greek only (PR 13)
- Marios keeps FreeCAD in English on purpose (to learn the real terms) but wants the meaning in
  Greek, and "as many problems solved as possible". Not wanted: Greek search.
- Marios then asked: error cards ONLY in Greek. The card shows FreeCAD's message translated
  ("Το FreeCAD λέει: ..."), no English; pref ShowEnglish brings the English + glossary back.
- Translation data: Greek translation (content/errors_el.json
  "translations", sentence by sentence) and the key words ("glossary", e.g. wire = περίγραμμα).
- 55 rules (was 26): wrong-selection notifications of Sketcher / Part Design / Part (FreeCAD 26.3
  shows them in a short popup 'NotificationBox_label', read once per new notification; modal
  message boxes too), Up to face without face, Loft sections that do not match, Pipe without spine,
  Part boolean with a sketch, Draft with empty message, Part fillet too big (log).
- New silent checks found by probing: double lines / overlapping shapes give an EMPTY Pad (volume 0)
  without any error; dressups (Thickness...) that change nothing get their own advice.
- Card moved to the bottom LEFT of the 3D view: in 26.3 the task panel sits on the right.
- Next (asked by Marios): knurling on cylinders made easy, and sketches/text/holes on cylinders
  (he wants it for 3D printing, CNC 4th axis and drawings).

## 2026-10-17: error explainer + "show me where" (PR 12)
- Marios liked ideas 1 and 4 of addon-research.md → implemented in wikitips_errors.py.
- Error explainer: when a feature turns red after a recompute, a Greek card (bottom of the
  3D view) says what went wrong + numbered steps; also CAM errors in the Report view. Rules in
  content/errors_el.json (26 rules, regex on the English message), messages probed in real FreeCAD.
  Also catches two silent mistakes: feature that changed nothing, Body split in two solids.
  Waits while a task dialog is open; a closed card does not come back for the same error.
  Preference Mod/WikiTips ExplainErrors (default on).
- "Show me where": command names in the steps are blue links; a click outlines the real toolbar
  button (amber, pulsing ~3 s) or says which workbench / sketch mode shows it.
- New real-FreeCAD test tests/freecad_error_test.py (in run_freecad_tests.sh as "errors").

## 2026-10-17: a GIF for every toolbar button (PR 11)
- 72 new 3D scenes in tools/gifs/part_more.py (Part Design features, additive/subtractive
  primitives, dressups, Body, datums, binders, sketch 3D commands, Part ops and primitives)
  + 11 regenerated; Sketcher_CreateText added to sketcher_more.py. All 194 commands in
  commands_el.json now point to our own GIF (checked by script). Full real-FreeCAD suite: ALL PASS.
- Second gallery page (Sketcher / Part Design / Part) published as an artifact for Marios.
- Next (agreed direction "make it professional"): ideas from addon-research.md, first the
  plain-language error explainer and "show me where" (outline of the real button).

## 2026-10-17: Part Design dialog fields (PR 10) + addon survey
- Marios: "yes, do ALL functions; search for helper addons and take ideas, make it professional".
- 124 Part Design panel fields with Greek help (Pad, Pocket, Revolution, Groove, Hole, Fillet,
  Chamfer, Draft, Thickness, Helix, Loft, Pipe, Linear/Polar Pattern, Mirrored). Field names from
  the 26.3 .ui files (FreeCAD git tag 26.3rc1), meanings from the 26.3 wiki; Hole type mapping read
  in TaskHoleParameters.cpp (Clearance / Tap drill / Threaded = model or cosmetic thread).
- 15 setting animations recorded in real FreeCAD (tools/gifs/pd_rec.py → content/img/pd): sides,
  type, pocket type, taper, reversed, revolution angle, hole type, hole head, fillet, chamfer,
  thickness, draft, helix, linear and polar pattern. No mouse in these (setting changes only).
- Test suite opens 10 Part Design dialogs (Pad, Pocket, Revolution, Hole, Fillet, Chamfer,
  Thickness, Helix, Linear/Polar pattern) and hovers every field.
- Addon survey (see addon-research.md, second survey): ranked ideas list for next PRs.
- 55 more Sketcher animations (tools/gifs/sketcher_more.py, same recorder): every Sketcher toolbar
  button now has its own GIF except the 3D/UI ones (Leave/View/Section/Edit/Map/Validate/New sketch,
  Projection, Intersection, Text) → next PR. B-spline curvature comb hidden in recordings
  (Sketcher/General BSplineCombVisible etc.); composer draws an amber dot at each click until the
  result appears. Test found a missing field (Revolution sidesMode) → added.

## 2026-10-17: CAM dressups (PR 8)
- Marios: "more explanation for CAM, e.g. dressups, or better GIFs … check if you left something".
- Dressup command GIFs re-recorded: before (light indigo) vs after (rose) with a legend, quieter
  rapids, first rapid hidden. Found and fixed: the "before" path stayed selected (green).
- New: Greek help for every field of the dressup panels (47 entries) + 5 drawn GIFs
  (dogbone_style, tag_shape, lead_style, dragknife, boundary_inside). Test suite now opens six
  dressup panels (Dogbone opened with setEdit, the command itself does not open it): ALL PASS.
- Marios: "a bit slower, not too slow" → all GIFs regenerated 1.3× slower (draw.SLOWER).
- Audit: 128 toolbar commands of Sketcher / Part Design / Part still showed only the English
  wiki → PR 9 adds Greek for all of them. Found while testing: a Greek entry without our own GIF
  dropped the wiki picture → fixed (picture kept, credited). Field-hover test made robust
  against a missed 150 ms poll (one retry; it failed once, passed on reruns).

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

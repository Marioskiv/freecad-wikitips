# WikiTips — status (v0.2.1 on branch fix/real-freecad-groups, 2026-10-16)

## What it does
Hover a toolbar button → frameless popup (Qt ToolTip window) with: visible button label as title,
command id, menu path, shortcut, one picture from the wiki, a short description and up to 6 usage
steps. Replaces the normal tooltip only when we have an entry; otherwise FreeCAD's tooltip shows.
Global toolbar "WikiTips" with an on/off command `WikiTips_Toggle`
(parameter `BaseApp/Preferences/Mod/WikiTips/Enabled`).

## How it works (wikitips.py)
- `install()` (called from InitGui.py): registers the command, creates the global toolbar once
  (param `BaseApp/Workbench/Global/Toolbar/WikiTips`, flag `ToolbarCreated`), starts a 2 s timer
  that installs one event filter on every `QToolButton` of the main window (marked with the
  dynamic property `wikitips` so it is installed once). No app-wide filter (performance).
- On `QEvent.ToolTip`: `command_name(action, button)`: 1) `action.objectName()`; 2) the
  `<i>Name</i>` at the end of FreeCAD's rich tooltip (gives Std_Undo/Redo and the sub-command
  shown by C++ groups, e.g. `Sketcher_Projection (Sketcher_CompExternal:0)`); 3) the sub-actions
  in `button.menu()`, each named by `action_name()` (objectName → data() → `<i>` in tooltip →
  plain tooltip/statusTip looked up in a map built from `Gui.Command.listAll()/getInfo()`, needed
  for Python groups like Part_CompOffset whose sub-actions have no name); pick same tooltip, else
  checked, else same icon, else the first. `lookup()` also tries CAM_ ↔ Path_ prefixes.
- Popup text is shortened (`short_html`): first 2 paragraphs, ≤ 420 visible chars, ≤ 4 steps.
- A NEW `TipPopup` is created per hover (re-using one kept stale sizes). Labels get fixed width and
  `heightForWidth` heights; image max height 260 px (170 on screens < 900 px tall); GIFs via QMovie,
  scaled. Hidden on Leave/press/wheel/hide of the owner and by a 250 ms cursor-position check.
- `eventFilter` wraps everything in try/except → never disturbs FreeCAD.

## Field help in dialogs (branch feature/cam-field-help, PR 2)
- `content/fields_el.json` (hand-written, Greek): 72 fields keyed by Qt objectName; `Op:name`
  overrides per operation (Op = module of the edited object's Proxy, e.g. `MillFacing:clearingPattern`).
  Keys: t title, d text, w warning, f Fusion 360 name, i animation (content/img/...).
- `content/img/cam/*.gif`: 25 animations (2.3 MB) drawn by `tools/gifs/cam_gifs.py` + `draw.py`.
  Example situation: 6 mm flat end mill, wood/MDF, 12 mm pocket.
- `FieldWatcher` (150 ms timer, only while `Gui.Control.activeDialog()`): widget under cursor →
  objectName (or parents up to 3, for spin-box line edits; or the field next to a QLabel) → after
  450 ms rest shows the popup; the field's English tooltip is moved into the popup (small, gray).
  The popup stores only a screen rect. No event filters on dialog widgets (crash lesson, memory.md).
- Covered: CAM Profile, Pocket Shape, MillFacing, Adaptive, Drilling (+ Helix/Engrave fields).
  3D Surface/Waterline commands do not exist in this build (need experimental/OCL) — not done.

## Greek help for commands (branch feature/sketcher-help, PR 4)
- `content/commands_el.json`: hand-written Greek help for 17 Sketcher commands, overriding the
  English wiki text (menu path kept). Sections: d (what), sel/selw (how to select), uses (where
  useful), tip; rendered by `sections_html()`; shortcut shown as a badge in the header. On small
  screens the popup drops "uses" and "tip" if it would not fit (`compact`).
- `content/img/sketcher/*.gif`: 17 animations recorded in REAL FreeCAD 26.3
  (`tools/gifs/sketcher_rec.py`, light theme via View preferences) and composed with cursor,
  click rings and numbered step badges (`tools/gifs/sketcher_gifs.py`). ~0.9 MB.
- All GIFs (CAM + Sketcher) share one look (palette v4, draw.py): light background, slate stock
  block, floating slate caption pill with amber dot. Sketcher GIFs show the real toolbar icon being
  pressed first (icon saved by sketcher_rec.py from Gui.Command.get(name).getAction()).
- Popups are short by design: commands = d + selw (⚠) + uses; fields = d + w + Fusion name.

## Part / Part Design help (PR 6)
- 11 more commands in content/commands_el.json: Part_Cut/Fuse/Common/Section, PartDesign_Mirrored,
  PolarPattern, LinearPattern, Boolean, Plane, SubShapeBinder, Clone. Animations recorded in real
  FreeCAD 3D view by `tools/gifs/part_rec.py` (same events.json → sketcher_gifs.py), in
  content/img/part (~0.6 MB). Part booleans show "click, Ctrl+click, press button".

## Greek for every toolbar button (PR 9, 2026-10-17)
- content/commands_el.json now covers ALL visible toolbar buttons of Sketcher, Part Design, Part and
  CAM (194 commands). Without our own GIF the popup keeps the wiki picture (footer credits it).
- Still English: menu-only commands and other workbenches (Draft, TechDraw, Assembly...).
- DONE (PR 11, 2026-10-17): EVERY one of these toolbar buttons has its own GIF recorded in real
  FreeCAD 26.3 (only CAM Axis Map and Z Correct are drawn). Part / Part Design 3D scenes:
  tools/gifs/part_more.py (72 scenes) → content/img/part; Sketcher: tools/gifs/sketcher_more.py.
  content/img is ~18 MB in total.
- Still without field help: Part workbench dialogs (Extrude, Revolve, Fillet...), Sketcher dialogs.

## CAM toolbar commands (PR 7)
- 38 CAM commands in content/commands_el.json (all CAM toolbars of 26.3 + Surface/Waterline),
  animations in content/img/camcmd: recorded in real FreeCAD by tools/gifs/cam_rec.py
  (`HOME=<tmp> FREECAD=<fc> OUT=<dir> sh tools/gifs/cam_rec.sh [scene...]`, then
  `python3 tools/gifs/sketcher_gifs.py <dir> content/img/camcmd`), 4 drawn by cam_cmd_gifs.py.
- Not shown as a toolbar button but covered: CAM_PostSelected (uses the Post GIF), CAM_Surface and
  CAM_Waterline (shown only with OpenCamLib + "Enable OCL dependent features"; recorded for real).
- `lookup()` falls back to content/commands_el.json, so new commands without a wiki page
  (CAM_MillFacing, CAM_OperationCopy) still get a popup.
- Not covered yet (menu-only, rarely used): CAM_Tapping, CAM_Probe, CAM_Fixture, CAM_Comment,
  CAM_Stop, CAM_Custom, CAM_Shape, CAM_Area, CAM_ExportTemplate, ToolBit library commands.

## Data pipeline (tools/)
- Primary source: https://github.com/Reqrefusion/FreeCAD-Documentation-html (offline copy of the
  live wiki, all languages, updated daily, ~1.8 GB). Pages = `wiki/<Command>.html`, images
  `wiki/File/<name>`, translations in `wiki/<lang>/` (there is NO Greek).
  Command pages are detected by the `table.fcinfobox` with a "Menu location" row.
- Fallback for commands no longer on the wiki: https://github.com/FreeCAD/FreeCAD-documentation
  (markdown, last commit 2025-01-15, `wiki/*.md` with `GuiCommand:` front matter, images in
  `wiki/images/`). 15 entries come from here.
- The live wiki (wiki.freecad.org, incl. api.php) is behind Anubis bot protection — automated
  fetches get "Access Denied". Do not build anything that scrapes it at runtime.
- `convert_images.py`: SVG → PNG via cairosvg, everything fitted to 420×300, white background,
  PNG quantized or JPG; animated GIFs kept animated. Result ~19 MB.
- `build_data.sh` reproduces `data/` exactly (verified identical JSON 2026-10-16).

## Coverage (2026-10-16)
1293 commands, 642 with picture. Std 172/51, Sketcher 118/52, PartDesign 57/54, Part 83/54,
CAM 40/17, Draft ~84/63, TechDraw ~108/87, Assembly 25/1. Missing pictures = the wiki page has none.
Text is English (wiki has no Greek translation).

## Verified
- **Real FreeCAD 26.3.0 (conda-forge build 2026.09.16, Linux, Qt6) — 2026-10-16**, with
  `tests/freecad_gui_test.py`: loads without errors in the Report view; popups for normal buttons,
  C++ dropdowns (Sketcher arc/rectangle/dimension/external, PartDesign primitives) and, after the
  fix, Python dropdowns (Part offset/compound/join, CAM drilling/post/sim/engrave) and Undo/Redo.
  Sketcher 54, PartDesign 68, Part 57, CAM 44 visible buttons: all have an entry except
  CAM_MillFacing and CAM_OperationCopy (new in 26.3, no wiki page yet).
  Not yet seen on Windows — Marios still has to install and confirm.
- PR 2, real FreeCAD 26.3: `tests/run_freecad_tests.sh` ALL PASS — popups on 20/26 Profile,
  24/27 Pocket Shape, 21/22 MillFacing, 30/32 Adaptive, 24/26 Drilling visible fields (the rest
  are hidden/zero-size in the test layout), toolbars of 4 workbenches PASS.
- Offline test with PySide6 6.12 and a mock FreeCAD main window that mimics FreeCAD's real
  structures (objectName per command, dropdown group + button menu): popups for normal commands,
  CAM_/Path_ alias, dropdown group, unknown command falls back, toggle off/on, light and dark palette.
- FreeCAD-specific assumptions checked in FreeCAD source (see freecad-findings.md).

## NOT verified
- Windows build of FreeCAD (Marios's machine): screen scaling (HiDPI), fonts, popup placement.
  Ask him for a screenshot after install; check the Report view for "WikiTips" errors.
- Interaction with ribbon addons (NeoRibbon, FreeCAD-Ribbon) — should work if they use QToolButtons
  whose defaultAction is FreeCAD's QAction.
- Menus: no popup on menu items (only toolbar buttons).

## Error explainer + "show me where" (PR 12, 2026-10-17)
- wikitips_errors.py, started from wikitips.install() (failure only prints a warning).
- Document observer marks recomputed documents/objects; a 700 ms timer (only when no task dialog is
  open) finds red objects, picks the first one whose dependencies are fine, matches its status
  string against content/errors_el.json and shows ErrorCard (child widget of the main window,
  bottom left of the central area, the 26.3 task panel is on the right). Unknown message → generic card.
- Card is Greek only: FreeCAD's message translated sentence by sentence ("translations"); untranslated
  sentences are left out. Pref ShowEnglish=true adds the English text and glossary words.
- Notifications: status bar button 'notificationArea' count + top-level QLabel 'NotificationBox_label'
  rows (newest first); modal QMessageBox text via activeModalWidget. Note/log cards hide after 30 s.
- Silent checks on recomputed Part Design features: same volume as BaseFeature → "_nochange";
  more solids than before → "_split".
- Report view: new lines are matched only against rules with "src": "log" (CAM messages).
- Links {Command} in the steps → show_me(): finds the visible toolbar button (also inside dropdowns)
  and draws a pulsing Outline; if hidden, a hint where it is (sketch mode / workbench).
- Verified: tests/freecad_error_test.py in real FreeCAD 26.3 (rules for 20 real messages, cards for
  open sketch, conflicting constraints, missed Pocket, split Body, CAM heights; outline on the Pad
  button; card hides when fixed; closed card stays closed; preference off).
- Not verified: Marios's Windows machine; FreeCAD in Greek UI language (messages are matched in
  English; getStatusString seemed untranslated, to check).

## Knurl tool (PR 14, 2026-10-17)
- wikitips_knurl.py (geometry without GUI + command/panel/view provider when the GUI is up).
  WikiTips_Knurl is added to the global WikiTips toolbar (also for existing installs).
- Default pitch by diameter: ≤8 mm 0.6, ≤16 mm 0.8, ≤32 mm 1.0, else 1.2 (ideas from DIN 82 tables).
- Depth 0 = automatic (90° teeth: 0.5 x pitch x cos(angle)), capped at half the radius.
- Verified in real FreeCAD 26.3 (tests/freecad_knurl_test.py): button, wrong selection card, panel,
  preview, real teeth valid, Tip, Pocket after it, Part cylinder, save + reopen.
- Not done: inner (bore) knurling, G-code for a 4th axis, a GIF for the button.

## Drawing on a cylinder (PR 14, 2026-10-17)
- wikitips_wrap.py, button WikiTips_Wrap. Uses the picked point (Selection PickedPoints) for the
  tangent sketch (MapMode Deactivated, Placement set; in a Body: body.newObject). Construction frame
  2πR wide x cylinder length. The Wrap feature (PartDesign::FeaturePython or Part::FeaturePython)
  reads the sketch Placement on every recompute, so moving the sketch moves the drawing.
- Only closed shapes count (Bullseye face maker: letters with holes work). Open lines are ignored.
- Verified in real FreeCAD 26.3 (tests/freecad_wrap_test.py).

## Ideas / open (plan agreed 2026-10-16, see memory.md)
- NEXT PHASE (on hold until Marios says): CAM with his polar converter + 4th axis (memory.md, Pending).
- PR 2: field help inside dialogs — CAM task-panel widgets have stable objectNames (see
  freecad-findings.md) → Greek text + animated diagram per field (prototype: CAM heights GIF).
- PR 3: GIFs for unusual buttons (Binders, Boolean, Clone, Datums, Compound, Section...).
- PR 4: Sketcher + PartDesign dialog fields. GIF generator scripts go in `tools/`.
- Greek translations for his most-used commands (Sketcher, PartDesign, Part, CAM) as an overlay file
  (hand-written, outside the generated `data/commands.json`).
- Optional "Open full page" (the offline HTML page) on Ctrl+hover.
- Publish to the Addon Manager catalog later (needs a public repo; private repos cannot be installed
  through the Addon Manager without credentials).

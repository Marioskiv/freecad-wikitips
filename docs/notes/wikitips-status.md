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

## Ideas / open (plan agreed 2026-10-16, see memory.md)
- PR 2: field help inside dialogs — CAM task-panel widgets have stable objectNames (see
  freecad-findings.md) → Greek text + animated diagram per field (prototype: CAM heights GIF).
- PR 3: GIFs for unusual buttons (Binders, Boolean, Clone, Datums, Compound, Section...).
- PR 4: Sketcher + PartDesign dialog fields. GIF generator scripts go in `tools/`.
- Greek translations for his most-used commands (Sketcher, PartDesign, Part, CAM) as an overlay file
  (hand-written, outside the generated `data/commands.json`).
- Entries for CAM_MillFacing / CAM_OperationCopy (new commands without wiki pages).
- Optional "Open full page" (the offline HTML page) on Ctrl+hover.
- Publish to the Addon Manager catalog later (needs a public repo; private repos cannot be installed
  through the Addon Manager without credentials).

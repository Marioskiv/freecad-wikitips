# WikiTips — status (v0.2.0, 2026-10-16)

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
- On `QEvent.ToolTip`: `command_name(action, button)` → `action.objectName()` is the FreeCAD
  command name. Dropdown groups: the group QAction has the group name; sub-commands are in
  `button.menu()`; pick the sub-action whose toolTip equals the button's (FreeCAD copies it),
  else the checked one, else same icon. `lookup()` also tries CAM_ ↔ Path_ prefixes.
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
- Offline test with PySide6 6.12 and a mock FreeCAD main window that mimics FreeCAD's real
  structures (objectName per command, dropdown group + button menu): popups for normal commands,
  CAM_/Path_ alias, dropdown group, unknown command falls back, toggle off/on, light and dark palette.
- FreeCAD-specific assumptions checked in FreeCAD source (see freecad-findings.md).

## NOT verified
- Never run inside a real FreeCAD. Marios has FreeCAD "26.3.0RC1" on Windows (Qt6/PySide6, Python 3.13).
  Ask him for a screenshot after install; check the Report view for "WikiTips" errors.
- Interaction with ribbon addons (NeoRibbon, FreeCAD-Ribbon) — should work if they use QToolButtons
  whose defaultAction is FreeCAD's QAction.
- Menus: no popup on menu items (only toolbar buttons).

## Ideas / open
- Greek translations for his most-used commands (Sketcher, PartDesign, Part, CAM) as an overlay file.
- Optional "Open full page" (the offline HTML page) on Ctrl+hover.
- Publish to the Addon Manager catalog later (needs a public repo; private repos cannot be installed
  through the Addon Manager without credentials).

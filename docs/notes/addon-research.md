# Addon / fork research (checked 2026-10-16)

Method: official catalog `https://github.com/FreeCAD/Addons` (`Data/Index.json`, 180 addons),
package.xml of each fetched from raw.githubusercontent.com (148 readable), the promising ones cloned
and their code grepped for `QMovie`, `.gif`, image tooltips; plus web searches.
GitHub search API and repo creation are NOT available from Claude's cloud environment.

## Animated GIF / video help per button
- **Nothing usable exists.** No catalog addon shows GIF/image tooltips (grep found none).
- `luzpaz/freecad-animated-gif-tooltips`: idea + a few 200×200 GIFs, no code to show them in FreeCAD.
  Forum campaign since ~2017 (devtalk.freecad.org t/19127), never finished.
- FreeCAD issue #19365: request for extended tooltips in the Ribbon — static text only, open.
- **MDJ Works** (Daniel Johannesson, seen in a Facebook FreeCAD group video, Swedish UI:
  Konstruera/Bygg/Simulera/Tillverka/Ritning/Beredning): no public repo or page found. Probably a
  private build. Marios thinks it has GIF help.
- **Kovač** (github.com/aleksejko004/kovac): FreeCAD-based distribution with a Fusion-like UI
  (modes, timeline, radial menu, command search). Early (M1–M2 done 2026-10), no CAM, no GIF help.
- **FreeCAD Nut** (gumroad, free): icons/toolbars/stylesheet bundle; no GIF help mentioned.

## Recommended to Marios (in this order)
| Addon | Why | Status/date |
|---|---|---|
| WikiTips (ours) | picture + explanation on hover | v0.2.0 |
| ToolSeek (robdevtech/ToolSeek) | Ctrl+Space command palette, find any command by name | 2026-08, namespaced layout, FreeCAD 1.0+ |
| HistoryWorkbench (eblanshey) | version history with 3D/tree diff, safe restore; git inside, no git knowledge needed | active 2026-10 |
| FreeCAD-Documentation-html (Reqrefusion) | whole wiki offline, daily updates, ~1–2 GB | active 2026-10 |
| NeoRibbon (robdevtech) or FreeCAD-Ribbon (APEbbers) | Fusion-like ribbon with labels; NeoRibbon is light and FreeCAD 1.1+ only | 2026-08 / 2026-10 |
| FeedsAndSpeeds (dubstar-04) | CAM feeds/speeds into the tool controller; needs CAM ToolBits | 2025-12 |
| GearWorkBench (iplayfast) | parametric gears incl. racks, internal, planetary; alpha | 2026-10 |
| FreeCAD-Beginner-Assistant | best-practice report for PartDesign/Sketcher; old (2024), untested on 1.1 | 2024-12 |

## Interesting but not recommended yet
- **Nxt** (obelisk79/FreeCAD-Nxt): QML UI replacement, auto-repair "Wire not closed", viewport
  editing. Author says experimental/heavy development.
- **freecad-mcp-bridge** (CREATeNG): MCP server inside FreeCAD (127.0.0.1:39280/mcp) so an AI agent
  can drive the open session. New (2026-10); not tried.
- **Molding Wizard** (ryankembrey/FreeCAD-Molding-Wizard, workbench "Molding"): 2-part molds from a
  body; not in catalog, add via Addon Manager custom repo URL + branch `main`. Its package.xml has a
  placeholder repo URL (github.com/example/...), so updates may not be detected. 2026-10.
- **CamScripts**: requires FreeCAD ≤ 1.0 (new tool system broke it) — skip.
- MeshToFeatures / Detessellate: STL → editable PartDesign (prismatic parts).
- DFM (draft/thickness/undercut analysis), LiveSectionAnalyzer, PieMenu, Launcher/Runner (command
  search; may be merged into FreeCAD via PR #25833).

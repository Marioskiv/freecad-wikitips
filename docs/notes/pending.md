# Pending — open items and questions for Marios (WikiTips)

Made 2026-10-20 (he asked for a memory file and a pending file in every repo). Newest first. Move an item to
`memory.md` when it is decided, delete it when it is done. Only WikiTips items here.

## Waiting for Marios
- **Explanations for every setting** (his request 2026-10-22, order: Property view first, then Edit →
  Preferences). DONE in 0.6.0: Property view for App, Part, Part Design, Sketcher (461 entries). NEXT, same
  way: CAM (Python objects: Job, operations, Tool Controller; count them first), then Draft, TechDraw,
  Assembly, Spreadsheet, Mesh/Surface/Points, BIM, FEM, rest (701 Data + 132 View names counted for the C++
  objects). After that: Edit → Preferences (needs code: it is a modal dialog, not a task panel).
- **Greek text (+ GIF where possible) for ALL FreeCAD commands** (his request 2026-10-20: "where the
  explanation is still in English, I want Greek for all; GIFs for all if possible, Greek text for sure").
  Audit in real FreeCAD 26.3 (every workbench activated, toolbars + menus, 870 command names):
  | group | commands | Greek | GIF | English only | nothing |
  |---|---|---|---|---|---|
  | Sketcher | 102 | 102 | 102 | 0 | 0 |
  | Part | 59 | 54 | 50 | 0 | 5 (drop-down groups only) |
  | PartDesign | 49 | 46 | 46 | 0 | 3 (drop-down groups only) |
  | CAM | 48 | 43 | 42 | 0 | 5 (drop-down groups only) |
  | Std (common: file, edit, view…) | 171 | 0 | 0 | 142 | 29 |
  | TechDraw | 119 | 0 | 0 | 103 | 16 |
  | Draft | 69 | 0 | 0 | 66 | 3 |
  | BIM + Arch + IFC | 97 | 0 | 0 | 65 | 32 |
  | Mesh + MeshPart | 35 | 0 | 0 | 35 | 0 |
  | Assembly | 24 | 0 | 0 | 22 | 2 |
  | Spreadsheet | 15 | 0 | 0 | 15 | 0 |
  | Robot | 15 | 0 | 0 | 13 | 2 |
  | OpenSCAD, Surface, Points | 22 | 0 | 0 | 22 | 0 |
  | Reverse Engineering, Inspection, Materials, Test | 28 | 0 | 0 | 1 | 27 |
  FEM: its commands were not caught by the listing (to check). Proposed order (to confirm): Std →
  TechDraw → Draft → Assembly → Spreadsheet → Mesh/Surface/OpenSCAD/Points → BIM/Arch → the rest.
  GIFs: DECIDED 2026-10-20 (his answer "b"): Greek text for EVERY command; GIFs only where a moving
  picture really helps (drawing tools, TechDraw…), not for simple ones (Save, Undo…). 320 GIFs now = 51 MB.
  Still to confirm: the order above (he did not understand the question; asked again).
- **Try 0.5.0 on his PC** (Knurl and Wrap removed; their buttons are taken off the WikiTips toolbar at start).
  For his old files with Knurl/Wrap he needs the polar-cnc-converter addon installed (Knurling & Wrap).
- **Earlier priority (2026-10-17), still open:** GIFs and Greek error explanations must work correctly on his
  PC; the next step only after he has tried it and hears "I am sure".
- **CAM animations:** more colour contrast (darker stock edge and tool, stronger path colour, darker labels).
- **Question for him:** which cutters (flat/ball/V-bit) and materials (wood/alu/plastic) he uses, so the
  examples match his work.
- **Tool libraries → their own repository** (his request 2026-10-20; 2026-10-20: "I will find the zips later,
  leave it in pending"; he asked whether they should be an addon — answered: possible (an addon with an "install libraries"
  button that copies the files into CamAssets/Tools, asking before overwriting; updates through the Addon
  Manager), or plain files imported with CAM → Toolbit Library Manager; his choice is open). Not WikiTips work any more; the facts
  are in memory.md ("CAM tool library"). Open: repo name, private or public; the zips (YG-1, IZAR, Stepcraft,
  Amana) are not in any repo and not in the cloud machine: he uploads them, or they are rebuilt from his
  catalogs; his spindle max RPM; Clarkson (no catalog found).
- Old branch `origin/fix/real-freecad-groups`: its only commit not in `main` is a merge commit of PR 2
  (2026-10-16) with no file difference to `main` (checked 2026-10-20). Can be deleted: ask him.

## Found, not fixed (ask first)
- `tests/check_content.py` fails on `main` already (before 0.5.0, checked 2026-10-20):
  `commands_el.json Sketcher_LeaveGroup: missing picture sketcher/Sketcher_LeaveSketch.gif`.

## Ideas for later (he said later)
- SolidWorks-style tooltip size setting (big + GIF / big / small); Onshape-style two stages (short line
  first, GIF after ~1.5 s).

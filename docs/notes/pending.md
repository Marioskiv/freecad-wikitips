# Pending — open items and questions for Marios (WikiTips)

Made 2026-10-20 (he asked for a memory file and a pending file in every repo). Newest first. Move an item to
`memory.md` when it is decided, delete it when it is done. Only WikiTips items here.

## Waiting for Marios
- **Try 0.5.0 on his PC** (Knurl and Wrap removed; their buttons are taken off the WikiTips toolbar at start).
  For his old files with Knurl/Wrap he needs the polar-cnc-converter addon installed (Knurling & Wrap).
- **Earlier priority (2026-10-17), still open:** GIFs and Greek error explanations must work correctly on his
  PC; the next step only after he has tried it and hears "I am sure".
- **CAM animations:** more colour contrast (darker stock edge and tool, stronger path colour, darker labels).
- **Question for him:** which cutters (flat/ball/V-bit) and materials (wood/alu/plastic) he uses, so the
  examples match his work.
- **Tool libraries → their own repository** (his request 2026-10-20). Not WikiTips work any more; the facts
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

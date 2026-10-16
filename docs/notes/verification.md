# Fact check of the CAM field help (2026-10-16)

Every claim in `content/fields_el.json` and in the CAM animations, with the sources checked.
Rule: FreeCAD source/wiki first, then the controller documentation (LinuxCNC = Marios's post),
then vendor documentation; forum posts only as supporting evidence. Update this when a text changes.

| Claim (short) | Verdict | Sources |
|---|---|---|
| Clearance Height = clear clamps/obstructions; Safe Height = rapids allowed above, feed below; space for clamps between them | ✔ | FreeCAD source tooltips (Path/Op/Gui/Base.py, 26.3); FreeCAD wiki CAM_Profile / CAM_Pocket_Shape "Visual reference for Depth properties" (wiki/File/Path-DepthsAndHeights.gif) |
| Start Depth = top of material, Final Depth = lowest Z, Finish Depth = thickness of the last level, Step Down = depth per layer | ✔ | same as above |
| Final Depth = Start Depth → nothing is cut | ✔ | Langmuir forum (Fusion Bottom = Top); follows from the definitions |
| Fusion names: Clearance height, Retract height, Feed height, Top height, Bottom height | ✔ | help.autodesk.com Fusion CAM pages MFG-REF-*-HEIGHT |
| Other Fusion names (Optimal load, Maximum stay-down distance, cycle types, Drill tip through bottom, Pass extension, Stock offset, Sideways compensation, Conventional milling) | ~ from Claude's knowledge of Fusion's UI; not every page fetched | verify when possible |
| Climb: tooth enters thick, leaves thin; preferred on rigid/ball-screw machines; conventional for backlash | ✔ | Hurco cutter-compensation doc; Model Engineer "CNC milling with Mach3 part 4"; Datron/CTE definitions (via search) |
| M3 spindle, outside contour clockwise = climb (G41 = climb) | ✔ after a conflict | Hurco; Machmotion; "Appendix B Cutter Radius Compensation" (G41 → clockwise round a part); LinuxCNC g-code.adoc defines G41 = left of path. One search summary claimed the opposite: rejected (own vector check + 3 sources) |
| Step Down: start with half the tool diameter, up to 1× in soft wood on a rigid machine | ✔ | Amana Tool plunge chart (1×D); MIT feeds/speeds reference; maker tutorial (½·D first try); VCarve tutorial (≤ ½·D) |
| Plunge (vertical feed) below half of the horizontal feed | ✔ | MIT feeds & speeds "Plunge Rate" page; woodworking blog |
| Step Over: roughing 40–50 %, finer finish 10–25 %; too big leaves material | ✔ | FreeCAD Pocket default 50 %; Kiri:Moto help (">0.49 may leave uncut areas"); VCarve tutorial (1/10–1/3 for pockets) |
| Adaptive: small step over (10–20 %) with deeper step down | ✔ | Fusion help (adaptive varies stepover, climb only); common practice |
| Pocket patterns ZigZag/Offset/ZigZagOffset/Line/Grid; Facing ZigZag/Bidirectional/Directional/Spiral and what they do | ✔ | FreeCAD 26.3 source (PocketBase.py, MillFacing.py, Path/Base/Generator/*_facing.py docstrings) |
| Retract threshold = stay down for repositioning below this distance, 0 = off | ✔ | FreeCAD wiki CAM_Pocket_Shape / CAM_Profile (26.3) |
| Extra Offset (radial stock to leave) = stay away from final profile, for roughing | ✔ | FreeCAD wiki CAM_Pocket_Shape |
| Use Outline = ignore holes in the base geometry | ✔ | FreeCAD source tooltip + wiki |
| Min Travel = 3D sorting when several base geometries are used | ✔ | FreeCAD wiki CAM_Pocket_Shape |
| Peck (G83): feed down by Q, rapid out to R, rapid back near the last depth, repeat | ✔ | LinuxCNC docs/src/gcode/g-code.adoc (GitHub) |
| Chip break (G73): small rapid up (default 0.254 mm) instead of full retract | ✔ | LinuxCNC g-code.adoc |
| Dwell (G82, P seconds), Feed retract (G85 feed out), G98/G99 (G99 → R plane) | ✔ | LinuxCNC g-code.adoc |
| Peck retract R is not the operation's Retract/Safe Height | ✔ | FreeCAD 26.3 field tooltip |
| Feed rate numbers for wood | removed — machine dependent; text now says "use the cutter maker's chart" | — |

## Other CAM programs looked at (ideas only, nothing copied)
- Kiri:Moto (GridSpace/grid-apps, MIT): every operation parameter has hover help in the app
  (`web/kiri/lang/en.js`), "Animate" preview; same idea as WikiTips.
- Fabex (ex-BlenderCAM, pppalain/blendercam, GPL): strategies documented with one picture each;
  terms Skin (= stock to leave), Bridges (= tabs), Overcuts (= dogbones).
- LinuxCNC docs: canned-cycle behaviour (above).
- Fusion 360 help, SolidWorks animated tooltips, Onshape two-stage tooltips (memory.md).
- Not reachable from the cloud container: linuxcnc.org, camotics.org, docs.grid.space,
  docs.carbide3d.com, estlcam.de, vectric.com (DNS/proxy). Their GitHub sources were used instead
  where they exist. CAMotics/jscut/bCNC repos reachable but not yet read.

# Sketcher help (content/commands_el.json), checked 2026-10-16

Source for every row: the FreeCAD wiki page of the command (26.3 text, from the Reqrefusion mirror),
"Usage" section. FreeCAD has two ways to start a constraint: tool first ("continue mode", the
order often matters) or selection first ("run-once mode", usually any order). Our "Πώς επιλέγεις"
describes tool-first, the way the animations show it.

| Command | Checked statement | Verdict |
|---|---|---|
| ConstrainSymmetric | tool first: two points, then the symmetry point/line, in that order; select first: two points + line in any order | ✔ wiki |
| ConstrainHorVer | line or two points; horizontal or vertical, whichever is closest | ✔ wiki |
| ConstrainParallel | two lines; select-first allows more lines | ✔ wiki |
| ConstrainPerpendicular | two edges (one a line); also point+2 edges | ✔ wiki |
| ConstrainTangent | two edges; two lines → collinear; endpoints → joined + tangent | ✔ wiki |
| ConstrainEqual | same type of edges; several with select-first | ✔ wiki |
| ConstrainCoincidentUnified | two points join; point+edge → on the edge; two circles → concentric | ✔ wiki |
| ConstrainLock | one point → H+V dimensions from the origin; several points → from the LAST point | ✔ wiki (our first text said "first point": corrected) |
| Dimension | context-sensitive; M cycles types; the 2nd click position chooses horizontal/vertical/distance | ✔ wiki |
| ConstrainAngle | two lines, or one line vs. X axis (select first), or arc aperture; negative value reverses | ✔ wiki |
| CreateRectangle | M modes, U rounded corners, J frame | ✔ wiki; shortcut G,R from the 26.3 tooltip |
| CreateCircle / CreateArc | M → 3 rim points | ✔ wiki |
| CreatePolyline | M = next segment arc, F = fillet option, close by snapping to the start, right click/Esc = open | ✔ wiki |
| Trimming | no pre-selection; hold-and-drag; constraints transferred | ✔ wiki |
| CreateFillet | no pre-selection; M = chamfer; radius from the shortest edge (corner pick) or from the first click (two edges) | ✔ wiki (first text said "depends where you click": made exact) |
| ToggleConstruction | selection → toggles geometry; no selection → toggles creation mode | ✔ wiki |
| Symmetric of the two ends of an already horizontal line about the V axis is redundant | seen in our own scripted test (orange = redundant); NOT checked in the GUI tool → not written in the help | — |

Layout idea (numbered steps under the animation, "how to select" / "where useful" / tip boxes,
shortcut badge) came from a screenshot of another program's help (MDJ Works) shown by Marios;
drawn in our own colours, nothing copied.

# Part / Part Design help, checked 2026-10-16 (FreeCAD 26.3 wiki pages)

| Command | Checked statement | Verdict |
|---|---|---|
| Part_Cut | "the last one being subtracted from the first one" → order matters | ✔ wiki |
| Part_Fuse / Part_Common | two (or more for Fuse) shapes; Common = intersection | ✔ wiki |
| Part_Section | intersection wires/points; "selection order has no impact on the result" | ✔ wiki |
| PartDesign_Mirrored / Linear / Polar | select feature(s), parameters (plane, axis, Length, Occurrences) in the task panel; Linear Length = first to last occurrence, Occurrences include the original | ✔ wiki |
| PartDesign_Boolean | activate the receiving body, do not select it; Add Body, pick the other; Fuse/Cut/Common | ✔ wiki |
| PartDesign_Plane | only inside a Body; Z offset is normal to the plane | ✔ wiki |
| PartDesign_SubShapeBinder | references geometry of other bodies; using external geometry directly in a Body gives out-of-scope errors | ✔ wiki (ShapeBinder/SubShapeBinder pages) |
| PartDesign_Clone | linked copy following edits except placement, created inside a separate Body | ✔ wiki |
| Clone animation | the copy is drawn with a plain Part copy placed beside (same look as a moved clone) | visual only |

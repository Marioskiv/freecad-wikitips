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

# CAM toolbar commands (content/commands_el.json, `camcmd/` GIFs), checked 2026-10-16

Command list taken from the running FreeCAD 26.3 (toolbars Project Setup, Tool Commands, New
Operations, Path Modification + the dropdown groups). Sources: FreeCAD 26.3 wiki pages (Reqrefusion
mirror) and, where the wiki page is empty or missing, the 26.3 source (command ToolTip, property
tooltips, docstrings) in `Mod/CAM/Path/...`.

| Command | Checked statement | Source |
|---|---|---|
| CAM_Job | Job = models, stock, tool controllers, setup sheet, output/post-processor; tabs General/Output/Setup/Tools/Workplan; a selected element becomes the Model | wiki CAM_Job |
| CAM_Sanity | standalone HTML report (part, run summary/run time, stock, tools, output, coolant, fixtures, squawks); written next to the Job output file | wiki CAM_Sanity |
| CAM_Post / PostSelected | G-code in the controller's dialect via the post-processor; PostSelected = "Post Processes the selected operations" | wiki CAM_Post; source Post/Command.py |
| CAM_Inspect | shows the internal FreeCAD G-code dialect of an operation (not the post output) | wiki CAM_Inspect |
| CAM_SelectLoop | select one edge, the rest of the loop is added | wiki CAM_SelectLoop |
| CAM_OpActiveToggle | inactive op: greyed, no path shown, ignored by Inspect and Post | wiki CAM_OpActiveToggle |
| CAM_SimulatorGL / Simulator | GL = separate window, faster; legacy = in the 3D view and "only uses the standard end mill" | wiki CAM_SimulatorGL, CAM_Simulator, CAM_Adaptive note |
| CAM_ToolBitDock | double click a tool bit = new tool controller in the Job | wiki CAM_ToolBitDock |
| CAM_Profile | no selection = whole model (Contour); faces / edges; check Final Depth. Selecting only the TOP face leaves Final Depth at that face's height (nothing is cut) | wiki CAM_Profile ("manually set the Final Depth" for top edges); seen in our recording: top-face profile path stayed at Z = 15 of a 15 mm plate, whole-model contour went to Z = 0 |
| CAM_Pocket_Shape | select the pocket bottom; walls if the pocket goes through | wiki CAM_Pocket_Shape |
| CAM_MillFacing | "machine the top surface of stock"; works on the Job stock, no base geometry | source Op/Gui/MillFacing.py tooltip, Op/MillFacing.py (uses self.stock) |
| CAM_Helix | helical G2/G3, concentric passes by Step Over; select hole edge or wall | wiki CAM_Helix |
| CAM_Adaptive | engagement never exceeds a maximum; deactivate with Toggle while editing | wiki CAM_Adaptive |
| CAM_Slot | centre-line path; no lateral offset; faces/edges, two vertices or Custom Points | wiki CAM_Slot |
| CAM_Drilling | faces selected before the command are ignored for the initial hole list; Peck, Dwell | wiki CAM_Drilling |
| CAM_ThreadMilling | passes between minor and major diameter (tool radius subtracted); separate "ClearanceOp" clears the inside | source Op/ThreadMilling.py (wiki page empty) |
| CAM_Engrave | follows the lines of a ShapeString / flat 2D geometry | wiki CAM_Engrave |
| CAM_Vcarve | centre line (Voronoi), depth from the inscribed circle and the V angle; needs faces | wiki CAM_Vcarve |
| CAM_Deburr | W = chamfer width, h = extra depth of the tip | wiki CAM_Deburr Options |
| CAM_Pocket3D | rough only; Final Depth from the geometry; finish with ball + 3D Surface | wiki CAM_Pocket3D |
| CAM_Surface / Waterline | need OpenCamLib AND the preference "Enable OCL dependent features" (CAM → Advanced; parameter EnableAdvancedOCLFeatures). The wiki also asks for "experimental features": in the 26.3 source that flag only adds Planar/Rotary Surface. Verified in the test FreeCAD: with opencamlib installed the buttons appear only after setting the preference | source InitGui.py (26.3); wiki CAM_Surface, CAM_Waterline |
| CAM_OperationCopy | `copyObject` of the op and its dressups, added to the same Job: an independent copy. NOTE: the wiki page "CAM OperationCopy" redirects to "CAM Copy" (an older *linked* copy command) — the 26.3 source is what counts | source PathCommands.py `_CopyOperation` |
| CAM_SimpleCopy | non-parametric copy; 26.3 can combine several ops | wiki CAM_SimpleCopy |
| CAM_Array | repeats a path at an interval; properties in Data after Apply | wiki CAM_Array |
| Dressups | Dogbone (inside corners of profile/contour, interlocking parts), Tag (hold the part, break off + file), DragKnife (offset blade: extensions + corner actions), LeadInOut (styles Arc/Tangent/Perpendicular…), RampEntry (Angle), Boundary (box/cylinder/solid, Inside) | wiki pages of each dressup + Dressup/Gui sources |
| AxisMap, ZCorrect, Mirror, PlungeMilling, DressupArray | wiki pages empty: AxisMap "remaps one axis to another, e.g. Y→A for a 4th axis rotary", Radius = radius of the wrapped axis; ZCorrect = bilinear Z correction from a LinuxCNC G38 probe file; Mirror "Add path from base operation"; PlungeMilling: distance between passes, optional drilling cycles, peck, dwell; DressupArray types Linear1D/Linear2D/Polar | source docstrings / property tooltips |

GIFs: recorded in a real FreeCAD 26.3 (`tools/gifs/cam_rec.py`, real CAM objects and real toolpaths;
G-code cards show the real Inspect commands and the real linuxcnc post output). Drawn (not
recordable here): CAM_DressupAxisMap, CAM_DressupZCorrect; Surface/Waterline are recorded with
OpenCamLib 2023.01.11 (conda-forge) installed in the test FreeCAD
(`tools/gifs/cam_cmd_gifs.py`). The Simulator GIFs show material removal made with Part booleans
along the real path (same idea as the simulator, not a screenshot of its window).

# CAM dressup panel fields (content/fields_el.json, 2026-10-17)

Field names read from the 26.3 panel files (`:/panels/DogboneEdit.ui`, HoldingTagsEdit, DressUpLeadInOutEdit,
DragKnifeEdit, DressupPathBoundary, AxisMapEdit, ZCorrectEdit, read out of the running FreeCAD) and
checked in a real FreeCAD by tests/run_freecad_tests.sh (each dressup panel, every field: popup OK).

| Field | Statement | Source |
|---|---|---|
| Dogbone style / incision / custom / bones | Dogbone = shortest path to cover the corner, T-bone = extend one direction; incision adaptive / fixed (R·(2/√2−1) dogbone, R T-bone) / custom; 26.3: custom caps adaptive; greyed bone = already dressed | DogboneEdit.ui tooltips; wiki CAM_DressupDogbone |
| Tag width / height / angle / radius / min / max | as in the wiki options; height may come out smaller if width and angle don't allow it; tags on convex parts are easier to file | HoldingTagsEdit.ui tooltips; wiki CAM_DressupTag |
| Lead in/out style, radius/length, angle (1..90), extend (only Arc/Line/Perpendicular/Tangent), offset (move start/end point), rapid plunge (G0), retract threshold | LeadInOut.py property tooltips (26.3) |
| Drag knife filter angle / offset / pivot height | pivot: the point should stay slightly in the material, higher for thicker material | wiki CAM_DressupDragKnife; DragKnifeEdit.ui |
| Boundary shape, extents (negative values to cut part of a path), Create Box sets only the size, "Constrained to inside" | wiki CAM_DressupPathBoundary; DressupPathBoundary.ui |
| Axis map radius / mapping / reverse; Z correct probe file (LinuxCNC G38; CAM Probe makes a G38.2 grid) | AxisMap.py, ZCorrect.py, Op/Probe.py |
| Dressup animations (dogbone_style, tag_shape, lead_style, dragknife, boundary_inside) | geometry from the statements above; our own drawings |

# Greek for the remaining Sketcher / Part Design / Part toolbar commands (2026-10-17)

128 entries (every visible toolbar button of the four workbenches now has Greek help).
Source of every row: the FreeCAD 26.3 wiki page of the command (Description + Usage + Notes), read
from the Reqrefusion mirror. "⚠" lines are only written when the wiki states the point, e.g.:
Split / Extend take no pre-selection; Translate / Rotate / Scale / Offset / Symmetry select first;
ValidateSketch not in edit mode; CarbonCopy keeps dimensions linked; ConstrainGroup ignores member
constraints; CheckGeometry: select the whole object; Part Scale is relative to the global origin;
Part Compound with touching pieces is invalid for booleans; Cone: one radius 0 for a full cone;
Fillet/Chamfer: a face or the feature selects all its edges; Body with a selected solid → Base Feature.
Entries without our own animation keep the wiki picture; the footer then credits it (CC-BY 3.0).

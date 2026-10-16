# Session log

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

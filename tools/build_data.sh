#!/usr/bin/env bash
# Rebuild data/commands.json and data/img/ from the FreeCAD wiki.
# Needs: python3, beautifulsoup4, lxml, pillow, cairosvg, git.
# Downloads ~2 GB (offline wiki) into a work folder outside the repo.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mkdir -p "${WORK:-$REPO/../wikitips-build}" && cd "${WORK:-$REPO/../wikitips-build}" && pwd)"
mkdir -p "$WORK"
cd "$WORK"
# 1) current wiki as HTML (primary source, updated daily)
[ -d FreeCAD-Documentation-html ] || git clone --depth 1 https://github.com/Reqrefusion/FreeCAD-Documentation-html
# 2) older markdown export (fallback for commands that left the wiki)
if [ ! -d FreeCAD-documentation ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/FreeCAD/FreeCAD-documentation
  (cd FreeCAD-documentation && git sparse-checkout set --no-cone '/wiki/*.md')
fi
python3 -I "$REPO/tools/extract_wiki_html.py" FreeCAD-Documentation-html/wiki new.json
python3 -I "$REPO/tools/extract_wiki_md.py" FreeCAD-documentation/wiki old.json
# fetch only the images the fallback entries need
(cd FreeCAD-documentation && sed "s#^#/wiki/images/#" "$WORK/old.json.images.txt" | (echo '/wiki/*.md'; cat) | git sparse-checkout set --no-cone --stdin)
rm -rf "$REPO/data/img" && mkdir -p "$REPO/data/img"
python3 -I "$REPO/tools/merge_data.py" new.json old.json merged_raw.json
python3 - <<'PY'
import json
m = json.load(open("merged_raw.json")); n = json.load(open("new.json"))
json.dump({k: v for k, v in m.items() if k in n}, open("part_new.json", "w"), ensure_ascii=False)
json.dump({k: v for k, v in m.items() if k not in n}, open("part_old.json", "w"), ensure_ascii=False)
PY
python3 -I "$REPO/tools/convert_images.py" FreeCAD-Documentation-html/wiki/File part_new.json "$REPO/data/img"
python3 -I "$REPO/tools/convert_images.py" FreeCAD-documentation/wiki/images part_old.json "$REPO/data/img"
python3 -I "$REPO/tools/merge_data.py" part_new.json part_old.json "$REPO/data/commands.json"

"""Merge the current wiki data (primary) with the older markdown data (fallback
for commands no longer on the wiki). usage: merge_data.py new.json old.json out.json"""
import json
import sys

new = json.load(open(sys.argv[1], encoding="utf-8"))
old = json.load(open(sys.argv[2], encoding="utf-8"))
for k, v in old.items():
    if k not in new and not k.startswith(("Drawing_", "Sandbox_")):
        new[k] = v
json.dump(new, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(new), "commands,", sum(1 for v in new.values() if v.get("i")), "with picture")

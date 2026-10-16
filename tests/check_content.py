# SPDX-License-Identifier: LGPL-2.1-or-later
"""Offline check of the hand-written help: every entry has its texts and its picture.

    python3 tests/check_content.py        → prints OK or the problems, exit code 1 on problems
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "content", "img")


def main():
    bad = []
    for fname, need in (("commands_el.json", ("t", "d")), ("fields_el.json", ("t", "d"))):
        data = json.load(open(os.path.join(ROOT, "content", fname), encoding="utf-8"))
        for key, e in data.items():
            if key.startswith("_"):
                continue
            for k in need:
                if not e.get(k):
                    bad.append("%s %s: no '%s'" % (fname, key, k))
            if e.get("i") and not os.path.isfile(os.path.join(IMG, e["i"])):
                bad.append("%s %s: missing picture %s" % (fname, key, e["i"]))
            if len(e.get("d", "")) > 160:
                bad.append("%s %s: 'd' longer than 160 characters (keep it short)" % (fname, key))
    print("\n".join(bad) if bad else "OK content")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

# SPDX-License-Identifier: LGPL-2.1-or-later
"""Animations for the fields inside the CAM dressup task panels.

    python3 tools/gifs/cam_dressup_gifs.py content/img/cam [names...]

Our own drawings (same palette as cam_gifs.py). The geometry follows FreeCAD 26.3:
dogbone incision R*(sqrt2 - 1), T-bone incision R (DogboneEdit.ui tooltip); lead-in
Arc/Perpendicular/Tangent; drag knife offset + corner swivel; tag width/height/angle/
radius (wiki CAM_DressupTag); boundary "Constrained to inside".
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import (ACTIVE, AMBER, CUT, DIM, F_LABEL, F_SMALL, PATH, STOCK, STOCK_EDGE,  # noqa: E402
                  Frame, lerp, save_gif)

OUT = sys.argv[1] if len(sys.argv) > 1 else "content/img/cam"
GIFS = {}


def gif(name):
    def deco(fn):
        GIFS[name] = fn
        return fn
    return deco


def polyline_points(pts, n):
    """n points evenly spaced along a polyline."""
    segs = list(zip(pts, pts[1:]))
    total = sum(math.dist(a, b) for a, b in segs) or 1.0
    out = []
    for k in range(n + 1):
        s = total * k / n
        for a, b in segs:
            L = math.dist(a, b)
            if s <= L or (a, b) == segs[-1]:
                t = 0 if L == 0 else min(1.0, s / L)
                out.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t)))
                break
            s -= L
    return out


# ===========================================================================
# Dogbone: style and incision (top view of one inside corner)
# ===========================================================================
CX, CY = 110, 62          # the sharp inside corner of the pocket (material up and left)
R = 24                    # tool radius
PX1, PY1 = 330, 200       # pocket goes right and down


def dogbone_base(f, swept, path):
    f.rect(16, 14, 400, 214, fill=STOCK, outline=STOCK_EDGE)
    for (x, y) in swept:                                       # what the tool really cleared
        f.circle(x, y, R, fill=CUT)
    f.line([(CX, PY1), (CX, CY), (PX1, CY)], (30, 41, 59), 2)  # the drawn (sharp) inside corner
    f.text(CX - 8, PY1 - 4, "σχέδιο:", fill=(30, 41, 59), font=F_SMALL, anchor="rs")
    f.text(CX - 8, PY1 + 9, "κοφτερή γωνία", fill=(30, 41, 59), font=F_SMALL, anchor="rs")
    if len(path) > 1:
        f.line(path, PATH, 2)


def corner_path(bone):
    """Tool centre: down the left wall, into the bone, back out, along the top wall."""
    a = (CX + R, PY1 - R)
    c = (CX + R, CY + R)
    b = (PX1 - R, CY + R)
    if bone is None:
        return [a, c, b]
    return [a, c, bone, c, b]


def dogbone_variant(fr, bone, caption, label):
    pts = corner_path(bone)
    run = polyline_points(pts, 30)
    for k in range(1, len(run)):
        f = Frame()
        dogbone_base(f, run[:k + 1], run[:k + 1])
        f.tool_top(run[k][0], run[k][1], R, angle=k * 0.5)
        f.caption(caption)
        fr.append((f, 55))
    f = Frame()
    dogbone_base(f, run, run)
    if bone is None:
        f.tag(CX + 6, CY - 4, "μένει υλικό στη γωνία", fill=ACTIVE, anchor="ls")
        f.circle(CX + 7, CY + 7, 5, outline=ACTIVE, width=2)
    else:
        f.tag(CX + R + 30, CY + R + 40, label, fill=ACTIVE)
    f.caption(caption)
    fr.append((f, 1600))


@gif("dogbone_style")
def dogbone_style():
    fr = []
    d = R * math.sqrt(2) - R                     # dogbone incision along the bisector
    dogbone_variant(fr, None, "Χωρίς dressup: στρογγυλή γωνία", "")
    dogbone_variant(fr, (CX + R - d / math.sqrt(2), CY + R - d / math.sqrt(2)),
                    "Dogbone: λοξά, το πιο κοντό", "Dogbone")
    dogbone_variant(fr, (CX, CY + R), "T-bone horizontal: οριζόντια", "T-bone horizontal")
    dogbone_variant(fr, (CX + R, CY), "T-bone vertical: κάθετα", "T-bone vertical")
    return fr


# ===========================================================================
# Tag: width / height / angle / radius (side view of the bottom of a profile cut)
# ===========================================================================
ZT, ZB = 70, 186          # stock top and bottom (side view)
TX0, TX1 = 150, 250       # tag foot (Width)
TH = 46                   # tag height
ANG = 60                  # ramp angle from the horizontal, degrees (for the picture)


def tag_shape(rad=8):
    run = TH / math.tan(math.radians(ANG))
    top0, top1 = TX0 + run, TX1 - run
    pts = [(TX0, ZB), (top0, ZB - TH), (top1, ZB - TH), (TX1, ZB)]
    return pts, top0, top1


def tag_base(f, path_upto=None, tool=None):
    f.rect(20, ZT, 396, ZB, fill=STOCK, outline=STOCK_EDGE)
    pts, top0, top1 = tag_shape()
    # the cut slot seen from the side: everything is removed except the tag
    f.rect(20, ZT, 396, ZB, fill=CUT, outline=STOCK_EDGE)
    f.poly(pts, fill=STOCK, outline=STOCK_EDGE)
    f.line([(20, ZT), (396, ZT)], STOCK_EDGE, 1)
    path = [(30, ZB)] + pts + [(386, ZB)]
    if path_upto is not None:
        f.line(path_upto, PATH, 3)
    if tool is not None:
        x, y = tool
        f.endmill_side(x, y, d=18, flute_len=30)
    f.text(30, ZT - 8, "πλάγια όψη του κοψίματος", fill=DIM, font=F_SMALL, anchor="ls")
    return path


@gif("tag_shape")
def tag_anim():
    fr = []
    f0 = Frame()
    path = tag_base(f0)
    run = polyline_points(path, 50)
    for k in range(1, len(run)):
        f = Frame()
        tag_base(f, run[:k + 1], run[k])
        f.caption("Το εργαλείο ανεβαίνει πάνω από το tag")
        fr.append((f, 55))
    pts, top0, top1 = tag_shape()
    dims = [
        ("Width: φάρδος στη βάση", lambda f: (f.line([(TX0, ZB + 10), (TX1, ZB + 10)], ACTIVE, 2),
                                             f.tag((TX0 + TX1) / 2, ZB + 22, "Width", fill=ACTIVE, anchor="mm"))),
        ("Height: ύψος από τον πάτο", lambda f: (f.line([(TX1 + 26, ZB), (TX1 + 26, ZB - TH)], ACTIVE, 2),
                                                f.tag(TX1 + 34, ZB - TH / 2, "Height", fill=ACTIVE, anchor="lm"))),
        ("Angle: κλίση στις πλευρές", lambda f: (f.arc(TX0, ZB, 26, 360 - ANG, 360, ACTIVE, 2),
                                                f.tag(TX0 - 10, ZB - 16, "Angle", fill=ACTIVE, anchor="rm"))),
        ("Radius: στρογγύλεμα πάνω", lambda f: (f.circle(top0, ZB - TH, 9, outline=ACTIVE, width=2),
                                               f.circle(top1, ZB - TH, 9, outline=ACTIVE, width=2),
                                               f.tag((top0 + top1) / 2, ZB - TH - 22, "Radius", fill=ACTIVE,
                                                     anchor="mm"))),
    ]
    for cap, draw in dims:
        f = Frame()
        tag_base(f, path)
        draw(f)
        f.caption(cap)
        fr.append((f, 1700))
    return fr


# ===========================================================================
# Lead-in style: Arc / Perpendicular / Tangent (top view, outside profile)
# ===========================================================================
PY = 110                  # tool centre line along the bottom wall of the part
WALL = PY - 14            # the part's wall (tool radius 14 px)
SX = 200                  # where the profile starts


def lead_base(f, pts):
    f.rect(20, 14, 396, WALL, fill=STOCK, outline=STOCK_EDGE)
    f.text(30, 30, "κομμάτι", fill=DIM, font=F_LABEL)
    f.dashed(20, PY, 396, PY, DIM, 1, 4, 4)
    if len(pts) > 1:
        f.line(pts, PATH, 3)
    f.circle(SX, PY, 4, fill=AMBER)


def lead_variant(fr, lead, caption):
    pts = lead + [(SX, PY), (360, PY)]
    run = polyline_points(pts, 44)
    for k in range(1, len(run)):
        f = Frame()
        lead_base(f, run[:k + 1])
        f.tool_top(run[k][0], run[k][1], 14, angle=k * 0.5)
        f.caption(caption)
        fr.append((f, 55))
    f = Frame()
    lead_base(f, run)
    f.tag(SX + 8, PY + 28, "αρχή", fill=AMBER)
    f.caption(caption)
    fr.append((f, 1200))


@gif("lead_style")
def lead_style():
    fr = []
    L = 70
    # quarter circle with its centre below the start point: tangent to the path where it joins
    arc = [(SX - L * math.sin(math.radians(a)), PY + L - L * math.cos(math.radians(a))) for a in range(90, -1, -6)]
    lead_variant(fr, arc, "Arc: μπαίνει με τόξο")
    lead_variant(fr, [(SX, PY + L)], "Perpendicular: κάθετα στο τοίχωμα")
    lead_variant(fr, [(SX - L - 40, PY)], "Tangent: στην ίδια ευθεία")
    return fr


# ===========================================================================
# Drag knife: offset, corner action, pivot height (top view)
# ===========================================================================
@gif("dragknife")
def dragknife():
    fr = []
    K = (250, 70)             # the sharp corner of the shape to cut
    OFF = 30                  # blade tip trails the spindle by this
    start = (60, 70)
    end = (250, 210)
    # spindle: past the corner by OFF, swivel around the corner, continue
    sw = [(K[0] + OFF * math.cos(math.radians(a)), K[1] + OFF * math.sin(math.radians(a)))
          for a in range(0, 91, 6)]
    spindle = [start, (K[0] + OFF, K[1])] + sw + [(K[0], end[1] + OFF)]
    run = polyline_points(spindle, 70)

    def blade_of(i):
        """The blade tip trails OFF behind the spindle, along the travelled path."""
        back = OFF
        j = i
        while j > 0 and back > 0:
            back -= math.dist(run[j], run[j - 1])
            j -= 1
        return run[j]

    for k in range(1, len(run)):
        f = Frame()
        f.rect(16, 14, 400, 236, fill=(250, 245, 235), outline=STOCK_EDGE)
        f.line([start, K, end], DIM, 1)                       # the drawing to cut
        cut = [blade_of(i) for i in range(k + 1)]
        f.line(cut, ACTIVE, 3)                                 # what the blade cut
        f.line(run[:k + 1], PATH, 1.5)                         # spindle centre
        sx, sy = run[k]
        bx, by = blade_of(k)
        f.line([(sx, sy), (bx, by)], AMBER, 2)
        f.circle(sx, sy, 7, fill=(71, 85, 105))
        f.circle(bx, by, 4, fill=ACTIVE)
        on_corner = OFF - 1 <= math.dist((sx, sy), K) <= OFF + 1 and sx > K[0]
        if on_corner and sy > K[1] + 2:
            f.tag(K[0] + OFF + 12, K[1] + 20, "σηκώνεται (Pivot Height) και γυρίζει", fill=ACTIVE)
        f.caption("Η μύτη σέρνεται πίσω κατά Offset")
        fr.append((f, 60))
    f = fr[-1][0]
    f.tag(110, 40, "Offset = απόσταση μύτης-άξονα", fill=AMBER)
    f.caption("Κοφτερή γωνία χάρη στη στροφή")
    fr.append((f, 2200))
    return fr


# ===========================================================================
# Boundary: constrained to inside / outside (top view)
# ===========================================================================
@gif("boundary_inside")
def boundary_inside():
    fr = []
    BX0, BY0, BX1, BY1 = 150, 60, 300, 180
    lines = []
    y = 40
    while y <= 200:
        lines.append(y)
        y += 16

    def scene(inside, k):
        f = Frame()
        f.rect(20, 26, 396, 214, fill=STOCK, outline=STOCK_EDGE)
        for i, yy in enumerate(lines[:k]):
            segs = [(40, BX0), (BX0, BX1), (BX1, 376)]
            for x0, x1 in segs:
                kept = (BX0 <= (x0 + x1) / 2 <= BX1 and BY0 <= yy <= BY1) == inside
                f.line([(x0, yy), (x1, yy)], ACTIVE if kept else (203, 213, 225), 3 if kept else 1.5)
        f.dashed(BX0, BY0, BX1, BY0, AMBER, 2)
        f.dashed(BX1, BY0, BX1, BY1, AMBER, 2)
        f.dashed(BX1, BY1, BX0, BY1, AMBER, 2)
        f.dashed(BX0, BY1, BX0, BY0, AMBER, 2)
        f.tag(BX0 + 4, BY0 - 10, "όριο", fill=AMBER, anchor="lm")
        f.caption("☑ inside: κρατάει μέσα" if inside else "☐ inside: κρατάει έξω")
        return f

    for inside in (True, False):
        for k in range(1, len(lines) + 1):
            fr.append((scene(inside, k), 70))
        fr.append((scene(inside, len(lines)), 1800))
    return fr


def main():
    only = set(sys.argv[2:])
    for name, fn in GIFS.items():
        if only and name not in only:
            continue
        p = save_gif(fn(), os.path.join(OUT, name + ".gif"))
        print("%-22s %6.1f KB" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()

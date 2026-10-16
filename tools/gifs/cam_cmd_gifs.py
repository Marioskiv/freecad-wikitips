# SPDX-License-Identifier: LGPL-2.1-or-later
"""Drawn animations for the CAM commands that cannot be recorded in our test FreeCAD.

    python3 tools/gifs/cam_cmd_gifs.py content/img/camcmd [names...]

3D Surface / Waterline need OpenCamLib (not in the conda build, and Marios's FreeCAD
shows them only after enabling the OCL features); Axis Map needs a 4th axis and
Z Correct a probe file. Our own drawings, same palette as cam_gifs.py.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import (ACTIVE, CUT, DIM, F_LABEL, F_SMALL, H, PATH, SHANK, STOCK, STOCK_EDGE, TOOL,  # noqa: E402
                  TOOL_HI, W, Frame, ease, lerp, save_gif)

OUT = sys.argv[1] if len(sys.argv) > 1 else "content/img/camcmd"
GIFS = {}


def gif(name):
    def deco(fn):
        GIFS[name] = fn
        return fn
    return deco


X0, X1 = 30, 300
BASE_Y = 196


def surf(x):
    """A wavy 3D surface seen from the side (y of the surface at x)."""
    t = (x - X0) / (X1 - X0)
    return 128 - 26 * math.sin(t * math.pi * 1.6) - 10 * math.sin(t * math.pi * 5.0 + 0.6)


def part_side(f, fn=surf, x0=X0, x1=X1):
    pts = [(x, fn(x)) for x in range(int(x0), int(x1) + 1, 2)]
    f.poly([(x0, BASE_Y)] + pts + [(x1, BASE_Y)], fill=(203, 213, 225), outline=STOCK_EDGE, width=1)


def ball_tool(f, cx, cy, r=9, length=40):
    """Ball end mill from the side: ball centre at (cx, cy)."""
    f.metal(cx - r, cy - length, cx + r, cy, TOOL)
    f.d.pieslice([(cx - r) * 2, (cy - r) * 2, (cx + r) * 2, (cy + r) * 2], 0, 180, fill=TOOL)
    f.metal(cx - r * 0.7, cy - length - 14, cx + r * 0.7, cy - length, SHANK)
    f.circle(cx, cy, 1.6, fill=TOOL_HI)


def drop_y(fn, cx, r=9, x0=X0, x1=X1):
    """Drop cutter: lowest ball centre that touches the surface (what OpenCamLib computes)."""
    best = 1e9
    for k in range(-20, 21):
        x = cx + r * k / 20
        if x < x0 or x > x1:
            continue
        dy = math.sqrt(max(0.0, r * r - (x - cx) ** 2))
        best = min(best, fn(x) - dy)
    return best


@gif("CAM_Surface")
def surface():
    fr = []
    r = 9
    xs = list(range(X0 + 4, X1 - 3, 6))
    trail = []
    for i, cx in enumerate(xs):
        cy = drop_y(surf, cx, r)
        trail.append((cx, cy + r))
        f = Frame()
        part_side(f)
        if len(trail) > 1:
            f.line(trail, PATH, 2)
        ball_tool(f, cx, cy, r)
        f.caption("Η μπίλια ακολουθεί την 3D επιφάνεια")
        fr.append((f, 70))
    f = Frame()
    part_side(f)
    f.line(trail, PATH, 2)
    f.caption("Φινίρισμα · θέλει OpenCamLib")
    fr.append((f, 2200))
    return fr


DC, DR = 105, 72          # dome (side view): centre x, radius


def dome(x):
    dx = x - DC
    return BASE_Y - max(0.0, math.sqrt(max(0.0, DR * DR - dx * dx)) * 1.15 - 4)


@gif("CAM_Waterline")
def waterline():
    """Side view (left) and top view (right): one closed loop around the part per Z level."""
    fr = []
    levels = [188, 172, 156, 140, 126]
    done = []
    TX, TY = 250, 116          # top view centre
    tr = 7                     # tool radius
    for li, zy in enumerate(levels):
        half = max(dx for dx in range(0, DR + 1) if dome(DC + dx) <= zy + 0.5) + tr
        for k in range(15):
            a = 2 * math.pi * k / 14
            f = Frame()
            part_side(f, dome, DC - DR - 10, DC + DR + 10)
            f.text(DC, 34, "πλάγια", fill=DIM, font=F_LABEL, anchor="mm")
            f.text(TX, 34, "από πάνω", fill=DIM, font=F_LABEL, anchor="mm")
            f.circle(TX, TY, DR * 0.78, fill=(203, 213, 225), outline=STOCK_EDGE)
            for z, h in done:
                f.line([(DC - h, z), (DC + h, z)], PATH, 2)
                f.circle(TX, TY, h * 0.78, outline=PATH, width=2)
            f.dashed(DC - DR - 18, zy, DC + DR + 18, zy, ACTIVE, 1, 4, 3)
            f.tag(16, zy - 8, "Z%d" % (li + 1), fill=ACTIVE, font=F_SMALL)
            # tool on the right side of the side view, and going round in the top view
            x = DC + half
            f.metal(x - tr, zy - 38, x + tr, zy, TOOL)
            f.metal(x - tr * 0.7, zy - 52, x + tr * 0.7, zy - 38, SHANK)
            f.d.arc([(TX - half * 0.78) * 2, (TY - half * 0.78) * 2, (TX + half * 0.78) * 2, (TY + half * 0.78) * 2],
                    0, max(1, math.degrees(a)), fill=PATH, width=4)
            f.tool_top(TX + half * 0.78 * math.cos(a), TY + half * 0.78 * math.sin(a), tr)
            f.caption("Γύρω-γύρω, σε σταθερά ύψη")
            fr.append((f, 55))
        done.append((zy, half))
    fr.append((fr[-1][0], 300))
    f = Frame()
    part_side(f, dome, DC - DR - 10, DC + DR + 10)
    f.circle(TX, TY, DR * 0.78, fill=(203, 213, 225), outline=STOCK_EDGE)
    for z, h in done:
        f.line([(DC - h, z), (DC + h, z)], PATH, 2)
        f.circle(TX, TY, h * 0.78, outline=PATH, width=2)
    f.caption("Σαν ισοϋψείς χάρτη · θέλει OpenCamLib")
    fr.append((f, 2200))
    return fr


@gif("CAM_DressupAxisMap")
def axis_map():
    fr = []
    # left: flat plate with a path along Y (drawn as horizontal screen lines)
    PX0, PY0, PX1, PY1 = 24, 60, 134, 170
    lines = [PY0 + 14 + i * 16 for i in range(6)]
    CX, CY, RX, RY = 238, 115, 44, 60      # right: cylinder (side view, axis horizontal)

    def left(f, upto=None):
        f.rect(PX0, PY0, PX1, PY1, fill=STOCK, outline=STOCK_EDGE)
        for i, y in enumerate(lines):
            if upto is None or i < upto:
                f.line([(PX0 + 8, y), (PX1 - 8, y)], PATH, 2)
        f.text((PX0 + PX1) / 2, PY1 + 8, "Y", fill=ACTIVE, font=F_LABEL, anchor="mt")
        f.arrow(PX0 - 10, PY1, PX0 - 10, PY0, ACTIVE, 2, 6)

    def cyl(f, rot, upto=99):
        f.rect(CX - 70, CY - RY, CX + 70, CY + RY, fill=STOCK, outline=STOCK_EDGE)
        f.d.ellipse([(CX + 70 - 14) * 2, (CY - RY) * 2, (CX + 70 + 14) * 2, (CY + RY) * 2],
                    fill=(190, 201, 218), outline=STOCK_EDGE, width=2)
        for i in range(len(lines)):
            if i >= upto:
                continue
            ang = rot + i * 0.42
            s = math.sin(ang)
            if math.cos(ang) < 0:
                continue            # behind the cylinder
            y = CY - RY * s
            f.line([(CX - 62, y), (CX + 62, y)], PATH, 2)
        f.text(CX, CY + RY + 8, "A (περιστροφή)", fill=ACTIVE, font=F_LABEL, anchor="mt")
        f.arc(CX + 70, CY, RY * 0.55, 200, 330, ACTIVE, 3)
        f.arrow(CX + 70 + RY * 0.55 * math.cos(math.radians(320)), CY + RY * 0.55 * math.sin(math.radians(320)),
                CX + 70 + RY * 0.55 * math.cos(math.radians(334)), CY + RY * 0.55 * math.sin(math.radians(334)),
                ACTIVE, 3, 8)

    for k in range(16):
        f = Frame()
        left(f, upto=int(1 + k * 6 / 15))
        f.caption("Διαδρομή στο επίπεδο: κινείται στον Y")
        fr.append((f, 90))
    for k in range(40):
        f = Frame()
        left(f)
        t = ease(min(1.0, k / 10))
        f.arrow(146, 115, lerp(146, 168, t), 115, ACTIVE, 3, 9)
        cyl(f, -0.9 + k * 0.06)
        f.caption("Y → A: τυλίγεται γύρω από κύλινδρο")
        fr.append((f, 70))
    return fr


@gif("CAM_DressupZCorrect")
def z_correct():
    fr = []

    def bowed(x):
        t = (x - X0) / (X1 - X0)
        return 112 + 30 * t - 16 * math.sin(t * math.pi)      # tilted + bowed plate top (exaggerated)

    probes = list(range(X0 + 15, X1, 45))
    depth = 6

    def scene(f, show_probe=0, corrected=False, path_upto=None):
        part_side(f, bowed)
        flat = 118 + depth
        if not corrected:
            pts = [(x, flat) for x in range(X0, X1 + 1, 4)]
        else:
            pts = [(x, bowed(x) + depth) for x in range(X0, X1 + 1, 4)]
        if path_upto is not None:
            pts = pts[:path_upto]
        if len(pts) > 1:
            f.line(pts, ACTIVE if not corrected else PATH, 2)
        for i, x in enumerate(probes[:show_probe]):
            f.circle(x, bowed(x), 3.5, fill=(16, 185, 129), outline=SHANK)

    for k in range(1, 30):
        f = Frame()
        scene(f, path_upto=k * 3)
        f.caption("Ίσια διαδρομή: αλλού βαθιά, αλλού αέρας")
        fr.append((f, 60))
    f = Frame()
    scene(f)
    f.tag(52, 100, "αέρας", fill=ACTIVE)
    f.tag(232, 150, "πολύ βαθιά", fill=ACTIVE)
    f.caption("Ίσια διαδρομή: αλλού βαθιά, αλλού αέρας")
    fr.append((f, 1600))
    for k in range(len(probes) + 1):
        f = Frame()
        scene(f, show_probe=k)
        f.caption("Το probe μετράει την επιφάνεια")
        fr.append((f, 260))
    for k in range(1, 30):
        f = Frame()
        scene(f, show_probe=len(probes), corrected=True, path_upto=k * 3)
        f.caption("Ζ Correct: ίδιο βάθος παντού")
        fr.append((f, 60))
    fr.append((fr[-1][0], 2000))
    return fr


def main():
    only = set(sys.argv[2:])
    for name, fn in GIFS.items():
        if only and name not in only:
            continue
        p = save_gif(fn(), os.path.join(OUT, name + ".gif"))
        print("%-28s %6.1f KB" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()

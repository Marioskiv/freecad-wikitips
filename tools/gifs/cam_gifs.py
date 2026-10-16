# SPDX-License-Identifier: LGPL-2.1-or-later
"""Teaching animations for the fields of FreeCAD CAM task panels.

    python3 tools/gifs/cam_gifs.py content/img/cam

Every GIF is our own drawing (ideas only from how other CAM programs explain
these settings). Example situation: flat end mill 6 mm, wood/MDF, pocket 12 mm deep.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import (ACTIVE, BG, CAP_H, CUT, DIM, F_BIG, F_LABEL, F_SMALL, FEED, H, LEFT, PART,  # noqa: E402
                  PART_EDGE, PATH, RAPID, SHANK, STOCK, STOCK_EDGE, TOOL, W, Frame,
                  ease, lerp, save_gif)

OUT = sys.argv[1] if len(sys.argv) > 1 else "content/img/cam"
GIFS = {}


def gif(name):
    def deco(fn):
        GIFS[name] = fn
        return fn
    return deco


# ===========================================================================
# side view: heights and depths
# ===========================================================================
X0, X1 = 22, 292          # stock
PX0, PX1 = 120, 232       # pocket
PXL = 300                 # label column
MM = 5.0                  # px per mm
TOP_Y = 120               # Z = 0 (top of stock = Start Depth)
LEVELS = {"clear": 12.0, "safe": 4.0, "start": 0.0, "final": -12.0}
NAMES = {"clear": "Clearance Height", "safe": "Safe Height", "start": "Start Depth",
         "final": "Final Depth"}
TOOL_D = 18
CLAMP = (34, 64, TOP_Y - 8 * MM)   # x0, x1, top y of the clamp (8 mm high)


def zy(z):
    return TOP_Y - z * MM


class Side:
    """State of the side-view scene: what is cleared, where the tool is."""

    def __init__(self):
        self.cleared = []          # list of (x0, z_top, x1, z_bottom)
        self.trail = []            # list of (pts, color)

    def frame(self, active=(), tx=None, tz=None, caption="", warn=False, extra=None,
              show_levels=("clear", "safe", "start", "final"), drill=False):
        f = Frame()
        # stock + clamp
        f.rect(X0, zy(0), X1, zy(-14), fill=STOCK, outline=STOCK_EDGE, width=1)
        for x0, zt, x1, zb in self.cleared:
            f.rect(x0, zy(zt), x1, zy(zb), fill=BG)
        cx0, cx1, cty = CLAMP
        f.poly([(cx0, zy(0)), (cx1, zy(0)), (cx1, cty), (cx0 + 6, cty)], fill=(95, 95, 105))
        f.text((cx0 + cx1) / 2, cty - 4, "σφιγκτήρας", fill=DIM, font=F_SMALL, anchor="md")
        # levels
        for key in show_levels:
            y = zy(LEVELS[key])
            on = key in active
            col = ACTIVE if on else DIM
            f.dashed(8, y, PXL - 6, y, col, 2 if on else 1, 6, 4)
            f.text(PXL, y, NAMES[key], fill=col, font=F_LABEL if on else F_SMALL, anchor="lm")
        for pts, col in self.trail:
            f.line(pts, col, 1.5)
        if extra:
            extra(f)
        if tx is not None:
            if drill:
                f.drill_side(tx, zy(tz))
            else:
                f.endmill_side(tx, zy(tz), d=TOOL_D, flute_len=26)
        if caption:
            f.caption(caption, warn)
        return f


def move(scene, frames, x0, z0, x1, z1, n, color, cut=None, **kw):
    """Tool moves in a straight line; leaves a coloured trail; optional cutting."""
    for i in range(n + 1):
        t = ease(i / n) if color == RAPID else i / n
        x, z = lerp(x0, x1, t), lerp(z0, z1, t)
        trail = scene.trail + [([(x0, zy(z0)), (x, zy(z))], color)]
        if cut is not None:   # cut = (z_top, z_bottom): clears from pocket start to tool edge
            ztop, zb = cut
            right = min(PX1, x + TOOL_D / 2)
            scene.cleared.append((PX0, ztop, right, zb))
        saved, scene.trail = scene.trail, trail
        frames.append((scene.frame(tx=x, tz=z, **kw), kw.pop("_hold", 70)))
        scene.trail = saved
        if cut is not None:
            scene.cleared.pop()
    if cut is not None:
        scene.cleared.append((PX0, cut[0], PX1, cut[1]))
    scene.trail.append(([(x0, zy(z0)), (x1, zy(z1))], color))


def hold(frames, f, ms):
    frames.append((f, ms))


LX, RX = PX0 + TOOL_D / 2, PX1 - TOOL_D / 2   # tool centre limits inside the pocket


def pocket_run(active, captions, layers=(-4.0, -8.0, -11.0, -12.0), start_x=50, extra=None):
    s = Side()
    if extra:
        _frame = s.frame
        s.frame = lambda *a, **k: _frame(*a, extra=extra, **k)
    fr = []
    cs = lambda k: captions.get(k, captions.get("*", ""))  # noqa: E731
    hold(fr, s.frame(active, start_x, LEVELS["clear"], cs("intro")), 1600)
    move(s, fr, start_x, LEVELS["clear"], LX, LEVELS["clear"], 10, RAPID, active=active, caption=cs("traverse"))
    move(s, fr, LX, LEVELS["clear"], LX, LEVELS["safe"], 6, RAPID, active=active, caption=cs("down_rapid"))
    top = 0.0
    for i, z in enumerate(layers):
        key = "finish" if (i == len(layers) - 1 and len(layers) > 1 and top - z < 2) else "layer"
        cap = cs(key).format(n=i + 1, N=len(layers), dz=round(top - z, 1), z=z)
        move(s, fr, LX, LEVELS["safe"] if i == 0 else top, LX, z, 5, FEED, active=active, caption=cap)
        move(s, fr, LX, z, RX, z, 10, FEED, cut=(top, z), active=active, caption=cap)
        if i < len(layers) - 1:
            move(s, fr, RX, z, LX, z, 6, FEED, active=active, caption=cap)
        top = z
    hold(fr, s.frame(active, RX, layers[-1], cs("bottom")), 1400)
    move(s, fr, RX, layers[-1], RX, LEVELS["clear"], 8, RAPID, active=active, caption=cs("end"))
    hold(fr, s.frame(active, RX, LEVELS["clear"], cs("end")), 1400)
    return fr


@gif("clearance_height")
def clearance_height():
    s = Side()
    fr = []
    a = ("clear",)
    hold(fr, s.frame(a, 50, LEVELS["clear"], "Clearance: ψηλά, γρήγορα"), 1600)
    move(s, fr, 50, LEVELS["clear"], 250, LEVELS["clear"], 14, RAPID, active=a,
         caption="Περνά πάνω από όλα")
    hold(fr, s.frame(a, 250, LEVELS["clear"], "Περνά πάνω από όλα"), 900)
    # what goes wrong if it is too low
    s2 = Side()

    def bang(f):
        f.circle(CLAMP[1] - 2, zy(7), 13, outline=ACTIVE, width=3)
        f.text(CLAMP[1] + 14, zy(7) - 30, "ΜΠΑΜ!", fill=ACTIVE, font=F_LABEL)
    for i in range(9):
        x = lerp(250, CLAMP[1] + TOOL_D / 2 - 2, ease(i / 8))
        fr.append((s2.frame(a, x, 6, "Πιο χαμηλά από τον σφιγκτήρα…", warn=True), 80))
    hold(fr, s2.frame(a, CLAMP[1] + TOOL_D / 2 - 2, 6, "…θα τον χτυπούσε ✗",
                      warn=True, extra=bang), 2000)
    return fr


@gif("safe_height")
def safe_height():
    return pocket_run(("safe",), {
        "intro": "Safe Height: ως εδώ γρήγορα",
        "traverse": "Γρήγορα, ψηλά",
        "down_rapid": "Γρήγορα ως το Safe Height",
        "layer": "Από εκεί και κάτω ΑΡΓΑ",
        "finish": "Από εκεί και κάτω ΑΡΓΑ",
        "bottom": "Πράσινο γρήγορα · πορτοκαλί κόβει",
        "end": "Πάνω, γρήγορα"}, layers=(-4.0, -8.0, -12.0))


@gif("start_depth")
def start_depth():
    return pocket_run(("start",), {
        "intro": "Start Depth: η αρχή",
        "traverse": "Συνήθως η πάνω επιφάνεια",
        "down_rapid": "Συνήθως η πάνω επιφάνεια",
        "layer": "Από εδώ ξεκινούν τα περάσματα",
        "finish": "Από εδώ ξεκινούν τα περάσματα",
        "bottom": "Πιο ψηλό υλικό; Ανέβασέ το",
        "end": "Μπαίνει αυτόματα"}, layers=(-4.0, -8.0, -12.0))


@gif("step_down")
def step_down():
    return pocket_run((), {
        "intro": "Step Down: βάθος ανά πέρασμα",
        "traverse": "12 mm ÷ 4 mm = 3 περάσματα",
        "down_rapid": "12 mm ÷ 4 mm = 3 περάσματα",
        "layer": "Πέρασμα {n}/{N}: −{dz} mm",
        "bottom": "Μικρότερο = πιο ήπιο",
        "end": "Για αρχή: μισή διάμετρο φρέζας"},
        layers=(-4.0, -8.0, -12.0), extra=step_bracket)


def step_bracket(f):
    x = PX1 + 10
    for z0, z1 in ((0, -4), (-4, -8), (-8, -12)):
        f.line([(x, zy(z0) + 1), (x, zy(z1) - 1)], ACTIVE, 2)
        f.line([(x - 4, zy(z1)), (x + 4, zy(z1))], ACTIVE, 2)
        f.text(x + 6, (zy(z0) + zy(z1)) / 2, "4 mm", fill=ACTIVE, font=F_LABEL, anchor="lm")
    f.line([(x - 4, zy(0)), (x + 4, zy(0))], ACTIVE, 2)


@gif("finish_depth")
def finish_depth():
    return pocket_run(("final",), {
        "intro": "Finish Depth: λεπτό τελευταίο",
        "traverse": "Step Down 4 · Finish 1 mm",
        "down_rapid": "Step Down 4 · Finish 1 mm",
        "layer": "Πέρασμα {n}: −{dz} mm",
        "finish": "Τελευταίο: μόνο {dz} mm → λείος πάτος",
        "bottom": "0 = χωρίς ξεχωριστό τελικό πέρασμα",
        "end": "Για ωραίο πάτο"},
        layers=(-4.0, -8.0, -11.0, -12.0))


@gif("final_depth")
def final_depth():
    fr = pocket_run(("final",), {
        "intro": "Final Depth: ο πάτος",
        "traverse": "Τσέπη 12 mm",
        "down_rapid": "Τσέπη 12 mm",
        "layer": "Πέρασμα-πέρασμα ως κάτω",
        "bottom": "Ο πάτος = Final Depth",
        "end": "Διαμπερές: λίγο πιο κάτω (−0.3 mm)"},
        layers=(-4.0, -8.0, -12.0))
    s = Side()
    hold(fr, s.frame(("final", "start"), LX, 0.5,
                     "⚠ Final = Start → δεν κόβει τίποτα", warn=True), 2600)
    return fr


# ===========================================================================
# top view helpers
# ===========================================================================
TX0, TY0, TX1, TY1 = 40, 34, 290, 196     # pocket / face area in top views


def polyline_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def point_at(pts, dist):
    """Point at distance `dist` along a polyline and the part drawn so far."""
    done = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if dist <= L:
            t = dist / L if L else 0
            p = (lerp(a[0], b[0], t), lerp(a[1], b[1], t))
            return p, done + [p]
        dist -= L
        done.append(b)
    return pts[-1], done


def run_path(fr, base, segments, r, steps=40, caption="", ms=60, cleared=True, label=None):
    """Animate a tool (radius r) along segments = [(pts, kind)], kind 'cut' or 'rapid'."""
    total = sum(polyline_len(p) for p, _ in segments)
    for i in range(steps + 1):
        dist = total * i / steps
        f = Frame()
        base(f)
        tool_pos = segments[0][0][0]
        for pts, kind in segments:
            L = polyline_len(pts)
            if dist <= 0:
                break
            p, done = point_at(pts, min(dist, L))
            if kind == "cut":
                if cleared:
                    f.line(done, CUT, r * 2)
                f.line(done, PATH, 1.5)
            else:
                for a, b in zip(done, done[1:]):
                    f.dashed(a[0], a[1], b[0], b[1], RAPID, 1.2, 4, 3)
            tool_pos = p
            dist -= L
        f.tool_top(tool_pos[0], tool_pos[1], r, angle=i * 0.9)
        if label:
            label(f)
        f.caption(caption)
        fr.append((f, ms))


def face_base(f, title=None):
    f.rect(TX0, TY0, TX1, TY1, fill=STOCK, outline=STOCK_EDGE)
    if title:
        f.tag(TX1 + 8, TY0, title, anchor="la")


def zigzag(x0, y0, x1, y1, step, r):
    pts, y, k = [], y0 + r, 0
    while y <= y1 - r + 0.1:
        a, b = (x0 + r, x1 - r) if k % 2 == 0 else (x1 - r, x0 + r)
        pts += [(a, y), (b, y)]
        y += step
        k += 1
    return pts


def offsets(x0, y0, x1, y1, step, r):
    loops = []
    d = r
    while (x1 - x0) - 2 * d > 0 and (y1 - y0) - 2 * d > 0:
        loops.append([(x0 + d, y0 + d), (x1 - d, y0 + d), (x1 - d, y1 - d), (x0 + d, y1 - d), (x0 + d, y0 + d)])
        d += step
    return loops[::-1]   # from the centre outwards


def spiral(x0, y0, x1, y1, step, r):
    pts = []
    d = r
    while (x1 - x0) - 2 * d > 0 and (y1 - y0) - 2 * d > 0:
        pts += [(x0 + d, y0 + d), (x1 - d, y0 + d), (x1 - d, y1 - d), (x0 + d, y1 - d)]
        d += step
        pts.append((x0 + d, y0 + d - step + step))
    return pts


R_TOP = 13                 # tool radius in top views (6 mm tool → ~13 px)


@gif("step_over")
def step_over():
    fr = []
    for pct in (50, 25):
        step = 2 * R_TOP * pct / 100
        pts = zigzag(TX0, TY0, TX1, TY1, step, R_TOP)

        def lab(f, pct=pct, step=step):
            y = TY0 + R_TOP
            f.line([(TX1 + 10, y), (TX1 + 10, y + step)], ACTIVE, 2)
            f.line([(TX1 + 6, y), (TX1 + 14, y)], ACTIVE, 2)
            f.line([(TX1 + 6, y + step), (TX1 + 14, y + step)], ACTIVE, 2)
            f.text(TX1 + 18, y + step / 2, "%d%%" % pct, fill=ACTIVE, font=F_LABEL, anchor="lm")
            f.text(TX1 + 18, y + step / 2 + 14, "= %.1f mm" % (6 * pct / 100), fill=ACTIVE, anchor="lm")
        cap = ("Step Over %d%% = %.1f mm" % (pct, 6 * pct / 100))
        run_path(fr, face_base, [(pts, "cut")], R_TOP, steps=46 if pct == 50 else 70, caption=cap, label=lab)
        f = Frame()
        face_base(f)
        f.line(pts, CUT, R_TOP * 2)
        f.line(pts, PATH, 1.5)
        lab(f)
        f.caption("50% γρήγορο · 10–25% λείο" if pct == 50 else
                  "Μικρότερο = πιο λείο")
        fr.append((f, 1800))
    return fr


def pattern_frames(fr, name, gr, segs, total_steps=50):
    run_path(fr, lambda f: face_base(f, name), segs, R_TOP, steps=total_steps, caption=gr)
    f = Frame()
    face_base(f, name)
    for pts, kind in segs:
        if kind == "cut":
            f.line(pts, CUT, R_TOP * 2)
            f.line(pts, PATH, 1.5)
        else:
            for a, b in zip(pts, pts[1:]):
                f.dashed(a[0], a[1], b[0], b[1], RAPID, 1.2, 4, 3)
    f.caption(gr)
    fr.append((f, 1500))


@gif("pocket_clearing_pattern")
def pocket_patterns():
    fr = []
    st = R_TOP * 1.0
    zz = zigzag(TX0, TY0, TX1, TY1, st, R_TOP)
    pattern_frames(fr, "ZigZag", "ZigZag: πάει-έρχεται", [(zz, "cut")])
    off = offsets(TX0, TY0, TX1, TY1, st, R_TOP)
    segs = []
    for i, lp in enumerate(off):
        segs.append((lp, "cut"))
        if i + 1 < len(off):
            segs.append(([lp[-1], off[i + 1][0]], "cut"))
    pattern_frames(fr, "Offset", "Offset: γύροι σαν το σχήμα", segs)
    ring = [(TX0 + R_TOP, TY0 + R_TOP), (TX1 - R_TOP, TY0 + R_TOP), (TX1 - R_TOP, TY1 - R_TOP),
            (TX0 + R_TOP, TY1 - R_TOP), (TX0 + R_TOP, TY0 + R_TOP)]
    inner = zigzag(TX0 + R_TOP, TY0 + R_TOP, TX1 - R_TOP, TY1 - R_TOP, st, R_TOP)
    pattern_frames(fr, "ZigZagOffset", "ZigZagOffset: + γύρος στα τοιχώματα",
                   [(inner, "cut"), ([inner[-1], ring[0]], "rapid"), (ring, "cut")])
    segs = []
    y = TY0 + R_TOP
    while y <= TY1 - R_TOP + 0.1:
        segs.append(([(TX0 + R_TOP, y), (TX1 - R_TOP, y)], "cut"))
        segs.append(([(TX1 - R_TOP, y), (TX0 + R_TOP, y + st)], "rapid"))
        y += st
    segs.pop()
    pattern_frames(fr, "Line", "Line: όλες προς μία μεριά", segs, 60)
    gx = zigzag(TX0, TY0, TX1, TY1, st * 1.6, R_TOP)
    gy = [(p[1], p[0]) for p in zigzag(TY0, TX0, TY1, TX1, st * 1.6, R_TOP)]
    pattern_frames(fr, "Grid", "Grid: και προς τις δύο",
                   [(gx, "cut"), ([gx[-1], gy[0]], "rapid"), (gy, "cut")], 60)
    return fr


@gif("facing_clearing_pattern")
def facing_patterns():
    fr = []
    st = R_TOP * 1.4
    zz = zigzag(TX0 - 8, TY0, TX1 + 8, TY1, st, R_TOP)
    pattern_frames(fr, "ZigZag", "ZigZag: χωρίς σήκωμα", [(zz, "cut")])
    # Bidirectional: alternately from the bottom and the top edge towards the middle
    ys = []
    y = TY0 + R_TOP
    while y <= TY1 - R_TOP + 0.1:
        ys.append(y)
        y += st
    order, lo, hi = [], 0, len(ys) - 1
    while lo <= hi:
        order.append(("lr", ys[hi]))
        if lo != hi:
            order.append(("rl", ys[lo]))
        lo, hi = lo + 1, hi - 1
    segs, prev = [], None
    for d, y in order:
        a, b = (TX0 - 8, TX1 + 8) if d == "lr" else (TX1 + 8, TX0 - 8)
        if prev:
            segs.append(([prev, (a, y)], "rapid"))
        segs.append(([(a, y), (b, y)], "cut"))
        prev = (b, y)
    pattern_frames(fr, "Bidirectional", "Bidirectional: εναλλάξ", segs, 60)
    segs = []
    for i, y in enumerate(ys):
        segs.append(([(TX0 - 8, y), (TX1 + 8, y)], "cut"))
        if i + 1 < len(ys):
            segs.append(([(TX1 + 8, y), (TX0 - 8, ys[i + 1])], "rapid"))
    pattern_frames(fr, "Directional", "Directional: πάντα ίδια φορά", segs, 60)
    sp = spiral(TX0, TY0, TX1, TY1, st, R_TOP)
    pattern_frames(fr, "Spiral", "Spiral: σπείρα", [(sp, "cut")])
    return fr


@gif("pattern_angle")
def pattern_angle():
    fr = []
    cx, cy = (TX0 + TX1) / 2, (TY0 + TY1) / 2

    def scene(ang, tool_t=None, cap=""):
        a = math.radians(ang)
        f = Frame()
        face_base(f)
        L, k = 220, -9
        while k <= 9:
            ox, oy = -math.sin(a) * k * 13, math.cos(a) * k * 13
            f.line([(cx + ox - math.cos(a) * L, cy + oy - math.sin(a) * L),
                    (cx + ox + math.cos(a) * L, cy + oy + math.sin(a) * L)], PATH, 1.5)
            k += 1
        # mask everything outside the face, then frame it again
        f.d.rectangle([0, 0, TX0 * 2 - 1, H * 2], fill=BG)
        f.d.rectangle([TX1 * 2 + 1, 0, W * 2, H * 2], fill=BG)
        f.d.rectangle([0, 0, W * 2, TY0 * 2 - 1], fill=BG)
        f.d.rectangle([0, TY1 * 2 + 1, W * 2, H * 2], fill=BG)
        f.rect(TX0, TY0, TX1, TY1, outline=STOCK_EDGE)
        # angle gauge
        gx, gy = TX1 + 52, TY0 + 52
        f.line([(gx - 34, gy), (gx + 34, gy)], DIM, 1)
        f.arc(gx, gy, 26, -ang, 0, ACTIVE, 3) if ang > 0 else None
        f.line([(gx, gy), (gx + 34 * math.cos(-a), gy + 34 * math.sin(-a))], ACTIVE, 3)
        f.text(gx, gy + 22, "%d°" % round(ang), fill=ACTIVE, font=F_LABEL, anchor="mm")
        if tool_t is not None:   # tool running along the middle line
            d = (tool_t - 0.5) * 2 * 110
            f.tool_top(cx + math.cos(a) * d, cy + math.sin(a) * d, R_TOP, angle=tool_t * 20)
        f.caption(cap)
        return f

    for stop, nxt in ((0, 45), (45, 90), (90, 0)):
        for i in range(11):
            fr.append((scene(stop, i / 10, "Angle %d°" % stop), 70))
        steps = 12
        for i in range(1, steps + 1):
            ang = lerp(stop, nxt, ease(i / steps)) if nxt else lerp(stop, 0, ease(i / steps))
            fr.append((scene(ang, None, "Γυρίζουν όλες οι γραμμές"), 60))
    return fr


@gif("cut_mode")
def cut_mode():
    """Climb vs conventional, seen from above, spindle turning clockwise (M3)."""
    fr = []
    r = 26
    for mode in ("Climb", "Conventional"):
        mat_below = mode == "Climb"
        for i in range(24):
            f = Frame()
            ey = 125
            if mat_below:
                f.rect(20, ey, W - 20, TY1 + 10, fill=STOCK, outline=STOCK_EDGE)
            else:
                f.rect(20, 30, W - 20, ey, fill=STOCK, outline=STOCK_EDGE)
            x = lerp(70, 300, i / 23)
            cy = ey - r * 0.55 if mat_below else ey + r * 0.55
            # cleared groove behind the tool
            if mat_below:
                f.rect(20, ey, x, cy + r, fill=BG)
            else:
                f.rect(20, cy - r, x, ey, fill=BG)
            f.tool_top(x, cy, r, angle=i * 0.7)
            f.spin_arrow(x, cy, r + 9, cw=True)
            f.arrow(x + r + 14, cy, x + r + 44, cy, PATH, 3, 9)
            f.text(x + r + 29, cy - 9, "πορεία", fill=PATH, anchor="md")
            f.tag(30, 8, mode, fill=ACTIVE)
            f.text(30 + (60 if mode == "Climb" else 110), 13, "(ομόρροπη)" if mode == "Climb" else "(αντίρροπη)",
                   fill=DIM)
            f.caption("Climb: μπαίνει χοντρά" if mode == "Climb" else
                      "Conventional: μπαίνει λεπτά")
            fr.append((f, 90))
        f = fr[-1][0]
        fr.append((f, 400))
    f = Frame()
    f.tag(W / 2, 70, "Climb  ✓  CNC router, ξύλο", fill=RAPID, anchor="mm", font=F_BIG)
    f.tag(W / 2, 120, "Conventional  →  μηχανή με τζόγο", fill=DIM, anchor="mm", font=F_BIG)
    f.caption("Άξονας δεξιόστροφα (M3)")
    fr.append((f, 4200))
    return fr


# ===========================================================================
# profile (contour) top views
# ===========================================================================
PART_R = (120, 70, 230, 160)       # part outline in top view


def part_base(f, hole=False):
    x0, y0, x1, y1 = PART_R
    f.rect(20, 20, W - 20, TY1 + 8, fill=STOCK, outline=STOCK_EDGE)
    f.rrect(x0, y0, x1, y1, 10, fill=PART, outline=PART_EDGE, width=2)
    if hole:
        f.circle((x0 + x1) / 2, (y0 + y1) / 2, 26, fill=CUT, outline=PART_EDGE, width=2)


def loop_rect(x0, y0, x1, y1, d, cw=True):
    pts = [(x0 - d, y0 - d), (x1 + d, y0 - d), (x1 + d, y1 + d), (x0 - d, y1 + d), (x0 - d, y0 - d)]
    return pts if cw else pts[::-1]


def loop_circle(cx, cy, rr, n=40, cw=True):
    pts = [(cx + rr * math.cos(2 * math.pi * k / n), cy + rr * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    return pts if cw else pts[::-1]


@gif("cut_side")
def cut_side():
    fr = []
    r = 11
    x0, y0, x1, y1 = PART_R
    run_path(fr, lambda f: part_base(f, True), [(loop_rect(x0, y0, x1, y1, r), "cut")], r, 40,
             "Outside: γύρω-γύρω ΕΞΩ",
             label=lambda f: f.tag(24, 26, "Cut side = Outside"))
    run_path(fr, lambda f: part_base(f, True), [(loop_circle((x0 + x1) / 2, (y0 + y1) / 2, 26 - r), "cut")], r, 30,
             "Inside: ΜΕΣΑ (για τρύπες)",
             label=lambda f: f.tag(24, 26, "Cut side = Inside"))
    fr.append((fr[-1][0], 1500))
    return fr


@gif("use_compensation")
def use_compensation():
    fr = []
    r = 11
    x0, y0, x1, y1 = PART_R

    def eaten(f):
        f.rrect(x0, y0, x1, y1, 10, outline=ACTIVE, width=2)
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r), "cut")], r, 36,
             "Με Compensation: σωστό μέγεθος ✓",
             label=lambda f: f.tag(24, 26, "Use Compensation ✓"))
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, 0), "cut")], r, 36,
             "Χωρίς: τρώει το κομμάτι ✗",
             label=lambda f: (f.tag(24, 26, "Use Compensation ✗", fill=DIM), eaten(f)))
    fr.append((fr[-1][0], 1600))
    return fr


@gif("profile_direction")
def profile_direction():
    fr = []
    r = 11
    x0, y0, x1, y1 = PART_R
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r, cw=True), "cut")], r, 36,
             "CW έξω = Climb",
             label=lambda f: f.tag(24, 26, "Direction = CW"))
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r, cw=False), "cut")], r, 36,
             "CCW έξω = Conventional",
             label=lambda f: f.tag(24, 26, "Direction = CCW"))
    f = Frame()
    f.tag(W / 2, 70, "Έξω:  CW = Climb", fill=RAPID, anchor="mm", font=F_BIG)
    f.tag(W / 2, 120, "Τρύπα:  CCW = Climb", fill=RAPID, anchor="mm", font=F_BIG)
    f.caption("Με άξονα M3")
    fr.append((f, 3600))
    return fr


@gif("profile_passes")
def profile_passes():
    fr = []
    r = 11
    x0, y0, x1, y1 = PART_R
    segs = []
    for k, d in enumerate((r + 16, r + 8, r)):
        segs.append((loop_rect(x0, y0, x1, y1, d), "cut"))
    run_path(fr, part_base, segs, r, 70, "3 περάσματα = 3 γύροι",
             label=lambda f: f.tag(24, 26, "3 περάσματα"))
    fr.append((fr[-1][0], 1600))
    return fr


@gif("stock_to_leave")
def stock_to_leave():
    fr = []
    r = 11
    x0, y0, x1, y1 = PART_R
    leave = 5

    def thin(f):
        f.rrect(x0 - leave, y0 - leave, x1 + leave, y1 + leave, 12, fill=LEFT)
        f.rrect(x0, y0, x1, y1, 10, fill=PART, outline=PART_EDGE, width=2)

    def base(f):
        part_base(f)
        thin(f)
    run_path(fr, base, [(loop_rect(x0, y0, x1, y1, r + leave), "cut")], r, 36,
             "Αφήνει λίγο υλικό (κίτρινο)",
             label=lambda f: f.tag(24, 26, "Radial stock to leave = 0.5 mm"))
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r), "cut")], r, 36,
             "Ένα τελικό πέρασμα → λεία τοιχώματα",
             label=lambda f: f.tag(24, 26, "τελικό πέρασμα (finishing)"))
    fr.append((fr[-1][0], 1500))
    return fr


@gif("axial_stock_to_leave")
def axial_stock_to_leave():
    s = Side()
    fr = []
    a = ("final",)
    s.cleared.append((PX0, 0, PX1, -11.0))

    def floor(f):
        f.rect(PX0, zy(-11.0), PX1, zy(-12.0), fill=LEFT)
        f.tag(PX0 + 4, zy(-11.0) - 18, "0.5–1 mm μένει", fill=PATH)
    hold(fr, s.frame(a, RX, -11.0, "Αφήνει λίγο στον πάτο", extra=floor), 2200)
    s.cleared[-1] = (PX0, 0, PX1, -12.0)
    move(s, fr, LX, -12.0, RX, -12.0, 12, FEED, active=a, caption="Μετά: τελικό πέρασμα")
    hold(fr, s.frame(a, RX, -12.0, "Μετά: τελικό πέρασμα"), 1500)
    return fr


@gif("use_outline")
def use_outline():
    fr = []
    cx, cy = (TX0 + TX1) / 2, (TY0 + TY1) / 2

    def base_island(f):
        face_base(f)
        f.circle(cx, cy, 30, fill=PART, outline=PART_EDGE, width=2)

    st = R_TOP * 1.2
    zz = zigzag(TX0, TY0, TX1, TY1, st, R_TOP)
    # without outline: lines skip the island
    segs = []
    for a, b in zip(zz[::2], zz[1::2]):
        y = a[1]
        dy = abs(y - cy)
        if dy < 30 + R_TOP:
            half = math.sqrt((30 + R_TOP) ** 2 - dy ** 2)
            lo, hi = sorted((a[0], b[0]))
            for s0, s1 in ((lo, cx - half), (cx + half, hi)):
                if s1 > s0:
                    segs.append(([(s0, y), (s1, y)], "cut"))
        else:
            segs.append(([a, b], "cut"))
    run_path(fr, base_island, segs, R_TOP, 50, "Χωρίς ✓: κρατά το νησί",
             label=lambda f: f.tag(TX1 + 8, TY0, "Use outline ✗", fill=DIM))
    fr.append((fr[-1][0], 900))
    run_path(fr, base_island, [(zz, "cut")], R_TOP, 50, "Με ✓: κόβει και το νησί",
             label=lambda f: f.tag(TX1 + 8, TY0, "Use outline ✓"))
    fr.append((fr[-1][0], 1500))
    return fr


@gif("pass_extension")
def pass_extension():
    fr = []
    st = R_TOP * 1.4
    for ext, cap in ((0, "0: σταματά στην άκρη"),
                     (16, "3 mm έξω → καθαρή άκρη")):
        zz = zigzag(TX0 + R_TOP - ext - 4, TY0, TX1 - R_TOP + ext + 4, TY1, st, 0)

        def lab(f, ext=ext):
            if ext:
                f.dashed(TX1 + ext, TY0 - 6, TX1 + ext, TY1 + 6, ACTIVE, 1.5)
                f.tag(TX1 + ext + 4, TY1 - 12, "+3 mm")
        run_path(fr, face_base, [(zz, "cut")], R_TOP, 46, cap, label=lab)
        fr.append((fr[-1][0], 1200))
    return fr


# ===========================================================================
# drilling (side view)
# ===========================================================================
HOLE_X = 160


def drill_scene(active=(), tz=None, depth=0.0, cap="", warn=False, extra=None, show=("clear", "safe", "start", "final")):
    s = Side()
    s.cleared = [(HOLE_X - 7, 0, HOLE_X + 7, depth)] if depth < 0 else []
    return s.frame(active, HOLE_X if tz is not None else None, tz, cap, warn, extra, show, drill=True)


@gif("peck")
def peck():
    fr = []
    R = 2.0           # peck retract (R plane) above the top
    depth, q = 0.0, 4.0

    def rline(f):
        f.dashed(HOLE_X - 40, zy(R), HOLE_X + 40, zy(R), PATH, 1.5)
        f.text(HOLE_X + 44, zy(R), "R", fill=PATH, font=F_LABEL, anchor="lm")
    fr.append((drill_scene(("final",), LEVELS["safe"], 0, "Peck: λίγο-λίγο", extra=rline), 1600))
    first = True
    while depth > LEVELS["final"]:
        nd = max(LEVELS["final"], depth - q)
        if not first:   # G83: rapid back down to just above the last depth, then feed again
            for i in range(4):
                fr.append((drill_scene(("final",), lerp(R, depth + 0.3, ease(i / 3)), depth,
                                       "Γρήγορα ως το προηγούμενο βάθος", extra=rline), 60))
        first = False
        for i in range(6):
            fr.append((drill_scene(("final",), lerp(depth, nd, i / 5), min(depth, lerp(depth, nd, i / 5)),
                                   "−%g mm (Peck depth)" % q, extra=rline), 70))
        depth = nd
        for i in range(5):
            fr.append((drill_scene(("final",), lerp(depth, R, i / 4), depth,
                                   "Βγαίνει: φεύγουν τα ρινίσματα", extra=rline), 60))
        fr.append((fr[-1][0], 250))
    fr.append((drill_scene(("final",), R, depth, "Λίγο-λίγο = δεν σπάει το τρυπάνι", extra=rline), 2000))
    return fr


@gif("dwell")
def dwell():
    fr = []
    for i in range(8):
        z = lerp(LEVELS["safe"], LEVELS["final"], i / 7)
        fr.append((drill_scene(("final",), z, min(0, z), "Κάτω ως τον πάτο"), 70))
    for k in range(3, 0, -1):
        def clock(f, k=k):
            f.tag(HOLE_X + 22, zy(-9), "περιμένει… %d" % k, fill=PATH)
        fr.append((drill_scene(("final",), LEVELS["final"], LEVELS["final"], "Dwell: περιμένει στον πάτο", extra=clock), 600))
    for i in range(6):
        z = lerp(LEVELS["final"], LEVELS["safe"], i / 5)
        fr.append((drill_scene(("final",), z, LEVELS["final"], "Ίσιος πάτος ✓"), 70))
    fr.append((fr[-1][0], 1200))
    return fr


def drilled(f, bottom, d=14):
    """Hole made by a drill whose tip reached `bottom` (cone at the bottom)."""
    r = d / 2
    tip = r * 0.6
    yb = zy(bottom)
    f.poly([(HOLE_X - r, zy(0)), (HOLE_X + r, zy(0)), (HOLE_X + r, yb - tip), (HOLE_X, yb),
            (HOLE_X - r, yb - tip)], fill=BG)


@gif("drill_extra_offset")
def drill_extra_offset():
    fr = []
    fin, extra = LEVELS["final"], -1.6
    cap1 = "Το τρυπάνι έχει μύτη"

    def at(z, cap, marks=None, warn=False):
        def ex(f):
            drilled(f, min(0, z))
            if marks:
                marks(f)
        return drill_scene(("final",), z, 0, cap, warn, extra=ex)

    def narrow(f):   # red marks where the hole is narrower than the drill at Final Depth
        y = zy(fin)
        f.line([(HOLE_X - 7, y - 4), (HOLE_X - 2, y + 1)], ACTIVE, 2.5)
        f.line([(HOLE_X + 7, y - 4), (HOLE_X + 2, y + 1)], ACTIVE, 2.5)
        f.tag(HOLE_X + 26, y - 26, "εδώ στενεύει", fill=ACTIVE)

    def full(f):
        y = zy(fin)
        f.line([(HOLE_X - 7, y), (HOLE_X + 7, y)], RAPID, 3)
        f.tag(HOLE_X + 26, y - 26, "πλήρης διάμετρος ✓", fill=RAPID)
        f.dashed(HOLE_X - 34, zy(fin + extra), HOLE_X + 34, zy(fin + extra), PATH, 1.5)
        f.text(HOLE_X + 38, zy(fin + extra), "+Extra Offset", fill=PATH, font=F_SMALL, anchor="lm")

    for i in range(10):
        fr.append((at(lerp(LEVELS["safe"], fin, i / 9), cap1), 70))
    fr.append((at(fin, "Στενεύει στο κάτω μέρος ✗", narrow, True), 2000))
    for i in range(8):
        fr.append((at(lerp(LEVELS["safe"], 0, i / 7), "Extra Offset: λίγο πιο βαθιά"), 50))
    for i in range(10):
        fr.append((at(lerp(0, fin + extra, i / 9), "Extra Offset: λίγο πιο βαθιά"), 70))
    fr.append((at(fin + extra, "Σωστή διάμετρος ως κάτω ✓", full), 2400))
    return fr


@gif("peck_retract")
def peck_retract():
    fr = []
    R = 2.0
    show = ("clear", "safe", "start", "final")

    def rline(f):
        f.dashed(HOLE_X - 50, zy(R), HOLE_X + 50, zy(R), ACTIVE, 2)
        f.text(HOLE_X + 54, zy(R), "Peck Retract (R)", fill=ACTIVE, font=F_LABEL, anchor="lm")

    def fr_(z, depth, cap):
        return drill_scene((), z, depth, cap, extra=rline, show=show)

    for i in range(6):
        fr.append((fr_(lerp(LEVELS["clear"], R, ease(i / 5)), 0, "Γρήγορα ως το R"), 70))
    fr.append((fr_(R, 0, "R: 1–2 mm πάνω από το υλικό"), 1200))
    depth = 0.0
    for nd in (-4.0, -8.0, -12.0):
        if depth < 0:
            for i in range(4):
                fr.append((fr_(lerp(R, depth + 0.3, ease(i / 3)), depth, "Γρήγορα ως το προηγούμενο βάθος"), 60))
        for i in range(6):
            z = lerp(depth, nd, i / 5)
            fr.append((fr_(z, min(0, z), "Τρυπάει 4 mm"), 70))
        depth = nd
        for i in range(5):
            fr.append((fr_(lerp(depth, R, ease(i / 4)), depth, "Βγαίνει μόνο ως το R"), 60))
        fr.append((fr[-1][0], 300))
    fr.append((fr_(R, depth, "R ≠ Safe Height"), 2200))
    return fr


# ===========================================================================
# adaptive
# ===========================================================================
@gif("helix_entry")
def helix_entry():
    s = Side()
    fr = []
    cx, rad = 176, 14
    z = LEVELS["safe"]
    pts = []
    k = 0
    while z > LEVELS["final"]:
        z -= 0.25
        x = cx + rad * math.sin(k * 0.35)
        pts.append((x, zy(max(z, LEVELS["final"]))))
        k += 1
    n = 40
    for i in range(n + 1):
        cut_z = LEVELS["final"] if i == n else max(LEVELS["final"], LEVELS["safe"] - (LEVELS["safe"] - LEVELS["final"]) * i / n)
        s.cleared = [(cx - rad - TOOL_D / 2, 0, cx + rad + TOOL_D / 2, min(0, cut_z))]
        sub = pts[: max(2, int(len(pts) * i / n))]
        s.trail = [(sub, FEED)]
        x, y = sub[-1]
        z_now = (TOP_Y - y) / MM
        fr.append((s.frame(("final",), x, z_now, "Helix: μπαίνει σαν βίδα"), 70))
    fr.append((fr[-1][0], 1500))
    fr.append((s.frame(("final",), cx, LEVELS["final"], "Max pitch: πόσο απότομα"), 2200))
    return fr


@gif("retract_threshold")
def retract_threshold():
    s = Side()
    fr = []
    a = ()
    s.cleared = [(60, 0, 130, -6), (170, 0, 250, -6)]
    hold(fr, s.frame(a, 95, -6, "Δύο κοντινές περιοχές"), 1500)
    move(s, fr, 95, -6, 95, LEVELS["clear"], 6, RAPID, caption="Χωρίς: ανεβαίνει ως πάνω (αργό)")
    move(s, fr, 95, LEVELS["clear"], 210, LEVELS["clear"], 8, RAPID, caption="Χωρίς: ανεβαίνει ως πάνω (αργό)")
    move(s, fr, 210, LEVELS["clear"], 210, -6, 6, RAPID, caption="Χωρίς: ανεβαίνει ως πάνω (αργό)")
    s.trail = []
    move(s, fr, 95, -6, 95, 1, 3, RAPID, caption="Με threshold: πάει χαμηλά")
    move(s, fr, 95, 1, 210, 1, 8, RAPID, caption="Με threshold: πάει χαμηλά")
    move(s, fr, 210, 1, 210, -6, 3, RAPID, caption="Με threshold: πάει χαμηλά")
    hold(fr, s.frame(a, 210, -6, "Πιο γρήγορα ✓"), 1600)
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

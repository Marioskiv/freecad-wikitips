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
from draw import (ACTIVE, BG, CAP_H, DIM, F_LABEL, F_SMALL, FEED, H, LEFT, PART,  # noqa: E402
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
    hold(fr, s.frame(a, 50, LEVELS["clear"], "Clearance: το ψηλό επίπεδο για γρήγορες μετακινήσεις"), 1600)
    move(s, fr, 50, LEVELS["clear"], 250, LEVELS["clear"], 14, RAPID, active=a,
         caption="Περνάει ΠΑΝΩ από σφιγκτήρες και κομμάτι, χωρίς φόβο")
    hold(fr, s.frame(a, 250, LEVELS["clear"], "Περνάει ΠΑΝΩ από σφιγκτήρες και κομμάτι, χωρίς φόβο"), 900)
    # what goes wrong if it is too low
    s2 = Side()

    def bang(f):
        f.circle(CLAMP[1] - 2, zy(7), 13, outline=ACTIVE, width=3)
        f.text(CLAMP[1] + 14, zy(7) - 30, "ΜΠΑΜ!", fill=ACTIVE, font=F_LABEL)
    for i in range(9):
        x = lerp(250, CLAMP[1] + TOOL_D / 2 - 2, ease(i / 8))
        fr.append((s2.frame(a, x, 6, "Αν ήταν πιο χαμηλά από τον σφιγκτήρα...", warn=True), 80))
    hold(fr, s2.frame(a, CLAMP[1] + TOOL_D / 2 - 2, 6, "...θα τον χτυπούσε. Βάλ' το πάνω από όλα!",
                      warn=True, extra=bang), 2000)
    return fr


@gif("safe_height")
def safe_height():
    return pocket_run(("safe",), {
        "intro": "Safe Height: ως εδώ κατεβαίνει ΓΡΗΓΟΡΑ (πράσινο)",
        "traverse": "Γρήγορη μετακίνηση πάνω από το κομμάτι",
        "down_rapid": "Γρήγορα κάτω ως το Safe Height (λίγο πάνω από το ξύλο)",
        "layer": "Από εκεί και κάτω ΑΡΓΑ, με ταχύτητα κοπής (πορτοκαλί)",
        "finish": "Από εκεί και κάτω ΑΡΓΑ, με ταχύτητα κοπής (πορτοκαλί)",
        "bottom": "Πράσινο = γρήγορα στον αέρα · πορτοκαλί = αργά, κόβει",
        "end": "Στο τέλος ανεβαίνει πάλι γρήγορα"}, layers=(-4.0, -8.0, -12.0))


@gif("start_depth")
def start_depth():
    return pocket_run(("start",), {
        "intro": "Start Depth: από ποιο ύψος αρχίζει να κόβει",
        "traverse": "Συνήθως = η πάνω επιφάνεια του υλικού (ή της επιλεγμένης έδρας)",
        "down_rapid": "Συνήθως = η πάνω επιφάνεια του υλικού (ή της επιλεγμένης έδρας)",
        "layer": "Τα περάσματα μετρούν από το Start Depth και κάτω",
        "finish": "Τα περάσματα μετρούν από το Start Depth και κάτω",
        "bottom": "Αν το υλικό είναι πιο ψηλό από το μοντέλο, ανέβασέ το",
        "end": "Το FreeCAD το βάζει αυτόματα από τη γεωμετρία"}, layers=(-4.0, -8.0, -12.0))


@gif("step_down")
def step_down():
    return pocket_run((), {
        "intro": "Step Down: πόσο βαθιά κόβει σε κάθε πέρασμα",
        "traverse": "Ολικό βάθος 12 mm, Step Down 4 mm → 3 περάσματα",
        "down_rapid": "Ολικό βάθος 12 mm, Step Down 4 mm → 3 περάσματα",
        "layer": "Πέρασμα {n} από {N}: κατεβαίνει {dz} mm (Step Down)",
        "bottom": "Μικρότερο Step Down = πιο αργά αλλά πιο ήπια για τη φρέζα",
        "end": "Ξύλο/MDF με φρέζα 6 mm: συνήθως 2–6 mm ανά πέρασμα"},
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
        "intro": "Finish Depth: ένα τελευταίο ΛΕΠΤΟ πέρασμα στον πάτο",
        "traverse": "Εδώ: Step Down 4 mm, Finish Depth 1 mm",
        "down_rapid": "Εδώ: Step Down 4 mm, Finish Depth 1 mm",
        "layer": "Πέρασμα {n}: χοντρό κόψιμο ({dz} mm)",
        "finish": "Τελευταίο πέρασμα: μόνο {dz} mm → καθαρός, λείος πάτος",
        "bottom": "0 = χωρίς ξεχωριστό τελικό πέρασμα",
        "end": "Χρήσιμο όταν θέλεις ωραία επιφάνεια στον πάτο"},
        layers=(-4.0, -8.0, -11.0, -12.0))


@gif("final_depth")
def final_depth():
    fr = pocket_run(("final",), {
        "intro": "Final Depth: το πιο χαμηλό σημείο που θα φτάσει",
        "traverse": "Εδώ: τσέπη βάθους 12 mm",
        "down_rapid": "Εδώ: τσέπη βάθους 12 mm",
        "layer": "Κατεβαίνει πέρασμα-πέρασμα ως το Final Depth",
        "bottom": "Ο πάτος της τσέπης = Final Depth",
        "end": "Για διαμπερές κόψιμο: λίγο πιο κάτω από το υλικό (π.χ. −0.3 mm)"},
        layers=(-4.0, -8.0, -12.0))
    s = Side()
    hold(fr, s.frame(("final", "start"), LX, 0.5,
                     "⚠ Αν Final Depth = Start Depth, δεν κόβει ΤΙΠΟΤΑ!", warn=True), 2600)
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
                    f.line(done, (236, 228, 214), r * 2)
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
        cap = ("Step Over %d%%: κάθε πέρασμα πάει %.1f mm πιο δίπλα" % (pct, 6 * pct / 100))
        run_path(fr, face_base, [(pts, "cut")], R_TOP, steps=46 if pct == 50 else 70, caption=cap, label=lab)
        f = Frame()
        face_base(f)
        f.line(pts, (236, 228, 214), R_TOP * 2)
        f.line(pts, PATH, 1.5)
        lab(f)
        f.caption("50% = γρήγορο ξεχόνδρισμα · 10–25% = πιο λεία επιφάνεια" if pct == 50 else
                  "Μικρότερο Step Over = περισσότερα περάσματα, πιο λείο")
        fr.append((f, 1800))
    return fr


def pattern_frames(fr, name, gr, segs, total_steps=50):
    run_path(fr, lambda f: face_base(f, name), segs, R_TOP, steps=total_steps, caption=gr)
    f = Frame()
    face_base(f, name)
    for pts, kind in segs:
        if kind == "cut":
            f.line(pts, (236, 228, 214), R_TOP * 2)
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
    pattern_frames(fr, "ZigZag", "ZigZag: πάει-έρχεται σε ευθείες γραμμές", [(zz, "cut")])
    off = offsets(TX0, TY0, TX1, TY1, st, R_TOP)
    segs = []
    for i, lp in enumerate(off):
        segs.append((lp, "cut"))
        if i + 1 < len(off):
            segs.append(([lp[-1], off[i + 1][0]], "cut"))
    pattern_frames(fr, "Offset", "Offset: γύρους που ακολουθούν το σχήμα", segs)
    ring = [(TX0 + R_TOP, TY0 + R_TOP), (TX1 - R_TOP, TY0 + R_TOP), (TX1 - R_TOP, TY1 - R_TOP),
            (TX0 + R_TOP, TY1 - R_TOP), (TX0 + R_TOP, TY0 + R_TOP)]
    inner = zigzag(TX0 + R_TOP, TY0 + R_TOP, TX1 - R_TOP, TY1 - R_TOP, st, R_TOP)
    pattern_frames(fr, "ZigZagOffset", "ZigZagOffset: ZigZag + ένας γύρος στα τοιχώματα",
                   [(inner, "cut"), ([inner[-1], ring[0]], "rapid"), (ring, "cut")])
    segs = []
    y = TY0 + R_TOP
    while y <= TY1 - R_TOP + 0.1:
        segs.append(([(TX0 + R_TOP, y), (TX1 - R_TOP, y)], "cut"))
        segs.append(([(TX1 - R_TOP, y), (TX0 + R_TOP, y + st)], "rapid"))
        y += st
    segs.pop()
    pattern_frames(fr, "Line", "Line: όλες οι γραμμές προς την ίδια μεριά", segs, 60)
    gx = zigzag(TX0, TY0, TX1, TY1, st * 1.6, R_TOP)
    gy = [(p[1], p[0]) for p in zigzag(TY0, TX0, TY1, TX1, st * 1.6, R_TOP)]
    pattern_frames(fr, "Grid", "Grid: γραμμές και στις δύο κατευθύνσεις",
                   [(gx, "cut"), ([gx[-1], gy[0]], "rapid"), (gy, "cut")], 60)
    return fr


@gif("facing_clearing_pattern")
def facing_patterns():
    fr = []
    st = R_TOP * 1.4
    zz = zigzag(TX0 - 8, TY0, TX1 + 8, TY1, st, R_TOP)
    pattern_frames(fr, "ZigZag", "ZigZag: συνεχόμενο πάνω-κάτω, δεν σηκώνεται", [(zz, "cut")])
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
    pattern_frames(fr, "Bidirectional", "Bidirectional: εναλλάξ από κάτω και από πάνω", segs, 60)
    segs = []
    for i, y in enumerate(ys):
        segs.append(([(TX0 - 8, y), (TX1 + 8, y)], "cut"))
        if i + 1 < len(ys):
            segs.append(([(TX1 + 8, y), (TX0 - 8, ys[i + 1])], "rapid"))
    pattern_frames(fr, "Directional", "Directional: πάντα ίδια φορά → ίδιο φινίρισμα", segs, 60)
    sp = spiral(TX0, TY0, TX1, TY1, st, R_TOP)
    pattern_frames(fr, "Spiral", "Spiral: σπείρα από έξω προς τα μέσα", [(sp, "cut")])
    return fr


@gif("pattern_angle")
def pattern_angle():
    fr = []
    cx, cy = (TX0 + TX1) / 2, (TY0 + TY1) / 2
    for ang in (0, 45, 90):
        a = math.radians(ang)
        f = Frame()
        face_base(f, "Angle %d°" % ang)
        L = 200
        k = -8
        while k <= 8:
            ox, oy = -math.sin(a) * k * 13, math.cos(a) * k * 13
            p0 = (cx + ox - math.cos(a) * L, cy + oy - math.sin(a) * L)
            p1 = (cx + ox + math.cos(a) * L, cy + oy + math.sin(a) * L)
            f.line([p0, p1], PATH, 1.5)
            k += 1
        f.rect(0, 0, TX0, H, fill=BG)
        f.rect(TX1, 0, W, H, fill=BG)
        f.rect(0, 0, W, TY0, fill=BG)
        f.rect(0, TY1, W, H, fill=BG)
        f.rect(TX0, TY0, TX1, TY1, outline=STOCK_EDGE)
        f.tag(TX1 + 8, TY0, "Angle %d°" % ang)
        f.caption("Angle: γυρίζει τις γραμμές του μοτίβου κατά %d°" % ang)
        fr.append((f, 1300))
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
            f.caption("Climb: το δόντι μπαίνει χοντρά και βγαίνει λεπτά" if mode == "Climb" else
                      "Conventional: το δόντι μπαίνει λεπτά και βγαίνει χοντρά")
            fr.append((f, 90))
        f = fr[-1][0]
        fr.append((f, 400))
    f = Frame()
    f.title("Ποιο να διαλέξω;")
    lines = ["Climb (ομόρροπη)", "  • πιο καθαρά τοιχώματα, λιγότερη φθορά φρέζας",
             "  • η συνήθης επιλογή στα CNC router (ξύλο/MDF)",
             "Conventional (αντίρροπη)", "  • για μηχανές με τζόγο (μπόσικες βίδες/ιμάντες)",
             "  • μερικές φορές πιο ήρεμο σε σκληρά υλικά"]
    for k, s in enumerate(lines):
        f.text(14, 36 + k * 26, s, fill=ACTIVE if not s.startswith(" ") else (40, 40, 40),
               font=F_LABEL if not s.startswith(" ") else F_SMALL)
    f.caption("Ο άξονας γυρίζει δεξιόστροφα (M3), όπως σχεδόν πάντα")
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
        f.circle((x0 + x1) / 2, (y0 + y1) / 2, 26, fill=(236, 228, 214), outline=PART_EDGE, width=2)


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
             "Outside: η φρέζα γυρίζει ΕΞΩ από τη γραμμή → κρατάς το κομμάτι",
             label=lambda f: f.tag(24, 26, "Cut side = Outside"))
    run_path(fr, lambda f: part_base(f, True), [(loop_circle((x0 + x1) / 2, (y0 + y1) / 2, 26 - r), "cut")], r, 30,
             "Inside: η φρέζα μένει ΜΕΣΑ στη γραμμή → για τρύπες/ανοίγματα",
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
             "Με Compensation: το κέντρο της φρέζας μένει μισή διάμετρο έξω",
             label=lambda f: f.tag(24, 26, "Use Compensation ✓"))
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, 0), "cut")], r, 36,
             "Χωρίς: το κέντρο πάει ΠΑΝΩ στη γραμμή → τρώει το κομμάτι",
             label=lambda f: (f.tag(24, 26, "Use Compensation ✗", fill=DIM), eaten(f)))
    fr.append((fr[-1][0], 1600))
    return fr


@gif("profile_direction")
def profile_direction():
    fr = []
    r = 11
    x0, y0, x1, y1 = PART_R
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r, cw=True), "cut")], r, 36,
             "CW (δεξιόστροφα) γύρω από το κομμάτι = Climb",
             label=lambda f: f.tag(24, 26, "Direction = CW"))
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r, cw=False), "cut")], r, 36,
             "CCW (αριστερόστροφα) γύρω από το κομμάτι = Conventional",
             label=lambda f: f.tag(24, 26, "Direction = CCW"))
    f = Frame()
    f.title("Direction (κατεύθυνση)")
    for k, s in enumerate(["Εξωτερικό περίγραμμα:  CW = Climb,  CCW = Conventional",
                           "Εσωτερικό (τρύπα):       CCW = Climb,  CW = Conventional",
                           "(με τον άξονα να γυρίζει κανονικά, M3)"]):
        f.text(14, 50 + k * 30, s, fill=(40, 40, 40), font=F_LABEL if k < 2 else F_SMALL)
    f.caption("Δες και το «Cut mode» για το τι σημαίνει Climb")
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
    run_path(fr, part_base, segs, r, 70, "Number of passes 3, Pass stepover 8 mm: 3 γύροι",
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
             "Stock to leave: αφήνει λίγο υλικό (μπλε) στα τοιχώματα",
             label=lambda f: f.tag(24, 26, "Radial stock to leave = 0.5 mm"))
    run_path(fr, part_base, [(loop_rect(x0, y0, x1, y1, r), "cut")], r, 36,
             "Μετά ένα ελαφρύ τελικό πέρασμα το καθαρίζει → λεία τοιχώματα",
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
    hold(fr, s.frame(a, RX, -11.0, "Axial stock to leave: αφήνει λίγο υλικό στον πάτο", extra=floor), 2200)
    s.cleared[-1] = (PX0, 0, PX1, -12.0)
    move(s, fr, LX, -12.0, RX, -12.0, 12, FEED, active=a, caption="Ένα επόμενο πέρασμα το καθαρίζει στο σωστό βάθος")
    hold(fr, s.frame(a, RX, -12.0, "Ένα επόμενο πέρασμα το καθαρίζει στο σωστό βάθος"), 1500)
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
    run_path(fr, base_island, segs, R_TOP, 50, "Χωρίς: σέβεται το «νησί» στη μέση της τσέπης",
             label=lambda f: f.tag(TX1 + 8, TY0, "Use outline ✗", fill=DIM))
    fr.append((fr[-1][0], 900))
    run_path(fr, base_island, [(zz, "cut")], R_TOP, 50, "Με Use outline: αγνοεί τρύπες/νησιά, κόβει όλο το περίγραμμα",
             label=lambda f: f.tag(TX1 + 8, TY0, "Use outline ✓"))
    fr.append((fr[-1][0], 1500))
    return fr


@gif("pass_extension")
def pass_extension():
    fr = []
    st = R_TOP * 1.4
    for ext, cap in ((0, "Pass Extension 0: κάθε γραμμή σταματά στην άκρη"),
                     (16, "Pass Extension 3 mm: βγαίνει λίγο έξω → καθαρή άκρη")):
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
    fr.append((drill_scene(("final",), LEVELS["safe"], 0, "Peck: τρυπάει λίγο-λίγο και βγαίνει να καθαρίσει", extra=rline), 1600))
    while depth > LEVELS["final"]:
        nd = max(LEVELS["final"], depth - q)
        for i in range(6):
            fr.append((drill_scene(("final",), lerp(depth, nd, i / 5), min(depth, lerp(depth, nd, i / 5)),
                                   "Κατεβαίνει %g mm (Peck depth)" % q, extra=rline), 70))
        depth = nd
        for i in range(5):
            fr.append((drill_scene(("final",), lerp(depth, R, i / 4), depth,
                                   "Βγαίνει ως το R → φεύγουν τα ρινίσματα", extra=rline), 60))
        fr.append((fr[-1][0], 250))
    fr.append((drill_scene(("final",), R, depth, "Χωρίς Peck θα πήγαινε μονορούφι → κινδυνεύει να σπάσει", extra=rline), 2000))
    return fr


@gif("dwell")
def dwell():
    fr = []
    for i in range(8):
        z = lerp(LEVELS["safe"], LEVELS["final"], i / 7)
        fr.append((drill_scene(("final",), z, min(0, z), "Κατεβαίνει στον πάτο της τρύπας"), 70))
    for k in range(3, 0, -1):
        def clock(f, k=k):
            f.tag(HOLE_X + 22, zy(-9), "περιμένει… %d" % k, fill=PATH)
        fr.append((drill_scene(("final",), LEVELS["final"], LEVELS["final"], "Dwell: σταματά λίγο στον πάτο (Dwell time)", extra=clock), 600))
    for i in range(6):
        z = lerp(LEVELS["final"], LEVELS["safe"], i / 5)
        fr.append((drill_scene(("final",), z, LEVELS["final"], "Καθαρός, ίσιος πάτος → μετά ανεβαίνει"), 70))
    fr.append((fr[-1][0], 1200))
    return fr


@gif("drill_extra_offset")
def drill_extra_offset():
    fr = []

    def tipline(f):
        f.dashed(HOLE_X - 30, zy(LEVELS["final"] - 1.2), HOLE_X + 30, zy(LEVELS["final"] - 1.2), PATH, 1.5)
    fr.append((drill_scene(("final",), LEVELS["final"], LEVELS["final"],
                           "Το τρυπάνι έχει μύτη: στο Final Depth η τρύπα στενεύει"), 2200))
    fr.append((drill_scene(("final",), LEVELS["final"] - 1.2, LEVELS["final"] - 1.2,
                           "Extra Offset: πάει λίγο πιο βαθιά → πλήρης διάμετρος", extra=tipline), 2400))
    return fr


@gif("peck_retract")
def peck_retract():
    fr = []
    R = 2.0

    def rline(f):
        f.dashed(HOLE_X - 50, zy(R), HOLE_X + 50, zy(R), ACTIVE, 2)
        f.text(HOLE_X + 54, zy(R), "Peck Retract (R)", fill=ACTIVE, font=F_LABEL, anchor="lm")
    for i in range(6):
        fr.append((drill_scene((), lerp(-6, R, i / 5), -6, "Peck Retract: πόσο ανεβαίνει ανάμεσα στα «τσιμπήματα»",
                               extra=rline, show=("clear", "safe", "final")), 80))
    fr.append((fr[-1][0], 2000))
    fr.append((drill_scene((), R, -6, "Λίγο πάνω από το υλικό αρκεί (π.χ. 1–2 mm)", extra=rline,
                           show=("clear", "safe", "final")), 2000))
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
        fr.append((s.frame(("final",), x, z_now, "Helix: μπαίνει στο υλικό σαν βίδα, όχι κάθετα"), 70))
    fr.append((fr[-1][0], 1500))
    fr.append((s.frame(("final",), cx, LEVELS["final"], "Max pitch / ramp angle: πόσο απότομα κατεβαίνει"), 2200))
    return fr


@gif("retract_threshold")
def retract_threshold():
    s = Side()
    fr = []
    a = ()
    s.cleared = [(60, 0, 130, -6), (170, 0, 250, -6)]
    hold(fr, s.frame(a, 95, -6, "Δύο κοντινές περιοχές: πώς πάει από τη μία στην άλλη;"), 1500)
    move(s, fr, 95, -6, 95, LEVELS["clear"], 6, RAPID, caption="Χωρίς: ανεβαίνει ψηλά, πάει, ξανακατεβαίνει (αργό)")
    move(s, fr, 95, LEVELS["clear"], 210, LEVELS["clear"], 8, RAPID, caption="Χωρίς: ανεβαίνει ψηλά, πάει, ξανακατεβαίνει (αργό)")
    move(s, fr, 210, LEVELS["clear"], 210, -6, 6, RAPID, caption="Χωρίς: ανεβαίνει ψηλά, πάει, ξανακατεβαίνει (αργό)")
    s.trail = []
    move(s, fr, 95, -6, 95, 1, 3, RAPID, caption="Retract threshold: αν είναι κοντά, πάει «χαμηλά»")
    move(s, fr, 95, 1, 210, 1, 8, RAPID, caption="Retract threshold: αν είναι κοντά, πάει «χαμηλά»")
    move(s, fr, 210, 1, 210, -6, 3, RAPID, caption="Retract threshold: αν είναι κοντά, πάει «χαμηλά»")
    hold(fr, s.frame(a, 210, -6, "Λιγότερες άσκοπες ανεβοκατεβάσεις = πιο γρήγορα"), 1600)
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

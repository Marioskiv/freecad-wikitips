# SPDX-License-Identifier: LGPL-2.1-or-later
"""Small drawing kit for the WikiTips teaching animations (build time only).

Needs Pillow and the DejaVu fonts (Greek). Not used by the addon at runtime.
Everything is drawn at 2x and scaled down for smooth lines.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 416, 250          # final size; fits the popup without scaling
SS = 2                   # supersampling
CAP_H = 34               # caption bar height

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"]


def _font(name, size):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size * SS)
    raise RuntimeError("DejaVu font %s not found" % name)


F_SMALL = _font("DejaVuSans.ttf", 11)
F_LABEL = _font("DejaVuSans-Bold.ttf", 11)
F_CAP = _font("DejaVuSans-Bold.ttf", 12)
F_BIG = _font("DejaVuSans-Bold.ttf", 14)

# palette (kept in one place so every animation looks the same)
# v4 (2026-10-16): Marios found the wood-brown stock old-fashioned. Modern CAM look: a light
# slate block, graphite tool with an amber ring, indigo tool paths, rose = setting explained.
BG = (248, 250, 252)
STOCK = (214, 222, 233)          # block (drawn with a soft top-to-bottom gradient)
STOCK_BOTTOM = (178, 191, 209)
STOCK_EDGE = (100, 116, 139)
CUT = (255, 255, 255)            # floor of what has been cut, seen from above
PART = (224, 231, 255)
PART_EDGE = (79, 70, 229)
TOOL = (71, 85, 105)
TOOL_HI = (148, 163, 184)
SHANK = (30, 41, 59)
RING = (245, 158, 11)
ACTIVE = (225, 29, 72)           # rose: the setting being explained
DIM = (148, 163, 184)
RAPID = (16, 185, 129)
FEED = (245, 158, 11)
PATH = (79, 70, 229)
LEFT = (253, 224, 120)           # material left on purpose (stock to leave)
CAP_BG = (15, 23, 42)            # caption pill (slate 900)
WARN_BG = (190, 18, 60)
AMBER = (245, 158, 11)
SHADOW = (226, 232, 240)
WHITE = (255, 255, 255)


class Frame:
    """One picture. Coordinates are in final pixels; drawing happens at SS x."""

    def __init__(self, bg=BG):
        self.im = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.im)

    # -- primitives (final-pixel coordinates) ------------------------------
    def _p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        if fill == STOCK:        # wood gets a soft shadow and grain
            self.wood(x0, y0, x1, y1, outline)
            return
        self.d.rectangle([min(x0, x1) * SS, min(y0, y1) * SS, max(x0, x1) * SS, max(y0, y1) * SS],
                         fill=fill, outline=outline, width=width * SS)

    def wood(self, x0, y0, x1, y1, outline=None):
        """The stock block: soft gradient, light top edge, small shadow (no wood grain)."""
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        self.d.rounded_rectangle([(x0 + 3) * SS, (y0 + 4) * SS, (x1 + 3) * SS, (y1 + 4) * SS], 3 * SS, fill=SHADOW)
        n = max(2, int((y1 - y0) * SS))
        for i in range(n):
            t = i / (n - 1)
            c = tuple(int(a + (b - a) * t) for a, b in zip(STOCK, STOCK_BOTTOM))
            self.d.line([(x0 * SS, y0 * SS + i), (x1 * SS, y0 * SS + i)], fill=c)
        self.d.line([(x0 * SS, y0 * SS + SS), (x1 * SS, y0 * SS + SS)], fill=(241, 245, 249), width=SS)
        self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], outline=outline or STOCK_EDGE, width=SS)

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=1):
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], r * SS,
                                 fill=fill, outline=outline, width=width * SS)

    def poly(self, pts, fill=None, outline=None, width=1):
        self.d.polygon(self._p(pts), fill=fill, outline=outline, width=width * SS)

    def line(self, pts, fill, width=1):
        self.d.line(self._p(pts), fill=fill, width=max(1, int(width * SS)), joint="curve")

    def dashed(self, x0, y0, x1, y1, fill, width=1, dash=5, gap=4):
        L = math.hypot(x1 - x0, y1 - y0)
        if L == 0:
            return
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        s = 0.0
        while s < L:
            e = min(L, s + dash)
            self.line([(x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)], fill, width)
            s = e + gap

    def circle(self, cx, cy, r, fill=None, outline=None, width=1):
        self.d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS],
                       fill=fill, outline=outline, width=width * SS)

    def arc(self, cx, cy, r, a0, a1, fill, width=1):
        self.d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], a0, a1,
                   fill=fill, width=int(width * SS))

    def arrow(self, x0, y0, x1, y1, fill, width=2, head=6):
        self.line([(x0, y0), (x1, y1)], fill, width)
        a = math.atan2(y1 - y0, x1 - x0)
        p1 = (x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45))
        p2 = (x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))
        self.poly([(x1, y1), p1, p2], fill=fill)

    def text(self, x, y, s, fill=(40, 40, 40), font=F_SMALL, anchor="la"):
        self.d.text((x * SS, y * SS), s, fill=fill, font=font, anchor=anchor)

    def tag(self, x, y, s, fill=ACTIVE, font=F_LABEL, anchor="la"):
        """Text on a white rounded background, readable over drawings."""
        bb = self.d.textbbox((x * SS, y * SS), s, font=font, anchor=anchor)
        pad = 3 * SS
        self.d.rounded_rectangle([bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad], 4 * SS,
                                 fill=(255, 255, 255), outline=fill, width=SS)
        self.d.text((x * SS, y * SS), s, fill=fill, font=font, anchor=anchor)

    def caption(self, s, warn=False):
        """Floating rounded caption, like the Sketcher animations."""
        font = F_CAP
        tw = self.d.textlength(s, font=font) / SS
        if tw > W - 44:
            font = F_LABEL
            tw = self.d.textlength(s, font=font) / SS
        w = min(W - 12, tw + 34)
        x0, y0, h = (W - w) / 2, H - CAP_H + 4, CAP_H - 8
        self.rrect(x0, y0, x0 + w, y0 + h, h / 2, fill=WARN_BG if warn else CAP_BG)
        self.circle(x0 + 12, y0 + h / 2, 4, fill=(255, 210, 120) if warn else AMBER)
        self.text(x0 + 22, y0 + h / 2, s, fill=WHITE, font=font, anchor="lm")

    def title(self, s, color=CAP_BG):
        self.text(8, 6, s, fill=color, font=F_BIG)

    # -- CAM pieces ---------------------------------------------------------
    def endmill_side(self, x, ytip, d=18, flute_len=34, color=TOOL):
        """Flat end mill seen from the side, tip centre at (x, ytip)."""
        r = d / 2
        self.metal(x - r, ytip - flute_len, x + r, ytip, color)
        for k in range(int(flute_len / 9)):
            yy = ytip - 4 - k * 9
            self.line([(x - r, yy), (x + r, yy - 5)], TOOL_HI, 1.5)
        self.metal(x - r * 0.7, ytip - flute_len - 16, x + r * 0.7, ytip - flute_len, SHANK)
        self.rect(x - r * 0.7, ytip - flute_len - 3, x + r * 0.7, ytip - flute_len, fill=RING)

    def metal(self, x0, y0, x1, y1, color):
        """Rectangle shaded like a round bar lit from the left."""
        w = x1 - x0
        n = max(2, int(w * SS))
        for i in range(n):
            t = i / (n - 1)
            k = 1.0 - abs(t - 0.32) * 1.3          # highlight left of centre
            c = tuple(int(min(255, ch + 70 * max(0.0, k) - 25)) for ch in color)
            xx = x0 * SS + i
            self.d.line([(xx, y0 * SS), (xx, y1 * SS)], fill=c)

    def drill_side(self, x, ytip, d=14, length=36):
        r = d / 2
        tip = r * 0.6
        self.poly([(x - r, ytip - tip), (x + r, ytip - tip), (x, ytip)], fill=TOOL)
        self.metal(x - r, ytip - length, x + r, ytip - tip, TOOL)
        for k in range(int((length - tip) / 9)):
            yy = ytip - tip - 4 - k * 9
            self.line([(x - r, yy), (x + r, yy - 6)], TOOL_HI, 1.5)
        self.metal(x - r * 0.7, ytip - length - 14, x + r * 0.7, ytip - length, SHANK)

    def tool_top(self, cx, cy, r, angle=0.0, color=TOOL, alpha_ring=True):
        """End mill seen from above, with 2 flutes rotated by `angle` (radians)."""
        self.circle(cx + 2, cy + 3, r, fill=SHADOW)
        self.circle(cx, cy, r, fill=color, outline=SHANK, width=1)
        self.circle(cx - r * 0.3, cy - r * 0.3, r * 0.45, fill=TOOL_HI)
        for k in range(2):
            a = angle + k * math.pi
            self.line([(cx, cy), (cx + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a))],
                      (190, 205, 225), 2)
        self.circle(cx, cy, 2, fill=(230, 235, 240))

    def spin_arrow(self, cx, cy, r, cw=True, color=ACTIVE):
        """Rotation arrow around a tool seen from above (CW on screen = CW from above)."""
        a0, a1 = (200, 320) if cw else (320, 200)
        self.arc(cx, cy, r, min(a0, a1), max(a0, a1), color, 2)
        end = math.radians(a1)
        ex, ey = cx + r * math.cos(end), cy + r * math.sin(end)
        tang = end + (math.pi / 2 if cw else -math.pi / 2)
        self.arrow(ex - 4 * math.cos(tang), ey - 4 * math.sin(tang), ex + 2 * math.cos(tang),
                   ey + 2 * math.sin(tang), color, 2, 6)

    def image(self):
        return self.im.resize((W, H), Image.LANCZOS)


SLOWER = 1.3   # Marios (2026-10-17): "a bit slower, but not too slow" — all animations


def save_gif(frames, path):
    """frames: list of (Frame or PIL image, duration_ms)."""
    ims = [(f.image() if isinstance(f, Frame) else f) for f, _ in frames]
    durs = [int(ms * SLOWER) for _, ms in frames]
    # one shared palette (from a sample of all frames) keeps colours stable and the file small
    sample = ims[::max(1, len(ims) // 12)]
    sample += [im for im, ms in zip(ims, durs) if ms >= 1000][:8]   # the held frames carry the labels
    sheet = Image.new("RGB", (W, H * len(sample)))
    for i, im in enumerate(sample):
        sheet.paste(im, (0, H * i))
    pal = sheet.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0,
              optimize=True, disposal=1)
    return path


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))

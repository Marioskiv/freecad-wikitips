# SPDX-License-Identifier: LGPL-2.1-or-later
"""Turn recorded Sketcher scenes into animated GIFs (step 2 of 2).

    python3 tools/gifs/sketcher_gifs.py <recordings dir> content/img/sketcher [names...]

Adds what a person would see: the mouse cursor gliding to each click, an
expanding ring where it clicks, and a numbered Greek step badge that changes
with every step (idea seen in other CAD help, drawn in our own style).
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw import F_CAP, F_LABEL, W, H, save_gif, ease  # noqa: E402

ACCENT = (245, 158, 11)       # amber: click ring + step number
PILL = (15, 23, 42)           # caption pill (slate 900)
FRAME_MS = 50

CURSOR = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]


def draw_cursor(d, x, y):
    pts = [(x + px, y + py) for px, py in CURSOR]
    d.polygon([(a + 2, b + 3) for a, b in pts], fill=(0, 0, 0, 60))
    d.polygon(pts, fill=(255, 255, 255), outline=(17, 24, 39), width=3)


def draw_ring(d, x, y, t):
    r = 8 + 26 * t
    w = max(2, int(7 * (1 - t)))
    d.ellipse([x - r, y - r, x + r, y + r], outline=ACCENT + (int(255 * (1 - t * 0.7)),), width=w)
    if t < 0.5:
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=ACCENT + (200,))


def draw_caption(d, n, text, size):
    Wb, Hb = size
    if not text:
        return
    pad, h = 14, 52
    font = F_CAP
    if d.textlength(text, font=font) > Wb - 24 - 2 * pad - (50 if n else 0):
        font = F_LABEL          # long sentence: a size smaller, never cut off
    tw = d.textlength(text, font=font)
    badge = 40 if n else 0
    w = min(Wb - 24, tw + 2 * pad + badge + (10 if n else 0))
    x0 = (Wb - w) / 2
    y0 = Hb - h - 14
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 26, fill=PILL + (236,))
    tx = x0 + pad
    if n:
        cx, cy = x0 + pad + 18, y0 + h / 2
        d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=ACCENT)
        d.text((cx, cy), str(n), font=F_CAP, fill=(15, 23, 42), anchor="mm")
        tx += badge + 10
    d.text((tx, y0 + h / 2), text, font=font, fill=(255, 255, 255), anchor="lm")


BTN = (22, 22, 92)    # x, y, size of the toolbar button drawn top-left (2x pixels)


def draw_button(base_rgba, icon, pressed):
    """The command's real icon as a toolbar button; amber frame once it is pressed."""
    d = ImageDraw.Draw(base_rgba)
    x, y, s = BTN
    d.rounded_rectangle([x + 3, y + 4, x + s + 3, y + s + 4], 16, fill=(0, 0, 0, 40))
    d.rounded_rectangle([x, y, x + s, y + s], 16, fill=(255, 247, 230) if pressed else (255, 255, 255),
                        outline=ACCENT if pressed else (203, 213, 225), width=5 if pressed else 2)
    if icon is not None:
        base_rgba.alpha_composite(icon, (int(x + (s - icon.width) / 2), int(y + (s - icon.height) / 2)))


F_MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 25)
F_PTXT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
F_PTIT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)


PANEL_LH = 36


def panel_box(d, panel, size):
    """Where the card goes: right (G-code, reports) or left under the button (model tree)."""
    Wb, Hb = size
    font = F_MONO if panel.get("mono", True) else F_PTXT
    lines = panel["lines"]
    w = max([d.textlength(panel["title"], font=F_PTIT)] + [d.textlength(x, font=font) for x in lines]) + 48
    w = min(w, Wb * 0.56)
    h = 70 + PANEL_LH * len(lines) + 18
    x0, y0 = (26, 140) if panel.get("pos") == "left" else (Wb - w - 26, 30)
    return x0, y0, w, h, font


def panel_row(d, panel, size, i):
    x0, y0, w, h, font = panel_box(d, panel, size)
    return x0 + 22 + min(d.textlength(panel["lines"][i], font=font), 160) * 0.5, y0 + 74 + i * PANEL_LH + PANEL_LH / 2 - 4


def draw_panel(d, panel, size):
    """A card: real G-code lines, a report, a list, or the model tree (pos=left, sel=row)."""
    if not panel or not panel.get("title"):
        return
    lines = panel["lines"]
    lh = PANEL_LH
    x0, y0, w, h, font = panel_box(d, panel, size)
    d.rounded_rectangle([x0 + 4, y0 + 6, x0 + w + 4, y0 + h + 6], 18, fill=(0, 0, 0, 45))
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 18, fill=(255, 255, 255, 250), outline=(203, 213, 225), width=2)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 56], 18, fill=(15, 23, 42, 250))
    d.rectangle([x0, y0 + 36, x0 + w, y0 + 56], fill=(15, 23, 42, 250))
    d.text((x0 + 22, y0 + 28), panel["title"], font=F_PTIT, fill=(255, 255, 255), anchor="lm")
    for i, ln in enumerate(lines):
        if panel.get("sel") == i:
            d.rounded_rectangle([x0 + 10, y0 + 70 + i * lh - 2, x0 + w - 10, y0 + 70 + (i + 1) * lh - 4], 8,
                                fill=(209, 250, 229, 255), outline=(16, 185, 129), width=2)
        col = (225, 29, 72) if ln.startswith("⚠") or "←" in ln else (30, 41, 59)
        if font is F_MONO and ln[:2] in ("G0", "G1", "G2", "G3", "G8", "G9"):
            col = (79, 70, 229) if ln[:3] != "G0 " else (16, 120, 90)
        d.text((x0 + 22, y0 + 74 + i * lh + lh / 2 - 4), ln, font=font, fill=col, anchor="lm")


def load(path):
    """Key frame with thicker lines: FreeCAD draws 1 px lines and the GIF is half size."""
    return Image.open(path).convert("RGB").filter(ImageFilter.MinFilter(3))


def render(rec_dir, out_path):
    meta = json.load(open(os.path.join(rec_dir, "events.json"), encoding="utf-8"))
    size = tuple(meta["size"])
    frames = []
    first = next(e for e in meta["events"] if e["t"] == "img")   # scene before the first click
    base = load(os.path.join(rec_dir, first["f"]))
    cur = [size[0] * 0.82, size[1] * 0.2]
    cap = (0, "")
    icon = None
    if meta.get("icon"):
        icon = Image.open(os.path.join(rec_dir, meta["icon"])).convert("RGBA").resize((64, 64), Image.LANCZOS)
    pressed = [False]
    panel = [None]

    def emit(ms, ring=None, img=None):
        im = (img or base).convert("RGBA")
        if icon is not None:
            draw_button(im, icon, pressed[0])
        ov = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        if ring is not None:
            draw_ring(d, cur[0], cur[1], ring)
        draw_panel(d, panel[0], size)
        draw_cursor(d, cur[0], cur[1])
        draw_caption(d, cap[0], cap[1], size)
        im = Image.alpha_composite(im, ov).convert("RGB")
        frames.append((im.resize((W, H), Image.LANCZOS), ms))

    for ev in meta["events"]:
        t = ev["t"]
        if t == "img":
            new = load(os.path.join(rec_dir, ev["f"]))
            if ev.get("blend") and base is not None:
                for k in range(1, 6):
                    emit(70, img=Image.blend(base, new, k / 5))
            base = new
        elif t == "cap":
            cap = (ev["n"], ev["text"])
        elif t == "move":
            x0, y0 = cur
            x1, y1 = ev["to"]
            n = max(2, int(ev["ms"] / FRAME_MS))
            if math.hypot(x1 - x0, y1 - y0) < 3:
                n = 1
            for k in range(1, n + 1):
                e = ease(k / n)
                cur = [x0 + (x1 - x0) * e, y0 + (y1 - y0) * e]
                emit(FRAME_MS)
        elif t == "click":
            for k in range(5):
                emit(60, ring=k / 4)
        elif t == "press" and icon is not None:
            x0, y0 = cur
            x1, y1 = BTN[0] + BTN[2] * 0.55, BTN[1] + BTN[2] * 0.6
            n = 10
            for k in range(1, n + 1):
                e = ease(k / n)
                cur = [x0 + (x1 - x0) * e, y0 + (y1 - y0) * e]
                emit(FRAME_MS)
            pressed[0] = True
            for k in range(5):
                emit(60, ring=k / 4)
            emit(350)
        elif t == "panel":
            panel[0] = ev if ev.get("title") else None
            emit(300)
        elif t == "pick" and panel[0]:
            # click a row of the card (e.g. the Job in the tree), then show it selected
            probe = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
            x1, y1 = panel_row(probe, panel[0], size, ev["row"])
            x0, y0 = cur
            for k in range(1, 11):
                e = ease(k / 10)
                cur = [x0 + (x1 - x0) * e, y0 + (y1 - y0) * e]
                emit(FRAME_MS)
            panel[0] = dict(panel[0], sel=ev["row"])
            for k in range(5):
                emit(60, ring=k / 4)
        elif t == "hold":
            emit(ev["ms"])
    emit(1200)
    save_gif(frames, out_path)
    return out_path


def main():
    src, dst = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    for name in sorted(os.listdir(src)):
        d = os.path.join(src, name)
        if not os.path.exists(os.path.join(d, "events.json")) or (only and name not in only):
            continue
        p = render(d, os.path.join(dst, name + ".gif"))
        print("%-38s %6.1f KB" % (name, os.path.getsize(p) / 1024))


if __name__ == "__main__":
    main()

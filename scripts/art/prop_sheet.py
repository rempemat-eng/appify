"""A contact sheet for a prop library (world-rules.md 2a: a prop is checked "under the night
tint and on another ground" before it is handed on). Each prop stands on a patch of
ground with the cast shadow the zones throw for it (detail.silhouette_shadow), in three
rows: on the meadow by day; on the meadow at night, under the world's night tint with any
windows (garden_props.WINDOWS) and lamps (atlas-walk.tsx, LAMPS) lit above it as the
world draws them; and on a second ground (sand, snow or flagstones) by day.

    sheet(props_dict, path, second='sand')

The prop modules call it when run directly (python3 scripts/art/valley_props.py);
contact_sheet.py is the other sheet, of every zone prop grouped by region."""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw  # noqa: E402

import detail  # noqa: E402
import garden_props as gp  # noqa: E402
import style  # noqa: E402
from materials import G, MATERIALS  # noqa: E402
from pixel import Canvas, noise2  # noqa: E402

# atlas-walk.tsx and world-scene.tsx: the night tint over the world, and a lit pane
NIGHT = (22, 28, 66, int(0.42 * 255))
PANE = (255, 200, 104, int(0.92 * 255))
GROUNDS = {
    'meadow': [G[2], G[3]],
    'sand': [MATERIALS['sand'][1], MATERIALS['sand'][2]],
    'snow': [MATERIALS['snow'][2], MATERIALS['snow'][3]],
    'flags': [MATERIALS['stone'][2], MATERIALS['stone'][3]],
}
PAD = 8


def _lamps() -> dict:
    """Where each lamp's light sits on its sprite, read from the renderer (atlas-walk.tsx,
    LAMPS), so the sheet lights them as the world does."""
    src = open(os.path.join(os.path.dirname(__file__), '..', '..', 'components', 'atlas-walk.tsx')).read()
    block = src[src.index('const LAMPS'):]
    block = block[:block.index('};')]
    return {k: (int(x), int(y)) for k, x, y in re.findall(r"(\w+): \[(\d+), (\d+)\]", block)}


LAMPS = _lamps()


def _glow(img: Image.Image, cx: float, cy: float, rx: float, ry: float, rgba):
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rgba)
    img.alpha_composite(layer)


def _patch(w: int, h: int, ground: str) -> Canvas:
    a, b = GROUNDS[ground]
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            cv.set(x, y, a if noise2(x // 3, y // 2, 7) < 0.7 else b)
    return cv


def _cell(key: str, raw: Canvas, fin: Canvas, ground: str, night: bool) -> Image.Image:
    w, h = fin.w + PAD * 2 + 10, fin.h + PAD * 2
    cv = _patch(w, h, ground)
    x0, y0 = PAD, PAD
    for (sx, sy) in detail.silhouette_shadow(fin, x0, y0):
        style.darken(cv, sx, sy)
    img = cv.img.copy()
    img.alpha_composite(fin.img, (x0, y0))
    if night:
        img.alpha_composite(Image.new('RGBA', img.size, NIGHT))
        for (c, (gx, gy, gw, gh)) in gp.WINDOWS:
            if c is raw:
                img.alpha_composite(Image.new('RGBA', (gw, gh), PANE), (x0 + gx - fin.ox, y0 + gy - fin.oy))
        if key in LAMPS:  # a lamp's pool on the ground, its halo and its bright core
            lx, ly = x0 + LAMPS[key][0], y0 + LAMPS[key][1]
            _glow(img, lx, y0 + fin.h, 14, 6, (255, 214, 122, 56))
            _glow(img, lx, ly, 8, 8, (255, 214, 122, 89))
            _glow(img, lx, ly, 3, 3, (255, 240, 200, 204))
    return img


def sheet(items: dict[str, Canvas], path: str, second: str = 'sand', scale: int = 3, wrap: int = 900) -> tuple[int, int]:
    """Lay the props out in rows of at most `wrap` px; each row is drawn three times (day,
    night, the second ground). Returns the sheet's size."""
    fins = {k: style.finalize(v, name=k) for k, v in items.items()}
    lines, line, width = [], [], 0
    for k in items:
        cw = fins[k].w + PAD * 2 + 10
        if line and width + cw > wrap:
            lines.append(line); line, width = [], 0
        line.append(k); width += cw
    if line:
        lines.append(line)
    bands = []
    for keys in lines:
        for (ground, night) in (('meadow', False), ('meadow', True), (second, False)):
            cells = [_cell(k, items[k], fins[k], ground, night) for k in keys]
            band = Image.new('RGBA', (sum(c.width for c in cells), max(c.height for c in cells)), (40, 40, 48, 255))
            x = 0
            for c in cells:
                band.alpha_composite(c, (x, band.height - c.height)); x += c.width
            bands.append(band)
    out = Image.new('RGBA', (max(b.width for b in bands), sum(b.height + 2 for b in bands)), (40, 40, 48, 255))
    y = 0
    for b in bands:
        out.alpha_composite(b, (0, y)); y += b.height + 2
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    out.save(path)
    return out.size

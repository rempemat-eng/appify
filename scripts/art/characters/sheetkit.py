"""Design-sheet kit for the cast (Claude J, docs/vision/characters/).

A tiny drawing layer for character design sheets at the rig's density (2x: an adult
about 50 art px). Every pixel is stored as (family, tone) on the house palette
(scripts/art/house_palette.py), so shading moves along a material's own ramp and the
outline is each material's edge tone with the lit break (house-style 1 to 4).

    fig = Fig(64, 72)
    body = fig.ellipse(32, 40, 9, 12)
    fig.shade(body, 'clay')            # parts shading, light from the upper left
    fig.put(30, 30, 'ink', 0)          # eyes are ink
    fig.outline()                      # edge tone per family, lit break on tone 4-5
    img = fig.image()                  # PIL RGBA

`design_sheet(...)` lays a few options side by side for review: each view at 4x, the
same view at game scale (2 device px a texel) on house grass, its silhouette, its
palette and its numbers from style_lint.measure. Design sheets are review material:
production frames come from the shared rig (scripts/art/native/, Claude A).
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
sys.path.insert(0, ART)
import house_palette as hp  # noqa: E402

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

_PAL = hp.load()
RAMPS = _PAL['ramps']
EDGES = _PAL['edges']
INK = _PAL['ink']

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def family_of(name: str) -> str:
    """'clay_warm' -> 'clay' (a sibling shares its family's edge tone)."""
    for suffix in ('_warm', '_cool'):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def colour(fam: str, tone: int) -> str:
    if fam == 'ink':
        return INK
    if fam == 'edge':
        raise ValueError('edge needs a family: use edge_of')
    return RAMPS[fam][max(0, min(5, tone))]


def edge_of(fam: str) -> str:
    return EDGES[family_of(fam)]


class Fig:
    """A sprite being drawn: (x, y) -> (family, tone). 'ink' is the deep eye/gap colour."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.px: dict = {}
        self.fixed: set = set()   # pixels the outline pass must not treat as fill (glows)

    # --- masks -------------------------------------------------------------------
    def inside(self, x, y) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def ellipse(self, cx: float, cy: float, rx: float, ry: float) -> set:
        out = set()
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0 and self.inside(x, y):
                    out.add((x, y))
        return out

    def rect(self, x0: int, y0: int, x1: int, y1: int, knock: int = 0) -> set:
        """Inclusive rectangle; knock removes that many corner pixels (rounded corners)."""
        out = set()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                dx = min(x - x0, x1 - x)
                dy = min(y - y0, y1 - y)
                if knock and dx + dy < knock:
                    continue
                if self.inside(x, y):
                    out.add((x, y))
        return out

    def poly(self, pts) -> set:
        """Filled polygon (even-odd), pixel centres."""
        out = set()
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(int(min(ys)), int(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b))):
                    if self.inside(x, y):
                        out.add((x, y))
        return out

    def line(self, pts, fam: str, tone: int):
        """A 1 px polyline (Bresenham) in one tone: seams, stitches, a bow string."""
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = abs(x1 - x0), -abs(y1 - y0)
            sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
            err = dx + dy
            while True:
                self.put(x0, y0, fam, tone)
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x0 += sx
                if e2 <= dx:
                    err += dx
                    y0 += sy

    # --- paint -------------------------------------------------------------------
    def put(self, x, y, fam: str, tone: int):
        if self.inside(x, y):
            self.px[(x, y)] = (fam, tone)

    def fill(self, mask, fam: str, tone: int = 3):
        for p in mask:
            self.put(p[0], p[1], fam, tone)

    def shade(self, mask, fam: str, glint: bool = True, deep: bool = True, soft: float = 0.0):
        """Parts shading (house-style 3, 4): lit top-left planes tone 4, body 3, the
        lower right 2, the underside row 1, a two-pixel glint 5 at the top left. The
        terminator is one hard step. `soft` widens the body band for cloth or fur."""
        mask = set(mask)
        if not mask:
            return
        xs = [p[0] for p in mask]
        ys = [p[1] for p in mask]
        cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
        rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
        lit_cut, dark_cut = -0.55 - soft, 0.55 + soft
        for (x, y) in mask:
            u = (x + 0.5 - cx) / rx
            v = (y + 0.5 - cy) / ry
            n = 0.55 * u + 0.85 * v  # light from the upper left, a little more from above
            tone = 4 if n < lit_cut else 2 if n > dark_cut else 3
            if deep and (x, y + 1) not in mask and n > 0.1:
                tone = 1
            self.put(x, y, fam, tone)
        if glint:
            top = sorted(mask, key=lambda p: (0.55 * (p[0] - cx) / rx + 0.85 * (p[1] - cy) / ry))
            for p in top[:2]:
                self.put(p[0], p[1], fam, 5)

    def clusters(self, mask, fam: str, tone: int, pattern, step=(4, 3)):
        """Texture as 2-4 px clusters (dominoes, Ls) tiled through a mask: fur tufts,
        knit rows, oilskin creases. `pattern` is a list of (dx, dy) offsets."""
        mask = set(mask)
        xs = [p[0] for p in mask] or [0]
        ys = [p[1] for p in mask] or [0]
        row = 0
        for y in range(min(ys), max(ys) + 1, step[1]):
            off = (row % 2) * (step[0] // 2)
            for x in range(min(xs) + off, max(xs) + 1, step[0]):
                pts = [(x + dx, y + dy) for dx, dy in pattern]
                if all(p in mask for p in pts):
                    for p in pts:
                        self.put(p[0], p[1], fam, tone)
            row += 1

    def glow(self, x, y, fam: str, tone: int):
        """A light source pixel (lamp): never outlined."""
        self.put(x, y, fam, tone)
        self.fixed.add((x, y))

    def outline(self):
        """One pixel outside the silhouette in the edge tone of the family it closes;
        where it closes a lit (tone 4-5) top or left edge it breaks to tone 1."""
        add = {}
        for (x, y), (fam, tone) in list(self.px.items()):
            if fam == 'ink' or (x, y) in self.fixed:
                continue
            for dx, dy in N4:
                q = (x + dx, y + dy)
                if q in self.px or not self.inside(*q):
                    continue
                lit_side = dx == -1 or dy == -1
                if lit_side and tone >= 4:
                    c = ('_lit', fam)
                else:
                    c = ('_edge', fam)
                # prefer the darker claim when two families meet the same gap
                if q not in add or add[q][0] == '_lit':
                    add[q] = c
        for q, (kind, fam) in add.items():
            self.px[q] = (kind, fam)

    # --- out ---------------------------------------------------------------------
    def rgba(self, p):
        fam, tone = self.px[p]
        if fam == '_edge':
            h = edge_of(tone)
        elif fam == '_lit':
            h = colour(tone, 1)
        else:
            h = colour(fam, tone)
        r, g, b = hp.hex_rgb(h)
        return (r, g, b, 255)

    def image(self) -> Image.Image:
        img = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        for p in self.px:
            img.putpixel(p, self.rgba(p))
        return img

    def flipped_mask(self) -> set:
        return set(self.px)


def silhouette(img: Image.Image) -> Image.Image:
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    a = img.getchannel('A')
    out.paste((33, 26, 34, 255), mask=a)
    return out


def measure(img: Image.Image) -> dict:
    import style_lint  # noqa: E402 (needs art/materials.json; report only)
    return style_lint.measure(img)


# --- the review sheet ----------------------------------------------------------------
GRASS = hp.hex_rgb(RAMPS['grass'][3])
PAPER = (246, 240, 228)
TEXT = (33, 26, 34)


def _font(size=12):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def design_sheet(title: str, options: list, out_path: str, note: str = ''):
    """options: [{'label': 'A', 'name': ..., 'views': [(caption, PIL image)], 'parts': [...],
    'palette': [family, ...], 'pose': 'one line on personality', 'notes': [...]}]"""
    big = 4
    pad = 16
    f_title, f_head, f_body = _font(22), _font(15), _font(12)
    col_w = 0
    blocks = []
    for opt in options:
        views = opt['views']
        vw = sum(im.width * big + pad for _, im in views) + pad
        vh = max(im.height for _, im in views) * big
        col_w = max(col_w, vw, 560)
        blocks.append((opt, vw, vh))
    W = col_w + 2 * pad
    rows_h = []
    for opt, vw, vh in blocks:
        text_lines = 4 + len(opt.get('parts', [])) + len(opt.get('notes', []))
        gh = max(im.height for _, im in opt['views'][:3]) * 2
        rows_h.append(40 + vh + 24 + gh + 12 + 40 + 34 + text_lines * 16 + pad)
    H = 60 + (30 if note else 0) + sum(rows_h)
    sheet = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), title, fill=TEXT, font=f_title)
    y = 50
    if note:
        d.text((pad, y), note, fill=TEXT, font=f_body)
        y += 30
    for (opt, vw, vh), rh in zip(blocks, rows_h):
        d.text((pad, y), f"Option {opt['label']}: {opt['name']}", fill=TEXT, font=f_head)
        y += 26
        x = pad
        for cap, im in opt['views']:
            tile = Image.new('RGB', (im.width * big, im.height * big), GRASS)
            tile.paste(im.resize((im.width * big, im.height * big), Image.NEAREST), (0, 0),
                       im.resize((im.width * big, im.height * big), Image.NEAREST))
            sheet.paste(tile, (x, y))
            d.text((x, y + im.height * big + 2), cap, fill=TEXT, font=f_body)
            x += im.width * big + pad
        y += vh + 22
        # game scale (2 device px a texel), silhouette, palette
        x = pad
        for cap, im in opt['views'][:3]:
            g = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
            tile = Image.new('RGB', g.size, GRASS)
            tile.paste(g, (0, 0), g)
            sheet.paste(tile, (x, y))
            x += g.width + 6
        x += 10
        s = silhouette(opt['views'][0][1])
        s2 = s.resize((s.width * 2, s.height * 2), Image.NEAREST)
        sheet.paste(s2, (x, y), s2)
        y += max(im.height for _, im in opt['views'][:3]) * 2 + 12
        x = pad
        for fam in opt.get('palette', []):
            for t in range(6):
                d.rectangle([x + t * 8, y, x + t * 8 + 7, y + 14], fill=hp.hex_rgb(RAMPS[fam][t]))
            d.rectangle([x + 48, y, x + 55, y + 14], fill=hp.hex_rgb(edge_of(fam)))
            d.text((x, y + 16), fam, fill=TEXT, font=f_body)
            x += 70
            if x > W - 70:
                break
        y += 40
        m = measure(opt['views'][0][1])
        nums = (f"S view: {m['px']} px, {m['colours']} colours, on house {100 * m['on_house']:.0f}%, "
                f"outline dark {100 * m.get('outline_dark', 0):.0f}%, W-E {m['west_east']:+.1f}, "
                f"lone {100 * m['isolated']:.1f}%")
        d.text((pad, y), nums, fill=TEXT, font=f_body)
        y += 18
        d.text((pad, y), 'Personality: ' + opt.get('pose', ''), fill=TEXT, font=f_body)
        y += 16
        d.text((pad, y), 'Rig parts:', fill=TEXT, font=f_body)
        y += 16
        for p in opt.get('parts', []):
            d.text((pad + 12, y), '- ' + p, fill=TEXT, font=f_body)
            y += 16
        for n in opt.get('notes', []):
            d.text((pad, y), n, fill=TEXT, font=f_body)
            y += 16
        y = y + pad
    sheet = sheet.crop((0, 0, W, y + pad))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    return sheet

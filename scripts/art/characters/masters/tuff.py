"""Tuff's 1x master (Claude J, 21 Oct evening): the chosen 2x design drawn again at
density 1, the same golem at half the resolution (pixel art, never a downscale).

Matt, 21 Oct 18:17: all new art is drawn at density 2, the 1x design is the master and
every density draws the same design. This file holds the 1x drawing of S, E and W idle
(W drawn and lit on its own) as hand-placed texels on the house palette, then checks it
against the 2x final views (docs/vision/characters/designs/tuff-final.png):

  - the 2x alpha downscaled by 2 (a texel is solid when 2 of its 4 pixels are), aligned
    at the foot anchor, against the 1x alpha: silhouette IoU, at least 0.80;
  - the house families used, glows aside, the same at both densities.

Cell folkLarge 40 x 40, foot (20, 37); the 2x final cell is 80 x 80, foot (40, 74).

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/masters/tuff.py
(the 2x final views are read from $CHAR_VIEWS/tuff/final-<view>.png).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
import style_lint as sl  # noqa: E402
import house_palette as hp  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ID = 'tuff'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_DIR = os.path.join(ROOT, 'docs/vision/characters/masters')
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
CELL = (40, 40)
FOOT = (20, 37)
CELL2 = (80, 80)
FOOT2 = (40, 74)
GLOWS = {'lamp', 'neon_pink', 'neon_cyan', 'lava', 'glowflora'}

# Stamp tokens: a family letter, then a tone 0-5 or 'e' (that family's edge tone).
# '..' is empty. Glow families are light sources and never outlined.
LEGEND = {
    'B': 'basalt', 'W': 'basalt_warm', 'C': 'basalt_cool',
    'L': 'lagoon', 'M': 'lagoon_cool', 'S': 'sand',
    'R': 'berry', 'F': 'leaf', 'V': 'lava', 'K': 'ink',
}

# --- drawing ---------------------------------------------------------------------------
class Pic:
    """A 1x view painted back to front. Every part leaves a tone-0 seam on the parts it
    covers (the joint between two columns); the outside gets the edge-tone outline with
    the lit break from sheetkit at the end. Small hand-placed details (the turtle, the
    boulder head, thrift) are token stamps: a family letter and a tone 0-5 or 'e'."""

    def __init__(self):
        self.fig = sk.Fig(*CELL)

    def part(self, px: dict, seam: bool = True):
        if seam:
            for (x, y) in px:
                for dx, dy in sk.N4:
                    q = (x + dx, y + dy)
                    if q not in px and q in self.fig.px and q not in self.fig.fixed:
                        fam = self.fig.px[q][0]
                        if fam not in GLOWS and fam != 'ink':
                            self.fig.px[q] = (fam, 0)
        for (x, y), (fam, t) in px.items():
            if t == 'e':
                self.fig.px[(x, y)] = ('_edge', fam)
                self.fig.fixed.add((x, y))
            elif fam in GLOWS:
                self.fig.glow(x, y, fam, t)
            else:
                self.fig.put(x, y, fam, t)

    def image(self) -> Image.Image:
        self.fig.outline()
        return self.fig.image()


def column(x0, x1, y0, y1, fam, top=2) -> dict:
    """A hex column seen from the front-above: a lit top plane `top` rows deep (tone 4,
    the far end 3, a two-pixel glint 5), the west facet 3, the body 2, the east facet 1,
    the underside row 1; the top corners knocked off for the hex."""
    w = x1 - x0 + 1
    out = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if top and y == y0 and w >= 4 and x in (x0, x1):
                continue
            if y < y0 + top:
                t = 3 if x == x1 else 4
            elif y == y1:
                t = 2 if x == x0 else 1
            elif x == x0 or (w >= 6 and x == x0 + 1):
                t = 3
            elif x >= x1 - (1 if w >= 5 else 0):
                t = 1
            else:
                t = 2
            out[(x, y)] = (fam, t)
    if top >= 2 and w >= 4:
        out[(x0 + 1, y0)] = (fam, 5)
        out[(x0 + 2, y0)] = (fam, 5)
    return out


def stamp(x0, y0, rows) -> dict:
    out = {}
    for j, row in enumerate(rows):
        toks = row.split()
        for i, tok in enumerate(toks):
            if tok == '..':
                continue
            fam, t = LEGEND[tok[0]], tok[1]
            out[(x0 + i, y0 + j)] = (fam, t if t == 'e' else int(t))
    return out


def flip(px: dict) -> dict:
    """Mirror a part's placement (x -> 39 - x) for the W layout; tones are set again by
    the caller, so the light stays upper left."""
    return {(CELL[0] - 1 - x, y): v for (x, y), v in px.items()}


# Thrift: a berry head (3 x 3 at 2x) is a 2 x 2 cluster lit upper left on a leaf cushion.
THRIFT = ['.. R4 R4 ..',
          '.. R2 R2 ..',
          'F3 F3 F2 F2']
THRIFT2 = ['R4 R4 .. R4 R4',
           'R2 R2 F3 R2 R2',
           'F3 F3 F3 F2 F2']


def draw_S() -> Image.Image:
    p = Pic()
    p.part(column(5, 8, 22, 30, 'basalt_cool'))
    p.part(column(31, 34, 22, 30, 'basalt_cool'))
    p.part(column(9, 13, 19, 31, 'basalt', top=3))
    p.part(column(26, 30, 19, 31, 'basalt', top=3))
    p.part(column(14, 25, 20, 31, 'basalt_warm'))
    p.part(column(4, 7, 26, 33, 'basalt'))
    p.part(column(32, 35, 26, 33, 'basalt'))
    p.part(column(11, 15, 32, 36, 'basalt', top=0))
    p.part(column(24, 28, 32, 36, 'basalt', top=0))
    # the boulder head, low on the turtle column, ember eyes
    p.part(stamp(15, 25, [
        '.. W4 W4 W4 W3 W3 W3 W2 ..',
        'W4 W5 W5 W4 W3 W3 W3 W2 W1',
        'W4 W4 W3 W3 W3 W3 W3 W2 W1',
        'W3 W3 V3 W2 W2 W2 V3 W2 W1',
        'W3 W2 W2 W1 W1 W1 W2 W1 W1',
        '.. W2 W1 W1 W1 W1 W1 W1 ..',
    ]))
    # the turtle asleep on the middle column: sand head west, plated shell, flipper east
    p.part(stamp(14, 17, [
        '.. .. .. .. M4 M5 M5 M3 M3 .. .. ..',
        'S4 S4 S3 M4 M4 M3 M3 M2 M2 M2 .. ..',
        'S2 S2 S3 M1 M1 M1 M1 M1 M1 M1 M1 S3',
    ]), seam=False)
    p.part(stamp(5, 19, THRIFT[:2] + ['F3 F3 F2 ..']), seam=False)
    p.part(stamp(6, 34, THRIFT), seam=False)
    p.part(stamp(17, 34, THRIFT2), seam=False)
    p.part(stamp(30, 34, THRIFT), seam=False)
    return p.image()


def draw_EW(west: bool) -> Image.Image:
    p = Pic()
    f = flip if west else (lambda d: d)

    def col(x0, x1, y0, y1, fam, top=2):
        if west:
            x0, x1 = CELL[0] - 1 - x1, CELL[0] - 1 - x0
        return column(x0, x1, y0, y1, fam, top)

    # the back shoulder: lit basalt on the west in E, basalt_cool in shade on the east in W
    p.part(col(4, 8, 22, 30, 'basalt_cool' if west else 'basalt'))
    p.part(col(10, 13, 19, 31, 'basalt', top=3))
    p.part(col(14, 24, 20, 31, 'basalt_warm'))
    p.part(col(10, 14, 32, 35, 'basalt', top=1))           # far leg
    p.part(col(21, 25, 32, 36, 'basalt_warm', top=0))      # near leg
    p.part(col(17, 22, 25, 34, 'basalt'))                  # near arm, hanging
    if not west:
        p.part(stamp(25, 24, [
            '.. W4 W4 W4 W3 .. .. .. ..',
            'W4 W5 W5 W4 W0 W0 .. .. ..',
            'W4 W4 W3 W3 W2 V3 W2 .. ..',
            'W3 W3 W3 W3 W2 W2 W3 W3 W2',
            'W3 W2 W2 W2 W2 W1 W1 W1 W1',
            'W2 W2 W1 W1 W1 W1 W1 .. ..',
            '.. W1 W1 W1 W1 .. .. .. ..',
        ]))
        p.part(stamp(14, 17, [
            '.. .. M4 M5 M5 M3 M3 .. .. .. ..',
            '.. M4 M4 M3 M3 M2 M2 M2 S4 S4 S3',
            'S3 M1 M1 M1 M1 M1 M1 M1 S2 S2 S3',
        ]), seam=False)
        p.part(stamp(5, 33, THRIFT), seam=False)
        p.part(stamp(25, 34, THRIFT), seam=False)
    else:
        p.part(stamp(6, 24, [
            '.. .. .. .. W4 W4 W4 W3 ..',
            '.. .. .. W0 W0 W5 W5 W3 W2',
            '.. .. W3 V3 W4 W3 W3 W2 W2',
            'W4 W4 W4 W3 W3 W3 W3 W2 W1',
            'W3 W2 W2 W1 W2 W2 W2 W1 W1',
            '.. .. W2 W2 W2 W2 W1 W1 W1',
            '.. .. .. .. W1 W1 W1 W1 ..',
        ]))
        p.part(stamp(14, 17, [
            '.. .. .. .. .. M4 M5 M5 M3 M3 .. ..',
            'S4 S4 S3 S4 M4 M4 M3 M3 M2 M2 M2 ..',
            'S2 S2 S3 S3 M1 M1 M1 M1 M1 M1 M1 S2',
        ]), seam=False)
        p.part(stamp(11, 34, THRIFT), seam=False)
        p.part(stamp(31, 33, THRIFT), seam=False)
    return p.image()


VIEWS = {'S-idle': draw_S, 'E-idle': lambda: draw_EW(False), 'W-idle': lambda: draw_EW(True)}

SIMPLIFIED = [
    "Turtle: the closed eye and the shell's plate seams drop out at 1x (a single texel reads as speckle); the shell keeps its lit cap, glint and dark marginal rim, the sand head and flipper.",
    'Thrift: the 3 x 3 berry heads become 2 x 2 clusters (a lit row over a shade row) on a leaf cushion; the middle tuft keeps two heads, not three.',
    'Hex columns: each is a lit top plane with a glint, a west facet, the body and an east facet; the joints are one tone-0 seam.',
    'Boulder head: the mouth seam is one shade row (S); each ember eye is one lava texel, under a two-texel brow ledge in profile.',
]
NOTES = [
    'Drawn at 1x from parts (hex columns back to front, each leaving a seam on what it covers) plus hand-placed stamps for the head, turtle and thrift; W is laid out on its own and lit from the upper left, never mirrored pixels.',
    'Compared at 8x against the 2x final at 4x, and at game scale (1x at 2 px a texel beside 2x at 1 px): the same stepped skyline, turtle on the middle column, boulder head low in front, thrift at the base and on the west shoulder.',
]


# --- the agreement check ----------------------------------------------------------------
def alpha_set(img: Image.Image) -> set:
    a = img.getchannel('A').load()
    return {(x, y) for y in range(img.height) for x in range(img.width) if a[x, y] == 255}


def down_alpha(img2: Image.Image) -> set:
    """The 2x alpha at 1x: a texel is solid when at least 2 of its 4 pixels are; the
    foot anchors line up (FOOT2 = 2 * FOOT), any remainder is shifted out."""
    a = img2.getchannel('A').load()
    ox, oy = FOOT2[0] - 2 * FOOT[0], FOOT2[1] - 2 * FOOT[1]
    out = set()
    for y in range(CELL[1]):
        for x in range(CELL[0]):
            n = 0
            for dy in (0, 1):
                for dx in (0, 1):
                    X, Y = 2 * x + dx + ox, 2 * y + dy + oy
                    if 0 <= X < img2.width and 0 <= Y < img2.height and a[X, Y] == 255:
                        n += 1
            if n >= 2:
                out.add((x, y))
    return out


def families(img: Image.Image) -> list:
    px = img.load()
    fams = set()
    for y in range(img.height):
        for x in range(img.width):
            p = px[x, y]
            if p[3] == 255:
                m = sl.house_match(p)
                if m:
                    f = hp.family(m[0])
                    if f not in GLOWS:
                        fams.add(f)
    return sorted(fams)


def check(view: str, img1: Image.Image, img2: Image.Image) -> dict:
    a1, a2 = alpha_set(img1), down_alpha(img2)
    iou = len(a1 & a2) / max(1, len(a1 | a2))
    m = sk.measure(img1)
    return {'iou': round(iou, 4), 'families_1x': families(img1), 'families_2x': families(img2),
            'families_match': families(img1) == families(img2),
            'measure': {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}}


# --- the sheet ----------------------------------------------------------------------------
def sheet(pairs: list, results: dict, path: str):
    pad, gap = 16, 10
    f_title, f_body = sk._font(18), sk._font(12)
    tile_w = CELL[0] * 8
    W = pad + len(pairs) * (2 * tile_w + gap + pad)
    H = 44 + CELL[1] * 8 + 60 + CELL2[1] + 40
    img = Image.new('RGB', (W, H), sk.PAPER)
    d = ImageDraw.Draw(img)
    d.text((pad, 12), f'{ID}: 1x master (8x) beside the 2x final (4x); game scale below',
           fill=sk.TEXT, font=f_title)
    x = pad
    y0 = 44
    for view, i1, i2 in pairs:
        for im, k, dx in ((i1, 8, 0), (i2, 4, tile_w + gap)):
            big = im.resize((im.width * k, im.height * k), Image.NEAREST)
            tile = Image.new('RGB', big.size, sk.GRASS)
            tile.paste(big, (0, 0), big)
            img.paste(tile, (x + dx, y0))
        r = results[view]
        d.text((x, y0 + CELL[1] * 8 + 4),
               f"{view}  IoU {r['iou']:.3f}  families {'match' if r['families_match'] else 'DIFFER'}"
               f"  lone {100 * r['measure']['isolated']:.1f}%  W-E {r['measure']['west_east']:+.1f}",
               fill=sk.TEXT, font=f_body)
        gy = y0 + CELL[1] * 8 + 28
        for im, k, dx in ((i1, 2, 0), (i2, 1, CELL[0] * 2 + gap)):
            g = im.resize((im.width * k, im.height * k), Image.NEAREST)
            tile = Image.new('RGB', g.size, sk.GRASS)
            tile.paste(g, (0, 0), g)
            img.paste(tile, (x + dx, gy))
        d.text((x, gy + CELL2[1] + 4), '1x at 2 px a texel | 2x at 1 px', fill=sk.TEXT, font=f_body)
        x += 2 * tile_w + gap + pad
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def main():
    os.makedirs(VIEWS_DIR, exist_ok=True)
    results, pairs = {}, []
    for view in VIEWS:
        img1 = VIEWS[view]()
        img1.save(os.path.join(VIEWS_DIR, f'master-{view}.png'))
        img2 = Image.open(os.path.join(VIEWS_DIR, f'final-{view}.png')).convert('RGBA')
        results[view] = check(view, img1, img2)
        pairs.append((view, img1, img2))
    sheet(pairs, results, os.path.join(OUT_DIR, f'{ID}-1x.png'))
    out = {'id': ID, 'cell': list(CELL), 'foot': list(FOOT), 'views': results,
           'simplified': SIMPLIFIED, 'notes': NOTES}
    with open(os.path.join(OUT_DIR, f'{ID}.json'), 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    for v, r in results.items():
        print(f"{ID} {v}: IoU {r['iou']:.3f}  families {r['families_match']} "
              f"{r['families_1x']} vs {r['families_2x']}  lone {100 * r['measure']['isolated']:.1f}%"
              f"  W-E {r['measure']['west_east']:+.1f}  outline dark {r['measure'].get('outline_dark')}")


if __name__ == '__main__':
    main()

"""Nix's 1x master (Claude J, 21 Oct evening): the chosen 2x design (antenna hood,
glyph visor, slim delivery box at the back of the right hip) drawn again at density 1,
the same courier at half the resolution (pixel art, never a downscale).

Matt, 21 Oct 18:17: all new art is drawn at density 2, the 1x design is the master and
every density draws the same design. This file holds the 1x drawing of S, E and W idle
(W drawn and lit on its own) as hand-placed texels on the house palette, then checks it
against the 2x final views (docs/vision/characters/designs/nix-final.png):

  - the 2x alpha downscaled by 2 (a texel is solid when 2 of its 4 pixels are), aligned
    at the foot anchor, against the 1x alpha: silhouette IoU, at least 0.80;
  - the house families used, glows aside, the same at both densities.

Cell folk 32 x 36, foot (16, 33); the 2x final cell is 64 x 72, foot (32, 66).

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/masters/nix.py
(the 2x final views are read from $CHAR_VIEWS/nix/final-<view>.png).
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

ID = 'nix'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_DIR = os.path.join(ROOT, 'docs/vision/characters/masters')
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
CELL = (32, 36)
FOOT = (16, 33)
CELL2 = (64, 72)
FOOT2 = (32, 66)
GLOWS = {'lamp', 'neon_pink', 'neon_cyan', 'lava', 'glowflora'}

# Stamp tokens: a family letter, then a tone 0-5 or 'e' (that family's edge tone).
# '..' is empty. Glow families are light sources and never outlined.
LEGEND = {
    'A': 'asphalt', 'D': 'concrete', 'H': 'slate', 'N': 'snow', 'I': 'iron', 'J': 'iron_warm',
    'P': 'neon_pink', 'Q': 'neon_cyan', 'K': 'ink',
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


def rows(*spec) -> dict:
    """Hand-placed texels: each item is (y, x, 'tokens'), the tokens running east from x."""
    out = {}
    for y, x, toks in spec:
        for i, tok in enumerate(toks.split()):
            if tok == '..':
                continue
            fam, t = LEGEND[tok[0]], tok[1]
            out[(x + i, y)] = (fam, t if t == 'e' else int(t))
    return out


def draw_S() -> Image.Image:
    p = Pic()
    p.part(rows(
        # hood: two antenna bumps, crown lit upper left
        (9, 12, 'A3 .. .. .. .. .. .. A2'),
        (10, 12, 'A4 A4 A4 A4 A3 A3 A3 A2'),
        (11, 11, 'A4 A4 A5 A5 A3 A3 A3 A3 A2 A2'),
        (12, 11, 'A3 A4 A4 A3 A3 A3 A3 A2 A2 A1'),
        # visor: iron bezel, deep glass, the cyan crescent glyph (idle)
        (13, 11, 'A3 I2 I2 I2 I2 I2 I2 I2 I1 A1'),
        (14, 11, 'A3 I1 A1 A1 A1 A1 Q3 A1 I1 A1'),
        (15, 11, 'A3 I1 A1 A1 A1 Q3 A1 A1 I1 A1'),
        (16, 11, 'A3 I1 A1 A1 A1 A1 Q3 A1 I1 A1'),
        (17, 11, 'A3 I1 I1 I1 I1 I1 I1 I1 I1 A1'),
        (18, 12, 'A2 A2 A2 A2 A2 A2 A1 A1'),
        # jacket: concrete yoke, snow strip with the sling strap, rib, cuffs
        (19, 11, 'A3 D4 D4 D3 D3 D3 D3 D2 D2 A1'),
        (20, 10, 'A3 A3 D3 D3 D3 D3 D3 D2 D2 D2 A1 A1'),
        (21, 5, 'D4 D4 D4 D3 D3 De N5 N5 N5 N5 N5 D2 N4 N4 N3 N3 A1'),
        (22, 5, 'D2 D2 D2 D1 D1 De A3 A2 A2 A2 A2 A2 A2 A1 A1 A2 A1'),
        (23, 5, 'D3 P3 D3 D3 D2 De A3 A2 A2 A2 A2 A2 A1 A1 A1 A2 A1'),
        (24, 5, 'D3 D2 D2 P3 D2 De D3 D3 D3 D3 D2 D2 D2 D1 D1 D2 D2'),
        (25, 5, 'D3 D2 D2 P3 D2 De I3 .. H4 H3 .. H3 H2 .. .. I2 I2'),
        (26, 5, 'D3 D3 D3 P3 D2 .. .. .. H4 H3 .. H3 H2'),
        (27, 5, 'D1 D1 D1 D1 D1 .. .. .. D3 D3 .. D2 D2'),
        # legs: slate, concrete knee pads above; iron boots
        (28, 13, 'H4 H3 .. H3 H2'),
        (29, 13, 'H4 H3 .. H3 H2'),
        (30, 13, 'I3 I3 .. I2 I2'),
        (31, 12, 'I3 I3 I3 .. I2 I2 I2'),
        (32, 12, 'I1 I1 I1 .. I1 I1 I1'),
    ))
    return p.image()


def draw_E() -> Image.Image:
    p = Pic()
    p.part(rows(
        # hood seen from the side: round, one bump, visor proud at the front (east)
        (9, 14, 'A3'),
        (10, 13, 'A4 A4 A4 A3 A3'),
        (11, 12, 'A4 A5 A5 A4 A4 A3 A3 A2'),
        (12, 11, 'A4 A4 A4 A4 A3 A3 A3 I2 I2'),
        (13, 11, 'A4 A4 A4 A3 A3 A3 I1 A1 Q3 I1'),
        (14, 11, 'A3 A4 A3 A3 A3 A3 I1 A1 Q3 I1'),
        (15, 11, 'A3 A3 A3 A3 A3 A2 I1 A1 Q3 I1'),
        (16, 12, 'A3 A3 A3 A2 A2 I1 I1 I1'),
        (17, 13, 'A2 A2 A2 A2 A2 A1'),
        (18, 14, 'A1 A1 A1 A1'),
        # jacket; the box behind the hip (west), its pink light strip
        (19, 13, 'A2 D3 D3 D2 D2 A1'),
        (20, 12, 'De A2 A2 A2 A1 A1 A1'),
        (21, 9, 'D4 D4 D3 De A3 N5 N5 N4 N4 A1'),
        (22, 9, 'D2 D1 D1 De A2 A2 A1 A1 A1 A1'),
        (23, 9, 'D3 P3 D2 De A2 A2 A1 A1 A1 A1'),
        (24, 9, 'D3 P3 D2 De D3 D3 D3 D2 D2 D1'),
        (25, 9, 'D3 P3 D2 De .. H4 H3 I2 I2'),
        (26, 9, 'D1 D1 D1 De .. H4 H3 H2 H2'),
        (27, 14, 'D3 D3 D2 D2'),
        (28, 14, 'H4 H3 H2 H2'),
        (29, 14, 'H4 H3 H2 H2'),
        # iron boot, toe forward
        (30, 14, 'I3 I3 I2 I2'),
        (31, 13, 'I3 I3 I3 I2 I2 I2 I2'),
        (32, 14, 'I1 I1 I1 I1 I1 I1'),
    ))
    return p.image()


def draw_W() -> Image.Image:
    p = Pic()
    p.part(rows(
        # the visor faces west, into the light; the hood's back falls into shade
        (9, 17, 'A3'),
        (10, 14, 'A4 A4 A3 A3 A2'),
        (11, 12, 'A4 A4 A5 A5 A3 A3 A3 A2'),
        (12, 12, 'I2 I2 A4 A4 A3 A3 A3 A2 A2'),
        (13, 11, 'Q3 A1 I2 A4 A4 A3 A3 A3 A2 A1'),
        (14, 10, 'I2 Q3 A1 I2 A4 A3 A3 A3 A2 A2 A1'),
        (15, 11, 'Q3 A1 I2 A3 A3 A3 A3 A2 A2 A1'),
        (16, 12, 'I1 I1 A3 A3 A3 A2 A2 A1'),
        (17, 13, 'A3 A2 A2 A2 A2 A1'),
        (18, 14, 'A1 A1 A1 A1'),
        # jacket; the box behind the hip (east) in the same anchor
        (19, 13, 'A2 D3 D3 D2 D2 A1'),
        (20, 13, 'A2 A2 A2 A1 A1 A1 D4 D4 D3 D3'),
        (21, 13, 'N5 N5 N5 N4 N4 A1 D2 D2 D1 D1'),
        (22, 13, 'A2 A2 A1 A1 A1 A1 D3 P3 D2 D2'),
        (23, 13, 'A2 A2 A1 A1 A1 A1 D3 D3 P3 D2'),
        (24, 13, 'D3 D3 D3 D2 D2 D1 D3 D2 P3 D2'),
        (25, 14, 'I2 I2 H2 H2 D0 D3 D2 P3 D2'),
        (26, 14, 'H3 H3 H2 H2 D0 D3 D3 D3 D2'),
        (27, 14, 'D3 D3 D2 D2 D0 D1 D1 D1 D1'),
        (28, 14, 'H4 H3 H2 H2'),
        (29, 14, 'H4 H3 H2 H2'),
        (30, 14, 'I3 I3 I3 I2'),
        (31, 13, 'I3 I3 I3 I2 I2'),
        (32, 13, 'I1 I1 I1 I1 I1'),
    ))
    return p.image()


VIEWS = {'S-idle': draw_S, 'E-idle': draw_E, 'W-idle': draw_W}

SIMPLIFIED = [
    'Visor crack dropped: a one-texel crack is speckle at 1x.',
    'Glyph: the idle crescent is three cyan texels (S); in profile it is a lit glyph column on the visor glass (E, W).',
    'Reflective strips are one lit snow row; the shaded lower edge does not survive. The sling strap is one concrete texel where it crosses the strip (S).',
    'Delivery box: lid seam, pink logo and light strip kept (S, W); in E the box is three texels wide and keeps the light strip only; the stencil is dropped.',
    'Jacket fold bands, rib cuffs and the wrist screen are dropped; the knee pads are one concrete row and the rib waistband one concrete row.',
]
NOTES = [
    'Drawn texel by texel; W is drawn and lit on its own (visor into the light, hood back in shade), never mirrored pixels.',
    'Compared at 8x against the 2x final at 4x, and at game scale: the same round bumped hood over a slim body, glyph visor at the front, box at the back of the right hip, long slate legs and iron boots.',
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

"""Bunk's 1x master (Claude J, 21 Oct evening): the chosen 2x design (one white
barrel, curved visor band, Sleep Cycle dial hatch, bedroll shelf behind the shoulders)
drawn again at density 1, the same night-light robot at half the resolution (pixel art,
never a downscale).

Matt, 21 Oct 18:17: all new art is drawn at density 2, the 1x design is the master and
every density draws the same design. This file holds the 1x drawing of S, E and W idle
(W drawn and lit on its own) as hand-placed texels on the house palette, then checks it
against the 2x final views (docs/vision/characters/designs/bunk-final.png):

  - the 2x alpha downscaled by 2 (a texel is solid when 2 of its 4 pixels are), aligned
    at the foot anchor, against the 1x alpha: silhouette IoU, at least 0.80;
  - the house families used, glows aside, the same at both densities.

Cell folk 32 x 36, foot (16, 33); the 2x final cell is 64 x 72, foot (32, 66).

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/masters/bunk.py
(the 2x final views are read from $CHAR_VIEWS/bunk/final-<view>.png).
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

ID = 'bunk'
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
    'P': 'path', 'Q': 'path_cool', 'T': 'plaster', 'N': 'panel', 'U': 'hull', 'W': 'hull_warm',
    'C': 'hull_cool', 'V': 'void', 'L': 'lamp', 'Y': 'neon_cyan', 'K': 'ink',
}

# --- drawing ---------------------------------------------------------------------------
class Pic:
    """A 1x view painted back to front. Every part leaves a tone-0 seam on the parts it
    covers (the joint between two columns); the outside gets the edge-tone outline with
    the lit break from sheetkit at the end. Small hand-placed details (the turtle, the
    boulder head, thrift) are token stamps: a family letter and a tone 0-5 or 'e'."""

    def __init__(self):
        self.fig = sk.Fig(*CELL)

    def part(self, px: dict, seam=True):
        """seam=True leaves a tone-0 joint on the parts behind; seam='edge' outlines the
        front part over them in its own edge tone (the barrel against the bedroll)."""
        if seam:
            for (x, y) in sorted(px):
                for dx, dy in sk.N4:
                    q = (x + dx, y + dy)
                    if q not in px and q in self.fig.px and q not in self.fig.fixed:
                        fam = self.fig.px[q][0]
                        if fam in GLOWS or fam == 'ink':
                            continue
                        if seam == 'edge':
                            self.fig.px[q] = ('_edge', px[(x, y)][0])
                            self.fig.fixed.add(q)
                        else:
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
    # the bedroll crossbar behind the shoulders: path quilt, panel straps, the cool east end
    p.part(rows(
        (10, 9, 'P4 N3 P4 P4 P4 P4 P4 P4 P4 P4 P4 P4 N3 P4'),
        (11, 8, 'P3 P3 N3 P3 P3 P3 P3 P3 P3 P3 P3 P3 P3 N3 Q3 Q3'),
        (12, 7, 'P3 P3 P2 N3 P2 P2 P2 P2 P2 P2 P2 P2 P2 P2 N3 Q2 Q2 Q1'),
        (13, 7, 'P3 P3 P2 N3 P2 P2 P2 P2 P2 P2 P2 P2 P2 P2 N3 Q2 Q2 Q1'),
        (14, 7, 'P3 P3 P2 N3 P2 P2 P2 P2 P2 P2 P2 P2 P2 P2 N3 Q2 Q2 Q1'),
        (15, 8, 'P1 P1 .. .. .. .. .. .. .. .. .. .. .. .. Q1 Q1'),
    ), seam=False)
    # one barrel: warm lit band and sheen west, hull, cool shade east; visor band with
    # two lamp eyes; the dial hatch (lamp half lit, dream half dark); arms; magnetic boots
    p.part(rows(
        (12, 12, 'W4 W4 U3 U3 U3 C3 C3 C2'),
        (13, 11, 'W5 W4 W4 U3 U3 U3 C3 C3 C2 C2'),
        (14, 10, 'W4 W5 W4 W4 U3 U3 U3 C3 C3 C2 C2 C1'),
        (15, 10, 'W4 W5 W4 W4 U3 U3 U3 C3 C3 C2 C2 C1'),
        (16, 10, 'W2 W2 W2 W2 U1 U1 U1 C1 C1 C1 C1 C1'),
        (17, 10, 'W4 V1 V1 V1 V1 V1 V1 V1 V1 V1 V1 C1'),
        (18, 10, 'W4 V1 V1 L3 L3 V1 V1 L3 L3 V1 V1 C1'),
        (19, 10, 'W4 V1 V1 V1 V1 V1 V1 V1 V1 V0 V0 C1'),
        (20, 8, 'N3 N2 W4 W5 W4 W4 U3 U3 U3 C3 C3 C2 C2 C1 N2 N1'),
        (21, 7, 'N3 N3 N2 W4 W5 W4 N3 N3 N3 N2 N2 N2 C2 C2 C1 N2 N1 N1'),
        (22, 7, 'W4 W3 .. W4 W5 W4 N3 L4 L4 V1 V1 N2 C2 C2 C1 .. C2 C1'),
        (23, 7, 'W4 W3 .. W4 W5 W4 N3 L3 L3 V1 V1 N2 C2 C2 C1 .. C2 C1'),
        (24, 7, 'W4 W3 .. W4 W5 W4 N2 N2 N2 N1 N1 N1 C2 C2 C1 .. C2 C1'),
        (25, 7, 'N3 N3 .. W4 W5 W4 W4 U3 U3 U3 C3 C3 C2 C2 C1 .. N1 N1'),
        (26, 8, 'N3 .. W4 W5 W4 W4 U3 U3 U3 C3 C3 C2 C2 C1 .. N1'),
        (27, 10, 'N3 N3 N3 N3 N2 N2 N2 N2 N2 N1 N1 N1'),
        (28, 11, 'U2 U2 U2 U1 U1 U1 C1 C1 C1 C1'),
        (29, 12, 'N3 N3 .. .. .. .. N2 N2'),
        (30, 10, 'N4 N4 N3 N3 N2 .. .. N4 N4 N3 N3 N2'),
        (31, 9, 'N3 N3 Y3 N3 N3 N2 .. .. N3 N3 Y3 N3 N3 N2'),
        (32, 10, 'V1 V1 V1 V1 V1 .. .. V1 V1 V1 V1 V1'),
    ), seam='edge')
    return p.image()


def draw_E() -> Image.Image:
    p = Pic()
    # the bedroll end on behind the dome: quilt spiral round its plaster lining, a strap
    p.part(rows(
        (11, 9, 'P4 P3 N3'),
        (12, 8, 'P4 T3 P3 N3'),
        (13, 8, 'P3 T3 P2 N2'),
        (14, 8, 'P3 P2 P2 N2'),
        (15, 9, 'P2 P1 N1'),
    ), seam=False)
    p.part(rows(
        (12, 13, 'W4 W4 U3 U3 C3'),
        (13, 12, 'W5 W4 U3 U3 U3 C3 C2 C2'),
        (14, 11, 'W4 W5 W4 U3 U3 U3 C3 C2 C2 C1'),
        (15, 11, 'W4 W5 W4 U3 U3 U3 C3 C2 C2 C1'),
        (16, 11, 'W2 W2 W2 U1 U1 U1 C1 C1 C1 C1'),
        # the visor band: its back end in shade (the cheek), the glass a pixel proud
        (17, 11, 'W4 W5 W4 C2 V1 V1 V1 V1 V1 V1 V1'),
        (18, 11, 'W4 W5 W4 C2 V1 V1 V1 L3 L3 V1 V1'),
        (19, 11, 'W4 W5 W4 C2 V1 V1 V1 V0 V0 V0 V0'),
        # the lit sill (chin step), the near arm, the hatch bezel edge on at the front
        (20, 11, 'W4 W5 W4 N4 N3 N2 U4 U4 U4 U4'),
        (21, 11, 'W4 W5 W4 N3 N3 N2 C3 C2 C2 N3'),
        (22, 11, 'W4 W5 W2 W4 W3 U3 C3 C2 C2 N3'),
        (23, 11, 'W4 W5 W2 W4 W3 U3 C3 C2 C2 L3'),
        (24, 11, 'W4 W5 W2 W4 W3 U3 C3 C2 C2 N2'),
        (25, 11, 'W4 W5 W2 W4 W3 U3 C3 C2 C2 C1'),
        (26, 11, 'W4 W5 W2 N3 N2 U3 C3 C2 C2 C1'),
        (27, 11, 'N3 N3 N3 N3 N2 N2 N2 N1 N1 N1'),
        (28, 12, 'U2 U2 U1 U1 U1 C1 C1 C1'),
        (29, 14, 'N2 N2 N4 N3'),
        (30, 13, 'N3 N3 N4 N4 N3 N3 N2'),
        (31, 13, 'N3 N3 N3 Y3 N3 N3 N3 N2'),
        (32, 13, 'V1 V1 V1 V1 V1 V1 V1'),
    ), seam='edge')
    return p.image()


def draw_W() -> Image.Image:
    p = Pic()
    # the bedroll end on behind the dome, now on the shaded east
    p.part(rows(
        (11, 20, 'N3 P3 P2'),
        (12, 20, 'N3 P3 T2 P2'),
        (13, 20, 'N2 P2 T2 P1'),
        (14, 20, 'N2 P2 P1 P1'),
        (15, 20, 'N1 P1 P1'),
    ), seam=False)
    p.part(rows(
        (12, 14, 'W4 U3 U3 C3 C3'),
        (13, 12, 'W5 W4 U3 U3 U3 C3 C2 C2'),
        (14, 11, 'W4 W5 W4 W4 U3 U3 U3 C3 C2 C1'),
        (15, 11, 'W4 W5 W4 W4 U3 U3 U3 C3 C2 C1'),
        (16, 11, 'W2 W2 W2 W2 U1 U1 U1 C1 C1 C1'),
        # the visor band faces west into the light, the glass a pixel proud
        (17, 10, 'V1 V1 V1 V1 V1 V1 V1 C2 C3 C2 C1'),
        (18, 10, 'V1 V1 L3 L3 V1 V1 V1 C2 C3 C2 C1'),
        (19, 10, 'V1 V1 V1 V1 V0 V0 V0 C2 C3 C2 C1'),
        (20, 11, 'U4 U4 U4 U4 N4 N3 N2 C3 C2 C1'),
        (21, 11, 'N3 W4 W4 U3 N3 N3 N2 C2 C2 C1'),
        (22, 11, 'N3 W5 W4 U3 U3 W4 W3 C1 C2 C1'),
        (23, 11, 'L3 W5 W4 U3 U3 W4 W3 C1 C2 C1'),
        (24, 11, 'N2 W5 W4 U3 U3 W4 W3 C1 C2 C1'),
        (25, 11, 'W4 W5 W4 U3 U3 W4 W3 C1 C2 C1'),
        (26, 11, 'W4 W5 W4 U3 U3 N3 N2 C1 C2 C1'),
        (27, 11, 'N3 N3 N3 N3 N2 N2 N2 N1 N1 N1'),
        (28, 12, 'U2 U2 U1 U1 U1 C1 C1 C1'),
        (29, 14, 'N4 N3 N2 N2'),
        (30, 12, 'N2 N3 N4 N4 N3 N3 N2'),
        (31, 12, 'N3 N3 Y3 N3 N3 N3 N2'),
        (32, 12, 'V1 V1 V1 V1 V1 V1 V1'),
    ), seam='edge')
    return p.image()


VIEWS = {'S-idle': draw_S, 'E-idle': draw_E, 'W-idle': draw_W}

SIMPLIFIED = [
    'Dial: the needle is dropped; the hatch keeps the lit lamp half and the dark dream half inside a panel bezel (S), and a lamp glimpse on the edge-on bezel (E, W).',
    'Bedroll: quilt stitching and buckles are dropped; the straps stay as panel columns (S) and the end-on spiral is two plaster texels round the path quilt (E, W).',
    'Visor band: straight across in S at 1x; its curve round the front shows in profile as the shaded cheek and the glass one texel proud.',
    'Boot lock lights are one neon_cyan texel each; the mittens are one panel row.',
]
NOTES = [
    'Drawn texel by texel; the barrel outlines itself in the hull edge over the bedroll; W is drawn and lit on its own, never mirrored pixels.',
    'Compared at 8x against the 2x final at 4x, and at game scale: the same white barrel with warm lit band and cool east, dark visor band with two lamp eyes, the bedroll bar behind the shoulders, dial hatch and magnetic boots.',
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

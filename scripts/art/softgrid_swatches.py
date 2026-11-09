"""Soft grid terrain swatches, for Matt's approval before any zone changes (26 Oct).

Matt, 26 Oct 17:46: "make sure to really refine the soft grid before you implement it everywhere.
which parts stay as before and which parts needs to adhere to the softgrid (remember that wells for
example should still be round ...). most props should probably stay as before (detailled of course)
but the ground and the placement of the props changes. consider what natural terrain looks like
under these constraints". 17:48: "eastward is really the example the soft grid should follow".

The plans come from scripts/art/native/softgrid.py (whole cells, rounded corners, lumpy outlines);
the ground in them is painted by scripts/art/native/softground.py at Eastward's level of detail
(textured fills, frayed and broken edges, lips, faces, feet and cast shadows, ambient occlusion);
the props, trees and plants are the kit's own (village.py, props.py, the woodland's tree recipes),
their feet on cells, so the sheet shows what the soft grid governs and what stays organic
(docs/vision/eastward-edges.md, "What the soft grid governs").

    python3 -m scripts.art.softgrid_swatches OUT_DIR [--only I ...]

writes OUT_DIR/softgrid_swatches_1080p.png (nine swatches, 160 x 120 world px each at density 3,
1:1, and three of them again under the 24 px cell grid) and OUT_DIR/swatch_<i>_<name>.png, each a
ground picture that `npm run review:asset -- <png> --kind ground --biome woodland` and `npm run
review:scene -- <png> --scale 1 --H 74` pass. The side-by-side with Eastward (our crops at 3x, its
crops at the same character height: our adult 74 art px, its 54 native px) is made locally from
the references, which are never committed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from scripts.art.native import ctx, load_biome  # noqa: E402

BIOME = load_biome('woodland')
ctx.configure(3.0, BIOME, json.load(open(os.path.join(ROOT, 'art', 'scenes', 'woodland.json'))))

from scipy import ndimage as ndi  # noqa: E402

from scripts.art.native import softgrid as SG  # noqa: E402
from scripts.art.native import softground as GD  # noqa: E402
from scripts.art.native import props as P4  # noqa: E402
from scripts.art.native import village as V  # noqa: E402
from scripts.art.native.palette import to_rgba  # noqa: E402

D = ctx.D
CELL = SG.cell_px()                  # 24 art px
TW, TH = 20 * CELL, 15 * CELL        # a swatch: 160 x 120 world px


def cells(rects):
    return SG.cells_rects(rects, TH, TW)


def g(x, y):
    """A cell's foot point (on the cell's lower edge, centred) in texels."""
    return int((x * 8 + 4) * D), int((y * 8 + 8) * D)


class Swatch:
    """A ground canvas in codes plus the sprites that stand on it (feet on cells)."""

    def __init__(self, cv, caption):
        self.cv = cv
        self.cap = caption
        self.sprites = []          # (image, anchor, (foot x, foot y), base width for its shadow or 0)
        self.structures = []       # structures carrying props, for logic.composition (scene gate)
        self.plan = {}             # tiers and stairs, for logic.tiers (scene gate)
        self.canopy = None         # where a canopy's shade already lies (no second shadow on it)

    def add(self, img, anc, foot, shade_w=0.0, depth=0.3):
        self.sprites.append((img.convert('RGBA'), anc, foot))
        if shade_w:
            GD.contact(self.cv, foot[0], foot[1], shade_w, depth=depth)

    def prop(self, kind, x, y, seed):
        if kind == 'well':
            pic = V.prop('well', 18, 14, seed=seed)
            self.add(pic.rgba(), (pic.ax, pic.ay), (x, y), 44, 0.45)
        elif kind == 'bench':
            pic = V.prop('bench', 24, 6, seed=seed)
            self.add(pic.rgba(), (pic.ax, pic.ay), (x, y), 66, 0.32)
        elif kind in ('bench_side_e', 'bench_side_w'):
            # side on: the shade lies under the whole seat, north to south, thrown a little east
            pic = V.prop(kind, 6, 18, seed=seed)
            yy, xx = np.mgrid[0:self.cv.shape[0], 0:self.cv.shape[1]]
            m = (xx >= x - 2.2 * D) & (xx < x + 4.6 * D) & (yy >= y - 17.5 * D) & (yy < y + 1.2 * D)
            GD.shadow(self.cv, m, core=2, rim=2)
            self.add(pic.rgba(), (pic.ax, pic.ay), (x, y))
        elif kind == 'rock':
            w = 9 + seed % 5
            img, anc, _ = P4.boulder4(D, w, 6 + seed % 3, seed=seed)
            self.add(img, anc, (x, y), w * D * 0.95, 0.5)
        elif kind == 'fern':
            img, anc, _ = P4.fern_hd(D, seed=seed, size=0.72)
            self.add(img, anc, (x, y), 24, 0.3)
        elif kind == 'stump':
            img, anc, _ = P4.stump4(D, seed=seed)
            self.add(img, anc, (x, y), 70, 0.35)
        elif kind in BIOME['recipes']:
            from scripts.art.native import screen as SN
            img, anc, a, ex = SN.sprite(kind, BIOME['recipes'][kind], seed)
            if ex is not None:                      # a tree: its crown's shadow on the ground
                fx, fy = x / D, y / D
                m = SN.tree_shadow_hd(fx, fy, ex, TW, TH)
                if self.canopy is not None:
                    m &= ~self.canopy
                GD.shadow(self.cv, m, core=1, rim=0, fade=True)
                # what falls from the crown lies in its shade: needles or leaves, twigs
                GD.litter(self.cv, m & GD.grassy(self.cv), np.random.default_rng(seed), 0.3, shade=False)
                GD.contact(self.cv, x, y, ex['tw'] * D * 1.6, depth=0.35)
                yy_, xx_ = np.mgrid[0:TH, 0:TW]
                near = ((xx_ - x) / (ex['tw'] * D * 1.4)) ** 2 + ((yy_ - y) / 12.0) ** 2 <= 1
                GD.litter(self.cv, near & GD.grassy(self.cv), np.random.default_rng(seed + 1), 0.8, shade=False)
                img, anc = GD.seat_tree(img.convert('RGBA'), anc, np.random.default_rng(seed), crown=kind != 'pine')
                self.sprites.append((img.convert('RGBA'), anc, (x, y)))
            else:
                bw = (np.asarray(img)[..., 3] > 0).any(0).sum()
                self.add(img, anc, (x, y), bw * 0.9, 0.3)
        else:
            raise KeyError(kind)


def rect_mask(x0, y0, x1, y1):
    m = np.zeros((TH, TW), bool)
    m[max(0, y0):y1, max(0, x0):x1] = True
    return m


# ------------------------------------------------------------------------------------------------
# the swatches
# ------------------------------------------------------------------------------------------------
def sw_plateau():
    """One plateau, one level (16 world px over the lawn): its rim runs straight with a spur of
    whole cells to the south; the spur's sides show as narrow walls; log steps are cut into the
    straight face, their head flush with the rim and their foot on the path (logic.tiers)."""
    rng = np.random.default_rng(3)
    cv = GD.lawn(TH, TW, 11)
    rects = [[0, 0, 160, 40], [104, 40, 40, 16]]
    tm = SG.shape(cells(rects), TH, TW, 301, r_out=0.65, r_in=0.4)
    top = GD.lawn(TH, TW, 31, base=3, lush=0.5, grain=0.6)
    cv[tm] = top[tm]
    x0, x1 = int(40 * D), int(64 * D)
    y_rim = int(40 * D)
    face_h = int(16 * D)
    path = SG.route_shape([[52, 120], [52, 60]], 3, TH, TW, seed=5)
    path[:y_rim + face_h] = False
    path |= rect_mask(x0, y_rim + face_h - 2, x1, y_rim + face_h + 6) & ndi.binary_dilation(path, iterations=8)
    GD.dirt(cv, path, 21, ruts=None, cell=13)
    face, items, lip = GD.ledge(cv, tm, face_h, rng, seed=301, kind='earth', shadow_px=15)
    cv_turf = GD.grassy(cv) & ~path
    GD.sunken_edge(cv, path, cv_turf & ~face, rng, stones=0.6)
    GD.log_steps(cv, x0, x1, y_rim - 1, y_rim + face_h + 2, 4, rng)
    s = Swatch(cv, 'plateau: one level, a spur with side walls, log steps flush with the rim')
    for img, anc, foot in items:
        if not (x0 - 20 < foot[0] < x1 + 20):
            s.add(img, anc, foot, (np.asarray(img)[..., 3] > 0).any(0).sum() * 0.9, 0.45)
    s.prop('bush', int(14 * D), y_rim + 2, 3)
    s.prop('holly', int(150 * D), int(100 * D), 5)
    s.prop('fern', int(94 * D), int(61 * D), 4)
    s.prop('rock', int(80 * D), int(30 * D), 33)
    s.prop('bench', *g(3, 3), 41)
    s.prop('well', *g(10, 14), 3)
    s.prop('rock', *g(1, 13), 31)
    s.prop('fern', int(24 * D), int(62 * D), 9)
    s.plan = dict(density=3, cell=8, tiers=[dict(id='plateau', level=16, below=0, face_px=face_h, rects=rects)],
                  stairs=[dict(tier='plateau', x0=x0, x1=x1, y_top=y_rim - 1, y_foot=y_rim + face_h + 2)])
    return s


def sw_paths():
    rng = np.random.default_rng(9)
    cv = GD.lawn(TH, TW, 12)
    plan = SG.cells_route([[0, 60], [100, 60], [100, 120]], 3, TH, TW)                # a run and a bend
    plan |= SG.cells_route([[100, 60], [100, 0]], 2, TH, TW)                           # a T: the side path two cells
    m = SG.shape(plan, TH, TW, 7, r_out=SG.R_TURN_OUT, r_in=SG.R_TURN_IN)
    turf = GD.grassy(cv) & ~m
    GD.dirt(cv, m, 22, ruts=17)
    GD.sunken_edge(cv, m, turf, rng)
    s = Swatch(cv, 'path: straight run, bend, T-junction, constant widths (3 and 2 cells)')
    s.prop('bench', *g(4, 5), 41)
    s.prop('rock', *g(15, 12), 35)
    s.prop('well', *g(16, 4), 4)
    s.prop('holly', *g(2, 13), 6)
    s.prop('fern', *g(9, 13), 5)
    return s


def sw_pond():
    cv = GD.lawn(TH, TW, 13)
    pond = SG.shape(cells([[32, 32, 88, 48], [48, 24, 56, 72], [112, 48, 16, 24]]), TH, TW, 401, r_out=1.0, r_in=0.6)
    items = GD.water(cv, pond, 401, bank_h=11, lilies=0.35, stones=0.6)
    s = Swatch(cv, 'pond: a rounded union of cells, earth bank, stones, lilies')
    for it in items:
        s.add(*it)
    s.prop('rock', *g(4, 5), 36)
    s.prop('fern', int(38 * D), int(28 * D), 7)
    s.prop('bush', int(136 * D), int(44 * D), 8)
    s.prop('bench', *g(3, 13), 42)
    s.prop('well', *g(17, 13), 5)
    return s


def sw_river():
    cv = GD.lawn(TH, TW, 14)
    river = SG.shape(SG.cells_route([[0, 48], [72, 48], [72, 96], [160, 96]], 3, TH, TW) |
                     SG.cells_route([[0, 48], [40, 48]], 4, TH, TW), TH, TW, 402, r_out=1.3, r_in=0.6)
    items = GD.water(cv, river, 402, bank_h=10, flow='auto', stones=0.8)
    GD.footbridge(cv, int(108 * D), int(128 * D), river, np.random.default_rng(12))
    s = Swatch(cv, 'river: cell plan, wide rounded bends, 3 to 4 cells, bridge on footings')
    for it in items:
        s.add(*it)
    s.prop('rock', *g(3, 2), 38)
    s.prop('bench', *g(14, 4), 43)
    s.prop('well', *g(3, 13), 6)
    s.prop('fern', *g(9, 13), 39)
    s.prop('bush', int(146 * D), int(44 * D), 4)
    return s


def sw_cliff():
    """One rock tier 32 world px over the lawn, an L of whole cells: an outer corner (east), an inner
    corner where the west lobe's wall meets the main face, side walls at every end (logic.tiers)."""
    rng = np.random.default_rng(4)
    cv = GD.lawn(TH, TW, 15)
    rects = [[0, 16, 104, 24], [0, 40, 56, 24]]
    tm = SG.shape(cells(rects), TH, TW, 303, r_out=0.4, r_in=0.25)
    top = GD.lawn(TH, TW, 35, lush=0.5, grain=0.6)
    cv[tm] = top[tm]
    face, items, lip = GD.ledge(cv, tm, int(32 * D), rng, seed=303, kind='rock', earth='crag', shadow_px=18)
    s = Swatch(cv, 'cliff: one tier 32 world px, outer and inner corner, side walls')
    for img, anc, foot in items:
        s.add(img, anc, foot, (np.asarray(img)[..., 3] > 0).any(0).sum() * 0.9, 0.45)
    s.prop('rock', *g(15, 13), 40)
    s.prop('fern', int(96 * D), int(76 * D), 3)
    s.prop('fern', int(150 * D), int(30 * D), 8)
    s.prop('holly', int(20 * D), int(36 * D), 7)
    s.prop('bench', *g(13, 14), 44)
    s.plan = dict(density=3, cell=8, tiers=[dict(id='cliff', level=32, below=0, face_px=int(32 * D), rects=rects)])
    return s


def sw_beds():
    rng = np.random.default_rng(6)
    cv = GD.lawn(TH, TW, 16)
    frame = SG.shape(cells([[32, 24, 96, 48]]), TH, TW, 404, r_out=0.3, r_in=0.1, amp=(0.0, 0.0))
    frame &= ~SG.shape(cells([[40, 32, 80, 32]]), TH, TW, 404, r_out=0.0, r_in=0.0, amp=(0.0, 0.0)) | frame
    # the bed sits on a worn margin of earth where the gardener kneels
    GD.bed(cv, frame, rng, (5, 4, 15, 8), CELL)
    GD.weeds_at_foot(cv, frame, rng, rate=0.06)
    s = Swatch(cv, 'garden bed: a raised frame of cells, a rounded plot per cell')
    s.structures.append(dict(id='bed', rect=[4 * CELL, 3 * CELL, 16 * CELL, 9 * CELL],
                             props=[dict(kind='plot', x=(c + 0.5) * CELL, y=5 * CELL, w=CELL - 2) for c in range(5, 15)]))
    s.prop('well', *g(1, 14), 7)
    s.prop('bench', *g(16, 14), 45)
    s.prop('rock', *g(18, 2), 41)
    s.prop('holly', int(16 * D), int(30 * D), 9)
    s.prop('fern', int(146 * D), int(70 * D), 6)
    return s


def sw_square():
    """A village square composed round its contents (Matt, 26 Oct 19:35 and 22:30): the well on
    the centre axis with a clear cell all round its roof, a pair of benches side on to its west and
    east, their seats facing it, lamps at the four corners, planters flanking the way in, the path meeting the
    square on its axis; the square 17 x 12 cells, raised a little on a kerb with a lip, a low face
    and its shadow (logic.composition checks centre, pairs, margins and the way in)."""
    rng = np.random.default_rng(5)
    cv = GD.lawn(TH, TW, 17)
    ax = 84                                                    # the centre axis, world px
    sq = [16, 8, 136, 96]                                      # x, y, w, h in world px: whole cells
    pave = SG.shape(cells([sq]), TH, TW, 405, r_out=0.25, r_in=0.1, amp=(0, 0))
    path = SG.route_shape([[ax, 104], [ax, 120]], 3, TH, TW, seed=11) & ~pave
    turf = GD.grassy(cv) & ~path & ~pave
    GD.dirt(cv, path, 23, ruts=None)
    face = GD.paving(cv, pave, rng)
    path &= ~face
    GD.sunken_edge(cv, path, turf & ~face & ~pave, rng)
    GD.weeds_at_foot(cv, pave, rng)
    s = Swatch(cv, 'village square: well centred, benches facing it, lamps and planters at the way in')
    from scripts.art.native import village as VV
    well = (int(ax * D), int(76 * D))
    # benches side on, west and east of the well, both seats facing it (Matt, 26 Oct), a clear
    # cell between each and the well's roof
    benches = [(int((ax - 28) * D), int(80 * D)), (int((ax + 28) * D), int(80 * D))]
    lamps = [(int(28 * D), int(96 * D)), (int(140 * D), int(96 * D))]      # at the south corners, by the way in
    tubs = [(int((ax - 20) * D), int(100 * D)), (int((ax + 20) * D), int(100 * D))]
    s.prop('well', *well, 8)
    for i, b in enumerate(benches):
        s.prop(('bench_side_e', 'bench_side_w')[i], *b, 46 + i)
    for i, (x, y) in enumerate(lamps):
        img, anc, _ = P4.lantern4(D, seed=60 + i)
        s.add(img, anc, (x, y), 18, 0.4)
    for i, (x, y) in enumerate(tubs):
        pic = VV.prop('flower_tub', 10, 6, seed=70 + i)
        s.add(pic.rgba(), (pic.ax, pic.ay), (x, y), 30, 0.4)
    s.prop('rock', *g(1, 14), 42)
    s.structures.append(dict(id='square', rect=[int(sq[0] * D), int(sq[1] * D), int((sq[0] + sq[2]) * D),
                                                int((sq[1] + sq[3]) * D)],
                             props=[dict(kind='well', x=well[0], y=well[1], w=54, centre=True)] +
                             [dict(kind='bench', x=b[0], y=b[1], w=18) for b in benches] +
                             [dict(kind='lamp', x=x, y=y, w=18) for x, y in lamps] +
                             [dict(kind='tub', x=x, y=y, w=30) for x, y in tubs],
                             entries=[dict(x=int(ax * D), w=int(24 * D))]))
    return s


def sw_forest():
    rng = np.random.default_rng(18)
    cv = GD.lawn(TH, TW, 18, fam='leaf', base=3, lush=0.6, flowers=0.1, grain=0.15, mottle=5.0)
    trees = [('pine', *g(3, 9), 11), ('birch', *g(10, 6), 17), ('pine', *g(17, 9), 13), ('oak', *g(13, 1), 14)]
    from scripts.art.native import screen as SN
    tws = {k: (BIOME['recipes'][k].get('trunk_w') or SN.tree_dims(BIOME['recipes'][k]['master'])['tw']) * D for k in ('oak', 'pine', 'beech', 'birch', 'willow', 'hollow_tree')}
    canopy = GD.forest_floor(cv, rng, 418, feet=[(x, y, tws[k] * 0.9) for k, x, y, _ in trees if y > 60])
    trail = SG.route_shape([[0, 96], [64, 96], [64, 120]], 2, TH, TW, seed=19)
    turf = GD.grassy(cv) & ~trail
    GD.dirt(cv, trail, 24, fam='path', cell=12, stones=0.5)
    GD.litter(cv, trail, rng, 0.6)
    GD.sunken_edge(cv, trail, turf, rng, tufts=0.7)
    s = Swatch(cv, 'forest floor: trunks on cells, roots, ferns, litter, crowns overhead')
    s.canopy = canopy
    # trunks on cells; their crowns fill the top of the picture, as under a canopy
    for kind, x, y, sd in trees:
        s.prop(kind, x, y, sd)
    for kind, x, y, sd in trees:               # over the shadows: the roots catch the light
        GD.roots(cv, x, y, rng, half=int(tws[kind] * 0.55), n=4 if kind != 'pine' else 3)
    for (x, y, sd) in ((int(46 * D), int(80 * D), 1), (int(104 * D), int(66 * D), 2), (int(90 * D), int(112 * D), 3),
                       (int(150 * D), int(108 * D), 4), (int(8 * D), int(112 * D), 5), (int(122 * D), int(86 * D), 6),
                       (int(149 * D), int(95 * D), 8)):
        s.prop('fern', x, y, sd)
    s.prop('bramble', int(30 * D), int(102 * D), 7)
    s.prop('stump', *g(16, 13), 61)
    s.prop('rock', *g(6, 11), 43)
    img, anc, _ = P4.mushrooms_hd(D, n=5, seed=4, kind='brown')
    s.add(img, anc, (int(48 * D), int(70 * D)), 18, 0.3)
    img, anc, _ = P4.mushrooms_hd(D, n=3, seed=5, kind='red')
    s.add(img, anc, (int(136 * D), int(116 * D)), 14, 0.3)
    return s


def sw_shore():
    rng = np.random.default_rng(20)
    cv = GD.lawn(TH, TW, 19)
    sandm = SG.shape(cells([[0, 56, 160, 64], [56, 40, 64, 16]]), TH, TW, 406, r_out=0.15, r_in=0.1, amp=(0.5, 1.0))
    sea = SG.shape(cells([[0, 88, 160, 32], [24, 80, 48, 8]]), TH, TW, 408, r_out=0.65, r_in=0.4)
    turf = GD.grassy(cv) & ~sandm
    GD.sand(cv, sandm, 406)
    GD.shore(cv, sandm, sea, rng, 408)
    GD.frayed_edge(cv, sandm, turf, rng)
    s = Swatch(cv, 'grass to sand to sea: frayed, low-contrast transitions, wet sand, swash')
    s.prop('rock', *g(15, 7), 45)
    s.prop('bench', *g(4, 3), 49)
    s.prop('well', *g(16, 3), 10)
    s.prop('rock', int(40 * D), int(100 * D), 46)
    s.prop('holly', int(70 * D), int(22 * D), 5)
    return s


SWATCHES = (sw_plateau, sw_paths, sw_pond, sw_river, sw_cliff, sw_beds, sw_square, sw_forest, sw_shore)
GRIDDED = (0, 1, 3)                # the plateau, the paths and the river again, with the cell grid over them


def render(fn, out=None):
    s = fn()
    if out:
        p = os.path.join(out, f'swatch_{SWATCHES.index(fn)}_{fn.__name__[3:]}.compose.json')
        if s.structures or s.plan:
            json.dump(dict(structures=s.structures, **s.plan), open(p, 'w'), indent=1)
            from scripts.review import composition as CP, tiers as TI
            for f in CP.check(s.structures) + (TI.check(s.plan) if s.plan else []):
                print('composition/tiers:', f.message)
        elif os.path.exists(p):
            os.remove(p)
    im = Image.fromarray(to_rgba(s.cv), 'RGBA')
    for img, anc, (fx, fy) in sorted(s.sprites, key=lambda t: t[2][1]):
        im.alpha_composite(img, (int(round(fx - anc[0])), int(round(fy - anc[1]))))
    return im, s.cap


def grid_overlay(im):
    o = im.copy()
    d = ImageDraw.Draw(o)
    for x in range(0, im.width, CELL):
        d.line([(x, 0), (x, im.height)], fill=(255, 0, 255, 60))
    for y in range(0, im.height, CELL):
        d.line([(0, y), (im.width, y)], fill=(255, 0, 255, 60))
    return o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--only', type=int, nargs='*')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    which = a.only if a.only else range(len(SWATCHES))
    tiles = {}
    for i in which:
        tiles[i] = render(SWATCHES[i], a.out)
        tiles[i][0].save(os.path.join(a.out, f'swatch_{i}_{SWATCHES[i].__name__[3:]}.png'))
    if a.only:
        return 0
    sheet = Image.new('RGB', (1920, 1080), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, (im, cap) in tiles.items():
        x, y = (i % 4) * TW, (i // 4) * TH
        sheet.paste(im.convert('RGB'), (x, y))
        d.rectangle([x + 2, y + 2, x + 8 + 6 * len(cap), y + 14], fill=(0, 0, 0))
        d.text((x + 5, y + 3), cap, fill=(255, 255, 255))
    for j, idx in enumerate(GRIDDED):
        gx, gy = (1 + j) * TW, 2 * TH
        sheet.paste(grid_overlay(tiles[idx][0]).convert('RGB'), (gx, gy))
        d.rectangle([gx + 2, gy + 2, gx + 230, gy + 14], fill=(0, 0, 0))
        d.text((gx + 5, gy + 3), f'{SWATCHES[idx].__name__[3:]}, with the 24 px cell grid', fill=(255, 255, 255))
    sheet.save(os.path.join(a.out, 'softgrid_swatches_1080p.png'))
    print('wrote', os.path.join(a.out, 'softgrid_swatches_1080p.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

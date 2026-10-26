"""Soft grid terrain swatches, for Matt's approval before any zone changes (26 Oct).

Matt, 26 Oct 17:46: "make sure to really refine the soft grid before you implement it everywhere.
which parts stay as before and which parts needs to adhere to the softgrid (remember that wells for
example should still be round ...). most props should probably stay as before (detailled of course)
but the ground and the placement of the props changes. consider what natural terrain looks like
under these constraints". 17:48: "eastward is really the example the soft grid should follow".

Every swatch is drawn only from scripts/art/native/softgrid.py (the ground) and the kit's own props
(a round well, a bench, rocks), placed with their feet on cells, so the sheet shows what the soft
grid governs and what stays organic (docs/vision/eastward-edges.md, "What the soft grid governs").

    python3 -m scripts.art.softgrid_swatches OUT_DIR [--eastward NATIVE_DIR]

writes OUT_DIR/softgrid_swatches_1080p.png (ten swatches, 160 x 120 world px each at density 3,
1:1) and, with the Eastward native frames (local only, never committed), OUT_DIR/
softgrid_crops_3x.png: each swatch's key detail at 3x beside the matching Eastward crop scaled to
the same character height (our adult 74 art px, Eastward's 54 native px).
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

ctx.configure(3.0, load_biome('woodland'), json.load(open(os.path.join(ROOT, 'art', 'scenes', 'woodland.json'))))

from scipy import ndimage as ndi  # noqa: E402

from scripts.art.native import softgrid as SG  # noqa: E402
from scripts.art.native import props as P4  # noqa: E402
from scripts.art.native import village as V  # noqa: E402
from scripts.art.native import water as WA  # noqa: E402
from scripts.art.native.palette import C, FI, sib, step, to_rgba  # noqa: E402

D = ctx.D
CELL = SG.cell_px()                  # 24 art px
TW, TH = 20 * CELL, 15 * CELL        # a swatch: 160 x 120 world px


# ------------------------------------------------------------------------------------------------
# ground fills (texture inside a fill is not governed: soft, low contrast, irregular)
# ------------------------------------------------------------------------------------------------
def lawn(seed: int, fam: str = 'grass', base: int = 3) -> np.ndarray:
    cv = np.full((TH, TW), C(fam, base), np.int32)
    p = SG.soft_patches(TH, TW, seed, 20.0 * D, 0.10)
    cv[p] = sib(cv[p], 'cool')
    rng = np.random.default_rng(seed)
    # Eastward's blade marks: small V marks a tone down, staggered, sparse
    sx, sy = int(2.6 * D), int(1.9 * D)
    for gy in range(0, TH - 2, sy):
        for gx in range((gy // sy) % 2 * (sx // 2), TW - 3, sx):
            if rng.random() > 0.55:
                continue
            y, x = gy + int(rng.integers(-1, 2)), gx + int(rng.integers(-2, 3))
            for dy, dx in ((0, 0), (1, 1), (0, 2)):
                if 0 <= y + dy < TH and 0 <= x + dx < TW:
                    cv[y + dy, x + dx] = step(cv[y + dy, x + dx], -1)
    return cv


def dirt_fill(cv, m, seed, fam='path'):
    famc = np.full(cv.shape, FI[fam])
    famc[SG.soft_patches(*cv.shape, seed, 10.0 * D, 0.15)] = FI[fam + '_warm']
    famc[SG.soft_patches(*cv.shape, seed + 7, 8.0 * D, 0.10)] = FI[fam + '_cool']
    cv[m] = (famc * 8 + 3)[m]
    rng = np.random.default_rng(seed)
    from scripts.art.native import softedge as SE
    SE.soil_marks(cv, m & ndi.binary_erosion(m, iterations=3), rng, spacing=1.2, p=0.55)


def turf(cv):
    return (cv // 8 == FI['grass']) | (cv // 8 == FI['grass_cool']) | (cv // 8 == FI['grass_warm']) | \
        (cv // 8 == FI['leaf']) | (cv // 8 == FI['leaf_cool'])


# ------------------------------------------------------------------------------------------------
# the swatches: (ground codes, [(sprite RGBA, foot x, foot y in texels)], caption)
# ------------------------------------------------------------------------------------------------
def cells(rects):
    return SG.cells_rects(rects, TH, TW)


def props_row(spots):
    """Organic props, feet on cells (a round well, a bench, rocks)."""
    out = []
    for kind, cx, cy, seed in spots:
        if kind == 'well':
            pic = V.prop('well', 18, 14, seed=seed)
            out.append((pic.rgba(), (pic.ax, pic.ay), (cx, cy)))
        elif kind == 'bench':
            pic = V.prop('bench', 24, 6, seed=seed)
            out.append((pic.rgba(), (pic.ax, pic.ay), (cx, cy)))
        elif kind == 'rock':
            img, anc, _ = P4.boulder4(D, 9 + seed % 5, 6 + seed % 3, seed=seed)
            out.append((img, anc, (cx, cy)))
        elif kind == 'trunk':
            img, anc, _ = P4.trunk4(D, length=40.0, trunk_w=9.0, seed=seed, flare=1.0)
            out.append((img, anc, (cx, cy)))
        elif kind == 'fern':
            img, anc, _ = P4.fern_hd(D, seed=seed, size=0.8)
            out.append((img, anc, (cx, cy)))
    return out


def g(x, y):
    """A cell's foot point (world px, on the cell's lower edge, centred) in texels."""
    return int((x * 8 + 4) * D), int((y * 8 + 8) * D)


def sw_plateau():
    cv = lawn(11)
    top = cells([[0, 0, 160, 40], [0, 40, 64, 16], [104, 40, 32, 8]])        # unions at 1, 2 and 4+ cells
    tm = SG.shape(top, TH, TW, 301, r_out=0.65, r_in=0.4)
    rng = np.random.default_rng(3)
    SG.ledge(cv, tm, 12, rng, seed=301)
    SG.breakers(cv, tm, rng, 0.12, kind='lip')
    # steps cut into the face: three cells wide, four treads
    x0, x1 = int(72 * D), int(96 * D)
    ys = np.nonzero(tm[:, (x0 + x1) // 2])[0]
    y_top = int(ys.max()) + 1
    SG.steps(cv, x0, x1, y_top - 2, y_top + int(12 * D), 4, rng)
    path = SG.route_shape([[84, 120], [84, 52]], 3, TH, TW, seed=5) & ~tm
    path[:y_top + int(12 * D)] = False
    dirt_fill(cv, path, 21)
    SG.path_rim(cv, path, turf(cv) & ~path)
    sp = props_row([('well', *g(15, 12), 3), ('bench', *g(3, 3), 41), ('rock', *g(2, 10), 31), ('rock', *g(17, 3), 33)])
    return cv, sp, 'grass plateau, earth ledge, steps cut in the face'


def sw_paths():
    cv = lawn(12)
    m = SG.route_shape([[0, 60], [100, 60], [100, 120]], 3, TH, TW, seed=7)          # a run and a bend
    m |= SG.route_shape([[100, 60], [100, 0]], 2, TH, TW, seed=8)                   # a T: the side path two cells
    dirt_fill(cv, m, 22)
    SG.path_rim(cv, m, turf(cv) & ~m)
    SG.breakers(cv, m, np.random.default_rng(9), 0.15, kind='path', turf=turf(cv))
    sp = props_row([('bench', *g(4, 5), 41), ('rock', *g(15, 12), 35), ('well', *g(16, 4), 4)])
    return cv, sp, 'path: straight run, bend, T-junction, constant widths'


def sw_pond():
    cv = lawn(13)
    pond = SG.shape(cells([[32, 32, 88, 48], [48, 24, 56, 72], [112, 48, 16, 24]]), TH, TW, 401, r_out=1.4, r_in=0.8)
    WA.paint_hd(cv, pond)
    sp = props_row([('rock', *g(4, 5), 36), ('rock', *g(15, 3), 37), ('bench', *g(3, 13), 42), ('well', *g(17, 13), 5)])
    return cv, sp, 'pond: a rounded union of cells'


def sw_river():
    cv = lawn(14)
    river = SG.shape(SG.cells_route([[0, 48], [72, 48], [72, 96], [160, 96]], 3, TH, TW) |
                     SG.cells_route([[0, 48], [40, 48]], 4, TH, TW), TH, TW, 402, r_out=1.0, r_in=0.6)
    WA.paint_hd(cv, river)
    from scripts.art.native import screen as SN
    SN.footbridge_hd(cv, 120, 16, 84, 112, river)
    sp = props_row([('rock', *g(3, 2), 38), ('bench', *g(14, 4), 43), ('well', *g(3, 13), 6), ('rock', *g(9, 13), 39)])
    return cv, sp, 'river: cell plan, wide rounded bends, width 3 to 4 cells, bridge on footings'


def sw_cliff():
    cv = lawn(15)
    top = cells([[0, 0, 96, 32], [0, 32, 48, 32], [96, 0, 64, 16]])
    tm = SG.shape(top, TH, TW, 303, r_out=0.25, r_in=0.15)
    rng = np.random.default_rng(4)
    SG.ledge(cv, tm, 32, rng, seed=303, earth='crag', roots=False)
    SG.breakers(cv, tm, rng, 0.12, kind='lip')
    sp = props_row([('rock', *g(9, 11), 40), ('rock', *g(17, 9), 44), ('bench', *g(13, 13), 44)])
    return cv, sp, 'cliff corner: outer and inner, a rock face 32 world px'


def sw_beds():
    cv = lawn(16)
    frame = SG.shape(cells([[24, 24, 112, 56]]), TH, TW, 404, r_out=0.15, r_in=0.1, amp=(0.5, 1.0))
    cv[frame] = C('path_warm', 3)                                    # the raised soil rim (13)
    inner = SG.shape(cells([[32, 32, 96, 40]]), TH, TW, 409, r_out=0.15, r_in=0.1, amp=(0, 0))
    cv[inner] = C('earth', 2)
    cv[frame & ~inner & ~np.roll(frame, 1, 0)] = C("path_warm", 4)
    cv[inner & ~np.roll(inner, 1, 0)] = C('earth', 0)
    for cy in range(4, 10):
        for cx in range(4, 17):
            if cy in (4, 9) or cx in (4, 16):
                continue
            y0, x0 = int((cy * 8 + 1) * D), int((cx * 8 + 1) * D)
            y1, x1 = int((cy * 8 + 7) * D), int((cx * 8 + 7) * D)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            u, v = (xx - x0) / (x1 - x0) * 2 - 1, (yy - y0) / (y1 - y0) * 2 - 1
            mound = (np.abs(u) ** 3 + np.abs(v) ** 3) <= 1
            t = np.where(u + v < -0.5, 4, np.where(u + v < 0.6, 3, 2))
            sub = cv[y0:y1, x0:x1]
            sub[mound] = (FI['earth_warm'] * 8 + t)[mound]
    SG.path_rim(cv, frame, turf(cv) & ~frame)
    sp = props_row([('well', *g(2, 13), 7), ('bench', *g(16, 13), 45), ('rock', *g(18, 2), 41)])
    return cv, sp, 'garden beds: a frame of cells, a mound per cell'


def sw_square():
    cv = lawn(17)
    pave = SG.shape(cells([[32, 16, 96, 72]]), TH, TW, 405, r_out=0.15, r_in=0.1, amp=(0, 0))
    rng = np.random.default_rng(5)
    y = 0
    flags = np.full(cv.shape, C('stone_warm', 3), np.int32)
    while y < TH:
        rh = int(rng.uniform(2.4, 3.2) * D)
        x = -int(rng.integers(0, int(4 * D)))
        while x < TW:
            L = int(rng.uniform(3.5, 6.0) * D)
            V.blk(flags, x, y, x + L - 1, y + rh - 1, ('stone_warm', 'stone', 'stone_warm')[int(rng.integers(0, 3))],
                  int(rng.choice([3, 3, 4, 2])), cut=1)
            x += L
        y += rh
    flags[flags < 0] = C('stone', 1)
    cv[pave] = flags[pave]
    edge = pave & ~ndi.binary_erosion(pave, iterations=int(1.2 * D))
    cv[edge] = C('stone_warm', 4)
    cv[edge & ~np.roll(pave, -1, 0)] = C('stone', 2)
    path = SG.route_shape([[80, 88], [80, 120]], 3, TH, TW, seed=11) & ~pave
    dirt_fill(cv, path, 23)
    SG.path_rim(cv, path, turf(cv) & ~path)
    sp = props_row([('well', *g(10, 6), 8), ('bench', *g(6, 3), 46), ('bench', *g(14, 3), 47), ('rock', *g(2, 12), 42)])
    return cv, sp, 'paved square meeting grass and a dirt path'


def sw_forest():
    cv = lawn(18, fam='leaf', base=2)
    litter = SG.soft_patches(TH, TW, 418, 9.0 * D, 0.2)
    cv[litter] = C('earth_warm', 3)
    cv[litter & SG.soft_patches(TH, TW, 419, 4.0 * D, 0.4)] = C('earth', 2)
    trunks = [('trunk', *g(4, 4), 11), ('trunk', *g(12, 3), 12), ('trunk', *g(8, 10), 13), ('trunk', *g(16, 11), 14)]
    ferns = [('fern', int(rng_x * D), int(rng_y * D), s) for (rng_x, rng_y, s) in ((22, 58, 1), (118, 46, 2), (60, 100, 3), (140, 70, 4), (95, 30, 5))]
    sp = props_row(trunks + ferns + [('rock', *g(18, 6), 43), ('bench', *g(2, 13), 48), ('well', *g(13, 14), 9)])
    return cv, sp, 'forest floor: trunks on cells, undergrowth free'


def sw_shore():
    cv = lawn(19)
    sand = SG.shape(cells([[0, 56, 160, 64], [56, 40, 64, 16]]), TH, TW, 406, r_out=0.15, r_in=0.1, amp=(0.5, 1.0))
    cv[sand] = C('sand', 3)
    p = SG.soft_patches(TH, TW, 407, 10.0 * D, 0.15) & sand
    cv[p] = sib(cv[p], 'warm')
    sea = SG.shape(cells([[0, 88, 160, 32], [24, 80, 48, 8]]), TH, TW, 408, r_out=0.65, r_in=0.4)
    WA.paint_hd(cv, sea)
    SG.path_rim(cv, sand & ~sea, turf(cv))
    sp = props_row([('rock', *g(15, 7), 45), ('bench', *g(4, 3), 49), ('well', *g(16, 3), 10)])
    return cv, sp, 'grass to sand to water: soft, low-contrast transitions'


SWATCHES = (sw_plateau, sw_paths, sw_pond, sw_river, sw_cliff, sw_beds, sw_square, sw_forest, sw_shore)
GRIDDED = (1, 3)                   # the path and the river again, with the cell grid over them


def render(fn):
    cv, sprites, cap = fn()
    V.tidy(cv, passes=1, keep=cv % 8 >= 6)
    im = Image.fromarray(to_rgba(cv), 'RGBA')
    for img, anc, (fx, fy) in sorted(sprites, key=lambda s: s[2][1]):
        im.alpha_composite(img.convert('RGBA'), (int(round(fx - anc[0])), int(round(fy - anc[1]))))
    return im, cap


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
    ap.add_argument('--eastward', help='folder of Eastward native frames (local only)')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    tiles = [render(fn) for fn in SWATCHES]
    sheet = Image.new('RGB', (1920, 1080), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, (im, cap) in enumerate(tiles):
        x, y = (i % 4) * TW, (i // 4) * TH
        if y + TH > 1080:
            break
        sheet.paste(im.convert('RGB'), (x, y))
        d.rectangle([x + 2, y + 2, x + 8 + 6 * len(cap), y + 14], fill=(0, 0, 0))
        d.text((x + 5, y + 3), cap, fill=(255, 255, 255))
    # the last cells of the sheet: the grid over the plateau, the paths and the river, so the plans read
    for j, idx in enumerate((0,) + GRIDDED):
        gx, gy = (1 + j) * TW, 2 * TH
        sheet.paste(grid_overlay(tiles[idx][0]).convert('RGB'), (gx, gy))
        d.rectangle([gx + 2, gy + 2, gx + 200, gy + 14], fill=(0, 0, 0))
        d.text((gx + 5, gy + 3), 'the same, with the 24 px cell grid', fill=(255, 255, 255))
    sheet.save(os.path.join(a.out, 'softgrid_swatches_1080p.png'))
    for i, (im, cap) in enumerate(tiles):
        im.save(os.path.join(a.out, f'swatch_{i}_{SWATCHES[i].__name__[3:]}.png'))
    print('wrote', os.path.join(a.out, 'softgrid_swatches_1080p.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main())

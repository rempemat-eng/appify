"""The forest kit: woodland, conifer forest, their edges, glades and the old forest's border.

Claude E's lane (the home valley's places), the rebuild plan's kit table
(docs/vision/rebuild-plan.md, section 3: "Forest kit: woodland, forest edges, clearings, the
old forest's border"). The valley's woodland west of the garden, the Fern hills, Fir Hollow,
the Brackens' pines and the old forest above the Fern hills (the world's north-east edge) are
painted with it. Nothing in the game reads it yet; region builders wire it in once the tools
land (terrace toolkit #90, house style #121, size guide #124, asset ledger #142).

It is drawn on the river and meadow kit's core (river_kit.py, #133: the house-ramp `Plot`,
clusters, outline, cast shadows, `blend`), so the two kits meet without a seam, and in the
house style (docs/vision/house-style.md): every pixel a tone of a house ramp or a family's edge
tone, shade and light moving along the ramps, texture in clusters of two or more pixels,
light from the upper left, cast shadows stepping the ground two tones down, walkable ground
calm (body tone 3) with flowers in drifts rather than flecks (`drifts()`, `calm()`), and
dither only as the 2 x 2 checker in a tier shadow's last 3 px, as the terrace toolkit does. Sizes follow docs/vision/size-guide.md (#124): a broadleaf 90 (78 to
125) with a crown 56 to 80, a pine or spruce 64 to 125 with a crown 28 to 48, a birch 64 to
104, a veteran tree 88 to 160, a holly or young tree 40 to 80, a sapling 20 to 40, a bush 12
to 28, a fern 8 to 16, a stump 8 to 16 tall and 12 to 22 wide, a fallen log 30 to 64 long,
mushrooms in clusters, an earth face 32 a tier with lumps about 13 x 9 and roots in its top
6 px, a side band 5, a stair 40 open between 4 px cheeks with 8 px landings.

The pieces (each takes a seed; all deterministic, numpy only):

- trees: `broadleaf()` (oak, beech, ash, holly, hornbeam), `conifer()` (spruce, fir, Scots
  pine), `veteran()` (the old forest's giants), `young()` (saplings and young trees). Each
  crown is built of lobes in the house foliage recipe (four light bands, clumps of radius 2.6
  a tone above their band with a light cap and a dark U, all three siblings, a yellow-green
  rim on the lit edge), lit once more as a whole tree, so a crown reads as a tree and a row of
  crowns as many trees, not one blob. Leaf tips break the silhouette.
- masses: `woodland()` plants a canopy of many trees from a mix (three or more species and
  sizes, never three of one kind in a row on its front), north to south, so each crown's lit
  top stands against the shaded underside of the one behind; the floor under the canopy goes
  to its dark underside; along the front the trunks, roots and the shade show. Conifers mass
  the same way with their jagged spires.
- undergrowth: `bracken()`, `bramble()` (a thicket of arching stems), `fern()` (male fern,
  hart's tongue), `foxglove()`, `log()` (a fallen trunk with moss, rings and bracket fungus),
  `stump()`, `mushrooms()` (fly agaric, brown caps, a fairy ring of them), `roots()`.
- ground: `litter()` (broadleaf floor: leaves, moss, twigs, sun flecks, bluebells and wood
  anemones), `needles()` (conifer floor: needles, cones, moss cushions), `glade()` (a sunny
  clearing), `path()` (a woodland path: worn earth, leaf drifts at its edges, roots across it,
  stones, a puddle).
- edges and bands: `edge()` (a forest edge frays into the meadow over a band: tall herbs,
  bramble and scrub, outlying trees and saplings, then the canopy, its boundary warped so it
  never runs straight), `old_forest()` (the world's edge in three layers: the walkable fade
  thickening with thicket and fallen trees, the wall of old trees, and the forest beyond as
  `distance()`: layers of distant crowns cooling and lightening as they recede), `strip()`
  (meadow to woodland to old forest).
- slopes on the soft grid: `Tiers` (a tier map: 32 px south faces only, west and east ends as
  5 px side bands), `bank()` (a woodland bank: packed clods, roots hanging from the lip, moss,
  ferns in the face, a litter lip, a damp foot), `side_bands()`, `tier_shadows()` and
  `log_steps()` (a path climbing a face on log risers between earth cheeks).

Walking: trunks, logs, stumps, thickets, faces and the canopy's interior block; paths, the
glade, the litter under the front row and the old forest's fade stay open. `--check` holds
the kit to it (the sample's path walks from the meadow, through the glade and up the steps to
the upper wood; the canopy's front never repeats one species more than three times; the
fade is walkable and the wall is not).

Run:
    python3 scripts/art/forest_kit.py --check      (the walking and mixing contract)
    python3 scripts/art/forest_kit.py [OUT_DIR]
writes OUT_DIR/kit-sheet.png (every piece at 2x, labelled with its detail bar result),
OUT_DIR/compare-eastward.png (measured pieces beside Eastward's at the same character height,
when the references are in REF_DIR), OUT_DIR/sample.png and sample-2x.png (a woodland path
from a meadow edge into a glade and up a slope, 640 x 576), OUT_DIR/strip-2x.png (meadow to
woodland to old forest on one phone screen, 320 x 576), OUT_DIR/sample-vs-eastward.png and
prints the detail bar for every piece and the sample. Default OUT_DIR: napattack-forest-kit in the system's temp folder, never
the repository.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import house_palette as hp  # noqa: E402
import river_kit as rk  # noqa: E402
from river_kit import (BLADES, DOMINOES, EDGE_T, FAMILY, IDX, SMALL, Plot, Sprite, blob, cast,  # noqa: E402
                       despeckle, dilate, erode, fbm, hash01, outline_mask, paste, shift, stamp)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FACE = 32          # a tier's face (size guide: earth face 32)
BAND = 5           # a side band: 0.2 of an adult
STAIR = 40         # a stair's open width between its cheeks


# --- small helpers --------------------------------------------------------------------------
def light(u, v):
    """Light on a round form from the upper left: u, v its offsets in units of its radius."""
    return -0.6 * u - 0.75 * v + 0.25 * np.sqrt(np.maximum(0, 1 - np.minimum(1, u * u + v * v)))


def bands(lv):
    """The house foliage recipe's four light bands."""
    return np.where(lv > 0.5, 4, np.where(lv > 0.05, 3, np.where(lv > -0.45, 2, 1))).astype(np.int8)


def sib(ramp, r):
    """The ramp's warm sibling, cool sibling or body by r in [0, 1)."""
    fam = hp.family(ramp)
    return f'{fam}_warm' if r < 0.3 else f'{fam}_cool' if r > 0.7 else fam


def ellipse(shape, cx, cy, rx, ry, seed=0, wob=0.1, lobes=7):
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    a = np.arctan2(v, u)
    r = 1 + wob * (0.6 * np.sin(a * lobes + seed) + 0.4 * np.sin(a * (lobes + 5) + seed * 1.9))
    return u * u + v * v <= r * r, u, v


def line_px(x0, y0, x1, y1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    return [(int(round(x0 + (x1 - x0) * i / max(1, n - 1))), int(round(y0 + (y1 - y0) * i / max(1, n - 1))))
            for i in range(n)]


def sput(sp: Sprite, x, y, ramp, tone):
    if 0 <= x < sp.w and 0 <= y < sp.h:
        sp.f[y, x] = IDX[ramp]
        sp.t[y, x] = tone
        sp.m[y, x] = True


def pput(p: Plot, x, y, ramp, tone):
    if 0 <= x < p.w and 0 <= y < p.h:
        p.f[y, x] = IDX[ramp]
        p.t[y, x] = tone


def unspeck(a, m, passes=2):
    """No lone pixels inside `m` (a Plot or a Sprite): a pixel unlike all four neighbours
    takes the colour two of them share (glints included; edges stay)."""
    m = np.asarray(m, bool)
    for _ in range(passes):
        key = a.f.astype(np.int32) * 8 + a.t
        nb = [shift(key, dx, dy, -1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        lone = m & (a.t < EDGE_T) & np.all([key != n for n in nb], axis=0)
        if not lone.any():
            return
        pick_ = np.full(key.shape, -1)
        for i in range(4):
            for j in range(i + 1, 4):
                pick_ = np.where((nb[i] == nb[j]) & (nb[i] >= 0) & (nb[i] % 8 < EDGE_T), nb[i], pick_)
        ok = lone & (pick_ >= 0)
        a.f[ok], a.t[ok] = pick_[ok] // 8, pick_[ok] % 8


# --- foliage: the house recipe on any shape -------------------------------------------------
def foliage(sp: Sprite, shape, lv, seed, ramp='leaf', clump=2.6, rim=True, tips=True, needles=False):
    """Paint leaves into `shape` (a mask in the sprite) lit by `lv` (the light at each
    pixel): four light bands; leaf clumps of radius `clump` one tone above their band, each
    with a light cap and a dark U under it, from all three siblings; a yellow-green rim on
    the lit edge; the deep band quiet. `needles` draws conifer sprays instead: short strokes
    hanging down and out. `tips` breaks the silhouette with leaf tips on the lit edges."""
    band = bands(lv)
    sp.put(shape, ramp, band)
    ys, xs = np.nonzero(shape)
    if not len(xs):
        return band
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    fam = hp.family(ramp)
    sx, sy = clump * 2.4, clump * 1.6
    row = 0
    yy = y0 + 1.0
    R = int(math.ceil(clump)) + 2
    while yy < y1:
        xx = x0 + (sx / 2 if row % 2 else 0.6)
        while xx < x1:
            cx = xx + (hash01(int(xx * 3), int(yy * 3), seed) - 0.5) * 1.4
            cy = yy + (hash01(int(xx * 3), int(yy * 3), seed + 1) - 0.5) * 0.8
            ix, iy = int(cx), int(cy)
            xx += sx
            if not (0 <= ix < sp.w and 0 <= iy < sp.h) or not shape[iy, ix]:
                continue
            b = int(band[iy, ix])
            if b <= 1 and hash01(ix, iy, seed + 2) < 0.7:
                continue
            wx0, wx1 = max(0, ix - R), min(sp.w, ix + R + 1)
            wy0, wy1 = max(0, iy - R), min(sp.h, iy + R + 2)
            gx, gy = sp.x[wy0:wy1, wx0:wx1] + 0.5 - cx, sp.y[wy0:wy1, wx0:wx1] + 0.5 - cy
            rr = clump * (0.8 + 0.45 * hash01(ix, iy, seed + 3))
            if needles:
                lean = -1 if cx < (x0 + x1) / 2 else 1
                pts = (np.abs(gx - lean * np.clip(gy, 0, None) * 0.6) < 0.9) & (gy > -clump * 0.6) & (gy < clump * 1.4)
                pts |= (gx * gx + (gy + 0.5) ** 2 <= (clump * 0.7) ** 2)
            else:
                pts = gx * gx + gy * gy * 1.15 <= rr * rr
            pts &= shape[wy0:wy1, wx0:wx1]
            nm = hash01(ix * 7, iy * 7, seed + 5)
            rp = IDX[f'{fam}_warm'] if nm < 0.3 else IDX[f'{fam}_cool'] if nm > 0.7 else IDX[fam]
            F, T, M = sp.f[wy0:wy1, wx0:wx1], sp.t[wy0:wy1, wx0:wx1], sp.m[wy0:wy1, wx0:wx1]
            bb = T.copy()
            bb[pts] = band[wy0:wy1, wx0:wx1][pts]
            F[pts], T[pts] = rp, bb[pts]
            low = pts & ~shift(pts, 0, -1, False) & (gy > 0.5)
            T[low] = np.maximum(0, bb[low] - 1)
            cap = pts & (~shift(pts, 1, 0, False) | ~shift(pts, 0, 1, False)) & (gx < -0.3) & (gy < -0.3) & (b >= 2)
            T[cap] = np.minimum(5, bb[cap] + 1)
            M |= pts
        yy += sy
        row += 1
    # small sibling clusters: more leaves, no more contrast
    sw = shape & (band >= 2) & (hash01(sp.x, sp.y, seed + 11) < 0.05)
    alt = IDX[f'{fam}_warm'] if hash01(seed, 0, 3) < 0.5 else IDX[f'{fam}_cool']
    for dx, dy in ((0, 0), (1, 0)):
        tg = shift(sw, dx, dy, False) & shape
        sp.f[tg] = np.where(sp.f[tg] == alt, IDX[fam], alt)
    if rim:
        edge = shape & (~shift(shape, 1, 0, False) | ~shift(shape, 0, 1, False)) & (band >= 4)
        sp.put(edge, 'grass', 5)
    if tips:
        # leaf tips standing out of the silhouette on its top and west: pairs, never one
        out = ~shape & shift(shape, 0, -1, False) & (hash01(sp.x // 2, sp.y, seed + 13) < 0.22)
        out &= (lv > -0.1) | (hash01(sp.x, sp.y, seed + 14) < 0.3)
        for dx, dy in ((0, 0), (0, -1)) if not needles else ((0, 0), (-1, -1)):
            tg = shift(out, dx, dy, False) & ~shape & ~sp.m
            sp.put(tg, ramp, np.where(lv[np.clip(sp.y + 1, 0, sp.h - 1), sp.x] > 0.05, 3, 2))
    return band


# --- trees ----------------------------------------------------------------------------------
# kind: (leaf ramp, crown w, crown h, trunk seen below the crown, trunk w, bark ramp, lobe
#        size, lobes, clump, habit)
BROADLEAF = {
    'oak': ('leaf', 72, 58, 15, 7, 'timber', 0.34, 9, 2.6, 'broad'),
    'beech': ('leaf_warm', 66, 62, 17, 6, 'stone_warm', 0.34, 10, 2.4, 'broad'),
    'ash': ('grass_cool', 60, 58, 19, 5, 'stone_cool', 0.28, 8, 2.1, 'airy'),
    'hornbeam': ('leaf', 56, 56, 14, 5, 'stone', 0.3, 8, 2.3, 'round'),
    'holly': ('leaf_cool', 34, 40, 8, 3, 'stone', 0.36, 6, 2.0, 'cone'),
}


def broadleaf(kind='oak', seed=0, scale=1.0):
    """A broadleaf tree (size guide: 90, 78 to 125; crown 56 to 80): a crown of lobes, each
    in the house foliage recipe, lit again as one tree; a trunk lit on the west with bark in
    the family's grain, roots flaring at its foot; ivy or moss on the old ones. Kinds: oak
    (broad, gnarled), beech (smooth warm grey bole, a dense rounded crown), ash (light, airy, gaps),
    hornbeam (round, fluted grey), holly (a small dark evergreen of the understorey, berries).
    Returns (sprite, shadow mask, meta)."""
    ramp, cw, ch, th, tw, bark, lr, nl, clump, habit = BROADLEAF[kind]
    j = 0.88 + 0.24 * hash01(seed, 1, 77)
    cw, ch, th = int(cw * scale * j), int(ch * scale * j), int(th * scale * (0.9 + 0.2 * hash01(seed, 2, 77)))
    tw = max(3, int(round(tw * scale)))
    if scale > 1.2:                       # a bigger crown carries more lobes, not bigger ones
        nl, lr = int(nl * scale ** 1.6), lr / scale ** 0.5
    W, H = cw + 14, ch + th + 8
    fx, fy = W // 2, H - 4
    sp = Sprite(W, H, fx, fy)
    lean = int((hash01(seed, 3, 77) - 0.5) * 6 * scale)
    cx, cy = fx + lean, fy - th - ch / 2 + 2
    # the trunk first: the crown hangs over its top
    _bole(sp, fx - tw // 2, int(cy), fy, tw, bark, seed, flare=2 if tw >= 5 else 1, kind=kind)
    # the lobes, laid out over the crown and drawn top first, so the lower ones stand in
    # front with their lit tops against the shade of the ones behind
    lobes = []
    rx, ry = cw / 2, ch / 2
    for i in range(nl):
        a = i * 2.39996 + seed * 0.7
        fr = math.sqrt((i + 0.5) / nl) * 0.66
        lx = cx + rx * fr * math.cos(a)
        ly = cy + ry * fr * math.sin(a) * (0.9 if habit != 'cone' else 1.0)
        if habit == 'cone':
            lx = cx + (lx - cx) * (0.4 + 0.6 * (ly - (cy - ry)) / (2 * ry))
        # big masses inside, small clumps at the rim: lobes vary 2 to 3x within a crown
        big = 1.45 - 1.05 * fr / 0.66
        s = big * (0.8 + 0.4 * hash01(i, 5, seed))
        r0 = min(rx, ry) * lr * s * (1.15 if habit == 'broad' else 1.0)
        lobes.append((lx, ly, r0 * 1.06, r0))
    for j in range(max(3, nl // 3)):                          # small clumps breaking the rim
        a = j * 2.1 + seed * 1.3
        lx, ly = cx + rx * 0.64 * math.cos(a), cy + ry * 0.62 * math.sin(a)
        if ly > cy + ry * 0.5:
            continue
        r0 = min(rx, ry) * lr * (0.42 + 0.2 * hash01(j, 6, seed))
        lobes.append((lx, ly, r0, r0 * 0.95))
    lobes.append((cx, cy - ry * 0.1, rx * 0.55, ry * 0.5))       # the core, so no lobe floats
    shape_all = np.zeros(sp.m.shape, bool)
    _u, _v = (sp.x + 0.5 - cx) / rx, (sp.y + 0.5 - cy) / ry
    tree_lv = light(_u * 0.9, _v * 0.9)
    for k, (lx, ly, lrx, lry) in enumerate(sorted(lobes, key=lambda q: q[1])):
        m, u, v = ellipse(sp.m.shape, lx, ly, lrx, lry, seed + k, 0.2, 7)
        lv = 1.05 * light(u, v) + 0.4 * tree_lv - 0.02
        # the lobe in front shades the leaves just behind it by one tone (no dark line)
        occ = shape_all & ~m & shift(m, 0, -1, False)
        sp.step(occ, -1, lo=1)
        if habit == 'airy':
            m &= ~((hash01(sp.x // 3, sp.y // 3, seed + k) < 0.06) & (light(u, v) < 0))
        foliage(sp, m, lv, seed * 31 + k, ramp, clump, rim=True, tips=k >= len(lobes) - 3 or ly < cy)
        shape_all |= m
    # the deep shade pockets between the lobes drop cool, towards blue-violet
    pocket = shape_all & (sp.t <= 1) & (tree_lv < 0.1)
    sp.f[pocket] = IDX['leaf_cool']
    deep = pocket & (hash01(sp.x // 3, sp.y // 2, seed + 21) < 0.3)
    sp.f[deep], sp.t[deep] = IDX['slate_cool'], 1
    sp.t[pocket & ~deep & (hash01(sp.x // 2, sp.y // 2, seed + 23) < 0.35)] = 0
    # a limb glimpsed through a gap, and the odd gap open to the sky
    if habit in ('broad', 'airy', 'round'):
        for i in range(2):
            gx = int(cx + (hash01(i, 0, seed + 22) - 0.5) * rx)
            gy = int(cy + ry * (0.15 + 0.3 * hash01(i, 1, seed + 22)))
            for (px, py) in line_px(gx, gy, gx + (4 if i else -4), gy + 4):
                if 0 <= px < W and 0 <= py < H and shape_all[py, px] and sp.t[py, px] <= 2:
                    sp.f[py, px], sp.t[py, px] = IDX[bark], 2
    if kind == 'holly':
        b = shape_all & (sp.t >= 2) & (hash01(sp.x // 2, sp.y // 2, seed + 30) < 0.07) & (sp.y % 2 == 0)
        sp.put(b, 'berry_warm', 4)
        sp.put(shift(b, 1, 0, False) & shape_all, 'berry', 2)
    unspeck(sp, shape_all, 1)
    sh = rk.tree_shadow(sp, fx + 3, cw * 0.46, max(4, cw * 0.14))
    return sp, sh, {'kind': kind, 'crown': (cx, cy, rx, ry), 'trunk': (fx - tw // 2, tw)}


def _bole(sp: Sprite, x, y0, y1, w, bark, seed, flare=2, kind='', fork=True):
    """A trunk from y0 down to its foot y1, `w` wide at breast height: tapering upward and
    wandering a little, lit on the west and dark on the east, its bark in irregular patches
    (furrows of uneven length on timber; smooth grey with lenticels and patches of the cool
    sibling), forking into one or two limbs that run up into the crown, the foot flaring
    into two to four roots that run down and out into the litter, moss on the north and
    west low down, ivy up an old oak."""
    H = max(1, y1 - y0)
    mid = x + w / 2
    cols = {}
    for y in range(y0, y1 + 1):
        f = (y - y0) / H                                       # 0 at the top, 1 at the foot
        ww = max(2.0, w - 2.5 + 3.0 * f)
        ww += flare * max(0.0, (y - (y1 - 5)) / 5.0) ** 2 * 2  # the flare, in the last rows
        cxw = mid + 0.7 * math.sin(y / 7.0 + seed)
        l, r = int(round(cxw - ww / 2)), int(round(cxw + ww / 2))
        cols[y] = (l, r)
        for px in range(l, r):
            u = (px - l + 0.5) / max(1, r - l)
            k = 4 if u < 0.2 else 3 if u < 0.45 else 2 if u < 0.78 else 1
            sput(sp, px, y, bark, k)
    fam = hp.family(bark)
    inner = np.zeros(sp.m.shape, bool)
    for y, (l, r) in cols.items():
        if r - l > 2:
            inner[y, l + 1:r - 1] = True
    inner &= sp.m
    run = 3 + (hash01(sp.x, 0, seed + 8) * 5).astype(int)      # furrows of uneven length
    off = (hash01(sp.x, 1, seed + 9) * 7).astype(int)
    if fam == 'timber':
        fur = inner & (hash01(sp.x, (sp.y + off) // run, seed + 1) < 0.32)
        sp.step(fur, -1, lo=1)
        rid = inner & ~fur & (hash01(sp.x // 2, (sp.y + off) // 3, seed + 2) < 0.22)
        sp.f[rid] = IDX[f'{fam}_warm']
    else:
        patch = inner & (hash01((sp.x + sp.y // 5) // 2, sp.y // 4, seed + 4) < 0.3)
        sp.f[patch] = IDX[f'{fam}_cool']
        lent = inner & (hash01(sp.x // 2, sp.y, seed + 3) < 0.07)
        sp.step(lent & ~shift(lent, 1, 0, False), -1, lo=1)
        lit = inner & (hash01(sp.x, (sp.y + off) // run, seed + 5) < 0.18) & (sp.t >= 3)
        sp.step(lit, 1, hi=4)
    # limbs: the bole forks under the crown; the leaves cover where they go
    if fork and H > 14:
        l, r = cols[y0]
        for side in (-1, 1):
            if side > 0 and hash01(seed, 4, 3) < 0.3:
                continue
            sx0 = l if side < 0 else r - 1
            ln = 6 + int(hash01(side + 2, 5, seed) * 6)
            for i in range(ln):
                px, py = sx0 + side * (i * 2 // 3), y0 - i
                sput(sp, px, py, bark, 3 if side < 0 else 2)
                sput(sp, px + side, py, bark, 2 if side < 0 else 1)
    # moss on the north and west low down, in patches; ivy up an old oak
    l1, r1 = cols[y1]
    moss = sp.m & inner.copy()
    moss = sp.m & (sp.y > y1 - 10) & (sp.y < y1 - 1) & (sp.t >= 3) & \
        (hash01(sp.x // 2, sp.y // 2, seed + 5) < 0.55)
    sp.f[moss] = IDX['leaf']
    sp.t[moss] = np.where(sp.t[moss] >= 4, 3, 2)
    if kind == 'oak' and hash01(seed, 9, 5) < 0.6:
        ivy = sp.m & (sp.y >= y0) & (sp.y < y1 - 2) & (hash01(sp.x // 2, sp.y // 2, seed + 6) < 0.3) & \
            ((sp.y - y0) > 3 * np.abs(sp.x - mid))
        sp.put(ivy, 'leaf_cool', np.where(hash01(sp.x, sp.y, seed + 7) < 0.4, 3, 2))
    # roots: running down and out from the flare into the litter, lit along their tops
    n = 2 + int(hash01(seed, 0, 6) * 3)
    for i in range(n):
        side = -1 if i % 2 == 0 else 1
        ln = 4 + int(hash01(i, 1, seed) * 5)
        sx = l1 if side < 0 else r1 - 1
        sy = y1 - 2 - int(hash01(i, 2, seed) * 2)
        for s_ in range(ln):
            px, py = sx + side * (s_ + 1), sy + (s_ + 1) // 2
            if py > y1 + 1:
                break
            sput(sp, px, py, bark, 3 if s_ < ln - 1 else 2)
            if s_ < ln - 2:
                sput(sp, px, py + 1, bark, 1)


# kind: (leaf ramp, height, width, trunk seen, tiers, habit)
CONIFER = {
    'spruce': ('leaf_cool', 92, 40, 6, 9, 'skirts'),
    'fir': ('grass_cool', 100, 42, 6, 9, 'skirts'),
    'pine': ('leaf_cool', 96, 48, 34, 4, 'clumps'),
}


def conifer(kind='spruce', seed=0, scale=1.0):
    """A conifer (size guide: pine and fir 64 to 125, crown 28 to 48). Spruce and fir: a cone
    of drooping tiers, each tier lit along its top and its west, in its own shade where the
    tier above hangs over it, its branch tips lit; needles as short strokes hanging down and
    out; uneven tiers, a lean, each side its own reach, the trunk showing in a gap. Scots
    pine: a long bare bole, fox-red above, grey and furrowed below, under a flattish umbrella
    of two or three pads set off to one side. Returns (sprite, shadow mask, meta)."""
    ramp, Ht, Wd, ts, nt, habit = CONIFER[kind]
    j = 0.86 + 0.28 * hash01(seed, 1, 91)
    Ht, Wd = int(Ht * scale * j), int(Wd * scale * (0.9 + 0.2 * hash01(seed, 2, 91)))
    W, H = Wd + 10, Ht + 6
    fx, fy = W // 2, H - 4
    sp = Sprite(W, H, fx, fy)
    lean = (hash01(seed, 3, 91) - 0.5) * 0.14                   # px of lean per px of height
    if habit == 'clumps':
        # Scots pine: a long bare bole, fox-red above, grey and furrowed below; a flattish
        # umbrella of two or three irregular pads at the top, set off to one side
        top = fy - Ht
        tw = max(3, int(4 * scale))
        _bole(sp, fx - tw // 2, top + 8, fy, tw, 'stone_cool', seed, flare=1, fork=False)
        fox = sp.m & (sp.y < fy - int(Ht * 0.45))
        sp.f[fox] = IDX['clay_warm']
        sp.t[fox] = np.clip(sp.t[fox] + 1, 2, 4)
        side = 1 if hash01(seed, 4, 91) < 0.5 else -1
        pads = [(fx + side * Wd * 0.12, top + 9, Wd * 0.46, 6.5),
                (fx - side * Wd * 0.2, top + 16 + 3 * hash01(seed, 5, 91), Wd * 0.28, 5.0)]
        if hash01(seed, 6, 91) < 0.7:
            pads.append((fx + side * Wd * 0.3, top + 21 + 3 * hash01(seed, 7, 91), Wd * 0.2, 4.0))
        for i, (cx, cy, rx, ry) in enumerate(pads):              # branches to each pad
            for (px, py) in line_px(fx, cy + ry + 5, cx, cy + ry * 0.3):
                sput(sp, px, py, 'clay_warm', 3)
                sput(sp, px, py + 1, 'timber_cool', 1)
        for i, (cx, cy, rx, ry) in enumerate(sorted(pads, key=lambda q: q[1])):
            m, u, v = ellipse(sp.m.shape, cx, cy, rx, ry, seed + i, 0.24, 9)
            m &= ~((v > 0.35) & (hash01(sp.x // 3, 0, seed + i) < 0.4))   # a ragged underside
            foliage(sp, m, light(u, v * 1.3) - 0.05, seed * 13 + i, ramp, 2.0, rim=True, needles=True)
        unspeck(sp, sp.m, 2)
        sh = rk.tree_shadow(sp, fx + 3, Wd * 0.4, max(4, Wd * 0.12))
        return sp, sh, {'kind': kind, 'crown': (fx, fy - Ht / 2, Wd / 2, Ht / 2), 'trunk': (fx - tw // 2, tw)}
    # spruce and fir: uneven tiers from the bottom up, each upper tier hanging over the next,
    # the whole tree leaning a little, each side its own reach, tips drooping past the tier
    # below, the trunk showing through a gap or two
    tw = max(3, int(4 * scale))
    top = fy - Ht
    body = Ht - ts
    _bole(sp, fx - tw // 2, top + 6, fy, tw, 'timber_cool', seed, flare=1, fork=False)
    wts = [0.75 + 0.55 * hash01(i, 8, seed) for i in range(nt)]
    edges = np.cumsum([0] + wts) / sum(wts)
    gaps = {int(1 + hash01(seed, 9, 91) * (nt - 3)), int(2 + hash01(seed, 10, 91) * (nt - 3))}
    hang = np.zeros(sp.m.shape, bool)
    for i in range(nt - 1, -1, -1):
        f0, f1 = edges[i], edges[i + 1]
        y_top = top + int(body * f0 ** 1.05) - (2 if i else 0)
        y_bot = top + int(body * f1 ** 1.05) + 3
        cxt = fx + lean * (fy - (y_top + y_bot) / 2)
        base = max(3, (Wd / 2) * (0.18 + 0.82 * f1))
        hl = base * (0.78 + 0.36 * hash01(i, 0, seed))
        hr = base * (0.78 + 0.36 * hash01(i, 11, seed))
        half = np.where(sp.x + 0.5 < cxt, hl, hr)
        uu = (sp.x + 0.5 - cxt) / half
        dl, dr = 3 + 5 * hash01(i, 12, seed), 3 + 5 * hash01(i, 13, seed)
        droop = np.where(uu < 0, dl, dr) * np.abs(uu) ** 1.6
        saw = ((sp.x + i * 2 + seed) % (3 + i % 3) < 2) * 1.5
        upper = y_top + np.abs(uu) ** 0.8 * (y_bot - y_top) * 0.6
        tier = (np.abs(uu) <= 1) & (sp.y + 0.5 >= upper) & (sp.y + 0.5 <= y_bot + droop - saw)
        if i in gaps:                                             # the trunk seen in a gap
            gs = 1 if hash01(i, 14, seed) < 0.5 else -1
            tier &= ~((sp.y > y_bot - 4) & (np.abs(sp.x + 0.5 - (cxt + gs * 2)) < 2.5))
        if not tier.any():
            continue
        vv = (sp.y + 0.5 - (y_top + y_bot) / 2) / max(2, (y_bot - y_top) / 2)
        lv = light(uu * 0.9, vv * 1.1) - 0.05
        lv = np.where(sp.y + 0.5 < upper + 2.5, lv + 0.5, lv)      # each tier's lit top
        tr = ramp if (i + seed) % 3 else ('grass_cool' if ramp == 'leaf_cool' else 'leaf_cool')
        foliage(sp, tier, lv, seed * 17 + i, tr, 1.9, rim=i < 3, tips=True, needles=True)
        tipw = tier & ~shift(tier, 0, 1, False) & (uu < 0.3) & (hash01(sp.x // 2, sp.y, seed + i) < 0.35)
        sp.put(tipw | (shift(tipw, 1, 0, False) & tier), 'grass_warm', 4)
        if kind == 'spruce' and i < nt // 2:
            cone = tier & (hash01(sp.x // 2, sp.y // 3, seed + 40 + i) < 0.025) & (sp.y > y_bot - 3)
            sp.put(cone, 'timber', 3)
            sp.put(shift(cone, 0, 1, False) & tier, 'timber', 1)
        fringe = tier & ~shift(tier, 0, -2, False)                  # the skirt's dark hem
        sp.step(fringe, -1, lo=0)
        sp.step(fringe & (uu > 0.1), -1, lo=0)
        under = hang & ~tier & (shift(tier, 0, 1, False) | shift(tier, 0, 2, False))
        sp.step(under, -2, lo=0)
        sp.step(hang & ~tier & shift(tier, 0, 3, False) & ~under, -1, lo=0)
        hang |= tier
    lx = int(round(fx + lean * Ht))
    for y in range(top - 3, top + 3):                             # the leader
        sput(sp, lx, y, ramp, 4 if y < top else 3)
        if y >= top:
            sput(sp, lx + 1, y, ramp, 2)
    unspeck(sp, sp.m, 2)
    sh = rk.tree_shadow(sp, fx + 3, Wd * 0.42, max(4, Wd * 0.13))
    return sp, sh, {'kind': kind, 'crown': (fx, fy - Ht / 2, Wd / 2, Ht / 2), 'trunk': (fx - tw // 2, tw)}


def veteran(seed=0, scale=1.0):
    """An old forest giant (size guide: veteran tree 88 to 160, crown 64 to 128, trunk 2 x 2
    cells): a massive buttressed bole, hollow at its foot, furred with moss and ferns, under a
    wide crown of heavy lobes in the cool green of old shade."""
    sp0, _sh, meta = broadleaf('oak', seed, 1.45 * scale)
    W, H = sp0.w, sp0.h
    sp = Sprite(W, H, sp0.fx, sp0.fy)
    tw = int(16 * scale)
    x = sp.fx - tw // 2
    cy = int(meta['crown'][1])
    _bole(sp, x, cy, sp.fy, tw, 'timber_cool', seed, flare=3, kind='oak')
    # buttresses: wedges at both sides of the foot
    for side in (-1, 1):
        for y in range(sp.fy - 12, sp.fy + 1):
            reach = int((y - (sp.fy - 12)) * 0.45)
            for dx in range(reach):
                px = (x - 3 - dx) if side < 0 else (x + tw + 2 + dx)
                sput(sp, px, y, 'timber_cool', 3 if side < 0 and dx < reach - 1 else 1)
    # the hollow: a dark arch in the foot
    hx = sp.fx - 3
    for y in range(sp.fy - 11, sp.fy):
        half = 3 if y > sp.fy - 9 else 2
        for dx in range(-half, half + 1):
            sput(sp, hx + dx, y, 'timber_cool', 0)
    for dx in (-3, -2):
        sput(sp, hx + dx, sp.fy - 10, 'timber_cool', 3)
    # moss over the whole lower bole, ferns in its crotch
    mm = sp.m & (sp.y > cy + 6) & (hash01(sp.x // 2, sp.y // 2, seed + 40) < 0.45) & (sp.t >= 1)
    sp.f[mm] = IDX['leaf_warm']
    sp.t[mm] = np.where(sp.x[mm] < sp.fx, 3, 2)
    # the crown hangs over the bole: every leaf pixel of the oak's crown stays on top
    lf = sp0.m & np.isin(FAMILY[sp0.f], [IDX['leaf'], IDX['grass']])
    lf &= ~(sp.m & (sp.y > sp.fy - 14))
    sp.f[lf], sp.t[lf] = sp0.f[lf], sp0.t[lf]
    sp.m |= lf
    cool = sp.m & (sp.y < cy + 6) & (FAMILY[sp.f] == IDX['leaf'])
    sp.f[cool] = np.where(hash01(sp.x // 3, sp.y // 3, seed + 41)[cool] < 0.6, IDX['leaf_cool'], sp.f[cool])
    unspeck(sp, sp.m, 2)
    sh = rk.tree_shadow(sp, sp.fx + 4, W * 0.46, max(6, W * 0.13))
    return sp, sh, {'kind': 'veteran', 'crown': meta['crown'], 'trunk': (x, tw)}


def young(kind='oak', seed=0):
    """A young tree or sapling of a kind (size guide: young 40 to 80, sapling 20 to 40),
    standing at a wood's edge or in a glade where light reaches the floor."""
    if kind in CONIFER:
        return conifer(kind, seed, 0.42 + 0.2 * hash01(seed, 0, 5))
    sc = 0.42 + 0.25 * hash01(seed, 0, 5)
    return broadleaf(kind if kind in BROADLEAF else 'hornbeam', seed, sc)


# --- undergrowth ----------------------------------------------------------------------------
def _frond(sp: Sprite, x0, y0, ang, ln, ramp, seed, lit, pinna=3, droop=0.5, rust=False):
    """One frond: a rachis arching from (x0, y0) at angle `ang` (radians from vertical,
    negative to the west) over `ln` px, its pinnae as short strokes down both sides, longest
    near the base; lit fronds (west) a tone higher; a rust tip on old bracken."""
    pts = []
    for i in range(int(ln * 1.4)):
        s = i / (ln * 1.4)
        a = ang + droop * s * s * (1 if ang >= 0 else -1) * 0.9
        x = x0 + math.sin(a) * s * ln * 1.05
        y = y0 - math.cos(a) * s * ln + droop * s * s * ln * 0.35
        pts.append((int(round(x)), int(round(y)), s))
    seen = set()
    k0 = 3 if lit else 2
    for (x, y, s) in pts:
        if (x, y) in seen:
            continue
        seen.add((x, y))
        k = k0
        tip = rust and s > 0.78
        sput(sp, x, y, 'clay' if tip else ramp, 3 if tip else min(4, k + 1) if lit else k)
        n = int(round(pinna * (1 - s * 0.75)))
        if n >= 1:
            for side in (-1, 1):
                for d in range(1, n + 1):
                    px, py = x + side * d, y + (d + 1) // 2
                    kk = k - (1 if side > 0 and not lit else 0)
                    sput(sp, px, py, 'clay_warm' if tip else ramp, kk)
                    sput(sp, px, py + 1, 'clay_warm' if tip else ramp, max(1, kk - 1))


def bracken(seed=0, w=26):
    """Bracken (size guide: fern, low leafy plant 8 to 16, 12 to 28 wide): four to six fronds
    arching out of the floor, green with the odd rust tip, lit on the west."""
    sp = Sprite(w + 10, 26, (w + 10) // 2, 24)
    n = 4 + int(hash01(seed, 0, 3) * 3)
    for i in range(n):
        a = -0.8 + 1.6 * (i + 0.5) / n + (hash01(i, 1, seed) - 0.5) * 0.25
        ramp = 'grass_warm' if hash01(i, 2, seed) < 0.55 else 'leaf_warm'
        _frond(sp, sp.fx + int((hash01(i, 3, seed) - 0.5) * 6), sp.fy, a, 13 + hash01(i, 4, seed) * 5, ramp,
               seed + i, lit=a < 0.25, pinna=3, droop=0.35, rust=hash01(i, 5, seed) < 0.3)
    unspeck(sp, sp.m, 2)
    sh = np.zeros(sp.m.shape, bool)
    sh[sp.fy - 1:sp.fy + 1, sp.fx - 6:sp.fx + 10] = True
    return sp, sh


def fern(kind='male', seed=0):
    """A fern in the shade (size guide 8 to 16 tall): 'male' a shuttlecock of fronds rising
    from one crown, dark green, lit on the west; 'hart' hart's tongue, glossy straps arching
    out of a bank, each lit along its upper edge."""
    if kind == 'hart':
        sp = Sprite(20, 13, 10, 11)
        for i in range(5):
            a = -1.1 + 2.2 * (i + 0.5) / 5
            ln = 7 + int(hash01(i, 0, seed) * 4)
            for s in range(ln):
                ss = s / ln
                x = sp.fx + math.sin(a) * s
                y = sp.fy - math.cos(a) * s * 0.9 + ss * ss * 3
                xi, yi = int(round(x)), int(round(y))
                lit = a < 0.2
                sput(sp, xi, yi, 'leaf_cool', 4 if lit and s > 1 else 3)
                sput(sp, xi, yi + 1, 'leaf_cool', 2 if lit else 1)
        sh = np.zeros(sp.m.shape, bool)
        sh[sp.fy:sp.fy + 1, sp.fx - 5:sp.fx + 8] = True
        return sp, sh
    sp = Sprite(32, 26, 16, 24)
    n = 6 + int(hash01(seed, 0, 4) * 2)
    for i in range(n):
        a = -0.62 + 1.24 * (i + 0.5) / n + (hash01(i, 1, seed) - 0.5) * 0.2
        _frond(sp, sp.fx, sp.fy, a, 14 + hash01(i, 2, seed) * 3, 'leaf' if i % 2 else 'leaf_cool', seed + i,
               lit=a < 0.2, pinna=3, droop=0.45)
    unspeck(sp, sp.m, 2)
    sput(sp, sp.fx, sp.fy, 'timber', 1)
    sput(sp, sp.fx + 1, sp.fy, 'timber', 1)
    sh = np.zeros(sp.m.shape, bool)
    sh[sp.fy - 1:sp.fy + 1, sp.fx - 7:sp.fx + 11] = True
    return sp, sh


def foxglove(seed=0):
    """A foxglove at a glade's edge (tall herb 14 to 32): a stem of pink bells hanging on
    one side, opening from the bottom, over a rosette of broad leaves."""
    sp = Sprite(14, 30, 6, 28)
    H = 18 + int(hash01(seed, 0, 6) * 8)
    for y in range(sp.fy - H, sp.fy - 2):
        sput(sp, sp.fx, y, 'leaf', 2)
    for j, y in enumerate(range(sp.fy - H + 2, sp.fy - 6, 2)):
        k = 4 if j % 2 == 0 else 3
        sput(sp, sp.fx + 1, y, 'berry_warm', k)
        sput(sp, sp.fx + 2, y, 'berry_warm', k - 1)
        sput(sp, sp.fx + 1, y + 1, 'berry', k - 2)
        if j % 3 == 1:
            sput(sp, sp.fx - 1, y, 'berry_warm', 3)
            sput(sp, sp.fx - 1, y + 1, 'berry', 2)
    for y in range(sp.fy - H - 3, sp.fy - H + 2):
        sput(sp, sp.fx, y, 'leaf_warm', 3)
    for dx in range(-5, 7):
        h = 2 if abs(dx) < 4 else 1
        for dy in range(h):
            sput(sp, sp.fx + dx, sp.fy - dy, 'leaf', 3 if dx < 0 and dy else 2)
    sh = np.zeros(sp.m.shape, bool)
    sh[sp.fy:sp.fy + 2, sp.fx - 2:sp.fx + 9] = True
    return sp, sh


def bramble(seed=0, w=40):
    """A bramble thicket (bush 12 to 28 tall, 16 to 42 wide): a mound of leaves in the house
    recipe, arching stems lit along their tops, white flowers and berries in clusters, red
    unripe and black ripe."""
    h = max(12, int(w * 0.5))
    sp = Sprite(w + 6, h + 6, (w + 6) // 2, h + 3)
    m, u, v = ellipse(sp.m.shape, sp.fx, sp.fy - h * 0.45, w / 2, h * 0.5, seed, 0.22, 9)
    m &= sp.y <= sp.fy
    foliage(sp, m, light(u, v) - 0.1, seed, 'leaf', 2.0, rim=False, tips=True)
    for i in range(3 + w // 14):
        x0 = sp.fx + int((hash01(i, 0, seed) - 0.5) * w * 0.8)
        ln = 8 + int(hash01(i, 1, seed) * 8)
        d = 1 if hash01(i, 2, seed) < 0.5 else -1
        for s in range(ln):
            x = x0 + d * s
            y = int(sp.fy - h * 0.55 - math.sin(math.pi * s / ln) * 6)
            sput(sp, x, y, 'berry_cool', 3)
            sput(sp, x, y + 1, 'berry_cool', 1)
    fl = m & (sp.t >= 3) & (hash01(sp.x // 2, sp.y // 2, seed + 3) < 0.06) & (sp.x % 2 == 0)
    sp.put(fl, 'plaster', 5)
    sp.put(shift(fl, 1, 0, False) & m, 'plaster', 3)
    fr = m & (hash01(sp.x // 2, sp.y // 2, seed + 4) < 0.05) & (sp.y % 2 == 1) & ~fl & ~shift(fl, 1, 0, False)
    sp.put(fr, 'dusk_cool', 1)
    sp.put(shift(fr, 1, 0, False) & m, 'berry', 2)
    sh = blob(sp.fx + 3, sp.fy, w * 0.5, 3, sp.m.shape, seed, 0.1)
    return sp, sh


def log(seed=0, length=48):
    """A fallen trunk (size guide: 8 to 18 tall, 30 to 64 long): a lying cylinder lit along
    its top, bark furrowed along its length, moss and a fern on its back, its cut end showing
    rings and a split, the broken end jagged, bracket fungus on its side, a stub of a branch."""
    d = 10 + int(hash01(seed, 0, 8) * 5)
    W, H = length + 8, d + 8
    sp = Sprite(W, H, W // 2, H - 3)
    x0, x1 = 4, length + 3
    yt = H - 3 - d
    for x in range(x0, x1):
        jag = 0
        if x > x1 - 5:
            jag = int(hash01(x, 0, seed) * 4)
        for r in range(jag, d):
            fy = r / max(1, d - 1)
            k = 4 if fy < 0.18 else 3 if fy < 0.45 else 2 if fy < 0.75 else 1
            sput(sp, x, yt + r, 'timber', k)
    body = sp.m.copy()
    fur = body & (hash01(sp.x // 4, sp.y, seed + 1) < 0.3) & (sp.t >= 2) & (sp.t <= 3)
    sp.step(fur, -1, lo=1)
    sp.f[body & (hash01(sp.x // 3, sp.y // 2, seed + 2) < 0.2)] = IDX['timber_cool']
    # moss along the back, in clumps lit on their tops
    mo = body & (sp.y < yt + 4) & (fbm(sp.x, sp.y, 5, seed + 3) > 0.45)
    sp.put(mo, 'leaf', np.where(sp.y == yt, 4, 3))
    sp.put(mo & (sp.y == yt + 3), 'leaf', 2)
    # the sawn end at the west: an ellipse of rings
    cx, cy = x0 + 2, yt + d / 2
    for y in range(yt, yt + d):
        for x in range(x0 - 2, x0 + 4):
            u, v = (x + 0.5 - cx) / 3.2, (y + 0.5 - cy) / (d / 2)
            rr = math.sqrt(u * u + v * v)
            if rr <= 1:
                k = 4 if rr > 0.85 else 3 if int(rr * 4) % 2 else 2
                sput(sp, x, y, 'sand_warm' if rr < 0.85 else 'timber_warm', k)
    for y in range(int(cy) - 1, int(cy) + 2):
        sput(sp, x0 + 2, y, 'timber_cool', 1)
    # bracket fungus on the side, a branch stub on top
    bx = x0 + 10 + int(hash01(seed, 4, 8) * (length - 24))
    for j in range(2):
        for dx in range(4 - j):
            sput(sp, bx + dx + j * 6, yt + d // 2 + j * 2, 'brass_cool', 4 if dx < 2 else 3)
            sput(sp, bx + dx + j * 6, yt + d // 2 + j * 2 + 1, 'brass_cool', 1)
    sx = x0 + length // 2 + 4
    for i in range(5):
        sput(sp, sx + i // 2, yt - i, 'timber', 3)
        sput(sp, sx + i // 2 + 1, yt - i, 'timber', 1)
    sh = np.zeros(sp.m.shape, bool)
    sh[H - 3:H, x0 + 3:x1 + 3] = True
    sh[H - 5:H - 2, x1 - 2:x1 + 3] = True
    block = body.copy()
    return sp, sh, block


def stump(seed=0):
    """A stump (8 to 16 tall, 12 to 22 wide): the sawn top in rings with a crack, lit; bark
    sides lit on the west; roots running into the floor; moss on its foot and mushrooms on
    its north side."""
    w = 13 + int(hash01(seed, 0, 9) * 6)
    hgt = 7 + int(hash01(seed, 1, 9) * 5)
    W, H = w + 12, hgt + 12
    sp = Sprite(W, H, W // 2, H - 3)
    x0 = sp.fx - w // 2
    ty = sp.fy - hgt
    for y in range(ty, sp.fy + 1):
        for dx in range(w):
            k = 4 if dx < 2 else 3 if dx < w // 2 else 2 if dx < w - 2 else 1
            sput(sp, x0 + dx, y, 'timber_cool', k)
    fur = sp.m & (hash01(sp.x, sp.y // 3, seed + 2) < 0.3)
    sp.step(fur, -1, lo=1)
    for y in range(ty - 4, ty + 3):
        for x in range(x0, x0 + w):
            u, v = (x + 0.5 - (x0 + w / 2)) / (w / 2), (y + 0.5 - (ty - 0.5)) / 3.5
            rr = math.sqrt(u * u + v * v)
            if rr <= 1:
                k = 3 if rr > 0.86 else 5 if (int(rr * 5) % 2 and u < 0) else 4 if int(rr * 5) % 2 else 3
                sput(sp, x, y, 'timber_warm' if rr > 0.86 else 'sand_warm', k)
    for i in range(3):
        sput(sp, x0 + w // 2 + i, ty - 1 + i // 2, 'timber_cool', 1)
    for side in (-1, 1):
        for s in range(4):
            px = (x0 - 1 - s) if side < 0 else (x0 + w + s)
            sput(sp, px, sp.fy - 1 + s // 2, 'timber_cool', 3 if side < 0 else 2)
            sput(sp, px, sp.fy + s // 2, 'timber_cool', 1)
    mo = sp.m & (sp.y > sp.fy - 3) & (hash01(sp.x // 2, sp.y, seed + 3) < 0.6)
    sp.put(mo, 'leaf', np.where(sp.x < sp.fx, 3, 2))
    sh = blob(sp.fx + 4, sp.fy, w * 0.6, 3, sp.m.shape, seed, 0.08)
    return sp, sh


def mushrooms(kind='brown', seed=0, n=3):
    """A cluster of mushrooms (2 to 18 tall, clusters of two or more pixels): 'agaric' fly
    agaric, red caps with white flecks in pairs; 'brown' brown caps lit on their tops; pale
    stems, a dark gill line under each cap."""
    sp = Sprite(16, 12, 7, 10)
    for i in range(n):
        x = 2 + int(i * 10 / max(1, n - 1)) + int((hash01(i, 0, seed) - 0.5) * 2)
        hh = 3 + int(hash01(i, 1, seed) * 3)
        cw = 4 + (1 if hash01(i, 2, seed) < 0.5 else 0)
        for y in range(sp.fy - hh, sp.fy + 1):
            sput(sp, x, y, 'plaster', 4)
            sput(sp, x + 1, y, 'plaster', 2)
        ramp = 'berry_warm' if kind == 'agaric' else 'timber_warm'
        cy = sp.fy - hh - 1
        for dy, half in ((-1, cw // 2 - 1), (0, cw // 2), (1, cw // 2)):
            for dx in range(-half, half + 2):
                k = 4 if dx < 0 and dy < 1 else 3 if dx <= 0 else 2
                if dy == 1:
                    k = 1
                sput(sp, x + dx, cy + dy, ramp, k)
        if kind == 'agaric':
            sput(sp, x - 1, cy, 'plaster', 5)
            sput(sp, x, cy, 'plaster', 4)
    sh = np.zeros(sp.m.shape, bool)
    sh[sp.fy:sp.fy + 1, 2:15] = True
    return sp, sh


def roots(p: Plot, x, y, seed=0, toward=None, n=3, reach=12):
    """Roots running out from a trunk's foot over the ground or across a path: two pixels
    thick, lit along the top, a dark underside and a pixel of shade below."""
    for i in range(n):
        if toward is None:
            a = (-0.5 + i / max(1, n - 1)) * 2.6 + (hash01(i, 0, seed) - 0.5) * 0.4
            dx, dy = math.sin(a), 0.35 + 0.2 * abs(math.cos(a))
        else:
            a = math.atan2(toward[1], toward[0]) + (hash01(i, 0, seed) - 0.5) * 1.1
            dx, dy = math.cos(a), math.sin(a)
        ln = int(reach * (0.6 + 0.6 * hash01(i, 1, seed)))
        bend = (hash01(i, 2, seed) - 0.5) * 0.08
        px, py = float(x), float(y)
        for s in range(ln):
            px += dx + bend * s * -dy
            py += dy * 0.7 + bend * s * dx
            xi, yi = int(round(px)), int(round(py))
            pput(p, xi, yi, 'timber', 4 if s < ln - 2 else 3)
            pput(p, xi, yi + 1, 'timber', 2)
            if 0 <= xi < p.w and 0 <= yi + 2 < p.h and not p.solid[yi + 2, xi]:
                p.step(rk._pt(p, xi, yi + 2), -1, lo=1)


# --- ground ---------------------------------------------------------------------------------
LEAVES = (((0, 0), (1, 0), (1, -1)), ((0, 0), (0, -1), (1, -1)), ((0, 0), (1, 0), (2, -1), (1, -1)),
          ((0, 0), (1, 0), (2, 0), (1, -1)), ((0, 0), (1, 0), (0, 1), (1, 1)))


FLOWER_FAMS = ('plaster', 'brass', 'berry', 'dusk', 'clay', 'sky')
TRI = (((0, 0), (1, 0), (0, -1)), ((0, 0), (1, 0), (1, -1)), ((0, 0), (1, 0)), ((0, 0), (0, -1)))


def drifts(p: Plot, m, seed, kinds, every=1400, n=(5, 15), r=(4, 8)):
    """Flowers gathered in drifts (Claude A's review: never confetti): about one drift per
    `every` px of the mask, each of n flowers (clusters of two or three pixels) within a
    radius r of its centre, all of one kind; kinds: (ramp, tone) each."""
    m = np.asarray(m, bool)
    for i, (x, y) in enumerate(rk._scatter(m, every, seed, 3)):
        ramp, tone = kinds[int(hash01(x, y, seed + 1) * len(kinds))]
        cnt = n[0] + int(hash01(x, y, seed + 2) * (n[1] - n[0] + 1))
        rad = r[0] + hash01(x, y, seed + 3) * (r[1] - r[0])
        for j in range(cnt):
            a = hash01(j, i, seed + 4) * 6.283
            d = math.sqrt(hash01(j, i, seed + 5)) * rad
            fx, fy = int(round(x + math.cos(a) * d)), int(round(y + math.sin(a) * d * 0.7))
            shp = TRI[int(hash01(j, i, seed + 6) * len(TRI))]
            for dx, dy in shp:
                px, py = fx + dx, fy + dy
                if 0 <= px < p.w and 0 <= py < p.h and m[py, px] and not p.solid[py, px]:
                    p.f[py, px], p.t[py, px] = IDX[ramp], tone if dy == 0 else max(1, tone - 1)


def calm(p: Plot, m, share=0.6, seed=0):
    """Cut lone flower flecks on open ground by about `share` (Claude A's review: the meadow
    read as confetti): small flower clusters outside the denser drifts go back to the ground
    around them."""
    m = np.asarray(m, bool) & ~p.solid
    fl = m & np.isin(FAMILY[p.f], [IDX[k] for k in FLOWER_FAMS])
    dense = rk.dilate(fl, 3)
    near = np.zeros(m.shape, np.int16)
    for dx in range(-4, 5, 2):
        for dy in range(-4, 5, 2):
            near += shift(fl, dx, dy, False)
    lone = fl & (near < 6) & (hash01(p.x // 2, p.y // 2, seed + 70) < share)
    for _ in range(3):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0)):
            src_f, src_t = shift(p.f, dx, dy, -1), shift(p.t, dx, dy, 0)
            ok = lone & (src_f >= 0) & ~np.isin(FAMILY[np.clip(src_f, 0, None)], [IDX[k] for k in FLOWER_FAMS])
            p.f[ok], p.t[ok] = src_f[ok], src_t[ok]
            lone &= ~ok
    del dense
    despeckle(p, m)


def meadow(p: Plot, m, seed=0, kind='hay'):
    """The river kit's hay meadow or pasture, calmed for the forest's margins: lone flower
    flecks cut by about 60 % and flowers gathered into drifts of 5 to 15."""
    m = np.asarray(m, bool)
    (rk.hay_meadow if kind == 'hay' else lambda q, mm, sd: rk.pasture(q, mm, sd, tussocks=False))(p, m, seed)
    calm(p, m, 0.6, seed)
    drifts(p, m, seed + 5, (('brass', 5), ('plaster', 5), ('berry', 4), ('dusk', 4)), every=1600, n=(5, 12))


def litter(p: Plot, m, seed=0, shade=0, bluebells=True):
    """The broadleaf floor: earth under last year's leaves (small clusters in brown, rust and
    gold), moss in soft patches, twigs, sun flecks where the canopy opens, bluebells and wood
    anemones in drifts. Calm: body tone 3, patches one tone off. `shade` steps it down."""
    m = np.asarray(m, bool)
    rk.base(p, m, 'earth', seed, scale=7, warm=0.45, cool=0.8)
    moss = m & (fbm(p.x, p.y, 13, seed + 1) > 0.62)
    rk.base(p, moss, 'leaf', seed + 2, scale=5)
    bare = m & ~moss
    stamp(p, bare, 0.026, seed + 3, LEAVES, ramp='timber_warm', tone=3, same_family=False)
    stamp(p, bare, 0.022, seed + 4, LEAVES, ramp='earth_warm', tone=4, same_family=False)
    stamp(p, bare, 0.018, seed + 5, LEAVES, ramp='earth_cool', tone=2, same_family=False)
    stamp(p, bare & (fbm(p.x, p.y, 15, seed + 18) > 0.55), 0.02, seed + 6, LEAVES, ramp='brass_cool', tone=3,
          same_family=False)                              # fallen leaves gathered, not sprinkled
    # moss creeps out of its patches in clusters, so no patch has a clean edge
    fringe = dilate(moss, 2) & ~moss & m
    stamp(p, fringe, 0.18, seed + 17, SMALL, ramp='leaf', tone=3, same_family=False)
    stamp(p, moss, 0.08, seed + 7, SMALL[3:], swap='mix')
    stamp(p, moss, 0.03, seed + 8, SMALL[3:], dt=1)
    tw = bare & (hash01(p.x, p.y, seed + 9) < 0.004)
    for dx, dy in ((0, 0), (1, 0), (2, 1), (3, 1)):
        t = shift(tw, dx, dy, False) & m
        p.f[t], p.t[t] = IDX['timber_cool'], 2
    if bluebells:                       # bluebells and wood anemones in drifts, not flecks
        drifts(p, m, seed + 11, (('dusk_warm', 4), ('dusk_warm', 4), ('plaster', 4)), every=1800, n=(6, 14))
    if shade:
        p.step(m, -shade, lo=1)
    sun = m & (fbm(p.x, p.y, 8, seed + 15) > 0.72)
    p.step(sun, 1, hi=4)
    despeckle(p, m)
    unspeck(p, m, 2)


def needles(p: Plot, m, seed=0, shade=0):
    """The conifer floor: a rust carpet of fallen needles in short crossing strokes, cones
    lit on their tops, moss cushions and the odd tuft of wood sorrel."""
    m = np.asarray(m, bool)
    rk.base(p, m, 'timber', seed, scale=6, warm=0.45, cool=0.8)
    p.f[m & (fbm(p.x, p.y, 9, seed + 1) > 0.62)] = IDX['clay_cool']
    strokes = (((0, 0), (1, 1)), ((0, 0), (1, -1)), ((0, 0), (1, 0), (2, 1)), ((0, 0), (1, 0), (2, -1)))
    s2 = (((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (2, 0)))
    stamp(p, m, 0.10, seed + 2, s2, dt=1)
    stamp(p, m, 0.07, seed + 3, s2, dt=-1)
    stamp(p, m, 0.05, seed + 4, strokes[2:], swap='mix')
    moss = m & (fbm(p.x, p.y, 11, seed + 5) > 0.68)
    rk.base(p, moss, 'leaf', seed + 6, scale=4, warm=0.1, cool=0.4)
    stamp(p, moss, 0.06, seed + 7, SMALL[:4], dt=1)
    cones = m & ~moss & (hash01(p.x, p.y, seed + 8) < 0.003)
    for dx, dy, k in ((0, 0, 3), (1, 0, 2), (0, 1, 2), (1, 1, 1)):
        t = shift(cones, dx, dy, False) & m
        p.f[t], p.t[t] = IDX['timber'], k
    sorrel = m & (fbm(p.x, p.y, 17, seed + 9) > 0.72) & ~moss
    stamp(p, sorrel, 0.05, seed + 10, DOMINOES, ramp='grass', tone=4, same_family=False)
    if shade:
        p.step(m, -shade, lo=1)
    despeckle(p, m)


GLADE_FLOWERS = (('plaster', 5, 0.4), ('brass', 5, 0.3), ('berry_warm', 4, 0.2), ('dusk', 4, 0.1))


def glade(p: Plot, m, seed=0):
    """A sunny clearing: short grass lighter and warmer than the meadow's, daisies,
    buttercups, red campion and bugle in drifts, the odd tuft; the floor of the wood creeping
    in at its edges under the canopy."""
    m = np.asarray(m, bool)
    rk.base(p, m, 'grass', seed, scale=6, warm=0.35, cool=0.75)
    rk.texture(p, m, seed + 1, swaps=0.13, ups=0.02, downs=0.015)
    stamp(p, m, 0.03, seed + 2, BLADES, dt=1)
    despeckle(p, m)
    drifts(p, m, seed + 3, [(r, t) for r, t, _s in GLADE_FLOWERS], every=900, n=(6, 15))


def _dist(mask, cap=24):
    """Approximate distance (4-neighbour steps) from each pixel to the mask."""
    d = np.full(mask.shape, cap, np.int16)
    cur = np.asarray(mask, bool).copy()
    d[cur] = 0
    for i in range(1, cap):
        nxt = dilate(cur, 1)
        d[nxt & ~cur] = i
        cur = nxt
    return d


def centreline(p: Plot, pts, step=0.7):
    line = np.zeros(p.f.shape, bool)
    cs = rk.spline(pts, step)
    for (x, y) in cs:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < p.w and 0 <= yi < p.h:
            line[yi, xi] = True
    return line, cs


def path(p: Plot, pts, width=20, seed=0, stones=True, puddle=True):
    """A woodland path (16 to 24 wide): worn earth, lightest along the middle where feet go,
    its edges wandering and drifted with leaves, moss creeping in, stones lit on their tops,
    a puddle in a hollow. Returns (mask, centre points)."""
    line, cs = centreline(p, pts)
    d = _dist(line, width)
    wob = (fbm(p.x, p.y, 11, seed) - 0.5) * 5 + (fbm(p.x, p.y, 4, seed + 1) - 0.5) * 2
    m = d + wob < width / 2
    m = dilate(erode(m, 1), 1)
    rk.base(p, m, 'path', seed + 2, scale=6, warm=0.4, cool=0.8)
    mid = m & (d + wob * 0.5 < width * 0.22)
    p.step(mid & (fbm(p.x, p.y, 7, seed + 3) > 0.35), 1, hi=4)
    rim = m & ~erode(m, 3)
    p.step(rim & (hash01(p.x // 2, p.y // 2, seed + 4) < 0.5), -1, lo=1)
    stamp(p, rim | (m & (d > width * 0.3)), 0.12, seed + 5, LEAVES, ramp='timber_warm', tone=3, same_family=False)
    stamp(p, rim, 0.06, seed + 6, LEAVES, ramp='brass_cool', tone=3, same_family=False)
    rk.texture(p, m, seed + 7, swaps=0.12, ups=0.02, downs=0.03)
    stamp(p, m & ~mid, 0.03, seed + 11, SMALL[:3], ramp='earth_cool', tone=2, same_family=False)
    if stones:
        for i, (x, y) in enumerate(rk._scatter(m & ~mid, 900, seed + 8, 2)):
            w = 2 + int(hash01(x, y, seed) * 2)
            for dx in range(w):
                pput(p, x + dx, y, 'stone_warm', 4 if dx == 0 else 3)
                pput(p, x + dx, y + 1, 'stone', 2)
            pput(p, x + w, y + 1, 'path', 1)
            pput(p, x + 1, y + 2, 'path', 2)
    if puddle:
        best = None
        for i in range(len(cs) // 3, len(cs) * 2 // 3, 7):
            x, y = int(cs[i][0]), int(cs[i][1])
            if 4 < x < p.w - 10 and 4 < y < p.h - 6:
                n = fbm(np.array(x), np.array(y), 9, seed + 9)
                if best is None or n < best[0]:
                    best = (n, x, y)
        if best:
            _, x, y = best
            pm = blob(x, y, 7, 3, p.f.shape, seed, 0.2) & m
            p.put(pm, 'water_cool', 2)
            p.put(pm & ~shift(pm, 0, 1, False), 'water', 1)
            p.put(pm & ~shift(pm, 0, -1, False) & ~shift(pm, 0, 1, False), 'sky_cool', 4)
            gl = pm & (hash01(p.x, p.y, seed + 10) < 0.15)
            p.put(gl & shift(pm, 1, 0, False), 'sky', 4)
    despeckle(p, m)
    return m, cs


# --- masses: many trees ---------------------------------------------------------------------
WOODLAND = (('oak', 4), ('beech', 3), ('hornbeam', 2), ('ash', 2), ('holly', 1))
MIXED = (('oak', 3), ('spruce', 2), ('beech', 2), ('pine', 1), ('hornbeam', 1), ('holly', 1))
CONIFERS = (('spruce', 4), ('fir', 2), ('pine', 2), ('birch', 1))
OLD = (('veteran', 3), ('spruce', 2), ('oak', 2), ('beech', 1), ('holly', 1))


def make(kind, seed=0, scale=1.0):
    """Any standing thing of the kit by name: (sprite, shadow, block or None)."""
    if kind in BROADLEAF:
        sp, sh, meta = broadleaf(kind, seed, scale)
    elif kind in CONIFER:
        sp, sh, meta = conifer(kind, seed, scale)
    elif kind == 'veteran':
        sp, sh, meta = veteran(seed, scale)
    elif kind == 'birch':
        sp, sh = rk.birch(seed)
        return sp, sh, None
    elif kind.startswith('young:'):
        sp, sh, meta = young(kind[6:], seed)
    elif kind == 'bramble':
        sp, sh = bramble(seed, 28 + int(hash01(seed, 0, 1) * 16))
        return sp, sh, sp.m & (sp.y > sp.fy - 6)
    elif kind == 'log':
        return log(seed, 34 + int(hash01(seed, 0, 2) * 26))
    elif kind == 'stump':
        sp, sh = stump(seed)
        return sp, sh, sp.m & (sp.y > sp.fy - 5)
    elif kind in ('hawthorn', 'hazel'):
        sp, sh = rk.shrub(kind, seed)
        return sp, sh, None
    else:
        fn = {'bracken': lambda s: bracken(s), 'fern': lambda s: fern('male', s), 'hart': lambda s: fern('hart', s),
              'foxglove': foxglove, 'agaric': lambda s: mushrooms('agaric', s), 'brown': lambda s: mushrooms('brown', s)}[kind]
        sp, sh = fn(seed)
        return sp, sh, np.zeros(sp.m.shape, bool)       # low plants: walked through
    x0, tw = meta['trunk']
    b = np.zeros(sp.m.shape, bool)
    b[sp.fy - 2:sp.fy + 1, max(0, x0 - 1):x0 + tw + 1] = True
    return sp, sh, b


def pick(mix, x, y, seed):
    tot = sum(w for _k, w in mix)
    r = hash01(x, y, seed) * tot
    for k, w in mix:
        r -= w
        if r < 0:
            return k
    return mix[-1][0]


class Placed:
    __slots__ = ('x', 'y', 'kind', 'seed', 'scale', 'front', 'dim', 'cool')

    def __init__(self, x, y, kind, seed, scale=1.0, dim=0, cool=False):
        self.x, self.y, self.kind, self.seed, self.scale, self.front = x, y, kind, seed, scale, False
        self.dim, self.cool = dim, cool


def plan(m, mix, every, seed, density=None, clear=None, scale=(0.9, 1.15)):
    """Feet for things over a mask, about one per `every` px (fewer where `density` is low),
    none in `clear`; each with a kind from `mix`."""
    out = []
    for i, (x, y) in enumerate(rk._scatter(m, every, seed, 2)):
        if density is not None and hash01(x, y, seed + 1) > density[y, x]:
            continue
        if clear is not None and clear[y, x]:
            continue
        k = pick(mix, x, y, seed + 2)
        sc = scale[0] + (scale[1] - scale[0]) * hash01(x, y, seed + 3)
        out.append(Placed(x, y, k, seed * 101 + i, sc))
    return out


TALL = set(BROADLEAF) | set(CONIFER) | {'veteran', 'birch'}


def mark_front(trees, reach=40, half=22):
    """A tree is on the front when no other tree stands just south of it (its trunk shows)."""
    tall = [t for t in trees if t.kind in TALL or t.kind.startswith('young:')]
    for t in tall:
        t.front = not any(0 < o.y - t.y < reach and abs(o.x - t.x) < half for o in tall if o is not t)
    return [t for t in tall if t.front]


def no_runs(trees, mix, most=3):
    """Benchmark check 9: a tree wall mixes species; never more than `most` of one kind side
    by side along its front. Changes the kind of the tree that would make a longer run."""
    front = sorted(mark_front(trees), key=lambda t: t.x)
    kinds = [k for k, _w in mix]
    run = 0
    for i, t in enumerate(front):
        run = run + 1 if i and front[i - 1].kind == t.kind else 1
        if run > most:
            t.kind = next(k for k in kinds[1:] + kinds if k != t.kind)
            run = 1
    return front


def longest_run(trees):
    front = sorted(mark_front(trees), key=lambda t: t.x)
    best = run = 0
    for i, t in enumerate(front):
        run = run + 1 if i and front[i - 1].kind == t.kind else 1
        best = max(best, run)
    return best


def underside(p: Plot, m, seed=0):
    """The ground under a closed canopy, seen only through gaps between crowns: the canopy's
    own dark underside, cool and deep, with a few dim leaves."""
    m = np.asarray(m, bool)
    p.put(m, 'leaf_cool', 1)
    stamp(p, m, 0.10, seed, SMALL, swap='mix')
    stamp(p, m, 0.05, seed + 1, SMALL[:4], tone=0, same_family=True)
    stamp(p, m, 0.04, seed + 2, LEAVES, ramp='earth_cool', tone=1, same_family=False)
    despeckle(p, m)


def woodland(p: Plot, m, seed=0, mix=WOODLAND, every=900, clear=None, front_band=14, density=None):
    """A canopy of many trees over the feet mask `m`: the floor under it goes to the dark
    underside (it shows only between crowns), trees from the mix, never more than three of a
    kind along the front, the interior blocked to walkers and the front band open between
    its trunks. Returns the planned trees (draw them with `draw`, sorted with everything
    else that stands)."""
    m = np.asarray(m, bool)
    front = m & ~shift(m, 0, -front_band, False)
    closed = m & ~front if clear is None else m & ~front & ~clear
    underside(p, closed, seed + 5)
    p.walk &= ~closed
    # the crowns' shadow on the open floor along the front: dappled pools, not one dark band
    below = (front | (shift(m, 0, 12, False) & ~m)) & ~closed & ~p.solid & ~p.wet
    pools = below & (fbm(p.x, p.y, 7, seed + 11) > 0.46)
    p.step(pools, -1, lo=1)
    p.step(pools & (fbm(p.x, p.y, 7, seed + 11) > 0.62) & front, -1, lo=1)
    trees = plan(m, mix, every, seed, density=density, clear=clear)
    no_runs(trees, mix)
    # deeper in the wood the crowns stand in each other's shade: a tone down, and cooler
    deep = np.zeros(m.shape, np.int16)              # how far the wood runs on south of here
    cur = m.copy()
    for d in range(4, 100, 4):
        cur = cur & shift(m, 0, -d, False)
        deep += cur
    for t in trees:
        if deep[t.y, t.x] * 4 > 44 and hash01(t.x, t.y, seed + 9) < 0.7:
            t.dim = max(t.dim, 1)
        if deep[t.y, t.x] * 4 > 80:
            t.dim = 1
    return trees


def draw(p: Plot, things):
    """Set everything that stands, north to south, each with its cast shadow and outline."""
    leafy = np.array([FAMILY[i] in (IDX['leaf'], IDX['grass']) for i in range(len(FAMILY))])
    for t in sorted(things, key=lambda q: (q.y, q.x)):
        sp, sh, b = make(t.kind, t.seed, t.scale)
        if t.dim:
            lf = sp.m & leafy[sp.f] & (sp.t < EDGE_T)
            if t.dim:                   # most clumps a tone down, so the crown sits in shade
                dm = lf & (hash01(sp.x // 3, sp.y // 3, t.seed + 7) < 0.6) & (sp.t > 1)
                sp.t[dm] -= t.dim
        paste(p, sp, t.x, t.y, shadow=sh, block=b)


def corridor(m, up=68, half=20):
    """Where a tree's foot would put its crown over `m` (a path, a glade, a face): feet up
    to `up` px south of it and about `half` px to either side. Plant nothing there, so the
    ground stays seen between the trunks."""
    m = np.asarray(m, bool)
    wide = dilate(m, half)
    out = dilate(m, 8)
    for d in range(8, up + 1, 4):
        out |= shift(wide, 0, d, False)
    return out


# --- the forest's edge ----------------------------------------------------------------------
def edge(p: Plot, m, t, seed=60, mix=WOODLAND, floor=None, clear=None, low_clear=None):
    """A forest edge fraying into the meadow over a band, `t` 0 (open meadow) to 1 (the
    wood). Its line is warped at two scales so it never runs straight; in front of it lie tall
    herbs and bramble, then scrub (hawthorn, hazel, bracken, foxgloves) and outlying trees and
    saplings standing out in the meadow; behind it the canopy, whose shade turns the floor to
    leaf litter. Returns (things to draw, canopy feet mask, wood floor mask)."""
    m = np.asarray(m, bool)
    v = t + 0.34 * (fbm(p.x, p.y, 52, seed) - 0.5) + 0.14 * (fbm(p.x, p.y, 13, seed + 1) - 0.5)
    canopy = m & (v > 0.66)
    snap = (p.f.copy(), p.t.copy())

    def pa(q, mm):
        q.f[:], q.t[:] = snap

    def pb(q, mm):
        (floor or litter)(q, mm, seed + 2)
    wood = rk.blend(p, m, np.clip((v - 0.42) / 0.26, 0, 1), pa, pb, seed + 3, warp=0.25, outliers=0.12)
    herbs = m & (v > 0.3) & (v < 0.6) & ~wood & (fbm(p.x, p.y, 14, seed + 4) > 0.42)
    meadow(p, herbs, seed + 5)
    things = woodland(p, canopy, seed + 6, mix, clear=clear)
    band = m & (v > 0.36) & (v <= 0.68) & ~canopy
    d = np.clip(1 - np.abs(v - 0.55) * 4, 0, 1)
    things += plan(band, (('bramble', 3), ('hawthorn', 2), ('hazel', 2), ('bracken', 3), ('foxglove', 1)),
                   520, seed + 7, density=d, clear=low_clear)
    things += plan(m & (v > 0.24) & (v < 0.62) & ~canopy,
                   (('young:oak', 2), ('young:beech', 1), ('young:spruce', 1), ('oak', 1), ('hornbeam', 1),
                    ('birch', 1)), 3600, seed + 8, density=np.clip(1 - np.abs(v - 0.45) * 3.5, 0, 1), scale=(0.7, 1.0),
                   clear=clear)
    things += plan(m & (v > 0.6) & (v < 0.8), (('fern', 3), ('bracken', 2), ('brown', 1), ('hart', 1)), 380, seed + 9,
                   clear=low_clear)
    return things, canopy, wood


# --- slopes on the soft grid ----------------------------------------------------------------
def smooth(T, seed=0, round_r=6, wob=1.5):
    """Round a tier map's corners and let its edges wander a pixel or two (never a ruled
    line), each level kept inside the one below so two drops stay one edge."""
    n = (fbm(*np.mgrid[0:T.shape[0], 0:T.shape[1]][::-1], 9, seed) - 0.5) * 2 * wob
    top = int(T.max())
    masks = {}
    for k in range(top, 0, -1):
        mk = T >= k
        r = max(1, round_r // 2)
        mk = erode(dilate(mk, r), r)
        mk = dilate(erode(mk, r), r)
        din, dout = rk._edge_dist(mk, 4), rk._edge_dist(~mk, 4)
        mk = (mk & ~((din <= 2) & (n < -(din - 0.5)))) | (~mk & (dout <= 2) & (n > dout - 0.5))
        if k < top:
            mk |= masks[k + 1]
        masks[k] = mk
    out = np.zeros_like(T)
    for k in range(1, top + 1):
        out[masks[k]] = k
    return out


class Tiers:
    """Where each tier's top is seen and where its south face hangs (the soft grid: faces on
    south edges only, FACE px a level, carved out of the ground below), and its west- and
    east-facing side bands (BAND px, inside the higher tier)."""

    def __init__(self, T, F=FACE):
        self.T = np.asarray(T, np.int8)
        self.F = F
        h, w = self.T.shape
        self.face = np.zeros((h, w), bool)
        self.depth = np.zeros((h, w), np.int16)
        self.fh = np.zeros((h, w), np.int16)
        self.kf = np.zeros((h, w), np.int8)
        for k in range(int(self.T.max()), 0, -1):
            below = shift(self.T, 0, -1, 99)
            rim = (self.T == k) & (below < k) & ~self.face
            fhk = np.where(rim, (k - np.minimum(below, k)) * F, 0).astype(np.int16)
            for d in range(1, k * F + 1):
                rd, hd = shift(rim, 0, d, False), shift(fhk, 0, d, 0)
                c = rd & (hd >= d) & ~self.face & (self.T < k)
                self.face |= c
                self.kf[c], self.depth[c], self.fh[c] = k, d - 1, hd[c]
        self.rim = (self.T >= 1) & shift(self.face, 0, -1, False) & ~self.face
        top = ~self.face
        self.west = np.zeros((h, w), bool)
        self.east = np.zeros((h, w), bool)
        for d in range(1, BAND + 1):
            self.west |= top & (shift(self.T, d, 0, 99) < self.T) & ~shift(self.face, d, 0, False)
            self.east |= top & (shift(self.T, -d, 0, 99) < self.T) & ~shift(self.face, -d, 0, False)
        # a face's ends are side bands too, so the face wraps round into the light or the
        # shade: where a column a few px to the side holds no face at all
        col = self.face.copy()
        for d in range(1, F + 2):
            col |= shift(self.face, 0, d, False) | shift(self.face, 0, -d, False)
        for d in range(1, BAND + 1):
            self.west |= self.face & ~shift(col, d, 0, True)
            self.east |= self.face & ~shift(col, -d, 0, True)
        self.east &= ~self.west

    def top(self, k):
        return (self.T == k) & ~self.face & ~self.west & ~self.east


def bank(p: Plot, L: Tiers, seed=70, steps=()):
    """A woodland bank in every south face: packed clods of earth (about 13 x 9) lit on their
    upper left with dark crevices between, mossy clods and the odd stone, roots hanging from
    the lip in its top 6 px, a lip of moss and litter overhanging it with its shadow under it,
    a damp dark foot. Faces block walkers; `steps` are cut later by `log_steps`."""
    fc = L.face
    if not fc.any():
        return
    inside, du, dv, cid = rk.clumps(p, fc, 7, 3.6, 5.6, seed)
    lv = -du - dv
    pick_ = hash01(cid, 0, seed + 1)
    fam = np.where(pick_ < 0.33, IDX['earth_warm'], np.where(pick_ < 0.75, IDX['earth'], IDX['earth_cool']))
    p.f[fc] = fam[fc]
    p.t[fc] = np.where(inside, np.where(lv > 0.6, 4, np.where(lv > -0.25, 3, 2)), 1)[fc]
    up = fc & (L.depth < L.fh * 0.5)
    mossy = up & inside & (hash01(cid, 1, seed + 2) < 0.22)
    p.f[mossy] = IDX['leaf']
    stone = fc & inside & (hash01(cid, 2, seed + 3) > 0.9)
    p.f[stone] = IDX['stone_warm']
    # grit and small stones in the crevices, pale root ends, clusters of moss on the clods
    crev = fc & ~inside
    stamp(p, crev, 0.18, seed + 30, DOMINOES, ramp='stone', tone=3, same_family=False)
    stamp(p, fc & inside, 0.08, seed + 31, SMALL[:4], dt=-1)
    stamp(p, fc & inside & (lv > 0.2), 0.05, seed + 32, DOMINOES, swap='mix')
    stamp(p, up & inside, 0.05, seed + 33, SMALL[:3], ramp='leaf', tone=3, same_family=False)
    # under the lip: its shadow; at the foot: damp
    lipd = (hash01(p.x // 3, 0, seed + 4) * 2.6).astype(np.int16)
    lip = fc & (L.depth < lipd)
    p.put(lip, 'leaf', np.where(L.depth == 0, 4, 3))
    stamp(p, lip, 0.4, seed + 5, DOMINOES, swap='mix')
    under = fc & (L.depth == lipd)
    p.f[under], p.t[under] = IDX['earth'], EDGE_T
    shade = fc & (L.depth > lipd) & (L.depth <= lipd + 3)
    p.step(shade, -1, lo=1)
    foot = fc & (L.depth >= L.fh - 3)
    p.step(foot, -1, lo=1)
    # roots hanging from the lip, in its top 6 px
    cols = fc & (L.depth == lipd + 1) & (hash01(p.x, 3, seed + 6) < 0.07) & (hash01(p.x // 6, 5, seed + 9) < 0.6)
    ys, xs = np.nonzero(cols)
    for (x, y) in zip(xs, ys):
        ln = 3 + int(hash01(x, 4, seed) * 5)
        cur = x
        for s in range(ln):
            if hash01(x, s, seed + 7) < 0.25:
                cur += 1 if hash01(x, s, seed + 8) < 0.5 else -1
            if 0 <= cur < p.w and 0 <= y + s < p.h and fc[y + s, cur]:
                p.f[y + s, cur], p.t[y + s, cur] = IDX['timber_cool'], 3 if s < ln - 1 else 2
                if cur + 1 < p.w and fc[y + s, cur + 1]:
                    p.f[y + s, cur + 1], p.t[y + s, cur + 1] = IDX['timber_cool'], 1
    # buttresses: columns of the bank standing proud, lit on their west, the light catching
    # them; between them the face falls back into shade, so it never reads as flat bands
    wid = 15 + (hash01(p.x // 40, 2, seed + 39) * 12).astype(int)
    seg = (p.x + (hash01(p.y // 9, 0, seed + 40) * 3).astype(int)) // wid
    proud = fc & (hash01(seg, 1, seed + 41) < 0.45) & (L.depth > lipd + 1)
    p.step(proud & inside & (lv > -0.3), 1, hi=4)
    back = fc & ~proud & (L.depth > lipd + 1) & (L.depth < L.fh - 3)
    p.step(back & inside & (hash01(cid, 3, seed + 42) < 0.6), -1, lo=1)
    # fissures: dark vertical cracks between the buttresses, lit on their west lip
    edge_x = proud & ~shift(proud, 1, 0, False)                  # a buttress's west edge
    edge_x |= ~proud & fc & shift(proud, 1, 0, False)            # where one falls back east
    a = lipd + 2 + (hash01(p.x, 7, seed + 43) * 8).astype(int)            # each crack's top
    b = a + 5 + (hash01(p.x, 8, seed + 46) * 14).astype(int)               # and its foot
    ys, xs = np.nonzero(edge_x & (L.depth >= a) & (L.depth <= b) & (hash01(seg, 9, seed + 47) < 0.55))
    for (x, y) in zip(xs, ys):
        if L.depth[y, x] < L.fh[y, x] - 2:
            p.f[y, x], p.t[y, x] = IDX['earth_cool'], 0
            if x - 1 >= 0 and fc[y, x - 1]:
                p.f[y, x - 1], p.t[y, x - 1] = IDX['earth_warm'], 4
    # overhangs: where the lip juts out its shadow is deeper and longer
    jut = fc & (hash01(p.x // 7, 9, seed + 44) < 0.3) & (L.depth > lipd) & (L.depth <= lipd + 4)
    p.step(jut, -1, lo=0)
    # hanging plants: trails of ivy and moss from the lip, lit on their tops
    ys, xs = np.nonzero(fc & (L.depth == lipd + 1) & (hash01(p.x // 2, 11, seed + 45) < 0.05))
    for (x, y) in zip(xs, ys):
        ln = 4 + int(hash01(x, 12, seed) * 9)
        for s_ in range(ln):
            for dx in (0, 1):
                if 0 <= x + dx < p.w and 0 <= y + s_ < p.h and fc[y + s_, x + dx]:
                    p.f[y + s_, x + dx] = IDX['leaf_cool' if (s_ // 3) % 2 else 'leaf']
                    p.t[y + s_, x + dx] = (3 if dx == 0 else 2) if s_ < ln - 1 else 1
    p.walk &= ~fc


def side_bands(p: Plot, L: Tiers, seed=71):
    """The 5 px side bands: a column of clods, lit when the band faces west, in the two
    darkest tones when it faces east, with a dark line where it meets the ground below."""
    for band, lit in ((L.west, True), (L.east, False)):
        if not band.any():
            continue
        cl = (p.y + (hash01(p.x // 5, 0, seed) * 5).astype(int)) // 5
        r = hash01(cl, p.x // 5, seed + 1)
        p.f[band] = np.where(r < 0.5, IDX['earth'], IDX['earth_warm'])[band]
        lit_t = np.where((p.y + cl) % 5 == 0, 2, np.where(r < 0.3, 4, 3))
        dark_t = np.where((p.y + cl) % 5 == 0, 0, np.where(r < 0.5, 2, 1))
        p.t[band] = (lit_t if lit else dark_t)[band]
        moss = band & (hash01(p.x // 2, p.y // 3, seed + 2) < 0.18)
        p.f[moss] = IDX['leaf']
        outer = dilate(band, 1) & ~band & ~L.face & (L.T < np.maximum(shift(L.T, 1, 0, 0), shift(L.T, -1, 0, 0)))
        p.f[outer & ~p.solid] = IDX['earth']
        p.t[outer & ~p.solid] = EDGE_T
        p.walk &= ~band


def tier_shadows(p: Plot, L: Tiers, throw=8):
    """A tier's cast shadow on the ground below: thrown down and to the right, so the ground
    east of an east-facing band and under a face's foot steps down: 2 px two tones, 3 px one
    tone, 3 px one tone on the 2 x 2 checker (the atmospheric fade's dither)."""
    low = ~L.face & ~L.west & ~L.east
    src = L.east | L.face
    for d in range(1, throw + 1):
        reach = (shift(L.east, d, 0, False) | shift(L.face, 0, d, False) & ~L.face) & low & ~src & ~p.solid
        reach &= L.T < np.maximum(shift(L.T, d, 0, 0), shift(L.kf, 0, d, 0))
        if d <= 2:
            p.step(reach, -2, lo=0)
        elif d <= 5:
            p.step(reach, -1, lo=1)
        else:
            p.step(reach & (((p.x // 2) + (p.y // 2)) % 2 == 0), -1, lo=1)
        low &= ~reach


def log_steps(p: Plot, L: Tiers, x0, width=STAIR, seed=72):
    """A path climbing a face on log steps: 4 px cheeks of earth either side (the west lit,
    the east dark), and in the 40 px between them a log riser (lit along its top, its sawn
    end showing at the west cheek) then a 4 px earth tread, every 8 px down the face. Opens
    the face to walkers between the cheeks."""
    fc = L.face
    cols = (p.x >= x0 - 4) & (p.x < x0 + width + 4)
    st = fc & cols
    if not st.any():
        return st
    inner = st & (p.x >= x0) & (p.x < x0 + width)
    west = st & (p.x < x0)
    east = st & (p.x >= x0 + width)
    p.f[west] = IDX['earth_warm']
    p.t[west] = np.where(p.x == x0 - 4, 4, np.where(p.x == x0 - 1, 2, 3))[west]
    p.f[east] = IDX['earth_cool']
    p.t[east] = np.where(p.x == x0 + width + 3, 1, np.where(p.x == x0 + width, 2, 1))[east]
    ph = (L.depth - (hash01(0, 0, seed) * 2).astype(int)) % 8
    riser = inner & (ph < 4)
    tread = inner & (ph >= 4)
    p.f[riser] = IDX['timber']
    p.t[riser] = np.choose(np.clip(ph, 0, 3), [4, 3, 2, 1])[riser]
    grain = riser & (ph == 2) & (hash01(p.x // 3, p.y, seed + 1) < 0.4)
    p.f[grain] = IDX['timber_cool']
    end = riser & (p.x < x0 + 3)
    p.f[end] = IDX['sand_warm']
    p.t[end] = np.where(ph == 0, 4, 3)[end]
    rk.base(p, tread, 'path', seed + 2, scale=4)
    p.step(tread & (ph == 4), -1, lo=1)                          # each log's shadow on its tread
    stamp(p, tread, 0.08, seed + 3, LEAVES, ramp='timber_warm', tone=3, same_family=False)
    for (x, y) in ((x0 - 1, None), (x0 + width, None)):
        line = st & (p.x == x)
        p.f[line], p.t[line] = IDX['earth'], EDGE_T
    p.walk |= inner
    p.walk &= ~(west | east)
    return inner


# --- the old forest: the world's edge in three layers ---------------------------------------
# the layers of the forest beyond, near to far: (ramp, body tone, crown radius)
DISTANCE = (('leaf_cool', 2, 11), ('leaf_cool', 3, 9), ('slate_cool', 3, 7), ('slate', 4, 5))


def distance(p: Plot, m, t, t0, seed=0):
    """The forest beyond the wall, seen in haze: rows of distant crowns in four layers, each
    a silhouette of round tops lit on their upper left with a shaded underside, the layers
    stepping up in value and cooling from leaf to slate as they recede, the nearest at the
    wall. Nothing here is walked."""
    m = np.asarray(m, bool) & (t >= t0)
    if not m.any():
        return
    span = max(1e-3, 1 - t0)
    n = len(DISTANCE)
    ramp, tone, _r = DISTANCE[-1]
    p.put(m, ramp, tone)                                        # the farthest haze first
    for k in range(n - 1, -1, -1):                              # far to near, near on top
        ramp, tone, r = DISTANCE[k]
        lo = t0 + span * k / n
        zone = m & (t >= lo)
        pts = rk._scatter(zone, int((r * 1.5) ** 2), seed + 10 * k, 0)
        cover = np.zeros(m.shape, bool)
        lv = np.full(m.shape, -9.0)
        for i, (x, y) in enumerate(sorted(pts, key=lambda q: q[1])):
            rr = r * (0.75 + 0.5 * hash01(x, y, seed + k))
            x0, x1 = max(0, int(x - rr - 2)), min(p.w, int(x + rr + 3))
            y0, y1 = max(0, int(y - rr - 2)), min(p.h, int(y + rr * 2 + 3))
            gx, gy = p.x[y0:y1, x0:x1] + 0.5 - x, p.y[y0:y1, x0:x1] + 0.5 - y
            u, v = gx / rr, gy / rr
            blobm = (u * u + np.minimum(v, 0) ** 2 <= 1) & (v < 1.8)   # a round top on a body
            blobm &= m[y0:y1, x0:x1]
            cover[y0:y1, x0:x1] |= blobm
            lv[y0:y1, x0:x1] = np.where(blobm, -0.7 * u - 0.9 * v, lv[y0:y1, x0:x1])
        p.f[cover] = IDX[ramp]
        p.t[cover] = np.where(lv > 0.55, tone + 1, np.where(lv < -0.5, tone - 1, tone))[cover]
        rimm = cover & ~shift(cover, 0, 1, False) & (lv > 0)
        p.t[rimm] = min(5, tone + 1)
    despeckle(p, m)
    p.walk &= ~m


def old_forest(p: Plot, m, t, seed=80, fade=0.25, wall=0.5):
    """The old forest as the world's edge, `t` 0 (the walked side) to 1 (beyond): the fade,
    walkable, with bramble, fallen trees, stumps, ferns and saplings thickening outward; the
    wall of old trees (giants, spruce, oak, beech, holly) that nobody walks through; and the
    forest beyond in haze, drawn here as layers of distant crowns. Returns the things to draw
    in front of it."""
    m = np.asarray(m, bool)
    # the layers' boundaries wander at two scales: never a ruled line
    t = np.clip(t + 0.34 * (fbm(p.x, p.y, 40, seed + 30) - 0.5) + 0.1 * (fbm(p.x, p.y, 11, seed + 31) - 0.5), 0, 1)
    t = np.where(m, t, 0)
    f_m = m & (t < fade)
    w_m = m & (t >= fade) & (t < wall)
    b_m = m & (t >= wall)
    litter(p, m & (t < wall + 0.05), seed, shade=0)
    p.step(m & (t > fade * 0.5) & (t < wall + 0.05), -1, lo=1)
    distance(p, b_m, t, wall, seed + 1)
    things = woodland(p, w_m, seed + 2, OLD, every=640, front_band=10)
    for q in things:
        q.dim = 1 if hash01(q.x, q.y, seed + 5) < 0.6 and q.kind != 'veteran' else 0
    dens = np.clip(t / fade, 0, 1)
    clump = (fbm(p.x, p.y, 26, seed + 6) > 0.5).astype(float)     # thicket in clumps, not rows
    things += plan(f_m, (('bramble', 4), ('log', 2), ('stump', 1), ('young:holly', 1), ('young:spruce', 1)),
                   900, seed + 3, density=(0.15 + 0.85 * dens) * (0.25 + 0.75 * clump))
    things += plan(f_m, (('fern', 3), ('bracken', 3), ('hart', 1), ('brown', 1), ('agaric', 1)), 260, seed + 4,
                   density=0.3 + 0.7 * dens)
    p.layer_t = t                         # the wandering layers, for checks
    return things


def strip(w=320, h=576, seed=90):
    """The transition from the meadow to the woodland to the old forest, south to north on
    one phone screen: hay meadow; the edge fraying out of it with scrub and outlying trees;
    a belt of woodland, its trunks along one front line; the old forest's walkable fade in
    the light between; its wall of old trees, trunks along their own line; and the forest
    beyond as layers of distant crowns."""
    p = Plot(w, h)
    every = np.ones((h, w), bool)
    meadow(p, every, seed)
    t1 = np.clip((470 - p.y - 10 * np.sin(p.x / 37.0)) / 120.0, 0, 1)
    belt = every & (p.y > 330 + 8 * np.sin(p.x / 43.0))         # the woodland's feet stop here
    t2 = np.clip((300 - p.y - 10 * np.sin(p.x / 29.0 + 1)) / 300.0, 0, 1)
    things, canopy, wood = edge(p, belt & (t2 <= 0), t1, seed + 1)
    litter(p, every & ~belt & (t2 <= 0) & ~wood, seed + 3)
    things += old_forest(p, every & (t2 > 0), t2, seed + 2)
    t2 = p.layer_t
    draw(p, things)
    despeckle(p, ~p.solid)
    return p, {'t_edge': t1, 't_old': t2, 'canopy': canopy, 'things': things}


def organic_tier(W, H, seed=0, cell=8):
    """The sample's upper wood as a tier on the 8 px grid with an organic outline (Claude A,
    to-all-kits-organic: curving, lobed, with spurs and bays, snapped to the grid only as
    stepped curves; never a straight face across a screen): a rim that wanders at two
    scales, a spur pushing south into the lower wood in the east, a bay cut back in the west
    where the bank turns, and its west end lobed."""
    cols, rows = W // cell, H // cell
    gy, gx = np.mgrid[0:rows, 0:cols]
    px, py = gx * cell + cell / 2, gy * cell + cell / 2
    rim = 146 + 26 * (fbm(px, np.zeros_like(px), 120, seed + 60) - 0.5) * 2 + 9 * np.sin(px / 47.0 + 0.7)
    rim = rim + 44 * np.exp(-((px - 540) / 46.0) ** 2)          # a spur running south
    rim = rim - 34 * np.exp(-((px - 196) / 40.0) ** 2)          # a bay cut back
    west = 84 + 22 * (fbm(np.zeros_like(py), py, 60, seed + 61) - 0.5) * 2
    T = ((py < rim) & (px > west)).astype(np.int8)
    return np.kron(T, np.ones((cell, cell), np.int8))[:H, :W]


# --- the sample: a woodland path from a meadow edge into a glade and up a slope ------------
SAMPLE_W, SAMPLE_H = 640, 576
PATH = [(128, 600), (150, 540), (196, 478), (238, 420), (262, 360), (290, 300), (330, 262), (368, 226),
        (384, 196), (388, 150), (380, 110), (352, 60), (336, -12)]
GLADE = (322, 252, 104, 58)
STEPS_X = 368


def sample(seed=1):
    """A woodland path, 640 x 576 (two phone screens wide, one tall): it leaves a hay meadow
    in the south through the fraying edge of the wood (scrub, outlying trees), runs under the
    canopy over roots and leaf litter, opens into a sunny glade at the foot of a wooded bank
    (a tier one level up, its earth face 32 px with side bands where it ends in the west), climbs
    the bank on log steps into the upper wood of oak, beech, pine and spruce. (The old
    forest's border, which needs a screen of its own to stand in three layers, is `strip()`.)"""
    W, H = SAMPLE_W, SAMPLE_H
    p = Plot(W, H)
    every = np.ones((H, W), bool)
    # the tier: the upper wood north of a wandering rim, ending in the west
    T0 = organic_tier(W, H, seed)
    L = Tiers(smooth(T0, seed, 6, 1.5))
    rim = np.full(p.f.shape, 0.0)
    for x in range(W):                       # the rim's row in each column (for planting)
        col = np.nonzero(L.T[:, x] >= 1)[0]
        rim[:, x] = col.max() if len(col) else -1
    upper = L.T >= 1
    # ground: the meadow in the south, the wood's floor, the glade, the upper wood's floor
    meadow_y = 452 + 22 * np.sin(p.x / 71.0) + 10 * np.sin(p.x / 23.0)
    meadow(p, every, seed + 2)
    t_edge = np.clip((meadow_y + 46 - p.y) / 150.0, 0, 1)
    gx, gy, grx, gry = GLADE
    gm, _u, _v = ellipse(p.f.shape, gx, gy, grx, gry, seed, 0.16, 5)
    gm &= ~upper & ~L.face
    t_old = np.zeros(p.f.shape)            # the old forest has its own strip (strip())
    old_m = upper & (t_old > 0)
    pm, cs = path(p.crop(0, 0, W, H), PATH, 20, seed + 3)                # where the path will run
    keep = corridor(pm, 56, 13) | corridor(gm, 56, 12) | corridor(L.face, 52, 8)
    # the lower wood: an edge fraying into the meadow, the glade cut out of it
    lower = ~upper & ~L.face
    things, canopy, wood = edge(p, lower & ~gm, t_edge, seed + 4, clear=keep, low_clear=dilate(pm, 4) | gm)
    glade(p, gm, seed + 5)
    soft = dilate(gm, 6) & ~gm & lower
    stamp(p, soft, 0.25, seed + 6, SMALL, ramp='grass', tone=3, same_family=False)
    # the upper wood: oak, beech and spruce, its floor of litter going to needles under spruce
    litter(p, upper & ~old_m, seed + 7, shade=0)
    needles(p, upper & ~old_m & (fbm(p.x, p.y, 60, seed + 8) > 0.55), seed + 9)
    up_trees = woodland(p, upper & ~old_m & (p.y < rim - 26), seed + 10, MIXED, every=820,
                        clear=corridor(pm, 56, 13) | dilate(old_m, 6))
    up_front = plan(upper & ~old_m & (p.y >= rim - 26) & (p.y < rim - 8),
                    (('fern', 3), ('bracken', 2), ('hart', 1), ('brown', 1)), 300, seed + 11, clear=dilate(pm, 3))
    # the path, then the bank and its steps
    pm, cs = path(p, PATH, 20, seed + 3)
    bank(p, L, seed + 12)
    side_bands(p, L, seed + 13)
    steps = log_steps(p, L, STEPS_X, STAIR, seed + 14)
    p.walk |= pm & ~L.face & ~L.west & ~L.east
    tier_shadows(p, L)
    # the glade's furniture: a fallen trunk, a stump with fungus, a ring of mushrooms,
    # foxgloves and ferns at its rim, bracken where the shade begins
    things += [Placed(268, 238, 'log', seed + 16), Placed(402, 284, 'stump', seed + 17),
               Placed(414, 289, 'brown', seed + 18), Placed(250, 278, 'agaric', seed + 19),
               Placed(240, 286, 'agaric', seed + 20)]
    rim_g = dilate(gm, 4) & ~gm & lower & ~dilate(pm, 4)
    things += plan(rim_g, (('foxglove', 2), ('fern', 2), ('bracken', 2), ('hart', 1)), 160, seed + 21)
    things += [Placed(x, y, 'hart', seed + 30 + i) for i, (x, y) in
               enumerate(rk._scatter(L.face & (L.depth > 10) & (L.depth < 22) & ~dilate(steps, 4), 900, seed + 22, 1))]
    # roots across the path from the trees beside it
    for i, q in enumerate(things + up_trees):
        if q.kind in TALL and dilate(pm, 14)[q.y, q.x] and not pm[q.y, q.x]:
            ys, xs = np.nonzero(pm[max(0, q.y - 20):q.y + 20, max(0, q.x - 20):q.x + 20])
            if len(xs):
                k = np.argmin((xs + max(0, q.x - 20) - q.x) ** 2 + (ys + max(0, q.y - 20) - q.y) ** 2)
                tx, ty = xs[k] + max(0, q.x - 20) - q.x, ys[k] + max(0, q.y - 20) - q.y
                roots(p, q.x, q.y, seed + i, toward=(tx, ty), n=2, reach=16)
    no_runs(things + up_trees, WOODLAND + (('spruce', 1), ('pine', 1)))   # one front across both woods
    draw(p, things + up_trees + up_front)
    p.walk |= steps
    despeckle(p, ~p.solid)
    return p, {'tiers': L, 'path': pm, 'glade': gm, 'steps': steps, 'old': old_m, 't_old': t_old,
               'things': things + up_trees, 'meadow_y': meadow_y, 'canopy': canopy}


# --- the kit sheet, the bar and the comparisons --------------------------------------------
def best_box(m, size=36, need=0.97):
    """The size x size box holding the most of mask `m` (at least `need` of it), or None."""
    h, w = m.shape
    if h < size or w < size:
        return None
    c = np.pad(np.cumsum(np.cumsum(m.astype(np.int32), 0), 1), ((1, 0), (1, 0)))
    s = c[size:, size:] - c[:-size, size:] - c[size:, :-size] + c[:-size, :-size]
    y, x = np.unravel_index(np.argmax(s), s.shape)
    if s[y, x] < need * size * size:
        return None
    return (int(x), int(y), int(x) + size, int(y) + size)


def _tile(w, h, ground='pasture', seed=0):
    p = Plot(w, h)
    m = np.ones((h, w), bool)
    {'pasture': lambda: meadow(p, m, seed, 'pasture'), 'litter': lambda: litter(p, m, seed),
     'hay': lambda: meadow(p, m, seed), 'needles': lambda: needles(p, m, seed)}[ground]()
    return p


def _leafy(p):
    return p.solid & np.isin(FAMILY[p.f], [IDX['leaf'], IDX['grass']]) & (p.t < EDGE_T)


def pieces():
    """Every piece on its own tile: (group, name, plot, bar box or None, bar kind)."""
    out = []
    # single trees
    for name, kind, sc in (('oak', 'oak', 1.0), ('beech', 'beech', 1.0), ('ash', 'ash', 1.0),
                           ('hornbeam', 'hornbeam', 1.0), ('holly (understorey)', 'holly', 1.0),
                           ('Norway spruce', 'spruce', 1.0), ('silver fir', 'fir', 1.0), ('Scots pine', 'pine', 1.0),
                           ('veteran (the old forest)', 'veteran', 1.0), ('young oak', 'young:oak', 1.0),
                           ('young spruce', 'young:spruce', 1.0)):
        sp, sh, b = make(kind, 7, sc)
        p = _tile(sp.w + 24, sp.h + 14, 'pasture', 3)
        paste(p, sp, p.w // 2, p.h - 8, shadow=sh, block=b)
        box = (best_box(_leafy(p), 34, 0.93) or best_box(_leafy(p), 34, 0.85)) if sp.w >= 38 else None
        out.append(('trees', name, p, box, 'tree'))
    # masses
    for name, mix, ground in (('broadleaf woodland: oak, beech, hornbeam, ash, holly', WOODLAND, 'litter'),
                              ('conifer forest: spruce, fir, pine, birch', CONIFERS, 'needles'),
                              ('mixed wood', MIXED, 'litter')):
        p = _tile(240, 210, ground, 5)
        m = (p.y > 60 + 8 * np.sin(p.x / 23.0)) & (p.y < 190 + 6 * np.sin(p.x / 17.0))
        draw(p, woodland(p, m, 11, mix, every=860))
        box = best_box(_leafy(p) & (p.y < 150), 48, 0.97) or best_box(_leafy(p), 36, 0.97) or best_box(_leafy(p), 34, 0.9)
        out.append(('masses', name, p, box, 'tree'))
    # undergrowth
    p = _tile(232, 84, 'litter', 6)
    row = (('bracken', 18), ('fern', 46), ('hart', 72), ('foxglove', 92), ('bracken', 116), ('fern', 146),
           ('brown', 168), ('bracken', 190), ('agaric', 214))
    for j, yy in enumerate((48, 64, 80)):
        for i, (k, x) in enumerate(row[j % 2:] + row[:j % 2]):
            if j and k in ('foxglove', 'agaric', 'brown'):
                continue
            sp, sh, b = make(k, 20 + i + 9 * j)
            paste(p, sp, x + 9 * j, yy, shadow=sh, block=b)
    despeckle(p, ~p.solid)
    out.append(('under', 'bracken, male fern, hart\'s tongue, foxglove, mushrooms', p, (8, 34, 224, 82), 'ground'))
    p = _tile(150, 64, 'litter', 7)
    sp, sh, b = make('bramble', 9)
    paste(p, sp, 44, 56, shadow=sh, block=b)
    sp, sh, b = make('bramble', 14)
    paste(p, sp, 108, 58, shadow=sh, block=b)
    out.append(('under', 'bramble thickets', p, best_box(p.solid & (p.f != IDX['plaster']), 34, 0.9), 'hedge'))
    p = _tile(150, 64, 'litter', 8)
    for k, x, y, sd in (('log', 60, 44, 3), ('stump', 120, 50, 4), ('agaric', 104, 56, 5), ('hart', 20, 56, 6)):
        sp, sh, b = make(k, sd)
        paste(p, sp, x, y, shadow=sh, block=b)
    out.append(('under', 'fallen trunk, stump, fly agaric', p, None, 'ground'))
    # ground
    for name, fn in (('leaf litter (bluebells, moss, sun flecks)', litter), ('conifer needles (cones, moss)', needles),
                     ('glade turf', glade)):
        p = Plot(96, 96)
        fn(p, np.ones((96, 96), bool), 3)
        out.append(('ground', name, p, (8, 8, 88, 88), 'ground'))
    p = _tile(200, 120, 'litter', 9)
    pm, _cs = path(p, [(-10, 90), (60, 70), (120, 66), (210, 30)], 20, 10)
    for i, (x, y) in enumerate(((50, 48), (150, 30), (100, 100))):
        roots(p, x, y, i, toward=(0, 1) if y < 60 else (0, -1), n=2, reach=16)
    out.append(('ground', 'woodland path: worn middle, leaf drifts, roots, stones, a puddle', p,
                best_box(pm & ~p.solid, 34, 0.5), 'ground'))
    # bands and places
    p = _tile(320, 240, 'hay', 12)
    t = np.clip((200 - p.y) / 150.0, 0, 1)
    things, canopy, wood = edge(p, np.ones(p.f.shape, bool), t, 13)
    draw(p, things)
    out.append(('bands', 'forest edge fraying into the meadow', p, (20, 186, 300, 236), 'ground'))
    p = _tile(320, 260, 'litter', 14)
    gm, _u, _v = ellipse(p.f.shape, 160, 170, 100, 56, 3, 0.16, 5)
    glade(p, gm, 15)
    tm = ~gm & ~corridor(gm, 50, 10)
    draw(p, woodland(p, tm, 16, WOODLAND, every=820) + [Placed(120, 170, 'log', 3), Placed(210, 190, 'stump', 4),
                                                         Placed(224, 196, 'brown', 5)] +
         plan(dilate(gm, 4) & ~gm, (('foxglove', 2), ('fern', 2), ('bracken', 1)), 200, 17))
    out.append(('bands', 'a glade', p, best_box(gm & ~p.solid, 40, 0.98), 'ground'))
    p = _tile(320, 200, 'litter', 18)
    T0 = ((p.y < 70 + 6 * np.sin(p.x / 29.0)) & (p.x > 30)).astype(np.int8)
    T0[:, 290:] = 0
    L = Tiers(smooth(T0, 3, 6, 1.5))
    bank(p, L, 19)
    side_bands(p, L, 20)
    log_steps(p, L, 150, STAIR, 21)
    tier_shadows(p, L)
    draw(p, woodland(p, (L.T >= 1) & (p.y < 44) & ~L.west & ~L.east, 22, MIXED, every=700) +
         [Placed(x, y, 'hart', 30 + i) for i, (x, y) in enumerate(rk._scatter(L.face & (L.depth > 10) & (L.depth < 22) &
                                                                                ((p.x < 140) | (p.x > 200)), 700, 23, 1))])
    out.append(('bands', 'wooded bank: earth face, roots, side bands, log steps', p,
                best_box(L.face & ~p.solid & ((p.x < 140) | (p.x > 200)), 34, 0.95), 'face'))
    p = _tile(320, 300, 'litter', 24)
    t = np.clip((300 - p.y) / 300.0, 0, 1)
    things = old_forest(p, np.ones(p.f.shape, bool), t, 25)
    draw(p, things)
    wall_box = best_box(_leafy(p) & (FAMILY[p.f] != IDX['slate']) & (t > 0.42) & (t < 0.66), 34, 0.95)
    out.append(('bands', 'the old forest: fade, wall, haze beyond', p, wall_box, 'tree'))
    return out


REF_FOR = {'tree': 'eastward-08-canopy', 'ground': 'eastward-37-lawn-flowers', 'hedge': 'eastward-17-bushes',
           'face': 'eastward-12-cliff-face'}
TONES_RULING = 0.85        # house-style.md 7, rulings: art drawn in ramps passes tones at 85 %


def judge(img, box, kind):
    """The detail bar for a box, under the house rulings (tones at 85 %, the rest in full)."""
    import detail_bar as db
    _ok, c, _lines = db.check_image(img, box, kind)
    ref = db.bar(kind)
    ok = (c['tones'] >= TONES_RULING * ref['tones'] and c['shapes'] >= db.TOLERANCE * ref['shapes']
          and c['dressing'] >= db.TOLERANCE * ref['dressing'] and c['isolated'] <= ref['isolated'] + db.ISOLATED_MARGIN
          and c['cluster'] >= db.CLUSTER_SHARE * ref['cluster'])
    return ok, c, ref


def bar_rows(items):
    rows = []
    for (group, name, p, box, kind) in items:
        if box is None:
            rows.append((name, kind, None, None, rk.lone_share(p)))
            continue
        ok, c, _ref = judge(p.image(), box, kind)
        rows.append((name, kind, ok, c, rk.lone_share(p)))
    return rows


GROUPS = (('trees', 'Trees: broadleaf, conifer, veteran, young'), ('masses', 'Masses: many trees, never one blob'),
          ('under', 'Undergrowth'), ('ground', 'Floors and the woodland path'),
          ('bands', 'Edges, glades, slopes and the old forest'))


def kit_sheet(items, rows, scale=2):
    """Every piece at `scale`, grouped, each labelled with its detail bar result."""
    import detail_bar as db
    pad, lab, maxw = 10, 28, 1500
    layout, y = [], 0
    for g, _title in GROUPS:
        y += 30
        x, rowh = pad, 0
        for it, r in zip(items, rows):
            if it[0] != g:
                continue
            w, h = it[2].w * scale, it[2].h * scale
            if x + w > maxw:
                x, y = pad, y + rowh + lab + pad
                rowh = 0
            layout.append((g, it, r, x, y))
            x += w + pad
            rowh = max(rowh, h)
        y += rowh + lab + pad
    sheet = Image.new('RGB', (maxw + pad, y + pad), (46, 40, 52))
    d = ImageDraw.Draw(sheet)
    seen = set()
    titles = dict(GROUPS)
    for (g, it, r, x, y0) in layout:
        if g not in seen:
            rk._label(sheet, titles[g], (pad, y0 - 22), (250, 214, 140))
            seen.add(g)
        img = it[2].image(scale)
        sheet.paste(img, (x, y0))
        box = it[3]
        if box:
            d.rectangle([x + box[0] * scale, y0 + box[1] * scale, x + box[2] * scale - 1, y0 + box[3] * scale - 1],
                        outline=(250, 214, 140))
        name, kind, ok, c, _lone = r
        if c:
            ref = db.bar(kind)
            sub = (f'{kind} t{c["tones"]:.0f}/{ref["tones"]:.0f} s{c["shapes"]:.0f}/{ref["shapes"]:.0f} '
                   f'd{c["dressing"]:.0f}/{ref["dressing"]:.0f} {"PASS" if ok else "FAIL"}')
        else:
            sub = 'by eye'
        rk._label(sheet, it[1][:int(img.width / 6)], (x, y0 + img.height + 2))
        rk._label(sheet, sub, (x, y0 + img.height + 14), (200, 200, 210))
    return sheet


def compare_sheet(items, rows, scale=4):
    """Measured pieces beside an official Eastward crop of the same kind of surface at the
    same character height (an adult 25 px), both at `scale`."""
    import detail_bar as db
    tiles = []
    for it, r in zip(items, rows):
        if it[3] is None or r[3] is None:
            continue
        x0, y0, x1, y1 = it[3]
        ref = rk.eastward_crop(REF_FOR[it[4]], (x1 - x0, y1 - y0))
        tiles.append((it[1], it[4], it[2].image().crop(it[3]), ref, r))
    if not tiles:
        return None
    side = max(t[2].width for t in tiles) * scale
    tw, th = side * 2 + 30, max(t[2].height for t in tiles) * scale + 40
    cols = 3
    sheet = Image.new('RGB', (cols * tw + 10, ((len(tiles) + cols - 1) // cols) * th + 10), (46, 40, 52))
    for i, (name, kind, ours, ref, r) in enumerate(tiles):
        x, y = 10 + (i % cols) * tw, 10 + (i // cols) * th
        sheet.paste(ours.resize((ours.width * scale, ours.height * scale), Image.NEAREST), (x, y))
        if ref is not None:
            sheet.paste(ref.resize((ref.width * scale, ref.height * scale), Image.NEAREST), (x + side + 8, y))
        c, b = r[3], db.bar(kind)
        rk._label(sheet, f'{name[:34]} | Eastward {REF_FOR[kind][9:]}', (x, y + ours.height * scale + 2))
        rk._label(sheet, f't {c["tones"]:.1f}/{b["tones"]:.1f} s {c["shapes"]:.1f}/{b["shapes"]:.1f} '
                  f'd {c["dressing"]:.1f}/{b["dressing"]:.1f} {"PASS" if r[2] else "FAIL"}',
                  (x, y + ours.height * scale + 15), (200, 200, 210))
    return sheet


def eastward_side_by_side(p, scale=2):
    """The sample beside Eastward's forest screens at the same character height (an adult
    25 px), for the eye: their wood at Coal Town's level crossing and their farm with pines."""
    import detail_bar as db
    ref_dir = os.environ.get('REF_DIR', os.path.join(tempfile.gettempdir(), 'napattack-refs'))
    shots = []
    for key, box in (('eastward-08-canopy', (0, 0, 960, 1080)), ('eastward-13-pine', (240, 0, 1400, 1080))):
        b = db.load()['baselines'][key]
        path_ = os.path.join(ref_dir, b['url'].rsplit('/', 1)[1])
        if not os.path.exists(path_):
            return None
        im = Image.open(path_).convert('RGB').crop(box)
        f = 25.0 / b['adult_px']
        shots.append(im.resize((int(im.width * f), int(im.height * f)), Image.LANCZOS))
    ours = p.image()
    W = ours.width + sum(s.width for s in shots) + 20
    H = max(ours.height, max(s.height for s in shots))
    out = Image.new('RGB', (W, H + 16), (46, 40, 52))
    out.paste(ours, (0, 16))
    x = ours.width + 10
    for s in shots:
        out.paste(s, (x, 16))
        x += s.width + 10
    rk._label(out, 'forest kit sample', (4, 2))
    rk._label(out, 'Eastward (official screenshots), adult scaled to 25 px', (ours.width + 14, 2))
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def sample_preview(p, scale=2, people=True):
    """The sample at `scale` with residents standing on the path for scale (preview only:
    the residents are old art shown beside the new for size, not used in it)."""
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in (('hiker', (210, 446)), ('forager', (300, 300))):
            path_ = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')  # ledger: compare
            if os.path.exists(path_):
                r = Image.open(path_).convert('RGBA')
                r = r.resize((r.width // 4, r.height // 4), Image.NEAREST)
                img.alpha_composite(r, (x - r.width // 2, y - r.height))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def check() -> list:
    """The kit's walking and mixing contract."""
    faults = []
    p, parts = sample()
    L, pm = parts['tiers'], parts['path']
    a = (138, 570)                                    # the path at the meadow's south edge
    ys, xs = np.nonzero(pm & (p.y < 20))
    if not len(xs):
        faults.append('the sample path does not reach the upper wood')
    else:
        seen = np.zeros(p.walk.shape, bool)
        seen[a[1], a[0]] = p.walk[a[1], a[0]]
        while True:
            grown = dilate(seen, 1) & p.walk
            if (grown == seen).all():
                break
            seen = grown
        if not (seen & pm & (p.y < 20)).any() or not seen[GLADE[1], GLADE[0]]:
            faults.append('the sample path cannot be walked from the meadow, through the glade and up the steps')
    if (p.walk & L.face & ~parts['steps']).any():
        faults.append(f'{int((p.walk & L.face & ~parts["steps"]).sum())} face pixels are walkable off the steps')
    if (p.walk & (L.west | L.east)).any():
        faults.append('a side band is walkable')
    gx, gy = GLADE[0], GLADE[1]
    if not p.walk[gy, gx]:
        faults.append('the glade centre is blocked')
    run = longest_run(parts['things'])
    if run > 3:
        faults.append(f'{run} trees of one kind stand side by side on a canopy front (most 3)')
    q, sp = strip()
    t2 = sp['t_old']
    fade_rows = [y for y in range(q.h) if 0.05 < t2[y, :].mean() < 0.2]
    if fade_rows:
        y = fade_rows[len(fade_rows) // 2]
        cols = np.nonzero(q.walk[y])[0]
        if len(cols) < q.w * 0.4:
            faults.append(f'the old forest fade is mostly blocked (row {y}: {len(cols)} of {q.w} px open)')
    wm = (t2 >= 0.25) & (t2 < 0.5)
    inner = wm & shift(wm, 0, -12, False)                 # the wall behind its open front band
    if inner.any() and q.walk[inner].mean() > 0.02:
        faults.append(f'the old forest wall is walkable ({q.walk[inner].mean():.0%} of it open)')
    if longest_run(sp['things']) > 3:
        faults.append('the strip has more than three trees of a kind side by side on a front')
    return faults


def main(argv):
    if '--check' in argv:
        faults = check()
        for f in faults:
            print('FAULT:', f)
        print('forest_kit check:', 'pass' if not faults else f'{len(faults)} faults')
        return 1 if faults else 0
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-forest-kit')
    os.makedirs(out, exist_ok=True)
    items = pieces()
    rows = bar_rows(items)
    kit_sheet(items, rows).save(os.path.join(out, 'kit-sheet.png'))
    cmp = compare_sheet(items, rows)
    if cmp is not None:
        cmp.save(os.path.join(out, 'compare-eastward.png'))
    print(f'{"piece":62s} {"kind":6s} tones  shapes dressing isolated cluster  lone   result')
    for (name, kind, ok, c, lone) in rows:
        if c is None:
            print(f'{name:62s} {kind:6s} (judged by eye)                              {lone:.3f}')
            continue
        print(f'{name:62s} {kind:6s} {c["tones"]:5.1f} {c["shapes"]:6.1f} {c["dressing"]:7.1f} '
              f'{c["isolated"]:8.3f} {c["cluster"]:7.1f}  {lone:.3f}  {"PASS" if ok else "FAIL"}')
    p, parts = sample()
    p.image().save(os.path.join(out, 'sample.png'))
    sample_preview(p, 2).save(os.path.join(out, 'sample-2x.png'))
    q, _sp = strip()
    q.image(2).save(os.path.join(out, 'strip-2x.png'))
    sbs = eastward_side_by_side(p)
    if sbs is not None:
        sbs.save(os.path.join(out, 'sample-vs-eastward.png'))
    img = p.image()
    L = parts['tiers']
    print('sample boxes:')
    for name, box, kind in (('canopy, lower wood', best_box(_leafy(p) & (p.y > 300) & (p.y < 430), 40, 0.93), 'tree'),
                            ('canopy, upper wood', best_box(_leafy(p) & (L.T >= 1) & (p.y < 120) & ~parts['old'], 36), 'tree'),
                            ('glade', best_box(parts['glade'] & ~p.solid & ~parts['path'], 40, 0.99), 'ground'),
                            ('woodland path', best_box(parts['path'] & ~p.solid & (p.y > 300), 34, 0.5), 'ground'),
                            ('bank face', best_box(L.face & ~p.solid & ~dilate(parts['steps'], 6), 34, 0.95), 'face'),
                            ('hay meadow', (420, 500, 520, 570), 'ground')):
        if box is None:
            print(f'  {name:22s} (no clear box)')
            continue
        ok, c, ref = judge(img, box, kind)
        print(f'  {name:22s} {kind:6s} {box} tones {c["tones"]:.1f}/{ref["tones"]:.1f} shapes {c["shapes"]:.1f}/'
              f'{ref["shapes"]:.1f} dressing {c["dressing"]:.1f}/{ref["dressing"]:.1f} isolated {c["isolated"]:.3f} '
              f'cluster {c["cluster"]:.1f}  {"PASS" if ok else "FAIL"}')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

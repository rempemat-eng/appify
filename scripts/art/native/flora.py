"""Plants drawn natively at any density, in units (1 unit = 1 texel at density 2).

Every function takes the density `d` and a `fams` dict from the biome file (scripts/art/biomes/
<biome>.json, "flora"), so a second biome is a new data file. Each returns a Drawn: the image,
its anchor (the foot, in image px) and the mask that throws the cast shadow; trees also carry
their crown mask (for the canopy's shade on the ground).

Foliage follows house-style 5 ("a crown in four light bands, leaf clumps one tone above their
band, each with a light cap and a dark U under it, a yellow-green rim on the lit edge, the deep
band quiet") as Eastward's layered canopies: masses back to front, each lit as its own form.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage as ndi

from . import raster as pk
from . import style as ST


@dataclass
class Drawn:
    img: object
    anchor: tuple
    alpha: np.ndarray
    crown: np.ndarray | None = None
    trunk_h: float = 0.0           # units from the foot to the crown's underside (shadow on the trunk)
    meta: dict = field(default_factory=dict)


def sprite(d, wu, hu, ax_u, pad_u=2, mirror=False):
    """A sprite canvas wu x hu units at density d with its foot at (ax_u, hu - pad_u) units.
    Sizes and the anchor are even texels at density 2, so the sprite's top-left is a whole
    world px when it is placed by its foot (zone objects are placed in world px)."""
    s = d / 2
    W = int(math.ceil(wu * s / 2)) * 2
    H = int(math.ceil(hu * s / 2)) * 2
    ox = int(round(ax_u * s / 2)) * 2
    oy = H - max(2, int(round(pad_u * s / 2)) * 2)
    return pk.Sprite(W, H, s, ox, oy, mirror)


def done(sp, crown=None, trunk_h=0.0, outline=True, **meta) -> Drawn:
    img = sp.render(outline=outline)
    a = np.asarray(img)[..., 3] > 0
    return Drawn(img, (sp.g.ox, sp.g.oy), a, crown, trunk_h, meta)


# ------------------------------------------------------------------------------------------------
# crowns
# ------------------------------------------------------------------------------------------------
def crown(sp, lobes, fams, name='crown', seed=3, z=5.0, leaf=None, bump=None, rim=None, deep_base=2):
    """Layered foliage: the crown is a stack of masses, back (upper) to front (lower). Each mass
    is lit as its own form from the upper left, has a run of bumps along its upper edge, and a
    dark gap where it rises over the mass behind it (its line). Inside, small pointed leaf marks
    (2 to 4 px at 2x) one tone up in the light and one down in the shade, some only a sibling
    swap; a yellow-green rim on the crown's lit edge. Returns the crown mask."""
    g = sp.g
    s = sp.s
    leaf = ST.get('crown', 'leaf_units', 2.4) if leaf is None else leaf
    bump = ST.get('crown', 'bump_units', 7.0) if bump is None else bump
    rim = ST.get('crown', 'rim_family', 'grass') if rim is None else rim
    rng = np.random.default_rng(seed)
    order = sorted(range(len(lobes)), key=lambda i: lobes[i][1])
    masks = []
    for i in order:
        cx, cy, rx, ry = lobes[i]
        m = g.ellipse(cx, cy, rx, ry)
        n = max(5, int(2 * math.pi * max(rx, ry) / (bump * 1.7)))
        for k in range(n):
            a = math.pi + math.pi * (k + rng.uniform(-0.25, 0.25)) / (n - 1)
            bx = cx + math.cos(a) * (rx - bump * 0.35)
            by = cy + math.sin(a) * (ry - bump * 0.35)
            br = bump * rng.uniform(0.8, 1.15)
            m |= g.ellipse(bx, by, br, br * 0.82)
        masks.append(m)
    full = np.zeros((g.h, g.w), bool)
    for m in masks:
        full |= m
    if not full.any():
        return full
    X0, X1, Y0, Y1 = g.X[full].min(), g.X[full].max(), g.Y[full].min(), g.Y[full].max()
    ccx, ccy, rx, ry = (X0 + X1) / 2, (Y0 + Y1) / 2, max(1, (X1 - X0) / 2), max(1, (Y1 - Y0) / 2)
    Lg = -0.62 * (g.X - ccx) / rx - 0.78 * (g.Y - ccy) / ry
    if g.mirror:
        Lg = 0.62 * (g.X - ccx) / rx - 0.78 * (g.Y - ccy) / ry
    fl = [fams['body'], fams['warm'], fams['cool']]
    clump = leaf * ST.get('crown', 'clump_factor', 1.7)   # a leaf clump's radius in units (about 8 texels across at 2x)
    for j, i in enumerate(order):
        m = masks[j]
        f = fl[j % 3]
        nm = f'{name}{j}'
        cx, cy, lrx, lry = lobes[i]
        gl = -0.62 * (cx - ccx) / rx - 0.78 * (cy - ccy) / ry
        base = 3 if gl > -0.25 else deep_base
        p = sp.add(nm, m, f, base=base, lo=1, hi=5 if base == 3 else 4, z=z + j * 0.01, k=ST.get('crown', 'mass_k', 0.85), casts=False, line=True)
        p.famarr = np.full(m.shape, f, dtype=object)
        rel = np.zeros(m.shape, int)
        # clumps in staggered rows, back (top) to front, each nearer one over the one behind:
        # the clump a tone up, a light cap at its upper left on the lit side, a dark U under it
        # (house-style 5); none in the deep shade, which stays quiet
        rows = np.arange(cy - lry - bump, cy + lry + bump * 0.5, clump * ST.get('crown', 'row_step', 1.45))
        for ri, gy in enumerate(rows):
            for gx in np.arange(cx - lrx - bump + (clump if ri % 2 else 0), cx + lrx + bump, clump * ST.get('crown', 'col_step', 2.05)):
                x = gx + rng.uniform(-0.3, 0.3) * clump
                y = gy + rng.uniform(-0.3, 0.3) * clump
                px, py = g.px(x, y)
                if not (0 <= px < g.w and 0 <= py < g.h) or not m[py, px]:
                    continue
                v = -0.62 * (x - cx) / lrx - 0.78 * (y - cy) / lry + 0.5 * Lg[py, px]
                if g.mirror:
                    v = 0.62 * (x - cx) / lrx - 0.78 * (y - cy) / lry + 0.5 * Lg[py, px]
                if v < ST.get('crown', 'deep_skip', -0.8) or (v < ST.get('crown', 'deep_thin', -0.4) and rng.random() < 0.5):
                    continue
                r = clump * rng.uniform(0.85, 1.15)
                c = g.ellipse(x, y, r, r * 0.78) & m
                u = g.ellipse(x + r * 0.08, y + r * 0.62, r * 1.02, r * 0.5) & ~c & m
                cap = c & g.ellipse(x - r * 0.38, y - r * 0.42, r * 0.5, r * 0.3)
                rel[u] = -1
                rel[c] = 1 if v > -0.1 else (0 if v > ST.get('crown', 'shade_clump_below', -0.4) else -1)
                if v > ST.get('crown', 'lit_cap_above', 0.35):
                    rel[cap] = 2
                    if v > 0.8 and rng.random() < 0.5:
                        p.famarr[cap] = rim
                if rng.random() < ST.get('crown', 'sibling_swap', 0.4):
                    alt = [q for q in fl if q != f]
                    p.famarr[c] = alt[int(rng.integers(0, len(alt)))]
        p.rel = rel
    er = ndi.binary_erosion(full, iterations=max(1, int(round(s))))
    rimm = full & ~er & (Lg > 0.3)
    sp.add(name + '_rim', rimm, rim, base=4, lo=3, hi=5, z=z + 1, flat=True, casts=False, clean=True)
    sp.part(name + '_rim').rel = np.where(Lg > 0.75, 1, 0)
    return full


def bark(sp, name, mask, rng, k, x0, x1, y0, y1, n=7):
    """Bark marks: short fissures, each a dark streak with a lit one west of it (broken, never a
    full-height stripe; eastward-edges 2.4 for faces, the same for trunks)."""
    g = sp.g
    for _ in range(n):
        x = rng.uniform(x0, x1)
        ya = rng.uniform(y0, y1)
        ln = rng.uniform(5, 11) * k
        sp.mark(name, g.capsule(x, ya, x + rng.uniform(-0.8, 0.8), ya + ln, 0.7) & mask, -1)
        sp.mark(name, g.capsule(x - 1.6, ya + 1, x - 1.6, ya + ln * 0.6, 0.6) & mask, 1 if x < (x0 + x1) / 2 else 0)


def _roots(g, k, w=8.0, spread=13.0):
    return (g.poly([(-w * k, -12 * k), (w * k, -12 * k), (w * k + 1, -6 * k), (spread * k, -1.5 * k), (w * k - 1, -3 * k),
                    (2 * k, 0), (-3 * k, -1 * k), (-w * k, -2.5 * k), (-spread * k + 1, -1 * k), (-w * k - 1, -7 * k)]))


# ------------------------------------------------------------------------------------------------
def broadleaf(d, fams, seed=11, scale=1.0, shape='oak'):
    """A mature broadleaf (oak or beech): a trunk on roots, two limbs, a crown of nine or ten
    masses. Oak: a rugged brown trunk and a deep green crown; beech: a smooth grey trunk and a
    rounder, lighter crown. About 84 world px tall at scale 1 (size guide: broadleaf 78 to 125)."""
    k = scale
    sp = sprite(d, 150 * k, 172 * k, 75 * k, 4)
    g = sp.g
    rng = np.random.default_rng(seed)
    tf = fams['trunk_' + shape]
    tw = 7.0 if shape == 'oak' else 6.0
    tr = g.poly([(-tw * k, -64 * k), (tw * k, -64 * k), ((tw + 1) * k, -12 * k)]) | g.rect(-tw * k, -64 * k, tw * k, -6 * k)
    tr = pk.round_mask(tr | _roots(g, k, tw + 1), 1)
    sp.add('trunk', tr, tf, base=3, lo=0, hi=4, z=1, mode='cyl', k=1.0)
    if shape == 'oak':
        bark(sp, 'trunk', tr, rng, k, -4.5 * k, 5.0 * k, -60 * k, -16 * k)
    else:   # beech: smooth, a few horizontal lenticels and a lit band
        for _ in range(6):
            x, y = rng.uniform(-4, 4) * k, rng.uniform(-58, -14) * k
            sp.mark('trunk', g.rect(x - 1.5, y, x + 1.5, y + 1) & tr, -1)
    sp.add('limbL', g.capsule(-2 * k, -58 * k, -20 * k, -86 * k, 3.4 * k, 2.2 * k), tf, base=2, lo=0, hi=3, z=1.5)
    sp.add('limbR', g.capsule(3 * k, -60 * k, 22 * k, -82 * k, 3.2 * k, 2.0 * k), tf, base=2, lo=0, hi=3, z=1.5)
    if shape == 'oak':
        lobes = [(0, -112, 46, 34), (-34, -96, 30, 24), (34, -94, 30, 24), (-18, -134, 30, 22), (20, -132, 28, 22),
                 (-48, -110, 18, 16), (50, -108, 17, 15), (-14, -80, 26, 14), (16, -80, 24, 13), (0, -148, 20, 13)]
        cf = fams['oak']
    else:
        lobes = [(0, -114, 44, 36), (-32, -100, 28, 24), (32, -98, 28, 24), (-14, -138, 30, 22), (18, -136, 26, 20),
                 (-44, -116, 16, 16), (46, -114, 16, 15), (0, -84, 34, 14)]
        cf = fams['beech']
    lobes = [(a * k, b * k, c * k, e * k) for (a, b, c, e) in lobes]
    cm = crown(sp, lobes, cf, seed=seed, z=5)
    sp.mark('trunk', g.rect(-20, -66 * k, 20, -56 * k), -1)
    sp.mark('trunk', g.rect(-20, -66 * k, 20, -61 * k), -1)
    return done(sp, cm, 66 * k)


def veteran_oak(d, fams, seed=3, scale=1.0):
    """The hollow oak: a landmark (size guide: veteran tree, 88 to 160 tall): a broad trunk on
    spreading roots with a dark hollow at its foot (a lit lip round it, its depth in ink), a
    huge crown of eleven masses. About 112 world px tall."""
    k = scale
    sp = sprite(d, 210 * k, 228 * k, 105 * k, 4)
    g = sp.g
    rng = np.random.default_rng(seed)
    tf = fams['trunk_oak']
    tr = g.poly([(-15 * k, -92 * k), (14 * k, -92 * k), (17 * k, -20 * k), (28 * k, -2 * k), (14 * k, -4 * k),
                 (6 * k, 0), (-4 * k, -1 * k), (-14 * k, -3 * k), (-30 * k, -1 * k), (-18 * k, -22 * k)])
    tr = pk.round_mask(tr, 1)
    sp.add('trunk', tr, tf, base=3, lo=0, hi=4, z=1, mode='cyl', k=1.0)
    bark(sp, 'trunk', tr, rng, k, -12 * k, 13 * k, -88 * k, -30 * k, n=14)
    # the hollow: an arch at the foot, dark inside, a lit lip on its west and top
    hol = g.rrect(-6 * k, -26 * k, 6 * k, -2 * k, 5.5 * k)
    sp.add('hollow', hol, 'earth', fixed=0, z=1.2)
    lip = (g.rrect(-8 * k, -28 * k, 8 * k, -1 * k, 7 * k) & ~hol) & tr
    sp.add('lip', lip & (g.X < 0) | (lip & (g.Y < -22 * k)), tf, base=4, lo=3, hi=5, z=1.3, flat=True)
    sp.add('lipR', lip & (g.X >= 0) & (g.Y >= -22 * k), tf, base=1, lo=0, hi=2, z=1.3, flat=True)
    for (x0, y0, x1, y1, r0, r1) in ((-4, -88, -34, -128, 6.0, 3.0), (5, -90, 36, -122, 5.6, 2.8), (0, -90, 2, -136, 5.0, 2.6)):
        sp.add(f'limb{x1}', g.capsule(x0 * k, y0 * k, x1 * k, y1 * k, r0 * k, r1 * k), tf, base=2, lo=0, hi=3, z=1.5)
    lobes = [(0, -160, 64, 46), (-50, -140, 40, 32), (50, -138, 40, 32), (-26, -190, 40, 28), (28, -188, 38, 28),
             (-72, -156, 24, 20), (74, -152, 22, 20), (-20, -116, 38, 18), (24, -116, 36, 17), (0, -210, 26, 16),
             (-56, -120, 22, 14)]
    lobes = [(a * k, b * k, c * k, e * k) for (a, b, c, e) in lobes]
    cm = crown(sp, lobes, fams['oak'], seed=seed, z=5, bump=8.0)
    sp.mark('trunk', g.rect(-40, -96 * k, 40, -84 * k), -1)
    return done(sp, cm, 96 * k)


def birch(d, fams, seed=31, scale=1.0):
    """A birch: a pale trunk with dark lenticels and a black-marked base, a narrow, airy crown
    in the light greens. About 76 world px tall at scale 1 (size guide: birch 64 to 104)."""
    k = scale
    sp = sprite(d, 76 * k, 160 * k, 38 * k, 4)
    g = sp.g
    rng = np.random.default_rng(seed)
    tr = pk.round_mask(g.poly([(-3.4 * k, -86 * k), (3.0 * k, -86 * k), (4.6 * k, -4 * k), (7 * k, 0), (-6 * k, 0), (-4.4 * k, -4 * k)]), 1)
    sp.add('trunk', tr, fams['trunk_birch'], base=4, lo=1, hi=5, z=1, mode='cyl')
    for j in range(9):
        y = rng.uniform(-82, -8) * k
        x = rng.uniform(-3, 2) * k
        sp.mark('trunk', g.rect(x, y, x + rng.uniform(2, 4) * k, y + 1.2) & tr, -3)
    sp.mark('trunk', g.rect(-8, -9 * k, 8, 0) & tr, -2)
    sp.add('limb', g.capsule(1 * k, -70 * k, 12 * k, -96 * k, 2.0 * k, 1.2 * k), fams['trunk_birch'], base=3, lo=1, hi=4, z=1.5)
    lobes = [(0, -112, 24, 30), (-12, -96, 16, 18), (12, -98, 16, 18), (-4, -136, 18, 18), (6, -84, 18, 10)]
    lobes = [(a * k, b * k, c * k, e * k) for (a, b, c, e) in lobes]
    cm = crown(sp, lobes, fams['birch'], seed=seed, z=5, leaf=2.0, bump=5.5)
    return done(sp, cm, 84 * k)


def pine(d, fams, seed=41, scale=1.0):
    """A pine or fir: a straight trunk and stacked tiers of drooping boughs, each tier lit on
    its upper left with a dark underside, the top a narrow spire. About 82 world px tall at
    scale 1 (size guide: conifer 64 to 125, 28 to 48 wide)."""
    k = scale
    sp = sprite(d, 92 * k, 172 * k, 46 * k, 4)
    g = sp.g
    rng = np.random.default_rng(seed)
    tr = pk.round_mask(g.rect(-3.2 * k, -40 * k, 3.2 * k, -3 * k) | _roots(g, k, 4, 8), 1)
    sp.add('trunk', tr, fams['trunk_pine'], base=3, lo=0, hi=4, z=1, mode='cyl')
    tiers = int(ST.get('pine', 'tiers', 7))
    full = np.zeros((g.h, g.w), bool)
    fl = fams['pine']
    for t in range(tiers):
        u = t / (tiers - 1)                       # 0 bottom .. 1 top
        yb = (-24 - u * 120) * k
        hw = (40 - u * 31) * k * rng.uniform(0.92, 1.08)
        hh = (28 - u * 10) * k
        xo = rng.uniform(-1.5, 1.5) * k
        # a bough tier: from the apex out to a skirt of drooping needle tips (a zigzag), so the
        # silhouette is a run of tips, never a ruled triangle
        n = max(4, int(hw / (4.5 * k)))
        skirt = []
        for q in range(n + 1):
            xx = -hw + 2 * hw * q / n
            skirt.append((xo + xx, yb + (2.6 * k if q % 2 else -0.8 * k) - abs(xx) / hw * 3 * k))
        pts = [(xo, yb - hh)] + [(xo + hw * 0.62, yb - hh * 0.42)] + skirt[::-1] + [(xo - hw * 0.62, yb - hh * 0.42)]
        m = pk.round_mask(g.poly(pts), 1)
        f = (fl['body'], fl['cool'], fl['warm'])[t % 3]
        nm = f'tier{t}'
        sp.add(nm, m, f, base=3, lo=1, hi=5, z=5 + (tiers - t) * 0.01, k=0.9, casts=False, line=True)
        rel = np.zeros(m.shape, int)
        # needle sprays: short strokes down and out, lit on the west, dark on the east; the
        # bough's underside a tone down
        for j in range(int(hw * 0.45)):
            x = xo + rng.uniform(-hw * 0.85, hw * 0.85)
            y = yb - rng.uniform(1, hh * 0.75)
            sm = g.capsule(x, y, x + (2.0 if x > xo else -2.0) * k, y + 3.5 * k, 0.9) & m
            rel[sm] = 1 if x < xo - hw * 0.1 else -1
        under = m & ~g.poly([(a_, b_ - 2.6 * k) for (a_, b_) in pts])
        rel[under] = -1
        sp.part(nm).rel = rel
        full |= m
    rimm = full & ~ndi.binary_erosion(full, iterations=max(1, int(round(sp.s)))) & (g.X < 0)
    sp.add('rim', rimm, fl['rim'], base=4, lo=3, hi=5, z=6, flat=True, casts=False)
    return done(sp, full, 30 * k)


def sapling(d, fams, seed=51, scale=1.0):
    """A young tree (size guide: young tree 40 to 80): a thin stem staked by nothing, a small
    round crown of five masses."""
    k = scale
    sp = sprite(d, 64 * k, 104 * k, 32 * k, 3)
    g = sp.g
    st = g.capsule(0, -2, 0.5 * k, -52 * k, 2.4 * k, 1.6 * k)
    sp.add('stem', st, fams['trunk_oak'], base=3, lo=1, hi=4, z=1, mode='cyl')
    lobes = [(0, -66, 22, 18), (-14, -58, 12, 11), (14, -60, 12, 10), (-6, -80, 14, 11), (6, -50, 14, 7)]
    lobes = [(a * k, b * k, c * k, e * k) for (a, b, c, e) in lobes]
    cm = crown(sp, lobes, fams['sapling'], seed=seed, z=5, leaf=2.0, bump=5.0)
    return done(sp, cm, 50 * k)


def bush(d, fams, seed=21, w=40.0, h=30.0, kind='bush'):
    """A shrub (size guide: bush 12 to 28 tall, 16 to 42 wide) as four masses; holly is dark and
    glossy with red berries; bramble is a loose tangle of arching canes with blackberries."""
    sp = sprite(d, w + 10, h + 10, (w + 10) / 2, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    lobes = [(0, -h * 0.5, w * 0.42, h * 0.44), (-w * 0.25, -h * 0.36, w * 0.26, h * 0.34),
             (w * 0.26, -h * 0.38, w * 0.25, h * 0.32), (-w * 0.05, -h * 0.72, w * 0.27, h * 0.26)]
    f = fams[kind]
    cm = crown(sp, lobes, f, name=kind, seed=seed, z=2, bump=4.0 if kind != 'bramble' else 3.2, leaf=2.0)
    if kind in ('holly', 'bramble'):
        fam = f.get('fruit', 'berry')
        for j in range(9 if kind == 'holly' else 7):
            x = rng.uniform(-w * 0.38, w * 0.38)
            y = -rng.uniform(h * 0.25, h * 0.85)
            px, py = g.px(x, y)
            if not (0 <= px < g.w - 1 and 0 <= py < g.h - 1) or not cm[py, px]:
                continue
            b = np.zeros((g.h, g.w), bool)
            b[py:py + 2, px:px + 2] = True
            sp.detail(b, pk.rgb(fam, 3 if kind == 'holly' else 1))
            gl = np.zeros_like(b)
            gl[py, px] = True
            sp.detail(gl, pk.rgb(fam, 5 if kind == 'holly' else 3), inside=False)
    return done(sp, cm, 0)


# ------------------------------------------------------------------------------------------------
# ground plants: drawn into the ground layer (no outline on ground textures; ferns and flowers
# stand up, so they keep their outline)
# ------------------------------------------------------------------------------------------------
def fern(d, fams, seed=51, size=1.0):
    """A fern of six fronds fanning from the upper left to the lower right, each frond a rachis
    with leaflets, the middle two nearer (size guide: fern 8 to 16 tall, 12 to 28 wide)."""
    sp = sprite(d, 40 * size, 28 * size, 20 * size, 2)
    g = sp.g
    rng = np.random.default_rng(seed)
    f = fams['fern']
    for k in range(6):
        a = math.radians(-160 + k * 28 + rng.uniform(-6, 6))
        ln = (14 + rng.uniform(-2, 4)) * size
        tx, ty = math.cos(a) * ln, math.sin(a) * ln * 0.75 - 2
        mx, my = tx * 0.5, ty * 0.5 - 3 * size
        frond = g.stroke([(0, -1), (mx, my), (tx, ty)], 1.0)
        for j in range(1, 5):
            t = j / 5
            if t < 0.5:
                px_, py_ = mx * t * 2, my * t * 2
            else:
                px_, py_ = mx + (tx - mx) * (t - 0.5) * 2, my + (ty - my) * (t - 0.5) * 2
            frond |= g.ellipse(px_, py_, 2.6 * size * (1.1 - t * 0.6), 1.4 * size, rot=math.degrees(a) + 60)
        sp.add(f'f{k}', frond, (f['body'], f['warm'], f['cool'])[k % 3], base=3, lo=1, hi=4, z=1 + (k in (2, 3)), k=1.0)
    return done(sp)


def tuft(d, fams, seed, size=1.0):
    """A tuft of 4 to 6 blades: dark roots, the body, lit tips (no outline: ground texture)."""
    rng = np.random.default_rng(seed)
    sp = sprite(d, 22 * size, 18 * size, 11 * size, 1)
    g = sp.g
    b0, b1 = ST.get('tuft', 'blades', [4, 7])
    h0, h1 = ST.get('tuft', 'height_units', [9, 14])
    spread, lean = ST.get('tuft', 'spread_units', 5.0), ST.get('tuft', 'lean_units', 8.0)
    nb = int(rng.integers(b0, b1))
    m = np.zeros((g.h, g.w), bool)
    tips = np.zeros_like(m)
    wbase = 2 if d >= 1.75 else 1
    for k in range(nb):
        a = (k - (nb - 1) / 2) / max(1, nb - 1)
        bx = a * spread * size + rng.uniform(-0.6, 0.6)
        tx = bx + a * lean * size + rng.uniform(-1.5, 1.5)
        ty = -(h0 + rng.uniform(0, h1 - h0)) * size * (1.0 - 0.3 * abs(a))
        mx, my = bx + (tx - bx) * 0.45, ty * 0.5
        m |= g.line([(bx, 0), (mx, my)], wbase) | g.line([(mx, my), (tx, ty)], 1)
        tips |= g.line([(bx + (tx - bx) * 0.72, ty * 0.72), (tx, ty)], 1)
    m = m & ~g.rect(-50, 0.2, 50, 10)
    sp.add('blades', m, fams['tuft'], base=2, lo=0, hi=4, z=1, flat=True, casts=False)
    sp.mark('blades', tips, 2)
    sp.mark('blades', g.rect(-50, -2.6 * size, 50, 1), -1)
    return Drawn(sp.render(outline=False, contact=False), (sp.g.ox, sp.g.oy), None)


def flowers(d, fams, seed, kind='white', n=3):
    """A clump of n flower heads on short stems, each head a cluster (never one pixel)."""
    rng = np.random.default_rng(seed)
    sp = sprite(d, 24, 18, 12, 1)
    g = sp.g
    fam = fams['flowers'][kind]
    leaves = np.zeros((g.h, g.w), bool)
    heads = []
    for k in range(n):
        hx = (k - (n - 1) / 2) * 5.0 + rng.uniform(-1.5, 1.5)
        hy = -6.0 - rng.uniform(0, 5.0)
        leaves |= g.capsule(hx * 0.6, 0, hx, hy + 1.5, 1.0, 0.6)
        heads.append((hx, hy))
    leaves |= g.ellipse(-2.0, -1.2, 3.0, 1.4, rot=-20) | g.ellipse(2.4, -1.4, 3.0, 1.3, rot=25)
    sp.add('leaves', leaves, fams['fern']['body'], base=2, lo=1, hi=3, z=1, flat=True, casts=False)
    for k, (hx, hy) in enumerate(heads):
        sp.add(f'h{k}', g.ellipse(hx, hy, 2.2, 1.8), fam, base=4, lo=2, hi=5, z=2 + k, k=1.2)
        if fam == 'plaster' and d >= 1.75:
            c = np.zeros((g.h, g.w), bool)
            px, py = g.px(hx + 0.3, hy + 0.3)
            c[py:py + 1, px:px + 2] = True
            sp.detail(c, pk.rgb('brass', 4))
    return done(sp)


def mushrooms(d, fams, seed=81, n=3):
    """A clump of small red-capped toadstools (the Mossling's cousins), 6 to 12 units tall."""
    sp = sprite(d, 30, 22, 15, 2)
    g = sp.g
    rng = np.random.default_rng(seed)
    for k in range(n):
        x = (k - (n - 1) / 2) * 6.5 + rng.uniform(-1, 1)
        hgt = rng.uniform(6, 11)
        r = rng.uniform(3.2, 4.4)
        sp.add(f'st{k}', g.rrect(x - 1.3, -hgt + 1, x + 1.3, 0, 0.8), 'plaster', base=3, lo=2, hi=4, z=1 + k * 0.1, mode='cyl')
        cap = g.ellipse(x, -hgt, r, r * 0.7) & g.rect(x - r - 1, -hgt - r, x + r + 1, -hgt + r * 0.35)
        sp.add(f'cap{k}', cap, fams['toadstool'], base=3, lo=1, hi=5, z=2 + k * 0.1)
        sp.add(f'sp{k}', g.ellipse(x - r * 0.35, -hgt - r * 0.3, 0.9, 0.7) & cap, 'plaster', fixed=5, z=2.5 + k * 0.1)
    return done(sp)


def pebbles(d, fams, seed, n=3):
    """Two or three pebbles lying together (never one by one), each lit on its upper left with
    a dark underside, in the biome's loose stone."""
    rng = np.random.default_rng(seed)
    sp = sprite(d, 20, 12, 10, 1)
    g = sp.g
    for k in range(n):
        x = (k - (n - 1) / 2) * 5.2 + rng.uniform(-1, 1)
        y = -2.6 - rng.uniform(0, 2.2)
        rx, ry = rng.uniform(2.0, 3.0), rng.uniform(1.4, 2.0)
        sp.add(f'p{k}', g.ellipse(x, y, rx, ry), fams.get('pebble', 'stone'), base=3, lo=1, hi=5, z=1 + k * 0.1, k=1.2)
    return done(sp)


TREES = {'oak': lambda d, f, seed, scale: broadleaf(d, f, seed, scale, 'oak'),
         'beech': lambda d, f, seed, scale: broadleaf(d, f, seed, scale, 'beech'),
         'birch': birch, 'pine': pine, 'sapling': sapling,
         'veteran_oak': lambda d, f, seed, scale: veteran_oak(d, f, seed, scale)}
SHRUBS = ('bush', 'holly', 'bramble')

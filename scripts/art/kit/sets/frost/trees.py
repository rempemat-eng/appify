"""Frostline conifers and dead pines."""
from __future__ import annotations

from ._shared import (
    C,
    FI,
    K,
    SNOW,
    WEATHERED,
    _drift_west,
    _snowcap,
    _solo,
    ndi,
    np,
)

# ------------------------------------------------------------------------------------------------
# conifers (F-P1, Z2): the woodland pine's painter at other sizes, snow lying as shelves on its tiers
# ------------------------------------------------------------------------------------------------
CONIFERS = {'spruce': ((0.95, 1.06), 507), 'pine': ((1.0, 1.0), 511), 'squat': ((1.18, 0.74), 521),
            'krummholz': ((1.25, 0.44), 531), 'krummholz_b': ((1.0, 0.36), 547), 'krummholz_c': ((1.4, 0.52), 559)}



def _shelves(code, mask, seed, load=1.0):
    """Snow lying on the tiers of a conifer's crown, in place: on every bough top (an opaque texel
    with nothing above it, or with its tier's dark underside above it) a continuous shelf 3 to 6
    texels thick on the west and top, thinning to nothing at the east tips; none in the east third
    of the lower crown; a cool lower edge and a dark green row of shade under it."""
    H, W = mask.shape
    above = np.full_like(code, -1)
    above[1:] = code[:-1]
    leafy = np.isin(code // 8, [FI[n] for n in ('leaf', 'leaf_cool', 'leaf_warm', 'grass', 'grass_cool', 'grass_warm')])
    tops = mask & ((above < 0) | (leafy & (above >= 0) & (above % 8 + 2 <= code % 8)))
    tops = ndi.binary_closing(tops, structure=np.ones((1, 5), bool)) & mask
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    snow = np.zeros_like(mask)
    lvl = np.zeros(mask.shape, int)
    rng = np.random.default_rng(seed * 13 + 5)
    lab, n = ndi.label(tops, structure=np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]]))
    # (Matt's review of round 3: the snow read as one white triangle stamped on every bough) each
    # bough top carries one to three clumps of its own length and height, following the tier's top
    # edge, heaped where the bough is stiff (west, near the trunk) and sagging a row at the tip;
    # some boughs are bare; the bough's dark underside shows beneath every clump
    Nf = ndi.gaussian_filter(rng.random((H, W)), (2.5, 2.2), mode='nearest')
    Nf = (Nf - Nf.min()) / max(1e-6, Nf.max() - Nf.min())
    for k in range(1, n + 1):
        ry, rx = np.nonzero(lab == k)
        if len(rx) < 3:
            continue
        xl, xr = rx.min(), rx.max()
        for y, xx in zip(ry, rx):
            ux_ = (xx - x0) / max(1, x1 - x0)
            uy_ = (y - y0) / max(1, y1 - y0)
            if ux_ > 0.74 and uy_ > 0.45:
                continue
            v = Nf[y, xx]
            if v < 0.45:
                continue                                    # a gap between two clumps
            t = int(round((2.0 + 5.5 * (v - 0.45) / 0.55) * load * (1.3 - 0.65 * ux_) * (1.0 if uy_ < 0.8 else 0.8)))
            sag = 1 if (xr - xx) <= 1 and xr - xl >= 4 else 0  # the bough's tip bends under it
            for j in range(t):
                yy = y + j + sag
                if yy < H and mask[yy, xx]:
                    snow[yy, xx] = True
                    lvl[yy, xx] = j
    # no one-texel strip of green left between two clumps (it would read as a drawn line)
    for _ in range(2):
        gap = mask & ~snow & ((np.roll(snow, 1, 0) & np.roll(snow, -1, 0)) | (np.roll(snow, 1, 1) & np.roll(snow, -1, 1)))
        snow |= gap
        lvl[gap] = 1
    # tones: each clump's top row lit on its west, its body, a cool lower edge, the shade under it
    lowest = snow & ~np.roll(snow, -1, 0)
    Hh, Wd = H, W
    Xg = np.mgrid[0:Hh, 0:Wd][1]
    ux = (Xg - x0) / max(1, x1 - x0)
    west_end = snow & ~np.roll(snow, 1, 1)
    c = np.where(lvl == 0, np.where(ux < 0.5, C('snow', 5), C('snow', 4)), C('snow', 4))
    c = np.where(west_end & (lvl <= 1), C('snow', 5), c)
    c = np.where(lowest & (lvl > 0), C('snow_cool', 3), c)
    c = np.where((ux > 0.62) & (lvl > 0), C('snow_cool', 4), c)
    code[snow] = c[snow]
    # the bough's dark underside: two rows under the heavier clumps, so it reads as shade, not a line
    under = np.roll(lowest & (lvl >= 2), 1, 0) & mask & ~snow
    code[under] = C('leaf_cool', 1)
    under2 = np.roll(under, 1, 0) & mask & ~snow
    code[under2] = C('leaf_cool', 1)
    under3 = np.roll(under2, 1, 0) & mask & ~snow
    code[under3] = C('leaf_cool', 2)
    del seed
    return snow



def conifer(form='pine', load=1.0, seed=None):
    """A conifer of the Frostline: the woodland pine's tiered painter (woodtrees.pine_tiers and
    pine_crown, the approved pine's recipe) at another size and seed, so the forms differ in
    silhouette (`spruce` tall and narrow, `pine`, `squat` wind-cropped, `krummholz` a low
    tree-line shrub), with snow as shelves on its tiers and a small heap at the trunk's west foot."""
    from scripts.art.native import compose as CO
    from scripts.art.native import screen as SCR
    from scripts.art.native import woodtrees as WT
    from scripts.art.native import ctx
    scale, s0 = CONIFERS[form]
    seed = s0 if seed is None else seed
    arr = np.asarray(CO.old_sprite(SCR._master('zones_props_pine.png'), raw=True)[0])
    tw = SCR.tree_dims('zones_props_pine.png')['tw']
    d = ctx.D
    rng = np.random.default_rng(seed * 7 + 31)
    fams, wts, lo, hi = WT.LOOKS['pine']
    lad = WT.Ladder(fams, wts)
    S, foot, _ = WT.master_crown(arr, d, size=scale)
    tiers = WT.pine_tiers(S, rng)
    code, mask, _v = WT.pine_crown(S, tiers, lad, rng, lo, hi, fams, wts)
    _shelves(code, mask, seed, load)
    T = tw * d * (0.8 if form.startswith('krummholz') else 1.0)
    cols = int(round(foot[0]))
    half_t = max(2, int(T / 2))
    band = mask[:, max(0, cols - half_t):cols + half_t + 1]
    bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
    cb = min(bots) if bots else foot[1] - 10 * d
    length = int(foot[1] - cb + (4 if form.startswith('krummholz') else 10))
    tc, tm, (tfx, tfy), _ty = WT.trunk2('oak', length, T * 0.6, T * 1.05, rng, lean=2, twist=1.0, roots=3, limbs=0,
                                        limb_rise=12.0, limb_spread=0.0, bark='oak', front_root=False,
                                        root_rows=(5, 12), root_reach=(1, 8), root_w=(0.45, 3.4))
    out, ft = WT._compose((tc, tm, (tfx, tfy)), code, mask, foot)
    WT._close_pinholes(out)
    out, ft = WT._crop(out, ft)
    # the heap of snow at the trunk's west foot
    fx, fy = int(round(ft[0])), int(round(ft[1]))
    pad = 6
    big = np.full((out.shape[0] + 2, out.shape[1] + 2 * pad), -1, np.int64)
    big[:out.shape[0], pad:pad + out.shape[1]] = out
    fx += pad
    for x in range(fx - 14, fx - 1):
        h = int(round(3.2 - abs(x - (fx - 8)) * 0.38))
        for k_ in range(max(0, h)):
            y = fy - k_
            if 0 <= y < big.shape[0]:
                big[y, x] = C('snow', 5) if k_ == h - 1 else C('snow', 4)
    out = big
    pic = K.crop(out.astype(np.int32), fx, fy)
    return pic



def snag(seed=541):
    """A dead pine at the tree line: a weathered grey bole leaning a little east and tapering, its
    top snapped into two jagged points, four stub limbs of different lengths, snow on the break and
    the stubs, a drift at its west foot, a root flare."""
    sc = K.Scene(-36, 36, -16, 14, 200)
    rng = np.random.default_rng(seed)
    h = 0.0
    r = 7.0
    x = 0.0
    sc.ellipsoid(0, 0, 2.0, 11, 7, 4.0, WEATHERED, base=2.4, k=1.6, tag='wood', flat=1.2)          # the root flare
    for k in range(8):
        z1 = h + 17 + rng.uniform(-2, 2)
        sc.cylinder(x, 0, r, h, z1, WEATHERED, base=2.7, k=1.7, tag='wood', mix=rng.random(), tex='wood_v')
        h = z1
        r = max(2.2, r - 0.6)
        x += 0.6 + k * 0.08
    sc.cylinder(x - 1.2, 0, 1.6, h, h + 14, WEATHERED, base=2.9, k=1.7, tag='wood')                 # the snapped points
    sc.cylinder(x + 1.4, 0, 1.3, h, h + 8, WEATHERED, base=2.6, k=1.7, tag='wood')
    for (z, ln, side) in ((58, 9, -1), (78, 13, 1), (101, 7, -1), (119, 10, 1)):
        xx = x * z / max(1.0, h)
        x0, x1 = (xx - ln - 2, xx - 1) if side < 0 else (xx + 1, xx + ln + 2)
        sc.box(x0, -1.3, z, x1, 1.3, z + 2.6, WEATHERED, base=2.8, k=1.6, tag='wood', round_=0.8)
        sc.box(x0 + 1, -1.3, z + 2.3, x1 - 1, 1.3, z + 4.0, SNOW, base=3.9, k=1.0, tag='snow', round_=0.6)
    _snowcap(sc, x - 1.2, 0.0, h + 14.5, 1.8, 1.6, th=1.4, seed=seed)
    _drift_west(sc, -9, 2, 9, seed)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)

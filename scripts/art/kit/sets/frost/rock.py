"""Frostline granite rocks, faces and stairs."""
from __future__ import annotations

from ._shared import (
    B,
    C,
    FACE_PX,
    FI,
    GRANITE,
    K,
    LIP_PX,
    SNOW,
    SNOWS,
    V,
    _chip,
    _cracks,
    _drift_west,
    _fractures,
    _grain_after,
    _granite_dress,
    _rock,
    _rock_r2,
    _snow_light,
    _snowcap,
    _solo,
    hsh,
    math,
    ndi,
    np,
)
from .water_ice import (
    _icefall,
)

def boulder(kind='a', seed=43):
    """A Frostline granite boulder (not the woodland's): `a` and `b` mid-sized, `large` a cluster
    of a big block with two smaller ones in its lee, `small` a stone a cell across."""
    sc = K.Scene(-60, 60, -40, 24, 120)
    if kind == 'a':
        _rock(sc, 0, -6, 30, 20, 20, seed)
    elif kind == 'b':
        _rock(sc, -2, -6, 26, 18, 26, seed + 1)
    elif kind == 'large':
        _rock(sc, -10, -12, 36, 26, 38, seed + 2)
        _rock(sc, 12, -16, 26, 20, 28, seed + 6, drift=False)
        _rock(sc, 26, 4, 20, 14, 16, seed + 3, drift=False)
        _rock(sc, 36, -10, 14, 10, 12, seed + 4, drift=False)
    else:
        _rock_r2(sc, 0, -4, 8, 5, 6, seed + 5)
    if kind == 'small':
        a = _solo(sc, dress=lambda s, a: _cracks(s, a, n=2, seed=seed))
    else:
        a = _solo(sc, dress=lambda s, a: (_chip(s, a, seed), _granite_dress(s, a, seed, n_frac=6 if kind == 'large' else 3)))
        _grain_after(sc, a, seed)
    return K.crop(a, sc.ox, sc.oy)


def crag(kind='a', seed=61):
    """A crag of the headwall's foot (round 3, R2-R1): overlapping granite blocks of different sizes,
    the big ones behind and the small ones stepping down in front, staggered in depth and height
    (none a tower, no pile of equal balls), snow with thickness on every top and ledge, drifts at the
    west foot. The zone's north frame (B8, Z1)."""
    rng = np.random.default_rng(seed + (0 if kind == 'a' else 9))
    sc = K.Scene(-110, 110, -60, 24, 160)
    if kind == 'a':
        spec = [(-34, -36, 54, 30, 44), (12, -40, 62, 32, 52), (54, -28, 40, 26, 34), (-62, -16, 36, 22, 24),
                (-20, -8, 40, 22, 26), (24, -8, 34, 20, 20), (60, -2, 26, 16, 14), (-2, 8, 22, 12, 10)]
    else:
        spec = [(-28, -38, 60, 32, 58), (28, -34, 52, 28, 46), (-64, -20, 34, 22, 26), (60, -16, 36, 22, 24),
                (-4, -12, 42, 22, 24), (32, 2, 26, 14, 12), (-42, 4, 24, 14, 11)]
    for k, (x, y, w, d, h) in enumerate(spec):
        _rock(sc, x + rng.uniform(-3, 3), y, w * rng.uniform(0.9, 1.1), d, h * rng.uniform(0.9, 1.1), seed + 13 * k,
              drift=False)
    for k in (3, len(spec) - 1) if kind == 'a' else (2, len(spec) - 1):
        x, y, w, d, h = spec[k]
        r = 6 + w * 0.2
        sc.ellipsoid(x - w * 0.42, y + d * 0.3, 0.2, r, r * 0.6, r * 0.55, SNOW, base=3.8, k=1.0, tag='drift', flat=1.0)
    a = _solo(sc, dress=lambda s, a: (_chip(s, a, seed), _granite_dress(s, a, seed, n_frac=10)))
    _grain_after(sc, a, seed)
    return K.crop(a, sc.ox, sc.oy)



def cairn(kind='standing', seed=47):
    """A Frostline waymark of granite (not the Brackens' gritstone): stones laid in shrinking rings,
    each ring's top under a ledge of snow, the upright capped, a drift at the west foot; `toppled`
    spilled east, `small` a two-ring marker."""
    sc = K.Scene(-44, 48, -30, 20, 90)
    rng = np.random.default_rng(seed)
    if kind == 'standing':
        rings = [(11.0, 8, 0.0, 6.0, 0.55), (8.0, 6, 7.0, 5.4, 0.55), (5.5, 5, 13.5, 4.8, 0.6), (3.0, 4, 19.5, 4.2, 0.6)]
    elif kind == 'toppled':
        rings = [(11.0, 8, 0.0, 6.0, 0.55), (7.5, 6, 6.5, 5.2, 0.5)]
    else:
        rings = [(8.2, 6, 0.0, 4.8, 0.55), (4.2, 4, 5.8, 4.2, 0.6)]
    B.stone_pile(sc, rings, seed, tag='rock', sets=GRANITE, base=2.8, flat=1.9,
                 spill=[(19, 4, 4.2), (25, -3, 3.6), (14, 9, 3.4), (-15, 8, 3.2)] if kind == 'toppled' else None)
    for r, n, z, size, sq in rings:
        _snowcap(sc, -1.0, -0.8, z + size * sq * 1.45, r * 0.8 + 1.5, r * 0.62 + 1.2, th=2.2 if kind != 'toppled' else 3.4,
                 seed=int(z * 7) + seed)
    if kind != 'toppled':
        top = rings[-1][2] + rings[-1][3] * rings[-1][4] * 1.5
        sc.ellipsoid(0.5, -0.5, top + 7.5, 3.0, 2.5, 8.5, GRANITE, base=3.0, k=1.9, tag='rock', mix=0.4, flat=1.7)
        _snowcap(sc, 0.0, -0.5, top + 15.2, 2.8, 2.3, th=2.0, seed=seed + 2)
    else:
        # (round 3, R2-R2) the fallen upright: a long granite stone lying east, its top plane lit
        # with a ledge of snow along it, its dark east end, its foot half buried in a drift
        sc.ellipsoid(25, -2, 4.2, 11.5, 4.2, 4.4, GRANITE, base=3.0, k=1.9, tag='rock', mix=0.4, flat=2.3, tex='stone')
        sc.ellipsoid(23.0, -3.0, 8.3, 8.5, 3.2, 2.6, SNOW, base=3.9, k=1.1, tag='snow', flat=1.6)
        sc.ellipsoid(33, 2.5, 0.2, 7.5, 4.5, 4.2, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)
    _drift_west(sc, -rings[0][0] - 2, 3, 6.0 if kind != 'small' else 4.0, seed)
    del rng
    if kind == 'toppled':
        a = _solo(sc, dress=lambda s, a: _granite_dress(s, a, seed, n_frac=3))
        _grain_after(sc, a, seed)
        return K.crop(a, sc.ox, sc.oy)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)



COURSES = [0, 17, 33, 52, 72, FACE_PX]            # the face's bedding planes (z), the same in every panel

SET_BACK = 3.0                                      # each course stands this far behind the one under it



def _wall_blocks(W, seed, ends):
    """The blocks of one panel (round 5: natural granite, not laid courses): the face split again and
    again at random into joint-bounded blocks of very different sizes (a guillotine split, so joints
    meet in T's and never line up across the face), each set back or leaning by its own amount, its
    top out of level, its corners weathered round; here and there a block is missing, a dark pocket.
    At each panel edge a column of bridge blocks on the shared bedding planes, whose params depend
    only on the plane, so neighbouring panels meet in one block. Each block is (x0, x1, z0, z1,
    y_front, base, mix, round)."""
    rng = np.random.default_rng(seed)
    out = []
    brs = []
    for k in range(len(COURSES) - 1):
        z0, z1 = COURSES[k], COURSES[k + 1]
        br = 14
        brs.append(br)
        bb = 2.75 + 0.35 * (hsh(k, 43) - 0.5)
        bm = hsh(k, 47)
        yf = 2.0 - SET_BACK * k
        if not ends[0]:
            out.append((-br, br - 1, z0, z1 - 1, yf, bb, bm, 9.0))
        if not ends[1]:
            out.append((W - br, W + br - 1, z0, z1 - 1, yf, bb, bm, 9.0))
    lo = (max(brs) if not ends[0] else 2.0)
    hi = (W - max(brs) if not ends[1] else W - 2.0)

    def split(x0, x1, z0, z1, depth):
        w, h = x1 - x0, z1 - z0
        stop = (w < 30 and h < 26 and rng.random() < 0.55) or depth > 7 or (w < 14 and h < 14)
        if not stop:
            vertical = (w > h * 1.8) if rng.random() < 0.75 else (rng.random() < 0.4)
            if vertical and w >= 22:
                c = x0 + w * rng.uniform(0.28, 0.72)
                split(x0, c, z0, z1, depth + 1)
                split(c, x1, z0, z1, depth + 1)
                return
            if h >= 18:
                c = z0 + h * rng.uniform(0.3, 0.7)
                split(x0, x1, z0, c, depth + 1)
                split(x0, x1, c, z1, depth + 1)
                return
        if w * h < 220 and rng.random() < 0.18:
            return                                         # a pocket: the block has weathered out
        u = (z0 + z1) / 2.0 / FACE_PX
        yf = 2.0 - 5 * SET_BACK * u + rng.uniform(-3.0, 1.5)
        base = 2.8 + rng.uniform(-0.4, 0.4) - 0.3 * (z0 < 12)
        out.append((x0, x1 - 1.2, z0, z1 - 1.0 + rng.uniform(-1.5, 1.0), yf, base, rng.random(), rng.uniform(6.0, 10.0)))

    split(lo, hi, 0.0, float(FACE_PX), 0)
    return out



def _face(width, seed, ends=(True, True), fall=None, stair=None):
    """A south-facing granite face `width` texels wide (round 3, R2-F1, after Eastward 12's block
    cliff): stratified granite blocks of 12 to 40 texels on shared bedding planes, each course set a
    little behind the one under it, so every block shows a lit top lip, a front in its own tone and
    a shaded underside where it tucks over the course below; dark joints, fractures, water streaks
    and snow lying on the ledges; a snow lip with thickness hanging over the top, a blue shade under
    it; a dark stony foot with drifts. Blocks run across the panel edges (bridge blocks), so a run of
    panels reads as one face; side ends only where `ends` says. `fall`: (x0, x1) the frozen fall;
    `stair`: (x0, x1) the stair cut up it."""
    rng = np.random.default_rng(seed)
    H = LIP_PX + FACE_PX + 6
    W = width
    zmax = FACE_PX + 40
    sc = K.Scene(0, W, -30, 12, zmax)
    cheeks = ends                                         # (Matt's review of round 3) an end is a stair's cheek
    ends = (False, False)
    blocks = _wall_blocks(W, seed, ends)
    bx0 = 8.0 if ends[0] else -2.0
    bx1 = W - 8.0 if ends[1] else W + 2.0
    spans = [(bx0, bx1)]
    if stair is not None:
        s0, s1 = stair
        # the cheeks: the face's blocks either side of the cut, standing a little proud, ending a
        # tread above the foot
        blocks = [(x0, min(x1, s0 + 2), z0, z1, yf + 3.0, base, mix, rnd) for (x0, x1, z0, z1, yf, base, mix, rnd) in blocks
                  if x0 < s0 - 4 and z0 >= COURSES[1]] + \
                 [(max(x0, s1 - 2), x1, z0, z1, yf + 3.0, base, mix, rnd) for (x0, x1, z0, z1, yf, base, mix, rnd) in blocks
                  if x1 > s1 + 4 and z0 >= COURSES[1]]
        spans = [(bx0, s0 + 1.0), (s1 - 1.0, bx1)]
    # the joints: the rock behind the blocks, dark
    for (j0, j1) in spans:
        sc.box(j0, -30, 0 if stair is None else COURSES[1], j1, -6 - SET_BACK * 5, FACE_PX, [('soot', 'slate_cool', 'slate_cool')],
               base=0.9, k=0.3, tag='joint')
    if stair is not None:
        _stair_steps(sc, stair, seed)
    for (x0, x1, z0, z1, yf, base, mix, rnd) in blocks:
        # (Matt's review of round 3: the pillow stones) an angular granite block on its bedding plane:
        # a flat lit top lip where the course above stands back, a flat front in its own tone, sharp
        # arrises with a texel of chamfer, its top a little out of level
        tilt = (hsh(int(x0), int(z0), 5) - 0.5) * 2.0
        sc.box(x0, yf - 16, z0, x1, yf, z1 + tilt, GRANITE, base=base + 0.1, k=1.9, tag='rock', round_=0.9 + 0.25 * rnd,
               mix=mix)
    # snow on some ledges: where a block stands proud of the one above it
    for k_, (x0, x1, z0, z1, yf, base, mix, rnd) in enumerate(blocks):
        if z1 >= FACE_PX - 1 or x1 - x0 < 10 or hsh(seed, k_, 3) < 0.45:
            continue
        sw = (x1 - x0) * rng.uniform(0.45, 0.8)
        sx = x0 + 1 + rng.uniform(0, max(0.1, (x1 - x0) - sw - 2))
        sc.ellipsoid(sx + sw / 2, yf - 2.5, z1 + 0.6, sw / 2, 2.6, 2.0, SNOW, base=3.9, k=1.1, tag='snow', flat=2.0)
    # the lip: the upper tier's snow running over the top, its front hanging over the face
    top = FACE_PX
    yl = 2.0 - SET_BACK * 5
    lx0 = -4 if not ends[0] else 0
    lx1 = W + 4 if not ends[1] else W
    lips = [(lx0, lx1)] if stair is None else [(lx0, stair[0] + 2), (stair[1] - 2, lx1)]
    for (p0, p1) in lips:
        sc.box(p0, -30, top - 1, p1, yl - 1 + (3.0 if stair is not None else 0.0), top + 4, SNOW, base=3.9, k=1.0, tag='snow',
               round_=1.5)
    n = max(3, W // 12)
    for j in range(n + 1):
        x = W * j / n + rng.uniform(-4, 4)
        r = rng.uniform(7, 12)
        if stair is not None and stair[0] - 4 < x < stair[1] + 4:
            continue
        sc.ellipsoid(x, yl + rng.uniform(-0.5, 1.5), top + 2.5, r, 4.2, 4.2 + rng.uniform(-0.8, 1.2), SNOW, base=3.9, k=1.1,
                     tag='snow', flat=1.6)
    # the foot: talus in front, drifts banked against it
    x = -3.0 if not ends[0] else 4.0
    while x < (W + 3 if not ends[1] else W - 6):
        r = rng.uniform(3, 7)
        if stair is not None and stair[0] - 2 < x + r < stair[1] + 2:
            x += r
            continue
        sc.ellipsoid(x + r, -0.5 + rng.uniform(-1, 1), r * 0.45, r, r * 0.6, r * 0.6, GRANITE, base=2.0 + rng.uniform(-0.3, 0.3),
                     k=1.7, tag='rock', mix=rng.random(), flat=1.8)
        x += r * rng.uniform(1.3, 2.2)
    dp = ndi.gaussian_filter1d(rng.random(W + 20), 5.0, mode='wrap')
    for j in range(0, W + 1, 9):
        h = 2.5 + 7 * (dp[j] - dp.min()) / max(1e-6, dp.max() - dp.min())
        if h > 4.0 and not (stair is not None and stair[0] - 6 < j < stair[1] + 6):
            sc.ellipsoid(j + rng.uniform(-3, 3), 4.5, 0.2, rng.uniform(6, 10), 4.0, h * 0.45, SNOW, base=3.8, k=1.0, tag='drift', flat=1.3)
    sc.render()
    a = sc.shade(crevice=1.6, rim=0.8)
    m = sc.label >= 0
    rockm = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag == 'rock'])
    # the lower courses in the shade of the step (a tone down in the lowest third)
    Y, X = np.mgrid[0:sc.H, 0:sc.W]
    zfoot = sc.oy - 0                                     # canvas row of the ground line
    low = rockm & (Y > zfoot - 30) & (sc.n[..., 2] < 0.6)
    a[low] = (a[low] // 8) * 8 + np.maximum(1, a[low] % 8 - 1)
    # the lit top lips: each block's top plane where the course above stands back, two tones up
    lip_ = rockm & (sc.n[..., 2] > 0.5)
    a[lip_] = np.where(sc.light()[lip_] > 0.6, C('slate', 5), C('slate', 4))
    lip_edge = lip_ & ~np.roll(lip_, -1, 0)
    a[lip_edge] = C('slate_warm', 4)
    # each block's front: lit high where it meets its lip, shaded low where it tucks over the course
    # below (three tones down its height)
    labm = sc.label
    fr = rockm & ~lip_
    run = np.zeros(labm.shape, int)
    for y in range(1, labm.shape[0]):
        run[y] = np.where(fr[y] & (labm[y] == labm[y - 1]), run[y - 1] + 1, 0)
    rev = np.zeros(labm.shape, int)
    for y in range(labm.shape[0] - 2, -1, -1):
        rev[y] = np.where(fr[y] & (labm[y] == labm[y + 1]), rev[y + 1] + 1, 0)
    hi_ = fr & (run <= 1) & (rev > 3)
    a[hi_] = (a[hi_] // 8) * 8 + np.minimum(5, a[hi_] % 8 + 1)
    lo_ = fr & (rev <= 2) & (run > 3)
    a[lo_] = (a[lo_] // 8) * 8 + np.maximum(1, a[lo_] % 8 - 1)
    _fractures(a, rockm & (sc.n[..., 1] > 0.5), seed + 5, n=max(2, W // 30))
    # vertical fractures running down through two or three blocks, and a few dark cracks
    frng = np.random.default_rng(seed + 77)
    for _ in range(max(2, W // 40)):
        x = float(frng.integers(6, W - 6))
        y = float(sc.oy - FACE_PX + frng.integers(4, 30))
        for _j in range(int(frng.integers(28, 60))):
            yi, xi = int(y), int(round(x))
            if not (0 <= yi < sc.H and 1 <= xi < sc.W - 1):
                break
            if rockm[yi, xi]:
                a[yi, xi] = C('slate_cool', 0)
                if rockm[yi, xi - 1]:
                    a[yi, xi - 1] = (a[yi, xi - 1] // 8) * 8 + min(5, a[yi, xi - 1] % 8 + 1)
            y += 1
            x += frng.choice((-1, 0, 0, 0, 1)) * 0.8
    # water streaks: from under some ledges, a darker run down the face
    for j in range(max(2, W // 28)):
        xs_ = int(rng.integers(3, W - 3))
        col = np.nonzero(rockm[:, xs_] & (sc.n[:, xs_, 1] > 0.5))[0]
        if len(col) < 10:
            continue
        y0 = int(col[int(rng.integers(0, len(col) // 2))])
        for yy in range(y0, min(sc.H, y0 + int(rng.integers(6, 16)))):
            for dx in (0, 1) if rng.random() < 0.5 else (0,):
                if rockm[yy, xs_ + dx]:
                    a[yy, xs_ + dx] = C('slate_cool', max(1, a[yy, xs_ + dx] % 8 - 1))
    _snow_light(sc, a)
    if stair is not None:
        _stair_dress(sc, a, stair, seed)
    V.tidy(a)
    K.despeckle(a)
    V.outline(a)
    _grain_after(sc, a, seed, swap=0.3, step=0.04)
    if stair is not None:
        _stair_wear(sc, a, stair, seed)
    # onto the panel's canvas: the ground line at row LIP_PX + FACE_PX - 1
    yf = LIP_PX + FACE_PX
    off = sc.oy - (yf - 1)
    out = np.full((H, W), -1, np.int32)
    src0 = max(0, off)
    out[max(0, -off):max(0, -off) + min(sc.H - src0, H - max(0, -off))] = a[src0:src0 + min(sc.H - src0, H - max(0, -off))]
    # the top rows are the upper tier's snow (the picture meets the ground above it)
    first = np.argmax(out >= 0, axis=0)
    rk = np.isin(out // 8, [FI['slate'], FI['slate_cool'], FI['slate_warm'], FI['iron'], FI['stone_cool'], FI['soot']]) & (out >= 0)
    for x in range(W):
        if stair is not None and stair[0] <= x < stair[1]:
            # the trod coming over the top of the stair: packed snow, a tone cooler, worn grooves
            for y in range(first[x]):
                out[y, x] = C('snow_cool', 4) if hsh(seed, x // 3, y // 2, 11) > 0.22 else (
                    C('snow_cool', 3) if (x + y) % 3 else C('snow', 4))
        elif rk[:LIP_PX + 30, x].any():
            out[:first[x], x] = C('snow', 4)
        else:
            out[:, x] = -1
    for side, on in enumerate(cheeks):
        if on:
            _cheek(out, side, seed)
    # under the foot: the drifts' lower edge, then nothing (the ground below is the zone's)
    prof = ndi.gaussian_filter1d(np.array([hsh(seed, x, 9) for x in range(W)]), 3.0, mode='wrap')
    prof = (prof - prof.min()) / max(1e-6, prof.max() - prof.min())
    for x in range(W):
        out[yf + int(round(2.2 * prof[x])):, x] = -1
    a = out
    V.outline(a)
    if stair is not None:
        _stair_flat(a, stair, seed)
    if fall is not None:
        _icefall(a, fall, seed)
    return V.Pic(W, H, W // 2, yf - 1), a



STEPS = 6

RISE, TREAD = 6.5, 9.5          # (Matt's review of round 3) seen from above a stair is mostly treads

CHEEK = 14



STEP_PX = FACE_PX // STEPS           # 16 rows a step in the picture: a broad tread over a thin riser

RISER_PX = 3



def _cheek(a, side, seed):
    """The face's end where the stair is cut through it (round 5): the face's own stone stepping
    down beside the treads, one weathered block end a step (two where a block spans two), each with
    a lit top level with its tread, a front in shade, a dark joint under it and a rounded outer
    corner; the upper tier's snow on the top block, snow lodged on each step of the cheek."""
    H, W = a.shape
    yf = LIP_PX + FACE_PX
    rng = np.random.default_rng(seed + 61 + side)
    k = 0
    while k < STEPS:
        span = 2 if (rng.random() < 0.35 and k < STEPS - 1) else 1
        y0 = LIP_PX + k * STEP_PX
        y1 = min(yf, y0 + span * STEP_PX)
        wd = CHEEK + int(rng.integers(-2, 3))
        for x in range(W):
            d = x if side == 1 else (W - 1 - x)          # 0 at the picture's edge (the stair side)
            d = (W - 1 - x) if side == 1 else x
            if d >= wd:
                continue
            for y in range(y0, y1):
                r = y - y0
                c = C('slate', 2) if side == 0 else C('slate_cool', 2)
                if r < 3:
                    c = C('slate', 5) if r == 0 else C('slate', 4)          # the lit top, level with the tread
                elif r < 5:
                    c = C('slate', 3)
                elif y == y1 - 1:
                    c = C('slate_cool', 0)                                   # the joint under it
                elif hsh(seed, x // 2, y // 2, side) > 0.86:
                    c = C('slate_cool', 1)
                if d == wd - 1 and r >= 3:
                    c = C('slate_cool', 1) if side == 0 else C('slate', 4)  # the turned outer corner
                if d == wd - 1 and r < 2:
                    continue                                                 # its corner rounded off
                a[y, x] = c
            if hsh(seed, x // 3, k, side) > 0.35 and d < wd - 2:
                a[y0, x] = C('snow', 5)                                      # snow lodged on the step
        k += span
    x0, x1 = (0, CHEEK + 2) if side == 0 else (W - CHEEK - 2, W)
    for x in range(x0, x1):
        top = LIP_PX - 6 + int(round(1.5 * hsh(seed, x // 4, 2)))
        for y in range(max(0, top), LIP_PX):
            a[y, x] = C('snow', 5) if y == top else (C('snow', 4) if y < LIP_PX - 2 else C('snow_cool', 3))



def _stair_flat(a, stair, seed):
    """The stair seen from above (round 5): six broad lit treads, each one calm plane of stone (the
    lightest value), sparse wear, a thin dark riser (three rows, the darkest value) under each; a
    path of packed snow trodden up the middle two or three footprints wide; snow in the back corners
    of every tread. No joints across the treads."""
    s0, s1 = stair
    yf = LIP_PX + FACE_PX
    mid = (s0 + s1) / 2.0
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        y_r = y0 + STEP_PX - RISER_PX
        for x in range(s0, s1):
            for y in range(y0, y_r):
                r = y - y0
                # one calm plane, a shade cooler at its back under the riser above, lightest at its
                # nose; wear in sparse two-texel scuffs and a few granite grains of the same value
                c = C('slate', 5) if r >= 4 else (C('slate_warm', 4) if r >= 1 else C('slate', 3))
                cell = hsh(seed, (x + (y // 2) % 2) // 2, y // 2, k)
                if cell > 0.9:
                    c = C('slate_warm', 4) if r >= 4 else C('slate', 4)      # sparse wear
                elif cell < 0.12 and r >= 4:
                    c = C('slate_warm', 5)
                a[y, x] = c
            a[y_r - 1, x] = C('snow', 5) if hsh(seed, x // 4, k, 4) > 0.55 else C('slate', 5)   # the nose
            for y in range(y_r, min(yf, y0 + STEP_PX)):
                rr = y - y_r
                a[y, x] = C('slate_cool', 1) if rr == 0 else C('slate_cool', 0)
        # snow in the tread's back corners
        for side in (0, 1):
            wl = 10 + int(round(6 * hsh(seed, k, side)))
            for dx in range(wl):
                x = s0 + dx if side == 0 else s1 - 1 - dx
                h = int(round(2 + (wl - dx) * 0.6))
                for r in range(min(h, STEP_PX - RISER_PX - 2)):
                    a[y0 + r, x] = C('snow', 5) if r == 0 else (C('snow', 4) if dx < wl - 2 else C('snow_cool', 4))
        # the trodden path up the middle: packed snow, its edges ragged, footprints in it
        for y in range(y0, y_r):
            wob = 2.5 * math.sin((y + k * 7) / 9.0)
            hw = 14 + 2 * hsh(seed, y // 3, k, 5)
            for x in range(int(mid - hw + wob), int(mid + hw + wob)):
                if s0 <= x < s1:
                    a[y, x] = C('snow_cool', 4) if hsh(seed, x // 2, y // 2, 6) > 0.18 else C('snow', 4)
            if y == y_r - 1:
                for x in range(int(mid - hw + wob), int(mid + hw + wob)):
                    if s0 <= x < s1:
                        a[y, x] = C('snow', 5)
        for j, fx in enumerate((-8, 3, -3, 8)):
            fy = y0 + 2 + (j % 2) * 5
            if fy + 2 < y_r - 1:
                x = int(mid + fx)
                a[fy:fy + 3, x:x + 2] = C('snow_cool', 3)



def _stair_steps(sc, stair, seed):
    """The stair's stones (round 3, R2-F2): six steps, each laid from three to five granite stones of
    their own widths and heights (a texel either way), set back a tread each step up; every stone a
    rounded block, so its nose catches the light and its riser falls into shade."""
    rng = np.random.default_rng(seed + 17)
    s0, s1 = stair
    for k in range(STEPS):
        z1 = RISE * (k + 1)
        yfr = 2.0 - TREAD * k
        x = s0 + 1.0
        while x < s1 - 1:
            w = rng.uniform(30, 62)
            x1 = min(s1 - 1.0, x + w)
            if s1 - 1 - x1 < 20:
                x1 = s1 - 1.0
            sc.box(x, yfr - TREAD - 2.5, max(0.0, z1 - RISE - 6), x1 - 1, yfr + rng.uniform(-0.6, 0.8), z1 + rng.uniform(-0.8, 0.8), GRANITE,
                   base=2.75 + rng.uniform(-0.3, 0.3), k=1.9, tag='step', round_=rng.uniform(1.6, 2.6), mix=rng.random(),
                   tex='stone')
            x = x1



def _stair_dress(sc, a, stair, seed):
    """The steps' snow before the outline: snow lying at the back of each tread and banked into its
    ends against the cheeks; the riser stepping darker toward its foot (four tones)."""
    lab = sc.label
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'step']
    m = np.isin(lab, ids)
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    s0, s1 = stair
    top = m & (sc.n[..., 2] > 0.55)
    front = m & ~top
    # (Matt's review of round 3: the stair read as a brick wall) seen from above each step is a broad
    # lit tread: the stone's top in light greys, a shaded row at its back where the riser above
    # meets it, a lit nose at its front; under the nose a shallow riser in shade, darkest at its foot
    trun = np.zeros((H, W), int)
    for y in range(1, H):
        trun[y] = np.where(top[y], np.where(top[y - 1], trun[y - 1] + 1, 0), 0)
    nose = top & ~np.roll(top, -1, 0)
    g = K.vhash((X + (Y // 2) % 2) // 2, Y // 2, seed + 41)
    a[top] = np.where(g[top] > 0.78, C('slate_warm', 4), np.where(g[top] > 0.55, C('slate', 5), C('slate', 4)))
    a[top & (trun == 0)] = C('slate', 3)
    a[nose] = C('slate', 5)
    run = np.zeros((H, W), int)
    for y in range(1, H):
        run[y] = np.where(front[y], np.where(front[y - 1], run[y - 1] + 1, 0), 0)
    a[front] = np.where(run[front] == 0, C('slate', 3), np.where(run[front] <= 2, C('slate_cool', 2),
                        np.where(run[front] <= 4, C('slate_cool', 1), C('slate_cool', 0))))
    # snow at the back of each tread and in its ends
    for y in range(H):
        row = top[y]
        if not row.any():
            continue
        back = row & ~np.roll(top, 1, 0)[y]
        for x in np.nonzero(back)[0]:
            edge = min(x - s0, s1 - x)
            depth = 3 if edge < 10 else (2 if hsh(seed, x // 5, y) > 0.55 else 0)
            for d_ in range(depth):
                if y + d_ < H and top[y + d_, x]:
                    a[y + d_, x] = C('snow', 5) if d_ == 0 else C('snow_cool', 4)



def _stair_wear(sc, a, stair, seed):
    """After the grain: the trod worn into the middle of each tread (the stone smoothed a tone
    lighter, the grain gone, packed snow in the hollow), the nose lit with snow dust at intervals."""
    lab = sc.label
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'step']
    m = np.isin(lab, ids) & (a >= 0)
    top = m & (sc.n[..., 2] > 0.55)
    s0, s1 = stair
    mid0, mid1 = s0 + (s1 - s0) * 0.3, s1 - (s1 - s0) * 0.3
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    wob = (K.vhash(Y, 3, seed) * 6).astype(int)
    worn = top & (X >= mid0 + wob - 3) & (X < mid1 - wob + 3) & ~np.isin(a // 8, list(SNOWS))
    a[worn] = np.where(K.vhash(X // 3, Y, seed + 2)[worn] > 0.8, C('snow_cool', 3), C('slate', 5))
    # snow banked into each tread's corners against the cheeks, deepest at the back
    rel = np.zeros_like(Y)
    for y in range(1, H):
        rel[y] = np.where(top[y], np.where(top[y - 1], rel[y - 1] + 1, 0), 0)
    lump = (K.vhash(Y // 3, 7, seed) * 5).astype(int)
    corner = top & (((X - s0) < 5 + lump) | ((s1 - X) < 6 + lump))
    a[corner] = np.where(rel[corner] <= 1, C('snow', 5), np.where(X[corner] < (s0 + s1) / 2, C('snow', 4), C('snow_cool', 4)))
    nose = top & ~np.roll(top, -1, 0) & ~np.isin(a // 8, list(SNOWS))
    a[nose] = np.where(K.vhash(X // 4, Y, seed + 3)[nose] > 0.5, C('snow', 5), C('slate', 4))



def rockface(width_cells=6, seed=101, ends=(True, True)):
    pic, a = _face(width_cells * 24, seed, ends=ends)
    pic.a[:] = a
    return pic



def rockface_fall(seed=113):
    """The face where the tarn's outlet comes over it, frozen into a curtain of icicles."""
    pic, a = _face(4 * 24, seed, ends=(False, False), fall=(0, 96))
    pic.a[:] = a
    return pic



def rock_stair(seed=127):
    """The Col Path's stair up the face: five cells (40 world px, over the 34 a stair needs), six
    granite steps with snow-dusted treads, cut through the lip."""
    pic, a = _face(5 * 24, seed, ends=(False, False), stair=(1, 119))
    pic.a[:] = a
    return pic

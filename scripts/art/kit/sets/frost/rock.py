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
from .ground import (
    paint_snow,
    paint_snow_trod,
)
from .water_ice import (
    _icefall,
)



def _boulder_r3(kind='a', seed=43):

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



# ------------------------------------------------------------------------------------------------
# round 7 (A1, the #536 audits of round 1): granite painted in flat planes, its grain in clusters
# ------------------------------------------------------------------------------------------------
# Round 6 shaded the darkest planes in diagonal two-texel dashes (hatching), laid the granite's grain
# as lone texels in warm sibling ramps (terrazzo), stamped the same strip of snow with a comb of
# icicles on every ledge, darkened the foot as an overlay and drew the cheeks and crags as stacked
# blocks. Round 7 shades every plane flat (eastward-edges.md 5.4: dither belongs to light, never to
# a plane), lays the grain in clusters of two to four texels of the stone's own ramp, keeps a lone
# texel only where a line needs it (5.5), and builds crags and boulders from the face's own strata.
GRAIN_SHAPES = (((0, 0), (0, 1)), ((0, 0), (0, 1), (0, 2)), ((0, 0), (0, 1), (1, 1), (1, 2)), ((0, 0), (0, 1), (1, 1)),
                ((0, 0), (0, 1), (0, 2), (0, 3)), ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0), (1, 0)), ((0, 1), (0, 2), (1, 0), (1, 1)))
# (mostly along the beds: marks on a face run across, eastward-edges.md 2.4)


GR_COOL = {'slate': ('slate_warm', 'slate_cool', 'iron'), 'slate_warm': ('slate', 'slate_cool', 'slate'),
           'slate_cool': ('slate', 'iron', 'slate_warm'), 'iron': ('slate_cool', 'slate', 'slate_cool')}     # granite's minerals at one value: the cool ramps only, no brown


def _cgrain(a, m, seed, step=4, p=0.8, lit=None, fleck=0.08, sib=0.0, keep_value=False):
    """Granite's grain in clusters (eastward-edges.md 5.5: detail in clusters of two or more): on a
    grid jittered `step` texels apart, a cluster of two to four texels of the stone's own ramp, a
    tone up on lit planes and a tone down in shade (never toward the next plane's value); here and there a
    feldspar fleck of three or four texels two tones up; with `sib`, that share of the clusters keeps
    its value and takes a sibling cool ramp instead (quartz and hornblende: hue, not noise; with
    `keep_value` only these, so a flat shade keeps its two values). A cluster
    lies on one tone of one plane, or is not laid; it never reaches tone 0, which is for lines."""
    H, W = a.shape
    for gy in range(0, H, step):
        for gx in range(0, W, step):
            if hsh(seed, gx, gy, 1) > p:
                continue
            y = gy + int(hsh(seed, gx, gy, 2) * step)
            x = gx + int(hsh(seed, gx, gy, 3) * step)
            if not (0 <= y < H and 0 <= x < W) or not m[y, x]:
                continue
            base = int(a[y, x])
            shp = GRAIN_SHAPES[int(hsh(seed, gx, gy, 4) * len(GRAIN_SHAPES))]
            pts = [(y + dy, x + dx) for dy, dx in shp
                   if 0 <= y + dy < H and 0 <= x + dx < W and m[y + dy, x + dx] and a[y + dy, x + dx] == base]
            if len(pts) < 2:
                continue
            fb = FI_NAME.get(base // 8)
            if sib and fb in GR_COOL and hsh(seed, gx, gy, 6) < sib:
                g = GR_COOL[fb][int(hsh(seed, gx, gy, 7) * 3)]
                q = hsh(seed, gx, gy, 8)
                up_ = lit is not None and bool(lit[y, x])
                t = int(np.clip(base % 8 + (0 if q < 0.5 or keep_value else (1 if up_ else -1)) + (1 if g == 'iron' else 0), 1,
                                3 if g == 'iron' else 5))                # iron's light end is warm: kept out
                for (yy, xx) in pts:
                    a[yy, xx] = FI[g] * 8 + t
                continue
            up = bool(lit[y, x]) if lit is not None else False
            r = hsh(seed, gx, gy, 5)
            d = 1 if up else -1                                    # a lit plane's grain lighter, a shaded one's darker
            if up and r > 1 - fleck and len(pts) >= 3:
                d = 2
            t = base % 8 + d
            if not 1 <= t <= 5:
                continue
            for (yy, xx) in pts:
                a[yy, xx] = (base // 8) * 8 + t


FI_NAME = {v: k for k, v in FI.items()}


def _unlone(a, m, passes=2):
    """A texel unlike all four of its neighbours (in `m`) takes the commonest of them, on a tie the
    nearest in tone on its own ramp: the picture's lone texels down to what its lines need."""
    H, W = a.shape
    for _ in range(passes):
        p = np.pad(a, 1, constant_values=-9)
        c = p[1:-1, 1:-1]
        ns = (p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:])
        lone = m & (c >= 0) & (c != ns[0]) & (c != ns[1]) & (c != ns[2]) & (c != ns[3])
        for y, x in zip(*np.nonzero(lone)):
            v0 = int(c[y, x])
            vals = [int(n[y, x]) for n in ns if n[y, x] >= 0]
            if not vals:
                continue
            a[y, x] = max(set(vals), key=lambda v: (vals.count(v), -(abs(v % 8 - v0 % 8) + 8 * (v // 8 != v0 // 8))))


def _icicles(out, x0, y0, n, seed, lo=2, hi=6, below=None):
    """A cluster of `n` icicles hanging from row `y0`: each two texels wide (its west texel lit, its
    east in the snow's shade), its own length from `lo` to `hi`, its last row a single lit tip; a
    texel or two of gap between them. Only over `below` (stone) where given."""
    H, W = out.shape
    x = x0
    for j in range(n):
        ln = lo + int(hsh(seed, x0, j, 31) * (hi - lo + 1))
        for r in range(ln):
            y = y0 + r
            for dx in (0, 1):
                xx = x + dx
                if not (0 <= y < H and 0 <= xx < W) or out[y, xx] < 0:
                    continue
                if below is not None and not below[y, xx]:
                    continue
                if r == ln - 1 and dx == 1:
                    continue                                     # the tip: one texel
                out[y, xx] = C('snow', 5) if dx == 0 else C('snow_cool', 3)
        x += 3 + int(hsh(seed, x0, j, 32) * 2)
    return x


def _drift(out, cx, yb, hw, hh, seed, stone=None):
    """A drift banked at a foot, shaded in three planes (the #536 detail audit, finding 5): its lit
    top and west (snow 5), a mid body (snow 4), a blue-grey shade on its lower east (snow 2, its
    deepest corner snow 1); its top wanders a texel at a time, its windward west a little higher; a
    contact row of the stone's shade on the face above it (`stone`)."""
    H, W = out.shape
    wob = 0
    for x in range(int(cx - hw), int(cx + hw) + 1):
        u = (x - cx) / hw
        if abs(u) > 1 or not (0 <= x < W):
            continue
        if hsh(seed, x // 4, 41) > 0.7:
            wob = int(np.clip(wob + (1 if hsh(seed, x, 42) > 0.5 else -1), -1, 1))
        h = hh * (1 - u * u) ** 0.65 * (1.0 + 0.2 * (u < 0)) + wob
        top = int(round(yb - h))
        if top >= yb:
            continue
        for y in range(max(0, top), min(H, yb + 2)):
            v = (y - top) / max(1.0, yb + 1 - top)
            if y == top or (u < -0.15 and v < 0.45):
                c = C('snow', 5) if u < 0.35 else C('snow', 4)
            elif u > 0.62 and v > 0.5:
                c = C('snow', 1)
            elif u > 0.3 and v > 0.35 or u > 0.55:
                c = C('snow', 2)
            else:
                c = C('snow', 4)
            out[y, x] = c
        if stone is not None and top - 1 >= 0 and stone[top - 1, x] and out[top - 1, x] >= 0:
            out[top - 1, x] = C('slate_cool', 1)


BEDS = (16, 34, 54, 75)          # the inner bedding planes, art px under the face's top, at every panel seam
SEAM = 10                        # either side of a seam a plane follows one shared profile, so panels meet
SEAM_BLOCK = 14                  # no joint stands nearer a panel's edge than this
LICHEN = (('grass_warm', 3), ('grass_warm', 2), ('grass', 2))



def _run(lab, axis, rev):
    """Per texel, how many texels of the same block lie before it along `axis` (0 on its edge)."""
    a = np.moveaxis(lab, axis, 0)
    if rev:
        a = a[::-1]
    out = np.zeros(a.shape, np.int32)
    for i in range(1, a.shape[0]):
        out[i] = np.where((a[i] >= 0) & (a[i] == a[i - 1]), out[i - 1] + 1, 0)
    if rev:
        out = out[::-1]
    return np.moveaxis(out, 0, axis)



def _shift(a, sel, d):
    """Step the texels `sel` `d` tones along their own ramp."""
    a[sel] = (a[sel] // 8) * 8 + np.clip(a[sel] % 8 + d, 0, 5)



def _bed_lines(W, seed, fault=False):
    """The inner bedding planes across a panel (the #536 detail audit, finding 13): sheet joints that
    dip east and rise again in gentle folds (1 in 4 to 1 in 7, so no run of one is level for more
    than about seven texels), stepping a texel or two at some joints, entering and leaving every
    panel on one shared profile so the strata run on across the seams; `fault` puts one deliberate
    fault of 4 to 5 texels in the panel."""
    rng = np.random.default_rng(seed + 3)
    xs = np.arange(W)
    lines = []
    S0 = 0.16
    fk = int(rng.integers(0, len(BEDS))) if fault else -1
    for k, e in enumerate(BEDS):
        kx, ky = [0.0, float(SEAM)], [0.0, S0 * SEAM]
        x, y = float(SEAM), S0 * SEAM
        ex, ey = float(W - SEAM), -S0 * SEAM
        dip = rng.random() < 0.6
        faulted = False
        while True:
            L = float(rng.integers(18, 40))
            if ex - (x + L) < 20:
                break
            if y > 3.0:
                dip = False
            elif y < -3.0:
                dip = True
            sl = rng.uniform(0.15, 0.24) if dip else -rng.uniform(0.14, 0.2)
            x += L
            y += sl * L
            kx.append(x)
            ky.append(y)
            if k == fk and not faulted and x > W * 0.3:
                y -= float(rng.integers(4, 6))                # the panel's one fault
                faulted = True
                x += 1.0
                kx.append(x)
                ky.append(y)
            elif rng.random() < 0.3:
                y += float(rng.choice((-2.0, -1.0, 1.0)))     # a small step at a joint
                x += 1.0
                kx.append(x)
                ky.append(y)
            dip = not dip if rng.random() < 0.7 else dip
        d = ey - y
        h = (ex - x) / 2.0
        if h > 2 and abs(d / (2 * h)) < 0.14:
            off = 0.14 * h + abs(d) / 2.0 + 0.5
            kx.append(x + h)
            ky.append(y + d / 2.0 + (off if y + d / 2.0 < 2 else -off))
        kx += [ex, float(W)]
        ky += [ey, 0.0]
        ln = np.round(e + np.interp(xs, kx, ky)).astype(int)
        if lines:
            ln = np.maximum(ln, lines[-1] + 9)
        lines.append(np.minimum(ln, FACE_PX - 12))
    return lines


def _blocks(W, seed, fault=False):
    """The face (FACE_PX x W) split into blocks: the bedding planes and the leaning joints between
    them (each 0.2 to 0.55 off the vertical, kinking once in a tall bed, one in five stopping short
    as a crack). Returns (labels, joints, bed of each texel)."""
    rng = np.random.default_rng(seed + 5)
    lines = _bed_lines(W, seed, fault=fault)
    Y, X = np.mgrid[0:FACE_PX, 0:W]
    joint = np.zeros((FACE_PX, W), bool)
    for ln in lines:
        joint[ln, np.arange(W)] = True
        for x in range(1, W):
            lo_, hi_ = sorted((int(ln[x - 1]), int(ln[x])))
            joint[lo_ + 1:hi_, x] = True                 # a jog: the plane steps at a joint, no gap in it
    bed = np.zeros((FACE_PX, W), np.int32)
    for ln in lines:
        bed += (Y > ln[None, :]).astype(np.int32)
    tops = [np.full(W, -1)] + lines
    bots = lines + [np.full(W, FACE_PX)]
    for k in range(len(tops)):
        x = float(SEAM_BLOCK + rng.integers(2, 14))
        lo = 18 + 5 * k
        while x < W - SEAM_BLOCK - 4:
            xj = int(x)
            s = rng.uniform(0.2, 0.55) * (1 if rng.random() < 0.5 else -1)
            t, b = int(tops[k][xj]), int(bots[k][xj])
            kink = t + (b - t) * rng.uniform(0.35, 0.65) if b - t > 16 and rng.random() < 0.5 else None
            stop = b - int((b - t) * rng.uniform(0.3, 0.5)) if rng.random() < 0.2 else b
            xf = float(xj)
            for y in range(t + 1, stop):
                if kink is not None and y > kink:
                    s2 = -s * 0.6
                    xf += s2
                else:
                    xf += s
                xi = int(round(xf))
                if xi < SEAM_BLOCK - 4 or xi > W - SEAM_BLOCK + 3:
                    break
                if tops[k][xi] < y < bots[k][xi]:
                    joint[y, xi] = True
            x += rng.uniform(lo, lo + 30)
    lab, _n = ndi.label(~joint)
    return lab - 1, joint, bed



def _paint_blocks(W, seed, lab, joint, bed):
    """Each block shaded as a granite ledge by the way its planes face, lit from the upper left
    (the #536 detail audit, findings 1 and 14): its top plane lit and warm (its front arris the
    brightest, its back row in the shade of the block above, its east end a tone down), its front
    at the body's tone 3 with its west arris lit, its east end and its foot a tone down and its last
    row a tone further (the occlusion where it sits on the block below), a big block turned on a
    crease with the plane east of it a tone down. Every plane is flat: no dashes, no dither. A block
    is darker than its neighbours only as a pocket (a block weathered out, in the shade of the one
    above)."""
    a = np.full(lab.shape, -1, np.int32)
    dt, db = _run(lab, 0, False), _run(lab, 0, True)
    dl, dr = _run(lab, 1, False), _run(lab, 1, True)
    # a block cut by the panel's edge runs on into the next panel: its edge there is no arris
    for e, dd in ((0, dl), (W - 1, dr)):
        for b in np.unique(lab[:, e]):
            if b >= 0:
                dd[lab == b] += 60
    Y, X = np.mgrid[0:FACE_PX, 0:W]
    fams = ('slate', 'slate', 'slate_warm', 'slate', 'slate_cool')
    info = {}
    for b, sl in enumerate(ndi.find_objects(lab + 1)):
        if sl is None:
            continue
        m = lab[sl] == b
        k = int(np.median(bed[sl][m]))
        seam = sl[1].start == 0 or sl[1].stop == W
        if seam:
            # a block across a seam is one block in both panels: its looks depend on its bed only
            r = [hsh(k, 71 + j) for j in range(6)]
        else:
            r = [hsh(seed, b, 71 + j) for j in range(6)]
        fam = fams[int(r[0] * len(fams))]
        t0 = 3
        lipd = (3 + int(hsh(seed if not seam else 0, k, 77) * 3) + int(r[2] * 3) - 1) if k > 0 else 1 + int(r[2] * 2)
        w = sl[1].stop - sl[1].start
        pocket = (not seam) and m.sum() < 170 and r[3] < 0.3
        crease = (not seam) and w > 30 and r[4] < 0.7
        info[b] = dict(fam=fam, t0=t0, lipd=lipd, pocket=pocket, seam=seam, k=k, w=w, x0=sl[1].start, y0=sl[0].start)
        ys, xs = np.nonzero(m)
        ys = ys + sl[0].start
        xs = xs + sl[1].start
        t = np.full(len(ys), t0, np.int32)
        f = np.full(len(ys), FI[fam], np.int32)
        _dt, _db, _dl, _dr = dt[ys, xs], db[ys, xs], dl[ys, xs], dr[ys, xs]
        if pocket:
            # a block weathered out: a recess in the shade of the block above, its top rows darkest
            t[:] = 2
            t[_dt <= 2] = 1
            t[_dl <= 1] = 3
        else:
            front = _dt - lipd
            t = np.where((front >= 0) & (_dl <= 1), t0 + 1, t)                 # the lit west arris
            t = np.where((front >= 0) & (_dr <= 2) & (_dl > 1), t0 - 1, t)     # the east end turned away
            t = np.where((front >= 0) & (_db <= 2) & (_dl > 1), t0 - 1, t)     # the foot, toward the block below
            t = np.where((front >= 0) & (_db == 0) & (_dl > 1), t0 - 1, t)     # where it sits (the joint under it is the line)
            if crease:
                # a big block turned on a crease: the plane east of it a tone down, its edge lit
                cx = info[b]['x0'] + w * (0.45 + 0.3 * r[5])
                xc = cx + 0.4 * (ys - info[b]['y0'])
                east = (xs > xc) & (front > 0) & (_db > 2) & (_dr > 2)
                t = np.where(east, t0 - 1, t)
                t = np.where((np.abs(xs - xc) < 0.6) & (front > 0) & (_db > 2), t0 + 1, t)
            top = _dt < lipd
            t = np.where(top, 4, t)
            f = np.where(top, FI[('slate_warm', 'slate_warm', 'slate')[int(r[1] * 3)]], f)
            t = np.where(top & (_dt == 0) & (lipd > 2), 3, t)                  # its back row, under the block above
            arris = _dt == lipd - 1
            t = np.where(arris & (lipd > 1), 5, t)
            f = np.where(arris & (lipd > 1), FI['slate'], f)
            t = np.where(top & (_dr <= 1), 3, t)
        a[ys, xs] = f * 8 + np.clip(t, 0, 5)
    # the joints: dark, the one under a lit lip a tone lighter in runs where it is only a hairline
    a[joint] = C('slate_cool', 0)
    hair = joint & (Y > 0) & (np.roll(a, 1, 1) % 8 >= 3) & (K.vhash(X // 4, Y, seed + 9) > 0.65)
    a[hair] = C('slate_cool', 1)
    return a, info, dict(dt=dt, db=db, dl=dl, dr=dr)


def _ledge_snow(a, lab, info, d, W, seed, stone):
    """Snow lying on the ledges as loads (the #536 detail audit, finding 4): about a third of the
    ledges bare; on the rest a load 1 to 4 rows thick, thickest at its inner corner and tapering to
    its ends, its top lit, its body snow 4, its front row the snow's mid tone, a row of the stone's
    darkest under it; icicles under at most one load in three. Returns the snow's mask."""
    H, Wd = a.shape
    out = np.zeros(a.shape, bool)
    for b, bi in sorted(info.items()):
        if bi['pocket'] or bi['lipd'] < 2 or bi['w'] < 12 or bi['k'] == 0:
            continue
        if hsh(seed, b, 91) < 0.36:
            continue                                               # a bare ledge
        m = (lab == b) & (d['dt'] < bi['lipd'])
        m[:, :SEAM_BLOCK] = False                                  # never across a seam: panels meet in bare stone
        m[:, Wd - SEAM_BLOCK:] = False
        cols = [x for x in np.nonzero(m.any(0))[0]
                if np.ptp(np.nonzero(m[:, x])[0]) + 1 <= bi['lipd'] + 1]   # not on a jog in the plane
        if len(cols) < 10:
            continue
        span = int(len(cols) * (0.4 + 0.5 * hsh(seed, b, 92)))
        span = max(6, span)
        c0i = int((len(cols) - span) * hsh(seed, b, 93))
        run = cols[c0i:c0i + span]
        tmax = 2 + int(hsh(seed, b, 94) * 3)                       # 2 to 4 rows at its deepest
        deep = hsh(seed, b, 95)                                    # where along it the inner corner lies
        for i, x in enumerate(run):
            u = i / max(1, len(run) - 1)
            v = max(0.35, 1.0 - abs(u - deep) / 0.5)
            th = 1 + (tmax - 1) * v
            th = min(th, 1 + 0.8 * min(i, len(run) - 1 - i))     # tapering at its ends
            th = int(np.clip(round(th), 1, 4))
            col = np.nonzero(m[:, x])[0]
            yl = int(col.max())                                    # the ledge's front row
            for j in range(th):
                y = yl - j
                if not 0 <= y < H:
                    continue
                if j == 0:
                    c = C('snow_cool', 3)                          # its front, the mid tone
                elif j == th - 1:
                    c = C('snow', 5)                               # its lit top
                else:
                    c = C('snow', 4)
                a[y, x] = c
                out[y, x] = True
            if yl + 1 < H and stone[yl + 1, x] and not out[yl + 1, x]:
                a[yl + 1, x] = C('slate_cool', 0)                  # the shade under its front
        if hsh(seed, b, 96) < 0.33 and len(run) > 8:
            i = int(len(run) * (0.2 + 0.5 * hsh(seed, b, 97)))
            x = run[i]
            yl = int(np.nonzero(m[:, x])[0].max())
            _icicles(a, x, yl + 2, 1 + int(hsh(seed, b, 98) * 2), seed + b, lo=2, hi=4, below=stone)
    return out


def _lichen(a, info, d, lab, W, seed, avoid):
    """One or two patches of lichen (3 to 6 texels, clustered) on lit fronts, never on a seam block:
    the face's only warm hue (the #536 detail audit, finding 2)."""
    rng = np.random.default_rng(seed + 31)
    cand = [b for b, bi in info.items() if not bi['seam'] and not bi['pocket'] and bi['k'] > 0]
    n = 1 + int(W >= 144)
    shapes = ([(0, 0), (0, 1), (1, 0), (1, 1), (0, 2)], [(0, 0), (0, 1), (1, 1), (1, 2)], [(0, 1), (1, 0), (1, 1), (1, 2), (0, 2), (2, 1)])
    for b in rng.permutation(cand)[:n]:
        bi = info[b]
        m = (lab == b) & (d['dt'] >= bi['lipd'] + 1) & (d['dl'] >= 2) & (d['dr'] >= 4) & (d['db'] >= 3) & ~avoid
        ys, xs = np.nonzero(m)
        if not len(ys):
            continue
        j = int(rng.integers(0, len(ys)))
        y, x = int(ys[j]), int(xs[j])
        f, t = LICHEN[int(rng.integers(0, len(LICHEN)))]
        shape = shapes[int(rng.integers(0, len(shapes)))]
        for dy, dx in shape:
            if 0 <= y + dy < a.shape[0] and 0 <= x + dx < W and m[y + dy, x + dx]:
                a[y + dy, x + dx] = C(f, t if dy > 0 else min(5, t + 1))


def _cornice(W, seed):
    """How far the upper tier's snow hangs over the face, per column: 0 or 1 row in runs of 3 to 8
    (eastward-edges.md 3.1: the lip wobbles a texel; no dark line under it runs ruled), 0 at every
    seam."""
    rng = np.random.default_rng(seed + 41)
    ov = np.zeros(W, int)
    x = SEAM + int(rng.integers(0, 6))
    v = 1
    while x < W - SEAM:
        n = int(rng.integers(3, 9))
        ov[x:min(W - SEAM, x + n)] = v
        v = 1 - v
        x += n
    return ov


def _foot(out, stone, W, seed, yf, sfill, keep_clear=None):
    """The face's foot (the #536 detail audit, finding 5; eastward-edges.md 3.2): a band 2 to 3
    texels deep in the stone's tone 2 (its two values) holding pebbles of 2 to 4 texels; the lower ground's
    snow climbing it 2 to 3 texels on a wandering edge; a few stones fallen to the foot and drifts
    banked against the face, shaded in three planes."""
    rng = np.random.default_rng(seed + 51)
    H = out.shape[0]
    depth = 2
    for x in range(W):
        if hsh(seed, x // 5, 52) > 0.6:
            depth = 3 if depth == 2 else 2
        for y in range(yf - depth, yf):
            if stone[y, x] and out[y, x] >= 0:
                out[y, x] = C('slate_cool', 2) if y >= yf - 2 else (out[y, x] // 8) * 8 + 2
    # pebbles in the band: a lit top-left over a shaded body
    x = int(rng.integers(2, 9))
    while x < W - 4:
        pw = int(rng.integers(2, 5))
        if keep_clear is None or not (keep_clear(x) or keep_clear(x + pw)):
            fam = 'slate' if rng.random() < 0.6 else 'slate_warm'
            for i in range(pw):
                if stone[yf - 2, x + i]:
                    out[yf - 2, x + i] = C(fam, 4 if i == 0 else 3)
                if stone[yf - 1, x + i]:
                    out[yf - 1, x + i] = C(fam, 3 if i == 0 else 2)
        x += pw + int(rng.integers(4, 12))
    # the lower ground's snow climbing the foot
    climb = 1
    for x in range(W):
        if hsh(seed, x // 3, 53) > 0.55:
            climb = int(np.clip(climb + (1 if hsh(seed, x, 54) > 0.45 else -1), 0, 3))
        for y in range(yf - climb, yf):
            if stone[y, x]:
                out[y, x] = sfill[y, x]
    # stones fallen to the foot: angular, a lit top over a front and a shaded east, outlined
    x = SEAM_BLOCK + float(rng.integers(6, 30))
    while x < W - SEAM_BLOCK - 10:
        w = rng.uniform(7, 12) if rng.random() < 0.6 else rng.uniform(12, 17)
        h = w * rng.uniform(0.5, 0.7)
        if keep_clear is not None and (keep_clear(int(x)) or keep_clear(int(x + w))):
            x += w + rng.uniform(20, 40)
            continue
        cx, cy = x + w / 2, yf + 1 - h / 2
        fam = 'slate' if rng.random() < 0.6 else 'slate_warm'
        ys, xs = np.mgrid[int(cy - h / 2) - 1:int(cy + h / 2) + 2, int(x) - 1:int(x + w) + 2]
        dx_, dy_ = (xs + 0.5 - cx) / (w / 2), (ys + 0.5 - cy) / (h / 2)
        r = np.maximum(np.maximum(np.abs(dx_), np.abs(dy_)), (np.abs(dx_) + np.abs(dy_)) / 1.45)
        ins = r <= 1.0
        tp = rng.uniform(-0.3, -0.1)
        tone = np.where(dy_ < tp, np.where(dx_ < 0.3, 5, 4), np.where(dx_ > 0.4, 2, 3))
        rim = ins & ~ndi.binary_erosion(ins)
        ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        for (yy, xx, tt, rr) in zip(ys[ins & ok], xs[ins & ok], tone[ins & ok], rim[ins & ok]):
            out[yy, xx] = C('slate_cool', 0) if rr and not (tt >= 5) else C(fam, tt)
        # a contact shadow east of it on the ground, one row, joined to it
        for xx in range(int(cx), int(x + w) + 3):
            yy = yf + 1
            if 0 <= yy < H and 0 <= xx < W and out[yy, xx] < 0:
                out[yy, xx] = C('snow_cool', 3)
        x += w + rng.uniform(30, 70)
    # drifts banked against the face, two or three a panel, of their own sizes
    x = SEAM_BLOCK + float(rng.integers(0, 24))
    while x < W - SEAM_BLOCK - 10:
        hw = rng.uniform(7, 15)
        hh = rng.uniform(3.5, 8)
        cx = x + hw
        if cx + hw > W - SEAM_BLOCK + 4:
            break
        if keep_clear is None or not (keep_clear(int(cx - hw)) or keep_clear(int(cx + hw))):
            _drift(out, cx, yf, hw, hh, seed + int(x), stone=stone)
        x = cx + hw + rng.uniform(26, 60)


STEP_TREAD, STEP_RISE = 9, 7          # (the #536 audits) nine rows of tread over seven of riser: mostly treads


def _step_rows(k):
    """A step's sixteen rows as (ramp, tone), tread then riser: its back row in the shade of the
    riser above, the lit plane (warm), its nosing (the brightest) and its rounded front; the riser
    under it darkest under the nose, its stone in shade, the contact line at its foot."""
    rows = [('slate_cool', 2) if k > 0 else ('slate', 3), ('slate', 3)] + [('slate_warm', 4)] * 5 + [('slate', 5), ('slate', 4)]
    rows += [('slate_cool', 1), ('slate', 2), ('slate', 2), ('slate', 2), ('slate_cool', 2), ('slate_cool', 1), ('slate_cool', 0)]
    return rows


def _granite_cheek(out, side, seed, stone):
    """The face's end beside the stair (the #536 audits: detail findings 6 and 8, logic finding 1;
    eastward-edges.md 3.3 and 6.1; after the woodland's approved timber stair, #513): a stepped wall
    of two or three granite blocks, the joints at their own heights on each side, ending a tread
    short of the foot. On each step a lit top plane (2 to 3 rows, level with its tread) over a front
    in shade stepping down; the cheek lit on its west side and dark on its east flank; a broken ink
    line where it meets the face's rock (the side band); one chipped corner; snow lodged on some
    steps. Under its end the bottom step runs on out under it (the stair's last tread and riser,
    their lit nosing unbroken from cheek end to cheek end) and the face's foot wraps round it.
    `side` 0 is the piece's west end (the stair lies west: this is the stair's east cheek), 1 its
    east end (the stair's west cheek)."""
    H, W = out.shape
    yf = LIP_PX + FACE_PX
    rng = np.random.default_rng(seed + 61 + side)
    wd = CHEEK
    c_end = LIP_PX + (STEPS - 1) * STEP_PX                         # the last step's top: the cheek ends here

    def X(d):
        return d if side == 0 else W - 1 - d                       # d: 0 at the stair's side
    j1 = LIP_PX + int(rng.integers(1, 3)) * STEP_PX + int(rng.integers(6, 12))
    j2 = j1 + int(rng.integers(2, 3)) * STEP_PX + int(rng.integers(-3, 4))
    joints = [j for j in (j1, j2) if LIP_PX + 4 < j < c_end - 4]
    bf = ('slate', 'slate_warm', 'slate') if side == 0 else ('slate_warm', 'slate', 'slate')

    def block_of(y):
        return sum(1 for j in joints if y > j)
    for k in range(STEPS - 1):
        ya = LIP_PX + k * STEP_PX
        y0_ = ya - 2 if k == 0 else ya
        for y in range(y0_, ya + STEP_PX):
            dd = y - y0_
            r_ = y - ya
            fb = bf[min(2, block_of(y))]
            if dd == 0:
                c = C('slate', 5)                                  # the step's lit edge
            elif r_ < 3:
                c = C('slate_warm', 4)                             # its lit top plane, level with its tread
            elif r_ < STEP_TREAD - 1:
                c = C(fb, 3)                                       # the top turning down to its front
            elif r_ == STEP_TREAD - 1:
                c = C('slate_cool', 2)                             # the shade under its edge
            elif r_ < STEP_TREAD + 3:
                c = C(fb, 2)                                       # its front in shade, beside the riser
            else:
                c = C(fb, 2)
            for d in range(wd):
                out[y, X(d)] = c
                stone[y, X(d)] = True
        # the step's front: a pit or two and a worn texel pair (clusters, never single texels)
        for _ in range(2):
            py = ya + int(rng.integers(5, 12))
            px = int(rng.integers(3, wd - 5))
            out[py, X(px)] = C('slate', 1)
            out[py, X(px + 1)] = C('slate', 1)
            out[py + 1, X(px)] = C('slate_warm', 4)
            out[py + 1, X(px + 1)] = C('slate_warm', 4)
    # the blocks: a texel of joint where one meets the next, the next one's top lit
    for j in joints:
        for d in range(1, wd - 1):
            jj = j + (1 if d >= wd // 2 else 0)                     # the joint jogs a texel halfway across
            out[jj, X(d)] = C('slate_cool', 0)
            t_ = out[jj + 1, X(d)]
            if t_ % 8 < 4:
                out[jj + 1, X(d)] = t_ + 1
    # the flanks: lit on the west, dark on the east (3 texels of side band each side of the cheek),
    # the ink line broken every 4 to 8 rows where it meets the face's rock
    west = [0, 1] if side == 0 else [wd - 2, wd - 3]               # in d, the cheek's west columns
    east = [wd - 3, wd - 2] if side == 0 else [0, 1]
    outer = wd - 1                                                 # the face side (d)
    for y in range(LIP_PX - 2, c_end):
        for d in west:
            if out[y, X(d)] % 8 >= 2 and out[y, X(d)] % 8 < 4:
                out[y, X(d)] = C('slate_warm', 4)
        for d in east:
            if 2 <= out[y, X(d)] % 8 <= 3:
                out[y, X(d)] = C('slate_cool', 2)
    y = LIP_PX - 1
    while y < c_end:
        n = int(rng.integers(4, 9))
        for yy in range(y, min(c_end, y + n)):
            out[yy, X(outer)] = C('slate_cool', 0)
        if y + n < c_end:
            out[y + n, X(outer)] = C('slate', 2)                   # the break in the line
        y += n + 1
    # a chipped corner: a block's corner knocked off, its broken face lit
    ck = int(rng.integers(1, STEPS - 2))
    cy = LIP_PX + ck * STEP_PX
    for (dy, dd_, c) in ((0, 0, C('slate_cool', 1)), (0, 1, C('slate_cool', 1)), (0, 2, C('slate_cool', 1)),
                         (1, 0, C('slate_cool', 1)), (1, 1, C('slate', 2)), (2, 0, C('slate', 5)), (2, 1, C('slate', 5))):
        d = (wd - 2 - dd_) if (ck % 2) else (1 + dd_)
        out[cy + dy, X(d)] = c
    # snow lodged at the back of some steps' tops, of its own length and depth
    for k in range(STEPS - 1):
        if hsh(seed, k, side, 71) < 0.4:
            continue
        ya = LIP_PX + k * STEP_PX
        n = 4 + int(hsh(seed, k, side, 72) * 7)
        d0 = 1 + int(hsh(seed, k, side, 73) * (wd - n - 1)) if wd - n - 1 > 1 else 1
        th = 1 + int(hsh(seed, k, side, 74) * 2)
        for i in range(n):
            d = d0 + i
            tt = th if 0 < i < n - 1 else 1
            for j in range(tt):
                out[ya + tt - 1 - j, X(d)] = C('snow', 5) if j == tt - 1 and tt > 1 else (C('snow_cool', 3) if j == 0 else C('snow', 4))
            out[ya + tt, X(d)] = C('slate_cool', 1)
    # its head: the upper tier's snow turning down over the cheek
    for d in range(wd + 2):
        x = X(d)
        top = LIP_PX - 5 + int(round(1.0 * hsh(seed, d // 4, 2)))
        for y in range(max(0, top), LIP_PX - 1):
            out[y, x] = C('snow', 4) if y > top else C('snow', 5)
        out[LIP_PX - 1, x] = C('snow_cool', 3)
    # under the cheek's end: the bottom step running on out under it, its nosing unbroken
    rows = _step_rows(STEPS - 1)
    for r_, (f_, t_) in enumerate(rows):
        y = c_end + r_
        if y >= yf:
            break
        for d in range(wd):
            c = C(f_, t_)
            if d == wd - 1:
                c = C('slate_cool', 0) if r_ >= STEP_TREAD else C('slate', 2)   # the step's end against the face
            out[y, X(d)] = c
            stone[y, X(d)] = True
    out[c_end - 1, [X(d) for d in range(wd)]] = C('slate_cool', 2)  # the cheek's foot on the step
    # snow drifted into the corner where the cheek ends on the step, a pebble on the tread
    n = 4 + int(rng.integers(0, 5))
    for i in range(n):
        d = wd - 2 - i
        h = max(1, 3 - i // 2)
        for j in range(h):
            out[c_end + j, X(d)] = C('snow', 5) if j == 0 and i < n - 2 else (C('snow', 4) if j < h - 1 else C('snow_cool', 3))
    pd = int(rng.integers(2, 6))
    out[c_end + 4, X(pd)] = C('slate', 5)
    out[c_end + 4, X(pd + 1)] = C('slate', 3)
    out[c_end + 5, X(pd)] = C('slate', 2)
    out[c_end + 5, X(pd + 1)] = C('slate_cool', 1)


def _granite_face(W, seed, cheeks=(False, False)):
    """A south granite face W texels wide on its picture (see the section's notes). Panel seams
    meet: the bedding planes, the lip and the seam blocks are the same at every edge.

    Top to bottom (eastward-edges.md 2.3, 3.1): the upper tier's snow ending in one row a tone
    darker, hanging 0 or 1 row over the face on a wobble of 3 to 8 texels; a 1 px rim line in the
    stone's darkest; the under-lip shade, 4 to 5 rows in two flat values (slate_cool 2 over the
    block's own tone 2, its grain only a sibling hue at the same value); a zone of horizontal
    streaks; the strata; the foot (3.2). Icicles hang from the lip in two or three clusters. No dark
    row runs ruled across the face (forms.masonry_rock): the rim line steps with the lip, and the
    block feet and the foot band keep to tone 2 over the 1 px joints."""
    H = LIP_PX + FACE_PX + 6
    yf = LIP_PX + FACE_PX
    lab, joint, bed = _blocks(W, seed, fault=seed in FAULT_SEEDS)
    face, info, d = _paint_blocks(W, seed, lab, joint, bed)
    out = np.full((H, W), -1, np.int32)
    out[LIP_PX:yf] = face
    rock = np.zeros((H, W), bool)
    rock[LIP_PX:yf] = True
    labf = np.full((H, W), -1, np.int32)
    labf[LIP_PX:yf] = lab
    jointf = np.zeros((H, W), bool)
    jointf[LIP_PX:yf] = joint
    df = {k_: np.zeros((H, W), np.int32) for k_ in d}
    for k_ in d:
        df[k_][LIP_PX:yf] = d[k_]
    Y, X = np.mgrid[0:H, 0:W]
    ov = _cornice(W, seed)
    lipb = LIP_PX + ov                                              # the first row of stone under the lip
    # the under-lip shade's lower edge wanders a texel in long runs
    sh = np.array([5 + int(hsh(seed, x // 7, 43) > 0.55) for x in range(W)])
    u = Y - lipb[None, :]
    fam_ = out // 8
    out[rock & (u == 0)] = C('slate_cool', 0)                       # the rim line on the lip's wobble
    s1 = rock & (u >= 1) & (u < 3) & ~jointf
    out[s1] = C('slate_cool', 2)                                    # the under-lip shade, its darker value
    s2 = rock & (u >= 3) & (u < 1 + sh[None, :]) & ~jointf
    out[s2] = fam_[s2] * 8 + 2                                      # and its lighter
    out[rock & (u < 0)] = -1
    # the zone of horizontal streaks under the shade: marks 2 to 6 texels long, a tone down
    zone = rock & (u >= 1 + sh[None, :]) & (u < 13) & ~jointf & (out % 8 >= 3)
    srng = np.random.default_rng(seed + 44)
    for _ in range(W // 5):
        y = int(srng.integers(LIP_PX + 7, LIP_PX + 13))
        x = int(srng.integers(0, W - 6))
        n = int(srng.integers(2, 7))
        if zone[y, x:x + n].all() and not (zone[y - 1, x:x + n] & (out[y - 1, x:x + n] % 8 < out[y, x:x + n] % 8)).any():
            out[y, x:x + n] = out[y, x:x + n] - 1
    for side, on in enumerate(cheeks):
        if on:
            _granite_cheek(out, side, seed, rock)
    snow = _ledge_snow(out[LIP_PX:yf], lab, info, d, W, seed, rock[LIP_PX:yf])
    snowf = np.zeros((H, W), bool)
    snowf[LIP_PX:yf] = snow
    # granite's grain in clusters, on the stone's planes (not its lines, not the shade under the lip)
    body = rock & (out >= 0) & (out % 8 >= 2) & ~jointf & ~snowf & ~np.isin(out // 8, list(SNOWS)) & (u >= 1 + sh[None, :])
    _cgrain(out, body, seed, step=3, p=0.9, lit=(out % 8 >= 4), sib=0.65, fleck=0.15)
    shade = rock & (u >= 1) & (u < 1 + sh[None, :]) & ~jointf & (out % 8 == 2)
    _cgrain(out, shade, seed + 3, step=3, p=0.8, sib=1.0, keep_value=True)
    _fractures(out, rock & (Y > yf - FACE_PX + 18) & (Y < yf - 12) & (out % 8 >= 2) & ~snowf & ~np.isin(out // 8, list(SNOWS)),
               seed + 5, n=max(1, W // 72))
    _lichen(out, info, {k_: df[k_] for k_ in df}, labf, W, seed, avoid=snowf | (u < 13))
    # the upper tier's snow (the zone's own fill), ending in a row a tone darker on the lip's wobble
    sfill = np.full((H, W), -1, np.int32)
    paint_snow(sfill, np.ones((H, W), bool))
    for x in range(W):
        if cheeks[0] and x < CHEEK + 2 or cheeks[1] and x >= W - CHEEK - 2:
            continue
        for y in range(0, lipb[x]):
            out[y, x] = sfill[y, x] if y < lipb[x] - 1 else C('snow_cool', 3)
    # icicles from the lip: two or three clusters a panel, none near a seam or a cheek
    lo_x = SEAM_BLOCK + (CHEEK + 4 if cheeks[0] else 0)
    hi_x = W - SEAM_BLOCK - 8 - (CHEEK + 4 if cheeks[1] else 0)
    n_cl = 2 + int(W >= 144 and hsh(seed, 61) > 0.3)
    for i in range(n_cl):
        if hi_x <= lo_x:
            break
        span = (hi_x - lo_x) / n_cl
        x = int(lo_x + span * i + span * (0.15 + 0.6 * hsh(seed, i, 62)))
        _icicles(out, x, lipb[x], 2 + int(hsh(seed, i, 63) * 2), seed + 7 * i, lo=2, hi=6, below=rock)
    clear = None
    if cheeks[0] or cheeks[1]:
        def clear(x, c=cheeks):
            return (c[0] and x < CHEEK + 4) or (c[1] and x >= W - CHEEK - 4)
    stone = rock & (out >= 0) & ~np.isin(out // 8, list(SNOWS))
    for side, on in enumerate(cheeks):
        if on:
            x0, x1 = (0, CHEEK) if side == 0 else (W - CHEEK, W)
            stone[:, x0:x1] = False                                  # the bottom step's run under the cheek
    _foot(out, stone, W, seed, yf, sfill, keep_clear=clear)
    # under the foot: the drifts' lower edge, then nothing (the ground below is the zone's)
    prof = ndi.gaussian_filter1d(np.array([hsh(seed, x, 9) for x in range(W)]), 3.0, mode='wrap')
    prof = (prof - prof.min()) / max(1e-6, prof.max() - prof.min())
    for x in range(W):
        out[yf + int(round(2.2 * prof[x])):, x] = -1
    lines_ = (out % 8 == 0) & (out >= 0)
    _unlone(out, (out >= 0) & ~lines_ & (Y >= LIP_PX) & (Y < yf))
    return V.Pic(W, H, W // 2, yf - 1), out


FAULT_SEEDS = {130}                    # the long face's third plain look (plain_c) carries the one deliberate fault


def _granite_stair(W, seed):
    """The Col Path's stair up the face, seen from above (eastward-edges.md 6.1, size guide: six
    steps on a 16 px pitch; the #536 audits, detail findings 7 and 9, logic finding 4): each step a
    tread nine rows deep over a riser of seven (`_step_rows`). Each step is laid from slabs 25 to 70
    texels long whose joints break from step to step (one step a single long slab), each slab a
    texel high or low; every row of the flight is stone (no gaps under a riser). The steps differ:
    a chipped nosing on one, a crack across another, the trod worn lighter up the middle of all.
    Snow lies in loads at the back of the treads against the riser above, of their own lengths and
    depths, and drifts into the cheeks' corners on some steps; the packed trod comes over the top."""
    H = LIP_PX + FACE_PX + 6
    yf = LIP_PX + FACE_PX
    rng = np.random.default_rng(seed + 7)
    out = np.full((H, W), -1, np.int32)
    mid0, mid1 = int(W * 0.36), int(W * 0.64)
    single = int(rng.integers(1, STEPS - 1))                       # the step laid as one long slab
    chip_k, crack_k = int(rng.integers(0, STEPS)), int(rng.integers(0, STEPS))
    if crack_k == chip_k:
        crack_k = (chip_k + 2) % STEPS
    prev = []
    tread_m = np.zeros((H, W), bool)
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        rows = _step_rows(k)
        # the step's slabs: cuts 25 to 70 apart, never within 10 of a joint on the step above
        cuts = []
        if k != single:
            x = 0
            while True:
                w = int(rng.integers(25, 71))
                x += w
                if x > W - 25:
                    break
                for _ in range(6):
                    if all(abs(x - p) >= 10 for p in prev):
                        break
                    x += 11
                if x > W - 25:
                    break
                cuts.append(x)
        prev = cuts
        edges = [0] + cuts + [W]
        for s in range(len(edges) - 1):
            x0, x1 = edges[s], edges[s + 1]
            fam = ('slate', 'slate_warm', 'slate')[int(hsh(seed, k, s, 3) * 3)]
            dy = (0, 0, 1, -1)[int(hsh(seed, k, s, 5) * 4)] if k > 0 else 0
            for x in range(x0, x1):
                for y in range(y0 - (1 if dy < 0 else 0), y0 + STEP_PX):
                    r = int(np.clip(y - y0 - dy, 0, STEP_PX - 1))
                    f, t = rows[r]
                    if f == 'slate_warm' and fam != 'slate':
                        f = fam
                    if x == x0 and x0 > 0:
                        # the joint: a fine dark seam on the tread, a dark one on the riser
                        f, t = ('slate', max(1, t - 2)) if r < STEP_TREAD else ('slate_cool', 0)
                    elif x == x0 + 1 and x0 > 0 and 1 <= r < STEP_TREAD - 2:
                        t = min(5, t + 1)                          # the next slab's lit west end
                    out[y, x] = C(f, t)
                    tread_m[y, x] = 2 <= r < STEP_TREAD - 2
        # the step's own marks
        if k == chip_k:
            cx = int(rng.integers(mid1 + 4, W - 14)) if rng.random() < 0.5 else int(rng.integers(8, mid0 - 6))
            n = int(rng.integers(3, 6))
            out[y0 + STEP_TREAD - 2, cx:cx + n] = C('slate', 2)        # the nosing knocked off
            out[y0 + STEP_TREAD - 1, cx:cx + n] = C('slate_cool', 1)
            out[y0 + STEP_TREAD - 3, cx:cx + n] = C('slate', 5)        # its broken face lit
        if k == crack_k:
            cx = float(rng.integers(mid0 - 10, mid1 + 6))
            for r in range(1, STEP_TREAD - 1):
                xi = int(round(cx))
                out[y0 + r, xi] = C('slate', 1)
                out[y0 + r, xi - 1] = C('slate', 5)
                cx += 0.6
    # every row of the flight is stone
    assert (out[LIP_PX:yf] >= 0).all(), 'a gap in the stair'
    # the trod worn lighter up the middle of each tread, in a lens that wanders step to step
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        c = (mid0 + mid1) / 2 + rng.uniform(-4, 4)
        hw = rng.uniform(9, 14)
        for r in range(3, STEP_TREAD - 2):
            w_ = hw * (1 - ((r - 4.5) / 3.5) ** 2) ** 0.5
            for x in range(int(c - w_), int(c + w_)):
                if out[y0 + r, x] == C('slate_warm', 4) or out[y0 + r, x] == C('slate', 4):
                    out[y0 + r, x] = C('slate', 5)
    # the west cheek shades the west end of each tread (3 texels) and riser (2)
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        for y in range(y0, y0 + STEP_PX):
            n = 3 if y - y0 < STEP_TREAD else 2
            for x in range(n):
                if out[y, x] % 8 >= 1:
                    out[y, x] -= 1
    stone = out >= 0
    stone[:LIP_PX] = False
    Y, X = np.mgrid[0:H, 0:W]
    _cgrain(out, stone & (out % 8 >= 2) & (out % 8 <= 4) & ~((X >= mid0) & (X < mid1) & tread_m), seed, step=3, p=0.9,
            lit=(out % 8 >= 4), sib=0.65)
    # snow: loads at the back of the treads (against the riser above), drifts into the cheeks' corners
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX + (1 if k > 0 else 0)
        for side in (0, 1):
            if hsh(seed, k, side, 8) < 0.3:
                continue                                           # this corner bare
            wl = 5 + int(round(9 * hsh(seed, k, side, 9)))
            hm = 2 + int(round(3 * hsh(seed, k, side, 13)))
            for dx in range(wl):
                x = dx if side == 0 else W - 1 - dx
                h = int(round(hm * math.sqrt(max(0.0, 1 - (dx / wl) ** 2))))
                if h <= 0:
                    continue
                for r in range(max(1, h)):
                    y = y0 + r
                    rim = r == max(1, h) - 1
                    out[y, x] = C('snow_cool', 3) if rim else (C('snow', 5) if r == 0 and dx < wl * 0.6 else C('snow', 4))
                yy = y0 + max(1, h)
                if out[yy, x] % 8 >= 3 and out[yy, x] // 8 not in SNOWS:
                    out[yy, x] -= 1                                # the shade row under it
        x = 10 + int(rng.integers(0, 14))
        while x < W - 16:
            n = int(rng.integers(5, 17))
            if not (mid0 - 4 <= x + n and x <= mid1 + 4) and hsh(seed, x, k, 9) > 0.4:
                th = 1 + int(hsh(seed, x, k, 10) * 2)
                for i in range(n):
                    xx = x + i
                    tt = th if 1 <= i < n - 1 else 1
                    for r in range(tt):
                        out[y0 + r, xx] = C('snow', 5) if r == 0 and tt > 1 else (C('snow_cool', 3) if r == tt - 1 else C('snow', 4))
                    if out[y0 + tt, xx] % 8 >= 3 and out[y0 + tt, xx] // 8 not in SNOWS:
                        out[y0 + tt, xx] -= 1
            x += n + int(rng.integers(10, 26))
    # the trod coming over the top (the zone's own trod fill) between the snow either side, its lone
    # specks cleared, a pair of bootprints in it
    sfill = np.full((H, W), -1, np.int32)
    paint_snow(sfill, np.ones((H, W), bool))
    tfill = np.full((H, W), -1, np.int32)
    paint_snow_trod(tfill, np.ones((H, W), bool))
    for x in range(W):
        for y in range(0, LIP_PX):
            side = x < 12 + int(hsh(seed, y // 3, 15) * 3) or x >= W - 12 - int(hsh(seed, y // 3, 16) * 3)
            c = sfill[y, x] if side else tfill[y, x]
            if y == LIP_PX - 1 and not side:
                c = C('snow_cool', 3)                     # the trod's worn edge over the head tread
            out[y, x] = c
    head = np.zeros((H, W), bool)
    head[:LIP_PX - 1] = True
    out[head & np.isin(out, [C('snow_cool', 2), C('snow_cool', 5)])] = C('snow_cool', 4)   # no specks floating in it
    _unlone(out, head)
    for (fx, fy) in ((int(W * 0.44), 3), (int(W * 0.53), 6)):
        out[fy:fy + 2, fx:fx + 2] = C('snow_cool', 3)
        out[fy, fx] = C('snow_cool', 2)
        out[fy, fx + 1] = C('snow_cool', 2)
    _unlone(out, stone & (out % 8 > 0))
    return V.Pic(W, H, W // 2, yf - 1), out


def _slab(out, stone, x0, yfo, h, dtop, seed, fam='slate', dip=0.0, load=0.0, ledge=False, fissure=False,
          chamfer=1):
    """One slab of the face's strata (the #536 detail audit, findings 10 and 11), its west end at
    column x0 and its foot along the rows `yfo` (one per column, so an upper slab stands on the back
    of the slab under it). Its top dips east by `dip` a column, like the face's beds. Seen from
    the south and above: a top plane `dtop` rows deep (bare rock, lit and warm, its front arris the
    brightest, its back row in the shade where it meets what stands behind), a front at tone 3 with
    its west arris lit, an east flank turned from the light (flat, tone 1), its foot a tone down and
    its last row the occlusion where it sits; `ledge` puts a bedding ledge across a tall front (a
    dark line, the lower bed's lit lip under it), `fissure` one crack down it from its top; `load`
    the share of its top under a load of snow. Paints over what is behind it (draw back to front).
    Returns the rows of its top plane's back edge, per column (for the slab stacked on it)."""
    H, W = out.shape
    w = len(yfo)
    rng = np.random.default_rng(seed)
    xs = np.arange(x0, x0 + w)
    fe = max(3, min(8, w // 6))                                    # the east flank's width
    jag = np.zeros(w, int)
    j_ = 0
    for i in range(w):
        if hsh(seed, i // 6, 81) > 0.75:
            j_ = int(np.clip(j_ + (1 if hsh(seed, i, 82) > 0.5 else -1), -1, 1))
        jag[i] = j_
    ytf = np.array([yfo[i] - h + int(round(dip * i)) + jag[i] for i in range(w)])
    ytb = ytf - dtop + 1
    for i in range(w):
        if i < chamfer:
            ytb[i] += chamfer - i
            ytf[i] += max(0, chamfer - i - 1)
        if i >= w - fe:
            ytb[i] += int(round((i - (w - fe) + 1) * dtop / (fe + 1)))   # the top turning down over the flank
        if i > w - 1 - chamfer:
            ytf[i] += i - (w - 1 - chamfer)
    yl = None
    if ledge:
        hb = int(h * rng.uniform(0.4, 0.6))
        yl = ytf + hb
    xf = None
    if fissure:
        xf = float(x0 + int(w * rng.uniform(0.25, 0.6)))
    # its sides and its foot wander a texel at a time (weathered, never a ruled edge)
    def walk(n, k):
        v, o, c_ = 0, np.zeros(n, int), 0
        for q in range(n):
            if c_ <= 0:
                v = 1 - v
                c_ = 3 + int(hsh(seed, q, k + 1) * 4)
            o[q] = v
            c_ -= 1
        return o
    y_hi = int(ytb.min())
    li, ri, bo = walk(H, 90), walk(H, 92), walk(w, 94)
    m = np.zeros((H, W), bool)
    for i, x in enumerate(xs):
        if not 0 <= x < W:
            continue
        flank = i >= w - fe
        for y in range(max(0, ytb[i]), min(H, yfo[i] + 1 - bo[i])):
            q = y - y_hi
            if (i < li[q] or i > w - 1 - ri[q]) and y > ytf[min(i, w - 1)]:
                continue
            if y <= ytf[i]:
                # the top plane
                if flank:
                    c = C('slate', 3)
                elif y == ytf[i]:
                    c = C('slate', 5)
                elif y == ytb[i] and dtop > 2:
                    c = C('slate', 3)
                else:
                    c = C('slate_warm', 4)
            else:
                t = 3
                if flank:
                    t = 2
                elif i <= 1:
                    t = 4
                if y >= yfo[i] - 1 and not flank:
                    t = 2
                if y == yfo[i] - bo[i]:
                    t = 1
                f = fam if not flank else 'slate_cool'
                c = C(f, t)
                if yl is not None and not flank and i > 1:
                    if y == yl[i]:
                        c = C('slate_cool', 1)                      # the bedding line
                    elif y == yl[i] + 1:
                        c = C('slate', 5)                           # the lower bed's lit lip
                    elif y == yl[i] + 2:
                        c = C('slate_warm', 4)
            out[y, x] = c
            m[y, x] = True
    # one fissure, from the top down to the ledge or the foot, leaning; its west lip lit
    if xf is not None:
        i0 = int(xf - x0)
        y = int(ytf[i0]) + 1
        yend = int(yl[i0]) if yl is not None else int(yfo[i0]) - 2
        x = xf
        while y < yend:
            xi = int(round(x))
            if 0 <= xi < W and m[y, xi]:
                out[y, xi] = C('slate_cool', 0)
                if m[y, xi - 1] and out[y, xi - 1] % 8 < 5:
                    out[y, xi - 1] = C(fam, 4)
            y += 1
            x += 0.35
    # the outline: the stone's darkest, a tone lighter along the lit top where it meets the sky
    edge = m & ~ndi.binary_erosion(m)
    sky = np.zeros_like(m)
    sky[1:] = ~m[:-1]
    out[edge] = C('slate_cool', 0)
    lit_top = edge & sky & (np.arange(W)[None, :] < x0 + w - fe)
    out[lit_top] = C('slate', 2)
    stone |= m
    # a load of snow on part of the top: heaped toward its back and west, its front the snow's mid
    # tone, a shade row on the stone under it
    if load > 0:
        full = hsh(seed, 87) > 0.4                                 # over the whole plane, or a shallow load at its front
        n = max(5, int((w - fe) * (max(load, 0.6) if full else load)))
        s0 = int((w - fe - n) * hsh(seed, 83) * 0.7)
        heap = 1 + int(hsh(seed, 84) > 0.45)                       # rows it heaps above the plane's back
        D0 = dtop - 1 if full else 2 + int(hsh(seed, 88) * 2)
        for i in range(s0, min(w - fe, s0 + n)):
            x = x0 + i
            if not 0 <= x < W:
                continue
            e = min(i - s0, s0 + n - 1 - i)
            # the rows of the plane it covers, from its front: the whole depth in its body (and a row
            # or two heaped over the back toward its west), fewer toward its rounded ends
            v = 1.0 - (i - s0) / max(1, n)
            D = D0 + (heap if full and v > 0.45 and e >= 4 else 0) - int(hsh(seed, x // 5, 89) > 0.8)
            depth = int(max(1, min(D, 1 + 2.0 * e)))
            for j in range(depth):
                y = ytf[i] - j
                if not 0 <= y < H:
                    continue
                if j == 0:
                    c = C('snow', 2) if v < 0.5 else C('snow_cool', 3)   # its front in shade, bluer to the east
                elif j == depth - 1 or (v > 0.6 and j > depth // 2):
                    c = C('snow', 5)                               # its lit top and west
                elif v > 0.3:
                    c = C('snow', 4)
                else:
                    c = C('snow_cool', 3)                          # its east end turning from the light
                out[y, x] = c
            if ytf[i] + 1 < H and m[ytf[i] + 1, x]:
                out[ytf[i] + 1, x] = C('slate_cool', 1)            # the shade under its front
    return ytb


def _mass(out, stone, x0, yb, layers, seed, dip=0.16, loads=(), fissure=-1, chamfer=1):
    """A mass of the face's strata: `layers` from the bottom up, each (dx, w, h, dtop, fam), the one
    above standing on the back of the one under it, set back and stepping (so each shows its own lit
    top as a ledge); drawn top down so each lower bed overlaps the foot of the one above it.
    `loads` the snow on each layer's top (0 bare)."""
    feet = []
    ytbs = []
    for li, (dx, w, h, dtop, fam) in enumerate(layers):
        if li == 0:
            yfo_i = np.full(w, yb)
        else:
            pdx, pw = layers[li - 1][0], layers[li - 1][1]
            xa = x0 + dx
            yfo_i = np.array([ytbs[-1][int(np.clip(xa + i - (x0 + pdx), 0, pw - 1))] for i in range(w)])
        # dry run to find this layer's back edge (for the layer above), then paint top down
        H, W = out.shape
        tmp = np.full((H, W), -1, np.int32)
        ytb = _slab(tmp, np.zeros((H, W), bool), x0 + dx, yfo_i, h, dtop, seed + 17 * li, fam=fam,
                    dip=dip if li == 0 else 0.0, chamfer=chamfer)
        ytbs.append(ytb)
        feet.append(yfo_i)
    for li in range(len(layers) - 1, -1, -1):
        dx, w, h, dtop, fam = layers[li]
        _slab(out, stone, x0 + dx, feet[li], h, dtop, seed + 17 * li, fam=fam, dip=dip if li == 0 else 0.0,
              load=loads[li] if li < len(loads) else 0.0, ledge=(h >= 26), fissure=(li == fissure), chamfer=chamfer)


def _ground_contact(out, stone, seed):
    """Where the rock meets the ground: one row of the ground's shade under the east two thirds of
    each foot, joined to the rock (no stray texels)."""
    H, W = out.shape
    foot = stone & ~np.vstack([stone[1:], np.zeros((1, W), bool)])
    for y, x in zip(*np.nonzero(foot)):
        if y + 1 < H and 0 < x and foot[y, x - 1] and out[y + 1, x] < 0:
            out[y + 1, x] = C('snow_cool', 3)


def _rockpaint(masses, seed, canvas=(260, 190), origin=(130, 170), drifts=(), chips=()):
    """Masses ((x, depth, layers, loads, fissure)) relative to the piece's foot, drawn back to front,
    with its grain in clusters, drifts and the ground's contact; returns a Pic cropped to them."""
    Wc, Hc = canvas
    ox, oy = origin
    out = np.full((Hc, Wc), -1, np.int32)
    stone = np.zeros((Hc, Wc), bool)
    for k, (x, dep, layers, loads, fis) in enumerate(sorted(masses, key=lambda m_: m_[1])):
        _mass(out, stone, ox + x, oy + dep, layers, seed + 101 * k, dip=0.15 + 0.06 * hsh(seed, k, 86), loads=loads, fissure=fis,
              chamfer=2 if len(layers) == 1 and layers[0][1] < 24 else 1)
    for (x, dep, w, h) in chips:
        _slab(out, stone, ox + x, np.full(w, oy + dep), h, max(3, h // 2), seed + 7 * (x + 200), fam='slate_warm', dip=0.15, chamfer=2)
    rock = stone & (out >= 0) & ~np.isin(out // 8, list(SNOWS)) & (out % 8 >= 2)
    inner = rock & ndi.binary_erosion(stone)
    # the fronts' grain keeps their value (so the dark flank and the lit top stay apart), the other planes'
    # steps away from the front's
    _cgrain(out, inner & (out % 8 == 3), seed, step=3, p=0.9, sib=0.7, keep_value=True)
    _cgrain(out, inner & (out % 8 != 3), seed + 1, step=3, p=0.9, lit=(out % 8 >= 4), sib=0.5)
    _unlone(out, stone & (out % 8 > 0) & ndi.binary_erosion(stone))
    for (dx, hw, hh) in drifts:
        _drift(out, ox + dx, oy, hw, hh, seed + dx + 200, stone=stone)
    _ground_contact(out, stone, seed)
    return K.crop(out, ox, oy)


def boulder(kind='a', seed=43):
    """A Frostline granite boulder (round 7, A1: the face's strata as broken slabs, findings 10 and
    11): `a` a block of two beds with a piece split off its east side, `b` a tilted slab on a lower
    block, `large` a big block of two beds with two smaller in its lee and a chip in front; `small`
    the round 2 stone, a cell across."""
    if kind == 'small':
        return _boulder_r3('small', seed)
    if kind == 'a':
        ms = [(-16, -2, [(0, 26, 12, 6, 'slate'), (3, 17, 7, 5, 'slate')], (0.0, 0.6), -1),
              (8, 1, [(0, 13, 8, 5, 'slate_warm')], (0.0,), -1)]
        return _rockpaint(ms, seed, canvas=(90, 70), origin=(45, 60), drifts=[(-17, 5, 3)])
    if kind == 'b':
        ms = [(-18, -1, [(0, 24, 7, 5, 'slate')], (0.0,), -1),
              (-14, -6, [(0, 28, 9, 6, 'slate_warm')], (0.5,), -1),
              (9, 2, [(0, 10, 6, 4, 'slate')], (0.0,), -1)]
        return _rockpaint(ms, seed, canvas=(90, 70), origin=(45, 60))
    ms = [(-34, -10, [(0, 38, 18, 8, 'slate'), (4, 28, 12, 7, 'slate_warm')], (0.0, 0.55), 0),
          (4, -8, [(0, 26, 15, 7, 'slate_warm')], (0.4,), -1),
          (22, 0, [(0, 18, 9, 5, 'slate')], (0.0,), -1)]
    return _rockpaint(ms, seed, canvas=(120, 90), origin=(60, 78), drifts=[(-36, 6, 3.5)])


def crag(kind='a', seed=61):
    """A crag of the headwall's foot (round 7, A1; the #536 detail audit, finding 10): broken slabs
    of the face's own strata dipping east at the face's angle, stacked bed on bed into masses of very
    different sizes (the tall ones behind, low ones stepping down in front), each bed with a lit top
    plane of bare rock, a front at tone 3 and a flat dark east flank, occlusion where one stands on
    another; snow lying as loads on some of the tops; at most one fissure a mass. Its rock keeps
    inside its collision rect (within a few texels; the #536 logic audit, finding 3). The zone's
    north frame (B8, Z1)."""
    if kind == 'a':
        ms = [(-58, -28, [(0, 48, 26, 9, 'slate'), (5, 38, 22, 8, 'slate_warm'), (9, 24, 14, 6, 'slate')], (0.0, 0.5, 0.0), 1),
              (-12, -32, [(0, 56, 30, 10, 'slate_warm'), (4, 46, 26, 9, 'slate'), (10, 30, 18, 7, 'slate_warm')], (0.35, 0.0, 0.6), 0),
              (34, -16, [(0, 38, 26, 9, 'slate'), (6, 24, 16, 7, 'slate')], (0.0, 0.45), -1),
              (-70, -6, [(0, 36, 20, 8, 'slate_warm'), (4, 22, 10, 6, 'slate')], (0.0, 0.0), -1),
              (-28, -2, [(0, 40, 15, 7, 'slate')], (0.4,), -1),
              (18, 0, [(0, 34, 12, 6, 'slate_warm')], (0.0,), -1)]
        return _rockpaint(ms, seed, drifts=[(-72, 8, 4.5), (14, 6, 3)], chips=[(-2, 0, 12, 6)])
    ms = [(-54, -30, [(0, 64, 28, 10, 'slate'), (8, 50, 24, 9, 'slate_warm'), (16, 30, 14, 7, 'slate')],
           (0.0, 0.55, 0.4), 1),
          (10, -24, [(0, 50, 28, 10, 'slate_warm'), (5, 36, 20, 8, 'slate')], (0.3, 0.0), 0),
          (-74, -12, [(0, 32, 18, 8, 'slate'), (3, 20, 10, 6, 'slate_warm')], (0.0, 0.5), -1),
          (40, -10, [(0, 32, 16, 7, 'slate')], (0.0,), -1),
          (-34, -4, [(0, 42, 14, 7, 'slate_warm')], (0.0,), -1),
          (14, 0, [(0, 26, 10, 6, 'slate')], (0.5,), -1)]
    return _rockpaint(ms, seed + 9, drifts=[(-60, 7, 4)], chips=[(-58, 0, 10, 5)])


def rockface(width_cells=6, seed=101, ends=(True, True)):
    # the looks with ends share a seed in FACE_LOOKS: each end of the stair gets its own stone
    pic, a = _granite_face(width_cells * 24, seed + 7 * int(ends[0]) + 19 * int(ends[1]), cheeks=ends)
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
    pic, a = _granite_stair(5 * 24, seed)
    pic.a[:] = a
    return pic

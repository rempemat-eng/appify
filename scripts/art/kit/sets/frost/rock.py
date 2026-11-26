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
    """A cluster of `n` icicles hanging from row `y0` (the snow's own bottom row, so none floats): each
    two texels wide, its west texel lit and its east in the snow's shade (snow 2, so a pair never
    reads as two white ticks), one long and the others short, its last row a single lit tip; a texel
    or two of gap between them. Only over `below` (stone) where given."""
    H, W = out.shape
    x = x0
    for j in range(n):
        if j == 0:
            ln = max(lo, hi - int(hsh(seed, x0, j, 31) * 2))           # the long one
        else:
            ln = lo + int(hsh(seed, x0, j, 31) * 2)                    # the short ones
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
                out[y, xx] = C('snow', 5) if dx == 0 else C('snow', 2)
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
CHEEK2 = 9                        # (the #536 round 2 audits) a cheek 8 to 10 texels wide, in the face's own rock
MAX_RUN = 7                      # no dark line lies level for longer than this (forms.masonry_rock's ruled runs are 9)


# ------------------------------------------------------------------------------------------------
# round 8 (A1, the #536 audits of round 2): the face as a few big tilted masses, not coursed rubble
# ------------------------------------------------------------------------------------------------
# Round 7 split every face into five even beds of 17 to 19 texels, the same rows on all 12 looks,
# each bed into blocks closed all round in the edge tone: at play scale a coursed retaining wall
# (calibration F7, detail N1). Round 8 draws two to four big masses a face, split by deep leaning
# crevices; each mass tilted 3 to 8 degrees its own way, its beds 8 to 28 texels thick, pinching
# out and merging; a bedding joint is a crevice on its shaded (lower) side over the lit top edge of
# the bed below, a vertical joint crosses a bed or two and dies out inside the mass; no block is
# outlined all round. Only at a panel's seam do the beds enter and leave on the shared rows (BEDS),
# so the panels still tile.
def _wobble_line(base, seed, k, pin=()):
    """A crevice's row per column: `base` (floats) plus a wobble of a texel that steps every 3 to 6
    columns, never level for more than MAX_RUN columns (a run that would be is notched a texel for two
    columns, never shifted for good). The columns in `pin` (a panel's seam) keep `base` exactly, so
    neighbouring panels meet on the same rows."""
    n = len(base)
    out = np.zeros(n, int)
    w, c_ = 0, 0
    for i in range(n):
        if c_ <= 0:
            w = int(np.clip(w + (1 if hsh(seed, k, i, 101) > 0.5 else -1), -1, 1))
            c_ = 3 + int(hsh(seed, k, i, 102) * 4)
        c_ -= 1
        out[i] = int(round(base[i])) + w
    pinned = np.zeros(n, bool)
    for (a_, b_) in pin:
        out[a_:b_] = np.round(base[a_:b_]).astype(int)
        pinned[a_:b_] = True
    run = 1
    for i in range(1, n):
        run = run + 1 if out[i] == out[i - 1] else 1
        if run > MAX_RUN and not pinned[i]:
            d = 1 if hsh(seed, k, i, 103) > 0.5 else -1
            for j in range(i, min(n, i + 2)):
                if not pinned[j]:
                    out[j] += d
            run = 1
    return out


def _masses(W, seed, cheeks):
    """The face's masses: the leaning crevices between them (a column per face row for each) and,
    per mass, its bedding crevices as (row per column, first column, last column, deep)."""
    rng = np.random.default_rng(seed + 211)
    n = (3 if rng.random() < 0.6 else 4) if W >= 144 else (2 if rng.random() < 0.5 else 3)
    lo = SEAM_BLOCK + 8 + (CHEEK2 if cheeks[0] else 0)
    hi = W - SEAM_BLOCK - 8 - (CHEEK2 if cheeks[1] else 0)
    xs = None
    for _ in range(200):
        c = sorted(rng.uniform(lo, hi, n - 1))
        wd = np.diff([0.0] + list(c) + [float(W)])
        if wd.min() >= 24 and (W < 144 or 40 <= wd.max() <= 70) and np.diff(c).min(initial=99) >= 24:
            xs = c
            break
    if xs is None:
        xs = list(np.linspace(lo, hi, n + 1)[1:-1])
    bounds = []
    for b, xb in enumerate(xs):
        lean = rng.uniform(0.13, 0.32) * (1 if rng.random() < 0.5 else -1)
        base = xb + lean * (np.arange(FACE_PX) - FACE_PX / 2)
        col = np.zeros(FACE_PX, int)
        w = 0
        for y in range(FACE_PX):
            if hsh(seed, b, y // 5, 105) > 0.7:
                w = int(np.clip(w + (1 if hsh(seed, b, y, 106) > 0.5 else -1), -1, 1))
            col[y] = int(round(base[y])) + w
        bounds.append(col)
    lab = np.zeros((FACE_PX, W), np.int32)
    X = np.arange(W)
    crev = np.zeros((FACE_PX, W), bool)
    for col in bounds:
        lab += (X[None, :] > col[:, None]).astype(np.int32)
        crev[np.arange(FACE_PX), np.clip(col, 0, W - 1)] = True
    beds = []
    for m in range(n):
        cols = np.nonzero((lab == m).any(0))[0]
        x0, x1 = int(cols.min()), int(cols.max())
        s = rng.uniform(0.05, 0.14) * (1 if rng.random() < 0.7 else -1)
        lines = []
        # (the #536 round 3 detail audit, N1 residual) at a seam two of the four shared beds pinch out
        # within 6 to 18 texels, a different two on each side and in each look, so a long run of panels
        # never shows four even beds running on round every seam
        short = set(int(v) for v in rng.permutation(len(BEDS))[:2])
        if m == 0 and not cheeks[0]:
            for j, e in enumerate(BEDS):
                end = int(rng.uniform(SEAM + 6, SEAM + 18)) if j in short else x1
                lines.append((e + s * np.arange(W), 0, min(end, x1), True))
        elif m == n - 1 and not cheeks[1]:
            for j, e in enumerate(BEDS):
                st = W - 1 - int(rng.uniform(SEAM + 6, SEAM + 18)) if j in short else x0
                lines.append((e - s * (W - 1 - np.arange(W)), max(st, x0), W - 1, True))
        else:
            y = float(rng.integers(10, 22))
            xm = (x0 + x1) / 2
            while y < FACE_PX - 14:
                span = x1 - x0
                if rng.random() < 0.35 and span > 30:
                    a_ = int(rng.uniform(x0, x0 + span * 0.5))
                    b_ = int(rng.uniform(a_ + 14, x1 + 1))
                    full = False
                else:
                    a_, b_, full = x0, x1, True
                lines.append((y + s * (np.arange(W) - xm), a_, b_, full))
                y += float(rng.integers(8, 29))
        pin = []
        if m == 0 and not cheeks[0]:
            pin.append((0, SEAM))
        if m == n - 1 and not cheeks[1]:
            pin.append((W - SEAM, W))
        beds.append([(_wobble_line(np.clip(bl, 3, FACE_PX - 8), seed + m, j, pin=pin), a_, b_, deep)
                     for j, (bl, a_, b_, deep) in enumerate(lines)])
    return n, bounds, lab, crev, beds


def _paint_masses(W, seed, cheeks):
    """The face's stone (FACE_PX x W) from its masses; returns the picture, the bedding-crevice mask,
    the deep crevices, the lit ledge rows (for snow) and the mass labels."""
    n, bounds, lab, crev, beds = _masses(W, seed, cheeks)
    a = np.full((FACE_PX, W), -1, np.int32)
    line = np.zeros((FACE_PX, W), bool)
    deepm = np.zeros((FACE_PX, W), bool)
    ledge = np.zeros((FACE_PX, W), np.int32) - 1
    fams = ('slate', 'slate_warm', 'slate', 'slate_cool')
    Y = np.arange(FACE_PX)
    for m in range(n):
        fam = fams[int(hsh(seed, m, 107) * len(fams))]
        for x in range(W):
            ys = Y[lab[:, x] == m]
            if not len(ys):
                continue
            ls = sorted(int(bl[x]) for (bl, a_, b_, deep) in beds[m] if a_ <= x <= b_)
            for (bl, a_, b_, deep) in beds[m]:
                if a_ <= x <= b_ and lab[int(np.clip(bl[x], 0, FACE_PX - 1)), x] == m:
                    line[int(bl[x]), x] = True
                    deepm[int(bl[x]), x] = deep
            left = [b[ys[0]] for b in bounds if b[ys[0]] < x]
            for y in ys:
                above = [v for v in ls if v < y]
                below = [v for v in ls if v > y]
                top = above[-1] if above else -1
                bot = below[0] if below else FACE_PX
                dt, db = y - top - 1, bot - y - 1
                thick = bot - top - 1
                lb = max([b[y] for b in bounds if b[y] < x], default=None)
                rb = min([b[y] for b in bounds if b[y] > x], default=None)
                dl = x - lb - 1 if lb is not None else (x if cheeks[0] else 99)
                dr = rb - x - 1 if rb is not None else ((W - 1 - x) if cheeks[1] else 99)
                f, t = fam, 3
                # each bed graded as a volume (the #536 round 3 detail audit, P4): a lit band under its
                # top edge, lightest toward the mass's west, the body, a darker lower third, the
                # underside; the bands' edges wander a texel, so no tone change runs ruled
                wob = int(hsh(seed, m, x // 5, y // 9, 121) * 3) - 1
                band = 1 + int(round(0.22 * thick)) + wob
                low = thick - int(round(0.34 * thick)) + int(hsh(seed, m, x // 6, y // 9, 122) * 3) - 1
                west = dl / max(1, dl + dr) < 0.6 if (dl < 99 and dr < 99) else hsh(seed, m, x // 9, 123) > 0.4
                if dt == 0 and top >= 0:
                    f, t = 'slate_warm', 4                         # the lit top edge of the bed under a crevice
                elif db <= (2 if thick >= 14 else 1):
                    t = 2                                          # its underside, turning from the light
                elif thick >= 7 and dt < band:
                    f, t = ('slate', 4) if west else ('slate_warm', 3)   # the lit band
                elif thick >= 7 and dt >= low:
                    f, t = 'slate_cool', 3                         # the lower third, a step down
                if dl <= 1 and t != 2:
                    t = 4                                          # the mass's west face, lit
                elif dr <= 2 and dt > 0:
                    t = 2                                          # its east face, in shade
                a[y, x] = C(f, t)
                if dt == 0 and top >= 0:
                    ledge[y, x] = top
            del left
    a[line] = C('slate_cool', 1)
    a[line & deepm] = C('slate_cool', 0)
    a[crev] = C('slate_cool', 0)
    # vertical joints: one now and then, crossing a bed or two and dying out inside the mass, a
    # crevice with its west lip lit
    rng = np.random.default_rng(seed + 223)
    for m in range(n):
        cols = np.nonzero((lab == m).any(0))[0]
        x = int(cols.min()) + int(rng.integers(12, 30))
        while x < cols.max() - 10:
            y0 = int(rng.integers(4, FACE_PX - 30))
            ln = int(rng.integers(10, 30))
            xf = float(x)
            lean = rng.uniform(0.2, 0.4) * (1 if rng.random() < 0.5 else -1)
            for y in range(y0, min(FACE_PX - 6, y0 + ln)):
                xi = int(round(xf))
                if 1 <= xi < W - 1 and lab[y, xi] == m and not line[y, xi] and not crev[y, xi]:
                    a[y, xi] = C('slate_cool', 1)
                    if a[y, xi - 1] % 8 >= 2 and not line[y, xi - 1]:
                        a[y, xi - 1] = (a[y, xi - 1] // 8) * 8 + min(5, a[y, xi - 1] % 8 + 1)
                    # (the #536 round 3 detail audit, P2) it opens wider where it starts and narrows as it
                    # dies out: its upper part two texels, its east wall in shade
                    if y - y0 < 0.45 * ln and lab[y, xi + 1] == m and not line[y, xi + 1] and not crev[y, xi + 1]:
                        a[y, xi + 1] = C('slate_cool', 2)
                xf += lean
            x += int(rng.integers(30, 51))
    return a, line | crev, ledge, lab


def _ledge_loads(out, line, ledge, W, seed, stone, keep_clear=None):
    """Snow on the ledges (the lit top edge under a bedding crevice): about a third of the ledge runs
    bare; on the rest a load 2 to 3 rows deep (never a 1 px line between two dark rows: the #536
    round 3 detail audit, P1), deepest at its inner corner, its back lit, its front row the snow's
    mid tone, a row of the stone's darkest under it; loads under 6 texels are not laid; icicles hang
    from the load's own bottom row under at most one load in six. Returns the snow mask."""
    H, Wd = out.shape
    snow = np.zeros(out.shape, bool)
    lit = ledge >= 0
    lab_, nrun = ndi.label(lit, structure=np.ones((3, 3)))
    for r in range(1, nrun + 1):
        ys, xs = np.nonzero(lab_ == r)
        if xs.max() - xs.min() < 12 or hsh(seed, r, 111) < 0.35:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        x0, x1 = max(x0, SEAM_BLOCK), min(x1, Wd - SEAM_BLOCK - 1)
        if x1 - x0 < 8:
            continue
        span = int((x1 - x0) * (0.4 + 0.45 * hsh(seed, r, 112)))
        if span < 6:
            continue
        s0 = x0 + int((x1 - x0 - span) * hsh(seed, r, 113))
        deep = hsh(seed, r, 114)
        tmax = 2 + int(hsh(seed, r, 115) * 2)
        ths = {}
        col_y = {int(x): int(y) for y, x in zip(ys, xs)}
        for i, x in enumerate(range(s0, s0 + span)):
            if x not in col_y or (keep_clear is not None and keep_clear(x)):
                continue
            u = i / max(1, span - 1)
            th = 1 + (tmax - 1) * max(0.3, 1 - abs(u - deep) / 0.5)
            th = int(np.clip(round(min(th, 2 + 0.8 * min(i, span - 1 - i))), 2, 3))
            y0 = col_y[x]
            ths[x] = th
            for j in range(th):
                y = y0 + j
                if y < H and stone[y, x]:
                    out[y, x] = C('snow', 5) if j == 0 and th > 1 else (C('snow_cool', 3) if j == th - 1 else C('snow', 4))
                    snow[y, x] = True
            if y0 + th < H and stone[y0 + th, x] and not snow[y0 + th, x]:
                out[y0 + th, x] = C('slate_cool', 0)
        if hsh(seed, r, 116) < 0.17 and span > 8:
            x = s0 + int(span * (0.25 + 0.5 * hsh(seed, r, 117)))
            if x in ths and x + 1 in ths:
                _icicles(out, x, col_y[x] + max(ths[x], ths[x + 1]), 2, seed + r, lo=2, hi=4, below=stone & ~snow)
    return snow


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
    """The face's foot (the #536 audits, round 2 item 5; eastward-edges.md 2.5 and 3.2): the lowest
    rows darker than the body, tone 2 over a band of tone 1 two rows deep whose top wanders, holding
    pebbles every 3 to 6 texels (a lit top-left over a shaded body) that break it; the lower ground's
    snow climbing it on a wandering edge, so its lower line is never straight; a few stones fallen to
    the foot; drifts banked against the face in three planes. No pale contact row."""
    rng = np.random.default_rng(seed + 51)
    H = out.shape[0]
    top = 0
    for x in range(W):
        if hsh(seed, x // 4, 52) > 0.55:
            top = int(np.clip(top + (1 if hsh(seed, x, 57) > 0.5 else -1), 0, 2))
        for y in range(yf - 6 - top, yf):
            if not stone[y, x] or out[y, x] < 0 or out[y, x] % 8 == 0:
                continue
            if y >= yf - 2:
                out[y, x] = C('slate_cool', 1)
            elif y >= yf - 4 - top:
                out[y, x] = (out[y, x] // 8) * 8 + min(2, out[y, x] % 8)
            elif out[y, x] % 8 > 2:
                out[y, x] = (out[y, x] // 8) * 8 + 2 if out[y, x] % 8 == 3 else out[y, x] - 1
    # pebbles in the band
    x = int(rng.integers(1, 5))
    while x < W - 3:
        pw = int(rng.integers(2, 4))
        if keep_clear is None or not (keep_clear(x) or keep_clear(x + pw)):
            fam = ('slate', 'slate_warm', 'slate_cool')[int(rng.integers(0, 3))]
            ph = 2 if rng.random() < 0.7 else 3
            for i in range(pw):
                for j in range(ph):
                    y = yf - ph + j
                    if stone[y, x + i]:
                        out[y, x + i] = C(fam, 4 if (i == 0 and j == 0) else (3 if j == 0 or i == 0 else 2))
        x += pw + int(rng.integers(3, 6))
    # the lower ground's snow climbing the foot
    climb = 0
    for x in range(W):
        if hsh(seed, x // 3, 53) > 0.5:
            climb = int(np.clip(climb + (1 if hsh(seed, x, 54) > 0.5 else -1), 0, 2))
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
        tone = np.where(dy_ < tp, np.where(dx_ < 0.3, 5, 4), np.where(dx_ > 0.4, 2, np.where(dy_ > 0.5, 2, 3)))
        rim = ins & ~ndi.binary_erosion(ins)
        ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        for (yy, xx, tt, rr) in zip(ys[ins & ok], xs[ins & ok], tone[ins & ok], rim[ins & ok]):
            out[yy, xx] = C('slate_cool', 0) if rr and not (tt >= 5) else C(fam, tt)
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
    riser above, the lit plane (warm), its nosing (the brightest) and its rounded front; the
    riser under it darkest under the nose, its stone in shade, the contact line at its foot."""
    rows = [('slate_cool', 2) if k > 0 else ('slate', 3), ('slate', 3)] + [('slate_warm', 4)] * 5 + [('slate', 5), ('slate', 4)]
    rows += [('slate_cool', 1), ('slate', 2), ('slate', 2), ('slate', 2), ('slate_cool', 2), ('slate_cool', 1), ('slate_cool', 0)]
    return rows


def _granite_cheek(out, side, seed, stone):
    """The face's end beside the stair (the #536 round 2 audits, items 6 and 8; eastward-edges.md 3.3
    and 6.1: the cheeks carry the face's rock down beside the steps): the face's own masses and beds
    run on to the piece's end, and over its last CHEEK2 texels they step down with the flight, each
    step a lit top 3 rows deep (granite 5 then 4) with the shade of its edge under it. The side toward
    the stair is shaded by its facing (the east cheek's faces west: lit; the west cheek's faces east:
    in shade); where the cheek meets the face a crevice broken every 4 to 8 rows; one chipped corner;
    snow on some of the steps. The cheek ends a tread short of the foot, and the bottom step runs on
    under it. `side` 0 is the piece's west end (the stair lies west: the stair's east cheek), 1 its
    east end (the stair's west cheek)."""
    H, W = out.shape
    yf = LIP_PX + FACE_PX
    rng = np.random.default_rng(seed + 61 + side)
    wd = CHEEK2
    c_end = LIP_PX + (STEPS - 1) * STEP_PX

    def X(d):
        return d if side == 0 else W - 1 - d                       # d: 0 at the stair's side
    for k in range(STEPS - 1):
        ya = LIP_PX + k * STEP_PX
        for d in range(wd):
            out[ya, X(d)] = C('slate', 5)
            out[ya + 1, X(d)] = C('slate_warm', 4)
            out[ya + 2, X(d)] = C('slate_warm', 4)
            out[ya + 3, X(d)] = C('slate_cool', 2)
            for y in range(ya, ya + STEP_PX):
                stone[y, X(d)] = True
    # the side toward the stair, by its facing; on each step its own stone, a tone down in its lower
    # half (the #536 round 3 detail audit, P3: no full-height strip of one tone)
    tones = ((('slate_warm', 4), ('slate_warm', 3)), (('slate', 4), ('slate', 3))) if side == 0 else \
            ((('slate_cool', 2), ('slate_cool', 1)), (('slate', 2), ('slate_cool', 2)))
    for y in range(LIP_PX, c_end):
        r_ = (y - LIP_PX) % STEP_PX
        if r_ < 4:
            continue
        k = (y - LIP_PX) // STEP_PX
        hi_, lo_ = tones[(k + side) % 2]
        for d in (0, 1):
            t_ = out[y, X(d)]
            if t_ < 0 or t_ % 8 == 0:
                continue
            out[y, X(d)] = C(*(hi_ if r_ < 9 + int(hsh(seed, k, d, side, 75) * 2) else lo_))
    # where the cheek meets the face: a crevice broken every 4 to 8 rows
    y = LIP_PX + 4
    while y < c_end:
        n = int(rng.integers(4, 9))
        for yy in range(y, min(c_end, y + n)):
            if (yy - LIP_PX) % STEP_PX >= 3:
                out[yy, X(wd)] = C('slate_cool', 0)
        y += n + 1 + int(rng.integers(0, 2))
    # chipped corners on three of the steps, toward the stair, their broken faces lit
    for ck in sorted(int(v) for v in rng.permutation(STEPS - 1)[:3]):
        cy = LIP_PX + ck * STEP_PX
        for (dy, dd_, c) in ((0, 0, C('slate_cool', 1)), (0, 1, C('slate_cool', 1)), (1, 0, C('slate_cool', 1)),
                             (0, 2, C('slate', 2)), (1, 1, C('slate', 2)), (2, 0, C('slate', 5)), (2, 1, C('slate', 5))):
            out[cy + dy, X(dd_)] = c
    # snow lodged on some steps, of its own length
    for k in range(STEPS - 1):
        if hsh(seed, k, side, 71) < 0.5:
            continue
        ya = LIP_PX + k * STEP_PX
        n = 3 + int(hsh(seed, k, side, 72) * 4)
        d0 = int(hsh(seed, k, side, 73) * (wd - n))
        for i in range(n):
            out[ya + 1, X(d0 + i)] = C('snow', 5) if 0 < i < n - 1 else C('snow', 4)
            out[ya + 2, X(d0 + i)] = C('snow_cool', 3)
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
    n = 3 + int(rng.integers(0, 4))
    for i in range(n):
        d = wd - 2 - i
        h = max(1, 3 - i // 2)
        for j in range(h):
            out[c_end + j, X(d)] = C('snow', 5) if j == 0 and i < n - 2 else (C('snow', 4) if j < h - 1 else C('snow_cool', 3))
    pd = int(rng.integers(1, 3))
    out[c_end + 4, X(pd)] = C('slate', 5)
    out[c_end + 4, X(pd + 1)] = C('slate', 3)
    out[c_end + 5, X(pd)] = C('slate', 2)
    out[c_end + 5, X(pd + 1)] = C('slate_cool', 1)


def _granite_face(W, seed, cheeks=(False, False)):
    """A south granite face W texels wide on its picture (round 8: see the section's note). Panel
    seams meet: the beds' rows at a seam and the lip are the same at every edge.

    Top to bottom (eastward-edges.md 2.3, 3.1): the upper tier's ground is the zone's own, so the
    picture is clear above its lip (the #536 round 2 detail audit, N2); the lip, one row of snow a
    tone darker than the field, on a wobble of 0 or 1 row in runs of 3 to 8; a 1 px rim line in the
    stone's darkest; the under-lip shade in two flat values (slate_cool 2 over the stone's tone 2,
    its lower edge wandering 1 to 2 rows); the masses; the foot, darker than the body. Icicles hang
    in two or three clusters where the lip overhangs. No dark row runs ruled across the face
    (forms.masonry_rock): every crevice steps within MAX_RUN texels."""
    H = LIP_PX + FACE_PX + 6
    yf = LIP_PX + FACE_PX
    face, linem, ledge, labm = _paint_masses(W, seed, cheeks)
    out = np.full((H, W), -1, np.int32)
    out[LIP_PX:yf] = face
    rock = np.zeros((H, W), bool)
    rock[LIP_PX:yf] = True
    linef = np.zeros((H, W), bool)
    linef[LIP_PX:yf] = linem
    ledgef = np.full((H, W), -1, np.int32)
    ledgef[LIP_PX:yf] = np.where(ledge >= 0, ledge + LIP_PX, -1)
    Y, X = np.mgrid[0:H, 0:W]
    ov = _cornice(W, seed)
    lipb = LIP_PX + ov                                              # the first row of stone under the lip
    sh = np.zeros(W, int)
    v, c_ = 5, 0
    for x in range(W):
        if c_ <= 0:
            v = 4 + int(hsh(seed, x, 43) * 3)                       # 4 to 6 rows, wandering every 8 to 20
            c_ = 8 + int(hsh(seed, x, 44) * 13)
        sh[x] = v
        c_ -= 1
    u = Y - lipb[None, :]
    fam_ = out // 8
    out[rock & (u == 0)] = C('slate_cool', 0)                       # the rim line on the lip's wobble
    s1 = rock & (u >= 1) & (u < 3) & ~linef
    out[s1] = C('slate_cool', 2)                                    # the under-lip shade, its darker value
    # (the #536 round 3 audits) its top two rows at tone 1 over about 70 % of the width, in runs of 3 to
    # 6 broken by 2 to 3 texels of tone 2 (a run of 9 would read as a ruled joint, forms.masonry_rock)
    for uu in (1, 2):
        x, on = int(hsh(seed, uu, 45) * 4), True
        while x < W:
            n = (3 + int(hsh(seed, uu, x, 46) * 4)) if on else (2 + int(hsh(seed, uu, x, 47) * 2))
            if on:
                for xx in range(x, min(W, x + n)):
                    y = lipb[xx] + uu
                    if rock[y, xx] and not linef[y, xx]:
                        out[y, xx] = C('slate_cool', 1)
            x += n
            on = not on
    s2 = rock & (u >= 3) & (u < 1 + sh[None, :]) & ~linef
    out[s2] = np.where(fam_[s2] >= 0, fam_[s2], FI['slate']) * 8 + 2   # and its lighter
    out[rock & (u < 0)] = -1
    ledgef[u < 1 + sh[None, :]] = -1
    # the zone of horizontal streaks under the shade: marks 2 to 6 texels long, a tone down
    zone = rock & (u >= 1 + sh[None, :]) & (u < 13) & ~linef & (out % 8 >= 3)
    srng = np.random.default_rng(seed + 44)
    for _ in range(W // 6):
        y = int(srng.integers(LIP_PX + 7, LIP_PX + 13))
        x = int(srng.integers(0, W - 6))
        n = int(srng.integers(2, 7))
        if zone[y, x:x + n].all():
            out[y, x:x + n] = out[y, x:x + n] - 1
    for side, on in enumerate(cheeks):
        if on:
            _granite_cheek(out, side, seed, rock)
            x0, x1 = (0, CHEEK2 + 1) if side == 0 else (W - CHEEK2 - 1, W)
            ledgef[:, x0:x1] = -1
    clear = None
    if cheeks[0] or cheeks[1]:
        def clear(x, c=cheeks):
            return (c[0] and x < CHEEK2 + 4) or (c[1] and x >= W - CHEEK2 - 4)
    stone = rock & (out >= 0)
    snowf = _ledge_loads(out, linef, ledgef, W, seed, stone, keep_clear=clear)
    # granite's grain in clusters: the body keeps its value (a sibling hue), the lit and shaded planes
    # step away from it (the #536 round 2 audit: one step, never L89 against L119)
    gr = rock & (out >= 0) & ~linef & ~snowf & ~np.isin(out // 8, list(SNOWS)) & (u >= 1 + sh[None, :]) & (out % 8 > 0)
    _cgrain(out, gr & (out % 8 == 3), seed, step=3, p=0.9, sib=0.85, keep_value=True)
    _cgrain(out, gr & (out % 8 != 3), seed + 1, step=3, p=0.85, lit=(out % 8 >= 4), sib=0.5)
    shade = rock & (u >= 1) & (u < 1 + sh[None, :]) & ~linef & (out % 8 == 2)
    _cgrain(out, shade, seed + 3, step=3, p=0.8, sib=1.0, keep_value=True)
    # the lip: one row of snow a tone darker than the field, on the wobble; clear above it (the zone's
    # own snow runs to it)
    for x in range(W):
        if cheeks[0] and x < CHEEK2 or cheeks[1] and x >= W - CHEEK2:
            out[LIP_PX - 1, x] = C('snow_cool', 3)
            continue
        out[lipb[x] - 1, x] = C('snow_cool', 3)
    # icicles where the lip overhangs: two or three clusters a panel, none near a seam or a cheek
    lo_x = SEAM_BLOCK + (CHEEK2 + 4 if cheeks[0] else 0)
    hi_x = W - SEAM_BLOCK - 8 - (CHEEK2 + 4 if cheeks[1] else 0)
    n_cl = 2 + int(W >= 144 and hsh(seed, 61) > 0.3)
    for i in range(n_cl):
        if hi_x <= lo_x:
            break
        span = (hi_x - lo_x) / n_cl
        x = int(lo_x + span * i + span * (0.15 + 0.6 * hsh(seed, i, 62)))
        over = [xx for xx in range(x - 6, x + 7) if 0 <= xx < W - 8 and ov[xx] == 1 and ov[min(W - 1, xx + 6)] == 1]
        if over:
            x = over[0]
        _icicles(out, x, lipb[x], 2 + int(hsh(seed, i, 63) * 2), seed + 7 * i, lo=2, hi=6, below=rock)
    stone = rock & (out >= 0) & ~np.isin(out // 8, list(SNOWS))
    for side, on in enumerate(cheeks):
        if on:
            x0, x1 = (0, CHEEK2) if side == 0 else (W - CHEEK2, W)
            stone[LIP_PX + (STEPS - 1) * STEP_PX:, x0:x1] = False   # the bottom step's run under the cheek
    sfill = np.full((H, W), -1, np.int32)
    paint_snow(sfill, np.ones((H, W), bool))
    _foot(out, stone, W, seed, yf, sfill, keep_clear=clear)
    # under the foot: the drifts' lower edge, then nothing (the ground below is the zone's)
    prof = ndi.gaussian_filter1d(np.array([hsh(seed, x, 9) for x in range(W)]), 3.0, mode='wrap')
    prof = (prof - prof.min()) / max(1e-6, prof.max() - prof.min())
    for x in range(W):
        out[yf + int(round(2.2 * prof[x])):, x] = -1
    lines_ = (out % 8 == 0) & (out >= 0)
    _unlone(out, (out >= 0) & ~lines_ & (Y >= LIP_PX) & (Y < yf))
    return V.Pic(W, H, W // 2, yf - 1), out


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
    crack_k = single if chip_k != single else crack_k             # the long slab cracked across (no lit band runs 40 texels)
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
    # the worn middle keeps its value, its grain only a sibling hue; chips and pits along each tread
    _cgrain(out, stone & (X >= mid0) & (X < mid1) & tread_m & (out % 8 >= 3), seed + 5, step=3, p=0.7, sib=1.0, keep_value=True)
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        for _ in range(4):
            cx = int(rng.integers(6, W - 8))
            cy = y0 + int(rng.integers(2, STEP_TREAD - 3))
            if mid0 - 3 <= cx <= mid1 + 3 or not stone[cy, cx]:
                continue
            out[cy, cx:cx + 2] = C('slate', 2)                     # a pit: a dark pair over a lit one
            out[cy + 1, cx:cx + 2] = C('slate_warm', 5)
    # snow: loads at the back of the treads (against the riser above), drifts into the cheeks' corners
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX + (1 if k > 0 else 0)
        for side in (0, 1):
            if (k + 3 * side) % 3 == 1:
                continue                                           # a third of the corners bare (4 of 12)
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
    # above the head the zone's own ground runs to it (the #536 round 2 detail audit, N2): only the
    # trod's worn edge, one row a tone darker, belongs to the stair
    out[:LIP_PX - 1] = -1
    out[LIP_PX - 1] = C('snow_cool', 3)
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
    prev = out.copy()
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
                # the front graded down its height (the #536 round 2 audits: no one-tone crate fronts):
                # lit at its top-left, the body, a darker lower part, the underside darkest
                r = (y - ytf[i]) / max(1.0, yfo[i] - bo[i] - ytf[i])
                t = 3
                if flank:
                    t = 2
                elif r >= 0.62:
                    t = 2
                elif i <= 1 or (i < max(3, w * 0.28) and r < 0.35):
                    t = 4
                if y >= yfo[i] - bo[i] - 1 and not flank:
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
    # no texel standing alone on the silhouette (the #536 round 2 detail audit, N6: spikes on the tops)
    for _ in range(2):
        nb = np.zeros((H, W), int)
        nb[1:] += m[:-1]
        nb[:-1] += m[1:]
        nb[:, 1:] += m[:, :-1]
        nb[:, :-1] += m[:, 1:]
        lone_ = m & (nb <= 1)
        out[lone_] = prev[lone_]
        m &= ~lone_
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
        s0 = max(chamfer + 1, int((w - fe - n) * hsh(seed, 83) * 0.7))   # never on the chamfered corner (P5)
        while s0 + 2 < w - fe and not (ytf[s0] == ytf[s0 + 1] == ytf[s0 + 2]):
            s0 += 1                                                # nor where its edge steps: it starts on a level run
        D0 = dtop - 2 if full else 2 + int(hsh(seed, 88) * 2)
        for i in range(s0, min(w - fe, s0 + n)):
            x = x0 + i
            if not 0 <= x < W:
                continue
            e = min(i - s0, s0 + n - 1 - i)
            # the rows of the plane it covers, from its front: the plane's depth along its body, following
            # the slab's dip (no dome: the #536 round 2 detail audit, N7), fewer toward its ends
            v = 1.0 - (i - s0) / max(1, n)
            D = D0 - int(hsh(seed, x // 5, 89) > 0.8)
            depth = int(max(1, min(D, 2 + 3 * e)))
            for j in range(depth):
                y = ytf[i] - j
                if not 0 <= y < H or not m[y, x]:
                    continue                                       # inside the stone's outline only
                if j == 0:
                    c = C('snow', 2) if v < 0.5 else C('snow_cool', 3)   # its front in shade, bluer to the east
                elif j == depth - 1 or (v > 0.6 and j > depth // 2):
                    c = C('snow', 5)                               # its lit top and west
                elif v > 0.3:
                    c = C('snow', 4)
                else:
                    c = C('snow_cool', 3)                          # its east end turning from the light
                out[y, x] = c
            if ytf[i] + 1 < H and m[ytf[i] + 1, x] and (e > 0 or depth > 1):
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


def _rockpaint(masses, seed, canvas=(260, 190), origin=(130, 170), drifts=(), chips=(), chamfer=None):
    """Masses ((x, depth, layers, loads, fissure)) relative to the piece's foot, drawn back to front,
    with its grain in clusters and drifts; returns a Pic cropped to them. No pale contact row under
    the feet (the #536 round 2 audits, detail N3 and logic N1): the outline and the piece's shadow
    carry the contact."""
    Wc, Hc = canvas
    ox, oy = origin
    out = np.full((Hc, Wc), -1, np.int32)
    stone = np.zeros((Hc, Wc), bool)
    for k, (x, dep, layers, loads, fis) in enumerate(sorted(masses, key=lambda m_: m_[1])):
        _mass(out, stone, ox + x, oy + dep, layers, seed + 101 * k, dip=0.15 + 0.06 * hsh(seed, k, 86), loads=loads, fissure=fis,
              chamfer=chamfer or (2 if len(layers) == 1 and layers[0][1] < 24 else 1))
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
        return _rockpaint(ms, seed, canvas=(90, 70), origin=(45, 60), chamfer=2)
    if kind == 'b':
        ms = [(-18, -1, [(0, 24, 7, 5, 'slate')], (0.0,), -1),
              (-14, -6, [(0, 28, 9, 6, 'slate_warm')], (0.5,), -1),
              (9, 2, [(0, 10, 6, 4, 'slate')], (0.0,), -1)]
        return _rockpaint(ms, seed, canvas=(90, 70), origin=(45, 60), drifts=[(-20, 4, 2.5)], chamfer=2)
    ms = [(-34, -10, [(0, 38, 20, 8, 'slate'), (4, 28, 11, 7, 'slate_warm'), (9, 15, 6, 5, 'slate')], (0.0, 0.55, 0.0), 0),
          (4, -8, [(0, 26, 13, 7, 'slate_warm'), (4, 16, 7, 5, 'slate')], (0.0, 0.5), 1),
          (22, 0, [(0, 18, 9, 5, 'slate')], (0.0,), -1),
          (-24, 2, [(0, 12, 6, 4, 'slate_warm')], (0.0,), -1)]
    return _rockpaint(ms, seed, canvas=(120, 90), origin=(60, 78), drifts=[(30, 4, 3)], chamfer=2)


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
        return _rockpaint(ms, seed, drifts=[(-70, 9, 5)], chips=[(-2, 0, 12, 6)])
    ms = [(-54, -30, [(0, 64, 28, 10, 'slate'), (8, 50, 24, 9, 'slate_warm'), (16, 30, 14, 7, 'slate')],
           (0.0, 0.55, 0.4), 1),
          (10, -24, [(0, 50, 28, 10, 'slate_warm'), (5, 36, 20, 8, 'slate')], (0.3, 0.0), 0),
          (-74, -12, [(0, 32, 18, 8, 'slate'), (3, 20, 10, 6, 'slate_warm')], (0.0, 0.5), -1),
          (40, -10, [(0, 32, 16, 7, 'slate')], (0.0,), -1),
          (-44, -1, [(0, 50, 14, 7, 'slate_warm')], (0.0,), -1),
          (14, 0, [(0, 26, 10, 6, 'slate')], (0.5,), -1)]
    return _rockpaint(ms, seed + 9, chips=[(-58, 0, 10, 5)])


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

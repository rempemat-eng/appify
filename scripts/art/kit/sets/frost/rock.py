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
    _grain,
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

# ------------------------------------------------------------------------------------------------
# round 6 (A1): boulders and crags as the face's granite, painted texel by texel
# ------------------------------------------------------------------------------------------------
def _gblock(out, own, x0, yb, w, hf, dtop, seed, fam='slate', snow=1.0, tilt=0, crease=True):
    """One granite block seen from the south and above, its foot's west corner at (x0, yb): a top
    plane `dtop` rows deep (lit, warm, its back row cooler, its front arris the brightest), a front
    `hf` rows tall (lit at its west arris, a tone down past a crease, darker to its foot), the
    corners knocked off in 1 x 1 chamfers; its outline in the stone's edge tone, lighter along the lit
    top; a snow cap on the top plane heaped west, hanging a texel over the arris with the blue shade
    row under it. `tilt` lifts the top's east end. Paints over what is behind it (draw back to
    front); `own` gets the block's id."""
    rng = np.random.default_rng(seed)
    H, W = out.shape
    bid = int(own.max()) + 1
    xs = np.arange(x0, x0 + w)
    u = (xs - x0) / max(1, w - 1)
    # the top's line wanders in single steps (a weathered arris, never a ruled edge)
    jag = np.zeros(w)
    j_, run_ = 0.0, 0
    for i in range(w):
        if run_ <= 0:
            j_ = float(np.clip(j_ + rng.choice((-1, 1)), -2, 1))
            run_ = int(rng.integers(3, 8))
        jag[i] = j_
        run_ -= 1
    ytop_front = np.round(yb - hf - tilt * u + jag).astype(int)    # the arris row per column
    yback = ytop_front - dtop
    # big knocked corners: the top corners rounded off, the west one more (weathered from the wind)
    cl, cr = int(rng.integers(2, max(3, w // 4))), int(rng.integers(2, max(3, w // 5)))
    # the front's facets: a lit west facet, the body, a turned east facet
    xa = x0 + w * rng.uniform(0.18, 0.32)
    xc = x0 + w * rng.uniform(0.6, 0.78)
    # its sides and foot wander a texel at a time (never a ruled edge)
    def walk(n, lo, hi):
        v, out_, c_ = int(rng.integers(lo, hi + 1)), np.zeros(n, int), 0
        for q in range(n):
            if c_ <= 0:
                v = int(np.clip(v + rng.choice((-1, 1)), lo, hi))
                c_ = int(rng.integers(3, 7))
            out_[q] = v
            c_ -= 1
        return out_
    span_y = int(hf + dtop + 6)
    li, ri, bo = walk(span_y, 0, 2), walk(span_y, 0, 2), walk(w, 0, 1)
    m = np.zeros((H, W), bool)
    for i, x in enumerate(xs):
        if not (0 <= x < W):
            continue
        dl_, dr_ = i, w - 1 - i
        cut = 0
        if dl_ < cl:
            cut = int(round((cl - dl_) ** 1.3))
        if dr_ < cr:
            cut = max(cut, int(round((cr - dr_) ** 1.3)))
        foot_cut = 1 if min(dl_, dr_) == 0 else 0
        y0 = max(0, int(yback[i]) + cut)
        y1 = min(H, yb + 1 - foot_cut)
        for y in range(y0, y1 - int(bo[i])):
            q = min(span_y - 1, max(0, yb - y))
            if dl_ < li[q] or dr_ < ri[q]:
                continue
            if y <= ytop_front[i] and y < yb - 2:
                if y == y0:
                    c = C('slate', 3)
                elif y == ytop_front[i]:
                    c = C('slate', 5)
                else:
                    c = C('slate_warm', 4)
            else:
                r = y - ytop_front[i]
                t, f_ = 3, fam
                if x < xa + 0.35 * r:
                    t = 4
                elif x > xc - 0.3 * r:
                    # the turned east facet: a cooler plane, its shade in diagonal dashes (no solid band)
                    f_, t = 'slate_cool', (2 if ((x + y) // 2) % 2 else 3)
                if r <= 1:
                    t = min(5, t + 1)
                elif yb - y < hf * 0.4 and ((x + y) // 2) % 2 == 0:
                    t -= 1                                             # darker toward its foot
                if yb - y <= 2:
                    t = 2 if ((x + y) // 2) % 2 or yb - y > 0 else 1
                c = C(f_, t)
            out[y, x] = c
            m[y, x] = True
            own[y, x] = bid
    # small ledges where the front steps back a texel: a lit lip over a shade line, snow on some
    for _ in range(int(hf > 12) + int(hf > 24) + int(w > 30)):
        lw = int(rng.integers(5, 10))
        lx = int(x0 + rng.uniform(2, max(3, w - lw - 2)))
        ly = int(yb - rng.uniform(4, max(5, hf - 4)))
        for x in range(lx, lx + lw):
            yy = ly + (1 if (x - lx) > lw * 0.6 else 0)
            if 0 <= yy + 1 < H and 0 <= x < W and m[yy - 1, x] and m[yy + 1, x] and out[yy, x] // 8 not in SNOWS:
                out[yy, x] = C('slate', 5) if x < lx + lw * 0.7 else C('slate', 4)
                out[yy + 1, x] = C('slate_cool', 1)
                if rng.random() < 0.6 and x < lx + lw - 1:
                    out[yy - 1, x] = C('snow', 5) if x < lx + lw * 0.5 else C('snow_cool', 4)
    # cracks down a big front
    for _c in range(int(crease and hf > 14 and w > 18) + int(w > 34)):
        x = float(x0 + w * rng.uniform(0.2, 0.75))
        y = int(ytop_front[int(x - x0)]) + 3
        for _ in range(int(hf * rng.uniform(0.4, 0.7))):
            xi = int(round(x))
            if 0 <= y < H and 0 <= xi < W and m[y, xi]:
                out[y, xi] = C('slate_cool', 0)
                if m[y, xi - 1]:
                    out[y, xi - 1] = (out[y, xi - 1] // 8) * 8 + min(5, out[y, xi - 1] % 8 + 1)
            y += 1
            x += rng.choice((-0.6, 0.3, 0.5))
    # the outline: the edge tone, lighter where the top's lit edge meets the sky
    edge = m & ~ndi.binary_erosion(m)
    lit = edge & (np.roll(out, 1, 0) < 0) & (np.arange(W)[None, :] < xc)
    out[edge] = C('slate_cool', 0)
    out[lit] = C('slate', 2)
    # the snow cap on the top plane
    if snow > 0 and dtop >= 2:
        sw = int(w * rng.uniform(0.55, 0.85) * snow)
        sx = x0 + 1 + int((w - sw - 2) * rng.uniform(0.0, 0.35))
        for x in range(sx, sx + sw):
            i = x - x0
            if not (0 <= x < W) or i < 0 or i >= w:
                continue
            e = min(x - sx, sx + sw - 1 - x)
            yf_ = int(ytop_front[i]) + (1 if e >= 2 else 0)
            yt = int(yback[i]) + (1 if e >= 1 else 2) - (1 if (e >= 3 and x < sx + sw * 0.6) else 0)
            for y in range(max(0, yt), min(H, yf_ + 1)):
                if y == yt:
                    c = C('snow', 5)
                elif y == yf_:
                    c = C('snow_cool', 3)
                elif x < sx + sw * 0.3 and y < yf_ - 1:
                    c = C('snow', 5)                                   # the cap's lit west shoulder
                else:
                    c = C('snow', 4) if x < sx + sw * 0.65 else C('snow_cool', 4)
                    if hsh(seed, (x + y) // 3, y, 17) > 0.8:
                        c = C('snow_cool', 4) if c == C('snow', 4) else C('snow_cool', 3)   # wind crust
                out[y, x] = c
                own[y, x] = bid
            if e >= 2 and yf_ + 1 < H and m[yf_ + 1, x]:
                out[yf_ + 1, x] = C('sky_cool', 2)
    return m



def _gdrift(out, cx, yb, hw, hh):
    """A drift banked at a west foot: lit on its top and west, cool to the east."""
    H, W = out.shape
    for x in range(int(cx - hw), int(cx + hw) + 1):
        uu = (x - cx) / hw
        if abs(uu) > 1 or not (0 <= x < W):
            continue
        h = hh * (1 - uu * uu) ** 0.7
        top = int(round(yb - h))
        for y in range(max(0, top), min(H, yb + 2)):
            if y == top:
                c = C('snow', 5) if uu < 0.3 else C('snow_cool', 4)
            elif y >= yb:
                c = C('snow_cool', 4) if uu > -0.2 else C('snow', 4)
            else:
                c = C('snow', 4) if uu < 0.2 else C('snow_cool', 4)
            out[y, x] = c



def _gcontact(out, m, yb):
    """The contact shadow on the ground: east of the foot and a row or two under it."""
    H, W = out.shape
    foot = m & ~np.roll(m, -1, 0)
    for y, x in zip(*np.nonzero(foot)):
        for (dy, dx) in ((1, 1), (1, 2), (2, 3), (1, 3)):
            Y2, X2 = y + dy, x + dx
            if 0 <= Y2 < H and 0 <= X2 < W and out[Y2, X2] < 0:
                out[Y2, X2] = C('snow_cool', 3)



def _gpaint(spec, seed, canvas=(240, 180), origin=(120, 150), drifts=(), snow=1.0):
    """Blocks (x, depth, w, front, top, fam, tilt) relative to the piece's foot, drawn back to
    front; returns a Pic cropped to them."""
    Hc, Wc = canvas[1], canvas[0]
    ox, oy = origin
    out = np.full((Hc, Wc), -1, np.int32)
    own = np.zeros((Hc, Wc), np.int32)
    allm = np.zeros((Hc, Wc), bool)
    for k, (x, dep, w, hf, dt, fam, tilt) in sorted(enumerate(spec), key=lambda kv: kv[1][1]):
        allm |= _gblock(out, own, int(ox + x), int(oy + dep), int(w), int(hf), int(dt), seed + 13 * k, fam=fam,
                        snow=snow, tilt=tilt)
    stone = (out >= 0) & ~np.isin(out // 8, list(SNOWS)) & (out % 8 >= 1) & (out != C('sky_cool', 2))
    _grain(out, stone & ndi.binary_erosion(allm), seed, swap=0.3, step=0.06, lit=(out % 8 >= 4))
    for (dx, hw, hh) in drifts:
        _gdrift(out, ox + dx, oy, hw, hh)
    _gcontact(out, out >= 0, oy)
    return K.crop(out, ox, oy)



def boulder(kind='a', seed=43):
    """A Frostline granite boulder (round 6, A1: the face's granite as blocks): `a` one block with a
    smaller one split off its east side, `b` a tilted slab on a lower block, `large` a big block
    with two smaller in its lee and a chip in front; `small` the round 2 stone, a cell across."""
    if kind == 'small':
        return _boulder_r3('small', seed)
    if kind == 'a':
        spec = [(-14, -3, 22, 15, 8, 'slate', 1), (6, 0, 12, 9, 5, 'slate_warm', 0)]
        return _gpaint(spec, seed, drifts=[(-15, 6, 4)])
    if kind == 'b':
        spec = [(-12, -4, 26, 11, 9, 'iron', -3), (-15, 0, 14, 7, 5, 'slate', 0), (9, 1, 9, 6, 4, 'slate', 0)]
        return _gpaint(spec, seed, drifts=[(-15, 5, 3)])
    spec = [(-30, -14, 34, 26, 12, 'slate', 2), (2, -12, 28, 20, 10, 'slate_warm', -2), (18, -4, 20, 13, 7, 'slate', 0),
            (-36, -2, 16, 10, 6, 'iron', 0), (-14, 2, 12, 7, 5, 'slate', 0), (30, 2, 10, 6, 4, 'slate_warm', 0)]
    return _gpaint(spec, seed, drifts=[(-36, 9, 5)])



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


def crag(kind='a', seed=61):
    """A crag of the headwall's foot (round 6, A1): the face's granite as blocks of very different
    sizes, the big ones behind and the small ones stepping down in front, staggered in depth and
    height, some tilted (strata dipping east like the face's), each with a lit top plane under a
    snow cap, a front stepping darker, a crack down the biggest; drifts at the west foot. The
    zone's north frame (B8, Z1)."""
    rng = np.random.default_rng(seed + (0 if kind == 'a' else 9))
    fams = ('slate', 'slate', 'slate_warm', 'slate')
    if kind == 'a':
        spec = [(-62, -26, 50, 44, 14, 3), (-18, -30, 60, 52, 16, 4), (34, -22, 44, 36, 12, 3), (-86, -12, 34, 24, 10, 2),
                (-48, -6, 42, 22, 10, 2), (2, -6, 36, 20, 9, 1), (40, -2, 30, 14, 7, 0), (-14, 2, 22, 10, 6, 0)]
    else:
        spec = [(-58, -28, 62, 54, 16, 4), (2, -24, 54, 44, 14, 3), (-86, -14, 34, 26, 10, 2), (46, -12, 36, 24, 10, 2),
                (-32, -6, 44, 22, 10, 1), (16, 0, 28, 12, 6, 0), (-58, 2, 24, 11, 6, 0)]
    sp = []
    for k, (x, d, w, hf, dt, tl) in enumerate(spec):
        sp.append((x + rng.uniform(-3, 3), d, w * rng.uniform(0.92, 1.08), hf * rng.uniform(0.9, 1.1), dt,
                   fams[int(rng.integers(0, len(fams)))], tl * (1 if rng.random() < 0.7 else -1)))
    dr = [(spec[3][0] - 2, 9, 5), (spec[-1][0] - 4, 7, 4)]
    return _gpaint(sp, seed, canvas=(260, 180), origin=(130, 160), drifts=dr)



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
# round 6 (A1): the face and the stair painted texel by texel
# ------------------------------------------------------------------------------------------------
# Rounds 3 to 5 built the face from rendered boxes, so its joints ran ruled across and down it and
# it read as a brick wall (detail.masonry_rock, calibration F12), and the stair's risers were lines
# (detail.stair_read, F11). Round 6 paints both on the texel grid. The face is granite split along
# bedding planes that dip and kink (never level for more than a few texels) into blocks by joints
# that lean, so no joint runs straight across or down it (eastward-edges.md 2.4); each block a
# ledge: a lit top plane where the block above stands back, its lit west arris, a front stepping
# darker to its foot and its east side, big blocks turned on a crease; snow lying on the wider
# ledges, lichen on a few lit fronts; under the snow lip the under-lip shade in two values (2.3), at
# the foot a dark band, talus with contact shadows and drifts (3.2). The frozen fall keeps the
# round 5 face behind its ice (water and ice are another stream's).
BEDS = (16, 34, 54, 75)          # the inner bedding planes, art px under the face's top, at every panel seam
SEAM = 10                        # either side of a seam a plane follows one shared profile, so panels meet
SEAM_BLOCK = 14                  # no joint stands nearer a panel's edge than this
LICHEN = (('grass_warm', 3), ('grass_warm', 2), ('brass', 2))



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



def _bed_lines(W, seed):
    """The inner bedding planes across a panel: tilted strata, each plane dipping east 1 in 4 to
    1 in 7 for 18 to 40 texels and then stepping back up 3 to 7 texels where a joint offsets it (so
    no run of it is level for more than about seven texels and the blocks between read as tilted
    slabs), passing every seam on one shared profile (the same dip of 0.3)."""
    rng = np.random.default_rng(seed + 3)
    xs = np.arange(W)
    lines = []
    for k, e in enumerate(BEDS):
        kx, ky = [0.0, float(SEAM)], [0.0, 0.3 * SEAM]
        x, y = float(SEAM), 0.3 * SEAM
        while True:
            rest = W - SEAM - x
            L = float(rng.integers(18, 41))
            if rest - L < 22:
                break
            sl = rng.uniform(0.15, 0.25)
            y = min(y + sl * L, 8.0)
            x += L
            kx.append(x)
            ky.append(y)
            j = float(rng.integers(3, 8))
            y = max(y - j, -8.0)
            x += 1.5
            kx.append(x)
            ky.append(y)
        rest = W - SEAM - x
        # the last stretch dips into the seam's profile: step up to where it must start
        y0 = max(-9.0, -0.3 * SEAM - 0.2 * (rest - 2))
        if abs(y0 - y) > 0.5:
            x += 1.5
            kx.append(x)
            ky.append(y0)
        kx += [float(W - SEAM), float(W)]
        ky += [-0.3 * SEAM, 0.0]
        ln = np.round(e + np.interp(xs, kx, ky)).astype(int)
        if lines:
            ln = np.maximum(ln, lines[-1] + 9)
        lines.append(np.minimum(ln, FACE_PX - 12))
    return lines



def _blocks(W, seed):
    """The face (FACE_PX x W) split into blocks: the bedding planes and the leaning joints between
    them (each 0.2 to 0.55 off the vertical, kinking once in a tall bed, one in five stopping short
    as a crack). Returns (labels, joints, bed of each texel)."""
    rng = np.random.default_rng(seed + 5)
    lines = _bed_lines(W, seed)
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
    """Each block shaded as a granite ledge, lit from the upper left (see the section's note)."""
    a = np.full(lab.shape, -1, np.int32)
    dt, db = _run(lab, 0, False), _run(lab, 0, True)
    dl, dr = _run(lab, 1, False), _run(lab, 1, True)
    # a block cut by the panel's edge runs on into the next panel: its edge there is no arris
    for e, dd in ((0, dl), (W - 1, dr)):
        for b in np.unique(lab[:, e]):
            if b >= 0:
                dd[lab == b] += 60
    Y, X = np.mgrid[0:FACE_PX, 0:W]
    fams = ('slate', 'slate', 'slate_warm', 'iron', 'slate', 'slate_cool')
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
        t0 = 3 if r[1] > 0.4 else 2
        lipd = (3 + int(hsh(seed if not seam else 0, k, 77) * 3) + int(r[2] * 3) - 1) if k > 0 else 1 + int(r[2] * 2)
        w = sl[1].stop - sl[1].start
        h = sl[0].stop - sl[0].start
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
            # a block weathered out: a recess, its top row in the shadow of the block above
            t[:] = 1
            t[_dt <= 1] = 0
            t[_dl == 0] = 2
        else:
            front = _dt - lipd
            t = np.where((front >= 0) & (front <= 1) & (_dl <= 6), t0 + 1, t)
            t = np.where((front > 0) & (_dl <= 1), t0 + 1, t)
            t = np.where((_dr <= 2) & (front >= 0), t0 - 1, t)
            t = np.where((_db <= 2) & (front >= 0), np.minimum(t, t0 - 1), t)
            t = np.where((_db == 0) & (front >= 0) & (((xs + ys) // 2) % 2 == 0), t0 - 2, t)
            if crease:
                # a big block turned on a crease: the plane east of it a tone down, a lit texel on its edge
                cx = info[b]['x0'] + w * (0.4 + 0.3 * r[5])
                xc = cx + 0.45 * (ys - info[b]['y0'])
                east = (xs > xc) & (front > 0)
                t = np.where(east, t - 1, t)
                t = np.where((np.abs(xs - xc) < 0.6) & (front > 0), t0, t)
            # the top plane: lit, warm, its front arris the brightest, its back row in the shade of
            # the face above it
            top = _dt < lipd
            t = np.where(top, 4, t)
            f = np.where(top, FI['slate_warm'], f)
            t = np.where(top & (_dt == 0) & (lipd > 2), 3, t)
            arris = _dt == lipd - 1
            t = np.where(arris & (lipd > 1), 5, t)
            f = np.where(arris & (lipd > 1), FI['slate'], f)
            t = np.where(top & (_dr <= 1), 3, t)
            # the darkest tones only as lines and diagonal two-texel dashes, never as solid bands
            t = np.where((t < 2) & (((xs + ys) // 2) % 2 == 1), 2, t)
        a[ys, xs] = f * 8 + np.clip(t, 0, 5)
    # the joints: dark, the one under a lit lip a tone lighter where it is only a hairline
    a[joint] = C('slate_cool', 0)
    hair = joint & (Y > 0) & (np.roll(a, 1, 1) % 8 >= 3) & (K.vhash(X // 3, Y, seed + 9) > 0.6)
    a[hair & ~np.isin(Y, [0])] = C('slate_cool', 1)
    return a, info, dict(dt=dt, db=db, dl=dl, dr=dr)



def _ledge_snow(a, lab, info, d, W, seed):
    """Snow lying on the wider ledges: heaped west of the ledge's middle, its top lit, its front
    cool, its ends rounded, a shade row on the stone under where it hangs over."""
    out = np.zeros(a.shape, bool)
    for b, bi in info.items():
        if bi['pocket'] or bi['lipd'] < 2 or bi['w'] < 12 or bi['k'] == 0:
            continue
        if hsh(seed, b, 91) < 0.2:
            continue
        m = (lab == b) & (d['dt'] < bi['lipd'])
        m[:, :SEAM_BLOCK] = False                              # never across a seam: panels meet in bare stone
        m[:, W - SEAM_BLOCK:] = False
        cols = np.nonzero(m.any(0))[0]
        if len(cols) < 12:
            continue
        span = int(len(cols) * (0.5 + 0.4 * hsh(seed, b, 92)))
        c0 = cols[0] + int((len(cols) - span) * 0.3 * hsh(seed, b, 93))
        th = 2 + int(hsh(seed, b, 94) * 2)
        for x in range(c0, c0 + span):
            if not m[:, x].any():
                continue
            col = np.nonzero(m[:, x])[0]
            if col.max() - col.min() + 1 > bi['lipd'] + 1:
                continue                                       # a jog in the plane: no ledge to lie on
            yl = int(col.max())                                # the ledge's front row
            e = min(x - c0, c0 + span - 1 - x)
            hh = th if e >= 2 else max(1, th - 2 + e)
            for j in range(hh + 1):
                y = yl - j + 1
                if not (0 <= y < a.shape[0]):
                    continue
                if j == hh:
                    c = C('snow', 5) if x < c0 + span * 0.7 else C('snow', 4)
                elif j == 0:
                    c = C('snow_cool', 3)
                else:
                    c = C('snow', 4) if x < c0 + span * 0.6 else C('snow_cool', 4)
                a[y, x] = c
                out[y, x] = True
    return out



def _drips(out, seed, rows=None):
    """Snow hanging in short tongues from the underside of every snow lip and ledge (1 texel wide,
    1 to 3 long, every 3 to 7 texels), so the shade under the snow is broken, never a ruled band."""
    H, W = out.shape
    sn = (out >= 0) & np.isin(out // 8, list(SNOWS))
    below = np.zeros_like(sn)
    below[:-1] = sn[:-1] & (out[1:] >= 0) & ~sn[1:]
    if rows is not None:
        below &= rows
    nxt = -1
    for x in range(W):
        if x < nxt:
            continue
        ys = np.nonzero(below[:, x])[0]
        if not len(ys):
            continue
        for y in ys:
            n = 1 + int(hsh(seed, x, int(y), 21) * 3)
            for j in range(1, n + 1):
                if y + j < H and out[y + j, x] >= 0 and not sn[y + j, x]:
                    out[y + j, x] = C('snow_cool', 4) if j < n else C('snow_cool', 3)
        nxt = x + 3 + int(hsh(seed, x, 22) * 5)



def _lichen(a, info, d, lab, W, seed, avoid):
    """A few rosettes of lichen (two to five texels) on lit fronts, never on a seam block."""
    rng = np.random.default_rng(seed + 31)
    cand = [b for b, bi in info.items() if not bi['seam'] and not bi['pocket'] and bi['k'] > 0]
    n = max(1, W // 40)
    for b in rng.permutation(cand)[:n]:
        bi = info[b]
        m = (lab == b) & (d['dt'] >= bi['lipd'] + 1) & (d['dl'] >= 2) & (d['dr'] >= 4) & (d['db'] >= 3) & ~avoid
        ys, xs = np.nonzero(m)
        if not len(ys):
            continue
        j = int(rng.integers(0, len(ys)))
        y, x = int(ys[j]), int(xs[j])
        f, t = LICHEN[int(rng.integers(0, len(LICHEN)))]
        shape = [(0, 0), (0, 1), (1, 0), (1, 1), (0, 2)] if rng.random() < 0.5 else [(0, 0), (0, 1), (1, 1), (1, 2)]
        for dy, dx in shape:
            if 0 <= y + dy < a.shape[0] and 0 <= x + dx < W and m[y + dy, x + dx]:
                a[y + dy, x + dx] = C(f, t if (dy, dx) != (0, 0) else min(5, t + 1))
        if y + 2 < a.shape[0] and m[y + 2, x + 1]:
            a[y + 2, x + 1] = C(f, max(1, t - 2))



def _cornice(W, seed, stair=None):
    """How far the upper tier's snow hangs over the face, per column (2 to 7 rows, in lumps 4 to 8
    wide stepping a row at a time, so the shade under it never runs level); the same 3 rows at
    every seam."""
    rng = np.random.default_rng(seed + 41)
    ov = np.full(W, 3.0)
    x = SEAM
    prev = 3
    while x < W - SEAM:
        n = int(rng.integers(4, 9))
        v = int(np.clip(prev + rng.choice((-3, -2, 2, 3)), 2, 7))
        ov[x:min(W - SEAM, x + n)] = float(v)
        prev = v
        x += n
    o = ov.copy()
    for _ in range(3):
        for x in range(1, W):
            o[x] = min(o[x], o[x - 1] + 1)
        for x in range(W - 2, -1, -1):
            o[x] = min(o[x], o[x + 1] + 1)
    return o.astype(int)



def _talus(out, W, seed, yf, keep_clear=None):
    """Stones fallen to the foot (7 to 14 texels, outlined, lit at their upper left) with a contact
    shadow thrown east on the ground, and drifts banked against the face (the windward west of each
    heaped higher)."""
    rng = np.random.default_rng(seed + 51)
    H = out.shape[0]
    # drifts first, stones in front of them
    x = SEAM_BLOCK + float(rng.integers(0, 20))
    while x < W - SEAM_BLOCK - 10:
        hw = rng.uniform(8, 17)
        hh = rng.uniform(4, 9)
        cx = x + hw
        if cx + hw > W - SEAM_BLOCK + 4:
            break
        for xi in range(int(cx - hw), int(cx + hw) + 1):
            if keep_clear is not None and keep_clear(xi):
                continue
            u = (xi - cx) / hw
            if abs(u) > 1:
                continue
            h = hh * (1 - u * u) ** 0.7 * (1.0 + 0.25 * (u < 0))
            top = int(round(yf - 1 - h))
            for y in range(top, yf + 1):
                if not (0 <= y < H):
                    continue
                if y == top:
                    c = C('snow', 5) if u < 0.2 else C('snow_cool', 4)
                elif y <= top + 2:
                    c = C('snow', 4) if u < 0.35 else C('snow_cool', 4)
                else:
                    c = C('snow', 4) if u < -0.1 else C('snow_cool', 4)
                out[y, xi] = c
            if top - 1 >= 0 and out[top - 1, xi] >= 0 and out[top - 1, xi] // 8 not in SNOWS and u > -0.5:
                out[top - 1, xi] = (out[top - 1, xi] // 8) * 8 + max(0, out[top - 1, xi] % 8 - 1)
        x = cx + hw + rng.uniform(18, 46)
    x = SEAM_BLOCK + float(rng.integers(4, 26))
    while x < W - SEAM_BLOCK - 8:
        w = rng.uniform(6, 11) if rng.random() < 0.6 else rng.uniform(12, 19)
        h = w * rng.uniform(0.55, 0.8)
        if keep_clear is not None and (keep_clear(int(x)) or keep_clear(int(x + w))):
            x += w + rng.uniform(16, 40)
            continue
        cx, cy = x + w / 2, yf + 1 - h / 2
        fam = 'slate' if rng.random() < 0.6 else 'slate_warm'
        ys, xs = np.mgrid[int(cy - h / 2) - 1:int(cy + h / 2) + 2, int(x) - 1:int(x + w) + 2]
        dx_, dy_ = (xs + 0.5 - cx) / (w / 2), (ys + 0.5 - cy) / (h / 2)
        # an angular block, its corners knocked off: a lit top plane, a front, a shaded east side
        r = np.maximum(np.maximum(np.abs(dx_), np.abs(dy_)), (np.abs(dx_) + np.abs(dy_)) / 1.45)
        ins = r <= 1.0
        tp = rng.uniform(-0.3, -0.05)
        tone = np.where(dy_ < tp, np.where(dx_ < 0.3, 5, 4), np.where(dx_ > 0.4, 2, np.where(dy_ > 0.55, 2, 3)))
        tone = np.where((dy_ >= tp) & (dy_ < tp + 0.3) & (dx_ <= 0.4), 4, tone)
        rim = ins & ~ndi.binary_erosion(ins)
        ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        # contact shadow: east and a row down, on the ground only
        for (yy, xx) in zip(ys[ins & ok], xs[ins & ok]):
            for (sy, sx) in ((1, 2), (1, 1), (2, 3)):
                Y2, X2 = yy + sy, xx + sx
                if Y2 < H and X2 < W and Y2 > yf - 1 and out[Y2, X2] < 0:
                    out[Y2, X2] = C('snow_cool', 3)
        for (yy, xx, tt, rr) in zip(ys[ins & ok], xs[ins & ok], tone[ins & ok], rim[ins & ok]):
            out[yy, xx] = C('slate_cool', 0) if rr and not (tt >= 5) else C(fam, tt)
        # a cap of snow on the bigger stones
        if w > 10:
            capy = int(cy - h / 2) + 1
            for xx in range(int(cx - w * 0.3), int(cx + w * 0.15)):
                if 0 <= capy < H and 0 <= xx < W:
                    out[capy, xx] = C('snow', 5)
                    if capy + 1 < H:
                        out[capy + 1, xx] = C('snow_cool', 4)
        x += w * rng.uniform(0.6, 1.0) if rng.random() < 0.3 else w + rng.uniform(22, 60)



def _granite_cheek(out, side, seed):
    """The face's end beside the stair (eastward-edges.md 3.3 and 6.1, after the woodland's
    approved timber stair, #513): a stepped wall of the face's granite beside the treads, its
    blocks one or two steps tall with the joints at their own heights; on each step a lit top plane
    (three rows) level with its tread, a front in shade under it, the block's foot a tone darker; on
    the stair side a band 3 texels wide (lit where it faces west, in shade where it faces east) with
    the broken ink line at its edge; a broken ink line where the cheek meets the face's rock, its
    edge staggered every few rows; snow lodged on each top; the snow lip turning down over the
    corner. `side` 0 is the piece's west end (the stair lies west), 1 its east end."""
    H, W = out.shape
    yf = LIP_PX + FACE_PX
    rng = np.random.default_rng(seed + 61 + side)
    k = 0
    while k < STEPS:
        span = 2 if (k < STEPS - 1 and rng.random() < 0.4) else 1
        y0 = LIP_PX + k * STEP_PX
        y1 = yf if k + span >= STEPS else y0 + span * STEP_PX
        wd = CHEEK + int(rng.integers(-1, 3))
        fam = ('slate', 'slate', 'slate_warm', 'iron')[int(rng.integers(0, 4))]
        for y in range(y0, y1):
            r = y - y0
            in_step = (y - LIP_PX) % STEP_PX                       # rows into the step (the tread's own)
            wdy = wd + (1 if ((y + 3 * k) // 5) % 2 else 0)
            for d in range(wdy):
                x = d if side == 0 else W - 1 - d
                if in_step < 3 and (r < 3 or span == 2):
                    # a lit top plane on every step, the upper one of a two-step block a ledge cut in it
                    c = C('slate_warm', 4) if in_step < 2 else C('slate', 5)
                    if in_step == 0 and r > 0:
                        c = C(fam, 2)                              # the crease where the block steps back
                elif y == y1 - 1:
                    c = C('slate_cool', 0)                         # the joint under the block
                elif y >= y1 - 4:
                    c = C(fam, 1)
                elif in_step < 5:
                    c = C(fam, 3)
                else:
                    c = C(fam, 2)
                if d < 3 and in_step >= 3 and y < y1 - 1:
                    # the side band toward the stair: facing west it is lit, facing east in shade
                    if d == 0:
                        c = C('slate_cool', 0) if hsh(seed, y // 3, side, 5) > 0.3 else C(fam, 1)
                    else:
                        c = C(fam, 4 if side == 0 else 1)
                if d == wdy - 1 and in_step >= 3:
                    c = C('slate_cool', 0) if hsh(seed, y // 2, side, 6) > 0.35 else C(fam, 1)
                out[y, x] = c
            if r == 0 or (span == 2 and in_step == 0):
                for d in range(1, wd - 2):
                    x = d if side == 0 else W - 1 - d
                    if hsh(seed, d // 3, y, side) > 0.45:
                        out[y, x] = C('snow', 5)
                        if hsh(seed, d // 2, y, side, 3) > 0.5:
                            out[y + 1, x] = C('snow_cool', 4)
        k += span



def _granite_face(W, seed, cheeks=(False, False)):
    """A south granite face W texels wide on its picture (see the section's note). Panel seams meet:
    the bedding planes, the cornice and the seam blocks are the same at every edge."""
    H = LIP_PX + FACE_PX + 6
    yf = LIP_PX + FACE_PX
    lab, joint, bed = _blocks(W, seed)
    face, info, d = _paint_blocks(W, seed, lab, joint, bed)
    out = np.full((H, W), -1, np.int32)
    out[LIP_PX:yf] = face
    rock = np.zeros((H, W), bool)
    rock[LIP_PX:yf] = True
    labf = np.full((H, W), -1, np.int32)
    labf[LIP_PX:yf] = lab
    df = {k_: np.zeros((H, W), np.int32) for k_ in d}
    for k_ in d:
        df[k_][LIP_PX:yf] = d[k_]
    # the under-lip shade, in two values, under the cornice's own wobble
    ov = _cornice(W, seed)
    Y, X = np.mgrid[0:H, 0:W]
    under = Y - (LIP_PX + ov[None, :])
    # (the deepest shade broken in diagonal two-texel dashes, so it never lies as a ruled band)
    chk = (((X + Y) // 2) % 2) == 0
    band = rock & (under >= 0) & (under < 5)
    t_ = out % 8
    out[band] = (out[band] // 8) * 8 + np.where(chk[band], np.maximum(0, t_[band] - 2), np.clip(t_[band] - 1, 2, 3))
    _shift(out, rock & (under >= 5) & (under < 13) & chk & (out % 8 >= 3), -1)
    # the foot: a dark band, darkest in its last rows
    _shift(out, rock & (Y >= yf - 8) & (out % 8 >= 3), -1)
    _shift(out, rock & (Y >= yf - 4) & chk, -1)
    for side, on in enumerate(cheeks):
        if on:
            _granite_cheek(out, side, seed)
    # lone texels tidied, except in the dashed shades
    V.tidy(out, passes=1, keep=rock & (((under >= 0) & (under < 13)) | (Y >= yf - 8) | (out % 8 <= 1)))
    # granite's grain and a few fractures, on the stone's lit and mid texels
    body = rock & (out >= 0) & (out % 8 >= 1) & (out // 8 != FI['slate_cool']) | (rock & (out // 8 == FI['slate_cool']) & (out % 8 >= 2))
    _grain(out, body, seed, swap=0.3, step=0.06, lit=(out % 8 >= 4))
    _fractures(out, rock & (Y > yf - FACE_PX + 16) & (Y < yf - 10) & (out % 8 >= 2), seed + 5, n=max(1, W // 60))
    snow = _ledge_snow(out[LIP_PX:yf], lab, info, d, W, seed)
    snowf = np.zeros((H, W), bool)
    snowf[LIP_PX:yf] = snow
    _lichen(out, info, {k_: df[k_] for k_ in df}, labf, W, seed, avoid=snowf | (under < 13))
    # the upper tier's snow (the zone's own snow fill) and the cornice hanging over the face
    sfill = np.full((H, W), -1, np.int32)
    paint_snow(sfill, np.ones((H, W), bool))
    for x in range(W):
        o = int(ov[x])
        for y in range(0, LIP_PX + o):
            if cheeks[0] and x < CHEEK + 2 or cheeks[1] and x >= W - CHEEK - 2:
                if y >= LIP_PX - 5:
                    continue
            if y < LIP_PX - 4:
                c = sfill[y, x]
            elif y < LIP_PX - 1:
                c = C('snow', 5)                            # the crest of the lip, lit
            elif y == LIP_PX + o - 1:
                c = C('snow_cool', 2)                       # its underside
            elif y >= LIP_PX + o - 3:
                c = C('snow_cool', 3)
            else:
                c = C('snow_cool', 4)
            out[y, x] = c
    for side, on in enumerate(cheeks):
        if on:
            x0, x1 = (0, CHEEK + 2) if side == 0 else (W - CHEEK - 2, W)
            for x in range(x0, x1):
                top = LIP_PX - 5 + int(round(1.5 * hsh(seed, x // 4, 2)))
                for y in range(max(0, top), LIP_PX):
                    out[y, x] = C('snow', 5) if y == top else (C('snow', 4) if y < LIP_PX - 2 else C('snow_cool', 3))
    fringe = np.zeros((H, W), bool)
    fringe[:yf - 10] = True
    if cheeks[0]:
        fringe[:, :CHEEK + 3] = False
    if cheeks[1]:
        fringe[:, W - CHEEK - 3:] = False
    _drips(out, seed, rows=fringe)
    clear = None
    if cheeks[0] or cheeks[1]:
        def clear(x, c=cheeks):
            return (c[0] and x < CHEEK + 4) or (c[1] and x >= W - CHEEK - 4)
    _talus(out, W, seed, yf, keep_clear=clear)
    return V.Pic(W, H, W // 2, yf - 1), out



def _granite_stair(W, seed):
    """The Col Path's stair up the face, seen from above (eastward-edges.md 6.1, size guide: six
    steps on a 16 px pitch): each step a tread of two or three long granite slabs, 8 rows deep, its
    back row in the shade of the riser above, its nose lit and chipped, over a riser 8 rows deep
    darkening to a contact line at its foot (half the pitch, Eastward's 43 to 53 %). The
    slab joints line up from step to step (laid, not bonded) and each slab sits a texel high or low,
    so no tread edge runs ruled across. The cheeks' shade on the treads at both sides, snow banked
    in the back corners and along the outer thirds of the treads, the trod worn smooth up the middle
    with a few packed bootprints; the packed trod coming over the top."""
    H = LIP_PX + FACE_PX + 6
    yf = LIP_PX + FACE_PX
    rng = np.random.default_rng(seed + 7)
    out = np.full((H, W), -1, np.int32)
    TR = 8
    j0 = [int(W * 0.34 + rng.integers(-3, 4)), int(W * 0.68 + rng.integers(-3, 4))]
    mid0, mid1 = int(W * 0.36), int(W * 0.64)
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        js = [j + int(rng.integers(-1, 2)) for j in j0]
        if rng.random() < 0.3:
            js = [js[int(rng.integers(0, 2))]]                       # one long slab and a short one
        edges = [0] + js + [W]
        for s in range(len(edges) - 1):
            x0, x1 = edges[s], edges[s + 1]
            fam = ('slate', 'slate_warm', 'slate', 'iron')[int(hsh(seed, k, s, 3) * 4)]
            base = 4
            dy = (0, 0, 1, -1)[int(hsh(seed, k, s, 5) * 4)] if k > 0 else 0
            tb = y0 + dy                                           # the slab's back row
            nose = y0 + TR - 1 + dy
            for x in range(x0, x1):
                for y in range(max(y0 - 1, tb), min(yf, y0 + STEP_PX)):
                    if y <= nose:
                        r = y - tb
                        if r == 0 and k > 0:
                            t = 2                                            # the riser above shades its back
                        elif y == nose:
                            t = 5 if hsh(seed, x // 2, k, 6) > 0.12 else 3   # the lit nose, chipped
                        else:
                            t = base
                        f = fam if (y != nose and r > 0) else 'slate'
                        if base == 4 and 0 < r < TR - 3 and y != nose:
                            f = 'slate_warm' if fam != 'iron' else fam       # the lit plane warm
                    else:
                        rr = y - nose - 1                                    # the riser, 8 rows under the nose
                        # the riser: its stone in shade under the nose, the contact line at its foot
                        t = 2 if rr <= 1 else (1 if rr <= 6 else 0)
                        f = fam if rr <= 5 else 'slate_cool'
                    if x == x0 and x0 > 0:
                        # the joint between slabs: a dark seam on the riser, a fine one on the tread
                        t, f = (0, 'slate_cool') if y > nose else (max(1, t - 2), fam)
                    elif x == x0 + 1 and x0 > 0 and y <= nose and y != nose:
                        t = min(5, t + 1)                                    # the next slab's lit west end
                    out[y, x] = C(f, t)
        # the west cheek shades the west end of every tread and riser; the east cheek only meets it
        for y in range(y0, min(yf, y0 + STEP_PX)):
            for x in range(0, 5):
                if out[y, x] >= 0 and out[y, x] % 8 >= 1 and (x < 3 or hsh(seed, y, k, 12) > 0.4):
                    out[y, x] = (out[y, x] // 8) * 8 + max(0, out[y, x] % 8 - (2 if x < 2 else 1))
            out[y, W - 1] = (out[y, W - 1] // 8) * 8 + max(0, out[y, W - 1] % 8 - 2)
    V.tidy(out, passes=1)
    Y, X = np.mgrid[0:H, 0:W]
    stone = out >= 0
    tread = stone & (out % 8 >= 3)
    worn = tread & (X >= mid0) & (X < mid1)
    _grain(out, stone & ~worn & (out % 8 >= 1), seed, swap=0.45, step=0.06, lit=(out % 8 >= 4))
    _grain(out, worn, seed + 1, swap=0.2, step=0.0)
    # snow banked into the treads' back corners against the cheeks (a quarter heap, its top lit,
    # its rim toward the tread cool), clumps lying at the back of the outer thirds
    for k in range(STEPS):
        y0 = LIP_PX + k * STEP_PX
        for side in (0, 1):
            wl = 8 + int(round(7 * hsh(seed, k, side, 8)))
            hm = 4 + int(round(2 * hsh(seed, k, side, 13)))
            for dx in range(wl):
                x = dx if side == 0 else W - 1 - dx
                h = int(round(hm * math.sqrt(max(0.0, 1 - (dx / wl) ** 2))))
                for r in range(h):
                    y = y0 + r + (1 if k > 0 else 0)
                    rim = r == h - 1 or dx >= wl - 2
                    c = C('snow', 5) if r == 0 and dx < wl - 2 else (C('snow_cool', 3) if rim else (
                        C('snow', 4) if side == 0 or dx > 2 else C('snow_cool', 4)))
                    out[y, x] = c
        x = 16 + int(rng.integers(0, 8))
        while x < W - 18:
            n = int(rng.integers(3, 7))
            if not (mid0 - 6 <= x + n and x <= mid1 + 6) and hsh(seed, x, k, 9) > 0.35:
                for xx in range(x, x + n):
                    out[y0 + 2, xx] = C('snow', 5) if xx < x + n - 1 else C('snow_cool', 4)
                    if 0 < xx - x < n - 1:
                        out[y0 + 3, xx] = C('snow_cool', 4)
            x += n + int(rng.integers(6, 16))
        # a pair of packed bootprints on alternate treads
        if k % 2 == 0:
            for j, fx in enumerate((-6, 4)):
                x = int((mid0 + mid1) / 2 + fx + rng.integers(-2, 3))
                y = y0 + 3 + 2 * j
                out[y:y + 3, x:x + 2] = C('snow_cool', 4)
                out[y, x] = C('snow', 5)
    # the trod coming over the top (the zone's own trod fill) between the snow either side
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
    return V.Pic(W, H, W // 2, yf - 1), out



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

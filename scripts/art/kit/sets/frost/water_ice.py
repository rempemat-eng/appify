"""Frostline open water, cut ice and frozen falls."""
from __future__ import annotations

from ._shared import (
    C,
    FACE_PX,
    FI,
    K,
    LIP_PX,
    V,
    _drift_west,
    hsh,
    math,
    ndi,
    np,
)

# ------------------------------------------------------------------------------------------------
# the ice-cutter's sledge and the cut blocks (F-S1, B4)
# ------------------------------------------------------------------------------------------------
ICE = [('water_cool', 'sky_cool', 'sky_cool')]



def _ice_faces(sc, a, seed):
    """The cut blocks drawn as translucent lake ice: a frosted lit top plane, front faces in bands
    deepening downward, a lit west edge, a dark east face, saw-cut striations, a crack line and air
    bubbles in clusters."""
    rng = np.random.default_rng(seed)
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'ice']
    for i in ids:
        m = sc.label == i
        if not m.any():
            continue
        nz, ny, nx = sc.n[..., 2], sc.n[..., 1], sc.n[..., 0]
        topm = m & (nz > 0.6)
        front = m & (ny > 0.5) & ~topm
        eastm = m & (nx > 0.5) & ~topm
        a[topm] = np.where(sc.gy[topm] < np.median(sc.gy[topm]) if topm.any() else False, C('snow', 5), C('snow', 4))
        if front.any():
            ys, xs = np.nonzero(front)
            yt, yb = ys.min(), ys.max()
            v = (ys - yt) / max(1, yb - yt)
            band = np.where(v < 0.25, C('sky_cool', 5), np.where(v < 0.55, C('sky_cool', 4), np.where(v < 0.85, C('sky_cool', 3),
                                                                                                             C('water_cool', 3))))
            a[ys, xs] = band
            xl = xs.min()
            a[ys[xs == xl], xl] = C('snow_cool', 4)                               # the lit west edge
            stri = ((ys - yt) % 4 == 2) & (xs > xl + 1) & (np.array([hsh(seed, x // 3, i) for x in xs]) > 0.35)
            a[ys[stri], xs[stri]] = np.where(v[stri] < 0.5, C('sky_cool', 3), C('water_cool', 2))
            # a crack and a cluster of bubbles
            cx = int(rng.integers(xs.min() + 2, max(xs.min() + 3, xs.max() - 2)))
            for k_ in range(int((yb - yt) * 0.7)):
                y = yt + 1 + k_
                x = cx + (k_ // 3) % 2
                if 0 <= y < a.shape[0] and front[y, x]:
                    a[y, x] = C('sky_cool', 2)
            bx, by = int(rng.integers(xs.min() + 2, max(xs.min() + 3, xs.max() - 3))), int(yt + (yb - yt) * 0.6)
            for dx, dy in ((0, 0), (2, -1), (1, 2)):
                if 0 <= by + dy < a.shape[0] and 0 <= bx + dx < a.shape[1] and front[by + dy, bx + dx]:
                    a[by + dy, bx + dx] = C('sky_cool', 5)
        if eastm.any():
            a[eastm] = C('water_cool', 2)



def _line(a, p0, p1, code, w=1):
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
    for t in np.linspace(0, 1, n):
        x = int(round(p0[0] + (p1[0] - p0[0]) * t))
        y = int(round(p0[1] + (p1[1] - p0[1]) * t))
        for k_ in range(w):
            if 0 <= y < a.shape[0] and 0 <= x + k_ < a.shape[1]:
                a[y, x + k_] = code



def ice_stack(seed=59):
    """The ice-cut's stack on the shore: cut blocks in two courses, frosted on top, a little snow
    blown against their west end."""
    sc = K.Scene(-40, 40, -24, 14, 80)
    blocks = [(-26, -12, 0, -9, 2, 14), (-7, -13, 0, 10, 1, 13), (12, -11, 0, 28, 3, 15), (-17, -10, 14, 0, 0, 26),
              (3, -11, 13, 19, -1, 25)]
    for (x0, y0, z0, x1, y1, z1) in blocks:
        sc.box(x0, y0, z0, x1, y1, z1, ICE, base=3.4, k=1.3, tag='ice', round_=1.2)
    _drift_west(sc, -28, 0, 7, seed)
    sc.render()
    a = sc.shade(crevice=1.0, rim=0.6)
    _ice_faces(sc, a, seed)
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)



_FALL_T = [0]                 # the frame open_fall() asks _icefall for (rock.rockface_fall takes no frame)

FALL_FRAMES, FALL_FPS = 8, 10.0

SHEET_X = (30, 86)            # the sheet's columns at the lip (the outlet narrows to them; rock either side)

WINTER = {0: C('slate_cool', 0), 1: C('slate_cool', 1), 2: C('slate_warm', 1), 3: C('slate', 2), 4: C('slate', 3),
          5: C('snow_cool', 2)}  # the house water's tones as the outlet's winter water (outlet.RAMPS['winter'])



def _winter(a):
    """The house painters' water (water, water_cool) recoloured to the outlet's winter ramp, tone for tone."""
    for fam in ('water', 'water_cool'):
        for t in range(6):
            a[a == C(fam, t)] = WINTER[t]



def _icicles(a, c0, c1, x0, x1, seed):
    """What is left of the winter's ice beside the open fall (round 1 logic audit, F1): a fringe of
    four to seven icicles of uneven length (3 to 10 texels) hanging from the snow lip in the face's
    top quarter, joined at the root under the lip, each lit on its west flank, blue in its body and
    shaded east; and a glaze of one or two texels on the wet rock right beside the sheet, in short
    runs, stopping well above the plunge (nothing white reaches it)."""
    H, W = a.shape
    rng = np.random.default_rng(seed + 31)
    spots = sorted(set(int(v) for v in rng.choice(np.arange(c0 + 2, x0 - 3), size=int(rng.integers(3, 5)), replace=False)))
    spots += sorted(set(int(v) for v in rng.choice(np.arange(x1 + 2, c1 - 1), size=int(rng.integers(1, 3)), replace=False)))
    for x in spots:
        ln = int(rng.integers(3, 11))
        wd = 2 if ln < 6 else 3
        for k in range(ln):
            y = LIP_PX + k
            half = max(0, int(round((wd - 1) * (1 - k / float(ln)))))
            for dx in range(-half, half + 1):
                X = x + dx
                if 0 <= X < W and 0 <= y < H:
                    a[y, X] = C('sky_cool', 5) if dx < 0 or (half == 0 and k < ln - 1) else (
                        C('sky_cool', 3) if dx > 0 else C('sky_cool', 4))
        if LIP_PX + ln < H:
            a[LIP_PX + ln, x] = C('sky_cool', 3)                    # the drip at its tip
        a[LIP_PX - 1, max(0, x - 1):min(W, x + 2)] = C('snow', 4)    # the root under the lip
    # the glaze beside the sheet: short runs of one or two texels, a darker wet streak between
    yf = LIP_PX + FACE_PX
    for side, xs in ((0, (x0 - 2, x0 - 1)), (1, (x1, x1 + 1))):
        y = LIP_PX + 2
        while y < yf - 22:
            n = int(rng.integers(3, 9))
            if rng.random() < 0.6:
                for k in range(n):
                    for j, X in enumerate(xs):
                        if 0 <= X < W and y + k < yf - 22 and (j == (1 - side) or k % 3 != 2):
                            a[y + k, X] = C('sky_cool', 4) if (j + side) % 2 else C('sky_cool', 3)
            y += n + int(rng.integers(2, 7))



def _icefall(a, fall, seed):
    """The tarn's outlet over the cirque's step (Matt, 23 Nov: the outlet open, thawing water), after
    the round 1 audits of #535: an open fall, the house's one sheet (rocks.sheet, eastward-edges.md
    5.3b) exactly as wide as the channel the outlet narrows to at the lip, frame `_FALL_T` of an
    8-frame loop. The rock shows 4 to 10 texels either side, wet (a tone darker) and glazed in short
    runs; the face's own stones break over the sheet's edges here and there, so it narrows and
    widens down the face; its navy east band follows that wobble and is broken by pale streaks. A
    fringe of short icicles hangs from the lip beside it (_icicles). Above the rim nothing is drawn
    in the channel's columns: the outlet piece's water runs to the lip."""
    from scripts.art.native import rocks as RK
    H, W = a.shape
    f0, f1 = fall
    yf = LIP_PX + FACE_PX
    x0, x1 = f0 + SHEET_X[0], f0 + SHEET_X[1]
    rock0 = a.copy()
    a[:LIP_PX, x0 - 1:x1 + 1] = -1
    # the wet rock either side of the sheet: a tone darker, 4 to 10 texels out
    rng = np.random.default_rng(seed + 5)
    for y in range(LIP_PX, yf):
        for side, xs in ((0, range(max(0, x0 - 4 - int(6 * hsh(seed, y // 7, 1))), x0)),
                         (1, range(x1, min(W, x1 + 4 + int(6 * hsh(seed, y // 7, 2)))))):
            for X in xs:
                c = a[y, X]
                if c >= 0 and (c // 8) in (FI['slate'], FI['slate_cool'], FI['slate_warm']) and c % 8 > 0:
                    a[y, X] = c - 1
    wet = a.copy()
    mask = np.zeros((H, W), bool)
    mask[LIP_PX - 7:LIP_PX, x0:x1] = True
    a[mask] = C('water', 2)
    RK.sheet(a, x0, x1, LIP_PX, yf, LIP_PX / 3.0, np.random.default_rng(seed), seed, water=mask, t=_FALL_T[0],
             n=FALL_FRAMES, phase_y=LIP_PX, stagger=True)
    a[mask & (a == C('water', 2))] = -1
    sheet = (a != wet) & ~mask
    # the face's stones breaking over the sheet's edges: per stretch of 6 to 14 rows, up to 3 texels
    y = LIP_PX + 4
    while y < yf - 2:
        n = int(rng.integers(6, 15))
        for side in (0, 1):
            d = int(rng.choice([0, 0, 1, 2, 3]))
            for k in range(n):
                Y = y + k
                if Y >= yf - 1:
                    break
                cols = np.nonzero(sheet[Y])[0]
                if not len(cols) or d == 0:
                    continue
                dd = d if 1 < k < n - 2 else max(0, d - 1)
                xs = range(cols.min(), cols.min() + dd) if side == 0 else range(cols.max() - dd + 1, cols.max() + 1)
                for X in xs:
                    a[Y, X] = wet[Y, X] if wet[Y, X] >= 0 else C('slate_cool', 1)
        y += n
    # the navy east band: recoloured greyer and broken by two or three short pale streaks
    for fam in ('water', 'water_cool'):
        a[sheet & (a == C(fam, 0))] = C('slate_cool', 1)
    for _k in range(3):
        Y = int(rng.integers(LIP_PX + 8, yf - 16))
        cols = np.nonzero(sheet[Y])[0]
        if not len(cols):
            continue
        X = int(cols.max()) - int(rng.integers(2, 7))
        for k in range(int(rng.integers(5, 10))):
            if Y + k < yf and sheet[Y + k, X]:
                a[Y + k, X] = C('water', 3)
    _icicles(a, f0, f1, x0, x1, seed)



def sheet_foot(seed=113):
    """The sheet's foot columns (picture texels of the fall piece) on its last row."""
    from scripts.art.native import rocks as RK
    rows = RK.sheet_rows(SHEET_X[0], SHEET_X[1], LIP_PX, LIP_PX + FACE_PX, phase_y=LIP_PX)
    _y, xl, xr = rows[-1]
    return int(math.floor(xl)), int(math.ceil(xr))



def open_fall(seed=113):
    """The fall piece's picture as an open fall, and its loop: the sheet's 8 frames over the face
    (rock.rockface_fall paints the face and calls _icefall for the water)."""
    from .rock import rockface_fall
    pics = []
    try:
        for t in range(FALL_FRAMES):
            _FALL_T[0] = t
            pics.append(rockface_fall())
    finally:
        _FALL_T[0] = 0
    p0 = pics[0]
    ry0 = LIP_PX - 8
    rh, rw = p0.H - ry0, p0.W
    frames = []
    for p in pics:
        fr = V.Pic(rw, rh, 0, rh)
        fr.a[:] = p.a[ry0:ry0 + rh, :rw]
        frames.append(fr)
    return p0, {'frames': frames, 'fps': FALL_FPS, 'clip': 'flow', 'region': (0, ry0, rw, rh)}



PLUNGE_W, PLUNGE_H, PLUNGE_TOP, PLUNGE_DX = 120, 48, 8, 24



def plunge(seed=113):
    """Where the open fall lands (the zone's plunge pool, under the step): the house's foam
    (rocks.plunge, eastward-edges.md 5.3b) churning at the sheet's foot in 8 frames, painted over two
    pool fills and kept only where both agree, so it lies on the outlet's own water, its blues in the
    outlet's winter ramp; two floes broken off the shelf turning in the eddy downstream, each with
    its wet contact (the water a tone darker round it, a light ripple arc downstream)."""
    from scripts.art.native import rocks as RK
    xl, xr = sheet_foot(seed)
    xl, xr = xl + PLUNGE_DX, xr + PLUNGE_DX
    outs = []
    for t in range(FALL_FRAMES):
        runs = []
        for pool in (C('water', 2), C('water', 1)):
            cv = np.full((PLUNGE_H, PLUNGE_W), pool, np.int32)
            RK.plunge(cv, xl, xr, PLUNGE_TOP, seed, t=t, n=FALL_FRAMES, rings=True, seat_gaps=True)
            runs.append(cv)
        a = np.where(runs[0] == runs[1], runs[0], -1)
        _winter(a)
        _floe(a, xl - 8, PLUNGE_TOP + 24, 7, 4, seed + 1)
        _floe(a, xr + 1, PLUNGE_TOP + 30, 6, 3, seed + 2)
        outs.append(a)
    p = V.Pic(PLUNGE_W, PLUNGE_H, PLUNGE_W // 2, PLUNGE_H - 1)
    p.a[:] = outs[0]
    frames = []
    for a in outs:
        fr = V.Pic(PLUNGE_W, PLUNGE_H, 0, PLUNGE_H)
        fr.a[:] = a
        frames.append(fr)
    return p, {'frames': frames, 'fps': FALL_FPS, 'clip': 'flow', 'region': (0, 0, PLUNGE_W, PLUNGE_H)}



# ------------------------------------------------------------------------------------------------
# floes (Matt, 23 Nov: the outlet thaws)
# ------------------------------------------------------------------------------------------------
def _sh(m, k, axis):
    """np.roll without the wrap: what shifts in from the canvas's edge is empty."""
    out = np.zeros_like(m)
    if k == 0:
        return m.copy()
    src = [slice(None)] * m.ndim
    dst = [slice(None)] * m.ndim
    if k > 0:
        src[axis], dst[axis] = slice(0, -k), slice(k, None)
    else:
        src[axis], dst[axis] = slice(-k, None), slice(0, k)
    out[tuple(dst)] = m[tuple(src)]
    return out



def _floe(a, x, y, rx, ry, seed):
    """A floe on open water: a plate with a lit top and north rim, its thickness on its south edge,
    and its wet contact (round 1 detail audit, 14): the water a tone darker in a ring round it and a
    light ripple arc on its downstream side."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    nz = K.vhash(X // 2, Y // 2, seed)
    f = (((X - x) / rx) ** 2 + ((Y - y) / ry) ** 2 + 0.35 * (nz - 0.5)) < 1.0
    ring = ndi.binary_dilation(f, iterations=1) & ~f
    a[ring] = C('slate_cool', 1)
    arc = _sh(ring, 2, 0) & ~f & ~ring & (Y > y)
    a[arc & (K.vhash(X, Y, seed + 3) > 0.2)] = C('slate', 3)
    a[f] = C('snow_cool', 4)
    a[f & (K.vhash(X // 2, Y, seed + 4) > 0.65)] = C('sky_cool', 5)
    a[f & ~_sh(f, 1, 0)] = C('snow', 5)
    a[f & ~_sh(f, -1, 0)] = C('sky_cool', 3)



# ------------------------------------------------------------------------------------------------
# the tarn's edge: pressure ridges (Matt, 23 Nov: the tarn is frozen)
# ------------------------------------------------------------------------------------------------
def pressure_ridge(kind='long', seed=191):
    """A pressure ridge where the tarn's ice has pushed against its shore (round 1 detail audit, 8):
    broken plates of lake ice heaped along a bending line, no fixed pitch: sizes from 4 to 13 texels,
    tilted every way, two or three piled up where the line kinks, the odd gap. Each plate shows a
    lit top plane two or more texels deep, a front broken in two shades where it faces the camera,
    blue translucency on its thin edges, and is outlined as anything standing off the ice is; snow is
    banked on the windward west of the heap, and its shade falls short to the east and south onto
    the ice. `long` runs three cells west to east, `short` two, `side` three cells down a shore."""
    L = {'long': 72, 'short': 48, 'side': 72}[kind]
    vertical = kind == 'side'
    W, H = (30, L + 14) if vertical else (L + 8, 28)
    rng = np.random.default_rng(seed + L + (5 if vertical else 0))
    a = np.full((H, W), -1, np.int32)
    Y, X = np.mgrid[0:H, 0:W]
    # the line bends: a slow curve with a kink
    kink = float(rng.uniform(0.35, 0.65)) * L
    slabs = []
    t = 2.0
    while t < L - 3:
        if rng.random() < 0.12:                              # a gap in the heap
            t += float(rng.uniform(3, 7))
            continue
        sl = float(rng.choice([rng.uniform(4, 6), rng.uniform(6, 9), rng.uniform(9, 13)], p=[0.4, 0.35, 0.25]))
        flat = sl > 9 and rng.random() < 0.5
        ang = float(rng.uniform(-0.3, 0.3)) if flat else float(rng.choice([-1, 1]) * rng.uniform(0.25, 1.2))
        lift = 1 if flat else int(rng.integers(2, 6))
        th = float(rng.uniform(1.8, 3.0)) if flat else float(rng.uniform(1.2, 2.2))
        bend = 3.5 * math.sin(math.pi * t / L) + (2.5 if t > kink else 0.0)
        off = bend + float(rng.uniform(-1.5, 1.5))
        if vertical:
            cx, cy = W / 2.0 + off - 2, t + 7
        else:
            cx, cy = t + 4, H - 10 + off * 0.6
        slabs.append((cy, cx, sl, ang, lift, th))
        if abs(t - kink) < 6:                                # piled up where the line kinks
            for _p in range(int(rng.integers(1, 3))):
                slabs.append((cy + rng.uniform(-2, 1), cx + rng.uniform(-3, 3), rng.uniform(4, 8),
                              float(rng.uniform(-1.2, 1.2)), int(rng.integers(3, 6)), float(rng.uniform(1.2, 2.0))))
        t += sl * float(rng.uniform(0.3, 1.0))
    slabs.sort()
    for (cy, cx, sl, ang, lift, th) in slabs:
        u = (X - cx) * math.cos(ang) + (Y - (cy - lift)) * math.sin(ang)
        w_ = -(X - cx) * math.sin(ang) + (Y - (cy - lift)) * math.cos(ang)
        top = (np.abs(u) <= sl / 2) & (np.abs(w_) <= th)
        front = np.zeros_like(top)
        for k in range(1, lift + 1):
            front |= _sh(top, k, 0)
        front &= ~top
        brk = K.vhash(X // 2, Y // 2, int(cx * 7 + cy)) > 0.5
        a[front] = np.where(brk[front], C('sky_cool', 3), C('sky_cool', 2))
        a[front & ~_sh(front | top, -1, 1)] = C('water_cool', 2)            # its east end in shade
        a[top] = C('sky_cool', 5)
        a[top & ((X - cx) * math.cos(ang) > sl / 5)] = C('snow_cool', 4)
        edge = top & ~ndi.binary_erosion(top)
        a[edge & ((X - cx) * math.cos(ang) > 0)] = C('sky_cool', 4)         # thin edges translucent blue
        if sl >= 8:
            cap = top & (w_ < -th * 0.2) & ((X - cx) * math.cos(ang) < sl / 4)
            a[cap] = C('snow', 5)
    V.outline(a)
    o = a >= 0
    # snow banked on the windward west, its lit top and a cool lee row
    west = ndi.binary_dilation(o, iterations=3) & ~o & _sh(o, -3, 1) & ~_sh(o, 3, 1)
    drift = west & (K.vhash(X // 3, Y // 2, seed + 1) > 0.2)
    drift = ndi.binary_opening(drift | (ndi.binary_dilation(drift) & west), iterations=1)
    a[drift] = C('snow_cool', 4)
    a[drift & ~_sh(drift, 1, 0)] = C('snow', 5)
    a[drift & ~_sh(drift, -1, 0)] = C('snow_cool', 3)
    o = a >= 0
    # the shade: short, east and south of the heap, on the ice
    shade = (_sh(_sh(o, 2, 0), 2, 1) | _sh(_sh(o, 1, 0), 1, 1)) & ~o
    a[shade] = C('sky_cool', 3)
    p = V.Pic(W, H, W // 2, H - 1)
    p.a[:] = a
    return p



def _pic(a):
    H, W = a.shape
    p = V.Pic(W, H, W // 2, H - 1)
    p.a[:] = a
    return p

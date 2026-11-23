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

SHEET_X = (27, 92)            # the sheet's columns at the lip: the outlet's three cells (zone cols 9 to 11)



def _curtain(a, c0, c1, seed):
    """What is left of the winter's ice beside the open fall (Matt, 23 Nov: the outlet thaws): a
    curtain of ice frozen from the spray on the rock west of the sheet, narrower at the lip, swelling
    to the foot, lit on its west edge and blue to its shaded east, its lanes falling in streaks; it is
    rotting: its foot slumped into a low wet mound, its east edge wet against the sheet, and short
    icicles dripping from the lip over the bare rock beside it."""
    H, W = a.shape
    rng = np.random.default_rng(seed + 31)
    yf = LIP_PX + FACE_PX
    y_top, y_bot = LIP_PX - 3, yf + 1
    yy = np.arange(H)
    v = np.clip((yy - y_top) / float(y_bot - y_top), 0, 1)
    body = [C('snow', 5), C('snow', 4), C('snow_cool', 4), C('sky_cool', 5), C('sky_cool', 5), C('sky_cool', 4),
            C('sky_cool', 4), C('sky_cool', 3)]
    icem = np.zeros((H, W), bool)
    cols, x = [], c0 + 1
    while x < c1 - 4:
        hw = float(rng.uniform(3.5, 6.0))
        cols.append((x + hw, hw, rng.uniform(0, 2 * math.pi), rng.uniform(0.1, 0.25), rng.uniform(30, 60),
                     LIP_PX + int(rng.integers(-2, 10))))
        x += 2 * hw - rng.uniform(0.5, 2.0)
    for j, (cx, hw, ph, bs, per, t0) in enumerate(cols):
        wy = hw * (1 + bs * np.sin(2 * math.pi * yy / per + ph)) * (0.45 + 0.8 * v ** 1.4)
        L_ = np.round(ndi.uniform_filter1d(cx - wy, 5)).astype(int)
        R_ = np.round(ndi.uniform_filter1d(cx + wy, 5)).astype(int)
        q = 6 + j % 3
        idx_ = np.clip(((yy + j * 2) // q) * q, 0, H - 1)
        L_, R_ = np.clip(L_[idx_], c0, c1 - 1), np.clip(R_[idx_], c0, c1 - 1)
        for y in range(max(0, t0), y_bot):
            l, r = int(L_[y]), int(R_[y])
            if y - t0 < 3:
                l, r = l + (3 - (y - t0)), r - (3 - (y - t0))
            if r - l < 1:
                continue
            for x in range(l, r + 1):
                d, e = x - l, r - x
                if d == 0:
                    c = C('snow', 5)
                elif e == 0:
                    c = C('sky_cool', 2)
                elif e == 1:
                    c = C('sky_cool', 3)
                else:
                    ln = (x * 5 + int(hsh(seed, x // 2) * 3)) // 7
                    sg = (y + int(hsh(seed, ln, 1) * 30)) // (8 + int(hsh(seed, ln, 2) * 18))
                    k_ = int(round((d / max(1.0, r - l)) * 6.5 + (hsh(seed, ln, sg) - 0.5) * 2.0))
                    c = body[max(0, min(len(body) - 1, k_))]
                a[y, x] = c
                icem[y, x] = True
    # snow on each curtain's crown, short dripping icicles over the bare rock between
    for x in range(c0, c1):
        col = np.nonzero(icem[:, x])[0]
        if len(col):
            t = int(col.min())
            for k_ in range(2):
                if 0 <= t - 1 + k_ < H:
                    a[t - 1 + k_, x] = C('snow', 5) if k_ == 0 else C('sky_cool', 5)
        elif hsh(seed, x // 2, 7) > 0.45:
            ln = 2 + int(7 * hsh(seed, x, 8) ** 1.8)
            for k_ in range(ln):
                y = LIP_PX - 1 + k_
                a[y, x] = C('sky_cool', 5) if k_ < ln - 1 else C('sky_cool', 3)
            if hsh(seed, x, 9) > 0.6:                           # a drop about to fall
                a[LIP_PX + ln + 1, x] = C('sky_cool', 4)
    # the slumped foot: a low mound of old ice, wet and grey where it sits in the spray
    for x in range(c0, c1):
        e = min(x - c0, c1 - 1 - x)
        h = int(round(min(6.0, 3 + e * 0.5) + 1.5 * hsh(seed, x // 4, 8)))
        for k_ in range(h):
            y = yf + 1 - h + k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5) if k_ == 0 else (C('snow_cool', 4) if k_ < h - 2 else C('sky_cool', 3))



def _icefall(a, fall, seed):
    """The tarn's outlet over the cirque's step (Matt, 23 Nov: the tarn frozen, its outlet open,
    thawing water): an open fall, the house's one sheet (rocks.sheet, eastward-edges.md 5.3b) exactly
    the feed's width at the lip (the outlet's three cells), frame `_FALL_T` of an 8-frame loop. Above
    the rim nothing is drawn in the channel's columns, so the zone's own water runs to the lip. West
    of the sheet the winter's ice curtain is rotting on the rock (_curtain); the rock either side of
    the sheet is wet a texel or two out (a tone darker); the plunge is the piece at its foot
    (frost_plunge), never spray on the face."""
    from scripts.art.native import rocks as RK
    H, W = a.shape
    f0, f1 = fall
    yf = LIP_PX + FACE_PX
    x0, x1 = f0 + SHEET_X[0], f0 + SHEET_X[1]
    # the channel's columns above the rim: the zone's water shows (the face's snow lip stops at its banks)
    a[:LIP_PX, x0 - 1:x1 + 1] = -1
    # the wet rock beside the sheet
    wet = np.zeros((H, W), bool)
    for x in list(range(max(0, x0 - 6), x0)) + list(range(x1, min(W, x1 + 6))):
        wet[LIP_PX:yf, x] = True
    rock = wet & (a >= 0) & np.isin(a // 8, [FI['slate'], FI['slate_cool']])
    a[rock] = np.maximum(a[rock] - 1, (a[rock] // 8) * 8)
    _curtain(a, f0, x0 - 2, seed)
    # the sheet: the house's fall, its glassy tongue in the last rows above the lip
    mask = np.zeros((H, W), bool)
    mask[LIP_PX - 7:LIP_PX, x0:x1] = True
    a[mask] = C('water', 2)
    rng = np.random.default_rng(seed)
    RK.sheet(a, x0, x1, LIP_PX, yf, LIP_PX / 3.0, rng, seed, water=mask, t=_FALL_T[0], n=FALL_FRAMES,
             phase_y=LIP_PX, stagger=True)
    # the tongue only where the sheet will be: the rows above the lip lie over the zone's water
    a[mask & (a == C('water', 2))] = -1



def sheet_foot(seed=113):
    """The sheet's foot columns (picture texels of the fall piece) on its last row."""
    from scripts.art.native import rocks as RK
    rows = RK.sheet_rows(SHEET_X[0], SHEET_X[1], LIP_PX, LIP_PX + FACE_PX, phase_y=LIP_PX)
    _y, xl, xr = rows[-1]
    return int(math.floor(xl)), int(math.ceil(xr))



def open_fall(seed=113):
    """The frozen fall piece's picture as an open fall, and its loop: the sheet's 8 frames over the
    face (rock.rockface_fall paints the face and calls _icefall for the water)."""
    from .rock import rockface_fall
    pics = []
    for t in range(FALL_FRAMES):
        _FALL_T[0] = t
        pics.append(rockface_fall())
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
    pool fills and kept only where both agree, so it lies on the zone's own water; two floes broken
    off the curtain turning in the eddy downstream, each with its thickness and its shade."""
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
        _floe(a, xl - 10, PLUNGE_TOP + 22, 9, 5, seed + 1)
        _floe(a, xr + 2, PLUNGE_TOP + 27, 7, 4, seed + 2)
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
# thawing ice on open water (Matt, 23 Nov): slabs and floes
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



def _slab(a, m, seed, shade=True):
    """Paint ice slab `m` (a floating or shore-fast plate) seen from above: rotting candled ice
    (sky_cool 4 with sky_cool 3 candles in short vertical pairs), wet snow lying on it in patches,
    its north and west rims lit, its east rim in shade, its south edge showing the plate's thickness
    (a sky_cool 3 row) and under it a dark wet line on the water (its shade), and a lit ripple line on
    the water hugging its west side."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    cand = K.vhash(X // 2, Y // 3, seed) > 0.62
    snow = (K.vhash(X // 4, Y // 3, seed + 5) > 0.7) & (K.vhash(X // 2, Y // 2, seed + 6) > 0.25)
    a[m] = C('sky_cool', 4)
    a[m & cand] = C('sky_cool', 3)
    a[m & snow] = C('snow_cool', 4)
    north = m & ~_sh(m, 1, 0)
    west = m & ~_sh(m, 1, 1)
    east = m & ~_sh(m, -1, 1)
    south = m & ~_sh(m, -1, 0)
    a[east] = C('sky_cool', 3)
    a[north | west] = C('snow', 5)
    a[south] = C('sky_cool', 2)
    if shade:
        under = _sh(south, 1, 0) & ~m
        a[under] = C('water_cool', 1)
        rip = _sh(west, -2, 1) & ~m & ~under & (K.vhash(X, Y // 2, seed + 7) > 0.3)
        a[rip] = C('water', 4)



def _floe(a, x, y, rx, ry, seed):
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    nz = K.vhash(X // 2, Y // 2, seed)
    m = (((X - x) / rx) ** 2 + ((Y - y) / ry) ** 2 + 0.35 * (nz - 0.5)) < 1.0
    _slab(a, m, seed)



def shore_ice(kind='west', seed=151):
    """Shelf ice left along a bank of the outlet as it thaws (ground dressing on the zone's water): a
    plate fast to the bank, its free edge ragged and rotten with a melt hole or two, a cell wide at
    most and two cells long, thinning downstream; `floe` a plate broken off and drifting."""
    if kind == 'floe':
        H, W = 20, 26
        a = np.full((H, W), -1, np.int32)
        _floe(a, 12, 9, 10, 6, seed)
        _floe(a, 21, 15, 4, 3, seed + 3)
        return _pic(a)
    H, W = 48, 16
    rng = np.random.default_rng(seed + (0 if kind == 'west' else 1))
    yy = np.arange(H)
    w = 6.0 + 5.0 * np.sin(math.pi * (yy + 0.5) / H) ** 0.6 + 2.0 * np.sin(yy / 4.7 + rng.uniform(0, 6))
    w = np.round(ndi.uniform_filter1d(w * (1 - 0.45 * yy / H), 3)).astype(int)
    Y, X = np.mgrid[0:H, 0:W]
    m = (X < w[:, None]) if kind == 'west' else (X >= W - w[:, None])
    # a melt hole or two near the free edge
    for _k in range(2):
        cy = int(rng.integers(8, H - 10))
        cx = int(w[cy] - 3) if kind == 'west' else int(W - w[cy] + 2)
        m &= ~(((X - cx) / 1.6) ** 2 + ((Y - cy) / 2.4) ** 2 < 1.0)
    a = np.full((H, W), -1, np.int32)
    _slab(a, m, seed)
    # fast to the bank: no rim or shade on the bank side
    side = 0 if kind == 'west' else W - 1
    a[m[:, side], side] = C('sky_cool', 4)
    return _pic(a)



def thaw(kind='west', seed=173):
    """The short thaw band at the woodland's north seam (Matt, 23 Nov), ground dressing over the
    snow beside the outlet's last cells: the snow wet and greying southward, then breaking into
    patches with bare ground between (cold earth, flattened last-year's grass, a stone, a wet slush
    rim round each patch), and meltwater rivulets running downhill into the stream, each a dark line
    with its north edge lit. `west` and `east` sit on the stream's banks (the water's side left
    clear for the bank's own edge), `trod` is the Col Path's slush over the same rows."""
    W = {'west': 96, 'east': 48, 'trod': 48}[kind]
    H = 72
    rng = np.random.default_rng(seed + W + (7 if kind == 'trod' else 0))
    Y, X = np.mgrid[0:H, 0:W]
    v = Y / (H - 1.0)                                          # 0 at the band's north edge, 1 at the seam
    n = ndi.gaussian_filter(rng.random((H, W)), (3.0, 4.5), mode='wrap')
    n = (n - n.mean()) / (n.std() + 1e-9)
    n2 = ndi.gaussian_filter(rng.random((H, W)), 1.6)
    n2 = (n2 - n2.mean()) / (n2.std() + 1e-9)
    a = np.full((H, W), -1, np.int32)
    # the stream's side stays clear for the bank's edge
    if kind == 'west':
        keep = X < W - 12
        dx = 1
    elif kind == 'east':
        keep = X >= 10
        dx = -1
    else:
        keep = np.ones((H, W), bool)
        dx = 0
    # the band thins out toward the piece's sides as well, so no straight edge shows on the snow
    xl_, xr_ = (0, W - 12) if kind == 'west' else ((10, W) if kind == 'east' else (0, W))
    side = np.clip(np.minimum(X - xl_, xr_ - 1 - X) / 14.0, 0.0, 1.0)
    vv = v * (0.25 + 0.75 * side) - 0.9 * (1 - side)
    wet = keep & (n + 0.35 * n2 > 1.2 - 1.9 * vv)
    bare = keep & (n + 0.35 * n2 > 2.05 - 1.8 * vv)
    bare = ndi.binary_opening(bare, iterations=1)
    wet = wet | ndi.binary_dilation(bare, iterations=2) & keep
    # wet snow: greying, in two tones
    a[wet] = np.where(n2[wet] > 0.3, C('snow_cool', 3), C('snow_cool', 2))
    # the slush rim round each bare patch: a dark wet row, and a lit meltwater film on its north side
    rim = ndi.binary_dilation(bare, iterations=1) & ~bare & keep
    a[rim] = C('sky_cool', 3)
    a[rim & _sh(bare, -1, 0)] = C('sky_cool', 5)
    if kind == 'trod':
        # the path's slush: puddles where the snow went, mud only in the deepest
        a[bare] = C('sky_cool', 3)
        a[bare & ~_sh(bare, 1, 0)] = C('sky_cool', 5)
        mud = bare & ndi.binary_erosion(bare, iterations=2) & (n > 2.6 - 1.0 * v)
        a[mud] = C('earth_cool', 2)
        a[mud & ~_sh(mud, 1, 0)] = C('earth_cool', 3)
    else:
        a[bare] = np.where(n2[bare] > 0.0, C('earth_cool', 2), C('earth_cool', 3))
        # flattened last-year's grass: short blades lying downhill in pairs, a lit tip each
        g = bare & (K.vhash(X // 2, Y // 2, seed) > 0.7) & ~_sh(~bare, -1, 0)
        a[g] = C('grass', 1)
        a[g & (K.vhash(X, Y, seed + 1) > 0.7)] = C('earth', 3)
        tip = _sh(g, -1, 0) & bare & ~g
        a[tip & (K.vhash(X, Y, seed + 2) > 0.5)] = C('grass', 2)
        # a stone or two: lit top-left, dark lower-right, a wet foot
        for _k in range(1 if kind == 'east' else 2):
            ys, xs = np.nonzero(bare & ndi.binary_erosion(bare, iterations=3))
            if not len(ys):
                break
            j = int(rng.integers(0, len(ys)))
            cy, cx = ys[j], xs[j]
            st = ((X - cx) / 3.2) ** 2 + ((Y - cy) / 2.4) ** 2 < 1.0
            a[st] = C('stone', 3)
            a[st & ((X - cx) + (Y - cy) < -1)] = C('stone', 4)
            a[st & ((X - cx) + (Y - cy) > 1.5)] = C('stone', 2)
            foot = _sh(st, 1, 0) & ~st
            a[foot] = C('earth_cool', 1)
    # meltwater rivulets running downhill to the stream: a dark line, its north edge lit
    if kind != 'trod':
        for _k in range(3 if kind == 'west' else 2):
            y = float(rng.integers(H // 3, H - 8))
            x = float(rng.integers(4, W // 2)) if kind == 'west' else float(rng.integers(W // 2, W - 4))
            while 0 <= int(y) < H - 1 and keep[int(y), int(x)] and 0 <= x < W:
                a[int(y), int(x)] = C('water', 2)
                if a[int(y) - 1, int(x)] != C('water', 2):
                    a[int(y) - 1, int(x)] = C('sky_cool', 5)
                x += dx * 1.0
                y += 0.45 + 0.3 * math.sin(x / 3.0)
                if not (0 <= x < W):
                    break
    # no texel alone
    V.tidy(a)
    return _pic(a)



# ------------------------------------------------------------------------------------------------
# the tarn's edge: pressure ridges (Matt, 23 Nov: the tarn is frozen)
# ------------------------------------------------------------------------------------------------
def pressure_ridge(kind='long', seed=191):
    """A pressure ridge where the tarn's ice has pushed against its shore: broken slabs of lake ice
    heaped in a line and tilted every way, each with a lit top plane (snow lying on the tops of the
    larger ones), a blue front where it faces the camera, a dark east side, outlined as anything that
    stands up from the ice is; snow banked in the ridge's lee, and its shade lying on the ice to the
    south-east. `long` runs three cells west to east, `short` two, `side` three cells down a west or
    east shore."""
    L = {'long': 72, 'short': 48, 'side': 72}[kind]
    vertical = kind == 'side'
    W, H = (22, L + 12) if vertical else (L + 6, 24)
    rng = np.random.default_rng(seed + L + (5 if vertical else 0))
    a = np.full((H, W), -1, np.int32)
    Y, X = np.mgrid[0:H, 0:W]
    slabs = []
    t = 3.0
    while t < L - 3:
        flat = rng.random() < 0.25                           # now and then a plate lying almost flat
        sl = float(rng.uniform(8, 13)) if flat else float(rng.uniform(4, 10))
        ang = float(rng.uniform(-0.25, 0.25)) if flat else float(rng.choice([-1, 1]) * rng.uniform(0.3, 1.1))
        lift = 1 if flat else int(rng.integers(2, 6))
        th = float(rng.uniform(2.2, 3.2)) if flat else float(rng.uniform(1.3, 2.2))
        if vertical:
            cx, cy = W / 2.0 + rng.uniform(-3, 3), t + 6
        else:
            cx, cy = t + 3, H - 9 + rng.uniform(-3, 2)
        slabs.append((cy, cx, sl, ang, lift, th))
        t += sl * float(rng.uniform(0.45, 0.95))
    slabs.sort()
    obj = np.zeros((H, W), bool)
    for (cy, cx, sl, ang, lift, th) in slabs:
        # the top plane: a thin rotated plate, lifted `lift` rows; its front below it
        u = (X - cx) * math.cos(ang) + (Y - (cy - lift)) * math.sin(ang)
        w_ = -(X - cx) * math.sin(ang) + (Y - (cy - lift)) * math.cos(ang)
        top = (np.abs(u) <= sl / 2) & (np.abs(w_) <= th)
        front = np.zeros_like(top)
        for k in range(1, lift + 1):
            front |= _sh(top, k, 0)
        front &= ~top
        a[front] = C('sky_cool', 3)
        a[front & (Y >= cy - 1)] = C('water_cool', 3)
        a[front & _sh(~front & ~top, -1, 1)] = C('water_cool', 3)       # its east end in shade
        a[top] = C('sky_cool', 5)
        a[top & ((X - cx) * math.cos(ang) > sl / 6)] = C('sky_cool', 4)
        if sl > 7.5:
            cap = top & ~_sh(top, -1, 0) | (top & _sh(~top, 1, 0))
            a[cap & (K.vhash(X // 2, Y, seed) > 0.25)] = C('snow', 5)
        obj |= top | front
    V.outline(a)
    # snow banked in the lee (south-east of the heap) and its shade on the ice
    o = a >= 0
    lee = ndi.binary_dilation(o, iterations=2) & ~o & _sh(o, -2, 1)
    shade = (_sh(_sh(o, 2, 0), 1, 1) | _sh(o, 1, 0)) & ~o & ~lee
    a[shade] = C('sky_cool', 3)
    drift = lee & (K.vhash(X // 3, Y // 2, seed + 1) > 0.35)
    a[drift] = C('snow_cool', 4)
    a[drift & _sh(~drift, 1, 0)] = C('snow', 5)
    p = V.Pic(W, H, W // 2, H - 1)
    p.a[:] = a
    return p



# ------------------------------------------------------------------------------------------------
# open water in a frozen country (Matt's review of round 3): still water freezes first and fast water
# last, so the outlet is ice with a narrow dark lead of running water down its middle
# ------------------------------------------------------------------------------------------------
LEAD_WATER = [C('slate_cool', 1), C('slate', 1), C('slate_cool', 2), C('slate', 2), C('sky_cool', 2)]



def _lead_mask(H, W, seed, width=(5.0, 9.0), close=(), ends=True):
    """A lead's open water down a picture H tall: a channel that meanders a texel or two, swells and
    narrows, pinched shut at its ends (and where `close` lists rows, an ice bridge across it)."""
    rng = np.random.default_rng(seed)
    yy = np.arange(H)
    cx = W / 2.0 + 1.6 * np.sin(yy / 11.0 + rng.uniform(0, 6)) + 0.8 * np.sin(yy / 4.3 + rng.uniform(0, 6))
    w = width[0] + (width[1] - width[0]) * (0.5 + 0.5 * np.sin(yy / 13.0 + rng.uniform(0, 6)))
    if ends == 'north':
        # (23 Nov) the lead where the outlet leaves: shut at its north, opening south into the water
        t = (yy + 0.5) / H
        w = np.maximum(0.0, w * np.sin(0.5 * math.pi * t) ** 0.55 + 1.0) * (yy >= 1)
    elif ends:
        # (round 5) wide through its middle, tapering gradually to a rounded end, not a sliver
        t = (yy + 0.5) / H
        w = np.maximum(0.0, w * np.sin(math.pi * t) ** 0.45 + 1.0) * (np.minimum(yy, H - 1 - yy) >= 1)
    for (c0, c1) in close:
        w[c0:c1] = 0
    w = ndi.uniform_filter1d(w, 3)
    L = np.round(cx - w / 2).astype(int)
    R = np.round(cx + w / 2).astype(int)
    m = np.zeros((H, W), bool)
    for y in range(H):
        if R[y] - L[y] >= 2:
            m[y, max(0, L[y]):min(W, R[y])] = True
    return m



def _paint_lead(a, m, seed):
    """Open water under shelf ice: a calm dark centre, lighter shallows at its edges, a faint line of
    current; the shelf's snow-covered lip round it (lit on the west and north), the lip's shadow
    lying on the water under its south-facing edges, and a stone breaking the ice here and there."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    dist = ndi.distance_transform_edt(m)
    # (23 Nov) the same water as the open outlet it runs into, seen dark through the hole
    a[m] = np.where(dist[m] <= 1, C('water', 3), np.where(dist[m] <= 2, C('water', 2), C('water', 1)))
    cur = m & (dist >= 2) & ((X + (Y // 7)) % 5 == 0) & (K.vhash(X, Y // 4, seed) > 0.55)
    a[cur] = C('water', 2)
    l1 = ndi.binary_dilation(m, iterations=1) & ~m
    grow = K.vhash(X // 3, Y // 3, seed + 3) > 0.45
    lip = l1 | (ndi.binary_dilation(l1, iterations=1) & ~m & grow)
    lip2 = ndi.binary_dilation(lip, iterations=1) & ~m & ~lip & (K.vhash(X // 2, Y // 3, seed + 4) > 0.4)
    north = lip & _sh(m, -1, 0) & ~_sh(m, 1, 0)
    a[lip] = C('snow', 4)
    a[lip & _sh(m, 1, 1)] = C('snow_cool', 3)                       # the east lip, facing west in shade
    a[lip & _sh(m, -1, 1)] = C('snow', 5)                           # the west lip, lit
    a[lip2] = C('snow_cool', 4)
    shade = m & _sh(lip, 1, 0) & (dist <= 2)                         # the lip's shadow on the water
    a[shade] = C('water_cool', 0)
    a[north] = C('snow', 5)
    # small shelves of ice overhanging the water here and there, their shade on it
    rng = np.random.default_rng(seed + 9)
    edge = m & ~ndi.binary_erosion(m)
    ys, xs = np.nonzero(edge)
    for k in range(max(1, len(ys) // 18)):
        j = int(rng.integers(0, len(ys)))
        cy, cx = ys[j], xs[j]
        r = rng.uniform(1.4, 2.6)
        bump = ((Y - cy) ** 2 + (X - cx) ** 2 <= r * r) & m
        a[bump] = C('snow_cool', 4)
        a[bump & ~_sh(bump, 1, 0)] = C('snow', 5)
        under = _sh(bump, 1, 0) & m & ~bump
        a[under] = C('water_cool', 0)



def lead(kind='outlet', seed=137):
    """The one dark lead in the frozen tarn (Matt, 23 Nov): where the outlet leaves, the ice is
    rotten and open in a channel a cell wide and three long, shut at its north end and running out
    at its south into the outlet's open water: a calm dark centre, lighter shallows at its edges, a
    faint line of current, the shelf's snow-covered lip round it, lit on the west and north, and the
    lip's shadow on the water under its south-facing edges."""
    H, W = 72, 24
    m = _lead_mask(H, W, seed + H, (8.0, 13.0), ends='north')
    a = np.full((H, W), -1, np.int32)
    _paint_lead(a, m, seed)
    # the last rows meet the zone's water: no lip across the south end
    a[H - 2:, :][m[H - 2:, :]] = C('water', 2)
    return _pic(a)



def _pic(a):
    H, W = a.shape
    p = V.Pic(W, H, W // 2, H - 1)
    p.a[:] = a
    return p

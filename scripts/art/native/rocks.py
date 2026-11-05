"""Rocks of the woodland on the soft grid (Matt, 27 Oct 11:08: "the little waterfall doesn't look
quite right yet, including the stones. the stone circle is lacking detail"): the cascade's rocks
(flat-topped slabs and rounded boulders, each its own shape), the fall itself, and the ancient
standing stones of the moon circle. All drawn as palette codes at the zone's density, lit from the
upper left (a lit top plane, a mid front, a dark east side and underside), weathered.

    rock(w, h, seed, flat=False, moss=0.5)       -> (codes, anchor at the foot)
    fall(cv, x0, w, y0, y1, seed)                 the falling water over a lip into a pool
    standing_stone(w, h, seed, **look)            -> (codes, anchor at the foot)
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from . import ctx
from .palette import C, FI, step

WATERS = ('water', 'water_warm', 'water_cool')


def _P(v, lo=1):
    return max(lo, int(round(v * ctx.D)))


def _field(H, W, seed, sigma):
    """A smooth noise field, 0..1."""
    rng = np.random.default_rng(seed)
    v = ndi.gaussian_filter(rng.random((H, W)), sigma)
    return (v - v.min()) / max(1e-6, v.max() - v.min())


def _paint(a, m, fam, tone):
    """Tones (array or int) on mask m in a ramp, warm where lit, cool in shade."""
    t = np.clip(np.broadcast_to(np.asarray(tone), a.shape), 0, 5).astype(int)
    warm, cool = fam + '_warm', fam + '_cool'
    f = np.where(t >= 4, FI.get(warm, FI[fam]), np.where(t <= 1, FI.get(cool, FI[fam]), FI[fam]))
    a[m] = (f * 8 + t)[m]


def _outline(a, body, u):
    """Dark on the east and the foot, a lit rim on the west and the top."""
    ed = body & ~ndi.binary_erosion(body)
    below = np.zeros_like(body)
    below[:-1] = body[1:]
    a[ed & ((u > 0.1) | ~below)] = C('stone_cool', 0)
    lit = ed & (u <= 0.1) & below
    a[lit] = np.where(a[lit] % 8 >= 3, C('stone_warm', 5), a[lit])


def _moss(a, m, seed, share=0.5):
    """Moss cushions: lumpy patches, lit on their upper left, a dark rim at their lower edge."""
    f = _field(*a.shape, seed, 1.6) > (1.0 - share)
    cap = m & f
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    up = np.zeros_like(cap)
    up[1:] = cap[:-1]
    g = _field(*a.shape, seed + 11, 0.9)
    a[cap] = np.where(~up[cap], C('leaf_warm', 4), np.where(g[cap] > 0.62, C('leaf_warm', 4),
                                                           np.where(g[cap] < 0.3, C('leaf_cool', 2), C('leaf', 3))))
    low = cap & ~np.roll(cap, -1, 0)
    a[low] = C('leaf_cool', 2)


def _lichen(a, m, rng, n, yellow=True):
    """Lichen rosettes: lumpy round patches 3 to 6 texels across, yellow-ochre or grey-green, a
    lit upper-left edge and a darker lower rim, never a bright dot."""
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    H, W = a.shape
    for k in rng.permutation(len(ys))[:n]:
        y, x = int(ys[k]), int(xs[k])
        r = rng.uniform(1.4, 2.8)
        yel = yellow and rng.random() < 0.5
        body_t = (('sand', 3), ('sand_warm', 4), ('sand_cool', 2)) if yel else (('grass_cool', 3), ('grass', 4), ('grass_cool', 2))
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d2 = dy * dy + dx * dx * 0.8
                Y, X = y + dy, x + dx
                if d2 > r * r or not (0 <= Y < H and 0 <= X < W) or not m[Y, X] or rng.random() < 0.15:
                    continue
                if dy + dx <= -2:
                    f, t = body_t[1]
                elif dy >= r - 1.2:
                    f, t = body_t[2]
                else:
                    f, t = body_t[0]
                a[Y, X] = C(f, t)


def _cracks(a, body, rng, n, x0, x1, y0, y1):
    for _ in range(n):
        y = int(rng.uniform(y0, y1))
        x = int(rng.uniform(x0, x1))
        d = 1 if rng.random() < 0.5 else -1
        L = int(rng.integers(4, 10))
        for j in range(L):
            Y, X = y + j, x + d * (j // 3)
            if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1] - 1 and body[Y, X]:
                a[Y, X] = C('stone_cool', 0)
                if body[Y, X - 1] and a[Y, X - 1] % 8 >= 2:
                    a[Y, X - 1] = step(a[Y, X - 1], 1)


def _weather(a, body, rng, per, vertical=False):
    """Plates and pits: short dashes a tone down with a lit edge above (or, on an upright stone, to
    the west: its grain runs up and down), the odd bright grain."""
    ys, xs = np.nonzero(body)
    for k in rng.permutation(len(ys))[: len(ys) // per]:
        y, x = int(ys[k]), int(xs[k])
        L = int(rng.integers(2, 4))
        if vertical:
            if y + L >= a.shape[0] or x < 1 or not body[y:y + L, x].all():
                continue
            a[y:y + L, x] = step(a[y:y + L, x], -1)
            if body[y:y + L, x - 1].all() and rng.random() < 0.6:
                a[y:y + L, x - 1] = step(a[y:y + L, x - 1], 1)
            continue
        if x + L >= a.shape[1] or y < 1 or not body[y, x:x + L].all():
            continue
        if rng.random() < 0.7:
            a[y, x:x + L] = step(a[y, x:x + L], -1)
            if body[y - 1, x:x + L].all():
                a[y - 1, x:x + L] = step(a[y - 1, x:x + L], 1)
        else:
            a[y, x:x + 2] = step(a[y, x:x + 2], 1)


# ------------------------------------------------------------------------------------------------
# the cascade's rocks
# ------------------------------------------------------------------------------------------------
def rock(w: float, h: float, seed: int, flat: bool = False, moss: float = 0.5):
    """One rock w x h world px. flat: a slab with a broad, nearly level top (a ledge of the cascade)
    and a front face; else a rounded boulder. Lit from the upper left, weathered, cracked, lichen
    on the lit side, moss on the top. Returns (codes, (ax, ay) the foot's centre)."""
    rng = np.random.default_rng(seed)
    pad = _P(2)
    Wt, Ht = _P(w) + 2 * pad, _P(h) + 2 * pad
    a = np.full((Ht, Wt), -1, np.int32)
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    cx, rx = Wt / 2.0, _P(w) / 2.0
    yb = Ht - pad
    wob = (_field(Ht, Wt, seed + 1, 2.5) - 0.5)
    if flat:
        top_h = _P(h) * rng.uniform(0.38, 0.5)                       # the top plane's depth on screen
        yt = yb - _P(h)
        u = (xx - cx) / rx
        # the outline: straight-ish sides, corners broken off, the top edge a little uneven
        side = np.abs(u) <= 1.0 - 0.12 * np.clip((yy - (yb - 3)) / 3.0, 0, 1)
        top_edge = yt + 2.5 * np.clip(np.abs(u) - 0.7, 0, 1) * 6 + wob * 3
        body = side & (yy >= top_edge) & (yy <= yb)
        topm = body & (yy < yt + top_h + wob * 3)
        f = _field(Ht, Wt, seed + 2, 1.4)
        vt = (yy - yt) / max(1.0, top_h)                               # 0 back .. 1 front edge of the top
        tone = np.where(topm, np.clip(np.round(3.4 - 1.1 * u + 1.1 * vt + (f - 0.5) * 1.6), 2, 5),
                        np.clip(np.round(2.6 - 0.9 * u + (f - 0.5) * 1.6 - 0.8 * ((yy - yt - top_h) / max(1, _P(h) - top_h))), 1, 3))
        _paint(a, body, 'stone', tone)
        # the arris where the top meets the face: lit on the west, a dark shadow line under it
        arr = topm & ~np.roll(topm, -1, 0)
        a[arr & (u < 0.3)] = C('stone_warm', 5)
        under = body & ~topm & np.roll(topm, 1, 0)
        a[under] = C('stone_cool', 1)
        _weather(a, body, rng, 14)
        # the lit top is the most weathered: pits and short dashes all over it, so no lit plane is
        # one smooth patch
        lit_ = topm & (a % 8 >= 4)
        ly_, lx_ = np.nonzero(lit_)
        for kk in rng.permutation(len(ly_))[: len(ly_) // 6]:
            y_, x_ = int(ly_[kk]), int(lx_[kk])
            if x_ + 1 < Wt and lit_[y_, x_ + 1]:
                a[y_, x_:x_ + 2] = step(a[y_, x_:x_ + 2], -1 if rng.random() < 0.75 else 1)
        _cracks(a, body & ~topm, rng, 2, cx - rx * 0.7, cx + rx * 0.6, yt + top_h + 1, yb - 3)
        _lichen(a, body & (u < 0.2), rng, int(w * h / 50) + 1)
        if moss > 0:
            _moss(a, topm & (yy < yt + top_h * 0.8), seed + 3, share=moss * 0.6)
    else:
        ry = _P(h) / 2.0
        cy = yb - ry
        u, v = (xx - cx) / rx, (yy - cy) / ry
        r = np.sqrt(u * u + v * v) + wob * 0.18
        body = (r <= 1.0) & (yy <= yb - 0.0) & ~((v > 0.75) & (np.abs(u) > 0.55))
        nz = np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
        lam = -0.55 * u - 0.6 * v + 0.6 * nz
        f = _field(Ht, Wt, seed + 2, 1.3)
        tone = np.clip(np.round(2.3 + 2.8 * lam + (f - 0.5) * 1.3), 1, 5)
        tone = np.where(v > 0.6, np.minimum(tone, 2), tone)               # the dark underside
        _paint(a, body, 'stone', tone)
        _weather(a, body, rng, 24)
        _cracks(a, body & (v > -0.3), rng, 1, cx - rx * 0.4, cx + rx * 0.3, cy - ry * 0.2, yb - 4)
        _lichen(a, body & (lam > 0.2), rng, int(w * h / 110) + 1)
        if moss > 0:
            _moss(a, body & (v < -0.35), seed + 3, share=moss * 0.7)
        u = (xx - cx) / rx
    _outline(a, a >= 0, (xx - cx) / rx)
    return a, (cx, yb)


# ------------------------------------------------------------------------------------------------
# the fall
# ------------------------------------------------------------------------------------------------
PLUNGE_FRAMES = 8       # the foam's churn: a closed loop of 8 frames
PLUNGE_PAD = 8          # texels the foam may reach beyond the sheet's foot on each side


def _runs(row: np.ndarray):
    """(start, stop) of each run of True in a 1-D mask."""
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def crest_breaks(w: int, rng, seed: int | None = None) -> np.ndarray:
    """How deep the white water breaks under the bend, per column of a lip `w` texels wide (the
    woodland review, 4 Nov: the crest read as one lid): two or three runs of different lengths,
    1 to 3 texels deep and rounded at their ends, with a gap or two where the darker sheet goes
    straight on. With `seed`, no run is longer than a cell (split_long_runs)."""
    out = np.zeros(w, np.int32)
    n = int(rng.choice([2, 3, 3]))
    gaps = [int(rng.integers(3, 6)) for _ in range(n - 1)]
    edge = [int(rng.integers(1, 4)), int(rng.integers(1, 4))]
    room = max(n * 4, w - sum(gaps) - sum(edge))
    cut = np.sort(rng.choice(np.arange(3, room - 2), n - 1, replace=False)) if n > 1 and room > 8 else []
    lens = np.diff(np.concatenate([[0], cut, [room]])).astype(int)
    x = edge[0]
    for k, L in enumerate(lens):
        prof = np.clip(np.round(1.4 + rng.uniform(0.6, 1.6) * np.sin(np.linspace(0.15, np.pi - 0.15, max(1, L)))
                                + rng.uniform(-0.4, 0.4, max(1, L))), 1, 3).astype(int)
        out[x:x + L] = prof[:max(0, min(L, w - x))]
        x += L + (gaps[k] if k < len(gaps) else 0)
    if seed is not None:
        out = split_long_runs(out, seed)
    return out


CREST_RUN_MAX = 24       # no white run under a lip longer than a cell (review round 8, K8-1)


def split_long_runs(out: np.ndarray, seed: int) -> np.ndarray:
    """Any white run longer than CREST_RUN_MAX texels broken by a gap of 3 to 5 where the darker sheet
    goes on, each new run with its own rounded depth profile (review round 8, K8-1: on a two- to
    four-cell lip, crest_breaks' two or three runs grew into one white bar 36 to 64 texels long, the
    round-4 lid). Draws from its own generator (from `seed`), so the fall's other draws keep their
    order; a crest with no run over a cell (the woodland's longest is 23) is returned unchanged."""
    out = out.copy()
    w = len(out)
    rng = None
    changed = True
    while changed:
        changed = False
        for a, b in _runs(out > 0):
            if b - a <= CREST_RUN_MAX:
                continue
            if rng is None:
                rng = np.random.default_rng(seed * 4099 + w)
            L = b - a
            g = int(rng.integers(3, 6))
            # cut so that both sides are at least 6 long and the first at most a cell
            cut = int(rng.integers(6, min(CREST_RUN_MAX, L - g - 6) + 1))
            out[a + cut:a + cut + g] = 0
            for (p, q) in ((a, a + cut), (a + cut + g, b)):
                n = q - p
                prof = np.clip(np.round(1.4 + rng.uniform(0.6, 1.6) * np.sin(np.linspace(0.15, np.pi - 0.15, max(1, n)))
                                        + rng.uniform(-0.4, 0.4, max(1, n))), 1, 3).astype(int)
                out[p:q] = prof[:n]
            changed = True
            break
    return out


def fall(cv: np.ndarray, x0: float, w: float, y0: float, y1: float, seed: int = 11, t: int = 0) -> dict:
    """The water over the lip and down into the pool (world px), fitted to the channel that feeds it
    (the woodland review, 4 Nov: the crest overhung the channel and read as a lid): the channel's
    last rows lighten into a glassy tongue; the lip is exactly the channel's width, its bend line
    bowed a texel or two downstream; the white water breaks under it in two or three runs with gaps;
    the sheet widens a little as it falls, shaded as a ribbon (lit west, body, shade east), with
    streaks at different speeds and a darker thinning near the foot; at the foot plunge() churns.
    The sheet is sheet(), the one painter the kit's pieces share (structures.fall_sheet). Returns
    where the foot lies (texels) for the churn's frames."""
    H, W = cv.shape
    D = ctx.D
    rng = np.random.default_rng(seed)
    cx = x0 + w / 2.0
    Y0, Y1 = _P(y0 - 1.5, 0), _P(y1, 0)
    water = np.isin(cv // 8, [FI[n] for n in WATERS]) & (cv >= 0)
    # the channel's columns just above the lip (the run nearest the fall's centre)
    cl, cr = _P(cx - w / 2.0, 0), _P(cx + w / 2.0, 0)
    for yy_ in range(Y0 - 1, max(0, Y0 - 6), -1):
        runs = [(a, b) for a, b in _runs(water[yy_]) if b - a >= _P(4)]
        if runs:
            a, b = min(runs, key=lambda r: abs((r[0] + r[1]) / 2.0 - cx * D))
            if abs((a + b) / 2.0 - cx * D) < w * D:
                cl, cr = int(a), int(b)
                break
    foot = sheet(cv, cl, cr, Y0, Y1, y0, rng, seed, water)
    box = plunge_box(foot[0], foot[1], Y1, H, W)
    pre = cv[box[1]:box[3], box[0]:box[2]].copy()        # what lies under the foam (its frames)
    plunge(cv, foot[0], foot[1], Y1, seed, t=t)
    return {'xl': foot[0], 'xr': foot[1], 'y1': Y1, 'seed': seed, 'box': box, 'under': pre}


def sheet_rows(cl: int, cr: int, Y0: int, Y1: int, phase_y: int = 0) -> list:
    """The sheet's edges per row (texels; rows Y0 .. Y1 - 1, each (Y, xl, xr) as floats, a texel X
    lying on the sheet when xl <= X + 0.5 <= xr): the lip's width at the top, widening a little as it
    falls (0.45 of it west, 0.55 east) with each edge wobbling a texel. The wobble's phase runs from
    row `phase_y` (0: the canvas's own rows, as the woodland paints; a piece passes its rim row, so
    its picture and its bake are the same sheet)."""
    D = ctx.D
    out = []
    for Y in range(Y0, Y1):
        f = (Y - Y0) / max(1.0, (Y1 - Y0))
        widen = max(0.0, f) * 2.4 * D
        Yp = Y - phase_y
        wob_l = 0.35 * D * math.sin(Yp / D / 3.1) * min(1.0, f * 4)
        wob_r = 0.35 * D * math.sin(Yp / D / 2.6 + 1.0) * min(1.0, f * 4)
        out.append((Y, cl - widen * 0.45 - wob_l, cr + widen * 0.55 + wob_r))
    return out


def sheet_mask(shape, cl: int, cr: int, Y0: int, Y1: int, phase_y: int = 0) -> np.ndarray:
    """The texels sheet() paints for the sheet itself (rows Y0 .. Y1 - 1), on a canvas of `shape`."""
    H, W = shape
    m = np.zeros((H, W), bool)
    for (Y, xl, xr) in sheet_rows(cl, cr, Y0, Y1, phase_y):
        if not (0 <= Y < H):
            continue
        for X in range(max(0, int(math.floor(xl))), min(W, int(math.ceil(xr)))):
            if xl <= X + 0.5 <= xr:
                m[Y, X] = True
    return m


def sheet(cv: np.ndarray, cl: int, cr: int, Y0: int, Y1: int, y0: float, rng, seed: int, water=None,
          t: int = 0, n: int = PLUNGE_FRAMES, phase_y: int = 0, stagger: bool = False) -> tuple:
    """One falling sheet (texels), the house's one design, painted for the woodland's fall (fall())
    and for every kit piece (structures.fall_sheet, review round 7: two painters had drifted into two
    designs): the channel's columns cl .. cr feed a lip at row Y0 and the sheet falls to Y1. Above
    the lip, where the canvas is water (`water`), the channel's last rows lighten into a glassy
    tongue fading up in a checker, with two or three lit streaks converging on the lip; the bend
    line bows a texel or two downstream and the white water breaks under it in runs (crest_breaks);
    the sheet widens as it falls (sheet_rows), shaded as a ribbon (lit west, body, shade east), with
    streaks of their own lengths, gaps and phases (y0 is the world row their phase runs from), thinner
    and darker near the foot. `rng` is the fall's generator, drawn in this order.

    `t` of `n` frames moves each streak down by a step of its own period a frame, so a loop of n
    frames closes and frame 0 is the still (the woodland's sheet is its frame 0). `phase_y` (sheet_rows)
    and `stagger` (the tongue's two tones meeting a texel earlier or later row by row, round 7, P7-3)
    are for pieces; the woodland's sheet uses neither. Returns the foot's columns (xl, xr)."""
    H, W = cv.shape
    D = ctx.D
    if water is None:
        water = np.isin(cv // 8, [FI[n_] for n_ in WATERS]) & (cv >= 0)
    lw = cr - cl
    # the glassy tongue: the channel's last rows lighten as the water speeds up to the lip, fading
    # up into the channel in a checker over two or three rows, its top stepping a row or two
    # (review round 2, R2-3: it was two flat rectangles with a ruler-straight top)
    step_top = np.round(1.2 * np.sin(np.arange(lw) / 5.3 + seed) + 0.8 * np.sin(np.arange(lw) / 2.1 + 2 * seed)).astype(int)
    for k in range(7):
        Y = Y0 - 7 + k
        if not (0 <= Y < H):
            continue
        for X in range(cl, cr):
            if not water[Y, X]:
                continue
            s = (X + 0.5 - cl) / lw
            kk = k - int(step_top[X - cl])               # rows into the tongue at this column
            if kk < 0:
                continue
            if kk < 3:
                if (X + Y) % 2 == 0:
                    cv[Y, X] = C('water', 3)             # the fade: a checker into the channel
            else:
                cv[Y, X] = C('water', (4 if kk >= 5 else 3) if s < 0.7 else 3)
    # two or three lit streaks in the channel converging on the lip
    nst = int(rng.integers(2, 4))
    for j in range(nst):
        xa = cl + lw * (0.15 + 0.7 * (j + rng.uniform(0.2, 0.8)) / nst)
        xb = xa + (cl + lw / 2.0 - xa) * 0.3                 # leaning in a little towards the lip's middle
        L = int(rng.integers(9, 16))
        for q in range(L):
            Y = Y0 - 4 - L + q
            X = int(round(xa + (xb - xa) * q / max(1, L - 1)))
            if 0 <= Y < H and cl <= X < cr and water[Y, X]:
                cv[Y, X] = C('water', 5 if q > L * 0.55 else 4)
    brk = crest_breaks(lw, rng, seed=seed)
    cols = {}
    foot = (cl, cr)
    for (Y, xl, xr) in sheet_rows(cl, cr, Y0, Y1, phase_y):
        if not (0 <= Y < H):
            continue
        f = (Y - Y0) / max(1.0, (Y1 - Y0))
        foot = (int(math.floor(xl)), int(math.ceil(xr)))
        # the tongue's tones meet at s 0.65; a piece staggers that a texel or two row by row
        sd = (0.06 * ((Y - Y0) % 3 - 1) + 0.04 * (((Y - Y0) * 7 + seed) % 3 - 1)) if stagger else 0.0
        for X in range(max(0, int(math.floor(xl))), min(W, int(math.ceil(xr)))):
            if not (xl <= X + 0.5 <= xr):
                continue
            s = (X + 0.5 - xl) / max(1.0, xr - xl)
            k_ = min(lw - 1, max(0, X - cl))
            bow = int(round(1.6 * (1.0 - (2.0 * min(1.0, max(0.0, (X + 0.5 - cl) / lw)) - 1.0) ** 2)))
            dy = Y - Y0 - bow
            d_ = int(brk[k_]) if cl <= X < cr else 0
            if dy < 2:
                c = C('water', 4) if s < 0.65 + sd else C('water', 3)  # the glassy tongue over the edge
            elif dy == 2:
                c = (C('water', 5) if s < 0.7 + sd else C('water', 4)) if (d_ or not (cl <= X < cr)) else C('water', 3)
            elif d_ and dy < 3 + d_:
                c = C('snow', 5) if s < 0.65 else C('snow', 4)        # the white water breaking under it
            elif d_ and dy < 4 + d_:
                c = C('water', 2)                                      # its shade
            elif not d_ and cl <= X < cr and dy < 7:
                c = C('water', 3) if s < 0.45 else C('water', 2)      # a gap: the darker sheet going on
            elif dy < 4:
                c = C('water', 3) if s < 0.6 else C('water', 2)
            else:
                # the navy east band: the last 0.15 of the sheet, never more than 9 texels (review
                # round 8, K8-2: as a share of a four-cell sheet it became a flat slab 15 to 17 texels
                # wide); east of s 0.6 the ribbon (water 2 with its streaks) runs on to it. At the
                # woodland's width this is exactly s >= 0.85.
                navy = (xr - X - 0.5) <= min(0.15 * (xr - xl), 9.0)
                tt = 4 if s < 0.2 else (3 if s < 0.6 else (1 if navy else 2))
                if f > 0.75:
                    tt = max(1, tt - 1)                                # thinner and darker near the foot
                c = C('water', tt)
                key = int((X + 0.5 - cl) / D * 2.2)
                if key not in cols:
                    # each streak its own speed: long fast ones and short slow ones
                    cols[key] = (rng.uniform(0, 40), rng.uniform(4, 18), rng.uniform(2, 9), rng.random())
                ph, run, gap, kind = cols[key]
                if Y1 - Y0 < 100:
                    # on a sheet under 100 rows (a kit piece; the woodland's is 124) the longest
                    # streaks are cut to 13 world px, so no more of its columns hold one tone over 40
                    # rows than the sibling's over the same height (review round 8, P8-2)
                    run = min(run, 13.0)
                # frame t of n: each streak a step of its own period down (frame 0 the still)
                if (((Y + 0.5) / D - y0 + ph - t * (run + gap) / n) % (run + gap)) < run and 0.05 < s and not navy:
                    c = C('snow', 5) if (kind < 0.35 and s < 0.5) else (C('snow', 4) if kind < 0.7 else C('water', 5))
            cv[Y, X] = c
    return foot


def plunge_box(xl: int, xr: int, y1: int, H: int, W: int):
    """(x0, y0, x1, y1) texels: everything plunge() may draw."""
    return (max(0, int(xl - PLUNGE_PAD - 4)), max(0, int(y1 - 4)), min(W, int(xr + PLUNGE_PAD + 4)), min(H, int(y1 + 30)))


def plunge_frames(codes: np.ndarray, info: dict, n: int = PLUNGE_FRAMES) -> list:
    """The foam's churn as overlays (codes, -1 where nothing changes) of the box plunge() draws,
    one per frame: frame t drawn over what lay under the foam, against frame 0, so frame 0 is
    empty (the still the ground shows) and every other frame holds only what moved."""
    x0, y0, x1, y1 = info['box']
    outs = []
    base = None
    for t in range(n):
        cv = codes.copy()
        cv[y0:y1, x0:x1] = info['under']
        plunge(cv, info['xl'], info['xr'], info['y1'], info['seed'], t=t, n=n)
        sub = cv[y0:y1, x0:x1]
        if base is None:
            base = sub.copy()
        outs.append(np.where(sub != base, sub, -1))
    return outs



def plunge(cv: np.ndarray, xl: int, xr: int, y1: int, seed: int, t: int = 0, n: int = PLUNGE_FRAMES,
           rings: bool = True, seat_gaps: bool = False) -> np.ndarray:
    """The white water where a fall lands (texels; the sheet's foot spans xl .. xr at row y1), after
    the woodland review (4 Nov: a flat two-tone plate twice the sheet's width; Eastward 37's mist).
    It keeps to the foot plus PLUNGE_PAD each side and about 10 texels down; it is a heap of broken
    clumps, each lit white on its upper left over a pale blue-grey body, mid-blue water showing in
    the gaps between them, a darker band under its downstream edge; its outline breaks into
    loose flecks that dissolve into the pool; spray specks fly up beside the foot (on the water
    only: no spray on the face, Matt, 2 Nov); ripple arcs spread downstream. Only water (and the
    sheet's own foot) is painted, so the stones beside the fall keep their wet feet.

    `t` (0 .. n-1) is the frame: the clumps swell, drift and break, flecks pop, spray rises and
    the arcs travel downstream, in a closed loop; frame 0 is the still. Returns the foam mask."""
    H, W = cv.shape
    rng = np.random.default_rng(seed * 31 + 7)
    fw = max(4, xr - xl)
    cx = (xl + xr) / 2.0
    X0, Y0, X1, Y1 = plunge_box(xl, xr, y1, H, W)
    sub = cv[Y0:Y1, X0:X1]
    ok = (np.isin(sub // 8, [FI[n_] for n_ in WATERS] + [FI['snow']]) & (sub >= 0))
    ok &= ~((np.arange(Y0, Y1)[:, None] < y1) & ~((np.arange(X0, X1)[None, :] >= xl) & (np.arange(X0, X1)[None, :] < xr)))
    yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(float)
    a = 2.0 * math.pi * t / n
    best = np.full(sub.shape, 9.0)
    lit = np.zeros(sub.shape)
    K = max(9, int(fw / 4) + 8)
    for k in range(K):
        u = rng.uniform(-1.0, 1.0)
        px = cx + u * (fw / 2.0 + PLUNGE_PAD * 0.4) * rng.uniform(0.6, 1.0)
        py = y1 + rng.uniform(-0.5, 5.5) * (1.0 - 0.45 * abs(u))
        r = rng.uniform(2.4, 6.5) * (1.25 - 0.55 * abs(u))
        if k == 0:
            u, r = 0.0, max(6.5, fw / 7.0)                  # one large heap under the sheet's middle
            px, py = cx + rng.uniform(-1.5, 1.5), y1 + 2.5
        ph = rng.uniform(0.0, 2.0 * math.pi)
        swell = 1.0 + 0.28 * math.sin(a + ph)
        if t and k and math.sin(a + ph) < -0.8:
            continue                                         # this clump has broken (its flecks below)
        dx, dy = 1.1 * math.sin(a + 1.7 * ph), 0.9 * math.sin(a + ph + 1.0)
        rx, ry = r * swell, r * 0.7 * swell
        q = ((xx - px - dx) / rx) ** 2 + ((yy - py - dy) / ry) ** 2
        nearer = q < best
        best = np.where(nearer, q, best)
        lit = np.where(nearer, -((xx - px - dx) / rx + (yy - py - dy) / ry), lit)
    inside = (np.abs(xx - cx) <= fw / 2.0 + PLUNGE_PAD) & (yy <= y1 + 10)
    foam = (best < 1.0) & ok & inside
    if seat_gaps:
        # (a piece's foot, review round 7, P7-2) under any stretch of 4 or more foot columns that no
        # clump reaches in its first rows, seat one more clump, so the sheet never ends in a ruler
        # line on the water, in any frame; no draws from rng, so the other clumps are unchanged
        cover = foam[(yy[:, 0] >= y1) & (yy[:, 0] < y1 + 3)].any(0)
        cols_ = (xx[0] >= xl) & (xx[0] < xr)
        bare = cols_ & ~cover
        for a_, b_ in _runs(bare):
            if b_ - a_ < 4:
                continue
            px = X0 + (a_ + b_) / 2.0 + 0.6 * math.sin(a + a_)
            py = y1 + 1.8 + 0.5 * math.sin(a + 1.3 * a_)
            rx, ry = (b_ - a_) / 2.0 + 1.5, 2.6
            q = ((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2
            nearer = q < best
            best = np.where(nearer, q, best)
            lit = np.where(nearer, -((xx - px) / rx + (yy - py) / ry), lit)
        foam = (best < 1.0) & ok & inside
    out = sub.copy()
    gaps = ndi.binary_closing(foam, structure=np.ones((5, 5), bool)) & ~foam & ok & inside
    out[gaps] = C('water', 3)                                   # the pool showing between the clumps
    # each clump lit on its upper left, its lower right third in the blue-greys (review round 2, R2-4)
    tone = np.where((best < 0.5) & (lit > 0.1), 5, np.where(best < 0.78, np.where(lit > -0.4, 4, 3), np.where(lit > 0.2, 3, 2)))
    tone = np.where((lit < -0.55) & (best < 0.85), 2, tone)
    tone = np.where((lit < -0.95) & (best >= 0.6), 1, tone)
    out[foam] = (FI['snow'] * 8 + tone)[foam]
    # the outer rim dissolves into the pool in a checker on the shaded side (Eastward 37's mist)
    fray = foam & (best > 0.82) & (lit < 0.3) & (((xx + yy).astype(int) + t) % 2 == 0)
    out[fray] = C('water', 4)
    # a darker band under the downstream edge (its shade on the pool): a soft shade one texel deep
    # that follows the clumps' lobes, two where a lobe hangs lowest, never a comb of ticks (review
    # round 4, K4-3: the second row was a checker of navy ticks)
    mass = foam | gaps
    under = np.zeros_like(mass)
    under[1:] = mass[:-1]
    under &= ~mass & ok & (yy >= y1)
    bot = np.where(mass.any(0), mass.shape[0] - 1 - np.argmax(mass[::-1], 0), -1)
    hang = (bot >= 0) & (bot >= ndi.maximum_filter1d(bot, 5))          # where a lobe hangs lowest
    under2 = np.zeros_like(mass)
    for j in np.nonzero(hang)[0]:
        if bot[j] + 2 < mass.shape[0]:
            under2[bot[j] + 2, j] = True
    under2 &= ~mass & ~under & ok & (yy >= y1)
    under2 &= ndi.binary_dilation(under2, structure=np.array([[0, 0, 0], [1, 0, 1], [0, 0, 0]], bool))   # runs, not ticks
    out[under] = C('water', 1)
    out[under2] = C('water', 2)
    taken = mass | under | under2
    # flecks round the outline, dissolving into the pool: pairs and singles that pop in and out
    for j in range(int(fw / 3) + 10):
        ang = rng.uniform(0.0, math.pi) if rng.random() < 0.8 else rng.uniform(math.pi, 2 * math.pi)
        rr = rng.uniform(1.05, 1.5)
        fx_ = cx + math.cos(ang) * (fw / 2.0 + PLUNGE_PAD * 0.6) * rr
        fy_ = y1 + 3.0 + math.sin(ang) * 6.0 * rr
        on = ((t + j * 3) % n) < 5
        if not on:
            continue
        X, Y = int(round(fx_ + 0.7 * math.sin(a + j))) - X0, int(round(fy_ + 0.5 * math.cos(a + j))) - Y0
        pair = rng.random() < 0.6
        for (b_, c_) in ((0, C('snow', 4)), (1, C('snow', 2))) if pair else ((0, C('snow', 3)),):
            if 0 <= Y < out.shape[0] and 0 <= X + b_ < out.shape[1] and ok[Y, X + b_] and not taken[Y, X + b_]:
                out[Y, X + b_] = c_
    # spray: specks of one and two texels thrown out beside the foot in a loose fan, larger and
    # denser near the foot, thinning outward, each its own size and phase (review round 4, K4-3: a
    # row of identical ticks on alternate columns, and a lone block); over the pool only (no spray
    # on the face, Matt, 2 Nov) and within the foot plus PLUNGE_PAD - 2
    spr = np.random.default_rng(seed * 53 + 11).random((10, 6))       # the same specks in every frame
    for j in range(10):
        side = -1 if j % 2 else 1
        r_ = spr[j]
        d = PLUNGE_PAD * (0.15 + 0.75 * r_[0] ** 1.6)                      # nearer the foot more often
        if r_[1] >= 1.0 - 0.6 * d / PLUNGE_PAD:
            continue                                                        # thinning outward
        if ((t + j * 5) % n) >= 6 - int(2 * d / PLUNGE_PAD):
            continue                                                        # it has fallen back
        sx = (xl - 1 - d) if side < 0 else (xr + d)
        sy = y1 + 1 + 0.45 * d + (r_[2] * 2.0 - 1.0) - 1.5 * math.sin(a + 6.3 * r_[3]) ** 2
        X, Y = int(round(sx)) - X0, int(round(sy)) - Y0
        big = d < PLUNGE_PAD * 0.45 and r_[4] < 0.6
        cells = [(0, 0, C('snow', 5 if big else 4))]
        if big:
            cells.append((0, side, C('snow', 3)) if r_[5] < 0.5 else (1, 0, C('snow', 3)))
        for (dy_, dx_, c_) in cells:
            Yb, Xb = Y + dy_, X + dx_
            if not (0 <= Yb < out.shape[0] and 0 <= Xb < out.shape[1]):
                continue
            if abs(Xb + X0 - cx) > fw / 2.0 + PLUNGE_PAD - 2:
                continue
            if ok[Yb, Xb] and not taken[Yb, Xb] and Yb + Y0 >= y1:
                out[Yb, Xb] = c_
    if rings:
        # ripple arcs spreading downstream from the foam, broken, fading as they go
        top = int(np.max(np.nonzero(mass.any(1))[0])) + Y0 if mass.any() else y1 + 6
        for k in range(3):
            r = 4.0 + ((k * 6.0 + t * 6.0 / n) % 18.0)
            rx, ry = fw / 2.0 + r * 0.9, 2.0 + r * 0.55
            q = ((xx - cx) / rx) ** 2 + ((yy - (top - 2)) / ry) ** 2
            arc = (np.abs(q - 1.0) < 1.1 / max(rx, 1.0) + 0.04) & (yy > top) & ok & ~taken
            arc &= (((xx.astype(int) // (5 + k)) + k) % 3) != 0
            out[arc] = C('water', 5 if r < 9 else (4 if r < 15 else 3))
    cv[Y0:Y1, X0:X1] = out
    full = np.zeros((H, W), bool)
    full[Y0:Y1, X0:X1] = foam
    return full



# ------------------------------------------------------------------------------------------------
# the moon circle's standing stones
# ------------------------------------------------------------------------------------------------
def standing_stone(w: float, h: float, seed: int, lean: float = 0.0, broken: bool = False,
                   carved: str | None = None, squat: bool = False):
    """An ancient standing stone (Matt, 27 Oct 11:08: "the stones are not interesting enough"): a
    rough upright slab w x h world px, its silhouette its own (leaning `lean` of its width, a squat
    block, or `broken` off in a jagged top), its face weathered into plates with cracks, lichen in
    yellow and grey-green rosettes on the lit side, moss at its foot; `carved`: a spiral ('spiral')
    or rune strokes ('runes') cut into the face, the grooves dark with a lit lower lip (the circle
    held the moon's light). Returns (codes, (ax, ay) the foot's centre)."""
    rng = np.random.default_rng(seed)
    pad = _P(3)
    Wt, Ht = _P(w) + 2 * pad + int(abs(lean) * _P(w)) + 2, _P(h) + 2 * pad
    a = np.full((Ht, Wt), -1, np.int32)
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    yb, yt = Ht - pad, pad
    base_cx = Wt / 2.0 - lean * _P(w) / 2.0
    t = (yb - yy) / max(1.0, yb - yt)                                    # 0 foot .. 1 top
    cx = base_cx + lean * _P(w) * t
    half0 = _P(w) / 2.0
    taper = 0.05 if squat else 0.22
    wob = (_field(Ht, 1, seed + 9, 2.0)[:, :1] - 0.5)
    half = half0 * (1.0 - taper * t) + wob * 2.2
    u = (xx - cx) / np.maximum(half, 1)
    body = (np.abs(u) <= 1.0) & (yy <= yb)
    # the top: a rough, sloping crown, or a broken jagged edge
    sl = (1 if seed % 2 else -1) * rng.uniform(0.15, 0.4)
    crown = yt + _P(h) * 0.08 * (1 + sl * u) + _P(w) * 0.35 * np.clip(np.abs(u) - 0.35, 0, 1) ** 1.4 * 2.0
    if broken:
        jag = np.round((_field(1, Wt, seed + 4, 2.5)[0][None, :] - 0.5) * _P(3) / 2.0) * 2.0 + _P(h) * 0.14 * np.clip(u + 0.2, 0, 1)
        crown = crown + jag
    body &= yy >= crown + (_field(1, Wt, seed + 7, 1.5)[0][None, :] - 0.5) * 2.0
    capd = _P(1.6) if not broken else _P(1.2)
    capm = body & (yy < crown + capd)
    f = _field(Ht, Wt, seed + 2, 1.6)
    lv = 3.3 - 1.4 * u + (f - 0.5) * 1.8 + 0.4 * t
    tone = np.clip(np.round(lv), 1, 4)
    tone = np.where(u > 0.8, 1, tone)
    tone = np.where(capm, np.clip(np.round(4.6 - 1.2 * u + (f - 0.5)), 3, 5), tone)
    if broken:                                                           # the fresh break, paler
        tone = np.where(capm, np.clip(tone + 0, 3, 5), tone)
    tone = np.where(body & (yy >= yb - _P(1.2)), np.maximum(1, tone - 1), tone)
    _paint(a, body, 'stone', tone)
    if broken:
        a[capm] = np.where((a[capm] % 8) >= 4, C('ashlar_warm', 4) if 'ashlar_warm' in FI else a[capm], a[capm])
    _weather(a, body & ~capm, rng, 11, vertical=True)
    # deep weathering: hollows worn into the face (a tone or two down, their upper-left rim lit)
    ys_, xs_ = np.nonzero(body & ~capm & (yy < yb - _P(3)))
    for k_ in rng.permutation(len(ys_))[: 2 + int(w * h / 90)]:
        y_, x_ = int(ys_[k_]), int(xs_[k_])
        r_ = rng.uniform(1.2, 2.2)
        hol = body & (((xx - x_) / (r_ * 1.3)) ** 2 + ((yy - y_) / r_) ** 2 <= 1.0)
        a[hol] = step(a[hol], -2)
        rim = body & ~hol & np.roll(np.roll(hol, 1, 0), 1, 1)
        a[rim & (a % 8 < 5)] = step(a[rim & (a % 8 < 5)], 1)
    _cracks(a, body & ~capm, rng, 3 + int(broken), base_cx - half0 * 0.6, base_cx + half0 * 0.5, yt + _P(4), yb - _P(4))
    # the lit planes weather most: short upright grain a tone down all over them
    lit_ = body & (a % 8 >= 4)
    ly_, lx_ = np.nonzero(lit_)
    for kk in rng.permutation(len(ly_))[: len(ly_) // 6]:
        y_, x_ = int(ly_[kk]), int(lx_[kk])
        if y_ + 1 < Ht and lit_[y_ + 1, x_]:
            a[y_:y_ + 2, x_] = step(a[y_:y_ + 2, x_], -1 if rng.random() < 0.75 else 1)
    # carving: grooves dark, their lower lip lit (cut into a face lit from the upper left)
    if carved:
        ccx, ccy = base_cx - half0 * 0.1 + lean * _P(w) * 0.5, yt + (yb - yt) * 0.42
        pts = []
        if carved == 'spiral':
            for k in range(70):
                th = k * 0.22
                r = 0.5 + th * _P(0.42) / (2 * math.pi) * 2.2
                pts.append((ccy + r * math.sin(th) * 0.9, ccx + r * math.cos(th)))
        else:
            for k_ in range(3):
                X0 = ccx - _P(3) + k_ * _P(3)
                for j in range(_P(5)):
                    pts.append((ccy - _P(2.5) + j, X0))
                    if j in (1, 3):
                        pts.append((ccy - _P(2.5) + j, X0 + 1 + (j % 2)))
        for (py, px) in pts:
            Y, X = int(round(py)), int(round(px))
            if 0 <= Y < Ht - 1 and 0 <= X < Wt and body[Y, X] and body[Y + 1, X]:
                a[Y, X] = C('stone_cool', 0)
                if a[Y + 1, X] != C('stone_cool', 0):
                    # the groove's lower lip catches the light, a cold moonlit gleam
                    a[Y + 1, X] = C('sky', 5) if 'sky' in FI else C('stone_warm', 5)
    _lichen(a, body & (u < 0.3) & ~capm, rng, int(w * h / 38) + 2)
    _moss(a, body & (yy >= yb - _P(3) - 2 * f * _P(1)), seed + 3, share=0.4)
    _outline(a, a >= 0, u)
    # the foot: no hard line where the stone meets the ground; grass grows up against it in blades
    # of uneven height (lit and shaded), past its sides, and a few small flowers
    bl = yb - 1
    for X in range(max(0, int(base_cx - half0) - 3), min(Wt, int(base_cx + half0) + 4)):
        if rng.random() < 0.18:
            continue
        L = int(rng.integers(2, _P(2.4) + 1))
        lit = rng.random() < 0.45
        for j in range(L):
            Y = bl - j + 1
            if 0 <= Y < Ht:
                tt = (4 if lit else 3) if j >= L - 1 else (2 if j == 0 else 3)
                a[Y, X] = C('grass_warm' if lit else 'grass', tt)
    for _ in range(int(rng.integers(1, 3))):
        fx = int(base_cx + rng.uniform(-half0 - 2, half0 + 2))
        fy = bl - int(rng.integers(1, 3))
        col = ('plaster', 5) if rng.random() < 0.6 else ('sand_warm', 5)
        for dy, dx in ((0, 0), (-1, 0), (0, -1), (0, 1), (1, 0)):
            Y, X = fy + dy, fx + dx
            if 0 <= Y < Ht and 0 <= X < Wt:
                a[Y, X] = C(*col) if (dy, dx) != (0, 0) else C('brass', 4)
    return a, (base_cx, yb)


def lintel(w: float, h: float, seed: int):
    """A fallen capstone lying in the grass: a long slab seen from above and a little in front, its
    top weathered and lichened, a front face in shade, sunk at one end, moss along its foot."""
    a, anc = rock(w, h, seed, flat=True, moss=0.35)
    return a, anc


def face(cv: np.ndarray, x0: float, y0: float, x1: float, y1: float, seed: int = 5) -> None:
    """The cascade's rock face behind the fall (world px): a rounded block of wet rock in shade,
    its plates running down in vertical bands, darker near the water, moss streaks where the
    spray keeps it wet; the slabs and the fall are laid over it."""
    H, W = cv.shape
    D = ctx.D
    rng = np.random.default_rng(seed)
    X0, Y0, X1, Y1 = _P(x0, 0), _P(y0, 0), _P(x1, 0), _P(y1, 0)
    yy, xx = np.mgrid[Y0:Y1, X0:X1]
    u = (xx - (X0 + X1) / 2.0) / max(1.0, (X1 - X0) / 2.0)
    v = (yy - Y0) / max(1.0, Y1 - Y0)
    m = (np.abs(u) <= 1.0 - 0.25 * np.clip(v - 0.8, 0, 1) * 5) & (np.abs(u) <= 1.0 - 0.3 * np.clip(0.15 - v, 0, 1) * 6)
    f = _field(Y1 - Y0, X1 - X0, seed, 1.5)
    band = (np.floor((xx - X0) / _P(2.2)) % 3)
    t = np.clip(np.round(2.2 - 0.9 * u + (f - 0.5) * 1.6 - 0.5 * (band == 2)), 0, 3).astype(int)
    fam = np.where(t >= 3, FI['stone'], FI['stone_cool'])
    sub = cv[Y0:Y1, X0:X1]
    sub[m] = (fam * 8 + t)[m]
    mo = m & (_field(Y1 - Y0, X1 - X0, seed + 1, 1.2) > 0.72)
    sub[mo] = np.where(f[mo] > 0.5, C('leaf', 3), C('leaf_cool', 2))

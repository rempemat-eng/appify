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
def fall(cv: np.ndarray, x0: float, w: float, y0: float, y1: float, seed: int = 11) -> None:
    """The water over the lip and down into the pool (world px): at the lip the water thickens and
    curls over the rock's lit edge, catching the light in a bright band; the sheet widens a little
    as it falls, shaded as a ribbon (lit west, body, shade east), with streaks running at different
    speeds (long and short, bright and dim) and a darker thinning near the foot; white foam and
    spray where it lands, and rings of ripples spreading on the pool."""
    H, W = cv.shape
    D = ctx.D
    rng = np.random.default_rng(seed)
    cx = x0 + w / 2.0
    cols = {}
    for Y in range(_P(y0 - 1.5, 0), _P(y1, 0)):
        yw = (Y + 0.5) / D
        f = (yw - y0) / max(1.0, (y1 - y0))
        hw = w / 2.0 + 0.6 + max(0.0, f) * 2.4                           # wider as it falls
        if yw < y0:                                                      # the curl over the lip: a bulge
            hw = w / 2.0 + 0.9
        hl = hw + 0.35 * math.sin(yw / 3.1)
        hr = hw + 0.35 * math.sin(yw / 2.6 + 1.0)
        for X in range(max(0, _P(cx - hw - 1.5, 0)), min(W, _P(cx + hw + 1.5, 0) + 1)):
            uu = (X + 0.5) / D - cx
            if not (-hl <= uu <= hr) or not (0 <= Y < H):
                continue
            s = (uu + hl) / (hl + hr)
            bulge = 1.4 * (1.0 - (2.0 * s - 1.0) ** 2)               # the curl hangs lowest mid-sheet
            if yw < y0 - 0.6:
                cv[Y, X] = C('water', 4) if s < 0.6 else C('water', 3)   # glassy water sliding to the edge
                continue
            if yw < y0 + 0.2 + bulge:
                # the water thickening as it bends over the edge: a lit band, a white crest at its rim
                rim = yw > y0 - 0.2 + bulge
                c = C('snow', 5) if (rim and s < 0.8) else (C('water', 5) if s < 0.55 else C('water', 4))
                cv[Y, X] = c
                continue
            if yw < y0 + 1.2 + bulge:
                cv[Y, X] = C('water', 2) if s > 0.15 else C('water', 3)    # the shade just under the curl
                continue
            tt = 4 if s < 0.2 else (3 if s < 0.6 else (2 if s < 0.85 else 1))
            if f > 0.75:
                tt = max(1, tt - 1)                                      # thinner and darker near the foot
            c = C('water', tt)
            key = int(((X + 0.5) / D - (cx - hw)) * 2.2)
            if key not in cols:
                # each streak its own speed: long fast ones and short slow ones
                cols[key] = (rng.uniform(0, 40), rng.uniform(4, 18), rng.uniform(2, 9), rng.random())
            ph, run, gap, kind = cols[key]
            if ((yw - y0 + ph) % (run + gap)) < run and 0.05 < s < 0.85:
                c = C('snow', 5) if (kind < 0.35 and s < 0.5) else (C('snow', 4) if kind < 0.7 else C('water', 5))
            cv[Y, X] = c
    # foam and spray where it lands
    parts = [(cx + rng.uniform(-0.8, 0.8) * w, y1 + rng.uniform(-0.8, 0.5) * 2.4, w * rng.uniform(0.4, 0.75),
              2.4 * rng.uniform(0.6, 1.0)) for _ in range(8)]
    for Y in range(_P(y1 - 5, 0), _P(y1 + 5, 0) + 1):
        for X in range(_P(cx - w * 2, 0), _P(cx + w * 2, 0) + 1):
            if not (0 <= Y < H and 0 <= X < W):
                continue
            r = min(((X / D - px) / pw) ** 2 + ((Y / D - py) / ph) ** 2 for (px, py, pw, ph) in parts)
            if r <= 1.0:
                lit = (X / D - cx) < 0.3 * w
                cv[Y, X] = C('snow', 5) if (r < 0.55 and lit) else (C('snow', 4) if r < 0.8 else C('snow', 2))
    water = np.isin(cv // 8, [FI[n] for n in WATERS])
    for k, (rx, ry) in enumerate(((w * 1.5, 2.4), (w * 2.2, 3.4), (w * 3.0, 4.4))):
        for Y in range(_P(y1 - ry, 0), _P(y1 + ry + 2.5, 0) + 1):
            for X in range(_P(cx - rx - 1, 0), _P(cx + rx + 1, 0) + 1):
                if not (0 <= Y < H and 0 <= X < W) or not water[Y, X]:
                    continue
                q = ((X / D - cx) / rx) ** 2 + ((Y / D - (y1 + 1.0)) / ry) ** 2
                if abs(q - 1.0) < 0.08 and (Y / D) > y1 - 0.5 and ((X // _P(2)) + k) % 3:
                    cv[Y, X] = C('water', 5 - min(k, 2))
    for k in range(14):
        side = -1 if k % 2 else 1
        sx = cx + side * (w * 0.9 + (k // 2) * 1.2 + rng.uniform(0, 1.2))
        sy = y1 - 2.0 - (k // 2) * 1.1 - rng.uniform(0, 1.0)
        Y, X = _P(sy, 0), _P(sx, 0)
        for (a_, b_) in ((0, 0), (0, 1), (1, 0)):
            if 0 <= Y + a_ < H and 0 <= X + b_ < W and (k < 6 or (a_, b_) == (0, 0)):
                cv[Y + a_, X + b_] = C('snow', 5) if k < 6 else C('snow', 4)


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
    _weather(a, body & ~capm, rng, 16, vertical=True)
    _cracks(a, body & ~capm, rng, 2 + int(broken), base_cx - half0 * 0.6, base_cx + half0 * 0.5, yt + _P(4), yb - _P(4))
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
                a[Y, X] = C('stone_cool', 1)
                if a[Y + 1, X] != C('stone_cool', 1):
                    a[Y + 1, X] = C('stone_warm', 4)
    _lichen(a, body & (u < 0.3) & ~capm, rng, int(w * h / 38) + 2)
    _moss(a, body & (yy >= yb - _P(3) - 2 * f * _P(1)), seed + 3, share=0.4)
    _outline(a, a >= 0, u)
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

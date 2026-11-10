"""The woodland circle's standing stones, its fallen lintel and the stone top at density 3 and up (the
9 Nov detail audit, findings W-S1 to W-S5, docs/reviews/2026-11-09-woodland-assets.md; the stone
recipe and eastward-edges 2.3; Eastward's rocks in 17 and 12 at the same character height).

A stone is 3 to 5 calm planes, each a few tones, not speckle:

- a lit crown (stone 4) with a stone 5 rim on its upper-left arris;
- a mid west face (stone 3) and a darker east flank (stone 1 to 2), met at a wandering arris;
- a dark underside at the foot and a contact line one texel under it (no baked grass skirt; the
  ground's tufts grow over the foot);
- texture only as sibling swaps (stone, stone warm, stone cool, ashlar at the same value) in
  clusters of 2 to 4 texels and a few one-tone steps;
- 2 or 3 chips knocked off the arrises (a notch in the lit edge with a shade texel under it);
- cracks 2 texels wide: a dark line with a lit lower lip;
- lichen as irregular crusts of 2 to 3 sibling tones, 3 to 10 texels across, on the lit and upper
  faces, no two the same shape; moss low on the shaded east and in the cracks, a 2-texel cap over a
  4-texel band;
- carving cut as grooves 2 texels wide, stone 1 on the upper (shaded) edge and stone 4 on the lower
  lip, weathered and broken in places; a broken stone ends in a lit, jagged fracture plane.

Third pass (round 2, W2-S1 to W2-S5): texture by plane (calm patches on the lit crown, smaller blocks
on the cool shaded flank), a damp band at the foot, lobed lichen crusts, moss as clumps placed
differently on each stone, a whole lit rim, grooves cut with a shaded wall and a lit lip, runes as
branching glyphs, the broken stone's fracture as its own stepped plane, and a lintel with a sagging
top, rounded and chipped corners and its lit top edge showing. The stone round 2 passed
(standing_stone_lean, seed 933) keeps the second pass byte for byte (KEEP_PASS2).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from . import ctx
from .palette import C
from .woodtrees import Ladder, _clean, _lum

STONES = ('stone', 'stone_warm', 'stone_cool', 'ashlar', 'ashlar_warm')
LICHEN = ('brass', 'sand_warm', 'sand')


def _P(v, lo=1):
    return max(lo, int(round(v * ctx.D)))


def _planes(code, body, val, lad, rng, cell=5.5, facet=9.0):
    """Paint `body` from a value field as calm planes: each plane cut into facets (cells about `cell`
    texels across, each a few L off its neighbours, as weathered rock breaks into faces), the value
    posterised into steps of about 12 L, each step drawn in clusters of 2 to 4 sibling texels at the
    same value (shape without value noise), never single-texel speckle."""
    H, W = body.shape
    yy, xx = np.mgrid[0:H, 0:W]
    seeds = []
    for j, y in enumerate(np.arange(-cell, H + cell, cell * 0.8)):
        for x in np.arange(-cell, W + cell, cell) + (cell / 2) * (j % 2):
            seeds.append((x + rng.uniform(-2, 2), y + rng.uniform(-2, 2)))
    S_ = np.array(seeds)
    d2 = (xx[..., None] - S_[:, 0]) ** 2 + ((yy[..., None] - S_[:, 1]) * 1.3) ** 2
    cellid = np.argmin(d2, axis=2)
    off = rng.uniform(-facet, facet, len(seeds))
    v = val + off[cellid]
    q = np.round(v / 12.0) * 12.0
    # clusters: 2 x 2 blocks, some joined into 2 x 3 or 3 x 2
    by = (yy + (xx // 3) % 2) // 2
    bx = (xx + (yy // 3) % 2) // 2
    bid = by * (W + 4) + bx
    r = np.random.default_rng(int(rng.integers(0, 1 << 30))).random(bid.max() + 1)[bid]
    for vv in np.unique(q[body]):
        m = body & (q == vv)
        opts = [lad.pick(vv, rng, 5)]
        for _ in range(2):
            opts.append(lad.pick(vv + rng.uniform(-3, 3), rng, 6, avoid=tuple(opts)))
        k = np.where(r[m] < 0.45, 0, np.where(r[m] < 0.8, 1, 2))
        code[m] = np.array(opts)[k]
    # each facet's upper-left edge a step lighter where it meets the facet above it (the break)
    P = np.pad(cellid, 1, mode='edge')
    brk = body & (cellid != P[:-2, 1:-1]) & (off[cellid] > 0)
    for y, x in zip(*np.nonzero(brk)):
        if rng.random() < 0.6:
            code[y, x] = lad.pick(_lum(int(code[y, x])) + 12, rng, 5)
    dk = body & (cellid != P[2:, 1:-1]) & (off[cellid] < 0)
    for y, x in zip(*np.nonzero(dk)):
        if rng.random() < 0.6:
            code[y, x] = lad.pick(_lum(int(code[y, x])) - 12, rng, 5)


def _flakes(code, zone, lad, rng, n):
    """Flakes come away as small plates (2 x 2 to 3 x 3 texels) a step down, lit on their upper and
    west edge: clusters, never single texels or ruled dashes."""
    H, W = code.shape
    ys, xs = np.nonzero(zone)
    for k in rng.permutation(len(ys))[:n]:
        y, x = int(ys[k]), int(xs[k])
        h_, w_ = int(rng.integers(2, 4)), int(rng.integers(2, 4))
        if y + h_ >= H or x + w_ >= W or y < 1 or x < 1 or not zone[y:y + h_, x:x + w_].all():
            continue
        b_ = _lum(int(code[y, x]))
        code[y:y + h_, x:x + w_] = lad.pick(b_ - 12, rng, 5)
        if zone[y - 1, x:x + w_].all():
            code[y - 1, x:x + w_] = lad.pick(b_ + 12, rng, 5)


def _groove(code, body, pts, lad, rng, breaks=2):
    """A groove 2 texels wide along pts: its upper edge in shade (stone 1), its lower lip catching
    the light (stone 4), broken off in `breaks` places."""
    H, W = code.shape
    n = len(pts)
    gaps = set()
    for _ in range(breaks):
        g = int(rng.integers(3, max(4, n - 3)))
        gaps.update(range(g, g + 2))
    done = set()
    for i, (py, px) in enumerate(pts):
        if i in gaps:
            continue
        Y, X = int(round(py)), int(round(px))
        for (dy, c) in ((0, C('stone_cool', 1)), (1, C('stone_cool', 1)), (2, C('stone', 4))):
            for dx in (0, 1) if dy < 2 else (0,):
                y_, x_ = Y + dy, X + dx
                if 0 <= y_ < H and 0 <= x_ < W and body[y_, x_] and (y_, x_) not in done:
                    if dy < 2:
                        code[y_, x_] = c
                        done.add((y_, x_))
                    elif code[y_, x_] != C('stone_cool', 1):
                        code[y_, x_] = c


def _crack(code, body, x, y, L, lad, rng, dirx=0.25):
    H, W = code.shape
    for k in range(L):
        X, Y = int(round(x)), int(round(y))
        if not (0 <= Y < H - 2 and 1 <= X < W - 1) or not body[Y, X]:
            break
        code[Y, X] = C('stone_cool', 0)
        if body[Y, X + 1] and k % 3:
            code[Y, X + 1] = C('stone_cool', 0)          # two texels wide in places
        if body[Y + 1, X - 1] and code[Y + 1, X - 1] != C('stone_cool', 0):
            code[Y + 1, X - 1] = C('stone', 4)            # the lit lower lip
        y += 1
        x += dirx + rng.uniform(-0.6, 0.6)


def _lichen(code, body, zone, rng, n):
    """Crusts of 2 to 3 sibling tones, 3 to 10 texels across, each its own shape."""
    H, W = code.shape
    ys, xs = np.nonzero(zone)
    if not len(ys):
        return
    for k in rng.permutation(len(ys))[:n]:
        y, x = int(ys[k]), int(xs[k])
        size = rng.uniform(3, 10)
        pts = [(y, x)]
        m = np.zeros((H, W), bool)
        m[y, x] = True
        for _ in range(int(size * size * 0.35)):
            py, px = pts[int(rng.integers(0, len(pts)))]
            dy, dx = [(0, 1), (0, -1), (1, 0), (-1, 0)][int(rng.integers(0, 4))]
            ny, nx = py + dy, px + dx
            if 0 <= ny < H and 0 <= nx < W and zone[ny, nx] and abs(nx - x) <= size / 2 + 1 and abs(ny - y) <= size / 3 + 1:
                m[ny, nx] = True
                pts.append((ny, nx))
        if m.sum() < 3:
            continue
        fam = LICHEN[int(rng.integers(0, len(LICHEN)))]
        code[m] = C(fam, 3)
        P = np.pad(m, 1)
        code[m & ~P[:-2, 1:-1]] = C(fam, 4)                # the crust's lit upper edge
        code[m & ~P[2:, 1:-1] & ~P[:-2, 1:-1]] = C(fam, 2)


def _moss(code, body, zone, rng):
    """Moss low on the shaded side and in cracks: a 2-texel cap over a 4-texel band."""
    f = ndi.gaussian_filter(rng.random(body.shape), 1.6)
    f = (f - f.min()) / max(1e-6, f.max() - f.min())
    m = zone & (f > 0.55)
    m = ndi.binary_opening(m, iterations=1)
    code[m] = C('leaf', 2)
    P = np.pad(m, 1)
    cap = m & ~P[:-2, 1:-1]
    cap |= m & np.pad(cap, ((1, 0), (0, 0)))[:-1]
    code[cap] = C('leaf', 3)
    code[m & ~P[2:, 1:-1]] = C('leaf_cool', 1)


def _chips(code, body, lad, rng, edge_pts, n):
    H, W = code.shape
    for k in rng.permutation(len(edge_pts))[:n]:
        y, x = edge_pts[k]
        w = int(rng.integers(2, 4))
        for dx in range(w):
            if 0 <= x + dx < W and body[y, x + dx]:
                body[y, x + dx] = False
                code[y, x + dx] = -1
                if y + 1 < H and body[y + 1, x + dx]:
                    code[y + 1, x + dx] = C('stone_cool', 1)      # the shade under the notch


def _outline(code, body, u, v3=False):
    edge = body & ~ndi.binary_erosion(body)
    P = np.pad(body, 1)
    west_top = edge & (~P[1:-1, :-2] | ~P[:-2, 1:-1]) & P[2:, 1:-1] & (u < 0.15)
    code[edge & ~west_top] = C('stone_cool', 0)
    if v3:
        # the lit rim whole (no dark dashes on it, W2-S2): stone warm 5 in runs, stone 4 between
        yy = np.arange(code.shape[0])[:, None]
        run = ((yy // 3) % 3 == 2)
        code[west_top] = np.where(run[np.nonzero(west_top)[0], 0], C('stone', 4), C('stone_warm', 5))
        return
    lit = west_top & (code % 8 >= 3)
    code[lit] = C('stone_warm', 5)



# ------------------------------------------------------------------------------------------------
# third pass (round 2 of the detail audit, W2-S1 to W2-S5)
# ------------------------------------------------------------------------------------------------
KEEP_PASS2 = {933}       # seeds of the stones round 2 passed (standing_stone_lean): kept byte for byte
WARM = Ladder(('stone_warm', 'ashlar_warm', 'stone', 'sand_cool'), {'stone_warm': 2.0, 'sand_cool': 0.4})
LIT = Ladder(STONES + ('sand_cool',), {'stone_warm': 1.6, 'stone': 1.4, 'sand_cool': 0.4})
COOL = Ladder(('stone_cool', 'stone', 'slate_cool', 'ashlar'), {'stone_cool': 2.0, 'slate_cool': 0.3})


def _planes3(code, body, val, west, east, capm, rng, cells=(8.0, 5.0, 3.4)):
    """W2-S1: texture by plane. The lit crown in calm patches of 5 to 10 texels, the west face in
    blocks of 4 to 6 on the warm siblings, the shaded flank in smaller ones (2 to 4) on the cool
    siblings, as weathered rock: the light planes calm, the shade busier."""
    lad = Ladder(STONES, {'stone': 2.0})
    for zone, cell, facet, ld in ((capm, cells[0], 5.0, LIT), (west, cells[1], 7.0, WARM), (east, cells[2], 6.0, COOL)):
        z = body & zone
        if not z.any():
            continue
        tmp = np.full(code.shape, -1, np.int64)
        _planes(tmp, z, val, ld if ld is not None else lad, rng, cell=cell, facet=facet)
        code[z] = tmp[z]


def _moss3(code, body, spots, rng):
    """W2-S2: moss as clumps, each a 2-texel cap (leaf 3) over a band about 4 texels deep (leaf 2,
    its lowest row leaf cool 1), 3 to 6 texels wide, its lower edge ragged; spots [(y, x)]."""
    H, W = code.shape
    for (y, x) in spots:
        w = int(rng.integers(3, 7))
        d = int(rng.integers(3, 6))
        for i in range(w):
            dd = d - abs(i - w // 2) // 2 - int(rng.integers(0, 2))
            for j in range(max(2, dd)):
                Y, X = y + j, x + i - w // 2
                if 0 <= Y < H and 0 <= X < W and body[Y, X]:
                    code[Y, X] = C('leaf', 3) if j < 2 and 0 < i < w - 1 else (C('leaf', 2) if j < dd - 1 else C('leaf_cool', 1))
        # a drip into the joint below
        if rng.random() < 0.5:
            X = x + int(rng.integers(-w // 2 + 1, w // 2))
            for j in range(d, d + int(rng.integers(2, 4))):
                if 0 <= y + j < H and 0 <= X < W and body[y + j, X]:
                    code[y + j, X] = C('leaf_cool', 1)


def _lichen3(code, body, zone, rng, n, fams=LICHEN):
    """W2-S2: crusts 3 to 10 texels across, each its own lobed shape, in 2 or 3 sibling tones: a lit
    upper rim, a body, a darker core or lower edge."""
    H, W = code.shape
    ys, xs = np.nonzero(zone)
    if not len(ys):
        return
    placed = []
    for k in rng.permutation(len(ys)):
        if len(placed) >= n:
            break
        y, x = int(ys[k]), int(xs[k])
        if any(abs(y - py) < 6 and abs(x - px) < 6 for (py, px) in placed):
            continue
        size = rng.uniform(3, 10)
        m = np.zeros((H, W), bool)
        for _ in range(int(rng.integers(2, 5))):                      # lobes
            cy_ = y + rng.uniform(-size / 4, size / 4)
            cx_ = x + rng.uniform(-size / 3, size / 3)
            r_ = rng.uniform(1.2, max(1.6, size / 3))
            yy, xx = np.ogrid[0:H, 0:W]
            m |= ((xx - cx_) / r_) ** 2 + ((yy - cy_) / (r_ * 0.75)) ** 2 <= 1
        m &= zone
        if m.sum() < 4:
            continue
        placed.append((y, x))
        fam = fams[int(rng.integers(0, len(fams)))]
        code[m] = C(fam, 3)
        P = np.pad(m, 1)
        code[m & ~P[:-2, 1:-1]] = C(fam, 4)
        core = ndi.binary_erosion(m) & ~np.pad(m, ((2, 0), (0, 0)))[:-2] | (m & ~P[2:, 1:-1] & P[:-2, 1:-1])
        code[core & m] = C(fam, 2)


def _groove3(code, body, pts, rng, breaks=1):
    """W2-S3: a groove cut 2 texels wide: its upper and west wall in shade (stone 1), its lower and
    east lip catching the light (stone 4), worn through in `breaks` places."""
    H, W = code.shape
    n = len(pts)
    gaps = set()
    for _ in range(breaks):
        if n > 6:
            g = int(rng.integers(2, n - 3))
            gaps.update(range(g, g + 2))
    dark, lit = set(), set()
    for i, (py, px) in enumerate(pts):
        if i in gaps:
            continue
        Y, X = int(round(py)), int(round(px))
        dark.add((Y, X))
    for (Y, X) in dark:
        for (dy, dx) in ((1, 0), (0, 1), (1, 1)):
            if (Y + dy, X + dx) not in dark:
                lit.add((Y + dy, X + dx))
    for (Y, X) in dark:
        if 0 <= Y < H and 0 <= X < W and body[Y, X]:
            code[Y, X] = C('stone_cool', 1)
    for (Y, X) in lit:
        if 0 <= Y < H and 0 <= X < W and body[Y, X]:
            code[Y, X] = C('stone', 4)


# runes: angular strokes in a 4 x 7 box (x, y), each glyph a stem with its own branches
RUNES = [
    [((0, 0), (0, 7)), ((0, 1), (3, 0)), ((0, 3), (3, 2))],            # fehu
    [((0, 0), (0, 7)), ((0, 0), (3, 2)), ((3, 2), (0, 4)), ((0, 4), (3, 7))],   # raido
    [((2, 0), (2, 7)), ((2, 2), (0, 0)), ((2, 2), (4, 0))],            # algiz
    [((2, 0), (2, 7)), ((2, 0), (0, 2)), ((2, 0), (4, 2))],            # tiwaz
    [((0, 0), (0, 7)), ((4, 0), (4, 7)), ((0, 0), (4, 4)), ((4, 0), (0, 4))],   # mannaz
    [((0, 0), (0, 7)), ((0, 2), (3, 4)), ((3, 4), (0, 6))],            # thurisaz
]


def _rune(code, body, x0, y0, glyph, rng, sc=1.0):
    for (a, b) in glyph:
        (xa, ya), (xb, yb) = a, b
        L = int(max(abs(xb - xa), abs(yb - ya)) * sc) + 1
        pts = [(y0 + (ya + (yb - ya) * t) * sc, x0 + (xa + (xb - xa) * t) * sc) for t in np.linspace(0, 1, L)]
        _groove3(code, body, pts, rng, breaks=0)


def _damp(code, body, yb, rng, P_):
    """W2-S1: a damp band at the foot, stone 1 to 2, with moss in its joints."""
    H, W = code.shape
    band = body & (np.arange(H)[:, None] >= yb - P_ - 1) & (np.arange(H)[:, None] < yb - 1)
    wav = (ndi.gaussian_filter1d(rng.random(W), 1.5) * 3).astype(int)
    band &= np.arange(H)[:, None] >= (yb - P_ - 1 + wav[None, :])
    f = ndi.zoom(rng.random((H // 2 + 2, W // 3 + 2)), (2, 3), order=0)[:H, :W]
    code[band] = np.where(f[band] > 0.5, C('stone_cool', 2), C('stone', 1))
    code[band & (f > 0.85)] = C('slate_cool', 2) if True else C('stone', 2)
    ys, xs = np.nonzero(band)
    for k in rng.permutation(len(ys))[: max(2, int(band.sum() / 18))]:
        y, x = int(ys[k]), int(xs[k])
        if x + 1 < W and band[y, x + 1]:
            code[y, x] = code[y, x + 1] = C('leaf', 2) if rng.random() < 0.6 else C('leaf_cool', 2)



def standing_stone(w: float, h: float, seed: int, lean: float = 0.0, broken: bool = False,
                   carved: str | None = None, squat: bool = False):
    """An ancient standing stone, w x h world px. Returns (codes, (ax, ay) the foot's centre)."""
    rng = np.random.default_rng(seed)
    v3 = seed not in KEEP_PASS2
    lad = Ladder(STONES, {'stone': 2.0})
    pad = _P(2)
    Wt = _P(w) + 2 * pad + int(abs(lean) * _P(w)) + 2
    Ht = _P(h) + 2 * pad
    code = np.full((Ht, Wt), -1, np.int64)
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    yb, yt = Ht - pad, pad
    base_cx = Wt / 2.0 - lean * _P(w) / 2.0
    t = (yb - yy) / max(1.0, yb - yt)
    cx = base_cx + lean * _P(w) * t
    half0 = _P(w) / 2.0
    taper = 0.05 if squat else 0.2
    wob = (ndi.gaussian_filter1d(rng.random(Ht), 2.5) - 0.5)[:, None] * 2.4
    half = half0 * (1.0 - taper * t) + wob
    u = (xx - cx) / np.maximum(half, 1)
    if squat:
        # W3-S1: no tombstone: the west side leans in toward the top, the east bulges 2 to 4 texels
        # about mid-height, so neither side runs straight
        r2 = np.random.default_rng(seed + 313)
        lean_w = r2.uniform(2.0, 3.5) * t
        bulge_e = r2.uniform(2.5, 4.0) * np.sin(np.pi * np.clip(t * 1.15, 0, 1)) ** 1.3
        wx = (xx - cx) / np.maximum(half - lean_w, 1)
        ex_ = (xx - cx) / np.maximum(half + bulge_e, 1)
        u = np.where(xx < cx, wx, ex_)
    body = (np.abs(u) <= 1.0) & (yy < yb)
    sl = (1 if seed % 2 else -1) * rng.uniform(0.15, 0.35)
    crown = yt + _P(h) * 0.07 * (1 + sl * u) + _P(w) * 0.33 * np.clip(np.abs(u) - 0.35, 0, 1) ** 1.4 * 2.0
    if squat:
        # one shoulder lower than the other
        crown = crown + _P(h) * 0.13 * np.clip(u * (1 if seed % 2 else -1), 0, 1)
    if broken:
        # a fracture: a jagged top in 1 to 2 texel steps, falling to the east
        steps = np.cumsum(rng.integers(0, 3, Wt)) * 0 + 0
        jag = np.zeros(Wt)
        level = 0.0
        for x in range(Wt):
            if x % int(rng.integers(2, 5)) == 0:
                level += rng.choice([-2, -1, 1, 2, 2])
            jag[x] = level
        jag = jag - jag.min()
        crown = yt + _P(h) * 0.06 + jag[None, :] * 0.6 + _P(h) * 0.16 * np.clip(u + 0.3, 0, 1.3)
        del steps
    body &= yy >= crown
    body = ndi.binary_opening(body, iterations=1)
    lab, n = ndi.label(body)
    if n > 1:
        sizes = ndi.sum(body, lab, range(1, n + 1))
        body = lab == (1 + int(np.argmax(sizes)))
    # the planes: the crown (lit), the west face, the east flank past a wandering arris, the foot
    capd = _P(1.4) if not broken else (_P(2.4) if v3 else _P(1.8))
    capm = body & (yy < crown + capd)
    ridge = 0.15 + (ndi.gaussian_filter1d(rng.random(Ht), 4) - 0.5)[:, None] * 0.6
    west = body & ~capm & (u < ridge)
    east = body & ~capm & (u >= ridge)
    val = np.zeros((Ht, Wt))
    val[west] = 132 + 10 * (-u[west]) + 6 * t[west]                   # stone 3, lighter toward the top-left
    val[east] = 92 - 18 * np.clip(u[east], 0, 1)
    val[capm] = 160 + 6 * (-u[capm])                                 # stone 4
    foot = body & (yy >= yb - _P(1.6))
    val[foot] = np.minimum(val[foot], 92) - 14
    if v3 and squat:
        _planes3(code, body, val, west, east, capm, rng, cells=(11.0, 6.0, 3.4))   # calmer lit crown (W3-S1)
    elif v3:
        _planes3(code, body, val, west, east, capm, rng)
    else:
        _planes(code, body, val, lad, rng)
    # the fracture plane on a broken stone: lit, in steps
    if broken and v3:
        # W2-S5: its own plane, lit (stone 4 to 5) with 1 to 2 texel steps along the break, its far
        # (upper) edge dark; the crown never runs over it
        code[capm] = C('stone', 4)
        xs_c = np.nonzero(capm.any(0))[0]
        x = xs_c.min() + int(rng.integers(2, 4))
        tone = 0
        while x <= xs_c.max():
            w_ = int(rng.integers(3, 6))
            sub = capm & (xx >= x) & (xx < x + w_)
            code[sub] = (C('stone_warm', 5), C('stone', 4), C('ashlar_warm', 4))[tone % 3]
            P = np.pad(sub, 1)
            code[sub & ~P[1:-1, :-2]] = C('stone', 3)                  # the riser of the step, 1 texel
            tone += 1
            x += w_
        P = np.pad(capm, 1)
        code[capm & ~P[:-2, 1:-1]] = C('stone_cool', 1)               # the far edge, dark
        code[capm & ~P[2:, 1:-1]] = C('stone', 3)                     # the near arris under it
    elif broken:
        for y, x in zip(*np.nonzero(capm)):
            code[y, x] = C('stone_warm', 5) if (x // 3 + y) % 4 == 0 else C('stone', 4)
        P = np.pad(capm, 1)
        code[capm & ~P[2:, 1:-1]] = C('stone', 3)
        step_edge = capm & ~P[1:-1, 2:]
        code[step_edge] = C('stone_cool', 1)
    # weathering: a few one-tone steps as small hollows (3 to 5 texels), lit on their lower lip
    ys, xs = np.nonzero(body & ~capm & ~foot)
    for k in rng.permutation(len(ys))[: 2 + int(w * h / 160)]:
        y, x = int(ys[k]), int(xs[k])
        m = body & (((xx - x) / 1.6) ** 2 + ((yy - y) / 1.0) ** 2 <= 1.0)
        if m.sum() < 3:
            continue
        code[m] = np.array([lad.pick(_lum(int(c)) - 14, rng, 5) for c in code[m]])
        lip = body & ~m & np.roll(m, 1, 0)
        code[lip] = np.array([lad.pick(_lum(int(c)) + 12, rng, 5) for c in code[lip]])
    _flakes(code, body & ~capm & ~foot, lad, rng, int(body.sum() / 22))
    # cracks
    starts = []
    for k in range((1 if v3 else 2) + int(broken)):
        sx = base_cx + rng.uniform(-0.5, 0.4) * half0
        sy = yt + (yb - yt) * rng.uniform(0.25, 0.6)
        starts.append((int(sy), int(sx)))
        _crack(code, body, sx, sy, int(rng.integers(_P(2), _P(5))), lad, rng)
    if v3:
        _damp(code, body, int(yb), rng, _P(1.4))
        _lichen3(code, body, body & (west | capm) & ~foot & (yy < yb - _P(3)), rng, 2 + int(w * h / 110))
        # moss: one or two clumps, each stone its own place (in a crack one time in three)
        spots = []
        if rng.random() < 0.34 and starts:
            spots.append((starts[0][0] + 2, starts[0][1]))
        zone_m = body & ~capm & (yy > yt + (yb - yt) * rng.uniform(0.3, 0.7)) & (yy < yb - _P(2))
        zone_m &= (u > 0.1) if rng.random() < 0.6 else (u < -0.3)
        ys_m, xs_m = np.nonzero(zone_m)
        if len(ys_m):
            k = int(rng.integers(0, len(ys_m)))
            spots.append((int(ys_m[k]), int(xs_m[k])))
        _moss3(code, body, spots[:2], rng)
    else:
        _lichen(code, body, body & (west | capm) & ~foot & (yy < yb - _P(3)), rng, 3 + int(w * h / 90))
        _moss(code, body, body & ((east & (yy > yb - _P(5))) | (foot & (u > -0.2))), rng)
    # carving
    if carved:
        ccx = base_cx - half0 * 0.08 + lean * _P(w) * 0.5
        ccy = yt + (yb - yt) * 0.4
        if carved == 'spiral':
            pts = []
            for k in range(160):
                th = k * 0.1
                r = 0.8 + th * (1.1 if v3 else 0.95)
                if r > half0 * (0.68 if v3 else 0.62):
                    break
                pts.append((ccy + r * math.sin(th) * 0.95, ccx + r * math.cos(th)))
            if v3:
                _groove3(code, body, pts, rng, breaks=2)
            else:
                _groove(code, body, pts, lad, rng, breaks=2)
        elif v3:
            # W2-S3: 3 to 5 runes in a column, 7 texels tall, each its own glyph
            order = rng.permutation(len(RUNES))
            ng = int(np.clip((yb - yt - _P(6)) // 10, 3, 5))
            gy = yt + _P(3.5)
            for i in range(ng):
                gx = ccx - 2 + (1 if i % 2 else -1) * rng.uniform(0, 1.2)
                _rune(code, body, int(round(gx)), int(round(gy)), RUNES[int(order[i % len(order)])], rng)
                gy += 10
        else:
            for k_ in range(3):
                X0 = ccx - _P(3.2) + k_ * _P(3.2)
                stem = [(ccy - _P(2.6) + j, X0 + (j % 5 == 4) * 0) for j in range(_P(5))]
                _groove(code, body, stem, lad, rng, breaks=0)
                # a branch off the stem, a different one on each rune
                bj = int(rng.integers(1, _P(3)))
                dirx = (-1, 1, 1)[k_]
                br = [(ccy - _P(2.6) + bj + i * 0.8, X0 + dirx * (i + 1) * 0.9) for i in range(int(rng.integers(3, 5)))]
                _groove(code, body, br, lad, rng, breaks=0)
    # chips on the arrises (the upper-left rim and the crown's edge)
    edge = body & ~ndi.binary_erosion(body)
    pts = [(int(y), int(x)) for y, x in zip(*np.nonzero(edge & (yy < yb - _P(3))))]
    _chips(code, body, lad, rng, pts, int(rng.integers(2, 4)))
    _clean(code, body, 2)
    _outline(code, body, u, v3=v3)
    if squat:
        # W3-S1: a chip on each shoulder, a notch out of the silhouette with a shade texel under it
        r3 = np.random.default_rng(seed + 717)
        for sd in (-1, 1):
            cols_ = np.nonzero(body.any(0))[0]
            xs_ = [x for x in cols_ if (x - base_cx) * sd > half0 * 0.45 and (x - base_cx) * sd < half0 * 0.85]
            if not xs_:
                continue
            x = int(xs_[int(r3.integers(0, len(xs_)))])
            for dx in range(int(r3.integers(2, 4))):
                X = x + dx * sd
                col = np.nonzero(body[:, X])[0] if 0 <= X < Wt else []
                if not len(col):
                    continue
                y = int(col.min())
                body[y, X] = False
                code[y, X] = -1
                if dx == 0 and body[y + 1, X]:
                    body[y + 1, X] = False
                    code[y + 1, X] = -1
                    y += 1
                code[y + 1, X] = C('stone_cool', 1)
                if body[y + 2, X]:
                    code[y + 2, X] = C('stone', 2)
    # the contact line: one texel under the foot
    fy = int(yb)
    row = body[fy - 1]
    code[fy - 1, row] = C('stone_cool', 0)
    code[~body] = -1
    return code, (base_cx, yb)


def lintel(w: float, h: float, seed: int):
    """A fallen dressed capstone lying in the grass (W2-S4): a long slab whose top line sags a texel
    over its length, its corners rounded and its arrises chipped (2 to 4 notches an arris, each with a
    shade texel under it, the lit arris line broken where they fall); the top one calm lit plane with
    broad sibling patches and lichen crusts, two mortise sockets cut in it; a front face in shade with
    a weathered tooling band; a dark east end; its lit top edge shows (no outline on it); moss in one
    or two clumps with a drip into a joint, never in a row."""
    rng = np.random.default_rng(seed)
    lad = Ladder(STONES, {'stone': 2.0})
    pad = _P(2)
    Wt, Ht = _P(w) + 2 * pad, _P(h) + pad + 2
    code = np.full((Ht, Wt), -1, np.int64)
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    x0, x1 = pad, Wt - pad
    yb = Ht - pad
    yt = 1
    sink = rng.uniform(1.0, 2.5) * (1 if seed % 2 else -1)
    tilt = sink * (xx - x0) / max(1, x1 - x0)                          # one end sunk a little
    u = (xx - (x0 + x1) / 2) / ((x1 - x0) / 2)
    sag = np.round(1.0 - u * u).astype(int)                            # the top line sags a texel
    top_d = int(round((yb - yt) * 0.55))
    end_w = max(4, int(_P(w) * 0.07))
    ytop = yt + np.clip(tilt, 0, None) + sag
    body = (xx >= x0) & (xx < x1) & (yy >= ytop) & (yy < yb)
    # rounded, worn corners (radius 2 to 3)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        r_ = rng.uniform(3.0, 4.2) if sy < 0 else 2.2
        cx_ = (x0 + r_ - 0.5) if sx < 0 else (x1 - r_ - 0.5)
        cy_ = (yt + r_ - 0.5) if sy < 0 else (yb - r_ - 0.5)
        out = ((xx - cx_) * sx > 0) & ((yy - cy_) * sy > 0) & ((xx - cx_) ** 2 + (yy - cy_) ** 2 > r_ * r_)
        body &= ~out
    # W3-S2: rounded ends (each row set in by up to 2 to 3 texels toward the top and the foot, the
    # two ends unlike) and a bottom with a lip a texel up or down here and there, not a ruled line
    r4 = np.random.default_rng(seed + 401)
    tv = np.clip((yy - yt) / max(1, yb - 1 - yt), 0, 1)
    for sx, amp in ((-1, r4.uniform(2.0, 3.0)), (1, r4.uniform(2.4, 3.4))):
        inset = np.round(amp * np.abs(2 * tv - 1.1) ** 2.2)
        if sx < 0:
            body &= xx >= x0 + inset
        else:
            body &= xx < x1 - inset
    x = x0
    while x < x1:
        n_ = int(r4.integers(5, 13))
        dy = int(r4.choice((-1, 0, 0, 1)))
        if dy < 0:
            body[int(yb) - 1, x:x + n_] = False
        elif dy > 0:
            seg = body[int(yb) - 1, x:x + n_].copy()
            body[int(yb), x:x + n_] = seg
        x += n_
    top = body & (yy < yt + top_d + tilt * 0.4 + sag)
    endf = body & ~top & (xx >= x1 - end_w)
    front = body & ~top & ~endf
    val = np.zeros((Ht, Wt))
    val[top] = 158 - 8 * u[top]
    val[front] = 96 - 10 * u[front]
    val[endf] = 66
    _planes(code, body, val, lad, rng, cell=3.6)
    ys, xs = np.nonzero(top)
    for k in rng.permutation(len(ys))[:2]:
        y, x = int(ys[k]), int(xs[k])
        m = top & (((xx - x) / rng.uniform(4, 8)) ** 2 + ((yy - y) / rng.uniform(1.5, 3)) ** 2 <= 1)
        code[m] = WARM.pick(158 + rng.uniform(-6, 4), rng, 5)
    # the arris between the top and the front: lit, broken by chips
    P = np.pad(top, 1)
    arris = top & ~P[2:, 1:-1]
    code[arris] = C('stone_warm', 5)
    ap = sorted((int(x), int(y)) for y, x in zip(*np.nonzero(arris)))
    nch = int(rng.integers(2, 5))
    xs_ch = sorted(rng.choice(np.arange(len(ap)), size=min(nch, len(ap)), replace=False))
    chips = []
    for k in xs_ch:
        x, y = ap[k]
        for dx in range(int(rng.integers(2, 4))):
            if x + dx < Wt and body[y, x + dx]:
                code[y, x + dx] = C('stone_cool', 1) if dx == 0 else C('stone', 2)
                chips.append((y, x + dx, int(code[y, x + dx])))
                if y + 1 < Ht and body[y + 1, x + dx]:
                    code[y + 1, x + dx] = C('stone_cool', 1)
                    chips.append((y + 1, x + dx, C('stone_cool', 1)))
    # chips knocked off the top edge too (notches in the silhouette, a shade texel under each)
    edge_top = body & ~np.pad(body, 1)[:-2, 1:-1]
    et = sorted((int(x), int(y)) for y, x in zip(*np.nonzero(edge_top)) if x0 + 3 < x < x1 - 4)
    for k in rng.choice(np.arange(len(et)), size=min(int(rng.integers(2, 4)), len(et)), replace=False):
        x, y = et[k]
        for dx in range(int(rng.integers(1, 3))):
            if body[y, x + dx]:
                body[y, x + dx] = False
                code[y, x + dx] = -1
                if body[y + 1, x + dx]:
                    code[y + 1, x + dx] = C('stone', 3)
                    if body[y + 2, x + dx]:
                        code[y + 2, x + dx] = C('stone_cool', 2)
    # a tooling band along the front: short diagonal strokes a sibling down, unevenly worn
    fy = int(np.nonzero(front.any(1))[0].min() + 2) if front.any() else yb - 3
    fy = int(np.nonzero(front.any(1))[0].min() + 1) if front.any() else yb - 3
    for x in range(x0 + 2, x1 - end_w - 2, 3):
        if rng.random() < 0.65:
            c_ = COOL.pick(88 + rng.uniform(-6, 6), rng, 6)
            for j in range(2):
                y_, x_ = fy + j, x + j
                if 0 <= y_ < Ht and x_ < Wt and front[y_, x_]:
                    code[y_, x_] = c_
    if w >= 20:
        mw, mh = _P(8 / 3), _P(4 / 3)
        for fx in (0.28, 0.66):
            sx = int(x0 + (x1 - x0) * fx)
            sy = int(yt + top_d * 0.35 + tilt[0, min(Wt - 1, sx)] * 0.4 + 1)
            # W3-S2: a 4 x 3 socket seen from above and the south: its far (north) wall lit one row
            # (stone 4), its floor stone 2, its near wall dark (stone 0 to 1); a rectangle, not a glyph
            mw, mh = 4, 3
            for j in range(mh):
                for i in range(mw):
                    y_, x_ = sy + j, sx + i
                    if top[y_, x_]:
                        code[y_, x_] = (C('stone', 4), C('stone', 2), C('stone_cool', 1))[j]
                        chips.append((y_, x_, int(code[y_, x_])))
            if top[sy + mh, sx:sx + mw].all():
                code[sy + mh, sx:sx + mw] = C('stone_cool', 0)
                chips += [(sy + mh, sx + i, C('stone_cool', 0)) for i in range(mw)]
            code[sy:sy + mh, sx] = np.where(top[sy:sy + mh, sx], C('stone_cool', 0), code[sy:sy + mh, sx])
            chips += [(sy + j, sx, C('stone_cool', 0)) for j in range(mh) if top[sy + j, sx]]
    mort = np.zeros(code.shape, bool)
    for (y, x, c_) in chips:
        mort[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = True
    _flakes(code, top & ~arris & ~mort, lad, rng, int(top.sum() / 16))
    _flakes(code, front, COOL, rng, int(front.sum() / 14))
    _lichen3(code, body, top & ~arris, rng, 3 + int(w / 4), fams=('sand_warm', 'sand', 'sand_cool'))   # no ochre (W3-S3)
    # moss: one or two clumps at the foot on the shaded side, a drip into a joint
    zone_m = front & (yy > yb - _P(2.2)) & (u > -0.3)
    ys_m, xs_m = np.nonzero(zone_m)
    spots = []
    for k in rng.permutation(len(ys_m))[: int(rng.integers(1, 3))]:
        spots.append((int(ys_m[k]) - 1, int(xs_m[k])))
    _moss3(code, body, spots, rng)
    _damp(code, body, int(yb), rng, 1)
    _clean(code, body, 2)
    for (y, x, c_) in chips:                                         # the chips and sockets stay cut
        if body[y, x]:
            code[y, x] = c_
    if w < 20:
        # the stone top (pass 7, W4-S1; its own stream, so the lintel keeps its bytes): calm lit
        # patches of 4 to 8 texels on the top in place of the tan bars, a crack with a step on the
        # front, and 1 to 2 chips knocked out of the base, a shade texel over each
        r7 = np.random.default_rng(seed + 707)
        topz = top & ~arris & ndi.binary_erosion(body)
        ty_, tx_ = np.nonzero(topz)
        if len(ty_):
            seeds_ = np.zeros(code.shape, int)
            for i_, j_ in enumerate(r7.permutation(len(ty_))[: max(3, len(ty_) // 5)]):
                seeds_[ty_[j_], tx_[j_]] = i_ + 1
            idx_ = ndi.distance_transform_edt(seeds_ == 0, return_distances=False, return_indices=True)
            lab_ = seeds_[idx_[0], idx_[1]]
            tones_ = [C('stone', 4), C('stone_warm', 4), C('ashlar_warm', 4), C('ashlar', 4), C('stone_warm', 3)]
            got = {}
            for i_ in np.unique(lab_[topz]):
                sel_ = topz & (lab_ == i_)
                ring_ = ndi.binary_dilation(sel_) & ~sel_ & topz
                ban_ = {got.get(int(q)) for q in np.unique(lab_[ring_])}
                ch_ = [q for q in range(4) if q not in ban_] or [4]
                got[int(i_)] = int(r7.choice(ch_))
                code[sel_] = tones_[got[int(i_)]]
        fz = front & ndi.binary_erosion(body)
        fy_, fx_ = np.nonzero(fz)
        if len(fy_):
            x = int(np.clip(np.median(fx_) + r7.integers(-6, 7), fx_.min() + 2, fx_.max() - 2))
            y = int(fy_.min())
            for j_ in range(int(r7.integers(3, 5))):
                if fz[y, x]:
                    code[y, x] = C('stone_cool', 0)
                    if x + 1 < Wt and fz[y, x + 1]:
                        code[y, x + 1] = C('stone', 3)                # the crack's lit far lip
                y += 1
                if j_ == 1:
                    x += 1 if r7.random() < 0.5 else -1              # a step
        bot = body & ~np.pad(body, 1)[2:, 1:-1]
        bx_ = sorted(int(x) for x in np.nonzero(bot.any(0))[0] if x0 + 4 < x < x1 - 5)
        for x in r7.choice(bx_, size=min(2, len(bx_)), replace=False) if bx_ else []:
            for dx in range(int(r7.integers(2, 4))):
                col = np.nonzero(body[:, x + dx])[0]
                if not len(col):
                    continue
                yb_ = int(col.max())
                body[yb_, x + dx] = False
                code[yb_, x + dx] = -1
                code[yb_ - 1, x + dx] = C('stone_cool', 1)
    edge = body & ~ndi.binary_erosion(body)
    P = np.pad(body, 1)
    lit_ = edge & ~P[:-2, 1:-1] & (u < 0.75)                          # the lit top edge shows
    code[edge & ~lit_] = C('stone_cool', 0)
    code[lit_] = np.where(u[lit_] < 0.2, C('stone_warm', 5), C('stone', 4))
    code[lit_ & (np.arange(Wt)[None, :] % 7 == 3)] = C('stone', 4)
    code[~body] = -1
    return code, ((x0 + x1) / 2.0, yb)

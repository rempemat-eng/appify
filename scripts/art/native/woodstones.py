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


def _outline(code, body, u):
    edge = body & ~ndi.binary_erosion(body)
    P = np.pad(body, 1)
    west_top = edge & (~P[1:-1, :-2] | ~P[:-2, 1:-1]) & P[2:, 1:-1] & (u < 0.15)
    code[edge & ~west_top] = C('stone_cool', 0)
    lit = west_top & (code % 8 >= 3)
    code[lit] = C('stone_warm', 5)


def standing_stone(w: float, h: float, seed: int, lean: float = 0.0, broken: bool = False,
                   carved: str | None = None, squat: bool = False):
    """An ancient standing stone, w x h world px. Returns (codes, (ax, ay) the foot's centre)."""
    rng = np.random.default_rng(seed)
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
    body = (np.abs(u) <= 1.0) & (yy < yb)
    sl = (1 if seed % 2 else -1) * rng.uniform(0.15, 0.35)
    crown = yt + _P(h) * 0.07 * (1 + sl * u) + _P(w) * 0.33 * np.clip(np.abs(u) - 0.35, 0, 1) ** 1.4 * 2.0
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
    capd = _P(1.4) if not broken else _P(1.8)
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
    _planes(code, body, val, lad, rng)
    # the fracture plane on a broken stone: lit, in steps
    if broken:
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
    for k in range(2 + int(broken)):
        sx = base_cx + rng.uniform(-0.5, 0.4) * half0
        sy = yt + (yb - yt) * rng.uniform(0.25, 0.6)
        _crack(code, body, sx, sy, int(rng.integers(_P(2), _P(5))), lad, rng)
    # lichen on the lit and upper faces, moss low on the shaded side
    _lichen(code, body, body & (west | capm) & ~foot & (yy < yb - _P(3)), rng, 3 + int(w * h / 90))
    _moss(code, body, body & ((east & (yy > yb - _P(5))) | (foot & (u > -0.2))), rng)
    # carving
    if carved:
        ccx = base_cx - half0 * 0.08 + lean * _P(w) * 0.5
        ccy = yt + (yb - yt) * 0.4
        if carved == 'spiral':
            pts = []
            for k in range(140):
                th = k * 0.11
                r = 0.8 + th * 0.95
                if r > half0 * 0.62:
                    break
                pts.append((ccy + r * math.sin(th) * 0.95, ccx + r * math.cos(th)))
            _groove(code, body, pts, lad, rng, breaks=2)
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
    _outline(code, body, u)
    # the contact line: one texel under the foot
    fy = int(yb)
    row = body[fy - 1]
    code[fy - 1, row] = C('stone_cool', 0)
    code[~body] = -1
    return code, (base_cx, yb)


def lintel(w: float, h: float, seed: int):
    """A fallen dressed capstone lying in the grass: a long slab, its top one calm lit plane with
    broad sibling patches and lichen crusts, two mortise sockets cut in its top (lit on their far
    wall), a front face in shade with a weathered tooling band, a dark east end, chipped front
    arrises, sunk a little at one end with moss along its foot."""
    rng = np.random.default_rng(seed)
    lad = Ladder(STONES, {'stone': 2.0})
    pad = _P(2)
    Wt, Ht = _P(w) + 2 * pad, _P(h) + pad + 1
    code = np.full((Ht, Wt), -1, np.int64)
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    x0, x1 = pad, Wt - pad
    yb = Ht - pad
    yt = 0
    sink = rng.uniform(1.0, 2.5) * (1 if seed % 2 else -1)
    tilt = sink * (xx - x0) / max(1, x1 - x0)                          # one end sunk a little
    top_d = int(round((yb - yt) * 0.55))
    end_w = max(4, int(_P(w) * 0.07))
    body = (xx >= x0) & (xx < x1) & (yy >= yt + 1 + np.clip(tilt, 0, None)) & (yy < yb)
    # rounded worn corners
    corner = ((xx - x0) < 2) & ((yy - yt) < 2) | ((x1 - 1 - xx) < 2) & ((yy - yt) < 2)
    body &= ~corner
    top = body & (yy < yt + top_d + tilt * 0.4)
    endf = body & ~top & (xx >= x1 - end_w)
    front = body & ~top & ~endf
    val = np.zeros((Ht, Wt))
    u = (xx - (x0 + x1) / 2) / ((x1 - x0) / 2)
    val[top] = 158 - 8 * u[top]
    val[front] = 96 - 10 * u[front]
    val[endf] = 66
    _planes(code, body, val, lad, rng)
    # broad sibling patches on the top (3 or 4, calm)
    ys, xs = np.nonzero(top)
    for k in rng.permutation(len(ys))[:4]:
        y, x = int(ys[k]), int(xs[k])
        m = top & (((xx - x) / rng.uniform(4, 8)) ** 2 + ((yy - y) / rng.uniform(1.5, 3)) ** 2 <= 1)
        code[m] = lad.pick(158 + rng.uniform(-6, 4), rng, 5)
    # the arris between the top and the front: lit, chipped
    P = np.pad(top, 1)
    arris = top & ~P[2:, 1:-1]
    code[arris] = C('stone_warm', 5)
    ap = [(int(y), int(x)) for y, x in zip(*np.nonzero(arris))]
    for k in rng.permutation(len(ap))[: int(rng.integers(2, 5))]:
        y, x = ap[k]
        for dx in range(int(rng.integers(2, 4))):
            if body[y, x + dx] if x + dx < Wt else False:
                code[y, x + dx] = lad.pick(106, rng, 5)
                if y + 1 < Ht and body[y + 1, x + dx]:
                    code[y + 1, x + dx] = C('stone_cool', 1)
    # a tooling band along the front: short diagonal strokes a sibling down, in a row
    fy = int(np.nonzero(front.any(1))[0].min() + 2) if front.any() else yb - 3
    for x in range(x0 + 2, x1 - end_w - 2, 3):
        if rng.random() < 0.8:
            for j in range(2):
                y_, x_ = fy + j, x + j
                if 0 <= y_ < Ht and x_ < Wt and front[y_, x_]:
                    code[y_, x_] = lad.pick(92, rng, 5)
    # the mortise sockets: two recesses (4 x 3 world-px scaled) on the top, lit on the far (north)
    # wall... seen from the front, the far wall is the socket's lower half, lit; the near wall dark
    if w >= 20:
        mw, mh = _P(8 / 3), _P(4 / 3)
        for fx in (0.28, 0.66):
            sx = int(x0 + (x1 - x0) * fx)
            sy = int(yt + top_d * 0.35 + tilt[0, min(Wt - 1, sx)] * 0.4)
            for j in range(mh):
                for i in range(mw):
                    y_, x_ = sy + j, sx + i
                    if top[y_, x_]:
                        code[y_, x_] = C('stone_cool', 0) if j == 0 else (C('stone', 3) if j == mh - 1 else C('stone_cool', 1))
            if top[sy - 1, sx:sx + mw].all():
                code[sy - 1, sx:sx + mw] = C('stone_warm', 5)
    _flakes(code, top & ~arris, lad, rng, int(top.sum() / 30))
    _flakes(code, front, lad, rng, int(front.sum() / 30))
    # lichen crusts on the top; moss along the foot on the shaded side
    _lichen(code, body, top & ~arris, rng, 2 + int(w / 9))
    _moss(code, body, body & (yy >= yb - _P(1.3)) & (u > -0.4), rng)
    _clean(code, body, 2)
    edge = body & ~ndi.binary_erosion(body)
    P = np.pad(body, 1)
    lit_ = edge & ~P[:-2, 1:-1] & (u < 0.4)
    code[edge & ~lit_] = C('stone_cool', 0)
    code[lit_] = C('stone_warm', 5)
    code[~body] = -1
    return code, ((x0 + x1) / 2.0, yb)

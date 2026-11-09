"""The woodland's trees and shrubs at density 3 and up (the 9 Nov detail audit, findings W-T1 to
W-T8 and W-B1 to W-B3, docs/reviews/2026-11-09-woodland-assets.md).

One crown painter for every tree and shrub of the woodland's recipes (`crown`), and one trunk
painter with a bark per kind. Both work in palette codes (palette.C), so every colour is a house
colour.

The crown (art-style "Density 3"; the red tree in Eastward 12 at the same character height):

- the light: each clump a dome lit from the upper left, plus the crown as one dome, in five bands;
  where a clump tucks under the one in front of it, the deep band;
- the leaves: clusters 4 to 7 texels wide, a tip pointing down, painted from the bottom up so each
  leaf's tip lies over the leaf below. A leaf takes its band from the light at its centre, so the
  bands meet in leaf-shaped scallops. Each leaf has three parts: an upper-left crescent a sibling
  lighter, a body, a lower-right rim a sibling darker. The siblings are the greens of the tree's
  families nearest the band's value (within about 9 L), so the tones and shapes come from leaves
  and sibling swaps, not from value grain. Between leaves the band below shows as a dark pocket;
- the deep band stays quiet (its siblings close, no lit crescents, no marks);
- marks only along each clump's lit rim, a third of the leaves there, drawn from four shapes
  (domino, L, 2 x 2, three-texel arc) in any orientation; yellow-green glints in pairs on the
  upper-left clumps only;
- the silhouette: the leaves themselves (no smooth bumped outline) and a leaf tip of 2 to 4 texels
  every 6 to 12 texels along the top and the west; closed in the leaf edge tone, broken lighter on
  the lit upper left.

The trunk: a tapering column with a cylinder ramp, roots or a buttressed foot, the bark of its kind
(plates with lit west edges and dark cracks for oak and pine; smooth mottled grey with eye scars for
beech; white with lenticels and a dark fissured base for birch; a bent stem with twigs for a
sapling; a squat burred bole with a split scar and a deep hollow for the veteran; a short bole
splitting into arching limbs for the willow), and the crown's shade across its top.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from .palette import C, FI, LUT

GREENS = ('grass', 'grass_cool', 'grass_warm', 'leaf', 'leaf_cool', 'leaf_warm')


def _lum(code: int) -> float:
    r, g, b = LUT[code]
    return 0.299 * r + 0.587 * g + 0.114 * b


def _leafy(code: int) -> bool:
    """A green that reads as leaf (hue 62 to 170 degrees), not as straw: a yellow-green tone is kept
    for the glints only."""
    import colorsys
    r, g, b = (int(v) / 255.0 for v in LUT[code])
    h, s_, v = colorsys.rgb_to_hsv(r, g, b)
    return (62 <= h * 360 < 170 and s_ >= 0.2) or v < 0.25


def _crisp(code: int) -> float:
    """Colours that keep their edges at the screen's scale (no channel on a 16-step boundary, where
    compression and scaling smear a cluster into speckle) are preferred."""
    d = min(min(int(c) % 16, 15 - int(c) % 16) for c in LUT[code])
    return (0.3, 0.6, 1.0, 1.0)[min(d, 3)]


class Ladder:
    """Every tone 0..5 of some families, sorted by luminance: a fine value ramp whose neighbours are
    siblings (a tone of one family next to a near tone of another)."""

    def __init__(self, fams, weights=None):
        self.fams = [f for f in fams if f in FI]
        w = dict(weights or {})
        if all(f in GREENS for f in self.fams):
            # every leaf green is a sibling: the tree's own families weigh most, the rest add shapes
            for f in self.fams:
                w.setdefault(f, 1.0)
            extra = [f for f in GREENS if f not in self.fams]
            for f in extra:
                w[f] = 0.35
            self.fams = self.fams + extra
        self.items = sorted((_lum(C(f, t)), C(f, t), w.get(f, 1.0) * _crisp(C(f, t))) for f in self.fams for t in range(6)
                            if not (f in GREENS and not _leafy(C(f, t))))
        self.L = np.array([i[0] for i in self.items])
        self.lo, self.hi = float(self.L.min()), float(self.L.max())

    def pick(self, target: float, rng, spread: float = 6.0, avoid=()) -> int:
        d = np.abs(self.L - target)
        ok = (d <= spread) & np.array([i[1] not in avoid for i in self.items])
        if not ok.any():
            ok = d <= d[[k for k in range(len(d)) if self.items[k][1] not in avoid] or [int(np.argmin(d))]].min() + 0.01
        idx = np.nonzero(ok)[0]
        w = np.array([self.items[k][2] / (1.0 + d[k] / 4.0) for k in idx])
        return int(self.items[int(rng.choice(idx, p=w / w.sum()))][1])


# ------------------------------------------------------------------------------------------------
# leaves
# ------------------------------------------------------------------------------------------------
def _leaf_shapes(seed: int = 5, n: int = 40, wr=(4, 8), hr=(4, 7)):
    """Leaf clusters 4 to 7 texels wide, 4 to 6 tall, each with a tip pointing down (a little to
    one side or the other): (mask, crescent, rim) arrays."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        w = int(rng.integers(*wr))
        h = int(rng.integers(*hr))
        tip = int(rng.integers(-1, 2))
        H, W = h + 2, w + 2
        yy, xx = np.mgrid[0:H, 0:W].astype(float)
        cx, cy = (W - 1) / 2.0, (h - 1) / 2.0
        m = ((xx - cx) / (w / 2.0)) ** 2 + ((yy - cy) / (h / 2.0)) ** 2 <= 1.0 + rng.uniform(-0.08, 0.12)
        # the tip: one or two texels below the body, off-centre by `tip`
        ty = int(np.nonzero(m.any(1))[0].max())
        tx = int(round(cx + tip * 0.8))
        m[min(H - 1, ty + 1), tx] = True
        if rng.random() < 0.5:
            m[min(H - 1, ty + 1), tx + (1 if tip >= 0 else -1)] = True
        # a notch now and then on the upper edge (two lobes), never a hole
        if w >= 6 and rng.random() < 0.5:
            top = int(np.nonzero(m.any(1))[0].min())
            m[top, int(cx)] = False
        P = np.pad(m, 1)
        up, left = P[:-2, 1:-1], P[1:-1, :-2]
        upl = P[:-2, :-2]
        down, right = P[2:, 1:-1], P[1:-1, 2:]
        cres = m & (~up | (~left & (yy < cy + 0.5)) | ~upl)
        P2 = np.pad(m, 2)
        cres |= m & ~P2[:-4, 2:-2] & (xx < cx + 1)                   # two texels deep on top
        rim = m & ~cres & (~down | ~right)
        out.append((m, cres, rim))
    return out


SHAPES = _leaf_shapes(wr=(3, 7), hr=(3, 6))
TICKS = [np.array(s, bool) for s in (
    [[1, 1]], [[1], [1]],                                    # domino
    [[1, 0], [1, 1]], [[1, 1], [0, 1]], [[0, 1], [1, 1]], [[1, 1], [1, 0]],      # L
    [[1, 1], [1, 1]],                                        # 2 x 2
    [[1, 1, 1]], [[0, 1, 1], [1, 0, 0]], [[1, 1, 0], [0, 0, 1]], [[1, 0], [1, 0], [0, 1]],  # arc
)]


def _clean(code: np.ndarray, mask: np.ndarray, passes: int = 2) -> None:
    """No lone texels inside: a texel unlike all four neighbours takes its commonest neighbour."""
    for _ in range(passes):
        P = np.pad(np.where(mask, code, -1), 1, constant_values=-1)
        nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
        c = code
        lone = mask & (c != nb[0]) & (c != nb[1]) & (c != nb[2]) & (c != nb[3])
        for y, x in zip(*np.nonzero(lone)):
            vals = [int(q) for q in nb[:, y, x] if q >= 0]
            if vals:
                code[y, x] = max(set(vals), key=vals.count)


def _spurs(mask: np.ndarray) -> np.ndarray:
    for _ in range(2):
        P = np.pad(mask, 1)
        n = P[:-2, 1:-1].astype(int) + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]
        mask = (mask & (n >= 2)) | (~mask & (n >= 3))
    return mask


def dome_light(S: np.ndarray, clumps, under_gap: int = 3) -> np.ndarray:
    """A value 0..1 per texel: each clump a dome lit from the upper left, half the crown as one dome;
    where a clump tucks under the clump in front of (below) it, near 0."""
    Hp, Wp = S.shape
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    owner = np.full((Hp, Wp), -1)
    for k, (cx, cy, rx, ry) in enumerate(clumps):
        ang = np.arctan2(yy - cy, xx - cx)
        wob = 1 + 0.07 * np.sin(3 * ang + k) + 0.05 * np.sin(5 * ang + 2 * k)
        owner[(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= wob * wob) & S] = k
    miss = S & (owner < 0)
    if miss.any() and (owner >= 0).any():
        idx = ndi.distance_transform_edt(owner < 0, return_distances=False, return_indices=True)
        owner[miss] = owner[idx[0][miss], idx[1][miss]]
    L = np.array([-0.55, -0.68, 0.48])
    L = L / np.linalg.norm(L)
    Cc = np.array(clumps, float)
    o = np.clip(owner, 0, None)
    cx, cy, rx, ry = (Cc[o, i] for i in range(4))
    U = np.clip((xx - cx) / rx, -1, 1)
    V = np.clip((yy - cy) / ry, -1, 1)
    lam = U * L[0] + V * L[1] + np.sqrt(np.clip(1 - U * U - V * V, 0, 1)) * L[2]
    ys, xs = np.nonzero(S)
    gx, gy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    grx, gry = (xs.max() - xs.min()) / 2 + 1, (ys.max() - ys.min()) / 2 + 1
    Ug, Vg = np.clip((xx - gx) / grx, -1, 1), np.clip((yy - gy) / gry, -1, 1)
    lamg = Ug * L[0] + Vg * L[1] + np.sqrt(np.clip(1 - Ug * Ug - Vg * Vg, 0, 1)) * L[2]
    s = np.clip(0.5 * lam + 0.5 * lamg, -1, 1)
    v = np.clip((s + 0.1) / 1.0, 0, 1)
    under = np.zeros((Hp, Wp), bool)
    for k in range(len(clumps)):
        mk = owner == k
        down = np.zeros_like(mk)
        for j in range(1, under_gap + 1):
            down[:-j] |= (owner[j:] > k) & S[j:]
        under |= mk & down
    v = np.where(under, np.minimum(v, 0.12), v)
    return v, owner, lam


def leaf_crown(S: np.ndarray, clumps, lad: Ladder, rng, *, lo: float, hi: float, bands: int = 5,
               spacing=(3.6, 2.8), shapes=None, glint_fam: str = 'grass_warm', tips: bool = True,
               marks: float = 0.33, quiet: int = 1, edge_fam: str = 'leaf_cool', shapes_fn=None, split: bool = True, veins: float = 0.6,
               under_gap: int = 3, low_band: float = 0.0, carve=None):
    """Paint a crown mask S as leaves (module doc). lo/hi: the luminance of the deepest and the most
    lit band. under_gap: how far (texels) a mass's dark underside reaches where it overhangs the one
    below; low_band: the share of the crown's height that falls into the dark under-band at its foot;
    carve(mask, code): cuts sky gaps before the outline is drawn. Returns (codes, mask, value)."""
    Hp, Wp = S.shape
    clumps = sorted(clumps, key=lambda c: (c[1] + 0.15 * c[0]))
    v, owner, lam = dome_light(S, clumps, under_gap=under_gap)
    if low_band:
        # the lowest masses in a clearly dark under-band, so the crown has volume
        ysS = np.nonzero(S.any(1))[0]
        bh = max(4.0, low_band * (ysS.max() - ysS.min()))
        f = np.clip((np.arange(Hp)[:, None] - (ysS.max() - bh)) / bh, 0, 1)
        v = v * (1 - 0.75 * f)
    band = np.clip(np.floor(v * bands), 0, bands - 1).astype(int)
    T = lo + (hi - lo) * np.arange(bands) / max(1, bands - 1)          # each band's value
    code = np.full((Hp, Wp), -1, np.int64)
    # the pockets: the band below, as broad sibling patches (never one flat field)
    patch = ndi.zoom(rng.random((Hp // 5 + 2, Wp // 5 + 2)), 5, order=0)[:Hp, :Wp]
    for b in range(bands):
        m = S & (band == b)
        if not m.any():
            continue
        tgt = T[max(0, b - 1)] - (10 if b <= 1 else 4)
        opts = [lad.pick(tgt, rng, 7) for _ in range(3)]
        code[m] = np.array(opts)[np.minimum(2, (patch[m] * 3).astype(int))]
    shapes = shapes or SHAPES
    # the leaves, on a staggered grid, bottom first so each tip lies over the leaf below
    sx, sy = spacing
    cells = []
    for j, y in enumerate(np.arange(-2, Hp + 2, sy)):
        off = (sx / 2.0) * (j % 2)
        for x in np.arange(-2, Wp + 2, sx) + off:
            yc = int(round(y + rng.uniform(-1.0, 1.0)))
            xc = int(round(x + rng.uniform(-1.2, 1.2)))
            if 0 <= yc < Hp and 0 <= xc < Wp and S[yc, xc]:
                cells.append((yc, xc))
    cells.sort(key=lambda c: (-c[0], c[1]))
    leafmask = np.zeros((Hp, Wp), bool)
    for (yc, xc) in cells:
        m, cres, rim = shapes[int(rng.integers(0, len(shapes)))] if shapes_fn is None else shapes_fn(rng)
        if rng.random() < 0.5:
            m, cres, rim = m[:, ::-1], cres[:, ::-1], rim[:, ::-1]
        h, w = m.shape
        y0, x0 = yc - h // 2, xc - w // 2
        b = int(band[yc, xc])
        t = T[b] + rng.uniform(-3, 3)
        deep = b < quiet
        body = lad.pick(t, rng, 8)
        lit = body if deep and rng.random() < 0.7 else lad.pick(t + (5 if deep else 9), rng, 5, avoid=(body,))
        dark = lad.pick(t - (5 if deep else 9), rng, 5, avoid=(body,))
        # the body in two siblings at the same value, split across the leaf's diagonal (shape, not grain)
        body2 = lad.pick(t - 3, rng, 4, avoid=(body, lit, dark)) if split else body
        hh, ww = m.shape
        low = m & ((np.arange(hh)[:, None] / hh + np.arange(ww)[None, :] / ww) > 1.15)
        # a vein: a two-texel sibling swap inside the body now and then (shape without value noise)
        vein = np.zeros_like(m)
        inner_ = m & ~cres & ~rim
        if veins and inner_.sum() >= 4 and rng.random() < veins:
            vy, vx = np.nonzero(inner_)
            k_ = int(rng.integers(0, len(vy)))
            vein[vy[k_], vx[k_]] = True
            for dy, dx in ((1, 0), (0, 1), (1, 1), (0, -1)):
                Y_, X_ = vy[k_] + dy, vx[k_] + dx
                if 0 <= Y_ < hh and 0 <= X_ < ww and inner_[Y_, X_]:
                    vein[Y_, X_] = True
                    break
        vc = lad.pick(t + (4 if rng.random() < 0.5 else -4), rng, 4, avoid=(body, body2))
        for part, c_ in ((m, body), (low, body2), (vein, vc), (cres, lit), (rim, dark)):
            ys, xs = np.nonzero(part)
            Y, X = ys + y0, xs + x0
            ok = (Y >= 0) & (Y < Hp) & (X >= 0) & (X < Wp)
            code[Y[ok], X[ok]] = c_
            leafmask[Y[ok], X[ok]] = True
    mask = S | leafmask
    # the silhouette's leaf tips on the top and the west (2 to 4 texels, every 6 to 12)
    if tips:
        dist, idx = ndi.distance_transform_edt(~mask, return_indices=True)
        din = ndi.distance_transform_edt(mask)
        gy_, gx_ = np.gradient(ndi.gaussian_filter(mask.astype(float), 2.0))
        edge = mask & ~ndi.binary_erosion(mask)
        ys, xs = np.nonzero(edge)
        order = rng.permutation(len(ys))
        taken = []
        for k in order:
            y, x = int(ys[k]), int(xs[k])
            nx_, ny_ = -gx_[y, x], -gy_[y, x]
            nn = math.hypot(nx_, ny_)
            if nn < 1e-6:
                continue
            nx_, ny_ = nx_ / nn, ny_ / nn
            if not (ny_ < -0.35 or nx_ < -0.35):                 # the top and the west only
                continue
            gap = rng.uniform(6, 12)
            if any((y - ty) ** 2 + (x - tx) ** 2 < gap * gap for (ty, tx) in taken):
                continue
            taken.append((y, x))
            L_ = int(rng.integers(2, 5))
            c_ = int(code[y, x]) if code[y, x] >= 0 else lad.pick(T[-2], rng)
            px, py = -ny_, nx_                                    # across the tip
            for s_ in range(1, L_ + 1):
                half = (L_ - s_) / 2.0 * 0.9
                for q in np.arange(-half, half + 0.01, 0.5):
                    X = int(round(x + nx_ * s_ + px * q))
                    Y = int(round(y + ny_ * s_ + py * q))
                    if 0 <= X < Wp and 0 <= Y < Hp:
                        mask[Y, X] = True
                        code[Y, X] = c_
        del dist, idx, din
    mask = _spurs(mask)
    mask = ndi.binary_fill_holes(mask)
    hole = mask & (code < 0)
    if hole.any():
        idx = ndi.distance_transform_edt(code < 0, return_distances=False, return_indices=True)
        code[hole] = code[idx[0][hole], idx[1][hole]]
    code[~mask] = -1
    # marks along each clump's lit rim only: a third of the places there, from four shapes
    rimzone = mask & (lam > 0.72) & (band >= 2)
    ys, xs = np.nonzero(rimzone)
    for k in rng.permutation(len(ys))[: int(len(ys) * marks / 14)]:
        y, x = int(ys[k]), int(xs[k])
        tk = TICKS[int(rng.integers(0, len(TICKS)))]
        if rng.random() < 0.5:
            tk = tk[::-1]
        if rng.random() < 0.5:
            tk = tk[:, ::-1]
        c_ = lad.pick(T[min(bands - 1, band[y, x])] + 18, rng, 6)
        for dy, dx in zip(*np.nonzero(tk)):
            Y, X = y + dy, x + dx
            if 0 <= Y < Hp and 0 <= X < Wp and rimzone[Y, X]:
                code[Y, X] = c_
    # glints: yellow-green pairs on the upper-left clumps' lit caps
    ys_, xs_ = np.nonzero(mask)
    gx0, gy0 = (xs_.min() + xs_.max()) / 2, (ys_.min() + ys_.max()) / 2
    for (cx, cy, rx, ry) in clumps:
        if cx > gx0 or cy > gy0 + 0.1 * (ys_.max() - ys_.min()):
            continue
        for _ in range(int(rng.integers(0, 3))):
            y = int(cy - ry * rng.uniform(0.3, 0.6))
            x = int(cx - rx * rng.uniform(0.15, 0.5))
            if 0 <= y < Hp and 0 <= x + 1 < Wp and mask[y, x] and mask[y, x + 1] and band[y, x] >= bands - 2:
                g = C(glint_fam, 5)
                code[y, x] = g
                code[y, x + 1] = g
    _clean(code, mask)
    if carve is not None:
        carve(mask, code)
        code[~mask] = -1
    # the outline: the leaf edge tone on the silhouette, lighter where the light hits (upper left)
    edge = mask & ~ndi.binary_erosion(mask)
    P = np.pad(mask, 1)
    lit_side = edge & (~P[:-2, 1:-1] | ~P[1:-1, :-2]) & P[2:, 1:-1] & P[1:-1, 2:] & (v > 0.55)
    code[edge & ~lit_side] = C(edge_fam, 0)
    # the edge tone in runs of 2 to 4 texels of its dark siblings, so the outline is leaf edges and
    # not one drawn line
    edge_alt = [C(edge_fam, 0), C('leaf', 0), C('leaf_cool', 0), C('grass_cool', 0)]
    run = (ndi.zoom(rng.integers(0, 4, (Hp // 3 + 2, Wp // 3 + 2)), 3, order=0)[:Hp, :Wp])
    sel = edge & ~lit_side
    code[sel] = np.array(edge_alt)[run[sel]]
    for y, x in zip(*np.nonzero(lit_side)):
        code[y, x] = lad.pick(max(lad.lo, _lum(int(code[y, x])) - 26), rng, 6)
    return code, mask, v


# ------------------------------------------------------------------------------------------------
# the crown's silhouette from the 1x master (as foliage.paint_masses reads it)
# ------------------------------------------------------------------------------------------------
def master_crown(arr: np.ndarray, d: float, size=None, form: str = 'round'):
    """(S, pad, sx, sy, (W1, H1)): the master's greens closed and filled, scaled to density d, with
    `form` 'bush' flattening its foot."""
    H1, W1 = arr.shape[:2]
    if size is not None:                                           # the recipe's scale (x, y)
        size = (W1 * size[0], H1 * size[1])
    a8 = arr.astype(int)
    green = (a8[..., 3] > 0) & (a8[..., 1] > a8[..., 0] + 4)
    fol = ndi.binary_fill_holes(ndi.binary_closing(np.pad(green, 2), iterations=1))[2:-2, 2:-2] & (a8[..., 3] > 0)
    fol |= green
    widths = fol.sum(1)
    peak = int(np.argmax(widths))
    low = np.nonzero((np.arange(H1) > peak) & (widths < 0.2 * widths.max()))[0]
    if len(low):
        fol[low[0]:] = False
    sx = d * (size[0] / W1 if size else 1.0)
    sy = d * (size[1] / H1 if size else 1.0)
    W, H = int(round(W1 * sx)), int(round(H1 * sy))
    pad = int(np.ceil(2 * d)) + 4
    Wp, Hp = W + 2 * pad, H + 2 * pad
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    u = (xx - pad + 0.5) / sx - 0.5
    v = (yy - pad + 0.5) / sy - 0.5
    f = ndi.map_coordinates(ndi.gaussian_filter(fol.astype(float), 0.7), [v, u], order=1, mode='constant', cval=0.0)
    S = f > 0.45
    if form == 'bush':
        ys_ = np.nonzero(S.any(1))[0]
        S[ys_.max() - max(1, int(0.6 * d)) + 1:] = False
    else:
        r_ = max(2, int(round(2.5 * d)))
        Y_, X_ = np.mgrid[-r_:r_ + 1, -r_:r_ + 1]
        S = ndi.binary_closing(np.pad(S, r_ + 1), structure=(X_ * X_ + Y_ * Y_) <= r_ * r_)[r_ + 1:-r_ - 1, r_ + 1:-r_ - 1]
    lab, n = ndi.label(S)
    if n > 1:
        sizes = ndi.sum(S, lab, range(1, n + 1))
        S = np.isin(lab, 1 + np.nonzero(sizes >= 0.04 * sizes.max())[0])
    # the master's trunk foot (its opaque, non-green pixels in the bottom rows)
    al = a8[..., 3] > 0
    yb = int(np.nonzero(al.any(1))[0].max())
    rows = slice(max(0, yb - 5), yb - 1) if yb > 6 else slice(yb, yb + 1)
    base = al[rows] & ~green[rows]
    cols = np.nonzero(base.any(0))[0]
    if not len(cols):
        cols = np.nonzero(al[yb])[0]
    tcx = (cols.min() + cols.max() + 1) / 2.0
    foot = (pad + tcx * sx, pad + (yb + 1) * sy)
    return S, foot, (W1, H1)


def clump_cover(S, r, rng, max_n=40):
    from . import foliage as F5
    Si = ndi.binary_erosion(S, iterations=2)
    if Si.sum() < 10:
        Si = S
    out = [(cx, cy, rr, rr * 0.9) for (cx, cy, rr) in F5._clump_cover(Si, r, rng, max_n=max_n)]
    if not out:
        ys, xs = np.nonzero(S)
        out = [(xs.mean(), ys.mean(), (xs.max() - xs.min()) / 2 + 1, (ys.max() - ys.min()) / 2 + 1)]
    return out


# ------------------------------------------------------------------------------------------------
# trunks
# ------------------------------------------------------------------------------------------------
BARKS = {
    # families (and weights), the body's value, the cracks' code, the light's spread (L)
    'oak': (('timber_cool', 'timber', 'earth_warm', 'earth'), {'timber_cool': 2.0}, 92, ('timber_cool', 0), 34),
    'pine': (('timber_warm', 'timber', 'clay', 'fox'), {'timber_warm': 2.0, 'fox': 0.5}, 96, ('timber_cool', 0), 34),
    'beech': (('stone', 'stone_cool', 'stone_warm', 'ashlar', 'ashlar_warm'), {'stone': 2.0}, 116, ('stone_cool', 0), 50),
    'birch': (('plaster', 'plaster_warm', 'stone_warm'), {'plaster': 2.0, 'stone_warm': 0.4}, 176, ('stone_cool', 1), 62),
    'sapling': (('timber_cool', 'timber', 'earth_warm'), {'timber_cool': 2.0}, 92, ('timber_cool', 0), 30),
    'willow': (('timber_cool', 'earth', 'earth_warm', 'stone_cool'), {'timber_cool': 2.0}, 88, ('timber_cool', 0), 34),
}


def _hollow(code, body, xx, yy, cx, cy, rx, ry, rng):
    """A hollow with depth: a lip two to three texels thick lit on its lower and west edge, the far
    (east) inner wall lit, the near (west) inner wall in shade, falling to near-black at the back;
    two eyes set inside the dark."""
    o = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    jag = (ndi.gaussian_filter(rng.random(body.shape), 1.2) - 0.5) * 0.5
    open_ = body & (o + jag <= 1.0)
    lip = body & ~open_ & (o + jag <= 1.0 + 2.6 / max(rx, ry) * 2.2)
    code[lip] = C('timber_cool', 2)
    lip_lit = lip & (((yy - cy) > ry * 0.25) | ((xx - cx) < -rx * 0.35))
    code[lip_lit] = C('timber', 4)
    code[lip & ((yy - cy) > ry * 0.7)] = C('timber_warm', 4)
    depth = np.clip(1.0 - o, 0, 1)
    inner = open_.copy()
    far = inner & ((xx - cx) > rx * 0.35)                          # the east inner wall faces the light
    near = inner & ((xx - cx) < -rx * 0.25)
    code[inner] = C('timber_cool', 0)
    code[far & (depth < 0.55)] = C('timber_cool', 2)
    code[far & (depth < 0.3)] = C('timber', 3)
    code[near & (depth < 0.45)] = C('timber_cool', 1)
    back = inner & (depth > 0.5)
    code[back] = C('soot', 0) if 'soot' in FI else C('timber_cool', 0)
    # the eyes, inside the dark
    ey, ex = int(cy - ry * 0.05), int(cx + rx * 0.05)
    for dx in (-2, 2):
        if body[ey, ex + dx]:
            code[ey, ex + dx] = C('brass', 5)
            code[ey, ex + dx + (1 if dx > 0 else -1)] = C('brass', 4)


# ------------------------------------------------------------------------------------------------
# kinds
# ------------------------------------------------------------------------------------------------
LOOKS = {
    # crown families and weights, the deepest and the most lit band's value, leaf spacing
    'oak': (('grass', 'grass_warm', 'leaf', 'leaf_warm', 'grass_cool'), {'grass': 2.0, 'leaf_warm': 1.4}, 62, 168),
    'beech': (('grass_cool', 'grass', 'leaf', 'leaf_cool'), {'grass_cool': 2.0, 'grass': 1.3}, 58, 165),
    'birch': (('leaf_warm', 'grass_warm', 'grass', 'leaf'), {'leaf_warm': 2.0, 'grass_warm': 1.4}, 66, 176),
    'pine': (('leaf_cool', 'leaf', 'grass_cool'), {'leaf_cool': 2.0, 'leaf': 1.5}, 44, 132),
    'hollow_tree': (('grass_cool', 'grass', 'leaf', 'leaf_warm', 'grass_warm'), {'grass_cool': 2.0}, 58, 162),
    'willow': (('grass_cool', 'grass', 'grass_warm', 'leaf_warm'), {'grass_cool': 2.0, 'grass': 1.5}, 60, 172),
    'sapling': (('grass', 'grass_warm', 'leaf_warm', 'grass_cool'), {'grass': 2.0}, 66, 172),
    'bush': (('grass_cool', 'grass', 'leaf', 'grass_warm'), {'grass_cool': 2.0}, 60, 160),
    'bush_b': (('grass', 'grass_warm', 'grass_cool', 'leaf_warm'), {'grass': 2.0}, 64, 168),
    'bush_c': (('grass_cool', 'grass', 'leaf', 'leaf_cool'), {'grass_cool': 2.0}, 58, 160),
    'bramble': (('leaf', 'leaf_cool', 'grass_cool', 'leaf_warm'), {'leaf': 2.0}, 48, 140),
    'holly': (('leaf_cool', 'leaf', 'grass_cool'), {'leaf_cool': 2.0}, 40, 122),
}


def _compose(trunk_out, crown_code, crown_mask, foot_in_crown, extra=None):
    """The crown over the trunk, the trunk's foot at the crown's foot point; the crown's shade
    across the top of the trunk (two tones down for 6 to 10 rows under the crown)."""
    tc, tm, (tfx, tfy) = trunk_out
    fx, fy = foot_in_crown
    ox, oy = int(round(fx - tfx)), int(round(fy - tfy))            # trunk origin in crown coords
    x0, y0 = min(0, ox), min(0, oy)
    W = max(crown_code.shape[1], ox + tc.shape[1]) - x0
    H = max(crown_code.shape[0], oy + tc.shape[0]) - y0
    out = np.full((H, W), -1, np.int64)
    tsub = out[oy - y0:oy - y0 + tc.shape[0], ox - x0:ox - x0 + tc.shape[1]]
    tsub[tm] = tc[tm]
    # the crown's shade on the trunk: under each crown column, 6 to 10 rows two tones down
    cm = np.zeros((H, W), bool)
    cm[-y0:-y0 + crown_mask.shape[0], -x0:-x0 + crown_mask.shape[1]] = crown_mask
    trm = out >= 0
    depth = 7 + (np.arange(W) % 3)
    for x in np.nonzero(trm.any(0))[0]:
        col = np.nonzero(cm[:, x])[0]
        if not len(col):
            continue
        yb = col.max()
        ys = np.arange(yb + 1, min(H, yb + 1 + depth[x]))
        ys = ys[trm[ys, x]]
        if len(ys):
            c = out[ys, x]
            t = c % 8
            out[ys, x] = np.where(t < 6, c - np.minimum(t, 2), c)
    if extra is not None:
        extra(out, -x0, -y0)
    csub = out[-y0:-y0 + crown_code.shape[0], -x0:-x0 + crown_code.shape[1]]
    csub[crown_mask] = crown_code[crown_mask]
    foot = (ox - x0 + tfx, oy - y0 + tfy)
    return out, foot


def _crop(code, foot):
    ys, xs = np.nonzero(code >= 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return code[y0:y1, x0:x1], (foot[0] - x0, foot[1] - y0)


def _needle_shapes(seed=77, n=30):
    nr = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        w = int(nr.integers(2, 4))
        h = int(nr.integers(4, 7))
        m = np.zeros((h, w + 2), bool)
        lean = nr.uniform(-1, 1)
        for y in range(h):
            x0 = int(round(1 + lean * y / h))
            m[y, x0:x0 + max(1, w - (1 if y >= h - 2 else 0))] = True
        P = np.pad(m, 1)
        cres = m & (~P[1:-1, :-2] | ~P[:-2, 1:-1])
        rim = m & ~cres & ~P[1:-1, 2:]
        out.append((m, cres, rim))
    return out


NEEDLES = _needle_shapes()


def pine_crown(S, tiers, lad, rng, lo, hi):
    """A pine's tiers, each a skirt widening to its foot, lower tiers in front: needles as narrow
    leaves lit on the west; each tier's foot broken into downward needle tips (2 to 4 texels every 4
    to 6); a dark underside (2 to 3 rows) where a tier overhangs the one below, and the shade it
    casts on that tier's top; the west tip of each tier lit."""
    Hp, Wp = S.shape
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    code = np.full((Hp, Wp), -1, np.int64)
    mask = np.zeros((Hp, Wp), bool)
    v_all = np.zeros((Hp, Wp))
    tiers = sorted(tiers, key=lambda c: c[1])
    prev = None
    for k, (cx, cy, rx, ry) in enumerate(tiers):
        ytop = cy - ry * 1.25
        ybot = cy + ry * 0.75
        f = np.clip((yy - ytop) / max(1, ybot - ytop), 0, 1)
        half = rx * (0.22 + 0.78 * f ** 0.85) + 1.2 * np.sin(yy * 0.9 + k)
        tm = (np.abs(xx - cx) <= half) & (yy >= ytop) & (yy <= ybot)
        if not tm.any():
            continue
        # the tier's foot: needle tips hanging every 4 to 6 texels
        x = cx - rx + rng.uniform(0, 3)
        while x < cx + rx - 1:
            L_ = int(rng.integers(2, 5))
            for j in range(1, L_ + 1):
                for dx in ((0, 1) if j < L_ else (0,)):
                    Y, X = int(ybot) + j, int(x) + dx
                    if 0 <= Y < Hp and 0 <= X < Wp:
                        tm[Y, X] = True
            x += rng.uniform(4, 6.5)
        cl = [(cx - rx * 0.3, cy - ry * 0.2, rx * 1.1, ry * 1.4)]
        tc, tmask, tv = leaf_crown(tm, cl, lad, rng, lo=lo, hi=hi, bands=4, spacing=(3.0, 3.2),
                                   shapes_fn=lambda r: NEEDLES[int(r.integers(0, len(NEEDLES)))], tips=False,
                                   marks=0.2, edge_fam='leaf_cool', glint_fam='leaf_warm', quiet=2)
        # the underside: the tier's lowest 2 to 3 rows (and its tips) in the deep shade
        rows = np.arange(Hp)[:, None]
        under = tmask & (rows >= ybot - 2)
        for y, x_ in zip(*np.nonzero(under)):
            tc[y, x_] = lad.pick(lo - 2, rng, 6)
        # the west tip lit
        wt = tmask & (xx < cx - rx * 0.7) & (rows < ybot - 2) & (rows > ybot - 5) & ~under
        wt &= np.roll(tmask, 1, 1) & np.roll(tmask, -1, 0)
        tip_c = (lad.pick(hi - 14, rng, 6), lad.pick(hi - 24, rng, 6))
        for y, x_ in zip(*np.nonzero(wt)):
            tc[y, x_] = tip_c[(x_ // 2 + y) % 2]
        code[tmask] = tc[tmask]
        mask |= tmask
        v_all[tmask] = tv[tmask]
        # the shade this tier throws on the one behind it is drawn when the next tier comes: here, the
        # top rows of this tier under the previous tier's foot
        if prev is not None:
            pm = prev
            below = np.zeros_like(pm)
            for j in range(1, 4):
                below[j:] |= pm[:-j]
            sh = tmask & below & ~pm
            for y, x_ in zip(*np.nonzero(sh)):
                code[y, x_] = lad.pick(lo + 6, rng, 6)
        prev = tmask.copy()
    mask = _spurs(mask)
    code[~mask] = -1
    _clean(code, mask)
    return code, mask, v_all


def _twig_hangs(code, mask, lad, rng, lo, hi):
    """The birch's lower edge thinned into hanging twig clusters: short drops of small leaves (2 to 3
    texels wide, lit on the west) on fine twigs, so the crown reads lighter than the oak's."""
    Hp, Wp = mask.shape
    cols = np.nonzero(mask.any(0))[0]
    x = cols.min() + rng.uniform(3, 6)
    while x < cols.max() - 3:
        X = int(x)
        col = np.nonzero(mask[:, X])[0]
        if len(col):
            yb = col.max()
            L_ = int(rng.integers(4, 8))
            for j in range(0, L_):
                Y = yb + j
                if Y >= Hp:
                    break
                w = 3 if j < L_ - 2 else 2
                xo = X + int(round(math.sin(j / 2.0 + x) * 0.8))
                for k in range(w):
                    if 0 <= xo + k < Wp:
                        t = 0.42 if k == 0 else (0.2 if k == w - 1 else 0.3)
                        code[Y, xo + k] = lad.pick(lo + (hi - lo) * (t + 0.15 * (j % 2)), rng, 7)
                        mask[Y, xo + k] = True
        x += rng.uniform(6, 10)


def sapling_stem(length, rng):
    """A young stem: 5 texels at its foot tapering to 3, with a slight bend, two small side twigs
    under the crown, a root flare of 2 to 4 texels and a contact line."""
    fams, wts, base, crack, spread = BARKS['sapling']
    lad = Ladder(fams, wts)
    Wt, Ht = 22, length + 2
    code = np.full((Ht, Wt), -1, np.int64)
    body = np.zeros((Ht, Wt), bool)
    cxs = []
    for y in range(length):
        t = y / max(1, length - 1)
        cx = Wt / 2.0 + 1.6 * math.sin(t * 2.4 + 0.3)
        w = 3 + 2 * t
        if y >= length - 3:
            w += (y - (length - 4)) * 1.2
        x0 = int(round(cx - w / 2))
        x1 = int(round(cx + w / 2))
        body[y, x0:x1] = True
        cxs.append((x0, x1))
        for x in range(x0, x1):
            u = (x - x0) / max(1, x1 - x0 - 1)
            vv = base + spread * (0.6 - 1.0 * u)
            code[y, x] = lad.pick(vv, rng, 6)
    # twigs
    for k, (yy, sd) in enumerate(((int(length * 0.18), -1), (int(length * 0.32), 1))):
        x0, x1 = cxs[yy]
        x = x0 if sd < 0 else x1 - 1
        for j in range(1, 6):
            X, Y = x + sd * j, yy - j // 2
            if 0 <= X < Wt and Y >= 0:
                code[Y, X] = lad.pick(base + 12, rng, 6)
                body[Y, X] = True
        # a leaf pair at the twig's end
        X, Y = x + sd * 6, yy - 3
        for dy, dx in ((0, 0), (0, sd), (-1, 0), (1, sd)):
            if 0 <= X + dx < Wt and Y + dy >= 0:
                code[Y + dy, X + dx] = C('grass', 3 if dy <= 0 else 2)
                body[Y + dy, X + dx] = True
    edge = body & ~ndi.binary_erosion(body)
    P = np.pad(body, 1)
    east = edge & ~P[1:-1, 2:]
    code[east] = C(*crack)
    code[length - 1, :][body[length - 1, :]] = C(*crack)            # the contact line
    return code, body, (int(round(sum(cxs[-1]) / 2)), length)


# ------------------------------------------------------------------------------------------------
# the willow (W-T7)
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# shrubs (W-B1 to W-B3)
# ------------------------------------------------------------------------------------------------
def shrub(kind: str, master_arr: np.ndarray, d: float, seed: int, look: dict, scale=None):
    """bush, bush_b, bush_c, bramble, bramble_b, holly, holly_b. Returns (codes, foot)."""
    rng = np.random.default_rng(seed * 7 + 53)
    base_kind = kind.split('_')[0] if kind.startswith(('bramble', 'holly')) else kind
    fams, wts, lo, hi = LOOKS[base_kind]
    lad = Ladder(fams, wts)
    S, _foot, _ = master_crown(master_arr, d, size=scale, form='bush')
    if kind == 'holly_b':
        # a conical habit: narrower toward a pointed top
        ys, xs = np.nonzero(S)
        y0, y1 = ys.min(), ys.max()
        cxm = (xs.min() + xs.max()) / 2
        yy, xx = np.mgrid[0:S.shape[0], 0:S.shape[1]]
        f = np.clip((yy - y0) / max(1, y1 - y0), 0, 1)
        S &= np.abs(xx - cxm) <= (xs.max() - xs.min()) / 2 * (0.18 + 0.86 * f ** 0.75)
    clumps = clump_cover(S, look.get('clump', 6.0) * d * 0.7, rng)
    if base_kind == 'holly':
        code, mask, v = holly(S, clumps, lad, rng, lo, hi, kind)
    else:
        code, mask, v = leaf_crown(S, clumps, lad, rng, lo=lo, hi=hi, edge_fam='leaf' if base_kind == 'bramble' else 'leaf_cool')
    # the foot: the lowest leaves in the deep band where it meets the ground, flat (no legs)
    ysS = np.nonzero(S.any(1))[0]
    yb = int(ysS.max())
    mask[yb + 1:] = False                                          # nothing hangs below the foot
    rows = np.arange(mask.shape[0])[:, None]
    foot_rows = mask & (rows >= yb - 2) & (rows < yb)
    for y, x in zip(*np.nonzero(foot_rows)):
        code[y, x] = lad.pick(lo + 6, rng, 6)
    code[mask & (rows == yb)] = C('leaf_cool', 0)
    if base_kind == 'bramble':
        code, mask = bramble_canes(code, mask, rng, kind)
    ys, xs = np.nonzero(mask)
    return _crop(np.where(mask, code, -1), ((xs.min() + xs.max() + 1) / 2.0, ys.max() + 1))


def holly(S, clumps, lad, rng, lo, hi, kind):
    """Holly: glossy dark leaves (leaf cool 1 to 3) with spined points of two texels that break the
    silhouette every 3 to 5 texels, a hard one-texel glint on each leaf's upper-left lobe; berries in
    clusters of 3 to 5 at the leaf axils, each with a glint."""
    shapes = []
    nr = np.random.default_rng(91)
    for _ in range(30):
        w = int(nr.integers(5, 8))
        h = int(nr.integers(4, 6))
        m = np.zeros((h + 2, w + 2), bool)
        yy, xx = np.mgrid[0:h + 2, 0:w + 2]
        cx, cy = (w + 1) / 2.0, (h + 1) / 2.0
        m |= ((xx - cx) / (w / 2.0)) ** 2 + ((yy - cy) / (h / 2.0 - 0.3)) ** 2 <= 1.0
        # spines: notch the rim every 2 texels so points stand out
        edge = m & ~ndi.binary_erosion(m)
        ey, ex = np.nonzero(edge)
        for k in range(len(ey)):
            if (ex[k] + ey[k]) % 3 == 0:
                m[ey[k], ex[k]] = False
        P = np.pad(m, 1)
        cres = m & (~P[:-2, 1:-1] | ~P[1:-1, :-2])
        rim = m & ~cres & (~P[2:, 1:-1] | ~P[1:-1, 2:])
        shapes.append((m, cres, rim))
    code, mask, v = leaf_crown(S, clumps, lad, rng, lo=lo, hi=hi, shapes=shapes, spacing=(4.6, 3.6), tips=False,
                               marks=0.0, glint_fam='leaf_cool', edge_fam='leaf_cool')
    Hp, Wp = mask.shape
    # spined points round the silhouette every 3 to 5 texels, two texels out
    gy_, gx_ = np.gradient(ndi.gaussian_filter(mask.astype(float), 1.5))
    edge = mask & ~ndi.binary_erosion(mask)
    ys, xs = np.nonzero(edge)
    taken = []
    for k in rng.permutation(len(ys)):
        y, x = int(ys[k]), int(xs[k])
        if y >= np.nonzero(mask.any(1))[0].max() - 3:
            continue
        gap = rng.uniform(3, 5)
        if any((y - ty) ** 2 + (x - tx) ** 2 < gap * gap for (ty, tx) in taken):
            continue
        taken.append((y, x))
        nx_, ny_ = -gx_[y, x], -gy_[y, x]
        nn = math.hypot(nx_, ny_) or 1
        for s in (1, 2):
            X, Y = int(round(x + nx_ / nn * s)), int(round(y + ny_ / nn * s))
            if 0 <= X < Wp and 0 <= Y < Hp:
                mask[Y, X] = True
                code[Y, X] = C('leaf_cool', 1) if s == 2 else code[y, x]
    # glints: a hard tone-5 texel on the upper-left lobe of the lit leaves
    lit = mask & (v > 0.55)
    ys, xs = np.nonzero(lit)
    for k in rng.permutation(len(ys))[: int(lit.sum() / 30)]:
        y, x = int(ys[k]), int(xs[k])
        code[y, x] = C('leaf_cool', 5) if rng.random() < 0.6 else C('grass_cool', 5)
        if x + 1 < Wp and mask[y, x + 1]:
            code[y, x + 1] = C('leaf_cool', 4)
    # berries: clusters of 3 to 5, each 2 x 2 with a glint, at axils (between leaves, mid-crown)
    ys, xs = np.nonzero(ndi.binary_erosion(mask, iterations=4))
    nb = 5 if kind == 'holly' else 6
    placed = []
    for k in rng.permutation(len(ys)):
        if len(placed) >= nb:
            break
        y, x = int(ys[k]), int(xs[k])
        if any(abs(y - py) < 8 and abs(x - px) < 9 for (py, px) in placed):
            continue
        placed.append((y, x))
        n = int(rng.integers(3, 6))
        offs = [(0, 0), (0, 2), (2, 1), (-2, 1), (2, -1), (1, 3)][:n]
        for (dy, dx) in offs:
            Y, X = y + dy, x + dx
            if 0 <= Y < Hp - 1 and 0 <= X < Wp - 1:
                code[Y:Y + 2, X:X + 2] = C('berry', 3)
                code[Y + 1, X + 1] = C('berry', 1)
                code[Y, X] = C('berry_warm', 5) if 'berry_warm' in FI else C('berry', 5)
                mask[Y:Y + 2, X:X + 2] = True
    return code, mask, v


def bramble_canes(code, mask, rng, kind):
    """Arching canes (3 to 5, two texels thick, a lit top edge) looping out of the mass and back to
    the ground past its silhouette, with thorns; berries in clusters of 3 to 6 drupelets (2 x 2) of
    mixed ripeness, each with a glint at its top left; serrated leaf tips on the silhouette."""
    Hp, Wp = mask.shape
    padx, pady = 14, 6
    big = np.full((Hp + pady, Wp + 2 * padx), -1, np.int64)
    bm = np.zeros(big.shape, bool)
    big[pady:, padx:padx + Wp] = code
    bm[pady:, padx:padx + Wp] = mask
    H2, W2 = big.shape
    ys, xs = np.nonzero(bm)
    yb, yt = ys.max(), ys.min()
    x0, x1 = xs.min(), xs.max()
    n = int(rng.integers(3, 6))
    inside0 = bm.copy()
    for k in range(n):
        side = -1 if k % 2 == 0 else 1
        # a cane leaves the mass near its top, arches up and out past the silhouette and comes back
        # down to the ground just outside it
        sx = x0 + (x1 - x0) * (0.5 + side * rng.uniform(0.22, 0.4))
        col = np.nonzero(inside0[:, int(sx)])[0]
        sy = (col.min() + 3) if len(col) else yt + 3
        ex = (x0 - rng.uniform(2, 7)) if side < 0 else (x1 + rng.uniform(2, 7))
        ey = yb
        peak = sy - rng.uniform(2, 5)
        cxp = sx + (ex - sx) * rng.uniform(0.6, 0.9)
        pts = []
        for s_ in np.linspace(0, 1, 90):
            px = (1 - s_) ** 2 * sx + 2 * (1 - s_) * s_ * cxp + s_ * s_ * ex
            py = (1 - s_) ** 2 * sy + 2 * (1 - s_) * s_ * peak + s_ * s_ * ey
            pts.append((px, py))
        last = None
        for i, (px, py) in enumerate(pts):
            X, Y = int(round(px)), int(round(py))
            if (X, Y) == last or not (0 <= X < W2 and 2 <= Y < H2):
                continue
            last = (X, Y)
            if inside0[Y, X] and inside0[Y - 1, X] and inside0[min(H2 - 1, Y + 1), X]:
                continue                                            # behind the leaves
            if Y >= yb - 4:
                # the tip roots where it meets the ground, in a tuft of new leaves
                big[Y - 1, X] = C('leaf', 3)
                big[Y, X] = C('leaf', 2)
                bm[Y - 1, X] = True
                bm[Y, X] = True
                continue
            big[Y - 1, X] = C('berry', 3)                           # the lit top edge
            big[Y, X] = C('berry_cool', 1) if 'berry_cool' in FI else C('berry', 1)
            bm[Y - 1, X] = True
            bm[Y, X] = True
            if i % 9 == 4 and not inside0[Y - 2, X]:
                big[Y - 2, X] = C('berry', 2)                       # a thorn
                bm[Y - 2, X] = True
    # berry clusters: 3 to 6 drupelets of mixed ripeness on the mass and the canes
    ys, xs = np.nonzero(ndi.binary_erosion(bm, iterations=3))
    placed = []
    want = 3 if kind == 'bramble' else 2
    for k in rng.permutation(len(ys)):
        if len(placed) >= want:
            break
        y, x = int(ys[k]), int(xs[k])
        if any(abs(y - py) < 9 and abs(x - px) < 14 for (py, px) in placed):
            continue
        placed.append((y, x))
        nb = int(rng.integers(3, 7))
        offs = [(0, 0), (0, 2), (2, 1), (-2, 1), (2, -1), (-1, 3), (1, -2)][:nb]
        for j, (dy, dx) in enumerate(offs):
            Y, X = y + dy, x + dx
            if not (0 <= Y < H2 - 1 and 0 <= X < W2 - 1):
                continue
            ripe = rng.random()
            if ripe < 0.25:
                body_c, dk = C('grass_warm', 3), C('grass', 1)
            elif ripe < 0.6:
                body_c, dk = C('berry', 3), C('berry', 1)
            else:
                body_c, dk = C('dusk', 1) if 'dusk' in FI else C('berry', 0), C('berry', 0)
            big[Y:Y + 2, X:X + 2] = body_c
            big[Y + 1, X + 1] = dk
            big[Y, X] = C('berry', 5) if ripe >= 0.25 else C('grass_warm', 5)
            bm[Y:Y + 2, X:X + 2] = True
    # serrated leaf tips on the top of the silhouette: a texel notch every 3
    edge = bm & ~ndi.binary_erosion(bm)
    P = np.pad(bm, 1)
    top = edge & ~P[:-2, 1:-1] & P[2:, 1:-1]
    for y, x in zip(*np.nonzero(top)):
        if (x % 3) == 0 and y > 0 and y < yb - 4:
            big[y - 1, x] = C('leaf', 1)
            bm[y - 1, x] = True
    big[~bm] = -1
    return big, bm


# ------------------------------------------------------------------------------------------------
# second pass (coordinator's review of #446, 9 Nov): trunks that taper, lean and fork into limbs,
# crowns built from a few major masses with shade notches and sky gaps, and a wider willow
# ------------------------------------------------------------------------------------------------
LIGHT2 = np.array([-0.72, -0.69])            # the light's direction in the picture (upper left)


def _tube(pts, w0, w1, H, W, off=(0.0, 0.0)):
    """A tapered tube along pts [(x, y)]: (mask, shade) where shade is -1 (the side away from the
    light) .. 1 (the side facing the upper left), as a cylinder lit from the upper left."""
    mask = np.zeros((H, W), bool)
    shade = np.full((H, W), -9.0)
    n = len(pts)
    seg = []
    for i in range(n - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        L = max(abs(xb - xa), abs(yb - ya))
        for s_ in np.linspace(0, 1, int(L * 2) + 2):
            seg.append((xa + (xb - xa) * s_ + off[0], ya + (yb - ya) * s_ + off[1], (i + s_) / max(1, n - 1)))
    for (px, py, f) in seg:
        r = max(0.8, (w0 + (w1 - w0) * f) / 2.0)
        y0, y1 = int(max(0, py - r - 1)), int(min(H, py + r + 2))
        x0, x1 = int(max(0, px - r - 1)), int(min(W, px + r + 2))
        if y0 >= y1 or x0 >= x1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dx, dy = xx - px, yy - py
        dd = np.sqrt(dx * dx + dy * dy)
        m = dd <= r
        sh = (dx * LIGHT2[0] + dy * LIGHT2[1]) / r          # facing the light: positive
        sub_m = mask[y0:y1, x0:x1]
        sub_s = shade[y0:y1, x0:x1]
        upd = m & ~sub_m
        sub_s[upd] = sh[upd]
        sub_m |= m
    return mask, shade


def _bark(code, body, shade, kind, lad, base, spread, crack, rng, aspect=2.0, pw=4.6, ph=8.5):
    """Bark over `body`: the cylinder in three zones (a lit west strip, the mid, a dark east), then
    per kind: plates (irregular, 3 to 6 wide, 5 to 11 tall) with lit west edges and dark cracks, or
    smooth grey with sibling mottle and eye scars (beech), or white with lenticels (birch)."""
    H, W = body.shape
    yy, xx = np.mgrid[0:H, 0:W]
    zone = np.where(shade > 0.38, 1.0, np.where(shade < -0.3, -1.0, 0.0))
    val = base + spread * (0.62 * zone + 0.25 * np.clip(shade, -1, 1))
    if kind in ('oak', 'pine', 'willow', 'sapling', 'hollow'):
        seeds = []
        for j, y in enumerate(np.arange(-ph, H + ph, ph * 0.75)):
            for x in np.arange(-pw, W + pw, pw) + (pw / 2) * (j % 2):
                seeds.append((x + rng.uniform(-1.4, 1.4), y + rng.uniform(-ph * 0.35, ph * 0.35)))
        S_ = np.array(seeds)
        wts = rng.uniform(0.75, 1.3, len(seeds))                  # plates of different sizes
        best = np.full((H, W), 1e9)
        plate = np.full((H, W), -1)
        for k, (sx, sy) in enumerate(S_):
            d2 = (((xx - sx)) ** 2 + ((yy - sy) / aspect) ** 2) / wts[k]
            m = d2 < best
            best[m] = d2[m]
            plate[m] = k
        plate[~body] = -1
        for p in np.unique(plate[body]):
            m = plate == p
            ys, xs = np.nonzero(m)
            vv = float(np.median(val[m])) + rng.uniform(-7, 7)
            code[m] = lad.pick(vv, rng, 6)
            P = np.pad(m, 1)
            west = m & ~P[1:-1, :-2]
            if vv > base - spread * 0.2:
                code[west] = lad.pick(vv + 20, rng, 6)
            low_ = m & ~P[2:, 1:-1] & ~west
            code[low_] = lad.pick(vv - 12, rng, 6)
        Pp = np.pad(plate, 1, constant_values=-1)
        crk = body & (plate != Pp[1:-1, 2:]) & (Pp[1:-1, 2:] >= 0)
        crk |= body & (plate != Pp[2:, 1:-1]) & (Pp[2:, 1:-1] >= 0) & (ndi.gaussian_filter(rng.random((H, W)), 1) > 0.5)
        code[crk] = np.where(shade[crk] > 0.38, C(crack[0], min(5, crack[1] + 1)), C(*crack))
    elif kind == 'beech':
        f = ndi.zoom(rng.random((H // 4 + 2, W // 4 + 2)), 4, order=0)[:H, :W]
        q = np.round((val + (f - 0.5) * 8) / 9.0) * 9.0
        for vv in np.unique(q[body]):
            m = body & (q == vv)
            opts = [lad.pick(vv, rng, 5), lad.pick(vv, rng, 6)]
            code[m] = np.array(opts)[(f[m] > 0.55).astype(int)]
        ys, xs = np.nonzero(body & (np.abs(shade) < 0.6))
        for k in rng.permutation(len(ys))[: max(2, int(body.sum() / 700))]:
            y, x = int(ys[k]), int(xs[k])
            if y + 3 < H and x + 3 < W and body[y:y + 3, x:x + 3].all():
                code[y:y + 2, x:x + 3] = C('stone_cool', 1)          # an eye scar, 3 x 2
                code[y + 2, x:x + 3] = lad.pick(val[y, x] + 14, rng, 6)
                code[y - 1, x + 1] = C('stone_cool', 1)
    elif kind == 'birch':
        f = ndi.zoom(rng.random((H // 3 + 2, W // 3 + 2)), 3, order=0)[:H, :W]
        q = np.round(val / 9.0) * 9.0
        for vv in np.unique(q[body]):
            m = body & (q == vv)
            opts = [lad.pick(vv, rng, 5), lad.pick(vv, rng, 7)]
            code[m] = np.array(opts)[(f[m] > 0.6).astype(int)]
        ys, xs = np.nonzero(body)
        for k in rng.permutation(len(ys))[: int(body.sum() / 24)]:
            y, x = int(ys[k]), int(xs[k])
            L_ = int(rng.integers(2, 7))
            row = [(y, x + j) for j in range(L_) if x + j < W and body[y, x + j] and y + 1 < H and body[y + 1, x + j]]
            if len(row) < 2:
                continue
            dk = C('stone_cool', 1) if rng.random() < 0.6 else C('stone', 1)
            for (Y, X) in row:
                code[Y, X] = dk
                code[Y + 1, X] = lad.pick(val[Y, X] + 10, rng, 6)
    return val


def trunk2(kind: str, length: int, top_w: float, foot_w: float, rng, *, lean: float = 0.0, twist: float = 0.0,
           roots: int = 3, root_reach=(6, 12), root_rows=(16, 20), limbs: int = 2, limb_rise: float = 30.0,
           limb_spread: float = 24.0, hollow: bool = False, scar: bool = False, burrs: int = 0, front_root=True,
           bark: str | None = None, base_rows: int = 0):
    """A trunk that tapers from foot_w at its foot to top_w under the crown, leans and twists, flares
    into 2 or 3 roots over its last rows (each lit on its west top, dark on its east), and forks at its
    top into `limbs` arching limbs that reach `limb_rise` texels up into the crown. Lit as a cylinder
    from the upper left: a lit west strip, the mid, a dark east. Returns (codes, mask, (foot_x, foot_y),
    top_y) with top_y the row where the bole meets the limbs."""
    bk = bark or kind
    fams, wts, base, crack, spread = BARKS['oak' if bk == 'hollow' else bk]
    lad = Ladder(fams, wts)
    reach = int(root_reach[1]) + 2 if roots else 4
    rise = int(limb_rise) + 4 if limbs else 0
    Wt = int(max(foot_w + 2 * reach, top_w + 2 * limb_spread + 8) + 2 * abs(lean) + 2 * abs(twist) + 10)
    Ht = int(length + rise + 2)
    top_y = rise
    foot_y = Ht - 2
    cx0 = Wt / 2.0
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    t = np.clip((yy - top_y) / max(1.0, foot_y - top_y), 0, 1)
    ph = rng.uniform(0, 6.28)
    cx = cx0 + lean * (1 - t) + twist * np.sin(t * math.pi * 1.3 + ph)
    half = (top_w + (foot_w - top_w) * t ** 1.4) / 2.0 + (ndi.gaussian_filter1d(rng.random(Ht), 3.0)[:, None] - 0.5) * 1.6
    u = (xx - cx) / np.maximum(half, 0.5)
    body = (np.abs(u) <= 1.0) & (yy >= top_y) & (yy < foot_y)
    shade = np.where(body, -u * 0.95 + 0.1, -9.0)                  # west (u < 0) faces the light
    # roots: tapered tubes from the bole's sides out and down to the ground, lit on the west top
    if roots:
        sides = [-1, 1, -1 if rng.random() < 0.5 else 1][:roots]
        for k, sd in enumerate(sides):
            R = rng.uniform(*root_rows)
            y0 = foot_y - R
            yi = int(np.clip(y0, top_y, foot_y - 1))
            h0 = half[yi, 0]
            out_ = rng.uniform(*root_reach) * (0.75 if k == 2 else 1.0)
            sx = cx[yi, 0] + sd * h0 * 0.55
            ex = cx[foot_y - 1, 0] + sd * (half[foot_y - 1, 0] + out_)
            pts = [(sx + (ex - sx) * s_ ** 0.8, y0 + (foot_y - 1 - y0) * (s_ ** 1.6)) for s_ in np.linspace(0, 1, 8)]
            m, sh = _tube(pts, foot_w * 0.42, 3.0, Ht, Wt)
            new = m & ~body
            shade[new] = sh[new]
            body |= m
    if front_root and roots:
        fx = cx[foot_y - 1, 0] + rng.uniform(-0.3, 0.15) * half[foot_y - 1, 0]
        pts = [(fx, foot_y - rng.uniform(10, 14)), (fx + rng.uniform(-2, 2), foot_y - 1)]
        m, sh = _tube(pts, 4.0, 7.0, Ht, Wt)
        shade[m] = np.maximum(shade[m], sh[m]) if False else sh[m]
        body |= m
    body &= yy < foot_y
    # limbs: forking from the bole's top and arching up and out into the crown
    limbm = np.zeros_like(body)
    if limbs:
        tx = cx[top_y, 0]
        dirs = [-1, 1, 0][:limbs] if limbs < 3 else [-1, 0.15, 1]
        for k, sd in enumerate(dirs):
            sx = tx + sd * top_w * 0.22
            sy = top_y + rng.uniform(6, 10)
            ex = tx + sd * limb_spread * rng.uniform(0.8, 1.15)
            ey = top_y - limb_rise * rng.uniform(0.75, 1.0)
            cxp = sx + (ex - sx) * 0.15
            cyp = sy - (sy - ey) * 0.8
            pts = [((1 - s_) ** 2 * sx + 2 * (1 - s_) * s_ * cxp + s_ * s_ * ex,
                    (1 - s_) ** 2 * sy + 2 * (1 - s_) * s_ * cyp + s_ * s_ * ey) for s_ in np.linspace(0, 1, 10)]
            m, sh = _tube(pts, top_w * (0.55 if sd else 0.4), 3.0, Ht, Wt)
            new = m & ~body
            shade[new] = sh[new]
            limbm |= new
        body |= limbm
    code = np.full((Ht, Wt), -1, np.int64)
    val = _bark(code, body, shade, 'hollow' if bk == 'hollow' else bk, lad, base, spread, crack, rng)
    # roots' upper surface lit (west) or a step down (east); the east root's flank dark
    P = np.pad(body, 1)
    top_edge = body & ~P[:-2, 1:-1] & (yy > foot_y - root_rows[1] - 2)
    for y, x in zip(*np.nonzero(top_edge)):
        code[y, x] = lad.pick(val[y, x] + (22 if x < cx[y, 0] else 4), rng, 6)
    # a birch's dark fissured base
    if base_rows:
        dlad = Ladder(('timber_cool', 'stone_cool', 'earth'), {'stone_cool': 1.5})
        bm = body & (yy >= foot_y - base_rows - (ndi.gaussian_filter1d(rng.random(Wt), 2)[None, :] * 6).astype(int))
        for y, x in zip(*np.nonzero(bm)):
            code[y, x] = dlad.pick(60 + 34 * np.clip(shade[y, x], -1, 1), rng, 7)
        Pb = np.pad(bm, 1)
        code[bm & (xx.astype(int) % 3 == 0) & Pb[2:, 1:-1]] = C('stone_cool', 0)
    for _ in range(burrs):
        ys, xs = np.nonzero(body & (np.abs(u) < 0.7) & (yy > top_y + 6) & (yy < foot_y - 14))
        if not len(ys):
            break
        k = int(rng.integers(0, len(ys)))
        y, x = int(ys[k]), int(xs[k])
        r = rng.uniform(2.4, 3.8)
        m = body & (((xx - x) / r) ** 2 + ((yy - y) / (r * 0.8)) ** 2 <= 1)
        bv = val[y, x]
        code[m] = lad.pick(bv, rng, 6)
        code[m & ((xx - x) + (yy - y) < -r * 0.4)] = lad.pick(bv + 20, rng, 6)
        code[m & ((xx - x) + (yy - y) > r * 0.7)] = lad.pick(bv - 18, rng, 6)
        ring = ndi.binary_dilation(m) & ~m & body & ((xx - x) + (yy - y) > 0)
        code[ring] = C(*crack)
    if scar:
        x = int(cx[top_y + 4, 0] - top_w * 0.2)
        for y in range(top_y + 2, int(top_y + (foot_y - top_y) * 0.7)):
            x += int(rng.integers(-1, 2)) if y % 3 == 0 else 0
            for dx, c_ in ((-1, C('timber_cool', 0)), (0, C('plaster', 2)), (1, C('plaster', 1)), (2, C('timber_cool', 0))):
                if 0 <= x + dx < Wt and body[y, x + dx]:
                    code[y, x + dx] = c_
    code[~body] = -1
    hole_ = body & (code < 0)
    if hole_.any():
        idx = ndi.distance_transform_edt(code < 0, return_distances=False, return_indices=True)
        code[hole_] = code[idx[0][hole_], idx[1][hole_]]
    edge = body & ~ndi.binary_erosion(body)
    lit_e = edge & (shade > 0.5) & (yy < foot_y - 2)
    code[edge & ~lit_e] = C(*crack)
    for y, x in zip(*np.nonzero(lit_e)):
        code[y, x] = lad.pick(val[y, x] - 22, rng, 6)
    code[foot_y - 1][body[foot_y - 1]] = C(*crack)                 # the contact line
    _clean(code, body, 1)
    if hollow:
        mid = int(foot_y - 24)                                     # in the bare bole, clear of the crown
        _hollow(code, body, xx, yy, cx[mid, 0] - top_w * 0.05, mid, top_w * 0.22, 8.5, rng)
    return code, body, (float(cx[foot_y - 1, 0]), float(foot_y)), top_y


def crown_masses(S0, n, rng, *, asym=0.12, squat=1.0, wide=1.0):
    """A crown of n major masses inside the box of the master's crown S0 (its size and place kept):
    ellipses of different sizes, set asymmetrically (one shoulder higher and fuller), each with a
    wobbled edge; their union is the silhouette, so they meet in shade notches. Returns (S, masses)
    with masses [(cx, cy, rx, ry)]."""
    H, W = S0.shape
    ys, xs = np.nonzero(S0)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    bw, bh = (x1 - x0) * wide, (y1 - y0) * squat
    cxm = (x0 + x1) / 2.0
    y0 = y1 - bh
    sd = 1 if rng.random() < 0.5 else -1                           # the fuller side
    layout = {
        3: [(0.0, 0.3, 0.36), (-0.27, 0.62, 0.3), (0.27, 0.66, 0.3)],
        4: [(0.05, 0.27, 0.33), (-0.28, 0.52, 0.29), (0.3, 0.47, 0.28), (-0.02, 0.74, 0.31)],
        5: [(0.04, 0.24, 0.3), (-0.3, 0.45, 0.27), (0.31, 0.4, 0.26), (-0.18, 0.74, 0.29), (0.24, 0.76, 0.27)],
        6: [(-0.08, 0.2, 0.27), (0.22, 0.26, 0.24), (-0.33, 0.47, 0.24), (0.35, 0.5, 0.25), (-0.15, 0.76, 0.28),
            (0.25, 0.77, 0.26)],
    }[n]
    masses = []
    for (fx, fy, fr) in layout:
        fx = fx + rng.uniform(-0.04, 0.04) + asym * 0.5
        big = 1.0 + (0.14 if fx * sd > 0 else -0.06)
        rx = fr * bw * big * rng.uniform(0.92, 1.08)
        ry = rx * rng.uniform(0.82, 0.92) * float(np.clip(bh / bw, 0.85, 1.45))
        cy = y0 + fy * bh + (-0.05 * bh if fx * sd > 0 else 0.03 * bh)
        masses.append((cxm + fx * bw, cy, rx, ry))
    # room on every side: the masses may reach past the master's box (then everything shifts)
    sx_ = max(0.0, 4 - min(m[0] - m[2] * 1.12 for m in masses))
    sy_ = max(0.0, 4 - min(m[1] - m[3] * 1.12 for m in masses))
    masses = [(m[0] + sx_, m[1] + sy_, m[2], m[3]) for m in masses]
    shift = (sx_, sy_)
    pad = 6
    Wn = int(max(W + sx_, max(m[0] + m[2] * 1.12 for m in masses) + 4) + pad)
    Hn = int(max(H + sy_, y1 + sy_ + 10) + pad)
    yy, xx = np.mgrid[0:Hn, 0:Wn]
    S = np.zeros((Hn, Wn), bool)
    for k, (cx, cy, rx, ry) in enumerate(masses):
        ang = np.arctan2(yy - cy, xx - cx)
        wob = 1 + 0.06 * np.sin(4 * ang + k * 1.7) + 0.04 * np.sin(7 * ang + k)
        S |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= wob * wob
    return S, masses, shift


def sky_gaps(gaps):
    """Gaps in the crown where the sky shows, set over the limbs so they show through. gaps:
    [(cx, cy, rx, ry)]. Returns carve(mask, code)."""

    def carve(mask, code):
        H, W = mask.shape
        yy, xx = np.mgrid[0:H, 0:W]
        for (cx, cy, rx, ry) in gaps:
            ang = np.arctan2(yy - cy, xx - cx)
            wob = 1 + 0.18 * np.sin(5 * ang + cx) + 0.1 * np.sin(9 * ang + cy)
            g = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= wob * wob
            mask[g] = False
            # the leaves round a gap: their undersides dark over it, their lower lips lit
            ring = ndi.binary_dilation(g, iterations=2) & mask & ~g
            above = ring & (yy < cy)
            for y, x in zip(*np.nonzero(above)):
                code[y, x] = C('leaf_cool', 1)
    return carve


def tree2(kind: str, master_arr: np.ndarray, d: float, seed: int, look: dict, tw: float, scale=None):
    """The second pass of the woodland's trees: crowns of 3 to 6 masses on trunks that taper, lean,
    root and fork into limbs that show through a gap. Returns (codes, foot)."""
    rng = np.random.default_rng(seed * 7 + 31)
    if kind == 'willow':
        return willow2(master_arr, d, rng)
    fams, wts, lo, hi = LOOKS[kind]
    lad = Ladder(fams, wts)
    S0, foot, _ = master_crown(master_arr, d, size=scale)
    T = tw * d
    cfg = {
        'oak': dict(n=5, squat=1.0, wide=0.9, low=0.22, top=0.6, foot=1.05, lean=11, twist=5, roots=3, limbs=2,
                    bark='oak', gaps=2),
        'beech': dict(n=4, squat=1.0, wide=0.9, low=0.2, top=0.68, foot=1.25, lean=-4, twist=1.5, roots=3, limbs=2,
                      bark='beech', gaps=1),
        'birch': dict(n=5, squat=1.0, wide=0.9, low=0.18, top=0.7, foot=1.15, lean=5, twist=1.5, roots=0, limbs=2,
                      bark='birch', gaps=1),
        'hollow_tree': dict(n=6, squat=1.0, wide=0.84, low=0.24, top=0.72, foot=1.0, lean=-5, twist=4, roots=3,
                            limbs=3, bark='hollow', gaps=2),
        'sapling': dict(n=3, squat=1.0, wide=0.9, low=0.2, top=0.6, foot=1.0, lean=3, twist=1.0, roots=0, limbs=0,
                        bark='sapling', gaps=0),
        'pine': dict(top=0.6, foot=1.05, lean=2, twist=1.0, roots=3, limbs=0, bark='pine'),
    }[kind]
    if kind == 'pine':
        from . import foliage as F5
        S = S0
        tiers = list(F5._tiers(S, look.get('clump', 9.0) * d * 0.7))
        code, mask, v = pine_crown(S, tiers, lad, rng, lo, hi)
        gaps = []
    else:
        S, masses, sh_ = crown_masses(S0, cfg['n'], rng, squat=cfg['squat'], wide=cfg['wide'])
        foot = (foot[0] + sh_[0], foot[1] + sh_[1])
        # the gaps go where the limbs will pass: about halfway up each limb's arch
        ysS = np.nonzero(S.any(1))[0]
        cbot, chgt = ysS.max(), ysS.max() - ysS.min()
        Wc = np.nonzero(S.any(0))[0]
        spread = (Wc.max() - Wc.min()) * 0.16
        ltop = cbot - 10                                            # where the bole meets its limbs
        rise_ = max(12.0, ltop - (ysS.min() + chgt * 0.45))
        gaps = []
        for k_, sd in enumerate((-1, 1)[:cfg['gaps']] if cfg['gaps'] else ()):
            gaps.append((foot[0] + cfg['lean'] + sd * 0.42 * spread, ltop - 0.55 * rise_,
                         rng.uniform(9, 12) if k_ == 0 else rng.uniform(6, 8), rng.uniform(7, 9) if k_ == 0 else rng.uniform(5, 6.5)))
        carve = sky_gaps(gaps) if gaps else None
        code, mask, v = leaf_crown(S, masses, lad, rng, lo=lo, hi=hi, under_gap=7, low_band=cfg['low'], carve=carve,
                                   edge_fam='leaf_cool' if kind in ('beech', 'hollow_tree') else 'leaf')
        if kind == 'birch':
            _twig_hangs(code, mask, lad, rng, lo, hi)
    H, W = mask.shape
    # the trunk: from the foot up into the crown, its limbs reaching into the lowest masses
    cols = int(round(foot[0]))
    half_t = max(2, int(T / 2))
    band = mask[:, max(0, cols - half_t):cols + half_t + 1]
    bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
    cb = min(bots) if bots else foot[1] - 10 * d
    if kind == 'hollow_tree':
        # a squat veteran: a bare bole about 0.6 H below the crown's lowest leaves
        foot = (foot[0], np.nonzero(mask.any(1))[0].max() + 0.6 * 74)
    if kind == 'sapling':
        tr = sapling_stem(int(foot[1] - cb + 8), rng)
        out, ft = _compose(tr, code, mask, foot)
        return _crop(out, ft)
    length = int(foot[1] - cb + 10)
    ys_c = np.nonzero(mask.any(1))[0]
    rise = (foot[1] - length) - (ys_c.min() + (ys_c.max() - ys_c.min()) * 0.45)
    tw2 = T * (1.25 if kind == 'beech' else 1.0) * (1.6 if kind == 'hollow_tree' else 1.0)
    tc, tm, (tfx, tfy), ty = trunk2(cfg['bark'] if cfg['bark'] != 'hollow' else 'oak', length, tw2 * cfg['top'],
                                    tw2 * cfg['foot'], rng, lean=cfg['lean'], twist=cfg['twist'], roots=cfg['roots'],
                                    limbs=cfg['limbs'], limb_rise=max(12.0, rise), limb_spread=spread if kind != 'pine' else 0.0,
                                    hollow=kind == 'hollow_tree', scar=kind == 'hollow_tree',
                                    burrs=3 if kind == 'hollow_tree' else (1 if kind == 'oak' else 0),
                                    bark=cfg['bark'], base_rows=12 if kind == 'birch' else 0,
                                    front_root=kind not in ('birch',))
    out, ft = _compose((tc, tm, (tfx, tfy)), code, mask, foot)
    return _crop(out, ft)


def _hang_leaves(seed=11, n=30):
    r = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        lw, lh, tp = int(r.integers(4, 7)), int(r.integers(5, 8)), int(r.integers(-1, 2))
        m = np.zeros((lh + 1, lw), bool)
        for y in range(lh + 1):
            w_ = lw * (1 - (y / (lh + 1)) ** 2 * 0.8)
            c_ = (lw - 1) / 2 + tp * y / lh * 0.6
            m[y, max(0, int(round(c_ - w_ / 2))):int(round(c_ + w_ / 2)) + 1] = True
        out.append(m)
    return out


HANG = _hang_leaves()


def _swag(code, mask, pts, w, lad, lo, hi, rng, dim=0.0):
    """One swag of hanging leaves along pts [(x, y, s)], w wide at its top, tapering to its tip; lit
    on its west side, dark on its east, leaf tips out of its sides."""
    H, W = mask.shape
    for (px, py, s_) in reversed(pts):                              # the tip first: upper leaves over it
        ww = w * (1 - 0.72 * s_ ** 1.3)
        for q in (-1, 0, 1):
            if ww < 4 and q != 0:
                continue
            m = HANG[int(rng.integers(0, len(HANG)))]
            lx = int(round(px + q * ww / 3 - m.shape[1] / 2 + rng.uniform(-1.0, 1.0)))
            ly = int(round(py - m.shape[0] / 2 + rng.uniform(-1.5, 1.5)))
            if q != 0 and rng.random() < 0.3:
                lx += q * 2
            val = 0.78 - 0.4 * s_ - dim + rng.uniform(-0.05, 0.05) + (0.16 if q < 0 else (-0.18 if q > 0 else 0))
            T = lo + (hi - lo) * float(np.clip(val, 0.02, 1))
            c_ = lad.pick(T, rng, 6)
            ys2, xs2 = np.nonzero(m)
            Y, X = ys2 + ly, xs2 + lx
            ok = (Y >= 0) & (Y < H) & (X >= 0) & (X < W)
            code[Y[ok], X[ok]] = c_
            mask[Y[ok], X[ok]] = True
            P = np.pad(m, 1)
            for part, dv in ((m & ~P[1:-1, :-2], 11), (m & ~P[1:-1, 2:], -13)):
                ys3, xs3 = np.nonzero(part)
                Y, X = ys3 + ly, xs3 + lx
                ok = (Y >= 0) & (Y < H) & (X >= 0) & (X < W)
                code[Y[ok], X[ok]] = lad.pick(T + dv, rng, 5)


def willow2(master_arr, d, rng):
    """A weeping willow (W-T7, second pass): a short thick leaning trunk forking into three limbs that
    arch up and out; a cap of leaf masses over them, wider than tall; swags that spring from the cap,
    swing outward past its shoulders and curve back in as they hang, of very different lengths (some
    end at mid-height), so the trunk and the limbs show between them; the crown about 1.3 times as
    wide as it is tall, with no straight side."""
    fams, wts, lo, hi = LOOKS['willow']
    lad = Ladder(fams, wts)
    al = master_arr[..., 3] > 0
    ys, xs = np.nonzero(al)
    W = int(round((xs.max() - xs.min() + 1) * d * 1.12))          # a little wider than the master
    Hc = int(round(W / 1.32))                                       # the crown: wider than tall
    pad = int(0.16 * W)
    Wp = W + 2 * pad
    top = pad
    hem = top + Hc
    foot_y = hem + 26
    Hp = foot_y + 4
    cx = Wp / 2.0
    code = np.full((Hp, Wp), -1, np.int64)
    mask = np.zeros((Hp, Wp), bool)
    # the interior: deep shade under the cap, behind the swags (painted where swags hang round it)
    # the cap: 5 masses along an arch (the middle highest and fullest), a dome wider than tall
    cap = []
    for k, f in enumerate((-0.7, -0.36, 0.0, 0.36, 0.7)):
        rx = W * (0.22 if abs(f) < 0.2 else 0.19) * rng.uniform(0.95, 1.05)
        ry = rx * rng.uniform(0.74, 0.84)
        cap.append((cx + f * W * 0.48 + rng.uniform(-3, 3), top + ry + Hc * 0.34 * f * f + rng.uniform(0, 3), rx, ry))
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    capS = np.zeros((Hp, Wp), bool)
    for k, (mx, my, rx, ry) in enumerate(cap):
        ang = np.arctan2(yy - my, xx - mx)
        wob = 1 + 0.06 * np.sin(4 * ang + k)
        capS |= ((xx - mx) / rx) ** 2 + ((yy - my) / ry) ** 2 <= wob * wob
    ccode, cmask, v = leaf_crown(capS, cap, lad, rng, lo=lo + 12, hi=hi, under_gap=6, low_band=0.3, edge_fam='leaf')
    # the swags' springing points: along the cap's underside and its shoulders
    springs = []
    n_sw = 33
    for k in range(n_sw):
        f = (k + rng.uniform(-0.3, 0.3)) / (n_sw - 1) * 2 - 1           # -1 west .. 1 east
        x = cx + f * W * 0.45
        col = np.nonzero(cmask[:, int(np.clip(x, 0, Wp - 1))])[0]
        # a front swag springs from high in the cap and hangs over its lower half (no hard hem to the
        # cap); the outer ones from its shoulders, so they carry the dome's outline down
        y = (col.min() + (col.max() - col.min()) * rng.uniform(0.3, 0.65)) if len(col) else top + Hc * 0.3
        springs.append((f, x, y))
    # the trunk: short, thick and leaning, forking into three arching limbs
    fork = top + Hc * 0.74
    tc, tm, (tfx, tfy), ty = trunk2('willow', int(foot_y - fork), 22, 36, rng, lean=16 * (1 if rng.random() < 0.5 else -1),
                                    twist=5, roots=3, root_reach=(6, 11), root_rows=(12, 16), limbs=3,
                                    limb_rise=Hc * 0.55, limb_spread=W * 0.3, bark='willow')
    ox, oy = int(round(cx - tfx)), int(round(foot_y - tfy))
    # order: back swags (the middle, darker), the interior, the trunk and limbs, the front swags, the cap
    back = [s for s in springs if abs(s[0]) < 0.55 and abs(s[0]) > 0.16 and rng.random() < 0.75]
    front = [s for s in springs if s not in back]

    def swag_path(f, x, y, short):
        span = hem - y
        L = span * ((rng.uniform(0.3, 0.48) if abs(f) < 0.25 else rng.uniform(0.38, 0.7)) if short
                    else rng.uniform(0.72, 1.0))
        A = (6 + 16 * abs(f)) * rng.uniform(0.8, 1.2)              # out past the shoulder
        B = (4 + 14 * abs(f)) * rng.uniform(0.8, 1.2)              # and back in as it hangs
        sg = 1 if f >= 0 else -1
        pts = []
        n = max(4, int(L / 2.8))
        for j in range(n + 1):
            s_ = j / n
            px = x + sg * (A * math.sin(min(1.0, s_ / 0.4) * math.pi / 2) - B * max(0.0, s_ - 0.4) ** 1.4 / 0.6 ** 1.4)
            px += 0.8 * math.sin(s_ * 6 + x)
            pts.append((px, y + L * s_, s_))
        return pts

    paths = {}
    for s in springs:
        short = abs(s[0]) < 0.3 and rng.random() < 0.9 or rng.random() < 0.3
        paths[s] = swag_path(*s, short)
    for s in back:
        _swag(code, mask, paths[s], rng.uniform(7, 10), lad, lo, hi, rng, dim=0.28)
    # the interior shade: inside the cap's shadow, between the back swags and the front
    region = (yy > top + Hc * 0.25) & (yy < hem - Hc * 0.35) & (np.abs(xx - cx) < W * 0.4)
    region &= ndi.binary_dilation(mask, iterations=4) | (yy < top + Hc * 0.45)
    pf = ndi.gaussian_filter(rng.random((Hp, Wp)), 2.5)
    pf = (pf - pf.min()) / max(1e-6, pf.max() - pf.min())
    opts = [lad.pick(lo - 10, rng, 4), lad.pick(lo - 2, rng, 4), lad.pick(lo + 6, rng, 4)]
    for y, x in zip(*np.nonzero(region & ~mask)):
        code[y, x] = opts[min(2, int(pf[y, x] * 3))]
    mask |= region
    # the trunk and limbs over the interior
    for y, x in zip(*np.nonzero(tm)):
        Y, X = y + oy, x + ox
        if 0 <= Y < Hp and 0 <= X < Wp:
            code[Y, X] = tc[y, x]
            mask[Y, X] = True
    code[cmask] = ccode[cmask]
    mask |= cmask
    for s in front:
        _swag(code, mask, paths[s], rng.uniform(7, 11), lad, lo, hi, rng, dim=0.0 if abs(s[0]) > 0.4 else 0.1)
    mask = ndi.binary_fill_holes(_spurs(mask))
    hole = mask & (code < 0)
    if hole.any():
        idx = ndi.distance_transform_edt(code < 0, return_distances=False, return_indices=True)
        code[hole] = code[idx[0][hole], idx[1][hole]]
    code[~mask] = -1
    _clean(code, mask)
    # the outline: leaf edge round the leaves, the bark's crack round the wood
    tmf = np.zeros_like(mask)
    ty_, tx_ = np.nonzero(tm)
    ok = (ty_ + oy < Hp) & (tx_ + ox < Wp) & (ty_ + oy >= 0) & (tx_ + ox >= 0)
    tmf[ty_[ok] + oy, tx_[ok] + ox] = True
    edge = mask & ~ndi.binary_erosion(mask)
    P = np.pad(mask, 1)
    lit_side = edge & (~P[1:-1, :-2] | ~P[:-2, 1:-1]) & (xx < cx) & (yy < hem - Hc * 0.4)
    woodedge = edge & tmf & (yy > hem - 30)
    code[edge & ~lit_side & ~woodedge] = C('leaf_cool', 0)
    code[woodedge] = C('timber_cool', 0)
    for y, x in zip(*np.nonzero(lit_side & ~woodedge)):
        code[y, x] = lad.pick(lo + (hi - lo) * 0.35, rng, 6)
    return _crop(code, (cx, foot_y))

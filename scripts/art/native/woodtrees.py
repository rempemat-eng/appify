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

Third pass (round 2 of the audit, W2-F1 to W2-B3): `clump_crown` builds every broadleaf crown, the
willow's cap, the pine's tiers and the shrubs from overlapping leaf clumps (lit crescent, body in two
siblings, a two-step dark U) with no seam band between masses: an upper mass's lowest clumps hang
over the lower one as scallops with lit tips and small pockets; sky gaps open only at the crown's
foot or edge. Bark is vertical plates (`_bark`); the beech is mottled grey with algae, eye scars and
buttress fins; the hollow has an inner wall; the pine's tiers are irregular; the willow's swags are
hanging leaf clumps; brambles have drooping, thorned canes; holly has edge-grown spines.
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


def _key(code: int):
    return tuple(int(v) // 16 for v in LUT[code])


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
# third pass (round 2 of the detail audit, W2-F1 to W2-F4): crowns of overlapping leaf clumps
# ------------------------------------------------------------------------------------------------
def _clump_shapes(seed: int = 3, n: int = 48, wr=(5, 10), hf=(0.7, 0.88)):
    """Leaf clumps wr[0]..wr[1]-1 texels across, a little wider than tall: a round top (now and then
    a notch between two lobes) and a lower edge of 2 or 3 scallops, each a leaf tip pointing down.
    Each: (mask, crescent, tip, body2, under): the crescent is the lit upper-left rim 2 texels deep,
    the tip its brightest 2 texels, body2 the body's lower-right sibling half, under the dark U (the
    scalloped lower rim 1 to 2 texels deep and the east side below mid-height)."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        w = int(rng.integers(*wr))
        h = max(4, int(round(w * rng.uniform(*hf))))
        lob = 2 if w < 7 else int(rng.integers(2, 4))
        H, W = h + 2, w
        m = np.zeros((H, W), bool)
        cx = (W - 1) / 2.0
        ry = h / 2.0
        ph = rng.uniform(-0.4, 0.4)
        for x in range(W):
            u = (x - cx) / (w / 2.0)
            q = max(0.0, 1 - u * u)
            top = ry - ry * math.sqrt(q) * (1 + rng.uniform(-0.04, 0.04))
            # the scallops: lob rounded bumps along the lower edge
            sc = 0.5 + 0.5 * math.cos((u * lob / 2.0 + 0.5 * (lob % 2) + ph * 0.3) * 2 * math.pi)
            bot = ry + ry * math.sqrt(q) * 0.92 + 1.6 * sc * q ** 0.3
            y0, y1 = int(round(top + 0.2)), int(round(bot))
            m[max(0, y0):min(H, y1 + 1), x] = True
        if w >= 7 and rng.random() < 0.4:                             # two lobes on top
            xs_ = int(round(cx + rng.uniform(-1, 1)))
            col = np.nonzero(m[:, xs_])[0]
            if len(col):
                m[col.min(), xs_] = False
        m = _spurs(m)
        yy, xx = np.mgrid[0:H, 0:W].astype(float)
        cy = (H - 1) / 2.0
        P = np.pad(m, 2)
        up1, up2 = P[1:-3, 2:-2], P[:-4, 2:-2]
        lf1, lf2 = P[2:-2, 1:-3], P[2:-2, :-4]
        dn1, dn2 = P[3:-1, 2:-2], P[4:, 2:-2]
        rt1 = P[2:-2, 3:-1]
        ul = (xx - cx) / w * 1.2 + (yy - cy) / h < 0.15
        cres = m & ul & (~up1 | ~up2 | ~lf1 | (~lf2 & (yy < cy)))
        under = m & ~cres & (~dn1 | (~dn2 & (yy > cy)) | (~rt1 & (yy > cy - 1)))
        body = m & ~cres & ~under
        body2 = body & ((xx - cx) / w + (yy - cy) / h > 0.1)
        cy_, cx_ = np.nonzero(cres)
        o = np.argsort(cy_ * 1.0 + 0.8 * cx_)[:2]
        tip = np.zeros_like(m)
        tip[cy_[o], cx_[o]] = True
        out.append((m, cres, tip, body2, under))
    return out


CLUMPS = _clump_shapes()
CLUMPS_S = _clump_shapes(seed=4, wr=(4, 8))
CLUMPS_XS = _clump_shapes(seed=6, wr=(4, 6))
NEEDLE_CLUMPS = _clump_shapes(seed=8, wr=(4, 7), hf=(1.0, 1.4))      # pine sprays: taller than wide


def dark_runs(code: np.ndarray, mask: np.ndarray, thr: float = 62.0, erode: int = 3) -> int:
    """The longest dark component (L under thr) inside the crown eroded by `erode`: the W2-F1 check
    (a drawn seam band between masses is 30 to 150 px long; pockets stay under 16)."""
    L = np.zeros(code.shape)
    ok = code >= 0
    L[ok] = np.array([_lum(int(c)) for c in code[ok]])
    inner = ndi.binary_erosion(mask, iterations=erode)
    lab, n = ndi.label(inner & (L < thr) & ok)
    best = 0
    for sl in ndi.find_objects(lab):
        if sl is not None:
            best = max(best, sl[0].stop - sl[0].start, sl[1].stop - sl[1].start)
    return best


def _clump_crown_p3(S: np.ndarray, masses, lad: Ladder, rng, *, lo: float, hi: float, bands: int = 4,
                shapes=None, gaps=(), low_band: float = 0.0, edge_fam: str = 'leaf_cool',
                glint_fam: str = 'grass_warm', pockets: float = 0.8, density: float = 0.85, quiet: int = 1,
                lift: float = 0.0, fams=('grass', 'leaf'), fam_w=None, order: int = -1, ccon=(13.0, 26.0, 17.0), tips_from: int = 1, cres2: bool = False,
                avoid_near: bool = True, sib_spread: float = 5, inner_pockets: float = 0.0,
                veins: float = 0.9, u2: bool = True, tips: bool = True, ufloor: float = 61.0):
    """Paint a crown S as overlapping leaf clumps (art-style 4, the red tree in Eastward 12 at the
    same character height; W2-F1 to F3):

    - masses [(cx, cy, rx, ry)] are domes lit from the upper left, the upper ones in front; there is
      no seam between them: where an upper mass overlaps a lower one its lowest clumps hang over the
      lower mass's lit caps as scallops with their tips down, and under every second or third of
      them a small pocket (leaf 0 to 1, 2 to 4 texels deep, never joined into a line);
    - every clump (5 to 9 texels) has a lit crescent at its upper left (its 2 brightest texels a
      tone up again), a body in two siblings and a dark U under it; clumps overlap by about a third,
      offset like scales, painted from the bottom up so each one's tips lie over the clump below;
      between them the deep band shows in small pockets;
    - the deep band (low_band: the crown's foot) is clumps in its dark tones only, no caps;
    - gaps [(cx, cy, rx, ry)] are sky where a limb leaves the under-band: open to the outside, no
      clump centred in them, their rim the clumps' own undersides and hanging tips (no outline);
    - the silhouette is the clumps' own outlines, closed in the leaf edge tone except on the lit
      upper left.
    Returns (codes, mask, value)."""
    Hp, Wp = S.shape
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    shapes = shapes or CLUMPS
    S = ndi.binary_fill_holes(S)                                      # no bare patch where masses part
    gapm = np.zeros((Hp, Wp), bool)
    for (gx, gy, grx, gry) in gaps:
        ang = np.arctan2(yy - gy, xx - gx)
        wob = 1 + 0.16 * np.sin(5 * ang + gx) + 0.08 * np.sin(9 * ang + gy)
        gapm |= ((xx - gx) / grx) ** 2 + ((yy - gy) / gry) ** 2 <= wob * wob
    S &= ~gapm
    # the masses' light: each a dome, half the crown as one dome; the upper masses in front
    ms = sorted(masses, key=lambda m: -m[1])                           # lowest first, upper over it
    owner = np.full((Hp, Wp), -1)
    for k, (cx, cy, rx, ry) in enumerate(ms):
        ang = np.arctan2(yy - cy, xx - cx)
        wob = 1 + 0.07 * np.sin(3 * ang + k) + 0.05 * np.sin(5 * ang + 2 * k)
        owner[(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= wob * wob * 1.1) & S] = k
    miss = S & (owner < 0)
    if miss.any() and (owner >= 0).any():
        idx = ndi.distance_transform_edt(owner < 0, return_distances=False, return_indices=True)
        owner[miss] = owner[idx[0][miss], idx[1][miss]]
    Lv = np.array([-0.55, -0.68, 0.48])
    Lv = Lv / np.linalg.norm(Lv)
    Cc = np.array(ms, float)
    o = np.clip(owner, 0, None)
    mcx, mcy, mrx, mry = (Cc[o, i] for i in range(4))
    U = np.clip((xx - mcx) / mrx, -1, 1)
    V = np.clip((yy - mcy) / mry, -1, 1)
    lam = U * Lv[0] + V * Lv[1] + np.sqrt(np.clip(1 - U * U - V * V, 0, 1)) * Lv[2]
    ys, xs = np.nonzero(S)
    gx0, gy0 = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    grx, gry = (xs.max() - xs.min()) / 2 + 1, (ys.max() - ys.min()) / 2 + 1
    Ug, Vg = np.clip((xx - gx0) / grx, -1, 1), np.clip((yy - gy0) / gry, -1, 1)
    lamg = Ug * Lv[0] + Vg * Lv[1] + np.sqrt(np.clip(1 - Ug * Ug - Vg * Vg, 0, 1)) * Lv[2]
    # a mass's underside never falls into a band of its own (no seam): the masses part by their
    # scallops and pockets, and the crown's own dome carries the light
    lam = np.maximum(lam, 0.15)
    v = np.clip((0.45 * lam + 0.55 * lamg + 0.1 + lift) / 1.0, 0, 1)
    if low_band:
        bh = max(4.0, low_band * (ys.max() - ys.min()))
        f = np.clip((yy - (ys.max() - bh)) / bh, 0, 1)
        v = v * (1 - 0.8 * f)
    band = np.clip(np.floor(v * bands), 0, bands - 1).astype(int)
    T = lo + (hi - lo) * np.arange(bands) / max(1, bands - 1)
    code = np.full((Hp, Wp), -1, np.int64)
    # the deep band under everything: small pockets in two or three dark siblings
    base_in = ndi.binary_erosion(S, iterations=2) | (S & (owner >= 0) & False)
    patch = ndi.zoom(rng.random((Hp // 3 + 2, Wp // 3 + 2)), 3, order=0)[:Hp, :Wp]
    deep = [C('leaf_warm', 1), C('grass_cool', 1), C('leaf_warm', 1)]   # between clumps: mid-dark (pockets go darker)
    fw = np.array([fam_w.get(f, 1.0) for f in fams])
    fw = fw / fw.sum()
    code[S] = np.array(deep)[np.minimum(2, (patch[S] * 3).astype(int))]
    # the clump centres: a staggered grid at about two thirds of a clump, jittered
    sz = np.mean([s[0].shape[1] - 2 for s in shapes])
    sx_, sy_ = sz * density * 1.05, sz * density * 0.82
    cells = []
    inner = ndi.binary_erosion(S, iterations=1)
    for j, y in enumerate(np.arange(-2, Hp + 2, sy_)):
        off = (sx_ / 2.0) * (j % 2)
        for x in np.arange(-2, Wp + 2, sx_) + off:
            yc = int(round(y + rng.uniform(-1.2, 1.2)))
            xc = int(round(x + rng.uniform(-1.4, 1.4)))
            if 0 <= yc < Hp and 0 <= xc < Wp and inner[yc, xc]:
                cells.append((yc, xc))
    # the lower masses first, the upper ones over them (their lowest clumps hang over as scallops);
    # inside a mass from the top down, so every clump shows its lit cap over the one above it
    cells.sort(key=lambda c: (int(owner[c[0], c[1]]), order * c[0] + rng.uniform(-0.8, 0.8), c[1]))
    cover = np.zeros((Hp, Wp), bool)
    pockets_at = []
    low_items = tuple(it[1] for it in lad.items if it[0] < ufloor)

    def _pk(t_, rng_, spread_, avoid=()):
        # the clumps' colours stay over the floor: only the pockets go to leaf 0 to 1 (W2-F1)
        c_ = lad.pick(max(t_, ufloor), rng_, spread_, avoid=avoid)
        if _lum(c_) < ufloor:
            c_ = lad.pick(max(t_, ufloor), rng_, spread_ + 6, avoid=tuple(avoid) + low_items)
        return c_

    for (yc, xc) in cells:
        m, cres, tip, body2, under = shapes[int(rng.integers(0, len(shapes)))]
        if rng.random() < 0.35:                                     # mirrored now and then: the
            m, cres, tip, body2, under = (a[:, ::-1] for a in (m, cres, tip, body2, under))   # light stays
            cres = cres & (np.arange(m.shape[1])[None, :] < m.shape[1] * 0.75)
        h, w = m.shape
        y0, x0 = yc - h // 2 + 1, xc - w // 2
        b = int(band[yc, xc])
        t = max(lo + 3, ufloor + 6, T[b] + rng.uniform(-3, 3))
        k = int(owner[yc, xc])
        # where this (upper) mass hangs over a lower one: the clump is a scallop with its tips lit and
        # its U only on the east; under every second or third a pocket (leaf 0 to 1, 2 to 4 deep)
        yb = y0 + h - 1
        rim_clump = False
        if k >= 0 and yb + 2 < Hp:
            below = owner[min(Hp - 1, yb + 2), min(Wp - 1, max(0, xc))]
            rim_clump = bool(below >= 0 and below < k)
            if rim_clump and pockets and rng.random() < pockets \
                    and all(abs(xc - px) > 8 or abs(yb - py) > 5 for (py, px) in pockets_at):
                pw, pd = int(rng.integers(2, 4)), int(rng.integers(2, 4))
                px0 = xc - pw // 2 + int(rng.integers(-1, 2))
                pc = C('leaf_cool', 0) if rng.random() < 0.5 else C('leaf', 1)
                for dy in range(pd + 1):
                    ww_ = max(1, pw - (dy * pw) // (pd + 1))
                    for dx in range(ww_):
                        Y, X = yb - 1 + dy, px0 + dx + (pw - ww_) // 2
                        if 0 <= Y < Hp and 0 <= X < Wp and S[Y, X]:
                            code[Y, X] = pc
                            cover[Y, X] = True
                pockets_at.append((yb, xc))
            elif not rim_clump and inner_pockets and int(band[yc, xc]) >= quiet and rng.random() < inner_pockets \
                    and all(abs(xc - px) > 6 or abs(yb - py) > 4 for (py, px) in pockets_at):
                # a small dark pocket between this clump and the ones below (2 to 3 texels)
                sd_ = 1 if rng.random() < 0.5 else -1
                px0 = xc + sd_ * int(rng.integers(1, max(2, w // 2)))
                pc = lad.pick(_lum(int(code[min(Hp - 1, yb), min(Wp - 1, max(0, px0))])) - 30
                              if code[min(Hp - 1, yb), min(Wp - 1, max(0, px0))] >= 0 else lo - 10, rng, 6)
                for (dy, dx) in ((0, 0), (0, 1), (1, 0), (1, 1), (2, int(rng.integers(0, 2))))[:int(rng.integers(3, 6))]:
                    Y, X = yb + dy, px0 + dx
                    if 0 <= Y < Hp and 0 <= X < Wp and S[Y, X]:
                        code[Y, X] = pc
                pockets_at.append((yb, xc))
        # one ramp a clump (cap a tone up, its tip two, the U a tone down); its lower-right half and
        # the next clump a sibling of another green at the same value
        # the colours the clump lands on: its parts take siblings unlike them, so two clumps never
        # merge into one patch (the next clump a sibling of another green at the same value)
        yy0, xx0 = np.nonzero(m)
        Yc, Xc = np.clip(yy0 + y0, 0, Hp - 1), np.clip(xx0 + x0, 0, Wp - 1)
        near = set(int(c) for c in np.unique(code[Yc, Xc]) if c >= 0) if avoid_near else set()
        if near:
            # and unlike them at the screen's 16 levels too, so they stay apart through compression
            nk = {_key(c) for c in near}
            near |= {it[1] for it in lad.items if _key(it[1]) in nk}
        body = _pk(t, rng, sib_spread, avoid=tuple(near))
        if _lum(body) < ufloor:
            body = _pk(t, rng, 9, avoid=tuple(it[1] for it in lad.items if it[0] < ufloor))
        Lb = _lum(body)
        b2 = _pk(Lb, rng, 4, avoid=tuple(near | {body}))
        if abs(_lum(b2) - Lb) > 7:
            b2 = body
        if b < quiet:
            # quiet: no lit cap, its crescent a sibling at the body's value (shape, not light)
            lit = tipc = _pk(Lb + 3, rng, 4, avoid=tuple(near | {body}))
            if abs(_lum(lit) - Lb) > 7:
                lit = tipc = body
            dark = _pk(max(Lb - 7, ufloor), rng, 4, avoid=tuple(near | {body}))
        else:
            lit = _pk(Lb + ccon[0], rng, 5, avoid=tuple(near | {body}))
            tipc = _pk(Lb + ccon[1], rng, 5, avoid=(lit,)) if b >= bands - 1 - tips_from else lit
            dark = _pk(max(Lb - ccon[2], ufloor), rng, 5, avoid=tuple(near | {body, b2}))
        if rim_clump and b >= quiet:
            hh_ = np.arange(h)[:, None]
            low_tips = under & (hh_ >= h - 3) & (np.arange(w)[None, :] < w * 0.7)
            under = under & ~low_tips
            parts = ((m, body), (body2, b2), (cres, lit), (tip, tipc), (under, dark), (low_tips, lit))
        else:
            parts = ((m, body), (body2, b2), (cres, lit), (tip, tipc), (under, dark))
        if u2 and b >= quiet:
            # the U in two steps: its lowest texels darkest, the row above and the east side half way
            Pm = np.pad(m, ((0, 1), (0, 0)))
            low_row = under & ~Pm[1:, :]
            dark2 = _pk(max(Lb - ccon[2] * 0.55, ufloor + 5), rng, 4, avoid=tuple(near | {body, b2, dark}))
            parts = parts + ((under & ~low_row, dark2), (low_row, dark))
        if veins and rng.random() < veins:
            # a leaf inside the clump: 2 to 3 texels of a sibling at the body's value (house-style 4)
            inner_b = m & ~cres & ~under & ~tip
            iy, ix = np.nonzero(inner_b)
            if len(iy) >= 6:
                j_ = int(rng.integers(0, len(iy)))
                vm_ = np.zeros_like(m)
                vm_[iy[j_], ix[j_]] = True
                for dy, dx in ((0, 1), (1, 0), (1, 1), (0, -1))[:int(rng.integers(1, 3))]:
                    Y_, X_ = iy[j_] + dy, ix[j_] + dx
                    if 0 <= Y_ < h and 0 <= X_ < w and inner_b[Y_, X_]:
                        vm_[Y_, X_] = True
                bk_ = {_key(body), _key(b2)}
                vc_ = _pk(Lb + rng.choice((-4, 4)), rng, 5,
                               avoid=tuple({body, b2, lit, dark} | {it[1] for it in lad.items if _key(it[1]) in bk_}))
                if abs(_lum(vc_) - Lb) <= 8 and vm_.sum() >= 2:
                    parts = parts + ((vm_, vc_),)
        if cres2 and b >= quiet:
            # the crescent's west arm a sibling of its top (two leaves, not one band)
            ww_ = np.arange(w)[None, :]
            arm = cres & (ww_ < w * 0.3) & (np.arange(h)[:, None] > h * 0.3)
            parts = parts + ((arm, _pk(_lum(lit), rng, 4, avoid=(lit,))),)
        for part, c_ in parts:
            py_, px_ = np.nonzero(part)
            Y, X = py_ + y0, px_ + x0
            ok = (Y >= 0) & (Y < Hp) & (X >= 0) & (X < Wp)
            Y, X = Y[ok], X[ok]
            code[Y, X] = c_
            cover[Y, X] = True
    mask = ndi.binary_erosion(S, iterations=2) | cover
    # glints: yellow-green pairs on the most lit caps of the upper-left masses
    lit_caps = mask & (band >= bands - 1) & (xx < gx0) & (yy < gy0)
    ys, xs = np.nonzero(lit_caps)
    for k in rng.permutation(len(ys))[: max(1, int(len(ys) / 160))]:
        y, x = int(ys[k]), int(xs[k])
        if x + 1 < Wp and mask[y, x + 1]:
            code[y, x] = code[y, x + 1] = C(glint_fam, 5)
    if tips:
        # the silhouette's leaf tips on the top and the west (2 to 4 texels, every 6 to 12), each in
        # the colour of the leaf it grows from
        gy_, gx_ = np.gradient(ndi.gaussian_filter(mask.astype(float), 2.0))
        edge = mask & ~ndi.binary_erosion(mask) & ~ndi.binary_dilation(gapm, iterations=3)
        ys, xs = np.nonzero(edge)
        taken = []
        for k in rng.permutation(len(ys)):
            y, x = int(ys[k]), int(xs[k])
            nx_, ny_ = -gx_[y, x], -gy_[y, x]
            nn = math.hypot(nx_, ny_)
            if nn < 1e-6:
                continue
            nx_, ny_ = nx_ / nn, ny_ / nn
            if not (ny_ < -0.35 or nx_ < -0.35 or (nx_ > 0.35 and ny_ < 0.3)):
                continue
            gap = rng.uniform(5, 10)
            if any((y - ty) ** 2 + (x - tx) ** 2 < gap * gap for (ty, tx) in taken):
                continue
            taken.append((y, x))
            L_ = int(rng.integers(2, 5))
            c0_ = int(code[y, x]) if code[y, x] >= 0 else deep[1]
            # the tip a leaf of its own: a sibling a touch lighter (it catches the light at the edge)
            c_ = lad.pick(_lum(c0_) + 6, rng, 5, avoid=tuple(it[1] for it in lad.items if _key(it[1]) == _key(c0_)))
            px, py = -ny_, nx_
            for s_ in range(1, L_ + 1):
                half = (L_ - s_) / 2.0 * 0.9
                for q in np.arange(-half, half + 0.01, 0.5):
                    X = int(round(x + nx_ * s_ + px * q))
                    Y = int(round(y + ny_ * s_ + py * q))
                    if 0 <= X < Wp and 0 <= Y < Hp:
                        mask[Y, X] = True
                        code[Y, X] = c_
    mask = _spurs(mask)
    # no enclosed holes: a hole left between clumps is a pocket of the deep band
    filled = ndi.binary_fill_holes(mask)
    hole = filled & ~mask
    mask = filled
    hole |= mask & (code < 0)
    if hole.any():
        code[hole] = deep[1]
    code[~mask] = -1
    _clean(code, mask, 3)
    # the outline: the leaf edge tone in runs of its dark siblings, broken lighter on the lit upper
    # left; round a gap no outline, the clumps' own undersides (leaf 1)
    edge = mask & ~ndi.binary_erosion(mask)
    P = np.pad(mask, 1)
    lit_side = edge & (~P[:-2, 1:-1] | ~P[1:-1, :-2]) & P[2:, 1:-1] & P[1:-1, 2:] & (v > 0.5)
    gap_rim = edge & ndi.binary_dilation(gapm, iterations=2)
    sel = edge & ~lit_side & ~gap_rim
    edge_alt = [C(edge_fam, 0), C('leaf', 0), C('leaf_cool', 0), C('grass_cool', 0)]
    run = ndi.zoom(rng.integers(0, 4, (Hp // 3 + 2, Wp // 3 + 2)), 3, order=0)[:Hp, :Wp]
    code[sel] = np.array(edge_alt)[run[sel]]
    for y, x in zip(*np.nonzero(lit_side & ~gap_rim)):
        code[y, x] = lad.pick(max(lad.lo, _lum(int(code[y, x])) - 22), rng, 6)
    for y, x in zip(*np.nonzero(gap_rim & ~lit_side)):
        code[y, x] = C('leaf', 1) if (x + y) % 5 else C('leaf_cool', 1)
    return code, mask, v


NB_FLOOR = 51.0        # near-black (L 50 and under) only at the deepest point of a gap (W3-F2)
TUNE = dict(sep=0.95, a_lit=0.45, a_mid=0.15, big=(7, 11), capy=0.2, lo=0.5, d_mid=34.0, d_sh=70.0,
            sh_cap=8.0, litmarks=0.6, hl=0.8, nsib=5, lit_cap=20.0, pk_r=(3.0, 4.4), deep=0.42, sib=12, shrub_px=2000.0, mw_tree=1.0, mw_shrub=0.45)


def _leaf_blob(rx, ry, rng):
    """One leaf clump's footprint: three to five overlapping lobes about a centre, its rim stepped
    into leaf points (a texel taken out here and there on the top and the sides, never leaving a
    one-texel spur), about 2 rx across and 2 ry tall."""
    W, H = int(2 * rx + 3), int(2 * ry + 3)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    m = ((xx - cx) / (rx * 0.82)) ** 2 + ((yy - cy) / (ry * 0.82)) ** 2 <= 1.0
    for _ in range(int(rng.integers(3, 6))):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.35, 0.6)
        lx, ly = cx + math.cos(a) * rx * 0.45, cy + math.sin(a) * ry * 0.45
        m |= ((xx - lx) / (rx * r + 0.6)) ** 2 + ((yy - ly) / (ry * r + 0.6)) ** 2 <= 1.0
    edge = m & ~ndi.binary_erosion(m)
    ey, ex = np.nonzero(edge)
    for k in rng.permutation(len(ey))[: max(1, len(ey) // 5)]:
        m[ey[k], ex[k]] = False
    m = _spurs(m)
    return m


def _crown_light(S, masses, lift=0.0, low_band=0.0):
    """A value 0..1 per texel: each mass a dome lit from the upper left, the crown as one dome over
    them (the form shadow on the east and the foot); low_band darkens the crown's foot."""
    Hp, Wp = S.shape
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    ms = sorted(masses, key=lambda m: -m[1])
    owner = np.full((Hp, Wp), -1)
    for k, (cx, cy, rx, ry) in enumerate(ms):
        owner[(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.1) & S] = k
    miss = S & (owner < 0)
    if miss.any() and (owner >= 0).any():
        idx = ndi.distance_transform_edt(owner < 0, return_distances=False, return_indices=True)
        owner[miss] = owner[idx[0][miss], idx[1][miss]]
    Lv = np.array([-0.55, -0.68, 0.48])
    Lv = Lv / np.linalg.norm(Lv)
    Cc = np.array(ms, float)
    o = np.clip(owner, 0, None)
    mcx, mcy, mrx, mry = (Cc[o, i] for i in range(4))
    U = np.clip((xx - mcx) / mrx, -1, 1)
    V = np.clip((yy - mcy) / mry, -1, 1)
    lam = U * Lv[0] + V * Lv[1] + np.sqrt(np.clip(1 - U * U - V * V, 0, 1)) * Lv[2]
    ys, xs = np.nonzero(S)
    gx0, gy0 = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    grx, gry = (xs.max() - xs.min()) / 2 + 1, (ys.max() - ys.min()) / 2 + 1
    Ug, Vg = np.clip((xx - gx0) / grx, -1, 1), np.clip((yy - gy0) / gry, -1, 1)
    lamg = Ug * Lv[0] + Vg * Lv[1] + np.sqrt(np.clip(1 - Ug * Ug - Vg * Vg, 0, 1)) * Lv[2]
    lam = np.maximum(lam, TUNE['lamf'])
    v = np.clip(TUNE['lamw'] * lam + (1 - TUNE['lamw']) * lamg + TUNE['lvo'] + lift, 0, 1)
    if low_band:
        bh = max(4.0, low_band * (ys.max() - ys.min()))
        f = np.clip((yy - (ys.max() - bh)) / bh, 0, 1)
        v = v * (1 - 0.75 * f)
    return v, (gx0, gy0)


def _clump_size(shapes):
    """The clump diameters (min, max) a shape set stands for: trees 5 to 9, shrubs 4 to 7."""
    if shapes is None or shapes is CLUMPS:
        return (5, 9)
    if shapes is CLUMPS_S:
        return (5, 8)
    if shapes is NEEDLE_CLUMPS:
        return (4, 7)
    return (4, 7)


def _mass_fit(S, masses, rng):
    """The crown's masses: the given ones for a tree; for a shrub (a cover of many small circles) 2 to
    4 masses fitted to its shape (k-means on its texels), each an ellipse over its share."""
    ys, xs = np.nonzero(S)
    if masses and len(masses) <= 6:
        return [tuple(float(q) for q in m[:4]) for m in masses]
    k = int(np.clip(round(len(ys) / TUNE['shrub_px']), 1, 3))
    if k == 1:
        return [((xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0 - (ys.max() - ys.min()) * 0.08,
                 (xs.max() - xs.min()) / 2.0 + 3, (ys.max() - ys.min()) / 2.0 * 1.1 + 3)]
    pts = np.stack([xs, ys * 1.2], 1).astype(float)
    cen = pts[rng.choice(len(pts), size=k, replace=False)]
    for _ in range(12):
        lab = np.argmin(((pts[:, None, :] - cen[None]) ** 2).sum(-1), 1)
        cen = np.array([pts[lab == j].mean(0) if (lab == j).any() else cen[j] for j in range(k)])
    out = []
    for j in range(k):
        sel = lab == j
        if sel.sum() < 10:
            continue
        x_, y_ = xs[sel], ys[sel]
        out.append(((x_.min() + x_.max()) / 2.0, (y_.min() + y_.max()) / 2.0 - (y_.max() - y_.min()) * 0.08,
                    (x_.max() - x_.min()) / 2.0 * 1.15 + 3, (y_.max() - y_.min()) / 2.0 * 1.1 + 3))
    return out


def clump_crown(S: np.ndarray, masses, lad: Ladder, rng, *, lo: float, hi: float, shapes=None, gaps=(),
                low_band: float = 0.0, lift: float = 0.0, edge_fam: str = 'leaf_cool', glint_fam: str = 'grass_warm',
                density: float = 0.85, tips: bool = True, size=None, deep: float = 0.34, cap_l=None, **_old):
    """Paint a crown S at two scales, as the red tree in Eastward 12 at the same character height
    (round 3 of the audit, W3-F1 to F3; the coordinator's read of pass 4):

    - masses: each a dome lit from the upper left, its value falling from a lit cap through the mid
      to a core shade, with a reflected rim at its lower east; the masses sit in front of the ones
      below them, and the crown's own dome darkens the east and the foot;
    - on the lit upper west of a mass the clumps merge into one lit field 15 to 30 texels across
      (one value, its leaves sibling marks), its edge the clumps' own scalloped lobes, with only a
      few short gap marks inside; toward the shade the clumps stand apart (cap, body, a gap row under
      an overlapping edge), smaller (4 to 6 texels against 7 to 11 in the light) and closer in value;
    - between masses and under each overhang one large irregular dark pocket (8 to 20 texels), not a
      gap net or a seam; near-black only at its deepest texel in the shade;
    - the silhouette is the clumps' lobes (no one-texel spurs), closed in the leaf edge tone on the
      shaded sides and open on the lit upper west; sky gaps open to the outside.
    Returns (codes, mask, value)."""
    T_ = TUNE
    Hp, Wp = S.shape
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    S = ndi.binary_fill_holes(S)
    gapm = np.zeros((Hp, Wp), bool)
    for (gx, gy, grx, gry) in gaps:
        ang = np.arctan2(yy - gy, xx - gx)
        wob = 1 + 0.16 * np.sin(5 * ang + gx) + 0.08 * np.sin(9 * ang + gy)
        gapm |= ((xx - gx) / grx) ** 2 + ((yy - gy) / gry) ** 2 <= wob * wob
    S = S & ~gapm
    ys0, xs0 = np.nonzero(S)
    gx0, gy0 = (xs0.min() + xs0.max()) / 2, (ys0.min() + ys0.max()) / 2
    grx, gry = (xs0.max() - xs0.min()) / 2 + 1, (ys0.max() - ys0.min()) / 2 + 1
    Lv = np.array([-0.58, -0.66, 0.48])
    Lv = Lv / np.linalg.norm(Lv)

    def lamb(U, V):
        U, V = np.clip(U, -1, 1), np.clip(V, -1, 1)
        return U * Lv[0] + V * Lv[1] + np.sqrt(np.clip(1 - U * U - V * V, 0, 1)) * Lv[2]

    # the masses: the upper ones in front; each texel's mass and its light on that mass
    ms = sorted(_mass_fit(S, masses, rng), key=lambda m: -m[1])
    mown = np.full((Hp, Wp), -1)
    for k, (cx, cy, rx, ry) in enumerate(ms):
        ang = np.arctan2(yy - cy, xx - cx)
        wob = 1 + 0.07 * np.sin(3 * ang + k) + 0.05 * np.sin(5 * ang + 2 * k)
        mown[(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= wob * wob * 1.1) & ndi.binary_dilation(S, iterations=3)] = k
    miss = ndi.binary_dilation(S, iterations=3) & (mown < 0)
    if miss.any() and (mown >= 0).any():
        idx = ndi.distance_transform_edt(mown < 0, return_distances=False, return_indices=True)
        mown[miss] = mown[idx[0][miss], idx[1][miss]]
    M = np.array(ms, float)
    mo = np.clip(mown, 0, None)
    Um, Vm = (xx - M[mo, 0]) / M[mo, 2], (yy - M[mo, 1]) / M[mo, 3]
    rr = np.sqrt(Um * Um + Vm * Vm)
    lamg = lamb((xx - gx0) / grx, (yy - gy0) / gry)
    # -1 .. 1: the mass's own dome, with the crown's over it (a shrub's few masses lean on the crown's)
    mw = T_['mw_tree'] if (masses and len(masses) <= 6) else T_['mw_shrub']
    lam = mw * lamb(Um, Vm) + (1 - mw) * lamg
    glob = np.clip(0.5 + 0.5 * lamg + lift, 0, 1)                      # the crown's own dome
    if low_band:
        bh = max(4.0, low_band * (ys0.max() - ys0.min()))
        glob = glob * (1 - 0.55 * np.clip((yy - (ys0.max() - bh)) / bh, 0, 1))
    # the value: lit cap / mid / core shade / reflected rim on the mass, the crown's dome over it
    zone = np.where(lam > T_['a_lit'], 3, np.where(lam > T_['a_mid'], 2, 1))
    rim = (zone == 1) & (rr > 0.78) & (Um > 0.1) & (Vm > 0.1)
    zone = np.where(rim, 0, zone)                                      # 0: the reflected rim
    v = np.clip(0.35 * (0.5 + 0.5 * lam) + 0.65 * glob, 0, 1)
    # the clumps: larger in the light (7 to 11), smaller toward the shade and the silhouette (4 to 6)
    small, big = (size or (4, 6)), T_['big']
    if shapes is not None and shapes is not CLUMPS and shapes is not CLUMPS_S:
        big = (max(5, big[0] - 2), big[1] - 3)                         # shrubs: a size down
    inner = ndi.binary_erosion(S, iterations=2)
    if inner.sum() < 6:
        inner = S
    edist = ndi.distance_transform_edt(S)
    iy, ix = np.nonzero(inner)
    cand = rng.permutation(len(iy))
    cand = cand[np.argsort(iy[cand] // 3, kind='stable')]
    cl = []
    grid = {}
    for c_ in cand:
        yc, xc = iy[c_] + rng.uniform(-0.5, 0.5), ix[c_] + rng.uniform(-0.5, 0.5)
        f = float(np.clip((lam[iy[c_], ix[c_]] - T_['a_mid']) / max(0.05, T_['a_lit'] - T_['a_mid']), 0, 1))
        f *= float(np.clip(edist[iy[c_], ix[c_]] / 7.0, 0.35, 1))
        d = (small[0] + (big[0] - small[0]) * f) + rng.uniform(0, (small[1] - small[0]) + ((big[1] - big[0]) - (small[1] - small[0])) * f + 0.99)
        r = d / 2.0
        gk = (int(yc // 6), int(xc // 6))
        ok = True
        for gy_ in range(gk[0] - 2, gk[0] + 3):
            for gx_ in range(gk[1] - 2, gk[1] + 3):
                for j in grid.get((gy_, gx_), ()):
                    q = cl[j]
                    if math.hypot(q[0] - xc, (q[1] - yc) * 1.1) < (q[2] + r) * T_['sep']:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if not ok:
            continue
        grid.setdefault(gk, []).append(len(cl))
        cl.append([xc, yc, r * rng.uniform(0.98, 1.12), r * rng.uniform(0.88, 1.02)])
    order = sorted(range(len(cl)), key=lambda k: (-cl[k][1], rng.uniform()))
    own = np.full((Hp, Wp), -1)
    reach = ndi.binary_dilation(S, iterations=1) & ~gapm
    for k in order:
        xc, yc, rx, ry = cl[k][:4]
        m = _leaf_blob(rx, ry, rng)
        h, w = m.shape
        y0, x0 = int(round(yc)) - h // 2, int(round(xc)) - w // 2
        Y, X = np.nonzero(m)
        Y, X = Y + y0, X + x0
        ok = (Y >= 0) & (Y < Hp) & (X >= 0) & (X < Wp)
        Y, X = Y[ok], X[ok]
        ok = reach[Y, X]
        own[Y[ok], X[ok]] = k
    for k in range(len(cl)):
        mk = own == k
        if mk.any() and (mk.sum() < 6 or not ndi.binary_erosion(mk).any()):
            own[mk] = -1
    mask = _spurs(ndi.binary_fill_holes((own >= 0) | inner))
    own[~mask] = -1
    isc = own >= 0
    o = np.clip(own, 0, None)
    A = np.array([c[:4] for c in cl] or [[0.0, 0.0, 1.0, 1.0]])
    ccx, ccy, cry = A[o, 0], A[o, 1], A[o, 3]
    # each clump's zone and mass at its centre
    cz = np.array([int(zone[int(np.clip(round(c[1]), 0, Hp - 1)), int(np.clip(round(c[0]), 0, Wp - 1))]) for c in cl] or [1])
    cm = np.array([int(mo[int(np.clip(round(c[1]), 0, Hp - 1)), int(np.clip(round(c[0]), 0, Wp - 1))]) for c in cl] or [0])
    cg = np.array([float(glob[int(np.clip(round(c[1]), 0, Hp - 1)), int(np.clip(round(c[0]), 0, Wp - 1))]) for c in cl] or [0.5])
    P = np.pad(own, 3, constant_values=-2)

    def sh(dy, dx):
        return P[3 + dy:3 + dy + Hp, 3 + dx:3 + dx + Wp]

    # the edge between two clumps: a gap row on the one behind, under the front one's edge
    ovl = np.zeros((Hp, Wp), bool)
    for dy, dx in ((-1, 0), (-1, -1), (-1, 1), (0, -1)):
        nb = sh(dy, dx)
        ovl |= isc & (nb >= 0) & (nb != own) & (A[np.clip(nb, 0, None), 1] < ccy - 0.5)
    # ... merged away inside a lit field: only a few short marks stay (every third lit clump, 3 to 5
    # texels under its front neighbour)
    zc = cz[o]
    lit_c = isc & (zc == 3)
    keep_mark = np.zeros(len(cl), bool)
    keep_mark[rng.random(len(cl)) < T_['litmarks']] = True
    ovl_lit = ovl & lit_c
    if ovl_lit.any():
        lab_, n_ = ndi.label(ovl_lit)
        for i, sl in enumerate(ndi.find_objects(lab_)):
            comp = lab_[sl] == i + 1
            k_ = int(np.bincount(o[sl][comp]).argmax())
            if not keep_mark[k_]:
                ovl[sl][comp] = False
            else:
                ys_, xs_ = np.nonzero(comp)
                far = np.abs(xs_ - xs_.mean()) > rng.uniform(1.5, 2.6)
                ovl[sl][ys_[far], xs_[far]] = False
    up = (yy - ccy) < T_['capy'] * cry
    capm = np.zeros((Hp, Wp), bool)
    for dy, dx in ((-1, 0), (0, -1), (-2, 0), (-1, -1), (-3, 0), (-2, -1), (-1, -2)):
        capm |= sh(dy, dx) != own
    capm1 = np.zeros((Hp, Wp), bool)
    for dy, dx in ((-1, 0), (0, -1), (-2, 0), (-1, -1)):
        capm1 |= sh(dy, dx) != own
    # a lit-field clump keeps its shape by a lit crescent (a tone up), not by a gap round it
    cap = isc & up & ((capm & (zc == 2)) | (capm1 & (zc == 3)))
    cap &= ~ovl
    body = isc & ~cap & ~ovl

    # the values, per mass: L_hi lit field, the mid, the core shade, the rim, the pocket
    def levels(g):
        Lh = lo + T_['lo'] * (hi - lo) + (hi - lo) * (1 - T_['lo']) * g
        return dict(hi=Lh, mid=Lh - T_['d_mid'], sh=max(NB_FLOOR + 16, Lh - T_['d_sh']),
                    rim=max(NB_FLOOR + 24, Lh - T_['d_sh'] + 12), pk=max(NB_FLOOR + 3, Lh - T_['d_sh'] - 22))

    def sibs(c0, n, spread):
        L0 = _lum(c0)
        keys_ = {_key(c0)}
        out = [c0]
        cand_ = sorted(((abs(it[0] - L0) + rng.uniform(0, 2.5), it[1]) for it in lad.items
                        if abs(it[0] - L0) <= spread and (it[0] > NB_FLOOR or _lum(c0) <= NB_FLOOR)),
                       key=lambda q: q[0])
        for _, c_ in cand_:
            if len(out) > n:
                break
            if _key(c_) not in keys_:
                keys_.add(_key(c_))
                out.append(c_)
        base_ = list(out)
        while len(out) < n + 1:
            out.append(base_[len(out) % len(base_)])
        return out

    pal = {}

    def palette(L):
        q = int(round(L / 3.0))
        if q not in pal:
            pal[q] = sibs(lad.pick(q * 3.0, rng, 3), T_['nsib'] - 1, T_['sib'])
        return pal[q]

    # the clumps' values: a lit-field clump takes its mass's lit value (so neighbours merge); a
    # mid clump a lit cap over a mid body; a shade clump a low cap over the core shade; a rim clump
    # the reflected rim
    cval = []
    for k in range(len(cl)):
        Lv_ = levels(cg[k])
        z = cz[k]
        if z == 3:
            cval.append((Lv_['hi'] + T_['lit_cap'], Lv_['hi'], Lv_['mid'] - 6))
        elif z == 2:
            cval.append((Lv_['hi'] - 4, Lv_['mid'], Lv_['sh']))
        elif z == 1:
            cval.append((Lv_['sh'] + T_['sh_cap'], Lv_['sh'], Lv_['sh'] - 12))
        else:
            cval.append((Lv_['rim'] + 6, Lv_['rim'], Lv_['sh'] - 6))
    # the leaves: 2 x 2 marks in offset rows, each a sibling unlike the marks round it
    gr_ = yy // 2
    gc_ = (xx + (gr_ % 2)) // 2
    nr_, nc_ = gr_.max() + 2, gc_.max() + 2
    g4 = np.zeros((nr_, nc_), int)
    for i in range(nr_):
        for j in range(nc_):
            ab = (j, j + 1) if i % 2 else (j - 1, j)
            ban = {g4[i, j - 1] if j else -1} | {g4[i - 1, q] if i and 0 <= q < nc_ else -1 for q in ab}
            g4[i, j] = int(rng.choice([q for q in range(T_['nsib']) if q not in ban]))
    mk_ = g4[gr_, gc_]
    code = np.full((Hp, Wp), -1, np.int64)
    # the lit fields: one value per mass (rounded), so the clumps merge
    for k in range(len(cl)):
        sel = own == k
        if not sel.any():
            continue
        cv, bv, gv = cval[k]
        pc, pb, pg = palette(cv), palette(bv), palette(gv)
        s_cap, s_body, s_ovl = sel & cap, sel & body, sel & ovl
        code[s_cap] = np.array(pc)[mk_[s_cap]]
        code[s_body] = np.array(pb)[mk_[s_body]]
        code[s_ovl] = np.array(pg)[mk_[s_ovl] % 2]
    # the lit field's brightest clumps: a few at the top west of each mass get a crescent a tone up
    for k in range(len(cl)):
        if cz[k] != 3 or rng.random() > T_['hl']:
            continue
        sel = (own == k) & capm & (lam > T_['a_lit'] + 0.12)
        if sel.sum() >= 4:
            code[sel] = np.array(palette(cval[k][0] + 13))[mk_[sel]]
    # between clumps: the mid in the light, the shade elsewhere
    bare = mask & ~isc
    if bare.any():
        for y, x in zip(*np.nonzero(bare)):
            Lv_ = levels(float(glob[y, x]))
            L_ = Lv_['hi'] if zone[y, x] == 3 else (Lv_['sh'] - 6 if zone[y, x] == 2 else Lv_['sh'] - 14)
            code[y, x] = palette(max(NB_FLOOR + 3, L_))[mk_[y, x]]
    # the pockets: between masses and under each overhang one large irregular dark pocket, set
    # where a mass in front meets the one behind it, in the shade of the one behind
    inner3 = ndi.binary_erosion(mask, iterations=3)
    pk_all = np.zeros((Hp, Wp), bool)
    for k in range(len(ms)):
        front = (mown == k) & mask
        behind = mask & (mown >= 0) & (mown < k)
        if not front.any() or not behind.any():
            continue
        band = behind & ndi.binary_dilation(front, iterations=3) & (lam < T_['a_lit'])
        ys_, xs_ = np.nonzero(band & inner3)
        if not len(ys_):
            continue
        npk = int(np.clip(round(len(ys_) / 90.0), 1, 3))
        taken = []
        for j in rng.permutation(len(ys_)):
            if len(taken) >= npk:
                break
            y, x = int(ys_[j]), int(xs_[j])
            if any(abs(x - tx) < 14 for (ty, tx) in taken):
                continue
            taken.append((y, x))
            ar = rng.uniform(*T_['pk_r'])
            ang = np.arctan2(yy - y, xx - x)
            wob = 1 + 0.28 * np.sin(3 * ang + rng.uniform(0, 6.3)) + 0.16 * np.sin(5 * ang + rng.uniform(0, 6.3))
            blob = (((xx - x) / (ar * 1.35)) ** 2 + ((yy - y) / ar) ** 2 <= wob * wob) & mask & ~front
            blob |= ndi.binary_dilation(blob, iterations=1) & front & ~ndi.binary_erosion(front, iterations=1) & (yy >= y - 1)
            pk_all |= blob & ndi.binary_erosion(mask, iterations=2)
    if pk_all.any():
        dist = ndi.distance_transform_edt(pk_all)
        for y, x in zip(*np.nonzero(pk_all)):
            Lv_ = levels(float(glob[y, x]))
            code[y, x] = palette(max(NB_FLOOR + 3, Lv_['pk'] - (8 if dist[y, x] >= 2 else 0)))[mk_[y, x] % 2]
        lab_, n_ = ndi.label(pk_all)
        for i, sl in enumerate(ndi.find_objects(lab_)):
            dd = np.where(lab_[sl] == i + 1, dist[sl], 0)
            if dd.max() < 2:
                continue
            y, x = np.unravel_index(int(np.argmax(dd)), dd.shape)
            y, x = y + sl[0].start, x + sl[1].start
            if glob[y, x] < T_['deep'] and inner3[y, x]:
                bc = C('leaf_cool', 0) if rng.random() < 0.5 else C('leaf', 0)
                code[y, x] = bc
                if dd.max() >= 2.5 and x + 1 < Wp and dist[y, x + 1] >= 2:
                    code[y, x + 1] = bc
    # glints: a yellow-green pair on a few lit-field texels of the upper west
    litf = isc & (zc == 3) & (xx < gx0) & (yy < gy0) & ndi.binary_erosion(mask, iterations=2)
    ys_, xs_ = np.nonzero(litf)
    for k in rng.permutation(len(ys_))[: max(1, int(len(ys_) / 160))]:
        y, x = int(ys_[k]), int(xs_[k])
        if x + 1 < Wp and litf[y, x + 1]:
            code[y, x] = code[y, x + 1] = C(glint_fam, 5)
    code[~mask] = -1
    # the outline: the leaf edge tone on the shaded sides, open on the lit upper west
    edge = mask & ~ndi.binary_erosion(mask)
    Pm = np.pad(mask, 1)
    open_ul = (~Pm[:-2, 1:-1] | ~Pm[1:-1, :-2])
    lit_side = edge & open_ul & (zone >= 2)
    gap_rim = edge & ndi.binary_dilation(gapm, iterations=2)
    sel = edge & ~lit_side & ~gap_rim
    run = ndi.zoom(rng.integers(0, 2, (Hp // 3 + 2, Wp // 3 + 2)), 3, order=0)[:Hp, :Wp]
    code[sel] = np.where(run[sel] > 0, C(edge_fam, 1), C('leaf', 1))
    code[sel & (glob < 0.3)] = C(edge_fam, 0)
    code[gap_rim & ~lit_side] = C('leaf', 1)
    _clean(code, mask, 2)
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
    'oak': (('timber_cool', 'timber', 'earth_warm', 'earth', 'earth_cool'), {'timber_cool': 2.0}, 92, ('timber_cool', 0), 34),
    'pine': (('timber_warm', 'timber', 'clay', 'fox'), {'timber_warm': 2.0, 'fox': 0.5}, 96, ('timber_cool', 0), 34),
    'beech': (('stone', 'stone_cool', 'stone_warm', 'ashlar', 'ashlar_warm'), {'stone': 2.0}, 116, ('stone_cool', 0), 50),
    'birch': (('plaster', 'plaster_warm', 'stone_warm'), {'plaster': 2.0, 'stone_warm': 0.4}, 176, ('stone_cool', 1), 62),
    'sapling': (('timber_cool', 'timber', 'earth_warm'), {'timber_cool': 2.0}, 92, ('timber_cool', 0), 30),
    'willow': (('timber_cool', 'earth', 'earth_warm', 'earth_cool'), {'timber_cool': 2.0}, 88, ('timber_cool', 0), 34),
}


def _hollow(code, body, xx, yy, cx, cy, rx, ry, rng):
    """A hollow with depth (W2-T6): a lip 2 to 3 texels thick lit only on its lower and west edges
    (timber 4), dark on its upper and east (timber 1); inside the top of the opening the far inner
    wall as a band 2 to 3 texels deep (timber 3 to 2) falling to near-black at the back; two eyes
    set inside the dark."""
    o = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    jag = (ndi.gaussian_filter(rng.random(body.shape), 1.2) - 0.5) * 0.5
    open_ = body & (o + jag <= 1.0)
    lip = body & ~open_ & (o + jag <= 1.0 + 2.6 / max(rx, ry) * 2.2)
    dx_, dy_ = (xx - cx) / rx, (yy - cy) / ry
    code[lip] = C('timber_cool', 1)                                  # the upper and east lip: dark
    lit_lip = lip & ((dy_ > 0.3) | (dx_ < -0.45)) & ~((dx_ > 0.5) & (dy_ < 0.6))
    code[lit_lip] = C('timber', 4)
    code[lip & (dy_ > 0.75) & (dx_ < 0.4)] = C('timber_warm', 4)
    code[lip & (dy_ > 0.3) & (dx_ >= 0.4)] = C('timber', 3)          # the lower lip turning away east
    # the opening (W3-T2): the far inner wall under the upper lip, 3 to 4 rows graded timber 3 to 1;
    # the floor lit a tone just inside the lower west lip; the interior in three tones falling to
    # near-black at the back, where the eyes are
    dark0 = C('soot', 0) if 'soot' in FI else C('timber_cool', 0)
    back = ((xx - cx - 0.1 * rx) / rx) ** 2 + ((yy - cy - 0.2 * ry) / ry) ** 2
    code[open_] = C('timber_cool', 1)
    code[open_ & (back < 0.55)] = C('timber_cool', 0)
    code[open_ & (back < 0.22)] = dark0
    dtop = np.zeros(body.shape, int)
    for x in np.nonzero(open_.any(0))[0]:
        col = np.nonzero(open_[:, x])[0]
        dtop[col, x] = col - col.min()
    wall = [(0, C('timber_cool', 3)), (1, C('timber_cool', 3)), (2, C('timber_cool', 2)), (3, C('timber_cool', 1))]
    for d_, c_ in wall:
        sel = open_ & (dtop == d_)
        code[sel] = c_
        code[sel & (dx_ > 0.35) & (d_ < 3)] = C('timber_cool', max(1, 2 - d_ // 2))
    dbot = np.zeros(body.shape, int)
    for x in np.nonzero(open_.any(0))[0]:
        col = np.nonzero(open_[:, x])[0]
        dbot[col, x] = col.max() - col
    code[open_ & (dbot <= 1) & (dx_ < 0.1) & (dy_ > 0.2)] = C('timber', 2)
    # the eyes, inside the dark
    ey, ex = int(round(cy + ry * 0.2)), int(round(cx + rx * 0.1))
    for dx in (-2, 2):
        if open_[ey, ex + dx] and open_[ey, ex + dx + (1 if dx > 0 else -1)]:
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


def pine_tiers(S, rng):
    """A pine's tiers (W2-T5): spaced 8 to 20 texels (some overlapping), each as wide as the cone at its
    foot give or take a sixth, the top few tilted a few texels to one side; 2 to 4 branch clumps
    pushed 6 to 12 texels past the cone line; 1 or 2 tiers notched (one side cut back).
    [(cx, cy, rx, ry, (west, east))], top first."""
    ys, xs = np.nonzero(S)
    yt, yb = ys.min(), ys.max()
    cxm = (xs.min() + xs.max()) / 2.0
    hw = (xs.max() - xs.min()) / 2.0
    H = yb - yt
    feet = []
    y = yt + rng.uniform(9, 12)
    while y < yb - 4:
        feet.append(y)
        y += rng.uniform(8, 20) * (0.75 if y < yt + 0.3 * H else 1.0)
    feet.append(yb)
    tilt = rng.choice((-1, 1)) * rng.uniform(3, 5)
    out = []
    prev = yt - 2
    for k, fy in enumerate(feet):
        f = (fy - yt) / H
        rx = max(4.0, hw * (0.12 + 0.88 * f) * rng.uniform(0.86, 1.14))
        th = max(8.0, fy - prev + rng.uniform(4, 9))                  # a skirt reaching over the tier above
        cx = cxm + tilt * (1 - f) ** 2 + rng.uniform(-1.2, 1.2)
        out.append((cx, fy - th * 0.75 / 2.0, rx, th / 2.0, (1.0, 1.0)))
        prev = fy
    # notches: one or two lower tiers cut back on one side
    for k in rng.choice(np.arange(2, max(3, len(out) - 1)), size=min(2, max(1, len(out) - 3)), replace=False):
        cx, cy, rx, ry, _ = out[int(k)]
        out[int(k)] = (cx, cy, rx, ry, (0.72, 1.0) if rng.random() < 0.5 else (1.0, 0.72))
    # branch clumps past the cone line, at a tier's foot
    for _ in range(int(rng.integers(2, 5))):
        k = int(rng.integers(max(1, len(out) // 3), len(out) - 1))
        cx, cy, rx, ry, (aw_, ae_) = out[k]
        sd = rng.choice((-1, 1))
        brx, bry = rng.uniform(6, 9), rng.uniform(4, 6)
        foot_ = cy + ry * 0.75
        reach_ = rx * (ae_ if sd > 0 else aw_)
        out.append((cx + sd * (reach_ + rng.uniform(6, 12) - brx * 1.3), foot_ - bry * 0.75 + 1, brx, bry, (1.0, 1.0)))
    out.sort(key=lambda c: c[1])
    return out


def pine_crown(S, tiers, lad, rng, lo, hi, fams_=('leaf_cool', 'leaf'), wts_=None, pine_kw=None):
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
    for k, tier in enumerate(tiers):
        cx, cy, rx, ry = tier[:4]
        aw, ae = tier[4] if len(tier) > 4 else (1.0, 1.0)
        ytop = cy - ry * 1.25
        ybot = cy + ry * 0.75
        f = np.clip((yy - ytop) / max(1, ybot - ytop), 0, 1)
        half = rx * (0.22 + 0.78 * f ** 0.85) + 1.2 * np.sin(yy * 0.9 + k)
        tm = (xx - cx <= half * ae) & (cx - xx <= half * aw) & (yy >= ytop) & (yy <= ybot)
        if not tm.any():
            continue
        # the tier's foot: needle tips hanging every 4 to 6 texels
        x = cx - rx * aw + rng.uniform(0, 3)
        while x < cx + rx * ae - 1:
            L_ = int(rng.integers(2, 5))
            for j in range(1, L_ + 1):
                for dx in ((0, 1) if j < L_ else (0,)):
                    Y, X = int(ybot) + j, int(x) + dx
                    if 0 <= Y < Hp and 0 <= X < Wp:
                        tm[Y, X] = True
            x += rng.uniform(4, 6.5)
        cl = [(cx - rx * 0.3, cy - ry * 0.2, rx * 1.1, ry * 1.4)]
        tc, tmask, tv = _clump_crown_p3(tm, cl, lad, rng, lo=lo, hi=hi, shapes=NEEDLE_CLUMPS, tips=False, pockets=0.0,
                                    edge_fam='leaf_cool', glint_fam='leaf_warm', fams=fams_, fam_w=wts_,
                                    ufloor=lo + 4, ccon=(11.0, 22.0, 14.0), **(pine_kw or {}))
        # the underside: the tier's lowest 2 to 3 rows (and its tips) in the deep shade
        rows = np.arange(Hp)[:, None]
        under = tmask & (rows >= ybot - 2)
        ud = [lad.pick(lo - 4, rng, 4), lad.pick(lo + 2, rng, 4), lad.pick(lo - 1, rng, 4)]
        run_ = ndi.zoom(rng.integers(0, 3, (Hp // 2 + 2, Wp // 3 + 2)), (2, 3), order=0)[:Hp, :Wp]
        tc[under] = np.array(ud)[run_[under]]
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
            sd_c = [lad.pick(lo + 6, rng, 4), lad.pick(lo + 10, rng, 4)]
            run_ = ndi.zoom(rng.integers(0, 2, (Hp // 2 + 2, Wp // 3 + 2)), (2, 3), order=0)[:Hp, :Wp]
            code[sh] = np.array(sd_c)[run_[sh]]
        prev = tmask.copy()
    mask = _spurs(mask)
    filled = ndi.binary_fill_holes(mask)
    hole = filled & ~mask
    if hole.any():
        code[hole] = lad.pick(lo + 2, rng, 6)
    mask = filled
    # a branch clump standing clear of the cone hangs on a branch (2 texels, timber 1 to 2) run back
    # into its tier (W3-T1)
    lab, n = ndi.label(mask)
    if n > 1:
        sizes = ndi.sum(mask, lab, range(1, n + 1))
        main = 1 + int(np.argmax(sizes))
        axis = (np.nonzero(mask.any(0))[0].min() + np.nonzero(mask.any(0))[0].max()) / 2.0
        for k in range(1, n + 1):
            if k == main:
                continue
            ys_, xs_ = np.nonzero(lab == k)
            if len(ys_) < 6:
                mask[lab == k] = False
                continue
            y, x = int(ys_.max()) - 1, float(xs_.mean())
            sd = 1 if axis > x else -1
            X = int(round(x))
            for _ in range(60):
                X += sd
                if not (0 <= X < Wp):
                    break
                for dy, c_ in ((0, C('timber', 2)), (1, C('timber', 1))):
                    if 0 <= y + dy < Hp and not (lab[y + dy, X] == main):
                        code[y + dy, X] = c_
                        mask[y + dy, X] = True
                if lab[y, X] == main or lab[min(Hp - 1, y + 1), X] == main:
                    break
                if (X - int(round(x))) % 4 == 0:
                    y += 0 if rng.random() < 0.6 else 1
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
    # the stem's light (pass 4, the dotted-line check): a lit west column, a body and a shaded east
    # side, each one colour along the stem with a few 2-texel bark marks, not random per texel
    lit_c, mid_c, sh_c = lad.pick(base + spread * 0.6, rng, 4), lad.pick(base + spread * 0.1, rng, 4), \
        lad.pick(base - spread * 0.35, rng, 4)
    for y in range(length):
        x0, x1 = cxs[y]
        for x in range(x0, x1):
            u = (x - x0) / max(1, x1 - x0 - 1)
            code[y, x] = lit_c if u < 0.3 else (mid_c if u < 0.7 else sh_c)
    for y in range(int(rng.integers(3, 6)), length - 4, int(rng.integers(5, 8))):
        x0, x1 = cxs[y]
        if x1 - x0 >= 3:
            code[y:y + 2, x0 + 1] = lad.pick(_lum(int(mid_c)) - 12, rng, 4)
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
    for y in range(length):                                          # the east edge unbroken
        code[y, cxs[y][1] - 1] = C(*crack)
    code[length - 1, :][body[length - 1, :]] = C(*crack)            # the contact line
    return code, body, (int(round(sum(cxs[-1]) / 2)), length)


# ------------------------------------------------------------------------------------------------
# the willow (W-T7)
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# shrubs (W-B1 to W-B3)
# ------------------------------------------------------------------------------------------------
# per kind, the clump size and spacing chosen side by side at 4x and by the detail bar (pass 3)
SHRUB_KW = {
    'bush': dict(shapes=CLUMPS_XS), 'bush_b': dict(density=0.95), 'bush_c': dict(density=0.8, sib_spread=7),
    'bramble': dict(shapes=CLUMPS_XS, density=0.75), 'bramble_b': dict(shapes=CLUMPS_XS, density=0.75),
}
HOLLY_KW = {'holly': dict(shapes=CLUMPS_XS, cap_l=(88.0, 136.0)), 'holly_b': dict(cap_l=(88.0, 140.0))}
TREE_KW = {'beech': dict(shapes=CLUMPS_S), 'birch': dict(sib_spread=7), 'hollow_tree': dict(pockets=1.0),
           'sapling': dict(shapes=CLUMPS_XS)}
WILLOW_KW = dict(density=0.75)


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
    if base_kind == 'holly':
        # the foot closed along the ground: no notch at the centre of the base (W2-B2)
        ys_, xs_ = np.nonzero(S)
        y_lo = int(ys_.max() - 0.35 * (ys_.max() - ys_.min()))
        for y in range(y_lo, ys_.max() + 1):
            row = np.nonzero(S[y])[0]
            if len(row):
                S[y, row.min():row.max() + 1] = True
    clumps = clump_cover(S, look.get('clump', 6.0) * d * 0.7, rng)
    if base_kind == 'holly':
        code, mask, v = holly(S, clumps, lad, rng, lo, hi, kind)
    else:
        code, mask, v = clump_crown(S, clumps, lad, rng, lo=lo, hi=hi, fams=fams, fam_w=wts,
                                    low_band=0.22, lift=0.1 if base_kind != 'bramble' else 0.18,
                                    edge_fam='leaf' if base_kind == 'bramble' else 'leaf_cool',
                                    **{'shapes': CLUMPS_S, **SHRUB_KW.get(kind, {})})
    # the foot: the lowest leaves in the deep band where it meets the ground, flat (no legs), and a
    # contact line under them
    ysS = np.nonzero(S.any(1))[0]
    yb = int(ysS.max())
    mask[yb + 2:] = False                                          # nothing hangs below the foot
    code[~mask] = -1
    # the contact: each column's lowest texel in the dark underside (1 to 2 texels, uneven), not a row
    for x in np.nonzero(mask.any(0))[0]:
        y = int(np.nonzero(mask[:, x])[0].max())
        code[y, x] = C('leaf_cool', 0) if (x * 7 + y) % 5 else C('leaf', 1)
    if base_kind == 'bramble':
        code, mask = bramble_canes(code, mask, rng, kind)
    ys, xs = np.nonzero(mask)
    return _crop(np.where(mask, code, -1), ((xs.min() + xs.max() + 1) / 2.0, ys.max() + 1))


def _holly_leaves(seed=91, n=36):
    """Holly leaves as clumps (W2-B3): 5 to 7 texels wide, a wavy rim with notches between the
    points; parts as _clump_shapes gives them."""
    out = []
    for m, cres, tip, body2, under in _clump_shapes(seed=seed, n=n, wr=(5, 8), hf=(0.6, 0.8)):
        m = m.copy()
        edge = m & ~ndi.binary_erosion(m)
        ey, ex = np.nonzero(edge)
        for k in range(len(ey)):
            if (ex[k] * 2 + ey[k]) % 4 == 0 and 0 < ey[k] < m.shape[0] - 2:
                m[ey[k], ex[k]] = False                            # a notch between two points
        out.append((m, cres & m, tip & m, body2 & m, under & m))
    return out


HOLLY = _holly_leaves()


def holly(S, clumps, lad, rng, lo, hi, kind):
    """Holly (W2-B3): glossy dark leaves (leaf cool 1 to 3) built as clumps; each spine a 2-texel point
    grown edge-on from a leaf's edge every 3 to 5 texels round the silhouette; one leaf in four with a
    hard glint (tone 5) on its upper-left lobe; berries in clusters of 3 to 5, each arranged its own
    way, each berry with a glint, at the leaf axils; the foot the mass's own dark underside."""
    code, mask, v = clump_crown(S, clumps, lad, rng, lo=lo, hi=hi, tips=False, fams=('leaf_cool', 'leaf'),
                                fam_w={'leaf_cool': 2.0}, glint_fam='leaf_cool', edge_fam='leaf_cool', ufloor=lo + 6,
                                lift=0.12, low_band=0.2, **{'shapes': HOLLY, **HOLLY_KW.get(kind, {})})
    Hp, Wp = mask.shape
    # the leaves (W3-B3): distinct spiky ovals 5 to 7 texels long at a few angles, each with a lit
    # midrib, a darker lower edge and a point at each end; more of them in the light
    inner_l = ndi.binary_erosion(mask, iterations=3)
    yy_l, xx_l = np.mgrid[0:Hp, 0:Wp]
    ys, xs = np.nonzero(inner_l)
    placed = []
    want = int(inner_l.sum() / 75)
    for k in rng.permutation(len(ys)):
        if len(placed) >= want:
            break
        y, x = int(ys[k]), int(xs[k])
        if v[y, x] < 0.4 or rng.random() > 0.2 + 0.8 * float(v[y, x]):
            continue
        if any(abs(y - py) < 7 and abs(x - px) < 8 for (py, px) in placed):
            continue
        placed.append((y, x))
        L_ = rng.uniform(2.6, 3.6)
        a_ = float(rng.choice((0.0, 0.46, -0.46)))
        ca, sa = math.cos(a_), math.sin(a_)
        Lc = _lum(int(code[y, x])) if code[y, x] >= 0 else lo + 30
        body_c = lad.pick(max(NB_FLOOR + 14, Lc), rng, 4)
        dark_c = lad.pick(max(NB_FLOOR + 3, Lc - 20), rng, 5)
        rib_c = lad.pick(Lc + 16, rng, 5)
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                Y, X = y + dy, x + dx
                if not (0 <= Y < Hp and 0 <= X < Wp and mask[Y, X]):
                    continue
                u_ = dx * ca + dy * sa
                w_ = -dx * sa + dy * ca
                q = (u_ / L_) ** 2 + (w_ / 1.45) ** 2
                if q <= 1.0:
                    code[Y, X] = dark_c if (w_ > 0.6 and q > 0.35) else body_c
                    if abs(w_) < 0.5 and abs(u_) < L_ - 1.2:
                        code[Y, X] = rib_c
        for sgn in (-1, 1):                                          # the points at each end
            X, Y = int(round(x + sgn * (L_ + 0.6) * ca)), int(round(y + sgn * (L_ + 0.6) * sa))
            if 0 <= Y < Hp and 0 <= X < Wp and mask[Y, X]:
                code[Y, X] = body_c
        _clean(code, mask & (np.abs(yy_l - y) <= 5) & (np.abs(xx_l - x) <= 6), 1)
    ybot = np.nonzero(mask.any(1))[0].max()
    # spines: a 2-texel point grown from the edge (each texel edge-joined to the last)
    gy_, gx_ = np.gradient(ndi.gaussian_filter(mask.astype(float), 1.5))
    edge = mask & ~ndi.binary_erosion(mask)
    ys, xs = np.nonzero(edge)
    taken = []
    for k in rng.permutation(len(ys)):
        y, x = int(ys[k]), int(xs[k])
        if y >= ybot - 3:
            continue
        gap = rng.uniform(3, 5)
        if any((y - ty) ** 2 + (x - tx) ** 2 < gap * gap for (ty, tx) in taken):
            continue
        nx_, ny_ = -gx_[y, x], -gy_[y, x]
        if abs(nx_) >= abs(ny_):
            d1 = (0, 1 if nx_ > 0 else -1)
        else:
            d1 = (1 if ny_ > 0 else -1, 0)
        Y1, X1 = y + d1[0], x + d1[1]
        if not (0 <= Y1 < Hp and 0 <= X1 < Wp) or mask[Y1, X1]:
            continue
        # the second texel: straight on, or turned toward the diagonal (still edge-joined to the first)
        if rng.random() < 0.5:
            d2 = d1
        else:
            d2 = (0, 1 if nx_ > 0 else -1) if d1[1] == 0 else (1 if ny_ > 0 else -1, 0)
        Y2, X2 = Y1 + d2[0], X1 + d2[1]
        if not (0 <= Y2 < Hp and 0 <= X2 < Wp):
            continue
        taken.append((y, x))
        base_c = int(code[y, x])
        code[Y1, X1] = base_c
        code[Y2, X2] = C('leaf_cool', 1) if _lum(base_c) > 70 else C('leaf_cool', 2)
        mask[Y1, X1] = mask[Y2, X2] = True
    # glints (W3-B3): one leaf in four, 2 texels set against its lit upper-left edge (where the leaf
    # above or west of it is darker), never a lone speck
    Lm = np.zeros(code.shape)
    okc = code >= 0
    Lm[okc] = np.array([_lum(int(c)) for c in code[okc]])
    P_ = np.pad(Lm, 1, constant_values=255)
    rim_lit = mask & (v > 0.45) & ndi.binary_erosion(mask, iterations=2) & (Lm >= 85) & \
        ((P_[:-2, 1:-1] < Lm - 15) | (P_[1:-1, :-2] < Lm - 15))
    ys, xs = np.nonzero(rim_lit)
    placed = []
    want = max(3, int(mask.sum() / (4 * 32)))
    for k in rng.permutation(len(ys)):
        if len(placed) >= want:
            break
        y, x = int(ys[k]), int(xs[k])
        if x + 1 >= Wp or not rim_lit[y, x + 1] or any(abs(y - py) < 6 and abs(x - px) < 7 for (py, px) in placed):
            continue
        g_ = C('leaf_cool', 5) if rng.random() < 0.6 else C('grass_cool', 5)
        code[y, x] = code[y, x + 1] = g_
        placed.append((y, x))
    # berries at the axils: the darker places between leaves, mid-crown; 3 to 5 a cluster, each
    # cluster its own arrangement
    arrangements = [
        [(0, 0), (0, 2), (2, 1)], [(0, 0), (2, 0), (1, 2)], [(0, 1), (2, 0), (2, 2)],
        [(0, 0), (0, 2), (2, 1), (1, 3)], [(0, 1), (1, -1), (2, 1), (1, 3)], [(0, 0), (2, 0), (1, 2), (3, 2)],
        [(0, 1), (2, 0), (2, 2), (-1, 3), (1, 4)], [(0, 0), (0, 2), (2, -1), (2, 1), (2, 3)],
    ]
    rng.shuffle(arrangements)
    inner = ndi.binary_erosion(mask, iterations=4)
    ys, xs = np.nonzero(inner & (v < 0.62))
    nb = 5 if kind == 'holly' else 6
    placed = []
    for k in rng.permutation(len(ys)):
        if len(placed) >= nb:
            break
        y, x = int(ys[k]), int(xs[k])
        if any(abs(y - py) < 8 and abs(x - px) < 9 for (py, px) in placed):
            continue
        placed.append((y, x))
        arr = arrangements[len(placed) % len(arrangements)]
        for j, (dy, dx) in enumerate(arr):
            Y, X = y + dy, x + dx
            if 0 <= Y < Hp - 1 and 0 <= X < Wp - 1:
                code[Y:Y + 2, X:X + 2] = C('berry', 3) if (j + len(placed)) % 3 else C('berry', 2)
                code[Y + 1, X:X + 2] = C('berry', 2)                        # its shade, a tone down
                code[Y, X] = C('berry', 5)
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
    # canes (W2-B2): 3 to 5 of uneven curvature, leaving the mass at different heights and drooping
    # back to the ground; 2 texels thick in the berry ramp, a lit top texel and a dark one under it,
    # a thorn hook every 4 to 6 texels; one or two pass behind leaf clumps on their way out
    behind = set(rng.choice(n, size=min(n, int(rng.integers(1, 3))), replace=False).tolist())
    for k in range(n):
        side = -1 if k % 2 == 0 else 1
        if k == n - 1 and n % 2 == 1:
            side = -1 if rng.random() < 0.5 else 1
        f0 = rng.uniform(0.15, 0.42)
        sx = x0 + (x1 - x0) * (0.5 + side * f0)
        col = np.nonzero(inside0[:, int(np.clip(sx, 0, W2 - 1))])[0]
        top_ = col.min() if len(col) else yt
        sy = top_ + (yb - top_) * rng.uniform(0.15, 0.6)               # leaves at different heights
        ex = (x0 - rng.uniform(-2, 13)) if side < 0 else (x1 + rng.uniform(-2, 13))
        ey = yb - rng.uniform(0, 2)
        high = rng.random() < 0.5                                   # over the top, or out of the flank
        peak = (top_ - rng.uniform(3, 9)) if high else (sy - rng.uniform(0, 4))
        c1 = (sx + (ex - sx) * rng.uniform(0.05, 0.35), peak - rng.uniform(0, 4))
        c2 = (sx + (ex - sx) * rng.uniform(0.7, 1.15), peak + (ey - peak) * rng.uniform(0.05, 0.5))
        pts = []
        for s_ in np.linspace(0, 1, 120):
            px = (1 - s_) ** 3 * sx + 3 * (1 - s_) ** 2 * s_ * c1[0] + 3 * (1 - s_) * s_ ** 2 * c2[0] + s_ ** 3 * ex
            py = (1 - s_) ** 3 * sy + 3 * (1 - s_) ** 2 * s_ * c1[1] + 3 * (1 - s_) * s_ ** 2 * c2[1] + s_ ** 3 * ey
            pts.append((px, py))
        # the bend changes along the cane (W3-B2): a node every 6 to 10 texels where it kinks a texel
        # or two, and the tip droops; so no cane is a circular arc
        pts = np.array(pts)
        seg = np.r_[0, np.cumsum(np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1])))]
        nodes = [0.0]
        while nodes[-1] < seg[-1]:
            nodes.append(nodes[-1] + rng.uniform(6, 10))
        kick = np.array([0.0] + [rng.uniform(-1.8, 1.8) for _ in nodes[1:-1]] + [0.0])
        off = np.interp(seg, nodes, kick)
        tx_, ty_ = np.gradient(pts[:, 0]), np.gradient(pts[:, 1])
        nn_ = np.hypot(tx_, ty_) + 1e-9
        pts[:, 0] += -ty_ / nn_ * off
        pts[:, 1] += tx_ / nn_ * off
        f_ = seg / max(seg[-1], 1)
        pts[:, 1] += np.clip((f_ - 0.7) / 0.3, 0, 1) ** 2 * rng.uniform(1.5, 3.5)
        pts = [tuple(p_) for p_ in pts]
        last = None
        step = 0
        nxt = int(rng.integers(4, 7))
        for i, (px, py) in enumerate(pts):
            X, Y = int(round(px)), int(round(py))
            if (X, Y) == last or not (0 <= X < W2 and 2 <= Y < H2):
                continue
            last = (X, Y)
            inside = inside0[Y, X] and inside0[Y - 1, X] and inside0[min(H2 - 1, Y + 1), X]
            if inside and (k in behind or i < 40):
                continue                                            # behind the leaves
            if Y >= yb - 3:
                big[Y - 1, X] = C('leaf', 3)                        # the tip roots in a tuft of new leaves
                big[Y, X] = C('leaf', 2)
                bm[Y - 1, X] = bm[Y, X] = True
                continue
            big[Y - 1, X] = C('berry', 3) if py < pts[min(len(pts) - 1, i + 3)][1] + 0.5 else C('berry', 2)
            big[Y, X] = C('berry_cool', 2) if 'berry_cool' in FI else C('berry', 2)
            bm[Y - 1, X] = bm[Y, X] = True
            step += 1
            if step >= nxt and not inside0[Y - 2, X]:
                hx = X + (1 if ex > sx else -1)
                big[Y - 2, X] = C('berry', 4)                       # a thorn hook, leaning back
                bm[Y - 2, X] = True
                if 0 <= hx < W2 and not bm[Y - 2, hx]:
                    big[Y - 2, hx] = C('berry', 2)
                    bm[Y - 2, hx] = True
                step = 0
                nxt = int(rng.integers(4, 7))
    # the base: the mass's own dark underside, its contact uneven; nothing under the arches but the
    # canes' feet (W3-B2)
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
                body_c, dk = C('berry', 3), C('berry', 2)
            else:
                body_c, dk = C('dusk', 2) if 'dusk' in FI else C('berry', 2), C('dusk', 1) if 'dusk' in FI else C('berry', 1)
            big[Y:Y + 2, X:X + 2] = body_c
            big[Y + 1, X + 1] = dk
            big[Y, X] = C('berry', 5) if ripe >= 0.25 else C('grass_warm', 5)
            bm[Y:Y + 2, X:X + 2] = True
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
        # vertical plates (W2-T2): columns 3 to 5 texels wide following the trunk's lean, cut into
        # plates 6 to 12 tall; cracks between the columns and at one plate end in three, in timber 1
        # on the lit west third; the east third a dark field with few cracks; a lit west edge on one
        # plate in three
        rows = body.any(1)
        cxr = np.zeros(H)
        for y in np.nonzero(rows)[0]:
            xs_ = np.nonzero(body[y])[0]
            cxr[y] = np.median(xs_)
        cxr[~rows] = np.interp(np.nonzero(~rows)[0], np.nonzero(rows)[0], cxr[rows]) if rows.any() else 0
        cxr = ndi.gaussian_filter1d(cxr, 3.0)
        off = xx - cxr[:, None] + 200.0
        edges_ = [0.0]
        while edges_[-1] < 400:
            edges_.append(edges_[-1] + rng.uniform(3, 5.6))
        edges_ = np.array(edges_)
        wander = (ndi.gaussian_filter1d(rng.random(H), 4.0) - 0.5) * 2.2
        colf = np.searchsorted(edges_, off + wander[:, None]) - 1
        ncol = len(edges_)
        cut_ph = rng.uniform(0, 12, ncol)
        cut_h = [np.cumsum(rng.uniform(6, 12.5, H // 5 + 4)) - cut_ph[c] for c in range(ncol)]
        plate = np.full((H, W), -1, np.int64)
        endrow = np.zeros((H, W), bool)
        for c in np.unique(colf[body]):
            cm = body & (colf == c)
            pr = np.searchsorted(cut_h[c], yy[cm])
            plate[cm] = c * 1000 + pr
        P_ = np.pad(plate, 1, constant_values=-1)
        lit_cols = set(int(c) for c in np.unique(colf[body]) if rng.random() < 0.34)
        for p_ in np.unique(plate[body]):
            m = plate == p_
            c = int(p_ // 1000)
            vv = float(np.median(val[m]))
            sh_m = float(np.median(shade[m]))
            if sh_m < -0.3:                                        # the east third: a dark field
                # the core shadow, then a little reflected light at the far edge
                q_ = -sh_m
                vv = base - spread * 0.35 - spread * 0.9 * min(1.0, (q_ - 0.3) / 0.4) + spread * 0.45 * max(0.0, (q_ - 0.78) / 0.22)
                ring_ = ndi.binary_dilation(m) & ~m & body
                near_ = tuple(int(c) for c in np.unique(code[ring_]) if c >= 0)
                code[m] = lad.pick(vv + rng.uniform(-3, 11), rng, 7, avoid=near_)
                # the lower half of a dark plate a sibling a step down: the field is plates, not paint
                yl_ = yy[m]
                lowp = m & (yy > (yl_.min() + yl_.max()) / 2.0)
                if lowp.any():
                    code[lowp] = lad.pick(vv - 12, rng, 6, avoid=near_)
            else:
                code[m] = lad.pick(vv + rng.uniform(-6, 6), rng, 6)
            P = np.pad(m, 1)
            west = m & ~P[1:-1, :-2]
            if c in lit_cols and sh_m > -0.3 and rng.random() < 0.8:
                code[west] = lad.pick(vv + 20, rng, 6)
            elif sh_m <= -0.3 and rng.random() < 0.45:
                code[west] = lad.pick(vv + 22, rng, 6)              # a ridge catching the reflected light
            # one plate end in three is a crack
            if rng.random() < 0.34:
                e_ = m & ~P[2:, 1:-1] & (P_[2:, 1:-1] >= 0)
                ey_, ex_ = np.nonzero(e_)
                if len(ex_):
                    keep = np.abs(ex_ - ex_[int(rng.integers(0, len(ex_)))]) <= int(rng.integers(0, 2))
                    endrow[ey_[keep], ex_[keep]] = True
                    endrow[np.clip(ey_[keep] - 1, 0, H - 1), ex_[keep]] |= rng.random() < 0.4
        colb = body & (colf != np.pad(colf, ((0, 0), (0, 1)), constant_values=-1)[:, 1:]) & \
            np.pad(body, ((0, 0), (0, 1)))[:, 1:]
        east_keep = (np.arange(ncol) % 3 == 0)
        crk = colb & ((shade >= -0.3) | east_keep[np.clip(colf, 0, ncol - 1)])
        crk |= endrow
        litc = shade > 0.38
        code[crk & litc] = C(crack[0], min(5, crack[1] + 1))
        # the mid and the east: the bark's own darks (not the outline's near-black)
        dk = [lad.pick(lad.lo + 4, rng, 6), lad.pick(lad.lo + 10, rng, 6), C(*crack)]
        sel_ = crk & ~litc
        code[sel_] = np.array(dk)[(ndi.zoom(rng.integers(0, 3, (H // 4 + 2, W // 4 + 2)), 4, order=0)[:H, :W])[sel_]]
    elif kind == 'beech':
        # smooth grey (W2-T3): the cylinder ramp in bands, each broken by sibling mottle patches of 3 to
        # 6 texels in warm and cool greys; green algae on the east and the north; 2 or 3 eye scars
        q = np.round(val / 10.0) * 10.0
        f = ndi.zoom(rng.random((H // 3 + 2, W // 3 + 2)), 3, order=0)[:H, :W]
        g = ndi.zoom(rng.random((H // 4 + 2, W // 5 + 2)), (4, 5), order=0)[:H, :W]
        wl = Ladder(('stone_warm', 'ashlar_warm', 'stone'), {'stone_warm': 2.0})
        cl = Ladder(('stone_cool', 'stone', 'ashlar'), {'stone_cool': 2.0})
        for vv in np.unique(q[body]):
            m = body & (q == vv)
            base_c = lad.pick(vv, rng, 4)
            code[m] = base_c
            code[m & (f > 0.62)] = wl.pick(vv + 3, rng, 5, avoid=(base_c,))
            code[m & (f < 0.3)] = cl.pick(vv - 3, rng, 5, avoid=(base_c,))
            code[m & (g > 0.8) & (f >= 0.3) & (f <= 0.62)] = lad.pick(vv - 7, rng, 5, avoid=(base_c,))
        # algae on the shaded east and under the crown (the north side)
        ys_t = np.nonzero(body.any(1))[0]
        top_ = ys_t.min() if len(ys_t) else 0
        # (W3-T5) in irregular patches set in from the outline, more on the north under the crown,
        # in desaturated mossy tones
        nz = ndi.gaussian_filter(rng.random((H, W)), 1.3)
        nz = (nz - nz.min()) / max(1e-6, nz.max() - nz.min())
        zone_a = ((shade < -0.2) & (shade > -0.8)) | (yy < top_ + 20)
        alg = body & zone_a & (nz > 0.5 + 0.1 * np.clip((yy - top_ - 20) / 40.0, 0, 1))
        alg &= ndi.binary_erosion(body, iterations=2)
        alg = ndi.binary_opening(alg)
        code[alg] = np.where(nz[alg] > 0.72, C('grass', 1), C('grass_cool', 2))
        # eye scars: a dark lens 3 x 2 with a lit lower lip
        ys, xs = np.nonzero(body & (np.abs(shade) < 0.55) & (yy > top_ + 12))
        placed = []
        for k in rng.permutation(len(ys)):
            if len(placed) >= int(rng.integers(2, 4)):
                break
            y, x = int(ys[k]), int(xs[k])
            if any(abs(y - py) < 12 for py, _ in placed):
                continue
            if 0 < y and y + 3 < H and x + 3 < W and body[y - 1:y + 3, x - 1:x + 4].all():
                code[y, x + 1] = C('stone_cool', 1)
                code[y + 1, x:x + 3] = C('stone_cool', 1)
                code[y, x] = code[y, x + 2] = cl.pick(val[y, x] - 14, rng, 6)
                code[y + 2, x:x + 3] = wl.pick(val[y, x] + 18, rng, 6)
                placed.append((y, x))
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
           bark: str | None = None, base_rows: int = 0, root_w=(0.42, 3.0), wob: float = 1.6):
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
    half = (top_w + (foot_w - top_w) * t ** 1.4) / 2.0 + (ndi.gaussian_filter1d(rng.random(Ht), 3.0)[:, None] - 0.5) * wob
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
            m, sh = _tube(pts, foot_w * root_w[0], root_w[1], Ht, Wt)
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
    # a birch's dark fissured base (W2-T4): its top edge uneven, fissures rising 4 to 10 texels into
    # the white
    if base_rows:
        dlad = Ladder(('timber_cool', 'stone_cool', 'earth'), {'stone_cool': 1.5})
        topb = foot_y - base_rows - (ndi.gaussian_filter1d(rng.random(Wt), 1.2) * 7).astype(int)
        bm = body & (yy >= topb[None, :])
        xs_b = np.nonzero(bm.any(0))[0]
        if len(xs_b):
            for _ in range(int(rng.integers(3, 6))):
                fx = int(rng.integers(xs_b.min() + 1, xs_b.max()))
                L_ = int(rng.integers(4, 11))
                y_ = int(topb[fx])
                for j in range(L_):
                    X = fx + (1 if (j > L_ // 2 and rng.random() < 0.3) else 0)
                    for dx in ((0, 1) if j < L_ * 0.4 else (0,)):
                        if 0 <= y_ - j < Ht and 0 <= X + dx < Wt and body[y_ - j, X + dx]:
                            bm[y_ - j, X + dx] = True
        for y, x in zip(*np.nonzero(bm)):
            code[y, x] = dlad.pick(60 + 34 * np.clip(shade[y, x], -1, 1), rng, 7)
        Pb = np.pad(bm, 1)
        code[bm & (xx.astype(int) % 3 == 0) & Pb[2:, 1:-1] & (yy > topb[None, :] + 2)] = C('stone_cool', 0)
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
        'oak': dict(n=5, squat=1.0, wide=0.82, low=0.22, top=0.6, foot=1.05, lean=11, twist=5, roots=3, limbs=2,
                    bark='oak', gaps=2),
        'beech': dict(n=4, squat=1.0, wide=0.9, low=0.2, top=0.68, foot=1.25, lean=-4, twist=1.5, roots=3, limbs=2,
                      bark='beech', gaps=1, tk=dict(root_rows=(10, 14), root_reach=(3, 7), root_w=(0.6, 4.5))),
        'birch': dict(n=5, squat=1.0, wide=0.9, low=0.18, top=0.7, foot=1.15, lean=5, twist=1.5, roots=2, limbs=2,
                      bark='birch', gaps=1, edge_gaps=((-1, 0.42), (1, 0.62)),
                      tk=dict(root_rows=(9, 12), root_reach=(2, 4), root_w=(0.45, 3.0), wob=0.0)),
        'hollow_tree': dict(n=6, squat=1.13, wide=0.84, low=0.24, top=0.72, foot=1.0, lean=-5, twist=4, roots=3,
                            limbs=3, bark='hollow', gaps=2),
        'sapling': dict(n=3, squat=1.0, wide=0.9, low=0.2, top=0.6, foot=1.0, lean=3, twist=1.0, roots=0, limbs=0,
                        bark='sapling', gaps=0),
        'pine': dict(top=0.6, foot=1.05, lean=2, twist=1.0, roots=3, limbs=0, bark='oak',
                     tk=dict(root_rows=(5, 12), root_reach=(1, 8), root_w=(0.45, 3.4))),
    }[kind]
    if kind == 'pine':
        from . import foliage as F5
        S = S0
        tiers = pine_tiers(S, rng)
        code, mask, v = pine_crown(S, tiers, lad, rng, lo, hi, fams, wts)
        gaps = []
    else:
        S, masses, sh_ = crown_masses(S0, cfg['n'], rng, squat=cfg['squat'], wide=cfg['wide'])
        foot = (foot[0] + sh_[0], foot[1] + sh_[1])
        # the gaps (W2-F3): sky only where a limb leaves the crown's under-band, open to the outside
        ysS = np.nonzero(S.any(1))[0]
        Wc = np.nonzero(S.any(0))[0]
        spread = (Wc.max() - Wc.min()) * 0.16
        gaps = []
        for k_, sd in enumerate((-1, 1)[:cfg['gaps']] if cfg['gaps'] else ()):
            gx = foot[0] + cfg['lean'] + sd * (0.32 * spread + rng.uniform(1, 3))
            col = np.nonzero(S[:, int(np.clip(gx, 0, S.shape[1] - 1))])[0]
            if not len(col):
                continue
            gry = rng.uniform(13, 16) if k_ == 0 else rng.uniform(10, 13)
            gaps.append((gx, col.max() - gry * 0.2, rng.uniform(8, 10) if k_ == 0 else rng.uniform(6.5, 8), gry))
        for (ex_, ey_) in cfg.get('edge_gaps', ()):                    # notches at the crown's edge
            yr = int(ysS.min() + ey_ * (ysS.max() - ysS.min()))
            row = np.nonzero(S[yr])[0]
            if len(row):
                gaps.append((row.min() if ex_ < 0 else row.max(), yr, rng.uniform(5, 7), rng.uniform(5, 7)))
        code, mask, v = clump_crown(S, masses, lad, rng, lo=lo, hi=hi, gaps=gaps, low_band=cfg['low'],
                                    fams=fams, fam_w=wts, lift=0.12, **{'shapes': CLUMPS_S, **TREE_KW.get(kind, {})},
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
                                    front_root=kind not in ('birch', 'pine'), **cfg.get('tk', {}))
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


def _hang_clumps(seed=12, n=40):
    """Hanging leaf clumps for the willow's swags (W2-T7): 3 to 5 texels wide, 4 to 7 long, widest
    near the top and drawn to a point at the foot, the point off-centre now and then."""
    r = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        lw, lh = int(r.integers(4, 8)), int(r.integers(4, 8))
        tp = int(r.integers(-1, 2))
        m = np.zeros((lh, lw), bool)
        for y in range(lh):
            f = y / max(1, lh - 1)
            w_ = lw * (1.0 - 0.75 * max(0.0, f - 0.35) / 0.65) if f > 0.35 else lw * (0.75 + 0.25 * f / 0.35)
            c_ = (lw - 1) / 2 + tp * f * 0.7
            x0, x1 = int(round(c_ - w_ / 2 + 0.25)), int(round(c_ + w_ / 2 - 0.25))
            m[y, max(0, x0):min(lw, x1 + 1)] = True
        out.append(m)
    return out


HANG2 = _hang_clumps()


def _swag2(code, mask, pts, w, lad, lo, hi, rng, dim=0.0):
    """One swag as overlapping hanging leaf clumps (W2-T7): along pts [(x, y, s)] from the tip up, so
    each clump's point lies over the clump below; up to three abreast at the top, one at the tip;
    each lit on its west (a texel column a sibling up), dark on its east, its point a leaf tip on
    the outline."""
    H, W = mask.shape
    last = None
    for (px, py, s_) in reversed(pts):
        if last is not None and abs(py - last) < 2.6:
            continue
        last = py
        ww = w * (1 - 0.55 * s_ ** 1.3)
        n_ab = int(np.clip(round(ww / 2.6), 1, 4))
        for q in range(n_ab):
            off = (q - (n_ab - 1) / 2.0) * (ww / max(1, n_ab)) * 0.95 + rng.uniform(-0.7, 0.7)
            m = HANG2[int(rng.integers(0, len(HANG2)))]
            lx = int(round(px + off - m.shape[1] / 2))
            ly = int(round(py - 1 + rng.uniform(-1.0, 1.0)))
            side = off / max(1.0, ww / 2)
            val = 0.74 - 0.38 * s_ - dim + rng.uniform(-0.04, 0.04) - 0.14 * side
            T = lo + (hi - lo) * float(np.clip(val, 0.04, 1))
            body = lad.pick(T, rng, 5)
            Lb = _lum(body)
            lit = lad.pick(Lb + 20, rng, 5, avoid=(body,))
            dark = lad.pick(max(NB_FLOOR + 4, Lb - 24), rng, 5, avoid=(body,))
            P = np.pad(m, 1)
            westc = m & ~P[1:-1, :-2]
            eastc = m & ~P[1:-1, 2:] & ~westc
            tipc = m & ~P[2:, 1:-1] & (np.arange(m.shape[0])[:, None] >= m.shape[0] - 2)
            for part, c_ in ((m, body), (westc, lit), (eastc, dark), (tipc & ~westc, lit)):
                ys2, xs2 = np.nonzero(part)
                Y, X = ys2 + ly, xs2 + lx
                ok = (Y >= 0) & (Y < H) & (X >= 0) & (X < W)
                code[Y[ok], X[ok]] = c_
                mask[Y[ok], X[ok]] = True
    # the swag ends in 2 or 3 leaf tips of different lengths, lit, pointing down (W3-T3)
    px, py, s_ = pts[-1]
    val = 0.74 - 0.38 * s_ - dim
    tip_c = lad.pick(lo + (hi - lo) * float(np.clip(val + 0.12, 0.1, 1)), rng, 5)
    tip_d = lad.pick(lo + (hi - lo) * float(np.clip(val - 0.05, 0.05, 1)), rng, 5, avoid=(tip_c,))
    for q, dx in enumerate(sorted(rng.choice([-3, -1, 1, 3], size=int(rng.integers(2, 4)), replace=False))):
        L_ = int(rng.integers(2, 6))
        for j in range(L_):
            Y, X = int(round(py)) + 3 + j, int(round(px + dx + 0.3 * j * np.sign(dx)))
            for X2 in ((X, X + 1) if j < L_ - 2 else (X,)):
                if 0 <= Y < H and 0 <= X2 < W:
                    code[Y, X2] = tip_c if X2 == X else tip_d
                    mask[Y, X2] = True


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
    ccode, cmask, v = clump_crown(capS, cap, lad, rng, lo=lo + 12, hi=hi, low_band=0.3, edge_fam='leaf', fams=fams,
                                  fam_w=wts, lift=0.12, shapes=CLUMPS_S, **WILLOW_KW)
    # the swags' springing points: along the cap's underside and its shoulders
    springs = []
    # the swags gathered into 4 curtains, each 15 to 30 texels wide, with the dark interior and the
    # trunk showing between them (W3-T3)
    n_c = 4
    cfs = np.linspace(-0.78, 0.78, n_c) + rng.uniform(-0.06, 0.06, n_c)
    cws = [rng.uniform(18, 30) / (W * 0.45) for _ in range(n_c)]
    curtains = list(zip(cfs, cws))
    fl = []
    for (fc, wc) in curtains:
        nk = int(round(wc * W * 0.45 / 3.4))
        fl += [fc - wc / 2 + wc * (j + rng.uniform(0.2, 0.8)) / nk for j in range(nk)]
    for f in fl:
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
                                    limb_rise=Hc * 0.72, limb_spread=W * 0.3, bark='willow')
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
    cshort = [abs(fc) < 0.3 and rng.random() < 0.8 for (fc, wc) in curtains]
    for s in springs:
        ci = int(np.argmin([abs(s[0] - fc) for (fc, wc) in curtains]))
        short = cshort[ci] if rng.random() < 0.8 else not cshort[ci]
        paths[s] = swag_path(*s, short)
    for s in back:
        _swag2(code, mask, paths[s], rng.uniform(8, 11), lad, lo, hi, rng, dim=0.28)
    # the interior shade: inside the cap's shadow, between the back swags and the front
    region = (yy > top + Hc * 0.25) & (yy < hem - Hc * 0.22) & (np.abs(xx - cx) < W * 0.42)
    region &= ndi.binary_dilation(mask, iterations=6) | (yy < top + Hc * 0.5)
    pf = ndi.gaussian_filter(rng.random((Hp, Wp)), 2.5)
    pf = (pf - pf.min()) / max(1e-6, pf.max() - pf.min())
    opts = [lad.pick(max(lo - 10, NB_FLOOR + 3), rng, 3), lad.pick(lo - 2, rng, 4), lad.pick(lo + 6, rng, 4)]
    free = region & ~mask
    for y, x in zip(*np.nonzero(free)):
        code[y, x] = opts[min(2, int(pf[y, x] * 3))]
    # the far curtain in the interior: hanging clumps in the deep shade (no flat fill)
    far = np.zeros_like(mask)
    for j, y in enumerate(np.arange(top, hem, 4.0)):
        for x in np.arange(0, Wp, 3.4) + 1.7 * (j % 2):
            yi, xi = int(y + rng.uniform(-1, 1)), int(x + rng.uniform(-1, 1))
            if 0 <= yi < Hp and 0 <= xi < Wp and free[yi, xi]:
                m = HANG2[int(rng.integers(0, len(HANG2)))]
                T_ = max(NB_FLOOR + 6, lo - 6 + 22 * rng.random())
                body = lad.pick(T_, rng, 5)
                dk = lad.pick(_lum(body) - 9, rng, 4, avoid=(body,))
                P = np.pad(m, 1)
                for part, c_ in ((m, body), (m & ~P[1:-1, 2:], dk)):
                    ys2, xs2 = np.nonzero(part)
                    Y, X = ys2 + yi - 1, xs2 + xi - m.shape[1] // 2
                    ok = (Y >= 0) & (Y < Hp) & (X >= 0) & (X < Wp)
                    ok[ok] = free[Y[ok], X[ok]]
                    code[Y[ok], X[ok]] = c_
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
        # each curtain a mass (pass 5): lit on its west, its east in its own shade
        ci = int(np.argmin([abs(s[0] - fc) for (fc, wc) in curtains]))
        fc, wc = curtains[ci]
        u_c = float(np.clip((s[0] - (fc - wc / 2)) / max(1e-3, wc), 0, 1))
        _swag2(code, mask, paths[s], rng.uniform(8, 12), lad, lo, hi, rng, dim=-0.08 + 0.34 * u_c ** 1.3)
    # inside a curtain, the slits between swags are shade (leaf 1 to 2), not outline (W3-T3)
    for (fc, wc) in curtains:
        x0c, x1c = int(cx + (fc - wc / 2) * W * 0.45) - 4, int(cx + (fc + wc / 2) * W * 0.45) + 4
        for y in range(int(hem - Hc * 0.55), Hp):
            row = mask[y, max(0, x0c):min(Wp, x1c)]
            xs_ = np.nonzero(row)[0]
            if len(xs_) < 2:
                continue
            for a_, b_ in zip(xs_[:-1], xs_[1:]):
                if 1 < b_ - a_ <= 5:
                    for X in range(a_ + 1, b_):
                        X0 = X + max(0, x0c)
                        below = mask[min(Hp - 1, y + 2), X0] or mask[min(Hp - 1, y + 4), X0]
                        if below:
                            code[y, X0] = C('leaf', 1) if (X0 + y) % 3 else C('grass_cool', 1)
                            mask[y, X0] = True
    mask = ndi.binary_fill_holes(_spurs(mask))
    hole = mask & (code < 0)
    if hole.any():
        idx = ndi.distance_transform_edt(code < 0, return_distances=False, return_indices=True)
        code[hole] = code[idx[0][hole], idx[1][hole]]
    code[~mask] = -1
    # the cap's edge tone where swags now hang over it is inside the tree: a gap tone, not black
    inner_ = ndi.binary_erosion(mask, iterations=1)
    for c0 in (C('leaf', 0), C('leaf_cool', 0)):
        code[inner_ & (code == c0)] = C('leaf', 1)
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

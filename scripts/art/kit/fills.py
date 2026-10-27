"""Seamless material fills for the terrain kit (docs/world-editor.md, "The kit").

A fill is the inside of one ground material (a lawn, packed earth, sand ...) painted once as a
periodic texture of PERIOD x PERIOD texels: its right edge continues into its left and its bottom
into its top, so the renderer can lay it anywhere by world position (texel mod PERIOD) and it never
shows a seam. Each fill is the soft-grid painter's own recipe (scripts/art/native/softground.py),
made periodic in three ways:

1. every noise field is periodic: value noise on a lattice wrapped to the period
   (`periodic_noise`), smoothed white noise filtered with mode='wrap';
2. every morphological step (dilations, openings) wraps round the period (`wrap_op`);
3. every random placement (a blade, a tuft, a flower, a pebble) is drawn once in [0, PERIOD) and
   stamped at all nine periodic copies on a canvas padded by MARGIN (`Torus`), so a stamp that
   crosses the right edge comes back on the left. The copies are applied in the same order
   everywhere, so local read-modify-write stamps stay consistent; the centre is cropped.

Codes are palette codes (family * 8 + tone, palette.py). The painters here follow softground.lawn
and softground.dirt line by line (same sizes, shares, seeds' roles); a change to the look is made
in both until softground grows a periodic mode of its own.
"""
from __future__ import annotations

import contextlib

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

from scripts.art.native import softground as GD
from scripts.art.native.palette import C, FI, step
from scripts.art.native.terrain import noise as TN

PERIOD = 768          # texels: 32 cells of 24 (8 world px at density 3)
MARGIN = 32           # pad for stamps that cross the period's edge


# ------------------------------------------------------------------------------------------------
# periodic building blocks
# ------------------------------------------------------------------------------------------------
@contextlib.contextmanager
def periodic_noise(period: int = PERIOD):
    """Within the block, TN.vnoise_hd is periodic with `period` texels: its lattice cell is rounded
    so a whole number of cells spans the period, and lattice indices wrap."""
    orig = TN.vnoise_hd

    def vn(x, y, cell, seed):
        n = max(1, int(round(period / float(cell))))
        c = period / n
        gx, gy = np.floor(x / c).astype(np.int64), np.floor(y / c).astype(np.int64)
        fx, fy = x / c - gx, y / c - gy

        def h(a, b):
            a, b = a % n, b % n
            k = TN._fmix((a & 0xffffffff) * 0x9E3779B1 + 0x632BE5AB * seed)
            return TN._fmix(k ^ ((b & 0xffffffff) * 0x85EBCA77)) / 4294967295.0
        sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        return (h(gx, gy) * (1 - sx) + h(gx + 1, gy) * sx) * (1 - sy) + \
            (h(gx, gy + 1) * (1 - sx) + h(gx + 1, gy + 1) * sx) * sy
    TN.vnoise_hd = vn
    try:
        yield
    finally:
        TN.vnoise_hd = orig


def wrap_op(m: np.ndarray, fn, pad: int) -> np.ndarray:
    """A morphological step on a periodic mask: pad by wrapping, apply, crop."""
    p = np.pad(m, pad, mode='wrap')
    return fn(p)[pad:-pad, pad:-pad]


def dil(m, it):
    return wrap_op(m, lambda a: ndi.binary_dilation(a, iterations=it), it + 1)


def blobs(P: int, seed: int, cell: float, share: float) -> np.ndarray:
    """softground.blobs on a torus (its gaussian already wraps)."""
    return GD.blobs(P, P, seed, cell, share)


def fbm(P: int, cell: float, seed: int) -> np.ndarray:
    return GD.fbm(P, P, cell, seed)


def nz(P: int, cell: float, seed: int) -> np.ndarray:
    return GD.nz(P, P, cell, seed)


class Torus:
    """A periodic canvas: `cv` is PERIOD + 2 * MARGIN square; `at(y, x)` yields the canvas
    coordinates of a world texel's nine periodic copies that can touch the canvas."""

    def __init__(self, base: np.ndarray, margin: int = MARGIN):
        self.P = base.shape[0]
        self.M = margin
        self.cv = np.pad(base, margin, mode='wrap')

    def at(self, y, x):
        S = self.P + 2 * self.M
        for dy in (-self.P, 0, self.P):
            for dx in (-self.P, 0, self.P):
                Y, X = int(y) + self.M + dy, int(x) + self.M + dx
                if -self.M <= Y < S + self.M and -self.M <= X < S + self.M:
                    yield Y, X

    def crop(self) -> np.ndarray:
        return self.cv[self.M:self.M + self.P, self.M:self.M + self.P].copy()


# ------------------------------------------------------------------------------------------------
# the lawn (softground.lawn, periodic)
# ------------------------------------------------------------------------------------------------
def lawn(seed: int = 977, P: int = PERIOD, fam: str = 'grass', base: int = 3, lush: float = 1.0,
         flowers: float = 1.0, grain: float = 1.0, mottle: float = 3.0) -> np.ndarray:
    """softground.lawn's calm field, blotches, mottle, blades, tuft clumps and flower groups, on a
    torus of P texels."""
    rng = np.random.default_rng(seed)
    with periodic_noise(P):
        cv = np.full((P, P), C(fam, base), np.int32)
        cool = fam + '_cool' if fam + '_cool' in FI else fam
        warm = fam + '_warm' if fam + '_warm' in FI else fam
        dark = blobs(P, seed + 1, 70.0, 0.42)
        lit = blobs(P, seed + 2, 80.0, 0.2) & ~dil(dark, 4)
        yy, xx = np.mgrid[0:P, 0:P]
        chk = ((xx // 2 + yy // 2) % 2) == 0
        cv[dark] = C(cool, base)
        cv[dil(dark, 3) & ~dark & chk] = C(cool, base)
        cv[lit] = C(warm, base)
        cv[dil(lit, 2) & ~lit & ~dark & chk] = C(warm, base)
        damp = ndi.gaussian_filter(dark.astype(float), 5.0, mode='wrap')
        mot = wrap_op(fbm(P, mottle, seed + 21) > 0.5,
                      lambda a: ndi.binary_opening(a, structure=np.ones((2, 2), bool)), 3)
        swap = np.where(dark, C(fam, base), np.where(lit, C(fam, base), C(cool, base)))
        sel = mot & ((cv == C(fam, base)) | (cv == C(cool, base)) | (cv == C(warm, base)))
        cv[sel] = swap[sel]
        gather = fbm(P, 50.0, seed + 3) + 0.5 * damp
    T = Torus(cv)
    c_ = T.cv
    for _ in range(int(P * P / 75)):
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        for Y, X in T.at(y, x):
            if 1 <= Y < c_.shape[0] and 0 <= X < c_.shape[1]:
                c = step(c_[Y, X], 1)
                c_[Y, X] = c
                c_[Y - 1, X] = c
    for _ in range(int(P * P / 420 * grain)):
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        L = int(rng.integers(2, 4))
        for Y, X in T.at(y, x):
            if L <= Y < c_.shape[0] and 0 <= X < c_.shape[1]:
                c = step(c_[Y, X], -1)
                for j in range(L):
                    c_[Y - j, X] = c
    cl = []
    for _ in range(int(P * P / 900)):
        y, x = rng.uniform(0, P), rng.uniform(0, P)
        rad = 36 * (1.2 - 0.4 * lush)

        def wd(a, b):
            d = abs(a - b) % P
            return min(d, P - d)
        if any(wd(y, a) ** 2 + wd(x, b) ** 2 < rad ** 2 for a, b in cl):
            continue
        g = gather[int(y) % P, int(x) % P]
        if rng.random() > np.clip(0.25 + g * 0.9, 0.1, 0.95) * lush:
            continue
        cl.append((y, x))
        dmp = damp[int(y) % P, int(x) % P]
        for _k in range(int(rng.integers(3, 8))):
            ty = int(round(y + rng.normal(0, 4.5)))
            tx = int(round(x + rng.normal(0, 8.0)))
            shp = GD.tuft_shape(rng, rng.uniform(1.25, 2.1))
            if rng.random() < 0.5 * dmp:
                shp = [(dy, dx, dt - 1 if dt <= 0 else dt) for (dy, dx, dt) in shp]
            for Y, X in T.at(ty % P, tx % P):
                GD.stamp(c_, Y, X, shp, None)
    low = (c_ % 8 == 0)
    c_[low] = c_[low] + 1
    GD.tidy_codes(c_)
    if flowers > 0:
        n = int(P * P / 16000 * flowers)
        for _ in range(n):
            cy, cx = int(rng.integers(0, P)), int(rng.integers(0, P))
            kind = ('white', 'white', 'yellow', 'violet')[int(rng.integers(0, 4))]
            for _k in range(int(rng.integers(2, 5))):
                fy, fx = (cy + int(rng.normal(0, 3.0))) % P, (cx + int(rng.normal(0, 4.5))) % P
                for Y, X in T.at(fy, fx):
                    GD.flower(c_, Y, X, kind)
    return T.crop()


# ------------------------------------------------------------------------------------------------
# packed earth (softground.dirt with the mask everywhere, periodic)
# ------------------------------------------------------------------------------------------------
def dirt(seed: int = 43, P: int = PERIOD, fam: str = 'path', cell: float = 12.0,
         stones: float = 1.0, joints: float = 0.28, lit: float = 0.4, blades: float = 1.0,
         soft_joints: bool = False) -> np.ndarray:
    """softground.dirt's clods, dry and damp patches, dry blades and pebble clusters on a torus.
    The crumbs along an edge belong to the transition (edges.py), not to the fill. `joints` is the
    slow field's threshold above which the gaps between clods show (softground's 0.28 shows most:
    a cobbled look, kept for the cobble road; 0.62 shows a few soft joints in drifts, the calm
    packed earth of the swatches), `lit` the share of clods without a lit rim."""
    rng = np.random.default_rng(seed)
    with periodic_noise(P):
        yy, xx = np.mgrid[0:P, 0:P]
        # the clods' jittered lattice, made to tile: whole rows and columns across the period
        nr = max(2, int(round(P / (cell * 0.82))) // 2 * 2)
        nc = max(1, int(round(P / cell)))
        sy, sx = P / nr, P / nc
        pts = []
        for j in range(nr):
            for i in range(nc):
                pts.append(((i * sx + (j % 2) * sx / 2 + rng.uniform(-0.32, 0.32) * sx) % P,
                            (j * sy + rng.uniform(-0.3, 0.3) * sy) % P))
        pts = np.array(pts)
        tree = cKDTree(pts, boxsize=P)
        q = np.stack([(xx.ravel() + 0.5) % P, (yy.ravel() + 0.5) % P], 1)
        d, i = tree.query(q, k=2)
        d1, d2 = d[:, 0].reshape(P, P), d[:, 1].reshape(P, P)
        cid = i[:, 0].reshape(P, P)
        h = (cid * 2654435761 % 1000) / 1000.0
        famc = np.full((P, P), FI[fam])
        pw = GD.patches(P, P, seed + 5, 40.0, 0.28)
        pc = GD.patches(P, P, seed + 6, 36.0, 0.22) & ~pw
        famc[pw] = FI[fam + '_warm']
        famc[pc] = FI[fam + '_cool']
        famc[(h < 0.12) & ~pc] = FI[fam + '_warm']
        t = np.full((P, P), 3)
        vx = (xx + 0.5 - pts[cid, 0] + P / 2) % P - P / 2
        vy = (yy + 0.5 - pts[cid, 1] + P / 2) % P - P / 2
        rr = cell * 0.5 * (0.86 + 0.22 * nz(P, 5.0, seed + 11))
        gap = (d1 > rr) | ((d2 - d1) < 1.3)
        show = nz(P, 26.0, seed + 7) > joints
        t[gap & show] = 2
        if soft_joints:
            # the hidden joints still part the clods, in the damp sibling at the body's tone: the
            # clods read as packed earth, never as cobbles or as cracks breaking off in drifts
            hid = gap & ~show
            base_ = hid & (famc == FI[fam])
            famc[hid & (famc == FI[fam + '_warm'])] = FI[fam]
            famc[base_] = FI[fam + '_cool']
        hi = ~gap & ((vx * 0.6 + vy * 0.8) < -0.42 * rr) & (d1 > 0.42 * rr) & (h > lit)
        t[hi] = 4
        cv = (famc * 8 + t).astype(np.int32)
    T = Torus(cv)
    c_ = T.cv
    # dry blades blown onto the dirt
    for _ in range(int(P * P / 1800 * blades)):
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        L = int(rng.integers(3, 7))
        d_ = 1 if rng.random() < 0.5 else -1
        for Y, X in T.at(y, x):
            for j in range(L):
                GD.put(c_, Y - (j * j) // 6, X + d_ * j, C('grass_warm', 4 if j < L - 1 else 5))
    # pebbles in small clusters, a larger stone now and then
    if stones > 0:
        for _ in range(max(1, int(P * P / 2600 * stones))):
            ky, kx = int(rng.integers(0, P)), int(rng.integers(0, P))
            for _j in range(int(rng.integers(2, 6))):
                py = (ky + int(rng.normal(0, 4.0))) % P
                px = (kx + int(rng.normal(0, 6.0))) % P
                big = rng.random() < 0.15
                s = int(rng.integers(0, 2 ** 31))
                for Y, X in T.at(py, px):
                    GD.pebble(c_, Y, X, np.random.default_rng(s), big=big)
    return T.crop()


PAINTERS = {'lawn': lawn, 'dirt': dirt}


def seam_error(f: np.ndarray) -> float:
    """How unlike a fill's wrapped edges are its inner rows and columns (0 for a perfect torus is
    not expected: neighbouring rows differ anyway). Returns the share of texels on the wrap seam
    that differ from their neighbour across it, divided by the same share one row inside."""
    across = np.mean(f[0] != f[-1]) + np.mean(f[:, 0] != f[:, -1])
    inside = np.mean(f[1] != f[0]) + np.mean(f[:, 1] != f[:, 0])
    return float(across / max(1e-9, inside))

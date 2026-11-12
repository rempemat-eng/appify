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


# ------------------------------------------------------------------------------------------------
# water (softground.water's body, periodic; its banks are the transition's, edges.bank)
# ------------------------------------------------------------------------------------------------
def water(seed: int = 402, P: int = PERIOD, fam: str = 'water', ripples: float = 1.0) -> np.ndarray:
    """softground.water's body: one calm tone, broad soft patches of the warm sibling (the sky),
    ripple lines 4 to 12 px (a lit line over a darker texel) gathered in drifts, a few glints."""
    rng = np.random.default_rng(seed)
    with periodic_noise(P):
        t = np.full((P, P), 2)
        famw = np.full((P, P), FI[fam])
        sky = blobs(P, seed + 2, 70.0, 0.25)
        famw[sky] = FI[fam + '_warm'] if fam + '_warm' in FI else FI[fam]
        dens = nz(P, 26.0, seed + 5)
    cv = (famw * 8 + t).astype(np.int32)
    T = Torus(cv)
    c_ = T.cv
    nr = int(P * P / 650 * ripples)
    while nr > 0:
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        if dens[y, x] < 0.45 or rng.random() > dens[y, x]:
            continue
        nr -= 1
        L = int(rng.integers(4, 13))
        for Y, X in T.at(y, x):
            for j in range(L):
                if not (0 <= Y + 1 < c_.shape[0] and 0 <= X + j < c_.shape[1]):
                    continue
                d = 2 if 0 < j < L - 1 else 1
                c_[Y, X + j] = c_[Y, X + j] - c_[Y, X + j] % 8 + min(5, c_[Y, X + j] % 8 + d)
                c_[Y + 1, X + j] = c_[Y + 1, X + j] - c_[Y + 1, X + j] % 8 + max(0, c_[Y + 1, X + j] % 8 - 1)
    for _ in range(P * P // 4000 + 1):
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        for Y, X in T.at(y, x):
            for (dy, dx) in ((0, 0), (0, 1), (-1, 0), (0, -1), (1, 0)):
                if 0 <= Y + dy < c_.shape[0] and 0 <= X + dx < c_.shape[1]:
                    v = c_[Y + dy, X + dx]
                    c_[Y + dy, X + dx] = v - v % 8 + (5 if (dy, dx) == (0, 0) else 4)
    return T.crop()


# ------------------------------------------------------------------------------------------------
# a ledge's face (softground.ledge's earth face as a strip, periodic across)
# ------------------------------------------------------------------------------------------------
def face_strip(seed: int = 301, P: int = PERIOD, face_px: int = 48, earth: str = 'earth') -> np.ndarray:
    """The face of raised ground as a strip `face_px` tall (rows below the rim; the rest of the
    period unused), periodic across (eastward-edges.md 2.2): the under-lip shade (the rim line and
    the under-lip line are the lip transition's, which follows the lumped outline), a body of
    rounded clods wider than tall, each lit at its upper left with its lower right in shade and dark
    crevices between them, a root now and then, and a dark foot band with pebbles. Indexed by the
    texel's depth below the rim (terrain.gdshader's strip fills)."""
    rng = np.random.default_rng(seed)
    e0 = earth
    ew = earth + '_warm' if earth + '_warm' in FI else earth
    ec = earth + '_cool' if earth + '_cool' in FI else earth
    cv = np.full((P, P), C(e0, 1), np.int32)
    H = face_px
    cv[:3, :] = C(e0, 1)
    cv[3:5, :] = C(e0, 2)
    body0, body1 = 5, H - 4
    # clods on a jittered lattice that tiles across the period
    sx = 12.0
    ncol = int(round(P / sx))
    sx = P / ncol
    yy, xx = np.mgrid[0:H, 0:P] + 0.5
    rows = np.arange(body0 + 3.0, body1 + 2.0, 7.5)
    lumps_ = []
    for j, gy in enumerate(rows):
        for i in range(ncol):
            cx = (i + 0.5 * (j % 2)) * sx + rng.uniform(-0.3, 0.3) * sx
            cy = gy + rng.uniform(-1.2, 1.2)
            lumps_.append((cy, cx % P, rng.uniform(5.0, 7.5), rng.uniform(3.4, 4.6)))
    for (cy, cx, rw, rh) in sorted(lumps_):
        for off in (-P, 0, P):
            x0, x1 = max(0, int(cx + off - rw - 1)), min(P, int(cx + off + rw + 2))
            if x0 >= x1:
                continue
            y0, y1 = max(body0, int(cy - rh - 1)), min(body1, int(cy + rh + 2))
            dy = (yy[y0:y1, x0:x1] - cy) / rh
            dx = (xx[y0:y1, x0:x1] - cx - off) / rw
            r = (np.abs(dx) ** 2.4 + np.abs(dy) ** 2.4) ** (1 / 2.4)
            inside = r <= 1.0
            lam = -0.62 * dx - 0.78 * dy + 0.35 * (1 - r)
            t = np.where(lam > 0.62, 4, np.where(lam > 0.05, 3, np.where(lam > -0.55, 2, 1)))
            fam = np.where(lam > 0.62, FI[ew], np.where(lam < -0.55, FI[ec], FI[e0]))
            sub = cv[y0:y1, x0:x1]
            sub[inside] = (fam * 8 + t)[inside]
    # roots from under the lip, a few
    for _ in range(int(P / 90)):
        x = int(rng.integers(0, P))
        L = int(rng.integers(6, 14))
        for j in range(L):
            cv[3 + j, x % P] = C('timber_cool', 2 if j % 3 else 3)
            if rng.random() < 0.3:
                x += 1 if rng.random() < 0.5 else -1
    # the foot: dark, a pebble now and then
    cv[body1:H, :] = C(e0, 1)
    cv[H - 2:H, :] = C(ec, 0)
    for _ in range(int(P / 40)):
        x = int(rng.integers(0, P))
        w = int(rng.integers(3, 6))
        for dx in range(w):
            cv[body1 + 1, (x + dx) % P] = C('stone', 3 if dx < w - 1 else 2)
            cv[body1 + 2, (x + dx) % P] = C('stone', 2)
    return cv


# ------------------------------------------------------------------------------------------------
# the Frostline's grounds (scripts/art/kit/sets/frost.py; the detail audit of #478, F-G1 to F-G3)
# ------------------------------------------------------------------------------------------------
def aniso(P: int, sx: float, sy: float, seed: int) -> np.ndarray:
    """Periodic smooth noise with features about `sx` by `sy` texels (wind-drawn when sx > sy):
    white noise filtered by an anisotropic gaussian in frequency, so it tiles exactly. Mean 0, sd 1."""
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.standard_normal((P, P)))
    ky = np.fft.fftfreq(P)[:, None]
    kx = np.fft.fftfreq(P)[None, :]
    g = np.exp(-0.5 * ((kx * sx * 2 * np.pi / 2.355) ** 2 + (ky * sy * 2 * np.pi / 2.355) ** 2))
    a = np.real(np.fft.ifft2(f * g))
    return (a - a.mean()) / (a.std() + 1e-9)


def _no_specks(sel: np.ndarray, area: int) -> np.ndarray:
    """A periodic mask without its components under `area` texels (no lone flecks)."""
    pad = 24
    p = np.pad(sel, pad, mode='wrap')
    lab, n = ndi.label(p)
    if n:
        sizes = np.bincount(lab.ravel())
        p = p & (sizes[lab] >= area)
    return p[pad:-pad, pad:-pad]


def snow(seed: int = 1401, P: int = PERIOD) -> np.ndarray:
    """Lying snow: a calm plane in three tones laid by the wind. Long soft patches 40 to 120 texels
    across: lit wind-polished crests (snow 5), the body (snow 4) and cool hollows (snow_cool 4); each
    crest's lee (its south edge) falls away in a cool row (snow_cool 3), so the patches read as low
    drifts, not stains. No grass stamps: tufts belong where the wind scours (the moraine's edge
    dressing)."""
    w = aniso(P, 90.0, 22.0, seed) + 0.35 * aniso(P, 30.0, 12.0, seed + 1)
    crest = _no_specks(w > 0.85, 60)
    hollow = _no_specks(w < -0.75, 60)
    cv = np.full((P, P), C('snow', 4), np.int32)
    cv[hollow] = C('snow_cool', 4)
    cv[crest] = C('snow', 5)
    lee = crest & ~np.roll(crest, -1, 0)                    # the crest's last row before the fall
    fall = np.roll(lee, 1, 0) & ~crest
    cv[fall] = C('snow_cool', 3)
    return cv


def snow_trod(seed: int = 1402, P: int = PERIOD) -> np.ndarray:
    """Trodden snow: a calm packed plane a tone cooler and greyer than the snow (snow_cool 4), worn
    patches a tone darker (snow_cool 3), the odd lit compressed ridge, and bootprints in staggered
    pairs (2 by 3 texels, snow_cool 2) along short runs, at a 7 texel pitch."""
    rng = np.random.default_rng(seed)
    w = aniso(P, 40.0, 40.0, seed)
    cv = np.full((P, P), C('snow_cool', 4), np.int32)
    cv[_no_specks(w > 0.7, 40)] = C('snow_cool', 3)
    T = Torus(cv)
    c_ = T.cv
    # lit ridges between the worn patches
    for _ in range(P * P // 9000):
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        L = int(rng.integers(8, 20))
        for Y, X in T.at(y, x):
            for j in range(L):
                if 0 <= Y + 1 < c_.shape[0] and 0 <= X + j < c_.shape[1]:
                    c_[Y, X + j] = C('snow', 4)
                    c_[Y + 1, X + j] = C('snow_cool', 3)
    # bootprint runs: vertical runs (up and down the trod) and fewer across
    for _ in range(P * P // 5200):
        y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
        vert = rng.random() < 0.6
        n = int(rng.integers(4, 8))
        for i in range(n):
            side = (i % 2) * 2 - 1
            py = y + (i * 7 if vert else side * 2)
            px = x + (side * 2 if vert else i * 7)
            h, wd = (3, 2) if vert else (2, 3)
            for Y, X in T.at(py, px):
                for dy in range(h):
                    for dx in range(wd):
                        if 0 <= Y + dy < c_.shape[0] and 0 <= X + dx < c_.shape[1]:
                            c_[Y + dy, X + dx] = C('snow_cool', 2)
                # the print's south lip lit by the light from above
                for dx in range(wd):
                    if 0 <= Y + h < c_.shape[0] and 0 <= X + dx < c_.shape[1]:
                        c_[Y + h, X + dx] = C('snow_cool', 5)
    return T.crop()


def moraine(seed: int = 1403, P: int = PERIOD) -> np.ndarray:
    """A granite moraine: an unsorted cold grey grit field (slate_cool and slate in 2 by 2 grains)
    carrying stones of three size classes (3 to 5, 8 to 12 and a few 16 to 24 texels across), laid
    in drifts with open grit between. Each stone has a lit upper-west cap, a body, a dark lower-east
    side and a contact texel; old snow lies in the hollow on the north side of the large ones."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:P, 0:P]
    gq = TN._fmix((((yy // 2) % (P // 2)) * 92821 + ((xx // 2) % (P // 2)) * 68917 + seed) & 0xffffffff) / 4294967295.0
    g = aniso(P, 9.0, 7.0, seed + 2)
    cv = np.where(g > 0.2, C('slate', 3), C('slate_cool', 3)).astype(np.int32)
    cv[(gq > 0.9) & (g < 0.9)] = C('slate_cool', 2)            # dark grains, 2 by 2, one in ten
    cv[(gq < 0.04) & (g > 0.5)] = C('slate', 4)                # the odd lit grain on the rises
    drift = aniso(P, 60.0, 40.0, seed + 1)
    T = Torus(cv)
    c_ = T.cv
    taken = np.zeros_like(c_, bool)
    sets = [('slate', 'slate_cool'), ('slate', 'slate'), ('iron', 'slate_cool')]

    def stone(y, x, r, fam):
        rx, ry = r * rng.uniform(1.0, 1.3), r * rng.uniform(0.7, 0.85)
        big = r >= 7
        for Y, X in T.at(y, x):
            y0, y1 = int(Y - ry * (1.8 if big else 1.0) - 1), int(Y + ry + 3)
            x0, x1 = int(X - rx - 1), int(X + rx + 2)
            if y0 < 0 or x0 < 0 or y1 >= c_.shape[0] or x1 >= c_.shape[1]:
                continue
            sy, sx = np.mgrid[y0:y1, x0:x1]
            dy, dx = (sy + 0.5 - Y) / ry, (sx + 0.5 - X) / rx
            q = dx * dx + dy * dy
            body = q <= 1.0
            if big:   # old snow in the hollow on the north side, laid before the stone
                sq = ((sx + 0.5 - X - rx * 0.1) / (rx * 0.8)) ** 2 + ((sy + 0.5 - (Y - ry * 1.05)) / (ry * 0.6)) ** 2
                sn = (sq <= 1.0) & ~body
                c_[y0:y1, x0:x1][sn] = C('snow', 4)
                c_[y0:y1, x0:x1][sn & (sy + 1 > Y - ry * 0.75)] = C('snow_cool', 4)
            lit = body & ((dx + dy) < -0.55)
            dark = body & ((dx + dy) > 0.6)
            reg = c_[y0:y1, x0:x1]
            reg[body] = C(fam[1], 3)
            reg[body & (dx + dy < -0.1)] = C(fam[0], 3)
            reg[lit] = C(fam[0], 5 if big else 4)
            reg[dark] = C(fam[1], 1)
            # contact: the grit under the stone's south-east edge in deep shade
            foot = (~body) & (q <= 1.35) & (dy > 0.35) & (dx > -0.3)
            reg[foot] = C('slate_cool', 0)
            taken[y0:y1, x0:x1] |= body

    classes = [(8.0, 12.0, P * P // 11000), (4.0, 6.0, P * P // 1700), (1.6, 2.5, P * P // 500)]
    for lo, hi, n in classes:
        placed = 0
        tries = 0
        while placed < n and tries < n * 30:
            tries += 1
            y, x = int(rng.integers(0, P)), int(rng.integers(0, P))
            if drift[y, x] < (-0.2 if hi < 3 else 0.1) or rng.random() > 0.5 + 0.5 * np.tanh(drift[y, x]):
                continue
            r = rng.uniform(lo, hi)
            Y, X = y + T.M, x + T.M
            if taken[max(0, int(Y - r - 2)):int(Y + r + 3), max(0, int(X - r * 1.3 - 2)):int(X + r * 1.3 + 3)].any():
                continue
            stone(y, x, r, sets[int(rng.integers(0, len(sets)))])
            placed += 1
    return T.crop()


def ice(seed: int = 1404, P: int = PERIOD) -> np.ndarray:
    """A frozen tarn: clear blue ice (sky_cool 4, water_cool 4 where it is deeper and darker) under
    wind-laid streaks of white ice and snow (snow_cool 3 and 4), crack lines (water_cool 2) running
    20 to 60 texels in slow bends with a lit texel on their north side (sky_cool 5)."""
    rng = np.random.default_rng(seed)
    w = aniso(P, 110.0, 30.0, seed)
    d = aniso(P, 60.0, 60.0, seed + 1)
    cv = np.full((P, P), C('sky_cool', 4), np.int32)
    cv[_no_specks(d < -0.4, 80)] = C('water_cool', 4)
    cv[_no_specks(w > 0.6, 80)] = C('snow_cool', 3)
    cv[_no_specks(w > 1.2, 60)] = C('snow_cool', 4)
    T = Torus(cv)
    c_ = T.cv
    for _ in range(P * P // 7000):
        y, x = float(rng.integers(0, P)), float(rng.integers(0, P))
        a = rng.uniform(0, np.pi)
        for _j in range(int(rng.integers(20, 60))):
            a += rng.normal(0, 0.25)
            y += np.sin(a)
            x += np.cos(a)
            for Y, X in T.at(int(y), int(x)):
                if 1 <= Y < c_.shape[0] and 0 <= X < c_.shape[1]:
                    c_[Y, X] = C('water_cool', 2)
                    if c_[Y - 1, X] != C('water_cool', 2):
                        c_[Y - 1, X] = C('sky_cool', 5)
    return T.crop()


PAINTERS = {'lawn': lawn, 'dirt': dirt, 'water': water, 'face_strip': face_strip,
            'snow': snow, 'snow_trod': snow_trod, 'moraine': moraine, 'ice': ice}


def seam_error(f: np.ndarray) -> float:
    """How unlike a fill's wrapped edges are its inner rows and columns (0 for a perfect torus is
    not expected: neighbouring rows differ anyway). Returns the share of texels on the wrap seam
    that differ from their neighbour across it, divided by the same share one row inside."""
    across = np.mean(f[0] != f[-1]) + np.mean(f[:, 0] != f[:, -1])
    inside = np.mean(f[1] != f[0]) + np.mean(f[:, 1] != f[:, 0])
    return float(across / max(1e-9, inside))

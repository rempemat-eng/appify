"""Transition tiles for the terrain kit: one material laid over another on the dual grid.

docs/world-editor.md, "Transitions". The logical grid holds one material per cell (24 texels). The
picture is drawn on a second grid offset by half a cell: each display tile is centred on a cell
corner and shows a quarter of each of the four cells round it, so its look depends on a 4-bit mask
(which of NW, NE, SW, SE hold the upper material): 16 masks, 14 of them transitions. The soft
grid's outline (softgrid.round_corners, then lumps) runs along the cell lines through the tile's
middle, so its rounded corners sit inside one tile and every outline crosses a tile's border at the
middle of a cell edge.

Seams. Any tile must sit next to any neighbour, so within CALM texels of its borders everything
is canonical. The outline lies flat at the crossing's profile offset (OFFS, chosen per crossing
by a hash of the cell edge, so neighbours agree and the rim does not pinch back to the cell line
every cell); no random feature (tuft, lobe, pebble, blade, crumb) comes within CALM + GUARD; and the
deterministic bands (lip, shadow rows, frayed darkening) are what that flat edge gives. A mask's
tiles are its crossing profiles times its variants (`layout`). Between the borders each tile lumps
and dresses its edge freely.

A tile does not store colours. Each texel is an operation on the two fills under it (the upper
material's and whatever lies below), so a tile fits any position of the periodic fills and any
lower material of its class:

    OP_KEEP   0  show what is below unchanged
    OP_UPPER  1  the upper material's fill, stepped `delta` tones along its own ramp
    OP_DELTA  2  what is below, stepped `delta` tones (a shadow, a lit lip on the lower ground)
    OP_ABS    3  an absolute palette code (a tuft's blade, a pebble, a crumb)

The painters here follow softground.sunken_edge and softground.dirt's edge crumbs (same depths,
rates and tones), drawing into that operation form instead of codes.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from scripts.art.native import softgrid as SG
from scripts.art.native import softground as GD
from scripts.art.native.palette import C, step

CELL = 24
HALF = CELL // 2
CALM = 2            # texels each side of a tile border kept canonical
RAMP = 4            # then the lumps grow back over this many texels
OP_KEEP, OP_UPPER, OP_DELTA, OP_ABS = 0, 1, 2, 3
BITS = {'nw': 1, 'ne': 2, 'sw': 4, 'se': 8}
N = 4 * CELL        # the working canvas: 4 x 4 cells, the tile in its middle
T0, T1 = CELL + HALF, 3 * CELL - HALF     # the tile's texels in the canvas (36 .. 60)


def mask_cells(k: int) -> np.ndarray:
    """The 4 x 4 cells round a tile of mask k: each quadrant's value carried straight outwards, so
    every edge leaves the tile straight (canonical at the borders)."""
    q = np.array([[k & 1, (k >> 1) & 1], [(k >> 2) & 1, (k >> 3) & 1]], bool)
    return np.kron(q, np.ones((2, 2), bool))


REACH = 2           # the edge bands look this far across the outline (two shadow rows), so the
                    # outline itself is held flat this much further than the canonical strip


def axis_weight(n: int = N) -> np.ndarray:
    """Per axis: 0 within CALM + REACH texels of a tile border line, rising to 1 over RAMP."""
    i = np.arange(n) + 0.5
    d = np.abs(((i - HALF) % CELL + CELL / 2) % CELL - CELL / 2)
    return np.clip((d - CALM - REACH) / RAMP, 0, 1)


# Where an outline crosses a tile border (the middle of a cell edge) it lies flat for CALM texels
# at one of a few offsets from the cell line, chosen per crossing by a hash of its place (Wang-style
# edge profiles): neighbouring tiles agree because they share the crossing, and the outline no
# longer pinches back to the cell line once a cell.
OFFS = (0.0, -2.0, 2.0)          # texels; positive moves the outline into the upper material
SIDES = ('n', 'e', 's', 'w')


def crossings(k: int) -> tuple:
    """Which of the tile's borders (N, E, S, W) an outline crosses for mask k."""
    nw, ne, sw, se = k & 1, (k >> 1) & 1, (k >> 2) & 1, (k >> 3) & 1
    return (nw != ne, ne != se, sw != se, nw != sw)


def layout(variants: int):
    """Every tile of a transition in atlas order: (index, mask, profiles (n, e, s, w), variant).
    A mask's tiles are its profile combinations (len(OFFS) per crossing) times the variants; a
    border it does not cross has profile 0."""
    out, idx = [], 0
    E = len(OFFS)
    for k in range(1, 15):
        cr = [i for i, c in enumerate(crossings(k)) if c]
        for combo in range(E ** len(cr)):
            prof = [0, 0, 0, 0]
            c = combo
            for i in reversed(cr):
                prof[i] = c % E
                c //= E
            for v in range(variants):
                out.append((idx, k, tuple(prof), v))
                idx += 1
    return out


def mask_base(variants: int) -> list:
    """The index of each mask's first tile (the shader computes the same)."""
    base, b, E = [0] * 16, 0, len(OFFS)
    for k in range(1, 15):
        base[k] = b
        b += E ** sum(crossings(k)) * variants
    return base


ATLAS_COLS = 64                  # tiles across a transition's atlas block


GUARD = 5           # random features (lobes, tufts, pebbles, crumbs) keep this much further off,
                    # so the morphology that tidies them cannot reach the canonical strip


def calm_weight(n: int = N, extra: float = 0.0) -> np.ndarray:
    """0 within CALM (+ extra) texels of a tile border line (texel x or y = HALF mod CELL), rising
    to 1 over RAMP texels: the share of free variation allowed at each texel."""
    i = np.arange(n) + 0.5
    d = np.abs(((i - HALF) % CELL + CELL / 2) % CELL - CELL / 2)
    w1 = np.clip((d - CALM - extra) / RAMP, 0, 1)
    return np.minimum.outer(w1, w1)


def free_zone(n: int = N) -> np.ndarray:
    """Where a random feature's every texel may go: more than CALM + GUARD from any tile border."""
    return calm_weight(n, GUARD) > 0


class Ops:
    """The canvas as operations: `own` 0 upper fill, 1 lower (keep), 2 absolute; `dl` tone delta;
    `ab` absolute code. `code()` resolves them against the fills at the working position."""

    def __init__(self, upper_m, fill_u, fill_l):
        self.fu, self.fl = fill_u, fill_l
        self.own = np.where(upper_m, 0, 1).astype(np.int8)
        self.dl = np.zeros(upper_m.shape, np.int32)
        self.ab = np.full(upper_m.shape, -1, np.int32)

    def code(self):
        base = np.where(self.own == 0, self.fu, self.fl)
        c = np.where(self.dl != 0, step(base, self.dl), base)
        return np.where(self.own == 2, self.ab, c)

    def shift(self, sel, d):
        c = self.code()
        sel = sel & (c >= 0) & (c % 8 < 6)
        a = sel & (self.own == 2)
        self.ab[a] = step(self.ab[a], d)
        self.dl[sel & (self.own < 2)] += d

    def put(self, y, x, code, ok=None):
        H, W = self.own.shape
        if 0 <= y < H and 0 <= x < W and (ok is None or ok[y, x]):
            self.own[y, x], self.ab[y, x] = 2, int(code)

    def stamp(self, y, x, shape, base, ok=None):
        """softground.stamp: base None steps what is there, else absolute codes."""
        H, W = self.own.shape
        for dy, dx, dt in shape:
            Y, X = y + dy, x + dx
            if not (0 <= Y < H and 0 <= X < W) or (ok is not None and not ok[Y, X]):
                continue
            if base is None:
                one = np.zeros(self.own.shape, bool)
                one[Y, X] = True
                self.shift(one, dt)
            else:
                self.put(Y, X, step(base, dt))

    def pebble(self, y, x, rng, big=False, fam='stone', ok=None):
        """softground.pebble into operations."""
        H, W = self.own.shape
        w = int(rng.integers(5, 8)) if big else int(rng.integers(3, 5))
        hh = max(2, int(round(w * rng.uniform(0.55, 0.75))))
        fam = fam if rng.random() < 0.6 else fam + '_warm'
        for dy in range(-1, hh + 1):
            for dx in range(-1, w + 1):
                Y, X = y + dy, x + dx
                if not (0 <= Y < H and 0 <= X < W) or (ok is not None and not ok[Y, X]):
                    continue
                inside = 0 <= dy < hh and 0 <= dx < w and not ((dy in (0, hh - 1)) and (dx in (0, w - 1)))
                if inside:
                    u, v = dx / max(1, w - 1), dy / max(1, hh - 1)
                    tt = 4 if (u + v < 0.55) else (3 if u + v < 1.25 else 2)
                    if big and (dy == hh - 1 or dx == w - 1):
                        tt = 1
                    self.put(Y, X, C(fam, tt))
                elif dy == hh and 0 < dx <= w:
                    one = np.zeros(self.own.shape, bool)
                    one[Y, X] = True
                    self.shift(one, -1)

    def encode(self, sl) -> np.ndarray:
        """The tile's texels as (op, value): value is delta + 128 for OP_UPPER and OP_DELTA, the
        code for OP_ABS."""
        own, dl, ab = self.own[sl], self.dl[sl], self.ab[sl]
        op = np.where(own == 2, OP_ABS, np.where(own == 0, OP_UPPER, np.where(dl != 0, OP_DELTA, OP_KEEP)))
        val = np.where(op == OP_ABS, ab, dl + 128)
        val = np.where(op == OP_KEEP, 0, val)
        return np.stack([op, val], -1).astype(np.int32)


def soft_lower(cells: np.ndarray, seed: int, r_out=SG.R_TURN_OUT, r_in=SG.R_TURN_IN, amp=SG.AMP,
               prof=(0, 0, 0, 0)) -> np.ndarray:
    """softgrid.soften with its lumps replaced, near each tile border, by the crossing's flat
    profile offset (texel mask, True = lower)."""
    m = SG.round_corners(SG.texels(cells, N, N), r_out * CELL, r_in * CELL)
    p = 4
    mp = np.pad(m, p, mode='edge')
    sd = np.where(mp, ndi.distance_transform_edt(mp) - 0.5, 0.5 - ndi.distance_transform_edt(~mp))[p:-p, p:-p]
    wa = axis_weight()
    wy, wx = wa[:, None], wa[None, :]
    mid = N / 2
    xs = np.arange(N)[None, :] + 0.5
    ys = np.arange(N)[:, None] + 0.5
    # a profile offset moves the outline into the upper material: the lower plan grows
    offx = np.where(xs < mid, OFFS[prof[3]], OFFS[prof[1]])
    offy = np.where(ys < mid, OFFS[prof[0]], OFFS[prof[2]])
    disp = SG.lumps(N, N, seed, amp) * np.minimum(wx, wy) + (1 - wx) * offx + (1 - wy) * offy
    m = sd + disp > 0
    return SG.clean(m)


def sunken(k: int, fill_u: np.ndarray, fill_l: np.ndarray, seed: int, prof=(0, 0, 0, 0), lobes: float = 1.0,
           tufts: float = 1.0, stones: float = 1.0, crumbs: bool = True) -> np.ndarray:
    """Turf (upper, the cells set in k) over a sunken surface (a path, a bed's soil): the edge of
    softground.sunken_edge on the soft grid of a path network (softgrid.shape of the lower plan with
    the route turns), as one tile's operations (CELL x CELL x 2)."""
    rng = np.random.default_rng(seed)
    lower_cells = ~mask_cells(k)
    m = soft_lower(lower_cells, seed, prof=prof)            # the path's soft outline
    turf = ~m
    ops = Ops(turf, fill_u, fill_l)
    free = free_zone()
    w = calm_weight()
    wf = calm_weight(extra=GUARD)
    H = W = N
    # lobes of turf over the edge, on every side (their depth fades out at the borders)
    dt = ndi.distance_transform_edt(m)
    dep = np.clip((GD.fbm(H, W, 15.0, seed + 3) - 0.3) * 15.0 * lobes, 0, 5.5) * wf
    near = ndi.binary_dilation(turf, iterations=6)
    lob = m & (dt <= dep) & near & (dep > 0.5)
    m2 = SG.clean(m & ~lob, min_area=1.0)
    lob = m & ~m2
    _, (iy, ix) = ndi.distance_transform_edt(~turf, return_indices=True)
    ops.own[lob] = 0
    ops.dl[lob] = ops.dl[iy[lob], ix[lob]]
    turf2 = (turf | lob) & ~m2
    # north edge: the lobes' underside a tone down, then two rows of shadow on the dirt
    und = turf2 & GD.down(m2, -1)
    ops.shift(und, -1)
    sh1 = m2 & GD.down(turf2, 1)
    sh2 = m2 & GD.down(turf2, 2) & ~sh1
    yy, xx = np.mgrid[0:H, 0:W]
    ops.shift(sh1, -1)
    ops.shift(sh2 & (((xx + yy) % 2) == 0), -1)
    # west turf shades a texel of dirt; east turf's west-facing side is lit
    ops.shift(m2 & GD.right(turf2, 1) & ~sh1, -1)
    ops.shift(turf2 & GD.right(m2, 1) & ~und & ~GD.down(m2, 1), 1)
    # south edge: the turf's first row lit
    s_lip = turf2 & GD.down(m2, 1)
    ops.shift(s_lip, 1)
    # the frayed last texels of turf a tone down, broken by a slow field (whole at the borders)
    fr = turf2 & ndi.binary_dilation(m2, iterations=2) & ~und & ~s_lip & \
        ((GD.nz(H, W, 7.0, seed + 5) > 0.35) | (w < 1))
    if tufts > 0:
        ops.shift(fr, -1)
    # tufts on the turf's edge leaning out over the dirt (about one in 10 px of edge)
    bnd = turf2 & ndi.binary_dilation(m2, structure=GD.CROSS) & ~und
    ys, xs = np.nonzero(bnd)
    taken = np.zeros((H, W), bool)
    for kk in rng.permutation(len(ys))[: int(len(ys) / 6 * tufts)]:
        y, x = int(ys[kk]), int(xs[kk])
        if taken[max(0, y - 4):y + 5, max(0, x - 5):x + 6].any():
            continue
        shp = [(dy, dx, dt_) for (dy, dx, dt_) in GD.tuft_shape(rng, rng.uniform(1.1, 1.7)) if dy < 0]
        if not all(0 <= y + 1 + dy < H and 0 <= x + dx < W and free[y + 1 + dy, x + dx] for dy, dx, _ in shp):
            continue
        taken[y, x] = True
        c0 = ops.code()[y, x]
        base = c0 if c0 % 8 < 6 else C('grass', 3)
        ops.stamp(y + 1, x, shp, step(base, 1))
    # blades hanging over the north edge
    ys, xs = np.nonzero(und)
    for kk in rng.permutation(len(ys))[: int(len(ys) / 16 * tufts)]:
        y, x = int(ys[kk]), int(xs[kk])
        nb, L = int(rng.integers(2, 4)), [int(rng.integers(1, 4)) for _ in range(4)]
        if not all(0 <= y + j < H and 0 <= x + 2 * b < W and free[y + j, x + 2 * b]
                   for b in range(nb) for j in range(0, L[b] + 1)):
            continue
        cc = ops.code()
        base = cc[y - 1, x] if y > 0 and cc[y - 1, x] % 8 < 6 else C('grass', 3)
        for b in range(nb):
            for j in range(1, L[b] + 1):
                ops.put(y + j, x + 2 * b, step(base, -1 if j == L[b] else 0), m2)
    # stones on the edge, straddling it
    e = m2 & ndi.binary_dilation(turf2, structure=GD.CROSS)
    ys, xs = np.nonzero(e)
    for kk in rng.permutation(len(ys))[: int(len(ys) / 90 * stones)]:
        y, x = int(ys[kk]), int(xs[kk])
        if not free[max(0, y - 3):y + 6, max(0, x - 4):x + 8].all():
            continue
        ops.pebble(y - 1, x - 2, rng, big=rng.random() < 0.45)
    # the dirt's dark crumbs along its edge (softground.dirt), 1 to 2 px
    if crumbs:
        edge = m2 & ~ndi.binary_erosion(m2, iterations=4) & free
        ey, ex = np.nonzero(edge)
        for kk in rng.permutation(len(ey))[:len(ey) // 24]:
            y, x = int(ey[kk]), int(ex[kk])
            if ops.own[y, x] != 1:
                continue
            ops.put(y, x, C('path', 1))
            if rng.random() < 0.5 and x + 1 < W and free[y, x + 1] and ops.own[y, x + 1] == 1:
                ops.put(y, x + 1, C('path', 2))
    sl = (slice(T0, T1), slice(T0, T1))
    return ops.encode(sl)


PAINTERS = {'sunken': sunken}

"""Transition tiles for the terrain kit: one material laid over another on the dual grid.

docs/world-editor.md, "Transitions". The logical grid holds one material per cell (24 texels). The
picture is drawn on a second grid offset by half a cell: each display tile is centred on a cell
corner (a grid vertex) and shows a quarter of each of the four cells round it, so its look depends
on a 4-bit mask (which of NW, NE, SW, SE hold the upper material): 16 masks, 14 transitions.

The outline. It runs along the cell lines through the tile's middle and is displaced, along every
cell edge, by a lump profile: one of PROFILES, a smooth curve over the whole cell edge (24 texels,
lumps 12 to 24 long and 1 to 3 deep) that is zero at both of its vertices, chosen by a hash of that
cell edge's place. A cell edge is split between two display tiles at its middle (where it crosses
their shared border), and both tiles draw the same curve, so lumps run across tile borders without
a seam. At the vertex in a tile's middle the curves meet at zero, and the corners are rounded there
(outer R_OUT, inner R_IN, within CORNER texels of the vertex). A mask's tiles are the profile
combinations of the borders it crosses (`layout`).

Everything in a tile is a deterministic function of its mask and its crossings' profiles, so a
neighbour always agrees at the shared border (test_kit checks the border strips). What is random
(tufts, pebbles, hanging blades) is not in the tiles: it is edge dressing, decals placed along the
cell edges by a hash (dressing.py), drawn over the ground in Godot and in compose.py alike.

A tile does not store colours. Each texel is an operation on the two fills under it (the upper
material's and whatever lies below), so a tile fits any position of the periodic fills and any
lower material of its class:

    OP_KEEP   0  show what is below unchanged
    OP_UPPER  1  the upper material's fill, stepped `delta` tones along its own ramp
    OP_DELTA  2  what is below, stepped `delta` tones (a shadow, a lit lip on the lower ground)
    OP_ABS    3  an absolute palette code (unused by `sunken`; kept for kerbs and banks)

`sunken` follows softground.sunken_edge's bands (the turf's dark underside and two rows of shadow
on the dirt under a north lip, the lit south lip, the shade at a west edge and the lit east turf,
the frayed last texels of turf), drawing into that operation form instead of codes.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from scripts.art.native import softgrid as SG
from scripts.art.native import softground as GD
from scripts.art.native.palette import step

CELL = 24
HALF = CELL // 2
CALM = 2            # texels each side of a tile border the test holds canonical
OP_KEEP, OP_UPPER, OP_DELTA, OP_ABS = 0, 1, 2, 3
N = 4 * CELL        # the working canvas: 4 x 4 cells, the tile in its middle
T0, T1 = CELL + HALF, 3 * CELL - HALF     # the tile's texels in the canvas (36 .. 60)
MID = N / 2         # the tile's vertex in the canvas
SIDES = ('n', 'e', 's', 'w')
ATLAS_COLS = 64     # tiles across a transition's atlas block
R_OUT = 8.0         # corner radii, texels (eastward-edges.md 1.5a: paths turn at 0.4 / 0.25 cell;
R_IN = 8.0          # 8 of 24 is what fits a tile with its border strips left canonical)
CORNER = 8          # corners are rounded within this many texels of the vertex


def _curve(u: np.ndarray, k: int) -> np.ndarray:
    s = np.sin(np.pi * u)
    return [
        1.6 * s ** 2,                                   # a low lump into the turf
        -2.6 * s ** 2,                                  # a turf lobe over the path
        2.2 * np.sin(2 * np.pi * u) * s ** 0.5,         # out, then in
        2.8 * np.sin(np.pi * u ** 1.6) ** 2,            # a lump leaning east (south)
    ][k]


NPROF = 4


def profile_curve(k: int, t) -> np.ndarray:
    """Profile k's displacement (texels, positive moves the outline into the upper material) at t
    texels from the cell edge's middle; zero at its vertices (|t| >= HALF)."""
    t = np.asarray(t, float)
    u = np.clip((t + HALF) / CELL, 0.0, 1.0)
    return np.where(np.abs(t) >= HALF, 0.0, _curve(u, k))


def curve_table() -> list:
    """Each profile at the 24 texel centres along a cell edge (t = -11.5 .. 11.5), for Godot."""
    t = np.arange(CELL) - HALF + 0.5
    return [[round(float(v), 4) for v in profile_curve(k, t)] for k in range(NPROF)]


def mask_cells(k: int) -> np.ndarray:
    """The 4 x 4 cells round a tile of mask k: each quadrant's value carried straight outwards."""
    q = np.array([[k & 1, (k >> 1) & 1], [(k >> 2) & 1, (k >> 3) & 1]], bool)
    return np.kron(q, np.ones((2, 2), bool))


def crossings(k: int) -> tuple:
    """Which of the tile's borders (N, E, S, W) an outline crosses for mask k."""
    nw, ne, sw, se = k & 1, (k >> 1) & 1, (k >> 2) & 1, (k >> 3) & 1
    return (nw != ne, ne != se, sw != se, nw != sw)


def layout(variants: int = 1):
    """Every tile of a transition in atlas order: (index, mask, profiles (n, e, s, w), variant).
    A mask's tiles are its profile combinations (NPROF per crossing); a border it does not cross
    has profile 0."""
    out, idx = [], 0
    for k in range(1, 15):
        cr = [i for i, c in enumerate(crossings(k)) if c]
        for combo in range(NPROF ** len(cr)):
            prof = [0, 0, 0, 0]
            c = combo
            for i in reversed(cr):
                prof[i] = c % NPROF
                c //= NPROF
            for v in range(variants):
                out.append((idx, k, tuple(prof), v))
                idx += 1
    return out


def mask_base(variants: int = 1) -> list:
    """The index of each mask's first tile (the shader computes the same)."""
    base, b = [0] * 16, 0
    for k in range(1, 15):
        base[k] = b
        b += NPROF ** sum(crossings(k)) * variants
    return base


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

    def encode(self, sl) -> np.ndarray:
        """The tile's texels as (op, value): value is delta + 128 for OP_UPPER and OP_DELTA, the
        code for OP_ABS."""
        own, dl, ab = self.own[sl], self.dl[sl], self.ab[sl]
        op = np.where(own == 2, OP_ABS, np.where(own == 0, OP_UPPER, np.where(dl != 0, OP_DELTA, OP_KEEP)))
        val = np.where(op == OP_ABS, ab, dl + 128)
        val = np.where(op == OP_KEEP, 0, val)
        return np.stack([op, val], -1).astype(np.int32)


def displacement(k: int, prof) -> np.ndarray:
    """The outline's displacement over the working canvas: along the horizontal cell line through
    the vertex by the W and E crossings' curves, along the vertical one by the N and S crossings',
    blended only near the vertex's diagonals (where both curves are close to zero)."""
    cr = crossings(k)
    xs = np.arange(N) + 0.5
    # horizontal line: x < MID is the W crossing's cell edge (its middle at T0), x >= MID the E one's
    dh = np.where(xs < MID, profile_curve(prof[3], xs - T0) * cr[3], profile_curve(prof[1], xs - T1) * cr[1])
    dv = np.where(xs < MID, profile_curve(prof[0], xs - T0) * cr[0], profile_curve(prof[2], xs - T1) * cr[2])
    ady = np.abs(xs[:, None] - MID)
    adx = np.abs(xs[None, :] - MID)
    a = np.clip((ady - adx) / 4.0 + 0.5, 0, 1)      # 1 near the vertical line, 0 near the horizontal
    return dh[None, :] * (1 - a) + dv[:, None] * a


def soft_lower(k: int, prof) -> np.ndarray:
    """The lower material's soft outline for mask k (texel mask, True = lower): the cell lines
    displaced by the crossings' lump curves, the corners rounded at the vertex, no one-texel teeth."""
    lower = SG.texels(~mask_cells(k), N, N)
    p = 4
    mp = np.pad(lower, p, mode='edge')
    sd = np.where(mp, ndi.distance_transform_edt(mp) - 0.5, 0.5 - ndi.distance_transform_edt(~mp))[p:-p, p:-p]
    m = SG.clean(sd + displacement(k, prof) > 0, min_area=1.0)
    # the corners rounded at the vertex only (nothing within CORNER + the bands' reach of a border
    # changes, so the border strips stay what a straight edge gives)
    rounded = SG.round_corners(m, R_OUT, R_IN)
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    near = (np.abs(yy - MID) < CORNER) & (np.abs(xx - MID) < CORNER)
    return np.where(near, rounded, m)


def sunken(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), fray: bool = True) -> np.ndarray:
    """Turf (upper, the cells set in k) over a sunken surface (a path, a bed's soil): the bands of
    softground.sunken_edge along the lumped outline, as one tile's operations (CELL x CELL x 2)."""
    m2 = soft_lower(k, prof)
    turf2 = ~m2
    ops = Ops(turf2, fill_u, fill_l)
    # north edge: the turf's underside a tone down, then a row of shadow on the dirt (softground's
    # second row is a checker; along a whole edge it read as a sawtooth, so it is left out)
    und = turf2 & GD.down(m2, -1)
    ops.shift(und, -1)
    sh1 = m2 & GD.down(turf2, 1)
    ops.shift(sh1, -1)
    # west turf shades a texel of dirt; east turf's west-facing side is lit
    ops.shift(m2 & GD.right(turf2, 1) & ~sh1, -1)
    ops.shift(turf2 & GD.right(m2, 1) & ~und & ~GD.down(m2, 1), 1)
    # south edge: the turf's first row lit
    s_lip = turf2 & GD.down(m2, 1)
    ops.shift(s_lip, 1)
    # the last texels of turf at the edge a tone down (the grass thinning over the edge)
    if fray:
        fr = turf2 & ndi.binary_dilation(m2, iterations=2) & ~und & ~s_lip
        ops.shift(fr, -1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


PAINTERS = {'sunken': sunken}

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
from scripts.art.native.palette import C, FI, step

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


def _bank_marks(prof: int) -> np.ndarray:
    """The bank face's clods along one cell edge, a function of its profile only (so the two tiles
    sharing the cell edge agree): per texel along it (t = -12 .. 11), 1 where a clod begins (lit),
    -1 where one ends (dark), 0 inside."""
    rng = np.random.default_rng(4100 + prof)
    out = np.zeros(CELL, np.int32)
    x = int(rng.integers(0, 4))
    while x < CELL:
        L = int(rng.integers(4, 8))
        out[x] = 1
        if x + L - 1 < CELL:
            out[x + L - 1] = -1
        x += L
    return out


def bank(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), side_w: int = 3) -> np.ndarray:
    """Turf (upper) over water (lower), softground.water's banks on the dual grid. Under a north
    lip: an earth face 3 px (lit top row, clods along it from the cell edge's profile, a dark wet
    bottom row), the 1 px very light waterline, then two rows of shade on the water. On a south
    shore: the turf's lip lit and the shallows lit, 2 tones at the edge and 1 for two more. On a
    west or east shore of a north-south run: a narrow earth wall seen edge-on (in shade facing east,
    lit facing west) with the waterline at its foot. All within 7 texels of the outline, so the
    tile below never needs to know."""
    m2 = soft_lower(k, prof)                      # the water
    land = ~m2
    ops = Ops(land, fill_u, fill_l)
    rt = GD.runs_from_top(m2)                     # 1 on the water's first row under land
    # which bank each texel may carry is read from the cells, not the texels (so a corner's bulge
    # never turns into a bank that a neighbour would not draw): a north bank under a horizontal cell
    # edge with land north and water south; a wall beside a vertical one
    q = [bool((k >> b) & 1) for b in range(4)]    # nw, ne, sw, se (True = land)
    xs_ = np.arange(N) + 0.5
    left = (xs_ < MID)[None, :]
    top = (xs_ < MID)[:, None]
    nb_cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    westwall_cfg = np.where(top, q[0] and not q[1], q[2] and not q[3]).astype(bool)     # land west, water east
    eastwall_cfg = np.where(top, q[1] and not q[0], q[3] and not q[2]).astype(bool)     # land east, water west
    top_of_run = m2 & GD.down(land, 1)
    col_bank = np.zeros_like(m2)
    for d in range(0, 6):
        col_bank |= GD.down(top_of_run, d) & m2
    yy_ = np.arange(N)[:, None] + 0.5
    col_bank &= (rt <= 6) & nb_cfg & (yy_ > MID - 5) & (yy_ < MID + 10)     # only under the horizontal cell line
    xs = np.arange(N) + 0.5
    # which cell edge each column's bank belongs to, and t along it
    t = np.where(xs < MID, xs - T0, xs - T1).astype(int) + HALF
    t = np.clip(t, 0, CELL - 1)
    pw, pe = _bank_marks(prof[3]), _bank_marks(prof[1])
    marks = np.where(xs < MID, pw[t], pe[t])[None, :].repeat(N, 0)
    face1 = col_bank & (rt == 1)
    face2 = col_bank & (rt == 2)
    face3 = col_bank & (rt == 3)
    wline = col_bank & (rt == 4)
    shade = col_bank & (rt >= 5) & (rt <= 6)
    for sel, code in ((face1, C('earth', 3)), (face3, C('earth_cool', 1)), (wline, C('water', 5))):
        ops.own[sel] = 2
        ops.ab[sel] = code
    ops.own[face2] = 2
    ops.ab[face2] = np.where(marks[face2] > 0, C('earth', 3), np.where(marks[face2] < 0, C('earth_cool', 1), C('earth', 2)))
    ops.shift(shade & (rt == 5), -2)
    ops.shift(shade & (rt == 6), -1)
    # the turf's last row over the bank a tone down (its underside)
    ops.shift(land & GD.down(m2, -1), -1)
    nb = col_bank
    # east and west shores of north-south runs: a narrow wall seen edge-on
    westl = np.zeros_like(m2)
    eastl = np.zeros_like(m2)
    for kk in range(1, side_w + 1):
        westl |= GD.right(land, kk)
        eastl |= GD.right(land, -kk)
    vert = m2 & (westl ^ eastl) & ~nb & (np.abs(xs_[None, :] - MID) < side_w + 4)     # only beside the vertical cell line
    wb, eb = vert & westl & westwall_cfg, vert & eastl & eastwall_cfg
    vert = wb | eb
    ops.own[wb] = 2
    ops.ab[wb] = C('earth', 2)
    ops.ab[wb & GD.right(land, 1)] = C('earth', 1)
    ops.own[eb] = 2
    ops.ab[eb] = C('earth_warm', 3)
    ops.ab[eb & GD.right(land, -1)] = C('earth_warm', 4)
    for b_, d_ in ((wb, 1), (eb, -1)):
        wl_ = m2 & ~vert & ~nb & GD.right(b_, d_)
        ops.own[wl_] = 2
        ops.ab[wl_] = C('water', 5)
    # south (and remaining) shores: the turf's lip lit, the shallows lit
    walls = wb | eb | nb
    dist = ndi.distance_transform_edt(m2)
    shal = m2 & ~walls & ~ndi.binary_dilation(walls, iterations=1) & (ops.own == 1)
    ops.shift(shal & (dist <= 1.5), 2)
    ops.shift(shal & (dist > 1.5) & (dist <= 3.5), 1)
    s_lip = land & GD.down(m2, 1)
    ops.shift(s_lip, 1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def plain(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0)) -> np.ndarray:
    """One surface running into another of the same look (worn ground into a path): the lumped
    outline and nothing else, so where the two fills are the same the join does not show."""
    m2 = soft_lower(k, prof)
    ops = Ops(~m2, fill_u, fill_l)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def _broken(n: int = N) -> np.ndarray:
    """A side wall's darkest line is broken (eastward-edges.md 3.3): a fixed rhythm down the rows,
    so it never depends on anything a neighbour could disagree on."""
    return ((np.arange(n)[:, None] % 5) != 4) & np.ones((1, n), bool)


def lip(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), earth: str = 'earth') -> np.ndarray:
    """A raised tier's turf (upper) over its own face (lower, a strip fill indexed by depth below
    the rim): the turf's last row a step darker and a lit row two behind it; under the lumped
    outline the rim line and the under-lip line (the face's darkest) follow it (eastward-edges.md
    2.2, 3.1). Where the turf meets a face beside it (an inner corner), the face's side line."""
    m2 = soft_lower(k, prof)                  # the face
    turf = ~m2
    ops = Ops(turf, fill_u, fill_l)
    ec = earth + '_cool' if earth + '_cool' in FI else earth
    # features keyed to the cells (so the border strips stay canonical): the rim along a
    # horizontal cell line with turf north and face south, the side line along a vertical one
    q = [bool((k >> b) & 1) for b in range(4)]          # True = turf
    xs = np.arange(N) + 0.5
    yv, xv = xs[:, None], xs[None, :]
    rim_cfg = np.where(xv < MID, q[0] and not q[2], q[1] and not q[3]).astype(bool) & (yv > MID - 7) & (yv < MID + 6)
    side_cfg = np.where(yv < MID, q[0] != q[1], q[2] != q[3]).astype(bool) & (np.abs(xv - MID) < 6)
    lipr = turf & GD.down(m2, -1) & rim_cfg
    ops.shift(lipr, -1)
    lit = turf & GD.down(m2, -3) & ~GD.down(m2, -1) & ~GD.down(m2, -2) & rim_cfg
    ops.shift(lit, 1)
    rim = m2 & GD.down(turf, 1) & rim_cfg
    under = m2 & GD.down(turf, 2) & ~rim & rim_cfg
    for sel, code in ((rim, C(earth, 1)), (under, C(ec, 0))):
        ops.own[sel] = 2
        ops.ab[sel] = code
    side = m2 & (GD.right(turf, 1) | GD.right(turf, -1)) & ~rim & ~under & side_cfg
    ops.own[side] = 2
    ops.ab[side] = C(ec, 0)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def foot(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), earth: str = 'earth') -> np.ndarray:
    """A face (upper) over the ground at its foot (lower): along the bottom, the face's dark foot
    band follows the lumped outline and the ground's first row is in its shade; at the face's west
    and east ends a side band seen edge-on, lit facing west and in shade facing east, with the
    picture's darkest line, broken, on its outside (eastward-edges.md 3.2, 3.3)."""
    m2 = soft_lower(k, prof)                  # the ground below
    face = ~m2
    ops = Ops(face, fill_u, fill_l)
    ec = earth + '_cool' if earth + '_cool' in FI else earth
    q = [bool((k >> b) & 1) for b in range(4)]          # nw, ne, sw, se (True = face)
    xs = np.arange(N) + 0.5
    top = (xs < MID)[:, None]
    # the foot: along horizontal cell lines with the face north of the ground
    left = (xs < MID)[None, :]
    foot_cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    yv = (np.arange(N) + 0.5)[:, None]
    foot_cfg = foot_cfg & (yv > MID - 6) & (yv < MID + 4)     # only along the cell line, never up or down a side
    f1 = face & GD.down(m2, -1) & foot_cfg
    f2 = face & GD.down(m2, -2) & ~f1 & foot_cfg
    f3 = face & GD.down(m2, -3) & ~f1 & ~f2 & foot_cfg
    for sel, code in ((f1, C(ec, 0)), (f2, C(ec, 0)), (f3, C(earth, 1))):
        ops.own[sel] = 2
        ops.ab[sel] = code
    ops.shift(m2 & GD.down(face, 1) & foot_cfg, -1)          # the ground's first row in the face's shade
    # the side bands at the face's ends, beside the vertical cell line
    east_end = np.where(top, q[0] and not q[1], q[2] and not q[3]).astype(bool)    # face west, ground east
    west_end = np.where(top, q[1] and not q[0], q[3] and not q[2]).astype(bool)    # face east, ground west
    near = np.abs(xs[None, :] - MID) < 6
    out_e = face & GD.right(m2, -1) & east_end & near & ~f1 & ~f2
    band_e = face & (GD.right(m2, -2) | GD.right(m2, -3)) & ~GD.right(m2, -1) & east_end & near & ~f1 & ~f2
    out_w = face & GD.right(m2, 1) & west_end & near & ~f1 & ~f2
    band_w = face & (GD.right(m2, 2) | GD.right(m2, 3)) & ~GD.right(m2, 1) & west_end & near & ~f1 & ~f2
    ops.shift(band_e, -1)
    ops.shift(band_w, 1)
    for sel in (out_e & _broken(), out_w & _broken()):
        ops.own[sel] = 2
        ops.ab[sel] = C(ec, 0)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def tier_side(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), earth: str = 'earth',
              band: int = 3) -> np.ndarray:
    """A raised tier's ground (upper) beside or behind ground of a lower tier (lower): on its west
    and east sides a wall seen edge-on, `band` texels on the lower side (lit facing west, in shade
    facing east, the darkest line broken on its outside) and the turf's edge a step darker; along
    its back (north) edge the turf's first row lit and a dark crease on the lower ground."""
    m2 = soft_lower(k, prof)                  # the lower tier
    up = ~m2
    ops = Ops(up, fill_u, fill_l)
    ec = earth + '_cool' if earth + '_cool' in FI else earth
    ew = earth + '_warm' if earth + '_warm' in FI else earth
    q = [bool((k >> b) & 1) for b in range(4)]          # True = raised
    xs = np.arange(N) + 0.5
    top = (xs < MID)[:, None]
    left = (xs < MID)[None, :]
    raised_east = np.where(top, q[1] and not q[0], q[3] and not q[2]).astype(bool)   # wall faces west: lit
    raised_west = np.where(top, q[0] and not q[1], q[2] and not q[3]).astype(bool)   # wall faces east: shade
    near = np.abs(xs[None, :] - MID) < band + 5
    wl = np.zeros_like(m2)
    wr = np.zeros_like(m2)
    for kk in range(1, band + 1):
        wl |= GD.right(up, -kk)                # raised ground kk texels to the east
        wr |= GD.right(up, kk)                 # raised ground kk texels to the west
    wall_w = m2 & wl & raised_east & near      # lit
    wall_e = m2 & wr & raised_west & near      # in shade
    ops.own[wall_w] = 2
    ops.ab[wall_w] = C(ew, 3)
    ops.own[wall_e] = 2
    ops.ab[wall_e] = C(earth, 1)
    out_w = wall_w & ~GD.right(up, -(band - 1)) & ~GD.right(up, -1)
    out_e = wall_e & ~GD.right(up, band - 1) & ~GD.right(up, 1)
    for sel in (out_w & _broken(), out_e & _broken()):
        ops.ab[sel] = C(ec, 0)
    ops.shift(up & (GD.right(m2, 1) | GD.right(m2, -1)) & near & (raised_east | raised_west), -1)
    # the back rim: raised ground south of a horizontal cell line, lower ground north of it
    yv = (np.arange(N) + 0.5)[:, None]
    back_cfg = np.where(left, q[2] and not q[0], q[3] and not q[1]).astype(bool) & (yv > MID - 6) & (yv < MID + 6)
    ops.shift(up & GD.down(m2, 1) & back_cfg, 1)
    crease = m2 & GD.down(up, -1) & back_cfg
    ops.own[crease] = 2
    ops.ab[crease] = C(ec, 1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


PAINTERS = {'sunken': sunken, 'bank': bank, 'plain': plain, 'lip': lip, 'foot': foot, 'tier_side': tier_side}

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
R_OUT = 9.0         # corner radii, texels (eastward-edges.md 1.5a: paths turn at 0.4 / 0.25 cell;
R_IN = 8.0          # 9 and 8 of 24 are what fit a tile with its border strips left canonical: test_kit)
CORNER = 9          # corners are rounded within this many texels of the vertex


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


def bank(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), side_w: int = 0) -> np.ndarray:
    """Turf (upper) over water (lower), softground.water's banks on the dual grid. Under a north
    lip (the only bank that turns a face to the camera): an earth face 6 px (lit top row, clods
    along it from the cell edge's profile, a dark wet bottom row), the 1 px very light waterline,
    then two rows of shade on the water. On every other shore (south, west, east; Matt, 4 Nov) one
    rim and no face: the turf's lip lit, a texel of wet earth, the water's mid tone, lit shallows.
    All within 9 texels of the outline, so the tile below never needs to know. `side_w` is kept for
    old piece files and ignored (the walls seen edge-on it sized are gone)."""
    m2 = soft_lower(k, prof)                      # the water
    land = ~m2
    ops = Ops(land, fill_u, fill_l)
    rt = GD.runs_from_top(m2)                     # 1 on the water's first row under land
    # which bank each texel may carry is read from the cells, not the texels (so a corner's bulge
    # never turns into a bank that a neighbour would not draw): a north bank under a horizontal cell
    # edge with land north and water south
    q = [bool((k >> b) & 1) for b in range(4)]    # nw, ne, sw, se (True = land)
    xs_ = np.arange(N) + 0.5
    left = (xs_ < MID)[None, :]
    nb_cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    top_of_run = m2 & GD.down(land, 1)
    col_bank = np.zeros_like(m2)
    for d in range(0, 6):
        col_bank |= GD.down(top_of_run, d) & m2
    yy_ = np.arange(N)[:, None] + 0.5
    col_bank &= (rt <= 9) & nb_cfg & (yy_ > MID - 5) & (yy_ < MID + 10)     # only under the horizontal cell line
    xs = np.arange(N) + 0.5
    # which cell edge each column's bank belongs to, and t along it
    t = np.where(xs < MID, xs - T0, xs - T1).astype(int) + HALF
    t = np.clip(t, 0, CELL - 1)
    pw, pe = _bank_marks(prof[3]), _bank_marks(prof[1])
    pw2, pe2 = _bank_marks(prof[3] + 8), _bank_marks(prof[1] + 8)
    marks = np.where(xs < MID, pw[t], pe[t])[None, :].repeat(N, 0)
    marks2 = np.where(xs < MID, pw2[t], pe2[t])[None, :].repeat(N, 0)
    # the bank's earth face, 6 texels (softground.water's bank_h): a lit top row, two courses of
    # small clods (each lit where it begins, dark where it ends), a dark wet bottom row; then the
    # light waterline and two rows of the bank's shade on the water (the depth layer carries on)
    face_rows = {1: None, 2: marks, 3: marks, 4: marks2, 5: marks2, 6: 'wet'}
    for r_, mk in face_rows.items():
        sel = col_bank & (rt == r_)
        ops.own[sel] = 2
        if mk is None:
            ops.ab[sel] = C('earth', 3)
        elif isinstance(mk, str):
            ops.ab[sel] = C('earth_cool', 0)
        else:
            body = C('earth', 2) if r_ % 2 == 0 else C('earth_cool', 2)
            ops.ab[sel] = np.where(mk[sel] > 0, C('earth', 3), np.where(mk[sel] < 0, C('earth_cool', 1), body))
    wline = col_bank & (rt == 7)
    ops.own[wline] = 2
    ops.ab[wline] = C('water', 5)
    ops.shift(col_bank & (rt == 8), -2)
    ops.shift(col_bank & (rt == 9), -2)
    # the turf's last row over the bank a tone down (its underside)
    ops.shift(land & GD.down(m2, -1), -1)
    nb = col_bank
    # every other shore (Matt, 4 Nov): only a bank with land to its north shows a face in this
    # top-down 3/4 view; east, west and south shores show one rim, wet earth at the land's edge and
    # the water's mid tone inside it (softground.RIM_EARTH, RIM_LINE), with no wall seen edge-on.
    # Where the north face ends beside open water its edge column is the face's wet foot, so the rim
    # runs on round inside and outside bends.
    # (what hangs on the face's end is kept off the CALM border strips, which must depend only on
    # the border's own cells and profile: test_kit.test_tiles_canonical_at_borders)
    yy2, xx2 = np.mgrid[0:N, 0:N]
    away = ((yy2 >= T0 + CALM + 1) & (yy2 < T1 - CALM - 1) & (xx2 >= T0 + CALM + 1) & (xx2 < T1 - CALM - 1))
    face = nb & (rt <= 6)
    face_end = face & (GD.right(m2 & ~nb, 1) | GD.right(m2 & ~nb, -1)) & away
    ops.own[face_end] = 2
    ops.ab[face_end] = C('earth_cool', 0)
    rim, _w = GD.shore_rim(m2, face)
    rim &= ~nb
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    wline = m2 & ~nb & ~rim & (ndi.binary_dilation(rim, structure=cross) |
                               (ndi.binary_dilation(face, structure=cross) & away))
    ops.own[rim] = 2
    ops.ab[rim] = GD.rim_earth()
    ops.own[wline] = 2
    ops.ab[wline] = C('water', GD.RIM_LINE)
    # the shallows inside the rim lit a tone (within 3.5 texels of the land: the bands' reach the
    # corners leave canonical at the borders)
    dist = ndi.distance_transform_edt(m2)
    shal = m2 & ~nb & ~rim & ~wline & (ops.own == 1)
    ops.shift(shal & (dist <= 3.5), 1)
    s_lip = land & GD.down(m2, 1)
    ops.shift(s_lip, 1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def _shore_geometry(k: int, prof):
    """What bank, quay_wall and beach share: the water's soft outline, the land, each water texel's
    rows from the land above it (`rt`), and the north shore's columns (land north of the cell line)."""
    m2 = soft_lower(k, prof)
    land = ~m2
    rt = GD.runs_from_top(m2)
    q = [bool((k >> b) & 1) for b in range(4)]    # nw, ne, sw, se (True = land)
    xs_ = np.arange(N) + 0.5
    left = (xs_ < MID)[None, :]
    nb_cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    yy_ = np.arange(N)[:, None] + 0.5
    return m2, land, rt, nb_cfg, yy_


def _course_joints(prof: int, salt: int) -> np.ndarray:
    """A quay course's blocks along one cell edge, a function of its profile only (so the two tiles
    sharing the cell edge agree): per texel t (0 .. 23), 0 on a joint, 1 on a block's lit west end,
    2 inside; and the block's stone sibling (0 to 2) in the next axis."""
    rng = np.random.default_rng(4300 + 16 * prof + salt)
    kind = np.full(CELL, 2, np.int32)
    fam = np.zeros(CELL, np.int32)
    x = int(rng.integers(0, 6)) - 6
    while x < CELL:
        L = int(rng.integers(6, 11))
        f = int(rng.integers(0, 3))
        for j in range(max(0, x), min(CELL, x + L)):
            kind[j] = 0 if j == x else (1 if j == x + 1 else 2)
            fam[j] = f
        x += L
    return np.stack([kind, fam])


QUAY_FAMS = ('stone', 'stone_warm', 'stone_cool')


def quay_wall(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), side_w: int = 0) -> np.ndarray:
    """A quay (upper) over water (lower): a dressed wall, not a turf bank (review round 9 of the Act 1
    props, F9-1; sets/coast.quay_wall's recipe and softground.quay_face's, fitted to the tile's 9
    rows under the outline). Under a quay to the north: on the land the coping, its lit edge (stone
    4) over its front (3); on the water a shadow line, a course of blocks (lit top, body, foot, the
    lit west end and the joints from the cell edge's profile), a bed joint, a lower course a tone
    down, a dark wet foot with weed in clusters, then the light waterline. On every other shore the
    coping's lit edge and 5.3a's rim in wet stone, the water's mid tone inside it and lit shallows.
    `side_w` is kept for old piece files and ignored."""
    m2, land, rt, nb_cfg, yy_ = _shore_geometry(k, prof)
    ops = Ops(land, fill_u, fill_l)
    top_of_run = m2 & GD.down(land, 1)
    col = np.zeros_like(m2)
    for d in range(0, 8):
        col |= GD.down(top_of_run, d) & m2
    col &= (rt <= 8) & nb_cfg & (yy_ > MID - 5) & (yy_ < MID + 10)
    xs = np.arange(N) + 0.5
    t = np.clip(np.where(xs < MID, xs - T0, xs - T1).astype(int) + HALF, 0, CELL - 1)
    fams = np.array([FI[f] * 8 for f in QUAY_FAMS])
    for course, rows, tones in ((0, (2, 3, 4), (4, 3, 2)), (1, (6, 7), (3, 2))):
        jw, je = _course_joints(prof[3], course), _course_joints(prof[1], course)
        kind = np.where(xs < MID, jw[0][t], je[0][t])[None, :].repeat(N, 0)
        fam = np.where(xs < MID, jw[1][t], je[1][t])[None, :].repeat(N, 0)
        for j, r_ in enumerate(rows):
            sel = col & (rt == r_)
            tone = np.minimum(tones[j] + ((kind == 1) & (j > 0)).astype(int), 4)
            code = np.where(kind == 0, C('stone_cool', 1), fams[fam] + tone)
            ops.own[sel] = 2
            ops.ab[sel] = code[sel]
    for r_, code in ((1, C('stone_cool', 1)), (5, C('stone_cool', 1))):
        sel = col & (rt == r_)
        ops.own[sel] = 2
        ops.ab[sel] = code
    # the wet foot, its weed in clusters of 2 to 4 texels (where the cell edge's joints fall)
    foot_ = col & (rt == 8)
    jw, je = _course_joints(prof[3], 7), _course_joints(prof[1], 7)
    weed = np.where(xs < MID, (jw[0][t] <= 1) & (jw[1][t] == 0), (je[0][t] <= 1) & (je[1][t] == 0))[None, :].repeat(N, 0)
    ops.own[foot_] = 2
    ops.ab[foot_] = np.where(weed, C('leaf_cool', 1), C('stone_cool', 0))[foot_]
    wline = col & (rt == 9)
    ops.own[wline] = 2
    ops.ab[wline] = C('water', 5)
    # the coping on the land over the wall
    front = land & GD.down(col & (rt == 1), -1)
    lit = land & GD.down(col & (rt == 1), -2) & ~front
    for sel, code in ((front, C('stone', 3)), (lit, C('stone', 4))):
        ops.own[sel] = 2
        ops.ab[sel] = code
    # every other shore: the coping's lit edge, a rim of wet stone, the mid tone, lit shallows
    yy2, xx2 = np.mgrid[0:N, 0:N]
    away = ((yy2 >= T0 + CALM + 1) & (yy2 < T1 - CALM - 1) & (xx2 >= T0 + CALM + 1) & (xx2 < T1 - CALM - 1))
    face = col & (rt <= 8)
    face_end = face & (GD.right(m2 & ~col, 1) | GD.right(m2 & ~col, -1)) & away
    ops.own[face_end] = 2
    ops.ab[face_end] = C('stone_cool', 0)
    rim, _w = GD.shore_rim(m2, face)
    rim &= ~col
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    wl2 = m2 & ~col & ~rim & (ndi.binary_dilation(rim, structure=cross) |
                              (ndi.binary_dilation(face, structure=cross) & away))
    ops.own[rim] = 2
    ops.ab[rim] = C('stone_cool', 1)
    ops.own[wl2] = 2
    ops.ab[wl2] = C('water', GD.RIM_LINE)
    dist = ndi.distance_transform_edt(m2)
    shal = m2 & ~col & ~rim & ~wl2 & (ops.own == 1)
    ops.shift(shal & (dist <= 3.5), 1)
    edge = land & ndi.binary_dilation(m2 & ~col, structure=cross) & ~front & ~lit
    ops.own[edge] = 2
    ops.ab[edge] = C('stone', 4)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def beach(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), side_w: int = 0) -> np.ndarray:
    """Shingle (upper) running into water (lower): no face on any shore, a beach shelves (review
    round 9 of the Act 1 props, F9-1). The shingle's last 6 texels before the water a tone down (wet
    shingle: as deep as the tile's border strips allow, test_kit.test_tiles_canonical_at_borders), a swash line on the water's edge 1 texel wide and 2 where the cell edge's lump bulges
    (so it wobbles with the soft grid's outline), then lit shallows. `side_w` is kept for old piece
    files and ignored."""
    m2, land, rt, nb_cfg, yy_ = _shore_geometry(k, prof)
    ops = Ops(land, fill_u, fill_l)
    wet = np.zeros_like(m2)
    for d in range(1, 7):
        wet |= GD.down(m2, -d) | GD.down(m2, d) | GD.right(m2, d) | GD.right(m2, -d)
    ops.shift(land & wet, -1)
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    rim = m2 & ndi.binary_dilation(land, structure=cross)
    second = m2 & ~rim & ndi.binary_dilation(rim, structure=cross) & (displacement(k, prof) > 0.8)
    sw = rim | second
    ops.own[sw] = 2
    ops.ab[sw] = C('water', 5)
    dist = ndi.distance_transform_edt(m2)
    ops.shift(m2 & ~sw & (dist <= 3.5), 1)
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
    near = np.abs(xs[None, :] - MID) < 8
    ew = earth + '_warm' if earth + '_warm' in FI else earth
    # from the ground inwards: the darkest line (broken), then a band of 3 texels seen edge-on,
    # in shade at an east end, lit at a west end (the plateau's side walls above match it)
    dist_e = np.zeros(face.shape, np.int32)
    dist_w = np.zeros(face.shape, np.int32)
    for kk in range(4, 0, -1):
        dist_e[face & GD.right(m2, -kk)] = kk          # ground kk texels to the east
        dist_w[face & GD.right(m2, kk)] = kk           # ground kk texels to the west
    sel_e = face & east_end & near & (dist_e > 0) & ~f1 & ~f2
    sel_w = face & west_end & near & (dist_w > 0) & ~f1 & ~f2
    for sel, dist, band in ((sel_e, dist_e, (C(earth, 1), C(earth, 2), C(earth, 3))),
                            (sel_w, dist_w, (C(ew, 3), C(ew, 4), C(ew, 4)))):
        for kk, code in zip((2, 3, 4), band):
            m_ = sel & (dist == kk)
            ops.own[m_] = 2
            ops.ab[m_] = code
        m_ = sel & (dist == 1) & _broken()
        ops.own[m_] = 2
        ops.ab[m_] = C(ec, 0)
        m_ = sel & (dist == 1) & ~_broken()
        ops.own[m_] = 2
        ops.ab[m_] = band[0]
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def tier_side(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), earth: str = 'earth',
              band: int = 4) -> np.ndarray:
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
    ops.ab[wall_w] = C(ew, 4)
    ops.ab[wall_w & ~GD.right(up, -(band - 2))] = C(ew, 3)
    ops.own[wall_e] = 2
    ops.ab[wall_e] = C(earth, 2)
    ops.ab[wall_e & GD.right(up, 1)] = C(earth, 3)
    ops.ab[wall_e & ~GD.right(up, band - 2)] = C(earth, 1)
    out_w = wall_w & ~GD.right(up, -(band - 1)) & ~GD.right(up, -1)
    out_e = wall_e & ~GD.right(up, band - 1) & ~GD.right(up, 1)
    for sel in (out_w & _broken(), out_e & _broken()):
        ops.ab[sel] = C(ec, 0)
    ops.shift(up & (GD.right(m2, 1) | GD.right(m2, -1)) & near & (raised_east | raised_west), 1)   # the lip turned down the side, lit
    # the back rim: raised ground south of a horizontal cell line, lower ground north of it
    yv = (np.arange(N) + 0.5)[:, None]
    back_cfg = np.where(left, q[2] and not q[0], q[3] and not q[1]).astype(bool) & (yv > MID - 6) & (yv < MID + 6)
    ops.shift(up & GD.down(m2, 1) & back_cfg, 1)
    crease = m2 & GD.down(up, -1) & back_cfg
    ops.own[crease] = 2
    ops.ab[crease] = C(ec, 1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


# ------------------------------------------------------------------------------------------------
# the Frostline's edges (scripts/art/kit/sets/frost.py; the detail audit of #478, F-G4 to F-G6)
# ------------------------------------------------------------------------------------------------
def _north_lip(k: int, m2: np.ndarray) -> np.ndarray:
    """The lower material's texels under a north lip, read from the cells (upper north of the
    horizontal cell line, lower south of it) and kept near that line, as bank does, so a vertical
    edge's lumps never cast a lip's bands into a neighbour's border strip."""
    q = [bool((k >> b) & 1) for b in range(4)]
    xs_ = np.arange(N) + 0.5
    left = (xs_ < MID)[None, :]
    nb_cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    yy_ = np.arange(N)[:, None] + 0.5
    return m2 & nb_cfg & (yy_ > MID - 5) & (yy_ < MID + 10)


def _south_lip(k: int, m2: np.ndarray) -> np.ndarray:
    """The upper material's texels over a south edge (upper north of the horizontal cell line, lower
    south), near that line."""
    q = [bool((k >> b) & 1) for b in range(4)]
    xs_ = np.arange(N) + 0.5
    left = (xs_ < MID)[None, :]
    cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    yy_ = np.arange(N)[:, None] + 0.5
    return ~m2 & cfg & (yy_ > MID - 10) & (yy_ < MID + 5)


def _fray_depth(prof: int, salt: int = 0) -> np.ndarray:
    """How far loose snow is kicked over a trod's edge along one cell edge, a function of its profile
    only (both tiles sharing the cell edge agree): per texel along it (t = -12 .. 11), 0 to 3 texels,
    changing by a texel every 2 to 5 texels, with a tongue of 4 now and then (eastward-edges.md 5.1:
    a band 2 to 3 wide in 1 texel steps, a tuft or bite 3 to 4 deep about every 16)."""
    rng = np.random.default_rng(6100 + 13 * prof + salt)
    out = np.zeros(CELL, np.int32)
    v, i = int(rng.integers(1, 3)), 0
    while i < CELL:
        L = int(rng.integers(2, 6))
        out[i:i + L] = v
        i += L
        v = int(np.clip(v + rng.choice((-1, 1)), 0, 3))
    if rng.random() < 0.7:
        j = int(rng.integers(2, CELL - 6))
        out[j:j + int(rng.integers(3, 6))] = 4
    return out


def _scallops(prof: int) -> np.ndarray:
    """The snow's north lip over a trod along one cell edge, a function of its profile only: per
    texel along it (t = -12 .. 11) how many rows the lip hangs over the trod, in rounded lobes 6 to
    10 texels long with a flat belly (round 5: 1 at the cusp between lobes, 3 across the belly)."""
    rng = np.random.default_rng(6600 + 11 * prof)
    out = np.ones(CELL, np.int32)
    x = int(rng.integers(-5, 1))
    while x < CELL:
        L = int(rng.integers(6, 11))
        for i in range(L):
            if 0 <= x + i < CELL:
                out[x + i] = 1 if i == 0 else min(3, 1 + int(round(2.4 * np.sin(np.pi * (i + 0.5) / L) ** 0.5)))
        x += L
    return out


def snow_lip(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0)) -> np.ndarray:
    """Snow (upper) over a trod packed into it. Under a north lip (round 4, after the lip read as a
    drawn line; round 5 rounds the lobes) the snow hangs over the trod in lobes 6 to 10 texels long
    with a flat belly and a one-texel cusp between them (`_scallops` of the cell edge's profile): its
    top row lit (a tone up), the hanging face in two cool rows (snow_cool 3, then snow_cool 2 at its
    foot) and a row of shade on the trod under each lobe. On the trod's south side the snow's first
    row is lit. Every other edge is soft (eastward-edges.md 5.1: a frayed edge, no line): loose snow
    kicked over the trod's edge lies on it in a band 0 to 3 texels wide that steps a texel at a time,
    with a tongue of 4 now and then, the trod there a tone lighter, so the packed plane fades into
    the snow instead of meeting it on a line. Every band's width is the cell edge's own, so
    neighbours agree at every border."""
    m2 = soft_lower(k, prof)
    snow = ~m2
    ops = Ops(snow, fill_u, fill_l)
    under = _north_lip(k, m2)
    rt = GD.runs_from_top(m2)
    xs = np.arange(N) + 0.5
    t = np.clip(np.where(xs < MID, xs - T0, xs - T1).astype(int) + HALF, 0, CELL - 1)
    sc = np.where(xs < MID, _scallops(prof[3])[t], _scallops(prof[1])[t])[None, :]
    lobe = under & (rt >= 1) & (rt <= sc)
    ops.own[lobe] = 2
    ops.ab[lobe] = np.where(((rt == sc) & (sc >= 2))[lobe], C('snow_cool', 2), C('snow_cool', 3))
    top3 = lobe & (rt == 1) & (sc == 3)
    ops.own[top3] = 0                                   # the belly's first row: the snow itself
    ops.shift(under & (rt == sc + 1), -1)
    ops.shift(_south_lip(k, m2) & GD.down(m2, -1), 1)   # the lip's lit top row
    ops.shift(snow & GD.down(m2, 1), 1)
    # the soft edges: each trod texel near the outline belongs to the cell edge whose line is nearer
    # (the vertical one through the vertex for N and S, the horizontal one for W and E)
    vert, depth = _edge_depth(prof)
    dist = _across(snow, vert)
    loose = m2 & (dist <= depth) & ~under
    ops.shift(loose, 1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def _across(snow: np.ndarray, vert: np.ndarray) -> np.ndarray:
    """Each texel's distance (1 to 5, else 99) to `snow` across its own cell edge only: along the row
    for texels of a vertical edge, up and down for a horizontal one, so a neighbouring edge's snow
    never widens a band at a border."""
    dist = np.full((N, N), 99, np.int32)
    for d in range(5, 0, -1):
        across = np.where(vert, GD.right(snow, d) | GD.right(snow, -d), GD.down(snow, d) | GD.down(snow, -d))
        dist[across] = d
    return dist


def _edge_depth(prof, salt: int = 0):
    """`vert` (the texel belongs to the vertical cell line through the vertex, N or S) and each
    texel's fray depth from its own cell edge's profile (`_fray_depth`)."""
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    vert = np.abs(xx - MID) < np.abs(yy - MID)
    depth = np.zeros((N, N), np.int32)
    for i, (sel, coord, mid_) in enumerate(((vert & (yy < MID), yy, T0), (~vert & (xx >= MID), xx, T1),
                                            (vert & (yy >= MID), yy, T1), (~vert & (xx < MID), xx, T0))):
        t = np.clip((coord - mid_).astype(int) + HALF, 0, CELL - 1)
        depth = np.where(sel, _fray_depth(prof[i], salt)[t], depth)
    return vert, depth


def snow_fray(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0)) -> np.ndarray:
    """Snow (upper) thinning over a stone field: no closed outline (the step is a texel at most).
    Where the snow ends to the south it keeps a lit lip row and a cool row under it, and a row of
    shade on the stones below; its north edge's first row is lit. Its east and west edges (the
    Frostline A4 pass, eastward-edges.md 5.1) are frayed: the snow runs out over the stones in
    tongues 0 to 4 texels long that step a texel at a time (`_fray_depth` of the cell edge's
    profile), each tongue's west face lit and a texel of shade on the stones east of it. Stones of
    the moraine's own slate break through its last texels, none to three a cell edge in clusters,
    3 to 12 texels long, a few of the big ones capped with snow (`_fray_list`)."""
    m2 = soft_lower(k, prof)
    snow = ~m2
    ops = Ops(snow, fill_u, fill_l)
    over = _south_lip(k, m2)
    south_end = over & GD.down(m2, -1)
    ops.shift(south_end, -1)
    ops.shift(over & GD.down(south_end, -1) & ~south_end, 1)
    ops.shift(m2 & GD.down(snow, 1), -1)
    ops.shift(snow & GD.down(m2, 1), 1)
    vert, depth = _edge_depth(prof, salt=3)
    tongue = m2 & vert & (_across(snow, vert) <= depth)
    ops.own[tongue] = 0
    ops.dl[tongue] = 0
    snow2 = snow | tongue
    side = vert & ~over
    ops.shift(side & snow2 & GD.right(m2 & ~tongue, 1), 1)       # the west face of the snow lit
    ops.shift(side & m2 & ~tongue & GD.right(snow2, 1), -1)      # a texel of shade east of it
    # the stones breaking through the snow's last texels (round 4: the moraine's own slate stones,
    # in place of the lawn kit's warm decals), from the cell edge's own profile
    stone, sid, kind, capm = _fray_stones(k, prof, snow2, vert)
    # round 5: a corner of stones closed round by snow on three sides (a lone moraine cell is four
    # such corners) always shows a whole stone in two of the four turns, so a small patch never reads
    # as a flat stain; drawn within the tile's middle, it depends on the whole tile
    if k in (7, 14):                                  # the stones only in the SE (7) or NW (14) quarter
        sx, sy = (1, 1) if k == 7 else (-1, -1)
        rng = np.random.default_rng(7900 + 31 * prof[0] + 17 * prof[1] + 13 * prof[2] + 7 * prof[3] + k)
        L, d = float(rng.uniform(6.5, 8.0)), float(rng.uniform(4.6, 5.6))
        cx, cy = MID + sx * 5.0, MID + sy * 4.5
        yy, xx = np.mgrid[0:N, 0:N] + 0.5
        m = (((xx - cx) / (L / 2)) ** 2 + ((yy - cy) / (d / 2)) ** 2) <= 1.0
        stone = stone | m
        sid = np.where(m, 99, sid)
        kind = np.where(m, int(rng.integers(0, 3)), kind)
        capm = capm | (m & (yy < cy - d * 0.15) & bool(rng.random() < 0.5))
    _shade_stones(ops, stone, sid, kind, capm, m2 & ~snow2)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def _fray_list(prof: int) -> list:
    """The stones along one cell edge of snow over moraine, a function of its profile only: (t
    centre, length, depth, offset across the edge (texels into the stones, negative into the
    snow), kind, cap). None to three a cell edge, clustered: two or three close together or one
    alone, 3 to 12 texels long."""
    rng = np.random.default_rng(7700 + 13 * prof)
    out = []
    n = int(rng.choice((0, 1, 2, 3), p=(0.3, 0.3, 0.25, 0.15)))
    tc = float(rng.uniform(3, CELL - 3))
    for _i in range(n):
        L = float(rng.choice((rng.uniform(3, 5), rng.uniform(5, 8), rng.uniform(8, 12)), p=(0.4, 0.4, 0.2)))
        d = max(3.0, L * rng.uniform(0.55, 0.75))
        out.append((tc, L, d, float(rng.uniform(-1.0, 2.5)), int(rng.integers(0, 3)), bool(L >= 8 and rng.random() < 0.5)))
        tc += float(rng.choice((-1, 1))) * (L / 2 + rng.uniform(2.5, 6))
    return out


def _edge_frames(prof):
    """Each texel's cell edge (0..3 as N, E, S, W; -1 none) and its t along it, by the nearer cell
    line through the vertex, and that edge's profile."""
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    vert = np.abs(xx - MID) < np.abs(yy - MID)
    eid = np.full((N, N), -1, np.int64)
    tt = np.zeros((N, N))
    for i, (sel, coord, mid_) in enumerate(((vert & (yy < MID), yy, T0), (~vert & (xx >= MID), xx, T1),
                                            (vert & (yy >= MID), yy, T1), (~vert & (xx < MID), xx, T0))):
        eid[sel] = i
        tt[sel] = (coord - mid_ + HALF)[sel]
    return vert, eid, tt


def _fray_stones(k, prof, snow, vert):
    """Rasterise `_fray_list` along every edge of the snow: the stone mask, an id per stone, its
    granite kind and its cap texels. Only edges the outline crosses carry stones."""
    _v, eid, tt = _edge_frames(prof)
    into = _across(snow, vert).astype(float)                   # into the stones
    back = _across(~snow, vert).astype(float)                  # back into the snow
    a = np.where(~snow, into - 0.5, 0.5 - back)
    stone = np.zeros((N, N), bool)
    sid = np.full((N, N), -1, np.int64)
    kind = np.zeros((N, N), np.int64)
    capm = np.zeros((N, N), bool)
    cr = crossings(k)
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    # a stone keeps to its own edge's corridor, clear of the perpendicular borders' strips
    corridor = np.where(vert, np.abs(xx - MID) < HALF - CALM - 1, np.abs(yy - MID) < HALF - CALM - 1)
    for i in range(4):
        if not cr[i]:
            continue
        for j, (tc, L, d, off, kk, cc) in enumerate(_fray_list(prof[i])):
            m = (eid == i) & corridor & (np.abs(a) < 8) & ((((tt - tc) / (L / 2)) ** 2 + ((a - off) / (d / 2)) ** 2) <= 1.0)
            stone |= m
            sid[m] = i * 8 + j
            kind[m] = kk
            if cc:
                capm |= m & (a - off < -d * 0.15)
    return stone, sid, kind, capm


def _shade_stones(ops, stone, sid, kind, capm, ground):
    """A stone shaded from its own outline, lit from the upper left: a lit top and west edge, the
    body, a darker east end and foot, outlined dark on its south and east, a snow cap where asked,
    and a texel of contact shade on `ground` at its south and east."""
    def nb(dy, dx):
        o = np.full((N, N), -2, np.int64)
        ys0, ys1 = max(0, -dy), N - max(0, dy)
        xs0, xs1 = max(0, -dx), N - max(0, dx)
        o[ys0:ys1, xs0:xs1] = sid[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
        return o
    up, dn, lf, rt_ = nb(-1, 0), nb(1, 0), nb(0, -1), nb(0, 1)
    fams = (('slate', 'slate_cool'), ('slate', 'slate'), ('slate_warm', 'slate'))
    code = np.zeros((N, N), np.int32)
    for i, (fl_, fs) in enumerate(fams):
        c = np.full((N, N), C(fl_, 3), np.int32)
        c[(up != sid) | (lf != sid)] = C(fl_, 4)
        c[(up != sid) & (lf != sid)] = C(fl_, 5)
        c[(dn != sid) | (rt_ != sid)] = C('slate_cool', 1)
        k_ = kind == i
        code[k_] = c[k_]
    cap = capm & stone
    code[cap] = np.where(up[cap] != sid[cap], C('snow', 5), C('snow', 4))
    code[cap & (dn == sid) & ~np.roll(cap, -1, 0)] = C('snow_cool', 3)
    ops.own[stone] = 2
    ops.ab[stone] = code[stone]
    foot = ground & ~stone & (GD.down(stone, 1) | GD.right(stone, 1))
    ops.shift(foot, -1)


def _mid_stone(prof: int) -> tuple:
    """The tarn bank's stone across the middle of one cell edge (round 5), a function of its profile
    only, so both tiles sharing the cell edge agree: (start, end, depth, drop, cap, kind) in texels
    along it (t = 0 .. 23). It starts 3 to 8 texels in and ends 15 to 21 in (9 to 18 long, so where
    the gaps fall moves from edge to edge), 5 to 8 deep, set 0 or 1 texel further from the shore
    (`drop`), now and then with a cap of snow, the granite one of three siblings (`kind`)."""
    rng = np.random.default_rng(5500 + 7 * prof)
    s0, s1 = int(rng.integers(3, 9)), int(rng.integers(15, 22))
    dd = int(np.clip(round((s1 - s0) * rng.uniform(0.45, 0.6)), 5, 8))
    return (s0, s1, dd, int(rng.random() < 0.35), bool(rng.random() < 0.3), int(rng.integers(0, 3)))


def _vertex_stones(p_w: int, p_e: int) -> list:
    """The stones between two cell edges' middle stones, across the vertex they share (round 5: so
    the gaps never fall on the 24-texel cell beat): a function of both edges' profiles, which only
    the tiles centred on that vertex see whole. In texels from the vertex (negative to the west):
    (start, end, depth, drop, cap, kind); none where the room is under 6, two where it is 15 or more.
    They stay within 10 texels of the vertex, clear of the tile's border strips."""
    rng = np.random.default_rng(5600 + 7 * p_w + 53 * p_e)
    a = _mid_stone(p_w)[1] - CELL + int(rng.integers(1, 3))
    b = _mid_stone(p_e)[0] - int(rng.integers(1, 3))
    room = b - a
    if room < 6:
        return []
    cuts = [a, b] if room < 15 else [a, a + room // 2 + int(rng.integers(-1, 2)), b]
    out = []
    for i in range(len(cuts) - 1):
        c0, c1 = cuts[i] + (1 if i else 0), cuts[i + 1]
        if c1 - c0 >= 6:
            dd = int(np.clip(round((c1 - c0) * rng.uniform(0.5, 0.65)), 4, 7))
            out.append((c0, c1, dd, int(rng.random() < 0.35), bool(rng.random() < 0.25), int(rng.integers(0, 3))))
    return out


def cornice_bank(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0), rim: str = 'ice') -> np.ndarray:
    """Snow (upper) over water or ice in a cold country (the Frostline A4 pass, rounds 4 and 5 after
    the audits). Only a north shore (land to the north) turns a face to the camera (eastward-edges.md
    5.3a): there the snow's lip runs on unbroken (a lit row, thicker where a stone sits a texel
    lower) and under it, sitting on the shoreline and following its wave, lies a bank of granite
    stones the size of Eastward's (5.3): one across the middle of each cell edge (9 to 18 texels long,
    5 to 8 deep, from the edge's profile) and one or two across each vertex between them (from both
    edges' profiles), so the gaps move from cell to cell instead of beating once a cell. Each stone
    is a rounded block in four planes of its own sibling granite (a lit top plane with a lit top
    edge and west edge, the front, a darker east end and foot), outlined dark on its south and east,
    a few with a cap of snow; under each a row of contact shade on the water or ice, and in every
    gap the light waterline (a light row, a lighter one above it). Where a run ends at a corner its
    last stone rounds off before the turn. Every other shore keeps the one rim: with rim 'ice', a
    rim of shore ice two texels wide (lit on its land side) on the open water; with rim 'lip', a
    cool row. The snow's south lip is lit."""
    m2 = soft_lower(k, prof)
    land = ~m2
    ops = Ops(land, fill_u, fill_l)
    q = [bool((k >> b) & 1) for b in range(4)]          # nw, ne, sw, se (True = land)
    cfg_l, cfg_r = q[0] and not q[2], q[1] and not q[3]
    rt = GD.runs_from_top(m2)
    xs = np.arange(N) + 0.5
    yy_ = np.arange(N)[:, None] + 0.5
    cfg = np.where(xs < MID, cfg_l, cfg_r)[None, :]
    band = (yy_ > MID - 5) & (yy_ < MID + 10)
    # the straight shore with this tile's W and E profiles bounds each stone's depth, so a corner's
    # rounding never changes a stone a neighbour draws (every stone stays above the border strip)
    ref = soft_lower(3, (0, prof[1], 0, prof[3]))
    ref_top = np.argmax(ref & band, 0)
    sid = np.full(N, -1, np.int64)
    u = np.zeros(N, np.int64)
    w = np.ones(N, np.int64)
    D = np.zeros(N, np.int64)
    jit = np.zeros(N, np.int64)
    cap = np.zeros(N, bool)
    kind = np.zeros(N, np.int64)
    vx = int(MID)                                       # the vertex's column
    stones = []                                         # (first column, end column, depth, drop, cap, kind)
    if cfg_l:
        s0, s1, *rest = _mid_stone(prof[3])
        stones.append((T0 - HALF + s0, T0 - HALF + s1, *rest))
    if cfg_r:
        s0, s1, *rest = _mid_stone(prof[1])
        stones.append((T1 - HALF + s0, T1 - HALF + s1, *rest))
    if cfg_l and cfg_r:
        for (c0, c1, *rest) in _vertex_stones(prof[3], prof[1]):
            stones.append((vx + c0, vx + c1, *rest))
    cols_all = np.arange(N)
    for i, (c0, c1, dd, jj, cc, kk) in enumerate(stones):
        c = cols_all[(cols_all >= c0) & (cols_all < c1)]
        deepest = int(ref_top[c].max()) + jj                    # the stone's top row at its lowest
        dd = int(min(dd, int(MID + 10) - deepest))              # its foot above the border strip
        sid[c] = i
        u[c] = c - c0
        w[c] = c1 - c0
        D[c] = max(dd, 2)
        jit[c] = jj
        cap[c] = cc
        kind[c] = kk
    # where the run ends at the vertex (the other half carries no north shore) its stone rounds off
    # before the corner's turn, on a quarter round 3 texels long (nothing within the border strips moves)
    lim = np.full(N, 99.0)
    if cfg_l and not cfg_r:
        cut = T0 - HALF + 17
        d_ = np.clip((cols_all + 0.5 - (cut - 3)) / 3.0, 0, None)
        lim = np.where(d_ >= 1, 0, np.sqrt(np.clip(1 - d_ ** 2, 0, 1)) * 99)
    if cfg_r and not cfg_l:
        cut = T1 - HALF + 7
        d_ = np.clip(((cut + 3) - (cols_all + 0.5)) / 3.0, 0, None)
        lim = np.where(d_ >= 1, 0, np.sqrt(np.clip(1 - d_ ** 2, 0, 1)) * 99)
    D = np.minimum(D, np.where(lim >= 99, D, np.round(D * lim / 99)).astype(np.int64))
    sid = np.where(D > 0, sid, -1)
    U, Wd, Dd = u[None, :], w[None, :], D[None, :]
    v = rt - 1 - jit[None, :]
    valid = m2 & cfg & band & (rt >= 1)
    has = (sid >= 0)[None, :]
    # each stone a rounded block (a superellipse in its own along-and-down frame)
    Dz = np.maximum(Dd, 1)
    ex = np.abs((U + 0.5 - Wd / 2) / (Wd / 2)) ** 2.6 + np.abs((v + 0.5 - Dz / 2) / (Dz / 2)) ** 2.6
    stone = valid & has & (v >= 0) & (v < Dd) & (ex <= 1.0)
    ids = np.where(stone, np.broadcast_to(sid[None, :], m2.shape), -1)
    edge = np.zeros(m2.shape, bool)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb_ = np.full(m2.shape, -1, np.int64)
        ys0, ys1 = max(0, -dy), N - max(0, dy)
        xs0, xs1 = max(0, -dx), N - max(0, dx)
        nb_[ys0:ys1, xs0:xs1] = ids[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
        edge |= stone & (nb_ != ids)
    top_edge = edge & stone & (np.vstack([np.full((1, N), -1), ids[:-1]]) != ids) & (U < 0.7 * Wd)
    outline = edge & ~top_edge & ((U + 0.5 >= 0.5 * Wd) | (v + 0.5 >= 0.5 * Dd))
    fams = (('slate', 'slate'), ('slate_warm', 'slate'), ('slate', 'slate_cool'))
    K = np.broadcast_to(kind[None, :], m2.shape)
    code = np.zeros(m2.shape, np.int32)
    for i, (fl_, fs) in enumerate(fams):
        c = np.full(m2.shape, C(fl_, 3), np.int32)                       # the front
        c[v < np.maximum(2, np.round(Dd * 0.4))] = C(fl_, 4)             # the top plane
        c[(U >= 0.8 * Wd) | (v == Dd - 1)] = C(fs, 2)                    # the east end and the foot
        c[edge & ~top_edge] = C(fl_, 4)                                  # the west edge, to the light
        c[top_edge] = C(fl_, 5)                                          # the lit top edge
        c[outline] = C('slate_cool', 1)                                  # the outline, south and east
        code[K == i] = c[K == i]
    capm = stone & np.broadcast_to(cap[None, :], m2.shape) & ~outline & (v <= 1)
    code[capm & (v == 0)] = C('snow', 5)
    code[capm & (v == 1)] = C('snow_cool', 3)
    # the snow's lip, thicker over a stone set a texel lower; the gaps' light waterline; the shade
    lip_top = land & cfg & band & GD.down(m2, -1)        # the snow's last row over the shore, lit
    lip_low = valid & (v < 0) & has
    gap = valid & ~stone & ~lip_top & ~lip_low
    under = gap & has & (v >= 0) & (v <= Dd) & np.vstack([np.zeros((1, N), bool), stone[:-1]])
    wline = gap & ((~has & (rt == 1)) | (has & (v == 0) & ~stone & ((U <= 1) | (U >= Wd - 2))))
    wline &= ~under
    wline2 = gap & ~has & (rt == 2) & ~under
    ops.shift(lip_top, 1)
    ops.own[lip_low] = 2
    ops.ab[lip_low] = C('snow_cool', 3)
    ops.own[stone] = 2
    ops.ab[stone] = code[stone]
    ops.shift(under, -1)
    ops.shift(wline, 2)
    ops.shift(wline2, 1)
    used = lip_top | lip_low | stone | under | wline | wline2
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    edge1 = m2 & ~used & ~(valid & has) & ndi.binary_dilation(land, structure=cross)
    if rim == 'ice':
        edge2 = m2 & ~used & ~(valid & has) & ~edge1 & ndi.binary_dilation(edge1, structure=cross)
        ops.own[edge1] = 2
        ops.ab[edge1] = C('sky_cool', 5)
        ops.own[edge2] = 2
        ops.ab[edge2] = C('snow_cool', 3)
    else:
        ops.shift(edge1, -1)
    ops.shift(land & GD.down(m2, 1), 1)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


def ice_edge(k: int, fill_u: np.ndarray, fill_l: np.ndarray, prof=(0, 0, 0, 0)) -> np.ndarray:
    """Lake ice (upper) cut or melted back from open water: under a north edge the ice's thickness
    shows (a lit cut edge, two rows of ice in shade, a dark wet line) and the water under it is in
    shade; every other edge is a crisp lit rim of ice."""
    m2 = soft_lower(k, prof)
    ice_ = ~m2
    ops = Ops(ice_, fill_u, fill_l)
    rt = GD.runs_from_top(m2)
    q = [bool((k >> b) & 1) for b in range(4)]
    xs_ = np.arange(N) + 0.5
    left = (xs_ < MID)[None, :]
    nb_cfg = np.where(left, q[0] and not q[2], q[1] and not q[3]).astype(bool)
    yy_ = np.arange(N)[:, None] + 0.5
    col = m2 & (rt <= 6) & nb_cfg & (yy_ > MID - 5) & (yy_ < MID + 10)
    for r_, code in ((1, C('sky_cool', 5)), (2, C('sky_cool', 3)), (3, C('sky_cool', 3)), (4, C('water_cool', 1))):
        sel = col & (rt == r_)
        ops.own[sel] = 2
        ops.ab[sel] = code
    ops.shift(col & ((rt == 5) | (rt == 6)), -1)
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    rim_ = ice_ & ndi.binary_dilation(m2 & ~col, structure=cross)
    ops.own[rim_] = 2
    ops.ab[rim_] = C('sky_cool', 5)
    return ops.encode((slice(T0, T1), slice(T0, T1)))


PAINTERS = {'sunken': sunken, 'bank': bank, 'quay_wall': quay_wall, 'beach': beach, 'plain': plain, 'lip': lip, 'foot': foot,
            'tier_side': tier_side, 'snow_lip': snow_lip, 'snow_fray': snow_fray, 'cornice_bank': cornice_bank,
            'ice_edge': ice_edge}

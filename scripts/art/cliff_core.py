"""Cliff core: one rock system for every cliff (docs/vision/cliff-core.md).

The cliff bake-off (20 to 21 Oct) graded three swatches. The look grader chose organic rock
masses (Sea of Stars' warm, dark, rounded crags); the method grader chose a hybrid. This is
that hybrid, built on the terrace toolkit's soft grid (terrace.py: 8 px grid, 32 px tiers,
5 px side bands, 8 px cast shadows):

- Structure (strata). The input is a world height field in plan space. Every rim is a contour
  of that field at a tier height, traced as a closed polyline with arc length (not a column
  per x). Every face pixel carries its arc along the rim, its depth below the rim and its
  absolute height z. Rock bands are fixed in absolute height (a STRATA table per setting), so
  one band runs through every face of a region whatever its outline.
- Noise. Every random choice is a hash of world coordinates (or of a contour's arc and z),
  numpy-vectorised, so any window of the world renders the same pixels: two adjacent 256 px
  tiles meet with no seam (`--check` tests it).
- Look (masses). Inside the bands, the rock is a row of large crag forms split by vertical
  fissures, each shaded as one rounded lump lit from the upper left (the bake-off's
  `shade_mass`), then split into quiet rounded plates; the bands show as partings inside each
  mass, so neighbouring masses read as one layered crag, not a pile of boulders.
- Kit (dressing by rule). Grass fringes, ivy and cascading greenery hang from rims, plants sit
  in fissures, scree and boulders gather at feet, falls leave spring lines in bays and drop into
  plunge pools, snow lies on the high tops with drifts against the cliff foot. Nothing is placed
  by a coordinate: each piece is a rule over the contours and the height field.

Every pixel is a (family, tone) cell of the house palette (art/house-palette.json), so a shadow
is a step along the pixel's own ramp. The one new family is `crag` (accent:highland).

HOWTO (a lane): build a plan height field (or rims as curves, `from_rims`), pick a table, render.
    import cliff_core as cc
    world = cc.World(Z, table='highland', path=PATH_MASK, water=STREAM_MASK, stairs=[...])
    img = cc.render(world).image()                # or render(world, box=(x0, y0, x1, y1))
    tiers = cc.walk_tiers(world)                  # terrace.from_plan's screen tier map, 8 px cells
The four demos below (`demo_highland`, `demo_coast`, `demo_canyon`, `demo_city`) are one screen
each and are meant to be copied.

Run:
    python3 scripts/art/cliff_core.py            # write the demos and proofs (art-repro runs this)
    python3 scripts/art/cliff_core.py --check    # seam test, detail bar and lint on three random
                                                 # outlines; exits non-zero on a fault
    python3 scripts/art/cliff_core.py --compare REFDIR OUT.png   # the highland demo beside the
                                                 # official references (local screenshots only)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import house_palette as hp  # noqa: E402
from terrace import FACE, GRID, SHADOW, STRIP, from_plan  # noqa: E402

OUT_DIR = os.path.join(ROOT, 'docs', 'vision', 'cliff-core')

# ---- the palette: every pixel is (family id, tone 0..5, or 6 for the family's edge tone) ------
_PAL = hp.load()
NAMES = list(_PAL['ramps'])
FID = {n: i for i, n in enumerate(NAMES)}
EDGE = 6
LUT = np.zeros((len(NAMES), 7, 3), np.uint8)
for _i, _n in enumerate(NAMES):
    _r = _PAL['ramps'][_n]
    LUT[_i, :6] = [hp.hex_rgb(c) for c in _r]
    _e = _PAL['edges'].get(hp.family(_n))
    LUT[_i, 6] = hp.hex_rgb(_e) if _e else hp.hex_rgb(_r[0])


def sibs(base: str) -> np.ndarray:
    """A family and its warm and cool siblings, as ids (base, warm, cool)."""
    return np.array([FID[base], FID[base + '_warm'], FID[base + '_cool']], np.int32)


# ---- hash noise on world coordinates ---------------------------------------------------------
_M32 = 0xFFFFFFFF


def _u32(v) -> np.ndarray:
    return (np.asarray(v, dtype=np.int64) & _M32).astype(np.uint32)


def _mix(h: np.ndarray) -> np.ndarray:
    h = h ^ (h >> np.uint32(16))
    h = h * np.uint32(0x7FEB352D)
    h = h ^ (h >> np.uint32(15))
    h = h * np.uint32(0x846CA68B)
    return h ^ (h >> np.uint32(16))


def hashu(seed, *vals) -> np.ndarray:
    """A 32-bit hash of integers (arrays broadcast): the same inputs always give the same
    bits, on any machine. Only integer arithmetic, so art-repro holds bit for bit."""
    with np.errstate(over='ignore'):
        h = _mix(_u32(seed) * np.uint32(0x9E3779B1) + np.uint32(0x7F4A7C15))
        for v in vals:
            h = _mix(h ^ (_u32(v) * np.uint32(0x85EBCA6B)))
    return h


def h01(seed, *vals) -> np.ndarray:
    """Hash noise in [0, 1)."""
    return hashu(seed, *vals).astype(np.float64) * (1.0 / 4294967296.0)


def _smooth(f):
    return f * f * (3.0 - 2.0 * f)


def vnoise2(x, y, scale: float, seed) -> np.ndarray:
    """Smooth value noise in [0, 1) on world coordinates, cell `scale` px."""
    gx = np.asarray(x, np.float64) / scale
    gy = np.asarray(y, np.float64) / scale
    ix, iy = np.floor(gx), np.floor(gy)
    fx, fy = _smooth(gx - ix), _smooth(gy - iy)
    ix, iy = ix.astype(np.int64), iy.astype(np.int64)
    a, b = h01(seed, ix, iy), h01(seed, ix + 1, iy)
    c, d = h01(seed, ix, iy + 1), h01(seed, ix + 1, iy + 1)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def vnoise1(t, scale: float, seed) -> np.ndarray:
    g = np.asarray(t, np.float64) / scale
    i = np.floor(g)
    f = _smooth(g - i)
    i = i.astype(np.int64)
    a, b = h01(seed, i), h01(seed, i + 1)
    return a + (b - a) * f


def fbm2(x, y, scale: float, seed, octaves: int = 3) -> np.ndarray:
    out = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        out = out + amp * vnoise2(x, y, scale / (2 ** o), hashu(seed, o))
        tot += amp
        amp *= 0.5
    return out / tot


# ---- the settings: STRATA tables -------------------------------------------------------------
# Bands are (thickness px, rock family, texture) from z = 0 upward, repeating, so any height has
# a band. A band's family is the bias of its plates among the family's siblings. `spring` is
# the z of a spring line (the top of an impermeable band), where falls leave the face.
STRATA = {
    'highland': dict(
        face=FACE, rock='crag', built=False,
        bands=[(9, 'crag_cool', 'plain'), (7, 'crag', 'lamina'), (11, 'crag_warm', 'plain'),
               (5, 'crag_cool', 'pebble'), (9, 'crag', 'plain'), (6, 'crag_warm', 'lamina'),
               (10, 'crag', 'flute'), (7, 'crag_cool', 'plain')],
        spring=52, mass_w=(18, 46), split64=0.7, split32=0.1, plate=(9.0, 7.0), inset=0.35,
        top='grass', top_sibs=(0.24, 0.02, 0.74), warm_lit=0.15, fringe='grass', fringe_len=(1, 5),
        ivy=0.14, cascade=0.12, crack_plants=0.5, scree=0.55, boulders=0.22, ferns=0.7,
        shrubs=0.006, trees=0.0015, flowers=0.05, snow_z=96, falls=0.5, tint=0),
    'coast': dict(
        face=FACE, rock='sand', built=False,
        bands=[(6, 'basalt', 'plain'), (8, 'basalt_cool', 'pebble'), (10, 'sand_cool', 'lamina'),
               (7, 'sand', 'plain'), (5, 'bleached', 'lamina'), (9, 'sand_warm', 'flute'),
               (6, 'sand_cool', 'plain'), (8, 'sand', 'lamina')],
        spring=None, mass_w=(20, 52), split64=0.6, split32=0.15, plate=(10.5, 6.0), inset=0.3,
        top='grass', floor={0: 'sand'}, top_sibs=(0.45, 0.25, 0.30), fringe='grass', fringe_len=(1, 4),
        ivy=0.0, cascade=0.04, crack_plants=0.3, scree=0.4, boulders=0.3, ferns=0.0,
        shrubs=0.01, trees=0.0, flowers=0.08, snow_z=None, falls=0.0, tint=0),
    'canyon': dict(
        face=40, rock='adobe', built=False,
        bands=[(7, 'clay_cool', 'plain'), (5, 'adobe', 'lamina'), (9, 'clay', 'plain'),
               (4, 'bleached', 'pebble'), (8, 'adobe_warm', 'flute'), (6, 'clay_warm', 'lamina'),
               (10, 'adobe', 'plain'), (5, 'bleached_warm', 'lamina')],
        spring=None, mass_w=(22, 56), split64=0.55, split32=0.2, plate=(13.0, 7.0), inset=0.25,
        top='sand', shrub='cactus', top_sibs=(0.45, 0.30, 0.25), fringe='crumble', fringe_len=(0, 3),
        ivy=0.0, cascade=0.0, crack_plants=0.12, scree=0.75, boulders=0.35, ferns=0.0,
        shrubs=0.006, trees=0.0, flowers=0.0, snow_z=None, falls=0.0, tint=0),
    'city': dict(
        face=40, rock='ashlar', built=True,
        bands=[(7, 'ashlar', 'course'), (6, 'ashlar_warm', 'course'), (7, 'ashlar_cool', 'course'),
               (6, 'ashlar', 'course'), (7, 'ashlar_warm', 'course'), (7, 'ashlar_cool', 'course')],
        spring=None, mass_w=(8, 15), split64=0.0, split32=0.0, plate=(12.0, 7.0), inset=0.0,
        top='stone', top_sibs=(0.45, 0.30, 0.25), fringe='coping', fringe_len=(3, 3),
        ivy=0.12, cascade=0.0, crack_plants=0.25, scree=0.0, boulders=0.0, ferns=0.0,
        shrubs=0.0, trees=0.0, flowers=0.0, snow_z=None, falls=0.0, tint=0),
}


def band_table(table: dict):
    """The band bounds (z of each band's bottom) over one period, and their families."""
    th = np.array([b[0] for b in table['bands']], np.float64)
    bounds = np.concatenate([[0.0], np.cumsum(th)])
    fams = [b[1] for b in table['bands']]
    tex = [b[2] for b in table['bands']]
    return bounds, fams, tex


# ---- the world --------------------------------------------------------------------------------
@dataclass
class Stair:
    """A stair cut through a face, in plan coordinates: open width x0..x1, the plan row of its
    foot `py` (the first row of the lower ground in front), from `z_low` up to `z_high`.
    Risers are 4 px, treads 3 px (terrace.RISER; size-guide 7); cheeks come from the side
    bands of the notch."""
    x0: int
    x1: int
    py: int
    z_low: int
    z_high: int
    tread: int = 3
    riser: int = 4


@dataclass
class World:
    """A world height field in plan space: Z[py, x] is the height (px) of the ground standing
    at plan row py. Screen row = py - top - Z, so the array carries `top` extra rows above the
    screen for the high tiers (top >= Z.max()). Optional plan masks: `path` (trodden ground on a
    top), `water` (streams and ponds on a top), `snow` (forced snow; the table's rule adds more)."""
    Z: np.ndarray
    table: str = 'highland'
    seed: int = 1
    top: int | None = None
    path: np.ndarray | None = None
    water: np.ndarray | None = None
    snow: np.ndarray | None = None
    stairs: list = field(default_factory=list)
    _geo: dict | None = None

    def __post_init__(self):
        self.Z = np.asarray(self.Z, np.int32).copy()
        if self.top is None:
            self.top = int(self.Z.max())
        # the screen's last rows show ground standing further south in plan: carry the field
        # on past its southern edge, so a raised tier there still covers the screen
        self._h = self.Z.shape[0] - self.top
        extra = int(self.Z.max()) + 1
        self.Z = np.concatenate([self.Z, np.repeat(self.Z[-1:], extra, 0)], 0)
        for name in ('path', 'water', 'snow'):
            m = getattr(self, name)
            if m is not None:
                m = np.asarray(m, bool)
                setattr(self, name, np.concatenate([m, np.repeat(m[-1:], extra, 0)], 0))
        self.T = STRATA[self.table]
        self._step_steep()
        self.flag = np.zeros(self.Z.shape, np.int8)       # 1 a stair
        for st in self.stairs:
            self._carve(st)

    def _step_steep(self, chunk: int = 2 * GRID, steep: float = 1.3):
        """Where a rim runs steeply (more than `steep` rows a column, about 52 degrees from
        east-west), its face would be a thin slanted strip. Cap it instead as short stepped
        faces: the rim is held level across each 8 px cell of the soft grid (at the row it has
        in the cell's middle), so the run becomes a stair of short full-height faces with side
        bands between them. Applied per tier level, lowest first; a higher tier is never cut."""
        Z = self.Z
        R, C = Z.shape
        face = self.T['face']
        for k in range(face, int(Z.max()) + 1, face):
            M = Z >= k
            edge = M[:-1] & ~M[1:]
            rows = [np.nonzero(edge[:, x])[0] for x in range(C)]

            def near_row(xx, r):
                rr = rows[min(max(xx, 0), C - 1)]
                if not len(rr):
                    return None
                j = int(np.argmin(np.abs(rr - r)))
                return int(rr[j]) if abs(int(rr[j]) - r) <= 48 else None
            moves = []
            for x in range(C):
                for r in rows[x]:
                    r = int(r)
                    a, b = near_row(x - 4, r), near_row(x + 4, r)
                    if a is None or b is None or abs(b - a) / 8.0 <= steep:
                        continue
                    rc = near_row((x // chunk) * chunk + chunk // 2, r)
                    if rc is not None and rc != r:
                        moves.append((x, r, rc))
            for x, r, rc in moves:
                below = Z[min(r + 1, R - 1), x]
                if rc > r:
                    seg = Z[r + 1:rc + 1, x]
                    Z[r + 1:rc + 1, x] = np.where(seg < k, k, seg)
                else:
                    seg = Z[rc + 1:r + 1, x]
                    Z[rc + 1:r + 1, x] = np.where(seg == k, below, seg)
            if not moves:
                continue
            # soften the steps' corners (no hard edges), only near the runs that were stepped
            import terrace
            near_cols = np.zeros(C, bool)
            for x, _r, _rc in moves:
                near_cols[max(0, x - 8):x + 9] = True
            M0 = Z >= k
            M1 = terrace.rounded(M0, 4, 3) & np.pad(M0, 0)
            M1 |= terrace.rounded(M0, 4, 3) & ~M0
            add = M1 & ~M0 & near_cols[None, :]
            rem = M0 & ~M1 & near_cols[None, :] & (Z == k)
            Z[add] = k
            for r in range(R - 2, -1, -1):
                row = rem[r]
                if row.any():
                    Z[r, row] = Z[r + 1, row]

    @property
    def width(self) -> int:
        return self.Z.shape[1]

    @property
    def height(self) -> int:
        return self._h

    def _carve(self, st: Stair):
        """Cut the stair into the field: steps falling south, the notch's back corners rounded
        (a 4 px radius, so the notch is not a box)."""
        n = (st.z_high - st.z_low) // st.riser
        top_row = st.py - n * st.tread
        # the rim runs straight across the stair and a cheek's width either side (a buttress),
        # so every step meets the face square
        for x in range(max(0, st.x0 - 6), min(self.Z.shape[1], st.x1 + 6)):
            for r in range(max(0, top_row - 4), min(self.Z.shape[0], st.py + 48)):
                if r < st.py and self.Z[r, x] == st.z_low:
                    self.Z[r, x] = st.z_high
                elif r >= st.py and self.Z[r, x] == st.z_high:
                    self.Z[r, x] = st.z_low
        for k in range(n):
            z = st.z_high - st.riser * (k + 1)
            r0 = top_row + k * st.tread
            for r in range(r0, r0 + st.tread):
                for x in range(st.x0, st.x1):
                    if 0 <= r < self.Z.shape[0] and 0 <= x < self.Z.shape[1]:
                        # round the notch's two back corners
                        dr = r - top_row
                        cx = min(x - st.x0, st.x1 - 1 - x)
                        if dr < 4 and cx < 4 and (4 - cx) ** 2 + (4 - dr) ** 2 > 17:
                            continue
                        if st.z_low < self.Z[r, x] <= st.z_high:
                            self.Z[r, x] = min(self.Z[r, x], z)
                            self.flag[r, x] = 1

    # ---- the contours: every rim as a closed polyline with arc length -------------------------
    def geometry(self) -> dict:
        if self._geo is None:
            self._geo = contours(self.Z, self.T['face'])
        return self._geo


def contours(Z: np.ndarray, face: int) -> dict:
    """Trace every rim of the height field: for each tier level k (a multiple of the table's
    face height), the boundary of Z >= k as closed crack-following loops (pixel edges, inside
    on the left), smoothed and measured by arc length. Returns per plan pixel, for the south
    edge of a pixel whose southern neighbour is lower: the loop id, the arc at that edge and the
    outward normal's x (negative: the face turns west, to the light), and the loops themselves.
    Deterministic and global, so every window of the world sees the same arcs."""
    R, C = Z.shape
    arc = np.full((R, C), np.nan, np.float64)
    loop = np.full((R, C), -1, np.int32)
    nrm = np.zeros((R, C), np.float64)
    bend = np.zeros((R, C), np.float64)
    loops = []
    levels = sorted({int(v) for v in np.unique(Z) if v > Z.min() and v % face == 0}
                    | {k for k in range(face, int(Z.max()) + 1, face)})
    for k in levels:
        M = np.pad(Z >= k, 1, mode='edge')    # the world carries on past its edge
        M = np.pad(M, 1)                       # then closes, out of sight
        _trace(M, k, loops, arc, loop, nrm, bend, Z)
    return dict(arc=arc, loop=loop, nx=nrm, bend=bend, loops=loops)


_DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))     # E, S, W, N in (row, col)


def _trace(M, level, loops, arc, loop, nrm, bend, Z):
    R, C = M.shape
    W1 = C + 1
    edges = {}          # start vertex -> list of (end vertex, dir, inside pixel, kind)
    inside = M
    outS = inside[:-1, :] & ~inside[1:, :]
    outN = inside[1:, :] & ~inside[:-1, :]
    outE = inside[:, :-1] & ~inside[:, 1:]
    outW = inside[:, 1:] & ~inside[:, :-1]
    for r, c in zip(*np.nonzero(outS)):       # pixel (r, c), south edge: (r+1, c) -> (r+1, c+1)
        edges.setdefault((r + 1) * W1 + c, []).append(((r + 1) * W1 + c + 1, 0, r, c))
    for r, c in zip(*np.nonzero(outN)):       # pixel (r+1, c), north edge: (r+1, c+1) -> (r+1, c)
        edges.setdefault((r + 1) * W1 + c + 1, []).append(((r + 1) * W1 + c, 2, r + 1, c))
    for r, c in zip(*np.nonzero(outE)):       # pixel (r, c), east edge: (r+1, c+1) -> (r, c+1)
        edges.setdefault((r + 1) * W1 + c + 1, []).append((r * W1 + c + 1, 3, r, c))
    for r, c in zip(*np.nonzero(outW)):       # pixel (r, c+1), west edge: (r, c+1) -> (r+1, c+1)
        edges.setdefault(r * W1 + c + 1, []).append(((r + 1) * W1 + c + 1, 1, r, c + 1))
    used = set()
    for v0 in sorted(edges):
        for i0 in range(len(edges[v0])):
            if (v0, i0) in used:
                continue
            seq = []
            v, i = v0, i0
            while (v, i) not in used:
                used.add((v, i))
                e = edges[v][i]
                seq.append((v, e))
                nv, d = e[0], e[1]
                outs = edges.get(nv, [])
                if len(outs) == 1:
                    v, i = nv, 0
                else:          # a saddle: turn left first (keeps diagonal inside pixels apart)
                    pref = [(d - 1) % 4, d, (d + 1) % 4]
                    best = min(range(len(outs)), key=lambda j: pref.index(outs[j][1]) if outs[j][1] in pref else 9)
                    v, i = nv, best
            _measure(seq, W1, level, loops, arc, loop, nrm, bend, Z)


def _measure(seq, W1, level, loops, arc, loop, nrm, bend, Z):
    n = len(seq)
    pts = np.array([(v // W1, v % W1) for v, _e in seq], np.float64)
    # smooth the staircase into a curve (circular moving average, two passes of 7)
    sm = pts
    for _ in range(2):
        acc = np.zeros_like(sm)
        for k in range(-3, 4):
            acc += np.roll(sm, k, axis=0)
        sm = acc / 7.0
    seg = np.sqrt(((np.roll(sm, -1, axis=0) - sm) ** 2).sum(1))
    cum = np.concatenate([[0.0], np.cumsum(seg)[:-1]])
    mid = cum + seg * 0.5
    tang = np.roll(sm, -3, axis=0) - np.roll(sm, 3, axis=0)
    tl = np.sqrt((tang ** 2).sum(1)) + 1e-9
    tr = tang[:, 0] / tl
    t1 = sm - np.roll(sm, 6, axis=0)
    t2 = np.roll(sm, -6, axis=0) - sm
    cross = (t1[:, 0] * t2[:, 1] - t1[:, 1] * t2[:, 0]) / (np.sqrt((t1 ** 2).sum(1) * (t2 ** 2).sum(1)) + 1e-9)
    lid = len(loops)
    loops.append(dict(level=level, length=float(cum[-1] + seg[-1]), n=n, arc=cum,
                      row=sm[:, 0] - 2, col=sm[:, 1] - 2))
    R, C = Z.shape
    south = np.array([e[1] == 0 for _v, e in seq])
    bays = []
    for j in np.nonzero(south & (cross < -0.18))[0]:
        lo, hi = j - 10, j + 11
        win = np.take(cross, np.arange(lo, hi), mode='wrap')
        if cross[j] <= win.min():
            e = seq[j][1]
            bays.append((float(mid[j]), int(e[2] - 2), int(e[3] - 2)))
    loops[-1]['bays'] = bays
    for j, (_v, e) in enumerate(seq):
        if e[1] != 0:
            continue
        r, c = e[2] - 2, e[3] - 2          # back to field coordinates (two pads)
        if 0 <= r < R and 0 <= c < C and Z[r, c] == level:
            arc[r, c] = mid[j]
            loop[r, c] = lid
            nrm[r, c] = -tr[j]            # outward normal (tc, -tr): its column part
            bend[r, c] = cross[j]


# ---- the painter: plan to screen ----------------------------------------------------------
TOP, FACEK = 1, 2


class Frame:
    """The render of one window of the world: per-pixel family and tone, plus what each pixel
    is (labels) and the geometry it came from. Arrays are window-sized (with the margin)."""

    def __init__(self, world: World, x0, y0, x1, y1):
        self.world, self.x0, self.y0, self.x1, self.y1 = world, x0, y0, x1, y1
        h, w = y1 - y0, x1 - x0
        self.shape = (h, w)
        self.F = np.full((h, w), FID['grass'], np.int32)
        self.T = np.full((h, w), 3, np.int32)
        self.tag = np.zeros((h, w), np.int32)
        self.extra = {}                   # (y, x) -> rgb: a sprite pasted for scale, off the palette
        ys, xs = np.mgrid[y0:y1, x0:x1]
        self.X, self.Y = xs, ys          # world screen coordinates of every pixel

    def image(self, crop=None) -> Image.Image:
        rgb = LUT[self.F, np.clip(self.T, 0, 6)]
        for (y, x), c in self.extra.items():
            rgb[y, x] = c
        im = Image.fromarray(rgb, 'RGB')
        return im.crop(crop) if crop else im


TAG = dict(ground=1, rock=2, recess=3, leaf=4, water=5, snow=6, path=7, stair=8, side=9, fringe=10,
           scree=11, figure=12, foam=13, wet=14, tree=15)


def project(world: World, x0, y0, x1, y1) -> dict:
    """The painter's walk (north to south, nearer ground drawn over farther): each plan pixel
    draws its top at screen row py - top - z, and where its southern neighbour is lower a face
    drops to it. Every face pixel keeps its rim pixel (plan row), rim height, foot height and
    depth below the rim. Vectorised per plan row."""
    Z, top, flag = world.Z, world.top, world.flag
    PH, PW = Z.shape
    h, w = y1 - y0, x1 - x0
    kind = np.zeros((h, w), np.int8)
    PY = np.full((h, w), -1, np.int32)
    ZH = np.zeros((h, w), np.int32)
    Z2 = np.zeros((h, w), np.int32)
    D = np.zeros((h, w), np.int32)
    ST = np.zeros((h, w), np.int8)
    cx0, cx1 = max(0, x0), min(PW, x1)
    if cx0 >= cx1:
        return dict(kind=kind, PY=PY, ZH=ZH, Z2=Z2, D=D, ST=ST)
    xs = np.arange(cx0, cx1)
    lo = max(0, y0 + top - 1)
    hi = min(PH, y1 + top + int(Z.max()) + 1)
    for py in range(lo, hi):
        z = Z[py, cx0:cx1]
        z2 = Z[py + 1, cx0:cx1] if py + 1 < PH else z
        fl = flag[py, cx0:cx1]
        sy = py - top - z
        r = sy - y0
        ok = (r >= 0) & (r < h)
        cc = xs[ok] - x0
        rr = r[ok]
        kind[rr, cc] = TOP
        PY[rr, cc] = py
        ZH[rr, cc] = z[ok]
        Z2[rr, cc] = z[ok]
        D[rr, cc] = 0
        ST[rr, cc] = fl[ok]
        dz = z - z2
        if dz.max() <= 0:
            continue
        fl2 = np.maximum(fl, flag[py + 1, cx0:cx1] if py + 1 < PH else fl)
        for d in range(1, int(dz.max()) + 1):
            rr = r + d
            ok = (dz >= d) & (rr >= 0) & (rr < h)
            if not ok.any():
                continue
            cc = xs[ok] - x0
            rr = rr[ok]
            kind[rr, cc] = FACEK
            PY[rr, cc] = py
            ZH[rr, cc] = z[ok]
            Z2[rr, cc] = z2[ok]
            D[rr, cc] = d
            ST[rr, cc] = fl2[ok]
    return dict(kind=kind, PY=PY, ZH=ZH, Z2=Z2, D=D, ST=ST)


# ---- small array helpers (edge-replicating shifts: no wrap-around, so windows agree) ---------
def nb(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """out[y, x] = a[y + dy, x + dx], the window's edge carried on."""
    h, w = a.shape
    p = max(abs(dy), abs(dx))
    big = np.pad(a, p, mode='edge')
    return big[p + dy:p + dy + h, p + dx:p + dx + w]


def step(fr: Frame, mask: np.ndarray, d: int, lo: int = 0, hi: int = 5):
    m = mask & (fr.T != EDGE)
    fr.T[m] = np.clip(fr.T[m] + d, lo, hi)


SIB_BIAS = {'': (0.56, 0.22, 0.22), '_warm': (0.25, 0.60, 0.15), '_cool': (0.25, 0.15, 0.60)}


def _sib_of(name: str):
    base = hp.family(name)
    tag = name[len(base):]
    return base, SIB_BIAS.get(tag, SIB_BIAS[''])


# ---- what lies on a top (a pure function of the plan, so every window agrees) ---------------
MAT_GROUND, MAT_SNOW, MAT_PATH, MAT_WATER = 0, 1, 2, 3


def top_material(world: World, py, x, z) -> np.ndarray:
    """The material of a top pixel at plan (py, x), height z: water and path from the world's
    masks, snow by the table's rule (tops at or above snow_z where a broad world field is high,
    with 6 px scallops on its margin), else the table's ground."""
    T = world.T
    out = np.zeros(np.shape(py), np.int8)
    sz = T.get('snow_z')
    if sz is not None:
        sy = py - world.top - z
        n = fbm2(x, sy, 64.0, hashu(world.seed, 301), 2) + 0.035 * vnoise2(x, sy, 3.0, hashu(world.seed, 302))
        out[(z >= sz) & (n > 0.53)] = MAT_SNOW
    if world.snow is not None:
        out[world.snow[py, x]] = MAT_SNOW
    if world.path is not None:
        out[world.path[py, x]] = MAT_PATH
    if world.water is not None:
        out[world.water[py, x]] = MAT_WATER
    return out


# ---- the ground on the tops ------------------------------------------------------------------
def paint_ground(fr: Frame, P: dict, world: World):
    """The house ground recipe: one family at body tone, broad soft patches of its siblings at
    the same tone, a blade texture of short upright dominoes (mostly sibling swaps), then tufts,
    clover and flowers in clusters (dress_ground, below). Paths are trodden earth a tone down at
    their edges; snow is a calm plane with swells (paint_snow)."""
    T, seed = world.T, world.seed
    K = P['kind']
    top = (K == TOP) & (P['ST'] == 0)
    X, Y = fr.X, fr.Y
    py = np.clip(P['PY'], 0, world.Z.shape[0] - 1)
    xw = np.clip(X, 0, world.width - 1)
    mat = np.where(top, top_material(world, py, xw, P['ZH']), -1)
    fr.mat = mat
    # ground
    g = top & (mat == MAT_GROUND)
    n = fbm2(X, Y, 16.0, hashu(seed, 11), 3)
    pb, pw, pc = T['top_sibs']
    lo_c, hi_w = 0.2 + 0.6 * pc, 0.8 - 0.6 * pw
    fi = np.where(n < lo_c, 2, np.where(n > hi_w, 1, 0))
    floors = T.get('floor', {})
    for fam_name in sorted({T['top']} | set(floors.values())):
        other = [z for z, f in floors.items() if f != fam_name]
        mine = [z for z, f in floors.items() if f == fam_name]
        gm = g & (np.isin(P['ZH'], mine) if fam_name != T['top'] else ~np.isin(P['ZH'], other))
        fams = sibs(fam_name)
        fr.F[gm] = fams[fi[gm]]
        fr.T[gm] = 3
        fr.tag[gm] = TAG['ground']
        if fam_name == 'grass':
            _blades(fr, gm, fams, fi, hashu(seed, 12), density=1.5, warm_lit=T.get('warm_lit', 0.5))
        elif fam_name == 'stone':
            _setts(fr, gm, fams, seed)
        else:
            _grains(fr, gm, fams, fi, hashu(seed, 16))
    # trodden path
    p = top & (mat == MAT_PATH)
    pf = sibs('path')
    n2 = vnoise2(X, Y, 9.0, hashu(seed, 13))
    fr.F[p] = pf[np.where(n2 < 0.3, 2, np.where(n2 > 0.75, 1, 0))[p]]
    fr.T[p] = 3
    fr.tag[p] = TAG['path']
    edge_p = p & ~(nb(p, 0, 1) & nb(p, 0, -1) & nb(p, 1, 0) & nb(p, -1, 0))
    fr.T[edge_p] = 2
    peb = p & ~edge_p & (h01(hashu(seed, 14), X // 3, Y // 2) < 0.06) & ((X % 3) < 2)
    fr.T[peb] = 4
    fr.T[peb & (h01(hashu(seed, 15), X, Y) < 0.3)] = 2


def _blades(fr, mask, fams, fi, seed, density=0.5, warm_lit=0.5):
    """Grass clusters (Eastward's ground: calm, with clumps rather than speckle): a 3 x 3 cell
    holds one cluster of 2 to 4 px (an upright domino, an L, a 2 x 2 tuft, a stalk of 3);
    most swap to a sibling at the same tone, some catch the light (a tone up), some sit in
    shade (a tone down), a few are leaf. Thick in rough stretches, thin in calm ones."""
    X, Y = fr.X, fr.Y
    cx, cy = X // 3, Y // 3
    hh = h01(seed, cx, cy)
    ox = (hashu(seed, cx, cy, 1) % np.uint32(2)).astype(np.int64)
    oy = (hashu(seed, cx, cy, 2) % np.uint32(2)).astype(np.int64)
    dx, dy = X - 3 * cx - ox, Y - 3 * cy - oy
    shape = (hashu(seed, cx, cy, 5) % np.uint32(4)).astype(np.int64)
    inside = np.where(shape == 0, (dx == 0) & ((dy == 0) | (dy == 1)),
                      np.where(shape == 1, ((dx == 0) & ((dy == 0) | (dy == 1))) | ((dx == 1) & (dy == 1)),
                               np.where(shape == 2, ((dx == 0) | (dx == 1)) & ((dy == 0) | (dy == 1)),
                                        (dx == 0) & (dy >= -1) & (dy <= 1))))
    dens = density * (0.45 + 0.7 * vnoise2(X, Y, 13.0, hashu(seed, 9)))
    on = mask & (hh < dens) & inside
    kind = h01(seed, cx, cy, 3)
    swap = on & (kind < 0.45)
    alt = (fi + 1 + (hashu(seed, cx, cy, 4) & np.uint32(1)).astype(np.int64)) % 3
    fr.F[swap] = fams[alt[swap]]
    up = on & (kind >= 0.45) & (kind < 0.66)
    fr.T[up] = np.minimum(4, fr.T[up] + 1)
    fr.F[up & (h01(seed, cx, cy, 6) < warm_lit)] = fams[1]
    fr.F[up & (h01(seed, cx, cy, 6) >= 0.6)] = fams[2]
    down = on & (kind >= 0.66) & (kind < 0.86)
    fr.T[down] = np.maximum(1, fr.T[down] - 1)
    fr.F[down & (h01(seed, cx, cy, 7) < 0.5)] = fams[2]
    leaf = on & (kind >= 0.86)
    lf = sibs('leaf')
    fr.F[leaf] = lf[(hashu(seed, cx, cy, 8) % np.uint32(3)).astype(np.int64)[leaf]]
    lt = h01(seed, cx, cy, 10)
    fr.T[leaf] = np.where(lt < 0.25, 2, np.where(lt > 0.7, 4, 3))[leaf]


def _grains(fr, mask, fams, fi, seed):
    """Sand and dry ground: broad soft patches (as grass), wind ripples as short lit and
    shaded dashes lying east-west, a few sibling clusters."""
    X, Y = fr.X, fr.Y
    r = vnoise2(X, Y * 3.0, 6.0, hashu(seed, 1))
    rip = mask & (h01(seed, X // 4, Y, 2) < 0.44) & (np.mod(X, 4) < 3)
    fr.T[rip & (r > 0.5)] = 4
    fr.T[rip & (r <= 0.5)] = 2
    sw = mask & ~rip & (h01(seed, X // 2, Y // 2, 3) < 0.4)
    fr.F[sw] = fams[(fi[sw] + 1) % 3]
    # broad patches of a second dry family (bleached sand, packed earth), at the same tone
    pf = sibs('adobe') if fams[0] in sibs('sand') else sibs('earth')
    pt = mask & (vnoise2(X, Y, 23.0, hashu(seed, 6)) > 0.7)
    fr.F[pt] = pf[fi[pt]]
    # grit: small stones of the rock above, two px each, lit on top
    gr = mask & (h01(seed, X // 3, Y // 2, 4) < 0.07) & (np.mod(X, 3) < 2)
    gf = sibs('stone') if fams[0] != FID['stone'] else sibs('earth')
    fr.F[gr] = gf[(hashu(seed, X // 3, Y // 2, 5) % np.uint32(3)).astype(np.int64)[gr]]
    fr.T[gr] = np.where(np.mod(Y[gr], 2) == 0, 4, 2)


def _setts(fr, mask, fams, seed):
    """Setts 5 x 4 laid in courses in world coordinates (size-guide 3: so they run on from
    zone to zone): each a soft pillow, lit on its top-left, a dark joint on its bottom and
    right, one of three siblings, the odd one a tone off."""
    X, Y = fr.X, fr.Y
    row = Y // 4
    q = X + 2 * (row % 2) + (hashu(seed, row, 17) % np.uint32(2)).astype(np.int64)
    col = q // 5
    sh = hashu(seed, row, col, 18)
    t = np.full(X.shape, 3)
    t = np.where(np.mod(Y, 4) == 0, 4, t)
    t = np.where(np.mod(q, 5) == 0, 4, t)
    t = np.where(np.mod(Y, 4) == 3, 2, t)
    t = np.where(np.mod(q, 5) == 4, 2, t)
    off = h01(sh, 1)
    t = np.where((off < 0.12) & (t >= 2), t - 1, np.where((off > 0.94) & (t <= 3), t + 1, t))
    fr.F[mask] = fams[(hashu(sh, 2) % np.uint32(3)).astype(np.int64)][mask]
    fr.T[mask] = t[mask]


# ---- the faces: crag masses on absolute-height strata ----------------------------------------
def _breaks(world, lid, course, length):
    cache = world.__dict__.setdefault('_breaks', {})
    key = (int(lid), course)
    if key not in cache:
        T, seed = world.T, world.seed
        lo, hi = T['mass_w']
        if lid < 0:
            length = world.width + 2 * hi
        n = int(length / lo) + 4
        k = np.arange(n)
        wv = lo + (hi - lo) * h01(seed, lid, k, course, 31) ** 1.15
        start = -hi * h01(seed, lid, course, 32)
        cache[key] = np.concatenate([[start], start + np.cumsum(wv)])
    return cache[key]


def _segment(world, lid, s, z, course, length):
    """The crag form a pixel belongs to along its rim: breaks in arc length (widths from the
    table, hashed per loop), each break wandering 1.5 px with height, so fissures are not ruled.
    Returns the segment index and its left and right edge at this pixel's height."""
    seed = world.seed
    k = np.zeros(s.shape, np.int64)
    bl = np.zeros(s.shape)
    br = np.zeros(s.shape)
    for L in np.unique(lid):
        m = lid == L
        B = _breaks(world, L, course, length.get(int(L), world.width))
        ss, zz = s[m], z[m]
        i0 = np.clip(np.searchsorted(B, ss, 'right') - 1, 1, len(B) - 3)

        def edge(i):
            return B[i] + 1.5 * (2 * vnoise1(zz, 6.0, hashu(seed, L, i, course, 33)) - 1)
        i = i0 - (ss < edge(i0)) + (ss >= edge(i0 + 1))
        k[m], bl[m], br[m] = i, edge(i), edge(i + 1)
    return k, bl, br


def paint_faces(fr: Frame, P: dict, world: World):
    T, seed = world.T, world.seed
    if T['built']:
        return paint_courses(fr, P, world)
    G = world.geometry()
    K = P['kind']
    sel = (K == FACEK) & (P['ST'] == 0)
    yy, xx = np.nonzero(sel)
    if not len(yy):
        return
    X = fr.X[yy, xx]
    xw = np.clip(X, 0, world.width - 1)
    py = P['PY'][yy, xx]
    h, h2, d = P['ZH'][yy, xx], P['Z2'][yy, xx], P['D'][yy, xx].astype(np.float64)
    Hf = (h - h2).astype(np.float64)
    s = G['arc'][py, xw].copy()
    lid = G['loop'][py, xw].copy()
    nx = G['nx'][py, xw]
    bad = np.isnan(s)
    s[bad] = X[bad]
    lid[bad] = -1
    lengths = {i: L['length'] for i, L in enumerate(G['loops'])}
    zc = h - d + 0.5                                  # absolute height of the pixel
    # courses: the upper crag (from the rim) and, where it splits, a lower one with its own
    # breaks, so fissures never line up from course to course
    ku, blu, bru = _segment(world, lid, s, zc, 0, lengths)
    sp = h01(seed, lid, ku, 34)
    split = np.where(Hf >= 48, sp < T['split64'], sp < T['split32'])
    ds = np.round(Hf * (0.36 + 0.28 * h01(seed, lid, ku, 35)))
    lower = split & (d > ds)
    kl, bll, brl = _segment(world, lid, s, zc, 1, lengths)
    k = np.where(lower, kl, ku)
    bl = np.where(lower, bll, blu)
    br = np.where(lower, brl, bru)
    course = lower.astype(np.int64)
    mass = hashu(seed, lid, k, course, 36)
    # each crag stands upright: its bands and plates are level, measured from the rim at its
    # middle (so a crag on a sloping rim steps instead of shearing) and only clipped by the rim
    yrim = (fr.Y[yy, xx] - d).astype(np.float64)
    yref = yrim.copy()
    sc = (bl + br) / 2
    for L in np.unique(lid):
        if L < 0:
            continue
        m = lid == L
        lp = G['loops'][L]
        rows = np.interp(sc[m], lp['arc'], lp['row'], period=lp['length'])
        yref[m] = rows - 1 - world.top - h[m]
    yref = np.where(np.abs(yref - yrim) > 24, yrim, yref)
    zc = h - (fr.Y[yy, xx] - yref) + 0.5
    inset = np.where(h01(mass, 1) < T['inset'], 1 + np.floor(6 * h01(mass, 2) ** 1.5), 0)
    dtop = np.where(lower, ds + 1, 1 + inset)
    dbot = np.where(split & ~lower, ds, Hf)
    Wm = br - bl
    ce = np.minimum(s - bl, br - s)
    R = np.clip(0.42 * Wm, 3, 9)
    lift = np.where(ce < R, R - np.sqrt(np.maximum(0, R * R - (R - ce) ** 2)), 0) * (0.5 + h01(seed, lid, k, course, 49))
    Rb = np.where(split & ~lower, 3.0, 2.0)
    liftb = np.where(ce < Rb, Rb - np.sqrt(np.maximum(0, Rb * Rb - (Rb - ce) ** 2)), 0)
    dte, dbe = dtop + lift, dbot - liftb
    # a fissure runs down from the rim only part of the way: below it the two crags are one
    # rock (no line between them, house-style: joints only where they make sense)
    fdep = dtop + (dbot - dtop) * np.where(h01(seed, lid, k, course, 47) < 0.55, 1.0, 0.35 + 0.5 * h01(seed, lid, k, course, 48))
    open_f = d <= fdep
    inside = (d >= dte) & (d <= dbe) & ((ce >= 0.9) | ~open_f)
    ce_d = np.where(open_f, ce, ce + 3.0)
    dist = np.minimum(np.minimum(ce_d, d - dte), dbe - d) + 0.5
    Hm = np.maximum(1.0, dbe - dte + 1)
    Dd = np.maximum(2.0, np.minimum(Wm, Hm) * 0.5)
    zz = np.sqrt(np.clip(1 - (1 - np.minimum(dist, Dd) / Dd) ** 2, 0, 1))
    # to the screen grid, for the normals
    shp = fr.shape
    MID = np.full(shp, -1, np.int64)
    MID[yy, xx] = np.where(inside, mass.astype(np.int64), -1)
    ZZ = np.zeros(shp)
    ZZ[yy, xx] = zz
    same_r, same_l = nb(MID, 0, 1) == MID, nb(MID, 0, -1) == MID
    same_d, same_u = nb(MID, 1, 0) == MID, nb(MID, -1, 0) == MID
    gx = (np.where(same_r, nb(ZZ, 0, 1), ZZ) - np.where(same_l, nb(ZZ, 0, -1), ZZ)) / 2
    gy = (np.where(same_d, nb(ZZ, 1, 0), ZZ) - np.where(same_u, nb(ZZ, -1, 0), ZZ)) / 2
    gx, gy = gx[yy, xx], gy[yy, xx]
    Kf = Dd * 0.9
    vx, vy = -gx * Kf, gy * Kf
    nn = np.sqrt(vx * vx + vy * vy + 1.0)
    I = (vx * LIGHT[0] + vy * LIGHT[1] + LIGHT[2]) / nn
    vrel = (d - dte) / Hm
    lean = np.clip(-nx * 2.5, -2, 1)
    I = I + 0.34 * (0.42 - vrel) + 0.07 * lean
    deep = h01(mass, 3) < 0.16
    I = I - np.where(deep, 0.3, 0)
    t = np.where(I > 0.82, 4, np.where(I > 0.5, 3, np.where(I > 0.14, 2, 1)))
    t = np.where((dist <= 2) & (I > 0.97), 5, t)
    t = np.where(d >= dbe - 0.01, np.minimum(t, 1), np.where(d >= dbe - 1, np.minimum(t, 2), t))
    # the band (absolute height, a slow wobble along the rim) and its family
    bounds, bfams, btex = band_table(T)
    period = bounds[-1]
    wob = 1.4 * (2 * vnoise1(s, 21.0, hashu(seed, lid, 37)) - 1)
    zb = np.mod(zc + wob, period)
    band = np.clip(np.searchsorted(bounds, zb, 'right') - 1, 0, len(bfams) - 1)
    # plates: rounded cells in (arc, z), each a sibling, the odd one set back
    Ps, Pz = T['plate']
    gs, gz = s / Ps, zc / Pz
    i0, j0 = np.floor(gs).astype(np.int64), np.floor(gz).astype(np.int64)
    best = np.full(s.shape, 1e9)
    pi, pj = i0.copy(), j0.copy()
    sxs = np.zeros(s.shape)
    szs = np.zeros(s.shape)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = i0 + di, j0 + dj
            jx = ci + 0.05 + 0.9 * h01(seed, lid, ci, cj, 38)
            jz = cj + 0.05 + 0.9 * h01(seed, lid, ci, cj, 39)
            dd = (gs - jx) ** 2 + (gz - jz) ** 2 + 0.18 * h01(seed, lid, ci, cj, 46)
            b = dd < best
            best = np.where(b, dd, best)
            pi, pj = np.where(b, ci, pi), np.where(b, cj, pj)
            sxs, szs = np.where(b, jx * Ps, sxs), np.where(b, jz * Pz, szs)
    pid = hashu(seed, lid, pi, pj, 40)
    PID = np.full(shp, -1, np.int64)
    PID[yy, xx] = pid.astype(np.int64)
    BND = np.full(shp, -1, np.int64)
    BND[yy, xx] = band
    rock = MID >= 0
    sm = lambda dy, dx: (nb(MID, dy, dx) == MID) & rock  # noqa: E731
    jr = (sm(0, 1) & (nb(PID, 0, 1) != PID)) | (sm(1, 0) & (nb(PID, 1, 0) != PID)) \
        | (sm(1, 1) & (nb(PID, 1, 1) != PID))
    lip = (sm(-1, 0) & (nb(PID, -1, 0) != PID)) | (sm(0, -1) & (nb(PID, 0, -1) != PID))
    groove = sm(1, 0) & (nb(BND, 1, 0) != BND)
    blip = sm(-1, 0) & (nb(BND, -1, 0) != BND)
    jr, lip, groove, blip = jr[yy, xx], lip[yy, xx], groove[yy, xx], blip[yy, xx]
    u = (s - bl) / np.maximum(1, Wm)
    t = np.where(h01(pid, 4) < 0.1, t - 1, t)
    t = np.where(lip & ~jr & (t >= 1), t + 1, t)
    t = np.where(blip & (u < 0.7), t + 1, t)
    t = np.where(jr | groove, t - 1, t)
    shade_join = jr & (t <= 0) & (h01(pid, 12) < 0.5)
    # textures of the bands
    tex = np.array(btex)[band]
    lam = (tex == 'lamina') & (np.abs(np.mod(zb - bounds[band], 1e9) - (bounds[band + 1] - bounds[band]) * 0.5) < 0.5) \
        & (vnoise1(s, 6.0, hashu(seed, 41)) > 0.42)
    t = np.where(lam, t - 1, t)
    peb = (tex == 'pebble') & (h01(seed, lid, np.floor(s / 2).astype(np.int64), np.floor(zc / 2).astype(np.int64), 42) < 0.09)
    t = np.where(peb & (t < 4), t + 1, t)
    flute = (tex == 'flute') & (vnoise1(s, 2.5, hashu(seed, lid, 43)) > 0.74)
    # grain: short dashes along the plates, lit on a plate's upper half, shaded on its lower
    gcell = h01(seed, lid, np.floor((s + 7 * pj) / 3).astype(np.int64), np.floor(zc).astype(np.int64), 44)
    dash = gcell < 0.03
    t = np.where(dash, np.where(zc > szs, t + 1, t - 1), t)
    # vertical fissures in the wide crags (the Sea of Stars columns)
    uc = 0.3 + 0.4 * h01(mass, 5)
    fd = 0.45 + 0.5 * h01(mass, 6)
    scr = bl + uc * Wm + 1.2 * (2 * vnoise1(zc, 5.0, hashu(mass, 7)) - 1)
    has = (Wm > 30) & (h01(mass, 10) < 0.6) & ((d - dte) < fd * Hm)
    crack = has & (np.abs(s - scr) < 0.55)
    wall = has & (s - scr >= 0.55) & (s - scr < 1.6)
    t = np.where(wall, t + 1, t)
    t = np.clip(t, 1, 5)
    t = np.where(crack | shade_join, 0, t)
    t = np.where(d >= Hf - 1, np.maximum(0, t - 1), t)     # damp foot
    # families: the band's bias among the rock's siblings, per plate; swaps in clusters
    base_ids, bias = [], []
    for name in bfams:
        b, p = _sib_of(name)
        base_ids.append(sibs(b))
        bias.append(np.cumsum(p))
    base_ids, bias = np.array(base_ids), np.array(bias)
    r = h01(pid, 8)
    si = (r > bias[band, 0]).astype(np.int64) + (r > bias[band, 1]).astype(np.int64)
    swap = (h01(seed, lid, np.floor(s / 2).astype(np.int64), np.floor(zc / 2).astype(np.int64), 45) < 0.08) | flute
    si = np.where(swap, (si + 1 + (h01(pid, 9) < 0.5)) % 3, si)
    fam = base_ids[band, si]
    # recesses: whatever of the face no crag covers (notches between rounded shoulders, insets
    # under the rim, the fissures between crags): deep shade of the band's cool sibling
    rec = ~inside
    fam = np.where(rec, base_ids[band, 2], fam)
    t = np.where(rec, 0, t)
    fr.F[yy, xx] = fam
    fr.T[yy, xx] = t
    fr.tag[yy, xx] = np.where(rec, TAG['recess'], TAG['rock'])
    # keep what the dressing and the checks need
    fr.MID = MID
    fr.face = dict(yy=yy, xx=xx, s=s, lid=lid, d=d, Hf=Hf, h=h, zc=zc, u=u, rec=rec, mass=mass, k=k,
                   crack=crack, ce=ce, Wm=Wm, nx=nx)


LIGHT = np.array([-0.74, 0.56, 0.44])
LIGHT = LIGHT / np.sqrt((LIGHT ** 2).sum())


def paint_courses(fr: Frame, P: dict, world: World):
    """A built face (the city's retaining wall): the same bands, but each band is a course of
    dressed blocks 8 to 15 long laid along the rim (stretcher bond, each course's breaks its
    own), mortar a recess in the cool sibling, each block a soft pillow with a lit top and left,
    the odd block a tone off, moss in the lowest joints."""
    T, seed = world.T, world.seed
    G = world.geometry()
    K = P['kind']
    sel = (K == FACEK) & (P['ST'] == 0)
    yy, xx = np.nonzero(sel)
    if not len(yy):
        return
    X = fr.X[yy, xx]
    xw = np.clip(X, 0, world.width - 1)
    py = P['PY'][yy, xx]
    h, h2, d = P['ZH'][yy, xx], P['Z2'][yy, xx], P['D'][yy, xx].astype(np.float64)
    Hf = (h - h2).astype(np.float64)
    s = G['arc'][py, xw].copy()
    lid = G['loop'][py, xw].copy()
    bad = np.isnan(s)
    s[bad] = X[bad]
    lid[bad] = -1
    zc = h - d + 0.5
    bounds, bfams, _tex = band_table(T)
    period = bounds[-1]
    zb = np.mod(zc, period)
    band = np.clip(np.searchsorted(bounds, zb, 'right') - 1, 0, len(bfams) - 1)
    cyc = np.floor(zc / period).astype(np.int64)
    course = cyc * len(bfams) + band
    lo, hi = T['mass_w']
    # blocks along the arc: per course, a hashed run of lengths (no shared joints between courses)
    off = h01(seed, lid, course, 51) * hi
    q = (s + off)
    bk = np.floor(q / ((lo + hi) / 2)).astype(np.int64)
    # vary block length by moving each joint up to a third of a block
    jit = lambda i: (lo + hi) / 2 * (i + 0.33 * (2 * h01(seed, lid, course, i, 52) - 1))  # noqa: E731
    bk = bk - (q < jit(bk)) + (q >= jit(bk + 1))
    bl, br = jit(bk), jit(bk + 1)
    zr = zb - bounds[band]                      # height within the course, 0 at its bottom
    th = bounds[band + 1] - bounds[band]
    u = (q - bl) / np.maximum(1, br - bl)
    ce = np.minimum(q - bl, br - q)
    blk = hashu(seed, lid, course, bk, 53)
    joint = (ce < 0.7) | (zr < 1.0)
    topr = zr >= th - 1
    t = np.full(s.shape, 3)
    t = np.where(topr & (u < 0.75), 4, t)
    t = np.where((zr < 2.0) & ~joint, 2, t)
    t = np.where((ce < 1.7) & (q - bl < 1.7) & ~joint, np.minimum(4, t + 1), t)    # lit left end
    t = np.where((ce < 1.7) & (br - q < 1.7) & ~joint, np.maximum(2, t - 1), t)    # shaded right end
    off_t = h01(blk, 1)
    t = np.where(off_t < 0.12, t - 1, np.where(off_t > 0.93, t + 1, t))
    gr = h01(seed, lid, np.floor(q / 3).astype(np.int64), np.floor(zc).astype(np.int64), 54) < 0.07
    t = np.where(gr & ~joint & ~topr, t - 1, t)
    t = np.where(joint, np.where(zr < 1.0, 1, 0), t)
    t = np.clip(t, 0, 5)
    t = np.where(d >= Hf - 1, np.maximum(0, t - 1), t)
    ids = np.array([sibs(hp.family(n)) for n in bfams])
    si = np.minimum(2, (h01(blk, 2) * 3).astype(np.int64))
    # weathering: a block now and then of the plain stone family, sibling clusters inside the
    # blocks, lichen on the lit tops, damp in the lowest courses, grime under the coping
    stone = sibs('stone')
    fam = np.where(h01(blk, 3) < 0.22, stone[si], ids[band, si])
    cl = h01(seed, lid, np.floor(q / 2).astype(np.int64), np.floor(zc / 2).astype(np.int64), 56) < 0.16
    fam = np.where(cl & ~joint, ids[band, (si + 1) % 3], fam)
    lich = ~joint & topr & (h01(seed, lid, np.floor(q / 3).astype(np.int64), 57) < 0.12)
    fam = np.where(lich, FID['grass_cool'], fam)
    t = np.where(lich, 3, t)
    damp = ~joint & (d >= Hf - 8) & (h01(seed, lid, np.floor(q / 2).astype(np.int64), np.floor(zc / 2).astype(np.int64), 58) < 0.3)
    fam = np.where(damp, np.where(h01(blk, 4) < 0.5, stone[2], FID['earth_cool']), fam)
    t = np.where(damp & (t >= 3), t - 1, t)
    grime = ~joint & (d <= 6) & (d > 3) & (vnoise1(s, 4.0, hashu(seed, 59)) > 0.55)
    t = np.where(grime, np.maximum(1, t - 1), t)
    fam = np.where(joint, ids[band, 2], fam)
    # moss in the lowest joints
    moss = joint & (d >= Hf - 9) & (vnoise1(s, 7.0, hashu(seed, 55)) > 0.5)
    fam = np.where(moss, FID['leaf_cool'], fam)
    t = np.where(moss, 2, t)
    fr.F[yy, xx] = fam
    fr.T[yy, xx] = t
    fr.tag[yy, xx] = np.where(joint, TAG['recess'], TAG['rock'])
    fr.face = dict(yy=yy, xx=xx, s=s, lid=lid, d=d, Hf=Hf, h=h, zc=zc, u=u, rec=joint, mass=blk, k=bk,
                   crack=joint & (zr >= 1.0), ce=ce, Wm=br - bl, nx=G['nx'][py, xw])


# ---- side bands: the 5 px rock strip where a top's edge runs north-south ---------------------
def side_maps(world: World):
    """Per plan pixel: how far (1..STRIP) the nearest lower ground lies to the west and to the
    east in the same plan row, and whether the ground just south is not lower (so the edge
    there runs north-south and a side band shows, rather than a south face)."""
    if getattr(world, '_side', None) is None:
        Z = world.Z
        R, C = Z.shape
        big = np.pad(Z, ((0, 3), (STRIP, STRIP)), mode='edge')
        dw = np.zeros(Z.shape, np.int8)
        de = np.zeros(Z.shape, np.int8)
        for k in range(STRIP, 0, -1):
            dw = np.where(big[:R, STRIP - k:STRIP - k + C] < Z, k, dw)
            de = np.where(big[:R, STRIP + k:STRIP + k + C] < Z, k, de)
        south_ok = np.ones(Z.shape, bool)
        for k in (1, 2):
            south_ok &= big[k:R + k, STRIP:STRIP + C] >= Z
        world._side = (dw, de, south_ok)
    return world._side


def paint_sides(fr: Frame, P: dict, world: World):
    """Side bands (terrace.py's rule): a west-facing band lit (3 to 4), an east-facing one in
    the dark tones (1 to 2), each a column of small lumps in the rock's own ramp, closed by the
    rock's edge tone where it meets the lower ground."""
    T, seed = world.T, world.seed
    dw, de, south_ok = side_maps(world)
    K = P['kind']
    top = (K == TOP) & (P['ST'] == 0)
    py = np.clip(P['PY'], 0, world.Z.shape[0] - 1)
    xw = np.clip(fr.X, 0, world.width - 1)
    a, b = dw[py, xw], de[py, xw]
    so = south_ok[py, xw]
    west = top & (a > 0) & so & (fr.mat != MAT_WATER)
    east = top & (b > 0) & so & ~west & (fr.mat != MAT_WATER)
    for m, dist, lit in ((west, a, True), (east, b, False)):
        if not m.any():
            continue
        bounds, bfams, _ = band_table(T)
        z = P['ZH'] - 2 * dist
        band = np.clip(np.searchsorted(bounds, np.mod(z, bounds[-1]), 'right') - 1, 0, len(bfams) - 1)
        ids = np.array([sibs(hp.family(n)) for n in bfams])
        lump = np.floor((py + 3 * (h01(seed, xw, 61) > 0.5)) / 5).astype(np.int64)
        lh = hashu(seed, xw // 3, lump, 62)
        si = (h01(lh, 1) * 3).astype(np.int64)
        fam = ids[band, np.minimum(si, 2)]
        rowin = np.mod(py, 5)
        if lit:
            t = np.where(rowin == 0, 4, np.where(rowin == 4, 2, 3))
            t = np.where(dist >= STRIP, np.minimum(t, 3), t)
        else:
            t = np.where(rowin == 0, 2, 1)
            t = np.where(dist <= 1, 1, t)
        t = np.where(dist == 1, EDGE, t)
        fr.F[m] = fam[m]
        fr.T[m] = t[m]
        fr.tag[m] = TAG['side']
    fr.side_w, fr.side_e = west, east


# ---- rims: the lip of a top, the fringe hanging over the face, the overhang's shade ----------
def fringe_len(world: World, lid, s, kind: str):
    lo, hi = world.T['fringe_len']
    cw = 6.0
    ph = h01(world.seed, lid, 71) * cw
    c = np.floor((s + ph) / cw).astype(np.int64)
    u = (s + ph) / cw - c
    Lc = lo + (hi - lo + 0.999) * h01(world.seed, lid, c, 72)
    if kind == 'snow':
        # a wind-blown cornice: lobes 9 px long, 2 to 5 px deep, built out by the west wind so
        # each lobe hangs deepest towards its east end
        cw = 9.0
        ph = h01(world.seed, lid, 74) * cw
        c = np.floor((s + ph) / cw).astype(np.int64)
        u = (s + ph) / cw - c
        Lc = 2 + 3.999 * h01(world.seed, lid, c, 73)
        prof = Lc * np.sqrt(np.clip(1 - (2 * u - 1) ** 2, 0, 1)) * (0.55 + 0.45 * u) + 0.5
        return np.floor(prof), u
    prof = Lc * np.sqrt(np.clip(1 - (2 * u - 1) ** 2, 0, 1)) + 0.35
    return np.floor(prof), u


def paint_rims(fr: Frame, P: dict, world: World):
    T, seed = world.T, world.seed
    K = P['kind']
    face = (K == FACEK) & (P['ST'] == 0)
    top = (K == TOP)
    # the lip: the last row of a top over a face is lit, with blades standing up along it
    lip = top & nb(face, 1, 0) & (fr.tag != TAG['side'])
    g = lip & (fr.mat == MAT_GROUND)
    fr.T[g] = 4
    above = nb(g, 1, 0) & top & (fr.mat == MAT_GROUND) & (fr.tag != TAG['side'])
    bl = above & (h01(hashu(seed, 81), fr.X // 2, fr.Y) < 0.45)
    fr.T[bl] = 4
    sn = lip & (fr.mat == MAT_SNOW)
    fr.T[sn] = 5
    if not hasattr(fr, 'face'):
        return
    f = fr.face
    yy, xx = f['yy'], f['xx']
    # what the top above each face column is made of (the rim pixel's own material)
    py = P['PY'][yy, xx]
    xw = np.clip(fr.X[yy, xx], 0, world.width - 1)
    mat = top_material(world, py, xw, f['h'])
    kind = T['fringe']
    L, u = fringe_len(world, f['lid'], f['s'], 'grass')
    Ls, _ = fringe_len(world, f['lid'], f['s'], 'snow')
    L = np.where(mat == MAT_SNOW, Ls, L)
    L = np.where(mat == MAT_WATER, 0, L)
    L = np.where(mat == MAT_PATH, np.minimum(L, 2), L)
    d = f['d']
    on = d <= L
    if kind == 'coping':
        on = d <= 3
    gf = sibs(T['top']) if kind != 'grass' else sibs('grass')
    fam = np.where(mat == MAT_SNOW, FID['snow'], np.where(mat == MAT_PATH, FID['earth'], gf[(h01(seed, f['lid'], np.floor(f['s'] / 6).astype(np.int64), 74) * 3).astype(np.int64) % 3]))
    if kind == 'crumble':
        fam = np.where(mat == MAT_SNOW, FID['snow'], sibs(T['top'])[0])
    if kind == 'coping':
        ids = sibs(T['rock'])
        jt = np.mod(f['s'] + 5 * h01(seed, f['lid'], 75), 13.0) < 1.0
        tc = np.where(d == 1, 4, np.where(d == 2, 3, 1))
        tc = np.where(jt & (d > 1), 1, tc)
        t = tc
        fam = ids[(h01(seed, f['lid'], np.floor((f['s'] + 5) / 13).astype(np.int64), 76) * 3).astype(np.int64) % 3]
    else:
        last = d >= L
        t = np.where(last, 2, 3)
        t = np.where((d == 1) & (u < 0.45), 4, t)
        t = np.where(last & (L >= 3), 1, t)
        t = np.where((mat == MAT_SNOW), np.where(d == 1, 4, np.where(last, 2, 3)), t)
    fam = np.broadcast_to(fam, on.shape)
    fr.F[yy[on], xx[on]] = fam[on]
    fr.T[yy[on], xx[on]] = t[on]
    fr.tag[yy[on], xx[on]] = TAG['fringe']
    # the overhang's shade on the rock under it: two tones down, then one, a row deeper east
    Lr = np.where(kind == 'coping', 3, L)
    under = ~on & (d - Lr <= 1 + (u > 0.6)) & (mat != MAT_WATER)
    r1 = under & (d - Lr <= 1)
    idx = (yy[r1], xx[r1])
    fr.T[idx] = np.maximum(0, np.where(fr.T[idx] == EDGE, EDGE, fr.T[idx] - 2))
    r2 = under & ~r1
    idx = (yy[r2], xx[r2])
    fr.T[idx] = np.where(fr.T[idx] == EDGE, EDGE, np.maximum(0, fr.T[idx] - 1))
    fr.fringeL = L
    fr.rim_mat = mat


# ---- cast shadows on the lower ground ------------------------------------------------------
def paint_shadows(fr: Frame, P: dict, world: World, steps: int = 2):
    """A face throws its shadow down onto the ground at its foot (two tones down to a wavy
    hard edge 2 to 4 px out, then one tone down to SHADOW px); an east-facing side band throws
    one east. On the ground's own ramp (house-style 6)."""
    K = P['kind']
    ground = (K == TOP) & np.isin(fr.tag, (TAG['ground'], TAG['path'], TAG['snow']))
    caster = (K == FACEK) | (fr.tag == TAG['side'])
    dist = np.zeros(fr.shape, np.int32)
    for k in range(SHADOW, 0, -1):
        dist = np.where(nb(caster, -k, 0), k, dist)
    w1 = 2 + np.floor(3 * vnoise1(fr.X, 5.0, hashu(world.seed, 91))).astype(np.int32)
    w2 = SHADOW - 1 - np.floor(3 * vnoise1(fr.X, 7.0, hashu(world.seed, 92))).astype(np.int32)
    s2 = ground & (dist > 0) & (dist <= w1)
    s1 = ground & (dist > w1) & (dist <= w2)
    east = getattr(fr, 'side_e', np.zeros(fr.shape, bool))
    de = np.zeros(fr.shape, np.int32)
    for k in range(SHADOW, 0, -1):
        de = np.where(nb(east, 0, -k), k, de)
    s2 |= ground & (de > 0) & (de <= 3)
    s1 |= ground & (de > 3) & (de <= SHADOW - 2)
    fr.T[s2] = np.maximum(0, fr.T[s2] - steps)
    fr.T[s1 & ~s2] = np.maximum(0, fr.T[s1 & ~s2] - 1)
    # contact line: the first ground row under a face
    c = ground & nb(K == FACEK, -1, 0)
    fr.T[c] = np.minimum(fr.T[c], 1)


# ---- no speckle -------------------------------------------------------------------------------
def despeckle(fr: Frame, passes: int = 2, keep=(TAG['figure'],)):
    """A pixel unlike all four neighbours (and not a deliberate glint, tone 5) takes the colour
    most of its neighbours share (house-style 4: lone pixels at most 6 %)."""
    for _ in range(passes):
        key = fr.F.astype(np.int64) * 8 + fr.T
        up, dn, lf, rt = nb(key, -1, 0), nb(key, 1, 0), nb(key, 0, -1), nb(key, 0, 1)
        lone = (key != up) & (key != dn) & (key != lf) & (key != rt) & (fr.T != 5) & ~np.isin(fr.tag, keep)
        best = up.copy()
        for a, b in ((up, dn), (up, lf), (up, rt), (dn, lf), (dn, rt), (lf, rt)):
            pass
        cand = np.where(dn == lf, dn, np.where(dn == rt, dn, np.where(lf == rt, lf, up)))
        pair_up = (up == dn) | (up == lf) | (up == rt)
        best = np.where(pair_up, up, cand)
        fr.F[lone] = (best[lone] // 8).astype(np.int32)
        fr.T[lone] = (best[lone] % 8).astype(np.int32)


# ---- render ------------------------------------------------------------------------------------
MARGIN = 48      # every neighbourhood rule reaches less than this, so windows agree


class Render:
    def __init__(self, fr: Frame, crop):
        self.fr, self.crop = fr, crop

    def image(self) -> Image.Image:
        return self.fr.image(self.crop)

    def arrays(self):
        x0, y0, x1, y1 = self.crop
        return self.fr.F[y0:y1, x0:x1], self.fr.T[y0:y1, x0:x1], self.fr.tag[y0:y1, x0:x1]


def render(world: World, box=None, dress: bool = True) -> Render:
    """Render a window of the world (screen box x0, y0, x1, y1; the whole world by default).
    The window is painted with a margin and cropped, and every decision is a function of world
    coordinates, so a tile is exactly the matching crop of the whole."""
    W, H = world.width, world.height
    x0, y0, x1, y1 = box or (0, 0, W, H)
    fx0, fy0, fx1, fy1 = max(0, x0 - MARGIN), max(0, y0 - MARGIN), min(W, x1 + MARGIN), min(H, y1 + MARGIN)
    fr = Frame(world, fx0, fy0, fx1, fy1)
    P = project(world, fx0, fy0, fx1, fy1)
    fr.P = P
    paint_ground(fr, P, world)
    paint_faces(fr, P, world)
    paint_stairs(fr, world)
    paint_sides(fr, P, world)
    paint_rims(fr, P, world)
    paint_snow(fr, world)
    paint_water(fr, world)
    snow_extras(fr, world)
    dress_ground(fr, world)
    paint_shadows(fr, P, world)
    if dress:
        dress_faces(fr, world)
        dress_feet(fr, world)
    despeckle(fr)
    return Render(fr, (x0 - fx0, y0 - fy0, x1 - fx0, y1 - fy0))


# ---- building a height field --------------------------------------------------------------------
def curve(pts, n: int) -> np.ndarray:
    """Catmull-Rom through (x, y) control points, sampled at every column 0..n-1."""
    pts = sorted(pts)
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    x = np.arange(n, dtype=float)
    i = np.clip(np.searchsorted(xs, x, side='right') - 1, 0, len(xs) - 2)
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    p0, p1, p2, p3 = ys[np.maximum(i - 1, 0)], ys[i], ys[i + 1], ys[np.minimum(i + 2, len(ys) - 1)]
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def from_rims(width: int, height: int, rims, top: int | None = None) -> tuple:
    """A plan height field from rims drawn as screen curves: `rims` is a list of (z, lip) where
    lip[x] is the screen row of that tier's lip (np.nan where the tier is absent). Returns
    (Z, top) for World(Z, top=top)."""
    top = top if top is not None else max(z for z, _ in rims)
    Z = np.zeros((height + top, width), np.int32)
    py = np.arange(height + top)[:, None]
    for z, lip in sorted(rims, key=lambda r: r[0]):
        lip = np.asarray(lip, float)
        ok = ~np.isnan(lip)
        m = (py <= np.where(ok, np.round(lip), -10 ** 6)[None, :] + top + z)
        Z = np.where(m, np.maximum(Z, z), Z)
    return Z, top


def walk_tiers(world: World, cell: int = GRID):
    """The screen tier map terrace.build() takes (one value per 8 px cell, in tiers), from this
    world's plan field: so a zone that paints its cliffs with this core walks on the same map."""
    Z = world.Z[world.top:, :]
    R, C = Z.shape
    cells = Z[: R - R % cell, : C - C % cell].reshape(R // cell, cell, C // cell, cell)
    plan = np.round(np.median(cells, axis=(1, 3)) / world.T['face']).astype(int)
    return from_plan(plan, world.T['face'])


# ---- stamps: small hand-drawn shapes, placed on world candidates -------------------------------
def stamp(rows):
    """Rows of characters: '.' empty, '0' to '5' a tone, 'e' the family's edge tone."""
    return [(y, x, EDGE if ch == 'e' else int(ch)) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != '.']


TUFTS = [stamp(['.4..4', '34.43', '.233.', '..2..']), stamp(['4.4', '343', '22.']),
         stamp(['..4.', '.44.', '4332', '.22.']), stamp(['4..', '34.', '.32', '..2']),
         stamp(['.4', '43', '32']), stamp(['5.4..', '44.4.', '.343.', '.222.'])]
CLOVER = [stamp(['.44.', '4433', '.32.']), stamp(['44', '32']), stamp(['.44', '443', '32.'])]
FLOWER = [stamp(['55', '43']), stamp(['.5.', '554', '.3.']), stamp(['55.', '453', '.3.'])]
MOUND = [stamp(['..4444..', '.444433.', '43333322', '32222221', '.111111.']),
         stamp(['.4443.', '443332', '322221', '.1111.'])]
PEBBLE = [stamp(['45', '32']), stamp(['.44.', '4332', '.22.']), stamp(['44', '43', '22']), stamp(['54', '31'])]


def candidates(fr: Frame, cell: int, seed, p, inset: int = 12):
    """World-anchored candidate points: one per `cell` px square of the world screen, jittered,
    kept with probability p (a number, or an array over the frame read at the point). Only
    points at least `inset` px inside the frame are returned (the margin covers the rest)."""
    gx0, gy0 = (fr.x0 + inset) // cell, (fr.y0 + inset) // cell
    gx1, gy1 = (fr.x1 - inset) // cell + 1, (fr.y1 - inset) // cell + 1
    if gx1 <= gx0 or gy1 <= gy0:
        return np.zeros((0,), np.int64), np.zeros((0,), np.int64), np.zeros((0,), np.uint32)
    gy, gx = np.mgrid[gy0:gy1, gx0:gx1]
    gx, gy = gx.ravel(), gy.ravel()
    hh = hashu(seed, gx, gy)
    x = gx * cell + (hashu(hh, 1) % np.uint32(cell)).astype(np.int64)
    y = gy * cell + (hashu(hh, 2) % np.uint32(cell)).astype(np.int64)
    ok = (x >= fr.x0 + inset) & (x < fr.x1 - inset) & (y >= fr.y0 + inset) & (y < fr.y1 - inset)
    x, y, hh = x[ok], y[ok], hh[ok]
    pv = p[y - fr.y0, x - fr.x0] if isinstance(p, np.ndarray) else p
    keep = h01(hh, 3) < pv
    return x[keep], y[keep], hh[keep]


def put_stamp(fr: Frame, st, x, y, fam, allow=None, tag=None, anchor=(0, 0)):
    """Paint a stamp with its top-left at world (x, y) - anchor, in family `fam` (an id or a
    callable (tone) -> id), only where `allow` (a frame mask) is true."""
    for (dy, dx, t) in st:
        X, Y = x + dx - anchor[0] - fr.x0, y + dy - anchor[1] - fr.y0
        if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1] and (allow is None or allow[Y, X]):
            fr.F[Y, X] = fam(t) if callable(fam) else fam
            fr.T[Y, X] = t
            if tag is not None:
                fr.tag[Y, X] = tag


def near(mask: np.ndarray, r: int) -> np.ndarray:
    """The mask grown by r px (4-neighbour steps: a diamond)."""
    out = mask.copy()
    for _ in range(r):
        out = out | nb(out, 1, 0) | nb(out, -1, 0) | nb(out, 0, 1) | nb(out, 0, -1)
    return out


def dress_ground(fr: Frame, world: World):
    """Tufts and long grass gathered at edges (rims, feet, paths, water), clover and the odd
    grass mound in the open, flowers in small clusters: the house ground recipe's dressing."""
    T, seed = world.T, world.seed
    if T['top'] != 'grass':
        return dress_dry(fr, world)
    g = (fr.tag == TAG['ground']) & np.isin(fr.F, sibs('grass'))
    edge = near(~g & (fr.P['kind'] > 0), 5) & g
    p = np.where(edge, 0.75, 0.6)
    gid = sibs('grass')
    for x, y, hh in zip(*candidates(fr, 6, hashu(seed, 101), p)):
        st = TUFTS[int(hh % np.uint32(len(TUFTS)))]
        f = int(gid[int(hashu(hh, 4) % np.uint32(3))])
        put_stamp(fr, st, x, y, f, allow=g, anchor=(2, 3))
    lid = sibs('leaf')
    for x, y, hh in zip(*candidates(fr, 10, hashu(seed, 102), np.where(edge, 0.05, 0.16))):
        put_stamp(fr, CLOVER[int(hh % np.uint32(3))], x, y, int(lid[int(hashu(hh, 4) % np.uint32(3))]), allow=g)
    for x, y, hh in zip(*candidates(fr, 28, hashu(seed, 103), 0.22)):
        put_stamp(fr, MOUND[int(hh % np.uint32(2))], x, y, int(gid[2]), allow=g, anchor=(3, 2))
    # flowers in patches: one kind to a clump, eight to fourteen heads round a centre
    fl = [FID['plaster'], FID['brass'], FID['dusk'], FID['berry'], FID['sky']]
    for x, y, hh in zip(*candidates(fr, 44, hashu(seed, 104), min(0.8, T['flowers'] * 10))):
        f = fl[int(hashu(hh, 5) % np.uint32(len(fl)))]
        for j in range(8 + int(hashu(hh, 6) % np.uint32(7))):
            ox = int(round((h01(hh, 7, j) * 2 - 1) * 6))
            oy = int(round((h01(hh, 8, j) * 2 - 1) * 4))
            if ox * ox / 36 + oy * oy / 16 > 1:
                continue
            put_stamp(fr, FLOWER[int(hashu(hh, 9, j) % np.uint32(3))], x + ox, y + oy, f, allow=g)


def dress_dry(fr: Frame, world: World):
    """Dry ground (sand, desert): pebbles and dry tufts in the top's own siblings, gathered at
    the feet; paving (stone): setts are drawn by paint_paving, so only weeds in its joints."""
    T, seed = world.T, world.seed
    g = fr.tag == TAG['ground']
    edge = near(~g & (fr.P['kind'] > 0), 6) & g
    ids = sibs(T['top'])
    if T['top'] == 'stone':
        return
    for x, y, hh in zip(*candidates(fr, 7, hashu(seed, 111), np.where(edge, 0.45, 0.12))):
        put_stamp(fr, PEBBLE[int(hh % np.uint32(4))], x, y, int(ids[int(hashu(hh, 4) % np.uint32(3))]), allow=g)
    for x, y, hh in zip(*candidates(fr, 11, hashu(seed, 112), np.where(edge, 0.3, 0.08))):
        put_stamp(fr, TUFTS[int(hh % np.uint32(len(TUFTS)))], x, y, FID['bleached_cool'] if T['top'] == 'sand' else FID['grass_cool'],
                  allow=g, anchor=(2, 3))


# ---- snow ---------------------------------------------------------------------------------------
def paint_snow(fr: Frame, world: World):
    """House snow, no grit: a calm plane (3) laid in large drifts. Each drift is a tone up on
    its windward west and north, its crest lit, and soft blue-violet shade (the cool sibling,
    tone 2) on its east and south sides and in its lee. Where the snow ends on lower ground a
    crisp edge: a lit lip (5) over the snow's shaded south face (2, then 1), the ground below
    two tones down. At a rim the fringe draws one wind-blown cornice (no doubled line)."""
    seed = world.seed
    K = fr.P['kind']
    sn = (K == TOP) & (fr.mat == MAT_SNOW) & (fr.P['ST'] == 0)
    if not sn.any():
        return
    X, Y = fr.X, fr.Y
    sf = sibs('snow')
    fr.F[sn] = sf[0]
    fr.T[sn] = 3
    fr.tag[sn] = TAG['snow']
    n = fbm2(X, Y * 1.7, 38.0, hashu(seed, 123), 2)
    D = sn & (n > 0.56)
    fr.T[D] = 4
    crest = D & (~nb(D, -1, 0) | ~nb(D, 0, -1)) & (n > 0.6)
    fr.T[crest] = 5
    shade = D & (~nb(D, 0, 1) | ~nb(D, 0, 2) | ~nb(D, 0, 3) | ~nb(D, 1, 0) | ~nb(D, 2, 0))
    fr.F[shade] = sf[2]
    fr.T[shade] = 2
    lee = sn & ~D & (nb(D, 0, -1) | nb(D, 0, -2) | nb(D, -1, 0) | nb(D, -1, -1))
    fr.F[lee] = sf[2]
    fr.T[lee] = 2
    calm = sn & ~D & ~lee & (vnoise2(X, Y * 1.5, 30.0, hashu(seed, 124)) < 0.3)
    fr.F[calm] = sf[2]
    ground_below = nb((K == TOP) & ~sn & (fr.tag != TAG['side']), 1, 0)
    s1 = sn & ground_below
    s2 = sn & nb(s1, 1, 0) & ~s1
    s3 = sn & nb(s2, 1, 0) & ~s2 & ~s1
    fr.F[s1 | s2] = sf[2]
    fr.T[s1] = 1
    fr.T[s2] = 2
    fr.T[s3] = 5
    west = sn & ~nb(sn, 0, -1) & ~s1 & ~s2
    fr.T[west] = np.maximum(fr.T[west], 4)
    east = sn & ~nb(sn, 0, 1) & ~s1 & ~s2 & ~s3
    fr.F[east] = sf[2]
    fr.T[east] = 2
    below = (K == TOP) & ~sn & (nb(s1, -1, 0) | nb(s1, -2, 0)) & (fr.tag == TAG['ground'])
    fr.T[below] = np.maximum(0, fr.T[below] - 2)


def snow_extras(fr: Frame, world: World):
    """Half-buried rocks in the snow (a cap on top, a drift piled on the windward west, blue
    shade on the east and at the foot) and drifts against the foot of a face whose top is
    snowy."""
    seed = world.seed
    sn = fr.tag == TAG['snow']
    for x, y, hh in zip(*candidates(fr, 30, hashu(seed, 131), np.where(sn & ~near(~sn, 7), 0.5, 0.0))):
        _snow_rock(fr, x, y, hh, sn, world.T['rock'])
    # drifts at the foot of a face with snow on its top
    if not hasattr(fr, 'face') or not hasattr(fr, 'rim_mat'):
        return
    f = fr.face
    foot = np.zeros(fr.shape, bool)
    sel = (f['d'] >= f['Hf']) & (fr.rim_mat == MAT_SNOW)
    foot[f['yy'][sel], f['xx'][sel]] = True
    if not foot.any():
        return
    ground = (fr.P['kind'] == TOP) & np.isin(fr.tag, (TAG['ground'], TAG['path']))
    # a drift is a mound banked against the foot, 16 to 28 px long and up to 6 to 11 deep, one
    # in two sites along the foot
    site = fr.X // 44
    hs = hashu(seed, site, 132)
    wv = 16 + 12 * h01(hs, 1)
    dx = fr.X + 0.5 - (site * 44 + 22 + 10 * (h01(hs, 2) - 0.5))
    shape = np.sqrt(np.clip(1 - (2 * dx / wv) ** 2, 0, 1))
    L = np.where(h01(hs, 3) < 0.5, np.floor((6 + 5 * h01(hs, 4)) * shape * (0.85 + 0.15 * vnoise1(fr.X, 3.0, hashu(seed, 133))) + 0.3), 0)
    dist = np.zeros(fr.shape, np.int32)
    for k in range(14, 0, -1):
        dist = np.where(nb(foot, -k, 0), k, dist)
    drift = ground & (dist > 0) & (dist <= L)
    sf = sibs('snow')
    fr.F[drift] = sf[0]
    t = np.where(dist <= np.maximum(2, L * 0.45), 4, 3)
    t = np.where((dist == 2) & (dx < 0) & (L >= 5), 5, t)
    face_s = (dist > L - 2) & (L >= 3)
    t = np.where(face_s, np.where(dist == L, 1, 2), t)
    east = dx > wv * 0.25
    t = np.where(east & ~face_s & (t >= 3), 2, t)
    fr.F[drift & (face_s | (east & (t <= 2)))] = sf[2]
    fr.T[drift] = t[drift]
    fr.tag[drift] = TAG['snow']
    sh = ground & ~drift & (nb(drift, -1, 0) | nb(drift, -2, 0))
    fr.T[sh] = np.maximum(0, fr.T[sh] - 2)


SNOW_ROCKS = [(3.6, 1.3, -0.45), (7.5, 0.45, 0.0), (2.8, 0.85, 0.15), (5.0, 0.95, 0.45)]   # (rx, ry / rx, lean)


def _snow_rock(fr: Frame, x, y, hh, sn, rock):
    """A rock poking out of the snow: an irregular lump lit on its west, its foot lost in the
    snow (no outline there, a blue shade line along it), a snow cap on its lit top, a drift
    piled on its windward west and blue shade on its lee."""
    # four rocks: a tall one leaning west, a long flat slab, a small round one, a block
    # leaning east; each scaled a little
    rx0, ratio, lean = SNOW_ROCKS[int(hashu(hh, 9) % np.uint32(len(SNOW_ROCKS)))]
    rx = rx0 * (0.85 + 0.3 * h01(hh, 1))
    ry = rx * ratio
    bx = _box(fr, int(x - rx - 7), int(y - ry - 4), int(x + rx + 8), int(y + ry + 4))
    if bx is None:
        return
    X, Y = fr.X[bx], fr.Y[bx]
    al = sn[bx]
    xs = X + 0.5 - x - lean * (y - (Y + 0.5))
    q = (xs / rx) ** 2 + ((Y + 0.5 - y) / ry) ** 2 + 0.3 * (vnoise2(X, Y, 2.0, hashu(hh, 3)) - 0.5)
    base = y + ry * (0.1 + 0.35 * vnoise1(X, 2.5, hashu(hh, 4)))
    m = (q <= 1.0) & (Y + 0.5 < base) & al
    if not m.any():
        return
    I = -xs / rx * 0.7 - (Y + 0.5 - y) / ry * 0.6
    t = np.where(I > 0.35, 3, np.where(I > -0.25, 2, 1))
    cap = m & (~nb(m, -1, 0) | ~nb(m, -2, 0)) & (I > -0.1 + 0.3 * h01(hh, 6))
    ids = sibs(rock)
    F, T, G = fr.F[bx], fr.T[bx], fr.tag[bx]
    F[m] = ids[int(hashu(hh, 5) % np.uint32(3))]
    T[m] = t[m]
    G[m] = TAG['scree']
    F[cap] = FID['snow']
    T[cap] = np.where(X[cap] < x + rx * 0.2, 5, 4)
    G[cap] = TAG['snow']
    ring = ~m & al & (nb(m, 0, 1) | nb(m, 0, -1) | nb(m, 1, 0)) & (Y + 0.5 < base - 0.5)
    litb = ring & (nb(m, 0, 1) | nb(m, 1, 0)) & (X + 0.5 < x)
    F[ring] = ids[0]
    T[ring] = np.where(litb[ring], 1, EDGE)
    G[ring] = TAG['scree']
    foot = ~m & al & nb(m, -1, 0) & ~ring
    T[foot] = 2
    drift = al & ~m & ~ring & (q > 0.9) & (q < 2.0) & (X + 0.5 < x - rx * 0.3)
    T[drift] = 4
    lee = al & ~m & ~ring & ~foot & (q > 0.9) & (q < 1.9) & (X + 0.5 > x + rx * 0.25) & (Y + 0.5 > y - ry * 0.2)
    T[lee] = 2


# ---- stairs ---------------------------------------------------------------------------------------
def paint_stairs(fr: Frame, world: World):
    """Steps cut from the crag itself, not laid like boards: each step is a row of stones 4 to
    10 px long in the rock's own ramp (one sibling a stone), each with a lit top-left and a
    shaded lower-right; the nosing is irregular (a stone chipped back, another standing a row
    proud), the centre of the flight is worn darker, moss gathers at the sides, the risers are
    rock in shade with a dark row under each nosing, and rock cheeks overlap both sides."""
    P = fr.P
    st = P['ST'] == 1
    if not st.any():
        return
    seed = world.seed
    ids = sibs(world.T['rock'])
    K = P['kind']
    flag = world.flag
    py = np.clip(P['PY'], 0, world.Z.shape[0] - 1)
    xw = np.clip(fr.X, 0, world.width - 1)
    zl = P['ZH']
    X, Y = fr.X, fr.Y
    stp = hashu(seed, zl, py // 16, 141)
    # distance (1 up) to the stair's west and east sides in plan
    if getattr(world, '_stair_d', None) is None:
        D = 64
        big = np.pad(flag, ((0, 0), (D, D)))
        wl = np.full(flag.shape, D, np.int16)
        wr = np.full(flag.shape, D, np.int16)
        for k in range(D, 0, -1):
            wl = np.where(big[:, D - k:D - k + flag.shape[1]] == 0, k, wl)
            wr = np.where(big[:, D + k:D + k + flag.shape[1]] == 0, k, wr)
        world._stair_d = (wl, wr)
    wl, wr = world._stair_d
    a, b = wl[py, xw].astype(np.int64), wr[py, xw].astype(np.int64)
    tread = st & (K == TOP)
    riser = st & (K == FACEK)
    nose = tread & nb(riser, 1, 0)
    under = riser & nb(nose, -1, 0)
    # stones along the step, their joints wandering
    Ls = 6 + (hashu(stp, 8) % np.uint32(4)).astype(np.int64)
    off = (hashu(stp, 2) % np.uint32(9)).astype(np.int64)
    q = X + off
    k0 = q // Ls
    edge = lambda k: k * Ls + np.round(2.6 * (h01(stp, k, 3) - 0.5)).astype(np.int64)  # noqa: E731
    kk = k0 - (q < edge(k0)) + (q >= edge(k0 + 1))
    lo, hi = edge(kk), edge(kk + 1)
    sh = hashu(stp, kk, 4)
    first = q == lo
    second = q == lo + 1
    last = q == hi - 1
    fam = ids[(hashu(sh, 1) % np.uint32(3)).astype(np.int64)]
    # each stone is a block: its top is the tread, its front the riser, a joint either side
    t = np.where(tread, 4, 2)
    t = np.where(tread & last, 3, t)
    t = np.where(tread & (h01(sh, 2) < 0.25), t - 1, t)
    # the nosing: lit, with a glint at a stone's left; one stone chipped back, another proud
    chipped = h01(sh, 5) < 0.22
    proud = (h01(sh, 6) > 0.8) & ~chipped
    t = np.where(nose, np.where(second, 5, 4), t)
    t = np.where(nose & chipped, 2, t)
    t = np.where(nb(nose & chipped, 1, 0) & tread, 4, t)
    t = np.where(riser & ~under, np.where(h01(sh, 7) < 0.5, 2, 1), t)
    t = np.where(riser & second & ~under, 3, t)
    t = np.where(riser & last & ~under, 1, t)
    t = np.where(under, np.where(proud, 3, 0), t)
    t = np.where(first, np.where(tread, 1, 0), t)
    # the worn centre of the flight, a tone darker on the treads
    width = a + b
    u = a / np.maximum(1, width)
    worn = tread & ~nose & (np.abs(u - 0.5) < 0.16 + 0.06 * vnoise1(Y, 4.0, hashu(seed, 143)))
    t = np.where(worn, np.maximum(2, t - 1), t)
    # moss at the sides, where feet do not go
    moss = (tread | riser) & (np.minimum(a, b) <= 6) & (h01(hashu(seed, 144), X // 2, Y // 2) < 0.55 - 0.07 * np.minimum(a, b))
    fam = np.where(moss, sibs('leaf')[(hashu(seed, X // 2, Y // 2, 145) % np.uint32(3)).astype(np.int64)], fam)
    t = np.where(moss, np.where(tread, 3, 2), t)
    t = np.clip(t, 0, 5)
    fr.F[st] = fam[st]
    fr.T[st] = t[st]
    fr.tag[st] = TAG['stair']
    # cheek stones overlap the stair's sides, so its edges are ragged and it sits in the rock
    allow = st | np.isin(fr.tag, (TAG['side'], TAG['rock'], TAG['recess']))
    for k, sr in enumerate(world.stairs):
        n = (sr.z_high - sr.z_low) // sr.riser
        y_top = sr.py - n * sr.tread - world.top - sr.z_high
        y_bot = sr.py - world.top - sr.z_low
        for side, xe in ((0, sr.x0), (1, sr.x1)):
            yy = y_top + 2
            j = 0
            while yy < y_bot:
                hh = hashu(seed, k, side, j, 142)
                rx = 3.0 + 2.0 * h01(hh, 1)
                ry = 3.0 + 1.8 * h01(hh, 2)
                cx = xe + (-1.5 if side == 0 else 0.5) + (h01(hh, 3) - 0.5) * 2
                boulder(fr, cx, yy + ry, rx, ry, hh, allow, world.T['rock'], moss=0.35, tag=TAG['side'])
                yy += int(2 * ry + 1 + 2 * h01(hh, 4))
                j += 1


# ---- water: streams on the tops, falls down the faces, plunge pools at the feet -----------------
def falls(world: World) -> list:
    """Every fall in the world, found by rule: where a stream (the water mask) reaches a rim,
    it pours over the whole face; where the table has a spring line, a fall leaves the face at
    that height in each bay the line crosses (a concave bend of the rim), when the bay's hash
    allows. Global and deterministic, so every window sees the same falls."""
    if getattr(world, '_falls', None) is not None:
        return world._falls
    T, seed, Z = world.T, world.seed, world.Z
    out = []
    if world.water is not None:
        R, C = Z.shape
        rim = (Z[:-1] > Z[1:]) & world.water[:-1] & ~world.flag[:-1].astype(bool)
        for r in range(R - 1):
            xs = np.nonzero(rim[r])[0]
            if not len(xs):
                continue
            runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
            for run in runs:
                c0, c1 = int(run[0]), int(run[-1]) + 1
                h, h2 = int(Z[r, c0]), int(Z[r + 1, c0])
                prev = [f for f in out if f['kind'] == 'stream' and abs(f['py'] - r) <= 3 and f['x0'] <= c1 + 1 and c0 <= f['x1'] + 1]
                if prev:      # one stream crossing a sloping rim: one fall, one pool
                    f = prev[0]
                    f['x0'], f['x1'] = min(f['x0'], c0), max(f['x1'], c1)
                    f.setdefault('rows', [f['py']]).append(r)
                    continue
                out.append(dict(x0=c0, x1=c1, py=r, h=h, h2=h2, ztop=h, kind='stream',
                                id=int(hashu(seed, r, c0, 151))))
    sz = T.get('spring')
    if sz is not None and T.get('falls', 0) > 0:
        G = world.geometry()
        for L, lp in enumerate(G['loops']):
            for (a, r, c) in lp.get('bays', []):
                if not (0 <= r < Z.shape[0] - 1 and 0 <= c < Z.shape[1]):
                    continue
                h, h2 = int(Z[r, c]), int(Z[r + 1, c])
                if not (h2 < sz < h) or world.flag[r, c] or h - h2 < 48:
                    continue
                if (Z[r + 1:r + 24, c] != h2).any():
                    continue
                if any(abs(f['x0'] - c) < 24 and f['py'] == r for f in out):
                    continue
                if h01(seed, L, int(a), 152) >= T['falls']:
                    continue
                w = 3
                out.append(dict(x0=c - w // 2, x1=c - w // 2 + w, py=r, h=h, h2=h2, ztop=sz, kind='spring',
                                id=int(hashu(seed, L, int(a), 154))))
    for f in out:          # the kit's rule: a fall widens with its drop
        w = max(f['x1'] - f['x0'], fall_width(f['ztop'] - f['h2']))
        c = (f['x0'] + f['x1']) / 2
        f['x0'], f['x1'] = int(round(c - w / 2)), int(round(c - w / 2)) + w
    world._falls = out
    return out


def fall_width(drop: int) -> int:
    """How wide a fall is for its drop: water speeds up and spreads as it falls, so a fall
    is 2 px plus one for every 9 px of drop, 3 to 12 px (a 32 px drop 6, a 64 px drop 9)."""
    return int(min(12, max(3, round(2 + drop / 9.0))))


def paint_water(fr: Frame, world: World):
    seed = world.seed
    P = fr.P
    K = P['kind']
    X, Y = fr.X, fr.Y
    wf = sibs('water')
    # streams and ponds on the tops
    wt = (K == TOP) & (fr.mat == MAT_WATER)
    if wt.any():
        up_bank = wt & ~nb(wt, -1, 0)
        lo_bank = wt & ~nb(wt, 1, 0)
        side = wt & (~nb(wt, 0, -1) | ~nb(wt, 0, 1))
        t = np.full(fr.shape, 2)
        t = np.where(side, 3, t)
        t = np.where(lo_bank, 3, t)
        t = np.where(up_bank, 1, t)
        st = wt & ~up_bank & ~side & (h01(hashu(seed, 161), X, Y // 4) < 0.18) & (np.mod(Y, 4) < 3)
        t = np.where(st, 4, t)
        sh = wt & nb(st, 0, -1) & ~st & ~up_bank
        t = np.where(sh, 1, t)
        fr.F[wt] = wf[np.where(vnoise2(X, Y, 7.0, hashu(seed, 162)) > 0.6, 2, 0)[wt]]
        # broad water (a lake, the sea): depth in bands by the distance from the shore, the
        # shore's foam line, swells as long lit streaks over their shadow lying with the waves
        sd = np.zeros(fr.shape, np.int32)
        shore = ~wt
        for k in range(1, 15):
            shore = near(shore, 1)
            sd = np.where(wt & ~shore & (sd == 0), 0, sd)
            sd = np.where(wt & shore & (sd == 0), k, sd)
        sd = np.where(wt & (sd == 0), 15, sd)
        broad = wt & near(sd >= 5, 5)
        tb = np.where(sd <= 1, 5, np.where(sd <= 2, 4, np.where(sd <= 5, 3, np.where(sd <= 10, 2, 1))))
        foam = broad & (sd <= 1 + (vnoise1(X, 5.0, hashu(seed, 165)) > 0.55))
        wave = broad & (sd > 3) & (h01(hashu(seed, 166), X // 5, Y // 2) < 0.16) & (np.mod(X, 5) < 4) & (np.mod(Y, 2) == 0)
        tb = np.where(wave, np.minimum(4, tb + 1), tb)
        tb = np.where(broad & nb(wave, -1, 0) & ~wave & (sd > 3), np.maximum(1, tb - 1), tb)
        t = np.where(broad, tb, t)
        fr.F[foam] = FID['snow']
        fr.T[wt] = t[wt]
        fr.tag[wt] = TAG['water']
        bank = (K == TOP) & ~wt & near(wt & ~broad, 1) & ~near(broad, 2) & np.isin(fr.tag, (TAG['ground'], TAG['snow'], TAG['path']))
        ef = sibs('earth')
        fr.F[bank & (fr.tag != TAG['snow'])] = ef[2]
        fr.T[bank] = np.where(nb(wt, 1, 0)[bank] | nb(wt, 0, 1)[bank], 2, 3)
        moss = (K == TOP) & ~wt & ~bank & near(bank, 1) & (fr.tag == TAG['ground']) & (h01(hashu(seed, 163), X // 2, Y // 2) < 0.4) \
            & (fr.F == fr.F) & np.isin(fr.F, sibs('grass'))
        fr.F[moss] = FID['leaf']
        fr.T[moss] = np.where(h01(hashu(seed, 164), X, Y)[moss] < 0.5, 3, 2)
    # falls
    for f in falls(world):
        _fall(fr, world, f)


def _fall(fr: Frame, world: World, f: dict):
    P = fr.P
    K = P['kind']
    rim_row = f['py'] - world.top - f['h']
    top_row = rim_row + (f['h'] - f['ztop']) + 1
    foot_row = rim_row + (f['h'] - f['h2'])
    if foot_row < fr.y0 - 4 or top_row > fr.y1 + 20 or f['x1'] < fr.x0 - 20 or f['x0'] > fr.x1 + 20:
        f['_foot'] = foot_row
        return
    wf = sibs('water')
    X, Y = fr.X, fr.Y
    w0 = f['x1'] - f['x0']
    # the course swells and narrows down the face
    dl = np.round(1.2 * (2 * vnoise1(Y, 9.0, hashu(f['id'], 1)) - 1) - 0.4 * (Y > top_row + 3)).astype(np.int64)
    dr = np.round(1.2 * (2 * vnoise1(Y, 11.0, hashu(f['id'], 2)) - 1)).astype(np.int64)
    fx0, fx1 = f['x0'] + dl, f['x1'] + dr
    onface = (K == FACEK) & np.isin(P['PY'], f.get('rows', [f['py']])) & (Y >= top_row) & (Y <= foot_row + 2)
    fall = onface & (X >= fx0) & (X < fx1)
    wet = onface & ~fall & (X >= fx0 - 3) & (X < fx1 + 3)
    # the frame: wet rock darker and cooler either side, a dark recess right beside the water
    fr.T[wet] = np.where(fr.T[wet] == EDGE, EDGE, np.maximum(0, fr.T[wet] - 1))
    beside = wet & ((X == fx0 - 1) | (X == fx1))
    fr.T[beside] = 0
    fr.tag[wet] = TAG['wet']
    rel = (X + 0.5 - fx0) / np.maximum(1, fx1 - fx0)
    # a lit west edge (5 then 4), the body in sheets (3 with 4 streaks), the shaded east edge
    t = np.where(rel < 0.2, 4, np.where(rel > 0.8, 2, 3))
    t = np.where(X == fx0, 5, t)
    streak = fall & (rel > 0.15) & (rel < 0.85) & (h01(hashu(f['id'], 3), X, Y // 6) < 0.45) & (np.mod(Y + X * 3, 6) < 4)
    t = np.where(streak, np.minimum(5, t + 1), t)
    gap = fall & (rel > 0.25) & (rel < 0.8) & (h01(hashu(f['id'], 5), X, Y // 4) < 0.12) & ~streak
    t = np.where(gap, 2, t)
    fr.F[fall] = wf[0]
    fr.T[fall] = t[fall]
    fr.tag[fall] = TAG['water']
    # foam at the lip: the water rolls over white
    lip = fall & (Y <= top_row + 2)
    fr.F[lip] = np.where((h01(hashu(f['id'], 6), X, Y) < 0.6)[lip], FID['snow'], wf[0])
    fr.T[lip] = np.where(Y[lip] == top_row, 5, 4)
    # mist where it lands: pale clusters rising over the rock and the pool's edge
    cx = (f['x0'] + f['x1']) / 2
    mq = ((X + 0.5 - cx) / (w0 / 2 + 7.0)) ** 2 + ((Y + 0.5 - foot_row) / 9.0) ** 2
    mist = (mq <= 1.0) & ~fall & (Y <= foot_row + 3) & (h01(hashu(f["id"], 7), X // 2, Y // 2) < 0.65 * (1.2 - mq)) \
        & np.isin(fr.tag, (TAG['rock'], TAG['recess'], TAG['wet'], TAG['ground'], TAG['leaf']))
    fr.F[mist] = np.where(mq[mist] < 0.45, FID['snow'], FID['water'])
    fr.T[mist] = np.where(mq[mist] < 0.45, 3, 5)
    fr.tag[mist] = TAG['foam']
    # the spring: a seep of moss and leaves at the head of a spring fall
    if f['kind'] == 'spring':
        seep = (K == FACEK) & (P['PY'] == f['py']) & (np.abs(Y - top_row + 1) <= 1) & (X >= fx0 - 3) & (X < fx1 + 3) & ~fall
        lf = sibs('leaf')
        fr.F[seep] = lf[(h01(hashu(f['id'], 4), X, Y) * 3).astype(np.int64)[seep]]
        fr.T[seep] = np.where(Y[seep] < top_row, 4, 2)
        fr.tag[seep] = TAG['leaf']
    _pool(fr, world, f, foot_row, (f['x0'] + f['x1']) / 2, w0)


def _pool(fr: Frame, world: World, f: dict, foot_row: int, cx: float, w0: int):
    """A plunge pool on the ground under the fall: the fall's width plus about 8 each side
    (size-guide 7), dark under the cliff, depth in bands, ripple arcs round the landing over
    their own shadow, foam at the landing, glints in pairs, a bank of earth and stones."""
    P = fr.P
    K = P['kind']
    X, Y = fr.X, fr.Y
    hh = f['id']
    rx = w0 / 2 + 11 + 4 * h01(hh, 11)
    ry = 8.0 + 3.0 * h01(hh, 12)
    cy = foot_row + ry * 0.75
    q = ((X + 0.5 - cx) / rx) ** 2 + ((Y + 0.5 - cy) / ry) ** 2
    q = q + 0.14 * (2 * vnoise2(X, Y, 5.0, hashu(hh, 13)) - 1)
    ground = (K == TOP) & (P['ZH'] == f['h2']) & (P['ST'] == 0)
    pool = ground & (q <= 1.0) & (Y > foot_row)
    if not pool.any():
        return
    wf = sibs('water')
    t = np.where(q < 0.3, 1, np.where(q < 0.65, 2, 3))
    t = np.where(Y <= foot_row + 2, 1, t)
    lx, ly = cx, foot_row + 1.5
    rr = np.sqrt(((X + 0.5 - lx) / 2.0) ** 2 + (Y + 0.5 - ly) ** 2)
    for i, r0 in enumerate((4.0, 7.5)):
        broken = vnoise1((X + 0.5 - lx) + 40 * i, 3.0, hashu(hh, 19, i)) > 0.3
        ring = (rr >= r0) & (rr < r0 + 1.0) & (Y > ly + 1) & broken
        t = np.where(ring, 4, t)
        t = np.where((rr >= r0 + 1.0) & (rr < r0 + 2.0) & (Y > ly + 1) & broken & ~ring, np.maximum(1, t - 1), t)
    # foam where the fall lands: white clumps in pairs, thinning outwards
    fq = ((X + 0.5 - lx) / (w0 / 2 + 3.0)) ** 2 + ((Y + 0.5 - ly) / 3.5) ** 2
    foam = (fq <= 1.0) & (h01(hashu(hh, 14), X // 2, Y) < 0.85 - 0.5 * fq)
    t = np.where(foam, np.where(fq < 0.5, 5, 4), t)
    gl = (h01(hashu(hh, 15), X // 2, Y) < 0.05) & (q < 0.8) & (q > 0.4) & ~foam
    t = np.where(gl, 5, t)
    fr.F[pool] = np.where(foam[pool], FID['snow'], wf[0])
    fr.T[pool] = t[pool]
    fr.tag[pool] = TAG['water']
    bank = ground & ~pool & (q <= 1.5) & (Y > foot_row)
    ef = sibs('earth')
    fr.F[bank] = ef[2]
    fr.T[bank] = np.where(q[bank] < 1.2, 2, 3)
    fr.tag[bank] = TAG['path']
    # a rim of stones round the pool's near side, each a small boulder
    rim_ok = ground | (fr.tag == TAG['path'])
    n = int(6 + rx / 2)
    for i in range(n):
        u = (i + 0.5 + 0.4 * (h01(hh, 20, i) - 0.5)) / n
        ang = np.pi * (0.05 + 0.9 * u)
        sx = cx + np.cos(ang) * rx * 1.08
        sy = cy + np.sin(ang) * ry * 1.08
        if sy <= foot_row + 1:
            continue
        r0 = 1.8 + 1.2 * h01(hh, 21, i)
        boulder(fr, sx, sy, r0, r0 * 0.75, hashu(hh, 22, i), rim_ok, 'stone', moss=0.25)
    fr.pools = getattr(fr, 'pools', []) + [(cx, cy, rx, ry, f['h2'])]


# ---- dressing by rule -----------------------------------------------------------------------------
FERN = [stamp(['.44..', '44433', '33322', '2.2.2', '2...2']), stamp(['..44.', '.4433', '43332', '2222.', '.2..2']),
        stamp(['.4.4.', '44443', '33332', '2.22.'])]
# fern fronds: (dx, dy) per step of a frond, for seven fronds fanning from upper left to lower right
FRONDS = [((-1.0, -0.35), 0.06), ((-0.8, -0.75), 0.07), ((-0.3, -1.0), 0.08), ((0.25, -1.0), 0.08),
          ((0.75, -0.8), 0.07), ((1.0, -0.3), 0.06), ((-1.0, 0.15), 0.04), ((1.0, 0.2), 0.04)]


def _box(fr, x0, y0, x1, y1):
    a, b = max(0, x0 - fr.x0), max(0, y0 - fr.y0)
    c, d = min(fr.shape[1], x1 - fr.x0), min(fr.shape[0], y1 - fr.y0)
    if a >= c or b >= d:
        return None
    return (slice(b, d), slice(a, c))


def foliage(fr: Frame, cx, cy, rx, ry, hh, allow, base='leaf', tag=TAG['tree'], shadow=True):
    """The house foliage recipe: a crown in four light bands lit from the upper left, leaf
    clumps of about 2.6 px one tone above their band (a light cap, a dark U under), clumps
    from all three siblings, a yellow-green rim on the lit edge, the deep band quiet, the
    leaf's edge tone outside, and a round shadow thrown down and right on the ground."""
    bx = _box(fr, int(cx - rx - 3), int(cy - ry - 3), int(cx + rx + 6), int(cy + ry + 6))
    if bx is None:
        return
    X, Y = fr.X[bx], fr.Y[bx]
    al = allow[bx]
    q = ((X + 0.5 - cx) / rx) ** 2 + ((Y + 0.5 - cy) / ry) ** 2 + 0.3 * (vnoise2(X, Y, 2.2, hashu(hh, 21)) - 0.5)
    m = (q <= 1.0) & al
    if not m.any():
        return
    if shadow:
        sq = ((X + 0.5 - cx - 3) / (rx * 0.95)) ** 2 + ((Y + 0.5 - cy - ry * 0.75) / (ry * 0.6)) ** 2
        sh = (sq <= 1.0) & ~m & (fr.P['kind'][bx] == TOP) & np.isin(fr.tag[bx], (TAG['ground'], TAG['path'], TAG['snow']))
        T = fr.T[bx]
        T[sh] = np.maximum(0, T[sh] - 2)
    I = -(X + 0.5 - cx) / rx * 0.62 - (Y + 0.5 - cy) / ry * 0.72 + 0.3 * (1 - np.minimum(q, 1))
    shade_leaves(fr, bx, m, I, hh, base, tag, al)


def shade_leaves(fr: Frame, bx, m, I, hh, base='leaf', tag=TAG['tree'], al=None, outline=True):
    """Leaves over a mask `m` (inside the frame slice `bx`) whose light is `I` (high: lit):
    four light bands, clumps of about 2.6 px on a jittered lattice in world coordinates, each
    a tone above its band with a light cap and a dark U, siblings per clump, a yellow-green
    rim where the light catches the top and left edges, the leaf edge tone outside."""
    X, Y = fr.X[bx], fr.Y[bx]
    al = np.ones(m.shape, bool) if al is None else al
    band = np.where(I > 0.5, 4, np.where(I > 0.0, 3, np.where(I > -0.5, 2, 1)))
    # clumps: nearest of a jittered 4 px lattice in world coordinates
    gi, gj = X // 4, Y // 4
    best = np.full(X.shape, 1e9)
    cid = np.zeros(X.shape, np.uint32)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            a, b = gi + di, gj + dj
            px = a * 4 + 4 * h01(hh, a, b, 22)
            py = b * 4 + 4 * h01(hh, a, b, 23)
            dd = (X + 0.5 - px) ** 2 + (Y + 0.5 - py) ** 2
            better = dd < best
            best = np.where(better, dd, best)
            cid = np.where(better, hashu(hh, a, b, 24), cid)
    C = np.where(m, cid.astype(np.int64), -1)
    up = (nb(C, -1, 0) != C) & m
    dn = (nb(C, 1, 0) != C) & m
    t = band.copy()
    t = np.where(up & (band >= 2), np.minimum(5, band + 1), t)
    t = np.where(dn & (band >= 2), band - 1, t)
    t = np.where(band == 1, 1, t)
    ids = sibs(base)
    fam = ids[(h01(cid, 1) * 3).astype(np.int64) % 3]
    rim = m & ~nb(m, -1, 0) & (I > 0.25)
    rim |= m & ~nb(m, 0, -1) & (I > 0.25)
    fam = np.where(rim, FID['grass'], fam)
    t = np.where(rim, 5, t)
    if outline:
        ring = ~m & al & (nb(m, 1, 0) | nb(m, -1, 0) | nb(m, 0, 1) | nb(m, 0, -1))
    else:        # a hanging mat: closed only along its foot and its shaded east side
        ring = ~m & al & (nb(m, -1, 0) | nb(m, 0, -1))
    F, T, G = fr.F[bx], fr.T[bx], fr.tag[bx]
    F[m], T[m], G[m] = fam[m], t[m], tag
    F[ring], T[ring], G[ring] = ids[0], EDGE, tag


def boulder(fr: Frame, cx, cy, rx, ry, hh, allow, base, moss=0.0, tag=TAG['scree']):
    """A boulder fallen from the crag: a rounded lump in the rock's ramp lit from the upper
    left (a hard terminator), a glint at its top left, the rock's edge tone outside (broken
    to tone 1 on the lit top and left), a moss cushion on its crown now and then, a contact
    line and a shadow down and to the right."""
    bx = _box(fr, int(cx - rx - 3), int(cy - ry - 3), int(cx + rx + 5), int(cy + ry + 5))
    if bx is None:
        return
    X, Y = fr.X[bx], fr.Y[bx]
    al = allow[bx]
    q = ((X + 0.5 - cx) / rx) ** 2 + ((Y + 0.5 - cy) / ry) ** 2 + 0.16 * (vnoise2(X, Y, 2.0, hashu(hh, 31)) - 0.5)
    m = (q <= 1.0) & al
    if not m.any():
        return
    G0 = fr.tag[bx]
    sq = ((X + 0.5 - cx - 2.5) / (rx * 0.95)) ** 2 + ((Y + 0.5 - cy - ry * 0.55) / (ry * 0.7)) ** 2
    sh = (sq <= 1.0) & ~m & np.isin(G0, (TAG['ground'], TAG['path'], TAG['snow']))
    fr.T[bx][sh] = np.maximum(0, fr.T[bx][sh] - 2)
    I = -(X + 0.5 - cx) / rx * 0.6 - (Y + 0.5 - cy) / ry * 0.75 + 0.35 * (1 - np.minimum(q, 1))
    t = np.where(I > 0.55, 4, np.where(I > 0.05, 3, np.where(I > -0.45, 2, 1)))
    t = np.where((I > 0.75) & (q > 0.45), 5, t)
    bottom = m & ~nb(m, 1, 0)
    t = np.where(bottom, 1, t)
    ids = sibs(base)
    fam = np.full(X.shape, ids[int(hashu(hh, 32) % np.uint32(3))])
    sw = h01(hh, X // 2, Y // 2, 33) < 0.2
    fam = np.where(sw, ids[int(hashu(hh, 34) % np.uint32(3))], fam)
    if moss > 0 and h01(hh, 35) < moss:
        cap = m & (Y + 0.5 < cy - ry * (0.2 + 0.25 * h01(hh, X, 36))) & (q < 0.9)
        fam = np.where(cap, FID['leaf'], fam)
        t = np.where(cap, np.where(nb(cap, -1, 0), 3, 4), t)
        t = np.where(cap & ~nb(cap, 1, 0), 2, t)
    ring = ~m & al & (nb(m, 1, 0) | nb(m, -1, 0) | nb(m, 0, 1) | nb(m, 0, -1))
    lit = ring & ((nb(m, 1, 0) & (nb(t, 1, 0) >= 4)) | (nb(m, 0, 1) & (nb(t, 0, 1) >= 4)))
    F, T, G = fr.F[bx], fr.T[bx], fr.tag[bx]
    F[m], T[m], G[m] = fam[m], t[m], tag
    F[ring], T[ring], G[ring] = ids[0], np.where(lit[ring], 1, EDGE), tag


def fern(fr: Frame, x, y, hh, allow, size=1.0):
    """A fern: seven or eight fronds fanning from its foot, each a rib of leaf pairs that
    droops at the tip; fronds to the upper left lit, to the right in shade."""
    lf = sibs('leaf')
    n = 0
    for k, ((ux, uy), droop) in enumerate(FRONDS):
        if h01(hh, k, 41) < 0.2:
            continue
        L = int(round((4 + 4 * h01(hh, k, 42)) * size))
        lit = 4 if ux < -0.2 and uy < 0 else (3 if ux < 0.4 else 2)
        f = int(lf[int(hashu(hh, k, 43) % np.uint32(3))])
        for i in range(L + 1):
            fx = x + ux * i
            fy = y + uy * i + droop * i * i * 1.6
            for (ox, oy, dt) in ((0, 0, 0), (1, 0, -1), (0, 1, -1)):
                X, Y = int(round(fx)) + ox - fr.x0, int(round(fy)) + oy - fr.y0
                if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1] and allow[Y, X]:
                    fr.F[Y, X] = f
                    fr.T[Y, X] = max(1, lit + dt - (1 if i == L else 0))
                    fr.tag[Y, X] = TAG['leaf']
                    n += 1
    return n


def dress_faces(fr: Frame, world: World):
    """On the faces: ivy mats and cascading greenery hanging from grassy rims (longest in the
    middle, clumps lit on the left, a shadow on the rock to their right, stringy strands below),
    moss on the crowns of lower crags, ferns and cushions in the fissures."""
    if not hasattr(fr, 'face'):
        return
    T, seed = world.T, world.seed
    f = fr.face
    yy, xx, s, lid, d, Hf = f['yy'], f['xx'], f['s'], f['lid'], f['d'], f['Hf']
    rimg = getattr(fr, 'rim_mat', np.zeros(s.shape)) == MAT_GROUND
    lf = sibs('leaf')
    mat = np.zeros(s.shape, bool)
    strands = np.zeros(s.shape, bool)
    tone = np.zeros(s.shape, np.int64)
    fam = np.zeros(s.shape, np.int64)
    for kind, sp, p, (w0, w1), (l0, l1), cl in (('ivy', 15.0, T['ivy'], (6, 13), (0.35, 0.8), 3.0),
                                                ('cascade', 23.0, T['cascade'], (16, 28), (0.5, 0.95), 4.0)):
        if p <= 0:
            continue
        k0 = np.floor(s / sp).astype(np.int64)
        for dk in (-1, 0, 1):
            kk = k0 + dk
            hk = hashu(seed, lid, kk, 201 if kind == 'ivy' else 202)
            on = (h01(hk, 1) < p) & rimg & (Hf >= 24)
            sk = kk * sp + sp * h01(hk, 2)
            Wv = w0 + (w1 - w0) * h01(hk, 3)
            Lv = Hf * (l0 + (l1 - l0) * h01(hk, 4))
            dx = s - sk
            u = np.clip(1 - (2 * dx / Wv) ** 2, 0, 1)
            ln = Lv * (0.4 + 0.6 * np.sqrt(u)) + 7 * (vnoise1(s, 2.5, hashu(hk, 5)) - 0.5) - 4 * (h01(hk, np.floor(s / 2).astype(np.int64), 9) < 0.3)
            half = Wv / 2 * (1 - 0.3 * np.clip(d / np.maximum(1, Lv), 0, 1)) + 2.2 * (vnoise1(d + 50 * (dx > 0), 3.0, hashu(hk, 10)) - 0.5)
            inside = on & (np.abs(dx) < half) & (d <= ln)
            lit = -dx / np.maximum(1, half) * 0.55 - d / np.maximum(1, ln) * 0.6 + 0.35
            new = inside & ~mat
            mat |= inside
            tone = np.where(new, (lit * 100).astype(np.int64), tone)
            fam = np.where(new, 1 if kind == 'cascade' else 0, fam)
            # stringy strands below the mat
            strand = on & (np.abs(dx) < half * 0.8) & (d > ln) & (d <= ln + 2 + 7 * h01(hk, np.floor(s).astype(np.int64), 7)) \
                & (h01(hk, np.floor(s).astype(np.int64), 8) < 0.28) & ~mat & (kind == 'ivy')
            strands |= strand
    # the mat's shadow on the rock, two px to its right; then the leaves
    MAT = np.zeros(fr.shape, bool)
    MAT[yy[mat], xx[mat]] = True
    shade = (nb(MAT, 0, -1) | nb(MAT, 0, -2)) & ~MAT & np.isin(fr.tag, (TAG['rock'], TAG['recess']))
    fr.T[shade] = np.where(fr.T[shade] == EDGE, EDGE, np.maximum(0, fr.T[shade] - 1))
    if MAT.any():
        LI = np.zeros(fr.shape)
        LI[yy[mat], xx[mat]] = tone[mat] / 100.0
        whole = (slice(0, fr.shape[0]), slice(0, fr.shape[1]))
        shade_leaves(fr, whole, MAT, LI, hashu(seed, 203), 'leaf', TAG['leaf'], np.isin(fr.tag, (TAG['rock'], TAG['recess'], TAG['leaf'])),
                     outline=False)
    if strands.any():
        ST_ = np.zeros(fr.shape, bool)
        ST_[yy[strands], xx[strands]] = True
        ST_ &= ~MAT
        fr.F[ST_] = lf[2]
        fr.T[ST_] = np.where(np.mod(fr.Y[ST_], 3) == 0, 3, 2)
        fr.tag[ST_] = TAG['leaf']
    if T['built']:
        return
    # moss cushions on the crowns of the lower crags (damp, under the overhang of the upper)
    m = f['mass']
    crown = (f['k'] >= 0) & ~f['rec'] & (h01(m, 51) < 0.55)
    MID = np.full(fr.shape, -1, np.int64)
    MID[yy, xx] = np.where(~f['rec'], m.astype(np.int64), -1)
    topm = (nb(MID, -1, 0) != MID)[yy, xx] & crown & (d > 6)
    TOPM = np.zeros(fr.shape, bool)
    TOPM[yy[topm], xx[topm]] = True
    TOPM2 = nb(TOPM, -1, 0) & (MID >= 0) & ~MAT & (h01(hashu(seed, 52), fr.X // 3, fr.Y) < 0.6)
    for M, tt in ((TOPM & ~MAT, 4), (TOPM2, 2)):
        fr.F[M] = lf[(h01(hashu(seed, 53), fr.X // 4, fr.Y) * 3).astype(np.int64) % 3][M]
        fr.T[M] = tt
        fr.tag[M] = TAG['leaf']
    # plants in the fissures: a cushion or a fern where a crag's west fissure has room
    allow = np.isin(fr.tag, (TAG['rock'], TAG['recess']))
    sel = f['rec'] & (f['ce'] < 1.2) & (f['ce'] >= 0) & (np.abs(d - np.round(Hf * (0.3 + 0.4 * h01(m, 54)))) < 0.5) \
        & (h01(m, 55) < T['crack_plants']) & (s - (s - f['ce']) < 1.2)
    done = set()
    for i in np.nonzero(sel)[0]:
        key = int(m[i])
        if key in done:
            continue
        done.add(key)
        st = FERN[int(hashu(m[i], 56) % np.uint32(3))]
        put_stamp(fr, st, int(fr.X[yy[i], xx[i]]), int(fr.Y[yy[i], xx[i]]),
                  lambda t, k=key: int(lf[int(hashu(k, t, 57) % np.uint32(3))]), allow=allow, tag=TAG['leaf'], anchor=(2, 1))


def dress_feet(fr: Frame, world: World):
    """At the feet: scree in the rock's own siblings, thickest close to the face; a boulder
    now and then (fallen from the crag, mossy where it is damp); tufts growing up over the
    foot so the line between ground and cliff is soft; ferns where the ground is damp (by
    water and in the shade of a face); shrubs at feet and on tops; a tree on a top well back
    from its rim."""
    T, seed = world.T, world.seed
    P = fr.P
    K = P['kind']
    ground = (K == TOP) & np.isin(fr.tag, (TAG['ground'], TAG['path'])) & (P['ST'] == 0)
    face = (K == FACEK)
    dist = np.zeros(fr.shape, np.int32)
    for k in range(14, 0, -1):
        dist = np.where(nb(face, -k, 0), k, dist)
    stair_near = near(P['ST'] == 1, 10)
    water_near = near(fr.tag == TAG['water'], 6)
    rock = T['rock']
    rid = sibs(rock)
    okg = ground & ~stair_near
    # tufts over the foot
    if T['top'] == 'grass':
        foot = okg & (dist >= 1) & (dist <= 2)
        allow = (ground | face) & ~(fr.tag == TAG['water'])
        gid = sibs('grass')
        for x, y, hh in zip(*candidates(fr, 5, hashu(seed, 211), np.where(foot, 0.75, 0.0))):
            put_stamp(fr, TUFTS[int(hh % np.uint32(len(TUFTS)))], x, y, int(gid[int(hashu(hh, 4) % np.uint32(3))]),
                      allow=allow, anchor=(2, 3))
    # scree
    if T['scree'] > 0:
        pv = np.where(okg & (dist > 0), T['scree'] * np.clip(1.15 - dist / 9.0, 0, 1), 0.0)
        for x, y, hh in zip(*candidates(fr, 4, hashu(seed, 212), pv)):
            r = h01(hh, 5)
            if r < 0.6:
                put_stamp(fr, PEBBLE[int(hh % np.uint32(4))], x, y, int(rid[int(hashu(hh, 4) % np.uint32(3))]), allow=okg, tag=TAG['scree'])
                Yc, Xc = y + 2 - fr.y0, x - fr.x0
                if 0 <= Yc < fr.shape[0] and 0 <= Xc + 1 < fr.shape[1] and okg[Yc, Xc]:
                    fr.T[Yc, Xc:Xc + 2] = np.maximum(0, fr.T[Yc, Xc:Xc + 2] - 2)
            else:
                boulder(fr, x, y, 1.8 + 1.6 * h01(hh, 6), 1.4 + 1.0 * h01(hh, 7), hh, okg, rock)
    if T['boulders'] > 0:
        pv = np.where(okg & (dist >= 3) & (dist <= 9) & ~water_near, T['boulders'], 0.0)
        for x, y, hh in zip(*candidates(fr, 26, hashu(seed, 213), pv)):
            rx = 4 + 5 * h01(hh, 8)
            boulder(fr, x, y, rx, rx * (0.62 + 0.15 * h01(hh, 9)), hh, okg | (fr.tag == TAG['scree']), rock, moss=0.6)
    # ferns where it is damp
    if T['ferns'] > 0:
        damp = ground & ~stair_near & ((water_near & (fr.tag != TAG['water'])) | ((dist >= 1) & (dist <= 4)))
        pv = np.where(damp, np.where(water_near, T['ferns'], T['ferns'] * 0.35), 0.0)
        for x, y, hh in zip(*candidates(fr, 12, hashu(seed, 214), pv)):
            fern(fr, x, y, hh, (ground | face) & (fr.tag != TAG['water']) & (fr.tag != TAG['stair']), 1.0 + 0.5 * h01(hh, 10))
    # shrubs and trees on open ground
    open_g = ground & ~near(~ground, 4) & ~near(fr.tag == TAG['water'], 16)
    if T['shrubs'] > 0:
        pv = np.where(open_g & (dist == 0), T['shrubs'] * 20, np.where(ground & (dist > 2) & (dist < 12) & ~stair_near & ~near(fr.tag == TAG['water'], 16), T['shrubs'] * 30, 0.0))
        for x, y, hh in zip(*candidates(fr, 28, hashu(seed, 215), pv)):
            rx = 4.5 + 3.5 * h01(hh, 11)
            foliage(fr, x, y - rx * 0.4, rx, rx * 0.75, hh, ground | (fr.tag == TAG['scree']), base=T.get('shrub', 'leaf'))
    if T['trees'] > 0:
        far = ground & ~near(~ground, 14)
        for x, y, hh in zip(*candidates(fr, 72, hashu(seed, 216), np.where(far & ~water_near, T['trees'] * 120, 0.0))):
            tr = sibs('timber')
            for dy in range(0, 9):
                for dx in (-1, 0, 1):
                    X, Y = x + dx - fr.x0, y - dy - fr.y0
                    if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1]:
                        fr.F[Y, X] = tr[0]
                        fr.T[Y, X] = 3 if dx < 0 else (2 if dx == 0 else 1)
                        fr.tag[Y, X] = TAG['tree']
            rx = 12 + 4 * h01(hh, 12)
            foliage(fr, x + 0.5, y - 9 - rx * 0.7, rx, rx * 0.85, hh, (fr.P['kind'] > 0) & (fr.tag != TAG['figure']), base='leaf')


# ---- the figure for scale ---------------------------------------------------------------------
def figure(fr: Frame, name: str, foot_x: int, foot_y: int):
    """A resident (an adult, 25 px) standing with its feet at (foot_x, foot_y), with a contact
    shadow: only for the demos, to judge the scale."""
    p = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')  # ledger: compare (scale figure)
    im = Image.open(p).convert('RGBA')
    im = im.resize((im.width // 4, im.height // 4), Image.NEAREST)
    a = np.asarray(im)
    ys, xs = np.nonzero(a[..., 3] > 127)
    h, w0 = ys.max() + 1, (xs.min() + xs.max()) // 2
    # the colours of the sprite are kept as they are: write them into spare palette slots
    for y, x in zip(ys, xs):
        X, Y = foot_x + x - w0 - fr.x0, foot_y + y - h - fr.y0
        if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1]:
            fr.extra[(Y, X)] = tuple(int(v) for v in a[y, x, :3])
            fr.tag[Y, X] = TAG['figure']
    for dx in range(-4, 5):
        X, Y = foot_x + dx - fr.x0, foot_y - fr.y0
        if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1] and fr.tag[Y, X] != TAG['figure']:
            fr.T[Y, X] = max(0, min(fr.T[Y, X], 5) - (2 if abs(dx) < 3 else 1))


# ---- the demos: one screen each, to copy ------------------------------------------------------
W_DEMO, H_DEMO = 320, 384


def _plan_rows(top):
    return np.arange(H_DEMO + top)[:, None], np.arange(W_DEMO)[None, :]


def demo_highland(seed: int = 3) -> tuple:
    """The bake-off brief as rules over a height field: a meadow (z 0); a 64 px cliff to the
    upper tier (64) with a ledge (32) along it; a 32 px step to the top (96), whose broad
    field takes snow by the table's rule; a stream from the snow to the upper rim, so it falls
    the 64 px face into a plunge pool; stairs cut from the meadow to the ledge and from the
    ledge to the upper tier; a trodden path on the ledge and up the meadow to the stair."""
    W = W_DEMO
    R2 = curve([(-20, 30), (30, 38), (62, 60), (84, 80), (104, 92), (128, 96), (152, 98), (176, 106), (200, 112),
                (222, 108), (248, 100), (276, 94), (300, 96), (340, 98)], W)
    R1 = curve([(-20, 176), (0, 178), (26, 184), (56, 192), (82, 189), (102, 188), (118, 198), (134, 196),
                (150, 186), (170, 190), (190, 196), (212, 188), (232, 174), (250, 168), (266, 174), (286, 190),
                (304, 200), (340, 196)], W)
    tread = curve([(-20, -8), (6, -6), (18, 2), (30, 12), (60, 13), (90, 12), (120, 14), (138, 26), (152, 40),
                   (170, 44), (186, 40), (198, 14), (208, -4), (230, -10), (340, -10)], W)
    RL = np.where(tread > 0, R1 + 32 + tread, np.nan)
    Z, top = from_rims(W, H_DEMO, [(96, R2), (64, R1), (32, RL)])
    py, px = _plan_rows(top)
    xc = 252 + 6 * np.sin(py / 13.0) + 2 * np.sin(py / 5.0)
    ww = 2.0 + 1.6 * (0.5 + 0.5 * np.sin(py / 7.0 + 1)) + 0.8 * (0.5 + 0.5 * np.sin(py / 3.1))
    water = (np.abs(px - xc) <= ww) & (Z == 64)
    ledge = Z == 32
    m = (np.abs(px - (168 + 18 * np.sin((py - top) / 40.0) - 0.15 * (py - top - 300))) <= 4 + (py - top - 280) * 0.02) & (Z == 0) \
        & (py - top > 250)
    path = ledge | m
    stairs = [Stair(150, 186, int(np.round(R1[168] + 32 + tread[168])) + top + 32 + 1, 0, 32, tread=4),
              Stair(30, 66, int(np.round(R1[48])) + top + 64 + 1, 32, 64, tread=4)]
    w = World(Z, 'highland', seed=seed, top=top, water=water, path=path, stairs=stairs)
    return w, ('hiker', 112, int(np.round(R1[112] + 32 + tread[112] * 0.6)))


def demo_coast(seed: int = 5) -> tuple:
    """A headland: a grass top (64) over a 64 px cliff of pale sandstone bands on a dark
    basalt foot, a lower grass shelf (32) at the west, a beach (0) and the sea."""
    W = W_DEMO
    R1 = curve([(-20, 120), (40, 128), (80, 150), (120, 162), (160, 156), (200, 150), (240, 162), (280, 176), (340, 170)], W)
    RS = curve([(-20, 236), (30, 240), (60, 232), (90, 220), (110, 214), (130, 260)], W)
    RS = np.where(np.arange(W) < 118, RS, np.nan)
    Z, top = from_rims(W, H_DEMO, [(64, R1), (32, RS)])
    py, px = _plan_rows(top)
    sea = (py - top > 300 + 14 * np.sin(px / 37.0) + 6 * np.sin(px / 11.0)) & (Z == 0)
    w = World(Z, 'coast', seed=seed, top=top, water=sea)
    return w, ('beachcomber', 200, 268)


def demo_canyon(seed: int = 7) -> tuple:
    """A canyon wall in the Reach: a mesa top (80), a bench (40) and the canyon floor (0),
    40 px faces of red and buff bands, a dry wash along the floor, a stair cut from the floor
    to the bench."""
    W = W_DEMO
    R2 = curve([(-20, 60), (40, 70), (90, 96), (130, 104), (170, 92), (220, 78), (270, 84), (340, 96)], W)
    R1 = curve([(-20, 190), (30, 196), (70, 214), (120, 222), (160, 206), (200, 196), (250, 210), (300, 230), (340, 226)], W)
    Z, top = from_rims(W, H_DEMO, [(80, R2), (40, R1)])
    py, px = _plan_rows(top)
    wash = (np.abs(py - top - (318 + 10 * np.sin(px / 29.0))) <= 5 + 2 * np.sin(px / 13.0)) & (Z == 0)
    stairs = [Stair(206, 246, int(np.round(R1[226])) + top + 40 + 1, 0, 40)]
    w = World(Z, 'canyon', seed=seed, top=top, path=wash, stairs=stairs)
    return w, ('prospector', 140, 300)


def demo_city(seed: int = 9) -> tuple:
    """A city retaining wall: an upper street (40) behind a 40 px wall of dressed stone with a
    coping, the lower street (0) at its foot, a stair with cheeks between them."""
    W = W_DEMO
    R1 = curve([(-20, 168), (60, 168), (100, 172), (140, 180), (180, 180), (220, 172), (260, 168), (340, 168)], W)
    Z, top = from_rims(W, H_DEMO, [(40, R1)])
    stairs = [Stair(140, 180, int(np.round(R1[160])) + top + 40 + 1, 0, 40)]
    w = World(Z, 'city', seed=seed, top=top, stairs=stairs)
    return w, ('porter', 90, 290)


DEMOS = {'highland': demo_highland, 'coast': demo_coast, 'canyon': demo_canyon, 'city': demo_city}


def random_world(seed: int, width: int = W_DEMO, height: int = H_DEMO, table: str = 'highland') -> World:
    """A random outline for the proofs: tiers of 32 rising to the north on a broad noise field,
    each level's mask rounded (terrace.rounded), so the faces are 32 or 64 px and the plan
    shapes lobe, bay and spur. Nothing in it is hand-placed."""
    top = 96
    PH = height + top
    py, px = np.mgrid[0:PH, 0:width]
    sy = py - top
    base = (1.0 - sy / height) * 4.0 + 0.1 + 2.6 * (fbm2(px, sy, 110.0, hashu(seed, 401), 3) - 0.5)
    lvl = np.clip(np.floor(base), 0, 3).astype(np.int32)
    import terrace
    Z = np.zeros((PH, width), np.int32)
    prev = np.ones((PH, width), bool)
    for k in (1, 2, 3):
        m = terrace.rounded(lvl >= k, 6) & prev
        Z[m] = 32 * k
        prev = m
    # the field was drawn in screen rows: a tier of height z stands z rows further south in
    # plan, so each rim lands where the noise put it on the screen
    Zs = np.zeros_like(Z)
    for k in (1, 2, 3):
        m = Z >= 32 * k
        sh = np.zeros_like(m)
        sh[32 * k:] = m[:PH - 32 * k]
        sh[:32 * k] = m[:1].repeat(32 * k, 0)
        Zs[sh] = 32 * k
    return World(Zs, table, seed=seed, top=top)


def build(world: World, fig=None, box=None) -> Image.Image:
    r = render(world, box)
    fr = r.fr
    if fig:
        figure(fr, *fig)
    return r.image()


# ---- the checks ------------------------------------------------------------------------------------
RAMP_TONES = 0.85     # house-style 7, ruling of 20 Oct 17:30: ramp-built art passes tones at 85 %


def best_box(mask: np.ndarray, w: int, h: int):
    """The w x h box holding the most of `mask` (a summed-area table, every second px)."""
    H, W = mask.shape
    ii = np.pad(mask.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    ys, xs = np.mgrid[0:H - h:2, 0:W - w:2]
    v = ii[ys + h, xs + w] - ii[ys, xs + w] - ii[ys + h, xs] + ii[ys, xs]
    i = int(np.argmax(v))
    y, x = int(ys.ravel()[i]), int(xs.ravel()[i])
    return (x, y, x + w, y + h), float(v.ravel()[i]) / (w * h)


def bar_check(img: Image.Image, box, kind: str):
    """detail_bar.py's check, with the house ruling for ramp-built art (tones at 85 %)."""
    import detail_bar as db
    ok, ours, lines = db.check_image(img, box, kind)
    ref = db.bar(kind)
    house = (ours['tones'] >= RAMP_TONES * ref['tones'] and ours['shapes'] >= db.TOLERANCE * ref['shapes']
             and ours['dressing'] >= db.TOLERANCE * ref['dressing']
             and ours['isolated'] <= ref['isolated'] + db.ISOLATED_MARGIN
             and ours['cluster'] >= db.CLUSTER_SHARE * ref['cluster'])
    return house, ok, ours, ref


def lint(img: Image.Image) -> dict:
    import style_lint as sl
    m = sl.measure(img)
    m['misses'] = sl.misses(m)
    return m


def crag_light(r: 'Render') -> float:
    """House light, measured the way style_lint measures a sprite (the west quarter of each row
    minus the east quarter, OKLab L x 100), on every crag of the render as its own sprite, and
    averaged: is each rock form lit from the west?"""
    fr = r.fr
    x0, y0, x1, y1 = r.crop
    MID = getattr(fr, 'MID', None)
    if MID is None:
        return 0.0
    MID = MID[y0:y1, x0:x1]
    Lmap = np.array([[hp.to_oklab(tuple(int(v) for v in LUT[f, t]))[0] for t in range(7)] for f in range(len(NAMES))])
    L = Lmap[fr.F[y0:y1, x0:x1], np.clip(fr.T[y0:y1, x0:x1], 0, 6)]
    vals = []
    for m in np.unique(MID[MID >= 0]):
        ys, xs = np.nonzero(MID == m)
        if len(ys) < 60:
            continue
        we = []
        for y in np.unique(ys):
            row = np.sort(xs[ys == y])
            if len(row) >= 8:
                q = max(1, len(row) // 4)
                we.append(L[y, row[:q]].mean() - L[y, row[-q:]].mean())
        if we:
            vals.append(100 * float(np.mean(we)))
    return float(np.mean(vals)) if vals else 0.0


def proof(img: Image.Image, tag: np.ndarray) -> dict:
    """The detail bar on the barest rock (stone-wall and face) and the most open ground of a
    render, and the lint on the whole of it."""
    rock_box, rf = best_box(np.isin(tag, (TAG['rock'], TAG['recess'])), 50, 34)
    ground_box, gf = best_box(tag == TAG['ground'], 66, 50)
    out = {'rock_box': rock_box, 'rock_share': rf, 'ground_box': ground_box, 'ground_share': gf}
    for kind, box in (('stone-wall', rock_box), ('face', rock_box), ('ground', ground_box)):
        out[kind] = bar_check(img, box, kind)
    out['lint'] = lint(img)
    out['lint_rock'] = lint(img.crop(rock_box))
    return out


def seam_test(seed: int = 11, size: int = 512, tile: int = 256) -> dict:
    """Render a random world whole and as four 256 px tiles; every tile must equal its crop
    of the whole, pixel for pixel (so two adjacent tiles meet with no seam)."""
    w = random_world(seed, size, size)
    whole = np.asarray(render(w).image())
    diffs = {}
    tiles = {}
    for ty in range(0, size, tile):
        for tx in range(0, size, tile):
            t = np.asarray(render(w, (tx, ty, tx + tile, ty + tile)).image())
            tiles[(tx, ty)] = t
            diffs[(tx, ty)] = int((t != whole[ty:ty + tile, tx:tx + tile]).any(-1).sum())
    a, b = tiles[(0, 0)], tiles[(tile, 0)]
    stitched = np.concatenate([a, b], axis=1)
    seam = int((stitched[:, tile - 2:tile + 2] != whole[:tile, tile - 2:tile + 2]).any(-1).sum())
    return {'diff_px': diffs, 'seam_px': seam}


def run_check() -> int:
    ok = True
    t = seam_test()
    print(f"seam: tiles differ from the whole by {t['diff_px']} px; the seam between two adjacent tiles: {t['seam_px']} px")
    ok &= t['seam_px'] == 0 and not any(t['diff_px'].values())
    for seed in PROOF_SEEDS:
        r = render(random_world(seed))
        img = r.image()
        _f, _t, tag = r.arrays()
        p = proof(img, tag)
        p['crag_light'] = crag_light(r)
        print(f'random outline {seed}: rock box {p["rock_box"]} ({100 * p["rock_share"]:.0f} % rock), '
              f'ground box {p["ground_box"]} ({100 * p["ground_share"]:.0f} % ground)')
        for kind in ('stone-wall', 'face', 'ground'):
            house, strict, ours, ref = p[kind]
            print(f'  {kind:10s} tones {ours["tones"]:5.1f}/{ref["tones"]:5.1f} shapes {ours["shapes"]:5.1f}/{ref["shapes"]:5.1f} '
                  f'dressing {ours["dressing"]:5.1f}/{ref["dressing"]:5.1f} isolated {ours["isolated"]:.3f}/{ref["isolated"]:.3f} '
                  f'cluster {ours["cluster"]:4.2f}/{ref["cluster"]:4.2f}  {"PASS" if house else "FAIL"}'
                  f'{"" if strict == house else " (90 % tones: " + ("PASS" if strict else "FAIL") + ")"}')
            ok &= house
        m = p['lint']
        bad = [x for x in m['misses'] if x in ('palette', 'speckle', 'dither')]
        bad += ['light-west (crags)'] if p['crag_light'] <= 0 else []
        print(f'  lint       {m["colours"]} colours, {100 * m["on_house"]:.1f} % on the house palette, '
              f'{100 * m["isolated"]:.1f} % lone px, {100 * m["checker"]:.2f} % dither; west minus east {p["crag_light"]:+.1f} '
              f'on the crags (whole picture {m["west_east"]:+.1f})  {"PASS" if not bad else "FAIL " + " ".join(bad)}')
        ok &= not bad
    print('cliff core check:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


PROOF_SEEDS = (1, 2, 3)


def outputs() -> dict:
    """Everything the generator writes (art-repro reproduces these bytes): the four demos and
    the three random-outline proofs, each at 1x and 3x."""
    out = {}
    for name, fn in DEMOS.items():
        w, fig = fn()
        r = render(w)
        figure(r.fr, *fig)
        out[name] = r.image()
    for seed in PROOF_SEEDS:
        out[f'proof-{seed}'] = render(random_world(seed)).image()
    return out


def compare(refdir: str, path: str):
    """The highland demo at 3x beside the Sea of Stars ledge path and cliff top and the
    Eastward Octopia crops, all brought to an adult of 25 px (detail_bar.to_scale). The
    screenshots are official and stay out of the repository: pass a local folder."""
    import detail_bar as db
    from PIL import ImageDraw

    def ref(p, box, adult):
        im = Image.open(os.path.join(refdir, p)).convert('RGB').crop(box)
        key = db.to_scale(im, adult)
        rgb = np.stack([(key >> 8) * 16 + 8, ((key >> 4) & 15) * 16 + 8, (key & 15) * 16 + 8], -1).astype(np.uint8)
        return Image.fromarray(rgb, 'RGB')

    S = 3
    up = lambda im: im.resize((im.width * S, im.height * S), Image.NEAREST)  # noqa: E731
    w, fig = demo_highland()
    r = render(w)
    figure(r.fr, *fig)
    ours = up(r.image())
    shots = [(ref('seaofstars/33.png', (0, 0, 1920, 1080), 150.0), 'Sea of Stars: the ledge path (press kit, Traversal-4)'),
             (ref('seaofstars/19.jpg', (0, 0, 960, 1080), 150.0), 'Sea of Stars: a cliff top over the void'),
             (ref('eastward/12.jpg', (0, 0, 960, 1080), 162.0), 'Eastward Octopia: rock cliff with grass top'),
             (ref('eastward/13.jpg', (0, 600, 1300, 1000), 162.0), 'Eastward Octopia: grass ledges and a stair')]
    g = 14
    r1 = up(shots[0][0])
    r2a, r2b = up(shots[1][0]), up(shots[2][0])
    r3 = up(shots[3][0])
    right_w = max(r1.width, r2a.width + g + r2b.width, r3.width)
    W_ = g + ours.width + g + right_w + g
    H_ = 34 + max(ours.height + 26, r1.height + 22 + max(r2a.height, r2b.height) + 22 + r3.height + 26)
    out = Image.new('RGB', (W_, H_), (34, 28, 36))
    d = ImageDraw.Draw(out)
    d.text((g, 10), 'Cliff core, highland demo at 3x (left) beside the references, every image at an adult of 25 px', fill=(240, 234, 222))
    out.paste(ours, (g, 34))
    d.text((g, 34 + ours.height + 6), 'ours: cliff_core.py demo_highland (the hiker on the ledge is 24 px)', fill=(240, 234, 222))
    x2, y = g + ours.width + g, 34
    out.paste(r1, (x2, y))
    d.text((x2, y + r1.height + 4), shots[0][1], fill=(240, 234, 222))
    y += r1.height + 22
    out.paste(r2a, (x2, y))
    out.paste(r2b, (x2 + r2a.width + g, y))
    d.text((x2, y + r2a.height + 4), shots[1][1], fill=(240, 234, 222))
    d.text((x2 + r2a.width + g, y + r2b.height + 4), shots[2][1], fill=(240, 234, 222))
    y += max(r2a.height, r2b.height) + 22
    out.paste(r3, (x2, y))
    d.text((x2, y + r3.height + 4), shots[3][1], fill=(240, 234, 222))
    out.save(path)


def main(argv) -> int:
    if '--check' in argv:
        return run_check()
    if '--compare' in argv:
        i = argv.index('--compare')
        compare(argv[i + 1], argv[i + 2])
        return 0
    out_dir = argv[0] if argv and not argv[0].startswith('--') else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    for name, img in outputs().items():
        img.save(os.path.join(out_dir, f'{name}.png'), optimize=False)
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(os.path.join(out_dir, f'{name}-3x.png'), optimize=False)
    print('cliff core: wrote', len(DEMOS) + len(PROOF_SEEDS), 'pictures at 1x and 3x to', os.path.relpath(out_dir, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

"""Cliff core: one terrain system, many biomes (docs/vision/cliff-core.md).

Edges and the soft grid follow Eastward only (Matt, 21 Oct 09:23; docs/vision/eastward-edges.md):
its geometry and value structure, never its colours. The look is the house look Matt chose from
the bake-off's tile swatch (21 Oct 09:31): rounded boulder faces, clean turf lips, warm house
ramps. The structure:

- Engine (crosses biomes). A world height field in plan space, its rims put on the soft grid
  (16 px along a rim, 8 across, corners rounded to radius 3) and traced as contours with arc
  length; strata fixed in absolute height; every random choice a hash of world coordinates, so
  any window renders the same pixels (`--check` tests a 512 px world against its four tiles);
  dressing placed by rule; walk masks and attach points.
- Grammar (shared by every biome, checked on every biome's output): the 8 px grid, the tier
  heights 12, 16, 32 and 40, the rim's 1 px wobble, light from the upper left, the lit lip, the
  dark line and shade under it, the foot band, the house palette and outline, the detail bar and
  the lint.
- Biomes (own, never recoloured): BIOMES tables and their EDGE_SETS: the face (boulders, slabs,
  an earthy bank, dressed courses), the lip (turf, sod, crumble, coping, the snow cornice), the
  foot, the stair (rock steps, timber steps), the bank of its water, its dressing and the set
  pieces it owns (Matt, 21 Oct 10:08 and 10:09).
- Pieces (Plan): a stair through a face, a ledge path, a spring with its brook, falls and
  plunge pools, a hollow with a pool, a snow-capped corner, boulder clusters, a scree foot, ivy
  over a lip, a footpath. Each edits the plan and leaves its dressing to the painter, adapts to
  where it lands and takes its variant from a hash of where it stands.

Every pixel is a (family, tone) cell of the house palette (art/house-palette.json). The one new
family is `crag` (accent:highland).

HOWTO (a lane): build a Plan, place pieces, render.
    import cliff_core as cc
    plan = cc.Plan(512, 512, 'highland', seed=4)
    plan.tier(64, [(-20, 196), (200, 188), (540, 206)])        # a rim drawn as a screen curve
    st = plan.stair(208, 64, width=40)                          # through the face nearest x 208
    plan.path([st.attach['foot'], (226, 330), (220, 520)], z=0)
    img = cc.render(plan.world()).image()                       # or render(world, box=...)
    tiers = cc.walk_tiers(plan.world())                         # terrace.from_plan's tier map

Run:
    python3 scripts/art/cliff_core.py            # write the demos, the area, the proofs and the
                                                 # module, reuse and edge sheets (art-repro)
    python3 scripts/art/cliff_core.py --check    # seam test, biome ownership, and the grammar
                                                 # on every biome's output; non-zero on a fault
    python3 scripts/art/cliff_core.py --compare REFDIR OUT.png   # beside Eastward (local
                                                 # official screenshots; keep OUT outside the repo)
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
from terrace import FACE, GRID, from_plan  # noqa: E402

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


# ---- the biomes: one table each, each with its own edges ------------------------------------
# Matt, 21 Oct 10:08: "do consider what can and cannot be reused. the edge of the grass biome
# should look different from an edge in the mountain. you can safely reuse parts in the same
# biome, in other biomes you have to be careful." So a biome is not a recolour: it owns its
# EDGE SET (the shapes of its faces, lips, feet, stair cuts and water banks, eastward-edges.md
# 2 to 6) and its set pieces (PIECES), and only the engine crosses biomes: the height field,
# the contour tracing, strata at absolute heights, the seamless hash noise, the placement
# rules, walk masks and attach points, plus the NEUTRAL parts listed below. A loose stone that
# crosses is drawn in the target biome's own rock (`loose`). `--check` fails if a biome draws
# with another biome's edge set or places a piece it does not own.
#
# Edge-set sizes (lip `over`, `shade`, `streaks`, foot `band`) are written in Eastward native px
# at its adult of 54 and turned into texels at the render's density by `measures`.
#
# A biome table: tier height, the rock (lump families in bands fixed in absolute height, so one
# band runs through every face of a region), the ground on its tops, the edge set's name, the
# dressing and the pieces it allows. Every colour is a house ramp (house-style.md 1).
EDGE_SETS = {
    # the highland cliff: rounded boulder faces (the house look, 21 Oct 09:31) under a clean
    # turf lip, a stony foot with scree, steps cut from the rock between boulder cheeks,
    # brooks in a small earth bank
    'highland': dict(
        biome='highland',
        face=dict(style='cobbles', shade='stone', world_lumps=True, big=0.09, big_f=1.9, aspect=0.3,
                  lump=dict(cw=5.6, ch=4.4, rx=(2.5, 3.7), ry=(2.1, 3.1), p=2.2), moss_caps=0.04),
        lip=dict(kind='turf', over=(0, 2), scale=3.2, lit_row=0.65, under=(1, 0), shade=(5, 7), streaks=(4, 9)),
        foot=dict(band=6, pebbles=0.18, tufts=0.75), stair='rock', bank=dict(rows=2, reeds=0.0)),
    # the meadow bank: a low earthy turf edge, soil in thin layers with clods, pale roots
    # hanging from a soft sod overhang, grass grown thick over its foot, timber steps with
    # posts, banks with reeds
    'meadow': dict(
        biome='meadow',
        face=dict(style='earth', lump=dict(cw=12, ch=7, rx=(4.6, 7.4), ry=(3.0, 4.6), p=2.2), roots=0.09),
        lip=dict(kind='sod', over=(0, 6), scale=5.5, lit_row=0.5, under=(0, 0), shade=(0, 0), streaks=(0, 0)),
        foot=dict(band=4, pebbles=0.05, tufts=1.0), stair='timber', bank=dict(rows=2, reeds=0.5)),
    # the woodland bank (the first finished screen, 21 Oct): packed rounded cobbles of mossy
    # grey stone (Matt liked the highland cobbles) with many moss caps, under a clean
    # forest-floor turf lip; a damp mossy foot with ferns; brooks in a reedy bank
    'woodland': dict(
        biome='woodland',
        face=dict(style='cobbles', shade='stone', world_lumps=True, big=0.11, big_f=1.8, aspect=0.25,
                  lump=dict(cw=5.2, ch=4.2, rx=(2.4, 3.5), ry=(2.0, 3.0), p=2.2), moss_caps=0.16),
        lip=dict(kind='turf', over=(0, 2), scale=2.8, lit_row=0.55, under=(1, 0), shade=(4, 6), streaks=(3, 7)),
        foot=dict(band=5, pebbles=0.12, tufts=0.9), stair='rock', bank=dict(rows=2, reeds=0.3)),
    # the sea cliff: pale bedded sandstone slabs on a dark basalt foot under a thin turf lip
    'coast': dict(
        biome='coast',
        face=dict(style='slabs', lump=dict(cw=24, ch=9, rx=(10.0, 17.0), ry=(3.8, 5.6), p=3.2), moss_caps=0.0),
        lip=dict(kind='turf', over=(0, 2), scale=2.4, lit_row=0.8, under=(1, 0), shade=(2, 4), streaks=(2, 4)),
        foot=dict(band=4, pebbles=0.3, tufts=0.3), stair='rock', bank=dict(rows=1, reeds=0.0)),
    # the canyon wall: red and buff slabs, a crumbling dry lip, a gritty foot
    'canyon': dict(
        biome='canyon',
        face=dict(style='slabs', lump=dict(cw=28, ch=8, rx=(12.0, 20.0), ry=(3.4, 4.8), p=3.6), moss_caps=0.0),
        lip=dict(kind='crumble', over=(0, 2), scale=2.0, lit_row=0.9, under=(1, 0), shade=(4, 4), streaks=(4, 9)),
        foot=dict(band=6, pebbles=0.35, tufts=0.0), stair='rock', bank=dict(rows=1, reeds=0.0)),
    # the city's retaining wall: dressed courses under a coping
    'city': dict(
        biome='city',
        face=dict(style='courses', lump=None, moss_caps=0.0),
        lip=dict(kind='coping', over=(6, 6), scale=1.0, lit_row=0.0, under=(1, 0), shade=(2, 2), streaks=(0, 0)),
        foot=dict(band=2, pebbles=0.0, tufts=0.0), stair='rock', bank=dict(rows=1, reeds=0.0)),
}
# what may cross biomes besides the engine: the figure for scale, falls and plunge pools as
# water (their banks are the biome's), cast shadows, despeckle, and the hand-drawn stamp shapes
# (tufts, pebbles, ferns), always drawn in the target biome's own families
NEUTRAL = ('figure', 'fall', 'shadow', 'despeckle', 'stamps')
_PIECES_HIGHLAND = ('stair', 'spring', 'ledge', 'snow_corner', 'boulders', 'ivy', 'path', 'pond', 'scree')
BIOMES = {
    'highland': dict(
        face=FACE, rock='crag', loose='crag', built=False, edges='highland',
        bands=[(14, 'crag_cool', 'plain'), (11, 'crag', 'plain'), (16, 'crag_warm', 'plain'),
               (9, 'crag', 'pebble'), (14, 'crag_cool', 'plain'), (12, 'crag_warm', 'plain')],
        spring=None, top='grass', top_sibs=(0.33, 0.14, 0.53), warm_lit=0.1, ledge='path',
        ivy=0.0, cascade=0.0, crack_plants=0.5, scree=0.45, boulders=0.2, ferns=0.6,
        shrubs=0.006, trees=0.0015, flowers=0.07, flower_fams=('plaster', 'brass', 'dusk', 'berry', 'sky'),
        snow_z=None, falls=0.0, pieces=_PIECES_HIGHLAND),
    'meadow': dict(
        face=16, rock='earth', loose='stone', built=False, edges='meadow',
        bands=[(4, 'earth_warm', 'plain'), (3, 'earth', 'plain'), (5, 'earth_cool', 'plain'), (3, 'earth', 'pebble')],
        spring=None, top='grass', top_sibs=(0.40, 0.30, 0.30), warm_lit=0.5, ledge='path',
        ivy=0.0, cascade=0.0, crack_plants=0.0, scree=0.0, boulders=0.05, ferns=0.3,
        shrubs=0.008, trees=0.002, flowers=0.09, flower_fams=('plaster', 'brass', 'berry', 'sky'),
        snow_z=None, falls=0.0, pieces=('stair', 'path', 'pond', 'boulders', 'spring')),
    'woodland': dict(
        face=32, rock='stone', loose='stone', built=False, edges='woodland', dress=False,
        bands=[(9, 'stone_cool', 'plain'), (8, 'stone', 'plain'), (11, 'stone_warm', 'plain'), (7, 'stone', 'pebble')],
        spring=None, top='moss', top_sibs=(0.45, 0.25, 0.30), warm_lit=0.3, ledge='path',
        ivy=0.0, cascade=0.0, crack_plants=0.6, scree=0.2, boulders=0.1, ferns=0.8,
        shrubs=0.0, trees=0.0, flowers=0.0, flower_fams=(), snow_z=None, falls=0.0,
        pieces=('path', 'pond', 'boulders', 'spring', 'ivy', 'scree')),
    'coast': dict(
        face=FACE, rock='sand', loose='basalt', built=False, edges='coast',
        bands=[(8, 'basalt', 'plain'), (6, 'basalt_cool', 'pebble'), (10, 'sand_cool', 'plain'),
               (8, 'sand', 'plain'), (6, 'bleached', 'plain'), (9, 'sand_warm', 'plain'), (10, 'sand', 'plain'),
               (7, 'bleached_cool', 'plain'), (9, 'sand_cool', 'plain')],
        spring=None, top='grass', floor={0: 'sand'}, top_sibs=(0.45, 0.25, 0.30), ledge='path',
        ivy=0.0, cascade=0.0, crack_plants=0.3, scree=0.4, boulders=0.3, ferns=0.0,
        shrubs=0.01, trees=0.0, flowers=0.08, flower_fams=('plaster', 'brass', 'berry'),
        snow_z=None, falls=0.0, pieces=('stair', 'ledge', 'boulders', 'path', 'scree')),
    'canyon': dict(
        face=40, rock='adobe', loose='clay', built=False, edges='canyon',
        bands=[(7, 'clay_cool', 'plain'), (5, 'adobe', 'plain'), (9, 'clay', 'plain'),
               (4, 'bleached', 'pebble'), (8, 'adobe_warm', 'plain'), (6, 'clay_warm', 'plain')],
        spring=None, top='sand', shrub='cactus', top_sibs=(0.45, 0.30, 0.25), ledge='path',
        ivy=0.0, cascade=0.0, crack_plants=0.12, scree=0.75, boulders=0.35, ferns=0.0,
        shrubs=0.006, trees=0.0, flowers=0.0, flower_fams=(), snow_z=None, falls=0.0,
        pieces=('stair', 'ledge', 'boulders', 'path', 'scree')),
    'city': dict(
        face=40, rock='ashlar', loose='ashlar', built=True, edges='city',
        bands=[(7, 'ashlar', 'course'), (6, 'ashlar_warm', 'course'), (7, 'ashlar_cool', 'course'),
               (6, 'ashlar', 'course'), (7, 'ashlar_warm', 'course'), (7, 'ashlar_cool', 'course')],
        mass_w=(8, 15), spring=None, top='stone', top_sibs=(0.45, 0.30, 0.25), ledge='path',
        ivy=0.12, cascade=0.0, crack_plants=0.25, scree=0.0, boulders=0.0, ferns=0.0,
        shrubs=0.0, trees=0.0, flowers=0.0, flower_fams=(), snow_z=None, falls=0.0,
        pieces=('stair', 'ledge', 'path')),
}
STRATA = BIOMES       # the earlier name of the tables
GREEN = ('grass', 'moss')    # tops drawn as a clean lawn (the meadow's grass, the woodland's moss)


# Eastward's edge measures in its own native px at an adult of 54 (eastward-edges.md), which
# `measures` converts to texels at a density: k = 25 x density / 54 (0.46 at 1x, 0.93 at 2x),
# so at 2x they apply almost one to one. Not doubled from the 1x numbers: each is rounded
# from Eastward's own size at that density.
EASTWARD = dict(corner=5.0, side=6.0, shadow=6.0, bank=4.5, band=(4.5, 9.0), wobble_run=7.0, adult=54.0)


def measures(s: float, E: dict) -> dict:
    """The edge measures in texels at density s, for an edge set E whose numbers are written in
    Eastward native px (lip, shade, streaks, foot) or are fixed one-texel lines."""
    k = ADULT_PX * s / EASTWARD['adult']

    def r(v, lo=0):
        return max(lo, int(round(v * k)))
    L, F = E['lip'], E['foot']
    return dict(
        k=k, corner=r(EASTWARD['corner'], 2), side=r(EASTWARD['side'], 3), shadow=r(EASTWARD['shadow'], 2),
        bank=r(EASTWARD['bank'], 1), band=(r(EASTWARD['band'][0], 1), r(EASTWARD['band'][1], 1)),
        lip=(r(L['over'][0]), r(L['over'][1])), lip_run=max(2.0, L['scale'] * k / 0.463),
        shade=(r(L['shade'][0]), r(L['shade'][1])), streaks=(r(L['streaks'][0]), r(L['streaks'][1])),
        foot=r(F['band'], 1 if F['band'] else 0))


def check_biomes() -> list:
    """The reuse rule as a check: every biome draws with its own edge set, no two edge sets are
    the same shapes in another colour, and every piece a biome allows is one the engine has."""
    faults = []
    for b, T in BIOMES.items():
        E = EDGE_SETS.get(T['edges'])
        if E is None or E['biome'] != b:
            faults.append(f'{b}: draws with edge set {T["edges"]!r}, which belongs to {E and E["biome"]}')
        for p in T['pieces']:
            if p not in PIECES:
                faults.append(f'{b}: allows an unknown piece {p!r}')
    keys = {}
    for name, E in EDGE_SETS.items():
        shape = repr((E['face'], E['lip'], E['foot'], E['stair'], E['bank']))
        if shape in keys:
            faults.append(f'edge sets {keys[shape]!r} and {name!r} are the same shapes')
        keys[shape] = name
    return faults


def band_table(table: dict, s: float = 1.0):
    """The band bounds (z of each band's bottom, in texels at density s) over one period, and
    their families."""
    th = np.array([b[0] for b in table['bands']], np.float64) * s
    bounds = np.concatenate([[0.0], np.cumsum(th)])
    fams = [b[1] for b in table['bands']]
    tex = [b[2] for b in table['bands']]
    return bounds, fams, tex


# ---- the world --------------------------------------------------------------------------------
@dataclass
class Stair:
    """A stair built out from a face (eastward-edges.md 6.1; Matt, 21 Oct: a stair belongs only
    in the face it climbs), in plan coordinates: open width x0..x1, `py` the plan row just in
    front of the rim (the first row of the lower ground), from `z_low` up to `z_high`. The
    flight stands in front of the face: a few broad steps of `riser` px (5 to 6, so 10 to 12
    art px at 2x) and `tread` plan rows each, the top one a riser below the upper floor, so the
    head is flush with the rim and the upper floor runs on flat behind it; the foot lands on
    the lower ground `(n - 1) * tread` rows out. Rock cheeks close both sides."""
    x0: int
    x1: int
    py: int
    z_low: int
    z_high: int
    tread: int = 5
    riser: float = 5.5
    landing: int = 2
    cheek: int = 8

    @property
    def n(self) -> int:
        """The number of risers (one more than the treads)."""
        return max(2, int(round((self.z_high - self.z_low) / self.riser)))

    @property
    def foot_row(self) -> int:
        """The plan row of the lower ground the flight lands on."""
        return self.py + (self.n - 1) * self.tread

    @property
    def top_row(self) -> int:
        return self.py

    def z_step(self, j: int) -> int:
        """The height of tread j (0 the one against the face, the highest)."""
        return int(round(self.z_high - (self.z_high - self.z_low) * (j + 1) / self.n))

    def rows(self) -> list:
        """(first plan row, last plan row + 1, z) of every tread."""
        return [(self.py + j * self.tread, self.py + (j + 1) * self.tread, self.z_step(j)) for j in range(self.n - 1)]

    def attach(self, top: int) -> dict:
        """Where paths join it, in screen px: the foot (the first row of lower ground in front
        of the bottom step) and the head (the upper floor just behind the rim)."""
        cx = (self.x0 + self.x1) // 2
        return {'foot': (cx, self.foot_row - top - self.z_low), 'head': (cx, self.py - 1 - top - self.z_high),
                'width': self.x1 - self.x0}


def _min_runs(cells: np.ndarray, n: int = 2) -> np.ndarray:
    """Merge runs shorter than n cells (a one-cell tab or notch) into their neighbours, along x
    then y, so an outline reads as a few clean blocks, not stair-stepping."""
    c = cells.copy()
    for _ in range(2):
        for axis in (1, 0):
            a = c if axis == 1 else c.T
            for row in a:
                k = 0
                L = len(row)
                while k < L:
                    j = k
                    while j < L and row[j] == row[k]:
                        j += 1
                    if j - k < n and k > 0 and j < L and row[k - 1] == row[j]:
                        row[k:j] = row[k - 1]
                    k = j
    return c


def grid_mask(m: np.ndarray, cell: int = 8, r: int = 4, r_in: int = 2, min_run: int = 3) -> np.ndarray:
    """A plan mask on the soft grid (Matt, 21 Oct 11:44 and the pilot review): taken cell by cell
    by majority, runs shorter than `min_run` cells merged away, then the corners rounded (outer
    radius r, inner r_in, in px)."""
    import terrace
    R, C = m.shape
    Rp, Cp = -(-R // cell) * cell, -(-C // cell) * cell
    M = np.pad(m, ((0, Rp - R), (0, Cp - C)), mode='edge')
    cells = M.reshape(Rp // cell, cell, Cp // cell, cell).mean(axis=(1, 3)) >= 0.5
    cells = _min_runs(cells, min_run)
    S = np.repeat(np.repeat(cells, cell, 0), cell, 1)[:R, :C]
    return terrace.rounded(S, r, r_in)


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
    decals: list = field(default_factory=list)      # dressing placed by set pieces (PIECES)
    snap: bool = True                               # rims on the soft grid (eastward-edges.md 1)
    density: float = 1.0                            # art texels per world px (1 to 3)
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
        self.T = BIOMES[self.table]
        self.E = EDGE_SETS[self.T['edges']]
        if self.snap:
            self._snap()
        else:
            self._step_steep()
        self.flag = np.zeros(self.Z.shape, np.int8)       # 1 a stair
        for st in self.stairs:
            self._carve(st)
        self.Zw = self.Z.copy()                          # the field in world units (walk maps)
        self.s = float(self.density)
        if not 1.0 <= self.s <= 3.0:
            raise ValueError('density: 1 to 3 art texels a world px')
        self.M = measures(self.s, self.E)
        self.face_t = int(round(self.T['face'] * self.s))
        if self.s != 1.0:
            self._densify()

    def _densify(self):
        """Raster the world at `s` texels a world px. The field, masks, stairs and the pieces'
        dressing are carried over from world units; then every tier's outline is rounded again
        at texel scale (Eastward's corner radius and its 1 texel steps, eastward-edges.md 1.4
        and 1.5), so a rim steps one texel at a time instead of in blocks of s."""
        import terrace
        s = self.s
        R, C = self.Z.shape
        R2, C2 = int(round(R * s)), int(round(C * s))
        ri = np.minimum((np.arange(R2) / s).astype(np.int64), R - 1)
        ci = np.minimum((np.arange(C2) / s).astype(np.int64), C - 1)
        Z2 = np.round(self.Z[ri][:, ci] * s).astype(np.int32)
        flag2 = self.flag[ri][:, ci]
        rr = max(self.M['corner'], int(round(4 * s)))      # half a cell outside, a quarter inside
        r_inner = max(1, int(round(2 * s)))
        out = np.zeros_like(Z2)
        prev = None
        for k in sorted({int(v) for v in np.unique(Z2[flag2 == 0]) if v > 0}):
            m = terrace.rounded(Z2 >= k, rr, r_inner)
            if prev is not None:
                m &= prev
            out[m] = k
            prev = m
        self.Z = np.where(flag2 > 0, Z2, out).astype(np.int32)
        self.flag = flag2
        for name in ('path', 'water', 'snow'):
            m = getattr(self, name)
            if m is not None:
                m2 = m[ri][:, ci]
                if name == 'water':      # close the raster's steps; never open (a brook is thin)
                    m2 = terrace.rounded(m2, 0, rr)
                setattr(self, name, m2)
        self.top = int(round(self.top * s))
        self._h = int(round(self._h * s))
        self.stairs = [Stair(int(round(st.x0 * s)), int(round(st.x1 * s)), int(round(st.py * s)), int(round(st.z_low * s)),
                             int(round(st.z_high * s)), tread=max(2, int(round(st.tread * s))), riser=st.riser * s,
                             landing=int(round(st.landing * s)), cheek=int(round(st.cheek * s))) for st in self.stairs]
        for st in self.stairs:       # the raster's rounding can leave a step row out: put it back
            for r0, r1, z in st.rows():
                self.Z[max(0, r0):r1, st.x0:st.x1] = z
                self.flag[max(0, r0):r1, st.x0:st.x1] = 1
        self.decals = [_scale_decal(d, s) for d in self.decals]

    def _snap(self, r: int = 4, r_in: int = 2):
        """Put every rim on the soft grid (eastward-edges.md 1.6; Matt, 21 Oct 11:44: "remember
        the grid shape like in eastward"): each tier's plan outline is taken cell by cell (8 px
        cells, by majority), runs shorter than three cells are merged away (no one- or two-cell
        tabs or notches), so a rim runs straight along x or y, turns only at a cell line, and a side
        face is vertical; then its corners are rounded (outer radius 4, half a cell; inner 2).
        Tiers stay nested. The rim's 1 px wobble is the lip's (lip_overhang), not the plan's."""
        Z = self.Z
        face = self.T['face']
        out = np.zeros_like(Z)
        prev = None
        for k in range(face, int(Z.max()) + 1, face):
            S = grid_mask(Z >= k, GRID, r, r_in)
            if prev is not None:
                S &= prev
            out[S] = k
            prev = S
        self.Z = out

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
        """Build the stair in front of the face. The upper floor is made good for a row or two
        behind the rim (so the head is flush), the ground either side of the flight is the
        lower ground, and the treads step down from the rim to the foot."""
        R, C = self.Z.shape
        x_a, x_b = max(0, st.x0 - st.cheek), min(C, st.x1 + st.cheek)
        back = self.Z[max(0, st.py - st.landing):st.py, x_a:x_b]
        self.Z[max(0, st.py - st.landing):st.py, x_a:x_b] = np.maximum(back, st.z_high)
        front = self.Z[st.py:min(R, st.foot_row + 1), x_a:x_b]
        self.Z[st.py:min(R, st.foot_row + 1), x_a:x_b] = np.minimum(front, st.z_low)
        # the flight is cut into a spur of the face (Matt's review, 21 Oct): rock cheeks at the
        # upper floor's height either side, ending a tread short of the foot, so their fronts
        # carry the face's strata down beside the stair
        r_sp = min(R, st.foot_row - st.tread)
        for c0, c1 in ((x_a, max(0, st.x0)), (min(C, st.x1), x_b)):
            if c1 > c0:
                self.Z[st.py:r_sp, c0:c1] = st.z_high
        for r0, r1, z in st.rows():
            self.Z[max(0, r0):min(R, r1), max(0, st.x0):min(C, st.x1)] = z
            self.flag[max(0, r0):min(R, r1), max(0, st.x0):min(C, st.x1)] = 1

    # ---- the contours: every rim as a closed polyline with arc length -------------------------
    def geometry(self) -> dict:
        if self._geo is None:
            self._geo = contours(self.Z, self.face_t)
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
           scree=11, figure=12, foam=13, wet=14, tree=15, soil=16)


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
        if fam_name in GREEN:
            _lawn(fr, gm, fams, hashu(seed, 12))
        elif fam_name == 'stone':
            _setts(fr, gm, fams, seed)
        else:
            _grains(fr, gm, fams, fi, hashu(seed, 16))
    # trodden path: calm patches of its siblings, a few stones; no line at its edge
    p = top & (mat == MAT_PATH)
    pf = sibs(T.get('ledge', 'path'))
    n2 = vnoise2(X, Y, 9.0 * world.s, hashu(seed, 13))
    fr.F[p] = pf[np.where(n2 < 0.3, 2, np.where(n2 > 0.75, 1, 0))[p]]
    fr.T[p] = 3
    fr.tag[p] = TAG['path']
    peb = p & (h01(hashu(seed, 14), X // 3, Y // 2) < 0.02) & ((X % 3) < 2)
    fr.T[peb] = 4
    fr.T[peb & (h01(hashu(seed, 15), X, Y) < 0.3)] = 2
    fray_path(fr, world, p, g)


def fray_path(fr: Frame, world: World, p: np.ndarray, g: np.ndarray):
    """Grass meets a path in a frayed band (eastward-edges.md 5.1): the grass reaches 0 to 2 px
    over the path's edge in 1 px steps, dark crumbs of the path lie along it, and about every
    16 px a tuft leans over the path or the path bites into the grass. No line, no dither."""
    T, seed = world.T, world.seed
    if not p.any():
        return
    X, Y = fr.X, fr.Y
    grass = g & ~p
    dist = np.zeros(fr.shape, np.int32)
    reach = grass.copy()
    for k in range(1, int(3 + 2 * world.s)):
        reach = near(reach, 1)
        dist = np.where(p & reach & (dist == 0), k, dist)
    k = np.floor((1.7 + world.s) * vnoise2(X, Y, 3.0 * world.s, hashu(seed, 17))).astype(np.int32)
    over = p & (dist > 0) & (dist <= k)
    gid = sibs(T['top'])
    fr.F[over] = gid[(h01(hashu(seed, 18), X // 2, Y // 2) * 3).astype(np.int64) % 3][over]
    fr.T[over] = 3
    fr.tag[over] = TAG['ground']
    fr.mat[over] = MAT_GROUND
    p2 = p & ~over
    crumb = p2 & (dist > 0) & (dist <= k + 2) & (h01(hashu(seed, 19), X // 2, Y) < 0.10) & (np.mod(X, 2) == 0)
    crumb = crumb | (nb(crumb, 0, -1) & p2)
    fr.T[crumb] = 1
    edge = p2 & (dist == k + 1)
    if T['top'] in GREEN:
        for x, y, hh in zip(*candidates(fr, int(16 * world.s), hashu(seed, 105), np.where(edge, 0.9, 0.0))):
            if h01(hh, 6) < 0.6:
                put_stamp(fr, TUFTS[int(hh % np.uint32(len(TUFTS)))], x, y, int(gid[int(hashu(hh, 4) % np.uint32(3))]),
                          allow=p | g, anchor=(2, 3))
            else:
                put_stamp(fr, BITE, x, y, int(sibs(T.get('ledge', 'path'))[2]), allow=g | p, anchor=(2, 1))


def _lawn(fr, mask, fams, seed):
    """A clean lawn (eastward-edges.md 5.5; Matt, 21 Oct: "one main field tone, a few large soft
    patches one tone apart, and light patches only where the light is"): the body tone over
    everything; broad soft patches of the cool sibling (hue, same value); a few large patches a
    tone darker; light pools a tone up, rare and large. No speckle and no mottle: the detail is
    the clumped tufts and flowers that dress_ground places sparsely by rule."""
    X, Y = fr.X, fr.Y
    S_ = fr.world.s
    hue = fbm2(X, Y, 64.0 * S_, hashu(seed, 3), 2) + 0.02 * (vnoise2(X, Y, 4.0 * S_, hashu(seed, 2)) - 0.5)
    fr.F[mask] = fams[np.where(hue < 0.4, 2, 0)][mask]
    n = fbm2(X, Y, 58.0 * S_, hashu(seed, 1), 2) + 0.02 * (vnoise2(X, Y, 4.0 * S_, hashu(seed, 4)) - 0.5)
    shade = mask & (n < 0.3)
    fr.T[shade] = 2
    lit = mask & (fbm2(X, Y, 90.0 * S_, hashu(seed, 5), 2) > 0.7) & ~near(fr.P['kind'] == FACEK, int(16 * S_))   # no sun under a face
    fr.T[lit] = 4
    fr.F[lit] = fams[1]


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
    swap = on & (kind < 0.8)
    alt = (fi + 1 + (hashu(seed, cx, cy, 4) & np.uint32(1)).astype(np.int64)) % 3
    fr.F[swap] = fams[alt[swap]]
    up = on & (kind >= 0.8) & (kind < 0.86)
    fr.T[up] = np.minimum(4, fr.T[up] + 1)
    fr.F[up & (h01(seed, cx, cy, 6) < warm_lit)] = fams[1]
    fr.F[up & (h01(seed, cx, cy, 6) >= 0.6)] = fams[2]
    down = on & (kind >= 0.86) & (kind < 0.94)
    fr.T[down] = np.maximum(1, fr.T[down] - 1)
    fr.F[down & (h01(seed, cx, cy, 7) < 0.5)] = fams[2]
    leaf = on & (kind >= 0.94)
    lf = sibs('leaf')
    fr.F[leaf] = lf[(hashu(seed, cx, cy, 8) % np.uint32(3)).astype(np.int64)[leaf]]
    lt = h01(seed, cx, cy, 10)
    fr.T[leaf] = np.where(lt < 0.25, 2, np.where(lt > 0.7, 4, 3))[leaf]


def _grains(fr, mask, fams, fi, seed):
    """Sand and dry ground: broad soft patches (as grass), wind ripples as short lit and
    shaded dashes lying east-west, a few sibling clusters."""
    X, Y = fr.X, fr.Y
    r = vnoise2(X, Y * 3.0, 6.0, hashu(seed, 1))
    rip = mask & (h01(seed, X // 4, Y, 2) < 0.1) & (np.mod(X, 4) < 3) & (vnoise2(X, Y, 20.0, hashu(seed, 7)) > 0.55)
    fr.T[rip & (r > 0.5)] = 4
    fr.T[rip & (r <= 0.5)] = 2
    sw = mask & ~rip & (vnoise2(X, Y, 9.0, hashu(seed, 3)) > 0.62)
    fr.F[sw] = fams[(fi[sw] + 1) % 3]
    # broad patches of a second dry family (bleached sand, packed earth), at the same tone
    pf = sibs('adobe') if fams[0] in sibs('sand') else sibs('earth')
    pt = mask & (vnoise2(X, Y, 23.0, hashu(seed, 6)) > 0.7)
    fr.F[pt] = pf[fi[pt]]
    # grit: small stones of the rock above, two px each, lit on top
    gr = mask & (h01(seed, X // 3, Y // 2, 4) < 0.025) & (np.mod(X, 3) < 2)
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


# ---- the faces: rounded lumps on absolute-height strata (the house look) ---------------------
L3 = np.array([-0.55, -0.62, 0.56])
L3 = L3 / np.sqrt((L3 ** 2).sum())


def _lamb(u, v):
    """Light on a dome at (u, v) inside a lump (u right, v down, 1 at the rim), upper left."""
    r2 = np.clip(u * u + v * v, 0, 0.98)
    return u * L3[0] + v * L3[1] + np.sqrt(1 - r2) * L3[2]


def lump_field(world: World, X, V, lid=None):
    """Which lump covers each face point, in world coordinates: X the world column, V = -z
    (the absolute height, downwards). Lumps sit on a staggered lattice (each row of cells
    shifted half a cell, so they pack like a dry-built crag), each with its own centre and
    radii by hash; where several cover a point, the lowest wins (its round crown stands in
    front of the underside of the lump above). Returns the lump id (-1: a gap), its centre and
    radii and the point's (u, v) in it. Pure function of world coordinates: seamless."""
    T, seed = world.T, world.seed
    L = dict(world.E['face']['lump'])
    # cobbles sized in world px (Matt's crops: 8 to 14 art px at 2x), never under ~8 texels
    # across, so a cobble still holds a lit top-left, a body and a shade at 1x
    g = max(world.s, 2.0) if world.E['face'].get('world_lumps') else 1 + world.E['face'].get('grow', 0.25) * (world.s - 1)
    L.update(cw=L['cw'] * g, ch=L['ch'] * g, rx=(L['rx'][0] * g, L['rx'][1] * g), ry=(L['ry'][0] * g, L['ry'][1] * g))
    if L.get('fill'):
        F_ = dict(L['fill'])
        F_.update(cw=F_['cw'] * g, ch=F_['ch'] * g, rx=(F_['rx'][0] * g, F_['rx'][1] * g), ry=(F_['ry'][0] * g, F_['ry'][1] * g))
        L['fill'] = F_
    cw, ch, p = L['cw'], L['ch'], L['p']
    X = np.asarray(X, np.float64)
    V = np.asarray(V, np.float64)
    j0 = np.floor(V / ch).astype(np.int64)
    best = np.full(X.shape, -1e9)
    out = dict(id=np.full(X.shape, -1, np.int64), cx=np.zeros(X.shape), cv=np.zeros(X.shape),
               rx=np.ones(X.shape), ry=np.ones(X.shape), u=np.zeros(X.shape), v=np.zeros(X.shape))
    wob = 0.07 * (vnoise2(X, V, 2.5, hashu(seed, 501)) - 0.5)
    for dj in (-1, 0, 1):
        j = j0 + dj
        shift = 0.5 * (j % 2)
        i0 = np.floor(X / cw - shift).astype(np.int64)
        for di in (-1, 0, 1, 2):
            i = i0 + di - 1
            hh = hashu(seed, i, j, 502)
            cx = (i + shift + 0.12 + 0.76 * h01(hh, 1)) * cw
            cv = (j + 0.15 + 0.7 * h01(hh, 2)) * ch
            bigf = np.where(h01(hh, 9) < world.E['face'].get('big', 0.0), world.E['face'].get('big_f', 1.45), 1.0)   # the odd boulder
            asp = 1.0 + world.E['face'].get('aspect', 0.0) * (2 * h01(hh, 10) - 1)            # some flat, some tall
            rx = (L['rx'][0] + (L['rx'][1] - L['rx'][0]) * h01(hh, 3)) * bigf * asp
            ry = (L['ry'][0] + (L['ry'][1] - L['ry'][0]) * h01(hh, 4)) * bigf / asp
            u = (X + 0.5 - cx) / rx
            v = (V + 0.5 - cv) / ry
            dd = (np.abs(u) ** p + np.abs(v) ** p) ** (1.0 / p) + wob
            take = (dd <= 1.0) & (cv > best)
            best = np.where(take, cv, best)
            lid_ = hashu(hh, 7).astype(np.int64)
            for k, val in (('id', lid_), ('cx', cx), ('cv', cv), ('rx', rx), ('ry', ry), ('u', u), ('v', v)):
                out[k] = np.where(take, val, out[k])
    # small stones wedged in the gaps the big ones leave (a dry-built crag is packed)
    fill = L.get('fill')
    if fill:
        fw, fh = fill['cw'], fill['ch']
        gapm = out['id'] < 0
        fbest = np.full(X.shape, -1e9)
        fj0 = np.floor(V / fh).astype(np.int64)
        for dj in (-1, 0, 1):
            j = fj0 + dj
            i0 = np.floor(X / fw).astype(np.int64)
            for di in (-1, 0, 1):
                i = i0 + di
                hh = hashu(seed, i, j, 503)
                cx = (i + 0.2 + 0.6 * h01(hh, 1)) * fw
                cv = (j + 0.2 + 0.6 * h01(hh, 2)) * fh
                rx = fill['rx'][0] + (fill['rx'][1] - fill['rx'][0]) * h01(hh, 3)
                ry = fill['ry'][0] + (fill['ry'][1] - fill['ry'][0]) * h01(hh, 4)
                u = (X + 0.5 - cx) / rx
                v = (V + 0.5 - cv) / ry
                dd = (np.abs(u) ** p + np.abs(v) ** p) ** (1.0 / p) + wob
                take = gapm & (dd <= 1.0) & (cv > fbest)
                fbest = np.where(take, cv, fbest)
                lid_ = hashu(hh, 8).astype(np.int64)
                for k, val in (('id', lid_), ('cx', cx), ('cv', cv), ('rx', rx), ('ry', ry), ('u', u), ('v', v)):
                    out[k] = np.where(take, val, out[k])
    return out


def paint_faces(fr: Frame, P: dict, world: World):
    """A natural face (eastward-edges.md 2): rounded lumps (or flat slabs) in the rock's ramp,
    each shaded as a dome lit from the upper left with hard steps, cut into a few facets, a
    crevice (tone 0) on its upper left where it meets the lump behind and an underside (tone 1)
    on its lower right; gaps between lumps are deep recesses; sibling clusters, lichen on lit
    crowns, moss caps now and then. The under-lip line and shade, the horizontal streaks under
    it and the dark foot are the rim's and the foot's (paint_rims, foot_band)."""
    T, seed = world.T, world.seed
    if T['built']:
        return paint_courses(fr, P, world)
    if world.E['face']['style'] == 'earth':
        return paint_earth(fr, P, world)
    if world.E['face']['style'] == 'cobbles':
        return paint_cobbles(fr, P, world)
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
    zc = h - d + 0.5
    V = -zc
    F = lump_field(world, X, V)
    mid, u, v = F['id'], F['u'], F['v']
    rr = np.sqrt(u * u + v * v)
    # facets: the nearest of a jittered 5 px lattice in world coordinates, toned by the light
    # at the facet's own centre, so a lump reads as broken rock, its rim kept round
    fi, fj = np.floor(X / 6.0).astype(np.int64), np.floor(V / 6.0).astype(np.int64)
    fbest = np.full(X.shape, 1e9)
    fid = np.zeros(X.shape, np.int64)
    fx = np.zeros(X.shape)
    fv = np.zeros(X.shape)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            a, b = fi + di, fj + dj
            px = (a + 0.1 + 0.8 * h01(seed, a, b, 511)) * 6.0
            pv = (b + 0.1 + 0.8 * h01(seed, a, b, 512)) * 6.0
            dd = (X + 0.5 - px) ** 2 + 1.4 * (V + 0.5 - pv) ** 2
            bt = dd < fbest
            fbest = np.where(bt, dd, fbest)
            fid = np.where(bt, hashu(seed, a, b, 513).astype(np.int64), fid)
            fx, fv = np.where(bt, px, fx), np.where(bt, pv, fv)
    lam_px = _lamb(u, v)
    lf = _lamb((fx - F['cx']) / F['rx'] * 1.15, (fv - F['cv']) / F['ry'] * 1.15)
    lam = np.where(rr > 0.86, lam_px, 0.8 * lf + 0.2 * lam_px)
    lam = lam + 0.06 * np.clip(-nx * 2.5, -2, 1)
    t = np.where(lam > 0.74, 4, np.where(lam < 0.24, 1, np.where(lam < 0.5, 2, 3)))
    big = np.minimum(F['rx'], F['ry']) > 5.5
    t = np.where(big & (lam > 0.93) & (rr > 0.5), 5, t)
    t = np.where(h01(mid, 21) < 0.1, t - 1, t)                   # the odd lump set back
    # the screen grid, for neighbours
    shp = fr.shape
    MID = np.full(shp, -2, np.int64)
    MID[yy, xx] = mid
    FID_ = np.full(shp, -2, np.int64)
    FID_[yy, xx] = fid
    gap = mid < 0
    up_d = (nb(MID, -1, 0) != MID)[yy, xx]
    lf_d = (nb(MID, 0, -1) != MID)[yy, xx]
    dn_d = (nb(MID, 1, 0) != MID)[yy, xx]
    rt_d = (nb(MID, 0, 1) != MID)[yy, xx]
    crev = ~gap & up_d
    under = ~gap & ~crev & (dn_d | rt_d)
    # facet joints: a crack on the lower-right side of a joint, a lit lip over it
    fj_ = ~gap & ~crev & (((nb(FID_, -1, 0) != FID_) & (nb(MID, -1, 0) == MID)) |
                          ((nb(FID_, 0, -1) != FID_) & (nb(MID, 0, -1) == MID)))[yy, xx]
    crack = fj_ & (vnoise2(X, V, 2.0, hashu(seed, 514)) > 0.55)
    CR = np.zeros(shp, bool)
    CR[yy, xx] = crack
    lipc = (nb(CR, 1, 0)[yy, xx]) & ~crack & ~gap & (lam > 0.55)
    t = np.where(crack, t - 1, t)
    t = np.where(lipc, t + 1, t)
    # skin: sibling swaps in dominoes, a few lit flecks and pits
    cell = hashu(seed, np.floor(X / 2).astype(np.int64), np.floor(V).astype(np.int64), 515)
    kind = h01(cell, 1)
    edge_any = up_d | lf_d | dn_d | rt_d
    swap = ~gap & ~edge_any & (kind < 0.05)
    fleck = ~gap & ~edge_any & (kind >= 0.05) & (kind < 0.07) & (lam > 0.6)
    pit = ~gap & ~edge_any & (kind >= 0.07) & (kind < 0.09) & (lam < 0.8)
    t = np.where(fleck, t + 1, np.where(pit, t - 1, t))
    t = np.clip(t, 1, 5)
    t = np.where(under & (t > 2), t - 1, t)
    t = np.where(crev | gap, 0, t)
    # families: the band at the lump's centre (absolute height), a sibling per lump
    bounds, bfams, _btex = band_table(T, world.s)
    period = bounds[-1]
    zb = np.mod(-F['cv'], period)
    band = np.clip(np.searchsorted(bounds, zb, 'right') - 1, 0, len(bfams) - 1)
    base_ids, bias = [], []
    for name in bfams:
        b_, p_ = _sib_of(name)
        base_ids.append(sibs(b_))
        bias.append(np.cumsum(p_))
    base_ids, bias = np.array(base_ids), np.array(bias)
    r = h01(mid, 22)
    si = (r > bias[band, 0]).astype(np.int64) + (r > bias[band, 1]).astype(np.int64)
    si = np.where(swap, (si + 1 + (h01(cell, 2) < 0.5)) % 3, si)
    fam = base_ids[band, si]
    fam = np.where(crev | gap, base_ids[band, 2], fam)
    # lichen crusts on lit crowns, damp stains on the shaded undersides (clusters)
    lich = ~gap & ~edge_any & (lam > 0.72) & (h01(seed, np.floor(X / 3).astype(np.int64), np.floor(V / 2).astype(np.int64), 516) < 0.015)
    fam = np.where(lich, np.where(h01(cell, 3) < 0.5, FID['grass_cool'], FID['earth_warm']), fam)
    t = np.where(lich, np.clip(t, 2, 4), t)
    # damp stains on the shaded undersides (clusters of the earth's cool sibling)
    damp = ~gap & ~crev & (lam < 0.45) & (v > 0.2) & (h01(seed, np.floor(X / 2).astype(np.int64), np.floor(V / 2).astype(np.int64), 517) < 0.03)
    fam = np.where(damp, FID['earth_cool'], fam)
    t = np.where(damp, np.clip(t, 1, 3), t)
    # moss caps on the crowns of a few lumps
    if T['top'] in GREEN:
        cap = ~gap & ~crev & (h01(mid, 23) < world.E['face'].get('moss_caps', 0.0)) & (v < -0.6 - 0.12 * (h01(cell, 4) > 0.5)) & (np.abs(u) < 0.62)
        fam = np.where(cap, FID['leaf'], fam)
        t = np.where(cap, np.where(lam > 0.78, 4, 3), t)
    fr.F[yy, xx] = fam
    fr.T[yy, xx] = t
    fr.tag[yy, xx] = np.where(gap | crev, TAG['recess'], TAG['rock'])
    MIDs = np.full(shp, -1, np.int64)
    MIDs[yy, xx] = np.where(gap, -1, mid)
    fr.MID = MIDs
    ce = (1 - np.minimum(rr, 1)) * np.minimum(F['rx'], F['ry'])
    fr.face = dict(yy=yy, xx=xx, s=s, lid=lid, d=d, Hf=Hf, h=h, zc=zc, u=(u + 1) / 2, rec=gap | crev, mass=mid,
                   k=np.where(gap, -1, mid), crack=crack, ce=ce, Wm=2 * F['rx'], nx=nx)


def paint_cobbles(fr: Frame, P: dict, world: World):
    """The highland face as Matt chose it (21 Oct 11:44: "i like the rocks on the cliff face";
    Eastward's crag inside its grid outline): rounded cobbles packed in the crag, each a soft
    dome lit from the upper left in a few calm steps, the light catching its top-left, a dark
    seam only where one cobble meets the next above or behind it (no outline round every
    stone), the odd larger boulder; warm ochre on the lit tops, the crag's body in the middle
    tones, violet-grey stone in the shade (so it reads as stone, not potatoes)."""
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
    sarc = G['arc'][py, xw].copy()
    lid = G['loop'][py, xw].copy()
    nx = G['nx'][py, xw]
    bad = np.isnan(sarc)
    sarc[bad] = X[bad]
    lid[bad] = -1
    zc = h - d + 0.5
    F = lump_field(world, X, -zc)
    mid, u, v = F['id'], F['u'], F['v']
    gap = mid < 0
    rr = np.sqrt(u * u + v * v)
    lam = _lamb(u, v) + 0.05 * np.clip(-nx * 2.5, -2, 1)
    t = np.where(lam > 0.74, 4, np.where(lam > 0.38, 3, 2))          # three calm steps a cobble
    t = np.where((h01(mid, 21) < 0.12) & (t > 2), t - 1, t)          # the odd cobble set back
    shp = fr.shape
    MID = np.full(shp, -2, np.int64)
    MID[yy, xx] = mid
    up_d = (nb(MID, -1, 0) != MID)[yy, xx]
    seam = ~gap & up_d                                                # where it meets the cobble above
    t = np.where(seam, 0, t)
    t = np.where(gap, 0, t)
    rec = gap | seam
    # families: warm where the light falls, the crag in the middle, violet-grey stone in shade
    rid = sibs(T['rock'])
    shf = sibs(world.E['face'].get('shade', T['rock']))
    fam = np.where(t >= 4, rid[1], np.where(t == 3, rid[np.where(h01(mid, 22) < 0.6, 2, 0)], np.where(t == 2, shf[0], shf[2])))
    fam = np.where(rec, shf[2], fam)
    t = np.where((t == 2) & ~rec, 1, t)      # the violet-grey shade a value below the crag's body (stone 1 is darker than crag 3)
    if T['top'] in GREEN:
        cap = ~rec & (h01(mid, 23) < world.E['face'].get('moss_caps', 0.0)) & (v < -0.62) & (np.abs(u) < 0.6)
        fam = np.where(cap, FID['leaf'], fam)
        t = np.where(cap, np.where(lam > 0.7, 4, 3), t)
    fr.F[yy, xx] = fam
    fr.T[yy, xx] = np.clip(t, 0, 5)
    fr.tag[yy, xx] = np.where(rec, TAG['recess'], TAG['rock'])
    MIDs = np.full(shp, -1, np.int64)
    MIDs[yy, xx] = np.where(rec, -1, mid)
    fr.MID = MIDs
    ce = (1 - np.minimum(rr, 1)) * np.minimum(F['rx'], F['ry'])
    fr.face = dict(yy=yy, xx=xx, s=sarc, lid=lid, d=d, Hf=Hf, h=h, zc=zc, u=(u + 1) / 2, rec=rec, mass=mid,
                   k=np.where(rec, -1, mid), crack=np.zeros(X.shape, bool), ce=ce, Wm=2 * F['rx'], nx=nx)


def paint_earth(fr: Frame, P: dict, world: World):
    """The meadow's own face: a low earthy turf bank (the meadow edge set). Soil in thin layers
    fixed in absolute height (each layer's top row a tone down, so the layers read), small
    rounded clods lit on their top left with a soft underside (no deep crevices: soil is not
    rock), the odd field stone, and pale roots hanging from the sod, each with its shadow."""
    T, seed = world.T, world.seed
    K = P['kind']
    sel = (K == FACEK) & (P['ST'] == 0)
    yy, xx = np.nonzero(sel)
    if not len(yy):
        return
    G = world.geometry()
    X = fr.X[yy, xx]
    xw = np.clip(X, 0, world.width - 1)
    py = P['PY'][yy, xx]
    h, h2, d = P['ZH'][yy, xx], P['Z2'][yy, xx], P['D'][yy, xx].astype(np.float64)
    Hf = (h - h2).astype(np.float64)
    s = G['arc'][py, xw].copy()
    lid = G['loop'][py, xw].copy()
    s[np.isnan(s)] = X[np.isnan(s)]
    zc = h - d + 0.5
    V = -zc
    bounds, bfams, btex = band_table(T, world.s)
    S_ = world.s
    Xw = np.floor(X / S_).astype(np.int64)          # world columns: marks are S_ texels wide (no lone px at 2x)
    zw = zc / S_
    dw = d / S_
    zb = np.mod(zc + 0.8 * S_ * (2 * vnoise1(X, 11.0 * S_, hashu(seed, 601)) - 1), bounds[-1])
    band = np.clip(np.searchsorted(bounds, zb, 'right') - 1, 0, len(bfams) - 1)
    ids = np.array([sibs(hp.family(n)) for n in bfams])
    sib = np.array([{'': 0, '_warm': 1, '_cool': 2}[n[len(hp.family(n)):]] for n in bfams])
    fam = ids[band, sib[band]]
    t = np.full(X.shape, 3)
    parting = (zb - bounds[band] > bounds[band + 1] - bounds[band] - S_) & (vnoise1(X, 5.0 * S_, hashu(seed, 602)) > 0.3)
    t = np.where(parting, 2, t)
    F = lump_field(world, X, V)
    mid, u, v = F['id'], F['u'], F['v']
    inl = mid >= 0
    lam = _lamb(u, v)
    ct = np.where(lam > 0.66, 4, np.where(lam < 0.36, 2, 3))
    t = np.where(inl & (h01(mid, 31) < 0.88), ct, t)
    fam = np.where(inl & (lam > 0.66), ids[band, 1], fam)
    shp = fr.shape
    MID = np.full(shp, -2, np.int64)
    MID[yy, xx] = mid
    upl = ((nb(MID, -1, 0) != MID) | (nb(MID, 0, -1) != MID))[yy, xx] & inl
    dnr = ((nb(MID, 1, 0) != MID) | (nb(MID, 0, 1) != MID))[yy, xx] & inl & ~upl
    t = np.where(upl, 1, t)                                      # a crack over each clod
    t = np.where(dnr & (h01(mid, 31) < 0.88), 2, t)
    sw = inl & (h01(mid, 32) < 0.35)
    fam = np.where(sw, ids[band, (sib[band] + 1 + (h01(mid, 33) < 0.5)) % 3], fam)
    # the odd field stone, 3 x 2, lit on its top left
    gx, gz = np.floor(Xw / 10).astype(np.int64), np.floor(zw / 7).astype(np.int64)
    stn = h01(seed, gx, gz, 603) < 0.16
    sw_ = 3 + (h01(seed, gx, gz, 605) * 3).astype(np.int64)
    ox = (h01(seed, gx, gz, 604) * (10 - sw_)).astype(np.int64)
    sx_ = Xw - gx * 10 - ox
    sz_ = zw - gz * 7 - 2
    st_m = stn & (sx_ >= 0) & (sx_ < sw_) & (sz_ >= 0) & (sz_ < 3) & ~(((sx_ == 0) | (sx_ == sw_ - 1)) & ((sz_ < 1) | (sz_ >= 2)))
    fam = np.where(st_m, FID[T['loose']], fam)
    t = np.where(st_m, np.where((sz_ >= 2) & (sx_ <= 1), 4, np.where(sz_ < 1, 2, 3)), t)
    # roots: pale threads hanging 2 to 8 px from the sod, wandering a pixel, a shadow to the right
    root = np.zeros(X.shape, bool)
    rsh = np.zeros(X.shape, bool)
    for dx in range(-2, 3):
        cx = Xw - dx
        on = h01(seed, cx, 605) < world.E['face']['roots']
        Lr = 3 + 4 * h01(seed, cx, 606)
        wig = np.round(1.1 * np.sin(dw / 2.4 + 6.28 * h01(seed, cx, 607))).astype(np.int64)
        hit = on & (dw >= 2) & (dw <= Lr) & (dx == wig)
        root |= hit
        rsh |= on & (dw >= 2) & (dw <= Lr) & (dx == wig + 1)
    rsh &= ~root
    fam = np.where(root, FID['earth_warm'], fam)
    t = np.where(root, 5, np.where(rsh, np.maximum(1, t - 1), t))
    # the lower part of a bank is damp: a tone down in its last third
    t = np.where(d > Hf * 0.7, np.maximum(1, t - 1), t)
    t = np.clip(t, 1, 5)
    fr.F[yy, xx] = fam
    fr.T[yy, xx] = t
    fr.tag[yy, xx] = np.where(root, TAG['leaf'], TAG['soil'])
    MIDs = np.full(shp, -1, np.int64)
    MIDs[yy, xx] = np.where(inl, mid, -1)
    fr.MID = MIDs
    fr.face = dict(yy=yy, xx=xx, s=s, lid=lid, d=d, Hf=Hf, h=h, zc=zc, u=(u + 1) / 2, rec=np.zeros(X.shape, bool),
                   mass=mid, k=np.where(inl, mid, -1), crack=np.zeros(X.shape, bool), ce=np.zeros(X.shape),
                   Wm=2 * F['rx'], nx=G['nx'][py, xw])


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
    bounds, bfams, _tex = band_table(T, world.s)
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
    MIDs = np.full(fr.shape, -1, np.int64)
    MIDs[yy, xx] = np.where(joint, -1, blk.astype(np.int64))
    fr.MID = MIDs
    fr.face = dict(yy=yy, xx=xx, s=s, lid=lid, d=d, Hf=Hf, h=h, zc=zc, u=u, rec=joint, mass=blk, k=bk,
                   crack=joint & (zr >= 1.0), ce=ce, Wm=br - bl, nx=G['nx'][py, xw])


# ---- side bands: the narrow rock strip where a top's edge runs north-south --------------------
SIDE = 3        # eastward-edges.md 3.3: a 3 px band at our scale


def side_maps(world: World):  # noqa: C901
    """Per plan pixel: how far (1..SIDE) the nearest lower ground lies to the west and to the
    east in the same plan row, and whether the ground just south is not lower (so the edge
    there runs north-south and a side band shows, rather than a south face)."""
    if getattr(world, '_side', None) is None:
        Z = world.Z
        R, C = Z.shape
        SD = world.M['side']
        big = np.pad(Z, ((0, 3), (SD, SD)), mode='edge')
        dw = np.zeros(Z.shape, np.int8)
        de = np.zeros(Z.shape, np.int8)
        for k in range(SD, 0, -1):
            dw = np.where(big[:R, SD - k:SD - k + C] < Z, k, dw)
            de = np.where(big[:R, SD + k:SD + k + C] < Z, k, de)
        south_ok = np.ones(Z.shape, bool)
        for k in (1, 2):
            south_ok &= big[k:R + k, SD:SD + C] >= Z
        world._side = (dw, de, south_ok)
    return world._side


def paint_sides(fr: Frame, P: dict, world: World):
    """Side bands (eastward-edges.md 3.3): two px of rock on the outside, lit (4, 3) facing
    west and dark (2, 1) facing east, then the darkest line in the picture between the band and
    the top (the rock's edge tone, broken every few px), and the top's lip row darker beside it."""
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
    bounds, bfams, _ = band_table(T, world.s)
    ids = np.array([sibs(hp.family(n)) for n in bfams])
    for m, dist, lit in ((west, a, True), (east, b, False)):
        if not m.any():
            continue
        z = P['ZH'] - 2 * dist
        band = np.clip(np.searchsorted(bounds, np.mod(z, bounds[-1]), 'right') - 1, 0, len(bfams) - 1)
        lump = np.floor((fr.Y + 3 * (h01(seed, xw, 61) > 0.5)) / 5).astype(np.int64)
        lh = hashu(seed, xw // 3, lump, 62)
        fam = ids[band, np.minimum((h01(lh, 1) * 3).astype(np.int64), 2)]
        rowin = np.mod(fr.Y + (h01(seed, xw // 3, 63) * 5).astype(np.int64), 5)
        if lit:
            t = np.where(dist == 1, np.where(rowin == 4, 3, 4), np.where(rowin == 4, 2, 3))
        else:
            t = np.where(dist == 1, np.where(rowin == 0, 2, 1), 1)
        line = dist == world.M['side']
        brk = h01(hashu(seed, 64), fr.X, fr.Y // 3) < 0.22
        t = np.where(line, np.where(brk, 1, EDGE), t)
        fr.F[m] = fam[m]
        fr.T[m] = t[m]
        fr.tag[m] = TAG['side']
    fr.side_w, fr.side_e = west, east
    # the top's lip row runs down the side too: a darker row of the top's own ground
    beside = top & ~(west | east) & (nb(west | east, 0, -1) | nb(west | east, 0, 1)) & (fr.mat == MAT_GROUND)
    fr.T[beside] = np.minimum(fr.T[beside], 2)


# ---- rims: the lip, the dark line and shade under it, the streaks, the foot ----------------------
def lip_overhang(world: World, X, kind: str):
    """How far the lip hangs over the face at each column, in texels (eastward-edges.md 3.1, the
    shared rule: a one-texel wobble in runs of 1 to 10): the biome's turf or crumble 0 to its
    `lip` measure, the meadow's sod swelling and thinning in scallops, a snow cornice in rounded
    lobes, a built coping fixed. Sizes come from `measures` at the render's density."""
    M = world.M
    lo, hi = M['lip']
    if kind == 'coping':
        return np.full(np.shape(X), hi)
    if kind == 'cornice':      # a wind-built cornice: rounded lobes
        n = vnoise1(X, 7.0 * world.s, hashu(world.seed, 72))
        return np.round(max(2, hi) * (1 + 1.5 * n * n)).astype(np.int64)
    if kind == 'sod':          # a soft sod: its overhang swells and thins in rounded scallops
        n = vnoise1(X, M['lip_run'], hashu(world.seed, 73)) * 0.75 + 0.25 * vnoise1(X, 2.2, hashu(world.seed, 74))
        return np.round(lo + (hi - lo) * n).astype(np.int64)
    # turf and crumble (Matt, 21 Oct: the lip's light grass 1 px, no teeth): the overhang is 0
    # or 1 texel at any density, in long soft runs
    w = vnoise1(X, M['lip_run'] * 2.0, hashu(world.seed, 71)) > 0.5
    return np.where(w, min(1, hi), 0).astype(np.int64)


def paint_rims(fr: Frame, P: dict, world: World):
    """The rim in Eastward's value structure (eastward-edges.md 2.2 and 3.1), in the biome's
    own ramps: on the top, a row of its ground a step darker at the edge with a broken lit row
    two rows behind; over the face, the lip hanging 0 or 1 px (no teeth, no blades); then the
    rim line (tone 1), the darkest line (0), a shade of two or three rows stepping back up, a
    zone of short horizontal streaks, and at the bottom a dark foot band with a pebble or two."""
    T, seed = world.T, world.seed
    K = P['kind']
    face = (K == FACEK) & (P['ST'] == 0)
    top = (K == TOP)
    edge_row = top & nb(face, 1, 0) & (fr.tag != TAG['side'])
    E_ = world.E
    lit_row = top & nb(edge_row, 2, 0) & ~edge_row & (fr.tag != TAG['side']) & (vnoise1(fr.X, 9.0 * world.s, hashu(seed, 81)) < E_['lip']['lit_row'])
    for m, mat_ok in ((lit_row, (fr.mat == MAT_GROUND) | (fr.mat == MAT_PATH)),):
        mm = m & mat_ok
        fr.T[mm] = np.maximum(fr.T[mm], 4)
    sn = edge_row & (fr.mat == MAT_SNOW)
    fr.T[sn] = 5
    if not hasattr(fr, 'face'):
        return
    f = fr.face
    yy, xx = f['yy'], f['xx']
    py = P['PY'][yy, xx]
    X = fr.X[yy, xx]
    xw = np.clip(X, 0, world.width - 1)
    mat = top_material(world, py, xw, f['h'])
    lipk = E_['lip']['kind']
    L = np.where(mat == MAT_SNOW, lip_overhang(world, X, 'cornice'), lip_overhang(world, X, lipk))
    L = np.where(mat == MAT_WATER, 0, L)
    d = f['d']
    # the edge row of the top, where nothing hangs over
    E = np.zeros(fr.shape, bool)
    E[yy[(d == 1) & (L == 0)], xx[(d == 1) & (L == 0)]] = True
    E = nb(E, 1, 0) & edge_row & ((fr.mat == MAT_GROUND) | (fr.mat == MAT_PATH))
    fr.T[E] = np.minimum(fr.T[E], 2)
    # the overhang
    on = d <= L
    topf = sibs(T['top'])
    lip_fam = np.where(mat == MAT_SNOW, FID['snow'],
                       np.where(mat == MAT_PATH, sibs(T.get('ledge', 'path'))[0], topf[(h01(seed, np.floor(X / 7).astype(np.int64), 74) * 3).astype(np.int64) % 3]))
    if lipk == 'coping':
        ids = sibs(T['rock'])
        jt = np.mod(X + 5 * h01(seed, f['lid'], 75), 13.0) < 1.0
        tl = np.where(d == 1, 4, np.where(d == 2, 3, 1))
        tl = np.where(jt & (d > 1), 1, tl)
        lip_fam = ids[(h01(seed, f['lid'], np.floor((X + 5) / 13).astype(np.int64), 76) * 3).astype(np.int64) % 3]
    elif lipk == 'sod':
        # a soft sod overhang: grass at body tone, its underside a dark row of the cool sibling
        tl = np.where(mat == MAT_SNOW, np.where(d >= L, 2, np.where(d == 1, 4, 3)), np.where(d >= L, 1, np.where((d == 1) & (L >= 2), 4, 3)))
        lip_fam = np.where((d >= L) & (mat == MAT_GROUND), topf[2], lip_fam)
    else:
        tl = np.where(mat == MAT_SNOW, np.where(d >= L, 2, np.where(d == 1, 4, 3)), 2)
    lip_fam = np.broadcast_to(lip_fam, on.shape)
    fr.F[yy[on], xx[on]] = lip_fam[on]
    fr.T[yy[on], xx[on]] = tl[on] if np.ndim(tl) else tl
    fr.tag[yy[on], xx[on]] = TAG['fringe']
    rock = ~on & np.isin(fr.tag[yy, xx], (TAG['rock'], TAG['recess'], TAG['soil']))
    q = d - L                                        # rows below the lip
    big = f['Hf'] >= 48 * world.s
    sh = np.where(big, world.M['shade'][1], world.M['shade'][0])
    zs = np.where(big, world.M['streaks'][1], world.M['streaks'][0])
    cur = fr.T[yy, xx]
    t = cur.copy()
    ul = E_['lip']['under'][0] > 0
    t = np.where(rock & (q == 1) & ul, np.minimum(cur, 1), t)                    # rim line
    t = np.where(rock & (q == 2) & ul, 0, t)                                     # darkest line
    t = np.where(rock & (q <= 2) & ~ul, np.maximum(0, cur - 3 + q), t)          # under a sod: its shade, 2 then 1
    t = np.where(rock & (q >= 3) & (q < 3 + sh), np.maximum(0, cur - np.where(q < 3 + sh - 1, 2, 1)), t)
    # the streak zone: short horizontal dashes (4 px) a tone down, a lit pixel row over some
    qz = q - 3 - sh
    off = (h01(seed, np.floor(f['zc']).astype(np.int64), 77) * 5).astype(np.int64)
    qx = X + off
    dash = rock & (qz >= 0) & (qz < zs) & (h01(seed, qx // 5, np.floor(f['zc']).astype(np.int64), 78) < 0.16) & (np.mod(qx, 5) < 4)
    t = np.where(dash, np.maximum(1, cur - 1), t)
    # the foot band (3.2): the last rows dark, the very last darkest, a pebble now and then
    Hf = f['Hf']
    foot = rock & (d > Hf - world.M['foot'])
    t = np.where(foot & (d >= Hf), np.minimum(t, 1), np.where(foot, np.maximum(0, t - 1), t))
    peb = foot & (d < Hf) & (h01(seed, X // 3, np.floor(f['zc']).astype(np.int64), 79) < E_['foot']['pebbles']) & (np.mod(X, 3) < 2)
    t = np.where(peb, 3, t)
    nonedge = t != EDGE
    fr.T[yy[nonedge], xx[nonedge]] = t[nonedge]
    pb = peb & nonedge
    fr.F[yy[pb], xx[pb]] = sibs(T['loose'])[1]
    fr.fringeL = L
    fr.rim_mat = mat


# ---- cast shadows on the lower ground ------------------------------------------------------
def paint_shadows(fr: Frame, P: dict, world: World, steps: int = 2):
    """Under a face the foot band is the shadow (eastward-edges.md 7.2): the ground's first row
    one tone down, the next one broken. An east-facing side band throws its shadow east: the
    core two tones down for 2 or 3 px, its rim one tone down for 2 more (the nearest the ramp
    comes to Eastward's soft edge). On the ground's own ramp (house-style 6)."""
    K = P['kind']
    ground = (K == TOP) & np.isin(fr.tag, (TAG['ground'], TAG['path'], TAG['snow']))
    face = (K == FACEK) & (P['ST'] == 0)
    c1 = ground & nb(face, -1, 0)
    c2 = ground & nb(c1, -1, 0) & ~c1 & (vnoise1(fr.X, 3.0, hashu(world.seed, 93)) > 0.45)
    fr.T[c1] = np.maximum(0, fr.T[c1] - 1)
    fr.T[c2] = np.maximum(0, fr.T[c2] - 1)
    east = getattr(fr, 'side_e', np.zeros(fr.shape, bool))
    core = world.M['shadow']
    rim = max(2, core // 2 + 1)
    de = np.zeros(fr.shape, np.int32)
    for k in range(core + rim + 1, 0, -1):
        de = np.where(nb(east, 0, -k), k, de)
    w1 = core - 1 + (vnoise1(fr.Y, 5.0 * world.s, hashu(world.seed, 91)) > 0.5)
    s2 = ground & (de > 0) & (de <= w1)
    s1 = ground & (de > w1) & (de <= w1 + rim)
    fr.T[s2] = np.maximum(0, fr.T[s2] - steps)
    fr.T[s1] = np.maximum(0, fr.T[s1] - 1)


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
MARGIN = 48      # every neighbourhood rule reaches less than this (x density), so windows agree
ADULT_PX = 25    # our adult at density 1 (size-guide.md)


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
    mg = int(MARGIN * world.s)
    fx0, fy0, fx1, fy1 = max(0, x0 - mg), max(0, y0 - mg), min(W, x1 + mg), min(H, y1 + mg)
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
        paint_decals(fr, world)
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
    top_w = int(round(world.top / world.s))
    Z = world.Zw[top_w:, :]
    R, C = Z.shape
    cells = Z[: R - R % cell, : C - C % cell].reshape(R // cell, cell, C // cell, cell)
    plan = np.round(np.median(cells, axis=(1, 3)) / world.T['face']).astype(int)
    return from_plan(plan, world.T['face'])


# ---- stamps: small hand-drawn shapes, placed on world candidates -------------------------------
def stamp(rows):
    """Rows of characters: '.' empty, '0' to '5' a tone, 'e' the family's edge tone."""
    return [(y, x, EDGE if ch == 'e' else int(ch)) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch != '.']


CLUMPS = [stamp(['..4...4.', '.443.44.', '.3343432', '22333322', '.222222.']),
          stamp(['.4..4..', '4434.4.', '3343343', '2233322', '.2222..']),
          stamp(['...4..', '.4.44.', '443343', '233332', '.2222.']),
          stamp(['.4....4..', '443..443.', '3343.3343', '223322332', '.22222222'])]
TUFTS = [stamp(['.4..4', '34.43', '.233.', '..2..']), stamp(['4.4', '343', '22.']),
         stamp(['..4.', '.44.', '4332', '.22.']), stamp(['4..', '34.', '.32', '..2']),
         stamp(['.4', '43', '32']), stamp(['5.4..', '44.4.', '.343.', '.222.'])]
CLOVER = [stamp(['.44.', '4433', '.32.']), stamp(['44', '32']), stamp(['.44', '443', '32.'])]
FLOWER = [stamp(['55', '43']), stamp(['.5.', '554', '.3.']), stamp(['55.', '453', '.3.'])]
MOUND = [stamp(['..4444..', '.444433.', '43333322', '32222221', '.111111.']),
         stamp(['.4443.', '443332', '322221', '.1111.'])]
BITE = stamp(['.33.', '3333', '.22.'])
REED = [stamp(['4..', '4.4', '343', '343', '232', '22.']), stamp(['.4.', '34.', '344', '233', '22.']), stamp(['4.', '43', '34', '23', '22'])]
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
    if T['top'] not in GREEN:
        return dress_dry(fr, world)
    if not T.get('dress', True):
        return      # the screen dresses its own ground (scripts/art/native: the biome's plant set)
    g = (fr.tag == TAG['ground']) & np.isin(fr.F, sibs(T['top']))
    edge = near(~g & (fr.P['kind'] > 0), 5) & g
    gid = sibs(T['top'])
    # clumps of grass, 5 to 9 px, sparse in the open and a little thicker at edges
    for x, y, hh in zip(*candidates(fr, int(11 * world.s), hashu(seed, 101), np.where(edge, 0.62, 0.5))):
        st = CLUMPS[int(hh % np.uint32(len(CLUMPS)))]
        f = int(gid[int(hashu(hh, 4) % np.uint32(3))])
        put_stamp(fr, st, x, y, f, allow=g, anchor=(4, 4))
    for x, y, hh in zip(*candidates(fr, int(36 * world.s), hashu(seed, 103), 0.12)):
        put_stamp(fr, MOUND[int(hh % np.uint32(2))], x, y, int(gid[2]), allow=g, anchor=(3, 2))
    # flowers in patches: one kind to a clump, eight to fourteen heads round a centre
    fl = [FID['plaster'], FID['brass'], FID['dusk'], FID['berry'], FID['sky']]
    for x, y, hh in zip(*candidates(fr, int(56 * world.s), hashu(seed, 104), min(0.8, T['flowers'] * 7))):
        f = fl[int(hashu(hh, 5) % np.uint32(len(fl)))]
        for j in range(8 + int(hashu(hh, 6) % np.uint32(7))):
            ox = int(round((h01(hh, 7, j) * 2 - 1) * 6 * world.s))
            oy = int(round((h01(hh, 8, j) * 2 - 1) * 4 * world.s))
            if ox * ox / (36 * world.s ** 2) + oy * oy / (16 * world.s ** 2) > 1:
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
    """House snow, no grit and no contour lines: a calm plane (3) laid in broad drifts a tone
    up, each drift's crest lit (5) along its windward north-west edge and a single cool row (2)
    on its south edge only. Where the snow ends on the same ground it is a thin layer with a
    height: a lit lip (5) over a shaded south face of two rows (2, then 1), the ground under it
    a tone down; its west and east ends lit and shaded. At a rim the lip draws the cornice."""
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
    n = fbm2(X, Y * 1.6, 34.0 * world.s, hashu(seed, 123), 2)
    D = sn & (n > 0.56)
    fr.T[D] = 4
    crest = D & (~nb(D, -1, 0) | ~nb(D, 0, -1)) & (n > 0.6) & nb(D, 1, 0)
    fr.T[crest] = 5
    # a drift's lee: its south edge a broken row of the cool sibling at the plane's tone, only
    # where the drift is thick (no drawn contour lines)
    south = D & ~nb(D, 1, 0) & nb(D, -2, 0) & (vnoise1(X, 5.0, hashu(seed, 125)) > 0.45)
    fr.F[south] = sf[2]
    fr.T[south] = 3
    n2 = vnoise2(X, Y * 1.5, 26.0 * world.s, hashu(seed, 124))
    cool = sn & ~D & (n2 < 0.3)
    fr.F[cool] = sf[2]
    hollow = sn & ~D & (n2 < 0.2)
    fr.T[hollow] = 2
    # the margin (Matt, 21 Oct: a drift hugging the ground, broken by grass and rock): within a
    # few px of its edge the snow thins, and the grass shows through in soft patches
    S_ = world.s
    other = (K == TOP) & ~sn & (fr.tag != TAG['side'])
    de = np.zeros(fr.shape, np.int32)
    cur = other.copy()
    DM = max(2, int(3 * S_))
    for k in range(1, DM + 1):
        cur = near(cur, 1)
        de = np.where(sn & cur & (de == 0), k, de)
    de = np.where(sn & (de == 0), DM + 1, de)
    thin = sn & (de <= DM) & (vnoise2(X, Y * 1.4, 5.0 * S_, hashu(seed, 126)) < 0.72 - 0.6 * de / DM)
    gid = sibs(world.T['top']) if world.T['top'] in ('grass', 'sand') else sibs('grass')
    fr.F[thin] = gid[2]
    fr.T[thin] = 3
    fr.tag[thin] = TAG['ground']
    fr.mat[thin] = MAT_GROUND
    sn = sn & ~thin
    # a thin layer: its south edge one cool row, the ground under it in a soft shadow
    ground_below = nb((K == TOP) & ~sn & (fr.tag != TAG['side']), 1, 0)
    s1 = sn & ground_below
    band = s1.copy()
    for _k in range(max(1, int(round(1.25 * S_))) - 1 + 1):      # a cool shadow band 2 to 3 px deep on its south edge
        band |= sn & nb(band, 1, 0)
    fr.F[band] = sf[2]
    fr.T[band] = 2
    fr.T[s1] = np.minimum(fr.T[s1], 2)
    west = sn & ~nb(sn, 0, -1) & ~s1
    fr.T[west] = np.maximum(fr.T[west], 4)
    east = sn & ~nb(sn, 0, 1) & ~s1
    fr.F[east] = sf[2]
    below = (K == TOP) & ~sn & (nb(s1, -1, 0) | (nb(s1, -2, 0) & (h01(hashu(seed, 127), X // 3, Y) < 0.5))) & (fr.tag == TAG['ground'])
    fr.T[below] = np.maximum(0, fr.T[below] - 1)
    shp_ = (K == TOP) & ~sn & near(sn, max(1, int(S_))) & (fr.tag == TAG['ground']) & ~below
    fr.T[shp_] = np.minimum(fr.T[shp_], 2)


def snow_extras(fr: Frame, world: World):
    """Half-buried rocks in the snow (a cap on top, a drift piled on the windward west, blue
    shade on the east and at the foot) and drifts against the foot of a face whose top is
    snowy."""
    seed = world.seed
    sn = fr.tag == TAG['snow']
    for x, y, hh in zip(*candidates(fr, int(20 * world.s), hashu(seed, 131), np.where(sn & ~near(~sn, int(4 * world.s)), 0.45, 0.0))):
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
    S_ = world.s
    site = fr.X // int(44 * S_)
    hs = hashu(seed, site, 132)
    wv = (16 + 12 * h01(hs, 1)) * S_
    dx = fr.X + 0.5 - (site * int(44 * S_) + (22 + 10 * (h01(hs, 2) - 0.5)) * S_)
    shape = np.sqrt(np.clip(1 - (2 * dx / wv) ** 2, 0, 1))
    L = np.where(h01(hs, 3) < 0.5, np.floor((6 + 5 * h01(hs, 4)) * S_ * shape * (0.85 + 0.15 * vnoise1(fr.X, 3.0, hashu(seed, 133))) + 0.3), 0)
    dist = np.zeros(fr.shape, np.int32)
    for k in range(int(14 * S_), 0, -1):
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


SNOW_ROCKS = [(4.6, 1.1, -0.4), (7.5, 0.55, 0.0), (4.0, 0.85, 0.15), (5.5, 0.9, 0.4)]   # (rx, ry / rx, lean)


def _snow_rock(fr: Frame, x, y, hh, sn, rock):
    """A rock poking out of the snow: an irregular lump lit on its west, its foot lost in the
    snow (no outline there, a blue shade line along it), a snow cap on its lit top, a drift
    piled on its windward west and blue shade on its lee."""
    # four rocks: a tall one leaning west, a long flat slab, a small round one, a block
    # leaning east; each scaled a little
    rx0, ratio, lean = SNOW_ROCKS[int(hashu(hh, 9) % np.uint32(len(SNOW_ROCKS)))]
    rx = rx0 * (0.85 + 0.3 * h01(hh, 1)) * fr.world.s
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
def _timber_steps(fr, world, st, tread, riser, nose, under, a, b):
    """The meadow's own stair (Eastward's farm stair): a plank laid along each step, lit at
    its front edge and worn pale in the middle, its riser in shade with a dark row under the
    nosing and short posts holding the plank at both ends and every 12 to 16 px."""
    seed = world.seed
    X, Y = fr.X, fr.Y
    tf = sibs('timber')
    fam = np.full(fr.shape, tf[0])
    t = np.where(tread, 3, 1)
    t = np.where(nose, 4, t)
    t = np.where(tread & nb(tread, -1, 0) & ~nb(tread, -2, 0) & ~nose, 4, t)     # the plank's back edge
    width = a + b
    u = a / np.maximum(1, width)
    worn = tread & ~nose & (np.abs(u - 0.5) < 0.18)
    fam = np.where(worn, tf[1], fam)
    gr = tread & (h01(hashu(seed, 147), X // 4, Y) < 0.2) & (np.mod(X, 4) < 3) & ~nose
    t = np.where(gr, 2, t)
    pitch = 12 + (hashu(seed, 148) % np.uint32(5)).astype(np.int64)
    post = riser & ((a <= 2) | (b <= 2) | (np.mod(a - 3, pitch) < 2)) & ~under
    fam = np.where(post, tf[2], fam)
    t = np.where(post, np.where(np.mod(a - 3, pitch) == 0, 3, 2), t)
    t = np.where(under, 0, t)
    fr.F[st] = fam[st]
    fr.T[st] = t[st]
    fr.tag[st] = TAG['stair']


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
    stp = hashu(seed, zl, py // int(16 * world.s), 141)
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
    pys = np.where((flag[py, xw] == 0) & st, np.minimum(py + 1, world.Z.shape[0] - 1), py)   # a top riser's own row
    a, b = wl[pys, xw].astype(np.int64), wr[pys, xw].astype(np.int64)
    tread = st & (K == TOP)
    riser = st & (K == FACEK)
    nose = tread & nb(riser, 1, 0)
    under = riser & nb(nose, -1, 0)
    if world.E['stair'] == 'timber':
        return _timber_steps(fr, world, st, tread, riser, nose, under, a, b)
    # stones along the step, their lengths wandering (2 to 14 px)
    Ls = int(round(30 * world.s))     # broad slabs: one, now and then two, to a step
    off = (hashu(stp, 2) % np.uint32(31)).astype(np.int64)
    q = X + off
    k0 = q // Ls
    edge = lambda k: k * Ls + np.round(9.0 * world.s * (h01(stp, k, 3) - 0.5)).astype(np.int64)  # noqa: E731
    kk = k0 - (q < edge(k0)) + (q >= edge(k0 + 1))
    lo, hi = edge(kk), edge(kk + 1)
    sh = hashu(stp, kk, 4)
    first = q == lo
    second = q == lo + 1
    last = q == hi - 1
    fam = ids[(hashu(sh, 1) % np.uint32(3)).astype(np.int64)]
    # each stone is a rounded block: its top the tread, its front the riser below it, shaded as
    # a dome lit from the upper left, its corners knocked back into crevices (rock, not boards)
    trow = np.zeros(fr.shape, np.int64)
    for sr in world.stairs:
        m = tread & (fr.X >= sr.x0) & (fr.X < sr.x1)
        trow = np.where(m, np.mod(py - sr.py, sr.tread), trow)
    TR = max(st_.tread for st_ in world.stairs) if world.stairs else 8
    v = np.where(tread, trow, TR - 1 + P['D'])
    au = (q - lo + 0.5) / np.maximum(1, hi - lo)
    vn = v / (2.0 * TR - 1)
    I = -(au - 0.5) * 0.9 - (vn - 0.4) * 1.1 + 0.4 * (1 - (2 * au - 1) ** 2)
    I = I + 0.25 * (h01(sh, 2) - 0.5)
    t = np.where(I > 0.45, 4, np.where(I > 0.0, 3, np.where(I > -0.45, 2, 1)))
    t = np.where(tread & (v == 0) & second, 5, t)
    corner = (first | last) & ((tread & (v == 0)) | (riser & ~nb(riser, 1, 0)))
    seam = first & (h01(sh, 11) < 0.45)
    chipped = h01(sh, 5) < 0.3
    proud = (h01(sh, 6) > 0.72) & ~chipped
    worn_n = nose & (vnoise1(X, 5.0 * world.s, hashu(seed, 149)) > 0.62)          # the nosing worn round
    t = np.where(nose & chipped, 2, t)
    t = np.where(worn_n, 3, t)
    t = np.where(under, np.where(proud, 3, 0), t)
    t = np.where(seam | corner, np.where(tread, 1, 0), t)
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
    # the floor just behind the head is the upper floor's own ground, flush to the first riser
    for sr in world.stairs:
        hd = (K == TOP) & (P['ST'] == 0) & (P['PY'] >= sr.py - sr.landing - 2) & (P['PY'] < sr.py) & (fr.X >= sr.x0) & (fr.X < sr.x1) \
            & (P['ZH'] == sr.z_high)
        if hd.any() and (fr.mat[hd] == MAT_PATH).mean() > 0.3:
            fr.F[hd] = sibs(world.T.get('ledge', 'path'))[0]
            fr.T[hd] = np.where(nb(st, 1, 0)[hd], 2, 3)
            fr.tag[hd] = TAG['path']
            fr.mat[hd] = MAT_PATH
    # cheek stones overlap the stair's sides, so its edges are ragged and it sits in the rock
    allow = st | np.isin(fr.tag, (TAG['side'], TAG['rock'], TAG['recess'])) | \
        (near(st, int(round(7 * world.s))) & np.isin(fr.tag, (TAG['ground'], TAG['path'], TAG['fringe'])))
    for k, sr in enumerate(world.stairs if world.E['stair'] == 'rock' else []):
        y_top = sr.py - 1 - world.top - sr.z_high
        y_bot = sr.foot_row - world.top - sr.z_low
        # above the face's foot the face itself stands either side of the flight; below it a
        # few rough rocks of the crag lie against the flight, ragged and of mixed size
        y_face = sr.py - world.top - sr.z_low
        for side, xe in ((0, sr.x0), (1, sr.x1)):
            # one large rock against the face's foot, and a smaller one lower down on some sides
            for j, (fy, sz) in enumerate(((1.0, 0.5),)):
                hh = hashu(seed, sr.x0, sr.py, side, j, 142)
                if h01(hh, 5) < 0.5:
                    continue
                rx = (4.2 + 2.4 * h01(hh, 1)) * world.s * sz
                ry = (3.0 + 1.4 * h01(hh, 2)) * world.s * sz
                cx = xe + (-1 if side == 0 else 1) * (0.25 + 0.35 * h01(hh, 3)) * rx
                cy = y_face + fy * (y_bot - y_face) - (1.0 - fy) * 2 * world.s
                boulder(fr, cx, cy, rx, ry, hh, allow, world.T['loose'], moss=0.3 if world.T['top'] in GREEN else 0.0,
                        tag=TAG['side'])


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
    for f in out:          # the kit's rule: a fall widens with its drop (in world px, then texels)
        w = max(f['x1'] - f['x0'], int(round(fall_width((f['ztop'] - f['h2']) / world.s) * world.s)))
        c = (f['x0'] + f['x1']) / 2
        f['x0'], f['x1'] = int(round(c - w / 2)), int(round(c - w / 2)) + w
    world._falls = out
    return out


def fall_width(drop: int) -> int:
    """How wide a fall is for its drop: water speeds up and spreads as it falls, so a fall
    is 2 px plus one for every 9 px of drop, 3 to 12 px (a 32 px drop 6, a 64 px drop 9)."""
    return int(min(12, max(3, round(2 + drop / 9.0))))


def paint_water(fr: Frame, world: World):
    """Still and running water on the tops (eastward-edges.md 5.3): water lies a little below
    its banks, so the north bank shows a small face (2 px of earth under a darker lip row of
    the grass), the water's top row is a broken light waterline (tone 5), and under it a dark
    band (two to four rows on a pond, one on a stream) steps back to the body. Side and south
    banks meet the water directly. Broad water (a lake, the sea) has depth bands, a foam line
    at the shore and swells. Current streaks lie with the flow."""
    seed = world.seed
    P = fr.P
    K = P['kind']
    X, Y = fr.X, fr.Y
    wf = sibs('water')
    wt = (K == TOP) & (fr.mat == MAT_WATER)
    if wt.any():
        # how far each water pixel lies below the north bank, and how wide the water is there
        dn = np.zeros(fr.shape, np.int32)
        cur = wt & ~nb(wt, -1, 0)
        DM = int(4 + world.M['band'][1])
        for k in range(1, DM):
            dn = np.where(cur & (dn == 0), k, dn)
            cur = wt & nb(cur, -1, 0)
        dn = np.where(wt & (dn == 0), DM, dn)
        k3 = int(round(4 * world.s))       # wider than a rill (about 8 world px across)
        wide = wt & near(wt & nb(wt, 0, k3) & nb(wt, 0, -k3) & nb(wt, k3, 0), k3)
        b0, b1 = world.M['band']
        band = np.where(wide, b0 + np.floor((b1 - b0 + 0.999) * vnoise1(X, 9.0 * world.s, hashu(seed, 167))).astype(np.int64), max(1, b0 // 2))
        t = np.full(fr.shape, 3)
        t = np.where((dn >= 2) & (dn < 2 + band), np.where(dn == 2, 1, 2), t)
        line = (dn == 1) & (vnoise1(X, 2.5, hashu(seed, 169)) > 0.3)
        t = np.where(dn == 1, np.where(line, 5, 2), t)
        # current: 3 to 5 px lit streaks over their own shadow, glints in pairs
        st = wt & (dn > 1 + band) & (h01(hashu(seed, 161), X // 4, Y // 3) < 0.16) & (np.mod(X, 4) < 3) & (np.mod(Y, 3) == 0)
        t = np.where(st, 4, t)
        sh = wt & nb(st, -1, 0) & ~st & (dn > 1 + band)
        t = np.where(sh, 2, t)
        fr.F[wt] = wf[np.where(vnoise2(X, Y, 9.0, hashu(seed, 162)) > 0.62, 2, 0)[wt]]
        # broad water: depth by the distance from the shore, foam at the shore, swells
        sd = np.zeros(fr.shape, np.int32)
        shore = ~wt
        SB = int(round(22 * world.s))
        for k in range(1, SB + 1):
            shore = near(shore, 1)
            sd = np.where(wt & shore & (sd == 0), k, sd)
        sd = np.where(wt & (sd == 0), SB + 1, sd)
        broad = wt & near(sd >= SB, SB)      # a lake or the sea: wider than three adults
        sw = sd / world.s
        tb = np.where(sw <= 2, 4, np.where(sw <= 6, 3, np.where(sw <= 11, 2, 1)))
        foam = broad & (sw <= 1 + (vnoise1(X, 5.0 * world.s, hashu(seed, 165)) > 0.55))
        wave = broad & (sd > 3) & (h01(hashu(seed, 166), X // 5, Y // 2) < 0.14) & (np.mod(X, 5) < 4) & (np.mod(Y, 2) == 0)
        tb = np.where(wave, np.minimum(4, tb + 1), tb)
        tb = np.where(broad & nb(wave, -1, 0) & ~wave & (sd > 3), np.maximum(1, tb - 1), tb)
        t = np.where(broad, tb, t)
        # a rill (narrow running water): a light ribbon along its west side, its east side in
        # shade, riffles across the flow every few px (a lit dash over its dark trough)
        rill = wt & ~wide & ~broad
        if rill.any():
            S_ = world.s
            dw = np.zeros(fr.shape, np.int32)
            de = np.zeros(fr.shape, np.int32)
            cw_, ce_ = rill & ~nb(rill, 0, -1), rill & ~nb(rill, 0, 1)
            for k in range(1, int(8 * S_)):
                dw = np.where(cw_ & (dw == 0), k, dw)
                de = np.where(ce_ & (de == 0), k, de)
                cw_ = rill & nb(cw_, 0, -1)
                ce_ = rill & nb(ce_, 0, 1)
            wid = dw + de
            rt = np.where(dw <= max(1, int(0.6 * S_)), 4, np.where(de <= max(1, int(0.8 * S_)), 2, 3))
            ph = (Y + 2.0 * S_ * vnoise1(X, 6.0 * S_, hashu(seed, 171))) / (5.0 * S_)
            rif = rill & (np.mod(ph, 1.0) < 0.5 / S_) & (dw > 1) & (de > 1) & (wid >= 3)
            rt = np.where(rif, 5, rt)
            rt = np.where(rill & nb(rif, -1, 0) & ~rif & (de > 1), 2, rt)
            t = np.where(rill & (dn > 1), rt, t)
        fr.F[foam] = FID['snow']
        fr.T[wt] = t[wt]
        fr.tag[wt] = TAG['water']
        if rill.any():
            gr_ = (K == TOP) & ~wt & np.isin(fr.tag, (TAG['ground'], TAG['snow']))
            bw = (1.2 + 1.4 * vnoise1(Y + 3 * X, 7.0 * S_, hashu(seed, 172))) * S_
            bd = np.zeros(fr.shape, np.int32)
            cur_ = rill.copy()
            for k in range(1, int(3 * S_) + 2):
                cur_ = near(cur_, 1)
                bd = np.where(gr_ & cur_ & (bd == 0), k, bd)
            bank_ = gr_ & (bd > 0) & (bd <= bw)
            ef_ = sibs('earth')
            fr.F[bank_] = ef_[np.where(bd[bank_] <= 1, 2, 0)]
            fr.T[bank_] = np.where(bd[bank_] <= 1, 2, 3)
            fr.tag[bank_] = TAG['path']
            for x, y, hh in zip(*candidates(fr, max(3, int(4 * S_)), hashu(seed, 173), np.where(bank_, 0.35, 0.0), inset=4)):
                put_stamp(fr, PEBBLE[int(hh % np.uint32(4))], x, y, int(sibs('stone')[int(hashu(hh, 4) % np.uint32(3))]), allow=bank_ | rill)
        # the north bank's small face: two rows of earth over the water, the lip row darker
        gnd = (K == TOP) & ~wt & np.isin(fr.tag, (TAG['ground'], TAG['path'], TAG['snow'], TAG['side']))
        b1 = gnd & nb(wt & ~broad, 1, 0)
        b2 = gnd & (nb(b1, 1, 0) | (nb(b1, 2, 0) & (world.M['bank'] >= 3)) | (nb(b1, 3, 0) & (world.M['bank'] >= 4))) & ~b1 & (world.E['bank']['rows'] >= 2)
        ef = sibs('earth')
        fr.F[b1 | b2] = ef[2]
        fr.T[b1] = 1
        fr.T[b2] = 2
        fr.tag[b1 | b2] = TAG['path']
        lipr = gnd & nb(b2, 1, 0) & ~b1 & ~b2
        fr.T[lipr] = np.minimum(fr.T[lipr], 2)
        # side banks: one px of damp earth where the water meets the grass east or west
        sb = gnd & ~b1 & ~b2 & (nb(wt & ~broad, 0, 1) | nb(wt & ~broad, 0, -1))
        fr.F[sb] = ef[2]
        fr.T[sb] = 2
        # the meadow's banks grow reeds: upright blades of leaf at the water's edge
        if world.E['bank']['reeds'] > 0:
            edge_g = gnd & near(wt & ~broad, 2) & ~b1
            lf = sibs('leaf')
            for x, y, hh in zip(*candidates(fr, 5, hashu(seed, 170), np.where(edge_g, world.E['bank']['reeds'], 0.0), inset=4)):
                put_stamp(fr, REED[int(hh % np.uint32(len(REED)))], x, y, int(lf[int(hashu(hh, 4) % np.uint32(3))]), allow=gnd | wt, tag=TAG['leaf'], anchor=(1, 5))
    for f in falls(world):
        _fall(fr, world, f)


def _fall(fr: Frame, world: World, f: dict):
    """A fall over a rim: its width set by the drop (fall_width) and changing all the way down
    (narrower at the lip, spreading as it falls, swelling and pinching by noise), a lit west
    edge, sheets and gaps, white water rolling over the lip, wet rock darker either side, mist
    where it lands, and a plunge pool on the ground under it."""
    P = fr.P
    K = P['kind']
    rim_row = f['py'] - world.top - f['h']
    top_row = rim_row + (f['h'] - f['ztop']) + 1
    foot_row = rim_row + (f['h'] - f['h2'])
    if foot_row < fr.y0 - 4 or top_row > fr.y1 + 24 or f['x1'] < fr.x0 - 24 or f['x0'] > fr.x1 + 24:
        return
    wf = sibs('water')
    X, Y = fr.X, fr.Y
    w0 = f['x1'] - f['x0']
    c = (f['x0'] + f['x1']) / 2.0
    prog = np.clip((Y - top_row) / max(1.0, foot_row - top_row), 0, 1)
    S_ = world.s
    half = (w0 / 2.0) * (0.75 + 0.45 * prog) + 0.6 * S_ * (2 * vnoise1(Y, 7.0 * S_, hashu(f['id'], 1)) - 1)
    half = np.maximum(1.0, half)
    cx = c + 0.8 * S_ * (2 * vnoise1(Y, 13.0 * S_, hashu(f['id'], 2)) - 1)
    fx0 = np.floor(cx - half).astype(np.int64)
    fx1 = np.ceil(cx + half).astype(np.int64)
    onface = (K == FACEK) & np.isin(P['PY'], f.get('rows', [f['py']])) & (Y >= top_row) & (Y <= foot_row + 2)
    fall = onface & (X >= fx0) & (X < fx1)
    wet = onface & ~fall & (X >= fx0 - 3) & (X < fx1 + 3)
    fr.T[wet] = np.where(fr.T[wet] == EDGE, EDGE, np.maximum(0, fr.T[wet] - 1))
    beside = wet & ((X == fx0 - 1) | (X == fx1))
    fr.T[beside] = 0
    fr.tag[wet] = TAG['wet']
    rel = (X + 0.5 - fx0) / np.maximum(1, fx1 - fx0)
    # light and dark ribbons running down the sheet (long in Y), the lit west edge, the east in shade
    rib = vnoise2(X * 1.0, Y / 7.0, 1.6 * S_, hashu(f['id'], 3))
    t = np.where(rib > 0.6, 4, np.where(rib < 0.3, 2, 3))
    t = np.where(rel < 0.18, 4, np.where(rel > 0.82, 2, t))
    t = np.where(X == fx0, 5, t)
    # where it lands the sheet breaks into white water
    brk = fall & (prog > 0.82 - 0.06 * vnoise1(X, 2.0 * S_, hashu(f['id'], 5)))
    t = np.where(brk, np.where(h01(hashu(f['id'], 9), X // 2, Y // 2) < 0.6, 5, 4), t)
    fr.F[fall] = np.where(brk, FID['snow'], wf[0])[fall]
    fr.T[fall] = t[fall]
    fr.tag[fall] = TAG['water']
    # lip stones: a stone either side where the water leaves the top
    if f['kind'] == 'stream':
        okl = (K == TOP) & np.isin(fr.tag, (TAG['ground'], TAG['path'], TAG['fringe']))
        for side in (0, 1):
            hl = hashu(f['id'], 30, side)
            lx = (f['x0'] - 1.2 * S_) if side == 0 else (f['x1'] + 1.2 * S_)
            boulder(fr, lx, top_row - 1.5 * S_, (2.2 + 1.2 * h01(hl, 1)) * S_, (1.7 + 0.8 * h01(hl, 2)) * S_, hl,
                    okl | (fr.tag == TAG['water']) & (K == TOP), 'stone', moss=0.4)
    lip = fall & (Y <= top_row + 1)
    fr.F[lip] = np.where((h01(hashu(f['id'], 6), X, Y) < 0.6)[lip], FID['snow'], wf[0])
    fr.T[lip] = np.where(Y[lip] == top_row, 5, 4)
    mq = ((X + 0.5 - c) / (w0 / 2 + 6.0 * world.s)) ** 2 + ((Y + 0.5 - foot_row) / (6.0 * world.s)) ** 2
    mist = (mq <= 1.0) & ~fall & (Y <= foot_row + 2) & (h01(hashu(f['id'], 7), X // 2, Y // 2) < 0.55 * (1.2 - mq)) \
        & np.isin(fr.tag, (TAG['rock'], TAG['recess'], TAG['wet']))
    fr.F[mist] = FID['snow']
    fr.T[mist] = 3
    fr.tag[mist] = TAG['foam']
    if f['kind'] == 'spring':
        seep = (K == FACEK) & (P['PY'] == f['py']) & (np.abs(Y - top_row + 1) <= 1) & (X >= fx0.min() - 3) & (X < fx1.max() + 3) & ~fall
        lf = sibs('leaf')
        fr.F[seep] = lf[(h01(hashu(f['id'], 4), X, Y) * 3).astype(np.int64)[seep]]
        fr.T[seep] = np.where(Y[seep] < top_row, 4, 2)
        fr.tag[seep] = TAG['leaf']
    _pool(fr, world, f, foot_row, c, w0)


def _pool(fr: Frame, world: World, f: dict, foot_row: int, cx: float, w0: int):
    """A plunge pool under a fall (eastward-edges.md 5.3): a rounded rectangle on the ground
    at the foot, a little wider than the fall each side, its top edge the face's foot; a light
    waterline under the foot, a dark band stepping back to the body, small broken ripples and
    foam where the fall lands, glints in pairs, a bank of damp earth on the south and a rim of
    stones round its near side."""
    P = fr.P
    K = P['kind']
    X, Y = fr.X, fr.Y
    hh = f['id']
    S_ = world.s
    # a rounded rectangle on the soft grid (Matt, 21 Oct 11:44): its sides on cell lines, its
    # corners rounded (3 world px), so q is the distance outside the box in units of its size
    cell = GRID * S_
    gx0 = np.floor((cx - w0 / 2 - 9 * S_) / cell) * cell
    gx1 = np.ceil((cx + w0 / 2 + 9 * S_) / cell) * cell
    gy1 = np.ceil((foot_row + 13 * S_) / cell) * cell
    rx, ry = (gx1 - gx0) / 2, (gy1 - foot_row) / 2
    cy = foot_row + ry
    rc = 3.0 * S_
    qx = np.maximum(np.abs(X + 0.5 - (gx0 + gx1) / 2) - (rx - rc), 0)
    qy = np.maximum(np.abs(Y + 0.5 - cy) - (ry - rc), 0)
    q = np.sqrt(qx ** 2 + qy ** 2) / rc
    q = np.where(q <= 1.0, np.maximum(np.abs(X + 0.5 - (gx0 + gx1) / 2) / rx, np.abs(Y + 0.5 - cy) / ry) * 0.999, 1.0 + q - 1.0)
    cx = (gx0 + gx1) / 2
    ground = (K == TOP) & (P['ZH'] == f['h2']) & (P['ST'] == 0)
    pool = ground & (q <= 1.0) & (Y > foot_row)
    if not pool.any():
        return
    wf = sibs('water')
    dn = Y - foot_row
    b0 = world.M['band'][0]
    t = np.where(dn == 1, np.where(vnoise1(X, 2.5, hashu(hh, 18)) > 0.3, 5, 2), np.where(dn <= 1 + b0, 1, np.where(dn <= 2 + b0, 2, 3)))
    lx, ly = cx, foot_row + 2.5 * S_
    rr = np.sqrt(((X + 0.5 - lx) / 2.2) ** 2 + (Y + 0.5 - ly) ** 2)
    ring = (rr >= 3.5 * S_) & (rr < 3.5 * S_ + 1) & (Y > ly) & (vnoise1(X, 3.0 * S_, hashu(hh, 19)) > 0.35)
    t = np.where(ring, 4, t)
    fq = ((X + 0.5 - lx) / (w0 / 2 + 2.5 * S_)) ** 2 + ((Y + 0.5 - ly) / (2.2 * S_)) ** 2
    foam = (fq <= 1.0) & (h01(hashu(hh, 14), X // 2, Y) < 0.85 - 0.5 * fq)
    t = np.where(foam, np.where(fq < 0.5, 5, 4), t)
    gl = (h01(hashu(hh, 15), X // 2, Y) < 0.05) & (dn > 4) & ~foam & (np.mod(X, 2) == 0)
    gl = gl | (nb(gl, 0, -1) & (dn > 4))
    t = np.where(gl & (q < 0.85), 4, t)
    fr.F[pool] = np.where(foam[pool], FID['snow'], wf[0])
    fr.T[pool] = t[pool]
    fr.tag[pool] = TAG['water']
    bank = ground & ~pool & (q <= 1.22) & (Y > foot_row)
    ef = sibs('earth')
    fr.F[bank] = ef[2]
    fr.T[bank] = np.where(q[bank] < 1.1, 2, 3)
    fr.tag[bank] = TAG['path']
    rim_ok = ground | (fr.tag == TAG['path']) | (fr.tag == TAG['water'])
    # stones sit on the outline, half in the water, so they break it (west, south and east)
    n = int(5 + rx / (2.5 * S_))
    for i in range(n):
        u = (i + 0.5 + 0.5 * (h01(hh, 20, i) - 0.5)) / n
        ang = np.pi * (-0.05 + 1.1 * u)
        cs, sn_ = np.cos(ang), np.sin(ang)
        k_ = 1.0 / max(abs(cs), abs(sn_), 1e-6)          # out to the rectangle's side
        sx = cx + cs * k_ * rx
        sy = cy + sn_ * k_ * ry
        if sy <= foot_row + 2 * S_ or h01(hh, 24, i) < 0.22:
            continue
        r0 = (2.0 + 1.6 * h01(hh, 21, i)) * S_
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
    S_ = world.s
    for kind, sp, p, (w0, w1), (l0, l1), cl in (('ivy', 15.0 * S_, T['ivy'], (6 * S_, 13 * S_), (0.35, 0.8), 3.0),
                                                ('cascade', 23.0 * S_, T['cascade'], (16 * S_, 28 * S_), (0.5, 0.95), 4.0)):
        if p <= 0:
            continue
        k0 = np.floor(s / sp).astype(np.int64)
        for dk in (-1, 0, 1):
            kk = k0 + dk
            hk = hashu(seed, lid, kk, 201 if kind == 'ivy' else 202)
            on = (h01(hk, 1) < p) & rimg & (Hf >= 24 * S_)
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
    crown = (f['k'] >= 0) & ~f['rec'] & (h01(m, 51) < 0.1) & (d > Hf * 0.4)
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
    # plants in the crevices: a fern or a cushion here and there, at world candidates (so every
    # window of the world places the same ones)
    allow = np.isin(fr.tag, (TAG['rock'], TAG['recess']))
    REC = np.zeros(fr.shape, bool)
    REC[yy[f['rec']], xx[f['rec']]] = True
    REC &= nb(allow, 0, 1) & nb(allow, 1, 0) & nb(allow, -1, 0)
    for x, y, hh in zip(*candidates(fr, int(14 * S_), hashu(seed, 58), np.where(REC, T['crack_plants'] * 0.6, 0.0), inset=8)):
        st = FERN[int(hh % np.uint32(3))]
        put_stamp(fr, st, int(x), int(y), lambda t, k=int(hh): int(lf[int(hashu(k, t, 57) % np.uint32(3))]), allow=allow, tag=TAG['leaf'], anchor=(2, 1))


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
    S_ = world.s
    for k in range(int(14 * S_), 0, -1):
        dist = np.where(nb(face, -k, 0), k, dist)
    stair_near = near(P['ST'] == 1, int(10 * S_))
    water_near = near(fr.tag == TAG['water'], int(6 * S_))
    dist = np.where(dist > 0, np.maximum(1, np.round(dist / S_)), 0).astype(np.int32)   # in world px
    rock = T['rock']
    rid = sibs(rock)
    okg = ground & ~stair_near
    # tufts over the foot
    if T['top'] in GREEN:
        foot = okg & (dist >= 1) & (dist <= 2)
        allow = (ground | face) & ~(fr.tag == TAG['water'])
        gid = sibs(T['top'])
        for x, y, hh in zip(*candidates(fr, int(5 * S_), hashu(seed, 211), np.where(foot, world.E['foot']['tufts'], 0.0))):
            put_stamp(fr, TUFTS[int(hh % np.uint32(len(TUFTS)))], x, y, int(gid[int(hashu(hh, 4) % np.uint32(3))]),
                      allow=allow, anchor=(2, 3))
    # scree
    if T['scree'] > 0:
        pv = np.where(okg & (dist > 0), T['scree'] * np.clip(1.15 - dist / 9.0, 0, 1), 0.0)
        for x, y, hh in zip(*candidates(fr, int(4 * S_), hashu(seed, 212), pv)):
            r = h01(hh, 5)
            if r < 0.6:
                put_stamp(fr, PEBBLE[int(hh % np.uint32(4))], x, y, int(rid[int(hashu(hh, 4) % np.uint32(3))]), allow=okg, tag=TAG['scree'])
                Yc, Xc = y + 2 - fr.y0, x - fr.x0
                if 0 <= Yc < fr.shape[0] and 0 <= Xc + 1 < fr.shape[1] and okg[Yc, Xc]:
                    fr.T[Yc, Xc:Xc + 2] = np.maximum(0, fr.T[Yc, Xc:Xc + 2] - 2)
            else:
                boulder(fr, x, y, (1.8 + 1.6 * h01(hh, 6)) * S_, (1.4 + 1.0 * h01(hh, 7)) * S_, hh, okg, rock)
    if T['boulders'] > 0:
        pv = np.where(okg & (dist >= 3) & (dist <= 9) & ~water_near, T['boulders'], 0.0)
        for x, y, hh in zip(*candidates(fr, int(26 * S_), hashu(seed, 213), pv)):
            rx = (4 + 5 * h01(hh, 8)) * S_
            boulder(fr, x, y, rx, rx * (0.62 + 0.15 * h01(hh, 9)), hh, okg | (fr.tag == TAG['scree']), rock, moss=0.6)
    # ferns where it is damp
    if T['ferns'] > 0:
        damp = ground & ~stair_near & ((water_near & (fr.tag != TAG['water'])) | ((dist >= 1) & (dist <= 4)))
        pv = np.where(damp, np.where(water_near, T['ferns'], T['ferns'] * 0.35), 0.0)
        for x, y, hh in zip(*candidates(fr, int(12 * S_), hashu(seed, 214), pv)):
            fern(fr, x, y, hh, (ground | face) & (fr.tag != TAG['water']) & (fr.tag != TAG['stair']), (1.0 + 0.5 * h01(hh, 10)) * S_)
    # shrubs and trees on open ground
    open_g = ground & ~near(~ground, int(4 * S_)) & ~near(fr.tag == TAG['water'], int(16 * S_))
    if T['shrubs'] > 0:
        pv = np.where(open_g & (dist == 0), T['shrubs'] * 20, np.where(ground & (dist > 2) & (dist < 12) & ~stair_near & ~near(fr.tag == TAG['water'], int(16 * S_)), T['shrubs'] * 30, 0.0))
        for x, y, hh in zip(*candidates(fr, int(28 * S_), hashu(seed, 215), pv)):
            rx = (4.5 + 3.5 * h01(hh, 11)) * S_
            foliage(fr, x, y - rx * 0.4, rx, rx * 0.75, hh, ground | (fr.tag == TAG['scree']), base=T.get('shrub', 'leaf'))
    if T['trees'] > 0:
        far = ground & ~near(~ground, int(14 * S_))
        for x, y, hh in zip(*candidates(fr, int(72 * S_), hashu(seed, 216), np.where(far & ~water_near, T['trees'] * 120, 0.0))):
            tr = sibs('timber')
            for dy in range(0, int(9 * S_)):
                for dx in range(-int(S_), int(S_) + 1):
                    X, Y = x + dx - fr.x0, y - dy - fr.y0
                    if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1]:
                        fr.F[Y, X] = tr[0]
                        fr.T[Y, X] = 3 if dx < 0 else (2 if dx == 0 else 1)
                        fr.tag[Y, X] = TAG['tree']
            rx = (12 + 4 * h01(hh, 12)) * S_
            foliage(fr, x + 0.5, y - 9 * S_ - rx * 0.7, rx, rx * 0.85, hh, (fr.P['kind'] > 0) & (fr.tag != TAG['figure']), base='leaf')


# ---- set pieces: the polished swatch as parts any region can place -----------------------------
# Matt, 21 Oct 09:51 and 09:52: "consider how you can reuse assets like the screenshot i just
# attached once it's polished in other places of the same biome. should help speed up terrain
# building". A piece is not a picture: it is a rule that edits a region's plan (its height
# field, masks, stairs) and leaves dressing for the painter, so it adapts to the face height and
# the outline where it lands, takes its colours from the biome's table, and picks its variant
# (boulder order, plants, lip runs) by a hash of where it stands, so two copies never match.
# Nothing is mirrored: the light stays upper left. Every piece returns a Placed record: its
# footprint on the 8 px grid, its attach points (where paths, streams and ledges join it) and
# its kind; walk_mask() gives what can be walked.
@dataclass
class Placed:
    """A placed piece: footprint (screen px, on the 8 px grid), attach points (name -> screen
    (x, y)), the tier it stands on and its variant hash."""
    kind: str
    box: tuple
    attach: dict
    z: int = 0
    variant: int = 0


def _g8(v: float) -> int:
    return int(round(v / GRID)) * GRID


class Plan:
    """A region being built: a plan height field and its masks, in the biome's table. Pieces
    are placed in screen coordinates (x, y of the ground they stand on) with the tier z they
    stand on; the plan row is y + top + z. `world()` makes the World the painter renders.

        plan = Plan(512, 512, 'highland', seed=4)
        plan.tier(32, [(-20, 300), (200, 292), (540, 310)])     # a rim drawn as a screen curve
        st = plan.stair(240, 32, z_low=0, width=40)            # through the face nearest x 240
        plan.path([st.attach['foot'], (230, 420), (180, 512)], z=0)
        img = render(plan.world()).image()
    """

    def __init__(self, width: int, height: int, biome: str = 'highland', seed: int = 1, top: int = 96):
        self.W, self.H, self.biome, self.seed, self.top = width, height, biome, seed, top
        self.T = BIOMES[biome]
        self.Z = np.zeros((height + top, width), np.int32)
        self.path_m = np.zeros(self.Z.shape, bool)
        self.water_m = np.zeros(self.Z.shape, bool)
        self.snow_m = np.zeros(self.Z.shape, bool)
        self.stairs, self.decals, self.placed = [], [], []
        self._snapped = False

    # -- terrain ---------------------------------------------------------------------------------
    def tier(self, z: int, rim, x0: int = None, x1: int = None, lobes: float = 1.0):
        """Raise ground to z north of a rim: `rim` is a list of (x, screen row) control points
        (a Catmull-Rom curve) or an array of screen rows per column (nan where absent). The
        rim is given lobes, bays and spurs by world-anchored noise (8 to 12 px, about every 30
        to 60 px; `lobes` scales them), so no rim runs ruler-straight. Where the tier ends at
        x0 or x1 it does not stop in a north-south wall: its rim turns north in a rounded end
        and leaves the picture, so a side band shows only where a face really ends."""
        rim = curve(rim, self.W) if isinstance(rim, (list, tuple)) else np.asarray(rim, float).copy()
        cols = np.arange(self.W, dtype=np.float64)
        hz = hashu(self.seed, z, 801)
        rim = rim + lobes * (6.0 * (2 * vnoise1(cols, 48.0, hz) - 1) + 5.0 * (2 * vnoise1(cols, 90.0, hashu(hz, 2)) - 1))
        far = -6.0                                      # just north of the picture's top row
        for xe, sgn in ((x0, 1), (x1, -1)):
            if xe is None:
                continue
            R = max(48.0, 2.4 * float(np.nanmedian(rim) - far))   # leave at about 22 degrees
            u = (cols - xe) * sgn                       # 0 at the end, growing into the tier
            k = np.clip(1 - u / R, 0, 1)
            lift = (rim - far) * (1 - np.sqrt(np.clip(1 - k * k, 0, 1)))
            rim = np.where(u < 0, np.nan, np.where(u < R, rim - lift, rim))
        ok = ~np.isnan(rim)
        py = np.arange(self.Z.shape[0])[:, None]
        m = py <= np.where(ok, np.round(np.nan_to_num(rim, nan=-10 ** 6)), -10 ** 6)[None, :] + self.top + z
        self.Z = np.where(m, np.maximum(self.Z, z), self.Z)
        self._snapped = False

    def mound(self, z: int, x0: int, y0: int, x1: int, y1: int):
        """A raised block whose top, seen on screen, covers x0..x1, y0..y1 (a plateau, an
        outcrop, the far side of a hollow): plan rows y + top + z."""
        r0, r1 = y0 + self.top + z, y1 + self.top + z
        sub = self.Z[max(0, r0):max(0, r1), max(0, x0):x1]
        self.Z[max(0, r0):max(0, r1), max(0, x0):x1] = np.maximum(sub, z)
        self._snapped = False

    def snap(self):
        """Put the outline on the soft grid now (World._snap), so pieces that look for a face
        find the one that will be drawn."""
        if not self._snapped:
            w = World(self.Z, self.biome, seed=self.seed, top=self.top)
            self.Z = w.Z[:self.Z.shape[0]].copy()
            self._snapped = True

    def z_at(self, x: int, y: int) -> int:
        """The height of the ground seen at screen (x, y) (the painter's walk: the nearest)."""
        self.snap()
        best = 0
        for z in sorted({int(v) for v in np.unique(self.Z)}):
            r = y + self.top + z
            if 0 <= r < self.Z.shape[0] and self.Z[r, x] == z:
                best = z
        return best

    def rim_row(self, x: int, z_high: int, near_y: int = None) -> int:
        """The plan row of the last row of tier z_high above a drop at column x (its face),
        nearest the screen row near_y if given."""
        self.snap()
        col = self.Z[:, x]
        rows = np.nonzero((col[:-1] >= z_high) & (col[1:] < z_high))[0]
        if not len(rows):
            raise ValueError(f'no face below tier {z_high} at x {x}')
        if near_y is None:
            return int(rows[-1])
        return int(rows[np.argmin(np.abs(rows - (near_y + self.top + z_high)))])

    def world(self, density: float = 1.0) -> World:
        """The World to render, at `density` art texels a world px (1 to 3). Everything placed
        stays in world px; only the raster scales."""
        self.snap()
        w = World(self.Z, self.biome, seed=self.seed, top=self.top, path=self.path_m, water=self.water_m,
                  snow=self.snow_m if self.snow_m.any() else None, stairs=list(self.stairs), decals=list(self.decals),
                  snap=False, density=density)
        w.placed = list(self.placed)
        return w

    def _place(self, kind, box, attach, z, variant):
        x0, y0, x1, y1 = box
        p = Placed(kind, (_g8(x0) if x0 % GRID else x0, _g8(y0) if y0 % GRID else y0,
                          _g8(x1) if x1 % GRID else x1, _g8(y1) if y1 % GRID else y1), attach, z, int(variant))
        self.placed.append(p)
        return p

    def _var(self, kind, x, y):
        if kind not in self.T['pieces']:
            raise ValueError(f'the {self.biome} biome does not own a {kind!r} piece (BIOMES[...]["pieces"])')
        return int(hashu(self.seed, x, y, sum(map(ord, kind))))

    # -- pieces ----------------------------------------------------------------------------------
    def stair(self, x: int, z_high: int, z_low: int = None, width: int = 40, near_y: int = None) -> Placed:
        """A stair through the face below tier z_high at column x (its west edge, on the grid):
        any face height, any width (a multiple of 8, 24 or more). Its foot lands on the lower
        ground, its head on the upper floor (eastward-edges.md 6.1)."""
        x = _g8(x)
        width = max(24, _g8(width))
        r = self.rim_row(x + width // 2, z_high, near_y)
        if z_low is None:
            z_low = int(self.Z[r + 1, x + width // 2])
        st = Stair(x, x + width, r + 1, z_low, z_high)
        self.stairs.append(st)
        a = st.attach(self.top)
        box = (x - st.cheek, a['head'][1] - st.landing, x + width + st.cheek, a['foot'][1] + st.landing)
        return self._place('stair', box, {'foot': a['foot'], 'head': a['head']}, z_low, self._var('stair', x, r))

    def ledge(self, x0: int, x1: int, z_high: int, z: int = None, depth: int = 24, near_y: int = None) -> Placed:
        """A ledge path along the face below tier z_high, from x0 to x1: a shelf `depth` px deep
        at height z (half the face by default, on the tier grid) cut into the face, its floor a
        trodden path, its ends rounded by the soft grid."""
        self.snap()
        z = z if z is not None else z_high - self.T['face']
        cols = range(max(0, x0), min(self.W, x1))
        rows = []
        for x in cols:
            r = self.rim_row(x, z_high, near_y)
            lo = int(self.Z[r + 1, x])
            if lo >= z:
                continue
            # the shelf: the ground in front of the face raised to z for `depth` rows; where it
            # ends inside the picture it narrows in a quarter round (no north-south cut)
            R = min(depth, 32)
            e = max((x0 + R - x) if x0 > 0 else 0, (x - (x1 - R)) if x1 < self.W else 0, 0)
            dd = int(round(depth * np.sqrt(max(0.0, 1.0 - (e / R) ** 2)))) if e else depth
            if dd < 4:
                continue
            self.Z[r + 1:r + 1 + dd, x] = np.maximum(self.Z[r + 1:r + 1 + dd, x], z)
            self.path_m[r + 1:r + 1 + dd, x] = True
            rows.append(r)
        self._snapped = False
        self.snap()
        self.path_m &= (self.Z == z) | ~np.isin(np.arange(self.W)[None, :], list(cols))
        if not rows:
            raise ValueError('ledge: no face to cut it into')
        ym = int(np.median(rows)) + 1 + depth // 2 - self.top - z
        box = (x0, int(min(rows)) + 1 - self.top - z, x1, int(max(rows)) + 1 + depth - self.top - z)
        return self._place('ledge', box, {'west': (x0 + 6, ym), 'east': (x1 - 6, ym)}, z, self._var('ledge', x0, ym))

    def path(self, pts, z: int, width: int = 12) -> Placed:
        """A footpath on tier z through screen points (a smooth curve), `width` px (12 a
        footpath, 16 to 24 a lane); its edges fray where it meets grass (fray_path)."""
        pts = [(float(a), float(b)) for a, b in pts]
        seg = []
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            n = int(max(abs(bx - ax), abs(by - ay))) + 1
            for i in range(n):
                u = i / max(1, n - 1)
                seg.append((ax + (bx - ax) * u, ay + (by - ay) * u))
        seg = np.array(seg)
        # smooth the polyline (a moving average), so a bend is a curve
        for _ in range(3):
            k = 9
            pad = np.concatenate([np.repeat(seg[:1], k, 0), seg, np.repeat(seg[-1:], k, 0)])
            seg = np.array([pad[i:i + 2 * k + 1].mean(0) for i in range(len(seg))])
        yy, xx = np.mgrid[0:self.Z.shape[0], 0:self.W]
        sy = yy - self.top - z
        m = np.zeros(self.Z.shape, bool)
        r = width / 2.0
        for cx, cy in seg[::2]:
            x0, x1 = int(cx - r - 1), int(cx + r + 2)
            y0, y1 = int(cy + self.top + z - r - 1), int(cy + self.top + z + r + 2)
            sub = (slice(max(0, y0), max(0, y1)), slice(max(0, x0), max(0, x1)))
            m[sub] |= (xx[sub] - cx) ** 2 + (sy[sub] - cy) ** 2 <= r * r
        m &= self.Z == z
        self.path_m |= m
        xs, ys = seg[:, 0], seg[:, 1]
        box = (int(xs.min() - r), int(ys.min() - r), int(xs.max() + r), int(ys.max() + r))
        return self._place('path', box, {'start': pts[0], 'end': pts[-1]}, z, self._var('path', int(xs[0]), int(ys[0])))

    def spring(self, x: int, y: int, z: int) -> Placed:
        """A spring on tier z at screen (x, y): a small stone-rimmed pool, and the brook it feeds
        running south across every lower tier until it falls the last face into a plunge pool
        (falls are found by rule, sized by their drop). The brook swells and narrows."""
        self.snap()
        v = self._var('spring', x, y)
        py0 = y + self.top + z
        R = self.Z.shape[0]
        ph = h01(v, 1) * 50
        xs = []
        base = int(self.Z.min())
        for py in range(py0, R):
            pc = (py // GRID) * GRID                     # the brook runs straight through a cell and jogs at its line
            xc = x + 4.0 * np.round((4.5 * np.sin((pc + ph) / 10.0) + 1.8 * np.sin((pc + ph) / 4.3)) / 4.0)
            col = int(round(xc))
            if not (0 <= col < self.W):
                break
            if self.Z[py, col] <= base:
                break
            w = 1.6 + 0.8 * (0.5 + 0.5 * np.sin((pc + ph) / 7.0))
            lo, hi = int(np.floor(xc - w)), int(np.ceil(xc + w))
            self.water_m[py, max(0, lo):min(self.W, hi)] = True
            xs.append((xc, py))
        # the spring's pool: a rounded rectangle 12 x 7 round its head
        yy, xx = np.mgrid[0:R, 0:self.W]
        import terrace
        box_ = (np.abs(xx + 0.5 - x) <= 6) & (yy >= py0 - 3) & (yy < py0 + 5)
        pool = terrace.rounded(box_, 2, 0) & (self.Z == z)
        self.water_m |= pool
        self.decals.append(dict(kind='spring', x=x, y=y, z=z, v=v))
        foot = xs[-1] if xs else (x, py0)
        return self._place('spring', (x - 12, y - 8, x + 12, foot[1] - self.top + 16), {'source': (x, y), 'outflow': (int(foot[0]), int(foot[1] - self.top))},
                           z, v)

    def pond(self, x0: int, y0: int, x1: int, y1: int, z: int = None) -> Placed:
        """A hollow with a pool: a rounded rectangle of still water on the ground at screen box
        x0..x1, y0..y1, with its north bank's small face, a light waterline, a dark band, and
        stones round its south and east banks."""
        z = self.z_at((x0 + x1) // 2, (y0 + y1) // 2) if z is None else z
        R = self.Z.shape[0]
        yy, xx = np.mgrid[0:R, 0:self.W]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0 + self.top + z
        q = np.abs((xx + 0.5 - cx) / ((x1 - x0) / 2.0)) ** 2.3 + np.abs((yy + 0.5 - cy) / ((y1 - y0) / 2.0)) ** 2.3
        q = q + 0.1 * (2 * vnoise2(xx, yy, 6.0, hashu(self.seed, x0, y0, 9)) - 1)
        self.water_m |= (q <= 1.0) & (self.Z == z)
        v = self._var('pond', x0, y0)
        self.decals.append(dict(kind='pond_rim', x0=x0, y0=y0, x1=x1, y1=y1, z=z, v=v))
        return self._place('pond', (x0 - 4, y0 - 4, x1 + 4, y1 + 4), {'inlet': ((x0 + x1) // 2, y0), 'outlet': ((x0 + x1) // 2, y1)}, z, v)

    def snow_corner(self, x0: int, y0: int, x1: int, y1: int, z: int) -> Placed:
        """A snow-capped corner of tier z (screen box): a drifted snow field with a soft
        scalloped margin (no single-pixel teeth), a cornice wherever it reaches a rim, drifts
        against the foot under it and half-buried rocks."""
        R = self.Z.shape[0]
        yy, xx = np.mgrid[0:R, 0:self.W]
        sy = yy - self.top - z
        v = self._var('snow_corner', x0, y0)
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        q = np.abs((xx + 0.5 - cx) / ((x1 - x0) / 2.0)) ** 3 + np.abs((sy + 0.5 - cy) / ((y1 - y0) / 2.0)) ** 3
        q = q + 0.38 * (2 * vnoise2(xx, sy, 15.0, hashu(v, 1)) - 1) + 0.1 * (2 * vnoise2(xx, sy, 5.0, hashu(v, 2)) - 1)
        self.snow_m |= grid_mask(q <= 1.0) & (self.Z >= z)      # a drift block on the grid, rounded corners
        return self._place('snow_corner', (x0, y0, x1, y1), {}, z, v)

    def boulders(self, x: int, y: int, size: str = 'm') -> Placed:
        """A rock outcrop or boulder cluster on the ground at screen (x, y): 's' one or two
        stones, 'm' three or four, 'l' five to seven with a large one; mossy where the biome is
        green. Blocks walking under its stones."""
        v = self._var('boulders', x, y)
        n = {'s': 2, 'm': 4, 'l': 7}[size]
        r = {'s': 5, 'm': 9, 'l': 14}[size]
        self.decals.append(dict(kind='boulders', x=x, y=y, n=n, r=r, v=v))
        return self._place('boulders', (x - r - 4, y - r - 2, x + r + 4, y + r // 2 + 4), {}, self.z_at(x, y), v)

    def scree(self, x0: int, x1: int, z_high: int, near_y: int = None) -> Placed:
        """A scree foot under the face below tier z_high from x0 to x1: stones thickest against
        the face, a few larger ones, thinning out over 10 to 14 px of ground."""
        r = self.rim_row((x0 + x1) // 2, z_high, near_y)
        z_low = int(self.Z[r + 1, (x0 + x1) // 2])
        y = r + 1 - self.top - z_low
        v = self._var('scree', x0, y)
        self.decals.append(dict(kind='scree', x0=x0, x1=x1, z_high=z_high, v=v))
        return self._place('scree', (x0, y - 4, x1, y + 16), {}, z_low, v)

    def ivy(self, x: int, z_high: int, width: int = 16, near_y: int = None) -> Placed:
        """A grass-lip overhang with ivy: a mat of leaves 10 to 24 px wide hanging from the lip
        of the face below tier z_high at column x, longest in the middle, lit on its left, with
        stringy strands under it and its shadow on the rock to its right."""
        r = self.rim_row(x, z_high, near_y)
        y = r - self.top - z_high
        v = self._var('ivy', x, y)
        self.decals.append(dict(kind='ivy', x=x, w=width, z_high=z_high, row=r, v=v))
        return self._place('ivy', (x - width // 2, y, x + width // 2, y + 24), {}, z_high, v)


PIECES = ('stair', 'ledge', 'path', 'spring', 'pond', 'snow_corner', 'boulders', 'scree', 'ivy')


def paint_decals(fr: Frame, world: World):
    """The dressing the pieces left: each drawn from its own hash, adapted to what lies under
    it (only on ground, only on rock, only along the face it belongs to)."""
    P = fr.P
    K = P['kind']
    T = world.T
    ground = (K == TOP) & np.isin(fr.tag, (TAG['ground'], TAG['path'], TAG['scree'], TAG['snow'])) & (P['ST'] == 0)
    ground &= ~near(fr.tag == TAG['water'], 2)
    rock = T['loose']
    green = T['top'] in GREEN
    for dc in world.decals:
        v = dc['v']
        if dc['kind'] == 'boulders':
            x, y, n, r = dc['x'], dc['y'], dc['n'], dc['r']
            pts = []
            for i in range(n):
                big = i == 0 and n >= 4
                rx = (r * 0.55 if big else 2.2 + 2.6 * h01(v, i, 1) * (r / 9.0) ** 0.5)
                ang = 2 * np.pi * h01(v, i, 2)
                dd = 0 if i == 0 else r * (0.35 + 0.55 * h01(v, i, 3))
                pts.append((y + dd * np.sin(ang) * 0.5, x + dd * np.cos(ang), rx * (world.s if not big else 1.0), i))
            for cy, cx, rx, i in sorted(pts):          # the nearer (lower) stones drawn last
                boulder(fr, cx, cy, rx, rx * (0.66 + 0.14 * h01(v, i, 4)), hashu(v, i, 5), ground | (fr.tag == TAG['scree']), rock,
                        moss=0.5 if green else 0.0)
        elif dc['kind'] == 'scree':
            face = (K == FACEK) & (P['ZH'] == dc['z_high'])
            dist = np.zeros(fr.shape, np.int32)
            for k in range(int(14 * world.s), 0, -1):
                dist = np.where(nb(face, -k, 0), k, dist)
            dist = np.where(dist > 0, np.maximum(1, np.round(dist / world.s)), 0)
            inx = (fr.X >= dc['x0']) & (fr.X < dc['x1'])
            pv = np.where(ground & inx & (dist > 0), 0.85 * np.clip(1.2 - dist / 12.0, 0, 1), 0.0)
            rid = sibs(rock)
            for x, y, hh in zip(*candidates(fr, max(3, int(3 * world.s)), hashu(v, 1), pv, inset=4)):
                if h01(hh, 5) < 0.75:
                    put_stamp(fr, PEBBLE[int(hh % np.uint32(4))], x, y, int(rid[int(hashu(hh, 4) % np.uint32(3))]), allow=ground, tag=TAG['scree'])
                else:
                    boulder(fr, x, y, (1.8 + 1.8 * h01(hh, 6)) * world.s, (1.4 + 1.1 * h01(hh, 7)) * world.s, hh, ground | (fr.tag == TAG['scree']), rock)
        elif dc['kind'] == 'spring':
            x, y = dc['x'], dc['y']
            for i in range(7):
                ang = np.pi * (-0.1 + 1.2 * i / 6.0)
                S_ = world.s
                sx = x + np.cos(ang) * 7.5 * S_
                sy = y + S_ + np.sin(ang) * 4.5 * S_
                if h01(v, i, 1) < 0.2:
                    continue
                boulder(fr, sx, sy, (1.6 + 1.1 * h01(v, i, 2)) * S_, (1.3 + 0.8 * h01(v, i, 3)) * S_, hashu(v, i, 4), ground, 'stone', moss=0.5 if green else 0.0)
            if green:
                for i in range(2):
                    fern(fr, int(x + (-8 + 16 * i + 3 * h01(v, i, 6)) * world.s), int(y - 2 * world.s), hashu(v, i, 5), ground, 0.9 * world.s)
        elif dc['kind'] == 'pond_rim':
            x0, y0, x1, y1 = dc['x0'], dc['y0'], dc['x1'], dc['y1']
            cx, cy, rx, ry = (x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) / 2.0, (y1 - y0) / 2.0
            wet = ground | (fr.tag == TAG['water'])
            n = int(8 + (rx + ry) / (3 * world.s))
            for i in range(n):
                u = (i + 0.5 + 0.4 * (h01(v, i, 5) - 0.5)) / n
                ang = np.pi * (-0.2 + 1.4 * u)
                if h01(v, i, 1) < 0.2:
                    continue
                sx = cx + np.cos(ang) * rx * 0.98
                sy = cy + np.sin(ang) * ry * 0.98
                boulder(fr, sx, sy, (2.0 + 1.6 * h01(v, i, 2)) * world.s, (1.5 + 1.1 * h01(v, i, 3)) * world.s, hashu(v, i, 4), wet, 'stone', moss=0.35 if green else 0.0)
            if green:
                fern(fr, int(x1 - 2), int(cy - 1), hashu(v, 9), ground, world.s)
        elif dc['kind'] == 'ivy' and hasattr(fr, 'face'):
            f = fr.face
            yy, xx, d, Hf = f['yy'], f['xx'], f['d'], f['Hf']
            on = np.abs(P['PY'][yy, xx] - dc['row']) <= 2 * world.s
            if on.any():
                _vines(fr, yy[on], xx[on], d[on], Hf[on], dc['x'], dc['w'], v, world.s)


def _vines(fr: Frame, yy, xx, d, Hf, x0: float, w: float, v, S_: float):
    """Ivy hanging from a lip (Matt, 21 Oct: organic strands, not rectangles): a short ragged
    cushion under the lip, and from it strands of different lengths, longest near the middle,
    each a thin stem that sways a little with leaf pairs along it, lit on their upper left, and
    a soft shadow on the rock east of every leaf."""
    X = fr.X[yy, xx].astype(np.float64)
    lf = sibs('leaf')
    n = max(2, int(round(w / (2.6 * S_))))       # x0 and w are in texels (the decal is scaled)
    LEAF = np.zeros(X.shape, bool)
    TL = np.zeros(X.shape, np.int64)
    STEM = np.zeros(X.shape, bool)
    # the cushion: 2 to 5 world px deep, scalloped, narrowing at both ends
    dx0 = (X + 0.5 - x0) / (w / 2)
    cush = (np.abs(dx0) < 1) & (d <= (2.0 + 3.0 * vnoise1(X, 3.0 * S_, hashu(v, 21)) * np.sqrt(np.clip(1 - dx0 ** 2, 0, 1))) * S_)
    LEAF |= cush
    TL = np.where(cush, np.where(d <= 1.2 * S_, 4, np.where(dx0 < 0.1, 3, 2)), TL)
    for i in range(n):
        hi = hashu(v, i, 22)
        xi = x0 - w / 2 + (i + 0.5) * w / n + 0.8 * S_ * (h01(hi, 1) - 0.5)
        mid = 1 - abs(2 * (i + 0.5) / n - 1)
        Li = Hf * (0.2 + 0.55 * mid * h01(hi, 2) + 0.15 * h01(hi, 3))
        if h01(hi, 4) < 0.2:
            Li = Li * 0.4
        ph = 6.28 * h01(hi, 5)
        sway = 0.9 * S_ * np.sin(d / (5.0 * S_) + ph)
        cx = xi + sway
        stem = (np.abs(X + 0.5 - cx) <= 0.5 * max(1.0, S_ * 0.6)) & (d <= Li) & (d > 2 * S_)
        STEM |= stem
        step_ = 3.0 * S_
        k = np.floor(d / step_)
        side = np.where(np.mod(k + i, 2) == 0, -1.0, 1.0)
        lx = cx + side * 1.1 * S_
        ly = (k + 0.5) * step_
        rx = (1.4 + 0.8 * h01(hi, k.astype(np.int64), 6)) * S_
        ry = 0.85 * rx
        q = ((X + 0.5 - lx) / rx) ** 2 + ((d - ly) / ry) ** 2
        leaf = (q <= 1.0) & (ly <= Li) & (d > 1.5 * S_) & (h01(hi, k.astype(np.int64), 7) < 0.85)
        lt = np.where((X + 0.5 < lx) & (d < ly), 4, np.where((X + 0.5 > lx) & (d > ly), 2, 3))
        TL = np.where(leaf & ~LEAF, lt, TL)
        LEAF |= leaf
    STEM &= ~LEAF
    shp = fr.shape
    M = np.zeros(shp, bool)
    M[yy[LEAF | STEM], xx[LEAF | STEM]] = True
    sh = (nb(M, 0, -1) | nb(M, -1, -1)) & ~M & np.isin(fr.tag, (TAG['rock'], TAG['recess']))
    fr.T[sh] = np.where(fr.T[sh] == EDGE, EDGE, np.maximum(0, fr.T[sh] - 1))
    ly_, lx_ = yy[LEAF], xx[LEAF]
    fr.F[ly_, lx_] = np.where(TL[LEAF] >= 4, lf[1], np.where(TL[LEAF] <= 2, lf[2], lf[0]))
    fr.T[ly_, lx_] = TL[LEAF]
    fr.tag[ly_, lx_] = TAG['leaf']
    sy_, sx_ = yy[STEM], xx[STEM]
    fr.F[sy_, sx_] = lf[2]
    fr.T[sy_, sx_] = 2
    fr.tag[sy_, sx_] = TAG['leaf']


def walk_mask(r: 'Render') -> np.ndarray:
    """What can be walked in a render (screen px): the tops that are not water, not a stone or
    a plant that blocks, and every stair. For a piece, crop it to the piece's box."""
    fr = r.fr
    x0, y0, x1, y1 = r.crop
    K = fr.P['kind']
    ok = ((K == TOP) & ~np.isin(fr.tag, (TAG['water'], TAG['scree'], TAG['tree'], TAG['side'], TAG['foam']))) | (fr.P['ST'] == 1)
    return ok[y0:y1, x0:x1]


# ---- the figure for scale ---------------------------------------------------------------------
def figure(fr: Frame, name: str, foot_x: int, foot_y: int):
    """A resident (an adult, 25 px) standing with its feet at (foot_x, foot_y), with a contact
    shadow: only for the demos, to judge the scale."""
    p = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')  # ledger: compare (scale figure)
    S_ = fr.world.s
    foot_x, foot_y = int(round(foot_x * S_)), int(round(foot_y * S_))
    im = Image.open(p).convert('RGBA')
    im = im.resize((int(round(im.width * S_ / 4)), int(round(im.height * S_ / 4))), Image.NEAREST)
    a = np.asarray(im)
    ys, xs = np.nonzero(a[..., 3] > 127)
    h, w0 = ys.max() + 1, (xs.min() + xs.max()) // 2
    # the colours of the sprite are kept as they are: write them into spare palette slots
    for y, x in zip(ys, xs):
        X, Y = foot_x + x - w0 - fr.x0, foot_y + y - h - fr.y0
        if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1]:
            fr.extra[(Y, X)] = tuple(int(v) for v in a[y, x, :3])
            fr.tag[Y, X] = TAG['figure']
    for dx in range(-int(4 * S_), int(4 * S_) + 1):
        X, Y = foot_x + dx - fr.x0, foot_y - fr.y0
        if 0 <= Y < fr.shape[0] and 0 <= X < fr.shape[1] and fr.tag[Y, X] != TAG['figure']:
            fr.T[Y, X] = max(0, min(fr.T[Y, X], 5) - (2 if abs(dx) < 3 * S_ else 1))


# ---- the demos: one screen each, to copy ------------------------------------------------------
W_DEMO, H_DEMO = 320, 384


def _plan_rows(top):
    return np.arange(H_DEMO + top)[:, None], np.arange(W_DEMO)[None, :]


def demo_highland(seed: int = 3, density: float = 1.0) -> tuple:
    """The polished swatch, built only from the kit and the pieces (one screen, to copy): a
    meadow (z 0) under a 64 px cliff to the upper tier (64) with a ledge path (32) cut along
    its west half, a stair from the meadow up through the ledge's face, the footpath from the
    stair's foot, a spring on the upper tier whose brook falls the cliff into a plunge pool,
    a 32 px step to the summit (96) with a snow-capped corner, ivy over two lips, scree and
    boulders at the feet."""
    plan = Plan(W_DEMO, H_DEMO, 'highland', seed=seed)
    plan.tier(64, [(-20, 186), (60, 182), (120, 190), (180, 196), (240, 188), (300, 196), (340, 192)])
    plan.tier(96, [(150, 64), (200, 70), (260, 62), (340, 70)], x0=168)
    led = plan.ledge(0, 176, 64, depth=40, near_y=190)
    st = plan.stair(80, 32, width=40)
    plan.path([st.attach['foot'], (100, 300), (124, 340), (118, H_DEMO + 8)], z=0)
    plan.spring(236, 132, 64)
    plan.snow_corner(226, -16, 350, 76, 96)
    plan.ivy(30, 64, 18, near_y=190)
    plan.ivy(292, 64, 16)
    plan.ivy(206, 96, 12)
    plan.scree(176, 320, 64)
    plan.boulders(36, 312, 'l')
    plan.boulders(284, 300, 'm')
    plan.boulders(184, 282, 's')
    w = plan.world(density)
    hx = 132
    return w, ('hiker', hx, led.attach['west'][1] + 6)


W_PILOT, H_PILOT = 300, 180


def demo_pilot(seed: int = 3, density: float = 2.0) -> tuple:
    """The pilot cliff for the 2x screen (Matt's c-tiles pick, 21 Oct): one screen-wide band
    of highland, 300 x 180 world px. The meadow (z 0) under a 64 px cliff to the upper tier
    (64); a ledge path (32) cut along the west half of the face; a stone stair from the meadow
    up to the ledge, flush at its head and landing on the footpath at its foot; a spring on
    the upper tier whose brook falls the cliff into a stone-rimmed plunge pool; a snow-capped
    corner at the north-east; ivy over the lip; scree and boulders at the foot. Clean ground:
    flat fills, a few large soft blotches, sparse clumped tufts. Returns the world and a
    dict of attach points in world px (screen x, y of the ground, and its z)."""
    plan = Plan(W_PILOT, H_PILOT, 'highland', seed=seed)
    plan.tier(64, [(-20, 44), (50, 40), (110, 46), (170, 60), (230, 56), (320, 64)], lobes=0.5)
    led = plan.ledge(14, 158, 64, depth=40, near_y=48)
    st = plan.stair(64, 32, width=32)
    plan.path([st.attach['foot'], (90, 160), (110, 176), (104, H_PILOT + 8)], z=0)
    sp = plan.spring(212, 16, 64)
    plan.snow_corner(238, -34, 326, 30, 64)
    plan.ivy(176, 64, 20)
    plan.ivy(272, 64, 18)
    plan.scree(170, 300, 64)
    plan.boulders(30, 168, 'm')
    plan.boulders(262, 160, 'm')
    plan.boulders(160, 170, 's')
    w = plan.world(density)
    pts = {'stair_foot': st.attach['foot'], 'stair_head': st.attach['head'],
           'ledge_west': led.attach['west'], 'ledge_east': led.attach['east']}
    for k, v in list(sp.attach.items()):
        pts['spring_' + k] = v
    return w, pts


def _rle(row) -> list:
    out, prev, n = [], None, 0
    for v in row.tolist():
        if v == prev:
            n += 1
        else:
            if prev is not None:
                out.append([prev, n])
            prev, n = v, 1
    out.append([prev, n])
    return out


def write_pilot(out_dir: str, densities=(2.0, 1.5)) -> list:
    """The pilot cliff at each density: cliff-<d>x.png, its height mask and walk mask as PNG
    and JSON (run-length rows, art px), and the attach points of every placed piece (world px
    and art px). Masks are in art px of the matching picture."""
    import json
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for d in densities:
        tag_ = f'{d:g}'.replace('.', '_') + 'x'
        w, pts = demo_pilot(density=d)
        r = render(w)
        img = r.image()
        fr = r.fr
        x0, y0, x1, y1 = r.crop
        K = fr.P['kind'][y0:y1, x0:x1]
        zh = np.rint(fr.P['ZH'][y0:y1, x0:x1] / w.s).astype(np.int32)
        hgt = np.where(K == TOP, zh, 255).astype(np.uint8)          # top: z in world px; face: 255
        walk = walk_mask(r).astype(np.uint8)
        names = {f'cliff-{tag_}.png': img}
        Image.fromarray(hgt, 'L').save(os.path.join(out_dir, f'height-{tag_}.png'), optimize=False)
        Image.fromarray(walk * 255, 'L').save(os.path.join(out_dir, f'walk-{tag_}.png'), optimize=False)
        for n, im in names.items():
            im.save(os.path.join(out_dir, n), optimize=False)
        S_ = w.s
        pieces = [dict(kind=p.kind, z=p.z, box_world=list(p.box), box_art=[int(round(v * S_)) for v in p.box],
                       attach_world={k: list(v) for k, v in p.attach.items()},
                       attach_art={k: [int(round(v[0] * S_)), int(round(v[1] * S_))] for k, v in p.attach.items()})
                  for p in w.placed]
        meta = dict(density=d, art_size=[img.width, img.height], world_size=[W_PILOT, H_PILOT],
                    note='art px = world px x density; rows are run-length [value, count] pairs, top to bottom')
        with open(os.path.join(out_dir, f'height-{tag_}.json'), 'w') as f:
            json.dump(dict(meta, legend={'0..254': 'the ground seen here is a top (or a stair tread) at this z, world px',
                                         '255': 'a cliff face or the side of raised ground (not a floor)'},
                           tiers=sorted(set(int(v) for v in np.unique(hgt) if v != 255)),
                           rows=[_rle(row) for row in hgt]), f, separators=(',', ':'))
        with open(os.path.join(out_dir, f'walk-{tag_}.json'), 'w') as f:
            json.dump(dict(meta, legend={'1': 'walkable (tops, stairs, the path)', '0': 'blocked (faces, water, boulders, scree, trees, snow cornice sides)'},
                           rows=[_rle(row) for row in walk]), f, separators=(',', ':'))
        with open(os.path.join(out_dir, f'pieces-{tag_}.json'), 'w') as f:
            json.dump(dict(meta, attach_world={k: list(v) for k, v in pts.items()},
                           attach_art={k: [int(round(v[0] * S_)), int(round(v[1] * S_))] for k, v in pts.items()},
                           pieces=pieces), f, indent=1)
        written += [f'cliff-{tag_}.png', f'height-{tag_}.png', f'height-{tag_}.json', f'walk-{tag_}.png', f'walk-{tag_}.json', f'pieces-{tag_}.json']
    return written


def demo_meadow(seed: int = 6, density: float = 1.0) -> tuple:
    """The meadow, the second biome, from its own pieces: low earthy turf banks of 16 (soil
    layers, roots under a soft sod), timber steps through each bank, a footpath, a hollow with
    a reed-fringed pool, a spring on the top whose brook drops both banks, field stones."""
    plan = Plan(W_DEMO, H_DEMO, 'meadow', seed=seed)
    plan.tier(16, [(-20, 214), (80, 206), (160, 222), (240, 210), (340, 218)])
    plan.tier(32, [(100, 104), (180, 96), (260, 110), (340, 100)], x0=120)
    s1 = plan.stair(88, 16, width=32)
    s2 = plan.stair(184, 32, width=32)
    plan.path([s1.attach['foot'], (100, 290), (86, 340), (96, H_DEMO + 8)], z=0)
    plan.path([s1.attach['head'], (120, 170), (190, 150), s2.attach['foot']], z=16)
    plan.path([s2.attach['head'], (204, 60), (230, -8)], z=32)
    plan.pond(28, 276, 92, 312)
    plan.spring(272, 40, 32)
    plan.boulders(250, 300, 's')
    plan.boulders(36, 150, 'm')
    w = plan.world(density)
    return w, ('hiker', 150, 300)


def demo_coast(seed: int = 5, density: float = 1.0) -> tuple:
    """A headland in the coast's own edge set: a grass top (64) over a 64 px cliff of pale
    sandstone slabs on a dark basalt foot, a lower shelf (32) at the west, a beach (0), the
    sea, a stair from the beach to the shelf."""
    plan = Plan(W_DEMO, H_DEMO, 'coast', seed=seed)
    plan.tier(64, [(-20, 120), (40, 128), (80, 150), (120, 162), (160, 156), (200, 150), (240, 162), (280, 176), (340, 170)])
    plan.tier(32, [(-20, 236), (30, 240), (60, 232), (90, 222), (110, 216), (124, 216)], x1=124)
    st = plan.stair(40, 32, width=32)
    py, px = np.mgrid[0:plan.Z.shape[0], 0:plan.W]
    plan.water_m |= (py - plan.top > 300 + 14 * np.sin(px / 37.0) + 6 * np.sin(px / 11.0)) & (plan.Z == 0)
    plan.path([st.attach['foot'], (64, 280), (90, 296)], z=0, width=10)
    plan.scree(130, 300, 64)
    plan.boulders(250, 260, 'm')
    return plan.world(density), ('beachcomber', 200, 268)


def demo_canyon(seed: int = 7, density: float = 1.0) -> tuple:
    """A canyon wall in the Reach in the canyon's own edge set: a mesa top (80), a bench (40)
    and the floor (0), 40 px faces of red and buff slabs, a dry wash, a stair to the bench."""
    plan = Plan(W_DEMO, H_DEMO, 'canyon', seed=seed)
    plan.tier(80, [(-20, 60), (40, 70), (90, 96), (130, 104), (170, 92), (220, 78), (270, 84), (340, 96)])
    plan.tier(40, [(-20, 190), (30, 196), (70, 214), (120, 222), (160, 206), (200, 196), (250, 210), (300, 230), (340, 226)])
    st = plan.stair(208, 40, width=40)
    plan.path([st.attach['foot'], (240, 300), (300, 330), (340, 336)], z=0, width=12)
    plan.scree(0, 190, 40)
    plan.boulders(90, 300, 'l')
    return plan.world(density), ('prospector', 140, 300)


def demo_city(seed: int = 9, density: float = 1.0) -> tuple:
    """A city retaining wall in the city's own edge set: an upper street (40) behind a 40 px
    wall of dressed stone with a coping, the lower street (0), a stair between them."""
    plan = Plan(W_DEMO, H_DEMO, 'city', seed=seed)
    plan.tier(40, [(-20, 168), (60, 168), (100, 172), (140, 180), (180, 180), (220, 172), (260, 168), (340, 168)])
    plan.stair(136, 40, width=40)
    return plan.world(density), ('porter', 90, 290)


# ---- a region from the pieces: what a lane writes -----------------------------------------------
def demo_area(seed: int = 21, density: float = 1.0) -> tuple:
    """A 512 x 512 highland area built only from the kit and the pieces, the way a lane would
    build one (about twenty lines): a summit (96) in the north-east with snow on its corner, an
    upper tier (64) across the north, a ledge path along part of its cliff, the meadow (0) in
    the south with a hollow and its pool, a spring on the upper tier whose brook falls into a
    plunge pool, stairs where the paths meet the faces, boulders and scree at the feet."""
    plan = Plan(512, 512, 'highland', seed=seed)
    plan.tier(64, [(-20, 196), (80, 188), (170, 204), (260, 214), (360, 200), (450, 214), (540, 206)])
    plan.tier(96, [(300, 92), (380, 84), (460, 100), (540, 92)], x0=320)
    plan.tier(32, [(-20, 360), (60, 352), (120, 366), (150, 368)], x1=152)     # a low shelf in the south-west
    led = plan.ledge(168, 330, 64, depth=40)
    s1 = plan.stair(208, 32, width=40)                       # meadow up to the ledge
    s2 = plan.stair(296, 64, width=32, near_y=200)           # ledge up to the upper tier
    s3 = plan.stair(400, 96, width=32)                       # upper tier up to the summit
    s4 = plan.stair(64, 32, width=40)                        # meadow up to the south-west shelf
    plan.path([s1.attach['foot'], (226, 330), (190, 420), (220, 520)], z=0)
    plan.path([s4.attach['foot'], (90, 440), (150, 470), (196, 440)], z=0)
    plan.path([s2.attach['head'], (330, 150), (400, 160), s3.attach['foot']], z=64)
    plan.path([led.attach['west'], s1.attach['head']], z=32, width=10)
    plan.spring(120, 120, 64)
    plan.pond(360, 380, 440, 424)
    plan.snow_corner(420, -12, 524, 50, 96)
    plan.ivy(60, 64, 18)
    plan.ivy(470, 96, 14)
    plan.scree(330, 500, 64)
    plan.scree(10, 150, 32)
    for x, y, size in ((40, 470, 'l'), (300, 300, 'm'), (470, 330, 'm'), (140, 300, 's'), (330, 470, 's')):
        plan.boulders(x, y, size)
    return plan.world(density), ('hiker', 250, 300)


# ---- module, reuse and biome sheets -------------------------------------------------------------
def _host(biome: str, seed: int, w: int = 160, h: int = 160, face: int = None) -> Plan:
    """A small piece of ground to show a module on: the meadow (0) under one tier."""
    plan = Plan(w, h, biome, seed=seed)
    f = face or BIOMES[biome]['face']
    plan.tier(f, [(-20, 70 + 4 * (seed % 3)), (w // 2, 66 + 6 * (seed % 2)), (w + 20, 72)])
    return plan


def modules(seed: int = 31) -> list:
    """Each highland module alone on a small piece of ground: (title, plan, placed)."""
    out = []

    def add(title, fn, biome='highland', face=None):
        p = _host(biome, seed + len(out), face=face)
        pl = fn(p)
        out.append((title, p, pl if isinstance(pl, list) else [pl]))
    add('stair through a face (1 tier)', lambda p: p.stair(56, 32, width=40))
    def two(p):
        p.tier(64, [(-20, 44), (180, 40)])
        return p.stair(64, 64, width=32)
    add('stair through a face (2 tiers)', two)
    def ledge(p):
        p.tier(64, [(-20, 40), (180, 38)])
        return p.ledge(10, 150, 64, depth=24)
    add('ledge path', ledge)
    add('spring, fall and plunge pool', lambda p: p.spring(90, 30, 32))
    add('snow-capped corner', lambda p: p.snow_corner(60, -10, 170, 50, 32))
    add('boulder cluster s, m, l', lambda p: [p.boulders(30, 120, 's'), p.boulders(76, 124, 'm'), p.boulders(126, 128, 'l')])
    add('grass lip with ivy', lambda p: p.ivy(80, 32, 20))
    add('footpath bend', lambda p: p.path([(20, 160), (40, 110), (110, 120), (140, 80), (150, 20)], z=0))
    add('hollow with a pool', lambda p: p.pond(40, 100, 120, 140))
    add('scree foot', lambda p: p.scree(10, 150, 32))
    return out


def _marks(img: Image.Image, placed, scale: int, crop=(0, 0)):
    """Draw each piece's footprint (on the 8 px grid) and its attach points over a render."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for p in placed:
        x0, y0, x1, y1 = p.box
        d.rectangle([x0 * scale, y0 * scale, x1 * scale - 1, y1 * scale - 1], outline=(255, 236, 120))
        for name, (ax, ay) in p.attach.items():
            ax, ay = int(ax) * scale, int(ay) * scale
            d.line([ax - 4, ay, ax + 4, ay], fill=(255, 80, 200), width=2)
            d.line([ax, ay - 4, ax, ay + 4], fill=(255, 80, 200), width=2)
            d.text((ax + 5, ay - 10), name, fill=(255, 220, 245))


def module_sheet(seed: int = 31) -> Image.Image:
    """Every highland module at 2x with its footprint, attach points and walk mask."""
    from PIL import ImageDraw
    S = 2
    mods = modules(seed)
    cw, chh = 160 * S * 2 + 12, 160 * S + 26
    cols = 2
    rows = -(-len(mods) // cols)
    sheet = Image.new('RGB', (cols * (cw + 16) + 16, rows * (chh + 12) + 40), (34, 28, 36))
    d = ImageDraw.Draw(sheet)
    d.text((16, 12), 'Highland modules: each piece alone, 2x; yellow its footprint on the 8 px grid, pink its attach points; right, its walk mask (light: walkable)',
           fill=(240, 234, 222))
    for i, (title, plan, placed) in enumerate(mods):
        w = plan.world()
        r = render(w)
        im = r.image()
        big = im.resize((im.width * S, im.height * S), Image.NEAREST)
        _marks(big, placed, S)
        wm = walk_mask(r)
        wim = Image.fromarray(np.where(wm, 214, 60).astype(np.uint8)).convert('RGB').resize(big.size, Image.NEAREST)
        x = 16 + (i % cols) * (cw + 16)
        y = 40 + (i // cols) * (chh + 12)
        sheet.paste(big, (x, y + 18))
        sheet.paste(wim, (x + big.width + 12, y + 18))
        d.text((x, y + 2), title, fill=(240, 234, 222))
    return sheet


def reuse_sheet() -> Image.Image:
    """The same set of highland pieces (a stair, a spring with its fall, a boulder cluster, ivy
    and scree) placed in three spots of three different highland outlines: the same parts,
    never the same picture (each takes its variant from where it stands)."""
    from PIL import ImageDraw
    S = 2
    shots = []
    for k, (seed, rim, sx) in enumerate(((41, [(-20, 112), (60, 104), (120, 136), (200, 140), (300, 118)], 48),
                                          (42, [(-20, 140), (70, 120), (150, 100), (220, 124), (300, 112)], 120),
                                          (43, [(-20, 100), (90, 132), (170, 136), (240, 104), (300, 110)], 176))):
        plan = Plan(256, 256, 'highland', seed=seed)
        plan.tier(32, rim)
        st = plan.stair(sx, 32, width=40)
        plan.path([st.attach['foot'], (sx + 30, 220), (sx + 10, 270)], z=0)
        plan.spring((sx + 120) % 230 + 10, 40, 32)
        plan.boulders((sx + 80) % 220 + 18, 216, 'm')
        plan.ivy((sx + 170) % 230 + 12, 32, 16)
        plan.scree((sx + 60) % 200, (sx + 60) % 200 + 56, 32)
        shots.append(render(plan.world()).image())
    sheet = Image.new('RGB', (3 * (256 * S + 16) + 16, 256 * S + 60), (34, 28, 36))
    d = ImageDraw.Draw(sheet)
    d.text((16, 12), 'Reuse in one biome: the same five highland pieces in three spots of three outlines, 2x. Variants come from a hash of where each stands.',
           fill=(240, 234, 222))
    for i, im in enumerate(shots):
        sheet.paste(im.resize((im.width * S, im.height * S), Image.NEAREST), (16 + i * (256 * S + 16), 40))
    return sheet


def edges_sheet() -> Image.Image:
    """Highland and meadow side by side on the same outline: one grammar (the soft grid, the
    rim wobble and corners, the lit lip, the dark under-lip and foot, light from the upper left,
    the house palette), two edge sets (boulder cliff under a clean turf lip and rock steps;
    earthy turf bank with roots under a soft sod and timber steps). 3x."""
    from PIL import ImageDraw
    S = 3
    shots = []
    for biome in ('highland', 'meadow'):
        f = BIOMES[biome]['face']
        plan = Plan(192, 160, biome, seed=51)
        plan.tier(2 * f, [(-20, 40), (100, 34), (220, 44)], x0=96)
        plan.tier(f, [(-20, 92), (60, 86), (140, 98), (220, 92)])
        st = plan.stair(40, f, width=32)
        plan.path([st.attach['foot'], (60, 150), (50, 170)], z=0)
        plan.spring(150, 10, 2 * f)
        plan.boulders(150, 140, 's')
        shots.append((biome, render(plan.world()).image()))
    sheet = Image.new('RGB', (2 * (192 * S + 16) + 16, 160 * S + 66), (34, 28, 36))
    d = ImageDraw.Draw(sheet)
    d.text((16, 12), 'One grammar, two edge sets (3x): highland (left: boulder cliff, turf lip, rock steps) and meadow (right: earthy turf bank, sod and roots, timber steps)',
           fill=(240, 234, 222))
    for i, (b, im) in enumerate(shots):
        x = 16 + i * (192 * S + 16)
        sheet.paste(im.resize((im.width * S, im.height * S), Image.NEAREST), (x, 40))
        d.text((x, 40 + 160 * S + 6), b, fill=(240, 234, 222))
    return sheet


def _scale_decal(d: dict, s: float) -> dict:
    """A piece's dressing carried from world px to texels."""
    d = dict(d)
    for k in ('x', 'y', 'x0', 'y0', 'x1', 'y1', 'w', 'r', 'z', 'z_high', 'row'):
        if k in d:
            d[k] = int(round(d[k] * s))
    return d


DEMOS = {'highland': demo_highland, 'meadow': demo_meadow, 'coast': demo_coast, 'canyon': demo_canyon, 'city': demo_city}


def random_world(seed: int, width: int = W_DEMO, height: int = H_DEMO, table: str = 'highland', density: float = 1.0) -> World:
    """A random outline for the proofs: tiers of 32 rising to the north on a broad noise field,
    each level's mask rounded (terrace.rounded), so the faces are 32 or 64 px and the plan
    shapes lobe, bay and spur. Nothing in it is hand-placed."""
    top = 96
    PH = height + top
    py, px = np.mgrid[0:PH, 0:width]
    sy = py - top
    base = (1.0 - sy / height) * 4.0 + 0.1 + 2.6 * (fbm2(px, sy, 110.0, hashu(seed, 401), 2) - 0.5)
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
    return World(Zs, table, seed=seed, top=top, density=density)


def build(world: World, fig=None, box=None) -> Image.Image:
    r = render(world, box)
    fr = r.fr
    if fig:
        figure(fr, *fig)
    return r.image()


# ---- the checks ------------------------------------------------------------------------------------
RAMP_TONES = 0.85     # house-style 7, ruling of 20 Oct 17:30: ramp-built art passes tones at 85 %
ROCK_TONES = 0.5      # calm planar faces (Matt, 21 Oct 10:52; pilot review): tones at 50 %, shapes and dressing reported only
RIM_ON_GRID = 0.7     # the soft grid (Matt, 21 Oct 11:44): most of every rim on a cell line
GROUND_VARIETY = 4    # a clean lawn still shows its field, a patch tone and dressing in a 66 x 50 box


def best_box(mask: np.ndarray, w: int, h: int):
    """The w x h box holding the most of `mask` (a summed-area table, every second px)."""
    H, W = mask.shape
    ii = np.pad(mask.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    ys, xs = np.mgrid[0:H - h:2, 0:W - w:2]
    v = ii[ys + h, xs + w] - ii[ys, xs + w] - ii[ys + h, xs] + ii[ys, xs]
    i = int(np.argmax(v))
    y, x = int(ys.ravel()[i]), int(xs.ravel()[i])
    return (x, y, x + w, y + h), float(v.ravel()[i]) / (w * h)


def bar_check(img: Image.Image, box, kind: str, s: float = 1.0):
    """detail_bar.py's check, with the house ruling for ramp-built art (tones at 85 %). At a
    density s the picture's adult is 25 x s px, so it goes through the reference's own pipe
    from there: blown up (nearest) to the reference's adult height, through its JPEG quality,
    and brought to our scale by the most common colour in each block (detail_bar.to_scale),
    exactly as each reference was. Cleanliness compares area averages at our scale, as the
    references' were (ref_scale). Ground is judged for cleanliness (CLEAN_KINDS)."""
    import detail_bar as db
    ref = db.bar(kind)
    crop = img.convert('RGB').crop(tuple(box))
    if s == 1.0:
        ok, ours, lines = db.check_image(img, box, kind)
    else:
        q = ref.get('jpeg_quality')
        f = ref['adult_px'] / (db.ADULT * s)
        big = crop.resize((max(1, round(crop.width * f)), max(1, round(crop.height * f))), Image.NEAREST)
        if q:
            import io
            b_ = io.BytesIO()
            big.save(b_, 'JPEG', quality=q)
            b_.seek(0)
            big = Image.open(b_).convert('RGB')
        ours = db.counts(db.to_scale(big, ref['adult_px']))
        if kind in getattr(db, 'CLEAN_KINDS', ()) and 'clean' in ref:
            ours['clean'] = db.clean_counts(crop.resize((max(1, round(crop.width / s)), max(1, round(crop.height / s))), Image.BOX))
        ok, _lines = db.judge(ours, ref)
    if kind in getattr(db, 'CLEAN_KINDS', ()):
        return ok, ok, ours, ref
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
        if len(ys) < 14:
            continue
        we = []
        for y in np.unique(ys):
            row = np.sort(xs[ys == y])
            if len(row) >= 4:
                q = max(1, len(row) // 4)
                we.append(L[y, row[:q]].mean() - L[y, row[-q:]].mean())
        if we:
            vals.append(100 * float(np.mean(we)))
    return float(np.mean(vals)) if vals else 0.0


def proof(img: Image.Image, tag: np.ndarray) -> dict:
    """The detail bar on the barest rock (stone-wall and face) and the most open ground of a
    render, and the lint on the whole of it."""
    rock_box, rf = best_box(np.isin(tag, (TAG['rock'], TAG['recess'], TAG['soil'])), 50, 34)
    ground_box, gf = best_box(tag == TAG['ground'], 66, 50)
    out = {'rock_box': rock_box, 'rock_share': rf, 'ground_box': ground_box, 'ground_share': gf}
    for kind, box in (('stone-wall', rock_box), ('face', rock_box), ('ground', ground_box)):
        out[kind] = bar_check(img, box, kind)
    out['lint'] = lint(img)
    out['lint_rock'] = lint(img.crop(rock_box))
    return out


def seam_test(seed: int = 11, size: int = 512, tile: int = 256, density: float = 1.0) -> dict:
    """Render a random world whole and as four tiles; every tile must equal its crop of the
    whole, pixel for pixel (so two adjacent tiles meet with no seam). Sizes in texels."""
    w = random_world(seed, int(size / density), int(size / density), density=density)
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


GRAMMAR_HEIGHTS = (12, 16, 32, 40)     # world-rules 3.2: the only face heights between tiers


def rim_steps(r: 'Render') -> tuple:
    """The shared rim rule, measured on a render (eastward-edges.md 1, the soft grid): along
    every face the row where the face starts lies on a cell line of the 8 world px grid (a
    1 px wobble allowed) except where a rounded corner turns, and moves between neighbouring
    columns in single texel steps. Returns (steps, steps over 1 texel, the share of rim
    columns on the grid)."""
    fr = r.fr
    f = getattr(fr, 'face', None)
    if f is None:
        return 0, 0, 1.0
    first = f['d'] == 1
    X = fr.X[f['yy'][first], f['xx'][first]]
    Y = fr.Y[f['yy'][first], f['xx'][first]]
    lid = f['lid'][first]
    S_ = fr.world.s
    cell = GRID * S_
    on = np.abs(Y - np.round(Y / cell) * cell) <= max(1.0, S_)
    n = big = 0
    for L in np.unique(lid):
        m = lid == L
        order = np.argsort(X[m], kind='stable')
        xs, ys = X[m][order], Y[m][order]
        if len(xs) < 2:
            continue
        adj = np.diff(xs) == 1
        dy = np.abs(np.diff(ys))
        steps = adj & (dy > 0)
        n += int(steps.sum())
        big += int((steps & (dy > 1)).sum())
    return n, big, float(on.mean()) if len(on) else 1.0


def grammar(name: str, r: 'Render', world: World) -> tuple:
    """The shared grammar on one render (Matt, 21 Oct 10:09: "make sure everything has the same
    sort of soft grid and the visual art style is consistent"; 10:52: "i want it to be cleaner,
    like eastward"): ground judged for cleanliness (detail_bar), rock with the house ruling as
    stone-wall (the face kind's shape and dressing minimums reward noise and are reported only),
    the lint (palette, lone pixels, dither), light from the west on every rock form, rims in
    single texel steps with no long straight run, the lip and the foot within Eastward's widths
    at the density, the tier heights. Prints a line per test."""
    ok = True
    img = r.image()
    _f, _t, tag = r.arrays()
    T, E, M, S_ = world.T, world.E, world.M, world.s
    low = T['face'] <= 16
    rock_tags = (TAG['rock'], TAG['recess'], TAG['soil'])
    bw, bh, gw, gh = int(50 * S_), int(34 * S_), int(66 * S_), int(50 * S_)
    if low:      # a low bank is judged with its lip and foot, as Eastward's farm ledge ('rim')
        near_face = near(np.isin(tag, rock_tags), int(6 * S_))
        rock_box, rf = best_box(near_face & ~np.isin(tag, (TAG['water'], TAG['figure'])), bw, bh)
        kinds = [('rim', True)]
    else:
        rock_box, rf = best_box(np.isin(tag, rock_tags), bw, bh)
        kinds = [('stone-wall', True), ('face', False)]
    if T['built']:
        kinds = [('stone-wall', True)]
    ground_box, gf = best_box(np.isin(tag, (TAG['ground'],)), gw, gh)
    print(f'{name}: rock box {rock_box} ({100 * rf:.0f} %), ground box {ground_box} ({100 * gf:.0f} %)')
    gkind = 'paving' if T['top'] == 'stone' else 'ground'
    for kind, box, gate in [(k, rock_box, g) for k, g in kinds] + [(gkind, ground_box, True)]:
        if kind == 'ground' and gf < 0.85:
            print(f'  {kind:10s} skipped: no open ground of 66 x 50 world px in this picture')
            continue
        house, strict, ours, ref = bar_check(img, box, kind, S_)
        if kind != 'ground':     # rock and paving: as clean as the reference, tones at 75 %; the shape and
            import detail_bar as db      # dressing minimums reward noise, so they are reported (Matt, 10:52)
            house = ours['tones'] >= ROCK_TONES * ref['tones']
            if S_ == 1.0:     # isolated and cluster gate at 1x; at higher densities they are reported: the
                # stone-wall references are Eastward's larger boulders (2.3), and Matt's cobbles (8 to 14 art px
                # at 2x, 21 Oct) fall apart under the bar's 2:1 mode downsample. The lint gates lone px natively.
                house = house and ours['isolated'] <= ref['isolated'] + db.ISOLATED_MARGIN and ours['cluster'] >= db.CLUSTER_SHARE * ref['cluster']
        if kind == 'ground' and 'clean' in ours:
            # ground (Matt, 21 Oct 10:52 and the pilot review): clean like Eastward, and not flat.
            # The per-patch tones minimum rewards mottle, so it is reported; the box must show
            # its field, a patch tone and dressing (GROUND_VARIETY colours of 0.5 % or more)
            import detail_bar as db
            c, rc = ours['clean'], ref['clean']
            x0b, y0b, x1b, y1b = box
            arr = np.asarray(img.convert('RGB'))[y0b:y1b, x0b:x1b].reshape(-1, 3)
            _v, cnt = np.unique(arr, axis=0, return_counts=True)
            variety = int((cnt >= 0.005 / S_ * len(arr)).sum())     # stamps are texel-sized: their share falls with density
            house = (c['edges'] <= rc['edges'] + db.CLEAN_EDGES and c['lone'] <= rc['lone'] + db.CLEAN_LONE
                     and c['top2'] >= db.CLEAN_TOP2 * rc['top2'] and c['colours'] <= db.CLEAN_COLOURS * rc['colours'] + 1
                     and variety >= GROUND_VARIETY)
            ours['variety'] = variety
            print(f'  {kind:10s} clean: edges {c["edges"]:.3f}/{rc["edges"]:.3f} lone {c["lone"]:.3f}/{rc["lone"]:.3f} '
                  f'top2 {c["top2"]:.2f}/{rc["top2"]:.2f} colours {c["colours"]:4.1f}/{rc["colours"]:4.1f}; '
                  f'variety {ours["variety"]} (>= {GROUND_VARIETY}); tones {ours["tones"]:4.1f}/{ref["tones"]:4.1f} (report)  {"PASS" if house else "FAIL"}')
        else:
            print(f'  {kind:10s} tones {ours["tones"]:5.1f}/{ref["tones"]:5.1f} shapes {ours["shapes"]:5.1f}/{ref["shapes"]:5.1f} '
                  f'dressing {ours["dressing"]:5.1f}/{ref["dressing"]:5.1f} isolated {ours["isolated"]:.3f}/{ref["isolated"]:.3f} '
                  f'cluster {ours["cluster"]:4.2f}/{ref["cluster"]:4.2f}  {("PASS" if house else "FAIL") if gate else ("(report) " + ("pass" if house else "below"))}')
        if gate:
            ok &= house
    m = lint(img)
    light = crag_light(r)
    bad = [x for x in m['misses'] if x in ('palette', 'speckle', 'dither')]
    bad += ['light-west'] if light <= 0 else []
    n, rb, on_grid = rim_steps(r)
    bad += [f'off-grid {100 * on_grid:.0f} %'] if on_grid < RIM_ON_GRID else []
    fl = getattr(r.fr, 'fringeL', np.zeros(1))
    rm = getattr(r.fr, 'rim_mat', np.zeros(np.shape(fl)))
    lip_max = int(fl[rm != MAT_SNOW].max()) if np.any(rm != MAT_SNOW) else 0
    k = M['k']
    bad += [f'lip {lip_max}'] if lip_max > max(M['lip'][1], int(round(6 * k))) else []
    bad += [f'foot {M["foot"]}'] if M['foot'] > int(round(7 * k)) + 1 else []
    bad += [f'tier {T["face"]}'] if T['face'] not in GRAMMAR_HEIGHTS else []
    print(f'  grammar    {m["colours"]} colours, {100 * m["on_house"]:.1f} % house palette, {100 * m["isolated"]:.1f} % lone px, '
          f'{100 * m["checker"]:.2f} % dither, west minus east {light:+.1f} on each rock form, rim steps {n - rb}/{n} of 1 texel, '
          f'{100 * on_grid:.0f} % of rim columns on the grid, lip <= {lip_max}, foot {M["foot"]}, side {M["side"]} texels, '
          f'tier {T["face"]}  {"PASS" if not bad else "FAIL " + " ".join(bad)}')
    return ok and not bad


CHECK_DENSITIES = (1.0, 1.5, 2.0)


def run_check(densities=None) -> int:
    """The seam test, biome ownership and the grammar, at each density: every biome's demo at
    1x, the highland and meadow demos and a random outline at the higher densities."""
    ok = True
    faults = check_biomes()
    print('biomes: every biome draws with its own edge set and owns its pieces:', 'PASS' if not faults else 'FAIL ' + '; '.join(faults))
    ok &= not faults
    for d in densities or CHECK_DENSITIES:
        print(f'---- density {d:g} (texels a world px)')
        t = seam_test(density=d)
        print(f"seam: tiles differ from the whole by {t['diff_px']} px; the seam between two adjacent tiles: {t['seam_px']} px")
        ok &= t['seam_px'] == 0 and not any(t['diff_px'].values())
        for seed in (PROOF_SEEDS if d == 1.0 else PROOF_SEEDS[:1]):
            w = random_world(seed, density=d)
            ok &= grammar(f'random outline {seed} (highland, {d:g}x)', render(w), w)
        for name, fn in DEMOS.items():
            if d != 1.0 and name not in ('highland', 'meadow'):
                continue
            w, _fig = fn(density=d)
            ok &= grammar(f'demo {name} ({d:g}x)', render(w), w)
            foreign = [p.kind for p in getattr(w, 'placed', []) if p.kind not in w.T['pieces']]
            if foreign:
                print(f'  pieces     {name} places pieces it does not own: {foreign}  FAIL')
                ok = False
    print('cliff core check:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


PROOF_SEEDS = (1, 2, 3)


def outputs() -> dict:
    """Everything the generator writes (art-repro reproduces these bytes): name -> (picture,
    whether a 3x copy is written too). The five biome demos, the 512 px highland area, the
    three random-outline proofs, and the module, reuse and edge sheets (already enlarged)."""
    out = {}
    for name, fn in DEMOS.items():
        w, fig = fn()
        r = render(w)
        figure(r.fr, *fig)
        out[name] = (r.image(), True)
    w, fig = demo_area()
    r = render(w)
    figure(r.fr, *fig)
    out['area'] = (r.image(), True)
    for seed in PROOF_SEEDS:
        out[f'proof-{seed}'] = (render(random_world(seed)).image(), True)
    out['modules'] = (module_sheet(), False)
    out['reuse'] = (reuse_sheet(), False)
    out['edges'] = (edges_sheet(), False)
    return out


def compare(refdir: str, path: str):
    """Ours beside Eastward only (eastward-edges.md; Matt, 21 Oct 09:23), every image at an
    adult of 25 px (detail_bar.to_scale), 3x: the highland demo and the meadow demo beside
    Eastward's rock cliff with a grass top (Octopia, 12), its grass ledges and stair (13) and
    its pond (37, Octopia-7, shown at the game's 3.3 zoom). The screenshots are official and
    stay out of the repository, and so does this picture: write it to a scratch folder."""
    import detail_bar as db
    from PIL import ImageDraw

    def ref(p, box, adult):
        im = Image.open(os.path.join(refdir, p)).convert('RGB').crop(box)
        key = db.to_scale(im, adult)
        rgb = np.stack([(key >> 8) * 16 + 8, ((key >> 4) & 15) * 16 + 8, (key & 15) * 16 + 8], -1).astype(np.uint8)
        return Image.fromarray(rgb, 'RGB')

    S = 3
    up = lambda im: im.resize((im.width * S, im.height * S), Image.NEAREST)  # noqa: E731
    ours = []
    for name in ('highland', 'meadow'):
        w, fig = DEMOS[name]()
        r = render(w)
        figure(r.fr, *fig)
        ours.append((up(r.image()), f'ours: {name} (cliff_core.demo_{name})'))
    shots = [(up(ref('eastward/12.jpg', (0, 0, 960, 700), 162.0)), 'Eastward Octopia: rock cliff with a grass top'),
             (up(ref('eastward/13.jpg', (0, 600, 1300, 1000), 162.0)), 'Eastward Octopia: grass ledges, a stair, a canal bank'),
             (up(ref('eastward/37.jpg', (0, 120, 700, 900), 178.0)), 'Eastward Octopia: a pond rimmed with stones')]
    g = 14
    left_w = sum(o.width for o, _ in ours) + g
    right_w = max(im.width for im, _ in shots)
    W_ = g + left_w + g + right_w + g
    H_ = 34 + max(max(o.height for o, _ in ours) + 26, sum(im.height + 26 for im, _ in shots))
    out = Image.new('RGB', (W_, H_), (34, 28, 36))
    d = ImageDraw.Draw(out)
    d.text((g, 10), 'Edges and the soft grid beside Eastward only, every image at an adult of 25 px, 3x', fill=(240, 234, 222))
    x = g
    for o, t in ours:
        out.paste(o, (x, 34))
        d.text((x, 34 + o.height + 6), t, fill=(240, 234, 222))
        x += o.width + g
    y = 34
    for im, t in shots:
        out.paste(im, (g + left_w + g, y))
        d.text((g + left_w + g, y + im.height + 4), t, fill=(240, 234, 222))
        y += im.height + 26
    out.save(path)


def main(argv) -> int:
    if '--check' in argv:
        ds = [float(argv[argv.index('--density') + 1])] if '--density' in argv else None
        return run_check(ds)
    if '--pilot' in argv:
        i = argv.index('--pilot')
        ds = [float(v) for v in argv[i + 2:]] or [2.0, 1.5]
        print('pilot cliff: wrote', ', '.join(write_pilot(argv[i + 1], ds)))
        return 0
    if '--compare' in argv:
        i = argv.index('--compare')
        compare(argv[i + 1], argv[i + 2])
        return 0
    out_dir = argv[0] if argv and not argv[0].startswith('--') else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    pics = outputs()
    for name, (img, triple) in pics.items():
        img.save(os.path.join(out_dir, f'{name}.png'), optimize=False)
        if triple:
            img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(os.path.join(out_dir, f'{name}-3x.png'), optimize=False)
    print('cliff core: wrote', len(pics), 'pictures to', os.path.relpath(out_dir, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

"""The terrace toolkit: ground at several heights on the soft 8 px grid.

docs/vision/verticality.md, 4a (the toolkit) and 4f (grid-led terrain, "Side faces"). Every
region's generator calls this instead of drawing its own cliffs; owners adopt it zone by zone.

The model. A zone gives a tier map on the 8 px grid: one integer per cell (40 x 72 for a
zone), the tier whose top surface the camera sees there. Tiers are ground, not walk levels:
where a higher tier ends to the south its face hangs below the rim, carved from the lower
ground (32 px per level by default, 40 in the city), so the map is what the camera sees and
the tops are drawn already offset by their height. `from_plan()` converts a plan height map
(where each tier stands on the ground) into that screen map.

What `build()` paints on the ground canvas:
- corners rounded by one cell (the grid mask closed, then opened, with a small disc), so
  straight runs stay exactly on grid lines; all roughness lives inside the edge cells;
- south faces in a material (earth, stone, concrete, timber, sandstone), each lit from the
  upper left, with a lip (a scalloped grass overhang of 1 to 3 px on earth, a coping on
  built faces), a dark damp foot and tall grass along it;
- side faces (anything facing west or east) as a band 5 px wide (0.2 of an adult, as
  Eastward draws them: measured 0.17 to 0.21 A on its Strange Forest ledges): the lip wraps
  the corner and runs down the side in small scallops; the band is a column of lumps, lit
  when it faces west and in the two darkest tones when it faces east, with a dark outline
  where it meets the ground; outer corners wrap the face's clods or courses round the
  radius, narrowing; inner corners meet in a shaded crease; a band always ends on ground;
- cast shadows down and to the right (8 px, stepped: 2 strong, 3 medium, 3 dithered), so
  an east-facing strip throws a stepped shadow on the lower ground east of it and a
  west-facing one keeps a 1 px contact line;
- stairs cut through a face (timber or stone; 40 px open between 4 px cheeks, 4 px risers,
  8 px landings, the west cheek lit and the east cheek dark), ramps built against a face
  (rise 1 in 3, at least 24 wide), and streams that fall straight down a face into a pool.

What it returns (`Terrace`): the walk blocking (face bands and strips blocked, stairs and
ramps open, a hidden drop behind each back rim blocked), the per-4 px-cell tier map for the
renderer and lint (`zoneTier`: digits for tiers, `f` a face, `s` a stair or ramp), the
links between levels, the water pixels (the falls included, so water_flow.py animates
them), and rail runs for built rims. `check()` runs the toolkit's own lint on the result.

Edge dressing is on by default (dress=True), so any zone that uses the toolkit gets it: earth
faces as packed clods (Eastward's cobbled banks) with mossy clods and embedded rocks, built
faces weathered (grime, pits, rain streaks, cracks, moss low down), tall grass breaking
rims, corners, feet and banks, loose rocks at the feet and corners, soft shade and worn
ground pooled along every foot and deeper in inner corners. The detail bar (detail_bar.py,
Matt 20 Oct: Eastward's level of detail "has to be reached") checks it: `--sheet OUT --bar`.

Everything is deterministic (hash noise from pixel.py, no randomness), so art-repro holds.

HOWTO: a zone's terrain as a map
    MAP = '''
    0000000000000000000000000000000000000000      one character per 8 px cell, 40 a row
    0001111111111111000000000000000000000000      1: a tier one level up (its top as seen)
    0001111111111111000000000000000000000000
    000000SSSSSS0000000000000000000000000000      its face hangs in the 4 rows below its
    000000SSSSSS0000000000000000000000000000      south edge (32 px); S cuts a timber stair
    000000SSSSSS0000000000000000000000000000      through it (Z for stone), 6 cells wide
    000000SSSSSS0000000000000000000000000000
    ...                                           72 rows; ~ water; R a ramp cut
    '''
    ground = Canvas(320, 576)  # paint the zone's own ground first and pass tops=False,
    t = terrace.build(ground, **terrace.from_ascii(MAP, MATERIALS, {'t': 16}), tops=False)
    # or let it paint grass (tops=True, the default)
    # then: t.blocked into the zone's blocked ground, t.water into WATER_MASKS,
    # t.tiers for zoneTier, terrace.one_tier(t, foot box) before placing a prop.
TEST_MAP below is a complete example.

Run: python3 scripts/art/terrace.py --sheet OUT.png [--bar]   (the test zone at 1x, 3x, night,
     walk; --bar judges it against the Eastward detail bar, detail_bar.py)
     python3 scripts/art/terrace.py --check            (build the test zone and lint it)
"""
from __future__ import annotations

import math
import os
import sys
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from materials import INK, MATERIALS  # noqa: E402
from pixel import Canvas, hex_rgba, noise2, smooth_noise  # noqa: E402

GRID = 8          # the terrain grid (zone px)
CELL = 4          # the walk grid
FACE = 32         # a tier's face (valley, isles, west, garden yard)
FACE_CITY = 40
STRIP = 5         # a side band, lip to outline: Eastward's measure 0.2 of an adult (A = 25)
SHADOW = 8        # cast shadow: constant whatever the height; 3 strong, 3 medium, 2 dithered
HEIGHTS = (12, 16, 32, 40)   # the only face heights: a low step or a tier (soft-grid research 6.1)
STAIR_W = 40      # open width between the cheeks
CHEEK = 4
RISER = 4
LANDING = 8
RAMP_W = 24
ROUND = 6         # corner radius: one cell
ROUND_IN = 4      # inner corners: a tighter crease

# what each pixel is
TOP, FACE_K, STRIP_K, STAIR_K, CHEEK_K, RAMP_K, FALL_K = range(7)
FACE_LIKE = (FACE_K, STRIP_K, CHEEK_K, FALL_K)

RAMPS = {
    'earth': None,                     # 6 tones: SOIL below
    'stone': MATERIALS['ashlar'],      # 6
    'concrete': MATERIALS['ash'],      # 5
    'timber': MATERIALS['wood'],       # 5
    'sandstone': MATERIALS['desert'],  # 6
}
MATS = list(RAMPS)
# The palette measured on Eastward (20 Oct): its earth is olive-brown and less saturated
# (hue 27 to 42, saturation 0.21 to 0.26, purple-grey darks) and its grass a lighter, cleaner
# green (hue 78 to 97, lightness about 0.59 in the mids). Proposed for art/materials.json
# ('grass' and 'soil'); drawn by the terrace toolkit only until that is agreed, because those
# two ramps also colour battle, garden, garden_meadow, garden_props, icons, journey,
# mission_map, prop_sheet, sunstone_zones, valley_props, valley_zones, world_props and zones.
# Set TERRACE_PALETTE = False to draw with the shared ramps.
TERRACE_PALETTE = True
PROPOSED_GRASS = ['#3A4E36', '#5E7E48', '#86A85A', '#9CC068', '#BAD486']
PROPOSED_SOIL = ['#2A2026', '#3E2F33', '#54443E', '#6B5A48', '#857254', '#A08C66']
GRASS = PROPOSED_GRASS if TERRACE_PALETTE else MATERIALS['grass']   # dark .. light
LEAF = MATERIALS['leaf']
SOIL = PROPOSED_SOIL if TERRACE_PALETTE else MATERIALS['soil']
RAMPS['earth'] = SOIL
STONE = MATERIALS['stone']
WOOD = MATERIALS['wood']
PATH = MATERIALS['path']
WTR = MATERIALS['water']
FOAM = MATERIALS['snow'][3]

STRONG = (0.56, 0.60, 0.72)
SOFT = (0.90, 0.92, 0.96)      # the soft shade pooled along a face's foot

MEDIUM = (0.70, 0.74, 0.83)


def rgb(c) -> tuple:
    return hex_rgba(c)[:3] if isinstance(c, str) else tuple(int(v) for v in c[:3])


def lerp(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


CREV = lerp(SOIL[0], '#2E2238', 0.4)     # the gaps between clods: dark, cool
OUTLINE = lerp(SOIL[0], '#241A2C', 0.5)  # the face's outer edge (Eastward's dark outline)
ROCK = MATERIALS['bleached']             # loose rocks at the feet: warm tan


def grass_ramp(level: int):
    """Each tier its own tone: an upper tier a step lighter and warmer (verticality 4c)."""
    return [lerp(c, '#E8EBA0', 0.13 * level) for c in GRASS]


# ---- the spec -----------------------------------------------------------------------------

@dataclass
class Stair:
    """Steps cut through a face. `x` is the west edge of the west cheek and `rim` the rim
    row they cut (both on the grid); `w` the open width between the cheeks."""
    x: int
    rim: int
    w: int = STAIR_W
    material: str = 'timber'   # 'timber' | 'stone'
    cheek: int = CHEEK


@dataclass
class Ramp:
    """A ramp cut through a face: a sloped path sunk between two walls, from `top` (a row
    inside the upper tier, where the path leaves its surface) down through the face to the
    lower ground. x0..x1 spans the walls (STRIP each) and the path between (at least 34 px
    open: 48 on the grid gives 38). The slope is the face's height over (rim - top): 1 in 2
    for a 32 px face cut 64 px in. The walls are the tier's own side faces, so they follow
    the side rule: the west wall faces east (dark, casting its shadow on the path), the east
    wall faces west (lit)."""
    x0: int
    x1: int
    top: int
    material: str = 'earth'


@dataclass
class Edge:
    """An override for the faces under part of the map: the cells (c0, r0, c1, r1) hold the
    upper tier's top just above or beside the face."""
    rect: tuple
    material: str | None = None
    face: int | None = None


@dataclass
class Terrace:
    width: int
    height: int
    level: np.ndarray            # per px: the tier of the ground under it
    kind: np.ndarray             # per px: TOP, FACE_K, ...
    walk: list                   # per 4 px cell: '.' open, '#' blocked
    tiers: list                  # per 4 px cell: '0'..'9' a tier top, 'f' a face, 's' a stair or ramp
    blocked: set                 # px of the blocked cells (zones.build's blocked_ground)
    water: set                   # px of water, falls included (zones.WATER_MASKS, water_flow)
    falls: list                  # (x0, y0, x1, y1) of each fall down a face
    links: list                  # {'kind', 'top': (x, y), 'bottom': (x, y), 'from', 'to'}
    rails: list                  # (x0, x1, y): built rims that want railing props, stairs left open
    faces: list                  # (x0, x1, rim, height, top, material): south face runs
    stairs: list = field(default_factory=list)
    ramps: list = field(default_factory=list)


def from_plan(plan, face=FACE):
    """A plan height map (each cell: the height of the ground standing there) to the screen
    tier map build() takes. Each cell is drawn `face` px per level higher up the screen;
    where several land on one screen cell the nearest (southmost) wins, hiding the ground
    behind a tier; the rows a tier leaves below its south edge take the level of the ground
    in front, and build() carves its face out of them."""
    plan = np.array(plan, dtype=np.int16)
    rows, cols = plan.shape
    fh = face if isinstance(face, int) else face.get(1, FACE)
    k = fh // GRID
    out = np.full((rows, cols), -1, np.int16)
    for c in range(cols):
        for r in range(rows):              # north to south: nearer ground is drawn over
            h = int(plan[r, c])
            sr = r - h * k
            if 0 <= sr < rows:
                out[sr, c] = h
            elif sr < 0:
                pass
        for r in range(rows - 2, -1, -1):  # a face's rows: the ground in front of it
            if out[r, c] < 0:
                out[r, c] = out[r + 1, c]
        if out[rows - 1, c] < 0:
            out[rows - 1, c] = plan[rows - 1, c]
        for r in range(rows - 2, -1, -1):
            if out[r, c] < 0:
                out[r, c] = out[r + 1, c]
    return out.tolist()


MAT_LETTERS = {'e': 'earth', 's': 'stone', 'c': 'concrete', 't': 'timber', 'a': 'sandstone'}


def from_ascii(tiers: str, materials: str | None = None, heights: dict | None = None) -> dict:
    """A zone's terrain from a readable map: one character per 8 px cell, one line per row
    (40 x 72 for a zone). Returns the keyword arguments for build():
    `build(cv, **from_ascii(MAP, MATS, {'t': 16}))`.

    tiers      digits 0-9: the tier whose top the camera sees in that cell
               S / Z: a timber / stone stair cut through a face (mark its whole cut: its
                     cheeks and treads, from the rim row down the face's rows)
               R: a ramp cut through a face (mark the whole cut: its two walls and the
                     path, from the row where it leaves the upper surface down to the
                     face's foot; 6 cells wide gives 38 px open)
               ~ / F: water (a channel, a pool, a fall: a channel that reaches a rim falls)
               a marker's tier is the nearest digit in its row (the lower one on a tie)
    materials  optional, the same shape: e earth, s stone, c concrete, t timber,
               a sandstone, '.' or ' ' the default; it marks the cells of the upper tier
               whose faces (below and beside) take that material
    heights    optional face height per material letter, e.g. {'t': 16, 'c': 40}

    Blank lines and lines starting with ';' are skipped; whitespace at the ends is ignored.
    """
    rows = [ln.strip() for ln in tiers.strip('\n').split('\n') if ln.strip() and not ln.strip().startswith(';')]
    width = max(len(r) for r in rows)
    rows = [r.ljust(width, r[-1]) for r in rows]
    grid = [[0] * width for _ in rows]
    water = [[False] * width for _ in rows]
    marks = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch.isdigit():
                grid[r][c] = int(ch)
                continue
            if ch not in 'SZR~F':
                raise ValueError(f'from_ascii: unknown cell {ch!r} at row {r}, column {c}')
            left = next((int(row[k]) for k in range(c - 1, -1, -1) if row[k].isdigit()), None)
            ld = next((c - k for k in range(c - 1, -1, -1) if row[k].isdigit()), 999)
            right = next((int(row[k]) for k in range(c + 1, width) if row[k].isdigit()), None)
            rd = next((k - c for k in range(c + 1, width) if row[k].isdigit()), 999)
            near = [v for (v, d) in ((left, ld), (right, rd)) if v is not None and d == min(ld, rd)]
            grid[r][c] = min(near) if near else 0
            if ch in '~F':
                water[r][c] = True
            else:
                marks.setdefault(ch, []).append((r, c))
    stairs, ramps = [], []
    for ch, cells in marks.items():
        todo = set(cells)
        while todo:          # each 4-connected group of one marker is one stair or ramp
            st = [todo.pop()]
            grp = set(st)
            while st:
                r, c = st.pop()
                for n in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if n in todo:
                        todo.discard(n)
                        grp.add(n)
                        st.append(n)
            r0 = min(r for r, _ in grp)
            c0, c1 = min(c for _, c in grp), max(c for _, c in grp) + 1
            if ch in 'SZ':
                stairs.append(Stair(x=c0 * GRID, rim=r0 * GRID, w=(c1 - c0) * GRID - 2 * CHEEK,
                                    material='stone' if ch == 'Z' else 'timber'))
            else:
                ramps.append(Ramp(x0=c0 * GRID, x1=c1 * GRID, top=r0 * GRID))
    edges = []
    if materials:
        mrows = [ln.strip() for ln in materials.strip('\n').split('\n') if ln.strip() and not ln.strip().startswith(';')]
        heights = heights or {}
        for r, row in enumerate(mrows):
            c = 0
            while c < len(row):
                ch = row[c]
                if ch in '. ':
                    c += 1
                    continue
                c0 = c
                while c < len(row) and row[c] == ch:
                    c += 1
                edges.append(Edge((c0, r, c, r + 1), material=MAT_LETTERS[ch], face=heights.get(ch)))
    stairs.sort(key=lambda st: (st.rim, st.x))
    ramps.sort(key=lambda rp: (rp.top, rp.x0))
    return dict(tiers=grid, stairs=stairs, ramps=ramps, water=water, edges=edges)


def rects_map(cols: int, rows: int, rects, base: int = 0):
    """A tier map from rectangles of cells (c0, r0, c1, r1, tier), later ones on top."""
    m = [[base] * cols for _ in range(rows)]
    for (c0, r0, c1, r1, t) in rects:
        for r in range(max(0, r0), min(rows, r1)):
            for c in range(max(0, c0), min(cols, c1)):
                m[r][c] = t
    return m


# ---- masks --------------------------------------------------------------------------------

def _disc(r):
    return [(dx, dy) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dx * dx + dy * dy <= r * r + r * 0.6]


def _shift(m, dx, dy, fill=False):
    """m moved by (dx, dy): out[y, x] = m[y - dy, x - dx], `fill` beyond the edge."""
    h, w = m.shape
    out = np.full_like(m, fill)
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out


def _dilate(m, r):
    out = np.zeros_like(m)
    for dx, dy in _disc(r):
        out |= _shift(m, dx, dy)
    return out


def rounded(m, r=ROUND, r_in=None):
    """Round a grid-led mask's corners by about one cell: close (fills inner corners, by
    `r_in`, tighter so a notch keeps a crisp crease), then open (rounds outer corners by
    `r`). Straight runs stay exactly on the grid; edges at the zone border run on straight
    (the mask is padded with its own edge)."""
    r_in = r if r_in is None else r_in
    if r <= 0 and r_in <= 0:
        return m.copy()
    p = max(r, r_in) + 2
    big = np.pad(m, p, mode='edge')
    if r_in > 0:
        big = ~_dilate(~_dilate(big, r_in), r_in)
    if r > 0:
        big = _dilate(~_dilate(~big, r), r)
    return big[p:-p, p:-p]


def _shift_edge(m, dx, dy):
    """m moved by (dx, dy), the zone's edge rows and columns carried on beyond it."""
    h, w = m.shape
    p = max(abs(dx), abs(dy)) + 1
    big = np.pad(m, p, mode='edge')
    return big[p - dy:p - dy + h, p - dx:p - dx + w]


# ---- lumps, blocks and courses: the face's own structure -----------------------------------

def _lump(u: float, y: int, seed: int):
    """Which earth lump a face pixel belongs to: the nearest of seeds jittered on a 13 x 9
    lattice, distances stretched sideways, so lumps are wide, rounded and irregular (the
    rock face of valley_zones.cliff(), in soil)."""
    gx, gy = int(u // 13), y // 9
    best, bd = None, 1e9
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            cx, cy = gx + ox, gy + oy
            sx = cx * 13 + noise2(cx, cy, seed + 1) * 11
            sy = cy * 9 + noise2(cx, cy, seed + 2) * 7
            d = ((u - sx) / 1.6) ** 2 + (y - sy) ** 2
            if d < bd:
                best, bd = (cx, cy), d
    return best


def _block(u: float, d: int, course_h: int, seed: int, base: int = 14, var: int = 6):
    """Dressed blocks in courses: (course, block) for a face pixel; block lengths vary per
    course, joints offset course to course."""
    ci = d // course_h
    p = u + noise2(ci, 3, seed) * 23
    bi = int(p // base)
    start = bi * base + int(noise2(bi, ci, seed + 5) * var) - var // 2
    if p < start:
        bi -= 1
    return ci, bi


def _bay(u: float, seed: int, lo: int = 16, hi: int = 24):
    """Irregular bays along a face (timber posts, concrete joints): (bay index, px into it).
    Bay widths vary between lo and hi so nothing repeats on a fixed period."""
    p, i = -96, 0
    while True:
        w = lo + int(noise2(i, 9, seed) * (hi - lo + 1))
        if u < p + w:
            return i, int(u - p)
        p += w
        i += 1


def _strata(d: int, seed: int, x: int = 0):
    """Sandstone strata of 3 to 7 px from the rim down: (stratum index, row in it, its height)."""
    y, i = 0, 0
    while True:
        t = 3 + int(noise2(i, 7, seed) * 5)
        if d < y + t:
            return i, d - y, t
        y += t
        i += 1


# ---- the build ----------------------------------------------------------------------------

def build(cv: Canvas | None, tiers, *, face=FACE, material='earth', edges=(), stairs=(), ramps=(),
          water=(), tops=True, seed=0, round_r=ROUND, round_in=ROUND_IN, dress=True,
          bank='earth') -> Terrace:
    """Paint terraced ground on `cv` (a zone's ground canvas, or None for the maps alone) and
    return its walk blocking and maps.

    tiers     the tier map, rows of cells (8 px), screen space (see the module docstring)
    face      px per level: an int, or {level: px}
    material  the face material: a name, or {level: name}; `edges` override parts
    stairs    [Stair], ramps [Ramp]
    water     cells of water: [(c0, r0, c1, r1)] or a bool map of cells; where a channel on a
              tier reaches a rim it falls straight down the face (into a pool the map gives)
    bank      the banks of water on a tier top: 'earth' (default) or 'stone'
    dress     edge dressing, on by default: tall grass breaking rims, corners and feet,
              rocks at the feet, soft shade pooled along feet and in inner corners
    tops      True paints the tier tops as grass (a step lighter per tier); False keeps what
              the canvas holds (the generator painted its own ground); or a callable
              (x, y, level) -> colour
    """
    lv_cells = np.array(tiers, dtype=np.int16)
    rows, cols = lv_cells.shape
    H, W = rows * GRID, cols * GRID
    top_lv = int(lv_cells.max())
    edges = list(edges)

    def edge_at(x, y):
        cx, cy = x // GRID, y // GRID
        for e in reversed(edges):
            c0, r0, c1, r1 = e.rect
            if c0 <= cx < c1 and r0 <= cy < r1:
                return e
        return None

    def face_px(level, x, y):
        e = edge_at(x, y)
        if e and e.face:
            return e.face
        return face if isinstance(face, int) else face.get(level, FACE)

    for h in ([face] if isinstance(face, int) else list(face.values())) + [e.face for e in edges if e.face]:
        if h not in HEIGHTS:
            raise ValueError(f'terrace: a face of {h} px; faces come from {HEIGHTS}')

    def mat_of(level, x, y):
        e = edge_at(x, y)
        if e and e.material:
            return e.material
        return material if isinstance(material, str) else material.get(level, 'earth')

    # 1. the rounded tier masks, and the level of the ground at each pixel
    lvl = np.zeros((H, W), np.int16)
    for L in range(1, top_lv + 1):
        m = np.kron(lv_cells >= L, np.ones((GRID, GRID), bool))
        lvl += rounded(m, round_r, round_in)

    kind = np.full((H, W), TOP, np.uint8)
    rim = np.full((H, W), -1, np.int16)      # face: the rim row of its column
    ftop = np.zeros((H, W), np.int16)        # face: the tier it drops from
    fh = np.zeros((H, W), np.int16)          # face: its height in this column
    fmat = np.full((H, W), -1, np.int8)      # face/strip/cheek: material index
    face_runs = []

    # 2. south faces: below each rim, carved from the lower ground
    for x in range(W):
        col = lvl[:, x]
        y = 1
        while y < H:
            a = int(col[y - 1])
            if a > col[y] and kind[y, x] == TOP:
                d = 0
                while y + d < H:
                    b = int(col[y + d])
                    if b >= a:
                        break
                    need = sum(face_px(L, x, y - 1) for L in range(b + 1, a + 1))
                    if d >= need:
                        break
                    d += 1
                mi = MATS.index(mat_of(a, x, y - 1))
                kind[y:y + d, x] = FACE_K
                rim[y:y + d, x] = y
                ftop[y:y + d, x] = a
                fh[y:y + d, x] = d
                fmat[y:y + d, x] = mi
                y += max(1, d)
            else:
                y += 1
    # runs of south face per rim (for rails, lint and the report)
    for y in range(H):
        x = 0
        while x < W:
            if kind[y, x] == FACE_K and rim[y, x] == y:
                x0 = x
                while x < W and kind[y, x] == FACE_K and rim[y, x] == y:
                    x += 1
                face_runs.append((x0, x, y, int(fh[y, x0]), int(ftop[y, x0]), MATS[fmat[y, x0]]))
            else:
                x += 1

    ramp_h = np.zeros((H, W), np.int16)     # ramp: the height of its surface above the lower ground
    sk = np.zeros((H, W), np.int8)          # side strips: 1..STRIP from the rim line out
    sdir = np.zeros((H, W), np.int8)        # +1 faces east (the tier is to the west), -1 faces west
    sreg = np.zeros((H, W), np.int8)        # 1 beside the face (the corner wrap), 0 beside the top
    slev = np.zeros((H, W), np.int16)
    links = []

    # 3. ramps cut through a face
    ramp_cut = []
    for rp in ramps:
        cx = (rp.x0 + rp.x1) // 2
        r0 = next((y for y in range(rp.top, H) if kind[y, cx] == FACE_K), None)
        if r0 is None:
            raise ValueError(f'terrace: the ramp at x {rp.x0} meets no face below row {rp.top}')
        hgt = int(fh[r0, cx])
        a = int(ftop[r0, cx]) or 1
        mi = MATS.index(rp.material)
        bottom = r0 + hgt
        for y in range(rp.top, min(H, bottom)):
            depth = (y - rp.top) / max(1, bottom - rp.top)        # 0 at the top .. 1 at the foot
            wall = max(1, min(STRIP, 1 + int(depth * hgt / 3)))   # the walls grow from nothing
            for x in range(rp.x0, min(W, rp.x1)):
                lvl[y, x] = a - 1
                if x < rp.x0 + STRIP and x - rp.x0 < wall:
                    kind[y, x] = STRIP_K
                    sdir[y, x], sk[y, x] = 1, x - rp.x0 + 1          # the west wall, facing east
                elif x >= rp.x1 - STRIP and rp.x1 - 1 - x < wall:
                    kind[y, x] = STRIP_K
                    sdir[y, x], sk[y, x] = -1, rp.x1 - x             # the east wall, facing west
                else:
                    kind[y, x] = RAMP_K
                    ramp_h[y, x] = max(1, int(round(hgt * (1 - depth))))
                    continue
                sreg[y, x], slev[y, x], ftop[y, x], fmat[y, x], fh[y, x], rim[y, x] = 0, a, a, mi, hgt, -1
        ramp_cut.append((rp, r0, bottom))
        links.append({'kind': 'ramp', 'top': (cx, rp.top - 4), 'bottom': (cx, bottom + 4), 'from': a - 1, 'to': a})

    # 4. stairs cut through a face
    stair_id = np.full((H, W), -1, np.int16)
    for si, st in enumerate(stairs):
        cx = st.x + st.cheek + st.w // 2
        hgt = int(fh[st.rim, cx]) if kind[st.rim, cx] == FACE_K else FACE
        a = int(ftop[st.rim, cx]) or 1
        x1 = st.x + 2 * st.cheek + st.w
        mi = MATS.index('stone' if st.material == 'stone' else 'timber')
        for y in range(st.rim, min(H, st.rim + hgt)):
            for x in range(st.x, min(W, x1)):
                cheek = x < st.x + st.cheek or x >= x1 - st.cheek
                kind[y, x] = CHEEK_K if cheek else STAIR_K
                stair_id[y, x] = si
                ftop[y, x] = a
                rim[y, x] = st.rim
                fh[y, x] = hgt
                fmat[y, x] = mi
        links.append({'kind': 'stair', 'top': (cx, st.rim - 4), 'bottom': (cx, st.rim + hgt + 4),
                      'from': a - 1, 'to': a})

    # 5. water: grid-led channels; a channel reaching a rim falls straight down the face
    wm_cells = np.zeros((rows, cols), bool)
    if isinstance(water, np.ndarray) or (water and isinstance(water[0], (list, np.ndarray))):
        wm_cells = np.array(water, bool)
    else:
        for (c0, r0, c1, r1) in water:
            wm_cells[max(0, r0):r1, max(0, c0):c1] = True
    wet = rounded(np.kron(wm_cells, np.ones((GRID, GRID), bool)), 4) if wm_cells.any() else np.zeros((H, W), bool)
    falls = []
    fall = np.zeros((H, W), bool)
    for x in range(W):
        for y in range(1, H):
            if kind[y, x] == FACE_K and rim[y, x] == y and wet[y - 1, x] and kind[y - 1, x] == TOP:
                fall[y:y + fh[y, x], x] = True
                kind[y:y + fh[y, x], x] = FALL_K
    ys, xs = np.nonzero(fall)
    if len(xs):
        lab = _components(fall)
        for k in range(1, lab.max() + 1):
            yy, xx = np.nonzero(lab == k)
            falls.append((int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1))
    wet &= (kind == TOP)
    wet |= fall

    # 6. side strips: the face seen from the side, on the lower ground beside a higher tier
    for L in range(top_lv, 0, -1):
        solid_top = (kind == TOP) & (lvl >= L) & ~wet
        solid_face = ((kind == FACE_K) | (kind == FALL_K) | (kind == CHEEK_K)) & (ftop >= L)
        solid = solid_top | solid_face
        recv_top = (kind == TOP) & (lvl < L)
        recv_face = (kind == FACE_K) & (ftop == L)   # an inner corner: the strip meets a face behind it
        depth = np.where(recv_face, np.arange(H)[:, None] - rim, 999)
        hh = np.where(recv_face, fh, FACE)
        for dirn in (1, -1):
            prev = None
            for k in range(1, STRIP + 1):
                src = _shift(solid, dirn * k, 0)
                src_top = _shift(solid_top, dirn * k, 0)
                src_face = _shift(solid_face, dirn * k, 0)
                cand = (sk == 0) & ((recv_top & src) | (recv_face & src_top))
                if prev is not None:
                    cand &= _shift(prev, dirn, 0)      # continuous out from the rim line
                    # the band's far end is cut on a short diagonal by the ground behind
                    # (3 rows a px), so it reads as a side, not as an outline round the top
                    lift = 3 * (k - 1)
                    cand &= _shift_edge(solid, dirn * k, lift)
                # inner corner: the strip shows only where it stands in front of the face
                # behind it (a diagonal crease, one strip px per face/STRIP rows)
                cand &= ~recv_face | (depth * STRIP >= hh * (k - 1))
                sk[cand] = k
                sdir[cand] = dirn
                sreg[cand & src_face] = 1
                slev[cand] = L
                kind[cand] = STRIP_K
                prev = cand
    # the strip's material and its anchor rim (the south face it wraps into)
    for y in range(H):
        for x in range(W):
            if kind[y, x] != STRIP_K:
                continue
            qx = int(x) - int(sdir[y, x]) * int(sk[y, x])
            if 0 <= qx < W and kind[y, qx] in (FACE_K, FALL_K, CHEEK_K):
                fmat[y, x] = fmat[y, qx]
                rim[y, x] = rim[y, qx]
                fh[y, x] = fh[y, qx]
            else:
                fmat[y, x] = MATS.index(mat_of(int(slev[y, x]), max(0, min(W - 1, qx)), y))
                fh[y, x] = face_px(int(slev[y, x]), max(0, min(W - 1, qx)), y)
            ftop[y, x] = slev[y, x]
    # anchor rims for the side strips above a corner: carried up each strip from its face
    for x in range(W):
        cur = -1
        for y in range(H - 1, -1, -1):
            if kind[y, x] == STRIP_K:
                if rim[y, x] >= 0 and sreg[y, x]:
                    cur = rim[y, x]
                elif cur >= 0:
                    rim[y, x] = cur
            else:
                cur = -1

    res_kind = kind
    # 7. paint
    if cv is not None:
        img = np.array(cv.img.convert('RGB'))[cv.pad:cv.pad + H, cv.pad:cv.pad + W].copy() \
            if cv.pad else np.array(cv.img.convert('RGB'))[:H, :W].copy()
        P = _Painter(img, lvl, kind, rim, ftop, fh, fmat, sk, sdir, sreg, ramp_h, stair_id, wet, fall,
                     stairs, ramps, seed)
        P.dressed = bool(dress)
        P.bank = bank
        if tops is True:
            P.tops()
        elif callable(tops):
            for y in range(H):
                for x in range(W):
                    c = tops(x, y, int(lvl[y, x]))
                    if c is not None:
                        img[y, x] = rgb(c)
        P.back_rims()
        P.landings()
        P.ramps_paint()
        P.water()
        P.shadows()
        P.foot_grass()
        P.faces()
        P.strips()
        P.lips()
        P.stairs_paint()
        P.falls_paint()
        if dress:
            P.weather()
            P.dress()
        out = Image.fromarray(img, 'RGB').convert('RGBA')
        if cv.pad:
            cv.img.paste(out, (cv.pad, cv.pad))
        else:
            cv.img.paste(out, (0, 0))

    # 8. the walk grid and the tier map (4 px cells)
    crow, ccol = H // CELL, W // CELL
    bank = _banks(wet, kind)
    cells = []
    walk = []
    for r in range(crow):
        trow, wrow = '', ''
        for c in range(ccol):
            sl = (slice(r * CELL, r * CELL + CELL), slice(c * CELL, c * CELL + CELL))
            k = kind[sl]
            n_face = int(np.isin(k, FACE_LIKE).sum())
            n_stair = int(np.isin(k, (STAIR_K, RAMP_K)).sum())
            n_wet = int((wet[sl] | bank[sl]).sum())
            if n_face * 2 >= CELL * CELL:
                trow += 'f'
                wrow += '#'
            elif n_stair * 2 >= CELL * CELL:
                trow += 's'
                wrow += '.'
            else:
                v = np.bincount(lvl[sl].ravel().clip(0, 9)).argmax()
                trow += str(int(v))
                wrow += '#' if n_wet * 2 >= CELL * CELL else '.'
        cells.append(trow)
        walk.append(wrow)
    # a drop with no face shown (a back rim, a strip's top end) is blocked on its lower side
    walk = [list(rw) for rw in walk]
    for r in range(crow):
        for c in range(ccol):
            if walk[r][c] == '#' or not cells[r][c].isdigit():
                continue
            for (dr, dc) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < crow and 0 <= cc < ccol and walk[rr][cc] != '#' and cells[rr][cc].isdigit():
                    if int(cells[rr][cc]) > int(cells[r][c]):
                        walk[r][c] = '#'
    walk = [''.join(rw) for rw in walk]
    blocked = {(c * CELL + dx, r * CELL + dy) for r in range(crow) for c in range(ccol) if walk[r][c] == '#'
               for dx in range(CELL) for dy in range(CELL)}
    water_px = {(int(x), int(y)) for (y, x) in zip(*np.nonzero(wet))}
    rails = []
    face_runs = [f for f in face_runs if f[1] - f[0] >= GRID]   # (not a corner's rounding)
    for (x0, x1, y, h, t, m) in face_runs:
        if m == 'earth' or x1 - x0 < 2 * GRID:
            continue
        segs, cur = [], x0
        for st in stairs:
            sx0, sx1 = st.x - 2, st.x + 2 * st.cheek + st.w + 2
            if st.rim == y and sx0 < x1 and sx1 > x0:
                if sx0 > cur:
                    segs.append((cur, sx0, y))
                cur = max(cur, sx1)
        if cur < x1:
            segs.append((cur, x1, y))
        rails += [sg for sg in segs if sg[1] - sg[0] >= 4]
    return Terrace(W, H, lvl, res_kind, walk, cells, blocked, water_px, falls, links, rails, face_runs,
                   list(stairs), list(ramps))


def _components(m):
    """4-connected components of a bool mask (labels 1..n)."""
    lab = np.zeros(m.shape, np.int32)
    n = 0
    H, W = m.shape
    for y0, x0 in zip(*np.nonzero(m)):
        if lab[y0, x0]:
            continue
        n += 1
        q = deque([(y0, x0)])
        lab[y0, x0] = n
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    q.append((yy, xx))
    return lab


def _banks(wet, kind):
    """The earth banks round water on a tier top: 3 px above the water (its north bank seen
    as a little face), 3 px at the sides, 1 px lit lip below."""
    top = kind == TOP
    above = np.zeros_like(wet)
    for d in (1, 2, 3):
        above |= _shift(wet, 0, -d)
    side = _shift(wet, 1, 0) | _shift(wet, -1, 0) | _shift(wet, 2, 0) | _shift(wet, -2, 0) | \
        _shift(wet, 3, 0) | _shift(wet, -3, 0)
    below = _shift(wet, 0, 1)
    return (above | side | below) & top & ~wet


# ---- painting -----------------------------------------------------------------------------

class _Painter:
    def __init__(self, img, lvl, kind, rim, ftop, fh, fmat, sk, sdir, sreg, ramp_h, stair_id, wet, fall,
                 stairs, ramps, seed):
        self.img, self.lvl, self.kind, self.rim, self.ftop, self.fh = img, lvl, kind, rim, ftop, fh
        self.fmat, self.sk, self.sdir, self.sreg, self.ramp_h = fmat, sk, sdir, sreg, ramp_h
        self.stair_id, self.wet, self.fall, self.stairs, self.ramps, self.seed = stair_id, wet, fall, stairs, ramps, seed
        self.H, self.W = kind.shape
        self.foot_blades = []
        self.dressed = False

    # helpers
    def put(self, x, y, c):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.img[y, x] = rgb(c)

    def mul(self, x, y, k):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.img[y, x] = (self.img[y, x] * np.array(k)).astype(np.uint8)

    def n(self, x, y, s):
        return noise2(x, y, self.seed * 101 + s)

    # tops: grass in broad patches, each tier a step lighter, tufts and the odd flower
    def tops(self):
        """Tier tops as grass in Eastward's manner: a calm base in three tones laid in large
        soft patches; detail as drawn shapes of several pixels (tufts of blades lit on their
        left, small flowers, worn dirt) gathered in loose clusters, never single-pixel
        speckle. Darker grass gathering at feet and edges comes with the dressing."""
        H, W, s = self.H, self.W, self.seed
        tidx = np.zeros((H, W), np.int8)
        tones = {}
        for L in range(0, int(self.lvl.max()) + 1):
            g = grass_ramp(L)
            tones[L] = (lerp(g[2], g[1], 0.32), lerp(g[2], g[3], 0.45), lerp(g[3], g[4], 0.38))
        for y in range(H):
            for x in range(W):
                T = tones[int(self.lvl[y, x])]
                v = smooth_noise(x, y, 26, s * 7 + 501) + 0.42 * (smooth_noise(x, y, 8, s * 7 + 503) - 0.5) + \
                    0.16 * (smooth_noise(x, y, 3, s * 7 + 504) - 0.5)
                ti = 0 if v < 0.36 else 2 if v > 0.63 else 1
                tidx[y, x] = ti
                # light as a material (Eastward's painted light): a slow, soft swell of
                # brightness and of hue, dry and warm in places, damp and cool in others
                lum = 1 + 0.2 * (smooth_noise(x, y, 15, s * 7 + 506) - 0.5)
                hue = smooth_noise(x, y, 21, s * 7 + 507)
                c = T[ti]
                c = lerp(c, '#D6C46E', 0.3 * (hue - 0.55)) if hue > 0.55 else lerp(c, '#4E8A78', 0.3 * (0.45 - hue)) \
                    if hue < 0.45 else c
                self.img[y, x] = tuple(min(255, int(v2 * lum)) for v2 in c)
        gd = self._growth()
        sd = s * 7 + 510
        # the weave: Eastward's open grass is a close, low-contrast scatter of little
        # chevrons a step darker than the ground (here a 5 px cup, all one piece), calm
        # because it is even and faint
        for j, y in enumerate(range(2, H, 3)):
            for i, x in enumerate(range((j % 2) * 2, W - 3, 4)):
                xx = x + int(noise2(i, j, sd + 30) * 2)
                if noise2(i, j, sd + 31) > 0.7 - 1.4 * float(gd[y, min(W - 1, xx + 1)]) or not self._open(xx, y - 1, xx + 3, y + 1):
                    continue
                base = tuple(int(v) for v in self.img[y, xx + 1])
                c = lerp(base, '#2E4A30', 0.17)
                for (dx, dy) in ((0, -1), (0, 0), (1, 0), (2, 0), (2, -1)):
                    self.put(xx + dx, y + dy, c)
        # the grain: short blade strokes (2 px, never one) a tone off the ground under them,
        # thicker where the clusters gather, thin in the calm
        sd = s * 7 + 510
        for j, y in enumerate(range(2, H - 1, 3)):
            for i, x in enumerate(range(1 + (j % 2), W - 1, 3)):
                xx = x + int(noise2(i, j, sd + 4) * 2)
                yy = y + int(noise2(i, j, sd + 5) * 2)
                if not self._open(xx, yy - 1, xx + 2, yy + 1):
                    continue
                q = noise2(i, j, sd + 6)
                if q > 0.62 - 0.35 * float(gd[yy, xx]):
                    continue
                T = tones[int(self.lvl[yy, xx])]
                base = tuple(int(v) for v in self.img[yy, xx])
                dark = tidx[yy, xx] == 0
                light = tidx[yy, xx] == 2
                if q < 0.12:
                    c = lerp(base, '#F2EEB8', 0.22) if not dark else T[1]     # a lit stroke
                elif q < 0.24:
                    c = lerp(base, '#2E4A36', 0.22) if not light else T[1]    # a shaded stroke
                else:
                    c = lerp(base, '#D0C070', 0.18) if light else lerp(base, '#3E5A3A', 0.14)
                if (i + j) % 3:
                    self.put(xx, yy, c); self.put(xx, yy - 1, c)             # upright
                else:
                    self.put(xx, yy, c); self.put(xx + 1, yy - 1, c); self.put(xx + 1, yy, c)  # a little V
        # growth gathers where Eastward puts it: by edges, feet, banks and stairs, and in a
        # few slow clumps out in the open; the open stays calm
        dens = self._growth()
        for j, y in enumerate(range(3, H - 1, 3)):
            for i, x in enumerate(range(2 + (j % 2) * 2, W - 3, 4)):
                xx = x + int(noise2(i, j, sd + 1) * 3) - 1
                yy = y + int(noise2(i, j, sd + 2) * 3) - 1
                if not (6 <= yy < H - 1 and 4 <= xx < W - 4) or not self._open(xx - 3, yy - 6, xx + 4, yy + 1):
                    continue
                k = noise2(i, j, sd)
                L = int(self.lvl[yy, xx])
                dv = float(dens[yy, xx])
                if k < 0.46 * dv ** 1.4:
                    self._tuft(xx, yy, L, i * 131 + j, dv)
                elif k > 0.988 - 0.02 * dv:
                    self._flower(xx, yy, (i * 7 + j) % 4)
        for j, y in enumerate(range(10, H - 2, 22)):          # long grass: a few patches, one shape each
            for i, x in enumerate(range(8 + (j % 2) * 20, W - 16, 40)):
                xx = x + int(noise2(i, j, sd + 21) * 16) - 8
                yy = y + int(noise2(i, j, sd + 22) * 10) - 5
                w = 8 + int(noise2(i, j, sd + 23) * 9)
                if 0 <= yy < H and 0 <= xx < W and dens[yy, xx] > 0.45 and noise2(i, j, sd + 24) > 0.35 and \
                        self._open(xx - 1, yy - 7, xx + w + 1, yy + 1):
                    self._long_grass(xx, yy, w, int(self.lvl[yy, xx]), i * 17 + j)
        for k in range(0):                         # (worn patches come with feet and landings)
            cx, cy = int(noise2(k, 1, sd + 3) * W), int(noise2(k, 2, sd + 3) * H)
            self._worn(cx, cy, 6 + int(noise2(k, 3, sd + 3) * 8), 3 + int(noise2(k, 4, sd + 3) * 3), k)

    def _open(self, x0, y0, x1, y1):
        """Whether a box is all open tier top (no face, water, stair)."""
        if x0 < 0 or y0 < 0 or x1 > self.W or y1 > self.H:
            return False
        return bool(((self.kind[y0:y1, x0:x1] == TOP) & ~self.wet[y0:y1, x0:x1]).all())

    def _growth(self):
        """0 (bare, calm) .. 1 (thick growth) per pixel: high within ~14 px of any edge (a
        face, a band, water, a stair or ramp) and in slow clumps out in the open."""
        if getattr(self, '_gr', None) is not None:
            return self._gr
        H, W = self.H, self.W
        edge = (self.kind != TOP) | self.wet
        dist = np.full((H, W), 15, np.int16)
        cur = edge.copy()
        for d in range(1, 15):
            cur = cur | _shift(cur, 1, 0) | _shift(cur, -1, 0) | _shift(cur, 0, 1) | _shift(cur, 0, -1)
            dist[cur & (dist > d)] = d
        near = np.clip(1 - dist / 14.0, 0, 1)
        ys, xs = np.mgrid[0:H, 0:W]
        blob = np.vectorize(lambda x, y: smooth_noise(x, y, 38, self.seed + 901))(xs[::4, ::4], ys[::4, ::4])
        blob = np.kron(blob, np.ones((4, 4)))[:H, :W]
        open_g = np.clip((blob - 0.52) * 2.6, 0, 0.8)
        self._gr = np.clip(np.maximum(near * 0.95, open_g) + 0.06, 0, 1)
        return self._gr

    TUFTS = [   # bottom row is the root's shadow; l lit, h highlight, m mid, d dark, y / Y dry
        ['l.m', 'lmm', 'rrr'],
        ['.l..m', '.l.mm', 'llmm.', 'rrrr.'],
        ['..h..', '.lh.m', '.l..m', 'll.mm', 'lmmmm', '.rrr.'],
        ['l..h..m', 'll.h.mm', '.lmmmm.', '.rrrrr.'],
        ['Y...y', 'Y.y.y', 'YYyyy', '.yyy.', '.rrr.'],
        ['.h.', 'lhm', 'lmm', 'rr.'],
        ['h.....m', 'hl..mmm', '.ll.mm.', '..lmm..', '.rrrrr.'],
    ]

    def _tuft(self, x, y, L, k, dv=0.5):
        """A tuft from a set of seven drawn shapes and sizes (bigger where growth is thick),
        lit on its left, every part two pixels or more; its shadow falls to the right."""
        g = grass_ramp(L)
        col = {'l': lerp(g[4], '#F4F2C4', 0.15), 'h': lerp(g[4], '#F4F2C4', 0.4), 'm': g[3],
               'd': lerp(g[2], g[1], 0.5), 'r': lerp(g[1], g[2], 0.3),
               'y': lerp(g[3], '#D8C070', 0.5), 'Y': lerp(g[4], '#F0DE90', 0.55)}
        q = noise2(k, 1, self.seed + 871)
        big = dv > 0.5 and noise2(k, 2, self.seed + 872) < dv
        pick = [2, 3, 6] if big else [0, 1, 5]
        if q > 0.86:
            pick = [4]                                        # dry grass, here and there
        pat = self.TUFTS[pick[int(noise2(k, 3, self.seed + 873) * len(pick)) % len(pick)]]
        hgt, wid = len(pat), len(pat[0])
        x0, y0 = x - wid // 2, y - hgt + 1
        for j, row in enumerate(pat):
            for i, ch in enumerate(row):
                if ch != '.':
                    self.put(x0 + i, y0 + j, col[ch])
        self.mul(x0 + wid, y, MEDIUM); self.mul(x0 + wid, y - 1, MEDIUM)

    def _long_grass(self, x, y, w, L, k):
        """A patch of long grass drawn as one shape: strands two px wide rising 4 to 7 px,
        a dark mass at the root, lit tips on the left, a ragged top, its shadow to the right."""
        g = grass_ramp(L)
        for i in range(0, w, 2):
            h = 4 + int(3 * smooth_noise(x + i, y, 4, self.seed + 911) + noise2(k, i, self.seed + 912) * 1.5)
            lit = i < w * 0.45
            tip = lerp(g[4], '#F4F2C4', 0.2) if lit else g[3]
            body = g[3] if lit else lerp(g[3], g[2], 0.5)
            for dx in (0, 1):
                if i + dx >= w:
                    continue
                hh = h - (1 if dx and noise2(k, i, self.seed + 913) > 0.5 else 0)
                for t in range(hh):
                    c = lerp(g[1], g[2], 0.4) if t < 2 else body if t < hh - 2 else tip
                    self.put(x + i + dx, y - t, c)
        for t in range(3):
            self.mul(x + w + t // 2, y - t, MEDIUM)

    def _flower(self, x, y, k):
        petal = ['#F2E6C8', '#E8B4C8', '#F0D060', '#B8C8F0'][k]
        self.put(x, y - 1, petal); self.put(x + 1, y - 1, petal)
        self.put(x, y - 2, petal); self.put(x + 1, y - 2, lerp(petal, '#FFFFFF', 0.4))
        self.mul(x, y, MEDIUM); self.mul(x + 1, y, MEDIUM)

    def _worn(self, cx, cy, rx, ry, k):
        """Worn ground where feet go: bare earth in a rounded patch, grass breaking over its
        edge in clumps, a darker rim on its upper edge."""
        for y in range(cy - ry - 1, cy + ry + 2):
            for x in range(cx - rx - 1, cx + rx + 2):
                if not (0 <= x < self.W and 0 <= y < self.H) or self.kind[y, x] != TOP or self.wet[y, x]:
                    continue
                e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + (smooth_noise(x, y, 3, self.seed + 881 + k) - 0.5) * 0.7
                if e < 1:
                    inner = e < 0.55
                    c = PATH[2] if inner and smooth_noise(x, y, 4, self.seed + 882) > 0.45 else PATH[1] if not inner else \
                        lerp(PATH[2], PATH[1], 0.5)
                    self.img[y, x] = rgb(c)
                    if y > 0 and self.kind[y - 1, x] == TOP and \
                            ((x - cx) / rx) ** 2 + ((y - 1 - cy) / ry) ** 2 + (smooth_noise(x, y - 1, 3, self.seed + 881 + k) - 0.5) * 0.7 >= 1:
                        self.img[y, x] = rgb(lerp(PATH[1], PATH[0], 0.5))   # the turf lip above it

    def back_rims(self):
        """Where a tier's top meets lower ground behind it (north) there is no face, only a
        crease inside the top: a dark line, then a lit one (the lower ground shows beyond)."""
        lvl, kind = self.lvl, self.kind
        for y in range(1, self.H - 1):
            for x in range(self.W):
                if kind[y, x] == TOP and kind[y - 1, x] == TOP and lvl[y, x] > lvl[y - 1, x] and not self.wet[y, x]:
                    g = grass_ramp(int(lvl[y, x]))
                    self.img[y, x] = lerp(g[1], INK, 0.35)
                    if kind[y + 1, x] == TOP:
                        self.put(x, y + 1, g[4] if (x // 4 + y) % 5 else g[3])

    def landings(self):
        """Worn ground on the stairs' landings: 8 px at the head, 8 px at the foot."""
        for si, st in enumerate(self.stairs):
            x0, x1 = st.x + st.cheek, st.x + st.cheek + st.w
            hgt = int(self.fh[st.rim, x0 + 1])
            for (y0, y1) in ((st.rim - LANDING, st.rim), (st.rim + hgt, st.rim + hgt + LANDING)):
                for y in range(y0, y1):
                    for x in range(x0 - 2, x1 + 2):
                        if not (0 <= x < self.W and 0 <= y < self.H) or self.kind[y, x] != TOP:
                            continue
                        edge = min(x - x0 + 2, x1 + 1 - x, (y - y0) if y0 > st.rim else (y1 - 1 - y))
                        if edge <= 2 and self.n(x, y, 521) > 0.3 + 0.2 * edge:
                            continue                 # grass breaks over the worn edge
                        if st.material == 'stone':
                            bx = _bay(x + (y - y0) // 4 * 7, self.seed + 522, 9, 14)
                            j = bx[1] == 0 or (y - y0) % 4 == 3
                            c = STONE[1] if j else (STONE[2] if self.n(bx[0], (y - y0) // 4, 522) > 0.5 else STONE[3])
                            c = lerp(c, self.img[y, x], 0.25)
                        else:
                            v = self.n(x // 3, y // 2, 523)
                            c = PATH[2] if v > 0.5 else PATH[3]
                            if smooth_noise(x, y, 5, 524) > 0.7:
                                c = PATH[1]
                        self.put(x, y, c)

    def water(self):
        """Water in grid-led banks. In the water: a dark band under the north bank, a broken
        foam line where it laps the other banks, lighter shallows inside that, the deep
        middle darker, and short ripples across the current (water_flow.py moves its own
        streaks over this). The banks: earth seen from the front on the north side, the
        west bank dark (it faces east), the east bank lit, a lit turf lip on the south;
        pebbles along them. `bank='stone'` lays dressed coping instead of earth."""
        wet, kind, H, W = self.wet, self.kind, self.H, self.W
        open_w = wet & ~self.fall

        def run(m, dx, dy, cap=6):
            d = np.full((H, W), cap + 1, np.int16)
            cur = m.copy()
            for i in range(1, cap + 1):
                cur = cur & _shift(m, -dx * i, -dy * i, fill=True)
                d[m & ~cur & (d > cap)] = i
            return d
        dn = run(wet, 0, -1)          # rows of water up to the north bank
        ds = run(wet, 0, 1)
        dw = run(wet, -1, 0)
        de = run(wet, 1, 0)
        near = np.minimum(np.minimum(dn, ds), np.minimum(dw, de))
        sd = self.seed + 531
        for y, x in zip(*np.nonzero(open_w)):
            c = WTR[1] if near[y, x] >= 5 else lerp(WTR[1], WTR[2], 0.6)
            if smooth_noise(x, y, 9, sd) > 0.62 and near[y, x] >= 3:
                c = lerp(c, WTR[2], 0.4)
            if dn[y, x] <= 2:
                c = WTR[0]                                   # the shade under the north bank
            elif dn[y, x] == 3:
                c = lerp(WTR[0], WTR[1], 0.5)
            elif min(dw[y, x], de[y, x], ds[y, x]) == 1:
                k = (y // 3) if min(dw[y, x], de[y, x]) == 1 else (x // 3)
                c = lerp(WTR[4], FOAM, 0.35) if noise2(k, x // 40 + y // 40, sd + 1) > 0.35 else lerp(WTR[2], WTR[3], 0.6)
            elif min(dw[y, x], de[y, x], ds[y, x]) <= 3:
                c = lerp(WTR[2], WTR[3], 0.55)               # the shallows
            self.img[y, x] = rgb(c)
        for j, y in enumerate(range(2, H, 5)):              # ripples: short dashes across the flow
            for i, x in enumerate(range(1 + 3 * (j % 2), W, 7)):
                if noise2(i, j, sd + 2) > 0.45:
                    continue
                xx, yy = x + int(noise2(i, j, sd + 3) * 4), y + int(noise2(i, j, sd + 4) * 3)
                n = 3 + int(noise2(i, j, sd + 5) * 3)
                if all(0 <= xx + t < W and 0 <= yy < H and open_w[yy, xx + t] and near[yy, xx + t] >= 3 and dn[yy, xx + t] > 3
                       for t in range(n)):
                    for t in range(n):
                        self.put(xx + t, yy, lerp(WTR[2], WTR[3], 0.75))
        bank = _banks(wet, kind)
        stone = getattr(self, 'bank', 'earth') == 'stone'
        R = RAMPS['stone']
        for y, x in zip(*np.nonzero(bank)):
            g = grass_ramp(int(self.lvl[y, x]))
            d_dn = next((d for d in (1, 2, 3) if y + d < H and wet[y + d, x]), 0)
            if d_dn:   # the north bank, seen from the front
                if stone:
                    c = [None, R[1], R[3], R[5]][d_dn]
                else:
                    c = [None, SOIL[1], SOIL[3], g[1]][d_dn]
                    if d_dn == 2 and noise2(x // 3, y, self.seed + 533) > 0.75:
                        c = ROCK[3]                          # a stone in the bank
            elif y > 0 and wet[y - 1, x]:
                c = (R[4] if stone else g[4]) if (x // 3) % 3 else (R[5] if stone else lerp(g[4], '#FFFFFF', 0.15))
            elif any(x + d < W and wet[y, x + d] for d in (1, 2, 3)):
                d = next(d for d in (1, 2, 3) if x + d < W and wet[y, x + d])   # the west bank faces east: dark
                c = [None, R[1], R[2], R[3]][d] if stone else [None, SOIL[1], SOIL[2], g[1]][d]
            else:
                d = next((d for d in (1, 2, 3) if x - d >= 0 and wet[y, x - d]), 3)   # the east bank faces west: lit
                c = [None, R[4], R[3], R[5]][d] if stone else [None, SOIL[4], SOIL[3], g[4]][d]
            if not stone and not d_dn and noise2(x, y // 4, self.seed + 534) > 0.85 and y + 1 < H and bank[y + 1, x]:
                c = ROCK[3]
                self.put(x, y + 1, ROCK[2])
            self.put(x, y, c)

    def shadows(self):
        """Cast shadows down and to the right of every face, strip and cheek onto the ground
        lower than it, 8 px whatever the face's height (Schlitter: "No matter how tall the
        rock wall all shadows are the same length"): 3 px strong, 3 medium, 2 dithered."""
        kind, H, W = self.kind, self.H, self.W
        caster_lv = np.where(np.isin(kind, (FACE_K, STRIP_K, CHEEK_K)), self.ftop, 0)
        caster_lv = np.where(kind == FALL_K, self.ftop, caster_lv)
        dist = np.full((H, W), 99, np.int16)
        recv_kind = np.isin(kind, (TOP, STAIR_K, RAMP_K))
        for L in range(1, int(caster_lv.max()) + 1):
            C = caster_lv >= L
            recv = recv_kind & (self.lvl < L)
            # treads only take the west cheek's shadow; the ground under the face takes all
            for t in range(1, SHADOW + 1):
                hit = _shift(C, t, t) & recv & (dist > t)
                dist[hit] = t
        for y, x in zip(*np.nonzero(dist <= SHADOW)):
            t = dist[y, x]
            if t <= 3:
                self.mul(x, y, STRONG)
            elif t <= 6:
                self.mul(x, y, MEDIUM)
            elif (x // 2 + y // 2) % 2:
                self.mul(x, y, MEDIUM)            # dithered in 2 x 2 blocks, never single pixels

    def foot_grass(self):
        """Tall grass gathers at the foot of each face and strip, carried round the corners.
        (Now drawn as clumps by dress(); this only remains for dress=False.)"""
        if self.dressed:
            return
        kind = self.kind
        H, W = self.H, self.W
        for y in range(1, H - 1):
            for x in range(W):
                if kind[y, x] != TOP or self.wet[y, x]:
                    continue
                above = kind[y - 1, x] in (FACE_K, STRIP_K)
                if not above:
                    continue
                if self.n(x // 3, y, 541) < 0.55:
                    continue
                g = grass_ramp(int(self.lvl[y, x]))
                h = 3 + int(self.n(x, y, 542) * 3)
                for t in range(h):
                    yy = y + 1 - t
                    if 0 <= yy < H:
                        self.foot_blades.append((x + (1 if t > h - 2 and x % 2 else 0), yy,
                                                 g[1] if t < 2 else g[3] if t < h - 1 else g[4]))

    # the faces
    def _u_map(self):
        """Per face pixel: a horizontal coordinate that runs on round the corners (compressed
        over the last 8 px of a run, so lumps and courses narrow as they turn) and the facing:
        -1 turning west (lit) .. 0 south .. +1 turning east (dark)."""
        H, W = self.H, self.W
        kind, sreg = self.kind, self.sreg
        u = np.zeros((H, W), np.float32)
        phi = np.zeros((H, W), np.float32)
        member = np.isin(kind, (FACE_K, FALL_K, CHEEK_K, STAIR_K)) | ((kind == STRIP_K) & (sreg == 1))
        for y in range(H):
            x = 0
            while x < W:
                if not member[y, x]:
                    x += 1
                    continue
                a = x
                while x < W and member[y, x]:
                    x += 1
                b = x - 1
                # a run turns only where it ends against lower ground (an outer corner);
                # against a side strip (an inner corner) or the zone's edge it runs on flat
                t_e = b < W - 1 and kind[y, b + 1] == TOP and not self.wet[y, b + 1]
                t_w = a > 0 and kind[y, a - 1] == TOP and not self.wet[y, a - 1]
                for xx in range(a, b + 1):
                    de, dw = b - xx, xx - a
                    uu = float(xx)
                    p = 0.0
                    if de < 8 and t_e:
                        uu += (8 - de)
                        p = max(0.0, 1 - de / 7)
                    if dw < 8 and t_w:
                        uu -= (8 - dw)
                        p = min(p, -max(0.0, 1 - dw / 7)) if p == 0 else p
                    if kind[y, xx] == STRIP_K:
                        p = float(self.sdir[y, xx])
                    u[y, xx] = uu
                    phi[y, xx] = p
        return u, phi

    def faces(self):
        H, W, kind = self.H, self.W, self.kind
        u, phi = self._u_map()
        phi[kind == STRIP_K] = 0.5 * self.sdir[kind == STRIP_K]   # a side turns one step from the light
        self.u, self.phi = u, phi
        sel = (kind == FACE_K) | ((kind == STRIP_K) & (self.sreg == 1)) | (kind == FALL_K)
        ids = {}
        for y, x in zip(*np.nonzero(sel)):
            m = MATS[self.fmat[y, x]]
            d = max(0, int(y - self.rim[y, x]))
            ids[(x, y)] = self._struct(m, float(u[y, x]), y, d, x)
        for y, x in zip(*np.nonzero(sel)):
            if kind[y, x] == FALL_K:
                continue
            m = MATS[self.fmat[y, x]]
            d = max(0, int(y - self.rim[y, x]))
            hgt = int(self.fh[y, x])
            c = self._shade(m, x, y, d, hgt, float(phi[y, x]), ids)
            self.put(x, y, c)
        self._earth_clods()

    def _earth_clods(self):
        """Earth faces as Eastward draws them: rounded clods packed like scales, each lit on
        its upper left with a dark cool gap under it, lower clods overlapping upper ones;
        the odd mossy clod or embedded rock; darker toward the foot; turned by the light
        round corners and on the side bands; a dark outline where the face meets ground."""
        kind, H, W = self.kind, self.H, self.W
        earth = self.fmat == MATS.index('earth')
        M = earth & np.isin(kind, (FACE_K, STRIP_K))
        if not M.any():
            return
        ys, xs = np.nonzero(M)
        for y, x in zip(ys, xs):
            self.img[y, x] = rgb(CREV)
        # how high up the face each pixel is (0 top .. 1 foot)
        f = np.zeros((H, W), np.float32)
        fm = M & (kind == FACE_K) | (M & (self.sreg == 1))
        f[fm] = np.clip((np.arange(H)[:, None] - self.rim) / np.maximum(1, self.fh), 0, 1)[fm]
        side = M & (kind == STRIP_K) & (self.sreg == 0)
        f[side] = (self.sk[side] / STRIP)
        R = RAMPS['earth']
        y0, y1, x0, x1 = ys.min() - 4, ys.max() + 5, xs.min() - 6, xs.max() + 7
        sd = self.seed * 101 + 700
        clods = []
        for j, cy in enumerate(range(y0, y1, 5)):
            for i, cx in enumerate(range(x0 + (4 if j % 2 else 0), x1, 8)):
                a = noise2(i, j, sd)
                b = noise2(i, j, sd + 1)
                rx = 3.4 + noise2(i, j, sd + 2) * 2.2
                clods.append((cy + (b - 0.5) * 2.4, cx + (a - 0.5) * 3.0, rx, rx * (0.72 + 0.2 * b), i, j))
        clods.sort()
        for (cy, cx, rx, ry, i, j) in clods:
            v = noise2(i, j, sd + 3)
            t = 3 if v > 0.45 else 2
            if v > 0.86:
                t = 4
            moss = noise2(i, j, sd + 4) > 0.9
            rock = not moss and noise2(i, j, sd + 5) > 0.94
            hue = noise2(i, j, sd + 6)
            tint = ('#6A5A78', 0.28) if hue > 0.78 else ('#B08A58', 0.22) if hue < 0.16 else None
            for yy in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for xx in range(int(cx - rx) - 1, int(cx + rx) + 2):
                    if not (0 <= xx < W and 0 <= yy < H) or not M[yy, xx]:
                        continue
                    nx, ny = (xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry
                    e = nx * nx + ny * ny
                    if e > 1:
                        continue
                    if e > 0.62 and 0.45 * nx + ny > 0.35:
                        self.put(xx, yy, CREV)                 # its dark underside, the gap
                        continue
                    lit = -(0.55 * nx + 0.85 * ny)
                    i2 = t + (1 if lit > 0.4 else 0) - (1 if lit < -0.45 else 0)
                    ph = float(self.phi[yy, xx])
                    side_px = kind[yy, xx] == STRIP_K and self.sreg[yy, xx] == 0
                    i2 += (0 if side_px else (-1 if ph > 0.3 else 0) + (-1 if ph > 0.75 else 0)) + (1 if ph < -0.4 else 0)
                    i2 -= 1 if f[yy, xx] > 0.82 else 0
                    i2 = max(1, min(5, i2))
                    if moss and lit > -0.1 and ph < 0.5:
                        g = grass_ramp(int(self.ftop[yy, xx]))
                        c = g[3] if lit > 0.4 else g[2]
                    elif rock:
                        c = ROCK[min(5, i2 + 1)]
                    else:
                        c = R[i2] if tint is None else lerp(R[i2], tint[0], tint[1])
                    self.put(xx, yy, c)
        # the side bands (beside a tier's top) carry on the same clods, turned one step
        # (lighter facing west, darker facing east) and cut by the outline, so a long side
        # reads as the same lumpy earth as the corner and the south face
        # the outline where the face meets the ground: the band's outer edge, the foot row
        for y, x in zip(ys, xs):
            outer = kind[y, x] == STRIP_K and self.sk[y, x] == STRIP
            foot = y + 1 < H and kind[y + 1, x] == TOP and not M[y + 1, x] and kind[y, x] == FACE_K
            if outer or foot:
                self.put(x, y, OUTLINE if (self.sdir[y, x] > 0 or foot) else R[1])
        # the band's outer edge bulges a pixel where a lump sits, as Eastward's banks do
        for y, x in zip(*np.nonzero(side & (self.sk == STRIP))):
            dr = int(self.sdir[y, x])
            pos, ln, sid = self._seg(x - dr * STRIP, y)
            ox = x + dr
            if 0 < pos < ln - 1 and ln >= 5 and 0 <= ox < W and kind[y, ox] == TOP and not self.wet[y, ox]:
                self.put(ox, y, OUTLINE if dr > 0 else R[1])
                self.put(x, y, R[2] if dr > 0 else R[3])

    def _struct(self, m, u, y, d, x):
        s = self.seed * 31
        if m == 'earth':
            return _lump(u, y, s + 600)
        if m == 'stone':
            if d < 4:
                return ('cope',)
            return _block(u, d - 4, 6, s + 610, 14, 8)
        if m == 'concrete':
            if d < 4:
                return ('cope',)
            ci = (d - 4) // 8
            return (ci, _bay(u + ci * 11, s + 625, 16, 26)[0])
        if m == 'timber':
            if d < 3:
                return ('cap',)
            return ((d - 3) // 4,)
        if m == 'sandstone':
            return _strata(d, s + 620)[0]
        return 0

    def _shade(self, m, x, y, d, hgt, phi, ids):
        R = RAMPS[m]
        top = len(R) - 1
        me = ids.get((x, y))
        up, dn = ids.get((x, y - 1)), ids.get((x, y + 1))
        rt, lf = ids.get((x + 1, y)), ids.get((x - 1, y))
        foot = hgt - d                       # rows to the foot (1 = the last row)
        turn = -1 if phi > 0.3 else 0
        turn += -1 if phi > 0.75 else 0
        turn += 1 if phi < -0.4 else 0
        n = lambda a, b, s: noise2(a, b, self.seed * 101 + s)  # noqa: E731
        if m == 'earth':
            t = 3 if n(*me, 601) > 0.45 else 2
            if n(*me, 602) > 0.88:
                t = 4
            if up != me:
                i = t + 1 if phi <= 0.5 else t  # each lump's lit top (dimmed as it turns away)
            elif dn != me and dn is not None:
                i = 0                           # the crevice under it
            elif rt != me and rt is not None:
                i = 1                           # and down its right side
            elif lf != me and lf is not None and t < 4:
                i = t + 1 if (x + y) % 2 else t
            else:
                i = t
                if n(x, y, 603) > 0.94:
                    i = max(1, t - 1)
            if i:
                i = max(1, min(top, i + turn))
            if 2 <= d <= 4 and i > 1:
                i -= 1                          # the start row, in the lip's shade
            if up != me and n(*me, 604) > 0.9 and phi > -0.5 and phi < 0.5:
                return GRASS[2] if (x + y) % 2 else LEAF[2]      # moss on a lump
            if foot <= 4:
                i = min(i, 1) if foot <= 2 else max(0, min(i, 2) - (1 if phi > 0.3 else 0))
                if foot <= 2 and n(x, y, 605) > 0.75:
                    return LEAF[1]                                  # weed in the damp foot
            return R[i]
        if m == 'stone':
            if me == ('cope',):
                i = [5, 4, 3, 1][min(3, d)]
                if d == 1 and n(x // 9, 0, 611) > 0.8:
                    i = 3                        # a chipped coping
                return R[max(0, min(top, i + turn))]
            ci, bi = me
            t = 3 if n(ci, bi, 612) > 0.4 else 2
            if n(ci, bi, 613) > 0.9:
                t = 4
            if dn != me and dn is not None and dn != ('cope',):
                i = 1                            # the bed joint
            elif lf != me and lf is not None and lf != ('cope',):
                i = 1                            # the head joint
            elif up != me:
                i = t + 1                        # the block's lit arris
            elif rt != me and rt is not None:
                i = max(1, t - 1)                # shade at its right end
            else:
                i = t
            i = max(0, min(top, i + turn)) if i > 1 else max(0, i + min(0, turn))
            if foot <= 4:
                i = max(0, min(i, 2) - (1 if foot <= 2 else 0))
                if foot <= 3 and n(x, y, 614) > 0.7:
                    return LEAF[1] if (x + y) % 2 else LEAF[2]   # moss in the lower joints
            return R[i]
        if m == 'concrete':
            if me == ('cope',):
                return R[max(0, min(top, [4, 3, 2, 0][min(3, d)] + turn))]
            ci, pi = me
            if (dn != me and dn is not None) or (lf != me and lf is not None):
                i = 1
            else:
                i = 3 if smooth_noise(x, y, 9, 621) > 0.5 else 2
                if n(x // 2, 0, 622) > 0.8 and (d - 4) < 4 + int(n(x // 2, 1, 623) * 14):
                    i = max(1, i - 1)            # rain streaks from the coping
            i = max(0, min(top, i + turn))
            if foot <= 4:
                i = min(i, 1)
                if foot <= 2 and n(x, y, 624) > 0.6:
                    return LEAF[1]
            return R[i]
        if m == 'timber':
            if me == ('cap',):
                return R[max(0, min(top, [4, 3, 0][min(2, d)] + turn))]
            pl = me[0]
            r = (d - 3) % 4
            t = 3 if n(pl, x // 37, 631) > 0.4 else 2
            i = [t + 1, t, t, 0][r]
            post = _bay(float(self.u[y, x]), self.seed * 31 + 632, 16, 24)[1]
            if post < 3 or abs(phi) > 0.6:
                i = [4, 3, 1][min(2, post)] if abs(phi) <= 0.6 else (4 if phi < 0 else 1)
                if r == 1 and post == 1:
                    return STONE[4]              # a nail head
            if foot <= 2:
                i = min(i, 1)
            if i:
                i = max(1, min(top, i + turn))
            return R[i]
        if m == 'sandstone':
            si, rr, th = _strata(d, self.seed * 31 + 620)
            t = 2 + si % 3
            i = t + 1 if rr == 0 else (1 if rr == th - 1 and n(si, x // 6, 641) > 0.5 else t)
            if n(x // 3, y, 642) > 0.95:
                i = max(1, t - 1)                 # a pit
            i = max(0, min(top, i + turn))
            if foot <= 3:
                i = min(i, 2)
            return R[i]
        return R[2]

    def strips(self):
        """The side region of each strip (beside a tier's top, above its corner): the face seen
        nearly edge on. Across the strip runs the face's height (the lip at the rim line, the
        foot at its outer edge), down it runs the face's length."""
        kind, sreg = self.kind, self.sreg
        for y, x in zip(*np.nonzero((kind == STRIP_K) & (sreg == 0))):
            k, dr = int(self.sk[y, x]), int(self.sdir[y, x])
            m = MATS[self.fmat[y, x]]
            R = RAMPS[m]
            top = len(R) - 1
            ex = x - dr * k                       # the rim line's column (outside the strip)
            lit = dr < 0
            n = lambda a, b, s: noise2(a, b, self.seed * 101 + s)  # noqa: E731
            # lumps / blocks along the strip: boundaries every 5 to 9 px
            seg = self._seg(ex, y)
            pos, ln, sid = seg
            split = n(sid, ex, 651) > 0.6 and k >= 3
            if m == 'earth':
                continue                          # (drawn as clods with the face)
                body = 4 if lit else 1
                if n(sid, ex, 652) > 0.6:
                    body += -1 if lit else 1
                if pos == ln - 1 or (split and k == 3):
                    i = 3 if lit else 0           # the crevice under each lump
                elif pos == 0:
                    i = body + 1                  # the lump's lit top
                else:
                    i = body
                if k == STRIP:                    # its outer edge, where it meets the ground
                    i = (4 if pos not in (0, ln - 1) else 3) if lit else 0
                self.put(x, y, R[max(0, min(top, i))])
                if lit and k == STRIP:            # a west face keeps only a contact line
                    self.mul(x - 1, y, MEDIUM)
            elif m in ('stone', 'concrete'):
                # a column of blocks seen end on: the coping's edge along the rim line, each
                # block lit on its top, a dark joint under it, an outline on the outer edge
                if k == 1:
                    i = top if lit else 3         # the coping's edge, catching the light
                elif k == STRIP:
                    i = 1 if lit else 0           # the outline where it meets the ground
                elif pos == ln - 1:
                    i = 1 if lit else 0           # the joint
                elif pos == 0:
                    i = top - 1 if lit else 4     # the block's lit top
                else:
                    body = noise2(sid, ex, self.seed + 657) > 0.5
                    i = (3 if body else top - 2) if lit else 2
                    if m == 'concrete':
                        i = 3 if lit else 1
                self.put(x, y, R[max(0, min(top, i))])
                if lit and k == STRIP:
                    self.mul(x - 1, y, MEDIUM)
            elif m == 'timber':
                if k == STRIP:
                    i = 1 if lit else 0
                elif pos == 0 and sid % 3 == 0:
                    i = 4 if lit else 2
                else:
                    i = (3 if k % 2 else 4) if lit else (1 if k % 2 else 2)   # planks seen end on
                self.put(x, y, R[max(0, min(top, i))])
            else:  # sandstone: strata run down the strip
                i = (4 if lit else 2) - (k % 2)
                if k == STRIP:
                    i = 1 if lit else 0
                self.put(x, y, R[max(0, min(top, i))])

    def _seg(self, ex, y):
        """Where y lies in the strip's run of lumps: (row in the lump, its length, its id)."""
        key = ex
        cache = self.__dict__.setdefault('_segs', {})
        if key not in cache:
            bounds, b, i = [], -20, 0
            while b < self.H + 20:
                bounds.append(b)
                b += 5 + int(noise2(i, ex, self.seed * 101 + 653) * 5)
                i += 1
            cache[key] = bounds
        bounds = cache[key]
        lo = 0
        for i, b in enumerate(bounds):
            if b <= y:
                lo = i
            else:
                break
        a = bounds[lo]
        z = bounds[lo + 1] if lo + 1 < len(bounds) else a + 8
        return y - a, z - a, lo

    def _dtop(self, L):
        """Px from each pixel to the nearest top of tier L or higher (1 = touching), up to 6."""
        cache = self.__dict__.setdefault('_dtops', {})
        if L not in cache:
            top = (self.kind == TOP) & (self.lvl >= L) & ~self.wet
            dist = np.full(top.shape, 99, np.int16)
            for r in range(1, 7):
                ring = [(dx, dy) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
                        if math.ceil(math.hypot(dx, dy) - 0.25) == r]
                hit = np.zeros_like(top)
                for dx, dy in ring:
                    hit |= _shift(top, dx, dy)
                dist[hit & (dist > r)] = r
            cache[L] = dist
        return cache[L]

    def lips(self):
        """The rim: on earth a grass lip overhanging the face in scallops of 1 to 3 px, lit on
        top and dark under, wrapping round the corners and down the side strips; on built
        faces the coping is the lip and grass only breaks over it here and there."""
        kind, H, W = self.kind, self.H, self.W
        for y, x in zip(*np.nonzero(np.isin(kind, (FACE_K, STRIP_K)))):
            m = MATS[self.fmat[y, x]]
            L = int(self.ftop[y, x])
            g = grass_ramp(L)
            if kind[y, x] == FACE_K or (kind[y, x] == STRIP_K and self.sreg[y, x] == 1):
                r0 = int(self.rim[y, x])
                if r0 < 0:
                    continue
                if self.ramp_h[max(0, r0 - 1), x]:
                    continue                         # a ramp's front: no grass lip
                # how far below the top's edge, measured round the corner's curve, so the
                # lip wraps an outer corner instead of stopping at the rim row
                d = min(y - r0, int(self._dtop(L)[y, x]) - 1)
                sc = (x + int(noise2(x // 7, r0, self.seed + 553) * 4)) % 7
                k = 1 + (2 if sc in (2, 3, 4) else 1 if sc in (1, 5) else 0)
                if kind[y, x] == STRIP_K:
                    k = max(1, k - 1)
                if m == 'earth' or m == 'sandstone':
                    if m == 'sandstone':
                        k = max(1, k - 1)
                    if d < k:   # the lip: lit edge, body, dark underside
                        c = (g[3] if (x // 3) % 3 else lerp(g[3], g[4], 0.5)) if d == 0 else \
                            g[2] if d < k - 1 else g[1]
                        self.put(x, y, c)
                    elif d == k:
                        self.put(x, y, CREV if m == 'earth' else RAMPS[m][1])
                    elif d == k + 1 and m == 'earth' and kind[y, x] == FACE_K:
                        self.mul(x, y, (0.78, 0.76, 0.84))   # the clods in the lip's shade
                    if d == 0 and y > 0 and kind[y - 1, x] == TOP:
                        self.put(x, y - 1, g[4] if (x // 3) % 3 else g[3])
                else:
                    tuftk = noise2(x // 3, r0, self.seed + 554)
                    if tuftk > 0.72 and d < (2 if tuftk > 0.86 else 1):
                        self.put(x, y, g[2] if d == 0 else g[1])
                    if d == 0 and y > 0 and kind[y - 1, x] == TOP:
                        self.put(x, y - 1, g[4] if (x // 3) % 3 else g[3])
            else:
                k = int(self.sk[y, x])
                dr = int(self.sdir[y, x])
                lit = dr < 0
                ex = x - dr * k
                sc = (y + int(noise2(y // 6, ex, self.seed + 555) * 4)) % 6
                kk = 1 if sc in (2, 3) else 0           # the lip wraps the side in small scallops
                if m in ('earth', 'sandstone'):
                    if k <= kk:
                        self.put(x, y, g[3] if lit else (g[2] if k == 1 else g[1]))
                    elif k == kk + 1 and m == 'earth' and not lit:
                        self.put(x, y, SOIL[0])
                    if k == 1:
                        tx = x + dr
                        if 0 <= tx < W and kind[y, tx] == TOP:
                            self.put(tx, y, g[4] if lit else g[3])
                else:
                    if k == 1 and noise2(y // 3, ex, self.seed + 556) > 0.75:
                        self.put(x, y, g[2])
        # roots hanging from earth lips, stones set in the faces
        for y, x in zip(*np.nonzero((kind == FACE_K))):
            if MATS[self.fmat[y, x]] != 'earth' or y != self.rim[y, x] or self.fh[y, x] < 20:
                continue
            if noise2(x, y, self.seed + 561) > 0.9 and abs(self.phi[y, x]) < 0.3:
                ln = 4 + int(noise2(x, y, self.seed + 562) * 9)
                for t in range(ln):
                    xx, yy = x + (t // 5) * (1 if x % 2 else -1), y + 3 + t
                    if 0 <= xx < W and 0 <= yy < H and kind[yy, xx] == FACE_K:
                        self.put(xx, yy, SOIL[0] if (t // 2) % 2 else '#4A3022')
        for (x, y, c) in self.foot_blades:   # tall grass at the feet, over the face's foot
            if 0 <= x < W and 0 <= y < H and kind[y, x] in (TOP, FACE_K, STRIP_K):
                self.put(x, y, c)

    def stairs_paint(self):
        for si, st in enumerate(self.stairs):
            x0 = st.x
            x1 = st.x + 2 * st.cheek + st.w
            hgt = int(self.fh[st.rim, x0 + st.cheek + 1])
            stone = st.material == 'stone'
            R = RAMPS['stone'] if stone else WOOD
            for y in range(st.rim, min(self.H, st.rim + hgt)):
                d = y - st.rim
                r = d % RISER
                step = d // RISER
                for x in range(x0, x1):
                    k = self.kind[y, x]
                    if k == CHEEK_K:
                        west = x < x0 + st.cheek
                        c0 = (x - x0) if west else (x - (x1 - st.cheek))
                        if stone:
                            tones = [5, 4, 4, 2] if west else [3, 1, 1, 0]
                            i = tones[c0]
                            if d < 3:
                                i = 5 if west else 3        # the cheek's coping
                                if d == 2:
                                    i = 2 if west else 1
                            elif (d - 3) % 6 == 5:
                                i = max(0, i - 2)           # its courses
                            self.put(x, y, R[i])
                        else:
                            tones = [4, 3, 3, 1] if west else [2, 1, 1, 0]
                            i = tones[c0]
                            if d < 2:
                                i = 4 if west else 2        # the post cap
                            self.put(x, y, R[i])
                    elif k == STAIR_K:
                        xi = x - x0 - st.cheek
                        worn = st.w * 0.3 < xi < st.w * 0.7
                        if stone:
                            j = (xi + step * 7) % 13 == 0
                            i = [5 if worn else 4, 3, 3 if not j else 1, 1][r]
                            if r == 3:
                                i = 1
                        else:
                            i = [4, 3, 2, 0][r]
                            if r in (1, 2) and xi % 12 == 6:
                                i = 1                       # the stake holding each tread
                            if r == 0 and worn:
                                self.put(x, y, '#D8B87C')
                                continue
                        self.put(x, y, R[i])
            # the west cheek shades the first treads (cast shadow takes the rest)
            for y in range(st.rim, min(self.H, st.rim + hgt)):
                for t in (0, 1, 2):
                    x = x0 + st.cheek + t
                    if self.kind[y, x] == STAIR_K and (t < 2 or (y // 2) % 2):
                        self.mul(x, y, STRONG if t == 0 else MEDIUM)

    def ramps_paint(self):
        """The path down a ramp's cut: trodden earth (or slabs), a little darker than level
        ground because the slope turns away from the light, soft ridges across it where the
        feet push the soil down, a worn track in the middle, pebbles by the walls, grass
        breaking over its top."""
        for rp in self.ramps:
            xa, xb = rp.x0 + STRIP, rp.x1 - STRIP
            for x in range(rp.x0, rp.x1):
                ys = [y for y in range(rp.top, self.H) if self.kind[y, x] == RAMP_K]
                if not ys:
                    continue
                y0, y1 = min(ys), max(ys)
                for y in ys:
                    xi = (x - xa) / max(1, xb - xa - 1)
                    if rp.material == 'stone':
                        bx = _bay(x + (y - y0) // 6 * 9, self.seed + 571, 10, 16)
                        c = STONE[2] if bx[1] == 0 or (y - y0) % 6 == 5 else \
                            (STONE[3] if noise2(bx[0], (y - y0) // 6, self.seed + 572) > 0.45 else lerp(STONE[3], STONE[2], 0.5))
                    else:
                        f = (y - y0) / max(1, y1 - y0)                    # down the slope
                        v = smooth_noise(x, y, 6, self.seed + 573)
                        c = lerp(PATH[2], PATH[1], 0.15 + 0.3 * f) if v > 0.45 else lerp(PATH[1], PATH[2], 0.45 - 0.3 * f)
                        if 0.3 < xi < 0.7 and smooth_noise(x, y, 4, self.seed + 574) > 0.45:
                            c = lerp(c, PATH[0], 0.25)                    # the trodden track
                        if smooth_noise(x, y, 4, self.seed + 575) > 0.78:
                            c = lerp(c, PATH[3], 0.5)                     # a dry, lit hump
                        wd = min(x - rp.x0, rp.x1 - 1 - x) - STRIP
                        if wd < 2 and f > 0.15:
                            c = lerp(c, PATH[0], 0.3 if wd < 1 else 0.15)  # damp along the walls
                    self.put(x, y, c)
            for j, y in enumerate(range(rp.top + 3, self.H, 3)):        # the dirt's grain, in 2 px marks
                for i, x in enumerate(range(rp.x0 + (j % 2) * 2, rp.x1 - 1, 4)):
                    xx = x + int(noise2(i, j, self.seed + 580) * 3)
                    q = noise2(i, j, self.seed + 581)
                    if q > 0.55 or self.kind[y, xx] != RAMP_K or self.kind[y, xx + 1] != RAMP_K:
                        continue
                    base = tuple(int(v) for v in self.img[y, xx])
                    c = lerp(base, PATH[0], 0.3) if q < 0.25 else lerp(base, PATH[3], 0.35) if q < 0.42 else lerp(base, ROCK[2], 0.5)
                    self.put(xx, y, c); self.put(xx + 1, y, c)
            ys_all = [y for y in range(rp.top, self.H) if self.kind[y, (xa + xb) // 2] == RAMP_K]
            span = (max(ys_all) - rp.top) if ys_all else 1
            for k in range(span // 3):                                    # pebbles, more by the walls
                q = noise2(k, 2, self.seed + 576)
                x = xa + 1 + int((q * q if k % 2 else 1 - q * q) * (xb - xa - 4))
                y = rp.top + 4 + int(noise2(k, 1, self.seed + 576) * max(1, span - 6))
                if 0 <= y < self.H - 1 and self.kind[y, x] == RAMP_K and self.kind[y, x + 1] == RAMP_K:
                    self.put(x, y, ROCK[3]); self.put(x + 1, y, ROCK[2]); self.mul(x + 2, y, MEDIUM)
            for j, y in enumerate(range(rp.top + 10, rp.top + span, 7)):  # grass along the walls' feet
                for side, x in ((0, xa + 2), (1, xb - 3)):
                    if noise2(j, side, self.seed + 578) > 0.35 and self.kind[y, x] == RAMP_K:
                        self._tuft(x + int(noise2(j, side + 2, self.seed + 578) * 3) - 1, y, 1, j * 7 + side)
            for j in range(span // 12):                                  # a root or a rut across
                y = rp.top + 8 + int(noise2(j, 5, self.seed + 579) * max(1, span - 12))
                x = xa + 4 + int(noise2(j, 6, self.seed + 579) * max(1, xb - xa - 14))
                for t in range(4 + int(noise2(j, 7, self.seed + 579) * 5)):
                    if self.kind[y, x + t] == RAMP_K:
                        self.put(x + t, y, lerp(PATH[1], PATH[0], 0.5))
                        self.put(x + t, y - 1, lerp(PATH[2], PATH[3], 0.5))
            g = grass_ramp(int(self.ftop[rp.top, rp.x0]) if self.ftop[rp.top, rp.x0] else 1)
            for x in range(rp.x0, rp.x1):                                # grass breaking over its head
                h = 2 + int(noise2(x // 3, rp.top, self.seed + 577) * 3)
                for t in range(h):
                    if self.kind[rp.top + t, x] == RAMP_K:
                        self.put(x, rp.top + t, g[2] if t < h - 1 else g[1])

    def falls_paint(self):
        """A fall drops straight down the face as wide as its channel, white where it tips
        over the lip, spray on the face beside it, foam where it lands."""
        fall, H, W = self.fall, self.H, self.W
        lab = _components(fall)
        for k in range(1, lab.max() + 1):
            yy, xx = np.nonzero(lab == k)
            fx0, fx1, fy0, fy1 = xx.min(), xx.max() + 1, yy.min(), yy.max() + 1
            for y in range(fy0, fy1):
                for x in range(fx0, fx1):
                    if not fall[y, x]:
                        continue
                    kx = x - fx0
                    # sheets of falling water in columns two px wide, each streaked with
                    # runs of foam, light and blue (3 to 6 px), never a checker
                    col = kx // 2
                    ph = int(noise2(col, k, self.seed + 585) * 11)
                    r = (y + ph) % 11
                    c = FOAM if r < 3 else WTR[4] if r < 7 else WTR[3]
                    if kx in (0, fx1 - fx0 - 1):
                        c = WTR[2] if r >= 3 else WTR[3]
                    if y < fy0 + 2:
                        c = FOAM                                   # white where it tips over
                    self.put(x, y, c)
            for y in range(fy0, fy1):   # wet face beside it, and spray
                for x in (fx0 - 1, fx0 - 2, fx1, fx1 + 1):
                    if 0 <= x < W and self.kind[y, x] == FACE_K:
                        self.mul(x, y, (0.8, 0.84, 0.92))
                for side, x in ((0, fx0 - 2 - int(noise2(y, 0, self.seed + 583) * 2)),
                                (1, fx1 + 1 + int(noise2(y, 1, self.seed + 583) * 2))):
                    if noise2(y, side, self.seed + 584) > 0.72 and 0 <= x < W and self.kind[y, x] == FACE_K:
                        self.put(x, y, WTR[4])   # spray, irregular
            cx = (fx0 + fx1) / 2
            half = (fx1 - fx0) / 2 + 6
            for y in range(fy1, fy1 + 10):
                for x in range(int(fx0) - 6, int(fx1) + 6):
                    if not (0 <= x < W and 0 <= y < H) or not self.wet[y, x]:
                        continue
                    dd = abs(x + 0.5 - cx) / half + (y - fy1) / 9
                    v = smooth_noise(x, y, 2.5, self.seed + 581)          # foam in clumps
                    if dd < 1 and v > 0.25 + dd * 0.45:
                        self.put(x, y, FOAM if v > 0.55 + dd * 0.3 else WTR[4])
            for (rx, ry) in ((cx - 9, fy1 + 13), (cx + 8, fy1 + 11)):   # rings spreading out, as arcs
                for a in (200, 230, 260, 290, 320):
                    for da in (0, 8):
                        x = int(rx + 5 * math.cos(math.radians(a + da)))
                        y = int(ry + 2 * math.sin(math.radians(a + da)))
                        if 0 <= x < W and 0 <= y < H and self.wet[y, x] and not self.fall[y, x]:
                            self.put(x, y, lerp(WTR[2], WTR[3], 0.7))


    # ---- edge dressing ------------------------------------------------------------------
    def dress(self):
        """What makes Eastward's edges soft: shade pooled along every foot and in inner
        corners, worn ground there, loose rocks at the feet and corners, and tall grass that
        breaks every rim, corner and foot. Decoration only: the walk grid ignores it."""
        kind, H, W = self.kind, self.H, self.W
        wall = np.isin(kind, (FACE_K, STRIP_K, CHEEK_K))
        ground = (kind == TOP) & ~self.wet
        # 1. soft shade pooled down and right of every face and band (beyond the hard 8 px)
        dist = np.full((H, W), 99, np.int16)
        for t in range(1, 15):
            hit = np.zeros((H, W), bool)
            for dx in range(0, t + 1):
                hit |= _shift(wall, dx, t)
            hit |= _shift(wall, t, 0) | _shift(wall, t, t // 2)
            dist[hit & ground & (dist > t)] = t
        for y, x in zip(*np.nonzero(dist <= 14)):
            t = int(dist[y, x])
            if t <= 10 or (x // 2 + y // 2) % 2:
                self.mul(x, y, SOFT)
            if t <= 3 and noise2(x // 2, y, self.seed + 801) > 0.62:
                self.img[y, x] = lerp(self.img[y, x], PATH[1], 0.35)   # worn, damp ground
        # inner corners: where a band and a face both shade the same ground, it pools deeper
        band = (kind == STRIP_K)
        near_band = np.zeros((H, W), bool)
        near_face = np.zeros((H, W), bool)
        for d in range(1, 9):
            near_band |= _shift(band, d, 0) | _shift(band, -d, 0)
            near_face |= _shift(kind == FACE_K, 0, d)
        for y, x in zip(*np.nonzero(near_band & near_face & ground)):
            self.mul(x, y, SOFT)
        # 2. the feet: runs of ground directly under a face or beside a band's outer edge
        feet = []
        for y in range(1, H - 1):
            for x in range(W):
                if ground[y, x] and kind[y - 1, x] in (FACE_K, STRIP_K) and self.stair_id[y - 1, x] < 0:
                    feet.append((x, y, int(self.lvl[y, x])))
        corners = []
        for y in range(1, H - 1):       # outer corners: the foot row's ends against a band
            for x in range(1, W - 1):
                if kind[y, x] == STRIP_K and kind[y + 1, x] == TOP and self.sk[y, x] >= STRIP - 1 and \
                        kind[y, x - int(self.sdir[y, x])] in (FACE_K, STRIP_K):
                    corners.append((x, y + 1, int(self.sdir[y, x])))
        # lusher, darker grass gathering in the damp along each foot
        for y, x in zip(*np.nonzero((dist <= 7) & ground)):
            if smooth_noise(x, y, 4, self.seed + 805) > 0.4 - 0.04 * (7 - int(dist[y, x])):
                self.img[y, x] = lerp(self.img[y, x], '#2E5A3C', 0.22)
        # leafy sprigs and pebbles among the grass at the feet
        for (x, y, L) in feet:
            b, off = _bay(x * 1.0 + y * 11, self.seed + 806, 12, 30)
            if off in (5, 15) and noise2(b + off, y, self.seed + 807) > 0.25:
                self._sprig(x, y + 5 + int(noise2(b, y, self.seed + 808) * 5), b)
            elif off in (9, 21) and noise2(b + off, y, self.seed + 809) > 0.35:
                yy = y + 3 + int(noise2(b, y, self.seed + 810) * 4)
                for (dx, c) in ((0, ROCK[3]), (1, ROCK[2])):
                    self.put(x + dx, yy, c)
                self.put(x + 3, yy + 1, STONE[3]); self.put(x + 4, yy + 1, STONE[2]); self.mul(x + 2, yy, MEDIUM)
        # rocks: a few per run, irregular bays; a bigger one at each outer corner
        for (x, y, L) in feet:
            b, off = _bay(x + y * 3, self.seed + 811, 18, 44)
            if off == 6 and noise2(b, y, self.seed + 812) > 0.45:
                self._rock(x, y + 1, 1.6 + noise2(b, y, self.seed + 813) * 2.2, b)
        seen = set()
        for (x, y, dr) in corners:
            key = (x // 8, y // 8)
            if key in seen:
                continue
            seen.add(key)
            if noise2(*key, self.seed + 814) > 0.35:
                self._rock(x + dr * 3, y + 1, 2.4 + noise2(*key, self.seed + 815) * 1.6, key[0] * 7 + key[1])
        # tall grass: clumps along feet, at corners, and leaning over rims from the top
        for (x, y, L) in feet:
            b, off = _bay(x * 1.0 + y * 5, self.seed + 821, 9, 22)
            if off in (2, 13) and noise2(b + off, y, self.seed + 822) > 0.25:
                self._clump(x, y + 1, L, 4 + int(noise2(b, y, self.seed + 823) * 4), b)
        for (x, y, dr) in corners:
            self._clump(x + dr, y + 1, int(self.lvl[min(H - 1, y), x]), 7, x * 13 + y)
        # reeds and grass along the banks of streams and pools
        bank = _banks(self.wet, kind)
        for y, x in zip(*np.nonzero(bank)):
            if y + 1 < H and (self.wet[y + 1, x] or (x + 1 < W and self.wet[y, x + 1]) or self.wet[y, x - 1]):
                b, off = _bay(x * 1.0 + y * 7, self.seed + 861, 9, 20)
                if off == 1 and noise2(b, y, self.seed + 862) > 0.45:
                    self._clump(x, y + 1, int(self.lvl[y, x]), 4 + int(noise2(b, y, self.seed + 863) * 3), b)
        for y in range(1, H - 1):      # rims: on the top, just behind the lip
            for x in range(1, W - 1):
                if kind[y, x] == TOP and kind[y + 1, x] == FACE_K and self.rim[y + 1, x] == y + 1 and \
                        not self.wet[y, x] and self.stair_id[y + 1, x] < 0:
                    b, off = _bay(x * 1.0, self.seed + 831 + y, 10, 26)
                    if off == 3 and noise2(b, y, self.seed + 832) > 0.35:
                        self._clump(x, y + 1, int(self.lvl[y, x]), 4 + int(noise2(b, y, self.seed + 833) * 3), b,
                                    droop=True)
                # beside a band's outer edge, on the lower ground: grass rising over its foot
                beside = ground[y, x] and ((kind[y, x - 1] == STRIP_K and self.sdir[y, x - 1] > 0) or
                                           (kind[y, x + 1] == STRIP_K and self.sdir[y, x + 1] < 0))
                if beside and noise2(x, y // 11, self.seed + 834) > 0.8 and y % 11 == 5:
                    self._clump(x, y + 3, int(self.lvl[y, x]), 4 + (y % 3), x * 31 + y)

    def weather(self):
        """Built faces and stone stairs weathered to the same grain as earth: mottled stone,
        pits and light flecks, chipped arrises, rain streaks under the coping, the odd crack,
        and moss gathering low on the face and in the joints."""
        kind, H, W = self.kind, self.H, self.W
        built = np.isin(self.fmat, (MATS.index('stone'), MATS.index('concrete')))
        sel = built & np.isin(kind, (FACE_K, STRIP_K, CHEEK_K, STAIR_K))
        sd = self.seed * 101 + 900
        for y, x in zip(*np.nonzero(sel)):
            m = MATS[self.fmat[y, x]]
            R = RAMPS[m]
            c = self.img[y, x]
            hgt = max(1, int(self.fh[y, x]))
            f = (y - int(self.rim[y, x])) / hgt if self.rim[y, x] >= 0 else 0.5
            mo = smooth_noise(x, y, 8 if kind[y, x] != STAIR_K else 7, sd)
            if mo > 0.66:
                c = lerp(c, '#6E6252', 0.16)               # warm grime
            elif mo < 0.3:
                c = lerp(c, '#98A0AC', 0.14)               # cool, rain-washed
            n = noise2(x // 2, y, sd + 1) if kind[y, x] != STAIR_K else 0.5
            if n > 0.97:
                c = lerp(c, R[1], 0.4)                     # a pit (2 px)
            elif n < 0.02:
                c = lerp(c, R[-1], 0.45)                   # a light fleck (2 px)
            col = noise2(x, 0, sd + 2)
            if kind[y, x] == FACE_K and col > 0.8 and 0.12 < f < 0.12 + col * 0.6:
                c = lerp(c, '#3E3A40', 0.18)               # a rain streak from the coping
            moss = smooth_noise(x, y, 3.2, sd + 3)
            def mossy(yy, ff):
                mv = smooth_noise(x, yy, 3.2, sd + 3)
                return (ff > 0.6 and mv > 0.66) or mv > 0.8
            if kind[y, x] != STAIR_K and mossy(y, f):
                c = LEAF[3] if not mossy(y - 1, f - 1 / hgt) else LEAF[2]   # moss cushions, lit on top
            self.img[y, x] = rgb(c)
        # timber and sandstone faces: grain, knots and bleaching; holes, chips and varnish
        for y, x in zip(*np.nonzero(np.isin(self.fmat, (MATS.index('timber'), MATS.index('sandstone'))) &
                                    np.isin(kind, (FACE_K,)))):
            m = MATS[self.fmat[y, x]]
            c = self.img[y, x]
            d = y - int(self.rim[y, x])
            if m == 'timber':
                if d >= 3 and (d - 3) % 4 in (1, 2):
                    g0 = noise2(x // 5, y, sd + 11)
                    if g0 > 0.7:
                        c = lerp(c, WOOD[1], 0.35)                 # a grain streak (5 px)
                    elif g0 < 0.12:
                        c = lerp(c, WOOD[4], 0.35)                 # a lit splinter
                kn = noise2(x // 2, (y - 1) // 2, sd + 12)
                if kn > 0.965 and (d - 3) % 4 in (1, 2):
                    c = WOOD[0]                                    # a knot (2 x 2)
                b = smooth_noise(x, y, 6, sd + 13)
                if b > 0.68:
                    c = lerp(c, '#C8B89A', 0.2)                    # sun-bleached
                elif b < 0.25:
                    c = lerp(c, '#3E4A30', 0.15)                   # damp, greening
            else:
                hole = noise2(x // 2, y // 2, sd + 14)
                if hole > 0.95:
                    c = lerp(c, RAMPS['sandstone'][0], 0.55)       # a weathered hole (2 x 2)
                elif hole < 0.04:
                    c = lerp(c, RAMPS['sandstone'][-1], 0.5)       # a pale pebble (2 x 2)
                v = noise2(x, 7, sd + 15)
                if v > 0.8 and d > 2 and d < 4 + v * 20:
                    c = lerp(c, '#5A3A30', 0.22)                   # desert varnish from the lip
                b = smooth_noise(x, y, 7, sd + 16)
                c = lerp(c, '#E8C898', 0.15) if b > 0.66 else lerp(c, '#8A5A48', 0.12) if b < 0.3 else c
            self.img[y, x] = rgb(c)
        # a few cracks: short zigzags down from a joint
        for k in range(int(sel.sum() / 220)):
            ys, xs = np.nonzero(sel & (kind == FACE_K))
            if not len(xs):
                break
            i = int(noise2(k, 1, sd + 4) * len(xs))
            x, y = int(xs[i]), int(ys[i])
            for t in range(3 + int(noise2(k, 2, sd + 4) * 5)):
                if 0 <= x < W and 0 <= y < H and sel[y, x] and kind[y, x] == FACE_K:
                    self.img[y, x] = lerp(self.img[y, x], '#2A2630', 0.6)
                y += 1
                x += 1 if noise2(k, t, sd + 5) > 0.55 else (-1 if noise2(k, t, sd + 6) > 0.7 else 0)

    def _sprig(self, x, y, k):
        """A small leafy plant: paired leaves lit on top, a short stem; every part 2 px or more."""
        flip = noise2(k, 4, self.seed + 891) > 0.5
        big = noise2(k, 5, self.seed + 892) > 0.45
        pat = ['.ll....', 'llmm.hh', '..mmhh.', 'dd.dd..', '..dd...'] if big else ['..ll.', 'llm..', '.mmdd', '..d..', '..d..']
        col = {'l': '#86C08A', 'h': '#5E9E74', 'm': '#3F7A5E', 'd': '#2A5244'}
        for j, row in enumerate(pat):
            for i, ch in enumerate(row):
                if ch != '.':
                    xx = x + (4 - i if flip else i) - 2
                    yy = y - 4 + j
                    if 0 <= xx < self.W and 0 <= yy < self.H and self.kind[yy, xx] == TOP:
                        self.put(xx, yy, col[ch])
        self.mul(x + 2, y + 1, MEDIUM); self.mul(x + 3, y + 1, MEDIUM)

    def _rock(self, cx, by, r, k):
        """A loose rock sitting on the ground, its base at row by: lit upper left, outlined,
        a hard shadow down and right."""
        rx, ry = r * 1.25, r
        cy = by - ry + 0.5
        pts = [(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2) for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
               if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1]
        if not pts:
            return
        ps = set(pts)
        for (x, y) in pts:   # shadow first
            self.mul(x + 2, y + 1, STRONG) if (x + 2, y + 1) not in ps else None
        warm = noise2(k, 1, self.seed + 841) > 0.4
        R = ROCK if warm else STONE
        top = len(R) - 1
        for (x, y) in pts:
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            lit = -(0.6 * nx + 0.8 * ny)
            i = 3 if lit > 0.35 else 2 if lit > -0.3 else 1
            if lit > 0.75:
                i = 4
            self.put(x, y, R[min(top, i + (1 if warm else 0))])
        for (x, y) in pts:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in ps:
                    self.put(x + dx, y + dy, OUTLINE) if dy >= 0 or dx > 0 else None

    def _clump(self, x, y, L, h, k, droop=False, n=None):
        """Tall grass: a clump of blades from (x, y) up; each blade a dark lower half and a
        lit upper half, each at least 2 px (never a lone pixel); the left blades lighter;
        `droop` adds blades hanging forward over a lip."""
        g = grass_ramp(L)
        n = n or 4 + int(noise2(k, 3, self.seed + 851) * 4)
        for b in range(n):
            bx = x + b - n // 2
            bh = max(2, h - abs(b - n // 2) - int(noise2(k, b, self.seed + 852) * 2))
            lean = (-1 if b < n // 2 else 1) if bh >= 5 and noise2(k, b, self.seed + 853) > 0.5 else 0
            lo = bh // 2 if bh >= 4 else 0
            tip = lerp(g[4], '#F4F2C4', 0.15) if b < n // 2 else g[3] if b == n // 2 else lerp(g[3], g[2], 0.5)
            for t in range(bh):
                xx = bx + (lean if t >= bh - 2 else 0)
                yy = y - 1 - t
                c = lerp(g[1], g[2], 0.25) if t < lo else tip
                if 0 <= xx < self.W and 0 <= yy < self.H:
                    self.put(xx, yy, c)
        if droop:
            for b in range(0, n, 2):
                bx = x + b - n // 2
                for t in range(2 + int(noise2(k, b, self.seed + 854) * 2)):
                    if 0 <= bx < self.W and 0 <= y + t < self.H:
                        self.put(bx, y + t, g[2] if t < 2 else g[1])


# ---- the toolkit's own lint ---------------------------------------------------------------

def check(t: Terrace, stands: dict | None = None, start: str | None = None) -> list:
    """verticality.md's tier checks on a built terrace: tier-step (walkable neighbours on
    different tiers only through stair or ramp cells), stair-width (open width at least 34),
    face-height (at least 24, or 12 to 16 for a low step), rim-on-grid (straight rim rows and
    side columns on the 8 px grid), stair-ends (both landings open), and, given stands,
    that every stand is reachable from `start` (a name, or names: the stream splits the test zone)."""
    out = []
    rows, cols = len(t.walk), len(t.walk[0])
    for r in range(rows):
        for c in range(cols):
            if t.walk[r][c] == '#' or not t.tiers[r][c].isdigit():
                continue
            for (dr, dc) in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < rows and cc < cols and t.walk[rr][cc] != '#' and t.tiers[rr][cc].isdigit() \
                        and t.tiers[rr][cc] != t.tiers[r][c]:
                    out.append(f'tier-step: cells ({c},{r}) and ({cc},{rr}) change tier with no stair')
    for st in t.stairs:
        if st.w < 34:
            out.append(f'stair-width: the stair at x {st.x} is {st.w} px open (< 34)')
    for (x0, x1, y, h, top, m) in t.faces:
        if x1 - x0 >= 16 and h % 4 == 0 and not any(h == a + b for a in (0,) + HEIGHTS for b in HEIGHTS):
            out.append(f'face-height: the face at ({x0}..{x1}, {y}) is {h} px')
        if x1 - x0 >= 24 and y % GRID:
            out.append(f'rim-on-grid: the rim at ({x0}..{x1}) runs on row {y}')
    kind = t.kind
    sides = {}
    for y in range(t.height):     # side columns: the rim line beside a strip's straight run
        for x in range(1, t.width - 1):
            if kind[y, x] != STRIP_K:
                continue
            if kind[y, x - 1] == TOP and t.level[y, x - 1] > t.level[y, x] and kind[y, x + 1] == STRIP_K:
                sides.setdefault(x, []).append(y)          # faces east: the line is at x
            elif kind[y, x + 1] == TOP and t.level[y, x + 1] > t.level[y, x] and kind[y, x - 1] == STRIP_K:
                sides.setdefault(x + 1, []).append(y)      # faces west: the line is at x + 1
    for x, ys in sides.items():
        if len(ys) >= 24 and x % GRID:
            out.append(f'rim-on-grid: a side runs on column {x} ({len(ys)} px)')
    for ln in t.links:
        for end in ('top', 'bottom'):
            x, y = ln[end]
            if not (0 <= y < t.height and 0 <= x < t.width) or t.walk[y // CELL][x // CELL] == '#':
                out.append(f'stair-ends: the {ln["kind"]} {end} at {ln[end]} is blocked')
    if stands:
        starts = [start] if isinstance(start, str) else list(start or [next(iter(stands))])
        seen = set()
        for k in starts:
            seen |= reach(t.walk, stands[k])
        lost = [k for k, (x, y) in stands.items() if (y // CELL, x // CELL) not in seen]
        if lost:
            out.append(f'reach: not reachable on foot: {lost}')
    return out


def tier_at(t: Terrace, x: int, y: int) -> str:
    """The tier map at a zone px: a digit, 'f' (face) or 's' (stair or ramp)."""
    return t.tiers[y // CELL][x // CELL]


def one_tier(t: Terrace, x0: int, y0: int, x1: int, y1: int):
    """The tier a prop's foot box stands on, or None if it straddles tiers, faces or stairs
    (verticality 4a `one-tier`; soft-grid research 6.5 `prop-footprint`)."""
    seen = {t.tiers[r][c] for r in range(y0 // CELL, (y1 - 1) // CELL + 1)
            for c in range(x0 // CELL, (x1 - 1) // CELL + 1)}
    return next(iter(seen)) if len(seen) == 1 and next(iter(seen)).isdigit() else None


def reach(walk, start):
    s = (start[1] // CELL, start[0] // CELL)
    seen, q = {s}, deque([s])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (r + dr, c + dc)
            if 0 <= n[0] < len(walk) and 0 <= n[1] < len(walk[0]) and n not in seen and walk[n[0]][n[1]] != '#':
                seen.add(n)
                q.append(n)
    return seen


def rle(rows) -> list:
    """Run-length encode cell rows as zone-maps.ts does ('12.3#')."""
    out = []
    for row in rows:
        s, i = '', 0
        while i < len(row):
            j = i
            while j < len(row) and row[j] == row[i]:
                j += 1
            s += f'{j - i}{row[i]}'
            i = j
        out.append(s)
    return out


# ---- the test sheet -----------------------------------------------------------------------

TEST_MAP = """
; the terrace test zone: 40 x 72 cells of 8 px (from_ascii). A free-standing earth tier
; with four outer corners and a timber stair (A); an L in stone with a stone stair (B); a
; middle tier (C) with a second tier on it (D) and a ramp, a notch, a timber stair and a
; stream falling down its face into a pool; low samples: timber, concrete, sandstone.
0000000000000000000001111111111111111100
0000000000000000000001111111111111111100
0011111111111111100001111111111111111100
0011111111111111100001111111111111111100
0011111111111111100001111111111111111100
0011111111111111100001111111111111111100
0011111111111111100001111111111111111100
0011111111111111100000000000011111111100
0011111111111111100000000000011111111100
0011111111111111100000000000011111111100
0011111111111111100000000000011111111100
0000000SSSSSS000000000000000011111111100
0000000SSSSSS000000000000000011111111100
0000000SSSSSS000000000000000011111111100
0000000SSSSSS00000000000000000ZZZZZZ0000
000000000000000000000000000000ZZZZZZ0000
000000000000000000000000000000ZZZZZZ0000
000000000000000000000000000000ZZZZZZ0000
0000000000000000000000000000000000000000
0000000000000000000000000000000000000000
0000000000000000000000000000000000000000
0000000000000000000000000000000000000000
222222222222222222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
22222222RRRRRR2222221111111111~~~1111000
11111111RRRRRR1111111111111111~~~1111000
11111111RRRRRR1111111111111111~~~1111000
11111111RRRRRR1111111111111111~~~1111000
11111111RRRRRR1111111111111111~~~1111000
111111111111111111111111111111~~~1111000
111111111111111111111111111111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
111111111111111111110000001111~~~1111000
00000000000SSSSSS00000000000000000000000
00000000000SSSSSS00000000000000000000000
00000000000SSSSSS00000000000000000000000
00000000000SSSSSS00000000000000000000000
00000000000000000000000000000~~~~~000000
00000000000000000000000000000~~~~~000000
00000000000000000000000000000~~~~~000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000111111110000000000~~~0000000
001111111100111111110000000000~~~0000000
001111111100111111110011111100~~~0000000
001111111100111111110011111100~~~0000000
001111111100111111110011111100~~~0000000
001111111100111111110011111100~~~0000000
001111111100000000000011111100~~~0000000
000000000000000000000011111100~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
000000000000000000000000000000~~~0000000
"""
TEST_MATERIALS = "\n".join(['.....................sssssssssssssssss..'] * 17 + ['.' * 40] * 38 + [
    '............cccccccc....................',
    '..tttttttt..cccccccc....................',
    '..tttttttt..cccccccc..aaaaaa............',
    '..tttttttt..cccccccc..aaaaaa............',
    '..tttttttt..cccccccc..aaaaaa............',
    '..tttttttt..cccccccc..aaaaaa............',
    '..tttttttt............aaaaaa............',
    '......................aaaaaa............'])


def test_zone():
    """The test zone (TEST_MAP), every case the side-face rules name (verticality 4f, Check)."""
    return from_ascii(TEST_MAP, TEST_MATERIALS, {'t': 16, 'c': FACE_CITY})


def _sprite_img(sp, size=32):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    for (x, y), c in sp.c.items():
        im.putpixel((x, y), hex_rgba(c))
    return im


def _resident(root, name):
    p = os.path.join(root, 'assets', 'residents', f'{name}-0.png')
    im = Image.open(p).convert('RGBA')
    return im.resize((im.width // 4, im.height // 4), Image.NEAREST)


def sheet(out: str):
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
    spec = test_zone()
    cv = Canvas(320, 576)
    t = build(cv, spec['tiers'], edges=spec['edges'], stairs=spec['stairs'], ramps=spec['ramps'],
              water=spec['water'], seed=3)
    base = cv.img.copy()
    import pets
    sp, _h, _e = pets.mossling(2, 'open')
    pet = _sprite_img(sp)
    actors = [  # (image, foot x, foot y): residents (A = 25) and the companion beside the cases
        (pet, 80, 88), (_resident(root, 'hiker'), 112, 156), (_resident(root, 'forager'), 270, 196),
        (_resident(root, 'naturalist'), 40, 232), (pet, 196, 342), (_resident(root, 'gardener'), 300, 412),
        (_resident(root, 'stroller'), 60, 466), (pet, 150, 560), (_resident(root, 'botanist'), 180, 300),
    ]
    img = base.copy()
    for (im, fx, fy) in sorted(actors, key=lambda a: a[2]):
        x, y = fx - im.width // 2, fy - im.height
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
        for xx in range(x + 4, x + im.width - 2):
            for yy in (fy - 1, fy, fy + 1):
                if 0 <= xx < img.width and 0 <= yy < img.height:
                    sh.putpixel((xx, yy), (16, 20, 30, 90))
        img.alpha_composite(sh)
        img.alpha_composite(im, (x, y))
    stem = out[:-4] if out.endswith('.png') else out
    img.save(stem + '.png')
    base.save(stem + '-ground.png')                       # the ground alone: what the bar judges
    big = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    big.save(stem + '-3x.png')
    night = img.copy()
    night.alpha_composite(Image.new('RGBA', img.size, (22, 28, 66, int(0.42 * 255))))
    night.resize((img.width * 3, img.height * 3), Image.NEAREST).save(stem + '-night-3x.png')
    walk = img.copy()
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    lp = lay.load()
    tints = {'0': (40, 200, 90, 60), '1': (40, 160, 230, 70), '2': (180, 90, 230, 80)}
    for r, row in enumerate(t.walk):
        for c, ch in enumerate(row):
            tr = t.tiers[r][c]
            col = (220, 40, 40, 110) if ch == '#' else (250, 210, 40, 150) if tr == 's' else tints.get(tr, (255, 255, 255, 60))
            for dy in range(CELL):
                for dx in range(CELL):
                    lp[c * CELL + dx, r * CELL + dy] = (0, 0, 0, 70) if dx == CELL - 1 or dy == CELL - 1 else col
    walk.alpha_composite(lay)
    walk.resize((img.width * 2, img.height * 2), Image.NEAREST).save(stem + '-walk-2x.png')
    # the falls move: water_flow's frames for this ground
    import water_flow
    fl = water_flow.sheet(base, t.water, set())
    if fl:
        fl[0].save(stem + '-flow.png')
    return t


def _stands():
    return {'corridor': (308, 300), 'A top': (80, 60), 'A stair foot': (80, 140), 'B top': (264, 40),
            'B stair foot': (264, 164), 'C west': (40, 340), 'notch floor': (184, 344), 'D top': (60, 200),
            'ramp foot': (88, 284), 'C stair foot': (120, 412), 'south west': (60, 572)}


# where each kind of surface sits on the test sheet (zone px), for the detail bar
BAR_WINDOWS = {   # name: (kind, box), each box 2 px more than whole 16 px patches (resampling rounds down)
    'face': ('face', (16, 366, 82, 400)),            # C's south face, earth, lip to foot
    'rim': ('rim', (16, 350, 82, 384)),              # C's lip, the top behind it, the face under it
    'side': ('side', (118, 24, 152, 90)),            # A's east band, its shadow and the ground beside
    'corner': ('corner', (112, 80, 146, 130)),       # A's south-east corner, top to foot
    'stair': ('stair', (56, 80, 106, 130)),          # A's timber stair and its landings
    'foot': ('foot', (16, 390, 82, 424)),            # C's foot and the ground below
    'ground': ('ground', (176, 416, 242, 450)),      # open ground on the lower tier
    'ground, upper tier': ('ground', (16, 180, 82, 214)),
    'water': ('water', (226, 398, 276, 448)),        # the pool under the fall and the stream leaving it
    'notch': ('corner', (152, 288, 218, 354)),
    'stone face': ('face', (176, 54, 226, 88)),
    'stone band (east)': ('side', (286, 20, 320, 104)),
    'stone stair': ('stair', (240, 104, 290, 154)),
    'ramp': ('ground', (64, 186, 114, 236)),         # a dirt path: judged as ground
    'timber step': ('face', (16, 478, 82, 512)),
    'concrete face': ('face', (96, 478, 146, 528)),
    'sandstone face': ('face', (176, 494, 226, 528)),
}


def bar_report(img: Image.Image) -> bool:
    """The test sheet against the Eastward detail bar (detail_bar.py), kind by kind."""
    import detail_bar
    ok_all = True
    for name, (kind, box) in BAR_WINDOWS.items():
        ok, _ours, lines = detail_bar.check_image(img, box, kind)
        ok_all &= ok
        print(f'{name:18s} ' + '; '.join(lines) + ('' if ok else '  <- below the bar'))
    print('detail bar:', 'PASS' if ok_all else 'FAIL')
    return ok_all


def main(argv):
    if '--sheet' in argv:
        i = argv.index('--sheet')
        out = argv[i + 1] if i + 1 < len(argv) else 'terrace-sheet.png'
        t = sheet(out)
        probs = check(t, _stands(), ('corridor', 'south west'))
        print('\n'.join(probs) if probs else 'terrace: clean')
        if '--bar' in argv:
            stem = out[:-4] if out.endswith('.png') else out
            bar_report(Image.open(stem + '-ground.png'))
        return 0
    if '--check' in argv:
        spec = test_zone()
        a = build(Canvas(320, 576), seed=3, **spec)
        b = build(Canvas(320, 576), seed=3, **spec)
        probs = check(a, _stands(), ('corridor', 'south west'))
        if a.walk != b.walk or a.tiers != b.tiers:
            probs.append('determinism: two builds differ')
        print('\n'.join(probs) if probs else 'terrace: clean')
        return 1 if probs else 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

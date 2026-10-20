"""The world canvas, step 1: the build (docs/vision/region-canvas.md).

Matt, 20 Oct: the zones give way to one world canvas (about 10:50, world plan v2,
decision 2; at 11:45, one canvas for the whole continent). The continent is authored
in **chunks** (a region, a route, the land between), each a rectangle of the world with
a world origin, a bounding box and a blend margin it may paint into its neighbours. The
build composites every chunk on a plane onto shared 256 x 256 **world tiles** and
exports, per tile, the ground picture, its moving water, its walk, terrain, tiers,
stands and props. Areas (the names, the map, saves and the ways) are a separate small
table. The station, the moon and the inside of the hut are planes of their own.

Step 1 changes nothing in the game. zones.py still draws the zones and writes
assets/zones/** and lib/zone-*.ts, which the game reads. At the end of its run it hands
its built zones to build_all() here, which assembles each region's chunk from them (the
adapter, from_zones), checks the compatibility cut back into zones (cut_zone) and writes
the new outputs alongside:

  assets/world/<plane>/t_<col>_<row>.png   a tile's ground, at TILE_SCALE
  assets/world/shared/s_<hash>.png         a ground two or more tiles share (deduplicated)
  assets/world/shared/u_<rrggbbaa>.png     a tile of one colour (sea, deep forest)
  assets/world/<plane>/f_<col>_<row>.png   a tile's moving water (water_flow.py), 1x, frames stacked
  lib/world-canvas.ts                      typed data: chunks, areas, per-tile walk/terrain/tiers/stands/props
  lib/world-canvas-assets.ts               the pictures, imported one by one (they bundle on native)

A lane that draws a chunk whole registers a painter (see `painter`). finish() derives
what the adapter copies from the zones: the walk grid, the terrain and the moving water.
The build caches per chunk (CACHE, git-ignored): a chunk whose content is unchanged keeps
its tiles' pictures, and a painter with declared sources is not even re-run, so a lane's
change re-encodes only the tiles its chunks touch. The check is lib/world-canvas.test.ts.
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import re
import shutil
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import water_flow  # noqa: E402
import worlds  # noqa: E402

GRID = 8          # chunks, origins, margins and areas sit on the 8 px soft grid
CELL = 4          # walk cells, as the zones have them
TILE = 256        # world tiles, in art px (64 x 64 walk cells)
TCELLS = TILE // CELL
# The pictures' scale. The plan (world-plan.md, decision 8): 1x with nearest-neighbour
# scaling once that is shown crisp on iOS, Android and the web; 2x until then. The web is
# crisp at 1x (data-pixel sets image-rendering: pixelated); React Native's Image has no
# nearest-neighbour filter on iOS or Android, so 2x stays the default until step 2 tests it.
TILE_SCALE = int(os.environ.get('WORLD_TILE_SCALE', '2'))
EMPTY_TERRAIN = '-'  # a terrain cell no chunk covers
CACHE = os.environ.get('WORLD_CACHE') or os.path.join(worlds.ROOT, '.cache', 'world-canvas')
OUT = os.path.join(worlds.ROOT, 'assets', 'world')

# Where each of today's regions lies as a chunk: its plane and the world pixel of its
# box's top-left. PLACEHOLDERS until world plan v4 lays out the continent: the regions
# stand in a row on it, a tile apart, the valley at the world's origin (so the valley's
# world px are today's region px). Moving a chunk changes only its origin here; the build
# renames its tiles and every coordinate in lib/world-canvas.ts moves with it.
PLACES = {
    'valley': ('continent', (0, 0)),
    'steam': ('continent', (1280, 0)),
    'west': ('continent', (1792, 0)),
    'isles': ('continent', (3328, 0)),
    'neon': ('continent', (4352, 0)),
    'space': ('orbit', (0, 0)),
    'moon': ('moon', (0, 0)),
    'home': ('hut', (0, 0)),
}


def _sha(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, (bytes, bytearray, memoryview)) else repr(p).encode())
    return h.hexdigest()


CODE = _sha(open(__file__, 'rb').read(), open(water_flow.__file__, 'rb').read())


class Chunk:
    """A piece of the world drawn whole, in its own pixels: (0, 0) is its box's top-left.

    ground   PIL RGBA image of the box plus `margin` on every side; the box is at
             (margin, margin) in it (see `at`). Inside the box the chunk's ground is the
             world's; in the margin it is blended over its neighbours' (alpha over), so
             two chunks meet in a drawn transition, not a cut. Walks and terrain come from
             the box only.
    objects  [(id, sprite key, x, y)], the sprite's top-left in box px (as zones.build)
    stands   {name: (x, y)}
    blocked  set of box px a walk may not enter (water, cliffs, walls drawn in the ground)
    water    set of box px that are water, when declared (else read by colour)
    tiers    walk rows of digits, the terrace each cell stands on (verticality.md), or None
    decks    [{'rect', 'height', 'connectors'}] and deck_walk rows (two-level-walk.md)
    areas    [{'id', 'kind', 'rect': (x, y, w, h)}, optionally 'cells': rows of '.'/'#']
    walk, terrain, flow: filled by finish() for a painted chunk, copied by the adapter
    """

    def __init__(self, id: str, w: int, h: int, kind: str = 'region', plane: str | None = None,
                 origin: tuple | None = None, margin: int = 0):
        for v, what in ((w, 'width'), (h, 'height'), (margin, 'margin')):
            assert v % GRID == 0, f'{id}: its {what} sits on the {GRID} px grid ({v})'
        self.id, self.kind, self.w, self.h, self.margin = id, kind, w, h, margin
        if plane is None or origin is None:
            plane, origin = PLACES[id]
        self.plane, self.origin = plane, tuple(origin)
        assert self.origin[0] % GRID == 0 and self.origin[1] % GRID == 0, f'{id}: origin off the grid'
        self.ground = Image.new('RGBA', (w + 2 * margin, h + 2 * margin), (0, 0, 0, 0))
        self.objects: list = []
        self.stands: dict = {}
        self.blocked: set = set()
        self.water: set | None = None
        self.tiers: list[str] | None = None
        self.decks: list = []
        self.deck_walk: list[str] | None = None
        self.deck_art: Image.Image | None = None      # box-sized, the decks drawn (decks.py)
        self.deck_shadow: Image.Image | None = None
        self.areas: list = []
        self.walk: list[str] | None = None
        self.terrain: list[str] | None = None
        self.flow: np.ndarray | None = None           # (FRAMES, h, w, 4) uint8 over the box
        self.flow_given = False
        self.seams: list = []                         # [(col, row, 'open'|'shut')] in box cells
        self.joined_walk: list[str] | None = None     # adapter: the zones' grids joined

    def at(self, x: int, y: int) -> tuple:
        """Where box pixel (x, y) is in `ground`."""
        return x + self.margin, y + self.margin

    def core(self) -> Image.Image:
        m = self.margin
        return self.ground if not m else self.ground.crop((m, m, m + self.w, m + self.h))

    @property
    def cols(self):
        return self.w // CELL

    @property
    def rows(self):
        return self.h // CELL

    def extent(self):
        """World px the chunk paints: its box plus its margin."""
        x, y = self.origin
        return x - self.margin, y - self.margin, x + self.w + self.margin, y + self.h + self.margin

    def tiles(self):
        x0, y0, x1, y1 = self.extent()
        return [(c, r) for r in range(y0 // TILE, -(-y1 // TILE)) for c in range(x0 // TILE, -(-x1 // TILE))]

    def digest(self) -> str:
        """Everything about the chunk that shows in a tile's pictures."""
        parts = [self.plane, self.origin, self.w, self.h, self.margin, np.asarray(self.ground).tobytes()]
        if self.flow is not None:
            parts.append(self.flow.tobytes())
        for img in (self.deck_art, self.deck_shadow):
            if img is not None:
                parts.append(np.asarray(img).tobytes())
        return _sha(*parts)


RegionCanvas = Chunk  # (the name step 1 first used)

PAINTERS: dict = {}


def painter(id: str, sources: tuple = ()):
    """Register a function that paints a chunk whole (a lane's generator):

        @world_canvas.painter('steam', sources=('scripts/art/cogsworth.py',))
        def cogsworth() -> world_canvas.Chunk:
            ch = world_canvas.Chunk('steam', 704, 960, margin=32)
            ...draw ch.ground (box pixel (x, y) is ch.at(x, y)); list ch.objects / stands /
            blocked / areas...
            return ch

    build_all() then uses it in place of the zones. With `sources` (repo-relative files
    its drawing depends on) the finished chunk is cached, and the painter is not re-run
    until one of them (or this build) changes. Until step 2 the game still reads zones, so
    a painted region also writes its zones from cut_zone() (as the isles already cut theirs)."""
    def wrap(fn):
        PAINTERS[id] = (fn, tuple(sources))
        return fn
    return wrap


# --- deriving a chunk's walk, terrain and moving water (a painted chunk) ----------------

def derive_walk(ch: Chunk, sprite_map: dict) -> list[str]:
    """The walk grid from the chunk alone, by the rules zones.build applies to a zone: a
    prop's foot band blocks (gateways excepted), drawn obstacles block, the cell beside lava
    is kept back from on each side, and ground the box does not cover blocks. Over the whole
    box, so nothing is cut at a seam."""
    import zones
    import world_lint
    cells = set()
    for (_id, key, x, y) in ch.objects:
        if key in zones.OVERHEAD:
            continue
        sp = sprite_map[key]
        if key in zones.FEET:  # a wide prop on a few feet (zones.FEET): only its footings block
            for (fx0, fx1, depth) in zones.FEET[key]:
                for yy in range(y + sp.h - depth, y + sp.h):
                    for xx in range(x + fx0, x + fx1):
                        cells.add((xx // CELL, yy // CELL))
            continue
        foot = 20 if sp.w > 60 else 10 if key in ('tree', 'tree_small', 'tree_autumn', 'pine') else 6
        gap = zones.OPENINGS.get(key)
        for yy in range(y + sp.h - foot, y + sp.h):
            for xx in range(x + 3, x + sp.w - 3):
                if gap and x + gap[0] <= xx < x + gap[1]:
                    continue
                cells.add((xx // CELL, yy // CELL))
    ground = {(x // CELL, y // CELL) for (x, y) in ch.blocked}
    core = ch.core()
    px = core.load()
    hot = {(c, r) for (c, r) in ground
           if 0 <= c < ch.cols and 0 <= r < ch.rows and world_lint._lava(*px[c * CELL + 2, r * CELL + 2][:3])}
    ground |= {(c + d, r) for (c, r) in hot for d in (-1, 1) if 0 <= c + d < ch.cols}
    cells |= ground
    bare = np.asarray(core)[..., 3].reshape(ch.rows, CELL, ch.cols, CELL).max(axis=(1, 3)) == 0
    return [''.join('#' if (c, r) in cells or bare[r, c] else '.' for c in range(ch.cols)) for r in range(ch.rows)]


def derive_terrain(ch: Chunk) -> list[str]:
    import world_lint
    core = ch.core()
    rows = world_lint.classify(core, ch.blocked, ch.water, cols=ch.cols, rows=ch.rows)
    a = np.asarray(core)[..., 3].reshape(ch.rows, CELL, ch.cols, CELL).max(axis=(1, 3))
    return [''.join(c_ if a[r, c] else EMPTY_TERRAIN for c, c_ in enumerate(row)) for r, row in enumerate(rows)]


def derive_flow(ch: Chunk, terrain: list[str]):
    """The moving water over the whole box (water_flow.sheet, as zones.build does for a
    zone), as full-size frames, or None."""
    import world_lint
    core = ch.core()
    px = core.load()
    wet, hot = set(), set()
    for r, row in enumerate(terrain):
        for c, k in enumerate(row):
            if k not in '~!':
                continue
            for y in range(r * CELL - 1, r * CELL + CELL + 1):
                for x in range(c * CELL - 1, c * CELL + CELL + 1):
                    if not (0 <= x < ch.w and 0 <= y < ch.h):
                        continue
                    if ch.water is not None:
                        if k == '~' and (x, y) in ch.water:
                            wet.add((x, y))
                        continue
                    p = px[x, y][:3]
                    if k == '~' and world_lint._bluish(*p):
                        wet.add((x, y))
                    elif k == '!' and world_lint._lava(*p):
                        hot.add((x, y))
    sheet = water_flow.sheet(core, wet, hot)
    return None if not sheet else unstack(*sheet, ch.w, ch.h)


def unstack(img: Image.Image, rect, w: int, h: int) -> np.ndarray:
    """A water_flow sheet (frames stacked in a box) as full-size frames."""
    x0, y0, bw, bh = rect
    a = np.asarray(img.convert('RGBA'))
    out = np.zeros((water_flow.FRAMES, h, w, 4), dtype=np.uint8)
    for f in range(water_flow.FRAMES):
        out[f, y0:y0 + bh, x0:x0 + bw] = a[f * bh:(f + 1) * bh]
    return out


def area_has(a: dict, x: int, y: int) -> bool:
    ax, ay, aw, ah = a['rect']
    if not (ax <= x < ax + aw and ay <= y < ay + ah):
        return False
    cells = a.get('cells')
    return cells is None or cells[(y - ay) // CELL][(x - ax) // CELL] == '.'


def finish(ch: Chunk, sprite_map: dict):
    """Fill in what a painter leaves to the build, and check the chunk."""
    ch._sized_objects = [(i, k, x, y, sprite_map[k].w, sprite_map[k].h) for (i, k, x, y) in ch.objects]
    if ch.walk is None:
        ch.walk = derive_walk(ch, sprite_map)
    if ch.terrain is None:
        ch.terrain = derive_terrain(ch)
    if ch.flow is None and not ch.flow_given:
        ch.flow = derive_flow(ch, ch.terrain)
    for name, rows in (('walk', ch.walk), ('terrain', ch.terrain), ('tiers', ch.tiers), ('deck walk', ch.deck_walk)):
        if rows is not None:
            assert len(rows) == ch.rows and all(len(r) == ch.cols for r in rows), f'{ch.id}: {name} is not {ch.cols} x {ch.rows}'
    if ch.tiers is not None:
        assert all(set(r) <= set('0123456789') for r in ch.tiers), f'{ch.id}: tiers are digits'
    assert ch.areas, f'{ch.id}: a chunk names its areas'
    for a in ch.areas:
        x, y, w, h = a['rect']
        assert x % GRID == 0 and y % GRID == 0 and w % GRID == 0 and h % GRID == 0, f'{ch.id}/{a["id"]}: off the grid'
        assert 0 <= x and 0 <= y and x + w <= ch.w and y + h <= ch.h, f'{ch.id}/{a["id"]}: outside the box'
    loose = [(c, r) for r, row in enumerate(ch.walk) for c, k in enumerate(row)
             if k == '.' and not any(area_has(a, c * CELL, r * CELL) for a in ch.areas)]
    assert not loose, f'{ch.id}: {len(loose)} walkable cells in no area (first {loose[:3]})'
    for s, (x, y) in ch.stands.items():
        assert 0 <= x < ch.w and 0 <= y < ch.h, f'{ch.id}: stand {s} outside the box'
    return ch


# --- the adapter: today's zones placed at their offsets --------------------------------

def _garden_walk() -> list[str]:
    """The garden's walk as lib/region-walk.ts lays it into the valley today: its own grid
    (garden.py, lib/garden-map.ts) with the gate and the ridge trail open and its west and
    east edges closed two cells deep outside their ports."""
    import frames
    import zones
    src = open(os.path.join(worlds.ROOT, 'lib', 'garden-map.ts')).read()
    block = src.split('export const gardenWalk', 1)[1].split('];', 1)[0]
    rows = re.findall(r"[\"']([.#]+)[\"']", block)
    fence = int(re.search(r'fenceY:\s*(\d+)', src).group(1))
    gh = int(re.search(r'export const GARDEN = \{[^}]*height:\s*(\d+)', src).group(1))
    ports = frames.export()
    west, east = ports['woodland|garden']['span'], ports['garden|riverside']['span']
    openings = ((144, 176, fence - 20, gh), (198, 214, 0, 48))
    cols = zones.W // CELL
    out = []
    for r, row in enumerate(rows):
        line = ''
        for c, k in enumerate(row[:cols]):
            x, y = c * CELL + CELL // 2, r * CELL + CELL // 2
            if any(x0 <= x < x1 and y0 <= y < y1 for (x0, x1, y0, y1) in openings):
                line += '.'
            elif c < 2 and not (west and west[0] <= y < west[1]):
                line += '#'
            elif c >= cols - 2 and not (east and east[0] <= y < east[1]):
                line += '#'
            else:
                line += k
        out.append(line)
    return out


def from_zones(region: str, built: dict) -> Chunk:
    """A region's chunk assembled from today's zones: each zone's ground, props, stands,
    blocked ground, walk, terrain, decks and moving water placed at its offset. The garden
    (the valley's 0, 0) brings its ground and walk; its props stay the garden's own."""
    import world_lint
    import zones
    W, H = zones.W, zones.H
    zs = zones.LAYOUT[region]
    min_c = min(c for c, _r in zs.values())
    min_r = min(r for _c, r in zs.values())
    cols = max(c for c, _r in zs.values()) - min_c + 1
    rows = max(r for _c, r in zs.values()) - min_r + 1
    ch = Chunk(region, cols * W, rows * H)
    walk = [['#'] * ch.cols for _ in range(ch.rows)]
    terrain = [[EMPTY_TERRAIN] * ch.cols for _ in range(ch.rows)]
    deck_rows = [['#'] * ch.cols for _ in range(ch.rows)]
    flow = None
    for z, (col, row) in zs.items():
        ox, oy = (col - min_c) * W, (row - min_r) * H
        oc, orow = ox // CELL, oy // CELL
        if z == 'garden':
            g = Image.open(os.path.join(worlds.ROOT, 'assets', 'garden', 'ground.png')).convert('RGBA')
            ch.ground.paste(g.resize((W, H), Image.NEAREST), (ox, oy))
            zwalk, zterrain = _garden_walk(), world_lint.garden_zone()['terrain']
            ch.areas.append({'id': z, 'kind': 'garden', 'rect': (ox, oy, W, H)})
        else:
            b = built[z]
            assert b['ground_img'].size == (W, H), f'{z}: ground is not {W} x {H}'
            ch.ground.paste(b['ground_img'], (ox, oy))
            ch.objects += [(f'{z}:{i}', k, x + ox, y + oy) for (i, k, x, y) in b['objects']]
            ch.stands.update({f'{z}:{s}': (x + ox, y + oy) for s, (x, y) in b['stands'].items()})
            ch.blocked |= {(x + ox, y + oy) for (x, y) in b['blocked']}
            if b.get('water'):
                ch.water = (ch.water or set()) | {(x + ox, y + oy) for (x, y) in b['water']}
            zwalk, zterrain = b['walk'], b['terrain']
            ch.areas.append({'id': z, 'kind': 'zone', 'rect': (ox, oy, W, H)})
            if b.get('deck'):
                d = b['deck']
                for r, line in enumerate(d['walk']):
                    for c, k in enumerate(line):
                        if k == '.':
                            deck_rows[orow + r][oc + c] = '.'
                ch.decks.append({'rect': (ox, oy, W, H), 'height': d['height'], 'connectors': [
                    {'kind': c['kind'], 'bottom': (c['bottom'][0] + ox, c['bottom'][1] + oy),
                     'top': (c['top'][0] + ox, c['top'][1] + oy)} for c in d['connectors']]})
                for attr, name in (('deck_art', 'deck.png'), ('deck_shadow', 'deck-shadow.png')):
                    if getattr(ch, attr) is None:
                        setattr(ch, attr, Image.new('RGBA', (ch.w, ch.h), (0, 0, 0, 0)))
                    art = Image.open(os.path.join(worlds.ROOT, 'assets', 'zones', z, name)).convert('RGBA')
                    getattr(ch, attr).paste(art.resize((W, H), Image.NEAREST), (ox, oy))
            if z in zones.FLOW_RECT:
                sheet = Image.open(os.path.join(worlds.ROOT, 'assets', 'zones', z, 'flow.png'))
                frames = unstack(sheet, zones.FLOW_RECT[z], W, H)
                if flow is None:
                    flow = np.zeros((water_flow.FRAMES, ch.h, ch.w, 4), dtype=np.uint8)
                flow[:, oy:oy + H, ox:ox + W] = frames
        for r, line in enumerate(zwalk):
            walk[orow + r][oc:oc + W // CELL] = list(line[:W // CELL])
        for r, line in enumerate(zterrain):
            terrain[orow + r][oc:oc + W // CELL] = list(line[:W // CELL])
    ch.joined_walk = [''.join(r) for r in walk]
    ch.terrain = [''.join(r) for r in terrain]
    ch.flow, ch.flow_given = flow, True
    if ch.decks:
        ch.deck_walk = [''.join(r) for r in deck_rows]
    # The seams, settled: walk the whole box by the zone rules (no seams) and take that
    # wherever it differs from the zones' grids joined (share_feet closes only east and west
    # neighbours; the lava step-back is cut at a zone's edge). Each such cell is reported.
    # The garden keeps its own walk (its props are the garden's, not zone props).
    derived = derive_walk(ch, zones.sprites())
    garden = [a['rect'] for a in ch.areas if a['kind'] == 'garden']
    settled = [list(r) for r in ch.joined_walk]
    for r in range(ch.rows):
        for c in range(ch.cols):
            if derived[r][c] == settled[r][c]:
                continue
            x, y = c * CELL, r * CELL
            if any(gx <= x < gx + gw and gy <= y < gy + gh for (gx, gy, gw, gh) in garden):
                continue
            settled[r][c] = derived[r][c]
            ch.seams.append((c, r, 'open' if derived[r][c] == '.' else 'shut'))
    ch.walk = [''.join(r) for r in settled]
    return ch


def cut_zone(ch: Chunk, rect: tuple, joined: bool = False) -> dict:
    """The compatibility cut: the part of a chunk inside one of today's zones (box px
    rect), in that zone's own coordinates, as the zone outputs hold it. A painted region
    writes its zones from this until step 2 retires them. `joined` takes the zones' grids
    joined (the adapter's) rather than the settled walk."""
    x0, y0, w, h = rect
    c0, r0 = x0 // CELL, y0 // CELL
    walk = ch.joined_walk if joined and ch.joined_walk else ch.walk
    objects = []
    for (i, k, x, y, sw, sh) in ch._sized_objects:
        fx = min(max(x + sw // 2, 0), ch.w - 1)
        fy = min(max(y + sh - 2, 0), ch.h - 1)
        if x0 <= fx < x0 + w and y0 <= fy < y0 + h:
            objects.append((i.split(':', 1)[-1], k, x - x0, y - y0, sw, sh))
    return {
        'ground': ch.core().crop((x0, y0, x0 + w, y0 + h)),
        'walk': [row[c0:c0 + w // CELL] for row in walk[r0:r0 + h // CELL]],
        'terrain': [row[c0:c0 + w // CELL] for row in ch.terrain[r0:r0 + h // CELL]],
        'objects': objects,
        'stands': {s.split(':', 1)[-1]: (x - x0, y - y0) for s, (x, y) in ch.stands.items()
                   if x0 <= x < x0 + w and y0 <= y < y0 + h},
    }


def check_cut(ch: Chunk, built: dict):
    """Every zone cut back out of its region's chunk is that zone, exactly: its ground
    byte for byte, its terrain, props and stands, and its walk (the zones' grids joined;
    the settled walk differs only at the reported seam cells)."""
    import zones
    seams = {(c, r) for (c, r, _k) in ch.seams}
    for a in ch.areas:
        if a['kind'] != 'zone':
            continue
        z, b = a['id'], built[a['id']]
        cut = cut_zone(ch, a['rect'], joined=True)
        assert cut['ground'].tobytes() == b['ground_img'].tobytes(), f'{z}: the cut ground differs'
        assert cut['walk'] == b['walk'], f'{z}: the cut walk differs'
        assert cut['terrain'] == b['terrain'], f'{z}: the cut terrain differs'
        sm = zones.sprites()
        want = [(i, k, x, y, sm[k].w, sm[k].h) for (i, k, x, y) in b['objects']]
        assert sorted(cut['objects']) == sorted(want), f'{z}: the cut props differ'
        assert cut['stands'] == {s: tuple(p) for s, p in b['stands'].items()}, f'{z}: the cut stands differ'
        settled = cut_zone(ch, a['rect'])['walk']
        ax, ay = a['rect'][0] // CELL, a['rect'][1] // CELL
        for r, (s_row, j_row) in enumerate(zip(settled, b['walk'])):
            for c, (s, j) in enumerate(zip(s_row, j_row)):
                assert s == j or (ax + c, ay + r) in seams, f'{z}: settled walk differs off a seam at {c},{r}'


# --- writing the world: tiles keyed by world coordinates, cached per chunk ---------------

def _tag(n: int) -> str:
    return str(n).replace('-', 'm')


def _window(arr: np.ndarray, x0: int, y0: int, wx: int, wy: int) -> tuple:
    """The part of arr (..., h, w, 4), placed with its top-left at world (x0, y0), inside the
    tile whose top-left is world (wx, wy): (source slices, tile slices) or None."""
    h, w = arr.shape[-3], arr.shape[-2]
    sx0, sy0 = max(0, wx - x0), max(0, wy - y0)
    sx1, sy1 = min(w, wx + TILE - x0), min(h, wy + TILE - y0)
    if sx1 <= sx0 or sy1 <= sy0:
        return None
    return ((slice(sy0, sy1), slice(sx0, sx1)),
            (slice(y0 + sy0 - wy, y0 + sy1 - wy), slice(x0 + sx0 - wx, x0 + sx1 - wx)))


def _over(dst: np.ndarray, src: np.ndarray):
    """src over dst, both uint8 RGBA arrays of one shape (Porter-Duff over, rounded)."""
    sa = src[..., 3:4].astype(np.float64) / 255
    da = dst[..., 3:4].astype(np.float64) / 255
    oa = sa + da * (1 - sa)
    rgb = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-9), 0)
    out = np.concatenate([np.rint(rgb), np.rint(oa * 255)], axis=-1)
    full = src[..., 3] == 255
    out[full] = src[full]
    keep = src[..., 3] == 0
    out[keep] = dst[keep]
    dst[...] = out.astype(np.uint8)


def composite(chunks: list, c: int, r: int) -> dict:
    """World tile (c, r) of one plane: every chunk's box written first (boxes never overlap),
    then every margin blended over them in chunk order; the moving water and decks from
    the boxes."""
    wx, wy = c * TILE, r * TILE
    ground = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    flow = np.zeros((water_flow.FRAMES, TILE, TILE, 4), dtype=np.uint8)
    deck = np.zeros((2, TILE, TILE, 4), dtype=np.uint8)
    for ch in chunks:
        m = ch.margin
        g = np.asarray(ch.ground)
        core = g[m:m + ch.h, m:m + ch.w]
        win = _window(core, *ch.origin, wx, wy)
        if win:
            src, dst = win
            mask = core[src][..., 3] > 0
            ground[dst][mask] = core[src][mask]
            if ch.flow is not None:
                fsrc = ch.flow[(slice(None),) + src]
                fdst = flow[(slice(None),) + dst]
                fmask = fsrc[..., 3] > 0
                fdst[fmask] = fsrc[fmask]
            if ch.deck_art is not None:
                for k, img in enumerate((ch.deck_art, ch.deck_shadow)):
                    a = np.asarray(img)[src]
                    dmask = a[..., 3] > 0
                    deck[k][dst][dmask] = a[dmask]
    for ch in chunks:
        m = ch.margin
        if not m:
            continue
        ring = np.array(ch.ground)
        ring[m:m + ch.h, m:m + ch.w] = 0  # the box itself is already down
        win = _window(ring, ch.origin[0] - m, ch.origin[1] - m, wx, wy)
        if win:
            src, dst = win
            part = ground[dst].copy()
            _over(part, ring[src])
            ground[dst] = part
    return {'ground': ground, 'flow': flow, 'deck': deck}


def _png_bytes(arr: np.ndarray, scale: int) -> bytes:
    import io
    img = Image.fromarray(arr, 'RGBA')
    if scale != 1:
        img = img.resize((arr.shape[1] * scale, arr.shape[0] * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return buf.getvalue()


def _flow_box(flow: np.ndarray):
    moving = flow[..., 3].any(axis=0)
    if not moving.any():
        return None, None
    yy, xx = np.nonzero(moving)
    x0, x1, y0, y1 = int(xx.min()), int(xx.max()) + 1, int(yy.min()), int(yy.max()) + 1
    bh = y1 - y0
    stack = np.zeros((bh * water_flow.FRAMES, x1 - x0, 4), dtype=np.uint8)
    for f in range(water_flow.FRAMES):
        stack[f * bh:(f + 1) * bh] = flow[f, y0:y1, x0:x1]
    return stack, (x0, y0, x1 - x0, bh)


def write_world(chunks: list, out_root: str = OUT, cache_dir: str = CACHE) -> dict:
    """Composite every plane into world tiles and write their pictures. A tile whose
    contributing chunks are unchanged since the last build (the cache's manifest) is not
    composited or encoded again; its files are kept (or copied, if deduplication renamed
    them). Returns per plane {(c, r): {'art', 'fill', 'flow', 'deck'}} and the counts."""
    manifest_path = os.path.join(cache_dir, 'manifest.json')
    try:
        manifest = json.load(open(manifest_path))
    except (OSError, ValueError):
        manifest = {}
    old = manifest.get('tiles', {}) if manifest.get('code') == CODE and manifest.get('scale') == TILE_SCALE else {}
    digests = {ch.id: ch.digest() for ch in chunks}
    planes: dict = {}
    for ch in chunks:
        planes.setdefault(ch.plane, []).append(ch)
    records, pixels = {}, {}
    written = reused = 0
    for plane, chs in planes.items():
        keys = sorted({t for ch in chs for t in ch.tiles()}, key=lambda t: (t[1], t[0]))
        for (c, r) in keys:
            near = [ch for ch in chs if (c, r) in ch.tiles()]
            key = _sha(CODE, TILE_SCALE, [(ch.id, digests[ch.id]) for ch in near])
            tid = f'{plane}:{c},{r}'
            prev = old.get(tid)
            if prev and prev['key'] == key and all(
                    os.path.exists(os.path.join(out_root, f)) and _sha(open(os.path.join(out_root, f), 'rb').read()) == h
                    for f, h in prev['files'].items()):
                records[tid] = dict(prev)
                reused += 1
                continue
            t = composite(near, c, r)
            g = t['ground']
            rec = {'key': key, 'plane': plane, 'c': c, 'r': r, 'files': {}}
            if not g[..., 3].any():
                rec['empty'] = True
                records[tid] = rec
                continue
            first = g[0, 0]
            rec['fill'] = ('#%02X%02X%02X%02X' % tuple(int(v) for v in first)) if (g == first).all() and first[3] == 255 else None
            rec['hash'] = _sha(g.tobytes())[:16]
            stack, box = _flow_box(t['flow'])
            rec['flow'] = list(box) if box else None
            rec['deck'] = bool(t['deck'][..., 3].any())
            pixels[tid] = (t, stack)
            records[tid] = rec
            written += 1
    # name each ground picture: a colour, a shared ground, or the tile's own
    count: dict = {}
    for rec in records.values():
        if not rec.get('empty'):
            count[rec['hash']] = count.get(rec['hash'], 0) + 1
    for tid, rec in records.items():
        if rec.get('empty'):
            continue
        name = f'{_tag(rec["c"])}_{_tag(rec["r"])}'
        if rec['fill']:
            rec['art'] = f'shared/u_{rec["fill"][1:].lower()}'
        elif count[rec['hash']] > 1:
            rec['art'] = f'shared/s_{rec["hash"][:12]}'
        else:
            rec['art'] = f'{rec["plane"]}/t_{name}'
        want = {f'{rec["art"]}.png': 'ground'}
        if rec['flow']:
            want[f'{rec["plane"]}/f_{name}.png'] = 'flow'
        if rec['deck']:
            want[f'{rec["plane"]}/d_{name}.png'] = 'deck'
            want[f'{rec["plane"]}/s_{name}.png'] = 'shadow'
        files, roles = {}, {}
        for f, what in want.items():
            path = os.path.join(out_root, f)
            if tid in pixels:
                t, stack = pixels[tid]
                data = {'ground': lambda: _png_bytes(t['ground'], TILE_SCALE),
                        'flow': lambda: _png_bytes(stack, 1),
                        'deck': lambda: _png_bytes(t['deck'][0], TILE_SCALE),
                        'shadow': lambda: _png_bytes(t['deck'][1], TILE_SCALE)}[what]()
            else:  # kept: the same picture, under a new name if deduplication renamed it
                data = open(os.path.join(out_root, rec['roles'][what]), 'rb').read()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not (os.path.exists(path) and open(path, 'rb').read() == data):
                with open(path, 'wb') as fh:
                    fh.write(data)
            files[f], roles[what] = _sha(data), f
        rec['files'], rec['roles'] = files, roles
    produced = {f for rec in records.values() for f in rec.get('files', {})}
    if os.path.isdir(out_root):
        for d, _subs, fs in os.walk(out_root, topdown=False):
            for f in fs:
                rel = os.path.relpath(os.path.join(d, f), out_root)
                if rel not in produced:
                    os.remove(os.path.join(d, f))
            if d != out_root and not os.listdir(d):
                os.rmdir(d)
    os.makedirs(cache_dir, exist_ok=True)
    with open(manifest_path, 'w') as fh:
        json.dump({'code': CODE, 'scale': TILE_SCALE, 'tiles': records}, fh)
    index: dict = {p: {} for p in planes}
    for rec in records.values():
        if not rec.get('empty'):
            index[rec['plane']][(rec['c'], rec['r'])] = rec
    return {'index': index, 'written': written, 'reused': reused}


# --- per-tile data --------------------------------------------------------------------

def _rle(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f'{j - i}{s[i]}')
        i = j
    return ''.join(out)


def tile_data(chunks: list, plane: str, c: int, r: int, sprite_map: dict) -> dict:
    """Walk, terrain, tiers and deck walk (64 x 64 cells), stands and props (by their foot)
    of one world tile, in world coordinates."""
    walk = [['#'] * TCELLS for _ in range(TCELLS)]
    terrain = [[EMPTY_TERRAIN] * TCELLS for _ in range(TCELLS)]
    tiers = [['0'] * TCELLS for _ in range(TCELLS)]
    deck = [['#'] * TCELLS for _ in range(TCELLS)]
    has_tiers = has_deck = False
    stands, objects = {}, []
    wc0, wr0 = c * TCELLS, r * TCELLS
    for ch in chunks:
        if ch.plane != plane:
            continue
        oc, orow = ch.origin[0] // CELL, ch.origin[1] // CELL
        for tr in range(TCELLS):
            cr = wr0 + tr - orow
            if not 0 <= cr < ch.rows:
                continue
            lo, hi = max(0, oc - wc0), min(TCELLS, oc + ch.cols - wc0)
            if lo >= hi:
                continue
            a, b = wc0 + lo - oc, wc0 + hi - oc
            walk[tr][lo:hi] = ch.walk[cr][a:b]
            terrain[tr][lo:hi] = ch.terrain[cr][a:b]
            if ch.tiers:
                tiers[tr][lo:hi] = ch.tiers[cr][a:b]
                has_tiers = True
            if ch.deck_walk:
                deck[tr][lo:hi] = ch.deck_walk[cr][a:b]
                has_deck = True
        ox, oy = ch.origin
        for s, (x, y) in ch.stands.items():
            if (x + ox) // TILE == c and (y + oy) // TILE == r:
                stands[s] = [x + ox, y + oy]
        for (i, k, x, y, w, h) in ch._sized_objects:
            # by its foot (kept inside the chunk's box, as cut_zone does)
            fx = min(max(x + w // 2, 0), ch.w - 1) + ox
            fy = min(max(y + h - 2, 0), ch.h - 1) + oy
            if fx // TILE == c and fy // TILE == r:
                objects.append([i, k, x + ox, y + oy, w, h])
    flat = lambda g: ''.join(''.join(row) for row in g)  # noqa: E731
    out = {'walk': _rle(flat(walk)), 'terrain': _rle(flat(terrain))}
    if has_tiers and any(v != '0' for row in tiers for v in row):
        out['tiers'] = _rle(flat(tiers))
    if has_deck and any(v == '.' for row in deck for v in row):
        out['deck'] = _rle(flat(deck))
    out['stands'] = stands
    out['objects'] = sorted(objects, key=lambda o: (o[3] + o[5], o[2], o[0]))
    return out


def export_ts(chunks: list, result: dict, sprite_map: dict):
    index = result['index']
    planes = sorted({ch.plane for ch in chunks}, key=lambda p: ['continent', 'orbit', 'moon', 'hut'].index(p)
                    if p in ('continent', 'orbit', 'moon', 'hut') else 9)
    areas = [{'id': a['id'], 'plane': ch.plane, 'chunk': ch.id, 'kind': a['kind'],
              'rect': [a['rect'][0] + ch.origin[0], a['rect'][1] + ch.origin[1], a['rect'][2], a['rect'][3]],
              **({'cells': a['cells']} if a.get('cells') else {})} for ch in chunks for a in ch.areas]
    decks = [{'chunk': ch.id, 'rect': [d['rect'][0] + ch.origin[0], d['rect'][1] + ch.origin[1], d['rect'][2], d['rect'][3]],
              'height': d['height'],
              'connectors': [{'kind': k['kind'], 'bottom': [k['bottom'][0] + ch.origin[0], k['bottom'][1] + ch.origin[1]],
                              'top': [k['top'][0] + ch.origin[0], k['top'][1] + ch.origin[1]]} for k in d['connectors']]}
             for ch in chunks for d in ch.decks]
    lines = [
        '// Generated by scripts/art/world_canvas.py. Do not edit by hand.',
        '/* eslint-disable */',
        '/** The world canvas, step 1 (docs/vision/region-canvas.md): the world as chunks on planes,',
        ' *  composited into 256 px world tiles. Not read by the game yet; lib/world-canvas.test.ts',
        ' *  checks it against the zones it was assembled from. */',
        f'export const WORLD_TILE = {{ size: {TILE}, cell: {CELL}, grid: {GRID}, scale: {TILE_SCALE} }} as const;',
        f'export const worldPlanes = {json.dumps(planes)} as const;',
        'export type WorldPlane = (typeof worldPlanes)[number];',
        '/** A chunk: a piece of the world authored whole (a region, a route, the land between). Its box',
        ' *  is [origin, origin + size] in world px; it paints `margin` px past it, blended over its neighbours. */',
        "export type WorldChunk = { id: string; kind: 'region' | 'route' | 'land'; plane: WorldPlane; origin: readonly [number, number]; size: readonly [number, number]; margin: number };",
        'export const worldChunks: readonly WorldChunk[] = ' + json.dumps(
            [{'id': ch.id, 'kind': ch.kind, 'plane': ch.plane, 'origin': list(ch.origin), 'size': [ch.w, ch.h], 'margin': ch.margin}
             for ch in chunks]) + ';',
        '/** A named part of the world (today one per zone, and the garden), for names, the map, saves and',
        ' *  the ways, in world px. `cells`, when given, are walk rows of the rect (\'.\' inside), for any shape. */',
        "export type WorldArea = { id: string; plane: WorldPlane; chunk: string; kind: 'zone' | 'garden'; rect: readonly [number, number, number, number]; cells?: readonly string[] };",
        f'export const worldAreas: readonly WorldArea[] = {json.dumps(areas)};',
        '/** [id, sprite, x, y, w, h] in world px (ids are \'area:id\'), listed in the tile its foot stands in. */',
        'export type WorldObject = readonly [string, string, number, number, number, number];',
        '/** One world tile: its picture (`art`, a key of worldTileArt, absent where no ground is drawn; `fill`',
        ' *  when it is one colour, so it can be drawn as a plain colour), and',
        ' *  64 x 64 walk cells from its top-left, each run-length encoded row after row (unrle, tileRows):',
        " *  walk '.'/'#'; terrain '~' water, '!' lava, '^' wall or cliff, '=' path, '.' ground, '-' no chunk;",
        ' *  tiers, the terrace of each cell (omitted when all 0); deck, the deck level\'s walk (when it has one).',
        ' *  Stands (\'area:stand\') and props in world px; `flow` is the box [x, y, w, h] of its moving water. */',
        'export type WorldTile = { art: string; fill?: string; walk: string; terrain: string; tiers?: string; deck?: string; stands: Readonly<Record<string, readonly [number, number]>>; objects: readonly WorldObject[]; flow?: readonly [number, number, number, number] };',
        '/** \'12.3#\' -> twelve \'.\' then three \'#\'. */',
        "export const unrle = (s: string) => s.replace(/(\\d+)([^\\d])/g, (_m, n: string, c: string) => c.repeat(Number(n)));",
        '/** A tile\'s cells as rows of 64. */',
        f'export const tileRows = (s: string): string[] => {{ const flat = unrle(s); return Array.from({{ length: {TCELLS} }}, (_v, r) => flat.slice(r * {TCELLS}, (r + 1) * {TCELLS})); }};',
        'export const worldTiles: Record<WorldPlane, Readonly<Record<string, WorldTile>>> = {',
    ]
    for p in planes:
        lines.append(f'  {p}: {{')
        touched = {t for ch in chunks if ch.plane == p for t in ch.tiles()}
        for (c, r) in sorted(touched, key=lambda t: (t[1], t[0])):
            rec = index[p].get((c, r))
            d = tile_data(chunks, p, c, r, sprite_map)
            if not rec and not d['stands'] and not d['objects'] and '.' not in d['walk']:
                continue  # nothing here: no picture, nothing to walk on or stand at
            t = {**({'art': rec['art']} if rec else {}), **({'fill': rec['fill']} if rec and rec['fill'] else {}),
                 'walk': d['walk'], 'terrain': d['terrain'],
                 **({'tiers': d['tiers']} if 'tiers' in d else {}), **({'deck': d['deck']} if 'deck' in d else {}),
                 'stands': d['stands'], 'objects': d['objects'], **({'flow': rec['flow']} if rec and rec['flow'] else {})}
            lines.append(f"    '{c},{r}': {json.dumps(t)},")
        lines.append('  },')
    seams = {ch.id: [[c + ch.origin[0] // CELL, r + ch.origin[1] // CELL, k] for (c, r, k) in ch.seams] for ch in chunks}
    lines += [
        '};',
        '/** The seams settled: [world col, world row, \'open\' | \'shut\'] where the walk over the whole chunk',
        ' *  (the zone rules, no seams) differs from the zones\' grids joined, and the world walk takes it. */',
        "export const worldSeams: Readonly<Record<string, readonly (readonly [number, number, 'open' | 'shut'])[]>> = " + json.dumps(seams) + ';',
        '/** Decks (two-level-walk.md): their box, how high they are drawn and their connectors, in world px. */',
        "export type WorldDeck = { chunk: string; rect: readonly [number, number, number, number]; height: number; connectors: readonly { kind: 'stair' | 'ramp' | 'lift'; bottom: readonly [number, number]; top: readonly [number, number] }[] };",
        f'export const worldDecks: readonly WorldDeck[] = {json.dumps(decks)};',
        '/** The moving water\'s frames (scripts/art/water_flow.py). */',
        f'export const WORLD_FLOW = {{ frames: {water_flow.FRAMES}, frameMs: {water_flow.FRAME_MS} }} as const;',
        '',
    ]
    ident = lambda f: 'img_' + re.sub(r'[^0-9a-zA-Z]+', '_', f)  # noqa: E731  (img_continent_t_1_12)
    arts = sorted({rec['art'] for p in planes for rec in index[p].values()})
    flows = [(p, c, r) for p in planes for (c, r), rec in sorted(index[p].items()) if rec['flow']]
    decked = [(p, c, r) for p in planes for (c, r), rec in sorted(index[p].items()) if rec['deck']]
    assets = [
        '// Generated by scripts/art/world_canvas.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        "import type { WorldPlane } from './world-canvas';",
        *[f"import {ident(a)} from '@/assets/world/{a}.png';" for a in arts],
        *[f"import {ident(f'{p}/f_{_tag(c)}_{_tag(r)}')} from '@/assets/world/{p}/f_{_tag(c)}_{_tag(r)}.png';" for (p, c, r) in flows],
        *[f"import {ident(f'{p}/{k}_{_tag(c)}_{_tag(r)}')} from '@/assets/world/{p}/{k}_{_tag(c)}_{_tag(r)}.png';"
          for (p, c, r) in decked for k in ('d', 's')],
        '/** Each ground picture by its key (WorldTile.art): a tile\'s own, or one shared by several. */',
        'export const worldTileArt: Readonly<Record<string, ImageSourcePropType>> = {',
        *[f"  '{a}': {ident(a)}," for a in arts],
        '};',
        '/** Each tile\'s moving water, frames stacked (boxes in WorldTile.flow), by plane and \'col,row\'. */',
        'export const worldFlowArt: Record<WorldPlane, Readonly<Record<string, ImageSourcePropType>>> = {',
        *[f"  {p}: {{ " + ', '.join(f"'{c},{r}': {ident(f'{p}/f_{_tag(c)}_{_tag(r)}')}" for (q, c, r) in flows if q == p) + ' },' for p in planes],
        '};',
        '/** Decks drawn over a tile, and the street under them darkened with their shadow. */',
        'export const worldDeckArt: Record<WorldPlane, Readonly<Record<string, { deck: ImageSourcePropType; shadow: ImageSourcePropType }>>> = {',
        *[f"  {p}: {{ " + ', '.join(f"'{c},{r}': {{ deck: {ident(f'{p}/d_{_tag(c)}_{_tag(r)}')}, shadow: {ident(f'{p}/s_{_tag(c)}_{_tag(r)}')} }}"
                                    for (q, c, r) in decked if q == p) + ' },' for p in planes],
        '};',
        '',
    ]
    for name, text in (('world-canvas.ts', lines), ('world-canvas-assets.ts', assets)):
        with open(os.path.join(worlds.ROOT, 'lib', name), 'w') as f:
            f.write('\n'.join(text))
    import subprocess  # formatted as the repository formats, so reruns never drift
    subprocess.run(['npx', 'oxfmt', '--write', 'lib/world-canvas.ts', 'lib/world-canvas-assets.ts'],
                   cwd=worlds.ROOT, check=False, capture_output=True)


# --- the build -------------------------------------------------------------------------

def _painted(id: str, fn, sources: tuple, sprite_map: dict) -> tuple:
    """A painted chunk, from the cache when its sources are unchanged."""
    if not sources:
        return finish(fn(), sprite_map), False
    digest = _sha(CODE, *[open(os.path.join(worlds.ROOT, s), 'rb').read() for s in sources])
    path = os.path.join(CACHE, 'chunks', f'{id}.pkl')
    try:
        with open(path, 'rb') as fh:
            got = pickle.load(fh)
        if got['digest'] == digest:
            return got['chunk'], True
    except (OSError, pickle.PickleError, EOFError, KeyError):
        pass
    ch = finish(fn(), sprite_map)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as fh:
        pickle.dump({'digest': digest, 'chunk': ch}, fh)
    return ch, False


def check_planes(chunks: list):
    """Chunks on one plane may touch and blend their margins, never overlap their boxes."""
    for plane in {ch.plane for ch in chunks}:
        on = [ch for ch in chunks if ch.plane == plane]
        for i, a in enumerate(on):
            ax, ay = a.origin
            for b in on[i + 1:]:
                bx, by = b.origin
                assert not (ax < bx + b.w and bx < ax + a.w and ay < by + b.h and by < ay + a.h), \
                    f'{a.id} and {b.id} overlap on the {plane} plane'


def build_all(built: dict):
    """Every chunk (painted, or assembled from today's zones), its tiles and its data."""
    import zones
    t0 = time.time()
    sprite_map = zones.sprites()
    chunks, cached = [], []
    for region in zones.LAYOUT:
        if region in PAINTERS:
            fn, sources = PAINTERS[region]
            ch, hit = _painted(region, fn, sources, sprite_map)
            if hit:
                cached.append(region)
        else:
            ch = finish(from_zones(region, built), sprite_map)
            check_cut(ch, built)
        chunks.append(ch)
    check_planes(chunks)
    selftest()
    result = write_world(chunks)
    export_ts(chunks, result, sprite_map)
    n = sum(len(v) for v in result['index'].values())
    shared = len({rec['art'] for v in result['index'].values() for rec in v.values() if rec['art'].startswith('shared/')})
    print(f'ok world canvas: {len(chunks)} chunks, {n} tiles at {TILE_SCALE}x ({result["written"]} composited, '
          f'{result["reused"]} kept from the cache, {shared} shared pictures), '
          f'{sum(len(ch.seams) for ch in chunks)} seam cells settled'
          f'{", painters cached: " + ", ".join(cached) if cached else ""}, {time.time() - t0:.1f} s')


def selftest():
    """What today's data does not exercise, checked on two small chunks in a scratch folder:
    a margin blends over its neighbour across a tile edge, a tile of one colour becomes a
    shared colour picture and identical tiles share one, the cache keeps the tiles a change
    does not touch, and the compatibility cut returns a painted chunk's part exactly."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out, cache = os.path.join(tmp, 'world'), os.path.join(tmp, 'cache')
        sea = Chunk('sea', 512, 256, kind='land', plane='test', origin=(0, 0))
        sea.ground.paste((20, 60, 110, 255), (0, 0, 512, 256))
        isle = Chunk('isle', 256, 256, plane='test', origin=(512, 0), margin=16)
        isle.ground.paste((200, 180, 120, 255), isle.at(0, 0) + isle.at(256, 256))
        isle.ground.paste((200, 180, 120, 128), (0, 0, 16, 288))  # its west margin: wet sand, half over the sea
        for ch in (sea, isle):
            ch.walk = ['.' * ch.cols] * ch.rows
            ch.terrain = ['.' * ch.cols] * ch.rows
            ch.flow_given = True
            ch.areas = [{'id': ch.id, 'kind': 'zone', 'rect': (0, 0, ch.w, ch.h)}]
            ch._sized_objects = []
        check_planes([sea, isle])
        r1 = write_world([sea, isle], out, cache)
        idx = r1['index']['test']
        assert idx[(0, 0)]['art'] == 'shared/u_143c6eff', 'a tile of open sea is one shared colour'
        assert idx[(1, 0)]['art'] != idx[(0, 0)]['art'], 'the sea under the isle\'s margin is not open sea'
        tile = np.asarray(Image.open(os.path.join(out, idx[(1, 0)]['art'] + '.png')))
        k = TILE_SCALE
        edge, inside = tile[0, (TILE - 8) * k], tile[0, (TILE - 24) * k]
        assert tuple(inside) == (20, 60, 110, 255), 'past the margin the sea is untouched'
        assert tuple(edge) == (110, 120, 115, 255), f'the margin blends half over the sea ({tuple(edge)})'
        assert r1['reused'] == 0
        isle.ground.paste((90, 140, 60, 255), isle.at(64, 64) + isle.at(128, 128))  # the isle's lane redraws it
        r2 = write_world([sea, isle], out, cache)
        assert r2['reused'] == 1, 'only the tiles the changed chunk touches are redrawn'
        cut = cut_zone(isle, (64, 64, 64, 64))
        assert cut['ground'].tobytes() == Image.new('RGBA', (64, 64), (90, 140, 60, 255)).tobytes(), 'the cut is exact'
        twin = Chunk('twin', 256, 256, kind='land', plane='test', origin=(0, 256))
        twin.ground.paste(isle.core(), (0, 0))
        twin.walk, twin.terrain, twin.flow_given = isle.walk, isle.terrain, True
        twin.areas, twin._sized_objects = [{'id': 'twin', 'kind': 'zone', 'rect': (0, 0, 256, 256)}], []
        r3 = write_world([sea, isle, twin], out, cache)  # (its tile is the isle's box, exactly)
        art = r3['index']['test'][(0, 1)]['art']
        assert art.startswith('shared/s_') and art == r3['index']['test'][(2, 0)]['art'], 'identical tiles share a picture'
        assert r3['reused'] >= 1 and os.path.exists(os.path.join(out, art + '.png'))
        assert not os.path.exists(os.path.join(out, 'test', 't_2_0.png')), 'the renamed picture is not left behind'
        shutil.rmtree(out)


if __name__ == '__main__':
    import zones
    zones.main()  # draws the zones, then hands them to build_all()

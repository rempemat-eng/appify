"""Region canvases, step 1: the build (docs/vision/region-canvas.md).

Matt, 20 Oct (world plan v2, decision 2): each region becomes one continuous canvas on
the 8 px grid, streamed in 256 x 256 render tiles, its zones becoming named areas. Later
the same day (10:58) he asked for one connected world, so a canvas is just a rectangle of
the world: it has a plane ('continent' for the land you walk, others for the places you
reach by rocket or through a door) and an origin in world pixels. Tiles are named by
their world tile column and row and composited from every canvas on that plane; walk
grids, areas, stands and props are all in world coordinates. Nothing here assumes a
region is a closed box.

Step 1 changes nothing in the game. zones.py still draws the zones and writes
assets/zones/** and lib/zone-*.ts, which the game reads. At the end of its run it hands
its built zones to build_all() here, which assembles each region's canvas from them (the
adapter, from_zones) and writes the new outputs alongside:

  assets/world/<plane>/t_<col>_<row>.png   the ground, one world tile, at TILE_SCALE
  assets/world/<plane>/f_<col>_<row>.png   its moving water (water_flow.py), 1x, frames stacked
  lib/region-canvas.ts                     typed data: canvases, areas, props, stands, walk, terrain
  lib/region-canvas-assets.ts              the tile pictures, imported one by one (they bundle on native)

A lane that draws a region whole registers a painter instead (see `painter`): a function
returning a RegionCanvas of any size on the 8 px grid, in its own pixels. finish() then
derives what the adapter copies from the zones: the walk grid, the terrain and the
moving water. The check is lib/region-canvas.test.ts.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import water_flow  # noqa: E402
import worlds  # noqa: E402

GRID = 8          # canvases, origins and areas sit on the 8 px soft grid
CELL = 4          # walk cells, as the zones have them
TILE = 256        # render tiles, in art px (64 x 64 walk cells)
# The tiles' picture scale. The plan (world-plan.md, decision 8): 1x with nearest-neighbour
# scaling once that is shown crisp on iOS, Android and the web; 2x until then. The web is
# crisp at 1x (data-pixel sets image-rendering: pixelated); React Native's Image has no
# nearest-neighbour filter on iOS or Android, so 2x stays the default until step 2 tests it.
TILE_SCALE = int(os.environ.get('REGION_TILE_SCALE', '2'))
EMPTY_TERRAIN = '-'  # a terrain cell no canvas covers (the valley's corners today)

# Where each region lies: its plane and the world pixel of its canvas's top-left.
# PLACEHOLDERS until world plan v3 sets the continent: the regions stand in a row on
# the continent, a tile apart, the valley at the world's origin (so the valley's world
# pixels are today's region pixels); the station, the moon and the hut are each their
# own plane. Moving a region changes only its origin here; its tiles are renamed by the
# build and every coordinate in lib/region-canvas.ts moves with it.
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


class RegionCanvas:
    """One region drawn whole, in its own pixels (0, 0 at its top-left).

    ground   PIL RGBA image, w x h (transparent where the region has no ground)
    objects  [(id, sprite key, x, y)], the sprite's top-left in canvas px (as zones.build)
    stands   {name: (x, y)}
    blocked  set of canvas px a walk may not enter (water, cliffs, walls drawn in the ground)
    water    set of canvas px that are water, when declared (else read by colour)
    decks    [{'walk': set of px, 'height': px, 'connectors': [...]}] (two-level-walk.md)
    areas    [{'id', 'kind', 'rect': (x, y, w, h)} or with 'cells': rows of '#'/'.' too]
    walk, terrain, flow: filled by finish() for a painted canvas, copied by the adapter
    """

    def __init__(self, region: str, w: int, h: int):
        assert w % GRID == 0 and h % GRID == 0, f'{region}: a canvas sits on the {GRID} px grid ({w} x {h})'
        self.region, self.w, self.h = region, w, h
        self.plane, self.origin = PLACES[region]
        assert self.origin[0] % GRID == 0 and self.origin[1] % GRID == 0, f'{region}: origin off the grid'
        self.ground = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.objects: list = []
        self.stands: dict = {}
        self.blocked: set = set()
        self.water: set | None = None
        self.decks: list = []
        self.deck_art: Image.Image | None = None      # the decks drawn (decks.py), canvas-sized
        self.deck_shadow: Image.Image | None = None
        self.areas: list = []
        self.walk: list[str] | None = None
        self.terrain: list[str] | None = None
        self.flow: np.ndarray | None = None           # (FRAMES, h, w, 4) uint8, or None
        self.flow_given = False                       # the adapter brings the zones' own flow
        self.deck_walk: list[str] | None = None       # the deck level's walk rows, when it has decks
        self.seams: list = []                         # adapter: where a whole-canvas walk differs

    @property
    def cols(self):
        return self.w // CELL

    @property
    def rows(self):
        return self.h // CELL


PAINTERS: dict = {}


def painter(region: str):
    """Register a function that paints a region whole (a lane's generator):

        @regions.painter('steam')
        def cogsworth() -> regions.RegionCanvas:
            rc = regions.RegionCanvas('steam', 704, 960)
            ...draw rc.ground, list rc.objects / stands / blocked / areas...
            return rc

    build_all() then uses it in place of the zones. Until step 2 the game still reads the
    zones, so a painted region also cuts its canvas into zones (as the isles already do)."""
    def wrap(fn):
        PAINTERS[region] = fn
        return fn
    return wrap


# --- deriving a canvas's walk, terrain and moving water (a painted canvas) -------------

def derive_walk(rc: RegionCanvas, sprite_map: dict) -> list[str]:
    """The walk grid from the canvas alone, by the rules zones.build applies to a zone:
    a prop's foot band blocks (gateways excepted), drawn obstacles block, and a cell beside
    lava is kept back from on each side. Over the whole canvas, so nothing is cut at a seam."""
    import zones
    import world_lint
    cells = set()
    for (_id, key, x, y) in rc.objects:
        if key in zones.OVERHEAD:
            continue
        sp = sprite_map[key]
        foot = 20 if sp.w > 60 else 10 if key in ('tree', 'tree_small', 'tree_autumn', 'pine') else 6
        gap = zones.OPENINGS.get(key)
        for yy in range(y + sp.h - foot, y + sp.h):
            for xx in range(x + 3, x + sp.w - 3):
                if gap and x + gap[0] <= xx < x + gap[1]:
                    continue
                cells.add((xx // CELL, yy // CELL))
    ground = {(x // CELL, y // CELL) for (x, y) in rc.blocked}
    px = rc.ground.load()
    hot = {(c, r) for (c, r) in ground
           if 0 <= c < rc.cols and 0 <= r < rc.rows and world_lint._lava(*px[c * CELL + 2, r * CELL + 2][:3])}
    ground |= {(c + d, r) for (c, r) in hot for d in (-1, 1) if 0 <= c + d < rc.cols}
    cells |= ground
    # where the canvas has no ground at all (a gap round the land), nothing to walk on
    bare = np.asarray(rc.ground)[..., 3].reshape(rc.rows, CELL, rc.cols, CELL).max(axis=(1, 3)) == 0
    return [''.join('#' if (c, r) in cells or bare[r, c] else '.' for c in range(rc.cols)) for r in range(rc.rows)]


def derive_terrain(rc: RegionCanvas) -> list[str]:
    import world_lint
    rows = world_lint.classify(rc.ground, rc.blocked, rc.water, cols=rc.cols, rows=rc.rows)
    # where the canvas is transparent, no ground
    a = np.asarray(rc.ground)[..., 3].reshape(rc.rows, CELL, rc.cols, CELL).max(axis=(1, 3))
    return [''.join(ch if a[r, c] else EMPTY_TERRAIN for c, ch in enumerate(row)) for r, row in enumerate(rows)]


def derive_flow(rc: RegionCanvas, terrain: list[str]):
    """The moving water over the whole canvas (water_flow.sheet, as zones.build does for a
    zone): its frames at full canvas size, or None."""
    import world_lint
    px = rc.ground.load()
    wet, hot = set(), set()
    for r, row in enumerate(terrain):
        for c, ch in enumerate(row):
            if ch not in '~!':
                continue
            for y in range(r * CELL - 1, r * CELL + CELL + 1):
                for x in range(c * CELL - 1, c * CELL + CELL + 1):
                    if not (0 <= x < rc.w and 0 <= y < rc.h):
                        continue
                    if rc.water is not None:
                        if ch == '~' and (x, y) in rc.water:
                            wet.add((x, y))
                        continue
                    p = px[x, y][:3]
                    if ch == '~' and world_lint._bluish(*p):
                        wet.add((x, y))
                    elif ch == '!' and world_lint._lava(*p):
                        hot.add((x, y))
    sheet = water_flow.sheet(rc.ground, wet, hot)
    return None if not sheet else unstack(*sheet, rc.w, rc.h)


def unstack(img: Image.Image, rect, w: int, h: int) -> np.ndarray:
    """A water_flow sheet (frames stacked in a box) as full-size frames."""
    x0, y0, bw, bh = rect
    a = np.asarray(img.convert('RGBA'))
    out = np.zeros((water_flow.FRAMES, h, w, 4), dtype=np.uint8)
    for f in range(water_flow.FRAMES):
        out[f, y0:y0 + bh, x0:x0 + bw] = a[f * bh:(f + 1) * bh]
    return out


def finish(rc: RegionCanvas, sprite_map: dict):
    """Fill in what a painter leaves to the build, and check the canvas."""
    if rc.walk is None:
        rc.walk = derive_walk(rc, sprite_map)
    if rc.terrain is None:
        rc.terrain = derive_terrain(rc)
    if rc.flow is None and not rc.flow_given:
        rc.flow = derive_flow(rc, rc.terrain)
    assert len(rc.walk) == rc.rows and all(len(r) == rc.cols for r in rc.walk), f'{rc.region}: walk size'
    assert rc.areas, f'{rc.region}: a canvas names its areas'
    for a in rc.areas:
        x, y, w, h = a['rect']
        assert x % GRID == 0 and y % GRID == 0 and w % GRID == 0 and h % GRID == 0, f'{rc.region}/{a["id"]}: off the grid'
        assert 0 <= x and 0 <= y and x + w <= rc.w and y + h <= rc.h, f'{rc.region}/{a["id"]}: outside the canvas'
    loose = [(c, r) for r, row in enumerate(rc.walk) for c, ch in enumerate(row)
             if ch == '.' and not any(area_has(a, c * CELL, r * CELL) for a in rc.areas)]
    assert not loose, f'{rc.region}: {len(loose)} walkable cells in no area (first {loose[:3]})'
    return rc


def area_has(a: dict, x: int, y: int) -> bool:
    ax, ay, aw, ah = a['rect']
    if not (ax <= x < ax + aw and ay <= y < ay + ah):
        return False
    cells = a.get('cells')
    return cells is None or cells[(y - ay) // CELL][(x - ax) // CELL] == '.'


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
        for c, ch in enumerate(row[:cols]):
            x, y = c * CELL + CELL // 2, r * CELL + CELL // 2
            if any(x0 <= x < x1 and y0 <= y < y1 for (x0, x1, y0, y1) in openings):
                line += '.'
            elif c < 2 and not (west and west[0] <= y < west[1]):
                line += '#'
            elif c >= cols - 2 and not (east and east[0] <= y < east[1]):
                line += '#'
            else:
                line += ch
        out.append(line)
    return out


def from_zones(region: str, built: dict) -> RegionCanvas:
    """A region's canvas assembled from today's zones: each zone's ground, props, stands,
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
    rc = RegionCanvas(region, cols * W, rows * H)
    walk = [['#'] * rc.cols for _ in range(rc.rows)]
    terrain = [[EMPTY_TERRAIN] * rc.cols for _ in range(rc.rows)]
    deck_rows = [['#'] * rc.cols for _ in range(rc.rows)]
    flow = None
    for z, (col, row) in zs.items():
        ox, oy = (col - min_c) * W, (row - min_r) * H
        oc, orow = ox // CELL, oy // CELL
        if z == 'garden':
            g = Image.open(os.path.join(worlds.ROOT, 'assets', 'garden', 'ground.png')).convert('RGBA')
            rc.ground.paste(g.resize((W, H), Image.NEAREST), (ox, oy))
            zwalk, zterrain = _garden_walk(), world_lint.garden_zone()['terrain']
            rc.areas.append({'id': z, 'kind': 'garden', 'rect': (ox, oy, W, H)})
        else:
            b = built[z]
            assert b['ground_img'].size == (W, H), f'{z}: ground is not {W} x {H}'
            rc.ground.paste(b['ground_img'], (ox, oy))
            rc.objects += [(f'{z}:{i}', k, x + ox, y + oy) for (i, k, x, y) in b['objects']]
            rc.stands.update({f'{z}:{s}': (x + ox, y + oy) for s, (x, y) in b['stands'].items()})
            rc.blocked |= {(x + ox, y + oy) for (x, y) in b['blocked']}
            if b.get('water'):
                rc.water = (rc.water or set()) | {(x + ox, y + oy) for (x, y) in b['water']}
            zwalk, zterrain = b['walk'], b['terrain']
            rc.areas.append({'id': z, 'kind': 'zone', 'rect': (ox, oy, W, H)})
            if b.get('deck'):
                d = b['deck']
                for r, line in enumerate(d['walk']):
                    for c, ch in enumerate(line):
                        if ch == '.':
                            deck_rows[orow + r][oc + c] = '.'
                rc.decks.append({'rect': (ox, oy, W, H), 'height': d['height'], 'connectors': [
                    {'kind': c['kind'], 'bottom': (c['bottom'][0] + ox, c['bottom'][1] + oy),
                     'top': (c['top'][0] + ox, c['top'][1] + oy)} for c in d['connectors']]})
                for attr, name in (('deck_art', 'deck.png'), ('deck_shadow', 'deck-shadow.png')):
                    if getattr(rc, attr) is None:
                        setattr(rc, attr, Image.new('RGBA', (rc.w, rc.h), (0, 0, 0, 0)))
                    art = Image.open(os.path.join(worlds.ROOT, 'assets', 'zones', z, name)).convert('RGBA')
                    getattr(rc, attr).paste(art.resize((W, H), Image.NEAREST), (ox, oy))
            if z in zones.FLOW_RECT:
                sheet = Image.open(os.path.join(worlds.ROOT, 'assets', 'zones', z, 'flow.png'))
                frames = unstack(sheet, zones.FLOW_RECT[z], W, H)
                if flow is None:
                    flow = np.zeros((water_flow.FRAMES, rc.h, rc.w, 4), dtype=np.uint8)
                flow[:, oy:oy + H, ox:ox + W] = frames
        for r, line in enumerate(zwalk):
            walk[orow + r][oc:oc + W // CELL] = list(line[:W // CELL])
        for r, line in enumerate(zterrain):
            terrain[orow + r][oc:oc + W // CELL] = list(line[:W // CELL])
    rc.walk = [''.join(r) for r in walk]
    rc.terrain = [''.join(r) for r in terrain]
    rc.flow, rc.flow_given = flow, True
    if rc.decks:
        rc.deck_walk = [''.join(r) for r in deck_rows]
    # where the whole canvas, walked by the zone rules, differs from the zones' grids
    # joined: the seam rules (share_feet, the lava step-back clipped at a zone's edge).
    # Reported, not hidden: step 2 decides which to keep.
    derived = derive_walk(rc, zones.sprites())
    garden = [a['rect'] for a in rc.areas if a['kind'] == 'garden']
    for r in range(rc.rows):
        for c in range(rc.cols):
            if derived[r][c] == rc.walk[r][c]:
                continue
            x, y = c * CELL, r * CELL
            if any(gx <= x < gx + gw and gy <= y < gy + gh for (gx, gy, gw, gh) in garden):
                continue  # the garden's walk is the garden's own (its props are not zone props)
            rc.seams.append((c, r, 'open' if derived[r][c] == '.' else 'shut'))
    return rc


# --- writing the world: tiles keyed by world coordinates ---------------------------------

def _tag(n: int) -> str:
    return str(n).replace('-', 'm')


def _tiles_of(rc: RegionCanvas):
    """The world tiles (col, row) a canvas touches."""
    x0, y0 = rc.origin
    return [(c, r) for r in range(y0 // TILE, -(-(y0 + rc.h) // TILE))
            for c in range(x0 // TILE, -(-(x0 + rc.w) // TILE))]


def _cut(rc: RegionCanvas, layer: np.ndarray, c: int, r: int) -> np.ndarray:
    """The part of a canvas-sized layer (..., h, w, 4) inside world tile (c, r), placed in
    a full tile (transparent where the canvas does not reach)."""
    x0, y0 = rc.origin
    tx, ty = c * TILE - x0, r * TILE - y0
    out = np.zeros(layer.shape[:-3] + (TILE, TILE, 4), dtype=np.uint8)
    sx0, sy0 = max(0, tx), max(0, ty)
    sx1, sy1 = min(rc.w, tx + TILE), min(rc.h, ty + TILE)
    if sx1 > sx0 and sy1 > sy0:
        out[..., sy0 - ty:sy1 - ty, sx0 - tx:sx1 - tx, :] = layer[..., sy0:sy1, sx0:sx1, :]
    return out


def _over(dst: np.ndarray, src: np.ndarray):
    """Canvases on one plane meet edge to edge: where two overlap, the later one's
    opaque pixels win (the check reports any overlap)."""
    m = src[..., 3] > 0
    dst[m] = src[m]


def write_world(canvases: list) -> dict:
    """Cut every plane into world tiles and write them; returns what the TS export needs."""
    out_root = os.path.join(worlds.ROOT, 'assets', 'world')
    if os.path.isdir(out_root):
        for d, _subs, files in os.walk(out_root, topdown=False):
            for f in files:
                os.remove(os.path.join(d, f))
            if d != out_root:
                os.rmdir(d)
    planes: dict = {}
    for rc in canvases:
        planes.setdefault(rc.plane, []).append(rc)
    index = {}
    pixels = {id(rc): np.asarray(rc.ground) for rc in canvases}
    deck_px = {id(rc): np.stack([np.asarray(rc.deck_art), np.asarray(rc.deck_shadow)])
               for rc in canvases if rc.deck_art is not None}
    for plane, rcs in planes.items():
        os.makedirs(os.path.join(out_root, plane), exist_ok=True)
        keys = sorted({t for rc in rcs for t in _tiles_of(rc)}, key=lambda t: (t[1], t[0]))
        tiles, flows, decks = [], {}, []
        for (c, r) in keys:
            ground = np.zeros((TILE, TILE, 4), dtype=np.uint8)
            flow = np.zeros((water_flow.FRAMES, TILE, TILE, 4), dtype=np.uint8)
            deck = np.zeros((2, TILE, TILE, 4), dtype=np.uint8)
            for rc in rcs:
                if (c, r) not in _tiles_of(rc):
                    continue
                _over(ground, _cut(rc, pixels[id(rc)], c, r))
                if rc.flow is not None:
                    _over(flow, _cut(rc, rc.flow, c, r))
                if rc.deck_art is not None:
                    _over(deck, _cut(rc, deck_px[id(rc)], c, r))
            if not ground[..., 3].any():
                continue  # nothing of any canvas here: no picture
            name = f'{_tag(c)}_{_tag(r)}'
            img = Image.fromarray(ground, 'RGBA')
            if TILE_SCALE != 1:
                img = img.resize((TILE * TILE_SCALE, TILE * TILE_SCALE), Image.NEAREST)
            img.save(os.path.join(out_root, plane, f't_{name}.png'), optimize=True)
            tiles.append((c, r))
            moving = flow[..., 3].any(axis=0)
            if moving.any():
                yy, xx = np.nonzero(moving)
                x0, x1, y0, y1 = int(xx.min()), int(xx.max()) + 1, int(yy.min()), int(yy.max()) + 1
                bh = y1 - y0
                stack = np.zeros((bh * water_flow.FRAMES, x1 - x0, 4), dtype=np.uint8)
                for f in range(water_flow.FRAMES):
                    stack[f * bh:(f + 1) * bh] = flow[f, y0:y1, x0:x1]
                # native scale, like the zones' flow: the renderer draws it pixelated
                Image.fromarray(stack, 'RGBA').save(os.path.join(out_root, plane, f'f_{name}.png'), optimize=True)
                flows[(c, r)] = (x0, y0, x1 - x0, bh)
            if deck[..., 3].any():
                for k, prefix in ((0, 'd'), (1, 's')):
                    Image.fromarray(deck[k], 'RGBA').resize((TILE * TILE_SCALE, TILE * TILE_SCALE), Image.NEAREST) \
                        .save(os.path.join(out_root, plane, f'{prefix}_{name}.png'), optimize=True)
                decks.append((c, r))
        index[plane] = {'tiles': tiles, 'flows': flows, 'decks': decks}
    return index


def _rle(row: str) -> str:
    import zones
    return zones.rle(row)


def export_ts(canvases: list, index: dict, sprite_map: dict):
    import zones
    planes = list(index)
    lines = [
        '// Generated by scripts/art/regions.py. Do not edit by hand.',
        '/* eslint-disable */',
        '/** Region canvases, step 1 (docs/vision/region-canvas.md): each region as one canvas, a',
        ' *  rectangle of the world on a plane, cut into world tiles. Not read by the game yet;',
        ' *  lib/region-canvas.test.ts checks it against the zones it was assembled from. */',
        f'export const WORLD_TILE = {{ size: {TILE}, cell: {CELL}, grid: {GRID}, scale: {TILE_SCALE} }} as const;',
        f'export const worldPlanes = {json.dumps(planes)} as const;',
        'export type WorldPlane = (typeof worldPlanes)[number];',
        '/** A named part of a canvas (today: one per zone, and the garden), in world px. `cells`, when',
        ' *  given, are walk rows of the rect (\'.\' inside the area), for areas of any shape. */',
        "export type CanvasArea = { id: string; kind: 'zone' | 'garden'; rect: readonly [number, number, number, number]; cells?: readonly string[] };",
        '/** [id, sprite, x, y, w, h] in world px (ids are \'area:id\'); drawn in order of their feet (y + h). */',
        'export type CanvasObject = readonly [string, string, number, number, number, number];',
        '/** Where a walk over the whole canvas (the zone rules, no seams) differs from the zones\' grids',
        ' *  joined: [col, row, \'open\' | \'shut\'] in the canvas\'s cells. Reported for step 2 to settle. */',
        "export type CanvasSeam = readonly [number, number, 'open' | 'shut'];",
        'export type RegionCanvas = {',
        '  plane: WorldPlane;',
        '  /** World px of the canvas\'s top-left: world = origin + region px. */',
        '  origin: readonly [number, number];',
        '  size: readonly [number, number];',
        '  areas: readonly CanvasArea[];',
        '  objects: readonly CanvasObject[];',
        '  /** \'area:stand\' -> world px. */',
        '  stands: Readonly<Record<string, readonly [number, number]>>;',
        '  /** Walk rows in 4 px cells from the origin (world cell = origin / 4 + [col, row]). */',
        '  walk: readonly string[];',
        "  /** One character per walk cell: '~' water, '!' lava, '^' wall or cliff, '=' path, '.' ground, '-' no canvas. */",
        '  terrain: readonly string[];',
        '  decks: readonly { rect: readonly [number, number, number, number]; height: number; connectors: readonly { kind: string; bottom: readonly [number, number]; top: readonly [number, number] }[] }[];',
        '  deckWalk?: readonly string[];',
        '  seams: readonly CanvasSeam[];',
        '};',
        "const unrle = (row: string) => row.replace(/(\\d+)([.#~!^=-])/g, (_m, n: string, c: string) => c.repeat(Number(n)));",
        'export const regionCanvases = {',
    ]
    for rc in canvases:
        ox, oy = rc.origin
        objs = ', '.join(json.dumps([i, k, x + ox, y + oy, sprite_map[k].w, sprite_map[k].h]) for (i, k, x, y) in rc.objects)
        areas = [{'id': a['id'], 'kind': a['kind'], 'rect': [a['rect'][0] + ox, a['rect'][1] + oy, a['rect'][2], a['rect'][3]],
                  **({'cells': a['cells']} if a.get('cells') else {})} for a in rc.areas]
        decks = [{'rect': [d['rect'][0] + ox, d['rect'][1] + oy, d['rect'][2], d['rect'][3]], 'height': d['height'],
                  'connectors': [{'kind': k['kind'], 'bottom': [k['bottom'][0] + ox, k['bottom'][1] + oy],
                                  'top': [k['top'][0] + ox, k['top'][1] + oy]} for k in d['connectors']]} for d in rc.decks]
        lines += [
            f'  {rc.region}: {{',
            f"    plane: '{rc.plane}',",
            f'    origin: [{ox}, {oy}],',
            f'    size: [{rc.w}, {rc.h}],',
            f'    areas: {json.dumps(areas)},',
            f'    objects: [{objs}],',
            f'    stands: {json.dumps({k: [x + ox, y + oy] for k, (x, y) in rc.stands.items()})},',
            f'    walk: {json.dumps([_rle(r) for r in rc.walk])}.map(unrle),',
            f'    terrain: {json.dumps([_rle(r) for r in rc.terrain])}.map(unrle),',
            f'    decks: {json.dumps(decks)},',
            *([f"    deckWalk: {json.dumps([_rle(r) for r in rc.deck_walk])}.map(unrle),"] if rc.decks else []),
            f'    seams: {json.dumps([list(s) for s in rc.seams])},',
            '  },',
        ]
    lines += [
        '} as const satisfies Record<string, RegionCanvas>;',
        'export type CanvasRegionId = keyof typeof regionCanvases;',
        '/** The world tiles that have a picture, per plane: [col, row]; tile (c, r) covers world px',
        ' *  [c * size, r * size] to [(c + 1) * size, (r + 1) * size], its picture saved at `scale`. */',
        'export const worldTiles: Record<WorldPlane, readonly (readonly [number, number])[]> = {',
        *[f'  {p}: {json.dumps([list(t) for t in index[p]["tiles"]])},' for p in planes],
        '};',
        '/** Moving water per tile (scripts/art/water_flow.py): \'col,row\' -> the box [x, y, w, h] in tile px;',
        f' *  its picture (1x) holds {water_flow.FRAMES} frames of the box stacked, {water_flow.FRAME_MS} ms apart. */',
        'export const worldTileFlow: Record<WorldPlane, Readonly<Record<string, readonly [number, number, number, number]>>> = {',
        *[f'  {p}: {json.dumps({f"{c},{r}": list(v) for (c, r), v in index[p]["flows"].items()})},' for p in planes],
        '};',
        '/** Tiles with a deck drawn over them (deck and its shadow, two-level-walk.md). */',
        'export const worldTileDecks: Record<WorldPlane, readonly (readonly [number, number])[]> = {',
        *[f'  {p}: {json.dumps([list(t) for t in index[p]["decks"]])},' for p in planes],
        '};',
        '',
    ]
    ident = lambda p, pre, c, r: f'{pre}{p.capitalize()}{_tag(c).capitalize()}_{_tag(r)}'  # noqa: E731
    path = lambda p, pre, c, r: f'@/assets/world/{p}/{pre}_{_tag(c)}_{_tag(r)}.png'  # noqa: E731
    assets = [
        '// Generated by scripts/art/regions.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        "import type { WorldPlane } from './region-canvas';",
    ]
    for p in planes:
        assets += [f"import {ident(p, 't', c, r)} from '{path(p, 't', c, r)}';" for (c, r) in index[p]['tiles']]
        assets += [f"import {ident(p, 'f', c, r)} from '{path(p, 'f', c, r)}';" for (c, r) in index[p]['flows']]
        for pre in ('d', 's'):
            assets += [f"import {ident(p, pre, c, r)} from '{path(p, pre, c, r)}';" for (c, r) in index[p]['decks']]
    for (const, pre, key) in (('worldTileArt', 't', 'tiles'), ('worldFlowArt', 'f', 'flows'),
                              ('worldDeckArt', 'd', 'decks'), ('worldDeckShadowArt', 's', 'decks')):
        doc = {'t': 'The ground of each world tile, \'col,row\' -> picture.',
               'f': 'Each tile\'s moving water, frames stacked (boxes in region-canvas.ts).',
               'd': 'The decks drawn over a tile.', 's': 'The street under a deck, darkened with its shadow.'}[pre]
        assets += [f'/** {doc} */',
                   f'export const {const}: Record<WorldPlane, Readonly<Record<string, ImageSourcePropType>>> = {{']
        for p in planes:
            items = ', '.join(f"'{c},{r}': {ident(p, pre, c, r)}" for (c, r) in index[p][key])
            assets.append(f'  {p}: {{ {items} }},' if items else f'  {p}: {{}},')
        assets.append('};')
    assets.append('')
    for name, text in (('region-canvas.ts', lines), ('region-canvas-assets.ts', assets)):
        with open(os.path.join(worlds.ROOT, 'lib', name), 'w') as f:
            f.write('\n'.join(text))
    import subprocess  # formatted as the repository formats, so reruns never drift
    subprocess.run(['npx', 'oxfmt', '--write', 'lib/region-canvas.ts', 'lib/region-canvas-assets.ts'],
                   cwd=worlds.ROOT, check=False, capture_output=True)


def build_all(built: dict):
    """Every region's canvas (painted, or assembled from its zones), its tiles and its data."""
    import time
    import zones
    t0 = time.time()
    sprite_map = zones.sprites()
    canvases = []
    for region in zones.LAYOUT:
        if region in PAINTERS:
            rc = finish(PAINTERS[region](), sprite_map)
        else:
            rc = finish(from_zones(region, built), sprite_map)
        canvases.append(rc)
    for plane in {rc.plane for rc in canvases}:  # canvases on one plane may touch, never overlap
        rects = [(rc.region, *rc.origin, rc.w, rc.h) for rc in canvases if rc.plane == plane]
        for i, (a, ax, ay, aw, ah) in enumerate(rects):
            for (b, bx, by, bw, bh) in rects[i + 1:]:
                assert not (ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah), \
                    f'{a} and {b} overlap on the {plane} plane'
    index = write_world(canvases)
    export_ts(canvases, index, sprite_map)
    n = sum(len(v['tiles']) for v in index.values())
    print(f'ok region canvases: {len(canvases)} regions, {n} tiles at {TILE_SCALE}x, '
          f'{sum(len(rc.seams) for rc in canvases)} seam cells reported, {time.time() - t0:.1f} s')


if __name__ == '__main__':
    import zones
    zones.main()  # draws the zones, then hands them to build_all()

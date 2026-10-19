"""Zones of the open world (living-world plan, "The open world", step W2).

Run: python3 scripts/art/zones.py   (ZONE_PREVIEW=dir writes a preview with the props)

A zone is one screen-sized place (320 x 576, the garden's size) joined to its
neighbours at its edges. Crossroads Town lies south of the garden: the road from the
garden gate enters at the top, the library and the houses face the square, Moss's
stall stands on its corner, the sparring ring sits in the meadow below, and a street
leaves east for the Town Park. The south edge stays a hedge until the Cove exists.

The zone renderer and saved position come with step W1 (Codex C19); until then this
draws the art and checks its own logic (every exit and stand reachable on foot).
"""
from __future__ import annotations

import functools
import json
import math
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.setdefault('zones', sys.modules[__name__])  # so the district modules share this one
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import garden_meadow as meadow  # noqa: E402
import garden_props as gp  # noqa: E402
import style  # noqa: E402
import world_props as wp  # noqa: E402
import worlds  # noqa: E402
import ground  # noqa: E402
from materials import G, P, STONE, WOOD, SLATE, RED, MATERIALS  # noqa: E402
import valley_props as vp  # noqa: E402
import steampunk_props as sp  # noqa: E402
import cyber_props as cp  # noqa: E402
import western_props as wsp  # noqa: E402
import caldera_props as cdp  # noqa: E402
import harbour_props as hbp  # noqa: E402
import castle_props as csp  # noqa: E402
import space_props as spp  # noqa: E402
import home_props as hp  # noqa: E402
import frost_props as fp  # noqa: E402
import isle_props as ip  # noqa: E402

# Each prop module may declare how its props meet the ground, so its owner registers a
# boat or a ladder without editing the lint: PLACEMENT = {'harbour_ferry': 'floating',
# 'pier_ladder': 'supported', 'reeds': 'wet'} (world-rules.md, section 2).
def _register_placements():
    import world_lint as _wl
    kinds = {'floating': _wl.FLOATING, 'wet': _wl.WET, 'supported': _wl.SUPPORTED}
    for mod in (gp, wp, vp, sp, cp, wsp, cdp, hbp, csp, spp, hp, fp, ip):
        for key, kind in getattr(mod, 'PLACEMENT', {}).items():
            assert kind in kinds, f'{mod.__name__}.PLACEMENT[{key!r}]: unknown kind {kind!r}'
            kinds[kind].add(key)


_register_placements()

BRASS, IRON, BRICK = (MATERIALS[k] for k in ('brass', 'iron', 'brick'))
IRONm, LEAFm = MATERIALS['iron'], MATERIALS['leaf']

W, H, CELL = 320, 576, 4
worlds.W, worlds.H = W, H  # the world painters read the canvas size from the module

# Exits: where a road leaves the zone, and the zone it leads to.
EXITS = {
    'north': {'to': 'garden', 'x': 160, 'y': 0},
    'east': {'to': 'park', 'x': W - 1, 'y': 300},
}
SQUARE = (160, 288)


def well() -> Canvas:
    """The town well, 32 x 40: a ring of dressed stones lit on the left, dark water
    inside, two posts and a little slate roof seen from above."""
    cv = Canvas(32, 40, pad=4)
    ring = oval(16, 31, 13, 7)
    inner = oval(16, 29.5, 9, 4.2)
    for (x, y) in ring:
        cv.set(x, y, STONE[3] if x < 16 else STONE[2])
    detail.stones(cv, 3, 27, 26, 10, STONE, seed=7, course=3)
    for (x, y) in list(ring):
        if (x, y) not in oval(16, 31, 13, 7):
            continue
        if y < 27:
            cv.set(x, y, STONE[4] if x < 16 else STONE[3])
    for (x, y) in inner:
        cv.set(x, y, '#2B3A4A' if y < 30 else '#3E5468')
    for px in (5, 25):
        gp.post(cv, px, 8, 30, w=3)
    cv.hline(6, 13, 20, WOOD[1])
    cv.vline(16, 13, 10, '#8C8574')
    cv.set(16, 23, STONE[1])
    roof = {(x, y) for y in range(2, 11) for x in range(2 + (10 - y) // 3, 30 - (10 - y) // 3)}
    detail.slate_plane(cv, {(x, y) for (x, y) in roof if x < 16}, SLATE, 3, 16, -1, course=3, tile=4, seed=3)
    detail.slate_plane(cv, {(x, y) for (x, y) in roof if x >= 16}, SLATE, 2, 16, 1, course=3, tile=4, seed=4)
    cv.hline(2, 10, 28, SLATE[0])
    return cv


def notice_board() -> Canvas:
    """A notice board on two posts, 30 x 34, with pinned papers."""
    cv = Canvas(30, 34, pad=4)
    for px in (4, 23):
        gp.post(cv, px, 6, 34, w=3)
    detail.boards(cv, {(x, y) for x in range(2, 28) for y in range(6, 22)}, WOOD, 2, 6, board=4, seed=5, vertical=True, x0=2)
    for (x0, y0, w, h, c) in ((5, 9, 7, 8, '#EFE3C8'), (14, 8, 6, 6, '#F3D9A0'), (21, 10, 5, 7, '#E2E9F0'), (13, 15, 7, 5, '#EFE3C8')):
        for y in range(y0, y0 + h):
            cv.hline(x0, y, w, c)
        cv.hline(x0, y0 + h, w, WOOD[0])
        cv.set(x0 + w // 2, y0, RED[3])
    cv.hline(1, 5, 28, WOOD[3])
    cv.hline(1, 4, 28, WOOD[4])
    return cv


def ring_fence(cv_objects: list, cx: int, cy: int, rx: int, ry: int):
    """Posts around the sparring ring, leaving an opening to the north path."""
    for k in range(20):
        a = 2 * math.pi * k / 20
        if abs(a - 1.5 * math.pi) < 0.35:
            continue
        cv_objects.append((f'ring-post-{k}', 'ring_post', int(cx + rx * math.cos(a)) - 3, int(cy + ry * math.sin(a)) - 14))


def ring_post() -> Canvas:
    cv = Canvas(8, 16, pad=2)
    gp.post(cv, 2, 2, 16, w=4)
    return cv


def paint_road(cv: Canvas, mask):
    """Sandy earth with the ragged turf edge, like worlds.paint_dirt, except that pixels
    beyond the top or bottom edge count as road: the road runs on into the next zone,
    so the border gets no turf edge and the two zones meet without a seam."""
    for (x, y) in mask:
        cv.set(x, y, P[4] if smooth_noise(x, y, 7, 40) > 0.7 else P[3])
    # a trodden road (art-style.md, detail target): bedded pebbles, small dark hollows
    # where rain stood, and a few lighter scuffs; sparse, so the way still reads clearly
    inside = [(x, y) for (x, y) in mask if 0 <= x < W and 0 <= y < H]
    for (x, y) in inside:
        n = noise2(x, y, 545)
        if n < 0.0035 and all((x + dx, y + dy) in mask for dx in (-2, 0, 3) for dy in (-1, 0, 3)):
            detail.pebble(cv, x, y, STONE, big=n < 0.0012)
        elif n > 0.994 and (x + 1, y) in mask and (x, y + 1) in mask:
            cv.set(x, y, P[2]); cv.set(x + 1, y, P[2]); cv.set(x, y - 1, P[1])
        elif 0.5 < n < 0.508 and (x + 2, y) in mask:
            cv.hline(x, y, 3, P[4])
    detail.grass_edge(cv, set(mask), G, P, seed=11)  # pixels past any edge count as road too
    for (x, y) in mask:
        if (x, y + 1) not in mask and 0 <= y + 1 < H:
            cv.set(x, y + 1, G[3])


def bunting() -> Canvas:
    """Bunting strung across the square for market day, 200 x 20: a sagging cord with
    little pennants in the town's colours, each lit on its left half."""
    w, h = 200, 20
    cv = Canvas(w, h, pad=2)
    cols = (RED, MATERIALS['gold'], MATERIALS['water'], MATERIALS['leaf'], MATERIALS['nap'])
    for x in range(w):
        y = 2 + int(math.sin(x / (w - 1) * math.pi) * 7)
        cv.set(x, y, WOOD[1])
        if x % 9 == 3 and 4 < x < w - 6:
            c = cols[(x // 9) % len(cols)]
            for t in range(6):
                for dx in range(-(3 - t // 2), 4 - t // 2):
                    cv.set(x + dx, y + 1 + t, c[3] if dx < 0 else c[2])
    return cv


def cat() -> Canvas:
    """The town cat asleep in the sun, 16 x 10, curled with its tail round its nose."""
    cv = Canvas(16, 10, pad=2)
    for (x, y) in oval(8, 6, 6.5, 3.6):
        cv.set(x, y, '#E8A04A' if (x - 8) + (y - 6) < -1 else '#C47A30' if x < 11 else '#9A5A22')
    for (x, y) in disc(4, 4, 2.4):
        cv.set(x, y, '#E8A04A' if x < 4 else '#C47A30')
    cv.set(3, 1, '#C47A30'); cv.set(5, 1, '#C47A30')
    cv.set(3, 4, '#5A3A1E'); cv.set(5, 4, '#5A3A1E')  # closed eyes
    for t in range(6):
        cv.set(9 + t, 9 - t // 3, '#9A5A22')
    for k in range(4):
        cv.set(6 + k * 2, 5, '#9A5A22')  # tabby stripes
    return cv


def pennant() -> Canvas:
    pole = Canvas(16, 34, pad=2)
    gp.post(pole, 1, 4, 34, w=3)
    for y in range(5, 14):
        for x in range(4, 4 + max(1, 12 - (y - 5))):
            pole.set(x, y, RED[3] if y < 9 else RED[2])
    pole.hline(4, 5, 11, RED[4])
    return pole


@functools.lru_cache(maxsize=1)
def sprites() -> dict[str, Canvas]:
    """Every zone sprite, finalized once (drawing is deterministic, so one copy serves all zones)."""
    items = wp.props()
    items.update({'stall': gp.stall(), 'signpost': gp.signpost(), 'well': well(),
                  'notice_board': notice_board(), 'ring_post': ring_post(), 'pennant': pennant(),
                  'bunting': bunting(), 'cat': cat()})
    items.update(vp.props())
    items.update(sp.props())
    items.update(cp.props())
    items.update(wsp.props())
    items.update(cdp.props())
    items.update(hbp.props())
    items.update(csp.props())
    items.update(spp.props())
    items.update(hp.props())
    items.update(fp.props())
    items.update(ip.props())
    items['fence_c'] = gp.fence_h(60)
    out = {key: style.finalize(sp, name=key) for key, sp in items.items()}
    for key, raw in items.items():  # the window panes of each building, in sprite pixels
        fin = out[key]
        panes = [(gx - fin.ox, gy - fin.oy, gw, gh) for (c, (gx, gy, gw, gh)) in gp.WINDOWS if c is raw]
        if panes:
            SPRITE_WINDOWS[key] = panes
    return out


# Window panes per sprite (filled by sprites()): lit warm at night where a zone has no light of its own.
SPRITE_WINDOWS: dict = {}


# Props with a way through them: (from, to) in sprite pixels.
OPENINGS = {'gatehouse': (50, 72), 'sandstone_arch': (20, 44), 'ticket_gates': (4, 80), 'moon_arch': (20, 44)}


def walk_grid(objects, sprite_map) -> list[str]:
    blocked = set()
    for (_id, key, x, y) in objects:
        sp = sprite_map[key]
        foot = 20 if sp.w > 60 else 10 if key in ('tree', 'tree_small', 'tree_autumn', 'pine') else 6
        gap = OPENINGS.get(key)
        for yy in range(y + sp.h - foot, y + sp.h):
            for xx in range(x + 3, x + sp.w - 3):
                if gap and x + gap[0] <= xx < x + gap[1]:
                    continue  # a gateway you walk through
                blocked.add((xx // CELL, yy // CELL))
    rows = []
    for r in range(H // CELL):
        row = ''
        for c in range(W // CELL):
            cx, cy = c * CELL + 2, r * CELL + 2
            row += '.' if (c, r) not in blocked else '#'  # borders stay open: neighbours join here
        rows.append(row)
    return rows


def reachable(walk: list[str], start) -> set:
    s = (start[1] // CELL, start[0] // CELL)
    seen, q = {s}, deque([s])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (r + dr, c + dc)
            if 0 <= n[0] < len(walk) and 0 <= n[1] < len(walk[0]) and n not in seen and walk[n[0]][n[1]] == '.':
                seen.add(n)
                q.append(n)
    return seen


def thick_from(points, radius, seed, dx, dy=0):
    """worlds.thick drawn in a neighbour's coordinates and shifted into this zone by
    (dx, dy): a road or bed that crosses a border continues pixel for pixel."""
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 9, seed) - 0.5) * (2.4 if seed else 0)
            pts |= disc(cx, cy, r)
    return {(x + dx, y + dy) for (x, y) in pts if 0 <= x + dx < W and 0 <= y + dy < H}


def paint_rails(cv: Canvas, y0: int, x_off: int = 0):
    """A railway across the zone: ballast, wooden sleepers lit on top, and two iron
    rails with a bright running edge. x_off is the zone's x in its neighbour's
    coordinates, so the sleepers keep their spacing across a border."""
    for y in range(y0 - 3, y0 + 16):
        for x in range(W):
            n = noise2(x + x_off, y, 141)
            cv.set(x, y, STONE[2] if n > 0.55 else STONE[1] if n > 0.15 else STONE[3])
    for x in range(1 + (-x_off) % 7 if x_off else 1, W, 7):
        for y in range(y0, y0 + 13):
            cv.set(x, y, WOOD[3] if y == y0 else WOOD[2]); cv.set(x + 1, y, WOOD[2]); cv.set(x + 2, y, WOOD[1])
            cv.set(x + 3, y, WOOD[1] if y > y0 else WOOD[2])
    for ry in (y0 + 2, y0 + 9):
        cv.hline(0, ry, W, IRON[4]); cv.hline(0, ry + 1, W, IRON[2]); cv.hline(0, ry + 2, W, IRON[0])


def light_pool(cv: Canvas, cx: int, cy: int, rx: int, ry: int, colour: str, skip=frozenset()):
    """Light thrown on the ground: three stepped rings blending toward the light's
    colour, dithered at their edges (pixel art, no smooth gradient)."""
    rgb = tuple(int(colour[k:k + 2], 16) for k in (1, 3, 5))
    for y in range(cy - ry - 1, cy + ry + 2):
        for x in range(cx - rx - 1, cx + rx + 2):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d >= 1:
                continue
            amt = 0.42 if d < 0.3 else 0.26 if d < 0.62 else 0.13
            if 0.25 < d < 0.35 or 0.57 < d < 0.67 or d > 0.92:
                if (x + y) % 2:
                    amt = {0.42: 0.26, 0.26: 0.13, 0.13: 0.0}[amt]
            if amt <= 0 or (x, y) in skip:
                continue
            c = cv.get(x, y)
            if c[3]:
                cv.set(x, y, tuple(int(c[i] + (rgb[i] - c[i]) * amt) for i in range(3)) + (255,))


def rain(prev: Canvas, seed: int = 0):
    """Rain over a preview: short slanted streaks, lighter toward the top."""
    for i in range(900):
        x, y = int(noise2(i, 0, 191 + seed) * W), int(noise2(i, 1, 191 + seed) * H)
        for t in range(4):
            c = prev.get(x - t // 2, y + t)
            if c[3]:
                prev.set(x - t // 2, y + t, tuple(min(255, v + 40) for v in c[:3]) + (255,))


def cracked(x: int, y: int, cell: int = 9, seed: int = 0) -> bool:
    """True on the cracks of dried mud: the edges of jittered cells (a Voronoi
    pattern), so the plates are irregular polygons rather than a grid."""
    best, second = 1e9, 1e9
    gx, gy = x // cell, y // cell
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            cx = (gx + i) * cell + noise2(gx + i, gy + j, 240 + seed) * cell
            cy = (gy + j) * cell + noise2(gx + i, gy + j, 241 + seed) * cell
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d < best:
                best, second = d, best
            elif d < second:
                second = d
    return math.sqrt(second) - math.sqrt(best) < 1.1


def rect_set_z(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def cp_hex(cv: Canvas, cx: int, cy: int, r: int):
    """A short basalt column drawn straight into the ground: a lit hexagonal top and a
    stub of shaded face below it."""
    import caldera_props as cpz
    BASALT = MATERIALS['basalt']
    for y in range(cy, cy + 6):
        for x in range(cx - r + 1, cx + r):
            cv.set(x, y, BASALT[2] if x < cx else BASALT[1])
    cpz.hex_top(cv, cx, cy, r)


FOREST_FLOOR = ['#24382A', '#40603A', '#577A44', '#668A4E', '#8EAE68']
DARK_FLOOR = [tuple(int(c[k:k + 2], 16) for k in (1, 3, 5)) for c in FOREST_FLOOR]


# Every region is its own place (Matt, 17 Oct: "not just reskins of other worlds"): a
# zone outside the valley draws only its own region's props, plus the few shared
# things below that would really be found anywhere.
REGION_PROPS = {'junction': sp.props, 'canal': sp.props, 'springs': cdp.props, 'home': hp.props, 'neon': cp.props, 'skyport': cp.props, 'gulch': wsp.props, 'oasis': wsp.props, 'caldera': cdp.props, 'harbour': hbp.props, 'hearthold': lambda: {**csp.props(), **cdp.props()}, 'scorch': lambda: {**wsp.props(), **cdp.props()},
                'station': spp.props_station, 'lumen': spp.props_lumen}
SHARED_PROPS = {'steam_puff', 'drone', 'ring_post', 'fence_c'}
# Things above head height: they cast no ground shadow, never block a walk, draw on top.
OVERHEAD = {'steam_puff', 'drone', 'bunting', 'cables', 'dragon'}
OVERHEAD |= {key for (key, *_rest) in cp.city_skybridges()}  # the city's decks, until they can be walked


@functools.lru_cache(maxsize=None)
def region_keys(name: str) -> frozenset:
    return frozenset(REGION_PROPS[name]())


# Ground dressing (level of detail, Matt 18 Oct): small things lying on each zone's open
# ground, in that ground's own palette and in keeping with the place. Drawn only where
# the open ground is untouched for a few pixels round (never on a path, in water, on a
# floor or under a prop's foot), on a jittered grid so it reads as scattered, not tiled.
SOOT = ['#2B3B2E', '#46583F', '#5C6E4C', '#6B7C55', '#8E9C6E']
ALPINE = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']


def _rgb(c):
    return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))


def _flower(cv, x, y, petal, centre):
    for (dx, dy) in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        cv.set(x + dx, y + dy, petal)
    cv.set(x, y, centre)
    cv.set(x, y + 2, '#447A50')


def _decal(cv, kind, x, y, r):
    """One small thing on the ground at (x, y); r in [0, 1) picks which."""
    if kind == 'meadow':
        if r < 0.3:
            _flower(cv, x, y, '#F7F2E8', '#F2D27A')  # a daisy
            if r < 0.15:
                _flower(cv, x + 3, y + 2, '#F7F2E8', '#F2D27A')
        elif r < 0.5:
            cv.set(x, y, '#F2D27A'); cv.set(x + 2, y + 1, '#E6BC5C'); cv.set(x + 1, y + 2, '#F2D27A')  # buttercups
            cv.set(x, y + 1, '#447A50'); cv.set(x + 2, y + 2, '#447A50')
        elif r < 0.65:
            for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                cv.set(x + dx, y + dy, '#E8A0BC' if (dx + dy) % 2 else '#C8708A')  # clover head
            cv.set(x, y + 2, '#5C7A44')
        elif r < 0.78:
            cv.set(x, y, '#9A8BC8'); cv.set(x, y + 1, '#7464A8'); cv.set(x + 1, y + 2, '#447A50')  # a bellflower
        else:
            detail.pebble(cv, x, y, STONE, big=r > 0.93)
    elif kind == 'forest':
        if r < 0.4:
            col = ('#C8803A', '#A85A2E', '#E2BC5E')[int(r * 30) % 3]  # fallen leaves
            cv.set(x, y, col); cv.set(x + 1, y, col); cv.set(x + 1, y + 1, '#5E3A24')
        elif r < 0.48:
            cv.hline(x - 1, y, 3, '#C2453A'); cv.set(x, y - 1, '#E86A5A'); cv.set(x, y + 1, '#E8DCC8')  # a toadstool
            cv.set(x - 1, y, '#F7F2E8')
        elif r < 0.6:
            cv.set(x, y, '#5E3D2E'); cv.set(x + 1, y, '#80573A')  # a pine cone
        elif r < 0.8:
            for t in range(4):
                cv.set(x + t, y + t // 2, '#5E3D2E')  # a twig
        else:
            cv.set(x, y, '#8DAE5A'); cv.set(x + 1, y - 1, '#B2CA78'); cv.set(x - 1, y - 1, '#7E9F50')  # a seedling
    elif kind == 'snow':
        SN, ST = MATERIALS['snow'], MATERIALS['stone']
        if r < 0.35:  # a bird's tracks across the snow
            for k in range(3):
                cv.set(x + k * 2, y + (k % 2), SN[0])
        elif r < 0.7:  # a rock's tip through the snow, snow on its top
            cv.set(x, y, ST[2]); cv.set(x + 1, y, ST[1]); cv.set(x, y - 1, SN[3]); cv.set(x + 1, y - 1, SN[3])
        else:  # a twig blown up from below
            cv.hline(x, y, 3, WOOD[1]); cv.set(x + 1, y - 1, WOOD[2])
    elif kind == 'alpine':
        if r < 0.35:
            cv.set(x, y, '#5A8AD0'); cv.set(x + 1, y, '#3E6AA8'); cv.set(x, y + 1, '#4F7A5A')  # gentians
            cv.set(x + 3, y + 1, '#5A8AD0')
        elif r < 0.6:
            _flower(cv, x, y, '#F7FAFC', '#E8D8B8')  # edelweiss
        else:
            detail.pebble(cv, x, y, STONE, big=r > 0.85)
    elif kind == 'soot':
        if r < 0.4:
            cv.set(x, y, '#1E1C22'); cv.set(x + 1, y, '#3A3840'); cv.set(x + 2, y + 1, '#1E1C22')  # coal crumbs
        elif r < 0.6:
            cv.set(x, y, '#9E6C26'); cv.set(x, y + 1, '#6E4718')  # a lost brass bolt
        else:
            detail.grass_tuft(cv, x, y, int(r * 60) % 6, SOOT, 2)
    elif kind == 'desert':
        D = MATERIALS['desert']
        if r < 0.35:
            detail.pebble(cv, x, y, MATERIALS['adobe'], big=r > 0.25)
        elif r < 0.6:
            for (dx, h) in ((0, 3), (2, 4), (4, 2)):
                cv.vline(x + dx, y - h, h, '#B89A58' if dx else '#9A8044')  # dry grass
        elif r < 0.75:
            for k in range(3):
                cv.set(x + k * 3, y + (k % 2), D[1])  # tracks
        else:
            cv.set(x, y, D[5]); cv.set(x + 1, y, D[4])  # a pale chip of stone
    elif kind == 'ash':
        A, L = MATERIALS['basalt'], MATERIALS['lava']
        if r < 0.3:
            cv.set(x, y, L[3]); cv.set(x + 1, y, L[1])  # a cinder still glowing
        elif r < 0.75:
            detail.pebble(cv, x, y, A, big=r > 0.6)
        else:
            cv.set(x, y, '#D86AA2'); cv.set(x, y + 1, '#447A50')  # a fireweed seedling
    elif kind == 'street':
        N = MATERIALS['night']
        if r < 0.3:
            col = ('#E8429A', '#1FB5D0', '#E8962A')[int(r * 30) % 3]  # a crushed can
            cv.hline(x, y, 2, col); cv.set(x + 1, y, '#D2FBFF'); cv.hline(x, y + 1, 2, N[0])
        elif r < 0.55:
            cv.hline(x, y, 3, '#B8B4C8'); cv.set(x + 1, y + 1, '#8E8AA0')  # a paper flyer
        elif r < 0.8:
            cv.set(x, y, '#6FE6F2'); cv.set(x + 1, y, N[1])  # a glint in a puddle
        else:
            cv.set(x, y, N[0]); cv.set(x + 1, y + 1, N[0])  # gum and grime
    elif kind == 'regolith':
        R = MATERIALS['regolith']
        if r < 0.45:
            for (dx, dy, c) in ((-1, 0, R[1]), (1, 0, R[4]), (0, -1, R[1]), (0, 1, R[4])):
                cv.set(x + dx, y + dy, c)  # a tiny crater
        else:
            cv.set(x, y, R[5]); cv.set(x + 1, y, R[3])
            for t in range(1, 4):
                cv.set(x + 1 + t, y + 1, R[0])  # a pebble with its long airless shadow


DRESS = {
    'town': ('meadow', G[2:4], 0.32), 'park': ('meadow', G[2:4], 0.4), 'riverside': ('meadow', G[2:4], 0.4),
    'halt': ('meadow', G[2:4], 0.3), 'harbour': ('meadow', G[2:4], 0.3), 'headland': ('meadow', G[2:4], 0.4),
    'hearthold': ('ash', MATERIALS['ash'][1:3], 0.26), 'scorch': ('ash', MATERIALS['ash'][1:3], 0.22),
    'woodland': ('forest', None, 0.26), 'ridge': ('alpine', ALPINE[2:4], 0.32),
    'hollow': ('alpine', ALPINE[2:4], 0.3), 'snowmelt': ('snow', MATERIALS['snow'][1:4], 0.2),
    'saddle': ('snow', MATERIALS['snow'][1:4], 0.22), 'summit': ('snow', MATERIALS['snow'][1:4], 0.16),
    # (the isles' entries are added by isle_zones.py)
    'junction': ('soot', SOOT[2:4], 0.3), 'canal': ('soot', SOOT[2:4], 0.3),
    'gulch': ('desert', MATERIALS['desert'][2:5], 0.22), 'oasis': ('desert', MATERIALS['desert'][2:5], 0.16),
    'caldera': ('ash', MATERIALS['ash'][1:3], 0.3), 'springs': ('ash', MATERIALS['ash'][1:3], 0.3),
    'neon': ('street', MATERIALS['night'][1:4], 0.18), 'lumen': ('regolith', MATERIALS['regolith'][2:4], 0.3),
}


def dress(cv: Canvas, name: str, objects, sprite_map, blocked):
    if name not in DRESS:
        return
    kind, palette, density = DRESS[name]
    if kind == 'forest':
        palette = FOREST_FLOOR[1:4]
    ok = {_rgb(c) for c in palette}
    feet = set()
    for (_i, key, x, y) in objects:
        if key in OVERHEAD:
            continue
        sp = sprite_map[key]
        feet |= {(xx, yy) for xx in range(x - 4, x + sp.w + 4) for yy in range(y + sp.h - 24, y + sp.h + 6)}
    for ty in range(4, H - 4, 7):
        for tx in range(4, W - 6, 7):
            x, y = tx + int(noise2(tx, ty, 540) * 5), ty + int(noise2(tx, ty, 541) * 5)
            r = noise2(tx, ty, 542)
            # in drifts and patches rather than evenly: denser where a slow noise is high
            if r > density * (0.15 + 1.5 * max(0.0, smooth_noise(tx, ty, 46, 544) - 0.25)):
                continue
            if (x, y) in feet or (x, y) in blocked:
                continue
            if not all(cv.get(x + dx, y + dy)[:3] in ok for dx in (-2, 0, 2, 4) for dy in (-2, 0, 2)):
                continue
            _decal(cv, kind, x, y, noise2(tx, ty, 543))


def share_feet(built: dict):
    """A prop whose foot reaches over a side border closes the ground under it in the
    neighbouring zone too, so nothing can walk through the part of it across the line."""
    for region, zs in LAYOUT.items():
        at = {pos: z for z, pos in zs.items()}
        for z, (col, row) in zs.items():
            if z not in built:
                continue
            for side, dc in (('west', -1), ('east', 1)):
                other = at.get((col + dc, row))
                if other not in built:
                    continue
                shifted = []
                for (oid, key, x, y) in built[z]['objects']:
                    if key in OVERHEAD:
                        continue
                    sp = built[z]['sprites'][key]
                    if (dc < 0 and x + 3 < 0) or (dc > 0 and x + sp.w - 3 > W):
                        shifted.append((oid, key, x - dc * W, y))
                if not shifted:
                    continue
                extra = walk_grid(shifted, built[z]['sprites'])
                walk = built[other]['walk']
                built[other]['walk'] = [''.join('#' if e == '#' else ch for ch, e in zip(row_w, row_e))
                                        for row_w, row_e in zip(walk, extra)]


def check_overhangs(built: dict):
    """A tall prop that rises over a zone's north border must rise over empty ground in
    the zone behind it (no prop there for its top to cover)."""
    for region, zs in LAYOUT.items():
        at = {pos: z for z, pos in zs.items()}
        for z, (col, row) in zs.items():
            behind = at.get((col, row - 1))
            if z not in built or behind not in built:
                continue
            for (oid, key, x, y) in built[z]['objects']:
                sp = built[z]['sprites'][key]
                if y >= 0 or key in OVERHEAD:
                    continue
                top = H + y  # the overhang, in the zone behind
                for (oid2, key2, x2, y2) in built[behind]['objects']:
                    sp2 = built[behind]['sprites'][key2]
                    if key2 in OVERHEAD:
                        continue
                    assert not (x < x2 + sp2.w and x + sp.w > x2 and top < y2 + sp2.h), \
                        f'{z}/{oid} rises over {behind}/{oid2}'


def build(name: str, fn, start: str):
    sprite_map = sprites()
    cv, objects, stands, *rest = fn()
    blocked_ground = rest[0] if rest else set()
    # an upper walk level (docs/vision/two-level-walk.md): {'walk': pixels of the deck's
    # surface in the coordinates of the ground it stands over, 'height': px it is drawn
    # raised by, 'connectors': [{'kind', 'bottom': (x, y), 'top': (x, y)}]}
    deck = rest[1] if len(rest) > 1 else None
    if name in REGION_PROPS:
        own = region_keys(name) | SHARED_PROPS
        foreign = sorted({k for (_i, k, _x, _y) in objects} - own)
        assert not foreign, f'{name} borrows props from another region: {foreign}'
    objects = [(i, k, x + sprite_map[k].ox, y + sprite_map[k].oy) for (i, k, x, y) in objects]
    # the borders this zone shares are closed except at their ports (frames.py): drawn
    # over ground that was open, before the ground is dressed
    import frames
    import world_lint
    pre = walk_grid([o for o in objects if o[1] not in OVERHEAD], sprite_map)
    pre_cells = {(x // CELL, y // CELL) for (x, y) in blocked_ground}
    pre = [''.join('#' if (c, r) in pre_cells else ch for c, ch in enumerate(row)) for r, row in enumerate(pre)]
    wet = WATER_MASKS.get(fn.__name__) or set()

    def is_water(x, y):
        if fn.__name__ in WATER_MASKS:  # (night palettes: the zone declares its water)
            return (x, y) in wet
        px = cv.get(x, y)[:3]
        return world_lint._bluish(*px) or world_lint._lava(*px)

    blocked_ground = set(blocked_ground) | frames.apply(cv, name, LAYOUT, pre, is_water)
    allowed = (region_keys(name) | SHARED_PROPS) if name in REGION_PROPS else None
    objects = objects + frames.place(name, LAYOUT, sprite_map, allowed, objects, stands, pre, is_water)
    dress(cv, name, objects, sprite_map, blocked_ground)
    shade = set()
    for (_id, key, x, y) in objects:
        if key not in OVERHEAD:
            shade |= detail.silhouette_shadow(sprite_map[key], x, y)
    for (sx, sy) in shade:
        style.darken(cv, sx, sy)
    walk = walk_grid([o for o in objects if o[1] not in OVERHEAD], sprite_map)
    cells = {(x // CELL, y // CELL) for (x, y) in blocked_ground}
    # keep a step back from lava at the sides: the companion's body is wider than its
    # feet, so feet in the cell beside a lava cell would stand it in the glow
    # (a bridge's deck is never lava-coloured, so the way over it stays open)
    import world_lint
    hot = {(c, r) for (c, r) in cells if world_lint._lava(*cv.get(c * CELL + 2, r * CELL + 2)[:3])}
    cells |= {(c + d, r) for (c, r) in hot for d in (-1, 1) if 0 <= c + d < W // CELL}
    walk = [''.join('#' if (c, r) in cells else ch for c, ch in enumerate(row)) for r, row in enumerate(walk)]
    seen = reachable(walk, stands[start])
    lost = [k for k, (x, y) in stands.items() if (y // CELL, x // CELL) not in seen]
    assert not lost, f'{name}: not reachable on foot from {start}: {lost}'
    # every door can be walked up to: the ground just in front of it is open and
    # reachable (nothing parked or planted in front of a door)
    shut = []
    for (oid, key, x, y) in objects:
        if key not in DOORS:
            continue
        sp = sprite_map[key]
        dx = x + int(sp.w * DOORS[key])
        front = [(dx // CELL + d, (y + sp.h + k) // CELL) for d in (-1, 0, 1) for k in (2, 6)]
        if not any((r, c) in seen for (c, r) in front):
            shut.append(oid)
        foot = y + sp.h
        for (oid2, key2, x2, y2) in objects:  # and nothing stands in front of it, hiding it
            sp2 = sprite_map[key2]
            if oid2 == oid or key2 in OVERHEAD or y2 + sp2.h <= foot:
                continue
            if x2 + 3 < dx + 6 and x2 + sp2.w - 3 > dx - 6 and y2 < foot and y2 + sp2.h > foot - 16:
                shut.append(f'{oid} (hidden by {oid2})')
    assert not shut, f'{name}: nothing can reach the door of {shut}'
    # A prop may reach across a border into a neighbouring zone (Matt, 19 Oct: "the world
    # does not need to be divided into screen sized sections"): it belongs to the zone its
    # foot stands in, and share_feet() closes the ground under its foot on the other side.
    # (The renderer mounts every tile near the screen, so the reach always draws.)
    region = next(r for r, zs in LAYOUT.items() if name in zs)
    col, row = LAYOUT[region][name]
    near = set(LAYOUT[region].values())
    over = []
    for (oid, key, x, y) in objects:
        if key in OVERHEAD:
            continue
        sp = sprite_map[key]
        fx, fy = x + sp.w // 2, y + sp.h - 2
        dc = -1 if fx < 0 else 1 if fx >= W else 0
        dr = -1 if fy < 0 else 1 if fy >= H else 0
        if (dc or dr) and (col + dc, row + dr) in near:
            over.append(f'{oid}: its foot ({fx},{fy}) stands in the neighbouring zone')
    assert not over, f'{name}: {over}'
    out = os.path.join(worlds.ROOT, 'assets', 'zones', name)
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, 'ground.png'), worlds.SCALE)
    GROUND_TONE[name] = ground_tone(cv)
    if name == 'town':
        # the lane past the garden gate, drawn below the garden screen's fence, so the
        # garden's south edge shows the valley going on (components/garden-world.tsx)
        strip = Canvas(W, 64)
        strip.paste(cv, 0, 0)
        for (_id, key, x, y) in sorted(objects, key=lambda o: o[3] + sprite_map[o[1]].h):
            if key not in OVERHEAD and y < 64:
                strip.paste(sprite_map[key], x, y)
        strip.save(os.path.join(out, 'top.png'), worlds.SCALE)
    preview = os.environ.get('ZONE_PREVIEW')
    prev = None
    if preview or os.environ.get('LINT_OUT'):
        prev = Canvas(W, H)
        prev.paste(cv, 0, 0)
        for (_id, key, x, y) in sorted(objects, key=lambda o: o[3] + sprite_map[o[1]].h + (900 if o[1] in OVERHEAD else 0)):
            prev.paste(sprite_map[key], x, y)
        if name == 'neon':
            rain(prev)
        if preview:
            prev.save(os.path.join(preview, f'zone-{name}.png'), 2)
    print('ok zone', name, W, H)
    if deck:
        deck = deck_grid(name, deck, walk)
    return {'objects': objects, 'walk': walk, 'stands': stands, 'sprites': sprite_map, 'deck': deck,
            'ground_img': cv.img.copy(), 'blocked': blocked_ground, 'preview': prev.img if prev else None,
            'water': WATER_MASKS.get(fn.__name__)}


def deck_grid(name: str, deck: dict, ground_walk: list) -> dict:
    """A zone's deck as walk rows (a cell is open where most of its pixels are deck), its
    height and its connectors, checked: every connector's bottom stands on open ground,
    its top on the deck, and every open deck cell is reached from a connector's top."""
    surface = deck['walk']
    rows = []
    for cy in range(H // CELL):
        row = ''
        for cx in range(W // CELL):
            n = sum((cx * CELL + dx, cy * CELL + dy) in surface for dx in range(CELL) for dy in range(CELL))
            row += '.' if n * 2 > CELL * CELL else '#'
        rows.append(row)
    conns = deck.get('connectors', [])
    assert conns, f'{name}: a deck needs at least one stair, ramp or lift'
    for c in conns:
        assert c['kind'] in ('stair', 'ramp', 'lift'), f'{name}: unknown connector {c}'
        bx, by = c['bottom']
        tx, ty = c['top']
        assert ground_walk[by // CELL][bx // CELL] == '.', f'{name}: a {c["kind"]} starts on blocked ground at {c["bottom"]}'
        assert rows[ty // CELL][tx // CELL] == '.', f'{name}: a {c["kind"]} lands off the deck at {c["top"]}'
    seen = set()
    for c in conns:
        tx, ty = c['top']
        seen |= reachable(rows, (tx, ty))
    stranded = [(cx, cy) for cy, row in enumerate(rows) for cx, ch in enumerate(row) if ch == '.' and (cy, cx) not in seen]
    assert not stranded, f'{name}: {len(stranded)} deck cells reached by no stair or lift (first {stranded[:3]})'
    return {'walk': rows, 'height': int(deck['height']),
            'connectors': [{'kind': c['kind'], 'bottom': list(c['bottom']), 'top': list(c['top'])} for c in conns]}


# Buildings whose door faces the viewer, and where the door sits across the sprite
# (a fraction of its width).
DOORS = {k: 0.5 for k in ('house_blue', 'house_red', 'cabin', 'cafe', 'library', 'workshop', 'workshop_round',
                          'station_house', 'barn', 'bathhouse', 'foundry', 'tube_station', 'cottage', 'cottage_b',
                          'saloon', 'store', 'mine_portal', 'clock_tower', 'lookout_tower')}
DOORS.update({'cottage_c': 0.5, 'cottage_d': 0.4})  # Claude B's B6 (#45): cottage_d's door is off-centre


# Where each zone sits on its region's grid (column, row), in zone-sized steps. The
# garden is the valley's (0, 0); it is drawn by garden.py and joins here by position.
LAYOUT = {
    'valley': {'ridge': (0, -1), 'woodland': (-1, 0), 'garden': (0, 0), 'riverside': (1, 0), 'town': (0, 1), 'park': (1, 1),
               'harbour': (0, 2), 'headland': (1, 2), 'halt': (-1, 1),
               # the Frostline Highlands above the ridge (Matt, 18 Oct 19:07)
               'hollow': (-1, -1), 'snowmelt': (-1, -2), 'saddle': (0, -2), 'summit': (0, -3)},
    'steam': {'junction': (0, 0), 'canal': (0, 1)}, 
    # Sunstone Reach (Matt, 18 Oct 19:07: the world Codex drew): the desert and the fire
    # country are one walk, the Scorched Pass east of Dust Gulch climbing to Hearthold
    'west': {'gulch': (0, 0), 'oasis': (-1, 0), 'scorch': (1, 0), 'hearthold': (1, -1),
             'caldera': (1, -2), 'springs': (2, -2)},
    # the Tidebloom Isles, by ferry from Driftwood's jetty (Matt, 18 Oct 19:07)
    'isles': {'rainforest': (0, 0), 'headwaters': (1, 0), 'landing': (0, 1), 'cove': (1, 1)},
    # the city (N1, Claude C): the old core and the Skyport keep their cells on the coast,
    # the rest grows inland and along the east quay (city_zones.py)
    'neon': {'neon': (0, 0), 'skyport': (1, 0), 'point': (2, 0), 'market': (0, -1), 'downtown': (1, -1),
             'docks': (2, -1), 'heights': (0, -2), 'plaza': (1, -2), 'waterfront': (2, -2)}, 'space': {'station': (0, 0)}, 'moon': {'lumen': (0, 0)}, 'home': {'home': (0, 0)},
}


def rle(row: str) -> str:
    out, i = [], 0
    while i < len(row):
        j = i
        while j < len(row) and row[j] == row[i]:
            j += 1
        out.append(f'{j - i}{row[i]}')
        i = j
    return ''.join(out)


# Water a zone declares outright (world-rules.md, section 1: the semantic layer), for
# zones whose night palettes the lint cannot read by colour; others are read by colour.
WATER_MASKS: dict[str, set] = {}

BEYOND_SPILL = 20  # how far the forest's crowns spill over the zones beside it


@functools.lru_cache(maxsize=1)
def beyond() -> Canvas:
    """What lies past a region's own zones where its grid has a gap (the valley's corners):
    old forest, a closed canopy of leaf masses in deep shade, each row overlapping the
    one behind it. Its outermost crowns spill a little over the neighbouring zones, so
    the forest's edge is grown, not cut; the canvas is the zone plus that spill all round."""
    S = BEYOND_SPILL
    cv = Canvas(W + 2 * S, H + 2 * S)
    for y in range(S, H + S):
        for x in range(S, W + S):
            # the shade under the canopy, its edge ragged so no straight line shows
            m = 2 + int(noise2(x // 3, y // 3, 553) * 7)
            if min(x - S, W + S - 1 - x, y - S, H + S - 1 - y) < m:
                continue
            cv.set(x, y, style.FOREST_DARK if (x + y) % 2 else '#24382A')
    ramp = ['#122019', '#1A2C22', '#22392A', '#2E4C34', '#3E6240']
    crowns = []
    k = 0
    for gy in range(S + 4, H + S, 30):  # crowns on a jittered grid, so the canopy closes
        for gx in range(S + 6, W + S, 40):
            crowns.append((gy + (noise2(k, 1, 552) - 0.5) * 22, gx + (noise2(k, 0, 552) - 0.5) * 28,
                           22 + noise2(k, 2, 552) * 12, k))
            k += 1
    for t in range(0, max(W, H) + 1, 22):  # small crowns straddling the edge all round
        for (ex, ey) in ((S + t, S), (S + t, H + S), (S, S + t), (W + S, S + t)):
            if S <= ex <= W + S and S <= ey <= H + S:
                crowns.append((ey + (noise2(t, ex, 554) - 0.5) * 6, ex + (noise2(t, ey, 554) - 0.5) * 6,
                               9 + noise2(ex, ey, 555) * 4, k))
                k += 1
    for (cy, cx, rx, k) in sorted(crowns):
        # crowns by the edge stay inside the canvas, so the spill ends in round crowns
        rx = max(8.0, min(rx, cx - 8, cv.w - cx - 8, (cy - 8) / 0.72, (cv.h - cy - 8) / 0.72))
        ry = rx * 0.72
        blob = Canvas(int(rx * 2) + 14, int(ry * 2) + 14)
        style.leafy(blob, blob.w / 2, blob.h / 2, rx, ry, ramp, r=3.8, seed=k + 3)
        bx, by = int(cx - blob.w / 2), int(cy - blob.h / 2)
        for yy in range(blob.h):
            for xx in range(blob.w):
                c = blob.get(xx, yy)
                X, Y = bx + xx, by + yy
                if c[3] and 0 <= X < cv.w and 0 <= Y < cv.h:
                    cv.set(X, Y, c)
    return cv


WTR_ = MATERIALS['water']


def beyond_sea() -> Canvas:
    """What lies round the Tidebloom Isles: open sea, deep blue with long swells and
    the odd whitecap. It fills its own cell only: the islands' coasts meet it with
    their own surf."""
    S = BEYOND_SPILL
    cv = Canvas(W + 2 * S, H + 2 * S)
    for y in range(S, H + S):
        for x in range(S, W + S):
            n = smooth_noise(x, y, 40, 861)
            c = WTR_[0] if n > 0.55 else WTR_[1]
            swell = (y + int(math.sin(x / 23) * 4 + smooth_noise(x, y, 60, 862) * 8)) % 19
            if swell == 0:
                c = WTR_[2]
            elif swell == 1 and noise2(x // 5, y // 19, 863) > 0.8:
                c = '#F4F8F8'  # a whitecap
            cv.set(x, y, c)
    return cv


@functools.lru_cache(maxsize=1)
def beyond_peaks() -> Canvas:
    """What lies past the Frostline's zones: the high peaks themselves, steep snow with
    rock ribs down the fall line and crags breaking through, their edge spilling snowy
    boulders over the zones beside them (as the forest's crowns do lower down)."""
    S = BEYOND_SPILL
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W + 2 * S, H + 2 * S)
    for y in range(S, H + S):
        for x in range(S, W + S):
            m = 2 + int(noise2(x // 3, y // 3, 851) * 7)
            if min(x - S, W + S - 1 - x, y - S, H + S - 1 - y) < m:
                continue
            cv.set(x, y, high_slope_px(x, y))
    for i in range(14):  # crags: dark rock standing out of the snow, lit on the west
        cx, cy = S + 20 + int(noise2(i, 0, 852) * (W - 40)), S + 20 + int(noise2(i, 1, 852) * (H - 40))
        style.facet_stone(cv, oval(cx, cy, 9 + noise2(i, 2, 852) * 8, 6 + noise2(i, 3, 852) * 5), ST, seed=860 + i, outline=None)
        for (x, y) in oval(cx - 2, cy - 5, 6, 2):
            cv.set(x, y, SN[3])
    for t in range(0, max(W, H) + 1, 18):  # snowy boulders straddling the edge all round
        for (ex, ey) in ((S + t, S), (S + t, H + S), (S, S + t), (W + S, S + t)):
            if S <= ex <= W + S and S <= ey <= H + S:
                r = 6 + noise2(ex, ey, 853) * 5
                for (x, y) in disc(ex + (noise2(t, ex, 854) - 0.5) * 6, ey + (noise2(t, ey, 854) - 0.5) * 6, r):
                    if 0 <= x < cv.w and 0 <= y < cv.h:
                        dx, dy = x - ex, y - ey
                        cv.set(x, y, SN[3] if dy < -r * 0.3 else ST[3] if dx + dy < 0 else ST[1])
    return cv


GROUND_TONE: dict = {}


def ground_tone(cv) -> str:
    """The colour most of a zone's ground is, which the renderer lays under the ground's
    picture: if a phone drops the decoded picture (iOS Safari does under memory pressure)
    or it has not loaded yet, the place still shows its own ground rather than the
    region's backdrop (fault 30)."""
    count = {}
    for y in range(0, H, 4):
        for x in range(0, W, 4):
            c = cv.get(x, y)[:3]
            count[c] = count.get(c, 0) + 1
    r, g_, b = max(count, key=count.get)
    return f'#{r:02X}{g_:02X}{b:02X}'


def export(built: dict):
    """Write the props every zone uses and lib/zone-maps.ts (objects, walk grids,
    stands, the region layout and static image imports)."""
    props_dir = os.path.join(worlds.ROOT, 'assets', 'zones', 'props')
    os.makedirs(props_dir, exist_ok=True)
    for old in os.listdir(props_dir):
        os.remove(os.path.join(props_dir, old))
    beyond().save(os.path.join(worlds.ROOT, 'assets', 'zones', 'beyond.png'), worlds.SCALE)
    beyond_ash().save(os.path.join(worlds.ROOT, 'assets', 'zones', 'beyond-ash.png'), worlds.SCALE)
    beyond_dunes().save(os.path.join(worlds.ROOT, 'assets', 'zones', 'beyond-dunes.png'), worlds.SCALE)
    beyond_peaks().save(os.path.join(worlds.ROOT, 'assets', 'zones', 'beyond-peaks.png'), worlds.SCALE)
    beyond_sea().save(os.path.join(worlds.ROOT, 'assets', 'zones', 'beyond-sea.png'), worlds.SCALE)
    beyond_regolith().save(os.path.join(worlds.ROOT, 'assets', 'zones', 'beyond-regolith.png'), worlds.SCALE)
    # the land past the walkable world, cell by cell (scenery.py; art-faults.md rule 13)
    import scenery
    scen_dir = os.path.join(worlds.ROOT, 'assets', 'zones', 'scenery')
    os.makedirs(scen_dir, exist_ok=True)
    for old in os.listdir(scen_dir):
        os.remove(os.path.join(scen_dir, old))
    scenery_keys = []
    for region in LAYOUT:
        for (c, r), cv in sorted(scenery.cells(LAYOUT[region], region).items()):
            name = f'{region}_{c}_{r}'.replace('-', 'm')
            cv.save(os.path.join(scen_dir, f'{name}.png'), worlds.SCALE)
            scenery_keys.append((f'{region}:{c}:{r}', name))
    used = {}
    for z in built.values():
        for (_i, k, _x, _y) in z['objects']:
            used[k] = z['sprites'][k]
    # animation frames of a placed sprite ('windmill_f1', ...), placed relative to it
    frames = {}
    for key in sorted(used):
        sm = next(z['sprites'] for z in built.values())
        base = sm[key]
        n = 1
        while f'{key}_f{n}' in sm:
            fr = sm[f'{key}_f{n}']
            frames.setdefault(key, []).append([f'{key}_f{n}', fr.ox - base.ox, fr.oy - base.oy, fr.w, fr.h])
            n += 1
    for key, fl in frames.items():
        for (fk, *_r) in fl:
            used[fk] = next(z['sprites'] for z in built.values())[fk]
    for key, sp in sorted(used.items()):
        sp.save(os.path.join(props_dir, f'{key}.png'), worlds.SCALE)
    ident = lambda k: ''.join(p.capitalize() for p in k.split('_'))  # noqa: E731
    lines = [
        '// Generated by scripts/art/zones.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const ZONE = {{ width: {W}, height: {H}, cell: {CELL}, scale: {worlds.SCALE} }} as const;',
        f'export const zoneIds = {json.dumps(list(built))} as const;',
        'export type ZoneId = (typeof zoneIds)[number];',
        '/** [id, sprite, x, y, w, h] in zone pixels; drawn in order of their feet (y + h). */',
        'export type ZoneObject = readonly [string, string, number, number, number, number];',
        'export type ZoneMap = { objects: readonly ZoneObject[]; walk: readonly string[]; stands: Readonly<Record<string, readonly [number, number]>> };',
        '/** Things above head height: no ground shadow, never block a walk, drawn on top. */',
        f'export const zoneOverhead: readonly string[] = {json.dumps(sorted(OVERHEAD))};',
        '/** Animation frames of a sprite: [frame sprite, dx, dy, w, h] from the sprite\'s own top-left. */',
        f'export const zoneFrames: Record<string, readonly (readonly [string, number, number, number, number])[]> = {json.dumps(frames)};',
        '/** Window panes [x, y, w, h] in sprite pixels, lit warm at night. */',
        f'export const zoneWindows: Record<string, readonly (readonly [number, number, number, number])[]> = {json.dumps({k: [list(r) for r in v] for k, v in sorted(SPRITE_WINDOWS.items()) if k in used})};',
        '/** Walk rows are run-length encoded (\'12.3#\' = twelve open cells, three blocked). */',
        'const unrle = (row: string) => row.replace(/(\\d+)([.#])/g, (_m, n: string, c: string) => c.repeat(Number(n)));',
        'export const zoneMaps: Record<ZoneId, ZoneMap> = {',
    ]
    for zid, z in built.items():
        objs = ', '.join(json.dumps([i, k, x, y, z['sprites'][k].w, z['sprites'][k].h]) for (i, k, x, y) in z['objects'])
        lines.append(f'  {zid}: {{')
        lines.append(f'    objects: [{objs}],')
        lines.append(f"    walk: {json.dumps([rle(r) for r in z['walk']])}.map(unrle),")
        lines.append(f"    stands: {json.dumps({k: list(v) for k, v in z['stands'].items()})},")
        lines.append('  },')
    decks = {zid: z['deck'] for zid, z in built.items() if z.get('deck')}
    import world_lint
    placement = {k: t for t, ks in (('floating', world_lint.FLOATING), ('wet', world_lint.WET),
                                     ('supported', world_lint.SUPPORTED), ('overhead', OVERHEAD)) for k in sorted(ks) if k in used}
    lines += [
        '};',
        '/** A zone\'s upper walk level (docs/vision/two-level-walk.md): its walk rows in the coordinates of the',
        ' *  ground it stands over, how high it is drawn above that ground, and the stairs, ramps and lifts',
        ' *  joining it to the ground (bottom on the ground\'s walk, top on the deck\'s). */',
        'export type ZoneDeck = {',
        '  height: number;',
        '  walk: readonly string[];',
        "  connectors: readonly { kind: 'stair' | 'ramp' | 'lift'; bottom: readonly [number, number]; top: readonly [number, number] }[];",
        '};',
        'export const zoneDecks: Partial<Record<ZoneId, ZoneDeck>> = {',
        *[f"  {zid}: {{ height: {d['height']}, walk: {json.dumps([rle(r) for r in d['walk']])}.map(unrle), connectors: {json.dumps(d['connectors'])} }}," for zid, d in decks.items()],
        '};',
        '/** What each walk cell of a zone is (docs/vision/world-rules.md, section 1): \'~\' water, \'!\' lava,',
        ' *  \'^\' wall or cliff, \'=\' path, \'.\' ground. Rows are run-length encoded like the walk rows. */',
        'const unrleTerrain = (row: string) => row.replace(/(\\d+)([~!^=.])/g, (_m, n: string, c: string) => c.repeat(Number(n)));',
        'export const zoneTerrain: Record<ZoneId, readonly string[]> = {',
        *[f"  {zid}: {json.dumps([rle(r) for r in z['terrain']])}.map(unrleTerrain)," for zid, z in built.items()],
        '};',
        '/** How a prop meets the ground (world-rules.md, section 2); any sprite not listed stands on plain ground. */',
        f'export const zonePlacement: Record<string, \'floating\' | \'wet\' | \'supported\' | \'overhead\'> = {json.dumps(placement)};',
        '/** Each region\'s zones on a grid of zone-sized steps; the garden is the valley\'s (0, 0). */',
        f'export const regionLayout = {json.dumps({r: {z: list(p) for z, p in zs.items()} for r, zs in LAYOUT.items()})} as const;',
        '/** Where neighbouring zones meet (scripts/art/frames.py, Codex\'s connected-world contract): for each',
        ' *  shared edge, "west|east" or "north|south", the open span along it in art px; null = closed throughout. */',
        f'export const zoneTone: Record<string, string> = {json.dumps({**{z: GROUND_TONE[z] for z in built if z in GROUND_TONE}, 'garden': __import__('ground').MEADOW[2]})};',
        f'export const zonePorts: Record<string, {{ span: readonly [number, number] | null; frame: string }}> = {json.dumps(__import__("frames").export())};',
        '',
    ]
    assets = [
        '// Generated by scripts/art/zones.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        "import type { ZoneId } from './zone-maps';",
        *[f"import prop{ident(k)} from '@/assets/zones/props/{k}.png';" for k in sorted(used)],
        *[f"import ground{ident(z)} from '@/assets/zones/{z}/ground.png';" for z in built],
        'export const zoneGrounds: Record<ZoneId, ImageSourcePropType> = {',
        *[f'  {z}: ground{ident(z)},' for z in built],
        '};',
        *[f"import map{ident(z)} from '@/assets/zones/{z}/map.png';" for z in [*built, 'garden']],
        '/** Each zone drawn small as a paper map (scripts/art/map_tiles.py), 40 x 72 art pixels. */',
        'export const zoneMapTiles: Record<ZoneId | \'garden\', ImageSourcePropType> = {',
        *[f'  {z}: map{ident(z)},' for z in [*built, 'garden']],
        '};',
        "import beyondImage from '@/assets/zones/beyond.png';",
        "import beyondAshImage from '@/assets/zones/beyond-ash.png';",
        "import beyondDunesImage from '@/assets/zones/beyond-dunes.png';",
        "import beyondPeaksImage from '@/assets/zones/beyond-peaks.png';",
        "import beyondSeaImage from '@/assets/zones/beyond-sea.png';",
        "import beyondRegolithImage from '@/assets/zones/beyond-regolith.png';",
        '/** Old forest, drawn where a region\'s grid has no zone (the valley\'s corners). */',
        'export const zoneBeyond: ImageSourcePropType = beyondImage;',
        '/** What lies past a region other than the valley, in its gaps and round its edges when',
        ' * the screen sees past them: the volcano\'s flank, the open desert. */',
        'export const zoneBeyondByRegion: Record<string, ImageSourcePropType> = {',
        '  west: beyondDunesImage,',
        '  isles: beyondSeaImage,',
        '};',
        '/** The volcano\'s flank: what lies round the fire country\'s end of Sunstone Reach. */',
        'export const zoneBeyondAsh: ImageSourcePropType = beyondAshImage;',
        '/** The high peaks: what lies round the Frostline Highlands. */',
        'export const zoneBeyondPeaks: ImageSourcePropType = beyondPeaksImage;',
        '/** The moon\'s plain: what lies round Lumen below its horizon. */',
        'export const zoneBeyondRegolith: ImageSourcePropType = beyondRegolithImage;',
        *[f"import scenery{ident(n)} from '@/assets/zones/scenery/{n}.png';" for _k, n in scenery_keys],
        '/** The land past the walkable world, one picture per cell round a region and in its',
        ' *  grid\'s gaps, painted in the region\'s coordinates (scripts/art/scenery.py). */',
        'export const zoneScenery: Record<string, ImageSourcePropType> = {',
        *[f"  '{k}': scenery{ident(n)}," for k, n in scenery_keys],
        '};',
        f'export const BEYOND_SPILL = {BEYOND_SPILL};',
        'export const zoneProps: Record<string, ImageSourcePropType> = {',
        *[f'  {k}: prop{ident(k)},' for k in sorted(used)],
        '};',
        '',
    ]
    with open(os.path.join(worlds.ROOT, 'lib', 'zone-assets.ts'), 'w') as f:
        f.write('\n'.join(assets))
    target = os.path.join(worlds.ROOT, 'lib', 'zone-maps.ts')
    with open(target, 'w') as f:
        f.write('\n'.join(lines))
    import subprocess  # format it the way the repository's formatter does, so reruns never drift
    subprocess.run(['npx', 'oxfmt', '--write', target, os.path.join(worlds.ROOT, 'lib', 'zone-assets.ts')],
                   cwd=worlds.ROOT, check=False, capture_output=True)


# the districts drawn in their own files (frost_zones.py, isle_zones.py, sunstone_zones.py)
from frost_zones import *  # noqa: E402,F401,F403
from isle_zones import *  # noqa: E402,F401,F403
from sunstone_zones import *  # noqa: E402,F401,F403
from valley_zones import *  # noqa: E402,F401,F403
from home_zones import *  # noqa: E402,F401,F403
from space_zones import *  # noqa: E402,F401,F403
from city_zones import *  # noqa: E402,F401,F403


def main():
    built = {}
    built['town'] = build('town', town, 'garden')
    built['riverside'] = build('riverside', riverside, 'garden-north')
    built['woodland'] = build('woodland', woodland, 'garden')
    built['park'] = build('park', park, 'town')
    built['ridge'] = build('ridge', ridge, 'garden')
    built['hollow'] = build('hollow', hollow, 'ridge')
    built['snowmelt'] = build('snowmelt', snowmelt, 'hollow')
    built['saddle'] = build('saddle', saddle, 'ridge')
    built['summit'] = build('summit', summit, 'saddle')
    built['landing'] = build('landing', isle_landing, 'pier')
    built['rainforest'] = build('rainforest', isle_rainforest, 'landing')
    built['headwaters'] = build('headwaters', isle_headwaters, 'rainforest')
    built['cove'] = build('cove', isle_cove, 'headwaters')
    built['halt'] = build('halt', halt, 'town')
    built['junction'] = build('junction', junction, 'platform')
    built['canal'] = build('canal', canal, 'junction')
    built['neon'] = build('neon', city_neon, 'crossing')
    built['skyport'] = build('skyport', skyport, 'neon')
    built['market'] = build('market', city_market, 'avenue')
    built['downtown'] = build('downtown', city_downtown, 'towers')
    built['heights'] = build('heights', city_heights, 'hill')
    built['plaza'] = build('plaza', city_plaza, 'fountain')
    built['waterfront'] = build('waterfront', city_waterfront, 'promenade')
    built['docks'] = build('docks', city_docks, 'cranes')
    built['point'] = build('point', city_point, 'quay')
    built['gulch'] = build('gulch', gulch, 'platform')
    built['oasis'] = build('oasis', oasis, 'gulch')
    built['caldera'] = build('caldera', caldera, 'tunnel')
    built['springs'] = build('springs', springs, 'caldera')
    built['harbour'] = build('harbour', harbour, 'town')
    built['headland'] = build('headland', headland, 'harbour')
    # (a new zone id: the valley's old 'castle' corner is the Headland now, so saved
    # visits to 'castle' are read as the Headland, lib/world-save.ts)
    built['hearthold'] = build('hearthold', castle, 'scorch')
    built['scorch'] = build('scorch', scorch, 'gulch')
    built['station'] = build('station', station, 'lift')
    built['lumen'] = build('lumen', lumen, 'shuttle')
    built['home'] = build('home', home, 'door')
    check_overhangs(built)
    share_feet(built)
    import frames  # places meet only at their ports (Codex's connected-world contract)
    frames.check(built, LAYOUT)
    import world_lint  # the world's logic lint (world-rules.md, section 7): report only, for now
    world_lint.run(built, LAYOUT, None, OVERHEAD, {z: b['preview'] for z, b in built.items() if b['preview'] is not None})
    import map_tiles  # the world map's tiles, drawn from the same reading of each zone
    map_tiles.write_all(built, world_lint.garden_zone(), set(DOORS))
    export(built)


if __name__ == '__main__':
    main()

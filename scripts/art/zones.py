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


def town(frame: int = 0):
    cv = Canvas(W, H)
    ground.valley(cv, 'town', frame)  # one turf across the valley (ground.py)
    # the road from the garden gate, then cobbled streets and the paved square
    # the garden's main path (36 px wide, centred on x = 160) crosses the border unchanged
    road = worlds.thick([(160, -4), (160, 24)], 18, seed=0) | worlds.thick([(160, 20), (158, 60), (164, 130), (160, 240)], 15, seed=5)
    paint_road(cv, road | {(x, y) for (x, y0) in road if y0 == 0 for y in range(-12, 0)})
    square = {(x, y) for (x, y) in oval(SQUARE[0], SQUARE[1], 118, 62)}
    east = worlds.thick([(250, 300), (W + 4, 300)], 13)
    # the lane west to the Valley Halt, at the same height and width as the halt's lane
    west = worlds.thick([(-12, 300), (12, 300)], 11) | worlds.thick([(10, 300), (76, 296)], 11, seed=8)
    paint_road(cv, west | {(x, y) for (x0, y) in west if x0 == 0 for x in range(-12, 0)})
    # the road south to Driftwood Harbour, the same width and x as the harbour's road
    south = worlds.thick([(160, 340), (156, 470), (160, 560)], 15, seed=6) | worlds.thick([(160, 552), (160, H + 4)], 18)
    south |= worlds.thick([(150, 400), (110, 452)], 9, seed=7)  # a side path to the ring
    paint_road(cv, south | {(x, y) for (x, y0) in south if y0 == H - 1 for y in range(H, H + 12)})
    worlds.paint_paving(cv, square | east, seed=3)
    # a ring of darker setts around the well, and a kerb where the square meets the lawn
    for (x, y) in square:
        d = ((x - SQUARE[0]) / 30) ** 2 + ((y - SQUARE[1] + 6) / 18) ** 2
        if 0.78 < d < 1.0:
            cv.set(x, y, '#8C8574' if (x + y) % 3 else '#A9A28F')
        elif 1.0 <= d < 1.12:
            cv.set(x, y, '#D4CBB3')
    for (x, y) in square | east:
        if (x, y + 1) not in square and (x, y + 1) not in east and y + 1 < H:
            cv.set(x, y, STONE[1])
            cv.set(x, y + 1, G[1])
        elif (x, y - 1) not in square and (x, y - 1) not in east:
            cv.set(x, y, STONE[3])
    # the sparring ring: trodden earth edged with stones
    rcx, rcy = 76, 486
    ring = oval(rcx, rcy, 52, 24)
    for (x, y) in ring:
        cv.set(x, y, P[3] if smooth_noise(x, y, 6, 9) > 0.55 else P[2])
    detail.grass_edge(cv, set(ring), G, P, seed=35)
    for k in range(26):
        a = 2 * math.pi * k / 26
        detail.pebble(cv, int(rcx + 54 * math.cos(a)), int(rcy + 26 * math.sin(a)), STONE, big=k % 2 == 0)
    for fb in ((258, 196, 40, 16, 2), (200, 452, 40, 16, 1), (200, 500, 40, 16, 3)):
        meadow.flower_planter(cv, *fb)
    objects = [
        # the treeline either side of the road from the garden
        # (no prop crosses a border: the garden's meadow runs on above these)
        ('pine-n0', 'pine', 4, 6), ('tree-n1', 'tree', 40, 14), ('pine-n2', 'pine', 92, 4),
        ('pine-n3', 'pine', 200, 2), ('tree-n4', 'tree_autumn', 228, 12), ('pine-n5', 'pine', 280, 8),
        ('tree-n6', 'tree_small', 100, 96), ('bush-n7', 'bush', 196, 112), ('signpost', 'signpost', 192, 150),
        ('lamp-r1', 'lamp', 132, 168), ('lamp-r2', 'lamp', 178, 168),
        # buildings on the square's north side, facing south
        ('library', 'library', 6, 130), ('house-red', 'house_red', 214, 124),
        ('pot-lib-1', 'potted_plant', 28, 214), ('pot-lib-2', 'potted_plant', 112, 214),
        # the square
        ('well', 'well', 144, 262), ('board', 'notice_board', 230, 252),
        ('lamp-s1', 'lamp', 60, 300), ('lamp-s2', 'lamp', 262, 316),
        ('bench-s1', 'bench', 96, 330), ('cafe-1', 'cafe', 200, 318),
        # Moss's stall on the square's south-west corner, with its stock
        ('stall', 'stall', 2, 338), ('crate-1', 'crate', 92, 386), ('barrel-1', 'barrel', 108, 384),
        ('sack-1', 'sack', 6, 398),
        # the second street of houses, east
        ('house-blue', 'house_blue', 236, 344), ('pot-hb', 'potted_plant', 238, 418),
        # the ring and its spectators
        ('bench-r1', 'bench', 100, 524), ('pole', 'pennant', 130, 440),
        # hedges either side of the road south, and framing trees
        ('hedge-s1', 'hedge', 4, 548), ('hedge-s3', 'hedge', 192, 548),
        ('tree-w1', 'tree', 2, 196), ('tree-e1', 'tree', 252, 470),
        ('bush-e2', 'bush', 286, 228), ('bush-w4', 'bush', 196, 416),
        ('bunting', 'bunting', 60, 238), ('cat', 'cat', 182, 352),
    ]
    ring_fence(objects, rcx, rcy, 58, 28)
    stands = {
        'garden': (160, 18), 'library': (70, 238), 'well': (160, 316), 'stall': (60, 424),
        'ring': (76, 486), 'park': (306, 300), 'harbour': (160, 540), 'halt': (8, 300),
    }
    return cv, objects, stands


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


def harbour(frame: int = 0):
    """Driftwood Harbour: the road from Crossroads Town comes down between whitewashed
    cottages to a stone quay and the fish market; wooden jetties run out into a basin
    sheltered by a curving breakwater with the lighthouse on its tip; a sandy beach
    with rock pools and drying nets lies to the west; the cliff path climbs away east
    toward Hearthold Castle. The open sea lies beyond the breakwater."""
    SAND, WTRm = MATERIALS['sand'], MATERIALS['water']
    BLEACHED = MATERIALS['bleached']
    cv = Canvas(W, H)
    ground.valley(cv, 'harbour', frame)  # one turf across the valley (ground.py)
    # the water: the basin and the sea, deeper away from the shore
    shore_y = lambda x: 300 + int(math.sin(x / 40) * 4)  # noqa: E731  (the quay line)
    beach = {(x, y) for x in range(0, 130) for y in range(240, H) if x < 124 - (y - 240) * 0.38 + int(noise2(y // 9, 0, 291) * 6)}
    water = {(x, y) for y in range(H) for x in range(W) if y > shore_y(x) + 6 and (x, y) not in beach}
    for (x, y) in beach:
        n = smooth_noise(x, y, 6, 292)
        cv.set(x, y, SAND[2] if n > 0.35 or (n > 0.3 and (x + y) % 2) else SAND[1])
        if noise2(x, y, 299) > 0.97:
            cv.set(x, y, MATERIALS['stone'][3])  # a shell or a pebble
    for (x, y) in water:
        depth = (y - shore_y(x)) / 230 + smooth_noise(x, y, 40, 300) * 0.35
        n = smooth_noise(x, y, 12, 293 + frame)
        band = 2 if depth < 0.42 else 1 if depth < 0.8 else 0
        if (0.38 < depth < 0.46 or 0.76 < depth < 0.84) and (x + y) % 2:
            band = max(0, band - 1) if depth < 0.5 else band
        c = WTRm[band]
        if n > 0.72:
            c = WTRm[band + 1]
        cv.set(x, y, c)
    for (x, y) in water:  # foam along the beach
        if any((x + dx, y + dy) in beach for dx, dy in ((-1, 0), (0, -1), (-2, 0), (0, -2))):
            cv.set(x, y, WTRm[4] if (x + y + frame) % 3 else WTRm[3])
    for ty in range(300, H, 6):  # ripples
        for tx in range(0, W, 8):
            x, y = tx + int(noise2(tx, ty, 294) * 6), ty + int(noise2(tx, ty, 295) * 4)
            if (x, y) in water and (x + 4, y) in water and noise2(tx, ty, 296) < 0.45:
                cv.hline(x + (frame if noise2(tx, ty, 297) < 0.4 else 0), y, 3, WTRm[3])
    # rock pools on the beach
    for (px, py) in ((30, 320), (52, 352), (20, 400)):
        for (x, y) in oval(px, py, 8, 4):
            cv.set(x, y, WTRm[2] if (x, y - 1) in oval(px, py, 8, 4) else MATERIALS['stone'][3])
        for k in range(6):
            detail.pebble(cv, px - 9 + int(noise2(k, px, 298) * 18), py - 5 + int(noise2(k, py, 298) * 10), MATERIALS['stone'], big=k % 2 == 0)
    # the quay: dressed stone with a lit edge and a face down to the water
    quay = {(x, y) for x in range(100, 296) for y in range(232, shore_y(x) + 6)}
    worlds.paint_paving(cv, quay, seed=9)
    bank = set()
    for x in range(100, W):
        y = shore_y(x) + 6
        # past the quay the bank rises into the headland's sea cliff, as tall as the
        # castle's at the border (world-rules.md: edges continue), so the cliff runs on
        depth = 8 if x < 296 else 8 + (x - 296) * 18 // 23
        if x >= 296:
            y -= (x - 296) * 3 // 23
        for k in range(depth):
            if x < 296:  # the quay's dressed face
                c = STONE[3] if k == 0 else STONE[2] if (x + (k // 3) * 4) % 8 else STONE[0]
                if k > 5:
                    c = MATERIALS['leaf'][1] if (x + k) % 3 else STONE[1]  # weed at the waterline
            else:  # the cliff face, banded like the castle's
                b = k + int(noise2(x // 6, 2, 322) * 3)
                c = STONE[3] if (b // 5) % 2 else STONE[2]
                if b % 5 == 0:
                    c = STONE[4]
                if k > depth - 4:
                    c = STONE[1]
                if k < 3:
                    c = MATERIALS['grass'][4] if k == 0 else MATERIALS['grass'][1]
            cv.set(x, y + k, c)
            if x >= 296:
                water.discard((x, y + k))
                bank.add((x, y + k))
        if x >= 296:  # foam at the cliff's foot
            for k in range(depth, depth + 3):
                if (x, y + k) in water:
                    cv.set(x, y + k, WTRm[4] if (x + frame) % 3 else WTRm[3])
    # the breakwater: big blocks curving round the basin to the lighthouse
    bw = worlds.thick([(W + 6, 410), (260, 452), (200, 500), (130, 526), (92, 528)], 12, seed=15)
    bw |= {(x, y) for (x, y) in disc(90, 530, 22)}  # the round platform under the lighthouse
    for (x, y) in bw:
        blk = ((x + (y // 7) % 2 * 5) // 10 + y // 7) % 3
        c = STONE[3] if blk == 0 else STONE[2] if blk == 1 else STONE[4]
        if (x + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
            c = STONE[1]
        if (x, y - 2) not in bw:
            c = STONE[4]
        cv.set(x, y, c)
    for (x, y) in bw:
        if (x, y + 1) not in bw and (x, y + 1) in water:
            cv.set(x, y + 1, WTRm[4]); cv.set(x, y + 2, WTRm[3])
    # wooden jetties out over the basin (walkable planks)
    jetties = []
    for (jx, jy0, jy1) in ((150, 296, 392), (236, 296, 372)):
        deck = {(x, y) for x in range(jx, jx + 14) for y in range(jy0, jy1)}
        for (x, y) in deck:
            cv.set(x, y, BLEACHED[4] if (y % 4 == 0) else BLEACHED[3] if (x - jx) % 7 else BLEACHED[1])
        for (x, y) in ((jx - 1, yy) for yy in range(jy0, jy1, 12)):
            cv.set(x, y, WOOD[1]); cv.set(jx + 14, y, WOOD[1])
        for y in range(jy0, jy1):  # the deck's shadow on the water
            cv.set(jx + 14, y, WTRm[0]); cv.set(jx + 15, y, WTRm[1])
        jetties.append(deck)
    # the road down from the town and the lanes between the cottages
    road = worlds.thick([(160, -4), (160, 24)], 18) | worlds.thick([(160, 20), (150, 120), (170, 232)], 14, seed=16)
    road |= worlds.thick([(160, 120), (60, 140), (20, 200)], 9, seed=17)
    paint_road(cv, road | {(x, y) for (x, y0) in road if y0 == 0 for y in range(-12, 0)})
    cliff = worlds.thick([(W + 6, 110), (W - 12, 112)], 9) | worlds.thick([(W - 10, 112), (270, 130), (230, 180), (220, 232)], 9, seed=18)  # to the castle
    paint_road(cv, cliff | {(x, y) for (x0, y) in cliff if x0 == W - 1 for x in range(W, W + 12)})
    objects = [
        ('cottage-1', 'cottage', 10, 30), ('cottage-2', 'cottage_b', 210, 26), ('cottage-3', 'cottage', 40, 150),
        ('cottage-4', 'cottage_b', 236, 140), ('market', 'fish_stall', 108, 226), ('pots-1', 'lobster_pots', 196, 240),
        ('nets-1', 'net_rack', 6, 236), ('nets-2', 'net_rack', 4, 300), ('anchor', 'anchor', 286, 240),
        ('lighthouse', 'lighthouse', 68, 396), ('boat-1', 'boat_blue', 168, 330), ('boat-2', 'boat_red', 254, 340),
        ('boat-3', 'boat_blue', 186, 420), ('bollard-1', 'bollard', 140, 290), ('bollard-2', 'bollard', 226, 290),
        ('bollard-3', 'bollard', 290, 290), ('pots-2', 'lobster_pots', 286, 206),
        ('upturned', 'upturned_boat', 8, 400), ('washing', 'washing_line', 110, 90), ('buoy-1', 'buoy', 120, 450),
        ('buoy-2', 'buoy', 300, 380), ('chair-1', 'deck_chair', 10, 348), ('chair-2', 'deck_chair_b', 32, 354),
        ('drift', 'driftwood', 6, 452), ('sail', 'sailboat', 262, 496),
    ]
    # a rock pool on the lower beach: dark stones round a little pool of sky
    for (x, y) in oval(30, 506, 14, 6):
        d = math.hypot((x - 30) / 14, (y - 506) / 6)
        cv.set(x, y, WTRm[2] if d < 0.6 and (x + y) % 5 else WTRm[4] if d < 0.6 else STONE[3] if y < 506 else STONE[1])
        if 0.6 <= d and noise2(x, y, 611) > 0.5:
            cv.set(x, y, STONE[2])
        water.add((x, y))
    blocked = (water | bank) - set().union(*jetties)
    stands = {'town': (160, 18), 'market': (150, 288), 'jetty': (157, 384), 'beach': (34, 380), 'castle': (300, 116)}
    return cv, objects, stands, blocked


def sea_cliffs(cv: Canvas, frame: int, edge_y):
    """The headland's sea cliffs (shared by the Headland): below `edge_y(x)` a grass lip,
    a banded stone face and then the sea, foamy at the cliff's foot, with glints on the
    open water. Returns the sea and face pixels (blocked)."""
    WTRm, STONEm = MATERIALS['water'], MATERIALS['stone']
    sea = set()
    for x in range(W):
        e = edge_y(x)
        for y in range(e, H):
            k = y - e
            if k < 3:
                c = MATERIALS['grass'][4] if k == 0 else MATERIALS['grass'][1]
            elif k < 26:
                band = (k + int(noise2(x // 6, 2, 322) * 3)) // 5
                c = STONEm[3] if band % 2 else STONEm[2]
                if (k + int(noise2(x // 6, 2, 322) * 3)) % 5 == 0:
                    c = STONEm[4]
                if k > 22:
                    c = STONEm[1]
            else:
                n = smooth_noise(x, y, 10, 323 + frame)
                depth = k - 26 + int(n * 18)
                c = WTRm[2] if depth < 30 or (depth < 38 and (x + y) % 2) else WTRm[1]
                if depth > 90 or (depth > 82 and (x + y) % 2):
                    c = WTRm[0]
                if n > 0.74:
                    c = WTRm[min(4, WTRm.index(c) + 1)]
                if k < 30:
                    c = WTRm[4] if (x + frame) % 3 else WTRm[3]
                elif k < 34 and (x + y) % 2:
                    c = WTRm[3]
                sea.add((x, y))
            cv.set(x, y, c)
            if 2 < k < 26:
                sea.add((x, y))
    for ty in range(300, H, 6):
        for tx in range(0, W, 11):
            x, y = tx + int(noise2(tx, ty, 324) * 6), ty + int(noise2(tx, ty, 325) * 3)
            if (x, y) in sea and (x + 3, y) in sea and y - edge_y(min(W - 1, max(0, x))) > 36 and noise2(tx, ty, 326) < 0.45:
                cv.hline(x, y, 3, WTRm[3])
    return sea


def headland(frame: int = 0):
    """The Headland, east of the harbour (Matt, 18 Oct: the castle moved to the fire
    country): the cliff path from the harbour comes in at the west edge and climbs the
    open down to the lookout tower that watches the sea from the cliff top; sheep graze
    behind a dry stone wall to the north, a bench looks out over the water, and the sea
    cliffs drop away south and east to the breakwater's root at their foot. Wind-bent
    and quiet: the valley's last place before the sea."""
    STONEm = MATERIALS['stone']
    cv = Canvas(W, H)
    ground.valley(cv, 'headland', frame)  # one turf across the valley (ground.py)

    def edge_y(x):
        # the harbour's water meets the headland's west edge below y = 306 (seamless rule)
        e = 470 + int(math.sin(x / 31) * 10 + noise2(x // 7, 0, 321) * 8) - max(0, (x - 260) * 2)
        return min(e, 306 + int(x * 2.7)) if x < 60 else e
    sea = sea_cliffs(cv, frame, edge_y)
    # the harbour's breakwater runs on to its root against the cliff's foot
    root = worlds.thick([(-8, 415), (24, 405)], 12)
    for (x, y) in root:
        blk = ((x + 8 + (y // 7) % 2 * 5) // 10 + y // 7) % 3
        c = STONEm[3] if blk == 0 else STONEm[2] if blk == 1 else STONEm[4]
        if (x + 8 + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
            c = STONEm[1]
        cv.set(x, y, c)
    for (x, y) in root:
        if (x, y + 1) not in root and (x, y + 1) in sea:
            cv.set(x, y + 1, MATERIALS['water'][4]); cv.set(x, y + 2, MATERIALS['water'][3])
    # the cliff path from the harbour up the down to the tower's steps, and a spur to
    # the bench on the cliff top
    path = worlds.thick([(-6, 110), (12, 112)], 9) | worlds.thick(
        [(10, 112), (46, 150), (80, 222), (140, 300), (196, 368), (228, 412), (228, 424)], 9, seed=19)
    path |= worlds.thick([(120, 274), (92, 330), (76, 400), (74, 440)], 6, seed=23)
    paint_road(cv, path | {(x, y) for (x0, y) in path if x0 == 0 for x in range(-12, 0)})
    objects = [
        ('tower', 'lookout_tower', 198, 300),
        ('wall-1', 'drystone_wall', 150, 70), ('wall-2', 'drystone_wall', 214, 70), ('wall-3', 'drystone_wall', 150, 190),
        ('wall-end', 'stone', 284, 186),
        ('sheep-1', 'sheep', 176, 110), ('sheep-2', 'sheep_left', 236, 128), ('sheep-3', 'sheep', 204, 156),
        ('hive-1', 'beehive', 112, 40), ('hive-2', 'beehive', 128, 52),
        ('tree-w', 'tree_small', 10, 196), ('bush-1', 'bush', 270, 230), ('bush-2', 'bush', 30, 300),
        ('bench', 'bench', 52, 410), ('stone-1', 'stone', 280, 400), ('stone-2', 'stone', 140, 440),
    ]
    blocked = set(sea)
    stands = {'harbour': (14, 112), 'tower': (228, 430), 'bench': (74, 448), 'down': (150, 280)}
    return cv, objects, stands, blocked


def riverside(frame: int = 0):
    """The Riverside, east of the garden: the garden's stream comes in at the west edge
    exactly where it leaves the garden (same line, width and bluff), and widens as it
    runs east into a slow river. The watermill stands on the north bank with its wheel
    in the race, willows lean over the south bank, reeds and lily pads fill the
    shallows, a heron fishes, and stepping stones cross where it is still narrow."""
    WTRm, SAND = MATERIALS['water'], MATERIALS['sand']
    cv = Canvas(W, H)
    ground.valley(cv, 'riverside', frame)  # one turf across the valley (ground.py)
    OFF = meadow.W  # this zone continues the garden's x axis

    def centre(x):
        return meadow.stream_centre(x + OFF) + x * 0.06

    def half(x):
        return 9 + (smooth_noise(x + OFF, 0, 13, 91) - 0.5) * 2.4 + (x / W) ** 1.4 * 18

    river = {(x, y) for x in range(W) for y in range(int(centre(x) - half(x)), int(centre(x) + half(x)) + 1)}
    top = {x: min(y for (xx, y) in river if xx == x) for x in range(W)}
    bluff = {(x, y) for x in range(W) for y in range(top[x] - (7 + int(smooth_noise(x + OFF, 3, 9, 92) * 3)), top[x])}
    for (x, y) in river:  # the south bank: a sandy lip
        pass
    for x in range(W):
        bot = max(y for (xx, y) in river if xx == x)
        for k in range(1, 3 + int(x / 80)):
            cv.set(x, bot + k, SAND[1] if noise2(x, k, 411) < 0.8 else SAND[2])
        cv.set(x, bot + 1, SAND[0])
    for x in range(W):  # the north bank's bluff, as in the garden
        h = top[x] - min(y for (xx, y) in bluff if xx == x)
        col = (x + OFF + int(noise2((x + OFF) // 6, 1, 95) * 6)) % 6
        si = (x + OFF + int(noise2((x + OFF) // 6, 1, 95) * 6)) // 6
        for k in range(h):
            y = top[x] - h + k
            if k == 0:
                c = G[3]
            elif k == 1:
                c = G[2] if (x // 2) % 3 else G[1]
            else:
                row, r = (k - 2 + (si % 2) * 2) // 4, (k - 2 + (si % 2) * 2) % 4
                base = 3 if noise2(si, row, 97) > 0.45 else 2
                c = STONE[0] if col == 5 or r == 3 else STONE[base + 1] if col == 0 or r == 0 else STONE[base - 1] if col == 4 else STONE[base]
                if k == h - 1:
                    c = STONE[1] if col != 5 else STONE[0]
            cv.set(x, y, c)
    for (x, y) in river:
        d = abs(y - centre(x)) / max(1, half(x))
        c = WTRm[2] if d < 0.3 else WTRm[1]
        if half(x) > 16 and d < 0.15:
            c = WTRm[1] if (x + y) % 2 else WTRm[2]  # the deeper channel
        k = y - top[x]
        if k < 2:
            c = WTRm[0]  # the bluff's shadow
        elif k == 2 and (x // 2 + int(noise2(x // 4, 7, 98) * 3)) % 3:
            c = WTRm[4] if x % 5 else WTRm[3]
        cv.set(x, y, c)
    for i in range(46):  # flowing highlights
        x = int(noise2(i, 4, 412) * W)
        y = int(centre(x) + (noise2(i, 5, 412) - 0.5) * half(x) * 1.2)
        for t in range(5):
            if (x + t, y) in river and (x + t, y - 1) in river:
                cv.set(x + t, y, WTRm[3] if t < 4 else WTRm[2])
    # stepping stones where it is still narrow
    for k, sy in enumerate(range(int(centre(46) - half(46)) + 2, int(centre(46) + half(46)), 6)):
        sx = 44 + (3 if k % 2 else -2)
        for (x, y) in oval(sx, sy, 4, 2.5):
            cv.set(x, y, STONE[4] if (x - sx) + (y - sy) < 0 else STONE[2])
        for x in range(sx - 4, sx + 5):
            cv.set(x, sy + 3, WTRm[4])
    # the race beside the mill: a stone channel taking water to the wheel
    for y in range(top[220] - 30, top[220] + 2):
        for x in range(214, 236):
            cv.set(x, y, WTRm[2] if 216 <= x < 234 else STONE[3] if x < 216 else STONE[1])
    path = worlds.thick([(24, 222), (60, 214), (130, 236), (200, 230)], 9, seed=21)  # a lane to the mill (the garden has no path at this edge)
    path |= worlds.thick([(30, 404), (70, 390), (160, 420), (W - 20, 430)], 9, seed=22)  # the south bank walk
    paint_road(cv, {(x, y) for (x, y) in path if (x, y) not in river and (x, y) not in bluff})
    for i in range(160):  # wildflowers on the north meadow, thickest by the hives
        x, y = 14 + int(noise2(i, 0, 530) * 120), 30 + int(noise2(i, 1, 530) * 110)
        col = ('#F2D27A', '#E8A0BC', '#FFFFFF', '#B8A0E8')[i % 4]
        cv.set(x, y, col); cv.set(x, y + 1, '#447A50')
    for (x, y) in oval(206, 100, 52, 40):  # the pasture grazed short
        if (x + y) % 3 == 0:
            cv.set(x, y, '#8EB86A')
    objects = [
        ('mill', 'water_mill', 140, top[220] - 96 + 6), ('willow-1', 'willow', 70, 330), ('willow-2', 'willow', 230, 360),
        ('reeds-1', 'reeds', 110, int(centre(120) + half(120)) - 24), ('reeds-2', 'reeds', 280, int(centre(290) + half(290)) - 26),
        ('reeds-3', 'reeds', 160, int(centre(170) - half(170)) + 2), ('heron', 'heron', 196, int(centre(206)) - 6),
        ('lilies-1', 'lily_pads', 250, int(centre(265)) - 6), ('lilies-2', 'lily_pads', 120, int(centre(135)) + 2),
        ('tree-1', 'tree', 10, 120), ('tree-2', 'tree_small', 260, 110), ('bush-1', 'bush', 40, 470),
        ('bush-2', 'bush', 200, 500), ('tree-3', 'tree_autumn', 120, 470), ('bench', 'bench', 170, 440),
        ('sack-1', 'sack', 120, 220), ('sack-2', 'sack', 108, 224), ('barrel-m', 'barrel', 86, 206),
        # a pasture on the north meadow: sheep grazing inside a fence, beehives by the flowers
        ('pfence-1', 'fence_c', 150, 40), ('pfence-2', 'fence_c', 210, 40), ('pfence-3', 'fence_c', 150, 150),
        ('pfence-4', 'fence_c', 210, 150),
        ('sheep-1', 'sheep', 166, 72), ('sheep-2', 'sheep_left', 226, 92), ('sheep-3', 'sheep', 190, 118),
        ('sheep-4', 'sheep_left', 244, 60), ('hive-1', 'beehive', 40, 40), ('hive-2', 'beehive', 66, 46),
    ]
    stones = {(x, y) for x in range(38, 52) for y in range(int(centre(46) - half(46)) - 2, int(centre(46) + half(46)) + 3)}
    steps = {(x, y) for (x, y) in bluff if 38 <= x < 52}  # steps cut down the bluff to the stones
    for (x, y) in steps:
        cv.set(x, y, STONE[4] if (y - top[x]) % 3 == 0 else STONE[2] if x < 50 else STONE[1])
    stones |= steps
    blocked = (river | bluff) - stones
    stands = {'garden-north': (8, 220), 'garden-south': (8, 400), 'mill': (190, 232), 'stones': (46, int(centre(46))),
              'willows': (120, 430)}
    return cv, objects, stands, blocked


def park(frame: int = 0):
    """The Town Park, east of Crossroads Town: the town's paved street comes in at the
    west edge at the same height and width and opens on a ring of paths round the
    bandstand; the fountain plaza lies south, then a duck pond with a little island
    and a willow; flower beds, clipped hedges, benches, lamps and the ice cream cart."""
    WTRm = MATERIALS['water']
    cv = Canvas(W, H)
    ground.valley(cv, 'park', frame)  # one turf across the valley (ground.py)
    paths = worlds.thick([(-8, 300), (60, 300)], 13)  # the town's street, unchanged
    paths |= {(x, y) for (x, y) in oval(160, 190, 92, 52)} - {(x, y) for (x, y) in oval(160, 190, 74, 38)}
    paths |= worlds.thick([(60, 300), (160, 300), (160, 240)], 11, seed=27)
    paths |= {(x, y) for (x, y) in oval(160, 330, 44, 26)}  # the fountain plaza
    paths |= worlds.thick([(160, 356), (150, 420), (100, 460)], 9, seed=28)
    worlds.paint_paving(cv, paths | {(x, y) for (x0, y) in paths if x0 == 0 for x in range(-12, 0)}, seed=11)
    pond = {(x, y) for (x, y) in oval(200, 470, 84, 46)}
    island = {(x, y) for (x, y) in oval(232, 462, 20, 10)}
    water = pond - island
    for (x, y) in water:
        d = math.hypot((x - 200) / 84, (y - 470) / 46)
        c = WTRm[2] if d > 0.7 else WTRm[1]
        if (x, y - 1) not in pond or (x, y - 2) not in pond:
            c = WTRm[0]
        cv.set(x, y, c)
    for (x, y) in pond:
        if (x, y + 1) not in pond:
            cv.set(x, y + 1, MATERIALS['sand'][1])
    for ty in range(430, 516, 6):
        for tx in range(120, 290, 9):
            x, y = tx + int(noise2(tx, ty, 431) * 5), ty + int(noise2(tx, ty, 432) * 3)
            if (x, y) in water and (x + 3, y) in water and (x, y - 2) in water:
                cv.hline(x, y, 3, WTRm[3])
    for (x, y) in island:
        cv.set(x, y, G[3] if (x - 232) + (y - 462) < 0 else G[2])
    for fb in ((40, 120, 40, 16, 1), (240, 120, 40, 16, 2), (30, 380, 40, 16, 3), (250, 380, 40, 16, 0)):
        meadow.flower_planter(cv, *fb)
    objects = [
        ('bandstand', 'bandstand', 118, 140), ('fountain', 'fountain', 132, 300),
        ('willow', 'willow', 193, 371), ('lilies', 'lily_pads', 140, 476), ('duck-1', 'duck', 170, 500),
        ('duck-2', 'duck', 262, 488), ('heron', 'heron', 290, 440),
        ('hedge-n1', 'hedge', 4, 30), ('hedge-n2', 'hedge', 224, 30), ('tree-1', 'tree', 110, 4),
        ('tree-2', 'tree_autumn', 284, 140), ('tree-3', 'tree', 4, 150), ('tree-4', 'tree_small', 20, 470),
        ('bench-1', 'bench', 60, 196), ('bench-2', 'bench', 216, 196), ('bench-3', 'bench', 96, 360),
        ('lamp-1', 'lamp', 66, 260), ('lamp-2', 'lamp', 246, 260), ('lamp-3', 'lamp', 108, 410),
        ('icecream', 'ice_cream_cart', 220, 296), ('bush-1', 'bush', 0, 250), ('bush-2', 'bush', 290, 250),
        ('bush-3', 'bush', 4, 540), ('bush-4', 'bush', 220, 540),
    ]
    stands = {'town': (8, 300), 'bandstand': (160, 240), 'fountain': (160, 360), 'pond': (100, 456)}
    return cv, objects, stands, water


def ridge(frame: int = 0):
    """The Snowy Ridge, north of the garden: the trail comes up out of the garden's
    treeline at the bottom (the same x, through the same dark forest floor), climbs
    through thinning pines onto an alpine meadow with an open tarn and cairns, then
    by steps up a stone face to the terrace where the cabin stands under the peaks.
    Snow lies only above the face (world logic): the pines, the tarn and the meadow
    below it are clear of it."""
    SNOWm, STONEm = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W, H)
    alpine = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
    ground.valley(cv, 'ridge', frame)  # one turf across the valley (ground.py)
    # the forest floor at the bottom, deepening into the garden's own treeline band
    treeline = meadow.draw_top_band()
    B = H - treeline.h
    for y in range(B - 60, B):
        for x in range(W):
            t = (y - (B - 60)) / 60
            if noise2(x, y, 441) < t:
                cv.set(x, y, G[1])
    style.dither_dark(cv, 0, B - 20, W, 20, 1.0)
    style.dither_dark(cv, 0, B - 40, W, 20, 0.5)
    # the terrace: everything above the face is high ground under snow
    def rim(x):
        return 210 + int(math.sin(x / 27) * 8 + noise2(x // 6, 0, 442) * 6)
    FACE_H = 24
    for x in range(W):
        r = rim(x)
        for y in range(0, r):  # snow: soft drifts, wind ripples, blue in the hollows
            n = smooth_noise(x, y, 18, 443)
            c = SNOWm[3] if n > 0.4 else SNOWm[2] if n > 0.22 or (x + y) % 2 else SNOWm[1]
            rip = (y * 2 + int(math.sin(x / 13 + y / 31) * 4)) % 9
            if rip == 0 and n > 0.3:
                c = SNOWm[2]  # sastrugi: the wind's ripples
            elif rip == 1 and n > 0.3:
                c = SNOWm[3]
            cv.set(x, y, c)
        for k in range(FACE_H):
            y = r + k
            band = (k + int(noise2(x // 7, 3, 445) * 3)) // 5
            c = STONEm[3] if band % 2 else STONEm[2]
            if (k + int(noise2(x // 7, 3, 445) * 3)) % 5 == 0:
                c = STONEm[4]
            if k < 2:
                c = SNOWm[3] if k == 0 else SNOWm[1]
            if k > FACE_H - 4:
                c = STONEm[1]
            cv.set(x, y, c)
        for d in range(3):
            if (x + d) % 2 or d == 0:
                style.darken(cv, x, r + FACE_H + d)
    for i in range(26):  # rocks poking through the snow, each with snow on its top
        x, y = int(noise2(i, 0, 447) * W), 70 + int(noise2(i, 1, 447) * 130)
        if y < rim(x) - 6:
            detail.pebble(cv, x, y, STONEm, big=i % 3 == 0)
            cv.set(x, y - 1, SNOWm[3]); cv.set(x + 1, y - 1, SNOWm[3])
    # along the top: the stepped rock shoulders up to the Snow Saddle, one band with the
    # saddle's (frost_zones.shoulders), open where the switchback comes down
    shoulder = shoulders(cv, 'ridge')
    # the alpine tarn below the face, open water (no snow lies down here)
    WTR = MATERIALS['water']
    tarn = {(x, y) for (x, y) in oval(232, 404, 38, 15)}
    for (x, y) in tarn:
        d = math.hypot((x - 232) / 38, (y - 404) / 15)
        c = WTR[1] if d < 0.6 else WTR[2]
        if (x, y - 1) not in tarn or (x, y - 2) not in tarn:
            c = STONEm[1]
        cv.set(x, y, c)
    for (x, y) in oval(232, 405, 42, 18):
        if (x, y) not in tarn:
            cv.set(x, y, STONEm[3] if (x + y) % 3 else STONEm[2])  # a stony shore
    for k in range(5):
        gx = 206 + k * 11
        if (gx, 400 + k % 2) in tarn:
            cv.hline(gx, 400 + k % 2, 3, WTR[4])
    # the trail: up from the garden, round the tarn, steps up the face, to the cabin
    trail = worlds.thick([(206, H + 12), (206, H - 40), (190, 470), (150, 400), (130, 330), (150, 270), (150, 220)], 9.5, seed=29)
    trail |= worlds.thick([(150, 220), (150, 170), (120, 140)], 8, seed=30)
    # on up through the gap to the Snow Saddle, and west across the terrace to Fir Hollow
    # the switchback up past the cabin's east end to the saddle (Codex: it "reveals the
    # cabin roof"), and west across the meadow to Fir Hollow at its port
    trail |= gthick('ridge', [(150, -386), (236, -392), (262, -456), (258, -514), (204, -546), (204, -586)], 8)
    trail |= gthick('ridge', [(132, -240), (60, -228), (-10, -228)], 8)
    on_terrace = {(x, y) for (x, y) in trail if y < rim(x)}
    paint_road(cv, {(x, y) for (x, y) in trail if y >= rim(x) + FACE_H} | {(x, y) for (x0, y) in trail if y == H - 1 for x in [x0] for y in range(H, H + 12)})
    # the bottom is the band the garden screen draws above its clearing
    # (garden_meadow.draw_top_band): the same shade and the same trail, so the ridge runs
    # on into the garden without a seam, here and on the garden screen
    for y in range(treeline.h):
        for x in range(W):
            cv.set(x, B + y, treeline.get(x, y))
    for (x, y) in on_terrace:  # a trodden line in the snow
        cv.set(x, y, SNOWm[1] if (x + y) % 3 else SNOWm[2])
    steps = set()
    for (x, y) in trail:
        if rim(x) <= y < rim(x) + FACE_H:
            steps.add((x, y))
            cv.set(x, y, STONEm[4] if (y - rim(x)) % 4 == 0 else STONEm[2] if (y - rim(x)) % 4 < 3 else STONEm[1])
    objects = [
        # the garden's treeline continues at the bottom, clear of the trail
        ('pine-b1', 'pine', 4, H - 100), ('pine-b2', 'pine', 50, H - 92), ('pine-b3', 'pine', 96, H - 102),
        ('pine-b4', 'pine', 240, H - 98), ('pine-b5', 'pine', 280, H - 104), ('pine-b6', 'pine', 140, H - 150),
        ('pine-m1', 'pine', 14, 392), ('pine-m2', 'pine', 270, 440), ('pine-m3', 'pine', 270, 250),
        ('pine-m4', 'pine', 60, 250), ('cairn-1', 'cairn', 100, 360),
        ('cairn-2', 'cairn', 176, 250), ('boulder-1', 'boulder', 20, 430), ('stone-1', 'stone', 280, 470),
        ('cabin', 'cabin', 150, 80), ('campfire', 'campfire', 110, 176), ('pine-t1', 'snowy_pine', 10, 120),
        ('pine-t2', 'snowy_pine', 270, 120), ('pine-t3', 'snowy_pine', 40, 150),
        ('woodpile', 'woodpile', 122, 138), ('sled', 'sled', 214, 190), ('snowman', 'snowman', 90, 96),
        ('wall-1', 'drystone_wall', 166, 334), ('wall-2', 'drystone_wall', 228, 334), ('wall-end', 'stone', 288, 330), ('marmot', 'marmot_rock', 220, 470),
        ('cotton-1', 'cotton_grass', 196, 380), ('cotton-2', 'cotton_grass', 270, 398), ('cotton-3', 'cotton_grass', 210, 418),
    ]
    face = {(x, y) for x in range(W) for y in range(rim(x), rim(x) + FACE_H)}
    stands = {'garden': (206, H - 8), 'tarn': (186, 424), 'cabin': (200, 176), 'campfire': (146, 204),
              'saddle': (204, 6), 'hollow': (4, 348)}
    return cv, objects, stands, (face - steps) | shoulder | tarn


def halt(frame: int = 0):
    """The Valley Halt, west of Crossroads Town and south of the Woodland: the lane from
    the town comes in at the east edge and opens on the platform, where the little stone
    station faces the line under its canopy; the rails run west out of the valley (the
    train to Cogsworth) and stop at a buffer before the town. A windmill turns on the
    meadow to the north under the woodland's edge; south of the line, behind a fence, a
    small farm: cabbages, wheat with a scarecrow, a pumpkin patch, haystacks and a red
    barn, reached by a track down the east side."""
    cv = Canvas(W, H)
    ground.valley(cv, 'halt', frame)  # one turf across the valley (ground.py)
    # (the woodland's forest floor reaches down over the top: ground.py blends it)
    lane = worlds.thick([(W + 12, 300), (W - 12, 300)], 11) | worlds.thick([(W - 10, 300), (230, 296), (190, 290)], 11, seed=31)
    paint_road(cv, lane | {(x, y) for (x0, y) in lane if x0 == W - 1 for x in range(W, W + 12)})
    # the platform: dressed slabs with a white edge over the line
    plat = {(x, y) for x in range(0, 236) for y in range(282, 318)}
    worlds.paint_paving(cv, plat, seed=13)
    cv.hline(0, 316, 236, '#F4F0E6'); cv.hline(0, 317, 236, STONE[1])
    paint_rails(cv, 322)
    for y in range(316, 344):  # the line ends at a buffer before the town
        for x in range(246, W):
            cv.set(x, y, G[2] if (x + y) % 3 else G[3])
    for x in range(232, 244):
        cv.vline(x, 320, 18, WOOD[2] if x % 2 else WOOD[1])
    cv.hline(232, 320, 12, RED[3])
    # a farm track south from the lane, down the east side to the farmyard
    # (the farm ends at its yard: past it, to the south, the old forest begins, so
    # nothing runs off the edge into it; world-rules.md, every path ends at a node)
    for y in range(H - 56, H):  # the forest floor creeping out from under the trees
        for x in range(W):
            if noise2(x, y, 453) < (y - (H - 56)) / 56:
                cv.set(x, y, FOREST_FLOOR[2] if (x + y) % 3 else FOREST_FLOOR[1])
    track = worlds.thick([(298, 300), (304, 360), (300, 440), (292, 492), (262, 526)], 8, seed=33)
    yard = {(x, y) for (x, y) in oval(232, 528, 66, 17)}
    paint_road(cv, track | yard)
    # fields behind the fence: cabbages in furrows (west), wheat (east) with the
    # scarecrow, a pumpkin patch below; the farm's own bounds, not a grid
    SOILm = MATERIALS['soil']
    def furrows(mask, crop):
        for (x, y) in mask:
            row = (y - 372) % 10
            if crop == 'wheat':
                stalk = (x + (y // 3) % 2 + int(math.sin(y / 9) * 2)) % 3
                c = '#E2BC5E' if stalk == 0 else '#C99A3C' if stalk == 1 else '#F2D27A'
                if row == 9:
                    c = '#A87E2C'
            else:
                c = SOILm[3] if row < 3 else SOILm[2] if row < 8 else SOILm[1]
                if row == 0:
                    c = SOILm[4]
            cv.set(x, y, c)
    cabbage = {(x, y) for y in range(372, 472) for x in range(14, 150 - (y - 372) // 8)}
    wheat = {(x, y) for y in range(372, 446) for x in range(162 + (y - 372) // 10, 280 - max(0, y - 420))}
    patch = {(x, y) for y in range(492, 560) for x in range(16 + (y - 492) // 6, 128)}
    furrows(cabbage, 'cabbage'); furrows(wheat, 'wheat'); furrows(patch, 'patch')
    for y in range(375, 472, 10):  # cabbages along the furrows
        for x in range(18, 146, 7):
            cx = x + int(noise2(x, y, 452) * 2)
            if (cx, y + 2) not in cabbage:
                continue
            for (px, py) in disc(cx, y + 2, 2.4):
                cv.set(px, py, MATERIALS['leaf'][3] if (px - cx) + (py - y - 2) < 0 else MATERIALS['leaf'][2])
            cv.set(cx - 1, y + 1, MATERIALS['leaf'][4])
    for x in range(162, 280, 2):  # the wheat's lit heads along its top edge
        cv.set(x, 372, '#F8E6A0'); cv.set(x + 1, 373, '#F2D27A')
    for (mask, grass_edge) in ((cabbage, True), (wheat, True), (patch, True)):
        for (x, y) in mask:  # a low hedge of long grass round each field
            if any((x + dx, y + dy) not in mask for (dx, dy) in ((1, 0), (-1, 0), (0, 1))):
                cv.set(x, y, G[3] if (x + y) % 2 else G[4])
    objects = [
        ('station', 'station_house', 66, 204), ('signal', 'semaphore', 20, 262), ('bench-p', 'bench', 190, 280),
        ('lamp-p1', 'lamp', 40, 268), ('lamp-p2', 'lamp', 220, 268), ('sack-p', 'sack', 178, 300), ('crate-p', 'crate', 160, 298),
        ('pine-n1', 'pine', 10, 20), ('tree-n2', 'tree', 90, 30), ('pine-n3', 'pine', 150, 14),
        ('mill', 'windmill', 226, 70), ('bush-1', 'bush', 286, 200), ('bush-2', 'bush', 6, 200),
        ('fence-1', 'fence_c', 18, 356), ('fence-2', 'fence_c', 78, 356), ('fence-3', 'fence_c', 138, 356),
        ('fence-4', 'fence_c', 198, 356),
        ('scarecrow', 'scarecrow', 200, 380), ('barn', 'barn', 150, 452), ('hay-1', 'haystack', 132, 500),
        ('hay-2', 'haystack', 112, 530), ('pump-1', 'pumpkins', 30, 506), ('pump-2', 'pumpkins', 70, 524),
        ('pump-3', 'pumpkins', 44, 540), ('barrel-f', 'barrel', 276, 500), ('crate-f', 'crate', 284, 520),
        ('tree-s2', 'tree_autumn', 236, 196),
    ]
    rails = {(x, y) for x in range(0, 246) for y in range(319, 338)}
    stands = {'town': (312, 300), 'platform': (130, 300), 'station': (118, 292), 'mill': (258, 186),
              'farm': (262, 530)}
    return cv, objects, stands, rails | cabbage | wheat | patch


FOREST_FLOOR = ['#24382A', '#40603A', '#577A44', '#668A4E', '#8EAE68']
DARK_FLOOR = [tuple(int(c[k:k + 2], 16) for k in (1, 3, 5)) for c in FOREST_FLOOR]


def woodland(frame: int = 0):
    """The Woodland, west of the garden: the garden's stream is born here. It leaves the
    east edge exactly where it enters the garden, and upstream it narrows to a spring
    that falls from a mossy rock into a pool. Old trees close in at the edges, light
    comes through in dappled pools, a path winds to a clearing with the hollow oak,
    a fairy ring, ferns, fallen logs and a hidden bench."""
    WTRm, GOLDm = MATERIALS['water'], MATERIALS['gold']
    cv = Canvas(W, H)
    ground.valley(cv, 'woodland', frame)  # one turf across the valley (ground.py)
    for i in range(260):  # leaf litter
        x, y = int(noise2(i, 0, 421) * W), int(noise2(i, 1, 421) * H)
        cv.set(x, y, ('#8A6A3E', '#B8945A', '#6E8A3E')[i % 3])
    OFF = -meadow.W

    def centre(x):
        return meadow.stream_centre(x + OFF)

    def half(x):
        full = 9 + (smooth_noise(x + OFF, 0, 13, 91) - 0.5) * 2.4
        return full * min(1.0, max(0.0, (x - 96) / 120)) + 3 * (x >= 96)

    spring_x = 96
    river = {(x, y) for x in range(spring_x, W) for y in range(int(centre(x) - half(x)), int(centre(x) + half(x)) + 1)}
    pool = {(x, y) for (x, y) in oval(spring_x - 6, centre(spring_x) + 2, 20, 11)}
    water = river | pool
    for (x, y) in water:
        c = WTRm[2] if (x, y) in river and abs(y - centre(x)) < 2 else WTRm[1]
        if (x, y - 1) not in water:
            c = WTRm[0]
        cv.set(x, y, c)
    for (x, y) in water:  # a stony, mossy rim
        for dx, dy in ((0, 1), (0, 2), (1, 0), (-1, 0)):
            q = (x + dx, y + dy)
            if q not in water and 0 <= q[0] < W:
                cv.set(*q, STONE[3] if noise2(q[0], q[1], 422) > 0.5 else MATERIALS['leaf'][2])
    # the spring: a mossy rock face with the water falling from a cleft into the pool
    rock = {(x, y) for (x, y) in oval(spring_x - 22, centre(spring_x) - 22, 34, 18)}
    for (x, y) in rock:
        band = (y + int(noise2(x // 5, 0, 423) * 3)) // 4
        c = STONE[3] if band % 2 else STONE[2]
        if (x, y - 1) not in rock or noise2(x // 3, y // 3, 424) > 0.7:
            c = MATERIALS['leaf'][3] if (x, y - 1) not in rock else MATERIALS['leaf'][2]
        cv.set(x, y, c)
    fx = spring_x - 14
    for y in range(int(centre(spring_x) - 26), int(centre(spring_x) - 2)):
        for x in range(fx - 3, fx + 4):
            cv.set(x, y, WTRm[4] if (x + y + frame) % 3 == 0 else WTRm[3] if x < fx + 1 else WTRm[2])
    for k in range(10):  # foam where it lands
        cv.set(fx - 5 + k, int(centre(spring_x)) - 1 + (k % 2), WTRm[4])
    # the spring is the foot of Fir Hollow's fall: the meltwater from Snowmelt Lake comes
    # down off the escarpment above (frost_zones.FALLS_X) as a brook under the trees and
    # over the mossy rock (Codex: the lake's water reaches the valley's river)
    brook = worlds.thick([(FALLS_X, -4), (62, 60), (54, 140), (64, 214), (fx + 1, int(centre(spring_x)) - 26)], 3)
    for (x, y) in brook:
        if (x, y) in rock:
            continue
        c = WTRm[2] if (x + y // 2) % 4 else WTRm[3]
        if (x - 1, y) not in brook:
            c = WTRm[0]
        cv.set(x, y, c)
    for (x, y) in brook:
        if (x + 1, y) not in brook and noise2(x, y, 428) > 0.4:
            cv.set(x + 1, y, STONE[2])
    water = water | {p for p in brook if p not in rock}
    # the path from the garden's west side into the trees and the clearing
    # (the garden's orchard walk runs on across the border at the same height and width)
    path = worlds.thick([(W + 12, meadow.ORCHARD_WALK_Y), (250, meadow.ORCHARD_WALK_Y)], 8.5) | worlds.thick([(254, meadow.ORCHARD_WALK_Y), (190, 420), (150, 380), (130, 330)], 9, seed=25)
    path |= worlds.thick([(130, 270), (150, 200), (120, 140)], 9, seed=26)
    clearing = {(x, y) for (x, y) in oval(110, 140, 52, 34)}
    paint_road(cv, {(x, y) for (x, y) in path if (x, y) not in water} | {(x, y) for (x0, y) in path if x0 == W - 1 for x in range(W, W + 12)})
    for (x, y) in clearing:  # the clearing is sunlit grass
        n = smooth_noise(x, y, 14, 425)
        cv.set(x, y, G[3] if n > 0.45 else G[2])
    # the garden's bluff on the north bank runs on and sinks into the ground upstream
    for x in range(150, W):
        bh = int((7 + int(smooth_noise(x + OFF, 3, 9, 92) * 3)) * min(1.0, (x - 150) / 150))
        top = int(centre(x) - half(x))
        for k in range(bh):
            y = top - bh + k
            c = G[3] if k == 0 else STONE[3] if (x // 6 + k // 4) % 2 else STONE[2]
            if k == bh - 1:
                c = STONE[1]
            cv.set(x, y, c)
    # dappled light through the canopy
    for i in range(14):
        lx, ly = int(noise2(i, 0, 426) * W), int(noise2(i, 1, 426) * H)
        light_pool(cv, lx, ly, 12 + i % 3 * 4, 6 + i % 2 * 3, GOLDm[2], water)
    light_pool(cv, 110, 140, 44, 26, G[4], water)
    # the stone circle in its own small clearing: a ring of reddish trodden earth round
    # muted grass, the stones standing in it (the reference Matt chose as the bar)
    SX, SY, SRX, SRY = 78, 410, 44, 24
    spur = worlds.thick([(152, 386), (118, 408)], 5, seed=27)
    paint_road(cv, spur)
    for (x, y) in oval(SX, SY, SRX + 8, SRY + 6):
        d = math.hypot((x - SX) / SRX, (y - SY) / SRY)
        if d < 0.72:
            n = smooth_noise(x, y, 9, 428)
            cv.set(x, y, '#86A755' if n > 0.42 else '#76984A')
        elif d < 1.0:
            n = noise2(x // 2, y // 2, 429)
            c = '#AE7E64' if n > 0.35 else '#9A6A52'
            if d < 0.76 and (x + y) % 2:
                c = '#76984A'  # the grass fraying onto the earth
            if d > 0.95 and (x + y) % 2:
                c = '#C29A7E'
            cv.set(x, y, c)
        elif d < 1.12 and (x + y) % 2 == 0:
            cv.set(x, y, '#76984A')
    # where the canopy closes in at the outer edges, the floor goes into deep shade
    # (checker dithering toward FOREST_DARK, style rule 9); the path and the water stay lit
    keep = set(path) | water | rock | set(clearing) | set(oval(SX, SY, SRX + 8, SRY + 6))
    for y in range(H):
        for x in range(W):
            if (x, y) in keep:
                continue
            d = min(x + noise2(x // 6, y // 6, 430) * 10, y + 14 + noise2(x // 6, y // 6, 431) * 10)
            s = 1 - d / 44
            if s >= 0.85 or (s >= 0.6 and ((x + y) % 2 == 0 or (x % 2 == 0 and y % 2 == 0))) \
                    or (s >= 0.35 and (x + y) % 2 == 0) or (s >= 0.12 and x % 2 == 0 and y % 2 == 0):
                cv.set(x, y, style.FOREST_DARK)
    objects = [
        # the stone circle
        ('stone-1', 'standing_stone', SX - 10, SY - SRY - 26), ('stone-2', 'standing_stone_b', SX + 26, SY - SRY - 18),
        ('stone-3', 'standing_stone_low', SX + SRX - 8, SY - 10), ('stone-4', 'standing_stone', SX + 22, SY + SRY - 26),
        ('stone-5', 'standing_stone_b', SX - 34, SY + SRY - 28), ('stone-6', 'standing_stone_low', SX - SRX - 4, SY - 14),
        ('stone-7', 'standing_stone_low', SX - 38, SY - SRY - 12),
        ('stump-1', 'stump', 166, 232), ('stump-2', 'stump', 40, 340), ('stump-3', 'stump', 236, 120),
        ('pine-6', 'pine', -16, 110), ('pine-7', 'pine', 110, -44), ('tree-8', 'tree_small', -26, 380),
        ('bush-2', 'bush', 4, 250), ('bush-3', 'bush', 160, 40), ('fern-5', 'fern', 150, 250),
        # old trees closing in round the edges (none crosses the east border into the garden)
        ('tree-1', 'tree', -20, -30), ('pine-1', 'pine', 50, -40), ('tree-2', 'tree', 200, -26), ('pine-2', 'pine', 250, -36),
        ('tree-3', 'tree', -24, 200), ('pine-3', 'pine', -10, 330), ('tree-4', 'tree', 230, 160),
        ('tree-5', 'tree_small', 196, 300), ('pine-4', 'pine', 20, 470), ('tree-6', 'tree', 60, 480),
        ('pine-5', 'pine', 150, 490), ('tree-7', 'tree_small', 250, 504),
        ('oak', 'hollow_tree', 70, 30), ('ring', 'mushroom_ring', 128, 150), ('log-1', 'mossy_log', 200, 230),
        ('log-2', 'mossy_log', 128, 468), ('fern-1', 'fern', 30, 270), ('fern-2', 'fern', 180, 360),
        ('fern-3', 'fern', 260, 420), ('fern-4', 'fern', 100, 330), ('bench', 'forest_bench', 150, 170),
        ('willow', 'willow', 220, 340), ('bush-1', 'bush', 286, 380),
    ]
    # a split-log footbridge where the path crosses the young stream
    plank = {(x, y) for x in range(122, 140) for y in range(int(centre(130) - half(130)) - 3, int(centre(130) + half(130)) + 4)}
    for (x, y) in plank:
        cv.set(x, y, WOOD[4] if x in (122, 131) else WOOD[3] if x < 131 else WOOD[2])
    for y in range(min(yy for _, yy in plank), max(yy for _, yy in plank) + 1):
        cv.set(140, y, WTRm[0])
    stands = {'garden': (304, meadow.ORCHARD_WALK_Y), 'clearing': (110, 160), 'spring': (100, int(centre(96)) + 18),
              'stones': (SX, SY + 4)}
    return cv, objects, stands, (water | rock) - plank


# Every region is its own place (Matt, 17 Oct: "not just reskins of other worlds"): a
# zone outside the valley draws only its own region's props, plus the few shared
# things below that would really be found anywhere.
REGION_PROPS = {'junction': sp.props, 'canal': sp.props, 'springs': cdp.props, 'home': hp.props, 'neon': cp.props, 'skyport': cp.props, 'gulch': wsp.props, 'oasis': wsp.props, 'caldera': cdp.props, 'harbour': hbp.props, 'hearthold': lambda: {**csp.props(), **cdp.props()}, 'scorch': lambda: {**wsp.props(), **cdp.props()},
                'station': spp.props_station, 'lumen': spp.props_lumen}
SHARED_PROPS = {'steam_puff', 'drone', 'ring_post', 'fence_c'}
# Things above head height: they cast no ground shadow, never block a walk, draw on top.
OVERHEAD = {'steam_puff', 'drone', 'bunting', 'cables', 'dragon'}


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
    # no prop crosses a border into a neighbouring zone (world-atlas.md, "How borders meet")
    region = next(r for r, zs in LAYOUT.items() if name in zs)
    col, row = LAYOUT[region][name]
    near = {pos for pos in LAYOUT[region].values()}
    sides = {'west': (col - 1, row) in near, 'east': (col + 1, row) in near,
             'north': (col, row - 1) in near, 'south': (col, row + 1) in near}
    over = []
    for (oid, key, x, y) in objects:
        if key in OVERHEAD:
            continue
        sp = sprite_map[key]
        # (a tall prop may rise over the north border into the zone behind it, by up to
        # 48 px, as long as nothing stands there: see check_overhangs)
        if (sides['west'] and x < 0) or (sides['east'] and x + sp.w > W) or \
                (sides['north'] and y < -48) or (sides['south'] and y + sp.h > H):
            over.append(f'{oid} at {x},{y} size {sp.w}x{sp.h}')
    assert not over, f'{name}: props cross into a neighbouring zone: {over}'
    out = os.path.join(worlds.ROOT, 'assets', 'zones', name)
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, 'ground.png'), worlds.SCALE)
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
    return {'objects': objects, 'walk': walk, 'stands': stands, 'sprites': sprite_map,
            'ground_img': cv.img.copy(), 'blocked': blocked_ground, 'preview': prev.img if prev else None,
            'water': WATER_MASKS.get(fn.__name__)}


# Buildings whose door faces the viewer, and where the door sits across the sprite
# (a fraction of its width).
DOORS = {k: 0.5 for k in ('house_blue', 'house_red', 'cabin', 'cafe', 'library', 'workshop', 'workshop_round',
                          'station_house', 'barn', 'bathhouse', 'foundry', 'tube_station', 'cottage', 'cottage_b',
                          'saloon', 'store', 'mine_portal', 'clock_tower', 'lookout_tower')}


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
    'neon': {'neon': (0, 0), 'skyport': (1, 0)}, 'space': {'station': (0, 0)}, 'moon': {'lumen': (0, 0)}, 'home': {'home': (0, 0)},
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
    import world_lint
    placement = {k: t for t, ks in (('floating', world_lint.FLOATING), ('wet', world_lint.WET),
                                     ('supported', world_lint.SUPPORTED), ('overhead', OVERHEAD)) for k in sorted(ks) if k in used}
    lines += [
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
    built['neon'] = build('neon', neon_city, 'crossing')
    built['skyport'] = build('skyport', skyport, 'neon')
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
    import frames  # places meet only at their ports (Codex's connected-world contract)
    frames.check(built, LAYOUT)
    import world_lint  # the world's logic lint (world-rules.md, section 7): report only, for now
    world_lint.run(built, LAYOUT, None, OVERHEAD, {z: b['preview'] for z, b in built.items() if b['preview'] is not None})
    import map_tiles  # the world map's tiles, drawn from the same reading of each zone
    map_tiles.write_all(built, world_lint.garden_zone(), set(DOORS))
    export(built)


if __name__ == '__main__':
    main()

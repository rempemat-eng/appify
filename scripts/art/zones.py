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

import json
import math
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import garden_meadow as meadow  # noqa: E402
import garden_props as gp  # noqa: E402
import style  # noqa: E402
import world_props as wp  # noqa: E402
import worlds  # noqa: E402
from materials import G, P, STONE, WOOD, SLATE, RED, MATERIALS  # noqa: E402
import valley_props as vp  # noqa: E402
import steampunk_props as sp  # noqa: E402
import cyber_props as cp  # noqa: E402
import western_props as wsp  # noqa: E402
import caldera_props as cdp  # noqa: E402
import harbour_props as hbp  # noqa: E402
import castle_props as csp  # noqa: E402
import space_props as spp  # noqa: E402

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
    detail.grass_edge(cv, set(mask), G, P, seed=11)  # pixels past any edge count as road too
    for (x, y) in mask:
        if (x, y + 1) not in mask and 0 <= y + 1 < H:
            cv.set(x, y + 1, G[3])


def town(frame: int = 0):
    cv = Canvas(W, H)
    worlds.grass(cv, frame)
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
        ('pine-n3', 'pine', 200, 2), ('tree-n4', 'tree_autumn', 228, 12), ('pine-n5', 'pine', 288, 8),
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
        ('hedge-s1', 'hedge', 0, 548), ('hedge-s3', 'hedge', 192, 548),
        ('tree-w1', 'tree', 2, 196), ('tree-e1', 'tree', 252, 470),
        ('bush-e2', 'bush', 286, 228), ('bush-w4', 'bush', 250, 400),
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


def sprites() -> dict[str, Canvas]:
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
    items['fence_c'] = gp.fence_h(60)
    return {key: style.finalize(sp, name=key) for key, sp in items.items()}


# Props with a way through them: (from, to) in sprite pixels.
OPENINGS = {'gatehouse': (50, 72), 'sandstone_arch': (20, 44), 'ticket_gates': (4, 80)}


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


def grate(cv: Canvas, x0: int, y0: int, w: int = 12, h: int = 8):
    """An iron grate over a steam vent: a lit frame and dark slots."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
            cv.set(x, y, (IRON[3] if (x == x0 or y == y0) else IRON[1]) if edge else (IRON[0] if (x - x0) % 2 else IRON[2]))


def gear_ring(cv: Canvas, cx: int, cy: int, rx: int, ry: int):
    """The junction's sparring ring: an iron floor plate with a toothed brass rim."""
    plate = oval(cx, cy, rx, ry)
    for (x, y) in plate:
        k = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        a = math.atan2((y - cy) / ry, (x - cx) / rx)
        spoke = int((a + math.pi) / (2 * math.pi) * 12) % 2
        c = IRON[4] if k < 0.12 else (IRON[3] if spoke else IRON[2])
        if 0.55 < k < 0.68:
            c = BRASS[2]
        if (x - cx) + (y - cy) * 2 < -rx * 0.9 and k > 0.7:
            c = IRON[4]
        cv.set(x, y, c)
    for k in range(40):
        a = 2 * math.pi * k / 40
        for t in range(4):
            x = int(cx + (rx + 1 + t) * math.cos(a))
            y = int(cy + (ry + 1 + t * 0.5) * math.sin(a))
            if k % 2 == 0:
                cv.set(x, y, BRASS[4] if math.sin(a) < 0 else BRASS[2])
    for (x, y) in plate:
        if (x, y + 1) not in plate:
            cv.set(x, y + 1, BRASS[1])
    for (x, y) in disc(cx, cy, 5):
        cv.set(x, y, BRASS[3] if x < cx else BRASS[2])


def junction(frame: int = 0):
    """Cogsworth Junction: the train from the valley stands at the platform, the
    square below has the clock tower and the tinkerers' workshops, pipes and steam
    vents, and the gear ring at the bottom. The rails run on east toward Dust Gulch."""
    cv = Canvas(W, H)
    worlds.grass(cv, frame, ['#2B3B2E', '#46583F', '#5C6E4C', '#6B7C55', '#8E9C6E'])  # sooty grass
    # north of the line: a soot-dark yard behind a wall
    for y in range(0, 76):
        for x in range(W):
            n = noise2(x, y, 151)
            cv.set(x, y, IRON[1] if n > 0.6 else IRON[2] if n > 0.2 else STONE[1])
    detail.bricks(cv, 0, 62, W, 14, BRICK, seed=9, base=3)
    cv.hline(0, 62, W, BRICK[4])
    paint_rails(cv, 82)
    # the platform: stone slabs with a painted edge
    plat = {(x, y) for x in range(W) for y in range(100, 134)}
    worlds.paint_paving(cv, plat, seed=7)
    cv.hline(0, 100, W, '#E8C860'); cv.hline(0, 101, W, '#B8962E')
    for x in range(0, W):
        cv.set(x, 134, STONE[1]); cv.set(x, 135, STONE[2])
    # the cobbled square and lanes
    # cobbled streets fill the town; the meadow only returns round the ring
    square = {(x, y) for x in range(W) for y in range(136, 436)
              if y < 420 + int(noise2(x // 8, 1, 152) * 16) - (12 if x < 30 or x > 290 else 0)}
    lane = worlds.thick([(160, 430), (160, 468)], 16)
    worlds.paint_cobbles(cv, square | lane)
    for (x, y) in square | lane:  # a kerb of dressed stone where the cobbles meet the grass
        if (x, y + 1) not in square and (x, y + 1) not in lane and y + 1 < H:
            cv.set(x, y, STONE[3]); cv.set(x, y + 1, STONE[1])
    for (gx, gy) in ((70, 190), (238, 196), (110, 360), (214, 372)):
        grate(cv, gx, gy)
    # the lane on south through the gap in the pipe wall, down to the canal
    south = {(x, y) for x in range(144, 176) for y in range(500, H + 4)}
    worlds.paint_cobbles(cv, south)
    for y in range(500, H):
        cv.set(143, y, STONE[3]); cv.set(142, y, STONE[1]); cv.set(176, y, STONE[1]); cv.set(177, y, STONE[3])
    gear_ring(cv, 160, 492, 56, 24)
    objects = [
        # the far side of the line: chimneys and pipes over the wall
        ('ws-far-1', 'workshop_round', 10, -26), ('ws-far-2', 'workshop', 200, -24),
        ('pipes-far', 'pipe_run', 104, 48),
        # the train at the platform, steam from its stack
        ('engine', 'locomotive', 96, 50), ('puff-engine', 'steam_puff', 112, 34),
        # the platform
        ('lamp-p1', 'gas_lamp', 40, 92), ('lamp-p2', 'gas_lamp', 264, 92), ('bench-p', 'iron_bench', 208, 104),
        ('trunk-p1', 'steamer_trunk', 14, 112), ('trunk-p2', 'steamer_trunk', 30, 118), ('coal-p', 'coal_cart', 284, 110),
        # the square
        ('ws-left', 'workshop', 4, 150), ('ws-right', 'workshop', 220, 150),
        ('tower', 'clock_tower', 136, 176),
        ('lamp-s1', 'gas_lamp', 112, 280), ('lamp-s2', 'gas_lamp', 196, 280),
        ('gears-1', 'gear_pile', 96, 228), ('pipes-1', 'pipe_run', 236, 252),
        ('puff-c1', 'steam_puff', 66, 132), ('puff-c2', 'steam_puff', 282, 132),
        ('ws-low', 'workshop_round', 6, 320), ('coal-1', 'coal_cart', 90, 384),
        ('trunk-2', 'steamer_trunk', 280, 396), ('pipes-2', 'pipe_run', 240, 410),
        ('puff-v3', 'steam_puff', 206, 352), ('kiosk', 'tea_kiosk', 250, 300),
        # round the ring
        ('lamp-r1', 'gas_lamp', 92, 470), ('lamp-r2', 'gas_lamp', 216, 470), ('bench-r', 'iron_bench', 22, 486),
        ('mast', 'airship_mast', 214, 412),
        ('wall-s1', 'pipe_run', 0, 556), ('wall-s2', 'pipe_run', 64, 556), ('wall-s3', 'pipe_run', 192, 556),
        ('wall-s4', 'pipe_run', 256, 556),
    ]
    stands = {'platform': (160, 120), 'tower': (160, 322), 'ring': (160, 492), 'workshop': (52, 248),
              'canal': (160, 568)}
    return cv, objects, stands


def canal(frame: int = 0):
    """Cogsworth Canal, south of the junction: the working side of the town. The lane
    comes down through the gap in the pipe wall between two warehouses to a towpath of
    setts, crosses the canal on an iron bridge, and runs on between the foundry (its
    sawtooth roof glowing, its great door open on the pour) and the terminus of the
    atmospheric railway, Cogsworth's brass-and-glass end of the maglev from Neon
    Harbour. A steam narrowboat is moored by a jib crane; a lock with black-and-white
    balance beams steps the water up to the east. At the bottom the tinkerers keep
    allotments warmed by the foundry's waste steam, tended by a clockwork gardener."""
    ASHLAR = MATERIALS['ashlar']
    cv = Canvas(W, H)
    worlds.grass(cv, frame, ['#2B3B2E', '#46583F', '#5C6E4C', '#6B7C55', '#8E9C6E'])  # the junction's sooty grass
    blocked = set()
    CY0, CY1 = 176, 244  # the canal's water, between its embankments
    # towpaths of setts either side of the canal, and the lane
    towpath = {(x, y) for x in range(W) for y in range(126, CY0)} | {(x, y) for x in range(W) for y in range(CY1, 292)}
    lane = {(x, y) for x in range(144, 176) for y in range(-4, 430)}
    worlds.paint_cobbles(cv, (towpath | lane) - {(x, y) for x in range(W) for y in range(CY0, CY1)})
    for y in range(0, 126):  # the lane's kerbs, as in the junction
        cv.set(143, y, STONE[3]); cv.set(142, y, STONE[1]); cv.set(176, y, STONE[1]); cv.set(177, y, STONE[3])
    for y in range(292, 430):
        cv.set(143, y, STONE[3]); cv.set(142, y, STONE[1]); cv.set(176, y, STONE[1]); cv.set(177, y, STONE[3])
    for x in range(W):  # dressed kerbs where the setts meet the grass
        cv.set(x, 125, STONE[3]); cv.set(x, 292, STONE[3]); cv.set(x, 293, STONE[1])
    # the canal: embankment faces in ashlar, murky green water, lamps doubled in it
    for x in range(W):
        for y in range(CY0, CY1):
            k = y - CY0
            if k < 6:
                c = ASHLAR[1] if (x // 7 + k // 3) % 2 else ASHLAR[2]  # the north wall's face, in shade
                if k == 0:
                    c = ASHLAR[4]
            else:
                n = smooth_noise(x, y, 8, 494)
                c = '#2C4A44' if n > 0.6 else '#22403A' if n > 0.3 else '#1A3430'
                if k < 9:
                    c = '#14281F'  # the wall's shadow on the water
                if (y - CY0) % 6 == 2 and noise2(x // 7, y, 495) > 0.62:
                    c = '#3E6A5E'
            cv.set(x, y, c)
            blocked.add((x, y))
        cv.set(x, CY1, ASHLAR[5]); cv.set(x, CY1 + 1, ASHLAR[3])  # the south coping, lit
        cv.set(x, CY0 - 1, ASHLAR[3])
    for lx in (40, 120, 200, 280):  # lamplight on the water
        for y in range(CY0 + 10, CY1 - 2, 2):
            if noise2(lx, y // 2, 496) > 0.35:
                cv.hline(lx - 2 + int((noise2(y, lx, 497) - 0.5) * 4), y, 4, '#C99A3C' if y % 4 else '#9E6C26')
    # the lock: the chamber's water stands higher (lighter) between two pairs of mitre gates
    for x in range(236, 296):
        for y in range(CY0 + 6, CY1):
            c = cv.get(x, y)
            cv.set(x, y, tuple(min(255, v + 14) for v in c[:3]) + (255,))
    for gx in (234, 296):
        for t in range(CY1 - CY0 - 6):  # gates meeting in a V that points upstream (east)
            y = CY0 + 6 + t
            off = int(abs(t - (CY1 - CY0 - 6) / 2) * 0.35)
            for d in range(4):
                cv.set(gx + off + d, y, WOOD[3] if d < 2 else WOOD[1])
        cv.hline(gx, CY0 + 6, 4, WOOD[4])
        for (by, side) in ((CY0 - 30, -1), (CY1 + 6, 1)):  # balance beams on the towpaths, black and white
            for x in range(gx - 26, gx + 4):
                for y in range(by + (0 if side < 0 else 0), by + 5):
                    c = '#F2F0EA' if ((x - gx) // 6) % 2 else '#1E1C22'
                    if y == by:
                        c = '#FFFFFF' if c == '#F2F0EA' else '#3A3840'
                    cv.set(x, y, c)
                    blocked.add((x, y))
    # the iron bridge carrying the lane over the water
    for y in range(CY0 - 2, CY1 + 2):
        for x in range(138, 182):
            if x < 142 or x >= 178:
                c = IRON[3] if x in (138, 178) else IRON[1]  # the girders
                if (y - CY0) % 8 == 0:
                    c = BRASS[3]  # rivet plates
            else:
                c = WOOD[3] if (y // 3) % 2 else WOOD[2]
                if (x - 142) % 12 == 0:
                    c = WOOD[1]
            cv.set(x, y, c)
            blocked.discard((x, y))
    # the atmospheric railway's brass tube, east from the terminus on iron trestles
    for x in range(272, W):
        for y in range(340, 356):
            k = (y - 340) / 16
            c = BRASS[4] if k < 0.2 else BRASS[3] if k < 0.5 else BRASS[2] if k < 0.85 else BRASS[1]
            if (x - 38 - 196) % 10 == 0:
                c = IRON[1]
            cv.set(x, y, c)
            blocked.add((x, y))
        if x % 24 == 8:
            for y in range(356, 372):
                cv.set(x, y, IRON[3]); cv.set(x + 1, y, IRON[1])
                blocked.add((x, y))
        cv.set(x, 372, '#2B3B2E')
    # the forecourt before the foundry's door: setts black with spilt slag, lit orange
    fore = {(x, y) for x in range(24, 144) for y in range(404, 430)}
    worlds.paint_cobbles(cv, fore)
    for (x, y) in fore:
        if noise2(x // 4, y // 3, 498) > 0.72:
            cv.set(x, y, IRON[1])  # spilt slag
        if y == 429:
            cv.set(x, y, STONE[1])
    light_pool(cv, 72, 412, 52, 18, '#FFB648')
    # the allotments: raised beds of dark earth in rows, sprouts, gravel paths between
    beds = [(16, 452, 56, 26), (16, 500, 56, 26), (88, 452, 48, 26), (88, 500, 48, 26),
            (190, 452, 52, 26), (190, 500, 52, 26), (256, 452, 50, 26), (256, 500, 50, 26)]
    for y in range(436, 548):
        for x in range(8, 314):
            n = noise2(x // 2, y // 2, 499)
            cv.set(x, y, '#8C8576' if n > 0.6 else '#76705F' if n > 0.25 else '#9C9584')
    for (bx, by, bw, bh) in beds:
        for y in range(by, by + bh):
            for x in range(bx, bx + bw):
                c = '#3A2A22' if (y - by) % 6 else '#2A1E18'
                if (y - by) % 6 == 3 and (x * 7 + y) % 9 < 3:
                    c = '#62995E' if (x + y) % 2 else '#447A50'  # sprouts
                cv.set(x, y, c)
        for x in range(bx - 1, bx + bw + 1):  # timber edging, lit on top
            cv.set(x, by - 1, WOOD[4]); cv.set(x, by + bh, WOOD[1])
        for y in range(by, by + bh):
            cv.set(bx - 1, y, WOOD[3]); cv.set(bx + bw, y, WOOD[1])
    objects = [
        # warehouses either side of the lane at the top
        ('wh-1', 'workshop_round', 20, 22), ('wh-2', 'workshop', 204, 18),
        ('lamp-1', 'gas_lamp', 124, 96), ('lamp-2', 'gas_lamp', 184, 96),
        # the north towpath: the crane and the moored boat
        ('crane', 'canal_crane', 70, 112), ('boat', 'narrowboat', 8, 186), ('trunk-1', 'steamer_trunk', 30, 150),
        ('coal-1', 'coal_cart', 112, 140), ('lamp-3', 'gas_lamp', 290, 130),
        # the south towpath
        ('bench-t', 'iron_bench', 60, 262), ('lamp-4', 'gas_lamp', 124, 252), ('gears-t', 'gear_pile', 290, 256),
        # the foundry and the terminus
        ('foundry', 'foundry', 0, 296), ('puff-f1', 'steam_puff', 16, 278), ('puff-f2', 'steam_puff', 112, 284),
        ('station', 'tube_station', 196, 300), ('car', 'atmos_car', 252, 318),
        # the allotments
        ('pipe-a1', 'pipe_run', 8, 548), ('pipe-a2', 'pipe_run', 72, 548), ('pipe-a3', 'pipe_run', 184, 548),
        ('pipe-a4', 'pipe_run', 248, 548),
        ('gardener', 'automaton', 140, 476), ('cloche-1', 'cloche', 30, 460), ('cloche-2', 'cloche', 48, 508),
        ('cloche-3', 'cloche', 100, 462), ('cloche-4', 'cloche', 270, 510), ('cloche-5', 'cloche', 206, 458),
        ('bench-a', 'iron_bench', 186, 418), ('lamp-5', 'gas_lamp', 248, 410), ('kiosk-a', 'tea_kiosk', 270, 396),
    ]
    stands = {'junction': (160, 6), 'bridge': (160, 210), 'boat': (60, 166), 'lock': (264, 150),
              'foundry': (72, 418), 'terminus': (236, 384), 'allotments': (162, 520)}
    return cv, objects, stands, blocked


def neon_city(frame: int = 0):
    """Neon Harbour at its permanent dusk: tower blocks with neon signs along the north
    side of a wet street, a crossing, food stalls and vending machines on the south
    pavement, a neon-lined court for sparring, and the quay where the city meets the
    dark harbour water, every light doubled in puddles and in the water."""
    NIGHT, PINK, CYAN, AMBER = (MATERIALS[k] for k in ('night', 'neon_pink', 'neon_cyan', 'neon_amber'))
    cv = Canvas(W, H)
    # pavements: square tiles, lit on top
    for y in range(H):
        for x in range(W):
            tx, ty = x % 10, y % 10
            n = noise2(x // 10, y // 10, 181)
            c = NIGHT[3] if n > 0.5 else NIGHT[2]
            if tx == 0 or ty == 0:
                c = NIGHT[1]
            elif ty == 1:
                c = NIGHT[4] if n > 0.5 else NIGHT[3]
            cv.set(x, y, c)
    # the street: wet asphalt with a lane line and a crossing
    for y in range(156, 228):
        for x in range(W):
            n = noise2(x // 2, y // 2, 182)
            cv.set(x, y, NIGHT[1] if n > 0.3 else NIGHT[0])
    for x in range(0, W, 16):
        cv.hline(x, 191, 9, AMBER[2])
    for x in range(140, 184, 8):
        for y in range(160, 224):
            cv.hline(x, y, 5, '#C9C6D8' if y % 2 else '#B3AFC6')
    for x in range(W):  # kerbs
        cv.set(x, 155, NIGHT[4]); cv.set(x, 154, NIGHT[5]); cv.set(x, 228, NIGHT[4])
    # reflections of the signs and windows in the wet street (vertical streaks)
    for (sx, ramp) in ((103, PINK), (205, CYAN), (303, AMBER)):
        for y in range(160, 226):
            if noise2(sx, y // 3, 183) > 0.35:
                for dx in range(-2, 3):
                    if abs(dx) < 2 or y % 2:
                        cv.set(sx + dx + int((noise2(y, sx, 184) - 0.5) * 2), y, ramp[1] if abs(dx) else ramp[2])
    for (px, py, r) in ((40, 200, 10), (250, 176, 8), (90, 300, 9), (226, 316, 7)):  # puddles
        for (x, y) in oval(px, py, r, r * 0.45):
            cv.set(x, y, NIGHT[0] if (x + y) % 5 else CYAN[1])
        cv.hline(px - r // 2, py - 1, r // 2, PINK[2])
    # the sparring court: a neon ring painted on the ground
    ccx, ccy = 160, 382
    for (x, y) in oval(ccx, ccy, 62, 28):
        cv.set(x, y, NIGHT[2] if (x // 6 + y // 6) % 2 else NIGHT[3])
    for k in range(240):
        a = 2 * math.pi * k / 240
        for (rx, ry, ramp) in ((62, 28, CYAN), (40, 18, PINK)):
            x, y = int(ccx + rx * math.cos(a)), int(ccy + ry * math.sin(a))
            cv.set(x, y, ramp[3]); cv.set(x, y + 1, ramp[1])
    cv.hline(ccx - 2, ccy - 18, 5, PINK[3]); cv.vline(ccx, ccy - 18, 37, PINK[2])
    # the quay and the harbour water
    for y in range(470, H):
        for x in range(W):
            n = smooth_noise(x, y, 9, 185)
            c = '#0E1626' if n > 0.55 else '#121C30' if n > 0.3 else '#0B1220'
            if (y - 470) % 7 == 3 and noise2(x // 9, y, 186) > 0.6:
                c = '#22304C'
            cv.set(x, y, c)
    for (sx, ramp) in ((60, PINK), (150, AMBER), (262, CYAN)):
        for y in range(474, H, 2):
            wob = int((noise2(y, sx, 187) - 0.5) * 6)
            cv.hline(sx + wob - 3, y, 6 + wob % 3, ramp[2] if y % 4 else ramp[1])
    for x in range(W):
        cv.set(x, 466, NIGHT[4]); cv.set(x, 467, NIGHT[3]); cv.set(x, 468, NIGHT[1]); cv.set(x, 469, '#070B14')
    for bx in range(14, W, 44):  # bollards with a yellow band
        for (x, y) in disc(bx, 460, 3):
            cv.set(x, y, NIGHT[4] if x < bx else NIGHT[2])
        cv.hline(bx - 2, 460, 5, AMBER[3])
    for (lx, ly, rx, ry, col) in ((60, 150, 30, 12, CYAN[2]), (268, 152, 30, 12, CYAN[2]),
                                  (46, 352, 28, 12, CYAN[2]), (276, 356, 28, 12, CYAN[2]),
                                  (44, 290, 40, 14, AMBER[2]), (280, 290, 40, 14, AMBER[2]),
                                  (112, 290, 26, 10, CYAN[1]), (60, 150, 46, 8, PINK[1]),
                                  (164, 152, 46, 8, CYAN[1]), (264, 152, 46, 8, AMBER[1]),
                                  (160, 382, 70, 32, PINK[0]), (218, 290, 24, 10, CYAN[1])):
        light_pool(cv, lx, ly, rx, ry, col)
    objects = [
        ('tower-1', 'tower_pink', 0, 6), ('tower-2', 'tower_cyan', 116, 20), ('tower-3', 'tower_amber', 214, 14),
        ('light-1', 'street_light', 54, 100), ('light-2', 'street_light', 262, 102),
        ('stall-1', 'noodle_stall', 8, 236), ('vend-1', 'vending_machine', 90, 252), ('vend-2', 'vending_machine', 116, 252),
        ('holo-1', 'holo_board', 196, 238), ('stall-2', 'noodle_stall', 244, 236),
        ('light-3', 'street_light', 40, 300), ('light-4', 'street_light', 270, 304), ('pole-1', 'cable_pole', 150, 236),
        ('vend-3', 'vending_machine', 22, 392), ('holo-2', 'holo_board', 266, 360),
        ('drone-1', 'drone', 92, 140), ('drone-2', 'drone', 230, 330), ('drone-3', 'drone', 120, 440),
        ('boxes-q', 'containers', 252, 404), ('shelter-q', 'shelter', 70, 412), ('plant-q1', 'uv_planter', 4, 300),
        ('plant-q2', 'uv_planter', 290, 260), ('ferry', 'ferry', 120, 490),
    ]
    stands = {'crossing': (160, 192), 'stalls': (60, 300), 'court': (160, 382), 'quay': (160, 452)}
    return cv, objects, stands


def skyport(frame: int = 0):
    """The Skyport, east of Neon Harbour: where the city's noise stops. Neon Harbour's
    wet street runs in from the west and ends at a quiet drop-off loop round a tree;
    the dark tiles give way to pale polished slabs that hold the lights like still
    water. Along the north the maglev to Cogsworth waits at its platform on a white
    guideway (stairs down to the street); in the south a concourse with departure
    pylons, benches, a living tree or two and a row of ticket gates leads to the quay,
    and a pier runs out to the anchor in the harbour, where the space elevator's ribbon
    climbs out of sight toward Halcyon. Calmer and brighter than the street: the way
    up and out."""
    NIGHT, PINK, CYAN, AMBER = (MATERIALS[k] for k in ('night', 'neon_pink', 'neon_cyan', 'neon_amber'))
    PORC = cp.PORCELAIN
    cv = Canvas(W, H)
    blocked = set()
    # the floor: Neon's dark tiles at the west edge, giving way to pale polished slabs
    for y in range(H):
        for x in range(W):
            tx, ty = (x + W) % 10, y % 10
            n = noise2((x + W) // 10, y // 10, 181)
            dark = NIGHT[3] if n > 0.5 else NIGHT[2]
            if tx == 0 or ty == 0:
                dark = NIGHT[1]
            elif ty == 1:
                dark = NIGHT[4] if n > 0.5 else NIGHT[3]
            sx, sy = x % 24, y % 16
            m = noise2(x // 24, y // 16, 492)
            pale = PORC[2] if m > 0.45 else PORC[1]
            if sx == 0 or sy == 0:
                pale = PORC[0]
            elif sy == 1:
                pale = PORC[3] if m > 0.45 else PORC[2]
            if (x // 24 + y // 16) % 5 == 0 and sy == 8:
                pale = CYAN[1]  # a cyan inlay line now and then
            k = (x - 8) / 48  # the change over the first 56 pixels, in an ordered dither by whole tiles
            bayer = (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)[((y // 16) % 4) * 4 + (x // 12) % 4] / 16
            cv.set(x, y, dark if k < 0 or (k < 1 and bayer >= k) else pale)
    # Neon Harbour's street, continued, ending at a drop-off loop
    LX, LY = 238, 192
    loop = {(x, y) for (x, y) in oval(LX, LY, 66, 44)}
    island = {(x, y) for (x, y) in oval(LX, LY, 32, 18)}
    street = {(x, y) for y in range(156, 228) for x in range(0, LX)} | loop
    for (x, y) in street:
        if (x, y) in island:
            continue
        n = noise2((x + W) // 2, y // 2, 182)
        cv.set(x, y, NIGHT[1] if n > 0.3 else NIGHT[0])
    for x in range(0, LX - 60, 16):
        cv.hline(x, 191, 9, AMBER[2])
    for (x, y) in street:  # kerbs
        if (x, y) in island:
            continue
        if (x, y - 1) not in street:
            cv.set(x, y - 1, NIGHT[4]); cv.set(x, y - 2, NIGHT[5])
        if (x, y + 1) not in street:
            cv.set(x, y + 1, NIGHT[4])
    for (x, y) in island:  # the island: a ring of moss round the tree
        d = math.hypot((x - LX) / 32, (y - LY) / 18)
        cv.set(x, y, PORC[4] if d > 0.88 else '#2E5A40' if (x + y) % 3 else '#447A50')
    for (sx, ramp) in ((60, CYAN), (150, AMBER)):  # the lights in the wet road
        for y in range(160, 226):
            if noise2(sx, y // 3, 183) > 0.4:
                cv.hline(sx - 1 + int((noise2(y, sx, 184) - 0.5) * 2), y, 3, ramp[1])
    # the terminal's glass roof along the top
    for y in range(0, 34):
        for x in range(W):
            c = NIGHT[2] if (x // 20 + y // 12) % 2 else NIGHT[1]
            if x % 20 == 0 or y % 12 == 0:
                c = PORC[2]
            if y == 33:
                c = PORC[4]
            cv.set(x, y, c)
    # the guideway: a white deck with a cyan strip, its face in shade
    for y in range(34, 66):
        for x in range(W):
            if y < 58:
                c = PORC[3] if y < 40 else PORC[2]
                if 45 <= y <= 46:
                    c = CYAN[2]
            else:
                c = PORC[1] if y < 64 else PORC[0]
            cv.set(x, y, c)
            blocked.add((x, y))
    for x in range(0, 6):  # the buffer and the glass wall at the platform's west end
        for y in range(34, 100):
            cv.set(x, y, PORC[4] if x < 2 else CYAN[0])
            blocked.add((x, y))
    # the platform: pale slabs, a yellow edge strip, its front face, stairs down
    PLAT = 212
    for y in range(66, 100):
        for x in range(6, PLAT):
            c = PORC[3] if (x // 16 + y // 12) % 2 else PORC[4]
            if y in (68, 69):
                c = AMBER[3] if x % 3 else AMBER[2]
            if y >= 96:
                c = PORC[1] if y < 99 else PORC[0]
                if not 92 <= x < 124:
                    blocked.add((x, y))
            cv.set(x, y, c)
    for y in range(96, 152):  # the stairs
        for x in range(92, 124):
            c = PORC[4] if (y - 96) % 5 < 2 else PORC[2]
            if x in (92, 123):
                c = PORC[1]
            cv.set(x, y, c)
    for x in range(PLAT, W):  # under the guideway east of the platform: shade, and piers
        for y in range(66, 152):
            if (x + y) % 2 and y < 80:
                style.darken(cv, x, y)
    for px0 in (232, 288):
        for y in range(66, 152):
            for x in range(px0, px0 + 12):
                cv.set(x, y, PORC[3] if x < px0 + 3 else PORC[2] if x < px0 + 9 else PORC[1])
                if y > 140:
                    blocked.add((x, y))
    # the harbour: Neon's water continues, the anchor's light in it
    water = set()
    for y in range(470, H):
        for x in range(W):
            n = smooth_noise(x + W, y, 9, 185)
            c = '#0E1626' if n > 0.55 else '#121C30' if n > 0.3 else '#0B1220'
            if (y - 470) % 7 == 3 and noise2((x + W) // 9, y, 186) > 0.6:
                c = '#22304C'
            cv.set(x, y, c)
            water.add((x, y))
    for x in range(W):
        cv.set(x, 466, NIGHT[4]); cv.set(x, 467, NIGHT[3]); cv.set(x, 468, NIGHT[1]); cv.set(x, 469, '#070B14')
    AX, AY = 248, 528
    pier = {(x, y) for y in range(462, 506) for x in range(230, 268)}
    ring = {(x, y) for (x, y) in oval(AX, AY, 58, 28)}
    for y in range(470, H, 2):  # the ribbon's glow doubled in the water
        for x in range(AX - 8, AX + 9):
            if (x, y) not in ring and noise2(x // 2, y, 493) > 0.45:
                cv.set(x, y, CYAN[1] if abs(x - AX) < 4 else '#16324A')
    for (x, y) in pier:
        c = PORC[3] if (y // 8) % 2 else PORC[2]
        if x in (230, 231, 266, 267):
            c = PORC[5] if x in (230, 231) else PORC[1]  # rails
        cv.set(x, y, c)
    for (x, y) in ring:
        d = math.hypot((x - AX) / 58, (y - AY) / 28)
        c = PORC[4] if d < 0.3 else PORC[2] if d < 0.62 else PORC[3] if d < 0.9 else PORC[1]
        if 0.64 < d < 0.7 or 0.32 < d < 0.36:
            c = CYAN[3] if (x + y) % 2 else CYAN[2]
        if d > 0.94 and y > AY:
            c = PORC[0]  # the platform's side above the water
        cv.set(x, y, c)
    for bx in (46, 90, 134, 178, 310):  # bollards, on Neon's spacing
        for (x, y) in disc(bx, 460, 3):
            cv.set(x, y, NIGHT[4] if x < bx else NIGHT[2])
        cv.hline(bx - 2, 460, 5, AMBER[3])
    for (lx, ly, rx, ry, col) in ((AX, AY, 70, 34, CYAN[2]), (60, 84, 50, 14, AMBER[4]), (160, 84, 50, 14, AMBER[4]),
                                  (140, 300, 60, 22, CYAN[4]), (40, 410, 34, 12, AMBER[3]), (150, 420, 34, 12, AMBER[3]),
                                  (LX, LY, 40, 24, AMBER[3]), (AX, 400, 30, 60, CYAN[3])):
        light_pool(cv, lx, ly, rx, ry, col, skip=frozenset(water - ring - pier))
    blocked |= water - ring - pier
    objects = [
        ('maglev', 'maglev', 26, 26), ('pylon-p', 'departure_pylon', 160, 40), ('light-p', 'street_light', 30, 40),
        ('tree-loop', 'pod_tree', LX - 18, LY - 40), ('tree-1', 'pod_tree', 280, 236), ('tree-2', 'pod_tree', 4, 236),
        ('pylon-1', 'departure_pylon', 60, 240), ('pylon-2', 'departure_pylon', 180, 240),
        ('gates', 'ticket_gates', 64, 316), ('bench-1', 'sky_bench', 14, 400), ('bench-2', 'sky_bench', 124, 400),
        ('tree-3', 'pod_tree', 176, 372), ('tree-4', 'pod_tree', 284, 380), ('bot-1', 'luggage_bot', 150, 440),
        ('bot-2', 'luggage_bot', 200, 300), ('tether', 'tether', AX - 20, AY - 254),
        ('drone-1', 'drone', 120, 140), ('drone-2', 'drone', 290, 300),
    ]
    stands = {'neon': (10, 192), 'platform': (70, 84), 'gates': (104, 360), 'anchor': (AX, AY + 14)}
    return cv, objects, stands, blocked


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


def mesa_face(cv: Canvas, edge, top_ramp, face_ramp, face_h: int = 22):
    """A sandstone cliff: for each row the cliff's western edge x = edge(y); the mesa
    top lies east of it (lit, with scrub), the face runs down-left as banded strata,
    each band lit on its upper edge, with a shadow on the ground at its foot."""
    for y in range(H):
        ex = edge(y)
        if ex is None:
            continue
        for x in range(ex, W):
            n = smooth_noise(x, y, 9, 221)
            cv.set(x, y, top_ramp[4] if n > 0.62 else top_ramp[3])
        for k in range(face_h):  # the face is drawn below and left of the rim
            x = ex - 1 - k // 4
            yy = y + k
            if not (0 <= yy < H) or x < 0:
                continue
            band = (k + int(noise2(y // 7, 3, 222) * 3)) // 4
            c = face_ramp[3] if band % 2 else face_ramp[2]
            if (k + int(noise2(y // 7, 3, 222) * 3)) % 4 == 0:
                c = face_ramp[4]
            if k > face_h - 4:
                c = face_ramp[1]
            cv.set(x, yy, c)
        for d in range(1, 4):  # shadow at the foot, down and to the right of the face
            x = ex - 1 - (face_h // 4) - d
            if 0 <= x < W:
                style.darken(cv, x, y + face_h // 2)


GULCH_STREET = [(130, 78), (128, 200), (136, 300), (130, 420), (110, 500), (60, 540), (-40, 552)]
GULCH_CREEK = [(-14, 342), (40, 336), (96, 326), (120, 320), (176, 312), (230, 336), (246, 360)]


def wagon_ruts(cv: Canvas, road: set, xs, ramp):
    """Two wheel ruts along a road that runs east to west, following its centre in each
    column (so they continue across a border where the road does)."""
    for x in xs:
        ys = [y for y in range(H) if (x, y) in road and y > 440]
        if not ys:
            continue
        mid = (min(ys) + max(ys)) // 2
        for ry in (mid - 6, mid + 6):
            if noise2(x // 3, ry, 229) > 0.15:
                cv.set(x, ry, ramp[1])
        if x % 7 == 0:
            cv.set(x, mid + (2 if (x // 7) % 2 else -2), ramp[0])  # hoof prints


def gulch(frame: int = 0):
    """Dust Gulch, its own place: a town strung along one street that runs down from the
    railway's end, under a sandstone mesa on the east with the old mine cut into its
    foot. A dry creek bed of cracked mud winds across (the reason the well ran dry),
    crossed by a plank bridge; the water tower and windpump stand by it, still hoping.
    The corral sits under the cliff, and the wagon track leaves west for the oasis, along the creek's old line."""
    DESERT, ADOBE = MATERIALS['desert'], MATERIALS['adobe']
    BLEACHED = wsp.BLEACHED
    cv = Canvas(W, H)
    for y in range(H):  # sand with wind ripples, darker drifts dithered in
        for x in range(W):
            n = smooth_noise(x, y, 26, 211)
            c = DESERT[3]
            if n < 0.3 or (n < 0.36 and (x + y) % 2):
                c = DESERT[2]
            elif n > 0.68 or (n > 0.63 and (x + y) % 2):
                c = DESERT[4]
            ripple = (y + int(math.sin(x / 9 + y / 40) * 3)) % 9
            if ripple == 0 and 0.36 < n < 0.63:
                c = DESERT[4]
            elif ripple == 1 and 0.36 < n < 0.63:
                c = DESERT[2]
            cv.set(x, y, c)
    for y in range(H):  # hardpan: flat cracked patches
        for x in range(W):
            if smooth_noise(x, y, 18, 223) > 0.74:
                cv.set(x, y, DESERT[1] if cracked(x, y, 8, 1) else DESERT[4] if (x + y) % 5 else DESERT[3])
    # the dry creek: a winding bed of cracked mud with rounded stones and pale banks
    creek = worlds.thick(GULCH_CREEK, 9, seed=12)
    for (x, y) in creek:
        cv.set(x, y, ADOBE[0] if cracked(x, y, 6, 2) else ADOBE[2] if (x + y) % 3 else ADOBE[3])
    for (x, y) in creek:
        if (x, y - 1) not in creek:
            cv.set(x, y, ADOBE[0]); cv.set(x, y - 1, DESERT[4])
        elif (x, y + 1) not in creek:
            cv.set(x, y, ADOBE[4])
    for i in range(40):
        x, y = int(noise2(i, 0, 228) * W), int(noise2(i, 1, 228) * H)
        if (x, y) in creek and (x + 2, y) in creek:
            detail.pebble(cv, x, y, ADOBE, big=i % 3 == 0)
    # the railway's end and the plank platform at the top
    paint_rails(cv, 40)
    for y in range(36, 60):  # the line ends at the mesa: clear the rails beyond the buffer
        for x in range(226, W):
            cv.set(x, y, DESERT[3])
    for x in range(212, 224):  # buffer stop
        cv.vline(x, 38, 16, BLEACHED[2] if x % 2 else BLEACHED[1])
    cv.hline(212, 38, 12, RED[3])
    for y in range(58, 78):
        for x in range(20, 230):
            cv.set(x, y, BLEACHED[3] if (x // 6) % 2 else BLEACHED[2])
            if (x % 6) == 3 and y % 10 == 2:
                cv.set(x, y, BLEACHED[0])  # nail heads
    cv.hline(20, 58, 210, BLEACHED[5]); cv.hline(20, 78, 210, BLEACHED[0])
    # the street: packed earth with wheel ruts and hoof prints, down from the platform
    street = worlds.thick(GULCH_STREET, 17, seed=13)  # out of the west edge to the oasis
    for (x, y) in street:
        n = smooth_noise(x, y, 10, 213)
        c = DESERT[2] if n > 0.3 or (x + y) % 2 else DESERT[1]
        cv.set(x, y, c)
    for (x, y) in street:
        if (x - 7, y) not in street and (x - 6, y) in street:
            pass
    wagon_ruts(cv, street, range(0, 72), DESERT)
    for y in range(80, 506):  # two wheel ruts following the street's centre line
        cx = None
        for (xx, yy) in ((x2, y) for x2 in range(W)):
            if (xx, yy) in street:
                cx = xx if cx is None else cx
        if cx is None:
            continue
        right = max(x2 for x2 in range(cx, min(W, cx + 40)) if (x2, y) in street)
        mid = (cx + right) // 2
        for rx in (mid - 6, mid + 6):
            if noise2(rx, y // 3, 229) > 0.15:
                cv.set(rx, y, DESERT[1])
        if y % 7 == 0:
            cv.set(mid + (2 if (y // 7) % 2 else -2), y, DESERT[0])  # hoof prints
    # boardwalks in front of the buildings, out to the street
    for (x0, y0, w0) in ((6, 186, 108), (6, 300, 92)):
        for y in range(y0, y0 + 8):
            for x in range(x0, x0 + w0):
                cv.set(x, y, BLEACHED[3] if (x // 6) % 2 else BLEACHED[2])
        cv.hline(x0, y0, w0, BLEACHED[5]); cv.hline(x0, y0 + 8, w0, BLEACHED[0])
    # the plank bridge where the street crosses the dry bed
    for y in range(296, 334):
        for x in range(116, 152):
            if (x, y) in creek or (x, y - 3) in creek:
                cv.set(x, y, BLEACHED[3] if (y // 4) % 2 else BLEACHED[2])
                if (y % 4) == 0:
                    cv.set(x, y, BLEACHED[1])
    # the mesa in the north-east: red rock plateau, its south face in strata, the mine
    # cut into the face. The rail line stops short of it at the buffer.
    def rim(x):
        if x < 232:
            return None
        return 196 + int(math.sin(x / 23) * 6 + noise2(x // 6, 0, 230) * 5) - max(0, (250 - x) * 4)
    FACE_H = 26
    for x in range(232, W):
        top = rim(x)
        for y in range(0, top):
            n = smooth_noise(x, y, 24, 221)
            c = ADOBE[3] if n > 0.35 or (n > 0.3 and (x + y) % 2) else ADOBE[2]
            if n > 0.75 or (n > 0.7 and (x + y) % 2):
                c = ADOBE[4]
            if top - y < 3:
                c = DESERT[5] if top - y == 1 else ADOBE[4]  # the sunlit rim
            cv.set(x, y, c)
        for k in range(FACE_H):
            y = top + k
            band = (k + int(noise2(x // 9, 3, 222) * 3)) // 5
            c = ADOBE[2] if band % 2 else ADOBE[1]
            if (k + int(noise2(x // 9, 3, 222) * 3)) % 5 == 0:
                c = ADOBE[3]
            if k == 0:
                c = ADOBE[0]
            if k > FACE_H - 4:
                c = ADOBE[1]
            if x == 232 or (rim(x - 1) is not None and rim(x - 1) > top + 2):
                c = ADOBE[1]
            cv.set(x, y, c)
        for d in range(3):  # its shadow on the sand below
            if (x + d) % 2 or d == 0:
                style.darken(cv, x, top + FACE_H + d)
    for x in range(226, 233):  # the western end of the mesa, in shade
        for y in range(0, rim(232) + FACE_H):
            cv.set(x, y, ADOBE[1] if x > 229 else ADOBE[0] if x == 229 else cv.get(x, y))
    for i in range(36):  # scrub on the mesa top
        x, y = 240 + int(noise2(i, 0, 231) * 78), int(noise2(i, 1, 231) * 180)
        detail.grass_tuft(cv, x, y, i % 6, ['#5A4A2A', '#7A6436', '#9A8044', '#B89A58', '#D2B672'], 2)
    # the corral: hoof-churned ground under the cliff
    ccx, ccy = 190, 470
    for (x, y) in oval(ccx, ccy, 44, 26):
        n = smooth_noise(x, y, 5, 216)
        cv.set(x, y, DESERT[1] if n > 0.6 else DESERT[2] if n > 0.25 else ADOBE[2])
    objects = [
        ('saloon', 'saloon', 6, 94), ('hitch-1', 'hitching_rail', 118, 178), ('poster', 'poster_board', 184, 150),
        ('store', 'store', 6, 210), ('keg-1', 'keg', 100, 290), ('keg-2', 'keg', 104, 280),
        ('tower', 'water_tower', 168, 200), ('pump', 'windpump', 30, 226 + 100), ('trough', 'trough', 176, 300),
        ('well', 'dry_well', 58, 360), ('wagon', 'wagon', 16, 470), ('hay-1', 'hay_bale', 122, 524), ('hay-2', 'hay_bale', 108, 538),
        ('mine', 'mine_portal', 248, 170), ('dyn-1', 'dynamite_crate', 228, 214), ('dyn-2', 'dynamite_crate', 300, 222),
        ('corral-n', 'corral_rail', ccx - 46, ccy - 36), ('corral-s', 'corral_rail', ccx - 46, ccy + 22),
        ('corral-w', 'corral_side', ccx - 52, ccy - 22),
        ('cactus-1', 'saguaro', 10, 380), ('cactus-2', 'saguaro_small', 224, 400), ('cactus-3', 'saguaro', 150, 520),
        ('cactus-4', 'saguaro_small', 286, 540), ('cactus-5', 'saguaro', 280, 60), ('cactus-6', 'saguaro_small', 4, 2),
        ('cactus-7', 'saguaro', 290, 300), ('weed-1', 'tumbleweed', 170, 380), ('weed-2', 'tumbleweed', 96, 562),
        ('skull', 'cow_skull', 250, 520), ('barrel-p', 'keg', 40, 62), ('sack-p', 'hay_bale', 196, 56),
    ]
    stands = {'platform': (128, 70), 'saloon': (58, 200), 'street': (132, 260), 'corral': (190, 470),
              'oasis': (12, 548), 'mine': (284, 236), 'well': (75, 404)}
    return cv, objects, stands


def oasis(frame: int = 0):
    """The Desert Oasis, west of Dust Gulch. Not the gulch's flat cracked hardpan but a
    sea of sculpted dunes: long windward faces lit from the west with ripples across
    them, a sharp crest line, and a steep slip face in shade on the lee. In a hollow
    between them a spring fills a clear pool, shallow over pale sand at its rim and deep
    blue where the water wells up, with old stone steps down to it, papyrus at its edge,
    a shaduf for lifting water and palms all round. It is why there was ever a town: the
    gulch's creek was its overflow, until a dune crept over the outlet (the drift still
    lies across the dry bed). The wagon track from the gulch ends at a caravan camp (a
    tent, a resting camel, a fire with tea on it), the railway runs on west along the top
    with a water crane fed from the spring, and the ruins of an older town stand
    half-buried in the south-west."""
    DESERT, ADOBE, WTRm, GRASS = MATERIALS['desert'], MATERIALS['adobe'], MATERIALS['water'], MATERIALS['grass']
    cv = Canvas(W, H)
    PCX, PCY = 116, 300  # the pool

    def pool_r(a):
        return 1 + math.sin(a * 3 + 0.6) * 0.08 + math.sin(a * 5) * 0.05
    pool = set()
    for y in range(PCY - 50, PCY + 50):
        for x in range(PCX - 80, PCX + 80):
            a = math.atan2(y - PCY, x - PCX)
            if math.hypot((x - PCX) / 62, (y - PCY) / 34) < pool_r(a):
                pool.add((x, y))
    pool_d = lambda x, y: math.hypot((x - PCX) / 62, (y - PCY) / 34)  # noqa: E731
    # the street from the gulch, continued pixel for pixel, then the track to the camp
    street = thick_from(GULCH_STREET, 17, 13, W)
    track = street | worlds.thick([(W - 24, 552), (284, 546), (252, 520)], 15, seed=32)
    path = worlds.thick([(252, 520), (226, 470), (196, 410), (170, 352)], 7, seed=33)  # trodden on foot
    creek = thick_from(GULCH_CREEK, 9, 12, W) | worlds.thick([(W - 4, 342), (276, 334), (236, 312), (200, 300), (174, 296)], 8, seed=34)

    def dune(x, y):
        """Phase across the dune lines (0 at a trough, rising to the crest at 0.78, then
        the slip face), and how strongly dunes form here (none in the hollow round the
        pool, along the track or by the gulch)."""
        u = x * 0.86 + y * 0.32 + math.sin(y / 57) * 22 + math.sin(y / 23 + x / 90) * 6 + smooth_noise(x, y, 30, 471) * 18
        p = (u / 74) % 1
        hollow = max(0.0, 1.0 - max(0.0, pool_d(x, y) - 1.15) / 0.9)
        k = min(1.0, max(0.0, (W - 24 - x) / 60))  # flatten into the gulch's ground at the east edge
        return p, max(0.0, 1.0 - hollow) * k
    for y in range(H):
        for x in range(W):
            p, amp = dune(x, y)
            # the flat sand of the hollows and the gulch: the gulch's own mottled ground
            n = smooth_noise(x - W, y, 26, 211)  # in the gulch's coordinates, so it runs on across the border
            flat = DESERT[3]
            if n < 0.3 or (n < 0.36 and (x + y) % 2):
                flat = DESERT[2]
            elif n > 0.68 or (n > 0.63 and (x + y) % 2):
                flat = DESERT[4]
            if p < 0.78:
                t = p / 0.78
                c = DESERT[3] if t < 0.3 else DESERT[4]
                if t > 0.9:
                    c = DESERT[5]
                rip = x * 0.86 + y * 0.32 + math.sin(x / 7) * 1.5
                if 0.15 < t < 0.8 and rip % 6 < 1 and noise2(int(rip // 6), y // 5, 480) < 0.6:
                    c = DESERT[3] if c == DESERT[4] else DESERT[2]  # ripples across the windward face
            else:
                t = (p - 0.78) / 0.22
                c = DESERT[1] if t < 0.45 else DESERT[2]  # the slip face, darkest just under the crest
                if t < 0.06:
                    c = DESERT[0]
            # blend: dunes where they form, flat ground elsewhere, dithered between
            gate = amp * 1.4 - 0.2
            if gate > 0.5 or (gate > 0.3 and (x + y) % 2):
                cv.set(x, y, c)
            elif x > W - 90 and smooth_noise(x - W, y, 18, 223) > 0.74 + max(0, W - 40 - x) / 200:
                # the gulch's cracked hardpan, thinning out westward
                cv.set(x, y, DESERT[1] if cracked(x - W, y, 8, 1) else DESERT[4] if (x + y) % 5 else DESERT[3])
            else:
                cv.set(x, y, flat)
    # the damp hollow round the pool: darker sand, then grass and rushes at the rim
    for y in range(PCY - 70, PCY + 70):
        for x in range(max(0, PCX - 110), min(W, PCX + 110)):
            d = pool_d(x, y)
            if 1.0 <= d < 1.5:
                n = smooth_noise(x, y, 7, 472)
                if d < 1.22 + n * 0.18:
                    c = GRASS[3] if n > 0.55 else GRASS[2] if n > 0.32 else GRASS[1]
                elif d < 1.35 + n * 0.1 or (d < 1.45 and (x + y) % 2):
                    c = DESERT[2]
                else:
                    continue
                cv.set(x, y, c)
    for i in range(70):  # grass tufts in the green ring
        a = noise2(i, 0, 473) * 2 * math.pi
        r = 1.05 + noise2(i, 1, 473) * 0.25
        x, y = int(PCX + math.cos(a) * 62 * r), int(PCY + math.sin(a) * 34 * r)
        detail.grass_tuft(cv, x, y, i % 6, GRASS, 2)
    # the water: pale sand showing through the shallows, deep blue where the spring wells
    for (x, y) in pool:
        d = pool_d(x, y)
        c = WTRm[3] if d > 0.86 else WTRm[2] if d > 0.55 else WTRm[1]
        if d > 0.94 and (x + y) % 2:
            c = '#B8C6B0'  # sand through the shallows
        if (x, y - 1) not in pool or (x, y - 2) not in pool:
            c = DESERT[1]  # the bank's shadow on the water (light from the upper left)
        cv.set(x, y, c)
    for k in range(5):  # rings where the spring wells up
        r = 3 + k * 4 + frame
        for j in range(40):
            a = 2 * math.pi * j / 40
            x, y = int(PCX + 8 + math.cos(a) * r), int(PCY + 4 + math.sin(a) * r * 0.55)
            if (x, y) in pool and pool_d(x, y) < 0.5 and (j + k) % 3:
                cv.set(x, y, WTRm[2] if k % 2 else WTRm[3])
    for ty in range(PCY - 30, PCY + 30, 5):  # glints
        for tx in range(PCX - 56, PCX + 56, 11):
            x, y = tx + int(noise2(tx, ty, 474) * 6), ty + int(noise2(tx, ty, 475) * 3)
            if (x, y) in pool and pool_d(x, y) < 0.8 and noise2(tx, ty, 476) < 0.5:
                cv.hline(x, y, 3, WTRm[4])
    # stone steps down into the water on the south shore
    for k in range(5):
        y = PCY + 26 + k * 3
        for x in range(PCX - 18 + k, PCX + 18 - k):
            if pool_d(x, y) < 1.4:
                cv.set(x, y, STONE[3] if x < PCX - 16 + k + 2 else STONE[2])
                cv.set(x, y + 1, STONE[2]); cv.set(x, y + 2, STONE[1])
    # the dry creek: the old overflow, its mouth choked by a dune tongue
    for (x, y) in creek:
        cv.set(x, y, ADOBE[0] if cracked(x - W, y, 6, 2) else ADOBE[2] if (x + y) % 3 else ADOBE[3])
    for (x, y) in creek:
        if (x, y - 1) not in creek:
            cv.set(x, y, ADOBE[0]); cv.set(x, y - 1, DESERT[4])
        elif (x, y + 1) not in creek:
            cv.set(x, y, ADOBE[4])
    drift = {(x, y) for (x, y) in oval(206, 300, 26, 16)} | {(x, y) for (x, y) in oval(180, 298, 14, 10)}
    for (x, y) in drift:
        if pool_d(x, y) < 1.05:
            continue
        d = math.hypot((x - 206) / 26, (y - 300) / 16)
        cv.set(x, y, DESERT[5] if d < 0.3 and x < 206 else DESERT[4] if x < 210 else DESERT[2] if d < 0.85 else DESERT[1])
    for i in range(30):  # stones in the dry bed
        x, y = 220 + int(noise2(i, 0, 477) * 100), 280 + int(noise2(i, 1, 477) * 40)
        if (x, y) in creek and (x + 2, y) in creek and (x, y) not in drift:
            detail.pebble(cv, x, y, ADOBE, big=i % 3 == 0)
    # the track: the gulch's street and its ruts carry on to the camp, where wagons stop
    for (x, y) in track:
        n = smooth_noise(x, y, 10, 213)
        cv.set(x, y, DESERT[2] if n > 0.3 or (x + y) % 2 else DESERT[1])
    wagon_ruts(cv, track, range(262, W), DESERT)
    for (x, y) in path:  # then a path trodden in the sand down to the water, with footprints
        if pool_d(x, y) >= 1.0 and (x, y) not in creek:
            cv.set(x, y, DESERT[2] if (x + y) % 3 else DESERT[3])
    for t in range(0, 40):
        x = int(252 + (170 - 252) * t / 40 + math.sin(t) * 2)
        y = int(520 + (352 - 520) * t / 40)
        if t % 2:
            cv.set(x - 2, y, DESERT[1])
        else:
            cv.set(x + 2, y, DESERT[1])
    for t in range(60):  # a line of footprints over a dune to the north, someone's walk at dawn
        x, y = int(150 + t * 1.6), int(250 - t * 3.2)
        cv.set(x + (2 if t % 2 else -1), y, DESERT[1] if dune(x, y)[0] < 0.78 else DESERT[0])
    # the railway west along the top, drifted with sand, and the pipe from the spring
    paint_rails(cv, 40, x_off=-W)
    for x in range(W):
        if smooth_noise(x, 0, 18, 478) > 0.55:  # sand blown over the ballast's edges
            depth = int((smooth_noise(x, 0, 18, 478) - 0.55) * 30)
            for y in range(37, 37 + min(depth, 4)):
                cv.set(x, y, DESERT[4] if (x + y) % 2 else DESERT[3])
            for y in range(55 - min(depth, 3), 56):
                cv.set(x, y, DESERT[3])
    for y in range(56, PCY - 36):  # the buried pipe shows as a ridge of disturbed sand
        if y % 3:
            cv.set(96, y, DESERT[2]); cv.set(97, y, DESERT[4])
    # the ruins of the older town in the south-west: wall stubs and a paved court
    court = {(x, y) for y in range(440, 520) for x in range(10, 110)
             if smooth_noise(x, y, 12, 479) > 0.42 and (x - 60) ** 2 / 2500 + (y - 480) ** 2 / 1600 < 1}
    for (x, y) in court:
        if (x // 8 + y // 6) % 2 == 0 and (x % 8 == 0 or y % 6 == 0):
            cv.set(x, y, ADOBE[1])
        else:
            cv.set(x, y, ADOBE[3] if (x // 8 + y // 6) % 3 else ADOBE[2])
    for (x0, y0, w0, h0) in ((14, 536, 46, 6), (114, 470, 6, 40), (2, 420, 6, 34)):  # wall stubs, worn to knee height
        for y in range(y0, y0 + h0 + 4):
            for x in range(x0, x0 + w0):
                top = y < y0 + h0
                c = (ADOBE[4] if x == x0 or y == y0 else ADOBE[3]) if top else ADOBE[2] if x < x0 + w0 - 1 else ADOBE[1]
                if not top and (x + y) % 5 == 0:
                    c = ADOBE[1]  # courses in the face
                if top and noise2(x, y, 481) > 0.85:
                    c = ADOBE[2]  # gaps where bricks fell
                cv.set(x, y, c)
        cv.hline(x0 + 1, y0 + h0 + 4, w0, DESERT[1])
    objects = [
        # the pool's grove
        ('palm-1', 'palm', 8, 196), ('palm-2', 'palm', 120, 186), ('palm-3', 'palm_small', 20, 300),
        ('palm-4', 'palm', 168, 226), ('palm-5', 'palm_small', 70, 330), ('palm-6', 'palm', 150, 334),
        ('palm-7', 'palm_small', 196, 260), ('papyrus-1', 'papyrus', 52, 266), ('papyrus-2', 'papyrus', 160, 288),
        ('papyrus-3', 'papyrus', 98, 316), ('shaduf', 'shaduf', 158, 256), ('jar-1', 'water_jar', 140, 344),
        ('jar-2', 'water_jar', 152, 350),
        # the railway's water crane, fed from the spring
        ('crane', 'water_crane', 84, 52),
        # the caravan camp where the track ends
        ('tent', 'tent', 238, 420), ('camel-1', 'camel', 214, 482), ('camel-2', 'camel', 274, 486),
        ('fire', 'fire_pit', 260, 460), ('awning', 'awning', 240, 360), ('jar-3', 'water_jar', 228, 386),
        # the older town
        ('arch', 'sandstone_arch', 26, 450), ('col-1', 'column_stump', 92, 470), ('col-2', 'column_stump_b', 92, 500),
        ('col-3', 'column_stump_b', 10, 500),
        # out in the dunes
        ('cactus-1', 'saguaro_small', 286, 118), ('skull', 'cow_skull', 180, 540), ('weed', 'tumbleweed', 40, 150),
        ('weed-2', 'tumbleweed', 250, 220),
    ]
    stands = {'gulch': (312, 548), 'pool': (130, 352), 'camp': (250, 500), 'arch': (58, 500),
              'crane': (110, 76), 'dunes': (200, 140)}
    return cv, objects, stands, pool


SPRINGS_PATH = [(-6, 300), (40, 316), (52, 380), (48, 440), (130, 470), (190, 486), (250, 488)]
CALDERA_RIVER = [(170, 60), (178, 140), (160, 230), (200, 320), (250, 400), (300, 470), (W + 6, 520)]


def caldera_rim(x):
    """The crater rim's line (x in the caldera's coordinates)."""
    return 62 + int(math.sin(x / 19) * 7 + noise2(x // 5, 0, 263) * 6)


def caldera(frame: int = 0):
    """The Ember Caldera: the crater rim at the top with the lava lake glowing beyond,
    a lava river running downhill out of it and away to the south-east under a basalt
    bridge, plates of cooling crust with glowing seams along its banks, the forge
    settlement on the cooled ground, basalt column cliffs, obsidian, and a ring of
    columns where the forge keeper spars. The mine cart line from Dust Gulch comes out
    of a tunnel in the west wall."""
    LAVA, BASALT, ASH = MATERIALS['lava'], MATERIALS['basalt'], MATERIALS['ash']
    cv = Canvas(W, H)
    for y in range(H):  # ash ground with cinders, gently darker in hollows
        for x in range(W):
            n = smooth_noise(x, y, 30, 261)
            c = ASH[2] if n > 0.3 or (n > 0.26 and (x + y) % 2) else ASH[1]
            g = noise2(x, y, 270)
            if g > 0.93:
                c = BASALT[2]  # a cinder
            elif g > 0.9:
                c = ASH[3]
            cv.set(x, y, c)
    for i in range(200):
        x, y = int(noise2(i, 0, 262) * W), int(noise2(i, 1, 262) * H)
        detail.pebble(cv, x, y, BASALT, big=i % 4 == 0)
    # the crater: a lava lake at the top behind a ragged basalt rim
    rim = caldera_rim
    for x in range(W):
        r = rim(x)
        for y in range(0, r):
            n = smooth_noise(x, y, 8, 264 + frame)
            c = LAVA[3] if n > 0.5 else LAVA[2]
            if n > 0.78:
                c = LAVA[4]
            if cracked(x, y, 11, 3) and n < 0.6:
                c = LAVA[1]  # crust floating on the lake
            cv.set(x, y, c)
        for k in range(14):  # the rim's inner face, lit by the lake, then its lip
            y = r + k
            c = LAVA[1] if k < 2 else BASALT[3] if k < 5 else BASALT[2] if k < 10 else BASALT[1]
            if k == 5:
                c = BASALT[4]
            cv.set(x, y, c)
    # the lava river: out of the lake, downhill to the south-east
    river = worlds.thick(CALDERA_RIVER, 13, seed=14)
    for (x, y) in river:
        n = smooth_noise(x, y + frame * 3, 7, 265)
        c = LAVA[3] if n > 0.45 else LAVA[2]
        if n > 0.75:
            c = LAVA[5] if n > 0.88 else LAVA[4]
        cv.set(x, y, c)
    # crust plates along the banks, their seams still glowing
    for (x, y) in list(river):
        for (dx, dy) in ((10, 0), (-10, 0), (0, 10), (7, 7), (-7, 7)):
            q = (x + dx, y + dy)
            if q in river or not (0 <= q[0] < W and 0 <= q[1] < H):
                continue
            if cracked(q[0], q[1], 7, 4):
                cv.set(*q, LAVA[2] if noise2(q[0], q[1], 267) > 0.4 else LAVA[1])
            elif noise2(q[0] // 3, q[1] // 3, 268) > 0.3:
                cv.set(*q, BASALT[2] if (q[0] + q[1]) % 3 else BASALT[3])
    for (x, y) in river:  # the river's lip
        if (x, y - 1) not in river:
            cv.set(x, y, LAVA[5])
        if (x, y + 1) not in river and 0 <= y + 1 < H:
            cv.set(x, y + 1, BASALT[0])
    # the lava lights the ground round it (stepped pools, see light_pool)
    # (applied once per spot, never over the lava itself)
    glow_skip = set(river) | {(x, y) for x in range(W) for y in range(0, rim(x) + 2)}
    spots = sorted({(x // 26 * 26 + 13, y // 26 * 26 + 13) for (x, y) in river})
    for (x, y) in spots:
        light_pool(cv, x, y, 22, 14, LAVA[1], glow_skip)
    for x in range(0, W, 48):
        light_pool(cv, x + 24, rim(x) + 18, 30, 10, LAVA[1], glow_skip)
    # the mine cart line out of a timbered tunnel in the west wall
    wall = {(x, y) for y in range(236, 320) for x in range(0, 34 - abs(y - 278) // 4)}
    for (x, y) in wall:
        band = (y + int(noise2(x // 6, 0, 271) * 3)) // 6
        cv.set(x, y, BASALT[3] if band % 2 else BASALT[2])
        if (x + 1, y) not in wall:
            cv.set(x, y, BASALT[4])
    tunnel = {(x, y) for (x, y) in disc(16, 278, 11) if y < 278} | rect_set_z(5, 278, 23, 22)
    for (x, y) in tunnel:
        cv.set(x, y, '#120C10' if x < 24 else '#22161C')
    for px in (3, 27):
        for y in range(272, 300):
            cv.set(px, y, MATERIALS['wood'][3]); cv.set(px + 1, y, MATERIALS['wood'][1])
    cv.hline(3, 270, 26, MATERIALS['wood'][4]); cv.hline(3, 271, 26, MATERIALS['wood'][2])
    for x in range(10, 150, 5):
        cv.vline(x, 284, 12, MATERIALS['wood'][2])
    for ry in (286, 293):
        cv.hline(6, ry, 144, MATERIALS['iron'][3])
    cv.vline(150, 282, 14, MATERIALS['wood'][3])  # the line's buffer
    # the forge yard: flagstones of basalt
    yard = worlds.thick([(40, 400), (110, 400)], 30)
    for (x, y) in yard:
        if (x, y) in river:
            continue
        sx = (x + (y // 8) % 2 * 5) // 10
        c = BASALT[3] if noise2(sx, y // 8, 269) > 0.4 else BASALT[2]
        if (x + (y // 8) % 2 * 5) % 10 == 0 or y % 8 == 0:
            c = BASALT[0]
        cv.set(x, y, c)
    # flagstones on from the bridge's east end to Cinder Springs
    east_path = worlds.thick([(232, 300), (W - 2, 300)], 8) | thick_from(SPRINGS_PATH, 8, 43, W)
    for (x, y) in east_path:
        if (x, y) in river:
            continue
        sx = (x + (y // 7) % 2 * 5) // 10
        c = BASALT[3] if noise2(sx, y // 7, 505) > 0.4 else BASALT[2]
        if (x + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
            c = BASALT[0]
        cv.set(x, y, c)
    # the sparring ring: crust floor in a circle of short columns
    ccx, ccy = 120, 500
    for (x, y) in oval(ccx, ccy, 46, 22):
        cv.set(x, y, ASH[1] if not cracked(x, y, 9, 5) else LAVA[1])
    for k in range(14):
        a = 2 * math.pi * k / 14
        hex_px = (int(ccx + 52 * math.cos(a)), int(ccy + 26 * math.sin(a)))
        cp_hex(cv, hex_px[0], hex_px[1], 5)
    objects = [
        ('forge', 'forge', 20, 320), ('shrine', 'ember_shrine', 150, 360), ('vent-1', 'cooling_vent', 40, 460),
        ('cols-1', 'basalt_columns', 4, 96), ('cols-2', 'basalt_columns_low', 70, 120), ('cols-3', 'basalt_columns', 250, 120),
        ('cols-4', 'basalt_columns_low', 262, 220), ('cols-5', 'basalt_columns', 0, 520),
        ('obs-1', 'obsidian', 110, 200), ('obs-2', 'obsidian_small', 238, 326), ('obs-3', 'obsidian', 262, 556 - 26),
        ('obs-4', 'obsidian_small', 60, 230), ('vent-2', 'cooling_vent', 214, 196), ('vent-3', 'cooling_vent', 280, 360),
    ]
    # the bridge is part of the ground (walkable), drawn across the river
    deck = style.finalize(cdp.basalt_bridge(), name='basalt_bridge')
    bx, by = 168, 290
    cv.paste(deck, bx, by)
    span = {(x, y) for x in range(bx, bx + deck.w) for y in range(by + 4, by + 20)}
    lake = {(x, y) for x in range(W) for y in range(0, rim(x) + 14)}
    blocked = (river | lake) - span
    stands = {'tunnel': (44, 300), 'forge': (68, 404), 'bridge': (200, 302), 'ring': (120, 500), 'rim': (100, 96),
              'east': (290, 300), 'springs': (312, 300)}
    return cv, objects, stands, blocked


def springs(frame: int = 0):
    """Cinder Springs, east of the caldera: where the fire country rests. The crater's
    lava lake ends against its rim in the north-west; the caldera's lava river runs in
    from the west and dies here in a delta of black crust, hissing where a hot stream
    meets it. The stream comes down a staircase of hot-spring terraces: pools of milky
    turquoise held by cream travertine lips, the highest ringed with orange mats where
    it is hottest, each spilling over a frozen-waterfall face into the next. Fireweed,
    the first thing to grow back on burnt ground, flowers on the ash; a flagstone path
    lit by stone lanterns leads to a bathhouse of charred cedar."""
    LAVA, BASALT, ASH = MATERIALS['lava'], MATERIALS['basalt'], MATERIALS['ash']
    TRAV = ['#8A6A4A', '#B89A74', '#D8C4A0', '#EEE2C8', '#FAF4E6']  # travertine
    SPRING = ['#0E4A54', '#1A7A84', '#2FA8B0', '#6CCFCC', '#B4ECE6']
    cv = Canvas(W, H)
    blocked = set()
    for y in range(H):  # the caldera's ash ground, continued
        for x in range(W):
            n = smooth_noise(x + W, y, 30, 261)
            c = ASH[2] if n > 0.3 or (n > 0.26 and (x + y) % 2) else ASH[1]
            g = noise2(x + W, y, 270)
            if g > 0.93:
                c = BASALT[2]
            elif g > 0.9:
                c = ASH[3]
            cv.set(x, y, c)
    for i in range(140):
        x, y = int(noise2(i, 0, 500) * W), int(noise2(i, 1, 500) * H)
        detail.pebble(cv, x, y, BASALT, big=i % 4 == 0)
    # the end of the crater lake, closed by its rim
    def rim(x):
        return caldera_rim(x + W) - max(0, x - 16) * 0.9
    lake = set()
    for x in range(W):
        r = int(rim(x))
        for y in range(0, r):
            n = smooth_noise(x + W, y, 8, 264 + frame)
            c = LAVA[3] if n > 0.5 else LAVA[2]
            if n > 0.78:
                c = LAVA[4]
            if cracked(x + W, y, 11, 3) and n < 0.6:
                c = LAVA[1]
            cv.set(x, y, c)
            lake.add((x, y))
        for k in range(14):
            y = max(r, 0) + k
            if r < -14:
                break
            c = LAVA[1] if k < 2 else BASALT[3] if k < 5 else BASALT[2] if k < 10 else BASALT[1]
            if k == 5:
                c = BASALT[4]
            if y >= 0 and r > -2:
                cv.set(x, y, c)
                lake.add((x, y))
    # the terraces: pools held by scalloped travertine lips, each spilling into the next
    pools = [(236, 150, 50, 24), (192, 228, 56, 24), (148, 306, 54, 24), (104, 382, 46, 20)]

    def pool_d(i, x, y):
        cx, cy, rx, ry = pools[i]
        a = math.atan2(y - cy, x - cx)
        wob = 1 + 0.08 * math.sin(5 * a + i * 1.7) + 0.05 * math.sin(9 * a + i * 2.3)
        return math.hypot((x - cx) / rx, (y - cy) / ry) / wob
    pool_sets = [{(x, y) for y in range(cy - ry - 6, cy + ry + 6) for x in range(cx - rx - 8, cx + rx + 8)
                  if pool_d(i, x, y) < 1} for i, (cx, cy, rx, ry) in enumerate(pools)]
    sinter = set()
    for i, (cx, cy, rx, ry) in enumerate(pools):  # one mineral slope under them all
        sinter |= {(x, y) for y in range(cy - ry - 20, cy + ry + 26) for x in range(cx - rx - 22, cx + rx + 22)
                   if pool_d(i, x, y - 6) < 1.45 + smooth_noise(x, y, 9, 506) * 0.25}
        if i + 1 < len(pools):
            sinter |= worlds.thick([(cx, cy), (pools[i + 1][0], pools[i + 1][1])], 30, seed=44)
    for (x, y) in sinter:
        n = smooth_noise(x, y, 6, 501)
        c = TRAV[3] if n > 0.55 else TRAV[2] if n > 0.25 else TRAV[1]
        if (x * 5 + y * 3) % 17 == 0:
            c = TRAV[4]
        cv.set(x, y, c)
    for (x, y) in sinter:  # its edge on the ash, a soft stained margin
        if any((x + dx, y + dy) not in sinter for (dx, dy) in ((0, 3), (3, 0), (-3, 0), (0, -3))):
            cv.set(x, y, '#9A7A52' if (x + y) % 2 else TRAV[1])
    for i in range(len(pools) - 1):  # the spill from each pool to the next, down the slope
        (cx, cy, rx, ry), (nx, ny, _, _) = pools[i], pools[i + 1]
        sx, sy = cx - rx // 2, cy + ry // 2
        for t in range(0, 41):
            x = int(sx + (nx + 10 - sx) * t / 40)
            y = int(sy + (ny - 6 - sy) * t / 40)
            if any((x, y) in ps for ps in pool_sets):
                continue
            for dx in range(-2, 3):
                cv.set(x + dx, y, SPRING[3] if abs(dx) < 2 else TRAV[4])
                blocked.add((x + dx, y))
    for (i, (cx, cy, rx, ry)) in enumerate(pools):
        pool = pool_sets[i]
        for x in range(cx - rx - 8, cx + rx + 8):  # the frozen-waterfall face under the lip
            ys = [y for (xx, y) in pool if xx == x]
            if not ys:
                continue
            yb = max(ys)
            drop = 5 + int(noise2(x // 3, i, 507) * 6)
            for k in range(drop):
                streak = (x * 3 + int(noise2(x, 0, 502 + i) * 4)) % 5
                c = TRAV[4] if k < 2 else TRAV[3] if streak < 2 else TRAV[2] if streak < 4 else '#C8803A'
                if k == drop - 1:
                    c = TRAV[1]
                cv.set(x, yb + 1 + k, c)
        for (x, y) in pool:
            d = pool_d(i, x, y)
            c = SPRING[1] if d < 0.45 and i == 0 else SPRING[2] if d < 0.7 else SPRING[3]
            if d > 0.86:
                c = '#C8803A' if i == 0 and (x + y) % 3 else SPRING[4] if (x + y) % 2 else TRAV[4]  # mats at the hottest, else the lip
            if (x, y - 1) not in pool or (x, y - 2) not in pool:
                c = TRAV[1]  # the lip's shadow on the water
            cv.set(x, y, c)
            blocked.add((x, y))
        for k in range(6):  # still glints
            gx, gy = cx - rx // 2 + int(noise2(k, i, 503) * rx), cy - ry // 2 + int(noise2(k, i, 504) * ry)
            if (gx, gy) in pool and (gx + 3, gy) in pool:
                cv.hline(gx, gy, 3, SPRING[4])
    # sulphur crusts round the fumaroles on the upper slope
    for (vx, vy) in ((162, 80), (312, 140)):
        for (x, y) in oval(vx, vy, 18, 9):
            if noise2(x // 2, y // 2, 508) > 0.45:
                cv.set(x, y, '#E8D24A' if (x + y) % 3 else '#B8A030')
    # the hot stream from the lowest pool down to the lava, and stepping stones over it
    stream = worlds.thick([(96, 400), (88, 440), (98, 480), (90, 516), (92, 534)], 4, seed=41)
    for (x, y) in stream:
        cv.set(x, y, SPRING[2] if (x + y) % 3 else SPRING[3])
        blocked.add((x, y))
    for (x, y) in stream:
        if (x - 1, y) not in stream:
            cv.set(x - 1, y, TRAV[2])
    stones = [(92, 462), (95, 470)]
    # the caldera's lava river, continued, dying in a delta of crust
    river = thick_from(CALDERA_RIVER, 13, 14, -W) | worlds.thick([(0, 520), (34, 534), (66, 544)], 11, seed=40)
    tongue = worlds.thick([(60, 544), (84, 548)], 7, seed=42)
    for (x, y) in river | tongue:
        n = smooth_noise(x + W, y + frame * 3, 7, 265)
        c = LAVA[3] if n > 0.45 else LAVA[2]
        if n > 0.75:
            c = LAVA[5] if n > 0.88 else LAVA[4]
        if (x, y) in tongue and (x, y) not in river:
            c = LAVA[1] if cracked(x, y, 5, 6) else BASALT[1]  # crusting over
        if x > 40 and cracked(x, y, 6, 7) and (x, y) not in tongue:
            c = LAVA[1]
        cv.set(x, y, c)
        blocked.add((x, y))
    for (x, y) in list(river):
        for (dx, dy) in ((10, 0), (0, 10), (7, 7), (-7, 7), (0, -9)):
            q = (x + dx, y + dy)
            if q in river or q in tongue or not (0 <= q[0] < W and 0 <= q[1] < H):
                continue
            if cracked(q[0] + W, q[1], 7, 4):
                cv.set(*q, LAVA[2] if noise2(q[0] + W, q[1], 267) > 0.4 else LAVA[1])
            elif noise2((q[0] + W) // 3, q[1] // 3, 268) > 0.3:
                cv.set(*q, BASALT[2] if (q[0] + q[1]) % 3 else BASALT[3])
    for (x, y) in river:
        if (x, y - 1) not in river:
            cv.set(x, y, LAVA[5])
        if (x, y + 1) not in river and 0 <= y + 1 < H:
            cv.set(x, y + 1, BASALT[0])
    glow_skip = river | lake | tongue
    for (x, y) in sorted({(x // 26 * 26 + 13, y // 26 * 26 + 13) for (x, y) in river}):
        light_pool(cv, x, y, 22, 14, LAVA[1], glow_skip)
    # the flagstone path from the caldera to the bathhouse, lantern-lit
    path = worlds.thick(SPRINGS_PATH, 8, seed=43)
    for (x, y) in path:
        if (x, y) in blocked:
            continue
        sx = (x + (y // 7) % 2 * 5) // 10
        c = BASALT[3] if noise2(sx, y // 7, 505) > 0.4 else BASALT[2]
        if (x + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
            c = BASALT[0]
        cv.set(x, y, c)
    for (sx, sy) in stones + [(132, 468)]:
        cp_hex(cv, sx, sy, 4)
    for (x, y) in stream:  # the path crosses the stream on stepping stones
        if (x, y) in path:
            blocked.discard((x, y))
    for (lx, ly) in ((52, 330), (60, 420), (150, 466), (214, 478)):
        light_pool(cv, lx, ly + 22, 18, 8, '#F2A048', glow_skip)
    objects = [
        ('bath', 'bathhouse', 196, 404), ('lantern-1', 'stone_lantern', 44, 306), ('lantern-2', 'stone_lantern', 52, 398),
        ('lantern-3', 'stone_lantern', 142, 444), ('lantern-4', 'stone_lantern', 206, 456),
        ('weed-1', 'fireweed', 20, 360), ('weed-2', 'fireweed_small', 8, 410), ('weed-3', 'fireweed', 150, 520),
        ('weed-4', 'fireweed_small', 176, 540), ('weed-5', 'fireweed', 290, 330), ('weed-6', 'fireweed_small', 300, 250),
        ('weed-7', 'fireweed', 130, 120), ('weed-8', 'fireweed_small', 20, 240), ('weed-9', 'fireweed', 264, 300),
        ('weed-10', 'fireweed_small', 280, 340), ('weed-11', 'fireweed', 300, 470), ('weed-12', 'fireweed_small', 60, 180),
        ('cols-4', 'basalt_columns', 250, 236),
        ('cols-1', 'basalt_columns', 262, 520), ('cols-2', 'basalt_columns_low', 286, 40), ('cols-3', 'basalt_columns_low', 210, 540),
        ('vent-1', 'cooling_vent', 150, 60), ('vent-2', 'cooling_vent', 300, 120), ('vent-3', 'cooling_vent', 110, 556 - 20),
        ('obs-1', 'obsidian_small', 20, 470), ('obs-2', 'obsidian', 286, 400),
    ]
    stands = {'caldera': (8, 300), 'pools': (100, 250), 'bath': (250, 494), 'delta': (130, 540), 'slope': (220, 70)}
    return cv, objects, stands, blocked | lake


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
    worlds.grass(cv, frame)
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
    for x in range(100, W):
        y = shore_y(x) + 6
        for k in range(8):
            if x < 296:  # the quay's dressed face
                c = STONE[3] if k == 0 else STONE[2] if (x + (k // 3) * 4) % 8 else STONE[0]
                if k > 5:
                    c = MATERIALS['leaf'][1] if (x + k) % 3 else STONE[1]  # weed at the waterline
            else:  # past the quay, a rough rocky bank that runs on below the headland
                c = STONE[3] if (x // 4 + k // 3) % 2 else STONE[2]
                if k < 2:
                    c = G[1]
            cv.set(x, y + k, c)
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
        ('bollard-3', 'bollard', 290, 290), ('pots-2', 'lobster_pots', 270, 196),
        ('upturned', 'upturned_boat', 8, 400), ('washing', 'washing_line', 110, 90), ('buoy-1', 'buoy', 120, 450),
        ('buoy-2', 'buoy', 300, 380),
    ]
    blocked = water - set().union(*jetties)
    stands = {'town': (160, 18), 'market': (150, 288), 'jetty': (157, 384), 'beach': (34, 380), 'castle': (300, 116)}
    return cv, objects, stands, blocked


def castle(frame: int = 0):
    """Hearthold Castle on the headland: the cliff path from the harbour arrives at the
    west edge and runs along the outer meadow to a drawbridge over the dry ditch; the
    gatehouse in the south wall opens on a courtyard with the keep to the north, the
    bedtime bell tower in the north-east corner, the walled herb garden and the
    training yard where the steward spars. Sea cliffs drop away to the east and south."""
    ASHLAR, WTRm, STONEm = MATERIALS['ashlar'], MATERIALS['water'], MATERIALS['stone']
    cv = Canvas(W, H)
    worlds.grass(cv, frame)
    # the sea cliffs: the headland's edge to the south and east, a face and the sea
    def edge_y(x):
        # the harbour's water meets the headland's west edge below y = 306 (seamless rule)
        e = 470 + int(math.sin(x / 31) * 10 + noise2(x // 7, 0, 321) * 8) - max(0, (x - 260) * 2)
        return min(e, 306 + int(x * 2.7)) if x < 60 else e
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
                c = WTRm[1] if n > 0.4 else WTRm[0]
                if k < 30:
                    c = WTRm[4] if (x + frame) % 3 else WTRm[3]
                sea.add((x, y))
            cv.set(x, y, c)
            if k < 26:
                sea.add((x, y)) if k > 2 else None
    # the harbour's breakwater runs on to its root against the headland's foot
    root = worlds.thick([(-8, 410), (22, 404)], 12)
    for (x, y) in root:
        blk = ((x + 8 + (y // 7) % 2 * 5) // 10 + y // 7) % 3
        c = STONEm[3] if blk == 0 else STONEm[2] if blk == 1 else STONEm[4]
        if (x + 8 + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
            c = STONEm[1]
        cv.set(x, y, c)
    # the path from the harbour along the outer meadow to the drawbridge
    path = worlds.thick([(-6, 110), (12, 112)], 9) | worlds.thick([(10, 112), (30, 150), (40, 300), (74, 404), (140, 420), (182, 404), (182, 384)], 10, seed=19)
    paint_road(cv, path | {(x, y) for (x0, y) in path if x0 == 0 for x in range(-12, 0)})
    # the dry ditch below the south wall, crossed by the drawbridge
    ditch = {(x, y) for x in range(60, 300) for y in range(352, 380)}
    for (x, y) in ditch:
        k = y - 352
        cv.set(x, y, STONEm[3] if k < 2 else STONEm[1] if k < 6 else MATERIALS['grass'][1] if k > 22 else MATERIALS['soil'][2] if (x + y) % 3 else MATERIALS['soil'][1])
    for y in range(350, 384):  # the drawbridge planks
        for x in range(168, 196):
            cv.set(x, y, MATERIALS['wood'][3] if y % 4 else MATERIALS['wood'][1])
        cv.set(167, y, IRONm[1]); cv.set(196, y, IRONm[1])
    # the castle walls seen from above: a lit wall walk between merlons
    def wall_v(x0, y0, y1):
        for y in range(y0, y1):
            for x in range(x0, x0 + 12):
                k = x - x0
                c = ASHLAR[4] if 2 <= k < 4 else ASHLAR[3] if 4 <= k < 9 else ASHLAR[1]
                if k < 2 or k >= 10:
                    c = ASHLAR[5] if (y // 4) % 2 == 0 and k < 2 else ASHLAR[2] if (y // 4) % 2 == 0 else ASHLAR[1]
                cv.set(x, y, c)
    wall_v(70, 40, 350)
    wall_v(282, 40, 350)
    # the courtyard: worn flagstones, grass in the joints
    yard = {(x, y) for x in range(82, 282) for y in range(190, 350)}
    worlds.paint_paving(cv, yard, seed=21)
    garden_plot = {(x, y) for x in range(86, 150) for y in range(250, 330)}
    for (x, y) in garden_plot:
        cv.set(x, y, MATERIALS['grass'][3] if (x + y) % 5 else MATERIALS['grass'][2])
    for x in range(86, 150):  # a low hedge round the herb garden
        for y in (250, 251, 252):
            cv.set(x, y, LEAFm[2] if y == 250 else LEAFm[1])
    objects = [
        ('wall-n1', 'wall_run', 70, 0), ('wall-n2', 'wall_run', 166, 0), ('wall-n3', 'wall_run', 198, 0),
        ('tower-nw', 'round_tower', 52, -40), ('keep', 'keep', 112, 76), ('bell', 'bell_tower', 244, 40),
        ('herbs-1', 'herb_bed', 92, 262), ('herbs-2', 'herb_bed', 92, 286), ('herbs-3', 'herb_bed', 92, 310),
        ('dummy-1', 'training_dummy', 214, 220), ('dummy-2', 'training_dummy', 246, 236),
        ('wall-s1', 'wall_run', 70, 306), ('gate', 'gatehouse', 122, 262), ('wall-s2', 'wall_run', 200, 306),
        ('tower-sw', 'round_tower', 52, 262), ('tower-se', 'round_tower', 268, 262),
        ('tower-ne', 'round_tower', 268, -40),
    ]
    blocked = sea | ditch - {(x, y) for x in range(168, 196) for y in range(350, 384)}
    blocked |= {(x, y) for x in range(70, 82) for y in range(40, 350)} | {(x, y) for x in range(282, 294) for y in range(40, 350)}
    stands = {'harbour': (14, 112), 'bridge': (182, 396), 'gate': (182, 344), 'courtyard': (190, 230),
              'keep': (176, 206), 'herbs': (160, 290), 'meadow': (220, 430)}
    return cv, objects, stands, blocked


def station(frame: int = 0):
    """Halcyon Station: the space elevator arrives through the airlock at the bottom; a
    corridor of deck plates with light strips leads up to the atrium of garden pods and
    on to the long viewport where the planet turns below; the crew's sleep pods line
    the west bay, the navigation consoles the east; a low-gravity ring is marked out on
    the atrium floor; the shuttle hatch to Lumen is in the east wall."""
    HULL, VOID = MATERIALS['hull'], MATERIALS['void']
    CYAN = MATERIALS['neon_cyan']
    cv = Canvas(W, H)
    for y in range(H):  # deck plates, each lit along its top and left edge
        for x in range(W):
            px, py = x % 32, y % 24
            n = noise2(x // 32, y // 24, 351)
            c = HULL[2] if n > 0.18 else HULL[1]
            if px == 0 or py == 0:
                c = HULL[0]
            elif px == 1 or py == 1:
                c = HULL[3]
            elif (px, py) in ((4, 4), (27, 4), (4, 19), (27, 19)):
                c = HULL[4]  # bolts
            cv.set(x, y, c)
    for x in range(W):  # the hull walls on both sides, with pipes and a light strip
        pass
    for (x0, x1) in ((0, 18), (W - 18, W)):
        for y in range(H):
            for x in range(x0, x1):
                k = (x - x0) / 18
                c = HULL[3] if (x0 == 0 and k > 0.8) or (x0 > 0 and k < 0.2) else HULL[1]
                if (x - x0) in (6, 7, 12):
                    c = HULL[2]
                cv.set(x, y, c)
            cv.set(x1 - 1 if x0 == 0 else x0, y, CYAN[2] if (y // 6) % 2 else CYAN[1])
    # a soft violet runner down the corridor (the station keeps quiet hours)
    for y in range(300, H - 40):
        for x in range(146, 174):
            cv.set(x, y, MATERIALS['nap'][1] if (x in (146, 173)) else MATERIALS['nap'][2] if (y // 2 + x // 2) % 2 else MATERIALS['nap'][1])
    # the corridor's floor light strips
    for y in range(300, H - 40):
        for x in (140, 179):
            cv.set(x, y, CYAN[3] if (y // 3 + frame) % 4 else CYAN[2])
    # the low-gravity ring on the atrium floor
    ccx, ccy = 160, 250
    for k in range(260):
        a = 2 * math.pi * k / 260
        for (rx, ry) in ((64, 30), (50, 23)):
            x, y = int(ccx + rx * math.cos(a)), int(ccy + ry * math.sin(a))
            cv.set(x, y, CYAN[3]); cv.set(x, y + 1, CYAN[1])
    for (x, y) in oval(ccx, ccy, 10, 5):
        cv.set(x, y, CYAN[2] if (x + y) % 2 else CYAN[1])
    objects = [
        ('view-1', 'viewport', 20, 8), ('view-2', 'viewport', 140, 8), ('view-3', 'viewport', 200, 8),
        ('pod-1', 'garden_pod', 30, 120), ('pod-2', 'garden_pod', 226, 120), ('pod-3', 'garden_pod', 30, 330),
        ('sleep-1', 'sleep_pod', 22, 210), ('sleep-2', 'sleep_pod', 22, 270), ('sleep-3', 'sleep_pod', 60, 404),
        ('console-1', 'console', 258, 330), ('console-2', 'console', 258, 372), ('lock-lift', 'airlock', 132, 516),
        ('lock-shuttle', 'airlock', 258, 214),
    ]
    stands = {'lift': (160, 512), 'atrium': (160, 250), 'viewport': (160, 96), 'sleep': (70, 250),
              'shuttle': (286, 280)}
    return cv, objects, stands


def lumen(frame: int = 0):
    """Lumen, the quiet moon: pale regolith pocked with craters lit on their far rims,
    the shuttle landed at the top, a trail of footprints, glowing shrubs and moon
    crystals, dream pools holding the stars, and a wide crater for gentle sparring."""
    R, GLOWm, VOID = MATERIALS['regolith'], MATERIALS['glowflora'], MATERIALS['void']
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 28, 361)
            c = R[3] if n > 0.26 or (n > 0.21 and (x + y) % 2) else R[2]
            if noise2(x, y, 362) > 0.96:
                c = R[4]
            cv.set(x, y, c)
    # the horizon: the moon's edge against the void, the planet rising beyond it
    def horizon(x):
        return 64 + int(math.sin(x / 23) * 4 + noise2(x // 6, 0, 363) * 5)
    for x in range(W):
        hz = horizon(x)
        for y in range(0, hz):
            c = VOID[0] if noise2(x, y, 364) > 0.015 else '#FFFFFF'
            d = math.hypot(x - 230, y - 150)
            if d < 120:
                band = int((y + math.sin(x / 11) * 3) / 5) % 3
                c = ('#3E6AA8', '#5A8AC4', '#E6EEF6')[band] if d < 117 else '#9AD2FF'
            cv.set(x, y, c)
        cv.set(x, hz, R[5]); cv.set(x, hz + 1, R[4])
        for k in range(2, 6):
            cv.set(x, hz + k, R[2] if k < 4 else R[3])
    craters = [(60, 120, 22), (250, 80, 14), (220, 300, 30), (70, 380, 12), (150, 470, 40), (280, 460, 10),
               (40, 250, 9), (120, 200, 8)]
    for (cx, cy, r) in craters:
        for (x, y) in oval(cx, cy, r, r * 0.6):
            dx, dy = (x - cx) / r, (y - cy) / (r * 0.6)
            d = math.hypot(dx, dy)
            t = dx * 0.7 + dy * 0.7  # toward the lower right
            if d < 0.8:  # the bowl: its far wall in shade, its near wall catching the light
                v = 1.6 + t * 1.8 + (0.3 if (x + y) % 2 else 0)
            else:  # the raised rim: lit on its upper-left outside, shaded lower right
                v = 3.4 - t * 2.2 + (0.3 if (x + y) % 2 else 0)
            cv.set(x, y, R[max(0, min(5, int(v)))])
    for i, y in enumerate(range(140, 460, 7)):  # footprints from the shuttle
        x = 160 + int(math.sin(y / 40) * 30) + (3 if i % 2 else -3)
        cv.set(x, y, R[1]); cv.set(x + 1, y, R[1]); cv.set(x, y + 1, R[2])
    objects = [
        ('shuttle', 'shuttle', 118, 72), ('shrub-1', 'moon_shrub', 20, 180), ('shrub-2', 'moon_shrub', 270, 160),
        ('shrub-3', 'moon_shrub', 30, 470), ('shrub-4', 'moon_shrub', 280, 360), ('shrub-5', 'moon_shrub', 196, 380),
        ('crystal-1', 'moon_crystal', 96, 290), ('crystal-2', 'moon_crystal', 290, 250), ('crystal-3', 'moon_crystal', 6, 320),
        ('crystal-4', 'moon_crystal', 250, 530), ('pool-1', 'dream_pool', 70, 240), ('pool-2', 'dream_pool', 200, 210),
        ('pool-3', 'dream_pool', 40, 540), ('shrub-6', 'moon_shrub', 120, 330), ('shrub-7', 'moon_shrub', 150, 256),
        ('crystal-5', 'moon_crystal', 214, 120), ('crystal-6', 'moon_crystal', 230, 128), ('shrub-8', 'moon_shrub', 290, 520),
    ]
    for (_i, key, x, y) in objects:  # the flora's glow on the dust
        if key == 'moon_shrub':
            light_pool(cv, x + 17, y + 32, 26, 12, GLOWm[1])
    stands = {'shuttle': (160, 142), 'pool': (100, 274), 'crater': (150, 470), 'east': (290, 300)}
    return cv, objects, stands


def riverside(frame: int = 0):
    """The Riverside, east of the garden: the garden's stream comes in at the west edge
    exactly where it leaves the garden (same line, width and bluff), and widens as it
    runs east into a slow river. The watermill stands on the north bank with its wheel
    in the race, willows lean over the south bank, reeds and lily pads fill the
    shallows, a heron fishes, and stepping stones cross where it is still narrow."""
    WTRm, SAND = MATERIALS['water'], MATERIALS['sand']
    cv = Canvas(W, H)
    worlds.grass(cv, frame)
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
    objects = [
        ('mill', 'water_mill', 140, top[220] - 96 + 6), ('willow-1', 'willow', 70, 330), ('willow-2', 'willow', 230, 360),
        ('reeds-1', 'reeds', 110, int(centre(120) + half(120)) - 24), ('reeds-2', 'reeds', 280, int(centre(290) + half(290)) - 26),
        ('reeds-3', 'reeds', 160, int(centre(170) - half(170)) + 2), ('heron', 'heron', 196, int(centre(206)) - 6),
        ('lilies-1', 'lily_pads', 250, int(centre(265)) - 6), ('lilies-2', 'lily_pads', 120, int(centre(135)) + 2),
        ('tree-1', 'tree', 10, 120), ('tree-2', 'tree_small', 260, 110), ('bush-1', 'bush', 40, 470),
        ('bush-2', 'bush', 200, 500), ('tree-3', 'tree_autumn', 120, 470), ('bench', 'bench', 170, 440),
        ('sack-1', 'sack', 120, 220), ('sack-2', 'sack', 108, 224), ('cart', 'cart', 80, 200),
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
    worlds.grass(cv, frame)
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
        ('willow', 'willow', 196, 400), ('lilies', 'lily_pads', 140, 476), ('duck-1', 'duck', 170, 500),
        ('duck-2', 'duck', 262, 488), ('heron', 'heron', 290, 440),
        ('hedge-n1', 'hedge', 0, 30), ('hedge-n2', 'hedge', 224, 30), ('tree-1', 'tree', 110, -24),
        ('tree-2', 'tree_autumn', 284, 140), ('tree-3', 'tree', 4, 150), ('tree-4', 'tree_small', 20, 470),
        ('bench-1', 'bench', 60, 196), ('bench-2', 'bench', 216, 196), ('bench-3', 'bench', 96, 360),
        ('lamp-1', 'lamp', 66, 260), ('lamp-2', 'lamp', 246, 260), ('lamp-3', 'lamp', 108, 410),
        ('icecream', 'ice_cream_cart', 220, 296), ('bush-1', 'bush', 0, 250), ('bush-2', 'bush', 290, 250),
        ('bush-3', 'bush', 40, 540), ('bush-4', 'bush', 280, 540),
    ]
    stands = {'town': (8, 300), 'bandstand': (160, 240), 'fountain': (160, 360), 'pond': (100, 456)}
    return cv, objects, stands, water


def ridge(frame: int = 0):
    """The Snowy Ridge, north of the garden: the trail comes up out of the garden's
    treeline at the bottom (the same x, through the same dark forest floor), climbs
    through thinning pines onto an alpine meadow with a frozen tarn and cairns, then
    by steps up a stone face to the terrace where the cabin stands under the peaks.
    Snow lies only above the face (world logic); below it only a dusting on the pines."""
    SNOWm, STONEm = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W, H)
    alpine = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
    worlds.grass(cv, frame, alpine)
    # the forest floor at the bottom, matching the garden's treeline band
    for y in range(H - 80, H):
        for x in range(W):
            t = (y - (H - 80)) / 80
            if noise2(x, y, 441) < t:
                cv.set(x, y, G[1])
    style.dither_dark(cv, 0, H - 40, W, 40, 1.0)
    style.dither_dark(cv, 0, H - 60, W, 20, 0.5)
    # the terrace: everything above the face is high ground under snow
    def rim(x):
        return 210 + int(math.sin(x / 27) * 8 + noise2(x // 6, 0, 442) * 6)
    FACE_H = 24
    for x in range(W):
        r = rim(x)
        for y in range(0, r):
            n = smooth_noise(x, y, 18, 443)
            c = SNOWm[3] if n > 0.35 else SNOWm[2]
            if smooth_noise(x, y, 7, 444) > 0.8:
                c = STONEm[3] if smooth_noise(x, y - 1, 7, 444) > 0.8 else STONEm[4]  # rock showing through
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
    # peaks along the top
    peak_pts = {}
    for (ax, ay, half, base) in ((70, -14, 70, 70), (230, -24, 80, 80), (310, -6, 40, 50)):
        for y in range(max(0, ay), base):
            spread = (y - ay) / (base - ay) * half
            for x in range(int(ax - spread), int(ax + spread * 0.9) + 1):
                if 0 <= x < W:
                    lit = x < ax + (y - ay) * 0.15
                    hem = ay + 26 + abs((x + ax) % 8 - 4) + int(noise2(x // 8, ax, 446) * 5)
                    c = (SNOWm[3] if lit else SNOWm[1]) if y < hem else (STONEm[3] if lit else STONEm[1])
                    if y >= hem and (y - ay + (x if lit else -x) // 4) % 9 == 0:
                        c = STONEm[2] if lit else STONEm[0]
                    peak_pts[(x, y)] = c
    for (x, y), c in peak_pts.items():
        if (x - 1, y) not in peak_pts or (x + 1, y) not in peak_pts or (y > 0 and (x, y - 1) not in peak_pts):
            c = STONEm[0]
        cv.set(x, y, c)
    # the trail: up from the garden, round the tarn, steps up the face, to the cabin
    trail = worlds.thick([(206, H + 12), (206, H - 40), (190, 470), (150, 400), (130, 330), (150, 270), (150, 220)], 9.5, seed=29)
    trail |= worlds.thick([(150, 220), (150, 170), (120, 140)], 8, seed=30)
    on_terrace = {(x, y) for (x, y) in trail if y < rim(x)}
    paint_road(cv, {(x, y) for (x, y) in trail if y >= rim(x) + FACE_H} | {(x, y) for (x0, y) in trail if y == H - 1 for x in [x0] for y in range(H, H + 12)})
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
        ('pine-m1', 'snowy_pine', 20, 330), ('pine-m2', 'snowy_pine', 262, 420), ('pine-m3', 'snowy_pine', 270, 250),
        ('pine-m4', 'snowy_pine', 60, 250), ('tarn', 'frozen_tarn', 196, 380), ('cairn-1', 'cairn', 100, 360),
        ('cairn-2', 'cairn', 176, 250), ('boulder-1', 'boulder', 20, 430), ('stone-1', 'stone', 280, 470),
        ('cabin', 'cabin', 150, 80), ('campfire', 'campfire', 110, 176), ('pine-t1', 'snowy_pine', 10, 120),
        ('pine-t2', 'snowy_pine', 270, 120), ('pine-t3', 'snowy_pine', 40, 150),
    ]
    face = {(x, y) for x in range(W) for y in range(rim(x), rim(x) + FACE_H)}
    peaks_block = set(peak_pts)
    stands = {'garden': (206, H - 8), 'tarn': (170, 420), 'cabin': (200, 176), 'campfire': (146, 204)}
    return cv, objects, stands, (face - steps) | peaks_block


def halt(frame: int = 0):
    """The Valley Halt, west of Crossroads Town and south of the Woodland: the lane from
    the town comes in at the east edge and opens on the platform, where the little stone
    station faces the line under its canopy; the rails run west out of the valley (the
    train to Cogsworth) and stop at a buffer before the town. South of the line lie
    fields in rows behind a fence; to the north the woodland's floor reaches down."""
    cv = Canvas(W, H)
    worlds.grass(cv, frame)
    # the woodland's forest floor reaches down along the top edge
    for y in range(0, 60):
        for x in range(W):
            if noise2(x, y, 451) < 1 - y / 60:
                cv.set(x, y, FOREST_FLOOR[2] if (x + y) % 3 else FOREST_FLOOR[1])
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
    # fields south of the line, behind a fence: furrows of soil, cabbages in rows on
    # the first, ripening wheat swaying in the second
    SOILm = MATERIALS['soil']
    for y in range(380, 540):
        for x in range(20, 300):
            row = (y - 380) % 10
            wheat = 460 <= y < 540 and x > 160
            if wheat:
                stalk = (x + (y // 3) % 2) % 3
                c = '#E2BC5E' if stalk == 0 else '#C99A3C' if stalk == 1 else '#F2D27A'
                if row == 9:
                    c = '#A87E2C'
            else:
                c = SOILm[3] if row < 3 else SOILm[2] if row < 8 else SOILm[1]
                if row == 0:
                    c = SOILm[4]
            cv.set(x, y, c)
    for y in range(383, 540, 10):  # cabbages along the furrows
        for x in range(24, 296, 7):
            if 460 <= y < 540 and x > 160:
                continue
            cx = x + int(noise2(x, y, 452) * 2)
            for (px, py) in disc(cx, y + 2, 2.4):
                cv.set(px, py, MATERIALS['leaf'][3] if (px - cx) + (py - y - 2) < 0 else MATERIALS['leaf'][2])
            cv.set(cx - 1, y + 1, MATERIALS['leaf'][4])
    for x in range(161, 300, 2):  # the wheat's lit heads along its top edge
        cv.set(x, 460, '#F8E6A0'); cv.set(x + 1, 461, '#F2D27A')
    objects = [
        ('station', 'station_house', 66, 204), ('signal', 'semaphore', 20, 262), ('bench-p', 'bench', 190, 280),
        ('lamp-p1', 'lamp', 40, 268), ('lamp-p2', 'lamp', 220, 268), ('sack-p', 'sack', 178, 300), ('crate-p', 'crate', 160, 298),
        ('pine-n1', 'pine', 10, 20), ('tree-n2', 'tree', 90, 30), ('pine-n3', 'pine', 200, 14), ('tree-n4', 'tree_small', 260, 40),
        ('bush-1', 'bush', 250, 220), ('bush-2', 'bush', 6, 200),
        ('fence-1', 'fence_c', 18, 362), ('fence-2', 'fence_c', 78, 362), ('fence-3', 'fence_c', 138, 362),
        ('fence-4', 'fence_c', 198, 362), ('fence-5', 'fence_c', 258, 362),
        ('tree-s1', 'tree', 4, 500), ('tree-s2', 'tree_autumn', 250, 520), ('sack-f', 'sack', 120, 548),
    ]
    rails = {(x, y) for x in range(0, 246) for y in range(319, 338)}
    fields = {(x, y) for x in range(20, 300) for y in range(370, 540)}
    stands = {'town': (312, 300), 'platform': (130, 300), 'station': (118, 292)}
    return cv, objects, stands, rails | fields


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
    worlds.grass(cv, frame, FOREST_FLOOR)  # shaded forest floor
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
    # near the garden the forest floor brightens into the garden's own grass
    for y in range(H):
        for x in range(W - 56, W):
            t = (x - (W - 56)) / 56
            if noise2(x, y, 427) < t and cv.get(x, y)[:3] in DARK_FLOOR:
                cv.set(x, y, G[DARK_FLOOR.index(cv.get(x, y)[:3])])
    # dappled light through the canopy
    for i in range(14):
        lx, ly = int(noise2(i, 0, 426) * W), int(noise2(i, 1, 426) * H)
        light_pool(cv, lx, ly, 12 + i % 3 * 4, 6 + i % 2 * 3, GOLDm[2], water)
    light_pool(cv, 110, 140, 44, 26, G[4], water)
    objects = [
        # old trees closing in round the edges (none crosses the east border into the garden)
        ('tree-1', 'tree', -20, -30), ('pine-1', 'pine', 50, -40), ('tree-2', 'tree', 200, -26), ('pine-2', 'pine', 250, -36),
        ('tree-3', 'tree', -24, 200), ('pine-3', 'pine', -10, 330), ('tree-4', 'tree', 230, 160),
        ('tree-5', 'tree_small', 196, 300), ('pine-4', 'pine', 20, 470), ('tree-6', 'tree', 60, 480),
        ('pine-5', 'pine', 150, 490), ('tree-7', 'tree_small', 250, 504),
        ('oak', 'hollow_tree', 70, 30), ('ring', 'mushroom_ring', 128, 150), ('log-1', 'mossy_log', 200, 230),
        ('log-2', 'mossy_log', 40, 420), ('fern-1', 'fern', 30, 270), ('fern-2', 'fern', 180, 360),
        ('fern-3', 'fern', 260, 420), ('fern-4', 'fern', 90, 380), ('bench', 'forest_bench', 150, 170),
        ('willow', 'willow', 220, 340), ('bush-1', 'bush', 286, 380),
    ]
    # a split-log footbridge where the path crosses the young stream
    plank = {(x, y) for x in range(122, 140) for y in range(int(centre(130) - half(130)) - 3, int(centre(130) + half(130)) + 4)}
    for (x, y) in plank:
        cv.set(x, y, WOOD[4] if x in (122, 131) else WOOD[3] if x < 131 else WOOD[2])
    for y in range(min(yy for _, yy in plank), max(yy for _, yy in plank) + 1):
        cv.set(140, y, WTRm[0])
    stands = {'garden': (304, meadow.ORCHARD_WALK_Y), 'clearing': (110, 160), 'spring': (100, int(centre(96)) + 18)}
    return cv, objects, stands, (water | rock) - plank


# Every region is its own place (Matt, 17 Oct: "not just reskins of other worlds"): a
# zone outside the valley draws only its own region's props, plus the few shared
# things below that would really be found anywhere.
REGION_PROPS = {'junction': sp.props, 'canal': sp.props, 'springs': cdp.props, 'neon': cp.props, 'skyport': cp.props, 'gulch': wsp.props, 'oasis': wsp.props, 'caldera': cdp.props, 'harbour': hbp.props, 'castle': csp.props,
                'station': spp.props_station, 'lumen': spp.props_lumen}
SHARED_PROPS = {'steam_puff', 'drone', 'ring_post', 'fence_c'}
# Things above head height: they cast no ground shadow, never block a walk, draw on top.
OVERHEAD = {'steam_puff', 'drone', 'bunting'}


def build(name: str, fn, start: str):
    sprite_map = sprites()
    cv, objects, stands, *rest = fn()
    blocked_ground = rest[0] if rest else set()
    if name in REGION_PROPS:
        own = set(REGION_PROPS[name]()) | SHARED_PROPS
        foreign = sorted({k for (_i, k, _x, _y) in objects} - own)
        assert not foreign, f'{name} borrows props from another region: {foreign}'
    objects = [(i, k, x + sprite_map[k].ox, y + sprite_map[k].oy) for (i, k, x, y) in objects]
    shade = set()
    for (_id, key, x, y) in objects:
        if key not in OVERHEAD:
            shade |= detail.silhouette_shadow(sprite_map[key], x, y)
    for (sx, sy) in shade:
        style.darken(cv, sx, sy)
    walk = walk_grid([o for o in objects if o[1] not in OVERHEAD], sprite_map)
    cells = {(x // CELL, y // CELL) for (x, y) in blocked_ground}
    walk = [''.join('#' if (c, r) in cells else ch for c, ch in enumerate(row)) for r, row in enumerate(walk)]
    seen = reachable(walk, stands[start])
    lost = [k for k, (x, y) in stands.items() if (y // CELL, x // CELL) not in seen]
    assert not lost, f'{name}: not reachable on foot from {start}: {lost}'
    out = os.path.join(worlds.ROOT, 'assets', 'zones', name)
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, 'ground.png'), worlds.SCALE)
    preview = os.environ.get('ZONE_PREVIEW')
    if preview:
        prev = Canvas(W, H)
        prev.paste(cv, 0, 0)
        for (_id, key, x, y) in sorted(objects, key=lambda o: o[3] + sprite_map[o[1]].h + (900 if o[1] in OVERHEAD else 0)):
            prev.paste(sprite_map[key], x, y)
        if name == 'neon':
            rain(prev)
        prev.save(os.path.join(preview, f'zone-{name}.png'), 2)
    print('ok zone', name, W, H)
    return {'objects': objects, 'walk': walk, 'stands': stands, 'sprites': sprite_map}


# Where each zone sits on its region's grid (column, row), in zone-sized steps. The
# garden is the valley's (0, 0); it is drawn by garden.py and joins here by position.
LAYOUT = {
    'valley': {'ridge': (0, -1), 'woodland': (-1, 0), 'garden': (0, 0), 'riverside': (1, 0), 'town': (0, 1), 'park': (1, 1),
               'harbour': (0, 2), 'castle': (1, 2), 'halt': (-1, 1)},
    'steam': {'junction': (0, 0), 'canal': (0, 1)}, 'west': {'gulch': (0, 0), 'oasis': (-1, 0)}, 'lava': {'caldera': (0, 0), 'springs': (1, 0)},
    'neon': {'neon': (0, 0), 'skyport': (1, 0)}, 'space': {'station': (0, 0), 'lumen': (1, 0)},
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


def export(built: dict):
    """Write the props every zone uses and lib/zone-maps.ts (objects, walk grids,
    stands, the region layout and static image imports)."""
    props_dir = os.path.join(worlds.ROOT, 'assets', 'zones', 'props')
    os.makedirs(props_dir, exist_ok=True)
    for old in os.listdir(props_dir):
        os.remove(os.path.join(props_dir, old))
    used = {}
    for z in built.values():
        for (_i, k, _x, _y) in z['objects']:
            used[k] = z['sprites'][k]
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
    lines += [
        '};',
        '/** Each region\'s zones on a grid of zone-sized steps; the garden is the valley\'s (0, 0). */',
        f'export const regionLayout = {json.dumps({r: {z: list(p) for z, p in zs.items()} for r, zs in LAYOUT.items()})} as const;',
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


def main():
    built = {}
    built['town'] = build('town', town, 'garden')
    built['riverside'] = build('riverside', riverside, 'garden-north')
    built['woodland'] = build('woodland', woodland, 'garden')
    built['park'] = build('park', park, 'town')
    built['ridge'] = build('ridge', ridge, 'garden')
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
    built['castle'] = build('castle', castle, 'harbour')
    built['station'] = build('station', station, 'lift')
    built['lumen'] = build('lumen', lumen, 'shuttle')
    export(built)


if __name__ == '__main__':
    main()

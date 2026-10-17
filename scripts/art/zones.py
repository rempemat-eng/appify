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
import steampunk_props as sp  # noqa: E402
import cyber_props as cp  # noqa: E402
import western_props as wsp  # noqa: E402

BRASS, IRON, BRICK = (MATERIALS[k] for k in ('brass', 'iron', 'brick'))

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
    beyond the top edge count as road: the road runs on into the garden, so the border
    gets no turf edge and the two zones meet without a seam."""
    for (x, y) in mask:
        cv.set(x, y, P[4] if smooth_noise(x, y, 7, 40) > 0.7 else P[3])
    detail.grass_edge(cv, {(x, y) for (x, y) in mask if 0 <= x < W and y < H}, G, P, seed=11)
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
    south = worlds.thick([(150, 340), (176, 400), (196, 432)], 12, seed=6)
    worlds.paint_dirt(cv, south)
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
    rcx, rcy = 200, 470
    ring = oval(rcx, rcy, 52, 24)
    for (x, y) in ring:
        cv.set(x, y, P[3] if smooth_noise(x, y, 6, 9) > 0.55 else P[2])
    detail.grass_edge(cv, set(ring), G, P, seed=35)
    for k in range(26):
        a = 2 * math.pi * k / 26
        detail.pebble(cv, int(rcx + 54 * math.cos(a)), int(rcy + 26 * math.sin(a)), STONE, big=k % 2 == 0)
    for fb in ((258, 196, 40, 16, 2), (40, 452, 40, 16, 1)):
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
        ('bench-r1', 'bench', 96, 462), ('pole', 'pennant', 256, 420),
        # the south hedge (the Cove comes later) and framing trees
        ('hedge-s1', 'hedge', 0, 548), ('hedge-s2', 'hedge', 96, 548), ('hedge-s3', 'hedge', 192, 548),
        ('hedge-s4', 'hedge', 288, 548),
        ('tree-w1', 'tree', -26, 230), ('tree-w2', 'tree_small', -12, 470), ('tree-e1', 'tree', 286, 470),
        ('bush-e2', 'bush', 292, 228), ('bush-w3', 'bush', 54, 520), ('bush-w4', 'bush', 250, 520),
    ]
    ring_fence(objects, rcx, rcy, 58, 28)
    stands = {
        'garden': (160, 18), 'library': (70, 238), 'well': (160, 316), 'stall': (60, 424),
        'ring': (200, 470), 'park': (306, 300),
    }
    return cv, objects, stands


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
                  'notice_board': notice_board(), 'ring_post': ring_post(), 'pennant': pennant()})
    items.update(sp.props())
    items.update(cp.props())
    items.update(wsp.props())
    items['fence_c'] = gp.fence_h(60)
    return {key: style.finalize(sp, name=key) for key, sp in items.items()}


def walk_grid(objects, sprite_map) -> list[str]:
    blocked = set()
    for (_id, key, x, y) in objects:
        sp = sprite_map[key]
        foot = 20 if sp.w > 60 else 10 if key in ('tree', 'tree_small', 'tree_autumn', 'pine') else 6
        for yy in range(y + sp.h - foot, y + sp.h):
            for xx in range(x + 3, x + sp.w - 3):
                blocked.add((xx // CELL, yy // CELL))
    rows = []
    for r in range(H // CELL):
        row = ''
        for c in range(W // CELL):
            cx, cy = c * CELL + 2, r * CELL + 2
            row += '.' if (c, r) not in blocked and 0 <= cx < W and 6 <= cy <= H - 30 else '#'
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


def paint_rails(cv: Canvas, y0: int):
    """A railway across the zone: ballast, wooden sleepers lit on top, and two iron
    rails with a bright running edge."""
    for y in range(y0 - 3, y0 + 16):
        for x in range(W):
            n = noise2(x, y, 141)
            cv.set(x, y, STONE[2] if n > 0.55 else STONE[1] if n > 0.15 else STONE[3])
    for x in range(1, W, 7):
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
    stands = {'platform': (160, 120), 'tower': (160, 322), 'ring': (160, 492), 'workshop': (52, 248)}
    return cv, objects, stands


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


def light_pool(cv: Canvas, cx: int, cy: int, rx: int, ry: int, colour: str):
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
            if amt <= 0:
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


def gulch(frame: int = 0):
    """Dust Gulch, its own place: a town strung along one street that runs down from the
    railway's end, under a sandstone mesa on the east with the old mine cut into its
    foot. A dry creek bed of cracked mud winds across (the reason the well ran dry),
    crossed by a plank bridge; the water tower and windpump stand by it, still hoping.
    The corral sits under the cliff, and the wagon track leaves south-west to the oasis."""
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
    creek = worlds.thick([(-4, 300), (60, 296), (120, 320), (176, 312), (230, 336), (246, 360)], 9, seed=12)
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
    street = worlds.thick([(130, 78), (128, 200), (136, 300), (130, 420), (110, 500), (60, 560), (-6, 590)], 17, seed=13)
    for (x, y) in street:
        n = smooth_noise(x, y, 10, 213)
        c = DESERT[2] if n > 0.3 or (x + y) % 2 else DESERT[1]
        cv.set(x, y, c)
    for (x, y) in street:
        if (x - 7, y) not in street and (x - 6, y) in street:
            pass
    for y in range(80, H, 1):  # two wheel ruts following the street's centre line
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
        ('well', 'dry_well', 58, 360), ('wagon', 'wagon', 16, 470), ('hay-1', 'hay_bale', 96, 518), ('hay-2', 'hay_bale', 84, 530),
        ('mine', 'mine_portal', 248, 170), ('dyn-1', 'dynamite_crate', 228, 214), ('dyn-2', 'dynamite_crate', 300, 222),
        ('corral-n', 'corral_rail', ccx - 46, ccy - 36), ('corral-s', 'corral_rail', ccx - 46, ccy + 22),
        ('corral-w', 'corral_side', ccx - 52, ccy - 22),
        ('cactus-1', 'saguaro', 10, 380), ('cactus-2', 'saguaro_small', 224, 400), ('cactus-3', 'saguaro', 150, 520),
        ('cactus-4', 'saguaro_small', 286, 540), ('cactus-5', 'saguaro', 280, 60), ('cactus-6', 'saguaro_small', 4, 2),
        ('cactus-7', 'saguaro', 290, 300), ('weed-1', 'tumbleweed', 170, 380), ('weed-2', 'tumbleweed', 30, 540),
        ('skull', 'cow_skull', 250, 520), ('barrel-p', 'keg', 40, 62), ('sack-p', 'hay_bale', 196, 56),
    ]
    stands = {'platform': (128, 70), 'saloon': (58, 200), 'street': (132, 260), 'corral': (190, 470),
              'oasis': (30, 540), 'mine': (284, 236), 'well': (75, 404)}
    return cv, objects, stands


# Every region is its own place (Matt, 17 Oct: "not just reskins of other worlds"): a
# zone outside the valley draws only its own region's props, plus the few shared
# things below that would really be found anywhere.
REGION_PROPS = {'junction': sp.props, 'neon': cp.props, 'gulch': wsp.props}
SHARED_PROPS = {'steam_puff', 'drone', 'ring_post', 'fence_c'}


def build(name: str, fn, start: str):
    sprite_map = sprites()
    cv, objects, stands = fn()
    if name in REGION_PROPS:
        own = set(REGION_PROPS[name]()) | SHARED_PROPS
        foreign = sorted({k for (_i, k, _x, _y) in objects} - own)
        assert not foreign, f'{name} borrows props from another region: {foreign}'
    objects = [(i, k, x + sprite_map[k].ox, y + sprite_map[k].oy) for (i, k, x, y) in objects]
    shade = set()
    for (_id, key, x, y) in objects:
        if key not in ('steam_puff', 'drone'):
            shade |= detail.silhouette_shadow(sprite_map[key], x, y)
    for (sx, sy) in shade:
        style.darken(cv, sx, sy)
    walk = walk_grid([o for o in objects if o[1] not in ('steam_puff', 'drone')], sprite_map)
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
        for (_id, key, x, y) in sorted(objects, key=lambda o: o[3] + sprite_map[o[1]].h + (900 if o[1] in ('steam_puff', 'drone') else 0)):
            prev.paste(sprite_map[key], x, y)
        if name == 'neon':
            rain(prev)
        prev.save(os.path.join(preview, f'zone-{name}.png'), 2)
    print('ok zone', name, W, H)


def main():
    build('town', town, 'garden')
    build('junction', junction, 'platform')
    build('neon', neon_city, 'crossing')
    build('gulch', gulch, 'platform')


if __name__ == '__main__':
    main()

"""The home valley's places: the town, the harbour and the headland, the riverside and the park, the ridge cabin, the halt and the woodland.

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401
import ground  # noqa: F401

__all__ = ['town', 'harbour', 'headland', 'riverside', 'park', 'ridge', 'halt', 'woodland', 'sea_cliffs']


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

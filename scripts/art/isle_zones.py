"""The Tidebloom Isles: Lagoon Landing, the Rainforest, the Headwaters and Black-sand Cove.

Split out of zones.py (18 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['ISLE_TRAIL_NS', 'ISLE_TRAIL_WE', 'ISLE_RIVER_WE', 'ISLE_RIVER_NS', 'ISLE_RIVER_W', 'TROPIC', 'LAGOON', 'BASALT_R', 'FLOOR', 'isle_west_sea', 'isle_south_water', 'lagoon_tint', 'forest_edge', 'isle_ground', 'isle_water', 'river_pts', 'isle_trail', 'plank_bridge', 'isle_landing', 'isle_rainforest', 'isle_headwaters', 'isle_cove']


# ---- the Tidebloom Isles (Matt, 18 Oct 19:07: the world Codex drew) ----------------
# A dormant volcanic island off Driftwood Harbour, reached by the ferry to Lagoon Landing.
# Four zones on a 2 x 2 grid, walked as one loop: the Landing (south-west), the
# Rainforest (north-west), the Headwaters (north-east) and Black-sand Cove (south-east).
# Fresh water runs from the falls at the Headwaters through the Rainforest into the
# lagoon, crossed by footbridges; the sea is all round. Crossings, the same both sides:
ISLE_TRAIL_NS = 200   # x where the trail crosses the north/south borders
ISLE_TRAIL_WE = {'north': 140, 'south': 380}  # y where it crosses the west/east borders
ISLE_RIVER_WE = 300   # y where the river crosses from the Headwaters into the Rainforest
ISLE_RIVER_NS = 90    # x where it crosses from the Rainforest into the Landing
ISLE_RIVER_W = 9      # its half-width
TROPIC = ['#1F3A22', '#2E5A30', '#3F7A3A', '#5A9A46', '#86BE5E']
LAGOON = ['#1E6E7A', '#2A8E96', '#45B2B0', '#7FD6CC', '#C8F0E6']
BASALT_R = MATERIALS['basalt']
FLOOR = ['#1A2A1C', '#263A26', '#34492E', '#46603A', '#5E7A46']  # the rainforest's floor


def isle_west_sea(y_region: int) -> int:
    """Where the open sea ends on the island's west coast (x in zone pixels), at a y in
    the island's own pixels (the rainforest's rows first, then the landing's)."""
    return 26 + int(smooth_noise(0, y_region, 30, 924) * 12) - 8


def isle_south_water(x_region: int) -> int:
    """Where the water begins along the island's south shore, at an x in the island's
    own pixels (the landing's columns, then the cove's): the lagoon in the west, the
    open sea past the cove's beach in the east."""
    lagoon = 470 + int(smooth_noise(x_region, 0, 24, 913) * 16)
    if x_region < W:
        return lagoon
    x = x_region - W
    sea = 300 + int(math.sin(x / 50) * 20 + smooth_noise(x, 0, 30, 942) * 16) + 90 + int(smooth_noise(x, 1, 24, 943) * 14)
    t = min(1.0, x / 140)
    return int(lagoon * (1 - t) + sea * t)


def lagoon_tint(cv: Canvas, pts, near, seed: int):
    """Recolour water from the open sea's blues to the lagoon's turquoise where `near`
    (a function of x, y giving 0..1) says it is shallow and sheltered, dithered."""
    sea = MATERIALS['water']
    for (x, y) in pts:
        if noise2(x, y, seed) < near(x, y):
            c = '#%02X%02X%02X' % cv.get(x, y)[:3]
            if c in sea:
                cv.set(x, y, LAGOON[sea.index(c)])


def forest_edge(cv: Canvas, side: str, seed: int):
    """Where a zone meets the rainforest: its own ground gives way to the forest's floor
    over the last 56 pixels on that side, dithered, so the seam is grown, not cut."""
    for y in range(H):
        for x in range(W):
            d = {'west': x, 'north': y}[side]
            if d < 56 and noise2(x, y, seed) * 56 > d:
                n = smooth_noise(x, y, 16, 921)
                cv.set(x, y, FLOOR[3] if n > 0.6 else FLOOR[2] if n > 0.22 or (x + y) % 2 else FLOOR[1])


def isle_ground(cv: Canvas, ramp, seed: int, zone: str = ''):
    """Lush turf: broad patches in two close tones, small bright tufts. Drawn in the
    island's own coordinates, so the turf runs on unbroken from one zone into the next."""
    ox, oy = ((LAYOUT['isles'][zone][0] * W, LAYOUT['isles'][zone][1] * H) if zone else (0, 0))
    if zone:
        seed = 911
    for y in range(H):
        for x in range(W):
            gx, gy = x + ox, y + oy
            n = smooth_noise(gx, gy, 20, seed)
            c = ramp[3] if n > 0.5 else ramp[2] if n > 0.25 or (gx + gy) % 2 else ramp[1]
            if noise2(gx, gy, seed + 1) > 0.985:
                c = ramp[4]
            cv.set(x, y, c)


def isle_water(cv: Canvas, pts: set, ramp, seed: int, surf: bool = False):
    """Water: deeper in the middle of a body, a bright line where it meets land; a few
    ripples; surf (white foam) on an open coast."""
    # (past the zone's edge the water carries on into the next zone or the open sea)
    def wet(x, y):
        return (x, y) in pts or not (0 <= x < W and 0 <= y < H)
    for (x, y) in pts:
        land = sum(not wet(x + dx, y + dy) for dx in (-6, 0, 6) for dy in (-6, 0, 6))
        c = ramp[0] if land == 0 and smooth_noise(x, y, 30, seed) > 0.5 else ramp[1] if land == 0 else ramp[2]
        if land and (not wet(x + 1, y) or not wet(x - 1, y) or not wet(x, y + 1) or not wet(x, y - 1)):
            c = ramp[3] if not surf else '#F4F8F8'
        elif surf and land and (x + y) % 3 == 0:
            c = '#DDEBEE'
        if (y + int(math.sin(x / 9) * 2)) % 17 == 0 and land == 0 and noise2(x // 6, y, seed) > 0.4:
            c = ramp[3]
        cv.set(x, y, c)


def river_pts(points) -> set:
    return {(x, y) for (x, y) in worlds.thick(points, ISLE_RIVER_W, seed=0) if 0 <= x < W and 0 <= y < H}


def isle_trail(cv: Canvas, points, seed: int) -> set:
    """A trodden earth trail, like the valley's roads (it reads as a path on the map)."""
    pts = {(x, y) for (x, y) in worlds.thick(points, 9.5, seed=seed)}
    paint_road(cv, pts)
    return {(x, y) for (x, y) in pts if 0 <= x < W and 0 <= y < H}


def plank_bridge(cv: Canvas, x0: int, y0: int, w: int, h: int, vertical: bool = True):
    """A footbridge of planks between rope rails, its shadow on the water below.
    Returns (deck, rails): the deck is walkable, the rails are not."""
    deck, rails = set(), set()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            across = (x - x0) if vertical else (y - y0)
            span = w if vertical else h
            along = (y - y0) if vertical else (x - x0)
            if across < 2 or across >= span - 2:
                rails.add((x, y))
                c = MATERIALS['rope'][2] if across in (0, span - 2) else MATERIALS['rope'][0]
                if along % 8 == 0:
                    c = WOOD[1]  # a post
            else:
                deck.add((x, y))
                c = WOOD[3] if along % 4 else WOOD[1]
                if along % 4 == 1:
                    c = WOOD[4]
            cv.set(x, y, c)
    if vertical:
        for y in range(y0, y0 + h):
            style.darken(cv, x0 + w, y); style.darken(cv, x0 + w + 1, y)
    else:
        for x in range(x0, x0 + w):
            style.darken(cv, x, y0 + h); style.darken(cv, x, y0 + h + 1)
    return deck, rails


def isle_landing(frame: int = 0):
    """Lagoon Landing: where the ferry from Driftwood ties up. A plank pier runs out into
    the lagoon's clear shallows; the boathouse stands at the shore. The river from the
    rainforest comes down on the west and spreads into the lagoon; the trail goes north
    into the forest and east along the shore to the cove."""
    cv = Canvas(W, H)
    isle_ground(cv, TROPIC, 911, 'landing')
    # sand along the lagoon shore
    forest_edge(cv, 'north', 918)
    def shore_x(y):  # the lagoon's east shore along the west, widening to the south;
        # at the top it is the rainforest's own coast carried on
        own = 40 + int(smooth_noise(0, y, 30, 912) * 14) + 30 * min(1, max(0, (y - 380) / 60))
        t = min(1.0, y / 80)
        return int(isle_west_sea(H + y) * (1 - t) + own * t)
    lagoon = set()
    sand = set()
    rocks = set()
    for y in range(H):
        sx = shore_x(y)
        for x in range(W):
            if x < sx or y > isle_south_water(x):
                lagoon.add((x, y))
            elif y < 80 and x < sx + 8 * (1 - y / 80):
                rocks.add((x, y))  # the black rocks of the coast, giving way to sand
            elif x < sx + 18 or y > isle_south_water(x) - 20:
                sand.add((x, y))
    for (x, y) in rocks:
        cv.set(x, y, BASALT_R[3] if (x * 3 + y) % 7 == 0 else BASALT_R[2] if (x + y) % 3 else BASALT_R[1])
    S = MATERIALS['sand']
    for (x, y) in sand:
        cv.set(x, y, S[2] if noise2(x, y, 914) > 0.2 else S[1])
    # the river from the rainforest, out into the lagoon
    river = river_pts([(ISLE_RIVER_NS, -12), (84, 120), (60, 220), (30, 300)]) - lagoon
    water = lagoon | river
    isle_water(cv, lagoon, MATERIALS['water'], 915)
    # the open sea along the coast at the top turns to the lagoon's shallows further south
    lagoon_tint(cv, lagoon, lambda x, y: min(1.0, max(0.0, (y - 40) / 160)), 919)
    isle_water(cv, river, LAGOON, 916)
    # the pier: planks out over the shallows to where the ferry ties up
    pier, rails = plank_bridge(cv, 136, 470, 30, 100, vertical=True)
    trail = isle_trail(cv, [(ISLE_TRAIL_NS, -12), (196, 200), (170, 330), (150, 440), (151, 474)], 917)
    trail |= isle_trail(cv, [(170, 330), (250, 370), (W + 12, ISLE_TRAIL_WE['south'])], 918)
    objects = [
        ('boathouse', 'boathouse', 176, 390), ('ferry', 'island_ferry', 168, 520), ('canoe', 'canoe', 70, 420),
        ('palm-1', 'palm', 110, 180), ('palm-2', 'palm', 260, 250), ('palm-3', 'palm', 90, 300),
        ('fern-1', 'tree_fern', 250, 40), ('fern-2', 'tree_fern', 130, 60), ('jt-1', 'jungle_tree', 230, 60),
        ('hib-1', 'hibiscus', 120, 250), ('hib-2', 'hibiscus', 280, 320), ('mon-1', 'monstera', 220, 200),
        ('rock-1', 'black_rock_small', 60, 360), ('heron', 'heron', 20, 160),
    ]
    WATER_MASKS['isle_landing'] = water - pier
    stands = {'pier': (151, 556), 'rainforest': (ISLE_TRAIL_NS, 6), 'cove': (314, ISLE_TRAIL_WE['south']),
              'boathouse': (196, 474)}
    return cv, objects, stands, (water - pier) | rails | rocks


def isle_rainforest(frame: int = 0):
    """The Rainforest: giants with buttress roots, tree ferns and big-leafed plants under
    a closed canopy, the floor dark and damp. The river from the falls winds through it
    to the lagoon, crossed by a footbridge; the sea breaks on black rocks along the
    north and west."""
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 16, 921)
            c = FLOOR[3] if n > 0.6 else FLOOR[2] if n > 0.22 or (x + y) % 2 else FLOOR[1]
            if noise2(x, y, 922) > 0.97:
                c = FLOOR[4]  # a lit leaf on the floor
            cv.set(x, y, c)
    # the coast: sea beyond black rock on the north and the west
    sea = set()
    rocks = set()
    for y in range(H):
        for x in range(W):
            north = 34 + int(smooth_noise(x, 0, 30, 923) * 14)
            west = isle_west_sea(y) + 8
            if y < north - 8 or x < west - 8:
                sea.add((x, y))
            elif y < north or x < west:
                rocks.add((x, y))
    isle_water(cv, sea, MATERIALS['water'], 925, surf=True)
    for (x, y) in rocks:
        cv.set(x, y, BASALT_R[3] if (x * 3 + y) % 7 == 0 else BASALT_R[2] if (x + y) % 3 else BASALT_R[1])
    river = river_pts([(W + 12, ISLE_RIVER_WE), (220, 330), (120, 420), (ISLE_RIVER_NS, H + 12)])
    isle_water(cv, river, LAGOON, 926)
    trail = isle_trail(cv, [(ISLE_TRAIL_NS, H + 12), (200, 420), (186, 300), (210, 200), (260, 150), (W + 12, ISLE_TRAIL_WE['north'])], 927)
    deck, rails = plank_bridge(cv, 178, 326, 30, 50, vertical=True)
    objects = [
        ('jt-1', 'jungle_tree', 30, 90), ('jt-2', 'jungle_tree', 100, 180), ('jt-3', 'jungle_tree', 226, 230),
        ('jt-4', 'jungle_tree', 20, 330), ('jt-5', 'jungle_tree', 226, 420), ('jt-6', 'jungle_tree', 110, 60),
        ('fern-1', 'tree_fern', 150, 120), ('fern-2', 'tree_fern', 60, 260), ('fern-3', 'tree_fern', 270, 330),
        ('fern-4', 'tree_fern', 30, 470), ('fern-5', 'tree_fern', 260, 500), ('mon-1', 'monstera', 140, 260),
        ('mon-2', 'monstera', 240, 120), ('mon-3', 'monstera', 70, 400), ('mon-4', 'monstera', 150, 500),
        ('hib', 'hibiscus', 280, 60), ('log', 'mossy_log', 120, 360),
    ]
    WATER_MASKS['isle_rainforest'] = (sea | river) - deck
    stands = {'landing': (ISLE_TRAIL_NS, H - 6), 'headwaters': (314, ISLE_TRAIL_WE['north']), 'bridge': (193, 390)}
    return cv, objects, stands, ((river - deck) | rails | sea | rocks)


def isle_headwaters(frame: int = 0):
    """The Headwaters: the island's old volcano rises behind, its flank green with moss
    and fern, and a waterfall drops from it into a deep round pool. The river leaves the
    pool west for the rainforest; a footbridge carries the trail over it, and a spur goes
    to the pool's edge. The sea breaks on the cliffs to the east."""
    cv = Canvas(W, H)
    isle_ground(cv, TROPIC, 931, 'headwaters')
    forest_edge(cv, 'west', 939)
    MOSS = ['#22362A', '#2F4A34', '#3E6040', '#56784A']
    # the volcano's flank across the top: a steep jumble of great mossy basalt blocks
    # stepping up out of the forest, ferns in the joints between them (blocked)
    flank = set()
    tops = {}
    for x in range(W):
        tops[x] = 120 + int(math.sin(x / 40) * 18 + smooth_noise(x, 0, 20, 932) * 14)
        for y in range(0, tops[x]):
            # the deep shade between the blocks: wet dark green, not black
            cv.set(x, y, TROPIC[0] if (x + y) % 3 else BASALT_R[1])
            flank.add((x, y))
    blocks = []
    for i in range(70):  # back (high) to front (low), so the lower blocks overlap
        bx = int(noise2(i, 0, 951) * (W + 20)) - 10
        by = int(noise2(i, 1, 951) * 150) - 20
        if by + 8 > tops[max(0, min(W - 1, bx))]:
            continue
        blocks.append((by, bx, 10 + noise2(i, 2, 951) * 12, 7 + noise2(i, 3, 951) * 7, i))
    for (by, bx, rx, ry, i) in sorted(blocks):
        pts = {(x, y) for (x, y) in oval(bx, by, rx, ry) if (x, y) in flank}
        if len(pts) > 12:
            style.facet_stone(cv, pts, BASALT_R, moss=TROPIC, seed=960 + i, outline=None)
    for i in range(40):  # ferns and moss tumbling from the joints
        fx = int(noise2(i, 4, 951) * W)
        fy = int(noise2(i, 5, 951) * (tops[max(0, min(W - 1, fx))] - 6))
        style.leafy(cv, fx, fy, 4 + noise2(i, 6, 951) * 3, 3, TROPIC, r=1.8, seed=970 + i)
    for x in range(W):  # the forest's dark edge at the flank's foot
        for d in range(3):
            cv.set(x, tops[x] - 1 - d, TROPIC[0] if d == 0 else TROPIC[1] if (x + d) % 2 else BASALT_R[0])
    # the top-left corner meets the rainforest's sea
    sea = {(x, y) for x in range(W) for y in range(H)
           if (x < 60 - int(smooth_noise(0, y, 20, 934) * 20) and y < 34 + int(smooth_noise(x, 0, 30, 923) * 14) - 8)}
    east = {(x, y) for x in range(W) for y in range(H) if x > 286 + int(smooth_noise(0, y, 30, 935) * 12)}
    isle_water(cv, sea | east, MATERIALS['water'], 936, surf=True)
    # the fall: white water down the flank into the pool
    pool = {(x, y) for x in range(170, 270) for y in range(140, 215)
            if math.hypot((x - 220) / 42, (y - 176) / 30) < 1 - (smooth_noise(x, y, 10, 955) - 0.5) * 0.3}
    for y in range(0, 160):
        half = 7 + y / 40
        for x in range(200, 240):
            off = abs(x - 220 - math.sin(y / 17) * 1.5)
            if off < half:
                # falling water: white streaks down a pale sheet, the edges in shadow
                streak = (x * 5 + int(y * 0.15)) % 7
                c = '#F4F8F8' if streak < 3 else LAGOON[4] if off < half - 2 else LAGOON[3]
                cv.set(x, y, c)
                flank.add((x, y))
            elif off < half + 2:
                cv.set(x, y, BASALT_R[0])
    river = river_pts([(200, 196), (176, 226), (150, 236), (128, 256), (90, 280), (60, 290), (-12, ISLE_RIVER_WE)])
    isle_water(cv, pool | river, LAGOON, 937)
    for (x, y) in pool:  # foam where the fall lands, thinning outward
        d = math.hypot(x - 220, (y - 154) * 1.4)
        if d < 14 and noise2(x, y, 956) * 14 > d - 2:
            cv.set(x, y, '#F4F8F8' if (x + y) % 2 else LAGOON[4])
    deck, rails = plank_bridge(cv, 113, 234, 30, 46, vertical=True)
    trail = isle_trail(cv, [(-12, ISLE_TRAIL_WE['north']), (60, 160), (110, 200), (128, 255), (150, 330), (196, 430), (ISLE_TRAIL_NS, H + 12)], 938)
    trail |= isle_trail(cv, [(150, 330), (200, 250)], 939)  # the spur to the pool's edge
    objects = [
        ('fern-1', 'tree_fern', 20, 200), ('fern-2', 'tree_fern', 260, 230), ('fern-3', 'tree_fern', 60, 400),
        ('jt-1', 'jungle_tree', 210, 330), ('jt-2', 'jungle_tree', 10, 460), ('mon-1', 'monstera', 160, 380),
        ('mon-2', 'monstera', 250, 450), ('hib-1', 'hibiscus', 90, 330), ('rock-1', 'black_rock', 230, 470),
        ('rock-2', 'black_rock_small', 120, 480),
    ]
    WATER_MASKS['isle_headwaters'] = (sea | east | pool | river) - deck
    stands = {'rainforest': (6, ISLE_TRAIL_WE['north']), 'pool': (196, 256), 'cove': (ISLE_TRAIL_NS, H - 6)}
    return cv, objects, stands, ((pool | river) - deck) | rails | flank | sea | east


def isle_cove(frame: int = 0):
    """Black-sand Cove: the trail comes down out of the trees onto a beach of black volcanic
    sand where the surf runs in white; rocks of old lava stand in the shallows, a turtle
    rests above the tide line. The shore path goes west back to the landing."""
    cv = Canvas(W, H)
    isle_ground(cv, TROPIC, 941, 'cove')
    SAND = BASALT_R
    def sea_y(x):
        return isle_south_water(W + x)
    def beach_y(x):  # a narrow strip by the lagoon, a broad black beach to the east
        return sea_y(x) - 20 - int(70 * min(1.0, x / 140))
    sand, sea = set(), set()
    for x in range(W):
        for y in range(H):
            east = x > 286 + int(smooth_noise(0, y, 30, 935) * 12) - max(0, y - 300) // 3
            if y >= sea_y(x) or east:
                sea.add((x, y))
            elif y >= beach_y(x):
                sand.add((x, y))
    LIGHT = MATERIALS['sand']
    for (x, y) in sand:
        if noise2(x, y, 949) * 160 > x - 60:  # the landing's pale sand, darkening east
            cv.set(x, y, LIGHT[2] if noise2(x, y, 914) > 0.2 else LIGHT[1])
            continue
        n = smooth_noise(x, y, 10, 944)
        cv.set(x, y, SAND[2] if n > 0.5 else SAND[1] if (x + y) % 2 else SAND[2])
        if noise2(x, y, 945) > 0.97:
            cv.set(x, y, '#E6EEF2')  # a pale shell
    isle_water(cv, sea, MATERIALS['water'], 946, surf=True)
    lagoon_tint(cv, sea, lambda x, y: min(1.0, max(0.0, (160 - x) / 140)), 947)
    trail = isle_trail(cv, [(ISLE_TRAIL_NS, -12), (196, 200), (176, 290), (120, 360), (-12, ISLE_TRAIL_WE['south'])], 948)
    objects = [
        ('rock-1', 'black_rock', 236, 330), ('rock-2', 'black_rock_small', 110, 330), ('rock-3', 'black_rock', 150, 360),
        ('turtle', 'sea_turtle', 200, 340), ('palm-1', 'palm', 250, 210), ('palm-2', 'palm', 60, 230),
        ('fern-1', 'tree_fern', 260, 60), ('jt-1', 'jungle_tree', 20, 40), ('hib-1', 'hibiscus', 110, 120),
        ('canoe', 'canoe', 210, 360),
    ]
    WATER_MASKS['isle_cove'] = sea
    stands = {'headwaters': (ISLE_TRAIL_NS, 6), 'landing': (6, ISLE_TRAIL_WE['south']), 'beach': (180, 330)}
    return cv, objects, stands, sea


# how each island zone's open ground is dressed (zones.dress)
DRESS.update({'landing': ('meadow', TROPIC[2:4], 0.3), 'headwaters': ('meadow', TROPIC[2:4], 0.3),
              'cove': ('meadow', TROPIC[2:4], 0.26), 'rainforest': ('forest', None, 0.3)})

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

__all__ = ['town', 'harbour', 'headland', 'riverside', 'park', 'ridge', 'halt', 'woodland']


# ---------------------------------------------------------------------------------------
# Natural shapes and small living things drawn into the ground (docs/vision/art-faults.md,
# rules 3, 9 and 11: no perfect shapes in nature, every surface has its material, drawn
# to the detail target from the first draw). Each is lit from the upper left and sits on
# the ground with a contact shadow.
# ---------------------------------------------------------------------------------------
LEAF = MATERIALS['leaf']
WTR = MATERIALS['water']
FOAM = '#EEF5F8'


def blob(cx: float, cy: float, rx: float, ry: float, seed: int = 0, rough: float = 0.18) -> set:
    """An organic closed shape: an ellipse whose radius wanders with the angle in a few
    slow lobes, so ponds, clearings and rocks never read as a drawn ellipse."""
    ph = [noise2(seed, k, 771) * 6.283 for k in range(4)]
    pts = set()
    span = 1 + rough * 1.3
    for y in range(int(cy - ry * span) - 2, int(cy + ry * span) + 3):
        for x in range(int(cx - rx * span) - 2, int(cx + rx * span) + 3):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            a = math.atan2(dy, dx)
            r = 1 + rough * (0.55 * math.sin(2 * a + ph[0]) + 0.35 * math.sin(3 * a + ph[1])
                             + 0.2 * math.sin(5 * a + ph[2]) + 0.1 * math.sin(8 * a + ph[3]))
            if dx * dx + dy * dy <= r * r:
                pts.add((x, y))
    return pts


def edge_of(mask: set) -> set:
    return {(x, y) for (x, y) in mask if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def contact(cv: Canvas, cx: float, cy: float, rx: float, ry: float):
    """A hard contact shadow on the ground, offset down and right."""
    style.cast_shadow(cv, cx + 1, cy + 1, rx, ry)


def boulder(cv: Canvas, cx: float, base: float, w: float, h: float, seed: int, moss: bool = True,
            ramp=None) -> set:
    """One stone lying on the ground: a lumpy mass with a lit top plane, a mid front, a
    dark right flank and base, a crack or two and moss on its top (style.facet_stone),
    on its own contact shadow. Returns its pixels."""
    ramp = ramp or STONE
    pts = blob(cx, base - h / 2, w / 2, h / 2, seed=seed, rough=0.16)
    pts = {(x, y) for (x, y) in pts if y < base}
    contact(cv, cx + 1, base - 1, w / 2 + 1, max(2, h / 5))
    style.facet_stone(cv, pts, ramp, moss=LEAF if moss else None, seed=seed)
    return pts


def outcrop(cv: Canvas, stones, seed: int = 0, moss: bool = True) -> set:
    """Several boulders heaped together, drawn back to front, with dark crevices
    between them: a rock face with form rather than a dithered oval.
    `stones` are (cx, base, w, h)."""
    pts = set()
    for i, (cx, base, w, h) in enumerate(sorted(stones, key=lambda s: s[1])):
        pts |= boulder(cv, cx, base, w, h, seed + i * 7, moss=moss)
    return pts


def fern(cv: Canvas, x: int, y: int, seed: int = 0, size: float = 1.0):
    """A fern growing from (x, y): seven arching fronds fanning up and out, each a
    spine with paired leaflets shrinking to its tip; the upper leaflets lit, the lower
    ones in shade, the back fronds darker, on a small shadow."""
    contact(cv, x + 1, y, 6 * size, 2)
    fronds = [(-160, 0.7, 1), (-20, 0.7, 1), (-125, 1.0, 2), (-55, 1.0, 2), (-100, 0.95, 3), (-78, 0.9, 3),
              (-140, 0.8, 3), (-38, 0.8, 3)]
    for k, (deg, ln, tier) in enumerate(fronds):
        a = math.radians(deg + (noise2(seed, k, 781) - 0.5) * 16)
        L = (8 + noise2(seed, k, 782) * 3) * ln * size
        steps = int(L * 1.6)
        for s in range(steps):
            t = s / max(1, steps - 1)
            px = x + math.cos(a) * L * t
            py = y + math.sin(a) * L * t + 5 * size * t * t * (0.6 if abs(math.cos(a)) > 0.5 else 0.3)
            ix, iy = int(round(px)), int(round(py))
            cv.set(ix, iy, LEAF[1 + (tier > 1)])
            if s % 2 == 0 and t < 0.92:
                leaf = max(1, int((1 - t) * 3 * size + 0.5))
                nx, ny = -math.sin(a), math.cos(a)
                for side in (-1, 1):
                    for q in range(1, leaf + 1):
                        lx, ly = int(round(px + nx * q * side)), int(round(py + ny * q * side - q * 0.4))
                        up = (ny * side) < 0  # this leaflet faces up, toward the light
                        c = LEAF[min(4, tier + 1)] if up else LEAF[max(1, tier - 1)]
                        if up and q == leaf and tier == 3:
                            c = LEAF[4]
                        cv.set(lx, ly, c)
    cv.set(x, y, LEAF[0]); cv.set(x + 1, y, LEAF[0])


def mushroom(cv: Canvas, x: int, y: int, size: int, seed: int = 0, cap=('#7A2A26', '#B0403A', '#D45E4A', '#F08A6E')):
    """A toadstool standing at (x, y): a pale stem, a domed cap lit on its upper left
    with white spots, a dark gill line under the rim and a contact shadow."""
    contact(cv, x + 1, y, size * 0.7 + 1, 1)
    hgt = size + 1
    for k in range(hgt):
        cv.set(x, y - k, '#E8DCC8' if k < hgt - 1 else '#C9B89C')
        if size > 2:
            cv.set(x + 1, y - k, '#C9B89C')
    top = y - hgt
    rx = size * 0.8 + 0.6
    for dy in range(-size // 2 - 1, 1):
        for dx in range(-int(rx) - 1, int(rx) + 2):
            if (dx / (rx + 0.3)) ** 2 + (dy / (size / 2 + 0.8)) ** 2 <= 1:
                lit = dx < 0 and dy < -size // 4
                c = cap[3] if lit and dx < -1 else cap[2] if dx <= 0 else cap[1]
                if dy == 0:
                    c = cap[0]
                cv.set(x + dx + (size > 2) // 2, top + dy, c)
    if size >= 2:
        cv.set(x - 1, top - size // 2, '#F7F2E8')
        if size >= 3:
            cv.set(x + 1 + (seed % 2), top - 1, '#F7F2E8')


def waterfall(cv: Canvas, x0: int, w: int, y0: int, y1: int, seed: int = 0):
    """A narrow fall of water from a lip at y0 to a pool at y1: a lit curl over the lip,
    streaks running down (lighter on the left, toward the light), a darker right edge,
    and white water where it lands."""
    for y in range(y0, y1):
        for x in range(x0, x0 + w):
            f = (x - x0) / max(1, w - 1)
            c = WTR[3] if f < 0.7 else WTR[2]
            if f < 0.2:
                c = WTR[4]
            run = (y - y0 + int(noise2(x, seed, 783) * 9)) % 7
            if 0.2 <= f < 0.7 and run < 3:
                c = WTR[4] if (x + seed) % 2 else FOAM
            if f >= 0.85:
                c = WTR[1]
            cv.set(x, y, c)
    cv.hline(x0 - 1, y0, w + 2, WTR[4]); cv.hline(x0, y0 - 1, w, FOAM)
    for k in range(w + 6):  # where it lands: white water in a broken crescent
        xx = x0 - 3 + k
        cv.set(xx, y1 + (k % 3 == 0), FOAM if k % 4 else WTR[4])
        if 1 < k < w + 4:
            cv.set(xx, y1 + 1 + (k % 2), WTR[4])
    for k in range(4):  # spray
        cv.set(x0 - 4 + k * (w + 6) // 3, y1 - 2 - (k % 2), FOAM)


def water_body(cv: Canvas, water: set, deep=None, seed: int = 0, glints: int = 40):
    """Still or slow water in an organic shape: a dark band under its near (north) bank
    where the bank casts its shadow, deeper colour toward the middle, short highlights
    on the open water and a lit wet edge along the far (south) bank."""
    deep = deep or set()
    water = set(water) | {(x, y) for x in range(-3, W + 3) for y in (-3, -2, -1, H, H + 1, H + 2)
                          if (min(max(x, 0), W - 1), min(max(y, 0), H - 1)) in water}  # it runs on past the edge
    water |= {(x, y) for y in range(H) for x in (-3, -2, -1, W, W + 1, W + 2) if (min(max(x, 0), W - 1), y) in water}
    for (x, y) in water:
        c = WTR[1] if (x, y) in deep else WTR[2]
        if (x, y) in deep and smooth_noise(x, y, 7, seed + 1) > 0.66:
            c = WTR[2]
        if (x, y - 1) not in water or (x, y - 2) not in water:
            c = WTR[0]
        elif (x, y - 3) not in water and (x + y) % 2:
            c = WTR[1]
        cv.set(x, y, c)
    for (x, y) in water:
        if (x, y + 1) not in water and (x, y - 3) in water:
            cv.set(x, y, WTR[3])  # the wet edge catching the light
    for i in range(glints):
        x = int(noise2(i, seed, 784) * 400)
        y = int(noise2(seed, i, 785) * 700)
        if all((x + t, y) in water and (x + t, y - 3) in water and (x + t, y + 2) in water for t in range(-1, 5)):
            cv.hline(x, y, 3 + (i % 2), WTR[3])
            if i % 3 == 0:
                cv.set(x + 1, y, WTR[4])


def bank(cv: Canvas, water: set, keep=frozenset(), seed: int = 0, sandy: bool = False):
    """The ground round water: on the far (south) side a lit lip of earth or sand
    dropping to the water; on the near (north) side the turf overhangs as a dark lip
    with a mossy shadow; pebbles and the odd reed clump at the waterline."""
    ring = set()
    for (x, y) in water:
        for dx, dy in ((0, -1), (0, -2), (0, 1), (0, 2), (-1, 0), (1, 0), (-2, 0), (2, 0)):
            q = (x + dx, y + dy)
            if q not in water and q not in keep:
                ring.add(q)
    for (x, y) in ring:
        below_water = any((x, y + k) in water for k in (1, 2))
        above_water = any((x, y - k) in water for k in (1, 2))
        if below_water:  # the north bank: turf breaking over the water
            c = G[1] if (x, y + 1) in water else G[2]
            if (x, y + 1) in water and noise2(x, y, seed + 786) > 0.6:
                c = LEAF[1]
        elif above_water:  # the south bank: a lit lip of earth or sand
            c = (SAND_R[2] if (x, y - 1) in water else SAND_R[1]) if sandy else (SOIL_R[5] if (x, y - 1) in water else SOIL_R[4])
        else:
            c = SOIL_R[4] if not sandy else SAND_R[1]
        cv.set(x, y, c)
    for (x, y) in ring:
        if noise2(x, y, seed + 787) > 0.965 and (x, y - 1) in water:
            detail.pebble(cv, x, y, STONE, big=noise2(x, y, seed + 788) > 0.5)
    return ring


SAND_R = MATERIALS['sand']
SOIL_R = MATERIALS['soil']  # (earth banks: kept off the path colours, so the lint reads them as ground)


def reeds(cv: Canvas, x: int, y: int, seed: int = 0, n: int = 6):
    """A clump of reeds standing in the shallows: blades of different heights, lit on
    the left, two brown seed heads."""
    for k in range(n):
        bx = x + k * 2 - n + int(noise2(seed, k, 789) * 2)
        h = 6 + int(noise2(k, seed, 790) * 6)
        lean = 1 if k > n // 2 else -1 if k < n // 3 else 0
        for t in range(h):
            xx = bx + (lean if t > h * 0.6 else 0)
            cv.set(xx, y - t, LEAF[3] if k % 2 == 0 and t > 1 else LEAF[2] if t > 1 else LEAF[1])
        if k in (1, n - 2):
            cv.vline(bx + lean, y - h - 2, 3, WOOD[1]); cv.set(bx + lean, y - h - 2, WOOD[2])
    cv.hline(x - n, y + 1, 2 * n, WTR[3])


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
    # the town grows down the road toward the harbour: lanes to the houses' doors
    south |= worlds.thick([(160, 424), (230, 426), (276, 424)], 6, seed=71)
    south |= worlds.thick([(160, 524), (200, 526), (228, 522)], 6, seed=72)
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
    for fb in ((258, 196, 40, 16, 2),):  # a planter by the red house's door
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
        # trees framing the road south (no hedge along the border: open land runs on)
        ('tree-s1', 'tree_small', 20, 500), ('bush-s2', 'bush', 250, 540), ('tree-w1', 'tree', 2, 196),
        ('house-s1', 'house_red', 188, 444), ('pot-s1', 'potted_plant', 252, 504), ('tree-e1', 'tree', 280, 446),
        ('bush-e2', 'bush', 286, 228), ('bush-w4', 'bush', 182, 396),
        # trees across the borders: the woods of the halt and the park reach into the town
        ('tree-x1', 'tree_small', -22, 120), ('tree-x2', 'tree', 284, 112),
        ('bunting', 'bunting', 60, 238), ('cat', 'cat', 182, 352),
    ]
    ring_fence(objects, rcx, rcy, 58, 28)
    stands = {
        'garden': (160, 18), 'library': (70, 238), 'well': (160, 316), 'stall': (60, 424),
        'ring': (76, 486), 'park': (306, 300), 'harbour': (160, 540), 'halt': (8, 300),
    }
    return cv, objects, stands


def west_shore(y: int) -> int:
    """Where Driftwood's west shore runs (harbour x): the open sea lies west of it, past
    the valley's edge, and the land rises from it in rocks."""
    return int(min(y / 2, 7) + smooth_noise(0, y, 17, 941) * 7 + (smooth_noise(1, y, 5, 942) - 0.5) * 2)


def shore_rocks(cv: Canvas, line, seed: int = 0, step: int = 11) -> set:
    """Boulders along a rocky shore, `line` being (x, y) points on the waterline: big
    ones and small ones in no order, some in pairs, a gap now and then where the
    shingle shows, the surf working round their feet."""
    pts = set()
    i, k = 0, 0
    while i < len(line):
        x, y = line[i]
        n = noise2(k, 0, seed)
        big = n > 0.78
        w = (16 + int(noise2(k, 1, seed) * 8)) if big else (7 + int(noise2(k, 1, seed) * 8))
        h = (10 + int(noise2(k, 2, seed) * 4)) if big else (5 + int(noise2(k, 2, seed) * 4))
        if noise2(k, 3, seed) > 0.12:
            pts |= boulder(cv, x + w // 2 - 3 + int(noise2(k, 4, seed) * 6), y + h // 2, w, h, seed + k,
                           moss=noise2(k, 5, seed) > 0.55)
        if noise2(k, 6, seed) > 0.7:  # a small one beside it, further up the shore
            pts |= boulder(cv, x + w + 2, y + 3, 6 + int(noise2(k, 7, seed) * 4), 4 + int(noise2(k, 8, seed) * 3), seed + k + 99, moss=False)
        i += max(5, int(h * 0.9 + noise2(k, 9, seed) * 6))
        k += 1
    return pts


def coast_top(gx: int) -> int:
    """Where the sea cliffs' turf lip runs, in the valley's x (harbour 0-319, headland
    320-639): low at Driftwood's east shore, swinging south round the Headland, and
    turning down out through the Headland's bottom edge near its east side."""
    x = gx - 320
    n = (smooth_noise(gx, 0, 9, 951) - 0.5) * 8 + (smooth_noise(gx, 3, 31, 952) - 0.5) * 10
    if x < 0:
        return 300 + int(n * 0.4)
    if x < 120:
        u = x / 120
        return int(300 + 172 * u * u * (3 - 2 * u) + n * (0.4 + u))
    if x < 250:
        return int(472 + math.sin(x / 23) * 8 + n)
    return int(472 + (x - 250) * 1.9 + n)


def coast_height(gx: int) -> int:
    return 22 + int(smooth_noise(gx, 1, 18, 953) * 14)


BREAKWATER = [(172, 470), (200, 458), (236, 440), (262, 416), (282, 392)]


@functools.lru_cache(maxsize=1)
def _coast_cells():
    """How far the sea off Driftwood and the Headland lies from land, on a 4 px grid in
    the valley's x (0-639), measured from one outline of both zones' shores, so the
    water deepens the same way on both sides of their border."""
    from collections import deque
    C = 4
    cw, ch = 640 // C, H // C
    land = set()
    for gx in range(0, 640, 2):  # the cliffs' feet, and the land above them
        if gx >= 292:
            foot = coast_top(gx) + coast_height(gx)
            for y in range(0, min(H, foot), C):
                land.add((gx // C, y // C))
    for y in range(0, H, 2):
        bx = int(100 - (y - 296) * 0.26 - math.sin((y - 296) / 70) * 12) if y >= 296 else 100
        for x in range(0, bx, C):
            land.add((x // C, y // C))
    for x in range(0, 292, C):  # the quay and the village above it
        for y in range(0, 306, C):
            land.add((x // C, y // C))
    for (x, y) in blob(16, 540, 62, 74, seed=972, rough=0.14):  # the west point
        if x >= 0 and y < H:
            land.add((x // C, y // C))
    for (ax, ay), (bx, by) in zip(BREAKWATER, BREAKWATER[1:]):  # the breakwater and its root
        for k in range(12):
            land.add((int(ax + (bx - ax) * k / 12) // C, int(ay + (by - ay) * k / 12) // C))
    for (x, y) in blob(294, 366, 22, 28, seed=0, rough=0.0):
        land.add((x // C, y // C))
    dist, q = {}, deque()
    for c in land:
        dist[c] = 0
        q.append(c)
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if 0 <= n[0] < cw and 0 <= n[1] < ch and n not in dist:
                dist[n] = dist[(cx, cy)] + 1
                q.append(n)
    return dist


class coast_depth:
    """Depth for one zone's sea, read from the shared outline (zone x + ox)."""
    def __init__(self, ox: int):
        self.ox = ox
        self.cells = _coast_cells()

    def __call__(self, x, y):
        gx = x + self.ox
        a = self.cells.get((gx // 4, y // 4), 0)
        b = self.cells.get(((gx + 3) // 4, (y + 3) // 4), a)
        return (a + b) * 2


def jetty(cv: Canvas, x0: int, w: int, y0: int, y1: int, water: set, ladder: bool = True) -> set:
    """A timber jetty out over the water: weathered planks laid across, a lit stringer
    along its west side and a shaded one along its east, piles under its sides and its
    end standing in rings of ripples, its shadow on the water, and a ladder down into
    the water at its end. Returns the deck (walkable)."""
    BL = MATERIALS['bleached']
    deck = {(x, y) for x in range(x0, x0 + w) for y in range(y0, y1)}
    for (x, y) in deck:
        r = (y - y0) % 3
        pk = (y - y0) // 3
        t = 4 + (1 if noise2(pk, x0, 961) > 0.82 else -1 if noise2(pk, x0, 961) < 0.18 else 0)
        c = detail.tone(BL, t + 1) if r == 0 else detail.tone(BL, t) if r == 1 else BL[1]
        if r == 1 and noise2(x // 4, pk, 962) < 0.15:
            c = detail.tone(BL, t - 1)
        if x == x0:
            c = BL[5] if r != 2 else BL[3]
        elif x == x0 + w - 1:
            c = BL[2] if r != 2 else BL[0]
        if r == 1 and x in (x0 + 2, x0 + w - 3):
            c = STONE[1]  # nails over the stringers
        cv.set(x, y, c)
    for y in range(y0 + 8, y1, 14):  # piles along each side, seen past the deck's edge
        for (px, dx) in ((x0 - 1, -1), (x0 + w, 1)):
            cv.vline(px, y, 5, WOOD[2] if dx < 0 else WOOD[1])
            cv.set(px, y + 5, WTR[4]); cv.set(px + dx, y + 5, WTR[3])
    for x in range(x0, x0 + w):  # the end: a beam, and piles going down into the water
        cv.set(x, y1, BL[1]); cv.set(x, y1 + 1, WOOD[1] if x in (x0, x0 + 1, x0 + w - 2, x0 + w - 1) else WTR[0])
        cv.set(x, y1 + 2, WOOD[0] if x in (x0, x0 + 1, x0 + w - 2, x0 + w - 1) else WTR[1])
    for (px) in (x0, x0 + w - 2):
        cv.hline(px - 1, y1 + 3, 4, WTR[4])
    if ladder:
        lx = x0 + w // 2 - 2
        for k in range(1, 8):
            cv.set(lx, y1 + k, WOOD[3]); cv.set(lx + 4, y1 + k, WOOD[2])
            if k % 2 == 0:
                cv.hline(lx + 1, y1 + k, 3, WOOD[2])
        cv.hline(lx - 1, y1 + 8, 7, WTR[3])
    for y in range(y0, y1 + 3):  # the deck's shadow on the water, down and right
        for x in range(x0 + w + 1, x0 + w + 4):
            if (x, y) in water and (x, y) not in deck:
                style.darken(cv, x, y)
    return deck


def breakwater(cv: Canvas, pts, seed: int = 0) -> set:
    """A curving rubble breakwater: a capped wall of big dressed blocks, its walkway top
    lit and jointed, its seaward face in courses, a round head, and a fringe of rough
    armour boulders along its foot on the sea side. Returns everything it covers."""
    cover = set()
    line = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)))
        for k in range(n):
            line.append((ax + (bx - ax) * k / n, ay + (by - ay) * k / n))
    cy = {}
    for (x, y) in line:
        cy.setdefault(int(x), y)
    xs = sorted(cy)
    # armour boulders first along the seaward foot (behind the cap when drawn after)
    for i, x in enumerate(xs[::9]):
        y = cy[x]
        cover |= boulder(cv, x + 4 + int(noise2(i, 0, seed) * 4), y + 18 + int(noise2(i, 1, seed) * 3),
                         12 + int(noise2(i, 2, seed) * 8), 9 + int(noise2(i, 3, seed) * 4), seed + i, moss=False)
    for x in xs:
        y = int(cy[x])
        for yy in range(y - 4, y + 4):  # the cap's top: big slabs, jointed
            j = (x + (0 if ((yy - y + 4) // 4) % 2 else 6)) % 12
            c = STONE[4] if yy == y - 4 else STONE[3] if j else STONE[1]
            if (yy - y + 4) % 4 == 3 and j:
                c = STONE[2]
            cv.set(x, yy, c)
            cover.add((x, yy))
        for k in range(8):  # the seaward face in courses
            yy = y + 4 + k
            c = STONE[2] if (x + (k // 4) * 5) % 10 else STONE[0]
            if k % 4 == 3:
                c = STONE[0]
            if k >= 6:
                c = STONE[1] if k == 6 else '#2E4A3A'
            cv.set(x, yy, c)
            cover.add((x, yy))
        cv.set(x, y - 5, STONE[1])  # the lip on the harbour side, lapped by the water
        cover.add((x, y - 5))
    hx, hy = xs[0], cy[xs[0]]  # the head: a round drum
    head = blob(hx, hy, 11, 8, seed=seed + 50, rough=0.04)
    for (x, y) in head:
        cv.set(x, y, STONE[4] if (x - hx) + (y - hy) < -6 else STONE[3] if (x - hx) < 4 else STONE[2])
    for x in range(int(hx) - 11, int(hx) + 12):
        bot = max((yy for (xx, yy) in head if xx == x), default=None)
        if bot is None:
            continue
        for k in range(1, 9):
            cv.set(x, bot + k, STONE[2] if k < 4 else STONE[1] if k < 7 else '#2E4A3A')
            cover.add((x, bot + k))
    cover |= head
    return cover


def harbour(frame: int = 0):
    """Driftwood Harbour: the road from Crossroads Town comes down between whitewashed
    cottages to a stone quay and the fish market. Two timber jetties run out from the
    quay with boats moored at their ends and ladders down to the water; a curving
    breakwater of big blocks reaches out from the eastern rocks to shelter the basin;
    across the mouth, the lighthouse stands on the rocks of the west point, where the
    beach of drying nets and rock pools ends. The cliff path climbs away east to the
    Headland. Past the breakwater the sea opens to the south."""
    BLEACHED = MATERIALS['bleached']
    cv = Canvas(W, H)
    ground.valley(cv, 'harbour', frame)  # one turf across the valley (ground.py)
    QX0, QX1, QY0, QY1 = 96, 272, 226, 296  # the quay's paved top
    # the shore: the beach's waterline curves from the slipway to the west point; past
    # the quay the eastern rocks rise to the sea cliffs that run on round the Headland
    def beach_x(y):
        return int(100 - (y - 296) * 0.26 - math.sin((y - 296) / 70) * 12 + (smooth_noise(0, y, 12, 971) - 0.5) * 6)
    point = {(x, y) for (x, y) in blob(16, 540, 62, 74, seed=972, rough=0.14) if x >= west_shore(y) + 2 and y < H + 8}
    sand_top = {x: 214 + int((smooth_noise(x, 0, 16, 973) - 0.5) * 14) for x in range(W)}
    beach = {(x, y) for y in range(200, H) for x in range(west_shore(y) + 2, QX0 + 8) if y >= sand_top[x] and (y < 296 or x <= beach_x(y))} - point
    cliff_t = {x: coast_top(x) for x in range(304, W)}
    cliff_h = {x: coast_height(x) for x in range(304, W)}
    river, rdeep, _rl = river_in('harbour')  # the valley's river, coming out into the basin
    water = {(x, y) for y in range(H) for x in range(0, west_shore(y))}  # the open sea off the west shore
    for y in range(QY1 + 9, H):
        for x in range(W):
            if (x, y) in beach or (x, y) in point:
                continue
            if x >= 304 and y < cliff_t[x] + cliff_h[x]:
                continue
            water.add((x, y))
    estuary = set(river) - water
    # the sand: dry and pale up the beach, darker and wet at the waterline, ripples
    for (x, y) in beach:
        n = smooth_noise(x, y, 7, 974)
        c = SAND_R[2] if n > 0.42 else SAND_R[1]
        wet = any((x + d, y) in water for d in (1, 2, 3, 4)) or any((x + d, y + 3) in water for d in (1, 3))
        if wet:
            c = SAND_R[0] if (x + y) % 3 else SAND_R[1]
        elif y > 300 and (y + int(math.sin(x / 6) * 2)) % 7 == 0 and n < 0.6:
            c = SAND_R[1]  # the ripples the tide left
        cv.set(x, y, c)
    for (x, y) in beach:  # the turf's edge onto the sand: dune grass in tufts
        if y == sand_top[x]:
            cv.set(x, y - 1, G[1])
            if noise2(x, y, 975) > 0.5:
                detail.grass_tuft(cv, x, y + 1, int(noise2(x, 0, 976) * 6), G, 2)
        elif noise2(x // 3, y // 3, 977) > 0.985:
            cv.set(x, y, '#F2EEE2'); cv.set(x + 1, y, SAND_R[0])  # a shell
    # rock pools left by the tide, each a ring of stones round still water
    pools = set()
    for (px, py, rx, ry, sd) in ((34, 330, 11, 5, 1), (58, 402, 8, 4, 2), (32, 438, 9, 4, 3)):
        pool = blob(px, py, rx, ry, seed=978 + sd, rough=0.25)
        for (x, y) in pool:
            cv.set(x, y, WTR[0] if (x, y - 1) not in pool else WTR[2] if (x + y) % 5 else WTR[3])
        for (x, y) in edge_of(pool):
            if (x, y - 1) not in pool:
                cv.set(x, y, WTR[0])
        for k, (x, y) in enumerate(sorted(edge_of(blob(px, py, rx + 2, ry + 2, seed=978 + sd, rough=0.25)))):
            if k % 3 == 0:
                detail.pebble(cv, x, y, STONE, big=k % 2 == 0)
        pools |= pool
    # the sea: calm inside the breakwater, surf on the beach and under the cliffs
    calm = {(x, y) for (x, y) in water if y < 440 - max(0, 120 - x) and x > 80}
    sea(cv, water, seed=979, calm=calm, depth=coast_depth(0), open_edges='ws')
    bank(cv, estuary, keep=water, seed=976)
    water_body(cv, estuary, set(rdeep) & estuary, seed=977, glints=12)
    water |= estuary
    west_rocks = shore_rocks(cv, [(west_shore(y), y) for y in range(-4, H, 1) if not (470 < y)], seed=943)
    # the quay: dressed stone with a lit kerb and a front face in courses down to the
    # water, a slipway down onto the beach at its west end, the eastern rocks at its east
    quay = {(x, y) for x in range(QX0, QX1) for y in range(QY0, QY1)}
    worlds.paint_paving(cv, quay, seed=9)
    cv.hline(QX0, QY1 - 1, QX1 - QX0, STONE[4])
    detail.stones(cv, QX0, QY1, QX1 - QX0, 8, STONE, seed=980, course=4, base=2)
    cv.hline(QX0, QY1 + 8, QX1 - QX0, '#2E4A3A')
    for x in range(QX0, QX1):  # weed and wet at the waterline
        if (x + 1) % 3:
            cv.set(x, QY1 + 7, STONE[1])
    for y in range(QY0 + 2, QY1 + 9):  # the quay's west end: a stone slipway down onto the sand
        for k in range(10):
            x = QX0 - 10 + k
            c = STONE[4] if (y - QY0) % 6 == 0 else STONE[3] if k < 7 else STONE[2]
            if k == 0:
                c = STONE[2]
            cv.set(x, y, c)
    for y in range(QY0 + 2, QY1 + 9):
        cv.set(QX0 - 1, y, STONE[1])
    for x in range(QX0, QX1):  # the kerb along the back
        cv.set(x, QY0, STONE[1]); cv.set(x, QY0 + 1, STONE[4])
    # the eastern rocks: boulders heaped from the quay's end up to the cliffs
    rocks = outcrop(cv, [(274, 310, 12, 9), (268, 322, 10, 7), (312, 300, 16, 12), (306, 318, 12, 9)], seed=981, moss=True)
    face = cliff(cv, cliff_t, cliff_h, seed=982)
    # the breakwater reaches out from the cliff's foot round the basin
    spur = outcrop(cv, [(298, 352, 26, 22), (288, 372, 22, 16), (306, 340, 14, 14), (276, 388, 16, 12),
                        (300, 384, 18, 12)], seed=988, moss=True)  # rocks fallen from the cliff: the breakwater's root
    bw = breakwater(cv, BREAKWATER, seed=983)
    # the west point: a rocky knoll with pines on it, the lighthouse on its tip
    for (x, y) in point:
        n = smooth_noise(x, y, 9, 984)
        cv.set(x, y, G[2] if n > 0.45 else G[1])
    knoll = outcrop(cv, [(50, 530, 46, 20), (52, 488, 30, 20), (64, 512, 26, 22), (48, 540, 34, 24), (70, 560, 28, 20),
                         (30, 474, 22, 14), (40, 572, 30, 16), (8, 478, 18, 12)], seed=985, moss=True)
    for (x, y) in point:
        if y < 470 and (x, y) not in knoll and noise2(x, y, 986) > 0.92:
            detail.grass_tuft(cv, x, y, int(noise2(x, y, 987) * 6), G, 2)
    # wooden jetties out over the basin, each ending at a moored boat and a ladder
    decks = set()
    decks |= jetty(cv, 146, 14, QY1 - 2, 392, water)
    decks |= jetty(cv, 232, 14, QY1 - 2, 372, water)
    # the road down from the town, the lanes to the cottages, the cliff path east
    road = worlds.thick([(160, -4), (160, 24)], 18) | worlds.thick([(160, 20), (152, 120), (166, 230)], 14, seed=16)
    road |= worlds.thick([(154, 112), (100, 116), (64, 112)], 8, seed=17)  # to cottage 1's door
    road |= worlds.thick([(160, 186), (116, 212), (84, 230)], 7, seed=18)  # down to cottage 3 and the beach
    road |= worlds.thick([(158, 96), (210, 106), (290, 104), (W + 6, 110)], 8, seed=19)  # past cottage 2: the cliff path
    road |= worlds.thick([(166, 200), (230, 222), (276, 222)], 7, seed=20)  # to cottage 4's door
    paint_road(cv, (road - quay) | {(x, y) for (x, y0) in road if y0 == 0 for y in range(-12, 0)}
               | {(x, y) for (x0, y) in road if x0 == W - 1 for x in range(W, W + 12)})
    objects = [
        ('cottage-1', 'cottage', 24, 30), ('cottage-2', 'cottage_b', 210, 26), ('cottage-3', 'cottage', 44, 150),
        ('cottage-4', 'cottage_b', 236, 140),
        # the washing line in cottage 1's yard, beside the house and clear of the lanes
        ('washing', 'washing_line', 106, 40),
        # the quay: the fish market, pots and the spare anchor by the chandler's corner
        ('market', 'fish_stall', 104, 226), ('pots-1', 'lobster_pots', 196, 236), ('pots-2', 'lobster_pots', 238, 246),
        ('anchor', 'anchor', 248, 228), ('bollard-1', 'bollard', 132, 284), ('bollard-2', 'bollard', 250, 284),
        # the beach: nets drying, boats hauled up, chairs, driftwood
        ('nets-1', 'net_rack', 16, 236), ('nets-2', 'net_rack', 16, 290), ('upturned', 'upturned_boat', 18, 386),
        ('chair-1', 'deck_chair', 30, 344), ('chair-2', 'deck_chair_b', 50, 352), ('drift', 'driftwood', 40, 452),
        # the boats: each at a jetty's end, one on its buoy in the basin, a sail beyond
        ('boat-1', 'boat_blue', 162, 368), ('boat-2', 'boat_red', 248, 348), ('boat-3', 'boat_blue', 186, 412),
        ('buoy-1', 'buoy', 252, 404), ('buoy-2', 'buoy', 112, 440), ('sail', 'sailboat', 238, 506),
        # the lighthouse on the west point's rocks, lighting the harbour mouth
        ('lighthouse', 'lighthouse', 30, 380),
    ]
    quay_face = {(x, y) for x in range(QX0, QX1) for y in range(QY1, QY1 + 9)}
    blocked = (water | face | rocks | spur | bw | knoll | pools | west_rocks | quay_face) - decks
    stands = {'town': (160, 18), 'market': (150, 288), 'jetty': (153, 384), 'beach': (34, 380), 'castle': (300, 116)}
    return cv, objects, stands, blocked


def headland(frame: int = 0):
    """The Headland, east of the harbour (Matt, 18 Oct: the castle moved to the fire
    country): the cliff path from the harbour comes in at the west edge and climbs the
    open down to the lookout tower that watches the sea from the cliff top. Sheep graze
    in a fold walled with dry stone, with a stile where the path passes; hives stand in
    the lee of its wall. The path ends at a flagged viewpoint on the cliff's edge with
    a bench beside it looking out to sea. The cliffs drop away south round the down,
    and turn inland at its east side under the trees."""
    cv = Canvas(W, H)
    ground.valley(cv, 'headland', frame)  # one turf across the valley (ground.py)
    top = {x: coast_top(x + W) for x in range(W)}
    hgt = {x: coast_height(x + W) for x in range(W)}
    sea_px = {(x, y) for x in range(W) for y in range(top[x] + hgt[x], H)}
    sea(cv, sea_px, seed=991, depth=coast_depth(W))
    face = cliff(cv, {x: t for x, t in top.items() if t < H}, {x: min(hgt[x], H - top[x]) for x in range(W) if top[x] < H}, seed=982)
    river, rdeep, _rl = river_in('headland')  # the valley's river, on its way down to Driftwood
    river = set(river) - sea_px - face
    bank(cv, river, seed=1501)
    water_body(cv, river, set(rdeep) & river, seed=1502, glints=30)
    # boulders fallen from the cliff, lying in the surf at its foot
    talus = set()
    for i, gx in enumerate(range(18, 300, 37)):
        by = top[gx] + hgt[gx] + 4 + int(noise2(i, 0, 992) * 6)
        if by < H - 4:
            talus |= boulder(cv, gx + int(noise2(i, 1, 992) * 12), by, 10 + int(noise2(i, 2, 992) * 8), 7 + int(noise2(i, 3, 992) * 4), 993 + i, moss=False)
    # the cliff path from the harbour up the down to the tower, then on to the viewpoint
    path = worlds.thick([(-6, 110), (58, 112)], 8) | worlds.thick(
        [(56, 112), (66, 150), (80, 222), (140, 300), (196, 368), (228, 412), (228, 424)], 8, seed=19)
    path |= worlds.thick([(118, 280), (100, 340), (112, 404), (120, 430)], 6, seed=23)
    path |= worlds.thick([(54, 168), (100, 162), (146, 146)], 5, seed=998)  # a spur from the path to the fold's gate
    paint_road(cv, (path - river) | {(x, y) for (x0, y) in path if x0 == 0 for x in range(-12, 0)})
    bspan = [x for (x, y) in river if y == 110]
    bridge = stone_bridge(cv, 0, max(bspan) + 8, 103, 118, river)  # the cliff path's bridge over the river
    view = blob(122, 440, 20, 9, seed=994, rough=0.1)  # the viewpoint: flags laid on the cliff top
    worlds.paint_paving(cv, view, seed=995)
    for (x, y) in edge_of(view):
        cv.set(x, y, STONE[1] if (x, y + 1) not in view else STONE[4] if (x, y - 1) not in view else STONE[2])
    # the sheep fold: a dry stone wall round a rough field on the down, open at a stile
    fold = blob(214, 122, 84, 56, seed=996, rough=0.12)
    wall = drystone_loop(cv, fold, gap=(136, 146, 8), seed=997)
    objects = [
        ('tower', 'lookout_tower', 198, 300),
        ('sheep-1', 'sheep', 176, 104), ('sheep-2', 'sheep_left', 236, 128), ('sheep-3', 'sheep', 210, 150),
        ('sheep-4', 'sheep_left', 262, 92),
        ('hive-1', 'beehive', 150, 186), ('hive-2', 'beehive', 172, 194),
        ('tree-w', 'tree_small', 70, 196), ('bush-1', 'bush', 270, 230), ('bush-2', 'bush', 66, 262),
        ('bench', 'bench', 146, 418), ('stone-1', 'stone', 278, 400), ('stone-2', 'stone', 60, 380),
        # the down falls to trees on the east, running on into the woods beyond
        ('pine-e1', 'pine', 290, 300), ('tree-e2', 'tree', 286, 380), ('pine-e3', 'pine', 300, 440),
    ]
    blocked = sea_px | face | wall | talus | (river - bridge)
    stands = {'harbour': (14, 112), 'tower': (228, 430), 'bench': (124, 440), 'down': (150, 280), 'fold': (144, 146)}
    return cv, objects, stands, blocked


def drystone_loop(cv: Canvas, field: set, gap=(0, 0), seed: int = 0) -> set:
    """A dry stone wall round a field: rough stones of every size laid in two courses
    with a row of upright coping stones, lit on their tops, dark in the joints, lichen
    here and there, the turf growing up against its foot; `gap` is the stretch of its
    length (in px, from its westmost point, clockwise) left open as a stile."""
    ring = edge_of(field)
    cx = sum(x for x, _ in ring) / len(ring)
    cy = sum(y for _, y in ring) / len(ring)
    order = sorted(ring, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    start = min(range(len(order)), key=lambda i: order[i][0])
    order = order[start:] + order[:start]
    if len(gap) == 3:  # (x, y, half-width): the gap where the wall passes nearest that point
        gi = min(range(len(order)), key=lambda i: math.hypot(order[i][0] - gap[0], order[i][1] - gap[1]))
        line = [p for i, p in enumerate(order) if min(abs(i - gi), len(order) - abs(i - gi)) > gap[2]]
    else:
        line = [p for i, p in enumerate(order) if not (gap[0] <= i < gap[1])]
    top = set()
    for (x, y) in line:
        top |= {(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    wall = set(top)
    for (x, y) in top:  # the wall's lit top: rough stones, two or three across
        st = noise2(x // 3, y // 2, seed)
        c = STONE[4] if st > 0.66 else STONE[3] if st > 0.25 else STONE[2]
        if noise2(x, y, seed + 2) > 0.85:
            c = STONE[1]  # a joint
        cv.set(x, y, c)
    for (x, y) in top:  # its face toward us where it runs across the slope: two courses
        if (x, y + 1) in top:
            continue
        for k in range(1, 5):
            st = (x // 4 + (k // 2) * 2 + int(noise2(x // 4, k // 2, seed) * 2)) % 3
            c = STONE[1] if k == 4 else STONE[0] if st == 0 and k % 2 else STONE[2] if st == 1 else STONE[3] if k == 1 else STONE[2]
            if k in (2, 3) and noise2(x, y + k, seed + 1) > 0.92:
                c = '#B8B47A'  # lichen
            cv.set(x, y + k, c)
            wall.add((x, y + k))
        style.darken(cv, x + 1, y + 5)
        if noise2(x, y, seed + 3) > 0.7:
            detail.grass_tuft(cv, x, y + 6, int(noise2(x, 1, seed) * 6), G, 2)
    return wall


def riverside(frame: int = 0):
    """The Riverside, east of the garden: the garden's stream comes in at the west edge
    exactly where it leaves the garden (same line, width and bluff) and widens into a
    slow river. It runs east past the watermill, whose wheel turns in a stone race off
    the north bank with a towpath along the mill's front, then swings south through the
    lower meadow toward the park. Stepping stones cross where it is still narrow; willows
    lean over its west bank, where a path ends at a fishing platform; reeds and lilies
    fill its slack water. Sheep graze in a walled fold on the north meadow by the hives,
    and old trees close in on the east under the forest."""
    cv = Canvas(W, H)
    ground.valley(cv, 'riverside', frame)  # one turf across the valley (ground.py)
    river, deep, line = river_in('riverside')
    river, deep = set(river), set(deep)
    top = {}
    for (x, y) in river:
        if y < 360:
            top[x] = min(top.get(x, 999), y)
    # the north bank's bluff, as in the garden, sinking into the meadow as the river
    # turns away south
    bluff = set()
    for x in range(0, 240):
        if x not in top:
            continue
        h = int((7 + int(smooth_noise(x + 320, 3, 9, 92) * 3)) * min(1.0, max(0.0, (240 - x) / 80)))
        col = (x + 320 + int(noise2((x + 320) // 6, 1, 95) * 6)) % 6
        si = (x + 320 + int(noise2((x + 320) // 6, 1, 95) * 6)) // 6
        for k in range(h):
            y = top[x] - h + k
            bluff.add((x, y))
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
    bank(cv, river, keep=bluff, seed=1402)
    water_body(cv, river, deep, seed=1403, glints=90)
    # the stepping stones where it is still narrow, steps cut down the bluff to them
    sx0 = 46
    ys = sorted(y for (x, y) in river if x == sx0)
    for k, sy in enumerate(range(ys[0] + 2, ys[-1], 6)):
        sx = sx0 - 2 + (3 if k % 2 else -2)
        for (x, y) in blob(sx, sy, 4, 2.5, seed=1404 + k, rough=0.15):
            cv.set(x, y, STONE[4] if (x - sx) + (y - sy) < -1 else STONE[3] if (x - sx) + (y - sy) < 2 else STONE[2])
        cv.hline(sx - 4, sy + 3, 9, WTR[4])
    stones = {(x, y) for x in range(38, 54) for y in range(ys[0] - 2, ys[-1] + 3)}
    steps = {(x, y) for (x, y) in bluff if 38 <= x < 54}
    for (x, y) in steps:
        cv.set(x, y, STONE[4] if (y - top[x]) % 3 == 0 else STONE[2] if x < 52 else STONE[1])
    stones |= steps
    # the mill on the north bank: its race off the river to the wheel, and a towpath of
    # flags along its front, where its door opens, joining the lane from the garden
    mx = 218
    mt = top.get(mx, 300)
    race = {(x, y) for x in range(mx - 6, mx + 16) for y in range(mt - 34, mt + 2)}
    for (x, y) in race:
        c = WTR[2] if mx - 4 <= x < mx + 14 else STONE[3] if x < mx - 4 else STONE[1]
        if mx - 4 <= x < mx + 14 and (y + x // 3) % 5 == 0:
            c = WTR[3]
        cv.set(x, y, c)
    towpath = {(x, y) for x in range(118, mx - 6) for y in range(mt - 20, mt - 6)}
    path = worlds.thick([(22, 224), (70, 230), (118, mt - 11)], 8, seed=21)  # the lane to the mill (the garden has no path at this edge)
    deck_x = min(x for (x, y) in river if y == 432) - 6
    path |= worlds.thick([(8, 402), (60, 398), (110, 418), (200, 430), (deck_x + 2, 432)], 8, seed=22)  # the west bank walk
    paint_road(cv, {(x, y) for (x, y) in path if (x, y) not in river and (x, y) not in bluff})
    worlds.paint_paving(cv, towpath, seed=1405)
    for x in range(118, mx - 6):
        cv.set(x, mt - 6, STONE[1]); cv.set(x, mt - 5, STONE[0])  # its kerb above the water
    # the fishing platform at the end of the bank walk, out over the slack water
    deck = dipping_deck(cv, deck_x, 424, 18, 12, river)
    for (rx, ry, n) in ((deck_x - 18, 460, 6), (300, 330, 5), (250, 520, 7), (120, 310, 5), (180, 318, 4)):
        if (rx, ry) in river or any((rx + d, ry) in river for d in (-3, 3)):
            reeds(cv, rx, ry, seed=rx, n=n)
    for i in range(160):  # wildflowers on the north meadow, thickest by the hives
        x, y = 14 + int(noise2(i, 0, 530) * 120), 30 + int(noise2(i, 1, 530) * 110)
        col = ('#F2D27A', '#E8A0BC', '#FFFFFF', '#B8A0E8')[i % 4]
        cv.set(x, y, col); cv.set(x, y + 1, '#447A50')
    fold = blob(206, 104, 64, 50, seed=1201, rough=0.12)
    for (x, y) in fold:  # the pasture grazed short
        n = smooth_noise(x, y, 6, 1202)
        if n > 0.62 or (n > 0.55 and (x // 2 + y // 2) % 2):
            cv.set(x, y, G[3])  # grazed short in patches, the sheep's favourite spots
    fold_wall = drystone_loop(cv, fold, gap=(170, 156, 7), seed=1203)  # its gate faces the mill lane
    lc = [(x, y) for (x, y, h) in line]
    objects = [
        ('mill', 'water_mill', 140, mt - 104), ('willow-1', 'willow', 176, 300), ('willow-2', 'willow', 96, 470),
        ('heron', 'heron', 262, 300), ('lilies-1', 'lily_pads', 230, 470), ('lilies-2', 'lily_pads', 120, 300),
        ('tree-1', 'tree', 10, 120), ('tree-2', 'tree_small', 266, 100), ('bush-1', 'bush', 40, 500),
        ('bench', 'bench', 196, 446), ('sack-1', 'sack', 124, mt - 30), ('barrel-m', 'barrel', 104, mt - 34),
        # old trees on the east bank, running on into the forest beyond
        ('tree-e1', 'tree', 276, 400), ('pine-e2', 'pine', 290, 470), ('tree-e3', 'tree_autumn', 280, 230),
        ('bush-e4', 'bush', 288, 540),
        ('sheep-1', 'sheep', 166, 72), ('sheep-2', 'sheep_left', 226, 92), ('sheep-3', 'sheep', 190, 118),
        ('sheep-4', 'sheep_left', 244, 60), ('hive-1', 'beehive', 40, 40), ('hive-2', 'beehive', 66, 46),
    ]
    blocked = ((river | bluff | race) - stones - deck - towpath) | fold_wall
    stands = {'garden-north': (8, 222), 'garden-south': (8, 402), 'mill': (190, mt - 14), 'stones': (46, (ys[0] + ys[-1]) // 2),
              'willows': (120, 426), 'platform': (deck_x + 8, 430)}
    return cv, objects, stands, blocked


def dipping_deck(cv: Canvas, x0: int, y0: int, w: int, h: int, water: set) -> set:
    """A small timber platform built out over the edge of a pond, where a path ends:
    planks laid east-west, a lit front edge and two posts into the water, its shadow on
    the water. Returns its pixels (walkable)."""
    BL = MATERIALS['bleached']
    deck = {(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)}
    for (x, y) in deck:
        r = (y - y0) % 3
        c = BL[4] if r == 0 else BL[3] if r == 1 else BL[1]
        if x == x0 + w - 1:
            c = BL[2]
        cv.set(x, y, c)
    for x in range(x0, x0 + w):
        cv.set(x, y0 + h, BL[1]); cv.set(x, y0 + h + 1, WOOD[0] if x in (x0 + 1, x0 + w - 2) else WTR[0])
    for (px) in (x0 + 1, x0 + w - 2):
        cv.set(px, y0 + h + 2, WOOD[0]); cv.hline(px - 1, y0 + h + 3, 3, WTR[4])
    for y in range(y0, y0 + h + 2):
        for x in range(x0 + w, x0 + w + 3):
            if (x, y) in water:
                style.darken(cv, x, y)
    return deck


def park(frame: int = 0):
    """The Town Park, east of Crossroads Town: the river comes down from the riverside
    along the park's west side, and the town's street crosses it on a stone bridge into
    the park, then runs on to the fountain plaza, where benches look onto the fountain
    and the ice cream cart stands at its edge. North of the plaza a ring of paths goes
    round the bandstand; south, a path goes down through the lawns to a timber platform
    on the river bank, with a willow leaning over the water and ducks on it. Trees
    gather in clumps, thickest on the east toward the old forest."""
    cv = Canvas(W, H)
    ground.valley(cv, 'park', frame)  # one turf across the valley (ground.py)
    river, deep, line = river_in('park')
    river, deep = set(river), set(deep)
    PX, PY = 200, 322  # the fountain plaza

    def on(y):  # the river's middle at row y (for things that float on it)
        return int(river_at('park', y))
    RX, RY = 222, 150  # the bandstand's ring
    paths = worlds.thick([(-8, 300), (100, 300)], 13)  # the town's street, unchanged, over the bridge
    paths |= worlds.thick([(96, 300), (PX - 30, 304)], 11, seed=27)
    paths |= {(x, y) for (x, y) in oval(RX, RY, 76, 46)} - {(x, y) for (x, y) in oval(RX, RY, 60, 33)}
    paths |= worlds.thick([(PX, PY - 20), (RX - 4, RY + 50)], 9, seed=29)  # plaza to the ring
    paths |= {(x, y) for (x, y) in oval(PX, PY, 44, 26)}
    deck_y = 436
    dx = max(x for (x, y) in river if y == deck_y + 6) - 4
    paths |= worlds.thick([(PX - 20, PY + 22), (150, 400), (dx + 20, deck_y + 6)], 8, seed=28)  # down to the river
    bridge_rows = range(290, 312)
    bx0 = min(x for (x, y) in river if y in bridge_rows) - 6
    bx1 = max(x for (x, y) in river if y in bridge_rows) + 7
    paths -= river
    worlds.paint_paving(cv, paths | {(x, y) for (x0, y) in paths if x0 == 0 for x in range(-12, 0)}, seed=11)
    ring = bank(cv, river, seed=1101)
    water_body(cv, river, deep, seed=1104, glints=60)
    for (x, y) in sorted(ring):
        if (x, y - 1) in river and noise2(x, y, 1105) > 0.9:
            detail.pebble(cv, x, y, STONE)
    bridge = stone_bridge(cv, bx0, bx1, 291, 310, river)
    deck = dipping_deck(cv, dx, deck_y, 18, 12, river)
    for (rx, ry, n) in ((70, 520, 6), (128, 60, 5), (40, 470, 5), (100, 180, 4)):
        reeds(cv, rx, ry, seed=rx, n=n)
    for fb in ((bx1 + 4, 268, 40, 16, 1), (bx1 + 4, 316, 40, 16, 2)):  # flanking the street at the bridge
        meadow.flower_planter(cv, *fb)
    objects = [
        ('bandstand', 'bandstand', RX - 39, RY - 50), ('fountain', 'fountain', PX - 27, PY - 32),
        # the willow on the east bank, leaning out over the water; ducks and lilies on it
        ('willow', 'willow', 70, 466), ('lilies', 'lily_pads', on(400) - 14, 400), ('lilies-2', 'lily_pads', on(128) - 12, 120),
        ('duck-1', 'duck', on(446) - 6, 440), ('duck-2', 'duck', on(358) - 8, 352), ('heron', 'heron', on(520) + 10, 494),
        # trees in clumps round the lawns, thickest on the east
        ('tree-1', 'tree', 230, 10), ('tree-1b', 'tree_small', 196, 24), ('tree-2', 'tree_autumn', 276, 200),
        ('tree-3', 'tree', 4, 110), ('tree-4', 'tree_small', 280, 420), ('tree-5', 'tree', 264, 470),
        ('tree-6', 'tree_small', 200, 480), ('tree-7', 'pine', 290, 300), ('tree-8', 'tree', 176, 470),
        # benches looking onto the fountain and the river
        ('bench-1', 'bench', PX - 52, PY - 66), ('bench-2', 'bench', PX + 20, PY - 66), ('bench-3', 'bench', 120, 450),
        ('lamp-1', 'lamp', bx1 + 2, 250), ('lamp-2', 'lamp', PX + 48, 290), ('lamp-3', 'lamp', 160, 380),
        ('icecream', 'ice_cream_cart', PX + 44, PY - 6), ('bush-1', 'bush', 160, 100), ('bush-2', 'bush', 292, 90),
        ('bush-3', 'bush', 230, 540), ('bush-4', 'bush', 284, 548),
    ]
    stands = {'town': (8, 300), 'bandstand': (RX, RY + 56), 'fountain': (PX, PY + 34), 'pond': (dx + 8, deck_y + 6)}
    return cv, objects, stands, (river - bridge - deck)


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
    # the terrace's face: stacked blocks with lit ledges and snow on them, not bands
    snow_lip = [SNOWm[0], SNOWm[0], SNOWm[1], SNOWm[2], SNOWm[3]]
    cliff(cv, {x: rim(x) + 1 for x in range(W)}, {x: FACE_H - 1 for x in range(W)}, seed=446, lip=snow_lip)
    for x in range(W):  # snow lying on the ledges
        for k in range(2, FACE_H - 4):
            y = rim(x) + 1 + k
            if cv.get(x, y)[:3] == _rgb(STONEm[4]) and noise2(x // 2, y, 448) > 0.45:
                cv.set(x, y, SNOWm[3] if (x + y) % 3 else SNOWm[2])
    # the alpine tarn below the face, open water (no snow lies down here)
    WTR = MATERIALS['water']
    tarn = blob(232, 404, 38, 15, seed=1301, rough=0.18)
    for (x, y) in tarn:
        d = math.hypot((x - 232) / 38, (y - 404) / 15)
        c = WTR[1] if d < 0.6 else WTR[2]
        if (x, y - 1) not in tarn or (x, y - 2) not in tarn:
            c = STONEm[1]
        cv.set(x, y, c)
    for (x, y) in blob(232, 405, 43, 19, seed=1301, rough=0.18):
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
    # the bottom: the forest floor in the shade of the two clumps of pines either side of
    # the trail, darkest under their crowns, with a ragged edge, deepening toward the
    # garden's treeline below (no ruled band)
    clumps = [(36, H - 46, 64, 52), (100, H - 34, 34, 30), (272, H - 50, 64, 56), (300, H - 120, 34, 40), (16, H - 120, 34, 36)]
    for y in range(H - 200, H):
        for x in range(W):
            if (x, y) in trail:
                continue
            sh = max(1 - math.hypot((x - cx) / rx, (y - cy) / ry) for (cx, cy, rx, ry) in clumps)
            sh += (smooth_noise(x, y, 8, 449) - 0.5) * 0.5 + max(0, (y - (H - 26)) / 26) * 0.6
            if sh > 0.12:
                style.darken(cv, x, y)
            if sh > 0.55:
                style.darken(cv, x, y, (0.78, 0.8, 0.84))
    for (x, y) in trail:  # the trail under the trees in dappled shade
        if y > H - 60 and smooth_noise(x, y, 5, 450) > 0.55:
            style.darken(cv, x, y, (0.85, 0.86, 0.9))
    # the trodden path in the snow: a darker worn centre and footprints along it
    tc = {}
    for (x, y) in on_terrace:
        tc.setdefault(y, []).append(x)
    for (x, y) in on_terrace:
        xs = tc[y]
        mid = (min(xs) + max(xs)) / 2
        d = abs(x - mid) / max(1, (max(xs) - min(xs)) / 2)
        c = SNOWm[0] if d < 0.35 and (x + y) % 3 else SNOWm[1] if d < 0.75 else SNOWm[2]
        cv.set(x, y, c)
    for y, xs in tc.items():
        if y % 6 == 0:
            mid = (min(xs) + max(xs)) // 2 + (1 if (y // 6) % 2 else -2)
            cv.set(mid, y, '#7E8FA6'); cv.set(mid + 1, y, '#7E8FA6')
    # the steps cut into the face: treads lit, risers in shade, a cheek wall each side
    steps = set()
    for (x, y) in trail:
        if rim(x) <= y < rim(x) + FACE_H + 1:
            steps.add((x, y))
    sx = {}
    for (x, y) in steps:
        sx.setdefault(y, []).append(x)
    for (x, y) in steps:
        k = (y - rim(x)) % 5
        c = STONEm[4] if k == 0 else STONEm[3] if k == 1 else STONEm[2] if k == 2 else STONEm[1]
        if k == 4:
            c = STONEm[0]
        if noise2(x // 3, y // 5, 451) > 0.85 and k in (0, 1):
            c = SNOWm[2]  # snow drifted onto a tread
        cv.set(x, y, c)
    for y, xs in sx.items():
        for (cxw, lit) in ((min(xs) - 1, True), (min(xs) - 2, True), (max(xs) + 1, False), (max(xs) + 2, False)):
            cv.set(cxw, y, STONEm[3] if lit else STONEm[1])
        cv.set(min(xs) - 3, y, STONEm[0]); cv.set(max(xs) + 3, y, STONEm[0])
    objects = [
        # two clumps of pines either side of the trail, running down into the garden's treeline
        ('pine-b1', 'pine', 0, H - 96), ('pine-b2', 'pine', 34, H - 82), ('pine-b3', 'pine', 70, H - 112),
        ('pine-b7', 'pine', 18, H - 140), ('pine-b4', 'pine', 238, H - 88), ('pine-b5', 'pine', 270, H - 108),
        ('pine-b6', 'pine', 290, H - 150), ('pine-b8', 'pine', 252, H - 160),
        ('pine-m1', 'pine', 14, 392), ('pine-m2', 'pine', 270, 440), ('pine-m3', 'pine', 270, 250),
        ('pine-m4', 'pine', 60, 250), ('cairn-1', 'cairn', 100, 360),
        ('cairn-2', 'cairn', 176, 250), ('boulder-1', 'boulder', 20, 430), ('stone-1', 'stone', 280, 470),
        ('cabin', 'cabin', 150, 80), ('campfire', 'campfire', 110, 176), ('pine-t1', 'snowy_pine', 10, 120),
        ('pine-t2', 'snowy_pine', 270, 120), ('pine-t3', 'snowy_pine', 40, 150),
        ('woodpile', 'woodpile', 122, 138), ('sled', 'sled', 214, 190), ('snowman', 'snowman', 90, 96),
        ('marmot', 'marmot_rock', 220, 470),
        ('cotton-1', 'cotton_grass', 196, 380), ('cotton-2', 'cotton_grass', 270, 398), ('cotton-3', 'cotton_grass', 210, 418),
    ]
    face = {(x, y) for x in range(W) for y in range(rim(x), rim(x) + FACE_H)}
    stands = {'garden': (206, H - 8), 'tarn': (186, 424), 'cabin': (200, 176), 'campfire': (146, 204),
              'saddle': (204, 6), 'hollow': (4, 348)}
    return cv, objects, stands, (face - steps) | shoulder | tarn


def shore_distance(water: set, cap: int = 90) -> dict:
    """How far each water pixel lies from the nearest land, in px (up to `cap`)."""
    from collections import deque
    dist, q = {}, deque()
    for (x, y) in water:
        if any((x + dx, y + dy) not in water and 0 <= x + dx < W and 0 <= y + dy < H
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            dist[(x, y)] = 0
            q.append((x, y))
    while q:
        x, y = q.popleft()
        d = dist[(x, y)]
        if d >= cap:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in water and n not in dist:
                dist[n] = d + 1
                q.append(n)
    return dist


def sea(cv: Canvas, water: set, seed: int = 0, calm=frozenset(), surf: bool = True, depth=None, open_edges=''):
    """The sea: pale over the sand in the shallows, deepening in broad soft-edged
    bands away from land to the open sea's deep blue with long swells (the same water
    as beyond-sea, so it runs on past the valley); a broken line of foam where it
    meets the shore and a second line of surf coming in. `calm` water (inside the
    harbour) has no surf, only a dark lap at the wall."""
    dist = shore_distance(water)
    ox = depth.ox if depth else 0
    for (x, y) in water:
        gx = x + ox
        d = (depth(x, y) if depth else dist.get((x, y), 90)) + (smooth_noise(gx, y, 26, 979) - 0.5) * 22
        if (x, y) in calm:
            d = min(d, 36)
        # where the world's sea runs on past the zone's edge (beyond-sea), the water at
        # the edge is the open sea's, so the two meet without a seam
        e = min([x for c in 'w' if c in open_edges] + [W - 1 - x for c in 'e' if c in open_edges]
                + [H - 1 - y for c in 's' if c in open_edges] + [999])
        d = max(d, 76 - e * 2.2)
        chk = (x // 2 + y // 2) % 2
        if d < 5:
            c = WTR[3]
        elif d < 8:
            c = WTR[3] if chk else WTR[2]
        elif d < 26:
            c = WTR[2]
        elif d < 32:
            c = WTR[2] if chk else WTR[1]
        elif d < 60:
            c = WTR[1]
        else:
            n = smooth_noise(gx, y, 40, 861)
            c = WTR[0] if n > 0.55 else WTR[1]
            if d < 66 and chk:
                c = WTR[1]
        sw = (y + int(math.sin(gx / 23) * 4 + smooth_noise(gx, y, 60, 862) * 8)) % 19
        if (x, y) in calm:
            sw = -1
        if d > 46 and sw == 0 and noise2(gx // 9, y // 19, 864) > 0.25:
            c = WTR[2] if d > 56 else WTR[3]
        elif d > 50 and sw == 1 and noise2(gx // 5, y // 19, 863) > 0.8:
            c = '#F4F8F8'  # a whitecap out on the open sea
        cv.set(x, y, c)
    for (x, y) in water:  # the waterline
        dd = dist.get((x, y), 90)
        if (x, y) in calm:
            if dd == 0:
                cv.set(x, y, WTR[0])
            elif dd == 1 and (x + y) % 3:
                cv.set(x, y, WTR[1])
            continue
        if not surf:
            continue
        wob = int((smooth_noise(x, y, 5, seed + 1) - 0.5) * 3)
        if dd == 0 or (dd == 1 and (x + y) % 3):
            cv.set(x, y, FOAM)
        elif dd == 2 and (x // 2 + y) % 3:
            cv.set(x, y, WTR[4])
        elif dd == 6 + wob and smooth_noise(x, y, 9, seed + 2) > 0.45:
            cv.set(x, y, WTR[4] if (x + y) % 4 else FOAM)  # the next wave coming in
        elif dd == 7 + wob and smooth_noise(x, y, 9, seed + 2) > 0.5 and (x + y) % 2:
            cv.set(x, y, WTR[3])
    return dist


def cliff(cv: Canvas, top: dict, height: dict, seed: int = 0, lip=None) -> set:
    """A rock face seen from the front, from its turf lip at `top[x]` down `height[x]`
    px: stacked irregular blocks, each with a lit ledge along its top, a dark crevice
    under it and down its right side, the odd one mossy or darker; wet and dark with
    weed at its foot. The lip is turf breaking over the edge in tufts."""
    lip = lip or G
    face = {(x, y) for x, t in top.items() for y in range(t, t + height[x])}
    if not face:
        return face
    seeds = {}
    for (x, y) in face:
        gx, gy = x // 11, y // 7
        if (gx, gy) not in seeds:
            seeds[(gx, gy)] = (gx * 11 + noise2(gx, gy, seed) * 10, gy * 7 + noise2(gx, gy, seed + 1) * 6)
    owner = {}
    for (x, y) in face:
        gx, gy = x // 11, y // 7
        best, bd = None, 1e9
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                sd = seeds.get((gx + ox, gy + oy))
                if sd is None:
                    sd = ((gx + ox) * 11 + noise2(gx + ox, gy + oy, seed) * 10, (gy + oy) * 7 + noise2(gx + ox, gy + oy, seed + 1) * 6)
                d = ((x - sd[0]) / 1.5) ** 2 + (y - sd[1]) ** 2
                if d < bd:
                    best, bd = (gx + ox, gy + oy), d
        owner[(x, y)] = best
    for (x, y) in face:
        b = owner[(x, y)]
        k = y - top[x]
        t = 3 if noise2(b[0], b[1], seed + 2) > 0.55 else 2
        if noise2(b[0], b[1], seed + 3) > 0.9:
            t = 1
        up, dn, rt, lf = owner.get((x, y - 1)), owner.get((x, y + 1)), owner.get((x + 1, y)), owner.get((x - 1, y))
        if up != b:
            c = STONE[min(4, t + 1)] if up is not None else STONE[4]
        elif dn != b and dn is not None:
            c = STONE[0]
        elif rt != b and rt is not None:
            c = STONE[0] if (x + y) % 3 else STONE[1]
        elif lf != b and lf is not None:
            c = STONE[t + 1] if t < 3 else STONE[3]
        else:
            c = STONE[t]
            if noise2(x, y, seed + 4) > 0.93:
                c = STONE[t - 1]  # a pit in the stone
        if up != b and noise2(b[0], b[1], seed + 5) > 0.7 and (x + b[0]) % 3:
            c = LEAF[2] if (x + y) % 2 else LEAF[3]  # moss on the ledge
        foot = height[x] - k
        if foot <= 4:
            c = STONE[1] if c in (STONE[2], STONE[3], STONE[4]) else c
            if foot <= 2:
                c = '#2E4A3A' if (x + y) % 2 else STONE[0]  # weed and wet rock at the waterline
        cv.set(x, y, c)
    for x, t in top.items():  # the turf lip breaking over the edge
        cv.set(x, t - 1, lip[1])
        cv.set(x, t - 2, lip[3] if x % 3 else lip[4])
        if noise2(x // 2, t, seed + 6) > 0.5:
            cv.set(x, t, lip[2]); 
            if noise2(x, t, seed + 7) > 0.6:
                cv.set(x, t + 1, lip[1])
    return face


# ---------------------------------------------------------------------------------------
# The valley's river, in the valley's own coordinates (world-ports.md, "the valley's
# water"; Matt, 19 Oct: "the world does not need to be divided into screen sized
# sections"). The garden's stream leaves the garden at the riverside's west edge, runs
# east past the mill, swings south through the riverside's lower meadow, down the park's
# west side under the town street's bridge, along the Headland's west edge under the cliff
# path's bridge, and out into Driftwood's basin by the quay's east end. Every zone it
# crosses cuts its own part from the one line, so it meets itself at every border.
# ---------------------------------------------------------------------------------------
def _catmull(pts, step: float = 1.0):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


@functools.lru_cache(maxsize=1)
def river_course():
    """The river's centre line, sampled every pixel, with its half-width there."""
    pts = [(320 + x, meadow.stream_centre(x + 320) + x * 0.06) for x in range(0, 101, 20)]
    pts += [(470, 309), (536, 312), (584, 340), (600, 404), (582, 470), (536, 520), (498, 556), (488, 580),
            (476, 620), (450, 680), (420, 760), (396, 840), (384, 920), (376, 1020), (368, 1110), (366, 1160),
            (366, 1230), (365, 1300), (360, 1356), (346, 1390), (322, 1402), (302, 1410), (288, 1430), (281, 1452),
            (279, 1470)]
    line = _catmull(pts)
    out = []
    total = len(line)
    for i, (x, y) in enumerate(line):
        t = i / total
        if 400 < y < 1350:  # meanders on its way south, straightening where it crosses a border
            seam = min(y % 576, 576 - y % 576)
            x += 8 * math.sin(y / 38 + 1.3) * min(1.0, seam / 70) * min(1.0, (y - 400) / 60)
        if x < 380 and y < 400:  # still the garden's stream, as it leaves the garden
            h = 9 + (smooth_noise(x, 0, 13, 91) - 0.5) * 2.4 + max(0, x - 320) / 60 * 2
        else:
            h = 11 + 5 * min(1, t * 2) + (smooth_noise(i, 0, 60, 1401) - 0.5) * 9 + max(0, t - 0.88) * 30
        out.append((x, y, h))
    return out


@functools.lru_cache(maxsize=None)
def river_in(zone: str):
    """The river's water in one zone's pixels, its deep channel, and its centre points."""
    col, row = LAYOUT['valley'][zone]
    ox, oy = col * W, row * H
    water, deep, line = set(), set(), []
    for (x, y, h) in river_course():
        lx, ly = x - ox, y - oy
        if -40 <= lx < W + 40 and -40 <= ly < H + 40:
            line.append((lx, ly, h))
            for (px, py) in disc(lx, ly, h):
                if 0 <= px < W and 0 <= py < H:
                    water.add((px, py))
                    if math.hypot(px - lx, py - ly) < h * 0.45:
                        deep.add((px, py))
    return frozenset(water), frozenset(deep), tuple(line)


def river_at(zone: str, y: int):
    """The river's centre x in a zone at row y (None if it does not cross that row)."""
    best = None
    for (x, yy, h) in river_in(zone)[2]:
        if abs(yy - y) < 0.7:
            best = x
    return best


def stone_bridge(cv: Canvas, x0: int, x1: int, y0: int, y1: int, water: set, horizontal: bool = True):
    """A stone bridge carrying a road east-west over the river: a paved deck between two
    parapets of dressed stone with lit copings, the arch's dark mouth and its reflection
    on the water to the south, cutwaters at its feet. Returns the deck (walkable)."""
    deck = {(x, y) for x in range(x0, x1) for y in range(y0, y1)}
    worlds.paint_paving(cv, deck, seed=x0)
    for x in range(x0 - 2, x1 + 2):
        for (py, lit) in ((y0 - 3, True), (y1, False)):  # the parapets
            for k in range(3):
                c = STONE[4] if k == 0 and lit else STONE[3] if k == 0 else STONE[2] if (x + k * 3) % 7 else STONE[1]
                cv.set(x, py + k, c)
        for k in range(3, 11):  # the face of the bridge on the downstream (south) side
            y = y1 + k
            if (x, y) not in water and k > 3:
                continue
            c = STONE[2] if (x + (k // 3) * 4) % 8 else STONE[1]
            if k == 3:
                c = STONE[3]
            cv.set(x, y, c)
    span = [x for x in range(x0, x1) if any((x, y1 + 8 + k) in water for k in range(3))]
    if span:
        a, b = min(span), max(span)
        cx, r = (a + b) / 2, max(3, (b - a) / 2 - 2)
        for x in range(int(cx - r), int(cx + r) + 1):  # the arch's dark mouth
            hgt = int(math.sqrt(max(0, r * r - (x - cx) ** 2)) * 0.6)
            for k in range(hgt + 1):
                cv.set(x, y1 + 10 - k, WTR[0] if k < hgt else STONE[1])
            if (x, y1 + 12) in water:
                cv.set(x, y1 + 12, WTR[1]); cv.set(x, y1 + 13, WTR[1] if x % 2 else WTR[2])
    return deck


def field_mask(x0: int, y0: int, x1: int, y1: int, seed: int = 0) -> set:
    """A worked field: a plot set out by hand, roughly rectangular, with corners rounded
    where the plough turned and sides that wander a pixel or two with the ground."""
    pts = set()
    r = 9
    for y in range(y0, y1):
        wl = int((smooth_noise(0, y, 14, seed) - 0.5) * 4)
        wr = int((smooth_noise(1, y, 14, seed) - 0.5) * 4)
        for x in range(x0 + wl, x1 + wr):
            dx = max(x0 + r - x, 0, x - (x1 - r))
            dy = max(y0 + r - y, 0, y - (y1 - r))
            if dx * dx + dy * dy <= r * r:
                pts.add((x, y))
    return pts


def tilled(cv: Canvas, mask: set, row: int = 9, seed: int = 0, ridged: bool = True):
    """Ploughed earth in east-west rows: each ridge lit along its top, the furrow beside
    it in shade, clods and the odd stone; or (unridged) dug earth in soft patches."""
    S = MATERIALS['soil']
    y0 = min(y for _, y in mask)
    for (x, y) in mask:
        if ridged:
            r = (y - y0) % row
            c = S[4] if r == 0 else S[3] if r < 3 else S[2] if r < row - 2 else S[1]
            if r in (1, 2) and noise2(x // 2, y, seed) > 0.85:
                c = S[4]  # a clod catching the light
        else:
            n = smooth_noise(x, y, 5, seed)
            c = S[3] if n > 0.55 else S[2]
            if noise2(x // 2, y // 2, seed + 1) > 0.9:
                c = S[4]
        cv.set(x, y, c)


def rows_of(mask: set, row: int, step: int, seed: int = 0):
    """Plant positions along a field's ridges: set out by hand, so evenly spaced but
    each a little off its mark, and now and then one missing."""
    y0 = min(y for _, y in mask)
    xs = [x for x, _ in mask]
    out = []
    k = 0
    for y in range(y0 + 4, max(y for _, y in mask) - 2, row):
        off = (step // 2) * ((y - y0) // row % 2)
        for x in range(min(xs) + 5 + off, max(xs) - 3, step):
            k += 1
            if noise2(x, y, seed) < 0.06:
                continue
            cx, cy = x + int((noise2(x, y, seed + 1) - 0.5) * 2), y
            if all((cx + dx, cy + dy) in mask for dx in (-4, 4) for dy in (-3, 3)):
                out.append((cx, cy, k))
    return out


def cabbage_head(cv: Canvas, cx: int, cy: int, r: float, seed: int = 0):
    """A cabbage on its ridge: a ring of loose outer leaves, darker and veined, round a
    pale tight head lit on its upper left, on its own small shadow."""
    contact(cv, cx + 1, cy + 1, r + 1.5, r * 0.6 + 0.5)
    outer = blob(cx, cy, r + 1.4, (r + 1.4) * 0.8, seed=seed, rough=0.25)
    for (x, y) in outer:
        cv.set(x, y, LEAF[2] if (x - cx) + (y - cy) < 0 else LEAF[1])
    for (x, y) in edge_of(outer):
        if y >= cy:
            cv.set(x, y, LEAF[0])
        elif (x + y) % 2:
            cv.set(x, y, LEAF[3])
    head = disc(cx - 0.3, cy - 0.6, r * 0.8)
    for (x, y) in head:
        d = (x - cx) + (y - cy)
        cv.set(x, y, '#C9E0A0' if d < -r * 0.6 else '#A8C878' if d < r * 0.3 else '#86A85E')
    cv.set(int(cx), int(cy - 0.6), '#86A85E')  # the head's fold


WHEAT = ['#6E4F1E', '#A87E2C', '#C99A3C', '#E2BC5E', '#F2D27A', '#F8E6A0']


def wheat_field(cv: Canvas, mask: set, seed: int = 0):
    """Standing wheat seen from above and a little in front: a dense pile of ears in
    staggered rows, each ear lit on its top, the stems in shade between them; long
    swathes where the wind has laid it lighter; stalks showing along the front edge and
    heads breaking over the back edge; a shaded right side."""
    xs = [x for x, _ in mask]
    x1 = max(xs)
    for (x, y) in mask:  # the shade down among the stalks
        cv.set(x, y, WHEAT[1] if (x + y // 2) % 3 else WHEAT[2])
    ys = [y for _, y in mask]
    for gy in range(min(ys) - 1, max(ys) + 1, 3):
        for gx in range(min(xs) + (gy // 3 % 2) * 2, x1 + 1, 4):
            if noise2(gx, gy, seed) < 0.08:
                continue
            ex = gx + int((noise2(gx, gy, seed + 1) - 0.5) * 3)
            ey = gy + int((noise2(gx, gy, seed + 2) - 0.5) * 2)
            wind = smooth_noise(ex + ey * 0.5, ey, 10, seed + 3) > 0.6
            lean = 1 if wind else 0
            shade = 1 if ex > x1 - 5 else 0
            ear = [(ex + lean, ey, WHEAT[5 - shade] if not wind else WHEAT[5]), (ex, ey + 1, WHEAT[4 - shade]),
                   (ex + 1, ey + 1, WHEAT[3 - shade]), (ex, ey + 2, WHEAT[3 - shade]), (ex + 1, ey + 2, WHEAT[2 - shade])]
            for (px, py, c) in ear:
                if (px, py) in mask:
                    cv.set(px, py, c)
    for (x, y) in edge_of(mask):
        if (x, y + 1) not in mask:  # the front edge: stalks standing on the ground
            for k in range(1, 3):
                if (x, y + k) not in mask and x % 2 == 0:
                    cv.set(x, y + k, WHEAT[1] if k == 1 else WHEAT[0])
        if (x, y - 1) not in mask and x % 2:  # the back edge: ears nodding over it
            cv.set(x, y - 1, WHEAT[4])
            cv.set(x, y, WHEAT[5])


PUMPKIN = ['#6A2E12', '#A44C1A', '#D46E26', '#EE9840', '#FFC97A']


def pumpkin(cv: Canvas, cx: int, cy: int, w: int, seed: int = 0):
    """A pumpkin lying on the earth: a squat ribbed round, lit on its upper left, a dark
    groove between the ribs, a woody stalk, and its shadow."""
    h = max(3, int(w * 0.7))
    contact(cv, cx + 1, cy + h // 2, w / 2 + 1, 1.5)
    pts = blob(cx, cy, w / 2, h / 2, seed=seed, rough=0.06)
    for (x, y) in pts:
        f = (x - cx) / (w / 2) + (y - cy) / (h / 2) * 0.8
        c = PUMPKIN[4] if f < -0.95 else PUMPKIN[3] if f < -0.2 else PUMPKIN[2] if f < 0.6 else PUMPKIN[1]
        if abs((x - cx) % max(3, w // 3)) == 0 and abs(x - cx) < w / 2 - 1 and f > -0.9:
            c = PUMPKIN[1] if f > -0.2 else PUMPKIN[2]  # the grooves between the ribs
        cv.set(x, y, c)
    for (x, y) in edge_of(pts):
        if y >= cy:
            cv.set(x, y, PUMPKIN[0])
    top = min(y for _, y in pts)
    cv.set(cx, top - 1, WOOD[2]); cv.set(cx + 1, top - 1, WOOD[1]); cv.set(cx, top, WOOD[1])


def pumpkin_patch(cv: Canvas, mask: set, seed: int = 0):
    """Pumpkins growing on the dug earth: vines wandering across it with broad leaves
    in clumps, and pumpkins of every size lying along them."""
    xs, ys = [x for x, _ in mask], [y for _, y in mask]
    vines = []
    for v in range(7):
        x, y = min(xs) + 6 + v * (max(xs) - min(xs) - 12) // 6, min(ys) + 6 + int(noise2(v, 0, seed) * 8)
        a = noise2(v, 1, seed) * 6.28
        for t in range(70):
            a += (noise2(v, t, seed + 1) - 0.5) * 0.9
            x += math.cos(a) * 1.1
            y += abs(math.sin(a)) * 0.6 + 0.25
            if (int(x), int(y)) not in mask:
                break
            cv.set(int(x), int(y), LEAF[2])
            vines.append((int(x), int(y), v, t))
    for (x, y, v, t) in vines:
        if t % 9 == 4:  # a broad leaf
            for (lx, ly) in blob(x, y, 3, 2.2, seed=v * 31 + t, rough=0.3):
                if (lx, ly) in mask:
                    cv.set(lx, ly, LEAF[3] if (lx - x) + (ly - y) < 0 else LEAF[2])
            cv.set(x - 1, y - 1, LEAF[4]); cv.set(x + 1, y + 2, LEAF[1])
    spots = [(x, y, v) for (x, y, v, t) in vines if t % 19 == 11]
    for (x, y, v) in sorted(spots, key=lambda s: s[1]):
        w = 8 + int(noise2(x, y, seed + 2) * 6)
        if all((x + dx, y + dy) in mask for dx in (-w // 2 - 1, w // 2 + 1) for dy in (-3, 3)):
            pumpkin(cv, x, y, w, seed=v)


def margin(cv: Canvas, mask: set, seed: int = 0):
    """The uncut margin round a field: long grass tufts along its edge, thickest at the
    corners, the odd poppy and cornflower in it."""
    for (x, y) in edge_of(mask):
        q = [(x + dx, y + dy) for dx, dy in ((0, 2), (0, -2), (2, 0), (-2, 0)) if (x + dx, y + dy) not in mask]
        if not q or noise2(x, y, seed) > 0.42:
            continue
        gx, gy = q[0]
        detail.grass_tuft(cv, gx, gy + 1, int(noise2(x, y, seed + 1) * 6), G, 3)
        n = noise2(x, y, seed + 2)
        if n > 0.93:
            cv.set(gx, gy - 2, '#D8463A'); cv.set(gx + 1, gy - 2, '#B0303A')  # a poppy
        elif n < 0.05:
            cv.set(gx, gy - 2, '#5A7AD0')  # a cornflower


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
    plat = {(x, y) for x in range(64, 236) for y in range(282, 318)}
    worlds.paint_paving(cv, plat, seed=13)
    cv.hline(64, 316, 172, '#F4F0E6'); cv.hline(64, 317, 172, STONE[1])
    for y in range(282, 318):  # the platform's west end: a ramp down, edged
        cv.set(64, y, STONE[1]); cv.set(65, y, STONE[3])
    paint_rails(cv, 322)
    # west of the platform the line runs into a cutting through the rising ground, out of
    # the valley under the trees: a retaining wall on its north side, a grassy bank on
    # its south, both closing in toward the edge
    cut = set()
    for x in range(0, 62):
        depth = 4 + int((62 - x) / 62 * 10)
        top = 318 - depth
        detail.stones(cv, x, top, 1, depth + 1, STONE, seed=461 + x // 9, course=4, base=2)
        cv.set(x, top - 1, G[1]); cv.set(x, top - 2, G[3] if x % 3 else G[4])
        for y in range(top, 319):
            cut.add((x, y))
        bank_h = 3 + int((62 - x) / 62 * 8)
        for k in range(bank_h):  # the south bank: turf falling to the ballast
            y = 339 + k - bank_h + 3
            c = G[1] if k == bank_h - 1 else G[2] if k > 1 else G[3]
            if k == 0:
                c = LEAF[1]
            cv.set(x, y, c)
            cut.add((x, y))
        for k in range(2):
            style.darken(cv, x + 1, 320 + k)  # the wall's shadow on the ballast
    for y in range(316, 344):  # the line ends at a buffer before the town
        for x in range(246, W):
            cv.set(x, y, G[2] if (x + y) % 3 else G[3])
    for x in range(232, 244):
        cv.vline(x, 320, 18, WOOD[2] if x % 2 else WOOD[1])
    cv.hline(232, 320, 12, RED[3])
    # a farm track south from the lane, down the east side to the farmyard
    # (the farm ends at its yard: past it, to the south, the old forest begins, so
    # nothing runs off the edge into it; world-rules.md, every path ends at a node)
    # past the farm the land ends at a low sea cliff (the open sea lies south of the halt)
    htop = {x: 556 + int((smooth_noise(x, 0, 13, 455) - 0.5) * 10) for x in range(W)}
    hh = {x: 11 + int(smooth_noise(x, 1, 9, 456) * 5) for x in range(W)}
    hsea = {(x, y) for x in range(W) for y in range(htop[x] + hh[x], H)}
    sea(cv, hsea, seed=457, open_edges='s')
    hface = cliff(cv, htop, hh, seed=458)
    track = worlds.thick([(298, 300), (304, 360), (300, 440), (292, 492), (262, 526)], 8, seed=33)
    yard = blob(236, 524, 62, 15, seed=459, rough=0.15)
    paint_road(cv, track | yard)
    # the fields behind the fence: worked plots with softened corners, their rows set out
    # east-west by hand; a margin of long grass round each, where the plough turned
    SOILm = MATERIALS['soil']
    cabbage = field_mask(14, 372, 142, 468, seed=81)
    wheat = field_mask(160, 372, 282, 444, seed=82)
    patch = field_mask(16, 482, 112, 538, seed=83)
    tilled(cv, cabbage, row=9, seed=84)
    tilled(cv, patch, row=11, seed=85, ridged=False)
    for (cx, cy, k) in rows_of(cabbage, row=9, step=8, seed=86):
        cabbage_head(cv, cx, cy, 2.2 + noise2(cx, cy, 87) * 1.3, seed=k)
    wheat_field(cv, wheat, seed=88)
    pumpkin_patch(cv, patch, seed=89)
    for mask in (cabbage, wheat, patch):
        margin(cv, mask, seed=90)
    # the windmill grinds the farm's wheat: a cart track up from the lane to its door,
    # and a cobbled apron round its foot
    mill_track = worlds.thick([(266, 294), (272, 240), (256, 182)], 6, seed=91)
    paint_road(cv, mill_track)
    apron = blob(252, 172, 26, 9, seed=92, rough=0.12)
    worlds.paint_paving(cv, apron, seed=93)
    for (x, y) in edge_of(apron):
        cv.set(x, y, STONE[1] if (x, y + 1) not in apron else STONE[3])
    objects = [
        ('station', 'station_house', 66, 204), ('signal', 'semaphore', 40, 244), ('bench-p', 'bench', 190, 280),
        ('lamp-p1', 'lamp', 70, 268), ('pine-c1', 'pine', -14, 228), ('bush-c2', 'bush', 4, 344), ('lamp-p2', 'lamp', 220, 268), ('sack-p', 'sack', 178, 300), ('crate-p', 'crate', 160, 298),
        ('pine-n1', 'pine', 10, 20), ('tree-n2', 'tree', 90, 30), ('pine-n3', 'pine', 150, 14),
        ('mill', 'windmill', 226, 70), ('sack-m', 'sack', 276, 160), ('bush-1', 'bush', 286, 200), ('bush-2', 'bush', 6, 200),
        ('fence-1', 'fence_c', 18, 356), ('fence-2', 'fence_c', 78, 356), ('fence-3', 'fence_c', 138, 356),
        ('fence-4', 'fence_c', 198, 356),
        ('scarecrow', 'scarecrow', 204, 384), ('barn', 'barn', 150, 452),
        # the hay stacked against the barn's west wall, by the pumpkin patch, out of the rain
        ('hay-1', 'haystack', 118, 486), ('hay-2', 'hay_bale', 124, 518),
        ('trough-f', 'trough', 254, 474), ('wood-f', 'woodpile', 276, 508), ('barrel-f', 'barrel', 258, 506),
        ('tree-s2', 'tree_autumn', 150, 160),
    ]
    rails = {(x, y) for x in range(0, 246) for y in range(319, 338)}
    stands = {'town': (312, 300), 'platform': (130, 300), 'station': (118, 292), 'mill': (258, 186),
              'farm': (262, 530)}
    return cv, objects, stands, rails | cut | cabbage | wheat | patch | hsea | hface


def footbridge(cv: Canvas, x0: int, w: int, y0: int, y1: int, water: set):
    """A plank footbridge carrying a path north-south over a stream, in the same
    three-quarter view as the buildings: planks laid across on two log stringers, each
    plank lit along its top edge with grain and a nail at each end, a rail on posts
    along each side (the west rail lit, the east in shade, throwing its shadow on the
    water), and stone abutments on both banks, the south one showing its face."""
    for y in range(y0, y1):
        r = (y - y0) % 3
        pk = (y - y0) // 3
        for x in range(x0, x0 + w):
            t = 3 + (1 if noise2(pk, 0, 791) > 0.8 else -1 if noise2(pk, 0, 791) < 0.2 else 0)
            c = detail.tone(WOOD, t + 1) if r == 0 else detail.tone(WOOD, t) if r == 1 else WOOD[1]
            if r == 1 and noise2(x // 3, pk, 792) < 0.2:
                c = detail.tone(WOOD, t - 1)  # grain
            if x in (x0 + 1, x0 + w - 2) and r == 1:
                c = STONE[1]  # nail heads over the stringers
            cv.set(x, y, c)
    # the stone abutments: a step of dressed stones at each end, the south face lit
    for x in range(x0 - 3, x0 + w + 3):
        for k in range(3):
            y = y0 - 1 - k
            if (x, y) not in water:
                cv.set(x, y, STONE[3] if k == 2 else STONE[2] if (x + k) % 5 else STONE[1])
        for k in range(4):
            y = y1 + k
            c = STONE[4] if k == 0 else STONE[3] if (x + (k // 2) * 3) % 6 else STONE[1]
            if k == 3:
                c = STONE[1]
            cv.set(x, y, c)
    # rails on posts: posts stand at the ends and the middle, the rail runs over them
    for (rx, lit) in ((x0 - 1, True), (x0 + w, False)):
        for y in range(y0 - 4, y1 - 2):
            cv.set(rx, y, WOOD[4] if lit else WOOD[2])
            if not lit:
                cv.set(rx + 1, y, WOOD[1])
        for py in (y0 - 1, (y0 + y1) // 2, y1 - 1):
            for k in range(4):
                cv.set(rx, py - k, WOOD[3] if lit else WOOD[1])
                cv.set(rx + (1 if lit else -1), py - k, WOOD[2] if lit else WOOD[1]) if k == 3 else None
    for y in range(y0 - 2, y1 + 2):  # the bridge's shadow on the water, down and right
        for x in range(x0 + w + 2, x0 + w + 5):
            if (x, y) in water:
                style.darken(cv, x, y)


def woodland(frame: int = 0):
    """The Woodland, west of the garden: the garden's stream is born here. It leaves the
    east edge exactly where it enters the garden, and upstream it springs from a heap of
    mossy boulders, falling in a white ribbon into a rock pool. Old trees close in at
    the edges with the floor going dark under them, light comes through in dappled
    pools, a path winds over a plank bridge to a sunlit glade round the hollow oak, where
    a ring of toadstools has come up in the grass, and south of the stream to the old
    stone circle. Ferns grow where it is damp and shaded."""
    GOLDm = MATERIALS['gold']
    cv = Canvas(W, H)
    ground.valley(cv, 'woodland', frame)  # one turf across the valley (ground.py)
    OFF = -meadow.W

    def centre(x):
        return meadow.stream_centre(x + OFF)

    def half(x):
        full = 9 + (smooth_noise(x + OFF, 0, 13, 91) - 0.5) * 2.4
        return full * min(1.0, max(0.0, (x - 96) / 120)) + 3 * (x >= 96)

    spring_x = 96
    cy = int(centre(spring_x))
    river = {(x, y) for x in range(spring_x, W) for y in range(int(centre(x) - half(x)), int(centre(x) + half(x)) + 1)}
    # the rock pool: an organic basin under the fall, its outlet narrowing into the stream
    pool = blob(spring_x - 10, cy + 1, 22, 11, seed=61, rough=0.2)
    water = river | pool
    deep = {(x, y) for (x, y) in pool if math.hypot((x - spring_x + 12) / 15, (y - cy) / 6) < 1}
    deep |= {(x, y) for (x, y) in river if half(x) > 8 and abs(y - centre(x)) < half(x) * 0.35}
    # the spring's rocks: a heap of mossy boulders behind (north of) the pool, the fall
    # coming down a cleft between them; the meltwater brook from Fir Hollow (frost_zones
    # FALLS_X) runs to the top of the heap under the trees
    fx = spring_x - 16
    brook = worlds.thick([(FALLS_X, -4), (62, 60), (54, 140), (62, 214), (fx + 2, cy - 40)], 3)
    rocks = [(fx - 30, cy - 9, 30, 22), (fx + 22, cy - 9, 28, 20), (fx - 14, cy - 22, 26, 22),
             (fx + 13, cy - 24, 24, 22), (fx - 2, cy - 36, 22, 16), (fx + 32, cy - 20, 16, 12),
             (fx - 40, cy - 20, 18, 13), (fx + 4, cy + 1 - 22 + 22, 1, 1)]
    rocks = [r for r in rocks if r[2] > 2]
    bank(cv, water, keep=set(brook), seed=62)
    water_body(cv, water, deep, seed=63, glints=60)
    for (x, y) in brook:
        if y > cy - 46:
            continue
        c = WTR[2] if (x + y // 2) % 4 else WTR[3]
        if (x - 1, y) not in brook:
            c = WTR[0]
        elif (x + 1, y) not in brook:
            c = WTR[1]
        cv.set(x, y, c)
    for (x, y) in brook:  # mossy stones along the brook
        if (x + 1, y) not in brook and y < cy - 46 and noise2(x, y, 428) > 0.55:
            cv.set(x + 1, y, STONE[2] if (x + y) % 3 else LEAF[2])
        if (x - 1, y) not in brook and y < cy - 46 and noise2(x, y, 429) > 0.7:
            cv.set(x - 1, y, LEAF[1])
    rock = outcrop(cv, rocks, seed=64)
    waterfall(cv, fx - 1, 6, cy - 40, cy - 2, seed=65)
    # moss and drips round the cleft, ferns in the damp at the heap's foot
    for k in range(9):
        cv.set(fx - 3 - (k % 3), cy - 36 + k * 4, LEAF[3] if k % 2 else LEAF[2])
        cv.set(fx + 6 + (k % 2), cy - 34 + k * 4, LEAF[1])
    water = water | {p for p in brook if p not in rock}
    # the path from the garden's west side into the trees and the glade
    # (the garden's orchard walk runs on across the border at the same height and width)
    path = worlds.thick([(W + 12, meadow.ORCHARD_WALK_Y), (250, meadow.ORCHARD_WALK_Y)], 8.5) | worlds.thick([(254, meadow.ORCHARD_WALK_Y), (190, 420), (150, 380), (130, 330)], 9, seed=25)
    path |= worlds.thick([(130, 270), (150, 200), (124, 150)], 9, seed=26)
    path |= worlds.thick([(130, 334), (130, 306)], 7) | worlds.thick([(130, 274), (130, 296)], 7)  # onto the bridge
    # the glade: a sunlit hollow in the trees round the oak, with a wandering edge
    glade = blob(112, 136, 58, 38, seed=66, rough=0.24)
    for (x, y) in glade:
        n = smooth_noise(x, y, 14, 425)
        e = min(math.hypot(x - ex, y - ey) for (ex, ey) in ((112, 136),)) / 60
        if (x, y) not in path:
            c = G[3] if n > 0.42 else G[2]
            if e > 0.75 and (x // 2 + y // 2) % 2 and n < 0.5:
                c = FOREST_FLOOR[3]
            cv.set(x, y, c)
    for (x, y) in edge_of(glade):  # the glade's edge frays into the forest floor in clumps
        if noise2(x // 2, y // 2, 667) > 0.45:
            cv.set(x, y, FOREST_FLOOR[2])
    spur = worlds.thick([(152, 386), (118, 408)], 5, seed=27)  # to the stone circle
    paint_road(cv, spur)
    paint_road(cv, {(x, y) for (x, y) in path if (x, y) not in water} | {(x, y) for (x0, y) in path if x0 == W - 1 for x in range(W, W + 12)})
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
    # the stone circle in its own small clearing: a ring of reddish trodden earth round
    # muted grass, the stones standing in it (the reference Matt chose as the bar)
    SX, SY, SRX, SRY = 78, 410, 44, 24
    ring_out = blob(SX, SY, SRX + 2, SRY + 2, seed=68, rough=0.12)
    ring_in = blob(SX, SY, SRX * 0.7, SRY * 0.68, seed=69, rough=0.14)
    for (x, y) in ring_out:
        if (x, y) in ring_in:
            n = smooth_noise(x, y, 9, 428)
            cv.set(x, y, '#86A755' if n > 0.42 else '#76984A')
        else:
            n = noise2(x // 2, y // 2, 429)
            c = '#AE7E64' if n > 0.35 else '#9A6A52'
            if any((x + d, y) in ring_in for d in (-1, 1)) and (x + y) % 2:
                c = '#76984A'  # the grass fraying onto the earth
            cv.set(x, y, c)
    for (x, y) in edge_of(ring_out):
        if (x, y + 1) not in ring_out:
            cv.set(x, y, '#C29A7E')  # the lit outer lip
        elif noise2(x, y, 670) > 0.5:
            cv.set(x, y, '#76984A')
    # where the canopy closes in at the outer edges the floor goes into shade: two calm
    # steps of shadow in broad soft-edged pools (no checker), darkest in the far corner
    keep = set(path) | water | rock | glade | ring_out
    for y in range(H):
        for x in range(W):
            if (x, y) in keep:
                continue
            d = min(x + 6, y + 18)
            s = (1 - d / 64 + (smooth_noise(x, y, 16, 431) - 0.5) * 0.7) * min(1.0, (H - y) / 70)
            if s > 0.12:
                style.darken(cv, x, y)
            if s > 0.55:
                style.darken(cv, x, y, (0.8, 0.82, 0.86))
    # dappled light through the canopy, and the glade in full sun
    for i in range(10):
        lx, ly = 20 + int(noise2(i, 0, 426) * 290), 170 + int(noise2(i, 1, 426) * 380)
        light_pool(cv, lx, ly, 10 + i % 3 * 4, 5 + i % 2 * 3, GOLDm[2], water | rock | path)
    sun = blob(108, 128, 40, 24, seed=72, rough=0.3)  # the sun on the glade, in a ragged patch
    for (x, y) in sun - path:
        if smooth_noise(x, y, 6, 673) > 0.35 or (x + y) % 2 == 0:
            c = cv.get(x, y)
            cv.set(x, y, tuple(int(c[i] + (_rgb(G[4])[i] - c[i]) * 0.3) for i in range(3)) + (255,))
    # the fairy ring: toadstools come up in a broken ring in the glade, the grass
    # inside it greener where the ring has fed it (not a grid of one mushroom)
    RX, RY = 154, 162
    for k in range(13):
        a = 2 * math.pi * k / 13 + noise2(k, 0, 671) * 0.4
        rr = 1 + (noise2(k, 1, 671) - 0.5) * 0.25
        mx, my = int(RX + 15 * rr * math.cos(a)), int(RY + 8 * rr * math.sin(a))
        if noise2(k, 2, 671) < 0.15:
            continue
        for (gx, gy) in disc(mx, my, 2.5):
            if (gx, gy) not in path:
                cv.set(gx, gy, G[1] if (gx + gy) % 2 else G[2])
    shrooms = []
    for k in range(13):
        a = 2 * math.pi * k / 13 + noise2(k, 0, 671) * 0.4
        rr = 1 + (noise2(k, 1, 671) - 0.5) * 0.25
        if noise2(k, 2, 671) < 0.15:
            continue
        shrooms.append((int(RX + 15 * rr * math.cos(a)), int(RY + 8 * rr * math.sin(a)), 2 + int(noise2(k, 3, 671) * 3), k))
    for (mx, my, sz, k) in sorted(shrooms, key=lambda m: m[1]):
        mushroom(cv, mx, my, sz, seed=k)
    # ferns where it is damp and shaded: by the spring, along the stream, at the trees' feet
    for (x, y, s) in ((44, 272, 1.1), (fx + 46, cy - 6, 0.9), (180, 352, 1.0), (262, 412, 1.1), (98, 322, 0.9),
                      (154, 244, 1.0), (30, 470, 1.2), (228, 266, 0.85), (20, 330, 1.0), (206, 520, 1.0),
                      (120, 228, 0.8), (290, 350, 0.9), (60, 250, 1.0), (250, 300, 0.9), (300, 470, 1.0), (20, 560, 1.1),
                      (110, 524, 0.9), (270, 236, 0.9), (204, 176, 0.8), (60, 170, 0.9), (16, 404, 1.0), (292, 560, 1.0)):
        if all((x + dx, y + dy) not in path and (x + dx, y + dy) not in water for dx in range(-16, 17, 2) for dy in range(-14, 4, 2)):
            fern(cv, x, y, seed=x * 7 + y, size=s * 1.5)
    for (x, y) in ((fx - 46, cy + 4), (fx + 44, cy + 8), (196, int(centre(196) + half(196)) + 1)):
        reeds(cv, x, y, seed=x)
    # a few fallen leaves gathered in drifts under the deciduous trees
    for i in range(70):
        bx, by = ((200, 150), (60, 500), (250, 520), (30, 220), (230, 340))[i % 5]
        x, y = bx + int((noise2(i, 0, 421) - 0.5) * 50), by + int((noise2(i, 1, 421) - 0.5) * 30)
        if (x, y) in keep:
            continue
        col = ('#B8703A', '#8A4A2A', '#D2A04E')[i % 3]
        cv.set(x, y, col); cv.set(x + 1, y, col); cv.set(x + 1, y + 1, '#4A2E1E')
    objects = [
        # the stone circle
        ('stone-1', 'standing_stone', SX - 10, SY - SRY - 26), ('stone-2', 'standing_stone_b', SX + 26, SY - SRY - 18),
        ('stone-3', 'standing_stone_low', SX + SRX - 8, SY - 10), ('stone-4', 'standing_stone', SX + 22, SY + SRY - 26),
        ('stone-5', 'standing_stone_b', SX - 34, SY + SRY - 28), ('stone-6', 'standing_stone_low', SX - SRX - 4, SY - 14),
        ('stone-7', 'standing_stone_low', SX - 38, SY - SRY - 12),
        ('stump-1', 'stump', 166, 232), ('stump-2', 'stump', 40, 340), ('stump-3', 'stump', 236, 120),
        ('pine-6', 'pine', -16, 110), ('pine-7', 'pine', 110, -44), ('tree-8', 'tree_small', -26, 380),
        ('bush-2', 'bush', 4, 250), ('bush-3', 'bush', 160, 40),
        # old trees closing in round the edges (none crosses the east border into the garden)
        ('tree-1', 'tree', -20, -30), ('pine-1', 'pine', 50, -40), ('tree-2', 'tree', 200, -26), ('pine-2', 'pine', 250, -36),
        ('tree-3', 'tree', -24, 200), ('pine-3', 'pine', -10, 330), ('tree-4', 'tree', 230, 160),
        ('tree-5', 'tree_small', 196, 300), ('pine-4', 'pine', 20, 470), ('tree-6', 'tree', 60, 480),
        ('pine-5', 'pine', 150, 490), ('tree-7', 'tree_small', 250, 504),
        ('oak', 'hollow_tree', 70, 30), ('log-1', 'mossy_log', 200, 230),
        ('log-2', 'mossy_log', 128, 468), ('bench', 'forest_bench', 150, 186),
        ('willow', 'willow', 220, 340), ('bush-1', 'bush', 286, 380),
    ]
    # the plank footbridge where the path crosses the young stream
    by0, by1 = int(centre(130) - half(130)) - 2, int(centre(130) + half(130)) + 3
    plank = {(x, y) for x in range(122, 138) for y in range(by0 - 3, by1 + 4)}
    footbridge(cv, 123, 14, by0, by1, water)
    stands = {'garden': (304, meadow.ORCHARD_WALK_Y), 'clearing': (110, 160), 'spring': (100, int(centre(96)) + 18),
              'stones': (SX, SY + 4)}
    return cv, objects, stands, (water | rock) - plank

"""Cogsworth and the city: the junction and the canal, Neon Harbour and the skyport.

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401

import cyber_props as cp  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['junction', 'canal', 'skyport', 'grate', 'gear_ring', 'paint_fan', 'GRANITE', 'city_neon', 'city_heights',
           'city_plaza', 'city_waterfront', 'city_market', 'city_downtown', 'city_docks', 'city_point']


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


def ring_posts(cv: Canvas, cx: int, cy: int, rx: int, ry: int):
    """Short iron posts round a ring with a sagging rope between them, open toward the
    lane (east) where the way in is."""
    posts = []
    for k in range(14):
        a = 2 * math.pi * k / 14
        if abs(math.cos(a) - 1) < 0.12:
            continue  # the way in, facing the lane
        posts.append((int(cx + (rx + 7) * math.cos(a)), int(cy + (ry + 4) * math.sin(a))))
    for (x0, y0), (x1, y1) in zip(posts, posts[1:]):
        n = max(abs(x1 - x0), 1)
        for t in range(n + 1):
            x = x0 + (x1 - x0) * t // n
            y = y0 + (y1 - y0) * t // n - 5 + int(math.sin(math.pi * t / n) * 2)
            cv.set(x, y, MATERIALS['rope'][2])
    for (x, y) in posts:
        for d in range(7):
            cv.set(x, y - d, IRON[3] if d > 4 else IRON[2]); cv.set(x + 1, y - d, IRON[1])
        cv.set(x, y - 7, BRASS[4]); cv.set(x + 1, y + 1, IRON[0])


GRANITE = ['#3A3A42', '#55555E', '#73737A', '#93918F', '#B4B0A8', '#D2CDC2']


def paint_fan(cv: Canvas, mask, seed: int = 0, R: int = 15):
    """Setts laid in fans (segmental arcs, the way a square is paved by hand): each
    course a curve, each sett lit on its top edge, a dark joint all round, the stones'
    tones varied one by one, so the square reads as laid stone and never as one flat
    texture."""
    for (x, y) in mask:
        col = (x + (R if (y // R) % 2 else 0)) // (2 * R)
        u = x + (R if (y // R) % 2 else 0) - col * 2 * R - R
        yy = y + R - math.sqrt(max(0.0, R * R - u * u)) * 0.85
        row = int(yy // 4)
        along = x + row * 3
        stone = along // 5
        r, a = int(yy) % 4, along % 5
        t = noise2(stone, row, 1701 + seed)
        base = GRANITE[4] if t > 0.78 else GRANITE[3] if t > 0.3 else GRANITE[2]
        if r == 0 or a == 0:
            c = GRANITE[1]
        elif r == 1:
            c = GRANITE[5] if t > 0.78 else GRANITE[4]
        elif r == 3 or a == 4:
            c = GRANITE[2] if base != GRANITE[2] else GRANITE[1]
        else:
            c = base
        cv.set(x, y, c)


def wear(cv: Canvas, lines, mask, width: float = 7.0, seed: int = 0):
    """Where feet go most the setts are polished paler: along the lines people walk
    (platform to tower, tower to the lane, the lane to each door), dithered at the edge."""
    for line in lines:
        for (x, y) in worlds.thick(line, width, seed=seed):
            if (x, y) in mask and noise2(x, y, 1711) > 0.35:
                r, g, b, a = cv.get(x, y)
                cv.set(x, y, (min(255, r + 14), min(255, g + 13), min(255, b + 10), a))


def cinder_yard(cv: Canvas, x0: int, y0: int, x1: int, y1: int, seed: int = 0):
    """A railway yard's ground: cinders and ballast in small lit and dark lumps, oil-dark
    where engines stood, sooty grass in the corners."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = (x // 3 + (y // 2) * 7) % 5
            n = noise2(x // 3, y // 2, 1720 + seed)
            c = IRON[3] if n > 0.8 else IRON[2] if n > 0.45 else STONE[1] if n > 0.15 else IRON[1]
            if (x % 3 == 0 or y % 2 == 0) and k:
                c = IRON[1] if c != IRON[1] else IRON[0]
            if smooth_noise(x, y, 18, 1721 + seed) > 0.76:
                c = IRON[0] if (x + y) % 2 else IRON[1]  # oil where engines stood
            if smooth_noise(x, y, 11, 1722 + seed) < 0.16 and (x + y) % 3:
                c = '#46583F' if (x + y) % 2 else '#5C6E4C'  # sooty grass
            cv.set(x, y, c)


def siding(cv: Canvas, blocked: set, x0: int, x1: int, y0: int):
    """A short siding: sleepers and rails ending at a timber buffer stop to the east."""
    for x in range(x0, x1, 7):
        for y in range(y0, y0 + 11):
            cv.set(x, y, WOOD[3] if y == y0 else WOOD[2]); cv.set(x + 1, y, WOOD[2]); cv.set(x + 2, y, WOOD[1])
    for ry in (y0 + 2, y0 + 8):
        cv.hline(x0, ry, x1 - x0, IRON[4]); cv.hline(x0, ry + 1, x1 - x0, IRON[2])
    for y in range(y0 - 4, y0 + 12):  # the buffer stop: a timber beam on rail posts
        for x in range(x1, x1 + 6):
            c = WOOD[4] if y < y0 - 1 else WOOD[3] if x < x1 + 2 else WOOD[1]
            if y in (y0 + 1, y0 + 7) and x < x1 + 3:
                c = RED[3]  # the buffers' red faces
            cv.set(x, y, c)
            blocked.add((x, y))


def sleeper_stack(cv: Canvas, blocked: set, x0: int, y0: int, n: int = 4):
    """Spare sleepers stacked crosswise: their lit tops and their end grain."""
    for k in range(n):
        y = y0 - k * 3
        for x in range(x0 + (k % 2) * 2, x0 + 30 + (k % 2) * 2):
            cv.set(x, y, WOOD[4] if x < x0 + 20 else WOOD[3]); cv.set(x, y + 1, WOOD[2]); cv.set(x, y + 2, WOOD[1])
            blocked |= {(x, y), (x, y + 1), (x, y + 2)}
    for x in range(x0, x0 + 32):
        style.darken(cv, x + 1, y0 + 3)


def junction(frame: int = 0):
    """Cogsworth Junction: the train from the valley stands at the platform, the
    square below has the clock tower and the tinkerers' workshops, pipes and steam
    vents, and the gear ring at the bottom. The rails run on east toward Dust Gulch."""
    cv = Canvas(W, H)
    worlds.grass(cv, frame, ['#2B3B2E', '#46583F', '#5C6E4C', '#6B7C55', '#8E9C6E'])  # sooty grass
    # north of the line: the engine yard, cinders and ballast, a siding ending at its
    # buffer stop, spare sleepers stacked; the signal box and the water tower stand
    # beside the running line (nothing is cut off by the world's edge)
    blocked = set()
    cinder_yard(cv, 0, 0, W, 80, seed=1)
    siding(cv, blocked, 128, 236, 12)
    sleeper_stack(cv, blocked, 248, 60, 4)
    sleeper_stack(cv, blocked, 20, 28, 3)
    paint_rails(cv, 82)
    # the platform: stone slabs with a painted edge
    plat = {(x, y) for x in range(W) for y in range(100, 134)}
    worlds.paint_paving(cv, plat, seed=7)
    cv.hline(0, 100, W, '#E8C860'); cv.hline(0, 101, W, '#B8962E')
    for x in range(0, W):
        cv.set(x, 134, STONE[1]); cv.set(x, 135, STONE[2])
    # the cobbled square and lanes
    # cobbled streets fill the town; the meadow only returns round the ring
    def square_edge(x):  # a gently curving edge, drawn back a little at the sides
        side = max(0, 30 - x, x - 290) / 30
        return 420 + int(math.sin(x / 41) * 5 + smooth_noise(x, 0, 23, 152) * 10 - side * 14)
    square = {(x, y) for x in range(W) for y in range(136, 436) if y < square_edge(x)}
    lane = worlds.thick([(160, 430), (160, 468)], 16)
    spur = worlds.thick([(150, 504), (128, 506)], 7)  # the short way off the lane into the ring
    paint_fan(cv, square | lane, seed=1)
    # a ring of dark granite setts round the clock tower, and a gutter down the lane
    for (x, y) in square:
        k = ((x - 163) / 52) ** 2 + ((y - 312) / 24) ** 2
        if 0.78 < k < 1.0:
            cv.set(x, y, GRANITE[1] if (x // 3 + y) % 2 else GRANITE[2])
        elif 0.74 < k <= 0.78:
            cv.set(x, y, GRANITE[4])
    for y in range(350, 470):
        cv.set(159, y, GRANITE[1]); cv.set(160, y, GRANITE[0] if y % 6 else GRANITE[2]); cv.set(161, y, GRANITE[3])
    wear(cv, [[(160, 136), (160, 176), (150, 300)], [(160, 330), (160, 436)], [(60, 240), (110, 270), (150, 300)],
              [(250, 262), (200, 290), (172, 300)], [(60, 392), (110, 360), (152, 336)], [(160, 120), (210, 120)]],
         square | lane)
    for (x, y) in square | lane:  # a kerb of dressed stone where the setts meet the grass
        if (x, y + 1) not in square and (x, y + 1) not in lane and y + 1 < H:
            cv.set(x, y, STONE[3]); cv.set(x, y + 1, STONE[1])
    for (gx, gy) in ((70, 190), (238, 196), (110, 360), (214, 372)):
        grate(cv, gx, gy)
    # the lane on south through the gap in the pipe wall, down to the canal
    south = {(x, y) for x in range(144, 176) for y in range(460, H + 4)}
    worlds.paint_cobbles(cv, south | spur)
    for y in range(460, H):
        if not (498 <= y <= 512):
            cv.set(143, y, STONE[3]); cv.set(142, y, STONE[1])
        cv.set(176, y, STONE[1]); cv.set(177, y, STONE[3])
    # the sparring ring beside the lane, not across it (art-faults.md, fault 19): an iron
    # floor with a toothed brass rim, ringed by short posts with a rope between them
    gear_ring(cv, 80, 508, 50, 21)
    ring_posts(cv, 80, 508, 50, 21)
    # the moored airship's shadow on the meadow, cast down and right of the ship
    for (x, y) in oval(268, 538, 34, 8):
        if 0 <= x < W and 0 <= y < H:
            k = ((x - 268) / 34) ** 2 + ((y - 538) / 8) ** 2
            style.darken(cv, x, y)
            if k < 0.55:
                style.darken(cv, x, y)
    objects = [
        # beside the running line: the signal box at the west end, the water tower east
        ('signal-box', 'signal_box', 4, 12), ('water-tower', 'engine_tank', 266, 12),
        ('wagon', 'coal_cart', 196, 2),
        # the train at the platform, steam from its stack
        ('engine', 'locomotive', 86, 33), ('puff-engine', 'steam_puff', 104, 12),
        # the platform
        ('lamp-p1', 'gas_lamp', 40, 92), ('lamp-p2', 'gas_lamp', 264, 92), ('bench-p', 'iron_bench', 208, 104),
        ('trunk-p1', 'steamer_trunk', 14, 112), ('trunk-p2', 'steamer_trunk', 30, 118), ('coal-p', 'coal_cart', 284, 110),
        # the square: the tinkerers' workshop, the lodging house, the outfitter's shop
        ('ws-left', 'workshop', 4, 150), ('ws-right', 'house_slate', 226, 152),
        ('tower', 'clock_tower', 136, 176),
        ('lamp-s1', 'gas_lamp', 112, 280), ('lamp-s2', 'gas_lamp', 196, 280),
        ('gears-1', 'gear_pile', 96, 228), ('pipes-1', 'pipe_run', 214, 420),
        ('puff-c1', 'steam_puff', 66, 132),
        ('ws-low', 'shop_ashlar', 2, 296), ('coal-1', 'coal_cart', 100, 384),
        ('trunk-2', 'steamer_trunk', 280, 396),
        ('puff-v3', 'steam_puff', 206, 352), ('kiosk', 'tea_kiosk', 250, 300),
        # round the ring
        ('lamp-r1', 'gas_lamp', 128, 466), ('bench-r', 'iron_bench', 52, 446),
        ('mast', 'airship_mast', 206, 392),
    ]
    stands = {'platform': (160, 120), 'tower': (160, 322), 'ring': (80, 508), 'workshop': (52, 248),
              'canal': (160, 568)}
    return cv, objects, stands, blocked


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
    paint_fan(cv, fore, seed=2)
    # the casting floors either side of the great door (the way to the door stays clear):
    # beds of moulding sand with the pig bed pressed in, a sow channel along each and
    # the pigs branching off it like teeth; the newest pour still glows nearest the door
    for (bx0, bx1) in ((28, 60), (86, 132)):
        for y in range(407, 428):
            for x in range(bx0, bx1):
                n = noise2(x // 2, y // 2, 1730)
                c = '#8C7A5E' if n > 0.5 else '#7A6A50' if n > 0.15 else '#9C8A6C'
                cv.set(x, y, '#B4A07E' if y == 407 else c)
                blocked.add((x, y))
        door_side = bx1 if bx0 < 72 else bx0
        for x in range(bx0 + 2, bx1 - 2):
            hot = abs(x - door_side) < 14
            cv.set(x, 417, '#FFB648' if hot else IRON[1]); cv.set(x, 418, '#F2721E' if hot else IRON[0])
        for px in range(bx0 + 3, bx1 - 3, 5):
            hot = abs(px - door_side) < 12
            for y in list(range(409, 416)) + list(range(420, 427)):
                c = ('#F2721E' if (y - 409) % 3 else '#FFB648') if hot else (IRON[2] if y in (409, 420) else IRON[1])
                cv.set(px, y, c); cv.set(px + 1, y, '#C2380E' if hot else IRON[0])
        for x in range(bx0, bx1):  # the bed's timber curb, lit on top
            cv.set(x, 406, WOOD[4]); cv.set(x, 428, WOOD[2])
        for y in range(406, 429):
            cv.set(bx0, y, WOOD[3]); cv.set(bx1 - 1, y, WOOD[1])
    light_pool(cv, 72, 412, 52, 18, '#FFB648')
    # the allotments (fault 23): beds of different sizes and crops, edged with boards
    # whose fronts are seen, gravel between them, a picket fence round the plot with
    # its gate on the lane
    for y in range(436, 556):
        for x in range(8, 314):
            n = noise2(x // 2, y // 2, 499)
            cv.set(x, y, '#8C8576' if n > 0.6 else '#76705F' if n > 0.25 else '#9C9584')
    beds = [(18, 452, 60, 24, 'cabbage'), (90, 448, 44, 30, 'beans'), (20, 492, 40, 28, 'marrow'),
            (68, 496, 66, 22, 'sprouts'), (186, 450, 60, 26, 'beans'), (256, 456, 48, 22, 'cabbage'),
            (190, 496, 46, 30, 'marrow'), (246, 494, 58, 26, 'sprouts')]
    for (bx, by, bw, bh, crop) in beds:
        allot_bed(cv, bx, by, bw, bh, crop, blocked)
    picket_fence(cv, blocked, 8, 314, 438, 556, gate=(142, 178))
    objects = [
        # warehouses either side of the lane at the top
        ('wh-1', 'warehouse', 14, -8), ('wh-2', 'workshop_round', 206, 24),
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
        ('gardener', 'automaton', 140, 476), ('cloche-1', 'cloche', 80, 502), ('cloche-2', 'cloche', 262, 500),
        ('compost', 'gear_pile', 284, 528), ('bench-a', 'iron_bench', 186, 404), ('lamp-5', 'gas_lamp', 248, 400),
    ]
    stands = {'junction': (160, 6), 'bridge': (160, 210), 'boat': (60, 166), 'lock': (264, 150),
              'foundry': (72, 418), 'terminus': (236, 384), 'allotments': (162, 520)}
    return cv, objects, stands, blocked


def allot_bed(cv: Canvas, bx: int, by: int, bw: int, bh: int, crop: str, blocked: set):
    """A raised bed: dark tilled earth, its board edging lit on top with the front
    board's face seen below, and a crop of its own."""
    SOIL = ['#22180F', '#2E2117', '#3A2A1E', '#4A3626']
    for y in range(by, by + bh):
        for x in range(bx, bx + bw):
            c = SOIL[2] if (y - by) % 5 else SOIL[1]
            if noise2(x, y, 520) > 0.9:
                c = SOIL[3]
            cv.set(x, y, c)
            blocked.add((x, y))
    for x in range(bx - 1, bx + bw + 1):
        cv.set(x, by - 1, WOOD[4])
        cv.set(x, by + bh, WOOD[3]); cv.set(x, by + bh + 1, WOOD[2]); cv.set(x, by + bh + 2, WOOD[1])
        blocked |= {(x, by + bh), (x, by + bh + 1), (x, by + bh + 2)}
    for y in range(by - 1, by + bh + 3):
        cv.set(bx - 1, y, WOOD[3]); cv.set(bx + bw, y, WOOD[1])
    G_ = ['#2A4A2E', '#3E6A3C', '#5A8C4A', '#86B262']
    if crop == 'cabbage':
        for ry in range(by + 4, by + bh - 2, 8):
            for rx_ in range(bx + 5 + (ry // 8) % 2 * 4, bx + bw - 3, 9):
                for (x, y) in disc(rx_, ry, 3.2):
                    cv.set(x, y, G_[3] if (x - rx_) + (y - ry) < -1 else G_[2] if (x - rx_) + (y - ry) < 2 else G_[1])
                cv.set(rx_, ry, '#C8DCA0')
    elif crop == 'beans':
        for k, rx_ in enumerate(range(bx + 6, bx + bw - 4, 12)):
            for t in range(16):  # a wigwam of canes, leaves climbing it
                for side in (-1, 1):
                    x, y = rx_ + side * (t // 4), by + bh - 3 - t
                    cv.set(x, y, '#C8A870' if t % 5 else '#9A7A48')
                    if t % 3 == 1 and t > 3:
                        cv.set(x + side, y, G_[2] if side < 0 else G_[1])
            cv.set(rx_, by + bh - 19, '#9A7A48')
            for (x, y) in ((rx_ - 2, by + bh - 8), (rx_ + 3, by + bh - 11)):
                cv.set(x, y, '#E05A4A')  # a red flower
    elif crop == 'marrow':
        for k in range(3):
            lx, ly = bx + 8 + k * (bw - 14) // 2, by + 8 + (k % 2) * 8
            for (x, y) in oval(lx, ly, 7, 5):
                if bx <= x < bx + bw and by <= y < by + bh:
                    cv.set(x, y, G_[2] if (x - lx) + (y - ly) < 0 else G_[1])
            for (x, y) in oval(lx + 3, ly + 4, 3.5, 2):
                if bx <= x < bx + bw and by <= y < by + bh:
                    cv.set(x, y, '#E8C24A' if x < lx + 3 else '#B8902A')
    else:  # sprouts in rows
        for ry in range(by + 3, by + bh - 1, 5):
            for rx_ in range(bx + 3, bx + bw - 2, 4):
                if noise2(rx_, ry, 521) < 0.85:
                    cv.set(rx_, ry, G_[3]); cv.set(rx_ + 1, ry, G_[2]); cv.set(rx_, ry + 1, G_[1])


def picket_fence(cv: Canvas, blocked: set, x0: int, x1: int, y0: int, y1: int, gate):
    """A low picket fence round three sides of a plot (the fourth is the zone's edge),
    painted pickets lit on their left, two rails behind, open at the gate."""
    def picket(x, y):
        for d in range(6):
            cv.set(x, y - d, '#E8E2D4' if d < 5 else '#FFFFFF'); cv.set(x + 1, y - d, '#B8B0A0')
        cv.set(x, y + 1, '#5E5848'); cv.set(x + 1, y + 1, '#5E5848')
        blocked.update({(x, y), (x + 1, y), (x, y - 1), (x + 1, y - 1)})
    for x in range(x0, x1, 4):
        if gate[0] <= x < gate[1]:
            continue
        cv.set(x, y0 - 3, '#9A9282'); cv.set(x + 1, y0 - 3, '#9A9282'); cv.set(x + 2, y0 - 3, '#9A9282')
        cv.set(x + 3, y0 - 3, '#9A9282')
        picket(x, y0)
    for y in range(y0 + 4, y1 - 2, 4):
        picket(x0, y); picket(x1 - 2, y)
    for gx in gate:  # gateposts
        for d in range(9):
            cv.set(gx - (2 if gx == gate[0] else 0), y0 - d, WOOD[3] if d < 8 else WOOD[4])
            cv.set(gx - (1 if gx == gate[0] else -1), y0 - d, WOOD[1])


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
            # the concourse: pale slabs laid in a running bond (each course offset by half a
            # slab), a slab here and there a shade off, worn paler where people walk
            bx_ = x + (y // 16 % 2) * 12
            sx, sy = bx_ % 24, y % 16
            m = noise2(bx_ // 24, y // 16, 492)
            pale = PORC[2] if m > 0.45 else PORC[1]
            if m > 0.9:
                pale = PORC[3]
            if sx == 0 or sy == 0:
                pale = PORC[0]
            elif sy == 1:
                pale = PORC[3] if m > 0.45 else PORC[2]
            if 236 <= y < 252 or 440 <= y < 452:  # border courses of darker slabs
                pale = PORC[1] if not (sx == 0 or sy == 0) else PORC[0]
            # Neon's tiles end at a granite edge that wanders with the old core's paving,
            # not a dither down the zone's side (review, to-c-after-65)
            edge = 12 + int(smooth_noise(0, y, 36, 494) * 14)
            if x < edge:
                c = dark
            elif x < edge + 2:
                c = GRANITE[4] if x == edge else GRANITE[2]
            else:
                c = pale
            cv.set(x, y, c)
    for gx in range(40, W, 64):  # drains along the border course by the quay
        for x in range(gx, gx + 8):
            cv.set(x, 444, NIGHT[0]); cv.set(x, 445, NIGHT[1] if x % 2 else NIGHT[0])
    # a compass rose inlaid in the concourse floor, pointing the way up
    MX, MY = 140, 300
    for (x, y) in oval(MX, MY, 44, 22):
        d = math.hypot((x - MX) / 44, (y - MY) / 22)
        a = math.atan2((y - MY) * 2, x - MX)
        star = d < 0.95 * (0.35 + 0.65 * abs(math.cos(2 * a)) ** 6)  # four long points
        if 0.9 < d < 0.96 or 0.55 < d < 0.58:
            cv.set(x, y, CYAN[2] if (x + y) % 2 else CYAN[1])
        elif star:
            cv.set(x, y, PORC[4] if (x - MX) * 0.3 + (y - MY) < 0 else PORC[3])
        elif d < 0.9:
            cv.set(x, y, PORC[2])
    # a still reflecting pool under the platform, holding the platform lights
    pool = rect_set_z(16, 108, 70, 36)
    for (x, y) in pool:
        c = '#16324A' if (x + y // 2) % 9 else '#22486A'
        if y < 111:
            c = '#0B1220'  # the shadow of its rim
        if (x - 30) % 22 < 3 and y % 6 == 3:
            c = AMBER[3]  # the platform lights doubled
        cv.set(x, y, c)
        blocked.add((x, y))
    for (x, y) in rect_set_z(14, 106, 74, 40):
        if (x, y) not in pool:
            cv.set(x, y, PORC[4] if y < 108 or x < 16 else PORC[1])
            blocked.add((x, y))
    # Neon Harbour's street, continued, ending at a drop-off loop
    LX, LY = 238, 192
    loop = {(x, y) for (x, y) in oval(LX, LY, 66, 36)}
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
            if x % 20 == 0 or y % 12 == 6:
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
    for px0 in (222, 298):
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
    for y in range(470, H):  # the ribbon's guide light doubled in the water, broken by ripples
        if (x := AX + int((noise2(y // 3, 0, 493) - 0.5) * 3)) is not None and y % 5 < 3:
            cv.hline(x - 1, y, 3, CYAN[1] if y % 5 else '#16324A')
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
    # the ring stands on a concrete caisson (review 15:54, finding 7): below its south rim
    # a wet face drops to the waterline, darker toward it, foam where the swell breaks;
    # the pier's deck shows its thickness along both sides
    for (x, y) in ring:
        if (x, y + 1) not in ring and y > AY:
            for d in range(1, 7):
                cv.set(x, y + d, GRANITE[2] if d < 3 else GRANITE[1] if d < 5 else '#16202E')
            if noise2(x // 2, 0, 495) > 0.3:
                cv.set(x, y + 7, '#C8D8E8' if x % 3 else '#8AA0B8')
    for y in range(470, 500):  # the pier's sides seen edge on over the water
        cv.set(229, y, GRANITE[3]); cv.set(268, y, GRANITE[1])
    # the pier's entry: its paving runs north to a bank of ticket gates, and glass screens
    # close it either side down to the quay edge, so the gates are the way onto the pier
    for y in range(436, 466):
        for x in range(186, 311):
            c = PORC[3] if (y // 8) % 2 else PORC[2]
            if 208 <= x < 290 and (x - 208) % 15 >= 7 and y in (438, 439):
                c = AMBER[3] if x % 2 else AMBER[2]  # a tactile strip across each lane's mouth
            cv.set(x, y, c)
    for gx in (185, 311):  # the screens running south, seen edge on
        for y in range(426, 466):
            cv.set(gx, y, PORC[5] if y < 456 else PORC[2]); cv.set(gx + 1, y, '#96CEE2' if y < 456 else PORC[1])
            if y % 10 == 6:
                cv.set(gx - 1, y, PORC[4]); cv.set(gx + 2, y, PORC[1])
        for y in range(430, 467):
            for x in range(gx - 2, gx + 4):
                blocked.add((x, y))
    for bx in (80, 170):  # bollards, on the city quay's spacing
        for (x, y) in disc(bx, 460, 3):
            cv.set(x, y, NIGHT[4] if x < bx else NIGHT[2])
        cv.hline(bx - 2, 460, 5, AMBER[3])
    # the ribbon above the car (to-c-after-65): a thin cable rising out of view, catching the
    # light here and there, behind everything that stands on the concourse, fading upward
    for y in range(200, AY + 6 - 64):
        t = (y - 200) / (AY + 6 - 64 - 200)  # 0 far up, 1 at the car's grip
        if t < 0.35 and y % 4:
            continue
        if t < 0.65 and y % 7 == 6:
            continue
        cv.set(AX, y, CYAN[3] if y % 9 else '#E8FBFF')
        if t > 0.5:
            cv.set(AX - 1, y, PORC[4] if y % 5 else PORC[5]); cv.set(AX + 1, y, PORC[2])
    # light thrown only where it reads (the dark road); the pale floor carries its own sheen
    light_pool(cv, LX, LY, 40, 24, AMBER[3], skip=frozenset(water - ring - pier))
    blocked |= water - ring - pier
    WATER_MASKS['skyport'] = water - ring - pier
    # Everything has a reason to be where it is (faults 24-26): the departures hall between
    # the two pylons, with the wayfinding table on the compass; the gates across the
    # pier's entry; the lift docked on its ring; seats on the quay looking at the sea and
    # the lift, each backed by a planter as a windbreak; trees on the road's kerb either
    # side of the concourse; the flower kiosk between the guideway's piers.
    objects = [
        ('maglev', 'maglev', 26, 26), ('pylon-p', 'departure_pylon', 160, 40), ('light-p', 'street_light', 30, 40),
        ('tree-loop', 'city_tree_planted', LX - 14, LY - 44), ('tree-1', 'pod_tree', 280, 236), ('tree-2', 'pod_tree', 4, 236),
        ('pylon-1', 'departure_pylon', 60, 240), ('pylon-2', 'departure_pylon', 180, 240), ('holo', 'holo_map', MX - 20, MY - 36),
        ('gates', 'ticket_gates', 207, 406), ('screen-w', 'glass_screen', 184, 410), ('screen-e', 'glass_screen', 289, 410),
        ('planter-1', 'sky_planter', 4, 414), ('bench-1', 'sky_bench', 14, 442),
        ('planter-2', 'sky_planter_b', 92, 414), ('bench-2', 'sky_bench', 102, 442),
        ('bot-1', 'luggage_bot', 196, 380), ('bot-2', 'luggage_bot', 96, 352), ('tether', 'tether', AX - 28, AY + 6 - 272),
        ('drone-1', 'drone', 120, 140), ('drone-2', 'drone', 290, 300),
        ('kiosk', 'flower_kiosk', 240, 108),
    ]
    stands = {'neon': (10, 192), 'platform': (70, 84), 'gates': (248, 396), 'anchor': (AX, AY + 14)}
    return cv, objects, stands, blocked


# ---- Neon Harbour, the city (N1; Matt, 19 Oct 00:44: "a bigger bustling city with lots
# and lots of high buildings and possibly verticality") ---------------------------------
# Nine zones on a 3 x 3 grid on the south-east coast, the sea to the south and east; the
# old core (`neon`) and the Skyport keep their cells, so saves stay where they were. The
# whole city is planned and painted once in city coordinates (CW x CH, the region's own
# pixels from the heights' top-left) and each zone is cut from it, like the isles, so no
# street, kerb or quay seams at a zone border.
#
#   heights (0,-2)   plaza (1,-2)     waterfront (2,-2)
#   market (0,-1)    downtown (1,-1)  docks (2,-1)
#   neon (0,0)       skyport (1,0)    point (2,0)
#
# Streets come in three grades: the avenue and the cross streets (two lanes, kerbs,
# pavements with lights and trees), the lanes (one lane), and the pedestrian ways (the
# plaza, the quay promenade, the terminal walk). Every building faces south onto the
# pavement of the street below it, as everything does in the three-quarter view, and is
# never taller than its block is deep, so no building hides a street (two-level-walk.md,
# rule 6). Height you can walk is the heights' terraces, climbed by stairs; the decks
# (skybridges, the tram deck) are drawn overhead with their supports until the second
# walk level exists (docs/vision/two-level-walk.md).
from cyber_props import (CITY, CW, CH, CN, QUAY_X, HARBOUR_Y, STREETS, PLAZA, TERRACES, TERRACE_STAIRS,  # noqa: E402
                         FRONTAGES, chaikin, street_y, street_x, city_buildings, city_skybridges, LINES, DOCK_X, rim_y)


NIGHT_, PINK_, CYAN_, AMBER_ = (MATERIALS[k] for k in ('night', 'neon_pink', 'neon_cyan', 'neon_amber'))
CONC = ['#1E1C2A', '#2C2A3C', '#3C3A50', '#4E4C64', '#64627C', '#807E96']  # wet concrete at dusk
SEA_C = ['#0B1220', '#0E1626', '#121C30', '#22304C', '#30446A']
FACE_H = 18


def _poly_samples(line, step: float = 1.0):
    out = []
    s = 0.0
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, s + L * t, (x1 - x0) / L, (y1 - y0) / L))
        s += L
    x1, y1 = line[-1]
    out.append((x1, y1, s, out[-1][3], out[-1][4]))
    return out


def _band(line, hw: float) -> bytearray:
    """Pixels within hw of a smoothed polyline (city px)."""
    m = bytearray(CN)
    for (cx, cy, _s, _dx, _dy) in _poly_samples(line, 1.0):
        r = hw
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            if not 0 <= y < CH:
                continue
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if 0 <= x < CW and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    m[y * CW + x] = 1
    return m


class CityPlan:
    """The city's ground and masks (city px): `cv`, the walk's blocked pixels, the water,
    the street classes, the tier of every pixel on the heights, and where each street's
    pavements lie (for placing buildings and street furniture)."""

    def __init__(self):
        self.cv = Canvas(CW, CH)
        self.over = Canvas(CW, CH)
        self.blocked = bytearray(CN)
        self.water = bytearray(CN)
        self.road = bytearray(CN)
        self.pave = bytearray(CN)
        self.tier = bytearray(CN)
        self.face = {}
        self.lines = {}
        self.open = set()
        self.shut = set()
        self.setts = bytearray(CN)
        self.plaza = bytearray(CN)
        self.lots = []  # (bbox, cells) of each pocket park


@functools.lru_cache(maxsize=1)
def city() -> CityPlan:
    P = CityPlan()
    cv = P.cv
    px = cv.img.load()
    put = lambda x, y, c: px.__setitem__((x, y), _city_rgba(c))  # noqa: E731
    # ---- the land and the sea: the south harbour and the east sea, the point's
    # breakwater out to the lighthouse rock
    land = bytearray(CN)
    for y in range(CH):
        for x in range(CW):
            if y >= HARBOUR_Y and x < 760:
                continue
            if x >= (DOCK_X if 640 <= y <= 1110 else QUAY_X) and y < 1440:
                continue
            if y >= 1440 and x >= 760:
                # the point: the east quay turns the corner into the harbour's south quay
                if not (x < QUAY_X and y < HARBOUR_Y):
                    continue
            land[y * CW + x] = 1
    arm = _band(chaikin([(796, 1560), (836, 1580), (880, 1610), (900, 1640)], 2), 7)
    rock = bytearray(CN)
    for y in range(1620, 1700):
        for x in range(870, 950):
            if math.hypot((x - 908) / 34, (y - 1662) / 22) < 1 - (smooth_noise(x, y, 6, 1801) - 0.5) * 0.3:
                rock[y * CW + x] = 1
    for i in range(CN):
        if arm[i] and not land[i]:
            land[i] = 2  # the breakwater: walkable stone over the sea
        if rock[i]:
            land[i] = 3  # the lighthouse's rock
    for i in range(CN):
        if not land[i]:
            P.water[i] = 1
    # ---- streets: roads and pavements
    for (name, line, hw, pw, grade) in STREETS:
        sm = chaikin(line, 3)
        P.lines[name] = (sm, hw, pw, grade)
        r = _band(sm, hw) if hw else bytearray(CN)
        p = _band(sm, hw + pw) if pw else bytearray(CN)
        for i in range(CN):
            if land[i] == 1:
                if r[i]:
                    P.road[i] = 1
                elif p[i]:
                    P.pave[i] = 1
    # the quay road ends in a turning head where the point's promenade begins (review
    # 15:54, finding 3), kerbed like every other street
    qx, qy = P.lines['quayroad'][0][-1]
    for y in range(int(qy) - 30, int(qy) + 31):
        for x in range(int(qx) - 30, int(qx) + 31):
            d = math.hypot(x - qx, y - qy)
            i = y * CW + x
            if d <= 22:
                P.road[i] = 1
            elif d <= 28 and land[i] == 1:
                P.pave[i] = 1
    for i in range(CN):
        if P.road[i]:
            P.pave[i] = 0
    # the plaza: a square for people; the roads end at bollards round its edge
    pcx, pcy, prx, pry = PLAZA
    plaza = bytearray(CN)
    for y in range(pcy - pry - 2, pcy + pry + 3):
        for x in range(pcx - prx - 2, pcx + prx + 3):
            d = ((x - pcx) / prx) ** 2 + ((y - pcy) / pry) ** 2
            if d < 1:
                plaza[y * CW + x] = 1
                P.plaza[y * CW + x] = 1
                P.road[y * CW + x] = 0
                P.pave[y * CW + x] = 0
    # ---- the pedestrian streets (N3; review 15:54, finding 1 and 2): Market Street west of
    # Tower Row is the night market's street and the avenue above Hill Street climbs the
    # heights as a stepped street; both are laid in setts with no lanes, flush with their
    # pavements, and bollards stop the traffic where they meet a road
    av_sm, av_hw = P.lines['avenue'][0], P.lines['avenue'][1]
    hill_sm, hill_hw = P.lines['hill'][0], P.lines['hill'][1]
    mk_sm, mk_hw = P.lines['market'][0], P.lines['market'][1]
    av_road, hill_road, mk_road = _band(av_sm, av_hw), _band(hill_sm, hill_hw), _band(mk_sm, mk_hw)
    for i in range(CN):
        if not P.road[i]:
            continue
        y, x = divmod(i, CW)
        if (mk_road[i] and x < PED_MARKET_X and not av_road[i]) or (av_road[i] and y < 300 and not hill_road[i]):
            P.road[i] = 0
            P.pave[i] = 1
            P.setts[i] = 1
    for y in range(4, 60):  # the lookout at the top of the stepped street
        for x in range(LOOKOUT[0], LOOKOUT[1]):
            i = y * CW + x
            if not P.road[i]:
                P.setts[i] = 2
                P.pave[i] = 1
    # ---- the heights' terraces (x < 300): rims that follow the hill, flat where stairs cross
    for x in range(0, 380):
        r1 = rim_y(x, 232, 1810)
        r2 = rim_y(x, 150, 1812)
        for (sx, rim, sw) in TERRACE_STAIRS:
            if sx - 6 <= x < sx + sw + 6:
                if abs(rim - 232) < 4:
                    r1 = rim
                else:
                    r2 = rim
        for y in range(0, int(r1)):
            # the hill's east end curves into the Plaza's north-west corner instead of
            # stopping on a ruled line at the seam (review 15:54, finding 6)
            if x >= 306 + 54 * max(0.0, 1 - y / 250) ** 2:
                continue
            P.tier[y * CW + x] = 2 if y < r2 else 1
    # faces: south-facing rims hang a face below; the east ends are seen edge on
    for x in range(CW):
        for y in range(1, 300):
            a, b = P.tier[(y - 1) * CW + x], P.tier[y * CW + x]
            if a > b:
                for r in range(FACE_H * (a - b)):
                    if y + r < CH and P.tier[(y + r) * CW + x] <= b:
                        P.face[(x, y + r)] = (r, FACE_H * (a - b))
    # ---- paint
    for y in range(CH):
        for x in range(CW):
            i = y * CW + x
            if P.water[i]:
                n = smooth_noise(x, y, 9, 185)
                c = SEA_C[1] if n > 0.55 else SEA_C[2] if n > 0.3 else SEA_C[0]
                if (y % 7) == 3 and noise2(x // 9, y, 186) > 0.6:
                    c = SEA_C[3]
            elif land[i] == 2:  # the mole's top: dressed granite blocks, their joints dark
                bx = (x + (y // 4 % 2) * 3) // 6
                c = GRANITE[3] if noise2(bx, y // 4, 1820) > 0.45 else GRANITE[2]
                if y % 4 == 0 or (x + (y // 4 % 2) * 3) % 6 == 0:
                    c = GRANITE[1]
                if not land[i - CW] or not land[i - 1]:
                    c = GRANITE[5]  # the coping, lit on its upper-left edge
                P.blocked[i] = 0
            elif land[i] == 3:
                c = CONC[3] if smooth_noise(x, y, 4, 1821) > 0.5 else CONC[2]  # the rock's worn top, walked to the door
            elif P.road[i]:
                n = noise2(x // 2, y // 2, 182)
                c = NIGHT_[1] if n > 0.3 else NIGHT_[0]
                if smooth_noise(x, y, 14, 1822) > 0.72 and (x + y) % 2:
                    c = '#26304A'  # a sheen where rain lies on the road
            elif plaza[i]:
                c = _plaza_px(x, y)
            elif P.setts[i] == 1:
                c = _setts_px(x, y)
            elif P.setts[i] == 2:  # the lookout's flags, pale granite in a running bond
                fx, fy = (x + (y // 10) * 7) % 14, y % 10
                c = GRANITE[3] if noise2((x + (y // 10) * 7) // 14, y // 10, 1834) > 0.5 else GRANITE[2]
                if fx == 0 or fy == 0:
                    c = GRANITE[1]
            elif P.pave[i]:
                tx, ty = x % 8, y % 8
                n = noise2(x // 8, y // 8, 181)
                c = NIGHT_[3] if n > 0.5 else NIGHT_[2]
                if tx == 0 or ty == 0:
                    c = NIGHT_[1]
                elif ty == 1:
                    c = NIGHT_[4] if n > 0.5 else NIGHT_[3]
            elif x >= 640 and y >= 1100 and _blend(x, y, 1100, 100):  # the Skyport's pale slabs run on round the point
                sx, sy = x % 24, y % 16
                m = noise2(x // 24, y // 16, 492)
                c = PORC_C[2] if m > 0.45 else PORC_C[1]
                if sx == 0 or sy == 0:
                    c = PORC_C[0]
                elif sy == 1:
                    c = PORC_C[3] if m > 0.45 else PORC_C[2]
            elif x < 320 and y >= 1100 and _blend(x, y, 1100, 100):  # the old core keeps its square tiles
                tx, ty = x % 10, y % 10
                n = noise2(x // 10, y // 10, 181)
                c = NIGHT_[3] if n > 0.5 else NIGHT_[2]
                if tx == 0 or ty == 0:
                    c = NIGHT_[1]
                elif ty == 1:
                    c = NIGHT_[4] if n > 0.5 else NIGHT_[3]
            elif 1140 <= y < 1152 and 320 <= x < 640:  # the Skyport terminal's glass roof, its
                # north eave: the Skyport's roof runs on across the seam (review 15:54, finding 6)
                lx, ly = x - 320, y - 1152
                c = NIGHT_[2] if (lx // 20 + ly // 12) % 2 else NIGHT_[1]
                if lx % 20 == 0 or ly % 12 == 6:
                    c = PORC_C[2]
                if y == 1140:
                    c = PORC_C[4]  # the eave's lit edge
                elif y == 1141:
                    c = PORC_C[1]
                P.blocked[i] = 1
            else:  # courts, yards and the ground round the buildings: poured concrete, worn
                # and patched, a joint every few metres, never a ruled grid
                n = smooth_noise(x, y, 14, 1823)
                c = CONC[3] if n > 0.62 else CONC[2] if n > 0.28 else CONC[1]
                if noise2(x // 2, y // 2, 1825) > 0.93:
                    c = CONC[4] if c != CONC[1] else CONC[2]
                jx = (x + int(smooth_noise(0, y, 30, 1826) * 6)) % 40 == 0
                jy = (y + int(smooth_noise(x, 0, 30, 1827) * 6)) % 32 == 0
                if (jx or jy) and (x + y) % 3:
                    c = CONC[1]
                if noise2(x, y // 3, 1828) > 0.997:
                    c = CONC[0]  # a crack
                if y < 320 and x < 380 and P.tier[i] and smooth_noise(x, y, 20, 1824) > 0.55:
                    c = '#2E4A36' if (x + y) % 3 else '#3E5E40'  # gardens on the terraces
            put(x, y, c)
    # kerbs where a road meets a pavement: the lit top of the stone, its face below
    for y in range(1, CH - 1):
        for x in range(CW):
            i = y * CW + x
            if P.pave[i] and P.road[i + CW]:
                put(x, y, NIGHT_[5]); put(x, y - 1, NIGHT_[4])
            elif P.pave[i] and P.road[i - CW]:
                put(x, y, NIGHT_[4])
            elif P.pave[i] and ((x + 1 < CW and P.road[i + 1]) or (x > 0 and P.road[i - 1])):
                put(x, y, NIGHT_[4])
    # the buildings' ground: a building stands on its whole lot, from its front to the
    # street behind (N3), so nobody walks hidden under its roofs
    for (_key, spec, fx, fy) in city_buildings():
        w, depth = spec[0], spec[7]
        for y in range(max(0, fy - depth), min(CH, fy + 1)):
            for x in range(max(0, fx - w // 2 + 1), min(CW, fx + w // 2 - 1)):
                P.blocked[y * CW + x] = 1
    _pocket_parks(P, put)
    _court(P, put)
    _markings(P, put)
    _plaza_bollards(P, put)
    _ped_bollards(P, put)
    _tram_rails(P, put)
    _lookout_rail(P, put)
    _quays(P, put, land)
    _mole(P, put, land)
    _terrace_faces(P, put)
    return P


_CRGBA: dict = {}


def _city_rgba(c):
    if c in _CRGBA:
        return _CRGBA[c]
    _CRGBA[c] = (*_rgb(c), 255) if isinstance(c, str) else c
    return _CRGBA[c]


def _blend(x: int, y: int, y0: int, span: int) -> bool:
    """Whether a pixel takes the southern ground where two grounds meet over `span` px
    from row y0: an ordered dither by whole tiles, so the change never lines up with a
    seam (art-faults.md, rule 1)."""
    k = (y - y0) / span
    if k >= 1:
        return True
    bayer = (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)[((y // 10) % 4) * 4 + (x // 10) % 4] / 16
    return bayer < k


def _plaza_bollards(P: CityPlan, put):
    """Where a road meets the square, a row of steel bollards across it: cars stop,
    people walk on between them."""
    pcx, pcy, prx, pry = PLAZA
    ends = [(pcx - prx - 3, street_y('hill', pcx - prx - 3), 'v'), (pcx + prx + 3, street_y('hill', pcx + prx + 3), 'v'),
            (street_x('towerrow', pcy + pry + 3), pcy + pry + 3, 'h')]
    for (ex, ey, d) in ends:
        for k in range(-14, 15, 7):
            bx, by = (int(ex), int(ey) + k) if d == 'v' else (int(ex) + k, int(ey))
            for (x, y) in disc(bx, by - 2, 1.6):
                put(x, y, METAL_C[4] if x < bx else METAL_C[2])
            put(bx, by - 4, METAL_C[5]); put(bx + 1, by, NIGHT_[0])
            put(bx, by - 2, AMBER_[3])


METAL_C = ['#1A1E26', '#2A303C', '#3C4452', '#56606E', '#76808E', '#A0A8B4']
PED_MARKET_X = 452  # Market Street is a pedestrian street west of here
TRAM_END = 600  # the tram's buffer on Hill Street, by the square


def _tram_rails(P: CityPlan, put):
    """Two steel rails in Hill Street's middle from the waterfront to the buffer by the
    square, their running tops lit, set in a band of darker setts; the buffer stop."""
    for x in range(TRAM_END, QUAY_X - 30):
        cy = street_y('hill', x)
        for d in range(-6, 7):
            y = int(cy + d)
            if P.road[y * CW + x]:
                if d in (-4, 4):
                    put(x, y, METAL_C[5] if x % 2 else METAL_C[4])
                elif d in (-3, 3):
                    put(x, y, METAL_C[1])
                else:
                    put(x, y, _setts_px(x, y))
    cy = int(street_y('hill', TRAM_END))
    for y in range(cy - 6, cy + 7):  # the buffer: a steel frame with a red lamp
        put(TRAM_END, y, METAL_C[4]); put(TRAM_END + 1, y, METAL_C[2])
    put(TRAM_END, cy - 7, PINK_[3]); put(TRAM_END + 1, cy - 7, PINK_[2])
LOOKOUT = (112, 186)  # the lookout's x span at the top of the stepped street


def _pocket_parks(P: CityPlan, put):
    """The lots the buildings leave (Eastward's towns: "lots are never just ground"; review
    15:54): every open lot at least 24 px across, away from the docks' yard, becomes a
    pocket park: a lawn mown in stripes inside a kerb, a gravel path, flowers along its
    edge. The trees and a bench go on it in city_props_placed."""
    from collections import deque

    def yard(x, y):
        i = y * CW + x
        return not (P.water[i] or P.road[i] or P.pave[i] or P.setts[i] or P.blocked[i] or P.tier[i] or P.plaza[i]
                    or (x, y) in P.face) and y < 1100 and x < 744 and not (x >= 630 and y >= 870)
    cells = {(cx, cy) for cy in range(0, 1100 // 4) for cx in range(0, 744 // 4) if yard(cx * 4 + 2, cy * 4 + 2)}
    core = {c for c in cells if all((c[0] + dx, c[1] + dy) in cells for dx in (-3, 0, 3) for dy in (-3, 0, 3))}
    grown = {(c[0] + dx, c[1] + dy) for c in core for dx in range(-3, 4) for dy in range(-3, 4)} & cells
    seen = set()
    for c in sorted(grown):
        if c in seen:
            continue
        q, comp = deque([c]), []
        seen.add(c)
        while q:
            a = q.popleft()
            comp.append(a)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (a[0] + d[0], a[1] + d[1])
                if nb in grown and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        pix = {(cx * 4 + dx, cy * 4 + dy) for (cx, cy) in comp for dx in range(4) for dy in range(4)
               if yard(cx * 4 + dx, cy * 4 + dy)}
        xs, ys = [p[0] for p in pix], [p[1] for p in pix]
        P.lots.append(((min(xs), min(ys), max(xs), max(ys)), frozenset(c for c in comp if c in core)))
        for (x, y) in pix:
            edge = any((x + dx, y + dy) not in pix for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                c = CONC[4] if (x, y - 1) not in pix else CONC[2]  # the kerb round the lawn
            elif any((x + dx, y + dy) not in pix for dx in (-2, 2) for dy in (-2, 2)) and noise2(x, y, 1836) > 0.7:
                c = ('#E8A0C0', '#F2E2A0', '#C8C0F0')[(x + y) % 3]  # flowers along the edge
            else:
                c = '#3E5E40' if (x // 6) % 2 else '#4A6C46'  # the lawn, mown in stripes
                if noise2(x // 2, y // 2, 1837) > 0.85:
                    c = '#2E4A36'
            put(x, y, c)
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        for t in range(0, 1000):  # a gravel path across it, corner to corner
            px_ = int(x0 + (x1 - x0) * t / 1000)
            py_ = int(y1 - (y1 - y0) * t / 1000)
            for d in (-1, 0, 1):
                if (px_ + d, py_) in pix:
                    put(px_ + d, py_, GRANITE[3] if (px_ + py_ + d) % 3 else GRANITE[2])


def _mole(P: CityPlan, put, land):
    """The mole out to the lighthouse (review 15:54, finding 3): below its south and east
    edges a wet face of granite in shadow drops into the sea, darkening to the waterline,
    with a broken line of foam where the swell breaks on it; three steps down where it
    leaves the quay."""
    for y in range(1, CH - 8):
        for x in range(1, CW - 2):
            i = y * CW + x
            if land[i] != 2:
                continue
            if P.water[i + CW]:
                for d in range(1, 6):
                    if P.water[i + d * CW]:
                        put(x, y + d, GRANITE[1] if d < 3 else GRANITE[0] if d < 5 else '#16202E')
                if P.water[i + 6 * CW] and noise2(x // 2, y, 1838) > 0.35:
                    put(x, y + 6, '#C8D8E8' if x % 3 else '#8AA0B8')
            elif P.water[i + 1]:
                put(x + 1, y, GRANITE[1]); put(x + 2, y, GRANITE[0])
    for y in range(1, CH - 1):  # the steps where the mole leaves the quay
        for x in range(1, CW - 1):
            i = y * CW + x
            if land[i] == 2 and any(land[i + dx + dy * CW] == 1 for dx in (-8, 0, 8) for dy in (-8, 0, 8)):
                k = (x + y) % 4
                put(x, y, GRANITE[4] if k == 0 else GRANITE[3] if k == 1 else GRANITE[2])


def _setts_px(x: int, y: int) -> str:
    """Setts: small dark granite blocks laid in courses across the street, each course
    offset by half a block, the joints darker, a block here and there worn pale or wet."""
    course = y // 3
    bx = (x + (course % 2) * 2) // 4
    c = GRANITE[2] if noise2(bx, course, 1832) > 0.55 else GRANITE[1]
    if y % 3 == 0 or (x + (course % 2) * 2) % 4 == 0:
        c = GRANITE[0]
    elif noise2(bx, course, 1833) > 0.93:
        c = GRANITE[3]
    elif smooth_noise(x, y, 12, 1835) > 0.74 and (x + y) % 2:
        c = '#2A3046'  # where the rain lies
    return c


def _bollard(put, bx: int, by: int):
    for (x, y) in disc(bx, by - 2, 1.6):
        put(x, y, METAL_C[4] if x < bx else METAL_C[2])
    put(bx, by - 4, METAL_C[5]); put(bx + 1, by, NIGHT_[0])
    put(bx, by - 2, AMBER_[3])


def _ped_bollards(P: CityPlan, put):
    """Rows of bollards across each pedestrian street's mouth where it meets a road: at
    Tower Row, both sides of the avenue's crossing, and where the stepped street comes
    down to Hill Street. People walk on between them (they are drawn, not blocked)."""
    mk_hw = LINES['market'][1]
    ends = [(PED_MARKET_X - 2, street_y('market', PED_MARKET_X - 2), 'v')]
    yx = street_y('market', street_x('avenue', 880))
    ax = street_x('avenue', yx)
    ends += [(ax - LINES['avenue'][1] - 3, street_y('market', ax - 20), 'v'),
             (ax + LINES['avenue'][1] + 3, street_y('market', ax + 20), 'v')]
    for (ex, ey, d) in ends:
        for k in range(-mk_hw, mk_hw + 1, 7):
            _bollard(put, int(ex), int(ey) + k)
    qx, qy = P.lines['quayroad'][0][-1]
    for k in range(-21, 22, 7):  # beyond the quay road's turning head, the promenade
        _bollard(put, int(qx) + k, int(qy) + 31)
    for (x, y) in disc(qx, qy, 8):  # the turning head's island: a kerbed bed of shrubs
        d = math.hypot(x - qx, y - qy)
        put(x, y, NIGHT_[5] if d > 7 and y < qy else NIGHT_[4] if d > 7 else '#3E5E40' if (x + y) % 3 else '#2E4A36')
        P.shut.add((x, y))
    hy = street_y('hill', street_x('avenue', 280)) - LINES['hill'][1] - LINES['hill'][2] - 3
    hx = street_x('avenue', hy)
    for k in range(-LINES['avenue'][1], LINES['avenue'][1] + 1, 7):
        _bollard(put, int(hx) + k, int(hy))


def _lookout_rail(P: CityPlan, put):
    """The lookout's railing along its south edge either side of the stepped street, so
    you stand at the rail and look south over the city; posts every 6 px, a lit top rail."""
    y = 58
    ax = street_x('avenue', y)
    for x in range(LOOKOUT[0], LOOKOUT[1]):
        if abs(x - ax) < LINES['avenue'][1] + 2:
            continue
        put(x, y - 4, IRON[3]); put(x, y - 3, IRON[2])
        if x % 6 == 0:
            put(x, y - 2, IRON[2]); put(x, y - 1, IRON[1])
        P.shut.add((x, y - 1)); P.shut.add((x, y))


def _court(P: CityPlan, put):
    """The old core's sparring court: a ring painted on the tiles in neon tubes, cyan
    round a pink inner ring, the floor inside in a dark chequer (city px)."""
    ccx, ccy = 160, 1534
    for (x, y) in oval(ccx, ccy, 62, 28):
        put(x, y, NIGHT_[2] if (x // 6 + y // 6) % 2 else NIGHT_[3])
    for k in range(240):
        a = 2 * math.pi * k / 240
        for (rx, ry, ramp) in ((62, 28, CYAN_), (40, 18, PINK_)):
            x, y = int(ccx + rx * math.cos(a)), int(ccy + ry * math.sin(a))
            put(x, y, ramp[3]); put(x, y + 1, ramp[1])


def _plaza_px(x: int, y: int) -> str:
    """The square: pale granite slabs in rings round its centre, a dark inlay ring, and a
    radial joint every so often, so it reads as laid stone, not a flat fill."""
    pcx, pcy, prx, pry = PLAZA
    d = math.hypot((x - pcx) / prx, (y - pcy) / pry)
    a = math.atan2((y - pcy) * prx / pry, x - pcx)
    ring = int(d * 12)
    seg = int((a + math.pi) / (2 * math.pi) * (8 + ring * 6))
    t = noise2(ring, seg, 1830)
    c = PORC_C[3] if t > 0.5 else PORC_C[2]
    if abs(d * 12 - round(d * 12)) < 0.07 or abs(((a + math.pi) / (2 * math.pi) * (8 + ring * 6)) % 1) < 0.06:
        c = PORC_C[1]
    if 0.42 < d < 0.47:
        c = CYAN_[1] if (x + y) % 2 else CYAN_[0]
    return c


PORC_C = ['#3A4258', '#5C6680', '#8A94AC', '#B8C0D2', '#DCE2EC', '#F4F7FB']


def _markings(P: CityPlan, put):
    """Lane lines along each road (amber dashes in the middle, broken where another road
    crosses), and zebra crossings on each arm of a junction of two graded streets."""
    for name, (sm, hw, pw, grade) in P.lines.items():
        if not hw or name == 'harbour':
            continue
        for (cx, cy, s, dx, dy) in _poly_samples(sm, 1.0):
            x, y = int(cx), int(cy)
            if not (0 <= x < CW and 0 <= y < CH):
                continue
            others = [n for n, (sm2, hw2, _p, _g) in P.lines.items() if n != name and hw2 and
                      _seg_near(cx, cy, sm2, hw2 + 10)]
            if others:
                continue
            if not P.road[y * CW + x]:
                continue
            if name == 'hill' and x >= TRAM_END - 4:
                continue  # (the tram's rails run here instead)
            if int(s) % 12 < 6 and hw >= 12:
                put(x, y, AMBER_[2])
                put(x + int(round(-dy)), y + int(round(dx)), AMBER_[1])
    # zebras: where each avenue crosses a street, on the street's arms
    for name, (sm, hw, pw, grade) in P.lines.items():
        if name not in ('avenue', 'towerrow') or not hw:
            continue
        for other, (sm2, hw2, _p, _g) in P.lines.items():
            if other in ('avenue', 'towerrow', 'quayroad', 'terminal') or not hw2:
                continue
            for (cx, cy, s, dx, dy) in _poly_samples(sm, 1.0):
                if _seg_near(cx, cy, sm2, 0.8):
                    for side in (-1, 1):
                        x0 = int(cx + side * (hw + 4))
                        for xx in range(x0, x0 + side * 9, side):
                            for yy in range(int(cy - hw2) + 1, int(cy + hw2)):
                                if 0 <= xx < CW and P.road[yy * CW + xx] and (yy // 2) % 2 == 0:
                                    put(xx, yy, '#C9C6D8' if yy % 2 else '#B3AFC6')
                    break


def _seg_near(px_: float, py_: float, pts, r: float) -> bool:
    for (x0, y0), (x1, y1) in zip(pts[::4], pts[4::4]):
        if min(x0, x1) - r <= px_ <= max(x0, x1) + r and min(y0, y1) - r <= py_ <= max(y0, y1) + r:
            dx, dy = x1 - x0, y1 - y0
            t = max(0.0, min(1.0, ((px_ - x0) * dx + (py_ - y0) * dy) / max(1e-6, dx * dx + dy * dy)))
            if math.hypot(px_ - x0 - dx * t, py_ - y0 - dy * t) <= r:
                return True
    return False


def _quays(P: CityPlan, put, land):
    """Where the city meets the sea: a dressed coping lit along its top with a yellow
    safety line, the quay's face dark into the water, and the water's dark band beside it."""
    for y in range(1, CH - 1):
        for x in range(1, CW - 1):
            i = y * CW + x
            if land[i] != 1:
                continue
            south = P.water[i + CW]
            east = P.water[i + 1]
            if south:
                put(x, y, NIGHT_[5]); put(x, y - 1, AMBER_[3] if x % 8 < 5 else NIGHT_[4])
                for d in (1, 2):
                    if y + d < CH and P.water[i + d * CW]:
                        put(x, y + d, CONC[1] if d == 1 else SEA_C[0])
                P.blocked[i] = 1
            elif east:
                put(x, y, NIGHT_[4]); put(x - 1, y, AMBER_[3] if y % 8 < 5 else NIGHT_[3])
                put(x + 1, y, CONC[1])
                P.blocked[i] = 1
    for i in range(CN):
        if P.water[i]:
            P.blocked[i] = 1


def _terrace_faces(P: CityPlan, put):
    """The heights' retaining walls: dressed concrete blocks in courses, lit on top, a
    railing along the rim above, rain streaks down the face and a dark foot."""
    for (x, y), (r, fh) in P.face.items():
        i = y * CW + x
        course = r // 5
        joint = (x + course * 7) % 14 == 0
        if r == 0:
            c = CONC[5]
        elif r == fh - 1:
            c = CONC[0]
        elif r % 5 == 0 or joint:
            c = CONC[1]
        else:
            c = CONC[3] if r % 5 == 1 else CONC[2]
        if r > 2 and noise2(x, 0, 1840) > 0.85 and r < 6 + noise2(x, 1, 1840) * 10:
            c = CONC[1]  # a rain streak
        put(x, y, c)
        P.blocked[i] = 1
    for (x, y), (r, fh) in P.face.items():  # the railing along each rim
        if r == 0:
            put(x, y - 1, IRON[2] if x % 6 else IRON[3])
            put(x, y - 3, IRON[3])
            if x % 6 == 0:
                put(x, y - 2, IRON[2])
    for (x0, rim, w) in TERRACE_STAIRS:  # stairs up through the rims, walkable
        for y in range(rim - 4, rim + FACE_H + 3):
            for x in range(x0, x0 + w):
                a, b = x - x0, x0 + w - 1 - x
                if a < 2 or b < 2:
                    c = CONC[4] if a == 1 or b == 0 else CONC[1]
                    P.shut.add((x, y))
                else:
                    k = (y - rim) % 3
                    c = CONC[4] if k == 0 else CONC[3] if k == 1 else CONC[1]
                    if y < rim or y >= rim + FACE_H:
                        c = CONC[3]
                    P.open.add((x, y))
                put(x, y, c)



def _door_aprons() -> list:
    """The ground in front of every building's door (city px), kept clear of furniture."""
    out = []
    for (key, (w, floors, style, seed, shop, setback, blade, *_rest), fx, fy) in city_buildings():
        x0 = fx - w // 2
        if style == 'glass':
            dx = fx
        else:
            dx = x0 + 10 if noise2(seed, 1, 1920) > 0.5 else x0 + w - 10
        out.append((dx - 12, fy - 2, dx + 12, fy + 16))
    return out


def _along(name: str, step: float, offset: float, start: float = 0.0):
    """Points along a street's centre line every `step` px of its length, pushed `offset`
    px to its right (south of an east-west street, west of a north-south one)."""
    sm = LINES[name][0]
    out = []
    nxt = start
    for (x, y, s, dx, dy) in _poly_samples(sm, 1.0):
        if s >= nxt:
            out.append((x - dy * offset, y + dx * offset))
            nxt += step
    return out


@functools.lru_cache(maxsize=1)
def city_props_placed() -> list:
    """Everything that stands in the city, as (id, key, foot x, foot y) in city px:
    the buildings and the skybridges by plan; then by rule, each checked against the
    ground (on a pavement, a quay or a plaza, never in a road, the water, a stair or a
    door's apron, never on another's foot): lamps along both kerbs of every street,
    trees down the avenue, crossing signals at the zebras, vending machines against the
    shop fronts, the market's stalls, the plaza's fountain and tram stop, benches that
    face something, the promenade's kiosks, the docks' cranes, stacks and ship, the
    point's lighthouse, water taxis at the quays."""
    P = city()
    smap = sprites()

    def size(key):
        return smap[key].w, smap[key].h

    out = []
    feet = []
    aprons = _door_aprons()
    tall = []  # each building's sprite box, for the cross-seam check in ok()
    for (key, spec, fx, fy) in city_buildings():
        out.append((key, key, fx, fy))
        w, _h = spec[0], 0
        feet.append((fx - w // 2, fy - 20, fx + w // 2, fy))
        tall.append((fx - w // 2, fy - smap[key].h, fx + w // 2, fy))
    for (key, w, fx, fy, h) in city_skybridges():
        out.append((key, key, fx, fy - h))  # (overhead: drawn raised, its foot on the deck)

    def ok(key, fx, fy, where=('pave',), gap=3):
        w, h = size(key)
        half = max(3, w // 2 - 2)
        if 'tree' in key:
            half = 7  # (a tree stands on its trunk and grate; its crown spreads over the road)
        x0, x1, y0, y1 = int(fx - half), int(fx + half), int(fy - 4), int(fy)
        if x0 < 2 or x1 >= CW - 2 or y0 < 2 or y1 >= CH - 2:
            return False
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1, 2):
                i = y * CW + x
                if P.blocked[i] and 'water' not in where:
                    return False
                if P.road[i] and 'road' not in where:
                    return False
                if P.water[i] and 'water' not in where:
                    return False
                if not P.water[i] and 'water' in where and 'land' not in where:
                    return False
                if (x, y) in P.open or (x, y) in P.face:
                    return False
        box = (x0 - gap, y0 - gap, x1 + gap, y1 + gap)
        if any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1] for b in feet + aprons):
            return False
        # nothing stands behind a building that rises over a zone's north edge from the
        # zone in front (zones.check_overhangs: its top would cover it across the seam)
        sx0, sx1, sy0 = fx - w // 2, fx + w // 2, fy - h
        for (bx0, by0, bx1, by1) in tall:
            if by1 // H != int(fy - 2) // H and sx0 < bx1 and sx1 > bx0 and sy0 < by1 and fy > by0:
                return False
        return True

    def put(oid, key, fx, fy, where=('pave',), gap=3):
        if ok(key, fx, fy, where, gap):
            w, h = size(key)
            if 'tree' in key:
                w = 18
            feet.append((int(fx - w // 2 + 2), int(fy - 4), int(fx + w // 2 - 2), int(fy)))
            out.append((oid, key, int(fx), int(fy)))
            return True
        return False

    n = 0
    # the tram waits at its stop (placed first, so nothing stands in the road under it)
    tx, ty = TRAM_END + 64, int(street_y('hill', TRAM_END + 64)) + 6
    out.append(('tram-car', 'city_tram', tx, ty))
    feet.append((tx - 56, ty - 40, tx + 56, ty + 22))
    # lamps along both kerbs of the graded streets, staggered
    for (name, line, hw, pw, grade) in STREETS:
        if grade != 1 or name == 'harbour':
            continue
        for side, start in ((1, 20), (-1, 52)):
            for (x, y) in _along(name, 64, side * (hw + 4), start):
                pcx, pcy, prx, pry = PLAZA
                if ((x - pcx) / prx) ** 2 + ((y - pcy) / pry) ** 2 < 1.1:
                    continue  # (the square is lit by its own lamps round its edge)
                if put(f'lamp-{n}', 'city_lamp', x, y):
                    n += 1
    # the avenue's trees, between the lamps
    for side, start in ((1, 4), (-1, 36)):
        for (x, y) in _along('avenue', 64, side * (LINES['avenue'][1] + 8), start):
            if put(f'tree-{n}', 'city_street_tree' if n % 2 else 'city_street_tree_b', x, y, gap=6):
                n += 1
    for side, start in ((1, 10), (-1, 42)):
        for (x, y) in _along('towerrow', 72, side * (LINES['towerrow'][1] + 8), start):
            if put(f'tree-{n}', 'city_street_tree_b' if n % 2 else 'city_street_tree', x, y, gap=6):
                n += 1
    # vending machines against the shop fronts, a bin beside some lamps
    for k, (key, spec, fx, fy) in enumerate(city_buildings()):
        if spec[2] != 'glass' and noise2(k, 0, 1980) > 0.45:
            x = fx + (spec[0] // 2 - 16) * (1 if noise2(k, 1, 1980) > 0.5 else -1)
            put(f'vend-{n}', ('city_vending_box', 'city_vending_box_b', 'city_vending_box_c')[k % 3], x, fy + 6)
            n += 1
    for (oid, key, x, y) in list(out):
        if key == 'city_lamp' and noise2(int(x), int(y), 1981) > 0.6:
            put(f'bin-{n}', 'city_litter_bin', x + 12, y)
            n += 1
    # street life (to-c-city-review 4; review 15:54, Eastward): cars parked at the kerbs of
    # the roads that keep their traffic, away from the crossings; steam from a grate by
    # some shopfronts, bikes racked by others, a cat on a doorstep; food carts where
    # people walk
    cars = ('city_car', 'city_car_b', 'city_car_c', 'city_car_d', 'city_car_e')

    def clear_of_junctions(x, y):
        for nm in ('avenue', 'towerrow', 'quayroad'):
            sm2 = LINES[nm][0]
            if min(p[1] for p in sm2) - 30 <= y <= max(p[1] for p in sm2) + 30 and abs(x - street_x(nm, y)) < 46:
                return False
        return True
    for nm, start in (('hill', 28), ('cable', 18), ('cable_e', 22), ('market', 40)):
        hw_ = LINES[nm][1]
        for (x, y) in _along(nm, 58, hw_ - 3, start):
            if nm == 'market' and x < PED_MARKET_X + 30:
                continue
            if nm == 'hill' and x > TRAM_END - 30:
                continue
            if clear_of_junctions(x, y) and noise2(int(x), 0, 1987) > 0.25:
                if put(f'car-{n}', cars[n % 5], x, y, where=('road',), gap=4):
                    n += 1
    for (x, y) in _along('quayroad', 130, -(LINES['quayroad'][1] - 3), 30):
        if 120 < y < 1300 and clear_of_junctions(x + 200, y) and put(f'car-{n}', cars[n % 5], x, y, where=('road',), gap=4):
            n += 1
    for k, (key, spec, fx, fy) in enumerate(city_buildings()):
        w_, style_, seed_ = spec[0], spec[2], spec[3]
        x0 = fx - w_ // 2
        dx = fx if style_ == 'glass' else (x0 + 10 if noise2(seed_, 1, 1920) > 0.5 else x0 + w_ - 10)
        r = noise2(k, 7, 1980)
        if r > 0.78:
            put(f'steam-{n}', 'city_steam', (x0 + 8) if dx > fx else (x0 + w_ - 8), fy + 7, gap=1)
        elif r > 0.6 and w_ >= 64:
            put(f'bikes-{n}', 'city_bike_rack', (x0 + 26) if dx > fx else (x0 + w_ - 26), fy + 8, gap=1)
        elif r < 0.12:
            put(f'cat-{n}', ('city_cat', 'city_cat_b', 'city_cat_c')[k % 3], dx + 18, fy + 3, gap=0)
        n += 1
    put('cart-q', 'city_food_cart', QUAY_X - 26, 250, gap=4)
    # the night market: stalls along Market Street's pedestrian stretch
    # (down the middle of the setts, a row of stalls with the walk on either side, as
    # night markets lay them out; the shopfronts behind stay clear)
    for (x, y) in _along('market', 70, 4, 20):
        if x < PED_MARKET_X - 20 and put(f'stall-{n}', ('city_market_stall', 'city_market_stall_b', 'city_market_stall_c',
                                                        'city_market_stall_d')[n % 4], x, y, gap=2):
            n += 1
    # the pocket parks: two trees and a bench on each, the bench by the path
    for k, ((x0, y0, x1, y1), core) in enumerate(P.lots):
        spots = sorted(core, key=lambda c: noise2(c[0], c[1], 1838 + k))
        placed = 0
        for (cx, cy) in spots:
            key = 'city_tree_planted' if placed < 2 else 'city_bench'
            if put(f'park-{k}-{placed}', key, cx * 4 + 2, cy * 4 + 2, gap=6):
                placed += 1
            if placed == 3:
                break
    # the lookout at the top of the stepped street: a bench facing south over the city, a
    # coin telescope at the rail
    put('look-bench', 'city_bench', LOOKOUT[0] + 16, 46, where=('pave',), gap=2)
    put('look-scope', 'city_telescope', LOOKOUT[1] - 14, 52, where=('pave',), gap=2)
    for k, x in enumerate(range(60, PED_MARKET_X - 20, 37)):  # food carts between the stalls
        if put(f'cart-{k}', 'city_food_cart_b' if k % 2 else 'city_food_cart', x, int(street_y('market', x)) + 4, gap=1):
            pass
    # the plaza: the fountain at its heart, the tram stop on Hill Street, benches round
    # the fountain facing it, trees in its corners
    pcx, pcy, prx, pry = PLAZA
    put('fountain', 'city_fountain', pcx, pcy + 20, where=('pave', 'plaza'))
    for k, (ax, ay) in enumerate(((-58, 18), (58, 18), (-40, 52), (40, 52))):
        put(f'bench-p{k}', 'city_bench', pcx + ax, pcy + ay + 20, where=('pave', 'plaza'))
    for k in range(10):  # lamps round the square's edge
        a = math.pi * (0.1 + 0.8 * k / 9)
        put(f'lamp-sq{k}', 'city_lamp', pcx + math.cos(a + math.pi) * (prx - 6) * -1, pcy + math.sin(a) * (pry - 4),
            where=('pave', 'plaza'), gap=2)
    # the tram (review 15:54, finding 1): its rails come along Hill Street from the
    # waterfront to a buffer at the square's edge; the shelter stands on the square's
    # paving by the buffer, its back to the fountain; a tram waits at the stop
    put('tram', 'city_tram_stop', PLAZA[0] + 82, PLAZA[1] + 14, where=('pave', 'plaza'), gap=2)
    # the promenade along the east quay: benches looking at the sea, kiosks, taxis moored
    for k, y in enumerate(range(80, 560, 96)):
        put(f'bench-q{k}', 'city_bench', QUAY_X - 14, y, gap=6)
    for k, y in enumerate(range(118, 560, 96)):
        put(f'tree-q{k}', 'city_street_tree' if k % 2 else 'city_street_tree_b', QUAY_X - 16, y, gap=4)
    for k, y in enumerate((150, 420)):
        put(f'kiosk-{k}', 'city_food_kiosk' if k else 'city_food_kiosk_b', QUAY_X - 44, y, gap=4)
    # the docks: cranes on the quay apron, containers on the yard, the ship alongside
    for k, y in enumerate((760, 960)):
        out.append((f'crane-{k}', 'city_gantry_crane', DOCK_X - 20, y))
    k = 0
    for y in range(916, 1110, 50):  # the container yard behind the cranes: stacks in a row, as a port lays them out
        for x in (684,):
            kind = ('city_container_stack', 'city_container_stack_b', 'city_container_stack_c', 'city_container_stack_d')[
                int(noise2(x, y, 1985) * 4)]
            if put(f'boxes-{k}', kind, x + int(noise2(y, x, 1986) * 6) - 3, y, gap=1):
                k += 1
    for k, (x, y) in enumerate(((664, 1210), (700, 1330), (668, 1460), (724, 1560))):  # the point's promenade
        put(f'tree-pt{k}', 'city_street_tree' if k % 2 else 'city_street_tree_b', x, y, gap=6)
    for k, (x, y) in enumerate(((690, 1260), (650, 1520))):
        put(f'bench-pt{k}', 'city_bench', x, y, gap=6)
    put('kiosk-pt', 'city_food_kiosk', 700, 1400, gap=4)
    for k, y in enumerate(range(1190, 1600, 90)):
        put(f'lamp-pt{k}', 'city_lamp', 742, y)
    out.append(('ship', 'city_cargo_ship', DOCK_X + 44, 1060))
    # the point: the lighthouse on its rock, bollards on the breakwater, taxis at the quays
    out.append(('lighthouse', 'city_lighthouse', 908, 1676))
    for k, x in enumerate(range(40, 740, 90)):
        put(f'bollard-{k}', 'city_quay_bollard', x, HARBOUR_Y - 6, gap=6)
    # the old core south of Harbour Road: noodle stalls and vending machines, the court
    for k, (x, key) in enumerate(((40, 'noodle_stall'), (112, 'city_market_stall_c'), (236, 'city_market_stall_b'))):
        put(f'noodle-{k}', key, x, 1452, where=('pave', 'plaza'))
    for k, x in enumerate((176, 290)):
        put(f'vend-core-{k}', 'city_vending_box_b' if k else 'city_vending_box', x, 1420)
    out.append(('taxi-1', 'city_water_taxi', 120, HARBOUR_Y + 30))
    out.append(('taxi-2', 'city_water_taxi', QUAY_X + 40, 300))
    return out



def _city_objects(zone: str) -> list:
    """This zone's share of the city's props (those whose foot stands in it), as the zones'
    lists give them (before each sprite's own offset)."""
    import style as _st
    col, row = CITY[zone]
    ox, oy = col * W, row * H
    smap = sprites()
    objs = []
    for (oid, key, fx, fy) in city_props_placed():
        if ox <= fx < ox + W and oy <= fy - 2 < oy + H:
            sp = smap[key]
            objs.append((oid, key, fx - ox - sp.w // 2 - sp.ox, fy - oy - sp.h - sp.oy))
    return objs


def _city_cut(zone: str):
    P = city()
    col, row = CITY[zone]
    ox, oy = col * W, row * H
    cv = Canvas(W, H)
    cv.img.paste(P.cv.img.crop((ox, oy, ox + W, oy + H)), (0, 0))
    cv.img.alpha_composite(P.over.img.crop((ox, oy, ox + W, oy + H)))
    water, blocked = set(), set()
    for y in range(H):
        base = (y + oy) * CW + ox
        for x in range(W):
            if P.water[base + x]:
                water.add((x, y))
            if P.blocked[base + x] and (x + ox, y + oy) not in P.open:
                blocked.add((x, y))
    blocked |= {(x - ox, y - oy) for (x, y) in P.shut if ox <= x < ox + W and oy <= y < oy + H}
    return cv, water, blocked


CITY_STANDS = {
    'heights': {'lookout': (150, 60), 'terrace': (150, 196), 'hill': (220, 300)},
    'plaza': {'fountain': (160, 400), 'tram': (298, 310), 'hill': (10, 300)},
    'waterfront': {'promenade': (140, 300), 'plaza': (10, 322), 'kiosk': (116, 180)},
    'market': {'avenue': (156, 300), 'stalls': (60, 330), 'downtown': (300, 296)},
    'downtown': {'towers': (160, 296), 'market': (10, 296), 'docks': (310, 304)},
    'docks': {'cranes': (110, 300), 'downtown': (10, 304), 'quay': (130, 500)},
    'point': {'lighthouse': (250, 470), 'quay': (100, 120)},
    'neon': {'crossing': (160, 192), 'stalls': (60, 330), 'court': (160, 382), 'quay': (160, 452)},
}


def _city_zone(zone: str, fn_name: str):
    cv, water, blocked = _city_cut(zone)
    WATER_MASKS[fn_name] = water
    return cv, _city_objects(zone), dict(CITY_STANDS[zone]), blocked


def city_heights(frame: int = 0):
    """The Heights: the old town on the hill above Hill Street, its terraces held up by
    concrete walls and climbed by the avenue's stairs, houses on each terrace looking
    south over the city, a lookout at the top."""
    return _city_zone('heights', 'city_heights')


def city_plaza(frame: int = 0):
    """The Plaza: the city's square, where Hill Street meets Tower Row, paved in rings of
    pale granite round a fountain; the tram stops at its east side."""
    return _city_zone('plaza', 'city_plaza')


def city_waterfront(frame: int = 0):
    """The Waterfront: Hill Street runs down to the promenade along the east quay, with
    benches looking at the sea, food kiosks and a water taxi waiting."""
    return _city_zone('waterfront', 'city_waterfront')


def city_market(frame: int = 0):
    """The Market: the avenue between Hill Street and the old core, stalls along Market
    Street's south pavement under striped canopies, walk-ups with blade signs."""
    return _city_zone('market', 'city_market')


def city_downtown(frame: int = 0):
    """Downtown: the tallest towers, standing on Market Street and the terminal walk,
    joined across Tower Row by a skybridge."""
    return _city_zone('downtown', 'city_downtown')


def city_docks(frame: int = 0):
    """The Docks: the quay road along the east quay, container cranes on the apron, a
    cargo ship alongside, stacks of containers on the yard."""
    return _city_zone('docks', 'city_docks')


def city_point(frame: int = 0):
    """The Point: where the east quay turns into the harbour, a breakwater out to the
    lighthouse on its rock."""
    return _city_zone('point', 'city_point')


def city_neon(frame: int = 0):
    """Neon Harbour's old core, at the foot of the avenue: Harbour Road with its crossing,
    walk-ups along its north side, noodle stalls and vending machines on the south side,
    the neon-ringed court for sparring, the quay and the dark harbour with water taxis."""
    return _city_zone('neon', 'city_neon')

"""Cogsworth and the city: the junction and the canal, Neon Harbour and the skyport.

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['junction', 'canal', 'neon_city', 'skyport', 'grate', 'gear_ring']


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
    def square_edge(x):  # a gently curving edge, drawn back a little at the sides
        side = max(0, 30 - x, x - 290) / 30
        return 420 + int(math.sin(x / 41) * 5 + smooth_noise(x, 0, 23, 152) * 10 - side * 14)
    square = {(x, y) for x in range(W) for y in range(136, 436) if y < square_edge(x)}
    lane = worlds.thick([(160, 430), (160, 468)], 16)
    spur = worlds.thick([(150, 504), (128, 506)], 7)  # the short way off the lane into the ring
    worlds.paint_cobbles(cv, square | lane)
    for (x, y) in square | lane:  # a kerb of dressed stone where the cobbles meet the grass
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
        # the far side of the line: chimneys and pipes over the wall
        ('ws-far-1', 'workshop_round', 10, -26), ('ws-far-2', 'workshop', 200, -24),
        ('pipes-far', 'pipe_run', 104, 48),
        # the train at the platform, steam from its stack
        ('engine', 'locomotive', 96, 43), ('puff-engine', 'steam_puff', 112, 26),
        # the platform
        ('lamp-p1', 'gas_lamp', 40, 92), ('lamp-p2', 'gas_lamp', 264, 92), ('bench-p', 'iron_bench', 208, 104),
        ('trunk-p1', 'steamer_trunk', 14, 112), ('trunk-p2', 'steamer_trunk', 30, 118), ('coal-p', 'coal_cart', 284, 110),
        # the square
        ('ws-left', 'workshop', 4, 150), ('ws-right', 'workshop_f1', 222, 166),
        ('tower', 'clock_tower', 136, 176),
        ('lamp-s1', 'gas_lamp', 112, 280), ('lamp-s2', 'gas_lamp', 196, 280),
        ('gears-1', 'gear_pile', 96, 228), ('pipes-1', 'pipe_run', 236, 252),
        ('puff-c1', 'steam_puff', 66, 132), ('puff-c2', 'steam_puff', 282, 132),
        ('ws-low', 'workshop_round', 6, 320), ('coal-1', 'coal_cart', 90, 384),
        ('trunk-2', 'steamer_trunk', 280, 396),
        ('puff-v3', 'steam_puff', 206, 352), ('kiosk', 'tea_kiosk', 250, 300),
        # round the ring
        ('lamp-r1', 'gas_lamp', 128, 466), ('bench-r', 'iron_bench', 52, 446),
        ('mast', 'airship_mast', 206, 392),
    ]
    stands = {'platform': (160, 120), 'tower': (160, 322), 'ring': (80, 508), 'workshop': (52, 248),
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
        ('wh-1', 'workshop_round', 20, 22), ('wh-2', 'workshop_f2', 200, 34),
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
        ('wires', 'cables', 10, 96), ('bikes', 'bike_rack', 170, 300), ('bikes-2', 'bike_rack', 176, 440),
    ]
    for (gx, gy) in ((112, 336), (232, 300), (60, 440)):  # steam grates in the pavement
        grate(cv, gx, gy)
    stands = {'crossing': (160, 192), 'stalls': (60, 300), 'court': (160, 382), 'quay': (160, 452)}
    water = {(x, y) for x in range(W) for y in range(470, H)}
    WATER_MASKS['neon_city'] = water
    return cv, objects, stands, water  # the harbour is water: no walking on it


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
    # a compass rose inlaid in the concourse floor, pointing the way up
    MX, MY = 140, 300
    for (x, y) in oval(MX, MY, 44, 22):
        d = math.hypot((x - MX) / 44, (y - MY) / 22)
        a = math.atan2((y - MY) * 2, x - MX)
        star = d < 0.95 * (0.35 + 0.65 * abs(math.cos(2 * a)) ** 6)  # four long points
        if 0.9 < d < 0.96 or 0.55 < d < 0.58:
            cv.set(x, y, CYAN[2] if (x + y) % 2 else CYAN[1])
        elif star:
            cv.set(x, y, PORC[5] if (x - MX) * 0.3 + (y - MY) < 0 else PORC[3])
        elif d < 0.9:
            cv.set(x, y, PORC[2] if (x // 3 + y // 3) % 2 else PORC[1])
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
                                  (140, 300, 52, 26, CYAN[4]), (40, 410, 34, 12, AMBER[3]), (150, 420, 34, 12, AMBER[3]),
                                  (LX, LY, 40, 24, AMBER[3]), (AX, 400, 30, 60, CYAN[3])):
        light_pool(cv, lx, ly, rx, ry, col, skip=frozenset(water - ring - pier))
    blocked |= water - ring - pier
    WATER_MASKS['skyport'] = water - ring - pier
    objects = [
        ('maglev', 'maglev', 26, 26), ('pylon-p', 'departure_pylon', 160, 40), ('light-p', 'street_light', 30, 40),
        ('tree-loop', 'pod_tree', LX - 18, LY - 40), ('tree-1', 'pod_tree', 280, 236), ('tree-2', 'pod_tree', 4, 236),
        ('pylon-1', 'departure_pylon', 60, 240), ('pylon-2', 'departure_pylon', 180, 240),
        ('gates', 'ticket_gates', 64, 316), ('bench-1', 'sky_bench', 14, 400), ('bench-2', 'sky_bench', 124, 400),
        ('tree-3', 'pod_tree', 176, 372), ('tree-4', 'pod_tree', 284, 380), ('bot-1', 'luggage_bot', 120, 440),
        ('bot-2', 'luggage_bot', 200, 300), ('tether', 'tether', AX - 20, AY - 254),
        ('drone-1', 'drone', 120, 140), ('drone-2', 'drone', 290, 300),
        ('kiosk', 'flower_kiosk', 244, 106), ('planter-1', 'sky_planter', 40, 424), ('planter-2', 'sky_planter_b', 160, 424),
    ]
    stands = {'neon': (10, 192), 'platform': (70, 84), 'gates': (104, 360), 'anchor': (AX, AY + 14)}
    return cv, objects, stands, blocked

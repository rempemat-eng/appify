"""Halcyon Station in orbit and Lumen on the moon, with the moon's plain beyond.

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['station', 'lumen', 'beyond_regolith']


def station(frame: int = 0):
    """Halcyon Station: the space elevator arrives through the airlock at the bottom into
    a hall of hydroponic troughs; through a bulkhead door the corridor runs up past the
    low-gravity ring and the garden pods of the atrium; the crew's sleep pods and
    lockers stand on soft carpet in the west bay, the galley (warm deck boards, a round
    table, tea) and the navigation consoles in the east, with the shuttle hatch to
    Lumen in the east wall; through the last bulkhead, the lounge under the long
    viewports, with benches, books and a telescope on the planet turning below. The
    hull is closed: Lumen is reached by shuttle, never on foot."""
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
    NAPm, WOODm = MATERIALS['nap'], MATERIALS['wood']
    blocked = {(x, y) for y in range(H) for x in list(range(0, 18)) + list(range(W - 18, W))}  # the hull
    # the observation lounge under the viewports: a round rug, starlight on the deck
    for (x, y) in oval(160, 124, 92, 22):
        d = math.hypot((x - 160) / 92, (y - 124) / 22)
        cv.set(x, y, NAPm[1] if d > 0.9 else NAPm[2] if (d * 10) % 2 < 1 else NAPm[1])
    for i in range(40):
        x, y = 20 + int(noise2(i, 0, 352) * 280), 82 + int(noise2(i, 1, 352) * 20)
        cv.set(x, y, HULL[4])  # starlight caught on the plates
    # the sleep bay: soft carpet, quiet
    for y in range(180, 462):
        for x in range(18, 104):
            n = noise2(x // 2, y // 2, 353)
            cv.set(x, y, NAPm[1] if n > 0.5 else '#3E3560')
            if x == 103:
                cv.set(x, y, NAPm[3])
    # the galley: warm deck boards
    for y in range(180, 320):
        for x in range(216, W - 18):
            c = WOODm[3] if (y // 6) % 2 else WOODm[2]
            if y % 6 == 0 or (x + (y // 6) * 13) % 37 == 0:
                c = WOODm[1]
            if x == 216:
                c = WOODm[4]
            cv.set(x, y, c)
    # bulkheads between the rooms, each with a lit doorway
    for by in (160, 470):
        for y in range(by, by + 10):
            for x in range(18, W - 18):
                if 136 <= x < 184:
                    continue
                c = HULL[4] if y == by else HULL[3] if y < by + 3 else HULL[1]
                if (x - 18) % 40 == 0:
                    c = HULL[0]
                cv.set(x, y, c)
                blocked.add((x, y))
        for y in range(by - 2, by + 12):
            cv.set(135, y, CYAN[3]); cv.set(184, y, CYAN[3])
    # a soft violet runner down the corridor (the station keeps quiet hours)
    for (y0, y1) in ((330, 470), (480, 512)):
        for y in range(y0, y1):
            for x in range(146, 174):
                cv.set(x, y, NAPm[1] if (x in (146, 173)) else NAPm[2] if (y // 2 + x // 2) % 2 else NAPm[1])
        for y in range(y0, y1):
            for x in (140, 179):
                cv.set(x, y, CYAN[3] if (y // 3 + frame) % 4 else CYAN[2])
    for x in range(126, 194):  # hazard stripes before the elevator's airlock
        for y in range(506, 514):
            cv.set(x, y, '#E8C04A' if ((x + y) // 4) % 2 else '#2A2630')
    # the low-gravity ring on the atrium floor
    ccx, ccy = 160, 300
    for k in range(260):
        a = 2 * math.pi * k / 260
        for (rx, ry) in ((64, 30), (50, 23)):
            x, y = int(ccx + rx * math.cos(a)), int(ccy + ry * math.sin(a))
            cv.set(x, y, CYAN[3]); cv.set(x, y + 1, CYAN[1])
    for (x, y) in oval(ccx, ccy, 10, 5):
        cv.set(x, y, CYAN[2] if (x + y) % 2 else CYAN[1])
    objects = [
        ('view-1', 'viewport', 20, 8), ('view-2', 'viewport', 140, 8), ('view-3', 'viewport', 200, 8),
        # the lounge
        ('shelf', 'bookshelf', 22, 104), ('bench-1', 'lounge_bench', 74, 120), ('bench-2', 'lounge_bench', 194, 120),
        ('scope', 'telescope', 262, 98),
        # the atrium and its gardens
        ('pod-1', 'garden_pod', 128, 180), ('pod-2', 'garden_pod', 178, 372),
        # the sleep bay
        ('sleep-1', 'sleep_pod', 24, 186), ('sleep-2', 'sleep_pod', 24, 246), ('sleep-3', 'sleep_pod', 24, 306),
        ('sleep-4', 'sleep_pod', 64, 186), ('lockers', 'lockers', 30, 410),
        # the galley, the shuttle hatch and the navigation consoles
        ('table', 'galley_table', 236, 240), ('tea', 'tea_dispenser', 280, 186), ('trough-g', 'hydro_trough', 226, 186),
        ('lock-shuttle', 'airlock', 262, 330), ('console-1', 'console', 226, 440), ('console-2', 'console', 268, 440),
        # the arrival hall: hydroponics either side
        ('aquarium', 'aquarium_column', 110, 380), ('crates', 'cargo_crates', 196, 330), ('cushions', 'floor_cushions', 68, 360),
        ('trough-1', 'hydro_trough', 22, 492), ('trough-2', 'hydro_trough', 22, 530), ('trough-3', 'hydro_trough', 242, 492),
        ('trough-4', 'hydro_trough', 242, 530), ('lock-lift', 'airlock', 132, 516),
    ]
    stands = {'lift': (160, 500), 'atrium': (160, 300), 'viewport': (160, 144), 'sleep': (84, 280),
              'galley': (256, 296), 'shuttle': (290, 392)}
    return cv, objects, stands, blocked


def lumen(frame: int = 0):
    """Lumen, the quiet moon and the deepest rest: pale regolith under a black sky with
    the planet rising over a far ridge. The shuttle sits on a scorched pad at the top;
    a winding line of footprints leads down past boulders with hard airless shadows,
    bright-rayed craters and a sinuous rille, by a ring of crystals round a small
    crater (gentle sparring), to the Dream Grove: a wide crater whose floor is carpeted
    in glowing moss round the sleeping tree, with dream pools holding the stars, little
    glowing caps, and a hammock slung between two crystal spires."""
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
    for x in range(W):  # a far ridge along the horizon, in shade
        top = horizon(x) - 6 - int(abs(math.sin(x / 37)) * 10 + noise2(x // 4, 1, 366) * 4)
        for y in range(max(0, top), horizon(x)):
            d = math.hypot(x - 230, y - 150)
            if d >= 117 or y > 40:
                cv.set(x, y, R[1] if y > top + 1 else R[2])
    # a rille: a winding collapsed channel across the west
    rille = worlds.thick([(-6, 210), (40, 230), (60, 290), (30, 350), (-6, 380)], 7, seed=367)
    for (x, y) in rille:
        lit = (x - 1, y) not in rille or (x, y - 1) not in rille
        cv.set(x, y, R[1] if not lit else R[4])
    for (x, y) in rille:
        if (x + 1, y) not in rille and (x + 2, y) not in rille:
            cv.set(x + 1, y, R[5])
    def crater(cx, cy, r, rays=False):
        if rays:  # bright ejecta rays across the dust
            for k in range(9):
                a = 2 * math.pi * k / 9 + 0.3
                for t in range(int(r * 1.1), int(r * (2.4 + noise2(k, 0, 368)))):
                    x, y = int(cx + math.cos(a) * t), int(cy + math.sin(a) * t * 0.6)
                    if (x + y) % 3 and 0 <= x < W and 0 <= y < H and y > 80:
                        cv.set(x, y, R[4])
        for (x, y) in oval(cx, cy, r, r * 0.6):
            dx, dy = (x - cx) / r, (y - cy) / (r * 0.6)
            d = math.hypot(dx, dy)
            t = dx * 0.7 + dy * 0.7  # toward the lower right
            if d < 0.8:  # the bowl: its far wall in shade, its near wall catching the light
                v = 1.6 + t * 1.8 + (0.3 if (x + y) % 2 else 0)
            else:  # the raised rim: lit on its upper-left outside, shaded lower right
                v = 3.4 - t * 2.2 + (0.3 if (x + y) % 2 else 0)
            cv.set(x, y, R[max(0, min(5, int(v)))])
    for (cx, cy, r, rays) in ((54, 130, 18, True), (270, 96, 10, False), (296, 380, 12, False), (40, 470, 9, False),
                              (120, 250, 8, False), (210, 150, 6, False), (280, 560, 14, True),
                              (130, 556, 7, False), (306, 236, 6, False), (196, 352, 5, False), (24, 330 - 20, 4, False)):
        crater(cx, cy, r, rays)
    # the shuttle's pad: a ring scorched into the dust
    for (x, y) in oval(160, 126, 50, 16):
        d = math.hypot((x - 160) / 50, (y - 126) / 16)
        if d > 0.55 and (x + y) % 2:
            cv.set(x, y, R[1] if d < 0.8 else R[2])
    # the sparring crater with its ring of crystals
    crater(236, 262, 34)
    # the Dream Grove: a wide crater carpeted in glowing moss
    GX, GY, GRX, GRY = 168, 452, 104, 58
    for (x, y) in oval(GX, GY, GRX, GRY):
        d = math.hypot((x - GX) / GRX, (y - GY) / GRY)
        t = ((x - GX) / GRX + (y - GY) / GRY) * 0.7
        if d > 0.86:  # its rim
            v = 3.4 - t * 2.2 + (0.3 if (x + y) % 2 else 0)
            cv.set(x, y, R[max(0, min(5, int(v)))])
            continue
        n = smooth_noise(x, y, 7, 369)
        c = GLOWm[1] if n > 0.45 else GLOWm[0]
        if n > 0.72 or (n > 0.66 and (x + y) % 2):
            c = GLOWm[2]
        if d > 0.76 and (x + y) % 2:
            c = R[2]  # the moss thinning toward the rim
        cv.set(x, y, c)
    for i in range(60):  # moss sparkles
        x, y = GX + int((noise2(i, 0, 370) - 0.5) * GRX * 1.5), GY + int((noise2(i, 1, 370) - 0.5) * GRY * 1.5)
        if math.hypot((x - GX) / GRX, (y - GY) / GRY) < 0.7:
            cv.set(x, y, GLOWm[4] if i % 3 == 0 else GLOWm[3])
    light_pool(cv, GX, GY + 10, 90, 44, GLOWm[3])
    # footprints from the shuttle, winding down past it all to the grove
    pts = [(160, 150), (176, 200), (150, 250), (130, 300), (170, 340), (164, 392)]
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        steps = int(math.hypot(x1 - x0, y1 - y0) / 7)
        for k in range(steps):
            x = int(x0 + (x1 - x0) * k / steps) + (3 if (k + i) % 2 else -3)
            y = int(y0 + (y1 - y0) * k / steps)
            cv.set(x, y, R[1]); cv.set(x + 1, y, R[1]); cv.set(x, y + 1, R[2])
    # the old lander's tracks: it rolled a little way on its feet before it stopped
    for track in ([(318, 372), (296, 376), (276, 362)], [(254, 358), (226, 372), (204, 362)]):
        for side in (0, 6):
            for i in range(len(track) - 1):
                (x0, y0), (x1, y1) = track[i], track[i + 1]
                n = int(math.hypot(x1 - x0, y1 - y0))
                for k in range(0, n, 2):
                    x, y = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n + side
                    cv.set(x, y, R[1]); cv.set(x, y + 1, R[4])
    objects = [
        ('shuttle', 'shuttle', 118, 72), ('lander', 'old_lander', 246, 322), ('arch', 'moon_arch', 196, 524),
        ('rock-7', 'moon_rock', 20, 420), ('rock-8', 'moon_rock_small', 50, 434), ('rock-9', 'moon_rock_small', 104, 206),
        ('rock-1', 'moon_rock', 26, 180), ('rock-2', 'moon_rock_small', 230, 200), ('rock-3', 'moon_rock', 278, 300),
        ('rock-4', 'moon_rock_small', 80, 330), ('rock-5', 'moon_rock_small', 290, 470), ('rock-6', 'moon_rock', 14, 540),
        ('crystal-1', 'moon_crystal', 196, 228), ('crystal-2', 'moon_crystal', 262, 236), ('crystal-3', 'moon_crystal', 200, 276),
        ('crystal-4', 'moon_crystal', 262, 280), ('crystal-5', 'moon_crystal', 214, 112), ('crystal-6', 'moon_crystal', 90, 150),
        ('shrub-1', 'moon_shrub', 30, 260), ('shrub-2', 'moon_shrub', 280, 150), ('shrub-3', 'moon_shrub', 96, 380),
        ('shrub-4', 'moon_shrub', 240, 380),
        # the Dream Grove
        ('tree', 'moon_tree', GX - 38, GY - 82), ('hammock', 'hammock', GX - 112 + 30, GY - 6),
        ('pool-1', 'dream_pool', GX + 40, GY + 6), ('pool-2', 'dream_pool', GX - 30, GY + 28),
        ('caps-1', 'glow_caps', GX + 14, GY + 30), ('caps-2', 'glow_caps', GX - 70, GY - 30), ('caps-3', 'glow_caps', GX + 64, GY - 24),
        ('shrub-5', 'moon_shrub', GX + 74, GY + 10), ('shrub-6', 'moon_shrub', GX - 96, GY + 20),
    ]
    for (_i, key, x, y) in objects:  # the flora's glow on the dust
        if key == 'moon_shrub':
            light_pool(cv, x + 17, y + 32, 26, 12, GLOWm[1])
    stands = {'shuttle': (160, 146), 'sparring': (236, 262), 'grove': (168, 410), 'hammock': (118, 496),
              'rille': (80, 300)}
    return cv, objects, stands


def beyond_regolith() -> Canvas:
    """What lies round Lumen below its horizon: the moon's grey plain running on, soft
    dust in two tones, small craters lit on their far rims, a few stones."""
    S = BEYOND_SPILL
    R = MATERIALS['regolith']
    cv = Canvas(W + 2 * S, H + 2 * S)
    for y in range(S, H + S):
        for x in range(S, W + S):
            n = smooth_noise(x, y, 26, 871)
            cv.set(x, y, R[3] if n > 0.55 else R[2] if n > 0.3 or (x + y) % 2 else R[1])
    for i in range(16):
        cx, cy = S + int(noise2(i, 0, 872) * W), S + int(noise2(i, 1, 872) * H)
        r = 4 + noise2(i, 2, 872) * 10
        for (x, y) in oval(cx, cy, r, r * 0.6):
            if S <= x < W + S and S <= y < H + S:
                d = (x - cx) + (y - cy) * 1.6
                cv.set(x, y, R[1] if d < 0 else R[4] if d > r * 0.9 else R[2])
    return cv

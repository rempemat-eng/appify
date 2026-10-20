"""Halcyon Station in orbit and Lumen on the moon, with the moon's plain beyond.

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['station', 'lumen', 'beyond_regolith', 'LUMEN_HUB', 'LUMEN_DOME', 'LUMEN_WALL']


def station(frame: int = 0):
    """Halcyon Station: the space elevator arrives through the airlock at the bottom into
    a hall of hydroponic troughs; through a bulkhead door the corridor runs up past the
    low-gravity ring and the garden pods of the atrium; the crew's sleep pods and
    lockers stand on soft carpet in the west bay, the galley (warm deck boards, a round
    table, tea) and the navigation consoles in the east, with the shuttle hatch to
    Lumen in the east wall; through the last bulkhead, the lounge under the long
    viewports, with benches, books and a telescope on the planet turning below. The
    hull is closed: Lumen is reached by shuttle, never on foot. It is a pressure vessel:
    ring frames hold the hull against the air inside, the windows look out on the planet
    and the station's own solar wing, the plants grow in hydroponic troughs and pods
    under lamps, and nothing ever falls from its ceiling (no weather, no rain)."""
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
    # the pressure hull on both sides, seen from inside: the outer skin, ring frames
    # every few paces holding it against the air inside, quilted insulation between
    # them, a run of coolant and air pipes on brackets, and a light strip at the foot
    for (x0, x1) in ((0, 18), (W - 18, W)):
        inner = x1 - 1 if x0 == 0 else x0
        for y in range(H):
            frame = y % 48 < 4
            for x in range(x0, x1):
                k = (x - x0) if x0 == 0 else (x1 - 1 - x)  # 0 at the outer skin, 17 at the inside
                if k < 3:
                    c = HULL[0] if k == 0 else HULL[1]  # the skin
                elif frame:
                    c = HULL[4] if y % 48 == 0 else HULL[3] if y % 48 < 3 else HULL[1]  # a ring frame
                elif 9 <= k <= 11:
                    c = HULL[3] if k == 9 else HULL[2] if k == 10 else HULL[1]  # the pipe run
                    if y % 16 == 8:
                        c = HULL[0]  # a bracket
                else:
                    c = HULL[2] if ((y // 6) + (k // 3)) % 2 else '#384056'  # quilted insulation
                    if k in (3, 8, 12, 16):
                        c = HULL[1]
                cv.set(x, y, c)
            cv.set(inner, y, CYAN[2] if (y // 6) % 2 else CYAN[1])
        for y in range(20, H, 96):  # pressure gauges on the frames
            gx = x0 + 6 if x0 == 0 else x1 - 9
            for (x, yy) in disc(gx + 1, y + 2, 2.2):
                cv.set(x, yy, '#E8ECF2' if x <= gx + 1 else '#A2A8BA')
            cv.set(gx + 1, y + 2, '#2A9A6A')
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
        ('view-1', 'viewport', 18, 8), ('view-2', 'viewport_b', 112, 8), ('view-3', 'viewport_c', 206, 8),
        # the lounge
        ('shelf', 'bookshelf', 22, 104), ('bench-1', 'lounge_bench', 74, 120), ('bench-2', 'lounge_bench', 194, 120),
        ('scope', 'telescope', 262, 98),
        # the atrium and its gardens
        ('pod-1', 'garden_pod', 128, 180), ('pod-2', 'garden_pod_b', 178, 372),
        # the sleep bay
        ('sleep-1', 'sleep_pod', 24, 186), ('sleep-2', 'sleep_pod', 24, 246), ('sleep-3', 'sleep_pod', 24, 306),
        ('sleep-4', 'sleep_pod', 64, 186), ('lockers', 'lockers', 30, 410),
        # the galley, the shuttle hatch and the navigation consoles
        ('table', 'galley_table', 236, 240), ('tea', 'tea_dispenser', 280, 186), ('trough-g', 'hydro_trough', 226, 186),
        ('lock-shuttle', 'airlock', 262, 316), ('console-1', 'console', 226, 440), ('console-2', 'console', 268, 440),
        # the arrival hall: hydroponics either side
        ('aquarium', 'aquarium_column', 110, 380), ('crates', 'cargo_crates', 196, 330), ('cushions', 'floor_cushions', 68, 360),
        # (review 19 Oct: four different crops, not two identical blocks)
        ('trough-1', 'hydro_trough', 20, 488), ('trough-2', 'hydro_trough_herbs', 34, 532),
        ('trough-3', 'hydro_trough_tomato', 248, 494), ('trough-4', 'hydro_trough_sprouts', 236, 536), ('lock-lift', 'airlock', 132, 502),
    ]
    stands = {'lift': (160, 500), 'atrium': (160, 300), 'viewport': (160, 144), 'sleep': (84, 280),
              'galley': (256, 296), 'shuttle': (290, 392)}
    return cv, objects, stands, blocked


# The base's roofed modules are gateways the companion walks through (their walk cells
# stay open under them; the renderer draws the companion behind them with its Ghost
# showing): registered in zones.py's OPENINGS table, as the castle's postern is.
OPENINGS.update({'pressure_tube': (0, 28), 'pressure_tube_dock': (0, 28), 'hab_hub': (62, 86), 'airlock_module': (12, 34)})


# Lumen's base (M1). The moon has no air, no water on the surface and nights two weeks
# long, so the companion and everyone with it live and walk only inside: a gangway from
# the shuttle, a hub dug in under a berm of regolith (shielding from radiation and
# micrometeorites), a corridor and an airlock, and the greenhouse dome where the plants
# grow under lamps, watered from ice dug out of a crater in permanent shadow and powered
# by solar arrays. Every pressurised volume is closed: the tubes and the airlock have
# hulls, the hub a roof under its berm, the dome glass all over, so the plants and the
# companion are seen through it (art-faults.md, faults 34 to 38, rule 10; Claude A's
# review, 19 Oct 14:20). The floors under them are drawn too, for the walk.
LUMEN_HUB = (90, 200, 230, 300)        # outer x0, y0, x1, y1 of the hub's berm
LUMEN_DOME = (166, 470, 118, 64, 74)   # base centre, radii and the dome's height
LUMEN_WALL = 10                         # the berm's thickness


def _deck(cv: Canvas, x: int, y: int, warm: bool = False):
    """One pixel of the base's floor: pale cast-regolith tiles, each lit along its top
    and left edge, warmer where the lamps fall."""
    HULL = MATERIALS['hull']
    px, py = x % 16, y % 12
    n = noise2(x // 16, y // 12, 392)
    c = HULL[4] if n > 0.3 else HULL[3]
    if px == 0 or py == 0:
        c = HULL[2]
    elif px == 1 or py == 1:
        c = HULL[5]
    cv.set(x, y, c)
    if warm:
        r, g, b, a = cv.get(x, y)
        cv.set(x, y, (min(255, r + 14), min(255, g + 8), b, a))


def _room(cv: Canvas, x0: int, y0: int, x1: int, y1: int, t: int, doors) -> tuple:
    """The walk inside a closed module (its hull or roof is the module's sprite, drawn
    over it): a tiled floor inside walls `t` thick, `doors` (side, a, b) the gaps where
    the next module joins. Returns (floor, walls)."""
    floor, walls = set(), set()

    def gap(x, y):
        for (side, a, b) in doors:
            if side in ('n', 's') and a <= x < b and ((side == 'n' and y < y0 + t) or (side == 's' and y >= y1 - t)):
                return True
            if side in ('w', 'e') and a <= y < b and ((side == 'w' and x < x0 + t) or (side == 'e' and x >= x1 - t)):
                return True
        return False
    for y in range(y0, y1):
        for x in range(x0, x1):
            edge = min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y)
            if gap(x, y):
                floor.add((x, y))
                _deck(cv, x, y)
            elif edge < t:
                walls.add((x, y))  # (the module's hull is its sprite; here, the walk's wall)
            else:
                floor.add((x, y))
                _deck(cv, x, y, warm=True)
    return floor, walls


def lumen(frame: int = 0):
    """Lumen, the quiet moon and the deepest rest, made livable (M1): grey regolith seen
    from above like everything else. The shuttle stands on a sintered pad ringed with
    landing lights; a closed tube runs from its hatch to the hub, a pressurised module on
    cradles with an EVA airlock at its west end (the melt tank and a padded ring for
    low-gravity sparring inside); a second tube and an airlock lead on to the greenhouse
    dome, glazed all over on a cast sill, with the sleeping tree, beds of moss, pools of
    melt water and a hammock under grow lamps. Outside, nothing grows: solar arrays
    turned to the sun, radiators, a mast, the ice rig at a crater whose floor never sees
    the sun, the old lander, boulders and craters."""
    R, GLOWm, VOID = MATERIALS['regolith'], MATERIALS['glowflora'], MATERIALS['void']
    HULL, CYAN, NAPm = MATERIALS['hull'], MATERIALS['neon_cyan'], MATERIALS['nap']
    cv = Canvas(W, H)
    for y in range(H):  # the regolith: two tones of dust, fine bright grains
        for x in range(W):
            n = smooth_noise(x, y, 28, 361) + (smooth_noise(x, y, 5, 363) - 0.5) * 0.12
            c = R[3] if n > 0.24 else R[2]   # (Matt, 20 Oct: no dither; soft-edged drifts of darker dust)
            if noise2(x // 2, y, 362) > 0.985:
                c = R[4]                      # a bright grain, two pixels wide
            cv.set(x, y, c)

    # (no sky: the camera looks down on the ground from above, as everywhere else in
    # the world; the review, 19 Oct 14:20: one camera)
    blocked = set()

    def crater(cx, cy, r, rays=False, seed=0):
        """An impact crater with real form in airless light: a raised rim lit on its
        upper-left outside, the bowl's upper-left inner wall in hard shadow and its far
        wall catching the sun, an outline broken by small slumps, ejecta round it."""
        if rays:  # bright ejecta rays across the dust
            for k in range(9):
                a = 2 * math.pi * k / 9 + 0.3 + seed
                end = int(r * (2.4 + noise2(k, seed, 368)))
                for t in range(int(r * 1.1), end):
                    x, y = int(cx + math.cos(a) * t), int(cy + math.sin(a) * t * 0.6)
                    # a ray of bright ejecta, broken into streaks that thin out with distance
                    if smooth_noise(t, k, 3, 371 + seed) > 0.35 + 0.4 * (t / end) and 0 <= x < W and 0 <= y < H:
                        cv.set(x, y, R[4])
                        if t < end * 0.6 and 0 <= y + 1 < H:
                            cv.set(x, y + 1, R[4])
        pts = []
        for y in range(int(cy - r * 0.75), int(cy + r * 0.75) + 1):
            for x in range(int(cx - r * 1.25), int(cx + r * 1.25) + 1):
                a = math.atan2(y - cy, x - cx)
                rr = r * (1 + 0.08 * math.sin(3 * a + seed) + 0.05 * math.sin(7 * a + seed * 2))
                d = math.hypot((x - cx) / rr, (y - cy) / (rr * 0.6))
                if d <= 1.18 and 0 <= x < W and 0 <= y < H:
                    pts.append((x, y, d, a))
        for (x, y, d, a) in pts:
            dx, dy = math.cos(a), math.sin(a)
            if d > 0.92:  # the raised rim: lit on its upper-left outside, shaded lower right
                v = 4.2 if dx + dy < -0.3 else 3.3 if dx + dy < 0.5 else 2.3
                if d > 1.08:
                    v = 3.6 if dx + dy < 0 else 2.6  # the ejecta apron
            elif d > 0.72:  # the inner wall: in hard black shadow on the upper left, lit on the far side
                v = 0 if dx + dy < 0 else 4.0 if dx + dy > 0.6 else 3.0
            else:  # the floor, half in the rim's hard shadow (no air, so no light fills it)
                v = 0 if (dx + dy) * d < 0.25 else 2.6
            c = R[max(0, min(5, int(v)))]
            cv.set(x, y, '#0C0B12' if v == 0 else c)
    # the rille: a winding collapsed lava tube across the south-west
    rille = worlds.thick([(-6, 392), (24, 420), (34, 470), (14, 520), (30, 560), (22, H + 6)], 6, seed=367)
    for (x, y) in rille:
        if not (0 <= x < W and 0 <= y < H):
            continue
        lit = (x + 1, y) not in rille  # its east wall faces west, into the sun; the west wall is in shadow
        cv.set(x, y, R[4] if lit else R[1] if (x - 1, y) not in rille or (x, y - 1) not in rille else R[2])
    for (cx, cy, r, rays, sd) in ((40, 132, 16, True, 1), (284, 98, 9, False, 2), (64, 372, 9, False, 3),
                                  (122, 556, 7, False, 4), (298, 236, 7, False, 5), (210, 572, 12, True, 6),
                                  (16, 252, 5, False, 7), (100, 158, 5, False, 8), (300, 512, 8, False, 9),
                                  (74, 300, 4, False, 10)):
        crater(cx, cy, r, rays, sd)
    # craters of every size (Matt, 20 Oct 10:15), the small ones simple bowls: a lit rim on
    # the far side, a hard black crescent of shadow inside the near rim
    keep_clear = [(160, 128, 76, 32), (160, 250, 82, 64), (166, 470, 124, 70), (262, 350, 46, 22)]
    for i in range(48):
        cx, cy = int(noise2(i, 0, 380) * W), int(noise2(i, 1, 380) * H)
        r = 2.5 + noise2(i, 2, 380) ** 2 * 5
        if any(abs(cx - kx) < kw and abs(cy - ky) < kh for (kx, ky, kw, kh) in keep_clear):
            continue
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r * 1.3) - 1, int(cx + r * 1.3) + 2):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                d = math.hypot((x - cx) / (r * 1.3), (y - cy) / r)
                if d > 1.15:
                    continue
                a = (x - cx) + (y - cy)
                if d > 0.85:
                    cv.set(x, y, R[4] if a > 0 else R[2])           # the rim: lit far side, near side in shade
                elif a < -r * 0.2 and r >= 3:
                    cv.set(x, y, '#0C0B12')                        # the shadow inside the near rim
                else:
                    cv.set(x, y, R[3])                             # the lit far wall
    # the shadowed crater in the east: its floor never sees the sun, so ice has lasted
    # there; frost glints in the dark, the rig's spoil heaped on the rim
    ICX, ICY, IRX = 262, 350, 40
    crater(ICX, ICY, IRX, False, 11)
    for y in range(ICY - 16, ICY + 18):
        for x in range(ICX - 34, ICX + 34):
            d = math.hypot((x - ICX) / 34, (y - ICY - 2) / 15)
            if d < 1:
                c = R[0] if d < 0.8 or (x + y) % 2 else R[1]
                if noise2(x // 2, y, 397) > 0.86 and d < 0.85:
                    c = '#A8C8E8' if noise2(x, y, 398) > 0.5 else '#5A7898'  # frost in the dark
                cv.set(x, y, c)
    for (x, y) in disc(ICX - 22, ICY + 10, 6):  # where the bucket has dug, ice showing bright
        if math.hypot((x - ICX) / 34, (y - ICY - 2) / 15) < 0.9:
            cv.set(x, y, '#C8DCEE' if (x + y) % 3 else '#E8F2FA')
    # the pad: sintered regolith pavers in rings round its centre, scorched where the
    # engine fires, landing lights round the edge and a low blast berm beyond them
    PX, PY, PRX, PRY = 160, 128, 62, 22
    for y in range(PY - PRY - 6, PY + PRY + 7):
        for x in range(PX - PRX - 8, PX + PRX + 9):
            d = math.hypot((x - PX) / PRX, (y - PY) / PRY)
            if d < 1:
                ring = int(d * 6)
                a = math.atan2((y - PY) / PRY, (x - PX) / PRX)
                seg = int((a + math.pi) * (4 + ring * 3) / math.pi)
                c = HULL[2] if (ring + seg) % 2 else HULL[3]
                if abs(d * 6 - round(d * 6)) < 0.08 or noise2(seg, ring, 399) > 0.97:
                    c = HULL[1]  # the joints between pavers
                if d < 0.35 and (x + y) % 2:
                    c = HULL[1]  # scorched where the engine fires
                cv.set(x, y, c)
            elif d < 1.22:  # the blast berm, lit on its upper left
                a = math.atan2(y - PY, x - PX)
                cv.set(x, y, R[4] if math.sin(a) > 0.2 else R[3] if math.cos(a) > -0.2 else R[2])
    for k in range(12):  # the landing lights
        a = 2 * math.pi * k / 12
        lx, ly = int(PX + math.cos(a) * PRX * 0.94), int(PY + math.sin(a) * PRY * 0.9)
        cv.set(lx, ly, '#FFE8A0'); cv.set(lx + 1, ly, '#F2A048'); cv.set(lx, ly + 1, HULL[1])
        light_pool(cv, lx, ly + 1, 6, 3, '#F2A048')
    # the base, cut away
    gang_f, gang_w = _room(cv, 146, 120, 176, 206, 6, [('n', 152, 170), ('s', 152, 170)])
    hx0, hy0, hx1, hy1 = LUMEN_HUB
    hub_f, hub_w = _room(cv, hx0, hy0, hx1, hy1, LUMEN_WALL, [('n', 152, 170), ('s', 152, 170)])
    cor_f, cor_w = _room(cv, 144, 300, 178, 372, 7, [('n', 152, 170), ('s', 152, 170)])
    walk = gang_f | hub_f | cor_f
    walls = gang_w | hub_w | cor_w
    # the sparring ring on the hub's floor: padded mats in a circle, a line round them
    for (x, y) in oval(160, 254, 34, 16):
        d = math.hypot((x - 160) / 34, (y - 254) / 16)
        c = NAPm[2] if (int(d * 4) + (x // 8)) % 2 else NAPm[1]
        if 0.9 < d:
            c = CYAN[3] if (x + y) % 3 else CYAN[2]
        cv.set(x, y, c)
    # the dome's floor and the cast sill it stands on (the glazed dome itself is the
    # greenhouse_dome sprite, drawn over everything inside it)
    DX, DY, DRX, DRY, DH = LUMEN_DOME
    inside = {(x, y) for x in range(DX - DRX, DX + DRX + 1) for y in range(DY - DRY, DY + DRY + 1)
              if math.hypot((x - DX) / DRX, (y - DY) / DRY) < 0.95}
    sill = {(x, y) for x in range(DX - DRX - 2, DX + DRX + 3) for y in range(DY - DRY - 2, DY + DRY + 5)
            if 0.95 <= math.hypot((x - DX) / DRX, (y - DY) / DRY) < 1.03 and y >= DY - 6}
    floor_d = set()
    for (x, y) in inside:  # the greenhouse floor: beds of moss in arcs, cast paths between
        d = math.hypot((x - DX) / DRX, (y - DY) / DRY)
        band = int(d * 7)
        path = abs(d * 7 - band - 0.5) > 0.36 or abs(x - DX) < 7
        if path:
            c = HULL[4] if (x // 6 + y // 4) % 2 else HULL[3]
            if y % 4 == 0:
                c = HULL[2]
        else:
            n = smooth_noise(x, y, 6, 369)
            c = GLOWm[1] if n > 0.45 else GLOWm[0]
            if n > 0.7 or (n > 0.64 and (x + y) % 2):
                c = GLOWm[2]
            if noise2(x, y, 370) > 0.94:
                c = GLOWm[3]
        cv.set(x, y, c)
        floor_d.add((x, y))
    for (x, y) in sill:  # the cast sill the glass stands on, its front lit, frame stubs on it
        k = math.atan2(y - DY, x - DX)
        c = '#E8E4EE' if y < DY else '#B8B4C8' if math.cos(k) < 0.4 else '#8A86A0'
        cv.set(x, y, c)
    for (x, y) in sill:
        if y > DY and (x, y + 1) not in sill and y + 1 < H:
            for d in (1, 2):
                style.darken(cv, x + d - 1, y + d)
    light_pool(cv, DX, DY + 4, 92, 46, '#FFE0A0', sill)  # the lamps' warm light
    # the airlock between the corridor and the dome: a short room through the glass
    lock_f, lock_w = _room(cv, 142, 366, 180, 420, 8, [('n', 152, 170), ('s', 152, 170)])
    for y in (380, 404):  # its two hatches, open, their frames lit
        for x in range(150, 172):
            cv.set(x, y, '#E8C04A' if (x // 3) % 2 else '#2A2630')
    walk |= lock_f | floor_d
    walls |= lock_w
    # the pipe from the ice rig to the hub on low trestles, and the arrays' cables
    pipe = [(200, 320), (214, 312), (224, 300)]
    for (a, b) in zip(pipe, pipe[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
        for t in range(n + 1):
            x, y = int(a[0] + (b[0] - a[0]) * t / n), int(a[1] + (b[1] - a[1]) * t / n)
            cv.set(x, y, '#E8ECF2'); cv.set(x, y + 1, '#8A93A8')
            if t % 6 == 0:
                cv.set(x, y + 2, HULL[2]); cv.set(x, y + 3, HULL[1])  # a trestle
    # the coolant line from the hub's east end out to the radiators on low trestles (review
    # 19 Oct: the radiators need a line to what they cool)
    cool = [(228, 246), (244, 240), (300, 240)]
    for (a, b) in zip(cool, cool[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
        for t in range(n + 1):
            x, y = int(a[0] + (b[0] - a[0]) * t / n), int(a[1] + (b[1] - a[1]) * t / n)
            cv.set(x, y, '#E8ECF2'); cv.set(x, y + 1, '#8A93A8')
            if t % 8 == 0:
                cv.set(x, y + 2, HULL[2]); cv.set(x, y + 3, HULL[1])
    for (rx, ry0) in ((254, 230), (286, 236)):  # the drops from each radiator's manifold
        for y in range(ry0, 240):
            cv.set(rx, y, '#E8ECF2'); cv.set(rx + 1, y, '#8A93A8')
    # the solar arrays, staggered across the dust at three tilts (review 19 Oct: not three
    # the same in a column): each casts its shadow down and to the right on the regolith,
    # and its cable runs on low pegs from its foot to the hub's west end
    ARRAYS = [('solar-1', 'solar_array', 4, 188, 64), ('solar-2', 'solar_array_b', 30, 252, 52),
              ('solar-3', 'solar_array_c', 2, 316, 58)]
    for (_n, _k, ax, ay, aw) in ARRAYS:
        for r in range(9):
            for x in range(ax + 8 + r, ax + aw + 2 + r):
                y = ay + 31 + r
                if (x, y) not in walk and 0 <= x < W:
                    style.darken(cv, x, y); style.darken(cv, x, y)  # hard and dark: no air to fill it
    for (a, b) in (((68, 230), (hx0 + 4, 236)), ((82, 294), (hx0 + 4, 286)), ((60, 358), (hx0 + 14, 300))):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
        for t in range(n + 1):
            x, y = int(a[0] + (b[0] - a[0]) * t / n), int(a[1] + (b[1] - a[1]) * t / n)
            cv.set(x, y, '#8A93A8'); cv.set(x, y + 1, '#3A3C4A')
            if t % 10 == 5:
                cv.set(x, y + 2, HULL[1])  # a peg
    # the rover's tracks from the pad round the base to the ice rig and on to the old
    # lander: two treads pressed into the dust, their chevrons in the bottom of each
    def polyline(pts):
        out = []
        for (a, b) in zip(pts, pts[1:]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
            out += [(a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n, (b[0] - a[0]) / n, (b[1] - a[1]) / n)
                    for t in range(n)]
        return out
    for route in ([(214, 150), (250, 170), (262, 262), (232, 300)], [(262, 262), (310, 330), (312, 420), (292, 500)]):
        for i, (x, y, dx, dy) in enumerate(polyline(route)):
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            for side in (-3.5, 3.5):
                for k in (0, 1):
                    px, py = int(round(x + nx * (side + k))), int(round(y + ny * (side + k)))
                    if 0 <= px < W and 0 <= py < H and (px, py) not in walk and cv.get(px, py)[:3] != (12, 11, 18):
                        cv.set(px, py, R[1] if (i + k) % 3 == 0 else R[2])
    # bootprints from the EVA airlock's steps out to the solar arrays and back
    for i, (x, y, dx, dy) in enumerate(polyline([(98, 296), (74, 310), (50, 336), (36, 352)])):
        if i % 5:
            continue
        ln = math.hypot(dx, dy) or 1
        side = 1.5 if (i // 5) % 2 else -1.5
        px, py = int(round(x - dy / ln * side)), int(round(y + dx / ln * side))
        for (qx, qy, c) in ((px, py, R[1]), (px + 1, py, R[1]), (px, py + 1, R[4])):
            if 0 <= qx < W and 0 <= qy < H and (qx, qy) not in walk:
                cv.set(qx, qy, c)
    # the hub's hard black shadow, thrown down and to the right on the dust (no air, so
    # nothing lightens it): under the module past its footpads, and east of its end cap
    hub = style.finalize(spp.hab_hub(), name='hab_hub')
    hx, hy = 86 + hub.ox, 180 + hub.oy
    solid = {(hx + x, hy + y) for y in range(hub.h) for x in range(hub.w) if hub.get(x, y)[3] > 200}
    hub_shadow = {(x + 9, y + 5) for (x, y) in solid if y > hy + 40} - solid
    for (x, y) in hub_shadow - walk:
        if 0 <= x < W and 0 <= y < H:
            c = cv.get(x, y)
            cv.set(x, y, (int(c[0] * 0.22) + 4, int(c[1] * 0.22) + 4, int(c[2] * 0.25) + 8, 255))
    walls |= {(x, y) for x in range(W) for y in range(H)} - walk
    # the regolith's cool greys would read as water to the lint's colour test; Lumen has
    # no open water at all (the pools are props on the greenhouse floor), so it says so
    WATER_MASKS['lumen'] = set()
    objects = [
        ('shuttle', 'shuttle', 120, 54),
        # outside, on the dust: power, heat, the mast, the ice rig, the old lander
        *[(n, k, ax, ay) for (n, k, ax, ay, _w) in ARRAYS],
        ('rad-1', 'radiator', 238, 192), ('rad-2', 'radiator', 270, 200), ('mast', 'comm_mast', 288, 132),
        ('rig', 'ice_rig', 188, 306), ('lander', 'old_lander', 268, 520),
        ('rock-1', 'moon_rock', 20, 164), ('rock-2', 'moon_rock_small_b', 52, 176), ('rock-3', 'moon_rock_b', 290, 412),
        ('rock-4', 'moon_rock_small', 304, 432), ('rock-5', 'moon_rock_small', 60, 550), ('rock-6', 'moon_rock_b', 214, 552),
        ('rock-7', 'moon_rock_small_b', 232, 102), ('rock-8', 'moon_rock', 76, 92),
        # the base: the gangway tube from the shuttle, the hub under its berm, the tube to
        # the airlock, the glazed dome (the companion walks inside them, behind them)
        ('gangway', 'pressure_tube_dock', 147, 118), ('hub', 'hab_hub', 86, 180),
        ('corridor', 'pressure_tube', 147, 300), ('lock', 'airlock_module', 137, 360),
        ('dome', 'glass_dome', DX - 120, DY - 140),
        # the greenhouse
        ('tree', 'moon_tree', DX - 10, DY - 50), ('hammock', 'hammock', DX - 94, DY - 4),
        ('pool-1', 'dream_pool', DX + 48, DY + 22), ('pool-2', 'dream_pool_b', DX - 34, DY + 34),
        ('caps-1', 'glow_caps', DX + 18, DY + 34), ('caps-2', 'glow_caps', DX - 76, DY - 30), ('caps-3', 'glow_caps', DX + 66, DY - 26),
        ('lamp-1', 'grow_lamp', DX - 102, DY - 30), ('lamp-2', 'grow_lamp', DX + 70, DY + 6),
    ]
    stands = {'shuttle': (160, 150), 'sparring': (160, 254), 'grove': (166, 446), 'hammock': (DX - 60, DY + 40),
              'airlock': (160, 392)}
    return cv, objects, stands, walls


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

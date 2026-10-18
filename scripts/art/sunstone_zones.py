"""Sunstone Reach: Dust Gulch, the oasis, the Scorched Pass, Hearthold, the caldera
and Cinder Springs, with what lies past them (the dunes, the volcano's ash flank).

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['GULCH_STREET', 'GULCH_CREEK', 'wagon_ruts', 'gulch_sand', 'buffer_stop', 'gulch', 'oasis', 'SPRINGS_PATH',
           'FIRE_OFF', 'LAVA_RIVER', 'LAVA_DRAIN', 'BASIN', 'ISLE', 'MOAT', 'fire_lava', 'lava_px', 'paint_lava',
           'caldera_rim', 'cooled_flow', 'caldera', 'springs', 'SCORCH_ROAD', 'GULCH_PASS', 'scorch', 'basalt_flags',
           'ash_flags', 'stone_bridge', 'castle', 'beyond_dunes', 'beyond_ash']


GULCH_STREET = [(130, 78), (128, 200), (136, 300), (130, 420), (110, 496), (60, 520), (-40, 524)]

# The mesa in Dust Gulch's north-east (x from MESA_X0 to MESA_X1, its south rim near
# MESA_RIM), and the mine cart line out of its face: rails at CART_X and CART_X + 11
# from the mine's mouth (MINE_Y) south to the buffer (CART_END).
MESA_X0, MESA_X1, MESA_RIM, MESA_FACE = 226, 306, 98, 28
CART_X, MINE_Y, CART_END = MESA_X0 + 34, MESA_RIM + MESA_FACE, 176
CART_STOP = 132  # where the cart line ends in the caldera, at a buffer on its basalt landing


def buffer_stop(cv: Canvas, x0: int, y0: int, vertical: bool = True, heap=None):
    """Where a line ends: a timber beam across the rails, painted red and white so it is
    seen from the cab, braced from behind by two raked posts, a heap of sand at its back.
    `vertical`: the beam stands across a line running east-west (as at the platform);
    otherwise across one running north-south (the cart bay)."""
    WOODm, IRONm = MATERIALS['wood'], MATERIALS['iron']
    DESERT = heap or MATERIALS['desert']
    if vertical:  # a line running east, ending at x0 + 6
        for (x, y) in oval(x0 + 13, y0 + 8, 6, 10):  # sand (or rock) heaped against the back
            cv.set(x, y, DESERT[4] if x < x0 + 13 else DESERT[2])
        for x in range(x0 + 6, x0 + 12):  # the raked braces
            for y in (y0 + 1 + (x - x0 - 6) // 2, y0 + 13 - (x - x0 - 6) // 2):
                cv.set(x, y, WOODm[1]); cv.set(x, y + 1, WOODm[0])
        for y in range(y0 - 2, y0 + 17):  # the beam, banded red and white
            band = ((y - y0 + 2) // 4) % 2
            cv.set(x0 + 3, y, RED[4] if band else '#E8E0D0')
            cv.set(x0 + 4, y, RED[3] if band else '#C8C0B0')
            cv.set(x0 + 5, y, RED[1] if band else '#8E887C')
            cv.set(x0 + 6, y, '#1E1917')
        for y in (y0 + 2, y0 + 9):  # the rails' ends, bolted to it
            cv.set(x0 + 2, y, IRONm[4]); cv.set(x0 + 2, y + 1, IRONm[1])
        return
    # a line running south, ending at y0
    for (x, y) in oval(x0 + 11, y0 + 7, 11, 5):
        cv.set(x, y, DESERT[4] if y < y0 + 7 else DESERT[2])
    for y in range(y0, y0 + 4):
        for x in range(x0 - 1, x0 + 23):
            band = ((x - x0 + 1) // 4) % 2
            c = (RED[4] if band else '#E8E0D0') if y == y0 else (RED[3] if band else '#C8C0B0') if y < y0 + 3 else '#1E1917'
            cv.set(x, y, c)
    for px in (x0 + 2, x0 + 18):
        cv.vline(px, y0 + 4, 4, WOODm[1]); cv.vline(px + 1, y0 + 4, 4, WOODm[0])


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


def gulch_sand(x: int, y: int) -> str:
    """Dust Gulch's open sand at its own pixel `x, y` (x past its east edge carries on
    into the Scorched Pass): wind ripples, darker drifts dithered in, and flat cracked
    hardpan in patches."""
    DESERT = MATERIALS['desert']
    if smooth_noise(x, y, 18, 223) > 0.74:
        return DESERT[1] if cracked(x, y, 8, 1) else DESERT[4] if (x + y) % 5 else DESERT[3]
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
    return c


def gulch(frame: int = 0):
    """Dust Gulch, its own place: a town strung along one street that runs down from the
    railway's end, under a sandstone mesa on the east with the old mine cut into its
    foot. A dry creek bed of cracked mud winds across (the reason the well ran dry),
    crossed by a plank bridge; the water tower and windpump stand by it, still hoping.
    The corral is out on the open sand, and the wagon track leaves west for the oasis.
    The railway comes in from the west and stops at a buffer by the mesa; the mine's cart
    line runs out of the mesa's face to its own bay beside the platform (18 Oct, Codex's
    transport contract: two lines, one dry forecourt between them, no junction)."""
    DESERT, ADOBE = MATERIALS['desert'], MATERIALS['adobe']
    BLEACHED = wsp.BLEACHED
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, gulch_sand(x, y))
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
    # the railway comes in from the west (through the oasis) and ends here at a buffer
    # stop in front of the mesa; the plank platform runs along its south side
    paint_rails(cv, 40)
    for y in range(36, 60):  # nothing beyond the buffer: the ballast stops with the line
        for x in range(MESA_X0 - 15, W):
            cv.set(x, y, gulch_sand(x, y))
    buffer_stop(cv, MESA_X0 - 22, 38)
    for y in range(58, 78):
        for x in range(20, MESA_X0 - 2):
            cv.set(x, y, BLEACHED[3] if (x // 6) % 2 else BLEACHED[2])
            if (x % 6) == 3 and y % 10 == 2:
                cv.set(x, y, BLEACHED[0])  # nail heads
    cv.hline(20, 58, MESA_X0 - 22, BLEACHED[5]); cv.hline(20, 78, MESA_X0 - 22, BLEACHED[0])
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
    # the track east under the mesa to the Scorched Pass (the lava region, 18 Oct)
    pass_track = worlds.thick(GULCH_PASS, 8, seed=755)
    for (x, y) in pass_track:
        if 0 <= x < W and 0 <= y < H and (x, y) not in street:
            n = smooth_noise(x, y, 10, 213)
            cv.set(x, y, DESERT[2] if n > 0.3 or (x + y) % 2 else DESERT[1])
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
    # the mesa in the north-east: a sandstone butte running on past the north edge, its
    # top scrubby, its sunlit west end and south face banded in strata, a shadow at its
    # foot. You cannot climb it. The old mine is cut into its south face.
    mesa = set()
    # adobe's ramp with its middle tone a shade duller (orange rock that blocks the way
    # would read as lava to the world lint)
    MESA = ADOBE[:2] + ['#A6704A'] + ADOBE[3:]

    def rim(x):
        if abs(x - CART_X - 5) < 22:
            return MESA_RIM  # dressed level over the mine's mouth
        return MESA_RIM + int(math.sin(x / 13) * 3 + noise2(x // 6, 0, 230) * 4)
    FACE_H = MESA_FACE
    for x in range(MESA_X0, MESA_X1):
        top = rim(x)
        for y in range(0, top):
            n = smooth_noise(x, y, 24, 221)
            c = MESA[3] if n > 0.2 or (n > 0.15 and (x + y) % 2) else MESA[2]
            if n > 0.75 or (n > 0.7 and (x + y) % 2):
                c = MESA[4]
            if top - y < 3:
                c = DESERT[5] if top - y == 1 else MESA[4]  # the sunlit rim
            cv.set(x, y, c)
            mesa.add((x, y))
        for k in range(FACE_H):  # the south face: strata, each band lit on its upper edge
            y = top + k
            wob = int(noise2(x // 9, 3, 222) * 3)
            band = (k + wob) // 5
            c = MESA[2] if band % 2 else MESA[1]
            if (k + wob) % 5 == 0:
                c = MESA[3]
            if k == 0:
                c = MESA[0]
            if k > FACE_H - 3:
                c = MESA[0]  # the foot, in its own shade
            cv.set(x, y, c)
            mesa.add((x, y))
        for d in range(4):  # the face's shadow on the sand below
            if d < 2 or (x + d) % 2:
                style.darken(cv, x, top + FACE_H + d)
    for y in range(0, rim(MESA_X0) + FACE_H):  # the west end, in the sun
        for k in range(5):
            x = MESA_X0 - 5 + k
            c = MESA[4] if (y // 5 + k) % 3 == 0 else MESA[3]
            if k == 0:
                c = MESA[1]  # its edge against the sand
            cv.set(x, y, c)
            mesa.add((x, y))
    for y in range(0, rim(MESA_X1 - 1) + FACE_H):  # the east end, in shade, and its shadow
        for k in range(5):
            x = MESA_X1 + k
            cv.set(x, y, MESA[1] if (y // 5 + k) % 3 else MESA[0])
            mesa.add((x, y))
        for d in range(5, 9):
            if (d + y) % 2 or d < 7:
                style.darken(cv, MESA_X1 + d, y)
    for i in range(30):  # scrub on the mesa top
        x, y = MESA_X0 + 6 + int(noise2(i, 0, 231) * (MESA_X1 - MESA_X0 - 12)), int(noise2(i, 1, 231) * (MESA_RIM - 10))
        detail.grass_tuft(cv, x, y, i % 6, ['#5A4A2A', '#7A6436', '#9A8044', '#B89A58', '#D2B672'], 2)
    # the mine's mouth cut into the south face: a timber frame round the dark, the
    # rails running in
    WOODm = MATERIALS['wood']
    mx0, mx1, my0 = CART_X - 7, CART_X + 19, MESA_RIM + 5
    for y in range(my0, MINE_Y):
        for x in range(mx0, mx1):
            cv.set(x, y, '#1A120E' if y > my0 + 3 else '#2A1C16')
    for y in range(my0 + 8, MINE_Y, 3):  # sleepers fading into the dark
        cv.hline(CART_X - 1, y, 14, '#3A2A20' if y > MINE_Y - 9 else '#2A1E18')
    for rx in (CART_X, CART_X + 11):
        cv.vline(rx, my0 + 10, MINE_Y - my0 - 10, MATERIALS['iron'][2])
    for px in (mx0 - 3, mx1):  # the posts, lit on the left
        cv.vline(px, my0, MINE_Y - my0, WOODm[4]); cv.vline(px + 1, my0, MINE_Y - my0, WOODm[3])
        cv.vline(px + 2, my0, MINE_Y - my0, WOODm[1])
    cv.rect(mx0 - 4, my0 - 4, mx1 - mx0 + 8, 4, WOODm[3])  # the lintel
    cv.hline(mx0 - 4, my0 - 4, mx1 - mx0 + 8, WOODm[4]); cv.hline(mx0 - 4, my0 - 1, mx1 - mx0 + 8, WOODm[1])
    cv.hline(mx0 - 5, my0 - 5, mx1 - mx0 + 10, '#1E1917')
    # the mine cart line (Codex's transport contract): narrow-gauge rails out of the
    # mine's mouth, south to a bay that ends at a buffer stop, with a plank landing on its
    # west side. A dry forecourt joins the landing to the railway platform: you walk
    # across from the train to the carts; the two lines never meet.
    ballast = rect_set_z(CART_X - 4, MINE_Y, 22, CART_END - MINE_Y + 2)
    for (x, y) in ballast:
        n = noise2(x, y, 141)
        cv.set(x, y, STONE[2] if n > 0.55 else STONE[1] if n > 0.15 else STONE[3])
    for y in range(MINE_Y + 1, CART_END, 4):  # sleepers
        cv.hline(CART_X - 2, y, 18, WOOD[2]); cv.hline(CART_X - 2, y + 1, 18, WOOD[1])
        cv.set(CART_X - 2, y, WOOD[3])
    for rx in (CART_X, CART_X + 11):  # the rails, with a bright running edge
        cv.vline(rx, MINE_Y, CART_END - MINE_Y, MATERIALS['iron'][4])
        cv.vline(rx + 1, MINE_Y, CART_END - MINE_Y, MATERIALS['iron'][2])
    buffer_stop(cv, CART_X - 4, CART_END, vertical=False)
    for y in range(MINE_Y, CART_END + 4):  # the cart landing, planks running north-south
        for x in range(CART_X - 24, CART_X - 5):
            c = BLEACHED[3] if (x // 6) % 2 else BLEACHED[2]
            if (x % 6) == 3 and y % 10 == 2:
                c = BLEACHED[0]
            cv.set(x, y, c)
        cv.set(CART_X - 24, y, BLEACHED[5]); cv.set(CART_X - 5, y, BLEACHED[0])
    cv.hline(CART_X - 24, CART_END + 4, 20, BLEACHED[0])
    forecourt = {(x, y) for y in range(79, MINE_Y + 2) for x in range(146, MESA_X0 - 5)
                 if not (x < 150 + (y - 79) // 3 and (x + y) % 2)}
    for (x, y) in forecourt:  # packed earth, swept, a few stones
        n = smooth_noise(x, y, 8, 236)
        c = P[3] if n > 0.4 or (n > 0.34 and (x + y) % 2) else P[2]
        if noise2(x, y, 237) > 0.97:
            c = P[4]
        cv.set(x, y, c)
    # the corral: hoof-churned ground out on the open sand
    ccx, ccy = 190, 470
    for (x, y) in oval(ccx, ccy, 44, 26):
        n = smooth_noise(x, y, 5, 216)
        cv.set(x, y, DESERT[1] if n > 0.6 else DESERT[2] if n > 0.25 else ADOBE[2])
    objects = [
        ('saloon', 'saloon', 6, 94), ('hitch-1', 'hitching_rail', 118, 178), ('poster', 'poster_board', 150, 86),
        ('store', 'store', 6, 210), ('keg-1', 'keg', 100, 290), ('keg-2', 'keg', 104, 280),
        ('tower', 'water_tower', 168, 200), ('pump', 'windpump', 30, 226 + 100), ('trough', 'trough', 176, 300),
        ('well', 'dry_well', 58, 360), ('wagon', 'wagon', 16, 470), ('hay-1', 'hay_bale', 122, 524), ('hay-2', 'hay_bale', 108, 538),
        ('dyn-1', 'dynamite_crate', CART_X + 20, MINE_Y + 8),
        ('dyn-2', 'dynamite_crate', CART_X + 26, MINE_Y + 30),
        ('corral-n', 'corral_rail', ccx - 46, ccy - 36), ('corral-s', 'corral_rail', ccx - 46, ccy + 22),
        ('corral-w', 'corral_side', ccx - 52, ccy - 22),
        ('cactus-1', 'saguaro', 10, 380), ('cactus-2', 'saguaro_small', 224, 400), ('cactus-3', 'saguaro', 150, 520),
        ('cactus-4', 'saguaro_small', 286, 540), ('cactus-5', 'saguaro', 276, 4), ('cactus-6', 'saguaro_small', 4, 2),
        ('cactus-7', 'saguaro', 290, 300), ('weed-1', 'tumbleweed', 170, 380), ('weed-2', 'tumbleweed', 96, 562),
        ('skull', 'cow_skull', 250, 520), ('barrel-p', 'keg', 40, 62), ('sack-p', 'hay_bale', 196, 56),
        ('horse', 'horse', ccx - 30, ccy - 24), ('pear-1', 'prickly_pear', 244, 466), ('pear-2', 'prickly_pear', 280, 426),
        ('pear-3', 'prickly_pear', 200, 548),
    ]
    stands = {'platform': (128, 70), 'saloon': (58, 200), 'street': (132, 260), 'corral': (190, 470),
              'oasis': (12, 524), 'mine': (CART_X - 14, CART_END + 12), 'well': (75, 404), 'pass': (312, 384),
              'forecourt': (190, 100)}
    return cv, objects, stands, mesa


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
    track = street | worlds.thick([(W - 24, 524), (284, 522), (252, 516)], 15, seed=32)
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
        ('tent', 'tent', 238, 420), ('camel-1', 'camel', 214, 482), ('camel-2', 'camel', 266, 486),
        ('fire', 'fire_pit', 260, 460), ('awning', 'awning', 240, 360), ('jar-3', 'water_jar', 228, 386),
        # the older town
        ('arch', 'sandstone_arch', 26, 450), ('col-1', 'column_stump', 92, 470), ('col-2', 'column_stump_b', 92, 500),
        ('col-3', 'column_stump_b', 10, 500),
        # out in the dunes
        ('cactus-1', 'saguaro_small', 286, 118), ('skull', 'cow_skull', 180, 540), ('weed', 'tumbleweed', 40, 150),
        ('weed-2', 'tumbleweed', 250, 220), ('acacia-1', 'acacia', 226, 84), ('acacia-2', 'acacia', 4, 92),
        ('scrub-1', 'desert_scrub', 128, 140), ('scrub-2', 'desert_scrub_b', 16, 400), ('scrub-3', 'desert_scrub', 184, 420),
        ('scrub-4', 'desert_scrub_b', 288, 300), ('rocks-1', 'sandstone_outcrop', 140, 505),
        ('rocks-2', 'sandstone_outcrop_b', 256, 170),
    ]
    stands = {'gulch': (312, 524), 'pool': (130, 352), 'camp': (250, 500), 'arch': (58, 500),
              'crane': (110, 76), 'dunes': (200, 140)}
    return cv, objects, stands, pool


SPRINGS_PATH = [(-6, 300), (40, 316), (52, 380), (48, 440), (130, 470), (190, 486), (250, 488)]


# The fire country's lava is one course (Codex's connected-world design, section 5):
# out of the crater lake, down through the caldera, round Hearthold's rock and away
# through the Scorched Pass into a crusted basin. It is drawn in the caldera's
# coordinates; each zone paints the part that crosses it (FIRE_OFF: the zone's top left
# in those coordinates), so colour, crust and glow run on across every border.
FIRE_OFF = {'caldera': (0, 0), 'springs': (W, 0), 'hearthold': (0, H), 'scorch': (0, 2 * H)}
LAVA_RIVER = [(170, 60), (178, 140), (160, 230), (200, 320), (236, 400), (234, 470), (228, 540),
              (226, H + 30), (218, H + 66)]                       # the caldera into the moat
LAVA_DRAIN = [(48, H + 396), (44, H + 470), (50, H + 540), (52, 2 * H + 10), (56, 2 * H + 110),
              (80, 2 * H + 250), (98, 2 * H + 372), (110, 2 * H + 444)]  # the moat into the basin
BASIN = (138, 2 * H + 496, 64, 40)  # the crusted basin in the Scorched Pass: centre and radii
ISLE = (160, 254, 116, 150)        # Hearthold's isle in the lava (its own coordinates)
MOAT = (152, 250, 138, 192)        # the moat's outer edge
def _course(points, radius: float, seed: int) -> set:
    """worlds.thick, unclipped: a band along a polyline in the fire country's coordinates."""
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 9, seed) - 0.5) * 2.4
            pts |= disc(cx, cy, r)
    return pts


def _superellipse(x, y, cx, cy, rx, ry, n):
    return abs((x - cx) / rx) ** n + abs((y - cy) / ry) ** n


@functools.lru_cache(maxsize=None)
def fire_lava():
    """The molten lava (a frozenset in the fire country's coordinates) and the basin's
    crust, which is solid but not to be walked on."""
    mx, my, mrx, mry = MOAT
    ix, iy, irx, iry = ISLE
    moat = {(x, y + H) for x in range(W) for y in range(H)
            if _superellipse(x, y, mx, my, mrx, mry, 3) <= 1 and _superellipse(x, y, ix, iy, irx, iry, 4) > 1}
    bx, by, brx, bry = BASIN
    core, crust = set(), set()
    for y in range(by - bry - 2, by + bry + 3):
        for x in range(bx - brx - 2, bx + brx + 3):
            a = math.atan2(y - by, x - bx)
            wob = 1 + 0.07 * math.sin(3 * a + 0.4) + 0.05 * math.sin(7 * a + 1.3)
            d = math.hypot((x - bx) / brx, (y - by) / bry) / wob
            if d < 0.42:
                core.add((x, y))  # still molten in the middle, where the channel pours in
            elif d < 1:
                crust.add((x, y))
    isle = {(x, y + H) for x in range(W) for y in range(H) if _superellipse(x, y, ix, iy, irx, iry, 4) <= 1}
    river = (_course(LAVA_RIVER, 12, 14) | _course(LAVA_DRAIN, 11, 734)) - isle
    pour = _course([(110, 2 * H + 444), (bx - 8, by - 6)], 9, 735) - isle
    return frozenset(river | moat | core | pour), frozenset(crust - pour - core)


def lava_px(X: int, Y: int, frame: int = 0) -> str:
    """Molten rock at a point of the fire country: moving bands of orange and gold."""
    LAVA = MATERIALS['lava']
    n = smooth_noise(X, Y + frame * 3, 7, 265)
    c = LAVA[3] if n > 0.45 else LAVA[2]
    if n > 0.75:
        c = LAVA[5] if n > 0.88 else LAVA[4]
    return c


def paint_lava(cv: Canvas, zone: str, frame: int = 0, lake=frozenset()) -> set:
    """Paint the part of the fire country's lava that crosses `zone`: the molten bands,
    crust plates drifting at the edges, cooled crust on the banks with glowing seams, a
    bright lip on the upper bank and dark rock under the lower one, the basin's crust,
    and the light it throws on the ground. Every test is made in the fire country's
    coordinates, so nothing starts or stops at a border. `lake`: the crater lake in this
    zone's pixels (the river leaves it without a lip). Returns the zone's blocked pixels."""
    LAVA, BASALT = MATERIALS['lava'], MATERIALS['basalt']
    ox, oy = FIRE_OFF[zone]
    molten, crust = fire_lava()
    lake_c = {(x + ox, y + oy) for (x, y) in lake}
    near = [(X, Y) for (X, Y) in molten if -14 <= X - ox < W + 14 and -14 <= Y - oy < H + 14]
    hot = molten | lake_c
    for (X, Y) in near:  # cooled crust on the banks, its seams still glowing
        for (dx, dy) in ((10, 0), (-10, 0), (0, 10), (7, 7), (-7, 7), (0, -9)):
            q = (X + dx, Y + dy)
            x, y = q[0] - ox, q[1] - oy
            if q in hot or q in crust or not (0 <= x < W and 0 <= y < H):
                continue
            if cracked(q[0], q[1], 7, 4):
                cv.set(x, y, LAVA[2] if noise2(q[0], q[1], 267) > 0.4 else LAVA[1])
            elif noise2(q[0] // 3, q[1] // 3, 268) > 0.3:
                cv.set(x, y, BASALT[2] if (q[0] + q[1]) % 3 else BASALT[3])
    local = set()
    for (X, Y) in near:
        x, y = X - ox, Y - oy
        if not (0 <= x < W and 0 <= y < H):
            continue
        c = lava_px(X, Y, frame)
        near_bank = any((X + dx, Y + dy) not in hot for dx, dy in ((5, 0), (-5, 0), (0, 5), (0, -5)))
        if near_bank and cracked(X, Y, 7, 4) and smooth_noise(X, Y + frame * 3, 7, 265) < 0.6:
            c = LAVA[1]  # a crust plate drifting at the edge
        cv.set(x, y, c)
        local.add((x, y))
    bx, by, brx, bry = BASIN
    for (X, Y) in crust:  # the basin: a skin of black crust, cracked into plates that glow
        x, y = X - ox, Y - oy
        if not (0 <= x < W and 0 <= y < H):
            continue
        d = math.hypot((X - bx) / brx, (Y - by) / bry)
        if cracked(X, Y, 9, 8):
            c = LAVA[3] if d < 0.6 else LAVA[2] if d < 0.8 else LAVA[1]
        else:
            c = BASALT[2] if smooth_noise(X, Y, 6, 269) > 0.45 else BASALT[1]
            if d > 0.9:
                c = BASALT[3]  # the rim of the crust, older and greyer
        cv.set(x, y, c)
        local.add((x, y))
    for (X, Y) in near + [p for p in crust if (p[0] - ox, p[1] - oy) in local]:
        x, y = X - ox, Y - oy
        if (x, y) not in local:
            continue
        if (X, Y - 1) not in hot and (X, Y - 1) not in crust:
            cv.set(x, y, LAVA[5] if (X, Y) in molten else BASALT[4])  # the lit upper bank
        if (X, Y + 1) not in hot and (X, Y + 1) not in crust and y + 1 < H:
            cv.set(x, y + 1, BASALT[0])
    spots = {(X // 26 * 26 + 13, Y // 26 * 26 + 13) for (X, Y) in molten}
    for (X, Y) in sorted(spots):  # its light on the ground round it, across borders too
        x, y = X - ox, Y - oy
        if -24 <= x < W + 24 and -16 <= y < H + 16:
            light_pool(cv, x, y, 22, 14, LAVA[1], local | set(lake))
    return local


def caldera_rim(x):
    """The crater rim's line (x in the caldera's coordinates)."""
    return 62 + int(math.sin(x / 19) * 7 + noise2(x // 5, 0, 263) * 6)


def cooled_flow(cv: Canvas, points, radius: float, seed: int, skip=frozenset()):
    """A tongue of old lava cooled flat on the ash (pahoehoe): a dark basalt sheet whose
    skin wrinkled into ropes as it flowed, the ropes bowed downstream (they ran faster
    down the middle), a lit lip along its upper edge and a dark toe with a hard shadow
    on the ash below. Walkable ground; paths and rivers painted later cover it."""
    BASALT = MATERIALS['basalt']
    # narrow where it left its source, spreading as it went, and ending in round toes
    total = sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(points, points[1:]))
    sheet, run = set(), 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        for i in range(int(seg) + 1):
            t = i / max(1, seg)
            f = (run + seg * t) / total
            r = radius * (0.45 + 0.75 * f) * (0.85 + 0.3 * smooth_noise(x0 + i, y0, 7, seed))
            sheet |= disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r)
        run += seg
    (ax, ay), (bx, by) = points[-2], points[-1]
    ux, uy = (bx - ax) / math.hypot(bx - ax, by - ay), (by - ay) / math.hypot(bx - ax, by - ay)
    for (side, ahead, rr) in ((-0.9, 0.4, 0.7), (0.9, 0.2, 0.62), (0.0, 0.9, 0.55)):  # the toes
        cx = bx + (ux * ahead - uy * side) * radius
        cy = by + (uy * ahead + ux * side) * radius
        sheet |= disc(cx, cy, radius * rr)
    sheet = {(x, y) for (x, y) in sheet if 0 <= x < W and 0 <= y < H} - set(skip)
    line, run = [], 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(n):
            t = i / n
            line.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, run + math.hypot(x1 - x0, y1 - y0) * t))
        run += math.hypot(x1 - x0, y1 - y0)
    for (x, y) in sheet:
        lx, ly, along = min(line, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        d2 = (lx - x) ** 2 + (ly - y) ** 2
        rope = int(along - d2 / (radius * 1.1) + noise2(x // 4, y // 4, seed) * 1.5) % 6
        c = BASALT[3] if smooth_noise(x, y, 6, seed + 1) > 0.35 else BASALT[2]  # a dull sheen
        if rope == 0:
            c = BASALT[4]  # the lit crest of a rope
        elif rope == 1:
            c = BASALT[2]  # its shaded downstream side
        cv.set(x, y, c)
    for (x, y) in sheet:
        if (x, y - 1) not in sheet:
            cv.set(x, y, MATERIALS['ash'][3] if x % 4 else BASALT[4])  # the lit lip
        elif (x, y + 1) not in sheet:
            cv.set(x, y, BASALT[1])  # the toe
            if (x, y + 1) not in skip and 0 <= y + 1 < H:
                style.darken(cv, x + 1, y + 1)  # its shadow on the ash
        elif (x + 1, y) not in sheet:
            cv.set(x, y, BASALT[2])


def caldera(frame: int = 0):
    """The Ember Caldera: the crater rim at the top with the lava lake glowing beyond,
    a lava river running downhill out of it under a basalt bridge and on south to fill
    Hearthold's moat, plates of cooling crust with glowing seams along its banks, the forge
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
    # old flows, cooled flat on the ash between the newer things
    for (pts, r, sd) in (([(226, 80), (256, 96), (284, 104)], 13, 601),
                         ([(4, 182), (36, 196), (70, 206)], 14, 602),
                         ([(152, 446), (170, 486), (186, 520)], 12, 604)):
        cooled_flow(cv, pts, r, sd)
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
    # the lava river: out of the lake, downhill through the caldera and on south into
    # Hearthold's moat (one course with the moat and the Scorch's channel, fire_lava)
    lake = {(x, y) for x in range(W) for y in range(0, rim(x) + 14)}
    river = paint_lava(cv, 'caldera', frame, lake=frozenset(lake))
    glow_skip = river | lake
    for x in range(0, W, 48):
        light_pool(cv, x + 24, rim(x) + 18, 30, 10, LAVA[1], glow_skip)
    # the mine cart line out of a timbered tunnel in the west wall (the other mouth of
    # the tunnel from Dust Gulch's mine), ending at a buffer on a basalt landing
    wall = {(x, y) for y in range(236, 320) for x in range(0, 34 - abs(y - 278) // 4)}
    for (x, y) in wall:
        band = (y + int(noise2(x // 6, 0, 271) * 3)) // 6
        cv.set(x, y, BASALT[3] if band % 2 else BASALT[2])
        if (x + 1, y) not in wall:
            cv.set(x, y, BASALT[4])
    tunnel = {(x, y) for (x, y) in disc(16, 278, 11) if y < 278} | rect_set_z(5, 278, 23, 22)
    for (x, y) in tunnel:
        cv.set(x, y, '#120C10' if x < 24 else '#22161C')
    landing = rect_set_z(28, 299, CART_STOP - 26, 14)
    for (x, y) in landing:
        basalt_flags(cv, x, y, 272)
    cv.hline(28, 299, CART_STOP - 26, BASALT[4]); cv.hline(28, 313, CART_STOP - 26, BASALT[0])
    for y in range(280, 299):  # the ballast
        for x in range(6, CART_STOP + 6):
            n = noise2(x, y, 141)
            cv.set(x, y, BASALT[2] if n > 0.55 else BASALT[1] if n > 0.15 else BASALT[3])
    for x in range(10, CART_STOP + 4, 5):  # sleepers and the two rails
        cv.vline(x, 284, 12, MATERIALS['wood'][2]); cv.set(x, 284, MATERIALS['wood'][3])
    for ry in (286, 293):
        cv.hline(6, ry, CART_STOP, MATERIALS['iron'][4]); cv.hline(6, ry + 1, CART_STOP, MATERIALS['iron'][2])
    for px in (3, 27):  # the tunnel's timber frame, over the rails
        for y in range(272, 300):
            cv.set(px, y, MATERIALS['wood'][3]); cv.set(px + 1, y, MATERIALS['wood'][1])
    cv.hline(3, 270, 26, MATERIALS['wood'][4]); cv.hline(3, 271, 26, MATERIALS['wood'][2])
    buffer_stop(cv, CART_STOP, 284, heap=BASALT)
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
    # flagstones from the cart landing to the bridge, and down past the forge to the ring
    for (x, y) in (worlds.thick([(CART_STOP + 8, 306), (172, 302)], 7, seed=273)
                   | worlds.thick([(118, 312), (126, 356), (110, 392)], 7, seed=274)
                   | worlds.thick([(96, 428), (112, 476)], 7, seed=275)):
        if (x, y) not in river:
            basalt_flags(cv, x, y, 505)
    # the path down from the ring to the castle's postern bridge
    down = worlds.thick([(122, 522), (128, 552), (130, H + 8)], 8, seed=738)
    for (x, y) in down:
        if (x, y) in river or not (0 <= x < W and 0 <= y < H):
            continue
        ash_flags(cv, x, y, 505)
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
        ('cols-4', 'basalt_columns_low', 262, 220), ('cols-5', 'basalt_columns', 0, 500),
        ('obs-1', 'obsidian', 110, 200), ('obs-2', 'obsidian_small', 238, 326), ('obs-3', 'obsidian', 262, 556 - 26),
        ('obs-4', 'obsidian_small', 60, 230), ('vent-2', 'cooling_vent', 214, 196), ('vent-3', 'cooling_vent', 280, 360),
        ('scree-1', 'scree', 92, 176), ('scree-2', 'scree_small', 206, 90), ('scree-3', 'scree_b', 170, 430),
        ('scree-4', 'scree_small', 176, 546), ('scree-5', 'scree_small', 6, 486),
        ('snag-1', 'charred_snag', 290, 236), ('snag-2', 'charred_snag', 14, 120 + 64), ('snag-3', 'charred_snag', 270, 466),
    ]
    # the bridge is part of the ground (walkable), drawn across the river
    deck = style.finalize(cdp.basalt_bridge(), name='basalt_bridge')
    bx, by = 168, 290
    cv.paste(deck, bx, by)
    span = {(x, y) for x in range(bx, bx + deck.w) for y in range(by + 4, by + 20)}
    blocked = (river | lake) - span
    stands = {'tunnel': (44, 300), 'forge': (68, 404), 'bridge': (200, 302), 'ring': (120, 500), 'rim': (100, 96),
              'east': (290, 300), 'springs': (312, 300), 'castle': (130, 568)}
    return cv, objects, stands, blocked


def springs(frame: int = 0):
    """Cinder Springs, east of the caldera: where the fire country rests. The crater's
    lava lake ends against its rim in the north-west, and that is all the lava here: the
    springs have their own water. It wells up at the top of a staircase of hot-spring
    terraces and runs off the bottom one as a steaming stream, away down the volcano's
    flank past the south edge. The terraces: pools of milky
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
    for (pts, r, sd) in (([(2, 112), (24, 132), (50, 146)], 13, 611),
                         ([(318, 176), (288, 194), (262, 200)], 12, 612),
                         ([(118, 498), (142, 520), (164, 546)], 12, 613)):
        cooled_flow(cv, pts, r, sd)
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
    # the hot stream from the lowest pool, the springs' own outflow: it runs south off
    # the terraces and away down the volcano's flank (it never meets the lava, which
    # keeps to the caldera's side of the rim: Codex's design, section 5), with stepping
    # stones where the bathhouse path crosses it
    stream = worlds.thick([(96, 400), (88, 440), (98, 480), (90, 516), (86, 546), (92, H + 8)], 4, seed=41)
    for (x, y) in stream:
        cv.set(x, y, SPRING[2] if (x + y) % 3 else SPRING[3])
        blocked.add((x, y))
    for (x, y) in stream:
        if (x - 1, y) not in stream:
            cv.set(x - 1, y, TRAV[2])  # a pale mineral lip on its lit bank
        elif (x + 1, y) not in stream and 0 <= x + 1 < W:
            cv.set(x + 1, y, '#C8803A')  # warm mats on the shaded one
    stones = [(92, 462), (95, 470)]
    glow_skip = set(lake)
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
        ('cols-1', 'basalt_columns', 262, 506), ('cols-2', 'basalt_columns_low', 286, 40), ('cols-3', 'basalt_columns_low', 214, 518), ('hiss', 'steam_puff', 78, 526),
        ('vent-1', 'cooling_vent', 150, 60), ('vent-2', 'cooling_vent', 300, 120), ('vent-3', 'cooling_vent', 110, 556 - 20),
        ('obs-1', 'obsidian_small', 20, 470), ('obs-2', 'obsidian', 286, 400),
        ('scree-1', 'scree', 28, 128), ('scree-2', 'scree_small', 196, 70), ('scree-3', 'scree_b', 250, 352),
        ('scree-4', 'scree_small', 40, 504), ('snag-1', 'charred_snag', 226, 84), ('snag-2', 'charred_snag', 4, 190),
        ('snag-3', 'charred_snag', 296, 166),
    ]
    stands = {'caldera': (8, 300), 'pools': (100, 250), 'bath': (250, 494), 'stream': (126, 540), 'slope': (220, 70)}
    return cv, objects, stands, blocked | lake


# The Scorched Pass (Sunstone Reach, east of Dust Gulch and below Hearthold): where the
# desert road from the gulch climbs into the fire country (Matt, 18 Oct: "you go through
# the desert biome and at the end there is a stone bridge underneath which lava flows").
SCORCH_ROAD = [(-12, 384), (40, 384), (130, 378), (166, 330), (172, 200), (164, 90), (160, -8)]


GULCH_PASS = [(136, 360), (190, 368), (250, 378), (W + 12, 384)]


def _distance(src: set, limit: int) -> list:
    """Each pixel's distance (chamfer 3-4, in px, capped at `limit`) to the nearest of
    `src`: two passes over the zone."""
    INF = limit * 3
    d = [[0 if (x, y) in src else INF for x in range(W)] for y in range(H)]
    for y in range(H):
        row, up = d[y], d[y - 1] if y else None
        for x in range(W):
            v = row[x]
            if x and row[x - 1] + 3 < v:
                v = row[x - 1] + 3
            if up:
                if up[x] + 3 < v:
                    v = up[x] + 3
                if x and up[x - 1] + 4 < v:
                    v = up[x - 1] + 4
                if x + 1 < W and up[x + 1] + 4 < v:
                    v = up[x + 1] + 4
            row[x] = v
    for y in range(H - 1, -1, -1):
        row, dn = d[y], d[y + 1] if y + 1 < H else None
        for x in range(W - 1, -1, -1):
            v = row[x]
            if x + 1 < W and row[x + 1] + 3 < v:
                v = row[x + 1] + 3
            if dn:
                if dn[x] + 3 < v:
                    v = dn[x] + 3
                if x + 1 < W and dn[x + 1] + 4 < v:
                    v = dn[x + 1] + 4
                if x and dn[x - 1] + 4 < v:
                    v = dn[x - 1] + 4
            row[x] = v
    return [[min(limit, v // 3) for v in row] for row in d]


def scorch(frame: int = 0):
    """The Scorched Pass: the road in from Dust Gulch at the west edge crosses the lava
    that drains from Hearthold's moat by a small stone bridge, then climbs north to the
    castle's long bridge. The gulch's sand runs in at the west edge and gives out in a
    belt of dry scrub; past it the ground is grey ash and black basalt, and the lava
    always has a collar of ash and cooled crust round it (sand never meets molten rock).
    The drain runs south into a crusted basin where it slows, skins over and cracks into
    glowing plates. The last things standing are charred snags, a sun-bleached skull
    and the cooled tongues of old flows."""
    DESERT, LAVA, BASALT, ASH = (MATERIALS[k] for k in ('desert', 'lava', 'basalt', 'ash'))
    cv = Canvas(W, H)
    ox, oy = FIRE_OFF['scorch']
    molten, crust = fire_lava()
    hot = {(X - ox, Y - oy) for (X, Y) in molten | crust if 0 <= X - ox < W and 0 <= Y - oy < H}
    dist = _distance(hot, 64)
    for y in range(H):
        for x in range(W):
            # sand at the west edge, a belt of scrub, then ash; never sand near the lava
            s = (34 - x) / 22 + (smooth_noise(x, y, 18, 741) - 0.5) * 0.9
            s = min(s, (dist[y][x] - 24) / 10)
            k = smooth_noise(x, y, 30, 745)
            c = ASH[2] if k > 0.3 or (k > 0.26 and (x + y) % 2) else ASH[1]
            if noise2(x, y, 746) > 0.94:
                c = BASALT[2]  # a cinder
            if s > 0.5 or (s > 0.3 and (x + y) % 2):
                c = gulch_sand(W + x, y)  # Dust Gulch's own sand, carried on over the border
            elif s > 0.1 and noise2(x // 2, y // 2, 744) > 0.7:
                c = DESERT[2] if (x + y) % 2 else ASH[3]  # sand blown in among the scrub
            cv.set(x, y, c)
    for i in range(46):  # dry tufts in the scrub belt, each with its small shadow
        x, y = 10 + int(noise2(i, 0, 748) * 40), 6 + int(noise2(i, 1, 748) * (H - 12))
        if dist[y][x] < 26 or 352 < y < 416:
            continue
        for (dx, dy) in ((0, 0), (-1, -1), (1, -1), (0, -2), (-2, -2), (2, -2)):
            cv.set(x + dx, y + dy, MATERIALS['cactus'][1] if dy else MATERIALS['cactus'][0])
        cv.set(x + 1, y + 1, DESERT[1] if x < 24 else ASH[1])
    for (pts, r, sd) in (([(190, 120), (226, 150), (262, 160)], 13, 747),
                         ([(250, 300), (276, 340), (300, 362)], 12, 748)):
        cooled_flow(cv, pts, r, sd)
    for i in range(70):  # cracks in the ash still glowing near the lava
        x, y = int(noise2(i, 0, 749) * W), int(noise2(i, 1, 749) * H)
        if 12 < dist[y][x] < 60 and x > 40:
            for k in range(5):
                cv.set(x + k, y + (k * 7 // 5) % 2, LAVA[1] if k % 2 else BASALT[1])
    channel = paint_lava(cv, 'scorch', frame)
    # the road: the gulch's rutted track over the sand, trodden pale through the scrub
    # and ash to the bridge, then flagged as it climbs to Hearthold
    road = worlds.thick(SCORCH_ROAD, 9, seed=752)
    for (x, y) in road:
        if not (0 <= x < W and 0 <= y < H) or (x, y) in channel:
            continue
        if x < 22:
            n = smooth_noise(x, y, 10, 753)
            c = DESERT[1] if n > 0.35 or (x + y) % 2 else DESERT[2]
            if abs(y - 378) in (5, 6) and noise2(x // 3, y, 229) > 0.2:
                c = DESERT[0]
        elif x < 116:
            n = smooth_noise(x, y, 6, 753)
            c = ASH[3] if n > 0.3 else ASH[4] if (x + y) % 3 else ASH[3]
            if abs(y - 382) in (5, 6) and noise2(x // 3, y, 229) > 0.25:
                c = ASH[2]  # the ruts carry on, fainter
        else:
            ash_flags(cv, x, y, 754)
            continue
        cv.set(x, y, c)
    deck, parapet = stone_bridge(cv, 84, 372, 36, 24, vertical=False)
    objects = [
        ('skull', 'cow_skull', 20, 430), ('weed-1', 'tumbleweed', 14, 320), ('cactus-1', 'saguaro_small', 2, 470),
        ('pear-1', 'prickly_pear', 4, 548), ('snag-1', 'charred_snag', 200, 250), ('snag-2', 'charred_snag', 270, 420),
        ('snag-3', 'charred_snag', 110, 140), ('obs-1', 'obsidian', 224, 470), ('obs-2', 'obsidian_small', 120, 300),
        ('cols-1', 'basalt_columns', 262, 40), ('cols-2', 'basalt_columns_low', 218, 70), ('scree-1', 'scree', 250, 220),
        ('scree-2', 'scree_small', 196, 410), ('lantern-1', 'stone_lantern', 182, 300), ('lantern-2', 'stone_lantern', 150, 150),
        ('vent-1', 'cooling_vent', 284, 500),
        # the scrub belt between the sand and the ash
        ('scrub-1', 'desert_scrub', 14, 238), ('scrub-2', 'desert_scrub_b', 18, 452), ('scrub-3', 'desert_scrub', 8, 120),
        ('scrub-4', 'desert_scrub_b', 22, 512),
    ]
    blocked = ((hot - deck) | parapet)
    stands = {'gulch': (8, 384), 'track': (48, 384), 'bridge': (102, 384), 'castle': (160, 8), 'climb': (170, 250),
              'basin': (232, 440)}
    return cv, objects, stands, blocked


def basalt_flags(cv: Canvas, x: int, y: int, seed: int):
    """One pixel of dark basalt flagstones (the caldera's yards and the way to the springs)."""
    BASALT = MATERIALS['basalt']
    sx = (x + (y // 7) % 2 * 5) // 10
    c = BASALT[3] if noise2(sx, y // 7, seed) > 0.4 else BASALT[2]
    if (x + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
        c = BASALT[0]
    cv.set(x, y, c)


def ash_flags(cv: Canvas, x: int, y: int, seed: int):
    """One pixel of a road of pale ash flags in the fire country: light enough to read
    as the way against the dark ground, with soot in the joints."""
    ASH = MATERIALS['ash']
    sx = (x + (y // 7) % 2 * 5) // 10
    c = ASH[4] if noise2(sx, y // 7, seed) > 0.55 else ASH[3]
    if (x + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
        c = ASH[1]
    elif (x + (y // 7) % 2 * 5) % 10 == 1 or y % 7 == 1:
        c = ASH[4] if c == ASH[3] else c  # the lit edge of each flag
    cv.set(x, y, c)


def stone_bridge(cv: Canvas, x0: int, y0: int, w: int, h: int, vertical: bool = True):
    """A dressed stone bridge seen from above, drawn into the ground: a flagged deck
    between two lit parapets, with the arches' shadow falling on what runs beneath.
    Returns (deck, parapets): the deck is walkable, the parapets are not."""
    ASH = MATERIALS['ashlar']
    deck, parapet = set(), set()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            across = (x - x0) if vertical else (y - y0)
            span = w if vertical else h
            if across < 3 or across >= span - 3:
                parapet.add((x, y))
                c = ASH[5] if across in (0, span - 3) else ASH[3] if across < 3 else ASH[1]
                if (y if vertical else x) % 9 == 0:
                    c = ASH[2]  # the joints between the coping stones
            else:
                deck.add((x, y))
                along = (y - y0) if vertical else (x - x0)
                row = along // 6
                c = ASH[3] if noise2((x + row * 3) // 7, row, 701) > 0.45 else ASH[2]
                if along % 6 == 0 or ((x if vertical else y) + row * 3) % 7 == 0:
                    c = ASH[1]
            cv.set(x, y, c)
    # the arches' shadow on the side away from the light
    if vertical:
        for y in range(y0, y0 + h):
            for d in range(1, 4):
                if 0 <= x0 + w - 1 + d < W:
                    style.darken(cv, x0 + w - 1 + d, y)
    else:
        for x in range(x0, x0 + w):
            for d in range(1, 4):
                if 0 <= y0 + h - 1 + d < H:
                    style.darken(cv, x, y0 + h - 1 + d)
    return deck, parapet


# Hearthold's curtain wall: the band of the isle (as a fraction of its radius) between
# the flagged yard and the cliff, and the two ways through it (x spans).
WALL_IN, WALL_OUT, WALL_FACE = 0.875, 0.965, 10
GATE_GAP, POSTERN_GAP = (146, 177), (91, 112)


def castle(frame: int = 0):
    """Hearthold Castle on its isle in the lava (Matt, 18 Oct: "around the castle is
    lava, perhaps with a dragon flying around"): the caldera's river pours in at the
    north and rings the isle, then drains away south-west into the Scorch. The road from
    the desert comes up from the south and crosses the long stone bridge to the
    gatehouse; a narrow postern bridge on the north side leads up to the caldera. A
    curtain wall runs all the way round the isle's rim (play-test 18 Oct, finding 14:
    no paving runs out to the moat), broken only by the gate and the postern; inside it,
    the keep, the round towers, the bell tower that still rings bedtime, the well and the
    steward's training yard. Nothing green grows this close to the lava: the courtyard
    is flagged, the old herb garden long gone."""
    LAVA, BASALT, ASH = MATERIALS['lava'], MATERIALS['basalt'], MATERIALS['ash']
    ASHLAR = MATERIALS['ashlar']
    cv = Canvas(W, H)
    for y in range(H):  # ash ground with cinders, as in the caldera
        for x in range(W):
            n = smooth_noise(x, y, 30, 731)
            c = ASH[2] if n > 0.3 or (n > 0.26 and (x + y) % 2) else ASH[1]
            g = noise2(x, y, 732)
            if g > 0.94:
                c = BASALT[2]
            elif g > 0.91:
                c = ASH[3]
            cv.set(x, y, c)
    lava = paint_lava(cv, 'hearthold', frame)  # the moat, the river in and the drain out
    ix, iy, irx, iry = ISLE

    def rr(x, y):
        return _superellipse(x, y, ix, iy, irx, iry, 4) ** 0.25

    def gap(x, y):
        return (GATE_GAP[0] <= x < GATE_GAP[1] and y > iy) or (POSTERN_GAP[0] <= x < POSTERN_GAP[1] and y < iy)
    isle = {(x, y) for x in range(W) for y in range(H) if rr(x, y) <= 1}
    rim = {(x, y) for (x, y) in isle if rr(x, y) > WALL_OUT}
    wall = {(x, y) for (x, y) in isle if WALL_IN < rr(x, y) <= WALL_OUT and not gap(x, y)}
    yard = isle - rim - wall
    # the isle's cliff, lit by the lava below it, its foot glowing
    for (x, y) in rim:
        c = BASALT[3] if y < iy else BASALT[2]
        if rr(x, y) > 0.99 and y > iy:
            c = LAVA[1] if (x + y) % 3 else BASALT[1]
        cv.set(x, y, c)
    for (x, y) in yard:  # square flags, each its own tone, lit on top and left (no moss here)
        SL = ['#8C8574', '#A9A28F', '#C2B9A2', '#D4CBB3', '#E6DEC8']
        row = y // 9
        cx, cy = (x + (row % 2) * 6) % 12, y % 9
        t = 3 if noise2((x + (row % 2) * 6) // 12, row, 797) > 0.35 else 2 if noise2((x + (row % 2) * 6) // 12, row, 797) > 0.1 else 4
        c = SL[t]
        if cx == 11 or cy == 8:
            c = SL[0]
        elif cx == 0 or cy == 0:
            c = SL[min(4, t + 1)]
        elif cx == 10 or cy == 7:
            c = SL[t - 1]
        cv.set(x, y, c)
    # the wall walk: a lit coping, merlons standing proud along the outer edge
    for (x, y) in wall:
        r = rr(x, y)
        c = ASHLAR[3] if (x // 7 + y // 6) % 3 else ASHLAR[2]
        if r > WALL_OUT - 0.018:
            c = ASHLAR[5] if (x // 4 + y // 4) % 2 else ASHLAR[1]  # merlons and embrasures
        elif r < WALL_IN + 0.012:
            c = ASHLAR[4]  # the inner coping, catching the light
        cv.set(x, y, c)
    # its faces: the inner one shows below the north wall, the outer one over the cliff
    # below the south wall; dressed blocks in courses, the lowest course in shade
    face = set()
    for (x, y) in wall:
        if (x, y + 1) in wall:
            continue
        for k in range(1, WALL_FACE + 1):
            q = (x, y + k)
            if q in wall or q not in isle or gap(*q):
                break
            if (y < iy and q in yard) or (y > iy and q in rim):
                face.add(q)
                course = (k - 1) // 4
                bx = (x + (7 if course % 2 else 0)) // 9
                c = ASHLAR[2] if noise2(bx, course, 737) > 0.4 else ASHLAR[3]
                if (k - 1) % 4 == 3 or (x + (7 if course % 2 else 0)) % 9 == 0:
                    c = ASHLAR[1]
                if k == WALL_FACE or (y > iy and k > 5):
                    c = ASHLAR[0] if y < iy else BASALT[1]
                cv.set(*q, c)
    for (x, y) in face:  # the face's shadow on the flags at its foot (north wall)
        if (x, y + 1) in yard and (x, y + 1) not in face and y < iy:
            style.darken(cv, x, y + 1); style.darken(cv, x + 1, y + 2)
    for (x, y) in wall:  # the west wall's shadow falls on the yard to its right
        if x < ix and (x + 1, y) in yard and (x + 1, y) not in face:
            for d in range(1, 4):
                if (x + d, y) in yard and (x + d, y) not in face:
                    style.darken(cv, x + d, y)
    for (x0, x1) in (GATE_GAP, POSTERN_GAP):  # the jambs either side of each way through
        for x in (x0 - 1, x1):
            for y in range(H):
                if (x, y) in isle and WALL_IN - 0.03 < rr(x, y) <= WALL_OUT and (y > iy) == (x0 == GATE_GAP[0]):
                    cv.set(x, y, ASHLAR[5] if x == x0 - 1 else ASHLAR[1])
    # the road from the desert up to the south bridge, and the path from the caldera
    # down to the north bridge
    road = worlds.thick([(160, H + 8), (160, H - 40), (162, 452)], 10, seed=737)
    north = worlds.thick([(130, -8), (124, 24), (101, 52)], 8, seed=738)
    for (x, y) in (road | north):
        if (x, y) in lava or not (0 <= x < W and 0 <= y < H):
            continue
        ash_flags(cv, x, y, 739)
    # the bridges: the long one from the south bank to the gatehouse, the postern bridge
    south_deck, south_par = stone_bridge(cv, 146, 392, 30, 66)
    north_deck, north_par = stone_bridge(cv, 89, 50, 24, 70)
    objects = [
        ('tower-nw', 'round_tower', 46, 66), ('wall-n1', 'wall_run', 114, 104), ('tower-ne', 'round_tower', 226, 66),
        ('keep', 'keep', 148, 156), ('bell', 'bell_tower', 54, 168),
        ('well', 'castle_well', 110, 300), ('dummy-1', 'training_dummy', 200, 300), ('rack', 'weapon_rack', 212, 336),
        ('tower-sw', 'round_tower', 50, 232), ('gate', 'gatehouse', 102, 322),
        ('pole-1', 'banner_pole', 128, 466), ('pole-2', 'banner_pole', 180, 466),
        ('lantern-n', 'stone_lantern', 150, 6),
        ('dragon', 'dragon', 196, 132),  # perched on the keep (it flies when motion is on)
    ]
    blocked = ((lava | rim | wall | face) - south_deck - north_deck) | south_par | north_par
    stands = {'scorch': (160, 568), 'bridge': (161, 476), 'gate': (161, 410), 'courtyard': (160, 296),
              'postern': (101, 132), 'caldera': (130, 6)}
    return cv, objects, stands, blocked


def beyond_dunes() -> Canvas:
    """What lies past Dust Gulch and the oasis: open desert, long dunes with a lit crest
    and a shaded lee, wind ripples, a few dry tufts and stones. Its edge drifts a little
    over the zones beside it as blown sand, dithered thin at the tip, so the desert runs
    on instead of stopping at a line (shown round a region shorter or narrower than the
    screen)."""
    S = BEYOND_SPILL
    DESERT = MATERIALS['desert']
    cv = Canvas(W + 2 * S, H + 2 * S)

    def sand(x, y):
        # a dune: its crest line wanders; light rises toward the crest, the lee falls dark
        lx = x + int(smooth_noise(0, y, 60, 781) * 40)
        k = (y + int(math.sin(lx / 23) * 9 + smooth_noise(x, 0, 50, 782) * 18)) % 46
        c = DESERT[3]
        if k < 2:
            c = DESERT[5]  # the crest catches the sun (upper left)
        elif k < 12:
            c = DESERT[4]
        elif k > 38:
            c = DESERT[2]  # the lee, out of the light
        elif k > 34 and (x + y) % 2:
            c = DESERT[2]
        ripple = (y + int(math.sin(x / 8 + y / 37) * 2)) % 7
        if ripple == 0 and 14 < k < 32:
            c = DESERT[4]
        return c

    for y in range(cv.h):
        for x in range(cv.w):
            # distance into the spill: 0 inside the cell, up to S past its edge
            d = max(S - x, x - (W + S - 1), S - y, y - (H + S - 1), 0)
            if d:
                reach = 3 + int(noise2(x // 4, y // 4, 783) * 9)
                if d > reach or (d > reach - 3 and (x + y) % 2):
                    continue
            cv.set(x, y, sand(x, y))
    for i in range(26):  # dry tufts with a shadow to the lower right, and a few stones
        x, y = S + 8 + int(noise2(i, 0, 784) * (W - 16)), S + 8 + int(noise2(i, 1, 784) * (H - 16))
        if i % 3:
            for (dx, dy) in ((0, 0), (-1, -1), (1, -1), (0, -2), (-2, -2), (2, -2)):
                cv.set(x + dx, y + dy, MATERIALS['cactus'][1] if dy else MATERIALS['cactus'][0])
            cv.set(x + 1, y + 1, DESERT[1])
            cv.set(x + 2, y + 1, DESERT[1])
        else:
            for (dx, dy) in ((0, 0), (1, 0), (0, -1), (1, -1)):
                cv.set(x + dx, y + dy, DESERT[1] if dy == 0 else DESERT[3])
            cv.set(x + 2, y + 1, DESERT[2])
    return cv


def beyond_ash() -> Canvas:
    """What lies past the fire country's zones where its grid has a gap: the volcano's
    flank, black basalt in rough steps with ash drifted in the hollows and a few cracks
    still glowing, its edge broken into boulders that spill over the zones beside it
    (as the valley's forest does, so no edge is a straight cut)."""
    S = BEYOND_SPILL
    BASALT, ASH, LAVA = MATERIALS['basalt'], MATERIALS['ash'], MATERIALS['lava']
    cv = Canvas(W + 2 * S, H + 2 * S)
    for y in range(S, H + S):
        for x in range(S, W + S):
            m = 2 + int(noise2(x // 3, y // 3, 761) * 7)
            if min(x - S, W + S - 1 - x, y - S, H + S - 1 - y) < m:
                continue
            step = (y + int(smooth_noise(x, 0, 40, 762) * 30)) // 22
            k = (y + int(smooth_noise(x, 0, 40, 762) * 30)) % 22
            c = BASALT[2] if step % 2 else BASALT[1]
            if k == 0:
                c = BASALT[4]  # the lit lip of a step
            elif k < 3:
                c = BASALT[3]
            elif k > 18:
                c = BASALT[0]
            if smooth_noise(x, y, 14, 763) > 0.68 and k > 3:
                c = ASH[1] if (x + y) % 2 else ASH[2]  # ash drifted in a hollow
            cv.set(x, y, c)
    for i in range(40):
        x, y = S + int(noise2(i, 0, 764) * W), S + int(noise2(i, 1, 764) * H)
        for k in range(6):
            cv.set(x + k, y + (k * 5 // 6) % 2, LAVA[1] if k % 2 else LAVA[2])
    k = 0
    for t in range(0, max(W, H) + 1, 18):  # boulders straddling the edge all round
        for (ex, ey) in ((S + t, S), (S + t, H + S), (S, S + t), (W + S, S + t)):
            if S <= ex <= W + S and S <= ey <= H + S:
                r = 6 + noise2(ex, ey, 765) * 5
                for (x, y) in disc(ex + (noise2(t, ex, 766) - 0.5) * 6, ey + (noise2(t, ey, 766) - 0.5) * 6, r):
                    if 0 <= x < cv.w and 0 <= y < cv.h:
                        dx, dy = x - ex, y - ey
                        cv.set(x, y, BASALT[4] if dx + dy < -r * 0.6 else BASALT[3] if dx + dy < 0 else BASALT[1])
                k += 1
    return cv

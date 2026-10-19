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

__all__ = ['GULCH_STREET', 'sand_share', 'desert_edge', 'scarp_line', 'north_scarp', 'GULCH_CREEK', 'wagon_ruts', 'gulch_sand', 'buffer_stop', 'gulch', 'oasis', 'SPRINGS_PATH',
           'FIRE_OFF', 'LAVA_RIVER', 'LAVA_DRAIN', 'DRAIN_BRIDGE', 'drain_bridge', 'BASIN', 'ISLE', 'MOAT', 'PLINTH', 'fire_lava', 'lava_px', 'paint_lava',
           'caldera_rim', 'cooled_flow', 'caldera', 'springs', 'SCORCH_ROAD', 'GULCH_PASS', 'scorch', 'basalt_flags',
           'ash_flags', 'stone_bridge', 'springs_bridge', 'postern_bridge', 'castle', 'beyond_dunes', 'beyond_ash']


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


GULCH_CREEK = [(-14, 342), (40, 336), (96, 326), (120, 322), (176, 324), (230, 344), (246, 364)]


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


def scarp_line(GX: int):
    """The north scarp at Dust Gulch's x `GX` (the oasis is GX - W): the rim's y and the
    face's height. Its foot wanders in spurs and bays; the face is highest beside the
    mesa and lowers westward, where the dunes have buried most of it."""
    west = max(0.0, min(1.0, -GX / 300))  # 0 in the gulch, 1 at the oasis's west edge
    foot = 28 + int((smooth_noise(GX, 0, 47, 761) - 0.5) * 12 + (smooth_noise(GX, 0, 9, 771) - 0.5) * 3)
    foot = max(20, min(33, foot))
    fh = int(17 - 6 * west + (smooth_noise(GX, 0, 31, 762) - 0.5) * 8)
    fh = max(5, min(foot - 3, fh))
    return foot - fh, fh


def north_scarp(cv: Canvas, ox: int, x_max: int = W) -> set:
    """The north edge of Dust Gulch and the oasis (art-faults.md, rule 13: a natural
    limit drawn inside the zones, not a cut): the rim of a sandstone plateau, a low scarp
    in banded strata above the railway, the mesa's own rock running west from it. On top,
    sand drifted over slabs of the bedrock, running on north into the desert past the
    world; on the face, strata lit along their upper edges, dark streaks of desert
    varnish and cracks; at its foot, blocks fallen from it and a talus of sand. In the
    west the dunes spill over it in tongues of sand. Drawn in the gulch's coordinates
    (`ox`: this zone's x in them), so it runs on across the border. Returns the pixels
    you cannot walk on (the plateau and the face)."""
    DESERT, ADOBE = MATERIALS['desert'], MATERIALS['adobe']
    MESA = ADOBE[:2] + ['#A6704A'] + ADOBE[3:]  # (orange rock that blocks must not read as lava)
    blocked = set()
    for x in range(0, min(W, x_max)):
        GX = x + ox
        rim, fh = scarp_line(GX)
        buried = smooth_noise(GX, 0, 26, 763) > 0.6 + max(0, GX) / 600  # a dune tongue over the face
        for y in range(0, rim):  # the plateau: sand over sandstone slabs
            c = gulch_sand(GX, y)
            if smooth_noise(GX, y, 9, 764) > 0.5 and not buried:
                c = MESA[3] if smooth_noise(GX, y, 4, 765) > 0.45 else MESA[4]  # a slab of the bedrock
                if cracked(GX, y, 7, 6):
                    c = MESA[2]  # its joints
            cv.set(x, y, c)
            blocked.add((x, y))
        for k in range(fh):  # the face
            y = rim + k
            if buried:  # a tongue of sand poured down over the rim, lit on its upper slope
                t = k / fh
                c = DESERT[4] if t < 0.35 else DESERT[3] if t < 0.75 else DESERT[2]
                if k == 0:
                    c = DESERT[5]
                if (GX * 3 + k) % 7 == 0 and 0.2 < t < 0.8:
                    c = DESERT[3] if c == DESERT[4] else DESERT[2]  # ripples running down it
            else:
                wob = int(noise2(GX // 9, 3, 766) * 3)
                band = (k + wob) // 4
                c = MESA[2] if band % 2 else MESA[1]
                if (k + wob) % 4 == 0:
                    c = MESA[3]  # each stratum lit along its upper edge
                if k == 0:
                    c = DESERT[5]  # the sunlit rim
                elif k == 1:
                    c = MESA[4]
                elif k >= fh - 2:
                    c = MESA[0]  # the foot, in its own shade
                if noise2(GX // 3, 0, 767) > 0.7 and 2 < k < 3 + int(noise2(GX // 3, 1, 767) * fh):
                    c = MESA[1] if k < fh - 3 else MESA[0]  # desert varnish streaking down
            cv.set(x, y, c)
            blocked.add((x, y))
        foot = rim + fh
        talus = 2 + int(smooth_noise(GX, 1, 11, 768) * 4) + (3 if buried else 0)
        for k in range(talus):  # sand banked at its foot, then the face's shadow on it
            y = foot + k
            if y >= 36:
                break
            c = DESERT[4] if k < talus - 1 else DESERT[3]
            if not buried and k < 2:
                c = DESERT[2] if (x + k) % 2 else DESERT[1]  # in the face's shadow
            cv.set(x, y, c)
    for i in range(30):  # blocks fallen from the face, lying at its foot
        x = int(noise2(i, 0, 769) * min(W, x_max))
        rim, fh = scarp_line(x + ox)
        y = rim + fh + 1 + int(noise2(i, 1, 769) * 3)
        if y < 35:
            detail.pebble(cv, x, y, MESA, big=i % 3 == 0)
    for i in range(24):  # dry grass on the plateau
        x = int(noise2(i, 0, 770) * min(W, x_max))
        rim, _fh = scarp_line(x + ox)
        if rim > 5:
            y = 2 + int(noise2(i, 1, 770) * (rim - 4))
            detail.grass_tuft(cv, x, y, i % 6, ['#5A4A2A', '#7A6436', '#9A8044', '#B89A58', '#D2B672'], 2)
    return blocked


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
            cv.set(x, y, desert_edge(x, y) if x > W - 180 else gulch_sand(x, y))
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
            cv.set(x, y, desert_edge(x, y) if x > W - 180 else gulch_sand(x, y))
    buffer_stop(cv, MESA_X0 - 22, 38)
    scarp = north_scarp(cv, 0, MESA_X0 - 4)
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
    flags = set()
    for (x, y) in pass_track:
        if 0 <= x < W and 0 <= y < H and (x, y) not in street:
            n = smooth_noise(x, y, 10, 213)
            if x < W - 48 + int(smooth_noise(x, y, 4, 773) * 18):
                cv.set(x, y, DESERT[2] if n > 0.3 or (x + y) % 2 else DESERT[1])
            else:  # where it reaches the ash it becomes the laid road up to Hearthold, its
                ash_flags(cv, x, y, 754)  # first flags half buried in drifted sand
                if x < W - 24 and smooth_noise(x, y, 3, 774) > 0.55:
                    cv.set(x, y, DESERT[3] if smooth_noise(x, y, 2, 775) > 0.5 else DESERT[2])
                else:
                    flags.add((x, y))
    road_edges(cv, flags)
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
    for (x0, y0, w0) in ((6, 186, 108), (150, 286, 88)):
        for y in range(y0, y0 + 8):
            for x in range(x0, x0 + w0):
                cv.set(x, y, BLEACHED[3] if (x // 6) % 2 else BLEACHED[2])
        cv.hline(x0, y0, w0, BLEACHED[5]); cv.hline(x0, y0 + 8, w0, BLEACHED[0])
    # worn ground where feet leave the boardwalks: before the saloon's door, and off the
    # boardwalk's east end onto the street (review 19 Oct: the door had no way to the road)
    for (cx, cy, rx, ry) in ((58, 198, 16, 6), (116, 192, 12, 8)):
        for (x, y) in oval(cx, cy, rx, ry):
            if (x, y) not in street and smooth_noise(x, y, 3, 231) > 0.3:
                cv.set(x, y, DESERT[2] if (x + y) % 3 else DESERT[1])
    for t in range(10):  # boot prints from the door
        cv.set(54 + (t % 2) * 6, 196 + t, DESERT[1])
    # the plank bridge where the street crosses the dry bed
    for y in range(296, 346):
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
    def east_end(y):
        """Where the mesa's east end stands at row y: not a straight cut on the border but
        buttresses and bays, the rock broken back where it has fallen."""
        return MESA_X1 - int(smooth_noise(0, y, 11, 776) * 12) - (3 if (y // 17) % 3 == 1 else 0)
    for y in range(0, rim(MESA_X1 - 1) + FACE_H):  # the east end, in shade, and its shadow
        e = east_end(y)
        for x in range(e, MESA_X1 + 5):  # ground where the rock has broken back
            cv.set(x, y, desert_edge(x, y))
            mesa.discard((x, y))
        for k in range(5):
            x = e + k
            c = MESA[1] if (y // 5 + k) % 3 else MESA[0]
            if k == 0 and east_end(y - 1) < e:
                c = MESA[3]  # the top of a buttress, catching the light
            cv.set(x, y, c)
            mesa.add((x, y))
        for d in range(5, 10):
            if smooth_noise(e + d, y, 2, 777) > 0.35 or d < 7:
                style.darken(cv, e + d, y)
        if noise2(y // 3, 0, 778) > 0.8:  # talus fallen from it
            detail.pebble(cv, e + 6 + int(noise2(y, 1, 778) * 6), y, MESA, big=y % 2 == 0)
    for x in range(MESA_X0, MESA_X1):  # desert varnish: dark streaks run down from the rim
        if noise2(x // 3, 0, 232) > 0.62:
            top = rim(x)
            for k in range(2, 4 + int(noise2(x // 3, 1, 232) * 14)):
                if (x + k) % 3:
                    cv.set(x, top + k, MESA[1] if k < 10 else MESA[0])
    for i in range(7):  # a few cracks down the face, lit on their left
        x = MESA_X0 + 6 + int(noise2(i, 0, 233) * (MESA_X1 - MESA_X0 - 12))
        if abs(x - CART_X - 5) < 20:
            continue
        top = rim(x)
        for k in range(2, FACE_H - 2):
            xx = x + (k // 7) % 2
            cv.set(xx, top + k, MESA[0]); cv.set(xx - 1, top + k, MESA[3])
    for i in range(16):  # blocks fallen from the face, lying in its shadow
        x = MESA_X0 + int(noise2(i, 0, 234) * (MESA_X1 - MESA_X0))
        if abs(x - CART_X - 5) < 24:
            continue
        y = rim(x) + FACE_H + 2 + int(noise2(i, 1, 234) * 7)
        detail.pebble(cv, x, y, MESA, big=i % 3 == 0)
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
        ('saloon', 'saloon', 6, 78), ('hitch-1', 'hitching_rail', 66, 178), ('poster', 'poster_board', 150, 86),
        ('store', 'store', 150, 178), ('keg-1', 'keg', 100, 290), ('keg-2', 'keg', 104, 280),
        ('tower', 'water_tower', 250, 196), ('pump', 'windpump', 30, 226 + 100), ('trough', 'trough', 14, 224),
        ('well', 'dry_well', 58, 360), ('wagon', 'wagon', 16, 470), ('hay-1', 'hay_bale', 122, 524), ('hay-2', 'hay_bale', 108, 538),
        ('dyn-1', 'dynamite_crate', CART_X + 20, MINE_Y + 8),
        ('dyn-2', 'dynamite_crate', CART_X + 26, MINE_Y + 30), ('tub', 'ore_tub', CART_X - 5, MINE_Y + 10),
        ('keg-f', 'keg', MESA_X0 - 30, 100), ('sack-f', 'hay_bale', 60, 60),
        ('corral-n', 'corral_rail', ccx - 46, ccy - 36), ('corral-s', 'corral_rail', ccx - 46, ccy + 22),
        ('corral-w', 'corral_side', ccx - 52, ccy - 22), ('corral-e', 'corral_gate', ccx + 14, ccy - 22),
        ('cactus-1', 'saguaro', 10, 380), ('cactus-2', 'saguaro_small', 224, 400), ('cactus-3', 'saguaro', 150, 520),
        ('cactus-4', 'saguaro_small', 286, 540), ('cactus-5', 'saguaro', 276, 4),
        ('cactus-7', 'saguaro', 244, 330), ('weed-1', 'tumbleweed', 170, 380),
        # scrub where the sand gives out into the ash, in clumps
        ('scrub-1', 'desert_scrub', 296, 262), ('scrub-2', 'desert_scrub_b', 270, 318), ('scrub-3', 'desert_scrub', 286, 410), ('weed-2', 'tumbleweed', 96, 562),
        ('skull', 'cow_skull', 250, 520), ('barrel-p', 'keg', 40, 62), ('sack-p', 'hay_bale', 196, 56),
        # life (S5): a saddled grey tied nose to the saloon's rail (the corral's bay dozes
        # side-on); vultures waiting in a dead mesquite above the skull in the dry scrub; a
        # lizard basking on warm sandstone
        ('horse-rail', 'horse_tied', 76, 181), ('vultures', 'snag_vultures', 258, 452), ('lizard', 'lizard_rock', 34, 528),
        ('horse', 'horse', ccx - 30, ccy - 24), ('pear-1', 'prickly_pear', 234, 472), ('pear-2', 'prickly_pear', 280, 426),
        ('pear-3', 'prickly_pear', 200, 548),
    ]
    stands = {'platform': (128, 70), 'saloon': (58, 200), 'street': (132, 260), 'corral': (190, 470),
              'oasis': (12, 524), 'mine': (CART_X - 14, CART_END + 12), 'well': (75, 404), 'pass': (312, 384),
              'forecourt': (190, 100)}
    return cv, objects, stands, mesa | scarp


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
        """The pool's shore at angle `a` (no oval, art-faults rule 3): a deep bay to the
        north-west where the spring wells, a shallow tongue reaching east toward the old
        outlet, a straighter south shore where the steps were built, and small coves."""
        return (1 + 0.12 * math.sin(2 * a + 2.4) + 0.09 * math.sin(3 * a + 0.6) + 0.06 * math.sin(5 * a + 1.9)
                + 0.035 * math.sin(8 * a + 0.3) + 0.02 * math.sin(13 * a + 1.1))

    def pool_d(x, y):  # 1 on the shore, less inside; the rings round the pool follow its shape
        a = math.atan2((y - PCY) / 34, (x - PCX) / 62)
        return math.hypot((x - PCX) / 62, (y - PCY) / 34) / pool_r(a)
    pool = {(x, y) for y in range(PCY - 56, PCY + 56) for x in range(PCX - 90, PCX + 90) if pool_d(x, y) < 1}
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
        r *= pool_r(math.atan2(math.sin(a), math.cos(a)))
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
    scarp = north_scarp(cv, -W)
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
        ('palm-4', 'palm', 168, 226), ('palm-5', 'palm_small', 60, 318), ('palm-6', 'palm', 150, 334),
        ('palm-7', 'palm_small', 196, 260), ('papyrus-1', 'papyrus', 52, 266), ('papyrus-2', 'papyrus', 160, 288),
        ('papyrus-3', 'papyrus', 98, 316), ('shaduf', 'shaduf', 158, 256), ('jar-1', 'water_jar', 140, 344),
        ('jar-2', 'water_jar', 152, 350),
        # the railway's water crane, fed from the spring
        ('crane', 'water_crane', 84, 52),
        # the caravan camp where the track ends
        ('tent', 'tent', 238, 420), ('camel-1', 'camel', 212, 480), ('camel-2', 'camel_b', 268, 498),
        ('fire', 'fire_pit', 260, 460), ('awning', 'awning', 240, 360), ('jar-3', 'water_jar', 228, 386),
        # the older town
        ('arch', 'sandstone_arch', 26, 450), ('col-1', 'column_stump', 92, 470), ('col-2', 'column_stump_b', 92, 500),
        ('col-3', 'column_stump_b', 10, 500),
        # out in the dunes
        ('cactus-1', 'saguaro_small', 286, 118), ('skull', 'cow_skull', 180, 540), ('weed', 'tumbleweed', 40, 150),
        ('weed-2', 'tumbleweed', 250, 220), ('acacia-1', 'acacia', 226, 84), ('acacia-2', 'acacia', 4, 92),
        ('scrub-1', 'desert_scrub', 128, 140), ('scrub-2', 'desert_scrub_b', 196, 448), ('scrub-3', 'desert_scrub', 184, 420),
        ('scrub-4', 'desert_scrub_b', 288, 300), ('rocks-1', 'sandstone_outcrop', 140, 505),
        ('rocks-2', 'lizard_rock_b', 256, 170),
        # a string of laden camels near the water, tethered nose to tail to a stake on open
        # sand below the grove (review 19 Oct: no palm inside the string)
        ('camels', 'camel_string', 4, 370),
    ]
    stands = {'gulch': (312, 524), 'pool': (130, 352), 'camp': (250, 500), 'arch': (58, 500),
              'crane': (110, 76), 'dunes': (200, 140)}
    return cv, objects, stands, pool | scarp


SPRINGS_PATH = [(-6, 300), (40, 316), (52, 380), (56, 436), (78, 457), (124, 458), (150, 472), (190, 486), (250, 488)]


# The fire country's lava is one course (Codex's connected-world design, section 5):
# out of the crater lake, down through the caldera, round Hearthold's rock and away
# through the Scorched Pass into a crusted basin. It is drawn in the caldera's
# coordinates; each zone paints the part that crosses it (FIRE_OFF: the zone's top left
# in those coordinates), so colour, crust and glow run on across every border.
FIRE_OFF = {'caldera': (0, 0), 'springs': (W, 0), 'hearthold': (0, H), 'scorch': (0, 2 * H)}
LAVA_RIVER = [(170, 60), (178, 140), (160, 230), (200, 320), (236, 400), (234, 470), (228, 540),
              (226, H + 30), (218, H + 66)]                       # the caldera into the moat
# the moat into the basin: (x, y, half-width). It meanders the way a lava channel does on
# a gentle slope, swinging from side to side and widest on the outside of each bend,
# where it has eaten into the bank; it runs straight and narrow only where the road's
# bridge crosses it, which is where the builders would have put the bridge (note
# to-d-after-61, 19 Oct)
LAVA_DRAIN = [(48, H + 396, 11), (40, H + 440, 12), (56, H + 498, 13), (46, H + 552, 11),
              (52, 2 * H + 10, 11), (66, 2 * H + 58, 13), (50, 2 * H + 112, 15), (60, 2 * H + 162, 11),
              (86, 2 * H + 206, 14), (80, 2 * H + 252, 11), (66, 2 * H + 294, 14), (88, 2 * H + 338, 10),
              (99, 2 * H + 364, 9), (101, 2 * H + 404, 9), (114, 2 * H + 430, 12), (110, 2 * H + 444, 11)]
DRAIN_BRIDGE = (372, 22)           # the road's bridge over the drain in the Scorched Pass: its top row and depth
BASIN = (138, 2 * H + 496, 64, 40)  # the crusted basin in the Scorched Pass: centre and radii
ISLE = (160, 254, 116, 150)        # Hearthold's isle in the lava (its own coordinates)
MOAT = (152, 250, 138, 192)        # the moat's outer edge
PLINTH = 6                         # the isle's footing of crust and basalt between the lava and the cliff
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


def _course_w(points, seed: int) -> set:
    """_course with its own half-width at each point, eased between them, so a channel
    can widen on a bend and narrow on a straight."""
    pts = set()
    for (x0, y0, r0), (x1, y1, r1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            e = t * t * (3 - 2 * t)
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = r0 + (r1 - r0) * e + (smooth_noise(cx, cy, 9, seed) - 0.5) * 2.4
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
    # the isle stands on a footing of cooled crust and basalt blocks (PLINTH px wide), so
    # the lava never laps the masonry itself
    moat = {(x, y + H) for x in range(W) for y in range(H)
            if _superellipse(x, y, mx, my, mrx, mry, 3) <= 1
            and _superellipse(x, y, ix, iy, irx + PLINTH, iry + PLINTH, 4) > 1}
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
    isle = {(x, y + H) for x in range(W) for y in range(H)
            if _superellipse(x, y, ix, iy, irx + PLINTH, iry + PLINTH, 4) <= 1}
    river = (_course(LAVA_RIVER, 12, 14) | _course_w(LAVA_DRAIN, 734)) - isle
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


def fire_ash(X: int, Y: int) -> str:
    """The fire country's ground at a point in its own coordinates: grey ash, gently
    darker in the hollows, with cinders and pale flecks. One painter for the caldera,
    the springs, Hearthold and the Scorched Pass, so the ground runs on across their
    borders with no change at a tile edge (art-faults.md, rule 1)."""
    ASH, BASALT = MATERIALS['ash'], MATERIALS['basalt']
    n = smooth_noise(X, Y, 30, 261)
    c = ASH[2] if n > 0.3 or (n > 0.26 and (X + Y) % 2) else ASH[1]
    g = noise2(X // 2, Y, 270)  # two pixels wide, so they hold up at the phone's scale
    if g > 0.965:
        c = BASALT[2]  # a cinder
    elif g > 0.95:
        c = ASH[3]
    return c


def sand_share(GX: int, GY: int, heat: float = 0.0) -> float:
    """How much of Dust Gulch's sand there is at a point (gulch coordinates; the Scorched
    Pass is GX - W): 1 deep in the desert, 0 in the fire country's ash. The front where
    the ash gives out runs slantwise across the gulch/pass border, not along it (from
    well inside the gulch under the mesa in the north to past the border in the south,
    where the drain's basin is), and wanders; the change takes about 90 px. `heat`
    (0..1) pushes it toward ash near the lava, which always keeps a collar of ash."""
    xb = W - 40 + (GY - 288) * 0.3 + (smooth_noise(0, GY, 70, 745) - 0.5) * 40
    s = (xb - GX) / 210 + 0.5 + (smooth_noise(GX, GY, 40, 741) - 0.5) * 0.3 + (smooth_noise(GX, GY, 12, 742) - 0.5) * 0.12
    return s - heat


def desert_edge(GX: int, GY: int, heat: float = 0.0) -> str:
    """The ground where Dust Gulch's sand gives out into the fire country (sand_share):
    sand, then a belt where scrub grows and sand is blown in among the ash, then ash,
    dithered where they meet, so no change lines up with a border (art-faults rule 1)."""
    s = sand_share(GX, GY, heat)
    grain = smooth_noise(GX, GY, 3, 746)  # small soft patches where they meet, not a checker
    if s + (grain - 0.5) * 0.16 > 0.62:
        return gulch_sand(GX, GY)
    if s > 0.3:  # the belt: drifts of sand lying in the ash, thinning toward the fire country
        drift = smooth_noise(GX, GY, 7, 744) + (s - 0.3) * 1.4 + (grain - 0.5) * 0.12
        if drift > 0.9:
            return gulch_sand(GX, GY)
        if drift > 0.8:
            return MATERIALS['desert'][2] if grain > 0.5 else MATERIALS['ash'][3]  # sand blown thin
    return fire_ash(GX - W, GY + 2 * H)


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
        if all((X + d, Y - 1) not in hot and (X + d, Y - 1) not in crust for d in (-1, 0, 1)):
            # the lit upper bank, only where the bank above runs across (a bank running down
            # the channel's side would leave a straight dotted line of light in the lava)
            cv.set(x, y, LAVA[5] if (X, Y) in molten else BASALT[4])
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
            cv.set(x, y, fire_ash(x, y))
    for i in range(200):
        x, y = int(noise2(i, 0, 262) * W), int(noise2(i, 1, 262) * H)
        detail.pebble(cv, x, y, BASALT, big=i % 4 == 0)
    # old flows, cooled flat on the ash between the newer things
    # (review 19 Oct: the two tongues lying west of the cart line and south of the shrine
    # read as grey worms, so only the one under the rim, where the lake once overflowed, stays)
    for (pts, r, sd) in (([(226, 80), (256, 96), (284, 104)], 13, 601),):
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
    # the forge yard: a laid apron of basalt flags in front of the smithy, square to its
    # front and as wide as it, its outer edge ragged where flags have sunk or gone (review
    # 19 Oct: not a rounded blob)
    yard = {(x, y) for x in range(14, 128) for y in range(396, 428)
            if not ((x < 18 or x > 123 or y > 423) and noise2(x // 5, y // 4, 268) > 0.45)}
    for (x, y) in yard:
        if (x, y) not in river:
            basalt_flags(cv, x, y, 269)
    # the forge's shadow, down and to the right of it (forge sprite at 20, 320, 96 x 80)
    for y in range(338, 404):
        for x in range(116, 116 + min(9, (y - 330) // 4)):
            if (x, y) not in river:
                style.darken(cv, x, y)
                if x < 116 + min(5, (y - 330) // 6):
                    style.darken(cv, x, y)  # deeper near the wall
    for x in range(20, 126):  # and its foot's shadow along the yard below the step
        for y in (400, 401):
            style.darken(cv, x + (y - 400) + 2, y)
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
    ash_dressing(cv, glow_skip | yard | landing | east_path | down | {(x, y) for y in range(270, 320) for x in range(0, CART_STOP + 30)}
                 | {(x, y) for (x, y) in oval(120, 500, 60, 32)}, 793, 110, *FIRE_OFF['caldera'])
    # the sparring ring: crust floor in a circle of short columns
    ccx, ccy = 120, 500
    def in_ring(x, y):  # the crust floor's outline: worn and slumped, not drawn with compasses
        a = math.atan2((y - ccy) / 22, (x - ccx) / 46)
        r = 1 + 0.09 * math.sin(3 * a + 0.7) + 0.06 * math.sin(5 * a + 2.1) + (smooth_noise(a * 12, 0, 6, 276) - 0.5) * 0.14
        return math.hypot((x - ccx) / 46, (y - ccy) / 22) < r
    ring_floor = {(x, y) for y in range(ccy - 28, ccy + 29) for x in range(ccx - 56, ccx + 57) if in_ring(x, y)}
    for (x, y) in ring_floor:
        cv.set(x, y, ASH[1] if not cracked(x, y, 9, 5) else LAVA[1])
    posts = []
    for k in range(14):  # short columns set round it, each its own height, a gap left at the south for the path
        a = 2 * math.pi * k / 14
        if abs(a - math.pi / 2) < 0.3:
            continue
        posts.append((int(ccy + 26 * math.sin(a)), int(ccx + 52 * math.cos(a)), k))
    for (py, px, k) in sorted(posts):
        cdp._column(cv, px, py - 4 - int(noise2(k, 0, 742) * 5), py + 4, 4.6, 900 + k, False, broken=k % 5 == 2)
    objects = [
        ('forge', 'forge', 20, 320), ('shrine', 'ember_shrine', 150, 360), ('vent-1', 'cooling_vent', 40, 460),
        # basalt columns where the lava once cooled slowly: a stepped formation under the
        # crater rim in the north-west, and another against the west wall by the tunnel
        ('cols-1', 'basalt_steps', 2, 88), ('cols-2', 'basalt_stumps', 74, 136),
        ('cols-3', 'basalt_columns', 266, 106), ('cols-4', 'basalt_columns_b', 230, 120),
        ('cols-5', 'basalt_stack', 2, 470),
        # obsidian where lava met the air and froze glassy: on the river's banks
        ('obs-1', 'obsidian', 110, 204), ('obs-2', 'obsidian_small', 238, 340), ('obs-3', 'obsidian', 258, 452),
        ('obs-4', 'obsidian_small', 140, 236),
        # the vents steam on the upper slope under the rim
        ('vent-2', 'cooling_vent', 214, 168), ('vent-3', 'cooling_vent', 262, 196),
        # scree fallen from the rim, at the foot of the columns
        ('scree-1', 'scree', 92, 170), ('scree-2', 'scree_small', 206, 92), ('scree-3', 'scree_b', 170, 430),
        ('scree-4', 'scree_small', 176, 546), ('scree-5', 'scree_small', 30, 486),
        # a stand of trees the old flows burnt, together on the south-east slope
        ('snag-1', 'charred_snag', 268, 380), ('snag-2', 'charred_snag', 290, 404), ('snag-3', 'charred_snag', 262, 418),
        ('tub', 'ore_tub', CART_STOP - 34, 282),  # a tub waiting at the buffer
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
    terraces and runs off the bottom one as a steaming stream, under the path's footbridge
    and into a fissure in an old flow, where it sinks. The terraces: pools of milky
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
            cv.set(x, y, fire_ash(x + W, y))
    for i in range(140):
        x, y = int(noise2(i, 0, 500) * W), int(noise2(i, 1, 500) * H)
        detail.pebble(cv, x, y, BASALT, big=i % 4 == 0)
    for (pts, r, sd) in (([(2, 112), (24, 132), (50, 146)], 13, 611),
                         ([(318, 176), (288, 194), (262, 200)], 12, 612)):
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
    # the terraces (Mammoth Hot Springs and Pamukkale build them this way: the water
    # drops travertine where it cools, so every pool is held by a lip it built itself):
    # a small, hottest source pool at the top, ringed with orange and yellow mats; a wide
    # shallow pool below it, its floor stepped by little rimstone dams; a pair side by
    # side, one a step lower than the other; and the broad, coolest pool at the foot,
    # greener where algae grow, which spills into the stream. Each has its own shape,
    # size and fall, so none is a copy of another.
    pools = [  # (cx, cy, rx, ry, seed, ramp)
        (238, 140, 30, 15, 1, 'hot'), (196, 214, 62, 21, 2, 'warm'), (148, 292, 42, 18, 3, 'warm'),
        (214, 306, 22, 11, 4, 'warm'), (128, 372, 48, 22, 5, 'cool')]
    RAMPS = {'hot': ['#0B3A4A', '#126474', '#2A98A8', '#64C6C8', '#B4ECE6'],
             'warm': SPRING,
             'cool': ['#164840', '#22705E', '#3E9C84', '#7CC6AA', '#C2EAD6']}
    DROP = [4, 9, 6, 5, 8]  # how far each lip falls to the slope below

    def pool_d(i, x, y):
        cx, cy, rx, ry, sd, _r = pools[i]
        a = math.atan2((y - cy) / ry, (x - cx) / rx)
        wob = (1 + 0.1 * math.sin(2 * a + sd * 1.3) + 0.07 * math.sin(3 * a + sd * 2.1)
               + 0.05 * math.sin(5 * a + sd * 0.7) + 0.03 * math.sin(9 * a + sd))
        if math.sin(a) > 0.2:  # the downhill lip is scalloped where the water spills over it
            wob += 0.035 * math.sin(a * (13 + sd % 4)) * math.sin(a)
        return math.hypot((x - cx) / rx, (y - cy) / ry) / wob
    pool_sets = [{(x, y) for y in range(cy - ry - 8, cy + ry + 8) for x in range(cx - rx - 10, cx + rx + 10)
                  if pool_d(i, x, y) < 1} for i, (cx, cy, rx, ry, _s, _r) in enumerate(pools)]
    spills = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)]
    sinter = set()
    for i, (cx, cy, rx, ry, sd, _r) in enumerate(pools):  # one mineral slope under them all
        sinter |= {(x, y) for y in range(cy - ry - 22, cy + ry + 28) for x in range(cx - rx - 24, cx + rx + 24)
                   if pool_d(i, x, y - 5) < 1.35 + smooth_noise(x, y, 9, 506) * 0.3}
    for (i, j) in spills:
        sinter |= worlds.thick([pools[i][:2], pools[j][:2]], 18 if i else 14, seed=44 + i * 3 + j)
    for (x, y) in sinter:
        n = smooth_noise(x, y, 6, 501)
        c = TRAV[3] if n > 0.55 else TRAV[2] if n > 0.25 else TRAV[1]
        if noise2(x // 2, y, 509) > 0.93:
            c = TRAV[4]  # a fresh white crust
        elif noise2(x // 3, y // 2, 510) > 0.95:
            c = '#C8A070'  # a stain of iron
        cv.set(x, y, c)
    for (x, y) in sinter:  # its edge on the ash, a soft stained margin
        if any((x + dx, y + dy) not in sinter for (dx, dy) in ((0, 3), (3, 0), (-3, 0), (0, -3))):
            cv.set(x, y, '#9A7A52' if (x + y) % 2 else TRAV[1])
    # the faces under each lip, like frozen falls: streaked cream and ochre, lit along
    # the lip, darker at the foot, the drop its own height for each pool
    for (i, (cx, cy, rx, ry, sd, _r)) in enumerate(pools):
        pool = pool_sets[i]
        for x in range(cx - rx - 10, cx + rx + 10):
            ys = [y for (xx, y) in pool if xx == x]
            if not ys:
                continue
            yb = max(ys)
            drop = DROP[i] + int(noise2(x // 3, i, 507) * 5)
            for k in range(drop):
                streak = (x * 3 + int(noise2(x, 0, 502 + i) * 4)) % 5
                c = TRAV[4] if k < 2 else TRAV[3] if streak < 2 else TRAV[2] if streak < 4 else '#C8803A'
                if k == drop - 1:
                    c = TRAV[1]
                cv.set(x, yb + 1 + k, c)
            for k in range(2):  # the face's shadow on the slope below
                if (x, yb + 1 + drop + k) in sinter and (x + k) % 2 == 0:
                    style.darken(cv, x + 1, yb + 1 + drop + k)
    # the spills: a thread of water out over each lower lip and down the face to the next
    for (i, j) in spills:
        (cx, cy, rx, ry, sd, _r), (nx, ny, nrx, nry, _s2, _r2) = pools[i], pools[j]
        ang = math.atan2(ny - cy, nx - cx)
        sx, sy = cx + math.cos(ang) * rx * 0.85, cy + math.sin(ang) * ry * 0.85
        tx, ty = nx - math.cos(ang) * nrx * 0.7, ny - math.sin(ang) * nry * 0.7
        n = int(max(abs(tx - sx), abs(ty - sy))) + 1
        for t in range(n + 1):
            x = int(sx + (tx - sx) * t / n + math.sin(t / 5 + i) * 1.5)
            y = int(sy + (ty - sy) * t / n)
            if any((x, y) in ps for ps in pool_sets):
                continue
            for dx in range(-1, 2):
                cv.set(x + dx, y, SPRING[3] if dx < 1 else SPRING[2])
                blocked.add((x + dx, y))
            cv.set(x - 2, y, TRAV[4]); cv.set(x + 2, y, TRAV[2])
    for (i, (cx, cy, rx, ry, sd, ramp)) in enumerate(pools):
        pool, R = pool_sets[i], RAMPS[ramp]
        for (x, y) in pool:
            d = pool_d(i, x, y)
            c = R[1] if d < 0.42 else R[2] if d < 0.72 else R[3]
            if d > 0.86:
                if ramp == 'hot':
                    c = '#E8A23A' if (x + y) % 3 else '#D8C048'  # mats: orange where cooler, yellow nearer the heat
                elif ramp == 'cool' and smooth_noise(x, y, 5, 511) > 0.55:
                    c = '#8A9A4A' if (x + y) % 2 else '#6E8A44'  # algae in the cool shallows
                else:
                    c = R[4] if (x + y) % 2 else TRAV[4]  # the lip
            elif ramp == 'warm' and i == 1 and (0.5 < d < 0.57 or 0.74 < d < 0.8) and y > cy - ry * 0.3 \
                    and smooth_noise(x, y, 4, 513) > 0.3:
                c = TRAV[3] if (x // 2 + y) % 3 else TRAV[4]  # rimstone dams stepping the floor, in arcs
            if (x, y - 1) not in pool or (x, y - 2) not in pool:
                c = TRAV[1]  # the lip's shadow on the water
            cv.set(x, y, c)
            blocked.add((x, y))
        for k in range(4 + i % 3):  # still glints
            gx, gy = cx - rx // 2 + int(noise2(k, i, 503) * rx), cy - ry // 2 + int(noise2(k, i, 504) * ry)
            if (gx, gy) in pool and (gx + 3, gy) in pool and pool_d(i, gx, gy) < 0.8:
                cv.hline(gx, gy, 2 + k % 3, R[4])
    hx, hy = pools[0][0] + 4, pools[0][1] + 1  # the source: water welling up, rings round the vent
    for (x, y) in oval(hx, hy, 5, 3):
        cv.set(x, y, RAMPS['hot'][0])
    for (x, y) in oval(hx, hy, 9, 5):
        if (x, y) in pool_sets[0] and not (x, y) in oval(hx, hy, 7, 4) and (x + y) % 2:
            cv.set(x, y, RAMPS['hot'][3])
    # sulphur crusts round the fumaroles on the upper slope
    for (vx, vy) in ((162, 80), (312, 140)):
        for (x, y) in oval(vx, vy, 18, 9):
            if noise2(x // 2, y // 2, 508) > 0.45:
                cv.set(x, y, '#E8D24A' if (x + y) % 3 else '#B8A030')
    # the old flow at the foot of the slope, where the stream ends: it sinks into a
    # fissure where the flow's crust cracked as it cooled (water sinks into porous
    # basalt; it never meets the lava, which keeps to the caldera's side of the rim)
    cooled_flow(cv, [(30, 508), (62, 530), (104, 546), (138, 552)], 13, 613)
    fissure = set()
    for t in range(52):
        fx = 70 + t
        fy = 536 + int(t * 0.28 + math.sin(t / 4) * 1.6)
        wdt = 1 + (2 if 6 < t < 30 else 1 if t < 44 else 0)
        for k in range(-wdt, wdt + 1):
            fissure.add((fx, fy + k))
    for (x, y) in fissure:
        cv.set(x, y, '#0C0A0E' if (x, y + 1) in fissure else BASALT[1])
        if (x, y - 1) not in fissure:
            cv.set(x, y - 1, BASALT[4])  # its lit upper lip
        blocked.add((x, y))
    # the hot stream from the lowest pool, the springs' own outflow, down past the
    # bathhouse path (a stone footbridge carries the path over it) and into a small
    # steaming soak at the old flow, which spills into the fissure
    STREAM = [(110, 392), (106, 416), (104, 440), (103, 462), (98, 486), (90, 506), (84, 522)]
    stream = worlds.thick(STREAM, 4, seed=41)
    soak = {(x, y) for (x, y) in oval(84, 528, 12, 7)
            if math.hypot((x - 84) / 12, (y - 528) / 7) < 1 + 0.1 * math.sin(3 * math.atan2(y - 528, x - 84) + 1)}
    for (x, y) in stream | soak:
        cv.set(x, y, SPRING[2] if (x + y) % 3 else SPRING[3])
        blocked.add((x, y))
    for (x, y) in stream | soak:
        if (x - 1, y) not in stream | soak:
            cv.set(x - 1, y, TRAV[2])  # a pale mineral lip on its lit bank
        elif (x + 1, y) not in stream | soak and 0 <= x + 1 < W:
            cv.set(x + 1, y, '#C8803A')  # warm mats on the shaded one
        if (x, y - 1) not in stream | soak:
            cv.set(x, y, TRAV[1])  # the bank's shadow on the water
    for t in range(9):  # the soak's spill over the fissure's lip, foaming
        x = 88 + t
        cv.set(x, 535 + t // 3, SPRING[4] if t % 2 else SPRING[3]); cv.set(x, 536 + t // 3, '#DDF4F0')
    glow_skip = set(lake)
    # the flagstone path from the caldera to the bathhouse, lantern-lit
    path = worlds.thick(SPRINGS_PATH, 8, seed=43)
    BRIDGE = (90, 449, 28, 20)  # x, y, length, width (deck and both parapets)
    bx0, by0, blen, bwid = BRIDGE
    span = rect_set_z(bx0, by0, blen, bwid)
    for (x, y) in path:
        if (x, y) in blocked and (x, y) not in span:
            continue
        sx = (x + (y // 7) % 2 * 5) // 10
        c = BASALT[3] if noise2(sx, y // 7, 505) > 0.4 else BASALT[2]
        if (x + (y // 7) % 2 * 5) % 10 == 0 or y % 7 == 0:
            c = BASALT[0]
        cv.set(x, y, c)
    deck, parapets = springs_bridge(cv, bx0, by0, blen, bwid, stream)
    blocked -= deck
    blocked |= parapets
    ash_dressing(cv, blocked | lake | sinter | path | fissure | span, 794, 70, *FIRE_OFF['springs'])
    for (lx, ly) in ((52, 330), (62, 404), (140, 440), (214, 478)):
        light_pool(cv, lx, ly + 22, 18, 8, '#F2A048', glow_skip | blocked)
    objects = [
        ('bath', 'bathhouse', 196, 404), ('lantern-1', 'stone_lantern', 44, 306), ('lantern-2', 'stone_lantern', 54, 382),
        ('lantern-3', 'stone_lantern', 134, 426), ('lantern-4', 'stone_lantern', 206, 456),
        ('weed-1', 'fireweed', 20, 360), ('weed-2', 'fireweed_small', 8, 410), ('weed-3', 'fireweed', 160, 520),
        ('weed-4', 'fireweed_small', 176, 540), ('weed-5', 'fireweed', 290, 330), ('weed-6', 'fireweed_small', 300, 250),
        ('weed-7', 'fireweed', 130, 120), ('weed-8', 'fireweed_small', 20, 240), ('weed-9', 'fireweed', 268, 360),
        ('weed-10', 'fireweed_small', 282, 372), ('weed-11', 'fireweed', 300, 470), ('weed-12', 'fireweed_small', 60, 180),
        # the outcrops: a stack left standing on the upper slope, the stumps of another
        # by the bathhouse, a column fallen across the ash in the south
        ('cols-1', 'basalt_stack', 274, 196), ('cols-2', 'basalt_stumps_b', 268, 30),
        ('cols-3', 'basalt_stumps', 222, 520), ('cols-4', 'basalt_fallen', 252, 552),
        ('hiss', 'steam_puff', 98, 522), ('steam-src', 'steam_puff', 232, 116),
        ('vent-1', 'cooling_vent', 150, 60), ('vent-2', 'cooling_vent', 300, 120),
        ('obs-1', 'obsidian_small', 20, 470), ('obs-2', 'obsidian', 286, 410),
        ('scree-1', 'scree', 28, 128), ('scree-2', 'scree_small', 196, 70), ('scree-3', 'scree_b', 276, 286),
        ('scree-4', 'scree_small', 30, 500), ('snag-1', 'charred_snag', 226, 84), ('snag-2', 'charred_snag', 4, 190),
        ('snag-3', 'charred_snag', 296, 166),
    ]
    stands = {'caldera': (8, 300), 'pools': (60, 250), 'bath': (250, 494), 'stream': (140, 500), 'slope': (220, 70)}
    return cv, objects, stands, blocked | lake


def springs_bridge(cv: Canvas, x0: int, y0: int, length: int, width: int, stream: set):
    """A small stone footbridge carrying the bathhouse path east-west over the hot stream,
    in the three-quarter view: dressed abutments on the dry banks at both ends, a deck of
    basalt flags between two low parapets (their copings lit, the south one showing its
    face), and under it a single arch, the stream running out of its shadow. Returns the
    deck (walkable) and the parapets and face (not)."""
    BASALT, ASHL = MATERIALS['basalt'], MATERIALS['ashlar']
    deck, walls = set(), set()
    xs = [x for (x, y) in stream if y0 <= y < y0 + width]
    sx0, sx1 = (min(xs), max(xs)) if xs else (x0 + length // 2 - 4, x0 + length // 2 + 4)
    for y in range(y0, y0 + width):
        for x in range(x0, x0 + length):
            if y < y0 + 4 or y >= y0 + width - 4:
                walls.add((x, y))
                k = y - y0 if y < y0 + 4 else y - (y0 + width - 4)
                c = ASHL[5] if k == 0 else ASHL[4] if k == 1 else ASHL[2] if k == 2 else ASHL[1]
                if (x - x0) % 7 == 0 and k > 0:
                    c = ASHL[1]  # the joints between the coping stones
                if x == x0 or x == x0 + length - 1:
                    c = ASHL[3] if x == x0 else ASHL[1]  # the parapet's ends
            else:
                deck.add((x, y))
                row = (y - y0 - 4) // 4
                c = BASALT[3] if noise2((x + row * 3) // 6, row, 512) > 0.45 else BASALT[2]
                if (y - y0) % 4 == 0 or (x + row * 3) % 6 == 0:
                    c = BASALT[1]
                if y == y0 + 4:
                    c = BASALT[1]  # the north parapet's shadow on the deck
            cv.set(x, y, c)
    face_y = y0 + width
    for x in range(x0 - 2, x0 + length + 2):  # the south face: dressed stone over an arch
        for k in range(6):
            y = face_y + k
            if sx0 - 1 <= x <= sx1 + 1 and k >= 2:
                cv.set(x, y, '#121014' if k < 4 else MATERIALS['basalt'][1])  # the arch's shadow, the stream in it
                walls.add((x, y))
                continue
            c = ASHL[2] if (x // 6 + k // 3) % 2 else ASHL[3]
            if k % 3 == 2 or x % 6 == 0:
                c = ASHL[1]
            if k == 5:
                c = ASHL[0]
            if x < x0 or x >= x0 + length:
                c = BASALT[3] if k < 3 else BASALT[2]  # the abutments, wider than the deck
            cv.set(x, y, c)
            walls.add((x, y))
        if sx0 - 2 <= x <= sx1 + 2:  # the voussoirs of the arch
            cv.set(x, face_y + 1, ASHL[4] if x < (sx0 + sx1) / 2 else ASHL[3])
    for x in range(x0 + length + 2, x0 + length + 5):  # the bridge's shadow, down and right
        for y in range(y0 + 4, face_y + 7):
            style.darken(cv, x, y)
    for x in range(x0, x0 + length + 2):
        style.darken(cv, x, face_y + 6)
    return deck, walls - deck


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
            # the gulch's sand giving out across the border into scrub and ash (one blend
            # across both zones, desert_edge); toward the lava it turns to ash
            heat = max(0.0, (34 - dist[y][x]) / 22)
            cv.set(x, y, desert_edge(x + W, y, heat) if heat < 1 else fire_ash(x + ox, y + oy))
    for i in range(80):  # dry tufts in the scrub belt, each with its small shadow
        x, y = int(noise2(i, 0, 748) * 90), 6 + int(noise2(i, 1, 748) * (H - 12))
        s = sand_share(x + W, y, max(0.0, (34 - dist[y][x]) / 22))
        if not 0.28 < s < 0.7 or dist[y][x] < 26 or 352 < y < 416:
            continue
        for (dx, dy) in ((0, 0), (-1, -1), (1, -1), (0, -2), (-2, -2), (2, -2)):
            cv.set(x + dx, y + dy, MATERIALS['cactus'][1] if dy else MATERIALS['cactus'][0])
        cv.set(x + 1, y + 1, DESERT[1] if s > 0.5 else ASH[1])
    for (pts, r, sd) in (([(190, 120), (226, 150), (262, 160)], 13, 747),
                         ([(250, 300), (276, 340), (300, 362)], 12, 748)):
        cooled_flow(cv, pts, r, sd)
    for i in range(70):  # cracks in the ash still glowing near the lava
        x, y = int(noise2(i, 0, 749) * W), int(noise2(i, 1, 749) * H)
        if 12 < dist[y][x] < 60 and x > 40:
            for k in range(5):
                cv.set(x + k, y + (k * 7 // 5) % 2, LAVA[1] if k % 2 else BASALT[1])
    channel = paint_lava(cv, 'scorch', frame)
    road = worlds.thick(SCORCH_ROAD, 9, seed=752)
    ash_dressing(cv, channel | road | {(x, y) for y in range(H) for x in range(W) if dist[y][x] < 14 or x < 40},
                 791, 120, *FIRE_OFF['scorch'])
    # the road: the gulch's rutted track turns into a laid road of pale ash flags where it
    # reaches the ash, over the small bridge and up to Hearthold
    for (x, y) in road:
        if not (0 <= x < W and 0 <= y < H) or (x, y) in channel:
            continue
        ash_flags(cv, x, y, 754)  # the laid road, from the sand's edge in the gulch to the castle
    road_edges(cv, {(x, y) for (x, y) in road if 0 <= x < W and 0 <= y < H and (x, y) not in channel}, channel)
    for (lx, ly) in ((182, 300), (150, 150), (136, 388)):  # the road's lanterns throw a warm pool
        light_pool(cv, lx + 6, ly + 26, 18, 8, '#F2A048', channel)
    deck, parapet = drain_bridge(cv, *DRAIN_BRIDGE, channel)
    objects = [
        ('skull', 'cow_skull', 20, 430), ('weed-1', 'tumbleweed', 14, 320), ('cactus-1', 'saguaro_small', 2, 470),
        ('pear-1', 'prickly_pear', 4, 548),
        # the last trees on the way up, burnt where the flows passed: one stand of them
        ('snag-1', 'charred_snag', 226, 236), ('snag-2', 'charred_snag', 252, 250), ('snag-3', 'charred_snag', 236, 268),
        # obsidian at the drain's banks
        ('obs-1', 'obsidian', 96, 230), ('obs-2', 'obsidian_small', 120, 300),
        # basalt columns in one outcrop on the high ground in the north-east, scree below
        ('cols-1', 'basalt_columns_low', 262, 40), ('cols-2', 'basalt_fallen', 212, 96), ('scree-1', 'scree', 250, 112),
        ('scree-2', 'scree_small', 196, 410), ('lantern-1', 'stone_lantern', 182, 300), ('lantern-2', 'stone_lantern', 150, 150),
        ('lantern-3', 'stone_lantern', 136, 388),  # at the bend past the bridge: the first of the lights up to the castle
        ('vent-1', 'cooling_vent', 270, 470),
        # the scrub belt between the sand and the ash, in clumps, never in a line
        ('scrub-1', 'desert_scrub', 14, 500), ('scrub-2', 'desert_scrub_b', 0, 456), ('scrub-4', 'desert_scrub_b', 26, 548),
    ]
    blocked = ((hot - deck) | parapet)
    stands = {'gulch': (8, 384), 'track': (48, 384), 'bridge': (102, 384), 'castle': (160, 8), 'climb': (170, 250),
              'basin': (232, 440)}
    return cv, objects, stands, blocked


def basalt_flags(cv: Canvas, x: int, y: int, seed: int):
    """One pixel of dark basalt flagstones seen from above (the caldera's landing, the
    forge's apron and the lanes from it; review 19 Oct: not wall courses): irregular
    flags of different sizes laid edge to edge, each its own tone, dark joints between
    them, each flag's upper-left lip catching the light."""
    BASALT = MATERIALS['basalt']
    cid, edge, dx, dy = _cell(x, y, 9, seed % 97)
    t = noise2(cid[0], cid[1], seed)
    c = BASALT[3] if t > 0.55 else BASALT[2] if t > 0.15 else BASALT[1]
    if edge < 1.0:
        c = BASALT[0]
    elif edge < 2.0 and dx + dy > 0:
        c = BASALT[4] if c != BASALT[1] else BASALT[3]  # the lit lip on its upper left
    cv.set(x, y, c)


def ash_dressing(cv: Canvas, skip, seed: int, count: int = 90, ox: int = 0, oy: int = 0):
    """Small things lying on the fire country's ash (art-style.md, "ground that is never
    flat", in clusters of two or more pixels so they hold up on a phone): little heaps
    of basalt rubble, each stone lit on its upper left, and short wind drifts of pale
    ash with a shaded lee. `skip`: pixels to leave alone (lava, paths, walls). Placed
    in the fire country's coordinates (ox, oy: this zone's offset), so the pattern
    never repeats from one zone to the next."""
    BASALT, ASH = MATERIALS['basalt'], MATERIALS['ash']
    for i in range(count):
        X, Y = int(noise2(i, ox // 7 + oy // 11, seed) * W), int(noise2(i, 5 + ox // 7 + oy // 11, seed) * H)
        if any((X + dx, Y + dy) in skip for dx in (-4, 0, 6) for dy in (-3, 0, 3)):
            continue
        if i % 3:  # rubble: two to four stones
            for k in range(2 + i % 3):
                sx = X + int((noise2(i, k, seed + 1) - 0.5) * 9)
                sy = Y + int((noise2(i, k, seed + 2) - 0.5) * 5)
                detail.pebble(cv, sx, sy, BASALT, big=(k == 0 and i % 4 == 1))
        else:  # a drift: a pale crest with its shaded lee below
            n = 4 + i % 4
            for k in range(n):
                cv.set(X + k, Y, ASH[3] if k % 3 else ASH[4])
                if 0 < k < n - 1:
                    cv.set(X + k + 1, Y + 1, ASH[1])


def road_edges(cv: Canvas, road: set, skip=frozenset()):
    """Where a flagged road meets the ash: a lit kerb on its upper left and a soft
    shadow on its lower right, so the road reads as laid, not painted."""
    BASALT, ASH = MATERIALS['basalt'], MATERIALS['ash']
    for (x, y) in road:
        if (x, y) in skip:
            continue
        for (dx, dy, c) in ((-1, 0, ASH[4]), (0, -1, ASH[4]), (1, 0, BASALT[3]), (0, 1, BASALT[3])):
            q = (x + dx, y + dy)
            if q not in road and q not in skip and 0 <= q[0] < W and 0 <= q[1] < H:
                cv.set(*q, c)
                if c == BASALT[3]:
                    style.darken(cv, q[0] + dx, q[1] + dy)


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


def drain_bridge(cv: Canvas, y0: int, h: int, lava: set):
    """The road's bridge over the drain in the Scorched Pass (note to-d-after-61, 19 Oct:
    "draw a stone bridge with dry ends, parapets, lit lip"), east-west across a channel
    running south, in the three-quarter view: a deck of the road's own flags between two
    parapets with lit copings and a squared post standing proud at each corner; below the
    south parapet the bridge's face toward the viewer: coursed stone that splays out at
    both ends into abutments standing on dry ash (with their foot shadow), and one arch
    over the lava, dark inside, its soffit lit orange by the lava running beneath and its
    rim catching the glow. Its shadow falls on the lava below and to the right. It spans
    the channel's widest row with ten px of footing on each bank. Returns the deck
    (walkable) and the stonework (not)."""
    ASHL, BASALT, LAVA = csp.STONE_R, MATERIALS['basalt'], MATERIALS['lava']
    F = 11  # the face's height below the deck
    rows = range(y0 - 1, y0 + h + F + 2)
    xs = [x for (x, y) in lava if y in rows]
    lx0, lx1 = min(xs), max(xs)
    xa, xb = lx0 - 10, lx1 + 10
    deck, walls = set(), set()
    for y in range(y0, y0 + h):
        r = y - y0
        for x in range(xa, xb + 1):
            if 4 <= r < h - 4:
                deck.add((x, y))
                ash_flags(cv, x, y, 754)  # the road's own flags, carried over
                if r == 4 or (r == 5 and x % 2):
                    style.darken(cv, x, y)  # the north parapet's shadow on the deck
                continue
            walls.add((x, y))
            cap = (x - xa) % 9 == 0
            if r < 4:  # the north parapet: its back edge, the lit coping, its face to the deck
                c = [ASHL[2], ASHL[5], ASHL[4], ASHL[3]][r]
            else:  # the south parapet: its coping, lit, then its top course
                c = [ASHL[4], ASHL[5], ASHL[3], ASHL[2]][r - (h - 4)]
            if cap and r in (1, 2, h - 3, h - 2):
                c = ASHL[1]  # the joint between two coping stones
            cv.set(x, y, c)
    # the face: coursed stone, splaying out at the ends into the abutments
    ac, aw = (lx0 + lx1) / 2, (lx1 - lx0) / 2 + 1.5
    for k in range(F):
        y = y0 + h + k
        sp = k * 4 // F  # how far the abutments splay out at this course
        for x in range(xa - sp, xb + sp + 1):
            u = (x - ac) / aw
            top = F + 1 if abs(u) >= 1 else 2 + round((F - 3) * (1 - math.sqrt(1 - u * u)))
            walls.add((x, y))
            if k >= top:  # through the arch: dark under the deck, the lava's light below
                c = BASALT[0] if k < top + 2 else LAVA[0] if k < F - 3 else LAVA[1] if k < F - 1 else LAVA[3]
                if k == top:
                    c = LAVA[2] if (x + k) % 2 else LAVA[1]  # the soffit, lit from below
            elif k == top - 1 and abs(u) < 1:
                c = LAVA[3] if abs(u) > 0.8 else LAVA[2] if x % 2 else ASHL[4]  # the arch's rim in the glow
            else:
                course = k // 3
                joint = k % 3 == 2 or (x + course * 4) % 8 == 0
                c = ASHL[1] if joint else ASHL[3] if x <= xa - sp + 1 else ASHL[2]
                if k == 0:
                    c = ASHL[1]  # the string course under the parapet, in its shade
            cv.set(x, y, c)
    for x in range(xa - 4, xb + 6):  # the abutments' foot on the ash, in their own shadow
        for d in (0, 1, 2):
            y = y0 + h + F + d
            if (x, y) not in lava and 0 <= x < W and 0 <= y < H and (d < 2 or x % 2):
                style.darken(cv, x, y)
    for (px, py) in ((xa, y0 - 3), (xb - 5, y0 - 3), (xa, y0 + h - 6), (xb - 5, y0 + h - 6)):
        for y in range(py, py + 9):  # the posts: a block standing proud, lit on top and west
            for x in range(px, px + 6):
                walls.add((x, y))
                r = y - py
                c = ASHL[5] if r < 3 and x < px + 5 else ASHL[2] if r < 3 else ASHL[4] if x == px else ASHL[3] if x < px + 5 else ASHL[1]
                if r == 2:
                    c = ASHL[3] if x < px + 5 else ASHL[1]  # the cap's lower edge
                cv.set(x, y, c)
        for y in range(py + 1, py + 9):  # its shadow on whatever lies to its right
            if (px + 6, y) not in walls:
                style.darken(cv, px + 6, y)
    for x in range(xa, xb + 1):  # the lava's light on the north parapet's back edge
        if (x, y0 - 1) in lava and x % 3 == 0:
            cv.set(x, y0, LAVA[1])
    for y in range(y0 + h + F, y0 + h + F + 4):  # the bridge's shadow on the lava, down and right
        for x in range(lx0 + 2 + (y - y0 - h - F), xb + 3):
            if (x, y) in lava:
                style.darken(cv, x, y)
    return deck, walls - deck


def postern_bridge(cv: Canvas, x0: int, y0: int, y1: int, lava: set):
    """Hearthold's postern bridge, from the caldera's path (y0) south over the moat to the
    isle's footing (y1), in the three-quarter view (review 19 Oct 08:04): a dressed
    abutment on the north bank with a lit lip, a deck of flags between two parapets with
    lit copings, two piers standing in the lava with cutwaters, their feet glowing where
    the lava laps them, and the bridge's shadow cast on the lava to its right. 24 px
    wide at x0 (the parapets at x0..x0+3 and x0+20..x0+23, a deck of four walk cells).
    Returns the deck (walkable) and the parapets and piers (not)."""
    ASHL, BASALT, LAVA = csp.STONE_R, MATERIALS['basalt'], MATERIALS['lava']
    deck, walls = set(), set()
    w = 24
    piers = [y0 + (y1 - y0) * 2 // 5, y0 + (y1 - y0) * 7 // 10]
    for (py) in piers:  # the piers first: cutwaters out either side, standing in the lava
        for y in range(py - 4, py + 8):
            for x in list(range(x0 - 7, x0)) + list(range(x0 + w, x0 + w + 7)):
                d = (x0 - 1 - x) if x < x0 else (x - x0 - w)
                if y < py - 4 + d:  # the cutwater's point, upstream
                    continue
                c = ASHL[3] if x < x0 else ASHL[2]
                if y == py - 4 + d or (x < x0 and d == 6):
                    c = ASHL[5] if x < x0 else ASHL[3]  # its lit top edge
                if y >= py + 4:
                    c = ASHL[1] if y < py + 6 else LAVA[4] if y == py + 6 else LAVA[3]  # its face, the lava lapping its foot
                cv.set(x, y, c)
                walls.add((x, y))
        for y in range(py - 1, py + 7):  # its shadow on the lava, down and right
            for d in range(1, 3):
                q = (x0 + w + 6 + d, y + d)
                if q in lava:
                    style.darken(cv, *q)
    for y in range(y0, y1):
        for x in range(x0, x0 + w):
            across = x - x0
            cap = (y - y0) % 10 < 2  # a capstone every few feet, standing a little proud
            if across < 4 or across >= w - 4:
                walls.add((x, y))
                if across < 4:  # the west parapet: its outer edge, the lit coping, its inner face
                    c = [ASHL[1], ASHL[5], ASHL[4], ASHL[2]][across]
                else:  # the east one: its inner face catches the light, its outer edge in shade
                    c = [ASHL[4], ASHL[5] if cap else ASHL[4], ASHL[3], ASHL[1]][across - (w - 4)]
                if (y - y0) % 10 == 2 and across not in (0, w - 1):
                    c = ASHL[1]  # the joint below a capstone
            else:
                deck.add((x, y))
                ash_flags(cv, x, y, 739)  # the path's own flags, carried over the moat
                if across == 4 or (across == 5 and y % 2):
                    style.darken(cv, x, y)  # the west parapet's shadow on the deck
                continue
            cv.set(x, y, c)
    for y in range(y0 - 4, y0 + 8):  # the abutment: a flagged landing on the north bank
        for x in range(x0 - 6, x0 + w + 6):
            if x0 <= x < x0 + w and y >= y0:
                continue
            q = (x, y)
            if y >= y0 + 5 or (y >= y0 and (x, y + 1) in lava):
                c = ASHL[1] if y < y0 + 6 else LAVA[1]  # its face down to the lava, glowing at the foot
                walls.add(q)
            elif x in (x0 - 6, x0 + w + 5) or (y == y0 - 4 and not x0 + 2 <= x < x0 + w - 2):
                c = ASHL[4] if x < x0 + w else ASHL[2]  # its kerb, lit
                walls.add(q) if y >= y0 else None
            else:
                ash_flags(cv, x, y, 739)
                if y >= y0:
                    walls.add(q)
                continue
            cv.set(x, y, c)
    for y in range(y0 + 8, y1):  # the shadow on the lava to the right, broken where a pier stands
        if any(py - 4 <= y < py + 8 for py in piers):
            continue
        for d in range(0, 5):
            q = (x0 + w + d, y)
            if q in lava:
                style.darken(cv, *q)
    for y in range(y0 + 8, y1):  # the lava's light on the parapets' outer faces
        if (x0 - 1, y) in lava and y % 2:
            cv.set(x0, y, LAVA[2])
        if (x0 + w, y) in lava and y % 2:
            cv.set(x0 + w - 1, y, LAVA[1])
    return deck, walls - deck


def _cell(x: int, y: int, cell: int, seed: int):
    """The jittered cell (Voronoi) a pixel falls in: its id, the distance to the next
    cell's edge, and which side of the cell's centre the pixel lies (for lit lips)."""
    best, second, bid, bc = 1e9, 1e9, None, (0, 0)
    gx, gy = x // cell, y // cell
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            cx = (gx + i) * cell + noise2(gx + i, gy + j, 240 + seed) * cell
            cy = (gy + j) * cell + noise2(gx + i, gy + j, 241 + seed) * cell
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d < best:
                best, second, bid, bc = d, best, (gx + i, gy + j), (cx, cy)
            elif d < second:
                second = d
    return bid, math.sqrt(second) - math.sqrt(best), bc[0] - x, bc[1] - y


# The postern in Hearthold's north wall is a gateway you walk through (its arch is drawn
# over the companion as it passes): this district registers its opening in zones.py's
# OPENINGS table, the way the gatehouse's is (x span inside the 28 px sprite).
OPENINGS['postern'] = (8, 24)


# Hearthold's curtain wall: the band of the isle (as a fraction of its radius) between
# the flagged yard and the cliff, and the two ways through it (x spans).
WALL_IN, WALL_OUT, WALL_FACE = 0.875, 0.965, 10
GATE_GAP, POSTERN_GAP = (146, 177), (92, 112)


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
    ASHLAR = csp.STONE_R  # the same dressed stone as the keep and the towers
    cv = Canvas(W, H)
    for y in range(H):  # the fire country's ash, running on from the caldera and the Scorch
        for x in range(W):
            cv.set(x, y, fire_ash(x, y + H))
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
    # the footing: a ledge of cooled crust and rough-laid basalt between the lava and the
    # isle's cliff, so the masonry never stands in molten rock (review 19 Oct 08:04): each
    # block its own tone, lit on its upper left, the joints dark, and its outer lip
    # glowing where the lava licks it
    def rp(x, y):
        return _superellipse(x, y, ix, iy, irx + PLINTH, iry + PLINTH, 4) ** 0.25
    plinth = {(x, y) for x in range(W) for y in range(max(0, iy - iry - PLINTH - 1), min(H, iy + iry + PLINTH + 2))
              if rr(x, y) > 1 and rp(x, y) <= 1}
    for (x, y) in plinth:
        cid, edge, dx, dy = _cell(x, y, 6, 812)
        t = noise2(cid[0], cid[1], 813)
        c = BASALT[3] if t > 0.55 else BASALT[2] if t > 0.15 else ASH[1]
        if edge < 1.0:
            c = BASALT[0]
        elif edge < 1.9 and dx + dy > 0:
            c = BASALT[4] if c != ASH[1] else ASH[2]
        if rp(x, y) > 0.985:
            c = LAVA[2] if (x + y) % 3 == 0 else LAVA[1]  # the lip in the lava's glow
        cv.set(x, y, c)
    # the yard: big irregular flagstones, dusty and worn, each its own tone, the joints
    # soft, a lit lip on the upper left of each stone; calmer than the walls so the
    # buildings stand off it. No moss this close to the lava.
    FLAG = ['#6E6862', '#857E75', '#968F84', '#A49C90', '#B4AC9E']
    for (x, y) in yard:
        cid, edge, dx, dy = _cell(x, y, 13, 797)
        t = noise2(cid[0], cid[1], 798)
        c = FLAG[3] if t > 0.6 else FLAG[2] if t > 0.2 else FLAG[1]
        if edge < 1.2:
            c = FLAG[0]  # the joint
        elif edge < 2.4 and dx + dy > 0:
            c = FLAG[4] if c != FLAG[1] else FLAG[3]  # the lit lip toward the light
        elif noise2(x // 2, y // 2, 799) > 0.94:
            c = FLAG[1]  # a scuff
        cv.set(x, y, c)
    # the wall walk: a lit coping, merlons standing proud along the outer edge
    def side(x, y):  # on the west or east wall, which run north-south down the isle's flanks
        return abs(x - ix) > irx * 0.62 and abs(y - iy) < iry * 0.82
    for (x, y) in wall:
        r = rr(x, y)
        c = ASHLAR[3] if (x // 7 + y // 6) % 3 else ASHLAR[2]
        if r > WALL_OUT - 0.018:
            c = ASHLAR[5] if (x // 4 + y // 4) % 2 else ASHLAR[1]  # merlons and embrasures
        elif r < WALL_IN + 0.012:
            c = ASHLAR[4]  # the inner coping, catching the light
        if side(x, y):
            # the flanks, built up so they read as wall, not paving (review 19 Oct 14:20): a
            # parapet of merlons along the outer edge, each block lit on its upper left
            # with a dark embrasure between, a walk of worn flags, a lit inner coping
            t = (r - WALL_IN) / (WALL_OUT - WALL_IN)
            west = x < ix
            if t > 0.62:
                blk = (y // 5) % 2
                c = (ASHLAR[5] if (y % 5 == 0 or (west and t > 0.9)) else ASHLAR[4]) if blk else ASHLAR[0]
                if blk and not west and t > 0.9:
                    c = ASHLAR[2]  # the merlons' shaded outer side, on the east wall
            elif t > 0.24:
                c = ASHLAR[2] if (y // 6 + x // 5) % 3 else ASHLAR[1]
                if y % 6 == 0:
                    c = ASHLAR[1]
            else:
                c = ASHLAR[5] if west else ASHLAR[4]
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
            if y > iy and q in rim:  # (the north wall's inner face is the wall sprites')
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
    for (x, y) in wall:
        if side(x, y) and ((x < ix and (x + 1, y) in yard) or (x > ix and (x - 1, y) in yard)):
            # the flank's inner face, a few courses of shaded masonry above the yard (it
            # stands taller than the yard; nothing walks into it)
            d = 1 if x < ix else -1
            for k in range(1, 4):
                q = (x + d * k, y)
                if q in yard:
                    face.add(q)
                    cv.set(*q, ASHLAR[1] if (y + k) % 4 else ASHLAR[0])
        if x < ix and (x + 1, y) in yard:  # the west wall's shadow falls on the yard to its right
            for d in range(1, 8 if side(x, y) else 4):
                if (x + d, y) in yard and (x + d, y) not in face:
                    style.darken(cv, x + d, y)
        if x > ix and side(x, y) and (x + 1, y) in rim:  # the east wall's shadow falls on its rim
            for d in range(1, 4):
                if (x + d, y) in rim:
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
    ash_dressing(cv, lava | isle | road | north | {(x, y) for x in range(130, 196) for y in range(456, 520)},
                 792, 70, *FIRE_OFF['hearthold'])
    for (x, y) in (road | north):
        if (x, y) in lava or not (0 <= x < W and 0 <= y < H):
            continue
        ash_flags(cv, x, y, 739)
    road_edges(cv, {(x, y) for (x, y) in road | north if (x, y) not in lava}, lava)
    light_pool(cv, 156, 32, 18, 8, '#F2A048', lava)  # the lantern by the postern path
    # the way most walked across the yard, gate to keep door: the flags worn smooth and
    # paler down its middle
    for (x, y) in worlds.thick([(161, 384), (162, 330), (200, 290)], 9, seed=740):
        if (x, y) in yard and (x, y) not in face and noise2(x // 3, y // 3, 741) > 0.25:
            r, g, b, _a = cv.get(x, y)
            cv.set(x, y, (min(255, r + 10), min(255, g + 9), min(255, b + 7), 255))
    # the bridges: the long one from the south bank to the gatehouse, the postern bridge
    south_deck, south_par = stone_bridge(cv, 146, 392, 30, 66)
    north_deck, north_par = postern_bridge(cv, 90, 44, 112, lava)
    light_pool(cv, 108, 154, 16, 7, '#F2A048', lava | plinth)  # the postern's lantern on the yard
    objects = [
        # the north wall stands on its footing line (the bridge passes behind it to the
        # postern's arch, which opens onto the yard at the wall's foot)
        ('tower-nw', 'round_tower', 40, 46), ('postern', 'postern', 86, 70), ('wall-n1', 'wall_run', 114, 82),
        ('tower-ne', 'round_tower', 226, 46),
        ('keep', 'keep', 148, 156), ('bell', 'bell_tower', 54, 168),
        ('well', 'castle_well', 110, 300), ('dummy-1', 'training_dummy', 200, 300), ('rack', 'weapon_rack', 212, 336),
        ('tower-sw', 'round_tower', 50, 232), ('gate', 'gatehouse', 102, 320),
        ('pole-1', 'banner_pole', 128, 466), ('pole-2', 'banner_pole', 180, 466),
        ('lantern-n', 'stone_lantern', 150, 6),
        ('bench-1', 'stone_bench', 64, 336), ('bench-2', 'stone_bench', 226, 266),
        ('dragon', 'dragon', 196, 132),  # perched on the keep (it flies when motion is on)
    ]
    blocked = ((lava | rim | wall | face | plinth) - south_deck - north_deck) | south_par | north_par
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

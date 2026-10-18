"""The Frostline Highlands: Fir Hollow, Snowmelt Lake, the Snow Saddle and the High Lookout.

Split out of zones.py (18 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['RIDGE_COL', 'HOLLOW_COL', 'LAKE_PORT', 'SUMMIT_COL', 'FACE_H', 'snow_px', 'high_slope_px', 'high_band', 'snow_trail', 'peak_row', 'rim_hollow', 'hollow', 'snowmelt', 'saddle', 'summit']


# ---- the Frostline Highlands (Matt, 18 Oct 19:07: the connected world Codex drew) ----
# Above the Ridge cabin the valley climbs on: Fir Hollow west of the ridge, Snowmelt Lake
# above it, the Snow Saddle above the ridge and the High Lookout at the top. One loop
# (ridge, hollow, lake, saddle, ridge) and one spur (the lookout). Snow deepens with
# height: below a face there is none; on the terraces it lies; up high it is all there is.
# The ways between them are gaps in the rock at fixed spans, the same on both sides.
RIDGE_COL = (172, 196)    # the ridge's north edge / the saddle's south edge
HOLLOW_COL = (120, 148)   # the hollow's north edge / the lake's south edge
LAKE_PORT = (404, 436)    # the lake's east edge / the saddle's west edge (y)
SUMMIT_COL = (140, 164)   # the saddle's north edge / the lookout's south edge
FACE_H = 24


def snow_px(x: int, y: int, seed: int = 443) -> str:
    """Lying snow: soft drifts, the wind's ripples (sastrugi), blue in the hollows."""
    SN = MATERIALS['snow']
    n = smooth_noise(x, y, 18, seed)
    c = SN[3] if n > 0.4 else SN[2] if n > 0.22 or (x + y) % 2 else SN[1]
    rip = (y * 2 + int(math.sin(x / 13 + y / 31) * 4)) % 9
    if rip == 0 and n > 0.3:
        c = SN[2]
    elif rip == 1 and n > 0.3:
        c = SN[3]
    return c


def high_slope_px(x: int, y: int) -> str:
    """The steep snow of the peaks' upper slopes, where no one walks: broad wind-packed
    fields, a shade bluer than the snow underfoot, with rock breaking through in patches
    (lit on their upper left)."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    rock = smooth_noise(x, y, 16, 805) * 0.7 + smooth_noise(x, y, 60, 806) * 0.3
    if rock > 0.8:
        # a rock outcrop: lit toward the upper left, its lower right in shade
        edge = smooth_noise(x - 2, y - 2, 16, 805) * 0.7 + smooth_noise(x - 2, y - 2, 60, 806) * 0.3
        return ST[3] if edge > rock else ST[2] if rock < 0.84 else ST[1]
    if rock > 0.78:
        return SN[1]  # the snow's shadowed lip round the rock
    n = smooth_noise(x, y, 40, 801)
    c = SN[2] if n > 0.4 else SN[1] if n > 0.2 or (x + y) % 2 else SN[0]
    return c


def high_band(cv: Canvas, y0: int, y1: int, gap: tuple[int, int], edge: str) -> set:
    """A band of steep upper slope across the zone from y0 to y1 (blocked), open only in
    the gap; the gap's sides are rock walls lit on the west. Returns the blocked set."""
    ST = MATERIALS['stone']
    blocked = set()
    for y in range(y0, y1):
        for x in range(W):
            # the gap narrows its walls a little with noise, never closing
            wob = int(noise2(y // 6, x // 40, 803) * 3)
            g0, g1 = gap[0] - wob, gap[1] + wob
            if g0 <= x < g1:
                cv.set(x, y, snow_px(x, y, 804))
                continue
            near = min(abs(x - g0), abs(x - g1))
            # the gully's sides: rock walls, lit on the side facing east
            cv.set(x, y, (ST[2] if x < g0 else ST[1]) if near < 3 else high_slope_px(x, y))
            blocked.add((x, y))
    return blocked


def snow_trail(cv: Canvas, pts, width=8.5, seed=0) -> set:
    """A trodden line in the snow: packed and a shade darker, with boot dimples."""
    SN = MATERIALS['snow']
    trail = {(x, y) for (x, y) in worlds.thick(pts, width, seed=seed) if 0 <= x < W and 0 <= y < H}
    for (x, y) in trail:
        c = SN[1] if (x + y) % 3 else SN[2]
        if noise2(x, y, seed + 900) > 0.93:
            c = SN[0]
        cv.set(x, y, c)
    return trail


def peak_row(cv: Canvas, summits, base: int, gap=None, seed: int = 448) -> set:
    """A row of summits along the top of a zone (as on the ridge): sunlit snowfields on
    their west faces, blue shade east, rock ribs; the slope above their outline is the
    next slope up, also snow. Open only in the gap. Returns the blocked set."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    pts = set()

    def ridge_y(x):
        return min(ay + abs(x - ax) * (1.05 if x < ax else 0.85) for (ax, ay) in summits) + noise2(x // 3, 7, seed) * 3

    for x in range(W):
        if gap and gap[0] <= x < gap[1]:
            continue
        top = int(ridge_y(x))
        ax, ay = min(summits, key=lambda p: p[1] + abs(x - p[0]))
        bottom = base + int(noise2(x // 9, 8, seed + 1) * 6)
        for y in range(0, bottom):
            if y < top:
                c = high_slope_px(x, y)
            else:
                lit = x < ax
                depth = y - top
                fall = (x - ax) * 0.6 + (y - ay) * (1 if lit else -1) * 0.25
                rib = (int(fall) % 11 == 0) and depth > 6
                snowline = 30 + int(noise2(x // 6, ax, seed + 2) * 14)
                if depth < snowline and not rib:
                    c = SN[3] if lit else SN[1] if depth % 7 else SN[0]
                    if lit and depth < 2:
                        c = '#FFFFFF'
                else:
                    c = ST[3] if lit else ST[1]
                    if rib:
                        c = ST[2] if lit else ST[0]
            cv.set(x, y, c)
            pts.add((x, y))
    if gap:  # the gap: a snow gully between rock walls
        for y in range(0, base + 6):
            for x in range(gap[0], gap[1]):
                cv.set(x, y, snow_px(x, y, seed + 3))
            cv.set(gap[0], y, ST[3]); cv.set(gap[1] - 1, y, ST[1])
    return pts


def rim_hollow(x: int) -> int:
    """The face's top in Fir Hollow: the ridge's own face carried on west (its x - 320),
    rising a little as it goes."""
    xr = x - W
    return 210 + int(math.sin(xr / 27) * 8 + noise2(xr // 6, 0, 442) * 6) - (W - x) // 10


def hollow(frame: int = 0):
    """Fir Hollow, west of the ridge: the ridge's snowy terrace and its stone face carry on
    west, the face bending up as the ground rises; under the face a sheltered hollow of
    old firs on alpine turf, no snow down there, closing into dark forest at the bottom
    (the escarpment above the Woodland: no way down). Steps in the face join the two.
    A trail crosses the terrace from the ridge and climbs north through a gap in the
    peaks to Snowmelt Lake."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W, H)
    alpine = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
    worlds.grass(cv, frame, alpine)
    for x in range(W):
        r = rim_hollow(x)
        for y in range(0, r):
            cv.set(x, y, snow_px(x, y))
        for k in range(FACE_H):
            y = r + k
            band = (k + int(noise2(x // 7, 3, 445) * 3)) // 5
            c = ST[3] if band % 2 else ST[2]
            if (k + int(noise2(x // 7, 3, 445) * 3)) % 5 == 0:
                c = ST[4]
            if k < 2:
                c = SN[3] if k == 0 else SN[1]
            if k > FACE_H - 4:
                c = ST[1]
            cv.set(x, y, c)
        for d in range(3):
            if (x + d) % 2 or d == 0:
                style.darken(cv, x, r + FACE_H + d)
    # (the ridge's own westmost summit stands just past the border, at its x + 320)
    peaks = peak_row(cv, [(30, -8), (110, 12), (220, -18), (374, -10)], 74, gap=HOLLOW_COL, seed=811)
    # the bottom: the forest closes in and darkens over the escarpment (no way down),
    # darkening where the ridge's does, into the same deep shade
    B = H - meadow.draw_top_band().h
    for y in range(B - 60, H):
        for x in range(W):
            t = (y - (B - 60)) / 60
            if noise2(x, y, 812) < t:
                cv.set(x, y, G[1])
    style.dither_dark(cv, 0, B - 20, W, H - B + 20, 1.0)
    style.dither_dark(cv, 0, B - 40, W, 20, 0.5)
    # (the forest floor is walkable like the ridge's; only the escarpment's lip at the
    # very bottom is closed, so there is no way down into the Woodland)
    forest = {(x, y) for x in range(W) for y in range(H - 12, H)}
    # steps up the face near the west, as on the ridge
    steps = set()
    for x in range(56, 70):
        r = rim_hollow(x)
        for y in range(r, r + FACE_H):
            steps.add((x, y))
            cv.set(x, y, ST[4] if (y - r) % 4 == 0 else ST[2] if (y - r) % 4 < 3 else ST[1])
    face = {(x, y) for x in range(W) for y in range(rim_hollow(x), rim_hollow(x) + FACE_H)}
    # the trail on the terrace: in from the ridge, across, and north through the gap
    trail = snow_trail(cv, [(W + 10, 168), (250, 166), (190, 150), (150, 120), (134, 80), (134, -10)], seed=813)
    trail |= snow_trail(cv, [(190, 150), (100, 180), (63, rim_hollow(63) - 4)], 7, seed=814)
    objects = [
        ('pine-t1', 'snowy_pine', 20, 96), ('pine-t2', 'snowy_pine', 230, 70), ('pine-t3', 'snowy_pine', 280, 104),
        ('pine-t4', 'snowy_pine', 70, 120), ('ibex', 'ibex', 250, 110), ('post', 'trail_post', 176, 118),
        ('stone-1', 'stone', 120, 176),
        # the hollow under the face: old firs in a ring round a quiet clearing
        ('fir-1', 'pine', 10, 260), ('fir-2', 'pine', 60, 300), ('fir-3', 'pine', 230, 260), ('fir-4', 'pine', 270, 320),
        ('fir-5', 'pine', 20, 390), ('fir-6', 'pine', 250, 400), ('fir-7', 'pine', 120, 420), ('fir-8', 'pine', 190, 430),
        ('fir-9', 'pine', 70, 440), ('fir-10', 'pine', 278, 444), ('log', 'mossy_log', 140, 330),
        ('stump', 'stump', 196, 330), ('fern-1', 'fern', 100, 360), ('fern-2', 'fern', 176, 380),
        ('mush', 'mushroom_ring', 150, 380),
    ]
    stands = {'ridge': (316, 168), 'lake': (134, 6), 'steps': (63, rim_hollow(63) + FACE_H + 8), 'clearing': (160, 370)}
    return cv, objects, stands, (face - steps) | peaks | forest


def snowmelt(frame: int = 0):
    """Snowmelt Lake, above Fir Hollow: a cirque, the bowl the old glacier left. Cliffs
    ring it on the north with a waterfall frozen down their face; the lake fills the
    bowl, open dark water in its middle and ice at its rim; snow all round. The trail
    comes up through the gap from the hollow and follows the south shore east to the
    Snow Saddle."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    WTR = MATERIALS['water']
    ICE = ['#7C9CB8', '#A6C2D8', '#C8DCEA', '#E6F0F7']
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, snow_px(x, y, 821))
    # the cirque wall: rock cliffs across the top and down the west side
    def wall_y(x):
        return 120 + int(math.sin(x / 31) * 14 + noise2(x // 7, 1, 822) * 8)
    def face_px(x, y, k, height):
        """A stratified rock face (as the ridge's): bands, lit ledges, snow on them."""
        band = (k + int(noise2(x // 7, 3, 827) * 3)) // 5
        c = ST[3] if band % 2 else ST[2]
        if (k + int(noise2(x // 7, 3, 827) * 3)) % 5 == 0:
            c = SN[2] if noise2(x // 4, band, 828) > 0.55 else ST[4]  # a ledge, snow on some
        if k > height - 3:
            c = ST[1]
        return c
    cliff = set()
    for x in range(W):
        wy = wall_y(x)
        for y in range(0, wy):
            cv.set(x, y, high_slope_px(x, y) if y < wy - 40 else face_px(x, y, y - (wy - 40), 40))
            cliff.add((x, y))
        for d in range(3):
            if (x + d) % 2 or d == 0:
                style.darken(cv, x, wy + d)
    for y in range(wall_y(0), H - 60):
        depth = 18 + int(smooth_noise(0, y, 30, 823) * 10)
        for x in range(0, depth):
            cv.set(x, y, high_slope_px(x, y) if x < depth - 10 else face_px(y, x, x - (depth - 10), 10))
            cliff.add((x, y))
    # the frozen fall down the north wall into the lake
    for y in range(20, wall_y(110) + 4):
        for x in range(104, 118):
            if abs(x - 111 - math.sin(y / 9) * 2) < 5:
                cv.set(x, y, ICE[3] if x < 110 else ICE[2] if (y // 3) % 2 else ICE[1])
    # the lake: open water within an ice rim, a stony shore
    def shore(x, y):
        return math.hypot((x - 160) / 112, (y - 270) / 74) - (smooth_noise(x, y, 24, 829) - 0.5) * 0.22
    lake = {(x, y) for x in range(W) for y in range(H) if shore(x, y) < 1} - cliff
    for (x, y) in lake:
        d = shore(x, y)
        if d > 0.86:
            c = ICE[3] if (x + y) % 4 else ICE[2]
        elif d > 0.78:
            c = ICE[1] if noise2(x // 3, y // 3, 824) > 0.5 else ICE[2]
        else:
            c = WTR[1] if d < 0.5 else WTR[2]
            if (y + int(math.sin(x / 11) * 2)) % 13 == 0 and d < 0.7:
                c = WTR[3]
        cv.set(x, y, c)
    for x in range(W):
        for y in range(H):
            if (x, y) not in lake and (x, y) not in cliff and shore(x, y) < 1.05:
                cv.set(x, y, ST[3] if (x + y) % 3 else ST[2])  # a stony shore
    floes = [(84, 300), (230, 238), (196, 320)]
    for (fx, fy) in floes:
        for (x, y) in oval(fx, fy, 9, 4):
            if (x, y) in lake:
                cv.set(x, y, ICE[3] if y < fy else ICE[2])
    # the high band at the bottom closes the bowl's lip toward the hollow, but for the gap
    lip = high_band(cv, H - 44, H, HOLLOW_COL, 'south')
    # the trail: up through the gap, round the south shore, east to the saddle
    trail = snow_trail(cv, [(134, H + 10), (134, 470), (170, 410), (230, 404), (280, 418), (W + 10, 420)], seed=825)
    objects = [
        ('pine-1', 'snowy_pine', 26, 400), ('pine-2', 'snowy_pine', 262, 470), ('pine-3', 'snowy_pine', 60, 470),
        ('cairn', 'cairn', 216, 440), ('post', 'trail_post', 150, 450), ('boulder-1', 'boulder', 270, 470),
        ('stone-1', 'stone', 48, 360), ('ibex', 'ibex', 260, 140), ('boulder-2', 'boulder', 30, 160),
    ]
    # the east edge is the saddle's rock except where the trail goes through
    east = set()
    for y in range(wall_y(W - 1), H - 44):
        if LAKE_PORT[0] <= y < LAKE_PORT[1]:
            continue
        for x in range(W - 14 - int(smooth_noise(0, y, 20, 826) * 10), W):
            cv.set(x, y, high_slope_px(x, y))
            east.add((x, y))
    stands = {'hollow': (134, H - 6), 'shore': (200, 404), 'saddle': (316, 420)}
    return cv, objects, stands, cliff | lake | lip | east


def saddle(frame: int = 0):
    """The Snow Saddle, above the ridge: the broad snow col between two peaks, where
    the wind never quite stops (a windsock shows which way). A stone bothy shelters by
    the fork: the trail up from the ridge's gap divides here, west to Snowmelt Lake,
    north to the High Lookout. Cairns mark the way in a whiteout; an ibex watches from
    the rocks."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, snow_px(x, y, 831))
    # the two peaks' flanks: west above the lake path, east all the way down
    rock = set()
    for y in range(H):
        e0 = 250 - int(math.sin(y / 70) * 18 + noise2(y // 9, 1, 832) * 8)
        w1 = 46 + int(math.sin(y / 53) * 14 + noise2(y // 9, 2, 833) * 6) if y < LAKE_PORT[0] - 10 or y >= LAKE_PORT[1] + 30 else 0
        for x in range(W):
            if x >= e0 or x < w1:
                cv.set(x, y, high_slope_px(x, y))
                rock.add((x, y))
            elif (e0 - 3 <= x < e0 or w1 <= x < w1 + 3) and (x + y) % 2:
                cv.set(x, y, SN[3])  # the walkable snow's bright lip at the steep edge
    top = peak_row(cv, [(60, -10), (240, -16)], 60, gap=SUMMIT_COL, seed=834)
    bottom = high_band(cv, H - 50, H, RIDGE_COL, 'south')
    trail = snow_trail(cv, [(184, H + 10), (184, 500), (170, 440), (152, 360), (152, 200), (152, -10)], seed=835)
    trail |= snow_trail(cv, [(170, 440), (110, 426), (40, 420), (-10, 420)], seed=836)
    objects = [
        ('bothy', 'bothy', 176, 300), ('windsock', 'windsock', 96, 340), ('post', 'trail_post', 130, 440),
        ('cairn-1', 'cairn', 200, 470), ('cairn-2', 'cairn', 120, 250), ('cairn-3', 'cairn', 172, 120),
        ('ibex', 'ibex', 210, 200), ('stone-1', 'stone', 80, 470), ('boulder-1', 'boulder', 196, 410),
    ]
    stands = {'ridge': (184, H - 6), 'fork': (160, 450), 'bothy': (204, 384), 'lake': (4, 420), 'lookout': (152, 6)}
    return cv, objects, stands, rock | top | bottom


def summit(frame: int = 0):
    """The High Lookout: the top of the valley's world. The path comes up through the gap
    onto a small snowy summit with a stone windbreak, a bench and a brass viewing scope
    that looks out over everything walked so far; crags fall away on every side."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, high_slope_px(x, y))
    # the summit: a rounded top of firm snow, rock showing at its crown
    def inside(x, y):
        d = ((x - 156) / 118) ** 2 + ((y - 300) / 200) ** 2
        return d < 0.92 + (smooth_noise(x, y, 20, 844) - 0.5) * 0.5
    top = {(x, y) for x in range(W) for y in range(H) if inside(x, y)}
    for (x, y) in top:
        cv.set(x, y, snow_px(x, y, 841))
    # the rim: a corniced lip of bright snow, then the drop's shadow below and right
    for (x, y) in top:
        if (x, y - 2) not in top or (x - 2, y) not in top:
            cv.set(x, y, SN[3])
        elif (x, y + 2) not in top or (x + 2, y) not in top:
            cv.set(x, y, SN[1])
    for x in range(W):
        for y in range(H):
            if (x, y) not in top and ((x - 2, y) in top or (x, y - 2) in top) and (x + y) % 2:
                cv.set(x, y, SN[0])
    for (x, y) in oval(156, 190, 40, 22):  # the summit's crown of bare rock
        if (x, y) in top:
            style.darken(cv, x, y) if (x + y) % 5 == 0 else None
    style.facet_stone(cv, oval(156, 186, 30, 14), ST, seed=845, outline=None)
    # the way up from the saddle's gap
    for y in range(H - 150, H):
        for x in range(SUMMIT_COL[0] - 6, SUMMIT_COL[1] + 6):
            if (x, y) not in top:
                cv.set(x, y, snow_px(x, y, 842))
                top.add((x, y))
    trail = snow_trail(cv, [(152, H + 10), (152, 470), (150, 340), (160, 250)], seed=843)
    rock = {(x, y) for x in range(W) for y in range(H)} - top
    objects = [
        ('scope', 'telescope', 150, 186), ('wall', 'drystone_wall', 110, 150), ('bench', 'forest_bench', 190, 230),
        ('cairn', 'cairn', 100, 220), ('post', 'trail_post', 170, 300), ('pine', 'snowy_pine', 80, 400),
    ]
    stands = {'saddle': (152, H - 6), 'scope': (162, 236), 'bench': (204, 262)}
    return cv, objects, stands, rock

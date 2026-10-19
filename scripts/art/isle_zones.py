"""The Tidebloom Isles: Lagoon Landing, the Rainforest, the Headwaters and Black-sand Cove.

Split out of zones.py (18 Oct) so one worker (Claude C) can own this district's drawing
while others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main().

Redrawn to Codex's geography (PR #23, docs/codex/ideas/connected-world/README.md,
section 10, and biome-extensions.json): one dormant volcanic island in open sea. Its
ground, coast and water are drawn once for the whole island, in island coordinates
(`island()`, 640 x 1152 art px, the four zones' 2 x 2 grid), and each zone is cut from
it, so nothing seams at x 320 or y 576 (play-test 18 Oct, finding 6). Each zone then
adds its own trail, bridges and props."""
from __future__ import annotations

import functools
import os
import math

from PIL import Image, ImageDraw

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['TROPIC', 'LAGOON', 'BASALT_R', 'FLOOR', 'IW', 'IH', 'island',
           'isle_trail', 'plank_bridge', 'isle_landing', 'isle_rainforest', 'isle_headwaters', 'isle_cove']


# ---- the Tidebloom Isles (Matt, 18 Oct 19:07: the world Codex drew) ----------------
# A dormant volcanic island in the south-west sea, beyond a channel from Driftwood. Four
# zones on a 2 x 2 grid, walked as one loop: the Landing (south-west, the sheltered
# lagoon and the pier), the Rainforest (north-west, a stream valley), the Headwaters
# (north-east, the upland and the falls) and Black-sand Cove (south-east, the exposed
# basalt coast). Fresh water runs from the Headwaters' falls west through the Rainforest
# and south into the lagoon; the walk goes the other way round.
#
# Height (Codex's tiers): the Landing and the Cove at sea level (0), the Rainforest one
# step up (1), the Headwaters two (2). The steps are basalt escarpments along the zone
# borders, so each border is closed by rock except where Codex put the way through
# (frames.PORTS): a broad stair up from the landing (x 128-184), a switchback up the
# Headwaters' escarpment beside the waterfall gorge (y 224-280) and a two-tier terraced
# descent round the island's east shoulder to the cove (x 192-248, then a second stair).
TROPIC = ['#1F3A22', '#2E5A30', '#3F7A3A', '#5A9A46', '#86BE5E']
LAGOON = ['#1E6E7A', '#2A8E96', '#45B2B0', '#7FD6CC', '#C8F0E6']
BASALT_R = MATERIALS['basalt']
FLOOR = ['#1A2A1C', '#263A26', '#34492E', '#46603A', '#5E7A46']  # the rainforest's floor
MANGROVE = ['#14281C', '#1F3A26', '#2C5030', '#3F6A3A', '#5E8A48']
ROOT_C = ['#2E2420', '#4A3A2C', '#6A5440']
CORAL = ['#B98272', '#D4A88A', '#E6CDA8']
SEA = MATERIALS['water']
FOAM = '#F4F8F8'
IW, IH = 2 * W, 2 * H  # the island's grid, in art px
N = IW * IH

# The island's outline, clockwise from the north-west (island px). The coast between
# these points is subdivided and pushed in and out by noise, so it reads as worn rock
# and sand, never as a polygon.
COAST = [
    # the north coast: the rainforest's rocks, a small sandy bay, the volcano's foot
    (60, 120), (84, 84), (124, 62), (160, 70), (186, 92), (214, 86), (240, 64), (282, 50), (330, 46),
    (400, 36), (470, 38), (540, 46), (586, 66), (612, 110),
    # the east coast: the headwaters' sea cliffs and their bight, the cove's headland
    (604, 170), (590, 230), (600, 290), (616, 340), (606, 400), (582, 440), (570, 482), (586, 522),
    (606, 562), (612, 620), (598, 690), (606, 760), (596, 830), (604, 900), (596, 960), (578, 1004),
    (552, 1012),
    # the cove's black-sand bay, the basalt headland at the turn into the lagoon
    (524, 998), (494, 986), (462, 982), (432, 988), (404, 1002), (382, 1022), (362, 1046), (340, 1064),
    (316, 1060), (298, 1042),
    # the lagoon's shore, the pier's root, the river mouth
    (266, 1012), (232, 994), (190, 980), (150, 970), (112, 962), (84, 950), (62, 922), (48, 886), (40, 846),
    # the west coast, back north, with a rocky bight in the rainforest
    (30, 796), (20, 744), (30, 690), (24, 620), (34, 560), (26, 500), (36, 440), (24, 380), (26, 330),
    (48, 302), (72, 272), (54, 236), (30, 204), (40, 160),
]
# The reef that shelters the lagoon: from the headland round the south-west to the west
# coast. Inside it the water is the lagoon's turquoise; outside, the open sea.
REEF = [(352, 1074), (318, 1094), (262, 1112), (196, 1122), (130, 1120), (76, 1106), (40, 1080), (18, 1040),
        (10, 980), (8, 910), (12, 850), (22, 800)]
# The fresh water: out of the pool below the falls, west across the upland, through the
# rainforest's valley and south into the lagoon by the mangroves.
RIVER = [(540, 196), (518, 214), (496, 228), (470, 238), (448, 256), (412, 278), (380, 290), (320, 300),
         (284, 310), (250, 322), (212, 336), (178, 356), (146, 384), (120, 422), (104, 466), (94, 516),
         (86, 576), (78, 630), (66, 700), (58, 760), (52, 820), (46, 870), (40, 912)]
RIVER_W = 8.5
POOL = (540, 176, 42, 30)  # the falls' pool (centre, radii), under the volcano's flank
FALLS_X = 540
# small islands off the coast: scenery, never walked
ISLETS = [(600, 1100, 22, 12, True), (478, 1128, 11, 6, False), (296, 1138, 9, 5, False), (20, 26, 10, 6, False)]
# the cove's black beach and the rainforest's sandy bay (everywhere else the open sea
# meets rock)
BEACH = (392, 570)

# The trails, in island px: drawn once, so each runs on unbroken across the borders.
TRAILS = [
    # the pier up the dry shore lane beside the stream, the broad stair, the footbridge
    # over the river and on to the foot of the switchback
    [(112, 950), (110, 904), (122, 862), (140, 806), (154, 736), (154, 660), (156, 600), (156, 540), (160, 470),
     (165, 420), (165, 330), (180, 304), (222, 292), (262, 284), (296, 270), (318, 266)],
    # the landing's shore path round the headland to the cove and up its terraces
    [(140, 806), (228, 814), (282, 880), (304, 940), (340, 958), (400, 952), (452, 936), (500, 908), (544, 864),
     (566, 800), (568, 740), (566, 690)],
    # the Headwaters: from the switchback's top over the footbridge, across the upland
    # and down round the east shoulder: the first stair, the terrace, the second stair
    [(380, 234), (396, 244), (400, 262), (400, 312), (430, 352), (480, 398), (532, 440), (548, 490), (542, 530),
     (540, 552), (540, 600), (562, 616), (566, 630)],
    # the spur to the pool's edge
    [(430, 352), (490, 292), (516, 266)],
]
TRAIL_W = 9.5
# the switchback up the Headwaters' escarpment: three short legs across the slope
ZIGZAG = [(316, 266), (370, 266), (370, 250), (346, 250), (346, 234), (390, 234)]
SLOPE = (336, 226, 280)  # its west edge and its rows; it runs east to the escarpment
# footbridges over the river (x, y, w, h), and the broad stairs at the escarpments
BRIDGES = [(152, 338, 26, 52), (387, 262, 26, 42)]
STAIR_XS = {'west': (126, 186), 'east': (510, 570), 'terrace': (552, 580)}
RECESS = (206, 312)  # the rows of the gorge's recess in the Headwaters' escarpment
FACE = 18  # a cliff face's height for one step of height, in art px


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _wobble(points, amp: float, seed: int, closed: bool = True, step: float = 3.0):
    """A line through `points`, subdivided and pushed in and out along its normal by
    two octaves of noise, so it reads as a natural edge."""
    out = []
    s = 0.0
    pts = list(points) + ([points[0]] if closed else [])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        nx, ny = (y1 - y0) / L, -(x1 - x0) / L
        for i in range(n):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            off = (smooth_noise(s, 0, 34, seed) - 0.5) * 2 * amp + (smooth_noise(s, 0, 9, seed + 1) - 0.5) * 0.8 * amp
            out.append((x + nx * off, y + ny * off))
            s += L / n
    if not closed:
        out.append(pts[-1])
    return out


def _fill(poly) -> bytearray:
    img = Image.new('L', (IW, IH), 0)
    ImageDraw.Draw(img).polygon([(round(x), round(y)) for (x, y) in poly], fill=1)
    return bytearray(img.tobytes())


def _thick(points, radius: float, seed: int) -> bytearray:
    """A band `radius` either side of a polyline, its width breathing with noise."""
    m = bytearray(N)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 9, seed) - 0.5) * 2.4
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                if 0 <= y < IH:
                    for x in range(int(cx - r) - 1, int(cx + r) + 2):
                        if 0 <= x < IW and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                            m[y * IW + x] = 1
    return m


_N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_N8 = _N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _dist(src: bytearray, limit: int) -> bytearray:
    """How far each pixel is from the nearest `src` pixel (octagonal steps), up to
    `limit`; 255 beyond it."""
    dist = bytearray(b'\xff') * N
    frontier = [i for i in range(N) if src[i]]
    for i in frontier:
        dist[i] = 0
    level = 0
    while frontier and level < limit:
        level += 1
        nb = _N8 if level % 2 == 0 else _N4
        nxt = []
        for i in frontier:
            x = i % IW
            for (dx, dy) in nb:
                if 0 <= x + dx < IW:
                    j = i + dy * IW + dx
                    if 0 <= j < N and dist[j] == 255:
                        dist[j] = level
                        nxt.append(j)
        frontier = nxt
    return dist


def _seg_dist(px: float, py: float, points) -> float:
    best = 1e9
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(px - x0 - dx * t, py - y0 - dy * t))
    return best


def coast_north(gx: float) -> float:
    """Roughly where the north coast runs at an x (for the volcano's flank above it)."""
    pts = COAST[:14]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= gx <= x1:
            return y0 + (y1 - y0) * (gx - x0) / max(1, x1 - x0)
    return 40.0


def flank_top(gx: float) -> int:
    """The foot of the old volcano's flank on the Headwaters' north side: nothing west of
    island x 340, rising to its full height by x 440, so the forest runs on unbroken
    across the border with the Rainforest."""
    full = 120 + math.sin((gx - W) / 40) * 18 + smooth_noise(gx - W, 0, 20, 932) * 14
    base = coast_north(gx)
    return int(base + (full - base) * _smoothstep((gx - 340) / 100))


def x12(gy: float) -> float:
    """The escarpment between the Rainforest (west) and the higher ground east of it.
    Where the river has cut its gorge the cliff steps back into a recess (island rows
    206-312): its north wall is a front face above the way through, the switchback
    climbs its east side, and the gorge's rim closes it to the south."""
    base = 320 + (smooth_noise(0, gy, 46, 1301) - 0.5) * 10 + (smooth_noise(0, gy, 11, 1306) - 0.5) * 4
    if RECESS[0] <= gy < RECESS[1]:
        return base + 44 + (smooth_noise(0, gy, 11, 1305) - 0.5) * 6
    return base


def y01(gx: float) -> float:
    """The escarpment between the Rainforest and the Landing below it."""
    return 566 + (smooth_noise(gx, 0, 48, 1302) - 0.5) * 13 + (smooth_noise(gx, 0, 12, 1307) - 0.5) * 4


def y2a(gx: float) -> float:
    """The Headwaters' south edge, down to the terrace."""
    return 566 + (smooth_noise(gx, 0, 48, 1303) - 0.5) * 13 + (smooth_noise(gx, 0, 12, 1308) - 0.5) * 4


def y2b(gx: float) -> float:
    """The terrace's south edge, down to the cove. It narrows to nothing toward the
    landing, so no step runs down the open border between the landing and the cove."""
    full = 664 + 22 * math.sin((gx - 320) / 60) + (smooth_noise(gx, 0, 20, 1304) - 0.5) * 10
    top = y2a(gx)
    return top + (full - top) * _smoothstep((gx - 326) / 120)


def tier(gx: int, gy: int, X12, Y01, Y2A, Y2B) -> int:
    if gx < X12[gy]:
        return 1 if gy < Y01[gx] else 0
    return 2 if gy < Y2A[gx] else 1 if gy < Y2B[gx] else 0


class Island:
    """The island's ground, drawn once: `cv` (IW x IH) and the masks the zones cut."""

    def __init__(self):
        self.cv = Canvas(IW, IH)
        self.blocked = bytearray(N)
        self.water = bytearray(N)
        self.trail = set()
        self.zig = set()
        self.stairs = []  # (x0, y0, w, h)


def _put(px, x, y, c):
    px[x, y] = _RGBA[c] if c in _RGBA else _RGBA.setdefault(c, (*_rgb(c), 255))


_RGBA: dict = {}


@functools.lru_cache(maxsize=1)
def island() -> Island:
    I = Island()
    cv = I.cv
    px = cv.img.load()
    land = _fill(_wobble(COAST, 9, 1201))
    lagoon_zone = _fill(_wobble(REEF, 4, 1202, closed=False) + [(360, 960), (200, 780), (22, 780)])
    river = _thick(RIVER, RIVER_W, 1203)
    pcx, pcy, prx, pry = POOL
    pool = bytearray(N)
    for y in range(int(pcy - pry) - 2, int(pcy + pry) + 3):
        for x in range(int(pcx - prx) - 2, int(pcx + prx) + 3):
            if math.hypot((x - pcx) / prx, (y - pcy) / pry) < 1 - (smooth_noise(x - W, y, 10, 955) - 0.5) * 0.3:
                pool[y * IW + x] = 1
    islet = bytearray(N)
    for k, (cx, cy, rx, ry, _green) in enumerate(ISLETS):
        for y in range(cy - ry - 2, cy + ry + 3):
            for x in range(cx - rx - 2, cx + rx + 3):
                if math.hypot((x - cx) / rx, (y - cy) / ry) < 1 - (smooth_noise(x, y, 5, 1210 + k) - 0.5) * 0.35:
                    islet[y * IW + x] = 1
    for i in range(N):
        if river[i] or pool[i]:
            land[i] = 0
    # the reef: a broken band of coral along the lagoon's outer edge
    reef_line = _wobble(REEF, 4, 1202, closed=False)
    reef = _thick(reef_line, 3.2, 1204)
    solid = bytearray(N)  # what the water's shading counts as shore
    for i in range(N):
        if land[i] or islet[i]:
            solid[i] = 1
    d_land = _dist(solid, 40)
    sea = bytearray(N)
    lag = bytearray(N)
    for i in range(N):
        if not solid[i]:
            I.water[i] = 1
            if river[i] or pool[i]:
                pass
            elif lagoon_zone[i] and not reef[i]:
                lag[i] = 1
            else:
                sea[i] = 1
    d_sea = _dist(sea, 44)
    d_lag = _dist(lag, 20)
    d_fresh = _dist(bytearray(1 if (river[i] or pool[i]) else 0 for i in range(N)), 48)
    foot = {gx: flank_top(gx) for gx in range(IW)}

    # ---- the ground: the forest in the north-west, turf elsewhere, sand at the shore
    S = MATERIALS['sand']
    for gy in range(IH):
        row = gy * IW
        for gx in range(IW):
            i = row + gx
            if not land[i]:
                continue
            # the forest: the north-west and up the river's valley, thinning out
            # (never along a zone border: it follows the valley and the volcano's foot)
            f = 0.9 * min((290 - gx) / 110, (560 - gy) / 100)
            if gy < 780:
                f = max(f, 0.9 * (1 - d_fresh[i] / 46) - max(0, gy - 640) / 140)
            if gx > 300 and gy - foot[gx] < 70:  # (only where it adds forest: no seam at x 300)
                f = max(f, 0.8 * (1 - (gy - foot[gx]) / 70) * _smoothstep((gx - 300) / 90))
            f += (smooth_noise(gx, gy, 48, 1211) - 0.5) * 1.3 + (smooth_noise(gx, gy, 14, 1215) - 0.5) * 0.35
            if f > 0:
                n = smooth_noise(gx, gy, 16, 921)
                c = FLOOR[3] if n > 0.6 else FLOOR[2] if n > 0.22 or (gx + gy) % 2 else FLOOR[1]
                if noise2(gx, gy, 922) > 0.975:
                    c = FLOOR[4]  # a lit leaf on the floor
            else:
                n = smooth_noise(gx, gy, 20, 911)
                c = TROPIC[3] if n > 0.5 else TROPIC[2] if n > 0.25 or (gx + gy) % 2 else TROPIC[1]
                if noise2(gx, gy, 912) > 0.985:
                    c = TROPIC[4]
                if f > -0.07:
                    c = TROPIC[1] if f > -0.035 or (gx + gy) % 2 else TROPIC[2]  # the canopy's shade
            # the lagoon's pale sand; the cove's black beach; damp banks by fresh water
            dl, ds = d_lag[i], d_sea[i]
            sand_w = 7 + int(smooth_noise(gx, gy, 18, 1213) * 9)
            beach_w = 0
            if BEACH[0] <= gx <= BEACH[1] and gy > 900:
                beach_w = int(14 + 50 * math.sin(math.pi * (gx - BEACH[0]) / (BEACH[1] - BEACH[0])) +
                              (smooth_noise(gx, 0, 14, 1214) - 0.5) * 10)
            if dl <= sand_w:
                c = S[2] if noise2(gx, gy, 914) > 0.2 else S[1]
                if dl <= 2:
                    c = S[1] if dl == 1 else c  # wet sand at the water's edge
            elif ds <= beach_w:
                n = smooth_noise(gx, gy, 10, 944)
                c = BASALT_R[3] if n > 0.55 else BASALT_R[2] if (gx + gy) % 2 or n > 0.4 else BASALT_R[3]
                if ds <= 2:
                    c = BASALT_R[1]
                elif noise2(gx, gy, 945) > 0.985:
                    c = '#C9D2D6'  # a pale shell
            elif ds <= 2 + int(smooth_noise(gx, gy, 11, 1245) * 4) and dl > 8 and not (150 <= gx <= 214 and gy < 110):
                # worn wet basalt along every exposed shore
                c = BASALT_R[1] if ds <= 1 else BASALT_R[3] if smooth_noise(gx, gy, 4, 1246) > 0.6 else BASALT_R[2]
                I.blocked[i] = 1
            elif d_fresh[i] <= 2:
                c = FLOOR[1] if d_fresh[i] == 1 else FLOOR[2]
            _put(px, gx, gy, c)

    # ---- the water
    for gy in range(IH):
        row = gy * IW
        for gx in range(IW):
            i = row + gx
            if not I.water[i]:
                continue
            d = d_land[i]
            if river[i] or pool[i]:
                deep = 4 if river[i] else 6
                c = LAGOON[3] if d <= 1 else LAGOON[2] if d < deep else (
                    LAGOON[0] if smooth_noise(gx, gy, 12, 1220) > 0.62 else LAGOON[1])
                if d > 1 and (gx * 3 + gy * 2) % 13 == 0 and noise2(gx // 3, gy // 3, 1221) > 0.55:
                    c = LAGOON[3]  # a ripple carried on the current
            elif lag[i]:
                if d <= 1:
                    c = LAGOON[4]
                elif d <= 5:
                    c = LAGOON[3] if d < 4 or noise2(gx // 2, gy // 2, 1222) > 0.4 else LAGOON[2]
                elif d <= 14:
                    c = LAGOON[2] if d < 10 or noise2(gx // 2, gy // 2, 1223) * 6 > d - 9 else LAGOON[1]
                else:
                    c = LAGOON[1] if smooth_noise(gx, gy, 26, 1224) > 0.3 else LAGOON[2]
                if d > 3 and (gy + int(math.sin(gx / 9) * 2)) % 17 == 0 and noise2(gx // 6, gy, 1225) > 0.45:
                    c = LAGOON[3]
            else:
                # the open sea: surf on the shore, a second line of breakers, then deep
                # water with long swells like the sea round the island (beyond_sea)
                if d <= 1:
                    c = FOAM if noise2(gx // 2, gy // 2, 1226) > 0.15 else SEA[3]
                elif d <= 3:
                    c = '#DDEBEE' if (gx + gy) % 3 == 0 else SEA[3]
                elif d <= 7:
                    c = SEA[2]
                    if d == 6 and smooth_noise(gx, gy, 12, 1227) > 0.58:
                        c = '#DDEBEE'
                elif d <= 14:
                    c = SEA[2] if noise2(gx // 2, gy // 2, 1228) * 7 > d - 8 else SEA[1]
                else:
                    c = SEA[0] if smooth_noise(gx, gy, 40, 861) > 0.55 else SEA[1]
                    swell = (gy + int(math.sin(gx / 23) * 4 + smooth_noise(gx, gy, 60, 862) * 8)) % 19
                    if swell == 0:
                        c = SEA[2]
                    elif swell == 1 and noise2(gx // 5, gy // 19, 863) > 0.8:
                        c = FOAM
            _put(px, gx, gy, c)

    # the reef: coral heads in the shallows, gaps where the tide runs, surf outside
    for i in range(N):
        if reef[i] and not solid[i]:
            gx, gy = i % IW, i // IW
            if smooth_noise(gx, gy, 7, 1230) > 0.64:
                continue  # a channel through the reef
            n = noise2(gx // 2, gy // 2, 1231)
            _put(px, gx, gy, CORAL[0] if n < 0.3 else CORAL[1] if n < 0.6 else LAGOON[4] if n < 0.85 else CORAL[2])
    for i in range(N):
        if sea[i] and not reef[i]:
            gx, gy = i % IW, i // IW
            near = any(0 <= gx + dx < IW and 0 <= gy + dy < IH and reef[(gy + dy) * IW + gx + dx]
                       for (dx, dy) in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, 2), (2, -2), (-2, -2)))
            if near and noise2(gx // 2, gy // 2, 1232) > 0.3:
                _put(px, gx, gy, FOAM if (gx + gy) % 2 else '#DDEBEE')

    # ---- rocks along every exposed shore: worn basalt boulders the surf breaks on
    taken = {}
    for gy in range(IH):
        for gx in range(IW):
            i = gy * IW + gx
            if not land[i] or d_sea[i] != 1 or d_lag[i] <= 8:
                continue
            if BEACH[0] + 14 <= gx <= BEACH[1] - 14 and gy > 900:
                continue  # the beach itself
            if 150 <= gx <= 214 and gy < 110:
                continue  # the rainforest's small sandy bay
            key = (gx // 6, gy // 6)
            if any(taken.get((key[0] + a, key[1] + b)) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            taken[key] = True
            if noise2(gx, gy, 1239) < 0.3:
                continue
            big = noise2(gx, gy, 1240)
            rx = 3.5 + big * big * 6
            ry = 2.5 + big * big * 4 + noise2(gx, gy, 1241)
            pts = {(x, y) for (x, y) in oval(gx, gy, rx, ry) if 0 <= x < IW and 0 <= y < IH}
            if len(pts) > 6:
                style.facet_stone(cv, pts, BASALT_R, moss=TROPIC if noise2(gx, gy, 1242) > 0.6 else None,
                                  seed=1243 + gx + gy, outline=None)
                for (x, y) in pts:
                    I.blocked[y * IW + x] = 1
    # the rainforest's bay: a strip of pale sand under the trees
    for gy in range(40, 110):
        for gx in range(150, 215):
            i = gy * IW + gx
            if land[i] and d_sea[i] <= 6 + int(smooth_noise(gx, gy, 9, 1244) * 6):
                _put(px, gx, gy, S[1] if d_sea[i] <= 1 else S[2] if noise2(gx, gy, 914) > 0.2 else S[1])

    # ---- the mangrove fringe round the river's mouth: roots in the brackish water
    for gy in range(780, 990, 7):
        for gx in range(10, 150, 8):
            x = gx + int(noise2(gx, gy, 1250) * 6)
            y = gy + int(noise2(gx, gy, 1251) * 6)
            i = y * IW + x
            if not lag[i] or not 2 <= d_land[i] <= 11 or _seg_dist(x, y, RIVER[-4:]) < 13:
                continue
            if noise2(gx, gy, 1252) > 0.8:
                continue
            _mangrove(cv, I, x, y, 1253 + gx * 7 + gy)
    for k, (cx, cy, rx, ry, green) in enumerate(ISLETS):
        _islet(cv, I, islet, cx, cy, rx, ry, green, 1260 + k)

    # ---- the Headwaters: the old volcano's flank, the falls and their pool
    _flank(cv, I, land)
    _falls(cv, I, pool)
    _heights(cv, I, land, river, d_fresh)
    _ground_detail(cv, I, land, d_fresh)

    for i in range(N):
        if I.water[i] or islet[i]:
            I.blocked[i] = 1
    return I


def _mangrove(cv: Canvas, I: Island, x: int, y: int, seed: int):
    """A mangrove: a low dark crown on arching roots standing in the shallows."""
    rx = 6 + noise2(seed, 1, 7) * 3
    ry = 4 + noise2(seed, 2, 7) * 2
    tmp = Canvas(30, 24)
    shape = style.leafy(tmp, 15, 9, rx, ry, MANGROVE, r=1.6, seed=seed)
    roots = set()
    for k in range(-2, 3):
        rx0 = 15 + k * 3
        for t in range(5):
            roots.add((rx0 + (k * t) // 4, 9 + int(ry) - 1 + t))
    for (a, b) in roots:
        if (a, b) not in shape:
            tmp.set(a, b, ROOT_C[1] if a < 15 else ROOT_C[0])
            if b == 9 + int(ry) + 3:
                tmp.set(a, b + 1, LAGOON[1])  # the root's shadow in the water
    for (a, b) in shape:
        if (a + 1, b + 1) not in shape and (a, b + 1) not in shape:
            tmp.set(a, b, MANGROVE[0])
    ox, oy = x - 15, y - 9 - int(ry)
    for (a, b) in shape | roots:
        gx, gy = ox + a, oy + b
        if 0 <= gx < IW and 0 <= gy < IH:
            cv.set(gx, gy, tmp.get(a, b))
            I.blocked[gy * IW + gx] = 1


def _islet(cv: Canvas, I: Island, mask: bytearray, cx, cy, rx, ry, green: bool, seed: int):
    """A small island off the coast: worn basalt, wooded on top if it is big enough."""
    pts = {(i % IW, i // IW) for i in range(max(0, (cy - ry - 3) * IW), min(N, (cy + ry + 3) * IW)) if mask[i]}
    style.facet_stone(cv, pts, BASALT_R, moss=TROPIC, seed=seed, outline=None)
    if green:
        tmp = Canvas(2 * rx + 8, 2 * ry + 8)
        shape = style.leafy(tmp, rx + 4, ry + 1, rx * 0.75, ry * 0.7, TROPIC, r=2.0, seed=seed)
        for (a, b) in shape:
            cv.set(cx - rx - 4 + a, cy - ry - 4 + b, tmp.get(a, b))


def _flank(cv: Canvas, I: Island, land: bytearray):
    """The volcano's flank across the Headwaters' top: a steep jumble of great mossy
    basalt blocks stepping up out of the forest, ferns in the joints (blocked)."""
    flank = set()
    tops = {}
    for gx in range(320, IW):
        tops[gx] = flank_top(gx)
        for gy in range(0, tops[gx]):
            if land[gy * IW + gx]:
                cv.set(gx, gy, TROPIC[0] if (gx + gy) % 3 else BASALT_R[1])
                flank.add((gx, gy))
    blocks = []
    for i in range(70):  # back (high) to front (low), so the lower blocks overlap
        bx = W + int(noise2(i, 0, 951) * (W + 20)) - 10
        by = int(noise2(i, 1, 951) * 150) - 20
        if by + 8 > tops.get(max(W, min(IW - 1, bx)), 0):
            continue
        blocks.append((by, bx, 10 + noise2(i, 2, 951) * 12, 7 + noise2(i, 3, 951) * 7, i))
    for (by, bx, rx, ry, i) in sorted(blocks):
        pts = {(x, y) for (x, y) in oval(bx, by, rx, ry) if (x, y) in flank}
        if len(pts) > 12:
            style.facet_stone(cv, pts, BASALT_R, moss=TROPIC, seed=960 + i, outline=None)
    for i in range(40):  # ferns and moss tumbling from the joints
        fx = W + int(noise2(i, 4, 951) * W)
        top = tops[max(W, min(IW - 1, fx))]
        fy = int(noise2(i, 5, 951) * (top - 6))
        if (fx, fy) not in flank or top < 60:
            continue
        tmp = Canvas(20, 16)
        shape = style.leafy(tmp, 10, 8, 4 + noise2(i, 6, 951) * 3, 3, TROPIC, r=1.8, seed=970 + i)
        for (a, b) in shape:
            if (fx - 10 + a, fy - 8 + b) in flank:
                cv.set(fx - 10 + a, fy - 8 + b, tmp.get(a, b))
    for gx in range(W, IW):  # the forest's dark edge at the flank's foot
        if tops[gx] - coast_north(gx) < 6:
            continue
        for d in range(3):
            if (gx, tops[gx] - 1 - d) in flank:
                cv.set(gx, tops[gx] - 1 - d, TROPIC[0] if d == 0 else TROPIC[1] if (gx + d) % 2 else BASALT_R[0])
    for (x, y) in flank:
        I.blocked[y * IW + x] = 1


def _falls(cv: Canvas, I: Island, pool: bytearray):
    """The fall: white water down the flank into the pool, foam where it lands."""
    top = int(coast_north(FALLS_X)) + 10
    for gy in range(top, 160):
        half = 7 + gy / 40
        for gx in range(FALLS_X - 20, FALLS_X + 20):
            off = abs(gx - FALLS_X - math.sin(gy / 17) * 1.5)
            if off < half:
                streak = (gx * 5 + int(gy * 0.15)) % 7
                cv.set(gx, gy, FOAM if streak < 3 else LAGOON[4] if off < half - 2 else LAGOON[3])
                I.blocked[gy * IW + gx] = 1
                I.water[gy * IW + gx] = 1
            elif off < half + 2:
                cv.set(gx, gy, BASALT_R[0])
    pcx, pcy = POOL[0], POOL[1]
    for i in range(N):
        if pool[i]:
            gx, gy = i % IW, i // IW
            d = math.hypot(gx - pcx, (gy - (pcy - 22)) * 1.4)
            if d < 14 and noise2(gx - W, gy, 956) * 14 > d - 2:
                cv.set(gx, gy, FOAM if (gx + gy) % 2 else LAGOON[4])


def _heights(cv: Canvas, I: Island, land: bytearray, river: bytearray, d_fresh: bytearray):
    """The island's three heights: basalt escarpments in courses where the ground steps
    down to the south (their faces seen from the front) or to the west (seen edge on), a
    cascade where the river goes over one, the gorge it has cut below, the switchback's
    vegetated slope, and the broad stairs where the trails go up and down."""
    px = cv.img.load()
    X12 = [x12(gy) for gy in range(IH)]
    Y01 = [y01(gx) for gx in range(IW)]
    Y2A = [y2a(gx) for gx in range(IW)]
    Y2B = [y2b(gx) for gx in range(IW)]
    T = [[0] * IW for _ in range(IH)]
    for gy in range(IH):
        row = T[gy]
        for gx in range(IW):
            row[gx] = tier(gx, gy, X12, Y01, Y2A, Y2B)
    wet = lambda i: river[i]  # noqa: E731
    face = {}  # (gx, gy) -> (row in the face, its height)
    for gx in range(IW):
        for gy in range(1, IH):
            drop = T[gy - 1][gx] - T[gy][gx]
            # (a front face only where an east-west line steps down; where the
            # north-south escarpment shifts a column it is seen edge on, below)
            if drop > 0 and ((gx >= X12[gy - 1]) == (gx >= X12[gy]) or abs(X12[gy] - X12[gy - 1]) > 6):
                fh = FACE * drop
                for r in range(fh):
                    if gy + r < IH:
                        face[(gx, gy + r)] = (r, fh)
    side = set()
    edges = []
    for gy in range(IH):
        for gx in range(1, IW):
            if T[gy][gx - 1] != T[gy][gx]:
                edges.append((gx, gy))
                for d in range(-5, 6):
                    if (gx + d, gy) not in face:
                        side.add((gx + d, gy))
    # the switchback's slope: a steep bank of fern and rock instead of a sheer face
    sx0, sy0, sy1 = SLOPE
    slope = {(gx, gy) for gy in range(sy0, sy1) for gx in range(sx0, int(X12[gy]) + 6)}
    side -= slope
    zig = _thick(ZIGZAG, 6.5, 0)
    stairs = []
    for key, (a, b) in STAIR_XS.items():
        line = Y01 if key == 'west' else Y2A if key == 'east' else Y2B
        top = int(min(line[a:b])) - 1
        bottom = int(max(line[a:b])) + FACE + 1
        if key != 'terrace':  # (a border stair runs well past the seam on both sides)
            top, bottom = min(top, H - 14), max(bottom, H + 14)
        stairs.append((a, top, b - a, bottom - top))
    I.stairs = stairs
    in_stair = {(x, y) for (x0, y0, w, h) in stairs for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
    O = BASALT_R
    for (gx, gy), (r, fh) in face.items():
        i = gy * IW + gx
        if not (land[i] or wet(i)) or (gx, gy) in in_stair:
            continue
        if wet(i):  # the river pours over the edge
            c = FOAM if (gx * 3 + r * 2) % 5 < 2 else LAGOON[4] if r < fh - 2 else LAGOON[3]
            _put(px, gx, gy, c)
            continue
        course, k = (r - 1) // 4, (r - 1) % 4
        off = int(noise2(course, gx // 9, 1310) * 9)
        joint = (gx + off) % 9 == 0
        if r == 0:
            c = TROPIC[4] if (gx // 2) % 3 else TROPIC[3]  # the grass lip, catching the light
        elif r == fh - 1:
            c = O[0]
        elif joint:
            c = O[0]
        elif k == 0:
            c = O[3] if (gx + off) % 9 < 6 else O[2]
        elif k == 3:
            c = TROPIC[1] if noise2(gx, course, 1311) > 0.7 else O[1]
        else:
            c = O[2] if (gx + off + 1) % 9 else O[1]
        if r and noise2(gx // 2, 0, 1312) > 0.86 and r < 2 + int(noise2(gx, 1, 1313) * (fh - 2)):
            c = TROPIC[2] if gx % 2 else TROPIC[3]  # a fern or a vine hanging over
        _put(px, gx, gy, c)
        I.blocked[i] = 1
    for (gx, gy), (r, fh) in face.items():  # its shadow at the foot
        if r == fh - 1 and (gx, gy + 1) not in face and 0 <= gy + 2 < IH:
            for d in (1, 2):
                j = (gy + d) * IW + gx
                if land[j] and (gx, gy + d) not in in_stair:
                    style.darken(cv, gx, gy + d)
                elif wet(j):
                    _put(px, gx, gy + d, FOAM if (gx + d) % 2 else LAGOON[4])
    for (gx, gy) in side:
        i = gy * IW + gx
        if not (0 <= gx < IW) or not (land[i] or wet(i)) or (gx, gy) in in_stair:
            continue
        e = gx - int(X12[gy])
        if wet(i):  # the falls into the gorge, seen edge on
            _put(px, gx, gy, FOAM if (gy * 3 + gx) % 5 < 2 else LAGOON[4])
            continue
        if e >= 5:
            c = TROPIC[4] if gy % 3 else TROPIC[3]
        elif e <= -5:
            c = O[0]
        elif gy % 5 == 0 or e <= -4:
            c = O[1]
        else:
            c = O[3] if e < 1 and (gy // 5 + gx) % 3 else O[2]
        _put(px, gx, gy, c)
        I.blocked[i] = 1
    for (gx, gy) in slope:
        i = gy * IW + gx
        if not land[i]:
            continue
        if zig[i]:
            continue
        n = smooth_noise(gx, gy, 5, 1314)
        c = O[2] if n > 0.7 else O[3] if n > 0.64 else TROPIC[1] if n < 0.3 or (gx + gy) % 2 else TROPIC[2]
        _put(px, gx, gy, c)
        I.blocked[i] = 1
    I.zig = {(i % IW, i // IW) for i in range(sy0 * IW, (sy1 + 8) * IW) if zig[i] and land[i]}
    # bushes leaning over each escarpment's lip, scree fallen at its foot
    near_stair = {(x, y) for (x0, y0, w, h) in stairs for y in range(y0 - 10, y0 + h + 10)
                  for x in range(x0 - 8, x0 + w + 8)}
    lips, feet = [], []
    for (gx, gy), (r, fh) in face.items():
        if r == 0 and smooth_noise(gx, gy, 26, 1315) > 0.48 and noise2(gx, gy // 8, 1314) < 0.2:
            lips.append((gx, gy - 1))
            feet.append((gx + int(noise2(gx, gy, 1316) * 6) - 3, gy + fh + 3))
    for (gx, gy) in edges:
        if smooth_noise(gx, gy, 26, 1317) > 0.48 and noise2(gx // 8, gy, 1316) < 0.16 and (gx, gy) not in slope:
            lips.append((gx + 7, gy))
            feet.append((gx - 9, gy + int(noise2(gx, gy, 1318) * 4)))
    for k, (gx, gy) in enumerate(lips):
        i = gy * IW + gx
        if not (0 < gx < IW - 1 and 0 < gy < IH - 1) or not land[i] or (gx, gy) in near_stair or (gx, gy) in slope:
            continue
        if noise2(gx, gy, 1319) < 0.25 or d_fresh[i] < 10:
            continue
        rx, ry = 4 + noise2(gx, gy, 1321) * 4, 3 + noise2(gx, gy, 1322) * 2
        tmp = Canvas(24, 18)
        shape = style.leafy(tmp, 12, 9, rx, ry, TROPIC, r=1.7, seed=1323 + k)
        for (a, b) in shape:
            x, y = gx - 12 + a, gy - 9 + b
            if 0 <= x < IW and 0 <= y < IH and land[y * IW + x]:
                cv.set(x, y, tmp.get(a, b))
                I.blocked[y * IW + x] = 1
    for k, (gx, gy) in enumerate(feet):
        if not (2 < gx < IW - 3 and 2 < gy < IH - 3) or (gx, gy) in near_stair or (gx, gy) in slope:
            continue
        i = gy * IW + gx
        if not land[i] or d_fresh[i] < 9 or (gx, gy) in face or noise2(gx, gy, 1324) < 0.35:
            continue
        rr = 2 + noise2(gx, gy, 1325) * 2.5
        pts = {(x, y) for (x, y) in oval(gx, gy, rr + 1, rr) if land[y * IW + x] and (x, y) not in face}
        if len(pts) > 4:
            style.facet_stone(cv, pts, O, seed=1326 + k, outline=None)
            for (x, y) in pts:
                I.blocked[y * IW + x] = 1
    # the gorge below the falls: basalt walls either side of the river
    for gy in range(260, 360):
        lip = int(X12[gy])
        for gx in range(lip - 64, lip - 2):
            i = gy * IW + gx
            rim = 5 + (8 if abs(gx - 320) < 16 and gy < 300 else 0)
            if land[i] and 1 <= d_fresh[i] <= rim and (gx, gy) not in face and (gx, gy) not in side:
                below = river[i + IW] if gy + 1 < IH else 0
                c = O[0] if d_fresh[i] == 1 else O[1] if below else O[3] if d_fresh[i] == rim else O[2]
                _put(px, gx, gy, c)
                I.blocked[i] = 1
    # the trails, in island px (painted zone by zone over the cut, see `paint`)
    for line in TRAILS:
        m = _thick(line, TRAIL_W, 1320)
        I.trail |= {(i % IW, i // IW) for i in range(N) if m[i]}
    for (gx, gy) in in_stair:
        I.blocked[gy * IW + gx] = 0
    for i in range(sy0 * IW, (sy1 + 8) * IW):
        if zig[i] and land[i]:
            I.blocked[i] = 0


def _ground_detail(cv: Canvas, I: Island, land: bytearray, d_fresh: bytearray):
    """Small things on the open ground, in clusters of two or more pixels (art-style.md,
    detail target): grass tufts and a few flowers on the turf, leaf litter and fern
    sprigs on the forest floor, shells and wrack on the pale sand, pebbles on the black,
    and the falls' spray drifting over the ground round the pool and the gorge."""
    px = cv.img.load()
    turf = {_rgb(c) for c in TROPIC[1:4]}
    floor = {_rgb(c) for c in FLOOR[1:5]}
    pale = {_rgb(c) for c in MATERIALS['sand']}
    black = {_rgb(c) for c in BASALT_R[1:4]}
    trail = I.trail

    def clear(x, y, r=2):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                j = (y + dy) * IW + x + dx
                if not (0 <= x + dx < IW and 0 <= y + dy < IH) or I.blocked[j] or not land[j] or (x + dx, y + dy) in trail:
                    return False
        return True

    for ty in range(4, IH - 4, 6):
        for tx in range(4, IW - 4, 6):
            x = tx + int(noise2(tx, ty, 1400) * 5)
            y = ty + int(noise2(tx, ty, 1401) * 5)
            r = noise2(tx, ty, 1402)
            if not clear(x, y):
                continue
            c = px[x, y][:3]
            if c in turf:
                if r < 0.16:
                    style.tuft(cv, x, y, TROPIC[1], TROPIC[4], tall=3 if r < 0.05 else 2)
                elif r < 0.19:
                    petal = ('#F2EEE6', '#E8C85A', '#E07A6A')[int(noise2(tx, ty, 1403) * 3)]
                    cv.set(x, y, petal); cv.set(x + 1, y, petal); cv.set(x, y + 1, petal)
                    cv.set(x + 1, y + 1, TROPIC[1])
            elif c in floor:
                if r < 0.12:  # fallen leaves
                    leaf = '#7A6A3A' if noise2(tx, ty, 1404) > 0.5 else '#5E5A2E'
                    cv.set(x, y, leaf); cv.set(x + 1, y, leaf); cv.set(x + 1, y + 1, FLOOR[0])
                elif r < 0.2:  # a fern sprig
                    for d in range(3):
                        cv.set(x - d, y - d, FLOOR[4] if d else FLOOR[3]); cv.set(x + d, y - d, FLOOR[3])
                    cv.set(x, y + 1, FLOOR[1])
            elif c in pale and r < 0.1:
                if noise2(tx, ty, 1405) > 0.6:
                    cv.set(x, y, '#F2EEE6'); cv.set(x + 1, y, '#D8C8B0')  # a shell
                else:
                    for d in range(4):  # a line of wrack along the strand
                        cv.set(x + d, y + (d // 2), '#4A5A3A' if d % 2 else '#3A4A2E')
            elif c in black and r < 0.1:
                cv.set(x, y, '#9AA4A8'); cv.set(x + 1, y, '#C9D2D6'); cv.set(x, y + 1, BASALT_R[0])
    # the spray: a pale drift over the ground round the pool and below the gorge's lip
    for (cx, cy, rad) in ((POOL[0], POOL[1] + 10, 70), (int(x12(300)) - 14, 304, 36)):
        for y in range(cy - rad, cy + rad):
            for x in range(cx - rad, cx + rad):
                if not (0 <= x < IW and 0 <= y < IH):
                    continue
                d = math.hypot(x - cx, (y - cy) * 1.3) / rad
                if d >= 1 or not land[y * IW + x]:
                    continue
                if noise2(x // 2, y // 2, 1406) < (1 - d) * 0.35:
                    r0, g0, b0, a0 = px[x, y]
                    px[x, y] = (int(r0 + (232 - r0) * 0.28), int(g0 + (244 - g0) * 0.28), int(b0 + (240 - b0) * 0.28), a0)


def cut(zone: str):
    """This zone's piece of the island: its ground, and its water and blocked ground in
    zone pixels."""
    I = island()
    col, row = LAYOUT['isles'][zone]
    ox, oy = col * W, row * H
    cv = Canvas(W, H)
    cv.img.paste(I.cv.img.crop((ox, oy, ox + W, oy + H)), (0, 0))
    water, blocked = set(), set()
    for y in range(H):
        base = (y + oy) * IW + ox
        for x in range(W):
            if I.water[base + x]:
                water.add((x, y))
            if I.blocked[base + x]:
                blocked.add((x, y))
    return cv, water, blocked, ox, oy


def _stair(cv: Canvas, x0: int, y0: int, w: int, h: int, gy0: int):
    """A broad stair of basalt steps between low walls; returns (steps, walls). The
    treads are laid from island row 576, so the stair matches itself across a border."""
    steps, walls = set(), set()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            a = min(x - x0, x0 + w - 1 - x)
            if a < 2:
                walls.add((x, y))
                c = STONE[0] if a == 0 or (x - x0 > 1 and y % 4 == 3) else STONE[2]
                if y == y0:
                    c = STONE[3]
            else:
                steps.add((x, y))
                g = gy0 + y - y0 - H
                k = g % 6
                c = STONE[4] if k == 0 else STONE[3] if k < 3 else STONE[2] if k < 5 else STONE[1]
                if k in (2, 3) and (x * 7 + (g // 6) * 3) % 11 == 0:
                    c = STONE[1]  # the joint between two slabs
            cv.set(x, y, c)
    return steps, walls


def paint(zone: str):
    """Cut this zone from the island and lay its share of the trails, stairs and
    footbridges over it. Returns (canvas, water, blocked, deck, ox, oy)."""
    I = island()
    cv, water, blocked, ox, oy = cut(zone)
    mask = {(x - ox, y - oy) for (x, y) in I.trail if ox - 2 <= x < ox + W + 2 and oy - 2 <= y < oy + H + 2}
    paint_road(cv, mask)
    for (gx, gy) in I.zig:  # the switchback, over the trail's grass edge
        x, y = gx - ox, gy - oy
        if 0 <= x < W and 0 <= y < H:
            c = P[4] if smooth_noise(gx, gy, 7, 40) > 0.7 else P[3]
            if (gx, gy + 1) not in I.zig:
                c = P[1]  # the downhill edge
            elif gx % 6 == 0 and (gx - 2, gy) in I.zig and (gx + 2, gy) in I.zig:
                c = P[2]  # a step
            cv.set(x, y, c)
    open_ = set()
    shut = set()
    for (x0, y0, w, h) in I.stairs:
        if x0 + w > ox and x0 < ox + W and y0 + h > oy and y0 < oy + H:
            steps, walls = _stair(cv, x0 - ox, y0 - oy, w, h, y0)
            open_ |= steps
            shut |= walls
    for (x0, y0, w, h) in BRIDGES:
        if ox <= x0 < ox + W and oy <= y0 < oy + H:
            deck, rails = plank_bridge(cv, x0 - ox, y0 - oy, w, h, vertical=True)
            open_ |= deck
            shut |= rails
    inside = lambda pts: {(x, y) for (x, y) in pts if 0 <= x < W and 0 <= y < H}  # noqa: E731
    return cv, water, (blocked - open_) | inside(shut) | (water - open_), inside(open_), ox, oy


def _stand(gx: int, gy: int, ox: int, oy: int):
    return (gx - ox, gy - oy)


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


@functools.lru_cache(maxsize=1)
def _sprites():
    return sprites()


@functools.lru_cache(maxsize=1)
def _routes() -> dict:
    """The residents' walks (lib/resident-routes.ts), so planting keeps clear of them."""
    import re
    src = open(os.path.join(worlds.ROOT, 'lib', 'resident-routes.ts')).read()
    out = {}
    for (zone, a, b, c, d) in re.findall(r"zone: '(\w+)', from: \[(\d+), (\d+)\], to: \[(\d+), (\d+)\]", src):
        out.setdefault(zone, []).append((int(a), int(b), int(c), int(d)))
    return out


def _kind(cv: Canvas, x: int, y: int) -> str:
    c = cv.get(x, y)[:3]
    if c in {_rgb(k) for k in MATERIALS['sand']}:
        return 'sand'
    if c in {_rgb(k) for k in BASALT_R[1:4]}:
        return 'black'
    if c in {_rgb(k) for k in FLOOR}:
        return 'floor'
    return 'turf'


def scatter(cv: Canvas, zone: str, blocked: set, objects: list, stands: dict, rules, seed: int,
            trail_gap: int = 14) -> list:
    """Plant more along the edges of a place (art-style.md: clutter gathers at the
    edges, the paths and the space round the companion stay open). Each rule is (key,
    how many, the ground kinds it grows on). A prop goes only where its foot is on open
    ground of that kind, clear of the trail by `trail_gap`, of every stand and of the
    other props, and inside the zone."""
    sm = _sprites()
    I = island()
    feet = []
    for (_i, k, x, y) in objects:
        sp = sm[k]
        feet.append((x + sp.ox - 3, y + sp.oy + sp.h - 12, x + sp.ox + sp.w + 3, y + sp.oy + sp.h + 4))
    path = blocked
    out = []
    col, row = LAYOUT['isles'][zone]
    ox, oy = col * W, row * H
    trail = {(x - ox, y - oy) for (x, y) in I.trail if ox - 30 <= x < ox + W + 30 and oy - 30 <= y < oy + H + 30}
    trail |= {(x - ox, y - oy) for (x, y) in I.zig}
    near_trail = set()
    for (x, y) in trail:
        if x % 3 == 0 and y % 3 == 0:
            for dy in range(-trail_gap, trail_gap + 1, 3):
                for dx in range(-trail_gap, trail_gap + 1, 3):
                    near_trail.add(((x + dx) // 3, (y + dy) // 3))
    for r, (key, n, kinds) in enumerate(rules):
        sp = sm[key]
        placed = 0
        for t in range(400):
            if placed >= n:
                break
            fx = int(noise2(t, r, seed) * (W - sp.w - 4)) + 2   # the sprite's left
            fy = int(noise2(t, r, seed + 1) * (H - sp.h - 8)) + 4  # its top
            x0, x1, yb = fx + 2, fx + sp.w - 2, fy + sp.h
            if fy < 2 or yb > H - 4 or (row == 0 and fy < 6):
                continue
            cx = (x0 + x1) // 2
            if _kind(cv, cx, yb - 2) not in kinds:
                continue
            if any((x, y) in path for x in range(x0, x1, 2) for y in range(yb - 8, yb + 2, 2)):
                continue
            if any(((x // 3), (y // 3)) in near_trail for x in range(x0, x1, 3) for y in range(yb - 10, yb + 3, 3)):
                continue
            if any(x0 - 18 < sx < x1 + 18 and yb - 30 < sy < yb + 18 for (sx, sy) in stands.values()):
                continue
            if any(fx - 12 < max(a, c) and fx + sp.w + 12 > min(a, c) and fy - 4 < max(b, d) and yb + 34 > min(b, d)
                   for (a, b, c, d) in _routes().get(zone, [])):
                continue  # a resident walks here
            box = (fx - 3, yb - 12, fx + sp.w + 3, yb + 4)
            if any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1] for b in feet):
                continue
            feet.append(box)
            # (objects are given before the sprite's own offset, as in the zones' lists)
            out.append((f'{key}-s{placed}', key, fx - sp.ox, fy - sp.oy))
            placed += 1
    return out



def isle_landing(frame: int = 0):
    """Lagoon Landing (sea level): the island's one pier, where the ferry from Driftwood
    ties up, out over the sheltered lagoon inside the reef. The river from the rainforest
    comes down over the escarpment on the west and spreads into the lagoon through a
    fringe of mangroves; the dry shore lane climbs beside it to the broad stair, and the
    shore path goes east round the basalt headland to the cove."""
    cv, water, blocked, deck, ox, oy = paint('landing')
    # the pier: planks out over the shallows to where the ferry ties up (Codex's anchor,
    # island-pier at (112, 440))
    pier, rails = plank_bridge(cv, 99, 368, 26, 104, vertical=True)
    objects = [
        ('boathouse', 'boathouse', 146, 272), ('ferry', 'island_ferry', 128, 432), ('canoe', 'canoe', 196, 388),
        ('palm-1', 'palm', 236, 110), ('palm-2', 'palm', 262, 292), ('palm-3', 'palm', 60, 200),
        ('fern-1', 'tree_fern', 250, 40), ('fern-2', 'tree_fern', 100, 60), ('jt-1', 'jungle_tree', 196, 20),
        ('hib-1', 'hibiscus', 190, 140), ('hib-2', 'hibiscus', 268, 236), ('mon-1', 'monstera', 216, 180),
        ('rock-1', 'black_rock_small', 290, 424), ('heron', 'heron', 64, 330),
    ]
    objects += scatter(cv, 'landing', blocked | pier | rails, objects, {'pier': (112, 440), 'boathouse': (184, 352)}, [
        ('palm', 4, {'turf', 'sand'}), ('pandanus', 4, {'sand', 'turf'}), ('banana', 3, {'turf'}),
        ('bird_of_paradise', 3, {'turf'}), ('hibiscus', 2, {'turf'}), ('bush', 3, {'turf'}), ('fern', 6, {'turf', 'floor'}),
        ('crab', 2, {'sand'}), ('driftwood', 2, {'sand'})], 1501)
    WATER_MASKS['isle_landing'] = water - pier - deck
    stands = {'pier': (112, 440), 'rainforest': (156, 6), 'cove': (314, 382), 'boathouse': (184, 352)}
    return cv, objects, stands, (blocked - pier) | rails


def isle_rainforest(frame: int = 0):
    """The Rainforest (one step up): a stream valley under a closed canopy, giants with
    buttress roots, tree ferns and big-leafed plants, the floor dark and damp. The river
    falls into it through a gorge from the Headwaters, winds west and turns south over
    the escarpment for the lagoon; the trail crosses it on a footbridge. The sea breaks
    on black rocks along the north and west, with one small sandy bay."""
    cv, water, blocked, deck, ox, oy = paint('rainforest')
    objects = [
        ('jt-1', 'jungle_tree', 52, 120), ('jt-2', 'jungle_tree', 90, 210), ('jt-3', 'jungle_tree', 210, 420),
        ('jt-4', 'jungle_tree', 30, 340), ('palm-1', 'palm', 176, 34),
        ('fern-1', 'tree_fern', 170, 130), ('fern-2', 'tree_fern', 40, 250), ('fern-3', 'tree_fern', 250, 360),
        ('fern-4', 'tree_fern', 20, 480), ('fern-5', 'tree_fern', 230, 500), ('mon-1', 'monstera', 120, 290),
        ('mon-2', 'monstera', 200, 200), ('mon-3', 'monstera', 30, 420), ('mon-4', 'monstera', 200, 520),
        ('hib', 'hibiscus', 250, 120), ('log', 'mossy_log', 210, 240),
    ]
    objects += scatter(cv, 'rainforest', blocked, objects, {'bridge': (165, 404)}, [
        ('jungle_tree', 4, {'floor'}), ('tree_fern', 6, {'floor'}), ('monstera', 6, {'floor', 'turf'}),
        ('banana', 2, {'floor'}), ('bird_of_paradise', 2, {'floor', 'turf'}), ('fern', 10, {'floor'}),
        ('pandanus', 2, {'sand'})], 1502)
    WATER_MASKS['isle_rainforest'] = water - deck
    stands = {'landing': (156, H - 6), 'headwaters': (314, 266), 'bridge': (165, 404)}
    return cv, objects, stands, blocked


def isle_headwaters(frame: int = 0):
    """The Headwaters (two steps up): the island's old volcano rises behind, its flank
    green with moss and fern, and a waterfall drops from it into a deep round pool. The
    river leaves the pool west across the upland and goes over the escarpment into the
    gorge; the switchback climbs the slope beside it, a footbridge carries the trail over
    the river well above the lip, and a spur goes to the pool's edge. The trail leaves by
    the east shoulder, down a broad stair to the terrace above the cove."""
    cv, water, blocked, deck, ox, oy = paint('headwaters')
    objects = [
        ('fern-1', 'tree_fern', 120, 170), ('fern-2', 'tree_fern', 250, 236), ('fern-3', 'tree_fern', 60, 400),
        ('jt-1', 'jungle_tree', 150, 300), ('jt-2', 'jungle_tree', 10, 440), ('mon-1', 'monstera', 120, 400),
        ('mon-2', 'monstera', 200, 480), ('hib-1', 'hibiscus', 60, 330), ('rock-1', 'black_rock', 250, 380),
        ('rock-2', 'black_rock_small', 100, 500),
    ]
    objects.append(('shelter', 'rain_shelter', 208, 292))  # a place to sit out the rain by the pool
    objects += scatter(cv, 'headwaters', blocked, objects, {'pool': (196, 266)}, [
        ('tree_fern', 5, {'turf', 'floor'}), ('jungle_tree', 2, {'turf', 'floor'}), ('monstera', 4, {'turf', 'floor'}),
        ('bird_of_paradise', 3, {'turf'}), ('hibiscus', 2, {'turf'}), ('banana', 2, {'turf', 'floor'}),
        ('fern', 8, {'turf', 'floor'}), ('black_rock_small', 3, {'turf'})], 1503)
    WATER_MASKS['isle_headwaters'] = water - deck
    stands = {'rainforest': (2, 266), 'pool': (196, 266), 'cove': (220, H - 6)}
    return cv, objects, stands, blocked


def isle_cove(frame: int = 0):
    """Black-sand Cove (sea level): the island's exposed south-east coast. From the
    terrace below the Headwaters a second stair goes down, and the trail comes out of the
    trees above a bay of black volcanic sand where the surf runs in white between basalt
    headlands; a turtle rests above the tide line. The shore path goes west round the
    headland to the lagoon and the landing."""
    cv, water, blocked, deck, ox, oy = paint('cove')
    objects = [
        ('rock-1', 'black_rock', 150, 330), ('rock-2', 'black_rock_small', 80, 392), ('rock-3', 'black_rock', 40, 280),
        ('turtle', 'sea_turtle', 120, 378), ('palm-1', 'palm', 180, 200), ('palm-2', 'palm', 60, 160),
        ('fern-1', 'tree_fern', 110, 40), ('jt-1', 'jungle_tree', 10, 20), ('hib-1', 'hibiscus', 150, 120),
        ('canoe', 'canoe', 190, 380),
    ]
    objects += scatter(cv, 'cove', blocked, objects, {'beach': (166, 388)}, [
        ('palm', 3, {'turf'}), ('pandanus', 3, {'turf', 'black'}), ('driftwood', 3, {'black'}), ('crab', 3, {'black'}),
        ('black_rock_small', 3, {'black', 'turf'}), ('tree_fern', 3, {'turf'}), ('hibiscus', 2, {'turf'}),
        ('bird_of_paradise', 2, {'turf'}), ('fern', 5, {'turf'})], 1504)
    WATER_MASKS['isle_cove'] = water
    stands = {'headwaters': (220, 24), 'landing': (6, 382), 'beach': (166, 388)}
    return cv, objects, stands, blocked


# how each island zone's open ground is dressed (zones.dress)
DRESS.update({'landing': ('meadow', TROPIC[2:4], 0.3), 'headwaters': ('meadow', TROPIC[2:4], 0.3),
              'cove': ('meadow', TROPIC[2:4], 0.26), 'rainforest': ('forest', None, 0.3)})

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
import math

from PIL import Image, ImageDraw

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['ISLE_TRAIL_NS', 'ISLE_TRAIL_WE', 'TROPIC', 'LAGOON', 'BASALT_R', 'FLOOR', 'IW', 'IH', 'island',
           'isle_trail', 'plank_bridge', 'isle_landing', 'isle_rainforest', 'isle_headwaters', 'isle_cove']


# ---- the Tidebloom Isles (Matt, 18 Oct 19:07: the world Codex drew) ----------------
# A dormant volcanic island in the south-west sea, beyond a channel from Driftwood. Four
# zones on a 2 x 2 grid, walked as one loop: the Landing (south-west, the sheltered
# lagoon and the pier), the Rainforest (north-west, a stream valley), the Headwaters
# (north-east, the upland and the falls) and Black-sand Cove (south-east, the exposed
# basalt coast). Fresh water runs from the Headwaters' falls west through the Rainforest
# and south into the lagoon; the walk goes the other way round. Trail crossings, the
# same both sides of each border:
ISLE_TRAIL_NS = 200   # x where the trail crosses the north/south borders
ISLE_TRAIL_WE = {'north': 140, 'south': 380}  # y where it crosses the west/east borders
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


class Island:
    """The island's ground, drawn once: `cv` (IW x IH) and the masks the zones cut."""

    def __init__(self):
        self.cv = Canvas(IW, IH)
        self.blocked = bytearray(N)
        self.water = bytearray(N)


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
            if gx > 300:
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
    return cv, water, blocked


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
    """Lagoon Landing: the island's one pier, where the ferry from Driftwood ties up, out
    over the sheltered lagoon inside the reef. The river from the rainforest comes down
    on the west and spreads into the lagoon through a fringe of mangroves; the trail
    goes north into the forest and east along the shore, round the basalt headland, to
    the cove."""
    cv, water, blocked = cut('landing')
    trail = isle_trail(cv, [(ISLE_TRAIL_NS, -12), (192, 140), (132, 236), (110, 300), (112, 376)], 917)
    trail |= isle_trail(cv, [(150, 212), (232, 246), (282, 330), (300, 370), (W + 12, ISLE_TRAIL_WE['south'])], 918)
    # the pier: planks out over the shallows to where the ferry ties up (Codex's anchor,
    # island-pier at (112, 440))
    pier, rails = plank_bridge(cv, 99, 368, 26, 104, vertical=True)
    objects = [
        ('boathouse', 'boathouse', 146, 272), ('ferry', 'island_ferry', 128, 432), ('canoe', 'canoe', 196, 388),
        ('palm-1', 'palm', 236, 120), ('palm-2', 'palm', 262, 292), ('palm-3', 'palm', 60, 210),
        ('fern-1', 'tree_fern', 250, 30), ('fern-2', 'tree_fern', 120, 40), ('jt-1', 'jungle_tree', 214, 12),
        ('hib-1', 'hibiscus', 150, 120), ('hib-2', 'hibiscus', 268, 236), ('mon-1', 'monstera', 216, 170),
        ('rock-1', 'black_rock_small', 290, 424), ('heron', 'heron', 64, 330),
    ]
    WATER_MASKS['isle_landing'] = water - pier
    stands = {'pier': (112, 440), 'rainforest': (ISLE_TRAIL_NS, 6), 'cove': (314, ISLE_TRAIL_WE['south']),
              'boathouse': (184, 352)}
    return cv, objects, stands, (blocked - pier - trail) | rails | (water - pier)


def isle_rainforest(frame: int = 0):
    """The Rainforest: a stream valley under a closed canopy, giants with buttress roots,
    tree ferns and big-leafed plants, the floor dark and damp. The river from the falls
    winds west through it and turns south for the lagoon, crossed by a footbridge; the
    sea breaks on black rocks along the north and west, with one small sandy bay."""
    cv, water, blocked = cut('rainforest')
    trail = isle_trail(cv, [(ISLE_TRAIL_NS, H + 12), (204, 470), (200, 384), (206, 320), (232, 250), (270, 176),
                            (W + 12, ISLE_TRAIL_WE['north'])], 927)
    deck, rails = plank_bridge(cv, 193, 314, 26, 52, vertical=True)
    objects = [
        ('jt-1', 'jungle_tree', 52, 120), ('jt-2', 'jungle_tree', 100, 200), ('jt-3', 'jungle_tree', 226, 380),
        ('jt-4', 'jungle_tree', 40, 340), ('jt-5', 'jungle_tree', 110, 440), ('jt-6', 'jungle_tree', 150, 30),
        ('fern-1', 'tree_fern', 160, 120), ('fern-2', 'tree_fern', 60, 250), ('fern-3', 'tree_fern', 270, 350),
        ('fern-4', 'tree_fern', 30, 470), ('fern-5', 'tree_fern', 262, 500), ('mon-1', 'monstera', 140, 280),
        ('mon-2', 'monstera', 160, 200), ('mon-3', 'monstera', 40, 420), ('mon-4', 'monstera', 150, 520),
        ('hib', 'hibiscus', 270, 90), ('log', 'mossy_log', 130, 230),
    ]
    WATER_MASKS['isle_rainforest'] = water - deck
    stands = {'landing': (ISLE_TRAIL_NS, H - 6), 'headwaters': (314, ISLE_TRAIL_WE['north']), 'bridge': (206, 380)}
    return cv, objects, stands, ((blocked - deck - trail) | rails | (water - deck))


def isle_headwaters(frame: int = 0):
    """The Headwaters: the island's old volcano rises behind, its flank green with moss
    and fern, and a waterfall drops from it into a deep round pool. The river leaves the
    pool west for the rainforest; a footbridge carries the trail over it, and a spur goes
    to the pool's edge. The sea breaks on the cliffs to the east."""
    cv, water, blocked = cut('headwaters')
    trail = isle_trail(cv, [(-12, ISLE_TRAIL_WE['north']), (50, 160), (100, 204), (130, 256), (150, 330), (196, 430),
                            (ISLE_TRAIL_NS, H + 12)], 938)
    trail |= isle_trail(cv, [(150, 330), (196, 262)], 939)  # the spur to the pool's edge
    deck, rails = plank_bridge(cv, 116, 228, 26, 50, vertical=True)
    objects = [
        ('fern-1', 'tree_fern', 20, 200), ('fern-2', 'tree_fern', 250, 236), ('fern-3', 'tree_fern', 60, 400),
        ('jt-1', 'jungle_tree', 200, 316), ('jt-2', 'jungle_tree', 10, 460), ('mon-1', 'monstera', 160, 380),
        ('mon-2', 'monstera', 196, 470), ('hib-1', 'hibiscus', 80, 330), ('rock-1', 'black_rock', 224, 500),
        ('rock-2', 'black_rock_small', 120, 480),
    ]
    WATER_MASKS['isle_headwaters'] = water - deck
    stands = {'rainforest': (6, ISLE_TRAIL_WE['north']), 'pool': (196, 256), 'cove': (ISLE_TRAIL_NS, H - 6)}
    return cv, objects, stands, ((blocked - deck - trail) | rails | (water - deck))


def isle_cove(frame: int = 0):
    """Black-sand Cove: the island's exposed south-east coast. The trail comes down out
    of the trees onto a bay of black volcanic sand where the surf runs in white between
    basalt headlands; a turtle rests above the tide line. The shore path goes west round
    the headland to the lagoon and the landing."""
    cv, water, blocked = cut('cove')
    trail = isle_trail(cv, [(ISLE_TRAIL_NS, -12), (196, 200), (176, 290), (120, 356), (60, 376),
                            (-12, ISLE_TRAIL_WE['south'])], 948)
    objects = [
        ('rock-1', 'black_rock', 236, 340), ('rock-2', 'black_rock_small', 80, 392), ('rock-3', 'black_rock', 60, 300),
        ('turtle', 'sea_turtle', 120, 378), ('palm-1', 'palm', 222, 200), ('palm-2', 'palm', 60, 200),
        ('fern-1', 'tree_fern', 250, 60), ('jt-1', 'jungle_tree', 20, 30), ('hib-1', 'hibiscus', 110, 120),
        ('canoe', 'canoe', 190, 380),
    ]
    WATER_MASKS['isle_cove'] = water
    stands = {'headwaters': (ISLE_TRAIL_NS, 6), 'landing': (6, ISLE_TRAIL_WE['south']), 'beach': (166, 388)}
    return cv, objects, stands, (blocked - trail) | water


# how each island zone's open ground is dressed (zones.dress)
DRESS.update({'landing': ('meadow', TROPIC[2:4], 0.3), 'headwaters': ('meadow', TROPIC[2:4], 0.3),
              'cove': ('meadow', TROPIC[2:4], 0.26), 'rainforest': ('forest', None, 0.3)})

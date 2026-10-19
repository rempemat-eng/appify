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
import detail
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
# and sand, never as a polygon. Bays and headlands 50 to 160 px across break both long
# coasts (world review 19 Oct 08:04: the island read as a rounded rectangle in quarters).
COAST = [
    # the north coast: the rainforest's rocks, a small sandy bay, the volcano's foot
    (60, 120), (84, 84), (124, 62), (160, 70), (186, 92), (214, 86), (240, 64), (282, 50), (330, 46),
    (400, 36), (470, 38), (540, 46), (586, 66), (612, 110),
    # the east coast: the Headwaters' sea cliffs round a deep bight below the upland
    (606, 170), (598, 232), (604, 290), (586, 318), (560, 336), (538, 362), (528, 398), (534, 434), (554, 458),
    (584, 472), (604, 500), (608, 560),
    # on south past the terrace to the cove's basalt arm, which hooks round to the west
    (612, 620), (600, 690), (608, 760), (600, 830), (606, 900), (612, 960), (614, 1020),
    (606, 1062), (588, 1092), (560, 1104), (534, 1094), (522, 1070), (528, 1042),
    # the cove's black-sand pocket, the basalt headland at the turn into the lagoon
    (512, 1018), (486, 1000), (452, 990), (420, 992), (392, 1004), (370, 1026), (352, 1052), (334, 1064),
    (310, 1063), (288, 1052),
    # the lagoon's shore, the pier's root, the river mouth
    (266, 1012), (232, 994), (190, 980), (150, 970), (112, 962), (84, 950), (62, 922), (48, 886), (40, 846),
    # the west coast, back north: a low point, a bay under the rainforest, a rocky bight
    (30, 796), (18, 750), (14, 700), (20, 660), (34, 620), (26, 560), (30, 520),
    (52, 500), (78, 478), (86, 446), (74, 414), (48, 398), (28, 380), (24, 330), (48, 302), (72, 272), (54, 236),
    (30, 204), (40, 160),
]
# The reef that shelters the lagoon: from the headland round the south-west to the west
# coast. Inside it the water is the lagoon's turquoise; outside, the open sea.
REEF = [(352, 1074), (318, 1094), (262, 1112), (196, 1122), (130, 1120), (76, 1106), (40, 1080), (18, 1040),
        (10, 980), (8, 910), (12, 850), (22, 800)]

# Height (Codex's tiers): the Landing and the Cove at sea level (0), the Rainforest and the
# terrace above the cove one step up (1), the Headwaters' upland two (2). Each step is a
# basalt escarpment that follows a contour, wherever the land puts it, never a zone seam:
# HIGH is the upland's outline (it bulges 40 to 80 px west into the Rainforest and is cut
# back by the notch the river has worn), LOW the outline of everything one step up (it
# crosses y 576 twice). Both run out past the coast; the sea clips them.
HIGH = [(300, -20), (300, 40), (294, 60), (276, 96), (250, 128), (240, 166), (250, 198), (268, 212), (304, 214),
        (326, 210), (342, 198), (362, 194), (380, 202),
        (382, 230), (366, 258), (342, 290), (310, 326), (282, 364), (264, 410), (268, 458), (292, 494), (332, 512),
        (380, 520), (430, 532), (476, 548), (502, 550), (532, 550), (560, 548), (600, 556), (660, 560), (660, -20)]
LOW = [(-20, -20), (660, -20), (660, 690), (610, 692), (566, 680), (532, 668), (500, 668), (470, 652), (440, 630),
       (406, 604), (376, 584), (350, 570), (326, 566), (300, 580), (270, 600), (236, 612), (202, 612), (170, 612),
       (140, 616), (112, 606), (92, 604), (66, 618), (40, 636), (-20, 644)]
FACE = 18  # a cliff face's height for one step of height, in art px

# The fresh water: from the pool under the volcano's fall, west across the upland, over
# the notch's head in a fall to a plunge pool, south-west down the rainforest's valley in
# bends with a deep pool, over the lower escarpment in a second fall and on south through
# the mangroves into the lagoon. Smoothed (Chaikin) so it meanders, never runs straight.
RIVER = [(540, 176), (500, 196), (466, 206), (432, 202), (404, 192), (378, 186), (362, 190), (358, 200), (357, 214),
         (356, 232), (346, 256), (322, 282), (290, 300), (250, 306), (214, 322), (186, 352), (168, 388), (150, 420),
         (140, 452), (146, 490), (136, 526), (118, 560), (104, 586), (100, 600), (99, 614), (98, 640), (106, 670),
         (100, 704), (78, 730), (64, 762), (72, 800), (82, 832), (66, 866), (48, 890), (38, 914)]
# where the river goes over an escarpment (x, the rim's row), and the pools it has dug:
# below each fall, and one deep bend in the rainforest (x, y, rx, ry)
FALLS = [(358, 197), (100, 605)]
POOLS = [(356, 238, 14, 9), (98, 640, 13, 9), (146, 456, 10, 8)]
POOL = (540, 176, 42, 30)  # the falls' pool (centre, radii), under the volcano's flank
FALLS_X = 540
# small islands off the coast, scenery, never walked: (x, y, rx, ry, kind) where kind is
# 'green' (wooded on top), 'rock' or 'stack' (a tall sea stack off the cove's arm)
ISLETS = [(574, 1128, 10, 6, 'stack'), (420, 1122, 16, 9, 'green'), (520, 1140, 7, 4, 'rock'),
          (296, 1138, 9, 5, 'rock'), (20, 26, 10, 6, 'rock')]
# the cove's black beach, and its basalt arm (blocked jumble)
BEACH = (330, 530)
ARM = [(540, 1010), (600, 1000), (624, 1040), (612, 1090), (580, 1112), (530, 1104), (516, 1068), (522, 1036)]

# The trails, in island px, smoothed and drawn once, so each runs on unbroken across the
# borders. They take the gentle line: round the river's bends, up each escarpment only at
# a stair, over the river only on a footbridge (found where a trail meets the water).
TRAILS = [
    # the pier up the dry shore lane beside the river, the stair up the lower escarpment,
    # through the rainforest and over the river, the stair up the notch's west side, and
    # across the upland north of the river, over it, and down round the east to the cove
    [(112, 950), (110, 904), (124, 862), (146, 816), (166, 770), (180, 720), (186, 660), (186, 630), (186, 596),
     (190, 560), (196, 500), (204, 440), (214, 390), (226, 340), (230, 312), (240, 286), (262, 258), (284, 238),
     (284, 200), (290, 186), (306, 170), (336, 158), (370, 156), (400, 164), (430, 176), (452, 190), (452, 224),
     (446, 270), (458, 320), (484, 372), (480, 430), (490, 490), (516, 534), (516, 572), (516, 640), (516, 690),
     (520, 740), (506, 800), (488, 852), (476, 900), (470, 950)],
    # the landing's shore path round the headland to the cove
    [(146, 816), (200, 822), (248, 850), (280, 890), (304, 932), (340, 950), (380, 946), (424, 932), (466, 920)],
    # the spur to the pool's edge
    [(430, 176), (466, 166), (494, 166)],
]
TRAIL_W = 9.5
# the stairs: (west x, the rim's row, width); each crosses one escarpment where a trail does
STAIRS = [(172, 612, 28), (270, 214, 28), (502, 550, 28), (502, 668, 28)]


def chaikin(pts, n: int = 3):
    """Corner-cutting: a polyline's corners rounded off, its ends kept."""
    pts = list(pts)
    for _ in range(n):
        out = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            out += [(x0 * .75 + x1 * .25, y0 * .75 + y1 * .25), (x0 * .25 + x1 * .75, y0 * .25 + y1 * .75)]
        out.append(pts[-1])
        pts = out
    return pts


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
    """The island's ground, drawn once: `cv` (IW x IH), `over` (the stairs and footbridges,
    laid over the trails once each zone has painted its share), and the masks the zones
    cut: what is blocked, what is water, the trails, and the tier of every pixel."""

    def __init__(self):
        self.cv = Canvas(IW, IH)
        self.over = Canvas(IW, IH)
        self.blocked = bytearray(N)
        self.water = bytearray(N)
        self.trail = set()
        self.shut = set()  # cheek walls and rails
        self.open = set()  # stair treads and footbridge decks: walkable over a cliff or water
        self.T = bytearray(N)
        self.face = {}
        self.stairs = []  # (x0, y0, w, h) of each stair with its landings
        self.bridges = []  # (x0, y0, w, h, vertical)


def _put(px, x, y, c):
    px[x, y] = _RGBA[c] if c in _RGBA else _RGBA.setdefault(c, (*_rgb(c), 255))


_RGBA: dict = {}


def _river() -> bytearray:
    """The river's water: a band along the smoothed line, narrow at the spring and
    widening toward the mouth, its width breathing with the current; and its pools."""
    line = chaikin(RIVER, 3)
    total = sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(line, line[1:]))
    m = bytearray(N)
    s = 0.0
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        for k in range(int(L) + 1):
            t = k / max(1, L)
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = 4.6 + 3.2 * (s + k) / total + (smooth_noise(s + k, 0, 26, 1203) - 0.5) * 2.2
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for x in range(int(cx - r) - 1, int(cx + r) + 2):
                    if 0 <= x < IW and 0 <= y < IH and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                        m[y * IW + x] = 1
        s += L
    for k, (cx, cy, rx, ry) in enumerate(POOLS):
        for y in range(cy - ry - 3, cy + ry + 4):
            for x in range(cx - rx - 3, cx + rx + 4):
                if math.hypot((x - cx) / rx, (y - cy) / ry) < 1 - (smooth_noise(x, y, 6, 1207 + k) - 0.5) * 0.35:
                    m[y * IW + x] = 1
    return m


def _flatten(T: bytearray, xa: int, xb: int, rim: int):
    """A straight rim across columns xa..xb at `rim` (where a stair or a fall crosses)."""
    for x in range(xa, xb):
        up, down = T[(rim - 16) * IW + x], T[(rim + 16) * IW + x]
        for y in range(rim - 15, rim + 16):
            T[y * IW + x] = up if y < rim else down


def _tiers(land: bytearray, fresh: bytearray) -> bytearray:
    hi = _fill(_wobble(HIGH, 4, 1330))
    lo = _fill(_wobble(LOW, 4, 1331))
    T = bytearray(N)
    for i in range(N):
        T[i] = 2 if hi[i] else 1 if lo[i] else 0
    for (x0, rim, w) in STAIRS:
        _flatten(T, x0 - 8, x0 + w + 8, rim)
    for (fx, rim) in FALLS:
        _flatten(T, fx - 16, fx + 16, rim)
    for i in range(N):
        if not (land[i] or fresh[i]):
            T[i] = 0  # the sea
    return T


def _faces(T: bytearray, land: bytearray, fresh: bytearray) -> dict:
    """Where the ground steps down to the south, the face of the step hangs below the
    upper tier's edge, FACE px a step (the three-quarter view). (x, y) -> (row in the
    face, its height, 'rock' or 'falls'). A face over the sea is kept only where the
    coast runs roughly east-west, so a wobbling coast gets no slivers of cliff."""
    face = {}
    for gx in range(IW):
        for gy in range(1, IH):
            a, b = T[(gy - 1) * IW + gx], T[gy * IW + gx]
            if a <= b:
                continue
            up = (gy - 1) * IW + gx
            if not (land[up] or fresh[up]):
                continue
            sea_below = not (land[gy * IW + gx] or fresh[gy * IW + gx])
            if sea_below:
                ok = all(0 <= gx + d < IW and land[(gy - 1) * IW + gx + d] and
                         not land[min(IH - 1, gy + 4) * IW + gx + d] for d in (-3, 3))
                if not ok:
                    continue
            fh = FACE * (a - b)
            kind = 'falls' if fresh[up] else 'rock'
            for r in range(fh):
                y = gy + r
                if y >= IH or T[y * IW + gx] > b:
                    break
                face[(gx, y)] = (r, fh, kind)
    return face


@functools.lru_cache(maxsize=1)
def island() -> Island:
    I = Island()
    cv = I.cv
    px = cv.img.load()
    land = _fill(_wobble(COAST, 9, 1201))
    lagoon_zone = _fill(_wobble(REEF, 4, 1202, closed=False) + [(360, 960), (200, 780), (22, 780)])
    fresh = _river()
    pcx, pcy, prx, pry = POOL
    for y in range(int(pcy - pry) - 2, int(pcy + pry) + 3):
        for x in range(int(pcx - prx) - 2, int(pcx + prx) + 3):
            if math.hypot((x - pcx) / prx, (y - pcy) / pry) < 1 - (smooth_noise(x - W, y, 10, 955) - 0.5) * 0.3:
                fresh[y * IW + x] = 1
    pool = bytearray(N)
    for y in range(int(pcy - pry) - 2, int(pcy + pry) + 3):
        for x in range(int(pcx - prx) - 2, int(pcx + prx) + 3):
            if math.hypot((x - pcx) / prx, (y - pcy) / pry) < 1 - (smooth_noise(x - W, y, 10, 955) - 0.5) * 0.3:
                pool[y * IW + x] = 1
    islet = bytearray(N)
    for k, (cx, cy, rx, ry, _kind) in enumerate(ISLETS):
        for y in range(cy - ry - 2, cy + ry + 3):
            for x in range(cx - rx - 2, cx + rx + 3):
                if 0 <= x < IW and 0 <= y < IH and \
                        math.hypot((x - cx) / rx, (y - cy) / ry) < 1 - (smooth_noise(x, y, 5, 1210 + k) - 0.5) * 0.35:
                    islet[y * IW + x] = 1
    for i in range(N):
        if fresh[i]:
            land[i] = 0
    arm = _fill(_wobble(ARM, 5, 1209))
    for i in range(N):
        arm[i] = arm[i] and land[i]
    I.T = T = _tiers(land, fresh)
    I.face = face = _faces(T, land, fresh)
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
            if fresh[i]:
                pass
            elif lagoon_zone[i] and not reef[i]:
                lag[i] = 1
            else:
                sea[i] = 1
    d_sea = _dist(sea, 44)
    d_lag = _dist(lag, 20)
    d_fresh = _dist(fresh, 90)
    foot = {gx: flank_top(gx) for gx in range(IW)}

    # ---- the ground: the forest in the north-west and down the river's valley, turf on
    # the upland and the low ground, sand at the lagoon, black sand in the cove
    S = MATERIALS['sand']
    for gy in range(IH):
        row = gy * IW
        for gx in range(IW):
            i = row + gx
            if not land[i]:
                continue
            f = 0.9 * min((300 - gx) / 110, (600 - gy) / 100)
            if gy < 800:
                f = max(f, 0.9 * (1 - d_fresh[i] / 46) - max(0, gy - 660) / 140)
            if gx > 300:  # the forest round the volcano's foot, thinning out down the slope
                t = (gy - foot[gx]) / 70
                g = 0.8 * (1 - (t if t < 1 else 1 + (t - 1) * 3))
                f = max(f, g * _smoothstep((gx - 300) / 90) if g > 0 else g)
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
            dl, ds = d_lag[i], d_sea[i]
            sand_w = 7 + int(smooth_noise(gx, gy, 18, 1213) * 9)
            beach_w = 0
            if BEACH[0] <= gx <= BEACH[1] and gy > 900:
                beach_w = int(10 + 26 * math.sin(math.pi * (gx - BEACH[0]) / (BEACH[1] - BEACH[0])) +
                              (smooth_noise(gx, gy, 14, 1214) - 0.5) * 14 + (smooth_noise(gx, gy, 5, 1216) - 0.5) * 5)
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
                elif beach_w - ds < 3 and (gx + gy) % 2:
                    c = TROPIC[1]  # where the turf gives out to the sand
            elif ds <= 2 + int(smooth_noise(gx, gy, 11, 1245) * 4) and dl > 8 and not (150 <= gx <= 214 and gy < 110):
                # worn wet basalt along every exposed shore
                c = BASALT_R[1] if ds <= 1 else BASALT_R[3] if smooth_noise(gx, gy, 4, 1246) > 0.6 else BASALT_R[2]
                I.blocked[i] = 1
            elif d_fresh[i] <= 2:
                c = FLOOR[1] if d_fresh[i] == 1 else FLOOR[2]  # the damp bank
            _put(px, gx, gy, c)

    # ---- the water
    for gy in range(IH):
        row = gy * IW
        for gx in range(IW):
            i = row + gx
            if not I.water[i]:
                continue
            d = d_land[i]
            if fresh[i]:
                deep = 4 if not pool[i] else 6
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

    # ---- rocks along every exposed shore (not on a cliff's top: a sea cliff's face is
    # drawn below it, with its own boulders in the surf)
    taken = {}
    for gy in range(IH):
        for gx in range(IW):
            i = gy * IW + gx
            if not land[i] or d_sea[i] != 1 or d_lag[i] <= 8 or arm[i]:
                continue
            if BEACH[0] + 14 <= gx <= BEACH[1] - 14 and gy > 900:
                continue  # the beach itself
            if 150 <= gx <= 214 and gy < 110:
                continue  # the rainforest's small sandy bay
            if any((gx, gy + d) in face for d in range(1, 4)):
                continue
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
    mouth = chaikin(RIVER, 2)[-12:]
    for gy in range(780, 990, 7):
        for gx in range(10, 150, 8):
            x = gx + int(noise2(gx, gy, 1250) * 6)
            y = gy + int(noise2(gx, gy, 1251) * 6)
            i = y * IW + x
            if not lag[i] or not 2 <= d_land[i] <= 11 or _seg_dist(x, y, mouth) < 13:
                continue
            if noise2(gx, gy, 1252) > 0.8:
                continue
            _mangrove(cv, I, x, y, 1253 + gx * 7 + gy)
    for k, (cx, cy, rx, ry, kind) in enumerate(ISLETS):
        _islet(cv, I, islet, cx, cy, rx, ry, kind, 1260 + k)
    _arm(cv, I, arm)

    # ---- the Headwaters: the old volcano's flank, the falls and their pool; the heights
    _flank(cv, I, land)
    _falls(cv, I, pool)
    _trails(I, land, fresh)
    _heights(cv, I, land, fresh, d_fresh)
    _ground_detail(cv, I, land, d_fresh)
    _crossings(cv, I, fresh)

    for i in range(N):
        if (I.water[i] or islet[i]) and (i % IW, i // IW) not in I.open:
            I.blocked[i] = 1
    for (x, y) in I.trail:
        if not I.water[y * IW + x]:
            I.blocked[y * IW + x] = 0
    for (x, y) in I.open:
        I.blocked[y * IW + x] = 0
    for (x, y) in I.shut:
        I.blocked[y * IW + x] = 1
    return I


def _trails(I: Island, land: bytearray, fresh: bytearray):
    """The trails' pixels: on land, never on water (a footbridge carries them over) or
    on a cliff's face (a stair carries them up)."""
    stair_cols = {(x, y) for (x0, rim, w) in STAIRS for x in range(x0, x0 + w) for y in range(rim - 6, rim + 2 * FACE + 6)}
    for line in TRAILS:
        m = _thick(chaikin(line, 3), TRAIL_W, 1320)
        for i in range(N):
            if m[i] and land[i]:
                p = (i % IW, i // IW)
                if p in I.face and p not in stair_cols:
                    continue
                I.trail.add(p)


def _crossings(cv: Canvas, I: Island, fresh: bytearray):
    """Footbridges where a trail meets the river: a plank deck square to the trail, its
    ends on the dry trail either side, its shadow on the water."""
    for line in TRAILS:
        pts = chaikin(line, 3)
        samples = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = max(1, int(math.hypot(x1 - x0, y1 - y0)))
            samples += [(x0 + (x1 - x0) * k / L, y0 + (y1 - y0) * k / L) for k in range(L)]
        wet = [fresh[int(y) * IW + int(x)] == 1 for (x, y) in samples]
        k = 0
        while k < len(samples):
            if not wet[k]:
                k += 1
                continue
            j = k
            while j < len(samples) and wet[j]:
                j += 1
            (sx, sy), (ex, ey) = samples[max(0, k - 1)], samples[min(len(samples) - 1, j)]
            vertical = abs(ey - sy) >= abs(ex - sx)
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            if vertical:
                x0, y0, w, h = int(mx) - 13, int(min(sy, ey)) - 7, 26, int(abs(ey - sy)) + 14
            else:
                x0, y0, w, h = int(min(sx, ex)) - 7, int(my) - 12, int(abs(ex - sx)) + 14, 24
            I.bridges.append((x0, y0, w, h, vertical))
            deck, rails = plank_bridge(I.over, x0, y0, w, h, vertical=vertical)
            shade = ([(x0 + w + d, y) for y in range(y0, y0 + h) for d in (0, 1)] if vertical else
                     [(x, y0 + h + d) for x in range(x0, x0 + w) for d in (0, 1)])
            for (x, y) in shade:
                style.darken(cv, x, y)
            I.open |= deck
            I.shut |= rails
            k = j


def _islet(cv: Canvas, I: Island, mask: bytearray, cx, cy, rx, ry, kind: str, seed: int):
    """A small island off the coast, in the three-quarter view: its top lit from the upper
    left (moss and a few palms on the green one, bare rock and gull-white on the others),
    a basalt face below it, dark and wet at the waterline, and the surf round its foot."""
    O = BASALT_R
    base = {(i % IW, i // IW) for i in range(max(0, (cy - ry - 3) * IW), min(N, (cy + ry + 4) * IW)) if mask[i]}
    fh = {'rock': 4, 'green': 6, 'stack': 22}[kind]
    shape = base if kind != 'stack' else {(x, y) for (x, y) in base if abs(x - cx) < rx * 0.75}
    top = {(x, y - fh) for (x, y) in shape}  # its top, raised by the height of its face
    tb = {}
    for (x, y) in top:
        tb[x] = max(tb.get(x, -1), y)
    face = {(x, yb + d) for x, yb in tb.items() for d in range(1, fh + 1)}
    cols = {x: yb + fh for x, yb in tb.items()}
    face |= {(x, y) for (x, y) in base if (x, y) not in top and (x, y) not in face}  # the wet skirt
    for (x, y) in list(face):
        cols[x] = max(cols.get(x, y), y)
    for (x, y) in face:
        bottom = cols.get(x, y)
        r = bottom - y
        k = (x + int(noise2(x // 3, 0, seed) * 3)) % 4
        c = O[1] if k == 0 else O[2] if x < cx + rx * 0.3 else O[1]
        if x - cx < -rx * 0.5 and k:
            c = O[3]  # the face's lit west side
        if r <= 1:
            c = '#3E4A52' if (x + y) % 2 else O[0]  # wet rock with a sheen at the waterline
        elif r == 2:
            c = O[0]
        cv.set(x, y, c)
    for (x, y) in top:
        edge = (x, y - 1) not in top or (x - 1, y) not in top
        n = smooth_noise(x, y, 4, seed)
        if kind == 'green':
            c = TROPIC[4] if edge and x < cx else TROPIC[3] if n > 0.5 else TROPIC[2]
        else:  # weathered grey rock, salt-crusted, with tufts of sea grass in its hollows
            c = '#8E8A96' if edge and x < cx + 2 else '#6E6878' if n > 0.45 else O[4]
            if n < 0.25:
                c = TROPIC[2] if (x + y) % 2 else TROPIC[3]
            if noise2(x, y, seed + 1) > 0.86:
                c = '#E6E8E2'  # where the gulls sit
        if (x, y + 1) not in top and (x, y + 1) in face:
            c = TROPIC[1] if kind == 'green' else O[2]
        cv.set(x, y, c)
    if kind == 'green':
        tmp = Canvas(2 * rx + 8, 2 * ry + 10)
        shape = style.leafy(tmp, rx + 4, ry + 1, rx * 0.6, ry * 0.65, TROPIC, r=1.8, seed=seed)
        for (a, b) in shape:
            cv.set(cx - rx - 4 + a, cy - ry - 4 - fh + b, tmp.get(a, b))
    # the surf round its foot
    ring = set()
    for (x, y) in base | face:
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (1, 1), (-1, 1), (0, 2)):
            q = (x + dx, y + dy)
            if q not in base and q not in face and q not in top and 0 <= q[0] < IW and 0 <= q[1] < IH:
                ring.add(q)
    for (x, y) in ring:
        cv.set(x, y, FOAM if noise2(x, y, seed + 2) > 0.3 else '#DDEBEE')
    for (x, y) in base | face | top:
        if 0 <= x < IW and 0 <= y < IH:
            I.blocked[y * IW + x] = 1


def _arm(cv: Canvas, I: Island, arm: bytearray):
    """The cove's basalt arm: an old lava flow the sea has not worn down, a jumble of
    great blocks, mossed on top, hooking round the east of the black-sand pocket."""
    pts = {(i % IW, i // IW) for i in range(N) if arm[i]}
    if not pts:
        return
    for (x, y) in pts:  # the old flow's ropy crust between the blocks
        n = smooth_noise(x, y, 4, 1269)
        cv.set(x, y, BASALT_R[3] if n > 0.62 else BASALT_R[2] if n > 0.3 else BASALT_R[1])
        I.blocked[y * IW + x] = 1
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    blocks = []
    for k in range(60):
        bx = min(xs) + int(noise2(k, 0, 1270) * (max(xs) - min(xs)))
        by = min(ys) + int(noise2(k, 1, 1270) * (max(ys) - min(ys)))
        if (bx, by) in pts:
            blocks.append((by, bx, 5 + noise2(k, 2, 1270) * 7, 4 + noise2(k, 3, 1270) * 4, k))
    for (by, bx, rx, ry, k) in sorted(blocks):  # back to front
        q = {(x, y) for (x, y) in oval(bx, by, rx, ry) if (x, y) in pts}
        if len(q) > 8:
            style.facet_stone(cv, q, BASALT_R, moss=TROPIC if noise2(k, 4, 1270) > 0.55 else None,
                              seed=1271 + k, outline=None)
    for (x, y) in pts:  # the sea's wet line at its foot
        if (x, y + 1) not in pts and I.water[min(N - 1, (y + 1) * IW + x)]:
            cv.set(x, y, '#3E4A52' if x % 2 else BASALT_R[0])


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


def _columns(seed: int):
    """Columnar basalt: for each x, (the column's index, the position in it, its width)."""
    out = []
    k = 0
    while len(out) < IW:
        w = 5 + int(noise2(k, 0, seed) * 3)
        out += [(k, p, w) for p in range(w)]
        k += 1
    return out[:IW]


def _heights(cv: Canvas, I: Island, land: bytearray, fresh: bytearray, d_fresh: bytearray):
    """The island's three heights. Where the ground steps down to the south the step's
    face hangs below the edge: columnar basalt lit on each column's west edge, the turf's
    lip and overhang along the top, ferns and moss hanging, the foot dark and its shadow
    on the ground below; over the sea the face stands in the surf. Where the river goes
    over, the face is a white curtain into its plunge pool. Where the ground steps down to
    the west or east the face is seen edge on (lit when it faces west), and where it steps
    down to the north only the rim shows. Then the stairs."""
    px = cv.img.load()
    T, face = I.T, I.face
    O = BASALT_R
    COLS = _columns(1340)
    is_land = lambda i: land[i] or fresh[i]  # noqa: E731
    falls_cols = {gx for (gx, gy), (_r, _fh, kind) in face.items() if kind == 'falls'}
    for (gx, gy), (r, fh, kind) in face.items():
        i = gy * IW + gx
        I.blocked[i] = 1
        if kind == 'falls':
            left = face.get((gx - 1, gy), (0, 0, ''))[2] != 'falls'
            right = face.get((gx + 1, gy), (0, 0, ''))[2] != 'falls'
            if r == 0:
                c = LAGOON[3]  # the water's smooth lip as it slides over
            elif r >= fh - 3:
                c = FOAM if (gx + r) % 2 or r == fh - 1 else '#DDEBEE'  # where it lands, boiling
            elif left:
                c = LAGOON[4]
            elif right:
                c = LAGOON[2]
            else:
                c = FOAM if (gx * 7 + r // 2 + int(noise2(gx, 0, 1345) * 5)) % 5 < 2 else \
                    LAGOON[4] if gx % 3 else LAGOON[3]
            _put(px, gx, gy, c)
            I.water[i] = 1
            continue
        I.water[i] = 0
        k, p, w = COLS[gx]
        brk = 7 + int(noise2(k, 1, 1341) * 6)  # rows between cross-joints in this column
        ph = int(noise2(k, 2, 1341) * brk)
        bottom = fh - 2 - int(noise2(k, 3, 1341) * 3)  # the columns end unevenly at the foot
        sea_foot = not is_land(min(N - 1, (gy - r + fh) * IW + gx))
        if r == 0:
            c = TROPIC[4] if (gx // 2) % 3 else TROPIC[3]  # the turf's lip in the light
        elif r == 1:
            c = TROPIC[1] if noise2(gx, 7, 1342) > 0.45 else O[0]  # its overhang
        elif r >= fh - 1:
            c = '#3E4A52' if sea_foot and gx % 2 else O[0]
        elif r > bottom:
            c = O[1] if (gx + r) % 2 else O[0]  # broken ends of the columns
        elif p == 0:
            c = O[0]  # the joint between two columns
        elif (r + ph) % brk == 0:
            c = O[1]  # a cross-joint
        elif (r + ph) % brk == 1:
            c = O[4] if p == 1 else O[3]  # the lit top of the column below it
        elif p == 1:
            c = O[3]  # the column's lit west edge
        elif p == w - 1:
            c = O[1]
        else:
            c = O[2]
        if 2 <= r < 2 + int(smooth_noise(gx, 0, 6, 1343) * 8) and smooth_noise(gx, 1, 9, 1344) > 0.56:
            c = TROPIC[3] if p == 1 else TROPIC[2] if p % 2 else TROPIC[1]  # ferns hanging over
        if any(abs(gx - f) <= 2 for f in falls_cols if abs(gx - f) <= 2) and r > 1:
            c = O[1] if c in (O[2], O[3], O[4]) else c  # rock wet with the fall's spray
        if sea_foot and r > fh - 4 and noise2(gx, r, 1346) > 0.6:
            c = '#3E4A52'
        _put(px, gx, gy, c)
    # at each face's foot: its shadow on the ground, or the surf where it stands in the sea
    for (gx, gy), (r, fh, kind) in face.items():
        if r != fh - 1 or (gx, gy + 1) in face:
            continue
        for d in (1, 2):
            if gy + d >= IH:
                break
            j = (gy + d) * IW + gx
            if kind == 'falls' or fresh[j]:
                if fresh[j]:
                    _put(px, gx, gy + d, FOAM if (gx + d) % 2 else LAGOON[4])
            elif land[j]:
                style.darken(cv, gx, gy + d)
            else:
                _put(px, gx, gy + d, FOAM if d == 1 or noise2(gx, gy, 1347) > 0.5 else '#DDEBEE')
    # the plunge pools boil white below each fall
    for (fx, rim) in FALLS:
        foot_y = rim + FACE
        for y in range(foot_y, foot_y + 12):
            for x in range(fx - 14, fx + 15):
                j = y * IW + x
                if fresh[j] and (x, y) not in face:
                    d = math.hypot(x - fx, (y - foot_y) * 1.6)
                    if noise2(x, y, 1348) * 12 > d - 1:
                        _put(px, x, y, FOAM if (x + y) % 2 else LAGOON[4])
    # boulders fallen into the surf below the sea cliffs
    for (gx, gy), (r, fh, kind) in face.items():
        if r == fh - 1 and kind == 'rock' and not is_land(min(N - 1, (gy + 2) * IW + gx)) \
                and noise2(gx // 7, gy // 7, 1349) > 0.55 and gx % 7 == 3:
            pts = {(x, y) for (x, y) in oval(gx, gy + 3, 3 + noise2(gx, 1, 1350) * 2.5, 2.4)
                   if 0 <= x < IW and 0 <= y < IH and (x, y) not in face}
            style.facet_stone(cv, pts, O, seed=1351 + gx, outline=None)
            for (x, y) in pts:
                I.blocked[y * IW + x] = 1
                I.water[y * IW + x] = 0
    # the faces seen edge on, where the ground steps down to the west or the east
    rims = []  # (where a bush grows on the rim's top)
    for gy in range(IH):
        for gx in range(1, IW):
            a, b = T[gy * IW + gx - 1], T[gy * IW + gx]
            if a == b or not is_land(gy * IW + gx - 1) or not is_land(gy * IW + gx):
                continue
            west_low = a < b
            band = 4 + 3 * abs(a - b)
            hi_x = gx if west_low else gx - 1
            if (hi_x, gy) not in face and land[gy * IW + hi_x] and (hi_x, gy) not in I.trail:
                _put(px, hi_x, gy, TROPIC[4] if gy % 3 else TROPIC[3])  # the lit lip
                I.blocked[gy * IW + hi_x] = 1
            for e in range(band):
                x = gx - 1 - e if west_low else gx + e
                if not 0 <= x < IW or (x, gy) in face or not land[gy * IW + x]:
                    continue
                if e == band - 1:
                    c = O[0]  # where the face meets the ground below
                elif west_low:  # the face looks west, into the light
                    c = O[3] if e < 2 else O[2]
                else:
                    c = O[2] if e == 0 else O[1]
                if (gy + int(noise2(gx, 0, 1352) * 5)) % 6 == 0:
                    c = O[1] if west_low else O[0]  # the courses, edge on
                _put(px, x, gy, c)
                I.blocked[gy * IW + x] = 1
            if noise2(gx, gy // 9, 1353) < 0.1 and gy % 9 == 0:
                rims.append((hi_x + (3 if west_low else -3), gy))
            sh = gx + band if not west_low else None  # an east-facing face shades the ground beside it
            if sh is not None and 0 <= sh < IW and land[gy * IW + sh] and (sh, gy) not in face:
                style.darken(cv, sh, gy)
    # where the ground steps down to the north, only the rim shows from here
    for gx in range(IW):
        for gy in range(1, IH - 1):
            a, b = T[(gy - 1) * IW + gx], T[gy * IW + gx]
            if a >= b or not land[(gy - 1) * IW + gx] or not land[gy * IW + gx] or (gx, gy) in face:
                continue
            # the lower ground's last row in the rim's shadow, the rock of the rim, its
            # lit edge and the turf's lip
            style.darken(cv, gx, gy - 2)
            _put(px, gx, gy - 1, O[0] if gx % 5 else O[1])
            _put(px, gx, gy, O[2] if (gx // 3) % 2 else O[1])
            _put(px, gx, gy + 1, O[3] if (gx // 2) % 3 else O[4])
            _put(px, gx, gy + 2, TROPIC[4] if gx % 3 else TROPIC[3])
            for d in (-1, 0, 1, 2):
                I.blocked[(gy + d) * IW + gx] = 1
            if gx % 11 == 0 and noise2(gx, gy, 1354) < 0.45:
                rims.append((gx, gy + 4))
    # bushes leaning over each lip, scree fallen at the foot (never on a trail)
    trail = I.trail
    near = {(x, y) for (x0, rim, w) in STAIRS for y in range(rim - 16, rim + 2 * FACE + 12)
            for x in range(x0 - 10, x0 + w + 10)}
    lips, feet = [], []
    for (gx, gy), (r, fh, kind) in face.items():
        if r == 0 and kind == 'rock' and smooth_noise(gx, gy, 26, 1315) > 0.48 and noise2(gx, gy // 8, 1314) < 0.2:
            lips.append((gx, gy - 1))
            feet.append((gx + int(noise2(gx, gy, 1316) * 6) - 3, gy + fh + 3))
    lips += rims
    for k, (gx, gy) in enumerate(lips):
        i = gy * IW + gx
        if not (0 < gx < IW - 1 and 0 < gy < IH - 1) or not land[i] or (gx, gy) in near:
            continue
        if noise2(gx, gy, 1319) < 0.25 or d_fresh[i] < 10:
            continue
        rx, ry = 4 + noise2(gx, gy, 1321) * 4, 3 + noise2(gx, gy, 1322) * 2
        tmp = Canvas(24, 18)
        shape = style.leafy(tmp, 12, 9, rx, ry, TROPIC, r=1.7, seed=1323 + k)
        if any((gx - 12 + a, gy - 9 + b) in trail for (a, b) in shape):
            continue
        for (a, b) in shape:
            x, y = gx - 12 + a, gy - 9 + b
            if 0 <= x < IW and 0 <= y < IH and (land[y * IW + x] or (x, y) in face):
                cv.set(x, y, tmp.get(a, b))
                I.blocked[y * IW + x] = 1
    for k, (gx, gy) in enumerate(feet):
        if not (2 < gx < IW - 3 and 2 < gy < IH - 3) or (gx, gy) in near:
            continue
        i = gy * IW + gx
        if not land[i] or d_fresh[i] < 9 or (gx, gy) in face or noise2(gx, gy, 1324) < 0.35:
            continue
        rr = 2 + noise2(gx, gy, 1325) * 2.5
        pts = {(x, y) for (x, y) in oval(gx, gy, rr + 1, rr) if land[y * IW + x] and (x, y) not in face}
        if len(pts) > 4 and not pts & trail:
            style.facet_stone(cv, pts, O, seed=1326 + k, outline=None)
            for (x, y) in pts:
                I.blocked[y * IW + x] = 1
    _stairs(cv, I)


def _stairs(cv: Canvas, I: Island):
    """A stair up each escarpment where a trail climbs it, cut into the face: basalt
    treads with lit noses and dark risers, worn pale in the middle and mossed in the
    corners, between cheek walls whose caps catch the light and whose front ends show at
    the foot; a flagged landing at the top and the bottom, and the right wall's shadow."""
    T = I.T
    S = STONE
    ov = I.over
    for (x0, rim, w) in STAIRS:
        cx = x0 + w // 2
        drop = max(1, T[(rim - 8) * IW + cx] - T[(rim + 8) * IW + cx])
        fh = FACE * drop
        top, bottom = rim - 6, rim + fh + 5
        w0, w1 = rim - 2, rim + fh + 2  # the walls' rows
        I.stairs.append((x0, top, w, bottom - top))
        for y in range(top, bottom):
            for x in range(x0, x0 + w):
                a, b = x - x0, x0 + w - 1 - x
                if a < 3 or b < 3:
                    if not w0 <= y <= w1:
                        continue
                    I.shut.add((x, y))
                    if y >= w1 - 3:  # the wall's front end, facing us
                        e = a if a < 3 else 2 - b
                        c = S[0] if y == w1 else S[3] if e == 0 else S[2]
                    elif y == w0:
                        c = S[4]
                    elif a < 3:
                        c = (S[1], S[4], S[2])[a]
                    else:
                        c = (S[1], S[3], S[3])[b]
                    if w0 < y < w1 - 3 and (y - w0) % 5 == 0:
                        c = S[2]  # the joint between two copings
                    if w0 < y < w1 - 3 and noise2(x * 5 + y, y // 3, 1360) > 0.88:
                        c = TROPIC[2]  # moss in the joints
                    ov.set(x, y, c)
                    continue
                I.open.add((x, y))
                ry = y - rim
                if 0 <= ry < fh:
                    k, step = ry % 3, ry // 3
                    if k == 0:
                        c = S[4] if x < x0 + 9 else S[3]  # the tread's nose, catching the light
                    elif k == 1:
                        c = S[2]
                        if abs(x - cx) < 5 and noise2(x, step, 1361) > 0.35:
                            c = S[3]  # worn pale where feet go
                        if (x + step * 4) % 9 == 0:
                            c = S[1]  # the joint between two slabs
                    else:
                        c = S[0]  # the riser in shadow
                    if (a == 3 or b == 3) and k and noise2(x * 3 + step, step, 1362) > 0.6:
                        c = TROPIC[1] if k == 2 else TROPIC[2]  # moss in the corner
                    elif a == 3 and k == 1:
                        c = S[1]  # the left wall's shadow on the step
                else:
                    c = S[2] if (x + (y // 5) * 3) % 8 and y % 5 else S[1]  # the flagged landing
                    if noise2(x, y, 1363) > 0.93:
                        c = S[3]
                ov.set(x, y, c)
        for y in range(w0, w1 + 1):  # the right wall's shadow on the face and the ground
            for d in (0, 1):
                style.darken(cv, x0 + w + d, y)


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
    for (cx, cy, rad) in ((POOL[0], POOL[1] + 10, 70), (FALLS[0][0], FALLS[0][1] + 40, 34),
                          (FALLS[1][0], FALLS[1][1] + 40, 30)):
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


def paint(zone: str):
    """Cut this zone from the island, lay its share of the trails over it, then the
    stairs and footbridges. Returns (canvas, water, blocked, deck, ox, oy)."""
    I = island()
    cv, water, blocked, ox, oy = cut(zone)
    mask = {(x - ox, y - oy) for (x, y) in I.trail if ox - 2 <= x < ox + W + 2 and oy - 2 <= y < oy + H + 2}
    paint_road(cv, mask)
    cv.img.alpha_composite(I.over.img.crop((ox, oy, ox + W, oy + H)))
    deck = {(x - ox, y - oy) for (x, y) in I.open if ox <= x < ox + W and oy <= y < oy + H}
    return cv, water, blocked, deck, ox, oy


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


# Where the companion and the residents stop, per zone (zone px). The entries named after a
# neighbour stand on the trail near the shared edge; the others at the place's node.
STANDS = {
    'landing': {'pier': (112, 440), 'rainforest': (188, 10), 'cove': (314, 366), 'boathouse': (184, 352)},
    'rainforest': {'landing': (188, 568), 'bridge': (226, 348), 'headwaters': (314, 167), 'notch': (276, 252)},
    'headwaters': {'rainforest': (6, 162), 'pool': (172, 166), 'cove': (188, 520)},
    'cove': {'headwaters': (196, 26), 'landing': (6, 367), 'beach': (150, 390)},
}

# The props each place is built round, by hand (key, the foot's centre in island px).
# Everything else grows in groves (GROVES) or along the edges (EDGES), placed by rule.
LANDMARKS = [
    # the landing: the boathouse above the lagoon, the ferry at the pier, a canoe hauled
    # up on the sand, a heron fishing the river's mouth, a banana patch behind the boathouse
    ('boathouse', 'boathouse', 184, 918), ('ferry', 'island_ferry', 174, 1049), ('canoe', 'canoe', 222, 974),
    ('heron', 'heron', 60, 905), ('banana-1', 'banana', 236, 906), ('banana-2', 'banana', 234, 892),
    # the rainforest: a fallen giant across the floor by the pool in the bend, its stump
    ('log', 'mossy_log', 106, 474),
    # the headwaters: a rain shelter by the pool, looking at the fall
    ('shelter', 'rain_shelter', 452, 140),
    # the cove: the turtle above the tide line, a canoe drawn up at the back of the beach
    ('turtle', 'sea_turtle', 428, 970), ('canoe-2', 'canoe', 500, 990),
]
# Groves (centre in island px, radius, what grows there): trees grow together, the giants
# in the wet valley and round the volcano's foot, palms and pandanus by the shore.
GROVES = [
    # the rainforest's giants in clumps either side of the valley, understory between
    ((70, 150), 40, [('jungle_tree', 2), ('tree_fern', 2), ('monstera', 2)]),
    ((172, 222), 28, [('jungle_tree', 1), ('tree_fern', 2)]),
    ((100, 300), 36, [('jungle_tree', 2), ('tree_fern', 1), ('monstera', 2)]),
    ((40, 236), 24, [('tree_fern', 2), ('monstera', 1)]),
    ((236, 430), 34, [('jungle_tree', 1), ('tree_fern', 2), ('fern', 2)]),
    ((60, 560), 30, [('jungle_tree', 1), ('tree_fern', 2), ('fern', 2)]),
    ((258, 520), 32, [('tree_fern', 2), ('banana', 1), ('monstera', 1)]),
    ((210, 120), 30, [('tree_fern', 2), ('bird_of_paradise', 1)]),
    # round the volcano's foot on the upland, and a few on it
    ((360, 110), 30, [('jungle_tree', 2), ('tree_fern', 1)]),
    ((590, 250), 24, [('tree_fern', 2), ('jungle_tree', 1)]),
    ((390, 300), 34, [('tree_fern', 2), ('hibiscus', 1), ('bird_of_paradise', 1)]),
    ((540, 270), 30, [('jungle_tree', 1), ('tree_fern', 2)]),
    ((410, 440), 36, [('jungle_tree', 2), ('hibiscus', 1), ('monstera', 1)]),
    ((560, 520), 26, [('bird_of_paradise', 2), ('hibiscus', 1)]),
    # the terrace above the cove
    ((420, 590), 30, [('pandanus', 2), ('hibiscus', 1), ('bird_of_paradise', 1)]),
    ((580, 620), 24, [('pandanus', 1), ('tree_fern', 1)]),
    # the low ground: palms on the landing's shore and the cove's back beach
    ((60, 760), 34, [('jungle_tree', 1), ('tree_fern', 2), ('banana', 1)]),
    ((290, 700), 40, [('jungle_tree', 1), ('palm', 2), ('hibiscus', 1)]),
    ((390, 760), 40, [('palm', 2), ('pandanus', 1), ('bird_of_paradise', 1)]),
    ((570, 820), 30, [('palm', 2), ('pandanus', 1)]),
    ((250, 950), 30, [('palm', 2), ('pandanus', 1)]),
    ((70, 960), 20, [('palm', 1)]),
    ((360, 990), 26, [('palm', 2), ('pandanus', 1)]),
    ((560, 960), 26, [('palm', 1), ('pandanus', 2)]),
    ((190, 860), 30, [('palm', 1), ('hibiscus', 1), ('bush', 1)]),
]
# Small things along the edges of places: (key, how many, the ground kinds it grows on)
EDGES = [
    ('fern', 36, {'floor', 'turf'}), ('monstera', 14, {'floor'}), ('tree_fern', 8, {'floor'}), ('bird_of_paradise', 6, {'turf'}),
    ('hibiscus', 4, {'turf'}), ('bush', 4, {'turf'}), ('black_rock_small', 5, {'black'}),
    ('black_rock', 2, {'black'}), ('crab', 4, {'black', 'sand'}), ('driftwood', 4, {'black', 'sand'}),
]
WET_OK = {'heron', 'driftwood', 'crab'}  # (stand at the water's edge)
TRUNK = ('jungle_tree', 'palm', 'tree_fern', 'pandanus', 'banana')


@functools.lru_cache(maxsize=None)
def _shadow(key: str) -> frozenset:
    """The ground a prop's shadow covers, from its sprite's top-left (zones.build casts it)."""
    return frozenset(detail.silhouette_shadow(_sprites()[key], 0, 0))


def _foot(key: str, fx: int, fy: int):
    """The ground a prop stands on: a trunk's base, or a plant's or a rock's whole width."""
    sp = _sprites()[key]
    half = max(3, sp.w // 8) if key in TRUNK else max(3, sp.w * 7 // 20)
    return (fx - half, fy - 5, fx + half, fy + 1)


@functools.lru_cache(maxsize=1)
def _island_props() -> list:
    """Every prop on the island as (id, key, foot x, foot y) in island px. Each one is
    checked: its foot on open ground of one tier (never on a trail, a stair, water, a
    cliff's face or another prop's foot), clear of the stands and the residents' walks,
    and its top never covering a cliff face it does not stand in front of."""
    I = island()
    sm = _sprites()
    stands = [(x + LAYOUT['isles'][z][0] * W, y + LAYOUT['isles'][z][1] * H)
              for z, ss in STANDS.items() for (x, y) in ss.values()]
    walks = []
    for z, rs in _routes().items():
        if z in LAYOUT['isles']:
            c, r = LAYOUT['isles'][z]
            walks += [(a + c * W, b + r * H, cc + c * W, d + r * H) for (a, b, cc, d) in rs]
    near_trail = set()
    for (x, y) in I.trail | I.open | {(x, y) for (x0, y0, w, h) in I.stairs for y in range(y0, y0 + h)
                                       for x in range(x0, x0 + w)}:
        if x % 3 == 0 and y % 3 == 0:
            near_trail.add((x // 6, y // 6))
    feet = []
    out = []
    # what a crown must never hide: the falls and their pool, the plunge pools
    sight = {(x, y) for (x, y), (_r, _fh, kind) in I.face.items() if kind == 'falls'}
    sight |= {(x, y) for (cx, cy, rx, ry) in [POOL[:4]] + POOLS for x in range(cx - rx, cx + rx)
              for y in range(cy - ry, cy + ry)}
    sight |= {(FALLS_X + dx, y) for dx in range(-10, 11) for y in range(40, 160)}

    def clear(key, fx, fy, kinds, gap=12, landmark=False):
        sp = sm[key]
        x0, y0, x1, y1 = _foot(key, fx, fy)
        if x0 < 2 or x1 >= IW - 2 or y0 < 2 or y1 >= IH - 2:
            return False
        tiers = set()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                i = y * IW + x
                if I.blocked[i] and not (key in WET_OK and I.water[i]):
                    return False
                if (x, y) in I.face or (x, y) in I.open:
                    return False
                tiers.add(I.T[i])
        if len(tiers) > 1:
            return False
        if kinds and _kind(I.cv, fx, fy - 1) not in kinds:
            return False
        g = max(1, gap // 6)
        if not landmark and any((x // 6 + dx, y // 6 + dy) in near_trail for x in (x0, fx, x1) for y in (y0, y1)
               for dx in range(-g, g + 1) for dy in range(-g, g + 1)):
            return False
        for (sx, sy) in ([] if landmark else stands):
            if x0 - 16 < sx < x1 + 16 and fy - 24 < sy < fy + 14:
                return False
        for (a, b, c, d) in ([] if landmark else walks):
            if x0 - 10 < max(a, c) and x1 + 10 > min(a, c) and fy - 26 < max(b, d) and fy + 30 > min(b, d):
                return False
        box = (x0 - 3, y0 - 4, x1 + 3, y1 + 3)
        if any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1] for b in feet):
            return False
        # where a sprite rises over a zone's north border, nothing in the zone behind may
        # stand under it (zones.check_overhangs)
        bx0, by0 = fx - sp.w // 2, fy - sp.h
        zc, zr = fx // W, (fy - 2) // H
        for (ox0, oy0, ow, oh, oc, orow) in boxes:
            if oc != zc or abs(orow - zr) != 1:
                continue
            low_top = by0 if zr > orow else oy0
            if low_top >= max(zr, orow) * H:
                continue  # (the one in front does not rise over the border)
            if bx0 < ox0 + ow and bx0 + sp.w > ox0 and by0 < oy0 + oh and by0 + sp.h > oy0:
                return False
        # its shadow, thrown down and to the right, never falls across a trail (the trail
        # must read as one unbroken way)
        bx0, by0 = fx - sp.w // 2, fy - sp.h
        if bx0 < 2 or by0 < 2 or bx0 + sp.w > IW - 2:
            return False  # (nothing reaches past the island's picture)
        if any((bx0 + dx, by0 + dy) in I.trail or (bx0 + dx, by0 + dy) in I.open for (dx, dy) in _shadow(key)):
            return False
        # a big crown never hides a stair or a footbridge, and leaves the trail in sight
        if sp.h > 60:
            cx0, cx1, cy0, cy1 = fx - sp.w // 2, fx + sp.w // 2, fy - sp.h, fy - sp.h // 3
            cover = [(x, y) for x in range(cx0, cx1, 3) for y in range(cy0, cy1, 3)]
            if any((x, y) in I.open or (x, y) in sight for (x, y) in cover):
                return False
            if sum((x, y) in I.trail for (x, y) in cover) > len(cover) * 0.08:
                return False
        # a tall prop's crown may rise in front of a cliff face below which it stands,
        # but a prop standing on the top must not hang down over the face in front of it
        for y in range(fy + 1, fy + 4):
            for x in (x0, fx, x1):
                if (x, y) in I.face:
                    return False
        return True

    boxes = []

    def put(oid, key, fx, fy):
        sp = sm[key]
        boxes.append((fx - sp.w // 2, fy - sp.h, sp.w, sp.h, fx // W, (fy - 2) // H))
        feet.append(tuple(a + d for a, d in zip(_foot(key, fx, fy), (-3, -4, 3, 3))))
        out.append((oid, key, fx, fy))

    for (oid, key, fx, fy) in LANDMARKS:
        if key in ('island_ferry',):
            put(oid, key, fx, fy)  # (it floats; drawn at the pier)
            continue
        if not clear(key, fx, fy, None, landmark=True):
            near = min(((abs(dx) + abs(dy), fx + dx, fy + dy) for dx in range(-30, 31, 2) for dy in range(-30, 31, 2)
                        if clear(key, fx + dx, fy + dy, None, landmark=True)), default=None)
            raise AssertionError(f'isles: the landmark {oid} has no footing at ({fx}, {fy}); nearest: {near}')
        put(oid, key, fx, fy)
    kinds_of = {'jungle_tree': {'floor', 'turf'}, 'tree_fern': {'floor', 'turf'}, 'monstera': {'floor', 'turf'},
                'fern': {'floor', 'turf'}, 'banana': {'floor', 'turf'}, 'bird_of_paradise': {'turf', 'floor'},
                'hibiscus': {'turf'}, 'palm': {'turf', 'sand'}, 'pandanus': {'turf', 'sand', 'black'},
                'bush': {'turf'}}
    for g, ((cx, cy), rad, recipe) in enumerate(GROVES):
        for r, (key, n) in enumerate(recipe):
            placed = 0
            for t in range(160):
                if placed >= n:
                    break
                a = noise2(t, g * 7 + r, 1601) * 2 * math.pi
                d = math.sqrt(noise2(t, g * 7 + r, 1602)) * rad
                fx, fy = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.8)
                if clear(key, fx, fy, kinds_of.get(key)):
                    put(f'{key}-g{g}-{placed}', key, fx, fy)
                    placed += 1
    for r, (key, n, kinds) in enumerate(EDGES):
        placed = 0
        for t in range(1400):
            if placed >= n:
                break
            fx = int(noise2(t, r, 1603) * (IW - 20)) + 10
            fy = int(noise2(t, r, 1604) * (IH - 20)) + 10
            if clear(key, fx, fy, kinds, gap=10):
                put(f'{key}-e{placed}', key, fx, fy)
                placed += 1
    return out


def _objects(zone: str) -> list:
    """This zone's share of the island's props: those whose foot stands in it, as the
    zones' lists give them (before each sprite's own offset)."""
    sm = _sprites()
    col, row = LAYOUT['isles'][zone]
    ox, oy = col * W, row * H
    objs = []
    for (oid, key, fx, fy) in _island_props():
        if ox <= fx < ox + W and oy <= fy - 2 < oy + H:
            sp = sm[key]
            objs.append((oid, key, fx - ox - sp.w // 2 - sp.ox, fy - oy - sp.h - sp.oy))
    return objs


def isle_landing(frame: int = 0):
    """Lagoon Landing (sea level): the island's one pier, where the ferry from Driftwood
    ties up, out over the sheltered lagoon inside the reef. The river comes down the lower
    escarpment in a fall to its pool on the west and spreads into the lagoon through a
    fringe of mangroves; the dry shore lane climbs beside it to the stair, and the shore
    path goes east round the basalt headland to the cove."""
    cv, water, blocked, deck, ox, oy = paint('landing')
    # the pier: planks out over the shallows to where the ferry ties up (Codex's anchor,
    # island-pier at (112, 440))
    pier, rails = plank_bridge(cv, 99, 368, 26, 104, vertical=True)
    WATER_MASKS['isle_landing'] = water - pier - deck
    return cv, _objects('landing'), dict(STANDS['landing']), (blocked - pier) | rails


def isle_rainforest(frame: int = 0):
    """The Rainforest (one step up): a stream valley under a closed canopy, giants with
    buttress roots in groves, tree ferns and big-leafed plants, the floor dark and damp.
    The river falls into it at the head of the notch it has cut in the upland's rim, bends
    south-west down the valley through a deep pool, and goes over the lower escarpment for
    the lagoon; the trail crosses it on a footbridge and climbs the notch's west side by a
    stair. The upland bulges into it from the east; the sea breaks on black rocks along
    the north and west, with one small sandy bay and a rocky bay in the west."""
    cv, water, blocked, deck, ox, oy = paint('rainforest')
    WATER_MASKS['isle_rainforest'] = water - deck
    return cv, _objects('rainforest'), dict(STANDS['rainforest']), blocked


def isle_headwaters(frame: int = 0):
    """The Headwaters (two steps up): the island's old volcano rises behind, its flank
    green with moss and fern, and a waterfall drops from it into a deep round pool, with a
    rain shelter looking at it. The river leaves the pool west across the upland to the
    notch; the trail crosses it on a footbridge above the fall and runs south past the sea
    cliffs of the east bight to the stair down the upland's south rim."""
    cv, water, blocked, deck, ox, oy = paint('headwaters')
    WATER_MASKS['isle_headwaters'] = water - deck
    return cv, _objects('headwaters'), dict(STANDS['headwaters']), blocked


def isle_cove(frame: int = 0):
    """Black-sand Cove (sea level): the island's exposed south-east coast. From the
    terrace below the Headwaters a second stair goes down, and the trail comes out of the
    palms above a pocket of black volcanic sand held by a basalt arm, a sea stack off its
    end; the surf runs in white, a turtle rests above the tide line. The shore path goes
    west round the headland to the lagoon and the landing."""
    cv, water, blocked, deck, ox, oy = paint('cove')
    WATER_MASKS['isle_cove'] = water - deck
    return cv, _objects('cove'), dict(STANDS['cove']), blocked


# how each island zone's open ground is dressed (zones.dress)
DRESS.update({'landing': ('meadow', TROPIC[2:4], 0.3), 'headwaters': ('meadow', TROPIC[2:4], 0.3),
              'cove': ('meadow', TROPIC[2:4], 0.26), 'rainforest': ('forest', None, 0.3)})

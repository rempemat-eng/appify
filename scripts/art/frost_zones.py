"""The Frostline Highlands: Fir Hollow, Snowmelt Lake, the Snow Saddle and the High Lookout.

Split out of zones.py (18 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import math  # noqa: F401

import numpy as np
from PIL import Image

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401
import detail
import ground
import terrace as T

__all__ = ['RIDGE_COL', 'HOLLOW_COL', 'LAKE_PORT', 'SUMMIT_COL', 'HOLLOW_PORT', 'FACE_H', 'FALLS_X', 'SHOULDER', 'ICE', 'origin', 'snow_px', 'high_slope_px', 'high_band', 'snow_trail', 'peak_row', 'steep_px', 'lip', 'gthick', 'cover', 'turf_or_snow', 'water', 'foot_bridge', 'shoulders', 'hollow', 'HOLLOW_FALL', 'HOLLOW_RIM', 'snowmelt', 'saddle', 'summit']


# ---- the Frostline Highlands (Codex's connected world, PR #23: biome-extensions.json) ----
# The valley's upper watershed above the Ridge cabin, drawn as one landscape in the
# valley's own coordinates (gx, gy: the garden's top-left is 0, 0), so no tile edge shows.
# Tiers: the Ridge and Fir Hollow 3, Snowmelt Lake and the Snow Saddle 4, the High
# Lookout 5. One loop (ridge, hollow, lake, saddle, ridge) and one spur (the lookout).
# Snow follows height: patches in the hollow's upper slope, all snow from the lake up.
# The lake's outflow runs south through the hollow and falls over the escarpment into
# the Woodland's spring, the stream that crosses the garden (the meltwater reaches the
# valley river). Ports, Codex's spans: the way through each shared edge.
RIDGE_COL = (176, 232)    # the ridge's north edge / the saddle's south edge (x)
HOLLOW_COL = (144, 200)   # the hollow's north edge / the lake's south edge (x)
LAKE_PORT = (248, 304)    # the lake's east edge / the saddle's west edge (y)
SUMMIT_COL = (120, 168)   # the saddle's north edge / the lookout's south edge (x)
HOLLOW_PORT = (320, 376)  # the ridge's west edge / the hollow's east edge (y)
FACE_H = 24
FALLS_X = 84              # where the hollow's stream goes over the escarpment
SHOULDER = (-640, -510)   # the stepped rock shoulders between saddle and ridge (gy range)
ALPINE = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
ICE = ['#7C9CB8', '#A6C2D8', '#C8DCEA', '#E6F0F7']


def origin(zone: str):
    """A zone's top-left in the valley's coordinates."""
    c, r = LAYOUT['valley'][zone]
    return c * W, r * H


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


def steep_px(gx: int, gy: int) -> str:
    """Ground too steep to walk, in the valley's coordinates: a mountainside of rock
    buttresses with snow lying in the gullies between them, the gullies running down
    the fall line. Rock is faceted and lit on the upper left, with darker strata; the
    snow on it is a shade bluer than the snow underfoot (play-test 18 Oct: rock read as
    walkable)."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    def rock_at(x, y):
        return smooth_noise(x, y * 0.45, 26, 805) * 0.75 + smooth_noise(x, y, 70, 806) * 0.25
    r = rock_at(gx, gy)
    if r > 0.5:
        if rock_at(gx, gy - 1) <= 0.5 and r < 0.56:
            return SN[3]  # snow caught on the buttress's top
        h = smooth_noise(gx, gy, 9, 809)
        lit = smooth_noise(gx - 2, gy - 2, 9, 809) < h
        c = ST[3] if lit else ST[2]
        if (gy + int(smooth_noise(gx, 0, 20, 810) * 10) + gx // 9) % 8 == 0:
            c = ST[1]  # a stratum
        if rock_at(gx + 1, gy + 1) <= 0.5:
            c = ST[1]  # the buttress's shaded edge
        if r > 0.7 and not lit:
            c = ST[1] if (gx + gy) % 2 else ST[2]
        return c
    if r > 0.47:
        return SN[0]  # the gully snow's shade under the rock
    streak = (gx + int(smooth_noise(gx, gy, 22, 811) * 8)) % 11 == 0
    c = SN[1] if r < 0.3 or (gx + gy) % 3 == 0 else SN[2]
    return SN[0] if streak and r > 0.2 else c


def lip(cv: Canvas, walk: set, steep: set, ox: int, oy: int):
    """Where walkable snow meets steep ground: a bright cornice on the upper-left edges
    and a blue shade on the lower right, so the edge reads at a glance."""
    SN = MATERIALS['snow']
    for (x, y) in walk:
        up, left = (x, y - 1) in steep, (x - 1, y) in steep
        down, right = (x, y + 1) in steep, (x + 1, y) in steep
        if up or left:
            cv.set(x, y, SN[3] if (x + y) % 3 else '#FFFFFF')
        elif down or right:
            cv.set(x, y, SN[0])


def gthick(zone: str, gpoints, radius: float) -> set:
    """A path or a stream given in the valley's coordinates, as this zone's pixels (no
    wobble, so it meets its continuation across a border exactly)."""
    ox, oy = origin(zone)
    pts = set()
    for (x0, y0), (x1, y1) in zip(gpoints, gpoints[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t - ox, y0 + (y1 - y0) * t - oy
            if -radius - 2 <= cx <= W + radius + 2 and -radius - 2 <= cy <= H + radius + 2:
                pts |= disc(cx, cy, radius)
    return {(x, y) for (x, y) in pts if 0 <= x < W and 0 <= y < H}


def cover(gx: int, gy: int) -> bool:
    """Does snow lie here? Patches in the hollow's upper slope, more the higher it goes,
    and everywhere above the hollow (the lake's tier and up)."""
    if gy < -576:
        return True
    a = (-gy) / 576  # 0 at the hollow's foot, 1 at its top
    return smooth_noise(gx, gy, 26, 851) < (a - 0.38) * 1.7


def turf_or_snow(cv: Canvas, zone: str, frame: int):
    """The hollow's ground: alpine turf, with snow lying in patches up the slope."""
    ox, oy = origin(zone)
    ground.valley(cv, zone, frame)
    for y in range(H):
        for x in range(W):
            if cover(x + ox, y + oy):
                cv.set(x, y, snow_px(x + ox, y + oy, 852))


def water(cv: Canvas, pts: set, ox: int, oy: int, frozen_rim: bool = True):
    """A mountain stream: dark clear water, white where it runs fast, an icy rim."""
    WTR = MATERIALS['water']
    for (x, y) in pts:
        gx, gy = x + ox, y + oy
        c = WTR[1] if (gx // 2 + gy) % 5 else WTR[2]
        if (gy + int(math.sin(gx / 5) * 2)) % 7 == 0:
            c = WTR[3]
        if (x, y - 1) not in pts or (x - 1, y) not in pts:
            c = ICE[2] if frozen_rim else WTR[0]
        cv.set(x, y, c)
    ST = MATERIALS['stone']
    for (x, y) in pts:  # stones along the banks
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q not in pts and 0 <= q[0] < W and 0 <= q[1] < H and noise2(q[0] + ox, q[1] + oy, 853) > 0.55:
                cv.set(*q, ST[3] if dy == 0 and dx < 0 else ST[2])


def foot_bridge(cv: Canvas, x0: int, y0: int, w: int, h: int, vertical: bool):
    """A plank footbridge with a rail each side, on stone abutments; vertical = the deck
    runs north-south. Returns the walkable deck."""
    WD, ST = MATERIALS['wood'], MATERIALS['stone']
    deck = set()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            across = (x - x0) if vertical else (y - y0)
            along = (y - y0) if vertical else (x - x0)
            span = w if vertical else h
            length = h if vertical else w
            if along < 3 or along >= length - 3:
                c = ST[3] if (x + y) % 3 else ST[2]  # the abutments
                deck.add((x, y))
            elif across < 2 or across >= span - 2:
                c = WD[1] if across in (0, span - 1) else WD[3]  # the rails
            else:
                c = WD[3] if (along // 3) % 2 else WD[2]
                if along % 3 == 0:
                    c = WD[1]
                deck.add((x, y))
            cv.set(x, y, c)
    for k in range(1, 3):  # its shadow on the water, down and right
        for t in range(h if vertical else w):
            if vertical:
                style.darken(cv, x0 + w - 1 + k, y0 + t)
            else:
                style.darken(cv, x0 + t, y0 + h - 1 + k)
    return deck


# ---- the waterfall kit (art-faults A1; world-references.md 3, rule 1) -------------------------
# Drawn over terrace.py's plain fall until the toolkit takes it in (see the PR: proposed for
# terrace.py's falls_paint, with the 'rock' material and a zone turf ramp).
ROCK = ['#25242C', '#3B3740', '#57545D', '#78757B', '#9C999B', '#C6C4BE']


class _FallKit:
    """Paints each fall of a built terrace on a zone's ground (numpy, in place)."""

    def __init__(self, img, t, seed):
        self.img, self.kind, self.seed = img, t.kind, seed
        self.H, self.W = t.kind.shape
        self.wet = np.zeros(t.kind.shape, bool)
        for (x, y) in t.water:
            self.wet[y, x] = True
        self.fall = (t.kind == T.FALL_K)
        self.rocks = np.zeros(t.kind.shape, bool)

    def put(self, x, y, c):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.img[y, x] = T.rgb(c)

    def mul(self, x, y, k):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.img[y, x] = (self.img[y, x] * np.array(k)).astype(np.uint8)

    def paint(self):
        """A fall (world-references.md, 3, the waterfall kit; verticality 4f, Water): the
        channel tips over a notch in the lip between two rock buttresses with a lit white
        curl, drops straight down the face as wide as its channel in a three-tone sheet with
        vertical streaks of different lengths, wets the rock beside it (darker, moss, ferns,
        spray) and lands in a foam band in a pool wider than the fall."""
        fall, H, W = self.fall, self.H, self.W
        lab = T._components(fall)
        sd = self.seed * 131 + 580
        n = lambda a, b, k: noise2(a, b, sd + k)  # noqa: E731
        ST = ROCK
        WHITE = '#FFFFFF'
        for k in range(1, lab.max() + 1):
            yy, xx = np.nonzero(lab == k)
            fx0, fx1, fy0, fy1 = int(xx.min()), int(xx.max()) + 1, int(yy.min()), int(yy.max()) + 1
            fw = fx1 - fx0
            # 1. the approach: the channel's last rows run fast and glassy toward the lip
            for y in range(max(0, fy0 - 10), fy0):
                d = fy0 - y                      # rows to the lip
                for x in range(fx0, fx1):
                    if not self.wet[y, x] or self.fall[y, x]:
                        continue
                    kx = x - fx0
                    if d <= 2:
                        c = T.WTR[4] if (x + y) % 2 or kx < fw // 2 else T.WTR[3]
                    elif n(kx, 0, 1) > 0.5 and d <= 7:
                        c = T.WTR[3]               # streaks drawn out by the pull of the drop
                    else:
                        c = T.WTR[2] if kx > 1 else T.WTR[3]
                    self.put(x, y, c)
            # 2. the sheet: three tones in columns, bright streaks of 3 to 14 px, whiter low down
            for x in range(fx0, fx1):
                kx = x - fx0
                east = kx / max(1, fw - 1)       # 0 lit west .. 1 shaded east
                base = T.WTR[3] if n(kx, 1, 2) > 0.35 + east * 0.45 else T.WTR[2]
                if n(kx, 2, 3) > 0.86 and 0 < kx < fw - 1:
                    base = T.WTR[1]                # a darker strand where the water runs thin
                y, seg = fy0 + 2, 0
                while y < fy1:
                    ln = 3 + int(n(kx, seg, 4) * 12)
                    r = n(kx, seg, 5)
                    tone = T.FOAM if r > 0.94 else T.WTR[4] if r > 0.74 - (0.08 if east < 0.5 else 0) else base
                    for yy_ in range(y, min(fy1, y + ln)):
                        c = tone
                        low = fy1 - yy_          # rows above the foot
                        if low <= 5 and n(x, yy_, 6) > 0.25 + low * 0.12:
                            c = T.FOAM if (x + yy_) % 2 else T.WTR[4]   # aerated at the foot
                        if kx == 0:
                            c = T.WTR[4] if c != T.FOAM else c          # the lit west edge
                        elif kx == fw - 1:
                            c = T.WTR[1] if c not in (T.FOAM,) else T.WTR[3]   # the shaded east edge
                        self.put(x, yy_, c)
                    y += ln
                    seg += 1
            # 3. the curl over the lip: white, bulging a px past the sheet each side
            for x in range(fx0 - 1, fx1 + 1):
                kx = x - fx0
                for dy, c in ((-1, T.WTR[4]), (0, WHITE if kx < fw * 0.6 else T.FOAM), (1, T.FOAM)):
                    if x in (fx0 - 1, fx1) and dy != 0:
                        continue
                    self.put(x, fy0 + dy, c)
                if 0 <= kx < fw and n(kx, 3, 7) > 0.45:
                    self.put(x, fy0 + 2, T.FOAM if kx < fw * 0.6 else T.WTR[4])   # a scalloped hem
            for i in range(3):                   # spray breaking off the curl
                x = fx0 + int(n(i, 4, 8) * fw)
                self.put(x + (1 if i % 2 else -1), fy0 - 2, T.WTR[4])
            # 4. the buttresses: a rock block either side of the notch, sitting on the lip
            for side in (-1, 1):
                bw = 9 + int(n(side, 5, 9) * 4)
                bh = 8 + int(n(side, 6, 10) * 4)
                bx0 = fx0 - bw if side < 0 else fx1
                ox, oy = bx0 + bw / 2 - 0.5, fy0 - bh / 2 + 1
                # two overlapping lumps: the main block and a lower one leaning out from the notch
                lumps = ((ox, oy, bw / 2, bh / 2 + 0.5), (ox - side * bw * 0.25, fy0 + 1.5, bw * 0.38, 3.5))
                blk = set()
                for y in range(fy0 - bh - 1, fy0 + 6):
                    for x in range(bx0 - 3, bx0 + bw + 3):
                        if not (0 <= x < W and 0 <= y < H) or self.fall[y, x] or (side < 0 and x >= fx0) \
                                or (side > 0 and x < fx1):
                            continue
                        rough = (n(x, y, 11) - 0.5) * 0.25
                        if any(((x - a) / ra) ** 2 + ((y - b_) / rb) ** 2 <= 1 + rough for (a, b_, ra, rb) in lumps):
                            blk.add((x, y))
                near = fx1 if side > 0 else fx0 - 1           # the column facing the fall
                for (x, y) in blk:
                    a, b_, ra, rb = min(lumps, key=lambda L: ((x - L[0]) / L[2]) ** 2 + ((y - L[1]) / L[3]) ** 2)
                    v = -((x - a) / ra * 0.75 + (y - b_) / rb * 0.65)   # lit from the upper left
                    c = ST[5] if v > 0.8 else ST[4] if v > 0.3 else ST[3] if v > -0.25 else ST[2]
                    if (x, y + 1) not in blk or (x + 1, y) not in blk:
                        c = ST[1]                             # its shaded under side and east edge
                    if (x, y - 1) not in blk and (x - 1, y) not in blk:
                        c = ST[5]
                    if x == near:
                        c = ST[3] if side > 0 else ST[1]      # the face toward the water
                    if y >= fy0 + 3:
                        c = ST[1] if v > -0.25 else ST[0]     # wet at its foot on the face
                    if n(x // 2, y // 2, 12) > 0.72 and y < fy0 and (x, y - 1) not in blk:
                        c = T.LEAF[3] if v > 0 else T.LEAF[2]     # moss on the wet block's top
                    self.put(x, y, c)
                    self.rocks[y, x] = True
                cx_ = int(ox) + (1 if side < 0 else -1)      # a crack down it
                for y in range(int(oy), fy0 + 2):
                    if (cx_, y) in blk and (cx_, y - 1) in blk and (cx_ + 1, y) in blk:
                        self.put(cx_ + (y - int(oy)) // 3 * side, y, ST[1])
                for (x, y) in blk:                     # its shade down and right on the turf
                    for d in (1, 2):
                        q = (x + d, y + d)
                        if q not in blk and 0 <= q[0] < W and 0 <= q[1] < H and self.kind[q[1], q[0]] == T.TOP \
                                and not self.wet[q[1], q[0]] and not self.rocks[q[1], q[0]]:
                            self.mul(q[0], q[1], T.STRONG if d == 1 else T.MEDIUM)
            # 5. beside the sheet: wet dark rock, moss in the crevices, ferns, spray
            for y in range(fy0 + 1, fy1):
                for x in list(range(fx0 - 7, fx0)) + list(range(fx1, fx1 + 7)):
                    if not (0 <= x < W) or self.kind[y, x] not in (T.FACE_K, T.STRIP_K) or self.rocks[y, x]:
                        continue
                    d = fx0 - x if x < fx0 else x - fx1 + 1
                    if d <= 2 or (d <= 5 and n(x, y // 3, 13) > d * 0.15):
                        self.mul(x, y, (0.7, 0.76, 0.86) if d <= 2 else (0.82, 0.86, 0.92))
                    px = self.img[y, x]
                    if d <= 5 and int(px[0]) + int(px[1]) + int(px[2]) < 190 and n(x, y, 14) > 0.55:
                        self.put(x, y, T.LEAF[1] if n(x, y, 15) > 0.5 else T.LEAF[2])   # moss in the dark
                    low = (y - fy0) / max(1, fy1 - fy0)
                    if d <= 3 and n(x, y, 16) > 0.9 - low * 0.25:
                        self.put(x, y, T.WTR[4] if (x + y) % 3 else T.FOAM)              # spray
            for i in range(4):                   # ferns hanging from the wet face
                side = -1 if i % 2 else 1
                fxp = (fx0 - 4 - int(n(i, 7, 17) * 3)) if side < 0 else (fx1 + 3 + int(n(i, 7, 17) * 3))
                fyp = fy0 + 6 + int(n(i, 8, 18) * max(1, fy1 - fy0 - 12))
                if not (0 <= fxp < W) or self.kind[fyp, fxp] not in (T.FACE_K, T.STRIP_K):
                    continue
                for t in range(4):               # a frond arching out and down, leaflets each side
                    x, y = fxp + side * (t // 2), fyp + t
                    if 0 <= x < W and 0 <= y < H and self.kind[y, x] in (T.FACE_K, T.STRIP_K):
                        self.put(x, y, T.LEAF[3] if t < 2 else T.LEAF[2])
                        self.put(x - 1, y + 1, T.LEAF[1])
                        if t % 2 == 0:
                            self.put(x + side, y, T.LEAF[4] if side < 0 else T.LEAF[3])
            # 6. the landing: a foam band across the pool under the fall, mist, rings, the pool's depth
            pool = np.zeros_like(self.wet)
            y0p = fy1
            for y in range(y0p, min(H, y0p + 32)):
                for x in range(max(0, fx0 - 24), min(W, fx1 + 24)):
                    if self.wet[y, x] and not self.fall[y, x]:
                        pool[y, x] = True
            dep = np.zeros(pool.shape, np.int16)
            cur = pool.copy()
            for i in range(4):
                inner = cur & T._shift(cur, 1, 0) & T._shift(cur, -1, 0) & T._shift(cur, 0, 1) & T._shift(cur, 0, -1)
                dep[inner] = i + 1
                cur = inner
            for y, x in zip(*np.nonzero(pool)):
                d = int(dep[y, x])
                if d >= 3:
                    c = T.WTR[0] if abs(x + 0.5 - (fx0 + fx1) / 2) < fw * 0.7 and y < fy1 + 12 else T.WTR[1]  # deep under the fall
                elif d >= 1:
                    c = T.WTR[2] if (x + y) % 5 else T.WTR[1]
                else:
                    below = y + 1 < H and not self.wet[y + 1, x]
                    c = T.WTR[3] if below else T.WTR[2]
                    if below and n(x, y, 20) > 0.55:
                        c = T.FOAM                  # the lit foam line at the waterline
                self.put(x, y, c)
            cx = (fx0 + fx1) / 2
            for y in range(fy1, min(H, fy1 + 6)):   # the foam band, wider than the sheet
                for x in range(fx0 - 3, fx1 + 3):
                    if not (0 <= x < W) or not pool[y, x]:
                        continue
                    r = y - fy1
                    edge = min(x - (fx0 - 3), fx1 + 2 - x)
                    if r <= 1 and edge >= 1:
                        c = WHITE if x < cx else T.FOAM
                    elif r <= 3 and (edge >= 2 or (x + y) % 2):
                        c = T.FOAM if (x + y) % 2 or edge >= 3 else T.WTR[4]
                    elif n(x, y, 21) > 0.45:
                        c = T.WTR[4] if (x + y) % 2 else T.FOAM
                    else:
                        continue
                    self.put(x, y, c)
            for y in range(fy1 - 4, fy1):          # mist over the face's foot beside the sheet
                for x in list(range(fx0 - 4, fx0)) + list(range(fx1, fx1 + 4)):
                    if 0 <= x < W and self.kind[y, x] in (T.FACE_K, T.STRIP_K) and (x + y) % 2 and n(x, y, 22) > 0.4:
                        self.put(x, y, T.lerp(self.img[y, x], T.FOAM, 0.55))
            for i, (rx, ry, ra) in enumerate(((cx - fw * 0.6 - 4, fy1 + 10, 6), (cx + fw * 0.5 + 4, fy1 + 9, 5),
                                              (cx, fy1 + 14, 8))):
                for a in range(0, 360, 20):     # rings spreading out from the landing
                    x = int(rx + ra * math.cos(math.radians(a)))
                    y = int(ry + ra * 0.4 * math.sin(math.radians(a)))
                    if 0 <= x < W and 0 <= y < H and pool[y, x] and dep[y, x] >= 1 and a % 60:
                        self.put(x, y, T.WTR[3])
            for i in range(6):                     # foam patches drifting off downstream
                x = int(cx + (n(i, 9, 23) - 0.5) * (fw + 20))
                y = fy1 + 6 + int(n(i, 10, 24) * 14)
                for dx in range(2 + i % 2):
                    if 0 <= x + dx < W and 0 <= y < H and pool[y, x + dx] and dep[y, x + dx] >= 1:
                        self.put(x + dx, y, T.FOAM if dx == 0 else T.WTR[4])


def _band(gx: int):
    """The shoulders' band at a valley x: (top, bottom) in valley y (unchanged since the
    Frostline was drawn: the walk does not change)."""
    tilt = int(gx * 0.1) - 16
    top = SHOULDER[0] + tilt + int(smooth_noise(gx, 0, 22, 861) * 8)
    bottom = SHOULDER[1] - 4 + tilt + int(smooth_noise(gx, 9, 18, 862) * 8)
    return top, bottom


def _outcrops():
    """The rock shoulders' outcrops, in the valley's coordinates (the same list for the
    saddle and the ridge, so an outcrop crossing the seam is drawn whole on both sides).
    Two rows, the back one standing higher up the slope; along each, outcrops of different
    widths and heights with snow-filled gullies between them. Each is a list of courses
    (x0, x1, y_top, y_bottom) from its foot up, each course set back on the one below, more
    on one side than the other, so a ledge of snow lies on it."""
    outs = []
    for row in (0, 1):                   # 0 the back row, 1 the front
        gx, i = -80 + row * 23, 0
        while gx < W + 80:
            key = row * 100 + i
            gap = 1 + int(noise2(key, 1, 880) * 6)
            w = 34 + int(noise2(key, 2, 880) * 48)
            x0, x1 = gx + gap, gx + gap + w
            gx = x1
            i += 1
            if x1 > RIDGE_COL[0] - 4 and x0 < RIDGE_COL[1] + 4:   # the switchback's gully stays open
                if x0 < RIDGE_COL[0] - 18:
                    x1 = RIDGE_COL[0] - 4
                elif x1 > RIDGE_COL[1] + 18:
                    x0 = RIDGE_COL[1] + 4
                else:
                    continue
            cx = (x0 + x1) // 2
            top, bottom = _band(cx)
            span = bottom - top
            foot = (top + int(span * 0.55) if row == 0 else bottom) - int(noise2(key, 4, 880) * 5)
            height = int(span * ((0.5 if row == 0 else 0.4) + noise2(key, 3, 880) * 0.35))
            steep_west = noise2(key, 5, 880) > 0.5           # one flank steep, the other stepped
            courses, y, a, b, k = [], foot, x0, x1, 0
            while y > foot - height and b - a >= 12:
                th = 6 + int(noise2(key, 10 + k, 881) * 7)
                courses.append((a, b, max(y - th, foot - height), y))
                y -= th
                da = int(noise2(key, 20 + k, 881) * 4)
                db = 2 + int(noise2(key, 30 + k, 881) * 10)
                a, b = (a + da, b - db) if steep_west else (a + db, b - da)
                k += 1
            outs.append((row, x0, x1, courses))
    return outs


def shoulders(cv: Canvas, zone: str) -> set:
    """The rock shoulders between the Snow Saddle and the Ridge cabin's terrace (art-faults
    A10), one band across the border in the valley's coordinates: two rows of outcrops of
    different widths and heights, each built of courses of rough blocks set back one on
    another, lit on top and on the west, with dark crevices; snow lies on each ledge and
    fills the gullies and hollows between them, blue in their shadow. Open only where the
    switchback comes down (RIDGE_COL), between rock walls. Returns the blocked pixels in this
    zone (the same band as before: the walk does not change)."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    ox, oy = origin(zone)
    blocked = set()
    owner = {}                           # (gx, gy) -> the course standing there, front row over back
    for oi, (row, x0, x1, courses) in enumerate(_outcrops()):
        for ci, (a, b, yt, yb) in enumerate(courses):
            for gy in range(yt, yb):
                r = gy - yt
                # the course's ends are rough: a lump in or out every few rows
                ia = int(noise2(a, gy // 3, 882) * 3) + (1 if r == 0 else 0)
                ib = int(noise2(b, gy // 3, 883) * 3) + (1 if r == 0 else 0)
                for gx in range(a + ia, b - ib):
                    owner[(gx, gy)] = (row, oi, ci, a + ia, b - ib, yt, yb)
    for y in range(H):
        gy = y + oy
        if not (SHOULDER[0] - 24 <= gy < SHOULDER[1] + 24):
            continue
        for x in range(W):
            gx = x + ox
            top, bottom = _band(gx)
            if gy < top or gy >= bottom:
                continue
            g0 = RIDGE_COL[0] + int(noise2(gy // 7, 1, 863) * 3)
            g1 = RIDGE_COL[1] - int(noise2(gy // 7, 2, 863) * 3)
            if g0 <= gx < g1:
                cv.set(x, y, snow_px(gx, gy, 864))
                continue
            blocked.add((x, y))
            near = min(abs(gx - g0), abs(gx - g1 + 1))
            if near < 2:
                cv.set(x, y, ST[3] if gx < g0 else ST[1])     # the gully's walls, lit on the west
                continue
            o = owner.get((gx, gy))
            if o is None:
                # deep snow in the gullies and hollows: a shade bluer than the snow underfoot
                # (steep ground, not a place to walk), darker in each outcrop's shadow
                n = smooth_noise(gx, gy, 14, 884)
                c = SN[2] if n > 0.7 else SN[1] if n > 0.25 or (gx + gy) % 2 else SN[0]
                sh = next((d for d in range(1, 6) if (gx - d, gy - d // 2) in owner), 0)
                if sh:
                    c = SN[0] if sh <= 2 else SN[1]
                elif (gx, gy - 1) in owner:
                    c = SN[0]                                  # drifted against a course's foot
                elif (gx, gy + 1) in owner or (gx, gy + 2) in owner:
                    c = SN[3]                                  # a cornice over the rock below
                cv.set(x, y, c)
                continue
            row, oi, ci, a, b, yt, yb = o
            r, th = gy - yt, yb - yt
            above = owner.get((gx, gy - 1))
            exposed = above is None or above[1] != oi            # nothing of this outcrop above
            # rough blocks: joints 10 to 24 px apart, offset course to course
            key = oi * 13 + ci

            def joint(k, key=key):
                return k * 17 + int(noise2(k, key, 887) * 9) - 4
            p = gx + int(noise2(ci, oi, 886) * 23)
            bi = p // 17
            while p < joint(bi):
                bi -= 1
            while p >= joint(bi + 1):
                bi += 1
            u, span = p - joint(bi), joint(bi + 1) - joint(bi)
            tone = 3 if noise2(bi, key, 888) > 0.5 else 2
            if noise2(bi, key, 889) > 0.85:
                tone = 4
            west, east = gx - a, b - 1 - gx
            if exposed and r <= 1:
                c = SN[3] if r == 0 or noise2(gx, gy, 890) > 0.35 else SN[2]   # snow on the ledge
                if west < 2:
                    c = '#FFFFFF' if r == 0 else SN[3]
                elif east < 3:
                    c = SN[1]
            elif exposed and r == 2:
                c = ROCK[5] if west < (b - a) * 0.6 else ROCK[4]              # the lit arris under it
            elif r == th - 1:
                c = ROCK[1] if (gx // 3 + gy) % 4 else ROCK[0]                # the bed: a crevice
            elif u == 0 and noise2(bi, key, 893) > 0.25:
                c = ROCK[1]                                                   # a joint between blocks
            elif u == 1:
                c = ROCK[min(5, tone + 1)]                                    # the next block's lit end
            elif u >= span - 2:
                c = ROCK[max(1, tone - 1)]                                    # this block's shaded end
            else:
                lit = r <= 3 and u < span * 0.6
                c = ROCK[tone + 1] if lit else ROCK[tone]
                if r >= th - 3:
                    c = ROCK[max(1, tone - 1)]                                # under the block's belly
                if noise2(gx // 2, gy // 3, 891) > 0.94:
                    c = ROCK[1]                                               # a crack
            if west < 2 and not (exposed and r <= 1):
                c = ROCK[5] if west == 0 else ROCK[4]                         # the outcrop's lit west end
            elif east < 3 and not (exposed and r <= 1):
                c = ROCK[1] if east == 0 else ROCK[2]                         # its east end in shade
            if r == th - 2 and c in ROCK[2:] and noise2(gx // 3, key, 892) > 0.88:
                c = SN[1] if gx % 3 else SN[0]                                # snow caught in the crevice
            cv.set(x, y, c)
    return blocked


HOLLOW_FALL = (88, 104)   # the hollow's fall over the escarpment: its channel, two grid cells
HOLLOW_RIM = 504          # the escarpment's rim (grid row 63); its face is 32 px
HOLLOW_NOTCH = 256        # the lower ground under the face runs from the west edge to here


def _hollow_water():
    """The hollow's stream on the soft grid, as cells for terrace.py: 16 px runs (two
    cells) with rounded turns, down the east side, a jog round the rocks, west under the
    trees to the notch, over the fall and into its pool. Its two ends meet water off the
    grid and are drawn by _water_seams()."""
    fc = HOLLOW_FALL[0] // 8
    return [(30, 0, 32, 23), (30, 21, 34, 23), (32, 21, 34, 38), (30, 36, 34, 38), (30, 36, 32, 57),
            (fc, 55, 32, 57), (fc, 55, fc + 2, 63), (fc - 2, 67, fc + 4, 70)]


def _hx(c) -> str:
    return '#%02X%02X%02X' % tuple(int(v) for v in c[:3])


def _alpine_turf(cv, t):
    """terrace.py draws its lips, banks, moss and foot grass in the valley's meadow grass;
    Fir Hollow's turf is alpine. Every pixel the toolkit painted in that ramp near its faces
    and water takes the matching alpine tone (proposed for terrace.py as a zone turf ramp)."""
    near = np.isin(t.kind, (T.FACE_K, T.STRIP_K, T.CHEEK_K, T.FALL_K))
    for (x, y) in t.water:
        near[y, x] = True
    for _ in range(8):
        near = near | T._shift(near, 1, 0) | T._shift(near, -1, 0) | T._shift(near, 0, 1) | T._shift(near, 0, -1)
    turf = {}
    for L in (0, 1):
        g = T.grass_ramp(L)
        a = [T.lerp(c, '#E8EBA0', 0.09 * L) for c in ALPINE]
        turf.update({T.rgb(g[i]): a[i] for i in range(5)})
    img = np.array(cv.img.convert('RGB'))
    for y, x in zip(*np.nonzero(near)):
        p = tuple(int(v) for v in img[y, x])
        if p in turf:
            img[y, x] = turf[p]
    cv.img.paste(Image.fromarray(img, 'RGB').convert('RGBA'), (0, 0))


def _water_seams(cv, base, t, water):
    """Where the stream meets its neighbours' water off the grid: the lake's outflow crosses
    the north seam 10 px wide at x 244..253 (snowmelt), and the Woodland's brook comes in 7 px
    wide at x 79..85 (valley_zones.woodland, from FALLS_X). The channel narrows to the first
    over its top 14 rows; the pool lets out into the second through a short channel."""
    WTR, SO, ST_ = MATERIALS['water'], T.SOIL, MATERIALS['stone']
    for y in range(0, 14):
        tt = min(1.0, max(0.0, (y - 5) / 8))
        lo, hi = int(round(244 - 4 * tt)), int(round(254 + 2 * tt))
        for x in range(234, 262):
            if lo <= x < hi:
                if x in (lo, lo + 1) and (x, y) not in water:
                    cv.set(x, y, WTR[0])
                continue
            water.discard((x, y))
            c = base.get(x, y)
            if x == lo - 1:
                c = SO[1]                                  # the west bank faces east: dark
            elif x == lo - 2:
                c = _hx(T.lerp(ALPINE[1], '#000000', 0.1))
            elif x == hi:
                c = SO[3]                                  # the east bank faces west: lit
            cv.set(x, y, c)
    for y in range(560, H):
        lo, hi = 79, 86                                    # straight out of the pool's floor
        for x in range(lo - 3, hi + 3):
            if lo <= x < hi:
                c = WTR[1] if (x + y // 2) % 7 else WTR[2]
                if x == lo or y >= H - 3:
                    c = WTR[0] if x == lo else WTR[1]
                elif (y * 3 + x) % 13 == 0:
                    c = WTR[2]
                cv.set(x, y, c)
                water.add((x, y))
            elif (x, y) not in water:
                if x == lo - 1:
                    c = SO[1]                             # earth banks, dark on the west
                elif x == hi:
                    c = SO[3]                             # lit on the east
                else:
                    continue
                if noise2(x, y // 2, 905) > 0.6:
                    c = ST_[2] if x == hi else ST_[1]     # a wet stone in the bank
                cv.set(x, y, c)


def _grid_path(T, rects, r=6):
    """A path of orthogonal runs (rects in zone px), its corners rounded."""
    m = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in rects:
        m[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = True
    m = T.rounded(m, r, 4)
    return {(int(x), int(y)) for (y, x) in zip(*np.nonzero(m))}


def hollow(frame: int = 0):
    """Fir Hollow (tier 3), west of the ridge's alpine meadow: a sheltered bowl of old
    firs on alpine turf, snow lying in patches that grow up the slope. The first place on
    the soft 8 px grid (verticality.md 4f; terrace.py): the way in from the ridge crosses
    the lake's outflow on a footbridge into a quiet clearing, and a switchback of straight
    runs climbs north through thinning, snowier firs to the lake. The stream runs in
    grid-led banks down the east side and west under the trees to a notch in the lip of the
    escarpment, a 32 px rock face above the Woodland, and falls between two buttresses into
    a pool (art-faults A1); a spur path crosses it to a lookout beside the fall. Firs stand
    in clumps of three to seven, two or three deep along the west edge and the rim, with
    saplings and stumps (A2). No way down the face: the Ridge is the way up."""
    import valley_zones as vz
    import zones as Z
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    ox, oy = origin('hollow')
    cv = Canvas(W, H)
    turf_or_snow(cv, 'hollow', frame)
    base = Canvas(W, H)
    base.paste(cv, 0, 0)
    # ---- the paths, on the grid (16 px footpaths, dog-legs with rounded turns)
    way_in = _grid_path(T, [(168, 340, W + 8, 356), (168, 340, 184, 412), (136, 396, 184, 412)])
    climb = _grid_path(T, [(136, 312, 152, 412), (96, 312, 152, 328), (96, 240, 112, 328), (96, 240, 160, 256),
                           (144, 184, 160, 256), (112, 184, 160, 200), (112, 128, 128, 200), (112, 128, 180, 144),
                           (164, -8, 180, 144)])
    spur = _grid_path(T, [(136, 396, 152, 470)])
    lookout = _grid_path(T, [(112, 464, 168, 500)], r=8)
    clearing = _grid_path(T, [(112, 380, 200, 428)], r=10)
    trail = way_in | climb | spur
    wet_cells = _hollow_water()
    wet = np.zeros((H, W), bool)
    for (c0, r0, c1, r1) in wet_cells:
        wet[r0 * 8:r1 * 8, c0 * 8:c1 * 8] = True
    # the clearing: sunlit turf in a ring of firs (a rounded rectangle, never an ellipse)
    for (x, y) in clearing:
        if not cover(x + ox, y + oy):
            cv.set(x, y, ALPINE[3] if smooth_noise(x, y, 10, 875) > 0.45 else ALPINE[2])
    for k in range(9):                 # dapple: a few pale blobs, never one bright oval
        bx, by = 118 + int(noise2(k, 1, 893) * 76), 384 + int(noise2(k, 2, 893) * 40)
        for (x, y) in oval(bx, by, 3 + k % 3, 2):
            if (x, y) in clearing and (x, y) not in trail and (x + y) % 2:
                cv.set(x, y, ALPINE[4])
    # the trodden track, earth all the way up (the snow melts off it first), slush at its
    # edges where the snow lies; ragged turf teeth over its edges elsewhere
    snowy_edge = set()
    trail = trail | lookout             # the lookout: worn to earth where people stand and look
    for (x, y) in trail:
        if wet[y, x]:
            continue
        gx, gy = x + ox, y + oy
        edge = any((x + dx, y + dy) not in trail for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge and cover(gx, gy):
            cv.set(x, y, SN[1])
            snowy_edge.add((x, y))
        else:
            cv.set(x, y, P[3] if smooth_noise(gx, gy, 7, 874) < 0.7 else P[4])
    keep = snowy_edge | {(x, y) for (x, y) in trail if cover(x + ox, y + oy)}
    # (the track runs on past the seams to the ridge and the lake: no turf edge across them)
    beyond = {(x, y) for x in range(W, W + 6) for y in range(340, 356)} | \
        {(x, y) for x in range(164, 180) for y in range(-6, 0)}
    detail.grass_edge(cv, {p for p in trail if 0 <= p[0] < W and 0 <= p[1] < H} | beyond,
                      ALPINE, P, keep=keep, seed=895)
    for (x, y) in trail | lookout:   # pebbles bedded in the track
        if 0 <= x < W - 2 and 0 <= y < H and noise2(x, y, 896) < 0.004 and (x + 2, y + 2) in trail and not wet[y, x]:
            detail.pebble(cv, x, y, ST, big=noise2(x, y, 897) < 0.0015)
    # ---- the terrain: the escarpment as a tier edge (terrace.py), the stream and its fall
    tiers = [[1] * (W // 8) for _ in range(H // 8)]
    for r in range(HOLLOW_RIM // 8, H // 8):
        for c in range(HOLLOW_NOTCH // 8):
            tiers[r][c] = 0
    t = T.build(cv, tiers, face=32, material='earth', water=wet_cells, tops=False, seed=17)
    _alpine_turf(cv, t)
    water = set(t.water)
    _water_seams(cv, base, t, water)
    img = np.array(cv.img.convert('RGB'))
    kit = _FallKit(img, t, 17)
    kit.paint()
    cv.img.paste(Image.fromarray(img, 'RGB').convert('RGBA'), (0, 0))
    rocks = {(int(x), int(y)) for (y, x) in zip(*np.nonzero(kit.rocks))}
    # ---- the lower ground under the face: woodland floor in the escarpment's shade,
    # mossy stones round the pool, ferns in the damp
    pool_wet = {(x, y) for (x, y) in water if y >= HOLLOW_RIM + 32}
    for y in range(HOLLOW_RIM + 32, H):
        for x in range(HOLLOW_NOTCH):
            if t.kind[y, x] != T.TOP or (x, y) in pool_wet:
                continue
            # the wood's floor below the face: shade deepening toward the trees of the Woodland
            # (its top rows lie under the crowns closing the seam), leaf litter in drifts
            k = 0.22 + 0.4 * (y - HOLLOW_RIM - 32) / 40
            if smooth_noise(x, y, 9, 898) > 0.6:
                k += 0.12
            cv.set(x, y, _hx(T.lerp(cv.get(x, y), '#24382A', k)))
    for (x, y) in sorted(pool_wet):  # a chain of stones along the pool's low (south and side) shore
        for (dx, dy) in ((0, 1), (-1, 0), (1, 0)):
            q = (x + dx, y + dy)
            if q in pool_wet or not (0 <= q[0] < W and 0 <= q[1] < H) or t.kind[q[1], q[0]] != T.TOP:
                continue
            if noise2(q[0] // 3, q[1] // 2, 899) > 0.35:
                cv.set(*q, ST[3] if dx <= 0 and dy == 0 else ST[2] if dy == 0 else ST[1])
                if q[1] + 1 < H and (q[0], q[1] + 1) not in pool_wet:
                    cv.set(q[0], q[1] + 1, ST[1])
    for i in range(7):                # ferns on the lower ground, clumped near the water
        fx = 40 + int(noise2(i, 1, 900) * 200)
        fy = HOLLOW_RIM + 40 + int(noise2(i, 2, 900) * 28)
        if any((fx + d, fy) in pool_wet for d in range(-6, 7)):
            continue
        if 0 <= fy < H and t.kind[fy, fx] == T.TOP:
            vz.fern(cv, fx, fy, seed=i)
    # ---- the scree east of the notch, where the escarpment gives way to the ridge's slope
    scree = set()
    for x in range(HOLLOW_NOTCH, W):
        top = 498 + int(noise2(x // 5, 1, 876) * 4) - max(0, (x - 296) // 3)
        for y in range(top, H):
            scree.add((x, y))
            # rough ground: tussocks and loose stones, thickest against the face's end and
            # thinning out to plain turf at the ridge's seam and the Woodland's (no cut edge)
            fade = max(0.0, min(1.0, (W - 4 - x) / 30, (H - 2 - y) / 24))
            v = noise2(x // 2, y // 2, 876)
            if v > 1 - 0.16 * fade * (1.3 if x < HOLLOW_NOTCH + 24 else 1.0):
                cv.set(x, y, ST[3] if (x // 2 + y // 2) % 2 else ST[2])
                if y + 1 < H:
                    cv.set(x, y + 1, ST[1])
            elif smooth_noise(x, y, 5, 879) > 0.66 + (1 - fade) * 0.3:
                cv.set(x, y, ALPINE[1] if (x + y) % 3 else ALPINE[2])     # tussocks
            elif noise2(x, y, 878) > 0.9:
                cv.set(x, y, ALPINE[4])
    # ---- the footbridges: the way in over the stream, the spur over it to the lookout
    deck = foot_bridge(cv, 234, 337, 28, 22, vertical=False)
    deck |= foot_bridge(cv, 133, 434, 22, 30, vertical=True)
    open_cells = {(x // 4, y // 4) for (x, y) in deck if 136 <= x < 152 or 340 <= y < 356}
    blocked = set(t.blocked) | rocks
    blocked |= {(x, y) for x in range(W) for y in range(HOLLOW_RIM, H)}   # the face and below
    blocked |= scree
    blocked = {(x, y) for (x, y) in blocked if (x // 4, y // 4) not in open_cells}
    # the water the renderer animates (water_flow.py): the stream, the fall and the pool;
    # the stream's long run west to the notch flows west
    water_px = water
    WATER_MASKS['hollow'] = water_px
    FLOW_WEST['hollow'] = {(x, y) for (x, y) in water_px if 436 <= y < 460 and x < 240}
    # ---- the firs: clumps of three to seven, crowns overlapping, two or three deep along
    # the west edge and the rim, thinning and snowier up the slope, saplings and stumps
    sm = Z.sprites()
    stands = {'ridge': (316, 348), 'lake': (172, 6), 'clearing': (160, 404), 'falls': (128, 488)}
    keep_clear = set(trail) | set(lookout) | set(clearing) | set(blocked) | deck
    for (sx, sy) in stands.values():
        keep_clear |= {(sx + dx, sy + dy) for dx in range(-14, 15) for dy in range(-12, 8)}
    keep_clear |= {(x, y) for x in range(136, 164) for y in range(100, 128)}   # the trail post
    keep_clear |= {(x, y) for x in range(190, 236) for y in range(36, 58)}     # the ibex's rock
    objects = []
    feet = []

    def fits(key, fx, fy):
        sp = sm[key]
        foot = 10 if key == 'pine' else 6
        x0, x1 = fx - sp.w // 2 + 3, fx - sp.w // 2 + sp.w - 3
        if not (0 <= fx < W and 8 <= fy < HOLLOW_RIM - 3):
            return False
        for yy in range(fy - foot - 4, fy + 3):
            for xx in range(x0 - 3, x1 + 3, 2):
                if (xx, yy) in keep_clear:
                    return False
        for (gx_, gy_, w_) in feet:      # trunks apart, crowns may overlap
            if abs(gx_ - fx) < max(9, (w_ + sp.w) // 5) and abs(gy_ - fy) < 9:
                return False
        return True

    def plant(i, key, fx, fy):
        sp = sm[key]
        objects.append((f'fir-{i}', key, fx - sp.w // 2 - sp.ox, fy - sp.h - sp.oy))
        feet.append((fx, fy, sp.w))

    def kind_at(fx, fy, size):
        snowy = cover(fx + ox, fy + oy) or fy < 210
        base = {'old': 'fir_old', 'mid': 'pine', 'young': 'fir_young', 'sap': 'fir_sapling'}[size]
        if snowy:
            return {'pine': 'snowy_pine'}.get(base, base + '_snow')
        return base

    # (centre x, foot y, spread x, spread y, sizes): sizes from the back of the clump
    clumps = [
        (22, 120, 18, 26, 'old mid sap'), (300, 150, 16, 22, 'mid young sap'), (212, 104, 10, 10, 'young'),
        (52, 222, 16, 14, 'mid young'), (206, 214, 16, 12, 'young sap'),
        (24, 300, 22, 26, 'old young mid old sap'), (210, 300, 22, 22, 'old young mid sap'),
        (296, 268, 20, 40, 'old mid young sap'), (28, 392, 24, 30, 'old young old mid young sap'),
        (220, 410, 20, 16, 'old mid young'), (292, 440, 22, 40, 'mid old young mid sap'),
        (36, 474, 30, 18, 'old mid young mid sap'), (204, 486, 44, 14, 'old mid young old mid sap'),
        (84, 360, 10, 10, 'sap'), (64, 150, 10, 10, 'sap'), (268, 220, 8, 8, 'sap'),
        (214, 172, 10, 10, 'young sap'), (78, 196, 10, 14, 'old sap'), (128, 300, 6, 6, 'young'),
        (60, 274, 10, 10, 'young'), (290, 360, 14, 10, 'young sap'), (8, 440, 6, 20, 'young mid'),
    ]
    n = 0
    for ci, (cx, cy, rx, ry, sizes) in enumerate(clumps):
        for k, size in enumerate(sizes.split()):
            for attempt in range(10):
                fx = int(cx + (noise2(ci * 13 + k, attempt, 901) - 0.5) * 2 * rx)
                fy = int(cy + (noise2(ci * 13 + k, attempt, 902) - 0.5) * 2 * ry)
                key = kind_at(fx, fy, size)
                if fits(key, fx, fy):
                    plant(n, key, fx, fy)
                    n += 1
                    break
    # stumps and a fallen trunk among them; the clearing's log, stump and toadstools
    extras = [('stump-1', 'stump', 60, 432), ('stump-2', 'stump', 222, 244), ('stump-3', 'stump', 18, 200),
              ('log', 'mossy_log', 74, 404), ('stump', 'stump', 190, 416), ('mush', 'mushroom_ring', 192, 366),
              ('fern-1', 'fern', 64, 448), ('fern-2', 'fern', 176, 470), ('post', 'trail_post', 136, 88),
              ('ibex', 'ibex', 192, 14), ('stone-1', 'stone', 40, 104), ('cotton', 'cotton_grass', 44, 482),
              ('stone-2', 'stone', 160, 484), ('stone-3', 'stone', 4, 486),
              ('boulder-1', 'boulder', 244, 505), ('stone-4', 'stone', 282, 517), ('stone-5', 'stone', 300, 506)]
    # (nothing lower than y 530: the Woodland's trees rise over the hollow's last 44 px,
    # zones.check_overhangs)
    walkway = set(trail) | set(lookout) | deck
    for (oid, key, x, y) in extras:
        sp = sm[key]
        fx, fy = x + sp.ox + sp.w // 2, y + sp.oy + sp.h
        if not any((fx + dx, fy - dy) in walkway for dx in range(-sp.w // 2, sp.w // 2 + 1, 2) for dy in (0, 3, 6)):
            objects.append((oid, key, x, y))
    return cv, objects, stands, blocked


def snowmelt(frame: int = 0):
    """Snowmelt Lake (tier 4): the cirque the old glacier left. Cliffs ring it north and
    west with a frozen fall down their face; the lake fills the bowl, dark open water
    within an ice rim. The trail climbs from the hollow by a wide switchback through the
    scarp, follows the south shore and crosses the outflow on a footbridge to the Snow
    Saddle. The outflow runs on south and drops through the scarp to the hollow."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    WTR = MATERIALS['water']
    ox, oy = origin('snowmelt')
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, snow_px(x + ox, y + oy, 821))
    # the cirque wall: cliffs across the top and down the west side (steep ground)
    def wall_y(x):
        return 96 + int(math.sin((x + ox) / 31) * 12 + smooth_noise(x + ox, 0, 14, 822) * 10)
    def wall_x(y):
        return 26 + int(smooth_noise(0, y + oy, 30, 823) * 14)
    steep = set()
    for y in range(H):
        for x in range(W):
            if y < wall_y(x) or (x < wall_x(y) and y < 520):
                cv.set(x, y, steep_px(x + ox, y + oy))
                steep.add((x, y))
    for x in range(W):  # the cliff's foot: a face of stratified rock under the wall
        wy = wall_y(x)
        for k in range(12):
            y = wy + k
            c = ST[2] if (k + int(noise2(x // 6, 2, 827) * 3)) // 4 % 2 else ST[3]
            if k > 9:
                c = ST[1]
            cv.set(x, y, c)
            steep.add((x, y))
    # the frozen fall down the north wall into the lake
    for y in range(10, wall_y(112) + 12):
        for x in range(104, 120):
            if abs(x - 112 - math.sin(y / 9) * 2) < 5:
                cv.set(x, y, ICE[3] if x < 111 else ICE[2] if (y // 3) % 2 else ICE[1])
    # the lake
    def shore(x, y):
        return math.hypot((x - 156) / 106, (y - 186) / 66) - (smooth_noise(x + ox, y + oy, 24, 829) - 0.5) * 0.2
    lake = {(x, y) for x in range(W) for y in range(H) if shore(x, y) < 1} - steep
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
            if (x, y) not in lake and (x, y) not in steep and shore(x, y) < 1.07:
                cv.set(x, y, ST[3] if (x + y) % 3 else ST[2])  # the stony shore
    for (fx, fy) in [(88, 200), (220, 160), (190, 224)]:
        for (x, y) in oval(fx, fy, 9, 4):
            if (x, y) in lake:
                cv.set(x, y, ICE[3] if y < fy else ICE[2])
    # the outflow: out of the lake's south-east, south to the scarp and over it
    outflow = gthick('snowmelt', [(226 + ox, 236 + oy), (244 + ox, 292 + oy), (252 + ox, 380 + oy),
                                  (244 + ox, 470 + oy), (250 + ox, 586 + oy)], 5)
    outflow -= lake
    water(cv, outflow, ox, oy)
    # the scarp at the bottom: the step down to the hollow's tier, open at the switchback
    def scarp_top(x):  # the step down to the hollow, rising toward the cirque's west wall
        return 520 - int((W - x) * 0.2) + int(smooth_noise(x + ox, 3, 14, 876) * 6)
    scarp = set()
    for x in range(W):
        if HOLLOW_COL[0] - 2 <= x < HOLLOW_COL[1] + 2:
            continue
        for y in range(scarp_top(x), min(H, scarp_top(x) + 28)):
            k = y - scarp_top(x)
            c = SN[3] if k == 0 else SN[1] if k == 1 else ST[3] if (k // 4 + x // 9) % 2 else ST[2]
            if k > 24:
                c = ST[1]
            if (x, y) in outflow:
                c = WTR[4] if (x + y) % 3 == 0 else WTR[3]
            cv.set(x, y, c)
            if (x, y) not in outflow:
                scarp.add((x, y))
    # the trail: up the switchback from the hollow, round the south shore, over the bridge
    # (the first point lies past the seam, so the trail meets the hollow's track with no gap)
    trail = gthick('snowmelt', [(-148, -566), (-148, -616), (-196, -664), (-134, -716), (-170, -760),
                                (-150, -828), (-100, -864), (-60, -872), (10, -876)], 8)
    for (x, y) in trail:
        if (x, y) not in outflow and (x, y) not in lake:
            # coming down through the scarp the snow thins off the trail: packed snow
            # gives way to the hollow's earth track over the last 80 px, in patches
            # (review 19 Oct, 7: the surface changed at the seam)
            t = (y - 496) / 80
            if smooth_noise(x + ox, y + oy, 9, 878) < t:
                cv.set(x, y, P[3] if smooth_noise(x + ox, y + oy, 7, 874) < 0.7 else P[4])
            else:
                cv.set(x, y, SN[1] if (x + y) % 3 else SN[2])
    cross = trail & outflow
    bx0 = min(x for (x, _y) in cross) - 6
    bx1 = max(x for (x, _y) in cross) + 7
    by0 = min(y for (_x, y) in cross) - 3
    by1 = max(y for (_x, y) in cross) + 4
    deck = foot_bridge(cv, bx0, by0, bx1 - bx0, by1 - by0, vertical=False)
    walk = {(x, y) for x in range(W) for y in range(H)} - steep - lake - outflow - scarp
    lip(cv, walk, steep | scarp, ox, oy)
    objects = [
        ('pine-1', 'snowy_pine', 40, 440), ('pine-2', 'snowy_pine', 276, 420), ('pine-3', 'snowy_pine', 96, 476),
        ('pine-4', 'snowy_pine', 200, 470), ('cairn', 'cairn', 124, 300), ('post', 'trail_post', 196, 332),
        ('boulder-1', 'boulder', 52, 300), ('stone-1', 'stone', 280, 340), ('ibex', 'ibex', 250, 40),
        ('boulder-2', 'boulder', 40, 520), ('scree', 'scree_small', 286, 500),
    ]
    stands = {'hollow': (172, H - 6), 'shore': (170, 300), 'saddle': (316, 276), 'outflow': (214, 290)}
    return cv, objects, stands, (steep | lake | outflow | scarp) - deck


def saddle(frame: int = 0):
    """The Snow Saddle (tier 4): a broad, treeless shoulder of snow between two peaks,
    where the wind never quite stops (a windsock shows which way). A stone bothy
    shelters by the fork. From the lake the shore path comes in on the west; a long
    switchback goes down through the rock shoulders to the Ridge cabin, and a short
    path climbs north to the High Lookout. Cairns mark the way in a whiteout."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    ox, oy = origin('saddle')
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, snow_px(x + ox, y + oy, 831))
    steep = set()
    for y in range(H):
        e0 = 262 - int(math.sin((y + oy) / 70) * 16 + smooth_noise(0, y + oy, 20, 832) * 10)
        open_west = LAKE_PORT[0] - 30 <= y < LAKE_PORT[1] + 20
        w1 = 0 if open_west else 34 + int(math.sin((y + oy) / 53) * 12 + smooth_noise(1, y + oy, 20, 833) * 8)
        # the west rock is two ribs coming down off the cirque wall, not a slab on the
        # seam: below the lake's wall the snow runs on from the lake's side, and each rib
        # ends in a tapering toe (review 19 Oct, 6)
        wall = 96 + int(math.sin((ox - 1) / 31) * 12 + smooth_noise(ox - 1, 0, 14, 822) * 10)
        if y < wall:
            x0 = 0
        elif y < LAKE_PORT[0] - 30:
            t = (y - wall) / max(1, LAKE_PORT[0] - 30 - wall)
            x0 = int(4 + 24 * t ** 0.8 + smooth_noise(2, y + oy, 12, 836) * 6)
            w1 = int(w1 * (1 - 0.75 * t ** 1.6))
        elif y >= LAKE_PORT[1] + 20:
            t = min(1.0, (y - LAKE_PORT[1] - 20) / 70)
            x0 = int(10 + 18 * (1 - t) + smooth_noise(3, y + oy, 12, 837) * 6) if y < 516 else 0
            w1 = int(w1 * (0.35 + 0.65 * t ** 0.7))
        else:
            x0 = 0
        for x in range(W):
            north = y < 70 - int(smooth_noise(x + ox, 0, 16, 834) * 14) and not (SUMMIT_COL[0] - 6 <= x < SUMMIT_COL[1] + 6)
            if x >= e0 or x0 <= x < w1 or north:
                cv.set(x, y, steep_px(x + ox, y + oy))
                steep.add((x, y))
    shoulder = shoulders(cv, 'saddle')
    # the paths: up from the ridge (the switchback), the fork, west to the lake, north
    up = gthick('saddle', [(204, -566), (204, -612), (176, -646), (226, -684), (186, -722)], 8)
    west = gthick('saddle', [(186, -722), (124, -772), (60, -838), (-10, -876)], 8)
    north = gthick('saddle', [(186, -722), (170, -822), (150, -932), (144, -1042), (144, -1162)], 8)
    trail = (up | west | north) - steep
    for (x, y) in trail:
        cv.set(x, y, SN[1] if (x + y) % 3 else SN[2])
        if noise2(x + ox, y + oy, 835) > 0.94:
            cv.set(x, y, SN[0])
    walk = {(x, y) for x in range(W) for y in range(H)} - steep - shoulder
    lip(cv, walk, steep | shoulder, ox, oy)
    objects = [
        ('bothy', 'bothy', 206, 330), ('windsock', 'windsock', 40, 420), ('post', 'trail_post', 140, 420),
        ('cairn-1', 'cairn', 226, 470), ('cairn-2', 'cairn', 110, 300), ('cairn-3', 'cairn', 176, 140),
        ('ibex', 'ibex', 240, 200), ('stone-1', 'stone', 80, 470), ('boulder-1', 'boulder', 216, 260),
    ]
    stands = {'ridge': (204, H - 6), 'fork': (186, 436), 'bothy': (247, 414), 'lake': (4, 276), 'lookout': (144, 6)}
    return cv, objects, stands, steep | shoulder


def summit(frame: int = 0):
    """The High Lookout (tier 5): a short broad path up from the saddle ends on a flagged
    terrace behind a low stone windbreak, with a bench and a brass viewing scope that
    looks out over everything walked so far. The peaks beyond are scenery; nothing goes
    on from here."""
    SN, ST, ASH = MATERIALS['snow'], MATERIALS['stone'], MATERIALS['ashlar']
    ox, oy = origin('summit')
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cv.set(x, y, steep_px(x + ox, y + oy))
    # the walkable ground: a snowy apron up from the saddle's gap to the terrace
    def apron(x, y):
        if y >= 440:
            half = 44 + (y - 440) * 0.02
            return abs(x - 144 - math.sin(y / 40) * 8) < half
        return ((x - 152) / 112) ** 2 + ((y - 384) / 62) ** 2 < 1 + (smooth_noise(x + ox, y + oy, 18, 847) - 0.5) * 0.3
    walk = {(x, y) for x in range(W) for y in range(H) if apron(x, y)}
    for (x, y) in walk:
        cv.set(x, y, snow_px(x + ox, y + oy, 841))
    # the terrace: flagstones, lit on their upper-left edges
    terrace = {(x, y) for (x, y) in oval(152, 372, 82, 34)}
    for (x, y) in terrace:
        row = y // 6
        c = ASH[3] if noise2((x + row * 3) // 9, row, 848) > 0.45 else ASH[2]
        if y % 6 == 0 or (x + row * 3) % 9 == 0:
            c = ASH[1]
        if (x, y - 1) not in terrace or (x - 1, y) not in terrace:
            c = ASH[4]
        cv.set(x, y, c)
    trail = gthick('summit', [(144, -1142), (144, -1190), (130, -1240), (150, -1290), (152, -1340)], 8) & walk
    for (x, y) in trail:
        if (x, y) not in terrace:
            cv.set(x, y, SN[1] if (x + y) % 3 else SN[2])
    steep = {(x, y) for x in range(W) for y in range(H)} - walk
    lip(cv, walk, steep, ox, oy)
    objects = [
        ('wall-1', 'drystone_wall', 88, 322), ('wall-2', 'drystone_wall', 152, 318),
        ('scope', 'telescope', 150, 340), ('bench', 'forest_bench', 196, 372), ('cairn', 'cairn', 84, 360),
        ('post', 'trail_post', 172, 470), ('stone-1', 'stone', 100, 520),
    ]
    stands = {'saddle': (144, H - 6), 'scope': (162, 388), 'bench': (214, 402)}
    return cv, objects, stands, steep

"""The Frostline Highlands: Fir Hollow, Snowmelt Lake, the Snow Saddle and the High Lookout.

Split out of zones.py (18 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import math  # noqa: F401

import numpy as np

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401
import ground

__all__ = ['RIDGE_COL', 'HOLLOW_COL', 'LAKE_PORT', 'SUMMIT_COL', 'HOLLOW_PORT', 'FACE_H', 'FALLS_X', 'SHOULDER', 'ICE', 'origin', 'snow_px', 'high_slope_px', 'high_band', 'snow_trail', 'peak_row', 'steep_px', 'lip', 'gthick', 'cover', 'turf_or_snow', 'water', 'foot_bridge', 'shoulders', 'hollow', 'snowmelt', 'saddle', 'summit', 'high_country', 'lookout_massif']


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


def _ridge_rim(x: int) -> int:
    """The Ridge's terrace edge (valley_zones.ridge's rim), in the Ridge's own x."""
    return 210 + int(math.sin(x / 27) * 5 + math.sin(x / 61 + 0.4) * 9 + noise2(x // 6, 0, 442) * 6)


def _ridge_face_h(x: int) -> int:
    """The Ridge's terrace face's height (valley_zones.ridge's face_h), 0 at its west edge."""
    t = min(1.0, max(0.0, (x - 10) / 44))
    return int((FACE_H - 1) * (t * t * (3 - 2 * t)))


SEAM_BLEND = 96   # px over which Fir Hollow's snow patches give way to the Ridge's snow line


def cover(gx: int, gy: int) -> bool:
    """Does snow lie here? One mask in the valley's coordinates for Fir Hollow and the
    Ridge (world review 20 Oct 15:53, finding 3: the snow line, the green patches and a
    snow patch were cut at the seam): the Hollow's patches, more the higher up the slope;
    the Ridge's terrace under snow down to its rim and the bank where its face dies out,
    the bank's lower edge frayed (valley_zones.ridge paints its snow by that rule, and this
    is the same rule at its pixels); over the last SEAM_BLEND px before the seam the
    Hollow's patches give way to the Ridge's line; everything above the hollow is snow."""
    if gy < -576:
        return True
    a = (-gy) / 576  # 0 at the hollow's foot, 1 at its top
    s_h = (a - 0.38) * 1.7 - smooth_noise(gx, gy, 26, 851)
    if gx < -SEAM_BLEND:
        return s_h > 0
    rox, roy = origin('ridge')
    rx, ry = gx - rox, gy - roy
    r = _ridge_rim(rx)
    bank = r + (FACE_H - 1 - _ridge_face_h(rx))
    s_r = (bank - ry) / 14
    if ry >= r and smooth_noise(rx, ry, 5, 449) > 0.82 and ry > bank - 3:
        s_r = min(s_r, -0.01)  # the bank's lower edge frays into the turf
    if gx >= 0:
        return s_r > 0
    w = (gx + SEAM_BLEND) / SEAM_BLEND
    w = w * w * (3 - 2 * w)
    return (1 - w) * s_h + w * s_r > 0


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


STEP_LEDGE = 16       # one course of the Frostline's step (tier 4 down to tier 3)
STEP_LOW = 2          # courses where the step is low: the lake's scarp, the shoulders' west end
LAKE_GAP = (HOLLOW_COL[0] - 320, HOLLOW_COL[1] - 320)  # the scarp's opening for the switchback (gx)


def step_rim(gx: int) -> int:
    """The top of the Frostline's step from tier 4 down to tier 3, in the valley's
    coordinates, one line across the Snowmelt and the Saddle (world review 20 Oct 07:53,
    finding 3: the lake's low scarp and the saddle's tall face met on the seam at
    different heights). Under the lake it falls toward the cirque's west wall; past the
    seam it climbs over 90 px to the shoulders' own line, which rises toward the peak."""
    lake = -632 - int(max(0, -gx) * 0.2) + int(smooth_noise(gx, 3, 14, 876) * 6)
    if gx < 0:
        return lake
    shoulder = SHOULDER[0] + int(gx * 0.1) - 16 + int(smooth_noise(gx, 0, 22, 861) * 8)
    t = min(1.0, gx / 90)
    t = t * t * (3 - 2 * t)
    return int(round(lake * (1 - t) + shoulder * t))


def _ledge_end(k: int) -> int:
    """Where course k of the shoulders begins (gx): the two top courses run on as the
    lake's scarp; each lower one starts further east, so the face steps up course by
    course from the scarp's height to the shoulders' instead of meeting it in a cut."""
    return -10 ** 6 if k < STEP_LOW else 6 + (k - STEP_LOW) * 13 + int(noise2(k, 0, 869) * 7)


def shoulders(cv: Canvas, zone: str, skip=frozenset()) -> set:
    """The Frostline's step from tier 4 down to tier 3, one band in the valley's
    coordinates across the Snowmelt, the Snow Saddle and the Ridge cabin's terrace:
    ledges of blocky rock, each with snow drifted on it, stepping down. Under the lake it
    is a low scarp of two courses, open where the switchback climbs from the hollow
    (HOLLOW_COL); past the seam the same two courses run on and the shoulders' lower
    courses begin one by one, each with a lit west end and snow on its corner, until the
    face is the shoulders' full height, open where the switchback comes down (RIDGE_COL).
    `skip` is water that goes over the step (drawn by the caller). Returns the blocked
    pixels in this zone."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    ox, oy = origin(zone)
    blocked = set()
    STEP = STEP_LEDGE
    for x in range(W):
        gx = x + ox
        top = step_rim(gx)
        if gx < 0:
            bottom = top + STEP * STEP_LOW + 6
        else:
            bottom = SHOULDER[1] - 4 + int(gx * 0.1) - 16 + int(smooth_noise(gx, 9, 18, 862) * 8)
        lake_side = gx < 0
        for gy in range(max(top, oy), min(bottom, oy + H)):
            y = gy - oy
            if (x, y) in skip:
                continue
            if lake_side:
                g0, g1 = LAKE_GAP[0] - 2, LAKE_GAP[1] + 2
                if g0 <= gx < g1:
                    continue  # the switchback's way up from the hollow (the trail is drawn later)
            else:
                g0 = RIDGE_COL[0] + int(noise2(gy // 7, 1, 863) * 3)
                g1 = RIDGE_COL[1] - int(noise2(gy // 7, 2, 863) * 3)
                if g0 <= gx < g1:
                    cv.set(x, y, snow_px(gx, gy, 864))
                    continue
            # which ledge, and how far down its face: each ledge's edge wanders
            w = int(smooth_noise(gx, 3, 14, 865) * 6)
            k, f = divmod(gy - top + w, STEP)
            end = _ledge_end(k)
            if gx < end or (lake_side and k >= STEP_LOW):
                continue  # this course has not begun yet: the tier below's own ground
            drift = 3 + int(smooth_noise(gx, k, 10, 866) * 4)  # snow on the ledge
            block = (gx + k * 7 + int(smooth_noise(gx, k, 30, 867) * 10)) // 15  # the blocks
            joint = (gx + k * 7 + int(smooth_noise(gx, k, 30, 867) * 10)) % 15 == 0
            into = gx - end  # how far along the course from its west end
            if f < drift:
                c = SN[3] if f == 0 or (gx + f) % 3 else SN[2]
                if into < 2 and f == drift - 1:
                    c = SN[2]  # the drift rounds over the course's corner
            elif f < STEP - 3:
                c = ST[3] if noise2(block, k, 868) > 0.4 else ST[2]
                if joint:
                    c = ST[1]
                if f == drift:
                    c = ST[4] if not joint else ST[2]  # the lit lip under the snow
                if into < 3:
                    c = ST[4] if into == 0 else ST[3]  # the course's west end, facing the light
            else:
                c = ST[1] if f < STEP - 1 else ST[0]  # the shade under the ledge
                if into < 2:
                    c = ST[2]
            near = min(abs(gx - g0), abs(gx - g1 + 1))
            if near < 2:
                c = ST[3] if gx < g0 else ST[1]  # the gully's walls, lit on the west
            cv.set(x, y, c)
            blocked.add((x, y))
    return blocked


def hollow(frame: int = 0):
    """Fir Hollow (tier 3), west of the ridge's alpine meadow: a sheltered bowl of old
    firs on alpine turf, snow lying in patches that grow up the slope. The way in from
    the ridge crosses the lake's outflow on a footbridge into a quiet clearing; from
    there a wide switchback climbs north through thinning trees to the lake. At the
    bottom the escarpment above the Woodland closes the hollow, and the stream goes
    over it in a fall (no way down: the Ridge is the way up)."""
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    ox, oy = origin('hollow')
    cv = Canvas(W, H)
    turf_or_snow(cv, 'hollow', frame)
    # the escarpment's rim along the bottom, then its face falling away to the woodland
    # (it wanders off the seam, and toward the Ridge it dies out as a scree slope rather
    # than ending in a cut at the zone's edge: review 15:54)
    def rim(x):
        base = 512 + int(smooth_noise(x + ox, 0, 22, 871) * 26)
        t = max(0.0, (x - 200) / 112)
        return min(H, base + int(t * t * (H - base + 4)))
    scarp = set()
    for x in range(W):
        r = rim(x)
        # the slope is too steep and loose to walk wherever the old face stood: no way
        # down to the woodland or round onto the ridge here (the Ridge is the way up)
        steep_top = min(r, 524 + int(smooth_noise(x + ox, 0, 16, 871) * 10))
        if x > 262:  # (the scree slope thins out toward the Ridge, so the seam meets turf)
            steep_top = max(steep_top, 524 + int(((x - 262) / 52) ** 0.7 * (H - 524)))
        if x > 262:  # (the toe's last stones: the border with the Woodland stays closed)
            for y in range(H - 6, H):
                scarp.add((x, y))
                if noise2(x, y, 876) > 0.55 + (x - 262) / 120:
                    cv.set(x, y, '#5A5A68' if noise2(x, y, 877) > 0.5 else '#464656')
        for y in range(steep_top, r):
            scarp.add((x, y))
            if noise2(x, y, 876) > 0.62:  # scree: loose stones over the turf, more lower down
                cv.set(x, y, ST[3] if noise2(x, y, 877) > 0.5 else ST[2])
            elif noise2(x // 2, y // 2, 878) > 0.8:
                cv.set(x, y, ST[4])
        # the face's toe stands on the talus it has shed, above the seam, so the cliff
        # meets the Woodland's band of scree on ground (review 15:53: it ran to the edge)
        toe = H - 9 - int(smooth_noise(x + ox, 0, 17, 879) * 7)
        for y in range(r, H):
            k = y - r
            if y >= toe:
                # scree in drifts with bare earth and moss between, in the cliff's shade: the
                # Woodland's band of talus begins here (valley_zones.woodland), in its tones
                # (a shade warmer than its blue-greys, so the lint reads stone, not water)
                n = noise2((x + ox) // 2, (y + oy) // 2, 1612)
                m = noise2((x + ox) // 2, y + oy, 1613)
                c = '#5A5A68' if m > 0.62 else '#464656'
                if n < 0.12:
                    c = '#3E2B20' if m > 0.5 else '#302019'   # bare earth
                elif n < 0.22:
                    c = '#2F472E'                             # moss
                elif n < 0.36:
                    c = '#2F313F'                             # the dark between the stones
                if y == toe:
                    c = ST[1]  # the face's foot in shade
                cv.set(x, y, c)
                scarp.add((x, y))
                continue
            c = ST[3] if (k + int(noise2(x // 6, 1, 872) * 3)) // 5 % 2 else ST[2]
            if k < 2:
                c = ST[4] if k == 0 else ST[3]
            elif k > 30:
                c = ST[1] if (x + y) % 3 else '#2A3A30'  # the face's foot in its own shade
            if noise2(x // 3, y // 3, 873) > 0.8 and k < 30:
                c = ALPINE[1]  # moss and fern in the face's cracks
            cv.set(x, y, c)
            scarp.add((x, y))
    # the stream from the lake: down the slope, under the footbridge, over the edge
    stream_pts = [(250 + ox, -10 + oy), (246 + ox, 80 + oy), (262 + ox, 170 + oy), (270 + ox, 262 + oy),
                  (248 + ox, 340 + oy), (226 + ox, 410 + oy), (176 + ox, 470 + oy), (118 + ox, 494 + oy),
                  (FALLS_X + ox, 528 + oy)]
    stream = gthick('hollow', stream_pts, 5)
    water(cv, stream, ox, oy, frozen_rim=False)
    falls = {(x, y) for x in range(FALLS_X - 6, FALLS_X + 7) for y in range(rim(FALLS_X) - 2, H)}
    WTR = MATERIALS['water']
    for (x, y) in falls:
        cv.set(x, y, WTR[4] if (x * 3 + y // 2) % 5 == 0 else WTR[3] if x < FALLS_X else WTR[2])
    # the way in from the ridge, over the footbridge to the clearing, and the switchback
    # up to the lake
    way_in = gthick('hollow', [(10, -228), (-70, -226), (-120, -216), (-160, -196)], 8)
    climb = gthick('hollow', [(-160, -196), (-210, -256), (-234, -326), (-180, -380), (-204, -436),
                              (-152, -488), (-148, -540), (-148, -586)], 8)
    trail = way_in | climb
    # where the way in crosses the stream: a footbridge, deck running east-west
    cross = way_in & stream  # where the way in meets the stream: a footbridge over it
    bx0 = min(x for (x, _y) in cross) - 6
    bx1 = max(x for (x, _y) in cross) + 7
    by0 = min(y for (_x, y) in cross) - 3
    by1 = max(y for (_x, y) in cross) + 4
    # a trodden earth track all the way up, laid as the Ridge lays its path (the shared
    # valley_zones.lay_road: the same earth, pebbles, turf edge and worn verge), so its
    # edge keeps one style across the seam (review 15:53); the snow melts off it first,
    # and where it lies, slush at the track's edges and no worn grass beside it
    import valley_zones
    snowy = {(x, y) for x in range(W) for y in range(H) if cover(x + ox, y + oy)}
    near = {(x + a, y + b) for (x, y) in trail for a in range(-8, 9) for b in range(-8, 9)}
    # (the mask runs on past the east edge, as the Ridge's runs on past its foot, so no turf
    # edge closes the track at the seam)
    past = {(x, y) for (x0, y) in trail if x0 == W - 1 for x in range(W, W + 12)}
    road = valley_zones.lay_road(cv, (trail - stream) | past, seed=79, avoid=stream | scarp | snowy)
    road = {(x, y) for (x, y) in road if 0 <= x < W and 0 <= y < H}
    for (x, y) in near & snowy:
        if (x, y) in road or (x, y) in stream:
            continue
        cv.set(x, y, snow_px(x + ox, y + oy, 852))   # (no turf edge drawn onto the snow)
    for (x, y) in road & snowy:
        if any((x + dx, y + dy) not in road for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cv.set(x, y, SN[1])
    deck = foot_bridge(cv, bx0, by0, bx1 - bx0, by1 - by0, vertical=False)
    # the Ridge's shade under its pines carried on over the seam, fading out (it ended in a
    # straight line on the seam: valley_zones.ridge, the same clumps and noise in its x)
    clumps = [(16, H - 120, 34, 36), (36, H - 46, 64, 52)]
    for y in range(H - 200, H):
        for x in range(W - 56, W):
            if (x, y) in scarp or (x, y) in trail or (x, y) in stream:
                continue
            rx = x - W
            sh = max(1 - math.hypot((rx - cx_) / rx_, (y - cy_) / ry_) for (cx_, cy_, rx_, ry_) in clumps)
            sh += (smooth_noise(rx, y, 8, 449) - 0.5) * 0.5 + max(0, (y - (H - 26)) / 26) * 0.6
            sh -= (1 - (rx + 56) / 56) ** 2 * 1.2
            if sh > 0.12:
                style.darken(cv, x, y)
            if sh > 0.55:
                style.darken(cv, x, y, (0.78, 0.8, 0.84))
    # the clearing, sunlit turf in a ring of firs
    for (x, y) in oval(150, 404, 40, 24):
        if (x, y) not in trail and not cover(x + ox, y + oy):
            cv.set(x, y, ALPINE[3] if smooth_noise(x, y, 10, 875) > 0.45 else ALPINE[2])
    objects = [
        # old firs low down, thinning and snowier up the slope
        ('fir-1', 'pine', 8, 430), ('fir-2', 'pine', 52, 448), ('fir-3', 'pine', 212, 430), ('fir-4', 'pine', 262, 440),
        ('fir-5', 'pine', 20, 330), ('fir-6', 'pine', 196, 270), ('fir-7', 'pine', 92, 358), ('fir-8', 'pine', 262, 420),
        ('fir-9', 'pine', 152, 450), ('fir-10', 'pine', 280, 300), ('fir-11', 'pine', 60, 250),
        ('sfir-1', 'snowy_pine', 10, 160), ('sfir-2', 'snowy_pine', 270, 150), ('sfir-3', 'snowy_pine', 150, 230),
        ('sfir-4', 'snowy_pine', 10, 40), ('sfir-5', 'snowy_pine', 200, 40),
        ('log', 'mossy_log', 116, 392), ('stump', 'stump', 182, 396), ('fern-1', 'fern', 100, 430),
        ('mush', 'mushroom_ring', 132, 420), ('post', 'trail_post', 112, 180), ('ibex', 'ibex', 250, 60),
        ('stone-1', 'stone', 40, 120), ('cotton', 'cotton_grass', 60, 500),
    ]
    stands = {'ridge': (316, 348), 'lake': (172, 6), 'clearing': (150, 412), 'falls': (118, 510)}
    return cv, objects, stands, (scarp | stream | falls) - deck


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
    # the scarp at the bottom: the step down to the hollow's tier, two courses of the one
    # step that runs on as the saddle's shoulders (shoulders), open at the switchback; the
    # outflow goes over it in a fall with a white lip, spray at its foot and a plunge pool
    fx = sorted(x for (x, y) in outflow if y == step_rim(x + ox) - oy + 6)
    fx0, fx1 = (fx[0], fx[-1]) if fx else (244, 254)
    fcx = (fx0 + fx1) / 2
    lip_y = step_rim(int(fcx) + ox) - oy
    foot = lip_y + STEP_LEDGE * STEP_LOW - 2
    prx, pry, pcy = (fx1 - fx0) / 2 + 9, 6.0, foot + 5
    pool = oval(fcx + 1, pcy, prx, pry)
    outflow |= {(x, y) for (x, y) in pool if 0 <= x < W and 0 <= y < H}
    water(cv, outflow, ox, oy)
    scarp = shoulders(cv, 'snowmelt', skip={(x, y) for (x, y) in outflow if lip_y - 1 <= y < foot + 1})
    FOAM = '#EEF5F8'
    for (x, y) in outflow:
        if not (lip_y - 1 <= y < foot + 1):
            continue
        k = y - lip_y
        side = min(x - fx0, fx1 - x)
        if k < 2:
            c = FOAM if k == 0 or (x + y) % 2 else ICE[2]  # the lip, where it tips over
        else:
            # falling water: long streaks down the fall line, darker at the sides
            b = x // 2  # bands two pixels wide, each its own tone, broken by dashes
            t = noise2(b, 0, 879)
            c = FOAM if t > 0.66 else WTR[4] if t > 0.3 else WTR[3]
            if (y + int(noise2(b, 1, 879) * 9)) % 9 < 2:
                c = WTR[4] if c == FOAM else FOAM
            if side <= 0:
                c = WTR[2] if (y // 2) % 2 else WTR[3]
        cv.set(x, y, c)
    for (x, y) in pool:  # the pool: deep in the middle, white where the fall lands
        d = math.hypot((x - fcx - 1) / prx, (y - pcy) / pry)
        if d > 0.84:
            cv.set(x, y, ICE[2] if noise2(x // 2, y, 881) > 0.35 else ICE[1])  # the icy rim
        elif y <= foot + 2 and fx0 - 3 <= x <= fx1 + 3:
            cv.set(x, y, FOAM if (x // 2 + y) % 3 else WTR[4])
        elif y <= foot + 4 and fx0 - 5 <= x <= fx1 + 5 and (x // 2 + y) % 2:
            cv.set(x, y, WTR[4])  # the rings spreading from it
        else:
            cv.set(x, y, WTR[0] if d < 0.42 else WTR[1] if d < 0.68 else WTR[2])
    for i in range(7):  # stones round the pool, snow on their tops
        a = math.pi * (0.1 + 0.8 * i / 6) if i % 2 else math.pi * (1.15 + 0.7 * i / 6)
        sx, sy = int(fcx + 1 + math.cos(a) * (prx + 1)), int(pcy + math.sin(a) * (pry + 1))
        if (sx, sy) not in outflow and noise2(i, 3, 883) > 0.25:
            detail.pebble(cv, sx, sy, ST, big=i % 3 == 0)
            cv.set(sx, sy - 1, SN[3])
    for i in range(10):  # spray thrown up beside the fall's foot
        sx = int(fcx + (noise2(i, 0, 882) - 0.5) * (fx1 - fx0 + 10))
        sy = foot - int(noise2(i, 1, 882) * 5)
        if (sx, sy) in outflow or (sx, sy) in scarp:
            cv.set(sx, sy, FOAM)
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
    # the Lookout's slope comes down to the saddle's north edge in the scenery's high country,
    # as the Summit's own ground is (summit, high_country)
    import scenery as sc
    NGX, NGY = np.meshgrid(np.arange(ox, ox + W), np.arange(oy, oy + 90))
    north_rgb = sc._mountain_rgb(NGX, NGY, sc.valley_fields(NGX, NGY)[0])
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
            # (the east rib too, up where it meets the Lookout's slope; it takes on its own
            # rock below, the change in soft clumps over 28 rows)
            high = north or (x >= e0 and y < 84 and smooth_noise(x + ox, y + oy, 5, 838) < (84 - y) / 28)
            # (by the west edge the Snowmelt's cirque wall comes down to the seam in its own
            # rock: the high country gives way to it over the first 60 px)
            if high and smooth_noise(x + ox, y + oy, 5, 839) >= min(1.0, x / 60):
                high = False
            if high:
                cv.set(x, y, (int(north_rgb[y, x, 0]), int(north_rgb[y, x, 1]), int(north_rgb[y, x, 2]), 255))
                steep.add((x, y))
            elif x >= e0 or x0 <= x < w1 or north:
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


# ---- the High Lookout's massif (world review 20 Oct 15:53, finding 2) ------------------
# The Summit was drip-shaped blobs of rock in hatched snow, with no lit faces and no
# ridgelines. Now it is drawn with scenery.py's tools for mountains: the high country's own
# ground (scenery._mountain_rgb, so the zone's west, east and north edges carry on into the
# scenery to the pixel), and over it one massif in the three-quarter view, as scenery's
# peaks are drawn: a main peak above the lookout with a lower summit on each shoulder, each
# split by its ridgeline into a lit west face and a shaded east face, gullies running down
# the fall line with snow lying in them, a snow cap whose ragged lower edge reaches down the
# gullies (snow only on what faces up), a lit rim along the west skyline. The lookout is a
# ledge cut into the peak's south shoulder: a rock face where it was cut, the flagged
# terrace, a retaining wall along its front with a lit lip. The trail from the Saddle climbs
# the snow slope below to it in two switchbacks, each leg a shelf with a cut bank on its
# uphill side and a lit lip on its downhill one.
MASSIF_FOOT = 344                         # the massif's foot (zone y): the ledge is cut into it
LEDGE_X = (48, 257)                       # the lookout's ledge: its west and east ends (zone x)
LEDGE_BACK, LEDGE_FRONT_Y = 334, 426      # its back (cut into the shoulder) and the front of its curve
LEDGE_FRONT = 10                          # the retaining wall's face, px
CUT_H = 16                                # the rock face where the ledge was cut into the shoulder
SWITCHBACKS = [(144, 590), (144, 558), (218, 526), (92, 480), (152, 440), (152, 420)]


def high_country(cv: Canvas, zone: str, y_to: int = H):
    """The scenery's high country (scenery._mountain_rgb) on a zone's ground in the
    valley's coordinates, rows 0 to y_to: rock lit from the upper left, snow lying where it
    can. Returns nothing; the caller decides what is walkable."""
    import scenery as sc
    ox, oy = origin(zone)
    GX, GY = np.meshgrid(np.arange(ox, ox + W), np.arange(oy, oy + y_to))
    rgb = sc._mountain_rgb(GX, GY, sc.valley_fields(GX, GY)[0])
    for y in range(y_to):
        for x in range(W):
            cv.set(x, y, (int(rgb[y, x, 0]), int(rgb[y, x, 1]), int(rgb[y, x, 2]), 255))


SKYLINE = ((-4, 262), (30, 178), (58, 134), (88, 160), (150, 22), (204, 130), (252, 106), (290, 172), (324, 246))
MASSIF_RIDGES = (((150, 22), (158, 118), (146, 214), (152, 340)),    # the main peak's south spur (the lookout's shoulder)
                 ((58, 134), (44, 230), (14, 340)),                  # the west summit's spur, splaying west
                 ((252, 106), (270, 206), (304, 340)))               # the east summit's spur, splaying east


def _poly_x(pts, y):
    """A ridge's x at rows y (array), nan above its top."""
    ys = np.array([p[1] for p in pts], dtype=float)
    xs = np.array([p[0] for p in pts], dtype=float)
    out = np.interp(y, ys, xs)
    return np.where(y < ys[0], np.nan, out)


def lookout_massif():
    """The massif over the Summit's upper part, zone px: (rgb array MASSIF_FOOT x W x 3,
    body mask). Faceted as a real mountain reads: a skyline through three summits and their
    cols, ridges running down from each summit and col, every face lit or in shade by
    which side of its ridge it lies (west lit, east in shade), the gullies where two faces
    meet, a snow cap down to a ragged line, snow along the lit crests and lying in the
    gullies, rock in beds dipping gently east, a lit rim along the west skyline."""
    import scenery as sc
    SN, ST = MATERIALS['snow'], MATERIALS['stone']
    h = MASSIF_FOOT
    yy, xx = np.mgrid[0:h, 0:W].astype(float)
    seed = 1501
    jag = (sc.vnoise(xx, 0 * yy, 6, seed + 1) - 0.5) * 5 + (sc.vnoise(xx, 0 * yy, 17, seed + 2) - 0.5) * 6
    top = np.interp(xx[0], [p[0] for p in SKYLINE], [p[1] for p in SKYLINE])[None, :] + jag
    foot = MASSIF_FOOT - 14 + 12 * sc.vnoise(xx, 0 * yy, 19, seed + 12)
    body = (yy >= top) & (yy < foot)
    # which ridge each point lies nearest, and how far to its west (< 0) or east (> 0)
    wob = (sc.vnoise(0 * xx, yy, 11, seed + 3) - 0.5) * 6 + (sc.vnoise(0 * xx, yy, 37, seed + 14) - 0.5) * 14
    ds = np.stack([xx - _poly_x(r, yy) - wob for r in MASSIF_RIDGES])
    ad = np.where(np.isnan(ds), 1e9, np.abs(ds))
    order = np.argsort(ad, axis=0)
    near = np.take_along_axis(ds, order[:1], axis=0)[0]
    near = np.where(np.isnan(near), xx - 150, near)
    second = np.take_along_axis(ad, order[1:2], axis=0)[0]
    lit = near < 0
    depth = np.abs(near)
    gully = np.abs(second - depth) < 2.2                     # where two faces meet
    # rock: lit faces bright by their crest, shaded faces dark toward their gully
    reach = depth / np.maximum(depth + second, 1.0)     # 0 on the crest .. 0.5 in the gully
    ri = np.where(lit, np.where(reach < 0.08, 4, np.where(reach < 0.3, 3, 2)), np.where(reach < 0.22, 2, 1))
    # buttresses: the rock steps down the faces in tiers, each tier's top a ledge that holds
    # snow, its foot in shade (snow only where the ground faces up)
    tier = (yy + sc.vnoise(xx, 0 * yy, 21, seed + 15) * 14 + np.where(lit, 0, 7)).astype(int) % 30
    ri = np.where(tier >= 27, np.maximum(ri - 1, 0), ri)
    beds = ((yy + xx * 0.14 + sc.vnoise(xx, 0 * yy, 23, seed + 4) * 7).astype(int) % 11 == 0) & \
        (sc.vnoise(xx, yy, 14, seed + 11) > 0.42)
    ri = np.where(beds, np.maximum(ri - 1, 0), ri)
    crack = beds & (sc.vnoise(xx, yy, 5, seed + 5) > 0.62)
    ri = np.where(crack, np.where(lit, 1, 0), ri)
    ri = np.where(gully, 0, ri)
    rgb = sc._pick(ST, ri)
    # snow: a cap down to a ragged line, lower where it runs down a gully, on the lit crests,
    # and lying in the gullies below the cap
    cap = top + 44 + 34 * sc.vnoise(xx, 0 * yy, 9, seed + 6) + np.where(gully, 34, 0)
    sn = yy < cap
    crest = lit & (depth < 3) & (sc.vnoise(xx, yy, 7, seed + 7) > 0.35)
    in_gully = (np.abs(second - depth) < 3.5 + 2.5 * sc.vnoise(xx, yy, 6, seed + 8)) & \
        (sc.vnoise(0 * xx, yy, 40, seed + 9) + sc.vnoise(xx, 0 * yy, 30, seed + 10) * 0.6 > 0.62)
    on_ledge = (tier < 2) & (sc.vnoise(xx, yy, 9, seed + 16) > 0.38) & ~gully
    sn = sn | crest | in_gully | on_ledge
    si = np.where(lit, np.where(depth < 12, 3, 2), np.where(depth < 10, 1, 0))
    si = np.where(in_gully & ~(yy < cap), np.where(lit, 2, 1), si)
    rgb = np.where(sn[..., None], sc._pick(SN, si), rgb)
    # the snow's lower edge throws a blue shade on the rock under it
    under = ~sn & np.roll(sn, 1, axis=0) & body
    rgb = np.where(under[..., None], sc._pick(ST, np.full(xx.shape, 0)), rgb)
    # the skyline: a lit rim on the west slopes, an outline over it all
    rim = body & ~np.roll(body, 1, axis=0) & (np.roll(top, 1, axis=1) > top - 0.5)
    rgb = np.where((rim & lit)[..., None], np.array(sc._rgb('#FFFFFF'), dtype=np.uint8), rgb)
    sky = body & ~(np.roll(body, 1, 0)) & (yy < foot - 30)
    rgb = np.where(sky[..., None], np.array(sc._rgb(sc.OUTLINE), dtype=np.uint8), rgb)
    # the foot: the rock breaks up into talus lying in the snow, stones lit on their upper left
    talus = body & (yy > foot - 18) & (sc.vnoise(xx, yy, 3, seed + 13) < 0.42 + (foot - 18 - yy) / 40)
    body = body & ~talus
    return rgb, body


def _ledge_back(x: int) -> int:
    return LEDGE_BACK + int(round(2 * math.sin(x / 23)))


def _ledge_front(x: int) -> int:
    cx, half = (LEDGE_X[0] + LEDGE_X[1]) / 2, (LEDGE_X[1] - LEDGE_X[0]) / 2
    u = max(0.0, 1 - ((x + 0.5 - cx) / half) ** 2)
    return LEDGE_BACK + 18 + int((LEDGE_FRONT_Y - LEDGE_BACK - 18) * math.sqrt(u))


def summit(frame: int = 0):
    """The High Lookout (tier 5): the trail climbs from the saddle in two switchbacks
    across the snow slope under the massif to a ledge cut into the peak's south shoulder,
    held up by a retaining wall; on it a flagged terrace behind a low stone windbreak, a
    bench and a brass viewing scope that looks out over everything walked so far. The
    peaks beyond are scenery; nothing goes on from here."""
    SN, ST, ASH = MATERIALS['snow'], MATERIALS['stone'], MATERIALS['ashlar']
    ox, oy = origin('summit')
    cv = Canvas(W, H)
    high_country(cv, 'summit')
    rgb, body = lookout_massif()
    for y, x in zip(*np.nonzero(body)):
        cv.set(int(x), int(y), (int(rgb[y, x, 0]), int(rgb[y, x, 1]), int(rgb[y, x, 2]), 255))
    ledge = {(x, y) for x in range(*LEDGE_X) for y in range(_ledge_back(x), _ledge_front(x) + 1)}
    top = {x: _ledge_back(x) for x in range(*LEDGE_X)}
    bot = {x: _ledge_front(x) for x in range(*LEDGE_X)}
    # the face where the ledge was cut into the shoulder: beds of rock under a lit lip,
    # dark at its foot, snow lying along its top; lower toward the ledge's ends
    for x, t in top.items():
        h = CUT_H - int(max(0, min(x - LEDGE_X[0], LEDGE_X[1] - 1 - x) * -1 + 24) * 0.4)
        for k in range(1, h + 1):
            y = t - k
            c = ST[2] if ((y // 3 + (x + (y // 3) * 5) // 9) % 2) else ST[3]
            if y % 3 == 0:
                c = ST[1]  # a bed's joint
            if k == h:
                c = SN[3]   # the snow on its top
            elif k == h - 1:
                c = ST[4]   # its lit lip
            elif k <= 2:
                c = ST[1] if k == 2 else ST[0]  # the shade at its foot
            cv.set(x, y, c)
    # the trail: two switchbacks up the slope, each leg a shelf of packed snow cut into it
    trail = gthick('summit', [(x + ox, y + oy) for (x, y) in SWITCHBACKS], 8) - ledge
    core = set(trail)
    # the trailhead: the way in from the saddle is as wide as the saddle's gully (the port,
    # SUMMIT_COL), narrowing to the trail over its first 26 px
    for y in range(H - 26, H):
        t = (y - (H - 26)) / 25
        half = 8 + t * (SUMMIT_COL[1] - SUMMIT_COL[0] + 8 - 16) / 2
        mid = (SUMMIT_COL[0] + SUMMIT_COL[1]) / 2
        trail |= {(x, y) for x in range(int(mid - half - 1), int(mid + half + 1))}
    for (x, y) in trail:
        if (x, y) not in core:
            cv.set(x, y, snow_px(x + ox, y + oy, 831))   # the saddle's lying snow, carried up to the trail
            continue
        cv.set(x, y, SN[1] if (x + y) % 3 else SN[2])
        if noise2(x + ox, y + oy, 842) > 0.93:
            cv.set(x, y, SN[0])  # boot prints
    for (x, y) in trail:
        if (x, y - 1) not in trail and (x, y - 1) not in ledge:
            for k in (1, 2):   # the cut bank on its uphill side
                q = (x, y - k)
                if q not in trail and q not in ledge and 0 <= q[1]:
                    cv.set(*q, ST[1] if k == 1 else ST[2])
        if (x, y + 1) not in trail and (x, y + 1) not in ledge and y + 1 < H:
            cv.set(x, y, '#FFFFFF' if (x + y) % 3 else SN[3])   # the shelf's lit lip
            style.darken(cv, x, y + 1)                           # and its shadow on the slope below
    # the ledge: packed snow round a flagged terrace, the flags lit on their upper-left edges
    terrace = oval(152, 372, 82, 34)
    for (x, y) in ledge:
        if (x, y) in terrace:
            row = y // 6
            c = ASH[3] if noise2((x + row * 3) // 9, row, 848) > 0.45 else ASH[2]
            if y % 6 == 0 or (x + row * 3) % 9 == 0:
                c = ASH[1]
            if (x, y - 1) not in terrace or (x - 1, y) not in terrace:
                c = ASH[4]
        else:
            c = snow_px(x + ox, y + oy, 841)
        cv.set(x, y, c)
    # the retaining wall along its front: a lit lip, courses of dressed stone, its shadow;
    # the trail comes up through it by four steps
    steps = {x for (x, y) in trail if y > bot.get(x, -9) and y <= bot.get(x, -9) + LEDGE_FRONT + 2}
    for x, b in bot.items():
        cv.set(x, b, ASH[5] if x % 9 else ASH[4])
        for k in range(1, LEDGE_FRONT + 1):
            y = b + k
            if x in steps:
                c = ASH[4] if k % 2 else ASH[2]   # a step's lit tread and its riser
            else:
                course = (k - 1) // 3
                c = ASH[3] if ((x + course * 5) // 8) % 2 else ASH[2]
                if (k - 1) % 3 == 2 or (x + course * 5) % 8 == 0:
                    c = ASH[1]
            cv.set(x, y, c)
        if x not in steps:
            for k in (1, 2):
                style.darken(cv, x, b + LEDGE_FRONT + k)
    walk = ledge | trail | {(x, bot[x] + k) for x in steps if x in bot for k in range(1, LEDGE_FRONT + 1)}
    objects = [
        ('wall-1', 'drystone_wall', 88, 322), ('wall-2', 'drystone_wall', 152, 318),
        ('scope', 'telescope', 150, 340), ('bench', 'forest_bench', 196, 372), ('cairn', 'cairn', 84, 360),
        ('post', 'trail_post', 214, 492), ('stone-1', 'stone', 100, 520),
    ]
    stands = {'saddle': (144, H - 6), 'scope': (162, 388), 'bench': (214, 402)}
    steep = {(x, y) for x in range(W) for y in range(H)} - walk
    return cv, objects, stands, steep


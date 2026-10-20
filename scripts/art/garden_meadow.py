"""The lower garden and the forest above it, drawn at native pixel resolution.

Step 6 of the coherence plan re-laid the garden at the new density: 320 art pixels
wide (about 300 show on a phone). The clearing sits at the top; below it a stream,
the bridge and a meadow; above it a band of forest behind the HUD. The meadow's beds and orchard pits are baked
into the ground; what grows in them is drawn as separate stage sprites so the
app can show the garden growing from the player's breaks.
"""
from __future__ import annotations

import math

from pixel import Canvas, disc, noise2, oval, shade_blob, smooth_noise
from materials import G, P, WTR, SAND, WOOD, STONE, LEAF, NAP, RED, CREAM, GOLD, INK, SOIL

W = 320
H = 576  # full walkable map height (native px)
TOP = 72  # forest band drawn above y = 0, behind the HUD (tall enough for the treeline)
PATH_X = 160  # the main path runs north-south down the middle

STREAM_Y = 300


def stream_centre(x: float) -> float:
    return STREAM_Y + 5 * math.sin(x / 31) + 2.5 * math.sin(x / 12 + 1)


STREAM = set()
for _x in range(-2, W + 2):
    c = stream_centre(_x)
    half = 9 + (smooth_noise(_x, 0, 13, 91) - 0.5) * 2.4
    for _y in range(int(c - half), int(c + half) + 1):
        STREAM.add((_x, _y))
STREAM_BANK = set()
for (_x, _y) in STREAM:
    for _dy in (-2, -1, 1, 2):
        if (_x, _y + _dy) not in STREAM:
            STREAM_BANK.add((_x, _y + _dy))

# The stream has cut into the land: its north bank is a small bluff, a raised tier
# with a shaded earth face (coherence plan, step 6b: depth without tilting the view).
STREAM_TOP = {}
for (_x, _y) in STREAM:
    STREAM_TOP[_x] = min(STREAM_TOP.get(_x, _y), _y)
BLUFF_H = {_x: 7 + int(smooth_noise(_x, 3, 9, 92) * 3) for _x in STREAM_TOP}
BLUFF = {(_x, _y) for _x, _top in STREAM_TOP.items() for _y in range(_top - BLUFF_H[_x], _top)}

# The bridge deck is 44 wide between its rails (the path fits with room either side).
BRIDGE = (PATH_X - 27, int(STREAM_Y - 20), 54, 40)  # x, y, w, h of the flat bridge decal

# Growing beds in the meadow, east of the path. (x, y) is the bed's top-left.
PLOT_W, PLOT_H = 44, 20
PLOTS = [(200, 368), (256, 368), (200, 408), (256, 408), (200, 448), (256, 448)]
PLOT_KINDS = ['tulip', 'chamomile', 'lavender', 'chamomile', 'lavender', 'tulip']
# The beds stand in one kitchen garden: a yard of packed earth that the paths run into.
YARD = (190, 358, 118, 120)  # x, y, w, h
# The orchard: three planting circles in a row west of the path, with a walk along
# their feet. (x, y) is each tree's base (feet) point.
ORCHARD = [(30, 438), (78, 438), (126, 438)]
ORCHARD_WALK_Y = 456

FENCE_Y = 528  # top of the lower fence
GATE_W, GATE_H = 48, 44
GATE_X, GATE_Y = PATH_X - GATE_W // 2, FENCE_Y - 16


def meadow_path(thick_path):
    pts = thick_path([(PATH_X, 280), (PATH_X - 1, 330), (PATH_X + 1, 400), (PATH_X, 470),
                      (PATH_X, 530), (PATH_X, H + 12)], 18.5, 7)
    pts |= thick_path([(PATH_X + 10, 432), (YARD[0] + 4, 432)], 9.5, 8)   # into the kitchen garden
    pts |= thick_path([(PATH_X - 10, ORCHARD_WALK_Y), (-12, ORCHARD_WALK_Y)], 8.5, 9)  # along the orchard, on into the Woodland
    # B10 (Matt, 19 Oct 22:40): the Riverside's west bank walk arrives at x 319 on rows
    # 394-410 (valley_zones riverside, thick((8, 402), 8)); it carries on into the kitchen
    # garden's pad here at the same row and width, square to the edge
    pts |= {(x, y) for x in range(YARD[0] + YARD[2] - 12, W + 12) for y in range(394, 411)}
    yx, yy, yw, yh = YARD
    r = 10
    for y in range(yy, yy + yh):
        for x in range(yx, yx + yw):
            cx = min(max(x, yx + r), yx + yw - 1 - r)
            cy = min(max(y, yy + r), yy + yh - 1 - r)
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                pts.add((x, y))
    return pts


def draw_bluff(cv: Canvas):
    """The north bank's face (Matt's references, 17 Oct): a lit grass lip with turf
    hanging over the edge, then a face of stacked stones, each lit on its left and top
    and dark on its right, in dark joints, wet and darkest at the foot, with foam where
    it meets the water."""
    for x in range(-2, W + 2):
        if x not in STREAM_TOP:
            continue
        h = BLUFF_H[x]
        top = STREAM_TOP[x] - h
        col = (x + int(noise2(x // 6, 1, 95) * 6)) % 6  # the stone's column within its run
        sw = 6
        si = (x + int(noise2(x // 6, 1, 95) * 6)) // sw
        for k in range(h):
            y = top + k
            if not (0 <= x < W):
                continue
            if k == 0:
                c = G[3]
            elif k == 1:
                c = G[2] if (x // 2 + int(noise2(x // 3, 2, 96) * 2)) % 3 else G[1]
            else:
                row = (k - 2 + (si % 2) * 2) // 4  # courses of stone, staggered per column
                r = (k - 2 + (si % 2) * 2) % 4
                base = 3 if noise2(si, row, 97) > 0.45 else 2
                if col == sw - 1 or r == 3:
                    c = STONE[0]  # the joint
                elif col == 0 or r == 0:
                    c = STONE[base + 1]
                elif col == sw - 2:
                    c = STONE[base - 1]
                else:
                    c = STONE[base]
                if k == h - 1:
                    c = STONE[1] if col != sw - 1 else STONE[0]  # wet at the foot
            cv.set(x, y, c)


def draw_stream(cv: Canvas, phase: int):
    for (x, y) in STREAM_BANK:
        if 0 <= x < W and (x, y) not in BLUFF:
            cv.set(x, y, SAND[1] if noise2(x, y, 23) < 0.82 else SAND[2])
    for (x, y) in STREAM_BANK:
        if (x, y - 1) in STREAM and (x, y + 1) not in STREAM:
            cv.set(x, y, SAND[0])  # wet lower lip
    draw_bluff(cv)
    for (x, y) in STREAM:
        if not (0 <= x < W):
            continue
        c = stream_centre(x)
        col = WTR[2] if abs(y - c) < 3 else WTR[1]
        if (x, y - 1) not in STREAM or (x, y - 2) not in STREAM:
            col = WTR[0]  # the bluff's shadow on the water
        elif (x, y - 3) not in STREAM:
            col = WTR[1]
        cv.set(x, y, col)
    for x in range(0, W):  # foam where the water meets the stone face
        if x in STREAM_TOP and (x // 2 + int(noise2(x // 4, 7, 98) * 3)) % 3 and (x, STREAM_TOP[x]) in STREAM:
            cv.set(x, STREAM_TOP[x], WTR[4] if x % 5 else WTR[3])
    # Flowing highlights drift two pixels east per frame along the current.
    for i in range(30):
        bx = int(noise2(i, 4, 77) * W)
        x = (bx + phase * 2) % (W + 8) - 4
        y = int(stream_centre(x) + (noise2(i, 5, 77) - 0.5) * 10)
        length = 4 + (i % 3)
        for s in range(length):
            if (x + s, y) in STREAM and (x + s, y - 1) in STREAM:
                cv.set(x + s, y, WTR[3] if s < length - 1 else WTR[2])
        if i % 5 == 0 and (x + 1, y - 1) in STREAM:
            cv.set(x + 1, y - 1, WTR[4])
    # Stones and reeds where the water meets the meadow.
    for sx in (14, 62, 104, 214, 262, 300):
        y = int(stream_centre(sx)) + 9
        cv.hline(sx, y, 4, STONE[1]); cv.hline(sx + 1, y - 1, 3, STONE[3]); cv.set(sx + 1, y - 2, STONE[4])
    for rx in (8, 40, 86, 120, 204, 246, 292, 312):
        y = int(stream_centre(rx)) + 16
        cv.vline(rx, y - 4, 5, LEAF[1]); cv.vline(rx + 2, y - 3, 4, LEAF[2])
        cv.set(rx - 1, y - 4, LEAF[3]); cv.set(rx + 1, y - 1, LEAF[3])


def planter(cv: Canvas, bx: int, by: int, w: int = PLOT_W, h: int = PLOT_H):
    """A raised timber bed seen from above and in front: a lit rim around dark tilled
    soil (furrows with lit ridges, shaded under the back and left rims), capped corner
    posts, a front face of planks turned away from the light, a dark outline, and its
    shadow on the ground below and to the right."""
    from detail import boards, shade
    import style
    rim, front = 2, 5
    soil_top, soil_bottom = by + rim, by + h - front - rim  # soil rows [soil_top, soil_bottom)
    box = {(x, y) for y in range(by - 1, by + h) for x in range(bx, bx + w)}
    # its shadow first, on whatever ground it stands on
    for (x, y) in {(x + 2, y + 2) for (x, y) in box} - box:
        style.darken(cv, x, y)
    for y in range(soil_top, soil_bottom):
        k = (y - soil_top) % 3
        for x in range(bx + rim, bx + w - rim):
            t = 3 if k == 0 else 2 if k == 1 else 0
            if k == 1 and noise2(x, y, 61) < 0.14:
                t = 3
            elif k == 2 and noise2(x, y, 62) < 0.2:
                t = 1
            cv.set(x, y, SOIL[t])
    for x in range(bx + rim, bx + w - rim):  # the back rim's shadow on the soil
        shade(cv, x, soil_top, 2); shade(cv, x, soil_top + 1, 1)
    for y in range(soil_top, soil_bottom):  # the left rim's shadow
        shade(cv, bx + rim, y, 1)
    # rims seen from above: lit on the left and back, the right a step darker
    for x in range(bx, bx + w):
        cv.set(x, by, WOOD[4] if x < bx + w - rim else WOOD[3]); cv.set(x, by + 1, WOOD[3])
    for y in range(by, soil_bottom):
        cv.set(bx, y, WOOD[4]); cv.set(bx + 1, y, WOOD[3])
        cv.set(bx + w - 2, y, WOOD[2]); cv.set(bx + w - 1, y, WOOD[2])
    for x in range(bx, bx + w):
        cv.set(x, soil_bottom, WOOD[4] if x < bx + w - rim else WOOD[3])
        cv.set(x, soil_bottom + 1, WOOD[3])
    # the front face: planks turned away from the light
    boards(cv, {(x, y) for y in range(soil_bottom + 2, by + h) for x in range(bx, bx + w)},
           WOOD, 1, soil_bottom + 2, board=3, seed=bx + by, grain=0.05)
    for x in range(bx, bx + w):
        cv.set(x, soil_bottom + 2, WOOD[2])
        cv.set(x, by + h - 1, WOOD[0])
    # corner posts, a pixel taller than the rim, capped, rounded by a lit stripe
    for px in (bx, bx + w - 3):
        lit = px == bx
        for y in range(by - 1, by + h):
            cv.set(px, y, WOOD[3] if lit else WOOD[2]); cv.set(px + 1, y, WOOD[4] if lit else WOOD[3])
            cv.set(px + 2, y, WOOD[2] if lit else WOOD[1])
        cv.hline(px, by - 1, 3, WOOD[4] if lit else WOOD[3])
        cv.set(px + 1, by + h - 1, WOOD[1]); cv.set(px + 2, by + h - 1, WOOD[0])
    # a dark outline closes the box against the ground
    for (x, y) in {(x + dx, y + dy) for (x, y) in box for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - box:
        cv.set(x, y, WOOD[0])


def flower_planter(cv: Canvas, bx: int, by: int, bw: int, bh: int, seed: int = 0):
    """A raised planter (see `planter`) planted in two rows of tulips, chamomile and
    lavender, each flower lit on its upper left."""
    from materials import PLASTER
    planter(cv, bx, by, bw, bh)
    for row, fy in enumerate((by + 6, by + bh - 7)):
        for k, fx in enumerate(range(bx + 5 + 3 * row, bx + bw - 4, 6)):
            kind = (k + row + seed) % 3
            cv.vline(fx, fy - 2, 3, LEAF[2]); cv.set(fx - 1, fy, LEAF[3]); cv.set(fx + 1, fy - 1, LEAF[1])
            if kind == 0:  # a cupped coral tulip
                cv.hline(fx - 1, fy - 4, 3, RED[3]); cv.hline(fx - 1, fy - 3, 3, RED[2])
                cv.set(fx - 1, fy - 5, RED[4]); cv.set(fx + 1, fy - 5, RED[3]); cv.set(fx - 1, fy - 4, RED[4])
            elif kind == 1:  # chamomile: cream rays around a warm centre
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    cv.set(fx + dx, fy - 4 + dy, PLASTER[5] if dy < 0 or dx < 0 else PLASTER[3])
                cv.set(fx, fy - 4, GOLD[3])
            else:  # a lavender spike, paler at the crown
                cv.vline(fx, fy - 6, 4, NAP[2]); cv.set(fx, fy - 6, NAP[4]); cv.set(fx - 1, fy - 5, NAP[3])
                cv.set(fx + 1, fy - 4, NAP[2]); cv.set(fx - 1, fy - 3, NAP[3])


def planting_circle(cv: Canvas, ox: int, oy: int):
    """Where an orchard tree is planted: a domed mound of mulched soil, lit on its upper
    left, inside a ring of small stones with their own highlights and shadows."""
    cx, cy = ox + 0.5, oy - 2.5
    mound = oval(cx, cy, 8.5, 4.2)
    for (x, y) in mound:
        nx, ny = (x + 0.5 - cx) / 8.5, (y + 0.5 - cy) / 4.2
        lit = -0.55 * nx - 0.8 * ny
        t = 4 if lit > 0.45 else 3 if lit > -0.2 else 2 if lit > -0.6 else 1
        if noise2(x, y, 71) < 0.1:
            t = min(5, t + 1)
        elif noise2(x, y, 72) < 0.08:
            t = max(0, t - 1)
        cv.set(x, y, SOIL[t])
    n = 13
    for k in range(n):
        a = 2 * math.pi * (k + 0.3) / n
        sx = int(round(cx + 11.2 * math.cos(a) - 1))
        sy = int(round(cy + 5.6 * math.sin(a)))
        big = k % 3 == 0
        cv.hline(sx, sy, 3, STONE[3]); cv.set(sx, sy, STONE[4])
        cv.hline(sx, sy + 1, 3, STONE[1]); cv.set(sx + 2, sy, STONE[2])
        if big:
            cv.set(sx + 3, sy, STONE[2]); cv.set(sx + 3, sy + 1, STONE[1])


def draw_beds(cv: Canvas):
    """The kitchen garden's raised beds and the orchard's planting circles."""
    for (bx, by) in PLOTS:
        planter(cv, bx, by)
    for (ox, oy) in ORCHARD:
        planting_circle(cv, ox, oy)


def draw_lower_details(cv: Canvas, path: set):
    """Wildflower drifts and clover patches give the meadow its own texture."""
    for i in range(56):
        x = int(noise2(i, 9, 81) * (W - 8)) + 4
        y = STREAM_Y + 24 + int(noise2(i, 10, 81) * (FENCE_Y - STREAM_Y - 30))
        if (x, y) in path or any(bx - 2 <= x <= bx + PLOT_W + 2 and by - 2 <= y <= by + PLOT_H + 2 for bx, by in PLOTS):
            continue
        if any(abs(x - ox) < 14 and -10 < y - oy < 6 for ox, oy in ORCHARD):
            continue
        col = [CREAM[3], '#F2D16B', NAP[4], RED[4], '#FFFFFF'][i % 5]
        cv.set(x, y, col); cv.set(x + 2, y + 1, col); cv.set(x + 1, y + 2, col)
        cv.set(x + 1, y + 1, '#E8A33D')
    for i in range(16):
        x = int(noise2(i, 11, 82) * (W - 20)) + 10
        y = 240 + int(noise2(i, 12, 82) * 300)
        if (x, y) in path:
            continue
        for dx, dy in ((0, 0), (2, 0), (1, -1), (1, 1)):
            cv.set(x + dx, y + dy, G[4])
        cv.set(x + 1, y, G[1])


# The pines along the clearing's top edge (garden.py places them from this table): each
# pine's number and the x, y of its sprite's nominal top-left. Two (7 and 8) stand back to
# let the ridge trail through.
# The pines along the clearing's north edge: spaced and set back unevenly, as trees grow,
# so neither their crowns nor the shadows they throw into the garden line up in a row
# (art-faults.md rules 8 and 12). Indices 7 and 8 stand back for the ridge trail.
# They stand in two clumps where the Snowy Ridge's clumps of pines come down to the seam
# (west of x ~110 and east of x ~220); between them the ridge's meadow runs open to the
# garden, with the trail through it.
_TREE_JITTER = [(-3, 2), (4, -5), (-2, 6), (5, -1), (-4, -6), (2, 4), (-5, 0), (0, 0), (0, 0), (5, -4), (-3, 5), (3, -3), (-2, 3)]
TREELINE = {i: (-14 + i * 26 + _TREE_JITTER[i][0], -60 + (i % 2) * 4 + _TREE_JITTER[i][1])
            for i in range(13) if i not in (5, 6, 7, 8)}
FOREST_FLOOR = ['#1E2A22', '#2C3F30', '#3E5A3C', '#577A44', '#6A9468']


def crown_shade(x: float, y: float) -> float:
    """How deep the forest's shade lies at a point of the garden (y < 0 is the band above
    the clearing, Claude A's review of 19 Oct, finding 2): deep under the forest beyond,
    thinning with dappled sun toward the clearing, and reaching into it in a lobe under
    each pine's crown, offset down and right (light from the upper left), with a ragged
    edge. Never a ruled line: no row or column is the same all along."""
    depth = min(1.0, max(0.0, (-y - 4) / (TOP - 30)))  # the forest beyond deepens upward
    for (px, py) in TREELINE.values():
        cx, cy = px + 22, py + 74  # just below and right of the crown, round the trunk's foot
        d = ((x - cx) / 21) ** 2 + ((y - cy) / 11) ** 2
        if d < 1:
            depth = max(depth, 0.85 * (1 - d) ** 0.6)
    rag = (smooth_noise(x, y, 9, 951) - 0.5) * 0.5 + (noise2(x // 2, y // 2, 952) - 0.5) * 0.18
    return max(0.0, min(1.0, depth + rag))


# The forest floor where the Snowy Ridge comes down to the garden: the shade of the two
# clumps of pines either side of the ridge trail (valley_zones.ridge places them), each
# (x, y, rx, ry) in the ridge's own coordinates, so -H above the garden's top row.
RIDGE_CLUMPS = [(36, -46, 64, 52), (100, -34, 34, 30), (272, -50, 64, 56), (300, -120, 34, 40), (16, -120, 34, 36)]


def forest_edge_shade(x: float, sy: float) -> float:
    """One shade field across the ridge/garden seam (sy < 0 in the ridge, sy = ridge y - H;
    sy >= 0 in the garden): the ridge's clumps of pines, a ragged noise edge, and a
    deepening toward the seam from both sides, so the forest floor runs on across it and
    then gives way to the clearing over twenty-odd rows. For y in the ridge it is exactly
    the field valley_zones.ridge paints its bottom rows from (its noise is read in its own
    rows, H + sy); darken above 0.12, darken again above 0.55."""
    sh = max(1 - math.hypot((x - cx) / rx, (sy - cy) / ry) for (cx, cy, rx, ry) in RIDGE_CLUMPS)
    sh += (smooth_noise(x, H + sy, 8, 449) - 0.5) * 0.5
    if sy < 0:
        return sh + max(0, (26 + sy) / 26) * 0.6
    # in the garden the deepening mirrors the ridge's and the clearing's light wins it back
    return sh + max(0, 1 - (sy + 1) / 26) * 0.6 - max(0, (sy - 10) / 16) * 0.4


def riverside_edge_shade(x: float, y: float) -> float:
    """The forest edge's shade carried round the garden's north-east corner into the
    Riverside's first rows (its x 0 is the garden's x 320), for valley_zones.riverside to
    darken its ground by exactly as garden.bake_shadows does (above 0.12 once, above 0.55
    again): the same field as the garden's, so the two meet at the seam in one tone, then
    thinning out over 60 px east as the trees fall back from the meadow."""
    if y >= 28:
        return 0.0
    return forest_edge_shade(W + x, y) - max(0.0, x / 70) * 0.6


def trail_dapple(x: int, sy: int) -> bool:
    """Sun and shade on the trail where it passes under the trees at the ridge/garden seam:
    the same noise valley_zones.ridge reads for its trail's last rows (in its own rows,
    H + sy), thinning out over the garden's first rows."""
    fade = 1.0 if sy < 0 else max(0.0, 1 - sy / 16)
    return smooth_noise(x, H + sy, 5, 450) > 1 - 0.45 * fade


def draw_top_band(phase: int = 0) -> Canvas:
    """The strip above the clearing (y -TOP..0), drawn as the Snowy Ridge's own last rows
    (Claude A, after #75: the band was a dark wall of trees while the ridge's bottom is open
    meadow with clumps of pines): the garden's turf, darkened exactly as the ridge darkens
    its bottom rows (forest_edge_shade, under the two clumps of pines either side of the
    trail and deepening toward the seam), with the ridge trail running up through it. The
    garden's treeline pines stand only where the ridge's clumps are."""
    import style
    cv = Canvas(W, TOP)
    turf = []
    for y in range(TOP):
        gy = y - TOP
        for x in range(W):
            n = smooth_noise(x, gy, 30, 11)
            light = n > 0.66 or (n > 0.62 and (x + gy) % 2 == 0) or (n > 0.6 and (x + 2 * gy) % 4 == 0)
            c = G[3] if light else G[2]
            if noise2(x // 2, y // 2, 957) > 0.97:
                c = G[4] if noise2(x, y, 958) > 0.5 else G[1]  # a tuft's lit tip, a blade's root
            elif noise2(x, y, 959) > 0.995:
                c = '#E9E4CF'  # a tiny white flower
            cv.set(x, y, c)
            turf.append((x, y))
    # the ridge trail runs up through the meadow as the ridge draws it: from where the
    # garden's path leaves the clearing (x 198-213 at the garden's top row) bending to
    # where the ridge's trail climbs on (x ~198 at the band's top), worn turf teeth along
    # its edges as on the garden's path, sunlit and dappled where the pines' shade reaches
    import detail
    trail = set()
    for y in range(TOP):
        t = y / (TOP - 1)
        cx = 198 + 7.5 * t * t + math.sin(y / 9) * 1.5 * (1 - t)
        hw = 8.5 + (noise2(y // 3, 0, 931) - 0.5) * 2.4
        b = min(1.0, max(0.0, (y - (TOP - 34)) / 20))  # narrowing to the garden path's own width at its top
        hw = hw * (1 - b) + (7.6 + (noise2(y // 3, 0, 931) - 0.5) * 0.8) * b
        for x in range(186, 226):
            if abs(x - cx) <= hw:
                cv.set(x, y, P[4] if noise2(x, y, 933) > 0.86 else P[3])
                trail.add((x, y))
    below = {(x, y) for (x, y) in trail if y == TOP - 1 for y in range(TOP, TOP + 12)}
    above = {(x, y) for (x, y) in trail if y == 0 for y in range(-12, 0)}
    detail.grass_edge(cv, trail | below | above, G, P, seed=7)
    for (x, y) in set(turf) - trail:
        e = forest_edge_shade(x, y - TOP)  # darkened exactly as the ridge and the garden darken theirs
        if e > 0.12:
            style.darken(cv, x, y)
        if e > 0.55:
            style.darken(cv, x, y, (0.78, 0.8, 0.84))
    for (x, y) in trail:  # the trail itself only dappled, as the ridge dapples its own (valley_zones.ridge)
        if trail_dapple(x, y - TOP):
            style.darken(cv, x, y, (0.85, 0.86, 0.9))
    return cv


# ---- sprites --------------------------------------------------------------
def _flower(cv: Canvas, x: int, y: int, kind: str, stage: int):
    """One plant whose stem foot is at (x, y). Stages: 1 sprout .. 4 bloom."""
    if stage <= 0:
        cv.set(x, y, '#3A2416'); cv.set(x + 1, y, WOOD[2]); cv.set(x - 1, y, '#3A2416')
        return
    stem = LEAF[2]
    height = (2, 5, 8, 10)[stage - 1]
    cv.vline(x, y - height + 1, height, stem)
    if stage == 1:
        cv.set(x - 1, y - 1, LEAF[3]); cv.set(x + 1, y - 2, LEAF[4]); cv.set(x - 2, y - 2, LEAF[4])
        return
    # two leaves, lit on top
    cv.hline(x - 3, y - 2, 3, LEAF[2]); cv.set(x - 3, y - 3, LEAF[3]); cv.set(x - 2, y - 3, LEAF[4])
    cv.hline(x + 1, y - 4, 3, LEAF[2]); cv.set(x + 2, y - 5, LEAF[3]); cv.set(x + 3, y - 5, LEAF[4])
    cv.set(x - 1, y, LEAF[1])
    top = y - height
    if stage == 2:
        cv.set(x, top, LEAF[4]); cv.set(x - 1, top + 1, LEAF[3]); cv.set(x + 1, top + 1, LEAF[3])
        return
    if kind == 'tulip':
        petals = (RED[1], RED[2], RED[3], RED[4])
    elif kind == 'chamomile':
        petals = (CREAM[0], CREAM[1], CREAM[2], CREAM[3])
    else:
        petals = (NAP[1], NAP[2], NAP[3], NAP[4])
    if stage == 3:  # a closed bud
        cv.vline(x, top - 1, 2, petals[2]); cv.set(x, top - 2, petals[3]); cv.set(x + 1, top, petals[1])
        cv.set(x - 1, top + 1, LEAF[3])
        return
    if kind == 'tulip':
        cv.hline(x - 2, top, 5, petals[2]); cv.hline(x - 2, top + 1, 5, petals[1])
        cv.set(x - 2, top - 1, petals[3]); cv.set(x, top - 2, petals[3]); cv.set(x + 2, top - 1, petals[2])
        cv.set(x - 1, top - 1, petals[3]); cv.set(x + 1, top - 1, petals[2]); cv.set(x, top - 1, petals[3])
    elif kind == 'chamomile':
        # one solid daisy head: lit upper petals, shaded lower ones, a gold centre
        for (px, py) in disc(x + 0.5, top + 0.5, 2.8):
            cv.set(px, py, petals[3] if py <= top else petals[2])
        cv.rect(x - 1, top - 1, 2, 2, GOLD[3]); cv.set(x - 1, top - 1, GOLD[4])
    else:
        cv.vline(x, top - 5, 6, petals[2])
        for k in range(0, 6, 2):
            cv.set(x - 1, top - 4 + k, petals[3]); cv.set(x + 1, top - 3 + k, petals[1])
        cv.set(x, top - 5, petals[3])


def plot_plants(kind: str, stage: int) -> Canvas:
    """A whole bed's planting at one stage; anchored to the bed's top-left."""
    lift = 14
    cv = Canvas(PLOT_W, PLOT_H + lift)
    for row, ry in enumerate((lift + 6, lift + 11)):
        for col in range(5):
            x = 5 + col * 8 + (3 if row else 0)
            if x > PLOT_W - 7:
                continue
            jitter = int(noise2(col, row, len(kind) + stage) * 2)
            _flower(cv, x, ry + jitter - 1, kind, stage)
    if stage >= 4:
        # a visiting butterfly on a blooming bed
        wing = NAP[4] if kind != 'lavender' else GOLD[3]
        cv.set(PLOT_W - 8, 2, wing); cv.set(PLOT_W - 8, 3, wing)
        cv.set(PLOT_W - 6, 2, wing); cv.set(PLOT_W - 6, 3, wing)
        cv.set(PLOT_W - 7, 3, INK)
    return cv


def orchard_tree(stage: int) -> Canvas:
    """0 seed marker, 1 sapling, 2 young tree, 3 grown tree, 4 fruiting tree."""
    import style
    from garden_props import canopy, plane, rect_set
    if stage == 0:
        cv = Canvas(14, 18)
        plane(cv, rect_set(6, 6, 2, 12), WOOD, 2)
        plane(cv, rect_set(2, 1, 10, 6), CREAM, 2)
        cv.set(5, 3, LEAF[2]); cv.set(6, 2, LEAF[3]); cv.set(7, 4, LEAF[2])
        return cv
    if stage == 1:
        cv = Canvas(18, 26)
        plane(cv, rect_set(8, 11, 2, 15), WOOD, 2)
        plane(cv, rect_set(13, 13, 2, 13), CREAM, 1)  # a support stake
        cv.hline(10, 16, 3, CREAM[2])
        canopy(cv, [(9, 9, 5.0), (7, 11, 4.2), (11, 11, 4.2)], LEAF, seed=21)
        return cv
    big = stage >= 3
    w, h = (48, 64) if big else (34, 46)
    cv = Canvas(w, h)
    cx = w / 2
    tw = 7 if big else 5
    tx = int(cx - tw / 2)
    trunk_top = h - (24 if big else 18)
    style.trunk(cv, tx, trunk_top - 4, h, tw, WOOD)
    k = 0.72 if big else 0.5
    d = 3 * k + 3  # room above the crown for the bumps and the outline
    lobes = [(cx + 11 * k, 20 * k + d, 15 * k), (cx - 12 * k, 22 * k + d, 15 * k), (cx + 2 * k, 13 * k + d, 15 * k),
             (cx - 9 * k, 36 * k + d, 14 * k), (cx + 10 * k, 37 * k + d, 14 * k), (cx, 30 * k + d, 14 * k)]
    shape = canopy(cv, lobes, LEAF, seed=20 + stage)
    style.trunk(cv, tx, trunk_top, h, tw, WOOD, shape)
    if stage >= 4:  # ripe fruit, lit from the top left
        for (fx, fy) in ((cx - 12, 12), (cx + 5, 7), (cx - 5, 22), (cx + 11, 20), (cx - 1, 14)):
            fx, fy = int(fx), int(fy)
            cv.rect(fx, fy, 3, 3, RED[2]); cv.set(fx, fy, RED[4]); cv.set(fx + 1, fy, RED[3])
            cv.set(fx + 2, fy + 2, RED[1])
    return cv


def growth_sprites() -> dict[str, Canvas]:
    out = {}
    for kind in ('tulip', 'chamomile', 'lavender'):
        for stage in range(5):
            out[f'plot_{kind}_{stage}'] = plot_plants(kind, stage)
    for stage in range(5):
        out[f'orchard_{stage}'] = orchard_tree(stage)
    return out

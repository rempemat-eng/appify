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
from materials import G, P, WTR, SAND, WOOD, STONE, LEAF, NAP, RED, CREAM, GOLD, INK

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

# The bridge deck is 44 wide between its rails (the path fits with room either side).
BRIDGE = (PATH_X - 27, int(STREAM_Y - 20), 54, 40)  # x, y, w, h of the flat bridge decal

# Growing beds in the meadow, east of the path. (x, y) is the bed's top-left.
PLOT_W, PLOT_H = 44, 20
PLOTS = [(200, 368), (256, 368), (200, 408), (256, 408), (200, 448), (256, 448)]
PLOT_KINDS = ['tulip', 'chamomile', 'lavender', 'chamomile', 'lavender', 'tulip']
# Orchard pits west of the path: (x, y) is the tree's base (feet) point.
ORCHARD = [(52, 410), (108, 440), (54, 488)]

FENCE_Y = 528  # top of the lower fence
GATE_W, GATE_H = 48, 44
GATE_X, GATE_Y = PATH_X - GATE_W // 2, FENCE_Y - 16


def meadow_path(thick_path):
    pts = thick_path([(PATH_X, 280), (PATH_X - 1, 330), (PATH_X + 1, 400), (PATH_X, 470),
                      (PATH_X, 530), (PATH_X, H + 12)], 18.5, 7)
    pts |= thick_path([(PATH_X + 10, 432), (196, 432)], 9.5, 8)   # to the beds
    pts |= thick_path([(PATH_X - 10, 446), (126, 446)], 9.5, 9)   # to the orchard
    return pts


def draw_stream(cv: Canvas, phase: int):
    for (x, y) in STREAM_BANK:
        if 0 <= x < W:
            cv.set(x, y, SAND[1] if noise2(x, y, 23) < 0.82 else SAND[2])
    for (x, y) in STREAM_BANK:
        if (x, y - 1) in STREAM and (x, y + 1) not in STREAM:
            cv.set(x, y, SAND[0])  # wet lower lip
    for (x, y) in STREAM:
        if not (0 <= x < W):
            continue
        c = stream_centre(x)
        col = WTR[2] if abs(y - c) < 3 else WTR[1]
        if (x, y - 1) not in STREAM:
            col = WTR[0]
        elif (x, y - 2) not in STREAM:
            col = WTR[1]
        cv.set(x, y, col)
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
        y = int(stream_centre(rx)) - 10
        cv.vline(rx, y - 4, 5, LEAF[1]); cv.vline(rx + 2, y - 3, 4, LEAF[2])
        cv.set(rx - 1, y - 4, LEAF[3]); cv.set(rx + 1, y - 1, LEAF[3])


def draw_beds(cv: Canvas):
    """Raised timber beds with tilled rows, and mulched pits for the orchard."""
    for (bx, by) in PLOTS:
        cv.rect(bx, by, PLOT_W, PLOT_H, WOOD[1])
        cv.rect(bx + 1, by + 1, PLOT_W - 2, PLOT_H - 2, '#5A3A26')
        for ry in range(by + 4, by + PLOT_H - 2, 4):
            cv.hline(bx + 2, ry, PLOT_W - 4, '#4A2E1E')
            cv.hline(bx + 2, ry - 1, PLOT_W - 4, '#6E4A30')
        cv.hline(bx + 1, by, PLOT_W - 2, WOOD[3])
        cv.hline(bx, by + PLOT_H - 1, PLOT_W, WOOD[0])
        cv.hline(bx + 1, by + PLOT_H, PLOT_W - 1, G[1])
        for sx in range(bx + 4, bx + PLOT_W - 2, 8):
            cv.set(sx, by + PLOT_H - 2, WOOD[3])
    for (ox, oy) in ORCHARD:
        pit = oval(ox, oy - 3, 13, 6)
        for (x, y) in pit:
            cv.set(x, y, '#6E4A30' if y > oy - 4 else '#5A3A26')
        for (x, y) in pit:
            if (x, y - 1) not in pit:
                cv.set(x, y, '#4A2E1E')
        cv.hline(ox - 7, oy - 6, 4, WOOD[3]); cv.hline(ox + 4, oy - 2, 3, WOOD[3])


def draw_lower_details(cv: Canvas, path: set):
    """Wildflower drifts and clover patches give the meadow its own texture."""
    for i in range(56):
        x = int(noise2(i, 9, 81) * (W - 8)) + 4
        y = STREAM_Y + 24 + int(noise2(i, 10, 81) * (FENCE_Y - STREAM_Y - 30))
        if (x, y) in path or any(bx - 2 <= x <= bx + PLOT_W + 2 and by - 2 <= y <= by + PLOT_H + 2 for bx, by in PLOTS):
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


def draw_top_band(phase: int = 0) -> Canvas:
    """Forest floor above the clearing: deep shade under the canopy."""
    from style import FOREST_DARK, dither_dark
    cv = Canvas(W, TOP)
    for y in range(TOP):
        for x in range(W):
            cv.set(x, y, G[2] if y > TOP - 4 else G[1])
    dither_dark(cv, 0, 0, W, TOP - 10, 1.0, FOREST_DARK)
    dither_dark(cv, 0, TOP - 10, W, 3, 0.75, FOREST_DARK)
    dither_dark(cv, 0, TOP - 7, W, 4, 0.5, FOREST_DARK)
    dither_dark(cv, 0, TOP - 3, W, 3, 0.25, FOREST_DARK)
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
    for row, ry in enumerate((lift + 7, lift + 15)):
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

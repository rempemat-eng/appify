"""The lower garden and the forest above it, drawn at native pixel resolution.

The original clearing keeps its coordinates (y 0-176). Below it a stream, a
bridge and a meadow fill the rest of a portrait phone screen; above it a band
of forest sits behind the HUD. The meadow's beds and orchard pits are baked
into the ground; what grows in them is drawn as separate stage sprites so the
app can show the garden growing from the player's breaks.
"""
from __future__ import annotations

import math

from pixel import Canvas, disc, noise2, oval, shade_blob, smooth_noise
from materials import G, P, WTR, SAND, WOOD, STONE, LEAF, NAP, RED, CREAM, INK

W = 192
H = 384  # full walkable map height (native px)
TOP = 32  # forest band drawn above y = 0, behind the HUD

STREAM_Y = 204


def stream_centre(x: float) -> float:
    return STREAM_Y + 4 * math.sin(x / 23) + 2 * math.sin(x / 9 + 1)


STREAM = set()
for _x in range(-2, W + 2):
    c = stream_centre(_x)
    half = 6 + (smooth_noise(_x, 0, 11, 91) - 0.5) * 2.4
    for _y in range(int(c - half), int(c + half) + 1):
        STREAM.add((_x, _y))
STREAM_BANK = set()
for (_x, _y) in STREAM:
    for _dy in (-2, -1, 1, 2):
        if (_x, _y + _dy) not in STREAM:
            STREAM_BANK.add((_x, _y + _dy))

BRIDGE = (80, 190, 32, 30)  # x, y, w, h of the bridge sprite (path crosses here)

# Growing beds in the meadow, east of the path. (x, y) is the bed's top-left.
PLOT_W, PLOT_H = 30, 14
PLOTS = [(116, 238), (152, 238), (116, 266), (152, 266), (116, 294), (152, 294)]
PLOT_KINDS = ['tulip', 'chamomile', 'lavender', 'chamomile', 'lavender', 'tulip']
# Orchard pits west of the path: (x, y) is the tree's base (feet) point.
ORCHARD = [(26, 258), (60, 276), (24, 306)]

FENCE_Y = 336  # top of the lower fence
GATE_X, GATE_Y = 78, 321


def meadow_path(thick_path):
    pts = thick_path([(96, 176), (95, 196), (96, 222), (97, 260), (96, 300), (96, 340), (96, 392)], 8.5, 7)
    pts |= thick_path([(98, 280), (110, 280)], 4.5, 8)   # to the beds
    pts |= thick_path([(92, 270), (78, 268)], 4.5, 9)    # to the orchard
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
    for i in range(18):
        bx = int(noise2(i, 4, 77) * W)
        x = (bx + phase * 2) % (W + 8) - 4
        y = int(stream_centre(x) + (noise2(i, 5, 77) - 0.5) * 6)
        length = 3 + (i % 3)
        for s in range(length):
            if (x + s, y) in STREAM and (x + s, y - 1) in STREAM:
                cv.set(x + s, y, WTR[3] if s < length - 1 else WTR[2])
        if i % 5 == 0 and (x + 1, y - 1) in STREAM:
            cv.set(x + 1, y - 1, WTR[4])
    # Stones and reeds where the water meets the meadow.
    for sx in (12, 47, 141, 176):
        y = int(stream_centre(sx)) + 6
        cv.hline(sx, y, 4, STONE[1]); cv.hline(sx + 1, y - 1, 3, STONE[3]); cv.set(sx + 1, y - 2, STONE[4])
    for rx in (6, 33, 63, 128, 160, 186):
        y = int(stream_centre(rx)) - 7
        cv.vline(rx, y - 4, 5, LEAF[1]); cv.vline(rx + 2, y - 3, 4, LEAF[2])
        cv.set(rx - 1, y - 4, LEAF[3]); cv.set(rx + 1, y - 1, LEAF[3])


def draw_beds(cv: Canvas):
    """Raised timber beds with tilled rows, and mulched pits for the orchard."""
    for (bx, by) in PLOTS:
        cv.rect(bx, by, PLOT_W, PLOT_H, WOOD[1])
        cv.rect(bx + 1, by + 1, PLOT_W - 2, PLOT_H - 2, '#5A3A26')
        for ry in range(by + 3, by + PLOT_H - 2, 3):
            cv.hline(bx + 2, ry, PLOT_W - 4, '#4A2E1E')
            cv.hline(bx + 2, ry - 1, PLOT_W - 4, '#6E4A30')
        cv.hline(bx + 1, by, PLOT_W - 2, WOOD[3])
        cv.hline(bx, by + PLOT_H - 1, PLOT_W, WOOD[0])
        cv.hline(bx + 1, by + PLOT_H, PLOT_W - 1, G[1])
        for sx in range(bx + 4, bx + PLOT_W - 2, 8):
            cv.set(sx, by + PLOT_H - 2, WOOD[3])
    for (ox, oy) in ORCHARD:
        for (x, y) in oval(ox, oy - 2, 9, 4.5):
            n = noise2(x, y, 31)
            cv.set(x, y, '#6E4A30' if n < 0.55 else '#5A3A26')
        for (x, y) in oval(ox, oy - 2, 9, 4.5):
            if (x, y - 1) not in oval(ox, oy - 2, 9, 4.5):
                cv.set(x, y, '#4A2E1E')
        cv.hline(ox - 5, oy - 4, 3, WOOD[3]); cv.set(ox + 3, oy - 1, WOOD[3])


def draw_lower_details(cv: Canvas, path: set):
    """Wildflower drifts and clover patches give the meadow its own texture."""
    for i in range(40):
        x = int(noise2(i, 9, 81) * (W - 8)) + 4
        y = 226 + int(noise2(i, 10, 81) * 150)
        if (x, y) in path or any(bx - 2 <= x <= bx + PLOT_W + 2 and by - 2 <= y <= by + PLOT_H + 2 for bx, by in PLOTS):
            continue
        col = [CREAM[3], '#F2D16B', NAP[4], RED[4], '#FFFFFF'][i % 5]
        cv.set(x, y, col); cv.set(x + 2, y + 1, col); cv.set(x + 1, y + 2, col)
        cv.set(x + 1, y + 1, '#E8A33D')
    for i in range(10):
        x = int(noise2(i, 11, 82) * (W - 20)) + 10
        y = 180 + int(noise2(i, 12, 82) * 200)
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
def bridge() -> Canvas:
    w, h = BRIDGE[2], BRIDGE[3]
    cv = Canvas(w, h)
    # deck planks run across the stream (north-south), lit from the left
    for x in range(4, w - 4):
        for y in range(2, h - 2):
            col = WOOD[3] if (y // 3) % 2 == 0 else WOOD[2]
            if y % 3 == 2:
                col = WOOD[1]
            if x == 4:
                col = WOOD[4] if y % 3 != 2 else WOOD[2]
            cv.set(x, y, col)
    for y in range(4, h - 3, 6):
        cv.set(8, y, WOOD[0]); cv.set(w - 9, y + 1, WOOD[0])  # nails
    # side rails with posts
    for x0 in (1, w - 4):
        cv.rect(x0, 0, 3, h, WOOD[2])
        cv.vline(x0, 0, h, WOOD[3] if x0 == 1 else WOOD[1])
        cv.vline(x0 + 2, 0, h, WOOD[1])
        for py in (0, h // 2 - 1, h - 3):
            cv.rect(x0 - 1, py, 5, 3, WOOD[2]); cv.hline(x0 - 1, py, 5, WOOD[4])
    cv.outline(INK)
    return cv


def _flower(cv: Canvas, x: int, y: int, kind: str, stage: int):
    """One plant whose stem foot is at (x, y). Stages: 1 sprout .. 4 bloom."""
    if stage <= 0:
        cv.set(x, y, '#3A2416'); cv.set(x + 1, y, WOOD[2])
        return
    stem = LEAF[2]
    height = (1, 3, 5, 7)[stage - 1]
    cv.vline(x, y - height + 1, height, stem)
    if stage == 1:
        cv.set(x - 1, y - 1, LEAF[3]); cv.set(x + 1, y - 1, LEAF[4])
        return
    cv.set(x - 1, y - 1, LEAF[3]); cv.set(x - 2, y - 2, LEAF[4])
    cv.set(x + 1, y - 2, LEAF[3]); cv.set(x + 2, y - 3, LEAF[4])
    cv.set(x - 1, y, LEAF[1])
    top = y - height
    if stage == 2:
        cv.set(x, top, LEAF[4]); cv.set(x - 1, top + 1, LEAF[3])
        return
    if kind == 'tulip':
        petals = (RED[2], RED[3], RED[4])
    elif kind == 'chamomile':
        petals = (CREAM[1], CREAM[2], CREAM[3])
    else:
        petals = (NAP[1], NAP[2], NAP[4])
    if stage == 3:  # closed bud
        cv.set(x, top, petals[1]); cv.set(x, top - 1, petals[2]); cv.set(x - 1, top, LEAF[3])
        return
    if kind == 'tulip':
        cv.hline(x - 1, top, 3, petals[1]); cv.set(x - 1, top - 1, petals[2]); cv.set(x + 1, top - 1, petals[1])
        cv.set(x, top + 1, petals[0]); cv.set(x, top - 1, petals[2])
    elif kind == 'chamomile':
        for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            cv.set(x + dx, top + dy, petals[2] if dy <= 0 else petals[1])
        cv.set(x, top, '#E8A33D'); cv.set(x, top - 1, '#F2D16B')
    else:
        cv.vline(x, top - 3, 4, petals[1])
        cv.set(x, top - 3, petals[2]); cv.set(x - 1, top - 1, petals[2]); cv.set(x + 1, top - 2, petals[1])
        cv.set(x - 1, top + 1, petals[0])


def plot_plants(kind: str, stage: int) -> Canvas:
    """A whole bed's planting at one stage; anchored to the bed's top-left."""
    cv = Canvas(PLOT_W, PLOT_H + 10)
    for row, ry in enumerate((10 + 5 - 3, 10 + 5 + 3)):
        for col in range(4):
            x = 5 + col * 7 + (2 if row else 0)
            jitter = int(noise2(col, row, len(kind) + stage) * 2)
            _flower(cv, x, ry + jitter - 1, kind, stage)
    if stage >= 4:
        # a visiting butterfly on a blooming bed
        cv.set(PLOT_W - 6, 2, NAP[4] if kind != 'lavender' else '#F2D16B')
        cv.set(PLOT_W - 4, 2, NAP[4] if kind != 'lavender' else '#F2D16B')
        cv.set(PLOT_W - 5, 3, INK)
    return cv


def orchard_tree(stage: int) -> Canvas:
    """0 seed marker, 1 sapling, 2 young tree, 3 grown tree, 4 fruiting tree."""
    if stage == 0:
        cv = Canvas(10, 12)
        cv.vline(5, 1, 10, WOOD[2]); cv.vline(4, 1, 10, WOOD[3])
        cv.rect(2, 1, 7, 4, CREAM[2]); cv.hline(2, 1, 7, CREAM[3]); cv.set(5, 2, LEAF[2])
        cv.outline(INK)
        return cv
    if stage == 1:
        cv = Canvas(12, 18)
        cv.vline(6, 7, 10, WOOD[2]); cv.vline(5, 9, 8, WOOD[3])
        for (x, y) in oval(6, 6, 4.5, 4):
            cv.set(x, y, LEAF[3] if x + y < 11 else LEAF[2])
        cv.set(4, 4, LEAF[4]); cv.set(5, 3, LEAF[4])
        cv.vline(9, 9, 8, WOOD[3]); cv.set(8, 10, CREAM[2])  # a little support stake
        cv.outline(INK)
        return cv
    import style
    big = stage >= 3
    w, h = (36, 46) if big else (24, 32)
    cv = Canvas(w, h)
    cx = w / 2
    tw = 6 if big else 4
    tx = int(cx - tw / 2)
    trunk_top = h - (20 if big else 15)
    style.trunk(cv, tx, trunk_top - 3, h, tw, WOOD)
    crx, cry = (15.0, 13.5) if big else (10.0, 9.0)
    canopy = style.leafy(cv, cx, cry + 2.5, crx, cry, LEAF, r=2.7 if big else 2.2, seed=20 + stage)
    style.trunk(cv, tx, trunk_top, h, tw, WOOD, canopy)
    if stage >= 4:  # ripe fruit, lit from the top left
        for (fx, fy) in ((cx - 9, 8), (cx + 6, 6), (cx - 3, 14), (cx + 9, 15), (cx - 12, 16), (cx + 2, 4)):
            fx, fy = int(fx), int(fy)
            cv.rect(fx, fy, 2, 2, RED[2]); cv.set(fx, fy, RED[4]); cv.set(fx + 1, fy + 1, RED[1])
    cv.outline(INK)
    return cv


def meadow_sign() -> Canvas:
    """A small hand-painted sign at the meadow: tap it to see what is growing."""
    cv = Canvas(16, 20)
    cv.rect(7, 9, 2, 10, WOOD[2]); cv.vline(7, 9, 10, WOOD[1])
    cv.rect(1, 2, 14, 8, WOOD[3]); cv.hline(1, 2, 14, WOOD[4]); cv.hline(1, 9, 14, WOOD[1])
    cv.set(4, 5, LEAF[2]); cv.set(4, 4, LEAF[3]); cv.set(3, 6, LEAF[3]); cv.set(5, 6, LEAF[4])
    cv.hline(7, 5, 6, WOOD[1]); cv.hline(7, 7, 4, WOOD[1])
    cv.outline(INK)
    return cv


def growth_sprites() -> dict[str, Canvas]:
    out = {}
    for kind in ('tulip', 'chamomile', 'lavender'):
        for stage in range(5):
            out[f'plot_{kind}_{stage}'] = plot_plants(kind, stage)
    for stage in range(5):
        out[f'orchard_{stage}'] = orchard_tree(stage)
    return out

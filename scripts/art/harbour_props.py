"""Props for Driftwood Harbour on the valley's coast (world-atlas.md).

Still the valley's materials and light (it is walkable from Crossroads Town), but the
coast's own things: whitewashed cottages with tarred roofs, a striped lighthouse, boats,
nets, pots and the fish market. Run directly for a contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, WOOD, STONE, RED, WTR, PLASTER, SLATE, GOLD, LEAF  # noqa: E402

TAR = MATERIALS['tar']  # tarred roof boards
SAILCLOTH = MATERIALS['sailcloth']
ROPE = MATERIALS['rope']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def cottage(width: int = 80, seed: int = 0) -> Canvas:
    """A fisher's cottage, 80 x 74: a steep roof of tarred boards seen from above with a
    whitewashed chimney, thick whitewashed walls with small deep windows, a blue door,
    a net hung to dry on the wall and a lobster pot by the step."""
    w, h = width, 74
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (w - 1) / 2, 18, 40, 40, 66
    chim = rect_set(12, 6, 10, 14)
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, TAR, hole=chim, seed=71 + seed, moss=None)
    for (x, y) in rect_set(12, 6, 10, 14):
        cv.set(x, y, PLASTER[4] if x < 16 else PLASTER[3])
    cv.rect(11, 5, 12, 3, PLASTER[5]); cv.rect(14, 6, 6, 2, '#2A2420')
    gable = gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2), 7, w - 8,
                             apex_y, wall_top, PLASTER, boards=False)
    for (x, y) in rect_set(7, wall_top, w - 14, wall_bottom - wall_top):  # whitewash over rough stone
        n = noise2(x // 2, y // 2, 281 + seed)
        cv.set(x, y, PLASTER[5] if n > 0.55 else PLASTER[4])
        if noise2(x, y, 282) > 0.94:
            cv.set(x, y, PLASTER[2])  # a chip showing the stone
    proud = set()
    dx = int(ridge) - 7
    for (x, y) in rect_set(dx, wall_bottom - 20, 14, 20):  # the blue door
        cv.set(x, y, WTR[2] if (x - dx) % 4 else WTR[1])
    cv.hline(dx, wall_bottom - 20, 14, WTR[3]); cv.set(dx + 11, wall_bottom - 10, GOLD[4])
    proud |= rect_set(dx - 1, wall_bottom - 21, 16, 1)
    for wx in (13, w - 25):
        gp.window(cv, wx, wall_top + 6, 12, 10, shutters=None, sill=True, warm=seed % 2 == 0)
    for k in range(10):  # a net drying on the wall: a diamond mesh of rope
        for t in range(8):
            x, y = w - 22 + (k + t) % 10 + (t // 2), wall_top + 2 + t
            if 7 < x < w - 7 and (x + y) % 3 == 0:
                cv.set(x, y, ROPE[2])
    detail.cast(cv, proud, 1, 1, k=1, on=PLASTER, reach=2)
    detail.overhang_shadow(cv, 7, w - 7, wall_top, lambda x: 3, k=2, cap=1)
    detail.stones(cv, 5, wall_bottom, w - 10, 8, STONE, seed=19 + seed, course=4, moss=LEAF)
    return cv


def lighthouse() -> Canvas:
    """The lighthouse at the breakwater's end, 44 x 140: a round tower in red and white
    bands shaded as a cylinder, a black gallery with a rail, a glazed lantern room with
    the lamp lit, a domed cap and a weather vane."""
    w, h = 44, 140
    cv = Canvas(w, h, pad=PAD)
    cx = (w - 1) / 2
    for y in range(36, h - 10):
        t = (y - 36) / (h - 46)
        r = 9 + t * 6
        for x in range(int(cx - r), int(cx + r) + 1):
            k = (x - (cx - r)) / (2 * r + 1)
            band = ((y - 36) // 14) % 2
            ramp = RED if band else PLASTER
            lo = 2 if ramp is RED else 3
            c = ramp[lo + 2] if k < 0.18 else ramp[lo + 1] if k < 0.45 else ramp[lo] if k < 0.78 else ramp[lo - 1]
            cv.set(x, y, c)
    for (x, y) in rect_set(int(cx) - 4, h - 34, 9, 14):  # a door at the foot
        cv.set(x, y, WOOD[2] if x < cx else WOOD[1])
    for wy in (60, 88):
        cv.rect(int(cx) - 2, wy, 4, 6, '#2A2D36')
    for y in range(h - 10, h):  # the plinth
        for x in range(int(cx - 18), int(cx + 18)):
            cv.set(x, y, STONE[3] if y == h - 10 else STONE[2] if x < cx else STONE[1])
    # gallery, lantern room, cap
    cv.rect(int(cx) - 14, 32, 29, 4, TAR[2]); cv.hline(int(cx) - 14, 32, 29, TAR[4])
    for x in range(int(cx) - 14, int(cx) + 15, 3):
        cv.vline(x, 28, 4, TAR[3])
    cv.hline(int(cx) - 14, 28, 29, TAR[3])
    for y in range(14, 28):
        for x in range(int(cx) - 8, int(cx) + 9):
            glass = (x - int(cx)) % 5 != 0
            cv.set(x, y, ('#FFF2B8' if abs(x - cx) < 3 and 17 < y < 25 else '#BFD6E6' if x < cx else '#8FAABF') if glass else TAR[1])
    for (x, y) in disc(cx, 20, 3):
        cv.set(x, y, '#FFFBE0')
    for y in range(4, 14):
        hw = (y - 2) * 0.9
        for x in range(int(cx - hw), int(cx + hw) + 1):
            cv.set(x, y, TAR[3] if x < cx else TAR[1])
    cv.vline(int(cx), 0, 5, TAR[2]); cv.hline(int(cx) - 3, 1, 7, GOLD[3])
    return cv


def fishing_boat(length: int = 64, hull=WTR) -> Canvas:
    """A small fishing boat at its mooring, 64 x 30, seen from above: a planked hull
    lit along its port side, a little wheelhouse, a stub mast, coiled rope and a float."""
    w, h = length, 30
    cv = Canvas(w, h, pad=PAD)
    body = set()
    for x in range(2, w - 2):
        t = (x - 2) / (w - 4)
        half = (8 + 2.5 * min(1.0, t * 8)) if t < 0.58 else 10.5 * (1 - ((t - 0.58) / 0.42) ** 1.7)  # blunt stern, pointed bow
        for y in range(int(15 - half), int(15 + half) + 1):
            body.add((x, y))
    for (x, y) in body:
        edge = (x, y - 1) not in body or (x, y + 1) not in body or (x - 1, y) not in body or (x + 1, y) not in body
        if edge:
            cv.set(x, y, hull[3] if y < 15 else hull[1])
        else:
            cv.set(x, y, WOOD[3] if (y % 3) else WOOD[2])
    for (x, y) in body:
        inner = all((x + dx, y + dy) in body for dx in (-2, 2) for dy in (-2, 2))
        if not inner and not ((x, y - 1) not in body or (x, y + 1) not in body):
            cv.set(x, y, hull[2])
    for (x, y) in rect_set(int(w * 0.55), 9, 12, 12):  # the wheelhouse roof
        cv.set(x, y, PLASTER[5] if y < 12 else PLASTER[3])
    cv.rect(int(w * 0.55) + 2, 18, 8, 2, '#3E5468')
    for (x, y) in disc(int(w * 0.3), 15, 2):
        cv.set(x, y, WOOD[1])
    for k in range(10):  # a coil of rope
        a = k * 0.7
        cv.set(int(w * 0.2 + math.cos(a) * 3), int(15 + math.sin(a) * 3), ROPE[2])
    for (x, y) in disc(int(w * 0.4), 7, 1.8):
        cv.set(x, y, RED[3] if x < w * 0.4 else RED[2])
    return cv


def net_rack() -> Canvas:
    """Nets drying on a rack of poles, 52 x 40: rope mesh sagging between posts, floats."""
    w, h = 52, 40
    cv = Canvas(w, h, pad=PAD)
    for px in (2, 25, 48):
        gp.post(cv, px, 4, h - 1, w=3, ramp=WOOD)
    cv.hline(2, 5, 49, WOOD[3])
    for seg in ((4, 25), (27, 48)):
        for x in range(seg[0], seg[1]):
            sag = int(math.sin((x - seg[0]) / (seg[1] - seg[0]) * math.pi) * 6)
            for y in range(6, 24 + sag):
                if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                    cv.set(x, y, ROPE[2] if y < 14 else ROPE[1])
            if (x - seg[0]) % 5 == 2:
                for (fx, fy) in disc(x, 24 + sag, 1.5):
                    cv.set(fx, fy, RED[3] if fx <= x else RED[2])
    return cv


def lobster_pots() -> Canvas:
    """Three lobster pots stacked by a coil of rope, 34 x 24."""
    cv = Canvas(34, 24, pad=PAD)
    for (bx, by) in ((2, 10), (16, 10), (9, 1)):
        for (x, y) in rect_set(bx, by, 14, 12):
            top = y < by + 3
            cv.set(x, y, (WOOD[4] if top else WOOD[2]) if (x - bx) % 4 == 0 or top or y == by + 11 else '#2A2420')
        for x in range(bx, bx + 14, 2):
            cv.vline(x, by + 3, 8, ROPE[1])
    return cv


def fish_stall() -> Canvas:
    """The fish market stall, 76 x 56: a blue and white canvas awning from above, a
    sloping counter of ice with fish laid in rows, a scale and a chalk price board
    (marks only, no words)."""
    w, h = 76, 56
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 20):
        for x in range(2, w - 2):
            stripe = (x // 8) % 2
            c = (WTR[2] if stripe else SAILCLOTH[4]) if y < 16 else (WTR[1] if stripe else SAILCLOTH[2])
            cv.set(x, y, c)
    for x in range(2, w - 2):
        cv.set(x, 20 + (x // 4) % 2, WTR[1] if (x // 8) % 2 else SAILCLOTH[1])
    for px in (4, w - 7):
        gp.post(cv, px, 20, h - 2, w=3, ramp=WOOD)
    for y in range(26, 40):  # ice
        for x in range(6, w - 6):
            cv.set(x, y, '#E6F2F6' if (x + y) % 4 else '#C6DDEE')
    for row, y in enumerate((28, 33)):
        for x in range(9, w - 12, 9):
            for t in range(7):
                cv.set(x + t, y + (1 if t in (0, 6) else 0), '#9AA8B8' if t < 5 else '#6E7E92')
            cv.set(x, y, '#2A2D36')
            cv.set(x + 6, y - 1, '#6E7E92'); cv.set(x + 6, y + 2, '#6E7E92')
    detail.boards(cv, rect_set(6, 40, w - 12, 12), WOOD, 2, 40, board=4, vertical=True, x0=6)
    cv.hline(6, 40, w - 12, WOOD[4])
    for (x, y) in rect_set(w - 20, 22, 12, 6):
        cv.set(x, y, '#2A2D36')
    cv.hline(w - 18, 24, 8, '#E6E2D0'); cv.hline(w - 18, 26, 5, '#E6E2D0')
    return cv


def bollard() -> Canvas:
    """An iron bollard with a mooring rope, 14 x 16."""
    cv = Canvas(14, 16, pad=PAD)
    for y in range(5, 15):
        for x in range(4, 10):
            cv.set(x, y, '#545A68' if x < 6 else '#3C404C' if x < 8 else '#2A2D36')
    for (x, y) in oval(7, 5, 4, 2):
        cv.set(x, y, '#727A8A' if x < 7 else '#545A68')
    for x in range(0, 6):
        cv.set(x, 9 + x // 3, ROPE[2])
    return cv


def anchor() -> Canvas:
    """An old anchor lying on the quay where it was set down, in the three-quarter view,
    34 x 20 (Matt, 19 Oct, fault 09: "pinned flat on a wall with no reason or mounting"):
    the shank lies east-west from its ring to the crown, the stock lies across it near
    the ring (foreshortened, being on the ground), one arm curls up off the stones toward
    us with its fluke, the other rests behind; rust at the flukes and the crown, and a few
    turns of chain trailing from the ring."""
    IRON = ['#24272F', '#363A46', '#4E5462', '#6C7484', '#8E96A6']
    RUST = ['#5A2E1E', '#8A4A2A', '#B0683A']
    cv = Canvas(34, 20, pad=PAD)
    for (cx, cy, wide) in ((3, 14, True), (6, 16, False), (9, 17, True), (13, 17, False), (16, 16, True)):
        for (x, y) in oval(cx, cy, 2 if wide else 1, 1 if wide else 1.5):  # the chain's links
            ring = abs(((x + 0.5 - cx) / (2 if wide else 1)) ** 2 + ((y + 0.5 - cy) / (1 if wide else 1.5)) ** 2 - 0.6) < 0.5
            if ring:
                cv.set(x, y, IRON[3] if y <= cy else IRON[1])
    for (x, y) in oval(6, 10, 3, 2):  # the ring, lying flat
        if ((x + 0.5 - 6) / 3) ** 2 + ((y + 0.5 - 10) / 2) ** 2 > 0.35:
            cv.set(x, y, IRON[4] if x < 6 and y < 10 else IRON[2])
    for x in range(9, 28):  # the shank: its top lit, its side in shade
        cv.set(x, 9, IRON[4] if x < 14 else IRON[3]); cv.set(x, 10, IRON[2]); cv.set(x, 11, IRON[1])
    for y in range(4, 16):  # the stock across it, foreshortened, ball ends
        cv.set(11, y, IRON[3] if y < 9 else IRON[2]); cv.set(12, y, IRON[1])
    for (x, y) in ((11, 3), (12, 3), (11, 16), (12, 16)):
        cv.set(x, y, IRON[3] if y < 9 else IRON[1])
    for t in range(9):  # the back arm, resting behind, curving away
        x, y = 27 + int(t * 0.6), 9 - int(t * 0.65)
        cv.set(x, y, IRON[2]); cv.set(x + 1, y, IRON[1])
    for (x, y) in ((32, 2), (31, 3), (32, 3), (33, 3), (32, 4)):
        cv.set(x, y, RUST[1])  # its fluke
    for t in range(9):  # the front arm, curling up off the quay toward us
        x, y = 27 + int(t * 0.7), 11 + int(t * 0.55)
        cv.set(x, y, IRON[3]); cv.set(x, y + 1, IRON[1])
    for (x, y) in ((31, 15), (32, 15), (33, 16), (31, 16), (32, 16), (32, 17), (31, 17)):
        cv.set(x, y, RUST[2] if y == 15 else RUST[1])  # its fluke, broad and rusted
    for (x, y) in ((26, 9), (27, 10), (26, 11), (28, 10)):
        cv.set(x, y, RUST[1])  # the crown, rusted
    return cv


def upturned_boat() -> Canvas:
    """A rowing boat turned keel-up on the beach for tarring, 50 x 22, on two trestles."""
    w, h = 50, 22
    cv = Canvas(w, h, pad=PAD)
    for x in range(3, w - 3):
        t = (x - 3) / (w - 6)
        half = 7 * math.sin(math.pi * min(1, t * 1.1)) if t < 0.9 else 7 * math.sin(math.pi * 0.99) * (1 - (t - 0.9) * 8)
        for y in range(int(11 - half), int(11 + half) + 1):
            k = (y - (11 - half)) / (2 * half + 1)
            cv.set(x, y, TAR[3] if k < 0.25 else TAR[2] if k < 0.6 else TAR[1])
        cv.set(x, 11, TAR[4])  # the keel
    for tx in (12, 36):
        cv.vline(tx, 15, 7, WOOD[2]); cv.vline(tx + 1, 15, 7, WOOD[1])
    return cv


def washing_line() -> Canvas:
    """A washing line in a cottage yard, 52 x 34, in the three-quarter view (Matt, 19 Oct,
    fault 08: "the sheets are flat squares and the posts are uneven"): two even posts
    with crosstrees, set in the ground, the line sagging between them, and on it a sheet
    with folds and a hem, a shirt with its sleeves hanging, a striped towel and a pair of
    socks, each pegged, lit on the left and shaded where it folds."""
    w, h = 52, 34
    cv = Canvas(w, h, pad=PAD)
    for px in (3, 47):  # the posts, the same height, with crosstrees
        for y in range(5, h):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
        cv.hline(px - 2, 5, 6, WOOD[4]); cv.hline(px - 2, 6, 6, WOOD[2])
        cv.set(px - 1, h - 1, WOOD[1]); cv.set(px + 2, h - 1, WOOD[1])  # where it goes into the ground

    def line_y(x):
        return 6 + int(round(4 * math.sin(math.pi * (x - 5) / 42)))

    for x in range(5, 47):
        cv.set(x, line_y(x), ROPE[3])

    def hang(x0, x1, length, ramp, kind):
        for x in range(x0, x1):
            top = line_y(x) + 1
            hem = top + length + (1 if (x - x0) % 5 == 2 else 0)
            for y in range(top, hem):
                fold = (x - x0) % 4
                c = ramp[2] if fold == 0 else ramp[4] if fold == 1 else ramp[3]
                if kind == 'stripe' and (y - top) in (3, 4):
                    c = RED[3]
                if x == x1 - 1:
                    c = ramp[1]  # its shaded edge
                cv.set(x, y, c)
            cv.set(x, hem, ramp[1])  # the hem
        for x in (x0, x1 - 1):
            cv.set(x, line_y(x), WOOD[4])  # pegs

    SHEET = ['#8A8478', '#B8B0A0', '#DCD6C8', '#F0EBE0', '#FBF8F2']
    hang(8, 21, 16, SHEET, 'plain')
    for x in range(24, 32):  # the shirt: its body, collar and sleeves hanging
        top = line_y(x) + 1
        for y in range(top, top + 11):
            cv.set(x, y, RED[4] if x < 26 else RED[3] if x < 30 else RED[2])
        cv.set(x, top + 11, RED[1])
    for (sx, lit) in ((23, True), (32, False)):
        top = line_y(sx) + 2
        for y in range(top, top + 7):
            cv.set(sx, y, RED[3] if lit else RED[2])
    cv.set(27, line_y(27) + 1, '#F0EBE0'); cv.set(28, line_y(28) + 1, '#F0EBE0')  # the collar
    for y in (4, 6, 8):
        cv.set(28, line_y(28) + y, '#F0EBE0')  # buttons
    hang(34, 40, 9, WTR[:1] + WTR[:4] if len(WTR) < 5 else WTR, 'stripe')
    for (sx, col) in ((42, GOLD), (44, GOLD)):  # a pair of socks
        top = line_y(sx) + 1
        for y in range(top, top + 6):
            cv.set(sx, y, col[3]); cv.set(sx + 1, y, col[2])
        cv.set(sx + 2, top + 5, col[2]); cv.set(sx + 2, top + 6, col[1])
    return cv


def buoy() -> Canvas:
    """A mooring buoy bobbing in the basin, 14 x 12, red with a white band."""
    cv = Canvas(14, 12, pad=PAD)
    for (x, y) in oval(7, 6, 5, 4):
        cv.set(x, y, RED[3] if x < 7 else RED[2])
    for x in range(2, 13):
        if cv.get(x, 6)[3]:
            cv.set(x, 6, PLASTER[5])
    cv.vline(7, 0, 3, TAR[2])
    return cv


def deck_chair(stripe=RED) -> Canvas:
    """A striped deck chair on the sand, 20 x 18: canvas slung in a wooden frame."""
    w, h = 20, 18
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, 13):  # the canvas, sloping back
        for x in range(4 + (y < 4), 16 - (y < 4)):
            band = (x // 3) % 2
            c = (stripe[3] if band else '#F2EEE6') if y < 9 else (stripe[2] if band else '#D8D2C6')
            cv.set(x, y, c)
    for (x0, x1) in ((3, 2), (16, 17)):  # the frame
        for t in range(14):
            cv.set(x0 + (x1 - x0) * t // 13, 2 + t, WOOD[3] if x0 < 10 else WOOD[2])
    cv.hline(3, 12, 14, WOOD[2]); cv.hline(3, 13, 14, WOOD[1])
    return cv


def driftwood() -> Canvas:
    """A bleached driftwood branch half in the sand, 34 x 12."""
    w, h = 34, 12
    cv = Canvas(w, h, pad=PAD)
    BONE = ['#6E625A', '#9A8E82', '#C2B8AA', '#E2DACE']
    for x in range(2, w - 4):
        y = 6 + int(math.sin(x / 6) * 1.5)
        cv.set(x, y - 1, BONE[3]); cv.set(x, y, BONE[2]); cv.set(x, y + 1, BONE[1])
    for (x0, dx, n) in ((10, 1, 6), (22, 1, 5)):  # snapped side branches
        for t in range(n):
            cv.set(x0 + dx * t, 5 - t // 2, BONE[2]); cv.set(x0 + dx * t, 6 - t // 2, BONE[1])
    cv.hline(4, 9, 20, '#C8A878')  # sand drifted along its foot
    return cv


def sailboat() -> Canvas:
    """A small sailboat out past the breakwater, 40 x 52: a white hull lit on its port
    side, a mast and a cream sail bellied by the wind, its shadow on the water."""
    w, h = 40, 52
    cv = Canvas(w, h, pad=PAD)
    hull = set()
    for x in range(4, w - 4):
        t = (x - 4) / (w - 8)
        half = 5 * (1 - abs(t - 0.4) ** 1.6 * 1.6) if t < 0.95 else 1
        for y in range(int(h - 10 - half), int(h - 10 + half) + 1):
            hull.add((x, y))
    for (x, y) in hull:
        cv.set(x, y, PLASTER[5] if y < h - 10 else PLASTER[3])
        if (x, y + 1) not in hull:
            cv.set(x, y, WTR[1])
    cv.hline(8, h - 10, w - 18, WOOD[3])  # the deck
    for y in range(4, h - 11):
        cv.set(18, y, WOOD[1])
    for y in range(6, h - 14):  # the sail, bellied out to the right
        span = int((y - 6) * 0.42 + 2 + math.sin((y - 6) / (h - 20) * math.pi) * 3)
        for x in range(19, 19 + span):
            cv.set(x, y, SAILCLOTH[4] if x < 19 + span - 3 else SAILCLOTH[3])
    cv.hline(19, h - 14, 16, WOOD[2])  # the boom
    for x in range(6, w - 4, 3):
        cv.set(x, h - 3, '#E6EEF6')  # its wake
    return cv


def props() -> dict[str, Canvas]:
    return {
        'cottage': cottage(80, 0), 'cottage_b': cottage(72, 1), 'lighthouse': lighthouse(),
        'boat_blue': fishing_boat(64, WTR), 'boat_red': fishing_boat(56, RED), 'net_rack': net_rack(),
        'lobster_pots': lobster_pots(), 'fish_stall': fish_stall(), 'bollard': bollard(), 'anchor': anchor(),
        'upturned_boat': upturned_boat(), 'washing_line': washing_line(), 'buoy': buoy(),
        'deck_chair': deck_chair(RED), 'deck_chair_b': deck_chair(WTR), 'driftwood': driftwood(), 'sailboat': sailboat(),
    }


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (221, 200, 164, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/harbour-props.png'))
    print('sheet', out.size)

"""The inside of the nap hut: the room you decorate (Claude B's).

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401

__all__ = ['home']


def home(frame: int = 0):
    """Inside the nap hut (living-world plan W4, the house you decorate), drawn with depth
    (Matt, 19 Oct: "lacks detail ... the fire pit should be against the wall ... looks
    very flat and not 3d"). Three rooms one behind another at the world's three-quarter
    angle. Every wall shows its thickness as a timber plate seen from above, then its
    face: crown moulding, plaster, a chair rail, panelled wainscot and a skirting board;
    a doorway shows the wall's depth at its ends and a threshold board. The floor is
    boards of varied tone with grain, knots and nails, shaded where it meets each wall.
    At the back the bedroom under two deep-set, curtained windows; through the first
    doorway the living room, its hearth built into the back wall with the chimney rising
    through the wall's top, the bookcase and the kitchen run along the same wall, the
    companion's basket and an armchair by the fire, the table with its chairs; through
    the second the sunroom on terracotta tiles, and the front door. Everything stands
    against a wall or round the hearth and the table, for a reason."""
    PL, WD = MATERIALS['plaster'], MATERIALS['wood']
    GOLD, NAP, CREAM = MATERIALS['gold'], MATERIALS['nap'], MATERIALS['cream']
    LEAF = MATERIALS['leaf']
    cv = Canvas(W, H)
    blocked = set()
    CAP, SIDE = 6, 8                    # a wall's thickness seen from above; the side walls' plates
    DOOR = (136, 184)                   # the doorways through both partitions
    BACK_FACE, PART_FACE = 58, 38       # how tall each wall's face shows
    MID, LOW, FRONT = 196, 396, H - 20  # where the partitions and the front wall stand

    def hexc(c):
        return c if isinstance(c, str) else '#%02X%02X%02X' % tuple(c[:3])

    def blend(a, b, t):
        ra, rb = _rgb(hexc(a)), _rgb(hexc(b))
        return '#%02X%02X%02X' % tuple(int(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))

    def dim(x, y, k):
        if 0 <= x < W and 0 <= y < H:
            r, g, b = cv.get(x, y)[:3]
            cv.set(x, y, (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), 255))

    # ---- the floor: boards running across the room, each its own tone ----------------
    tones = [blend(WD[2], WD[3], 0.25), blend(WD[2], WD[3], 0.45), blend(WD[2], WD[3], 0.6),
             blend(WD[2], WD[3], 0.75), blend(WD[2], WD[3], 0.9)]  # five boards' worth of timber, from five trees
    lit = [blend(t, WD[4], 0.3) for t in tones]
    dark = [blend(t, WD[1], 0.25) for t in tones]
    seam = blend(WD[1], WD[2], 0.45)
    for y in range(H):
        row, k = y // 8, y % 8
        off = (row * 37) % 72
        for x in range(W):
            plank = (x + off) // 72
            t = int(noise2(plank, row, 520) * 4.99)
            c = tones[t]
            j = (x + off) % 72
            if k == 7:
                c = seam  # the gap between rows
            elif k == 0:
                c = lit[t]  # the lit leading edge
            elif j == 0:
                c = seam  # a butt joint
            elif j == 1:
                c = lit[t]
            elif k in (2, 3, 5) and noise2((x + off) // 5, row * 8 + k, 523 + plank) > 0.8:
                c = dark[t]  # the grain, in runs along the board
            elif k in (1, 4) and noise2((x + off) // 4, row * 8 + k, 527 + plank) > 0.86:
                c = lit[t]  # a sheen where the grain rises
            if j in (3, 4, 67, 68) and k in (2, 5):
                c = dark[t] if j in (3, 67) else seam  # nail heads, two pixels each
            if 4 <= k <= 5 and noise2(x // 3, row, 528) > 0.93:
                c = blend(c, '#2A2018', 0.35)  # a scuff where a chair was dragged
            cv.set(x, y, c)
        if k == 3 and noise2(row, 9, 524) > 0.55:  # a knot now and then
            kx = int(noise2(row, 10, 524) * (W - 20)) + 10
            for (x, y2) in ((kx, y), (kx + 1, y), (kx, y + 1)):
                cv.set(x, y2, WD[1])
            cv.set(kx + 1, y + 1, dark[1])

    # ---- walls -------------------------------------------------------------------------
    def wall(y0, face, door=None, rail=0.5, posts=()):
        """A wall across the room: its top (the wall's thickness, a timber plate seen
        from above), then its face, shaded where the floor meets it."""
        def gap(x):
            return door is not None and door[0] <= x < door[1]
        for y in range(y0, y0 + CAP):
            k = y - y0
            for x in range(W):
                if gap(x):
                    continue
                c = WD[4] if k == 0 else WD[3] if k < CAP - 2 else WD[2] if k == CAP - 2 else WD[0]
                if k in (1, 2) and noise2(x // 9, y, 530) > 0.85:
                    c = WD[2]  # the plate's grain
                cv.set(x, y, c)
                blocked.add((x, y))
        top = y0 + CAP
        rail_y = top + int(face * rail)
        foot = top + face
        for y in range(top, foot):
            k = y - top
            for x in range(W):
                if gap(x):
                    continue
                if k < 3:
                    c = (WD[4], WD[3], WD[1])[k]  # the crown moulding
                elif y < rail_y:
                    c = PL[3] if k < 5 else PL[4]  # plaster, shaded just under the crown
                    if smooth_noise(x, y, 4, 531) > 0.68:
                        c = PL[3]  # the lime plaster trowelled unevenly, in broad soft patches
                    if x in posts or x - 1 in posts or x - 2 in posts:
                        c = WD[3] if x in posts else WD[2] if x - 1 in posts else WD[1]  # timber posts
                elif y < rail_y + 2:
                    c = WD[4] if y == rail_y else WD[1]  # the chair rail
                elif y < foot - 4:
                    px, py, ph = x % 32, y - rail_y - 2, foot - 4 - rail_y - 2
                    c = WD[2]  # panelled wainscot: a lit frame, a sunk panel
                    if px == 0 or py == 0:
                        c = WD[3]
                    elif px == 31 or py == ph - 1:
                        c = WD[1]
                    elif 3 <= px <= 28 and 2 <= py <= ph - 3:
                        c = WD[1] if px == 3 or py == 2 else WD[3] if px == 28 or py == ph - 3 else WD[2]
                        if c == WD[2] and noise2((x // 32) * 7 + px // 3, py, 534) > 0.8:
                            c = blend(WD[2], WD[1], 0.5)  # the panel's figure, running across it
                else:
                    c = (WD[4], WD[2], WD[2], WD[1])[y - (foot - 4)]  # the skirting board
                cv.set(x, y, c)
                blocked.add((x, y))
        if door:
            for y in range(y0, foot):  # the wall's ends either side of the doorway
                for d in range(3):
                    if y < top:
                        c = WD[3]
                    else:
                        c = PL[2] if d else WD[1]
                    cv.set(door[0] - 1 - d, y, c)  # the west end faces the light from the doorway
                    cv.set(door[1] + d, y, PL[5] if d == 0 and y >= top else WD[3] if y < top else PL[4])
            for x in range(door[0], door[1]):  # the threshold board
                cv.set(x, foot, WD[1]); cv.set(x, foot + 1, WD[3]); cv.set(x, foot + 2, WD[2])
        for k, f in enumerate((0.74, 0.82, 0.88, 0.93, 0.97)):  # the floor in the wall's shade
            for x in range(W):
                if not gap(x):
                    dim(x, foot + k, f)
        return foot

    floor_top = wall(0, BACK_FACE, posts=(126, 194))
    living_top = wall(MID, PART_FACE, door=DOOR)
    sun_top = wall(LOW, PART_FACE, door=DOOR)

    # ---- windows in the back wall: deep reveals, a sill, curtains --------------------
    for wx in (52, 220):
        wy, ww, wh = 14, 48, 34
        for y in range(wy, wy + wh):
            for x in range(wx, wx + ww):
                d = y - wy
                c = '#A9D3E6' if d < 12 else '#BFE0EE' if d < 15 else '#8CB874' if d < 22 else '#6E9A5C' if d < 28 else '#5E8A52'
                if 26 <= d <= 30 and noise2(x // 3, 1, 531 + wx) > 0.6:
                    c = '#4E7A46'  # the garden's hedge beyond
                cv.set(x, y, c)
        for (x, y) in disc(wx + 34, wy + 17, 5):  # a tree outside
            cv.set(x, y, '#5E8A52' if x + y < wx + wy + 51 else '#4E7A46')
        for y in range(wy, wy + wh):  # the reveal: the wall's depth round the glass
            for d in range(3):
                cv.set(wx + d, y, PL[2] if d < 2 else PL[3])
                cv.set(wx + ww - 1 - d, y, PL[5] if d == 0 else PL[4])
        for x in range(wx, wx + ww):
            cv.set(x, wy, PL[2]); cv.set(x, wy + 1, PL[2]); cv.set(x, wy + 2, PL[3])
        for y in range(wy + 3, wy + wh):  # the frame's bars
            cv.set(wx + ww // 2, y, WD[4]); cv.set(wx + ww // 2 + 1, y, WD[2])
        for x in range(wx + 3, wx + ww - 3):
            cv.set(x, wy + wh // 2 + 1, WD[4]); cv.set(x, wy + wh // 2 + 2, WD[2])
        cv.set(wx + 8, wy + 5, '#FFFFFF'); cv.set(wx + 7, wy + 6, '#E4F2F8')  # a glint
        for x in range(wx - 3, wx + ww + 3):  # the sill stands out from the wall, its shadow below
            cv.set(x, wy + wh, WD[4]); cv.set(x, wy + wh + 1, WD[3]); cv.set(x, wy + wh + 2, WD[1])
            cv.set(x, wy + wh + 3, PL[2]); cv.set(x, wy + wh + 4, PL[3])
        for (cx, side) in ((wx - 7, -1), (wx + ww + 1, 1)):  # curtains, gathered
            for y in range(wy - 3, wy + wh + 6):
                for i in range(6):
                    fold = (i + (y // 3) % 2) % 3
                    c = (NAP[3], NAP[2], NAP[1])[fold] if side < 0 else (NAP[2], NAP[1], NAP[1])[fold]
                    if y == wy + wh - 4:
                        c = GOLD[3]  # the tie
                    cv.set(cx + i, y, c)
        for x in range(wx - 9, wx + ww + 9):  # the rod
            cv.set(x, wy - 4, GOLD[4]); cv.set(x, wy - 3, GOLD[2])
        for (x, y) in ((wx + 39, wy + wh - 1), (wx + 40, wy + wh - 2), (wx + 41, wy + wh - 1), (wx + 40, wy + wh - 3)):
            cv.set(x, y, LEAF[3])  # a sprig in a pot on the east sill
        cv.set(wx + 40, wy + wh - 1, RED[2])
    for y in range(18, 44):  # a painting of the valley between them, gilt frame
        for x in range(142, 178):
            edge = x in (142, 143, 176, 177) or y in (18, 19, 42, 43)
            c = (GOLD[4] if x < 160 and y < 30 else GOLD[2]) if edge else '#A9D3E6' if y < 28 else '#7EA868' if y < 36 else '#5E8A52'
            cv.set(x, y, c)
    for (x, y) in disc(168, 23, 2):
        cv.set(x, y, '#F8DD8F')
    for x in range(144, 177):
        dim(x, 44, 0.86)  # its shadow on the plaster

    # ---- the living room's back wall: a clock; the sunroom's: two pictures ---------
    cx, cy = 195, MID + CAP + 14
    for (x, y) in disc(cx, cy, 6):
        cv.set(x, y, CREAM[3] if (x - cx) + (y - cy) < 3 else CREAM[2])
        if (x - cx) ** 2 + (y - cy) ** 2 > 25:
            cv.set(x, y, WD[1])
    cv.vline(cx, cy - 4, 4, WD[0]); cv.hline(cx, cy, 3, WD[0])
    for (px, scene) in ((44, 'sea'), (234, 'hill')):
        py = LOW + CAP + 6
        for y in range(py, py + 16):
            for x in range(px, px + 26):
                edge = x in (px, px + 25) or y in (py, py + 15)
                c = WD[1] if edge else ('#B8D8E8' if y < py + 8 else '#44628E') if scene == 'sea' else ('#9CC8E0' if y < py + 7 else '#6A9468')
                cv.set(x, y, c)
        for x in range(px + 1, px + 26):
            dim(x, py + 16, 0.86)

    # ---- the side walls: plates seen from above, shading the floor beside them -------
    for y in range(H):
        for x in range(SIDE):
            c = WD[1] if x == 0 else WD[0] if x == SIDE - 1 else WD[3] if noise2(y // 7, x, 532) > 0.3 else WD[2]
            cv.set(x, y, c); blocked.add((x, y))
            c = WD[4] if x == 0 else WD[1] if x == SIDE - 1 else WD[3] if noise2(y // 7, x, 533) > 0.3 else WD[2]
            cv.set(W - SIDE + x, y, c); blocked.add((W - SIDE + x, y))
        for k, f in enumerate((0.78, 0.86, 0.92, 0.97)):
            if (SIDE + k, y) not in blocked:
                dim(SIDE + k, y, f)
        if (W - SIDE - 1, y) not in blocked:
            dim(W - SIDE - 1, y, 0.92)

    # ---- the sunroom: terracotta tiles, lit at their top edge -------------------------
    for y in range(sun_top, FRONT):
        for x in range(SIDE, W - SIDE):
            tx, ty = x // 16, y // 16
            base = ('#C8743E', '#BE6E3C', '#B8683A')[int(noise2(tx, ty, 534) * 2.99)]
            c = base
            if x % 16 == 0 or y % 16 == 0:
                c = '#8A4A2A'  # the grout
            elif y % 16 == 1 or x % 16 == 1:
                c = blend(base, '#E8A07A', 0.4)  # each tile's lit edge
            cv.set(x, y, c)
        if y - sun_top < 5:
            for x in range(SIDE, W - SIDE):
                if not (DOOR[0] <= x < DOOR[1]):
                    dim(x, y, (0.76, 0.84, 0.9, 0.95, 0.98)[y - sun_top])

    # ---- the front wall: its top across the room, the door open onto the step --------
    for y in range(FRONT, H):
        for x in range(W):
            if 140 <= x < 180:
                c = STONE[3] if y < FRONT + 4 else '#8A6A3A' if (x + y) % 3 else '#A8844A'  # the step and the mat
                cv.set(x, y, c)
                continue
            k = y - FRONT
            c = WD[4] if k == 0 else WD[3] if k < 4 else WD[2] if noise2(x // 9, y, 535) > 0.3 else WD[3]
            cv.set(x, y, c); blocked.add((x, y))
    for y in range(FRONT, H):  # the door's jambs
        cv.set(139, y, WD[1]); cv.set(180, y, WD[4])

    # ---- light: the sun through the back windows, the fire's glow -------------------
    for wx in (52, 220):
        for y in range(floor_top + 2, floor_top + 56):
            for x in range(wx + int((y - floor_top) * 0.35), wx + 48 + int((y - floor_top) * 0.35)):
                if (x - wx) % 24 in (0, 1) or (y - floor_top) % 18 in (0, 1) or (x, y) in blocked:
                    continue
                if y > floor_top + 44 and (x + y) % 2:
                    continue  # the patch fades out, dithered
                r, g, b = cv.get(x, y)[:3]
                cv.set(x, y, (min(255, r + 20), min(255, g + 17), min(255, b + 10), 255))
    light_pool(cv, 46, living_top + 16, 50, 18, '#F2721E', skip=frozenset(blocked))

    # ---- rugs: a long one at the bed's foot, a braided oval by the fire -------------
    for y in range(152, 186):
        for x in range(46, 142):
            c = RED[3] if ((x - 46) // 6 + (y - 152) // 6) % 2 else RED[2]
            if y in (152, 185) or x in (46, 141):
                c = GOLD[3]
            if y == 185 or x == 141:
                c = GOLD[2]
            cv.set(x, y, c)
    for x in range(47, 143):
        dim(x, 186, 0.85)
    RX, RY, RCX, RCY = 46, 18, 58, 292  # the braided rug before the fire
    for (x, y) in oval(RCX, RCY, RX, RY):
        d = math.hypot((x - RCX) / RX, (y - RCY) / RY)
        ring = int(d * 6)
        c = (NAP[2], CREAM[3], NAP[3], RED[3], NAP[2], CREAM[2])[min(5, ring)]
        if (x + 2 * y) % 7 == 0:
            c = NAP[1]  # the braid
        if (x - RCX) + (y - RCY) * 2 > 0 and d > 0.9:
            c = NAP[1]  # its lower rim in shade
        cv.set(x, y, c)
    # a woven runner from the front door into the sunroom
    for y in range(470, FRONT):
        for x in range(142, 178):
            band = (y - 470) // 4 % 4
            c = (NAP[2], CREAM[3], RED[2], CREAM[3])[band] if 146 <= x < 174 else NAP[1]
            if (x + y) % 5 == 0 and 146 <= x < 174:
                c = CREAM[2]
            if x in (142, 177) and y % 2:
                c = CREAM[3]  # the fringe
            cv.set(x, y, c)

    # ---- the things a lived-in room collects (Eastward-level dressing, each where it
    # would be): two little framed portraits and a calendar on the bedroom wall, copper
    # pans on hooks by the kitchen door, slippers by the bed, a book left by the reading
    # chair, a ball of wool the companion has been at by its basket
    CREAM_HI = '#FBF5E6'

    def frame(x0, y0, w, h, inside):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                c = (GOLD[3] if x == x0 or y == y0 else GOLD[1]) if edge else inside[(x - x0 + y - y0) % len(inside)]
                cv.set(x, y, c)
        for x in range(x0 + 1, x0 + w + 1):
            dim(x, y0 + h, 0.82)  # its shadow on the plaster
    frame(113, 13, 8, 10, (CREAM[3], NAP[2], NAP[2], CREAM[2]))
    frame(123, 17, 7, 8, (LEAF[3], LEAF[2], CREAM[3]))
    for y in range(13, 25):  # the calendar on its nail
        for x in range(180, 189):
            c = RED[3] if y < 16 else CREAM_HI if (x + y) % 4 else CREAM[2]
            if y >= 17 and (x - 180) % 3 == 0 and (y - 17) % 3 == 0:
                c = RED[2]  # a day crossed off
            cv.set(x, y, c)
    cv.hline(184, 12, 2, WD[1])
    cv.hline(189, 205, 16, WD[1]); cv.hline(189, 204, 16, WD[3])  # the pan rail by the kitchen door
    for (px, r) in ((193, 3), (201, 2.5)):  # copper pans on their hooks, lit on the west
        cv.vline(px, 206, 3, MATERIALS['iron'][2])
        for (x, y) in oval(px, 212, r, r):
            cv.set(x, y, '#D8945A' if x < px else '#9A5A2E' if x > px else '#B8743E')
        cv.hline(int(px - 1), 211, 2, '#F0C090')
    for (sx, sy) in ((120, 100), (126, 101)):  # slippers by the bed
        cv.hline(sx, sy, 4, NAP[3]); cv.hline(sx, sy + 1, 4, NAP[2]); cv.hline(sx + 3, sy, 1, CREAM_HI)
    cv.hline(124, 276, 6, RED[3]); cv.hline(124, 277, 6, RED[1]); cv.vline(127, 276, 2, CREAM_HI)  # a book left by the chair
    for (x, y) in oval(48, 270, 2.6, 2.2):  # a ball of wool by the basket, and its loose end
        cv.set(x, y, NAP[3] if x + y < 318 else NAP[2])
    for i in range(6):
        cv.set(51 + i, 271 + (i % 2), NAP[2])

    objects = [
        # the bedroom: the bed between its nightstands against the back wall, the desk
        # under the east window, the wardrobe in the corner, the keepsake chest at the
        # bed's foot
        ('bed', 'bed', 64, 54), ('stand-1', 'nightstand', 40, 44), ('stand-2', 'nightstand', 130, 44),
        ('desk', 'desk', 222, 44), ('wardrobe', 'wardrobe', 270, 22), ('chest', 'keepsake_chest', 78, 128),
        # the living room: the hearth built into the back wall with its chimney through
        # the wall's top, the bookcase beside it, the kitchen run along the rest; the
        # basket on the hearth's warm corner, a reading chair before the books by the
        # fire, the table with its chairs by the kitchen
        ('hearth', 'fireplace', 12, 190), ('books', 'bookcase', 90, 194), ('kitchen', 'kitchen', 206, 199),
        ('basket', 'pet_bed', 12, 248), ('chair', 'armchair', 92, 250), ('table', 'dining_table', 226, 262),
        # the sunroom: a window seat and an armchair with its side table along the wall,
        # plants in the corners, coats and boots by the front door
        ('seat', 'window_seat', 20, 432), ('side', 'side_table', 206, 424), ('chair-s', 'armchair', 232, 410),
        ('plant-1', 'plant_tall', 278, 410), ('plant-2', 'plant_tall', 10, 506), ('plant-3', 'plant_tall', 282, 506),
        ('coats', 'coat_rack', 116, 512), ('boots', 'boots', 186, 542), ('can', 'watering_can', 262, 540),
    ]
    stands = {'door': (160, 544), 'bed': (140, 104), 'hearth': (64, 268), 'table': (250, 312),
              'sunroom': (120, 486), 'chest': (95, 162)}  # the keepsake chest: decorating starts here (C12)
    return cv, objects, stands, blocked

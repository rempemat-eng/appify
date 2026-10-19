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
    """Inside the nap hut (living-world plan W4, the house you decorate): a bedroom
    under the back wall's two windows, and through a doorway in the timber partition
    the living room, with the hearth and the companion's basket beside it, an armchair,
    the kitchen run along the partition, a round table, a bookcase and a big plant;
    the front door at the bottom opens on the garden. Warm boards, sun from the
    windows, the fire's glow. The furniture is placed by hand here; decorating (moving
    it, adding keepsakes) comes with C12."""
    PL, WD = MATERIALS['plaster'], MATERIALS['wood']
    GOLD, NAP, CREAM = MATERIALS['gold'], MATERIALS['nap'], MATERIALS['cream']
    cv = Canvas(W, H)
    blocked = set()
    # the floor: long boards, lit along their top edge
    for y in range(H):
        for x in range(W):
            row = y // 8
            off = (row * 53) % 96
            c = WD[3] if noise2((x + off) // 96, row, 520) > 0.5 else WD[2]
            if y % 8 == 0:
                c = WD[1]
            elif y % 8 == 1 and c == WD[3]:
                c = WD[4]
            if (x + off) % 96 == 0:
                c = WD[1]
            cv.set(x, y, c)

    def wall(y0, face, x0=0, x1=W, door=None):
        """A plastered wall seen from the room: a beamed top, the plaster face with
        timber posts, a skirting board; open where the doorway is."""
        for y in range(y0, y0 + face):
            for x in range(x0, x1):
                if door and door[0] <= x < door[1]:
                    continue
                k = y - y0
                c = PL[4]
                if k in (0, 1):
                    c = WD[4] if k == 0 else WD[3]
                elif k < 7:
                    c = WD[1] if k == 6 else WD[2]
                elif (x - x0) % 64 < 4:
                    c = WD[2] if (x - x0) % 64 < 2 else WD[1]  # posts
                elif y > y0 + face - 5:
                    c = WD[2] if y > y0 + face - 3 else WD[3]  # skirting
                cv.set(x, y, c)
                blocked.add((x, y))
        if door:
            for y in range(y0, y0 + face):  # the door frame
                for x in (door[0] - 2, door[0] - 1, door[1], door[1] + 1):
                    cv.set(x, y, WD[3] if x < door[0] else WD[1])
    # the back wall, with two windows onto the garden and a picture between them
    wall(0, 64)
    for wx in (52, 220):
        for y in range(14, 50):
            for x in range(wx, wx + 48):
                c = '#9CC8E0' if y < 30 else '#7EA868' if y < 40 else '#5E8A52'
                if (x - wx) in (0, 1, 23, 24, 46, 47) or (y - 14) in (0, 1, 17, 34, 35):
                    c = WD[3] if (x - wx) < 2 or (y - 14) < 2 else WD[1]
                cv.set(x, y, c)
        cv.hline(wx - 2, 50, 52, WD[4]); cv.hline(wx - 2, 51, 52, WD[2])  # sills
    for y in range(20, 42):  # a picture of the valley
        for x in range(146, 174):
            c = GOLD[3] if x in (146, 173) or y in (20, 41) else '#9CC8E0' if y < 30 else '#6A9468'
            cv.set(x, y, c)
    for (x, y) in disc(166, 25, 2):
        cv.set(x, y, '#F8DD8F')
    # the two partitions with their doorways, and the front wall with the front door
    wall(196, 44, door=(136, 184))
    wall(396, 44, door=(136, 184))
    wall(H - 20, 20, door=(140, 180))
    for (px, py, scene) in ((40, 408, 'sea'), (232, 408, 'hill')):  # pictures on the partition, from the sunroom
        for y in range(py, py + 18):
            for x in range(px, px + 26):
                edge = x in (px, px + 25) or y in (py, py + 17)
                sky = '#9CC8E0' if scene == 'hill' else '#B8D8E8'
                c = WD[1] if edge else sky if y < py + 9 else ('#6A9468' if scene == 'hill' else '#44628E')
                cv.set(x, y, c)
    for k, col in enumerate(('#C2453A', '#3E6A8A', '#E2BC5E')):  # coats on hooks by the door
        hx = 98 + k * 11
        cv.set(hx + 3, 410, WD[1])
        for y in range(412, 430):
            for x in range(hx, hx + 7 - (1 if y < 416 else 0)):
                cv.set(x, y, col if x < hx + 4 else tuple(int(int(col[i:i + 2], 16) * 0.75) for i in (1, 3, 5)) + (255,))
    for (x, y) in disc(110, 214, 7):  # the clock on the upper partition
        cv.set(x, y, CREAM[3] if (x - 110) + (y - 214) < 4 else CREAM[2])
    for (x, y) in disc(110, 214, 7):
        if (x - 110) ** 2 + (y - 214) ** 2 > 36:
            cv.set(x, y, WD[1])
    cv.vline(110, 209, 5, WD[0]); cv.hline(110, 214, 4, WD[0])
    # the sunroom at the front: terracotta tiles under a glazed wall
    for y in range(440, H - 20):
        for x in range(8, W - 8):
            c = '#C8743E' if ((x // 16) + (y // 16)) % 2 else '#B8683A'
            if x % 16 == 0 or y % 16 == 0:
                c = '#8A4A2A'
            cv.set(x, y, c)
    for x in range(8, W - 8):  # the glazing along the partition's foot lets the sun in
        if (x // 16) % 2:
            for y in range(440, 452):
                c = cv.get(x, y)
                cv.set(x, y, tuple(min(255, v + 22) for v in c[:3]) + (255,))
    for x in range(140, 180):  # the doorstep and mat
        for y in range(H - 20, H):
            cv.set(x, y, STONE[3] if y < H - 16 else '#8A6A3A' if (x + y) % 3 else '#A8844A')
    for (x0) in (0, W - 8):  # side walls, seen edge on
        for y in range(64, H - 20):
            for x in range(x0, x0 + 8):
                cv.set(x, y, WD[2] if x in (x0, x0 + 7) else PL[3])
                blocked.add((x, y))
    # sunlight through the back windows on the boards
    for wx in (52, 220):
        for y in range(66, 120):
            for x in range(wx + int((y - 66) * 0.3), wx + 48 + int((y - 66) * 0.3)):
                if (x - wx) % 24 > 1 and (y - 66) % 18 > 1:
                    c = cv.get(x, y)
                    cv.set(x, y, tuple(min(255, v + 18) for v in c[:3]) + (255,))
    # rugs: a long one by the bed, a round one in the living room
    for y in range(150, 186):
        for x in range(48, 160):
            c = RED[3] if ((x - 48) // 6 + (y - 150) // 6) % 2 else RED[2]
            if y in (150, 185) or x in (48, 159):
                c = GOLD[3]
            cv.set(x, y, c)
    for (x, y) in oval(150, 350, 60, 26):
        d = math.hypot((x - 150) / 60, (y - 350) / 26)
        ring = int(d * 6)
        cv.set(x, y, (NAP[2], CREAM[3], NAP[3], RED[3], NAP[2], CREAM[2])[min(5, ring)] if (x + y) % 7 else NAP[1])
    # a woven runner from the front door into the sunroom
    for y in range(470, 552):
        for x in range(142, 178):
            band = (y - 470) // 4 % 4
            c = (NAP[2], CREAM[3], RED[2], CREAM[3])[band] if 146 <= x < 174 else NAP[1]
            if (x + y) % 5 == 0 and 146 <= x < 174:
                c = CREAM[2]
            if x in (142, 177) and y % 2:
                c = CREAM[3]  # the fringe
            cv.set(x, y, c)
    # the hearth's glow on the floor
    light_pool(cv, 52, 300, 46, 18, '#F2721E', skip=frozenset(blocked))
    objects = [
        # the bedroom
        ('bed', 'bed', 64, 70), ('stand-1', 'nightstand', 38, 92), ('stand-2', 'nightstand', 130, 92),
        ('wardrobe', 'wardrobe', 264, 60), ('desk', 'desk', 200, 100), ('chest', 'keepsake_chest', 270, 150),
        # the living room
        ('hearth', 'fireplace', 14, 228), ('basket', 'pet_bed', 72, 282), ('chair', 'armchair', 108, 268),
        ('kitchen', 'kitchen', 206, 226), ('table', 'dining_table', 214, 310), ('books', 'bookcase', 12, 332),
        # the sunroom
        ('seat', 'window_seat', 30, 456), ('plant-1', 'plant_tall', 270, 446), ('plant-2', 'plant_tall', 240, 470),
        ('plant-3', 'plant_tall', 12, 500), ('chair-s', 'armchair', 200, 492),
        ('coats', 'coat_rack', 116, 510), ('boots', 'boots', 186, 544), ('side', 'side_table', 98, 466),
        ('can', 'watering_can', 262, 520),
    ]
    stands = {'door': (160, 544), 'bed': (96, 150), 'hearth': (60, 316), 'table': (240, 366), 'sunroom': (120, 500),
              'chest': (288, 186)}  # the keepsake chest: decorating starts here (C12)
    return cv, objects, stands, blocked

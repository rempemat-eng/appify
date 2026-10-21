"""The Millrace water wheel (Claude B; to-b-2245: the home valley's river threshold, wave 1),
redrawn to the newest standard and built from the house kit (house_kits.py: its walls,
roof, doors, windows, chimney and gutter, in the house palette with light from the upper
left), at the scale table's storeys and door, on a foot of whole 8 px cells.

The mill is the valley's working landmark where the race leaves the river: a drystone
ground floor (the millstones' room) with its ledged door (32 x 14) and deep windows, a
weatherboarded upper floor with the loading door, its hoist beam and a sack on the rope,
a slate roof with the miller's stove chimney at the east end, and on the east wall the
undershot wheel turning in the race between stone walls, its dressed end where the water runs on downstream.
Six frames a 24th of a turn apart loop (paddles and spokes repeat every quarter turn) and
the water spilling off the paddles moves with them.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval  # noqa: E402
import garden_props as gp  # noqa: E402
import house_kits as hk  # noqa: E402
from style_sheet import T, outline, sib  # noqa: E402

W, HT = 112, 112   # drawn size; re-seated so its foot stands where the old 112 x 96 sprite's wall stood
PAD = 16
HX, HW = 4, 72     # the house's west wall and width
ROOF_H, UPPER, GROUND = 30, 28, 44   # the roof, the upper floor and the ground floor (the scale table's storey)


def _house(seed: int = 7) -> Canvas:
    """The mill house from the house kit, on its own canvas (x from its west wall)."""
    h = ROOF_H + UPPER + GROUND + 4
    body = Canvas(HW, h)
    floor2 = ROOF_H + UPPER
    hk.wall(body, 0, ROOF_H, HW, UPPER, 'boards_timber', seed=seed)
    hk.wall(body, 0, floor2, HW, GROUND, 'drystone', seed=seed + 1)
    hk._corners(body, 'drystone', floor2, HW, GROUND)
    for x in range(HW):  # the floor beam between the storeys, lit on top
        body.set(x, floor2, T('timber', 4)); body.set(x, floor2 + 1, T('timber', 1))
    hk.plinth(body, 0, h - 4, HW, 4, 'stone', seed)
    for x in range(HW):  # the plinth's lowest course keeps a step above the outline at the foot
        hk.step(body, x, h - 1, 1)
    hk.roof_mass(body, 0, 0, HW, ROOF_H, 'slate', 'ridge', seed=seed + 2, gable_wall='boards_timber')
    roof = Canvas(HW, ROOF_H)  # this roof is wider than a cottage's, so its slates are cleaned of lone flecks
    for y in range(ROOF_H):
        for x in range(HW):
            roof.set(x, y, body.get(x, y))
    gp.despeckle(roof, passes=2)
    for y in range(ROOF_H):
        for x in range(HW):
            if roof.get(x, y)[3]:
                body.set(x, y, roof.get(x, y))
    hk.gutter(body, 0, HW, ROOF_H)
    hk.downpipe(body, HW - 4, ROOF_H + 3, h - 4)
    hk.doorway(body, 28, h - 5, 14, 32, 'timber', 'ledged', 'stone', seed=seed, lintel='stone')
    hk.doorway(body, 28, floor2 - 1, 14, 20, 'timber', 'ledged', 'timber', seed=seed + 3)  # the loading door
    for wx in (6, 50):
        hk.casement(body, wx, floor2 + 10, 14, 12, frame_fam='timber', cols=2, rows=2, sill='stone', lintel='stone', seed=seed)
        hk.casement(body, wx, ROOF_H + 7, 14, 11, frame_fam='timber', cols=2, rows=1, sill='timber', seed=seed + 1)
    return body


def _wheel(cv: Canvas, turn: float, axle_y: float):
    """The undershot wheel on the east wall, seen nearly edge-on (its axle runs into the
    wall, so its plane runs north-south and we look along it): two iron-shod rims and the
    paddles between them make a tall narrow ellipse beside the wall, the near half over the
    far, eight spokes a face to an iron hub, each surface toned by its normal against the
    upper-left light. Drawn in 3D and projected with the view's foreshortening and skew."""
    X0, r, half = 82.0, 19.0, 3.5
    sq, skew = 0.5, 0.42
    light = (-0.55, 0.35, 0.76)
    toward = (0.0, 0.64, 0.77)
    zbuf = {}

    def put(x, y, z, c):
        px, py = int(round(x + skew * y)), int(round(axle_y + y * sq - z))
        d = y * toward[1] + z * toward[2] + x * 0.001
        if d >= zbuf.get((px, py), -1e9):
            zbuf[(px, py)] = d
            cv.set(px, py, c)

    def tone(n, ramp='timber', lo=2):  # the darkest face stays a step above the outline
        k = max(0.0, n[0] * light[0] + n[1] * light[1] + n[2] * light[2])
        return T(ramp, max(2, lo) + int(k * (6 - max(2, lo)) * 0.999))

    for i in range(41):  # the axle from the wall to the hub
        x = HX + HW + i * (X0 + half + 1 - HX - HW) / 40
        for k in range(12):
            a = 2 * math.pi * k / 12
            put(x, 1.6 * math.cos(a), 1.6 * math.sin(a), tone((0.0, math.cos(a), math.sin(a)), 'iron', 1))
    for side in (-1, 1):  # the rims and their iron tyres
        xf = X0 + side * half
        for i in range(460):
            a = 2 * math.pi * i / 460
            ca, sa = math.cos(a), math.sin(a)
            for t in (r - 2, r - 1.5, r - 1, r - 0.5):
                put(xf, t * ca, t * sa, tone((float(side), 0.0, 0.0), 'timber', 2) if side > 0 else T('timber', 3))
            for dx in (0.0, 0.5, 1.0):
                put(xf - side * dx, r * ca, r * sa, tone((0.0, ca, sa), 'iron', 2))
    for side in (-1, 1):  # eight spokes a face
        xf = X0 + side * (half - 0.5)
        for k in range(8):
            a = 2 * math.pi * k / 8 + 0.2 + turn
            for i in range(60):
                t = 2.5 + i * (r - 4.5) / 60
                put(xf, t * math.cos(a), t * math.sin(a), T('timber', 3) if side > 0 else T('timber', 2))
    for k in range(16):  # the paddles, wet and dark on their faces
        a = 2 * math.pi * k / 16 + turn
        ca, sa = math.cos(a), math.sin(a)
        n = (0.0, -sa, ca)
        if n[1] * toward[1] + n[2] * toward[2] < 0:
            n = (0.0, sa, -ca)
        for i in range(17):
            x = X0 - half + i * (2 * half) / 16
            for j in range(11):
                t = r - 2 + j * 0.5
                c = T('timber', 2) if i in (0, 16) else tone(n, 'timber', 2) if j < 10 else T('timber', 5)
                put(x, t * ca, t * sa, c)
    for i in range(48):  # the iron hub and its strap
        a = 2 * math.pi * i / 48
        for t in (0.5, 1.2, 2.0, 2.8):
            put(X0 + half + 0.6, t * math.cos(a), t * math.sin(a), T('iron', 4) if t < 1.5 and math.sin(a) > 0 else T('iron', 2))


def water_mill(turn: float = 0.0) -> Canvas:
    cv = Canvas(W, HT, pad=PAD)
    foot = HT - 1
    body = _house()
    top = HT - body.h  # the house stands on the foot line
    hk.chimney(cv, HX + 56, top - 12, 16, 'stone')  # the miller's stove at the east gable, behind the roof
    for y in range(body.h):
        for x in range(body.w):
            c = body.get(x, y)
            if c[3]:
                cv.set(HX + x, top + y, c)
    for yy in range(top, top + 4):  # the stack's shadow on the slates to its east
        for xx in (HX + 65, HX + 66):
            hk.step(cv, xx, yy, -1)
    floor2 = top + ROOF_H + UPPER
    base = foot - 4
    for k in range(10):  # the hoist beam over the loading door, its pulley, the rope and a sack on the hook
        cv.set(HX + 24 + k, top + ROOF_H + 2, T('timber', 4)); cv.set(HX + 24 + k, top + ROOF_H + 3, T('timber', 2))
    for (x, y) in oval(HX + 25, top + ROOF_H + 5, 1.6, 1.6):
        cv.set(x, y, T('iron', 4 if x < HX + 25 else 2))
    for y in range(top + ROOF_H + 6, floor2 + 6):
        cv.set(HX + 25, y, T('sand_cool', 4 if y % 3 else 3))
    for y in range(floor2 + 6, floor2 + 14):
        half = 2 if y < floor2 + 8 else 3
        cv.hline(HX + 25 - half, y, 2 * half + 1, T('sand_cool', 4 if y < floor2 + 10 else 3 if y < floor2 + 12 else 2))
        cv.set(HX + 25 + half, y, T('sand_cool', 2))
    for (x, y) in oval(HX + 51, base - 6, 6, 6):  # a broken millstone leaning by the door, its eye and furrows
        d = math.hypot(x + 0.5 - HX - 51, y + 0.5 - base + 6)
        lit = (x - HX - 51) + (y - base + 6) < -1
        cv.set(x, y, T('stone', 0) if d < 1.5 else T('stone', 2) if abs(d - 3.8) < 0.5 else T('stone', 5 if lit else 3))
    for (sx, sh) in ((HX + 10, 9), (HX + 16, 7)):  # sacks of grain waiting to go in
        for y in range(base - sh + 1, base + 1):
            cv.hline(sx, y, 5, T('sand_cool', 4 if y < base - sh + 3 else 3 if y < base - 1 else 2))
        cv.set(sx + 2, base - sh, T('sand_cool', 2))
    race_y = foot - 12  # the race: its stone walls and the dark channel under the wheel
    for x in range(HX + HW, 95):
        for y in range(race_y, foot):
            if y < race_y + 3:
                cv.set(x, y, T(sib('stone', noise2(x // 6, 0, 405), 0.3), 5 if y == race_y else 3 if x < 96 else 2))
            else:
                v = y - race_y - 3
                cv.set(x, y, T('water', 3 if v < 2 else 2))
        cv.set(x, foot, T('stone', 3))
    for y in range(race_y - 1, foot + 1):  # the race wall's dressed end, where the water runs on downstream
        cv.hline(93, y, 2, T('stone', 4 if y == race_y - 1 else 2))
    _wheel(cv, turn, axle_y=foot - 33.0)
    phase = int(round(turn / (math.pi / 24))) % 6
    for i in range(5):  # water spilling off the paddles as they rise
        x = 76 + i * 4 + (phase + i) % 2
        y0 = foot - 52 + (phase * 4 + i * 7) % 18
        for k in range(3):
            cv.set(x, y0 + k, T('water', 5 if k == 0 else 4))
        cv.set(x - 1, y0 + 3, T('water', 3))
    for x in range(HX + HW, 92):  # white water churning under the wheel
        f = (x + phase * 3) % 7
        if f in (0, 1, 3):
            cv.set(x, race_y + 4 + (x + phase) % 2, T('water', 5) if f == 0 else T('snow', 5))
    for (gx, gy) in ((HX - 2, foot), (HX - 1, foot - 1), (HX - 2, foot - 1), (48, foot), (49, foot)):
        cv.set(gx, gy, T('grass', 3))  # grass at the wall's foot
    _fold_rare(cv, limit=110)
    out = Canvas(W + 2, HT + 2 + PAD, pad=PAD)  # the house outline, in each material's edge tone (style_sheet.outline)
    for y in range(-PAD, HT):
        for x in range(W):
            c = cv.get(x, y)
            if c[3]:
                out.set(x + 1, y + 1 + PAD, c)
    outline(out)
    floor2_body = ROOF_H + UPPER
    for wx in (6, 50):  # the window panes, lit warm at night where the zone has no light of its own
        for (wy, ww, wh) in ((floor2_body + 10, 14, 12), (ROOF_H + 7, 14, 11)):
            gp.WINDOWS.append((out, (HX + wx + 1 + 3, top + wy + 1 + PAD + 3, ww - 5, wh - 5)))
    return gp.keep_foot(out, 112, 87, dx=-1)  # its foot on row 86 of the old 112 x 96 box, where the zones expect the wall


def _fold_rare(cv: Canvas, limit: int):
    """A building this size gathers more tones than the style's 128 (the kit's walls and roof,
    the wheel, the race), so the rarest few, a handful of pixels each, take the nearest tone
    already used more widely (in Oklab), until the count is under the limit."""
    import house_palette as hp
    p = cv.pad
    count = {}
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            c = cv.get(x, y)
            if c[3] == 255:
                count[c] = count.get(c, 0) + 1
    if len(count) <= limit:
        return
    keep = sorted(count, key=count.get, reverse=True)[:limit]
    lab = {c: hp.to_oklab(c) for c in count}
    remap = {}
    for c in count:
        if c in keep:
            continue
        remap[c] = min(keep, key=lambda k: sum((a - b) ** 2 for a, b in zip(lab[c], lab[k])))
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            c = cv.get(x, y)
            if c in remap:
                cv.set(x, y, remap[c])

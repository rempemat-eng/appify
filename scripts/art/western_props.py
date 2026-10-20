"""Props for Dust Gulch, the western desert town (world-atlas.md).

The valley's rules under a harder sun: sun-bleached boards, adobe walls, long cast
shadows, cactus shaded as cylinders, everything dusty at its foot.
Run directly for a contact sheet: python3 scripts/art/western_props.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import reach_detail as rd  # noqa: E402
import garden_props as gp  # noqa: E402
import reach_house as rh  # noqa: E402
from reach_house import T, sib, part, rect, step, frame  # noqa: E402
import style_sheet as ss  # noqa: E402
from style_sheet import boards, grain as ss_grain  # noqa: E402
from materials import MATERIALS, WOOD, STONE, RED, WTR, GOLD  # noqa: E402

DESERT, CACTUS, ADOBE = (MATERIALS[k] for k in ('desert', 'cactus', 'adobe'))
IRON = MATERIALS['iron']
BLEACHED = MATERIALS['bleached']  # sun-bleached boards
ROPE = MATERIALS['rope']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def _glass(tones, x: int, y: int, w: int, h: int):
    """Window glass seen from a sunlit street: dark under the porch's shadow at the top,
    the room's dusk behind it, and two slanting streaks of reflected street light."""
    c = tones[0] if y < 3 else tones[1] if y < h * 0.6 else tones[2]
    t = x + y * 0.6
    if 3 <= t % 17 < 6:
        c = rd.mix(c, (210, 228, 236), 0.4)
    return c


def false_front(width: int = 104, seed: int = 0, sign_ramp=RED, kind: str = 'saloon') -> Canvas:
    """A false-front building, `width` x 108, at the people's scale (verticality.md 5: a
    shop's ground storey about 44 px, its door 32 px tall, an adult 25): the tall square
    facade hides a pitched tin roof (its top shows behind), bleached clapboards, a sign
    board with a pictogram (a mug or a sack), an upper window, a porch roof on posts that
    throws a deep shadow, and on the ground storey swinging half doors in a 22 x 32
    doorway (a saloon) or a 16 x 32 glazed door between two display windows (a store)."""
    w, h = width, 108
    cv = Canvas(w, h, pad=PAD)
    # the tin roof behind the facade, seen from above
    for y in range(2, 20):
        for x in range(10, w - 10):
            c = rd.rgb(IRON[3] if (x // 4) % 2 else IRON[2])
            if x % 4 == 0:
                c = rd.step(c, 1.2)              # the lit crest of each corrugation
            n = rd.smooth_noise(x, y, 5, seed + 41)
            if n < 0.3:
                c = rd.mix(c, (150, 88, 54), 0.5 if n < 0.18 else 0.3)   # rust in patches
            elif n > 0.8:
                c = rd.mix(c, (190, 176, 150), 0.25)                    # dust settled on it
            rd.put(cv, x, y, c)
        cv.hline(10, 2, w - 20, IRON[4])
    # the facade: stepped top, clapboards
    face = {(x, y) for x in range(4, w - 4) for y in range(14, h - 6)}
    face |= {(x, y) for x in range(14, w - 14) for y in range(8, 14)}
    # weathered boards of four woods and an old coat of the sign's paint, bleached most
    # high up, dusty at the boardwalk (D13: Eastward's level of detail)
    # (20 Oct, Claude A: one weathered timber, not a mix of pinkish, grey and tan boards;
    # fewer gaps, and those in groups where the wall has worked loose)
    woods = ('#AE9278', '#A88E76', '#B2967C', '#A48A72')
    rd.planks(cv, face, woods, seed=seed + 5, board=4, foot=h - 6, gaps=0.5, gap_groups=True)
    for (x, y) in face:
        if (x, y - 1) not in face:
            cv.set(x, y, BLEACHED[5])
            cv.set(x, y + 1, BLEACHED[4])
    cv.hline(4, 13, 10, BLEACHED[1]); cv.hline(w - 14, 13, 10, BLEACHED[1])
    # the sign board
    sx0, sx1, sy0, sy1 = 18, w - 18, 17, 29
    # painted boards, the paint worn through to the wood in places
    paint = (sign_ramp[2], rd.step(sign_ramp[2], 0.4), rd.mix(sign_ramp[2], '#B39277', 0.25))
    rd.planks(cv, rect_set(sx0, sy0, sx1 - sx0, sy1 - sy0), paint, seed=seed + 9, board=4,
              bleach=rd.mix(sign_ramp[3], '#E4CCB2', 0.4), bleach_top=0.3, gaps=0.0, length=(20, 40))
    for (x, y) in rect_set(sx0, sy0, sx1 - sx0, sy1 - sy0):
        if rd.smooth_noise(x, y, 3, seed + 17) < 0.14:
            rd.put(cv, x, y, '#A68266' if y % 4 else '#7E604C')     # paint flaked off
    cv.hline(sx0, sy0, sx1 - sx0, sign_ramp[3])
    cv.hline(sx0, sy1, sx1 - sx0, sign_ramp[0])
    for (nx, ny) in ((sx0 + 1, sy0 + 2), (sx1 - 2, sy0 + 2), (sx0 + 1, sy1 - 2), (sx1 - 2, sy1 - 2)):
        cv.set(nx, ny, '#3E363C'); cv.set(nx, ny + 1, '#7C4E36')   # its nails, rust below
    ink = '#F4E6C8'
    # a pictogram, not lettering (letters at this size read as nonsense words): a frothy
    # mug for the saloon, a tied sack for the store, with small diamonds either side
    mx = (sx0 + sx1) // 2
    if kind == 'saloon':
        for y in range(21, 28):
            cv.hline(mx - 4, y, 7, '#E8B04A' if y > 22 else ink)  # the mug, its froth on top
        cv.hline(mx - 4, 20, 7, ink); cv.set(mx - 3, 19, ink); cv.set(mx, 19, ink)
        cv.vline(mx + 3, 22, 4, ink); cv.vline(mx + 4, 22, 4, ink); cv.set(mx + 4, 22, sign_ramp[2]); cv.set(mx + 4, 25, sign_ramp[2])
        cv.vline(mx - 2, 23, 4, '#C8862A')
    else:
        for (x, y) in oval(mx, 24, 4.5, 3.6):
            cv.set(x, y, ink if x < mx + 1 else '#D8C8A0')  # the sack
        cv.hline(mx - 2, 20, 5, ink); cv.hline(mx - 1, 21, 3, '#C8862A')  # its tied neck
    for dx in (-14, -9, 9, 14):
        if sx0 + 2 < mx + dx < sx1 - 2:
            x = mx + dx
            cv.set(x, 22, ink); cv.set(x - 1, 23, ink); cv.set(x + 1, 23, ink); cv.set(x, 24, ink)
    # the upper storey's window with a sill (16 x 12, the table's window)
    gp.window(cv, w // 2 - 8, 34, 16, 14, shutters=None, sill=True, warm=False)
    # the porch roof and its posts
    py = 58
    for x in range(0, w):
        for y in range(py, py + 5):
            cv.set(x, y, BLEACHED[4] if y == py else BLEACHED[2] if y < py + 4 else BLEACHED[0])
    rd.shadow_band(cv, 4, w - 4, py + 5, lambda x: 6 + (x * 3) // w, k=2.2)
    # the posts run unbroken from the porch roof to the boardwalk (Matt, 20 Oct 10:15); at
    # the store they stand either side of the door, so the display windows sit between them
    dw0 = 22 if kind == 'saloon' else 16
    dx0 = w // 2 - dw0 // 2
    posts = (2, w // 3 - 6, 2 * w // 3 + 4, w - 5) if kind == 'saloon' else (2, dx0 - 6, dx0 + dw0 + 3, w - 5)
    for px in posts:
        gp.post(cv, px, py + 5, h - 4, w=3, ramp=BLEACHED)
    # the ground storey: the doorway stands on the boardwalk, 32 px tall
    foot = h - 6
    top = foot - 32
    if kind == 'saloon':
        dw = 22
        dx = w // 2 - dw // 2
        for (x, y) in rect_set(dx, top, dw, 32):  # the dark room inside
            cv.set(x, y, '#2A1C16' if y > top + 2 else '#3A2820')
        for (x, y) in rect_set(dx - 2, top - 2, dw + 4, 2):  # the lintel
            cv.set(x, y, BLEACHED[1] if y == top - 1 else BLEACHED[4])
        for y in range(top, foot):  # the jambs
            cv.set(dx - 1, y, BLEACHED[4]); cv.set(dx + dw, y, BLEACHED[1])
        for half in (0, dw // 2):  # the swinging half doors, hung at chest height
            for (x, y) in rect_set(dx + half, top + 9, dw // 2, 13):
                cv.set(x, y, WOOD[3] if (x - dx) % 3 else WOOD[2])
            cv.hline(dx + half, top + 9, dw // 2, WOOD[4]); cv.hline(dx + half, top + 21, dw // 2, WOOD[1])
        for (x, y) in rect_set(dx + 2, top + 22, dw - 4, 10):
            if (x + y) % 5 == 0:
                cv.set(x, y, '#4A3228')  # the floor inside, glimpsed under the doors
    else:
        dw = 16
        dx = w // 2 - dw // 2
        glass = ((44, 58, 82), (62, 86, 118), (92, 122, 150))
        for (x, y) in rect_set(dx, top, dw, 32):  # a glazed door: a panel below, glass above
            if y > top + 18:
                c = rd.step(WOOD[2], 0.6 if (x - dx) in (2, 3) else -0.8 if (x - dx) == dw - 3 else 0)
                if y in (top + 21, top + 29) and 2 <= x - dx < dw - 2:
                    c = rd.step(WOOD[2], -1.4)            # the panel's mouldings
            else:
                c = _glass(glass, x - dx, y - top, dw, 18)
            if x in (dx, dx + dw - 1) or y in (top, top + 18):
                c = rd.rgb(WOOD[1])
            rd.put(cv, x, y, c)
        cv.set(dx + dw - 4, top + 17, GOLD[3]); cv.set(dx + dw - 4, top + 18, GOLD[1])  # its handle
        for (x, y) in rect_set(dx - 2, top - 2, dw + 4, 2):
            cv.set(x, y, BLEACHED[1] if y == top - 1 else BLEACHED[4])
        goods = ((GOLD, 'jar'), (RED, 'can'), (WTR, 'jar'), (ADOBE, 'sack'), (WOOD, 'box'))
        for side, (wx0, ww) in enumerate(((8, dx - 16), (dx + dw + 9, w - (dx + dw + 9) - 8))):  # the display windows, between the posts
            wy0 = top + 4
            gp.WINDOWS.append((cv, (wx0, wy0, ww, 20)))  # its pane lights up at night (zoneWindows)
            for (x, y) in rect_set(wx0, wy0, ww, 20):
                rd.put(cv, x, y, _glass(glass, x - wx0, y - wy0, ww, 20))
            # two shelves of goods behind the glass, each lit on its left
            for sy, gh in ((wy0 + 9, 5), (wy0 + 17, 6)):
                cv.hline(wx0, sy, ww, WOOD[1])
                gx, k = wx0 + 1, side * 2 + (sy & 1)
                while gx < wx0 + ww - 3:
                    ramp, form = goods[k % len(goods)]
                    gw = 3 if form in ('jar', 'can') else 4
                    if gx + gw > wx0 + ww - 1:
                        break
                    for yy in range(sy - gh + (1 if form == 'can' else 0), sy):
                        for xx in range(gx, gx + gw):
                            c = ramp[3] if xx == gx else ramp[1] if xx == gx + gw - 1 else ramp[2]
                            if yy == sy - gh + (1 if form == 'can' else 0):
                                c = ramp[4] if form != 'sack' else ramp[3]   # a lid, a cap, a tied top
                            if form == 'jar' and yy == sy - 3:
                                c = '#E8DCC0'                              # its label
                            cv.set(xx, yy, c)
                    gx += gw + 1
                    k += 1
            # the glass's reflection over the goods: two slanting streaks of the bright street
            for (x, y) in rect_set(wx0, wy0, ww, 20):
                t = (x - wx0) + (y - wy0) * 0.6
                if 3 <= t % 17 < 6:
                    rd.put(cv, x, y, rd.mix(cv.get(x, y), (210, 228, 236), 0.45))
            cv.hline(wx0 - 1, wy0 + 20, ww + 2, BLEACHED[4])  # the sill
            cv.hline(wx0 - 1, wy0 + 21, ww + 2, BLEACHED[1])
            cv.vline(wx0 - 1, wy0, 20, BLEACHED[1]); cv.vline(wx0 + ww, wy0, 20, BLEACHED[1])
            cv.hline(wx0 - 1, wy0 - 1, ww + 2, BLEACHED[1])
    # the boardwalk at the foot
    rd.planks(cv, rect_set(0, h - 6, w, 6), woods, seed=seed + 7, board=5, vertical=True,
              bleach_top=0.2, length=(9, 12), gaps=0.25, nails=False)
    cv.hline(0, h - 6, w, BLEACHED[5])
    for x in range(0, w):
        if rd.smooth_noise(x, 0, 3, seed + 51) < 0.35:
            cv.set(x, h - 1, BLEACHED[1])   # the boards' worn front ends
    return cv


def store() -> Canvas:
    """Dust Gulch's general store, 88 x 108 (asset ledger 20 Oct: redrawn on the house
    ramps; prop audit ADJUST "doors 25" now a shop's pair of doors 22 x 32). A false
    front of bleached boards hides a tin roof (its rusty top shows behind); a cornice caps
    the stepped parapet and throws a band; the sign board is painted faded blue with a
    tied sack, the paint worn back to the wood; the upper window has its frame and sill.
    A porch roof of corrugated iron on unbroken posts throws the ground storey into shade:
    two display windows of goods on shelves either side of a pair of glazed doors under a
    lintel, a stone step, sacks on the boardwalk against the bulkhead. Footing: the
    boardwalk, 11 cells wide."""
    w, h = 88, 108
    cv = Canvas(w, h, pad=PAD)
    foot = h - 6                                   # the boardwalk's top
    for y in range(2, 16):                         # the tin roof behind the facade, seen from above
        for x in range(12, w - 12):
            j = x % 4
            k = 4 if j == 0 else 3 if j == 1 else 2
            if y == 2:
                k = 5 if j == 0 else 4
            rust = smooth_noise(x // 2, y, 4, 141) > 0.68 and 2 < y < 15
            cv.set(x, y, T('clay_cool', k - 1) if rust else T('iron', k))
    face = rect(4, 14, w - 8, foot - 14) | rect(14, 8, w - 28, 6)
    woods = lambda bi, si: (('bleached', 'bleached_warm', 'bleached_cool')[int(noise2(bi, si, 143) * 3)],
                            3 + (1 if bi < 4 else 0) - (1 if noise2(bi, si, 144) < 0.14 else 0))
    boards(cv, 4, 8, w - 8, foot - 8, woods, board=4, seed=145, clip=face)
    ss_grain(cv, {p for p in face if p[1] < 58}, 0.09, 146, shapes=rh.H_GRAIN, lit=lambda x, y: 1 - y / h)
    for (x0, x1, y) in ((14, w - 14, 7), (4, 14, 13), (w - 14, w - 4, 13)):   # the cornice on each step
        for x in range(x0 - 1, x1 + 1):
            cv.set(x, y, T('timber', 4 if x < w // 2 else 3)); cv.set(x, y + 1, T('timber', 2))
        rh.overhang(cv, x0, x1, y + 2, 1)
    sx0, sx1, sy0, sy1 = 18, w - 18, 18, 30       # the sign board, faded blue paint worn back to the wood
    boards(cv, sx0, sy0, sx1 - sx0, sy1 - sy0, lambda b, si: (('sky', 'sky_cool')[si % 2], 3), board=4, seed=147,
           nails=False, grain=0.04)
    for (x, y) in rect(sx0, sy0, sx1 - sx0, sy1 - sy0):
        if smooth_noise(x, y, 2.5, 148) > 0.78 and (y - sy0) % 4 in (1, 2):
            cv.set(x, y, T('bleached', 4 if (y - sy0) % 4 == 1 else 3))
    frame(cv, sx0 - 1, sy0 - 1, sx1 - sx0 + 2, sy1 - sy0 + 2, 'bleached', 2, t=1)
    for (nx, ny) in ((sx0, sy0 + 1), (sx1 - 1, sy0 + 1), (sx0, sy1 - 2), (sx1 - 1, sy1 - 2)):
        cv.set(nx, ny, T('iron', 1)); cv.set(nx, ny + 1, T('clay_cool', 2))   # its nails, rust run below
    mx = w // 2
    for (x, y) in rh.ellipse(mx + 0.5, 25.5, 4.5, 3.6):   # the sack pictogram
        cv.set(x, y, T('plaster', 5 if x < mx + 1 else 4))
    cv.hline(mx - 2, 21, 5, T('plaster', 5)); cv.hline(mx - 1, 22, 3, T('brass', 3))
    for dx in (-14, -9, 9, 14):
        x = mx + dx
        for (ex, ey) in ((0, 0), (-1, 1), (1, 1), (0, 2)):
            cv.set(x + ex, 23 + ey, T('plaster', 5))
    wx, wy = mx - 8, 36                           # the upper window, frame and sill
    frame(cv, wx, wy, 16, 14, 'bleached', 3, t=2)
    ss.glass(cv, wx + 2, wy + 2, 12, 10, False)
    gp.WINDOWS.append((cv, (wx + 2, wy + 2, 12, 10)))   # a room upstairs: its pane lights up at night
    cv.vline(mx - 1, wy + 2, 10, T('bleached', 2)); cv.hline(wx + 2, wy + 6, 12, T('bleached', 4))
    part(cv, wx - 2, wy + 14, 20, 3, 'bleached', 4)
    rh.overhang(cv, wx - 1, wx + 19, wy + 17, 2)
    py = 58                                        # the porch roof: corrugated iron, rust, lit crests
    for y in range(py, py + 6):
        for x in range(w):
            j = x % 4
            k = 4 if j == 0 else 3 if j == 1 else 2
            if y == py:
                k = 5 if j == 0 else 4
            if y == py + 5:
                k = 1
            rust = smooth_noise(x // 2, y, 5, 149) > 0.7 and py < y < py + 5
            cv.set(x, y, T('clay_cool', k - 1) if rust else T('iron', k))
    under = rect(4, py + 6, w - 8, foot - py - 6)  # the ground storey in the porch's shade
    boards(cv, 4, py + 6, w - 8, foot - py - 6, lambda b, si: (('bleached', 'bleached_cool')[si % 2], 2),
           board=4, seed=150, nails=False, grain=0.06)
    ss_grain(cv, under, 0.09, 153, shapes=rh.H_GRAIN, lit=lambda x, y: 0.3)
    rh.overhang(cv, 4, w - 4, py + 6, 3)
    dw, dtop = 22, foot - 32                       # the pair of glazed doors, 22 x 32
    dx = mx - dw // 2
    for (x, y) in rect(dx - 2, dtop - 2, dw + 4, 2):   # the lintel
        cv.set(x, y, T('timber', 3 if y == dtop - 2 else 1))
    for leaf in (0, 1):
        lx = dx + leaf * (dw // 2)
        frame(cv, lx, dtop, dw // 2, 32, 'timber', 2, t=1)
        ss.glass(cv, lx + 1, dtop + 1, dw // 2 - 2, 17, False)
        for (x, y) in rect(lx + 1, dtop + 19, dw // 2 - 2, 12):
            cv.set(x, y, T('timber', 2))
        part(cv, lx + 2, dtop + 21, dw // 2 - 4, 8, 'timber', 2)    # the raised panel
        cv.hline(lx + 1, dtop + 18, dw // 2 - 2, T('timber', 3))
    cv.set(mx - 2, dtop + 17, T('brass', 4)); cv.set(mx + 1, dtop + 17, T('brass', 4))   # the handles
    cv.set(mx - 2, dtop + 18, T('brass', 2)); cv.set(mx + 1, dtop + 18, T('brass', 2))
    part(cv, dx - 3, foot - 2, dw + 6, 3, 'stone', 3)  # the stone step
    posts = (2, dx - 6, dx + dw + 3, w - 5)
    goods = (('brass', 'jar'), ('clay', 'can'), ('sky', 'jar'), ('adobe', 'sack'), ('timber', 'box'))
    for side, (wx0, ww) in enumerate(((8, dx - 6 - 10), (dx + dw + 9, w - 5 - (dx + dw + 9) - 3))):
        wy0 = dtop + 4
        frame(cv, wx0 - 1, wy0 - 1, ww + 2, 22, 'bleached', 2, t=1)
        ss.glass(cv, wx0, wy0, ww, 20, False)
        gp.WINDOWS.append((cv, (wx0, wy0, ww, 20)))   # its pane lights up at night (zoneWindows)
        for sy, gh in ((wy0 + 9, 5), (wy0 + 17, 6)):   # two shelves of goods behind the glass
            cv.hline(wx0, sy, ww, T('timber', 1))
            gx, k = wx0 + 1, side * 2 + (sy & 1)
            while True:
                fam, form = goods[k % len(goods)]
                gw = 3 if form in ('jar', 'can') else 4
                if gx + gw > wx0 + ww - 1:
                    break
                y0 = sy - gh + (1 if form == 'can' else 0)
                for yy in range(y0, sy):
                    for xx in range(gx, gx + gw):
                        t = 3 if xx == gx else 1 if xx == gx + gw - 1 else 2
                        if yy == y0:
                            t = 4 if form != 'sack' else 3
                        if form == 'jar' and yy == sy - 3:
                            cv.set(xx, yy, T('plaster', 4 if xx == gx else 3))   # its label
                            continue
                        cv.set(xx, yy, T(fam, t))
                gx += gw + 1
                k += 1
        for i in range(3):                         # one glint across the pane, in two-pixel steps
            cv.set(wx0 + 2 + i, wy0 + 6 - 2 * i, T('slate', 4)); cv.set(wx0 + 2 + i, wy0 + 5 - 2 * i, T('slate', 4))
        part(cv, wx0 - 2, wy0 + 21, ww + 4, 2, 'bleached', 3)   # the sill
    for (nx0, ny0, fam) in ((22, py + 12, 'plaster'), (63, py + 9, 'plaster_warm')):   # bills tacked to the wall
        for (x, y) in rect(nx0, ny0, 4, 5):
            cv.set(x, y, T(fam, 4 if y == ny0 else 3))
        cv.hline(nx0 + 1, ny0 + 2, 2, T('clay', 2)); cv.hline(nx0 + 1, ny0 + 3, 2, T('soot', 3))
        cv.set(nx0 + 1, ny0, T('iron', 1))
    for px in posts:                               # the posts run unbroken from the porch roof to the boardwalk
        rh.cylinder(cv, px, py + 6, 3, foot - py - 6, 'bleached', 3)
    for (sx, sy, fam) in ((10, foot - 6, 'sand'), (15, foot - 5, 'sand_warm')):   # sacks against the bulkhead
        for (x, y) in rh.ellipse(sx + 2.5, sy + 3, 2.6, 3.0):
            cv.set(x, y, T(fam, 4 if x < sx + 2 else 3 if y < sy + 4 else 2))
        cv.hline(sx + 1, sy, 3, T('brass', 3))
    for x in range(w):                             # the boardwalk at the foot, boards across, worn ends
        for y in range(foot, h - 1):
            cv.set(x, y, T(('timber', 'timber_warm')[(x // 8) % 2], 4 if y == foot else 3 if y < h - 2 else 2))
        if x % 8 == 0:
            cv.set(x, foot + 1, T('timber', 1)); cv.set(x, foot + 2, T('timber', 1))
        cv.set(x, h - 1, T('timber', 1 if smooth_noise(x, 0, 3, 151) < 0.4 else 2))
    return rh.finish(cv)


def water_tower() -> Canvas:
    """A wooden water tank on a trestle, 48 x 96, with iron hoops and a spout."""
    w, h = 48, 96
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(24, 8, 21, 6):  # the conical lid, seen from above
        cv.set(x, y, BLEACHED[4] if x < 24 else BLEACHED[2])
    cv.set(24, 2, BLEACHED[5])
    tank = rect_set(4, 8, 40, 34)
    detail.boards(cv, tank, BLEACHED, 3, 8, board=4, vertical=True, x0=4, grain=0.05)
    for x in range(4, 44):
        k = (x - 4) / 40
        for y in range(8, 42):
            if k > 0.62:
                detail.shade(cv, x, y, 1)
            if k < 0.12:
                detail.shade(cv, x, y, -1)
    for hy in (14, 26, 38):
        cv.hline(4, hy, 40, IRON[3]); cv.hline(4, hy + 1, 40, IRON[1])
    for (x, y) in oval(24, 42, 20, 3):
        if y >= 42:
            cv.set(x, y, BLEACHED[1])
    for lx in (8, 20, 28, 40):  # the trestle
        gp.post(cv, lx, 44, h - 2, w=3, ramp=BLEACHED)
    for y0 in (56, 74):
        for t in range(32):
            cv.set(9 + t, y0 + t // 3 % 2, BLEACHED[2])
        for t in range(32):
            cv.set(9 + t, y0 + 10 - (t * 10 // 32), BLEACHED[1])
    cv.rect(40, 30, 6, 3, IRON[2])
    cv.vline(45, 33, 6, IRON[2])
    return cv


def saguaro(tall: bool = True) -> Canvas:
    """A saguaro cactus, 30 x 54 (or 22 x 36): ribbed cylinders lit on the left, arms
    that turn upward, spines picked out on the lit side."""
    w, h = (30, 54) if tall else (22, 36)
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2

    def cyl(x0, y0, y1, r):
        for y in range(y0, y1):
            for x in range(x0 - r, x0 + r + 1):
                k = (x - (x0 - r)) / (2 * r + 1)
                c = CACTUS[4] if k < 0.2 else CACTUS[3] if k < 0.45 else CACTUS[2] if k < 0.75 else CACTUS[1]
                if (x - x0) % 3 == 0 and k > 0.2:
                    c = CACTUS[max(0, CACTUS.index(c) - 1)]
                cv.set(x, y, c)
        for (x, y) in disc(x0, y0, r):
            if y <= y0:
                cv.set(x, y, CACTUS[4] if x < x0 else CACTUS[3])

    cyl(cx, 4, h - 2, 5 if tall else 4)
    if tall:
        cv_arm = [(cx - 11, 14, cx - 11, 30), (cx + 11, 20, cx + 11, 34)]
        for (ax, ay, bx, by) in cv_arm:
            cyl(ax, ay, by, 3)
            for x in range(min(ax, cx), max(ax, cx) + 1):
                for y in range(by - 3, by + 3):
                    cv.set(x, y, CACTUS[2] if y > by else CACTUS[3])
    else:
        cyl(cx + 7, 12, 22, 3)
        for x in range(cx, cx + 8):
            for y in range(19, 24):
                cv.set(x, y, CACTUS[2] if y > 21 else CACTUS[3])
    for y in range(6, h - 4, 4):
        cv.set(cx - 3, y, '#F1E6C0')
    cv.set(cx, 3, RED[3]); cv.set(cx + 1, 2, RED[4])  # a flower on top
    return cv


def tumbleweed() -> Canvas:
    """A tumbleweed, 16 x 14: a tangle of dry twigs."""
    cv = Canvas(16, 14, pad=PAD)
    for k in range(60):
        a = noise2(k, 0, 203) * 2 * math.pi
        r = noise2(k, 1, 203) * 6
        x, y = int(8 + r * math.cos(a)), int(7 + r * math.sin(a) * 0.85)
        cv.set(x, y, DESERT[2] if x + y < 15 else DESERT[0])
        cv.set(x + 1, y, DESERT[1])
    return cv


def wagon() -> Canvas:
    """A covered wagon, 66 x 46, in three-quarter view (prop audit, ADJUST: "side view,
    spoked wheels flat"; asset ledger 20 Oct). Seen from the south and above like every
    prop: the canvas bonnet's top plane catches the light and its south side falls away in
    panels between the hoops, flaring at both ends; the west end is drawn up on its
    puckering string over a dark opening with a sack inside. The bed is lapped boards
    between a lit top rail and a dark sill, held by wooden standards; the wheels are ellipses
    (iron tyres, jointed felloes, spokes), the rear ones larger. A water barrel rides on
    the south side, a jockey box at the front, the brake lever by the rear wheel, the
    tongue out west. Footing: the four wheels; its foot line spans 8 cells.
    All on the house ramps (bleached and timber boards, plaster canvas, iron)."""
    w, h = 72, 48
    cv = Canvas(w, h, pad=PAD)
    x0, x1 = 9, 63                       # the bed, west to east
    bed_top, bed_bot = 26, 35
    # the bonnet: a long half cylinder over hoops, its ends flared up and out
    hoops = [16, 24, 32, 40, 48, 56]
    hx0, hx1 = x0 - 2, x1 + 2
    hood, prof = set(), {}
    for x in range(hx0, hx1 + 1):
        u = (x - hx0) / (hx1 - hx0)
        y_top = 7 + round(1.4 * math.sin(u * math.pi)) - round(4 * max(0.0, abs(u - 0.5) * 2 - 0.72) / 0.28)
        end = min(x - hx0, hx1 - x)
        if end < 2:
            y_top += 2 - end                         # the rounded corner of each flared end
        prof[x] = y_top
        for y in range(y_top, bed_top):
            hood.add((x, y))
    for (x, y) in hood:
        span = bed_top - prof[x]
        u = (y - prof[x]) / span
        k = 4 if u < 0.22 else 3 if u < 0.62 else 2 if u < 0.88 else 1
        panel = sum(1 for hx in hoops if x >= hx)
        fam = ('plaster', 'plaster_warm', 'plaster_cool')[(panel * 2 + 1) % 3]
        hv = [x - hx for hx in hoops]
        if 0 in hv and u > 0.18:
            k += 1                                   # the hoop pushes the cloth out: a lit ridge
        elif 1 in hv and 0.22 < u < 0.9:
            k -= 1                                   # and its shade just east of it
        if x >= hx1 - 1:
            k -= 1                                   # the east end turns from the light
        if u < 0.08 and x < hx0 + 24 and x not in hoops:
            k = 5                                    # the crest's glint on the upper left
        cv.set(x, y, T(fam, max(1, min(5, k))))
    for x in range(hx0 + 3, hx1 - 2):              # the seam where two widths of canvas are sewn
        y = prof[x] + round((bed_top - prof[x]) * 0.5)
        if x % 4 < 2 and x not in hoops:
            step(cv, x, y, -1)
    for i, hx in enumerate(hoops[:-1]):           # tension: the cloth pulled taut from each hoop
        for t in range(4 + i % 2):                 # down into the slack panel, as a crease
            x, y = hx + 2 + t, prof[hx] + 6 + t + (i % 3)
            if (x, y) in hood and (x, y + 1) in hood:
                step(cv, x, y, -1, 1); step(cv, x, y + 1, 1)
    ss_grain(cv, {p for p in hood if p[0] not in hoops}, 0.2, 33, shapes=rh.H_GRAIN,   # the weave, sun-faded in streaks
             lit=lambda x, y: 1 - (y - 5) / 22, swap=0.8, up=0.18, down=0.14)
    for i, x in enumerate(range(hx0 + 13, hx0 + 41)):   # a merchant's name painted along the side, faded
        col = x - (hx0 + 13)
        glyph = col % 6
        if glyph == 5 or x in hoops:
            continue
        rows = (0b111, 0b101, 0b110, 0b011, 0b111)[(col // 6) % 5]
        for r in range(3):
            if rows >> r & 1 and noise2(col, r, 61) < 0.86:
                y = 17 + r
                if (x, y) in hood:
                    cv.set(x, y, T('clay_cool' if glyph < 3 else 'clay_warm', 4 if y == 17 else 3))
    for (px, py, fam) in ((49, 11, 'sand'), (25, 22, 'sand_warm')):   # patches over old tears, stitched round
        for (x, y) in rect(px, py, 5, 3):
            cv.set(x, y, T(sib(fam, noise2(x, y, 7), 0.3), 4 if y == py else 3 if fam == 'sand' else 2))
        for (x, y) in ((px - 1, py), (px - 1, py + 2), (px + 5, py + 1), (px + 1, py + 3), (px + 3, py + 3)):
            if (x, y) in hood:
                cv.set(x, y, T(fam, 1))
    for x in range(hx0 + 1, hx1):                  # trail dust kicked up onto the hem, water stains above it
        for y in (bed_top - 3, bed_top - 2, bed_top - 1):
            if smooth_noise(x, y // 2, 2.5, 31) > 0.5 - 0.08 * (y - bed_top + 3) and (x, y) in hood:
                hit = rh.tone_at(cv, x, y)
                cv.set(x, y, T('sand', hit[1] if hit else 2))
    # the west (front) end drawn shut on its string: gathers fan out from a knot of cloth
    kx, ky = hx0 + 2, 17
    for k in range(11):
        a = math.pi * (-0.62 + 1.24 * k / 10)
        for t in range(1, 7):
            px, py = round(kx + math.cos(a) * t * 0.9), round(ky + math.sin(a) * t * 1.25)
            if (px, py) in hood:
                cv.set(px, py, T(sib('plaster', noise2(k, 1, 3), 0.3), (4 if t < 4 else 3) if k % 2 == 0 else 2))
    cv.set(kx, ky, T('sand', 2)); cv.set(kx, ky + 1, T('sand', 1)); cv.set(kx + 1, ky, T('sand', 3))
    # the east (back) end drawn up on its string round an opening, the load inside in shade
    ocx, ocy = hx1 - 4.0, 17.5
    opening = rh.ellipse(ocx, ocy, 3.0, 5.6)
    for (x, y) in opening:
        cv.set(x, y, T('earth_cool', 0))
    for (x, y) in rect(int(ocx) - 2, 18, 4, 3):     # a crate's lid in the light from the opening
        cv.set(x, y, T('timber', 2 if y == 18 else 1))
    for (x, y) in rh.ellipse(ocx - 1, 21.5, 1.8, 1.6):   # a flour sack
        cv.set(x, y, T('sand', 2 if x < ocx - 1 else 1))
    for (x, y) in opening:                           # the end hoop round the mouth, lit on its upper left
        if (x - 1, y) not in opening and (x - 1, y) in hood:
            cv.set(x - 1, y, T('timber', 4 if y < ocy else 2))
    lx, ly = hx0 + 10, 21                            # a lantern hung on the front hoop, unlit by day
    cv.set(lx, ly - 2, T('iron', 2)); cv.set(lx, ly - 1, T('iron', 4)); cv.set(lx + 1, ly - 1, T('iron', 2))
    for (x, y) in rect(lx - 1, ly, 3, 3):
        cv.set(x, y, T('sand', 5 if (x, y) == (lx - 1, ly) else 4 if x < lx + 1 else 2))   # horn panes
    cv.hline(lx - 1, ly + 3, 3, T('iron', 1))
    for x in range(hx1 - 4, hx1 + 1):               # the east end turns away from the light
        for y in range(0, bed_top):
            if (x, y) in hood:
                step(cv, x, y, -1, 1)
    # tie-downs from the hem to a cleat on the top rail at each hoop
    for hx in hoops:
        cv.set(hx, bed_top - 1, T('sand', 2)); cv.set(hx, bed_top - 2, T('sand', 4))
    # the bed: lapped boards between the rails
    woods = lambda bi, si: (('bleached', 'timber', 'timber_warm')[int(noise2(bi, si, 41) * 3)],
                            3 - (1 if noise2(bi, si, 43) < 0.15 else 0))
    boards(cv, x0, bed_top + 2, x1 - x0, bed_bot - bed_top - 2, woods, board=4, seed=44)
    for x in range(x0, x1):
        cv.set(x, bed_top, T('timber', 4 if x < x0 + 30 else 3))
        cv.set(x, bed_top + 1, T('timber', 2))
        cv.set(x, bed_bot, T('timber', 1))
    for sx in (x0 + 1, 22, 44, x1 - 2):          # the bed's standards, capped in iron
        for y in range(bed_top + 1, bed_bot + 1):
            cv.set(sx, y, T('timber', 4 if y < bed_top + 4 else 3)); cv.set(sx + 1, y, T('timber', 1))
        cv.set(sx, bed_top, T('iron', 4)); cv.set(sx + 1, bed_top, T('iron', 2))
    # the shade under the bed and the running gear
    for x in range(x0 + 2, x1 - 1):
        cv.set(x, bed_bot + 1, T('earth_cool', 0)); cv.set(x, bed_bot + 2, T('earth_cool', 1) if (x // 3) % 2 else T('earth_cool', 0))
    for x in range(x0 + 6, x1 - 4):                # the reach pole between the axles
        cv.set(x, bed_bot + 3, T('timber', 2))
    # the wheels: the rear pair larger, iron tyres, jointed felloes
    rh.wheel(cv, 18.5, 39.5, 7.5, 6.6, spokes=10, seed=1)
    rh.wheel(cv, 51.5, 38.0, 9.2, 8.2, spokes=12, seed=2)
    # the water barrel lashed to the south side between the wheels
    bx0, by0 = 31, 27
    part(cv, bx0, by0, 8, 9, 'timber', 3)
    for y in (by0 + 2, by0 + 6):
        cv.hline(bx0, y, 8, T('iron', 2)); cv.set(bx0 + 1, y, T('iron', 4))
    cv.vline(bx0 + 2, by0 + 3, 3, T('timber', 4))
    # the jockey box at the front and the brake lever by the rear wheel
    part(cv, x0 - 5, bed_top + 3, 7, 6, 'bleached', 3)
    cv.hline(x0 - 5, bed_top + 2, 7, T('iron', 3))
    for y in range(23, 33):                        # the brake lever, in front of the rear wheel
        cv.set(40, y, T('iron', 3 if y < 28 else 2)); cv.set(41, y, T('iron', 1))
    cv.set(40, 22, T('iron', 4)); cv.set(41, 22, T('iron', 3))
    # the tongue out west to the doubletree
    for x in range(1, x0 + 4):
        cv.set(x, 37, T('timber', 4 if x < 6 else 3)); cv.set(x, 38, T('timber', 1))
    for y in range(34, 41):
        cv.set(2, y, T('timber', 3)); cv.set(3, y, T('timber', 1))
    return rh.finish(cv)


def windpump() -> Canvas:
    """A desert windpump, 40 x 88: a lattice tower, a fan of blades and a tail vane."""
    w, h = 40, 88
    cv = Canvas(w, h, pad=PAD)
    for y in range(26, h - 2):
        t = (y - 26) / (h - 28)
        lx, rx = int(16 - t * 10), int(23 + t * 10)
        cv.set(lx, y, IRON[3]); cv.set(rx, y, IRON[1])
        if (y - 26) % 10 == 0:
            for x in range(lx, rx + 1):
                cv.set(x, y, IRON[2])
            for k in range(rx - lx):
                cv.set(lx + k, y + min(9, k * 10 // max(1, rx - lx)), IRON[2])
    for k in range(12):
        a = 2 * math.pi * k / 12
        for t in range(3, 15):
            x, y = int(round(19 + math.cos(a) * t)), int(round(16 + math.sin(a) * t * 0.9))
            cv.set(x, y, '#D8D4C8' if math.cos(a) + math.sin(a) < 0 else '#A9A49A')
    for (x, y) in disc(19, 16, 2.5):
        cv.set(x, y, IRON[1])
    for x in range(22, 38):
        cv.set(x, 17, IRON[2])
    for y in range(12, 22):
        cv.hline(32, y, 6, RED[3] if y < 17 else RED[2])
    return cv


def trough() -> Canvas:
    """A horse trough, 34 x 14: planks round a strip of water."""
    cv = Canvas(34, 14, pad=PAD)
    detail.boards(cv, rect_set(1, 3, 32, 10), BLEACHED, 2, 3, board=3, seed=6)
    for (x, y) in rect_set(4, 4, 26, 4):
        cv.set(x, y, WTR[3] if y == 4 else WTR[2])
    cv.hline(1, 3, 32, BLEACHED[5])
    return cv


def cow_skull() -> Canvas:
    cv = Canvas(18, 10, pad=PAD)
    for (x, y) in oval(9, 5, 3.5, 3.2):
        cv.set(x, y, '#F2EAD8' if x < 9 else '#D8CDB6')
    for side in (-1, 1):
        for t in range(6):
            cv.set(9 + side * (3 + t), 3 - (t // 3), '#E8DEC8')
    cv.set(8, 5, '#3A2A22'); cv.set(10, 5, '#3A2A22')
    return cv


def mine_portal() -> Canvas:
    """The old mine's mouth in a sandstone outcrop, 72 x 56: layered rock lit on the
    left, a timber frame round a dark entrance and cart rails running in."""
    w, h = 72, 56
    cv = Canvas(w, h, pad=PAD)
    rock = oval(36, 34, 35, 20) | oval(22, 26, 18, 16) | oval(52, 28, 17, 14) | oval(38, 20, 14, 10)
    rock = {(x, y) for (x, y) in rock if y > 8 + int(noise2(x // 4, 0, 205) * 6)}
    for (x, y) in rock:
        if y > 52:
            continue
        layer = (y + int(noise2(x // 6, y // 5, 204) * 3)) // 5
        lit = (x - 36) + (y - 30) * 0.6 < -6
        c = ADOBE[4 if lit else 2] if layer % 2 else ADOBE[3 if lit else 1]
        if (x, y - 1) not in rock:
            c = ADOBE[4]
        cv.set(x, y, c)
    for (x, y) in rect_set(24, 26, 24, 26):
        cv.set(x, y, '#1A120E' if y > 28 else '#2A1C16')
    for px in (22, 47):
        gp.post(cv, px, 24, 52, w=3, ramp=WOOD)
    cv.rect(20, 22, 32, 4, WOOD[3]); cv.hline(20, 22, 32, WOOD[4]); cv.hline(20, 25, 32, WOOD[1])
    for y in range(40, 53, 3):  # sleepers and rails into the dark
        cv.hline(28, y, 16, WOOD[2])
    for rx in (30, 41):
        cv.vline(rx, 34, 19, IRON[3])
    return cv


def dry_well() -> Canvas:
    """The town's dry well, 34 x 42: fieldstone ring, a wooden windlass with a frayed
    rope and an empty bucket hung up, cracked mud showing at the bottom."""
    cv = Canvas(34, 42, pad=PAD)
    ring = oval(17, 33, 14, 7)
    for (x, y) in ring:
        cv.set(x, y, ADOBE[3] if x < 17 else ADOBE[1])
    detail.stones(cv, 3, 29, 28, 10, ADOBE, seed=11, course=3)
    for (x, y) in oval(17, 31, 10, 4.2):
        cv.set(x, y, DESERT[1] if (x + y) % 4 else DESERT[0])  # dry, cracked bottom
    for (x0, y0, x1, y1) in ((10, 30, 14, 32), (18, 29, 22, 33), (13, 33, 20, 31)):
        cv.set(x0, y0, DESERT[0]); cv.set(x1, y1, DESERT[0])
    for px in (5, 27):
        gp.post(cv, px, 8, 32, w=3, ramp=BLEACHED)
    for x in range(5, 30):  # the windlass drum
        cv.set(x, 12, BLEACHED[4]); cv.set(x, 13, BLEACHED[2]); cv.set(x, 14, BLEACHED[1])
    for x in range(13, 21):
        cv.set(x, 12, '#C9B48A'); cv.set(x, 13, '#A8936A')
    cv.vline(30, 10, 6, IRON[2]); cv.hline(30, 15, 3, IRON[2])
    for (x, y) in rect_set(24, 17, 6, 6):  # the bucket hung on the post
        cv.set(x, y, WOOD[3] if x < 26 else WOOD[1])
    cv.hline(24, 18, 6, IRON[2]); cv.hline(24, 21, 6, IRON[2])
    cv.vline(17, 15, 4, '#A8936A')  # a frayed end of rope
    cv.set(16, 19, '#A8936A'); cv.set(18, 19, '#A8936A')
    return cv


def keg() -> Canvas:
    """A wooden keg on its side, 18 x 14, with iron hoops."""
    cv = Canvas(18, 14, pad=PAD)
    for (x, y) in oval(9, 7, 8, 6):
        k = (y - 1) / 12
        cv.set(x, y, WOOD[4] if k < 0.25 else WOOD[3] if k < 0.55 else WOOD[2] if k < 0.8 else WOOD[1])
    for hx in (4, 14):
        for y in range(1, 13):
            if cv.get(hx, y)[3]:
                cv.set(hx, y, IRON[3] if y < 6 else IRON[1])
    for (x, y) in oval(2, 7, 2, 5):
        cv.set(x, y, BLEACHED[4] if y < 7 else BLEACHED[3])
    cv.set(2, 7, WOOD[0])
    return cv


def hay_bale() -> Canvas:
    """A square hay bale, 22 x 16, its straws lit on top, two twine bands."""
    cv = Canvas(22, 16, pad=PAD)
    for y in range(2, 16):
        for x in range(1, 21):
            top = y < 6
            n = noise2(x, y, 206)
            c = ('#F2D27A' if n > 0.5 else '#E2BC5E') if top else ('#C99A3C' if n > 0.4 else '#A87E2C')
            cv.set(x, y, c)
    for bx in (6, 15):
        cv.vline(bx, 2, 14, '#7A5A22')
    cv.hline(1, 6, 20, '#8E6A26')
    for x in range(1, 21, 3):
        cv.set(x, 1, '#F2D27A')
    return cv


def ore_tub() -> Canvas:
    """A mine cart's ore tub on the narrow-gauge rails, 22 x 18 (seen from the south):
    a riveted iron box, lit on its upper left, heaped with ore, on four small wheels."""
    cv = Canvas(22, 18, pad=PAD)
    for y in range(4, 14):  # the box, narrowing a little toward its foot
        inset = (y - 4) // 5
        for x in range(1 + inset, 21 - inset):
            c = IRON[3] if x < 7 else IRON[2] if x < 16 else IRON[1]
            if y == 4:
                c = IRON[4]  # the lit rim
            elif y == 13:
                c = IRON[0]
            cv.set(x, y, c)
    for x in (3, 10, 18):  # straps and rivets
        cv.vline(x, 5, 8, IRON[1]); cv.set(x, 6, IRON[4]); cv.set(x, 11, IRON[4])
    for (x, y) in oval(11, 4, 9, 4):  # the ore, heaped above the rim
        if y <= 4:
            n = noise2(x // 2, y // 2, 941)
            c = '#5A4A44' if n > 0.6 else '#3C302C' if n > 0.25 else '#2A2220'
            if (x + y) % 5 == 0 and x < 11:
                c = '#9A8A7A'
            cv.set(x, y, c)
    cv.set(8, 2, GOLD[4]); cv.set(14, 3, GOLD[3])  # a glint of ore
    for wx in (4, 16):  # the wheels under it
        cv.hline(wx - 1, 14, 4, IRON[1]); cv.hline(wx - 1, 15, 4, IRON[0]); cv.set(wx, 14, IRON[3])
    return cv


def dynamite_crate() -> Canvas:
    """A mining crate, 16 x 13 (size guide: a crate 9 to 13 tall), boards with a lit top
    edge and corner battens, red sticks peeking out of the open top, a stencilled band."""
    cv = Canvas(16, 13, pad=PAD)
    detail.boards(cv, rect_set(1, 4, 14, 9), BLEACHED, 2, 4, board=3, seed=7)
    cv.hline(1, 4, 14, BLEACHED[5])
    for x in range(3, 13, 3):
        cv.vline(x, 1, 3, RED[3]); cv.vline(x + 1, 1, 3, RED[2]); cv.set(x, 0, '#E8DEC8')
    cv.hline(1, 8, 14, RED[2])
    cv.vline(1, 4, 9, BLEACHED[4]); cv.vline(14, 4, 9, BLEACHED[1])   # the corner battens
    return cv


def hitching_rail() -> Canvas:
    """A hitching rail, 44 x 18: two posts and a worn rail."""
    cv = Canvas(44, 18, pad=PAD)
    for px in (3, 38):
        gp.post(cv, px, 4, 18, w=3, ramp=BLEACHED)
    for x in range(1, 43):
        cv.set(x, 5, BLEACHED[4]); cv.set(x, 6, BLEACHED[2]); cv.set(x, 7, BLEACHED[1])
    for x in (16, 17, 26):
        cv.set(x, 6, BLEACHED[3])
    return cv


def poster_board() -> Canvas:
    """A wanted-poster board, 30 x 38: a little shingled cap and pinned posters with an
    abstract portrait (never real text)."""
    cv = Canvas(30, 38, pad=PAD)
    for px in (4, 23):
        gp.post(cv, px, 8, 38, w=3, ramp=BLEACHED)
    detail.boards(cv, rect_set(2, 8, 26, 18), BLEACHED, 2, 8, board=4, vertical=True, x0=2)
    for y in range(3, 8):
        cv.hline(1 + (7 - y) // 2, y, 28 - (7 - y), BLEACHED[4] if y < 6 else BLEACHED[1])
    for (x0, y0) in ((5, 10), (16, 11)):
        for (x, y) in rect_set(x0, y0, 9, 12):
            cv.set(x, y, '#EAD9B2' if y > y0 else '#F4E6C8')
        for (x, y) in disc(x0 + 4, y0 + 5, 2.4):
            cv.set(x, y, '#6E5040')
        cv.hline(x0 + 1, y0 + 9, 7, '#93725A'); cv.hline(x0 + 2, y0 + 1, 5, '#93725A')
    return cv


def corral_rail(length: int = 64) -> Canvas:
    """A run of split-rail corral fence, 64 x 20: rough posts and two sagging rails."""
    cv = Canvas(length, 20, pad=PAD)
    for px in range(1, length, 16):
        gp.post(cv, px, 2, 20, w=3, ramp=BLEACHED)
    for ry in (6, 12):
        for x in range(0, length):
            sag = int(math.sin((x % 16) / 16 * math.pi) * 1.4)
            cv.set(x, ry + sag, BLEACHED[4]); cv.set(x, ry + sag + 1, BLEACHED[2])
    return cv


def corral_side() -> Canvas:
    """The side of a split-rail corral, 12 x 60: posts and rails seen end on."""
    cv = Canvas(12, 60, pad=PAD)
    for y0 in range(0, 60, 15):
        gp.post(cv, 4, y0, y0 + 14, w=3, ramp=BLEACHED)
    for y in range(0, 60):
        cv.set(3, y, BLEACHED[2]); cv.set(8, y, BLEACHED[1])
    return cv


def palm(tall: bool = True) -> Canvas:
    """A date palm, 56 x 84 (or 48 x 64): a ringed, gently curved trunk lit on the left,
    a crown of long arching fronds lit on their upper faces, and a cluster of dates."""
    w, h = (56, 84) if tall else (48, 64)
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    top = 22 if tall else 18
    for y in range(top, h - 1):
        bend = int(math.sin((y - top) / (h - top) * 2.2) * 3)
        for dx in range(-3, 3):
            x = cx + bend + dx
            c = WOOD[3] if dx < -1 else WOOD[2] if dx < 1 else WOOD[1]
            if (y - top) % 4 == 0:
                c = WOOD[1] if dx > -2 else WOOD[2]  # the rings
            cv.set(x, y, c)
    for k in range(12):  # fronds arching out and down from the crown
        a = math.pi * (-0.05 + 1.1 * k / 11)
        length = (24 if tall else 19) + (k % 2) * 3
        for t in range(length):
            x = cx + math.cos(a) * t * (1 if k % 2 else 0.95)
            y = top + 6 - math.sin(a) * t * 0.85 + (t / length) ** 2 * 12
            for side in (-1, 1):  # leaflets either side of the rib
                lx, ly = int(x + side * 0.5), int(y + side * 1.2 + (1 if t % 3 == 0 else 0))
                cv.set(lx, ly, CACTUS[3] if side < 0 else CACTUS[1])
            cv.set(int(x), int(y), CACTUS[4] if t < length * 0.6 else CACTUS[2])
    for (x, y) in disc(cx + 3, top + 4, 2.5):
        cv.set(x, y, '#8A4A2A' if (x + y) % 2 else '#B8693F')
    return cv


def sandstone_arch() -> Canvas:
    """A ruined sandstone arch, 64 x 56: two weathered piers in courses, a broken lintel,
    sand drifted against its feet."""
    w, h = 64, 56
    cv = Canvas(w, h, pad=PAD)
    for (x0, x1) in ((4, 18), (46, 60)):
        for y in range(10, h - 4):
            for x in range(x0, x1):
                course = (y - 10) // 6
                c = ADOBE[4] if x < x0 + 3 else ADOBE[3] if x < x1 - 3 else ADOBE[2]
                if (y - 10) % 6 == 5 or (x + course * 4) % 9 == 0:
                    c = ADOBE[1]
                cv.set(x, y, c)
    for y in range(4, 12):  # the lintel, broken at the right
        for x in range(2, 50 + (y // 3)):
            cv.set(x, y, ADOBE[4] if y < 6 else ADOBE[3] if y < 10 else ADOBE[1])
    for (x, y) in oval(11, h - 3, 12, 4) | oval(53, h - 3, 12, 4):
        if y >= h - 5:
            cv.set(x, y, DESERT[4] if x < 32 else DESERT[3])
    return cv


def awning() -> Canvas:
    """A traders' shade awning, 72 x 50: striped cloth on poles seen from above, rugs
    and cushions in its shade, a brass tea tray."""
    w, h = 72, 50
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 22):
        for x in range(2, w - 2):
            stripe = (x // 6) % 3
            c = ('#C2453A', '#E8D8B8', '#3E6A8A')[stripe]
            if y > 18:
                c = ('#9A3028', '#C8B898', '#2C4A68')[stripe]
            cv.set(x, y, c)
    for px in (4, w - 7):
        gp.post(cv, px, 20, h - 2, w=2, ramp=WOOD)
    for (x, y) in ((xx, yy) for xx in range(10, w - 10) for yy in range(30, 44)):
        cv.set(x, y, '#8A3A2A' if (x // 4 + y // 4) % 2 else '#B8693F')
    for (cx0, c) in ((18, '#3E6A8A'), (50, GOLD[3])):
        for (x, y) in oval(cx0, 34, 5, 3):
            cv.set(x, y, c)
    for (x, y) in oval(34, 38, 5, 2.5):
        cv.set(x, y, MATERIALS['brass'][3] if x < 34 else MATERIALS['brass'][2])
    return cv


def water_jar() -> Canvas:
    """A tall clay water jar, 14 x 20, beaded with damp."""
    cv = Canvas(14, 20, pad=PAD)
    for (x, y) in oval(7, 12, 6, 7):
        cv.set(x, y, ADOBE[3] if x < 6 else ADOBE[2] if x < 9 else ADOBE[1])
    for (x, y) in oval(7, 4, 3, 1.5):
        cv.set(x, y, ADOBE[4])
    cv.set(5, 10, '#C6DDEE'); cv.set(4, 13, '#C6DDEE')
    return cv


CAMEL = ['#4E3222', '#7E5638', '#A87C52', '#C9A06E', '#E0C08E']


def camel(variant: int = 0) -> Canvas:
    """A camel resting with its legs folded under it, 48 x 36, seen from the side: the
    hump lit from the upper left, a striped saddle blanket, the long neck curving up to
    a drowsy head, the folded knees in the sand. variant 1 (review 19 Oct: not two the
    same side by side) is a darker animal under a blue blanket, its neck stretched low
    along the sand with its chin resting on it, asleep."""
    w, h = 48, 36
    cv = Canvas(w, h, pad=PAD)
    if variant:
        return _camel_asleep(cv)
    body = oval(20, 24, 16, 8) | oval(18, 15, 8, 6)  # body and hump
    for (x, y) in body:
        k = (x - 4) / 32 + (y - 8) / 22
        c = CAMEL[4] if k < 0.55 else CAMEL[3] if k < 0.95 else CAMEL[2] if k < 1.3 else CAMEL[1]
        cv.set(x, y, c)
    for y in range(12, 23):  # a woven saddle blanket over the hump, diamonds on red
        for x in range(11, 27):
            if (x, y) in body:
                d = (abs(x - 18) + abs(y - 17)) % 6
                c = '#9A3028' if x < 13 or y > 21 else '#B8443A' if d > 1 else GOLD[3] if d == 0 else '#2C2A3A'
                cv.set(x, y, c)
    cv.hline(11, 22, 16, GOLD[2])  # its fringe
    for t in range(18):  # the neck, curving up and forward
        x, y = 34 + t * 0.55, 22 - t * 0.9 + (t / 18) ** 2 * 3
        for d in range(-1, 2 + (t < 5)):
            cv.set(int(x + d * 0.3), int(y + d), CAMEL[3] if d < 0 else CAMEL[2] if d < 1 else CAMEL[1])
    for (x, y) in oval(44, 7, 4, 2.5):  # the head, eyes half shut
        cv.set(x, y, CAMEL[3] if y < 7 else CAMEL[2])
    cv.set(47, 8, CAMEL[0]); cv.set(43, 6, CAMEL[0]); cv.set(41, 4, CAMEL[2])
    for (kx, ky) in ((8, 31), (28, 31), (34, 30)):  # the folded knees
        for (x, y) in oval(kx, ky, 4, 2):
            cv.set(x, y, CAMEL[2] if x < kx else CAMEL[1])
    for x in range(4, 8):  # the tail
        cv.set(x - 2, 22 + (x - 4), CAMEL[1])
    return cv


def _camel_asleep(cv: Canvas) -> Canvas:
    DARK = ['#3A2418', '#5E3E28', '#80583A', '#A27650', '#BE9468']
    body = oval(20, 25, 16, 7.5) | oval(17, 17, 8, 5.5)
    for (x, y) in body:
        k = (x - 4) / 32 + (y - 9) / 22
        cv.set(x, y, DARK[4] if k < 0.55 else DARK[3] if k < 0.95 else DARK[2] if k < 1.3 else DARK[1])
    for y in range(13, 24):  # a plain blue blanket with a pale stripe
        for x in range(10, 26):
            if (x, y) in body:
                cv.set(x, y, '#E8DCC0' if y in (16, 17) else '#3E6A8A' if x < 18 else '#2E506A')
    cv.hline(10, 24, 16, '#24405A')
    for t in range(16):  # the neck stretched low and forward along the sand
        x, y = 33 + t * 0.7, 25 + t * 0.32
        for d in range(-1, 2):
            cv.set(int(x), int(y + d), DARK[3] if d < 0 else DARK[2] if d == 0 else DARK[1])
    for (x, y) in oval(45, 30, 3.6, 2.2):  # the head, chin on the sand, eyes shut
        cv.set(x, y, DARK[3] if y < 30 else DARK[2])
    cv.hline(43, 29, 2, DARK[0])  # the shut eye
    cv.set(41, 27, DARK[2]); cv.set(40, 26, DARK[2])  # an ear laid back
    for (kx, ky) in ((8, 31), (27, 32)):  # the folded knees
        for (x, y) in oval(kx, ky, 4, 2):
            cv.set(x, y, DARK[2] if x < kx else DARK[1])
    for t in range(5):  # the tail curled round
        cv.set(3 + t // 2, 24 + t, DARK[1])
    return cv


def corral_gate() -> Canvas:
    """The east side of the corral with its gate, 18 x 60, seen end on like the west side:
    a stout gate post at each end and a middle run of rails, and a gate of four boards
    on iron strap hinges, swung open outward against its post so a hand can lead a horse
    through, a rope loop on its latch post."""
    cv = Canvas(18, 60, pad=PAD)
    for y0 in (0, 44):
        gp.post(cv, 4, y0, y0 + 15, w=3, ramp=BLEACHED)
    gp.post(cv, 4, 30, 44, w=3, ramp=BLEACHED)  # the latch post
    for y in list(range(0, 18)) + list(range(30, 60)):
        cv.set(3, y, BLEACHED[2]); cv.set(8, y, BLEACHED[1])
    for t in range(13):  # the gate, swung open outward (east) from the hinge post at the top
        x, y = 8 + int(t * 0.62), 16 + t
        for k in range(4):
            cv.set(x + k // 2, y - k * 2 + 6, BLEACHED[4] if k % 2 == 0 else BLEACHED[2])
        cv.set(x, y + 1, BLEACHED[1])
    cv.set(7, 17, IRON[3]); cv.set(7, 21, IRON[3])  # the strap hinges
    cv.set(4, 33, '#8A6A40'); cv.set(5, 34, '#8A6A40'); cv.set(4, 35, '#6A4A28')  # the rope loop
    return cv


def tent() -> Canvas:
    """A caravan tent, 72 x 48 (prop audit, REDRAW: "reads as two grey rocks"; asset
    ledger 20 Oct): a ridge tent of woven goat-hair cloth in long panels, dark brown with
    cream bands, pitched on a ridge pole carried by two uprights whose tops stand proud of
    it. Seen from the south and above like every prop: the front slope runs down from the
    ridge to the eave in panels sewn edge to edge, taut over the poles and slack between
    them; the west gable end, facing the light, is a lit triangle, the east end falls into
    shade. The middle of the front is rolled up to the eave on its ties, showing the shade
    inside with a rug, a cushion and a lamp. Guy ropes run from the eave's corners and the
    gable peaks to pegs. All on the house ramps (earth for the goat hair, plaster bands,
    berry and clay rugs, brass, timber, iron)."""
    w, h = 72, 48
    cv = Canvas(w, h, pad=PAD)
    poles = (22, 50)
    rx0, rx1 = 13, 58          # the ridge pole's ends
    ex0, ex1 = 3, 68           # the eave's ends: the cloth runs out to its corner pegs

    def ridge(x):   # the ridge sags between the two uprights
        if poles[0] <= x <= poles[1]:
            return 9 + round(2.0 * (1 - ((x - 36) / 14) ** 2))
        return 9

    def eave_at(x):  # the hem lifts a little where the guys pull it, and sags between
        pulls = (ex0, poles[0], poles[1], ex1)
        d = min(abs(x - p) for p in pulls)
        return 30 - (1 if d < 3 else 0) + (1 if d > 9 else 0)
    eave = 30
    slope = set()
    for x in range(ex0, ex1 + 1):
        top_line = ridge(min(max(x, rx0), rx1))
        if x < rx0:
            top_line = 9 + round((rx0 - x) * 21 / (rx0 - ex0))     # the west end slopes down to its corner
        elif x > rx1:
            top_line = 9 + round((x - rx1) * 21 / (ex1 - rx1))
        bot = eave_at(x)
        panel = (x - ex0) // 9
        fam = ('earth', 'earth_warm', 'earth_cool')[panel % 3]
        for y in range(top_line, bot + 1):
            slope.add((x, y))
            t = (y - ridge(min(max(x, rx0), rx1))) / max(1, bot - 9)
            k = 4 if t < 0.12 else 3 if t < 0.42 else 2 if t < 0.8 else 1
            if x < rx0:
                k = min(4, k + 1)                               # the west end faces the light
            elif x > rx1:
                k = max(1, k - 1)                               # the east end falls into shade
            sag = 2.0 * (1 - ((x - 36) / 14) ** 2) if poles[0] <= x <= poles[1] else 0
            yb = y - sag
            band = 17 <= yb < 19 or 24 <= yb < 25.5              # two woven cream bands, following the drape
            j = (x - ex0) % 9
            if band:
                f2 = ('plaster', 'plaster_warm', 'plaster_cool')[panel % 3]
                cv.set(x, y, T(f2, max(1, k - 1)))
            else:
                cv.set(x, y, T(fam, k))
            if j == 0 and rx0 <= x <= rx1 and y > top_line:
                cv.set(x, y, T(fam, max(0, k - 2)))             # the seam between two panels
            elif j == 1 and rx0 <= x <= rx1 and y > top_line + 1 and not band:
                cv.set(x, y, T(fam, min(4, k + 1)))             # the lapped edge catching the light
        if rx0 <= x <= rx1:
            cv.set(x, top_line, T('earth', 5 if x < 32 else 4))   # the ridge, lit along its crest
    ss_grain(cv, {p for p in slope if (p[0] - ex0) % 9 > 1}, 0.12, 645, shapes=rh.V_GRAIN, swap=0.7,
             up=0.15, down=0.25)                                # the weave, coarse, in short runs down the cloth
    for x in range(ex0, ex1 + 1):                               # sand blown up onto the hem
        for y in (eave_at(x) - 1, eave_at(x)):
            if smooth_noise(x, 0, 3, 647) > 0.48 and (x, y) in slope:
                cv.set(x, y, T('sand_cool', 1 if y == eave_at(x) else 2))
    for (px0, py0, pw, ph) in ((13, 18, 5, 4), (53, 14, 4, 5)):   # patches sewn over worn cloth, stitched round
        for y in range(py0, py0 + ph):
            for x in range(px0, px0 + pw):
                edge = x in (px0, px0 + pw - 1) or y in (py0, py0 + ph - 1)
                cv.set(x, y, T('timber_cool', (2 if px0 < 40 else 1) if not edge else 1))
        for x in range(px0, px0 + pw, 2):
            cv.set(x, py0 - 1, T('plaster', 2))
    for px in poles:   # the uprights' tops standing proud of the ridge, a knob on each
        for y in range(ridge(px) - 4, ridge(px) + 1):
            cv.set(px, y, T('timber', 4)); cv.set(px + 1, y, T('timber', 2))
        cv.set(px, ridge(px) - 5, T('timber', 5)); cv.set(px + 1, ridge(px) - 5, T('timber', 3))
    for x in range(ex0, ex1 + 1):        # the hem along the eave
        cv.set(x, eave_at(x) + 1, T('earth', 1))
    foot = 38                            # the ground line the side curtain hangs to
    ox0, ox1 = 26, 47                    # the open front, rolled up to the eave
    for x in range(ex0 + 2, ex1 - 1):    # the side curtain hung from the eave, in the eave's shade, in folds
        if ox0 - 1 <= x <= ox1:
            continue
        for y in range(eave_at(x) + 2, foot):
            f = (x - ex0) % 4
            k = 2 if f == 0 else 1 if f == 3 else 1
            if y == foot - 1:
                k = 1
            cv.set(x, y, T('earth_cool' if f in (1, 2) else 'earth', k + (1 if y > foot - 4 and f == 0 else 0)))
        if smooth_noise(x, 1, 3, 648) > 0.5:
            cv.set(x, foot - 1, T('sand_cool', 1))                 # sand banked against its foot
    for x in range(ox0 - 1, ox1 + 1):   # the roll: a cylinder of cloth, lit on top
        cream = (x // 3) % 2
        cv.set(x, eave - 3, T('plaster' if cream else 'earth', 4))
        cv.set(x, eave - 2, T('plaster' if cream else 'earth', 3))
        cv.set(x, eave - 1, T('earth', 1))
    for tx in (ox0 + 2, ox1 - 3):   # its ties
        cv.set(tx, eave - 3, T('sand', 4)); cv.set(tx, eave - 2, T('sand', 3)); cv.set(tx, eave - 1, T('sand', 2))
    for y in range(eave, foot):
        for x in range(ox0, ox1):
            if y < eave + 3:
                cv.set(x, y, T('earth_cool', 0))                # the shade deep inside
                continue
            u, v = x - ox0, y - eave - 3
            fam, k = ('berry', 2) if ((u // 4) + (v // 2)) % 2 else ('clay', 2)
            if v == 0 or u in (0, ox1 - ox0 - 1):
                fam, k = 'sand', 2                              # the rug's border
            if (u + v * 2) % 7 == 0 and 0 < v and 0 < u < ox1 - ox0 - 1:
                fam, k = 'brass', 2                             # a woven lozenge
            if y < eave + 6:
                k -= 1                                          # under the eave's shade
            cv.set(x, y, T(fam, k))
    for (x, y) in rh.ellipse(32.5, eave + 5.5, 3.5, 2.0):     # a cushion
        cv.set(x, y, T('brass', 4 if x < 31 and y < eave + 5 else 3 if x < 34 else 2))
    cv.set(40, eave, T('iron', 2)); cv.set(40, eave + 1, T('lamp', 4)); cv.set(41, eave + 1, T('lamp', 2))   # a lamp hung inside
    cv.set(40, eave + 2, T('iron', 1))
    for (x, y) in rh.ellipse(ox1 + 2.5, eave + 5.5, 1.6, 2.6):   # a water skin on the post
        cv.set(x, y, T('timber_warm', 3 if x <= ox1 + 2 else 2))
    for (x, y) in rh.ellipse(ox0 - 3.5, foot + 1.5, 3.0, 2.0):  # saddle bags by the door
        cv.set(x, y, T('clay', 4 if y < foot + 1 else 3))
    cv.set(ox0 - 5, foot, T('brass', 4)); cv.set(ox0 - 4, foot - 1, T('sand', 3))
    for px in (ox0 - 1, ox1):   # the door posts
        for y in range(eave - 1, foot):
            cv.set(px, y, T('timber', 3 if px == ox0 - 1 else 1))
    for (x0, y0, x1, y1) in ((ex0, eave, 1, foot + 4), (ex1, eave, w - 2, foot + 4),   # guy ropes to pegs
                             (rx0, 9, 2, 13), (rx1, 9, w - 3, 13)):
        rh.rope(cv, (x0, y0), (x1, y1), 0.0, 'sand', 2)
        rh.peg(cv, min(x1, w - 3), y1)
    return rh.finish(cv)


def fire_pit() -> Canvas:
    """A ring of stones round the embers of a small fire, 20 x 14, a teapot warming."""
    cv = Canvas(20, 14, pad=PAD)
    for k in range(10):
        a = 2 * math.pi * k / 10
        x, y = 10 + math.cos(a) * 7, 8 + math.sin(a) * 4
        for (sx, sy) in disc(x, y, 1.6):
            cv.set(sx, sy, STONE[3] if sy < y else STONE[1])
    for (x, y) in oval(10, 8, 4, 2):
        cv.set(x, y, '#3A2A22' if (x + y) % 2 else '#7A1A08')
    cv.set(9, 8, '#F2721E'); cv.set(11, 7, '#FFB648'); cv.set(10, 9, '#C2380E')
    for (x, y) in oval(15, 4, 2.5, 2):
        cv.set(x, y, MATERIALS['brass'][3] if x < 15 else MATERIALS['brass'][1])
    cv.set(18, 3, MATERIALS['brass'][2])
    return cv


def column_stump(seed: int = 0) -> Canvas:
    """A broken sandstone column, 16 x 26: fluted drums lit on the left, a jagged break
    at the top, one fallen drum and sand drifted at its foot."""
    cv = Canvas(16, 26, pad=PAD)
    top = 4 + seed % 3
    for y in range(top, 23):
        for x in range(3, 12):
            c = ADOBE[4] if x < 5 else ADOBE[3] if x < 9 else ADOBE[2]
            if (x - 3) % 3 == 2:
                c = ADOBE[2] if x < 9 else ADOBE[1]  # flutes
            if (y - top) % 7 == 6:
                c = ADOBE[1]
            cv.set(x, y, c)
    for x in range(3, 12):  # the break
        for y in range(top - 2 + int(noise2(x, seed, 470) * 3), top + 1):
            cv.set(x, y, ADOBE[4] if x < 8 else ADOBE[3])
    for (x, y) in oval(8, 23, 7, 2.5):
        if y >= 23:
            cv.set(x, y, DESERT[4] if x < 8 else DESERT[3])
    return cv


def papyrus() -> Canvas:
    """A clump of papyrus by the water, 22 x 28: tall stems ending in green tufts."""
    cv = Canvas(22, 28, pad=PAD)
    for k in range(7):
        bx = 5 + k * 2
        lean = (k - 3) * 0.35
        top = 6 + (k * 5) % 7
        for y in range(top, 27):
            cv.set(int(bx + lean * (27 - y) / 4), y, CACTUS[2] if k % 2 else CACTUS[3])
        tx = int(bx + lean * (27 - top) / 4)
        for (x, y) in disc(tx, top - 1, 2.6):
            cv.set(x, y, CACTUS[4] if x <= tx and y < top else CACTUS[3] if (x + y) % 2 else CACTUS[2])
    return cv


def shaduf() -> Canvas:
    """A shaduf, 56 x 52: the old lever for lifting water, a long pole balanced on a mud
    pillar with a stone counterweight at one end and a leather bucket on a rope at the
    other."""
    w, h = 56, 52
    cv = Canvas(w, h, pad=PAD)
    for y in range(22, h - 2):  # the pillar
        for x in range(20, 28):
            c = ADOBE[3] if x < 22 else ADOBE[2] if x < 26 else ADOBE[1]
            if (y + (x // 4) * 3) % 8 == 0:
                c = ADOBE[1]
            cv.set(x, y, c)
    for x in range(19, 29):
        cv.set(x, 21, ADOBE[4])
    for t in range(50):  # the pole, high over the water end
        x, y = 2 + t, 30 - t * 0.5
        cv.set(int(x), int(y), WOOD[3]); cv.set(int(x), int(y) + 1, WOOD[1])
    for (x, y) in disc(5, 30, 4):
        cv.set(x, y, STONE[3] if x + y < 33 else STONE[1])
    for y in range(6, 30):
        cv.set(51, y, MATERIALS['rope'][2])
    for (x, y) in oval(51, 32, 3.5, 3):
        cv.set(x, y, '#6A3E26' if x < 51 else '#4A2A1A')
    cv.hline(48, 30, 7, '#8A5A3A')
    return cv



def water_crane() -> Canvas:
    """A railway water crane, 34 x 56: an iron standpipe on a stone plinth, its arm
    swung out over the line with a canvas drop hose, a wheel valve, a red cap. The pipe
    under the sand brings it water from the spring."""
    w, h = 34, 56
    cv = Canvas(w, h, pad=PAD)
    for y in range(46, 54):
        for x in range(6, 22):
            cv.set(x, y, STONE[4] if y == 46 else STONE[3] if x < 9 else STONE[2] if x < 19 else STONE[1])
    for y in range(10, 46):
        for x in range(11, 17):
            cv.set(x, y, IRON[4] if x == 11 else IRON[3] if x < 14 else IRON[2] if x < 16 else IRON[1])
        if y % 12 == 0:
            cv.hline(10, y, 8, IRON[1])
    for x in range(8, 32):  # the arm
        for y in range(10, 14):
            cv.set(x, y, IRON[3] if y == 10 else IRON[2] if y < 13 else IRON[0])
    for y in range(14, 30):  # the drop hose
        cv.set(29, y, '#8A7A5A' if y % 3 else '#6E6046'); cv.set(30, y, '#6E6046')
    for (x, y) in disc(14, 6, 3):
        cv.set(x, y, RED[3] if x + y < 20 else RED[1])
    for k in range(12):
        a = 2 * math.pi * k / 12
        cv.set(int(round(19 + math.cos(a) * 3)), int(round(30 + math.sin(a) * 3)), RED[2])
    cv.set(19, 30, IRON[1]); cv.hline(17, 30, 2, IRON[1])
    return cv

def acacia() -> Canvas:
    """A desert acacia, 56 x 46: a flat umbrella crown of small olive leaf clumps (light
    caps, dark rims; style.leafy) on a leaning, forked trunk."""
    import style
    w, h = 56, 46
    cv = Canvas(w, h, pad=PAD)
    BARK = ['#3A2618', '#5A3C24', '#7A5434', '#9A7048', '#B88E62']
    for (x0, y0, x1, y1, wd) in ((26, h - 2, 24, 22, 3), (25, 28, 14, 16, 2), (25, 26, 40, 15, 2), (24, 24, 28, 12, 1)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            x, y = x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n
            for dx in range(wd + 1):
                cv.set(int(x) + dx, int(y), BARK[3] if dx == 0 else BARK[2] if dx < wd else BARK[1])
    OLIVE = ['#2E3A1C', '#4A5A2A', '#6A7A38', '#8E9A4A', '#B4BA6A']
    style.leafy(cv, 27, 12, 25, 8, OLIVE, r=2.4, seed=17)
    return cv


def desert_scrub(seed: int = 0) -> Canvas:
    """A low tamarisk scrub, 26 x 16: a tangle of grey-green feathery clumps with a few
    pink flower tips, dry twigs at its feet."""
    import style
    w, h = 26, 16
    cv = Canvas(w, h, pad=PAD)
    SAGE = ['#38402C', '#56603E', '#78825A', '#98A27A', '#BCC4A0']
    style.leafy(cv, 13, 8, 11, 5.5, SAGE, r=2.0, seed=seed + 9)
    for k in range(4):
        x, y = 5 + int(noise2(k, seed, 378) * 16), 4 + int(noise2(k, seed, 379) * 5)
        if cv.get(x, y)[3]:
            cv.set(x, y, '#E8A0BC')
    return cv


def sandstone_outcrop(seed: int = 0) -> Canvas:
    """Weathered sandstone blocks breaking out of the dune, 40 x 24: layered beds in
    adobe tones (lit tops, shaded right flanks; style.facet_stone), sand piled at the foot."""
    import style
    w, h = 40, 24
    cv = Canvas(w, h, pad=PAD)
    for k, (cx, cy, rx, ry) in enumerate(((16, 12, 13, 9), (30, 15, 9, 7), (8, 18, 6, 4))):
        pts = {(x, y) for y in range(cy - ry, cy + ry + 1) for x in range(cx - rx, cx + rx + 1)
               if max(abs(x - cx) / rx, abs(y - cy) / ry) * 0.7 + math.hypot((x - cx) / rx, (y - cy) / ry) * 0.3 <= 1}
        style.facet_stone(cv, pts, ADOBE, seed=seed + k)
        for (x, y) in pts:  # the beds
            if (y - cy + 40) % 4 == 0 and (x, y - 1) in pts and (x, y + 1) in pts:
                cv.set(x, y, ADOBE[1] if x > cx else ADOBE[2])
    for (x, y) in oval(20, h - 2, 18, 2.5):
        if y >= h - 3:
            cv.set(x, y, DESERT[4] if x < 20 else DESERT[3])
    return cv


def horse() -> Canvas:
    """A bay horse dozing on its feet in the corral, 44 x 36, seen from the side: the
    body lit along its back, a dark mane and tail, one hind hoof cocked (resting), the
    head low and its eyes shut."""
    w, h = 44, 36
    cv = Canvas(w, h, pad=PAD)
    BAY = ['#3A2218', '#5E3A24', '#80522E', '#A06A3C', '#C08850']
    body = oval(20, 17, 13, 7)
    for (x, y) in body:
        k = (x - 7) / 26 + (y - 10) / 14
        cv.set(x, y, BAY[4] if k < 0.45 else BAY[3] if k < 0.9 else BAY[2] if k < 1.3 else BAY[1])
    for (lx, cocked) in ((10, False), (14, True), (27, False), (30, False)):  # legs
        for y in range(22, h - 2 - (2 if cocked else 0)):
            cv.set(lx, y, BAY[2] if lx in (10, 27) else BAY[1]); cv.set(lx + 1, y, BAY[1])
        foot = h - 2 - (2 if cocked else 0)
        cv.hline(lx, foot, 2, '#2A2026')
        cv.set(lx, foot - 2, '#E8DCC8') if lx == 27 else None  # one white sock
    for t in range(9):  # the neck, low and forward
        x, y = 31 + t, 13 + t * 0.6
        for d in range(-2, 3):
            cv.set(int(x), int(y + d), BAY[3] if d < 0 else BAY[2])
    for (x, y) in oval(41, 20, 3.5, 2.8):  # the head, dozing
        cv.set(x, y, BAY[3] if y < 20 else BAY[2])
    cv.set(43, 22, BAY[0]); cv.set(40, 19, BAY[0]); cv.set(39, 16, BAY[2])
    for t in range(9):  # the mane
        cv.set(30 + t, 11 + int(t * 0.6), BAY[0]); cv.set(30 + t, 12 + int(t * 0.6), BAY[1])
    for t in range(10):  # the tail
        cv.set(7 - t // 4, 14 + t, BAY[0]); cv.set(8 - t // 4, 14 + t, BAY[1])
    return cv


def horse_tied() -> Canvas:
    """A saddled grey horse tied at the saloon's hitching rail, 24 x 44 (review 19 Oct:
    face it to the rail with a rein, and make it another horse than the corral's bay):
    it stands nose to the rail, so in the town's high three-quarter view we look down on
    its back: the long head reaching north over the beam with the bridle on it and the
    ears pricked at the poll, the neck widening to the shoulders, the barrel under a
    leather saddle on a striped blanket (stirrups hanging either side), the hips and the
    rounded rump toward the street with the tail falling over it, and the hind hooves
    showing behind. A dappled grey coat lit along its left side; the rein looped round
    the rail by its head."""
    w, h = 24, 44
    cv = Canvas(w, h, pad=PAD)
    GREY = ['#34343A', '#5A5A62', '#83838A', '#A9A8AA', '#CFCCC6']
    cx = 11.5

    def half(y):  # the silhouette's half width down its length, from muzzle to rump
        prof = [(0, 1.8), (3, 2.5), (7, 2.6), (9, 2.4), (11, 3.4), (14, 5.4), (17, 6.0), (21, 6.2),
                (24, 7.4), (28, 7.8), (31, 7.0), (33, 5.0), (34, 0)]
        for (y0, h0), (y1, h1) in zip(prof, prof[1:]):
            if y0 <= y <= y1:
                return h0 + (h1 - h0) * (y - y0) / (y1 - y0)
        return 0

    def coat(x, y, k):
        c = GREY[4] if k < -0.55 else GREY[3] if k < 0.15 else GREY[2] if k < 0.65 else GREY[1]
        if noise2(x // 2, y // 2, 811) > 0.78 and c in (GREY[3], GREY[2]):
            c = GREY[min(4, GREY.index(c) + 1)]  # the dapples
        return c
    for lx in (5, 16):  # the hind legs below the rump, the hocks lit on the left, dark hooves
        for y in range(31, 41):
            cv.set(lx, y, GREY[3] if lx < 11 else GREY[2]); cv.set(lx + 1, y, GREY[2] if lx < 11 else GREY[1])
            cv.set(lx + 2, y, GREY[1] if y < 36 else GREY[0]) if y > 31 else None
        cv.hline(lx, 41, 3, '#2A2026'); cv.hline(lx - 1, 42, 4, '#2A2026')
    for y in range(0, 34):
        hw = half(y + 0.5)
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if abs(x + 0.5 - cx) <= hw:
                k = (x + 0.5 - cx) / max(hw, 1) + (0.35 if y > 29 else 0)
                cv.set(x, y, coat(x, y, k))
    cv.hline(10, 0, 3, GREY[1])  # the muzzle, darker
    for (ex, c1, c2) in ((8, GREY[4], GREY[2]), (15, GREY[2], GREY[0])):  # the ears at the poll, pricked
        cv.set(ex, 9, c1); cv.set(ex, 10, c2)
    cv.hline(9, 8, 6, '#3A2618')  # the bridle's browband and cheek straps
    cv.vline(9, 3, 5, '#3A2618'); cv.vline(14, 3, 5, '#3A2618')
    for y in range(11, 18):
        cv.set(13, y, GREY[0])  # the mane falling on its off side
    for (x, y) in ((8, 3), (7, 2), (6, 1), (5, 1), (4, 2), (4, 3), (5, 4)):  # the rein looped round the rail
        cv.set(x, y, '#2E1E14')
    # the rail's beam passes in front of its neck (review 19 Oct): the stretch of the
    # hitching rail at the horse's height, the same rows and tones as hitching_rail, so it
    # meets the rail drawn behind (rows 2-4 here are its rows 5-7 at the rail's y 178, the
    # horse's 181); the muzzle shows above it, over the beam
    for x in range(0, w):
        cv.set(x, 2, BLEACHED[4]); cv.set(x, 3, BLEACHED[2]); cv.set(x, 4, BLEACHED[1])
    for y in range(15, 23):  # the striped blanket under the saddle, showing at the sides
        hw = half(y + 0.5) - 0.5
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if abs(x + 0.5 - cx) <= hw:
                cv.set(x, y, '#E8DCC0' if y % 3 == 0 else '#A8382C' if x < cx else '#842A22')
    for (x, y) in oval(cx, 19, 4.2, 3.4):  # the saddle: the seat, the pommel lit, the cantle behind
        cv.set(x, y, '#8A5A34' if x < cx else '#6A4226')
    cv.hline(10, 15, 4, '#B07C4C'); cv.hline(10, 22, 4, '#4E2E1A')
    for (sx, lit) in ((4, True), (19, False)):  # the stirrups hanging either side
        cv.vline(sx, 19, 5, '#3A2618'); cv.hline(sx - 1, 24, 2, '#C8A060' if lit else '#8A6A40')
    cv.vline(11, 27, 6, GREY[1])  # the cleft of the rump
    for y in range(28, 40):  # the tail falling over the rump between the hind legs
        cv.set(11, y, GREY[0] if y % 3 else GREY[1]); cv.set(12, y, GREY[1])
    return cv


def prickly_pear() -> Canvas:
    """A prickly pear, 20 x 18: flat round pads lit upper left, spines, two red fruit."""
    w, h = 20, 18
    cv = Canvas(w, h, pad=PAD)
    PAD_G = ['#2E5A34', '#447A44', '#62995A', '#8CBB72']
    for (cx, cy, rx, ry) in ((10, 13, 5, 4), (6, 8, 4, 3.5), (14, 7, 3.5, 3.2)):
        for (x, y) in oval(cx, cy, rx, ry):
            k = (x - cx) / rx + (y - cy) / ry
            cv.set(x, y, PAD_G[3] if k < -0.6 else PAD_G[2] if k < 0.4 else PAD_G[1])
        for (dx, dy) in ((-2, -1), (1, 1), (2, -2)):
            cv.set(cx + dx, cy + dy, '#E8DCC8')
    cv.set(6, 4, '#C2453A'); cv.set(7, 4, '#9A3028'); cv.set(15, 3, '#C2453A')
    return cv


# Sunstone's life (S5): animals where they would really be, each drawn alone in the one
# view and light, its shadow left to the zone. A lizard basks on sun-warmed rock in the
# morning; vultures wait on a dead tree near a skull (they perch when there is no thermal
# to ride); a string of laden camels stands tethered nose to tail at the caravan camp.
def _lizard(cv: Canvas, x: int, y: int, facing: int = 1):
    """A desert lizard basking flat on a rock, 14 x 6 (review 19 Oct: the first one read as
    moss): pale sand above with dark brown cross-bands, a dark outline so it reads on the
    sandstone, its tail tapering behind it in a curve, four splayed legs with toes, the head
    raised toward the sun with a dark eye, and its own small shadow on the rock below and to
    the right."""
    SKIN = ['#3A2618', '#6A4A2A', '#A8804E', '#D2B07A', '#ECD6A4']
    ROCK_SH = ADOBE[1]
    body = [(x + facing * t, y + (1 if 3 < t < 7 else 0)) for t in range(10)]
    for i, (bx, by) in enumerate(body):  # its shadow first, one row down and to the right
        cv.set(bx + 1, by + 2, ROCK_SH)
    for t in range(5):  # the tail: thin, curving down and back
        tx, ty = x - facing * (t + 1), y + 1 + t // 2
        cv.set(tx, ty, SKIN[2] if t < 3 else SKIN[1]); cv.set(tx + 1, ty + 1, ROCK_SH)
    for i, (bx, by) in enumerate(body):  # the body: two pixels deep, its back lit
        band = i in (3, 6)
        cv.set(bx, by - 1, SKIN[0])  # the outline along its back
        cv.set(bx, by, SKIN[1] if band else SKIN[4] if i < 6 else SKIN[3])
        cv.set(bx, by + 1, SKIN[1] if band else SKIN[2])
        cv.set(bx, by + 2, SKIN[0])  # and along its belly
    hx = x + facing * 10
    for (dx, dy, c) in ((0, -2, SKIN[0]), (0, -1, SKIN[3]), (1, -2, SKIN[3]), (1, -3, SKIN[0]), (2, -2, SKIN[0]),
                        (1, -1, SKIN[2]), (0, 0, SKIN[2])):
        cv.set(hx + facing * dx, y + dy, c)  # the raised head
    cv.set(hx + facing, y - 2, '#1A1210')  # its eye
    for lx in (1, 7):  # four splayed legs, the toes spread on the warm rock
        for side in (-1, 1):
            fx, fy = x + facing * lx, y + (3 if side > 0 else -2)
            cv.set(fx, fy, SKIN[1]); cv.set(fx - facing, fy + side, SKIN[0]); cv.set(fx + facing, fy + side, SKIN[0])


def lizard_rock(seed: int = 0) -> Canvas:
    """A sandstone outcrop with a lizard basking on its sunlit top, 40 x 26."""
    base = sandstone_outcrop(seed)
    cv = Canvas(40, 26, pad=PAD)
    cv.paste(base, 0, 2)
    _lizard(cv, 9, 7, 1)
    return cv


VULTURE = ['#1C1618', '#2E2628', '#4A3E3C', '#6A5A54', '#C8A890']


def _vulture(cv: Canvas, x: int, y: int, facing: int = 1):
    """A vulture perched, about 12 x 15: its dark wings folded and hunched round it like
    a cloak, their upper edges lit grey-brown, the long primaries crossing below its tail,
    a pale ruff, and a bare pinkish head with a hooked beak, sunk into its shoulders."""
    for yy in range(y, y + 11):
        t = (yy - y) / 10
        hw = 3 + int(2 * math.sin(t * math.pi))
        for xx in range(x - hw, x + hw + 1):
            k = (xx - (x - hw)) / (2 * hw)
            c = VULTURE[3] if (k < 0.3 and yy < y + 7) else VULTURE[2] if k < 0.65 else VULTURE[1]
            if yy == y or (yy == y + 1 and k < 0.6):
                c = VULTURE[3]
            if yy > y + 3 and abs(xx - x) == 1 and yy % 3 == 0:
                c = VULTURE[1]  # the folded feathers
            cv.set(xx, yy, c)
    for d in range(3):  # the primaries, crossed below the tail
        cv.set(x - facing * (1 + d), y + 11 + d // 2, VULTURE[0])
    for xx in range(x - 2, x + 3):
        cv.set(xx, y - 1, VULTURE[4])  # the ruff
    hx = x + facing
    for (px, py, c) in ((hx, y - 2, '#C88878'), (hx + facing, y - 2, '#B07060'), (hx, y - 3, '#D89888'),
                        (hx + facing * 2, y - 2, '#E8DCC8'), (hx + facing * 2, y - 1, '#E8DCC8')):
        cv.set(px, py, c)  # the bare head, the hooked pale beak
    cv.set(hx, y - 3, '#D89888'); cv.set(hx + facing, y - 3, VULTURE[0])  # an eye
    cv.set(x - 1, y + 11, '#4A3A2A'); cv.set(x + 1, y + 11, '#4A3A2A')  # feet on the branch


def snag_vultures() -> Canvas:
    """A dead mesquite, bleached grey, 40 x 58, with two vultures perched on its
    branches, hunched and waiting: the trunk split and lit along its left, bare limbs
    reaching up, its roots in the sand."""
    w, h = 40, 58
    cv = Canvas(w, h, pad=PAD)
    DRY = ['#4A4038', '#6E6458', '#948A7A', '#B8AE9C', '#D8D0BE']
    cx = 18
    for y in range(22, h - 1):  # the trunk
        half = 2 + (1 if y > h - 10 else 0) + (1 if y > h - 4 else 0)
        for x in range(cx - half, cx + half + 1):
            k = (x - (cx - half)) / (2 * half)
            c = DRY[3] if k < 0.35 else DRY[2] if k < 0.7 else DRY[1]
            if (y + x) % 7 == 0 and 0.2 < k < 0.8:
                c = DRY[1]  # cracks in the dead wood
            cv.set(x, y, c)
    for (x0, y0, dx, n) in ((cx - 2, 30, -1, 14), (cx + 2, 26, 1, 16), (cx, 24, -1, 8), (cx + 1, 36, 1, 9)):
        for t in range(n):  # bare limbs, lit on top
            x, y = x0 + dx * t, y0 - int(t * 0.7)
            cv.set(x, y, DRY[3] if dx < 0 else DRY[2]); cv.set(x, y + 1, DRY[1])
    for x in range(cx - 6, cx + 7):  # the roots in the sand
        cv.set(x, h - 1, DESERT[2] if x < cx else DESERT[1])
    _vulture(cv, 8, 10, -1)   # on the west limb
    _vulture(cv, 31, 6, 1)   # on the east limb, higher
    return cv


def camel_string() -> Canvas:
    """Three camels standing tethered nose to tail at the caravan camp, 150 x 66 (review
    19 Oct: not three identical camels in a row): seen from the side like the resting one,
    staggered along a gentle diagonal as a string stands when it has shuffled to a halt,
    each its own animal: the lead camel tall and pale with its head up, laden with a bale
    and a red water skin, roped to a stake; the second darker, its head lowered to nose
    the sand, carrying two clay jars in a net; the last a young one, smaller and sandy,
    under a striped saddle blanket only. Each wears a halter, and a lead rope sags from it
    to the saddle of the camel in front."""
    w, h = 150, 66
    cv = Canvas(w, h, pad=PAD)
    PALE = ['#5A3E2A', '#8E6A48', '#B8946A', '#D8B88C', '#ECD6AE']
    DARK = ['#3A2418', '#5E3E28', '#80583A', '#A27650', '#BE9468']
    ROPE = '#3E2818'

    def standing(ox: int, oy: int, ramp, load: str, head: str, s: float = 1.0):
        """One camel standing, facing east, its feet on row oy + 52 * s: a deep barrel
        under a single hump, long legs with knobbly knees and broad pads, and the neck
        in an S, the head up (`head` 'up') or lowered to the sand ('down'). Returns the
        halter's position and the saddle's rear (where the next rope ties)."""
        def P(x, y):
            return ox + int(x * s), oy + int(y * s)
        body = oval(*P(17, 24), 13 * s, 6 * s) | oval(*P(16, 17), 6 * s, 5 * s)
        for (x, y) in body:
            k = (x - ox - 4 * s) / (26 * s) + (y - oy - 11 * s) / (18 * s)
            cv.set(x, y, ramp[4] if k < 0.5 else ramp[3] if k < 0.9 else ramp[2] if k < 1.25 else ramp[1])
        foot = oy + int(52 * s)
        for (lx, back) in ((7, True), (10, False), (23, True), (26, False)):
            x0, _ = P(lx, 0)
            for y in range(oy + int(28 * s), foot):
                c = ramp[2] if not back else ramp[1]
                if y in (oy + int(38 * s), oy + int(39 * s)):
                    c = ramp[3] if not back else ramp[2]  # the knobbly knee
                cv.set(x0, y, c)
                cv.set(x0 + 1, y, ramp[1] if not back else ramp[0])  # two pixels thick, shaded behind
                if y < oy + int(33 * s):
                    cv.set(x0 - 1, y, c)  # the thigh, thicker
            cv.hline(x0 - 1, foot, 3, ramp[1])  # the broad pad
            cv.set(x0 - 1, foot + 1, '#2A2026'); cv.set(x0 + 1, foot + 1, '#2A2026')
        if head == 'up':
            hx, hy = P(40, 8)
            for t in range(20):
                u = t / 19
                x, y = P(29 + t * 0.55, 22 + math.sin(u * math.pi) * 3 - u * 14)
                for d in range(-2, 2):
                    cv.set(x, y + d, ramp[3] if d < 0 else ramp[2] if d == 0 else ramp[1])
        else:  # the neck reaching forward and down, the head low over the sand
            hx, hy = P(42, 40)
            for t in range(20):
                u = t / 19
                x, y = P(29 + t * 0.62, 20 + u * 19 - math.sin(u * math.pi) * 4)
                for d in range(-1, 2):
                    cv.set(x, y + d, ramp[3] if d < 0 else ramp[2] if d == 0 else ramp[1])
                    cv.set(x + 1, y + d, ramp[2] if d < 1 else ramp[1])
        for (x, y) in oval(hx + 1, hy, 4 * s, 2 * s):
            cv.set(x, y, ramp[3] if y < hy else ramp[2])
        cv.set(hx + int(4 * s), hy + 1, ramp[0]); cv.set(hx, hy - 1, ramp[0])  # the muzzle, a drowsy eye
        cv.set(hx - 2, hy - 2, ramp[2]); cv.set(hx - 1, hy - 3, ramp[2])  # an ear
        cv.vline(hx + 2, hy - 2, 4, ROPE); cv.hline(hx + 2, hy + 2, 3, ROPE)  # the halter
        tx, ty = P(4, 22)
        for t in range(int(6 * s)):  # the tail
            cv.set(tx - t // 3, ty + t, ramp[1])
        if load == 'bale':  # a bale on the near side, a red water skin behind, lashed over the hump
            for (x, y) in oval(*P(14, 17), 5 * s, 4 * s):
                cv.set(x, y, '#C8B48A' if x < ox + 14 * s else '#A8946A')
                if (x + y) % 5 == 0:
                    cv.set(x, y, '#8E7A54')
            for (x, y) in oval(*P(21, 17), 4 * s, 4 * s):
                cv.set(x, y, '#8E3A2E' if x < ox + 21 * s else '#6E2A22')
            cv.hline(*P(9, 14), int(17 * s), ROPE)
        elif load == 'jars':  # two clay jars hung either side in a rope net
            for jx in (12, 22):
                for (x, y) in oval(*P(jx, 19), 3.2 * s, 4.2 * s):
                    cv.set(x, y, '#C8743E' if x < ox + jx * s else '#9A5230')
                cv.hline(*P(jx - 2, 14), 5, '#E0A070')  # its lip
                for y in range(oy + int(15 * s), oy + int(23 * s), 2):
                    cv.hline(ox + int((jx - 3) * s), y, int(6 * s), ROPE) if y % 4 == 0 else None
            cv.hline(*P(10, 13), int(15 * s), ROPE)
        else:  # a striped saddle blanket only
            for (x, y) in oval(*P(16, 19), 7 * s, 4 * s):
                cv.set(x, y, '#E8DCC0' if (x // 2) % 3 == 0 else '#3E6A8A' if x < ox + 16 * s else '#2E506A')
        return (hx + int(5 * s), hy + 1), P(10, 16)

    # back to front: the lead camel (furthest, highest) first, the young one nearest last
    halter1, saddle1 = standing(96, 0, PALE, 'bale', 'up')
    halter2, saddle2 = standing(50, 6, DARK, 'jars', 'down')
    halter3, _ = standing(8, 18, CAMEL, 'blanket', 'up', 0.86)

    def rope(a, b, sag):
        (x0, y0), (x1, y1) = a, b
        n = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        for t in range(n + 1):
            u = t / n
            cv.set(round(x0 + (x1 - x0) * u), round(y0 + (y1 - y0) * u + math.sin(u * math.pi) * sag), ROPE)
    rope(halter2, saddle1, 4)  # the second's lead rope to the lead camel's saddle
    rope(halter3, saddle2, 5)  # the young one's to the second's
    sx = w - 4  # the lead camel's rope down to a stake driven into the sand
    rope(halter1, (sx, h - 12), 3)
    for y in range(h - 12, h - 1):
        cv.set(sx, y, WOOD[3]); cv.set(sx + 1, y, WOOD[1])
    cv.set(sx, h - 13, WOOD[4])
    return cv


def _budget(items: dict) -> dict:
    """Every sprite held to the house colour budget (rd.limit_colours)."""
    return {k: rd.limit_colours(v) for k, v in items.items()}


def props() -> dict[str, Canvas]:
    return _budget({
        'saloon': false_front(104, 0, RED, 'saloon'), 'store': store(),
        'water_tower': water_tower(), 'saguaro': saguaro(True), 'saguaro_small': saguaro(False),
        'tumbleweed': tumbleweed(), 'wagon': wagon(), 'windpump': windpump(), 'trough': trough(),
        'cow_skull': cow_skull(), 'mine_portal': mine_portal(), 'dry_well': dry_well(), 'keg': keg(),
        'hay_bale': hay_bale(), 'dynamite_crate': dynamite_crate(), 'hitching_rail': hitching_rail(),
        'poster_board': poster_board(), 'corral_side': corral_side(), 'corral_gate': corral_gate(), 'corral_rail': corral_rail(),
        'palm': palm(True), 'palm_small': palm(False), 'sandstone_arch': sandstone_arch(), 'awning': awning(),
        'water_jar': water_jar(), 'camel': camel(), 'camel_b': camel(1), 'tent': tent(), 'fire_pit': fire_pit(),
        'column_stump': column_stump(0), 'column_stump_b': column_stump(2), 'papyrus': papyrus(), 'shaduf': shaduf(),
        'water_crane': water_crane(), 'acacia': acacia(), 'desert_scrub': desert_scrub(0),
        'desert_scrub_b': desert_scrub(4), 'sandstone_outcrop': sandstone_outcrop(0), 'sandstone_outcrop_b': sandstone_outcrop(5),
        'horse': horse(), 'horse_tied': horse_tied(), 'prickly_pear': prickly_pear(), 'ore_tub': ore_tub(),
        'lizard_rock': lizard_rock(0), 'lizard_rock_b': lizard_rock(5), 'snag_vultures': snag_vultures(),
        'camel_string': camel_string(),
    })


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (224, 181, 131, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/west-props.png'))
    print('sheet', out.size)

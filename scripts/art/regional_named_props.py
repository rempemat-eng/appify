"""Named things for the regions beyond the valley (Claude B; Claude A's to-b-0120, from
docs/vision/regions/props.md section 3): for Sunstone's steppe the lone pine and the
drove well (Claude D keeps the wind pump, caravan camp, cliff shrine and wagon wreck), and
for Cogsworth and the coal hills the pit head, the charcoal burners' camp, the tram tipple
and the lookout over the Narrows.

Built from the house style's own pieces (style_sheet.py: parts, courses, boards, cylinders,
the house outline in each material's edge tone), in the house palette with light from the
upper left, at the size guide's scale, on footings of whole 8 px cells, and with every
part there for a reason: what holds it up, what it is for, who works it.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
from style_sheet import T, boards, courses, cylinder, leafy, outline, part, rect, sib, step, stone_pick, tone_at  # noqa: E402

PAD = 16


def finish(cv: Canvas) -> Canvas:
    """The house outline round the drawing, in each material's edge tone (style_sheet.outline),
    on a canvas one pixel bigger each way so the outline has room."""
    out = Canvas(cv.w + 2, cv.h + 2, pad=PAD)
    for y in range(-cv.pad, cv.h + cv.pad):
        for x in range(-cv.pad, cv.w + cv.pad):
            c = cv.get(x, y)
            if c[3] and -1 <= x <= cv.w and -1 <= y <= cv.h:
                out.set(x + 1, y + 1, c)
    outline(out)
    return out


def clean(cv: Canvas, passes: int = 2) -> Canvas:
    """Detail in clusters: a pixel unlike all its drawn neighbours (two or more drawn)
    takes the commonest of theirs."""
    p = cv.pad
    for _ in range(passes):
        changed = []
        for y in range(-p, cv.h + p):
            for x in range(-p, cv.w + p):
                c = cv.get(x, y)
                if not c[3]:
                    continue
                ns = [cv.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                ns = [n for n in ns if n[3]]
                if len(ns) >= 2 and all(n != c for n in ns):
                    changed.append((x, y, max(ns, key=ns.count)))
        for (x, y, c) in changed:
            cv.set(x, y, c)
        if not changed:
            break
    return cv


def shadow(cv: Canvas, x0: int, x1: int, y: int, depth: int = 2):
    """The soft contact shadow under a thing, down and to the east of its foot."""
    for d in range(depth):
        for x in range(x0 + d, x1 + d + 2):
            if not cv.get(x, y + d)[3]:
                cv.set(x, y + d, (24, 18, 30, 90 - d * 30))


def tuft(cv: Canvas, x: int, y: int, ramp: str = 'grass', base: int = 3):
    """A tuft of grass at a foot: two blades lit, one in shade."""
    for (dx, dy, k) in ((0, 0, 0), (0, -1, 1), (1, 0, -1), (-1, 0, 0), (1, -2, 1), (-1, -1, 1)):
        cv.set(x + dx, y + dy, T(ramp, base + k))


# ---- Sunstone's steppe ---------------------------------------------------------------------

def lone_pine() -> Canvas:
    """The lone pine on the steppe's rise (props.md: "lone pine viewpoint"): a Scots pine
    bent east by the prevailing wind, its trunk leaning and twisting up from roots that
    grip a split rock, orange bark in plates high on the trunk and grey and fissured at the
    foot; its crown flattened into windswept pads of needles, each pad lit on top and
    shaded beneath, with sky between them; a dead snag on the windward side, cones on the
    ground. The conifer kind, 64 to 125 tall and 28 to 48 wide."""
    w, h = 48, 88
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    # the rock it grips: a split slab of grey stone, lit on its top and west
    for (x, y) in oval(22, foot - 3, 16, 4.5):
        if y > foot:
            continue
        u, v = (x + 0.5 - 22) / 16, (y + 0.5 - foot + 3) / 4.5
        k = 5 if v < -0.55 and u < 0.3 else 4 if v < -0.2 else 3 if u < 0.4 else 2
        if abs(x - 27) < 1 and v > -0.6:
            k = 1  # the split
        cv.set(x, y, T(sib('stone', noise2(x // 5, y // 3, 501), 0.3), k))
    # the trunk: leaning east as it rises, twisting, thick at the foot
    path = []
    for t in range(0, 61):
        y = foot - 5 - t
        x = 16 + t * 0.28 + 1.8 * math.sin(t / 11.0)
        width = 6.5 - t * 0.06
        path.append((x, y, width))
    for (x, y, wd) in path:
        for k in range(int(round(wd))):
            u = k / max(1, wd - 1)
            high = y < foot - 30
            ramp = 'clay' if high else 'timber_cool'
            base = 4 if u < 0.3 else 3 if u < 0.65 else 2
            if noise2(int(x + k) // 2, int(y) // 3, 502) > 0.74:
                base -= 1  # a fissure between bark plates
            cv.set(int(x - wd / 2 + k), int(y), T(ramp, base))
    # roots gripping over the rock, lit on top
    for (sx, ex, sy) in ((12, 2, foot - 6), (19, 30, foot - 6), (14, 8, foot - 5)):
        n = abs(ex - sx)
        for k in range(n):
            x = sx + (k if ex > sx else -k)
            y = sy + int(k * 3 / max(1, n))
            cv.set(x, y, T('timber_cool', 4)); cv.set(x, y + 1, T('timber_cool', 2))
    # the limbs, swept east by the wind, out to the pads
    limbs = [((22, foot - 52), (40, foot - 64)), ((20, foot - 44), (6, foot - 54)), ((25, foot - 60), (36, foot - 76)),
             ((24, foot - 64), (18, foot - 80))]
    for (a, b) in limbs:
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
        for k in range(n + 1):
            x = a[0] + (b[0] - a[0]) * k / n
            y = a[1] + (b[1] - a[1]) * k / n
            cv.set(int(x), int(y), T('clay', 3)); cv.set(int(x), int(y) + 1, T('clay', 1))
    # the needle pads: flat, wind-shorn, lit on top, a dark underside, needles in short strokes
    pads = [(24, foot - 79, 15, 6.0), (11, foot - 70, 10, 5.0), (37, foot - 70, 11, 5.5), (28, foot - 64, 12, 5.0),
            (40, foot - 60, 7, 4.0), (8, foot - 56, 7, 3.6)]  # back to front
    for pi, (cx, cy, rx, ry) in enumerate(pads):  # each pad a crown of needle clumps (style_sheet.leafy), wind-flattened
        shape = leafy(cv, cx, cy, rx, ry, seed=503 + pi, ramp='leaf_cool')
        for (x, y) in shape:  # the pad's underside in the shade of its own needles
            if (x, y + 1) not in shape or (x, y + 2) not in shape:
                step(cv, x, y, -1, floor=1)
    for k in range(9):  # cones hanging under the pads, in twos, brown lit on their west
        px, py, prx, pry = pads[k % len(pads)]
        x = int(px - prx * 0.6 + noise2(k, 1, 504) * prx * 1.2)
        y = int(py + pry * 0.55)
        if tone_at(cv, x, y) and tone_at(cv, x + 1, y):
            cv.set(x, y, T('timber_warm', 4)); cv.set(x + 1, y, T('timber_warm', 2)); cv.set(x, y + 1, T('timber_warm', 2))
    for (hx, hy) in ((22, foot - 74), (34, foot - 66)):  # sky through the crown, a limb crossing it
        for (x, y) in oval(hx, hy, 2.4, 1.4):
            cv.set(x, y, (0, 0, 0, 0))
        cv.hline(hx - 2, hy, 4, T('clay', 2))
    # a dead snag on the windward (west) side, bleached
    for k in range(10):
        cv.set(14 - k // 2, foot - 46 - k, T('bleached', 4)); cv.set(15 - k // 2, foot - 46 - k, T('bleached', 2))
    cv.set(9, foot - 56, T('bleached', 3)); cv.set(10, foot - 55, T('bleached', 4))
    # fallen cones and needles on the rock's foot
    for (x, y) in ((34, foot - 1), (36, foot), (6, foot)):
        cv.hline(x, y, 2, T('timber_warm', 3)); cv.set(x, y - 1, T('timber_warm', 4))
    shadow(cv, 6, 40, foot + 1)
    tuft(cv, 4, foot, 'grass_warm'); tuft(cv, 40, foot, 'grass_warm')
    return finish(clean(cv))


def drove_well() -> Canvas:
    """The drove well on the steppe (props.md: "drove well"): where no timber grows, the
    well is roofed with a corbelled stone dome, courses of flat stones each stepping in a
    little, its opening on the south dark inside with the bucket on its chain, a flat
    cap-stone on top; a stone basin trough before the opening for driven stock, its water
    dark and lit at the far lip, the ground round it trodden bare and wet. The well kind,
    30 to 44 tall and 24 to 34 wide."""
    w, h = 32, 40
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    base_y = foot - 7
    # the dome: corbelled courses, each a little narrower, lit at the upper west
    for ci in range(9):
        y0 = base_y - (ci + 1) * 3
        half = 14 - int(ci * ci * 0.17) - ci // 2
        if half < 3:
            break
        x = 16 - half
        si = 0
        while x < 16 + half:
            ln = 5 + int(noise2(ci, si, 511) * 4)
            ln = min(ln, 16 + half - x)
            u = (x + ln / 2 - (16 - half)) / (2 * half)
            base = 4 if u < 0.3 else 3 if u < 0.7 else 2
            part(cv, x, y0, ln, 3, sib('stone', noise2(ci, si, 512), 0.3), base, seam=T('stone_cool', 1))
            x += ln
            si += 1
    part(cv, 12, base_y - 29, 8, 3, 'stone_warm', 4, seam=T('stone_cool', 1))  # the cap-stone
    # the opening on the south, dark inside, its lintel slab, the bucket on its chain
    for y in range(base_y - 14, base_y + 1):
        half = 4 if y > base_y - 12 else 3
        for x in range(16 - half, 16 + half):
            cv.set(x, y, T('stone', 0) if y < base_y - 4 else T('soot', 1))
    part(cv, 10, base_y - 16, 12, 3, 'stone_warm', 4, seam=T('stone_cool', 1))
    for y in range(base_y - 13, base_y - 7):
        cv.set(17, y, T('iron', 3 if y % 2 else 2))
    part(cv, 15, base_y - 7, 5, 4, 'timber', 3)
    cv.hline(15, base_y - 7, 5, T('iron', 3))
    # the stone basin trough before the opening
    for y in range(base_y + 1, foot - 1):
        for x in range(4, 28):
            r = y - base_y - 1
            k = 5 if r == 0 else 3 if x < 24 else 2
            if r >= 3:
                k -= 1
            cv.set(x, y, T(sib('stone', noise2(x // 6, 0, 513), 0.3), k))
    for x in range(6, 26):  # the water in it, dark under the near lip, the far lip's light on it
        cv.set(x, base_y + 2, T('water', 2) if x > 9 else T('water', 4))
        cv.set(x, base_y + 3, T('water', 1))
    # the trodden ground round it, damp and darker
    for x in range(1, 31):
        cv.set(x, foot - 1, T('path', 2 if (x // 3) % 2 else 3))
        cv.set(x, foot, T('path', 2))
    shadow(cv, 4, 28, foot + 1)
    tuft(cv, 1, foot - 1, 'grass_warm'); tuft(cv, 30, foot - 1, 'grass_warm')
    return finish(clean(cv))


# ---- the coal hills and the Narrows (Cogsworth) --------------------------------------------

def beam(cv: Canvas, a, b, wd: int = 3, ramp: str = 'timber', base: int = 3):
    """A squared timber from a to b, its west (or top) face lit, its east (or under) face
    dark, the grain along it in short darker runs."""
    (x0, y0), (x1, y1) = a, b
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    steep = abs(y1 - y0) >= abs(x1 - x0)
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / max(1, n)
        y = y0 + (y1 - y0) * k / max(1, n)
        for d in range(wd):
            px, py = (int(round(x)) + d, int(round(y))) if steep else (int(round(x)), int(round(y)) + d)
            u = d / max(1, wd - 1)
            kk = base + 1 if u < 0.34 else base if u < 0.67 else base - 1
            if noise2(k // 3, d, int(x0 * 7 + y0)) > 0.82 and kk > 1:
                kk -= 1
            cv.set(px, py, T(sib(ramp, noise2(k // 6, 0, int(x0 + y0 * 3)), 0.25), kk))


def pit_head() -> Canvas:
    """The pit head on the coal hills (props.md: "pit head"): a timber headframe over the
    shaft, two upright legs braced by girts and crossed struts, two raking back-legs that
    take the rope's pull toward the winding engine behind, the iron sheave wheel at the top
    on its bearing deck under a little roof, the rope running down the shaft to the cage at
    the banking deck and back over the wheel toward the engine house; at the foot the brick
    shaft collar, a coal tub on its rails, the banksman's bell and lamp. The tower kind,
    104 to 176 tall and 32 to 64 wide."""
    w, h = 56, 120
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    deck = foot - 14
    # the raking back-legs first, behind: from the top of the frame down and away to the north-west
    beam(cv, (16, 18), (2, deck), 3, 'timber', 2)
    beam(cv, (40, 18), (52, deck), 3, 'timber', 2)
    # the upright legs and the girts and crossed struts between them
    for lx in (13, 39):
        beam(cv, (lx, 16), (lx, deck), 4, 'timber', 3)
    for gy in (34, 56, 78):
        beam(cv, (16, gy), (39, gy), 3, 'timber', 3)
    for (y0, y1) in ((37, 56), (59, 78), (81, deck)):
        beam(cv, (17, y0), (38, y1 - 1), 2, 'timber', 2)
        beam(cv, (37, y0), (17, y1 - 1), 2, 'timber', 3)
    # the bearing deck and its little roof, the sheave wheel on its axle
    part(cv, 9, 14, 38, 4, 'timber', 3)
    for (x, y) in oval(28, 9, 9.5, 9.5):  # the sheave wheel above the deck, iron: rim, spokes and hub
        r = math.hypot(x + 0.5 - 28, y + 0.5 - 9)
        a = math.atan2(y + 0.5 - 9, x + 0.5 - 28)
        if r > 7.6:
            cv.set(x, y, T('iron', 4 if (x < 28 and y < 9) else 3 if x < 30 else 2))
        elif r < 2:
            cv.set(x, y, T('iron', 4 if x < 28 else 2))
        elif abs(math.sin(a * 3)) < 0.25:
            cv.set(x, y, T('iron', 3))
    # the ropes: down the shaft to the cage, and back over the wheel toward the engine house
    for y in range(22, deck - 10):
        cv.set(27, y, T('soot', 3)); cv.set(28, y, T('soot', 1))
    for k in range(22):  # the rope off the wheel's back toward the engine house
        cv.set(20 - k * 18 // 22, 3 + k, T('soot', 2))
    beam(cv, (18, 14), (18, 4), 2, 'iron', 3)  # the wheel's pedestals
    beam(cv, (37, 14), (37, 4), 2, 'iron', 2)
    # the cage at the banking deck: an iron box with mesh sides, its keps, a tub inside
    for y in range(deck - 12, deck):
        for x in range(21, 35):
            edge = x in (21, 34) or y in (deck - 12, deck - 1)
            if edge:
                cv.set(x, y, T('iron', 4 if (x == 21 or y == deck - 12) else 2))
            elif (x + y) % 3 == 0:
                cv.set(x, y, T('iron', 3))
            else:
                cv.set(x, y, T('soot', 1))
    part(cv, 24, deck - 6, 8, 5, 'iron_warm', 3)
    # the banking deck and the brick shaft collar under it
    part(cv, 0, deck, w, 3, 'timber', 4)
    for y in range(deck + 3, foot - 1):
        for x in range(4, w - 4):
            ci, r = divmod(y - deck - 3, 3)
            j = (x + (4 if ci % 2 else 0)) % 8
            k = 1 if r == 2 or j == 0 else (4 if x < 14 else 3 if x < w - 12 else 2)
            cv.set(x, y, T(sib('clay', noise2((x + 4 * ci) // 8, ci, 521), 0.3), k))
    part(cv, 22, deck + 5, 12, 5, 'brass', 3)  # the shaft's number plate on the collar
    for k in range(3):
        cv.hline(24 + k * 3, deck + 7, 2, T('brass', 1))
    for x in range(4, w - 4):  # coal dust darkening the collar's top course
        if noise2(x // 3, 0, 522) > 0.5:
            step(cv, x, deck + 3, -1, floor=1)
    for wx in (8, 44):  # iron tie plates on the collar
        part(cv, wx, deck + 6, 4, 4, 'iron', 3)
    # a coal tub on the deck rails, heaped, and the rails
    cv.hline(0, deck - 1, 20, T('iron', 4))
    part(cv, 2, deck - 8, 12, 6, 'iron', 3)
    for x in range(3, 13):  # its heap of coal, glinting
        cv.set(x, deck - 9, T('soot', 2 if x % 3 else 4)); cv.set(x + (x % 2), deck - 10, T('soot', 1)) if 5 < x < 11 else None
    for wx in (4, 11):
        cv.hline(wx, deck - 2, 2, T('iron', 1))
    # the banksman's signal bell on the east leg and a lamp
    part(cv, 43, deck - 22, 4, 4, 'brass', 4)
    cv.set(44, deck - 18, T('iron', 2))
    part(cv, 8, deck - 26, 3, 4, 'lamp', 4)
    cv.set(9, deck - 27, T('iron', 3))
    shadow(cv, 4, w - 4, foot)
    return finish(clean(cv))


def tram_tipple() -> Canvas:
    """The tram tipple at the foot of the coal hills (props.md: "tram tipple"): the tramway
    from the drifts runs out on a timber trestle to a tipping cradle at its end, where a
    tub is tipped forward to drop its coal down a plated chute into the wagon waiting on
    the siding below; the trestle's bents braced with crossed struts on stone footings,
    the cradle's iron pivot and its lever, coal dust black round the chute's mouth and a
    spill heaped on the ground. Unmeasured (a structure, 72 wide)."""
    w, h = 72, 60
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    top = 14
    # the trestle: three bents of two posts, braced, on stone footings
    for bx in (6, 26, 46):
        beam(cv, (bx, top + 3), (bx - 3, foot - 3), 3, 'timber', 3)
        beam(cv, (bx + 8, top + 3), (bx + 11, foot - 3), 3, 'timber', 2)
        beam(cv, (bx, top + 8), (bx + 9, foot - 8), 2, 'timber', 3)
        beam(cv, (bx + 9, top + 8), (bx, foot - 8), 2, 'timber', 2)
        beam(cv, (bx - 1, top + 22), (bx + 10, top + 22), 2, 'timber', 3)
        for fx in (bx - 5, bx + 9):
            part(cv, fx, foot - 3, 6, 3, sib('stone', noise2(fx, 0, 531), 0.3), 3)
    # the stringers and the deck with its rails
    part(cv, 0, top, 60, 4, 'timber', 4)
    cv.hline(0, top - 1, 60, T('iron', 4)); cv.hline(0, top - 2, 60, T('iron', 2))
    for x in range(0, 60, 5):
        cv.set(x, top + 1, T('timber', 1))  # the sleeper ends
    # a full tub coming along the rails
    part(cv, 8, top - 9, 11, 7, 'iron', 3)
    for x in range(9, 18):
        cv.set(x, top - 10, T('soot', 2 if x % 3 else 4))
    # the tipping cradle at the end, tilted forward, its tub tipping coal down the chute
    for k in range(12):
        x, y = 58 + k, top - 6 + k // 2
        cv.set(x, y, T('iron', 3)); cv.set(x, y + 1, T('iron', 1))
    part(cv, 60, top - 4, 9, 6, 'iron_warm', 3)
    for (x, y) in oval(60, top + 2, 2, 2):
        cv.set(x, y, T('iron', 4 if x < 60 else 2))  # the pivot
    beam(cv, (58, top - 12), (63, top + 1), 2, 'iron', 3)  # the lever
    # the chute: plated, sloping down to the siding, coal in it
    for k in range(20):
        x = 60 + k // 3
        y = top + 4 + k
        cv.hline(x, y, 8, T('iron', 3 if k % 4 else 2))
        cv.set(x + 2 + (k % 3), y, T('soot', 1))
    # the wagon on the siding below, half loaded, and the spill on the ground
    part(cv, 54, foot - 14, 18, 9, 'timber_cool', 3)
    for x in range(55, 71):
        cv.set(x, foot - 15, T('soot', 2 if x % 3 else 4))
    for wx in (56, 66):
        for (x, y) in oval(wx + 1, foot - 4, 2.5, 2.5):
            cv.set(x, y, T('iron', 4 if x <= wx else 2))
    for (x, y) in oval(46, foot - 1, 7, 2):
        cv.set(x, y, T('soot', 2 if (x + y) % 4 else 4))
    shadow(cv, 0, w - 2, foot)
    return finish(clean(cv))


def lookout() -> Canvas:
    """The lookout over the Narrows (props.md: "lookout over the Narrows"): a timber tower
    on four legs splayed for the wind, girts and crossed struts between them, a ladder up
    the south face through a hatch, the platform at the top with its handrail and a little
    pyramid roof of shingles against the rain, a flag on the roof; the legs on stone pads.
    The tower kind, 104 to 176 tall and 32 to 64 wide."""
    w, h = 44, 116
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    plat = 30
    # the back legs, then the front legs, splayed
    beam(cv, (13, plat), (6, foot - 3), 3, 'timber', 2)
    beam(cv, (29, plat), (36, foot - 3), 3, 'timber', 2)
    beam(cv, (10, plat), (2, foot - 3), 4, 'timber', 3)
    beam(cv, (32, plat), (39, foot - 3), 4, 'timber', 3)
    for gi, gy in enumerate((54, 78, 100)):  # girts and crossed struts
        half = 11 + (gy - plat) * 8 // (foot - plat)
        beam(cv, (21 - half, gy), (22 + half, gy), 2, 'timber', 3)
    for (y0, y1) in ((plat + 2, 54), (56, 78), (80, 100)):
        h0 = 11 + (y0 - plat) * 8 // (foot - plat)
        h1 = 11 + (y1 - plat) * 8 // (foot - plat)
        beam(cv, (21 - h0 + 2, y0), (22 + h1 - 2, y1), 2, 'timber', 2)
        beam(cv, (22 + h0 - 2, y0), (21 - h1 + 2, y1), 2, 'timber', 3)
    # the ladder up the middle of the south face
    for y in range(plat + 2, foot - 2):
        cv.set(18, y, T('timber', 4)); cv.set(24, y, T('timber', 2))
        if (y - plat) % 5 == 0:
            cv.hline(19, y, 5, T('timber', 3))
    # the platform, its handrail on posts, the hatch
    part(cv, 4, plat - 3, 36, 4, 'timber', 4)
    for px in (5, 14, 23, 32, 38):
        beam(cv, (px, plat - 12), (px, plat - 3), 2, 'timber', 3)
    beam(cv, (4, plat - 12), (40, plat - 12), 2, 'timber', 4)
    beam(cv, (4, plat - 8), (40, plat - 8), 1, 'timber', 3)
    # the pyramid roof of shingles over the platform, its finial and flag
    for y in range(4, plat - 13):
        half = 3 + (y - 4) * 19 // (plat - 17)
        for x in range(22 - half, 22 + half):
            course = (y - 4) // 3
            k = (4 if x < 22 else 2) if (y - 4) % 3 else (3 if x < 22 else 1)
            if (x + course * 2) % 5 == 0 and (y - 4) % 3:
                k -= 1
            cv.set(x, y, T(sib('timber', noise2(x // 5, course, 541), 0.3), k))
    for (mx, my) in ((28, 12), (29, 12), (30, 13), (33, 15), (34, 15), (14, 15), (15, 15)):  # moss in the roof's lee
        cv.set(mx, my, T('leaf', 3 if mx > 20 else 4))
    for x in range(5, 39):  # the roof's eaves board, lit, its shadow on the rail
        cv.set(x, plat - 13, T('timber', 4 if x < 22 else 3))
    cv.vline(22, 0, 4, T('iron', 3))
    for y in range(0, 4):  # the flag, red, catching the wind to the east
        cv.hline(23, y, 6 - y // 2, T('berry', 4 if y < 2 else 3))
    for fx in (0, 37):  # stone pads under the front legs
        part(cv, fx, foot - 3, 7, 3, sib('stone', noise2(fx, 1, 542), 0.3), 3)
    shadow(cv, 2, w - 2, foot)
    tuft(cv, 10, foot); tuft(cv, 32, foot)
    return finish(clean(cv))


def charcoal_clamp() -> Canvas:
    """The charcoal burners' clamp (props.md: "charcoal burners' camp"): a low dome of
    cordwood stacked round a central flue and sealed with turf and earth, the turfs laid
    in rough courses, darker and scorched near the top, little vent holes poked round its
    shoulder showing dark, the flue's mouth at the crown capped with a turf; a ladder laid
    on its side for the burner to climb and a rake beside it. Unmeasured (a mound, 48 wide)."""
    w, h = 48, 22
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    for (x, y) in oval(24, foot - 1, 22, 15):
        if y > foot:
            continue
        u, v = (x + 0.5 - 24) / 22, (y + 0.5 - foot + 1) / 15
        k = 4 if u + v * 1.2 < -0.9 else 3 if u + v < -0.2 else 2 if u < 0.5 else 1
        course = (y - (foot - 16)) // 3
        if (y + (x // 6)) % 3 == 0:
            k = max(1, k - 1)  # the joint between turfs
        fam = 'earth' if v > -0.55 else 'soot'  # scorched near the crown
        if fam == 'earth' and noise2(x // 5, course, 551) > 0.7:
            fam = 'grass'  # a turf still green
        cv.set(x, y, T(sib(fam, noise2(x // 6, course, 552), 0.3) if fam != 'soot' else 'soot', k))
    for vx in (8, 16, 33, 40):  # vent holes round the shoulder
        vy = foot - 1 - int(15 * math.sqrt(max(0.0, 1 - ((vx + 0.5 - 24) / 22) ** 2))) + 4
        cv.hline(vx, vy, 2, T('soot', 0))
    part(cv, 21, foot - 17, 6, 3, 'grass', 3)  # the turf capping the flue
    for k in range(18):  # the ladder laid on its east side
        cv.set(30 + k // 2, foot - 13 + k // 2, T('timber', 4)); cv.set(34 + k // 2, foot - 15 + k // 2, T('timber', 2))
        if k % 4 == 0:
            cv.hline(30 + k // 2, foot - 14 + k // 2, 4, T('timber', 3))
    for k in range(12):  # the rake against its west foot
        cv.set(2 + k // 3, foot - 12 + k, T('bleached', 4))
    cv.hline(1, foot - 13, 5, T('iron', 3))
    shadow(cv, 2, w - 2, foot)
    return finish(clean(cv))


def burners_hut() -> Canvas:
    """The charcoal burners' hut: a cone of poles leaned together and thatched with turf
    and bracken, a low doorway on the south with a sacking curtain, the poles' tops
    crossing out of the smoke hole, a stool and a kettle by the door. The tent kind,
    32 to 48 tall."""
    w, h = 36, 40
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    for y in range(6, foot - 2):  # the turf skin in rows, each row's lower edge in shade, lit at the west
        half = 2 + (y - 6) * 15 // (foot - 6)
        for x in range(18 - half, 18 + half):
            u = (x - (18 - half)) / max(1, 2 * half)
            k = 4 if u < 0.28 else 3 if u < 0.62 else 2 if u < 0.85 else 1
            course = (y - 6) // 4
            if (y - 6) % 4 == 3:
                k = max(1, k - 1)
            elif (y - 6) % 4 == 0 and (x + course * 3) % 6 == 0:
                k = max(1, k - 1)  # the joint between two turfs
            n = noise2((x + course * 3) // 5, course, 561)
            fam = 'earth_warm' if n < 0.45 else 'grass_warm' if n < 0.75 else 'earth' if n < 0.9 else 'timber_warm'
            cv.set(x, y, T(fam, k))
    for x in range(1, 35):  # a footing ring of field stones holding the turf down
        part(cv, x, foot - 3, 4, 3, sib('stone', noise2(x, 2, 563), 0.3), 4 if x < 12 else 3 if x < 26 else 2, glint=False) if x % 4 == 1 else None
    for k in range(10):  # bracken fronds tucked in over the turf, rust-brown and green
        fx = 8 + int(noise2(k, 0, 562) * 20)
        fy = 12 + int(noise2(0, k, 562) * 18)
        if tone_at(cv, fx, fy) and tone_at(cv, fx + 2, fy):
            fam = 'clay' if k % 2 else 'leaf_warm' if 'leaf_warm' else 'leaf'
            cv.hline(fx, fy, 3, T(fam, 4)); cv.set(fx + 1, fy + 1, T(fam, 2))
    for py in range(10, foot - 2, 9):  # the poles' edges showing at the lit side
        half = 2 + (py - 6) * 15 // (foot - 6)
        cv.set(18 - half, py, T('timber', 4)); cv.set(18 - half, py + 1, T('timber', 3))
    for (dx, dy) in ((-3, -5), (-1, -6), (2, -6), (4, -4)):  # pole tops through the smoke hole
        beam(cv, (18, 7), (18 + dx, 7 + dy), 1, 'timber', 3)
    for y in range(foot - 16, foot):  # the doorway, its sacking curtain hooked aside
        half = 4 if y > foot - 14 else 3
        for x in range(18 - half, 18 + half):
            cv.set(x, y, T('soot', 1) if x > 16 else T('sand_cool', 3 if y % 3 else 2))
    part(cv, 28, foot - 7, 5, 4, 'timber', 3)  # a stool
    beam(cv, (5, foot - 16), (2, foot - 3), 1, 'timber', 3)  # the kettle's tripod over a cold hearth
    beam(cv, (5, foot - 16), (8, foot - 3), 1, 'timber', 2)
    cv.vline(5, foot - 15, 6, T('iron', 2))
    part(cv, 3, foot - 9, 5, 4, 'iron', 3)
    for (x, y) in ((2, foot - 1), (3, foot), (6, foot), (7, foot - 1)):
        cv.set(x, y, T('soot', 2))
    shadow(cv, 4, w - 3, foot)
    return finish(clean(cv))


def cordwood() -> Canvas:
    """Cordwood stacked for the next clamp: split billets laid between two stakes at each
    end, their sawn ends to the south showing pale rings and dark bark, a wedge of bark and
    chips on the ground. The woodpile kind."""
    w, h = 40, 21
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    for row in range(3):  # three rows of billets, each end a disc: bark rim, pale wood, the heart
        y = foot - 4 - row * 6
        for i in range(5 - (row % 2)):
            cx = 7 + i * 7 + (3 if row % 2 else 0)
            if row == 2 and not 0 < i < 3:
                continue
            for (x, y2) in oval(cx, y, 3.4, 3.1):
                d = math.hypot((x + 0.5 - cx) / 3.4, (y2 + 0.5 - y) / 3.1)
                lit = (x - cx) + (y2 - y) < 0
                if d > 0.72:
                    cv.set(x, y2, T('timber_cool', 2 if lit else 1))  # the bark
                elif d > 0.3:
                    cv.set(x, y2, T(sib('sand', noise2(i, row, 571), 0.3), 4 if lit else 3))  # the sapwood
                else:
                    cv.set(x, y2, T('timber_warm', 3))  # the heart
            cv.set(cx + 1, y - 1, T('timber_warm', 2))  # a check (crack) across the end
    for sx in (1, 37):
        beam(cv, (sx, 1), (sx, foot), 2, 'timber', 3)  # the stakes
    for x in range(3, 38, 3):
        cv.set(x, foot, T('timber_cool', 2))  # chips and bark on the ground
    shadow(cv, 2, w - 2, foot)
    return finish(clean(cv))


def props() -> dict[str, Canvas]:
    return {
        'lone_pine': lone_pine(), 'drove_well': drove_well(),
        'pit_head': pit_head(), 'tram_tipple': tram_tipple(), 'narrows_lookout': lookout(),
        'charcoal_clamp': charcoal_clamp(), 'burners_hut': burners_hut(),
    }

"""House-style design kits, one per environment (docs/vision/house-style.md, "Kits").

Matt, 20 Oct ~11:35: "you can use the house style where it fits but mindful of the
environment. but within the same environment you can reuse it. but to make it less
repetative perhaps come up with a few different designs that you can then reuse".

So each environment has its own kit of reusable pieces, every piece in the house style
(house palette, parts and clusters, light from the upper left, edge-tone outline) and in
a few distinct variants:

    front(env, v)    a whole building front: wall, roof edge, door, windows, sign
    door(env, v)     a door in its surround, on a patch of the environment's wall
    window(env, v)   a window in its wall
    roof(env, v)     the roof or top edge as it meets the wall
    sign(env, v)     a sign, awning, banner or label
    prop(env, v)     a small prop that belongs there

`env` is one of ENVS; `v` is 0 .. variants(env, piece) - 1. Everything is deterministic and
sized by the scale table (verticality.md 5: an adult 25 px, a door 14 x 28, a shop's double
door 22 x 32, an upper storey 32 px, a window 12 to 16 wide). A front is a sprite with its
outline; a door, window or roof is drawn into a patch of its own wall, which is how a zone
uses it (draw the wall, then the pieces into it).

    python3 scripts/art/house_kits.py [OUT_DIR]

writes one kit sheet per environment (OUT_DIR/kit-<env>.png, at 3x, with today's
equivalents on the left) and prints the style lint and the detail bar for every front.
Nothing in the game reads this file yet; the lanes draw from it as their zones move to the
house style.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw  # noqa: E402

import house_palette as hp  # noqa: E402
from pixel import Canvas, disc, noise2, smooth_noise  # noqa: E402
from style_sheet import (T, sib, step, rect, part, courses, boards, bricks, roof_rows, plates, grain,  # noqa: E402
                         ground, glass, frame, overhang, cylinder, outline, cast, leafy, wall_light,
                         stone_pick, moss_joints, plaster, rivets, banner, H_GRAIN, V_GRAIN, regolith,
                         crater, pebble, tone_at, soft_patches)

ENVS = ('valley', 'cogsworth', 'sunstone', 'hearthold', 'neon', 'halcyon', 'lumen')
TITLES = {
    'valley': 'Valley and isles: cottages', 'cogsworth': 'Cogsworth: brick and iron',
    'sunstone': 'Sunstone Reach: frontier timber and adobe', 'hearthold': 'Hearthold: castle stone',
    'neon': 'Neon Harbour: shopfronts and facades', 'halcyon': 'Halcyon Station: modules',
    'lumen': 'Lumen: habitats and regolith',
}


# --- pictograms (signs use pictures, never words: world-atlas.md) ---------------------------
PICTO = {
    'cup': ['..+.+..', '...+...', '######.', '#####.#', '#####.#', '######.', '.####..'],
    'bread': ['.......', '..###..', '.#+#+#.', '#######', '#######', '.#####.', '.......'],
    'fish': ['.......', '#...##.', '##.##+#', '#######', '##.####', '#...##.', '.......'],
    'key': ['.###...', '#...#..', '#...####', '.###.#.#', '.....#..', '.......', '.......'],
    'moon': ['..###..', '.##....', '##.....', '##.....', '##.....', '.##....', '..###..'],
    'gear': ['.#.#.#.', '#######', '##...##', '##.+.##', '##...##', '#######', '.#.#.#.'],
    'mug': ['++++...', '####...', '####.#.', '####..#', '####.#.', '####...', '.......'],
    'shoe': ['.#...#.', '#.....#', '#.....#', '#.....#', '##...##', '.##.##.', '.......'],
    'star': ['...#...', '..###..', '#######', '.#####.', '..###..', '.##.##.', '##...##'],
    'sack': ['..#.#..', '...#...', '..###..', '.##+##.', '#######', '#######', '.#####.'],
    'anchor': ['..###..', '...#...', '#######', '...#...', '#..#..#', '##.#.##', '.#####.'],
    'bowl': ['#.#.#..', '.#.#.#.', '.......', '#######', '.#####.', '..###..', '.......'],
    'shield': ['#######', '#+..#.#', '#+..#.#', '#######', '.#.#.#.', '..#.#..', '...#...'],
    'bolt': ['...##..', '..##...', '.####..', '...##..', '..##...', '.##....', '#......'],
    'leaf': ['....##.', '..####.', '.##+##.', '.####..', '..#....', '.#.....', '#......'],
    'bed': ['#......', '#.##...', '#######', '#######', '#.....#', '.......', '.......'],
    'pot': ['.#.#.#.', '.......', '#######', '.#####.', '.#####.', '..###..', '.......'],
}


def picto(cv: Canvas, x, y, name, ramp='brass', base=4):
    """A pictogram, lit tone on its top rows, a tone down at its foot."""
    rows = PICTO[name]
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '#':
                cv.set(x + c, y + r, T(ramp, base if r < len(rows) - 2 else base - 1))
            elif ch == '+':
                cv.set(x + c, y + r, T(ramp, base + 1))


# --- walls ---------------------------------------------------------------------------------
def wall(cv: Canvas, x0, y0, w, h, kind, seed=0):
    """A wall of one material, lit at its upper left. The kinds are each environment's
    building materials; nothing else in a kit invents its own."""
    pts = rect(x0, y0, w, h)
    if kind in ('plaster', 'whitewash', 'pink'):
        fam = {'plaster': 'plaster', 'whitewash': 'plaster', 'pink': 'plaster'}[kind]
        plaster(cv, x0, y0, w, h, seed, fam)
        if kind == 'whitewash':   # limewash: the plaster a tone lighter
            for p in pts:
                step(cv, p[0], p[1], 1)
        if kind == 'pink':
            for p in pts:
                if smooth_noise(p[0], p[1], 9, seed) > 0.0:
                    hit = tone_at(cv, *p)
                    if hit:
                        cv.set(p[0], p[1], T('berry', min(5, hit[1] + 2)) if hit[1] >= 3 else T('plaster', hit[1]))
    elif kind == 'drystone':
        courses(cv, x0, y0, w, h, stone_pick(('stone', 'ashlar'), seed), course=5, lengths=(5, 10),
                seam=T('stone_cool', 1), seed=seed)
        grain(cv, pts, 0.05, seed + 1, lit=wall_light(x0, y0, w, h))
    elif kind == 'ashlar':
        courses(cv, x0, y0, w, h, stone_pick(('ashlar', 'ashlar', 'stone'), seed), course=6, lengths=(9, 15),
                seam=T('stone_cool', 1), seed=seed)
        grain(cv, pts, 0.03, seed + 1, lit=wall_light(x0, y0, w, h))
    elif kind == 'rubble':
        courses(cv, x0, y0, w, h, stone_pick(('stone', 'stone', 'ashlar'), seed), course=6, lengths=(6, 11),
                seam=T('stone_cool', 1), seed=seed)
    elif kind in ('brick', 'brick_soot'):
        bricks(cv, x0, y0, w, h, seed, soot_rows=3 if kind == 'brick_soot' else 1, moss_rows=1)
    elif kind == 'stock':   # London stock: yellow-grey brick
        bricks(cv, x0, y0, w, h, seed, soot_rows=2)
        for p in pts:
            hit = tone_at(cv, *p)
            if hit and hp.family(hit[0]) == 'clay':
                cv.set(p[0], p[1], T(sib('sand', noise2(p[0] // 8, p[1] // 4, seed), 0.3), hit[1] - 1))
    elif kind in ('boards_sky', 'boards_berry', 'boards_timber', 'bleached', 'boards_lagoon'):
        fam = {'boards_sky': 'sky', 'boards_berry': 'berry', 'boards_timber': 'timber', 'bleached': 'bleached',
               'boards_lagoon': 'lagoon'}[kind]
        mix = 'timber' if fam == 'bleached' else fam
        boards(cv, x0, y0, w, h, lambda b, s: (sib(fam if noise2(b, s, 3) < 0.8 else mix, noise2(b, s, 4), 0.3),
                                              3 + (1 if b < 2 and fam == 'bleached' else 0)), board=4, seed=seed)
        if fam not in ('bleached', 'timber'):
            for (x, y) in pts:   # paint worn back to the wood in clusters, most at the foot
                if smooth_noise(x, y, 3, seed + 6) > 0.78 - 0.1 * (y - y0) / max(1, h) and (y - y0) % 4 in (1, 2):
                    cv.set(x, y, T('bleached', 3))
        grain(cv, pts, 0.04, seed + 1, shapes=H_GRAIN, lit=wall_light(x0, y0, w, h))
    elif kind == 'adobe':
        for (x, y) in pts:
            cv.set(x, y, T(sib('adobe', smooth_noise(x, y, 8, seed), 0.2), 3))
        soft_patches(cv, pts, seed + 1, scale=5, light=0.68, dark=0.24)
        grain(cv, pts, 0.035, seed + 2, lit=wall_light(x0, y0, w, h), up=0.25, down=0.2)
        for i in range(w * h // 700):   # cracks in the render, and patches where it fell to the mud brick
            cx, cy = x0 + int(noise2(i, 1, seed) * (w - 6)), y0 + int(noise2(i, 2, seed) * (h - 4))
            if noise2(i, 3, seed) < 0.5:
                for k in range(4):
                    cv.set(cx + k // 2, cy + k, T('adobe', 1))
            else:
                part(cv, cx, cy, 6, 3, 'adobe_cool', 2, glint=False)
    elif kind == 'corrugated':
        for (x, y) in pts:
            j = (x - x0) % 4
            k = 4 if j == 0 else 3 if j == 1 else 2
            run = 3 + int(noise2(x // 2, 0, seed) * 9)
            rust = smooth_noise(x, 0, 3, seed) > 0.7 and (y - y0) % 12 < run
            cv.set(x, y, T('clay_cool', min(3, k)) if rust else T('iron', k))
    elif kind == 'concrete':
        courses(cv, x0, y0, w, h, lambda ci, si: (sib('concrete', noise2(ci, si, seed)), 2 + (1 if noise2(ci, si, 5) > 0.7 else 0)),
                course=16, lengths=(16, 24), seam=T('asphalt', 1), seed=seed)
        grain(cv, pts, 0.06, seed + 3, lit=wall_light(x0, y0, w, h), up=0.15, down=0.4)
        for x in range(x0, x0 + w):   # rain streaks
            if noise2(x, 0, seed + 4) < 0.1:
                for y in range(y0 + 1, y0 + 6 + int(noise2(x, 1, seed) * 10)):
                    step(cv, x, y, -1)
    elif kind == 'tile':     # glazed tiles, the old city's shop walls
        for (x, y) in pts:
            j, r = (x - x0) % 5, (y - y0) % 5
            ti = ((x - x0) // 5, (y - y0) // 5)
            rp = sib('lagoon_cool' if noise2(*ti, seed) < 0.15 else 'concrete', noise2(*ti, seed + 1), 0.3)
            k = 1 if (j == 4 or r == 4) else 3 if (j == 0 or r == 0) else 2
            cv.set(x, y, T(rp, k))
    elif kind in ('hull', 'panel', 'hull_ext'):
        fam = 'hull' if kind == 'hull_ext' else kind
        plates(cv, x0, y0, w, h, fam, seed, pw=22, ph=12, other='panel' if fam == 'hull' else 'iron')
        for y in range(y0 + 3, y0 + h, 12):
            rivets(cv, x0 + 3, x0 + w - 2, y, every=4)
        for y in range(y0 + 6, y0 + h - 2, 12):   # a ribbed band at mid plate
            for x in range(x0 + 1, x0 + w - 1):
                if (x - x0) % 22 not in (0, 1):
                    step(cv, x, y, -1)
        if kind == 'hull_ext' and seed % 2:   # gold foil blankets quilted over part of the shell
            fx = x0 + 4 + int(noise2(seed, 0, 3) * (w - 24))
            for (x, y) in rect(fx, y0 + 2, 18, min(14, h - 4)):
                q = ((x - fx) // 4 + (y - y0) // 4) % 2
                cv.set(x, y, T(sib('brass', noise2((x - fx) // 4, (y - y0) // 4, seed), 0.35), 4 if q else 3))
            frame(cv, fx - 1, y0 + 1, 20, min(14, h - 4) + 2, 'brass', 2, t=1)
    elif kind == 'bulkhead':   # a station wall inside: plates above, equipment bays, a kick plate
        plates(cv, x0, y0, w, h, 'panel', seed, pw=12, ph=8, other='hull')
        for y in range(y0 + 2, y0 + h - 6, 8):
            rivets(cv, x0 + 2, x0 + w - 2, y, every=6, ramp='panel')
        bay_y = y0 + max(4, h // 3)
        for i, bx in enumerate(range(x0 + 2, x0 + w - 10, 12)):
            kind_ = ('grille', 'locker', 'screen', 'label', 'valves')[int(noise2(i, seed, 5) * 5)]
            part(cv, bx, bay_y, 10, 12, 'panel', 2)   # the bay, set back
            for yy in range(bay_y, bay_y + 12):
                step(cv, bx, yy, -1)
            if kind_ == 'grille':
                for yy in range(bay_y + 2, bay_y + 10, 2):
                    cv.hline(bx + 2, yy, 6, T('panel', 1))
            elif kind_ == 'locker':
                part(cv, bx + 1, bay_y + 1, 8, 10, sib('hull', noise2(i, 1, seed), 0.3), 3)
                cv.hline(bx + 6, bay_y + 6, 2, T('brass', 4))
            elif kind_ == 'screen':
                part(cv, bx + 1, bay_y + 2, 8, 6, 'void', 2, glint=False)
                for yy in (bay_y + 3, bay_y + 5):
                    cv.hline(bx + 2, yy, 3 + (yy % 3), T('neon_cyan', 4))
            elif kind_ == 'label':
                part(cv, bx + 1, bay_y + 2, 8, 4, 'plaster', 4, glint=False)
                cv.hline(bx + 2, bay_y + 3, 5, T('iron', 2))
                cv.hline(bx + 2, bay_y + 8, 6, T('berry', 3))
            else:
                for gx in (bx + 3, bx + 7):
                    for (px, py) in disc(gx, bay_y + 6, 1.8):
                        cv.set(px, py, T('berry' if gx < bx + 5 else 'brass', 4 if px + py < gx + bay_y + 6 else 2))
        for (x, y) in rect(x0, y0 + h - 5, w, 5):   # the kick plate, scuffed, a hazard band at its top
            cv.set(x, y, T('iron', 3 if y == y0 + h - 5 else 2))
            if y == y0 + h - 4:
                cv.set(x, y, T('brass', 4) if ((x + y) // 3) % 2 else T('iron', 1))
        grain(cv, rect(x0, y0 + h - 4, w, 4), 0.1, seed + 2, shapes=H_GRAIN[:2], swap=0.3, up=0.1, down=0.5)
    elif kind == 'berm':     # moon soil heaped over a habitat shell: no stone, no bricks
        for (x, y) in pts:   # a smooth heap: lit to the west, broad soft drifts, grit as clusters
            u = (x - x0) / max(1, w)
            k = 4 if u < 0.22 else 3 if u < 0.72 else 2
            n = smooth_noise(x, y, 7, seed)
            if n > 0.68 and k < 4:
                k += 1
            elif n < 0.22 and k > 2:
                k -= 1
            cv.set(x, y, T(sib('regolith', smooth_noise(x, y, 5, seed + 3), 0.3), k))
        grain(cv, pts, 0.16, seed + 1, swap=0.95, up=0.05, down=0.05)
        for i in range(w * h // 160):   # stones half buried in the heap, each with its hard shadow
            px, py = x0 + int(noise2(i, 1, seed) * (w - 4)), y0 + int(noise2(i, 2, seed) * (h - 3))
            pebble(cv, px, py, 'regolith', 3, big=noise2(i, 3, seed) < 0.3)
    else:
        raise ValueError(kind)
    return pts


def plinth(cv, x0, y0, w, h, kind='stone', seed=0):
    fams = {'stone': ('stone', 'ashlar'), 'slate': ('slate', 'stone'), 'adobe': ('adobe',), 'regolith': ('regolith',)}[kind]
    courses(cv, x0, y0, w, h, stone_pick(fams, seed), course=max(3, h // 2), lengths=(5, 9),
            seam=T(fams[0] + '_cool', 1), seed=seed)


# --- doors ---------------------------------------------------------------------------------
def leaf(cv, x, y, w, h, fam, kind, seed=0, lit=False):
    """A door leaf. kinds: plank, ledged, panel, stable, glazed, studded, batwing, roller,
    slide, hatch, iris."""
    if kind in ('plank', 'ledged', 'studded'):
        for (px, py) in rect(x, y, w, h):
            bi, j = divmod(px - x, 4)
            rp = sib(fam, noise2(bi, 0, seed), 0.34)
            k = 0 if j == 0 and px > x else 4 if j == 1 else 2 if j == 3 else 3
            cv.set(px, py, T(rp, k))
        grain(cv, rect(x, y, w, h), 0.05, seed + 1, shapes=V_GRAIN)
        if kind == 'ledged':
            for ly in (y + 3, y + h - 6):
                part(cv, x, ly, w, 3, fam, 3, glint=False)
            for i in range(h - 12):   # the brace, rising to the hinge side
                bx = x + w - 2 - int(i * (w - 3) / (h - 12))
                cv.set(bx, y + 6 + i, T(fam, 4)); cv.set(bx + 1, y + 6 + i, T(fam, 2))
        if kind == 'studded':
            for sy in (y + 4, y + h // 2, y + h - 5):
                for px in range(x, x + w):
                    cv.set(px, sy, T('iron', 3)); cv.set(px, sy + 1, T('iron', 1))
                    if (px - x) % 4 == 2:
                        cv.set(px, sy - 1, T('iron', 4))
    elif kind in ('panel', 'stable', 'glazed'):
        for (px, py) in rect(x, y, w, h):
            cv.set(px, py, T(fam, 3))
        rows = [(y + 2, y + h // 2 - 2), (y + h // 2 + 1, y + h - 3)]
        for ri, (a, b) in enumerate(rows):
            if kind == 'glazed' and ri == 0:
                glass(cv, x + 2, a, w - 4, b - a, lit)
                cv.vline(x + w // 2, a, b - a, T(fam, 2))
                continue
            for cx0, cx1 in ((x + 2, x + w // 2 - 1), (x + w // 2 + 1, x + w - 2)):
                for (px, py) in rect(cx0, a, cx1 - cx0, b - a):   # a raised panel: lit top and left, dark bottom and right
                    k = 4 if (py == a or px == cx0) else 2 if (py == b - 1 or px == cx1 - 1) else 3
                    cv.set(px, py, T(fam, k))
        if kind == 'stable':
            part(cv, x - 1, y + h // 2 - 1, w + 2, 2, fam, 4, glint=False)
    elif kind == 'batwing':
        for (px, py) in rect(x, y, w, h):
            cv.set(px, py, T('earth_cool', 0 if py < y + h - 4 else 1))
        for (lx, lw) in ((x, w // 2 - 1), (x + w // 2 + 1, w // 2 - 1)):
            boards(cv, lx, y + 8, lw, 12, lambda b, s: (fam, 3), board=4, seed=seed + lx, nails=False, grain=0, joints=(40, 41))
            cv.vline(lx + lw - 1 if lx == x else lx, y + 8, 12, T(fam, 1))
    elif kind == 'roller':
        for (px, py) in rect(x, y, w, h):
            r = (py - y) % 3
            cv.set(px, py, T(sib('panel', noise2(0, (py - y) // 3, seed), 0.3), 4 if r == 0 else 3 if r == 1 else 1))
        part(cv, x + w // 2 - 3, y + h - 4, 6, 2, 'iron', 3)
        grain(cv, rect(x, y + h - 10, w, 10), 0.08, seed + 2, shapes=H_GRAIN[:2], swap=0.2, up=0.0, down=0.7)
    elif kind == 'slide':
        for (px, py) in rect(x, y, w, h):
            cv.set(px, py, T('iron', 2))
        half = w // 2
        glass(cv, x + 1, y + 1, half - 2, h - 2, lit); glass(cv, x + half + 1, y + 1, half - 2, h - 2, lit)
        cv.hline(x + 2, y + h // 2, w - 4, T('iron', 3))
    elif kind == 'hatch':   # a square pressure hatch: chamfered, a handwheel, a hazard sill
        for (px, py) in rect(x, y, w, h):
            dx, dy = min(px - x, x + w - 1 - px), min(py - y, y + h - 1 - py)
            if dx + dy < 3:
                continue
            k = 4 if (px - x) + (py - y) < 6 else 2 if dx < 2 or dy < 2 else 3
            cv.set(px, py, T('panel', k))
        cx, cy = x + w // 2, y + h // 2
        for (px, py) in disc(cx, cy, 3.2):
            cv.set(px, py, T('brass', 4 if px + py < cx + cy else 2))
        for (px, py) in disc(cx, cy, 1.4):
            cv.set(px, py, T('brass', 1))
        for px in range(x + 2, x + w - 2):
            cv.set(px, y + h - 2, T('brass', 4) if ((px + y) // 2) % 2 else T('iron', 1))
    elif kind == 'iris':    # a round hatch in a thick ring
        cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
        for (px, py) in disc(cx, cy, r):
            lv = -(px + 0.5 - cx) - (py + 0.5 - cy)
            cv.set(px, py, T('panel', 4 if lv > r * 0.5 else 3 if lv > -r * 0.5 else 2))
        for (px, py) in disc(cx, cy, r - 2.5):
            cv.set(px, py, T('panel', 1))
        for (px, py) in disc(cx, cy, r - 3.5):
            a = math.atan2(py + 0.5 - cy, px + 0.5 - cx)
            k = int((a + math.pi) / (math.pi / 3)) % 2
            cv.set(px, py, T('hull', 4 if k else 3))
        for (px, py) in disc(cx, cy, 1.5):
            cv.set(px, py, T('hull', 2))
    else:
        raise ValueError(kind)


def doorway(cv, x, yb, w, h, fam, kind, frame_fam, seed=0, arch=False, fan=False, step_fam='stone',
            knob='brass', lit=False, frame_t=2):
    """A door in its surround: a frame (or arch) round it, the leaf set back in a recess
    (its top row and hinge-side column in shade), a knob or latch, a step."""
    y = yb - h
    opening = rect(x, y, w, h)
    if arch:
        r = w / 2
        opening = {(px, py) for (px, py) in opening if py >= y + r or (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= r * r}
        ring = {(px, py) for px in range(x - frame_t, x + w + frame_t) for py in range(y - frame_t, yb)
                if (py >= y + r or (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= (r + frame_t) ** 2)} - opening
        for (px, py) in ring:
            a = math.atan2(-(py + 0.5 - (y + r)), px + 0.5 - (x + w / 2))
            lit_side = px < x + w / 2
            k = 4 if (py < y + r and a > 1.0) or (lit_side and py >= y + r) else 2 if not lit_side else 3
            if py < y + r and int(a / (math.pi / 7)) % 2 == 0 and abs(math.hypot(px + 0.5 - (x + w / 2), py + 0.5 - (y + r)) - r - frame_t / 2) < 0.6:
                k -= 1
            cv.set(px, py, T(frame_fam, k))
    else:
        frame(cv, x - frame_t, y - frame_t, w + 2 * frame_t, h + frame_t, frame_fam, 3, t=frame_t)
    if fan and not arch:
        glass(cv, x, y, w, 4, lit)
        cv.hline(x, y + 4, w, T(frame_fam, 3))
        y, h = y + 5, h - 5
    sub = Canvas(cv.w, cv.h)
    leaf(sub, x, y, w, h, fam, kind, seed, lit)
    for (px, py) in opening:
        if py >= y:
            c = sub.get(px, py)
            if c[3]:
                cv.set(px, py, c)
    for (px, py) in opening:   # the recess: shade under the head and on the hinge side
        if (px, py - 1) not in opening or (px - 1, py) not in opening:
            step(cv, px, py, -1)
    if knob and kind not in ('batwing', 'roller', 'slide', 'hatch', 'iris'):
        kx = x + w - 4
        cv.set(kx, y + h // 2, T(knob, 5)); cv.set(kx, y + h // 2 + 1, T(knob, 2))
    if step_fam:
        part(cv, x - frame_t - 1, yb, w + 2 * frame_t + 2, 3, step_fam, 4)
    return opening


# --- windows -------------------------------------------------------------------------------
def casement(cv, x, y, w, h, frame_fam='timber', cols=2, rows=2, lit=False, shutters=None, sill='stone',
             box=False, arch=False, lintel=None, bars=False, curtain=True, blind=False, leaded=False, t=2):
    """A window in its wall: frame, panes (lit from inside or the sky in them), glazing
    bars, optional shutters, lintel, arch, sill and flower box. The sill throws a band."""
    if lintel:
        part(cv, x - 2, y - 3, w + 4, 3, lintel, 4)
    if shutters:
        for sx in (x - 5, x + w):
            boards(cv, sx, y, 5, h, lambda b, s: (shutters, 3), board=4, seed=sx, nails=False, grain=0, joints=(40, 41))
            for yy in range(y, y + h):
                cv.set(sx, yy, T(shutters, 4)); cv.set(sx + 4, yy, T(shutters, 1))
    hole = rect(x, y, w, h)
    if arch:
        r = w / 2
        hole = {(px, py) for (px, py) in hole if py >= y + r or (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= r * r}
        for (px, py) in rect(x - 1, y - 1, w + 2, int(r) + 1):
            if (px, py) not in hole and (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= (r + 1.5) ** 2:
                cv.set(px, py, T(frame_fam, 4 if px < x + w / 2 else 2))
    for (px, py) in hole:
        cv.set(px, py, T(frame_fam, 3))
    inner = {(px, py) for (px, py) in hole if x + t <= px < x + w - t and y + t <= py < y + h - t and
             all((px + dx, py + dy) in hole for dx in (-t, t) for dy in (-t, t))}
    if not inner:
        return
    ix0, iy0 = min(p[0] for p in inner), min(p[1] for p in inner)
    ix1, iy1 = max(p[0] for p in inner) + 1, max(p[1] for p in inner) + 1
    sub = Canvas(cv.w, cv.h)
    glass(sub, ix0, iy0, ix1 - ix0, iy1 - iy0, lit)
    for p in inner:
        cv.set(p[0], p[1], sub.get(*p))
    for (px, py) in hole - inner:   # the frame: lit top and left, dark bottom and right
        k = 4 if (py < iy0 or px < ix0) and not (py >= iy1 or px >= ix1) else 2 if (py >= iy1 or px >= ix1) else 3
        cv.set(px, py, T(frame_fam, k))
    for c in range(1, cols):
        bx = ix0 + c * (ix1 - ix0) // cols
        for py in range(iy0, iy1):
            if (bx, py) in inner:
                cv.set(bx, py, T(frame_fam, 2))
    for r in range(1, rows):
        by = iy0 + r * (iy1 - iy0) // rows
        for px in range(ix0, ix1):
            if (px, by) in inner:
                cv.set(px, by, T(frame_fam, 4))
    if leaded:
        for (px, py) in inner:
            if (px - ix0 + py - iy0) % 3 == 0 and (px - ix0 - (py - iy0)) % 3 == 0:
                cv.set(px, py, T('iron', 1))
    if curtain and lit:
        for py in range(iy0, iy1):
            if (ix0, py) in inner:
                cv.set(ix0, py, T('berry', 3)); cv.set(ix0 + 1, py, T('berry', 2))
    elif curtain:
        for py in range(iy0, iy0 + (iy1 - iy0) // 2):
            cv.set(ix0, py, T('plaster', 5)); cv.set(ix0 + 1, py, T('plaster', 4))
    if blind:
        for py in range(iy0, iy0 + (iy1 - iy0) // 2):
            for px in range(ix0, ix1):
                if (px, py) in inner:
                    cv.set(px, py, T('plaster', 4 if (py - iy0) % 2 == 0 else 3))
    if bars:
        for px in range(ix0 + 1, ix1, 3):
            for py in range(iy0, iy1):
                if (px, py) in inner:
                    cv.set(px, py, T('iron', 2 if py > iy0 else 3))
    if sill:
        part(cv, x - 2, y + h, w + 4, 2, sill, 4, glint=False)
        overhang(cv, x - 1, x + w + 2, y + h + 2, 2)
    if box:
        part(cv, x - 1, y + h + 2, w + 2, 4, 'timber', 2)
        for i, fx in enumerate(range(x, x + w, 3)):
            cv.hline(fx, y + h + 1, 3, T('leaf', 3)); cv.set(fx + 1, y + h, T('leaf', 4))
            col = ('berry', 'brass', 'plaster', 'dusk')[(i + x) % 4]
            cv.hline(fx, y + h - 1 + (i % 2), 2, T(col, 4)); cv.set(fx, y + h - 1 + (i % 2), T(col, 5))
        overhang(cv, x - 1, x + w + 2, y + h + 6, 2)


def porthole(cv, cx, cy, r, ring='brass', lit=True):
    for (px, py) in disc(cx, cy, r):
        lv = -(px + 0.5 - cx) - (py + 0.5 - cy)
        cv.set(px, py, T(ring, 4 if lv > r * 0.4 else 3 if lv > -r * 0.4 else 2))
    sub = Canvas(cv.w, cv.h)
    glass(sub, int(cx - r), int(cy - r), int(2 * r) + 1, int(2 * r) + 1, lit)
    for (px, py) in disc(cx, cy, r - 1.6):
        cv.set(px, py, sub.get(px, py))
    for k in range(4):   # bolts round the ring
        a = k * math.pi / 2 + math.pi / 4
        cv.set(int(cx + (r - 0.8) * math.cos(a)), int(cy + (r - 0.8) * math.sin(a)), T(ring, 1))


# --- roofs and tops ------------------------------------------------------------------------
def roof_edge(cv, x0, y0, w, h, kind, seed=0):
    """The roof or top as it meets the wall below, h px tall, with the band it throws on the
    wall under it. kinds: tiles, slate, thatch, palm, shingle, copper, glass, corrugated,
    parapet, falsefront, vigas, crenel, cone, flat, radiator, berm, dome."""
    yb = y0 + h
    if kind in ('tiles', 'slate', 'shingle'):
        fam, row, tile = {'tiles': ('clay', 5, (6, 8)), 'slate': ('slate', 4, (5, 7)), 'shingle': ('timber', 4, (4, 6))}[kind]
        roof_rows(cv, x0, y0, w, h - 3, fam, 3, row=row, tile=tile, seed=seed, moss=kind != 'shingle')
        for x in range(x0, x0 + w):
            cv.set(x, yb - 3, T('timber', 4)); cv.set(x, yb - 2, T('timber', 2)); cv.set(x, yb - 1, T('timber', 1))
    elif kind in ('thatch', 'palm'):
        fam = 'sand' if kind == 'thatch' else 'bleached'
        for (x, y) in rect(x0, y0, w, h):
            ci = (y - y0) // 4
            sx = (x + (2 if ci % 2 else 0)) // 2
            n = noise2(sx, ci, seed)
            k = 3 + (1 if n > 0.7 else -1 if n < 0.25 else 0)
            if (y - y0) % 4 == 0:
                k -= 1
            if kind == 'palm' and (y - y0) % 6 == 4 and (x // 2) % 3:
                cv.set(x, y, T('bleached', 1))   # the binding of each bundle
                continue
            cv.set(x, y, T(sib(fam, noise2(sx, ci, seed + 1), 0.3), k))
        for x in range(x0, x0 + w):   # the thick rounded eave: lit lip, shade under
            d = 1 + (1 if (x // 3) % 2 else 0)
            for i in range(d):
                cv.set(x, yb - 3 + i, T(fam, 4))
            cv.set(x, yb - 1, T(fam, 1))
    elif kind == 'copper':
        for (x, y) in rect(x0, y0, w, h - 2):
            j = (x - x0) % 6
            k = 4 if j == 0 else 3 if j < 3 else 2 if j < 5 else 1
            cv.set(x, y, T(sib('copper', smooth_noise(x, y, 5, seed)), k + (1 if y < y0 + 2 else 0)))
        for x in range(x0, x0 + w):
            cv.set(x, yb - 2, T('copper', 1)); cv.set(x, yb - 1, T('iron', 2))
    elif kind == 'glass':   # a glazed roof on iron bars
        for (x, y) in rect(x0, y0, w, h - 2):
            j = (x - x0) % 7
            if j == 0:
                cv.set(x, y, T('iron', 3 if y > y0 else 4))
            else:
                k = 4 if (j == 1 and (y - y0) < 4) else 2 if (y - y0) > h // 2 else 3
                cv.set(x, y, T('sky_cool', k))
        for x in range(x0, x0 + w):
            cv.set(x, yb - 2, T('iron', 4)); cv.set(x, yb - 1, T('iron', 1))
    elif kind == 'corrugated':
        wall(cv, x0, y0, w, h - 1, 'corrugated', seed)
        for x in range(x0, x0 + w):
            cv.set(x, y0, T('iron', 5) if (x - x0) % 4 == 0 else T('iron', 4))
            cv.set(x, yb - 1, T('iron', 1))
    elif kind in ('parapet', 'falsefront', 'flat'):
        fam = {'parapet': 'ashlar', 'falsefront': 'bleached', 'flat': 'concrete'}[kind]
        part(cv, x0, yb - 4, w, 4, fam, 4)
        if kind == 'falsefront':   # the stepped top of a false front
            part(cv, x0 + w // 5, y0 + 2, w - 2 * (w // 5), yb - 4 - y0 - 2, fam, 3)
            part(cv, x0 + w // 3, y0, w - 2 * (w // 3), 3, fam, 4)
        if kind == 'flat':
            for x in range(x0 + 4, x0 + w - 4, 9):   # a rooftop rail
                cv.vline(x, y0 + 2, yb - 4 - y0 - 2, T('iron', 3))
            cv.hline(x0 + 3, y0 + 2, w - 6, T('iron', 4))
    elif kind == 'vigas':   # an adobe parapet with round roof beams poking through
        part(cv, x0, y0 + 2, w, h - 2, 'adobe', 4)
        for x in range(x0 + 4, x0 + w - 4, 10):
            for (px, py) in disc(x, yb - 3, 2.2):
                cv.set(px, py, T('timber', 4 if px + py < x + yb - 3 else 2))
            cv.set(x, yb - 3, T('timber', 1))
            step(cv, x + 1, yb, -2); step(cv, x + 2, yb, -1)
    elif kind == 'crenel':
        for x in range(x0, x0 + w):
            merlon = ((x - x0) // 6) % 2 == 0
            top = y0 if merlon else y0 + 5
            if not merlon:   # the wall walk seen through the gap, in the merlon's shadow
                for y in range(y0, top):
                    step(cv, x, y, -2 if (x - x0) % 6 < 2 else -1)
            for y in range(top, yb):
                k = 4 if y == top else 3
                if (x - x0) % 6 == 5 and merlon:
                    k = 2
                cv.set(x, y, T(sib('ashlar', noise2((x - x0) // 6, 0, seed), 0.3), k))
        for x in range(x0, x0 + w):
            cv.set(x, yb - 1, T('ashlar', 2))
    elif kind == 'cone':   # the foot of a slate cone roof, curving round a tower
        for (x, y) in rect(x0, y0, w, h - 2):
            u = (x - x0) / w
            roof_rows(cv, x, y, 1, 1, 'slate', 3 if 0.2 < u < 0.6 else 2 if u >= 0.6 else 4, row=4, tile=(5, 6), seed=seed)
        for x in range(x0, x0 + w):
            cv.set(x, yb - 2, T('slate', 1)); cv.set(x, yb - 1, T('timber', 1))
    elif kind == 'radiator':
        for x in range(x0, x0 + w):
            f = (x - x0) % 3
            for y in range(y0, yb):
                cv.set(x, y, T('panel', 4 if f == 0 else 3 if f == 1 else 1))
        cv.hline(x0, y0, w, T('panel', 5)); cv.hline(x0, yb - 1, w, T('panel', 1))
    elif kind == 'berm':
        wall(cv, x0, y0, w, h, 'berm', seed)
        for x in range(x0, x0 + w):
            cv.set(x, y0, T('regolith', 4))
    elif kind == 'dome':
        cx = x0 + w / 2
        for (x, y) in rect(x0, y0, w, h):
            u = (x + 0.5 - cx) / (w / 2)
            top = yb - h * math.sqrt(max(0, 1 - u * u))
            if y >= top:
                j = (x - x0) % 8
                k = 4 if u < -0.3 else 3 if u < 0.4 else 2
                cv.set(x, y, T('panel', 3) if j == 0 else T('sky_cool', k))
    else:
        raise ValueError(kind)
    overhang(cv, x0, x0 + w, yb, 2)


def chimney(cv, x, y, h=12, fam='brick'):
    """A chimney stack on a roof: lit west face, dark east face, a cap, its shadow on the roof."""
    if fam == 'brick':
        bricks(cv, x, y + 2, 7, h - 2, x + y, soot_rows=1)
    else:
        courses(cv, x, y + 2, 7, h - 2, stone_pick((fam,), x), course=3, lengths=(4, 6), seam=T(fam + '_cool', 1), seed=x)
    for yy in range(y + 2, y + h):
        step(cv, x + 6, yy, -1)
    part(cv, x - 1, y, 9, 3, 'stone', 4)
    for (px, py) in ((x + 2, y - 1), (x + 4, y - 1)):   # pots
        cv.set(px, py, T('clay', 4)); cv.set(px + 1, py, T('clay', 2))
    for yy in range(y + 3, y + h):   # its shadow on the roof, to the east
        step(cv, x + 7, yy, -2); step(cv, x + 8, yy, -1)


def roof_mass(cv, x0, y0, w, h, kind, shape, seed=0, gable_wall='plaster'):
    """The roof seen from the south and above, h px tall, standing on a wall that starts at
    y0 + h. Shapes: 'ridge' (the ridge runs across: the front plane narrows to a ridge cap,
    the gable ends cut its corners), 'gable' (the gable faces us: a lit west plane, a shaded
    east plane, barge boards, the gable wall between), 'hip' (a short ridge, hips lit west
    and shaded east), 'flat' (a flat roof seen from above with its parapet and rooftop
    things), 'falsefront' (a tall front with a stepped top and the tin roof behind it),
    'crenel' (battlements with the wall walk behind), 'dome', 'berm', 'radiator'."""
    fam = {'tiles': 'clay', 'slate': 'slate', 'shingle': 'timber', 'copper': 'copper', 'thatch': 'sand',
           'palm': 'bleached', 'glass': 'sky_cool', 'corrugated': 'iron'}.get(kind, 'slate')
    yb = y0 + h
    if shape in ('ridge', 'hip', 'gable'):
        if shape == 'gable':
            cx = x0 + w / 2
            plane = {(x, y) for x in range(x0, x0 + w) for y in range(y0, yb)
                     if abs(x + 0.5 - cx) < w / 2 * (0.42 + 0.58 * (y - y0) / h)}
            gab = {(x, y) for (x, y) in plane if abs(x + 0.5 - cx) < (y - y0) * (w * 0.32) / h}
            sub = Canvas(cv.w, cv.h)
            _roof_fill(sub, x0, y0, w, h, kind, fam, seed)
            for (x, y) in plane - gab:
                c = sub.get(x, y)
                if c[3]:
                    cv.set(x, y, c)
                    if x > cx:
                        step(cv, x, y, -1)
                    elif x < cx - w * 0.3:
                        step(cv, x, y, 1)
            wall(sub, x0, y0, w, h, gable_wall, seed + 3)
            for p in gab:
                cv.set(p[0], p[1], sub.get(*p))
            for (x, y) in gab:   # barge boards along the gable's two edges
                if (x - 1, y) not in gab and x < cx:
                    cv.set(x, y, T('timber', 4)); cv.set(x - 1, y, T('timber', 2))
                if (x + 1, y) not in gab and x >= cx:
                    cv.set(x, y, T('timber', 2)); cv.set(x + 1, y, T('timber', 1))
            for (x, y) in gab:   # the gable wall is in the roof's shadow at its top
                if y < y0 + 4:
                    step(cv, x, y, -1)
            vx = int(cx) - 2   # a vent in the gable
            if (vx, y0 + h // 2) in gab:
                part(cv, vx - 1, y0 + h // 2 - 2, 6, 5, 'timber', 2, glint=False)
        else:
            inset = 0.22 if shape == 'ridge' else 0.42
            sub = Canvas(cv.w, cv.h)
            _roof_fill(sub, x0, y0, w, h, kind, fam, seed)
            for (x, y) in rect(x0, y0, w, h):
                d = (yb - y) * inset * (w / max(1, h)) * 0.5
                if x0 + d - 1 <= x < x0 + w - d + 1:
                    c = sub.get(x, y)
                    if c[3]:
                        cv.set(x, y, c)
                        if shape == 'hip' and x < x0 + d + 6:
                            step(cv, x, y, 1)
                        elif x > x0 + w - d - 7:
                            step(cv, x, y, -1)
            top_d = int(h * inset * (w / max(1, h)) * 0.5)
            part(cv, x0 + top_d, y0, w - 2 * top_d, 3, fam if kind not in ('thatch', 'palm') else fam, 4)
        if kind not in ('thatch', 'palm', 'glass', 'corrugated'):
            for x in range(x0, x0 + w):   # fascia under the eave
                if cv.get(x, yb - 1)[3]:
                    cv.set(x, yb, T('timber', 4)); cv.set(x, yb + 1, T('timber', 2))
            overhang(cv, x0, x0 + w, yb + 2, 3)
        else:
            overhang(cv, x0, x0 + w, yb, 3)
    elif shape == 'flat':
        top = {'flat': 'ash', 'parapet': 'ashlar'}.get(kind, 'ash')
        ground(cv, x0 + 1, y0, w - 2, h - 4, top, 2, seed=seed, scale=4, density=0.12)
        part(cv, x0, yb - 4, w, 4, 'concrete' if top == 'ash' else 'ashlar', 4)
        part(cv, x0, y0 - 2, w, 3, 'concrete' if top == 'ash' else 'ashlar', 4, glint=False)
        for yy in range(y0, yb - 4):
            cv.set(x0, yy, T('concrete', 4)); cv.set(x0 + w - 1, yy, T('concrete', 2))
        # rooftop things, a different set on each roof, each with its shadow
        things = ['ac', 'tank', 'vent', 'dish', 'skylight', 'pots']
        order = sorted(things, key=lambda t: noise2(seed, things.index(t), 9))[:3]
        for i, t in enumerate(order):
            ax = x0 + 4 + i * (w - 8) // 3 + int(noise2(seed, i, 4) * 4)
            if t == 'ac':
                part(cv, ax, y0 + 2, 12, 7, 'panel', 3)
                for xx in range(ax + 2, ax + 10, 2):
                    cv.vline(xx, y0 + 4, 3, T('panel', 1))
                cast(cv, rect(ax + 12, y0 + 3, 2, 7))
            elif t == 'tank':
                cylinder(cv, ax, y0 + 1, 8, 9, 'timber', 3)
                cv.hline(ax, y0, 8, T('iron', 4))
                cast(cv, rect(ax + 8, y0 + 2, 2, 9))
            elif t == 'vent':
                cylinder(cv, ax + 2, y0 + 3, 3, 6, 'iron', 3)
                part(cv, ax, y0 + 1, 7, 3, 'iron', 4, glint=False)
                cast(cv, rect(ax + 5, y0 + 4, 2, 5))
            elif t == 'dish':
                for (px, py) in disc(ax + 5, y0 + 5, 4):
                    cv.set(px, py, T('hull', 4 if px + py < ax + y0 + 10 else 2))
                cast(cv, rect(ax + 9, y0 + 4, 2, 5))
            elif t == 'skylight':
                glass(cv, ax, y0 + 2, 10, 7, True)
                frame(cv, ax - 1, y0 + 1, 12, 9, 'iron', 3, t=1)
            else:
                for j in range(2):
                    part(cv, ax + j * 6, y0 + 5, 5, 4, 'clay', 3)
                    leafy(cv, ax + j * 6 + 2.5, y0 + 3, 3, 2.5, seed=seed + j)
        overhang(cv, x0, x0 + w, yb, 2)
    elif shape == 'falsefront':
        roof_mass(cv, x0 + 8, y0 + 4, w - 16, 10, 'corrugated', 'ridge', seed)
        wall(cv, x0, y0 + 10, w, h - 10, 'bleached', seed + 5)
        for (x, y) in rect(x0, y0 + 10, w, 4):   # the stepped top
            if x < x0 + 6 or x >= x0 + w - 6:
                cv.set(x, y, (0, 0, 0, 0))
        part(cv, x0 + 5, y0 + 9, w - 10, 2, 'bleached', 5, glint=False)
        part(cv, x0, y0 + 13, 6, 2, 'bleached', 5, glint=False); part(cv, x0 + w - 6, y0 + 13, 6, 2, 'bleached', 5, glint=False)
    elif shape == 'vigas':
        ground(cv, x0 + 2, y0 + 2, w - 4, h - 6, 'adobe', 3, seed=seed, scale=4, density=0.08)
        roof_edge(cv, x0, yb - 8, w, 8, 'vigas', seed)
        part(cv, x0, y0, w, 3, 'adobe', 4, glint=False)
        for yy in range(y0, yb - 8):
            cv.set(x0, yy, T('adobe', 4)); cv.set(x0 + w - 1, yy, T('adobe', 2))
    elif shape == 'crenel':
        courses(cv, x0, y0, w, h - 9, stone_pick(('stone',), seed), course=5, lengths=(8, 12), seam=T('stone_cool', 1), seed=seed)
        roof_edge(cv, x0, yb - 11, w, 11, 'crenel', seed)
    elif shape == 'conduit':   # the thick top of a bulkhead inside the station, services along it
        for (x, y) in rect(x0, y0, w, h):
            cv.set(x, y, T(sib('panel', noise2((x - x0) // 16, 0, seed), 0.3), 2 if (y - y0) % 6 else 1))
        part(cv, x0, y0, w, 2, 'panel', 4, glint=False)
        runs = [('pipe', y0 + 3), ('tray', y0 + 9), ('duct', y0 + 3), ('light', y0 + 14)]
        pick = [runs[int(noise2(seed, i, 7) * 4)] for i in range(2)] + [('light', yb - 4)]
        for kind_, y in pick:
            if kind_ == 'pipe':
                for x in range(x0, x0 + w):
                    for i, k in enumerate((4, 3, 2)):
                        cv.set(x, y + i, T('copper', k))
                    if (x - x0) % 14 in (0, 1):
                        cv.vline(x, y - 1, 5, T('brass', 4 if (x - x0) % 14 == 0 else 2))
            elif kind_ == 'tray':
                for x in range(x0, x0 + w):
                    cv.set(x, y, T('iron', 3)); cv.set(x, y + 4, T('iron', 1))
                    for i, c in enumerate(('berry', 'sky', 'brass')):
                        cv.set(x, y + 1 + i, T(c, 3 if (x + i) % 9 else 4))
            elif kind_ == 'duct':
                part(cv, x0, y, w, 5, 'hull', 3)
                for x in range(x0 + 6, x0 + w, 16):
                    cv.vline(x, y, 5, T('hull', 1))
            else:
                for x in range(x0 + 2, x0 + w - 2):
                    cv.set(x, y, T('lamp', 5 if (x - x0) % 12 < 9 else 2)); cv.set(x, y + 1, T('lamp', 3 if (x - x0) % 12 < 9 else 1))
        overhang(cv, x0, x0 + w, yb, 2)
    elif shape in ('dome', 'berm', 'radiator'):
        cx = x0 + w / 2
        for (x, y) in rect(x0, y0, w, h):
            u = (x + 0.5 - cx) / (w / 2)
            top = yb - h * math.sqrt(max(0, 1 - u * u)) * (0.95 if shape != 'radiator' else 0.5)
            if y < top:
                continue
            if shape == 'berm':
                continue
            else:
                pi_ = int((u + 1) * 4)
                k = 4 if u < -0.3 else 3 if u < 0.35 else 2
                if (y - y0) % 8 == 0 or int((u + 1) * 4 * 2) % 2 == 0 and (x + 0.5 - cx) % 8 < 1:
                    k -= 1
                cv.set(x, y, T(sib('hull', noise2(pi_, (y - y0) // 8, seed), 0.3), k))
        if shape == 'berm':   # the heap of moon soil over the shell, lit at the upper left
            sub = Canvas(cv.w, cv.h)
            wall(sub, x0, y0, w, h, 'berm', seed)
            for (x, y) in rect(x0, y0, w, h):
                u = (x + 0.5 - cx) / (w / 2)
                if y >= yb - h * math.sqrt(max(0, 1 - u * u)) * 0.95:
                    cv.set(x, y, sub.get(x, y))
                    if u < -0.35 and y < yb - h * 0.4:
                        step(cv, x, y, 1)
                    elif u > 0.45:
                        step(cv, x, y, -1)
        if shape == 'radiator':
            for x in range(x0 + w // 4, x0 + 3 * w // 4):
                f = (x - x0) % 3
                for y in range(y0, y0 + h // 2):
                    cv.set(x, y, T('panel', 4 if f == 0 else 3 if f == 1 else 1))
            cv.hline(x0 + w // 4, y0, w // 2, T('panel', 5))
        if shape != 'berm':   # the heap runs on down the wall: no eave
            overhang(cv, x0, x0 + w, yb, 2)
    else:
        raise ValueError(shape)


def _roof_fill(cv, x0, y0, w, h, kind, fam, seed):
    if kind in ('tiles', 'slate', 'shingle'):
        row, tile = {'tiles': (5, (6, 8)), 'slate': (4, (5, 7)), 'shingle': (4, (4, 6))}[kind]
        roof_rows(cv, x0, y0, w, h, fam, 3, row=row, tile=tile, seed=seed, moss=kind != 'shingle')
    elif kind == 'copper':
        for (x, y) in rect(x0, y0, w, h):
            j = (x - x0) % 6
            cv.set(x, y, T(sib('copper', smooth_noise(x, y, 5, seed)), 4 if j == 0 else 3 if j < 3 else 2 if j < 5 else 1))
    elif kind in ('thatch', 'palm'):
        for (x, y) in rect(x0, y0, w, h):
            ci = (y - y0) // 3
            sx = (x + (1 if ci % 2 else 0)) // 2
            n = noise2(sx, ci, seed)
            k = 3 + (1 if n > 0.72 else -1 if n < 0.22 else 0) - (1 if (y - y0) % 3 == 0 else 0)
            cv.set(x, y, T(sib(fam, noise2(sx, ci, seed + 1), 0.3), k))
        for x in range(x0, x0 + w):   # the thick rounded eave
            cv.set(x, y0 + h - 3, T(fam, 4)); cv.set(x, y0 + h - 2, T(fam, 3)); cv.set(x, y0 + h - 1, T(fam, 1))
        if kind == 'palm':   # tied bundles: a darker binding line every few rows
            for y in range(y0 + 4, y0 + h - 3, 6):
                for x in range(x0, x0 + w):
                    if (x // 2) % 3:
                        cv.set(x, y, T('bleached', 1))
    elif kind == 'glass':
        for (x, y) in rect(x0, y0, w, h):
            j = (x - x0) % 7
            cv.set(x, y, T('iron', 3) if j == 0 else T('sky_cool', 4 if (j == 1 and (y - y0) % 10 < 3) else 3 if (y - y0) < h // 2 else 2))
        for y in range(y0, y0 + h, 9):
            cv.hline(x0, y, w, T('iron', 4))
    elif kind == 'corrugated':
        wall(cv, x0, y0, w, h, 'corrugated', seed)
    else:
        roof_rows(cv, x0, y0, w, h, 'slate', 3, seed=seed)


# --- signs ---------------------------------------------------------------------------------
def hanging_sign(cv, x, y, pic, board='timber', ink='brass'):
    """An iron bracket from the wall and a board on two rings with a pictogram."""
    cv.hline(x, y, 14, T('iron', 4)); cv.hline(x, y + 1, 14, T('iron', 1))
    cv.set(x + 1, y + 2, T('iron', 2)); cv.set(x + 2, y + 3, T('iron', 2))   # the brace
    for rx in (x + 4, x + 11):
        cv.set(rx, y + 2, T('iron', 3))
    part(cv, x + 2, y + 3, 12, 11, board, 3)
    picto(cv, x + 4, y + 5, pic, ink)


def fascia(cv, x, y, w, pic, board='berry', ink='brass', h=8):
    """A fascia board over a shop: lit top moulding, painted board, a pictogram with dots
    either side, a shadow under it."""
    part(cv, x, y, w, 2, board, 4, glint=False)
    for (px, py) in rect(x, y + 2, w, h - 3):
        cv.set(px, py, T(sib(board, noise2(px // 9, 0, 3), 0.3), 2 if py == y + h - 2 else 3))
    picto(cv, x + w // 2 - 3, y + 1, pic, ink)
    for dx in (-10, 10):
        cv.hline(x + w // 2 + dx - 1, y + 4, 2, T(ink, 4))
    cv.hline(x, y + h - 1, w, T(board, 1))
    overhang(cv, x, x + w, y + h, 2)


def awning(cv, x, y, w, a='berry', b='plaster', drop=8):
    """A canvas awning: stripes, folds lit and shaded, a scalloped valance, its shade below."""
    for (px, py) in rect(x, y, w, drop):
        stripe = a if ((px - x) // 5) % 2 == 0 else b
        f = (px - x) % 5
        k = 4 if f == 0 else 3 if f < 3 else 2
        if py < y + 2:
            k += 1
        cv.set(px, py, T(stripe, k))
    for px in range(x, x + w):
        d = 2 if (px - x) % 5 in (1, 2, 3) else 1
        stripe = a if ((px - x) // 5) % 2 == 0 else b
        for i in range(d):
            cv.set(px, y + drop + i, T(stripe, 2 if i < d - 1 else 1))
    overhang(cv, x, x + w, y + drop + 2, 3)


def neon_tube(cv, x, y, pic, glow='neon_pink', wall_fams=('asphalt', 'concrete')):
    """A neon pictogram: the tube in the glow ramp, its halo in two bands on the wall."""
    tube = {(x + c, y + r) for r, row in enumerate(PICTO[pic]) for c, ch in enumerate(row) if ch in '#+'}
    for (px, py) in tube:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                p = (px + dx, py + dy)
                if p in tube:
                    continue
                hit = tone_at(cv, *p)
                if hit and hp.family(hit[0]) in wall_fams:
                    cv.set(p[0], p[1], T(glow, 0 if abs(dx) + abs(dy) > 2 else 1))
    for (px, py) in tube:
        cv.set(px, py, T(glow, 4))
    for (px, py) in sorted(tube)[::4]:
        cv.set(px, py, T(glow, 5))


def blade(cv, x, y, h, glow='neon_cyan', pics=('moon', 'cup')):
    """A vertical lightbox sign: a dark box, lit panels with abstract marks."""
    for (px, py) in rect(x, y, 9, h):
        edge = px in (x, x + 8) or py in (y, y + h - 1)
        cv.set(px, py, T('iron', 2 if edge else 1))
    for i, pic in enumerate(pics):
        picto(cv, x + 1, y + 2 + i * 9, pic, glow)


def stencil(cv, x, y, w, fam='berry', pic='bolt'):
    """A painted band on a hull with a pictogram, worn at its edges."""
    for (px, py) in rect(x, y, w, 7):
        cv.set(px, py, T(fam, 4 if py == y else 2 if py == y + 6 else 3))
    picto(cv, x + w // 2 - 3, y, pic, 'plaster', 5)
    grain(cv, rect(x, y, w, 7), 0.1, 7, shapes=H_GRAIN[:2], swap=0.2, up=0.0, down=0.6)


def status_light(cv, x, y, glow='glowflora'):
    part(cv, x - 1, y - 1, 5, 4, 'panel', 2, glint=False)
    cv.hline(x, y, 3, T(glow, 4)); cv.set(x, y, T(glow, 5))


# --- props ---------------------------------------------------------------------------------
def barrel(cv, x, yb, fam='timber', hoop='iron', w=10, h=12):
    y = yb - h
    for (px, py) in rect(x, y, w, h):
        f = (px - x + 0.5) / w
        bulge = 1 if 0.25 < (py - y) / h < 0.75 else 0
        k = 4 if 0.15 < f < 0.4 else 3 if f < 0.65 else 2 if f < 0.85 else 1
        if (px == x or px == x + w - 1) and not bulge:
            continue
        cv.set(px, py, T(fam, k))
    for hy in (y + 2, y + h - 3):
        for px in range(x, x + w):
            if cv.get(px, hy)[3]:
                cv.set(px, hy, T(hoop, 3 if px < x + w * 0.5 else 1))
    for px in range(x + 1, x + w - 1):   # the lid
        cv.set(px, y, T(fam, 4 if px < x + w - 3 else 3))


def crate(cv, x, yb, fam='timber', w=12, h=10):
    y = yb - h
    part(cv, x, y, w, 3, fam, 4)                   # the top, lit
    boards(cv, x, y + 3, w, h - 3, lambda b, s: (sib(fam, noise2(b, s, 2), 0.3), 3), board=3, seed=x, nails=True, grain=0.05, joints=(40, 41))
    for i in range(h - 4):   # the brace
        cv.set(x + 1 + i * (w - 3) // (h - 4), y + 3 + i, T(fam, 4))
    frame(cv, x, y + 3, w, h - 3, fam, 2, t=1)


def bench(cv, x, yb, fam='timber', leg='iron', w=22):
    for (px, py) in rect(x, yb - 9, w, 2):
        cv.set(px, py, T(fam, 4 if py == yb - 9 else 3))
    for (px, py) in rect(x, yb - 6, w, 2):
        cv.set(px, py, T(fam, 4 if py == yb - 6 else 2))
    for lx in (x + 2, x + w - 4):
        for py in range(yb - 7, yb):
            cv.set(lx, py, T(leg, 3)); cv.set(lx + 1, py, T(leg, 1))
    cv.hline(x + 1, yb - 11, w - 2, T(fam, 3)); cv.hline(x + 1, yb - 12, w - 2, T(fam, 4))
    for lx in (x + 2, x + w - 4):
        cv.vline(lx, yb - 12, 3, T(leg, 3))


def planter(cv, x, yb, pot='clay', plant='leaf', w=10, h=7, seed=0):
    part(cv, x, yb - h, w, h, pot, 3)
    cv.hline(x - 1, yb - h, w + 2, T(pot, 4))
    leafy(cv, x + w / 2, yb - h - 4, w * 0.55, 5, seed=seed, ramp=plant)


def potted_cactus(cv, x, yb):
    """A clay pot with a ribbed column cactus and one arm, spines as lit pairs."""
    part(cv, x, yb - 6, 10, 6, 'clay', 3)
    cv.hline(x - 1, yb - 6, 12, T('clay', 4))
    cylinder(cv, x + 3, yb - 22, 4, 16, 'cactus', 3)
    cylinder(cv, x + 7, yb - 17, 3, 3, 'cactus', 3)
    cylinder(cv, x + 8, yb - 21, 3, 5, 'cactus', 3)
    for (px, py) in rect(x + 3, yb - 23, 4, 1):
        cv.set(px, py, T('cactus', 4))
    for yy in range(yb - 20, yb - 7, 3):
        cv.set(x + 2, yy, T('sand', 5)); cv.set(x + 7, yy + 1, T('sand', 4))


def lamp(cv, x, yb, h=30, metal='iron', glow='lamp'):
    cylinder(cv, x, yb - h, 2, h, metal, 3)
    part(cv, x - 2, yb - 3, 6, 3, metal, 3)
    part(cv, x - 3, yb - h - 2, 8, 2, metal, 4, glint=False)
    glass(cv, x - 2, yb - h, 6, 6, True)
    cv.vline(x - 3, yb - h, 6, T(metal, 4)); cv.vline(x + 4, yb - h, 6, T(metal, 1))
    part(cv, x - 3, yb - h + 6, 8, 2, metal, 3, glint=False)


def trough(cv, x, yb, w=20):
    part(cv, x, yb - 7, w, 7, 'timber', 3)
    for (px, py) in rect(x + 2, yb - 6, w - 4, 2):
        cv.set(px, py, T('water', 3 if (px + py) % 5 else 4))


def tank(cv, x, yb, fam='hull', w=10, h=18, band='berry'):
    cylinder(cv, x, yb - h, w, h, fam, 3)
    for py in (yb - h + 3, yb - 4):
        for px in range(x, x + w):
            step(cv, px, py, -1)
    for (px, py) in rect(x, yb - h + 7, w, 3):
        hit = tone_at(cv, px, py)
        cv.set(px, py, T(band, hit[1] if hit else 3))
    part(cv, x + w // 2 - 2, yb - h - 2, 4, 2, 'iron', 3, glint=False)


def console(cv, x, yb, w=18):
    part(cv, x, yb - 14, w, 14, 'panel', 3)
    part(cv, x + 2, yb - 12, w - 4, 6, 'void', 2, glint=False)
    for i, px in enumerate(range(x + 3, x + w - 3, 3)):
        cv.hline(px, yb - 10 + (i % 2), 2, T('neon_cyan' if i % 3 else 'glowflora', 4))
    for px in range(x + 3, x + w - 3, 4):
        cv.hline(px, yb - 4, 2, T(('berry', 'brass', 'glowflora')[(px // 4) % 3], 4))


def rock(cv, cx, yb, r, fam='regolith'):
    pts = {(x, y) for (x, y) in disc(cx, yb - r * 0.7, r) if y < yb}
    for (x, y) in pts:
        lv = -(x + 0.5 - cx) - (y + 0.5 - (yb - r * 0.7))
        cv.set(x, y, T(sib(fam, noise2(x, y, 3), 0.3), 4 if lv > r * 0.5 else 3 if lv > -r * 0.3 else 2))
    return pts


def dish(cv, x, yb):
    cylinder(cv, x + 6, yb - 14, 2, 14, 'iron', 3)
    for (px, py) in disc(x + 7, yb - 18, 6):
        if py < yb - 15 + (px - x - 7) * 0.3:
            lv = -(px - x - 7) - (py - yb + 18)
            cv.set(px, py, T('hull', 4 if lv > 2 else 3 if lv > -3 else 2))
    cv.set(x + 7, yb - 19, T('berry', 5))


# --- the environments ----------------------------------------------------------------------
def _sprite(w, h, draw):
    cv = Canvas(w + 2, h + 2)
    sub = Canvas(w, h)
    draw(sub)
    for y in range(h):
        for x in range(w):
            c = sub.get(x, y)
            if c[3]:
                cv.set(x + 1, y + 1, c)
    outline(cv)
    return cv


def _patch(wall_kind, w, h, draw, seed=0):
    """A piece shown on a patch of its own wall (doors, windows, roofs)."""
    cv = Canvas(w, h)
    wall(cv, 0, 0, w, h, wall_kind, seed)
    draw(cv)
    return cv


ENV = {
    'valley': {
        'walls': ('plaster', 'drystone', 'whitewash', 'boards_sky', 'pink'),
        'roofs': ('tiles', 'slate', 'thatch', 'palm'),
        'doors': [('sky', 'plank', 'stone', True), ('berry', 'panel', 'timber', False), ('timber', 'ledged', 'stone', False),
                  ('dusk', 'stable', 'timber', False), ('lagoon', 'plank', 'timber', False)],
        'windows': [dict(shutters='dusk', box=True), dict(cols=3, rows=1, lintel='stone'), dict(arch=True, frame_fam='stone', cols=2, rows=1),
                    dict(shutters='lagoon', lit=True), dict(cols=1, rows=2, box=True, frame_fam='sky', curtain=False)],
        'signs': ('bread', 'cup', 'fish', 'key'),
        'wall_patch': 'plaster',
    },
    'cogsworth': {
        'walls': ('brick', 'brick_soot', 'stock', 'ashlar'),
        'roofs': ('copper', 'slate', 'glass', 'tiles'),
        'doors': [('berry', 'panel', 'ashlar', False, True), ('iron', 'studded', 'brick', True, False),
                  ('dusk', 'glazed', 'ashlar', False, False), ('copper', 'panel', 'ashlar', True, True)],
        'windows': [dict(frame_fam='plaster', cols=2, rows=2, lintel='ashlar', lit=True), dict(frame_fam='plaster', arch=True, lit=True, cols=2),
                    dict(frame_fam='iron', cols=4, rows=3, sill='ashlar'), dict(frame_fam='plaster', cols=1, rows=2, lintel='ashlar', blind=True)],
        'signs': ('gear', 'cup', 'key', 'pot'),
        'wall_patch': 'brick',
    },
    'sunstone': {
        'walls': ('bleached', 'adobe', 'corrugated', 'boards_berry'),
        'roofs': ('falsefront', 'vigas', 'corrugated', 'shingle'),
        'doors': [('bleached', 'batwing', 'bleached', False), ('timber', 'studded', 'adobe', True),
                  ('bleached', 'glazed', 'bleached', False), ('timber', 'ledged', 'bleached', False)],
        'windows': [dict(frame_fam='bleached', curtain=False), dict(frame_fam='timber', bars=True, sill='adobe', cols=1, rows=1),
                    dict(frame_fam='bleached', cols=3, rows=2, lit=True), dict(frame_fam='bleached', shutters='bleached', cols=1, rows=2)],
        'signs': ('mug', 'sack', 'shoe', 'star'),
        'wall_patch': 'bleached',
    },
    'hearthold': {
        'walls': ('ashlar', 'rubble', 'ashlar', 'rubble'),
        'roofs': ('crenel', 'cone', 'slate', 'parapet'),
        'doors': [('timber', 'studded', 'ashlar', True), ('timber', 'plank', 'ashlar', True), ('timber', 'ledged', 'ashlar', True),
                  ('timber', 'studded', 'stone', False)],
        'windows': [dict(arch=True, frame_fam='ashlar', cols=1, rows=1, lit=True, leaded=True, sill='ashlar'),
                    dict(frame_fam='ashlar', cols=1, rows=1, sill=None, curtain=False),
                    dict(arch=True, frame_fam='ashlar', cols=2, rows=2, lit=True, leaded=True, sill='ashlar'),
                    dict(frame_fam='timber', cols=2, rows=1, shutters='timber', sill='ashlar')],
        'signs': ('shield', 'moon', 'star', 'key'),
        'wall_patch': 'ashlar',
    },
    'neon': {
        'walls': ('concrete', 'tile', 'brick_soot', 'concrete'),
        'roofs': ('flat', 'flat', 'parapet', 'flat'),
        'doors': [('iron', 'slide', 'concrete', False), ('panel', 'roller', 'concrete', False),
                  ('iron', 'panel', 'concrete', False), ('dusk', 'glazed', 'concrete', False)],
        'windows': [dict(frame_fam='concrete', lit=True, cols=2, rows=1), dict(frame_fam='iron', lit=True, blind=True, cols=1, rows=1, curtain=False),
                    dict(frame_fam='concrete', lit=False, cols=2, rows=2), dict(frame_fam='iron', lit=True, cols=3, rows=1, bars=True, curtain=False)],
        'signs': ('cup', 'bowl', 'moon', 'fish'),
        'wall_patch': 'concrete',
    },
    'halcyon': {
        'walls': ('hull', 'panel', 'hull', 'panel'),
        'roofs': ('radiator', 'dome', 'flat', 'radiator'),
        'doors': [(None, 'hatch', 'panel', False), (None, 'iris', 'panel', False), ('panel', 'slide', 'panel', False),
                  (None, 'hatch', 'hull', False)],
        'windows': [dict(round=True), dict(frame_fam='panel', cols=3, rows=1, lit=False, curtain=False, sill=None),
                    dict(frame_fam='panel', cols=1, rows=1, lit=True, curtain=False, sill=None), dict(round=True, lit=False)],
        'signs': ('bolt', 'leaf', 'bed', 'cup'),
        'wall_patch': 'bulkhead',
    },
    'lumen': {
        'walls': ('berm', 'hull_ext', 'berm', 'panel'),
        'roofs': ('berm', 'dome', 'radiator', 'berm'),
        'doors': [(None, 'hatch', 'hull', False), (None, 'iris', 'hull', False), (None, 'hatch', 'panel', False),
                  ('panel', 'slide', 'hull', False)],
        'windows': [dict(round=True), dict(round=True, lit=False), dict(frame_fam='panel', cols=2, rows=1, lit=True, curtain=False, sill=None),
                    dict(frame_fam='hull', cols=1, rows=1, lit=False, curtain=False, sill=None)],
        'signs': ('leaf', 'bolt', 'bed', 'moon'),
        'wall_patch': 'berm',
    },
}

PIECES = ('front', 'door', 'window', 'roof', 'sign', 'prop')


def variants(env: str, piece: str) -> int:
    e = ENV[env]
    return {'front': 4, 'door': len(e['doors']), 'window': len(e['windows']), 'roof': len(LAYOUT[env]),
            'sign': 4, 'prop': 4}[piece]


def _door_into(cv, env, v, x, yb, seed=0):
    spec = ENV[env]['doors'][v % len(ENV[env]['doors'])]
    fam, kind, frame_fam, arch = spec[:4]
    fan = spec[4] if len(spec) > 4 else False
    big = kind in ('batwing', 'slide', 'roller', 'studded') and env in ('sunstone', 'neon', 'hearthold')
    w, h = (22, 32) if big else (16, 26) if kind in ('hatch', 'iris') else (14, 28)
    frame_fam = {'brick': 'clay'}.get(frame_fam, frame_fam)
    lit = env in ('neon', 'halcyon', 'lumen', 'cogsworth')
    doorway(cv, x, yb, w, h, fam or 'panel', kind, frame_fam, seed=seed + v, arch=arch, fan=fan,
            step_fam=None if env in ('halcyon',) else ('regolith' if env == 'lumen' else 'stone'), lit=lit)
    return w


def _window_into(cv, env, v, x, y, seed=0):
    spec = dict(ENV[env]['windows'][v % len(ENV[env]['windows'])])
    if spec.pop('round', False):
        lit = spec.get('lit', True)
        porthole(cv, x + 7, y + 7, 7, 'brass' if env == 'cogsworth' else 'hull' if env == 'lumen' else 'panel', lit)
        return 14
    w = 12 if env in ('neon', 'cogsworth') else 16
    h = 16 if env in ('neon', 'cogsworth') else 14
    if spec.get('cols', 2) >= 3:
        w = 18
    if env == 'hearthold' and spec.get('arch') and spec.get('cols', 1) == 1:
        w, h = 8, 18
    if env == 'hearthold' and not spec.get('arch') and spec.get('sill', 'x') is None:
        for yy in range(y, y + 16):   # an arrow slit: a splayed reveal, a dark slot, a cross at mid height
            cv.set(x, yy, T('ashlar', 5)); cv.set(x + 1, yy, T('ashlar', 4))
            cv.set(x + 2, yy, T('stone', 0)); cv.set(x + 3, yy, T('stone', 0))
            cv.set(x + 4, yy, T('ashlar', 2))
        cv.hline(x + 1, y + 7, 3, T('stone', 0))
        part(cv, x - 1, y - 2, 7, 2, 'ashlar', 4, glint=False)
        part(cv, x - 1, y + 16, 7, 2, 'ashlar', 4, glint=False)
        return 5
    casement(cv, x, y, w, h, **spec)
    return w


def door(env, v):
    kind = ENV[env]['wall_patch']
    return _patch(kind, 40, 44, lambda cv: _door_into(cv, env, v, 12, 40, seed=v), seed=v + 3)


def window(env, v):
    kind = ENV[env]['wall_patch']
    return _patch(kind, 36, 32, lambda cv: _window_into(cv, env, v, 9, 6, seed=v), seed=v + 5)


def roof(env, v):
    """A roof or top, standing on a short piece of wall."""
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    cv = Canvas(50, 46)
    wall(cv, 2, 28, 46, 18, lay['wall'], v)
    roof_mass(cv, 2, 2, 46, 26, lay['roof'], lay['shape'], seed=v + 11, gable_wall=lay.get('gable', lay['wall']))
    return cv


def sign(env, v):
    pics = ENV[env]['signs']
    pic = pics[v % len(pics)]
    kind = 'hull_ext' if env == 'lumen' else ENV[env]['wall_patch']   # signs go on the shell, never on the soil
    cv = Canvas(40, 30)
    wall(cv, 0, 0, 40, 30, kind, v + 7)
    if env == 'valley':
        hanging_sign(cv, 2, 6, pic, ('timber', 'sky', 'berry', 'dusk')[v], 'brass' if v != 3 else 'plaster')
    elif env == 'cogsworth':
        if v < 2:
            fascia(cv, 2, 8, 36, pic, ('berry', 'copper')[v], 'brass')
        elif v == 2:
            hanging_sign(cv, 2, 4, pic, 'iron', 'brass')
        else:
            part(cv, 10, 8, 20, 14, 'brass', 3)
            picto(cv, 17, 11, pic, 'iron', 2)
    elif env == 'sunstone':
        if v < 3:
            fascia(cv, 2, 8, 36, pic, ('berry', 'sky', 'bleached')[v], 'plaster' if v < 2 else 'berry')
        else:
            hanging_sign(cv, 2, 4, pic, 'bleached', 'clay')
    elif env == 'hearthold':
        if v == 0:
            banner(cv, 13, 5, 12, 20)
        elif v == 1:
            for (x, y) in rect(12, 4, 16, 18):   # a painted shield on the wall
                if y < 14 or abs(x + 0.5 - 20) < (22 - y) * 1.0:
                    cv.set(x, y, T('berry' if (x < 20) == (y < 13) else 'brass', 4 if x < 16 else 3))
            outline(cv, {(x, y) for (x, y) in rect(12, 4, 16, 18) if y < 14 or abs(x + 0.5 - 20) < (22 - y) * 1.0})
        elif v == 2:   # a torch in a sconce
            part(cv, 17, 14, 6, 3, 'iron', 3)
            cv.vline(19, 9, 5, T('timber', 3)); cv.vline(20, 9, 5, T('timber', 1))
            for (x, y) in disc(19.5, 7, 2.5):
                cv.set(x, y, T('lava', 4 if y > 6 else 5))
        else:
            part(cv, 10, 6, 20, 14, 'ashlar', 4)
            picto(cv, 17, 9, pic, 'ashlar', 2)
    elif env == 'neon':
        for (x, y) in rect(0, 8, 40, 12):
            cv.set(x, y, T('asphalt', 2 if 9 <= y <= 18 else 1))
        if v < 2:
            neon_tube(cv, 16, 10, pic, ('neon_pink', 'neon_cyan')[v])
        elif v == 2:
            blade(cv, 15, 2, 26, 'neon_cyan', ('moon', 'cup'))
        else:
            awning(cv, 0, 12, 40, 'lagoon', 'plaster')
    else:   # halcyon, lumen
        if v < 2:
            stencil(cv, 4, 10, 32, ('berry', 'sky')[v], pic)
        elif v == 2:
            part(cv, 10, 8, 20, 12, 'plaster', 4)
            picto(cv, 17, 10, pic, 'iron', 2)
            status_light(cv, 31, 9)
        else:
            for x in range(2, 38):
                for y in range(18, 22):
                    cv.set(x, y, T('brass', 4) if ((x + y) // 3) % 2 else T('iron', 1))
            status_light(cv, 18, 8, 'neon_cyan' if env == 'halcyon' else 'glowflora')
    return cv


def prop(env, v):
    def draw(cv):
        yb = cv.h - 2
        if env == 'valley':
            [lambda: barrel(cv, 4, yb), lambda: bench(cv, 1, yb, 'timber', 'timber'),
             lambda: planter(cv, 5, yb, 'clay', 'leaf', seed=v), lambda: crate(cv, 3, yb, 'timber')][v]()
        elif env == 'cogsworth':
            [lambda: lamp(cv, 9, yb, 26, 'iron'), lambda: bench(cv, 1, yb, 'timber', 'iron'),
             lambda: barrel(cv, 4, yb, 'iron', 'brass'), lambda: crate(cv, 3, yb, 'copper')][v]()
        elif env == 'sunstone':
            [lambda: barrel(cv, 4, yb, 'bleached', 'iron'), lambda: trough(cv, 1, yb),
             lambda: crate(cv, 3, yb, 'bleached'), lambda: potted_cactus(cv, 5, yb)][v]()
        elif env == 'hearthold':
            [lambda: barrel(cv, 4, yb, 'timber', 'iron'), lambda: bench(cv, 1, yb, 'ashlar', 'ashlar'),
             lambda: lamp(cv, 9, yb, 20, 'iron', 'lava'), lambda: crate(cv, 3, yb, 'timber')][v]()
        elif env == 'neon':
            [lambda: planter(cv, 5, yb, 'concrete', 'leaf', seed=v), lambda: bench(cv, 1, yb, 'iron', 'iron'),
             lambda: lamp(cv, 9, yb, 28, 'iron'), lambda: crate(cv, 3, yb, 'sky')][v]()
        elif env == 'halcyon':
            [lambda: tank(cv, 6, yb), lambda: console(cv, 2, yb), lambda: crate(cv, 3, yb, 'panel'),
             lambda: planter(cv, 5, yb, 'hull', 'leaf', seed=v)][v]()
        else:
            [lambda: rock(cv, 11, yb, 7), lambda: dish(cv, 4, yb), lambda: tank(cv, 6, yb, 'hull', band='brass'),
             lambda: crate(cv, 3, yb, 'panel')][v]()
    return _sprite(22, 34, draw)


# Each front is a whole building made only of its environment's pieces: wall, roof (kind and
# shape), storeys, and what stands in its face (x positions on a 68 px front).
LAYOUT = {
    'valley': [
        dict(wall='plaster', roof='tiles', shape='ridge', items=[('chimney', 10), ('door', 0, 10), ('win', 0, 40), ('rose', 27), ('pots', 58), ('lantern', 30), ('pipe', 64)]),
        dict(wall='drystone', roof='slate', shape='gable', gable='boards_timber', items=[('win', 1, 8), ('door', 1, 44), ('sign', 1, 26), ('lantern', 38)]),
        dict(wall='whitewash', roof='thatch', shape='hip', items=[('win', 3, 6), ('door', 2, 27), ('win', 0, 46), ('rose', 22), ('pots', 2), ('lantern', 44)]),
        dict(wall='boards_lagoon', roof='palm', shape='hip', items=[('door', 3, 8), ('win', 4, 40), ('sign', 2, 26), ('lantern', 26), ('pots', 58)]),
    ],
    'cogsworth': [
        dict(wall='brick', roof='copper', shape='ridge', storeys=2, items=[('door', 1, 27), ('win', 0, 8, 'up'), ('win', 0, 46, 'up'), ('fascia', 0)]),
        dict(wall='brick_soot', roof='slate', shape='gable', gable='brick_soot', storeys=2, items=[('chimney', 50), ('door', 0, 10), ('win', 0, 42), ('win', 3, 12, 'up'), ('win', 3, 42, 'up')]),
        dict(wall='stock', roof='slate', shape='ridge', storeys=2, items=[('shopwin', 4, 30), ('door', 2, 46), ('fascia', 2), ('win', 1, 10, 'up'), ('win', 1, 44, 'up')]),
        dict(wall='ashlar', roof='glass', shape='ridge', storeys=2, items=[('door', 3, 27), ('win', 2, 6, 'up'), ('win', 2, 26, 'up'), ('win', 2, 46, 'up'), ('lamp', 52), ('pipe', 2), ('fascia', 3), ('poster', 46, 52), ('pots', 18)]),
    ],
    'sunstone': [
        dict(wall='bleached', roof='corrugated', shape='falsefront', storeys=2, items=[('door', 0, 23), ('win', 0, 26, 'up'), ('fascia', 0), ('porch', 0)]),
        dict(wall='adobe', roof='adobe', shape='vigas', items=[('door', 1, 8), ('win', 1, 44), ('sign', 3, 30)]),
        dict(wall='boards_berry', roof='corrugated', shape='ridge', items=[('shopwin', 4, 26), ('door', 2, 44), ('fascia', 1), ('lantern', 36), ('poster', 58, 30)]),
        dict(wall='corrugated', roof='shingle', shape='ridge', items=[('door', 3, 26), ('win', 3, 6), ('win', 3, 48), ('sign', 3, 44)]),
    ],
    'hearthold': [
        dict(wall='ashlar', roof='ashlar', shape='crenel', storeys=2, items=[('door', 0, 23), ('win', 1, 10, 'up'), ('win', 1, 54, 'up'), ('banner', 6), ('banner', 52)]),
        dict(wall='rubble', roof='slate', shape='gable', gable='ashlar', storeys=2, items=[('door', 1, 27), ('win', 0, 8, 'up'), ('win', 0, 52, 'up')]),
        dict(wall='ashlar', roof='slate', shape='ridge', storeys=2, items=[('door', 2, 8), ('win', 2, 40, 'up'), ('banner', 52)]),
        dict(wall='rubble', roof='shingle', shape='ridge', items=[('door', 3, 40), ('win', 3, 8), ('sign', 2, 24)]),
    ],
    'neon': [
        dict(wall='concrete', roof='flat', shape='flat', storeys=2, items=[('shopwin', 4, 32), ('door', 0, 44), ('awning', 0), ('win', 0, 8, 'up'), ('win', 1, 44, 'up'), ('ac', 26, 26), ('poster', 54, 44), ('pipe', 64), ('lantern', 38), ('service', 50, 18), ('pots', 56)]),
        dict(wall='tile', roof='flat', shape='flat', storeys=2, items=[('shopwin', 4, 32), ('door', 1, 44), ('neon', 'bowl', 12), ('win', 0, 8, 'up'), ('win', 2, 44, 'up'), ('ac', 26, 30), ('pipe', 64), ('poster', 22, 46)]),
        dict(wall='brick_soot', roof='parapet', shape='flat', storeys=2, items=[('door', 2, 10), ('win', 3, 36), ('blade', 56), ('win', 0, 8, 'up'), ('win', 1, 36, 'up')]),
        dict(wall='concrete', roof='flat', shape='flat', storeys=2, items=[('shopwin', 4, 40), ('door', 3, 48), ('blade', 2), ('win', 3, 14, 'up'), ('win', 0, 44, 'up'), ('ac', 50, 36), ('poster', 32, 26), ('pipe', 64), ('service', 28, 40), ('pots', 2)]),
    ],
    'halcyon': [
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[('door', 0, 8), ('win', 0, 40), ('stencil', 0), ('status', 30), ('pipe', 60)]),
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[('door', 1, 26), ('win', 3, 6), ('win', 3, 50), ('status', 46), ('pipe', 22)]),
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[('door', 2, 44), ('win', 1, 6), ('stencil', 1), ('status', 38), ('pipe', 2)]),
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[('door', 3, 8), ('win', 2, 42), ('status', 30), ('pipe', 62)]),
    ],
    'lumen': [
        dict(wall='berm', roof='regolith', shape='berm', items=[('door', 0, 26), ('win', 0, 6), ('status', 46)]),
        dict(wall='hull_ext', roof='hull', shape='dome', items=[('door', 1, 8), ('win', 2, 40), ('stencil', 0), ('status', 30), ('service', 46, 52), ('pipe', 62)]),
        dict(wall='hull_ext', roof='hull', shape='radiator', items=[('door', 2, 44), ('win', 1, 8), ('win', 1, 24), ('status', 38), ('pipe', 62), ('service', 10, 50), ('stencil', 1)]),
        dict(wall='berm', roof='regolith', shape='berm', items=[('door', 3, 8), ('win', 3, 40), ('status', 30)]),
    ],
}
ROOF_H = {'valley': 28, 'cogsworth': 24, 'sunstone': 24, 'hearthold': 22, 'neon': 18, 'halcyon': 18, 'lumen': 26}
STOREY = {'valley': 40, 'cogsworth': 34, 'sunstone': 36, 'hearthold': 32, 'neon': 34, 'halcyon': 38, 'lumen': 36}


def front(env, v):
    """A whole building front in the environment, 68 px wide: roof or top, one or two
    storeys of its wall, its door, windows and sign; built only from this kit's pieces."""
    e = ENV[env]
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    W = 68
    rh = ROOF_H[env]
    storeys = lay.get('storeys', 1)
    sh = STOREY[env] if storeys == 1 else STOREY[env] + 28
    H = rh + sh + 4

    def draw(cv):
        wall(cv, 0, rh, W, sh, lay['wall'], seed=v * 13 + 1)
        if storeys == 2 and env in ('cogsworth', 'hearthold', 'neon'):   # a string course between the storeys
            part(cv, 0, rh + sh - STOREY[env] - 2, W, 3, 'ashlar' if env != 'neon' else 'concrete', 4, glint=False)
            overhang(cv, 0, W, rh + sh - STOREY[env] + 1, 1)
        if env in ('valley', 'cogsworth', 'hearthold'):
            plinth(cv, 0, H - 4, W, 4, 'stone', v)
        elif env == 'sunstone':
            for x in range(W):
                for y in range(H - 4, H):
                    cv.set(x, y, T(sib('timber', noise2(x // 8, 0, v), 0.3), 4 if y == H - 4 else 3 if y < H - 1 else 1))
                if x % 8 == 0:
                    cv.set(x, H - 3, T('timber', 1))
        elif env == 'lumen':
            plinth(cv, 0, H - 4, W, 4, 'regolith', v)
            if lay['wall'] in ('hull', 'hull_ext', 'panel'):   # moon dust kicked up onto the lower plates
                for (x, y) in rect(0, H - 14, W, 10):
                    if smooth_noise(x, y, 3, v + 40) > 0.5 + 0.04 * (H - 4 - y) and tone_at(cv, x, y) and hp.family(tone_at(cv, x, y)[0]) in ('hull', 'panel', 'iron'):
                        cv.set(x, y, T(sib('regolith', noise2(x, y, v), 0.3), 4 if y < H - 9 else 3))
        else:
            part(cv, 0, H - 4, W, 4, 'concrete' if env == 'neon' else 'panel', 3)
        roof_mass(cv, 0, 0, W, rh, lay['roof'], lay['shape'], seed=v * 7 + 2, gable_wall=lay.get('gable', lay['wall']))
        yb = H - 4
        up_y = rh + 6
        low_y = yb - 28 + 2 if storeys == 1 else yb - STOREY[env] + 8
        for it in lay['items']:
            k = it[0]
            if k == 'door':
                _door_into(cv, env, it[1], it[2], yb, seed=v)
            elif k == 'win':
                y = up_y if len(it) > 3 else low_y
                _window_into(cv, env, it[1], it[2], y, seed=v)
            elif k == 'chimney':
                chimney(cv, it[1], 0, 12, 'brick' if env == 'cogsworth' else 'stone')
            elif k == 'sign':
                hanging_sign(cv, it[2], rh + 4, e['signs'][it[1]], ('timber', 'sky', 'berry', 'bleached')[it[1]] if env != 'sunstone' else 'bleached',
                             'brass' if env != 'sunstone' else 'clay')
            elif k == 'fascia':
                fy = rh + 1 if env == 'sunstone' else yb - 40 if storeys == 2 else rh + 2
                fascia(cv, 3, fy, W - 6, e['signs'][it[1]], ('berry', 'copper', 'sky', 'dusk')[it[1]] if env == 'cogsworth' else ('berry', 'sky', 'bleached')[it[1]],
                       'brass' if env == 'cogsworth' else 'plaster')
            elif k == 'shopwin':
                x, w = it[1], it[2]
                top = yb - 26
                glass(cv, x, top, w, 22, True)
                for sy in (top + 8, top + 15):
                    cv.hline(x + 1, sy, w - 2, T('timber', 2))
                    for i, xx in enumerate(range(x + 2, x + w - 2, 4)):
                        col = ('lagoon', 'berry', 'brass', 'plaster', 'sky', 'leaf')[(i + sy + v) % 6]
                        cv.vline(xx, sy - 3, 3, T(col, 3)); cv.vline(xx + 1, sy - 3, 3, T(col, 2)); cv.set(xx, sy - 3, T(col, 4))
                frame(cv, x - 1, top - 1, w + 2, 24, 'iron' if env == 'neon' else 'timber', 3, t=1)
                part(cv, x - 2, top + 22, w + 4, 2, 'stone' if env != 'sunstone' else 'bleached', 4, glint=False)
            elif k == 'awning':
                awning(cv, 0, yb - 36, 40, 'berry', 'plaster', 6)
            elif k == 'neon':
                for (x, y) in rect(4, yb - 36, 32, 9):
                    cv.set(x, y, T('asphalt', 2 if yb - 35 <= y <= yb - 29 else 1))
                neon_tube(cv, it[2] + 4, yb - 35, it[1], 'neon_cyan', wall_fams=('asphalt',))
            elif k == 'blade':
                blade(cv, it[1], rh + 6, 26, 'neon_cyan' if it[1] > 30 else 'neon_pink', ('cup', 'moon'))
            elif k == 'porch':
                py = yb - 34
                for (x, y) in rect(0, py, W, 4):
                    j = x % 4
                    cv.set(x, y, T('iron', 5 if y == py and j == 0 else 4 if j == 0 else 3 if j == 1 else 2) if y < py + 3 else T('iron', 1))
                overhang(cv, 0, W, py + 4, 4)
                for px in (2, W - 5):
                    cylinder(cv, px, py + 4, 3, yb - py - 4, 'bleached', 3)
            elif k == 'rose':   # a climbing rose up the wall beside the door
                for i in range(20):
                    yy = yb - 2 - int(i * 1.5)
                    xx = it[1] + int(2 * math.sin(i * 0.7))
                    if yy < rh + 8:
                        break
                    cv.hline(xx, yy, 2, T(sib('leaf', noise2(i, 0, v), 0.3), 3 if i % 3 else 4)); cv.set(xx + 1, yy + 1, T('leaf', 1))
                    if i % 4 == 1:
                        cv.hline(xx - 1, yy - 1, 2, T('berry', 4)); cv.set(xx - 1, yy - 1, T('berry', 5))
            elif k == 'lantern':
                part(cv, it[1], yb - 26, 5, 7, 'iron', 2, glint=False)
                glass(cv, it[1] + 1, yb - 25, 3, 5, True)
                cv.hline(it[1], yb - 27, 5, T('iron', 4))
            elif k == 'pots':   # pots on the plinth, a herb in each
                for j in range(2):
                    part(cv, it[1] + j * 5, yb - 5, 4, 5, 'clay', 3, glint=False)
                    for (px, py) in disc(it[1] + j * 5 + 2, yb - 7, 2.4):
                        cv.set(px, py, T(sib('leaf', noise2(px, py, j), 0.35), 4 if px + py < it[1] + j * 5 + yb - 5 else 2))
            elif k == 'ac':   # a wall air conditioner on a bracket, its drip stain below
                part(cv, it[1], it[2], 12, 8, 'panel', 3)
                for xx in range(it[1] + 2, it[1] + 10, 2):
                    cv.vline(xx, it[2] + 2, 4, T('panel', 1))
                cv.hline(it[1], it[2] + 8, 12, T('iron', 1))
                for yy in range(it[2] + 9, min(yb - 2, it[2] + 20)):
                    step(cv, it[1] + 9, yy, -1); step(cv, it[1] + 10, yy, -1)
            elif k == 'poster':
                for j, (pw, ph, c) in enumerate(((7, 9, 'plaster'), (6, 8, 'sky'), (6, 6, 'berry'))):
                    px, py = it[1] + j * 5, it[2] + (j % 2) * 3
                    part(cv, px, py, pw, ph, c, 3, glint=False)
                    cv.hline(px + 1, py + 2, pw - 2, T(c, 1)); cv.hline(px + 1, py + 4, pw - 3, T(c, 2))
            elif k == 'pipe':   # a pipe down the wall on brackets, with a valve
                fam = 'copper' if env in ('halcyon', 'lumen') else 'iron'
                cylinder(cv, it[1], rh + 2, 3, yb - rh - 4, fam, 3)
                for by in range(rh + 6, yb - 4, 10):
                    part(cv, it[1] - 1, by, 5, 2, 'iron', 3, glint=False)
                for yy in range(rh + 2, yb - 2):
                    step(cv, it[1] + 3, yy, -1)
                for (px, py) in disc(it[1] + 1.5, yb - 14, 2.5):
                    cv.set(px, py, T('berry', 4 if px + py < it[1] + yb - 12 else 2))
            elif k == 'service':   # a service panel: a grille, a label plate, two gauges
                x0_, y0_ = it[1], it[2]
                part(cv, x0_, y0_, 14, 12, 'panel', 3)
                for xx in range(x0_ + 2, x0_ + 12, 2):
                    cv.vline(xx, y0_ + 2, 4, T('panel', 1))
                part(cv, x0_ + 2, y0_ + 7, 6, 3, 'plaster', 4, glint=False)
                for gx in (x0_ + 10, x0_ + 12):
                    cv.set(gx, y0_ + 8, T('brass', 4)); cv.set(gx, y0_ + 9, T('brass', 2))
                cv.hline(x0_, y0_ + 12, 14, T('iron', 1))
            elif k == 'lamp':
                cv.hline(it[1], rh + sh - 30, 6, T('iron', 4))
                glass(cv, it[1] + 3, rh + sh - 29, 5, 6, True)
                cv.vline(it[1] + 2, rh + sh - 29, 6, T('iron', 4)); cv.vline(it[1] + 8, rh + sh - 29, 6, T('iron', 1))
            elif k == 'banner':
                banner(cv, it[1], rh + 6, 10, 20)
            elif k == 'stencil':
                stencil(cv, 4 if it[1] != 1 else 20, rh + 4, 26, ('berry', 'sky', 'brass')[it[1]], e['signs'][it[1]])
            elif k == 'status':
                status_light(cv, it[1], yb - 30, 'glowflora' if v % 2 else 'neon_cyan')
    return _sprite(W, H, draw)


# --- today's equivalents -------------------------------------------------------------------
TODAY = {
    'valley': [('harbour_props', 'cottage'), ('world_props', 'house_red'), ('isle_props', 'boathouse')],
    'cogsworth': [('steampunk_props', 'workshop'), ('steampunk_props', 'house_slate'), ('steampunk_props', 'shop_ashlar')],
    'sunstone': [('western_props', 'saloon'), ('western_props', 'store'), ('western_props', 'water_jar')],
    'hearthold': [('castle_props', 'gatehouse'), ('castle_props', 'postern'), ('castle_props', 'weapon_rack')],
    'neon': [('cyber_props', 'noodle_stall'), ('cyber_props', 'vending_machine'), ('cyber_props', 'city_food_kiosk')],
    'halcyon': [('space_props', 'airlock'), ('space_props', 'lockers'), ('space_props', 'console')],
    'lumen': [('space_props', 'airlock_module'), ('space_props', 'glass_dome'), ('space_props', 'old_lander')],
}


def today(env):
    import importlib
    import style
    out = []
    for mod, key in TODAY[env]:
        sp = importlib.import_module(mod).props()[key]
        img = style.finalize(sp, name=key).img
        if img.height > 110:   # tall buildings: their lower part, where the pieces are
            img = img.crop((0, img.height - 110, img.width, img.height))
        if img.width > 110:
            img = img.crop(((img.width - 110) // 2, 0, (img.width - 110) // 2 + 110, img.height))
        out.append((key, img))
    return out


# --- the kit sheet -------------------------------------------------------------------------
BAR_KIND_FRONT = {('lumen', 0): 'ground', ('lumen', 3): 'ground'}   # a heap of moon soil is ground
BAR_KIND = {'valley': 'facade', 'cogsworth': 'facade', 'sunstone': 'wood-front', 'hearthold': 'stone-wall',
            'neon': 'facade', 'halcyon': 'machinery', 'lumen': 'machinery'}


def sheet(env, out_dir, scale=3):
    from style_sheet import _font
    bg, fg = (52, 48, 58, 255), (236, 230, 214, 255)
    rows = [('today (main)', [img for _k, img in today(env)])]
    for piece in PIECES:
        fn = globals()[piece]
        rows.append((piece + 's', [fn(env, v).img for v in range(variants(env, piece))]))
    pad, lab = 10 * scale, 22
    width = max(sum(i.width * scale + pad for i in imgs) + pad for _t, imgs in rows)
    width = max(width, 900)
    height = 60 + sum(max(i.height for i in imgs) * scale + lab + pad for _t, imgs in rows)
    im = Image.new('RGBA', (width, height), bg)
    d = ImageDraw.Draw(im)
    d.text((pad, 14), f'{TITLES[env]}: the house kit (3x; an adult is 25 px)', fill=fg, font=_font(24))
    y = 60
    for title, imgs in rows:
        d.text((pad, y), title, fill=fg, font=_font(15))
        y += lab
        x = pad
        hmax = max(i.height for i in imgs) * scale
        for i in imgs:
            big = i.resize((i.width * scale, i.height * scale), Image.NEAREST)
            im.alpha_composite(big, (x, y + hmax - big.height))
            x += big.width + pad
        y += hmax + pad
    path = os.path.join(out_dir, f'kit-{env}.png')
    im.save(path)
    return path


def report(env):
    import style_lint
    lines = []
    for v in range(variants(env, 'front')):
        cv = front(env, v)
        m = style_lint.measure(cv.img)
        miss = style_lint.misses(m)
        bar = ''
        try:
            import detail_bar
            rh = ROOF_H[env]
            box = (2, rh + 2, 66, cv.h - 6)
            kind = BAR_KIND_FRONT.get((env, v), BAR_KIND[env])
            ok, _c, bl = detail_bar.check_image(cv.img.convert('RGB'), box, kind)
            bar = f'bar {kind} {"PASS" if ok else "FAIL"} ' + '; '.join(s for s in bl if 'LOW' in s or 'NOISY' in s)
        except ImportError:
            bar = 'bar skipped (detail_bar.py not here)'
        lines.append(f'  front {v}: {m["colours"]} colours, {100 * m["on_house"]:.0f}% house, W-E {m["west_east"]:+.1f}, '
                     f'lone {100 * m["isolated"]:.1f}%  lint {" ".join(miss) or "ok"}  {bar}')
    worst = []
    for piece in ('prop',):
        for v in range(variants(env, piece)):
            m = style_lint.measure(globals()[piece](env, v).img)
            if style_lint.misses(m):
                worst.append(f'{piece} {v}: {" ".join(style_lint.misses(m))}')
    print(f'{env}:')
    print('\n'.join(lines))
    if worst:
        print('  ' + '; '.join(worst))


def main(argv) -> int:
    import tempfile
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-house-kits')
    os.makedirs(out, exist_ok=True)
    envs = [a for a in argv[1:] if a in ENVS] or list(ENVS)
    for env in envs:
        print('wrote', sheet(env, out))
        report(env)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

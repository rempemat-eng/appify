"""The world map's tiles (docs/vision/world-atlas.md, "The map"): every zone drawn small
as a paper map, from what the world lint reads it as (water, lava, walls and cliffs,
paths, ground) plus its buildings and trees. One map pixel stands for 8 zone pixels
(2 x 2 walk cells), so a zone is 40 x 72. Inked, not shrunk: the ground keeps its
place's colour softened toward parchment, shores and path edges get a darker line, and
buildings are solid roofs with a shadowed edge, so the map reads at a glance and every
tile agrees with the walkable world it stands for.
"""
from __future__ import annotations

import os
import re

from pixel import Canvas

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MW, MH = 40, 72  # a zone on the map
PARCHMENT = (233, 221, 187)
INK = {
    '~': ((127, 166, 201), (78, 122, 166)),  # water, its shore line
    '!': ((216, 106, 58), (150, 60, 34)),     # lava, its crust
    '^': ((122, 110, 98), (84, 74, 66)),      # walls and cliffs
    '=': ((176, 136, 98), (128, 92, 66)),     # paths, their worn edge
}
ROOF_EDGE = (70, 48, 44)
PRIORITY = {'~': 5, '=': 4, '!': 3, '^': 2, '.': 1}
TREE = (78, 112, 70)
TREE_DARK = (52, 80, 52)
TRUNKED = ('tree', 'pine', 'willow', 'acacia', 'palm', 'snag')


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _quant(c, step=12):
    return tuple(min(255, (v // step) * step + step // 2) for v in c)


def tile(terrain: list[str], ground, objects=(), sprites=None, doors=()) -> Canvas:
    """A zone's map tile. `terrain` is the lint's 80 x 144 cell grid, `ground` the zone's
    ground image in zone pixels, `objects` (id, sprite, x, y) with `sprites` sizes."""
    px = ground.convert('RGB').load()
    cv = Canvas(MW, MH)
    cls = [[None] * MW for _ in range(MH)]
    for my in range(MH):
        for mx in range(MW):
            cells = [terrain[my * 2 + dy][mx * 2 + dx] for dy in (0, 1) for dx in (0, 1)]
            # (ties broken by a fixed order, never by set order, which changes per run)
            k = max(sorted(set(cells)), key=lambda c: (cells.count(c), PRIORITY[c]))
            cls[my][mx] = k
            if k in ('.', '^'):
                # ground (and fields, walls, cliffs: whatever blocks the way) keeps the
                # place's own colour, softened toward the paper
                tot = [0, 0, 0]
                for yy in range(my * 8, my * 8 + 8, 2):
                    for xx in range(mx * 8, mx * 8 + 8, 2):
                        r, g, b = px[xx, yy]
                        tot[0] += r; tot[1] += g; tot[2] += b
                mean = tuple(t // 16 for t in tot)
                c = _quant(_mix(mean, PARCHMENT, 0.45 if k == '.' else 0.2))
            else:
                c = INK[k][0]
            cv.set(mx, my, '#%02X%02X%02X' % c)
    # ink the edges of water, lava and paths where they meet anything else
    for my in range(MH):
        for mx in range(MW):
            k = cls[my][mx]
            if k not in ('~', '!', '='):
                continue
            near = [cls[yy][xx] for (xx, yy) in ((mx + 1, my), (mx - 1, my), (mx, my + 1), (mx, my - 1))
                    if 0 <= xx < MW and 0 <= yy < MH]
            if any(n != k and not (k == '~' and n == '^') for n in near):
                cv.set(mx, my, '#%02X%02X%02X' % INK[k][1])
    # trees as dark dots, buildings as roofs (drawn by their feet, the way the map is read)
    for (_oid, key, x, y) in objects:
        if sprites is None or key not in sprites:
            continue
        w, h = sprites[key]
        if any(t in key for t in TRUNKED):
            cx, cy = (x + w // 2) // 8, (y + h * 2 // 3) // 8
            for (xx, yy) in ((cx, cy), (cx - 1, cy), (cx, cy - 1)) if w >= 40 else ((cx, cy),):
                if 0 <= xx < MW and 0 <= yy < MH:
                    cv.set(xx, yy, '#%02X%02X%02X' % (TREE if (xx, yy) != (cx, cy) else TREE_DARK))
        elif key in doors or (w >= 40 and h >= 36 and 'gate' not in key and 'fence' not in key):
            x0, x1 = max(0, x // 8), min(MW - 1, (x + w - 1) // 8)
            y0, y1 = max(0, (y + h // 3) // 8), min(MH - 1, (y + h - 1) // 8)
            roof = (164, 80, 62) if key in doors else (118, 108, 124)
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    edge = yy == y1 or xx == x1
                    cv.set(xx, yy, '#%02X%02X%02X' % (ROOF_EDGE if edge else roof))
    return cv


def garden_objects():
    """The garden's props from lib/garden-map.ts (garden.py draws them): id, sprite, box."""
    src = open(os.path.join(ROOT, 'lib', 'garden-map.ts')).read()
    out = []
    # (formatted or as garden.py first writes it, with JSON quotes)
    q = '["\']'
    pat = (rf"{q}?id{q}?:\s*{q}([^\"']+){q},\s*{q}?sprite{q}?:\s*{q}([^\"']+){q},\s*"
           rf"{q}?x{q}?:\s*(-?\d+),\s*{q}?y{q}?:\s*(-?\d+),\s*{q}?w{q}?:\s*(\d+),\s*{q}?h{q}?:\s*(\d+)")
    for m in re.finditer(pat, src):
        oid, key, x, y, w, h = m.groups()
        out.append((oid, key, int(x), int(y), int(w), int(h)))
    return out


def write_all(built: dict, garden: dict, doors) -> dict:
    """Write every zone's map tile next to its ground; returns {zone: path}."""
    paths = {}
    for name, z in built.items():
        sizes = {k: (sp.w, sp.h) for k, sp in z['sprites'].items()}
        cv = tile(z['terrain'], z['ground_img'], z['objects'], sizes, doors)
        out = os.path.join(ROOT, 'assets', 'zones', name, 'map.png')
        cv.save(out, 4)
        paths[name] = out
    gobjs = garden_objects()
    sizes = {key: (w, h) for (_i, key, _x, _y, w, h) in gobjs}
    cv = tile(garden['terrain'], garden['ground'], [(i, k, x, y) for (i, k, x, y, _w, _h) in gobjs],
              sizes, set(doors) | {'hut'})
    os.makedirs(os.path.join(ROOT, 'assets', 'zones', 'garden'), exist_ok=True)
    out = os.path.join(ROOT, 'assets', 'zones', 'garden', 'map.png')
    cv.save(out, 4)
    paths['garden'] = out
    return paths

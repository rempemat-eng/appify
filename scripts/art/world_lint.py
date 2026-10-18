"""The world's logic lint (docs/vision/world-rules.md, section 7, stage 1).

Every zone's ground is read as meaning, one 4 px walk cell at a time: water, lava,
wall or cliff, path, ground. Then the rules are checked: what each prop may stand on
(its placement type), whether water, paths and the ground's tone carry on across the
borders between neighbouring zones, and whether paths lead somewhere. zones.py calls
`run(built)` after building every zone; it prints a summary, returns the violations
and, when LINT_OUT names a folder, writes a report and each region drawn whole with
the violations boxed in red (stage 2, the stitched review).

Report-only for now: the build fails on it once the valley is fixed (rules, section 8).
"""
from __future__ import annotations

import json
import os
from collections import deque

from PIL import Image, ImageDraw

from materials import MATERIALS, P

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
W, H, CELL = 320, 576, 4
COLS, ROWS = W // CELL, H // CELL

# Placement types (rules, section 2); anything not listed is a ground prop.
FLOATING = {'boat_blue', 'boat_red', 'sailboat', 'narrowboat', 'ferry', 'buoy', 'lily_pads', 'duck', 'swan'}
WET = {'reeds', 'heron', 'net_rack', 'upturned_boat', 'driftwood', 'papyrus', 'water_crane', 'canal_crane'}
SUPPORTED = {'lighthouse', 'water_mill', 'tether', 'shaduf', 'bridge', 'basalt_bridge'}
_rgb = lambda c: tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))  # noqa: E731
PATH_COLOURS = {_rgb(c) for c in P[1:5]}  # P[1]: a path in shade
WATER_COLOURS = {_rgb(c) for c in MATERIALS['water']}  # foam and glints included


def _bluish(r, g, b):
    return b >= r + 18 and b >= g - 6 and r < 150


def _lava(r, g, b):
    return r >= 170 and g <= 160 and b <= 90 and r - g >= 50


def classify(ground: Image.Image, blocked: set) -> list[str]:
    """One character per walk cell: '~' water, '!' lava, '^' wall/cliff/other blocked,
    '=' path, '.' ground (the majority of the cell's pixels decides)."""
    px = ground.load()
    rows = []
    for cy in range(ROWS):
        row = []
        for cx in range(COLS):
            votes = {}
            for dy in range(CELL):
                for dx in range(CELL):
                    x, y = cx * CELL + dx, cy * CELL + dy
                    r, g, b, _a = px[x, y]
                    # water and lava are what you cannot walk into: a blue puddle on a
                    # pavement or an orange floor is ground (rules, section 1)
                    if (x, y) in blocked and _lava(r, g, b):
                        k = '!'
                    elif (x, y) in blocked and (_bluish(r, g, b) or (r, g, b) in WATER_COLOURS):
                        k = '~'
                    elif (x, y) in blocked:
                        k = '^'
                    elif (r, g, b) in PATH_COLOURS:
                        k = '='
                    else:
                        k = '.'
                    votes[k] = votes.get(k, 0) + 1
            row.append(max(votes, key=lambda k: (votes[k], k == '~')))
        rows.append(''.join(row))
    return rows


# Things that stand on a trunk or a post: only the middle of the sprite touches the
# ground (a willow's crown may hang over the water; its trunk may not stand in it).
TRUNKED = ('tree', 'pine', 'willow', 'acacia', 'palm', 'snag', 'lamp', 'light', 'pole', 'post')


def _foot_cells(x, y, w, h, key):
    if any(t in key for t in TRUNKED):
        x, w = x + w * 3 // 8, max(4, w // 4)
        foot = 8
    else:
        foot = 20 if w > 60 else 6
    return [(cx, cy) for cy in range((y + h - foot) // CELL, (y + h) // CELL)
            for cx in range((x + 1) // CELL, max((x + 1) // CELL + 1, (x + w - 1) // CELL))
            if 0 <= cx < COLS and 0 <= cy < ROWS]


def check_props(name, terrain, objects, sprites, overhead):
    out = []
    for (oid, key, x, y) in objects:
        if key in overhead or key in SUPPORTED:
            continue
        sp = sprites[key]
        cells = _foot_cells(x, y, sp.w, sp.h, key)
        if not cells:
            continue
        wet = sum(terrain[cy][cx] in '~' for (cx, cy) in cells) / len(cells)
        hot = sum(terrain[cy][cx] == '!' for (cx, cy) in cells) / len(cells)
        box = (x, y, sp.w, sp.h)
        if key in FLOATING:
            if wet < 0.5:
                out.append((name, 'floating-on-land', oid, box, f'{key} floats, but stands on land'))
        elif key in WET:
            continue
        elif wet > 0.34:
            out.append((name, 'ground-on-water', oid, box, f'{key} stands in water'))
        elif hot > 0.2:
            out.append((name, 'ground-on-lava', oid, box, f'{key} stands in lava'))
    return out


def _edge(terrain, side, depth=3):
    """The classes along a border, each position the set of classes in the first
    `depth` cells in from it (a path shaded at the very edge still counts)."""
    if side == 'north':
        rows = terrain[:depth]
        return [set(col) for col in zip(*rows)]
    if side == 'south':
        rows = terrain[-depth:]
        return [set(col) for col in zip(*rows)]
    if side == 'west':
        return [set(r[:depth]) for r in terrain]
    return [set(r[-depth:]) for r in terrain]


# A shore or a path edge that crosses a border at a slant is off by a cell or three
# where it meets; a run must be 16 px or longer to be a seam.
MIN_RUN = 4


def _runs(a, b, want):
    """Stretches along an edge where one side has `want` and the other has not."""
    out, start = [], None
    for i, (p, q) in enumerate(zip(a, b)):
        bad = bool(p & set(want)) != bool(q & set(want))
        if bad and start is None:
            start = i
        if not bad and start is not None:
            if i - start >= MIN_RUN:
                out.append((start, i))
            start = None
    if start is not None and len(a) - start >= MIN_RUN:
        out.append((start, len(a)))
    return out


def _strip_tone(ground, terrain, side):
    """Mean colour of the 6 px nearest the edge, over plain ground cells only."""
    px = ground.load()
    tot, n = [0, 0, 0], 0
    if side in ('north', 'south'):
        ys = range(0, 6) if side == 'north' else range(H - 6, H)
        for x in range(W):
            if terrain[0 if side == 'north' else ROWS - 1][x // CELL] != '.':
                continue
            for y in ys:
                r, g, b, _ = px[x, y]
                tot[0] += r; tot[1] += g; tot[2] += b; n += 1
    else:
        xs = range(0, 6) if side == 'west' else range(W - 6, W)
        for y in range(H):
            if terrain[y // CELL][0 if side == 'west' else COLS - 1] != '.':
                continue
            for x in xs:
                r, g, b, _ = px[x, y]
                tot[0] += r; tot[1] += g; tot[2] += b; n += 1
    return [t / n for t in tot] if n > 200 else None


def check_borders(region, layout, zones):
    out = []
    for a, (ca, ra) in layout.items():
        for b, (cb, rb) in layout.items():
            if (cb, rb) == (ca + 1, ra):
                sa, sb, horizontal = 'east', 'west', False
            elif (cb, rb) == (ca, ra + 1):
                sa, sb, horizontal = 'south', 'north', True
            else:
                continue
            if a not in zones or b not in zones:
                continue
            ea, eb = _edge(zones[a]['terrain'], sa), _edge(zones[b]['terrain'], sb)
            for (want, kind, what) in (('~', 'seam-water', 'water'), ('=', 'seam-path', 'a path'),
                                       ('!', 'seam-lava', 'lava')):
                for (i0, i1) in _runs(ea, eb, want):
                    span = (i0 * CELL, i1 * CELL)
                    out.append((a, kind, f'{a}|{b}', (sa, span), f'{what} stops at the {sa} border with {b} ({span[0]}-{span[1]} px)'))
            ta, tb = _strip_tone(zones[a]['ground'], zones[a]['terrain'], sa), _strip_tone(zones[b]['ground'], zones[b]['terrain'], sb)
            if ta and tb:
                d = sum(abs(x - y) for x, y in zip(ta, tb)) / 3
                if os.environ.get('LINT_DEBUG'):
                    print(f'  tone {a}|{b} {d:.1f}')
                if d > 14:
                    out.append((a, 'seam-tone', f'{a}|{b}', (sa, (0, W if horizontal else H)),
                                f'the ground changes tone at the {sa} border with {b} (mean difference {d:.0f})'))
    return out


def check_paths(name, terrain, stands, objects, sprites, exits):
    """A path component must reach a zone edge (an exit) or a node: a stand, or within
    a few cells of a prop (a door, a bench, a stall)."""
    out = []
    seen = set()
    near_prop = set()
    for (_oid, key, x, y) in objects:
        sp = sprites[key]
        for cy in range((y + sp.h - 10) // CELL, (y + sp.h + 12) // CELL):
            for cx in range((x - 8) // CELL, (x + sp.w + 8) // CELL):
                near_prop.add((cx, cy))
    nodes = {(sx // CELL, sy // CELL) for (sx, sy) in stands.values()}
    for cy in range(ROWS):
        for cx in range(COLS):
            if terrain[cy][cx] != '=' or (cx, cy) in seen:
                continue
            comp, q = [], deque([(cx, cy)])
            seen.add((cx, cy))
            while q:
                c = q.popleft()
                comp.append(c)
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (c[0] + d[0], c[1] + d[1])
                    if 0 <= n[0] < COLS and 0 <= n[1] < ROWS and n not in seen and terrain[n[1]][n[0]] == '=':
                        seen.add(n)
                        q.append(n)
            if len(comp) < 12:
                continue
            at_edge = any(x in (0, COLS - 1) or y in (0, ROWS - 1) for (x, y) in comp)
            at_node = any(c in nodes or c in near_prop for c in comp)
            if not at_edge and not at_node:
                xs, ys = [c[0] for c in comp], [c[1] for c in comp]
                box = (min(xs) * CELL, min(ys) * CELL, (max(xs) - min(xs) + 1) * CELL, (max(ys) - min(ys) + 1) * CELL)
                out.append((name, 'path-to-nowhere', f'path@{box[0]},{box[1]}', box, 'a path that reaches no exit and no place'))
    return out


def garden_zone():
    """The home garden, drawn by garden.py: its ground plus its water overlays."""
    g = Image.open(os.path.join(ROOT, 'assets', 'garden', 'ground.png')).convert('RGBA').resize((W, H), Image.NEAREST)
    for (name, x, y) in (('water-stream-0', 0, 282), ('water-pond-0', 22, 186)):
        try:
            o = Image.open(os.path.join(ROOT, 'assets', 'garden', f'{name}.png')).convert('RGBA')
            o = o.resize((o.width // 4, o.height // 4), Image.NEAREST)
            g.alpha_composite(o, (x, y))
        except FileNotFoundError:
            pass
    blocked = {(x, y) for x in range(W) for y in range(H) if _bluish(*g.getpixel((x, y))[:3])}
    return {'ground': g, 'terrain': classify(g, blocked)}


def run(built: dict, layout: dict, sprites_of, overhead, previews: dict | None = None):
    zones = {}
    violations = []
    for name, z in built.items():
        ground = z['ground_img']
        terrain = classify(ground, z['blocked'])
        zones[name] = {'ground': ground, 'terrain': terrain}
        z['terrain'] = terrain
        violations += check_props(name, terrain, z['objects'], z['sprites'], overhead)
        violations += check_paths(name, terrain, z['stands'], z['objects'], z['sprites'], None)
    zones['garden'] = garden_zone()
    for region, places in layout.items():
        violations += check_borders(region, places, zones)
    kinds = {}
    for v in violations:
        kinds[v[1]] = kinds.get(v[1], 0) + 1
    print('world lint:', len(violations), 'findings', json.dumps(kinds))
    out = os.environ.get('LINT_OUT')
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'world-lint.txt'), 'w') as f:
            for v in sorted(violations):
                f.write(f'{v[0]:10} {v[1]:18} {v[2]:16} {v[4]}\n')
        if previews is not None:
            _stitch(out, layout, previews, zones, violations)
    return violations


def _stitch(out, layout, previews, zones, violations):
    for region, places in layout.items():
        cols = [c for c, _r in places.values()]
        rows = [r for _c, r in places.values()]
        c0, r0 = min(cols), min(rows)
        img = Image.new('RGBA', ((max(cols) - c0 + 1) * W, (max(rows) - r0 + 1) * H), (30, 25, 23, 255))
        for z, (c, r) in places.items():
            src = previews.get(z) or (zones[z]['ground'] if z in zones else None)
            if src is not None:
                img.alpha_composite(src.convert('RGBA'), ((c - c0) * W, (r - r0) * H))
        d = ImageDraw.Draw(img)
        for (zone, kind, _oid, box, _msg) in violations:
            if zone not in places:
                continue
            ox, oy = (places[zone][0] - c0) * W, (places[zone][1] - r0) * H
            if kind.startswith('seam'):
                side, (a, b) = box
                if side == 'east':
                    d.rectangle([ox + W - 3, oy + a, ox + W + 2, oy + b], outline=(255, 40, 40, 255), width=2)
                else:
                    d.rectangle([ox + a, oy + H - 3, ox + b, oy + H + 2], outline=(255, 40, 40, 255), width=2)
            else:
                x, y, w, h = box
                d.rectangle([ox + x, oy + y, ox + x + w, oy + y + h], outline=(255, 40, 40, 255), width=2)
        img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(os.path.join(out, f'region-{region}.png'))

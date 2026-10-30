"""Lay a zone plan on the soft grid (Matt, 26 Oct 10:42: "following the soft grid should also make
world design and placement easier"; eastward-edges.md 1).

The cell is 8 world px (24 art px at density 3). Structures are whole cells with their outlines on
cell lines: buildings, beds, the paved square, lots, places, roads and paths (centre lines on cell
lines, widths whole cells). The terrain (tiers, faces, retaining walls, the gate stair) comes from
the region plan and its cliff core, which snaps it already (eastward-edges.md 1.6); it is left
as it is here. Props stand on a
cell: their foot (the middle of their footprint's south edge) on a half-cell column (x a multiple
of 4) and a cell row (y a multiple of 8). Clutter (rubble, debris, a fire in a forge, smoke over a
crater, boards nailed over a door) may sit anywhere in a cell.

    python3 -m scripts.art.grid_snap --check            # every plan on the grid (exit 1 if not)
    python3 -m scripts.art.grid_snap --write crossroads # snap game/data/plans/crossroads.json
    python3 -m scripts.art.grid_snap --write woodland   # snap art/scenes/woodland.json

A building's door and its things move with it. The scene gate's twin is scene.check_grid
(logic.off_grid), on the zone's sprites.
"""
from __future__ import annotations

import argparse
import math
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CELL = 8.0
HALF = 4.0
CLUTTER = {'rubble', 'debris', 'glow', 'smoke', 'boards'}
PLANS = {'crossroads': os.path.join(ROOT, 'game', 'data', 'plans', 'crossroads.json'),
         'woodland': os.path.join(ROOT, 'art', 'scenes', 'woodland.json')}


def r8(v):
    return float(math.floor(v / CELL + 0.5) * CELL)


def r4(v):
    return float(math.floor(v / HALF + 0.5) * HALF)


def num(v):
    return int(v) if float(v).is_integer() else v


def snap_rect(r):
    x0, y0 = r8(r[0]), r8(r[1])
    x1, y1 = r8(r[0] + r[2]), r8(r[1] + r[3])
    return [num(x0), num(y0), num(max(CELL, x1 - x0)), num(max(CELL, y1 - y0))]


def snap_foot_rect(r):
    """A prop's footprint moved so its foot stands on the grid (its size kept)."""
    x, y, w, h = r
    fx, fy = x + w / 2.0, y + h
    dx, dy = r4(fx) - fx, r8(fy) - fy
    return [num(x + dx), num(y + dy), num(w), num(h)]


def snap_crossroads(p):
    moved = {}
    for b in p.get('buildings', []):
        old = list(b['rect'])
        b['rect'] = snap_rect(old)
        dx, dy = b['rect'][0] - old[0], (b['rect'][1] + b['rect'][3]) - (old[1] + old[3])
        if 'door' in b:
            b['door'] = [num(r4(b['door'][0] + dx)), num(b['rect'][1] + b['rect'][3])]
        moved[b['id']] = (dx, dy)
    for pr in p.get('props', []):
        if pr['kind'] in CLUTTER:
            continue
        pr['rect'] = snap_rect(pr['rect']) if pr['kind'] in ('beds',) else snap_foot_rect(pr['rect'])
    for t in p.get('things', []):
        t['at'] = [num(r4(t['at'][0])), num(r8(t['at'][1]))]
    art = p.get('art', {})
    for d in art.get('dressing', []):
        if d['kind'] in CLUTTER:
            continue
        d['at'] = [num(r4(d['at'][0])), num(r8(d['at'][1]))]
    for key in ('paving', 'uplands'):
        art[key] = [snap_rect(r) for r in art.get(key, [])]
    art['setts'] = [[num(r4(s[0])), num(r4(s[1])), s[2], s[3]] for s in art.get('setts', [])]
    for pl in p.get('places', []):
        pl['rect'] = snap_rect(pl['rect'])
    for lot in p.get('lots', []):
        lot['rect'] = snap_rect(lot['rect'])
    for r in p.get('routes', []):
        r['points'] = [[num(r8(x)), num(r8(y))] for x, y in r['points']]
        r['width'] = num(max(CELL, r8(r.get('width', 24))))
    return p


def snap_woodland(p):
    out = []
    for o in p['objects']:
        oid, kind, x, y, w, h = o
        nx, ny, _w, _h = snap_foot_rect([x, y, w, h])
        out.append([oid, kind, nx, ny, w, h])
    p['objects'] = out
    for pa in p.get('paths', []):
        pa['points'] = [[num(r8(x)), num(r8(y))] for x, y in pa['points']]
        pa['radius'] = num(max(HALF, r4(pa['radius'])))
    return p


def off_grid(name, p) -> list[str]:
    bad = []
    if name == 'crossroads':
        for b in p.get('buildings', []):
            if snap_rect(b['rect']) != b['rect']:
                bad.append(f'building {b["id"]} {b["rect"]}')
        for pr in p.get('props', []):
            if pr['kind'] in CLUTTER:
                continue
            want = snap_rect(pr['rect']) if pr['kind'] == 'beds' else snap_foot_rect(pr['rect'])
            if want != pr['rect']:
                bad.append(f'prop {pr["id"]} {pr["rect"]}')
        for d in p.get('art', {}).get('dressing', []):
            if d['kind'] not in CLUTTER and (d['at'][0] % HALF or d['at'][1] % CELL):
                bad.append(f'dressing {d["kind"]} at {d["at"]}')
        for r in p.get('routes', []):
            if any(x % CELL or y % CELL for x, y in r['points']) or r.get('width', 24) % CELL:
                bad.append(f'route {r["id"]}')
        for key in ('paving',):
            for r in p.get('art', {}).get(key, []):
                if snap_rect(r) != r:
                    bad.append(f'{key} {r}')
        # raised ground (the soft grid, 26 Oct): a plateau's plan is whole cells
        for lg in p.get('art', {}).get('ledges', []):
            for r in lg['top']:
                if any(v % CELL for v in r):
                    bad.append(f'ledge top {r}')
            if lg.get('face', 12) % 2:
                bad.append(f'ledge face {lg.get("face")}')
    else:
        for oid, kind, x, y, w, h in p['objects']:
            if (x + w / 2.0) % HALF or (y + h) % CELL:
                bad.append(f'object {oid} foot ({x + w / 2.0}, {y + h})')
        for pa in p.get('paths', []):
            if any(x % CELL or y % CELL for x, y in pa['points']):
                bad.append(f'path {pa["points"]}')
    return bad


def dumps_rows(o, ind=1, lvl=0) -> str:
    """JSON with every list of plain values on one line (the scene plans' own layout)."""
    sp = ' ' * ind
    if isinstance(o, dict):
        if not o:
            return '{}'
        return '{\n' + ',\n'.join(f'{sp * (lvl + 1)}{json.dumps(k, ensure_ascii=False)}: {dumps_rows(v, ind, lvl + 1)}'
                                   for k, v in o.items()) + '\n' + sp * lvl + '}'
    if isinstance(o, list):
        if all(not isinstance(v, (dict, list)) for v in o):
            return json.dumps(o, ensure_ascii=False)
        return '[\n' + ',\n'.join(sp * (lvl + 1) + dumps_rows(v, ind, lvl + 1) for v in o) + '\n' + sp * lvl + ']'
    return json.dumps(o, ensure_ascii=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--write', choices=sorted(PLANS))
    a = ap.parse_args(argv)
    if a.write:
        p = json.load(open(PLANS[a.write]))
        p = snap_crossroads(p) if a.write == 'crossroads' else snap_woodland(p)
        text = json.dumps(p, indent=2, ensure_ascii=False) if a.write == 'crossroads' else dumps_rows(p)
        open(PLANS[a.write], 'w').write(text + '\n')
        print(f'snapped {PLANS[a.write]}')
    bad = []
    for name, path in PLANS.items():
        b = off_grid(name, json.load(open(path)))
        bad += [f'{name}: {x}' for x in b]
    print(f'[grid] {len(PLANS)} plans: {"ok" if not bad else str(len(bad)) + " off the soft grid"}')
    for x in bad[:40]:
        print('  OFF GRID:', x)
    return 1 if (bad and a.check) else 0


if __name__ == '__main__':
    sys.exit(main())

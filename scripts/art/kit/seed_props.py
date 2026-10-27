"""Seed the piece library with the woodland's and Crossroads' props and structures.

    python3 -m scripts.art.kit.seed_props [--force]

One piece per drawn design (`game/kit/pieces/<prop|structure>/<zone>_<kind>.json`), from what the
zones already know: the sprite's size, the foot and solid box in their kit.json, the stage
condition, the plan's restores. Everything a person must decide (the ground-rules role and its
relations, composition, story links not in the data) is listed in `audit.todo`; every seeded piece
is a `candidate` until it passes the library gate. An existing piece file is kept unless --force,
so edits made after seeding are never overwritten. Codex work package W1 completes this.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

from PIL import Image

from scripts.art.kit.schema import PIECES, ROOT, errors, load_schema

CELL_W = 8.0      # world px
D = 3             # texels per world px
STRUCT = ('building',)
SKIP = ('shadow', 'glow', 'smoke', 'damage')     # parts of another piece (its shadow, its overlay)

# what the ground rules and the plans say about some kinds (ground-rules.md 6), the rest is todo
ROLE = {
    'bench': ('seat', [{'rel': 'adjacent', 'what': 'route_edge', 'cells': 2, 'facing': True}],
              [{'rel': 'on', 'what': 'route'}, {'rel': 'on', 'what': 'water'}], {'verb': 'sit'}),
    'forest_bench': ('seat', [{'rel': 'adjacent', 'what': 'route_edge', 'cells': 2, 'facing': True}],
                     [{'rel': 'on', 'what': 'route'}, {'rel': 'on', 'what': 'water'}], {'verb': 'sit'}),
    'kit_lantern': ('light', [{'rel': 'at_edge', 'what': 'route', 'cells': 1}], [{'rel': 'on', 'what': 'route'}], None),
    'lantern': ('light', [{'rel': 'at_edge', 'what': 'route', 'cells': 1}], [{'rel': 'on', 'what': 'route'}], None),
    'lantern_lit': ('light', [{'rel': 'at_edge', 'what': 'route', 'cells': 1}], [{'rel': 'on', 'what': 'route'}], None),
    'well': ('centrepiece', [], [{'rel': 'on', 'what': 'route'}], {'verb': 'use'}),
    'well_choked': ('centrepiece', [], [{'rel': 'on', 'what': 'route'}], {'verb': 'look'}),
    'anvil': ('workplace', [{'rel': 'near', 'what': 'forge', 'cells': 3}], [{'rel': 'on', 'what': 'route'}], {'verb': 'forge'}),
    'notice_board': ('marker', [{'rel': 'at_edge', 'what': 'route', 'cells': 1}], [{'rel': 'on', 'what': 'route'}], {'verb': 'read'}),
    'waystone': ('marker', [{'rel': 'at_edge', 'what': 'route', 'cells': 2}], [], {'verb': 'read'}),
    'debris': ('clutter', [], [{'rel': 'on', 'what': 'water'}], None),
    'rubble': ('clutter', [], [{'rel': 'on', 'what': 'water'}], None),
    'boulder': ('rock', [], [{'rel': 'not_overlap', 'what': 'rock'}, {'rel': 'on', 'what': 'route'}], None),
    'standing_stone': ('rock', [], [{'rel': 'on', 'what': 'route'}], None),
    'oak': ('tree', [], [{'rel': 'on', 'what': 'route'}, {'rel': 'on', 'what': 'water'}], None),
}
OWNER = {'anvil': 'hale', 'stall': 'moss'}
LIGHTS = {'lantern_lit': {'radius': 40.0, 'colour': 'lamp', 'flicker': 0.1, 'when': 'night'},
          'kit_lantern': {'radius': 40.0, 'colour': 'lamp', 'flicker': 0.1, 'when': 'night'}}


def _base(kind: str) -> str:
    return re.sub(r'_\d+$', '', kind)


def _size(png: str):
    im = Image.open(png)
    bb = im.getbbox() if im.mode == 'RGBA' else None
    return im.size, bb


def _piece(zone, kind, pngs, foot_px, solid_world, cond, plan, structure=False, at=None):
    base = _base(kind)
    pid = '%s_%s' % (zone, re.sub(r'[^a-z0-9_]', '_', base.lower()))
    (w, h), _bb = _size(pngs[0])
    role = ROLE.get(base) or ROLE.get(base.split('_')[0])
    todo = []
    placement = {'snap': 'cell' if role is None or role[0] not in ('clutter',) else 'free'}
    if role:
        placement['role'] = role[0]
        if role[1]:
            placement['requires'] = role[1]
        if role[2]:
            placement['forbids'] = role[2]
    else:
        todo.append('placement.role, requires and forbids (ground-rules.md 6)')
    todo.append('composition role and clearance')
    geom = {'size_px': [w, h], 'size_cells': [max(1, round(w / D / CELL_W)), max(1, round(h / D / CELL_W))],
            'z_sort': 'foot'}
    if foot_px is not None:
        geom['foot'] = [float(foot_px[0]), float(foot_px[1])]
    if solid_world and at is not None:
        # the solid box relative to the foot (world px), and the cells it covers relative to the
        # foot's cell (a cell is covered when the box takes at least half of it)
        fx, fy = at
        sx, sy, sw, sh = solid_world
        geom['collision'] = {'shape': 'rect', 'rect': [round(sx - fx, 2), round(sy - fy, 2), float(sw), float(sh)]}
        c0x, c0y = int(fx // CELL_W), int(fy // CELL_W)
        cells = []
        for cy in range(int(sy // CELL_W), int((sy + sh - 1e-6) // CELL_W) + 1):
            for cx in range(int(sx // CELL_W), int((sx + sw - 1e-6) // CELL_W) + 1):
                ox = max(0.0, min(sx + sw, (cx + 1) * CELL_W) - max(sx, cx * CELL_W))
                oy = max(0.0, min(sy + sh, (cy + 1) * CELL_W) - max(sy, cy * CELL_W))
                if ox * oy >= CELL_W * CELL_W / 2:
                    cells.append([cx - c0x, cy - c0y])
        geom['footprint'] = cells
    else:
        geom['collision'] = {'shape': 'none'}
    stages = []
    if cond:
        if cond.get('not_restored') or cond.get('not_flags'):
            stages.append('broken')
        if cond.get('restored') or cond.get('flags'):
            stages.append('restored')
    if stages:
        placement['stages'] = stages
    func = {}
    if role and role[3]:
        func['interact'] = dict(role[3], triggers=[])
        todo.append('function.interact.triggers (what using it does)')
    restores = [r for r in plan.get('restores', []) if r.get('id') and r['id'] in pid] if plan else []
    if restores:
        func['saves'] = ['village.restored.%s' % r['id'] for r in restores]
    piece = {
        'schema': 'napattack.piece/1',
        'id': pid,
        'name': base.replace('_', ' ').capitalize(),
        'kind': 'structure' if structure else 'prop',
        'biomes': ['woodland'] if zone == 'woodland' else ['village'],
        'version': 1,
        'variants': [{'id': os.path.splitext(os.path.basename(p))[0], 'weight': 1.0,
                      'png': 'res://' + os.path.relpath(p, os.path.join(ROOT, 'game'))} for p in pngs],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': None,
                     'note': 'seeded from game/zones/%s (art/catalogue holds its asset-gate record)' % zone},
        'geometry': geom,
        'placement': placement,
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': True},
        'function': func,
        'story': {'owner': OWNER.get(base)},
        'gameplay': {'blocks_move': bool(solid_world), 'blocks_shots': bool(solid_world) and structure},
        'audit': {'size_class': None, 'eastward_ref': None, 'seeded_from': 'game/zones/%s/kit.json' % zone, 'todo': todo},
    }
    if base in LIGHTS:
        piece['rendering']['light'] = LIGHTS[base]
    return piece


def seed() -> list:
    out = []
    # the woodland: [id, kind, foot x, foot y, w, h] in world px; sprites padded so the foot is the
    # middle of the bottom edge (review-agents.md)
    wk = json.load(open(os.path.join(ROOT, 'game', 'zones', 'woodland', 'kit.json')))
    seen = {}
    for o in wk['objects']:
        kind = o[1]
        png = os.path.join(ROOT, 'game', 'zones', 'woodland', 'art', kind + '.png')
        if not os.path.exists(png):
            continue
        seen.setdefault(_base(kind), []).append(png)
    for base, pngs in seen.items():
        pngs = sorted(set(pngs))
        w, h = Image.open(pngs[0]).size
        out.append(_piece('woodland', base, pngs, (w / 2.0, float(h)), None, None, None))
    # Crossroads: objects with png, foot and offset in texels, solid in world px
    ck = json.load(open(os.path.join(ROOT, 'game', 'zones', 'crossroads', 'kit.json')))
    plan = json.load(open(os.path.join(ROOT, 'game', 'data', 'plans', 'crossroads.json')))
    groups = {}
    for o in ck['objects']:
        if not o.get('png') or o['kind'] in SKIP:
            continue
        groups.setdefault((o['kind'], _base(os.path.splitext(o['png'])[0])), []).append(o)
    for (kind, base), objs in groups.items():
        pngs = sorted({os.path.join(ROOT, 'game', 'zones', 'crossroads', 'art', o['png']) for o in objs})
        o = objs[0]
        foot = [-o['offset'][0], -o['offset'][1]] if o.get('offset') else None
        at = (o['foot'][0] / D, o['foot'][1] / D) if o.get('foot') else None
        out.append(_piece('crossroads', base, pngs, foot, o.get('solid'), o.get('cond'), plan, structure=kind in STRUCT, at=at))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    schema = load_schema()
    n = 0
    for p in seed():
        e = errors(p, schema)
        if e:
            print(p['id'], e)
            return 1
        d = os.path.join(PIECES, p['kind'])
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, p['id'] + '.json')
        if os.path.exists(path) and not a.force:
            continue
        json.dump(p, open(path, 'w'), indent=1)
        open(path, 'a').write('\n')
        n += 1
    print('seeded %d pieces' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())

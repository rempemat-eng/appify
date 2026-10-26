"""Hold the biome briefs (scripts/art/biomes/<id>.json, status 'brief') to what the kit will need:
every family they name is a house ramp and is in the brief's own `families`, every edge set it
says is in the cliff core is there (and belongs to this biome or is shared by name), and every
variant uses only ground kinds and edge sets the brief defines.

The shape follows the kit's reference biome, meadow.json (#215): `families` is one flat list of
house ramps, and a material's own families sit under `materials.<name>.families`.

    python3 scripts/art/biomes/check_briefs.py

Claude C, 21 Oct. Data only: nothing here paints (to-all-kit-freeze).
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'art'))


def families_in(node, out):
    """Every family named under a `families` key below node."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == 'families' and isinstance(v, list):
                out.update(v)
            else:
                families_in(v, out)
    elif isinstance(node, list):
        for v in node:
            families_in(v, out)
    return out


def check(path: str, ramps: set, edge_sets: dict) -> list:
    b = json.load(open(path))
    bid = b['id']
    out = []
    if not isinstance(b.get('families'), list):
        return [f'{bid}: families must be a list of house ramps, as in meadow.json (roles go under materials)']
    own = set(b['families'])
    for f in sorted(own - ramps):
        out.append(f'{bid}: family {f!r} is not a house ramp')
    named = families_in({k: v for k, v in b.items() if k != 'families'}, set())
    for f in sorted(named - own):
        out.append(f'{bid}: names family {f!r} outside its families list')
    for name, e in b.get('edge_sets', {}).items():
        if e.get('status') == 'in cliff core':
            if name not in edge_sets:
                out.append(f'{bid}: edge set {name!r} said to be in the cliff core, which has no such set')
            elif edge_sets[name]['biome'] != bid:
                out.append(f'{bid}: edge set {name!r} belongs to {edge_sets[name]["biome"]}')
    kinds = set(b.get('ground', {})) - {'_about'}
    for vid, v in b.get('variants', {}).items():
        if vid == '_about':
            continue
        for e in v.get('edges', []):
            if e not in b.get('edge_sets', {}):
                out.append(f'{bid}: variant {vid} uses edge set {e!r} the brief does not define')
        for g in v.get('ground', []):
            if g.split(' ')[0] not in kinds:
                out.append(f'{bid}: variant {vid} uses ground {g!r} the brief does not define')
    return out


def main() -> int:
    pal = json.load(open(os.path.join(ROOT, 'art', 'house-palette.json')))
    import cliff_core
    faults = []
    paths = sorted(glob.glob(os.path.join(HERE, '*.json')))
    for p in paths:
        b = json.load(open(p))
        if b.get('status') == 'brief' and b.get('owner') == 'claude-c':   # other lanes' briefs keep their own shapes
            faults += check(p, set(pal['ramps']), cliff_core.EDGE_SETS)
    for f in faults:
        print('FAULT', f)
    print(f'biome briefs (lane C): {len(faults)} faults')
    return 1 if faults else 0


if __name__ == '__main__':
    sys.exit(main())

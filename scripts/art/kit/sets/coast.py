"""The coast's ground for Act 1's Driftwood quay (docs/vision/props-backlog.md, the Act 1 set):
shingle and quay stone, added to the kit as new materials, as the moor was (scripts/art/kit/sets/
moor.py). Both bake natively through the kit's earth painter (scripts/art/native/softground.dirt),
so no zone's bake hash moves and no post-pass is needed:

- **shingle**: rounded pebbles in grey, buff and slate, packed small (clods of 6 texels, many
  stones), the beach between the quay and the sea;
- **quay**: dressed granite setts on the quay's top (clods of 15 texels, few loose stones); walkable
  hard-standing, not a route (kit_rules holds routes back from water unless a deck spans it, and a
  quay meets the water by design).

Their transitions: lawn over shingle and over quay (the turf's lip), shingle and quay over water (a
bank), path over quay and shingle over quay (plain).

    python3 -m scripts.art.kit.sets.coast --force     # write the terrain and transition pieces
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from scripts.art.kit.schema import PIECES

STANDARD = "eastward-edges.md 5.1 and 5.5, art-style.md density 3; Driftwood Harbour's brief (world-atlas.md)"
BIOMES = ['coast']


def _terrain(mid, name, mat_id, priority, surface, route, fill, paint, nav, note):
    return {
        'schema': 'napattack.piece/1', 'id': mid, 'name': name, 'kind': 'terrain', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'terrain': {'material_id': mat_id, 'priority': priority,
                    'fill': {'module': 'scripts.art.kit.fills', 'fn': fill[0], 'args': fill[1]},
                    'walkable': True, 'surface': surface, 'route': route, 'water': None, 'swatch': [96, 96], 'paint': paint},
        'placement': {'snap': 'cell'},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'nav_cost': nav},
        'audit': {'painter': {'module': paint['module'], 'fn': paint['fn'], 'args': paint.get('args', {})}, 'size_class': 'ground',
                  'eastward_ref': 'Eastward 12 (the stepping stones and the stream bed), 22 (the trodden ground); refs local only'},
    }


def _transition(upper, lower, fn, args=None, dressing=None, note=''):
    return {
        'schema': 'napattack.piece/1', 'id': '%s_over_%s' % (upper, lower), 'name': '%s over %s' % (upper.capitalize(), lower),
        'kind': 'transition', 'biomes': list(BIOMES), 'version': 1,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'transition': {'upper': upper, 'lower': lower, 'painter': {'module': 'scripts.art.kit.edges', 'fn': fn, 'args': args or {}},
                       'variants': 1, 'shape': 'lower', 'dressing': dressing},
        'audit': {'painter': {'module': 'scripts.art.kit.edges', 'fn': fn, 'args': args or {}},
                  'eastward_ref': 'Eastward 12 (the stream\'s edge), crops 10-grass-dirt'},
    }


SHINGLE_PAINT = {'module': 'scripts.art.native.softground', 'fn': 'dirt',
                 'args': {'seed': 1501, 'fam': 'stone', 'cell': 6, 'stones': 3.0, 'shape': {'seed': 1502, 'smooth': 2}}}
QUAY_PAINT = {'module': 'scripts.art.native.softground', 'fn': 'dirt',
              'args': {'seed': 1503, 'fam': 'stone', 'cell': 15, 'stones': 0.3, 'shape': {'seed': 1504, 'smooth': 1}}}
LIP = {'density': 0.5, 'south': ['tuft_0', 'tuft_1', 'pebble_0'], 'north': ['blades_0', 'pebble_1', 'pebble_2'],
       'side': ['pebble_0', 'tuft_2']}
WET = {'density': 0.4, 'south': ['pebble_0', 'pebble_2'], 'north': ['pebble_1', 'pebble_3'], 'side': ['pebble_2']}


def pieces():
    t = [
        _terrain('shingle', 'Shingle beach', 11, 17, 'earth', False,
                 ('dirt', {'seed': 1501, 'fam': 'stone', 'cell': 6.0, 'stones': 3.0, 'joints': 0.7, 'lit': 0.5, 'blades': 0.0}),
                 SHINGLE_PAINT, 1.4,
                 'Rounded pebbles packed small in grey, buff and slate: the beach under the quay (softground.dirt).'),
        _terrain('quay', 'Quay setts', 12, 21, 'earth', False,
                 ('dirt', {'seed': 1503, 'fam': 'stone', 'cell': 15.0, 'stones': 0.3, 'joints': 0.9, 'lit': 0.6, 'blades': 0.1}),
                 QUAY_PAINT, 0.8,
                 'Dressed granite setts on the quay\'s top, joints showing (softground.dirt in the stone family).'),
    ]
    tr = [
        _transition('lawn', 'shingle', 'sunken', {'fray': True}, LIP, 'The turf\'s lip over the beach.'),
        _transition('lawn', 'quay', 'sunken', {'fray': True}, LIP, 'The turf meeting the quay\'s setts.'),
        _transition('shingle', 'water', 'bank', {'side_w': 3}, WET, 'The beach running into the sea.'),
        _transition('quay', 'water', 'bank', {'side_w': 3}, WET, 'The quay\'s edge over the water.'),
        _transition('path', 'quay', 'plain', None, None, 'A path joining the quay.'),
        _transition('shingle', 'quay', 'plain', None, None, 'Shingle washed against the quay\'s foot.'),
    ]
    return t, tr


def write_pieces(force=False):
    t, tr = pieces()
    n = 0
    for kind, items in (('terrain', t), ('transition', tr)):
        for pc in items:
            path = os.path.join(PIECES, kind, pc['id'] + '.json')
            if force or not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump(pc, f, indent=1)
                    f.write('\n')
                n += 1
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    print('coast: %d pieces written' % write_pieces(force=a.force))
    return 0


if __name__ == '__main__':
    sys.exit(main())

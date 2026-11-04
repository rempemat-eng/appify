"""Two review studies for the Act 1 set (scripts/art/kit/sets/act1.py), each built only from kit
pieces and checked as a zone (not playable zones):

- **Driftwood quay**: the cliff-top turf and the path down to a quay of setts; the net rack, lobster
  pots and mooring bitts along its edge; a jetty out into the harbour with the harbour light at its
  head; the shingle beach with a boat drawn up on it; buoys on the water;
- **the Halt and the Millrace**: the halt's platform edge along the lane, its shelter, lamps,
  semaphore, timetable board and the churn stand at the lane's end; the leat with its sluice and the
  mill wheel; the landslip across the lane where it nears the race, the fence it broke and the
  miller's spare stones; hives by the lane; Old Fang's barrow on its rise with its kerb stones.

    python3 -m scripts.art.kit.sets.act1_study OUT_DIR [--scale 3]   # coast and valley, baked with every still

The checks are brackens_study's: kit_rules, relations, enclosures, placement_audit.check_plan and
the staging rules (`brackens_study.layout_faults`).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit.schema import ROOT

CELL = 24


def coast() -> dict:
    W, H = 34, 18
    g = np.full((H, W), 'q', '<U1')
    g[0:3, :] = ','                                         # the cliff-top turf
    g[0:3, 15:17] = '#'                                     # the path down to the quay
    g[9:13, 0:19] = 's'                                     # the shingle beach
    g[9:, 19:] = '~'                                        # the harbour
    g[13:, 0:19] = '~'                                      # the sea over the beach's foot
    g[9:14, 26:32] = 'q'                                    # the jetty
    pieces = [
        {'id': 'light', 'piece': 'coast_harbour_light', 'at': [29 * CELL, 14 * CELL]},
        {'id': 'bitt_1', 'piece': 'coast_mooring_bitt', 'at': [20 * CELL + 12, 9 * CELL]},
        {'id': 'bitt_2', 'piece': 'coast_mooring_bitt', 'at': [24 * CELL + 12, 9 * CELL]},
        {'id': 'bitt_3', 'piece': 'coast_mooring_bitt', 'at': [26 * CELL + 12, 12 * CELL]},
        {'id': 'net', 'piece': 'coast_net_rack', 'at': [22 * CELL, 6 * CELL]},
        {'id': 'pots_1', 'piece': 'coast_lobster_pots', 'at': [28 * CELL, 8 * CELL], 'variant': 'a'},
        {'id': 'pots_2', 'piece': 'coast_lobster_pots', 'at': [31 * CELL, 9 * CELL], 'variant': 'b'},
        {'id': 'boat', 'piece': 'coast_boat_beached', 'at': [12 * CELL, 12 * CELL]},
        {'id': 'buoy_1', 'piece': 'coast_buoy', 'at': [22 * CELL + 12, 14 * CELL]},
        {'id': 'buoy_2', 'piece': 'coast_buoy', 'at': [8 * CELL + 12, 16 * CELL]},
        {'id': 'buoy_3', 'piece': 'coast_buoy', 'at': [33 * CELL + 0, 16 * CELL]},
    ]
    return {'zone': 'act1_coast_study', 'note': 'Review study (scripts/art/kit/sets/act1_study.py), not a playable zone.',
            'legend': {',': 'lawn', '#': 'path', 'q': 'quay', 's': 'shingle', '~': 'water'},
            'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def valley() -> dict:
    W, H = 40, 26
    g = np.full((H, W), ',', '<U1')
    g[10:12, 0:25] = '#'                                    # the lane, ending short of the race
    g[3:8, 2:18] = 'w'                                      # the platform's gravel
    g[8:10, 3:5] = '#'                                      # the path up onto the platform
    g[:, 26:29] = '~'                                       # the leat (the Millrace)
    g[12:16, 7:9] = '#'                                     # the trod up to the barrow
    g[12:15, 19:23] = 'w'                                   # the miller's yard, trodden
    pieces = [
        # the halt
        *[{'id': 'edge_%d' % c, 'piece': 'halt_platform_edge', 'at': [c * CELL + 12, 8 * CELL], 'variant': 'a' if c % 3 else 'b'}
          for c in range(5, 17)],
        {'id': 'shelter', 'piece': 'halt_waiting_shelter', 'at': [10 * CELL, 5 * CELL]},
        {'id': 'lamp_1', 'piece': 'halt_platform_lamp', 'at': [6 * CELL + 12, 6 * CELL]},
        {'id': 'lamp_2', 'piece': 'halt_platform_lamp', 'at': [14 * CELL + 12, 6 * CELL]},
        {'id': 'signal', 'piece': 'halt_semaphore', 'at': [18 * CELL + 12, 8 * CELL]},
        {'id': 'timetable', 'piece': 'halt_timetable_board', 'at': [4 * CELL, 13 * CELL]},
        {'id': 'churns', 'piece': 'halt_churn_stand', 'at': [1 * CELL + 12, 10 * CELL]},
        # the Millrace
        {'id': 'sluice', 'piece': 'mill_sluice', 'at': [27 * CELL + 12, 4 * CELL]},
        {'id': 'wheel', 'piece': 'mill_wheel', 'at': [27 * CELL + 12, 12 * CELL]},
        {'id': 'slip', 'piece': 'mill_landslip', 'at': [21 * CELL, 12 * CELL]},
        {'id': 'fence', 'piece': 'mill_fence_broken', 'at': [16 * CELL, 14 * CELL]},
        {'id': 'stones', 'piece': 'mill_millstones', 'at': [21 * CELL, 15 * CELL]},
        # the hives by the lane
        {'id': 'hive', 'piece': 'hive_wbc', 'at': [12 * CELL + 12, 14 * CELL]},
        {'id': 'skep', 'piece': 'hive_skep', 'at': [10 * CELL + 12, 14 * CELL]},
        # Old Fang's barrow and its kerb
        {'id': 'barrow', 'piece': 'barrow_entrance', 'at': [8 * CELL, 21 * CELL]},
        {'id': 'kerb_1', 'piece': 'barrow_kerb', 'at': [2 * CELL + 12, 23 * CELL], 'variant': 'a'},
        {'id': 'kerb_2', 'piece': 'barrow_kerb', 'at': [13 * CELL + 12, 23 * CELL], 'variant': 'b'},
        {'id': 'kerb_3', 'piece': 'barrow_kerb', 'at': [14 * CELL + 12, 20 * CELL], 'variant': 'c'},
    ]
    return {'zone': 'act1_valley_study', 'note': 'Review study (scripts/art/kit/sets/act1_study.py), not a playable zone.',
            'legend': {',': 'lawn', '#': 'path', 'w': 'worn', '~': 'water'},
            'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def plans() -> list:
    return [coast(), valley()]


def faults(p) -> list:
    """Every rule check's faults on a plan, as messages."""
    from scripts.art.kit import enclosures as EN
    from scripts.art.kit import placement_audit as PA
    from scripts.art.kit import relations as RL
    from scripts.art.kit.sets import brackens_study as BS
    from scripts.review import kit_rules as KR
    out = ['kit_rules: ' + f['message'] for f in KR.check_zone(p) if f['severity'] == 'fault']
    out += ['relations: ' + f['message'] for f in RL.check_zone(p)]
    out += ['enclosures: ' + f['message'] for f in EN.check_zone(p, EN.library())]
    out += ['layout: ' + m for m in BS.layout_faults(p)]
    out += ['placement: ' + f['message'] for f in PA.check_plan(p)]
    return out


def render(p) -> Image.Image:
    """The bake of the plan's ground and every piece's still by foot (a loop shows frame 0, the
    reduced-motion picture)."""
    from scripts.art.kit import bake as BK
    from scripts.art.kit import compose as CO
    ground, _ = BK.bake(p)
    img = ground.convert('RGBA')
    idx = CO.piece_index()
    for pc in sorted(p['pieces'], key=lambda q: (q['at'][1], q['at'][0])):
        e = idx[pc['piece']]
        v = e['variants'].get(pc.get('variant')) or next(iter(e['variants'].values()))
        sp = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
        img.alpha_composite(sp, (int(pc['at'][0] - v['foot'][0]), int(pc['at'][1] - v['foot'][1])))
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--scale', type=int, default=1)
    ap.add_argument('--tag', default='')
    a = ap.parse_args(argv)
    for p in plans():
        img = render(p)
        if a.scale > 1:
            img = img.resize((img.width * a.scale, img.height * a.scale), Image.NEAREST)
        path = os.path.join(a.out, '%s_%dx%s.png' % (p['zone'].replace('_study', ''), a.scale, a.tag))
        img.save(path)
        print('wrote', path)
    return 0


if __name__ == '__main__':
    sys.exit(main())

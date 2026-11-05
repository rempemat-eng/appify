"""Two review studies for the Act 1 set (scripts/art/kit/sets/act1.py), each built only from kit
pieces and checked as a zone (not playable zones):

- **Driftwood quay**: the cliff-top turf and the path down to a quay of setts; the net rack, lobster
  pots and mooring bitts along its edge; a jetty out into the harbour with the harbour light at its
  head; the shingle beach with a boat drawn up on it; buoys on the water;
- **the Halt and the Millrace**: the halt's platform (its stone surface and its edge) along the lane,
  its shelter, lamps, semaphore, timetable board and the churn stand at the lane's end; the leat from
  its sluice turning east into the race under the mill's wheel; the landslip across the lane where
  it nears the leat, the fence it broke and the miller's spare stones in his yard; hives by the lane;
  Old Fang's barrow, its trod straight out of the portal to the field path, its kerb round its foot.

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
        {'id': 'pots_1', 'piece': 'coast_lobster_pots', 'at': [27 * CELL, 8 * CELL], 'variant': 'a'},
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
    W, H = 44, 30
    g = np.full((H, W), ',', '<U1')
    g[5:11, 2:20] = 'q'                                     # the platform's surface, stone (the coast's quay setts)
    g[13:15, 0:25] = '#'                                    # the lane, ending short of the leat
    g[11:13, 3:5] = '#'                                     # the path up onto the platform
    g[0:16, 26:29] = '~'                                    # the leat (the Millrace), from its sluice
    g[14:16, 26:40] = '~'                                   # turning east into the mill's race
    tiers = np.zeros((H, W), int)
    tiers[0:10, 20:26] = 1                                  # the hillside the slip came down from, between halt and leat
    g[19:30, 30:32] = '#'                                   # the yard's track to the south
    g[15:29, 2:4] = '#'                                     # the field path from the lane to the barrow
    g[28:30, 2:13] = '#'
    g[27:28, 11:13] = '#'                                   # the trod straight out of the barrow's portal
    pieces = [
        # the halt
        *[{'id': 'edge_%d' % c, 'piece': 'halt_platform_edge', 'at': [c * CELL + 12, 11 * CELL], 'variant': 'a' if c % 3 else 'b'}
          for c in range(5, 18)],
        {'id': 'shelter', 'piece': 'halt_waiting_shelter', 'at': [11 * CELL, 9 * CELL]},
        {'id': 'lamp_1', 'piece': 'halt_platform_lamp', 'at': [6 * CELL + 12, 9 * CELL]},
        {'id': 'lamp_2', 'piece': 'halt_platform_lamp', 'at': [16 * CELL + 12, 9 * CELL]},
        {'id': 'signal', 'piece': 'halt_semaphore', 'at': [19 * CELL + 12, 11 * CELL]},
        {'id': 'timetable', 'piece': 'halt_timetable_board', 'at': [7 * CELL, 16 * CELL]},
        {'id': 'churns', 'piece': 'halt_churn_stand', 'at': [1 * CELL + 12, 13 * CELL]},
        # the Millrace
        {'id': 'sluice', 'piece': 'mill_sluice', 'at': [27 * CELL + 12, 4 * CELL]},
        {'id': 'wheel', 'piece': 'mill_wheel', 'at': [34 * CELL, 15 * CELL]},
        {'id': 'slip', 'piece': 'mill_landslip', 'at': [22 * CELL + 12, 14 * CELL]},
        {'id': 'fence', 'piece': 'mill_fence_broken', 'at': [16 * CELL, 17 * CELL]},
        {'id': 'stones', 'piece': 'mill_millstones', 'at': [33 * CELL, 19 * CELL]},
        # the hives by the lane
        {'id': 'hive', 'piece': 'hive_wbc', 'at': [10 * CELL + 12, 17 * CELL]},
        {'id': 'skep', 'piece': 'hive_skep', 'at': [12 * CELL + 12, 17 * CELL]},
        # Old Fang's barrow, its trod straight out of the portal, its kerb round its foot
        {'id': 'barrow', 'piece': 'barrow_entrance', 'at': [12 * CELL, 27 * CELL]},
        {'id': 'kerb_1', 'piece': 'barrow_kerb', 'at': [4 * CELL + 12, 26 * CELL], 'variant': 'a'},
        {'id': 'kerb_2', 'piece': 'barrow_kerb', 'at': [20 * CELL + 12, 26 * CELL], 'variant': 'b'},
        {'id': 'kerb_3', 'piece': 'barrow_kerb', 'at': [19 * CELL + 12, 23 * CELL], 'variant': 'c'},
    ]
    return {'zone': 'act1_valley_study', 'note': 'Review study (scripts/art/kit/sets/act1_study.py), not a playable zone.',
            'legend': {',': 'lawn', '#': 'path', '~': 'water', 'q': 'quay'}, 'dress': {'quay': 'flags'},
            'rows': [''.join(r) for r in g], 'tiers': [''.join(str(v) for v in r) for r in tiers], 'pieces': pieces, 'decor': []}


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
    from scripts.art.kit.sets import coast as CS
    ground, _ = BK.bake(p)
    img = ground.convert('RGBA')
    if any('q' in r or 's' in r for r in p['rows']) and 'quay' in p['legend'].values():
        plain, _ = BK.bake(dict(p, pieces=[]))
        img = CS.dress(p, ground, plain).convert('RGBA')
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

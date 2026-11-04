"""A village green built only from kit pieces, as a review study (not a playable zone): two lanes
crossing with a fingerpost at the corner, a bakehouse with its woodpile and chopping block at the gable
and its washing in the side yard, a herbalist's and a hut on the green, the pump on the green with a
bench facing it, a pair of market stalls and a notice board at the lane's edge, a cart pulled in, a
wayside shrine and a lantern (docs/vision/placement-logic.md; scripts/art/kit/commons.py).

    python3 -m scripts.art.kit.village_study OUT.png [--scale 3]

Its plan has the kit zones' shape, so the editor's checks read it as they read a zone: kit_rules,
relations, enclosures and placement_audit.check_plan (needs, faces, avoid, points); test_kit keeps
it at 0 faults.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
from PIL import Image

from scripts.art.kit import farm_study as FS

CELL = 24
COLS, ROWS = 44, 30


def plan() -> dict:
    g = np.full((ROWS, COLS), '.', '<U1')
    g[15:17, :] = '#'                                   # the lane east and west
    g[:, 21:23] = '#'                                   # the lane north and south
    # door paths centred on their doors, straight out to the lane (thresholds.py; Matt, 4 Nov)
    g[11:15, 11:14] = '#'                               # the bakehouse's door path
    g[11:15, 35:38] = '#'                               # the herbalist's
    g[17:25, 35:38] = '#'                               # the hut's, up to the green
    g[20:23, 28:35] = 'w'                               # trodden round the pump
    g[19, 26:36] = '#'                                  # the way across the green, before the bench
    pieces = [
        {'id': 'cottage', 'piece': 'crossroads_bakery', 'at': [228, 264]},
        {'id': 'woodpile', 'piece': 'commons_woodpile', 'at': [60, 264]},
        {'id': 'block', 'piece': 'commons_chopping_block', 'at': [108, 312]},
        {'id': 'washing', 'piece': 'commons_washing_line', 'at': [420, 144]},
        {'id': 'herbalist', 'piece': 'crossroads_herbalist', 'at': [804, 264]},
        {'id': 'hut', 'piece': 'crossroads_hut', 'at': [876, 720]},
        {'id': 'fingerpost', 'piece': 'commons_fingerpost_nesw', 'at': [492, 360]},
        {'id': 'lantern', 'piece': 'crossroads_kit_lantern', 'at': [588, 336]},
        {'id': 'pump', 'piece': 'commons_pump', 'at': [684, 552]},
        {'id': 'bench', 'piece': 'commons_bench', 'at': [684, 432], 'facing': 's'},
        {'id': 'stall_1', 'piece': 'commons_stall_produce', 'at': [180, 432]},
        {'id': 'stall_2', 'piece': 'commons_stall_cloth', 'at': [348, 432]},
        {'id': 'notices', 'piece': 'commons_notice_board', 'at': [588, 432]},
        {'id': 'cart', 'piece': 'commons_cart', 'at': [972, 432]},
        {'id': 'shrine', 'piece': 'commons_shrine', 'at': [36, 432]},
    ]
    return {'zone': 'village_study', 'note': 'Review study (scripts/art/kit/village_study.py), not a playable zone.',
            'legend': {'.': 'lawn', '#': 'path', 'w': 'worn'}, 'rows': [''.join(r) for r in g], 'pieces': pieces, 'decor': []}


def layout_faults(p: dict | None = None) -> list:
    """No two placed things drawn over each other (houses may stand behind what is before them:
    only pieces whose feet are within a house's drawn box and behind its foot count)."""
    from scripts.art.kit import build as _B  # noqa: F401
    from scripts.art.kit import compose as CO
    from scripts.art.kit import enclosures as EN
    p = p or plan()
    idx = CO.piece_index()
    lib = EN.library()
    boxes = {pc['id']: FS._opaque_box(pc, idx) for pc in p['pieces']}
    house = {pc['id'] for pc in p['pieces'] if (lib[pc['piece']].get('placement') or {}).get('role') == 'house'}
    out = []

    def hit(r, q, tol=3):
        return r[0] + tol < q[2] and q[0] + tol < r[2] and r[1] + tol < q[3] and q[1] + tol < r[3]
    for a in p['pieces']:
        for b in p['pieces']:
            if a['id'] >= b['id'] or not hit(boxes[a['id']], boxes[b['id']]):
                continue
            if a['id'] in house or b['id'] in house:
                h, o = (a, b) if a['id'] in house else (b, a)
                if o['at'][1] > h['at'][1]:
                    continue                  # before the house: drawn over its wall's foot only
            out.append('%s and %s are drawn over each other' % (a['id'], b['id']))
    return out


def render(p: dict | None = None) -> Image.Image:
    return FS.render(p or plan())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--scale', type=int, default=1)
    a = ap.parse_args(argv)
    img = render()
    if a.scale > 1:
        img = img.resize((img.width * a.scale, img.height * a.scale), Image.NEAREST)
    img.save(a.out)
    print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())

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

**The dressing** (`dress`, as the moor's is: a post-pass over a bake, used by the Act 1 study; a real
zone needs a bake hook, which moves every bake hash, so it waits for the next baked-zone regeneration):
the quay's setts as rectangular blocks 12 x 7 in staggered courses, each lit along its top-left edge
with a dark joint; the shingle as loose rounded pebbles 3 to 6 texels on sand, the larger ones higher
up the beach and in drifts, each lit on its top-left with a dark foot. The bake's lips and banks and
the pieces' shadows stay.

    python3 -m scripts.art.kit.sets.coast --force     # write the terrain and transition pieces
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

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


def _px(mat, h, w):
    return np.repeat(np.repeat(mat, h // mat.shape[0], 0), w // mat.shape[1], 1)


def setts(cv, m, seed=1505, w=12, h=8, joint_t=2.0):
    """Granite setts (or, larger, flags) in courses staggered by half a block, laid as a floor: each
    block one calm tone of its own sibling ramp (now and then a touch lighter or darker), its top edge
    lit, a soft joint (a tone down, not black) along its bottom and right, its corners rounded into the
    joint so the courses read as stones, not as a brick wall."""
    from scripts.art.kit.sets import _common as K
    H, W = cv.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    course = Yg // h
    off = (course % 2) * (w // 2) + (K.vhash(course, 0, seed) * 3).astype(int)
    sx = (Xg + off) // w
    ux = (Xg + off) % w
    uy = Yg % h
    own = np.where(K.vhash(sx, course, seed) > 0.85, 0.6, np.where(K.vhash(sx, course, seed + 1) < 0.12, -0.6, 0.0))
    t = 3.0 + own
    t = np.where((uy == 0) & (ux > 0) & (ux < w - 2), t + 0.8, t)
    jnt = (uy == h - 1) | (ux == w - 1)
    corner = ((uy == 0) | (uy == h - 2)) & ((ux == 0) | (ux == w - 2))
    t = np.where(jnt | corner, joint_t, t)
    K.rpaint(cv, m, [('slate_cool', 'stone', 'stone_warm'), ('stone_cool', 'stone', 'stone'), ('stone_cool', 'stone_warm', 'stone_warm')], t,
             np.clip(K.vhash(sx, course, seed + 2) * 0.999, 0, 0.999))


def shingle(cv, m, seed=1506):
    """Loose shingle on sand: a calm sand base; rounded pebbles 3 to 6 texels in drifts, the larger
    higher up the beach (to the north), each lit on its top-left and dark at its foot, in grey, buff
    and slate."""
    from scripts.art.kit.sets import _common as K
    H, W = cv.shape
    K.rpaint(cv, m, [('sand_cool', 'sand_cool', 'sand'), ('sand_cool', 'sand', 'sand')], 3.0,
             np.clip(K.noise((H, W), np.random.default_rng(seed), 9.0) * 0.999, 0, 0.999))
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    y0, y1 = ys.min(), ys.max()
    drift = K.noise((H, W), np.random.default_rng(seed + 1), 6.0)
    fams = [('slate_cool', 'stone', 'stone_warm'), ('earth_cool', 'sand_cool', 'sand'), ('slate_cool', 'slate', 'slate_warm'),
            ('stone_cool', 'stone_cool', 'stone')]
    Yg, Xg = np.mgrid[0:H, 0:W]
    for gy in range(int(y0), int(y1) + 1, 4):
        for gx in range(0, W, 5):
            j = K.hsh(gx, gy, seed)
            x, y = int(gx + j * 4), int(gy + K.hsh(gy, gx, seed + 1) * 3)
            if not (0 <= y < H and 0 <= x < W) or not m[y, x]:
                continue
            up = 1.0 - (y - y0) / max(1.0, (y1 - y0))
            if drift[y, x] < 0.35 + 0.25 * (1 - up) and K.hsh(x, y, seed + 2) > 0.25:
                continue
            r = 1.4 + 1.6 * up * K.hsh(x, y, seed + 3) + 0.4
            pm = (((Xg - x) / r) ** 2 + ((Yg - y) / (r * 0.75)) ** 2 <= 1.0) & m
            u, v = (Xg - x) / r, (Yg - y) / (r * 0.75)
            t = 3.0 + 1.0 * ((u + v) < -0.4) - 1.2 * ((u + v) > 0.6)
            K.rpaint(cv, pm, [fams[int(K.hsh(x, y, seed + 4) * len(fams)) % len(fams)]], t, 0.0)


def dress(plan, img_with, img_without):
    """The coast's ground over a baked plan (img_with: the bake; img_without: the bake with no pieces,
    whose difference is the pieces' shadows): setts on the quay, shingle on the beach, inside the
    bake's lips; the shadows kept. Returns an RGBA image."""
    from scripts.art.native.palette import to_rgba
    from scripts.art.kit.sets import _common as K
    rows = plan['rows']
    R, Cn = len(rows), len(rows[0])
    h, w = R * K.CELL, Cn * K.CELL
    mat = np.array([[plan['legend'].get(c, '') for c in r] for r in rows])
    mp = _px(mat, h, w)
    base = np.asarray(img_with.convert('RGBA')).copy()
    plain = np.asarray(img_without.convert('RGBA'))
    lum = lambda im: im[..., :3].astype(float) @ np.array([0.3, 0.59, 0.11])   # noqa: E731
    shadow = (np.abs(base[..., :3].astype(int) - plain[..., :3].astype(int)).sum(-1) > 0) & (lum(base) < lum(plain) * 0.95)
    cv = np.full((h, w), -1, np.int32)
    quay = ndi.binary_erosion(mp == 'quay', iterations=3)
    beach = ndi.binary_erosion(mp == 'shingle', iterations=3)
    if (plan.get('dress') or {}).get('quay') == 'flags':
        setts(cv, quay, w=22, h=14)                     # a platform's flags
    else:
        setts(cv, quay)
    shingle(cv, beach)
    rgba = to_rgba(cv)
    m = (cv >= 0) & ~shadow
    base[m] = rgba[m]
    sh = (cv >= 0) & shadow
    base[sh, :3] = (rgba[sh, :3].astype(float) * 0.72).astype(np.uint8)
    return Image.fromarray(base, 'RGBA')


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

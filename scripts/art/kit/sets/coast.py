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


def setts(cv, m, seed=1505, w=12, h=8, joint_t=2.0, irregular=False):
    """Granite setts (or, larger and irregular, flags) laid as a floor: each stone one calm tone in one
    of two siblings at the same tone, the odd one a tone off; a 1-texel lit edge along its top-west
    corner only; a soft joint (a tone down, not black) along its bottom and east. Setts run in
    courses staggered by half a stone; flags (irregular) take courses of their own depth and stones of
    their own length, so no joint lines up with the next course's and the floor never reads as a
    block wall."""
    from scripts.art.kit.sets import _common as K
    H, W = cv.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    if irregular:
        edges_y = [0]
        while edges_y[-1] < H:
            edges_y.append(edges_y[-1] + int(h - 3 + 6 * K.hsh(len(edges_y), seed)))
        ey = np.array(edges_y)
        course = np.searchsorted(ey, Yg, side='right') - 1
        uy = Yg - ey[course]
        hh = ey[course + 1] - ey[course]
        sx = np.zeros((H, W), int)
        ux = np.zeros((H, W), int)
        ww = np.zeros((H, W), int)
        for c in range(len(edges_y) - 1):
            ex = [-int(w * K.hsh(c, seed + 3))]
            while ex[-1] < W:
                ex.append(ex[-1] + int(w * 0.7 + w * 0.7 * K.hsh(c, len(ex), seed + 4)))
            exa = np.array(ex)
            rows = course == c
            k = np.searchsorted(exa, Xg[rows], side='right') - 1
            sx[rows] = k
            ux[rows] = Xg[rows] - exa[k]
            ww[rows] = exa[k + 1] - exa[k]
        last_x, last_y = ux == ww - 1, uy == hh - 1
    else:
        # courses that wander a texel up or down every 8 to 16 texels, so no joint runs ruler-straight
        # (round 3 of the detail audit, R3-12), and setts of their own length (w - 1 to w + 1)
        wander = np.round(1.2 * (K.vhash(Xg // 11, Yg // h, seed + 7) - 0.5) * 2).astype(int)
        yy = Yg + np.clip(wander, -1, 1)
        course = yy // h
        off = (course % 2) * (w // 2) + (K.vhash(course, 0, seed) * 3).astype(int)
        xx = Xg + off
        sx = xx // w
        ux = xx % w
        ww = w - 1 + (K.vhash(sx, course, seed + 8) * 3).astype(int)
        last_x = ux >= ww - 1
        uy = yy % h
        last_y = uy == h - 1
    own = np.where(K.vhash(sx, course, seed) > 0.95, 1.0, np.where(K.vhash(sx, course, seed + 1) < 0.04, -1.0, 0.0))
    t = 3.0 + own
    lit = ((uy == 0) & (ux > 0) & (ux < 4)) | ((ux == 0) & (uy > 0) & (uy < 3))
    t = np.where(lit, t + 1.0, t)
    t = np.where(last_y | last_x, joint_t, t)
    if not irregular:
        # worn patches where feet go: the joints filled and the setts polished a step smoother
        worn = K.noise((H, W), np.random.default_rng(seed + 9), 14.0) > 0.7
        t = np.where(worn & (last_y | last_x), joint_t + 0.6, np.where(worn & ~(last_y | last_x), np.minimum(t, 3.4), t))
    K.rpaint(cv, m, [('slate_cool', 'stone', 'stone_warm'), ('stone_cool', 'stone_cool', 'stone')], t,
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
    # the sand wet and darker towards the water, its edge lumpy (round 3 of the detail audit, R3-12)
    Yg, Xg = np.mgrid[0:H, 0:W]
    toward = ndi.distance_transform_edt(~ndi.binary_dilation(~m, iterations=1) | (Yg < ys.min() + 14))
    lump = 7.0 + 7.0 * K.noise((H, W), np.random.default_rng(seed + 5), 4.0)
    wet = m & (toward < lump) & (Yg >= ys.min() + 14)
    K.rpaint(cv, wet, [('earth_cool', 'sand_cool', 'sand_cool'), ('earth_cool', 'sand_cool', 'sand')], 2.0,
             np.clip(K.noise((H, W), np.random.default_rng(seed + 6), 6.0) * 0.999, 0, 0.999))
    wedge = wet & ~ndi.binary_erosion(wet) & (toward >= lump - 1.5)
    cv[wedge] = cv[wedge] + 1                                            # the wet line's drying rim, a step up
    # ripple marks left by the tide: short broken crests every 4 to 5 rows, wandering, a lit crest
    # row over a shaded trough row (drawn, not blotched; calm: one tone each way)
    phase = Yg + np.round(1.6 * np.sin(Xg * 0.21 + Yg * 0.05) + 1.2 * np.sin(Xg * 0.07 + 2.0)).astype(int)
    rip = (phase % np.where(wet, 4, 5) == 0) & (K.noise((H, W), np.random.default_rng(seed + 7), 2.5) > 0.32) & m & (Yg >= ys.min() + 14)
    up_ = np.zeros_like(rip)
    up_[:-1] = rip[1:]
    K.rpaint(cv, rip, [('earth_cool', 'sand_cool', 'sand')], np.where(wet, 1.4, 2.0), 0.0)
    K.rpaint(cv, up_ & m & ~rip & ~wet & (Yg >= ys.min() + 14), [('earth_cool', 'sand', 'sand_warm')], 4.0, 0.0)
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
            if drift[y, x] < 0.55 + 0.2 * (1 - up) or K.hsh(x, y, seed + 2) < 0.2:
                continue                                                 # sand shows between the drifts
            r = 1.4 + 1.6 * up * K.hsh(x, y, seed + 3) + 0.4
            pm = (((Xg - x) / r) ** 2 + ((Yg - y) / (r * 0.75)) ** 2 <= 1.0) & m
            u, v = (Xg - x) / r, (Yg - y) / (r * 0.75)
            t = 3.0 + 1.0 * ((u + v) < -0.6) * (r > 2.2) - 1.0 * ((u + v) > 0.7)
            K.rpaint(cv, pm & ~wet, [fams[int(K.hsh(x, y, seed + 4) * len(fams)) % len(fams)]], t, 0.0)


def quay_wall(cv, beach_cells, quay_cells, face=11, seed=1507):
    """The quay's wall face where the quay stands over the beach (round 3 of the detail audit): under
    the quay's edge a lit coping row, then rubble blocks 6 to 10 texels across in courses of 4 to 5,
    each lit at its top-west and dark at its foot, dark joints; a dark foot band on the sand with a
    few pebbles. Drawn on the beach's top `face` rows wherever the quay is directly north of it."""
    from scripts.art.kit.sets import _common as K
    H, W = cv.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    north_q = np.zeros_like(quay_cells)
    north_q[1:] = quay_cells[:-1]
    top_edge = beach_cells & north_q
    ys, xs = np.nonzero(top_edge)
    if not len(ys):
        return
    y0 = int(ys.min())
    cols = np.zeros(W, bool)
    cols[xs] = True
    wall = np.zeros((H, W), bool)
    wall[y0 - 3:y0 + face, :] = cols[None, :]
    wall &= beach_cells | quay_cells
    r = Yg - y0
    course = np.where(r < 5, 0, 1)
    off = course * 4 + 2
    bx = (Xg + off) % 8
    jx = (bx == 0) & (K.vhash((Xg + off) // 8, course, seed + 3) > 0.15)
    cr = np.where(course == 0, r, r - 5)
    t = np.full((H, W), 2.6)
    t = np.where(cr == 0, 3.4, t)                                        # each block's lit top
    t = np.where((bx == 1) & (cr > 0), 3.0, t)                           # and its lit west end
    t = np.where(cr >= 3, 2.0, t)                                        # its foot turning under
    t = np.where(jx | (r == 4), 1.0, t)                                  # the joints
    t = np.where(r == -3, 4.0, t)                                        # the coping: its lit edge,
    t = np.where(r == -2, 3.4, t)                                        # its front,
    t = np.where(r == -1, 1.0, t)                                        # its shadow line on the face
    t = np.where(r >= face - 1, 1.0, t)                                  # the dark foot on the sand
    K.rpaint(cv, wall, [('stone_cool', 'stone', 'stone_warm'), ('stone_cool', 'stone_cool', 'stone')], t,
             np.clip(K.vhash((Xg + off) // 8, course, seed + 1) * 0.999, 0, 0.999))
    foot = beach_cells & (r >= face) & (r < face + 2) & cols[None, :]
    K.rpaint(cv, foot & (K.vhash(Xg // 3, Yg, seed + 2) > 0.3), [('earth_cool', 'sand_cool', 'sand')], 1.0, 0.0)


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
        setts(cv, quay, w=26, h=14, irregular=True)     # a platform's flags, laid irregularly
    else:
        setts(cv, quay, w=9, h=7)                       # squarer setts (R3-12)
    shingle(cv, beach)
    quay_wall(cv, mp == 'shingle', mp == 'quay')
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

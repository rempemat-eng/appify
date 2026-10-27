"""Pieces the kit paints itself (not seeded from a zone): the woodland's footbridge and its talus
boulders, from the soft-grid painters (softground.footbridge, props.boulder4).

    python3 -m scripts.art.kit.structures

writes game/kit/props/art/<id>[_<variant>].png and the pieces in game/kit/pieces/ (kept if they
exist, so their reviewed data is never overwritten; --force rewrites them).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.native import props as P4
from scripts.art.native import softground as GD
from scripts.art.native.palette import to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art')
D = 3


def _write(piece: dict, force: bool) -> None:
    d = os.path.join(PIECES, piece['kind'])
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, piece['id'] + '.json')
    if os.path.exists(path) and not force:
        return
    json.dump(piece, open(path, 'w'), indent=1)
    open(path, 'a').write('\n')


def footbridge(force: bool) -> None:
    """A plank footbridge over a river three cells wide, 20 world px wide (the woodland's)."""
    river = 72
    W, H = 60 + 40, river + 48
    x0, x1 = 20, 80
    cv = np.full((H, W), -1, np.int32)
    water = np.zeros((H, W), bool)
    water[24:24 + river, :] = True
    GD.footbridge(cv, x0, x1, water, np.random.default_rng(12))
    img = to_rgba(cv)
    os.makedirs(ART, exist_ok=True)
    Image.fromarray(img, 'RGBA').save(os.path.join(ART, 'woodland_footbridge.png'))
    # the foot: the middle of the deck's south end (where the path comes off it)
    ys = np.nonzero((cv >= 0).any(1))[0]
    foot = [(x0 + x1) / 2.0, float(ys.max() + 1)]
    deck_top = 24 - 10
    deck = [-(x1 - x0) / 2 / D, (deck_top - foot[1]) / D, (x1 - x0) / D, (foot[1] - deck_top) / D]
    _write({
        'schema': 'napattack.piece/1', 'id': 'woodland_footbridge', 'name': 'Plank footbridge', 'kind': 'structure',
        'biomes': ['woodland', 'valley'], 'version': 1,
        'variants': [{'id': 'river3', 'weight': 1.0, 'png': 'res://kit/props/art/woodland_footbridge.png'}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'eastward-edges.md 5.3; ground-rules.md 3 (a route crosses water only on a span)',
                     'note': 'softground.footbridge painted as a piece: abutments, deck, kerbs, posts and rails'},
        'geometry': {'size_px': [W, H], 'size_cells': [round(W / 24), round(H / 24)], 'foot': foot, 'z_sort': 'ground',
                     'collision': {'shape': 'none'}, 'footprint': []},
        'placement': {'role': 'bridge', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'water', 'note': 'spans a channel three cells wide, north to south'},
                                   {'rel': 'adjacent', 'what': 'route', 'cells': 1, 'note': 'a route meets it at both ends'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': False},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'deck': [round(v, 2) for v in deck]},
        'audit': {'painter': {'module': 'scripts.art.native.softground', 'fn': 'footbridge', 'args': {}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'eastward_ref': None,
                  'todo': ['a variant for each channel width (2 and 4 cells)']},
    }, force)


BOULDERS = [(10, 7, 1615, True), (11, 7, 1616, False), (13, 8, 1617, True), (15, 9, 1618, False),
            (18, 11, 1619, True), (22, 13, 1620, False)]


def boulders(force: bool) -> None:
    os.makedirs(ART, exist_ok=True)
    variants = []
    feet = []
    for i, (w, h, seed, moss) in enumerate(BOULDERS):
        img, anc, _ = P4.boulder4(D, w, h, seed=seed, moss='top' if moss else None)
        name = 'woodland_boulder_%d.png' % i
        img.save(os.path.join(ART, name))
        variants.append({'id': 'b%d' % i, 'weight': 1.0, 'png': 'res://kit/props/art/' + name,
                         'foot': [float(anc[0]), float(anc[1])]})
        feet.append(anc)
    w0, h0 = Image.open(os.path.join(ART, 'woodland_boulder_0.png')).size
    _write({
        'schema': 'napattack.piece/1', 'id': 'woodland_boulder', 'name': 'Talus boulder', 'kind': 'prop',
        'biomes': ['woodland', 'valley', 'highland'], 'version': 1, 'variants': variants,
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'eastward-edges.md 2.3 (boulders), ground-rules.md 6 (rocks rest side by side)',
                     'note': 'props.boulder4 at six sizes (10 x 7 to 22 x 13 world px), mossy and bare'},
        'geometry': {'size_px': [w0, h0], 'size_cells': [1, 1], 'foot': [float(feet[0][0]), float(feet[0][1])], 'z_sort': 'foot',
                     'collision': {'shape': 'rect', 'rect': [-4.0, -4.0, 8.0, 4.0]}},
        'placement': {'role': 'rock', 'snap': 'free', 'forbids': [{'rel': 'not_overlap', 'what': 'rock'}, {'rel': 'on', 'what': 'route'}],
                      'composition': 'cluster'},
        'rendering': {'cast_shadow': {'shape': 'ellipse', 'size': [7.0, 3.0], 'dir': [2.0, -1.0]}, 'contact_ao': True},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': True, 'blocks_shots': True},
        'audit': {'painter': {'module': 'scripts.art.native.props', 'fn': 'boulder4', 'args': {}}, 'seeded_from': 'scripts/art/kit/structures.py',
                  'todo': ['collision per variant size']},
    }, force)


def log_steps(force: bool) -> None:
    """Four log treads cut into a two-cell earth face, a flight two cells wide (softground.log_steps:
    the head flush with the rim, the foot on the lower ground; eastward-edges.md 6.1)."""
    W, H = 48, 48
    cv = np.full((H, W), -1, np.int32)
    GD.log_steps(cv, 0, W, 0, H, 4, np.random.default_rng(21))
    os.makedirs(ART, exist_ok=True)
    Image.fromarray(to_rgba(cv), 'RGBA').save(os.path.join(ART, 'log_steps.png'))
    _write({
        'schema': 'napattack.piece/1', 'id': 'log_steps', 'name': 'Log steps', 'kind': 'structure',
        'biomes': ['woodland', 'valley'], 'version': 1,
        'variants': [{'id': 'w2', 'weight': 1.0, 'png': 'res://kit/props/art/log_steps.png'}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'eastward-edges.md 6.1, ground-rules.md 1 (a stair stands where the rim runs straight across its whole width, its head flush with the rim, its foot on the lower ground)',
                     'note': 'softground.log_steps as a piece, for a face of two cells'},
        'geometry': {'size_px': [W, H], 'size_cells': [2, 2], 'foot': [W / 2.0, float(H)], 'z_sort': 'ground',
                     'collision': {'shape': 'none'}, 'footprint': []},
        'placement': {'role': 'stair', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'face', 'note': 'its whole flight on face cells, the rim straight above it'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': False},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'deck': [-8.0, -16.0, 16.0, 16.0]},
        'audit': {'painter': {'module': 'scripts.art.native.softground', 'fn': 'log_steps', 'args': {'n': 4}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'todo': ['flights for faces of one and three cells']},
    }, force)


def waterfall(force: bool, cells_w: int) -> None:
    """A fall where water crosses a south rim (ground-rules 2: lip flush with the rim, centred on
    the channel and as wide as it, landing in a pool): the woodland's painted fall (water.fall_hd:
    the stone lip, the sheet with streaks, the plume, foam rings and spray), over a face of two
    cells, for a channel `cells_w` cells wide."""
    from scripts.art.native import water as WA
    from scripts.art.native.palette import C as CC
    wpx = cells_w * 24
    W, H = wpx + 48, 12 + 48 + 34
    # paint over two different pool fills (the rings need water to lie on) and keep only the
    # pixels the fall drew, which agree between the two
    runs = []
    for pool in (CC('water', 2), CC('water', 1)):
        cv = np.full((H, W), -1, np.int32)
        cv[60:, :] = pool
        # the sheet a few texels wider than the channel, so it covers the bank lumps either side
        WA.fall_hd(cv, 20 / D, (wpx + 8) / D, 12 / D, 60 / D, seed=65 + cells_w)
        runs.append(cv)
    cv = np.where(runs[0] == runs[1], runs[0], -1)
    os.makedirs(ART, exist_ok=True)
    name = 'waterfall_%d' % cells_w
    Image.fromarray(to_rgba(cv), 'RGBA').save(os.path.join(ART, name + '.png'))
    cols = list(range(-(cells_w // 2), cells_w - cells_w // 2))
    _write({
        'schema': 'napattack.piece/1', 'id': name, 'name': 'Waterfall, %d cells' % cells_w, 'kind': 'structure',
        'biomes': ['woodland', 'valley', 'highland'], 'version': 1,
        'variants': [{'id': 'w%d' % cells_w, 'weight': 1.0, 'png': 'res://kit/props/art/%s.png' % name}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'ground-rules.md 2 (rules.water_fall), eastward-edges.md 5.3',
                     'note': "the woodland's painted fall (water.fall_hd) as a piece over a two-cell face"},
        'geometry': {'size_px': [W, H], 'size_cells': [cells_w, 2], 'foot': [W / 2.0, 60.0], 'z_sort': 'ground',
                     'collision': {'shape': 'none'},
                     'footprint': [[c, r] for r in (-2, -1) for c in cols]},
        'placement': {'role': 'waterfall', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'face', 'note': 'its footprint is the face under water crossing a south rim'},
                                   {'rel': 'under', 'what': 'water', 'note': 'water on the tier above, as wide as the fall'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'none'}, 'contact_ao': False,
                      'animations': [{'clip': 'fall', 'loop': True, 'reduced_motion': 'hold:0', 'on_screen_only': True}]},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': True, 'blocks_shots': False},
        'audit': {'painter': {'module': 'scripts.art.native.water', 'fn': 'fall_hd', 'args': {'seed': 65 + cells_w}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'todo': ['the falling animation (the woodland flow strip)']},
    }, force)


def main(argv=None) -> int:
    force = '--force' in (argv or sys.argv[1:])
    footbridge(force)
    boulders(force)
    log_steps(force)
    waterfall(force, 2)
    waterfall(force, 3)
    print('structures: footbridge, boulders, log steps, waterfalls')
    return 0


if __name__ == '__main__':
    sys.exit(main())

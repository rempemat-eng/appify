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


def footbridge(force: bool, cells: int = 3) -> None:
    """A plank footbridge over a channel `cells` wide (2: a stream, 3: the woodland's river, 4: a
    river), 20 world px wide: abutments set in both banks, the deck, kerbs, posts and rails. The
    bake paints it over the zone's own banks (rendering.paint), its picture is the preview."""
    river = 24 * cells
    pid = 'woodland_footbridge' if cells == 3 else 'footbridge_%d' % cells
    W, H = 60 + 40, river + 48
    x0, x1 = 20, 80
    cv = np.full((H, W), -1, np.int32)
    water = np.zeros((H, W), bool)
    water[24:24 + river, :] = True
    GD.footbridge(cv, x0, x1, water, np.random.default_rng(12))
    img = to_rgba(cv)
    os.makedirs(ART, exist_ok=True)
    Image.fromarray(img, 'RGBA').save(os.path.join(ART, pid + '.png'))
    # the foot: the middle of the deck's south end (where the path comes off it)
    ys = np.nonzero((cv >= 0).any(1))[0]
    foot = [(x0 + x1) / 2.0, float(ys.max() + 1)]
    deck_top = 24 - 10
    deck = [-(x1 - x0) / 2 / D, (deck_top - foot[1]) / D, (x1 - x0) / D, (foot[1] - deck_top) / D]
    _write({
        'schema': 'napattack.piece/1', 'id': pid, 'name': 'Plank footbridge, %d cells' % cells, 'kind': 'structure',
        'biomes': ['woodland', 'valley'], 'version': 1,
        'variants': [{'id': 'river%d' % cells, 'weight': 1.0, 'png': 'res://kit/props/art/%s.png' % pid}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'eastward-edges.md 5.3; ground-rules.md 3 (a route crosses water only on a span)',
                     'note': 'softground.footbridge painted as a piece: abutments, deck, kerbs, posts and rails'},
        'geometry': {'size_px': [W, H], 'size_cells': [round(W / 24), round(H / 24)], 'foot': foot, 'z_sort': 'ground',
                     'collision': {'shape': 'none'}, 'footprint': []},
        'placement': {'role': 'bridge', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'water', 'note': 'spans a channel %d cells wide, north to south' % cells},
                                   {'rel': 'adjacent', 'what': 'route', 'cells': 1, 'note': 'a route meets it at both ends'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': False,
                      'paint': {'module': 'scripts.art.native.softground', 'fn': 'footbridge', 'args': {'deck_px': x1 - x0}}},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'deck': [round(v, 2) for v in deck]},
        'audit': {'painter': {'module': 'scripts.art.native.softground', 'fn': 'footbridge', 'args': {}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'eastward_ref': None,
                  'todo': []},
    }, force)


def stepping_stones(force: bool, cells: int) -> None:
    """Flat stones across a rill (1 cell) or a stream (2 cells), a stride apart, each props.boulder4
    low and flat with its wet ring: a footpath's crossing where a bridge would be too much."""
    river = 24 * cells
    W, H = 30, river + 48
    pid = 'stepping_stones_%d' % cells
    cv = np.full((H, W), -1, np.int32)
    water = np.zeros((H, W), bool)
    water[24:24 + river, :] = True
    stones_into(cv, water, W // 2, np.random.default_rng(40 + cells))
    os.makedirs(ART, exist_ok=True)
    Image.fromarray(to_rgba(cv), 'RGBA').save(os.path.join(ART, pid + '.png'))
    foot = [W / 2.0, float(H)]
    deck = [-5.0, -H / D, 10.0, H / D]
    _write({
        'schema': 'napattack.piece/1', 'id': pid, 'name': 'Stepping stones, %d cell%s' % (cells, 's' if cells > 1 else ''), 'kind': 'structure',
        'biomes': ['woodland', 'valley'], 'version': 1,
        'variants': [{'id': 'w%d' % cells, 'weight': 1.0, 'png': 'res://kit/props/art/%s.png' % pid}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'ground-rules.md 3 (a route crosses water only on a span or stones)',
                     'note': 'a footpath crossing a rill or a stream'},
        'geometry': {'size_px': [W, H], 'size_cells': [1, cells + 1], 'foot': foot, 'z_sort': 'ground', 'collision': {'shape': 'none'}, 'footprint': []},
        'placement': {'role': 'bridge', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'water', 'note': 'across a channel %d cell%s wide' % (cells, 's' if cells > 1 else '')},
                                   {'rel': 'adjacent', 'what': 'route', 'cells': 1, 'note': 'a footpath meets it at both banks'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': False,
                      'paint': {'module': 'scripts.art.kit.structures', 'fn': 'stepping_stones', 'args': {'seed': 40 + cells}}},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'deck': deck},
        'audit': {'painter': {'module': 'scripts.art.kit.structures', 'fn': 'stones_into', 'args': {}}, 'seeded_from': 'scripts/art/kit/structures.py', 'todo': []},
    }, force)


def stones_into(cv: np.ndarray, water: np.ndarray, x: int, rng) -> None:
    """Flat stepping stones down column x over `water`, a stride (9 to 11 texels) apart."""
    from scripts.art.native import screen as SN
    H, W = cv.shape
    ys = np.nonzero(water[:, max(0, min(W - 1, x))])[0]
    if not len(ys):
        return
    y = int(ys.min()) + 6
    while y < ys.max() - 1:
        w_ = rng.uniform(5.5, 7.0)
        img, anc, _a = P4.boulder4(D, w_, w_ * 0.45, seed=int(rng.integers(0, 10 ** 6)), moss='top' if rng.random() < 0.4 else None)
        dec = SN.to_codes(img)
        ox = x + int(rng.integers(-2, 3))
        ring = np.zeros_like(water)
        ring[max(0, y - 2):y + 3, max(0, ox - int(w_ * D * 0.6)):ox + int(w_ * D * 0.6)] = True
        ring &= water
        from scripts.art.native.palette import step
        cv[ring & (cv >= 0)] = step(cv[ring & (cv >= 0)], 1)
        SN.DC.paste(cv, dec, int(round(ox - anc[0])), int(round(y - anc[1])), shadow=True, shadow_dx=2, shadow_dy=1)
        y += int(rng.integers(9, 12))


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


def log_steps(force: bool, cells: int = 2) -> None:
    """Four log treads cut into a two-cell earth face, a flight `cells` wide (1: a footpath's, 2: a
    lane's, 3: a road's; softground.log_steps: the head flush with the rim, the foot on the lower
    ground, earth cheeks either side; eastward-edges.md 6.1)."""
    W, H = 24 * cells, 48
    pid = 'log_steps' if cells == 2 else 'log_steps_%d' % cells
    cv = np.full((H, W), -1, np.int32)
    GD.log_steps(cv, 0, W, 0, H, 4, np.random.default_rng(21))
    os.makedirs(ART, exist_ok=True)
    Image.fromarray(to_rgba(cv), 'RGBA').save(os.path.join(ART, pid + '.png'))
    _write({
        'schema': 'napattack.piece/1', 'id': pid, 'name': 'Log steps, %d cell%s' % (cells, 's' if cells > 1 else ''), 'kind': 'structure',
        'biomes': ['woodland', 'valley'], 'version': 1,
        'variants': [{'id': 'w%d' % cells, 'weight': 1.0, 'png': 'res://kit/props/art/%s.png' % pid}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'eastward-edges.md 6.1, ground-rules.md 1 (a stair stands where the rim runs straight across its whole width, its head flush with the rim, its foot on the lower ground)',
                     'note': 'softground.log_steps as a piece, for a face of two cells'},
        'geometry': {'size_px': [W, H], 'size_cells': [cells, 2], 'foot': [W / 2.0, float(H)], 'z_sort': 'ground',
                     'collision': {'shape': 'none'}, 'footprint': []},
        'placement': {'role': 'stair', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'face', 'note': 'its whole flight on face cells, the rim straight above it'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': False,
                      'paint': {'module': 'scripts.art.native.softground', 'fn': 'log_steps', 'args': {'n': 4}}},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'deck': [-4.0 * cells, -16.0, 8.0 * cells, 16.0]},
        'audit': {'painter': {'module': 'scripts.art.native.softground', 'fn': 'log_steps', 'args': {'n': 4}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'todo': []},
    }, force)


def waterfall(force: bool, cells_w: int, drop: int = 1) -> None:
    """A fall where water crosses a south rim (ground-rules 2: lip flush with the rim, centred on
    the channel and as wide as it, landing in a pool): the woodland's painted fall (water.fall_hd:
    the stone lip, the sheet with streaks, the plume, foam rings and spray), over a face of two
    cells per tier it drops (`drop`: 1, or 2 for the woodland's own cascade, four cells high), for a
    channel `cells_w` cells wide."""
    from scripts.art.native import water as WA
    from scripts.art.native.palette import C as CC
    wpx = cells_w * 24
    face = 48 * drop
    W, H = wpx + 48, 12 + face + 34
    # paint over two different pool fills (the rings need water to lie on) and keep only the
    # pixels the fall drew, which agree between the two
    runs = []
    for pool in (CC('water', 2), CC('water', 1)):
        cv = np.full((H, W), -1, np.int32)
        cv[12 + face:, :] = pool
        # the sheet a few texels wider than the channel, so it covers the bank lumps either side
        WA.fall_hd(cv, 20 / D, (wpx + 8) / D, 12 / D, (12 + face) / D, seed=65 + cells_w)
        runs.append(cv)
    cv = np.where(runs[0] == runs[1], runs[0], -1)
    os.makedirs(ART, exist_ok=True)
    name = 'waterfall_%d' % cells_w + ('' if drop == 1 else '_tall')
    Image.fromarray(to_rgba(cv), 'RGBA').save(os.path.join(ART, name + '.png'))
    cols = list(range(-(cells_w // 2), cells_w - cells_w // 2))
    _write({
        'schema': 'napattack.piece/1', 'id': name, 'name': 'Waterfall, %d cells%s' % (cells_w, '' if drop == 1 else ', a two-tier drop'), 'kind': 'structure',
        'biomes': ['woodland', 'valley', 'highland'], 'version': 1,
        'variants': [{'id': 'w%d' % cells_w, 'weight': 1.0, 'png': 'res://kit/props/art/%s.png' % name}],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'ground-rules.md 2 (rules.water_fall), eastward-edges.md 5.3',
                     'note': "the woodland's painted cascade as a piece over a face of %d cells" % (2 * drop)},
        'geometry': {'size_px': [W, H], 'size_cells': [cells_w, 2 * drop], 'foot': [W / 2.0, float(12 + face)], 'z_sort': 'ground',
                     'collision': {'shape': 'none'},
                     'footprint': [[c, -r] for r in range(2 * drop, 0, -1) for c in cols]},
        'placement': {'role': 'waterfall', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'face', 'note': 'its footprint is the face under water crossing a south rim'},
                                   {'rel': 'under', 'what': 'water', 'note': 'water on the tier above, as wide as the fall'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'none'}, 'contact_ao': False,
                      'paint': {'module': 'scripts.art.native.rocks', 'fn': 'fall', 'args': {'seed': 9 + cells_w, 'face_px': face}},
                      'animations': [{'clip': 'fall', 'loop': True, 'reduced_motion': 'hold:0', 'on_screen_only': True}]},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': True, 'blocks_shots': False},
        'audit': {'painter': {'module': 'scripts.art.native.water', 'fn': 'fall_hd', 'args': {'seed': 65 + cells_w}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'todo': ['the falling animation (the woodland flow strip)']},
    }, force)


def main(argv=None) -> int:
    force = '--force' in (argv or sys.argv[1:])
    for c in (2, 3, 4):
        footbridge(force, c)
    for c in (1, 2):
        stepping_stones(force, c)
    boulders(force)
    for c in (1, 2, 3):
        log_steps(force, c)
    for c in (1, 2, 3, 4):
        waterfall(force, c)
        waterfall(force, c, drop=2)
    print('structures: footbridges (2, 3, 4), stepping stones (1, 2), boulders, log steps (1, 2, 3), waterfalls (1 to 4, one and two tiers)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

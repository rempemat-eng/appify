"""Pieces the kit paints itself (not seeded from a zone): the woodland's footbridge and its talus
boulders, from the soft-grid painters (softground.footbridge, props.boulder4).

    python3 -m scripts.art.kit.structures

writes game/kit/props/art/<id>[_<variant>].png and the pieces in game/kit/pieces/ (kept if they
exist, so their reviewed data is never overwritten; --force rewrites them).
"""
from __future__ import annotations

import json
import math
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
        'placement': {'role': 'bridge', 'purpose': 'cross', 'snap': 'cell',
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
        'placement': {'role': 'bridge', 'purpose': 'cross', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'water', 'note': 'across a channel %d cell%s wide' % (cells, 's' if cells > 1 else '')},
                                   # its deck carries its own landing stones onto both banks, so the
                                   # footpath meets it on them (within, not adjacent)
                                   {'rel': 'within', 'what': 'route', 'cells': 1, 'note': 'a footpath meets it at both banks'}],
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
    from scripts.art.native import softground as GD
    y = int(ys.min()) + 6
    stones = []
    while y < ys.max() - 1:
        w_ = rng.uniform(5.5, 7.0)
        img, anc, _a = P4.boulder4(D, w_, w_ * 0.45, seed=int(rng.integers(0, 10 ** 6)), moss='top' if rng.random() < 0.4 else None)
        ox = x + int(rng.integers(-2, 3))
        stones.append((SN.to_codes(img), int(round(ox - anc[0])), int(round(y - anc[1]))))
        y += int(rng.integers(9, 12))
    # each with the one wet contact every stone in the water has (eastward-edges.md 5.3a)
    GD.seat_stones(cv, water, stones, lambda c, d, x_, y_: SN.DC.paste(c, d, x_, y_, shadow=True, shadow_dx=2, shadow_dy=1))


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
        'placement': {'role': 'rock', 'purpose': 'mark', 'snap': 'free', 'forbids': [{'rel': 'not_overlap', 'what': 'rock'}, {'rel': 'on', 'what': 'route'}],
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
        'placement': {'role': 'stair', 'purpose': 'climb', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'face', 'note': 'its whole flight on face cells, the rim straight above it'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'baked'}, 'contact_ao': False,
                      'paint': {'module': 'scripts.art.native.softground', 'fn': 'log_steps', 'args': {'n': 4}}},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': False, 'blocks_shots': False, 'deck': [-4.0 * cells, -16.0, 8.0 * cells, 16.0]},
        'audit': {'painter': {'module': 'scripts.art.native.softground', 'fn': 'log_steps', 'args': {'n': 4}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'todo': []},
    }, force)


FALL_FRAMES, FALL_FPS = 8, 10      # the fall's loop: 8 frames, each streak a step of its own period a frame


CREST_MAX = 3      # the deepest the white water under the lip breaks (texels below the bend)


def crest_foam(w: int, seed: int) -> np.ndarray:
    """How far the white water breaks under the lip of a sheet `w` texels wide painted with `seed`,
    per column: rocks.crest_breaks, drawn from the fall's generator in the order rocks.sheet draws
    it (after its two or three converging streaks), so this is the crest the piece shows."""
    from scripts.art.native import rocks as RK
    rng = np.random.default_rng(seed)
    nst = int(rng.integers(2, 4))
    for _ in range(nst):
        rng.uniform(0.2, 0.8)
        rng.integers(9, 16)
    return RK.crest_breaks(w, rng)


def crest_bow(w: int, seed: int = 0) -> np.ndarray:
    """How many texels the bend line bows downstream, per column (rocks.sheet's bow)."""
    u = (np.arange(w) + 0.5) / w
    return np.round(1.6 * (1.0 - (2.0 * np.clip(u, 0.0, 1.0) - 1.0) ** 2)).astype(int)


def sheet_mask(shape, x0: int, w: int, y0: int, y1: int, seed: int = 0) -> np.ndarray:
    """The texels a piece's sheet covers (rows y0 .. y1 - 1), on a canvas of `shape`: rocks.sheet's
    own outline (rocks.sheet_mask), its wobble phased from the rim row, so a piece's picture and its
    bake are one sheet. `seed` is unused (the outline does not depend on it)."""
    from scripts.art.native import rocks as RK
    return RK.sheet_mask(shape, x0, x0 + w, y0, y1, phase_y=y0)


def sheet_outline(x0: int, w: int, y0: int, y1: int, seed: int = 0) -> np.ndarray:
    """The sheet's first and past-last column per row (rows y0 .. y1 - 1), from sheet_mask."""
    m = sheet_mask((y1 + 1, x0 + w + 4 * 24), x0, w, y0, y1)
    out = np.zeros((max(0, y1 - y0), 2), np.int32)
    for k, Y in enumerate(range(y0, y1)):
        xs = np.nonzero(m[Y])[0]
        out[k] = (int(xs.min()), int(xs.max()) + 1) if len(xs) else (x0, x0 + w)
    return out


def fall_sheet(cv: np.ndarray, x0: int, w: int, y0: int, y1: int, seed: int, t: int = 0, rings: bool = True,
               keep=None) -> None:
    """A fall drawn from the rim down (texels): the stream's own water bends over the face's top
    edge at row y0 and falls as one sheet exactly the channel's width (x0 .. x0 + w) at the lip, in
    front of the face and behind nothing, the white water only where it lands (no spray on the
    face, Matt, 2 Nov).

    The sheet is the woodland's own (review round 7: rounds 5 to 7 kept re-deriving a second design
    that drifted from the approved one): rocks.sheet paints it, the same code rocks.fall paints the
    woodland's fall with, parameterised only by the width, the height and the seed. Its wobble and
    its streaks' phase run from the rim row, so the piece's picture and its bake are one sheet, and
    the tongue's two tones meet a texel earlier or later row by row (round 7, P7-3). At its foot
    rocks.plunge churns, a clump seated under any stretch of the foot no clump reaches (P7-2).

    `t` is the frame of the loop (FALL_FRAMES frames): each streak falls a step of its own period a
    frame, so the loop closes; frame 0 is the still the bake draws. `keep` is unused (kept for old
    callers)."""
    from scripts.art.native import ctx
    from scripts.art.native import rocks as RK
    rng = np.random.default_rng(seed)
    t = t % FALL_FRAMES
    foot = RK.sheet(cv, x0, x0 + w, y0, y1, y0 / ctx.D, rng, seed, t=t, n=FALL_FRAMES, phase_y=y0, stagger=True)
    RK.plunge(cv, foot[0], foot[1], y1, seed, t=t, n=FALL_FRAMES, rings=rings, seat_gaps=True)


def waterfall(force: bool, cells_w: int, drop: int = 1) -> None:
    """A fall where water crosses a south rim (ground-rules 2: lip flush with the rim, centred on
    the channel and as wide as it, landing in a pool): fall_sheet, from the rim (row 12 of the
    picture, the face's top edge) to the pool (the foot, the face's bottom), over a face of two cells
    per tier it drops (`drop`: 1 or 2), for a channel `cells_w` cells wide. Nothing is drawn above
    the rim or outside the channel's columns above the pool (test_kit checks the picture)."""
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
        # the bake's seed (rendering.paint.args.seed, fall_frames): the picture is frame 0 of what a
        # baked zone shows (review round 6, L6-1: it was painted with 65 + c, its own lanes and edges)
        fall_sheet(cv, 24, wpx, 12, 12 + face, seed=9 + cells_w)
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
                     'footprint': [[c, -r] for r in range(2 * drop, 0, -1) for c in cols],
                     'sheet_px': [24, 24 + wpx, 12, 12 + face]},
        'placement': {'role': 'waterfall', 'purpose': 'flow', 'snap': 'cell',
                      'requires': [{'rel': 'on', 'what': 'face', 'note': 'its footprint is the face under water crossing a south rim'},
                                   {'rel': 'under', 'what': 'water', 'note': 'water on the tier above, as wide as the fall'}],
                      'composition': 'axis'},
        'rendering': {'cast_shadow': {'shape': 'none'}, 'contact_ao': False,
                      'paint': {'module': 'scripts.art.native.rocks', 'fn': 'fall', 'args': {'seed': 9 + cells_w, 'face_px': face}},
                      'animations': [{'clip': 'fall', 'loop': True, 'reduced_motion': 'hold:0', 'on_screen_only': True}]},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': True, 'blocks_shots': False},
        'audit': {'painter': {'module': 'scripts.art.kit.structures', 'fn': 'fall_sheet', 'args': {'seed': 9 + cells_w}},
                  'seeded_from': 'scripts/art/kit/structures.py', 'todo': ['the falling animation (the woodland flow strip)']},
    }, force)


def fall_frames(cells_w: int, drop: int = 1):
    """The fall's loop for a piece: FALL_FRAMES frames of its sheet and plume (the bake's seed, so
    frame 0 is what the baked ground shows), side by side, cut to the pixels the fall owns; and
    where they lie on the piece's picture (x, y, w, h texels)."""
    from scripts.art.native.palette import C as CC
    wpx, face = cells_w * 24, 48 * drop
    W, H = wpx + 48, 12 + face + 34
    seed = 9 + cells_w
    base = np.full((H, W), CC('water', 2), np.int32)
    drawn = []
    for t in range(FALL_FRAMES):
        f = base.copy()
        fall_sheet(f, 24, wpx, 12, 12 + face, seed=seed, t=t, rings=False)
        drawn.append(f)
    own = np.zeros((H, W), bool)
    for f in drawn:
        own |= f != base                 # every pixel some frame draws: where the foam leaves, the pool
    sheet = sheet_mask((H, W), 24, wpx, 12, 12 + face, seed)
    own |= sheet
    # only what surely lies over the fall's own pixels in any zone (review round 4, F4-1: nothing
    # that moves may lie over what is not water): not the crest (the rim's lip stones cast their
    # shade on it in the bake, and it does not move); beside the sheet above its foot, nothing (the
    # face); below the foot, only the inlet the bake lays under every fall (bake.py: the sheet plus
    # rocks.PLUNGE_PAD each side, its two outer columns its rim's wet earth and rim line, its top
    # corners rounded) for 14 rows
    own[:12 + 8] = False
    from scripts.art.native import rocks as RK
    y1 = 12 + face
    own[:y1] &= sheet[:y1]
    ix0, ix1 = 24 - RK.PLUNGE_PAD, 24 + wpx + RK.PLUNGE_PAD
    for k in range(14):
        # the inlet's row k under the foot starts max(0, 3 - k) in from each side (its rounded
        # corners), its outermost texel there the rim's wet earth
        cut = max(0, 3 - k) + 1
        if y1 + k < H:
            own[y1 + k, :ix0 + cut] = False
            own[y1 + k, ix1 - cut:] = False
    own[y1 + 14:] = False
    ys, xs = np.nonzero(own)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    frames = []
    for f in drawn:
        f = f.copy()
        f[~own] = -1
        frames.append(f[y0:y1, x0:x1])
    return np.concatenate(frames, axis=1), [x0, y0, x1 - x0, y1 - y0]


def falls_animated() -> None:
    """Write every fall's loop and its animation entry (rendering.animations) into its piece."""
    for c in (1, 2, 3, 4):
        for drop in (1, 2):
            name = 'waterfall_%d' % c + ('' if drop == 1 else '_tall')
            strip, region = fall_frames(c, drop)
            Image.fromarray(to_rgba(strip), 'RGBA').save(os.path.join(ART, name + '_flow.png'), optimize=True)
            path = os.path.join(PIECES, 'structure', name + '.json')
            pc = json.load(open(path))
            before = json.dumps(pc, sort_keys=True)
            pc['rendering']['animations'] = [{
                'clip': 'fall', 'loop': True, 'frames': FALL_FRAMES, 'fps': FALL_FPS,
                'strip': 'res://kit/props/art/%s_flow.png' % name, 'frame_px': [region[2], region[3]], 'region_px': region,
                'reduced_motion': 'hold:0', 'on_screen_only': True}]
            pc['audit']['todo'] = [t for t in pc['audit'].get('todo', []) if 'animation' not in t]
            if json.dumps(pc, sort_keys=True) != before:
                json.dump(pc, open(path, 'w'), indent=1)
                open(path, 'a').write('\n')


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
    falls_animated()
    print('structures: footbridges (2, 3, 4), stepping stones (1, 2), boulders, log steps (1, 2, 3), waterfalls (1 to 4, one and two tiers)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

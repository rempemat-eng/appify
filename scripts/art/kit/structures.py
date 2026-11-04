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


FALL_FRAMES, FALL_PERIOD, FALL_FPS = 8, 24, 10      # the fall's loop: 8 frames, the streaks 3 texels a frame


CREST_MAX = 3      # the deepest the white water under the lip breaks (texels below the bend)


def crest_foam(w: int, seed: int) -> np.ndarray:
    """How far the white water breaks under the lip, per column of a sheet `w` texels wide (Matt,
    4 Nov: the lip read as a row of identical white scallops, stamped; review round 4, K4-2: then
    as a lid, one ruler-straight white row with icicle drips). After eastward-edges 5.3b and the
    woodland's rocks.crest_breaks: two or three runs of different lengths (two on a one-cell sheet),
    each 1 to 3 texels deep and rounded at its ends, with gaps of 3 to 5 texels where the darker
    sheet goes straight on, and the sheet's own edges left glassy (1 to 3 texels west, 2 to 4 on
    the shaded east), so the white is never one row across. 0 where no white breaks."""
    rng = np.random.default_rng(seed * 7919 + w)
    out = np.zeros(w, np.int32)
    n = 2 if w < 40 else 3
    gaps = [int(rng.integers(3, 6)) for _ in range(n - 1)]
    edge = [int(rng.integers(1, 4)), int(rng.integers(2, 5))]
    room = w - sum(gaps) - sum(edge)
    # runs of different lengths: cut the room unevenly (no two within 15 % of each other)
    for _ in range(40):
        cut = np.sort(rng.uniform(0.18, 0.82, n - 1)) if n > 1 else np.array([])
        lens = np.diff(np.concatenate([[0.0], cut, [1.0]])) * room
        if n == 1 or (np.min(np.diff(np.sort(lens))) > 0.15 * room / n and lens.min() >= 3):
            break
    lens = np.maximum(3, np.round(lens).astype(int))
    x = edge[0]
    for k, L in enumerate(lens):
        L = int(min(L, w - edge[1] - x))
        if L <= 0:
            break
        prof = np.clip(np.round(1.3 + rng.uniform(0.7, 1.6) * np.sin(np.linspace(0.2, np.pi - 0.2, L))
                                + rng.uniform(-0.45, 0.45, L)), 1, CREST_MAX).astype(int)
        prof[0] = prof[-1] = 1                                   # each run rounds off at its ends
        out[x:x + L] = prof
        x += L + (gaps[k] if k < len(gaps) else 0)
    return out


def crest_bow(w: int, seed: int = 0) -> np.ndarray:
    """How many texels the white water breaks below the bend line, per column: the bend bows a
    texel or two downstream in the middle (eastward-edges 5.3b), and each run of white breaks at its
    own height, one run a texel or two lower than its neighbour (review round 4, K4-2: no white row
    runs straight across a wide sheet)."""
    u = (np.arange(w) + 0.5) / w
    bow = np.round(1.7 * (1.0 - (2.0 * u - 1.0) ** 2)).astype(int)
    f = crest_foam(w, seed)
    rng = np.random.default_rng(seed * 313 + w)
    d = np.diff(np.concatenate([[0], (f > 0).astype(np.int8), [0]]))
    starts, stops = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
    drops = rng.permutation([0, 2, 1][:len(starts)] if len(starts) <= 3 else [k % 3 for k in range(len(starts))])
    ph = rng.uniform(0.0, 2.0 * math.pi)
    for k, (a, b) in enumerate(zip(starts, stops)):
        bow[a:b] += int(drops[k]) if w >= 40 else min(1, int(drops[k]))
        # within a run the white's top steps a texel here and there as it breaks (not one row)
        if b - a >= 8:
            x_ = np.arange(a + 2, b - 2)
            bow[x_] += (np.sin(x_ / 2.6 + ph) + 0.5 * np.sin(x_ / 1.3 + 2 * ph) > 0.55).astype(int)
    return bow


def sheet_outline(x0: int, w: int, y0: int, y1: int, seed: int) -> np.ndarray:
    """The sheet's columns per row (texels; rows y0 .. y1 - 1, each (xl, xr)): exactly the channel's
    width at the lip and through the crest, below it each edge wandering a texel in now and then
    (review round 4, K4-1: the silhouette was a perfect rectangle), and swelling a texel or two in
    the last rows where it meets the pool. Above the last five rows it never leaves x0 .. x0 + w
    (Matt, 2 Nov: the sheet never spreads over the stones either side)."""
    rng = np.random.default_rng(seed * 131 + w)
    pl, pr = rng.uniform(0.0, 2.0 * math.pi, 2)
    out = np.zeros((max(0, y1 - y0), 2), np.int32)
    for k, Y in enumerate(range(y0, y1)):
        dy = Y - y0
        il = ir = 0
        if dy >= 8 and Y < y1 - 5:
            il = int(0.35 * math.sin(dy / 3.7 + pl) + 0.45 * math.sin(dy / 1.7 + 2.0 * pl) > 0.42)
            ir = int(0.35 * math.sin(dy / 3.1 + pr) + 0.45 * math.sin(dy / 2.3 + 2.0 * pr) > 0.3)
        sw = 0 if Y < y1 - 4 else (1 if Y < y1 - 2 else 2)
        out[k] = (x0 + il - sw, x0 + w - ir + sw)
    return out


def sheet_mask(shape, x0: int, w: int, y0: int, y1: int, seed: int) -> np.ndarray:
    """The texels sheet_outline covers, on a canvas of `shape`."""
    H, W = shape
    m = np.zeros((H, W), bool)
    for k, (xl, xr) in enumerate(sheet_outline(x0, w, y0, y1, seed)):
        if 0 <= y0 + k < H:
            m[y0 + k, max(0, xl):min(W, xr)] = True
    return m


def _lanes(x0: int, w: int, seed: int) -> list:
    """The sheet's streak lanes across x0 .. x0 + w: (first column, width 1 to 3, phase, pattern)
    where pattern holds FALL_PERIOD entries, each a tone offset for its row in the loop: a long lit
    run and a short broken one of a different tone, a darker trough behind each, the body between."""
    rng = np.random.default_rng(seed * 977 + w)
    lanes, x = [], x0
    while x < x0 + w:
        lw = int(rng.choice([1, 1, 2, 2, 3]))
        pat = np.zeros(FALL_PERIOD, np.int32)
        L1 = int(rng.integers(4, 12))
        a1 = int(rng.integers(0, FALL_PERIOD))
        L2 = int(rng.integers(2, 5))
        a2 = (a1 + L1 + int(rng.integers(2, max(3, FALL_PERIOD - L1 - L2 - 1)))) % FALL_PERIOD
        for j in range(L1):
            pat[(a1 + j) % FALL_PERIOD] = 2 if j < L1 - 2 else 1       # the run, fading at its tail
        for j in range(L2):
            pat[(a2 + j) % FALL_PERIOD] = 1
        # a third fleck of light, 2 to 3 texels, where the run's tail has room
        a3 = (a2 + L2 + int(rng.integers(2, 5))) % FALL_PERIOD
        L3 = int(rng.integers(2, 4))
        if all(pat[(a3 + j) % FALL_PERIOD] == 0 and pat[(a3 + j + 1) % FALL_PERIOD] == 0 for j in range(-1, L3)):
            for j in range(L3):
                pat[(a3 + j) % FALL_PERIOD] = 2 if j == 0 else 1
        else:
            a3, L3 = a2, L2
        for a_, L_ in ((a1, L1), (a2, L2), (a3, L3)):
            pat[(a_ + L_) % FALL_PERIOD] = -1                           # the trough behind it
        lanes.append((x, lw, int(rng.integers(0, FALL_PERIOD)), pat, int(rng.integers(0, 2))))
        x += lw
    return lanes


def fall_sheet(cv: np.ndarray, x0: int, w: int, y0: int, y1: int, seed: int, t: int = 0, rings: bool = True,
               keep=None) -> None:
    """A fall drawn from the rim down (texels): the stream's own water bends over the face's top
    edge at row y0 and falls as one sheet exactly the channel's width (x0 .. x0 + w) at the lip, in
    front of the face and behind nothing. Matt, 2 Nov: "the waterfall overlaps in an unrealistic way
    on the top bit": so no ledge stone or crest stands proud of the rim over the banks or the stream
    above, the sheet never spreads over the stones either side, and the white water is only where
    the sheet lands: the foam and its rings lie on the pool, no spray on the face.

    Drawn as the woodland's fall is (rocks.fall; review round 4, K4-1 to K4-3: the kit's sheet was
    four flat slabs of tone with 1 px white lines on fixed columns, a lid for a crest, a comb under
    the foam): where the channel runs over the rim its last rows fade into a glassy tongue in a
    checker; the bend line bows a texel or two downstream, and the white water breaks under it in
    two or three runs with gaps where the darker sheet goes on (crest_foam). The sheet is lit west,
    a body, shaded east, darker near the foot; across its whole width it falls in broken streak
    runs of different lengths in four to five tones, lanes one to three texels wide each on its own
    phase, and its east edge is broken dark streaks, not a slab; its edges wander a texel
    (sheet_outline). At its foot rocks.plunge churns.

    `t` is the frame of the fall's loop (FALL_FRAMES frames): every lane's pattern has one period
    (FALL_PERIOD texels) and falls FALL_PERIOD / FALL_FRAMES texels a frame, so the loop closes.
    Frame 0 is the still the bake draws. `keep` is unused (kept for old callers)."""
    from scripts.art.native.palette import C, FI
    H, W = cv.shape
    waters = [FI[n_] for n_ in ('water', 'water_warm', 'water_cool') if n_ in FI]
    foam = crest_foam(w, seed)
    bow = crest_bow(w, seed)
    # the channel's last rows above the rim fade into the glassy tongue (only where it is water)
    for k in range(1, 4):
        Y = y0 - k
        if not (0 <= Y < H):
            continue
        for X in range(max(0, x0), min(W, x0 + w)):
            if not (cv[Y, X] >= 0 and cv[Y, X] // 8 in waters):
                continue
            if k == 1:
                cv[Y, X] = C('water', 4) if (X + Y) % 2 == 0 else C('water', 3)     # the tongue itself
            elif (k == 2 and (X + Y) % 2 == 0) or (k == 3 and (X + 2 * Y) % 4 == 0):
                cv[Y, X] = C('water', 3)                                         # fading up the channel
    outline = sheet_outline(x0, w, y0, y1, seed)
    lanes = _lanes(x0, w, seed)
    lane_of = {}
    for (lx, lw, ph, pat, jog) in lanes:
        for j in range(lw):
            lane_of[lx + j] = (ph, pat, jog if j == lw - 1 else 0)
    shift = t * FALL_PERIOD // FALL_FRAMES
    for k, Y in enumerate(range(y0, y1)):
        if not (0 <= Y < H):
            continue
        xl, xr = int(outline[k][0]), int(outline[k][1])
        f = (Y - y0) / max(1.0, (y1 - y0))
        for X in range(max(0, xl), min(W, xr)):
            s = (X + 0.5 - xl) / max(1.0, xr - xl)                 # 0 west .. 1 east across the ribbon
            i = min(w - 1, max(0, X - x0))
            dy = Y - y0 - int(bow[i])
            d_ = int(foam[i]) if x0 <= X < x0 + w else 0
            tt = 4 if s < 0.18 else (3 if s < 0.6 else (2 if s < 0.86 else 1))
            if f > 0.78 + 0.05 * math.sin((X - x0) * 1.7 + seed) + 0.03 * math.sin((X - x0) * 0.61):
                tt = max(1, tt - 1)                                 # thinner and darker near the foot
            if Y - y0 < 2 or dy < 2:
                c = C('water', 4) if s < 0.65 else C('water', 3)    # the glassy tongue over the edge
            elif dy == 2:
                c = (C('water', 5) if s < 0.7 else C('water', 4)) if d_ else C('water', 3)   # the bend
            elif d_ and dy < 3 + d_:
                c = C('snow', 5) if s < 0.62 else C('snow', 4)      # the white water breaking under it
            elif d_ and dy < 4 + d_:
                c = C('water', 2)                                   # its shade
            elif not d_ and dy < 6:
                c = C('water', 3) if s < 0.45 else C('water', 2)    # a gap: the darker sheet going on
            else:
                ph, pat, jog = lane_of.get(X, (0, np.zeros(FALL_PERIOD, np.int32), 0))
                v = int(pat[(Y - y0 + jog - shift + ph) % FALL_PERIOD]) if dy > 6 else 0
                if v > 0:
                    # the sheet's surface varies down its height (fixed to the face, so the loop still
                    # closes): a run passing a thinner stretch dims a step, so a tall sheet does not
                    # repeat its lane's pattern every FALL_PERIOD rows
                    band_ = ((Y - y0 + ph * 3) // 9) * 7919 + (X - x0 - jog) // 2 * 104729 + seed * 31
                    if (band_ * 2654435761 >> 7) % 5 < 2:
                        v -= 1
                if s >= 0.86:
                    # the shaded east edge: broken dark streaks on the darkest body
                    c = C('water', 2) if v > 0 else (C('water', 0) if v < 0 else C('water', tt))
                elif v == 2:
                    c = C('snow', 5) if s < 0.32 else (C('snow', 4) if s < 0.5 else (C('water', 5) if s < 0.72 else C('water', 4)))
                elif v == 1:
                    c = C('water', 5) if s < 0.55 else C('water', 4)
                elif v == -1:
                    c = C('water', max(1, tt - 1))                  # the trough behind a streak
                else:
                    c = C('water', tt)
            cv[Y, X] = c
    # where it lands (rocks.plunge, shared with the woodland's fall; the woodland review, 4 Nov):
    # broken clumps of churning white in 4 to 5 tones within the foot plus a few texels, flecks
    # dissolving into the pool, spray on the water beside the foot, ripple arcs going downstream
    from scripts.art.native import rocks as RK
    RK.plunge(cv, x0, x0 + w, y1, seed, t=t % FALL_FRAMES, n=FALL_FRAMES, rings=rings)


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
        fall_sheet(cv, 24, wpx, 12, 12 + face, seed=65 + cells_w)
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
        'audit': {'painter': {'module': 'scripts.art.kit.structures', 'fn': 'fall_sheet', 'args': {'seed': 65 + cells_w}},
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

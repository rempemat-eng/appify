"""Prop and structure pieces as Godot scenes (docs/world-editor.md, "The kit: pieces").

    python3 -m scripts.art.kit.props        # writes game/kit/props/<id>.tscn and index.json

Each prop or structure piece becomes a scene: a KitPiece root (world/terrain/kit_piece.gd) at its
foot, its picture as a Sprite2D offset so the foot is the origin (the zone y-sorts by it), and its
solid box as a StaticBody2D on the walls layer. index.json carries what the game, the ground's
shadow pass and the validator read without opening the piece files: variants, foot, collision and
shadow in texels, role, approval. Generated: never edit the scenes by hand.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

from scripts.art.kit.schema import PIECES, ROOT, piece_files

OUT = os.path.join(ROOT, 'game', 'kit', 'props')
D = 3


def _res(path: str) -> str:
    return path if path.startswith('res://') else 'res://' + os.path.relpath(path, os.path.join(ROOT, 'game'))


from scripts.art.sun import CAST  # noqa: E402  (kx, ky), the one sun (game/data/sun.json)

RIM = 6
TRUNK_CORE, TRUNK_RIM = 1, 3   # the trunk's run: a core 3 texels thick, a rim of 3 each side (9 in all)
PAD_DEEP = 3                   # the contact pad under the base: 3 texels deep, the base's width + 2
BASE_ROWS = 6                  # rows over the foot whose opaque columns are the base (2 world px)
DEEP_MIN = 40                  # the third step's parts on snow: at least this many texels
DRIFT_L = 200                  # a drift at the foot: texels this bright (luma) joined to the base rows
SNOW_BIOMES = ('frostline',)   # a tree on snow steps its core one tone further (eastward-edges 7.1)


def _runs(row: np.ndarray) -> list:
    """The runs of True in a 1D array as (first, last) pairs."""
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0] - 1))


def crown_shadow(png_res: str, foot, out_name: str, deep: bool = False):
    """A tree's cast shadow from its own silhouette (Claude A, 27 Oct: shaped from the crown, not
    an ellipse), thrown by the one sun (game/data/sun.json: shadows fall south-east; light from the
    upper left): every opaque texel at height h above the foot lands CAST[0] h east and CAST[1] h
    south of the foot. What is drawn below the foot (a drift, a root) casts nothing. The shadow is
    tied to its tree (detail and logic audits of #545):
      - a contact pad in the core tone under the base, the base's width + 2 and PAD_DEEP deep, as the
        footprint rule's contact;
      - the trunk's run thrown along the sun's ray from the foot, its core TRUNK_CORE texels each side
        of the axis and its rim TRUNK_RIM beyond, wherever the tree's axis is drawn, so the core runs
        unbroken from the foot into the crown's shadow and a thin snag or sapling keeps a core;
      - the outer RIM texels one ramp step down, the rest two (house-style 6). On snow (`deep`) a
        third step lies 3 texels further in, along the trunk's axis and on the pad, so the shade
        reads as shade and not as a drift (snow's tones lie 5 % apart at the top of its ramp).
    Written as an R8 mask with its offset from the foot; TerrainGround and compose.shadows lay it
    like the ellipses."""
    from PIL import Image
    from scipy import ndimage as ndi
    rgba = np.asarray(Image.open(os.path.join(ROOT, 'game', png_res[len('res://'):])).convert('RGBA'))
    a = rgba[..., 3] > 0
    H, W = a.shape
    fx, fy = foot
    kx, ky = CAST
    fr = int(np.ceil(fy - 0.5))                     # rows above it stand over the ground
    # a snow drift drawn at the foot lies on the ground: bright texels joined to the bottom rows cast
    # nothing and are not the base (the krummholz's west drifts threw a band west of the shrub)
    luma = rgba[..., :3].astype(float) @ np.array([0.2126, 0.7152, 0.0722])
    lab, _n = ndi.label(a & (luma > DRIFT_L))
    low = np.unique(lab[max(0, fr - BASE_ROWS):fr])
    drift = ndi.binary_dilation(np.isin(lab, low[low > 0]), np.ones((3, 3), bool), iterations=2)   # and its outline
    a = a & ~drift
    # the base: the run of the bottom rows' opaque columns at the foot (or the nearest one)
    band = a[max(0, fr - BASE_ROWS):fr].any(0)
    runs = _runs(band)
    bx0, bx1 = min(runs, key=lambda r: 0 if r[0] <= fx < r[1] + 1 else min(abs(r[0] - fx), abs(r[1] + 1 - fx)))
    bw = bx1 - bx0 + 1
    # the trunk's axis from the foot up: it follows a narrow run (a leaning trunk), holds its line
    # through the crown, and is drawn where the tree is drawn there
    cx, axis = (bx0 + bx1 + 1) / 2.0, []
    for y in range(fr - 1, -1, -1):
        row = a[y]
        c = int(np.clip(np.floor(cx), 0, W - 1))
        near = [r for r in _runs(row) if r[0] - 1 <= c <= r[1] + 1]
        if not near:
            break                                   # the axis ends where the tree does: no loose stamps
        r0, r1 = near[0]
        if r1 - r0 + 1 <= bw + 4:
            cx = (r0 + r1 + 1) / 2.0
        axis.append((cx, fy - y - 0.5))
    # the silhouette thrown
    ys, xs = np.nonzero(a[:fr])
    h = fy - ys - 0.5
    sx = np.round(xs + 0.5 + h * kx - fx).astype(int)
    sy = np.round(h * ky).astype(int)
    ax = np.array([(np.round(x + h_ * kx - fx), np.round(h_ * ky)) for x, h_ in axis], int).reshape(-1, 2)
    px0, px1 = int(np.floor(bx0 - fx)) - 1, int(np.ceil(bx1 + 1 - fx)) + 1     # the pad's columns
    M = 8 + TRUNK_RIM + TRUNK_CORE
    xs_all = np.concatenate([sx, ax[:, 0], [px0, px1 - 1]])
    ys_all = np.concatenate([sy, ax[:, 1], [0, PAD_DEEP - 1]])
    x0, y0 = int(xs_all.min()) - M, int(ys_all.min()) - M
    shape = (int(ys_all.max()) - y0 + M + 1, int(xs_all.max()) - x0 + M + 1)
    m = np.zeros(shape, bool)
    m[sy - y0, sx - x0] = True
    m = ndi.binary_closing(m, iterations=2)
    m = ndi.binary_fill_holes(m)
    line = np.zeros(shape, bool)
    line[ax[:, 1] - y0, ax[:, 0] - x0] = True
    pad = np.zeros(shape, bool)
    pad[-y0:-y0 + PAD_DEEP, px0 - x0:px1 - x0] = True
    sq = np.ones((3, 3), bool)
    tcore = ndi.binary_dilation(line, sq, iterations=TRUNK_CORE) if len(ax) else line
    trim = ndi.binary_dilation(tcore, sq, iterations=TRUNK_RIM)
    m |= trim | pad
    core = ndi.binary_erosion(m, iterations=RIM) | tcore | pad
    out = np.where(core, 2, np.where(m, 1, 0)).astype(np.uint8)
    if deep:
        # the third step: deep in the crown's core (opened, and only parts of some size, so no
        # loose blocks), along the trunk's axis and on the pad
        inner = ndi.binary_opening(ndi.binary_erosion(m, iterations=RIM + 3) & core, sq)
        lab3, n3 = ndi.label(inner)
        if n3:
            size = ndi.sum(inner, lab3, range(1, n3 + 1))
            inner = np.isin(lab3, 1 + np.nonzero(size >= DEEP_MIN)[0])
        out[inner | tcore | pad] = 3
        out[ndi.binary_dilation(out == 3, sq) & (out == 1)] = 2     # never three tones beside one
    out[:max(0, -y0)] = 0                           # nothing north of the foot row (the trunk's rim at the foot)
    Image.fromarray(out, 'L').save(os.path.join(OUT, 'art', out_name))
    return {'png': 'res://kit/props/art/' + out_name, 'offset': [int(x0), int(y0)]}


# the footprint shadow rule (Frostline audit Z4, 12 Nov; round 2 after the audit of #479; house-style 6,
# eastward-edges 7.1 and 11.6). Light from the upper left, thrown by the one sun (game/data/sun.json):
# a texel h above the ground lands kx h east and ky h south. Every placed variant has its own mask.
#  - The base: per column, the picture's lowest opaque row where the column stands on the ground (within
#    BASE_BAND of the foot or below it), else the foot line (an overhang, a seat between legs). A texel's
#    height is measured from its column's base, so what is drawn below the foot stays on its own row.
#  - The contact: an ellipse centred on the base line under the footprint (the grounded columns,
#    widened to the solid box), so CONTACT texels (1 world px) show below the picture in the core tone.
#  - The cast: the silhouette thrown by the sun, closed into one shape on a padded canvas.
#  - Depth is not height: fences and walls cast their ground footprint (the cell's arms) swept up the
#    heights of their east-west section; a north-south gate its run, swept up its east-west twin's
#    height, the open leaf from its own lower edge; the fold ruin its walls' footprint swept up an
#    authored height, so the back wall's shadow lies on the fold's floor.
#  - Buildings (BUILDING_ROLES) cast nothing before their lit front: under the picture nothing south of
#    the base line but the contact, and south of the foot line only the wedge east of the sun's ray through
#    the box's front-east foot corner (11.6; Matt, 28 Nov: "Wedge, softer"), cut before the ramp.
#  - The ramp: two steps down in the core, one in the rim, the core chosen from the local thickness
#    (a distance transform), so every shadow at least 3 texels thick keeps a core.

BASE_BAND = 6            # columns whose lowest row lies within this of the foot (2 world px) stand on the ground
CONTACT = 3              # texels of contact shown below the base in the core tone (1 world px)
CLOSE = 7                # the closing that joins the projected texels into one shape
RIMS = (3, 6)            # the rim, 1 world px on a small shadow and 2 on a large one (house-style 6)
HALF = 12                # half a cell: a fence or wall arm's reach from the foot
BUILDING_ROLES = ('house', 'coop', 'shelter', 'sty', 'stall')
RUN_ON = 48              # how far a fence's or wall's arms run on past its cell before the cut (R2-1)
BLOCK_DEPTH = 30         # a solid box this deep (texels) or more casts as a block, swept up its height (R2-2)
CAST_HEIGHT = {'brackens_fold_ruin': 27}   # authored: the ruin's walls stand about 9 world px


def _alpha(png_res: str) -> np.ndarray:
    from PIL import Image
    return np.asarray(Image.open(os.path.join(ROOT, 'game', png_res[len('res://'):])).convert('RGBA'))[..., 3] > 0


_LIB = {}


def _lib() -> dict:
    if not _LIB:
        for f in piece_files():
            p = json.load(open(f))
            _LIB[p['id']] = p
    return _LIB


def _variant(p: dict, vid: str | None) -> dict:
    vs = p.get('variants') or []
    return next((v for v in vs if v['id'] == vid), None) or vs[0]


def _foot(p: dict, v: dict):
    g = p.get('geometry', {})
    return v.get('foot') or g.get('foot') or [g['size_px'][0] / 2.0, g['size_px'][1]]


def _rect(p: dict):
    col = p.get('geometry', {}).get('collision') or {}
    return [x * D for x in col['rect']] if col.get('shape') == 'rect' and col.get('rect') else None


def _height_rows(p: dict, vid: str | None, wide: float = 0.0):
    """A piece's heights (texels above its foot line) where its picture is opaque: every row, or only
    the rows covering `wide` of its width (an east-west section's rails, not its post)."""
    v = _variant(p, vid)
    a = _alpha(v['png'])
    fy = int(np.ceil(_foot(p, v)[1]))
    rows = np.nonzero(a.sum(1) >= max(1, wide * a.any(0).sum()))[0]
    return sorted({max(0, fy - 1 - int(y)) for y in rows})


BOUNDARY = re.compile(r'^(fence_(?:picket|rail|wattle)|wall_drystone)_(?:(stile)_)?([nesw]+)$')
GATE_NS = re.compile(r'^(.*)_gate_ns$')


def shadow_rule(p: dict) -> str:
    """Which way a piece's shadow is made: 'boundary' (a fence or wall cell), 'gate_ns' (a gate in a
    north-south run), 'ruin' (an enclosure with an authored cast height), 'building', 'block' (a solid
    box BLOCK_DEPTH deep or more: the drove well) or 'silhouette'."""
    if BOUNDARY.match(p['id']):
        return 'boundary'
    if GATE_NS.match(p['id']):
        return 'gate_ns'
    if p['id'] in CAST_HEIGHT:
        return 'ruin'
    if (p.get('placement') or {}).get('role') in BUILDING_ROLES:
        return 'building'
    rect = _rect(p)
    if rect is not None and rect[3] >= BLOCK_DEPTH:
        return 'block'
    return 'silhouette'


def _sweep(rr: np.ndarray, cc: np.ndarray, heights) -> tuple:
    """Ground texels (rows, cols) swept up the heights: the shadow of a slab standing on them."""
    kx, ky = CAST
    R, C = [], []
    for h in heights:
        R.append(np.floor(rr + 0.5 + ky * h).astype(int))
        C.append(np.floor(cc + 0.5 + kx * h).astype(int))
    return (np.concatenate(R), np.concatenate(C)) if R else (np.zeros(0, int), np.zeros(0, int))


def _box(x0, y0, x1, y1, dx, dy) -> tuple:
    """Texels (rows, cols, foot-relative) whose centres lie in a box given from the foot point."""
    c = np.arange(int(np.floor(x0 + dx)) - 1, int(np.ceil(x1 + dx)) + 1)
    r = np.arange(int(np.floor(y0 + dy)) - 1, int(np.ceil(y1 + dy)) + 1)
    c = c[(c + 0.5 >= x0 + dx) & (c + 0.5 < x1 + dx)]
    r = r[(r + 0.5 >= y0 + dy) & (r + 0.5 < y1 + dy)]
    R, C = np.meshgrid(r, c, indexing='ij')
    return R.ravel(), C.ravel()


def _ramp(m: np.ndarray, rim: int) -> np.ndarray:
    """2 in the core, 1 in the rim: the core lies deeper than min(rim, half the local thickness)
    and at least 1 texel in, so any shape 3 texels thick keeps a core (B7)."""
    from scipy import ndimage as ndi
    d = ndi.distance_transform_edt(m)
    local = ndi.grey_dilation(d, size=(2 * rim + 1, 2 * rim + 1))
    core = m & (d > np.maximum(1.0, np.minimum(rim, local / 2.0)))
    return np.where(core, 2, np.where(m, 1, 0)).astype(np.uint8)


def before_front(cols: np.ndarray, rows: np.ndarray, xe: float, fy: float) -> np.ndarray:
    """(rows, cols) texels (sprite frame) before a building's lit front: south of the foot line fy and
    west of the sun's ray through its front-east foot corner (xe, fy), as volume.before_front."""
    kx, ky = CAST
    Y = rows[:, None] + 0.5 - fy
    X = cols[None, :] + 0.5
    if ky <= 0:
        return np.broadcast_to(Y > 0, (len(rows), len(cols)))
    return (Y > 0) & (X < xe + kx / ky * Y)


def footprint_shadow(p: dict, vid: str, out_name: str) -> dict:
    """One variant's shadow by the footprint rule (the comment above). Written as an R8 mask (2 the
    core, 1 the rim) with its offset from the foot, laid by TerrainGround and compose.shadows."""
    from PIL import Image
    from scipy import ndimage as ndi
    kx, ky = CAST
    rule = shadow_rule(p)
    v = _variant(p, vid)
    a = _alpha(v['png'])
    fx, fy = _foot(p, v)
    rect = _rect(p)
    H, W = a.shape
    sx0, sy0 = int(np.floor(-fx)), int(np.floor(-fy))      # the sprite's top left from the foot, as it is laid
    dx, dy = fx + sx0, fy + sy0                              # the foot point in the sprite's texel frame, rel.
    FY = -sy0                                                # the foot line, in sprite rows
    has = a.any(0)
    g = np.where(has, H - np.argmax(a[::-1], 0), 0)          # each column's base: below its lowest opaque row
    grounded = has & (g >= FY - BASE_BAND)
    G = np.where(grounded, g, np.where(has, np.maximum(g, FY), FY))   # a standing column on its own base
    xs_all = np.nonzero(has)[0]
    pic0, pic1 = xs_all.min(), xs_all.max() + 1
    # the footprint's columns: the grounded ones, widened to the solid box, never past the picture
    if grounded.any():
        gx = np.nonzero(grounded)[0]
        x0, x1 = float(gx.min()), float(gx.max() + 1)
        if rect is not None and rule not in ('ruin',):
            x0, x1 = min(x0, fx + rect[0]), max(x1, fx + rect[0] + rect[2])
        x0, x1 = max(x0, pic0), min(x1, pic1)
    else:
        x0 = x1 = None
    # the shapes, each closed and ramped on its own and laid by the deepest step: 'cast' (the
    # silhouette's throw), 'band' (a fence's or wall's arms: cut to the cell, see below) and 'post'
    layers = {}

    def put(layer, r, c):
        R, C = layers.setdefault(layer, ([], []))
        R.append(r)
        C.append(c)

    def silhouette(cols_ok, base):
        ys, xs = np.nonzero(a & cols_ok[None, :])
        h = base[xs] - 1 - ys
        put('cast', np.floor(base[xs] - 0.5 + ky * h).astype(int), np.floor(xs + 0.5 + kx * h).astype(int))

    def band(rr_rel, cc_rel, heights, layer='cast'):
        r, c = _sweep(rr_rel, cc_rel, heights)
        put(layer, r - sy0, c - sx0)

    segmented = False
    if rule == 'boundary':
        fam, stile, letters = BOUNDARY.match(p['id']).groups()
        lib = _lib()
        twin = lib[fam + '_ew']                               # the run's section: its rails, its wall
        tall = lib.get(fam + '_stile_ew') if stile else twin  # what stands at the junction: a post, a stile
        rns, rew = _rect(lib[fam + '_ns']), _rect(lib[fam + '_ew'])
        hw, ey0, ey1 = -rns[0], rew[1], rew[1] + rew[3]
        twin_v = vid if any(t['id'] == vid for t in twin['variants']) else \
            ('plain' if any(t['id'] == 'plain' for t in twin['variants']) else None)
        rails = _height_rows(twin, twin_v, wide=0.3)
        # each arm runs on past the cell (as the run it belongs to does) and the band is cut back to the
        # cell afterwards (R2-1): so a cell's core and rim are the run's, and a run laid cell by cell joins
        # into one band with no rim at the seams
        far = HALF + RUN_ON
        boxes = [(-hw, ey0, hw, ey1)]
        boxes += [b for k, b in (('n', (-hw, -far, hw, ey0)), ('s', (-hw, ey1, hw, far)),
                                 ('e', (hw, ey0, far, ey1)), ('w', (-far, ey0, -hw, ey1))) if k in letters]
        for b in boxes:
            band(*_box(*b, dx, dy), rails, 'band')
        cut = letters
        jc = np.zeros(W, bool)
        jc[max(0, int(np.floor(fx - hw))):int(np.ceil(fx + hw))] = True
        if stile:
            # the stile's steps stand across the run, as wide as its picture, as high as its east-west twin
            band(*_box(min(-hw, pic0 - fx), ey0, max(hw, pic1 - fx), ey1, dx, dy),
                 range(0, max(_height_rows(tall, None)) + 1), 'post')
        elif (grounded & jc).any():                          # a post (or the wall) stands at the junction
            post = 'post' if any(t['id'] == 'post' for t in twin['variants']) else twin_v
            band(*_box(-hw, ey0, hw, ey1, dx, dy), range(0, max(_height_rows(twin, post)) + 1), 'post')
    elif rule == 'gate_ns':
        lib = _lib()
        twin = lib[GATE_NS.match(p['id']).group(1) + '_gate_ew']
        th = max(_height_rows(twin, 'shut'))
        sv = _variant(p, 'shut')
        sa = _alpha(sv['png'])
        sfx, sfy = _foot(p, sv)
        sys_, sxs = np.nonzero(sa)
        rx0, rx1 = sxs.min() - sfx, sxs.max() + 1 - sfx       # the run's x extent from the foot
        ry0, ry1 = sys_.min() + th - sfy, sys_.max() + 1 - sfy   # its ground from the north post to the south end
        if vid == 'shut' or p['id'].startswith('wall_'):
            band(*_box(rx0, ry0, rx1, ry1, dx, dy), range(0, th + 1))   # the shut leaf, or the wall, along the run
        else:
            for py0, py1 in ((ry0, ry0 + 3), (ry1 - 3, ry1)):        # an open fence gate: its two posts
                band(*_box(rx0, py0, rx1, py1, dx, dy), range(0, th + 1))
        leaf = has & ((np.arange(W) + 0.5 < fx + rx0) | (np.arange(W) + 0.5 > fx + rx1))
        silhouette(leaf, np.where(has, g, FY))                # the open leaf stands at its own lower edge
        if x0 is not None:
            x0, x1 = max(x0, fx + rx0), min(x1, fx + rx1)
    elif rule == 'ruin':
        hgt = CAST_HEIGHT[p['id']]
        f = np.zeros_like(a)
        f[hgt:] = a[hgt:] & a[:-hgt]                          # ground under a wall: the wall stands hgt above it
        f = ndi.binary_opening(f, iterations=1)
        ys, xs = np.nonzero(f)
        band(ys + sy0, xs + sx0, range(0, hgt + 1))
        segmented = True
    elif rule in ('building', 'block') and rect is not None:
        # a roofed building or a deep solid block (the drove well): its ground box swept up its height (the
        # picture's above the foot, less the box's depth that the picture shows above its front); a
        # building's is cut below at the front (11.6), so what shows is a column east of it from its back to
        # its front
        top = int(np.nonzero(a.any(1))[0].min())
        bx0, bx1 = rect[0], rect[0] + rect[2]
        if rule == 'block' and x0 is not None:
            bx0, bx1 = min(bx0, x0 - fx), max(bx1, x1 - fx)      # the block as wide as it stands
        band(*_box(bx0, rect[1], bx1, rect[1] + rect[3], dx, dy),
             range(0, max(1, FY - top - int(round(rect[3]))) + 1))
        if rule == 'block':
            # and what stands above the box's back row (the well's house behind its trough) stands on that
            # row: thrown from there, not from the trough's foot (R2-2: it was a thin wedge south of the trough)
            back = int(np.floor(fy + rect[1]))
            ys, xs = np.nonzero(a[:back])
            h = back - 1 - ys
            put('cast', np.floor(back - 0.5 + ky * h).astype(int), np.floor(xs + 0.5 + kx * h).astype(int))
    else:
        silhouette(has, G)
    pts = {k: (np.concatenate(R), np.concatenate(C)) for k, (R, C) in layers.items()}
    allr = np.concatenate([r for r, _ in pts.values()] + [np.zeros(0, int)])
    allc = np.concatenate([c for _, c in pts.values()] + [np.zeros(0, int)])
    # the canvas, in sprite texels, padded past the closing on every side (B6)
    pad = CLOSE + 3
    r0 = (allr.min() if len(allr) else FY) - pad
    r1 = (allr.max() if len(allr) else FY) + pad + 1
    c0 = (allc.min() if len(allc) else pic0) - pad
    c1 = (allc.max() if len(allc) else pic1) + pad + 1
    r0, r1 = min(r0, int(G.min()) - 8 - pad), max(r1, int(G.max()) + 8 + pad)
    c0, c1 = min(c0, pic0 - pad), max(c1, pic1 + pad)
    out = np.zeros((r1 - r0, c1 - c0), np.uint8)
    def closed(cr, cc):
        m = np.zeros((r1 - r0, c1 - c0), bool)
        m[cr - r0, cc - c0] = True
        if m.any():
            m = ndi.binary_dilation(m, iterations=CLOSE)
            m = ndi.binary_fill_holes(m)
            m = ndi.binary_erosion(m, iterations=CLOSE)
            m |= ndi.gaussian_filter(m.astype(float), 1.2) > 0.5   # a hem's teeth smoothed, nothing taken away
        return m

    post_m = None
    if 'band' in pts and 'post' in pts:
        # a post or stile is ramped with the run's band (no rim between them) and keeps its whole shadow
        # past the cut; the neighbours' bands lie under it at the same or a lighter step
        post_m = closed(*pts.pop('post'))
        post_keep = ndi.binary_dilation(post_m, structure=np.ones((3, 3)), iterations=RIMS[1])   # with its rim's reach into the band
        pts['band'] = (np.concatenate([pts['band'][0], np.nonzero(post_m)[0] + r0]),
                       np.concatenate([pts['band'][1], np.nonzero(post_m)[1] + c0]))
    cell = np.ones((r1 - r0, c1 - c0), bool)
    if rule == 'boundary':
        # the cell: the rows north of it belong to the cell north, and so on (the run's neighbours each
        # carry their own share), so the run's cells meet edge to edge
        R = np.arange(r0, r1)[:, None] + sy0
        C = np.arange(c0, c1)[None, :] + sx0
        if 'n' in cut:
            cell &= R >= -HALF
        if 's' in cut:
            cell &= R < HALF
        if 'w' in cut:
            cell &= C >= -HALF
        if 'e' in cut:
            cell &= C < HALF
    for k, (cr, cc) in sorted(pts.items()):
        m = closed(cr, cc)
        if not m.any():
            continue
        if k == 'cast' and rule == 'silhouette':
            # a fragment of the throw that touches nothing of the picture is dropped (R2-2: a stray streak
            # off the broken cart's crates, the muck heap's)
            pic_c = np.zeros_like(m)
            ys_, xs_ = np.nonzero(a)
            ok_ = (ys_ >= r0) & (ys_ < r1) & (xs_ >= c0) & (xs_ < c1)
            pic_c[ys_[ok_] - r0, xs_[ok_] - c0] = True
            pic_c = ndi.binary_dilation(pic_c, iterations=1)
            lab, n = ndi.label(m, structure=np.ones((3, 3)))
            keep = np.unique(lab[pic_c & m])
            m = np.isin(lab, keep[keep > 0])
        if rule == 'building' and rect is not None:
            # the ground before the lit front is lit: cut before the ramp (see the cut below)
            big = m.sum() > 600
            m &= ~before_front(np.arange(c0, c1), np.arange(r0, r1), fx + rect[0] + rect[2], FY)
            lv = _ramp(m, RIMS[1] if big else RIMS[0])
        else:
            lv = _ramp(m, RIMS[1] if (k == 'band' or m.sum() > 600) else RIMS[0])
        if k == 'band':
            lv = np.where(cell | (post_keep if post_m is not None else False), lv, 0).astype(np.uint8)
        out = np.maximum(out, lv)
    # the contact, centred on the base line: CONTACT texels show below it in the core tone
    if x0 is not None:
        Y, X = np.mgrid[r0:r1, c0:c1]
        cols = np.arange(c0, c1)
        base = np.where((cols >= 0) & (cols < W), G[np.clip(cols, 0, W - 1)], FY)[None, :]
        # the contact runs under the columns that stand on the ground or are low over it (a seat between
        # its legs), not across an open gateway or the mouth of the fold
        low = has & (g >= FY - max(BASE_BAND, 0.4 * (FY - int(np.nonzero(a.any(1))[0].min()))))
        lo = np.zeros(W, bool)
        lo[max(0, int(np.floor(x0))):int(np.ceil(x1))] = True
        if not segmented:
            lo &= low | grounded
        else:
            lo &= grounded
        segs = []
        cols_lo = np.nonzero(lo)[0]
        for sgm in np.split(cols_lo, np.nonzero(np.diff(cols_lo) > 1)[0] + 1):
            if len(sgm) and grounded[sgm].any():
                segs.append((float(max(x0, sgm.min())), float(min(x1, sgm.max() + 1))))
        for s0, s1 in segs:
            if rule == 'boundary':
                # a fence's or wall's contact is an even strip, so a run's cells meet without a scallop
                ry, east, flat = CONTACT + 1, 0.0, True
            else:
                # the contact's depth grows with what stands there (1 to 2 world px below the base at its
                # middle, R2: as grounded as main's pools at play scale), and the light from the upper left
                # carries it on east a little past the base
                ry = CONTACT + 1 + int(np.clip(round(0.2 * (s1 - s0)) - CONTACT, 0, CONTACT + 1))
                east, flat = (round(kx * 3 * ry) if rule != 'building' else 0.0), False
            s1e = s1 + east
            cx, rx = (s0 + s1e) / 2.0, max(0.5, (s1e - s0) / 2.0)
            t = np.minimum(1.0, np.abs(X + 0.5 - cx) / rx)
            prof = np.ones_like(t) if flat else (1.0 - t ** 3) ** (1.0 / 3.0)
            d = np.abs(Y + 0.5 - base)
            inside = (X + 0.5 >= s0) & (X + 0.5 <= s1e)
            out = np.maximum(out, np.where(inside & (d <= ry * prof), 1, 0).astype(np.uint8))
            out = np.maximum(out, np.where(inside & (d <= (ry - 1) * prof), 2, 0).astype(np.uint8))
    if rule == 'boundary':
        out = np.where(cell | (post_keep if post_m is not None else False), out, 0).astype(np.uint8)
    # nothing west: of the footprint where the piece stands, else of the picture
    west = x0 if (x0 is not None and rule in ('silhouette', 'building', 'block')) else pic0
    out[:, :max(0, int(np.ceil(west)) - c0)] = 0
    if rule == 'building':
        # nothing before the front (eastward-edges 11.6; Matt, 28 Nov: "Wedge, softer"): under the
        # picture the contact only; south of the foot line only the wedge east of the sun's ray through
        # the front-east foot corner (the box's east wall on the foot line), which that corner throws.
        # The cast was cut the same way before its ramp, so the rim runs along the wedge's diagonal as
        # on every other edge and the core never meets the lit ground before the front
        cols, rows = np.arange(c0, c1), np.arange(r0, r1)
        xe = fx + rect[0] + rect[2] if rect is not None else float(pic1)
        lim = np.where((cols >= pic0) & (cols < pic1), G[np.clip(cols, 0, W - 1)] + CONTACT, FY)
        out[(rows[:, None] >= lim[None, :]) & before_front(cols, rows, xe, FY)] = 0
    if rule in ('silhouette', 'block', 'building'):
        # what shows of the shadow is one with the picture: a piece seen apart from it (a stack's top thrown
        # past a stake, a crate's streak) is dropped (R2-2)
        pic_c = np.zeros(out.shape, bool)
        ys_, xs_ = np.nonzero(a)
        ok_ = (ys_ >= r0) & (ys_ < r1) & (xs_ >= c0) & (xs_ < c1)
        pic_c[ys_[ok_] - r0, xs_[ok_] - c0] = True
        vis = (out > 0) & ~pic_c
        lab, n = ndi.label(vis, structure=np.ones((3, 3)))
        keep = np.unique(lab[ndi.binary_dilation(pic_c, iterations=1) & vis])
        out = np.where(vis & ~np.isin(lab, keep[keep > 0]), 0, out).astype(np.uint8)
    ys, xs = np.nonzero(out)
    out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Image.fromarray(out, 'L').save(os.path.join(OUT, 'art', out_name))
    return {'png': 'res://kit/props/art/' + out_name, 'offset': [int(c0 + xs.min() + sx0), int(r0 + ys.min() + sy0)]}


def _set_looks() -> dict:
    """{piece id: look} for the prop sets' buildings (scripts/art/kit/sets/looks.py)."""
    from scripts.art.kit.sets import looks as LK
    return LK.VOLUME_LOOKS


def volume_look(p: dict) -> dict | None:
    """The look a piece's body was drawn from by the house builder (houses.building), or None: a
    zone plan's building (the piece's audit source, part body) or a prop set's building
    (sets/looks.VOLUME_LOOKS, the Act 1 mill). Every such piece casts its volume's shadow
    (volume_shadow, bake's VOL.bake_cast) and no other: no structure draws two shadows."""
    looks = _set_looks()
    if p['id'] in looks:
        return dict(looks[p['id']])
    src = next((s for s in (p.get('audit') or {}).get('sources') or [] if s.get('part') == 'body'), None)
    plan_path = os.path.join(ROOT, 'game', 'data', 'plans', '%s.json' % (src or {}).get('zone'))
    if not src or not os.path.exists(plan_path):
        return None
    plan = json.load(open(plan_path))
    b = next((b for b in plan.get('buildings', []) if b['id'] == src.get('object')), None)
    if b is None:
        return None
    look = dict(plan.get('art', {}).get('looks', {}).get(b['id'], {}))
    look.setdefault('w', b['rect'][2])
    look.setdefault('depth', b['rect'][3])
    look.setdefault('seed', sum(map(ord, b['id'])))      # the zone painter's seed (town.py), so a front
    return look                                           # gable's stack stands where it was drawn


def volume_shadow(p: dict, out_name: str) -> dict | None:
    """A house's cast shadow from its volume (scripts/art/native/volume.py, eastward-edges 11.6): a
    column east of it shaped by its roof and stacks, from the look its body was drawn from (the
    piece's audit source in the zone plan, or a set's look in scripts/art/kit/sets/looks.py). Written
    as an R8 mask like a crown's (2 the core, 1 the rim) with its offset from the foot."""
    from PIL import Image
    from scripts.art.native import volume as VOL
    look = volume_look(p)
    if look is None:
        return None
    lv, ox, oy = VOL.house_cast(look, D)
    Image.fromarray(lv, 'L').save(os.path.join(OUT, 'art', out_name))
    return {'png': 'res://kit/props/art/' + out_name, 'offset': [int(ox), int(oy)]}


def _anim(rendering: dict, foot) -> dict | None:
    """The piece's looping strip (rendering.animations with a strip): where it is, its frames and
    rate, and its offset from the foot (a fall's frames cover its sheet; an animal's its whole
    picture, frame 0 being the still)."""
    for a in rendering.get('animations') or []:
        if a.get('strip') and a.get('frames', 0) > 1:
            region = a.get('region_px') or [0, 0] + list(a.get('frame_px') or [0, 0])
            return {'clip': a['clip'], 'strip': a['strip'], 'frames': int(a['frames']), 'fps': float(a.get('fps', 8)),
                    'offset': [region[0] - foot[0], region[1] - foot[1]], 'cover': not a.get('region_px'),
                    'reduced_motion': a.get('reduced_motion', 'hold:0')}
    return None


def entry(p: dict) -> dict:
    g = p.get('geometry', {})
    r = p.get('rendering', {})
    foot = g.get('foot') or [g['size_px'][0] / 2.0, g['size_px'][1]]
    col = g.get('collision') or {}
    rect = [v * D for v in col['rect']] if col.get('shape') == 'rect' and col.get('rect') else None
    # a round post (a sign's: geometry.collision {shape: circle, radius}, centred on the foot). The
    # index keeps `collision` a box for everything that reads boxes (the circle's bounding box) and
    # names the radius beside it: the scene's body is the circle and the walk mask blocks the cells
    # the circle touches (walk.py, walk.gd). It used to be dropped here, so a sign had no body in
    # its scene while the walk mask blocked its whole 2 by 2 footprint.
    radius = None
    if col.get('shape') == 'circle' and col.get('radius'):
        radius = round(col['radius'] * D, 3)
        radius = int(radius) if radius == int(radius) else radius
        rect = [-radius, -radius, 2 * radius, 2 * radius]
    cs = r.get('cast_shadow') or {}
    shadow = None
    vshadow = {}
    is_tree = p.get('placement', {}).get('role') == 'tree' and p.get('variants')
    vol = None
    if not is_tree and (p['kind'] == 'structure' or p['id'] in _set_looks()) and p.get('variants'):
        # a building drawn by the house builder (houses.py), from a zone plan's look or a set's:
        # its volume's shadow, and only that one
        vol = volume_shadow(p, 'shadow_%s.png' % p['id'])
    if is_tree:
        # every variant of a tree casts its own crown (logic audit of #540, F1): KitPiece.shadow and
        # compose.shadows prefer a variant's own mask; `mask` (the first variant's) stays for readers
        # of the piece as a whole. A tree of one variant keeps its single mask as before.
        deep = any(b in SNOW_BIOMES for b in p.get('biomes') or [])
        if len(p['variants']) > 1:
            for i, v in enumerate(p['variants']):
                vshadow[v['id']] = crown_shadow(v['png'], v.get('foot', foot), 'shadow_%s.png' % p['id'] if i == 0 else
                                                'shadow_%s__%s.png' % (p['id'], v['id']), deep=deep)
            shadow = {'mask': vshadow[p['variants'][0]['id']], 'sun': list(CAST)}
        else:
            v0 = p['variants'][0]
            shadow = {'mask': crown_shadow(v0['png'], v0.get('foot', foot), 'shadow_%s.png' % p['id'], deep=deep),
                      'sun': list(CAST)}
    elif vol:
        shadow = {'mask': vol, 'kind': 'volume', 'sun': list(CAST)}
    elif cs.get('shape') == 'ellipse' and p.get('variants'):
        # by the footprint rule (footprint_shadow), one mask per variant: the placed variant's mask is
        # laid (KitPiece.shadow, compose.shadows), and `mask` (the first variant's) stays for readers of
        # the piece as a whole. The authored ellipse's size and dir are not read: half the sets wrote
        # full widths and the woodland half widths, and both renderers drew them as radii (Z4, 12 Nov)
        for i, v in enumerate(p['variants']):
            vshadow[v['id']] = footprint_shadow(p, v['id'], 'shadow_%s.png' % p['id'] if i == 0 else
                                                'shadow_%s__%s.png' % (p['id'], v['id']))
        shadow = {'mask': vshadow[p['variants'][0]['id']], 'kind': 'footprint', 'rule': shadow_rule(p),
                  'sun': list(CAST)}
    deck = p.get('gameplay', {}).get('deck')
    return {'kind': p['kind'], 'name': p['name'], 'foot': foot, 'collision': rect, 'shadow': shadow,
            'deck': [v * D for v in deck] if deck else None, 'z_sort': g.get('z_sort', 'foot'),
            'blocks_move': p.get('gameplay', {}).get('blocks_move', False),
            'requires': p.get('placement', {}).get('requires', []), 'forbids': p.get('placement', {}).get('forbids', []),
            'size_cells': g.get('size_cells'), 'footprint': g.get('footprint'), 'function': p.get('function', {}), 'story': p.get('story', {}),
            'role': p.get('placement', {}).get('role'), 'snap': p.get('placement', {}).get('snap', 'cell'),
            'approval': p['approval']['state'], 'painted': bool(r.get('paint')),
            **({'collision_circle': radius} if radius else {}),
            **({'sheet_px': g['sheet_px']} if g.get('sheet_px') else {}),
            **({'anim': _anim(r, foot)} if _anim(r, foot) else {}),
            'variants': {v['id']: {'png': v['png'], 'foot': v.get('foot', foot),
                                   **({'shadow': vshadow[v['id']]} if vshadow else {})}
                         for v in p.get('variants', [])}}


def scene(pid: str, e: dict) -> str:
    v0 = next(iter(e['variants'].values()))
    lines = ['[gd_scene format=3]', '',
             '[ext_resource type="Script" path="res://world/terrain/kit_piece.gd" id="1"]',
             '[ext_resource type="Texture2D" path="%s" id="2"]' % v0['png'], '']
    # a box that blocks nobody (gameplay.blocks_move false: a landslip the way system holds shut, a cold
    # fire ring) is kept in the index for the ground's shadow pass and gets no body, so a zone built from
    # these scenes blocks exactly what the walk mask derived from the same records blocks
    solid = e['collision'] if e.get('blocks_move') else None
    circle = e.get('collision_circle') if solid else None
    if circle:
        lines += ['[sub_resource type="CircleShape2D" id="solid"]', 'radius = %g' % circle, '']
    elif solid:
        x, y, w, h = solid
        lines += ['[sub_resource type="RectangleShape2D" id="solid"]', 'size = Vector2(%g, %g)' % (w, h), '']
    lines += ['[node name="%s" type="Node2D"]' % ''.join(s.capitalize() for s in pid.split('_')),
              'script = ExtResource("1")', 'piece_id = "%s"' % pid, '',
              '[node name="Sprite" type="Sprite2D" parent="."]', 'texture = ExtResource("2")', 'centered = false',
              'offset = Vector2(%g, %g)' % (-v0['foot'][0], -v0['foot'][1]), '']
    an = e.get('anim')
    if an:
        # the loop (world/loop_fx.gd: only on screen and while the screen is active, frame 0 under
        # reduced motion). An animal's loop replaces its still (the still stays for the variant
        # picker, the bake and the shadow); a fall's lies over the sheet the bake drew.
        lines[3:3] = ['[ext_resource type="Script" path="res://world/loop_fx.gd" id="3"]',
                      '[ext_resource type="Texture2D" path="%s" id="4"]' % an['strip']]
        if an['cover']:
            i = lines.index('centered = false')
            lines[i:i] = ['visible = false']
        lines += ['[node name="%s" type="Sprite2D" parent="."]' % ('Idle' if an['cover'] else 'Flow'),
                  'script = ExtResource("3")', 'texture = ExtResource("4")', 'centered = false',
                  'offset = Vector2(%g, %g)' % tuple(an['offset']), 'hframes = %d' % an['frames'], 'fps = %g' % an['fps'], '']
    if solid:
        x, y, w, h = solid
        lines += ['[node name="Solid" type="StaticBody2D" parent="."]', 'collision_mask = 0', '',
                  '[node name="Shape" type="CollisionShape2D" parent="Solid"]',
                  'position = Vector2(%g, %g)' % (x + w / 2, y + h / 2), 'shape = SubResource("solid")', '']
    return '\n'.join(lines)


def build(check: bool = False) -> int:
    """Write every prop scene and the index; with check, write nothing and fail if a committed
    scene or the index is not what the pieces make (Claude A, 2 Nov: the index had drifted from
    the pieces since the schema migration)."""
    os.makedirs(OUT, exist_ok=True)
    index, scenes = {}, {}
    for f in piece_files():
        p = json.load(open(f))
        if p['kind'] not in ('prop', 'structure') or not p.get('variants'):
            continue
        e = entry(p)
        index[p['id']] = e
        scenes[p['id'] + '.tscn'] = scene(p['id'], e)
    text = json.dumps(index, indent=1, sort_keys=True)
    if check:
        stale = [n for n, t in scenes.items()
                 if not os.path.exists(os.path.join(OUT, n)) or open(os.path.join(OUT, n)).read() != t]
        if open(os.path.join(OUT, 'index.json')).read().rstrip('\n') != text:
            stale.append('index.json')
        if stale:
            print('props: stale %s (run python3 -m scripts.art.kit.props)' % ', '.join(sorted(stale)))
            return 1
        print('props: %d scenes and the index match the pieces' % len(index))
        return 0
    for n, t in scenes.items():
        open(os.path.join(OUT, n), 'w').write(t)
    open(os.path.join(OUT, 'index.json'), 'w').write(text)
    print('props: %d scenes' % len(index))
    return 0


if __name__ == '__main__':
    sys.exit(build(check='--check' in sys.argv[1:]))

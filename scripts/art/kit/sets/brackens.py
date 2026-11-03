"""The Brackens' drove-road set: what the Drover's Road and its heather ridge need first
(docs/vision/props-backlog.md; docs/vision/regions/home-valley-frostline-brackens.md, sections 2,
3 and 5: "the drove well, sheepfolds and a shepherd's hut along the road", "a broken sheepfold",
"stile and bench", cairns, cold fire rings, carts with a broken wheel, "a peat-cutter's cart",
"a hermit at a fire", gorse at the edges).

    python3 -m scripts.art.kit.sets.brackens            # pictures and pieces (pieces kept unless --force)
    python3 -m scripts.art.kit.sets.brackens --check    # exit 1 if a committed picture is not what this draws

Gritstone country: the stone is buff and brown-grey, dark where it weathers, spotted with pale
green and yellow lichen; the walls are dry (no mortar: dark gaps between the stones), battered
(wider at the foot) and capped with stones set on edge ("cock and hen" coping). Light from the
upper left, the house palette, every piece drawn as solids in the three-quarter view
(sets/_common.py) and closed with each material's own edge tone. Sizes in texels at density 3
(A = 74, a cell 24):

- the drystone wall: 38 to the coping's bed, 44 to 47 over the coping (0.6 A; size-guide "garden
  fence, picket, drystone wall 14 world px (10 to 18)", class fence 41 to 67), 15 thick at the foot
  and 10 at the top. Modular cells in the fence cell model (scripts/art/kit/fences.py): a node in
  the middle of the cell's south line, arms half a cell long; straights (two stone patterns that
  meet the same stones at the cell's ends), four corners, a field gate three cells wide hung on
  two stone stoops, and a step stile (through-stones jutting from the face) where a path crosses.
  Each is drawn inside its neighbourhood and keeps only the texels its own cell wins, so placed
  cells meet without a seam. Style "drystone", enclosing sheep and horses (enclosures.py);
- the drove well: a spring-house of gritstone under a slab roof, its arched mouth on the dark
  water, a spout pouring into a long trough in front where the flocks drink, the overflow running
  off; the trickle loops in 8 frames;
- the shepherd's hut: a one-room stone hut under heather thatch held down by roped stones, a gable
  chimney whose smoke loops in 8 frames (the still has none: the loop lies over it);
- the broken fold: a round fold tumbled to a horseshoe, its stones spilled, nettles in it;
- the stone seat: a gritstone slab on two uprights with a back slab (Drover's Road "stile and bench");
- the cairn: a waymark pile of stones, standing or toppled;
- (the junctions' fingerposts are the village commons' `commons_fingerpost_*`, whose arms point
  along the routes: scripts/art/kit/commons.py);
- the peat stack: cut turves stacked to dry beside a home;
- the broken cart: a peat cart down on one side, its wheel off and broken, turves spilled;
- the fire ring: a ring of stones round ash, cold (a story mark) or lit (a hermit's fire, its flames
  looping in 8 frames; a light, so no outline round the flame);
- gorse: a spiny dark clump with yellow flowers, two shapes.

Moving pieces show a still (frame 0) and a strip beside it (rendering.animations): strip, frames,
fps, played by world/loop_fx.gd only while on screen, held on frame 0 under reduced motion.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.kit.sets import _common as K
from scripts.art.kit.sets._common import C, hsh, rpaint
from scripts.art.native import village as V
from scripts.art.native.palette import FI, to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'brackens')
RES = 'res://kit/props/art/brackens/'
CELL = K.CELL
HALF = CELL // 2
VEC = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}

# gritstone: buff and brown-grey with a warm and a cool weathering
GRIT = [('stone_cool', 'stone_warm', 'ashlar_warm'), ('earth_cool', 'stone_warm', 'ashlar_warm'),
        ('stone_cool', 'stone', 'ashlar'), ('earth_cool', 'earth_warm', 'sand_warm')]
GRIT_DARK = [('soot', 'stone_cool', 'stone'), ('soot', 'earth_cool', 'stone_warm')]
OAK = [('timber_cool', 'timber', 'timber_warm'), ('earth_cool', 'timber', 'timber_warm')]
PEAT = [('soot', 'earth_cool', 'earth'), ('soot', 'earth_cool', 'earth_warm'), ('soot', 'timber_cool', 'earth'), ('earth_cool', 'timber', 'timber_warm')]
LICHEN = (('brass', 4), ('sand_cool', 5), ('grass_warm', 4), ('brass_warm', 4), ('stone_warm', 5))


# ================================================================================================
# the drystone wall
# ================================================================================================
COURSES = (7, 6, 6, 5, 5, 5, 4)            # course heights from the foot (texels)
H_WALL = sum(COURSES)                       # 38 to the coping's bed
HB, HT = 7.5, 5.0                           # half thickness at the foot and at the top
GATE = 3                                    # cells a gate spans
STOOP_X = 36                                # the gate's ends (half its span)
STOOP_W = 9                                 # a stoop's width along the run


def _half(z):
    return HB - (HB - HT) * z / H_WALL


def _course_joints(c, variant):
    """The joints of course c in one cell's period (-12 .. 12 about a node): the stone that
    straddles the cell's east end (shared by every cell and variant) and the interior split."""
    a = 3 + int(hsh(c, 11) * 6)               # its west part, in this cell
    b = 3 + int(hsh(c, 12) * 6)               # its east part, in the next
    lo, hi = HALF - a, HALF + b - CELL        # the straddler: lo .. lo + a + b; the interior hi .. lo
    span = lo - hi
    if span < 11:
        cuts = []
    else:
        f = 0.36 + 0.28 * hsh(c, 13, variant)
        cuts = [hi + round(span * f)]
    return hi, cuts, lo, a + b


def _run_stones(sc, axis, fixed, a0, a1, owner_of, variant_at, base_z=0.0, tag='face'):
    """Lay a run of courses along axis ('x': y = fixed, from x a0 to a1; 'y': x = fixed): each stone
    a rounded lump on both faces of the wall, bulging out of the face by its own amount, so the dark
    hearting shows only where stones meet (a dry joint) and every stone turns from the light."""
    z = base_z
    for c, hc in enumerate(COURSES):
        w = _half(z + hc / 2.0)
        k0 = int(math.floor((a0 + HALF) / CELL)) - 1
        k1 = int(math.ceil((a1 + HALF) / CELL)) + 1
        for k in range(k0, k1 + 1):
            node = k * CELL
            hi, cuts, lo, sw = _course_joints(c, variant_at(node))
            joints = [hi] + cuts + [lo]
            pieces = [(node + j0, node + j1, ('i', c, j0, variant_at(node))) for j0, j1 in zip(joints, joints[1:])]
            pieces.append((node + lo, node + lo + sw, ('e', c)))
            for (s0, s1, key) in pieces:
                u0, u1 = max(s0, a0 - 2), min(s1, a1 + 2)
                if u1 - u0 < 1.5:
                    continue
                for side in (1, -1):
                    kk = hash_key(key + (side,))
                    out = (-0.5, 0.0, 0.4, 0.9)[int(hsh(kk, 1) * 4)]           # proud or set back
                    dh = (-0.8, 0.0, 0.0, 0.7)[int(hsh(kk, 2) * 4)]            # a touch taller or shorter
                    lean = (hsh(kk, 7) - 0.5) * 1.2                           # its middle off-centre
                    base = 2.4 + (hsh(kk, 3) - 0.5) * 1.6 + (0.5 if hsh(kk, 10) > 0.7 else 0.0)
                    um = 0.5 * (s0 + s1) + lean
                    ru = 0.5 * (s1 - s0) + 0.35
                    rz = 0.5 * hc + 0.55 + 0.5 * dh
                    fc = fixed + side * (w - 2.4 + out)
                    if axis == 'x':
                        sc.ellipsoid(um, fc, z + 0.5 * hc + 0.3 * dh, ru, 3.0, rz, K_GRIT, base=base, k=1.5,
                                     owner=owner_of(um, fixed), tag=tag, mix=hsh(kk, 4), flat=3.0)
                    else:
                        sc.ellipsoid(fc, um, z + 0.5 * hc + 0.3 * dh, 3.0, ru, rz, K_GRIT, base=base, k=1.5,
                                     owner=owner_of(fixed, um), tag=tag, mix=hsh(kk, 4), flat=3.0)
        z += hc


K_GRIT = GRIT


def hash_key(key):
    """An integer for a stone's key tuple (kind, course, position ...), stable across runs."""
    h = 0
    for v in key:
        v = {'i': 1, 'e': 2, 'c': 3}.get(v, v) if isinstance(v, str) else int(v)
        h = (h * 1000003 + int(v) + 7919) & 0x7fffffff
    return h


COPE_PATTERN = ((-12, 5, 5), (-7, 4, 3), (-3, 5, 5), (2, 4, 3), (6, 6, 4))   # (start, width, height): 24 in all


def _coping(sc, axis, fixed, a0, a1, owner_of, variant_at, skip=()):
    """Stones on edge along the top, tall ("cocks") and short ("hens") by turns: each a rounded
    slab across the wall, its own tone, a dark gap between."""
    k0 = int(math.floor((a0 + HALF) / CELL)) - 1
    k1 = int(math.ceil((a1 + HALF) / CELL)) + 1
    for k in range(k0, k1 + 1):
        node = k * CELL
        v = variant_at(node)
        for j, (s, w, h) in enumerate(COPE_PATTERN):
            u0, u1 = node + s, node + s + w
            if v and 0 < j < len(COPE_PATTERN) - 1:
                h = h + (1 if j % 2 else -1)
            c0, c1 = max(u0, a0 - 1), min(u1, a1 + 1)
            if c1 - c0 < 1.5 or any(lo <= 0.5 * (c0 + c1) <= hi for lo, hi in skip):
                continue
            kk = hash_key(('c', j, v if 0 < j < len(COPE_PATTERN) - 1 else 0))
            base = 2.6 + (hsh(kk, 5) - 0.5) * 1.4
            um = 0.5 * (u0 + u1) + (hsh(kk, 8) - 0.5)
            ru = 0.5 * w + 0.1
            tilt = (hsh(kk, 9) - 0.5) * 1.6
            if axis == 'x':
                sc.ellipsoid(um, fixed + 0.3 * tilt, H_WALL + 0.2 * h, ru, HT - 0.2, 0.7 * h + 0.6, K_GRIT, base=base, k=1.6,
                             owner=owner_of(um, fixed), tag='cope', mix=hsh(kk, 6), flat=2.5)
            else:
                sc.ellipsoid(fixed + 0.3 * tilt, um, H_WALL + 0.2 * h, HT - 0.2, ru, 0.7 * h + 0.6, K_GRIT, base=base, k=1.6,
                             owner=owner_of(fixed, um), tag='cope', mix=hsh(kk, 6), flat=2.5)


def _hearting(sc, axis, fixed, a0, a1, owner_of):
    """The small stones packed inside the wall: dark, seen only through the joints."""
    if axis == 'x':
        sc.box(a0, fixed - HT + 1, 0, a1, fixed + HT - 1, H_WALL - 0.5, GRIT_DARK, base=1.0, k=0.6,
               owner=owner_of(0.5 * (a0 + a1), fixed), tag='heart')
    else:
        sc.box(fixed - HT + 1, a0, 0, fixed + HT - 1, a1, H_WALL - 0.5, GRIT_DARK, base=1.0, k=0.6,
               owner=owner_of(fixed, 0.5 * (a0 + a1)), tag='heart')


def wall_scene(links, me_box, variant=0, pad=64, gate=False):
    """A Scene of drystone runs: links are ((x0, y0), (x1, y1)) between nodes (texels about the
    piece's node); me_box the ground box (x0, y0, x1, y1) this piece owns."""
    sc = K.Scene(-pad, pad, -pad, pad, 72)

    def owner_of(x, y):
        bx0, by0, bx1, by1 = me_box
        return 0 if (bx0 <= x < bx1 and by0 <= y < by1) else 1

    def variant_at(node):
        return variant if node == 0 else 0

    # merge collinear links into runs, extended past a corner node by the wall's half thickness
    nodes = {}
    for (a, b) in links:
        for p, q in ((a, b), (b, a)):
            nodes.setdefault(p, set()).add((int(np.sign(q[0] - p[0])), int(np.sign(q[1] - p[1]))))
    runs = []
    seen = set()
    for (a, b) in links:
        if (a, b) in seen:
            continue
        axis = 'x' if a[1] == b[1] else 'y'
        chain = {a, b}
        changed = True
        while changed:
            changed = False
            for (p, q) in links:
                if (p, q) in seen:
                    continue
                same = (axis == 'x' and p[1] == q[1] == a[1]) or (axis == 'y' and p[0] == q[0] == a[0])
                if same and (p in chain or q in chain):
                    chain |= {p, q}
                    seen.add((p, q))
                    changed = True
        seen.add((a, b))
        us = sorted(c[0] if axis == 'x' else c[1] for c in chain)
        fixed = a[1] if axis == 'x' else a[0]
        ends = []
        for u, sgn in ((us[0], -1), (us[-1], 1)):
            node = (u, fixed) if axis == 'x' else (fixed, u)
            perp = any(d[0] == 0 for d in nodes[node]) if axis == 'x' else any(d[1] == 0 for d in nodes[node])
            cap = node in gate_ends(gate)
            ends.append(u + sgn * (HB if perp and not cap else 0.0))
        runs.append((axis, fixed, ends[0], ends[1]))
    for axis, fixed, a0, a1 in runs:
        _hearting(sc, axis, fixed, a0, a1, owner_of)
        _run_stones(sc, axis, fixed, a0, a1, owner_of, variant_at)
    # the coping: along each run, and a flat capstone over a corner or a tee
    corners = [n for n, ds in nodes.items() if any(d[0] == 0 for d in ds) and any(d[1] == 0 for d in ds)]
    for axis, fixed, a0, a1 in runs:
        skip = []
        for (nx, ny) in corners:
            if axis == 'x' and ny == fixed:
                skip.append((nx - HT - 1, nx + HT + 1))
            if axis == 'y' and nx == fixed:
                skip.append((ny - HT - 1, ny + HT + 1))
        _coping(sc, axis, fixed, a0, a1, owner_of, variant_at, skip)
    for (nx, ny) in corners:
        sc.ellipsoid(nx + 0.4, ny, H_WALL + 1.5, HT + 1.6, HT + 1.4, 5.0, K_GRIT, base=2.8, k=1.9,
                     owner=owner_of(nx, ny), tag='cope', mix=0.3)
    return sc


def gate_ends(gate):
    return {(-STOOP_X, 0), (STOOP_X, 0)} if gate else set()


def _dress_wall(sc, a):
    """Lichen on the lit stones, moss in the low joints and on the coping's north side, grass
    tufts along the foot; each mark tied to its stone, so a stone two cells share looks the same
    in both."""
    lab = sc.label
    for i, s in enumerate(sc.solids):
        if s.tag not in ('face', 'cope', 'stoop'):
            continue
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 6:
            continue
        hk = hsh(i if s.tag == 'stoop' else hash_key(tuple(int(round(v * 2)) % 48 for v in s.p[:6])), 21)
        top = ys.min()
        sel = (ys <= top + 2)
        if hk < 0.42:
            k = int(hk * 1000) % max(1, sel.sum())
            y, x = ys[sel][k], xs[sel][k]
            fam, t = LICHEN[int(hk * 97) % len(LICHEN)]
            for dy, dx in ((0, 0), (0, 1), (1, 0)) if hk < 0.2 else ((0, 0), (0, 1)):
                yy, xx = y + dy + 1, x + dx
                if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and lab[yy, xx] == i:
                    a[yy, xx] = C(fam, t)
        elif s.tag == 'face' and s.p[2] < 12 and hk > 0.78:
            bot = ys.max()
            sel = ys >= bot - 1
            k = int(hk * 1000) % max(1, sel.sum())
            y, x = ys[sel][k], xs[sel][k]
            for dx in range(3):
                if x + dx < a.shape[1] and lab[y, x + dx] == i:
                    a[y, x + dx] = C('leaf_cool', 2 + (dx == 1))
    return a


def _tufts(sc, a, own, runs_x, me):
    """Grass tufts at the foot of the south face (the turf meets the wall), periodic along x."""
    for (fixed, a0, a1) in runs_x:
        yb = sc.oy + int(fixed + HB)               # the canvas row of the foot's front edge
        for x in range(int(math.floor(a0)), int(math.ceil(a1))):
            u = x % CELL
            h = hsh(u, 31)
            if h > 0.3 or not me[0] <= x + 0.5 < me[2]:
                continue
            cx = x + sc.ox
            ht = 2 + int(hsh(u, 32) * 4)
            for k in range(ht):
                yy = yb + 1 - k
                xx = cx + (1 if k > 2 and hsh(u, 33) > 0.5 else 0)
                if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]:
                    a[yy, xx] = C('grass' if k > 0 else 'grass_cool', 2 + min(3, k))


def render_wall(joins=None, gate=False, stile=False, variant=0):
    """(Pic, owned) for one wall cell (joins), the gate (three cells along x) or the stile."""
    links = []
    if gate:
        for sgn in (-1, 1):
            for k in range(3):
                x0 = sgn * (STOOP_X + k * CELL)
                links.append(((x0, 0), (x0 + sgn * CELL, 0)))
        me = (-STOOP_X, -HALF, STOOP_X, HALF)
    else:
        js = joins if not stile else ['e', 'w']
        for s in js:
            dx, dy = VEC[s]
            for k in range(3):
                links.append(((dx * CELL * k, dy * CELL * k), (dx * CELL * (k + 1), dy * CELL * (k + 1))))
        me = (-HALF, -HALF, HALF, HALF)
    links = [((int(a[0]), int(a[1])), (int(b[0]), int(b[1]))) for a, b in links]
    sc = wall_scene(links, me, variant=variant, pad=96 if gate else 64, gate=gate)
    if gate:
        _stoops(sc)
    a = K.modular(sc, me, dress=_dress_wall)
    own = np.where(a >= 0, 0, -1)
    if gate:
        runs_x = [(0, -96, -STOOP_X + STOOP_W), (0, STOOP_X - STOOP_W, 96)]
    elif stile or set(joins) & {'e', 'w'}:
        xs = [0.0] + ([-96] if (stile or 'w' in joins) else []) + ([96] if (stile or 'e' in joins) else [])
        runs_x = [(0, min(xs), max(xs))]
    else:
        runs_x = []
    over = np.full(a.shape, -1, np.int32)
    if gate:
        _gate_leaf(sc, over)
    if stile:
        _stile_steps(sc, a, over)
    if (over >= 0).any():
        o2 = over.copy()
        V.outline(o2)
        a = np.where(over >= 0, over, np.where((o2 >= 0) & (a < 0), o2, a))
    _tufts(sc, a, own, runs_x, me)
    return K.crop(a, sc.ox, sc.oy)


def _stoops(sc):
    """The gate's two stoops: tall dressed gateposts at the opening's ends, the wall built into
    them, an iron hanging eye on the west one and a latch on the east."""
    for sgn in (-1, 1):
        x0 = sgn * STOOP_X if sgn < 0 else STOOP_X - STOOP_W
        x1 = x0 + STOOP_W
        sc.box(x0, -5.5, 0, x1, 5.5, 54, K_GRIT, base=2.7, k=1.7, owner=0, tag='stoop', round_=2.5, mix=0.15 if sgn < 0 else 0.4)
        sc.box(x0 - 0.5, -6.5, 0, x1 + 0.5, 6.5, 7, K_GRIT, base=2.6, k=1.4, owner=0, tag='stoop', round_=1.0, mix=0.6)


def _gate_leaf(sc, a):
    """A five-bar field gate of oak between the stoops, shut: two stiles, five rails, a diagonal
    brace from the hanging foot to the latch head, iron straps and a ring latch; drawn on its plane
    (y = 0 along the run), over the turf seen through it."""
    oy, ox = sc.oy, sc.ox
    xa, xb = -STOOP_X + STOOP_W + 1, STOOP_X - STOOP_W - 1
    zs = [6, 14, 22, 30, 38]
    H_, W_ = a.shape
    paint = np.zeros((H_, W_), bool)
    tone = np.zeros((H_, W_), float)

    def put(x0, x1, z0, z1, t, lit_top=True):
        r0, r1 = oy - int(z1), oy - int(z0)
        c0, c1 = ox + int(x0), ox + int(x1)
        paint[r0:r1, c0:c1] = True
        tone[r0:r1, c0:c1] = t
        if lit_top:
            tone[r0, c0:c1] = t + 1.2
        tone[r1 - 1, c0:c1] = t - 1.0
    for z in zs:
        put(xa, xb, z, z + 3, 3.1)
    for (x0, x1, t) in ((xa, xa + 4, 3.6), (xb - 3, xb, 2.6), ((xa + xb) // 2 - 1, (xa + xb) // 2 + 2, 3.0)):
        put(x0, x1, 4, 42, t, lit_top=True)
        tone[oy - 42:oy - 4, ox + int(x0)] = t + 0.8
    # the brace: from the hanging foot up to the head at the middle upright
    for k in range(0, (xb - xa) // 2):
        x = xa + 3 + k
        z = 8 + k * (30.0 / ((xb - xa) / 2))
        r = oy - int(z)
        paint[r - 2:r + 1, ox + x:ox + x + 2] = True
        tone[r - 2:r + 1, ox + x:ox + x + 2] = 3.3
        tone[r - 2, ox + x:ox + x + 2] = 4.2
    m = paint
    grain = np.array([[hsh(xx, yy, 41) for xx in range(W_)] for yy in range(H_)])
    rpaint(a, m, OAK, tone + (grain - 0.5) * 0.9, grain)
    # iron: straps at the hanging stile, a ring latch at the shutting stile
    for z in (12, 34):
        a[oy - z - 1:oy - z + 1, ox + xa - 1:ox + xa + 6] = C('iron', 2)
        a[oy - z - 1, ox + xa - 1:ox + xa + 6] = C('iron', 4)
    a[oy - 28:oy - 24, ox + xb - 2:ox + xb + 1] = C('iron', 3)
    a[oy - 27, ox + xb - 3] = C('iron', 1)


def _stile_steps(sc, base, a):
    """Three through-stones jutting from the face as steps, climbing west to east (drawn into the
    overlay a), their shadows on the face below, and the coping worn pale where feet go over it
    (on the wall's own picture, base)."""
    oy, ox = sc.oy, sc.ox
    steps = [(-10, -3, 11), (-3, 4, 22), (4, 11, 33)]
    cols = np.arange(a.shape[1])[None, :] + np.zeros((a.shape[0], 1))
    for (x0, x1, z) in steps:
        y0, y1 = HB - 1, HB + 6                       # out from the face
        r_top0, r_top1 = oy + int(y0 - z - 2), oy + int(y1 - z - 2)
        r_fr1 = oy + int(y1 - z + 1)
        top = np.zeros(a.shape, bool)
        front = np.zeros(a.shape, bool)
        top[r_top0:r_top1, ox + x0:ox + x1] = True
        front[r_top1:r_fr1, ox + x0:ox + x1] = True
        rpaint(a, top, GRIT, 3.8 + 0.8 * (cols < ox + x0 + 2) - 0.8 * (cols >= ox + x1 - 1), 0.2)
        rpaint(a, front, GRIT, 2.2 - 0.6 * (cols >= ox + x1 - 2), 0.2)
        a[r_top0, ox + x0 + 1:ox + x1 - 1] = C('ashlar_warm', 5)
        a[r_fr1 - 1, ox + x0 + 1:ox + x1] = C('soot', 1)
        sh = np.zeros(a.shape, bool)
        sh[r_fr1:r_fr1 + 3, ox + x0 + 2:ox + x1 + 1] = True
        V._step(base, sh & (base >= 0), -1)
    m = np.zeros(base.shape, bool)
    for i, s_ in enumerate(sc.solids):
        if s_.tag == 'cope' and -7 <= s_.p[0] <= 9:
            m |= sc.label == i
    V._step(base, m & (sc.n[..., 2] > 0.5) & (base >= 0), 1)


# ================================================================================================
# single props
# ================================================================================================
def _solo(sc, dress=None, line=True):
    """A single prop's picture: render, shade, marks, no lone texels, the outline."""
    sc.render()
    a = sc.shade()
    if dress:
        dress(sc, a)
    V.tidy(a)
    if line:
        V.outline(a)
        V.tidy(a, passes=1)
    return a


def _lichen(sc, a, tags=('stone',), rate=0.45, seed=0):
    """Lichen spots on the lit tops of stones, moss low on a few; each mark tied to its stone."""
    lab = sc.label
    for i, s in enumerate(sc.solids):
        if s.tag not in tags:
            continue
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 8:
            continue
        hk = hsh(i, seed, 23)
        top = ys.min()
        sel = ys <= top + 2
        if hk < rate:
            k = int(hk * 997) % max(1, sel.sum())
            y, x = ys[sel][k] + 1, xs[sel][k]
            fam, t = LICHEN[int(hk * 89) % len(LICHEN)]
            for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1))[:2 + int(hk * 10) % 3]:
                if 0 <= y + dy < a.shape[0] and 0 <= x + dx < a.shape[1] and lab[y + dy, x + dx] == i:
                    a[y + dy, x + dx] = C(fam, t)
        elif hk > 0.82:
            bot = ys.max()
            sel = ys >= bot - 1
            k = int(hk * 991) % max(1, sel.sum())
            y, x = ys[sel][k], xs[sel][k]
            for dx in range(3):
                if 0 <= x + dx < a.shape[1] and lab[y, x + dx] == i:
                    a[y, x + dx] = C('leaf_cool', 2 + (dx == 1))


def _ground_tufts(a, ox, oy, xs, seed, fam='grass'):
    """Grass tufts standing at the foot, at ground x positions xs (texels from the foot)."""
    for j, x in enumerate(xs):
        h = 2 + int(hsh(seed, j, 3) * 4)
        lean = 1 if hsh(seed, j, 4) > 0.5 else -1
        for k in range(h):
            yy = oy - k + int(hsh(seed, j, 5) * 2)
            xx = ox + int(x) + (lean if k >= h - 1 and h > 3 else 0)
            if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]:
                a[yy, xx] = C(fam if k else fam + '_cool', 2 + min(3, k))


def stone_pile(sc, rings, seed, tag='stone', sets=GRIT, base=2.7, flat=1.6, spill=None):
    """Stones laid in rings, each ring smaller and higher: (radius, count, z, stone size, squash)."""
    rng = np.random.default_rng(seed)
    for r, n, z, size, sq in rings:
        a0 = rng.uniform(0, 2 * math.pi)
        for k in range(n):
            ang = a0 + 2 * math.pi * k / max(1, n) + rng.uniform(-0.25, 0.25)
            rx = size * rng.uniform(0.8, 1.2)
            ry = rx * rng.uniform(0.65, 0.9)
            rz = size * sq * rng.uniform(0.75, 1.1)
            sc.ellipsoid(r * math.cos(ang) + rng.uniform(-1, 1), r * 0.8 * math.sin(ang) + rng.uniform(-1, 1), z + rz * 0.7,
                         rx, ry, rz, sets, base=base + rng.uniform(-0.7, 0.7), k=1.7, tag=tag, mix=rng.random(), flat=flat, tex='stone')
    for (x, y, size) in spill or []:
        sc.ellipsoid(x, y, size * 0.45, size, size * 0.75, size * 0.55, sets, base=base + rng.uniform(-0.5, 0.5), k=1.7, tag=tag,
                     mix=rng.random(), flat=flat)


def cairn(toppled=False, seed=3):
    """A waymark cairn: rounded gritstone laid in shrinking rings, a long stone set upright on top;
    or the same pile tumbled, its top stones spilled to the east and lying in the grass."""
    sc = K.Scene(-40, 44, -30, 20, 80)
    if not toppled:
        rings = [(11.0, 8, 0.0, 6.0, 0.55), (8.0, 6, 7.0, 5.4, 0.55), (5.5, 5, 13.5, 4.8, 0.6), (3.0, 4, 19.5, 4.2, 0.6),
                 (1.0, 2, 25.0, 3.8, 0.65)]
        stone_pile(sc, rings, seed, flat=1.8)
        sc.ellipsoid(0.5, -0.5, 36.0, 3.2, 2.6, 9.0, GRIT, base=3.0, k=1.9, tag='stone', mix=0.55, flat=1.7)   # the waymark
    else:
        rings = [(11.0, 8, 0.0, 6.0, 0.55), (8.0, 6, 6.5, 5.2, 0.5), (4.0, 3, 12.0, 4.6, 0.55)]
        stone_pile(sc, rings, seed + 1, flat=1.8,
                   spill=[(19, 4, 4.2), (25, -3, 3.6), (14, 9, 3.4), (30, 6, 3.0), (-15, 8, 3.2)])
        sc.box(16, -6, 0, 34, 0, 5, GRIT, base=2.8, k=1.6, tag='stone', round_=2.2, mix=0.55)          # the waymark lying
    a = _solo(sc, dress=lambda s, a: _lichen(s, a, rate=0.5, seed=seed))
    _ground_tufts(a, sc.ox, sc.oy + 2, [-12, -6, 9, 14] if not toppled else [-12, 8, 37], seed)
    return K.crop(a, sc.ox, sc.oy)


def _bench_marks(sc, a, seed):
    """Lichen rosettes and moss on a big slab: several per stone, in clusters, more on the lit tops."""
    H, W = a.shape
    for i, s in enumerate(sc.solids):
        ys, xs = np.nonzero(sc.label == i)
        for j in range(max(2, len(ys) // 70)):
            k = int(hsh(seed, i, j, 5) * len(ys)) % len(ys)
            y, x = ys[k], xs[k]
            fam, t = LICHEN[int(hsh(seed, i, j, 6) * len(LICHEN)) % len(LICHEN)]
            if sc.n[y, x, 2] < 0.4 and hsh(seed, i, j, 7) > 0.5:
                fam, t = ('leaf_cool', 2) if hsh(seed, i, j, 8) > 0.5 else ('grass_cool', 3)
            for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1), (0, 2))[:2 + int(hsh(seed, i, j, 9) * 4)]:
                if y + dy < H and x + dx < W and sc.label[y + dy, x + dx] == i:
                    a[y + dy, x + dx] = C(fam, t - (1 if dy and dx else 0))


def bench(seed=7):
    """A drovers' seat: a long gritstone slab on two uprights, two rough back slabs set in the
    ground behind it, pitted and lichened, the grass grown up round the uprights."""
    sc = K.Scene(-56, 56, -30, 24, 70)
    mx = K.noise((sc.H, sc.W), np.random.default_rng(seed), 1.8)            # weathering: buff, grey, brown by patches
    sc.ellipsoid(-22, -9.5, 18, 22, 3.2, 21, GRIT, base=2.6, k=1.6, tag='stone', mix=mx, flat=3.5, tex='stone')
    sc.ellipsoid(22, -9.8, 16.5, 21, 3.2, 19.5, GRIT, base=2.5, k=1.6, tag='stone', mix=mx, flat=3.5, tex='stone')
    for x0, x1 in ((-38, -28), (28, 38)):
        sc.box(x0, -5, 0, x1, 4, 17, GRIT, base=2.4, k=1.6, tag='stone', round_=1.5, mix=mx, tex='stone')
    sc.ellipsoid(0, -0.5, 20, 46, 6.5, 3.4, GRIT, base=2.8, k=1.7, tag='stone', mix=mx, flat=4.0, tex='stone')
    a = _solo(sc, dress=lambda s, a: _bench_marks(s, a, seed))
    _ground_tufts(a, sc.ox, sc.oy + 4, [-39, -36, -27, 27, 30, 37, 40], seed)
    return K.crop(a, sc.ox, sc.oy)


def peat_stack(seed=9):
    """Cut turves stacked to dry beside a home: brick-like and fibrous, laid in shrinking courses
    on a herringbone with the courses crossing, a few on top leaning."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-50, 50, -40, 24, 60)
    mx = K.noise((sc.H, sc.W), rng, 1.4)
    layers = [(6, 0.0, 30), (5, 4.5, 26), (5, 9.0, 22), (4, 13.5, 18), (3, 18.0, 13), (2, 22.5, 8)]
    for li, (n, z, half) in enumerate(layers):
        for row in range(2):
            y0 = -16 + row * 9 + li * 0.8
            xs = np.linspace(-half, half, n + 1)
            for k in range(n):
                x0, x1 = xs[k] + rng.uniform(0, 0.8), xs[k + 1] - rng.uniform(0.4, 1.2)
                sc.box(x0, y0 + rng.uniform(-0.6, 0.6), z, x1, y0 + 8 + rng.uniform(-0.6, 0.6), z + 4.4,
                       PEAT, base=2.5 + rng.uniform(-0.6, 0.7), k=1.6, tag='turf', round_=1.2, mix=mx, tex='turf')
    for (x, z) in ((-6, 27.0), (5, 27.0)):
        sc.box(x - 4, -10, z, x + 4, -2, z + 4, PEAT, base=2.7, k=1.6, tag='turf', round_=1.2, mix=rng.random())
    a = _solo(sc)
    # fibres: pale roots and heather stalks in the cut faces, dark peat crumbs
    H, W = a.shape
    for i, s in enumerate(sc.solids):
        ys, xs = np.nonzero(sc.label == i)
        for j in range(len(ys) // 9):
            k = int(hsh(i, j, 71) * len(ys)) % len(ys)
            y, x = ys[k], xs[k]
            fam = ('timber_warm', 3) if hsh(i, j, 72) > 0.5 else ('soot', 1)
            a[y, x] = C(*fam)
            if hsh(i, j, 73) > 0.6 and x + 1 < W and sc.label[y, x + 1] == i:
                a[y, x + 1] = C(*fam)
    V.outline(a)
    V.tidy(a, passes=1)
    _ground_tufts(a, sc.ox, sc.oy + 1, [-31, -26, 22, 29], seed)
    return K.crop(a, sc.ox, sc.oy)


def _wheel(a, cx, cy, r, broken, seed, behind=False):
    """A spoked cart wheel face-on (its plane square to the view): an iron-shod oak rim, a hub,
    eight spokes (some snapped off when broken); behind=True paints only where nothing is drawn."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    d = np.hypot(X - cx, Y - cy)
    ang = np.arctan2(Y - cy, X - cx)
    rim = (d <= r) & (d > r - 3)
    tyre = (d <= r) & (d > r - 1.2)
    hub = d <= 3.2
    spoke = np.zeros((H, W), bool)
    for k in range(8):
        th = k * math.pi / 4 + 0.2
        if broken and k in (1, 2, 5):
            continue
        reach = r - 2 if not (broken and k == 6) else r * 0.45
        dd = np.abs(np.sin(ang - th)) * d
        spoke |= (dd <= 0.9) & (d <= reach) & (np.cos(ang - th) > 0)
    if broken:
        gap = (np.abs(((ang - 0.9) + math.pi) % (2 * math.pi) - math.pi) < 0.55)
        rim &= ~gap
        tyre &= ~gap
    m = rim | hub | spoke
    if behind:
        m &= a < 0
    t = 3.0 - 1.2 * ((X - cx) > 0) + 1.0 * ((Y - cy) < -r * 0.5) - 0.8 * ((Y - cy) > r * 0.5)
    rpaint(a, m & ~tyre, OAK, t - (0.8 if behind else 0), 0.3)
    a[(tyre if not behind else tyre & (a < 0)) & ~hub] = C('iron', 2)
    a[hub & (d <= 1.5) & m] = C('iron', 4)


def cart_broken(seed=11):
    """A peat cart broken down at the roadside: its bed of boards propped on a stone where the near
    wheel came off, the far wheel standing behind it, the shafts let down to the grass, the broken
    wheel lying flat with snapped spokes, turves spilled from the tail."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-56, 64, -40, 30, 60)
    sc.ellipsoid(-10, 6, 5, 7, 5, 6, GRIT, base=2.6, k=1.7, tag='stone', mix=0.4, flat=1.6)          # the prop stone
    # the bed: floor boards and side boards
    sc.box(-32, -12, 10, 20, 8, 13, OAK, base=2.8, k=1.5, tag='wood', round_=0.8, mix=0.2, tex='wood')
    for k, x0 in enumerate(range(-32, 20, 7)):
        sc.box(x0, 6, 10, x0 + 6.4, 8.5, 22, OAK, base=2.9 + (0.4 if k % 2 else -0.2), k=1.4, tag='board', round_=0.6,
               mix=hsh(k, 81), tex='wood_v')
    sc.box(-32, -13, 10, 20, -10.5, 22, OAK, base=2.5, k=1.4, tag='board', round_=0.6, mix=0.7, tex='wood')
    sc.box(-34, -13, 10, -31.5, 8.5, 23, OAK, base=2.6, k=1.4, tag='board', round_=0.6, mix=0.5)
    sc.box(18, -13, 10, 20.5, 8.5, 23, OAK, base=2.4, k=1.4, tag='board', round_=0.6, mix=0.5)
    # turves still in the bed, and spilled from the tail
    for k in range(6):
        x = -29 + k * 7.5 + rng.uniform(-1, 1)
        sc.box(x, -8 + rng.uniform(-1, 1), 13, x + 6.5, -1 + rng.uniform(-1, 1), 17.5 + rng.uniform(0, 1.5), PEAT, base=2.6,
               k=1.5, tag='turf', round_=1.2, mix=rng.random())
    for (x, y, z) in ((-44, 4, 0), (-50, 12, 0), (-41, 14, 0), (-46, 8, 4)):
        sc.box(x, y, z, x + 7, y + 4.5, z + 4, PEAT, base=2.5, k=1.5, tag='turf', round_=1.2, mix=rng.random())
    # the shafts, let down to the ground
    for y in (-9, 4):
        sc.box(20, y, 0, 58, y + 2.4, 3, OAK, base=3.0, k=1.5, tag='wood', round_=0.8, mix=0.25, tex='wood')
    sc.render()
    a = sc.shade()
    _lichen(sc, a, tags=('stone',), rate=1.0, seed=seed)
    # the far wheel standing behind the bed; the broken one lying flat in front
    _wheel(a, sc.ox - 6, sc.oy - 13 - 14, 14, broken=False, seed=seed, behind=True)
    _wheel(a, sc.ox + 34, sc.oy + 16, 13, broken=True, seed=seed)
    V.tidy(a)
    V.outline(a)
    V.tidy(a, passes=1)
    _ground_tufts(a, sc.ox, sc.oy + 1, [-24, 12, 46, 54], seed)
    return K.crop(a, sc.ox, sc.oy)


FIRE_FRAMES = 8


def _flames(a, cx, base_y, i, seed, scale=1.0):
    """One frame of a small wood fire's flames (a light: no outline): tongues rising and swaying on a
    loop of FIRE_FRAMES drawings, embers spitting up."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    t = i / FIRE_FRAMES
    level = np.zeros((H, W), int)
    tongues = [(-5, 11, 0.0), (-1, 17, 1.9), (3, 14, 3.6), (6, 9, 5.1), (-8, 7, 2.6)]
    for (dx, h, ph) in tongues:
        hh = scale * (h * (0.8 + 0.2 * math.sin(2 * math.pi * t + ph)) + 1.5 * math.sin(4 * math.pi * t + ph * 1.3))
        sway = 1.4 * math.sin(2 * math.pi * t + ph * 0.7)
        for lv, shrink in ((1, 0.0), (2, 0.2), (3, 0.45), (4, 0.7)):
            ht = hh * (1 - shrink)
            if ht < 2:
                continue
            rel = np.clip((Y - (base_y - ht)) / max(ht, 1e-3), 0, 1)
            half = (3.6 - 2.4 * shrink) * scale * np.sqrt(rel)
            m = (Y >= base_y - ht) & (Y <= base_y) & (np.abs(X - (cx + dx * scale + sway * (1 - rel))) <= half)
            level = np.where(m, np.maximum(level, lv), level)
    cols = {1: ('lava', 2), 2: ('lava', 3), 3: ('lamp', 4), 4: ('lamp', 5)}
    for lv, (f, tt) in cols.items():
        a[level == lv] = C(f, tt)
    for k in range(2):
        p = (t + k * 0.5) % 1.0
        sx = int(cx + 4 * math.sin(2 * math.pi * (p + k * 0.3)) + (k * 5 - 2))
        sy = int(base_y - 16 * scale - p * 14)
        if 0 <= sy < H and 0 <= sx < W:
            a[sy, sx] = C('lamp', 5 if k else 4)


def fire_ring(lit=False, seed=13):
    """A ring of gritstones round a fire bed: cold (grey ash, black charcoal, a half-burnt brand) or
    lit (a hermit's fire: three logs crossed, embers glowing, the flames looping)."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-30, 30, -26, 22, 46)
    sc.ellipsoid(0, -2, -0.3, 11, 9, 1.4, [('soot', 'ash', 'ash'), ('soot', 'stone_cool', 'ash')], base=2.4, k=1.0, tag='ash', mix=0.3)
    n = 10
    for k in range(n):
        ang = 2 * math.pi * k / n + rng.uniform(-0.15, 0.15)
        r = rng.uniform(12.5, 14.0)
        sz = rng.uniform(3.6, 4.6)
        sc.ellipsoid(r * math.cos(ang), -2 + r * 0.85 * math.sin(ang), sz * 0.45, sz, sz * 0.8, sz * 0.75, GRIT,
                     base=2.6 + rng.uniform(-0.6, 0.6), k=1.7, tag='stone', mix=rng.random(), flat=1.5)
    if lit:
        logs = [(-8, -4, 7, -1, 0), (-2, -9, 1, 4, 1), (-6, 1, 6, 3.5, 2)]
    else:
        logs = [(-7, -3, 5, -0.5, 0), (2, -7, 5, 2, 1)]
    for (x0, y0, x1, y1, k) in logs:
        if abs(x1 - x0) >= abs(y1 - y0):
            sc.box(min(x0, x1), min(y0, y1) - 1.2, 0.5, max(x0, x1), min(y0, y1) + 1.6, 3.4,
                   [('soot', 'soot', 'timber_cool'), ('soot', 'timber_cool', 'timber')], base=1.8, k=1.2, tag='log', round_=1.0, mix=0.3 * k)
        else:
            sc.box(min(x0, x1) - 1.4, min(y0, y1), 0.5, min(x0, x1) + 1.4, max(y0, y1), 3.4,
                   [('soot', 'soot', 'timber_cool')], base=1.8, k=1.2, tag='log', round_=1.0, mix=0.5)
    sc.render()
    a = sc.shade()
    _lichen(sc, a, tags=('stone',), rate=0.6, seed=seed)
    ash = sc.label == 0
    H, W = a.shape
    for j in range(40):
        y, x = int(hsh(seed, j, 91) * H), int(hsh(seed, j, 92) * W)
        if ash[y, x]:
            a[y, x] = C('soot', 0) if hsh(seed, j, 93) > 0.4 else C('ash', 4)
    if lit:
        logs_m = np.isin(sc.label, [i for i, s in enumerate(sc.solids) if s.tag == 'log'])
        for j in range(60):
            y, x = int(hsh(seed, j, 94) * H), int(hsh(seed, j, 95) * W)
            if logs_m[y, x] or (ash[y, x] and hsh(seed, j, 96) > 0.6):
                a[y, x] = C('lava', 3) if hsh(seed, j, 97) > 0.3 else C('lamp', 4)
    V.tidy(a)
    V.outline(a)
    V.tidy(a, passes=1)
    _ground_tufts(a, sc.ox, sc.oy + 6, [-17, -14, 15, 18], seed)
    if not lit:
        return K.crop(a, sc.ox, sc.oy)
    frames = []
    for i in range(FIRE_FRAMES):
        f = a.copy()
        _flames(f, sc.ox - 0.5, sc.oy - 4, i, seed)
        frames.append(f)
    ys, xs = np.nonzero(np.any([f >= 0 for f in frames], axis=0))
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    pics = []
    for f in frames:
        p = V.Pic(x1 - x0, y1 - y0, sc.ox - x0, sc.oy - y0)
        p.a[:] = f[y0:y1, x0:x1]
        pics.append(p)
    return pics[0], {'frames': pics, 'fps': 8.0, 'clip': 'burn'}


def _leaf_marks(X, Y, seed, w=6, h=4):
    """A leaf-stamp texture: staggered rows of small clumps, each lit on its crown and dark at its
    U-shaped lower rim (-1 .. 1)."""
    row = np.floor(Y / h)
    xx = X + (row % 2) * (w / 2) + (hsh(seed, 1) * w)
    u = (xx % w) / w - 0.5
    v = (Y % h) / h
    cup = (u * 2) ** 2 * 0.6 + v
    return np.where(cup > 1.05, -1.0, np.where(v < 0.3, 0.8, 0.0))


def gorse(variant='a', seed=17):
    """A gorse clump at density 3 as the woodland's bushes are drawn (art-style, "Density 3"): a few
    large domes, each built of leaf clumps lit on their upper west with a dark under-shade where a
    clump tucks under the one in front; spines as dark flecks and pale glints; yellow flowers in
    small clusters on the lit crowns; spines breaking the silhouette only; no stems."""
    rng = np.random.default_rng(seed + (0 if variant == 'a' else 50))
    sc = K.Scene(-48, 48, -40, 20, 70)
    G = [('leaf_cool', 'leaf_cool', 'leaf'), ('grass_cool', 'leaf_cool', 'leaf'), ('leaf_cool', 'grass_cool', 'grass')]
    domes = ([(-13, -7, 13, 12, 9, 13), (10, -9, 14, 13, 9, 15), (-1, -17, 15, 12, 8, 16), (-21, 2, 8, 8, 6, 9),
              (17, 1, 9, 9, 6, 10), (1, 0, 10, 11, 7, 11)] if variant == 'a' else
             [(-8, -5, 11, 11, 8, 12), (9, -4, 10, 10, 8, 11), (0, -12, 12, 10, 8, 14), (-1, 2, 9, 9, 6, 9)])
    for (x, y, z, rx, ry, rz) in domes:
        for j in range(9):
            th = rng.uniform(0, 2 * math.pi)
            ph = rng.uniform(0.15, 1.3)
            cx = x + rx * 0.7 * math.cos(th) * math.cos(ph)
            cy = y + ry * 0.7 * math.sin(th) * math.cos(ph)
            cz = z * 0.55 + rz * 0.7 * math.sin(ph)
            r = rng.uniform(4.6, 6.4)
            sc.ellipsoid(cx, cy, cz, r, r * 0.85, r * 0.9, G, base=2.1 + 0.5 * math.sin(ph) + rng.uniform(-0.3, 0.3), k=1.6,
                         tag='clump', mix=rng.random())
        sc.ellipsoid(x, y, z * 0.55, rx * 0.85, ry * 0.85, rz * 0.8, G, base=1.4, k=1.4, tag='core', mix=0.3)
    sc.render()
    a = sc.shade(crevice=2, rim=0.8)
    H, W = a.shape
    m = sc.label >= 0
    L = sc.light()
    for j in range(int(m.sum() * 0.08)):
        y, x = int(hsh(seed, j, 1) * H), int(hsh(seed, j, 2) * W)
        if m[y, x] and x + 1 < W:
            if hsh(seed, j, 3) > 0.5:
                a[y, x] = C('leaf_cool', 1)
                if m[y + 1, x + 1] if y + 1 < H else False:
                    a[y + 1, x + 1] = C('leaf_cool', 1)
            elif L[y, x] > 0.2:
                a[y, x] = C('grass', 4)
                a[y, x + 1] = C('grass_warm', 4) if m[y, x + 1] else a[y, x + 1]
    lit = m & (L > 0.3)
    k = 0
    for j in range(600):
        y, x = int(hsh(seed, j, 11) * H), int(hsh(seed, j, 12) * W)
        if lit[y, x] and k < (30 if variant == 'a' else 20):
            k += 1
            cl = ((0, 0), (0, 1), (1, 0)) if hsh(seed, j, 13) > 0.4 else ((0, 0), (1, 1), (0, 1), (1, 0))
            for dy, dx in cl:
                if 0 <= y + dy < H and 0 <= x + dx < W and m[y + dy, x + dx]:
                    a[y + dy, x + dx] = C('brass_warm', 4) if (dy, dx) != (0, 0) else C('lamp', 4)
            if y + 2 < H and m[y + 2, x]:
                a[y + 2, x] = C('brass', 2)
    edge = m & ~np.roll(m, 1, 0)
    ys, xs = np.nonzero(edge)
    for j in range(len(ys)):
        if hsh(seed, j, 21) < 0.22 and ys[j] > 2:
            a[ys[j] - 1, xs[j]] = C('leaf_cool', 2)
            if hsh(seed, j, 22) < 0.4:
                a[ys[j] - 2, xs[j] + (1 if hsh(seed, j, 23) > 0.5 else -1)] = C('leaf_cool', 2)
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)


def fold_ruin(seed=19):
    """A broken sheepfold: a round fold of drystone tumbled to a horseshoe, its back still standing
    and coped in places, its front gone to footings and spilled stones, nettles growing inside."""
    rng = np.random.default_rng(seed)
    R, cy = 44.0, -46.0
    sc = K.Scene(-64, 64, -100, 24, 70)
    n_c = [(0, 7), (7, 6), (13, 6), (19, 5)]
    for ci, (z, hc) in enumerate(n_c):
        circ = 2 * math.pi * R
        n = int(circ / rng.uniform(8.5, 10.5))
        off = rng.uniform(0, 2 * math.pi)
        for k in range(n):
            th = off + 2 * math.pi * k / n
            south = math.sin(th)                       # 1 at the front (south), -1 at the back
            hcap = 4 + 16 * (0.5 - 0.5 * south) ** 1.2 + rng.uniform(-4, 3)
            if math.cos(th) > 0.55 and south > -0.2:
                hcap = min(hcap, 5)                    # the east side tumbled to its footings
            if south > 0.75 and math.cos(th) < 0.1:
                continue                               # the old gateway, a gap
            if z + hc * 0.5 > hcap:
                continue
            for side in (1, -1):
                rr = R + side * (4.5 - 0.06 * z)
                x, y = rr * math.cos(th), cy + rr * 0.92 * math.sin(th)
                ru = 0.5 * circ / n + 0.4
                sc.ellipsoid(x, y, z + 0.5 * hc, abs(ru * math.sin(th)) + 2.6, abs(ru * math.cos(th)) + 2.6, 0.5 * hc + 0.6,
                             GRIT, base=2.4 + rng.uniform(-0.8, 0.8), k=1.6, tag='stone', mix=rng.random(), flat=2.2)
    # the floor inside, trodden bare where the flock stood, grass coming back at its edge
    sc.ellipsoid(0, cy + 2, -1.2, R - 4, (R - 4) * 0.92, 1.8, [('grass_cool', 'grass_cool', 'grass'), ('earth_cool', 'earth', 'grass')],
                 base=2.9, k=0.5, tag='floor', mix=0.2, tex='turf')
    # spilled stones in the gaps and the grass round them
    for _ in range(16):
        th = rng.uniform(0.0, math.pi)
        rr = R + rng.uniform(-10, 12)
        sz = rng.uniform(3.2, 5.2)
        sc.ellipsoid(rr * math.cos(th), cy + rr * 0.92 * math.sin(th), sz * 0.4, sz, sz * 0.75, sz * 0.55, GRIT,
                     base=2.5 + rng.uniform(-0.6, 0.6), k=1.7, tag='stone', mix=rng.random(), flat=1.6)
    # nettles inside, against the back wall
    NET = [('leaf_cool', 'leaf', 'grass'), ('grass_cool', 'leaf', 'leaf_warm')]
    for (x, y) in ((-16, cy - 20), (-6, cy - 24), (8, cy - 22), (20, cy - 16), (-24, cy - 12)):
        sc.ellipsoid(x, y, 5, 6.5, 4.5, 6, NET, base=2.4, k=1.9, tag='nettle', mix=rng.random())
    sc.render()
    a = sc.shade()
    _lichen(sc, a, tags=('stone',), rate=0.35, seed=seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W] + 0.5
    fl = sc.label == [i for i, s_ in enumerate(sc.solids) if s_.tag == 'floor'][0]
    worn = fl & (K.noise(a.shape, np.random.default_rng(seed + 5), 2.2) > 0.55)
    rpaint(a, worn, [('earth_cool', 'earth', 'earth_warm')], 2.4 + 0.8 * (K.vhash(Xg.astype(int) // 2, Yg.astype(int), 3) > 0.8), 0.0)
    for i, s in enumerate(sc.solids):
        if s.tag == 'nettle':
            mi = sc.label == i
            marks = _leaf_marks(Xg, Yg, seed + i, w=4, h=3)
            rpaint(a, mi, NET, s.base + s.k * sc.light() + 0.8 * marks, s.mix)
    V.tidy(a)
    V.outline(a)
    V.tidy(a, passes=1)
    _ground_tufts(a, sc.ox, sc.oy + 2, [-38, -30, -20, 22, 31, 40], seed)
    return K.crop(a, sc.ox, sc.oy)


WELL_FRAMES = 8


def drove_well(seed=23):
    """The drove well: a spring-house of drystone under stepped slab roofing, an arched mouth over
    the dark water, a stone spout pouring into a long trough where the flocks drink, the overflow
    running off east through the trodden mud; the trickle and the trough's rings loop."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-60, 60, -60, 30, 80)
    # the house: front, sides and back as drystone runs (the front's stones leave the arch open)
    zc = 0.0
    for c, hc in enumerate(COURSES[:6]):
        for (axis, fixed, u0, u1) in (('x', -12.0, -26, 26), ('x', -30.0, -26, 26), ('y', -26.0, -30, -12), ('y', 26.0, -30, -12)):
            u = u0
            j = 0
            while u < u1:
                L = 6 + int(hsh(c, j, axis == 'x', int(fixed), 31) * 7)
                s0, s1 = u, min(u + L, u1)
                u = s1
                j += 1
                um = 0.5 * (s0 + s1)
                if axis == 'x' and fixed == -12.0 and abs(um) < 8 and zc < 26:
                    continue
                if axis == 'x':
                    sc.ellipsoid(um, fixed + 1.2, zc + hc * 0.5, 0.5 * (s1 - s0) + 0.4, 3.0, 0.5 * hc + 0.6, GRIT,
                                 base=2.5 + (hsh(c, j, 32) - 0.5) * 1.4, k=1.5, tag='stone', mix=hsh(c, j, 33), flat=3.0)
                else:
                    sc.ellipsoid(fixed, um, zc + hc * 0.5, 3.0, 0.5 * (s1 - s0) + 0.4, 0.5 * hc + 0.6, GRIT,
                                 base=2.5 + (hsh(c, j, 34) - 0.5) * 1.4, k=1.5, tag='stone', mix=hsh(c, j, 35), flat=3.0)
        zc += hc
    # the dark inside (seen through the arch), the lintel over the mouth
    sc.box(-24, -28, 0, 24, -14, zc - 1, GRIT_DARK, base=0.6, k=0.3, tag='dark')
    sc.box(-11, -15, 24, 11, -9, 31, GRIT, base=2.9, k=1.7, tag='stone', round_=1.8, mix=0.2, tex='stone')
    # the roof: slabs stepping in, a ridge stone
    for j, (hw, d0, d1) in enumerate(((31, -34, -7), (25, -31, -9), (19, -29, -11), (13, -27, -13))):
        for kx, x0 in enumerate(range(-hw, hw, 9)):
            x1 = min(hw, x0 + 9)
            sc.box(x0 + 0.4, d0, zc + 4 * j, x1 - 0.4, d1, zc + 4 * j + 4.4, GRIT, base=2.4 + 0.3 * j + (hsh(j, kx, 41) - 0.5),
                   k=1.6, tag='slab', round_=1.4, mix=hsh(j, kx, 42), tex='stone')
    sc.ellipsoid(0, -20, zc + 17, 8, 5, 3.0, GRIT, base=2.8, k=1.8, tag='slab', mix=0.3, flat=2.0)
    # the spout and the trough
    sc.box(-2.5, -11, 18, 2.5, -4, 21, GRIT, base=3.0, k=1.6, tag='stone', round_=1.0, mix=0.4)
    sc.box(-34, -5, 0, 34, 9, 13, GRIT, base=2.7, k=1.7, tag='trough', round_=2.0, mix=0.3, tex='stone')
    sc.render()
    a = sc.shade()
    _lichen(sc, a, tags=('stone', 'slab', 'trough'), rate=0.55, seed=seed)
    H, W = a.shape
    oy, ox = sc.oy, sc.ox
    # water in the trough (inset from its rim) and inside the arch
    tw = np.zeros((H, W), bool)
    tw[oy + int(-3 - 13):oy + int(7 - 13), ox - 32:ox + 32] = True
    Yg, Xg = np.mgrid[0:H, 0:W]
    depth_t = (Yg - (oy - 16)) / 10.0
    rpaint(a, tw, [('water_cool', 'water', 'water_warm')], 1.4 + 1.6 * depth_t - 0.5 * (Xg > ox + 18), 0.0)
    a[oy - 16, ox - 31:ox + 31] = C('stone_cool', 1)            # the inner rim's shadow on the water
    for gx in (ox - 22, ox - 21, ox + 9):
        a[oy - 12, gx] = C('sky', 5)
    aw = np.zeros((H, W), bool)
    aw[oy - 14 - 6:oy - 14, ox - 7:ox + 7] = True
    aw &= sc.label == [i for i, s in enumerate(sc.solids) if s.tag == 'dark'][0]
    rpaint(a, aw, [('water_cool', 'water_cool', 'water')], 1.0, 0.0)
    a[oy - 16, ox - 4:ox - 1] = C('water', 3)
    # the overflow: trodden mud and a puddle at the trough's east end
    mud = (((Xg - (ox + 37)) / 7.0) ** 2 + ((Yg - (oy + 9)) / 3.4) ** 2 <= 1) & (a < 0)
    rpaint(a, mud, [('earth_cool', 'earth', 'earth_warm')], 2.0 + 0.9 * (K.vhash(Xg // 2, Yg, 5) > 0.75), 0.0)
    pud = mud & (((Xg - (ox + 38)) / 4.0) ** 2 + ((Yg - (oy + 9)) / 1.8) ** 2 <= 1)
    rpaint(a, pud, [('water_cool', 'water', 'water_warm')], 2.6 - 0.8 * (Yg < oy + 9), 0.0)
    V.tidy(a)
    V.outline(a)
    V.tidy(a, passes=1)
    _ground_tufts(a, ox, oy + 9, [-36, -33, 38, 52], seed)
    frames = []
    for i in range(WELL_FRAMES):
        f = a.copy()
        t = i / WELL_FRAMES
        # the trickle: from the spout's lip to the water, its light moving down the fall
        x0, y_top, y_bot = ox, oy - 4 - 21 + 2, oy - 13 - 1
        for y in range(y_top, y_bot):
            ph = ((y - y_top) / 3.0 - t * 2.67) % 1.0
            f[y, x0 - 1] = C('water', 3)
            f[y, x0] = C('water_warm', 5) if ph < 0.34 else C('water', 4)
        # rings spreading where it falls, and a glint wandering along the runnel
        r = 1 + int(t * 6)
        for dx in range(-r, r + 1):
            if abs(dx) >= r - 1:
                f[y_bot + 1, x0 + dx] = C('water_warm', 4) if r < 5 else C('water', 3)
        f[oy + 9, ox + 36 + (i % 4)] = C('sky', 5)
        frames.append(f)
    ys, xs = np.nonzero(np.any([f >= 0 for f in frames], axis=0))
    x0_, x1_, y0_, y1_ = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    pics = []
    for f in frames:
        p = V.Pic(x1_ - x0_, y1_ - y0_, ox - x0_, oy - y0_)
        p.a[:] = f[y0_:y1_, x0_:x1_]
        pics.append(p)
    return pics[0], {'frames': pics, 'fps': 8.0, 'clip': 'trickle'}


SMOKE_FRAMES = 8
SMOKE_BOX = (40, 64)                    # the smoke's loop region, w x h texels, its foot at the pot


def _smoke_frame(i, seed):
    """One frame of a peat fire's smoke from the hut's pot: three puffs a third of a cycle apart,
    rising, growing and leaning east, lit on their upper west, fading to a broken checker as they
    thin."""
    W, H = SMOKE_BOX
    a = np.full((H, W), -1, np.int32)
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    for k in range(3):
        p = ((i / SMOKE_FRAMES) + k / 3.0) % 1.0
        r = 2.6 + 6.0 * p
        cx = 8 + 14 * p + 2.0 * math.sin(2 * math.pi * p + k)
        cy = H - 3 - 54 * p
        d2 = ((X - cx) / r) ** 2 + ((Y - cy) / (r * 0.85)) ** 2
        m = d2 <= 1
        lam = -((X - cx) / r) * 0.6 - ((Y - cy) / r) * 0.6
        t = 3.2 + 1.3 * lam - 0.6 * (d2 > 0.6) + 0.8 * p
        fam = np.where(t < 2.6, FI['soot'], FI['ash'])
        tt = np.clip(np.round(np.where(t < 2.6, t + 1.5, t)), 1, 5).astype(int)
        thin = p > 0.55
        if thin:
            m &= ((X.astype(int) + Y.astype(int) + i) % 2 == 0) | (d2 < 0.35 * (1.1 - p))
        if p > 0.85:
            m &= (X.astype(int) * 3 + Y.astype(int)) % 4 == 0
        a[m] = (fam * 8 + tt)[m]
    return a


def shepherds_hut(seed=29):
    """The shepherd's hut on the Drover's Road: one room of gritstone under a heather thatch held
    down by ropes weighted with stones, a gable chimney; drawn with the village's house painter
    (scripts/art/native/houses.py) for the walls, door, window and roof's form, its materials the
    Brackens' own. The smoke from the pot loops over it (the still has none)."""
    from scripts.art.native import houses as HS
    spec = {'kind': 'hut', 'w': 58, 'depth': 40, 'wall': 'stone', 'wall_h': 34, 'roof': 'thatch', 'roof_h': 24, 'door': 17,
            'door_w': 15, 'door_h': 26, 'windows': [41], 'win_w': 11, 'win_h': 11, 'win_top': 27, 'chimney': [50],
            'chimney_h': 10, 'paint': 'timber', 'shutters': False}
    b = HS.building(spec, seed=seed)
    p = b.base
    a = p.a
    rm = b.info['roof']
    fam = a // 8
    tone = a % 8
    rng = np.random.default_rng(seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    # heather thatch: the straw's tones recoloured dark brown and heather-purple, a step darker
    straw = (a >= 0) & np.isin(fam, [FI[f] for f in ('sand', 'sand_warm', 'sand_cool', 'brass', 'brass_warm', 'plaster_warm')]) & rm
    n = K.noise(a.shape, rng, 1.6)
    t2 = np.clip(tone - 1, 0, 5)
    n2 = K.noise(a.shape, np.random.default_rng(seed + 1), 4.0)
    heather = np.where(t2 >= 4, np.where(n2 > 0.5, FI['sand_cool'], FI['earth_warm']),
                       np.where(t2 <= 1, np.where(n2 > 0.5, FI['timber_cool'], FI['earth_cool']),
                                np.where(n2 > 0.55, FI['earth'], FI['timber'])))
    a[straw] = (heather * 8 + np.where(t2 <= 5, t2, 5))[straw]
    # the heather's dry flower heads in small clusters, and moss creeping up from the eave
    eave = b.info.get('y_eave', b.info['y_e'])
    fl = straw & (K.noise(a.shape, np.random.default_rng(seed + 6), 1.0) > 0.8) & (Yg < eave - 6)
    a[fl] = np.where(tone[fl] >= 3, C('berry_cool', 3), C('berry_cool', 2))
    moss = straw & (Yg > eave - 22) & (K.noise(a.shape, np.random.default_rng(seed + 3), 2.0) > 0.68)
    a[moss] = np.where(tone[moss] >= 3, C('leaf', 3), C('leaf_cool', 2))
    a[moss & (K.vhash(Xg, Yg, seed + 4) > 0.8)] = C('grass_warm', 4)
    # gritstone walls: the house's grey stone turned buff and brown
    stone = (a >= 0) & np.isin(fam, [FI[f] for f in ('stone', 'stone_cool', 'stone_warm')])
    n3 = K.noise(a.shape, np.random.default_rng(seed + 2), 2.5)
    gm = np.where(tone >= 4, np.where(n3 > 0.5, FI['ashlar_warm'], np.where(n > 0.5, FI['stone_warm'], FI['sand_cool'])),
                  np.where(tone <= 1, np.where(n3 > 0.5, FI['earth_cool'], FI['stone_cool']),
                           np.where(n3 > 0.62, FI['earth_warm'], np.where(n > 0.5, FI['stone_warm'], FI['stone']))))
    a[stone] = (gm * 8 + tone)[stone]
    # ropes over the thatch, weighted with stones along the eave
    y_r, y_e = b.info['y_r'], b.info.get('y_eave', b.info['y_e'])
    rx0, rx1 = b.info['rx']
    for k, x in enumerate(range(int(rx0) + 14, int(rx1) - 6, 22)):
        for y in range(int(y_r) + 6, int(y_e) + 1):
            xx = x + (y - y_r) // 6
            if 0 <= xx < W and rm[y, xx] and a[y, xx] >= 0 and (y + k) % 3:
                a[y, xx] = C('timber_cool', 1)
                if xx + 1 < W and rm[y, xx + 1]:
                    a[y, xx + 1] = C('timber_warm', 3)
        sx = x + (int(y_e) - int(y_r)) // 6
        m = V.ellipse_mask(a.shape, sx + 0.5, y_e + 4.5, 3.2, 2.6)
        rpaint(a, m, GRIT, 3.6 - 1.4 * (Yg > y_e + 4) - 0.8 * (Xg > sx + 1), 0.3)
    V.outline(a)
    # the canvas grows up and east for the smoke loop over the pot (the still has no smoke)
    cxp = b.info['L'] + V.q(50)
    top = int(y_r - V.q(10))
    sw, sh = SMOKE_BOX
    up = max(0, sh - top + 2)
    east = max(0, cxp - 6 + sw - W)
    q_ = V.Pic(W + east, H + up, p.ax, p.ay + up)
    q_.a[up:, :W] = a
    region = (cxp - 6, top + up - sh, sw, sh)
    frames = [V.Pic(sw, sh, 0, sh) for _ in range(SMOKE_FRAMES)]
    for i, fr in enumerate(frames):
        fr.a[:] = _smoke_frame(i, seed)
    return q_, {'frames': frames, 'fps': 6.0, 'clip': 'smoke', 'region': region}


# ================================================================================================
# the pieces
# ================================================================================================
def _fp(cols, rows):
    xs = range(-(cols // 2), cols - cols // 2)
    return [[c, -r] for r in range(rows, 0, -1) for c in xs]


def _rel(rel, what, cells=None, note=None):
    r = {'rel': rel, 'what': what}
    if cells is not None:
        r['cells'] = cells
    if note:
        r['note'] = note
    return r


OFF_ROUTE = {'rel': 'on', 'what': 'route'}
OFF_WATER = {'rel': 'on', 'what': 'water'}
BIOMES = ['brackens', 'valley']
STANDARD = "art-style.md (Eastward's level of detail), placement-logic.md"


def _piece(pid, name, variants, size, cells, purpose, role, *, collision, fp, requires=(), forbids=(), enclosure=None,
           boundary=None, anim=None, shadow=(10, 3), blocks=True, size_class=None, eastward=None, note='', height=None,
           composition=None, interact=None, story=None, fn=None, extra=None):
    pl = {'snap': 'cell', 'purpose': purpose, 'role': role}
    pl.update(extra or {})
    if composition:
        pl['composition'] = composition
    if requires:
        pl['requires'] = list(requires)
    if forbids:
        pl['forbids'] = list(forbids)
    if boundary:
        pl['boundary'] = boundary
    if enclosure:
        pl['enclosure'] = enclosure
    rendering = {'cast_shadow': {'shape': 'ellipse', 'size': list(shadow), 'dir': [1, 1]} if shadow else {'shape': 'none'},
                 'contact_ao': True}
    if anim:
        rendering['animations'] = [anim]
    return {
        'schema': 'napattack.piece/1', 'id': pid, 'name': name, 'kind': 'prop', 'biomes': list(BIOMES), 'version': 1,
        'variants': [{'id': vid, 'weight': w, 'png': RES + png, 'foot': list(foot)} for (vid, w, png, foot) in variants],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': STANDARD, 'note': note},
        'geometry': {'size_px': list(size), 'size_cells': list(cells), 'z_sort': 'foot', 'height_px': int(height or size[1]),
                     'collision': collision, 'foot': list(variants[0][3]), 'footprint': fp},
        'placement': pl,
        'rendering': rendering,
        'function': {'interact': interact} if interact else {},
        'story': story or {'owner': None},
        'gameplay': {'blocks_move': blocks, 'blocks_shots': False},
        'audit': {'size_class': size_class, 'eastward_ref': eastward,
                  'painter': {'module': 'scripts.art.kit.sets.brackens', 'fn': fn or pid, 'args': {}},
                  'seeded_from': 'scripts/art/kit/sets/brackens.py', 'todo': []},
    }


def _wall_collision(js):
    """The wall's solid line in world px from the foot: its arms, the wall's foot half thickness
    (2.5 world px) either side."""
    x0 = -4.0 if 'w' in js else -2.5
    x1 = 4.0 if 'e' in js else 2.5
    y0 = -4.0 if 'n' in js else -2.5
    y1 = 4.0 if 's' in js else 2.5
    return {'shape': 'rect', 'rect': [x0, y0, x1 - x0, y1 - y0]}


WALL_CELLS = ('ew', 'ns', 'es', 'sw', 'ne', 'nw')
WALL_NAMES = {'ew': 'straight along x', 'ns': 'straight along y', 'es': 'corner (east and south)', 'sw': 'corner (south and west)',
              'ne': 'corner (north and east)', 'nw': 'corner (north and west)'}
ENCLOSES = ['sheep', 'horses', 'cattle']
WALL_EW = '12 (the drystone and boulder walls by the thatched hut), 17 (the farm fence and gate, 40 E = 0.75 A)'


def wall_jobs():
    """(piece id, [(variant id, Pic thunk)], piece kwargs) for every wall piece."""
    jobs = []
    for jn in WALL_CELLS:
        js = list(jn)
        vs = [('a' if jn == 'ew' else 'plain', lambda js=js: render_wall(js, variant=0))]
        if jn == 'ew':
            vs.append(('b', lambda js=js: render_wall(js, variant=1)))
        jobs.append(('wall_drystone_' + jn, vs, dict(
            name='Drystone wall, ' + WALL_NAMES[jn], purpose='contain', role='boundary', cells=(1, 1), fp=[[0, -1]],
            collision=_wall_collision(js), forbids=[OFF_ROUTE, OFF_WATER], composition='edge',
            boundary={'style': 'drystone', 'joins': js, 'gate': False, 'span_cells': 1, 'encloses': ENCLOSES},
            shadow=(9, 3), size_class='fence (size-guide: drystone wall 14 world px, 10 to 18)', eastward=WALL_EW, height=47,
            fn='render_wall', note='A gritstone wall cell: closes a fold with its neighbours (enclosures.py); dry joints, cock-and-hen coping.')))
    jobs.append(('wall_drystone_gate_ew', [('shut', lambda: render_wall(gate=True))], dict(
        name='Drystone wall, field gate along x', purpose='contain', role='gate', cells=(3, 1), fp=[[-1, -1], [0, -1], [1, -1]],
        collision={'shape': 'none'}, blocks=False, composition='edge',
        requires=[_rel('on', 'route', note='a gate stands where the path its owner walks crosses the wall (placement-logic rule 2)')],
        boundary={'style': 'drystone', 'joins': ['e', 'w'], 'gate': True, 'span_cells': GATE, 'encloses': ENCLOSES},
        interact={'verb': 'open', 'triggers': []}, shadow=(22, 3), height=54,
        size_class='fence (a field gate 1 m, between stoops 1.2 m: size-guide "field gate 32 to 48 wide so a cart passes")',
        eastward=WALL_EW, fn='render_wall', note='A five-bar oak gate hung on two gritstone stoops, shut: it keeps the flock in.')))
    jobs.append(('wall_drystone_stile_ew', [('steps', lambda: render_wall(stile=True))], dict(
        name='Drystone wall, step stile along x', purpose='cross', role='stile', cells=(1, 1), fp=[[0, -1]],
        collision={'shape': 'none'}, blocks=False, composition='edge',
        requires=[_rel('on', 'route', note='a stile carries a footpath over the wall; the flock stays behind it')],
        boundary={'style': 'drystone', 'joins': ['e', 'w'], 'gate': False, 'span_cells': 1, 'encloses': ENCLOSES, 'stile': True},
        shadow=(9, 3), height=47, size_class='fence (the wall) with steps 11, 22 and 33 up (stair pitch 12 to 22)',
        eastward=WALL_EW + '; 13 (the farm stair, 12 E a step)', fn='render_wall',
        note='Three through-stones jut from the face as steps; walkers cross, sheep do not (a closed wall to enclosures.py).')))
    return jobs


# ================================================================================================
# building and checking
# ================================================================================================
NATURE = [OFF_ROUTE, OFF_WATER]
EW_RURAL = '12 (the thatched hut, its bench, lantern post and stepping stones), 17 (the farm: cart, barrels, fence)'


def prop_jobs():
    """(piece id, [(variant id, thunk)], piece kwargs) for the single props."""
    return [
        ('brackens_drove_well', [('still', lambda: drove_well())], dict(
            name='Drove well', purpose='water', role='well', cells=(5, 3), fp=_fp(5, 2),
            collision={'shape': 'rect', 'rect': [-12.0, -13.0, 24, 16]}, shadow=(26, 5), composition='edge',
            requires=[_rel('near', 'route', 2, 'beside the drove road, where the flocks are watered on the way')],
            forbids=[OFF_ROUTE, _rel('not_near', 'water', 4, 'a spring is walled where there is no stream to drink from')],
            extra={'provides': ['feature', 'water']},
            size_class='well (89 to 141 tall, 70 to 118 wide)', eastward=EW_RURAL + '; 13 (the bell frame, 1.1 A)',
            note='A spring-house over the well and a trough in front; the trickle and rings loop (8 frames).')),
        ('brackens_shepherds_hut', [('still', lambda: shepherds_hut())], dict(
            name="Shepherd's hut", purpose='live', role='house', cells=(9, 6), fp=_fp(8, 5),
            collision={'shape': 'rect', 'rect': [-29.0, -36.0, 58, 36]}, shadow=(56, 8), composition='edge',
            requires=[_rel('near', 'route', 3, 'beside the Drover\'s Road, its door on the trod')], forbids=NATURE,
            extra={'provides': ['home', 'hearth']},
            size_class='hut (148 to 252 tall, 178 to 296 wide; size-guide "stone refuge, shepherd\'s bothy: as a hut")',
            eastward='12 (the thatched hut: 2.5 A to the ridge, 3 A wide)',
            note='One room of gritstone under roped heather thatch; the chimney\'s smoke loops (8 frames) over the still.')),
        ('brackens_fold_ruin', [('still', lambda: fold_ruin())], dict(
            name='Broken sheepfold', purpose='mark', role='ruin', cells=(5, 4), fp=[[c, -4] for c in range(-2, 3)],
            collision={'shape': 'rect', 'rect': [-12.0, -29.0, 24, 5]}, shadow=(28, 4), composition='free',
            requires=[_rel('near', 'route', 4, 'a fold stood by the drove road; its ruin still does')], forbids=NATURE,
            extra={'provides': ['feature', 'view']},
            size_class='ruin (a fold 4 to 5 cells across, walls to 34 at the back; size-guide drystone wall 14 world px)',
            eastward=WALL_EW, note='A round fold tumbled to a horseshoe: the back stands, the front is footings and spilled stones.')),
        ('brackens_bench', [('still', lambda: bench())], dict(
            name='Drovers\' seat', purpose='rest', role='seat', cells=(4, 1), fp=_fp(4, 1),
            collision={'shape': 'rect', 'rect': [-15.0, -4.0, 30, 4]}, shadow=(30, 4), composition='edge',
            requires=[_rel('near', 'route', 2, 'beside the road, facing it and the view (size-guide: a bench faces a view or a feature)')],
            extra={'faces': {'what': ['feature', 'view', 'water', 'lower'], 'cells': 6,
                             'note': 'a seat looks at something: across the road to a cairn, a ruin or a well'}},
            forbids=NATURE, size_class='bench (37 to 68 tall, 70 to 107 wide)', eastward='12 and 38 (the bench, 1.2 x 0.87 A)',
            note='A gritstone slab on two uprights, two back slabs set in the ground behind it.')),
        ('brackens_cairn', [('standing', lambda: cairn(False)), ('toppled', lambda: cairn(True))], dict(
            name='Cairn', purpose='guide', role='marker', cells=(2, 2), fp=_fp(2, 1),
            collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 4]}, shadow=(12, 3), composition='edge',
            requires=[_rel('near', 'route', 2, 'a waymark beside the trail, one every 64 to 96 world px along a high way')],
            extra={'provides': ['feature']},
            forbids=NATURE, size_class='cairn (size-guide: 12 to 28 tall, 12 to 24 wide in world px)', eastward='13 (the boulder, 0.35 x 0.42 A); 12 (the cliff\'s stones)',
            note='A waymark of stones in shrinking rings, a long stone upright on top; or tumbled, its top stones spilled east.')),
        ('brackens_peat_stack', [('still', lambda: peat_stack())], dict(
            name='Peat stack', purpose='store', role='store', cells=(3, 2), fp=_fp(3, 1),
            collision={'shape': 'rect', 'rect': [-10.0, -6.0, 20, 6]}, shadow=(22, 4), composition='edge',
            requires=[_rel('within', 'house', 3, 'fuel stacked to dry by the hut it warms')], forbids=NATURE,
            extra={'needs': [{'what': 'hearth', 'cells': 3, 'note': 'peat for a fire: by a home with a chimney'}]},
            size_class='pile (18 to 52 tall, 33 to 89 wide)', eastward='17 (the farm\'s stacked bales and logs)',
            note='Cut turves stacked to dry in shrinking courses.')),
        ('brackens_cart_broken', [('still', lambda: cart_broken())], dict(
            name='Peat cart with a broken wheel', purpose='mark', role='story', cells=(5, 2), fp=_fp(4, 1),
            collision={'shape': 'rect', 'rect': [-11.0, -5.0, 22, 6]}, shadow=(28, 4), composition='edge',
            requires=[_rel('near', 'route', 2, 'it broke down on the road and was pulled to the verge')], forbids=NATURE,
            size_class='cart (52 to 89 tall, 67 to 126 wide)', eastward='04 (the stall cart, 0.9 x 1.4 A), 17 (the farm cart)',
            note='The story slot "cart with a broken wheel": the bed propped on a stone, the wheel lying broken, turves spilled.')),
        ('brackens_fire_ring_cold', [('still', lambda: fire_ring(False))], dict(
            name='Cold fire ring', purpose='mark', role='story', cells=(2, 2), fp=_fp(2, 2),
            collision={'shape': 'rect', 'rect': [-5.0, -6.0, 10, 6]}, shadow=None, blocks=False, composition='free',
            forbids=NATURE, size_class='fire ring (a ring of stones 1.5 m across)', eastward='05 and 37 (the camp fires)',
            note='The story slot "cold fire ring": stones round grey ash and charcoal, a half-burnt brand.')),
        ('brackens_fire_ring_lit', [('still', lambda: fire_ring(True))], dict(
            name="Hermit's fire", purpose='light', role='hearth', cells=(2, 2), fp=_fp(2, 2),
            collision={'shape': 'rect', 'rect': [-5.0, -6.0, 10, 6]}, shadow=None, composition='free',
            requires=[_rel('near', 'route', 6, 'at the end of a side trod off the road (a secret pocket)')], forbids=NATURE,
            size_class='fire ring with flames to 0.4 A', eastward='05 and 37 (the camp fires, their glow)',
            note='A small wood fire in a ring of stones; the flames loop (8 frames), held still under reduced motion.')),
        ('brackens_gorse', [('a', lambda: gorse('a')), ('b', lambda: gorse('b'))], dict(
            name='Gorse', purpose='grow', role='shrub', cells=(3, 1), fp=_fp(3, 1),
            collision={'shape': 'rect', 'rect': [-10.0, -5.0, 20, 5]}, shadow=(18, 4), composition='cluster',
            forbids=NATURE, size_class='bush (41 to 81 tall, 44 to 115 wide)', eastward='12 and 38 (bushes, 0.7 to 0.93 A tall)',
            note='A gorse clump at the moor\'s edge (a fade clump for grass and fields, size-guide boundaries).')),
    ]


def jobs():
    return wall_jobs() + prop_jobs()


def build(write=True, force=False, only=None):
    out = {}
    pieces = []
    for pid, vs, kw in jobs():
        if only and pid not in only:
            continue
        pics = []
        for vid, thunk in vs:
            r = thunk()
            frames = None
            if isinstance(r, tuple):
                r, frames = r
            pics.append((vid, r, frames))
            png = '%s_%s.png' % (pid, vid) if len(vs) > 1 or vid not in ('still',) else pid + '.png'
            out[os.path.join(ART, png)] = to_rgba(r.a)
            if frames:
                out[os.path.join(ART, png[:-4] + '_loop.png')] = to_rgba(K.strip(frames['frames']))
        kw = dict(kw)
        name, purpose, role = kw.pop('name'), kw.pop('purpose'), kw.pop('role')
        cells, fp = kw.pop('cells'), kw.pop('fp')
        variants = []
        for vid, r, frames in pics:
            png = '%s_%s.png' % (pid, vid) if len(vs) > 1 or vid not in ('still',) else pid + '.png'
            variants.append((vid, 1.0 if len(variants) == 0 else 0.6, png, (r.ax, r.ay)))
            if frames:
                f0 = frames['frames'][0]
                anim = {'clip': frames['clip'], 'loop': True, 'frames': len(frames['frames']), 'fps': frames['fps'],
                        'strip': RES + png[:-4] + '_loop.png', 'frame_px': [f0.W, f0.H], 'reduced_motion': 'hold:0',
                        'on_screen_only': True}
                if frames.get('region'):
                    anim['region_px'] = list(frames['region'])
                kw['anim'] = anim
        size = (max(r.W for _v, r, _f in pics), max(r.H for _v, r, _f in pics))
        pieces.append(_piece(pid, name, variants, size, cells, purpose, role, fp=fp, **kw))
    if write:
        os.makedirs(ART, exist_ok=True)
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        for pc in pieces:
            path = os.path.join(PIECES, 'prop', pc['id'] + '.json')
            if force or not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump(pc, f, indent=1)
                    f.write('\n')
    return out


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('brackens: stale pictures %s (run python3 -m scripts.art.kit.sets.brackens)' % ', '.join(bad[:6]))
        return 1
    print('brackens: pictures current')
    return 0


# purpose, role and verdict for scripts/art/kit/placement_audit.py (None keeps the piece's own
# requires and forbids, as the farm's rows do)
AUDIT = {pid: (kw['purpose'], kw['role'], None, None, 'fine', 'Brackens set (scripts/art/kit/sets/brackens.py): ' + kw['note'])
         for pid, _vs, kw in jobs()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    print('brackens: %d pictures' % len(build(force=a.force)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""The Act 1 set (docs/vision/props-backlog.md, "The Act 1 set"): the props the first act's route
needs where its scenes come first in play, drawn to the Brackens bar (scripts/art/kit/sets/
brackens.py, whose renderer and helpers it shares).

- **Driftwood quay and the lighthouse**: a net rack hung with net, lobster pots, a mooring bitt, a
  clinker boat upturned on the shingle, a buoy that bobs (8 frames), the harbour light whose lamp
  glows (8 frames);
- **the Halt**: platform edge cells, a waiting shelter, a milk-churn stand, a semaphore signal, a
  platform lamp whose flame flickers (8 frames), a timetable board in pictograms;
- **the Millrace landslip**: an undershot mill wheel that turns (8 frames), a sluice gate, spare
  millstones in the miller's yard, the landslip itself, a broken rail fence;
- **Old Fang's barrow**: its entrance (a portal of stones into a turf mound) and kerb stones;
- **beehives**: a white WBC hive and a straw skep on its stone stool.

The asset ledger's REWORK pieces (`prop/net_rack`, `prop/lobster_pots`, `prop/buoy`, `prop/beehive`,
`prop/skep`, `prop/signal_box`, `prop/semaphore`) are redrawn here, not patched.

    python3 -m scripts.art.kit.sets.act1            # paint and write the pieces
    python3 -m scripts.art.kit.sets.act1 --check    # exit 1 if a picture is stale
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.kit.sets import _common as K
from scripts.art.kit.sets import brackens as B
from scripts.art.kit.sets._common import C, hsh, rpaint
from scripts.art.native import village as V
from scripts.art.native.palette import to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'act1')
RES = 'res://kit/props/art/act1/'

GRIT, OAK = B.GRIT, B.OAK
GRANITE = [('stone_cool', 'stone', 'ashlar'), ('slate_cool', 'stone_cool', 'stone'), ('stone_cool', 'ashlar', 'ashlar_warm')]
IRON = [('void', 'iron', 'iron'), ('void', 'iron', 'slate')]
WHITE = [('stone_cool', 'plaster', 'snow'), ('ashlar', 'plaster', 'plaster_warm'), ('slate_cool', 'snow_cool', 'snow')]
RED = [('crag_cool', 'clay', 'fox'), ('crag_cool', 'crag_warm', 'fox')]
GREEN = [('leaf_cool', 'leaf_cool', 'leaf'), ('soot', 'leaf_cool', 'leaf'), ('leaf_cool', 'grass_cool', 'leaf_warm')]
CREAM = [('ashlar', 'plaster_warm', 'plaster_warm'), ('ashlar_warm', 'plaster', 'snow_warm'), ('stone_warm', 'ashlar_warm', 'plaster')]
SLATE = [('void', 'slate', 'slate_warm'), ('void', 'slate_cool', 'slate')]
ROPE = [('earth_cool', 'sand_cool', 'sand'), ('earth_cool', 'brass', 'sand')]
WILLOW = [('timber_cool', 'timber', 'sand_cool'), ('earth_cool', 'timber', 'timber_warm')]
NET = [('soot', 'leaf_cool', 'grass_cool'), ('soot', 'earth_cool', 'earth')]
TIN = [('slate_cool', 'ash', 'snow_cool'), ('slate_cool', 'stone_cool', 'snow')]
TURF = [('leaf_cool', 'grass_cool', 'grass'), ('soot', 'grass_cool', 'grass_warm')]
EARTH = [('soot', 'earth_cool', 'earth'), ('earth_cool', 'earth', 'earth_warm')]
STRAW = [('earth_cool', 'brass', 'sand'), ('earth_cool', 'sand_cool', 'sand_warm')]
LOOP = 8


# ================================================================================================
# helpers
# ================================================================================================
def _poly(shape, pts):
    im = Image.new('L', (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=1)
    return np.asarray(im).astype(bool)


def _disc(shape, cx, cy, r, ry=None):
    Y, X = np.mgrid[0:shape[0], 0:shape[1]] + 0.5
    return ((X - cx) / r) ** 2 + ((Y - cy) / (ry or r)) ** 2 <= 1.0


def _line(shape, x0, y0, x1, y1, w=1.0):
    return V.seg_mask(shape, x0, y0, x1, y1, w / 2.0)


def _finish(a, keep=None, line=True):
    """No lone texels, clean clusters, the outline (a light keeps none where keep is set)."""
    V.tidy(a)
    K.despeckle(a, keep=keep)
    if line:
        V.outline(a)
        V.tidy(a, passes=1)
    return a


def _shade(sc, crevice=1.5, rim=0.8, tex=None):
    sc.render()
    return sc.shade(crevice=crevice, rim=rim)


def _rich(sc, a, tags, seed, grain=0.9, sigma=3.0, ao=0.7, sets=None, cell=(2, 2)):
    """Repaint the named solids with Eastward's tonal range: each solid's own ramp lit by the house
    light, a clustered grain of three levels in 2 x 2 texel steps, a smooth hue drift across the
    material's families, and contact shade where it meets the ground."""
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    L = sc.light()
    g = K.vhash(Xg // cell[0], Yg // cell[1], seed)
    G = np.where(g > 0.8, 1.0, np.where(g < 0.22, -1.0, 0.0))
    drift = K.noise((H, W), np.random.default_rng(seed + 1), sigma)
    for i, s in enumerate(sc.solids):
        if s.tag not in tags:
            continue
        m = sc.label == i
        if not m.any():
            continue
        t = s.base + s.k * L + grain * G - ao * (sc.depth < 2.5)
        rpaint(a, m, sets or s.sets, t, np.clip(drift * 0.999, 0, 0.999))
    return a


def _tagm(sc, *tags):
    return np.isin(sc.label, [i for i, s in enumerate(sc.solids) if s.tag in tags])


def _boards(a, m, sets, base, X, Y, seed, along='y', pitch=4):
    """Painted boards: a lit edge and a dark joint each pitch texels, the grain in 2-texel streaks."""
    u = X if along == 'x' else Y
    v = Y if along == 'x' else X
    jt = (u % pitch)
    t = base + np.where(jt == 0, 0.8, 0.0) - np.where(jt == pitch - 1, 1.0, 0.0)
    t = t + 0.9 * (K.vhash(u // pitch, v // 6, seed) - 0.5)
    g = K.vhash(X // 2, Y // 2, seed + 5)
    t = t + np.where(g > 0.84, 0.8, np.where(g < 0.18, -0.8, 0.0)) * (jt != pitch - 1)
    rpaint(a, m, sets, t, np.clip(0.6 * K.vhash(u // pitch, 0, seed + 1) + 0.4 * K.vhash(u // pitch, v // 9, seed + 2), 0, 0.999))


def _strip_frames(fn, n=LOOP):
    """n frames from fn(i), each a code canvas of the same shape with its foot at the same texel,
    cropped to the union so frame 0 is the still."""
    frames = [fn(i) for i in range(n)]
    ox, oy = frames[0][1], frames[0][2]
    ys, xs = np.nonzero(np.any([f[0] >= 0 for f in frames], axis=0))
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    pics = []
    for a, _ox, _oy in frames:
        p = V.Pic(x1 - x0, y1 - y0, ox - x0, oy - y0)
        p.a[:] = a[y0:y1, x0:x1]
        pics.append(p)
    return pics


# ================================================================================================
# Driftwood quay and the lighthouse
# ================================================================================================
def net_rack(seed=101):
    """A fisherman's net rack on the quay: three oak posts and a top rail, a green net hung over the
    rail to dry, sagging between the posts in folds, cork floats along its head, two glass floats
    caught in it, the net's tail heaped at one post."""
    sc = K.Scene(-48, 48, -16, 16, 70)
    for x in (-34, 0, 34):
        sc.cylinder(x, 0, 2.4, 0, 48, OAK, base=2.4, k=1.6, tag='post', mix=hsh(seed, x), tex='wood_v')
    sc.box(-38, -1.6, 46, 38, 1.6, 49.5, OAK, base=2.7, k=1.5, tag='rail', round_=1.0, mix=0.4, tex='wood')
    sc.ellipsoid(30, 6, 3, 11, 6, 4.5, NET, base=1.9, k=1.4, tag='heap', mix=0.2)
    a = _shade(sc)
    _rich(sc, a, ('post', 'rail', 'heap'), seed)
    B._lichen(sc, a, tags=('post',), rate=0.5, seed=seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    # the hung net: from under the rail down to a sagging hem between each pair of posts
    top = oy - 46 + 2
    net = np.zeros((H, W), bool)
    fold = np.zeros((H, W))
    for (xa, xb) in ((-34, 0), (0, 34)):
        for x in range(xa + 2, xb - 2):
            u = (x - xa) / float(xb - xa)
            hem = oy - 12 - 7 * math.sin(math.pi * u) * -1 + 3 * math.sin(6 * u + xa)
            net[top:int(hem), ox + x] = True
            fold[:, ox + x] = math.sin(x * 0.55)
    mesh = (((Xg + Yg) % 6) < 2) | (((Xg - Yg) % 6) < 2)
    netm = net & mesh
    t = 2.2 + 0.9 * fold - 0.8 * ((Yg - top) > 24) + 0.8 * ((Yg - top) < 4)
    rpaint(a, netm, NET + [('leaf_cool', 'grass_cool', 'grass')], t, K.noise(a.shape, np.random.default_rng(seed), 5.0) * 0.999)
    # the heap's mesh
    heap = _tagm(sc, 'heap')
    V._step(a, heap & ~mesh, -1)
    # cork floats along the head, glass floats in the net
    for x in range(-31, 32, 6):
        if abs(x) < 3 or abs(abs(x) - 34) < 3:
            continue
        a[top:top + 2, ox + x:ox + x + 2] = C('fox', 3)
        a[top + 1, ox + x + 1] = C('crag_warm', 2)
    for (gx, gz) in ((-20, 24), (15, 20)):
        g = _disc(a.shape, ox + gx, oy - gz, 3.2)
        rpaint(a, g, [('water_cool', 'water_warm', 'water_warm')], 2.6 + 1.2 * (Yg < oy - gz - 1), 0.0)
        a[oy - gz - 2, ox + gx - 1:ox + gx + 1] = C('sky', 5)
    _finish(a, keep=np.isin(a, [C('fox', 3), C('sky', 5)]))
    B._ground_tufts(a, ox, oy + 2, [-38, -31, 37], seed)
    return K.crop(a, ox, oy)


def lobster_pots(variant='a', seed=103):
    """Lobster pots of withies on a timber base, each a hooped dome with its mesh showing the dark
    inside, stacked three high (a) or a pot and a coil of rope with its float (b)."""
    sc = K.Scene(-36, 36, -20, 16, 48)
    pots = [(-11, -2, 0), (11, -2, 0), (0, -2, 10.5)] if variant == 'a' else [(-8, -2, 0)]
    for k, (x, y, z) in enumerate(pots):
        sc.box(x - 11, y - 6.5, z, x + 11, y + 6.5, z + 2.5, OAK, base=2.3, k=1.4, tag='pbase', round_=0.8, mix=0.3, tex='wood')
        sc.ellipsoid(x, y, z + 2.5, 10.5, 6.5, 8.0, NET, base=1.6 + 0.2 * k, k=1.6, tag='dome%d' % k, mix=hsh(seed, k))
    if variant == 'b':
        sc.cylinder(14, 1, 7.5, 0, 3.2, ROPE, base=2.6, k=1.4, tag='coil', mix=0.3)
        sc.ellipsoid(24, -6, 4, 4.5, 3.8, 4.5, RED, base=2.5, k=1.8, tag='float', mix=0.2)
    a = _shade(sc)
    _rich(sc, a, ('pbase', 'coil', 'float'), seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    for k, (x, y, z) in enumerate(pots):
        d = _tagm(sc, 'dome%d' % k)
        hoop = ((Xg - sc.ox - x + 41) % 6) < 2
        L_ = sc.light()
        rpaint(a, d & hoop, WILLOW, 2.6 + 1.6 * L_, hsh(seed, k, 3))           # the withy hoops over it
        V._step(a, d & ~hoop & ((((Xg // 2) + (Yg // 2)) % 2) == 0), 1)      # the netting between
        # the funnel's mouth at the pot's east end, dark
        mouth = _disc(a.shape, sc.ox + x + 7, sc.oy - (z + 6) + y, 2.6, 3.0) & d
        a[mouth] = C('soot', 1)
    if variant == 'b':
        coil = _tagm(sc, 'coil')
        ring = ((np.hypot(Xg - sc.ox - 14, (Yg - sc.oy + 2.2) * 1.3) % 2.4) < 1.2)
        V._step(a, coil & ring, -1)
        hole = _disc(a.shape, sc.ox + 14, sc.oy - 2.2, 2.6, 1.8) & coil
        a[hole] = C('soot', 1)
    _finish(a)
    B._ground_tufts(a, sc.ox, sc.oy + 3, [-18, 19], seed)
    return K.crop(a, sc.ox, sc.oy)


def mooring_bitt(seed=105):
    """A cast-iron mooring bitt on the quay's edge: a squat post on a bolted plate, a domed cap, a
    hawser twice round it and trailing off, rust where the paint has gone."""
    sc = K.Scene(-16, 18, -12, 10, 30)
    sc.box(-7.5, -6.5, 0, 7.5, 4.5, 1.5, IRON, base=2.0, k=1.5, tag='plate', round_=0.8, mix=0.6)
    sc.cylinder(0, -1, 4.6, 0, 11, IRON, base=2.2, k=1.9, tag='iron', mix=0.2)
    sc.ellipsoid(0, -1, 11.5, 6.4, 5.8, 2.6, IRON, base=2.4, k=1.9, tag='iron', mix=0.4)
    sc.cylinder(0, -1, 5.3, 4, 6.6, ROPE, base=2.6, k=1.6, tag='rope', mix=0.3)
    sc.box(4, 0.5, 0, 17, 2.8, 1.8, ROPE, base=2.6, k=1.5, tag='rope', round_=0.8, mix=0.5)
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    rope = _tagm(sc, 'rope')
    V._step(a, rope & (((Xg + Yg) % 3) == 0), -1)                    # the lay of the strands
    iron = _tagm(sc, 'iron', 'plate')
    rust = iron & (K.vhash(Xg // 2, Yg // 2, seed) > 0.86)
    a[rust] = np.where(sc.light()[rust] > 0.2, C('fox', 2), C('crag_cool', 2))
    for bx in (-5.5, 5.5):                                              # the plate's bolts
        a[sc.oy - 1 + int(-4.5), sc.ox + int(bx)] = C('slate', 4)
    _finish(a)
    return K.crop(a, sc.ox, sc.oy)


def boat_beached(seed=107):
    """A clinker rowing boat drawn up on the shingle above the tide: its strakes lapped down the hull
    (each lit along its lower edge), blue with a white sheer strake and red below the waterline; inside,
    its bottom boards, ribs and two thwarts, an oar laid across them; a stone chocked under the bow."""
    sc = K.Scene(-52, 52, -24, 18, 40)
    sc.ellipsoid(0, -4, 2, 44, 14, 13, [('water_cool', 'water_cool', 'water')], base=2.2, k=1.6, tag='hull', mix=0.3, flat=1.1)
    sc.ellipsoid(-38, 6, 2.5, 6, 4.5, 3.5, GRANITE, base=2.6, k=1.7, tag='stone', mix=0.4, flat=1.5)
    sc.render()
    a = sc.shade(crevice=0.0, rim=0.0)
    _rich(sc, a, ('stone',), seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    hull = _tagm(sc, 'hull')
    gx = Xg - sc.ox + 0.5
    gy = sc.gy + 4
    half = np.where(gx < 0, 14.0 * np.clip(1 - (gx / 43.0) ** 2, 0, 1) ** 0.9, 14.0 * np.clip(1 - (gx / 46.0) ** 4, 0, 1) ** 0.6)
    cut = hull & (np.abs(gy) > half)                                  # the plan pointed at the bow, a transom at the stern
    a[cut] = -1
    hull &= ~cut
    z = sc.depth
    zg = 11.0                                                         # the gunwale: above it the inside shows
    L_ = sc.light()
    inside = hull & (z >= zg + 1.2)
    rail = hull & (z >= zg - 1.0) & (z < zg + 1.2)
    out = hull & (z < zg - 1.0)
    # outside: the strakes, lapped, blue with a white sheer strake and red below the waterline
    lapz = (z % 3.0)
    t = 1.3 + 2.2 * L_ + np.where(lapz < 0.9, 1.0, 0.0) - np.where(lapz > 2.3, 0.7, 0.0)
    gq = K.vhash(Xg // 2, Yg // 2, seed + 3)
    t = t + np.where(gq > 0.84, 0.7, np.where(gq < 0.16, -0.7, 0.0))
    rpaint(a, out & (z >= 8), WHITE[:2], t + 0.4, 0.3)
    rpaint(a, out & (z < 8) & (z >= 3.5), [('water_cool', 'water_cool', 'water'), ('slate_cool', 'water_cool', 'water'),
                                           ('slate_cool', 'sky_cool', 'sky')], t,
           np.clip(K.noise(a.shape, np.random.default_rng(seed), 4.0) * 0.999, 0, 0.999))
    rpaint(a, out & (z < 3.5), RED, t - 0.3, 0.3)
    flake = out & (z < 8) & (z >= 3.5) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.9)
    a[flake] = C('timber', 3)
    # the gunwale's oak rail, lit
    rpaint(a, rail, OAK, 3.2 + 0.8 * L_, 0.3)
    # inside: bottom boards along the boat, ribs across, the far side lit and the near side in shade
    far = gy < 0
    it = 2.0 + 0.9 * far - 0.5 * (np.abs(gy) > half - 3) + 0.6 * ((gy.astype(int) % 3) == 0)
    rib = ((gx.astype(int) + 60) % 7) == 0
    it = np.where(rib, it - 1.0, it)
    rpaint(a, inside, OAK + [('earth_cool', 'timber_cool', 'timber')], it, K.vhash(gy.astype(int) // 3, 0, seed + 6))
    for tx in (-16, 9):                                               # the two thwarts
        th = inside & (gx >= tx) & (gx < tx + 4)
        rpaint(a, th, OAK, 3.2 + 0.7 * (gx < tx + 1), 0.4)
    oar = _line(a.shape, sc.ox - 30, sc.oy - 16, sc.ox + 24, sc.oy - 13, 2.2) & (inside | rail)
    rpaint(a, oar, [('timber_cool', 'timber_warm', 'sand')], 3.4, 0.0)
    water = inside & (np.abs(gy) < 3) & (np.abs(gx + 2) < 10)        # rain lying in her bottom
    rpaint(a, water, [('water_cool', 'water', 'water')], 2.0 + 1.0 * ((Yg % 3) == 0), 0.0)
    weed = out & (z < 2.5) & (K.vhash(Xg // 2, 0, seed + 4) > 0.6)
    a[weed] = C('leaf_cool', 2)
    under = np.zeros((H, W), bool)
    under[2:] = hull[:-2]
    under &= (a < 0) & (Yg > sc.oy - 3)
    _finish(a, keep=np.isin(a, [C('timber', 3)]))
    rpaint(a, under & (a < 0), [('slate_cool', 'stone_cool', 'stone_cool')], 1.4, 0.0)
    B._ground_tufts(a, sc.ox, sc.oy + 5, [-46, 44], seed, fam='grass')
    return K.crop(a, sc.ox, sc.oy)


def _buoy_frame(i, seed=109):
    """One frame of a buoy riding the swell: a red can buoy with a white band and its cage, lit upper
    west, a ring of ripples round it opening and fading over the cycle."""
    ph = 2 * math.pi * i / LOOP
    dz = int(round(1.2 * math.sin(ph)))
    sc = K.Scene(-22, 22, -16, 16, 40)
    sc.cylinder(0, 0, 6.5, 0 + dz, 12 + dz, RED, base=2.4, k=1.9, tag='can', mix=0.3)
    sc.ellipsoid(0, 0, 12 + dz, 6.5, 6.5, 2.0, RED, base=2.6, k=1.9, tag='can', mix=0.4)
    sc.cylinder(0, 0, 6.6, 6 + dz, 8.5 + dz, WHITE, base=2.8, k=1.9, tag='band', mix=0.2)
    for x in (-3.5, 3.5):
        sc.box(x - 0.8, -0.8, 13 + dz, x + 0.8, 0.8, 21 + dz, IRON, base=2.2, k=1.4, tag='cage', round_=0.4)
    sc.box(-4.4, -0.9, 20 + dz, 4.4, 0.9, 22 + dz, IRON, base=2.4, k=1.4, tag='cage', round_=0.4)
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    # the waterline: the can's foot sunk into the swell, darker, a lit lip of water at its sides
    can = _tagm(sc, 'can', 'band')
    wl = can & (sc.depth < 2.5 + dz)
    rpaint(a, wl, [('water_cool', 'water_cool', 'water')], 1.6, 0.0)
    _finish(a, keep=None)
    # the ripples: two rings round the can, opening over the cycle (water, no outline)
    for k in range(2):
        u = ((i / LOOP) + k * 0.5) % 1.0
        r = 8.5 + 7 * u
        ring = _disc(a.shape, sc.ox, sc.oy + 1, r + 1.4, (r + 1.4) * 0.45) & ~_disc(a.shape, sc.ox, sc.oy + 1, r, r * 0.45)
        ring &= (a < 0) & (Yg >= sc.oy - 2)
        ring &= ~(((Xg // 3) % 3 == 0) & (u > 0.5))                    # breaking up as it fades
        a[ring] = C('water_warm', 4) if u < 0.5 else C('water', 3)
    return a, sc.ox, sc.oy


def buoy(seed=109):
    pics = _strip_frames(_buoy_frame)
    return pics[0], {'frames': pics, 'fps': 5.0, 'clip': 'bob'}


def _light_frame(i, seed=111):
    """The harbour light: a short white tower banded red on a granite plinth, its gallery and rail,
    the lantern's glazing between iron astragals, a red dome and finial; the lamp's glow swells and
    eases over the cycle."""
    sc = K.Scene(-22, 22, -20, 18, 112)
    sc.box(-13, -13, 0, 13, 13, 8, GRANITE, base=2.5, k=1.7, tag='plinth', round_=1.5, mix=0.4, tex='stone')
    sc.cylinder(0, 0, 10, 8, 70, WHITE, base=2.6, k=2.0, tag='tower', mix=0.2)
    sc.cylinder(0, 0, 10.2, 30, 40, RED, base=2.3, k=2.0, tag='band', mix=0.2)
    sc.cylinder(0, 0, 10.2, 56, 64, RED, base=2.3, k=2.0, tag='band', mix=0.3)
    sc.cylinder(0, 0, 12.5, 70, 72.5, IRON, base=2.2, k=1.6, tag='gallery', mix=0.3)
    sc.cylinder(0, 0, 7, 72.5, 87, [('lamp', 'lamp', 'lamp')], base=3.0, k=0.6, tag='glass', mix=0.0)
    sc.ellipsoid(0, 0, 87, 8.5, 8.5, 6.5, RED, base=2.4, k=1.9, tag='dome', mix=0.4)
    sc.cylinder(0, 0, 1.2, 92, 98, IRON, base=2.4, k=1.4, tag='finial')
    for x in (-12.5, 12.5):
        sc.box(x - 0.6, -0.6, 72.5, x + 0.6, 0.6, 79, IRON, base=2.0, k=1.2, tag='rail')
    sc.box(-12.5, 11.5, 78, 12.5, 12.6, 79.5, IRON, base=2.0, k=1.2, tag='rail')
    a = _shade(sc)
    _rich(sc, a, ('plinth', 'dome', 'gallery'), seed, grain=0.7)
    _rich(sc, a, ('tower',), seed + 1, grain=0.6, ao=0.0, sets=[WHITE[0]])
    _rich(sc, a, ('band',), seed + 2, grain=0.6, ao=0.0, sets=[RED[0]])
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    glass = _tagm(sc, 'glass')
    glow = 0.5 + 0.5 * math.sin(2 * math.pi * i / LOOP)
    gx = Xg - sc.ox
    t = 3.4 + 1.2 * glow - 0.6 * (np.abs(gx) > 4) + 0.4 * (gx < 0)
    rpaint(a, glass, [('lamp', 'lamp', 'lamp')], t, 0.0)
    a[glass & (((gx + 40) % 5) == 0)] = C('iron', 1)                 # the astragals
    door = _poly(a.shape, [(sc.ox - 4, sc.oy - 8), (sc.ox + 4, sc.oy - 8), (sc.ox + 4, sc.oy - 24), (sc.ox, sc.oy - 27), (sc.ox - 4, sc.oy - 24)])
    door &= _tagm(sc, 'tower')
    rpaint(a, door, [('void', 'slate_cool', 'slate')], 1.4 + 0.6 * ((Xg % 3) == 0), 0.0)
    win = (np.abs(gx + 1) < 1.6) & (np.abs(Yg - (sc.oy - 50)) < 3) & _tagm(sc, 'tower')
    a[win] = C('void', 2)
    tower = _tagm(sc, 'tower', 'band')
    stain = tower & (K.vhash(Xg // 2, Yg // 5, seed) > 0.9) & (Yg > sc.oy - 66)
    V._step(a, stain, -1)                                                # rust weeping under the rail
    B._lichen(sc, a, tags=('plinth',), rate=0.7, seed=seed)
    keep = glass | (a == C('lamp', 5))
    _finish(a, keep=keep)
    # the halo: two texels of warm light round the lantern at the peak of the glow (no outline)
    if glow > 0.6:
        halo = ndi.binary_dilation(glass, iterations=2) & (a < 0)
        a[halo & (((Xg + Yg) % 2) == 0) & (Yg > sc.oy - 92)] = C('lamp', 5)
        a[halo & (((Xg + Yg) % 2) == 1) & (Yg > sc.oy - 92)] = C('lamp', 4)
    return a, sc.ox, sc.oy


def harbour_light(seed=111):
    pics = _strip_frames(_light_frame)
    return pics[0], {'frames': pics, 'fps': 4.0, 'clip': 'glow'}


# ================================================================================================
# the Halt
# ================================================================================================
def platform_edge(variant='a', seed=121):
    """One cell of the halt's platform edge, along x: a front of dressed stone courses, a coping of
    long slabs with a white-painted lip, the platform's gravel behind; drawn from a run of five
    cells so neighbours meet (joints at every cell line), cropped to its own cell."""
    sc = K.Scene(-60, 60, -26, 4, 20)
    sc.box(-60, -24, 0, 60, 0, 12, GRANITE, base=2.4, k=1.6, tag='body', mix=0.3)
    sc.box(-60, -6, 12, 60, 1, 14, GRANITE, base=2.8, k=1.6, tag='coping', mix=0.5, round_=1.0)
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    gx = Xg - sc.ox
    cut = {'a': (0,), 'b': (-5, 6)}[variant]
    lx = ((gx + 12) % 24) - 12                                      # x within the cell, -12 .. 11
    cell = (gx + 12) // 24
    joint = (lx == -12) | np.isin(lx, cut)
    body = _tagm(sc, 'body')
    cop = _tagm(sc, 'coping')
    z = sc.depth
    top = sc.n[..., 2] > 0.5
    # the front: two courses of dressed blocks, joints staggered course to course
    front = body & ~top
    course = (z > 6).astype(int)
    fj = ((lx + 12 + course * 6) % 12) == 0
    t = 2.4 + 0.5 * (K.vhash((lx + 12 + course * 6) // 12 + cell * 0, course, seed) - 0.5) * 2
    t = np.where(fj | (np.abs(z - 6) < 0.8), 0.9, t)
    t = np.where((z > 11.2) & ~fj, t + 0.8, t)
    g = K.vhash((lx + 12) // 2, Yg // 2, seed + 7)
    t = t + np.where(g > 0.8, 0.9, np.where(g < 0.2, -0.8, 0.0)) * (~fj) + 0.6 * sc.light() - 0.7 * (z < 2.5)
    rpaint(a, front, GRANITE, t, K.vhash((lx + 12 + course * 6) // 12, course, seed + 1))
    # the coping slabs: lit tops, a white lip along the front edge, joints at the cell lines
    gc = K.vhash((lx + 12) // 2, Yg // 2, seed + 8)
    ct = 2.8 + 0.8 * (K.vhash(lx // 7, 1, seed) - 0.5) + np.where(gc > 0.82, 1.0, np.where(gc < 0.2, -0.8, 0.0))
    lip = cop & top & (sc.gy > -1.2)
    rpaint(a, cop & top & ~lip, GRANITE, ct, 0.4)
    worn = lip & (K.vhash((lx + 12) // 3, 0, seed + 9) > 0.75)
    rpaint(a, lip & ~worn, WHITE, 3.4 + 0.8 * (K.vhash((lx + 12) // 2, Yg, seed + 10) > 0.6), 0.0)
    rpaint(a, worn, GRANITE, 3.0, 0.6)
    a[cop & joint] = C('stone_cool', 1)
    # the gravel behind: small stones in two-texel clusters
    gr = body & top & ~cop
    gt = 2.0 + 1.0 * (K.vhash((lx + 12) // 2, Yg // 2, seed + 3) > 0.7) - 0.8 * (K.vhash((lx + 12) // 2, Yg // 2, seed + 4) > 0.8)
    rpaint(a, gr, [('stone_cool', 'ash', 'stone'), ('slate_cool', 'ash', 'ash'), ('earth_cool', 'stone_cool', 'stone')], gt,
           K.vhash((lx + 12) // 6, Yg // 4, seed + 11))
    weed = front & (z < 3) & (K.vhash((lx + 12) // 2, 0, seed + 12) > 0.7)
    a[weed] = np.where(z[weed] < 1.5, C('leaf_cool', 2), C('grass_cool', 3))
    V.tidy(a)
    V.outline(a)
    a[:, :sc.ox - 12] = -1
    a[:, sc.ox + 12:] = -1
    p = K.crop(a, sc.ox, sc.oy)
    return p


def waiting_shelter(seed=123):
    """The halt's waiting shelter: a timber lean-to in the railway's green and cream, boarded back and
    sides, a slate roof on a fretted valance, a bench inside along the back, the shadow under the
    roof; a poster frame on the back wall."""
    sc = K.Scene(-50, 50, -34, 6, 80)
    sc.box(-40, -28, 0, 40, -24, 46, GREEN, base=2.4, k=1.3, tag='back', mix=0.3)
    for x0 in (-40, 36):
        sc.box(x0, -28, 0, x0 + 4, -8, 46, GREEN, base=2.4, k=1.6, tag='side', mix=0.3)
    sc.box(-45, -33, 46, 45, -14, 51, SLATE, base=2.4, k=1.8, tag='roof', round_=2.0, mix=0.4)
    sc.box(-45, -15, 41, 45, -14, 46, CREAM, base=2.6, k=1.4, tag='valance', mix=0.3)
    sc.box(-32, -23.5, 11, 32, -17, 13.5, OAK, base=2.6, k=1.6, tag='bench', round_=0.8, mix=0.3, tex='wood')
    for x in (-28, 0, 28):
        sc.box(x - 1.5, -22, 0, x + 1.5, -19, 11, IRON, base=2.0, k=1.4, tag='leg')
    a = _shade(sc)
    _rich(sc, a, ('roof', 'bench', 'valance'), seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    z = sc.depth
    walls = _tagm(sc, 'back', 'side')
    upper = walls & (z > 26)
    _boards(a, walls & ~upper, GREEN, 2.3 + 0.8 * sc.light(), Xg, Yg, seed, along='y', pitch=4)
    _boards(a, upper, CREAM, 2.8 + 0.8 * sc.light(), Xg, Yg, seed + 2, along='y', pitch=4)
    a[walls & (np.abs(z - 26) < 0.8)] = C('leaf_cool', 1)             # the dado rail
    roof = _tagm(sc, 'roof')
    top = roof & (sc.n[..., 2] > 0.5)
    row = (Yg - sc.oy) // 3
    sl = 2.4 + 0.8 * sc.light() + 0.5 * (K.vhash((Xg + row * 3) // 6, row, seed) - 0.5)
    sl = np.where(((Yg - sc.oy) % 3) == 2, sl - 0.9, sl)
    rpaint(a, top, SLATE + [('iron', 'slate_cool', 'ash')], sl, K.vhash((Xg + row * 3) // 6, row, seed + 1))
    lich = top & (K.vhash(Xg // 2, Yg // 2, seed + 7) > 0.95)
    a[lich] = np.where((Xg[lich] % 2) == 0, C('brass', 4), C('sand_cool', 4))
    val = _tagm(sc, 'valance')
    fret = val & (((Xg % 4) == 0) & (Yg > sc.oy - 44))
    a[fret] = C('ashlar', 1)
    # under the roof: the back wall and bench in shade
    under = (walls | _tagm(sc, 'bench', 'leg')) & (sc.gy < -14)
    V._step(a, under & (Yg < sc.oy - 46) & (Yg >= sc.oy - 61), -1)        # the roof's shadow, deepest at its eave
    V._step(a, under & (Yg < sc.oy - 54) & (Yg >= sc.oy - 61), -1)
    # a poster frame: a cream sheet in a dark frame with a coloured pictogram (a train)
    px, py = sc.ox - 12, sc.oy - 28 - 30
    a[py:py + 12, px:px + 16] = C('leaf_cool', 1)
    a[py + 1:py + 11, px + 1:px + 15] = C('plaster', 4)
    a[py + 5:py + 8, px + 3:px + 12] = C('clay', 3)
    a[py + 3:py + 5, px + 9:px + 11] = C('clay', 3)
    a[py + 8:py + 9, px + 4:px + 6] = C('void', 2)
    a[py + 8:py + 9, px + 9:px + 11] = C('void', 2)
    _finish(a)
    B._ground_tufts(a, sc.ox, sc.oy - 6, [-43, 41], seed)
    return K.crop(a, sc.ox, sc.oy)


def churn_stand(seed=125):
    """A milk-churn stand at the lane's end: a timber platform at cart height on four posts, three
    galvanised churns on it (shoulder, neck, lid and handles) waiting for the train, one on the
    ground beside it."""
    sc = K.Scene(-36, 36, -16, 10, 52)
    for x in (-18, 18):
        for y in (-10, 0):
            sc.box(x - 1.8, y - 1.8, 0, x + 1.8, y + 1.8, 14, OAK, base=2.2, k=1.5, tag='leg', mix=hsh(x, y), tex='wood_v')
    sc.box(-21, -12, 14, 21, 2, 17, OAK, base=2.7, k=1.5, tag='deck', round_=0.8, mix=0.3, tex='wood')
    churns = [(-11, -6, 17), (0, -4, 17), (11, -6, 17), (28, 2, 0)]
    for k, (x, y, z0) in enumerate(churns):
        sc.cylinder(x, y, 4.6, z0, z0 + 14, TIN, base=2.4, k=2.0, tag='churn', mix=hsh(seed, k))
        sc.ellipsoid(x, y, z0 + 14, 4.6, 4.6, 3.2, TIN, base=2.5, k=2.0, tag='churn', mix=hsh(seed, k))
        sc.cylinder(x, y, 2.4, z0 + 15, z0 + 20, TIN, base=2.5, k=2.0, tag='churn', mix=hsh(seed, k))
        sc.cylinder(x, y, 3.0, z0 + 20, z0 + 21.5, TIN, base=2.8, k=1.6, tag='lid', mix=0.5)
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ch = _tagm(sc, 'churn')
    rim = ch & (np.abs(sc.depth - 17 - 3) < 0.7)
    V._step(a, rim, 1)
    for k, (x, y, z0) in enumerate(churns):                            # the handles each side
        for sx in (-1, 1):
            hx = sc.ox + x + sx * 5
            hy = sc.oy + y - (z0 + 15)
            a[hy:hy + 3, hx] = C('slate', 2)
            a[hy, hx - sx] = C('slate', 3)
    dents = ch & (K.vhash(Xg // 2, Yg // 3, seed) > 0.9)
    V._step(a, dents, -1)
    B._lichen(sc, a, tags=('leg',), rate=0.6, seed=seed)
    _finish(a)
    B._ground_tufts(a, sc.ox, sc.oy + 1, [-23, -16, 15, 22], seed)
    return K.crop(a, sc.ox, sc.oy)


def semaphore(seed=127):
    """A semaphore home signal at the platform's end: a tall white-painted post (black at its foot)
    with a ladder, the red arm with its white stripe level (danger), the spectacle plate holding red
    and green glasses, a lamp case behind it and a finial on top."""
    sc = K.Scene(-30, 34, -10, 10, 150)
    sc.box(-12, -6, 0, 12, 6, 6, GRANITE, base=2.4, k=1.6, tag='base', round_=1.0, mix=0.4, tex='stone')
    sc.box(-2.2, -2.2, 6, 2.2, 2.2, 128, WHITE, base=2.6, k=2.0, tag='post', mix=0.2)
    sc.box(-2.2, -2.2, 6, 2.2, 2.2, 24, IRON, base=2.0, k=2.0, tag='foot', mix=0.3)
    sc.ellipsoid(0, 0, 131, 2.4, 2.4, 4.5, IRON, base=2.4, k=1.6, tag='finial')
    sc.box(2.2, -1.0, 112, 28, 1.0, 117, RED, base=2.4, k=1.6, tag='arm', round_=0.6, mix=0.2)
    sc.box(-7.5, -1.2, 104, -2.2, 1.2, 117, IRON, base=2.0, k=1.4, tag='spec')
    sc.box(-6, -4, 108, -2.2, -1.2, 114, IRON, base=2.2, k=1.4, tag='lampcase')
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    arm = _tagm(sc, 'arm')
    gx = Xg - sc.ox
    stripe = arm & (gx >= 20) & (gx < 24)
    a[stripe] = C('snow', 4)
    spec = _tagm(sc, 'spec')
    ys, xs = np.nonzero(spec)
    if len(ys):
        cy = ys.min() + 3
        cx = xs.min() + 2
        a[cy:cy + 3, cx:cx + 3] = C('clay', 3)
        a[cy + 5:cy + 8, cx:cx + 3] = C('leaf', 3)
        a[cy, cx] = C('fox', 4)
    # the ladder up the post's east side: stiles and rungs
    lad = (gx >= 3) & (gx <= 6) & (Yg > sc.oy - 112) & (Yg < sc.oy - 8)
    a[lad & ((gx == 3) | (gx == 6))] = C('iron', 2)
    a[lad & ((Yg % 5) == 0)] = C('iron', 3)
    _finish(a, keep=np.isin(a, [C('clay', 3), C('leaf', 3), C('fox', 4)]))
    B._ground_tufts(a, sc.ox, sc.oy + 1, [-13, -10, 11], seed)
    return K.crop(a, sc.ox, sc.oy)


def _lamp_frame(i, seed=129):
    """The platform lamp: a fluted cast-iron column in the railway's green on a stepped base, a
    ladder bar, the lantern's four panes round the oil flame (its glow flickering over the cycle), a
    ventilated cap and finial; the station's name plate hangs under the lantern."""
    sc = K.Scene(-20, 20, -10, 10, 140)
    sc.cylinder(0, 0, 4.0, 0, 6, IRON, base=2.2, k=1.8, tag='base', mix=0.3)
    sc.cylinder(0, 0, 3.0, 6, 14, GREEN, base=2.2, k=1.9, tag='col', mix=0.3)
    sc.cylinder(0, 0, 1.7, 14, 104, GREEN, base=2.3, k=2.0, tag='col', mix=0.2)
    sc.box(-7, -0.8, 96, 7, 0.8, 98, IRON, base=2.2, k=1.3, tag='bar')
    sc.box(-5.5, -5.5, 104, 5.5, 5.5, 106, IRON, base=2.2, k=1.5, tag='frame')
    sc.box(-5, -5, 106, 5, 5, 118, [('lamp', 'lamp', 'lamp')], base=3.0, k=0.6, tag='glass')
    sc.ellipsoid(0, 0, 118, 7, 7, 4.5, IRON, base=2.4, k=1.8, tag='cap', mix=0.3)
    sc.cylinder(0, 0, 1.0, 121, 125, IRON, base=2.4, k=1.4, tag='cap')
    sc.box(-9, -0.6, 86, 9, 0.6, 93, CREAM, base=2.8, k=1.2, tag='plate')
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    glass = _tagm(sc, 'glass')
    fl = [0.0, 0.6, 0.3, 0.9, 0.5, 0.2, 0.8, 0.4][i]
    gx = Xg - sc.ox
    t = 3.6 + 1.0 * fl - 0.7 * (np.abs(gx) > 3)
    rpaint(a, glass, [('lamp', 'lamp', 'lamp')], t, 0.0)
    a[glass & (gx == 0)] = C('iron', 1)                                   # the pane's glazing bar
    flame = glass & (np.abs(gx - 1) < 1.5) & (np.abs(Yg - (sc.oy - 111 - int(fl > 0.5))) < 2)
    a[flame] = C('lamp', 5)
    plate = _tagm(sc, 'plate')
    a[plate & (np.abs(Yg - (sc.oy - 89)) < 1) & ((gx % 3) != 2) & (np.abs(gx) < 7)] = C('void', 2)   # the name in marks
    col = _tagm(sc, 'col')
    V._step(a, col & ((gx % 2) == 0) & (gx > -1), -1)                    # the fluting
    _finish(a, keep=glass)
    B._ground_tufts(a, sc.ox, sc.oy + 1, [-6, 6], seed)
    return a, sc.ox, sc.oy


def platform_lamp(seed=129):
    pics = _strip_frames(_lamp_frame)
    return pics[0], {'frames': pics, 'fps': 6.0, 'clip': 'flicker'}


def timetable_board(seed=131):
    """The halt's timetable board on two posts, under a little gabled hood: a cream sheet in a green
    frame, its rows in pictograms (a clock face, an arrow, a train and the next stop's mark), a red
    heading band; lettering at this size reads as nonsense, so the board shows marks, not words."""
    sc = K.Scene(-34, 34, -10, 8, 110)
    for x in (-18, 18):
        sc.box(x - 2, -2, 0, x + 2, 2, 82, GREEN, base=2.2, k=1.8, tag='post', mix=0.3, tex='wood_v')
    sc.box(-24, -3, 34, 24, 1, 80, GREEN, base=2.2, k=1.4, tag='frame', mix=0.2)
    sc.box(-27, -6, 80, 27, 3, 86, SLATE, base=2.4, k=1.8, tag='hood', round_=1.5, mix=0.4)
    a = _shade(sc)
    _rich(sc, a, ('post', 'frame', 'hood'), seed)
    H, W = a.shape
    ox, oy = sc.ox, sc.oy
    x0, x1 = ox - 21, ox + 21
    ytop, ybot = oy + 1 - 77, oy + 1 - 37
    Yg0, Xg0 = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    sheetm = (Yg0 >= ytop) & (Yg0 < ybot) & (Xg0 >= x0) & (Xg0 < x1)
    pt = 4.6 - 2.2 * ((Xg0 - x0) / 42.0 + (Yg0 - ytop) / 40.0) * 0.5 + 0.7 * (K.vhash(Xg0 // 2, Yg0 // 2, seed + 4) > 0.8)
    rpaint(a, sheetm, [('plaster', 'plaster', 'plaster'), ('plaster_warm', 'plaster_warm', 'plaster_warm')], pt,
           K.noise(a.shape, np.random.default_rng(seed + 5), 4.0))
    a[ytop:ytop + 5, x0:x1] = C('clay', 3)
    a[ytop + 1:ytop + 2, x0 + 3:x1 - 3] = C('fox', 4)
    for r in range(5):
        y = ytop + 8 + r * 6
        cl = _disc(a.shape, x0 + 5, y + 2, 2.4)
        a[cl] = C('snow', 5)
        a[_disc(a.shape, x0 + 5, y + 2, 2.4) & ~_disc(a.shape, x0 + 5, y + 2, 1.5)] = C('void', 2)
        a[y + 1:y + 3, x0 + 5] = C('void', 2)
        a[y + 2, x0 + 10:x0 + 16] = C('slate', 2)
        a[y + 1, x0 + 14] = C('slate', 2)
        a[y + 3, x0 + 14] = C('slate', 2)
        a[y + 1:y + 4, x0 + 19:x0 + 27] = C('leaf_cool', 2)
        a[y + 1, x0 + 25:x0 + 27] = C('leaf', 4)
        a[y + 1:y + 4, x0 + 31:x0 + 31 + 2 + (r % 3) * 2] = C('clay', 2 + (r % 2))
        a[y + 1:y + 4, x0 + 37:x0 + 39] = C('sky', 2 + (r % 2))             # the platform's mark
    a[ybot - 1, x0:x1] = C('ashlar', 2)
    a[ytop - 1, x0 - 1:x1 + 1] = C('leaf', 4)                              # the frame's lit top bead
    a[ybot - 9:ybot - 2, x1 - 11:x1 - 3] = C('snow', 4)                         # a notice pinned at the corner
    a[ybot - 9, x1 - 11:x1 - 3] = C('clay', 3)
    a[ybot - 6:ybot - 4, x1 - 9:x1 - 5] = C('slate', 3)
    hood = _tagm(sc, 'hood')
    YY, XX = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    lich = hood & (K.vhash(XX // 2, YY // 2, seed + 7) > 0.9)
    a[lich] = np.where((XX[lich] % 2) == 0, C('brass', 4), C('leaf_cool', 3))
    a[ytop:ybot, x1] = C('soot', 1)
    # weathering on the sheet: a few stains in two-texel clusters, a lit top edge
    Yg, Xg = np.mgrid[0:H, 0:W]
    sheet = (Yg >= ytop + 5) & (Yg < ybot - 1) & (Xg >= x0) & (Xg < x1)
    st = sheet & (a // 8 == C('plaster', 0) // 8) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.88)
    a[st] = C('plaster_warm', 2)
    _finish(a, keep=sheet)
    for fx in (-18, 18):                                                   # moss at the posts' feet
        a[oy - 3:oy, ox + fx - 2:ox + fx] = C('leaf_cool', 2)
        a[oy - 2:oy, ox + fx:ox + fx + 2] = C('grass_cool', 3)
    B._ground_tufts(a, ox, oy + 1, [-21, -15, 15, 21], seed)
    return K.crop(a, ox, oy)


# ================================================================================================
# the Millrace landslip
# ================================================================================================
def _wheel_frame(i, seed=141):
    """The undershot mill wheel against the mill's gable: an oak wheel of two rims, sixteen paddles
    and eight spokes on an iron hub, turning one paddle's pitch over the cycle; the leat runs
    under it in a stone channel, white where the paddles strike it; the wall wet and green below."""
    R, D = 34.0, 9.0                                                   # the wheel's radius and width
    sc = K.Scene(-60, 60, -34, 22, 100)
    sc.box(-56, -32, 0, 56, -20, 78, GRIT, base=2.4, k=1.4, tag='wall', mix=0.4)
    sc.box(-8, -21, 34, 8, -18, 46, IRON, base=2.2, k=1.8, tag='bearing', round_=1.0, mix=0.4)
    sc.box(-48, -20, 0, -40, 14, 10, GRANITE, base=2.5, k=1.7, tag='chan', round_=1.0, mix=0.4)
    sc.box(40, -20, 0, 48, 14, 10, GRANITE, base=2.5, k=1.7, tag='chan', round_=1.0, mix=0.5)
    a = _shade(sc)
    _rich(sc, a, ('chan', 'bearing'), seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    wall = _tagm(sc, 'wall')
    z = sc.depth
    # the gable in rubble courses: each stone its own tone, lit at its top edge, a dark joint under
    # it and at its east end; wet and mossy low down where the leat splashes
    face = wall & ~(sc.n[..., 2] > 0.5)
    ci = np.floor(z / 7.0).astype(int)
    zin = z - ci * 7.0
    si, spos, snxt = B._stone_joints((Xg - ox).astype(float) + ci * 5.0, 900 + ci, lo=7.0, hi=15.0)
    st = 2.3 + (K.vhash(si, ci, seed) - 0.5) * 1.4 + 0.25 * sc.light()
    st = np.where(zin > 5.8, st + 0.9, st)
    st = np.where((zin < 1.0) | (snxt < 1.0), 0.7, st)
    st = np.where((spos < 1.2) & (zin >= 1.0), st + 0.5, st)
    wetz = (z < 24)
    st = st - 0.8 * wetz
    gw = K.vhash(Xg // 2, Yg // 2, seed + 5)
    st = st + np.where(gw > 0.82, 0.8, np.where(gw < 0.18, -0.7, 0.0)) * ~((zin < 1.0) | (snxt < 1.0))
    rpaint(a, face, GRIT, st, K.vhash(si, ci, seed + 1))
    moss = face & wetz & (zin < 2.5) & (K.vhash(Xg // 2, ci, seed + 2) > 0.45)
    a[moss] = np.where(K.vhash(Xg[moss] // 2, Yg[moss] // 2, seed + 3) > 0.5, C('leaf_cool', 2), C('grass_cool', 2))
    top = wall & (sc.n[..., 2] > 0.5)
    rpaint(a, top, GRIT, 3.2 + (K.vhash((Xg - ox) // 9, Yg // 4, seed + 4) - 0.5) * 1.2, 0.5)
    # the water in the channel, between the cheeks: dark, streaked, white under the wheel
    wy0, wy1 = oy - 6, oy + 14
    water = (Xg >= ox - 40) & (Xg < ox + 40) & (Yg >= wy0) & (Yg < wy1)
    water &= ~_tagm(sc, 'chan')
    ph = i / float(LOOP)
    streak = ((Xg + int(ph * 8)) % 8) < 2
    wt = 1.8 + 0.9 * streak - 0.8 * (Yg < wy0 + 3) + 0.6 * ((Yg - wy0) > 12) + 0.8 * (((Xg + Yg + int(ph * 8)) % 11) == 0)
    rpaint(a, water, [('water_cool', 'water', 'water_warm'), ('water_cool', 'water_cool', 'water')], wt, ((Xg // 6) % 2) * 0.6)
    # the wheel: back rim first, then paddles from back to front, then the front rim and spokes
    cx, cy = ox, oy - (R + 6) - (-14)                                   # its axle at y = -14, z = R + 6
    ang0 = (2 * math.pi / 16) * (i / float(LOOP))
    shape = a.shape
    wheel = np.full(shape, -1, np.int32)

    def ring(dy, r0, r1, fam, t0):
        m = _disc(shape, cx, cy + dy, r1) & ~_disc(shape, cx, cy + dy, r0)
        tt = t0 + 1.2 * ((Xg - cx) < 0) * ((Yg - cy - dy) < 0) - 0.8 * ((Xg - cx) > 0) * ((Yg - cy - dy) > 0)
        rpaint(wheel, m, fam, tt, 0.3)
    ring(-D, R - 3.5, R, OAK, 1.6)                                      # the back rim, in shade
    for k in range(16):
        th = ang0 + k * 2 * math.pi / 16
        c, s = math.cos(th), math.sin(th)
        p = [(cx + (R - 9) * c, cy + (R - 9) * s), (cx + (R + 4) * c, cy + (R + 4) * s),
             (cx + (R + 4) * c, cy + (R + 4) * s - D), (cx + (R - 9) * c, cy + (R - 9) * s - D)]
        pm = _poly(shape, p)
        lit = 0.9 if s < -0.2 else (-0.6 if s > 0.4 else 0.2)
        gq = K.vhash(Xg // 2, Yg // 2, seed + k)
        rpaint(wheel, pm, OAK + [('earth_cool', 'timber_cool', 'timber')], 2.4 + lit + 0.5 * ((k % 2) - 0.5)
               + np.where(gq > 0.8, 0.8, np.where(gq < 0.2, -0.8, 0.0)), hsh(seed, k))
        edge = _line(shape, p[1][0], p[1][1], p[2][0], p[2][1], 1.6)
        wheel[edge] = C('timber_warm', 4) if s < 0 else C('timber_cool', 1)
    ring(0, R - 3.5, R, OAK, 2.4)                                       # the front rim
    for k in range(8):
        th = ang0 + k * 2 * math.pi / 8 + math.pi / 16
        c, s = math.cos(th), math.sin(th)
        sp = _line(shape, cx + 4 * c, cy + 4 * s, cx + (R - 3) * c, cy + (R - 3) * s, 2.2)
        rpaint(wheel, sp, OAK, 2.6 + (0.9 if (c < 0 and s < 0) else -0.4), 0.4)
    low = (wheel >= 0) & (Yg > cy + R * 0.45)                            # the paddles' wet ends, slimed green
    V._step(wheel, low, -1)
    slime = low & (K.vhash(Xg // 2, Yg // 2, seed + 7) > 0.7)
    wheel[slime] = C('leaf_cool', 2)
    hub = _disc(shape, cx, cy, 5.5)
    rpaint(wheel, hub, IRON, 2.2 + 1.2 * ((Xg < cx) & (Yg < cy)), 0.3)
    wheel[_disc(shape, cx, cy, 1.8)] = C('void', 2)
    # the wheel in front of the wall, behind the near cheek and the water's surface below its axle
    near = _tagm(sc, 'chan') & (Yg > oy - 14)
    sel = (wheel >= 0) & ~near & ~((Yg > oy - 2) & water)
    a[sel] = wheel[sel]
    # the strike: white water where the lowest paddles meet the leat (it churns over the cycle)
    for k in range(5):
        x = ox - 20 + k * 10 + int(4 * math.sin(2 * math.pi * ph + k))
        foam = _disc(shape, x, oy - 3 + (k % 2), 3.2 + (k + i) % 3 * 0.6, 1.6) & water
        a[foam] = C('snow', 4) if (k + i) % 2 else C('water_warm', 5)
    _finish(a, keep=None)
    return a, ox, oy


def mill_wheel(seed=141):
    pics = _strip_frames(_wheel_frame)
    return pics[0], {'frames': pics, 'fps': 6.0, 'clip': 'turn'}


def sluice(seed=143):
    """The sluice at the leat's head: two dressed stone piers with grooves, an oak gate of planks
    drawn up a hand's breadth on its iron rack, the headstock beam and the handwheel, the water
    pouring white under the gate."""
    sc = K.Scene(-36, 36, -24, 18, 56)
    for x0 in (-24, 14):
        sc.box(x0, -12, 0, x0 + 10, 2, 32, GRANITE, base=2.5, k=1.8, tag='pier', round_=1.5, mix=hsh(seed, x0), tex='stone')
    sc.box(-15, -7, 5, 15, -4, 30, OAK, base=2.3, k=1.5, tag='gate', mix=0.3)
    sc.box(-25, -10, 32, 25, -2, 36, OAK, base=2.6, k=1.5, tag='beam', round_=1.0, mix=0.5, tex='wood')
    sc.box(-1, -6.5, 36, 1, -4.5, 46, IRON, base=2.2, k=1.4, tag='rack')
    a = _shade(sc)
    _rich(sc, a, ('pier', 'beam'), seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    gate = _tagm(sc, 'gate')
    _boards(a, gate, OAK + [('earth_cool', 'timber_cool', 'timber')], 2.2 + 1.0 * sc.light() - 0.6 * ((Yg - sc.oy) > -14), Xg, Yg, seed,
            along='x', pitch=4)
    slime = gate & ((Yg - sc.oy) > -12) & (K.vhash(Xg // 2, Yg // 2, seed + 9) > 0.6)
    a[slime] = C('leaf_cool', 2)
    a[gate & (((Xg - sc.ox) % 10) == 0)] = C('iron', 1)                    # the straps
    # the handwheel on the rack's head, face on: rim, four spokes, hub
    hx, hy = sc.ox + 4, sc.oy - 4 - 44
    rimm = _disc(a.shape, hx, hy, 6.5) & ~_disc(a.shape, hx, hy, 5.0)
    rpaint(a, rimm, IRON, 2.4 + 1.0 * (Yg < hy), 0.3)
    for (dx, dy) in ((1, 0), (0, 1)):
        a[_line(a.shape, hx - 5 * dx, hy - 5 * dy, hx + 5 * dx, hy + 5 * dy, 1.6)] = C('iron', 2)
    a[_disc(a.shape, hx, hy, 1.6)] = C('iron', 4)
    # the water: dark in the channel, pouring white from under the gate
    wx0, wx1 = sc.ox - 14, sc.ox + 14
    water = (Xg >= wx0) & (Xg < wx1) & (Yg >= sc.oy - 6) & (Yg < sc.oy + 14) & ~_tagm(sc, 'pier', 'gate')
    st = ((Xg + Yg // 3) % 7) < 2
    rpaint(a, water, [('water_cool', 'water', 'water_warm'), ('water_cool', 'water_cool', 'water')], 1.8 + 0.9 * st + 0.7 * ((Yg - sc.oy) > 6),
           ((Xg // 5) % 2) * 0.6)
    foam = water & (Yg < sc.oy - 2) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.4)
    a[foam] = C('snow', 4)
    a[water & (Yg >= sc.oy - 2) & (Yg < sc.oy) & ((Xg % 3) < 2)] = C('water_warm', 5)
    B._lichen(sc, a, tags=('pier',), rate=0.7, seed=seed)
    _finish(a, keep=foam)
    return K.crop(a, sc.ox, sc.oy)


def millstones(seed=145):
    """Spare millstones in the miller's yard: one lying flat with its dressing (harps of furrows
    round the eye), one on edge leaning against a post, a sack of meal against it."""
    sc = K.Scene(-44, 44, -20, 18, 50)
    sc.cylinder(-10, 2, 16, 0, 6, GRANITE, base=2.5, k=1.8, tag='flat', mix=0.3)
    sc.box(26, -12, 0, 30, -8, 34, OAK, base=2.2, k=1.6, tag='post', tex='wood_v', mix=0.3)
    sc.ellipsoid(32, 6, 6, 6.5, 5, 7, CREAM, base=2.6, k=1.8, tag='sack', mix=0.2)
    a = _shade(sc)
    _rich(sc, a, ('flat', 'post', 'sack'), seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    flat = _tagm(sc, 'flat')
    top = flat & (sc.n[..., 2] > 0.5)
    fx, fy = sc.ox - 10, sc.oy + 2 - 6
    ang = np.arctan2((Yg - fy) * 1.0, (Xg - fx) * 0.8)
    rr = np.hypot((Xg - fx) * 0.8, Yg - fy)
    harp = (np.floor((ang + math.pi) / (2 * math.pi / 8)))
    fur = ((rr + harp * 3) % 4) < 1.2
    V._step(a, top & fur & (rr > 3), -1)
    a[top & (rr < 2.6)] = C('void', 2)
    # the standing stone, face on: its rim (the stone's thickness) to the east, the face lit west
    cx, cy, r = sc.ox + 14, sc.oy - 17, 15.0
    rim = _disc(a.shape, cx + 3, cy, r) & ~_disc(a.shape, cx, cy, r)
    rpaint(a, rim, GRANITE, 1.8 + 0.4 * (Yg < cy), 0.2)
    face = _disc(a.shape, cx, cy, r)
    rr2 = np.hypot(Xg - cx, Yg - cy)
    ang2 = np.arctan2(Yg - cy, Xg - cx)
    harp2 = np.floor((ang2 + math.pi) / (2 * math.pi / 8))
    ft = 2.6 + 0.9 * (((Xg - cx) + (Yg - cy)) < -8) - 0.6 * (((Xg - cx) + (Yg - cy)) > 10)
    ft = ft - 1.0 * (((rr2 + harp2 * 3) % 4) < 1.2) * (rr2 > 3)
    g2 = K.vhash(Xg // 2, Yg // 2, seed + 6)
    ft = ft + np.where(g2 > 0.82, 0.9, np.where(g2 < 0.2, -0.8, 0.0))
    rpaint(a, face, GRANITE, ft, K.noise(a.shape, np.random.default_rng(seed + 7), 3.0) * 0.999)
    a[_disc(a.shape, cx, cy, 2.6)] = C('void', 2)
    sack = _tagm(sc, 'sack')
    a[sack & (np.abs(Yg - (sc.oy - 11)) < 1)] = C('sand_cool', 2)            # the sack's tie
    flour = (a < 0) & (Yg > sc.oy - 2) & (Yg < sc.oy + 6) & (np.abs(Xg - sc.ox - 30) < 9) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.6)
    _finish(a)
    a[flour & (a < 0)] = C('plaster', 4)
    B._ground_tufts(a, sc.ox, sc.oy + 6, [-30, -26, 40], seed)
    return K.crop(a, sc.ox, sc.oy)


def landslip(seed=147):
    """The Millrace landslip (way W3): a tongue of wet earth come down across the road, boulders
    carried in it lit on their tops, a birch snapped and lying across with its root plate torn up,
    and the mud fanning out at its toe in lobes."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-70, 70, -40, 24, 70)
    sc.ellipsoid(0, -10, 0, 60, 26, 19, EARTH, base=2.1, k=1.7, tag='earth', mix=0.3, flat=1.2)
    sc.ellipsoid(-30, 4, 0, 30, 14, 10, EARTH, base=2.0, k=1.7, tag='earth', mix=0.6, flat=1.2)
    sc.ellipsoid(34, 6, 0, 26, 12, 8, EARTH, base=2.0, k=1.7, tag='earth', mix=0.5, flat=1.2)
    for k in range(14):
        x, y = rng.uniform(-52, 52), rng.uniform(-26, 10)
        s = rng.uniform(4.5, 10.0)
        zt = max(0.0, 19 * math.sqrt(max(0.0, 1 - ((x / 60) ** 2 + ((y + 10) / 26) ** 2))))
        sc.ellipsoid(x, y, zt * 0.8 + s * 0.4, s, s * 0.75, s * 0.7, GRIT, base=2.6 + rng.uniform(-0.6, 0.5), k=1.8, tag='stone',
                     mix=rng.random(), flat=1.5, tex='stone')
    sc.box(-44, 3, 13, 30, 7.5, 17.5, [('stone_cool', 'snow_cool', 'snow'), ('ash', 'snow_cool', 'snow')], base=2.6, k=1.8,
           tag='trunk', round_=2.0, mix=0.3)
    sc.ellipsoid(34, 5, 16, 4, 9, 13, EARTH, base=1.8, k=1.6, tag='roots', mix=0.4)
    for k in range(5):                                                    # its broken crown of twigs
        sc.ellipsoid(-48 - k * 2.5, 2 + (k % 2) * 4, 15 + (k % 3), 5, 4, 3.5, [('soot', 'timber_cool', 'earth')], base=1.8, k=1.6,
                     tag='twigs', mix=hsh(seed, k))
    a = _shade(sc)
    _rich(sc, a, ('earth', 'stone', 'trunk', 'roots', 'twigs'), seed, grain=1.0)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    earth = _tagm(sc, 'earth')
    n = K.noise((H, W), rng, 2.5)
    wet = earth & (n > 0.62)
    V._step(a, wet, -1)
    clods = earth & (K.vhash(Xg // 3, Yg // 2, seed) > 0.82)
    V._step(a, clods & (sc.light() > 0), 1)
    # the scarp at the slip's head: raw earth in layers where it tore from the hill
    scarp = earth & (sc.gy < -24)
    lay = ((Yg // 2) % 3 == 0)
    rpaint(a, scarp, [('soot', 'earth_cool', 'earth_warm'), ('soot', 'clay_cool', 'earth')], 1.6 + 0.9 * lay + 0.6 * sc.light(), 0.3)
    trunk = _tagm(sc, 'trunk')
    a[trunk & (K.vhash(Xg // 3, Yg, seed + 2) > 0.8)] = C('void', 2)              # the birch's dark bark marks
    roots = _tagm(sc, 'roots')
    rr = roots & (((Xg + Yg) % 4) == 0)
    a[rr] = C('timber_cool', 1)
    B._lichen(sc, a, tags=('stone',), rate=0.4, seed=seed)
    # turf torn up and carried: green clumps on the slip's crown
    turf = earth & (sc.n[..., 2] > 0.75) & (K.noise((H, W), rng, 3.0) > 0.68)
    rpaint(a, turf, TURF, 2.2 + 1.0 * sc.light(), 0.3)
    _finish(a)
    B._ground_tufts(a, sc.ox, sc.oy + 10, [-60, -52, 55, 62], seed)
    return K.crop(a, sc.ox, sc.oy)


def fence_broken(seed=149):
    """A post-and-rail fence the slip broke: the near post snapped to a stump, the next leaning, the
    top rail split and hanging to the grass, the lower rail still whole between the last two."""
    sc = K.Scene(-44, 44, -8, 10, 60)
    sc.box(-38, -2, 0, -34, 2, 13, OAK, base=2.4, k=1.6, tag='post', tex='wood_v', mix=0.2)
    for k in range(6):
        sc.box(-2 + k * 0.9, -2, k * 7, 2 + k * 0.9, 2, k * 7 + 7, OAK, base=2.4, k=1.6, tag='post', tex='wood_v', mix=0.4)
    sc.box(34, -2, 0, 38, 2, 44, OAK, base=2.4, k=1.6, tag='post', tex='wood_v', mix=0.6)
    sc.box(2, -1, 14, 34, 1, 18, OAK, base=2.6, k=1.4, tag='rail', round_=0.8, tex='wood', mix=0.3)
    NET_ = [('leaf_cool', 'leaf', 'grass'), ('grass_cool', 'leaf', 'leaf_warm')]
    sc.ellipsoid(-30, 4, 7, 13, 8, 11, NET_, base=2.1, k=2.1, tag='nettle', mix=0.3)     # nettles grown up round the stump
    sc.ellipsoid(-18, 6, 5, 9, 6, 7, NET_, base=2.3, k=2.1, tag='nettle', mix=0.7)
    sc.ellipsoid(24, 6, 4, 8, 5, 6, NET_, base=2.2, k=2.1, tag='nettle', mix=0.5)
    a = _shade(sc)
    _rich(sc, a, ('post', 'rail'), seed)
    Yn, Xn = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    for i, s_ in enumerate(sc.solids):
        if s_.tag == 'nettle':
            mi = sc.label == i
            gq = K.vhash(Xn.astype(int) // 2, Yn.astype(int) // 2, seed + i)
            rpaint(a, mi, NET_ + [('soot', 'leaf_cool', 'grass')], s_.base + s_.k * sc.light() + 0.8 * B._leaf_marks(Xn, Yn, seed + i, w=4, h=3)
                   + np.where(gq > 0.85, 0.8, np.where(gq < 0.15, -0.8, 0.0)), K.noise(a.shape, np.random.default_rng(seed + i), 3.0) * 0.999)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    # the top rail, split: one end still on the leaning post, the other down in the grass
    p = [(ox + 4, oy - 38), (ox + 7, oy - 40), (ox + 33, oy - 8), (ox + 30, oy - 6)]
    rm = _poly(a.shape, p)
    gr = K.vhash(Xg // 2, Yg // 2, seed + 3)
    rpaint(a, rm, OAK + [('earth_cool', 'timber_cool', 'timber')], 2.2 + 1.2 * ((Xg - ox) < 15) - 0.6 * (Yg > oy - 14)
           + np.where(gr > 0.8, 0.9, np.where(gr < 0.2, -0.8, 0.0)), K.noise(a.shape, np.random.default_rng(seed), 3.0) * 0.999)
    a[_line(a.shape, ox + 5, oy - 37, ox + 31, oy - 7, 1.0)] = C('timber_warm', 4)
    # the splintered stump's top and the snapped stub on the near post
    a[oy - 15:oy - 13, ox - 38:ox - 34] = C('timber_warm', 4)
    a[oy - 16, ox - 37] = C('timber_warm', 3)
    a[oy - 16, ox - 35] = C('timber_warm', 3)
    B._lichen(sc, a, tags=('post',), rate=0.6, seed=seed)
    _finish(a)
    B._ground_tufts(a, ox, oy + 2, [-40, -33, -3, 4, 31, 39], seed)
    return K.crop(a, ox, oy)


# ================================================================================================
# Old Fang's barrow
# ================================================================================================
def barrow_entrance(seed=161):
    """Old Fang's barrow from the south: a long turf mound, and set into its front a portal of two
    tall stones and a capstone over the dark passage, a forecourt of kerb stones curving away
    either side, a blocking stone rolled aside, moss on the stones' shaded faces."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-80, 80, -70, 22, 76)
    sc.ellipsoid(0, -34, 0, 70, 34, 40, TURF, base=1.9, k=2.3, tag='mound', mix=0.3, flat=1.1)
    for x0 in (-17, 9):
        sc.box(x0, -6, 0, x0 + 8, 0, 34, GRIT, base=2.5, k=1.8, tag='stone', round_=2.5, mix=rng.random(), tex='stone')
    sc.box(-21, -8, 34, 21, 1, 42, GRIT, base=2.8, k=1.8, tag='stone', round_=3.0, mix=0.4, tex='stone')
    for k, ang in enumerate(np.linspace(0.35, 1.25, 4)):
        for sgn in (-1, 1):
            x = sgn * (24 + 44 * math.sin(ang) * 0.85)
            y = -2 - 30 * (1 - math.cos(ang)) * 0.8
            h = 14 - k * 2 + rng.uniform(-2, 2)
            sc.box(x - 4.5, y - 3, 0, x + 4.5, y + 3, h, GRIT, base=2.5 + rng.uniform(-0.4, 0.4), k=1.8, tag='stone', round_=2.0,
                   mix=rng.random(), tex='stone')
    sc.ellipsoid(32, 12, 7, 9, 6, 8, GRIT, base=2.6, k=1.8, tag='stone', mix=0.5, flat=1.5, tex='stone')
    a = _shade(sc)
    _rich(sc, a, ('stone',), seed + 9, grain=0.8)
    _rich(sc, a, ('mound',), seed, grain=1.0, sigma=3.0, cell=(2, 3), sets=[('leaf_cool', 'grass_cool', 'grass'), ('soot', 'grass_cool', 'grass_cool'),
                                                              ('leaf_cool', 'leaf_cool', 'grass_cool'), ('leaf_cool', 'grass', 'grass_warm')])
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    mound = _tagm(sc, 'mound')
    tuft = K.vhash(Xg // 2, Yg // 2, seed)
    V._step(a, mound & (tuft > 0.82) & (sc.light() > 0), 1)
    V._step(a, mound & (tuft < 0.12), -1)
    tf = mound & (K.vhash(Xg // 4, Yg // 3, seed + 5) > 0.72) & ((Yg % 3) == 0) & ((Xg % 4) != 3)   # tussocks: lit tips over shadow
    a[tf & (sc.light() > -0.2)] = C('grass', 4)
    sh_ = np.zeros_like(tf)
    sh_[1:] = tf[:-1]
    a[sh_ & mound] = C('leaf_cool', 1)
    fl = mound & (K.vhash(Xg // 2, Yg // 2, seed + 6) > 0.985)                   # tormentil and eyebright in pairs
    a[fl & ((Xg % 2) == 0)] = C('brass', 4)
    a[fl & ((Xg % 2) == 1)] = C('snow_warm', 4)
    # the passage: dark between the uprights under the capstone, a step of light on its floor
    pas = (Xg >= sc.ox - 9) & (Xg < sc.ox + 9) & (Yg >= sc.oy - 34) & (Yg < sc.oy - 2) & (mound | (a < 0))
    a[pas] = C('void', 1)
    side = pas & ((Xg < sc.ox - 6) | (Xg >= sc.ox + 6))                 # the passage's side stones, just seen
    a[side & (((Yg // 5) + (Xg // 3)) % 2 == 0)] = C('slate_cool', 1)
    a[side & (((Yg // 5) + (Xg // 3)) % 2 == 1)] = C('void', 2)
    a[pas & (Yg >= sc.oy - 5)] = C('void', 3)
    a[pas & (Yg >= sc.oy - 3) & (np.abs(Xg - sc.ox) < 5)] = C('earth_cool', 1)   # the trodden sill
    a[pas & (Yg < sc.oy - 31)] = C('soot', 1)
    a[pas & (Yg >= sc.oy - 31) & (Yg < sc.oy - 29)] = C('soot', 2)
    stone = _tagm(sc, 'stone')
    shaded = stone & (sc.light() < -0.05) & (K.vhash(Xg // 2, Yg // 2, seed + 3) > 0.55)
    a[shaded] = C('leaf_cool', 2)
    B._lichen(sc, a, tags=('stone',), rate=0.7, seed=seed)
    _finish(a, keep=pas)
    B._ground_tufts(a, sc.ox, sc.oy + 4, [-70, -62, -50, 48, 60, 68], seed)
    return K.crop(a, sc.ox, sc.oy)


def kerb_stone(variant='a', seed=163):
    """A kerb stone of the barrow's ring standing alone in the grass: a low rounded gritstone slab set
    on edge, lit on its top and west, lichen in rosettes, moss at its foot; three shapes."""
    w, h, d = {'a': (9, 14, 4), 'b': (11, 10, 5), 'c': (7, 17, 4)}[variant]
    sc = K.Scene(-20, 20, -10, 10, 30)
    sc.box(-w, -d, 0, w, d, h, GRIT, base=2.5, k=1.9, tag='stone', round_=3.0, mix=hsh(seed, ord(variant)), tex='stone')
    sc.ellipsoid(w * 0.4, -d, h * 0.6, w * 0.6, d * 0.9, h * 0.45, GRIT, base=2.6, k=1.9, tag='stone', mix=0.5, flat=1.5)
    a = _shade(sc)
    B._lichen(sc, a, tags=('stone',), rate=0.9, seed=seed + ord(variant))
    B._bench_marks(sc, a, seed + ord(variant))
    _finish(a)
    B._ground_tufts(a, sc.ox, sc.oy + 3, [-w - 2, -w + 2, w - 1, w + 2], seed + ord(variant))
    return K.crop(a, sc.ox, sc.oy)


# ================================================================================================
# beehives
# ================================================================================================
def wbc_hive(seed=171):
    """A WBC beehive, white: a plinth on four splayed legs, the brood lift and two supers each with
    its flared skirt overlapping the one below, a gabled roof, the landing board and the entrance
    slot dark under the porch."""
    sc = K.Scene(-26, 26, -20, 14, 80)
    for x in (-12, 12):
        for y in (-12, 2):
            sc.box(x - 1.5, y - 1.5, 0, x + 1.5, y + 1.5, 10, WHITE, base=2.4, k=1.6, tag='leg')
    sc.box(-15, -14, 10, 15, 4, 13, WHITE, base=2.7, k=1.6, tag='plinth', round_=0.6)
    for k in range(3):
        z0 = 13 + k * 11
        sc.box(-13, -12, z0, 13, 2, z0 + 11, WHITE, base=2.6, k=1.9, tag='lift', mix=0.2)
        sc.box(-14.5, -13.5, z0 + 7, 14.5, 3.5, z0 + 11, WHITE, base=2.8, k=1.9, tag='skirt', mix=0.3)
    sc.box(-16, -15, 46, 16, 5, 50, SLATE, base=2.4, k=1.9, tag='zinc', round_=1.0, mix=0.2)
    sc.box(-16, -7, 50, 16, -3, 56, SLATE, base=2.6, k=1.9, tag='zinc', round_=2.0, mix=0.3)
    sc.box(-9, 2, 13, 9, 8, 14.5, WHITE, base=2.9, k=1.4, tag='board', mix=0.3)
    a = _shade(sc)
    _rich(sc, a, ('leg', 'plinth', 'lift', 'skirt', 'board'), seed, grain=0.6, sigma=4.0, sets=WHITE[:2])
    _rich(sc, a, ('zinc',), seed + 3, grain=0.8, sets=SLATE + [('iron', 'slate_cool', 'ash')])
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    # the lifts' boards and the shadow under each skirt
    lift = _tagm(sc, 'lift')
    V._step(a, lift & (((Yg - sc.oy) % 4) == 0), -1)
    sk = _tagm(sc, 'skirt')
    below = np.zeros((H, W), bool)
    below[1:] = sk[:-1]
    V._step(a, below & lift, -1)
    ent = (np.abs(Xg - sc.ox) < 6) & (Yg >= sc.oy - 2 - 17) & (Yg < sc.oy - 2 - 15)
    a[ent] = C('void', 1)
    # weather: a few grey streaks, a moss line on the roof's north
    st = (lift | sk) & (K.vhash(Xg // 2, Yg // 3, seed) > 0.9)
    a[st] = C('stone_cool', 3)
    roof = _tagm(sc, 'zinc')
    a[roof & (sc.gy < -12) & (K.vhash(Xg // 2, Yg, seed + 1) > 0.6)] = C('leaf_cool', 2)
    rust = roof & (K.vhash(Xg // 2, Yg // 2, seed + 2) > 0.9)
    a[rust] = C('fox', 2)
    _finish(a)
    # two bees at the board (2 x 1 marks, no outline)
    for (bx, by) in ((sc.ox - 4, sc.oy - 21), (sc.ox + 6, sc.oy - 24)):
        a[by, bx:bx + 2] = C('lamp', 3)
        a[by + 1, bx:bx + 2] = C('void', 2)
    B._ground_tufts(a, sc.ox, sc.oy + 3, [-17, -11, 11, 17], seed)
    return K.crop(a, sc.ox, sc.oy)


def skep(seed=173):
    """A straw skep on a stone stool under a little thatched hackle: coiled straw rope in rings
    (each lit along its top), bound with split bramble, the entrance notch dark at its foot."""
    sc = K.Scene(-22, 22, -16, 14, 66)
    sc.box(-12, -10, 0, 12, 4, 12, GRIT, base=2.5, k=1.8, tag='stool', round_=1.5, tex='stone', mix=0.4)
    sc.ellipsoid(0, -3, 12, 10.5, 10, 18, STRAW, base=2.4, k=1.9, tag='skep', mix=0.3)
    sc.ellipsoid(0, -3, 31, 9, 9, 7, STRAW, base=2.2, k=1.9, tag='hackle', mix=0.7)
    a = _shade(sc)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    sk = _tagm(sc, 'skep')
    z = sc.depth
    coil = (z % 3.0)
    V._step(a, sk & (coil < 0.9), -1)
    V._step(a, sk & (coil > 2.2) & (sc.light() > 0), 1)
    bind = sk & (((Xg - sc.ox + 40) % 6) == 0) & (coil < 1.5)
    a[bind] = C('timber_cool', 2)
    hk = _tagm(sc, 'hackle')
    V._step(a, hk & (((Xg + Yg // 3) % 3) == 0), -1)                    # the hackle's straws
    notch = (np.abs(Xg - sc.ox) < 2.5) & (Yg >= sc.oy - 3 - 15) & (Yg < sc.oy - 3 - 12) & sk
    a[notch] = C('void', 1)
    B._lichen(sc, a, tags=('stool',), rate=0.9, seed=seed)
    _finish(a)
    a[sc.oy - 16, sc.ox + 4:sc.ox + 6] = C('lamp', 3)
    a[sc.oy - 15, sc.ox + 4:sc.ox + 6] = C('void', 2)
    B._ground_tufts(a, sc.ox, sc.oy + 3, [-14, -9, 10, 14], seed)
    return K.crop(a, sc.ox, sc.oy)


# ================================================================================================
# pieces
# ================================================================================================
_fp, _rel = B._fp, B._rel
OFF_ROUTE, OFF_WATER = B.OFF_ROUTE, B.OFF_WATER
NATURE = [OFF_ROUTE, OFF_WATER]
EW_COAST = '22 (crates, barrels and stakes on brick plinths, 0.5 to 1.2 A), 30 (rope rails on posts); no harbour in the local refs'
EW_HALT = '21 (the street front: lamp posts 2.3 A, posters and boards on posts, timber and painted trim)'
EW_MILL = '17 (the farm: cart, fence, sacks), 12 (the boulder wall and the stepping stones in water)'
EW_RURAL = '12 (the thatched hut, the boulder wall, the stepping stones), 13 (the standing stones)'


def prop_jobs():
    J = []

    def add(pid, variants, **kw):
        J.append((pid, variants, kw))
    # Driftwood quay and the lighthouse
    add('coast_net_rack', [('still', lambda: net_rack())], name='Net rack', purpose='store', role='rack', cells=(4, 1), fp=_fp(4, 1),
        collision={'shape': 'rect', 'rect': [-14.0, -2.0, 28, 3]}, shadow=(32, 4), composition='edge',
        requires=[_rel('near', 'water', 4, 'nets are hung to dry on the quay, by the boats that set them')],
        forbids=[OFF_WATER], size_class='rack (a net rack 1.6 m to its rail, 3 to 4 m long)', eastward=EW_COAST,
        note='Three oak posts and a rail with a green net hung to dry over it, cork floats on its head, two glass floats.')
    add('coast_lobster_pots', [('a', lambda: lobster_pots('a')), ('b', lambda: lobster_pots('b'))], name='Lobster pots',
        purpose='store', role='store', cells=(2, 1), fp=_fp(2, 1),
        collision={'shape': 'rect', 'rect': [-7.0, -3.0, 14, 4]}, shadow=(16, 3), composition='cluster',
        requires=[_rel('near', 'water', 3, 'creels stacked on the quay between trips')], forbids=[OFF_WATER],
        size_class='crate_stack (a creel 0.5 m long; three stacked 0.6 m)', eastward=EW_COAST,
        note='Withy creels on timber bases: three stacked (a), or one with a coil of rope and its float (b).')
    add('coast_mooring_bitt', [('still', lambda: mooring_bitt())], name='Mooring bitt', purpose='contain', role='mooring',
        cells=(1, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-2.5, -2.5, 5, 4]}, shadow=(8, 2), composition='edge',
        requires=[_rel('near', 'water', 1, 'on the quay\'s edge, where a boat\'s line is made fast')], forbids=[OFF_WATER],
        size_class='mooring bitt (0.5 m: 22 tall)', eastward=EW_COAST,
        note='A cast-iron bitt on a bolted plate, a hawser round it and trailing off.')
    add('coast_boat_beached', [('still', lambda: boat_beached())], name='Beached boat', purpose='mark', role='boat',
        cells=(4, 2), fp=_fp(4, 1), collision={'shape': 'rect', 'rect': [-14.0, -6.0, 28, 6]}, shadow=(30, 5), composition='free',
        requires=[_rel('near', 'water', 4, 'drawn up the beach above the tide line')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='boat (a 3.5 m clinker rowing boat, 0.6 m to its gunwale)', eastward=EW_COAST,
        note='A clinker rowing boat drawn up on the shingle: lapped strakes, blue and white, red below; thwarts and an oar inside.')
    add('coast_buoy', [('still', lambda: buoy())], name='Buoy', purpose='guide', role='marker', cells=(1, 1), fp=_fp(1, 1),
        collision={'shape': 'none'}, shadow=None, blocks=False, composition='free',
        requires=[_rel('on', 'water', note='a can buoy moored off the quay, marking the channel')],
        extra={'provides': ['view']}, size_class='buoy (a can buoy 0.6 m above the water)', eastward=EW_COAST,
        note='A red can buoy with a white band and its cage, riding the swell (8 frames), held still under reduced motion.')
    add('coast_harbour_light', [('still', lambda: harbour_light())], name='Harbour light', purpose='light', role='beacon',
        cells=(2, 2), fp=_fp(2, 2), collision={'shape': 'rect', 'rect': [-4.5, -4.5, 9, 9]}, shadow=(16, 6), composition='edge',
        requires=[_rel('near', 'water', 1, 'at the quay\'s head, its light over the harbour mouth')], forbids=[OFF_WATER],
        extra={'provides': ['feature', 'view']},
        size_class='harbour light (a quay-head tower 2.4 m to the lantern)', eastward=EW_COAST + '; 21 (the lamp heads)',
        note='A white tower banded red, its gallery and lantern; the lamp\'s glow swells and eases (8 frames).')
    # the Halt
    add('halt_platform_edge', [('a', lambda: platform_edge('a')), ('b', lambda: platform_edge('b'))], name='Platform edge',
        purpose='cross', role='platform', cells=(1, 1), fp=[[0, -1]], collision={'shape': 'none'}, shadow=None, blocks=False,
        composition='edge', requires=[_rel('near', 'route', 3, 'the platform runs beside the lane the halt serves')],
        forbids=[OFF_WATER], size_class='platform (0.9 m: a front of 12 and a coping)', eastward=EW_HALT,
        note='One cell of the platform\'s edge along x: stone courses, a coping with a white lip, gravel behind; cells meet.')
    add('halt_waiting_shelter', [('still', lambda: waiting_shelter())], name='Waiting shelter', purpose='rest', role='shelter',
        cells=(4, 2), fp=_fp(4, 2), collision={'shape': 'rect', 'rect': [-14.0, -10.0, 28, 4]}, shadow=(32, 6), composition='edge',
        requires=[_rel('near', 'route', 5, 'on the platform, open to the line, a few steps from the lane')], forbids=[OFF_ROUTE, OFF_WATER],
        extra={'provides': ['feature']},
        size_class='shelter (2.4 m wide, 2.2 m to its roof)', eastward=EW_HALT,
        note='A green-and-cream timber lean-to with a slate roof, a bench inside and a poster frame.')
    add('halt_churn_stand', [('still', lambda: churn_stand())], name='Milk-churn stand', purpose='store', role='store',
        cells=(3, 1), fp=_fp(3, 1), collision={'shape': 'rect', 'rect': [-8.0, -4.0, 16, 4]}, shadow=(22, 4), composition='edge',
        requires=[_rel('near', 'route', 1, 'at the lane\'s side, where the cart sets the churns down for the train')],
        forbids=[OFF_ROUTE, OFF_WATER], size_class='stand (cart-bed height 0.4 m; a churn 0.7 m)', eastward=EW_HALT + '; ' + EW_MILL,
        note='A timber stand at cart height with three galvanised churns on it and one beside.')
    add('halt_semaphore', [('still', lambda: semaphore())], name='Semaphore signal', purpose='guide', role='signal',
        cells=(2, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-2.0, -2.0, 4, 4]}, shadow=(8, 3), composition='edge',
        requires=[_rel('near', 'route', 3, 'at the platform\'s end, where the driver sees it')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='signal (a semaphore post 3 m)', eastward=EW_HALT,
        note='A white post with a ladder, the red arm with its stripe at danger, the spectacle\'s red and green glasses.')
    add('halt_platform_lamp', [('still', lambda: platform_lamp())], name='Platform lamp', purpose='light', role='lamp',
        cells=(1, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 3]}, shadow=(6, 2), composition='edge',
        requires=[_rel('near', 'route', 5, 'along the platform, lighting the way from the lane to the train')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='lamp (107 to 178 tall: a platform lamp 2.8 m)', eastward=EW_HALT,
        note='A fluted green column, the lantern\'s flame flickering (8 frames), the halt\'s name plate in marks.')
    add('halt_timetable_board', [('still', lambda: timetable_board())], name='Timetable board', purpose='guide', role='notice',
        cells=(2, 1), fp=_fp(2, 1), collision={'shape': 'rect', 'rect': [-7.0, -1.0, 14, 2]}, shadow=(16, 3), composition='edge',
        requires=[_rel('near', 'route', 2, 'by the platform\'s entrance from the lane')], forbids=[OFF_ROUTE, OFF_WATER],
        extra={'provides': ['feature']},
        size_class='notice board (81 to 126 tall, 44 to 89 wide)', eastward=EW_HALT,
        note='A cream sheet under a slate hood, its rows in pictograms (clock, arrow, train, stop), no words.')
    # the Millrace landslip
    add('mill_wheel', [('still', lambda: mill_wheel())], name='Mill wheel', purpose='work', role='wheel', cells=(5, 3),
        fp=_fp(5, 2), collision={'shape': 'rect', 'rect': [-18.0, -11.0, 36, 11]}, shadow=None, composition='edge',
        requires=[_rel('near', 'water', 2, 'the wheel sits in the leat that drives it')], forbids=[OFF_ROUTE],
        extra={'provides': ['feature', 'water', 'view']},
        size_class='mill wheel (an undershot wheel 3.4 m across against the gable)', eastward=EW_MILL,
        note='An undershot oak wheel on the mill\'s gable, turning one paddle\'s pitch over 8 frames; white water at the strike.')
    add('mill_sluice', [('still', lambda: sluice())], name='Sluice gate', purpose='water', role='sluice', cells=(3, 2),
        fp=_fp(3, 1), collision={'shape': 'rect', 'rect': [-12.0, -4.0, 24, 4]}, shadow=None, composition='edge',
        requires=[_rel('near', 'water', 1, 'at the leat\'s head, holding back the race')], forbids=[OFF_ROUTE],
        extra={'provides': ['feature', 'water']},
        size_class='sluice (piers 0.75 m, the rack to 1 m above)', eastward=EW_MILL,
        note='Two stone piers, an oak gate drawn up on its rack with a handwheel, the water white under it.')
    add('mill_millstones', [('still', lambda: millstones())], name='Millstones', purpose='store', role='store', cells=(4, 2),
        fp=_fp(4, 1), collision={'shape': 'rect', 'rect': [-14.0, -5.0, 28, 6]}, shadow=(26, 4), composition='edge',
        requires=[_rel('near', 'route', 3, 'in the miller\'s yard, by the door they will be carried through')],
        forbids=[OFF_ROUTE, OFF_WATER], size_class='millstones (1.2 m across)', eastward=EW_MILL,
        note='A dressed millstone flat, one on edge against a post, a sack of meal with its flour spilled.')
    add('mill_landslip', [('still', lambda: landslip())], name='Landslip', purpose='mark', role='barrier', cells=(6, 3),
        fp=_fp(6, 2), collision={'shape': 'rect', 'rect': [-22.0, -14.0, 44, 14]}, shadow=None, blocks=False, composition='free',
        requires=[_rel('on', 'route', note='the slip lies across the road: way W3, cleared once the Millrace is mended')],
        extra={'provides': ['feature']},
        size_class='landslip (a tongue of earth 6 m across, 1.5 m deep)', eastward='13 (the rockfall and boulders, 0.4 to 1.4 A)',
        story={'owner': None, 'lore': 'Way W3 (world-plan.md 6): the Millrace landslip on the Foothill Road; the way system '
                                      '(world-unlocks.md) holds the road shut, this piece is its picture', 'gating': {'act': 1}},
        note='Wet earth across the road with boulders in it, a snapped birch with its root plate, mud in lobes.')
    add('mill_fence_broken', [('still', lambda: fence_broken())], name='Broken rail fence', purpose='mark', role='story',
        cells=(3, 1), fp=_fp(3, 1), collision={'shape': 'rect', 'rect': [-13.0, -1.0, 26, 2]}, shadow=(26, 3), composition='edge',
        requires=[_rel('near', 'route', 3, 'the field fence the slip knocked down beside the road')], forbids=[OFF_WATER],
        size_class='fence (41 to 67 tall)', eastward=EW_MILL,
        note='A snapped post, a leaning one, the top rail split and hanging to the grass.')
    # Old Fang's barrow
    add('barrow_entrance', [('still', lambda: barrow_entrance())], name="Old Fang's barrow", purpose='mark', role='tomb',
        cells=(7, 4), fp=[[c, -r] for r in range(4, 0, -1) for c in range(-3, 4)],
        collision={'shape': 'rect', 'rect': [-22.0, -22.0, 44, 20]}, shadow=None, composition='free',
        requires=[_rel('near', 'route', 5, 'off the path on its own rise, reached by a short trod')], forbids=NATURE,
        extra={'provides': ['feature', 'view']},
        size_class='barrow (a mound 9 m long; the portal 0.8 m wide, 1.1 m high)', eastward=EW_RURAL,
        story={'owner': None, 'lore': "Old Fang's barrow (the map legend's Act 1 beat)", 'gating': {'act': 1}},
        note='A turf mound with a portal of two uprights and a capstone, the passage dark, kerb stones either side.')
    add('barrow_kerb', [('a', lambda: kerb_stone('a')), ('b', lambda: kerb_stone('b')), ('c', lambda: kerb_stone('c'))],
        name='Kerb stone', purpose='mark', role='marker', cells=(1, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-3.0, -1.5, 6, 3]}, shadow=(8, 2), composition='cluster',
        requires=[_rel('near', 'barrow_entrance', 6, 'a stone of the ring round the barrow\'s foot')], forbids=NATURE,
        size_class='kerb stone (0.3 to 0.4 m)', eastward=EW_RURAL,
        note='A low gritstone slab on edge with lichen and moss; three shapes.')
    # beehives
    add('hive_wbc', [('still', lambda: wbc_hive())], name='Beehive', purpose='work', role='hive', cells=(2, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 6]}, shadow=(12, 3), composition='cluster',
        requires=[_rel('near', 'route', 3, 'in a garden or an orchard by the path, its entrance to the morning sun')],
        forbids=[OFF_ROUTE, OFF_WATER], size_class='hive (a WBC hive 1.2 m with its roof)', eastward='12 and 37 (the garden props)',
        note='A white WBC hive: legs, plinth, three lifts with their skirts, gabled roof, two bees at the board.')
    add('hive_skep', [('still', lambda: skep())], name='Straw skep', purpose='work', role='hive', cells=(2, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-4.0, -3.0, 8, 5]}, shadow=(10, 3), composition='cluster',
        requires=[_rel('near', 'route', 3, 'on its stool by a cottage garden wall')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='skep (0.45 m on a 0.3 m stool)', eastward='12 and 37 (the garden props)',
        note='A coiled straw skep on a stone stool under a straw hackle, bound with bramble, a bee at its notch.')
    return J


def jobs():
    return prop_jobs()


def _piece(pid, name, variants, size, cells, purpose, role, **kw):
    p = B._piece(pid, name, variants, size, cells, purpose, role, **kw)
    p['variants'] = [{'id': vid, 'weight': w, 'png': RES + png, 'foot': list(foot)} for (vid, w, png, foot) in variants]
    p['biomes'] = ['coast', 'valley', 'brackens']
    p['audit']['painter'] = {'module': 'scripts.art.kit.sets.act1', 'fn': kw.get('fn') or pid, 'args': {}}
    p['audit']['seeded_from'] = 'scripts/art/kit/sets/act1.py'
    return p


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
            png = '%s_%s.png' % (pid, vid) if len(vs) > 1 or vid != 'still' else pid + '.png'
            out[os.path.join(ART, png)] = to_rgba(r.a)
            if frames:
                out[os.path.join(ART, png[:-4] + '_loop.png')] = to_rgba(K.strip(frames['frames']))
        kw = dict(kw)
        name, purpose, role = kw.pop('name'), kw.pop('purpose'), kw.pop('role')
        cells, fp = kw.pop('cells'), kw.pop('fp')
        variants = []
        for vid, r, frames in pics:
            png = '%s_%s.png' % (pid, vid) if len(vs) > 1 or vid != 'still' else pid + '.png'
            variants.append((vid, 1.0 if not variants else 0.6, png, (r.ax, r.ay)))
            if frames:
                f0 = frames['frames'][0]
                kw['anim'] = {'clip': frames['clip'], 'loop': True, 'frames': len(frames['frames']), 'fps': frames['fps'],
                              'strip': RES + png[:-4] + '_loop.png', 'frame_px': [f0.W, f0.H], 'reduced_motion': 'hold:0',
                              'on_screen_only': True}
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
        print('act1: stale pictures %s (run python3 -m scripts.art.kit.sets.act1)' % ', '.join(bad[:6]))
        return 1
    print('act1: pictures current')
    return 0


AUDIT = {pid: (kw['purpose'], kw['role'], None, None, 'fine', 'Act 1 set (scripts/art/kit/sets/act1.py): ' + kw['note'])
         for pid, _vs, kw in jobs()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    print('act1: %d pictures' % len(build(force=a.force, only=a.only)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

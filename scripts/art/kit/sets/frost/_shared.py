"""Shared Frostline painter helpers and palette constants."""
from __future__ import annotations


import argparse

import json

import math

import os

import sys


import numpy as np

from PIL import Image

from scipy import ndimage as ndi


from scripts.art.kit.schema import PIECES, ROOT

from scripts.art.kit.sets import _common as K

from scripts.art.kit.sets import brackens as B

from scripts.art.kit.sets._common import C, hsh

from scripts.art.native import village as V

from scripts.art.native.palette import FI, LUT, to_rgba


ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'frost')

RES = 'res://kit/props/art/frost/'

STANDARD = ("eastward-edges.md 5.1 and 5.5, art-style.md density 3; the Frostline brief (snow lying on what faces the "
            "sky, granite and slate, lake ice)")

BIOMES = ['frostline']

OAK = B.OAK



# ================================================================================================
# helpers
# ================================================================================================
def _grow(p: V.Pic, top: int, side: int = 0) -> V.Pic:
    """The same picture on a canvas `top` texels taller (and `side` wider each side)."""
    q = V.Pic(p.W + 2 * side, p.H + top, p.ax + side, p.ay + top)
    q.a[top:, side:side + p.W] = p.a
    return q



# ================================================================================================
# the props (round 2: the detail audit of #478, F-H1 to F-S1 and Z2, Z5, Z6; the logic audit's B5, B6)
# ================================================================================================
# Scene units are ground texels at density 3 (a cell is 24, an adult 74). Snow is drawn as solids
# lying on what faces the sky (a cap on a stone's top plane, a slab on a ledge), so the renderer
# shades it with the light and closes its outline like any material: no halo, no flecks.
GRANITE = [('slate_cool', 'slate', 'slate'), ('iron', 'slate', 'slate'), ('slate_cool', 'iron', 'slate')]

SNOW = [('snow_cool', 'snow', 'snow'), ('snow_cool', 'snow', 'snow_warm')]

WEATHERED = [('soot', 'ash', 'ash'), ('stone_cool', 'ash', 'ash')]

RED = [('berry_cool', 'berry', 'clay')]



def _solo(sc, dress=None):
    return B._solo(sc, dress=dress)



def _snowcap(sc, cx, cy, ztop, rx, ry, th=3.2, seed=0):
    """A cap of snow on a top plane: a flattened mass, a little west of centre (the wind lays it from
    the east), lit by the renderer on its top and west, cool on its east fall."""
    sc.ellipsoid(cx - rx * 0.06, cy - ry * 0.05, ztop + th * 0.25, rx, ry, th, SNOW, base=3.9, k=1.1, tag='snow',
                 mix=hsh(seed, 3) * 0.6, flat=1.5)



def _drift_west(sc, x, y, r, seed=0):
    """A drift banked against an object's west foot (the windward side)."""
    sc.ellipsoid(x - r * 0.4, y + 1.5, 0.6, r, r * 0.55, r * 0.32, SNOW, base=3.8, k=1.0, tag='drift', mix=hsh(seed, 5) * 0.6,
                 flat=1.1)



# granite's grain (round 3, R2-R1 and R2-F1): clusters of three or four texels that swap to a sibling
# ramp at the same value (feldspar, quartz, hornblende: shape without value noise, house-style 4),
# a few stepping a tone up on lit planes or down in shade
GR_SIB = {'slate': (('slate_warm', 0), ('slate_cool', 0), ('stone_cool', 0)),
          'slate_cool': (('slate', 0), ('iron', 1), ('slate_warm', 0)),
          'slate_warm': (('slate', 0), ('stone_cool', 0), ('ashlar', -1)),
          'iron': (('slate_cool', -1), ('soot', 1), ('slate', -1)),
          'stone_cool': (('slate_warm', 0), ('stone', 0), ('slate', 0)),
          'stone': (('stone_cool', 0), ('stone_warm', 0), ('ashlar', 0)),
          'stone_warm': (('stone', 0), ('ashlar', 0)),
          'ash': (('stone_cool', 0), ('slate_warm', 0), ('ashlar', 0)),
          'soot': (('iron', -1), ('ash', -1))}

SNOWS = {FI['snow'], FI['snow_warm'], FI['snow_cool']}



def _grain(a, m, seed, swap=0.45, step=0.10, lit=None, drop_p=0.4):
    """Granite's grain on the texels `m` (see GR_SIB): 2 x 2 cells staggered row pair to row pair,
    texels of a cell left at random (blobs of two to four, never one); `lit` (a mask) takes the steps
    up. Laid after the despeckle, so the two-texel grains stay."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    cx, cy = (X + (Y // 2) % 2) // 2, Y // 2
    drop = K.vhash(X, Y, seed + 1) < drop_p
    cell = (cy * 4099 + cx)
    keep = ~drop & m
    n_in = ndi.sum(keep, cell, index=None) if False else None
    flat = cell.ravel()
    cnt = np.bincount(flat - flat.min(), weights=keep.ravel().astype(float))
    lone = (cnt[flat - flat.min()] < 2).reshape(H, W)
    drop = drop | lone
    h = K.vhash(cx, cy, seed)
    pick = K.vhash(cx, cy, seed + 2)
    fam, t = a // 8, a % 8
    cl = m & (h < swap) & ~drop & (a >= 0)
    for f, sibs in GR_SIB.items():
        sel = cl & (fam == FI[f])
        k = np.minimum((pick * len(sibs)).astype(int), len(sibs) - 1)
        for j, (g, dt) in enumerate(sibs):
            s2 = sel & (k == j)
            a[s2] = FI[g] * 8 + np.clip(t[s2] + dt, 0, 5)
    st = m & (a >= 0) & (h > 1 - step) & ~drop
    if lit is None:
        lit = np.zeros_like(m)
    up, dn = st & lit, st & ~lit
    a[up] = (a[up] // 8) * 8 + np.clip(a[up] % 8 + 1, 0, 5)
    a[dn] = (a[dn] // 8) * 8 + np.clip(a[dn] % 8 - 1, 0, 5)



def _snow_light(sc, a, tags=('snow', 'drift'), swell=0.16):
    """Snow shaded by its own planes: the lit top and west (snow 5), the body (snow 4), the turn
    (snow_cool 4), the cool east and front fall (snow_cool 3), the underside where it overhangs
    (snow_cool 2), with wind-laid swells in clusters across the planes; under every snow mass that
    overhangs stone a blue shade row on the stone (the lip's shadow)."""
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag in tags]
    m = np.isin(sc.label, ids)
    if not m.any():
        return m
    L = sc.light()
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    sw = K.vhash((X + Y // 3) // 3, Y // 2, 77) * swell
    v = L + sw
    code = np.where(v > 0.86, C('snow', 5), np.where(v > 0.7, C('snow', 4), np.where(v > 0.48, C('snow_cool', 4),
                    np.where(v > 0.1, C('snow_cool', 3), C('snow_cool', 2)))))
    a[m] = code[m]
    below = np.zeros_like(m)
    below[1:] = m[:-1]
    under = below & ~m & (a >= 0) & ~np.isin(a // 8, list(SNOWS))
    a[under] = C('sky_cool', 2)
    return m



def _fractures(a, m, seed, n=2, lit_side=True):
    """Fracture lines across granite: a dark run 1 texel wide bending down and across the stone,
    a lit texel on its upper west lip; the stone east of a fracture a tone down (a plane turned
    from the light)."""
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    H, W = a.shape
    for _ in range(n):
        k = int(rng.integers(0, len(ys)))
        y, x = float(ys[k]), float(xs[k])
        dx = rng.choice((-0.8, -0.4, 0.4, 0.8))
        path = []
        for _j in range(int(rng.integers(6, 16))):
            yi, xi = int(round(y)), int(round(x))
            if not (0 <= yi < H and 0 <= xi < W) or not m[yi, xi]:
                break
            path.append((yi, xi))
            y += 1.0
            x += dx + rng.uniform(-0.4, 0.4)
        for yi, xi in path:
            a[yi, xi] = C('slate_cool', 0)
            if lit_side and xi - 1 >= 0 and m[yi, xi - 1]:
                a[yi, xi - 1] = (a[yi, xi - 1] // 8) * 8 + min(5, a[yi, xi - 1] % 8 + 1)
            for d in (1, 2):
                if xi + d < W and m[yi, xi + d] and a[yi, xi + d] >= 0 and a[yi, xi + d] // 8 not in SNOWS:
                    a[yi, xi + d] = (a[yi, xi + d] // 8) * 8 + max(1, a[yi, xi + d] % 8 - 1)



def _granite_dress(sc, a, seed, tags=('rock',), n_frac=2, swap=0.45):
    """The granite's surface after shading: grain, fractures, the snow's own planes and the shade
    under each lip."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags])
    _fractures(a, m & ~(sc.n[..., 2] > 0.8), seed + 5, n=n_frac)
    _snow_light(sc, a)



def _grain_after(sc, a, seed, tags=('rock',), swap=0.6, step=0.08, crust=0.3):
    """The grain laid on a finished picture (after the despeckle and the outline): only on the
    stone's own texels, not its outline."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags]) & (a >= 0) & (a % 8 >= 1)
    m &= ~np.isin(a // 8, list(SNOWS)) & (a != C('sky_cool', 2))
    _grain(a, m, seed, swap=swap, step=step, lit=sc.light() > 0.45)
    if crust:
        _crust(sc, a, seed, rate=crust)



SNOW_LADDER = [C('snow_cool', 2), C('snow_cool', 3), C('snow_cool', 4), C('snow', 4), C('snow', 5)]



def _crust(sc, a, seed, tags=('snow', 'drift'), rate=0.3):
    """The snow's wind crust: short runs of two to four texels along the wind (west to east), each a
    step down the ladder on the lit planes and a step up in the cool ones; none on the outline."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags]) & np.isin(a, SNOW_LADDER)
    m &= ndi.binary_erosion(a >= 0)
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    off = (K.vhash(Y, Y // 2, seed + 9) * 4).astype(int)
    run = (X + off) // 3
    h = K.vhash(run, Y, seed + 4)
    tip = K.vhash(X, Y, seed + 6) < 0.25
    sel = m & (h < rate) & ~tip
    idx = {c: i for i, c in enumerate(SNOW_LADDER)}
    for c, i in idx.items():
        s2 = sel & (a == c)
        j = i - 1 if i >= 3 else i + 1
        a[s2] = SNOW_LADDER[max(0, min(4, j))]



def _block(sc, cx, cy, w, d, h, seed, base=2.8, z0=0.0, tilt=0.0):
    """One granite block: a rounded box (flat top, front, rounded arrises) with a lower shoulder
    knocked off one corner and a chamfer, so it reads as a weathered block, not a ball."""
    rng = np.random.default_rng(seed)
    mix = rng.random()
    r = min(w, d, h) * rng.uniform(0.28, 0.4)
    sc.box(cx - w / 2, cy - d / 2, z0, cx + w / 2, cy + d / 2, z0 + h, GRANITE, base=base, k=1.9, tag='rock', round_=r,
           mix=mix, tex='stone')
    # a shoulder: a lower step on the east or west of the block (a fracture plane), set forward
    side = 1 if rng.random() < 0.6 else -1
    sw = w * rng.uniform(0.3, 0.45)
    sh = h * rng.uniform(0.45, 0.7) + tilt
    x0 = cx + side * (w / 2 - sw * 0.6) - sw / 2
    sc.box(x0, cy - d / 2 + 1.5, z0, x0 + sw, cy + d / 2 + rng.uniform(0.5, 2.0), z0 + sh, GRANITE, base=base - 0.3, k=1.9,
           tag='rock', round_=min(sw, sh) * 0.35, mix=(mix + 0.37) % 1.0, tex='stone')



def _cap(sc, cx, cy, ztop, w, d, seed, th=4.0, over=1.5):
    """Snow with thickness on a block's top: a slab a little smaller than the top, heaped west of
    centre, its front hanging `over` texels past the block's front (a lip with shade under it)."""
    rng = np.random.default_rng(seed)
    sc.ellipsoid(cx - w * 0.08, cy - d * 0.1 + over * 0.5, ztop + th * 0.35, w * 0.5, d * 0.5 + over * 0.5, th, SNOW,
                 base=3.9, k=1.1, tag='snow', flat=2.2)
    if w > 14:
        sc.ellipsoid(cx - w * 0.25, cy - d * 0.15, ztop + th * 0.6, w * 0.3, d * 0.35, th * 0.9, SNOW, base=3.9, k=1.1,
                     tag='snow', flat=1.6, mix=rng.random())



def _mass(sc, cx, cy, rx, ry, rz, seed, base=3.2, flat=2.3):
    """A weathered granite mass: a superellipsoid seated on the ground (flat faces, rounded arrises)."""
    sc.ellipsoid(cx, cy, rz * 0.92, rx, ry, rz, GRANITE, base=base, k=1.9, tag='rock', mix=hsh(seed, 17), flat=flat,
                 tex='stone')



def _rock(sc, cx, cy, w, d, h, seed, cap=True, drift=True):
    """A granite boulder (round 3, R2-R1): a main mass of jointed granite with a lower mass split
    from it on the east and a chip on the west, so its outline breaks in planes; a snow cap with
    thickness on the top plane (heaped west, lumped, hanging a little over the front), a drift
    banked at the west foot."""
    rng = np.random.default_rng(seed)
    rx, ry, rz = w / 2, d / 2, h / 2
    _mass(sc, cx, cy, rx, ry, rz, seed, flat=2.4 + rng.uniform(0, 0.5))
    if w > 12:
        _mass(sc, cx + rx * 0.62, cy + ry * 0.35, rx * 0.55, ry * 0.65, rz * rng.uniform(0.5, 0.65), seed + 3, base=2.5,
              flat=2.2)
        _mass(sc, cx - rx * 0.7, cy + ry * 0.45, rx * 0.35, ry * 0.45, rz * 0.4, seed + 5, base=2.7, flat=2.0)
    if cap:
        th = max(2.4, min(4.5, h * 0.2))
        top = rz * 0.92 + rz - th * 0.45
        sc.ellipsoid(cx - rx * 0.12, cy - ry * 0.05, top, rx * 0.74, ry * 0.7, th, SNOW, base=3.9, k=1.1, tag='snow',
                     flat=1.7)
        sc.ellipsoid(cx - rx * 0.38, cy - ry * 0.2, top + th * 0.5, rx * 0.36, ry * 0.4, th * 0.85, SNOW, base=3.9, k=1.1,
                     tag='snow', flat=1.4)
        if w > 12:
            sc.ellipsoid(cx + rx * 0.62, cy + ry * 0.3, rz * 0.92 * 0.6 + rz * 0.6 * 0.95, rx * 0.36, ry * 0.4, th * 0.7, SNOW,
                         base=3.9, k=1.1, tag='snow', flat=1.5)
    if drift:
        r = max(4.0, w * 0.3)
        sc.ellipsoid(cx - rx * 0.85, cy + ry * 0.4, 0.2, r, r * 0.6, r * 0.6, SNOW, base=3.8, k=1.0, tag='drift', flat=1.0)



def _chip(sc, a, seed, tags=('rock',)):
    """Knock the arrises: notches of two and three texels taken out of the stone's outline (its
    silhouette breaks in planes, not in an ellipse)."""
    m = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags])
    edge = m & ~ndi.binary_erosion(m)
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    out = edge & (K.vhash(X // 3, Y // 2, seed) > 0.72) & (Y < np.nonzero(m.any(1))[0].max() - 2 if m.any() else True)
    a[out] = -1
    sc.label[out] = -1



def _cracks(sc, a, tags=('rock',), n=2, seed=0):
    """Crack lines on stone: short bending runs down a face in the shade tone, a lit texel on their
    west side."""
    lab = sc.label
    m = np.isin(lab, [i for i, s_ in enumerate(sc.solids) if s_.tag in tags])
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    rng = np.random.default_rng(seed)
    for _ in range(n):
        k = int(rng.integers(0, len(ys)))
        y, x = float(ys[k]), float(xs[k])
        for _j in range(int(rng.integers(5, 11))):
            yi, xi = int(y), int(x)
            if not (0 <= yi < a.shape[0] and 0 <= xi < a.shape[1]) or not m[yi, xi]:
                break
            a[yi, xi] = C('slate_cool', 1)
            if xi - 1 >= 0 and m[yi, xi - 1]:
                a[yi, xi - 1] = C('slate', 4)
            y += 1.0
            x += rng.choice((-1, 0, 0, 1)) * 0.6



def _rock_r2(sc, cx, cy, rx, ry, rz, seed, cap=True, drift=True):
    """Round 2's rounded boulder, kept for the small stone (it passed the r2 audit)."""
    rng = np.random.default_rng(seed)
    h = rz * 0.75
    sc.ellipsoid(cx, cy, h, rx, ry, h, GRANITE, base=2.9, k=1.8, tag='rock', mix=rng.random(), flat=3.2, tex='stone')
    sc.ellipsoid(cx + rx * 0.55, cy + ry * 0.3, h * 0.55, rx * 0.6, ry * 0.65, h * 0.6, GRANITE, base=2.6, k=1.8,
                 tag='rock', mix=rng.random(), flat=3.0, tex='stone')
    if rx > 10:
        sc.ellipsoid(cx - rx * 0.7, cy + ry * 0.45, h * 0.4, rx * 0.45, ry * 0.5, h * 0.45, GRANITE, base=2.7, k=1.8,
                     tag='rock', mix=rng.random(), flat=3.0, tex='stone')
    if cap:
        _snowcap(sc, cx - rx * 0.1, cy - ry * 0.12, 2 * h - 1.5, rx * 0.72, ry * 0.62, th=max(2.4, rz * 0.2), seed=seed)
    if drift:
        _drift_west(sc, cx - rx * 1.0, cy + ry * 0.4, max(4.0, rx * 0.45), seed)



# ------------------------------------------------------------------------------------------------
# the cirque's step (B7): a 32 px granite face with a snow lip, its stair and its frozen fall
# ------------------------------------------------------------------------------------------------
FACE_PX = 96          # the face's height in art px (32 world px, one Frostline tier: size guide)

LIP_PX = 12

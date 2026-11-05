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
from scripts.art.native import houses as Hs
from scripts.art.native import village as V
from scripts.art.native.palette import FI as FI_
from scripts.art.native.palette import to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'act1')
RES = 'res://kit/props/art/act1/'

GRIT, OAK = B.GRIT, B.OAK
# each material's sibling ramps (cool, body, warm): at one tone the bodies sit within about 10 L of
# each other, so a cluster swapping between them adds shape, not value noise (house-style.md 4)
GRANITE = [('slate_cool', 'stone', 'stone_warm'), ('stone_cool', 'stone_warm', 'stone_warm'), ('stone_cool', 'stone', 'stone')]
IRON = [('void', 'iron', 'iron'), ('soot', 'iron', 'iron')]
WHITE = [('snow_cool', 'snow_cool', 'snow'), ('snow_cool', 'snow', 'snow_warm'), ('snow_cool', 'snow', 'snow')]
RED = [('crag_cool', 'clay', 'clay'), ('clay_cool', 'clay', 'clay'), ('crag_cool', 'crag_warm', 'clay')]
GREEN = [('leaf_cool', 'leaf', 'leaf_warm'), ('leaf_cool', 'leaf_cool', 'leaf'), ('soot', 'leaf', 'leaf')]
CREAM = [('ashlar', 'plaster_warm', 'plaster_warm'), ('ashlar', 'plaster', 'plaster_warm'), ('ashlar_warm', 'plaster_warm', 'plaster_warm')]
SLATE = [('slate_cool', 'slate', 'slate_warm'), ('void', 'slate_cool', 'slate'), ('slate_cool', 'slate_warm', 'slate_warm')]
ROPE = [('earth_cool', 'sand_cool', 'sand'), ('timber_cool', 'sand_cool', 'sand_warm')]
WILLOW = [('timber_cool', 'timber_warm', 'brass'), ('earth_cool', 'timber', 'brass_warm')]
NET = [('soot', 'leaf_cool', 'grass_cool'), ('soot', 'leaf', 'grass_cool')]
TIN = [('slate_cool', 'stone', 'snow_cool'), ('slate_cool', 'stone_warm', 'snow_cool')]
TURF = [('leaf_cool', 'grass_cool', 'grass'), ('leaf_cool', 'grass', 'grass_warm'), ('leaf_cool', 'grass_cool', 'grass_cool')]
EARTH = [('soot', 'earth_cool', 'earth'), ('earth_cool', 'earth', 'earth_warm'), ('soot', 'earth', 'earth')]
STRAW = [('earth_cool', 'brass', 'sand_cool'), ('earth_cool', 'brass_warm', 'sand_cool'), ('timber_cool', 'brass', 'brass_warm')]
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


def _rich(sc, a, tags, seed, grain=0.9, sigma=3.0, ao=0.7, sets=None, cell=(2, 2), rate=0.08):
    """Repaint the named solids calmly (house-style.md 4; the detail audit of 4 Nov, finding 4): each
    solid's own ramp lit by the house light, contact shade where it meets the ground, and in 2 x 2
    clusters mostly a swap to a sibling family at the same tone (shape without value noise). A tone
    step falls on at most `rate` of the clusters and only with the form: +1 on lit planes, -1 in shade.
    `grain` scales those steps (0 turns them off)."""
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    L = sc.light()
    G = _form_steps(Xg, Yg, L, seed, rate, cell) * min(1.0, grain)
    mix = _sibling_mix((H, W), Xg, Yg, seed, sigma, cell)
    for i, s in enumerate(sc.solids):
        if s.tag not in tags:
            continue
        m = sc.label == i
        if not m.any():
            continue
        t = s.base + s.k * L + G - ao * (sc.depth < 2.5)
        rpaint(a, m, sets or s.sets, t, mix)
    return a


def _form_steps(X, Y, L, seed, rate=0.08, cell=(2, 2)):
    """A tone step in a few clusters, tied to the form: +1 where the plane faces the light, -1 where
    it turns away, nothing on the turning planes between."""
    g = K.vhash(X // cell[0], Y // cell[1], seed + 17)
    return np.where((g > 1.0 - rate) & (L > 0.25), 1.0, np.where((g < rate) & (L < -0.05), -1.0, 0.0))


def _sibling_mix(shape, X, Y, seed, sigma=3.0, cell=(2, 2)):
    """0..1 per texel: which of a material's sibling ramps a cluster takes, a smooth drift across the
    surface with a swap now and then in 2 x 2 clusters."""
    drift = K.noise(shape, np.random.default_rng(seed + 1), sigma)
    swap = K.vhash(X // cell[0], Y // cell[1], seed + 23)
    return np.clip(np.where(swap > 0.7, 1.0 - drift, drift) * 0.999, 0, 0.999)


def _tone(a):
    """The tone (0..5) of every painted texel (codes are family * 8 + tone)."""
    return np.where(a >= 0, a % 8, 0)


def _refam(a, m, sets, X, Y, seed, sigma=3.0, cell=(2, 2)):
    """Keep each texel's tone and repaint it in a sibling family: texture without value noise."""
    rpaint(a, m, sets, _tone(a), _sibling_mix(a.shape, X, Y, seed, sigma, cell))


def _planks(a, m, sets, base, u, v, seed, pitch=5, lit_lip=True, grain=0.07, joint=1.0):
    """Boards running along u, `pitch` texels across v: each board one calm tone in its own sibling
    ramp, its upper edge lit, a dark joint under it, the grain as sparse streaks 1 x 4 to 8 along the
    board, a knot now and then (house-style.md 5, wood)."""
    u = np.asarray(u).astype(int)
    v = np.asarray(v).astype(int)
    b = np.floor_divide(v, pitch)
    jv = v - b * pitch
    t = base + np.where((jv == 0) & lit_lip, 1.0, 0.0) - np.where(jv == pitch - 1, joint, 0.0)
    seg = np.floor_divide(u + (b * 7) % 11, 6)
    streak = (K.vhash(seg, b * 31 + jv, seed) < grain) & (jv > 0) & (jv < pitch - 1)
    t = t - 1.0 * streak
    knot = (K.vhash(np.floor_divide(u, 3), b, seed + 3) < 0.02) & (jv == pitch // 2)
    t = t - 1.0 * knot
    rpaint(a, m, sets, t, np.clip(K.vhash(b, 0, seed + 1) * 0.999, 0, 0.999))


def _streaks(a, m, X, Y, seed, rate=0.05, length=(4, 6), fam=None, step=-1):
    """Weathering running down a plane: 1-texel streaks `length` long from random starts (a rust run
    under a ledge, rain down whitewash). Steps the tone (or paints `fam` at the texel's tone)."""
    H, W = a.shape
    out = np.zeros((H, W), bool)
    ys, xs = np.nonzero(m & (K.vhash(X, Y // 3, seed) < rate))
    for y, x in zip(ys, xs):
        n = int(length[0] + (length[1] - length[0]) * K.hsh(x, y, seed))
        out[y:y + n, x] = True
    out &= m
    if fam is None:
        V._step(a, out, step)
    else:
        a[out] = C(fam, 0) + np.clip(_tone(a)[out] + step, 0, 5)
    return out


def _stone_parts(a, m, u, v, seed, sets, t, lo=8, hi=15, course=7, mortar=('slate_cool', 1), moss=None):
    """Dressed or rubble stone in parts `lo` to `hi` long and `course` high (u along the course, v up
    it): each part a calm tone of its own (the light in t), a lit top edge, a dark joint under it and
    at its end, the corner by the joint chipped, cracks now and then; `moss` (a v below which the low
    joints take moss)."""
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    ci = np.floor(v / course).astype(int)
    vin = v - ci * course
    si, spos, snxt = B._stone_joints(u + ci * 5.0, 1700 + seed + ci, lo=float(lo), hi=float(hi))
    off = np.round((K.vhash(si, ci, seed) - 0.5) * 1.2)
    tt = t + off
    top = vin > course - 1.2
    jnt = (vin < 1.0) | (snxt < 1.0)
    tt = np.where(top & ~jnt, tt + 1.0, tt)
    chip = (vin < 2.0) & (snxt < 2.0) & (K.vhash(si, ci, seed + 5) > 0.5)
    crack = (np.abs(spos - (snxt + spos) * 0.5) < 0.6) & (vin > 2) & (vin < course - 2) & (K.vhash(si, ci, seed + 7) > 0.88)
    tt = np.where(crack, tt - 1.0, tt)
    rpaint(a, m, sets, tt, np.clip(K.vhash(si, ci, seed + 1) * 0.999, 0, 0.999))
    jm = m & (jnt | chip)
    a[jm] = C(mortar[0], mortar[1])
    if moss is not None:
        mm = jm & (v < moss) & (K.vhash(si, 0, seed + 9) > 0.35)
        a[mm] = C('leaf_cool', 2)
    return jm


def _clods(a, m, X, Y, seed, rate=0.05, w=(3, 5)):
    """Earth or turf clods in drifts: a cluster 3 to 5 wide, its top row lit, its underside dark."""
    H, W = a.shape
    drift = K.noise((H, W), np.random.default_rng(seed + 31), 5.0) > 0.45
    ys, xs = np.nonzero(m & drift & (K.vhash(X // 3, Y // 2, seed) < rate))
    for y, x in zip(ys, xs):
        n = int(w[0] + (w[1] - w[0] + 1) * K.hsh(x, y, seed + 1))
        if y + 2 >= H or x + n >= W:
            continue
        if not m[y:y + 3, x:x + n].all():
            continue
        V._step(a, np.pad(np.ones((1, n), bool), ((y, H - y - 1), (x, W - x - n))), 1)
        V._step(a, np.pad(np.ones((1, n), bool), ((y + 2, H - y - 3), (x, W - x - n))), -1)


def _lathe(shape, fx, fy, prof, sq=0.4):
    """A round object turned on a lathe, seen as Eastward draws cans and churns: its rings flattened
    to ellipses (squash `sq`), stacked from the foot. prof[h] is the radius at height h (texels).
    Returns (mask, h, u, top): the height and the place across (-1 west .. 1 east) of every texel, and
    whether it lies on an upward face (the crown, or a ledge where the radius steps in)."""
    H, W = shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    x = Xg - fx + 0.5
    hm = np.full((H, W), -1.0)
    rm = np.ones((H, W))
    ym = np.zeros((H, W))
    for h, r in enumerate(prof):
        if r <= 0.4:
            continue
        cyy = fy - h
        e = (x / r) ** 2 + ((Yg + 0.5 - cyy) / max(0.5, sq * r)) ** 2 <= 1.0
        hm = np.where(e, h, hm)
        rm = np.where(e, r, rm)
        ym = np.where(e, Yg + 0.5 - cyy, ym)
    m = hm >= 0
    hi = np.clip(hm.astype(int), 0, len(prof) - 1)
    nxt = np.array([prof[min(len(prof) - 1, k + 1)] if k + 1 < len(prof) else 0.0 for k in range(len(prof))])
    front = sq * rm * np.sqrt(np.clip(1.0 - (x / np.maximum(rm, 1e-6)) ** 2, 0, 1))
    top = m & ((ym < front - 1.0) & ((nxt[hi] < rm - 0.7) | (hi == len(prof) - 1)))
    return m, hm, x / np.maximum(rm, 1e-6), top


def _turned(a, fx, fy, prof, sets, mix=0.3, lit=4.0, body=2.8, shade=1.5, top_t=3.8, sq=0.4):
    """Paint a lathe part (see _lathe) on canvas a: its sides lit as a cylinder, its upward faces lit.
    Returns (mask, h, u, top)."""
    m, hh, u, top = _lathe(a.shape, fx, fy, prof, sq)
    t = _cyl_tone(u, 1.0, lit=lit, body=body, shade=shade)
    t = np.where(top, top_t + 0.6 * (u < -0.2) - 0.6 * (u > 0.5), t)
    rpaint(a, m, sets, t, mix)
    return m, hh, u, top


def _cyl_tone(dx, r, lit=4.6, body=3.0, shade=1.4):
    """A standing cylinder's tones across its face (dx from its axis, r its radius): a highlight band
    left of centre, the body, a core shadow on the right third and a little reflected light at the
    very edge (never a diagonal split)."""
    u = np.asarray(dx, float) / max(1e-6, r)
    t = np.full(u.shape, body)
    t = np.where((u > -0.62) & (u < -0.12), lit, t)
    t = np.where((u >= -0.12) & (u < 0.0), (lit + body) / 2.0, t)
    t = np.where(u > 0.38, shade, t)
    t = np.where(u > 0.86, shade + 0.6, t)
    t = np.where(u < -0.82, body - 0.4, t)
    return t


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
def _coil_template(w=16, h=9, side=2):
    """A rope flaked down as a flat Flemish coil, seen mostly from the top (rounds 3 and 4 of the
    detail audit, R3-4, R4-3): three turns as rings about 14 x 7, 10 x 5 and 6 x 3, each turn 2
    texels with its upper-west arc lit (rope 4) over a body (rope 3); between turns a continuous seam
    two tones down (rope 1) on every side, broken only by a lay tick here and there; a dark eye about
    4 x 2; below, the outer turn's side `side` texels tall with the lay as diagonal ticks. Returns an
    (h + side) x w array of tone keys (-1 empty, 1..4 rope tones, 9 eye)."""
    def ell(box, fill):
        im = Image.new('L', (w, h + side), 0)
        d = ImageDraw.Draw(im)
        if fill:
            d.ellipse(box, fill=1)
        else:
            d.ellipse(box, outline=1, width=1)
        return np.asarray(im).astype(bool)
    top = ell((0, 0, w - 1, h - 1), True)
    foot = ell((0, side, w - 1, h - 1 + side), True)
    seam = (ell((2, 1, w - 3, h - 2), False) | ell((4, 2, w - 5, h - 3), False)) & top
    eye = ell((w // 2 - 2, h // 2 - 1, w // 2 + 1, h // 2), True)
    Yg, Xg = np.mgrid[0:h + side, 0:w]
    dxn = (Xg + 0.5 - w / 2.0) / (w / 2.0)
    dyn = (Yg + 0.5 - h / 2.0) / (h / 2.0)
    diag = dxn + dyn
    k = np.full((h + side, w), -1)
    k[top] = np.where(diag < -0.15, 4, np.where(diag > 0.9, 2, 3))[top]
    tick = seam & ((Xg * 3 + Yg * 5) % 11 == 0)                         # the lay crossing a seam
    k[seam] = np.where(tick, 2, 1)[seam]
    k[eye & top] = 9
    sd = foot & ~top
    st = np.where(dxn < -0.4, 3, np.where(dxn > 0.45, 1, 2))
    st = np.where((Xg + Yg) % 3 == 0, np.maximum(st - 1, 1), st)
    k[sd] = st[sd]
    return k


COIL = _coil_template()
COIL_C = {4: C('sand', 4), 3: C('sand_cool', 3), 2: C('sand_cool', 2), 1: C('sand_cool', 1), 9: C('earth_cool', 1)}


def _rope_coil(a, cx, cy, seed=0, **_kw):
    """Lay the COIL on canvas a with its foot's centre at (cx, cy), closed in the rope's own edge
    tone, a contact shade to the east."""
    H, W = a.shape
    h, w = COIL.shape
    x0, y0 = int(round(cx)) - w // 2, int(round(cy)) - h + 1
    coil = np.zeros((H, W), bool)
    tmp = np.full((H, W), -1, np.int32)
    for r in range(h):
        for c in range(w):
            y, x = y0 + r, x0 + c
            if COIL[r, c] >= 0 and 0 <= y < H and 0 <= x < W:
                tmp[y, x] = COIL_C[int(COIL[r, c])]
                coil[y, x] = True
    V.outline(tmp)
    ring = (tmp >= 0) & ~coil & (a < 0)
    for dx, dy in ((1, 1), (2, 1), (1, 0)):                                 # the contact shade, east
        sh = np.zeros_like(coil)
        sh[max(0, dy):, max(0, dx):] = (coil | ring)[:H - dy, :W - dx]
        sh &= ~coil & ~ring & (a < 0)
        a[sh] = C('soot', 2)
    a[coil] = tmp[coil]
    a[ring] = tmp[ring]


def _laid_rope(a, pts, w=2.0, seed=0):
    """A laid rope along a polyline: lit along its top edge, darker underneath, the lay as a short
    darker tick every four texels along it (not stripes)."""
    m = np.zeros(a.shape, bool)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        m |= _line(a.shape, x0, y0, x1, y1, w)
    Yg, Xg = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    up = np.zeros_like(m)
    up[1:] = m[:-1]
    dn = np.zeros_like(m)
    dn[:-1] = m[1:]
    t = np.where(~up, 3.8, np.where(~dn, 2.2, 3.0))
    tick = m & ((Xg % 4) == 0) & up
    t = np.where(tick, t - 1.0, t)
    rpaint(a, m, ROPE, t, 0.3)
    return m


def _float_ball(a, cx, cy, r, seed=0):
    """A glass float: a sphere of sea-green glass, lit upper left with a 2-texel glint, dark lower
    right, held in a bag of netting (two dark cords across it)."""
    Yg, Xg = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    d = _disc(a.shape, cx, cy, r)
    u, v = (Xg + 0.5 - cx) / r, (Yg + 0.5 - cy) / r
    t = 3.0 + 1.0 * ((u + v) < -0.5) - 1.2 * ((u + v) > 0.6)
    rpaint(a, d, [('water_cool', 'water', 'water_warm')], t, 0.0)
    a[d & (np.abs(u - v * 0.3) < 0.18)] = C('soot', 2)
    a[d & (np.abs(v + 0.1) < 0.16)] = C('soot', 2)
    gx_, gy_ = int(cx - r * 0.45), int(cy - r * 0.5)
    a[gy_, gx_:gx_ + 2] = C('snow', 5)


def net_rack(seed=101):
    """A fisherman's net rack on the quay: three oak posts and a top rail; a green net hung over the
    rail to dry, sagging between the posts in folds (lit vertical crests, dark troughs, the diamond
    mesh closing up in the troughs), cork floats along its head rope; two glass floats caught in it,
    each a sphere in its bag; the net's tail coiled at the end post as rope rings."""
    sc = K.Scene(-48, 48, -16, 16, 70)
    for x in (-34, 0, 34):
        sc.box(x - 2, -2, 0, x + 2, 2, 48, OAK, base=2.6, k=1.4, tag='post', mix=hsh(seed, x))
    sc.box(-38, -1.6, 46, 38, 1.6, 49.5, OAK, base=2.8, k=1.4, tag='rail', mix=0.4)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox
    side = sc.n[..., 2] < 0.5
    posts = _tagm(sc, 'post')
    for x in (-34, 0, 34):
        m = posts & side & (np.abs(gx - x) <= 2)
        rpaint(a, m, OAK, np.where(gx < x, 3.4, 2.4), 0.3)               # lit west half, shaded east half
    rail = _tagm(sc, 'rail')
    rys = np.nonzero(rail & side)[0]
    rys_t = np.nonzero(rail & ~side)[0]
    rpaint(a, rail, OAK, np.where(~side & (Yg == rys_t.min()), 4.0, np.where(Yg == rys.max(), 2.2, 3.0)), np.where(~side, 0.8, 0.3))
    B._lichen(sc, a, tags=('post',), rate=0.5, seed=seed)
    # the hung net, draped over the rail and sagging between the posts (round 3 of the detail audit,
    # R3-6): mostly air, twine in diamonds 9 texels across whose strokes are 2 texels wide on the
    # diagonal (so no twine texel stands alone), the strokes facing the upper left lit and the others
    # in shade; folds as bands
    # where the diamonds close up, denser and darker, at uneven spacing; gathered solid over the rail;
    # the foot hanging in an uneven sag on its weights, the posts and the quay showing through
    top = oy - 46 + 1
    net = np.zeros((H, W), bool)
    hemrow = {}
    for (xa, xb) in ((-34, 0), (0, 34)):
        for x in range(xa + 3, xb - 2):
            u = (x - xa) / float(xb - xa)
            sag = 9.0 * math.sin(math.pi * u) + 2.2 * math.sin(2.3 * math.pi * u + xa * 0.13) + 1.2 * (hsh(seed, x // 4) - 0.5)
            hem = oy - 14 + sag
            hemrow[ox + x] = int(hem)
            net[top:int(hem), ox + x] = True
    gx_ = (Xg - ox).astype(float)
    dy = (Yg - top).astype(float)
    # the folds: vertical bands 2 to 4 wide at uneven spacing, bending a little with the depth
    fold = np.zeros((H, W), bool)
    nfold = np.zeros((H, W), int)
    fx = -32.0
    k = 0
    while fx < 34:
        fx += 8 + 5 * hsh(seed, k, 11)
        wdt = 3 + int(3 * hsh(seed, k, 12))
        bend = 0.08 * dy * math.sin(k * 1.3)
        fold |= (gx_ - bend >= fx) & (gx_ - bend < fx + wdt)
        nfold += (gx_ - bend >= fx).astype(int)
        k += 1
    # (R4-10) the diamonds stretch tall and narrow in the folds (5 x 9) and open out between them
    # (9 x 7); each stroke steps a texel where it crosses a fold, so the net hangs, not a trellis
    Px = np.where(fold, 5.0, 9.0)
    Py = np.where(fold, 9.0, 7.0)
    Xb = Xg + nfold
    sa = np.mod(Xb / Px - Yg / Py, 1.0) < 2.0 / Px                       # the strokes falling to the east: in shade
    sb = np.mod(Xb / Px + Yg / Py, 1.0) < 2.0 / Px                       # the strokes rising to the east: lit
    gathered = Yg < top + 6
    twine = net & (sa | sb | gathered)
    tw = np.where(sb, 4.0, 2.0)
    tw = np.where(fold, np.where(sb, 2.0, 1.0), tw)
    tw = np.where(gathered, np.where(sb, 3.4, 2.6), tw)
    tw = np.where(dy > 24, tw - 0.6, tw)
    rpaint(a, twine, [('leaf_cool', 'grass_cool', 'grass'), ('leaf_cool', 'leaf', 'grass_cool')], tw, np.where(sb, 0.2, 0.7))
    holes = net & ~twine
    # the head rope along the rail, its corks
    hr = top + 3
    a[net & (Yg >= hr - 1) & (Yg <= hr)] = C('sand_cool', 3)              # the head rope, two texels thick
    for x in range(-30, 32, 7):
        if abs(x) < 3 or abs(abs(x) - 34) < 3:
            continue
        a[hr - 1:hr + 1, ox + x:ox + x + 3] = C('fox', 3)                  # a cork on it
        a[hr - 1, ox + x] = C('fox', 4)
    hem_ = net & ~np.roll(net, -1, 0)
    a[hem_] = C('leaf_cool', 1)
    holes &= ~hem_
    xs_h = sorted(hemrow)
    xw = xs_h[0] + 3
    while xw < xs_h[-1] - 1:                                             # lead sinkers on the foot rope, uneven
        y = hemrow.get(xw)
        if y is not None and 0 <= y < H:
            a[y - 1:y + 1, xw:xw + 2] = C('slate', 2)
            a[y - 1, xw] = C('slate', 4)
            holes[y - 1:y + 1, xw:xw + 2] = False
        xw += 5 + int(5 * hsh(seed, xw, 13))
    _finish(a, keep=np.isin(a, [C('fox', 3), C('fox', 4)]) | holes)
    a[holes] = -1
    _float_ball(a, ox - 20, oy - 26, 3.6, seed)
    _float_ball(a, ox + 15, oy - 21, 3.2, seed + 1)
    _rope_coil(a, ox + 40, oy - 2, rings=3, rx=7.5, ry=3.6, seed=seed)
    B._ground_tufts(a, ox, oy, [-38, -31, 30], seed)
    return K.crop(a, ox, oy)


def _creel(sc, cx, cy, z0, L=22.0, ry=6.5, rz=10.0, yaw=0.32):
    """A creel's body as a half-cylinder lying along its length, turned `yaw` in plan so its east end
    turns towards the viewer (a three-quarter view): rasterised against the scene's depth. Returns
    (mask, part, s, phi, z): part 1 the arched back (the top plane), 2 the south face, 3 the D-shaped
    east end, 4 the west end; s the place along the length (-1 west .. 1 east), phi round the arch
    (0 the south foot .. pi the north foot)."""
    H, W = sc.depth.shape
    ca, sa = math.cos(yaw), math.sin(yaw)
    zb = np.full((H, W), -1e9)
    part = np.zeros((H, W), int)
    S = np.zeros((H, W))
    PH = np.zeros((H, W))
    ZZ = np.zeros((H, W))

    def put(x, y, z, pt, s_, ph):
        X = np.floor(x + sc.ox).astype(int)
        Y = np.floor(y - z + sc.oy).astype(int)
        ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
        for xx, yy, zz, ss, pp, tt in zip(X[ok], Y[ok], z[ok], s_[ok], ph[ok], np.broadcast_to(pt, X.shape)[ok]):
            if zz >= zb[yy, xx] and zz >= sc.depth[yy, xx] - 0.5:
                zb[yy, xx], part[yy, xx], S[yy, xx], PH[yy, xx], ZZ[yy, xx] = zz, tt, ss, pp, zz
    ss_, pp_ = np.meshgrid(np.linspace(-1, 1, 90), np.linspace(0, math.pi, 60))
    ss_, pp_ = ss_.ravel(), pp_.ravel()
    u = ss_ * L / 2.0
    v = ry * np.cos(pp_)
    zz = z0 + rz * np.sin(pp_)
    x = cx + u * ca - v * sa
    y = cy + u * sa + v * ca
    nz = np.sin(pp_) / rz
    nv = np.cos(pp_) / ry
    pt = np.where(nz / np.hypot(nz, nv) > 0.72, 1, 2)
    put(x, y, zz, pt, ss_, pp_)
    for end, ptn in ((1.0, 3), (-1.0, 4)):
        rr_, pp2 = np.meshgrid(np.linspace(0, 1, 18), np.linspace(0, math.pi, 50))
        rr_, pp2 = rr_.ravel(), pp2.ravel()
        u = np.full(rr_.shape, end * L / 2.0)
        v = ry * rr_ * np.cos(pp2)
        z2 = z0 + rz * rr_ * np.sin(pp2)
        put(cx + u * ca - v * sa, cy + u * sa + v * ca, z2, ptn, np.full(rr_.shape, end), pp2 + 10 * rr_)
    return part > 0, part, S, PH, ZZ


def lobster_pots(variant='a', seed=103):
    """Withy creels on timber bases, 0.5 m long (round 3 of the detail audit, R3-5): each a
    half-cylinder seen in three-quarter view: the arched back a lit top plane (willow 4), the south
    face with its hoops (willow 3), the D-shaped east end in shade (willow 2) with the funnel's mouth
    in it, a willow ring round a dark eye; the lower third of the body at least a tone darker than the
    top, a dark base band and a contact shade; stacked three high, the top one set back (a), or one
    with a coil of rope and its float at its side (b)."""
    sc = K.Scene(-36, 36, -22, 8, 48)
    pots = [(-11, -4, 0), (11, -4, 0), (0, -9, 13.5)] if variant == 'a' else [(-4, -4, 0)]
    for k, (x, y, z) in enumerate(pots):
        sc.box(x - 11, y - 6.5, z, x + 11, y + 6.5, z + 2.5, OAK, base=2.6, k=1.4, tag='pbase%d' % k, mix=0.3)
    if variant == 'b':
        sc.ellipsoid(17, 2, 5, 4.6, 4.0, 4.6, RED, base=2.6, k=1.6, tag='float', mix=0.2)
        sc.cylinder(17, 2, 0.8, 9, 13, IRON, base=2.4, k=1.4, tag='flag')
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    L = sc.light()
    # a browner, quieter willow than v6's brass (R5-8): the most saturated thing on the quay no more
    WEAVE = [('earth_cool', 'earth_warm', 'timber_warm'), ('earth_cool', 'timber_warm', 'earth_warm'), ('timber_cool', 'earth_warm', 'earth_warm')]
    for k, (x, y, z) in enumerate(pots):
        pb = _tagm(sc, 'pbase%d' % k)
        rpaint(a, pb, OAK, np.where(sc.n[..., 2] > 0.5, 3.6, 2.4), 0.3)
    for k, (x, y, z) in enumerate(sorted(pots, key=lambda p: p[2])):
        d, part, S, PH, ZZ = _creel(sc, x, y, z + 2.5, yaw=0.0)
        # its silhouette (round 4 of the detail audit, R4-4): the east end's top corner a quarter
        # circle of half the creel's height, so the end reads as a D from the side; the west end's top
        # corner rounded 3 texels, a cylinder seen in three-quarter view
        ys_, xs_ = np.nonzero(d)
        ytop_, ybot_, x0_, x1_ = ys_.min(), ys_.max(), xs_.min(), xs_.max()
        rd = max(5.0, (ybot_ - ytop_ + 1) / 2.0)
        for (cxr, rr_, sgn) in ((x0_ + 3.0, 3.0, -1), (x1_ + 1 - rd, rd, 1)):
            cyr = ytop_ + rr_
            corner = d & ((Xg + 0.5 - cxr) * sgn > 0) & (Yg + 0.5 < cyr) & \
                (((Xg + 0.5 - cxr) / rr_) ** 2 + ((Yg + 0.5 - cyr) / rr_) ** 2 > 1.0)
            d &= ~corner
        # the D end: the part of the body under the quarter circle, in shade, its rim lit
        dc_x = x1_ + 1 - rd
        endf = d & (Xg + 0.5 > dc_x + 1)
        hgt = np.clip((ybot_ - Yg) / max(1.0, ybot_ - ytop_), 0, 1)       # 0 at the foot .. 1 at the crown
        # the arch shaded as one curve: willow 4 on top, 3 on the south shoulder, 2 just above the base
        t = np.where(part == 1, 4.0, 2.2 + 1.6 * hgt)
        t = np.where(endf, 2.0 + 0.4 * hgt, t)
        # the weave between the hoops: willow courses as 2 x 1 lit and dark pairs, alternating course
        # by course (a basket's weave, not a checker of single texels)
        crs = (Yg // 2)
        pair = ((Xg // 2) + crs) % 2 == 0
        t = np.where(d & ~endf & pair, t + 0.5, np.where(d & ~endf, t - 0.5, t))      # a full tone apart (R5-8)
        rpaint(a, d, WEAVE, t, np.clip(((crs % 3) + 0.5) / 3.0, 0, 0.999))
        arc = d & endf & ~ndi.binary_erosion(d | ~endf, iterations=1)
        rim_d = endf & (np.hypot(Xg + 0.5 - dc_x, Yg + 0.5 - (ytop_ + rd)) > rd - 1.5) & (Yg + 0.5 < ytop_ + rd)
        a[rim_d] = C('sand_cool', 3)                                      # the D's lit willow rim
        a[d & endf & (Xg + 0.5 > dc_x) & (Xg + 0.5 <= dc_x + 1.5)] = C('timber', 2)   # where the end meets the face
        del arc
        # the hoops: bent rods round the arch, 2 texels, lit on the top
        for hs in (-0.62, 0.0, 0.5):
            hoop = d & ~endf & (np.abs(S - hs) < 0.05)
            ht = np.where(part == 1, 4.6, 3.6 + 0.8 * hgt)                 # a tone over the weave
            rpaint(a, hoop, [('timber_cool', 'timber_warm', 'earth_warm')], ht, 0.0)
            htop = hoop & ~np.roll(hoop, 1, 0)
            a[htop & (part == 1)] = C('sand_cool', 4)                          # its top caught by the light
        # the funnel inside the D, its mouth on the axis: a willow ring round the dark eye
        my = ytop_ + rd + 0.5
        mx = dc_x + rd * 0.45
        rr = np.hypot((Xg + 0.5 - mx) / max(1.8, rd * 0.42), (Yg + 0.5 - my) / max(2.2, rd * 0.55))
        e = d & endf
        a[e & (rr <= 1.0) & (rr > 0.62)] = C('earth_warm', 3)              # the funnel's willow ring, 1 texel,
        a[e & (rr <= 1.0) & (rr > 0.62) & (Yg + 0.5 < my + 0.5)] = C('sand_cool', 4)   # lit on its upper half
        a[e & (rr <= 0.62)] = C('earth_cool', 0)
        if z > 0:                                                          # the contact shade under the top pot
            shm = np.zeros_like(d)
            shm[1:] = d[:-1]
            shm2 = np.zeros_like(d)
            shm2[2:] = d[:-2]
            V._step(a, (shm | shm2) & ~d & (a >= 0) & (Yg > np.nonzero(d)[0].max() - 3), -1)
    if variant == 'b':
        fl = _tagm(sc, 'float')
        rpaint(a, fl, RED, np.where(L > 0.3, 4.0, np.where(L > -0.1, 3.0, 1.8)), 0.3)
        a[fl & (np.abs(Yg - (oy + 2 - 6)) < 1)] = C('snow', 4)                # its white band
    _finish(a)
    if variant == 'b':
        _rope_coil(a, ox - 23, oy - 1, seed=seed)                          # the coil on the west, the float east
        K.despeckle(a, size=1)
    B._ground_tufts(a, ox, oy, [-24, -20, 22], seed)
    return K.crop(a, ox, oy)


def mooring_bitt(seed=105):
    """A cast-iron mooring bitt on the quay's edge, 0.5 m: a squat post with a waist on a bolted plate,
    a domed cap with its rim lit, rust running in streaks under the cap and in the waist; a hawser made
    fast with turns round its waist, the strands of its lay showing, and the rest of the line flaked
    in a coil on the quay beside it: tied off, not trailing."""
    W, H = 52, 40
    a = np.full((H, W), -1, np.int32)
    ox, oy = 34, 34
    Yg, Xg = np.mgrid[0:H, 0:W]
    plate = (np.abs(Xg + 0.5 - ox) <= 8) & (Yg >= oy - 3) & (Yg < oy + 1)
    rpaint(a, plate, IRON, np.where(Yg == oy - 3, 3.4, 2.2), 0.3)
    for bx in (-6, 6):
        a[oy - 2, ox + bx] = C('slate', 4)
        a[oy - 1, ox + bx] = C('void', 1)
    prof = [5.8, 5.8, 4.8, 4.6, 4.2, 4.0, 4.0, 4.0, 4.2, 4.6, 5.0, 6.4, 6.4, 5.4, 4.4, 2.8]
    m, hh, u, top = _turned(a, ox, oy - 2, prof, IRON, lit=3.6, body=2.4, shade=1.2, top_t=3.4)
    a[m & ~top & (hh >= 11) & (hh < 12)] = C('slate', 4)                      # the cap's lit rim
    for (x0, y0, n) in ((1, oy - 2 - 11, 4),):                              # rust weeping from under the cap
        a[y0:y0 + n, ox + x0:ox + x0 + 2] = C('crag', 2)
        a[y0, ox + x0:ox + x0 + 2] = C('fox', 2)
    _finish(a)
    # the silhouette closed in the iron's own darkest edge (the outline round dark iron)
    body_m = (a >= 0)
    edge = body_m & ~ndi.binary_erosion(body_m)
    a[edge] = C('void', 0)
    # the hawser: three turns round the waist, each a 2-texel band rising a little to the east, lit
    # on its upper west and in shade where it turns behind the post (a dark end each side), the
    # standing part leaving from under the last turn and led off east to its coil on the quay
    # (R5-11) two turns, each 2 rows deep (a lit top row over a body row), a seam two tones down
    # between them, as on the coil
    for k in range(2):
        y0 = oy - 6 - 3 * k
        for x in range(ox - 5, ox + 6):
            yy = y0 - int(round((x - ox) * 0.18))
            behind = x in (ox - 5, ox + 5)
            a[yy, x] = C('sand_cool', 1) if behind else (C('sand', 4) if x < ox - 1 else (C('sand', 3) if x < ox + 2 else C('sand_cool', 3)))
            a[yy + 1, x] = C('timber_cool', 1) if behind else (C('sand_cool', 3) if x < ox + 2 else C('sand_cool', 2))
            if k == 0:
                a[yy - 1, x] = C('sand_cool', 1)                          # the seam to the turn above
    _laid_rope(a, [(ox - 4.5, oy - 4), (ox - 12, oy - 1.5), (ox - 20, oy - 1)], 2.0, seed + 3)
    _rope_coil(a, ox - 26, oy - 1, rings=3, rx=7.5, ry=3.6, seed=seed)
    K.despeckle(a, size=1)
    return K.crop(a, ox, oy)


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
    ring_ = ndi.binary_dilation(inside, structure=np.ones((5, 3), bool)) & hull & ~inside
    rail = ring_ & ~ndi.binary_dilation(~hull, iterations=1)             # the gunwale: a 2-texel rail round the inside
    out = hull & ~inside & ~rail
    # outside: the strakes lapped down from the gunwale, 3 texels each (counted from the rail), each
    # lit along its lower edge over the shade of the next; the sheer strake white, then blue, red
    # below the waterline; the hull lit at its west and shaded east
    dist = ndi.distance_transform_cdt(~(inside | rail), metric='taxicab')
    # strakes of their own widths (R3-13), the sheer strake tapering towards the bow
    w0 = 3 - (gx > 18).astype(int) - (gx > 32).astype(int)
    widths = [4, 3, 4, 2, 3, 4, 3, 3, 4, 3]
    d1 = dist - 1
    stk = np.where(d1 < w0, 0, 1)
    start = w0.copy()
    wid = w0.copy()
    for k, wk in enumerate(widths, start=1):
        here = (stk == k) & (d1 >= start + wk)
        stk = np.where(here, k + 1, stk)
        start = np.where(here, start + wk, start)
        wid = np.where(stk == k, wk, wid)
    wid = np.where(stk == 0, w0, np.where(stk <= len(widths), np.array([0] + widths + [3])[np.clip(stk, 0, len(widths) + 1)], 3))
    inn = np.where(stk == 0, d1, d1 - start)
    t = 2.6 + 1.0 * (gx < -20) - 0.9 * (gx > 26) + np.where(inn == wid - 1, 1.0, 0.0) - np.where(inn == 0, 0.7, 0.0)
    t = t - 0.5 * (gy > 6)
    rpaint(a, out & (stk == 0), WHITE[:2], t + 0.6, 0.3)
    rpaint(a, out & (stk >= 1) & (z >= 3.5), [('water_cool', 'water_cool', 'water'), ('water_cool', 'water', 'water')], t,
           np.clip(K.vhash(stk, 0, seed) * 0.999, 0, 0.999))
    rpaint(a, out & (stk >= 1) & (z < 3.5), RED, t - 0.3, 0.3)
    flake = out & (z < 8) & (z >= 3.5) & (K.vhash(Xg // 3, Yg // 2, seed) > 0.96)
    a[flake] = C('timber', 3)
    # the gunwale's oak rail, lit
    rpaint(a, rail, OAK, 3.2 + 0.8 * L_, 0.3)
    # inside: the far inner planking lit, the near inner wall under the gunwale in shade, the floor
    # boards between with frames across them every 7 texels (2 wide, darker in the bilge), the
    # thwarts with a lit top edge, the oar laid across with its shadow on the floor
    rel = gy / np.maximum(half, 1.0)                                    # -1 at the far gunwale, 1 at the near
    it = np.where(rel < -0.55, 4.0, np.where(rel < -0.25, 3.4, np.where(rel > 0.62, 1.0, np.where(rel > 0.3, 1.8, 2.6))))
    it = it - 0.6 * ((gy.astype(int) % 4) == 0) * (rel >= -0.25) * (rel <= 0.3)   # the floor boards' seams
    it = it + 0.4 * ((gy.astype(int) % 3) == 0) * (rel < -0.25)            # the far strakes' lands
    rib = (((gx.astype(int) + 60) % 7) < 2) & (rel > -0.45) & (rel < 0.62)
    it = np.where(rib, it - 1.0 - 0.4 * (np.abs(rel) < 0.2), it)
    rpaint(a, inside, OAK + [('earth_cool', 'timber_cool', 'timber')], it, K.vhash(gy.astype(int) // 3, 0, seed + 6))
    for tx in (-16, 9):                                               # the two thwarts
        th = inside & (gx >= tx) & (gx < tx + 5)
        tys = np.nonzero(th)[0]
        rpaint(a, th, OAK, np.where(gx < tx + 1, 4.4, np.where(gx >= tx + 4, 1.8, 3.2)), 0.4)
    oar = _line(a.shape, sc.ox - 30, sc.oy - 16, sc.ox + 24, sc.oy - 13, 2.2) & (inside | rail)
    oar_sh = _line(a.shape, sc.ox - 29, sc.oy - 13.5, sc.ox + 25, sc.oy - 10.5, 1.6) & inside & ~oar
    V._step(a, oar_sh, -1)
    rpaint(a, oar, [('timber_cool', 'timber_warm', 'sand')], np.where(np.roll(oar, 1, 0), 3.2, 4.2), 0.0)
    weed = out & (z < 2.0) & (K.vhash(Xg // 3, 0, seed + 4) > 0.7)
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
    """The harbour light at the jetty's head, a cast-iron lamp column as the Crossroads lantern is
    drawn (the anchor kit/lantern), in the lamp class: a coursed granite plinth with a lit coping,
    an iron mooring ring on its face; the column turned and banded, lit as a
    cylinder (a highlight band left of centre, a core shadow on its right third), fluted between a
    bell foot and a capital, each collar's top lit as a ledge; a ladder bar with ball ends on scroll
    brackets; the lantern a glazed box in an iron frame, its corner posts lit west and dark east,
    glazing bars across the red glass lit from inside (brighter low in the middle, a stepped glint
    in the upper west pane); a conical cap with a lit eave rim, a vent ball and a finial. The lamp's
    glow swells and eases over the cycle."""
    sc = K.Scene(-17, 17, -9, 9, 150)
    sc.box(-12, -7, 0, 12, 7, 17, GRANITE, base=2.6, k=1.4, tag='plinth', round_=1.0, mix=0.4)
    sc.box(-13.5, -8, 17, 13.5, 8, 20, GRANITE, base=3.0, k=1.4, tag='cope', round_=1.2, mix=0.5)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox + 0.5
    z = sc.depth
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    # the plinth: dressed granite in two courses, the coping's top lit and its front lip catching it
    pl = _tagm(sc, 'plinth')
    _stone_parts(a, pl & side, gx + 100, z, seed, GRANITE, 2.8, lo=10, hi=15, course=8, moss=3.0)
    cope = _tagm(sc, 'cope')
    rpaint(a, cope & ~side, GRANITE, 3.7 + 0.4 * (gx < -6), 0.4)
    rpaint(a, cope & side, GRANITE, np.where(z > 18.8, 4.0, 2.6), 0.4)
    a[cope & side & (gx > 10)] = C('stone_cool', 2)
    a[cope & ~side & (gx > 11)] = C('stone', 3)
    rpaint(a, cope & ~side & (gx > 3.5), [GRANITE[1]], 3.7 + 0.4 * (gx < -6) - 0.6 * (gx > 11), 0.0)   # the second slab, a sibling
    a[cope & ~side & (np.abs(gx - 3.5) < 0.5)] = C('stone_cool', 1)          # the slab joint
    a[cope & ~side & (np.abs(gx - 4.5) < 0.5)] = C('stone_warm', 4)
    cys_ = np.nonzero(cope & side)[0]
    chip = cope & (gx < -9) & (gx > -13) & (Yg <= cys_.min() + 1) & (Yg >= cys_.min() - 1)
    a[chip] = C('stone_cool', 2)                                          # a chip off the front-west arris
    a[chip & (gx < -12)] = C('stone_warm', 4)
    B._lichen(sc, a, tags=('plinth',), rate=0.6, seed=seed)
    # the column, turned: a bell foot with two rings, the fluted shaft with two bands, the capital
    prof = ([7.6, 7.6, 7.0, 6.2, 6.2, 5.6, 5.2, 4.9, 4.7, 5.8, 5.8, 4.6] + [4.2] * 30 + [5.0, 5.0] + [4.2] * 28
            + [5.0, 5.0] + [4.2] * 18 + [4.5, 4.9, 5.4, 6.2, 6.2])
    fy = oy - 20
    col, hh, u, top = _turned(a, ox, fy, prof, IRON, mix=0.3, lit=4.5, body=2.9, shade=1.4, top_t=4.3)
    shaft = col & ~top & (hh >= 12) & (np.isin(np.clip(hh.astype(int), 0, len(prof) - 1),
                                               [k for k, r in enumerate(prof) if abs(r - 4.2) < 0.01]))
    for g in (-0.5, -0.05, 0.42):                                       # the flutes: a groove a tone down
        V._step(a, shaft & (np.abs(u - g) < 0.13), -1)
    a[col & ~top & (np.abs(u + 0.95) < 0.12) & (hh > 12)] = C('iron', 3)  # reflected light on the far west edge
    # the column's shadow thrown down and to the east across the coping, two tones down
    csh = cope & ~side & ~col & (gx > 2) & (Yg >= fy - 3) & (Yg <= fy + 6) & ((gx - 2) < (Yg - (fy - 3)) * 0.9 + 6)
    V._step(a, csh, -2)
    ztop = len(prof)
    # the ladder bar on scroll brackets, ball ends
    yb = fy - ztop - 2
    bar = (np.abs(gx) <= 11) & (Yg >= yb) & (Yg < yb + 2)
    a[bar] = np.where(Yg[bar] == yb, C('iron', 4), C('iron', 1))
    for sx in (-1, 1):
        a[yb - 1:yb + 2, ox + sx * 12 - (1 if sx < 0 else 0):ox + sx * 12 + (1 if sx > 0 else 0) + 1] = C('iron', 2)
        a[yb - 1, ox + sx * 12 - (1 if sx < 0 else 0)] = C('iron', 4)
        br = _line(a.shape, ox + sx * 2.5, yb + 7, ox + sx * 8.5, yb + 2, 1.2)
        a[br & (a < 0)] = C('iron', 2 if sx > 0 else 3)
    # the lantern: a base plate, the glazed box, the cap
    yl1 = yb - 1                                                       # the lantern's foot row
    plate = _disc(a.shape, ox, yl1 - 1, 8.5, 3.0)
    rpaint(a, plate, IRON, np.where(Yg < yl1 - 1, 3.8, 1.8) + 0.5 * (gx < -3), 0.3)
    gh = 17
    y0g, y1g = yl1 - 3 - gh, yl1 - 3
    box = (np.abs(gx) < 7.5) & (Yg >= y0g) & (Yg < y1g)
    glow = 0.5 + 0.5 * math.sin(2 * math.pi * i / LOOP)
    zt = (Yg - y0g) / float(gh)
    gt = 2.2 + 1.0 * glow + 1.2 * (1 - np.abs(gx) / 7.5) * (zt > 0.35) + 0.6 * (zt > 0.6)
    gt = np.where((zt < 0.18) | (gx < -5), gt - 0.8, gt)                # in the frame's shadow at top and west
    rpaint(a, box, [('clay_cool', 'clay', 'fox')], gt, 0.0)
    flame = box & (np.abs(gx) < 1.6) & (zt > 0.45) & (zt < 0.8)
    rpaint(a, flame, [('fox', 'lamp', 'lamp')], 3.6 + 1.4 * glow, 0.0)
    gl = box & (np.abs((gx + 6) - (Yg - y0g - 3) * 0.6 - 1.0) < 0.7) & (zt > 0.2) & (zt < 0.55) & (gx < -1)
    a[gl] = C('fox', 5)
    posts = box & (np.abs(gx) >= 6.0)
    a[posts & (gx < 0)] = np.where(gx[posts & (gx < 0)] < -6.8, C('iron', 4), C('iron', 3))
    a[posts & (gx > 0)] = np.where(gx[posts & (gx > 0)] > 6.8, C('iron', 1), C('iron', 2))
    a[box & (np.abs(gx - 0.5) < 0.5) & ~flame] = C('iron', 2)              # the glazing bars
    a[box & (Yg == y0g + gh // 2) & ~posts] = C('iron', 2)
    a[box & (Yg == y0g + gh // 2 - 1) & ~posts & (gx < 0)] = C('iron', 3)
    a[box & (Yg == y1g - 1)] = C('iron', 1)
    # the cap: an eave rim lit along its top, a cone lit west, the vent ball and the finial
    yc = y0g
    rim = _disc(a.shape, ox, yc, 9.5, 3.2)
    rpaint(a, rim, IRON, np.where(Yg < yc, 4.4, np.where(Yg > yc + 1, 1.2, 2.6)) + 0.6 * (gx < -4) - 0.6 * (gx > 5), 0.3)
    cone = np.zeros_like(rim)
    for k in range(11):
        r = 8.5 - 0.7 * k
        cone |= _disc(a.shape, ox, yc - 2 - k, r, max(1.0, r * 0.32))
    cone &= Yg < yc - 1
    rpaint(a, cone, IRON, _cyl_tone(gx, 8.5, lit=4.2, body=2.8, shade=1.4), 0.3)
    a[cone & (np.abs(gx + 3.5) < 0.9) & (Yg > yc - 9)] = C('iron', 5)                # the cone's sheen, a rib lit
    ball = _disc(a.shape, ox, yc - 15, 2.6, 2.4)
    rpaint(a, ball, IRON, np.where((gx < 0) & (Yg < yc - 15), 4.2, np.where(gx > 1, 1.6, 2.8)), 0.3)
    fin = (np.abs(gx) < 1.0) & (Yg >= yc - 22) & (Yg < yc - 17)
    a[fin] = np.where(gx[fin] < 0, C('iron', 3), C('iron', 1))
    a[(np.abs(gx) < 1.0) & (Yg == yc - 22)] = C('iron', 4)
    # the mooring ring on the plinth's face, a rope rove through it and hanging in a bight
    ry = oy - 9
    ring = _disc(a.shape, ox + 0.5, ry, 4.0, 3.8) & ~_disc(a.shape, ox + 0.5, ry, 2.0, 1.8)
    rsh = np.roll(np.roll(ring, 1, 0), 1, 1) & ~ring & pl
    V._step(a, rsh, -2)                                                  # its shadow on the stone
    ra = np.arctan2(Yg + 0.5 - ry, Xg + 0.5 - (ox + 0.5))
    upw = np.cos(ra + 2.36)
    a[ring] = np.where(upw[ring] > 0.4, C('slate', 4), np.where(upw[ring] < -0.3, C('iron', 1), C('iron', 2)))
    a[ry - 4:ry - 3, ox - 1:ox + 2] = C('iron', 1)                      # its staple
    # the column stands clear of the coping: its edge where it meets the stone, a contact line at its foot
    nb = ndi.binary_dilation(col, structure=np.ones((3, 3), bool)) & ~col & cope
    a[nb & (gx < 0)] = C('stone_cool', 1)
    a[nb & (gx >= 0)] = C('stone_cool', 0)
    edge_c = col & ndi.binary_dilation(cope & ~col, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)) & (hh < 4)
    a[edge_c] = C('iron', 1)
    keep = box
    _finish(a, keep=keep)
    if glow > 0.6:                                                     # a soft halo at the peak, no outline
        halo = ndi.binary_dilation(box, iterations=2) & (a < 0) & (Yg < y1g) & (Yg > y0g)
        a[halo & (((Xg + Yg) % 2) == 0)] = C('lamp', 4)
    return a, ox, oy


def harbour_light(seed=111):
    pics = _strip_frames(_light_frame)
    return pics[0], {'frames': pics, 'fps': 4.0, 'clip': 'glow'}


# ================================================================================================
# the Halt
# ================================================================================================
def platform_edge(variant='a', seed=121):
    """One cell of the halt's platform edge, along x: a front of dressed stone blocks, two a cell,
    each a pillow (its top arris lit, its west end lit, its east end and foot turning away), the
    joints recessed and dark, a damp foot with weeds; a coping of one long slab a cell standing proud of the front
    (its top calm and lit, the white lip painted along its front edge and worn where feet go, its
    nosing lit along the arris, its shadow on the front under it, a dark joint at the cell line with
    a lit lip after it); the platform's gravel behind as sparse clumped pebbles on a calm base; drawn
    from a run of five cells so neighbours meet, cropped to its own cell. Variant b has a chipped
    corner and a longer worn patch on its lip."""
    sc = K.Scene(-60, 60, -26, 4, 20)
    sc.box(-60, -24, 0, 60, 0, 12, GRANITE, base=2.6, k=1.4, tag='body', mix=0.3)
    sc.box(-60, -7, 12, 60, 1.5, 15, GRANITE, base=3.0, k=1.4, tag='coping', mix=0.5, round_=1.0)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    gx = Xg - sc.ox
    lx = ((gx + 12) % 24) - 12                                      # x within the cell, -12 .. 11
    body = _tagm(sc, 'body')
    cop = _tagm(sc, 'coping')
    z = sc.depth
    top = sc.n[..., 2] > 0.5
    front = body & ~top
    rng = np.random.default_rng(seed)
    # the front: one block a cell in each course, staggered, each a pillow; the joints recessed
    fys = np.nonzero(front)[0]
    fy0, fy1 = fys.min(), fys.max() + 1
    a[front] = C('stone_cool', 1)
    yb = fy1 - 2
    for k in range(-10, 11):                                        # one course of blocks, two a cell
        xa = sc.ox + k * 12 - 12
        hh, ww = yb - fy0 - 1, 11
        m = V.chamfer(hh, ww, 1)
        hk = hsh(seed, k, 'abcd'.index(variant), 5)                     # each variant its own blocks
        t = 3 if hk < 0.55 else 2
        tt = Hs.pillow(m, t, np.random.default_rng(seed + int(hk * 97)), flecks=0, lit_top=1, under=1)
        fam = ('stone_warm', 'stone', 'stone_cool')[int(hk * 2.99)]
        V.put(a, xa, fy0 + 1, m, fam, tt, front)
    foot = front & (Yg >= yb)
    rpaint(a, foot, [('stone_cool', 'stone', 'stone'), ('earth_cool', 'stone_cool', 'stone')], np.where(Yg == yb, 2.0, 1.0),
           np.clip(K.vhash((Xg - sc.ox + 300) // 12, 0, seed + 3) * 0.999, 0, 0.999))
    # four variants, shuffled along a run, so nothing repeats under about 100 texels (round 3 of the
    # detail audit, R3-2): each its own coping joint, worn gaps, chip and flags
    vi = 'abcd'.index(variant)
    sv = seed + 17 * vi
    # the coping: slabs 24 long whose joints fall off the cell line, each slab one calm sibling with
    # a lit nosing; the white paint on its lip worn through where feet go
    jx = (-5, -1, 4, -9)[vi]
    slab = np.floor_divide(lx - jx + 48, 24)
    ctop = cop & top
    cfr = cop & ~top
    lip = ctop & (sc.gy > -1.6)
    rpaint(a, ctop & ~lip, GRANITE, 3.6, np.clip(K.vhash(slab, 3, sv + 21) * 0.999, 0, 0.999))
    # its back arris turning away, in the slab's own sibling, broken where the flags' joints meet it
    back = ctop & ~lip & (sc.gy < -6)
    a[back] = np.where(K.vhash(slab, 5, sv)[back] > 0.5, C('stone', 3), C('stone_warm', 3))
    gaps = {0: [(-10, -7), (1, 6)], 1: [(-4, -2), (4, 7), (9, 11)], 2: [(-12, -10), (-1, 2)], 3: [(-7, -3), (6, 8)]}[vi]
    worn = np.zeros_like(lip)
    for g0, g1 in gaps:
        worn |= lip & (lx >= g0) & (lx <= g1)
    a[lip & ~worn & (sc.gy > -0.6)] = C('snow', 4)                    # the paint: its top row bright,
    a[lip & ~worn & (sc.gy <= -0.6)] = C('snow', 3)                    # the row behind a little greyer
    rpaint(a, worn, GRANITE, np.where(sc.gy > -0.6, 3.6, 3.2), 0.6)    # worn through to the stone
    cfy = np.nonzero(cfr)[0]
    rpaint(a, cfr, GRANITE, np.where(Yg == cfy.min(), 4.4, np.where(Yg == cfy.max(), 2.0, 3.0)), np.clip(K.vhash(slab, 7, sv) * 0.999, 0, 0.999))
    a[cfr & (Yg == cfy.min()) & (lx < jx + 8) & (lx > jx)] = C('stone_warm', 5)   # the nosing's lit arris
    joint = cop & (lx == jx)
    a[joint] = C('stone_cool', 1)
    a[cop & (lx == jx + 1) & top] = C('stone_warm', 4)
    # a chip: a bite out of the lip's outline, the paint broken back to the stone, the broken face
    # a tone down under a lit west edge (never a dark square inside the white)
    cx_ = (8, -9, 0, 5)[vi]
    cw = (3, 2, 4, 2)[vi]
    bite = cop & (lx >= cx_) & (lx < cx_ + cw)
    a[bite & lip] = C('stone', 4)
    a[bite & lip & (sc.gy > -0.6) & (lx > cx_) & (lx < cx_ + cw - 1)] = C('stone', 3)
    a[bite & cfr & (Yg <= cfy.min() + 1)] = C('stone_cool', 2)
    a[bite & cfr & (Yg <= cfy.min() + 1) & (lx == cx_)] = C('stone_warm', 4)
    # the coping's shadow on the front under its nosing: two rows, each slab its own sibling
    sh = front & (Yg >= fy0) & (Yg < fy0 + 2)
    V._step(a, sh, -1)
    top_line = front & (Yg == fy0)
    a[top_line & (K.vhash(slab, 9, sv) > 0.5)] = C('void', 2)                  # the darkest row, a sibling a slab
    shs = sh & (K.vhash(slab, 9, sv) > 0.5)
    a[shs & (a // 8 == FI_['stone_warm'])] = a[shs & (a // 8 == FI_['stone_warm'])] - (FI_['stone_warm'] - FI_['stone']) * 8
    # weeds by rule: only in a block joint at the foot, and only on cell b (one in four cells), a
    # tuft of blades of mixed height, dark at the root and lit at the tip
    weed_m = np.zeros((H, W), bool)
    if variant == 'b':
        for k, (dx, hgt) in enumerate(((-3, 4), (-1, 7), (1, 5), (3, 3))):
            x = sc.ox + dx
            for j in range(hgt):
                y = yb - j
                if 0 <= y < H:
                    c = C('grass', 4) if j >= hgt - 2 else (C('grass_cool', 3) if j >= hgt // 2 else C('leaf_cool', 2))
                    a[y, x:x + 2] = c
                    weed_m[y, x:x + 2] = True
    # the lane's grass grows 2 to 3 texels up over the foot here and there
    # (R4-9) in some cells only, each tuft its own kind and size: a low fringe, a spray, a single blade
    kinds = {0: [(0, 1), (1, 2), (2, 1)], 1: [], 2: [], 3: [(0, 2), (1, 3), (2, 4), (3, 2), (4, 1)]}
    for k, gx0 in enumerate({0: (-8,), 1: (), 2: (), 3: (5,)}[vi]):
        for dx, hgt in kinds[vi]:
            x = sc.ox + gx0 + dx
            for j in range(hgt):
                y = fy1 - j
                if 0 <= y < H and 0 <= x < W:
                    a[y, x] = C('grass', 3) if j == hgt - 1 else C('grass_cool', 2)
                    weed_m[y, x] = True
    # the platform's top behind: big flags in calm siblings with dark joints, worn paler where feet
    # go, lichen in clusters, the odd cracked flag
    gr = body & top & ~cop
    fv = (-sc.gy).astype(float)
    row = np.floor_divide(fv.astype(int) + 2, 8)
    fx = lx + 12 + (row % 2) * 9 + vi * 5
    flag = np.floor_divide(fx + 48, 16)
    fl_t = 3.0 + 0.6 * (K.vhash(flag, row, sv + 12) > 0.8)                   # the odd flag worn a tone paler
    rpaint(a, gr, [('stone_cool', 'stone', 'stone'), ('stone_cool', 'stone_cool', 'stone'), ('stone_cool', 'stone_warm', 'stone_warm')], fl_t,
           np.clip(K.vhash(flag, row, sv + 11) * 0.999, 0, 0.999))
    fj = gr & ((((fv.astype(int) + 2) % 8) == 0) | (((fx + 48) % 16) == 0))
    a[fj] = C('stone_cool', 2)
    # the coping's back arris stops where a flag's joint runs into it
    a[back & np.roll(fj & (((fx + 48) % 16) == 0), -1, 0)] = C('stone_cool', 2)
    for k in range(2):                                                   # lichen in clusters on the flags
        lxc = sc.ox - 9 + int(18 * hsh(sv, k, 1))
        lyc = int(np.nonzero(gr.any(1))[0].min()) + 2 + int(6 * hsh(sv, k, 2))
        if hsh(sv, k, 3) < 0.35:
            continue
        cl = gr & ~fj & (Xg >= lxc) & (Xg < lxc + 3 + (k == 0)) & (Yg >= lyc) & (Yg < lyc + 2)
        cl &= ~((Yg == lyc + 1) & (Xg == lxc + 2 + (k == 0)))
        a[cl] = C('stone_warm', 4) if k == 0 else C('grass_cool', 3)        # pale crust lichen; a green one
        a[cl & (Yg == lyc + 1) & (Xg == lxc)] = C('brass', 3) if k == 0 else C('grass_cool', 2)
    if vi in (1, 2):                                                     # a cracked flag
        y0c = int(np.nonzero(gr.any(1))[0].min()) + 3
        ck = _line(a.shape, sc.ox - 5 + 6 * vi, y0c, sc.ox - 1 + 6 * vi, y0c + 4, 1.0) & gr & ~fj
        a[ck] = C('stone_cool', 1)
        a[np.roll(ck, 1, 1) & gr & ~ck & ~fj] = C('stone', 4)
    keepw = a.copy()
    V.tidy(a)
    a[weed_m] = keepw[weed_m]
    V.outline(a)
    a[:, :sc.ox - 12] = -1
    a[:, sc.ox + 12:] = -1
    return K.crop(a, sc.ox, sc.oy)


def waiting_shelter(seed=123):
    """The halt's waiting shelter, a timber lean-to in the railway's green and cream at the size
    guide's height (eave 118 art px, 2.7 m): boarded back and sides, green below the dado rail and
    cream above; a slate roof falling to the front in staggered courses (each course's lower edge lit),
    its eave with thickness, a cream fascia with a lit lip and a half-round iron gutter; a fretted
    valance under the eave with a scalloped edge; a bench of boards along the back; a poster on the
    back wall, its corner torn; a flagged floor, in the roof's shade under it."""
    X0, X1, YB, YF = -66, 66, -38, 0                   # the walls' outer x, the back wall's y, the posts' y
    ZE, ZB = 118.0, 130.0                              # the eave's and the back's height
    sc = K.Scene(-72, 72, -46, 10, 136)
    sc.box(X0 + 4, YB + 4, 0, X1 - 4, -5, 1.5, GRANITE, base=2.7, k=1.4, tag='floor', mix=0.4)
    sc.box(X0 + 4, YB, 1.5, X1 - 4, YB + 4, ZB - 2, GREEN, base=2.5, k=1.2, tag='back', mix=0.3)
    for x0 in (X0, X1 - 4):
        sc.box(x0, YB, 1.5, x0 + 4, -14, ZE + 4, GREEN, base=2.5, k=1.6, tag='side', mix=0.3)
        sc.box(x0, -9, 1.5, x0 + 4, -5, ZE, GREEN, base=2.6, k=1.6, tag='post', mix=0.3)
    nrow = 11
    for k in range(nrow):                              # the roof's courses, back to front
        y0 = -44 + k * 4.4
        z1 = ZB + 1 - (ZB - ZE) * (k / (nrow - 1.0))
        sc.box(X0 - 3, y0, z1 - 3.0, X1 + 3, y0 + 5.0, z1, SLATE, base=2.5, k=1.2, tag='roof%d' % k, mix=0.3)
    sc.box(X0 - 3, 3.0, ZE - 6.0, X1 + 3, 4.0, ZE - 2.0, CREAM, base=3.0, k=1.2, tag='fascia', mix=0.2)
    sc.box(X0 - 4, 4.0, ZE - 7.0, X1 + 4, 6.5, ZE - 4.0, IRON, base=2.2, k=1.6, tag='gutter', round_=1.2, mix=0.3)
    sc.box(X0 + 2, 1.5, ZE - 22.0, X1 - 2, 3.0, ZE - 6.0, CREAM, base=2.9, k=1.2, tag='valance', mix=0.3)
    sc.box(-44, YB + 4, 30, 30, YB + 12, 34, OAK, base=2.8, k=1.4, tag='seat', mix=0.3)
    sc.box(-44, YB + 4, 38, 30, YB + 6, 54, OAK, base=2.6, k=1.4, tag='backrest', mix=0.3)
    for x in (-40, -7, 26):
        sc.box(x - 1.5, YB + 6, 1.5, x + 1.5, YB + 10, 30, IRON, base=2.0, k=1.4, tag='leg')
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = (Xg - ox).astype(float)
    z = sc.depth
    L = sc.light()
    # walls: vertical boards, green below the dado rail, cream above, the rail itself lit on its top
    walls = _tagm(sc, 'back', 'side')
    front = walls & (sc.n[..., 2] < 0.5)
    low = front & (z < 46)
    _planks(a, low, GREEN, 2.5 + 0.8 * L, z, gx + 200, seed, pitch=6, lit_lip=True, grain=0.0, joint=0.8)
    _planks(a, front & ~low, CREAM, 2.9 + 0.8 * L, z, gx + 200, seed + 2, pitch=6, lit_lip=True, grain=0.0, joint=0.8)
    rail = front & (np.abs(z - 46.5) < 1.6)
    rpaint(a, rail, GREEN, np.where(z > 46.5, 3.6, 1.6), 0.2)
    posts = _tagm(sc, 'post')
    pc = np.where(gx < 0, X0 + 2.0, X1 - 2.0)                             # each post's axis
    rpaint(a, posts & (sc.n[..., 2] < 0.5), GREEN, np.where(gx < pc - 1, 3.8, np.where(gx >= pc + 1, 1.8, 2.8)), 0.3)
    # the roof, as the Crossroads houses draw theirs (scripts/art/native/houses.py): slates in
    # overlapping courses, each a pillow with its butt lit and its head in the shade of the course
    # above, the plane lighter under the ridge and to the west; a capping along its top edge, barge
    # boards on both verges with the roof's thickness, the eave course seen edge on
    roof = np.zeros((H, W), bool)
    for k in range(nrow):
        roof |= _tagm(sc, 'roof%d' % k)
    rys, rxs = np.nonzero(roof)
    y_r, y_e = int(rys.min()), int(rys.max()) + 1
    rx0, rx1 = int(rxs.min()), int(rxs.max()) + 1
    rng = np.random.default_rng(seed + 40)
    a[roof] = C('slate_cool', 0)
    Hs.slate_roof(a, roof, rx0, rx1, y_r + 5, y_e - 3, rng, fams=('slate', 'slate', 'slate_cool'), moss=0.0, lichen=0.05)
    lich = roof & np.isin(a, [C('grass_cool', 2), C('grass_cool', 3)])          # the lichen a pale grey crust, not green,
    a[lich] = np.where(a[lich] == C('grass_cool', 3), C('slate_warm', 4), C('slate_warm', 3))
    # broken into 2-texel rosettes (R4-12): the crust's patches keep only every other 2 x 2 cluster
    ys_l, xs_l = np.nonzero(lich)
    for y_, x_ in zip(ys_l, xs_l):
        if ((y_ // 2) + (x_ // 2) + int(hsh(seed, x_ // 2, y_ // 2) * 2)) % 2:
            a[y_, x_] = a[y_ + 1, x_] if (y_ + 1 < a.shape[0] and not lich[y_ + 1, x_]) else C('slate', 2)
    _moss_cushions(a, roof, y_r + 5, y_e - 3, seed + 41, n=4)
    Hs.ridge_tiles(a, roof, rx0 + 3, rx1 - 3, y_r, rng, fam='clay')
    a[roof & (Yg >= y_e - 3) & (Yg == y_e - 3)] = C('slate', 5)                 # the eave course edge on: its lit arris,
    a[roof & (Yg >= y_e - 2)] = C('slate_cool', 2)                                # the slates' thickness,
    a[roof & (Yg == y_e - 1)] = C('slate_cool', 1)                                # the shade under them
    for (xa, t) in ((rx0, 3), (rx1 - 5, 2)):                                     # barge boards on the verges
        V.beam(a, xa, y_r - 1, xa + 5, y_e + 2, rng, 'timber', t, hd=True)
        a[(Xg >= xa) & (Xg < xa + 5) & (Yg == y_r - 1)] = C('timber', t + 1)
    a[(Xg >= rx0 + 5) & (Xg < rx0 + 7) & (Yg > y_r + 6) & (Yg < y_e - 3) & roof] = C('slate', 4)     # the cut slates lit inside the west board
    a[(Xg >= rx1 - 7) & (Xg < rx1 - 5) & (Yg > y_r + 6) & (Yg < y_e - 3) & roof] = C('slate_cool', 1)
    # the eave: fascia with a lit lip, the gutter lit on its upper left
    fas = _tagm(sc, 'fascia')
    rpaint(a, fas, CREAM, np.where(sc.n[..., 2] > 0.5, 4.2, 3.0), 0.3)
    gut = _tagm(sc, 'gutter')
    gt = np.where(sc.n[..., 2] > 0.5, 2.6, 2.2)
    gr = (Yg - ox) * 0
    rpaint(a, gut, IRON, gt, 0.3)
    gys, gxs = np.nonzero(gut)
    if len(gys):
        g0 = gys.min()
        a[(Yg == g0 + 1) & gut & ((Xg % 7) != 3)] = C('slate', 4)          # the gutter's highlight
        a[(Yg == gys.max()) & gut] = C('void', 1)
    # the valance: boards on end, 4 texels wide, each lit on its west edge and darker on its east, a
    # dark line under the fascia above, the lower edge cut in scallops with the wall behind showing
    val = _tagm(sc, 'valance')
    vys = np.nonzero(val)[0]
    vt, vb = vys.min(), vys.max()
    bx = (Xg - ox + 120) % 4
    vt_ = np.where(bx == 0, 4.2, np.where(bx == 3, 2.6, 3.4))
    vt_ = vt_ + np.where(K.vhash((Xg - ox + 120) // 4, 0, seed + 7) > 0.8, -0.6, 0.0)
    rpaint(a, val, CREAM, vt_, np.clip(K.vhash((Xg - ox + 120) // 4, 1, seed + 8) * 0.999, 0, 0.999))
    a[val & (Yg == vt)] = C('ashlar', 1)                                  # the shade under the fascia
    ph = (Xg - ox + 120) % 8
    cut = val & (((Yg == vb) & np.isin(ph, (5, 6, 7, 0, 1))) | ((Yg == vb - 1) & np.isin(ph, (6, 7, 0))) | ((Yg == vb - 2) & (ph == 7)))
    rpaint(a, cut, CREAM, 2.0, 0.0)                                       # the wall behind, through the cut-outs
    hole = val & (ph == 3) & (Yg >= vb - 6) & (Yg <= vb - 5)
    a[hole] = C('ashlar', 1)
    # under the roof: the eave's shadow on the back wall and sides, deepest under the eave
    under = walls & (z > 0) & (sc.gy < -6)
    V._step(a, under & (z > 36), -1)
    # the bench: a seat seen as a lit top plane of boards, its front edge, the shade under it, a
    # backrest of boards, legs lit on their west side, its shadow on the floor
    seat = _tagm(sc, 'seat')
    stop = seat & (sc.n[..., 2] > 0.5)
    sfr = seat & ~stop
    _planks(a, stop, OAK, 3.6, gx + 200, (Yg - oy).astype(float) + 300, seed + 4, pitch=4, grain=0.05)
    sfy = np.nonzero(sfr)[0]
    rpaint(a, sfr, OAK, np.where(Yg == sfy.min(), 3.2, np.where(Yg == sfy.max(), 1.2, 2.4)), 0.3)
    br = _tagm(sc, 'backrest')
    _planks(a, br, OAK, 2.8 + 0.4 * L, gx + 200, -z + 300, seed + 5, pitch=5)
    nails = (stop | br) & ((np.abs(gx + 40) < 0.6) | (np.abs(gx - 26) < 0.6)) & (((Yg - oy) % 4) == 1)
    a[nails] = C('iron', 1)
    legs = _tagm(sc, 'leg')
    for x in (-40, -7, 26):
        lm = legs & (np.abs(gx - x) < 1.6)
        rpaint(a, lm, IRON, np.where(gx < x - 0.5, 3.4, np.where(gx > x + 0.5, 1.4, 2.4)), 0.3)
    fl_ = _tagm(sc, 'floor', 'back')
    sh = fl_ & (Yg > sfy.max()) & (Yg <= sfy.max() + 3) & (gx > -42) & (gx < 33)
    V._step(a, sh, -1)
    # the poster: a printed sheet in a dark frame with a coloured block and a torn corner
    px, py = ox + 36, oy + YB - 50
    a[py:py + 22, px:px + 18] = C('leaf_cool', 1)
    rpaint(a, (Yg >= py + 1) & (Yg < py + 21) & (Xg >= px + 1) & (Xg < px + 17), CREAM, 3.2 - 0.5 * (Yg > py + 14), 0.4)
    a[py + 3:py + 10, px + 3:px + 15] = C('clay', 2)
    a[py + 4:py + 6, px + 4:px + 14] = C('clay', 3)
    a[py + 6:py + 9, px + 5:px + 11] = C('sky_cool', 3)
    for r_ in range(3):
        n = 6 + int(5 * hsh(seed, r_))
        a[py + 12 + r_ * 2, px + 3:px + 3 + n] = C('slate', 2)
    a[py + 18:py + 21, px + 14:px + 17] = C('slate_cool', 2)
    a[py + 19:py + 21, px + 15:px + 17] = C('leaf', 2)
    a[py + 20, px + 16] = C('leaf', 2)
    # the floor: flags, worn, in the roof's shade under it
    fl = _tagm(sc, 'floor')
    ftop = fl & (sc.n[..., 2] > 0.5)
    _stone_parts(a, ftop, gx + 300, -(sc.gy) + 60, seed + 6, GRANITE, 2.9 + 0.0 * L, lo=10, hi=16, course=8,
                 mortar=('stone_cool', 1))
    V._step(a, ftop, -1)
    # the bench's shadow on the floor (R3-13): two rows two tones down at the legs' feet, thrown east
    lfoot = np.nonzero(legs.any(1))[0].max()
    fsh = ftop & (Yg > lfoot) & (Yg <= lfoot + 2) & (gx > -38) & (gx < 31) & ~legs
    V._step(a, fsh, -2)
    _finish(a)
    return K.crop(a, ox, oy)


CHURN_TIN = [('slate_cool', 'stone_cool', 'stone'), ('slate_cool', 'stone', 'stone_warm')]
# galvanised tin by tone, two siblings each at about one value (round 3 of the detail audit, R3-3):
# its own grey ramp from the outline (stone's edge, not navy) to a highlight at about 210 L
TIN_C = [(C('stone', 1), C('stone', 1)),              # 75 L: the deepest gaps
         (C('slate_cool', 3), C('iron', 4)),           # 111, 113: the east third
         (C('slate_warm', 3), C('slate_warm', 3)),     # 127: the handles, the shade turning
         (C('slate_warm', 4), C('snow_cool', 1)),      # 153, 144: the body
         (C('snow', 2), C('snow_cool', 2)),            # 187, 178: the lit west third, its middle and edges
         (C('snow_cool', 3), C('snow_cool', 3))]       # 211: the one-texel highlight


def _tin(a, m, t, X, Y, seed, sib=None):
    """Paint mask m in galvanised tin at float tones t (see TIN_C), the two siblings in a few streaks
    lying with the seams, or as `sib` gives them."""
    ti = np.clip(np.round(np.broadcast_to(np.asarray(t, float), m.shape)), 0, 5).astype(int)
    if sib is None:
        sib = K.vhash(X // 2, Y // 5, seed) > 0.82
    lut = np.array(TIN_C)
    a[m] = lut[ti, sib.astype(int)][m]


def _churn_profile():
    """A 17-gallon churn's radius from the foot (texels): the foot's rolling band, the body, the
    shoulder band, the taper, the neck stepping in under the lid, the lid's flange and its crown."""
    return [8.2] * 3 + [7.6] * 14 + [8.0] * 2 + [7.0, 6.0, 5.0, 4.4] + [4.0] * 3 + [5.6] * 2 + [5.2]


def churn_stand(seed=125):
    """A milk-churn stand at the lane's end: a deck of boards at cart height (0.65 m) on four posts with
    a cross-brace, three galvanised churns on it waiting for the train, each 0.78 m tall and 0.35 m
    across (Eastward's milk cans in 17). Each churn is a cylinder: a highlight band 2 texels wide a
    third in from the west (tin 5), the body, the east third in shade with a warm reflection from the
    stand along its lower east edge; rolling bands at the foot and the shoulder, each a lit top line
    over a dark under line; the neck stepping in under the lid; a mushroom lid seen from above, an
    ellipse lit on its far rim and dark on its near rim, with a loop handle; two side handles as lit
    hoops. The three differ: one has its lid handle turned to the front, one a dent, one a painted
    dairy mark."""
    sc = K.Scene(-40, 40, -14, 10, 72)
    for x in (-28, 28):
        for y in (-9, 1):
            sc.box(x - 1.6, y - 1.6, 0, x + 1.6, y + 1.6, 25, OAK, base=2.3, k=1.5, tag='leg', mix=hsh(x, y))
    sc.box(-28, 1.2, 8, 28, 2.4, 11, OAK, base=2.4, k=1.4, tag='brace', mix=0.4)
    sc.box(-32, -12, 25, 32, 4, 28, OAK, base=2.8, k=1.4, tag='deck', mix=0.3)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox + 0.5
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    deck = _tagm(sc, 'deck')
    _planks(a, deck & ~side, OAK, 3.0, gx + 200, (Yg - oy).astype(float) + 300, seed, pitch=5, grain=0.06, joint=0.8)
    rpaint(a, deck & side, OAK, 2.4, 0.3)
    a[deck & side & (Yg == np.nonzero(deck & side)[0].min())] = C('timber_warm', 3)
    legs = _tagm(sc, 'leg', 'brace')
    for x in (-28, 28):
        m = legs & side & (np.abs(gx - x) < 2)
        rpaint(a, m, OAK, np.where(gx < x - 0.5, 3.0, 2.2), 0.3)
    B._lichen(sc, a, tags=('leg',), rate=0.6, seed=seed)
    prof = _churn_profile()
    tins = np.zeros((H, W), bool)
    for k, (x, y) in enumerate(((-19, -4), (0, -2), (19, -4))):
        fx, fy = ox + x, oy + y - 28
        m, hh, u, top = _lathe(a.shape, fx, fy, prof)
        tins |= m
        hi = np.floor(hh).astype(int)
        side_ = m & ~top
        # galvanised tin is a mid-value body with a soft lit band (Eastward's churns in 17 and 13,
        # p90 126 to 193 L): the body in tin 3, the lit west third in tin 4, the east third in tin 1
        # to 2, the rim turning away a step down on the far west
        t = np.full((H, W), 3.0)
        t = np.where((u > -0.78) & (u < -0.18), 4.0, t)
        t = np.where(u > 0.22, 2.0, t)
        t = np.where(u > 0.58, 1.0, t)
        t = np.where(u < -0.86, 3.0, t)
        # rolling bands: a lit top line over a dark under line, at the foot and the shoulder
        for b0 in (0, 17):
            t = np.where(side_ & (hi == b0 + 1), np.minimum(np.maximum(t + 1, 2), 4), t)
            t = np.where(side_ & (hi == b0), np.maximum(t - 1, 1), t)
        # the neck in the lid's shade, stepping in; the lid's flange dark under
        t = np.where(side_ & (hi >= 23) & (hi < 26), np.maximum(t - 1, 1), t)
        t = np.where(side_ & (hi == 26), np.maximum(t - 1, 1), t)
        # upward faces: the shoulder's slope lit on the west, the lid's crown below
        t = np.where(top, 3.0 + 1.0 * (u < -0.1) - 1.0 * (u > 0.5), t)
        # the highlight: one texel wide, only on the mid-body and the shoulder (tin 5)
        band = side_ & (u > -0.6) & (u < -0.3) & (((hi >= 5) & (hi <= 14)) | ((hi >= 19) & (hi <= 21)))
        lead = band & ~np.roll(band, 1, 1)
        t = np.where(lead, 5.0, t)
        # the lit third turns through its own planes: its edges a step cooler, its middle the lightest
        sib = np.where(np.round(t) == 4, (u < -0.6) | (u > -0.32), K.vhash(Xg // 2, Yg // 5, seed + 7 * k) > 0.82)
        _tin(a, m, t, Xg, Yg, seed + 7 * k, sib=sib)
        crown = m & top & (hi >= 27)
        cys, cxs = np.nonzero(crown)
        if len(cys):
            cy0, cy1 = cys.min(), cys.max()
            ccy = (cy0 + cy1 + 1) / 2.0
            # the lid's crown: an ellipse with a raised inner ring in tin 2, a lit far rim, the near
            # rim a step down (a lid, not a pair of lenses)
            rr = np.hypot((Xg + 0.5 - fx) / 5.0, (Yg + 0.5 - ccy) / 2.0)
            ct = np.where(rr < 0.55, 2.0, 3.0)
            ct = np.where(rr < 0.3, 3.0, ct)
            ct = np.where(Yg == cy0, 4.0, ct)
            ct = np.where(Yg == cy1, 2.0, ct)
            _tin(a, crown, ct, Xg, Yg, seed + 3 * k)
            # the lid as the churn's main read (R4-7): a 10 x 4 ellipse, its far rim lit, a ring in
            # tin 2 round a centre in tin 3, the near rim a step down
            # (R5-9) a 12 x 5 lid overhanging the neck a texel each side, a ring line a tone down a
            # texel inside its rim, its far rim lit
            lcy = cy0 + 2.5
            lid = ((((Xg + 0.5 - fx) / 6.2) ** 2 + ((Yg + 0.5 - lcy) / 2.6) ** 2) <= 1.0)
            lr = np.hypot((Xg + 0.5 - fx) / 6.2, (Yg + 0.5 - lcy) / 2.6)
            lt = np.where(lr < 0.5, 3.0, np.where(lr < 0.78, 2.0, 3.0))
            lt = np.where(lid & (Yg + 0.5 < lcy) & (lr >= 0.78), 4.0, lt)
            lt = np.where(lid & (Yg + 0.5 > lcy + 1.2) & (lr >= 0.78), 2.0, lt)
            _tin(a, lid, lt, Xg, Yg, seed + 5 * k, sib=np.zeros((H, W), bool))
            tins |= lid
        # the warm light thrown up from the stand's boards along the lower east edge
        a[side_ & (u > 0.72) & (hi >= 3) & (hi < 7)] = C('timber_warm', 3)
        # the lid's loop handle: a strap of tin 2 with a lit top texel, turned to the front on the
        # middle churn, lying across the crown on the others
        ly = fy - 30
        if k == 1:
            a[ly - 1, fx - 1:fx + 2] = TIN_C[2][0]
            a[ly - 1, fx - 1] = TIN_C[4][0]
            a[ly, fx - 2] = TIN_C[2][0]
            a[ly, fx + 2] = TIN_C[1][0]
        else:
            a[ly - 1, fx - 2:fx + 3] = TIN_C[2][1]
            a[ly - 1, fx - 2] = TIN_C[4][0]
            a[ly - 1, fx + 2] = TIN_C[1][0]
        # side handles: small hoops at the shoulder in tin 2, lit on top
        for sx in (-1, 1):
            hx = fx + sx * 9
            hy = fy - 20
            a[hy, hx - (1 if sx > 0 else 0):hx + (1 if sx < 0 else 0) + 1] = TIN_C[4][0] if sx < 0 else TIN_C[3][0]
            a[hy + 1:hy + 4, hx] = TIN_C[2][0] if sx < 0 else TIN_C[1][0]
            a[hy + 3, hx - sx] = TIN_C[1][0]
        if k == 0:                                                         # a dent, its lit lower lip
            a[side_ & (np.abs(u - 0.15) < 0.14) & (np.abs(hh - 10) < 1.2)] = TIN_C[1][0]
            a[side_ & (np.abs(u - 0.15) < 0.14) & (np.abs(hh - 8.6) < 0.5)] = TIN_C[4][0]
        if k == 2:                                                         # the dairy's painted mark
            a[side_ & (u > -0.35) & (u < 0.25) & (hi >= 9) & (hi < 12)] = C('clay', 3)
            a[side_ & (u > -0.35) & (u < 0.25) & (hi == 11)] = C('clay', 4)
    _finish(a)
    # the tin closed in its own edge tone (about 67 L), not ink (R4-7)
    ring = ndi.binary_dilation(tins) & ~tins & (a >= 0) & (a % 8 == 6)
    a[ring] = C('stone_cool', 1)
    B._ground_tufts(a, ox, oy, [-31, -25, 25, 31], seed)
    return K.crop(a, ox, oy)


def semaphore(seed=127):
    """A semaphore home signal at the platform's end, 3 m: a square post painted white (black to a
    man's height) in three tones (a lit west column, the body, the shaded east column) on a granite
    base, a cap and a finial with a lit dome; the red arm at danger with a lit top edge and a shaded
    underside, its white stripe edged darker; the spectacle cast with the arm at its pivot, its red and
    green lenses round in their frame, each with a glint; a ladder up the post's front, its stiles lit
    on the west and its rungs lit on top."""
    sc = K.Scene(-30, 36, -10, 10, 150)
    sc.box(-10, -6, 0, 10, 6, 6, GRANITE, base=2.6, k=1.4, tag='base', round_=1.0, mix=0.4)
    sc.box(-2.5, -2.5, 6, 2.5, 2.5, 128, WHITE, base=3.0, k=1.2, tag='post', mix=0.2)
    sc.box(-3.5, -3.5, 128, 3.5, 3.5, 130.5, IRON, base=2.4, k=1.4, tag='cap', mix=0.3)
    sc.ellipsoid(0, 0, 132.5, 2.4, 2.4, 2.6, IRON, base=2.6, k=1.8, tag='finial', mix=0.3)
    sc.box(2.5, -1.2, 112, 29, 1.2, 117, RED, base=2.8, k=1.2, tag='arm', mix=0.2)
    sc.box(-4, -4.5, 108, 0, -2.5, 115, IRON, base=2.2, k=1.4, tag='lampcase', mix=0.3)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox
    z = sc.depth
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    post = _tagm(sc, 'post')
    col = np.where(gx < -1, 4.5, np.where(gx >= 1, 2.0, 3.4))
    rpaint(a, post & side & (z >= 26), WHITE, col, 0.3)
    rpaint(a, post & side & (z < 26), IRON, col - 1.0, 0.3)
    a[post & side & (np.abs(z - 26) < 0.6)] = C('void', 1)
    rpaint(a, post & ~side, WHITE, 4.6, 0.2)
    _streaks(a, post & side & (z > 30) & (z < 110), Xg, Yg, seed, rate=0.012, length=(3, 6), fam='snow_cool', step=-1)
    cap = _tagm(sc, 'cap', 'finial')
    rpaint(a, cap, IRON, 2.2 + 1.8 * L, 0.3)
    # the arm: a lit top edge, the shaded underside, the white stripe edged darker
    arm = _tagm(sc, 'arm')
    ays = np.nonzero(arm & side)[0]
    at, ab = ays.min(), ays.max()
    t = np.where(Yg == at, 3.9, np.where(Yg == ab, 1.6, 2.8))
    rpaint(a, arm & side, RED, t, 0.2)
    rpaint(a, arm & ~side, RED, 3.8, 0.2)
    stripe = arm & (gx >= 21) & (gx < 25)
    rpaint(a, stripe, WHITE, np.where(Yg == ab, 2.4, np.where(Yg == at, 4.6, 3.8)), 0.2)
    a[arm & side & ((gx == 20) | (gx == 25))] = C('crag_cool', 1)
    # the spectacle, cast with the arm at the pivot: an iron frame, two round lenses
    sx, sy = ox - 7, oy - 112
    frame = _line(a.shape, sx + 0.5, sy + 0.5, sx + 0.5, sy + 8.5, 3.0) | _line(a.shape, sx + 0.5, sy - 1.5, ox + 2.0, oy - 114.5, 2.4)
    frame |= _disc(a.shape, sx + 0.5, sy + 0.5, 3.8) | _disc(a.shape, sx + 0.5, sy + 8.5, 3.8)
    rpaint(a, frame, RED, np.where(Xg < sx - 1, 3.0, np.where(Xg > sx + 1, 1.6, 2.4)), 0.4)   # cast with the arm
    for (lx, ly, fam, gl) in ((sx, sy, 'clay', 'fox'), (sx, sy + 8, 'leaf', 'grass')):
        lens = _disc(a.shape, lx + 0.5, ly + 0.5, 2.5)
        a[lens] = C(fam, 3)
        a[_disc(a.shape, lx + 0.5, ly + 1.3, 1.5) & lens] = C(fam, 4)
        a[ly - 1, lx - 1] = C(gl, 5)
    piv = _disc(a.shape, ox + 1.5, oy - 114.5, 1.8)
    a[piv] = C('iron', 3)
    a[oy - 115, ox + 1] = C('slate', 4)
    base = _tagm(sc, 'base')
    btop = base & ~side
    rpaint(a, btop, GRANITE, np.where(gx < 0, 3.9, 3.4), np.where(gx < 3, 0.1, 0.5))   # two slabs, siblings
    a[btop & (np.abs(gx - 3) < 0.5)] = C('stone_cool', 1)                  # their joint
    bfr = np.nonzero(base & side)[0]
    if len(bfr):
        a[btop & (Yg == bfr.min() - 1) & (gx < 6)] = C('stone_warm', 5)      # the front arris, lit
    psh = btop & (gx > 2.5) & (gx < 7) & (Yg < (bfr.min() if len(bfr) else 0) - 1)
    V._step(a, psh, -1)                                                  # the post's shadow on it
    _stone_parts(a, base & side, gx + 100.0, z, seed, GRANITE, 2.6, lo=9, hi=13, course=6)
    _finish(a, keep=np.isin(a, [C('clay', 3), C('clay', 4), C('leaf', 3), C('leaf', 4), C('fox', 5), C('grass', 5)]))
    # the ladder up beside the post (after the outline, so the ground shows between its stiles):
    # stiles lit west, rungs lit on top
    ly0, ly1 = oy - 106, oy - 6
    for x0 in (ox + 4, ox + 9):
        a[ly0:ly1, x0] = C('iron', 3)
        a[ly0:ly1, x0 + 1] = C('void', 2)
    for yy in range(ly0 + 2, ly1 - 2, 6):
        a[yy, ox + 6:ox + 9] = C('iron', 3)
        a[yy + 1, ox + 6:ox + 9] = C('void', 2)
    B._ground_tufts(a, ox, oy, [-11, -9, 9, 11], seed)
    return K.crop(a, ox, oy)


def _lamp_frame(i, seed=129):
    """The platform lamp, 2.9 m: a cast-iron column in the railway's green on a fluted foot with a
    collar, lit as a cylinder; an iron ladder bar under the lantern, lit along its top; the lantern four
    panes in a frame (one face seen, two panes), the glass lit from inside, brighter low in the middle
    where the flame is, a glint on the frame; a domed cap with a vent and a finial. The flame flickers
    over the cycle."""
    W, H = 40, 140
    a = np.full((H, W), -1, np.int32)
    ox, oy = 20, 136
    Yg, Xg = np.mgrid[0:H, 0:W]
    gx = Xg - ox + 0.5
    prof = [6.0, 6.0] + [5.2] * 5 + [4.0] * 2 + [3.2] * 2 + [2.7] * 85 + [3.7] * 3
    m, hh, u, top = _turned(a, ox, oy, prof, GREEN, lit=4.0, body=2.8, shade=1.5)
    V._step(a, m & ~top & (hh >= 2) & (hh < 7) & ((np.floor(gx + 20).astype(int) % 3) == 1), -1)   # the foot's flutes
    a[m & ~top & (hh >= 2) & (hh < 3)] = C('soot', 1)
    zb = len(prof)                                                      # the ladder bar
    by = oy - zb
    a[by - 1, ox - 8:ox + 8] = C('iron', 3)
    a[by, ox - 8:ox + 8] = C('iron', 1)
    a[by - 1, ox - 8] = C('iron', 2)
    # the lantern: its base frame, two panes lit from inside, the frame's posts and astragal
    lx0, lx1, ly1 = ox - 8, ox + 8, by - 1
    a[ly1 - 2:ly1, lx0 - 1:lx1 + 1] = C('iron', 2)
    a[ly1 - 2, lx0 - 1:lx1 + 1] = C('iron', 3)
    gy0, gy1 = ly1 - 18, ly1 - 2
    gl = (Yg >= gy0) & (Yg < gy1) & (Xg >= lx0) & (Xg < lx1)
    fl = [0.0, 0.6, 0.3, 0.9, 0.5, 0.2, 0.8, 0.4][i]
    zt = (gy1 - Yg) / float(gy1 - gy0)
    gt = 3.0 + 1.0 * ((Yg >= gy0 + 6) & (np.abs(gx) < 5.5)) + 0.4 * fl * (Yg >= gy0 + 6)
    rpaint(a, gl, [('lamp', 'lamp', 'lamp')], gt, 0.0)
    hot = 2 + int(round(4 * fl))                                          # the flame's glow in each pane, flickering
    flame = gl & (np.abs(np.abs(gx) - 3.5) < 1.0) & (Yg >= gy1 - 2 - hot) & (Yg < gy1 - 2)
    a[flame] = C('lamp', 5)
    a[gl & ((Xg < lx0 + 2) | (Xg >= lx1 - 2) | (np.abs(gx) < 1.5))] = C('iron', 1)    # the frame's posts and astragal, 2 wide
    a[gl & (Xg == lx0) & (Yg >= gy0 + 4) & (Yg < gy1 - 4)] = C('slate', 4)          # the frame's glint
    # the cap: a rim, a dome lit west, a vent and a finial
    cprof = [7.4, 7.4, 6.2, 5.8, 5.0, 4.0, 2.6, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.6, 1.6]
    cm, ch, cu, ctop = _turned(a, ox, gy0, cprof, GREEN, lit=4.0, body=2.8, shade=1.5, top_t=3.6)
    a[cm & ~ctop & (ch < 1)] = C('soot', 1)                                   # the rim's drip edge
    a[cm & ~ctop & (ch >= 7) & (ch < 10) & ((np.floor(gx + 20).astype(int) % 2) == 0)] = C('soot', 1)   # the vent
    fin = cm & (ch >= 10)
    rpaint(a, fin, IRON, np.where(cu < 0, 3.6, 2.0), 0.3)
    keep = gl | flame
    _finish(a, keep=keep)
    B._ground_tufts(a, ox, oy, [-7, -6, 6, 7], seed)
    return a, ox, oy


def platform_lamp(seed=129):
    pics = _strip_frames(_lamp_frame)
    return pics[0], {'frames': pics, 'fps': 6.0, 'clip': 'flicker'}


def timetable_board(seed=131):
    """The halt's timetable board on two posts under a little gabled hood: a printed sheet behind glass
    in a green frame; the sheet's header band holds a small train and a clock, its rows are print (grey
    dashes of uneven length, as handwriting and type read at this size), a smaller notice pinned
    askew at the corner, a glint across the glass in 2-texel steps at the upper left. The posts are lit
    in three tones; the hood's west plane lit, its east plane in shade, a drip edge under it."""
    W, H = 64, 112
    a = np.full((H, W), -1, np.int32)
    ox, oy = 32, 108
    Yg, Xg = np.mgrid[0:H, 0:W]
    gx = Xg - ox
    # the posts, square, three tones each
    for px in (-19, 15):
        m = (gx >= px) & (gx < px + 4) & (Yg > oy - 84) & (Yg <= oy)
        rpaint(a, m, GREEN, np.where(gx == px, 3.8, np.where(gx == px + 3, 1.6, 2.6)), 0.3)
        a[(gx >= px) & (gx < px + 4) & (Yg > oy - 4) & (Yg <= oy)] = C('soot', 1)    # tarred at the foot
    # the frame and the sheet behind glass
    fx0, fx1, fy0, fy1 = ox - 24, ox + 24, oy - 82, oy - 38
    frame = (Xg >= fx0) & (Xg < fx1) & (Yg >= fy0) & (Yg < fy1)
    rpaint(a, frame, GREEN, np.where(Yg == fy0, 3.8, np.where(Xg == fx1 - 1, 1.6, np.where(Yg == fy1 - 1, 1.8, 2.8))), 0.3)
    sx0, sx1, sy0, sy1 = fx0 + 3, fx1 - 3, fy0 + 3, fy1 - 3
    sheet = (Xg >= sx0) & (Xg < sx1) & (Yg >= sy0) & (Yg < sy1)
    rpaint(a, sheet, [('ashlar', 'plaster', 'plaster'), ('ashlar', 'plaster_warm', 'plaster_warm')], 4.0 - 1.0 * (Yg < sy0 + 1),
           np.clip(K.noise(a.shape, np.random.default_rng(seed), 6.0) * 0.999, 0, 0.999))
    # the header band: a small train and a clock
    a[sy0 + 1:sy0 + 7, sx0 + 1:sx1 - 1] = C('leaf_cool', 2)
    a[sy0 + 1, sx0 + 1:sx1 - 1] = C('leaf', 3)
    tx, ty = sx0 + 4, sy0 + 2
    a[ty + 1:ty + 4, tx:tx + 7] = C('plaster', 4)                          # the engine's body
    a[ty:ty + 2, tx + 1:tx + 3] = C('plaster', 4)                          # its cab
    a[ty, tx + 5] = C('plaster', 4)                                         # its chimney
    a[ty + 4, tx + 1] = C('plaster', 3)
    a[ty + 4, tx + 5] = C('plaster', 3)
    cx, cy = sx1 - 6, sy0 + 4
    a[_disc(a.shape, cx + 0.5, cy + 0.5, 2.6)] = C('plaster', 4)
    a[cy - 1:cy + 1, cx] = C('slate', 1)
    a[cy, cx:cx + 2] = C('slate', 1)
    # the print: rows of grey dashes of uneven length, in two columns
    yy = sy0 + 10
    for r_ in range(6):
        yy += 0 if r_ == 0 else 3 + int(2 * hsh(seed, r_, 77))             # the rows unevenly spaced, as set by hand
        x = sx0 + 2
        k = 0
        while x < sx1 - 3:
            n = 2 + int(5 * hsh(seed, r_, k))
            n = min(n, sx1 - 3 - x)
            if r_ % 3 == 2 and x > sx0 + 20:
                break
            a[yy, x:x + n] = C('stone_cool', 2) if k == 0 else C('stone', 3)
            x += n + 1 + int(2 * hsh(seed + 1, r_, k))
            k += 1
    a[sy0 + 9:sy1 - 1, ox] = C('stone', 3)                                    # the column rule
    # a smaller notice pinned askew at the lower right, its pin red
    nx, ny = sx1 - 12, sy1 - 12
    note = _poly(a.shape, [(nx, ny + 1), (nx + 10, ny), (nx + 11, ny + 10), (nx + 1, ny + 11)])
    rpaint(a, note, [('ashlar_warm', 'plaster_warm', 'snow_warm')], 4.4 - 1.0 * (Yg > ny + 8), 0.0)
    for r_ in range(3):
        a[ny + 3 + r_ * 2, nx + 2:nx + 2 + 4 + int(4 * hsh(seed, 9, r_))] = C('clay', 2)
    a[ny + 1, nx + 5] = C('clay', 4)
    # the glint across the glass, in 2-texel steps, upper left
    for k in range(5):
        a[sy0 + 8 + k * 2:sy0 + 10 + k * 2, sx0 + 1 + k * 2:sx0 + 3 + k * 2] = C('snow', 5)
    # the hood: a little gable, its west plane lit, its east plane in shade, a drip edge under it
    hy = fy0 - 1
    for dy in range(10):
        half = 28 - dy * 2.8
        if half < 1:
            break
        yy = hy - dy
        xs = np.arange(int(ox - half), int(ox + half))
        a[yy, xs[xs < ox]] = C('slate', 4) if dy else C('slate', 3)
        a[yy, xs[xs >= ox]] = C('slate_cool', 2) if dy else C('slate_cool', 1)
        if dy and dy % 3 == 0:
            a[yy, xs[xs < ox]] = C('slate', 3)
            a[yy, xs[xs >= ox]] = C('slate_cool', 1)
    a[hy + 1, ox - 26:ox + 26] = C('void', 1)                                 # the drip edge's shadow
    a[hy - 9:hy - 1, ox] = C('slate_warm', 4)                                 # the ridge
    _finish(a)
    for px in (-19, 15):                                                       # moss at the posts' feet
        a[oy - 2:oy, ox + px - 1:ox + px + 1] = C('leaf_cool', 2)
    B._ground_tufts(a, ox, oy, [-21, -14, 13, 20], seed)
    return K.crop(a, ox, oy)


# ================================================================================================
# the Millrace landslip
# ================================================================================================
def _moss_cushions(a, rm, y_r, y_eave, seed, n=4, rh=None):
    """Moss as cushions in a slate roof's lower joints (round 3 of the detail audit, R3-13): each a
    soft mound 5 to 9 texels wide sitting in the joint along a course's butt in the lower part of the
    roof, its top lit (lit most on the west), its body, a dark row under it on the slate below; never
    a mark in the middle of a slate."""
    H, W = a.shape
    rh = rh or max(6, Hs.q(3.2))
    xs = np.nonzero(rm.any(0))[0]
    for k in range(n):
        course = 1 + int(3 * hsh(seed, k, 2))                           # one of the three lowest joints
        jy = y_eave - course * rh
        if jy <= y_r + 2:
            continue
        cx = int(xs.min() + 8 + (xs.max() - xs.min() - 16) * hsh(seed, k, 1))
        w_ = 5 + int(5 * hsh(seed, k, 3))
        for dx in range(w_):
            x = cx + dx
            hgt = 2 + (1 if 1 <= dx < w_ - 1 else 0) + (1 if 2 <= dx < w_ - 2 and hsh(seed, k, dx) > 0.5 else 0)
            for j in range(hgt):
                y = jy - j
                if 0 <= y < H and 0 <= x < W and rm[y, x]:
                    if j == hgt - 1:
                        a[y, x] = C('grass', 4) if dx < w_ // 2 else C('leaf', 3)
                    elif j == 0:
                        a[y, x] = C('leaf', 2)
                    else:
                        a[y, x] = C('leaf', 3) if dx < w_ // 2 else C('leaf', 2)
            if 0 <= jy + 1 < H and 0 <= x < W and rm[jy + 1, x]:
                a[jy + 1, x] = C('leaf_cool', 1)                            # its shade on the slate below


# The water mill at the size guide's `water_mill` (round 5 of the detail audit, R5-1): 104 world px
# wide (14 x 7 cells), two storeys and a loft, 76 to the eaves, built by the house builder
# (houses.building) like the Crossroads houses, whose eaves are 40: a loading door 32 x 22 on the
# yard side with a hoist door and its beam above, the wheel 44 across on the water side.
MILL_SPEC = dict(w=104, depth=56, wall_h=76, roof_h=40, wall='stone', roof='slate', paint='timber', doors=[[18, 'timber']],
                 door_w=22, door_h=32, windows=[44], win_w=12, win_h=12, win_top=34, shutters=False)
MILL_WHEEL_R = 66.0            # art px: a wheel 44 world px (132 art px) across
MILL_DIP = 14                  # art px: the race's surface below the wall's foot, where the wheel stands in it
_MILL = {}


def _hoist_door(a, cx, sill, w, h, seed):
    """The mill's hoist door under the eaves, over the loading door: a ledged door of vertical boards
    (each lit on its west edge over a dark groove, the head in the lintel's shade stepping down in
    two tones), two ledges lit on top, strap hinges; a dressed lintel and jambs and a sill; above it
    the hoist beam's end standing out of the wall (end grain with its rings, lit on top, its shadow on
    the wall) with its pulley and the rope hanging down past the door."""
    x0, x1, y0 = int(cx - w // 2), int(cx + w // 2), int(sill - h)
    jw = 5
    # the surround: lintel, jambs, sill
    a[y0 - 6:y0, x0 - jw:x1 + jw] = C('stone', 3)
    a[y0 - 6, x0 - jw:x1 + jw] = C('stone_warm', 4)
    a[y0 - 1, x0 - jw:x1 + jw] = C('stone_cool', 1)
    a[y0:sill, x0 - jw:x0] = C('stone', 3)
    a[y0:sill, x0 - jw] = C('stone_warm', 4)
    a[y0:sill, x1:x1 + jw] = C('stone_cool', 2)
    a[sill:sill + 3, x0 - jw - 2:x1 + jw + 2] = C('stone', 3)
    a[sill, x0 - jw - 2:x1 + jw + 2] = C('stone_warm', 4)
    a[sill + 2, x0 - jw - 2:x1 + jw + 2] = C('stone_cool', 1)
    # the boards
    for x in range(x0, x1):
        u = (x - x0) % 6
        for y in range(y0, sill):
            d = y - y0
            if u == 0:
                c = C('timber_cool', 1)
            elif u == 1:
                c = C('timber_warm', 4)
            else:
                c = C('timber_warm', 3) if hsh(seed, x // 6, y // 5) > 0.55 else C('timber', 3)
            if d < 2:
                c = C('timber_cool', 1) if u == 0 else C('timber_cool', 2)    # the head in the lintel's shade
            elif d < 5 and u != 0:
                c = C('timber', 2)
            a[y, x] = c
    for ly in (y0 + int(h * 0.28), y0 + int(h * 0.72)):              # the ledges
        a[ly, x0:x1] = C('timber_warm', 4)
        a[ly + 1:ly + 3, x0:x1] = C('timber', 3)
        a[ly + 3, x0:x1] = C('timber_cool', 1)
        a[ly + 1:ly + 3, x0:x0 + w // 2] = C('iron', 2)                 # a strap hinge
        a[ly + 1, x0:x0 + w // 2] = C('iron', 4)
        for nx in range(x0 + 3, x0 + w // 2, 6):
            a[ly + 2, nx] = C('slate', 4)
    # the hoist beam's end above the lintel: end grain with its rings, lit on top, its shadow below
    bx0, by0 = int(cx - 6), y0 - 6 - 14
    a[by0:by0 + 12, bx0:bx0 + 12] = C('earth_warm', 3)
    a[by0, bx0:bx0 + 12] = C('timber_warm', 4)
    a[by0:by0 + 12, bx0] = C('timber_warm', 4)
    a[by0 + 3:by0 + 9, bx0 + 3:bx0 + 9] = C('earth', 3)
    a[by0 + 5:by0 + 7, bx0 + 5:bx0 + 7] = C('earth_cool', 2)
    a[by0 + 11, bx0:bx0 + 12] = C('timber_cool', 1)
    a[by0 + 12:by0 + 14, bx0 + 2:bx0 + 14] = C('stone_cool', 1)          # its shadow on the wall
    # the pulley under it and the rope down past the door
    a[by0 + 12:by0 + 15, int(cx) - 2:int(cx) + 2] = C('iron', 3)
    a[by0 + 15:sill - 4, int(cx) + 1] = C('sand_cool', 3)
    a[by0 + 15:sill - 4, int(cx) + 2] = C('sand_cool', 2)


def _mill_house(seed):
    """The mill's front from the house builder, with its upper storey's windows and the hoist door
    under the eaves, its beam out over the loading door. Returns (codes, foot x, foot y, info)."""
    if seed in _MILL:
        a, ax, ay, info = _MILL[seed]
        return a.copy(), ax, ay, info
    built = Hs.building(dict(MILL_SPEC), seed=seed + 6)              # the slates' draw: no flat run on the roof
    p, info = built.base, built.info
    a = p.a
    rng = np.random.default_rng(seed + 7)
    L, B = info['L'], info['B']
    q = Hs.q
    for wx in (44, 70, 94):                                            # the upper storey's windows
        Hs.window(a, L + q(wx), B - q(70), 12, 11, 'timber', rng, wall='stone', shutters=False)
    hx = L + q(18)
    _hoist_door(a, hx, B - q(44), q(18), q(24), seed)
    # the doors' broad boards carry their grain (a sibling timber in short runs down each board)
    Yd, Xd = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    for (dcx, dB, dw, dh) in ((L + q(18), B, 22, 32),):
        dm = (np.abs(Xd + 0.5 - dcx) < q(dw) / 2 - 1) & (Yd < dB - 2) & (Yd >= dB - q(dh)) & (a >= 0)
        dm &= np.isin(a // 8, [FI_['timber'], FI_['timber_warm'], FI_['timber_cool']])
        _break_flats(a, dm, seed + 3, size=5, jitter=True)
    _MILL[seed] = (a.copy(), p.ax, p.ay, info)
    return a, p.ax, p.ay, info


def _wheel_frame(i, seed=141):
    """The water mill's south front (see _mill_house) with its undershot wheel on the water side: an
    oak wheel 132 art px across of two shrouds, 24 floats spanning them and 8 spokes on an iron hub,
    its bottom driven east by the race, turning an eighth of a spoke's pitch a frame so the cycle
    wraps evenly. The race is the zone's own water (round 4 of the detail audit, R4-5): below the
    wall's foot the sprite is see-through but for the wheel, cut where its lower floats dip into the
    race (R4-8), and the waterline broken float by float with white water at their entry and a lit
    wake downstream (R5-4). Every part of the wheel is closed in its own dark edge."""
    house, hx, hy, info = _mill_house(seed)
    Hh, W = house.shape
    pad = 24
    H = Hh + pad
    a = np.full((H, W), -1, np.int32)
    a[:Hh] = house
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = hx, hy                                                    # the foot: the wall's foot
    R = MILL_WHEEL_R
    D = 12.0
    wl = oy + MILL_DIP                                                 # the race's surface at the wheel
    cx = info['R'] - Hs.q(5) - R
    cy = wl + 9 - R                                                    # the lower floats dip about 9 texels
    ang0 = -(2 * math.pi / 8) * (i / float(LOOP))
    shape = a.shape
    wheel = np.full(shape, -1, np.int32)
    X_, Y_ = Xg + 0.5, Yg + 0.5

    def shroud(dy, t_lit, t_dark):
        rr = np.hypot(X_ - cx, Y_ - (cy + dy))
        m = (rr <= R) & (rr > R - 5.0)
        upw = -((X_ - cx) + (Y_ - cy - dy)) / max(1e-6, R * 1.41)
        tt = np.where(upw > 0.3, t_lit, np.where(upw < -0.3, t_dark, (t_lit + t_dark) / 2.0))
        tt = np.where(rr > R - 1.5, tt + 0.6, tt)
        tt = np.where(rr <= R - 3.5, tt - 0.6, tt)
        rpaint(wheel, m, B.OAK, tt, 0.3)
    shroud(-D, 3.0, 2.0)
    NF = 24
    for k in range(NF):
        th = ang0 + k * 2 * math.pi / NF
        c, s_ = math.cos(th), math.sin(th)
        tx, ty = -s_, c
        r0, r1 = R - 9.0, R + 6.0
        f0 = (cx + r0 * c, cy + r0 * s_)
        f1 = (cx + r1 * c, cy + r1 * s_)
        face = _poly(shape, [f0, f1, (f1[0], f1[1] - D), (f0[0], f0[1] - D)])
        lit_f = (-tx - ty) > 0.2
        ffr = np.clip((Y_ - (min(f0[1], f1[1]) - D)) / (D + abs(f0[1] - f1[1]) + 1e-6), 0, 1)   # back to front
        rpaint(wheel, face, B.OAK, (2.4 if lit_f else 1.2) + 1.2 * ffr, 0.6)
        p0 = (f0[0] - 2.5 * tx, f0[1] - 2.5 * ty)
        p1 = (f1[0] - 2.5 * tx, f1[1] - 2.5 * ty)
        p2 = (f1[0] + 2.5 * tx, f1[1] + 2.5 * ty)
        p3 = (f0[0] + 2.5 * tx, f0[1] + 2.5 * ty)
        board = _poly(shape, [p0, p1, p2, p3])
        lit = (s_ < 0.3) and (c < 0.6)
        rpaint(wheel, board, B.OAK, 3.8 if lit else (2.8 if s_ < 0.3 else 2.0), 0.2 + 0.3 * (k % 2))
        wheel[_line(shape, p2[0], p2[1], p3[0], p3[1], 1.0) & board] = C('timber_cool', 1)
        wheel[_line(shape, p0[0], p0[1], p1[0], p1[1], 1.0) & board] = C('timber_warm', 4) if lit else C('timber', 3)
    shroud(0, 4.0, 1.8)
    for k in range(8):
        th = ang0 + k * 2 * math.pi / 8 + math.pi / 24
        c, s_ = math.cos(th), math.sin(th)
        nx_, ny_ = -s_, c
        along = (X_ - cx) * c + (Y_ - cy) * s_
        across = (X_ - cx) * nx_ + (Y_ - cy) * ny_
        sp = (along > 5.0) & (along < R - 4.0) & (np.abs(across) < 2.3)
        sgn = np.sign(-(nx_ + ny_) + 1e-6)
        tt = np.where(across * sgn > 0.8, 3.8, np.where(across * sgn < -0.8, 1.6, 2.8))
        rpaint(wheel, sp, B.OAK, tt, 0.4)
    hub = _disc(shape, cx, cy, 6.0)
    rpaint(wheel, hub, IRON, np.where((X_ < cx) & (Y_ < cy), 3.8, np.where((X_ > cx + 0.5) & (Y_ > cy + 0.5), 1.4, 2.4)), 0.3)
    wheel[_disc(shape, cx, cy, 2.0)] = C('void', 2)
    for bx_, by_ in ((-3, -3), (3, 3), (3, -3), (-3, 3)):
        wheel[int(cy + by_), int(cx + bx_)] = C('slate', 4)                # the hub's bolts
    # the waterline broken float by float (R5-4): each float's tip cuts it, the dark band under the
    # cut stepping a row or two from float to float
    half = math.sqrt(max(0.0, R * R - (wl - cy) ** 2)) + 6
    seg = np.floor((Xg + 0.5 - (cx - half)) / 9.0).astype(int)
    wly = wl + (K.vhash(seg, 0, seed + i) > 0.5).astype(int) + (K.vhash(seg, 1, seed + i) > 0.8).astype(int)
    sel = (wheel >= 0) & (Yg < wly)
    a[sel] = wheel[sel]
    # every part closed in the wheel's own dark edge against the rubble (its inner edges too)
    ring = ndi.binary_dilation(sel) & ~sel & (Yg < wly) & (a >= 0) & (Yg < oy)
    a[ring] = C('timber_cool', 0)
    span = np.abs(Xg + 0.5 - cx) < half
    band = span & (Yg >= wly) & (Yg < wly + 2)
    a[band] = C('water_cool', 1)
    # white water where the floats bite in (west), in clumps of 2 to 3 texels, and a lit wake east
    xin = cx - half + 6
    for k in range(5):
        x = xin + k * 4 + (k + i) % 3
        yy = wl - 1 + ((k + i) % 2)
        a[_disc(a.shape, x, yy, 1.6, 1.1)] = C('snow', 4) if (k + i) % 3 == 0 else C('snow_cool', 3)
        a[_disc(a.shape, x + 1, yy + 2, 1.3, 0.7) & (Yg >= wl)] = C('water_warm', 4)
    xout = cx + half - 6
    for k in range(6):
        x = xout - 10 + k * 5 + (k + i) % 2
        yy = wl + 1 + (k % 2)
        a[yy, int(x):int(x) + 2 + k % 2] = C('water_warm', 5) if k < 3 else C('water_warm', 4)
    keep_w = (Yg >= oy) & (a >= 0)
    _finish(a, keep=keep_w)
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
        sc.box(x0, -12, 0, x0 + 10, 2, 32, GRANITE, base=2.5, k=1.8, tag='pier', round_=1.5, mix=hsh(seed, x0))
    sc.box(-15, -7, 5, 15, -4, 30, OAK, base=2.3, k=1.5, tag='gate', mix=0.3)
    sc.box(-25, -10, 32, 25, -2, 36, OAK, base=2.6, k=1.5, tag='beam', round_=1.0, mix=0.5, tex='wood')
    sc.box(-1, -6.5, 36, 1, -4.5, 46, IRON, base=2.2, k=1.4, tag='rack')
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    gxs = (Xg - sc.ox).astype(float)
    side = sc.n[..., 2] < 0.5
    pier = _tagm(sc, 'pier')
    _stone_parts(a, pier & side, gxs + 100, sc.depth, seed, GRANITE, 2.9 - 0.9 * (sc.depth < 8), lo=7, hi=11, course=7, moss=6.0)
    rpaint(a, pier & ~side, GRANITE, 3.8 + 0.3 * sc.light(), 0.3)
    beam = _tagm(sc, 'beam')
    _planks(a, beam & side, OAK, 2.7, gxs + 200, -sc.depth + 100, seed + 2, pitch=4)
    rpaint(a, beam & ~side, OAK, 3.8, 0.3)
    gate = _tagm(sc, 'gate')
    _planks(a, gate, OAK, 2.6 - 0.8 * ((Yg - sc.oy) > -14), Xg + 200, Yg + 300, seed, pitch=4, grain=0.05)
    slime = gate & ((Yg - sc.oy) > -12) & (K.vhash(Xg // 3, Yg // 2, seed + 9) > 0.7)
    a[slime] = C('leaf_cool', 2)
    a[gate & (((Xg - sc.ox) % 10) == 0)] = C('iron', 1)                    # the straps
    # the cast-iron gear on the rack's head, seen from the south: a web in iron 2, a rim 2 texels wide
    # lit on its upper-west arc, ten teeth each lit on its west face, a lit hub with a dark axle; the
    # rack bar it drives runs down past it
    hx, hy = sc.ox + 5, sc.oy - 4 - 44
    gt = np.full((H, W), 2.0)
    rr = np.hypot(Xg + 0.5 - hx, Yg + 0.5 - hy)
    ang = np.arctan2(Yg + 0.5 - hy, Xg + 0.5 - hx)
    web = rr <= 4.6
    rimm = (rr <= 6.2) & (rr > 4.6)
    tooth = (rr > 6.2) & (rr <= 8.0) & (np.mod(ang * 10 / (2 * math.pi) + 0.25, 1.0) < 0.5)
    gear = web | rimm | tooth
    upw = np.cos(ang + 2.36)                                           # 1 on the upper-west arc
    gt = np.where(rimm, np.where(upw > 0.3, 4.6, np.where(upw < -0.4, 1.4, 3.0)), gt)
    tw = np.mod(ang * 10 / (2 * math.pi) + 0.25, 1.0) < 0.22
    gt = np.where(tooth, np.where(tw, 4.2, 2.6) - 1.0 * (upw < -0.4), gt)
    rpaint(a, gear & ~web, [('void', 'iron', 'slate'), ('soot', 'iron', 'slate_warm')], gt, 0.3)
    rpaint(a, web, [('void', 'iron', 'slate')], np.where(np.mod(ang * 4 / (2 * math.pi), 1.0) < 0.2, 3.0, 1.8), 0.0)   # the web's ribs
    hub = rr <= 2.0
    a[hub] = C('slate', 4)
    a[hub & (Xg + 0.5 > hx) & (Yg + 0.5 > hy)] = C('iron', 2)
    a[(np.abs(Xg + 0.5 - hx) < 0.6) & (np.abs(Yg + 0.5 - hy) < 0.6)] = C('void', 0)
    rk = (Xg >= hx - 9) & (Xg < hx - 7) & (Yg >= hy - 4) & (Yg < sc.oy - 36)   # the rack bar, toothed on its east face
    a[rk] = np.where(Xg[rk] == hx - 9, C('iron', 3), C('iron', 1))
    a[rk & ((Yg % 3) == 0) & (Xg == hx - 8)] = C('iron', 3)
    # the water leaves under the gate as a jet (round 3 of the detail audit, R3-9), with no straight
    # border anywhere: a dark band under the gate's lip, a glassy tongue narrowing for 4 rows, white
    # water in a few uneven clumps (each with its grey-blue shaded underside) spreading downstream,
    # then the jet merging into the leat's own water over about 10 rows, streaks lying with the flow,
    # its edge ragged so the leat carries on under it
    cx_ = sc.ox
    r_ = (Yg - (sc.oy - 6)).astype(float)
    wob = np.array([1.6 * math.sin(y * 0.9 + 1.3) + 1.2 * (hsh(seed, y, 41) - 0.5) for y in range(H)])[:, None]
    half = np.where(r_ < 2, 14.0, np.where(r_ < 6, 14.0 - (r_ - 1) * 1.3, 9.0 + (r_ - 6) * 0.55)) + wob * (r_ >= 4)
    endr = 15 + (4 * K.vhash(Xg // 3, 0, seed + 42)).astype(int) - (np.abs(Xg + 0.5 - cx_) > 10) * 3
    water = (np.abs(Xg + 0.5 - cx_) < half) & (r_ >= 0) & (r_ < endr) & ~_tagm(sc, 'pier', 'gate')
    wt = np.full((H, W), 2.4)
    wt = np.where(r_ < 2, 1.0, wt)                                       # under the gate's lip
    wt = np.where((r_ >= 2) & (r_ < 6), np.where(np.abs(Xg + 0.5 - cx_) < half - 3, 4.4, 3.4), wt)   # the glassy tongue
    wt = np.where((r_ >= 6) & (r_ < 9), 3.0, wt)
    # streaks with the flow: short lit runs down the leat over their shadow, a few
    lane = np.floor((Xg + 0.5 - cx_) / 3.0)
    streak = (r_ >= 8) & (lane % 2 == 0) & (np.mod(Yg + 3 * lane, 7) < 3) & (K.vhash(lane, Yg // 7, seed + 43) > 0.45)
    wt = np.where(streak, 3.2, wt)
    und = np.zeros_like(streak)
    und[1:] = streak[:-1]
    wt = np.where(und & ~streak & (r_ >= 8), 1.8, wt)
    rpaint(a, water, [('water_cool', 'water', 'water_warm')], wt, np.where(r_ < 9, 0.0, 0.5))
    foam = np.zeros((H, W), bool)
    for k, (fxo, fyo, frx, fry) in enumerate(((-7, 3.5, 2.6, 1.3), (2, 4.5, 2.2, 1.1), (6.5, 3.2, 1.6, 1.0), (-2, 7.0, 1.4, 0.9),
                                               (5, 8.5, 1.2, 0.8), (-6, 9.5, 1.0, 0.7))):
        fx = cx_ + fxo + 1.5 * (hsh(seed, k, 1) - 0.5)
        fy = sc.oy - 6 + fyo
        clump = _disc(a.shape, fx, fy, frx, fry) & water
        under = _disc(a.shape, fx + 0.6, fy + 1.1, frx * 0.9, fry * 0.8) & water & ~clump
        a[under] = C('water_cool', 3)                                     # its shaded underside, grey-blue
        a[clump] = C('snow', 4)
        a[clump & (Yg + 0.5 > fy)] = C('snow_cool', 3)
        foam |= clump | under
    painted = a >= 0
    _finish(a, keep=foam)
    # water meeting the leat is never outlined (eastward-edges.md 4.1): its ragged edge stays open
    a[(a >= 0) & ~painted & ndi.binary_dilation(water) & (r_ >= 2)] = -1
    return K.crop(a, sc.ox, sc.oy)


SACK = [('earth_cool', 'sand_cool', 'sand'), ('earth_cool', 'sand_cool', 'sand_warm')]


def _dressing(px, py, harps=9, pitch=4.4, R=26.0):
    """A millstone's dressing on its face (px, py from its centre, unsquashed), as a miller cuts it
    (round 3 of the detail audit, R3-8): `harps` harps round the eye, each a master furrow running
    from near the eye to the rim with three parallel furrows beside it, each starting further out
    (falling length), so the face reads as fans of parallels, not radial spokes; every furrow 2
    texels wide with a lit lip on its trailing side. Returns (furrow, lip)."""
    th = np.arctan2(py, px) + math.pi
    rho = np.hypot(px, py)
    sec = 2 * math.pi / harps
    j = np.floor(th / sec)
    lead = j * sec
    d = rho * np.sin(th - lead)                                            # across the harp, from its master line
    al = rho * np.cos(th - lead)                                           # along it
    f = np.zeros(np.shape(px), bool)
    lip = np.zeros(np.shape(px), bool)
    for k in range(4):
        start = 6.0 + 5.5 * k
        on = (al > start) & (rho < R - 3.5)
        f |= on & (d >= k * pitch) & (d < k * pitch + 2.0)
        lip |= on & (d >= k * pitch + 2.0) & (d < k * pitch + 3.0)
    return f, lip & ~f


def millstones(seed=145):
    """Spare millstones in the miller's yard, 1.2 m across: one lying flat and one on edge leaning on a
    post, a sack of meal against it. Each stone carries its thickness as a band lit at the upper left
    and dark at the lower right, a bevel round its face lit on the north-west arc, its eye with the far
    wall lit and the near wall dark, and its dressing: eight harps of furrows, each a dark line with a
    lit lip on its south side."""
    sc = K.Scene(-64, 66, -26, 18, 70)
    sc.box(52, -6, 0, 56, -2, 40, OAK, base=2.3, k=1.4, tag='post', mix=0.3)
    sc.ellipsoid(44, 6, 7, 8.5, 6, 8, SACK, base=2.6, k=1.5, tag='sack', mix=0.2)
    sc.ellipsoid(44, 5, 15.5, 3.2, 2.6, 3.2, SACK, base=2.6, k=1.5, tag='neck', mix=0.2)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    post = _tagm(sc, 'post')
    gx = Xg - ox
    rpaint(a, post & (sc.n[..., 2] < 0.5), OAK, np.where(gx < 53, 3.4, np.where(gx > 54, 1.8, 2.6)), 0.3)
    sack = _tagm(sc, 'sack', 'neck')
    st = 2.6 + 1.4 * sc.light()
    crease = _line(a.shape, ox + 39, oy - 12, ox + 42, oy - 2, 1.0) | _line(a.shape, ox + 47, oy - 11, ox + 49, oy - 4, 1.0)
    st = np.where(crease, st - 1.0, st)
    rpaint(a, sack, SACK, st, 0.3)
    nk = _tagm(sc, 'neck')
    nys = np.nonzero(nk)[0]
    a[nk & (Yg == nys.max())] = C('timber_cool', 2)                      # the tie
    R = 26.0
    # the stone on edge, leaning on the post: its face, the thickness band along its top
    cx, cy = ox + 22, oy - 1 - 26
    face = _disc(a.shape, cx, cy, R)
    band = _disc(a.shape, cx + 5.5, cy - 1, R) & ~face                      # its thickness, 5 to 6 texels on the east
    bth = np.arctan2(Yg + 0.5 - cy, Xg + 0.5 - cx)
    rpaint(a, band, GRANITE, np.where(bth < -1.3, 3.6, np.where(bth < -0.5, 2.4, np.where(bth < 0.9, 1.6, 1.0))), 0.3)
    px, py = Xg - cx + 0.5, Yg - cy + 0.5
    rho = np.hypot(px, py)
    ft = 3.0 + 1.0 * ((px + py) < -14) - 0.6 * ((px + py) > 16)             # a tone lighter at its upper left
    edge = rho > R - 1.2
    bev = (rho > R - 3.2) & ~edge
    ft = np.where(edge, np.where((px + py) < 0, 4.6, 1.2), np.where(bev, np.where((px + py) < 0, 3.8, 2.0), ft))
    f, lip = _dressing(px, py)
    peck = (K.vhash(Xg // 4, Yg // 3, seed + 31) > 0.86) & (K.vhash(Xg // 2, Yg, seed + 32) > 0.5) & ~f & ~lip   # pecks in clusters
    inner = ~edge & ~bev
    ft = np.where(f & inner, 1.6, np.where(lip & inner, 3.8, np.where(peck & inner, ft - 1.0, ft)))
    rpaint(a, face, GRANITE, ft, 0.4)
    eye = _disc(a.shape, cx, cy, 4.2, 3.0)
    a[eye] = C('stone_cool', 1)                                              # the far inner wall a tone up (R4-12)
    a[eye & (py < -0.8)] = C('void', 0)                                      # the upper inner wall dark under the lip
    a[eye & (py > 0.8)] = C('stone', 3)                                      # the lower inner wall catching the light
    a[eye & (py > 1.8)] = C('stone_warm', 4)
    # the stone lying flat: a lathe of 10 texels, its face seen squashed (0.55)
    sq = 0.55
    fx, fy = ox - 30, oy - 13
    prof = [R] * 10
    m, hh, u, top = _lathe(a.shape, fx, fy, prof, sq)
    t = _cyl_tone(u, 1.0, lit=4.6, body=2.8, shade=1.2)
    t = np.where(u > 0.75, 1.0, t)
    qx, qy = Xg - fx + 0.5, (Yg - (fy - 9) + 0.5) / sq
    qr = np.hypot(qx, qy)
    tf = 3.0 + 1.0 * ((qx + qy) < -14) - 0.5 * ((qx + qy) > 16)
    rim = qr > R - 1.4
    bev = (qr > R - 3.4) & ~rim
    tf = np.where(rim, np.where((qx + qy) < 0, 4.6, 2.0), np.where(bev, np.where((qx + qy) < 0, 4.0, 2.2), tf))
    f2, lip2 = _dressing(qx, qy)
    peck2 = (K.vhash(Xg // 4, Yg // 3, seed + 33) > 0.86) & (K.vhash(Xg // 2, Yg, seed + 34) > 0.5) & ~f2 & ~lip2
    in2 = ~rim & ~bev
    tf = np.where(f2 & in2, 1.6, np.where(lip2 & in2, 3.8, np.where(peck2 & in2, tf - 1.0, tf)))
    t = np.where(top, tf, t)
    rpaint(a, m, GRANITE, t, 0.4)
    _break_flats(a, m & ~top, seed + 5, size=5)                          # pick marks on its rim, as sibling clusters
    eye2 = m & top & (np.hypot(qx / 4.2, qy / 4.6) < 1.0)
    a[eye2] = C('stone_cool', 1)
    a[eye2 & (qy < -0.8)] = C('stone', 3)                                    # the north inner wall, lit
    a[eye2 & (qy < -2.6)] = C('stone_warm', 4)
    a[eye2 & (qy > 2.4)] = C('void', 0)
    under_ = np.zeros_like(m)
    under_[1:] = m[:-1]
    under2 = np.zeros_like(m)
    under2[2:] = m[:-2]
    lyst = (under_ | under2) & ~m & (a < 0) & (Xg > fx - R + 2)               # its contact shadow on the yard
    a[m & ~top & (K.vhash(Xg // 3, 0, seed) > 0.8) & (hh < 2)] = C('leaf_cool', 2)  # moss at its foot
    flour = (a < 0) & (Yg > oy - 4) & (Yg < oy + 4) & (np.abs(Xg - ox - 44) < 10) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.55)
    _finish(a)
    a[lyst & (a < 0)] = C('slate_cool', 1)
    a[flour & (a < 0)] = C('plaster', 4)
    B._ground_tufts(a, ox, oy, [-58, -54, 60, 63], seed)
    return K.crop(a, ox, oy)


BIRCH_ROWS = [('snow', 3), ('snow', 4), ('snow', 4), ('snow_cool', 3), ('snow_cool', 3), ('snow', 2), ('ash', 4), ('ash', 4),
              ('ash', 3), ('ash', 2)]


def _birch_log(a, x0, x1, ytop, seed, stubs=()):
    """A fallen birch lying along x, 10 texels across, shaded as a cylinder top to bottom in five
    steps with no hard drop (Eastward's fallen trunk in shadows/g2018_002); its lit band broken along
    its length (round 3 of the detail audit, R3-7): the top row lit only in glints of 2 to 6 texels
    over about a third of the log, the next rows in patches of 6 to 12 among the bark's siblings, an
    older grey-pink patch by the sawn end, lichen and moss in the lower third; capped at 233 L, so it
    is never the brightest thing in its scene. Lenticels as bark-dark dashes of 2 to 5 texels at
    uneven spacing, some in pairs; near-black only in two scars; a papery curl or two lifting off the
    top; a strip of bark peeled to its warm underlayer; the west end sawn (an ellipse of pale wood
    with two rings and a dark rim), the east end snapped (pale splinters over a darker heart); branch
    stubs angled up and back, 3 texels thick, lit west. ytop is the trunk's top row. Returns its mask."""
    H, W = a.shape
    n = len(BIRCH_ROWS)
    m = np.zeros((H, W), bool)
    m[ytop:ytop + n, x0:x1] = True
    for j, (f, t) in enumerate(BIRCH_ROWS):
        a[ytop + j, x0:x1] = C(f, t)
    # the lit band broken along the length: glints on the top row, sibling patches below it
    x = x0
    while x < x1:
        ln = 2 + int(5 * hsh(seed, x, 91))
        if hsh(seed, x, 92) < 0.4:
            a[ytop, x:min(x1, x + ln)] = C('snow', 4)
        x += ln + 2 + int(6 * hsh(seed, x, 93))
    for j in (1, 2, 3):
        x = x0 + int(4 * hsh(seed, j, 94))
        while x < x1:
            ln = 6 + int(7 * hsh(seed, x, j, 95))
            pick = hsh(seed, x, j, 96)
            if j < 3:
                c = C('snow', 4) if pick < 0.35 else (C('snow', 3) if pick < 0.7 else C('snow_cool', 3))
            else:
                c = C('snow_cool', 3) if pick < 0.6 else C('snow', 2)
            a[ytop + j, x:min(x1, x + ln)] = c
            x += ln
    # an older grey-pink patch of bark by the sawn end
    for j in range(1, 6):
        xa = x0 + 2 + int(2 * hsh(seed, j, 97))
        a[ytop + j, xa:xa + 7 - abs(j - 3)] = C('stone_warm', 5) if j < 4 else C('stone', 4)
    # lenticels: bark-dark dashes, 2 to 5 long, uneven, some in pairs
    for j in range(1, 9):
        x = x0 + 4 + int(6 * hsh(seed, j, 98))
        while x < x1 - 4:
            ln = 2 + int(4 * hsh(seed, x, j, 99))
            if hsh(seed, x, j, 100) > 0.45:
                c = C('stone', 1) if j <= 5 else C('ash', 2)                 # bark-dark, 75 and 88 L (R4-12)
                a[ytop + j, x:min(x1 - 2, x + ln)] = c
                if hsh(seed, x, j, 101) > 0.6 and x + ln + 3 < x1 - 2:          # its pair
                    a[ytop + j, x + ln + 1:x + ln + 3] = c
            x += ln + 5 + int(9 * hsh(seed, x, j, 102))
    for k in range(2):                                                   # two black scars, small diamonds
        sx = int(x0 + 12 + (x1 - x0 - 24) * (k + 0.4 * hsh(seed, k, 1)))
        sy = ytop + 3 + int(3 * hsh(seed, k, 2))
        for dy, (dx0, dx1) in ((-1, (1, 2)), (0, (0, 3)), (1, (1, 2))):
            a[sy + dy, sx + dx0:sx + dx1 + 1] = C('void', 1)
    # lichen and moss in clusters along the lower third
    for k in range(5):
        lx = int(x0 + 6 + (x1 - x0 - 12) * hsh(seed, k, 103))
        ly = ytop + 6 + int(2 * hsh(seed, k, 104))
        w_ = 2 + int(3 * hsh(seed, k, 105))
        a[ly, lx:lx + w_] = C('grass', 3)
        a[ly + 1, lx + 1:lx + w_ + 1] = C('grass_cool', 2)
    # one or two papery curls lifting off the top: a lit strip over its dark underside
    for k in range(2):
        cx_ = int(x0 + 14 + (x1 - x0 - 28) * (0.15 + 0.6 * k + 0.2 * hsh(seed, k, 106)))
        a[ytop - 1, cx_:cx_ + 3] = C('snow', 4)
        a[ytop, cx_:cx_ + 3] = C('ash', 2)
        a[ytop, cx_ - 1] = C('snow_cool', 3)
        m[ytop - 1, cx_:cx_ + 3] = True
    px0 = int(x0 + (x1 - x0) * 0.58)
    a[ytop + 2:ytop + 4, px0:px0 + 6] = C('sand_warm', 4)              # bark peeled to the warm underlayer
    a[ytop + 4, px0 + 1:px0 + 6] = C('sand_warm', 3)
    # the sawn west end: an ellipse of pale wood, two rings, a dark rim, a dark heart
    cy = ytop + n / 2.0
    Yg, Xg = np.mgrid[0:H, 0:W]
    e = (((Xg + 0.5 - (x0 - 0.5)) / 2.6) ** 2 + ((Yg + 0.5 - cy) / 5.0) ** 2) <= 1.0
    rr = np.hypot((Xg + 0.5 - (x0 - 0.5)) / 2.6, (Yg + 0.5 - cy) / 5.0)
    a[e] = C('sand', 4)
    a[e & (rr > 0.45) & (rr < 0.62)] = C('sand_cool', 3)
    a[e & (rr > 0.85)] = C('timber', 2)
    a[e & (rr < 0.2)] = C('timber', 3)
    # the snapped east end: splinters of pale wood over a darker heart
    heart = (Xg >= x1) & (Xg < x1 + 2) & (Yg >= ytop + 2) & (Yg < ytop + n - 2)
    a[heart] = C('timber', 2)
    for k, (dy, ln) in enumerate(((1, 4), (3, 2), (5, 5), (7, 3))):
        y = ytop + dy
        a[y:y + 2, x1:x1 + ln] = C('sand', 4) if k % 2 == 0 else C('sand_cool', 3)
        a[y + 1, x1:x1 + ln - 1] = C('sand_cool', 2)
        m[y:y + 2, x1:x1 + ln] = True
    m |= e | heart
    for sx in stubs:                                                    # branch stubs, up and back, 3 thick
        for j in range(4):
            xx = sx - j // 2
            yy = ytop - 1 - j
            a[yy, xx] = C('snow', 4)
            a[yy, xx + 1] = C('snow_cool', 3)
            a[yy, xx + 2] = C('ash', 3)
            m[yy, xx:xx + 3] = True
        a[ytop - 5, sx - 2:sx + 1] = C('sand', 4)                     # its broken tip, pale
        m[ytop - 5, sx - 2:sx + 1] = True
    return m


def _soil_masses(a, m, light, seed, sx=16, sy=8, rx=(7, 10), ry=(3.6, 5.2), sets=None, rng=None):
    """Loose earth as lumps: each a soft mass lit as a sphere inside the spill's own band (its upper
    west a tone up, its lower east a tone down) with a dark underside over the lump below; drawn from
    the front row back. The band shows between them."""
    H, W = a.shape
    rng = rng or np.random.default_rng(seed)
    sets = sets or EARTH
    ys, xs = np.nonzero(m)
    band = _tone(a).astype(float)
    lumps = []
    for j in range(int(ys.min()) + 2, int(ys.max()), sy):
        off = ((j // sy) % 2) * (sx * 0.5)
        for i0 in range(int(xs.min()) - sx, int(xs.max()) + sx, sx):
            cx, cy = i0 + off + rng.uniform(-4, 4), j + rng.uniform(-2, 2)
            iy, ix = int(round(cy)), int(round(cx))
            if 0 <= iy < H and 0 <= ix < W and m[iy, ix] and rng.random() > 0.2:
                lumps.append((cx, cy, rng.uniform(*rx), rng.uniform(*ry), int(rng.integers(0, len(sets))), int(rng.integers(0, 999))))
    for (cx, cy, rx_, ry_, f, sd) in sorted(lumps, key=lambda c: -c[1]):
        b = float(band[int(round(cy)), int(round(cx))])
        sub, pts, u, v = _blob(a.shape, cx, cy, rx_, ry_, sd, lobes=5, wob=0.16)
        pts &= m[sub]
        if pts.sum() < 6:
            continue
        dn = np.zeros_like(pts)
        dn[:-1] = pts[1:]
        lv = _sphere_light(u, v)
        t = np.full(pts.shape, b)
        t = np.where(lv > 0.66, b + 1.0, t)
        t = np.where(lv < -0.05, b - 1.0, t)
        t = np.where(pts & ~dn & (v > 0), b - 1.0, t)
        _paint_codes(a[sub], pts, sets[f], np.clip(t, 0, 4))


# Where the slip leaves its bank (round 4 of the detail audit, R4-1): the bank's rim stands SLIP_RIM
# texels above the slip's foot; the slip tears a notch back into it SLIP_NOTCH[0] texels either side of
# its axis and SLIP_NOTCH[1] deep, whose scar shows the bank's low face (SLIP_FACE tall). The study
# (and a zone) cuts that notch into the bank; the sprite starts its earth at the scar's foot.
SLIP_RIM = 48
SLIP_NOTCH = (30, 10)
SLIP_FACE = 14


def landslip(seed=147):
    """The Millrace landslip (way W3), 3 m across: the low bank torn open behind the road (the notch
    and its raw scar are the bank's, cut where the slip lies: SLIP_NOTCH); from the scar's foot the
    spill comes down across the road as a tongue of loose earth in lumps (each lit on its upper west,
    dark under), its toe dark and wet; torn sods at the notch's two shoulders only; slumped clods of
    turf riding on the spill, grass on their tops and raw earth on their sides; boulders seated in the
    spill, each carried in planes with its contact shadow; a birch snapped and lying across, a
    cylinder of bark with its lenticels and black scars, its east end splintered, two branch stubs,
    its sawn west end and a dark underside."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-72, 72, -50, 24, 70)
    sc.ellipsoid(0, -38, 0, 25, 7, 3.5, EARTH, base=2.6, k=1.4, tag='earth', mix=0.3, flat=1.3)   # the throat, out of the scar
    sc.ellipsoid(0, -14, 0, 58, 20, 10, EARTH, base=2.6, k=1.6, tag='earth', mix=0.3, flat=1.3)
    sc.ellipsoid(-34, 6, 0, 28, 12, 6, EARTH, base=2.5, k=1.6, tag='earth', mix=0.6, flat=1.3)
    sc.ellipsoid(32, 8, 0, 26, 11, 5, EARTH, base=2.5, k=1.6, tag='earth', mix=0.5, flat=1.3)
    # (R5-10) the toe broken into uneven tongues of different lengths, thin where they run out
    for (tx, ty, trx, try_, tz) in ((-14, 17, 9, 6, 1.6), (12, 19, 6, 6, 1.2), (44, 15, 8, 5, 1.4), (-52, 12, 7, 4, 1.2), (26, 18, 4, 4, 1.0)):
        sc.ellipsoid(tx, ty, 0, trx, try_, tz, EARTH, base=2.4, k=1.4, tag='earth', mix=0.5, flat=1.2)
    clods = [(-40, -12, 6, 9, 5, 9), (26, -18, 8, 8, 5, 9), (44, -4, 3, 7, 4, 8), (-14, 4, 3, 6, 4, 7)]
    for k, (x, y, zb, w, d, h) in enumerate(clods):
        sc.ellipsoid(x, y, zb + h * 0.5, w, d, h * 0.62, EARTH, base=2.6, k=1.4, tag='clod%d' % k, mix=0.4, flat=1.7)
    boulders = [(-52, -2, 4, 8.0), (8, -24, 9, 9.0), (50, 10, 2, 6.5), (-6, 12, 2, 3.4), (30, -6, 8, 3.0), (-30, -22, 9, 3.6), (16, 14, 1, 2.8)]
    for k, (x, y, zb, r) in enumerate(boulders):
        sc.ellipsoid(x, y, zb + r * 0.5, r, r * 0.75, r * 0.7, GRANITE, base=2.7, k=1.4, tag='stone%d' % k, mix=0.3, flat=2.2)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    L = sc.light()
    z = sc.depth
    # the spill: bands by the light, the wet toe, then lumps of loose earth over it
    earth = _tagm(sc, 'earth')
    Ls = ndi.gaussian_filter(L, 2.0)
    et = np.where(Ls > 0.32, 3.6, np.where(Ls > -0.05, 2.8, 2.0))
    et = np.where(z < 3.0, 1.2 + 0.9 * (Ls > 0.0) + 0.5 * (K.vhash(Xg // 4, Yg // 2, seed + 7) > 0.7), et)
    rpaint(a, earth, EARTH, et, _sibling_mix(a.shape, Xg, Yg, seed, 6.0, (4, 3)))
    _soil_masses(a, earth & (z >= 3.0), Ls, seed, rng=rng)
    wet = earth & (z < 2.0)
    rpaint(a, wet, EARTH, np.where(Ls > 0.0, 2.0, 1.0), 0.6)            # the toe dark and wet
    wys, wxs = np.nonzero(wet & (Ls > 0.0))
    if len(wys):
        k = len(wys) // 3
        a[wys[k], wxs[k]:wxs[k] + 2] = C('water_warm', 4)                 # one glint pair in the wet
        a[wys[k] + 1, wxs[k] + 1:wxs[k] + 3] = C('water', 3)
    # the clods: turf on their tops (a lit front lip, blades over it), raw earth on their sides
    for k in range(len(clods)):
        cm = _tagm(sc, 'clod%d' % k)
        ct = cm & (sc.n[..., 2] > 0.5) & (sc.gy < np.array([clods[k][1]]) + 2)
        cs = cm & ~ct
        ctb = np.where(L > 0.3, 3.0, 2.0)
        rpaint(a, ct, BARROW_TURF, ctb, 0.3 + 0.2 * (k % 2))
        if ct.sum() > 20:
            _turf_clumps(a, ct, ctb, seed + 9 + k, sx=8, sy=4, rx=(3.4, 4.6), ry=(2.2, 3.0), flowers=False, rng=np.random.default_rng(seed + 9 + k))
        rpaint(a, cs, EARTH, np.where(sc.n[..., 0] > 0.4, 2.0, np.where(sc.n[..., 0] < -0.4, 3.2, 2.7)) - 0.8 * (z < 1.5 + clods[k][2]), 0.4)
        cdn = np.zeros_like(cm)
        cdn[:-1] = cm[1:]
        a[np.roll(cm & ~cdn, 1, 0) & ~cm & (a >= 0)] = C('earth_cool', 0)   # its contact line
        dn = np.zeros_like(ct)
        dn[:-1] = ct[1:]
        lip = ct & ~dn
        a[lip] = C('grass', 4)
        up_ = np.zeros_like(cs)
        up_[1:] = lip[:-1]
        a[cs & up_] = C('leaf_cool', 2)
        topr = ct & ~np.roll(ct, 1, 0)
        for y, x in zip(*np.nonzero(topr)):
            if hsh(seed, x, k) > 0.55 and y - 2 >= 0 and a[y - 1, x] < 0:
                a[y - 2:y, x] = C('grass', 3)
                a[y - 2, x] = C('grass', 4)
    # the boulders, seated: planes, marks, a contact shadow on the earth east and under each
    for k in range(len(boulders)):
        bm = _tagm(sc, 'stone%d' % k)
        tp, _w, _f, _e = _set_stone(sc, a, bm, seed + 80 + k)
        if boulders[k][3] > 5:
            _stone_marks(a, bm, tp, seed + 80 + k)
        sh = np.zeros_like(bm)
        for d in ((1, 0), (2, 1), (1, 1), (1, 2)):
            sh |= np.roll(np.roll(bm, d[0], 0), d[1], 1)
        V._step(a, sh & ~bm & (earth | _tagm(sc, *['clod%d' % j for j in range(len(clods))])), -1)
    # torn sods at the notch's two shoulders: turf on top, lit at the west, raw earth under
    for sx, w_ in ((-SLIP_NOTCH[0] + 3, 7), (SLIP_NOTCH[0] - 9, 6)):
        x0 = ox + sx
        y0 = oy - SLIP_RIM + 1
        for dx in range(w_):
            hgt = 2 + (1 if 1 <= dx < w_ - 1 else 0)
            for j in range(hgt):
                y = y0 + j
                a[y, x0 + dx] = (C('grass', 4) if dx < w_ // 2 else C('grass', 3)) if j == 0 else (
                    C('grass_cool', 2) if j == 1 else C('earth', 2))
            a[y0 + hgt, x0 + dx] = C('earth_cool', 1)
    _finish(a)
    # the birch: the trunk across the spill, its contact shadow on the earth under it
    lx0, lx1, ly = ox - 44, ox + 20, oy - 23
    lsh = np.zeros((H, W), bool)
    lsh[ly + 10:ly + 12, lx0 + 1:lx1 + 3] = True
    V._step(a, lsh & (a >= 0), -2)
    log = _birch_log(a, lx0, lx1, ly, seed, stubs=(ox - 28, ox - 4))
    a[ly + 10, lx0:lx1] = C('ash', 1)                                   # its outline under, the foot of the cylinder
    a[ly - 1, lx0:lx1][a[ly - 1, lx0:lx1] != C('snow', 4)] = C('snow_cool', 1)   # and over it, broken by the light
    # (R5-10) the outline opened where the earth thins into the grass: along the toe's south edge, in
    # runs of 3 to 6, the edge texel goes and the earth's last row thins to a scatter
    sol = a >= 0
    bot = sol & ~np.roll(sol, -1, 0) & (Yg > oy - 4)
    for y, x in zip(*np.nonzero(bot)):
        if hsh(seed, x // 4, 61) > 0.45 and a[y, x] % 8 == 6:
            a[y, x] = -1
            if y - 1 >= 0 and a[y - 1, x] >= 0 and hsh(seed, x, 62) > 0.5:
                a[y - 1, x] = C('earth', 2)
    # clods and pebbles rolled 2 to 6 texels past the edge onto the lawn, each lit on top, dark under
    for k in range(7):
        bx = ox - 56 + int(112 * hsh(seed, k, 63))
        col = np.nonzero(a[:, bx] >= 0)[0]
        if not len(col):
            continue
        by = int(col.max()) + 2 + int(4 * hsh(seed, k, 64))
        if by + 1 < H and bx + 2 < W:
            big = hsh(seed, k, 65) > 0.6
            a[by, bx:bx + 2 + big] = C('earth', 3) if k % 3 else C('stone', 3)
            a[by + 1, bx:bx + 2 + big] = C('earth_cool', 1) if k % 3 else C('stone_cool', 1)
    B._ground_tufts(a, ox, oy, [-64, -58, 58, 64], seed)
    return K.crop(a, ox, oy)


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
def _turf_masses(a, m, light, seed, cell=(11, 8)):
    """Turf in masses, as Eastward draws a grassy bank: rounded clumps a cell across, each lit along its
    upper-west rim, a dark line where it tucks under the clump below it; the clumps step with the
    light (a lit clump on the lit side, a shaded one in shade), never a uniform mottle."""
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    cw, ch = cell
    gi, gj = Xg // cw, Yg // ch
    best = np.full((H, W), 1e9)
    lab = np.zeros((H, W), np.int64)
    rx = np.zeros((H, W))
    ry = np.zeros((H, W))
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = gi + di, gj + dj
            cx = ci * cw + K.vhash(ci, cj, seed) * cw + (cj % 2) * cw * 0.5
            cy = cj * ch + K.vhash(ci, cj, seed + 1) * ch
            d = ((Xg - cx) / cw) ** 2 + ((Yg - cy) / ch) ** 2
            better = d < best
            best = np.where(better, d, best)
            lab = np.where(better, ci * 7919 + cj, lab)
            rx = np.where(better, (Xg - cx) / cw, rx)
            ry = np.where(better, (Yg - cy) / ch, ry)
    t = _tone(a).astype(float)
    t = np.where((rx + ry < -0.35) & (light > -0.3), t + 1.0, t)
    dn = np.zeros_like(lab)
    dn[:-1] = lab[1:]
    edge = (dn != lab) & m
    t = np.where(edge & (ry > 0), t - 1.0, t)
    rpaint(a, m, [('leaf_cool', 'grass_cool', 'grass'), ('leaf_cool', 'grass', 'grass'), ('leaf_cool', 'grass_cool', 'grass_cool')], t,
           np.clip(K.vhash(lab, 0, seed + 2) * 0.999, 0, 0.999))


def _turf_tufts(a, m, light, seed, density=0.05, drift_sigma=7.0, rng=None):
    """Grass on a turf surface as Eastward draws it: tufts of three to five blades in clumps, denser in
    drifts and sparse between (never an even wallpaper), each blade's tip lit on the lit side and its
    foot in shade, a shadow texel under the clump."""
    H, W = a.shape
    rng = rng or np.random.default_rng(seed)
    drift = K.noise((H, W), rng, drift_sigma)
    Yg, Xg = np.mgrid[0:H, 0:W]
    pick = m & (drift > 0.5) & (K.vhash(Xg, Yg, seed + 41) < density * (drift - 0.5) * 4.0)
    ys, xs = np.nonzero(pick)
    for y, x in zip(ys, xs):
        n = 3 + int(3 * hsh(x, y, seed))
        lit = light[y, x] > 0.2
        for k in range(n):
            bx = x + k - n // 2
            h = 2 + int(2 * hsh(bx, y, seed + 1))
            if k in (0, n - 1):
                h -= 1
            for j in range(h):
                yy = y - j
                if 0 <= yy < H and 0 <= bx < W and m[yy, bx]:
                    if j == h - 1:
                        a[yy, bx] = C('grass', 5) if lit else C('grass_cool', 3)
                    else:
                        a[yy, bx] = C('grass', 3) if lit else C('leaf_cool', 2)
        if y + 1 < H:
            for k in range(n):
                bx = x + k - n // 2
                if 0 <= bx < W and m[y + 1, bx]:
                    a[y + 1, bx] = C('leaf_cool', 2) if lit else C('leaf_cool', 1)




BARROW_TURF = [('leaf_cool', 'grass_cool', 'grass'), ('leaf_cool', 'grass', 'grass'), ('leaf_cool', 'grass_cool', 'grass')]
# the barrow's own grass (round 4 of the detail audit, R4-2): at or under the lawn's lightness, its
# shade a tone down in grass (75 to 83 L), never near-black, tone 0 only in the masses' Us
MOUND_TURF = [('grass_cool', 'grass_cool', 'grass'), ('grass', 'grass', 'grass'), ('grass_cool', 'grass_cool', 'grass_cool')]


def _blob(shape, cx, cy, rx, ry, seed, lobes=6, wob=0.12, box=None):
    """A soft mass's mask: an ellipse whose rim swells in a few lobes (a run of bumps, never a
    perfect shape). Returns (sub-slice, mask, u, v) on the box round it."""
    H, W = shape
    y0, y1 = int(max(0, cy - ry * (1 + wob) - 1)), int(min(H, cy + ry * (1 + wob) + 2))
    x0, x1 = int(max(0, cx - rx * (1 + wob) - 1)), int(min(W, cx + rx * (1 + wob) + 2))
    Ys, Xs = np.mgrid[y0:y1, x0:x1] + 0.5
    u, v = (Xs - cx) / rx, (Ys - cy) / ry
    ang = np.arctan2(v, u)
    rr = 1 + wob * np.sin(ang * lobes + seed * 1.7) * (0.6 + 0.4 * np.sin(ang * 3 + seed))
    return (slice(y0, y1), slice(x0, x1)), (u * u + v * v) <= rr * rr, u, v


def _sphere_light(u, v):
    """The house light on a sphere's face at (u, v) (-1..1 across and down): its terminator curves
    round the form, never a straight diagonal."""
    nz = np.sqrt(np.clip(1.0 - u * u - v * v, 0, 1))
    n = np.sqrt(u * u + v * v + nz * nz) + 1e-9
    return (-0.55 * u - 0.6 * v + 0.58 * nz) / n


def _paint_codes(tgt, pts, rp, t):
    tt = np.clip(np.round(t), 0, 5).astype(int)
    fam = np.where(tt >= 4, FI_[rp[2]], np.where(tt <= 1, FI_[rp[0]], FI_[rp[1]]))
    tgt[pts] = (fam * 8 + tt)[pts]


def _turf_clumps(a, m, band, seed, sx=30, sy=15, rx=(16, 22), ry=(9, 12), flowers=True, over=None, rng=None, sets=None):
    """Turf as the house foliage recipe draws a crown (house-style.md 5, foliage; style_sheet.leafy),
    at a grassy bank's scale, as Eastward draws the grass grown over its rocks in 17: soft masses of
    grass a cell or so across, each lit as a sphere inside the dome's own band (its upper west a tone
    up, its lower east a tone down) with a dark U along its underside where it hangs over the mass
    below; on each mass's lit half, a few small clumps a tone above it with a lit cap and a dark U.
    Drawn from the front row back, so each mass's underside lies over the top of the one below.
    `band` gives each texel the dome's band (1 to 4); `over` (a mask beside m) lets masses on the
    top edge rise past the silhouette, so the outline is a run of bumps."""
    H, W = a.shape
    rng = rng or np.random.default_rng(seed)
    sets = sets or BARROW_TURF
    ys, xs = np.nonzero(m)
    allow = m | (over if over is not None else np.zeros_like(m))
    bnd = band.copy()
    if over is not None and over.any():
        idx = ndi.distance_transform_edt(~m, return_distances=False, return_indices=True)
        bnd = np.where(over, bnd[idx[0], idx[1]], bnd)
    masses = []
    for j in range(int(ys.min()) + 4, int(ys.max()) + 2, sy):
        off = ((j // sy) % 2) * (sx * 0.5)
        for i0 in range(int(xs.min()) - sx, int(xs.max()) + sx, sx):
            cx = i0 + off + rng.uniform(-6, 6)
            cy = j + rng.uniform(-3, 3)
            iy, ix = int(round(cy)), int(round(cx))
            if 0 <= iy < H and 0 <= ix < W and m[iy, ix]:
                masses.append((cx, cy, rng.uniform(*rx), rng.uniform(*ry), int(rng.integers(0, len(sets))), int(rng.integers(0, 999))))
    for (cx, cy, rx_, ry_, f, sd) in sorted(masses, key=lambda c: -c[1]):
        b = float(bnd[int(round(cy)), int(round(cx))])
        sub, pts, u, v = _blob(a.shape, cx, cy, rx_, ry_, sd, lobes=7, wob=0.14)
        pts &= allow[sub]
        if not pts.any():
            continue
        dn = np.zeros_like(pts)
        dn[:-1] = pts[1:]
        dn2 = np.zeros_like(pts)
        dn2[:-2] = pts[2:]
        lv = _sphere_light(u, v)
        t = np.full(pts.shape, b)
        t = np.where(lv > (0.86 if b >= 4 else 0.66), b + 1.0, t)
        t = np.where(lv < -0.05, b - 1.0, t)
        t = np.where(pts & ~dn & (v > 0) & (u > -0.35), b - 1.0, t)       # the U, deepest east; open at its west
        t = np.clip(t, 1, 5)
        rp = sets[f]
        _paint_codes(a[sub], pts, rp, t)
        # the small clumps on the lit half
        for k in range(int(3 + 4 * (b >= 3))):
            ccx = cx + rx_ * rng.uniform(-0.8, 0.5)
            ccy = cy + ry_ * rng.uniform(-0.8, 0.3)
            s2, p2, u2, v2 = _blob(a.shape, ccx, ccy, rng.uniform(3.2, 4.4), rng.uniform(2.2, 3.0), sd + k, lobes=4, wob=0.1)
            ii, jj = int(round(ccy)), int(round(ccx))
            if not (0 <= ii < H and 0 <= jj < W):
                continue
            # only where it lies on this mass and on its lit side
            here = np.zeros((H, W), bool)
            here[sub] = pts
            p2 &= here[s2]
            lvc = _sphere_light((ccx - cx) / rx_, (ccy - cy) / ry_)
            if p2.sum() < 12 or lvc < 0.45:
                continue
            tb = float(np.clip(_tone(a)[ii, jj], 1, 4))
            dn_ = np.zeros_like(p2)
            dn_[:-1] = p2[1:]
            up_ = np.zeros_like(p2)
            up_[1:] = p2[:-1]
            lf_ = np.zeros_like(p2)
            lf_[:, 1:] = p2[:, :-1]
            t2 = np.full(p2.shape, min(5.0, tb + 1.0) if tb < 4 else 4.0)
            capm = p2 & (~up_ | ~lf_) & (u2 < 0.2)
            t2 = np.where(capm, min(5.0, tb + 2.0) if tb >= 3 else tb + 1.0, t2)
            t2 = np.where(p2 & ~dn_ & (v2 > 0), tb - 1.0, t2)
            _paint_codes(a[s2], p2, sets[(f + k) % len(sets)], t2)
            if flowers and tb >= 4 and hsh(seed, int(ccx), int(ccy)) < 0.12:
                cy_, cx_ = np.nonzero(capm)
                if len(cy_):
                    yy, xx = cy_[len(cy_) // 2] + s2[0].start, cx_[len(cx_) // 2] + s2[1].start
                    if 1 <= yy < H and xx + 1 < W and m[yy - 1, xx] and m[yy - 1, xx + 1]:
                        a[yy - 1, xx:xx + 2] = C('brass', 4) if hsh(seed, int(ccx)) < 0.6 else C('snow_warm', 4)
    return a


def _break_flats(a, m, seed, size=6, jitter=False):
    """No area of one colour larger than about size x size: where a window that size inside m is all
    one code, a 2 x 2 cluster at its middle swaps to a sibling ramp at the same tone (shape without
    value noise, house-style.md 4). With `jitter` the cluster falls anywhere in the window and takes
    a shape of its own (2 to 4 x 1 to 3), so the swaps never line up in a lattice."""
    H, W = a.shape
    for _ in range(3):
        same = np.ones((H - size + 1, W - size + 1), bool)
        ref = a[:H - size + 1, :W - size + 1]
        for dy in range(size):
            for dx in range(size):
                win = a[dy:dy + H - size + 1, dx:dx + W - size + 1]
                same &= (win == ref) & m[dy:dy + H - size + 1, dx:dx + W - size + 1]
        ys, xs = np.nonzero(same)
        if not len(ys):
            return
        done = np.zeros((H, W), bool)
        for y, x in zip(ys, xs):
            cy, cx = y + size // 2 - 1, x + size // 2 - 1
            h_ = 2
            if jitter:
                cy, cx = y + int(hsh(seed, x, y, 1) * (size - 2)), x + int(hsh(seed, x, y, 2) * (size - 3))
                h_ = 1 + int(hsh(seed, x, y, 3) * 3)
            if done[cy, cx]:
                continue
            c = a[cy, cx]
            fam, t = SIB.get(int(c) // 8), int(c) % 8
            if fam is None:
                continue
            w_ = 2 + int(hsh(seed, cx, cy) > 0.5) + (int(hsh(seed, cx, cy, 4) > 0.6) if jitter else 0)
            sl = (slice(cy, cy + h_), slice(cx, cx + w_))
            a[sl][m[sl] & ((a[sl] == c) | (not jitter))] = FI_[fam] * 8 + t
            done[max(0, cy - size // 2):cy + size, max(0, cx - size // 2):cx + size] = True


SIB = {FI_[a]: b for a, b in (('grass', 'grass_cool'), ('grass_cool', 'grass'), ('leaf_cool', 'leaf'), ('leaf', 'leaf_cool'),
                              ('stone', 'stone_warm'), ('stone_warm', 'stone'), ('stone_cool', 'stone'), ('earth', 'earth_warm'),
                              ('earth_cool', 'earth'), ('earth_warm', 'earth'), ('snow', 'snow_cool'), ('snow_cool', 'snow'),
                              ('timber', 'timber_warm'), ('timber_warm', 'timber'), ('timber_cool', 'timber'),
                              ('slate', 'slate_warm'), ('slate_warm', 'slate'), ('slate_cool', 'slate'), ('iron', 'slate_cool'),
                              ('brass', 'brass_warm'), ('brass_warm', 'brass'), ('sand', 'sand_warm'), ('sand_cool', 'sand'),
                              ('ashlar', 'ashlar_warm'), ('ashlar_warm', 'ashlar'), ('plaster', 'plaster_warm'),
                              ('plaster_warm', 'plaster'), ('clay', 'clay_cool'), ('clay_cool', 'clay'), ('water', 'water_warm'),
                              ('water_cool', 'water'), ('water_warm', 'water'))}


def _turf_bank(a, m, band, light, seed, over=None, rng=None, n=14, sets=None, extra=(), covered=None, u_drop=2, u_rows=2):
    """A grassy bank as Eastward draws the grass over its rocks in 17 (round 3 of the detail audit,
    R3-1): 8 to 14 soft masses of mixed size, out of rows, overlapping, each with the full value
    structure: a lit cap (grass 4 to 5) on its upper-west third, the body, its lower half a tone down
    and a dark U two texels thick along its whole lower edge where it overhangs the mass below; its top
    bumpy in steps of 2 to 3 texels. Texture only from small clumps of 2 to 4 texels placed by noise,
    dense on the crown's lit half and sparse in the east and the lower flanks, never in a lattice: a
    tone up with a lit top on the lit side, a tone down in the shade. No area of one colour is larger
    than about 6 x 6."""
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    rng = rng or np.random.default_rng(seed)
    sets = sets or BARROW_TURF
    allow = m | (over if over is not None else np.zeros_like(m))
    bnd = band.copy()
    if over is not None and over.any():
        idx = ndi.distance_transform_edt(~m, return_distances=False, return_indices=True)
        bnd = np.where(over, bnd[idx[0], idx[1]], bnd)
    # the masses: spread out of rows (sampled with a minimum spacing), mixed sizes
    ys, xs = np.nonzero(m)
    masses = []
    tries = 0
    while len(masses) < n and tries < 6000:
        tries += 1
        k = int(rng.integers(0, len(ys)))
        cx, cy = float(xs[k]), float(ys[k])
        rx = float(rng.uniform(18, 42))
        if any(math.hypot(cx - q[0], (cy - q[1]) * 1.8) < 0.6 * (rx + q[2]) for q in masses):
            continue
        masses.append((cx, cy, rx, rx * float(rng.uniform(0.48, 0.62)), int(rng.integers(0, len(sets))), int(rng.integers(0, 999))))
    masses += [(cx, cy, rx, ry, int(rng.integers(0, len(sets))), int(rng.integers(0, 999))) for (cx, cy, rx, ry) in extra]
    for (cx, cy, rx_, ry_, f, sd) in sorted(masses, key=lambda c: -c[1]):
        b = float(np.clip(bnd[int(round(cy)), int(round(cx))], 2, 4))
        sub, pts, u, v = _blob(a.shape, cx, cy, rx_, ry_, sd, lobes=int(6 + sd % 5), wob=0.16)
        pts &= allow[sub]
        if not pts.any():
            continue
        dn = np.zeros_like(pts)
        dn[:-1] = pts[1:]
        dn2 = np.zeros_like(pts)
        dn2[:-2] = pts[2:]
        lv = _sphere_light(u, v)
        t = np.full(pts.shape, b)
        t = np.where((lv > (0.8 if b >= 4 else 0.45)) & (v < 0.15), b + 1.0, t)   # the lit cap, upper west
        t = np.where((lv < 0.05) & (v > 0.15), b - 1.0, t)                  # the lower half turning away
        dn3 = np.zeros_like(pts)
        dn3[:-3] = pts[3:]
        edge2 = pts & (~dn | ~dn2 | ((~dn3) if u_rows >= 3 else False)) & (v > 0.05)
        t = np.where(edge2 & (u > -0.25), b - u_drop, np.where(edge2, b - 1.0, t))   # the dark U, u_rows texels
        _paint_codes(a[sub], pts, sets[f], np.clip(t, 0, 5))
        if covered is not None:
            covered[sub] |= pts
    # the texture: clumps of 2 to 4 texels, placed by noise at a density that follows the light
    dens = K.noise((H, W), rng, 5.0)
    lit = np.clip(light, -1, 1)
    p_keep = np.clip(0.2 + 0.5 * np.clip(lit, 0, 1) + 0.25 * (dens - 0.5), 0.08, 0.7)
    tq = _tone(a)
    cand = allow & (a >= 0) & (K.vhash(Xg, Yg, seed + 61) < p_keep * 0.45)
    for y, x in zip(*np.nonzero(cand)):
        w_ = 2 + int(hsh(seed, x, y) * 3)                                    # 2 to 4 across, 2 high
        t0 = int(tq[y, x])
        if lit[y, x] > 0.05 and t0 < 5 and not (t0 == 4 and lit[y, x] < 0.5 and hsh(seed, x, y, 9) < 0.5):
            t1 = t0 + 1
        elif t0 > 1 and lit[y, x] < -0.15:
            t1 = t0 - 1
        else:
            t1 = t0                                                          # a leaf cluster in a sibling green
        sel = np.zeros((2, w_), bool)
        sel[0, 1:] = True                                                    # a rounded top: the top row set in a texel
        sel[1, :] = True
        if w_ >= 4:
            sel[0, -1] = False
        ys_, xs_ = slice(y, y + 2), slice(x, x + w_)
        if y + 2 > H or x + w_ > W:
            continue
        sel &= allow[ys_, xs_] & (tq[ys_, xs_] == t0)
        rp = sets[int(hsh(seed, x // 7, y // 5) * len(sets)) % len(sets)]
        if t1 == t0:
            rp = ('leaf_cool', 'leaf', 'grass_cool') if hsh(seed, x, y, 3) < 0.5 else ('leaf_cool', 'grass_warm', 'grass_cool')
        _paint_codes(a[ys_, xs_], sel, rp, np.full(sel.shape, float(t1)))
        if t1 > t0 and y + 2 < H and x + w_ - 1 < W:                        # its dark underside, east
            fx0 = max(x, x + w_ - 2)
            selu = allow[y + 2, fx0:x + w_] & (tq[y + 2, fx0:x + w_] == t0)
            _paint_codes(a[y + 2:y + 3, fx0:x + w_], selu[None, :], rp, np.full((1, x + w_ - fx0), float(max(1, t0 - 1))))
    # a sibling green at the same tone in irregular patches (a noise field, never a lattice)
    pn = K.noise((H, W), np.random.default_rng(seed + 77), 1.3)
    sw = allow & (a >= 0) & (pn > 0.6)
    fam = a // 8
    for f0, f1 in SIB.items():
        mm = sw & (fam == f0)
        a[mm] = FI_[f1] * 8 + a[mm] % 8
    _break_flats(a, allow, seed, size=6, jitter=True)
    g5 = allow & ((a == C('grass', 5)) | (a == C('grass_warm', 5)) | (a == C('grass_warm', 4)))
    a[g5] = np.where(a[g5] == C('grass_warm', 4), C('grass', 4), C('grass_cool', 5))   # the brightest grass stays green, not straw
    return a


def _set_stone(sc, a, m, seed, sets=GRANITE):
    """A set stone in planes (art-style.md 5; Eastward's rocks in 17): its top plane lit (tone 4,
    a tone 5 arris along its front-west edge), the west face 3 to 4, the south face 3, the east
    face 2, the foot row 1; each plane one calm sibling, a crack with its lit lip, lichen in pale
    rosettes and a moss cap on the top's back edge."""
    n = sc.n
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    top = m & (n[..., 2] > 0.6)
    west = m & ~top & (n[..., 0] < -0.42)
    east = m & ~top & (n[..., 0] > 0.42)
    front = m & ~top & ~west & ~east
    k = int(hsh(seed, 1) * len(sets))
    k2 = (k + 1) % len(sets)
    ys_m = np.nonzero(m & ~top)[0]
    fdown = np.clip((Yg - (ys_m.min() if len(ys_m) else 0)) / max(1.0, float(np.ptp(ys_m)) if len(ys_m) else 1.0), 0, 1)
    rpaint(a, top, [sets[k]], 4.0, 0.0)
    rpaint(a, west, [sets[k2]], 3.4 - 0.6 * (fdown > 0.7), 0.0)
    COOL = ('slate_cool', 'stone_cool', 'stone')                      # the faces turned from the sky, cooler
    rpaint(a, front, [COOL], 2.9 - 0.8 * (fdown > 0.62), 0.0)
    rpaint(a, east, [COOL], 1.7 - 0.4 * (fdown > 0.7), 0.0)
    upm = np.zeros_like(m)
    upm[1:] = top[:-1]
    a[front & upm] = C('stone', 3)                                       # the arris's underside catches a little
    # grain: clusters of 2 or 3 texels swapped to a sibling at the same tone (shape, not value noise)
    gr = m & (K.vhash((Xg + (Yg // 2)) // 3, Yg // 2, seed + 13) > 0.72)
    tq = _tone(a)
    for fam_set in (GRANITE[0], GRANITE[1]):
        sel = gr & (K.vhash(Xg // 3, Yg // 2, seed + 14) > 0.5)
        rpaint(a, sel, [fam_set], tq, 0.0)
        gr &= ~sel
    rpaint(a, gr, [('slate_cool', 'stone_cool', 'stone_warm')], tq, 0.0)
    xf = np.nonzero(m)[1]
    if len(xf) and np.ptp(xf) >= 8:                                      # a rough-dressed facet turned away, lower east
        fx = (Xg - xf.min()) / max(1.0, float(np.ptp(xf)))
        fac = front & ~upm & (fx + 0.55 * fdown + 0.08 * np.sin(Yg * 1.3 + seed) > 1.0)
        V._step(a, fac, -1)
    _break_flats(a, m, seed + 3, size=5)
    dn = np.zeros_like(top)
    dn[:-1] = top[1:]
    arris = top & ~dn
    xs_ = np.nonzero(m)[1]
    if len(xs_):
        cxm = 0.5 * (xs_.min() + xs_.max())
        a[arris & (Xg < cxm + 2)] = C(sets[k][2], 5)
    dnm = np.zeros_like(m)
    dnm[:-1] = m[1:]
    a[m & ~dnm] = C(sets[k][0], 1)                                       # the foot
    up = np.zeros_like(m)
    up[1:] = m[:-1]
    foot2 = m & dnm & ~np.roll(dnm, -1, 0) & ~top
    V._step(a, foot2 & (Xg > (cxm if len(xs_) else 0)), -1)
    return top, west, front, east


def _stone_marks(a, m, top, seed):
    """A crack down the stone's face with its lit lip, two lichen rosettes, a moss cap on the back of
    its top."""
    ys, xs = np.nonzero(m)
    if len(ys) < 20:
        return
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    face = m & ~top
    fy = np.nonzero(face)[0]
    if len(fy) > 6:
        fy0 = fy.min()
        cx = int(x0 + (x1 - x0) * (0.35 + 0.3 * hsh(seed, 2)))
        crack = _line(a.shape, cx, fy0 + 1, cx + (2 if hsh(seed, 3) > 0.5 else -2), fy0 + min(9, (y1 - fy0) * 0.6), 1.0) & face
        a[crack] = C('stone_cool', 1)
        lip = np.zeros_like(crack)
        lip[:, :-1] = crack[:, 1:]
        a[lip & face & ~crack] = C('stone_warm', 4)
    for k in range(2):
        rx = int(x0 + 2 + (x1 - x0 - 4) * hsh(seed, k, 4))
        ry = int(y0 + 2 + (y1 - y0) * 0.5 * hsh(seed, k, 5))
        fam = 'grass_cool' if k == 0 else 'sand_cool'
        # a rosette: a 2 x 2 heart a tone up, lobes round it at the lichen's own tone
        for dx, dy, t in ((0, 0, 4), (1, 0, 4), (0, 1, 4), (1, 1, 3), (-1, 0, 3), (2, 1, 3), (1, -1, 3), (0, 2, 3)):
            if 0 <= ry + dy < a.shape[0] and 0 <= rx + dx < a.shape[1] and m[ry + dy, rx + dx]:
                a[ry + dy, rx + dx] = C(fam, t)
    ty = np.nonzero(top)[0]
    if len(ty):
        back = top & (np.arange(a.shape[0])[:, None] <= ty.min() + 1)
        bx = np.nonzero(back)[1]
        if len(bx):
            mx = int(bx.min() + (bx.max() - bx.min()) * hsh(seed, 7))
            mm = back & (np.abs(np.arange(a.shape[1])[None, :] - mx) < 3)
            a[mm] = C('leaf', 3)
            a[mm & (np.arange(a.shape[1])[None, :] < mx)] = C('grass', 4)
            mys = np.nonzero(mm)[0]
            if len(mys):                                                 # the cap's drip down the stone
                dy0 = mys.max() + 1
                for j, cc in ((0, C('leaf', 2)), (1, C('leaf', 2)), (2, C('leaf_cool', 2))):
                    if dy0 + j < a.shape[0] and m[dy0 + j, mx + 1]:
                        a[dy0 + j, mx + 1] = cc


def _seat_in_turf(a, m, seed, depth=3, shadow=4):
    """Seat a stone in the turf: grass grown over its foot in short blades (dark at the root, lit at
    the tip), and its contact shadow on the ground thrown east (grass two tones down)."""
    H, W = a.shape
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    for x in range(xs.min() - 1, xs.max() + shadow):
        col = np.nonzero(m[:, x])[0] if 0 <= x < W else []
        yb = col.max() if len(col) else ys.max()
        if len(col):
            for k in range(2):                                               # the contact line, the shadow's core
                if yb + 1 + k < H and a[yb + 1 + k, x] < 0:
                    a[yb + 1 + k, x] = C('leaf_cool', 1 if k == 0 else 2)
        elif x > xs.max():
            yb = ys.max() - (x - xs.max()) // 3
            for k in range(2):
                yy = ys.max() - 1 + k
                if 0 <= yy < H and a[yy, x] < 0 and x - xs.max() < shadow:
                    a[yy, x] = C('leaf_cool', 2)
    for x in range(xs.min(), xs.max() + 1):
        if hsh(seed, x, 11) < 0.45:
            continue
        col = np.nonzero(m[:, x])[0]
        if not len(col):
            continue
        yb = col.max()
        h = 2 + int(depth * hsh(seed, x, 12))
        lit = x < xs.min() + (xs.max() - xs.min()) * 0.6
        for j in range(h):
            yy = yb + 1 - j
            if 0 <= yy < H:
                a[yy, x] = C('grass', 4) if j == h - 1 and lit else (C('grass_cool', 3) if j >= h - 2 else C('leaf_cool', 2))




def barrow_entrance(seed=161):
    """Old Fang's barrow from the south: a long turf mound 7.4 m long and 2 m high, its dome lit in
    soft bands (the crown at the upper left, the body, the east and lower flanks) and covered in
    clumps of grass, each with a lit cap and a dark underside, its outline a run of bumps, a darker
    band at its foot where the clumps overhang; a few tufts and flowers, stones half sunk in it. Set
    into its front a portal Bramble can walk into (0.95 x 1.8 m): two jamb stones and a capstone
    lintel standing a little proud, each carried in planes, the lintel's top lit with a bright front
    arris and its shadow cast down the jambs and into the opening; the passage recedes in
    perspective, its west wall in shade, its east wall lit near the mouth, the drystone lining's
    courses running in, the floor falling away and the dark deepening to black at its end; a
    threshold slab; a forecourt of set stones curving away either side; a blocking stone rolled aside."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-178, 178, -96, 20, 108)                             # room round the dome's ends (R5-3)
    sc.ellipsoid(0, -46, 0, 160, 46, 96, BARROW_TURF, base=2.7, k=1.6, tag='mound', mix=0.3, flat=1.15)
    sc.box(-30, -9, 0, -21, 0, 80, GRIT, base=2.6, k=1.4, tag='jamb_w', round_=2.0, mix=0.3)
    sc.box(21, -9, 0, 30, 0, 80, GRIT, base=2.6, k=1.4, tag='jamb_e', round_=2.0, mix=0.6)
    sc.box(-36, -11, 80, 36, 2, 93, GRIT, base=2.8, k=1.4, tag='lintel', round_=3.0, mix=0.4)
    sc.box(-21, -9, 0, 21, 2, 2.5, GRIT, base=2.9, k=1.4, tag='sill', mix=0.5, round_=0.8)
    forecourt = []
    # the kerb ring: stones of three kinds (dressed slabs, low boulders, pillars), 30 to 50 % apart
    # in size, the spacing broken where a stone has gone
    angs = [0.32, 0.55, 0.71, 1.02, 1.2]
    for sgn in (-1, 1):
        for k, ang in enumerate(angs):
            if hsh(seed, k, sgn + 3) < 0.18:
                continue                                                 # a gap where one has gone
            x = sgn * (42 + 70 * math.sin(ang + 0.06 * (hsh(seed, k, sgn) - 0.5))) + rng.uniform(-3, 3)
            y = 2 - 20 * (1 - math.cos(ang))
            sz = 0.75 + 0.6 * hsh(seed, k, sgn + 7)
            kind = int(3 * hsh(seed, k, sgn + 11))
            forecourt.append((x, y))
            tag = 'set%d' % len(forecourt)
            if kind == 0:                                                # a dressed slab on edge
                sc.box(x - 6 * sz, y - 3, 0, x + 6 * sz, y + 3, 14 * sz, GRANITE, base=2.8, k=1.4, tag=tag, round_=1.4, mix=0.3)
            elif kind == 1:                                              # a low boulder
                sc.ellipsoid(x, y, 4 * sz, 9 * sz, 5.0, 7 * sz, GRANITE, base=2.8, k=1.4, tag=tag, mix=0.5, flat=2.3)
            else:                                                        # a pillar
                sc.ellipsoid(x, y, 7 * sz, 5.5 * sz, 4.0, 9 * sz, GRANITE, base=2.8, k=1.4, tag=tag, mix=0.4, flat=2.5)
    sc.ellipsoid(52, 14, 8, 10, 7, 9, GRIT, base=2.7, k=1.6, tag='block', mix=0.5, flat=2.0)
    sunk = [(-112, -16, 24, 8.0), (98, -12, 18, 7.0), (-62, -6, 10, 5.5)]
    for k, (x, y, zc, r) in enumerate(sunk):
        sc.ellipsoid(x, y, zc, r * 1.3, r, r, GRIT, base=2.7, k=1.4, tag='sunk%d' % k, mix=0.3, flat=2.0)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox
    z = sc.depth
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    # the turf: the dome in soft bands, a darker band at its foot, then the clumps over it
    mound = _tagm(sc, 'mound')
    Ls = ndi.gaussian_filter(L, 3.0)
    wob = (K.noise((H, W), rng, 6.0) - 0.5) * 0.35
    # at or under the lawn's lightness (R4-2): the lit crown and west in grass 3, the body and the
    # east in grass 2, the foot a tone down
    band = np.where(Ls + wob > 0.3, 3.0, 2.0)
    band = np.where(z < 4, 1.0, band)
    rpaint(a, mound, MOUND_TURF, band, _sibling_mix(a.shape, Xg, Yg, seed, 9.0, (6, 4)))
    above = np.zeros_like(mound)
    for d in range(1, 6):
        above[:-d] |= mound[d:]
    above &= (a < 0)
    stones = np.zeros_like(mound)
    for k in range(len(sunk)):
        stones |= _tagm(sc, 'sunk%d' % k)
    for k in range(len(sunk)):
        sm = _tagm(sc, 'sunk%d' % k)
        tp_ = _set_stone(sc, a, sm, seed + 70 + k)[0]
        _stone_marks(a, sm, tp_, seed + 70 + k)
    clump_m = mound & (z >= 3)
    # the silhouette is the masses' own bumps (R4-2): a band round the dome's top is kept only where a
    # mass covers it, and a row of smaller masses sits along the outline every 8 to 16 texels
    mys, mxs = np.nonzero(mound)
    mbot = mys.max()
    # the band is the dome's outer silhouette only, never the edge round the portal's stones (R5-2)
    portal = _tagm(sc, 'jamb_w', 'jamb_e', 'lintel', 'sill', 'block', *['set%d' % (k + 1) for k in range(len(forecourt))],
                   *['sunk%d' % k for k in range(len(sunk))])
    rimband = mound & ~ndi.binary_erosion(mound | portal, iterations=5) & (Yg < mbot - 14)
    edge_m = []
    x = int(mxs.min()) + 4
    while x < mxs.max() - 4:
        col = np.nonzero(mound[:, x])[0]
        if len(col):
            ry_ = 4.5 + 2.5 * hsh(seed, x, 51)
            lift = 2.5 if len(edge_m) % 2 else 0.0                        # bumps of 2 to 4 texels (R5-3)
            edge_m.append((float(x), float(col.min()) + ry_ * 0.25 - lift, 6.0 + 5.0 * hsh(seed, x, 52), ry_))
        x += 8 + int(9 * hsh(seed, x, 53))
    covered = np.zeros_like(mound)
    _turf_bank(a, clump_m & ~rimband, band, Ls + wob, seed, over=above | rimband, rng=rng, sets=MOUND_TURF,
               extra=edge_m, covered=covered, u_drop=1, u_rows=3)
    a[(rimband | above) & ~covered & ~stones] = -1
    # the stones half sunk: the turf grows over their lower part in a bumpy edge of small clumps,
    # each lit on its cap, with blades standing up against the stone
    for k, (x, y, zc, r) in enumerate(sunk):
        sm = _tagm(sc, 'sunk%d' % k)
        sys_, sxs_ = np.nonzero(sm)
        if not len(sys_):
            continue
        ycut = sys_.min() + (sys_.max() - sys_.min()) * 0.62
        for j, xx in enumerate(range(sxs_.min() - 2, sxs_.max() + 3, 4)):
            cy_ = ycut + 1.2 * math.sin(j * 1.7 + k)
            sub, pts, u_, v_ = _blob(a.shape, xx + 1.5, cy_ + 2.5, 3.2, 3.0, j + k, lobes=4)
            pts &= (sm | mound)[sub] & (Yg[sub] >= cy_ - 1)
            dn_ = np.zeros_like(pts)
            dn_[:-1] = pts[1:]
            up_ = np.zeros_like(pts)
            up_[1:] = pts[:-1]
            tq = np.where(~up_, 3.0, 2.0)
            tq = np.where(~up_ & (u_ < 0.2), 4.0, tq)
            tq = np.where(~dn_ & (v_ > 0.3), 1.0, tq)
            _paint_codes(a[sub], pts, BARROW_TURF[(j + k) % 3], tq)
        for xx in range(sxs_.min(), sxs_.max() + 1):
            if hsh(seed, xx, k) > 0.55:
                yy = int(ycut) - 1
                a[yy - 1:yy + 1, xx] = np.array([C('grass', 4), C('grass_cool', 3)]) if sm[yy, xx] else a[yy - 1:yy + 1, xx]
    # the foot: the lowest clumps overhang a dark band, blades hanging over the contact line
    footb = mound & (z < 4)
    a[footb] = np.where(K.vhash(Xg // 3, Yg // 2, seed + 4)[footb] > 0.6, C('leaf_cool', 1), C('grass_cool', 1))
    hang = mound & (z >= 4) & (z < 6) & (K.vhash(Xg // 2, 1, seed + 5) > 0.55)
    a[hang] = C('grass_cool', 2)
    # the stones: jambs, lintel, sill, the forecourt and the blocking stone, each in planes
    for tag in ['jamb_w', 'jamb_e', 'lintel', 'sill', 'block'] + ['set%d' % (k + 1) for k in range(len(forecourt))]:
        m = _tagm(sc, tag)
        if not m.any():
            continue
        tp, we, fr, ea = _set_stone(sc, a, m, seed + hash_tag(tag))
        if tag.startswith('set') or tag == 'block':
            _stone_marks(a, m, tp, seed + hash_tag(tag))
    # the orthostats' fronts: a lit west arris, the east margin turning away, a crack, lichen
    for tag in ('jamb_w', 'jamb_e'):
        m = _tagm(sc, tag) & side
        xs_ = np.nonzero(m)[1]
        x0, x1 = xs_.min(), xs_.max()
        a[m & (Xg <= x0 + 1)] = C('stone_warm', 4)
        a[m & (Xg == x0)] = C('ashlar_warm', 4)
        a[m & (Xg >= x1 - 1)] = C('stone_cool', 2)
        _stone_marks(a, _tagm(sc, tag), np.zeros_like(m), seed + hash_tag(tag))
    # the lintel: a capstone standing proud, its front arris bright, its shadow down the jambs
    lint = _tagm(sc, 'lintel')
    lf = lint & side
    lys = np.nonzero(lf)[0]
    lt0, lt1 = lys.min(), lys.max()
    a[lf & (Yg == lt0) & (gx < 26)] = C('ashlar_warm', 5)
    a[lf & (Yg == lt0 + 1) & (gx < 10)] = C('stone_warm', 4)
    a[lf & (Yg >= lt1 - 1)] = C('stone_cool', 1)
    crack = _line(a.shape, ox - 6, lt0 + 2, ox - 2, lt1 - 1, 1.0) & lf
    a[crack] = C('stone_cool', 1)
    a[np.roll(crack, 1, 1) & lf & ~crack] = C('stone_warm', 4)
    jambs = _tagm(sc, 'jamb_w', 'jamb_e') & side
    V._step(a, jambs & (Yg > lt1) & (Yg <= lt1 + 3) & (gx > -30 + (Yg - lt1)), -1)
    # the capstone's top: a drafted margin lit along its front, a long crack, the turf grown down
    # over its back edge in clumps that hang onto the stone
    ltop = lint & ~side
    lty0, lty1 = np.nonzero(ltop)[0].min(), np.nonzero(ltop)[0].max()
    facet = ltop & (Yg > lty0 + 4) & (gx > -8 + (Yg - lty0) * 1.5)
    V._step(a, facet, -1)
    tc = _line(a.shape, ox + 14, lty0 + 3, ox + 20, lty1 - 1, 1.0) & ltop
    a[tc] = C('stone_cool', 2)
    a[np.roll(tc, 1, 1) & ltop & ~tc] = C('stone_warm', 4)
    hang = np.zeros_like(ltop)
    for k, x in enumerate(range(ox - 36, ox + 37, 7)):
        sub, pts, u_, v_ = _blob(a.shape, x + 3.5 * hsh(seed, k), lty0 + 1.5, 5.0, 3.2 + 1.8 * hsh(seed, k, 1), k, lobes=4)
        hm = np.zeros_like(ltop)
        hm[sub] = pts
        hang |= hm & (ltop | ((a >= 0) & (Yg < lty0)))
    tb = np.where(Yg < lty0 + 1, 3.0, 3.0)
    rpaint(a, hang, BARROW_TURF, tb, 0.4)
    dnh = np.zeros_like(hang)
    dnh[:-1] = hang[1:]
    a[hang & ~dnh] = C('leaf_cool', 1)                                      # their dark U on the stone
    uph = np.zeros_like(hang)
    uph[1:] = hang[:-1]
    a[hang & ~uph & (gx < 20)] = C('grass', 4)
    # each orthostat rough-dressed: a broad facet in its lower east a tone down, its edge irregular
    for tag in ('jamb_w', 'jamb_e'):
        m = _tagm(sc, tag) & side
        xs_ = np.nonzero(m)[1]
        x0j = xs_.min()
        fac = m & ((Xg - x0j) * 6 + (Yg - lt1) * 0.35 + 3 * np.sin(Yg * 0.7) > 34) & (Xg < xs_.max() - 1)
        V._step(a, fac, -1)
    # the passage, in perspective: walls, ceiling and floor running in to a black end
    px0, px1 = ox - 21, ox + 21
    py0, py1 = lt1 + 1, oy - 3
    iw, ie, it, ib = 8, 6, 9, 9                                            # the inner frame's insets
    qx0, qx1, qy0, qy1 = px0 + iw, px1 - ie, py0 + it, py1 - ib
    pas = (Xg >= px0) & (Xg < px1) & (Yg >= py0) & (Yg < py1)
    wall_w = _poly(a.shape, [(px0, py0), (qx0, qy0), (qx0, qy1), (px0, py1)]) & pas
    wall_e = _poly(a.shape, [(px1, py0), (qx1, qy0), (qx1, qy1), (px1, py1)]) & pas
    ceil = _poly(a.shape, [(px0, py0), (px1, py0), (qx1, qy0), (qx0, qy0)]) & pas & ~wall_w & ~wall_e
    floor = _poly(a.shape, [(px0, py1), (px1, py1), (qx1, qy1), (qx0, qy1)]) & pas & ~wall_w & ~wall_e
    end = pas & ~wall_w & ~wall_e & ~ceil & ~floor
    fw = np.clip((Xg - px0) / float(iw), 0, 1)                            # 0 at the mouth, 1 at the inner frame
    fe = np.clip((px1 - 1 - Xg) / float(ie), 0, 1)
    rpaint(a, wall_w, [('void', 'soot', 'stone_cool')], 2.0 - 1.4 * fw, 0.0)
    rpaint(a, wall_e, [('soot', 'stone_cool', 'stone')], 3.4 - 2.4 * fe, 0.0)
    for f in (0.2, 0.42, 0.62, 0.8):                                     # the lining's courses running in
        yo = py0 + (py1 - py0) * f
        yi = qy0 + (qy1 - qy0) * f
        for (xa, xb, wm) in ((px0, qx0, wall_w), (px1 - 1, qx1, wall_e)):
            jl = _line(a.shape, xa, yo, xb, yi, 1.0) & wm
            V._step(a, jl, -1)
            ln = np.zeros_like(jl)
            ln[1:] = jl[:-1]
            if wm is wall_e:
                V._step(a, ln & wm & ~jl, 1)
    for (xa, wm) in ((px0 + 3, wall_w), (px1 - 3, wall_e)):              # a few upright joints
        for f in (0.1, 0.52, 0.71):
            yo = py0 + (py1 - py0) * f
            a[wm & (Xg == xa) & (Yg >= yo) & (Yg < yo + 5)] = C('void', 1)
    rpaint(a, ceil, [('void', 'void', 'soot')], 0.6 * (Yg - py0) / max(1, it), 0.0)
    rpaint(a, floor, [('void', 'soot', 'stone_cool')], 2.4 - 1.8 * np.clip((py1 - 1 - Yg) / float(ib), 0, 1), 0.0)
    pool = floor & (Yg >= py1 - 4) & (Xg > ox - 2) & (Xg < ox + 14)          # the daylight falling in on the floor
    V._step(a, pool, 1)
    dx = np.minimum(Xg - qx0, qx1 - 1 - Xg)
    dy = np.minimum(Yg - qy0, qy1 - 1 - Yg)
    rpaint(a, end, [('void', 'void', 'void')], np.clip(1.4 - np.minimum(dx, dy) / 2.0, 0, 1.4), 0.0)
    V._step(a, pas & (Yg < py0 + 3), -1)                                   # the lintel's shadow on the mouth
    sill = _tagm(sc, 'sill')
    a[sill & ~side] = C('stone', 4)
    a[sill & ~side & (Xg > ox + 12)] = C('stone', 3)
    _finish(a, keep=pas)
    # the silhouette broken by tufts of 1 to 3 texels every 6 to 12 along it, each standing out along
    # the outline's normal: a dark blade body, a lit tip on the crown's west
    stone_m = _tagm(sc, 'jamb_w', 'jamb_e', 'lintel', 'sill', 'block', *['set%d' % (k + 1) for k in range(len(forecourt))])
    solid = a >= 0
    rim = solid & ~ndi.binary_erosion(solid) & ndi.binary_dilation(mound, iterations=2) & ~ndi.binary_dilation(stone_m, iterations=3)
    mys, mxs = np.nonzero(mound)
    mcx, mcy = mxs.mean(), mys.max()
    ry_, rx_ = np.nonzero(rim)
    keep_ = ry_ < mcy - 12
    ry_, rx_ = ry_[keep_], rx_[keep_]
    ang_ = np.arctan2(ry_ - mcy, rx_ - mcx)
    order = np.argsort(ang_)
    acc, nxt = 0.0, 4
    prev = None
    for idx_ in order:
        y, x = int(ry_[idx_]), int(rx_[idx_])
        if prev is not None:
            acc += math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
        if acc < nxt:
            continue
        acc, nxt = 0.0, 8 + int(hsh(seed, x, y) * 9)
        nx_, ny_ = x - mcx, (y - mcy) * 2.2
        nl = math.hypot(nx_, ny_) + 1e-6
        nx_, ny_ = nx_ / nl, ny_ / nl
        litc = (nx_ + ny_) < 0.2
        # a tuft 2 to 3 texels: grass 3 to 4 on the lit west and top, grass 1 to 2 on the east (R4-2)
        hgt = 2 + int(hsh(seed, x, 31) > 0.5)
        for bx, hb in ((0, hgt), (-1, hgt - 1), (1, hgt - 1), (2, 1 if hsh(seed, x, 33) > 0.5 else 0)):
            for k in range(1, hb + 1):
                yy = int(round(y + ny_ * k - 0.4 * k))
                xx = int(round(x + nx_ * k)) + bx
                if 0 <= yy < H and 0 <= xx < W and a[yy, xx] < 0:
                    a[yy, xx] = (C('grass', 4) if k == hb else C('grass', 3)) if litc else (C('grass_cool', 2) if k == hb else C('grass', 1))
    mcols = np.nonzero(mound.any(0))[0]
    # the foot: a two-row contact shade where the dome meets the lawn, not a ruled line
    for x in mcols:
        ys_ = np.nonzero(mound[:, x])[0]
        yb = int(ys_.max())
        if stone_m[yb - 3:yb + 4, max(0, x - 1):x + 2].any():
            continue
        for k in (1, 2):
            if yb + k < H and (a[yb + k, x] < 0 or a[yb + k, x] % 8 == 6):
                a[yb + k, x] = C('grass', 1)
        if hsh(seed, x, 41) < 0.3 and yb + 3 < H and a[yb + 3, x] < 0:
            a[yb + 3, x] = C('grass', 1)
    B._ground_tufts(a, ox, oy, [-150, -141, -120, -95, 95, 118, 140, 151], seed)
    for tag in ['block'] + ['set%d' % (k + 1) for k in range(len(forecourt))]:
        _seat_in_turf(a, _tagm(sc, tag), seed + hash_tag(tag), depth=2, shadow=3)
    return K.crop(a, ox, oy)


def hash_tag(tag):
    return sum(ord(c) * (k + 1) for k, c in enumerate(tag)) % 997


def _boulder_planes(sc, a, m, seed, sets=GRIT):
    """A set stone carried in planes (art-style.md rule 5): its top-left plane lit, the front at mid
    tone, the east flank dark; a calm sibling drift, no pits."""
    n = sc.n
    t = np.where(n[..., 2] > 0.55, 4.0, np.where(n[..., 0] > 0.35, 1.8, np.where(n[..., 0] < -0.35, 3.4, 2.8)))
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    rpaint(a, m, sets, t, _sibling_mix(a.shape, Xg, Yg, seed, 4.0, (3, 3)))


def _rosette(a, m, x, y, fam=('brass', 4)):
    """A lichen rosette 3 texels across, on the stone only: a 2 x 2 heart, its rim a tone down."""
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (2, 1)):
        if 0 <= y + dy < a.shape[0] and 0 <= x + dx < a.shape[1] and m[y + dy, x + dx]:
            a[y + dy, x + dx] = C(fam[0], fam[1] - (1 if dx in (-1, 2) else 0))


def kerb_stone(variant='a', seed=163):
    """A kerb stone of the barrow's ring, seated in the turf: (a) a dressed slab set on edge, its
    arrises worn round and one top corner broken off; (b) an undressed boulder set low and long;
    (c) a tall rough pillar leaning a little. Each is carried in planes (its top plane lit with a
    bright front-west arris, the west face lit, the south face mid, the east face dark, a dark foot
    row), with a crack and its lit lip, pale lichen, a moss cap on the back of its top, grass grown
    over its foot and its contact shadow thrown east on the turf."""
    sc = K.Scene(-20, 20, -10, 10, 30)
    vs = seed + ord(variant)
    if variant == 'a':
        sc.box(-8, -4, 0, 8, 4, 17, GRANITE, base=2.8, k=1.4, tag='stone', round_=1.6, mix=0.3)
    elif variant == 'b':
        sc.ellipsoid(0, 0, 4, 9.5, 6.0, 9.0, GRANITE, base=2.8, k=1.4, tag='stone', mix=0.6, flat=2.4)   # low and long, within the class (R3-13)
        sc.ellipsoid(-3, -1, 7, 6.0, 5.0, 7.0, GRANITE, base=2.8, k=1.4, tag='stone', mix=0.6, flat=2.2)
    else:
        sc.ellipsoid(0, 0, 8.5, 7.2, 4.6, 11.5, GRANITE, base=2.8, k=1.4, tag='stone', mix=0.3, flat=2.6)
        sc.ellipsoid(1.5, 0, 15.5, 5.5, 4.0, 5.5, GRANITE, base=2.8, k=1.4, tag='stone', mix=0.3, flat=2.2)
    a = _shade(sc, crevice=1.0, rim=0.6)
    st = _tagm(sc, 'stone')
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    top, west, front, east = _set_stone(sc, a, st, vs)
    if variant == 'a':                                                  # the broken corner, its fresh face paler
        ys_, xs_ = np.nonzero(st)
        brk = st & (Xg >= xs_.max() - 4) & (Yg <= ys_.min() + 4) & ((Xg - (xs_.max() - 4)) + (ys_.min() + 4 - Yg) > 4)
        a[brk] = -1
        rim_ = st & ~brk & ndi.binary_dilation(brk, iterations=1)
        a[rim_] = C('stone_warm', 4)
        st &= ~brk
    _stone_marks(a, st, top, vs)
    _finish(a)
    _seat_in_turf(a, st, vs, depth=3, shadow=4)
    K.despeckle(a, size=1)
    return K.crop(a, ox, oy)


# ================================================================================================
# beehives
# ================================================================================================
def wbc_hive(seed=171):
    """A WBC beehive, painted white: four legs and a plinth, the brood lift and two supers of long
    horizontal boards, each lift's skirt overhanging the one below (its lower edge lit, a dark line
    under it), a gabled roof of grey-painted boards with its ridge running back (the west pitch lit,
    the east pitch in shade, the gable boards at the front, the overhang's shadow on the top lift), the
    landing board lit on its top and the entrance dark under the porch."""
    sc = K.Scene(-28, 28, -22, 16, 84)
    for x in (-12, 12):
        for y in (-12, 1):
            sc.box(x - 1.5, y - 1.5, 0, x + 1.5, y + 1.5, 7, WHITE, base=2.8, k=1.4, tag='leg', mix=0.3)
    sc.box(-15, -14, 7, 15, 4, 10, WHITE, base=3.0, k=1.4, tag='plinth', mix=0.3)
    sc.box(-9, 4, 8.5, 9, 9, 10, WHITE, base=3.2, k=1.4, tag='board', mix=0.3)
    LH = 9
    for k in range(3):
        z0 = 10 + k * LH
        sc.box(-13, -12, z0, 13, 2, z0 + LH, WHITE, base=3.0, k=1.4, tag='lift%d' % k, mix=0.2)
        sc.box(-14.5, -13.5, z0 + LH - 3, 14.5, 3.5, z0 + LH, WHITE, base=3.0, k=1.4, tag='skirt%d' % k, mix=0.3)
    zr = 10.0 + 3 * LH
    for k in range(7):                                                    # the roof, stepped to its ridge
        hw = 17.5 - k * 2.5
        sc.box(-hw, -15, zr + k * 1.4, hw, 5, zr + (k + 1) * 1.4, ROOFP, base=2.8, k=1.4, tag='roof', mix=0.3)
    a = _shade(sc, crevice=1.0, rim=0.5)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox + 0.5
    z = sc.depth
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    # the lifts: painted boards, the body in white 3 with its west column lit and its east 3 texels
    # in white 2, a faint joint between the two boards of each lift; each skirt's lower edge a lit lip
    # (white 5) with a dark line under it on the lift below (white 1, leaning violet)
    for k in range(3):
        lf = _tagm(sc, 'lift%d' % k) & side
        lys = np.nonzero(lf)[0]
        t = np.where(gx < -10, 4.0, np.where(gx > 9.5, 2.0, 3.0))
        if len(lys):
            mid = (lys.min() + lys.max()) // 2
            t = np.where(Yg == mid, t - 0.7, t)
        rpaint(a, lf, WHITE, t, 0.3)
        sk = _tagm(sc, 'skirt%d' % k)
        sys_ = np.nonzero(sk & side)[0]
        t = np.where(Yg == sys_.max(), 5.0, np.where(Yg == sys_.min(), 3.4, 4.0)) - 1.0 * (gx > 10)
        rpaint(a, sk & side, WHITE, t, 0.3)
        rpaint(a, sk & ~side, WHITE, 4.4, 0.3)
        sh = np.zeros_like(sk)
        sh[1:] = (sk & side)[:-1]
        a[sh & ~sk & (a >= 0)] = C('snow_cool', 1)
        sh2 = np.zeros_like(sk)
        sh2[1:] = sh[:-1]
        V._step(a, sh2 & ~sk & ~sh & _tagm(sc, 'lift%d' % max(0, k - 1)), -1)
    for tag in ('leg', 'plinth', 'board'):
        m = _tagm(sc, tag)
        rpaint(a, m, WHITE, np.where(side, 3.0 + 0.6 * (gx < -6) - 0.8 * (gx > 8), 4.4), 0.3)
    # the roof: the west pitch lit, the east pitch in shade, a ridge, the gable boards at the front
    roof = _tagm(sc, 'roof')
    rt = np.where(~side, np.where(gx < 0, 4.0 + 0.8 * (gx > -5), 1.8 + 0.8 * (gx < 5)), 2.8)
    seam = (np.abs(np.abs(gx) - 6.5) < 0.6) | (np.abs(np.abs(gx) - 12.5) < 0.6)     # the boards' seams down each pitch
    rt = np.where(~side & seam, rt - 1.0, rt)
    rt = np.where(~side & (np.abs(gx) < 1.2), 3.4, rt)
    rpaint(a, roof, ROOFP, rt, 0.3)
    gable = roof & side
    rys = np.nonzero(gable)[0]
    a[gable & (Yg == rys.max())] = C('slate_cool', 1)                         # the drip edge
    rpaint(a, gable & (Yg < rys.max()), WHITE, 3.4 + 0.6 * (gx < 0) - 0.6 * (gx > 6), 0.3)   # the gable boards
    a[roof & ~side & (np.abs(gx) < 0.7)] = C('slate_warm', 4)                # the ridge
    eave = np.zeros_like(roof)
    eave[1:2] = False
    sh = np.zeros_like(roof)
    sh[1:] = gable[:-1]
    sh2 = np.zeros_like(roof)
    sh2[2:] = gable[:-2]
    V._step(a, (sh | sh2) & ~roof & _tagm(sc, 'lift2', 'skirt2'), -1)       # the overhang's shadow on the top lift
    # the entrance: a dark slot along the foot of the brood lift; the landing board's lit top plane
    l0 = _tagm(sc, 'lift0') & side
    l0y = np.nonzero(l0)[0].max()
    ent = (np.abs(gx) < 7) & (Yg >= l0y - 1) & (Yg <= l0y) & l0
    a[ent] = C('void', 1)
    bd = _tagm(sc, 'board')
    a[bd & ~side] = C('snow', 5)
    a[bd & side] = C('snow_cool', 2)
    _finish(a, keep=ent)
    # weathering run down under each skirt's lip (R3-13): streaks 1 x 4 to 6 in white 2, two a lift
    lifts = _tagm(sc, 'lift0', 'lift1', 'lift2') & side
    for k in range(3):
        sk = _tagm(sc, 'skirt%d' % k) & side
        sy0 = np.nonzero(sk)[0].max() + 2
        for j, x0 in enumerate((-8 + 5 * k, 3 + 2 * k)):
            n = 4 + int(3 * hsh(seed, k, j))
            col = ox + x0
            run = lifts[sy0:sy0 + n, col]
            seg = a[sy0:sy0 + n, col]
            seg[run] = C('snow', 2) if x0 < 0 else C('snow_cool', 2)
            a[sy0:sy0 + n, col] = seg
    # a brick on the roof to hold it down against the wind: its lit top, its front, its shadow
    ry0 = int(np.nonzero(roof.any(1))[0].min())
    bx0, by0 = ox - 7, ry0 + 3
    a[by0 + 3, bx0 + 1:bx0 + 7] = C('slate_cool', 1)                        # its shadow on the pitch
    a[by0, bx0:bx0 + 6] = C('clay', 4)
    a[by0 + 1:by0 + 3, bx0:bx0 + 6] = C('clay', 3)
    a[by0 + 1:by0 + 3, bx0 + 5] = C('clay_cool', 2)
    a[by0 + 2, bx0 + 2] = C('clay_cool', 2)                                # a chipped frog
    a[by0 - 1, bx0:bx0 + 6] = C('clay', 1)
    a[by0:by0 + 3, bx0 - 1] = C('clay', 1)
    a[by0:by0 + 3, bx0 + 6] = C('clay', 6)
    for (bx, by) in ((ox - 3, l0y + 1), (ox + 1, l0y - 1), (ox + 4, l0y + 2), (ox + 2, l0y - 3)):   # bees at the slot
        if a[by, bx] >= 0:
            a[by, bx] = C('void', 1)
    B._ground_tufts(a, ox, oy, [-14, -11, 11, 14], seed)
    return K.crop(a, ox, oy)


ROOFP = [('slate_cool', 'slate', 'slate'), ('slate_cool', 'slate_warm', 'slate_warm')]


SKEP_STRAW = [('earth_cool', 'brass', 'brass_warm'), ('earth_cool', 'brass_warm', 'brass_warm'), ('timber_cool', 'brass', 'brass')]
HACKLE = [('earth_cool', 'sand_cool', 'sand_cool'), ('timber_cool', 'brass', 'sand_cool')]


def skep(seed=173):
    """A straw skep on its stone stool, under a straw hackle: a bell of coiled straw rope widest at its
    foot and sitting on the stool's slab (its foot a flattened ellipse, as Eastward draws a can's top),
    each coil lit along its top with a dark line under it and curving round the bell, split-bramble
    stitches binding coil to coil (staggered), the entrance notch dark at its foot on the south; a
    conical hackle of older, greyer straw over the crown, lit on its west flank."""
    sc = K.Scene(-22, 22, -20, 14, 72)
    cy = -5.0
    sc.box(-6, cy - 5, 0, 6, cy + 5, 9, GRIT, base=2.1, k=1.6, tag='pier', round_=1.0, mix=0.3)
    sc.box(-13, cy - 8, 9, 13, cy + 8, 13, GRIT, base=2.6, k=1.7, tag='slab', round_=1.4, mix=0.6)
    a = _shade(sc, crevice=1.2, rim=0.6)
    B._lichen(sc, a, tags=('slab', 'pier'), rate=0.9, seed=seed)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    R, HT, CO, SQ = 11.5, 23, 4, 0.4                    # foot radius, height, coil, the ellipse's squash
    fx, fy = ox, oy + int(cy) - 13                      # the foot's centre on the slab
    x = Xg - fx + 0.5
    # height above the foot of each texel on the bell's front: y = fy - h + sag(x, h)
    best = np.full((H, W), -1.0)
    for h in range(HT + 1):
        r = R * math.sqrt(max(0.0, 1.0 - (h / (HT + 0.5)) ** 2))
        if r < 0.8:
            continue
        inr = np.abs(x) < r
        sag = SQ * r * np.sqrt(np.clip(1.0 - (x / max(r, 1e-6)) ** 2, 0, 1))
        row = np.round(fy - h + sag).astype(int)
        hit = inr & (Yg == row)
        best = np.where(hit & (best < 0), h, np.where(hit, np.maximum(best, h), best))
        # fill between this ring's front and the next ring up so the face is closed
        hit2 = inr & (Yg == row - 1)
        best = np.where(hit2 & (best < 0), h + 0.5, best)
    bell = best >= 0
    hh = best
    rr = R * np.sqrt(np.clip(1.0 - (hh / (HT + 0.5)) ** 2, 0.02, 1))
    u = x / np.maximum(rr, 1.0)
    ci = np.floor(hh / CO).astype(int)
    cz = hh - ci * CO
    t = 3.0 + np.where(cz >= CO - 1, 1.0, 0.0) - np.where(cz < 1, 1.4, 0.0)
    t = t + np.where((u > -0.65) & (u < -0.1), 0.7, 0.0) - np.where(u > 0.4, 1.0, 0.0) - np.where(hh < 1.5, 0.6, 0.0)
    rpaint(a, bell, SKEP_STRAW, t, np.clip(K.vhash(ci, 0, seed) * 0.999, 0, 0.999))
    stitch = bell & (cz < 2.0) & (hh > 2) & (((np.floor(x).astype(int) + 40 + (ci % 2) * 4) % 8) == 0) & (np.abs(u) < 0.85)
    a[stitch] = C('timber_cool', 2)
    notch = bell & (np.abs(x) < 2.6) & (hh < 3)
    a[notch] = C('void', 1)
    a[bell & (np.abs(x) < 2.6) & (hh >= 3) & (hh < 4)] = C('brass_warm', 4)
    # the hackle: a cone of straw over the crown from h 15, its point at h 30, lit on the west
    hz0, hz1, hr = 15, 30, 10.5
    hk = np.zeros((H, W), bool)
    ht = np.zeros((H, W))
    for h in range(hz0, hz1 + 1):
        r = hr * (1.0 - (h - hz0) / float(hz1 - hz0 + 1))
        if r < 0.6:
            continue
        sag = SQ * r * np.sqrt(np.clip(1.0 - (x / max(r, 1e-6)) ** 2, 0, 1))
        for dy in (0, 1):
            m = (np.abs(x) < r) & (Yg == np.round(fy - h + sag).astype(int) - dy) & ~hk
            hk |= m
            ht = np.where(m, h, ht)
    uh = x / hr
    tt = 2.9 + np.where(uh < -0.15, 0.9, 0.0) - np.where(uh > 0.3, 1.0, 0.0)
    ang = np.arctan2(x, np.maximum(1.0, Yg - (fy - hz1)))
    sf = np.mod(ang * 13.0, 1.0)                                          # strands running down the cone from its point
    tt = tt - 1.0 * (sf < 0.22) * (ht > hz0 + 1) + 0.7 * ((sf > 0.5) & (sf < 0.68) & (uh < 0.2)) * (ht > hz0 + 1)
    tt = np.where(ht < hz0 + 1, tt - 0.8, tt)
    rpaint(a, hk, HACKLE, tt, 0.3)
    under = np.zeros_like(hk)
    under[1:] = hk[:-1]
    V._step(a, under & bell & ~hk, -1)                                    # the hackle's shadow on the coils
    _finish(a)
    B._ground_tufts(a, ox, oy, [-9, -7, 7, 9], seed)
    return K.crop(a, ox, oy)


# ================================================================================================
# pieces
# ================================================================================================
_fp, _rel = B._fp, B._rel
OFF_ROUTE, OFF_WATER = B.OFF_ROUTE, B.OFF_WATER
NATURE = [OFF_ROUTE, OFF_WATER]
EW_COAST = '17 (the churns and the farm props for painted metal and rope), 12 (the post box for a painted iron body); no harbour in the local refs'
EW_HALT = '13 (the lamp post 375,20,415,125), 17 (the churns 135,47,162,112 and the bench), the anchors kit/lantern and kit/bench'
EW_MILL = '17 (the rocks 460,165,550,250, the fence, sacks), 12 (the boulder wall and the stepping stones in water)'
EW_RURAL = '12 (the thatched hut, the boulder wall), 13 (the rocks 325,247,350,268), 17 (the rockfall for stones carried in planes)'


def prop_jobs():
    J = []

    def add(pid, variants, **kw):
        J.append((pid, variants, kw))
    # Driftwood quay
    add('coast_net_rack', [('still', lambda: net_rack())], name='Net rack', purpose='store', role='rack', cells=(4, 1), fp=_fp(4, 1),
        collision={'shape': 'rect', 'rect': [-13.0, -1.0, 26, 2]}, shadow=(30, 4), composition='edge',
        requires=[_rel('near', 'water', 4, 'nets are hung to dry on the quay, by the boats that set them')],
        forbids=[OFF_WATER], size_class='rack (a net rack 1.1 m to its rail, 2 m long; art px: 45 to 62 tall, 75 to 100 wide)',
        eastward=EW_COAST,
        note='Three oak posts and a rail with a net hung to dry: mostly air, twine in diamonds lit to the upper left, folds where the mesh closes, an uneven weighted foot; corks, two glass floats, its tail in a flat coil.')
    add('coast_lobster_pots', [('a', lambda: lobster_pots('a')), ('b', lambda: lobster_pots('b'))], name='Lobster pots',
        purpose='store', role='store', cells=(2, 1), fp=_fp(2, 1),
        collision={'shape': 'rect', 'rect': [-7.0, -3.0, 14, 4]}, shadow=(16, 3), composition='cluster',
        requires=[_rel('near', 'water', 3, 'creels stacked on the quay between trips')], forbids=[OFF_WATER],
        size_class='creel_stack (no size-guide kind: a creel is smaller than the guide\'s crate; a creel 0.5 m long, 0.3 m high; three stacked 0.6 m; art px: 18 to 48 tall, 40 to 56 wide)',
        eastward=EW_COAST,
        note='Woven withy creels on timber bases, half-cylinders in three-quarter view (a lit back, hooped south face, a D-shaped east end with its funnel mouth): three stacked (a), or one with its rope coil and float (b).')
    add('coast_mooring_bitt', [('still', lambda: mooring_bitt())], name='Mooring bitt', purpose='contain', role='mooring',
        cells=(2, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-2.5, -2.5, 5, 4]}, shadow=(8, 2), composition='edge',
        requires=[_rel('near', 'water', 1, 'on the quay\'s edge, where a boat\'s line is made fast')], forbids=[OFF_WATER],
        size_class='mooring bitt (0.45 m, its line coiled beside it; art px: 16 to 26 tall, 32 to 50 wide)', eastward=EW_COAST,
        note='A cast-iron bitt on a bolted plate, a hawser made fast round its waist and the rest flaked down in a flat coil.')
    add('coast_boat_beached', [('still', lambda: boat_beached())], name='Beached boat', purpose='mark', role='boat',
        cells=(4, 2), fp=_fp(4, 1), collision={'shape': 'rect', 'rect': [-14.0, -6.0, 28, 6]}, shadow=(30, 5), composition='free',
        requires=[_rel('near', 'water', 4, 'drawn up the beach above the tide line')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='boat (a 2.1 m clinker dinghy, 0.5 m to its gunwale; art px: 30 to 46 tall, 84 to 100 wide)', eastward=EW_COAST,
        note='A clinker dinghy drawn up on the shingle, dry: lapped strakes, blue and white, red below; thwarts inside.')
    add('coast_buoy', [('still', lambda: buoy())], name='Buoy', purpose='guide', role='marker', cells=(1, 1), fp=_fp(1, 1),
        collision={'shape': 'none'}, shadow=None, blocks=False, composition='free',
        requires=[_rel('on', 'water', note='a can buoy moored off the quay, marking the channel')],
        extra={'provides': ['view']}, size_class='buoy (a can buoy 0.6 m above the water; art px: 24 to 36 tall, 20 to 30 wide)',
        eastward=EW_COAST,
        note='A red can buoy with a white band and its cage, riding the swell (8 frames), held still under reduced motion.')
    add('coast_harbour_light', [('still', lambda: harbour_light())], name='Harbour light', purpose='light', role='beacon',
        cells=(1, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-4.0, -2.5, 8, 5]}, shadow=(10, 3), composition='edge',
        requires=[_rel('near', 'water', 1, 'at the jetty\'s head, its light over the harbour mouth')], forbids=[OFF_WATER],
        extra={'provides': ['feature', 'view']},
        size_class='lamp (a harbour light: a cast-iron column 3.4 m on its plinth, not the lighthouse; art px: 107 to 178 tall, 20 to 34 wide)',
        eastward=EW_COAST + '; 13 (the lamp post 375,20,415,125 for the iron and the lantern)',
        note='A turned cast-iron column, banded and fluted, on a granite plinth with a mooring ring; a ladder bar on scrolls; a red-glazed lantern with its glazing bars, a conical cap, vent ball and finial; it glows (8 frames).')
    # the Halt
    add('halt_platform_edge', [(v_, (lambda v_=v_: platform_edge(v_))) for v_ in 'abcd'], name='Platform edge',
        purpose='cross', role='platform', cells=(1, 1), fp=[[0, -1]], collision={'shape': 'none'}, shadow=None, blocks=False,
        composition='edge', requires=[_rel('near', 'route', 3, 'the platform runs beside the lane the halt serves')],
        forbids=[OFF_WATER], size_class='platform (a 0.3 m front and its coping, the gravel behind; art px: 30 to 44 tall, 24 to 24 wide)',
        eastward=EW_HALT,
        note='One cell of the platform\'s edge along x: dressed blocks, a coping slab standing proud with a worn white lip, flags behind; four variants to shuffle along a run; cells meet.')
    add('halt_waiting_shelter', [('still', lambda: waiting_shelter())], name='Waiting shelter', purpose='rest', role='shelter',
        cells=(6, 2), fp=_fp(6, 2), collision={'shape': 'rect', 'rect': [-22.0, -13.0, 44, 13]}, shadow=None, composition='edge',
        requires=[_rel('near', 'route', 5, 'on the platform, open to the line, a few steps from the lane')], forbids=[OFF_ROUTE, OFF_WATER],
        extra={'provides': ['feature']},
        size_class='shelter (size guide: a roof at 36 to 44 world px; eave 118 art px, 2.7 m; art px: 150 to 180 tall, 120 to 160 wide)',
        eastward=EW_HALT,
        note='A green-and-cream lean-to: boarded walls, a slate roof with fascia and gutter, a scalloped valance, a board bench, '
             'a poster, a flagged floor in the roof\'s shade.')
    add('halt_churn_stand', [('still', lambda: churn_stand())], name='Milk-churn stand', purpose='store', role='store',
        cells=(3, 1), fp=_fp(3, 1), collision={'shape': 'rect', 'rect': [-11.0, -4.0, 22, 5]}, shadow=(22, 4), composition='edge',
        requires=[_rel('near', 'route', 1, 'at the lane\'s side, where the cart sets the churns down for the train')],
        forbids=[OFF_ROUTE, OFF_WATER],
        size_class='stand (deck 0.65 m; churns 0.78 m tall, 0.35 m across as Eastward\'s in 17; art px: 60 to 80 tall, 56 to 80 wide)',
        eastward=EW_HALT,
        note='A board deck on four posts, three galvanised churns in mid-value tin with bands, shoulders, necks, ringed lids and handles.')
    add('halt_semaphore', [('still', lambda: semaphore())], name='Semaphore signal', purpose='guide', role='signal',
        cells=(2, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-2.0, -2.0, 4, 4]}, shadow=(8, 3), composition='edge',
        requires=[_rel('near', 'route', 3, 'at the platform\'s end, where the driver sees it')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='signal (a semaphore post 3 m; art px: 125 to 160 tall, 30 to 50 wide)', eastward=EW_HALT,
        note='A three-tone post with cap and finial, the red arm at danger, its spectacle cast with it, a ladder beside.')
    add('halt_platform_lamp', [('still', lambda: platform_lamp())], name='Platform lamp', purpose='light', role='lamp',
        cells=(1, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 3]}, shadow=(6, 2), composition='edge',
        requires=[_rel('near', 'route', 5, 'along the platform, lighting the way from the lane to the train')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='platform_lamp (no size-guide kind: a platform lamp is 2.9 m, under the guide\'s street lamp of 50 to 65 world px; a platform lamp 2.9 m; art px: 107 to 178 tall, 15 to 28 wide)', eastward=EW_HALT,
        note='A green column on a fluted foot, a ladder bar, a lantern of two panes lit from inside (8 frames), a domed cap.')
    add('halt_timetable_board', [('still', lambda: timetable_board())], name='Timetable board', purpose='guide', role='notice',
        cells=(3, 1), fp=_fp(2, 1), collision={'shape': 'rect', 'rect': [-7.0, -1.0, 14, 2]}, shadow=(16, 3), composition='edge',
        requires=[_rel('near', 'route', 2, 'by the platform\'s entrance from the lane')], forbids=[OFF_ROUTE, OFF_WATER],
        extra={'provides': ['feature']},
        size_class='notice board (2.2 m; art px: 81 to 126 tall, 44 to 89 wide)', eastward=EW_HALT,
        note='A printed sheet behind glass (a header with a train and a clock, rows of print, a notice pinned askew) under a gabled hood.')
    # the Millrace
    add('mill_wheel', [('still', lambda: mill_wheel())], name='Water mill and wheel', purpose='work', role='wheel', cells=(14, 7),
        fp=_fp(14, 7), collision={'shape': 'rect', 'rect': [-52.0, -48.0, 104, 48]}, shadow=None, composition='edge',
        requires=[_rel('near', 'water', 2, 'the wheel sits in the race that drives it')], forbids=[OFF_ROUTE],
        extra={'provides': ['feature', 'water', 'view']},
        size_class='water_mill (the size guide\'s water mill: 104 world px wide, two storeys and a loft, 76 to the eaves; the wheel 44 across on the water side, its race the zone\'s water; art px: 310 to 432 tall, 288 to 384 wide)',
        eastward=EW_MILL,
        note='A two-storey water mill of rubble with quoins under a slate roof (ridge tiles, barge boards, fascia and gutter) from the house builder: a loading door 32 x 22 with a hoist door and beam above, windows on both storeys; the undershot wheel turning (8 frames) on the water side, its lower floats dipping into the race, which is the zone\'s own water.')
    add('mill_sluice', [('still', lambda: sluice())], name='Sluice gate', purpose='water', role='sluice', cells=(3, 2),
        fp=_fp(3, 1), collision={'shape': 'rect', 'rect': [-12.0, -4.0, 24, 4]}, shadow=None, composition='edge',
        requires=[_rel('near', 'water', 1, 'at the leat\'s head, holding back the race')], forbids=[OFF_ROUTE],
        extra={'provides': ['feature', 'water']},
        size_class='sluice (piers 0.75 m, the rack to 1.1 m; art px: 55 to 80 tall, 44 to 60 wide)', eastward=EW_MILL,
        note='Two coursed stone piers, an oak gate of planks drawn up on its rack, a toothed gear, the water white under it.')
    add('mill_millstones', [('still', lambda: millstones())], name='Millstones', purpose='store', role='store', cells=(5, 2),
        fp=_fp(5, 1), collision={'shape': 'rect', 'rect': [-19.0, -6.0, 41, 6]}, shadow=(30, 4), composition='edge',
        requires=[_rel('near', 'route', 3, 'in the miller\'s yard, by the door they will be carried through')],
        forbids=[OFF_ROUTE, OFF_WATER], size_class='millstones (1.2 m across; art px: 56 to 76 tall, 112 to 132 wide)', eastward=EW_MILL,
        note='A dressed millstone flat and one on edge against a post: bevels, eyes, harps of furrows; a sack of meal.')
    add('mill_landslip', [('still', lambda: landslip())], name='Landslip', purpose='mark', role='barrier', cells=(6, 3),
        fp=_fp(6, 2), collision={'shape': 'rect', 'rect': [-22.0, -14.0, 44, 14]}, shadow=None, blocks=False, composition='free',
        requires=[_rel('on', 'route', note='the slip lies across the road: way W3, cleared once the Millrace is mended')],
        extra={'provides': ['feature']},
        size_class='landslip (a tongue of earth 3 m across, 0.5 m deep; art px: 56 to 80 tall, 120 to 145 wide)',
        eastward='17 (the rockfall 460,165,550,250: stones carried in planes with dark gaps), 13 (the rocks)',
        story={'owner': None, 'lore': 'Way W3 (world-plan.md 6): the Millrace landslip on the Foothill Road; the way system '
                                      '(world-unlocks.md) holds the road shut, this piece is its picture', 'gating': {'act': 1}},
        note='A break in a low bank: a raw scar under a torn turf lip (the bank\'s own, it has none of its own); a spill of earth in lumps with turf clods, seated boulders and a snapped birch.')
    add('mill_fence_broken', [('still', lambda: fence_broken())], name='Broken rail fence', purpose='mark', role='story',
        cells=(4, 1), fp=_fp(3, 1), collision={'shape': 'rect', 'rect': [-13.0, -1.0, 26, 2]}, shadow=(26, 3), composition='edge',
        requires=[_rel('near', 'route', 3, 'the field fence the slip knocked down beside the road')], forbids=[OFF_WATER],
        size_class='fence (art px: 41 to 67 tall, 70 to 96 wide)', eastward=EW_MILL,
        note='A snapped post, a leaning one, the top rail split and hanging to the grass.')
    # Old Fang's barrow
    add('barrow_entrance', [('still', lambda: barrow_entrance())], name="Old Fang's barrow", purpose='mark', role='tomb',
        cells=(14, 4), fp=[[c, -r] for r in range(4, 0, -1) for c in range(-6, 7)],
        collision={'shape': 'rect', 'rect': [-53.0, -29.0, 106, 29]}, shadow=None, composition='free',
        doors=[{'x': [-21, 21], 'faces': 's'}],
        requires=[_rel('near', 'route', 5, 'off the path on its own rise, reached by a short trod')], forbids=NATURE,
        extra={'provides': ['feature', 'view']},
        size_class='barrow (a mound 7.4 m long, 2 m high; its portal 0.95 m wide, 1.8 m high, so Bramble walks in; '
                   'art px: 150 to 190 tall, 300 to 340 wide)', eastward=EW_RURAL,
        story={'owner': None, 'lore': "Old Fang's barrow (the map legend's Act 1 beat)", 'gating': {'act': 1}},
        note='A turf mound in soft masses of grass with a portal of jambs and a capstone, the passage receding in perspective, set stones either side.')
    add('barrow_kerb', [('a', lambda: kerb_stone('a')), ('b', lambda: kerb_stone('b')), ('c', lambda: kerb_stone('c'))],
        name='Kerb stone', purpose='mark', role='marker', cells=(1, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-3.0, -1.5, 6, 3]}, shadow=(8, 2), composition='cluster',
        requires=[_rel('near', 'barrow_entrance', 4, 'a stone of the ring round the barrow\'s foot')], forbids=NATURE,
        size_class='kerb stone (0.35 to 0.45 m set on edge; art px: 16 to 28 tall, 14 to 30 wide)', eastward=EW_RURAL,
        note='A stone seated in the turf, carried in planes (a lit top, a shaded side), with a crack, lichen and its contact shadow: a dressed slab, a low boulder, a pillar.')
    # beehives
    add('hive_wbc', [('still', lambda: wbc_hive())], name='Beehive', purpose='work', role='hive', cells=(2, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-5.0, -4.0, 10, 6]}, shadow=(12, 3), composition='cluster',
        requires=[_rel('near', 'route', 3, 'in a garden or an orchard by the path, its entrance to the morning sun')],
        forbids=[OFF_ROUTE, OFF_WATER],
        size_class='beehive (size guide: hip high, 13 to 22 world px; a WBC hive 1.05 m with its roof; art px: 50 to 70 tall, 30 to 46 wide)',
        eastward='12 (the post box 387,200,420,248 for a painted box carried in a few planes)',
        note='A white WBC hive: legs, plinth, three lifts with overhanging skirts, a gabled roof lit west, the landing board.')
    add('hive_skep', [('still', lambda: skep())], name='Straw skep', purpose='work', role='hive', cells=(2, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-4.0, -3.0, 8, 5]}, shadow=(10, 3), composition='cluster',
        requires=[_rel('near', 'route', 3, 'on its stool by a cottage garden wall')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='beehive (a skep 0.5 m on a 0.3 m stool, hip high; art px: 40 to 62 tall, 22 to 36 wide)',
        eastward='17 (the churns for a round object\'s squashed top), 12 (the post box)',
        note='A bell of coiled straw sitting on its stone stool, bound coil to coil, its notch at the foot, under a straw hackle.')
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

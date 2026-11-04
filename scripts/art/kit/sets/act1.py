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
def _rope_coil(a, cx, cy, rings=4, rx=9.0, ry=4.0, seed=0):
    """A coil of rope lying on the ground: rings stepping inward and up, each lit along its top arc and
    dark along its bottom, the strands' lay as diagonal marks."""
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    for k in range(rings):
        r1, r2 = rx - k * 2.6, ry - k * 1.0
        yk = cy - k * 1.2
        outer = (((Xg + 0.5 - cx) / r1) ** 2 + ((Yg + 0.5 - yk) / r2) ** 2) <= 1.0
        inner = (((Xg + 0.5 - cx) / max(0.8, r1 - 2.2)) ** 2 + ((Yg + 0.5 - yk) / max(0.6, r2 - 1.4)) ** 2) <= 1.0
        ring = outer & ~inner
        t = np.where(Yg < yk, 4.0, 2.4) + 0.6 * (Xg < cx - r1 * 0.3) - 0.6 * (Xg > cx + r1 * 0.4)
        t = np.where(((Xg + Yg) % 5) < 2, t - 0.8, t)
        rpaint(a, ring, ROPE, t, 0.3)
        if k == rings - 1:
            a[inner] = C('earth_cool', 1)


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
        rpaint(a, m, OAK, np.where(gx < x - 1, 3.6, np.where(gx >= x + 1, 1.8, 2.7)), 0.3)
    rail = _tagm(sc, 'rail')
    rys = np.nonzero(rail & side)[0]
    rpaint(a, rail, OAK, np.where(~side, 3.9, np.where(Yg == rys.max(), 1.8, 2.8)), 0.3)
    B._lichen(sc, a, tags=('post',), rate=0.5, seed=seed)
    # the hung net, sagging between the posts in folds
    top = oy - 46 + 2
    net = np.zeros((H, W), bool)
    fold = np.zeros((H, W))
    for (xa, xb) in ((-34, 0), (0, 34)):
        for x in range(xa + 3, xb - 2):
            u = (x - xa) / float(xb - xa)
            hem = oy - 12 + 6 * math.sin(math.pi * u) + 2 * math.sin(5 * u + xa)
            net[top:int(hem), ox + x] = True
            fold[:, ox + x] = math.sin((x - xa) * 0.62)
    crest = fold > 0.35
    trough = fold < -0.35
    diam = ((((Xg + Yg) % 4) == 0) | (((Xg - Yg) % 4) == 0))
    t = np.where(crest, 3.4, np.where(trough, 1.6, 2.5)) - 0.6 * (Yg > oy - 18)
    t = np.where(diam & ~trough, t - 1.0, t)
    t = np.where(trough & ~diam, t - 0.5, t)
    rpaint(a, net, NET, t, 0.3)
    hem_ = net & ~np.roll(net, -1, 0)
    a[hem_] = C('leaf_cool', 1)
    # the head rope's corks
    for x in range(-31, 32, 5):
        if abs(x) < 3 or abs(abs(x) - 34) < 3:
            continue
        a[top + 1:top + 3, ox + x:ox + x + 2] = C('fox', 3)
        a[top + 1, ox + x] = C('fox', 4)
        a[top + 2, ox + x + 1] = C('crag_warm', 2)
    a[top, ox - 31:ox + 31][net[top, ox - 31:ox + 31]] = C('sand_cool', 3)          # the head rope
    _finish(a, keep=np.isin(a, [C('fox', 3), C('fox', 4)]))
    _float_ball(a, ox - 20, oy - 26, 3.6, seed)
    _float_ball(a, ox + 15, oy - 21, 3.2, seed + 1)
    _rope_coil(a, ox + 40, oy - 2, rings=4, rx=8.5, ry=3.8, seed=seed)
    B._ground_tufts(a, ox, oy, [-38, -31, 30], seed)
    return K.crop(a, ox, oy)


def lobster_pots(variant='a', seed=103):
    """Withy creels on timber bases, 0.5 m long: each a hooped D-shaped pot, its three hoops lit arcs
    over the top (willow, lit above, dark below), the netting a few dark diagonal cords between them, the
    funnel's mouth a dark ellipse at its east end; stacked three high, the top one set back with a
    contact shade under it (a), or one with a coil of rope and its float at its side (b)."""
    sc = K.Scene(-36, 36, -22, 8, 48)
    pots = [(-11, -4, 0), (11, -4, 0), (0, -9, 13.5)] if variant == 'a' else [(-7, -4, 0)]
    for k, (x, y, z) in enumerate(pots):
        sc.box(x - 11, y - 6.5, z, x + 11, y + 6.5, z + 2.5, OAK, base=2.6, k=1.4, tag='pbase%d' % k, mix=0.3)
        sc.ellipsoid(x, y, z + 2.5, 10.5, 6.5, 10.0, WILLOW, base=2.4, k=1.4, tag='dome%d' % k, mix=hsh(seed, k))
    if variant == 'b':
        sc.ellipsoid(20, -2, 5, 4.6, 4.0, 4.6, RED, base=2.6, k=1.6, tag='float', mix=0.2)
        sc.cylinder(20, -2, 0.8, 9, 13, IRON, base=2.4, k=1.4, tag='flag')
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox
    L = sc.light()
    for k, (x, y, z) in enumerate(pots):
        d = _tagm(sc, 'dome%d' % k)
        lx = gx - x
        hoop = np.zeros_like(d)
        for hx in (-6, 0, 6):
            hoop |= d & (lx >= hx - 1) & (lx < hx + 1) & (((lx - hx + 1) % 2) == 0) | (d & (lx == hx))
        ht = np.where(L > -0.15, 4.0, 2.6)
        rpaint(a, d & hoop, WILLOW, ht, 0.3)
        mesh = d & ~hoop
        rpaint(a, mesh, [('timber_cool', 'timber', 'timber_warm')], np.where(L > -0.15, 3.0, 2.0), 0.3)
        # the withies woven round the hoops: a dark line under each course, the courses following the dome
        cz = (sc.depth - z - 2.5)
        weave = mesh & ((np.floor(cz).astype(int) % 4) == 0) & (L > -0.15)
        V._step(a, weave, -1)
        mouth = _disc(a.shape, ox + x + 8, oy + y - (z + 7), 2.4, 3.2) & d
        a[mouth] = C('void', 1)
        ring = _disc(a.shape, ox + x + 8, oy + y - (z + 7), 3.4, 4.2) & d & ~mouth
        a[ring] = C('brass', 3)
        pb = _tagm(sc, 'pbase%d' % k)
        rpaint(a, pb, OAK, np.where(sc.n[..., 2] > 0.5, 3.6, 2.4), 0.3)
        if z > 0:                                                          # the contact shade under the top pot
            below = np.zeros_like(pb)
            below[1:] = pb[:-1]
            below2 = np.zeros_like(pb)
            below2[2:] = pb[:-2]
            V._step(a, (below | below2) & ~pb & (a >= 0), -1)
    if variant == 'b':
        fl = _tagm(sc, 'float')
        rpaint(a, fl, RED, np.where(L > 0.3, 4.0, np.where(L > -0.1, 3.0, 1.8)), 0.3)
        a[fl & (np.abs(Yg - (oy - 2 - 6)) < 1)] = C('snow', 4)                # its white band
    _finish(a)
    if variant == 'b':
        _rope_coil(a, ox + 7, oy - 2, rings=3, rx=7.0, ry=3.2, seed=seed)
        K.despeckle(a, size=1)
    B._ground_tufts(a, ox, oy, [-24, -20, 22], seed)
    return K.crop(a, ox, oy)


def _laid_rope(a, pts, w=2.0, seed=0):
    """A laid rope along a polyline: its strands as alternating lit and dark diagonal marks along it,
    its top edge lit."""
    m = np.zeros(a.shape, bool)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        m |= _line(a.shape, x0, y0, x1, y1, w)
    Yg, Xg = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    t = np.where(((Xg + Yg) % 4) < 2, 2.4, 3.4)
    up = np.zeros_like(m)
    up[1:] = m[:-1]
    t = np.where(m & ~up, t + 0.6, t)
    rpaint(a, m, ROPE, t, 0.3)
    return m


def mooring_bitt(seed=105):
    """A cast-iron mooring bitt on the quay's edge, 0.5 m: a squat post with a waist on a bolted plate,
    a domed cap with its rim lit, rust running in streaks under the cap and in the waist; a hawser made
    fast with turns round its waist, the strands of its lay showing, and the rest of the line flaked
    in a coil on the quay beside it: tied off, not trailing."""
    W, H = 52, 40
    a = np.full((H, W), -1, np.int32)
    ox, oy = 18, 34
    Yg, Xg = np.mgrid[0:H, 0:W]
    plate = (np.abs(Xg + 0.5 - ox) <= 8) & (Yg >= oy - 3) & (Yg < oy + 1)
    rpaint(a, plate, IRON, np.where(Yg == oy - 3, 3.4, 2.2), 0.3)
    for bx in (-6, 6):
        a[oy - 2, ox + bx] = C('slate', 4)
        a[oy - 1, ox + bx] = C('void', 1)
    prof = [5.8, 5.8, 4.8, 4.6, 4.2, 4.0, 4.0, 4.0, 4.2, 4.6, 5.0, 6.4, 6.4, 5.4, 4.4, 2.8]
    m, hh, u, top = _turned(a, ox, oy - 2, prof, IRON, lit=3.6, body=2.4, shade=1.2, top_t=3.4)
    a[m & ~top & (hh >= 11) & (hh < 12)] = C('slate', 4)                      # the cap's lit rim
    for (x0, y0, n) in ((-1, oy - 2 - 11, 4), (2, oy - 2 - 10, 3), (-2, oy - 2 - 6, 3)):
        a[y0:y0 + n, ox + x0] = C('fox', 2)
        a[y0 + n - 1, ox + x0] = C('crag', 2)
    _finish(a)
    # the hawser: two turns round the waist, then led off east to its coil on the quay
    for k in range(2):
        yy = oy - 2 - 5 - k * 2
        _laid_rope(a, [(ox - 4.5, yy + 1.5), (ox + 4.5, yy - 0.5)], 2.0, seed + k)
    _laid_rope(a, [(ox + 4.5, oy - 6), (ox + 12, oy - 2), (ox + 20, oy - 1)], 2.0, seed + 3)
    _rope_coil(a, ox + 26, oy - 1, rings=4, rx=8.0, ry=3.6, seed=seed)
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
    rail = hull & (z >= zg - 1.0) & (z < zg + 1.2)
    out = hull & (z < zg - 1.0)
    # outside: the strakes, lapped, blue with a white sheer strake and red below the waterline
    lapz = (z % 3.0)
    t = 1.3 + 2.2 * L_ + np.where(lapz < 0.9, 1.0, 0.0) - np.where(lapz > 2.3, 0.7, 0.0)
    rpaint(a, out & (z >= 8), WHITE[:2], t + 0.4, 0.3)
    rpaint(a, out & (z < 8) & (z >= 3.5), [('water_cool', 'water_cool', 'water'), ('water_cool', 'water', 'water')], t,
           np.clip(K.noise(a.shape, np.random.default_rng(seed), 6.0) * 0.999, 0, 0.999))
    rpaint(a, out & (z < 3.5), RED, t - 0.3, 0.3)
    flake = out & (z < 8) & (z >= 3.5) & (K.vhash(Xg // 3, Yg // 2, seed) > 0.96)
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
    """The harbour light at the jetty's head: a fluted cast-iron column painted white on a coursed
    granite plinth, a collar and a ladder bar under the lantern; the lantern a glazed box in an iron
    frame with its red lens to the sea, a domed red cap with a vent and a finial. The column is a lit
    cylinder (a highlight band left of centre, a core shadow on its right third), rust weeping from
    the collar and the bar. The lamp's glow swells and eases over the cycle."""
    sc = K.Scene(-22, 22, -16, 16, 150)
    sc.box(-11, -6, 0, 11, 6, 16, GRANITE, base=2.6, k=1.4, tag='plinth', round_=1.0, mix=0.4)
    sc.box(-12.5, -7, 16, 12.5, 7, 18, GRANITE, base=3.0, k=1.4, tag='cope', round_=0.8, mix=0.5)
    sc.cylinder(0, 0, 5.4, 18, 23, WHITE, base=3.0, k=1.4, tag='foot', mix=0.3)
    sc.cylinder(0, 0, 4.4, 23, 26, WHITE, base=3.0, k=1.4, tag='collar', mix=0.3)
    sc.cylinder(0, 0, 4.2, 26, 108, WHITE, base=3.0, k=1.4, tag='shaft', mix=0.3)
    sc.cylinder(0, 0, 4.2, 62, 64.5, WHITE, base=3.0, k=1.4, tag='collar', mix=0.3)
    sc.cylinder(0, 0, 4.8, 104, 108, WHITE, base=3.0, k=1.4, tag='collar', mix=0.3)
    sc.box(-9, -0.9, 108, 9, 0.9, 110, IRON, base=2.4, k=1.4, tag='bar', mix=0.3)
    sc.box(-7.5, -7.5, 110, 7.5, 7.5, 112.5, IRON, base=2.4, k=1.4, tag='frame', mix=0.3)
    sc.box(-6.5, -6.5, 112.5, 6.5, 6.5, 126, [('lamp', 'lamp', 'lamp')], base=3.0, k=0.4, tag='glass')
    sc.cylinder(0, 0, 8.0, 126, 128.5, RED, base=2.4, k=1.6, tag='rim', mix=0.3)
    sc.ellipsoid(0, 0, 128.5, 7.0, 7.0, 5.5, RED, base=2.6, k=1.8, tag='cap', mix=0.3)
    sc.cylinder(0, 0, 2.2, 132, 135, RED, base=2.6, k=1.6, tag='vent', mix=0.3)
    sc.ellipsoid(0, 0, 135.5, 3.0, 3.0, 1.4, RED, base=2.6, k=1.8, tag='vent', mix=0.3)
    sc.cylinder(0, 0, 0.8, 136, 141, IRON, base=2.4, k=1.4, tag='finial')
    sc.ellipsoid(0, 0, 142, 1.5, 1.5, 1.5, IRON, base=2.8, k=1.6, tag='finial')
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox + 0.5
    z = sc.depth
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    # the white iron: each round part a lit cylinder; the shaft fluted (dark lines in the shade, lit
    # ones on the highlight); the foot's flutes broader
    for tag, r in (('shaft', 4.2), ('collar', 4.6), ('foot', 5.4)):
        m = _tagm(sc, tag) & side
        t = _cyl_tone(gx, r, lit=4.4, body=3.4, shade=2.2)
        rpaint(a, m, WHITE, t, 0.3)
    sh = _tagm(sc, 'shaft') & side
    ft = _tagm(sc, 'foot') & side
    V._step(a, ft & ((np.floor(gx + 20).astype(int) % 3) == 0) & (z < 22), -1)
    for tag in ('foot', 'collar'):
        tm = _tagm(sc, tag) & ~side
        rpaint(a, tm, WHITE, 4.4 + 0.5 * L, 0.2)
    # rust weeping from the collar and the ladder bar, and at the foot
    for (x0, z0, n) in ((-2, 103, 6), (2, 103, 4), (1, 61, 5), (-2, 61, 3), (3, 22, 3)):
        yy = oy - z0
        a[yy:yy + n, ox + x0] = np.where(np.arange(n) < n - 1, C('fox', 2), C('crag', 2))
    # the lantern: the glazing lit from inside, brighter low in the middle; the iron frame and
    # astragals; the red lens on the sea side
    glass = _tagm(sc, 'glass')
    glow = 0.5 + 0.5 * math.sin(2 * math.pi * i / LOOP)
    zt = (z - 112.5) / 13.5
    gt = 2.8 + 1.0 * glow + 1.0 * (1 - np.abs(gx) / 6.5) * (zt < 0.6) - 0.6 * (zt > 0.75)
    rpaint(a, glass, [('clay_cool', 'clay', 'fox')], gt, 0.0)               # red glazing, lit from inside
    front = glass & side
    lens = front & (np.abs(gx) < 2.1) & (zt > 0.22) & (zt < 0.62)            # the flame behind the lens
    rpaint(a, lens, [('fox', 'fox', 'lamp')], 3.6 + 1.4 * glow, 0.0)
    a[glass & side & (np.abs(gx + 4.5) < 0.6) & (zt > 0.5) & (zt < 0.8)] = C('fox', 5)   # the pane's glint
    astr = glass & ((np.abs(gx) > 5.6) | ((np.abs(np.abs(gx) - 3.8) < 0.5) & side) | (np.abs(zt - 0.86) < 0.06))
    a[astr] = C('iron', 1)
    a[glass & ~side & (Yg == np.nonzero(glass)[0].min())] = C('iron', 2)
    # the red cap and rim: lit plane west, a vent band, the drip edge dark
    cap = _tagm(sc, 'cap', 'rim', 'vent')
    rpaint(a, cap, RED, 2.6 + 1.6 * L, 0.2)
    rim = _tagm(sc, 'rim')
    a[rim & (Yg == np.nonzero(rim)[0].max())] = C('crag_cool', 1)
    vent = _tagm(sc, 'vent') & side
    a[vent & ((np.floor(gx + 20).astype(int) % 2) == 0)] = C('crag_cool', 1)
    # the plinth: dressed granite in two courses, its coping lit along the front lip
    pl = _tagm(sc, 'plinth')
    _stone_parts(a, pl & side, gx + 100, z, seed, GRANITE, 2.9 + 0.0 * L, lo=11, hi=16, course=8, moss=3.0)
    cope = _tagm(sc, 'cope')
    rpaint(a, cope, GRANITE, np.where(side, 3.8, 3.0 + 0.6 * L), 0.4)
    B._lichen(sc, a, tags=('plinth',), rate=0.8, seed=seed)
    keep = glass | lens
    _finish(a, keep=keep)
    if glow > 0.6:                                                         # a soft halo at the peak, no outline
        halo = ndi.binary_dilation(glass, iterations=2) & (a < 0) & (Yg < oy - 108)
        a[halo & (((Xg + Yg) % 2) == 0)] = C('lamp', 4)
    return a, ox, oy


def harbour_light(seed=111):
    pics = _strip_frames(_light_frame)
    return pics[0], {'frames': pics, 'fps': 4.0, 'clip': 'glow'}


# ================================================================================================
# the Halt
# ================================================================================================
def platform_edge(variant='a', seed=121):
    """One cell of the halt's platform edge, along x: a front of dressed stone in two courses (the
    joints staggered), a coping of one long slab a cell (its lip painted white and worn, its top calm
    and lit, a dark joint at the cell line), the platform's gravel behind as sparse clumped pebbles on
    a calm base; drawn from a run of five cells so neighbours meet, cropped to its own cell. Variant b
    has a chipped corner and a worn patch on its lip."""
    sc = K.Scene(-60, 60, -26, 4, 20)
    sc.box(-60, -24, 0, 60, 0, 12, GRANITE, base=2.6, k=1.4, tag='body', mix=0.3)
    sc.box(-60, -6, 12, 60, 1, 14, GRANITE, base=3.0, k=1.4, tag='coping', mix=0.5, round_=1.0)
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
    course = (z > 6).astype(int)
    fj = ((lx + 12 + course * 12) % 24) == 0                         # one block a cell, staggered a half cell
    t = 2.7 + 0.4 * course + np.round((K.vhash((lx + 12 + course * 12) // 24, course, seed) - 0.5) * 1.0)
    t = np.where(fj | (np.abs(z - 6) < 0.8), 1.0, t)
    t = np.where((z > 5.0) & (z < 6.0) & ~fj, t + 0.8, t)
    t = np.where((z > 11.0) & ~fj, t + 0.8, t)
    t = t - 0.8 * (z < 2.5)
    rpaint(a, front, GRANITE, t, 0.4)
    weed = front & (z < 2.5) & (K.vhash((lx + 12) // 3, 0, seed + 12) > 0.8)
    a[weed] = np.where(z[weed] < 1.5, C('leaf_cool', 2), C('grass_cool', 3))
    # the coping: a calm lit top, the white lip along its front edge, worn where feet go, a joint a cell
    lip = cop & top & (sc.gy > -1.2)
    rpaint(a, cop & top & ~lip, GRANITE, 3.6, 0.4)
    worn = lip & (np.abs(lx - (4 if variant == 'a' else -3)) < (2 if variant == 'a' else 5))
    rpaint(a, lip & ~worn, WHITE, 4.6, 0.0)
    rpaint(a, worn, GRANITE, 3.4, 0.6)
    rpaint(a, cop & ~top, GRANITE, 2.6, 0.4)
    a[cop & (lx == -12)] = C('stone_cool', 1)
    if variant == 'b':
        chip = cop & (lx >= 8) & (lx <= 10) & (sc.gy > -2.5)
        a[chip & top] = C('stone_cool', 2)
    # the gravel behind: a calm base, pebbles in sparse clumps, each lit on top with a dark foot
    gr = body & top & ~cop
    rpaint(a, gr, [('stone_cool', 'stone', 'stone'), ('stone_cool', 'stone_cool', 'stone')], 2.9,
           np.clip(K.vhash((lx + 12) // 6, Yg // 4, seed + 11) * 0.999, 0, 0.999))
    drift = K.noise((H, W), np.random.default_rng(seed), 4.0) > 0.55
    pb = gr & drift & (K.vhash(Xg // 2, Yg // 2, seed + 3) > 0.82)
    ys, xs = np.nonzero(pb & ((Xg % 2) == 0) & ((Yg % 2) == 0))
    for y, x in zip(ys, xs):
        if y + 1 < H and x + 1 < W:
            a[y, x:x + 2] = C('stone', 4)
            a[y + 1, x:x + 2] = C('stone_cool', 2)
    V.tidy(a)
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
    # the roof: slates in staggered courses, each course's lower edge lit, a dark gap under it
    roof = np.zeros((H, W), bool)
    for k in range(nrow):
        m = _tagm(sc, 'roof%d' % k)
        roof |= m
        top = m & (sc.n[..., 2] > 0.5)
        fr = m & ~top
        sl = (Xg - ox + 80 + (k % 2) * 4) // 8                            # the slate's index along its course
        joint = ((Xg - ox + 80 + (k % 2) * 4) % 8) == 0
        hv = K.vhash(sl, k, seed + 3)
        own = np.where(hv > 0.92, 1.0, 0.0)                               # a slate here and there newer and lighter
        t = np.where(fr, 3.4, 2.6) + own * (~fr) + 0.0 * L - np.where(joint & ~fr, 1.2, 0.0) - np.where(joint & fr, 0.8, 0.0)
        t = t + 0.4 * (gx < -36) - 0.4 * (gx > 40) + (0.4 if k < 3 else 0.0)  # the roof's light, west and back
        frow = fr & (np.roll(fr, 1, 0) == 0)
        t = np.where(fr & ~frow, 1.6, t)                                  # the gap under the course's lip
        rpaint(a, m, SLATE, t, np.clip(np.where(K.vhash(sl, k, seed) > 0.85, 0.5, 0.0) + 0.3 * (k % 2), 0, 0.999))
        if k >= nrow - 3:                                                  # moss in a few gaps low on the roof
            mz = fr & ~frow & (K.vhash(sl, k, seed + 9) > 0.8)
            a[mz] = C('leaf_cool', 2)
            mz2 = np.zeros_like(mz)
            mz2[:-1] = mz[1:]
            a[mz2 & m & (K.vhash(sl, k, seed + 10) > 0.4)] = C('grass_cool', 3)
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
    # the valance: a fretted board, scalloped along its lower edge
    val = _tagm(sc, 'valance')
    vys = np.nonzero(val)[0]
    vb = vys.max()
    ph = (Xg - ox + 120) % 6
    cut = val & (((Yg == vb) & np.isin(ph, (4, 5, 0, 1))) | ((Yg == vb - 1) & np.isin(ph, (5, 0))) | ((Yg == vb - 2) & (ph == 5)))
    rpaint(a, val & ~cut, CREAM, 3.8 - 1.0 * ((Yg == vb) | ((Yg == vb - 1) & np.isin(ph, (1, 4)))), 0.2)
    rpaint(a, cut, CREAM, 1.8, 0.0)                                       # the shade behind, through the cut-outs
    hole = val & (ph == 2) & (Yg >= vb - 6) & (Yg <= vb - 5)
    a[hole] = C('ashlar', 1)
    # under the roof: the eave's shadow on the back wall and sides, deepest under the eave
    under = (walls | _tagm(sc, 'leg')) & (z > 0) & (sc.gy < -6)
    V._step(a, under & (z > 36), -1)
    # the bench: boards with a lit lip, dark joints, grain and nail heads
    seat = _tagm(sc, 'seat')
    _planks(a, seat, OAK, 2.9 + 0.8 * L, gx + 200, (Yg - oy).astype(float) + 300, seed + 4, pitch=4)
    br = _tagm(sc, 'backrest')
    _planks(a, br, OAK, 2.7 + 0.6 * L, gx + 200, -z + 300, seed + 5, pitch=5)
    V._step(a, (seat | br) & ((np.abs(gx + 40) < 0.6) | (np.abs(gx - 26) < 0.6)), 1)
    nails = (seat | br) & ((np.abs(gx + 40) < 0.6) | (np.abs(gx - 26) < 0.6)) & (((Yg - oy) % 5) == 2)
    a[nails] = C('iron', 1)
    V._step(a, (seat | br), -1)                                            # in the roof's shade
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
    _finish(a)
    return K.crop(a, ox, oy)


CHURN_TIN = [('slate_cool', 'stone_cool', 'stone'), ('slate_cool', 'stone', 'stone_warm')]


def _churn_profile():
    """A 17-gallon churn's radius from the foot (texels): the foot band, the body, the shoulder band,
    the taper, the neck, the lid's flange and its mushroom crown."""
    p = []
    for h in range(34):
        if h < 2:
            r = 8.2
        elif h < 17:
            r = 7.6
        elif h < 19:
            r = 8.2
        elif h < 23:
            r = 7.6 - (h - 18) * 0.85
        elif h < 27:
            r = 4.2
        elif h < 29:
            r = 5.8
        else:
            r = 5.2 - (h - 29) * 1.0
        p.append(r)
    return p


def churn_stand(seed=125):
    """A milk-churn stand at the lane's end: a deck of boards at cart height (0.65 m) on four posts with
    a cross-brace, three galvanised churns on it waiting for the train, each 0.78 m tall and 0.35 m
    across (Eastward's milk cans in 17), drawn as Eastward draws cans: rolling bands at the foot and
    the shoulder (a lit top line, a dark line under), the shoulder's taper and the neck, a mushroom lid
    with a handle loop, a side handle each side; the tin lit as a cylinder (a highlight band left of
    centre, the core shadow on the right third), never split on a diagonal."""
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
    _planks(a, deck & ~side, OAK, 2.9 + 0.6 * L, gx + 200, (Yg - oy).astype(float) + 300, seed, pitch=4)
    rpaint(a, deck & side, OAK, 2.6, 0.3)
    a[deck & side & (Yg == np.nonzero(deck & side)[0].min())] = C('timber_warm', 4)
    legs = _tagm(sc, 'leg', 'brace')
    for x in (-28, 28):
        m = legs & side & (np.abs(gx - x) < 2)
        rpaint(a, m, OAK, np.where(gx < x - 0.5, 3.4, np.where(gx > x + 0.6, 1.8, 2.6)), 0.3)
    B._lichen(sc, a, tags=('leg',), rate=0.6, seed=seed)
    prof = _churn_profile()
    for k, (x, y) in enumerate(((-19, -4), (0, -2), (19, -4))):
        fx, fy = ox + x, oy + y - 28
        m, hh, u, top = _lathe(a.shape, fx, fy, prof)
        t = _cyl_tone(u, 1.0, lit=4.2, body=3.0, shade=1.6)
        band = ((hh >= 0) & (hh < 2)) | ((hh >= 17) & (hh < 19))
        t = np.where(band & (np.floor(hh) % 17 == 1) | (band & (np.floor(hh) == 18)), t + 0.8, t)
        t = np.where(band & ((np.floor(hh) == 0) | (np.floor(hh) == 17)), t - 1.0, t)
        t = np.where(top, 3.6 + 0.8 * (u < 0) - 0.6 * (u > 0.5), t)
        t = np.where((hh >= 27) & (hh < 29) & ~top, t - 0.4, t)            # the lid's flange in its own shade
        rpaint(a, m, CHURN_TIN, t, 0.3 + 0.4 * (k == 1))
        a[m & ~top & (np.abs(u + 0.36) < 0.09) & (hh > 4) & (hh < 13)] = C('stone', 5)       # the tin's glint
        a[m & ~top & (np.abs(u - 0.2) < 0.12) & (np.abs(hh - 9 - 2 * k) < 1.0)] = C('stone_cool', 1)  # a dent
        # the lid's handle loop, the side handles at the shoulder
        ly = fy - 34
        a[ly, fx - 1:fx + 2] = C('iron', 2)
        a[ly + 1, fx - 1] = C('iron', 1)
        a[ly + 1, fx + 1] = C('iron', 1)
        a[ly, fx - 1] = C('slate', 4)
        for sx in (-1, 1):
            hx = fx + sx * 9
            hy = fy - 20
            a[hy:hy + 3, hx] = C('iron', 2)
            a[hy, hx - sx] = C('iron', 2)
            a[hy + 2, hx - sx] = C('iron', 1)
            if sx < 0:
                a[hy, hx] = C('slate', 4)
    _finish(a)
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
    rpaint(a, base & ~side, GRANITE, 3.4 + 0.4 * L, 0.3)
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
    for r_ in range(6):
        yy = sy0 + 10 + r_ * 4
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
def _wheel_frame(i, seed=141):
    """The mill's south end with its undershot wheel: the mill's rubble gable under a slate roof (its
    west pitch lit, its east in shade, bargeboards along the verge, a loft door in the gable), the
    oak wheel of two rims, sixteen paddles and eight spokes on an iron hub turning a quarter of a
    spoke's pitch a frame, so the cycle wraps at the same step as every other; the race runs under the
    wheel between stone cheeks: dark under the near cheek, the current in lit streaks along the flow
    over their own shadow, spray where the floats dip in and a churned, paler patch downstream, the
    waterline lit along the cheeks."""
    R, D = 34.0, 9.0                                                   # the wheel's radius and width
    sc = K.Scene(-64, 64, -74, 22, 112)
    sc.box(-56, -66, 0, 56, -20, 70, GRIT, base=2.4, k=1.2, tag='wall', mix=0.4)
    for k in range(15):                                                # the roof, stepped to its ridge
        hw = 61 - 4.0 * k
        sc.box(-hw, -70, 70 + 2.2 * k, hw, -16, 70 + 2.2 * (k + 1), SLATE, base=2.6, k=1.2, tag='roof', mix=0.3)
    sc.box(-8, -21, 34, 8, -18, 46, IRON, base=2.2, k=1.8, tag='bearing', round_=1.0, mix=0.4)
    sc.box(-48, -20, 0, -40, 14, 10, GRANITE, base=2.6, k=1.4, tag='chan', round_=1.0, mix=0.4)
    sc.box(40, -20, 0, 48, 14, 10, GRANITE, base=2.6, k=1.4, tag='chan', round_=1.0, mix=0.5)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = (Xg - ox).astype(float)
    side = sc.n[..., 2] < 0.5
    z = sc.depth
    wall = _tagm(sc, 'wall')
    roof = _tagm(sc, 'roof')
    # the gable: rubble courses, each stone lit on top with a dark joint, wet and mossy low down
    _stone_parts(a, wall & side, gx + 100, z, seed, GRIT, 2.7 - 0.8 * (z < 22), lo=7, hi=14, course=7, moss=10.0)
    rpaint(a, wall & ~side, GRIT, 3.6, 0.3)
    # the roof: the gable's triangle in rubble with bargeboards along the verge; slates on the pitches
    gab = roof & side
    _stone_parts(a, gab, gx + 100, z, seed + 1, GRIT, 2.7, lo=7, hi=14, course=7)
    verge = gab & ~(ndi.binary_erosion(gab, structure=np.ones((3, 3)), iterations=1))
    rpaint(a, verge & (Yg < oy - 20 - 70), B.OAK, np.where(gx < 0, 3.4, 2.0), 0.3)
    top = roof & ~side
    row = (Yg - oy) // 3
    sl = np.where(gx < 0, 3.8, 1.9) - np.where(((Yg - oy) % 3) == 2, 0.8, 0.0)
    sl = sl - 1.0 * (((Xg + row * 4) % 7) == 0)
    rpaint(a, top, SLATE, sl, 0.3)
    a[top & (np.abs(gx) < 1.0)] = C('slate_warm', 4)                         # the ridge
    # the loft door in the gable, above the wheel: boards, a lit sill
    dm = (np.abs(gx) < 6) & (Yg >= oy - 20 - 66) & (Yg < oy - 20 - 52)
    _planks(a, dm, B.OAK, 2.2, Xg + 200, Yg + 300, seed + 5, pitch=4, grain=0.0)
    a[(np.abs(gx) < 7) & (Yg == oy - 20 - 52)] = C('ashlar_warm', 4)
    a[dm & (np.abs(gx - 3) < 0.6) & (Yg == oy - 20 - 59)] = C('iron', 3)
    chan = _tagm(sc, 'chan')
    _stone_parts(a, chan & side, gx + 100, z, seed + 2, GRANITE, 2.8, lo=6, hi=9, course=5)
    rpaint(a, chan & ~side, GRANITE, 3.8, 0.3)
    # the race between the cheeks
    ph = i / float(LOOP)
    wy0, wy1 = oy - 6, oy + 14
    water = (Xg >= ox - 40) & (Xg < ox + 40) & (Yg >= wy0) & (Yg < wy1) & ~chan
    wt = np.full((H, W), 2.4)
    wt = np.where(Yg < wy0 + 3, 1.0, wt)                                   # dark under the near cheek
    wt = np.where(Yg >= wy1 - 3, 2.0, wt)
    sl_ = (Xg - ox + 200 - int(ph * 16)) % 16
    lane = ((Yg - wy0) // 3) % 2
    streak = (Yg >= wy0 + 4) & (Yg < wy1 - 3) & (((Yg - wy0) % 3) == 1) & (np.abs(sl_ - 5 - 6 * lane) < 2.5)
    wt = np.where(streak, 3.8, wt)
    under_s = np.zeros_like(streak)
    under_s[1:] = streak[:-1]
    wt = np.where(under_s & ~streak, 1.6, wt)
    churn = (Xg > ox + 4) & (Xg < ox + 30) & (Yg >= wy0 + 3) & (Yg < wy0 + 10)
    wt = np.where(churn & ~streak, wt + 0.8, wt)
    rpaint(a, water, [('water_cool', 'water', 'water_warm')], wt, 0.0)
    a[water & ((Xg == ox - 40) | (Xg == ox + 39))] = C('water_warm', 4)       # the waterline lit along the cheeks
    # the wheel: back rim, paddles back to front, front rim and spokes; a quarter spoke-pitch a frame
    cx, cy = ox, oy - (R + 6) - (-14)
    ang0 = (2 * math.pi / 8) * (i / float(LOOP))
    shape = a.shape
    wheel = np.full(shape, -1, np.int32)

    def ring(dy, r0, r1, t0):
        m = _disc(shape, cx, cy + dy, r1) & ~_disc(shape, cx, cy + dy, r0)
        tt = t0 + 1.0 * ((Xg - cx) + (Yg - cy - dy) < -R * 0.5) - 0.9 * ((Xg - cx) + (Yg - cy - dy) > R * 0.5)
        rpaint(wheel, m, B.OAK, tt, 0.3)
    ring(-D, R - 3.5, R, 1.8)
    for k in range(16):
        th = ang0 + k * 2 * math.pi / 16
        c, s_ = math.cos(th), math.sin(th)
        pp = [(cx + (R - 9) * c, cy + (R - 9) * s_), (cx + (R + 4) * c, cy + (R + 4) * s_),
              (cx + (R + 4) * c, cy + (R + 4) * s_ - D), (cx + (R - 9) * c, cy + (R - 9) * s_ - D)]
        pm = _poly(shape, pp)
        lit = 0.9 if s_ < -0.2 else (-0.6 if s_ > 0.4 else 0.2)
        rpaint(wheel, pm, B.OAK, 2.5 + lit, 0.3 + 0.3 * (k % 2))
        edge = _line(shape, pp[1][0], pp[1][1], pp[2][0], pp[2][1], 1.6)
        wheel[edge] = C('timber_warm', 4) if s_ < 0 else C('timber_cool', 1)
    ring(0, R - 3.5, R, 2.6)
    for k in range(8):
        th = ang0 + k * 2 * math.pi / 8 + math.pi / 16
        c, s_ = math.cos(th), math.sin(th)
        sp = _line(shape, cx + 4 * c, cy + 4 * s_, cx + (R - 3) * c, cy + (R - 3) * s_, 2.2)
        rpaint(wheel, sp, B.OAK, 2.6 + (0.9 if (c < 0 and s_ < 0) else -0.4), 0.4)
    low = (wheel >= 0) & (Yg > cy + R * 0.45)
    V._step(wheel, low, -1)
    slime = low & (K.vhash(Xg // 3, Yg // 2, seed + 7) > 0.8)
    wheel[slime] = C('leaf_cool', 2)
    hub = _disc(shape, cx, cy, 5.5)
    rpaint(wheel, hub, IRON, 2.2 + 1.2 * ((Xg < cx) & (Yg < cy)), 0.3)
    wheel[_disc(shape, cx, cy, 1.8)] = C('void', 2)
    near = chan & (Yg > oy - 14)
    sel = (wheel >= 0) & ~near & ~((Yg > oy - 2) & water)
    a[sel] = wheel[sel]
    # spray where the floats dip in, west of the wheel's foot; it changes with the turn
    for k in range(4):
        x = ox - 18 + k * 7 + (k + i) % 2
        sp = _disc(shape, x, oy - 4 - ((k + i) % 2), 1.6, 1.0) & (water | (a < 0))
        a[sp] = C('snow', 4) if (k + i) % 2 else C('water_warm', 5)
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
    # the handwheel on the rack's head, face on: rim, four spokes, hub
    hx, hy = sc.ox + 4, sc.oy - 4 - 44
    rimm = _disc(a.shape, hx, hy, 6.0) & ~_disc(a.shape, hx, hy, 4.4)
    for k in range(10):                                                  # the gear's teeth
        th = k * 2 * math.pi / 10
        rimm |= _disc(a.shape, hx + 6.6 * math.cos(th), hy + 6.6 * math.sin(th), 1.2)
    lit_g = (Xg - hx) + (Yg - hy) < -1
    rpaint(a, rimm, IRON, np.where(lit_g, 3.8, 2.0), 0.3)
    for (dx, dy) in ((1, 0), (0, 1)):
        a[_line(a.shape, hx - 4.5 * dx, hy - 4.5 * dy, hx + 4.5 * dx, hy + 4.5 * dy, 1.4)] = C('iron', 2)
    a[_disc(a.shape, hx, hy, 1.8)] = C('iron', 4)
    a[int(hy) - 1, int(hx) - 1] = C('slate', 5)
    # the water: dark in the channel, pouring white from under the gate
    wx0, wx1 = sc.ox - 14, sc.ox + 14
    water = (Xg >= wx0) & (Xg < wx1) & (Yg >= sc.oy - 6) & (Yg < sc.oy + 14) & ~_tagm(sc, 'pier', 'gate')
    st = ((Xg + Yg // 3) % 7) < 2
    rpaint(a, water, [('water_cool', 'water', 'water_warm'), ('water_cool', 'water_cool', 'water')], 1.8 + 0.9 * st + 0.7 * ((Yg - sc.oy) > 6),
           ((Xg // 5) % 2) * 0.6)
    foam = water & (Yg < sc.oy - 2) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.4)
    a[foam] = C('snow', 4)
    a[water & (Yg >= sc.oy - 2) & (Yg < sc.oy) & ((Xg % 3) < 2)] = C('water_warm', 5)
    _finish(a, keep=foam)
    return K.crop(a, sc.ox, sc.oy)


SACK = [('earth_cool', 'sand_cool', 'sand'), ('earth_cool', 'sand_cool', 'sand_warm')]


def _dressing(px, py, harps=8, pitch=4.0):
    """A millstone's dressing on its face (px, py from its centre, unsquashed): eight harps of
    furrows, each furrow parallel to its harp's leading line. Returns (furrow, lit lip south of it)."""
    th = np.arctan2(py, px) + math.pi
    rho = np.hypot(px, py)
    j = np.floor(th / (2 * math.pi / harps))
    lead = j * (2 * math.pi / harps)
    d = rho * np.sin(th - lead)
    f = (np.mod(d, pitch) < 1.0) & (rho > 6)
    lip = (np.mod(d, pitch) >= 1.0) & (np.mod(d, pitch) < 2.0) & (rho > 6)
    return f, lip


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
    band = _disc(a.shape, cx + 4, cy - 2, R) & ~face
    rpaint(a, band, GRANITE, np.where(Yg < cy - R * 0.4, 3.9, np.where(Xg > cx + R * 0.5, 1.8, 2.8)), 0.3)
    px, py = Xg - cx + 0.5, Yg - cy + 0.5
    rho = np.hypot(px, py)
    ft = 2.9 + 0.5 * ((px + py) < -10) - 0.5 * ((px + py) > 14)
    edge = rho > R - 2.2
    ft = np.where(edge & ((px + py) < 0), 3.9, np.where(edge, 2.0, ft))
    f, lip = _dressing(px, py)
    ft = np.where(f & ~edge, ft - 1.2, np.where(lip & ~edge, ft + 0.7, ft))
    rpaint(a, face, GRANITE, ft, 0.4)
    eye = _disc(a.shape, cx, cy, 4.5)
    a[eye] = C('void', 1)
    a[eye & (py < -1)] = C('stone_cool', 2)
    # the stone lying flat: a lathe of 10 texels, its face seen squashed (0.55)
    sq = 0.55
    fx, fy = ox - 30, oy - 13
    prof = [R] * 10
    m, hh, u, top = _lathe(a.shape, fx, fy, prof, sq)
    t = _cyl_tone(u, 1.0, lit=3.9, body=2.8, shade=1.6)
    qx, qy = Xg - fx + 0.5, (Yg - (fy - 9) + 0.5) / sq
    qr = np.hypot(qx, qy)
    tf = 2.9 + 0.4 * ((qx + qy) < -12) - 0.4 * ((qx + qy) > 16)
    bev = qr > R - 3.0
    tf = np.where(bev & ((qx + qy) < 0), 3.9, np.where(bev, 2.1, tf))
    f2, lip2 = _dressing(qx, qy)
    tf = np.where(f2 & ~bev, tf - 1.2, np.where(lip2 & ~bev, tf + 0.7, tf))
    t = np.where(top, tf, t)
    rpaint(a, m, GRANITE, t, 0.4)
    eye2 = m & top & (np.hypot(qx, qy) < 4.8)
    a[eye2] = C('void', 1)
    a[eye2 & (qy < -1)] = C('stone_cool', 2)                                 # the eye's far wall, lit
    a[m & ~top & (K.vhash(Xg // 3, 0, seed) > 0.8) & (hh < 2)] = C('leaf_cool', 2)  # moss at its foot
    flour = (a < 0) & (Yg > oy - 4) & (Yg < oy + 4) & (np.abs(Xg - ox - 44) < 10) & (K.vhash(Xg // 2, Yg // 2, seed) > 0.55)
    _finish(a)
    a[flour & (a < 0)] = C('plaster', 4)
    B._ground_tufts(a, ox, oy, [-58, -54, 60, 63], seed)
    return K.crop(a, ox, oy)


def _log2d(a, x0, x1, yc, r, seed, broken='e', stubs=(), bark='birch'):
    """A fallen trunk lying along x, painted as a cylinder seen from above and the south: its top band
    lit, the body, the underside in shade; birch bark with lenticel dashes following the curve; at the
    broken end the pale end grain in rings; branch stubs on its top. yc is its axis' screen row."""
    H, W = a.shape
    band = int(round(2 * r))
    m = np.zeros((H, W), bool)
    for x in range(int(x0), int(x1)):
        for j in range(band):
            y = int(yc - r + j)
            if 0 <= y < H and 0 <= x < W:
                m[y, x] = True
    Yg, Xg = np.mgrid[0:H, 0:W]
    v = (Yg - (yc - r)) / max(1.0, 2 * r - 1)                         # 0 at the top of the band, 1 under it
    if bark == 'birch':
        code = np.where(v < 0.2, C('snow', 5), np.where(v < 0.42, C('snow', 4), np.where(v < 0.62, C('snow_cool', 3),
                        np.where(v < 0.8, C('ash', 3), np.where(v < 0.92, C('ash', 2), C('ash', 1))))))
        a[m] = code[m]
        seg = Xg // 4
        dash = m & (v > 0.18) & (v < 0.78) & (K.vhash(seg, Yg // 2, seed) > 0.62) & ((Xg % 4) < 3)
        a[dash] = np.where(v[dash] < 0.45, C('ash', 3), C('void', 2))    # the lenticels, across the trunk
        mark = m & (v > 0.25) & (v < 0.85) & (K.vhash(Xg // 5, 0, seed + 4) > 0.72) & ((Xg % 5) < 3)
        a[mark] = C('void', 1)                                          # the dark bark scars
        peel = m & (v < 0.3) & (K.vhash(Xg // 3, 1, seed + 6) > 0.85)
        a[peel] = C('sand_warm', 4)                                     # bark peeling to its warm underlayer
    else:
        rpaint(a, m, B.OAK, np.where(v < 0.22, 4.2, np.where(v < 0.62, 3.0, np.where(v < 0.85, 2.0, 1.2))), 0.3)
    ex = int(x1) if broken == 'e' else int(x0) - 1
    end = _disc(a.shape, ex + 0.5, yc, 2.2, r)
    rpaint(a, end, [('timber', 'sand_cool', 'sand')], 4.0 - 1.0 * (np.hypot(Xg - ex, (Yg - yc) * 2.2 / r) > 1.4), 0.0)
    a[end & (np.abs(np.hypot((Xg - ex - 0.5), (Yg - yc) * 2.2 / r) - 1.2) < 0.4)] = C('sand_cool', 3)   # a ring
    for k in range(3):                                                  # splinters past the break
        sy = int(yc - r + 1 + k * 3)
        if 0 <= sy < H and 0 <= ex + 2 + (k % 2) < W:
            a[sy, ex + 2:ex + 3 + (k % 2)] = C('sand_cool', 4)
    for sx in stubs:                                                    # branch stubs on its top, lit west
        yb = int(yc - r)
        a[yb - 3:yb, sx] = C('snow', 4)
        a[yb - 3:yb, sx + 1] = C('ash', 2)
        a[yb - 4, sx + 1] = C('snow_cool', 3)
    return m


def landslip(seed=147):
    """The Millrace landslip (way W3), 6 m across: a tongue of earth come down across the road from the
    hillside, its crown lit and its front in shade, the torn lip along its uphill edge (raw earth under
    an overhang of turf), clods in drifts, its toe dark and wet; boulders carried in it, each lit on
    its crown with a dark underside and a contact shadow on the earth; a birch snapped and lying across,
    a cylinder of bark with its lenticels, its broken end showing pale end grain and two branch stubs;
    its crown of twigs at the west end."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-72, 72, -44, 24, 70)
    sc.ellipsoid(0, -12, 0, 62, 28, 20, EARTH, base=2.6, k=1.6, tag='earth', mix=0.3, flat=1.25)
    sc.ellipsoid(-32, 4, 0, 30, 14, 9, EARTH, base=2.5, k=1.6, tag='earth', mix=0.6, flat=1.25)
    sc.ellipsoid(34, 6, 0, 26, 12, 8, EARTH, base=2.5, k=1.6, tag='earth', mix=0.5, flat=1.25)
    stones = []
    for k in range(14):
        x, y = rng.uniform(-52, 52), rng.uniform(-24, 12)
        if -46 < x < 32 and abs(y - 2) < 9:
            continue
        sz = rng.uniform(5.0, 9.5) if k < 8 else rng.uniform(2.2, 3.5)
        zt = max(0.0, 20 * math.sqrt(max(0.0, 1 - ((x / 62) ** 2 + ((y + 12) / 28) ** 2))))
        stones.append((x, y, sz))
        sc.ellipsoid(x, y, zt * 0.85 + sz * 0.35, sz, sz * 0.75, sz * 0.65, GRIT, base=2.7, k=1.4, tag='stone', mix=rng.random(), flat=1.6)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    L = sc.light()
    earth = _tagm(sc, 'earth')
    gy = sc.gy
    # the earth in planes: the crown lit, the front in shade, the wet toe dark
    et = np.where(L > 0.3, 3.8, np.where(L > -0.1, 2.8, 1.9))
    et = np.where(sc.depth < 3.5, 1.3, et)
    rpaint(a, earth, EARTH, et, _sibling_mix(a.shape, Xg, Yg, seed, 5.0, (3, 3)))
    _clods(a, earth & (sc.depth > 4), Xg, Yg, seed, rate=0.07)
    wet = earth & (sc.depth < 2.5) & (K.vhash(Xg // 4, Yg // 2, seed + 3) > 0.9)
    a[wet] = C('water_cool', 2)                                             # a glint of water in the wet toe
    # the torn lip at the head: turf hanging over raw earth along the uphill edge
    head = earth & (gy < -20) & (sc.depth > 6)
    lay = ((Yg // 2) % 3 == 0)
    rpaint(a, head, [('soot', 'earth_cool', 'earth_warm'), ('soot', 'clay_cool', 'earth')], 1.4 + 0.9 * lay + 0.6 * (L > 0.2), 0.3)
    lip = np.zeros_like(head)
    lip[:-2] = head[2:] & ~head[:-2]
    lip &= (a >= 0) | head
    hys, hxs = np.nonzero(head)
    for x in np.unique(hxs):
        y0 = hys[hxs == x].min()
        for j, tt in ((0, ('grass', 4)), (1, ('grass_cool', 3)), (2, ('leaf_cool', 2))):
            if 0 <= y0 + j < H:
                a[y0 + j, x] = C(*tt)
        if y0 + 3 < H and head[y0 + 3, x]:
            a[y0 + 3, x] = C('earth_cool', 1)
    # the stones: lit crowns, dark undersides, a contact shadow on the earth under each
    st = _tagm(sc, 'stone')
    stt = np.where(L > 0.45, 4.0, np.where(L > -0.1, 2.9, 1.8))
    rpaint(a, st, GRIT, stt, _sibling_mix(a.shape, Xg, Yg, seed + 4, 4.0, (3, 3)))
    below = np.zeros_like(st)
    below[1:] = st[:-1]
    below2 = np.zeros_like(st)
    below2[2:] = st[:-2]
    V._step(a, (below | below2) & earth & ~st, -1)
    B._lichen(sc, a, tags=('stone',), rate=0.5, seed=seed)
    _finish(a)
    # the birch's crown at the west: twigs fanning from the trunk, leaves in small clumps at their ends
    for k in range(7):
        ang = math.pi * (0.6 + 0.8 * hsh(seed, k, 1))
        ln = 10 + 10 * hsh(seed, k, 2)
        x2, y2 = ox - 48 + ln * math.cos(ang), oy - 13 - ln * math.sin(ang) * 0.6
        tw = _line(a.shape, ox - 47, oy - 13 + (k % 3) - 1, x2, y2, 1.0)
        a[tw] = C('timber_cool', 1)
        lv = _disc(a.shape, x2, y2, 2.2, 1.6)
        rpaint(a, lv, [('leaf_cool', 'grass_warm', 'brass')], 3.0 + 1.0 * (Yg < y2) + 0.8 * (Xg < x2), 0.0)
    log = _log2d(a, ox - 48, ox + 18, oy - 14, 5.5, seed, broken='e', stubs=(ox - 30, ox - 4))
    lo = np.zeros_like(log)
    lo[1:] = log[:-1]
    V._step(a, lo & ~log & (a >= 0), -1)                                   # its shadow on the earth
    a[log & ~ndi.binary_erosion(log, iterations=1)] = np.where(Yg[log & ~ndi.binary_erosion(log, iterations=1)] > oy - 13, C('ash', 1), a[log & ~ndi.binary_erosion(log, iterations=1)])
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


BARROW_TURF = [('leaf_cool', 'grass_cool', 'grass'), ('leaf_cool', 'grass', 'grass_warm'), ('leaf_cool', 'grass_cool', 'grass_cool')]


def barrow_entrance(seed=161):
    """Old Fang's barrow from the south: a long turf mound 7.4 m long and 2 m high, lit in bands (the
    crown at the upper left, the body, the east and lower flanks), sparse clumped tufts on its crown;
    set into its front a portal Bramble can walk into (0.95 x 1.8 m): two jamb stones and a lintel,
    each lit on its top-left plane with a dark east face, moss only in their joints; the passage
    recedes, its east reveal lit and the dark deepening to black within 8 texels, a threshold slab at
    its foot; a forecourt of set stones curving away either side; a blocking stone rolled aside."""
    rng = np.random.default_rng(seed)
    sc = K.Scene(-170, 170, -96, 20, 104)
    sc.ellipsoid(0, -46, 0, 160, 46, 96, BARROW_TURF, base=2.7, k=1.6, tag='mound', mix=0.3, flat=1.15)
    sc.box(-30, -9, 0, -21, 0, 80, GRIT, base=2.6, k=1.4, tag='jamb_w', round_=2.0, mix=0.3)
    sc.box(21, -9, 0, 30, 0, 80, GRIT, base=2.6, k=1.4, tag='jamb_e', round_=2.0, mix=0.6)
    sc.box(-36, -11, 80, 36, 0, 93, GRIT, base=2.8, k=1.4, tag='lintel', round_=3.0, mix=0.4)
    sc.box(-21, -9, 0, 21, 0, 2.5, GRIT, base=2.9, k=1.4, tag='sill', mix=0.5)
    forecourt = []
    for k, ang in enumerate(np.linspace(0.35, 1.2, 4)):
        for sgn in (-1, 1):
            x = sgn * (42 + 70 * math.sin(ang)) + rng.uniform(-2, 2)
            y = 2 - 20 * (1 - math.cos(ang))
            h = 16 - k * 2.5 + rng.uniform(-2, 2)
            w = rng.uniform(6.0, 8.0)
            forecourt.append((x, y))
            sc.ellipsoid(x, y, h * 0.5, w, 4.5, h * 0.62, GRIT, base=2.6, k=1.4, tag='set', mix=rng.random(), flat=1.7)
    sc.ellipsoid(52, 14, 8, 10, 7, 9, GRIT, base=2.7, k=1.6, tag='block', mix=0.5, flat=1.5)
    a = _shade(sc, crevice=1.0, rim=0.6)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    gx = Xg - ox
    z = sc.depth
    L = sc.light()
    side = sc.n[..., 2] < 0.5
    # the turf: the dome lit in three bands, a calm sibling drift, tufts in sparse clumps on the crown
    mound = _tagm(sc, 'mound')
    wob = (K.noise((H, W), rng, 4.0) - 0.5) * 0.5                           # the bands' edges organic, not ruled
    band = np.where(L + wob > 0.45, 4.0, np.where(L + wob > -0.05, 3.0, 2.0))
    mt = band - 0.6 * (z < 6)
    rpaint(a, mound, [('leaf_cool', 'grass_cool', 'grass'), ('leaf_cool', 'grass', 'grass'), ('leaf_cool', 'grass_cool', 'grass_cool')], mt,
           _sibling_mix(a.shape, Xg, Yg, seed, 6.0, (4, 3)))
    _turf_masses(a, mound, L + wob, seed, cell=(13, 10))
    _turf_tufts(a, mound & (z > 4), L + wob, seed, density=0.012, rng=rng)
    fl = mound & (K.vhash(Xg // 2, Yg // 2, seed + 6) > 0.992) & (z > 20)
    a[fl] = np.where((Xg[fl] % 2) == 0, C('brass', 4), C('snow_warm', 4))
    # the stones: lit top-left planes, a body, dark east faces; moss only where they meet
    for tag in ('jamb_w', 'jamb_e', 'lintel', 'sill', 'set', 'block'):
        m = _tagm(sc, tag)
        if not m.any():
            continue
        st = np.where(~side, 3.8 + 0.3 * L, 2.8 + 0.8 * (L > 0.3) - 0.8 * (L < -0.2))
        rpaint(a, m, GRIT, st, _sibling_mix(a.shape, Xg, Yg, seed + 3, 4.0, (3, 3)))
    for tag, x0, x1 in (('jamb_w', -30, -21), ('jamb_e', 21, 30)):
        m = _tagm(sc, tag) & side
        a[m & (gx == x0)] = C('ashlar_warm', 4)
        V._step(a, m & (gx >= x1 - 2), -1)
    lint = _tagm(sc, 'lintel')
    lys = np.nonzero(lint & side)[0]
    a[lint & side & (Yg == lys.min())] = C('ashlar_warm', 4)                # the lintel's lit lip
    a[lint & side & (Yg == lys.max())] = C('stone_cool', 1)
    crack = _line(a.shape, ox - 6, lys.min() + 2, ox - 2, lys.max() - 1, 1.0) & lint
    a[crack] = C('stone_cool', 1)
    jt = np.zeros((H, W), bool)                                              # moss in the joints, nowhere else
    for tag in ('jamb_w', 'jamb_e'):
        m = _tagm(sc, tag)
        ys_ = np.nonzero(m)[0]
        jt |= m & (Yg <= ys_.min() + 1)
    a[jt & (K.vhash(Xg, 0, seed + 8) > 0.4)] = C('leaf_cool', 2)
    B._lichen(sc, a, tags=('set', 'block', 'jamb_w', 'jamb_e'), rate=0.7, seed=seed)
    # the passage: the dark deepening to black within 8 texels, the east reveal lit, a threshold slab
    px0, px1 = ox - 21, ox + 21
    py1 = oy - 3
    py0 = lys.max() + 1
    pas = (Xg >= px0) & (Xg < px1) & (Yg >= py0) & (Yg < py1)
    dx = np.minimum(Xg - px0, px1 - 1 - Xg)
    dy = Yg - py0
    d = np.minimum(dx, dy)
    pt = np.clip(2.0 - d / 3.0, 0, 2)
    rpaint(a, pas, [('void', 'void', 'void')], pt, 0.0)
    reveal = pas & (Xg >= px1 - 4) & (Yg > py0 + 1)
    rpaint(a, reveal, [('soot', 'stone_cool', 'stone')], np.where(Xg >= px1 - 2, 2.6, 1.6), 0.0)
    a[pas & (Yg >= py0) & (Yg < py0 + 2)] = C('void', 1)                     # the lintel's shadow inside
    floor = pas & (Yg >= py1 - 6)
    rpaint(a, floor, [('void', 'soot', 'stone_cool')], np.where(Yg >= py1 - 2, 2.0, 1.0), 0.0)
    sill = _tagm(sc, 'sill')
    a[sill & ~side] = C('stone', 4)
    _finish(a, keep=pas)
    B._ground_tufts(a, ox, oy, [-150, -141, -120, -95, 95, 118, 140, 151], seed)
    return K.crop(a, ox, oy)


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
    """A kerb stone of the barrow's ring: a boulder set on edge in the turf, its silhouette irregular
    (two lobes), carried in planes (the top-left plane lit, the front mid, the east flank dark), one
    crack, lichen in rosettes, moss in the low joint where it meets the turf; three shapes."""
    w, h, d, lx, lh = {'a': (9, 15, 5, 3.5, 0.65), 'b': (12, 11, 6, -4.0, 0.75), 'c': (7, 18, 5, 2.5, 0.55)}[variant]
    sc = K.Scene(-20, 20, -10, 10, 30)
    vs = seed + ord(variant)
    sc.ellipsoid(0, 0, h * 0.5, w, d, h * 0.55, GRIT, base=2.7, k=1.4, tag='stone', mix=0.3, flat=1.8)
    sc.ellipsoid(lx, -1, h * lh, w * 0.62, d * 0.9, h * 0.42, GRIT, base=2.7, k=1.4, tag='stone', mix=0.6, flat=1.8)
    a = _shade(sc, crevice=1.0, rim=0.6)
    st = _tagm(sc, 'stone')
    _boulder_planes(sc, a, st, vs)
    H, W = a.shape
    Yg, Xg = np.mgrid[0:H, 0:W]
    ox, oy = sc.ox, sc.oy
    ys, xs = np.nonzero(st)
    top, bot = ys.min(), ys.max()
    cx = int(np.median(xs))
    crack = _line(a.shape, cx - 1 + int(3 * hsh(vs, 1)), top + 3, cx + 1 - int(3 * hsh(vs, 2)), top + 3 + h // 2, 1.0) & st
    a[crack] = C('stone_cool', 1)
    lit = np.zeros_like(crack)
    lit[:, :-1] = crack[:, 1:]
    a[lit & st & ~crack] = C('ashlar_warm', 4)
    for k in range(2 + int(2 * hsh(vs, 3))):
        rx = int(xs.min() + 2 + (xs.max() - xs.min() - 4) * hsh(vs, k, 4))
        ry = int(top + 2 + (h * 0.6) * hsh(vs, k, 5))
        _rosette(a, st, rx, ry, ('brass_warm', 4) if k % 2 == 0 else ('snow_cool', 3))
    moss = st & (Yg >= bot - 1) & (K.vhash(Xg // 2, 0, vs) > 0.35)
    a[moss] = np.where(Yg[moss] == bot, C('leaf_cool', 2), C('grass_cool', 3))
    _finish(a)
    B._ground_tufts(a, ox, oy, [-w - 1, w + 1], vs)
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
    # the lifts: long boards with a lit lip and a joint, lit west; each skirt's lower edge lit, dark under
    for k in range(3):
        lf = _tagm(sc, 'lift%d' % k)
        _planks(a, lf & side, WHITE, 3.2 + 0.6 * (gx < -6) - 0.8 * (gx > 7), gx + 200, -(z - 10 - k * LH) + 40, seed + k, pitch=6,
                grain=0.0, joint=0.7)
        sk = _tagm(sc, 'skirt%d' % k)
        sys_ = np.nonzero(sk & side)[0]
        t = np.where(Yg == sys_.max(), 4.4, 3.4) + 0.5 * (gx < -6) - 0.8 * (gx > 8)
        rpaint(a, sk & side, WHITE, t, 0.3)
        rpaint(a, sk & ~side, WHITE, 4.4, 0.3)
        under = np.zeros_like(sk)
        under[1:2 + 0] = False
        sh = np.zeros_like(sk)
        sh[1:] = (sk & side)[:-1]
        V._step(a, sh & ~sk, -1)
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
    # the entrance under the porch, the landing board's lit top
    ent = (np.abs(gx) < 7) & (Yg >= oy + 2 - 12) & (Yg < oy + 2 - 10) & _tagm(sc, 'lift0')
    a[ent] = C('void', 1)
    bd = _tagm(sc, 'board')
    a[bd & ~side] = C('snow', 5)
    _streaks(a, _tagm(sc, 'lift0', 'lift1', 'lift2') & side, Xg, Yg, seed, rate=0.01, length=(3, 5), fam='snow_cool', step=-1)
    _finish(a)
    for (bx, by) in ((ox - 4, oy - 17), (ox + 6, oy - 20)):                  # two bees by the board
        a[by, bx:bx + 2] = C('lamp', 3)
        a[by + 1, bx:bx + 2] = C('void', 2)
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
    tt = tt - 1.0 * (((np.floor(ang * 18).astype(int)) % 3) == 0) * (ht > hz0 + 1)
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
        note='Three oak posts and a rail with a net hung in folds, corks on its head rope, two glass floats, its tail coiled.')
    add('coast_lobster_pots', [('a', lambda: lobster_pots('a')), ('b', lambda: lobster_pots('b'))], name='Lobster pots',
        purpose='store', role='store', cells=(2, 1), fp=_fp(2, 1),
        collision={'shape': 'rect', 'rect': [-7.0, -3.0, 14, 4]}, shadow=(16, 3), composition='cluster',
        requires=[_rel('near', 'water', 3, 'creels stacked on the quay between trips')], forbids=[OFF_WATER],
        size_class='crate_stack (a creel 0.5 m long, 0.3 m high; three stacked 0.6 m; art px: 18 to 48 tall, 40 to 56 wide)',
        eastward=EW_COAST,
        note='Woven withy creels on timber bases with hoops and mouths: three stacked (a), or one with its rope coil and float (b).')
    add('coast_mooring_bitt', [('still', lambda: mooring_bitt())], name='Mooring bitt', purpose='contain', role='mooring',
        cells=(2, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-2.5, -2.5, 5, 4]}, shadow=(8, 2), composition='edge',
        requires=[_rel('near', 'water', 1, 'on the quay\'s edge, where a boat\'s line is made fast')], forbids=[OFF_WATER],
        size_class='mooring bitt (0.45 m, its line coiled beside it; art px: 16 to 26 tall, 32 to 50 wide)', eastward=EW_COAST,
        note='A cast-iron bitt on a bolted plate, a hawser made fast round its waist and the rest flaked in a coil.')
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
        note='A white cast-iron column on a granite plinth, a red lantern with its cap, vent and finial; it glows (8 frames).')
    # the Halt
    add('halt_platform_edge', [('a', lambda: platform_edge('a')), ('b', lambda: platform_edge('b'))], name='Platform edge',
        purpose='cross', role='platform', cells=(1, 1), fp=[[0, -1]], collision={'shape': 'none'}, shadow=None, blocks=False,
        composition='edge', requires=[_rel('near', 'route', 3, 'the platform runs beside the lane the halt serves')],
        forbids=[OFF_WATER], size_class='platform (a 0.3 m front and its coping, the gravel behind; art px: 30 to 44 tall, 24 to 24 wide)',
        eastward=EW_HALT,
        note='One cell of the platform\'s edge along x: two dressed courses, a coping slab with a worn white lip, gravel; cells meet.')
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
        note='A board deck on four posts, three galvanised churns with bands, shoulders, necks, lids and handles.')
    add('halt_semaphore', [('still', lambda: semaphore())], name='Semaphore signal', purpose='guide', role='signal',
        cells=(2, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-2.0, -2.0, 4, 4]}, shadow=(8, 3), composition='edge',
        requires=[_rel('near', 'route', 3, 'at the platform\'s end, where the driver sees it')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='signal (a semaphore post 3 m; art px: 125 to 160 tall, 30 to 50 wide)', eastward=EW_HALT,
        note='A three-tone post with cap and finial, the red arm at danger, its spectacle cast with it, a ladder beside.')
    add('halt_platform_lamp', [('still', lambda: platform_lamp())], name='Platform lamp', purpose='light', role='lamp',
        cells=(1, 1), fp=_fp(1, 1), collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 3]}, shadow=(6, 2), composition='edge',
        requires=[_rel('near', 'route', 5, 'along the platform, lighting the way from the lane to the train')], forbids=[OFF_ROUTE, OFF_WATER],
        size_class='lamp (a platform lamp 2.9 m; art px: 107 to 178 tall, 15 to 28 wide)', eastward=EW_HALT,
        note='A green column on a fluted foot, a ladder bar, a lantern of two panes lit from inside (8 frames), a domed cap.')
    add('halt_timetable_board', [('still', lambda: timetable_board())], name='Timetable board', purpose='guide', role='notice',
        cells=(3, 1), fp=_fp(2, 1), collision={'shape': 'rect', 'rect': [-7.0, -1.0, 14, 2]}, shadow=(16, 3), composition='edge',
        requires=[_rel('near', 'route', 2, 'by the platform\'s entrance from the lane')], forbids=[OFF_ROUTE, OFF_WATER],
        extra={'provides': ['feature']},
        size_class='notice board (2.2 m; art px: 81 to 126 tall, 44 to 89 wide)', eastward=EW_HALT,
        note='A printed sheet behind glass (a header with a train and a clock, rows of print, a notice pinned askew) under a gabled hood.')
    # the Millrace
    add('mill_wheel', [('still', lambda: mill_wheel())], name='Mill and wheel', purpose='work', role='wheel', cells=(5, 4),
        fp=_fp(5, 3), collision={'shape': 'rect', 'rect': [-19.0, -22.0, 38, 22]}, shadow=None, composition='edge',
        requires=[_rel('near', 'water', 2, 'the wheel sits in the race that drives it')], forbids=[OFF_ROUTE],
        extra={'provides': ['feature', 'water', 'view']},
        size_class='mill (the mill\'s south end, 1.6 m to its eaves and a 2.3 m gable; the wheel 1.6 m across; art px: 175 to 205 tall, 115 to 135 wide)',
        eastward=EW_MILL,
        note='The mill\'s gable under a slate roof with its loft door; the undershot wheel turning in its race (8 frames).')
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
        note='Earth come down across the road: a torn turf lip, clods, shaded boulders, a snapped birch with its end grain.')
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
        note='A turf mound in masses with a portal of jambs and a lintel, the passage receding, set stones either side.')
    add('barrow_kerb', [('a', lambda: kerb_stone('a')), ('b', lambda: kerb_stone('b')), ('c', lambda: kerb_stone('c'))],
        name='Kerb stone', purpose='mark', role='marker', cells=(1, 1), fp=_fp(1, 1),
        collision={'shape': 'rect', 'rect': [-3.0, -1.5, 6, 3]}, shadow=(8, 2), composition='cluster',
        requires=[_rel('near', 'barrow_entrance', 4, 'a stone of the ring round the barrow\'s foot')], forbids=NATURE,
        size_class='kerb stone (0.35 to 0.45 m set on edge; art px: 16 to 28 tall, 14 to 30 wide)', eastward=EW_RURAL,
        note='A boulder set on edge in the turf, carried in planes, with a crack, lichen rosettes and moss at its foot; three shapes.')
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

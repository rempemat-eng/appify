"""Hale's hurdle barricade for a raid's pads (game-design.md 7.6; world/raid_barricade.gd).

    python3 -m scripts.art.kit.hurdles            # the pictures and their sheet of anchors
    python3 -m scripts.art.kit.hurdles --check    # exit 1 if a committed picture is not what this draws

Matt, 13 Nov, on the placeholder (posts and rails drawn in code): "what are those brown things on the
track?" A hurdle is a woven wattle panel, the kind used for sheep pens: hazel rods woven between upright
stakes, chest high (42 texels to the binding; the kit's wattle fence, fences.py, whose weave this
draws with). A pad's barricade is a run of them across the road from wall to wall. The first night's
road runs east to west, so the run stands north to south, up the screen, and a wall seen that way
shows only its top in the house's view (the kit's own north-south wattle is a thin line). So the
hurdles stand as free-standing hurdles do, in a zigzag: four panels folded like a screen, each turned
half towards the eye, so every woven face shows, the west-facing ones lit and the east-facing ones in
shade, with a post driven into the road at each fold, its cut top pale. The zigzag is 12 world px deep
round the pad's line; the barricade's solid stays the pad's own 6.

Three pictures, one frame and one foot (the pad's middle, on the ground):
  hurdle_standing   the run whole
  hurdle_battered   pushed east and sagging: the posts lean, one is snapped, the weave is burst in three
                    places with the rods' pale broken ends showing (from half health down)
  hurdle_broken     the posts' stumps, two panels thrown flat across the road to the east and the
                    rods of the others scattered: wreckage that lies on the road (drawn under everyone)
`hurdle.json` gives the frame, the foot and each picture's ground line and height for its contact
shadow, which the game lays by the one sun (data/sun.json), as it did for the placeholder.

Sizes are texels at density 3 for a 48 world px span (the first night's pads). Colours are the house
palette's (the kit fence's hazel ramps); the outline is the house outline. Deterministic.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.kit import fences as FN
from scripts.art.kit.fences import C, HAZEL, HAZELS, ramp, ramp_mix
from scripts.art.kit.schema import ROOT
from scripts.art.native import village as V
from scripts.art.native.palette import to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'raid')
SPAN = 144            # texels across the road (48 world px)
PANEL = 42            # texels up to the binding
POST = 54             # texels to a post's cut top
FOLD = 18             # texels each fold stands east or west of the pad's line
PANELS = 4
W, H = 96, 216        # the frame
AX, AY = 30, 134      # the pad's middle in the frame


def joints():
    """The folds, north to south: (x, y) texels from the pad's middle. The run starts and ends on the west."""
    step = SPAN / PANELS
    return [((-FOLD if i % 2 == 0 else FOLD), -SPAN / 2.0 + i * step) for i in range(PANELS + 1)]


def _down(codes, k=1):
    """Codes k tones down their own ramps (a face turned from the light)."""
    codes = np.asarray(codes)
    return np.where(codes >= 0, (codes // 8) * 8 + np.maximum(codes % 8 - k, 0), codes)


def _panel(a, pa, pb, seed, lean=0.0, sag=0.0, holes=(), shade=False):
    """One hurdle between two folds: its woven face (fences.wattle_front along the panel), column by
    column from the north. `lean` texels of its top pushed east, `sag` texels its middle drops; `holes`
    are bursts in the weave, (s0, s1, z0, z1) along the panel and up it."""
    (xa, ya), (xb, yb) = pa, pb
    length = math.hypot(xb - xa, yb - ya)
    face = FN.wattle_front(PANEL, seed)
    n = int(abs(xb - xa))
    cols = sorted(range(n + 1), key=lambda k: ya + (yb - ya) * k / n)
    gone = np.zeros(a.shape, bool)
    for k in cols:
        t = k / n
        x, gy = xa + (xb - xa) * t, ya + (yb - ya) * t
        s = t * length
        drop = int(round(sag * math.sin(math.pi * t)))
        zs = np.arange(0, PANEL - drop)
        codes = np.asarray(face(np.full(zs.shape, s + 6.0), zs + drop * (zs > PANEL - 6)))
        # the binding rides down with the sag
        codes = np.where(zs >= PANEL - drop - 3, np.asarray(face(np.full(zs.shape, s + 6.0), zs + drop)), codes)
        if shade:
            codes = np.where(codes % 8 >= 3, _down(codes, 2), _down(codes, 1))     # turned from the light
        for z, c in zip(zs, codes):
            xs = int(round(AX + x + lean * z / PANEL))
            r = int(round(AY + gy - z))
            if not (0 <= r < a.shape[0] and 0 <= xs < a.shape[1]):
                continue
            if any(s0 <= s < s1 and z0 <= z < z1 for (s0, s1, z0, z1) in holes):
                gone[r, xs] = True
                a[r, xs] = -1 if a[r, xs] < 0 else a[r, xs]
                continue
            a[r, xs] = c
            if lean and xs + 1 < a.shape[1]:
                a[r, xs + 1] = c                                    # a leaning face has no pinholes
    return gone


def _post(a, x, y, hgt, lean=0.0, snapped=False, seed=0):
    """A post driven into the road at a fold: barked, lit on its west, its cut top pale."""
    wdt = 6
    x0 = int(round(x - wdt / 2))
    front = FN.stake_front(x0, wdt)
    top = hgt if not snapped else hgt
    for z in range(top):
        r = int(round(AY + y - z))
        xo = int(round(lean * z / PANEL))
        xs_ = np.arange(x0, x0 + wdt)
        codes = np.asarray(front(xs_, np.full(xs_.shape, z)))
        for xx, c in zip(xs_, codes):
            if 0 <= r < a.shape[0]:
                a[r, AX + xx + xo] = c
    r = int(round(AY + y - top))
    xo = int(round(lean * top / PANEL))
    if snapped:
        # splintered: a jagged pale end, two points
        for dx, up in ((0, 2), (1, 3), (2, 1), (3, 0), (4, 2), (5, 1)):
            for u in range(up + 1):
                a[r - u, AX + x0 + dx + xo] = C('sand_warm', 5 if u == up else 4)
    else:
        for dr, tones in ((0, (4, 5, 5, 5, 4, 3)), (-1, (-1, 4, 5, 4, 3, -1))):
            for dx, t in enumerate(tones):
                if t >= 0:
                    a[r + dr, AX + x0 + dx + xo] = C('sand_warm', t)


def _broken_ends(a, gone):
    """Pale fresh wood where the weave burst: the rods' ends a texel or two into the gap, in pairs."""
    solid = a >= 0
    edge = gone & ~solid & (np.roll(solid, 1, axis=1) | np.roll(solid, -1, axis=1))
    Yi, Xi = np.indices(a.shape)
    pick = edge & ((Yi // 3) % 2 == 0)
    a[pick] = C('sand', 3)
    a[np.roll(pick, 1, axis=1) & gone & ~solid] = C('timber_warm', 4)


def standing():
    p = V.Pic(W, H, AX, AY)
    js = joints()
    for i in range(PANELS):
        _post(p.a, js[i][0], js[i][1], POST, seed=i)
        _panel(p.a, js[i], js[i + 1], 101 + 7 * i, shade=(js[i + 1][0] < js[i][0]))
    _post(p.a, js[-1][0], js[-1][1], POST, seed=9)
    V.finish(p)
    return p


def battered():
    p = V.Pic(W, H, AX, AY)
    js = joints()
    lean = (7.0, 9.0, 6.0, 10.0, 7.0)
    holes = {0: ((14, 30, 16, 34),), 1: ((4, 16, 22, 42), (30, 44, 8, 24)), 3: ((16, 34, 18, 42),)}
    gone = np.zeros(p.a.shape, bool)
    for i in range(PANELS):
        _post(p.a, js[i][0], js[i][1], POST - 4 if i != 2 else 30, lean=lean[i], snapped=(i == 2), seed=i)
        gone |= _panel(p.a, js[i], js[i + 1], 101 + 7 * i, lean=(lean[i] + lean[i + 1]) / 2.0, sag=(5.0, 3.0, 6.0, 4.0)[i],
                       holes=holes.get(i, ()), shade=(js[i + 1][0] < js[i][0]))
    _post(p.a, js[-1][0], js[-1][1], POST - 4, lean=lean[-1], seed=9)
    _broken_ends(p.a, gone)
    V.finish(p)
    return p


def broken():
    """The posts' stumps, the two north panels thrown flat to the east, the others' rods scattered by the line."""
    p = V.Pic(W, H, AX, AY)
    a = p.a
    rng = np.random.default_rng(1311)
    js = joints()
    # two panels lying flat: the weave seen from above, its rods running the way the panel fell
    for i in (0, 1):
        (xa, ya), (xb, yb) = js[i], js[i + 1]
        face = FN.wattle_front(PANEL, 101 + 7 * i)
        n = 36
        for k in range(n + 1):
            t = k / n
            x, gy = xa + (xb - xa) * t + (6 if i == 0 else -2), ya + (yb - ya) * t + (10 if i == 0 else 16)
            s = t * 51.0
            zs = np.arange(4, PANEL - 2)
            codes = np.asarray(face(np.full(zs.shape, s + 6.0), zs))
            for z, c in zip(zs, codes):
                if (z > 26 and 10 < s < 26 and i == 0) or (z < 16 and s > 34 and i == 1):
                    continue                                    # torn where it took the blows
                # it fell away from the blows, north-east of its foot, and lies flat: the road's depth
                # shows it shorter up the screen than across it
                xs = int(round(AX + x + z * 0.62))
                r = int(round(AY + gy - z * 0.34))
                c = int(c) if c % 8 >= 5 else int(c) + 1          # lying open to the sky, a tone up
                if 0 <= r < a.shape[0] and 0 <= xs < a.shape[1]:
                    a[r, xs] = c
                    if xs + 1 < a.shape[1] and a[r, xs + 1] < 0:
                        a[r, xs + 1] = c
    # the other panels' rods, loose: strands two texels thick, their broken ends pale
    for i in range(12):
        # (the south half of the run stands behind the next house's roof on the first night's pads: its
        # rods stay near the line, so none shows past the roof's end)
        base = js[2] if i < 6 else js[3]
        y = base[1] + 4 + (i % 6) * 6 + int(rng.integers(-2, 3))
        x = int(rng.integers(-14, 2))
        ln = int(rng.integers(14, 24))
        ang = math.radians(float(rng.uniform(-30, 30)))
        x1, y1 = x + ln * math.cos(ang), y + ln * math.sin(ang) * 0.6
        m = V.seg_mask(a.shape, AX + x, AY + y, AX + x1, AY + y1, 1.1)
        mix = (i * 0.37) % 1.0
        up = m & ~np.roll(m, 1, axis=0)
        a[m] = int(ramp_mix(HAZELS, np.array([2.6]), np.array([mix]))[0])
        a[up] = int(ramp_mix(HAZELS, np.array([4.0]), np.array([mix]))[0])
        e = V.seg_mask(a.shape, AX + x1 - 2.0 * math.cos(ang), AY + y1 - 2.0 * math.sin(ang) * 0.6, AX + x1, AY + y1, 1.1) & m
        a[e] = C('sand_warm', 4)
    # the stumps
    for i, (x, y) in enumerate(js):
        if i == 3:
            continue                                              # one torn clean out of the road
        _post(a, x, y, int(rng.integers(6, 12)), snapped=True, seed=i)
    V.finish(p)
    return p


def sheet():
    """What the game needs to lay each picture and its contact shadow (texels from the pad's middle)."""
    return {
        '_about': 'scripts/art/kit/hurdles.py: Hale\'s hurdle barricade for a 48 world px span. `foot` is the pad\'s middle in each picture; `ground` is the run\'s ground line (its folds, x and y from the pad\'s middle) and `rise` its height in texels, for the contact shadow by data/sun.json; a `flat` picture lies on the road, under everyone.',
        'span': SPAN // 3,
        'frame': [W, H],
        'foot': [AX, AY],
        'states': {
            'standing': {'png': 'hurdle_standing.png', 'ground': [[int(x), int(y)] for x, y in joints()], 'rise': PANEL, 'flat': False},
            'battered': {'png': 'hurdle_battered.png', 'ground': [[int(x), int(y)] for x, y in joints()], 'rise': PANEL - 6, 'flat': False},
            'broken': {'png': 'hurdle_broken.png', 'ground': [], 'rise': 0, 'flat': True},
        },
    }


def build(write=True):
    out = {}
    for name, fn in (('standing', standing), ('battered', battered), ('broken', broken)):
        out[os.path.join(ART, 'hurdle_%s.png' % name)] = to_rgba(fn().a)
    if write:
        os.makedirs(ART, exist_ok=True)
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        with open(os.path.join(ART, 'hurdle.json'), 'w') as f:
            json.dump(sheet(), f, indent=1)
            f.write('\n')
    return out


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    sp = os.path.join(ART, 'hurdle.json')
    if not os.path.exists(sp) or json.load(open(sp)) != sheet():
        bad.append(os.path.relpath(sp, ROOT))
    if bad:
        print('hurdles: stale %s (run python3 -m scripts.art.kit.hurdles)' % ', '.join(bad))
        return 1
    print('hurdles: pictures current')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    print('hurdles: %d pictures' % len(build()))
    return 0


if __name__ == '__main__':
    sys.exit(main())

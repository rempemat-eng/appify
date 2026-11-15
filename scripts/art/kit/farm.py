"""Farmyard pieces for the kit: hens and their coop, sheep and their field shelter, hay, and the
kitchen garden's beds (docs/vision/placement-logic.md: "Keep animals in: a paddock, sheep fold,
goat pen, chicken run or pigsty, with its animals inside, plus a trough, a water source and
shelter"; docs/vision/placement-audit.md flagged the beds and the hay for a redraw and the trough
as missing its animals and pen).

    python3 -m scripts.art.kit.farm            # pictures and pieces (pieces kept unless --force)
    python3 -m scripts.art.kit.farm --check    # exit 1 if a committed picture is not what this draws

Every picture is a code canvas on the house palette (scripts/art/native/village.py's helpers),
lit from the upper left, closed with the house outline; sizes in texels at density 3 (A = 74):
- a hen 21 tall (0.28 A; size-guide 2: "cat, hen ... 5 to 12 world px", 15 to 36 texels) in white,
  brown and speckled, and her idle: she looks about and pecks (8 frames at 4 a second);
- a sheep 38 tall, 55 long (size-guide 2: 12 to 17 by 16 to 22 world px), a curly fleece and a black
  face: standing (an ear flick and a turn of the head), grazing (her head down, chewing) and
  lying (breathing);
- the hen ark, 48 wide and 47 tall, on legs, with a pop hole and a ramp;
- the field shelter, four cells wide, open to the south, a boarded back, straw inside;
- hay: three bales stacked and tied, and a heap forked out loose (size-guide "haystack");
- the kitchen garden's beds: soil ridged into rows with a crop on each, in a dug patch with its
  rough edge where the spade stopped (no boards: Matt's review read the boarded boxes as crates);
  and the same beds burnt, the crops black stubs in ash (the storm's stage).
Animals show a still (the variant's picture: frame 0) and an idle strip beside it
(rendering.animations: strip, frames, fps), played by world/loop_fx.gd only while on screen and
held on frame 0 under reduced motion.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.native import village as V
from scripts.art.native.palette import FI, to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'farm')
RES = 'res://kit/props/art/farm/'


def C(fam, t):
    return FI[fam] * 8 + int(max(0, min(5, round(t))))


def canvas(w, h, ax, ay):
    return V.Pic(w, h, ax, ay)


def grid(a):
    """Texel coordinates (integers, so the courses, boards and rows can be counted with %)."""
    return np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(float)


def sphere_light(X, Y, cx, cy, rx, ry):
    """Light on an ellipsoid lit from the upper left (-1 .. 1)."""
    nx, ny = (X - cx) / rx, (Y - cy) / ry
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    return -0.55 * nx - 0.65 * ny + 0.5 * nz


def rpaint(a, m, sets, t, mix):
    """Paint mask m with float tones t (0..5) in one of several (cool, body, warm) triples chosen
    per pixel by mix (0..1): hue shifts across a material (a fleece's cream and grey, a bale's
    gold and straw), so a surface is more than one ramp."""
    t = np.clip(np.round(np.broadcast_to(np.asarray(t, float), m.shape)), 0, 5).astype(int)
    mix = np.broadcast_to(np.asarray(mix, float), m.shape)
    k = np.clip((mix * len(sets)).astype(int), 0, len(sets) - 1)
    fam = np.zeros(m.shape, int)
    for i, (cool, body, warm) in enumerate(sets):
        f = np.where(t >= 4, FI[warm], np.where(t <= 1, FI[cool], FI[body]))
        fam = np.where(k == i, f, fam)
    a[m] = (fam * 8 + t)[m]


def noise(shape, rng, sigma=1.0):
    n = ndi.gaussian_filter(rng.random(shape), sigma)
    return (n - n.min()) / max(1e-6, n.max() - n.min())


# ------------------------------------------------------------------------------------------------
# hens
# ------------------------------------------------------------------------------------------------
HENS = {
    # kind: body sets, wing sets, tail sets, face (1 east, -1 west), speckle family
    'white': ([('stone_cool', 'plaster_warm', 'plaster'), ('sand_cool', 'sand', 'snow_warm')],
              [('stone_warm', 'plaster_warm', 'plaster')], [('stone_cool', 'plaster_warm', 'snow_warm')], -1, None),
    'brown': ([('clay_cool', 'fox', 'brass_warm'), ('crag_cool', 'crag_warm', 'fox')],
              [('clay_cool', 'clay', 'fox')], [('soot', 'soot', 'sky_cool')], -1, None),
    'speckled': ([('slate_cool', 'stone', 'stone_warm'), ('stone_cool', 'ashlar', 'plaster_warm')],
                 [('stone_cool', 'stone', 'stone_warm')], [('soot', 'slate_cool', 'slate')], 1, 'soot'),
}
HEN_FRAMES = ['up', 'up', 'look', 'up', 'peck', 'peck2', 'peck', 'up']


def hen(kind, pose='up', seed=0):
    """A hen (about 22 x 26 texels): a round body lit on its upper left, its breast pale and its
    belly shaded; the folded wing a separate shape with a dark edge and two rows of feathers; the
    tail a fan of separate feathers cocked up behind, the sickles darker with a sheen; the head
    forward with a red comb lit on its crown and a wattle, a yellow beak, an amber eye with a glint;
    scaled yellow legs. `pose`: up, look (head turned back), peck, peck2 (head down at the ground)."""
    body_s, wing_s, tail_s, face, speck = HENS[kind]
    rng = np.random.default_rng(seed + 7)
    p = canvas(34, 31, 17, 28)
    a = p.a
    Y, X = grid(a)
    cx, yb = 17 - face * 1, 28
    nz = noise(a.shape, rng, 0.8)
    for dx in (-2, 2):                                          # legs: scaled, a toe forward
        x = int(cx + dx)
        a[yb - 6:yb - 1, x] = C('brass', 3)
        a[yb - 6:yb - 1:2, x] = C('brass', 4)
        a[yb - 1, x - 1:x + 2] = C('brass', 2)
        a[yb - 1, x + face * 2] = C('brass', 2)
    peck = pose in ('peck', 'peck2')
    tilt = 1.0 if peck else 0.0
    by = yb - 12 + tilt
    body = ((X - cx) / 8.6) ** 2 + ((Y - by) / 6.6) ** 2 <= 1
    lit = sphere_light(X, Y, cx, by, 8.6, 6.6)
    # the tail: four feathers fanned up and back, each its own lit blade with a dark edge
    tail = np.zeros(a.shape, bool)
    blades = []
    for i, (ang, L) in enumerate(((1.75, 9.5), (2.15, 10.5), (2.55, 9.5), (2.95, 7.5))):
        bx0, by0 = cx - face * 5.5, by - 1.0 + tilt
        tip = (bx0 - face * L * abs(math.cos(ang)), by0 - L * math.sin(ang))
        m = V.seg_mask(a.shape, bx0, by0, tip[0], tip[1], 1.45) & ~body
        tail |= m
        blades.append(m)
    rpaint(a, tail, tail_s, 3.2 + 1.3 * sphere_light(X, Y, cx - face * 8, by - 6, 6, 6), nz)
    for i, m in enumerate(blades):                              # each feather's shaded edge, so they separate
        if i % 2:
            a[m & ~ndi.binary_erosion(m) & (Y > by - 12)] = C(tail_s[0][1], 2)
    # the body
    rpaint(a, body, body_s, 2.9 + 1.7 * lit, nz)
    a[body & (Y > by + 4.0) & ~((X - cx) * face > 3)] = C(body_s[0][0], 2)        # the belly in shade
    a[body & (Y > by + 5.4)] = C(body_s[0][0], 1)
    # the breast, pale and catching the light at the front
    br = body & (((X - (cx + face * 5.0)) / 3.8) ** 2 + ((Y - (by - 0.5)) / 4.0) ** 2 <= 1)
    rpaint(a, br, body_s, 3.6 + 1.2 * lit, nz)
    # the wing: its own shape over the flank, a dark line along its top edge, two feather rows
    wx, wy = cx - face * 1.2, by + 0.6
    wing = (((X - wx) / 5.8) ** 2 + ((Y - wy) / 3.4) ** 2 <= 1) & body
    rpaint(a, wing, wing_s, 3.0 + 1.0 * sphere_light(X, Y, wx, wy - 2, 6, 4), nz)
    edge = wing & ~ndi.binary_erosion(wing) & (Y < wy + 1)
    a[edge] = C(wing_s[0][0], 2)
    sc = wing & (np.abs(Y - wy - 1.4 - 0.8 * np.cos((X - wx) * 1.4)) < 0.5)        # the flight feathers' row
    a[sc] = C(wing_s[0][0], 2)
    a[wing & (Y > wy + 2.2)] = C(wing_s[0][0], 1)                                  # the wing tips, tucked
    a[edge & (X * face < wx * face)] = C(wing_s[0][2], 4)                          # its lit top edge
    if speck:
        sp = body & (rng.random(a.shape) < 0.10) & ~wing
        a[sp] = C(speck, 2)
        a[body & (rng.random(a.shape) < 0.05) & ~wing] = C('plaster', 5)
    # the head
    if pose == 'look':
        hx, hy = cx + face * 4.2, by - 7.4
    elif peck:
        hx, hy = cx + face * 9.0, yb - (4.5 if pose == 'peck' else 3.0)
    else:
        hx, hy = cx + face * 6.8, by - 7.0
    neck = V.seg_mask(a.shape, cx + face * 3.6, by - 2.5, hx, hy + 1, 2.7)
    head = ((X - hx) / 3.2) ** 2 + ((Y - hy) / 3.1) ** 2 <= 1
    hm = (neck | head) & ~(body & (Y > by - 1))
    rpaint(a, hm, body_s, 3.5 + 1.4 * sphere_light(X, Y, hx, hy, 3.5, 3.5), nz)
    fwd = face if pose != 'look' else -face
    for k, dx in enumerate((-1.7, 0.0, 1.7)):                   # the comb, lit on its crown
        cm = ((X - (hx + dx * fwd * 0.8 - fwd * 0.4)) / 1.15) ** 2 + ((Y - (hy - 3.3 + 0.3 * abs(dx))) / 1.5) ** 2 <= 1
        a[cm] = C('berry', 3)
        a[cm & (Y < hy - 3.6 + 0.3 * abs(dx))] = C('berry', 5 if k == 1 else 4)
    wm = ((X - (hx + fwd * 1.6)) / 1.0) ** 2 + ((Y - (hy + 2.9)) / 1.7) ** 2 <= 1
    a[wm] = C('berry', 3)
    a[wm & (X * fwd < (hx + fwd * 1.6) * fwd)] = C('berry', 4)
    a[wm & (Y > hy + 3.8)] = C('berry_cool', 2)
    bx = int(round(hx + fwd * 3.0))
    by_ = int(round(hy))
    a[by_ - 1, min(bx, bx + fwd * 2):max(bx, bx + fwd * 2) + 1] = C('brass', 5)
    a[by_, min(bx, bx + fwd * 2):max(bx, bx + fwd * 2) + 1] = C('brass', 3)
    ex = int(round(hx + fwd * 0.9))
    a[by_ - 1, ex] = C('brass', 4)
    a[by_ - 1, ex + (1 if fwd > 0 else -1) * 0] = C('soot', 0)
    a[by_ - 2, ex] = C('plaster', 5)
    if pose == 'peck2':
        a[yb - 1, int(hx + fwd * 4)] = C('brass', 5)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# sheep
# ------------------------------------------------------------------------------------------------
SHEEP_FRAMES = {
    'stand': ['a', 'a', 'a', 'ear', 'a', 'turn', 'turn', 'a'],
    'graze': ['down', 'chew', 'down', 'chew', 'down', 'down', 'ear', 'down'],
    'lie': ['in', 'in', 'out', 'out', 'in', 'in', 'out', 'ear'],
}
WOOL = [('sand_cool', 'plaster_warm', 'plaster'), ('sand_cool', 'sand', 'plaster'), ('stone_warm', 'plaster_warm', 'plaster'),
        ('stone_warm', 'sand', 'sand_warm'), ('stone_cool', 'plaster_warm', 'sand_warm')]   # the 4th: yellowed with lanolin


def sheep(pose='stand', frame='a', face=1, seed=0):
    """A ewe (about 55 x 38 texels standing): a fleece built of clustered curls, each a small dome
    lit on its upper left with a cream highlight and a grey crease under it, the mass shading to a
    cool belly; a black face with a grey muzzle, an amber eye with a glint, ears out with a pink
    lining, a topknot of wool; legs black with a wool-covered thigh, a knee and a hoof (the far pair
    a step darker). Grazing her head is down at the grass; lying her legs are folded under."""
    rng = np.random.default_rng(seed)
    p = canvas(84, 56, 42, 52)
    a = p.a
    Y, X = grid(a)
    cx, yb = 42 - face * 3, 52
    lie = pose == 'lie'
    breathe = 1 if (lie and frame == 'out') else 0
    by = yb - (14 if lie else 21)
    rx, ry = 22.5, (14.0 + breathe * 0.5 if lie else 13.0)
    nz = noise(a.shape, rng, 1.0)
    if not lie:
        for lx, far in ((-12.5, True), (8.5, True), (-9.5, False), (12.0, False)):
            x = int(round(cx + face * lx))
            t = 1 if far else 2
            knee = yb - 6
            a[int(by + 6):knee, x:x + 4] = C('soot', t)                 # the thigh under the wool, thick
            a[int(by + 6):knee, x] = C('soot', t + 2)
            a[knee:knee + 1, x - 1:x + 4] = C('soot', t + 1)            # the knee, a knob lit on its top
            a[knee, x - 1] = C('soot', t + 3)
            a[knee + 1:yb - 1, x:x + 3] = C('soot', t)                  # the shank
            a[knee + 1:yb - 1, x] = C('soot', t + 2)
            a[yb - 2:yb, x - (1 if face < 0 else 0):x + 4] = C('soot', 0)   # the hoof
            a[yb - 2, x] = C('stone_cool', 1)
    fleece = ((X - cx) / rx) ** 2 + ((Y - by) / ry) ** 2 <= 1
    t = 2.6 + 1.7 * sphere_light(X, Y, cx, by, rx, ry)
    mix = np.zeros(a.shape)
    crease = np.zeros(a.shape, bool)
    hi = np.zeros(a.shape, bool)
    curls = rng.uniform(-1, 1, (48, 2))                          # few, large curl clusters: soft at 3x, never speckled
    curls = curls[(curls ** 2).sum(1) <= 1.08]
    cm_all = np.zeros(a.shape, bool)
    for ux, uy in sorted(curls.tolist(), key=lambda c: c[1]):
        px, py = cx + ux * (rx - 2.0), by + uy * (ry - 1.5)
        r1, r2 = rng.uniform(4.2, 5.4), rng.uniform(3.2, 4.0)
        m = ((X - px) / r1) ** 2 + ((Y - py) / r2) ** 2 <= 1
        inner = ((X - px + 0.7) / (r1 - 0.9)) ** 2 + ((Y - py + 0.7) / (r2 - 0.8)) ** 2 <= 1
        crease = (crease & ~m) | (m & ~inner & ((X - px) + (Y - py) > 0.3))
        hi = (hi & ~m) | (m & ((X - px + 1.4) ** 2 + (Y - py + 1.2) ** 2 <= 2.3))
        cm_all |= m
        mix = np.where(m, rng.choice([0.1, 0.1, 0.3, 0.5, 0.7]), mix)  # each curl one of a few creams, some yellowed
        t = np.where(m, (2.1 if lie else 2.5) + 1.5 * sphere_light(X, Y, cx, by, rx, ry) + 1.3 * sphere_light(X, Y, px, py, r1, r2), t)
    fleece = (fleece | cm_all) & (Y < yb - (0 if lie else 7))
    rpaint(a, fleece, WOOL, t, mix)
    shade = sphere_light(X, Y, cx, by, rx, ry)
    # the creases between curls: deeper where the fleece turns from the light, each curl's own hue
    # the creases: one soft step down in the curl's own cream (a darker step only on the shaded
    # side), so the fleece reads as soft lumps, not grit
    cr = crease & fleece
    a[cr] = np.maximum(a[cr] - np.where(shade[cr] < 0.0, 2, 1), (a[cr] // 8) * 8)
    hm_ = hi & fleece & (shade > 0.2)
    a[hm_] = np.where(mix[hm_] > 0.6, C('sand_warm', 5), C('plaster', 5))
    if lie:
        # the forelegs folded under her chest, a black knee and hoof showing, the wool pressed into
        # the grass along her underside
        for k, lx in enumerate((10.0, 15.5)):
            kx = int(round(cx + face * lx))
            ky = yb - 3
            a[ky - 1:ky + 1, min(kx, kx + face * 5):max(kx, kx + face * 5)] = C('soot', 1 + k)
            a[ky - 1, min(kx, kx + face * 5):max(kx, kx + face * 5)] = C('soot', 3)
            a[ky:ky + 1, kx + face * 5 - (1 if face > 0 else 0)] = C('soot', 0)
        a[fleece & (Y >= yb - 2)] = C('stone_warm', 1)
        hx_, hy_ = int(round(cx - face * (rx - 4))), yb - 3            # the hind leg folded under her, its hock showing
        a[hy_ - 1:hy_ + 1, min(hx_, hx_ - face * 5):max(hx_, hx_ - face * 5)] = C('soot', 2)
        a[hy_ - 1, min(hx_, hx_ - face * 5):max(hx_, hx_ - face * 5)] = C('soot', 3)
        a[hy_ - 2:hy_, hx_ - face * 5 - (1 if face < 0 else 0)] = C('slate_cool', 2)
        shadow_side = fleece & (Y >= yb - 5) & (Y < yb - 2) & ((X - cx) * face < rx * 0.6)
        rpaint(a, shadow_side, [('stone_warm', 'stone_warm', 'sand_cool')], np.full(a.shape, 3.0), 0)   # the grass's warm bounce under her
    belly = fleece & (Y > by + ry * 0.55)
    rpaint(a, belly, [('stone_warm', 'sand_cool', 'sand'), ('stone_cool', 'stone_warm', 'sand_cool')], 1.6 + 0.9 * (Y < by + ry * 0.75), mix)
    # the head
    if pose == 'graze':
        chew = 1 if frame == 'chew' else 0
        hx, hy = cx + face * (rx + 0.5), yb - 7 + chew
        neck = V.seg_mask(a.shape, cx + face * (rx - 5), by - 1, hx, hy - 2, 4.2)
        rpaint(a, neck & ~fleece, WOOL, 2.8 + sphere_light(X, Y, hx, by, 5, 5), mix)
    elif lie:
        hx, hy = cx + face * (rx - 1.0), by - 6
    else:
        hx, hy = cx + face * (rx + 0.5), by - 8
    hface = face if frame != 'turn' else 0
    head = ((X - hx - hface * 1.2) / 5.4) ** 2 + ((Y - hy) / 6.4) ** 2 <= 1
    muzzle = ((X - hx - hface * 3.8) / 2.8) ** 2 + ((Y - hy - 2.5) / 2.8) ** 2 <= 1
    hm = head | muzzle
    rpaint(a, hm, [('soot', 'soot', 'iron')], 1.5 + 1.8 * sphere_light(X, Y, hx, hy, 5, 6), 0)
    rpaint(a, muzzle & (X * (hface or 1) > (hx + (hface or 1) * 2.4) * (hface or 1)), [('soot', 'slate_cool', 'stone')],
           2.0 + 1.6 * sphere_light(X, Y, hx + hface * 3.8, hy + 1.5, 2.8, 2.8), 0)   # the grey muzzle, lit on its bridge
    a[muzzle & (Y > hy + 4.2)] = C('stone_cool', 1)
    nx_ = int(round(hx + hface * 5.6))
    a[int(round(hy + 2.4)), nx_] = C('soot', 0)                           # a nostril
    ey, ex = int(round(hy - 1.5)), int(round(hx + hface * 2.0))
    a[ey - 1:ey + 1, ex - 1:ex + 2] = C('brass', 3)                       # the eye, amber, with a glint
    a[ey - 1:ey + 1, ex + (1 if hface >= 0 else -1)] = C('soot', 0)
    a[ey - 1, ex] = C('plaster', 5)
    a[ey - 2, ex - 1:ex + 2] = C('slate_cool', 2)                         # the brow catching the light
    flick = frame == 'ear'
    for side in (-1, 1):
        ex0 = hx - face * 2.0 + side * 3.0
        ey0 = hy - 4.5 - (1.5 if (flick and side > 0) else 0)
        ear = ((X - (ex0 + side * 3.4)) / 3.8) ** 2 + ((Y - ey0) / 1.7) ** 2 <= 1
        a[ear & ~hm] = C('soot', 2 if side < 0 else 1)
        lining = ear & ~hm & ((X - (ex0 + side * 2.6)) ** 2 / 4.0 + (Y - ey0 - 0.3) ** 2 <= 0.5)
        a[lining] = C('berry_cool', 2)
    tk = ((X - (hx - face * 1.5)) / 3.0) ** 2 + ((Y - (hy - 5.5)) / 2.0) ** 2 <= 1
    rpaint(a, tk & ~hm, WOOL, 4.0 + sphere_light(X, Y, hx, hy - 6, 3, 2), mix)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the larger stock: cow and calf, horse, pig, goat
# ------------------------------------------------------------------------------------------------
BEASTS = {
    # canvas (w, h, foot x, foot y); body half length and half depth; leg length and width; head half
    # width, half height, how far before the chest, how high above the back's middle; coat; extras
    'cow': dict(c=(164, 116, 82, 112), rx=40, ry=22, leg=15, lw=9, head=(11, 11.5, 2, 11), coat='tan', horns=True, udder=True, tail=24, ears='side'),
    'calf': dict(c=(96, 72, 48, 68), rx=20, ry=12, leg=9, lw=6, head=(7.5, 8, 1, 7), coat='pied', horns=False, udder=False, tail=14, ears='side'),
    'horse': dict(c=(164, 132, 82, 128), rx=29, ry=18, leg=19, lw=8, head=(9.6, 13.8, 13, 24), coat='bay', horns=False, udder=False, tail=28, ears='up', mane=True),
    'pig': dict(c=(100, 64, 50, 60), rx=23, ry=13.5, leg=8, lw=7, head=(8.5, 9, 4, 2), coat='pig', horns=False, udder=False, tail=0, ears='flop', snout=True),
    'goat': dict(c=(88, 80, 44, 76), rx=19, ry=12, leg=9, lw=5, head=(6.5, 8, 2, 12), coat='goat', horns=True, udder=False, tail=5, ears='droop', beard=True),
    'goat_b': dict(c=(88, 80, 44, 76), rx=19, ry=12, leg=9, lw=5, head=(6.5, 8, 2, 12), coat='goat_b', horns=True, udder=False, tail=5, ears='droop', beard=True),
}
COATS = {
    # body ramps (shade leans violet, light leans gold), patches, the head's own ramp, the muzzle's
    'pied': ([('stone_cool', 'plaster_warm', 'plaster'), ('dusk_cool', 'sand', 'plaster'), ('slate_cool', 'stone_warm', 'sand_warm'),
              ('sand_cool', 'sand_warm', 'snow_warm')],
             [('soot', 'soot', 'slate_cool'), ('soot', 'slate_cool', 'slate'), ('dusk_cool', 'slate_cool', 'stone_cool')],
             [('berry_cool', 'plaster_warm', 'sand_warm'), ('crag_cool', 'clay', 'plaster_warm')]),
    'tan': ([('stone_cool', 'plaster_warm', 'plaster'), ('stone_warm', 'sand', 'plaster')],
            [('earth_cool', 'fox', 'brass_warm'), ('crag_cool', 'clay', 'fox'), ('earth_cool', 'earth_warm', 'fox')],
            [('berry_cool', 'plaster_warm', 'sand_warm'), ('crag_cool', 'clay', 'plaster_warm')]),
    'bay': ([('dusk_cool', 'fox', 'brass_warm'), ('crag_cool', 'crag_warm', 'fox'), ('earth_cool', 'clay', 'brass'),
             ('timber_cool', 'earth_warm', 'sand_warm')],
            [('soot', 'soot', 'slate_cool'), ('soot', 'dusk_cool', 'slate')],
            [('soot', 'slate_cool', 'stone'), ('dusk_cool', 'stone_cool', 'stone')]),
    'pig': ([('crag_cool', 'clay', 'sand_warm'), ('berry_cool', 'clay', 'plaster_warm'), ('dusk_cool', 'crag_warm', 'sand')],
            [('earth_cool', 'earth', 'earth_warm'), ('soot', 'earth_cool', 'earth'), ('path_cool', 'path', 'path_warm')],
            [('crag', 'clay', 'sand_cool'), ('crag', 'clay', 'sand_cool')]),
    'goat': ([('stone_cool', 'plaster_warm', 'plaster'), ('stone_warm', 'sand', 'plaster'), ('sand_cool', 'plaster_warm', 'snow_warm'),
              ('slate_cool', 'stone_warm', 'sand_warm')],
             [('clay_cool', 'fox', 'brass_warm'), ('earth_cool', 'earth_warm', 'sand_warm')],
             [('stone_cool', 'stone_warm', 'sand'), ('slate_cool', 'stone', 'plaster_warm')]),
    'goat_b': ([('earth_cool', 'earth', 'earth_warm'), ('timber_cool', 'earth_warm', 'sand_warm'), ('crag_cool', 'clay', 'brass')],
               [('soot', 'earth_cool', 'timber_cool'), ('soot', 'slate_cool', 'earth_cool')],
               [('sand_cool', 'sand', 'plaster_warm'), ('stone_warm', 'sand', 'plaster_warm')]),
}
# one character beat a kind, over eight frames
BEAST_FRAMES = {
    'cow': ['a', 'a', 'tail1', 'tail2', 'tail1', 'a', 'a', 'a'],
    'calf': ['a', 'a', 'a', 'ear', 'ear', 'a', 'a', 'a'],
    'horse': ['a', 'a', 'dip1', 'dip2', 'dip2', 'dip1', 'a', 'a'],
    'pig': ['a', 'snuff1', 'snuff2', 'snuff1', 'a', 'a', 'a', 'a'],
    'goat': ['a', 'chew', 'a', 'chew', 'a', 'chew', 'a', 'a'],
    'goat_b': ['dip2', 'dip2', 'chew2', 'dip2', 'chew2', 'dip2', 'dip2', 'dip2'],
}


def _ell(X, Y, cx, cy, rx, ry):
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1


def beast(kind, frame='a', face=1, seed=0):
    """A farm animal in the house's three-quarter view (round 4, after the art director's review:
    no boxes on stilts). The body is a bean, rump and chest swelling either side of a soft belly
    curve, lit on its upper left, a darker band along its underside and cool light reflected under
    it; legs short and thick (a third of the body's depth, a horse's a half), tapering to dark
    hooves, the far pair a tone darker and half hidden; the head large (about two fifths of the body
    and more), turned three quarters to us: a lit brow, both eyes (the near one with its highlight),
    a lighter muzzle or snout with its nostrils, ears that break the outline. `frame`: a (still),
    tail1/tail2 (a swish), ear (a flick), dip1/dip2 (the head down to graze), snuff1/snuff2 (a
    pig's snout working), chew/chew2 (the jaw)."""
    B = BEASTS[kind]
    rng = np.random.default_rng(seed)
    W, H, fx, fy = B['c']
    p = canvas(W, H, fx, fy)
    a = p.a
    Y, X = grid(a)
    body_sets, mark_sets, muzzle_sets = COATS[B['coat']]
    rx, ry = B['rx'], B['ry']
    cx = fx - face * 5
    by = fy - B['leg'] - ry + 3
    nz = noise(a.shape, rng, 1.0)
    smooth = noise(a.shape, np.random.default_rng(seed + 11), 2.5)
    # the bean: rump, chest and a belly that sags a little between them
    body = (_ell(X, Y, cx - face * rx * 0.38, by - 0.5, rx * 0.64, ry * 0.98) | _ell(X, Y, cx + face * rx * 0.36, by, rx * 0.66, ry * 0.95)
            | _ell(X, Y, cx, by + ry * 0.12, rx * 0.78, ry * 0.92))
    body = ndi.gaussian_filter(body.astype(float), 1.6) > 0.5
    bottom = np.where(body.any(axis=0), H - 1 - np.argmax(body[::-1], axis=0), -1)[None, :]
    topr = np.where(body.any(axis=0), np.argmax(body, axis=0), H)[None, :]
    lit = sphere_light(X, Y, cx, by, rx, ry)
    # the legs, the far pair first (a tone darker, set back and half hidden by the body)
    lw, leg = B['lw'], B['leg']
    for lx, far in ((-0.62, True), (0.42, True), (-0.48, False), (0.6, False)):
        x0 = cx + face * lx * rx - lw / 2 + (-face * 3 if far else 0)
        yt = by + ry * 0.4
        yh = fy - (1 if far else 0)
        f_ = np.clip((Y - yt) / max(1, yh - yt), 0, 1)
        wid = lw * (1.0 - 0.3 * f_) + 1.5 * (np.abs(Y - (yh - leg * 0.45)) < 1.2)      # thick at the top, a knee
        legm = (X >= x0 + (lw - wid) / 2) & (X < x0 + (lw + wid) / 2) & (Y >= yt) & (Y < yh)
        u = (X - x0) / lw
        sets = mark_sets if B['coat'] == 'bay' and True else body_sets
        tl = 2.6 - (1.0 if far else 0) + 1.1 * (u < 0.25) - 1.0 * (u > 0.75) - 0.6 * f_
        rpaint(a, legm, [body_sets[0] if not far else body_sets[-1]], tl, 0)
        if B['coat'] == 'bay':                                   # a bay's black points, one white sock
            lower = legm & (Y > yh - leg * 0.7)
            rpaint(a, lower, mark_sets, 1.4 - (0.6 if far else 0) + 1.0 * (u < 0.3), 0.2)
            if not far and lx > 0:
                rpaint(a, legm & (Y > yh - 5), [('stone_cool', 'plaster_warm', 'plaster')], 3.6 + (u < 0.3), 0)
        kn_y = int(round(yh - leg * 0.45))
        kx0 = int(round(x0 + lw * 0.15))
        knee_m = legm & (Y >= kn_y - 1) & (Y <= kn_y) & (X >= kx0) & (X < kx0 + max(2, int(lw * 0.5)))
        a[knee_m] = np.minimum(a[knee_m] + 1, (a[knee_m] // 8) * 8 + 5)       # the kneecap catching the light
        hollow = legm & (Y >= kn_y + 1) & (Y <= kn_y + 2) & (X >= kx0 + 1) & (X < kx0 + 1 + max(2, int(lw * 0.5)))
        a[hollow] = np.maximum(a[hollow] - 1, (a[hollow] // 8) * 8)
        hoof = legm & (Y >= yh - 3)
        a[hoof] = C('soot', 0 if far else 1)
        a[hoof & (Y == yh - 3) & (u < 0.6)] = C('slate_cool', 2 if far else 3)
    # the body in planned clusters (round 5, after the art director's review: tones from a few
    # large shapes, never from scattered pixels): a light plane along the back and over the shoulder
    # and haunch, the mid flank, a core shadow band along the belly, light reflected up under it
    # from the grass, a dark rim on the bottom contour; each its own ramp, each a solid shape
    depth = (Y - topr) / np.maximum(1, bottom - topr)
    sh = sphere_light(X, Y, cx + face * rx * 0.45, by - ry * 0.15, rx * 0.4, ry * 0.75)
    hn = sphere_light(X, Y, cx - face * rx * 0.5, by - ry * 0.2, rx * 0.42, ry * 0.8)
    lobe = np.maximum(sh, hn)
    east = (X - cx) / rx                                         # the light comes from the upper left
    v = 0.4 * depth + 0.45 * (1 - lit) + 0.1 * east - 0.18 * np.clip(lobe, 0, 1)
    v = ndi.gaussian_filter(v, 1.4)                              # band edges as smooth curves round the form
    cuts = np.quantile(v[body], [0.06, 0.2, 0.36, 0.52, 0.68, 0.82, 0.93])
    band = np.digitize(v, cuts)                                  # 0 the highlight .. 7 the rim
    band = np.where(body & (Y >= bottom - 1), 7, band)
    zone = np.select([band <= 1, band <= 3, band <= 5, band == 6], [0, 1, 2, 3], 4)
    # round 6: the light bounced up from the grass is a warm, low-chroma ochre, and the core shadow
    # and the bottom rim are the coat's own hue darkened, so no band reads as a coloured stripe
    pale = B['coat'] in ('pied', 'tan', 'goat')
    bounce = ('stone_warm', 'stone_warm', 'stone_warm') if pale else ('earth', 'earth', 'earth')
    own_dark = {'pied': 'stone_warm', 'tan': 'stone_warm', 'goat': 'stone_warm', 'bay': 'timber', 'goat_b': 'earth_cool', 'pig': 'crag'}[B['coat']]
    dk = (own_dark, own_dark, own_dark)
    if B['coat'] == 'pig':                                       # a pink apricot (hue 15 to 25 degrees), not a mauve
        bands = [('clay', 'clay', 'clay'), ('berry', 'berry', 'berry'), ('crag_warm', 'crag_warm', 'crag_warm'), ('crag', 'crag', 'crag'),
                 ('crag_warm', 'crag_warm', 'crag_warm'), ('crag', 'crag', 'crag'), ('earth_warm', 'earth_warm', 'earth_warm'), dk]
        tones_ = [5, 5, 4, 4, 3, 3, 3, 2]
    else:
        w_, m_ = body_sets[0], body_sets[min(1, len(body_sets) - 1)]
        # one house ramp from the lit back down the flank, a second close ramp for the half tones
        bands = [w_, w_, w_, m_, w_, dk, bounce, dk]
        tones_ = [5, 4, 3, 3, 2, 2 if not pale else 3, 3 if not pale else 4, 1 if not pale else 2]
    for k in range(8):                                           # each band one ramp and one tone: a solid shape
        rpaint(a, body & (band == k), [bands[k]], np.full(a.shape, float(tones_[k])), 0)
    dark = np.zeros(a.shape, bool)
    if B['coat'] in ('pied', 'tan'):                             # big soft-edged patches, shaded by the same plan
        pn = noise(a.shape, np.random.default_rng(seed + 3), 6.0) + 0.2 * (X - cx) * face / rx \
            + (0.5 * noise(a.shape, np.random.default_rng(seed + 13), 3.0) if kind == 'cow' else 0)      # more patches, their edges varied
        patch = body & (pn > np.percentile(pn[body], 52 if B['coat'] == 'pied' else 50))
        patch = ndi.binary_opening(ndi.binary_closing(patch, iterations=2), iterations=2) & body
        mt = [4, 4, 3, 3, 2, 2, 2, 1]
        for k in range(8):
            rpaint(a, patch & (band == k), [mark_sets[0]], np.full(a.shape, float(mt[k])), 0)
        dark = patch
    elif B['coat'] == 'goat':
        patch = body & (noise(a.shape, np.random.default_rng(seed + 5), 4.5) > 0.6)
        patch = ndi.binary_opening(patch, iterations=2)
        for k, tz in enumerate((4, 4, 3, 3, 2, 2, 2, 1)):
            rpaint(a, patch & (band == k), [mark_sets[0] if k < 4 else mark_sets[-1]], np.full(a.shape, float(tz)), 0)
    elif B['coat'] == 'goat_b':                                  # a dark stripe down the back
        stripe = body & (Y - topr <= 2)
        rpaint(a, stripe, [mark_sets[0]], 1.8 + 1.0 * (lobe > 0.4), 0)
        dark = stripe
    elif B['coat'] == 'pig':                                     # two or three shaped splashes of mud on the belly and legs
        mud = np.zeros(a.shape, bool)
        for k, (ux, uy, sx, sy) in enumerate(((-0.45, 0.78, 7.0, 3.6), (0.25, 0.86, 6.0, 3.0), (0.7, 0.7, 3.6, 2.6))):
            mx_, my_ = cx + face * ux * rx, by + uy * ry
            blob = _ell(X, Y, mx_, my_, sx, sy) | _ell(X, Y, mx_ - face * sx * 0.6, my_ + sy * 0.9, sx * 0.5, sy * 0.9)
            mud |= blob
        mud &= (a >= 0) & (Y > by + ry * 0.3)
        rpaint(a, mud, [mark_sets[0]], 2.0 + 0.8 * (Y < by + ry * 0.75) - 0.8 * (Y >= bottom - 1), 0)
        rpaint(a, mud & ~ndi.binary_erosion(mud, iterations=1) & (Y < by + ry * 0.75), [mark_sets[2]], np.full(a.shape, 3.4), 0)   # a wet lit lip
    # a few deliberate strokes of hair along the light plane's lower edge, 2 to 4 px each
    edge_zone = body & (band >= 1) & (band <= 5) & ndi.binary_dilation(np.diff(band, axis=0, prepend=band[:1]) != 0, iterations=1)
    ys_, xs_ = np.nonzero(edge_zone)
    if len(ys_):
        for k in rng.choice(len(ys_), size=min(len(ys_), int(rx * 1.6)), replace=False):
            y0_, x0_ = ys_[k], xs_[k]
            code = a[y0_, x0_]
            up = band[y0_, x0_] >= 4                             # in the shade a lock catches light, in the light it shades
            new = min(code + 1, (code // 8) * 8 + 5) if up else max(code - 1, (code // 8) * 8)
            for (dy_, dx_) in ((0, 0), (0, 1), (1, 1), (1, 2)):           # a lock of hair: four connected pixels
                yy, xx = y0_ + dy_, x0_ - face * dx_
                if 0 <= yy < H and 0 <= xx < W and body[yy, xx] and a[yy, xx] == code:
                    a[yy, xx] = new
    def plane(m, cx_, cy_):
        """A muscle mass as a shaped plane: its edge lit toward the upper left, shaded toward the lower right."""
        e = m & ~ndi.binary_erosion(m, iterations=1)
        litside = e & ((X - cx_) + (Y - cy_) < 0)
        a[litside] = np.minimum(a[litside] + 1, (a[litside] // 8) * 8 + 5)
        shd = e & ((X - cx_) + (Y - cy_) > 1)
        a[shd] = np.maximum(a[shd] - 1, (a[shd] // 8) * 8)
    if kind in ('horse', 'cow'):                                 # shoulder, forearm, barrel and haunch
        for ux, uy, sx_, sy_ in ((0.55, -0.05, 0.3, 0.68), (0.62, 0.72, 0.16, 0.3), (0.0, 0.18, 0.36, 0.7), (-0.55, -0.12, 0.36, 0.78)):
            pcx, pcy = cx + face * ux * rx, by + uy * ry
            plane(body & _ell(X, Y, pcx, pcy, rx * sx_, ry * sy_), pcx, pcy)
    if kind == 'cow':                                            # the last ribs showing as shallow arcs on the barrel
        for k in range(3):
            rcx = cx + face * rx * (0.05 + 0.13 * k)
            arc = body & (np.abs(np.hypot((X - rcx) / 7.0, (Y - (by + ry * 0.05)) / 9.0) - 1.0) < 0.09) & ((X - rcx) * face < 0) & (band >= 2) & (band <= 5)
            a[arc] = np.maximum(a[arc] - 1, (a[arc] // 8) * 8)
    if kind == 'cow':                                            # the hip bone, a small angular plane
        hpx, hpy = cx - face * rx * 0.45, by - ry * 0.62
        hipm = body & (np.abs(X - hpx) + 1.6 * np.abs(Y - hpy) <= 5)
        plane(hipm, hpx, hpy)
    if kind == 'horse':                                          # the chest and the hindquarter, each its own mass
        crease = body & (np.abs(np.hypot((X - (cx - face * rx * 0.28)) / (rx * 0.5), (Y - (by + ry * 0.1)) / (ry * 1.05)) - 1.0) < 0.05) \
            & ((X - (cx - face * rx * 0.28)) * face > 0) & (depth > 0.15) & (depth < 0.85)
        a[crease] = np.maximum(a[crease] - 1, (a[crease] // 8) * 8)
        chest = body & _ell(X, Y, cx + face * rx * 0.78, by + ry * 0.35, rx * 0.22, ry * 0.45) & (zone >= 1)
        a[chest & (zone == 1)] = np.minimum(a[chest & (zone == 1)] + 1, (a[chest & (zone == 1)] // 8) * 8 + 5)
    # the accents a painter would place: the shine on the shoulder and the hip bone (a few pixels,
    # one cluster each), the patches' edges a step darker, a cool rim where the back turns from the
    # light, the shade where the legs go up into the body
    for lx_, ly_ in ((0.42, -0.5), (-0.5, -0.55)):
        shine = body & _ell(X, Y, cx + face * rx * lx_ - face * 2, by + ry * ly_, 2.6, 1.6) & (band <= 2)
        a[shine] = np.minimum(a[shine] + 1, (a[shine] // 8) * 8 + 5)
    if B['coat'] in ('pied', 'tan'):
        pe = dark & ~ndi.binary_erosion(dark, iterations=1) & (band >= 2)
        a[pe] = np.maximum(a[pe] - 1, (a[pe] // 8) * 8)
    back_rim = body & (Y - topr <= 1) & (east > 0.45)
    a[back_rim] = np.maximum(a[back_rim] - 1, (a[back_rim] // 8) * 8)
    for lx_ in (-0.55, 0.5):
        ao = body & (np.abs(X - (cx + face * lx_ * rx)) <= B['lw'] / 2 + 1) & (Y >= bottom - 3) & (Y < bottom - 1)
        a[ao] = np.maximum(a[ao] - 1, (a[ao] // 8) * 8)
    rim = body & (Y - topr <= 0) & (east < 0.5) & ~dark
    a[rim] = C('sand_warm' if B['coat'] in ('bay', 'pig', 'goat_b') else 'plaster', 5)
    if kind == 'cow':                                            # the dewlap, a fold of skin hanging under the throat
        dew = _ell(X, Y, cx + face * rx * 0.92, by + ry * 0.3, 4.5, 7.5) & ~body & (a < 0)
        rpaint(a, dew, [body_sets[0]], 3.0 - 1.0 * ((X - (cx + face * rx * 0.92)) * face > 1.5) - 0.8 * (Y > by + ry * 0.55), 0)
    if B['udder']:
        ud = _ell(X, Y, cx - face * rx * 0.2, by + ry + 1, 4.5, 3.2) & ~body
        rpaint(a, ud, muzzle_sets, 2.4 + sphere_light(X, Y, cx - face * rx * 0.2, by + ry, 4.5, 3.2), 0)
    # the tail: a swish (a pig's a curl)
    tx0, ty0 = cx - face * (rx - 2), by - ry * 0.45
    if kind == 'pig':
        for k in range(7):
            ang = k * 1.1
            px_, py_ = tx0 - face * (2.5 + 1.6 * math.cos(ang) + 0.4 * k), ty0 - 1 + 1.8 * math.sin(ang)
            a[int(round(py_)):int(round(py_)) + 2, int(round(px_))] = C('clay' if k % 2 else 'sand_warm', 3 + (k % 2))
    elif B['tail']:
        sw = {'tail1': 2.5, 'tail2': 5.0}.get(frame, 0.0)
        tip = (tx0 - face * (2 + sw), ty0 + B['tail'])
        tm = V.seg_mask(a.shape, tx0, ty0, tip[0], tip[1], 1.0 if kind != 'horse' else 2.4) & ~body
        rpaint(a, tm, mark_sets if kind == 'horse' else body_sets, 1.8 + 0.8 * (Y < ty0 + 4), 0.3)
        if kind == 'horse':                                      # the tail in three locks, the top of each lit
            for k in (-1, 0, 1):
                lk = V.seg_mask(a.shape, tx0 - face * (1 + k), ty0 + 4, tip[0] - face * (k * 2), tip[1] - 2 + abs(k) * 2, 0.9) & ~body
                rpaint(a, lk, [mark_sets[0]], np.where(Y < ty0 + 10, 2.6, 1.4) - 0.6 * (k == 1), 0)
        if kind in ('cow', 'calf'):
            a[_ell(X, Y, tip[0], tip[1], 2.0, 3.0) & ~body] = C('soot', 1)
    # the head: up, dipped half or right down to the grass
    hrx, hry, reach, lift = B['head']
    dip = {'dip1': 0.5, 'dip2': 1.0}.get(frame, 0.0)
    hx = cx + face * (rx + reach - 2 * dip)
    hy_up = by - lift
    hy_dn = fy - hry - 1
    hy = hy_up + (hy_dn - hy_up) * dip + {'snuff1': 1, 'snuff2': 2}.get(frame, 0)
    nx0, ny0 = cx + face * rx * 0.6, by - ry * 0.3
    neck = V.seg_mask(a.shape, nx0, ny0, hx - face * hrx * 0.4, hy, hrx * (0.85 if kind != 'horse' else 1.2)) & ~body
    if kind == 'horse':                                          # a thick neck, its crest arching up from the withers
        neck |= V.seg_mask(a.shape, nx0 - face * 5, ny0 + 5, hx - face * hrx * 0.2, hy + 4, hrx * 1.25) & ~body
        neck |= V.seg_mask(a.shape, nx0 - face * 7, ny0 - 4, hx - face * hrx * 0.7, hy - hry * 0.4, hrx * 0.8) & ~body
    rpaint(a, neck, [body_sets[0] if kind != 'pig' else ('crag', 'crag_warm', 'berry')],
           2.4 + 1.6 * (sphere_light(X, Y, nx0, ny0 - 6, 9, 12) > 0.25) - 0.9 * (Y > ny0 + 4), 0)
    if B.get('mane'):
        # the mane in three locks falling from the crest, each lit on its top
        groove = V.seg_mask(a.shape, nx0 + face * 1, ny0 + 7, hx - face * hrx * 0.1, hy + hry * 0.55, 0.6) & neck & ~body
        a[groove] = np.maximum(a[groove] - 1, (a[groove] // 8) * 8)      # the jugular groove down the neck
        for ux, uy, sx_, sy_ in ((-0.42, 0.62, 4.0, 5.0), (0.3, 0.1, 4.5, 7.5), (-0.62, -0.62, 6.0, 3.0)):   # stifle, triceps, croup
            pcx, pcy = cx + face * ux * rx, by + uy * ry
            plane(body & _ell(X, Y, pcx, pcy, sx_, sy_), pcx, pcy)
        nplane = neck & _ell(X, Y, (nx0 + hx) / 2, (ny0 + hy) / 2 + 3, hrx * 0.9, hry * 0.9)
        plane(nplane, (nx0 + hx) / 2, (ny0 + hy) / 2 + 3)             # the neck's long muscle
        crest = V.seg_mask(a.shape, nx0 - face * 8, ny0 - 8, hx - face * hrx * 0.9, hy - hry * 0.75, 2.2) & ~body
        locks = crest.copy()
        for k in range(3):
            f_ = (k + 0.5) / 3
            mx_ = (nx0 - face * 8) * (1 - f_) + (hx - face * hrx * 0.9) * f_
            my_ = (ny0 - 8) * (1 - f_) + (hy - hry * 0.75) * f_
            locks |= V.seg_mask(a.shape, mx_, my_, mx_ - face * 3, my_ + 6, 1.8) & ~body
        rpaint(a, locks, [mark_sets[0]], 1.3 + 1.3 * crest, 0)       # the crest's lit top, the locks falling in shade
        fl = V.seg_mask(a.shape, hx - face * hrx * 0.2, hy - hry * 0.95, hx + face * hrx * 0.3, hy - hry * 0.45, 1.3)
        rpaint(a, fl, [mark_sets[0]], 2.2 + 1.0 * (Y < hy - hry * 0.75), 0)        # the forelock
    head = _ell(X, Y, hx, hy, hrx, hry)
    if kind == 'horse':                                          # a long face down to the muzzle
        head |= V.seg_mask(a.shape, hx, hy - 2, hx + face * hrx * 0.9, hy + hry * 0.9, hrx * 0.78)
    head_sets = mark_sets if B['coat'] == 'pied' else ([('crag', 'crag_warm', 'berry')] if kind == 'pig' else
                                                       [('earth_cool', 'earth_warm', 'sand_warm')] if kind == 'goat_b' else body_sets)
    if kind == 'pig':                                            # a round, heavy jowl under the cheek
        jowl = _ell(X, Y, hx - face * hrx * 0.25, hy + hry * 0.6, hrx * 0.75, hry * 0.5) & ~body
        head = head | jowl
    hl = sphere_light(X, Y, hx - face * 1, hy - 1, hrx, hry)
    rpaint(a, head, [head_sets[0]], 2.4 + 1.0 * (hl > 0.0) + 1.0 * (hl > 0.45) - 0.8 * (hl < -0.45) + (0.6 if kind == 'goat_b' else 0), 0)
    if kind == 'pig':
        jl = jowl & (Y > hy + hry * 0.75)
        a[jl] = np.maximum(a[jl] - 1, (a[jl] // 8) * 8)
    # where the head stands before the neck or the body, a shadow line parts them
    parted = head & ~ndi.binary_erosion(head, iterations=1) & ndi.binary_dilation(body | neck, iterations=1) & (X * face < hx * face)
    a[parted] = np.maximum(a[parted] - 2, (a[parted] // 8) * 8)
    if kind == 'goat_b':                                         # a wider shadow edge: the head stands clear of the shoulder
        part2 = ndi.binary_dilation(parted, iterations=1) & head & (X * face < hx * face)
        a[part2] = np.maximum(a[part2] - 1, (a[part2] // 8) * 8)
    if B['coat'] in ('pied', 'bay', 'tan'):                      # a white blaze down the face
        blaze = head & (np.abs(X - (hx + face * hrx * 0.35)) < (1.2 if kind == 'horse' else 2.2)) & (Y < hy + hry * 0.4)
        rpaint(a, blaze, [('stone_cool', 'plaster_warm', 'plaster')], 3.6 + (Y < hy), 0)
    # the muzzle (or a pig's snout), lighter, its nostrils
    jaw = {'chew': 1, 'chew2': 1}.get(frame, 0)
    if B.get('snout'):
        sx, sy = hx + face * (hrx + 1.5), hy + 2 + jaw
        disc = _ell(X, Y, sx, sy, 3.2, 3.8)
        rpaint(a, disc, muzzle_sets, 3.0 + 1.4 * sphere_light(X, Y, sx - face, sy - 1, 3.2, 3.8), 0)
        for dy_ in (-1, 1):
            a[int(round(sy + dy_)), int(round(sx + face * 0.5))] = C('berry_cool', 1)
        a[int(round(sy - 3)), int(round(sx - face)):int(round(sx - face)) + 2] = C('plaster_warm', 5)   # the snout's highlight
    else:
        mx, my = hx + face * hrx * (0.5 if kind != 'horse' else 1.15), hy + hry * (0.5 if kind != 'horse' else 0.95) + jaw
        mrx, mry = hrx * (0.72 if kind != 'horse' else 0.62), hry * 0.42
        muzzle = _ell(X, Y, mx, my, mrx, mry)
        rpaint(a, muzzle, muzzle_sets, 3.0 + 1.2 * sphere_light(X, Y, mx - face, my - 1, mrx, mry) - 0.8 * (Y > my + mry * 0.5), 0.3)
        nxp = int(round(mx + face * mrx * 0.45))
        a[int(round(my - 0.5)), nxp] = C('soot', 1)
        a[int(round(my - 0.5)), nxp - face * 2] = C('soot', 1) if kind in ('cow', 'calf', 'horse') else a[int(round(my - 0.5)), nxp - face * 2]
        a[int(round(my + mry * 0.6)), int(round(mx - face * 1)):int(round(mx + face * 2)) + 1] = C('soot', 2)   # the mouth
    # the eyes: the near one large with its highlight, the far one beyond the nose bridge
    ex, ey = int(round(hx - face * hrx * 0.1)), int(round(hy - hry * 0.18))
    a[ey - 1:ey + 1, ex:ex + 2] = C('soot', 0)
    a[ey - 1, ex + (1 if face < 0 else 0)] = C('plaster', 5)
    a[ey + 1, ex:ex + 2] = C(head_sets[0][0], 2)
    fx2 = int(round(hx + face * hrx * 0.62))
    a[ey - 1:ey + 1, fx2] = C('soot', 0)
    # the face's planes (round 5): a darker brow over the eye, a lighter cheek below and behind it,
    # a jaw line on the cow and the horse; one expression a kind
    def step(m, k):
        a[m] = np.clip(a[m] + k, (a[m] // 8) * 8, (a[m] // 8) * 8 + 5)
    lift_brow = 1 if kind.startswith('goat') else 0                  # a goat's raised brow: cheeky
    brow = head & (Y >= ey - 3 - lift_brow) & (Y <= ey - 2 - lift_brow) & (np.abs(X - (ex + 0.5)) <= 2)
    step(brow, -1)
    cheek = head & (Y >= ey + 2) & (Y <= ey + 3) & ((X - ex) * face <= -1) & ((X - ex) * face >= -4)
    step(cheek, 1)
    if kind in ('cow', 'calf', 'horse'):
        jaw = head & ~ndi.binary_erosion(head, iterations=1) & (Y > hy + hry * 0.15) & ((X - hx) * face < hrx * 0.5)
        step(jaw, -1)
    if kind == 'cow':                                            # placid: the lid half down over the eye
        a[ey - 1, ex:ex + 2] = C(head_sets[0][1], 2)
        a[ey, ex + (1 if face < 0 else 0)] = C('plaster', 5)
    elif kind == 'horse':                                        # alert: the white of the eye showing
        a[ey, ex + (2 if face > 0 else -1)] = C('plaster_warm', 4)
    elif kind.startswith('goat'):                                # cheeky: the mouth's corner turned up
        if kind == 'goat_b':                                     # a pale eye ring and a pale muzzle
            ring_ = head & (np.abs(np.hypot(X - (ex + 0.5), Y - (ey - 0.5)) - 2.2) < 0.7) & (a // 8 != FI['soot'])
            rpaint(a, ring_, [('sand_cool', 'sand', 'plaster_warm')], np.full(a.shape, 4.0), 0)
        mcx = int(round(hx + face * hrx * 0.5 - face * 2))
        a[int(round(hy + hry * 0.5)) - 1, mcx] = C('soot', 2)
    # the ears break the outline
    flick = 2 if frame == 'ear' else 0
    top_y = hy - hry * 0.7
    if B['ears'] == 'side':
        for side, far in ((-1, False), (1, True)):
            e0 = hx + side * face * hrx * 0.55
            em = V.seg_mask(a.shape, e0, top_y + 1, e0 + side * face * 6, top_y - 1 - (flick if not far else 0), 1.6)
            rpaint(a, em & ~head, head_sets, 2.4 - (0.9 if far else 0) + 0.8 * (Y < top_y), 0.3)
            a[em & ~head & (np.abs(X - (e0 + side * face * 4)) < 1)] = C('berry_cool', 2 if far else 3)
    elif B['ears'] == 'up':
        for k, far in ((-1, True), (1, False)):
            e0 = hx - face * hrx * 0.3 + k * 2
            em = V.seg_mask(a.shape, e0, hy - hry + 2, e0 - face * 1, hy - hry - 5 - (flick if not far else 0), 1.3)
            rpaint(a, em & ~head, body_sets, 2.4 - (0.9 if far else 0) + 0.8 * (Y < hy - hry), 0.3)
    elif B['ears'] == 'flop':                                    # a pig's big ears tipped forward over its eyes
        for k, far in ((-1, True), (1, False)):
            e0 = hx - face * 2 + k * 3.5
            tri = (Y >= top_y - 3) & (Y <= top_y + 4) & (np.abs(X - (e0 + face * (Y - (top_y - 3)) * 0.8)) <= 2.2 - 0.25 * np.abs(Y - top_y))
            rpaint(a, tri, [('crag', 'clay', 'clay')], 3.4 - (1.0 if far else 0) + 0.8 * (Y < top_y), 0)
            rimm = tri & ~ndi.binary_erosion(tri, iterations=1) & (Y < top_y + 2)
            rpaint(a, rimm, [('clay', 'clay', 'sand_cool')], np.full(a.shape, 4.6 if not far else 3.6), 0)   # backlit at the rim
    else:                                                        # a goat's long ears out and down
        for side, far in ((-1, False), (1, True)):
            e0 = hx + side * face * hrx * 0.6
            em = V.seg_mask(a.shape, e0, top_y + 2, e0 + side * face * 5, top_y + 5 - (flick if not far else 0), 1.4)
            rpaint(a, em & ~head, head_sets, 2.6 - (0.9 if far else 0), 0.3)
    if B['horns']:
        hb = (hx - face * hrx * 0.1, hy - hry * 0.8)
        if kind.startswith('goat'):
            horn = V.seg_mask(a.shape, hb[0], hb[1], hb[0] - face * 4, hb[1] - 6, 1.2) | V.seg_mask(a.shape, hb[0] - face * 4, hb[1] - 6, hb[0] - face * 8, hb[1] - 4, 1.0)
        else:
            horn = V.seg_mask(a.shape, hb[0] - 3, hb[1], hb[0] - 5, hb[1] - 4, 1.1) | V.seg_mask(a.shape, hb[0] + 3, hb[1], hb[0] + 5, hb[1] - 4, 1.1)
        rpaint(a, horn & ~head, [('stone_warm', 'sand', 'plaster')], 3.6 - 0.9 * (Y > hb[1] - 2), 0)
        hh = horn & ~head & (Y <= hb[1] - 4) & ((X - hb[0]) * face > -4)
        a[hh] = C('plaster', 5)                                  # the horn's highlight
    if B.get('beard'):
        bm = V.seg_mask(a.shape, hx + face * hrx * 0.5, hy + hry * 0.85, hx + face * hrx * 0.35, hy + hry * 0.85 + 5 + jaw, 1.1)
        rpaint(a, bm & ~head, [('stone_cool', 'stone_warm', 'sand')], 2.6, 0)
    V.finish(p)
    return p


def beast_frames(kind, face, seed, shift):
    fr = [beast(kind, f, face, seed) for f in BEAST_FRAMES[kind]]
    return fr[shift:] + fr[:shift]


# ------------------------------------------------------------------------------------------------
# the coop and the shelter
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# hay
# ------------------------------------------------------------------------------------------------
STRAW = [('brass', 'brass_warm', 'sand_warm'), ('earth_warm', 'brass', 'brass_warm'), ('brass', 'sand_warm', 'sand')]


def bale(a, x0, y0, w, h, d, rng, east=True):
    """A compressed bale, rounded at its arrises: its top (d texels deep) lit and combed along its
    length, its south face the cut ends of the stalks (a stipple of light ends and dark holes), its
    east end turning into shade, two twines wrapping the volume over the top, down the front and
    round the end, loose wisps at the edges, a dark line where it rests."""
    Y, X = grid(a)
    nz = noise(a.shape, rng, 0.7)
    R = 3.0
    yt, yf, ye = y0, y0 + d, y0 + d + h
    box = (X >= x0) & (X < x0 + w) & (Y >= yt) & (Y < ye)
    cx0, cx1 = np.clip(X, x0 + R, x0 + w - 1 - R), None
    # rounded corners: distance to the inner box
    ix = np.clip(X, x0 + R, x0 + w - 1 - R)
    iy = np.clip(Y, yt + R, ye - 1 - R)
    box &= (X - ix) ** 2 + (Y - iy) ** 2 <= R * R
    top = box & (Y < yf)
    front = box & (Y >= yf)
    u = (X - x0) / max(1, w - 1)                                 # 0 west .. 1 east
    # the top: lit, combed along x, darker towards the east end and the far edge
    tt = 4.1 - 1.2 * np.clip(u - 0.65, 0, 1) * 3 - 0.6 * (Y == yt) + 0.8 * (Y == yf - 1) + 0.3 * (nz - 0.5)
    tt += 0.6 * (((Y + (X // 6)) % 3) == 0)                      # combed: strands 6 px long
    rpaint(a, top, STRAW, tt, np.where(nz > 0.5, 0.6, 0.1))
    # the cut face: stalk ends, a stipple of lit ends and dark holes, rounded into shade at the
    # foot and the east end
    ft = 3.0 + 0.6 * (Y == yf) - 1.0 * (Y >= ye - 2) - 1.3 * np.clip(u - 0.7, 0, 1) * 3 + 0.4 * (nz - 0.5)
    def blocks(p_):                                              # stalk ends and holes in small 2 x 2 tufts: clusters, not a stipple
        b = rng.random(a.shape) < p_
        return b | np.roll(b, 1, axis=1) | np.roll(b, 1, axis=0) | np.roll(np.roll(b, 1, axis=0), 1, axis=1)
    ends = blocks(0.022)
    holes = blocks(0.012) & ~ends
    ft = np.round(ft)                                            # whole steps, so a tuft is not split by the gradient
    ft = ft + 1.2 * ends - 1.2 * holes
    rpaint(a, front, STRAW, ft, np.where(nz > 0.5, 0.1, 0.6))
    a[front & (Y == yf)] = C('brass', 2)                         # the arris's shade under the lit top
    a[box & (Y == ye - 1)] = C('earth_cool', 1)                  # where it rests
    # two twines: over the top, down the front, a lit strand and its shade
    for tx in (x0 + w // 4, x0 + 3 * w // 4 - 1):
        tw = box & (X >= tx) & (X < tx + 2)
        a[tw] = C('clay_cool', 2)
        a[tw & (X == tx) & (Y < yf)] = C('clay', 4)
        a[tw & (X == tx) & (Y >= yf)] = C('clay', 3)
        a[box & (Y == yf - 1) & (X >= tx - 1) & (X < tx + 3)] = C('clay', 3)       # the twine bends over the arris
    # loose wisps at the top edge and the ends
    for _ in range(int(w / 7)):
        sx = rng.uniform(x0, x0 + w)
        sy = yt + rng.uniform(-0.5, 1.5)
        L = rng.uniform(2, 4)
        ang = rng.uniform(-2.6, -0.5)
        m = V.seg_mask(a.shape, sx, sy, sx + L * math.cos(ang), sy + L * math.sin(ang), 0.7) & ~box
        a[m] = C('sand_warm', 4) if rng.random() < 0.6 else C('brass_warm', 3)


def hay_bales(seed=0):
    """Three bales: two side by side, one across them on top (about 68 x 52 texels), with stalks
    fallen round their foot."""
    rng = np.random.default_rng(seed)
    p = canvas(82, 66, 41, 60)
    a = p.a
    bale(a, 6, 32, 34, 14, 12, rng)
    bale(a, 40, 32, 34, 14, 12, rng)
    bale(a, 20, 12, 38, 14, 12, rng)
    Y, X = grid(a)
    # the top bale's shade on the two below
    sh = (Y >= 38) & (Y < 40) & (X >= 22) & (X < 60) & (a >= 0)
    a[sh] = np.maximum(a[sh] - 1, (a[sh] // 8) * 8)
    for _ in range(10):
        x = rng.uniform(4, 78)
        V.bar(a, x, 59, x + rng.uniform(-5, 5), 59 - rng.uniform(0, 1), 0.75, 'brass_warm' if rng.random() < 0.5 else 'brass', 3)
    V.finish(p)
    return p


def hay_heap(seed=0):
    """Loose hay forked out for the stock (about 60 x 34 texels): a dome of tangled stalks laid in
    layers, the deep layer dark and the top layer lit on its upper left, a darker core where the
    stalks overhang it, stalks fallen round its foot."""
    rng = np.random.default_rng(seed)
    p = canvas(76, 48, 38, 42)
    a = p.a
    Y, X = grid(a)
    cx, cy, rx, ry = 38, 28, 29, 15
    rough = ndi.gaussian_filter(rng.random(a.shape), 1.2)
    m = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1 + 1.6 * (rough - 0.5)) & (Y < 42)
    lit = sphere_light(X, Y, cx, cy, rx, ry)
    nz = noise(a.shape, rng, 0.9)
    rpaint(a, m, STRAW, 1.4 + 1.4 * lit, 0.3)                          # the dark core between the layers
    for layer, (n, base, fams) in enumerate(((60, 2.2, STRAW[1:2]), (70, 3.2, STRAW[:1]), (55, 4.2, STRAW[2:]))):
        for _ in range(n):
            x0, y0 = rng.uniform(cx - rx, cx + rx), rng.uniform(cy - ry, 41)
            ang = rng.uniform(-0.8, 0.8) + (math.pi if rng.random() < 0.5 else 0)
            L = rng.uniform(3, 8)
            s = V.seg_mask(a.shape, x0, y0, x0 + L * math.cos(ang), y0 + L * math.sin(ang), 0.7) & m
            if layer == 2:
                s &= lit > 0.0                                          # the top layer catches the light
            tone = base + 1.2 * lit + rng.choice([-0.6, 0.0, 0.6])
            rpaint(a, s, fams if rng.random() < 0.7 else STRAW, tone, rng.random())
    a[m & (Y >= 40)] = C('brass', 1)                                    # where it lies on the ground
    for _ in range(14):
        x = rng.uniform(cx - rx - 4, cx + rx + 4)
        V.bar(a, x, 42, x + rng.uniform(-6, 6), 42 - rng.uniform(0, 2), 0.5, 'brass', 3)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the trough
# ------------------------------------------------------------------------------------------------
def trough(seed=0):
    """A stone stock trough (84 x 40 texels): its rim lit along the top and the west end, the inner
    north wall in shade above the water, the water dark in its depth and catching the sky in a
    pale streak and a glint near the south rim, the outer face of dressed stone in courses darker
    at the foot, mud trodden round its base and tufts of grass the hooves missed."""
    rng = np.random.default_rng(seed)
    p = canvas(96, 50, 48, 44)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    x0, x1 = 8, 88
    yt, yr, yb = 8, 28, 44                    # the rim's top, the front face's top, the foot
    # mud and trodden grass round the base (under everything else)
    mud = (((X - 48) / 42) ** 2 + ((Y - (yb - 2)) / 5.0) ** 2 <= 1 + 0.5 * (nz - 0.5)) & (Y >= yb - 6)
    rpaint(a, mud, [('earth_cool', 'earth', 'earth_warm'), ('soot', 'earth_cool', 'earth')], 1.6 + 1.2 * (nz - 0.3), nz)
    a[mud & (rng.random(a.shape) < 0.06)] = C('water_cool', 2)                     # a puddle's glint in a hoofprint
    for _ in range(8):
        tx = int(rng.uniform(x0 - 4, x1 + 4))
        for k in range(int(rng.integers(3, 6))):
            a[yb - 1 - k, tx + (k > 2)] = C('grass', 3 if k < 2 else 4)
        a[yb - 1, tx + 1] = C('grass_cool', 2)
    # the outer front face: dressed stone in two courses, lit west end, dark foot
    face = (X >= x0) & (X < x1) & (Y >= yr) & (Y < yb - 2)
    course = (Y - yr) // 6
    block = (X - x0 + 7 * (course % 2)) // 14
    tf = 3.0 + 0.5 * np.sin(block * 2.7 + course) - 1.2 * (((X - x0 + 7 * (course % 2)) % 14) == 13) \
        - 1.0 * (((Y - yr) % 6) == 5) - 0.9 * (Y >= yb - 4) + 0.9 * (X < x0 + 2) - 0.9 * (X > x1 - 4)
    rpaint(a, face, [('stone_cool', 'stone', 'stone_warm'), ('stone_cool', 'ashlar', 'ashlar_warm'), ('slate_cool', 'stone_warm', 'ashlar_warm')],
           tf + 0.9 * (nz - 0.5), np.mod((block * 2 + course) * 0.37, 1.0))
    chips = face & (rng.random(a.shape) < 0.04)
    a[chips] = C('stone_warm', 4)
    a[face & (nz > 0.78) & (Y > yb - 8)] = C('leaf_cool', 2)                       # moss at the damp foot
    # the rim: a lit top all round, the inner basin below it
    outer = (X >= x0) & (X < x1) & (Y >= yt) & (Y < yr)
    inner = (X >= x0 + 5) & (X < x1 - 5) & (Y >= yt + 3) & (Y < yr - 2)
    rim = outer & ~inner
    rpaint(a, rim, [('stone_cool', 'stone', 'stone_warm')], 4.0 + 0.8 * (Y == yt) + 0.6 * (X < x0 + 3) - 1.2 * (X > x1 - 4) - 1.0 * (Y >= yr - 2), 0)
    a[rim & (Y >= yr - 1)] = C('stone', 2)                                          # the front arris in shade
    # the inner north wall in shade, then the water: dark in its depth, a pale streak of sky and
    # a glint near the south rim, a ring where it meets the stone
    wallm = inner & (Y < yt + 6)
    rpaint(a, wallm, [('stone_cool', 'stone_cool', 'stone')], 1.4 + 0.5 * (Y - yt - 3) / 3, 0)
    water = inner & ~wallm
    dep = (Y - (yt + 6)) / max(1, (yr - 2) - (yt + 6))
    rpaint(a, water, [('water_cool', 'water', 'water_warm'), ('water_cool', 'water_cool', 'water'), ('dusk_cool', 'water_cool', 'sky')],
           1.0 + 2.0 * dep + 0.8 * (nz - 0.5), nz)
    a[water & (rng.random(a.shape) < 0.03) & (dep > 0.4)] = C('sky', 4)                 # ripples catching the sky
    a[water & (Y == yt + 6)] = C('water_cool', 0)
    streak = water & (np.abs(Y - (yr - 4)) < 0.6) & (X > x0 + 12) & (X < x0 + 40)
    a[streak] = C('sky', 4)
    a[water & (np.abs(Y - (yr - 5)) < 0.6) & (X > x0 + 48) & (X < x0 + 58)] = C('sky', 3)
    a[water & (Y == yr - 3) & ((X == x0 + 20) | (X == x0 + 21))] = C('snow', 5)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# the kitchen garden's beds
# ------------------------------------------------------------------------------------------------
CROPS = {'dug': ('cabbage', 'leek', 'lettuce'), 'dug_b': ('carrot', 'cabbage', 'beans')}


LEAF = [('leaf_cool', 'leaf', 'leaf_warm'), ('grass_cool', 'leaf', 'grass_warm'), ('leaf_cool', 'grass', 'leaf_warm')]
SOIL = [('earth_cool', 'earth', 'earth_warm'), ('path_cool', 'path', 'path_warm'), ('earth_cool', 'earth_warm', 'sand_warm')]
BURNT = [('soot', 'ash', 'ash'), ('stone_cool', 'ash', 'stone'), ('soot', 'earth_cool', 'earth'), ('slate_cool', 'stone_cool', 'ash')]


def _plant(a, crop, px, cy, rng, burnt=False, s=1.0, lean=0.0):
    """One plant on its ridge, sized `s` (0.7 .. 1.25: some came on faster) and leaning `lean`
    texels at its top, lit on its upper left with its shade east and down on the soil."""
    Y, X = grid(a)
    if burnt:
        # a charred stub: a dark stalk and a curl of black leaf, ash at its foot
        h = int(4 + 4 * s)
        a[V.seg_mask(a.shape, px, cy + 1, px + lean, cy - h, 0.7)] = C('soot', 1)
        a[V.seg_mask(a.shape, px - 0.4, cy + 1, px - 0.4 + lean, cy - h, 0.3)] = C('soot', 3)
        cm = ((X - px - lean - 1.5) / (2.0 + 1.5 * s)) ** 2 + ((Y - cy + h) / 1.5) ** 2 <= 1
        a[cm] = C('soot', 0 if rng.random() < 0.5 else 2)
        a[cm & (X < px + lean + 1) & (Y < cy - h)] = C('soot', 4)                    # a charred leaf's lit curl
        a[int(cy + 1), int(px - 2):int(px + 3)] = C('ash', 4)
        a[int(cy + 2), int(px - 1):int(px + 3)] = C('earth_cool', 1)
        if rng.random() < 0.25:
            a[int(cy), int(px + 1)] = C('lava', 3)                                   # an ember still glowing
        return
    mix = rng.random()
    if crop == 'cabbage':
        rx_, ry_ = 5.6 * s, 4.4 * s
        m = ((X - px) / rx_) ** 2 + ((Y - cy) / ry_) ** 2 <= 1 + 0.18 * np.sin(np.arctan2(Y - cy, X - px) * 6 + mix * 6)
        rpaint(a, m, LEAF, 2.6 + 1.7 * sphere_light(X, Y, px, cy, rx_, ry_), mix)
        heart = ((X - px + 0.5 - lean * 0.3) / (2.8 * s)) ** 2 + ((Y - cy + 0.8) / (2.2 * s)) ** 2 <= 1
        rpaint(a, heart, [('leaf', 'leaf_warm', 'grass_warm')], 4.0 + sphere_light(X, Y, px, cy - 1, 3, 2), 0)
        for k in range(4):                                     # the outer leaves' veins
            ang = k * math.pi / 2 + 0.6 + mix
            a[V.seg_mask(a.shape, px, cy, px + 4.5 * s * math.cos(ang), cy + 3.5 * s * math.sin(ang), 0.4) & m & ~heart] = C('leaf_cool', 2)
    elif crop == 'lettuce':
        rx_, ry_ = 4.2 * s, 3.4 * s
        m = ((X - px) / rx_) ** 2 + ((Y - cy) / ry_) ** 2 <= 1 + 0.25 * np.sin(np.arctan2(Y - cy, X - px) * 7 + mix * 5)
        rpaint(a, m, [('leaf', 'grass_warm', 'grass_warm'), ('grass', 'grass_warm', 'leaf_warm')], 3.0 + 1.6 * sphere_light(X, Y, px, cy, rx_, ry_), mix)
        a[m & (((X - px) ** 2 + (Y - cy) ** 2) < 1.2)] = C('grass_warm', 5)
    elif crop == 'leek':
        for dx, h, t in ((-1.5, 9, 3), (0.5, 11, 4), (2.0, 8, 2)):
            a[V.seg_mask(a.shape, px + dx * 0.3, cy + 1, px + dx + lean, cy + 1 - h * s, 0.8)] = C('leaf_cool', t)
        a[V.seg_mask(a.shape, px + 0.5, cy, px + 0.5 + lean, cy - 9 * s, 0.4)] = C('leaf', 4)
        a[int(cy - 1):int(cy + 2), int(px - 1):int(px + 2)] = C('plaster', 4)       # the white shank
        a[int(cy + 1), int(px - 1):int(px + 2)] = C('plaster_warm', 3)
    elif crop == 'carrot':
        for dx in (-2, 0, 2):
            a[V.seg_mask(a.shape, px, cy + 1, px + dx * s + lean, cy - (6 - abs(dx)) * s, 0.6)] = C('grass', 4 if dx < 1 else 3)
        fm = ((X - px - lean) / (3.0 * s)) ** 2 + ((Y - cy + 5 * s) / (2.0 * s)) ** 2 <= 1
        rpaint(a, fm, [('grass', 'grass_warm', 'leaf_warm')], 3.4 + 1.2 * sphere_light(X, Y, px, cy - 5, 3, 2), 0)
        a[int(cy + 1), int(px - 1):int(px + 2)] = C('clay', 4)                      # the shoulder
        a[int(cy + 1), int(px + 1)] = C('clay', 3)
    elif crop == 'beans':
        a[V.seg_mask(a.shape, px, cy + 1, px + lean, cy - 18 * s, 0.7)] = C('timber', 3)        # the cane
        a[V.seg_mask(a.shape, px - 0.5, cy + 1, px - 0.5 + lean, cy - 18 * s, 0.3)] = C('timber_warm', 4)
        for k in range(5):
            ly = cy - 3 - k * 3 * s
            lx = px + lean * (k / 5) + (2 if k % 2 else -2)
            lm = ((X - lx) / 2.0) ** 2 + ((Y - ly) / 1.5) ** 2 <= 1
            rpaint(a, lm, LEAF, 3.6 if k % 2 == 0 else 2.6, mix)
        a[int(cy - 9 * s), int(px + 2)] = C('berry', 4)                                # a flower
    # the plant's shade on the soil, east and down
    sh = ((X - px - 2.5 * s) / (4.0 * s)) ** 2 + ((Y - cy - 3.5 * s) / 1.4) ** 2 <= 1
    soil_f = [FI[f] for f in ('earth', 'earth_warm', 'path', 'path_warm', 'sand_warm')]
    a[sh & np.isin(a // 8, soil_f)] = C('earth_cool', 1)


def beds(kind='dug', seed=0):
    """A kitchen garden's beds in a dug patch (240 x 120 texels, ten cells by five): three soil
    ridges east to west with a trodden furrow between them, each ridge's crest catching the light
    and the furrow under it in shade, crumbs of soil and clods lit on their upper left, a row of
    one crop on each ridge, the plants of a row each its own size and lean with a gap where one
    failed; the patch's edge dug ragged into the turf, the grass hanging over it. `scorched`: the
    same ground burnt grey, the crops black stubs, ash drifted in the furrows, a few green shoots
    coming back."""
    burnt = kind == 'scorched'
    rng = np.random.default_rng(seed)
    W, H = 252, 136
    p = canvas(W, H, W // 2, H - 6)
    a = p.a
    Y, X = grid(a)
    x0, x1, y0, y1 = 8, W - 8, 10, H - 6
    nz = ndi.gaussian_filter(rng.random(a.shape), 2.5)
    nz = (nz - nz.mean()) / max(1e-6, nz.std())
    fine = noise(a.shape, rng, 0.8)
    d = np.minimum.reduce([X - x0, x1 - X, Y - y0, y1 - Y])
    patch = d + 2.2 * nz > 2
    sets = BURNT if burnt else SOIL
    rpaint(a, patch, sets, (2.0 if burnt else 2.2) + 0.5 * nz + 1.2 * (fine - 0.5), fine)
    # the edge: no outline; the soil a step darker where the spade cut the turf, broken by grass
    # blades hanging over it from the lawn
    edge = patch & ~ndi.binary_erosion(patch, iterations=2)
    darker = edge & (rng.random(a.shape) < 0.6)
    a[darker] = np.maximum(a[darker] - 1, (a[darker] // 8) * 8)
    ey, ex = np.nonzero(edge & (rng.random(a.shape) < 0.07))
    for y_, x_ in zip(ey, ex):
        L = int(rng.integers(2, 5))
        for k in range(L):
            yy, xx = y_ - k if y_ > H / 2 else y_ + k - 1, x_ + (k // 2) * (1 if rng.random() < 0.5 else -1)
            if 0 <= yy < H and 0 <= xx < W:
                a[yy, xx] = C('grass', 3 if k else 2) if not burnt else C('ash', 3)
    rows = 3
    pitch = (y1 - y0 - 12) / rows
    crops = CROPS.get(kind, CROPS['dug'])
    for r in range(rows):
        ry0 = y0 + 8 + r * pitch
        ry1 = ry0 + pitch - 9
        rr = 4.0
        ridge = (np.abs(X - (x0 + x1) / 2) <= (x1 - x0) / 2 - 10 + 3 * nz) & (Y >= ry0) & (Y < ry1)
        ridge &= ~((X < x0 + 14) & (Y < ry0 + rr) & ((X - x0 - 14) ** 2 + (Y - ry0 - rr) ** 2 > rr * rr))
        fr = (Y - ry0) / max(1, ry1 - ry0)
        t = 3.4 - 1.2 * fr + 0.35 * nz - 0.9 * (Y >= ry1 - 3) - 0.6 * (X > x1 - 16) + 1.0 * (fine - 0.5)
        rpaint(a, ridge, [('soot', 'ash', 'ash'), ('stone_cool', 'ash', 'stone')] if burnt else SOIL, t - (0.4 if burnt else 0), fine)
        # the crest catching the light, the furrow under the ridge in shade
        crest = ridge & (Y < ry0 + 2) & (fine > 0.25)
        a[crest] = C('ash', 4) if burnt else C('earth_warm', 4)
        a[crest & (fine > 0.7)] = C('stone', 4) if burnt else C('sand_warm', 4)
        furrow = patch & ~ridge & (Y >= ry1) & (Y < ry1 + 4)
        a[furrow] = C('soot', 1) if burnt else np.where(fine[furrow] > 0.5, C('earth_cool', 1), C('path_cool', 1))
        for _ in range(int((x1 - x0) * pitch / 12)):            # clods, lit on their upper left
            cx_, cy_ = int(rng.uniform(x0 + 12, x1 - 12)), int(rng.uniform(ry0 + 2, ry1 - 3))
            if ridge[cy_, cx_]:
                a[cy_, cx_:cx_ + 2] = C('earth_warm' if not burnt else 'ash', 4 + (rng.random() < 0.3))
                a[cy_ + 1, cx_ + 1:cx_ + 3] = C('earth_cool' if not burnt else 'soot', 1)
        crop = crops[r % len(crops)]
        step = {'cabbage': 15, 'lettuce': 11, 'leek': 8, 'carrot': 8, 'beans': 14}[crop]
        cy = ry0 + (ry1 - ry0) * 0.5
        n = int((x1 - x0 - 32) // step)
        for i in range(n + 1):
            px = x0 + 16 + (x1 - x0 - 32) * i / max(1, n) + rng.uniform(-1.5, 1.5)
            if rng.random() < (0.35 if burnt else 0.1):
                continue                                       # a gap: one that failed (or the storm took)
            _plant(a, crop, px, cy + rng.uniform(-1, 1), rng, burnt=burnt, s=rng.uniform(0.72, 1.22), lean=rng.uniform(-1.6, 1.6))
        if burnt:
            for _ in range(4):                                 # green coming back
                sx = int(rng.uniform(x0 + 20, x1 - 20))
                a[int(cy + 2):int(cy + 5), sx] = C('grass', 4)
                a[int(cy + 2), sx - 1:sx + 2] = C('grass_warm', 4)
    if burnt:
        # ash drifted along the furrows and in hollows, pale where it lies thickest
        drift = patch & (ndi.gaussian_filter(rng.random(a.shape), 1.5) > 0.6) & (nz < 0.3)
        a[drift & (a // 8 != FI['soot'])] = C('ash', 4)
        a[drift & (fine > 0.8) & (a // 8 != FI['soot'])] = C('ash', 5)
        a[drift & (fine < 0.15) & (a // 8 != FI['soot'])] = C('snow_cool', 2)
        # where the fire passed quickly the soil is only browned: patches of it showing through
        brown = patch & (nz > 0.9) & (a // 8 != FI['soot'])
        rpaint(a, brown, SOIL[:2], 1.4 + 1.6 * (fine - 0.3), fine)
    V.finish(p, line=False)
    return p


def flower_border(seed=0):
    """A cottage border (72 x 40 texels, three cells by one): a strip of dark worked soil edged
    with a row of half-sunk stones, crowded with leafy clumps each crowned with its own flowers
    (foxglove spires, daisies, lavender, marigolds), lit on the upper left."""
    rng = np.random.default_rng(seed)
    p = canvas(80, 46, 40, 40)
    a = p.a
    Y, X = grid(a)
    x0, x1, y0, y1 = 4, 76, 26, 40
    soil = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    soil &= ~(((X < x0 + 3) | (X >= x1 - 3)) & ((Y < y0 + 2) | (Y >= y1 - 2)))
    V.paint(a, soil, ('earth_cool', 'earth', 'earth_warm'), 2.2 + 0.5 * np.sin(X * 0.9 + Y * 1.7) - 0.8 * (Y >= y1 - 2))
    for k, sx in enumerate(range(x0 + 1, x1 - 5, 7)):            # the edging stones along the front
        V.stone_chunk(a, sx, y1 - 5, 6, 5, 'stone', 3, rng)
    kinds = ['foxglove', 'daisy', 'lavender', 'marigold']
    for i, cx in enumerate(np.linspace(x0 + 8, x1 - 8, 6)):
        kind = kinds[(i + seed) % 4]
        cy = y0 + 4 + (i % 2) * 3
        leaf = ((X - cx) / 6.5) ** 2 + ((Y - cy) / 4.5) ** 2 <= 1
        V.paint(a, leaf, ('leaf_cool', 'leaf', 'leaf_warm'), 2.6 + 1.6 * sphere_light(X, Y, cx, cy, 6.5, 4.5))
        if kind == 'foxglove':
            for j in range(6):
                fy = cy - 5 - j * 2.2
                a[int(fy), int(cx) - 1:int(cx) + 2] = C('berry', 4 if j % 2 else 3)
                a[int(fy) + 1, int(cx)] = C('berry', 2)
            a[int(cy - 18):int(cy - 4), int(cx) + 1] = C('leaf_cool', 2)
        else:
            fam, tone, n = {'daisy': ('plaster', 5, 7), 'lavender': ('dusk', 4, 9), 'marigold': ('brass', 4, 7)}[kind]
            for _ in range(n):
                fx, fy = int(cx + rng.uniform(-5, 5)), int(cy + rng.uniform(-6, 0))
                a[fy:fy + 2, fx:fx + 2] = C(fam, tone)
                a[fy, fx] = C(fam, 5)
                if kind == 'daisy':
                    a[fy + 1, fx + 1] = C('brass', 4)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# yard things: churns, a water butt, a wheelbarrow, a scarecrow, feed sacks, a muck heap, a
# wallow and a pigsty
# ------------------------------------------------------------------------------------------------
METAL = [('slate_cool', 'stone', 'plaster'), ('stone_cool', 'stone_cool', 'stone_warm'), ('iron', 'stone', 'snow_cool')]
WOOD = [('timber_cool', 'timber', 'timber_warm'), ('earth_cool', 'earth', 'earth_warm'), ('timber_cool', 'earth_warm', 'sand_warm')]


def _cyl(a, cx, top, bot, half, sets, mix, rng, bands=(), lit_k=1.6):
    """An upright cylinder lit from the upper left: a highlight band left of centre, the core
    shadow right of it, a bounce at the east rim, darker at the foot."""
    Y, X = grid(a)
    f = np.clip((Y - top) / max(1, bot - top), 0, 1)
    hw = half(f)
    m = (np.abs(X - cx) <= hw) & (Y >= top) & (Y < bot)
    u = (X - cx) / np.maximum(hw, 1)
    t = 3.0 + lit_k * (np.exp(-((u + 0.4) / 0.35) ** 2) - 0.8 * np.clip(u - 0.1, 0, 1)) + 0.5 * (u > 0.85) - 0.9 * (f > 0.9)
    rpaint(a, m, sets, t, mix)
    for b in bands:
        bm = m & (np.abs(Y - b) < 1.0)
        a[bm] = np.maximum(a[bm] - 2, (a[bm] // 8) * 8)
        a[m & (Y == int(b) - 1) & (u < 0)] = C('plaster', 5) if sets is METAL else C('timber_warm', 4)
    return m


def water_butt(seed=0):
    """A water butt at a downpipe (34 x 46): a coopered barrel on a brick stand, staves lit on
    the left, two iron hoops, a lid of boards, a brass tap and a drip stain on the bricks."""
    rng = np.random.default_rng(seed)
    p = canvas(40, 56, 20, 52)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 0.9)
    stand = (X >= 7) & (X < 33) & (Y >= 42) & (Y < 52)
    brick = ((Y - 42) // 3)
    t = 2.6 + 0.8 * (np.mod(X + 4 * (brick % 2), 8) == 0) * -1 - 0.9 * (np.mod(Y - 42, 3) == 2) + 0.6 * (X < 9) - 0.8 * (X > 30)
    rpaint(a, stand, [('clay_cool', 'clay', 'crag_warm'), ('crag_cool', 'crag_warm', 'clay')], t, np.mod(brick * 0.37, 1))
    half = lambda f: 11.0 + 1.6 * np.sin(np.pi * f)
    m = _cyl(a, 20, 10, 43, half, WOOD, nz, rng, bands=(15, 37))
    staves = m & (np.mod(X - 20, 4) == 0)
    a[staves] = np.maximum(a[staves] - 1, (a[staves] // 8) * 8)
    for b in (15, 37):
        a[m & (np.abs(Y - b) < 1.0)] = C('iron', 2)
        a[m & (Y == b - 1) & (X < 17)] = C('iron', 4)
    lid = ((X - 20) / 12.5) ** 2 + ((Y - 10) / 3.0) ** 2 <= 1
    rpaint(a, lid, WOOD, 4.0 - 1.4 * (X > 24) + 0.5 * (np.mod(X, 5) == 0), 0.3)
    a[34:36, 30:34] = C('brass', 4)
    a[34, 30] = C('brass_warm', 5)
    a[42:46, 32] = C('water_cool', 2)
    a[stand & (X >= 30) & (X < 34) & (Y > 44)] = C('crag_cool', 1)
    V.finish(p)
    return p


def wheelbarrow(seed=0):
    """A wooden wheelbarrow (62 x 34): a plank tray lit inside its west wall, a spoked wheel at the
    front with an iron tyre, two handles and legs, a spill of earth in the tray."""
    rng = np.random.default_rng(seed)
    p = canvas(70, 44, 35, 40)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    for lx in (18, 40):                                          # legs and handles
        V.bar(a, lx, 26, lx - 2, 39, 1.2, 'timber', 2)
    V.bar(a, 6, 22, 30, 24, 1.3, 'timber_warm', 3)
    V.bar(a, 4, 20, 8, 21, 1.4, 'timber_warm', 4)
    tray = ((X >= 16) & (X < 52) & (Y >= 12) & (Y < 28)) & (Y - 12 <= (X - 16) * 1.2 + 4) & ((52 - X) * 1.1 + 4 >= Y - 12)
    rpaint(a, tray, WOOD, 2.8 + 1.0 * (Y < 15) - 0.7 * (np.mod(Y - 12, 5) == 4) + 0.6 * (nz - 0.5), nz)
    inner = tray & (Y < 18) & (X > 19) & (X < 49)
    rpaint(a, inner, [('earth_cool', 'earth', 'earth_warm'), ('path_cool', 'path', 'path_warm')], 1.6 + 2.0 * nz, nz)
    a[tray & (Y == 12)] = C('timber_warm', 5)
    # the wheel
    wx, wy, r = 54, 31, 8.0
    d = np.hypot(X - wx, Y - wy)
    tyre = (d <= r) & (d > r - 1.6)
    rpaint(a, tyre, [('soot', 'iron', 'stone')], 2.2 + 1.6 * ((X - wx) + (Y - wy) < -4), 0)
    rim = (d <= r - 1.6) & (d > r - 3.2)
    rpaint(a, rim, WOOD, 2.8 + 1.0 * ((X - wx) + (Y - wy) < 0), 0.2)
    for k in range(6):
        ang = k * math.pi / 3
        a[V.seg_mask(a.shape, wx, wy, wx + (r - 3) * math.cos(ang), wy + (r - 3) * math.sin(ang), 0.5)] = C('timber', 2)
    a[int(wy) - 1:int(wy) + 2, int(wx) - 1:int(wx) + 2] = C('iron', 3)
    V.finish(p)
    return p


def scarecrow(seed=0):
    """A scarecrow in a field (54 x 82): a pole and a cross-arm, a patched coat with straw at the
    cuffs and hem, a sack head with stitched eyes, a battered hat, a crow on one arm."""
    rng = np.random.default_rng(seed)
    p = canvas(62, 90, 31, 86)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.2)
    V.prism(a, 29, 30, 33, 86, 1, 'timber', 3, side=1)
    V.bar(a, 8, 34, 54, 34, 1.6, 'timber', 3)
    coat = ((X >= 18) & (X < 44) & (Y >= 32) & (Y < 66)) & ~((Y > 58) & (np.abs(X - 31) < 3))
    arms = ((Y >= 32) & (Y < 39) & (X >= 9) & (X < 53))
    cm = coat | arms
    fold = np.sin((X - 31) * 0.9 + (Y - 32) * 0.25) * (coat & (Y > 44))
    rpaint(a, cm, [('slate_cool', 'slate', 'stone_cool'), ('stone_cool', 'slate', 'slate_warm'), ('earth_cool', 'earth', 'earth_warm'),
                   ('timber_cool', 'timber', 'earth_warm')],
           2.6 + 1.3 * ((X < 28) & (Y < 50)) - 1.0 * (X > 38) + 0.8 * (nz - 0.5) + 0.7 * fold - 0.8 * (np.abs(X - 31) < 1) * coat,
           np.where((nz > 0.62) & coat, 0.9, np.where(arms & (X > 44), 0.6, 0.2)))
    a[coat & (np.abs(X - 31) < 1) & (np.mod(Y, 6) == 3) & (Y < 58)] = C('brass', 4)          # buttons
    for py, px in ((44, 22), (54, 36)):                         # patches with their stitches
        pm = (np.abs(X - px) < 4) & (np.abs(Y - py) < 3)
        rpaint(a, pm & cm, [('clay_cool', 'clay', 'crag_warm')], 2.8 + (X < px), 0)
        a[(np.abs(X - px) == 4) & (np.abs(Y - py) < 3) & cm & (np.mod(Y, 2) == 0)] = C('sand', 4)
    for sx, sy in ((9, 36), (53, 36), (24, 66), (38, 66), (31, 66)):     # straw at the cuffs and hem
        for k in range(5):
            ang = rng.uniform(0.5, 2.6) if sy > 50 else rng.uniform(-0.8, 0.8) + (math.pi if sx < 30 else 0)
            L = rng.uniform(3, 6)
            a[V.seg_mask(a.shape, sx, sy, sx + L * math.cos(ang), sy + L * math.sin(ang), 0.7)] = C('brass_warm' if k % 2 else 'sand_warm', 4)
    head = ((X - 31) / 7.0) ** 2 + ((Y - 24) / 7.5) ** 2 <= 1
    rpaint(a, head, [('earth_cool', 'sand', 'sand_warm'), ('stone_warm', 'sand_cool', 'sand')], 2.6 + 1.6 * sphere_light(X, Y, 31, 24, 7, 7.5), nz)
    a[head & (np.mod(X + Y, 2) == 0) & (nz > 0.55)] -= 1                 # the hessian's weave
    for k in range(7):
        sx = 25 + 2 * k
        a[V.seg_mask(a.shape, sx, 31, sx + rng.uniform(-2, 2), 35, 0.45)] = C(('brass_warm', 'sand_warm', 'brass')[k % 3], 3 + k % 2)
    for ex in (28, 34):
        a[23, ex - 1:ex + 2] = C('soot', 1)
        a[22:25, ex] = C('soot', 1)
    a[28, 28:35:2] = C('soot', 2)
    hat = ((X - 31) / 12.0) ** 2 + ((Y - 17) / 2.2) ** 2 <= 1
    crown = (X >= 25) & (X < 38) & (Y >= 8) & (Y < 17) & (np.abs(X - 31.5) <= 6.5 - 0.15 * (17 - Y))
    rpaint(a, hat | crown, [('soot', 'earth_cool', 'earth'), ('earth_cool', 'earth', 'earth_warm')], 2.0 + 1.4 * (X < 30) - 0.6 * (Y > 15) + 0.5 * nz, nz)
    a[(Y == 15) & crown] = C('berry_cool', 2)                    # the hat band
    # a crow on the east arm
    crow = ((X - 49) / 3.2) ** 2 + ((Y - 30) / 2.6) ** 2 <= 1
    a[crow] = C('soot', 1)
    a[crow & (Y < 29)] = C('slate_cool', 2)
    a[29, 51:53] = C('brass', 3)
    V.finish(p)
    return p


def feed_sacks(seed=0):
    """Feed sacks stacked on a pallet (52 x 40): hessian sacks, each a soft lumpy form lit on its
    upper left with a stencilled mark, their tied necks, a little spilled grain."""
    rng = np.random.default_rng(seed)
    p = canvas(58, 46, 29, 42)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 0.8)
    pal = (X >= 6) & (X < 52) & (Y >= 37) & (Y < 42)
    rpaint(a, pal, WOOD, 2.6 + 1.0 * (Y == 37) - 0.8 * (np.mod(X, 9) == 0), 0.4)
    for k, (cx, cy, rx, ry) in enumerate(((17, 30, 11, 8), (38, 30, 11, 8), (27, 18, 11, 8))):
        m = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1 + 0.12 * np.sin(np.arctan2(Y - cy, X - cx) * 5 + k)
        rpaint(a, m, [('earth_cool', 'sand_cool', 'sand'), ('stone_warm', 'sand', 'sand_warm'), ('earth_cool', 'earth_warm', 'sand_warm')],
               2.6 + 1.6 * sphere_light(X, Y, cx, cy, rx, ry) + 0.7 * (nz - 0.5) - 0.6 * (np.mod(X + Y, 3) == 0), nz)
        band = m & (np.abs(Y - cy - 1) < 1.0) & (np.abs(X - cx) < 6) & (np.mod(X, 3) != 0)
        a[band] = C('berry_cool' if k % 2 else 'sky_cool', 2)                               # the miller's band
        a[int(cy - ry), int(cx + rx * 0.5)] = C('sand', 4)
        a[int(cy - ry) + 1, int(cx + rx * 0.5) - 1:int(cx + rx * 0.5) + 2] = C('earth_cool', 1)   # the tied neck
    for _ in range(14):
        gx, gy = int(rng.uniform(4, 54)), int(rng.uniform(41, 45))
        a[gy, gx] = C('brass', 4 if rng.random() < 0.5 else 3)
    V.finish(p)
    return p


def muck_heap(seed=0):
    """A muck heap by the yard wall (60 x 30): straw and dung forked up into a steaming mound,
    dark and wet at its foot, bright straw on top, a fork stuck in it."""
    rng = np.random.default_rng(seed)
    p = canvas(70, 52, 35, 46)
    a = p.a
    Y, X = grid(a)
    cx, cy, rx, ry = 35, 34, 29, 13
    rough = ndi.gaussian_filter(rng.random(a.shape), 1.3)
    m = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1 + 1.2 * (rough - 0.5)) & (Y < 46)
    lit = sphere_light(X, Y, cx, cy, rx, ry)
    nz = noise(a.shape, rng, 0.8)
    rpaint(a, m, [('soot', 'earth_cool', 'earth'), ('earth_cool', 'earth', 'earth_warm'), ('crag_cool', 'earth', 'clay')],
           1.4 + 1.6 * lit + 1.2 * (nz - 0.5), nz)
    for _ in range(45):                                          # straw through it, brightest on top
        x0, y0 = rng.uniform(cx - rx, cx + rx), rng.uniform(cy - ry, 45)
        ang = rng.uniform(-0.8, 0.8) + (math.pi if rng.random() < 0.5 else 0)
        sm = V.seg_mask(a.shape, x0, y0, x0 + 4 * math.cos(ang), y0 + 4 * math.sin(ang), 0.7) & m
        rpaint(a, sm, STRAW, 2.0 + 2.4 * lit, rng.random())
    a[m & (Y >= 43)] = C('soot', 1)
    wet = m & (Y >= 40) & (rng.random(a.shape) < 0.08)
    a[wet] = C('water_cool', 2)
    # the fork, its tines in the heap
    V.bar(a, 46, 6, 50, 26, 1.0, 'timber_warm', 3)
    for dx in (-1.5, 0, 1.5):
        a[V.seg_mask(a.shape, 50 + dx, 25, 50.5 + dx, 30, 0.45)] = C('iron', 3)
    for k in range(3):                                           # steam
        sx = 26 + 7 * k
        a[V.seg_mask(a.shape, sx, 18 - k, sx + 2, 12 - k, 0.5)] = C('snow_cool', 2)
    V.finish(p)
    return p


def wallow(seed=0):
    """A pig's wallow (72 x 30): a hollow of wet mud, glossy where it pools, churned at its rim
    into ridges lit on their upper left, trotter prints in the soft edge."""
    rng = np.random.default_rng(seed)
    p = canvas(80, 36, 40, 32)
    a = p.a
    Y, X = grid(a)
    rough = ndi.gaussian_filter(rng.random(a.shape), 1.6)
    m = ((X - 40) / 34) ** 2 + ((Y - 18) / 12) ** 2 <= 1 + 0.6 * (rough - 0.5)
    d = ((X - 40) / 34) ** 2 + ((Y - 18) / 12) ** 2
    nz = noise(a.shape, rng, 0.9)
    ridge = np.sin(np.arctan2((Y - 18) * 2.8, X - 40) * 9 + 6 * rough)
    rpaint(a, m, [('soot', 'earth_cool', 'earth'), ('earth_cool', 'earth', 'earth_warm'), ('path_cool', 'path', 'path_warm'),
                  ('earth_cool', 'path_cool', 'path')],
           3.0 - 1.8 * (1 - d) + 0.9 * (nz - 0.5) + 0.8 * ((d > 0.7) & (Y < 16)) + 1.3 * ridge * (d > 0.45) - 0.7 * (Y > 22) * (d > 0.5),
           np.clip(0.75 * d + 0.25 * nz, 0, 0.99))
    pool = m & (d < 0.35)
    rpaint(a, pool, [('soot', 'earth_cool', 'earth_cool'), ('earth_cool', 'earth', 'path_cool')],
           1.0 + 1.4 * (nz > 0.6) + 0.8 * (Y > 21), nz)
    rim = m & ~ndi.binary_erosion(m, iterations=2) & (Y < 18) & (X < 46)
    a[rim] = C('path_warm', 4)
    a[m & ~ndi.binary_erosion(m, iterations=1) & (Y < 14) & (X < 34)] = C('sand', 4)
    sheen = pool & (np.abs(Y - 13 - 0.08 * (X - 40)) < 0.7) & (X > 30) & (X < 46)
    a[sheen] = C('sky_cool', 3)                                  # the sky in it
    a[pool & (np.abs(Y - 17) < 0.6) & (X > 44) & (X < 50)] = C('stone_cool', 3)
    for _ in range(10):                                          # straw trodden into the edge
        x0, y0 = rng.uniform(8, 72), rng.uniform(6, 30)
        if m[int(y0), int(x0)] and d[int(y0), int(x0)] > 0.55:
            a[V.seg_mask(a.shape, x0, y0, x0 + rng.uniform(-3, 3), y0 + rng.uniform(-1, 1), 0.45) & m] = C('brass', 3)
    for _ in range(9):                                           # trotter prints
        tx, ty = rng.uniform(10, 70), rng.uniform(8, 28)
        if m[int(ty), int(tx)] and d[int(ty), int(tx)] > 0.6:
            a[int(ty), int(tx):int(tx) + 2] = C('soot', 1)
            a[int(ty) + 1, int(tx)] = C('earth_warm', 4)
    V.finish(p, line=False)
    return p


# ------------------------------------------------------------------------------------------------
# sheds at the size guide's scale (round 4: "shed" 32 to 56 by 40 to 64 world px)
# ------------------------------------------------------------------------------------------------
BOARDS = [('timber_cool', 'timber', 'timber_warm'), ('earth_cool', 'earth', 'earth_warm'), ('timber_cool', 'earth_warm', 'sand_warm'),
          ('slate_cool', 'timber_cool', 'stone_warm'), ('crag_cool', 'clay', 'sand_warm'), ('stone_cool', 'stone_warm', 'ashlar_warm')]


def _boards(a, m, x0, x1, rng, w=6, base=2.8, east=True):
    """Vertical boards: each its own hue and tone, lit on its west edge, a dark gap, the grain in
    streaks, a nail head top and bottom, the east end of the wall a step into shade."""
    Y, X = grid(a)
    k = ((X - x0) // w).astype(int)
    u = np.mod(X - x0, w)
    tb = rng.uniform(-0.5, 0.5, 64)[np.clip(k, 0, 63)]
    t = base + tb + 1.0 * (u == 0) - 1.6 * (u == w - 1) - 0.7 * (_hash2(X, Y // 5) < 0.18) - (0.8 * (X > x0 + 0.75 * (x1 - x0)) if east else 0)
    rpaint(a, m, BOARDS, t, np.mod(k * 0.37, 1))
    lich = m & (noise(a.shape, rng, 1.2) > 0.82) & (u > 0) & (u < w - 1)
    rpaint(a, lich, [('brass', 'sand_warm', 'leaf_warm'), ('leaf_cool', 'leaf', 'brass')], 2.6 + rng.random(a.shape), rng.random(a.shape))


def _hash2(x, y):
    v = np.sin(np.asarray(x, float) * 12.9898 + np.asarray(y, float) * 78.233) * 43758.5453
    return v - np.floor(v)


def _shingles(a, m, top, rng, sets=None, row=4, w=6, lit_left=True, x_mid=None):
    Y, X = grid(a)
    r = ((Y - top) // row).astype(int)
    k = ((X + 3 * (r % 2)) // w).astype(int)
    t = 3.4 - 0.12 * (Y - top) / row + rng.uniform(-0.6, 0.6, (200, 200))[np.clip(r, 0, 199), np.clip(k, 0, 199)] - 1.6 * (np.mod(Y - top, row) == row - 1) \
        - 0.8 * (np.mod(X + 3 * (r % 2), w) == 0) + 0.5 * (np.mod(Y - top, row) == 0)
    t = t - 0.7 * ((_hash2(X // 3, 0) < 0.12) & (np.mod(Y - top, row) < row - 1))      # rain streaks down the courses
    if x_mid is not None:
        t = t - (1.2 * (X > x_mid) if lit_left else 0)
    rpaint(a, m, sets or [('timber_cool', 'timber', 'timber_warm'), ('slate_cool', 'timber_cool', 'stone_warm'), ('earth_cool', 'earth', 'earth_warm')],
           t, np.mod(k * 0.29 + r * 0.17, 1))
    moss = m & (noise(a.shape, rng, 1.6) > 0.8)
    rpaint(a, moss, [('leaf_cool', 'leaf', 'brass'), ('grass_cool', 'leaf_cool', 'leaf_warm')], 2.2 + 1.2 * (np.mod(Y - top, row) == 0), rng.random(a.shape))


def coop(seed=0):
    """A hen house (100 x 120, shed scale): a boarded house on short legs, its gable end to us
    under a shingled roof, a wire-meshed window, a nest box on its side with a lid, the pop hole and
    its slatted ramp down to the run, a little straw at the door."""
    rng = np.random.default_rng(seed)
    p = canvas(104, 126, 50, 122)
    a = p.a
    Y, X = grid(a)
    for lx in (16, 80):                                                  # the legs
        V.prism(a, lx, 106, lx + 5, 122, 1, 'timber', 2, side=1)
    wall = (X >= 12) & (X < 88) & (Y >= 54) & (Y < 108)
    gable = (Y >= 14) & (Y < 54) & (np.abs(X - 50) <= (Y - 14) * 0.95)
    _boards(a, wall | gable, 12, 88, rng)
    a[(Y >= 106) & (Y < 108) & (X >= 12) & (X < 88)] = C('soot', 1)      # the sill's shade
    # the roof's two slopes along the gable, overhanging, shingled; the left lit
    roofm = (Y >= 6) & (Y < 62) & (np.abs(np.abs(X - 50) - (Y - 14) * 0.95) <= 6) & (Y >= 6 + 0 * X)
    _shingles(a, roofm, 6, rng, x_mid=50)
    a[roofm & (np.abs(np.abs(X - 50) - (Y - 14) * 0.95 - 6) <= 0.6)] = C('timber_warm', 4)
    a[(Y >= 4) & (Y < 9) & (np.abs(X - 50) < 3)] = C('timber', 2)        # the ridge's finial
    # the window with its wire
    win = (X >= 24) & (X < 40) & (Y >= 64) & (Y < 78)
    a[win] = C('soot', 1)
    a[win & ((np.mod(X - Y, 4) == 0) | (np.mod(X + Y, 4) == 0))] = C('stone_cool', 2)
    V.prism(a, 22, 62, 42, 64, 1, 'timber', 4, side=1)
    # the nest box on the east side, its lid lifting
    V.prism(a, 88, 74, 100, 98, 4, 'timber', 3, side=2)
    V.bar(a, 87, 72, 101, 70, 1.2, 'timber_warm', 4)
    # the pop hole and the ramp
    hole = (X >= 44) & (X < 58) & (Y >= 88) & (Y < 106) & ((X - 51) ** 2 / 49 + (Y - 92) ** 2 / 16 <= 1) | ((X >= 44) & (X < 58) & (Y >= 92) & (Y < 106))
    a[hole] = C('soot', 0)
    ramp = V.seg_mask(a.shape, 51, 106, 64, 122, 3.2)
    rpaint(a, ramp, BOARDS, 3.2 - 1.5 * (np.mod(Y, 3) == 0), 0.2)
    for _ in range(12):
        sx, sy = rng.uniform(40, 80), rng.uniform(118, 123)
        a[V.seg_mask(a.shape, sx, sy, sx + rng.uniform(-3, 3), sy - 1, 0.45)] = C('brass' if rng.random() < 0.5 else 'sand_warm', 4)
    V.finish(p)
    return p


def shelter(seed=0):
    """A field shelter (124 x 118, shed scale): open to the south under a pent roof of boards, its
    back and sides boarded, the inside in deep shade with a hay rack on the back wall and straw on
    the floor, the corner posts lit on their west faces."""
    rng = np.random.default_rng(seed)
    p = canvas(128, 122, 64, 118)
    a = p.a
    Y, X = grid(a)
    inner = (X >= 10) & (X < 118) & (Y >= 46) & (Y < 112)
    _boards(a, inner, 10, 118, rng, base=1.4, east=False)                  # the back wall in shade
    rack = (X >= 30) & (X < 98) & (Y >= 56) & (Y < 72)
    a[rack & (np.mod(X, 5) == 0)] = C('timber', 2)
    a[rack & ((Y == 56) | (Y == 71))] = C('timber', 3)
    hay = (X >= 32) & (X < 96) & (Y >= 58) & (Y < 70) & (rng.random(a.shape) < 0.55)
    rpaint(a, hay, STRAW, 2.0 + 1.2 * (Y < 63), rng.random(a.shape))
    floor = (X >= 10) & (X < 118) & (Y >= 98) & (Y < 114)
    rpaint(a, floor, STRAW, 1.6 + 1.6 * (Y > 106) + 0.8 * (noise(a.shape, rng, 0.8) - 0.5), rng.random(a.shape))
    side = (X >= 6) & (X < 14) & (Y >= 40) & (Y < 116)
    _boards(a, side, 6, 14, rng, w=4, base=3.0, east=False)
    for px in (6, 114):                                                  # the corner posts
        V.prism(a, px, 40, px + 7, 118, 1, 'timber', 3, side=1)
    roof = (X >= 2) & (X < 126) & (Y >= 4) & (Y < 44)
    _shingles(a, roof, 4, rng, row=5, w=8)
    a[(Y >= 42) & (Y < 46) & (X >= 2) & (X < 126)] = C('timber', 2)       # the fascia
    a[(Y == 42) & (X >= 2) & (X < 126)] = C('timber_warm', 4)
    a[(Y >= 46) & (Y < 50) & (X >= 14) & (X < 114)] = C('soot', 0)       # the eave's shade inside
    V.finish(p)
    return p


def sty(seed=0):
    """A pigsty (112 x 118, shed scale): a low house of rubble under a slate roof, its ridge capped,
    a dark doorway the pigs come out of, a stone trough set in its front wall with swill in it, moss
    in the lower joints, the roof's eave throwing a shadow on the wall."""
    rng = np.random.default_rng(seed)
    p = canvas(116, 124, 58, 120)
    a = p.a
    Y, X = grid(a)
    x0, x1, wt, yb = 6, 110, 74, 120
    wall = (X >= x0) & (X < x1) & (Y >= wt) & (Y < yb)
    V.rubble(a, x0, wt, x1, yb, rng, course=(2.0, 3.0), length=(3.0, 6.5), hd=True)
    a[wall & (X > x1 - 10)] = np.maximum(a[wall & (X > x1 - 10)] - 1, (a[wall & (X > x1 - 10)] // 8) * 8)
    a[wall & (noise(a.shape, rng, 1.5) > 0.75) & (Y > yb - 16)] = C('leaf_cool', 2)
    roof = (X >= x0 - 4) & (X < x1 + 4) & (Y >= 6) & (Y < wt + 2)
    _shingles(a, roof, 8, rng, sets=[('slate_cool', 'slate', 'slate_warm'), ('stone_cool', 'slate', 'slate_warm'), ('dusk_cool', 'slate', 'stone'),
                                     ('crag_cool', 'stone_cool', 'stone_warm'), ('dusk_cool', 'dusk', 'ashlar')],
              row=5, w=7)
    a[roof & (Y < 9)] = C('stone', 3)                                     # the ridge tiles
    a[roof & (Y == 6)] = C('stone_warm', 4)
    lich = roof & (noise(a.shape, rng, 1.0) > 0.86)
    rpaint(a, lich, [('brass', 'sand_warm', 'leaf_warm'), ('leaf_cool', 'leaf', 'brass')], 2.5 + (X < 58), rng.random(a.shape))
    a[(Y >= wt + 2) & (Y < wt + 5) & wall] = C('soot', 1)
    a[yb - 26:yb, 18:38] = C('soot', 0)                                  # the doorway, its jambs
    a[yb - 24:yb, 20:36] = C('soot', 1)
    a[yb - 26:yb, 16:18] = C('timber', 3)
    a[yb - 26:yb, 38:40] = C('timber_cool', 2)
    V.prism(a, 14, yb - 30, 42, yb - 26, 2, 'stone', 4, side=2)          # the lintel
    V.prism(a, 54, yb - 14, 100, yb, 3, 'stone', 3, side=3)              # the trough in the wall
    sw = (X >= 57) & (X < 97) & (Y >= yb - 13) & (Y < yb - 10)
    rpaint(a, sw, [('earth_cool', 'earth', 'brass')], 2.0 + 1.2 * (np.mod(X, 4) == 0), 0)
    for _ in range(12):
        wx = rng.uniform(x0 + 2, x1 - 2)
        if 14 < wx < 42 or 52 < wx < 102:
            continue
        for k in range(3):
            a[V.seg_mask(a.shape, wx, yb, wx + rng.uniform(-2, 2), yb - rng.uniform(3, 7), 0.45)] = C(('grass', 'leaf', 'grass_warm')[k], 2 + k)
    V.finish(p)
    return p


def churns(seed=0):
    """A milk churn (36 x 44, barrel scale): tinned steel, a lit band down its left, the core
    shadow on its right, a rolled shoulder, a lid with its knob, a ring handle, mud at its foot."""
    rng = np.random.default_rng(seed)
    p = canvas(40, 50, 20, 46)
    a = p.a
    Y, X = grid(a)
    nz = noise(a.shape, rng, 1.0)
    cx, top = 19, 6
    half = lambda f: np.where(f < 0.12, 5.0 + 30 * f, np.where(f < 0.3, 8.6 - 6 * (f - 0.12), 9.6))
    _cyl(a, cx, top + 4, 46, half, METAL, nz, rng, bands=(top + 14, 46 - 6))
    lid = ((X - cx) / 6.0) ** 2 + ((Y - (top + 3)) / 2.4) ** 2 <= 1
    rpaint(a, lid, METAL, 4.2 - 1.2 * (X > cx + 1), 0.4)
    a[top:top + 2, cx - 1:cx + 2] = C('stone', 4)
    a[top, cx - 1] = C('plaster', 5)
    for hx_ in (cx - 11, cx + 11):
        ring = np.abs(np.hypot(X - hx_, Y - (top + 15)) - 2.2) < 0.6
        a[ring & (np.abs(X - cx) > 9)] = C('iron', 2)
    a[(Y >= top + 26) & (Y < top + 30) & (np.abs(X - cx) <= 6)] = C('berry_cool', 2)    # the dairy's painted band
    a[(Y == top + 26) & (np.abs(X - cx) <= 6) & (X < cx)] = C('berry', 3)
    mud = (((X - cx) / 14) ** 2 + ((Y - 46) / 2.6) ** 2 <= 1) & (Y >= 44) & (a < 0)
    rpaint(a, mud, [('earth_cool', 'earth', 'earth_warm')], 1.6 + nz, 0)
    V.finish(p)
    return p


# ------------------------------------------------------------------------------------------------
# pieces
# ------------------------------------------------------------------------------------------------
def _fp(cols, rows):
    """Footprint cells (offsets from the foot cell) for a piece cols wide, rows deep."""
    xs = range(-(cols // 2), cols - cols // 2)
    return [[c, -r] for r in range(rows, 0, -1) for c in xs]


def trim(pics):
    """The pictures cropped to what any of them draws (and the foot), the foot moved with them:
    a piece's size_px is its art, as the size guide measures it."""
    m = np.zeros(pics[0].a.shape, bool)
    for q in pics:
        m |= q.a >= 0
    ys, xs = np.nonzero(m)
    ax, ay = pics[0].ax, pics[0].ay
    x0, x1 = min(xs.min(), ax), max(xs.max() + 1, ax + 1)
    y0, y1 = min(ys.min(), ay - 1), max(ys.max() + 1, ay)
    out = []
    for q in pics:
        t = V.Pic(int(x1 - x0), int(y1 - y0), q.ax - x0, q.ay - y0)
        t.a[:] = q.a[y0:y1, x0:x1]
        out.append(t)
    return out


def strip(frames):
    w, h = frames[0].W, frames[0].H
    s = np.full((h, w * len(frames)), -1, np.int32)
    for k, f in enumerate(frames):
        s[:, k * w:(k + 1) * w] = f.a
    return s


def _base(pid, name, png_still, foot, size, purpose, role, *, cells, fp, collision, requires=(), forbids=(),
          enclosure=None, anim=None, shadow=(10, 3), blocks=True, biomes=('village', 'valley'), size_class=None,
          eastward=None, note=''):
    piece = {
        'schema': 'napattack.piece/1', 'id': pid, 'name': name, 'kind': 'prop', 'biomes': list(biomes), 'version': 1,
        'variants': [{'id': os.path.splitext(os.path.basename(png_still))[0], 'weight': 1.0, 'png': RES + os.path.basename(png_still),
                      'foot': list(foot)}],
        'approval': {'state': 'candidate', 'by': None, 'at': None,
                     'standard': "art-style.md (Eastward's level of detail), placement-logic.md", 'note': note},
        'geometry': {'size_px': list(size), 'size_cells': [max(1, int(math.floor(v / 24 + 0.5))) for v in size], 'z_sort': 'foot', 'height_px': size[1] - (size[1] - foot[1]),
                     'collision': collision, 'foot': list(foot), 'footprint': fp},
        'placement': {'snap': 'cell', 'purpose': purpose, 'role': role,
                      **({'requires': list(requires)} if requires else {}), **({'forbids': list(forbids)} if forbids else {}),
                      **({'enclosure': enclosure} if enclosure else {})},
        'rendering': {'cast_shadow': {'shape': 'ellipse', 'size': list(shadow), 'dir': [1, 1]} if shadow else {'shape': 'none'},
                      'contact_ao': True, **({'animations': [anim]} if anim else {})},
        'function': {}, 'story': {'owner': None},
        'gameplay': {'blocks_move': blocks, 'blocks_shots': False},
        'audit': {'size_class': size_class, 'eastward_ref': eastward,
                  'painter': {'module': 'scripts.art.kit.farm', 'fn': pid, 'args': {}},
                  'seeded_from': 'scripts/art/kit/farm.py', 'todo': []},
    }
    return piece


OFF_ROUTE = {'rel': 'on', 'what': 'route'}
OFF_WATER = {'rel': 'on', 'what': 'water'}


def _rel(rel, what, cells=None, note=None):
    r = {'rel': rel, 'what': what}
    if cells is not None:
        r['cells'] = cells
    if note:
        r['note'] = note
    return r


def animals():
    """(piece id, frames, fps, piece kwargs) for every animal."""
    out = []
    for kind, (_b, _w, _t, face, _s) in HENS.items():
        frames = [hen(kind, pose, seed=11) for pose in (HEN_FRAMES[k:] + HEN_FRAMES[:k] if False else HEN_FRAMES)]
        # each hen keeps her own rhythm: the loop starts at a different beat
        shift = {'white': 0, 'brown': 3, 'speckled': 5}[kind]
        frames = frames[shift:] + frames[:shift]
        out.append(('farm_hen_%s' % kind, frames, 4.0, dict(
            name='Hen, %s' % kind, purpose='live', role='stock', cells=(1, 1), fp=[[0, -1]],
            collision={'shape': 'none'}, blocks=False, shadow=(6, 2),
            requires=[_rel('within', 'coop', 4, 'hens live in a run with their coop (placement-logic: keep animals in)'),
                      _rel('within', 'boundary', 3, 'inside the run\'s fence')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['chickens'], 'as': 'contents'},
            eastward='17: the farm\'s animals, each a readable mass with its own pose', size_class='small_animal',
            note='A hen pecking in her run; 8 idle frames at 4 fps.')))
    for pose, face, seed in (('stand', -1, 3), ('graze', 1, 5), ('lie', -1, 4)):
        frames = [sheep(pose, f, face, seed) for f in SHEEP_FRAMES[pose]]
        # each ewe keeps her own rhythm, as the hens do: the loop starts at a different beat
        shift = {'stand': 0, 'graze': 3, 'lie': 5}[pose]
        frames = frames[shift:] + frames[:shift]
        out.append(('farm_sheep' + ('' if pose == 'stand' else '_' + pose), frames, 3.0, dict(
            name='Sheep, ' + {'stand': 'standing', 'graze': 'grazing', 'lie': 'lying'}[pose], purpose='live', role='stock',
            cells=(3, 1), fp=_fp(2, 1), collision={'shape': 'rect', 'rect': [-9.0, -3.0, 18, 3]}, shadow=(18, 4),
            requires=[_rel('within', 'trough', 9, 'a fold holds its trough (placement-logic: keep animals in)'),
                      _rel('within', 'boundary', 5, 'inside the fold\'s hurdles')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['sheep'], 'as': 'contents'},
            eastward='17: cows 0.9 A and pigs 0.55 A, chunky with a dark outline', size_class='sheep',
            note='A ewe in her fold; 8 idle frames at 3 fps.')))
    # the paddock, the sty and the goat pen: (piece, kind, facing, seed, loop start, collision in
    # world px from the foot, footprint cols, what holds it, what it needs within, how far)
    stock = (
        ('farm_cow', 'cow', 1, 8, 0, [-11.0, -3.0, 22, 3], 3, 'cattle', 'trough', 14, 'A cow in her paddock, her tail swishing'),
        ('farm_calf', 'calf', -1, 8, 3, [-6.5, -2.0, 13, 2], 2, 'cattle', 'trough', 14, 'A calf at grass near its mother, an ear flicking'),
        ('farm_horse', 'horse', -1, 1, 6, [-9.0, -3.0, 18, 3], 3, 'horses', 'trough', 14, 'A bay horse in its paddock, dipping its head to graze'),
        ('farm_pig', 'pig', 1, 2, 5, [-7.5, -3.0, 15, 3], 2, 'pigs', 'wallow', 6, 'A pig in the sty\'s run, its snout working'),
        ('farm_goat', 'goat', -1, 9, 1, [-6.0, -2.0, 12, 2], 2, 'goats', 'shelter', 8, 'A goat in its pen, chewing'),
        ('farm_goat_b', 'goat_b', 1, 3, 6, [-6.0, -2.0, 12, 2], 2, 'goats', 'shelter', 8, 'A brown goat grazing'),
    )
    for pid, kind, face, seed, shift, rect, cols, holds, need, far, note in stock:
        frames = beast_frames(kind, face, seed, shift)
        big = kind in ('cow', 'horse')
        out.append((pid, frames, 3.0, dict(
            name={'farm_goat_b': 'Goat, brown, grazing'}.get(pid, kind.capitalize()), purpose='live', role='stock',
            cells=(6 if big else 4, 4 if big else 3), fp=_fp(cols, 1), collision={'shape': 'rect', 'rect': rect},
            shadow=(int(rect[2] * 3 * 0.9), 5 if big else 4),
            requires=[_rel('within', need, far, 'stock keep to what their pen gives them (placement-logic: keep animals in)'),
                      _rel('within', 'boundary', 8 if big else 5, 'inside its fence')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': [holds], 'as': 'contents'},
            eastward='17: cows 0.9 A and pigs 0.55 A, chunky with a dark outline',
            size_class={'cow': 'cow', 'horse': 'horse'}.get(kind, 'sheep'), note=note + '; 8 idle frames at 3 fps.')))
    return out


def statics():
    """(piece id, picture, piece kwargs) for the coop, the shelter and the hay."""
    return [
        ('farm_coop', coop(seed=21), dict(
            name='Hen house', purpose='live', role='coop', cells=(4, 5), fp=_fp(4, 2),
            collision={'shape': 'rect', 'rect': [-12.5, -6.0, 25, 6]}, shadow=(30, 5),
            requires=[_rel('within', 'boundary', 2, 'against the run\'s fence, in its back corner'),
                      _rel('near', 'stock', 4, 'its hens about it')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['chickens'], 'as': 'needs'},
            size_class='shed',
            eastward='17: the barn\'s boarded walls, knots and nail heads', note='The hens\' house in their run.')),
        ('farm_shelter', shelter(seed=31), dict(
            name='Field shelter', purpose='live', role='shelter', cells=(5, 5), fp=_fp(5, 2),
            collision={'shape': 'rect', 'rect': [-20.0, -14.0, 40, 10]}, shadow=(42, 5),
            requires=[_rel('within', 'boundary', 2, 'its back to the fold\'s hurdles'), _rel('near', 'stock', 8, 'the flock it shelters')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['sheep', 'horses', 'cattle', 'goats'], 'as': 'needs'},
            size_class='shed',
            eastward='17: the barn\'s timber, its eave\'s shade', note='Shelter for the flock, its open side south.')),
        ('garden_flower_border', flower_border(seed=61), dict(
            name='Flower border', purpose='care', role='planter', cells=(3, 1), fp=_fp(3, 1),
            collision={'shape': 'none'}, blocks=False, shadow=None,
            requires=[_rel('within', 'boundary', 3, 'inside a front garden\'s fence or along a house\'s wall'),
                      _rel('near', 'house', 6, 'a home\'s garden')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['flowers'], 'as': 'contents'},
            size_class='flowers',
            eastward='12 and 13: flower clumps, heads a touch big', note='A cottage border in a front garden.')),
        ('farm_sty', sty(seed=8), dict(
            name='Pigsty', purpose='live', role='sty', cells=(5, 3), fp=_fp(4, 2),
            collision={'shape': 'rect', 'rect': [-17.5, -11.0, 35, 11]}, shadow=(36, 5),
            requires=[_rel('near', 'stock', 6, 'its pigs in the run before it')],
            forbids=[OFF_ROUTE, OFF_WATER], enclosure={'holds': ['pigs'], 'as': 'needs', 'serves': ['sty', 'trough']},
            size_class='shed',
            eastward='17: the barn\'s stone and slate, its dark door', note='The pigs\' house, its run fenced before it; a trough in its wall.')),
        ('farm_wallow', wallow(seed=7), dict(
            name='Wallow', purpose='live', role='wallow', cells=(3, 1), fp=_fp(3, 1),
            collision={'shape': 'none'}, blocks=False, shadow=None,
            requires=[_rel('within', 'boundary', 5, 'in the pigs\' run')], forbids=[OFF_ROUTE, OFF_WATER],
            enclosure={'holds': ['pigs'], 'as': 'needs'}, size_class='pile',
            eastward='17: mud and puddles, dark and glossy', note='A pig\'s mud wallow in the sty\'s run.')),
        ('farm_churns', churns(seed=1), dict(
            name='Milk churn', purpose='store', role='churns', cells=(1, 2), fp=_fp(1, 1),
            collision={'shape': 'rect', 'rect': [-4.0, -2.0, 8, 2]}, shadow=(10, 3),
            requires=[_rel('near', 'gate', 3, 'set out by the paddock gate or the yard\'s for the cart')], forbids=[OFF_ROUTE, OFF_WATER],
            size_class='barrel', eastward='17: tins and buckets by the barn', note='Churns waiting for the milk cart.')),
        ('farm_water_butt', water_butt(seed=2), dict(
            name='Water butt', purpose='water', role='water_butt', cells=(2, 1), fp=_fp(1, 1),
            collision={'shape': 'rect', 'rect': [-4.0, -4.0, 8, 4]}, shadow=(12, 3),
            requires=[_rel('adjacent', 'house', 1, 'at a building\'s downpipe')], forbids=[OFF_ROUTE, OFF_WATER],
            size_class='barrel', eastward='17 and 12: barrels by the walls', note='Rain from the roof, by a wall.')),
        ('farm_wheelbarrow', wheelbarrow(seed=3), dict(
            name='Wheelbarrow', purpose='work', role='barrow', cells=(3, 1), fp=_fp(2, 1),
            collision={'shape': 'rect', 'rect': [-8.0, -3.0, 18, 3]}, shadow=(22, 3),
            requires=[_rel('near', 'muck_heap', 4, 'left by the muck heap or the beds it serves')], forbids=[OFF_ROUTE, OFF_WATER],
            size_class='handcart', eastward='17: the farm\'s tools left where they are used',
            note='A barrow by the muck heap.')),
        ('farm_scarecrow', scarecrow(seed=4), dict(
            name='Scarecrow', purpose='grow', role='scarecrow', cells=(3, 1), fp=_fp(1, 1),
            collision={'shape': 'rect', 'rect': [-1.5, -1.5, 3, 1.5]}, shadow=(8, 3),
            requires=[_rel('within', 'garden', 3, 'in the crops it keeps the birds off')], forbids=[OFF_ROUTE, OFF_WATER],
            size_class='scarecrow', eastward='17: a figure in the field, its coat patched',
            note='A scarecrow in the beds.')),
        ('farm_feed_sacks', feed_sacks(seed=5), dict(
            name='Feed sacks', purpose='store', role='sacks', cells=(2, 1), fp=_fp(2, 1),
            collision={'shape': 'rect', 'rect': [-8.0, -4.0, 16, 4]}, shadow=(18, 3),
            requires=[_rel('near', 'stock', 8, 'by the stock it feeds, at a shelter or a coop')], forbids=[OFF_ROUTE, OFF_WATER],
            size_class='pile', eastward='17: sacks by the barn door', note='Sacks of feed on a pallet.')),
        ('farm_muck_heap', muck_heap(seed=6), dict(
            name='Muck heap', purpose='store', role='muck_heap', cells=(3, 1), fp=_fp(3, 1),
            collision={'shape': 'rect', 'rect': [-10.0, -4.0, 20, 4]}, shadow=(26, 3),
            requires=[_rel('near', 'stock', 10, 'mucked out of the pens beside it')], forbids=[OFF_ROUTE, OFF_WATER],
            size_class='pile', eastward='17: the farm\'s heaps of straw and dung, a fork in one',
            note='Straw and dung forked out of the pens, steaming.')),
    ]


def build(write=True, force=False):
    out = {}
    pieces = []
    for pid, frames, fps, kw in animals():
        frames = trim(frames)
        still = frames[0]
        sp = os.path.join(ART, pid + '.png')
        st = os.path.join(ART, pid + '_idle.png')
        out[sp] = to_rgba(still.a)
        out[st] = to_rgba(strip(frames))
        anim = {'clip': 'idle', 'loop': True, 'frames': len(frames), 'fps': fps, 'strip': RES + pid + '_idle.png',
                'frame_px': [still.W, still.H], 'reduced_motion': 'hold:0', 'on_screen_only': True, 'phase': 'placement'}
        pieces.append(_base(pid, kw.pop('name'), sp, (still.ax, still.ay), (still.W, still.H), kw.pop('purpose'), kw.pop('role'),
                            anim=anim, **kw))
    for pid, pic, kw in statics():
        pic = trim([pic])[0]
        sp = os.path.join(ART, pid + '.png')
        out[sp] = to_rgba(pic.a)
        pieces.append(_base(pid, kw.pop('name'), sp, (pic.ax, pic.ay), (pic.W, pic.H), kw.pop('purpose'), kw.pop('role'), **kw))
    # the redraws of the Crossroads pieces: new pictures for the existing pieces (their story,
    # gating and stages kept)
    redraw = {
        'crossroads_hay': [('hay_bales', hay_bales(seed=41)), ('hay_heap', hay_heap(seed=43))],
        'crossroads_beds_dug': [('beds_dug', beds('dug', seed=51)), ('beds_dug_b', beds('dug_b', seed=53))],
        'crossroads_beds_scorched': [('beds_scorched', beds('scorched', seed=51))],
        'crossroads_trough': [('trough', trough(seed=71))],
    }
    for pid, vs in redraw.items():
        vs[:] = [(vid, trim([pic])[0]) for vid, pic in vs]
        for vid, pic in vs:
            out[os.path.join(ART, vid + '.png')] = to_rgba(pic.a)
    if write:
        os.makedirs(ART, exist_ok=True)
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
        for pc in pieces:
            path = os.path.join(PIECES, 'prop', pc['id'] + '.json')
            if force or not os.path.exists(path):
                json.dump(pc, open(path, 'w'), indent=1)
                open(path, 'a').write('\n')
        for pid, vs in redraw.items():
            path = os.path.join(PIECES, 'prop', pid + '.json')
            pc = json.load(open(path))
            new = [{'id': vid, 'weight': 1.0, 'png': RES + vid + '.png', 'foot': [pic.ax, pic.ay]} for vid, pic in vs]
            if pc['variants'] != new:
                pc['variants'] = new
                g = pc['geometry']
                g['size_px'] = [max(p.W for _v, p in vs), max(p.H for _v, p in vs)]
                g['size_cells'] = [math.ceil(v / 24) for v in g['size_px']]
                g['foot'] = [vs[0][1].ax, vs[0][1].ay]
                pc['version'] = pc.get('version', 1) + 1
                json.dump(pc, open(path, 'w'), indent=1)
                open(path, 'a').write('\n')
        existing_metadata()
    return out


# What the existing Crossroads pieces are to an enclosure; the source fields Claude reviewed and
# authored over the seeded source (audit.overrides: seed_props keeps them on a refresh); the
# retired straight fence.
EXISTING = {
    'crossroads_beds_dug': {'enclosure': {'holds': ['crops'], 'as': 'contents'}},
    'crossroads_beds_scorched': {'enclosure': {'holds': ['crops'], 'as': 'contents'}},
    'crossroads_trough': {'enclosure': {'holds': ['sheep', 'horses', 'cattle', 'goats'], 'as': 'needs'}},
}
# The size-guide review of the solid boxes restored in #417 (3 Nov): boxes that disagreed with the
# art, in world px from the foot (docs/vision/placement-audit.md, "Solid boxes").
REVIEWED_BOXES = {
    'crossroads_lantern_lit': [-8.0, -6.0, 16, 6],      # the shard lantern's plinth (13 Nov redraw: 16 x 6; was 14 x 5)
    'crossroads_lantern_dark': [-8.0, -6.0, 16, 6],
    'crossroads_boulder': [-11.0, -6.0, 22, 6],         # was 12 wide under a 25 wide cluster
    'crossroads_bush': [-13.0, -6.0, 26, 6],            # was 16 wide under a 31 wide bush (woodland bushes: 85 %)
    'crossroads_well_choked': [-10.0, -16.0, 20, 16],   # was 24 x 20 round a 19 wide ring; now the well's own box
    'crossroads_trough': [-13.0, -8.0, 26, 8],          # the redrawn trough is 27 wide (was 20 under a 27 wide picture)
}
REDRAWN = ('crossroads_beds_dug', 'crossroads_beds_scorched', 'crossroads_hay', 'crossroads_trough')


def _save(path, pc):
    json.dump(pc, open(path, 'w'), indent=1)
    open(path, 'a').write('\n')


def _override(pc, field):
    ov = pc.setdefault('audit', {}).setdefault('overrides', [])
    if field not in ov:
        ov.append(field)
        ov.sort()


def existing_metadata():
    from scripts.art.kit import seed_props as SP
    for pid in set(EXISTING) | set(REVIEWED_BOXES) | set(REDRAWN) | {'crossroads_fence'}:
        path = os.path.join(PIECES, 'prop', pid + '.json')
        pc = json.load(open(path))
        before = json.dumps(pc, sort_keys=True)
        pc.setdefault('placement', {}).update(EXISTING.get(pid, {}))
        if pid in REVIEWED_BOXES:
            pc['geometry']['collision'] = {'rect': REVIEWED_BOXES[pid], 'shape': 'rect'}
            pc['geometry']['footprint'] = SP.footprint(REVIEWED_BOXES[pid])
            _override(pc, 'collision')
        if pid in REDRAWN:
            _override(pc, 'variants')
        if pid == 'crossroads_fence':
            pc['approval'].update(state='retired', note='Retired 3 Nov: a straight post-and-rail segment cannot close an enclosure. '
                                  'Use the fence cells fence_wattle_* and fence_picket_* (scripts/art/kit/fences.py).')
            _override(pc, 'approval')
        if json.dumps(pc, sort_keys=True) != before:
            _save(path, pc)


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('farm: stale pictures %s (run python3 -m scripts.art.kit.farm)' % ', '.join(bad[:6]))
        return 1
    print('farm: pictures current')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    print('farm: %d pictures' % len(build(force=a.force)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

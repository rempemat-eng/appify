"""Bramble (fox-folk courier, sky-blue cape) and the Mossling Grassling, drawn natively at any
density. One unit is one pixel at density 2 (Bramble 50 px feet to ear tips).

    bramble(d, action, facing, i) -> RGBA frame (anchor = feet centre at frame (W/2, H - pad))
    mossling(d, action, facing, i)
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from . import raster as pk
from .rig import TIMING

WALK_N = TIMING['walk']['frames']      # the rig's timing table (one for every folk)
WALK_MS = TIMING['walk']['ms']
IDLE_N = TIMING['idle']['frames']
IDLE_MS = TIMING['idle']['ms']

FW, FH = 64, 60       # frame in units
PAD = 4               # units of ground below the soles


def _frame(d, fw=FW, fh=FH, pad=PAD, mirror=False):
    """A frame canvas; mirror=True measures x to the left (a west facing drawn from the east
    facing's geometry, the light still upper left: SB-03)."""
    s = d / 2.0
    W = int(math.ceil(fw * s / 2)) * 2
    H = int(math.ceil(fh * s))
    oy = H - max(1, int(round(pad * s)))
    sp = pk.Sprite(W, H, s, W / 2, oy, mirror)
    sp.material_outline = d >= 1.5        # r2: outlines per material at 1.5x and 2x
    return sp


def _pxr(d, u):
    """A motion of u units as whole pixels at density d (at least one px when u != 0)."""
    s = d / 2.0
    v = u * s
    if v == 0:
        return 0
    r = int(round(v))
    if r == 0:
        r = 1 if v > 0 else -1
    return r / s


def _limb(sp, hip, foot, l1, l2, bend):
    """Knee point for a two-segment limb (bend > 0 bends the knee forward / +x)."""
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    dist = max(1e-6, math.hypot(dx, dy))
    dist_c = min(dist, l1 + l2 - 1e-3)
    a = (l1 * l1 - l2 * l2 + dist_c * dist_c) / (2 * dist_c)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    mx, my = hx + a * dx / dist, hy + a * dy / dist
    nx, ny = -dy / dist, dx / dist
    if nx * bend < 0:
        nx, ny = -nx, -ny
    return (mx + h * nx, my + h * ny)


# --------------------------------------------------------------------------------------------
# Bramble
# --------------------------------------------------------------------------------------------


FACINGS = ('S', 'N', 'E', 'W')


def _check(action, facing):
    if facing not in FACINGS:
        raise ValueError(f'facing {facing!r} is not one of {FACINGS}')
    if action not in TIMING:
        raise ValueError(f'action {action!r} is not one of {tuple(TIMING)}')


def bramble(d: float, action: str = 'idle', facing: str = 'S', i: int = 0) -> Image.Image:
    """Every facing is drawn: S front, N back, E profile, W the E geometry on a mirrored grid
    (lit from the upper left, the satchel kept on his right hip, now the far side)."""
    _check(action, facing)
    sp = _frame(d, mirror=(facing == 'W'))
    if facing == 'S':
        _bramble_S(sp, d, action, i)
    elif facing == 'N':
        _bramble_N(sp, d, action, i)
    else:
        _bramble_E(sp, d, action, i, west=(facing == 'W'))
    return sp.render()


def _eye(sp, cx, cy, d, wide=1.0, lid=True):
    """An eye: ink, about 2 x 3 px at 2x, 2 x 2 at 1.5x, with a glint at its upper left."""
    g = sp.g
    s = sp.s
    w = max(1, int(round(2.0 * s * wide)))
    h = max(2, int(round(3.0 * s))) if d >= 1.75 else 2
    if lid and d >= 1.25:
        w = 3 if d >= 1.75 else 2       # r5: a 3 px eye at 2x, 2 px at 1.5x, so the glint shows
    x0, y0 = g.px(cx, cy)
    x0 -= w // 2
    y0 -= h // 2
    m = np.zeros((g.h, g.w), bool)
    m[y0:y0 + h, x0:x0 + w] = True
    sp.detail(m, pk.ink())
    if w >= 2 and h >= 2:
        gl = np.zeros_like(m)
        gl[y0, x0] = True                 # the glint at the eye's upper left
        sp.detail(gl, pk.rgb('snow', 5), inside=False)
        if h >= 3 and lid:
            lid = np.zeros_like(m)
            lid[y0 - 1, x0:x0 + w + 1] = True
            sp.detail(lid, pk.rgb('fox', 0), inside=False)
    return m


def _bramble_S(sp, d, action, i):
    g = sp.g
    walk = action == 'walk'
    ph = 2 * math.pi * i / (WALK_N if walk else IDLE_N)
    if walk:
        bob = _pxr(d, 1.0) if (i % 3) != 0 else 0          # up on the passing frames
        liftA = max(0.0, -math.sin(ph)) * 4.0
        liftB = max(0.0, math.sin(ph)) * 4.0
        strideA, strideB = math.cos(ph) * 1.6, -math.cos(ph) * 1.6
        armA, armB = -math.cos(ph) * 3.0, math.cos(ph) * 3.0
        sway = math.sin(ph) * 1.0
        breath = 0
    else:
        bob = 0
        liftA = liftB = strideA = strideB = 0.0
        armA = armB = 0.0
        sway = 0.0
        breath = _pxr(d, 1.0) if i in (1, 2) else 0
    by = -bob                     # body offset (units, negative = up)
    hy = by - breath * 0.0        # head follows the body
    cy_breath = -breath           # chest rises
    # ---- tail (behind, to the viewer's left), white tip ------------------------------------
    tl = math.sin(ph) * 1.5 if walk else (0.6 if i in (1, 2) else 0)
    tail = g.ellipse(-12.5 + tl * 0.3, -19 + by, 6.2, 9.5, rot=-28) | g.ellipse(-9, -14 + by, 4.5, 4.5)
    tip = g.ellipse(-16.0 + tl, -26.5 + by, 4.6, 4.8, rot=-28) & tail
    sp.add('tail', tail & ~tip, 'fox', z=0, k=1.0)
    sp.add('tailtip', tip, 'plaster', base=4, z=0.1, hi=5, lo=2)
    # ---- cape behind the body ------------------------------------------------------------
    cape_back = g.poly([(-11, -29 + by), (11, -29 + by), (13.5 + sway * 0.4, -12 + by),
                        (-13.5 + sway * 0.4, -12 + by)])
    sp.add('capeback', cape_back, 'sky', base=2, lo=0, hi=3, z=1)
    # ---- legs and boots ------------------------------------------------------------------
    for side, lift, stride, nm in ((-1, liftA, strideA, 'A'), (1, liftB, strideB, 'B')):
        x = side * 4.2
        foot_y = -lift + max(0.0, stride) * 0.5
        leg = g.capsule(x, -14 + by, x, -4.5 + foot_y, 3.2, 3.0)
        sp.add('leg' + nm, leg, 'timber', base=2, lo=0, hi=3, z=2, mode='cyl')
        boot = g.rrect(x - 3.7, -6.2 + foot_y, x + 3.7 + side * 0.4, 0.0 + foot_y, 2.2)
        sp.add('boot' + nm, boot, 'earth', base=2, lo=0, hi=4, z=3)
        cuff = g.rect(x - 3.8, -6.6 + foot_y, x + 3.8, -4.8 + foot_y) & g.rrect(x - 4, -7, x + 4, 1 + foot_y, 1)
        sp.add('cuff' + nm, cuff, 'timber_warm', base=3, z=3.2, lo=1, hi=4)
        sp.mark('boot' + nm, g.rect(x - 3.7, -1.2 + foot_y, x + 4.5, 0.5 + foot_y), -1)   # sole
        sp.mark('boot' + nm, g.ellipse(x - 1.2, -3.6 + foot_y, 1.6, 1.0), 1)             # lit toe cap
        sp.mark('leg' + nm, g.rect(x - 1.8, -10.2 + foot_y * 0.5, x + 0.6, -9.2 + foot_y * 0.5), -1)  # knee crease
        sp.mark('boot' + nm, g.rect(x - 1.0, -5.6 + foot_y, x + 1.0, -4.6 + foot_y), 1)     # lace
    # ---- tunic -----------------------------------------------------------------------------
    tunic = g.poly([(-8.5, -28 + by), (8.5, -28 + by), (10.5, -16 + by), (11.2, -11.5 + by),
                    (-11.2, -11.5 + by), (-10.5, -16 + by)])
    tunic = pk.round_mask(tunic, 1)
    sp.add('tunic', tunic, 'leaf', base=3, lo=1, hi=4, z=4)
    # folds: two dark creases rising from the hem, a lit band west of each
    for fx in (-4.0, 3.2):
        sp.mark('tunic', g.capsule(fx, -11.5 + by, fx + 0.4, -15.5 + by, 0.6), -1)
        sp.mark('tunic', g.capsule(fx - 1.6, -11.5 + by, fx - 1.4, -14.5 + by, 0.55), 1)
    # hem: a darker last row
    # belt and buckle
    belt = g.rect(-10.6, -17.8 + by, 10.6, -15.4 + by) & tunic
    sp.add('belt', belt, 'timber', base=3, lo=1, hi=4, z=4.5, mode='cyl')
    buckle = g.rrect(-2.0, -18.4 + by, 2.0, -14.8 + by, 0.6)
    sp.add('buckle', buckle, 'brass', base=3, lo=2, hi=5, z=4.6)
    sp.mark('buckle', g.rect(-0.8, -17.2 + by, 0.8, -16.0 + by), -2)
    # satchel strap: from the right shoulder across to the left hip, and the bag at the left hip
    strap = g.stroke([(7.5, -28 + by), (-8.5, -15 + by)], 1.05) & ~g.rect(-12, -18.4, 12, -14.8)
    sp.add('strap', strap & tunic, 'timber_warm', base=2, lo=1, hi=4, z=4.7, mode='cyl')
    bag = g.rrect(-13.2, -17.5 + by, -6.0, -9.5 + by, 1.8)
    sp.add('bag', bag, 'timber_warm', base=3, lo=1, hi=4, z=6)
    flap = g.rrect(-13.4, -17.8 + by, -5.8, -13.5 + by, 1.6)
    sp.add('flap', flap, 'timber_warm', base=4, lo=2, hi=4, z=6.1)
    sp.mark('flap', g.rect(-14, -14.4 + by, -5, -13.4 + by), -2)
    stud = g.ellipse(-9.6, -14.6 + by, 0.9, 0.9)
    sp.add('stud', stud, 'brass', fixed=4, z=6.2)
    # ---- arms (sleeves) and paws -------------------------------------------------------------
    for side, sw, nm in ((-1, armA, 'A'), (1, armB, 'B')):
        sx = side * 10.2
        hand = (side * 12.0, -13.6 + by + sw * 0.6)
        arm = g.capsule(sx, -25.0 + by, hand[0], hand[1] - 1.6, 2.7, 2.4)
        sp.add('arm' + nm, arm, 'leaf_cool', base=3, lo=1, hi=4, z=5, line=True)
        sp.mark('arm' + nm, g.rect(side * 12 - 3, hand[1] - 3.4, side * 12 + 3, hand[1] - 2.2), -1)   # cuff
        paw = g.ellipse(hand[0], hand[1], 2.3, 2.2)
        sp.add('paw' + nm, paw, 'earth', base=2, lo=1, hi=3, z=6.5 if side > 0 else 5.5)
    # ---- capelet over the shoulders, clasp -----------------------------------------------------
    capelet = g.poly([(-6, -30.5 + by), (6, -30.5 + by), (12.6, -24.5 + by), (12.0, -20.6 + by),
                      (5.5, -22.4 + by), (0, -20.8 + by), (-5.5, -22.4 + by), (-12.0, -20.6 + by),
                      (-12.6, -24.5 + by)])
    capelet = pk.round_mask(capelet, 1)
    sp.add('capelet', capelet, 'sky', base=3, lo=1, hi=5, z=7)
    for fx in (-7.5, 7.0):          # two folds where the capelet breaks over the shoulders
        sp.mark('capelet', g.capsule(fx, -21.5 + by, fx + 0.6 * np.sign(fx), -24.0 + by, 0.65), -1)
    sp.mark('capelet', g.rect(-14, -22.0 + by, 14, -19.5 + by) & ~g.rect(-4.5, -40, 4.5, 0), -1)
    clasp = g.ellipse(0, -24.6 + by, 1.6, 1.6)
    sp.add('clasp', clasp, 'brass', base=4, lo=2, hi=5, z=7.5)
    # ---- head --------------------------------------------------------------------------------
    hb = by
    head = g.ellipse(0, -35.5 + hb, 10.2, 7.6)
    cheeks = g.poly([(-9.6, -37 + hb), (-14.2, -32.6 + hb), (-11.2, -32.0 + hb), (-13.6, -28.6 + hb),
                     (-8.0, -29.6 + hb), (-3.5, -28.0 + hb), (0, -28.8 + hb), (3.5, -28.0 + hb), (8.0, -29.6 + hb),
                     (13.6, -28.6 + hb), (11.2, -32.0 + hb), (14.2, -32.6 + hb), (9.6, -37 + hb)])
    skull = head | cheeks
    earL = g.poly([(-9.6, -37.5 + hb), (-9.2, -49.6 + hb), (-2.6, -41.6 + hb)])
    earR = g.poly([(9.6, -37.5 + hb), (9.2, -49.6 + hb), (2.6, -41.6 + hb)])
    sp.add('earL', earL, 'fox', base=3, lo=1, hi=4, z=8)
    sp.add('earR', earR, 'fox', base=3, lo=1, hi=4, z=8)
    innerL = g.poly([(-8.4, -40 + hb), (-8.4, -46.4 + hb), (-4.8, -41.8 + hb)])
    innerR = g.poly([(8.4, -40 + hb), (8.4, -46.4 + hb), (4.8, -41.8 + hb)])
    sp.add('innerL', innerL, 'earth', base=1, lo=0, hi=2, z=8.1, flat=True)
    sp.add('innerR', innerR, 'earth', base=1, lo=0, hi=2, z=8.1, flat=True)
    tipL = earL & g.rect(-12, -52 + hb, 0, -47.0 + hb)
    tipR = earR & g.rect(0, -52 + hb, 12, -47.0 + hb)
    sp.add('tipL', tipL, 'earth', base=1, lo=0, hi=2, z=8.2, flat=True)
    sp.add('tipR', tipR, 'earth', base=1, lo=0, hi=2, z=8.2, flat=True)
    sp.add('head', skull, 'fox', base=3, lo=1, hi=5, z=9, k=0.9)
    # forehead lock: a lit domino over the brow, a darker one under it
    sp.mark('head', g.ellipse(-2.6, -41.0 + hb, 2.4, 1.1), 1)
    # cream muzzle and cheeks
    muzzle = (g.ellipse(0, -31.2 + hb, 5.0, 3.4)
              | g.poly([(-14.2, -32.6 + hb), (-7.5, -34.2 + hb), (-3.0, -31.0 + hb), (-3.5, -28.0 + hb),
                        (-8.0, -29.6 + hb), (-13.6, -28.6 + hb), (-11.2, -32.0 + hb)])
              | g.poly([(14.2, -32.6 + hb), (7.5, -34.2 + hb), (3.0, -31.0 + hb), (3.5, -28.0 + hb),
                        (8.0, -29.6 + hb), (13.6, -28.6 + hb), (11.2, -32.0 + hb)])) & skull
    sp.add('muzzle', muzzle, 'plaster', base=4, lo=2, hi=5, z=9.5, k=0.8)
    nose = g.ellipse(0, -33.2 + hb, 1.6, 1.1)
    sp.detail(nose, pk.ink())
    mouth = g.rect(-0.6, -31.6 + hb, 0.6, -30.6 + hb) if d >= 1.75 else np.zeros((g.h, g.w), bool)
    sp.detail(mouth, pk.rgb('earth', 1))
    _eye(sp, -4.4, -36.2 + hb, d)
    _eye(sp, 4.4, -36.2 + hb, d)
    # chest bib of cream fur between the capelet's edges
    bib = g.poly([(-3.2, -29 + hb), (3.2, -29 + hb), (0, -25.5 + hb)])
    sp.add('bib', bib, 'plaster', base=3, lo=2, hi=4, z=7.2)


def _bramble_E(sp, d, action, i, west=False):
    """The profile. east: as drawn and approved. west (on a mirrored grid): the same geometry,
    with the light-placed marks (lit bands, lit crown) moved to the side that faces the upper
    left, and the asymmetric parts on the side they are really on: the satchel hangs on his
    right hip (the far side in W, peeking behind his back) and its strap crosses his left
    shoulder (the near side in W)."""
    g = sp.g
    L = -1 if west else 1           # light-placed offsets: their x flips with the grid
    walk = action == 'walk'
    ph = 2 * math.pi * i / (WALK_N if walk else IDLE_N)
    if walk:
        bob = _pxr(d, 1.0) if (i % 3) != 0 else 0
        stride = 8.6
        footA = (math.cos(ph) * stride, -max(0.0, -math.sin(ph)) * 4.0)
        footB = (-math.cos(ph) * stride, -max(0.0, math.sin(ph)) * 4.0)
        armA, armB = -math.cos(ph) * 5.5, math.cos(ph) * 5.5
        lag = math.sin(ph - 0.9)
        breath = 0
    else:
        bob = 0
        footA, footB = (1.2, 0.0), (-1.6, 0.0)
        armA = armB = 0.0
        lag = 0.0
        breath = 1 if i in (1, 2) else 0
    by = -bob
    # ---- tail behind (west), white tip ---------------------------------------------------------
    tl = lag * 1.4
    tail = np.zeros((g.h, g.w), bool)
    tip = np.zeros_like(tail)
    # r3: the 1x pose: the brush stretched straight back, rising only a little to its white tip
    P0, P1, P2 = (-4.0, -14.0 + by), (-14.5, -16.5 + by + tl * 0.3), (-24.0 + tl * 0.4, -21.5 + by + tl * 0.6)
    for k in range(17):
        t = k / 16
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
        r = 3.4 + 2.6 * math.sin(math.pi * min(1.0, t * 1.15)) if t < 0.92 else 3.6
        e = g.ellipse(x, y, r, r * 0.92)
        tail |= e
        if t >= 0.72:
            tip |= e
    tip &= ~g.ellipse(-17.6 + tl * 0.3, -18.5 + by + tl * 0.5, 4.0, 3.8)
    sp.add('tail', tail & ~tip, 'fox', z=0.5, k=1.0)
    sp.add('tailtip', tip, 'plaster', base=4, z=0.6, hi=5, lo=2)
    # ---- far leg, far arm (behind the body) ----------------------------------------------------
    hip = (-0.5, -13.5 + by)

    def leg(foot, nm, z, base):
        fx, fy = foot
        ankle = (fx - 0.6, -5.4 + fy)
        knee = _limb(sp, hip, ankle, 5.2, 4.6, +1)
        m = g.capsule(hip[0], hip[1], knee[0], knee[1], 3.1, 2.8) | g.capsule(knee[0], knee[1], ankle[0], ankle[1], 2.8, 2.6)
        sp.add('leg' + nm, m, 'timber', base=base, lo=0, hi=3, z=z, mode='form', k=0.8)
        boot = g.rrect(fx - 3.4, -6.4 + fy, fx + 4.4, 0.0 + fy, 2.0) | g.ellipse(fx + 2.6, -2.2 + fy, 2.3, 2.2)
        sp.add('boot' + nm, boot, 'earth', base=base, lo=0, hi=4, z=z + 0.1)
        cuff = g.rect(fx - 3.6, -7.0 + fy, fx + 3.4, -5.2 + fy)
        sp.add('cuff' + nm, cuff, 'timber_warm', base=base + 1, lo=1, hi=4, z=z + 0.2)
        sp.mark('boot' + nm, g.rect(fx - 4, -1.2 + fy, fx + 7, 0.6 + fy), -1)
        sp.mark('boot' + nm, g.ellipse(fx + 2.4, -3.8 + fy, 1.4, 0.9), 1)

    far, near = (footB, footA) if footA[0] >= footB[0] else (footA, footB)
    # the far leg is a tone darker (it stands in the body's shade)
    leg(footB, 'B', 1.5, 2)
    leg(footA, 'A', 3.0, 2)

    def arm(sw, nm, z, base):
        sh = (0.2, -25.0 + by)
        hand = (0.6 + sw, -14.6 + by + abs(sw) * 0.2)
        elbow = ((sh[0] + hand[0]) / 2 + 0.4 * sw * 0.2, -19.8 + by)
        m = g.capsule(sh[0], sh[1], elbow[0], elbow[1], 2.9, 2.6) | g.capsule(elbow[0], elbow[1], hand[0], hand[1] - 1.2, 2.6, 2.4)
        sp.add('arm' + nm, m, 'leaf_warm' if nm == 'A' else 'leaf_cool', base=base + (1 if nm == 'A' else 0), lo=1, hi=5,
               z=z, line=True)
        sp.mark('arm' + nm, g.capsule(elbow[0] + L * 1.6, elbow[1], hand[0] + L * 1.6, hand[1] - 1.4, 0.6), -2)
        sp.mark('arm' + nm, g.capsule(hand[0] - 0.2, hand[1] - 2.6, hand[0] + 0.2, hand[1] - 2.6, 2.6), -1)
        sp.mark('arm' + nm, g.capsule(sh[0] - L * 1.2, sh[1] + 1.0, elbow[0] - L * 1.4, elbow[1], 0.6), 1)
        sp.add('paw' + nm, g.ellipse(hand[0], hand[1], 2.4, 2.4), 'fox', base=base, lo=1, hi=4, z=z + 0.1)

    arm(armB, 'B', 1.2, 2)
    # ---- cape flowing behind -----------------------------------------------------------------
    fl = lag * 1.2
    cape = g.poly([(-2.0, -30.5 + by), (3.0, -29.5 + by), (1.0, -20 + by), (-1.5, -8.0 + by),
                   (-6.0 + fl, -6.2 + by), (-11.8 + fl * 1.5, -7.4 + by), (-11.0 + fl * 1.2, -13.0 + by),
                   (-7.6 + fl * 0.5, -26.0 + by)])
    cape = pk.round_mask(cape, 1)
    sp.add('cape', cape, 'sky', base=3, lo=1, hi=5, z=2.0)
    for fx in (-5.0, -8.4):
        sp.mark('cape', g.capsule(fx + fl * 0.8, -7.4 + by, fx + 1.8, -21 + by, 0.6), -1)
    if west:                        # the lit band on the fold's west (body) side
        sp.mark('cape', g.capsule(-3.4 + fl * 0.8, -7.6 + by, -1.8 + fl * 0.3, -18 + by, 0.55), 1)
    else:
        sp.mark('cape', g.capsule(-6.6 + fl * 0.8, -7.6 + by, -6.4 + fl * 0.3, -18 + by, 0.55), 1)
    sp.mark('cape', g.rect(-14, -8.2 + by, 2, -5.8 + by), -1)
    # ---- body (tunic), belt, satchel on the near hip -------------------------------------------
    tunic = g.poly([(-5.4, -28.5 + by), (5.6, -28.5 + by), (7.0, -17 + by), (7.8, -11.5 + by),
                    (-6.8, -11.5 + by), (-6.4, -18 + by)])
    tunic = pk.round_mask(tunic, 1)
    sp.add('tunic', tunic, 'leaf', base=3, lo=1, hi=4, z=4)
    sp.mark('tunic', g.capsule(1.6, -11.5 + by, 2.0, -15.4 + by, 0.6), -1)
    if west:
        sp.mark('tunic', g.capsule(3.4, -11.5 + by, 3.6, -14.4 + by, 0.55), 1)
    else:
        sp.mark('tunic', g.capsule(-0.2, -11.5 + by, 0.0, -14.4 + by, 0.55), 1)
    sp.mark('tunic', g.rect(-8, -12.6 + by, 8, -11 + by), -1)
    belt = g.rect(-6.4, -17.8 + by, 7.4, -15.4 + by) & tunic
    sp.add('belt', belt, 'timber', base=3, lo=1, hi=4, z=4.5)
    if west:
        # the strap over his left (near) shoulder: down the chest towards the front and down
        # the back, both runs leaving the near side for the far hip
        strap = g.stroke([(-6.2, -19.0 + by), (0.2, -28.6 + by), (6.8, -18.6 + by)], 1.1) & tunic & ~belt
        sp.add('strap', strap, 'timber', base=1, lo=0, hi=2, z=4.7, flat=True)
        # the bag on his right (far) hip: behind the body, a tone down, its back peeking out
        bag = g.rrect(-10.6, -16.0 + by, -2.4, -7.6 + by, 2.0)
        sp.add('bag', bag, 'clay', base=2, lo=1, hi=4, z=2.2)
        sp.mark('bag', g.rect(-11, -8.8 + by, -2, -7.4 + by), -1)
        flap = g.rrect(-10.8, -16.4 + by, -2.2, -12.2 + by, 1.8)
        sp.add('flap', flap, 'clay', base=3, lo=1, hi=4, z=2.3)
        sp.mark('flap', g.rect(-11, -13.2 + by, -2, -12.2 + by), -2)
        sp.mark('flap', g.rect(-10, -16.4 + by, -3, -15.4 + by), 1)
    else:
        strap = g.stroke([(4.5, -28 + by), (-5.5, -15.5 + by)], 1.1) & tunic & ~belt
        sp.add('strap', strap, 'timber', base=1, lo=0, hi=2, z=4.7, flat=True)
        bag = g.rrect(-10.6, -16.0 + by, -2.4, -7.6 + by, 2.0)
        sp.add('bag', bag, 'clay', base=3, lo=1, hi=5, z=5.2)
        sp.mark('bag', g.rect(-11, -8.8 + by, -2, -7.4 + by), -2)
        flap = g.rrect(-10.8, -16.4 + by, -2.2, -12.2 + by, 1.8)
        sp.add('flap', flap, 'clay', base=4, lo=2, hi=5, z=5.3)
        sp.mark('flap', g.rect(-11, -13.2 + by, -2, -12.2 + by), -2)
        sp.mark('flap', g.rect(-10, -16.4 + by, -3, -15.4 + by), 1)
        sp.add('stud', g.rrect(-7.4, -13.8 + by, -5.4, -11.8 + by, 0.5), 'brass', base=4, lo=2, hi=5, z=5.4)
    # ---- capelet on the shoulder ---------------------------------------------------------------
    capelet = g.poly([(-4.5, -31 + by), (5.6, -30.5 + by), (7.6, -25.0 + by), (6.4, -22.6 + by),
                      (0.0, -22.0 + by), (-6.2, -23.0 + by), (-7.0, -26.5 + by)])
    capelet = pk.round_mask(capelet, 1)
    arm(armA, 'A', 6.0, 3)
    sp.add('capelet', capelet, 'sky', base=3, lo=1, hi=5, z=7)
    sp.mark('capelet', g.rect(-8, -23.4 + by, 9, -21.0 + by), -1)
    sp.mark('capelet', g.capsule(2.2, -22.6 + by, 2.8, -25.0 + by, 0.6), -1)
    sp.add('clasp', g.ellipse(5.4, -25.0 + by, 1.5, 1.5), 'brass', base=4, lo=2, hi=5, z=7.5)
    # ---- head in profile, snout to the east ------------------------------------------------------
    hb = by
    head = g.ellipse(-0.8, -36.2 + hb, 8.8, 7.8)
    snout = g.poly([(2.6, -39.8 + hb), (6.4, -37.4 + hb), (11.8, -34.0 + hb), (11.8, -32.4 + hb),
                    (8.8, -30.8 + hb), (2.4, -29.6 + hb)])
    ruff = g.poly([(-8.6, -35 + hb), (-10.4, -29.0 + hb), (-6.0, -30.2 + hb), (-3.4, -28.2 + hb), (1, -29.4 + hb)])
    skull = pk.round_mask(head | snout | ruff, 1)
    earF = g.poly([(-2.4, -40.0 + hb), (-0.6, -49.8 + hb), (4.6, -41.6 + hb)])
    earB = g.poly([(-7.6, -38.8 + hb), (-7.0, -48.4 + hb), (-2.4, -41.2 + hb)])
    sp.add('earB', earB, 'fox', base=2, lo=1, hi=3, z=8)
    sp.add('tipB', earB & g.rect(-12, -52 + hb, 0, -45.6 + hb), 'earth', base=1, lo=0, hi=2, z=8.05, flat=True)
    sp.add('earF', earF, 'fox', base=3, lo=1, hi=4, z=8.2)
    sp.add('innerF', g.poly([(-1.4, -41.2 + hb), (-0.6, -46.6 + hb), (2.4, -41.8 + hb)]), 'clay', base=2, lo=1,
           hi=3, z=8.3, flat=True)
    sp.add('tipF', earF & g.rect(-12, -52 + hb, 6, -46.8 + hb), 'earth', base=1, lo=0, hi=2, z=8.35, flat=True)
    sp.add('head', skull, 'fox', base=3, lo=1, hi=5, z=9, k=0.9)
    sp.mark('head', g.ellipse(-1.0, -41.0 + hb, 2.6, 1.1), 1)
    if west:
        sp.mark('head', g.ellipse(1.6, -40.6 + hb, 4.0, 2.2) & skull, 1)         # the lit crown, brow side
    else:
        sp.mark('head', g.ellipse(-3.6, -40.4 + hb, 4.4, 2.4) & skull, 1)            # the lit crown
        sp.mark('head', g.ellipse(-6.4, -36.0 + hb, 2.2, 3.0) & skull, 1)            # the lit west cheek
    sp.mark('head', g.ellipse(3.0, -33.6 + hb, 3.2, 1.6) & skull, -1)            # under the eye, a tone down
    muzzle = g.poly([(4.0, -32.8 + hb), (11.8, -32.8 + hb), (8.8, -30.6 + hb), (3.0, -29.4 + hb),
                     (0.6, -30.6 + hb)]) & skull
    sp.add('muzzle', muzzle, 'plaster', base=4, lo=2, hi=5, z=9.5, k=0.8)
    sp.mark('head', g.capsule(-6.2, -31.5 + hb, -3.6, -33.6 + hb, 0.7), -1)    # the cheek ruff's lower lock
    sp.detail(g.ellipse(11.8, -33.4 + hb, 1.4, 1.2), pk.ink())
    _eye(sp, 4.2, -36.6 + hb, d, wide=0.9)
    sp.add('bib', g.poly([(2.0, -29.4 + hb), (6.0, -29.4 + hb), (3.6, -26.4 + hb)]), 'plaster', base=3, lo=2, hi=4,
           z=7.2)


def _bramble_N(sp, d, action, i):
    """The back view, on S's proportions, families and pose logic. From behind his right is the
    viewer's right: the tail sweeps out that side, the satchel hangs on that hip and its strap
    comes over his left shoulder (viewer's left) across the back. A foot stepping forward goes
    away from the viewer (up the frame); the legs and arms keep S's phase per side of his body."""
    g = sp.g
    walk = action == 'walk'
    ph = 2 * math.pi * i / (WALK_N if walk else IDLE_N)
    if walk:
        bob = _pxr(d, 1.0) if (i % 3) != 0 else 0
        liftA = max(0.0, -math.sin(ph)) * 4.0          # his right foot (S's viewer-left foot)
        liftB = max(0.0, math.sin(ph)) * 4.0
        strideA, strideB = math.cos(ph) * 1.6, -math.cos(ph) * 1.6
        armA, armB = -math.cos(ph) * 3.0, math.cos(ph) * 3.0
        sway = math.sin(ph) * 1.0
        lag = math.sin(ph - 0.9)
        breath = 0
    else:
        bob = 0
        liftA = liftB = strideA = strideB = 0.0
        armA = armB = 0.0
        sway = 0.0
        lag = 0.0
        breath = _pxr(d, 1.0) if i in (1, 2) else 0
    by = -bob
    sh = -breath                  # the shoulders rise with the breath
    # ---- legs and boots (his right leg on the viewer's right) -------------------------------
    for side, lift, stride, nm in ((1, liftA, strideA, 'A'), (-1, liftB, strideB, 'B')):
        x = side * 4.2
        foot_y = -lift - max(0.0, stride) * 0.5        # the forward foot is the farther one
        leg = g.capsule(x, -14 + by, x, -4.5 + foot_y, 3.2, 3.0)
        sp.add('leg' + nm, leg, 'timber', base=2, lo=0, hi=3, z=2, mode='cyl')
        boot = g.rrect(x - 3.7, -6.2 + foot_y, x + 3.7 + side * 0.4, 0.0 + foot_y, 2.2)
        sp.add('boot' + nm, boot, 'earth', base=2, lo=0, hi=4, z=3)
        cuff = g.rect(x - 3.8, -6.6 + foot_y, x + 3.8, -4.8 + foot_y) & g.rrect(x - 4, -7, x + 4, 1 + foot_y, 1)
        sp.add('cuff' + nm, cuff, 'timber_warm', base=3, z=3.2, lo=1, hi=4)
        sp.mark('boot' + nm, g.rect(x - 3.7, -1.2 + foot_y, x + 4.5, 0.5 + foot_y), -1)   # heel and sole
        sp.mark('boot' + nm, g.rect(x - 2.0, -4.2 + foot_y, x + 1.0, -2.6 + foot_y), 1)    # the lit heel counter
        sp.mark('leg' + nm, g.rect(x - 1.8, -10.2 + foot_y * 0.5, x + 0.6, -9.2 + foot_y * 0.5), -1)  # back of knee
    # ---- tunic and belt (only the sides show past the cape) -----------------------------------
    tunic = g.poly([(-8.5, -28 + by), (8.5, -28 + by), (10.5, -16 + by), (11.2, -11.5 + by),
                    (-11.2, -11.5 + by), (-10.5, -16 + by)])
    tunic = pk.round_mask(tunic, 1)
    sp.add('tunic', tunic, 'leaf', base=3, lo=1, hi=4, z=4)
    sp.add('belt', g.rect(-10.6, -17.8 + by, 10.6, -15.4 + by) & tunic, 'timber', base=3, lo=1, hi=4, z=4.5,
           mode='cyl')
    # ---- the satchel on his right hip (viewer's right), behind the cape -------------------------
    bag = g.rrect(6.0, -17.5 + by, 13.2, -9.5 + by, 1.8)
    sp.add('bag', bag, 'timber_warm', base=3, lo=1, hi=4, z=4.8)
    sp.mark('bag', g.rect(5, -10.6 + by, 14, -9.0 + by), -1)
    # ---- arms (sleeves) and paws at his sides --------------------------------------------------
    for side, sw, nm in ((1, armA, 'A'), (-1, armB, 'B')):
        sx = side * 10.2
        hand = (side * 12.0, -13.6 + by - sw * 0.6)    # a forward swing goes away (up)
        arm = g.capsule(sx, -25.0 + by, hand[0], hand[1] - 1.6, 2.7, 2.4)
        sp.add('arm' + nm, arm, 'leaf_cool', base=3, lo=1, hi=4, z=5, line=True)
        sp.mark('arm' + nm, g.rect(side * 12 - 3, hand[1] - 3.4, side * 12 + 3, hand[1] - 2.2), -1)   # cuff
        sp.add('paw' + nm, g.ellipse(hand[0], hand[1], 2.3, 2.2), 'earth', base=2, lo=1, hi=3,
               z=6.5 if side > 0 else 5.5)
    # ---- the cape to the knee, over the back ----------------------------------------------------
    sw_ = sway * 0.4
    fl = lag * 0.8
    cape = g.poly([(-8.4, -28.5 + by), (8.4, -28.5 + by), (10.6 + sw_, -16 + by), (11.6 + sw_ + fl, -9.0 + by),
                   (5.0 + sw_, -8.2 + by), (0.0 + sw_, -8.8 + by), (-5.0 + sw_, -8.2 + by),
                   (-11.6 + sw_ + fl, -9.0 + by), (-10.6 + sw_, -16 + by)])
    cape = pk.round_mask(cape, 1)
    sp.add('cape', cape, 'sky', base=3, lo=1, hi=5, z=7)
    for fx in (-4.6, 4.2):          # two folds falling from the shoulder blades, a lit band west of each
        sp.mark('cape', g.capsule(fx + sw_ + fl * 0.4, -8.6 + by, fx * 0.6, -21.0 + by, 0.6), -1)
        sp.mark('cape', g.capsule(fx - 1.8 + sw_ + fl * 0.4, -8.6 + by, fx * 0.6 - 1.6, -19.0 + by, 0.55), 1)
    sp.mark('cape', g.rect(-14, -10.0 + by, 14, -7.0 + by), -1)        # the hem
    # ---- the strap over his left shoulder, across the back to the right hip -----------------
    strap = g.stroke([(-8.0, -27.5 + by), (7.6, -15.4 + by)], 1.05)
    sp.add('strap', strap & cape, 'timber_warm', base=2, lo=1, hi=4, z=7.4, mode='cyl')
    # ---- the tail, in front of the cape, sweeping out to his right ------------------------------
    tl = lag * 1.5 if walk else (0.6 if i in (1, 2) else 0)
    tail = np.zeros((g.h, g.w), bool)
    tip = np.zeros_like(tail)
    # the profile's brush seen from behind: out from under the cape's hem, curving up his right side
    P0, P1, P2 = (2.0, -10.5 + by), (14.0 + tl * 0.3, -11.0 + by), (14.6 + tl, -26.0 + by)
    for k in range(17):
        t = k / 16
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
        r = 2.8 + 2.4 * math.sin(math.pi * min(1.0, t * 1.15)) if t < 0.92 else 3.4
        e = g.ellipse(x, y, r, r * 0.92)
        tail |= e
        if t >= 0.76:
            tip |= e
    tip &= ~g.ellipse(13.8 + tl * 0.8, -19.6 + by, 4.0, 3.6)
    sp.add('tail', tail & ~tip, 'fox', z=8, k=1.0)
    sp.add('tailtip', tip, 'plaster', base=4, z=8.1, hi=5, lo=2)
    sp.mark('tail', g.capsule(6.0 + tl * 0.1, -9.6 + by, 11.0 + tl * 0.3, -12.0 + by, 0.6), -1)   # a lock
    # ---- the capelet over the shoulders, seen from behind -----------------------------------
    capelet = g.poly([(-6, -30.5 + by + sh), (6, -30.5 + by + sh), (12.6, -24.5 + by + sh), (12.0, -20.6 + by + sh),
                      (5.5, -21.6 + by + sh), (0, -21.0 + by + sh), (-5.5, -21.6 + by + sh), (-12.0, -20.6 + by + sh),
                      (-12.6, -24.5 + by + sh)])
    capelet = pk.round_mask(capelet, 1)
    sp.add('capelet', capelet, 'sky', base=3, lo=1, hi=5, z=9)
    for fx in (-7.5, 7.0):
        sp.mark('capelet', g.capsule(fx, -21.5 + by + sh, fx + 0.6 * np.sign(fx), -24.0 + by + sh, 0.65), -1)
    sp.mark('capelet', g.rect(-14, -22.4 + by + sh, 14, -19.5 + by + sh), -1)
    sp.add('strapS', g.stroke([(-9.6, -29.0 + by + sh), (-7.0, -23.0 + by + sh)], 1.05) & capelet, 'timber_warm',
           base=2, lo=1, hi=4, z=9.2)          # the strap where it comes over the shoulder
    # ---- head from behind: fur, the ears' backs (no inner ear), no face ------------------------
    hb = by
    head = g.ellipse(0, -35.5 + hb, 10.2, 7.6)
    cheeks = g.poly([(-9.6, -37 + hb), (-14.2, -32.6 + hb), (-11.2, -32.0 + hb), (-13.6, -28.6 + hb),
                     (-8.0, -29.6 + hb), (-3.5, -29.4 + hb), (0, -30.0 + hb), (3.5, -29.4 + hb), (8.0, -29.6 + hb),
                     (13.6, -28.6 + hb), (11.2, -32.0 + hb), (14.2, -32.6 + hb), (9.6, -37 + hb)])
    skull = head | cheeks
    earL = g.poly([(-9.6, -37.5 + hb), (-9.2, -49.6 + hb), (-2.6, -41.6 + hb)])
    earR = g.poly([(9.6, -37.5 + hb), (9.2, -49.6 + hb), (2.6, -41.6 + hb)])
    sp.add('earL', earL, 'fox', base=3, lo=1, hi=4, z=10)
    sp.add('earR', earR, 'fox', base=3, lo=1, hi=4, z=10)
    sp.add('tipL', earL & g.rect(-12, -52 + hb, 0, -47.0 + hb), 'earth', base=1, lo=0, hi=2, z=10.2, flat=True)
    sp.add('tipR', earR & g.rect(0, -52 + hb, 12, -47.0 + hb), 'earth', base=1, lo=0, hi=2, z=10.2, flat=True)
    sp.add('head', skull, 'fox', base=3, lo=1, hi=5, z=11, k=0.9)
    sp.mark('head', g.ellipse(-3.0, -39.6 + hb, 3.6, 1.6), 1)                      # the lit crown
    sp.mark('head', g.ellipse(-7.0, -35.6 + hb, 2.2, 3.0) & skull, 1)             # the lit west cheek
    sp.mark('head', g.capsule(-2.0, -34.0 + hb, -0.6, -31.2 + hb, 0.7), -1)       # nape locks
    sp.mark('head', g.capsule(2.4, -34.4 + hb, 1.4, -31.4 + hb, 0.7), -1)
    # the cream tips of the cheek ruffs, just showing past the back of the head
    ruffs = (g.poly([(-14.2, -32.6 + hb), (-11.6, -33.4 + hb), (-11.2, -30.2 + hb), (-13.6, -28.6 + hb),
                     (-11.2, -32.0 + hb)])
             | g.poly([(14.2, -32.6 + hb), (11.6, -33.4 + hb), (11.2, -30.2 + hb), (13.6, -28.6 + hb),
                       (11.2, -32.0 + hb)])) & skull
    sp.add('ruff', ruffs, 'plaster', base=4, lo=2, hi=5, z=11.5, k=0.8)


# --------------------------------------------------------------------------------------------
# the Mossling (BLOB Grassling): a green mochi under a red mushroom cap, a sprout on top
# --------------------------------------------------------------------------------------------
def mossling(d: float, action: str = 'idle', facing: str = 'S', i: int = 0) -> Image.Image:
    """S front, N back (the cap from behind, the sprout, the green body, no face), E profile,
    W the E geometry on a mirrored grid with its lit marks kept on the upper left."""
    _check(action, facing)
    west = facing == 'W'
    prof = facing in ('E', 'W')
    L = -1 if west else 1
    sp = _frame(d, 36, 34, 3, mirror=west)
    g = sp.g
    walk = action == 'walk'
    ph = 2 * math.pi * i / (WALK_N if walk else IDLE_N)
    if walk:
        hop = max(0.0, math.sin(ph * 2 / 2)) if False else abs(math.sin(ph))
        lift = _pxr(d, 2.0) if i in (1, 2, 4, 5) else 0
        squash = 1.0 if i in (0, 3) else 0.0
        capl = -_pxr(d, 1.0) if i in (0, 3) else 0
    else:
        lift = 0
        squash = 1.0 if i in (1, 2) else 0.0
        capl = 0
    by = -lift
    wid = 9.6 + squash * 0.8
    hgt = 6.6 - squash * 0.6
    fx = 2.0 if prof else 0.0
    # feet
    if walk:
        fa = 1.4 * math.cos(ph)
    else:
        fa = 0.0
    for side, nm in ((-1, 'A'), (1, 'B')):
        off = fa * (1 if side < 0 else -1) if facing in ('E', 'W') else 0
        fy = -abs(off) * 0.4 if walk and lift == 0 else 0
        foot = g.ellipse(side * 4.2 + off + fx * 0.3, -1.4 + fy, 2.6, 1.6)
        sp.add('foot' + nm, foot, 'leaf', base=2, lo=0, hi=3, z=0.5)
    body = g.ellipse(0, -7.4 + by + squash * 0.6, wid, hgt)
    sp.add('body', body, 'leaf', base=3, lo=1, hi=5, z=1)
    sp.mark('body', g.ellipse(L * -4.6, -11.0 + by, 2.4, 1.1), 1)
    # cap
    cy = -15.2 + by + capl
    cap = g.ellipse(0, cy, 11.4, 6.6) & g.rect(-20, cy - 10, 20, cy + 2.2)
    cap = pk.round_mask(cap, 1)
    gills = g.ellipse(0, cy + 2.4, 10.4, 1.9) & ~cap
    sp.add('gills', gills, 'plaster', base=2, lo=1, hi=3, z=2, flat=True)
    sp.add('cap', cap, 'clay', base=3, lo=1, hi=5, z=3)
    sp.mark('cap', g.ellipse(0, cy - 4.0, 8.0, 3.4) & cap, -1)                # the darker crown
    band = cap & g.rect(-20, cy - 0.4, 20, cy + 2.2)
    sp.add('band', band, 'plaster', base=4, lo=3, hi=5, z=3.4, k=0.6)       # the pale band at the brim
    sp.mark('cap', g.ellipse(L * -4.6, cy - 3.0, 2.6, 1.2) & cap, 1)
    # sprout
    sx0 = -0.5 + fx * 0.2
    sp.add('stem', g.capsule(sx0, cy - 5.6, sx0 + 0.6, cy - 9.0, 0.8), 'leaf', base=3, lo=2, hi=4, z=2.5, flat=True)
    if facing == 'N':     # from behind the two leaves trade sides; the one on the light side stays lit
        sp.add('leafL', g.ellipse(sx0 + 2.6, cy - 9.6, 2.6, 1.3, rot=22), 'leaf', base=3, lo=2, hi=4, z=2.6)
        sp.add('leafR', g.ellipse(sx0 - 3.0, cy - 10.4, 2.4, 1.3, rot=-28), 'leaf', base=4, lo=2, hi=5, z=2.6)
    else:
        sp.add('leafL', g.ellipse(sx0 - 2.6, cy - 9.6, 2.6, 1.3, rot=-22), 'leaf', base=4 if not west else 3,
               lo=2, hi=5 if not west else 4, z=2.6)
        sp.add('leafR', g.ellipse(sx0 + 3.0, cy - 10.4, 2.4, 1.3, rot=28), 'leaf', base=3 if not west else 4,
               lo=2, hi=4 if not west else 5, z=2.6)
    if facing == 'N':     # the back: no face; a darker nape under the brim
        sp.mark('body', g.ellipse(0, -11.6 + by + squash * 0.6, 7.0, 1.4) & body, -1)
        return sp.render()
    # face
    ex = (-3.0 + fx, 3.0 + fx) if facing == 'S' else (1.6 + fx, 6.2 + fx)
    ey = -7.4 + by + squash * 0.6
    for x in ex:
        _eye(sp, x, ey, d, wide=0.8, lid=False)     # r4: the 1x master's neutral face (no brows)
    if d >= 1.4:
        for x in ex:
            blush = g.ellipse(x + (-1.6 if x < fx + 0.5 else 1.6), ey + 2.6, 1.3, 0.75)
            sp.add(f'blush{x}', blush & body, 'berry', base=4, z=1.5, flat=True)
    return sp.render()


def strip(frames, bg=(0, 0, 0, 0), gap=2) -> Image.Image:
    W = sum(f.width for f in frames) + gap * (len(frames) - 1)
    H = max(f.height for f in frames)
    out = Image.new('RGBA', (W, H), bg)
    x = 0
    for f in frames:
        out.alpha_composite(f, (x, H - f.height))
        x += f.width + gap
    return out

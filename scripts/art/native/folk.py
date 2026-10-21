"""The rig's first instances: Bramble (fox-folk forester, sky-blue cape, a satchel on his right
hip; cast.md) and the Mossling (the BLOB Grassling: a green mochi under a red mushroom cap, a
sprout on top), the familiar a step behind.

Each draw function hangs parts on the rig's Pose (native.rig.pose): body lift, feet, arm swing,
the lag of tail and cape. Parts are in units (1 texel at 2x); families are house ramps (fox is
the folk fur accent). Three views per folk: front (S), back (N) and side (E, and W drawn on the
mirrored grid with the satchel moved to the far hip, so the light stays upper left).
"""
from __future__ import annotations

import math

import numpy as np

from . import raster as pk
from .rig import Folk, eye


# ------------------------------------------------------------------------------------------------
# Bramble
# ------------------------------------------------------------------------------------------------
def _tail_front(sp, by, lag):
    g = sp.g
    tl = lag * 1.5
    tail = g.ellipse(-12.5 + tl * 0.3, -19 + by, 6.2, 9.5, rot=-28) | g.ellipse(-9, -14 + by, 4.5, 4.5)
    tip = g.ellipse(-16.0 + tl, -26.5 + by, 4.6, 4.8, rot=-28) & tail
    sp.add('tail', tail & ~tip, 'fox', z=0, k=1.0)
    sp.add('tailtip', tip, 'plaster', base=4, z=0.1, hi=5, lo=2)


def _legs_front(sp, P, by, heel=False):
    g = sp.g
    for side, (stride, fy_), nm in ((-1, P.foot_a, 'A'), (1, P.foot_b, 'B')):
        lift = -fy_
        x = side * 4.2
        foot_y = -lift + max(0.0, stride) * 0.5
        leg = g.capsule(x, -14 + by, x, -4.5 + foot_y, 3.2, 3.0)
        sp.add('leg' + nm, leg, 'timber', base=2, lo=0, hi=3, z=2, mode='cyl')
        boot = g.rrect(x - 3.7, -6.2 + foot_y, x + 3.7 + side * 0.4, 0.0 + foot_y, 2.2)
        sp.add('boot' + nm, boot, 'earth', base=2, lo=0, hi=4, z=3)
        cuff = g.rect(x - 3.8, -6.6 + foot_y, x + 3.8, -4.8 + foot_y) & g.rrect(x - 4, -7, x + 4, 1 + foot_y, 1)
        sp.add('cuff' + nm, cuff, 'timber_warm', base=3, z=3.2, lo=1, hi=4)
        sp.mark('boot' + nm, g.rect(x - 3.7, -1.2 + foot_y, x + 4.5, 0.5 + foot_y), -1)
        if not heel:
            sp.mark('boot' + nm, g.ellipse(x - 1.2, -3.6 + foot_y, 1.6, 1.0), 1)
            sp.mark('boot' + nm, g.rect(x - 1.0, -5.6 + foot_y, x + 1.0, -4.6 + foot_y), 1)
        sp.mark('leg' + nm, g.rect(x - 1.8, -10.2 + foot_y * 0.5, x + 0.6, -9.2 + foot_y * 0.5), -1)


def bramble_front(sp, P, d, facing):
    g = sp.g
    by = P.bob
    _tail_front(sp, by, P.lag if P.sway else (0.6 if P.breath else 0))
    cape_back = g.poly([(-11, -29 + by), (11, -29 + by), (13.5 + P.sway * 0.4, -12 + by), (-13.5 + P.sway * 0.4, -12 + by)])
    sp.add('capeback', cape_back, 'sky', base=2, lo=0, hi=3, z=1)
    _legs_front(sp, P, by)
    tunic = pk.round_mask(g.poly([(-8.5, -28 + by), (8.5, -28 + by), (10.5, -16 + by), (11.2, -11.5 + by),
                                  (-11.2, -11.5 + by), (-10.5, -16 + by)]), 1)
    sp.add('tunic', tunic, 'leaf', base=3, lo=1, hi=4, z=4)
    for fx in (-4.0, 3.2):
        sp.mark('tunic', g.capsule(fx, -11.5 + by, fx + 0.4, -15.5 + by, 0.6), -1)
        sp.mark('tunic', g.capsule(fx - 1.6, -11.5 + by, fx - 1.4, -14.5 + by, 0.55), 1)
    belt = g.rect(-10.6, -17.8 + by, 10.6, -15.4 + by) & tunic
    sp.add('belt', belt, 'timber', base=3, lo=1, hi=4, z=4.5, mode='cyl')
    sp.add('buckle', g.rrect(-2.0, -18.4 + by, 2.0, -14.8 + by, 0.6), 'brass', base=3, lo=2, hi=5, z=4.6)
    sp.mark('buckle', g.rect(-0.8, -17.2 + by, 0.8, -16.0 + by), -2)
    # the satchel's strap over his left shoulder (viewer's right) to the bag on his right hip
    strap = g.stroke([(7.5, -28 + by), (-8.5, -15 + by)], 1.05) & ~g.rect(-12, -18.4, 12, -14.8)
    sp.add('strap', strap & tunic, 'timber_warm', base=2, lo=1, hi=4, z=4.7, mode='cyl')
    sp.add('bag', g.rrect(-13.2, -17.5 + by, -6.0, -9.5 + by, 1.8), 'timber_warm', base=3, lo=1, hi=4, z=6)
    sp.add('flap', g.rrect(-13.4, -17.8 + by, -5.8, -13.5 + by, 1.6), 'timber_warm', base=4, lo=2, hi=4, z=6.1)
    sp.mark('flap', g.rect(-14, -14.4 + by, -5, -13.4 + by), -2)
    sp.add('stud', g.ellipse(-9.6, -14.6 + by, 0.9, 0.9), 'brass', fixed=4, z=6.2)
    for side, sw, nm in ((-1, P.arm_a, 'A'), (1, P.arm_b, 'B')):
        sx = side * 10.2
        hand = (side * 12.0, -13.6 + by + sw * 0.6)
        arm = g.capsule(sx, -25.0 + by, hand[0], hand[1] - 1.6, 2.7, 2.4)
        sp.add('arm' + nm, arm, 'leaf_cool', base=3, lo=1, hi=4, z=5, line=True)
        sp.mark('arm' + nm, g.rect(side * 12 - 3, hand[1] - 3.4, side * 12 + 3, hand[1] - 2.2), -1)
        sp.add('paw' + nm, g.ellipse(hand[0], hand[1], 2.3, 2.2), 'earth', base=2, lo=1, hi=3, z=6.5 if side > 0 else 5.5)
    capelet = pk.round_mask(g.poly([(-6, -30.5 + by), (6, -30.5 + by), (12.6, -24.5 + by), (12.0, -20.6 + by),
                                    (5.5, -22.4 + by), (0, -20.8 + by), (-5.5, -22.4 + by), (-12.0, -20.6 + by),
                                    (-12.6, -24.5 + by)]), 1)
    sp.add('capelet', capelet, 'sky', base=3, lo=1, hi=5, z=7)
    for fx in (-7.5, 7.0):
        sp.mark('capelet', g.capsule(fx, -21.5 + by, fx + 0.6 * np.sign(fx), -24.0 + by, 0.65), -1)
    sp.mark('capelet', g.rect(-14, -22.0 + by, 14, -19.5 + by) & ~g.rect(-4.5, -40, 4.5, 0), -1)
    sp.add('clasp', g.ellipse(0, -24.6 + by, 1.6, 1.6), 'brass', base=4, lo=2, hi=5, z=7.5)
    hb = by
    head = g.ellipse(0, -35.5 + hb, 10.2, 7.6)
    cheeks = g.poly([(-9.6, -37 + hb), (-14.2, -32.6 + hb), (-11.2, -32.0 + hb), (-13.6, -28.6 + hb),
                     (-8.0, -29.6 + hb), (-3.5, -28.0 + hb), (0, -28.8 + hb), (3.5, -28.0 + hb), (8.0, -29.6 + hb),
                     (13.6, -28.6 + hb), (11.2, -32.0 + hb), (14.2, -32.6 + hb), (9.6, -37 + hb)])
    skull = head | cheeks
    _ears(sp, hb, front=True)
    sp.add('head', skull, 'fox', base=3, lo=1, hi=5, z=9, k=0.9)
    sp.mark('head', g.ellipse(-2.6, -41.0 + hb, 2.4, 1.1), 1)
    muzzle = (g.ellipse(0, -31.2 + hb, 5.0, 3.4)
              | g.poly([(-14.2, -32.6 + hb), (-7.5, -34.2 + hb), (-3.0, -31.0 + hb), (-3.5, -28.0 + hb),
                        (-8.0, -29.6 + hb), (-13.6, -28.6 + hb), (-11.2, -32.0 + hb)])
              | g.poly([(14.2, -32.6 + hb), (7.5, -34.2 + hb), (3.0, -31.0 + hb), (3.5, -28.0 + hb),
                        (8.0, -29.6 + hb), (13.6, -28.6 + hb), (11.2, -32.0 + hb)])) & skull
    sp.add('muzzle', muzzle, 'plaster', base=4, lo=2, hi=5, z=9.5, k=0.8)
    sp.detail(g.ellipse(0, -33.2 + hb, 1.6, 1.1), pk.ink())
    if d >= 1.75:
        sp.detail(g.rect(-0.6, -31.6 + hb, 0.6, -30.6 + hb), pk.rgb('earth', 1))
    eye(sp, -4.4, -36.2 + hb, d)
    eye(sp, 4.4, -36.2 + hb, d)
    sp.add('bib', g.poly([(-3.2, -29 + hb), (3.2, -29 + hb), (0, -25.5 + hb)]), 'plaster', base=3, lo=2, hi=4, z=7.2)


def _ears(sp, hb, front=True):
    g = sp.g
    earL = g.poly([(-9.6, -37.5 + hb), (-9.2, -49.6 + hb), (-2.6, -41.6 + hb)])
    earR = g.poly([(9.6, -37.5 + hb), (9.2, -49.6 + hb), (2.6, -41.6 + hb)])
    sp.add('earL', earL, 'fox', base=3 if front else 2, lo=1, hi=4, z=8)
    sp.add('earR', earR, 'fox', base=3 if front else 2, lo=1, hi=4, z=8)
    if front:
        sp.add('innerL', g.poly([(-8.4, -40 + hb), (-8.4, -46.4 + hb), (-4.8, -41.8 + hb)]), 'earth', base=1, lo=0, hi=2, z=8.1, flat=True)
        sp.add('innerR', g.poly([(8.4, -40 + hb), (8.4, -46.4 + hb), (4.8, -41.8 + hb)]), 'earth', base=1, lo=0, hi=2, z=8.1, flat=True)
    sp.add('tipL', earL & g.rect(-12, -52 + hb, 0, -47.0 + hb), 'earth', base=1, lo=0, hi=2, z=8.2, flat=True)
    sp.add('tipR', earR & g.rect(0, -52 + hb, 12, -47.0 + hb), 'earth', base=1, lo=0, hi=2, z=8.2, flat=True)


def bramble_back(sp, P, d, facing):
    """From behind: the cape falls from the capelet to the hem with folds that swing with the
    walk, the satchel on his right hip (viewer's right) under its strap, the tail hanging in
    front of the cape's hem and swinging, the back of the head and the ears without their
    inner fur."""
    g = sp.g
    by = P.bob
    _legs_front(sp, P, by, heel=True)
    for side, sw, nm in ((-1, P.arm_b, 'A'), (1, P.arm_a, 'B')):
        sx = side * 10.2
        hand = (side * 12.0, -13.6 + by - sw * 0.6)
        sp.add('arm' + nm, g.capsule(sx, -25.0 + by, hand[0], hand[1] - 1.6, 2.7, 2.4), 'leaf_cool', base=3, lo=1, hi=4, z=3.5)
        sp.add('paw' + nm, g.ellipse(hand[0], hand[1], 2.3, 2.2), 'earth', base=2, lo=1, hi=3, z=3.6)
    sp.add('bag', g.rrect(6.0, -17.5 + by, 13.4, -9.5 + by, 1.8), 'timber_warm', base=3, lo=1, hi=4, z=3.8)
    sw = P.sway * 0.5
    cape = pk.round_mask(g.poly([(-9.5, -30 + by), (9.5, -30 + by), (12.5 + sw, -14 + by), (11.5 + sw, -10.2 + by),
                                 (0 + sw, -9.2 + by), (-11.5 + sw, -10.2 + by), (-12.5 + sw, -14 + by)]), 1)
    sp.add('cape', cape, 'sky', base=3, lo=1, hi=5, z=5)
    for fx in (-5.5, 0.5, 6.0):
        sp.mark('cape', g.capsule(fx + sw, -10 + by, fx * 0.7, -24 + by, 0.65), -1)
        sp.mark('cape', g.capsule(fx - 1.8 + sw, -10 + by, fx * 0.7 - 1.6, -21 + by, 0.55), 1)
    sp.mark('cape', g.rect(-14, -11.4 + by, 14, -9 + by), -1)
    sp.add('strap', g.stroke([(-7.5, -28 + by), (8.0, -15 + by)], 1.05) & cape, 'timber_warm', base=2, lo=1, hi=4, z=5.2, mode='cyl')
    capelet = pk.round_mask(g.poly([(-6, -31 + by), (6, -31 + by), (12.6, -25 + by), (12.0, -21 + by), (0, -19.6 + by),
                                    (-12.0, -21 + by), (-12.6, -25 + by)]), 1)
    sp.add('capelet', capelet, 'sky', base=3, lo=1, hi=5, z=6)
    sp.mark('capelet', g.rect(-14, -22.4 + by, 14, -19 + by), -1)
    tl = P.lag * 2.0
    tail = g.ellipse(1.5 + tl, -9.5 + by, 5.0, 7.5, rot=10 + tl * 6) | g.ellipse(0.5, -14 + by, 3.6, 3.6)
    tip = g.ellipse(2.6 + tl * 1.3, -3.6 + by, 4.2, 3.6) & tail
    sp.add('tail', tail & ~tip, 'fox', base=3, lo=1, hi=5, z=7, k=1.0)
    sp.add('tailtip', tip, 'plaster', base=4, z=7.1, hi=5, lo=2)
    hb = by
    head = g.ellipse(0, -35.5 + hb, 10.2, 7.8) | g.ellipse(0, -30.5 + hb, 9.0, 3.6)
    _ears(sp, hb, front=False)
    sp.add('head', head, 'fox', base=3, lo=1, hi=5, z=9, k=0.9)
    sp.mark('head', g.ellipse(-3.0, -40.0 + hb, 3.0, 1.2), 1)
    sp.mark('head', g.capsule(-6, -31 + hb, 6, -31 + hb, 0.7), -1)       # the ruff's line at the nape
    for x in (-10.4, 10.4):            # the cheek ruff showing either side of the nape
        sp.add(f'cheek{x}', g.ellipse(x, -31.0 + hb, 1.6, 1.8, rot=20 if x < 0 else -20) & ~head, 'fox', base=2, lo=1, hi=3, z=8.9)
    sp.mark('head', g.ellipse(2.5, -33.0 + hb, 6.5, 2.4) & head, -1)   # the back of the skull turning away


def bramble_side(sp, P, d, facing):
    """In profile, snout to the east (to the west on the mirrored grid). The satchel is on his
    right hip: the near hip facing east, the far hip facing west (behind the body)."""
    g = sp.g
    west = facing == 'W'
    by = P.bob
    tl = P.lag * 1.4
    tail = np.zeros((g.h, g.w), bool)
    tip = np.zeros_like(tail)
    P0, P1, P2 = (-4.0, -14.0 + by), (-16.0, -13.0 + by + tl * 0.3), (-19.5 + tl * 0.4, -29.0 + by + tl)
    for k in range(17):
        t = k / 16
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
        r = 3.4 + 2.6 * math.sin(math.pi * min(1.0, t * 1.15)) if t < 0.92 else 3.6
        e = g.ellipse(x, y, r, r * 0.92)
        tail |= e
        if t >= 0.72:
            tip |= e
    tip &= ~g.ellipse(-15.6 + tl * 0.3, -21.0 + by + tl * 0.6, 4.4, 3.6)
    sp.add('tail', tail & ~tip, 'fox', z=0.5, k=1.0)
    sp.add('tailtip', tip, 'plaster', base=4, z=0.6, hi=5, lo=2)
    hip = (-0.5, -13.5 + by)

    def leg(foot, nm, z, base):
        fx, fy = foot
        ankle = (fx - 0.6, -5.4 + fy)
        from .rig import limb
        knee = limb(hip, ankle, 5.2, 4.6, +1)
        m = g.capsule(hip[0], hip[1], knee[0], knee[1], 3.1, 2.8) | g.capsule(knee[0], knee[1], ankle[0], ankle[1], 2.8, 2.6)
        sp.add('leg' + nm, m, 'timber', base=base, lo=0, hi=3, z=z, mode='form', k=0.8)
        boot = g.rrect(fx - 3.4, -6.4 + fy, fx + 4.4, 0.0 + fy, 2.0) | g.ellipse(fx + 2.6, -2.2 + fy, 2.3, 2.2)
        sp.add('boot' + nm, boot, 'earth', base=base, lo=0, hi=4, z=z + 0.1)
        sp.add('cuff' + nm, g.rect(fx - 3.6, -7.0 + fy, fx + 3.4, -5.2 + fy), 'timber_warm', base=base + 1, lo=1, hi=4, z=z + 0.2)
        sp.mark('boot' + nm, g.rect(fx - 4, -1.2 + fy, fx + 7, 0.6 + fy), -1)
        sp.mark('boot' + nm, g.ellipse(fx + 2.4, -3.8 + fy, 1.4, 0.9), 1)

    leg(P.foot_b, 'B', 1.5, 2)          # the far leg, a tone darker (in the body's shade)
    leg(P.foot_a, 'A', 3.0, 2)

    def arm(sw, nm, z, base):
        sh = (0.2, -25.0 + by)
        hand = (0.6 + sw, -14.6 + by + abs(sw) * 0.2)
        elbow = ((sh[0] + hand[0]) / 2 + 0.4 * sw * 0.2, -19.8 + by)
        m = g.capsule(sh[0], sh[1], elbow[0], elbow[1], 2.9, 2.6) | g.capsule(elbow[0], elbow[1], hand[0], hand[1] - 1.2, 2.6, 2.4)
        sp.add('arm' + nm, m, 'leaf_cool', base=base, lo=1, hi=4, z=z, line=(nm == 'A'))
        sp.mark('arm' + nm, g.capsule(hand[0] - 0.2, hand[1] - 2.6, hand[0] + 0.2, hand[1] - 2.6, 2.6), -1)
        sp.add('paw' + nm, g.ellipse(hand[0], hand[1], 2.3, 2.3), 'earth', base=base - 1, lo=0, hi=3, z=z + 0.1)

    arm(P.arm_b, 'B', 1.2, 2)
    fl = P.lag * 1.2
    cape = pk.round_mask(g.poly([(-2.0, -30.5 + by), (3.0, -29.5 + by), (1.0, -20 + by), (-3.0, -12.5 + by),
                                 (-8.6 + fl, -11.0 + by), (-10.6 + fl * 1.4, -14.0 + by), (-7.2 + fl * 0.5, -26.0 + by)]), 1)
    sp.add('cape', cape, 'sky', base=3, lo=1, hi=5, z=2.0)
    for fx in (-5.4, -8.0):
        sp.mark('cape', g.capsule(fx + fl * 0.6, -12 + by, fx + 1.6, -22 + by, 0.6), -1)
    sp.mark('cape', g.capsule(-3.4, -13 + by, -2.0, -22 + by, 0.6), 1)
    tunic = pk.round_mask(g.poly([(-5.4, -28.5 + by), (5.6, -28.5 + by), (7.0, -17 + by), (7.8, -11.5 + by),
                                  (-6.8, -11.5 + by), (-6.4, -18 + by)]), 1)
    sp.add('tunic', tunic, 'leaf', base=3, lo=1, hi=4, z=4)
    sp.mark('tunic', g.capsule(1.6, -11.5 + by, 2.0, -15.4 + by, 0.6), -1)
    sp.mark('tunic', g.capsule(-0.2, -11.5 + by, 0.0, -14.4 + by, 0.55), 1)
    sp.mark('tunic', g.rect(-8, -12.6 + by, 8, -11 + by), -1)
    belt = g.rect(-6.4, -17.8 + by, 7.4, -15.4 + by) & tunic
    sp.add('belt', belt, 'timber', base=3, lo=1, hi=4, z=4.5)
    strap = g.stroke([(4.5, -28 + by), (-3.5, -16.5 + by)], 1.05) & tunic & ~belt
    sp.add('strap', strap, 'timber_warm', base=2, lo=1, hi=4, z=4.7)
    bz = 1.3 if west else 5.2           # the satchel on the far hip when he faces west
    bx = -1.0 if west else 0.0
    sp.add('bag', g.rrect(-6.8 + bx, -17.4 + by, 0.8 + bx, -9.6 + by, 1.8), 'timber_warm', base=2 if west else 3, lo=1, hi=4, z=bz)
    sp.add('flap', g.rrect(-7.0 + bx, -17.8 + by, 1.0 + bx, -13.6 + by, 1.6), 'timber_warm', base=3 if west else 4, lo=2, hi=4, z=bz + 0.1)
    sp.mark('flap', g.rect(-8 + bx, -14.5 + by, 2 + bx, -13.5 + by), -2)
    if not west:
        sp.add('stud', g.ellipse(-3.0, -14.6 + by, 0.9, 0.9), 'brass', fixed=4, z=5.4)
    capelet = pk.round_mask(g.poly([(-4.5, -31 + by), (5.6, -30.5 + by), (7.6, -25.0 + by), (6.4, -22.6 + by),
                                    (0.0, -22.0 + by), (-6.2, -23.0 + by), (-7.0, -26.5 + by)]), 1)
    arm(P.arm_a, 'A', 6.0, 3)
    sp.add('capelet', capelet, 'sky', base=3, lo=1, hi=5, z=7)
    sp.mark('capelet', g.rect(-8, -23.4 + by, 9, -21.0 + by), -1)
    sp.mark('capelet', g.capsule(2.2, -22.6 + by, 2.8, -25.0 + by, 0.6), -1)
    sp.add('clasp', g.ellipse(5.4, -25.0 + by, 1.5, 1.5), 'brass', base=4, lo=2, hi=5, z=7.5)
    hb = by
    head = g.ellipse(-0.8, -36.2 + hb, 8.8, 7.8)
    snout = g.poly([(2.6, -39.8 + hb), (6.4, -37.4 + hb), (11.8, -34.0 + hb), (11.8, -32.4 + hb), (8.8, -30.8 + hb), (2.4, -29.6 + hb)])
    ruff = g.poly([(-8.6, -35 + hb), (-10.4, -29.0 + hb), (-6.0, -30.2 + hb), (-3.4, -28.2 + hb), (1, -29.4 + hb)])
    skull = pk.round_mask(head | snout | ruff, 1)
    earF = g.poly([(-2.4, -40.0 + hb), (-0.6, -49.8 + hb), (4.6, -41.6 + hb)])
    earB = g.poly([(-7.6, -38.8 + hb), (-7.0, -48.4 + hb), (-2.4, -41.2 + hb)])
    sp.add('earB', earB, 'fox', base=2, lo=1, hi=3, z=8)
    sp.add('tipB', earB & g.rect(-12, -52 + hb, 0, -45.6 + hb), 'earth', base=1, lo=0, hi=2, z=8.05, flat=True)
    sp.add('earF', earF, 'fox', base=3, lo=1, hi=4, z=8.2)
    sp.add('innerF', g.poly([(-1.4, -41.2 + hb), (-0.6, -46.6 + hb), (2.4, -41.8 + hb)]), 'earth', base=1, lo=0, hi=2, z=8.3, flat=True)
    sp.add('tipF', earF & g.rect(-12, -52 + hb, 6, -46.8 + hb), 'earth', base=1, lo=0, hi=2, z=8.35, flat=True)
    sp.add('head', skull, 'fox', base=3, lo=1, hi=5, z=9, k=0.9)
    sp.mark('head', g.ellipse(-1.0, -41.0 + hb, 2.6, 1.1), 1)
    muzzle = g.poly([(4.0, -32.8 + hb), (11.8, -32.8 + hb), (8.8, -30.6 + hb), (3.0, -29.4 + hb), (0.6, -30.6 + hb)]) & skull
    sp.add('muzzle', muzzle, 'plaster', base=4, lo=2, hi=5, z=9.5, k=0.8)
    sp.mark('head', g.capsule(-6.2, -31.5 + hb, -3.6, -33.6 + hb, 0.7), -1)
    sp.detail(g.ellipse(11.8, -33.4 + hb, 1.4, 1.2), pk.ink())
    eye(sp, 4.2, -36.6 + hb, d, wide=0.9)
    sp.add('bib', g.poly([(2.0, -29.4 + hb), (6.0, -29.4 + hb), (3.6, -26.4 + hb)]), 'plaster', base=3, lo=2, hi=4, z=7.2)


BRAMBLE = Folk('bramble', height=50, frame=(64, 60), pad=4, gait='walk',
               draw={'front': bramble_front, 'back': bramble_back, 'side': bramble_side})


# ------------------------------------------------------------------------------------------------
# the Mossling (the BLOB Grassling)
# ------------------------------------------------------------------------------------------------
def _mossling(sp, P, d, facing):
    g = sp.g
    by = -P.lift
    squash = P.squash
    wid = 9.6 + squash * 0.8
    hgt = 6.6 - squash * 0.6
    side = facing in ('E', 'W')
    back = facing == 'N'
    fx = 2.0 if side else 0.0
    for sd, nm in ((-1, 'A'), (1, 'B')):
        off = (P.foot_a[0] if sd < 0 else P.foot_b[0]) if side else 0
        foot = g.ellipse(sd * 4.2 + off + fx * 0.3, -1.4, 2.6, 1.6)
        sp.add('foot' + nm, foot, 'leaf', base=2, lo=0, hi=3, z=0.5)
    body = g.ellipse(0, -7.4 + by + squash * 0.6, wid, hgt)
    sp.add('body', body, 'leaf', base=3, lo=1, hi=5, z=1)
    sp.mark('body', g.ellipse(-4.6, -11.0 + by, 2.4, 1.1), 1)
    cy = -15.2 + by - (P.lift * 0.5 if P.squash else 0)
    cap = pk.round_mask(g.ellipse(0, cy, 11.4, 6.6) & g.rect(-20, cy - 10, 20, cy + 2.2), 1)
    sp.add('gills', g.ellipse(0, cy + 2.4, 10.4, 1.9) & ~cap, 'plaster', base=2, lo=1, hi=3, z=2, flat=True)
    sp.add('cap', cap, 'berry', base=3, lo=1, hi=5, z=3)
    spots = ((-5.2, -3.0, 1.8), (2.0, -4.6, 1.5), (6.6, -1.6, 1.3), (-1.4, -0.4, 1.1))
    for (sx, sy, r) in spots:
        sp.add(f'spot{sx}', g.ellipse(sx + fx * 0.3, cy + sy, r, r * 0.85) & cap, 'plaster', base=4, lo=3, hi=5, z=3.5, k=0.6)
    sx0 = -0.5 + fx * 0.2 + (P.lag * 0.4 if side else 0)
    sp.add('stem', g.capsule(sx0, cy - 5.6, sx0 + 0.6, cy - 9.0, 0.8), 'leaf', base=3, lo=2, hi=4, z=2.5, flat=True)
    sp.add('leafL', g.ellipse(sx0 - 2.6, cy - 9.6, 2.6, 1.3, rot=-22), 'leaf', base=4, lo=2, hi=5, z=2.6)
    sp.add('leafR', g.ellipse(sx0 + 3.0, cy - 10.4, 2.4, 1.3, rot=28), 'leaf', base=3, lo=2, hi=4, z=2.6)
    if back:
        sp.mark('body', g.ellipse(0, -4.0 + by, 6.0, 1.4), -1)      # the shaded underside, no face
        return
    ex = (-3.0 + fx, 3.0 + fx) if not side else (1.6 + fx, 6.2 + fx)
    ey = -7.4 + by + squash * 0.6
    for x in ex:
        eye(sp, x, ey, d, wide=0.8)
    if d >= 1.4:
        for x in ex:
            sp.add(f'blush{x}', g.ellipse(x + (-1.6 if x < fx + 0.5 else 1.6), ey + 2.6, 1.3, 0.75) & body, 'berry', base=4, z=1.5, flat=True)


MOSSLING = Folk('mossling', height=26, frame=(36, 34), pad=3, gait='hop',
                draw={'front': _mossling, 'back': _mossling, 'side': _mossling})

FOLK = {'bramble': BRAMBLE, 'mossling': MOSSLING}

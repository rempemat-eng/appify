"""Mirra: adult oasis diviner.  Dark skin and an open, readable face under an ivory headwrap;
an ivory tunic to mid-thigh with a turquoise hem band, a brown belt with a gold buckle, loose
ivory trousers gathered by turquoise bands above brown boots, and a turquoise shawl with gold
trim draped round the shoulders.  Water is shaped by gestures: the hands are empty and open in
every clip, and the water, spring seals and currents are scene effects, never part of these
body sheets.  Fixed attachments, each exactly once and in the same place in every view:
  - the headwrap's tail falls from the back of the head on her LEFT side down the back;
  - a turquoise gem in a gold setting pinned on the wrap above her RIGHT ear;
  - a gold hoop in each ear;
  - turquoise wrist bands with gold studs on both forearms (they ride on the forearm);
  - the shawl's long end thrown back over the LEFT shoulder, hanging down the back.
About 74 px tall.

Pass 2: pose-driven on parts.Rig, with designer 1's Shift kit from morel.py.
Equipment tags: gem, tail, shawl, bands."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, EYE, Rig
import palette  # noqa: F401
import anim
import turn
from morel import Shift, add3, sub3, mul3, nrm, sdir, frame, legs, boot, arm_z, open_hand, up_z, reach

ID = 'mirra'
NAME = 'Mirra'
HEIGHT = 74
BAND = (68, 79)

mat('skin_m',  ['#301810', '#55301C', '#7A4A2C', '#A06A42'])
mat('ivory',   ['#7A6656', '#BCA284', '#E8D6B6', '#FCF2DC'])
mat('turq',    ['#0C3450', '#18628A', '#2690B8', '#5CC4D8', '#C8F4F8'])
mat('blush_m', ['#5C2C22', '#8E4636', '#AC5E48', '#C47E64'])        # dark-skin blush (tone 1)
mat('jewel',   ['#0A4A5A', '#14808E', '#2CC0C4', '#9CF0EC', '#FFFFFF'])

SHW = 12.0
REST_R = (2.0, 24.5, 14.5)
REST_L = (2.0, 24.5, -14.5)
HANG = (0.15, -1.0, 0.0)


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0,
             footR=(2.0, 0.0), footL=(-2.0, 0.0), stance=5.5,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             fingR=HANG, fingL=HANG, blink=False, brow=0, face=None)
    p.update(k)
    return p


# ------------------------------------------------------------------------------------ head
def wrap_folds(X, Y, t, hx, hy, side):
    """Wound layers of the headwrap: three diagonal fold lines in the shadow tone."""
    out = t.copy()
    k = 0.55 if side != 2 else -0.4
    for c in (-6.0, -2.0, 2.0):
        m = (np.abs((Y - hy) - c - (X - hx) * k) < 0.5 + 0.5 * abs(k)) & (Y < hy - 1.5)      # 4-connected: no dotted folds
        out[m & (t >= 2)] = 1
    return out


def headwrap(f, hx, hy, side):
    """Ivory headwrap: a rounded wound dome sitting low on the brow, ears free below its edge."""
    if side == 0:
        m = f.ell(hx, hy - 4.5, 10.0, 8.6) & (f.Y < hy - 0.5)
        m |= f.ell(hx - 1.5, hy - 10.5, 6.5, 3.2)
    elif side == 1:
        m = f.ell(hx - 1.0, hy - 4.5, 9.6, 8.6) & (f.Y < hy + 0.5)
        m |= f.ell(hx - 3.5, hy - 10.5, 6.2, 3.2) | f.ell(hx - 6.0, hy - 0.5, 3.6, 4.6)
        m &= ~(f.ell(hx + 6.0, hy + 3.5, 5.6, 5.4) & (f.Y > hy - 0.5))
    else:
        m = (f.ell(hx, hy - 4.0, 10.0, 8.8) & (f.Y < hy + 2.5)) | f.ell(hx + 1.5, hy - 10.5, 6.5, 3.2)
    f.add(m, 'ivory', z=44, rl=1.8, rs=3.0, ts=0.36, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: wrap_folds(X, Y, t, hx, hy, side))


def gem(f, x, y, z):
    """The turquoise gem in its gold setting, pinned on the wrap."""
    f.add(f.ell(x, y, 2.4, 2.4), 'gold', z=z, rl=1, rs=1.2, line='hard', tag='gem')
    f.add(f.ell(x, y, 1.3, 1.3) | f.rect(x - 1, y - 1, x + 1, y + 1), 'jewel', z=z + 0.01, flat=2, line=None)
    f.dot(x - 1, y - 1, ('jewel', 4), solid=False)


def wrap_tail(f, x, y, z, lag=0.0, dim=0, length=15):
    """The free end of the headwrap, falling from (x, y) down the back."""
    m = f.poly([(x - 2.0, y), (x + 2.2, y), (x + 1.4 - lag * 0.6, y + length), (x - 2.6 - lag, y + length - 1)])
    f.add(m, 'ivory', z=z, rl=1.4, rs=2.0, vgrad=0.3, line='hard', dim=dim, tag='tail',
          tonemap=lambda X, Y, t: np.where((np.abs(X - x + 0.2 + (Y - y) * 0.06) < 0.5) & (Y > y + 3) & (t >= 2), 1, t))


def hoop(f, x, y):
    """A small gold hoop hanging from the earlobe at (x, y): a 3x3 ring, lit at its upper left."""
    f.detail(f.pixels([(x, y), (x - 1, y + 1), (x + 1, y + 1), (x, y + 2)]), ('gold', 1))
    f.dot(x - 1, y + 1, ('gold', 3))
    f.dot(x, y, ('gold', 2))


def head_south(f, P, hy):
    f.add(f.ell(-8.4, hy + 1.8, 1.8, 2.6) | f.ell(8.4, hy + 1.8, 1.8, 2.6), 'skin_m', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 1.2, 8.0, 9.0), 'skin_m', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    headwrap(f, 0, hy, 0)
    gem(f, -6.5, hy - 2.5, z=45)                      # right side above the ear: viewer's left
    hoop(f, -9, hy + 4.5)
    hoop(f, 9, hy + 4.5)
    ey = hy + 1.5
    if P['blink']:
        f.detail(f.rect(-5, ey + 3, -3, ey + 4), EYE)
        f.detail(f.rect(3, ey + 3, 5, ey + 4), EYE)
    else:
        eye(f, -5, ey, 4)
        eye(f, 3, ey, 4)
    # open, warm face: lifted brows, soft smile
    f.detail(f.rect(-6, ey - 2, -3, ey - 1) | f.rect(-3, ey - 3, -2, ey - 2), ('skin_m', 0))
    f.detail(f.rect(3, ey - 2, 6, ey - 1) | f.rect(2, ey - 3, 3, ey - 2), ('skin_m', 0))
    f.detail(f.rect(-1, hy + 5, 1, hy + 6), ('skin_m', 3))
    f.detail(f.rect(0, hy + 6, 1, hy + 7), ('skin_m', 1))
    f.detail(f.rect(-1, hy + 8, 2, hy + 9), ('skin_m', 0))
    f.detail(f.rect(-7, hy + 6, -5, hy + 7), ('blush_m', 1))
    f.detail(f.rect(5, hy + 6, 7, hy + 7), ('blush_m', 1))


def head_side(f, P, hy, hx, west):
    # the wrap tail falls from the back of the head on her left: far side in east, near in west
    wrap_tail(f, hx - 6.5, hy + 0.5, z=2 if not west else 46, lag=P['lag'], dim=0 if west else 1)
    f.add(f.ell(hx + 1.8, hy + 1.2, 7.2, 9.0), 'skin_m', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(hx + 8.6, hy + 3.8, 1.3, 1.4), 'skin_m', z=40.5, rl=1, rs=1, line='hard')
    headwrap(f, hx, hy, 1)
    f.add(f.ell(hx - 1.4, hy + 2.6, 1.7, 2.4), 'skin_m', z=45, rl=1, rs=1.2, line='hard')
    f.dot(hx - 1.4, hy + 2.6, ('skin_m', 1))
    hoop(f, hx - 1.5, hy + 5)
    if not west:
        gem(f, hx - 0.5, hy - 3.0, z=45.5)            # right side above the ear: near in east
    ey = hy + 1.5
    if P['blink']:
        f.detail(f.rect(hx + 4, ey + 3, hx + 6, ey + 4), EYE)
    else:
        eye(f, hx + 4, ey, 4)
    f.detail(f.rect(hx + 4, ey - 2, hx + 7, ey - 1) | f.rect(hx + 3, ey - 3 + 1, hx + 4, ey - 1), ('skin_m', 0))
    f.detail(f.rect(hx + 6, hy + 8, hx + 8, hy + 9), ('skin_m', 0))
    f.detail(f.rect(hx + 3, hy + 6, hx + 5, hy + 7), ('blush_m', 1))


def head_north(f, P, hy):
    f.add(f.ell(-8.4, hy + 1.8, 1.8, 2.6) | f.ell(8.4, hy + 1.8, 1.8, 2.6), 'skin_m', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 1.2, 8.0, 9.0), 'skin_m', z=40, rl=2.0, rs=3.0, line='hard')
    headwrap(f, 0, hy, 2)
    hoop(f, -9, hy + 4.5)
    hoop(f, 9, hy + 4.5)
    # tail on her left: viewer's left from behind
    wrap_tail(f, -4.0, hy + 1.0, z=46, lag=P['lag'])
    # the gem on the right side (viewer's right from behind): its setting shows past the wrap's edge
    f.add(f.ell(9.6, hy - 2.5, 1.5, 1.6), 'gold', z=45.5, rl=1, rs=1, line='hard', tag='gem')
    f.dot(10, hy - 2.5, ('jewel', 2), z=45.6, tag='gem')


def head_3q(f, P, hy, back, west):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW on the mirrored grid).  The gem is on
    her RIGHT (near in SE and NE), the wrap's tail on her LEFT (near in the mirrored facings)."""
    if back:
        f.add(f.ell(7.8, hy + 1.8, 1.8, 2.6), 'skin_m', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(0.6, hy + 1.2, 8.0, 9.0), 'skin_m', z=40, rl=2.0, rs=3.0, line='hard')
        headwrap(f, 0.6, hy, 2)
        hoop(f, 8, hy + 4.5)
        wrap_tail(f, 4.0 if west else -3.6, hy + 1.0, z=46, lag=P['lag'])
        if not west:
            f.add(f.ell(9.6, hy - 2.5, 1.5, 1.6), 'gold', z=45.5, rl=1, rs=1, line='hard', tag='gem')
            f.dot(10, hy - 2.5, ('jewel', 2), z=45.6, tag='gem')
        return
    wrap_tail(f, -6.2, hy + 0.5, z=46 if west else 2, lag=P['lag'], dim=0 if west else 1)
    f.add(f.ell(-5.6, hy + 1.8, 1.7, 2.5), 'skin_m', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(1.2, hy + 1.2, 7.8, 9.0), 'skin_m', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    headwrap(f, 0.8, hy, 0)
    if not west:
        gem(f, -4.6, hy - 2.5, z=45)
    hoop(f, -6, hy + 4.5)
    ey = hy + 1.5
    if P['blink']:
        f.detail(f.rect(-1, ey + 3, 1, ey + 4), EYE)
        f.detail(f.rect(5, ey + 3, 7, ey + 4), EYE)
    else:
        eye(f, -1, ey, 4)
        eye(f, 5, ey, 4)
    f.detail(f.rect(-2, ey - 2, 1, ey - 1) | f.rect(1, ey - 3, 2, ey - 2), ('skin_m', 0))
    f.detail(f.rect(5, ey - 2, 8, ey - 1) | f.rect(4, ey - 3, 5, ey - 2), ('skin_m', 0))
    f.detail(f.rect(2, hy + 5, 4, hy + 6), ('skin_m', 3))
    f.detail(f.rect(3, hy + 6, 4, hy + 7), ('skin_m', 1))
    f.detail(f.rect(2, hy + 8, 5, hy + 9), ('skin_m', 0))
    f.detail(f.rect(-3, hy + 6, -1, hy + 7), ('blush_m', 1))
    f.detail(f.rect(7, hy + 6, 8, hy + 7), ('blush_m', 1))


# ------------------------------------------------------------------------------------ body
def tunic_front(f, b, ub, back=False):
    body = f.ell(0, -37.5 + ub, 11.0, 10.5) | f.rect(-10.2, -40 + ub, 10.2, -28 + b)
    skirt = f.poly([(-10.2, -29 + b), (10.2, -29 + b), (12.8, -17 + b), (-12.8, -17 + b)])
    f.add(body | skirt, 'ivory', z=20, rl=2, rs=3.6, vgrad=0.35, line='hard',
          tonemap=lambda X, Y, t: np.where((np.abs(X) < 0.5) & (Y > -24 + b) & (t >= 1), 0, t) if not back else t)
    f.add(skirt & (f.Y > -19.5 + b), 'turq', z=20.5, rl=1, rs=1.6, line='soft')
    f.add(f.rect(-10.6, -30.5 + b, 10.6, -27.5 + b), 'leather', z=24, rl=1, rs=1.2, line='soft')


def shawl_front(f, ub):
    """Turquoise shawl over both shoulders, a gold-trimmed edge dipping to a soft V at the chest."""
    sh = f.ell(0, -44 + ub, 13.0, 6.0) | f.rect(-13, -45 + ub, 13, -41 + ub)
    sh |= f.poly([(-13.5, -42 + ub), (-9, -35 + ub), (0, -33.5 + ub), (9, -35 + ub), (13.5, -42 + ub)])
    sh &= ~f.ell(0, -48.5 + ub, 5.8, 3.0)
    f.add(sh, 'turq', z=26, rl=2, rs=3.2, vgrad=0.4, line='hard', cast=(0, 1, 1), deep=True,
          tonemap=lambda X, Y, t: _shawl_trim(X, Y, t, ub))
    trim(f, sh)
    # gathered collar round the neck
    f.add(f.ell(0, -47 + ub, 7.8, 3.0) & ~f.ell(0, -48.5 + ub, 5.0, 2.0), 'turq', z=27, rl=1.4, rs=2, line='hard')


def trim(f, m):
    """Gold trim along the lower edge of a shawl mask: the bottom pixel of each column."""
    edge = m & ~np.roll(m, -1, 0)
    f.detail(edge, ('gold', 2), solid=False)


def _shawl_trim(X, Y, t, ub):
    """A gold-looking trim is drawn as the light tone line one pixel in from the hem."""
    out = t.copy()
    hem = -33.5 + ub + (np.abs(X) / 13.5) ** 1.6 * 8.5
    m = (Y > hem - 2.4) & (Y < hem - 1.2)
    out[m] = 3
    return out


def torso_south(f, P, b, ub):
    f.add(f.poly([(10, -44 + ub), (13.5, -42 + ub), (14.5 + P['lag'] * 0.3, -24 + b), (11, -25 + b)]), 'turq', z=3, rl=1.2, rs=2,
          dim=1, line='hard', tag='shawl')
    tunic_front(f, b, ub)
    f.add(f.rect(-2, -31 + b, 2, -27 + b), 'gold', z=24.5, rl=1, rs=1.2, line='hard')
    with f.tagging('shawl'):
        shawl_front(f, ub)


def torso_north(f, P, b, ub):
    tunic_front(f, b, ub, back=True)
    with f.tagging('shawl'):
        sh = f.ell(0, -42 + ub, 13.6, 6.5) | f.poly([(-13.5, -42 + ub), (-10, -34 + ub), (0, -32 + ub), (10, -34 + ub), (13.5, -42 + ub)])
        f.add(sh, 'turq', z=26, rl=2, rs=3.2, vgrad=0.4, line='hard', deep=True,
              tonemap=lambda X, Y, t: np.where((np.abs(Y + 34 - ub - (np.abs(X) / 13.5) ** 1.6 * 7) < 0.6) & (t >= 1), 3, t))
        trim(f, sh)
        end = f.poly([(-11, -46 + ub), (-6, -46 + ub), (-4.5 - P['lag'] * 0.3, -21 + b), (-9.5 - P['lag'], -22 + b)])
        f.add(end, 'turq', z=27, rl=1.6, rs=2.6, vgrad=0.3, line='hard', cast=(1, 1, 1),
              tonemap=lambda X, Y, t: np.where((np.abs(Y + 23.5 - b) < 0.6) & (t >= 1), 3, t))


def torso_side(f, P, b, ub, tx, west):
    lag = P['lag']
    body = f.ell(0.5 + tx, -37.5 + ub, 8.8, 10.5) | f.poly([(-8, -28 + b), (-8.4 + tx, -40 + ub), (9 + tx, -40 + ub), (9.4, -28 + b)])
    skirt = f.poly([(-8, -29 + b), (9.4, -29 + b), (11.5, -17 + b), (-10.5, -17 + b)])
    f.add(body | skirt, 'ivory', z=20, rl=2, rs=3.6, vgrad=0.35, line='hard')
    f.add(skirt & (f.Y > -19.5 + b), 'turq', z=20.5, rl=1, rs=1.6, line='soft')
    f.add(f.rect(-8.4, -30.5 + b, 9.8, -27.5 + b), 'leather', z=24, rl=1, rs=1.2, line='soft')
    f.add(f.rect(7.6, -31 + b, 10.2, -27 + b), 'gold', z=24.5, rl=1, rs=1.2, line='hard')
    with f.tagging('shawl'):
        sh = f.poly([(-9.5 + tx, -47 + ub), (-3 + tx, -49.5 + ub), (5 + tx, -49 + ub), (9.6 + tx, -45 + ub), (10.6 + tx, -38 + ub),
                     (6 + tx, -34.5 + ub), (-2 + tx, -35.5 + ub), (-10.5 + tx - lag * 0.5, -36 + ub)])
        f.add(sh, 'turq', z=26, rl=2, rs=3.2, vgrad=0.4, line='hard', cast=(0, 1, 1), deep=True,
              tonemap=lambda X, Y, t: np.where((np.abs(Y - (-37.2 + ub) - (X - tx) * -0.05) < 0.6) & (t >= 1), 3, t))
        trim(f, sh & (f.Y > -41 + ub))
        end = f.poly([(-9.0 + tx, -46 + ub), (-4.0 + tx, -47 + ub), (-6.5 - lag * 0.4, -22 + b), (-11.5 - lag, -23 + b)])
        f.add(end, 'turq', z=4 if not west else 27, rl=1.6, rs=2.6, vgrad=0.3, line='hard', dim=0 if west else 1,
              tonemap=lambda X, Y, t: np.where((np.abs(Y + 24.5 - b) < 0.6) & (t >= 1), 3, t))


# ------------------------------------------------------------------------------------ build
def _leg(f, R, up, lo, kn3, foot3, lat, far, z):
    dim = 1 if far else 0
    f.add(up | lo, 'ivory', z=z, rl=1.8, rs=3.0, vgrad=0.3, dim=dim, line='hard')
    fx, fy = boot(f, R, foot3, 'leather', z, far)
    f.add(f.rect(fx - 4.6, fy - 9.5, fx + 4.6, fy - 7.5), 'turq', z=z + 1.1, rl=1, rs=1.4, dim=dim, line='hard')


def _arm(f, R, sh3, h3, pole, z, far):
    up, lo, el3 = R.limb(sh3, h3, 8.0, 8.2, 3.8, 3.6, 3.3, pole)
    dim = 1 if far else 0
    f.add(up, 'ivory', z=up_z(R, z, far), rl=1.6, rs=2.6, line='hard', dim=dim, cast=(1, 1, 1) if not dim else None)
    f.add(lo, 'ivory', z=z - 0.05, rl=1.6, rs=2.6, line='hard', dim=dim, cast=(1, 1, 1) if not dim else None)
    e, w = R.p(el3), R.p(h3)
    tx, ty = w[0] * 0.72 + e[0] * 0.28, w[1] * 0.72 + e[1] * 0.28
    with f.tagging('bands'):
        f.add(f.cap(tx, ty, w[0] * 0.95 + e[0] * 0.05, w[1] * 0.95 + e[1] * 0.05, 3.3, 3.1), 'turq', z=z + 0.1, rl=1.2, rs=1.8,
              line='hard', dim=dim)
        if not dim:
            f.dot(tx - 1, ty - 0.5, ('gold', 3), z=z + 0.12)
            f.dot(tx + 1, ty + 1.0, ('gold', 2), z=z + 0.12)
    return el3


def build(f, facing, P):
    R = Rig(f, facing)
    west = facing in ('W', 'SW', 'NW')
    if P['face'] == 'shut':
        P = dict(P, blink=True)
    hip3, sh3, head3 = frame(P, 21.0, 21.0, 15.0)
    body_off = (P['hipx'], -P['crouch'] - P['bob'], 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    b = hy + 21.0
    ub = sy + 42.0
    tx = sx - hx
    shR = add3(sh3, (0.0, -1.0, SHW))
    shL = add3(sh3, (0.0, -1.0, -SHW))
    hR = add3(P['handR'] or REST_R, body_off)
    hL = add3(P['handL'] or REST_L, body_off)
    hR = reach(shR, hR, 16.2)
    hL = reach(shL, hL, 16.2)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    legs(f, R, P, hip3, _leg, 8.6, 8.4)
    with Shift(f, hx, 0):
        if R.diag:                       # contract v2 turn in-betweens: the S or N torso turned onto the body
            with turn.Warp(f, R, tx * 0.5, 11.0, 8.5, 'N' if R.back else 'S'):
                (torso_north if R.back else torso_south)(f, P, b, ub)
        elif facing == 'S':
            torso_south(f, P, b, ub)
        elif facing == 'N':
            torso_north(f, P, b, ub)
        else:
            torso_side(f, P, b, ub, tx, west)
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        pole = P['pole' + key] or (-1.0, -0.25, 0.6 * lat)
        z = arm_z(R, P, key, hh)
        if R.back and z < 40 and z > 20:
            z = 24.6                       # from behind the shawl drapes over the upper arms
        far = R.far(lat)
        _arm(f, R, sh, hh, pole, z, far)
        fing = P['fing' + key]
        thumb = (0.6, 0.2, -0.6 * lat) if fing[1] > -0.5 else (1.0, 0.0, -0.3 * lat)
        tip = open_hand(f, R, hh, fing, z + 0.8, 'skin_m', dim=1 if far else 0, thumb3=thumb)
        f.anchor('palm_' + key, *tip)
        # the shawl drapes over the shoulder top
        px, py = R.p(sh)
        if not R.back:
            f.add(f.ell(px, py - 0.5, 4.6, 3.8) & (f.Y < py + 1.5), 'turq', z=max(31.0, z + 0.2) if not far else up_z(R, z, far) + 0.2,
                  rl=1.4, rs=2.2, line='soft', dim=1 if far else 0, tag='shawl')
    hx2, hy2 = R.p(head3)
    with Shift(f, hx2, 0):
        if R.diag:
            head_3q(f, P, hy2, R.back, west)
        elif facing == 'S':
            head_south(f, P, hy2)
        elif facing == 'N':
            head_north(f, P, hy2)
        else:
            head_side(f, P, hy2, 0.0, west)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True              # merge lone stud and trim pixels (ew.despeckle)
    build(f, facing, P)
    return f

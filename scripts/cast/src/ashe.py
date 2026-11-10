"""Ashe: adult ember knight.  Red swept hair and an open face, steel plate (breastplate, big
pauldrons, faulds, knee cops, gauntlets) edged in brass, a crimson cape behind and a crimson
tabard hanging in front from the belt, brown leather boots.  ONE sword in the RIGHT hand (steel
blade with a fuller, brass cross guard, leather grip, brass pommel) and ONE helmet: a barred-visor
helm with a crimson crest, carried under the LEFT arm (the hand cups its chin) in the normal form.

Pass 2: one pose-driven build for all four facings (parts.Rig), like bramble.py.  The helm is one
object with one size that fits over the head: helm_t moves it along one path from under the left
arm (0) to the head (1).  It leaves the hand only when it reaches the head; on the head the hair
and face are inside it.  Cinderhelm (special) lifts it on and the armour's seams light (ember=1):
the same plates, their brass trim drawn in the ember ramp.  powered_exit takes it off again.

Equipment tags: sword, helm."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, boot_side, boot_front, EYE, Rig
import palette  # noqa: F401
import anim
from brine import add3, nrm, shoulders
import surf
import turn

ID = 'ashe'
NAME = 'Ashe'
HEIGHT = 75
BAND = (71, 81)

mat('ashe_steel',   ['#1C2036', '#363D5C', '#5A638C', '#909AC0', '#E4EAF8'])
mat('ashe_crimson', ['#3C0A18', '#6C1026', '#A81C38', '#D63C50'])
mat('ashe_hair',    ['#4A0E0C', '#881A10', '#C6341A', '#EE6A32'])
mat('ashe_blade',   ['#4A5266', '#8890A4', '#C4CAD6', '#EEF2F8', '#FFFFFF'])
mat('ashe_ember',   ['#7A1C08', '#D2480E', '#FF8A1E', '#FFD25A', '#FFF6C8'])

SHW = 10.5
ARM = (9.0, 8.6)
REST_R = (5.0, 28.5, 13.5)
REST_DIR = (0.5, -0.85, 0.12)         # v2: the blade continues the lowered forearm, forward and down, clear of the foot
HELM_ARM = (-2.0, 30.5, -15.0)          # helm centre when carried under the left arm
HELM_R = 10.0


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0, blink=False, face=None, brow=0,
             footR=(1.5, 0.0), footL=(-1.5, 0.0), stance=5.8,
             handR=None, sdir=None, handL=None, two=False, twist=None, poleR=None, poleL=None,
             helm_t=0.0, ember=0.0, sword='hand')
    p.update(k)
    return p


def trim_mat(P):
    return 'ashe_ember' if P['ember'] > 0.5 else 'gold'


# ------------------------------------------------------------------------------------ gear
def sword(f, R, g3, d3, z, dim=0, blade=23.0, ember=False):
    """The sword gripped at g3 (grip centre), blade along d3.  Returns the tip (pivot space)."""
    d = nrm(d3)
    w = np.cross(d, np.array([0.0, 1.0, 0.0]))
    if np.linalg.norm(w) < 0.2:
        w = np.cross(d, np.array([1.0, 0.0, 0.0]))
    w = nrm(w)

    def P(a, c=0.0):
        return R.p(tuple(np.array(g3) + d * a + w * c))
    with f.tagging('sword'):
        f.add(f.cap(*P(-3.0), *P(2.6), 1.3), 'leather', z=z, flat=1, dim=dim, line='hard')
        pm = P(-4.4)
        f.add(f.ell(pm[0], pm[1], 1.9, 1.9), 'gold', z=z + 0.1, rl=1, rs=1.2, dim=dim, line='hard')
        # cross guard across the blade: drawn on screen across the projected blade
        b0, b1 = P(3.6), P(8.0)
        ux, uy = b1[0] - b0[0], b1[1] - b0[1]
        L = math.hypot(ux, uy)
        if L > 0.5:
            ux, uy = ux / L, uy / L
        else:
            ux, uy = 0.0, 1.0
        px, py = -uy, ux
        cg = b0
        gw = 4.2 * max(0.55, min(1.0, math.hypot(*np.subtract(P(0, 1), P(0, 0)))))
        f.add(f.cap(cg[0] - px * 4.2, cg[1] - py * 4.2, cg[0] + px * 4.2, cg[1] + py * 4.2, 1.2), 'gold', z=z + 0.1,
              rl=1, rs=1.2, dim=dim, line='hard')
        s0 = P(4.8)
        tip = P(4.8 + blade)
        sh = P(blade + 0.8)
        Lb = math.hypot(tip[0] - s0[0], tip[1] - s0[1])
        hw = 1.9
        bl = f.poly([(s0[0] - px * hw, s0[1] - py * hw), (s0[0] + px * hw, s0[1] + py * hw),
                     (sh[0] + px * hw, sh[1] + py * hw), tip, (sh[0] - px * hw, sh[1] - py * hw)])
        if Lb < 4:
            bl |= f.ell(tip[0], tip[1], 1.8, 1.8)
        f.add(bl, 'ashe_blade', z=z + 0.05, rl=1.2, rs=1.4, dim=dim, line='hard')
        if Lb > 8 and (abs(ux) < 0.25 or abs(uy) < 0.25):
            fa, fb = P(6.8), P(18.8)
            f.add(f.seg(*fa, *fb) & bl, 'ashe_ember' if ember else 'ashe_blade', z=z + 0.06, flat=1 if not ember else 3,
                  dim=dim, line=None, clean=False)
        _ = gw
    return tip


def helm(f, x, cy, z, view='front', dim=0, trim='gold', ember=False, glint=True, worn=False):
    """The one helmet, centre (x, cy), sized to fit over the head.  view: 'front' shows the barred
    visor, 'side' its profile (visor toward +x), 'back' its plain rear.  Brass (or ember) rim and
    visor frame, crimson crest from brow to nape."""
    r = HELM_R
    with f.tagging('helm'):
        shell = f.ell(x, cy - 0.5, r, r + 0.2) | f.rect(x - r, cy, x + r, cy + r * 0.85)
        shell &= f.Y < cy + r * 0.9
        f.add(shell, 'ashe_steel', z=z, rl=1.8, rs=2.6, dim=dim, line='hard', cast=(0, 1, 1) if worn else None,
              tonemap=lambda X, Y, t: _shell_planes(X, Y, t, x, cy, r, _west(f)))
        f.add(f.rect(x - r, cy + r * 0.65, x + r, cy + r * 0.9) & shell, trim, z=z + 0.1, rl=1, rs=1, dim=dim, line='soft')
        sl = 'ashe_ember' if ember else 'ashe_steel'
        if view == 'front':
            vis = f.rect(x - 6.0, cy - 1.0, x + 6.5, cy + 4.0)
            f.add(vis, sl, z=z + 0.2, flat=0 if not ember else 2, dim=dim, line=None, tag='face' if worn else None)   # worn, the visor is her face
            bars = None
            for bx in (-4.5, -1.5, 1.5, 4.5):
                m = f.rect(x + bx, cy - 1.0, x + bx + 1, cy + 4.0)
                bars = m if bars is None else bars | m
            f.add(bars, 'ashe_steel', z=z + 0.3, flat=2, dim=dim, line=None, clean=False, tag='face' if worn else None)
            f.add(f.rect(x - 0.5, cy - r + 1, x + 1, cy - 1.0) & shell, trim, z=z + 0.1, flat=2, dim=dim, line=None)
            f.add(f.rect(x - 6.5, cy - 2.0, x + 7.0, cy - 1.0) & shell, trim, z=z + 0.1, flat=2, dim=dim, line=None)
            crest = f.ell(x + 0.5, cy - r - 1.5, 2.6, 3.4) & (f.Y < cy - r + 1)
        elif view == 'side':
            vis = f.rect(x + 2.0, cy - 1.0, x + r, cy + 4.0) & shell
            f.add(vis, sl, z=z + 0.2, flat=0 if not ember else 2, dim=dim, line=None, tag='face' if worn else None)
            for bx in (3.5, 6.5):
                f.add(f.rect(x + bx, cy - 1.0, x + bx + 1, cy + 4.0) & shell, 'ashe_steel', z=z + 0.3, flat=2, dim=dim, line=None,
                      clean=False, tag='face' if worn else None)
            f.add(f.rect(x + 1.0, cy - 2.0, x + r, cy - 1.0) & shell, trim, z=z + 0.1, flat=2, dim=dim, line=None)
            crest = f.poly([(x + 3, cy - r - 0.5), (x - 1, cy - r - 3), (x - 6, cy - r - 2), (x - r - 2.5, cy - 3.0),
                            (x - r + 0.5, cy - 2.0), (x - 4, cy - r + 1.5)])
        else:
            crest = (f.ell(x, cy - r - 0.5, 2.4, 3.2) & (f.Y < cy - r + 2)) | f.poly([(x - 1.6, cy - r + 1), (x + 1.6, cy - r + 1),
                                                                                    (x + 1.1, cy + 2.5), (x - 1.1, cy + 2.5)])
        f.add(crest, 'ashe_crimson', z=z + 0.4, rl=1.2, rs=1.6, dim=dim, line='hard')
        if glint and not dim:
            f.dot(x - 5, cy - 5, ('ashe_steel', 4), z=z + 0.5)


def _west(f):
    while not hasattr(f, 'flip') and hasattr(f, 'f'):
        f = f.f
    return bool(getattr(f, 'flip', False))


def _shell_planes(X, Y, t, x, cy, r, west=False):
    """26 Oct (asset gate, the helm hung at her back in the turn): the shell's lit upper-left plane
    and its dark lower-right, so the round helm never reads as a flat badge."""
    out = t.copy()
    d = ((X - x) * (0.55 if west else -0.55) - (Y - cy) * 0.85) / r       # the mirrored grid keeps the light at the upper left
    lit, dark = (d > 0.35) & (t >= 1), (d < -0.5) & (t >= 1)
    out[lit] = np.minimum(t[lit] + 1, 3)
    out[dark] = np.maximum(t[dark] - 1, 0)
    return out


def gauntlet(f, x, y, z, dim=0, trim='gold'):
    f.add(f.ell(x, y, 3.3, 3.3), 'ashe_steel', z=z, rl=1.4, rs=2.0, dim=dim, line='hard')
    f.add(f.ell(x, y - 2.6, 3.4, 1.4), trim, z=z + 0.05, flat=2, dim=dim, line='hard')


def pauldron(f, x, y, s, z, dim=0, trim='gold'):
    dome = f.ell(x, y, 5.8, 4.8) & (f.Y < y + 2.0)
    f.add(dome, 'ashe_steel', z=z, rl=1.8, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1))
    lame = f.ell(x + 0.6 * s, y + 2.4, 5.4, 2.6) & (f.Y > y + 1.4)
    f.add(lame, 'ashe_steel', z=z - 0.05, rl=1.2, rs=1.6, dim=dim, line='hard')
    f.add(f.ell(x + 0.6 * s, y + 2.4, 5.4, 2.6) & (f.Y > y + 2.9), trim, z=z - 0.04, flat=2, dim=dim, line=None)
    f.add(f.ell(x, y, 5.8, 4.8) & (f.Y >= y + 1.0) & (f.Y < y + 2.0), trim, z=z + 0.01, flat=2, dim=dim, line=None)


# ------------------------------------------------------------------------------------ hair, heads
def _locks(X, Y, t, hy, cx):
    out = t.copy()
    for k in (-5.0, -1.0, 3.5):
        m = (abs(X - cx - k - (Y - hy + 10) * 0.35) < 0.55) & (Y < hy - 3) & (Y > hy - 11)
        out[m & (t >= 2)] = 1
    r = ((X - cx + 2.5) / 6.5) ** 2 + ((Y - hy + 7.5) / 2.0) ** 2
    out[(r < 1) & (t == 2)] = 3
    r2 = ((X - cx - 6.5) / 2.6) ** 2 + ((Y - hy + 5.0) / 1.3) ** 2      # 26 Oct: a second sheen on the fringe, in sight when the blade crosses the crown
    out[(r2 < 1) & (t == 2)] = 3
    return out


def _back_locks(X, Y, t, x0, hy):
    out = t.copy()
    for k in (-5, 0, 5):
        m = (abs(X - x0 - k * (1 - (Y - hy + 10) / 26)) < 0.55) & (Y < hy + 8) & (Y > hy - 6)
        out[m & (t >= 2)] = 1
    return out


def head_south(f, P, x0, hy):
    f.add(f.ell(x0 - 8.6, hy + 1.5, 1.8, 2.6) | f.ell(x0 + 8.6, hy + 1.5, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy + 1.0, 8.2, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    cap = f.ell(x0, hy - 3.5, 10.6, 9.2) | f.ell(x0 - 9.2, hy + 2.5, 2.6, 6.0) | f.ell(x0 + 9.2, hy + 2.5, 2.6, 6.0)
    cap &= ~(f.ell(x0, hy + 3.0, 7.6, 6.6) & (f.Y > hy - 1.0))
    fringe = f.poly([(x0 - 9.5, hy - 6), (x0 - 8.0, hy + 0.5), (x0 - 6.0, hy - 2.5), (x0 - 3.0, hy - 0.5), (x0 - 1.0, hy - 3.5),
                     (x0 + 2.5, hy - 1.0), (x0 + 4.0, hy - 3.0), (x0 + 7.5, hy - 0.5), (x0 + 9.5, hy - 2.0), (x0 + 9.5, hy - 7)])
    tufts = f.poly([(x0 - 7, hy - 9), (x0 - 6.5, hy - 13.5), (x0 - 2, hy - 11.5)]) | \
        f.poly([(x0 - 1.5, hy - 11.5), (x0 + 3.5, hy - 15.0), (x0 + 2.5, hy - 11.5), (x0 + 7, hy - 12.5), (x0 + 6, hy - 8)])
    f.add(cap | fringe | tufts, 'ashe_hair', z=44, rl=1.8, rs=2.8, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _locks(X, Y, t, hy, x0))
    ey = hy + 0.5
    if P['face'] == 'shut' or P['blink']:
        f.detail(f.rect(x0 - 5, ey + 2, x0 - 3, ey + 3), EYE)
        f.detail(f.rect(x0 + 3, ey + 2, x0 + 5, ey + 3), EYE)
    else:
        eye(f, x0 - 5, ey, 3)
        eye(f, x0 + 3, ey, 3)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(x0 - 6, ey - 2 + lift, x0 - 2, ey - 1 + lift), ('ashe_hair', 1))
    f.detail(f.rect(x0 + 2, ey - 2 + lift, x0 + 6, ey - 1 + lift), ('ashe_hair', 1))
    f.detail(f.rect(x0 - 1, hy + 4, x0 + 1, hy + 5), ('skin', 3))
    f.detail(f.rect(x0, hy + 5, x0 + 2, hy + 6), ('skin', 1))
    f.detail(f.rect(x0 - 1, hy + 7, x0 + 1, hy + 8), ('skin', 0))
    f.detail(f.rect(x0 - 7, hy + 4, x0 - 5, hy + 5), ('blush', 2))
    f.detail(f.rect(x0 + 5, hy + 4, x0 + 7, hy + 5), ('blush', 2))


def head_north(f, P, x0, hy):
    f.add(f.ell(x0 - 8.6, hy + 1.5, 1.8, 2.6) | f.ell(x0 + 8.6, hy + 1.5, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
    back = f.ell(x0, hy - 1.5, 10.6, 10.2) | f.poly([(x0 - 9, hy + 3), (x0 + 9, hy + 3), (x0 + 7, hy + 9), (x0 + 3, hy + 7.5),
                                                     (x0, hy + 10), (x0 - 3, hy + 7.5), (x0 - 7, hy + 9)])
    back |= f.poly([(x0 - 7, hy - 9), (x0 - 6.5, hy - 13.5), (x0 - 2, hy - 11.5)]) | \
        f.poly([(x0 - 1.5, hy - 11.5), (x0 + 3.5, hy - 15.0), (x0 + 2.5, hy - 11.5), (x0 + 7, hy - 12.5), (x0 + 6, hy - 8)])
    f.add(back, 'ashe_hair', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _back_locks(X, Y, t, x0, hy))


def head_side(f, P, hx, hy):
    f.add(f.ell(hx + 2.0, hy + 1.0, 7.4, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(hx + 9.0, hy + 3.0, 1.5, 1.5), 'skin', z=40.5, rl=1, rs=1, line='hard')
    cap = f.ell(hx - 0.5, hy - 3.5, 10.2, 9.2) | f.ell(hx - 7.5, hy + 2.5, 3.6, 6.4)
    cap &= ~(f.ell(hx + 5.0, hy + 3.0, 6.2, 6.6) & (f.Y > hy - 2.0))
    fringe = f.poly([(hx + 1, hy - 8), (hx + 2.5, hy - 1.0), (hx + 4.5, hy - 3.5), (hx + 6.5, hy - 0.5), (hx + 8.5, hy - 3.0),
                     (hx + 10.0, hy - 2.0), (hx + 9.5, hy - 7)])
    tufts = f.poly([(hx - 7, hy - 8), (hx - 9.5, hy - 12.5), (hx - 3, hy - 11.5)]) | \
        f.poly([(hx - 3, hy - 11.5), (hx - 2, hy - 15.0), (hx + 3, hy - 12.0), (hx + 5.5, hy - 11), (hx + 2, hy - 8)])
    tail = f.poly([(hx - 9, hy - 2), (hx - 13.5 - P['lag'] * 0.5, hy + 4), (hx - 9.5, hy + 3.5), (hx - 11 - P['lag'] * 0.5, hy + 8),
                   (hx - 6, hy + 6)])
    f.add(cap | fringe | tufts | tail, 'ashe_hair', z=44, rl=1.8, rs=2.8, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _locks(X, Y, t, hy, hx - 1))
    f.add(f.ell(hx - 1.8, hy + 2.0, 1.7, 2.5), 'skin', z=45, rl=1, rs=1.2, line='hard')
    f.dot(hx - 1.8, hy + 2, ('skin', 1), z=45)
    ey = hy + 0.5
    if P['face'] == 'shut' or P['blink']:
        f.detail(f.rect(hx + 4.5, ey + 2, hx + 6.5, ey + 3), EYE)
    else:
        eye(f, hx + 4.5, ey, 3)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(hx + 3.5, ey - 2 + lift, hx + 7.5, ey - 1 + lift), ('ashe_hair', 1))
    f.detail(f.rect(hx + 6.5, hy + 7, hx + 8.5, hy + 8), ('skin', 0))
    f.detail(f.rect(hx + 3.5, hy + 4, hx + 5.5, hy + 5), ('blush', 2))


def head_3q(f, P, hx, hy, back):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW on the mirrored grid) for the turn
    in-betweens.  Front: the face turned a quarter from the profile toward the camera, both eyes
    (the far one near the cheek), the near ear under the hair, the swept cap and the short tail
    behind.  Back: the back of the head with the near ear and a sliver of cheek."""
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    tufts = f.poly([(hx - 7.5, hy - 8.5), (hx - 8.5, hy - 13.0), (hx - 2.5, hy - 11.5)]) | \
        f.poly([(hx - 2.0, hy - 11.5), (hx + 0.5, hy - 15.0), (hx + 4.0, hy - 12.0), (hx + 7.0, hy - 11.5), (hx + 4.0, hy - 8.0)])
    if back:
        f.add(f.ell(hx + 8.4, hy + 2.0, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(hx + 6.0, hy + 3.5, 3.6, 5.0), 'skin', z=39.5, rl=1, rs=1.6, line='hard')       # the cheek's edge
        hb = f.ell(hx - 0.5, hy - 1.5, 10.4, 10.2) | f.poly([(hx - 9, hy + 3), (hx + 7, hy + 3), (hx + 5, hy + 9), (hx + 1.5, hy + 7.5),
                                                              (hx - 1.5, hy + 10), (hx - 4.5, hy + 7.5), (hx - 8.5, hy + 9)])
        hb &= ~(f.ell(hx + 7.5, hy + 4.5, 3.0, 4.6) & (f.Y > hy + 0.5))
        f.add(hb | tufts, 'ashe_hair', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1),
              tonemap=lambda X, Y, t: _back_locks(X, Y, t, hx - 0.5, hy))
        return
    f.add(f.ell(hx + 1.5, hy + 1.0, 8.0, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    cap = f.ell(hx - 0.5, hy - 3.5, 10.4, 9.2) | f.ell(hx - 8.0, hy + 2.5, 3.2, 6.2)
    cap &= ~(f.ell(hx + 3.0, hy + 3.0, 7.0, 6.6) & (f.Y > hy - 1.0))
    fringe = f.poly([(hx - 4, hy - 7), (hx - 3.0, hy - 0.5), (hx - 0.5, hy - 3.0), (hx + 2.0, hy - 0.5), (hx + 4.0, hy - 3.5),
                     (hx + 6.5, hy - 1.0), (hx + 8.5, hy - 3.0), (hx + 10.0, hy - 2.0), (hx + 9.5, hy - 7)])
    tail = f.poly([(hx - 9, hy - 2), (hx - 12.5 - P['lag'] * 0.5, hy + 4), (hx - 9.5, hy + 3.5), (hx - 10.5 - P['lag'] * 0.5, hy + 7.5),
                   (hx - 6, hy + 6)])
    f.add(cap | fringe | tufts | tail, 'ashe_hair', z=44, rl=1.8, rs=2.8, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _locks(X, Y, t, hy, hx))
    f.add(f.ell(hx - 4.8, hy + 2.0, 1.6, 2.5), 'skin', z=45, rl=1, rs=1.2, line='hard')            # near ear
    f.dot(hx - 4.8, hy + 2, ('skin', 1), z=45)
    ey = hy + 0.5
    if P['face'] == 'shut' or P['blink']:
        f.detail(f.rect(hx - 0.5, ey + 2, hx + 1.5, ey + 3), EYE)
        f.detail(f.rect(hx + 5.5, ey + 2, hx + 7.5, ey + 3), EYE)
    else:
        eye(f, hx - 0.5, ey, 3)
        eye(f, hx + 5.5, ey, 3)
    f.detail(f.rect(hx - 1.5, ey - 2 + lift, hx + 2.5, ey - 1 + lift), ('ashe_hair', 1))
    f.detail(f.rect(hx + 4.5, ey - 2 + lift, hx + 8.0, ey - 1 + lift), ('ashe_hair', 1))
    f.detail(f.rect(hx + 3.5, hy + 4, hx + 5.5, hy + 5), ('skin', 3))
    f.detail(f.rect(hx + 4.5, hy + 5, hx + 6.5, hy + 6), ('skin', 1))
    f.detail(f.rect(hx + 3.0, hy + 7, hx + 5.0, hy + 8), ('skin', 0))
    f.detail(f.rect(hx - 2.5, hy + 4, hx - 0.5, hy + 5), ('blush', 2))
    f.detail(f.rect(hx + 7.5, hy + 4, hx + 8.5, hy + 5), ('blush', 2))


def _tab_fold(X, Y, t, x0, y0, y1):
    """The tabard's centre fold (a shaded trough) with lit cloth on its left (the light's) side and
    the right panel turning away into shade: three planes, not a flat card."""
    out = t.copy()
    out[(X > x0 - 4.5) & (X < x0 - 0.6) & (Y > y0) & (t >= 2)] = 3
    out[(X > x0 + 3.0) & (Y > y0) & (t >= 2)] = 1
    out[(abs(X - x0) < 0.55) & (Y > y0) & (Y < y1) & (t >= 1)] = 0
    return out


def _ridge(X, Y, t, x0, y0, y1):
    out = t.copy()
    out[(X > x0 - 1.5) & (X < x0 - 0.4) & (Y > y0) & (Y < y1) & (t >= 1)] = 3
    out[(X > x0 - 0.4) & (X < x0 + 0.6) & (Y > y0) & (Y < y1) & (t >= 2)] = 1
    return out


def _cape_folds(X, Y, t, x0, y0):
    out = t.copy()
    for k in (-5.5, 0.5, 6.5):
        m = (abs(X - x0 - k - (Y - y0) * 0.08 * np.sign(k + 0.01)) < 0.55) & (Y > y0 + 4) & (Y < y0 + 36)
        out[m & (t >= 1)] = np.maximum(out[m & (t >= 1)] - 1, 0)
    return out


# ------------------------------------------------------------------------------------ build
def helm_pos(P, sh3, head3):
    """Helm centre and the left hand's hold along the one path arm -> head (t 0..1)."""
    t = P['helm_t']
    a = np.array(HELM_ARM, float) + np.array([P['hipx'], -P['crouch'] - P['bob'], 0.0])
    h = np.array(head3, float) + np.array([0.0, 0.5, 0.0])
    mid = np.array(sh3, float) + np.array([9.0, 6.0, -8.0])
    if t <= 0.5:
        u = t / 0.5
        c = a + (mid - a) * u
        c[1] += 3.0 * math.sin(math.pi * u)
    else:
        u = (t - 0.5) / 0.5
        c = mid + (h - mid) * u
        c[1] += 3.0 * math.sin(math.pi * u)
    # hold: under the chin when carried, at the helm's left side when lifting
    hold0 = np.array([1.5, -5.5, 1.5])
    hold1 = np.array([0.5, -2.0, -9.5])
    k = min(1.0, t / 0.35)
    hold = hold0 + (hold1 - hold0) * k
    return tuple(c), tuple(c + hold)


def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    b, cr, lean = P['bob'], P['crouch'], P['lean']
    trim = trim_mat(P)
    ember = P['ember'] > 0.5
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 20.0 + P['breath'], 0.0)
    head3 = (sh3[0] + lean * 0.35, sh3[1] + 16.0, 0.0)
    off = (P['hipx'], -cr - b, 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    # ---------------------------------------------------------------- hands
    hR = add3(P['handR'] or REST_R, off)
    worn = P['helm_t'] >= 0.999
    helm3, hold3 = helm_pos(P, sh3, head3)
    if P['handL'] is not None:
        hL = add3(P['handL'], off)
    elif not worn:
        hL = hold3
    else:
        hL = add3((1.0, 26.5, -14.0), off)
    if P['two']:                        # both hands on the grip: left below the right
        d = nrm(P['sdir'] or REST_DIR)
        hL = tuple(np.array(hR) - d * 3.4)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    # ---------------------------------------------------------------- cape (behind)
    lag = P['lag']
    if side:
        cape = f.poly([(sx - 7, sy - 6), (sx - 1, sy - 6), (hx - 6, hy - 8), (hx - 8 - lag * 0.4, -8 + hy + 22),
                       (hx - 14.5 - lag, -8.5 + hy + 22 + abs(lag) * 0.3), (hx - 12.5 - lag * 0.5, hy - 8)])
        f.add(cape, 'ashe_crimson', z=1, rl=1.6, rs=2.8, vgrad=0.6, line='hard', deep=True)
    elif facing in ('S', 'SE', 'SW'):
        tw0 = turn.Warp(f, R, (sx + hx) / 2, 12.0, 9.0, 'S') if R.diag else None
        if tw0:
            tw0.__enter__()
        cape = f.poly([(sx - 11, sy - 5), (sx + 11, sy - 5), (hx + 15.5, -9 + hy + 22), (hx + 8, -7.5 + hy + 22), (hx, -8.5 + hy + 22),
                       (hx - 8, -7.5 + hy + 22), (hx - 15.5, -9 + hy + 22)])
        f.add(cape, 'ashe_crimson', z=1, rl=1.6, rs=3, vgrad=0.6, line='hard', deep=True)
        if tw0:
            tw0.__exit__(None, None, None)
    # ---------------------------------------------------------------- legs
    for lat, key in ((P['stance'], 'footR'), (-P['stance'], 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.5, lat)
        hp3 = add3(hip3, (0.0, 0.0, lat * 0.95))
        up, lo, kn3 = R.limb(hp3, ank3, 8.2, 8.0, 4.4, 4.0, 3.8, (1.0, 0.0, 0.1 * np.sign(lat)))
        far = R.far(lat)
        dim = 1 if far else 0
        z = 9 + 0.1 * R.d(foot3)
        f.add(up | lo, 'ashe_steel', z=z, rl=1.6, rs=2.4, dim=dim, line='hard')
        kx, ky = R.p(add3(kn3, (1.0, 0, 0)))
        cop = f.ell(kx, ky, 3.4 if not side else 2.4, 3.0)
        f.add(cop, 'ashe_steel', z=z + 0.2, rl=1.2, rs=1.6, dim=dim, line='hard')
        f.add(cop & (f.Y > ky + 1.8), trim, z=z + 0.25, flat=2, dim=dim, line=None)
        fx, fy = R.p(foot3)
        if R.diag:
            surf.boot_3q(f, R, foot3, 'leather', z + 1, dim=dim, cuff=False, shade=dict(rl=1.6))
            f.add(f.rect(fx - 3.6, fy - 8, fx + 3.6, fy - 6), trim, z=z + 1.1, flat=1, dim=dim, line='soft')
        elif side:
            boot_side(f, fx, fy, 'leather', z=z + 1, dim=dim)
            f.add(f.rect(fx - 3.4, fy - 8, fx + 2.6, fy - 6), trim, z=z + 1.1, flat=1, dim=dim, line='soft')
        else:
            boot_front(f, fx, fy, 'leather', z=z + 1, dim=dim)
            f.add(f.rect(fx - 3.8, fy - 8, fx + 3.8, fy - 6), trim, z=z + 1.1, flat=1, dim=dim, line='soft')
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    # ---------------------------------------------------------------- torso
    if side:
        body = f.ell(sx + 1.0, sy + 5, 9.0, 11) | f.poly([(hx - 7.5, hy - 5), (sx - 7.5, sy + 1), (sx + 9.0, sy + 1), (hx + 8.5, hy - 5)])
        body &= f.Y < hy - 4
        f.add(body, 'ashe_steel', z=20, rl=2.2, rs=3.6, vgrad=0.3, line='hard')
        for i, y in enumerate((hy - 5, hy - 2)):
            lame = f.rect(hx - 8 + i, y, hx + 9.5 - i, y + 3) & f.ell(hx + 0.8, y + 1.5, 9.4 - i, 4)
            f.add(lame, 'ashe_steel', z=22 + i * 0.1, rl=1, rs=1.6, line='hard')
            f.add(lame & (f.Y >= y + 2), trim, z=22.05 + i * 0.1, flat=1, line=None)
        f.add(f.rect(hx - 8, hy - 8, hx + 9.5, hy - 5), 'leather', z=24, rl=1, rs=1.2, line='soft')
        f.add(f.rect(hx + 7, hy - 9, hx + 10, hy - 4), trim, z=25, rl=1, rs=1.4, line='hard')
        f.add(f.ell(sx + 1, sy - 5.5, 6.5, 2.6) & (f.Y > sy - 6), trim, z=21, flat=2, line='hard')
        tab = f.poly([(hx + 4.5, hy - 5), (hx + 9.0, hy - 5), (hx + 10.5 + lag * 0.2, hy + 12), (hx + 5.5 + lag * 0.2, hy + 12.5)])
        f.add(tab, 'ashe_crimson', z=26, rl=1.4, rs=2.2, vgrad=0.4, line='hard')
        f.add(f.rect(hx + 5, hy + 10, hx + 11.5, hy + 11) & tab, trim, z=26.1, flat=1, line=None)
        if ember:
            f.detail(f.seg(sx + 7.5, sy + 1, hx + 7, hy - 6) & body, ('ashe_ember', 3), z=20.5)
    else:
        back = R.back
        vf = ('N' if back else 'S') if R.diag else facing      # turn in-betweens: the S or N drawing turned onto the body
        tw = turn.Warp(f, R, (sx + hx) / 2, 12.0, 9.0, vf) if R.diag else None
        if tw:
            tw.__enter__()
        body = f.ell(sx, sy + 5, 11.5, 11) | f.rect(sx - 10.5, sy + 1, sx + 10.5, sy + 4) | \
            f.poly([(sx - 10.5, sy + 2), (sx + 10.5, sy + 2), (hx + 10.5, hy - 5), (hx - 10.5, hy - 5)])
        body &= f.Y < hy - 4
        f.add(body, 'ashe_steel', z=20, rl=2.2, rs=3.6, vgrad=0.3, line='hard',
              tonemap=None if back else (lambda X, Y, t: _ridge(X, Y, t, (sx + hx) / 2, sy - 3, hy - 8)))
        f.add(f.ell(sx, sy - 5, 7.5, 3.0) & (f.Y > sy - 5.5), trim, z=21, flat=2, line='hard')
        for i, y in enumerate((hy - 5, hy - 2)):
            lame = f.rect(hx - 11 + i, y, hx + 11 - i, y + 3) & f.ell(hx, y + 1.5, 11.5 - i, 4)
            f.add(lame, 'ashe_steel', z=22 + i * 0.1, rl=1, rs=1.6, line='hard')
            f.add(lame & (f.Y >= y + 2), trim, z=22.05 + i * 0.1, flat=1, line=None)
        f.add(f.rect(hx - 11, hy - 8, hx + 11, hy - 5), 'leather', z=24, rl=1, rs=1.2, line='soft')
        if not back:
            f.add(f.rect(hx - 2, hy - 9, hx + 2, hy - 4), trim, z=25, rl=1, rs=1.4, line='hard')
            tab = f.poly([(hx - 5, hy - 5), (hx + 5, hy - 5), (hx + 6, hy + 12), (hx + 3, hy + 13), (hx, hy + 11.5), (hx - 3, hy + 13),
                          (hx - 6, hy + 12)])
            f.add(tab, 'ashe_crimson', z=26, rl=1.6, rs=2.6, vgrad=0.4, line='hard', cast=(0, 1, 1),
                  tonemap=lambda X, Y, t: _tab_fold(X, Y, t, hx + 1.5, hy - 2, hy + 9))
            f.add(f.rect(hx - 5, hy + 10, hx + 6, hy + 11) & tab, trim, z=26.1, flat=1, line=None)
            if ember:
                f.detail(f.seg(sx - 0.5, sy - 3, hx - 0.5, hy - 9) & body, ('ashe_ember', 3), z=20.5)
                for s_ in (-1, 1):
                    f.detail(f.seg(sx + 6 * s_, sy + 2, hx + 8 * s_, hy - 8) & body, ('ashe_ember', 2), z=20.5)
        else:
            cape = f.poly([(sx - 11.5, sy - 6), (sx + 11.5, sy - 6), (hx + 13.5, hy - 8), (hx + 14.5 + lag * 0.3, hy + 13), (hx + 7, hy + 14.5),
                           (hx, hy + 13.5), (hx - 7, hy + 14.5), (hx - 14.5 + lag * 0.3, hy + 13), (hx - 13.5, hy - 8)])
            f.add(cape, 'ashe_crimson', z=28, rl=1.8, rs=3.2, vgrad=0.6, line='hard', deep=True,
                  tonemap=lambda X, Y, t: _cape_folds(X, Y, t, sx, sy))
            f.add(f.rect(hx - 14.5, hy + 9, hx + 14.5, hy + 10.5) & cape, trim, z=28.1, flat=1, line=None)
        if tw:
            tw.__exit__(None, None, None)
    # ---------------------------------------------------------------- arms, sword, helm
    sdir = P['sdir'] or REST_DIR
    out = {}
    sRj, sLj, _ = shoulders(sh3, hR, hL, SHW, sum(ARM), P['twist'])
    for key, hh, lat, shp in (('R', hR, 1, sRj), ('L', hL, -1, sLj)):
        pole = P['pole' + key] or (-0.6, -1.0, 0.45 * lat)
        up, lo, el3 = R.limb(shp, hh, ARM[0], ARM[1], 3.6, 3.2, 3.0, pole)
        far = R.far(lat)
        dd = R.d(hh)
        if dd >= -3.5:
            zl = 30.0 + 0.05 * dd
        else:
            zl = 5.0 + 0.05 * dd
        if hh[1] > 50 and dd > -4:
            zl = 46.0
        zu = zl if R.d(el3) >= -3.5 else 5.0
        if R.back:                         # the cape (28) hides what is in front of him, not what is behind
            zl = 5.0 if dd < -3.0 else (46.0 if hh[1] > 50 else 30.0)
            zu = 5.0 if R.d(el3) < -3.0 else 29.0
        if far and hh[1] < 48:
            zu = zl = 4.5 if facing in 'EW' else zl
        out[key] = (shp, hh, up, lo, el3, far, zu, zl)
    # helm (not yet on the head)
    hz = None
    if not worn:
        dd = R.d(helm3)
        if helm3[1] > 50:
            hz = 47.5
        elif facing in 'EW' and R.far(-1) and dd < -6:
            hz = 3.0
        else:
            hz = 31.0
        view = {'S': 'front', 'N': 'back'}.get(facing, 'back' if (R.diag and R.back) else 'side')
        hx3, hy3 = R.p(helm3)
        if R.diag and R.back and R.d(helm3) < -2:
            hz = 3.0
        helm(f, hx3, hy3, hz, view=view, dim=1 if hz < 10 else 0, trim=trim, ember=ember, glint=hz > 10)
    for key in ('R', 'L'):
        shp, hh, up, lo, el3, far, zu, zl = out[key]
        dim = 1 if far else 0
        f.add(up, 'ashe_steel', z=zu, rl=1.4, rs=2.2, dim=dim, line='hard', cast=(1, 1, 1) if not far else None)
        f.add(lo, 'ashe_steel', z=zl, rl=1.4, rs=2.2, dim=dim, line='hard', cast=(1, 1, 1) if not far else None)
        ex, ey = R.p(el3)
        f.add(f.ell(ex, ey, 2.4, 2.4), 'ashe_steel', z=max(zu, zl) + 0.05, rl=1, rs=1.2, dim=dim, line='hard')
        f.dot(ex - 1, ey - 1, (trim, 3 if not dim else 2), z=max(zu, zl) + 0.05)
        hx2, hy2 = R.p(hh)
        gz = zl + 0.8
        if key == 'L' and not worn and P['handL'] is None and hz is not None and not P['two']:
            gz = hz + 1.0 if hz > 10 else 3.5          # cupping the helm's chin, in front of it
        if key == 'R' and P['sword'] == 'hand':
            sz = zl + 0.4
            if P['two']:
                sz = max(zl, out['L'][7]) + 0.4
            tip3 = np.array(hh) + nrm(sdir) * 28.0
            if tip3[1] > 50 and R.d(hh) > 3.0 and R.d(tuple(tip3)) > 0:     # raised in front of the face
                sz = 46.5
            if not side and hh[1] > 45 and R.d(tuple(tip3)) < R.d(hh) - 6:      # blade back over the shoulder
                sz = 38.5
            tip = sword(f, R, hh, sdir, sz, dim=dim if zl < 10 else 0, ember=ember)
            f.anchor('sword_tip', *tip)
            gz = sz + 0.5
        if key == 'L' and P['two']:
            gz = max(zl, out['R'][7]) + 1.0
        gauntlet(f, hx2, hy2, gz, dim=dim if gz < 10 else 0, trim=trim)
        px, py = R.p(shp)
        f.add(f.ell(px, py - 0.5, 5.8, 4.8) & (f.Y < py + 1.5), 'ashe_steel', z=34 if not (far and facing in 'EW') else 4.8,
              rl=1.8, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1))
        pauldron(f, px, py - 1.5, lat_sign(key, facing), 34 if not (far and facing in 'EW') else 4.9, dim=dim, trim=trim)
    # collar
    cx_, cy_ = R.p(add3(sh3, (0.5, -5.5, 0)))
    f.add(f.ell(cx_ + (0.5 if side else 0), sy - 5.5, 7.6 if not side else 6.4, 2.8), 'ashe_crimson', z=36, rl=1.2, rs=1.8,
          line='hard', cast=(0, 1, 1))
    # ---------------------------------------------------------------- head (or the helm on it)
    hx3, hy3 = R.p(head3)
    if worn:
        # 26 Oct (no face from behind): turned away (NE, NW) the worn helm shows its plain rear, no visor
        view = {'S': 'front', 'N': 'back'}.get(facing, 'back' if (R.diag and R.back) else 'side')
        helm(f, hx3 + (1.5 if side else 0), hy3 + 0.5, 44, view=view, trim=trim, ember=ember, worn=True)
        if facing == 'N':     # hair at the nape below the helm
            f.add(f.poly([(hx3 - 5, hy3 + 8), (hx3 + 5, hy3 + 8), (hx3 + 3, hy3 + 11), (hx3, hy3 + 10), (hx3 - 3, hy3 + 11)]),
                  'ashe_hair', z=43.5, rl=1, rs=1.4, line='hard')
    elif R.diag:
        head_3q(f, P, hx3, hy3, R.back)
    elif facing == 'S':
        head_south(f, P, hx3, hy3)
    elif facing == 'N':
        head_north(f, P, hx3, hy3)
    else:
        head_side(f, P, hx3 + 1.0, hy3)


def lat_sign(key, facing):
    s = 1 if key == 'R' else -1
    if facing in ('S', 'SE', 'SW'):
        return -s
    if facing in ('N', 'NE', 'NW'):
        return s
    return 1


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f

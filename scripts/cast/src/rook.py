"""Rook: mature human orbital salvager.  Thick dark hair, light stubble, a worn cream pressure suit
with dark padded panels and orange trim, an orange neck seal, dark gloves and heavy boots.
Exactly one of each item, always in the same place:
  - the pulse carbine: right hand on the grip, left hand on the fore-end (a 3D gun: grip point
    and direction in body space; the left hand is solved onto its fore-end);
  - the helmet: ONE helmet, clipped at the RIGHT hip (helmet='hip'), carried in the right hand
    ('hand') or worn ('head', Orbital Rig's powered state; an open faceplate keeps the face);
  - the twin-thruster backpack: two orange tanks on the back, each ending in an attached nozzle.
    Thruster Vault's exhaust (thrust 0..1) is drawn from those two nozzle bells and nowhere
    else; anchors nozzle_R and nozzle_L.  No disc, no tether.
Orbital Rig's two turrets are separate entities (out/rook/fx/turret_<F>.png), never body parts.

Pass 3: pose-driven on parts.Rig; torso, pack and head of the approved static design ride the
projected hip / shoulder / head through nix.Sh.  Tags: carbine, helmet, pack, exhaust."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, EYE, Rig, FLIP
import turn
import palette  # noqa: F401
import anim
from nix import Sh, skel, legs, add3, nrm

ID = 'rook'
NAME = 'Rook'
BAND = (70, 82)

mat('rk_suit',   ['#6A5E5A', '#A69584', '#D6C9B0', '#F2EAD8'])
mat('rk_orange', ['#6A2810', '#B44A16', '#EE7A22', '#FFAE5A', '#FFE0B0'])
mat('rk_pad',    ['#14141C', '#22222E', '#33344A', '#4C4E66'])
mat('rk_hair',   ['#120E16', '#201822', '#322632', '#4C3A46'])
mat('rk_stub',   ['#4A2C2C', '#76483E', '#9A6A54', '#B2846A'])
mat('rk_visor',  ['#0C1020', '#18223A', '#2A3A58', '#5A7498', '#CFE2F2'])
mat('rk_flame',  ['#B44A16', '#EE7A22', '#FFAE5A', '#FFE0B0', '#FFF8E8'])

SHW = 11.5
REST_R = (3.0, 31.0, 5.0)                 # grip hand
GUN = (0.62, -0.2, -0.76)                 # low ready: forward, a little down, across to his left
HELM_HIP = (-6.5, -5.5, 14.0)             # helmet clip at the right hip (relative to the hip)


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0,
             footR=(2.0, 0.0), footL=(-2.5, 0.0), stance=5.5,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             gun='hands', gdir=GUN, gpos=None, fore=4.5, helmet='hip', thrust=0.0, flash=False,
             lag=0.0, blink=False, brow=0, face=None)
    p.update(k)
    return p


# ------------------------------------------------------------------------------------ gear
def carbine(f, R, g3, d3, z, dim=0):
    """Pulse carbine: grip at g3, barrel along d3 (body space).  Drawn in the gun's own screen
    frame, foreshortened along its axis.  Returns (fore-end 3D point, muzzle screen point)."""
    d3 = nrm(d3)
    gx, gy = R.p(g3)
    ex, ey = R.p(add3(g3, tuple(d3)))
    ux, uy = ex - gx, ey - gy
    fs = max(0.35, math.hypot(ux, uy))
    ux, uy = ux / fs, uy / fs
    vx, vy = (-uy, ux) if ux >= 0 else (uy, -ux)          # 'down' across the gun
    k = 1.2

    def P(a, b=0.0):
        return gx + (ux * a * fs + vx * b) * k, gy + (uy * a * fs + vy * b) * k
    with f.tagging('carbine'):
        s0, s1 = P(-8.0, -0.6), P(-2.0, -1.4)
        f.add(f.cap(*s0, *s1, 2.6, 2.1), 'rk_pad', z=z, rl=1, rs=1.4, dim=dim, line='hard')
        b0, b1 = P(-2.5, -1.8), P(11.0, -1.6)
        body = f.cap(*b0, *b1, 3.4, 3.0)
        f.add(body, 'rk_suit', z=z + 0.1, rl=1.2, rs=1.8, dim=dim, line='hard')
        st0, st1 = P(0.5, -3.4), P(9.0, -3.2)
        f.add(f.cap(*st0, *st1, 1.0) & body, 'rk_orange', z=z + 0.15, flat=2, dim=dim, line=None)
        m0, m1 = P(3.5, 0.5), P(4.2, 4.2)
        f.add(f.cap(*m0, *m1, 1.8), 'rk_pad', z=z + 0.05, rl=1, rs=1.2, dim=dim, line='hard')
        g0, g1 = P(0.0, 0.4), P(-0.8, 3.6)
        f.add(f.cap(*g0, *g1, 1.6), 'rk_pad', z=z + 0.05, rl=1, rs=1.2, dim=dim, line='hard')
        r0, r1 = P(11.0, -1.8), P(18.0, -1.8)
        f.add(f.cap(*r0, *r1, 1.5), 'gunmetal', z=z + 0.12, rl=1, rs=1.2, dim=dim, line='hard')
        pr = P(13.0, -1.8)
        f.add(f.ell(pr[0], pr[1], 1.8, 2.1), 'rk_orange', z=z + 0.13, rl=1, rs=1.2, dim=dim, line='hard')
    mz = P(18.8, -1.8)
    f.anchor('muzzle', *mz)
    return mz


def flash(f, x, y, z, ux, uy):
    """Muzzle pulse: a short orange-white star at the muzzle (one drawing)."""
    m = f.poly([(x - uy * 3, y + ux * 3), (x + ux * 7, y + uy * 7), (x + uy * 3, y - ux * 3)]) | f.ell(x + ux, y + uy, 2.6, 2.6)
    f.add(m, 'rk_flame', z=z, flat=2, line=None, clean=False, tag='carbine')
    f.add(f.ell(x + ux, y + uy, 1.4, 1.4), 'rk_flame', z=z + 0.01, flat=4, line=None, clean=False, tag='carbine')


def helmet(f, x, y, z, dim=0, visor_dir=0, r=7.6):
    """The helmet off the head, at head size: an orange shell with a cream crest stripe, a big
    dark faceplate inside a padded rim, and the dark neck ring at its base (where the clip
    strap holds it).  visor_dir: 0 faceplate toward the viewer, +1 toward +x, None away."""
    with f.tagging('helmet'):
        shell = f.ell(x, y, r, r * 0.96)
        f.add(shell, 'rk_orange', z=z, rl=1.8, rs=2.8, dim=dim, line='hard', cast=(1, 1, 1))
        f.add(f.rect(x - 1.0, y - r, x + 1.0, y - r * 0.4) & shell, 'rk_suit', z=z + 0.05, rl=1, rs=1, dim=dim, line=None)
        ring = f.ell(x, y + r * 0.78, r * 0.62, r * 0.26)
        f.add(ring, 'rk_pad', z=z + 0.06, rl=1, rs=1.2, dim=dim, line='hard')
        if visor_dir is not None:
            if visor_dir == 0:
                rim = f.ell(x, y + 0.6, r * 0.74, r * 0.62)
                vis = f.ell(x, y + 0.6, r * 0.62, r * 0.5)
            else:
                rim = f.ell(x + r * 0.42 * visor_dir, y + 0.4, r * 0.5, r * 0.64) & shell
                vis = f.ell(x + r * 0.48 * visor_dir, y + 0.4, r * 0.38, r * 0.52) & shell
            f.add(rim, 'rk_pad', z=z + 0.08, rl=1, rs=1.2, dim=dim, line='hard')
            f.add(vis, 'rk_visor', z=z + 0.1, rl=1.6, rs=1.8, tl=0.3, dim=dim, line=None)
            gx = x + (r * 0.3 * visor_dir if visor_dir else -r * 0.32)
            f.detail(f.seg(gx - 1, y - 1.5, gx + 0.5, y - 3), ('rk_visor', 4), z=z + 0.1)


def helmet_worn(f, P, hy, facing):
    """The same helmet on the head: shell over the hair, an open faceplate (visor raised as a
    dark band over the brow), so the face stays readable."""
    with f.tagging('helmet'):
        if facing == 'S':
            shell = f.ell(0, hy - 1.5, 11.0, 11.0)
            hole = f.ell(0, hy + 3.0, 6.8, 6.6) | f.rect(-6.8, hy + 3.0, 6.8, hy + 12)
            band = f.ell(0, hy - 2.6, 7.6, 3.2) & ~f.ell(0, hy + 3.0, 6.8, 6.6)
        elif facing == 'N':
            shell = f.ell(0, hy - 1.5, 11.0, 11.0)
            hole = f.rect(-20, hy + 7.5, 20, hy + 20)
            band = None
        else:
            shell = f.ell(0.6, hy - 1.5, 10.6, 11.0)
            hole = f.ell(6.2, hy + 3.4, 5.4, 6.4) | f.rect(3.0, hy + 4.0, 12, hy + 12)
            band = f.ell(7.6, hy - 2.4, 3.6, 3.0) & ~f.ell(6.2, hy + 3.4, 5.4, 6.4)
        sm = shell & ~hole
        f.add(sm, 'rk_orange', z=46, rl=1.8, rs=2.8, line='hard', cast=(0, 1, 1))
        crest = f.rect(-1.0, hy - 13, 1.0, hy - 4) if facing in 'SN' else f.rect(-4, hy - 12.8, 3, hy - 10.6)
        f.add(crest & sm, 'rk_suit', z=46.1, rl=1, rs=1, line=None)
        if band is not None:
            f.add(band & sm, 'rk_visor', z=46.2, rl=1, rs=1.4, line='soft')
            bx = -3 if facing == 'S' else 6
            f.dot(bx, hy - 3, ('rk_visor', 4), z=46.2)


def tank(f, x, top, bot, z, dim=0, w=2.8):
    """One thruster unit: an orange tank with a dark band and a gunmetal cap, the nozzle bell
    attached at its bottom.  Returns the bell's mouth (x, y)."""
    with f.tagging('pack'):
        t = f.cap(x, top + w, x, bot - 1.5, w)
        f.add(t, 'rk_orange', z=z, rl=1.6, rs=2.0, tl=0.3, ts=0.3, dim=dim, line='hard')
        f.add(f.rect(x - w - 1, top + 7, x + w + 1, top + 8.5) & t, 'rk_pad', z=z + 0.05, flat=1, line=None, dim=dim)
        f.add(f.ell(x, top + 1.6, w - 0.6, 1.8), 'gunmetal', z=z + 0.06, rl=1, rs=1.2, dim=dim, line='hard')
        bell = f.poly([(x - 1.8, bot - 2), (x + 1.8, bot - 2), (x + 3.0, bot + 3.0), (x - 3.0, bot + 3.0)])
        f.add(bell, 'gunmetal', z=z + 0.08, rl=1.2, rs=1.6, dim=dim, line='hard')
        f.add(f.rect(x - 2.2, bot + 2.0, x + 2.2, bot + 3.0) & bell, 'rk_pad', z=z + 0.09, flat=0, line=None)
    return x, bot + 3.0


def exhaust(f, x, y, z, k, slant=0.0):
    """Thruster plume from a nozzle mouth (x, y) downward (slant leans it back): a hot core in a
    flame tongue; k 0..1 sets its length."""
    if k <= 0.02:
        return
    L = 4 + 16 * k
    w = 2.6 + 1.2 * k
    tip = (x + slant * L, y + L)
    with f.tagging('exhaust'):
        outer = f.poly([(x - w, y), (x + w, y), (x + w * 0.6 + slant * L * 0.5, y + L * 0.55), tip,
                        (x - w * 0.6 + slant * L * 0.5, y + L * 0.55)])
        f.add(outer, 'rk_flame', z=z, flat=1, line=None, clean=False)
        inner = f.poly([(x - w * 0.55, y), (x + w * 0.55, y), (x + slant * L * 0.6, y + L * 0.65)])
        f.add(inner, 'rk_flame', z=z + 0.01, flat=3, line=None, clean=False)
        f.add(f.rect(x - w * 0.5, y, x + w * 0.5, y + 1.2), 'rk_flame', z=z + 0.02, flat=4, line=None, clean=False)


# ------------------------------------------------------------------------------------ body
def gloved_hand(f, x, y, z, dim=0, r=2.9):
    f.add(f.ell(x, y, r, r), 'rk_pad', z=z, rl=1.4, rs=2.0, dim=dim, line='hard')


def suit_arm(f, R, sh3, h3, pole, z, dim):
    up, lo, el3 = R.limb(sh3, h3, 8.6, 8.4, 3.9, 3.5, 3.2, pole)
    f.add(up, 'rk_suit', z=z, rl=1.6, rs=2.6, dim=dim, line='hard', cast=(1, 1, 1))
    f.add(lo, 'rk_suit', z=z + 0.02, rl=1.6, rs=2.6, dim=dim, line='hard', cast=(1, 1, 1))
    ex, ey = R.p(el3)
    f.add(f.ell(ex, ey, 2.8, 2.6), 'rk_pad', z=z + 0.05, rl=1, rs=1.4, dim=dim, line='soft')
    hx, hy = R.p(h3)
    cx, cy = hx + (ex - hx) * 0.28, hy + (ey - hy) * 0.28
    f.add(f.ell(cx, cy, 3.2, 2.6), 'rk_orange', z=z + 0.06, rl=1, rs=1.4, dim=dim, line='soft')
    return el3


def shoulder_pad(f, x, y, z, w=5.0, dim=0):
    m = f.ell(x, y, w, 4.0) & (f.Y < y + 2.4)
    f.add(m, 'rk_pad', z=z, rl=1.6, rs=2.4, dim=dim, line='hard', cast=(0, 1, 1))


def _crotch(X, Y, t, b):
    out = t.copy()
    out[(abs(X) < 0.6) & (Y > -19 + b)] = 0
    # 26 Oct (asset gate): the seat in three planes, lit on its left, shaded on its right
    lit, dark = (X < -4.5) & (Y < -22.5 + b) & (out >= 1), ((X > 5.0) | (Y > -22.0 + b)) & (out >= 1)
    out[lit] = np.minimum(out[lit] + 1, 3)
    out[dark] = np.maximum(out[dark] - 1, 0)
    return out


def _wear(X, Y, t, marks):
    out = t.copy()
    for x0, y0, L in marks:
        m = (abs(Y - y0) < 0.6) & (X >= x0) & (X < x0 + L)
        out[m & (t >= 2)] = 1
    return out


def build(f, facing, P):
    R = Rig(f, facing)
    R.body_half = 12.0
    S = skel(R, P)
    T, b, ub = S['T'], S['b'], S['ub']
    side = R.side
    f.anchor('origin', 0.0, 0.0)
    th = P['thrust']
    # -------------------------------------------------- legs
    L = legs(f, R, P, S, 'rk_suit', 'rk_pad', r=(5.0, 4.7, 4.4), toe=2.0)
    for s, lg in L.items():
        kx, ky = lg['kn']
        d = 1 if lg['far'] else 0
        f.add(f.ell(kx + (1.4 if side else 0), ky + 0.5, 2.8 if side else 4.0, 3.0), 'rk_pad', z=lg['z'] + 0.5, rl=1, rs=1.6,
              dim=d, line='soft')
        fx, fy = lg['fx'], lg['fy']
        ox = 0.6 if side else 0
        f.add(f.rect(fx + ox - 4.4, fy - 9.5, fx + ox + 4.6, fy - 7) & f.ell(fx + ox, fy - 8, 4.8, 3), 'rk_orange', z=lg['z'] + 1.6,
              flat=1, line='soft', dim=d)
    # contract v2 turn in-betweens: the S or N pack and torso turned onto the body
    vf = ('N' if R.back else 'S') if R.diag else facing
    tw_ = turn.Warp(f, R, (S['sx'] + S['hx']) / 2, 11.5, 8.5, vf) if R.diag else None
    if tw_:
        tw_.__enter__()
    # -------------------------------------------------- pack (back) and its nozzles
    noz = {}
    if vf == 'S':
        for s, lat in ((-1, 1), (1, -1)):
            noz[lat] = tank(T, 10.0 * s, -58 + ub, -32 + ub, z=1, w=2.6)
        slant = 0.0
    elif vf == 'N':
        slant = 0.0
    else:
        noz[-1 if facing == 'E' else 1] = tank(T, -10.6, -57 + ub, -32 + ub, z=1, dim=1, w=2.7)
        with f.tagging('pack'):
            T.add(T.poly([(-8.5, -50 + ub), (-4, -50 + ub), (-4, -32 + ub), (-9.5, -32 + ub)]), 'rk_pad', z=1.5, rl=1.4, rs=2.2,
                  line='hard')
        noz[1 if facing == 'E' else -1] = tank(T, -9.6, -55 + ub, -30 + ub, z=2, w=2.9)
        slant = -0.3 - 0.06 * P['lean']
    if side and not R.diag:
        T.add(T.ell(-0.5, -23 + b, 8.8, 4.2), 'rk_suit', z=19, rl=1.8, rs=2.8, line='hard')
    else:
        T.add(T.rect(-11, -27 + b, 11, -21 + b) | T.ell(0, -21.5 + b, 11, 3.5), 'rk_suit', z=13, rl=2.0, rs=3.2, vgrad=0.3,
              line='hard', tonemap=lambda X, Y, t: _crotch(X, Y, t, b))
    # -------------------------------------------------- torso
    if vf == 'S':
        torso = T.ell(0, -37 + ub, 12.5, 10.5) | T.rect(-12, -40 + ub, 12, -26 + b)
        T.add(torso, 'rk_suit', z=20, rl=2.0, rs=3.6, vgrad=0.3, line='hard',
              tonemap=lambda X, Y, t: _wear(X, Y, t, [(-8, -33 + b, 3), (6, -38 + ub, 2)]))
        T.add(T.poly([(-10, -45 + ub), (10, -45 + ub), (9.5, -40 + ub), (3, -38 + ub), (-3, -38 + ub), (-9.5, -40 + ub)]) & torso,
              'rk_pad', z=21, rl=1.4, rs=2.6, line='soft')
        T.add(T.rect(-9, -38 + ub, -6.5, -29 + b) & torso, 'rk_orange', z=21.5, rl=1, rs=1.6, line='soft')
        T.add(T.rect(6.5, -38 + ub, 9, -29 + b) & torso, 'rk_orange', z=21.5, rl=1, rs=1.6, line='soft')
        T.add(T.rect(-12, -29 + b, 12, -26 + b), 'rk_pad', z=22, rl=1, rs=1.2, line='soft')
        T.add(T.rect(-1.5, -30 + b, 1.5, -25 + b), 'brass', z=22.5, rl=1, rs=1.4, line='hard')
        T.add(T.ell(0, -46 + ub, 7.6, 3.4), 'rk_orange', z=26, rl=1.6, rs=2.2, line='hard', cast=(0, 1, 1))
    elif vf == 'N':
        torso = T.ell(0, -37 + ub, 12.5, 10.5) | T.rect(-12, -40 + ub, 12, -26 + b)
        T.add(torso, 'rk_suit', z=20, rl=2.0, rs=3.6, vgrad=0.3, line='hard',
              tonemap=lambda X, Y, t: _wear(X, Y, t, [(-7, -30 + b, 3)]))
        T.add(T.rect(-12, -29 + b, 12, -26 + b), 'rk_pad', z=22, rl=1, rs=1.2, line='soft')
        with f.tagging('pack'):
            T.add(T.poly([(-9, -50 + ub), (9, -50 + ub), (10, -31 + ub), (-10, -31 + ub)]), 'rk_pad', z=46, rl=1.6, rs=2.6,
                  line='hard', cast=(1, 1, 1))
            for s, lat in ((1, 1), (-1, -1)):
                noz[lat] = tank(T, 5.4 * s, -55 + ub, -30 + ub, z=47)
            T.add(T.rect(-1.2, -47 + ub, 1.2, -34 + ub), 'gunmetal', z=47.5, rl=1, rs=1.2, line='hard')
            T.dot(0, -45 + ub, ('rk_orange', 4))
        T.add(T.ell(0, -46 + ub, 7.6, 3.4), 'rk_orange', z=26, rl=1.6, rs=2.2, line='hard')
    else:
        torso = T.ell(0.0, -37 + ub, 9.8, 10.5) | T.rect(-9.4, -40 + ub, 9.6, -26 + b)
        T.add(torso, 'rk_suit', z=20, rl=2.0, rs=3.6, vgrad=0.3, line='hard',
              tonemap=lambda X, Y, t: _wear(X, Y, t, [(-6, -33 + b, 3)]))
        T.add(T.poly([(-8, -45 + ub), (8, -45 + ub), (8.6, -39 + ub), (-8.6, -39 + ub)]) & torso, 'rk_pad', z=21, rl=1.4, rs=2.4,
              line='soft')
        T.add(T.rect(-8.8, -29 + b, 9.2, -26 + b), 'rk_pad', z=22, rl=1, rs=1.2, line='soft')
        T.add(T.rect(7.2, -30 + b, 9.6, -25 + b), 'brass', z=22.5, rl=1, rs=1.4, line='hard')
        T.add(T.poly([(-3.0, -47 + ub), (0.0, -47 + ub), (3.5, -38 + ub), (0.5, -37 + ub)]), 'rk_pad', z=23, flat=1, line='soft',
              tag='pack')
        T.add(T.ell(1.0, -46 + ub, 6.4, 3.2), 'rk_orange', z=26, rl=1.6, rs=2.2, line='hard', cast=(0, 1, 1))
    if tw_:
        tw_.__exit__(None, None, None)
    # exhaust from the two attached nozzles
    for lat, (nx, ny) in noz.items():
        sx = nx + float(T.dx(ny))
        if tw_:
            sx, ny = tw_.fwd(sx, ny)[:2]
        f.anchor('nozzle_R' if lat > 0 else 'nozzle_L', sx, ny)
        if th > 0:
            z = 47.4 if vf == 'N' else (0.5 if vf == 'S' else (2.1 if R.far(lat) is False else 0.9))
            exhaust(f, sx, ny, z, th * (0.8 if R.far(lat) else 1.0), slant)
    if facing == 'N':     # both nozzles are on the back: from behind both anchors are known
        pass
    # -------------------------------------------------- helmet at the hip
    if P['helmet'] == 'hip':
        h3 = add3(S['hip3'], HELM_HIP)
        x, y = R.p(h3)
        d = R.d(h3)
        # clipped by its neck ring, faceplate turned OUT from the hip (toward his right)
        if vf == 'N':
            helmet(f, x, y, 24 if d > -5 else 6, visor_dir=1)
        elif vf == 'S':
            helmet(f, x, y, 24, visor_dir=-1)
        elif facing == 'E':
            helmet(f, x, y, 26, visor_dir=0)
        else:
            helmet(f, x, y, 6, dim=1, visor_dir=None)
        zz = 24 if d > -5 else 6
        with f.tagging('helmet'):        # the clip strap: belt -> neck ring, with its buckle
            by = S['hy'] - 5.0
            f.add(f.rect(x - 1.0, by, x + 1.0, y + 5.5), 'rk_pad', z=zz - 0.05, rl=1, rs=1, dim=0 if d > -5 else 1, line='soft')
            f.add(f.rect(x - 1.5, by + 0.5, x + 1.5, by + 2.5), 'gunmetal', z=zz + 0.2, flat=2, dim=0 if d > -5 else 1, line=None)
    # -------------------------------------------------- arms, carbine, hands
    sh3 = S['sh3']
    hR = add3(P['handR'] or REST_R, S['body_off'])
    gun_z = None
    hL = add3(P['handL'], S['body_off']) if P['handL'] else None
    gp = add3(P['gpos'], S['body_off']) if P['gpos'] else hR
    if P['gun'] == 'hands':
        fore3 = add3(gp, tuple(nrm(P['gdir']) * P['fore']))
        fore3 = add3(fore3, (0.0, -1.2, 0.0))
        if hL is None:
            hL = fore3
    if hL is None:
        hL = add3((1.0, 27.0, -13.5), S['body_off'])
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    arms = {}
    for key, lat, hh in (('R', 1, hR), ('L', -1, hL)):
        far = R.far(lat)
        z = P['z' + key]
        if z is None:
            z = R.zarm(hh)
            if side and 30 <= z < 40:
                z = 29.0 if far else 31.5
        arms[key] = (lat, hh, z, far)
    if P['gun'] in ('hands', 'right'):
        if vf == 'S':
            gun_z = 33.0
        elif vf == 'N':
            gun_z = 5.0 if R.d(add3(gp, tuple(nrm(P['gdir']) * 10))) < 2 else 33.0
        else:
            gun_z = 30.5
        mz = carbine(f, R, gp, P['gdir'], gun_z, dim=0)
        if P['flash']:
            dd = nrm(np.subtract(R.p(add3(gp, tuple(nrm(P['gdir'])))), R.p(gp)))
            flash(f, mz[0], mz[1], gun_z + 1, dd[0], dd[1])
    elif P['gun'] == 'sling':
        pass
    for key in ('R', 'L'):
        lat, hh, z, far = arms[key]
        shp = add3(sh3, (0.5, -0.5, SHW * lat))
        pole = P['pole' + key] or (-1.0, -0.2, 0.7 * lat)
        suit_arm(f, R, shp, hh, pole, z, 1 if far else 0)
        px, py = R.p(shp)
        shoulder_pad(f, px, py - 2.0, (z + 1.0 if not far else z + 0.1), w=4.6 if side else 5.0, dim=1 if far else 0)
        hx, hy = R.p(hh)
        hz = z + 0.8
        if gun_z is not None and vf == 'S':
            hz = max(hz, gun_z + 1)
        if gun_z is not None and side and not far:
            hz = max(hz, gun_z + 1)
        if key == 'R' and P['helmet'] == 'hand':
            lift = hh[1] > 45.0 + S['body_off'][1]            # raised: the hand holds it from below
            helmet(f, hx + (0.0 if not side else 1.0), hy + (-8.0 if lift else 7.0), hz - 0.3, dim=1 if far else 0,
                   visor_dir=(0 if facing == 'S' else (None if vf == 'N' else 1)))
        gloved_hand(f, hx, hy, hz, dim=1 if far else 0)
    # -------------------------------------------------- head
    H, hy = S['H'], S['qy']
    if R.diag:
        head_3q(H, P, hy, R.back)
    elif facing == 'S':
        head_south(H, P, hy)
    elif facing == 'N':
        head_north(H, P, hy)
    else:
        head_side(H, P, hy)
    if P['helmet'] == 'head':
        helmet_worn(H, P, hy, facing)
    top = R.p(add3(sh3, (-6.0, 14.0, 0.0)))
    f.anchor('pack_top', *top)


# ------------------------------------------------------------------------------------ heads
def _eyes(f, P, xs, ey):
    for x in xs:
        if P['face'] == 'shut':
            f.detail(f.rect(x, ey + 1, x + 2, ey + 2), EYE)
        elif P['blink']:
            f.detail(f.rect(x, ey + 2, x + 2, ey + 3), EYE)
        else:
            eye(f, x, ey, 3)


def head_south(f, P, hy):
    f.add(f.ell(-8.6, hy + 1.8, 1.8, 2.6) | f.ell(8.6, hy + 1.8, 1.8, 2.6), 'skin_d', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 1.4, 8.2, 8.9), 'skin_d', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    stub = f.ell(0, hy + 1.4, 8.2, 8.9) & (f.Y > hy + 4.6) & ~f.ell(0, hy + 4.4, 3.4, 1.6)
    f.add(stub, 'rk_stub', z=40.5, rl=1.2, rs=2.4, line=None)
    cap = f.ell(0, hy - 3.6, 10.2, 8.2) | f.ell(-9.0, hy - 0.5, 2.2, 3.8) | f.ell(9.0, hy - 0.5, 2.2, 3.8)
    cap &= ~(f.ell(0, hy + 2.0, 7.6, 6.2) & (f.Y > hy - 2.4))
    locks = f.poly([(-9.6, hy - 6), (-8.6, hy - 0.6), (-6.4, hy - 3.2), (-4.0, hy - 1.0), (-1.4, hy - 3.4), (1.2, hy - 0.8),
                    (3.4, hy - 3.4), (6.0, hy - 1.4), (8.0, hy - 3.6), (9.6, hy - 1.4), (10, hy - 6)])
    tufts = f.ell(-4.0, hy - 10.4, 4.4, 2.6) | f.ell(3.4, hy - 10.8, 4.0, 2.4)
    f.add(_in_helmet(f, P, cap | locks | tufts, hy), 'rk_hair', z=44, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _hair_clumps(X, Y, t, hy))
    ey = hy + 0.6
    _eyes(f.f, P, (round(f._x(-5, ey)), round(f._x(3, ey))), ey)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(-6, ey - 2 + lift, -2, ey - 1 + lift), ('rk_hair', 1))
    f.detail(f.rect(2, ey - 2 + lift, 6, ey - 1 + lift), ('rk_hair', 1))
    f.dot(0, hy + 3, ('skin_d', 3))
    f.detail(f.rect(0, hy + 4, 2, hy + 5), ('skin_d', 1))
    f.detail(f.rect(-1, hy + 6, 2, hy + 7), ('rk_stub', 0))


def _in_helmet(f, P, m, hy, cx=0.0):
    """26 Oct (Matt: "make sure the hair doesn't poke through the helmet"): with the bubble helmet
    worn, the hair is cut to the glass's inner volume (radius 10.4 inside the 11.4 inner rim), so
    the glass, its rim and highlight always draw over all of it."""
    if P.get('helmet') != 'head':
        return m
    return m & f.ell(cx, hy - 0.5, 10.2, 10.2)


def head_3q(f, P, hy, back):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW on the mirrored grid): the face turned
    a quarter toward the facing (front) or away (back), the mop of dark hair round it."""
    if back:
        f.add(f.ell(7.6, hy + 1.8, 1.8, 2.6), 'skin_d', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(6.0, hy + 4.4, 3.0, 4.0), 'skin_d', z=39.5, rl=1, rs=1.4, line='hard')            # the cheek's edge, turned away
        back_ = f.ell(0.2, hy - 2.4, 10.0, 9.2) | f.ell(0.8, hy + 4.0, 7.4, 4.4)
        back_ |= f.ell(3.6, hy - 10.4, 4.4, 2.6) | f.ell(-3.6, hy - 10.6, 4.0, 2.4)
        back_ |= f.poly([(-5, hy + 7), (-3.5, hy + 9.6), (-1.5, hy + 7.6), (0.5, hy + 9.8), (2.5, hy + 7.6), (4.4, hy + 9.2), (5.0, hy + 6.5)])
        back_ &= ~(f.ell(7.0, hy + 4.0, 2.8, 4.4) & (f.Y > hy + 1.0))
        f.add(_in_helmet(f, P, back_, hy, 0.5), 'rk_hair', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1),
              tonemap=lambda X, Y, t: _hair_clumps(X, Y, t, hy + 5))
        return
    f.add(f.ell(-5.6, hy + 1.8, 1.7, 2.5), 'skin_d', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(1.2, hy + 1.4, 7.8, 8.9), 'skin_d', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    stub = f.ell(1.2, hy + 1.4, 7.8, 8.9) & (f.Y > hy + 4.6) & (f.X > -3.5) & ~f.ell(3.6, hy + 4.4, 2.8, 1.6)
    f.add(stub, 'rk_stub', z=40.5, rl=1.2, rs=2.4, line=None)
    cap = f.ell(0.0, hy - 3.6, 10.0, 8.2) | f.ell(-8.0, hy - 0.5, 2.6, 4.2) | f.ell(9.2, hy - 2.0, 1.4, 3.0)
    cap &= ~(f.ell(2.4, hy + 2.0, 7.2, 6.2) & (f.Y > hy - 2.4))
    locks = f.poly([(-9.4, hy - 6), (-8.4, hy - 0.6), (-5.6, hy - 3.2), (-3.0, hy - 1.0), (-0.2, hy - 3.4), (2.6, hy - 0.8),
                    (4.8, hy - 3.4), (7.2, hy - 1.4), (9.0, hy - 3.6), (9.8, hy - 6)])
    tufts = f.ell(-3.2, hy - 10.4, 4.4, 2.6) | f.ell(4.0, hy - 10.8, 4.0, 2.4)
    f.add(_in_helmet(f, P, cap | locks | tufts, hy, 0.5), 'rk_hair', z=44, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _hair_clumps(X, Y, t, hy))
    ey = hy + 0.6
    _eyes(f.f, P, (round(f._x(-1, ey)), round(f._x(5, ey))), ey)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(-2, ey - 2 + lift, 1, ey - 1 + lift), ('rk_hair', 1))
    f.detail(f.rect(4, ey - 2 + lift, 8, ey - 1 + lift), ('rk_hair', 1))
    f.dot(3, hy + 3, ('skin_d', 3))
    f.detail(f.rect(3, hy + 4, 5, hy + 5), ('skin_d', 1))
    f.detail(f.rect(2, hy + 6, 5, hy + 7), ('rk_stub', 0))


def _hair_clumps(X, Y, t, hy):
    out = t.copy()
    for x0, k in ((-5.0, 0.35), (-0.5, 0.3), (4.5, 0.25)):
        m = (abs(X - x0 - (Y - hy + 9) * k) < 0.55) & (Y > hy - 10) & (Y < hy - 3.5)
        out[m & (t >= 2)] = 1
    return out


def head_north(f, P, hy):
    f.add(f.ell(-8.6, hy + 1.8, 1.8, 2.6) | f.ell(8.6, hy + 1.8, 1.8, 2.6), 'skin_d', z=39, rl=1, rs=1.2, line='hard')
    back = f.ell(0, hy - 2.4, 10.2, 9.2) | f.ell(0, hy + 4.0, 7.6, 4.4)
    back |= f.ell(4.0, hy - 10.4, 4.4, 2.6) | f.ell(-3.4, hy - 10.8, 4.0, 2.4)
    back |= f.poly([(-5, hy + 7), (-3.5, hy + 9.6), (-1.5, hy + 7.6), (0.5, hy + 9.8), (2.5, hy + 7.6), (4.4, hy + 9.4), (5.5, hy + 6.5)])
    f.add(_in_helmet(f, P, back, hy), 'rk_hair', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _hair_clumps(X, Y, t, hy + 5))


def head_side(f, P, hy):
    f.add(f.ell(1.8, hy + 1.4, 7.4, 8.9), 'skin_d', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(8.8, hy + 3.4, 1.5, 1.5), 'skin_d', z=40.5, rl=1, rs=1, line='hard')
    stub = (f.ell(1.8, hy + 1.4, 7.4, 8.9) & (f.Y > hy + 4.8) & (f.X > -1.0)) & ~f.ell(8.0, hy + 4.4, 1.8, 1.4)
    f.add(stub, 'rk_stub', z=40.6, rl=1.2, rs=2.4, line=None)
    cap = f.ell(-0.6, hy - 3.6, 9.8, 8.2) | f.ell(-6.6, hy + 1.0, 3.6, 5.4)
    cap &= ~(f.ell(5.0, hy + 3.0, 6.2, 6.4) & (f.Y > hy - 2.4))
    cap |= f.poly([(1.0, hy - 8), (2.6, hy - 1.4), (4.6, hy - 3.6), (6.6, hy - 1.6), (8.6, hy - 3.8), (9.8, hy - 2.2), (9.6, hy - 7), (5, hy - 10)])
    cap |= f.ell(-3.6, hy - 10.2, 4.6, 2.6) | f.ell(3.0, hy - 10.6, 4.2, 2.4)
    cap |= f.poly([(-9, hy + 1), (-10.6, hy + 5.0), (-7.6, hy + 4.4), (-7.0, hy + 7.0), (-4.6, hy + 4.0)])
    f.add(_in_helmet(f, P, cap, hy, 0.5), 'rk_hair', z=44, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _hair_clumps(X, Y, t, hy))
    f.add(f.ell(-1.6, hy + 2.4, 1.8, 2.5), 'skin_d', z=45, rl=1, rs=1.2, line='hard')
    f.dot(-1.6, hy + 2.4, ('skin_d', 1))
    ey = hy + 0.6
    _eyes(f.f, P, (round(f._x(4, ey)),), ey)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(3, ey - 2 + lift, 7, ey - 1 + lift), ('rk_hair', 1))
    f.detail(f.rect(6, hy + 6.5, 8, hy + 7.5), ('rk_stub', 0))


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in FLIP))
    f.despeckle = True
    build(f, facing, P)
    return f


# Matt, 26 Oct 19:19: Rook is option C, the observatory moon-walker (blue and beige quilted suit, a
# glass bubble helmet in a brass ring).  The brass (A) and shard (B) suits stay in rook_opts.py as
# future cosmetic outfits (game/data/progression/rook.json, proposals).
import rook_opts as _opts  # noqa: E402
_opts.use('lantern')

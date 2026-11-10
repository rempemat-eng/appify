"""Nix: mature human cyborg.  Short asymmetric dark hair swept from his left to his right, a grey
streak at the LEFT temple, an open teal technical jacket with an orange lining over a black shirt,
a dark belt with a gold buckle, dark trousers with cyan circuit traces on the shins, dark boots.
The laser arm is his anatomical LEFT arm in every view and drawing: a steel-blue casing from a
shoulder pauldron to a heavy forearm emitter with a cyan lens at the end of the forearm.  The
RIGHT arm is natural, with a black fingerless wrist wrap.  About 74 px tall.

Pass 3: pose-driven on parts.Rig (as bramble.py).  The pose places hips, shoulders, feet and
hands in body space; the torso and head drawings of the approved static design are placed on
the projected hip / shoulder / head points through Sh (a coordinate shift with a lean shear),
so the approved art is kept pixel for pixel in the rest pose.

Gear states: casing 0..1 (Limit Release opens the SAME left forearm casing: two plates lift
off a lit core; it stays open in every powered clip), flare (lens flash at the release).
Tags: laser (the left arm's casing and emitter).  Anchors: hand_R, hand_L, foot_R, foot_L,
muzzle (the lens), origin (the foot pivot, where Afterimage leaves its decoy).

Sh, skel and legs are also used by rook.py and mote.py (designer 3's shared helpers)."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, boot_side, boot_front, EYE, Rig
import palette  # noqa: F401
import anim
import surf
import turn

ID = 'nix'
NAME = 'Nix'
BAND = (68, 80)

mat('nx_teal',   ['#11343E', '#1B5860', '#2A8488', '#52B4AC'])
mat('nx_lining', ['#6A2A12', '#B04A1C', '#E8762A', '#FFA858'])
mat('nx_shirt',  ['#111118', '#1C1C26', '#2A2A36', '#424256'])
mat('nx_trouser', ['#15151D', '#22222C', '#333342', '#4C4C5C'])
mat('nx_boot',   ['#101014', '#1C1C22', '#2C2C34', '#46464F'])
mat('nx_hair',   ['#10101C', '#1C1C2C', '#2C2A42', '#4A4664'])
mat('nx_temple', ['#4C4858', '#7C7884', '#A8A6AE', '#D4D2D6'])
mat('nx_cyber',  ['#28304E', '#4A5A86', '#7488B4', '#AEC2E0', '#EEF6FF'])
mat('nx_joint',  ['#0E1020', '#1A1E30', '#2A3044', '#424A62'])
mat('nx_glow',   ['#0E6A9A', '#1AA6E0', '#4ADCFF', '#C8F6FF'])
mat('nx_wrap',   ['#121216', '#1E1E26', '#2E2E38', '#4A4A56'])

SHW = 10.8
REST_R = (1.0, 28.5, 12.8)
REST_L = (4.0, 27.0, -13.0)


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0,
             footR=(1.5, 0.0), footL=(-2.0, 0.0), stance=5.0,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             casing=0.0, flare=False, lag=0.0, blink=False, brow=0, face=None)
    p.update(k)
    return p


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


# ================================================================ designer 3 shared helpers
class Sh:
    """A Fig seen through a shift: x moves by dx(y) = x0 + shear * t(y), t rising 0 -> 1 from
    the hip row y0 to the shoulder row y1 (clamped to 0..1.15).  Every primitive, X/Y, details
    and tonemaps follow, so a static drawing in pivot coordinates can ride a leaning torso."""

    def __init__(self, f, x0=0.0, y0=0.0, y1=-1.0, shear=0.0):
        self.f, self.x0, self.y0, self.y1, self.shear = f, x0, y0, y1, shear

    def dx(self, y):
        t = np.clip((self.y0 - y) / (self.y0 - self.y1), 0.0, 1.15)
        return self.x0 + self.shear * t

    def _x(self, x, y):
        return x + float(self.dx(y))

    @property
    def X(self):
        return self.f.X - self.dx(self.f.Y)

    @property
    def Y(self):
        return self.f.Y

    def ell(self, cx, cy, rx, ry):
        return self.f.ell(self._x(cx, cy), cy, rx, ry)

    def rell(self, cx, cy, a, b, ang):
        return self.f.rell(self._x(cx, cy), cy, a, b, ang)

    def rect(self, x0, y0, x1, y1):
        d = float(self.dx((y0 + y1) / 2))
        return self.f.rect(x0 + d, y0, x1 + d, y1)

    def cap(self, x0, y0, x1, y1, r0, r1=None):
        return self.f.cap(self._x(x0, y0), y0, self._x(x1, y1), y1, r0, r1)

    def poly(self, pts):
        return self.f.poly([(self._x(x, y), y) for x, y in pts])

    def seg(self, x0, y0, x1, y1):
        return self.f.seg(self._x(x0, y0), y0, self._x(x1, y1), y1)

    def dot(self, x, y, c, solid=True, tag=None, z=None):
        self.f.dot(self._x(x, y), y, c, solid, tag, z)

    def detail(self, *a, **k):
        self.f.detail(*a, **k)

    def tagging(self, tag):
        return self.f.tagging(tag)

    def anchor(self, name, x, y):
        self.f.anchor(name, self._x(x, y), y)

    def add(self, mask, m, **k):
        tm = k.get('tonemap')
        if tm is not None:
            k['tonemap'] = lambda X, Y, t, tm=tm: tm(X - self.dx(Y), Y, t)
        return self.f.add(mask, m, **k)


def skel(R, P, hip_up=22.0, sh_up=41.0, head_up=17.0):
    """Body points of a pose: hip, shoulder and head centre (3D) and their screen points, the
    static drawing offsets b (hip row) and ub (shoulder row), and the torso and head shifts."""
    cr, b = P['crouch'], P['bob']
    hip3 = (P['hipx'], hip_up - cr - b, 0.0)
    sh3 = (P['hipx'] + P['lean'], sh_up - cr - b + P['breath'], 0.0)
    head3 = (sh3[0] + P['lean'] * 0.35, sh3[1] + head_up, 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    qx, qy = R.p(head3)
    bS, ubS = hy + hip_up, sy + sh_up
    T = Sh(R.f, hx, hy, sy, sx - hx)
    H = Sh(R.f, qx)
    return dict(hip3=hip3, sh3=sh3, head3=head3, hx=hx, hy=hy, sx=sx, sy=sy, qx=qx, qy=qy, b=bS, ub=ubS, T=T, H=H,
                body_off=(P['hipx'], -cr - b, 0.0))


def legs(f, R, P, S, mat_leg, mat_boot, l=(8.2, 8.2), r=(4.0, 3.8, 3.5), hipw=0.9, ankle=6.5, toe=1.6, bh=7):
    """Two legs from the hip to the feet with the 3D rig; returns per side (lat sign) the
    projected foot, the masks and whether it is the far leg."""
    out = {}
    for lat, key in ((P['stance'], 'footR'), (-P['stance'], 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], ft[2] if len(ft) > 2 else lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + ankle, foot3[2])
        hp3 = add3(S['hip3'], (0.0, 0.0, lat * hipw))
        up, lo, kn3 = R.limb(hp3, ank3, l[0], l[1], r[0], r[1], r[2], (1.0, 0.0, 0.12 * np.sign(lat)))
        far = R.far(lat)
        z = R.zleg(foot3)
        f.add(up | lo, mat_leg, z=z, rl=1.8, rs=2.8, vgrad=0.3, dim=1 if far else 0, line='hard')
        fx, fy = R.p(foot3)
        if R.diag:                                   # contract v2: the three-quarter boot (turn in-betweens)
            surf.boot_3q(f, R, foot3, mat_boot, z + 1, dim=1 if far else 0, cuff=False)
        elif R.side:
            boot_side(f, fx, fy, mat_boot, z=z + 1, dim=1 if far else 0, toe=toe, h=bh)
        else:
            boot_front(f, fx, fy, mat_boot, z=z + 1)
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
        out[np.sign(lat)] = dict(fx=fx, fy=fy, up=up, lo=lo, far=far, z=z, kn=R.p(kn3), lat=lat)
    return out


def nrm(v):
    v = np.array(v, float)
    return v / (np.linalg.norm(v) or 1.0)


# ------------------------------------------------------------------------------------ arms
def _glow(f, mask, z, k, tag=None):
    """Lit pixels as a flat part (so a nearer part still hides them); never dimmed."""
    f.add(mask, 'nx_glow', z=z, flat=k, line=None, clean=False, tag=tag)


def natural_arm(f, R, sh3, h3, pole, z, dim):
    up, lo, el3 = R.limb(sh3, h3, 8.0, 7.5, 3.3, 3.0, 2.8, pole)
    f.add(up, 'nx_teal', z=z, rl=1.4, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1))
    f.add(lo, 'nx_teal', z=z + 0.05, rl=1.4, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1))
    hx, hy = R.p(h3)
    ex, ey = R.p(el3)
    # black fingerless wrist wrap just above the bare hand (skin), never metal or glow
    wx, wy = hx + (ex - hx) * 0.42, hy + (ey - hy) * 0.42
    f.add(f.cap(wx, wy, hx + (ex - hx) * 0.2, hy + (ey - hy) * 0.2, 2.9), 'nx_wrap', z=z + 0.1, rl=1, rs=1.4, dim=dim, line='hard')
    f.add(f.ell(hx, hy + 0.5, 2.9, 3.0), 'skin', z=z + 0.3, rl=1.4, rs=2.0, dim=dim, line='hard')
    return el3


def laser_arm(f, R, sh3, h3, pole, z, dim, casing=0.0, flare=False):
    """Left arm: segmented upper casing, a lit elbow joint, a heavy forearm casing with a cyan
    power seam, the emitter housing at the hand and its lens at the end of the forearm axis.
    casing > 0 opens the same forearm casing: two plates lift off a lit core."""
    with f.tagging('laser'):
        up, lo, el3 = R.limb(sh3, h3, 8.0, 7.5, 3.2, 2.9, 3.0, pole)
        f.add(up, 'nx_cyber', z=z, rl=1.3, rs=2.0, dim=dim, line='hard')
        ex, ey = R.p(el3)
        hx, hy = R.p(h3)
        f.add(f.ell(ex, ey, 2.7, 2.4), 'nx_joint', z=z + 0.1, rl=1, rs=1.2, dim=dim, line='hard')
        u3 = nrm(np.subtract(h3, el3))
        lens3 = tuple(np.array(h3) + u3 * 3.2)
        lx, ly = R.p(lens3)
        L = math.hypot(hx - ex, hy - ey) or 1.0
        ux, uy = (hx - ex) / L, (hy - ey) / L
        nx, ny = -uy, ux
        c = min(1.0, casing)
        if c < 0.1:
            fore = f.cap(ex + ux, ey + uy, hx, hy, 3.4, 4.8)
            f.add(fore, 'nx_cyber', z=z + 0.2, rl=1.6, rs=2.6, dim=dim, line='hard', cast=(1, 1, 1))
            seam = f.seg(ex + ux * 3 + nx * 1.5, ey + uy * 3 + ny * 1.5, hx - ux * 2 + nx * 2.2, hy - uy * 2 + ny * 2.2)
            f.detail(seam, ('nx_glow', 1), z=z + 0.25)
            f.dot(ex + ux * 3 + nx * 1.5, ey + uy * 3 + ny * 1.5, ('nx_glow', 3), z=z + 0.25)
        else:
            # Limit Release: the casing splits along its length, plates lift on both sides
            o = 1.6 + 2.2 * c
            _glow(f, f.cap(ex + ux, ey + uy, hx, hy, 2.6, 3.8), z + 0.15, 2)
            _glow(f, f.cap(ex + ux * 2.5, ey + uy * 2.5, hx - ux, hy - uy, 1.0, 1.6), z + 0.16, 3)
            for s in (-1, 1):
                pl = f.cap(ex + ux * 1.5 + nx * o * s, ey + uy * 1.5 + ny * o * s, hx + nx * (o + 0.6) * s, hy + ny * (o + 0.6) * s,
                           1.8, 2.4)
                f.add(pl, 'nx_cyber', z=z + 0.2 + (0.02 if s > 0 else 0), rl=1.2, rs=1.6, dim=dim, line='hard')
            # hinge pins tie the plates to the arm at the elbow end
            f.add(f.ell(ex + ux * 1.5, ey + uy * 1.5, 2.0, 2.0), 'nx_joint', z=z + 0.22, rl=1, rs=1, dim=dim, line='hard')
        # emitter housing: lit shell with a dark collar, the lens at the forearm's end
        em = f.ell(hx + ux * 1.2, hy + uy * 1.2, 4.2, 3.8)
        f.add(em, 'nx_glow', z=z + 0.3, rl=1.6, rs=2.2, line='hard')
        col = f.cap(hx - ux * 1.2 - nx * 4.5, hy - uy * 1.2 - ny * 4.5, hx - ux * 1.2 + nx * 4.5, hy - uy * 1.2 + ny * 4.5, 0.8)
        f.add(col & (em | f.ell(hx, hy, 5, 5)), 'nx_joint', z=z + 0.35, flat=1, line=None)
        _glow(f, f.ell(ex, ey, 1.0, 1.0), z + 0.5, 3)
        if R.d(lens3) > R.d(h3) - 1.5:          # the lens faces us or across: show its lit ring
            _glow(f, f.ell(lx, ly, 1.7, 1.7), z + 0.5, 3)
        if flare:
            _glow(f, f.poly([(lx - ux * 1 - nx * 3.5, ly - uy * 1 - ny * 3.5), (lx + ux * 6, ly + uy * 6),
                              (lx - ux * 1 + nx * 3.5, ly - uy * 1 + ny * 3.5)]) | f.ell(lx, ly, 3.0, 3.0), z + 0.6, 3)
            _glow(f, f.ell(lx, ly, 1.4, 1.4), z + 0.61, 2)
    f.anchor('muzzle', lx, ly)
    return el3


def pauldron(f, x, y, z, dim=0, w=4.6):
    with f.tagging('laser'):
        m = f.ell(x, y, w, 3.8) & (f.Y < y + 2.6)
        f.add(m, 'nx_cyber', z=z, rl=1.6, rs=2.4, dim=dim, line='hard', cast=(0, 1, 1))
        f.detail(f.rect(x - 2, y + 1, x + 2, y + 2) & m, ('nx_joint', 1), z=z)


# ------------------------------------------------------------------------------------ build
def build(f, facing, P):
    R = Rig(f, facing)
    R.body_half = 10.5
    S = skel(R, P)
    T, b, ub = S['T'], S['b'], S['ub']
    f.anchor('origin', 0.0, 0.0)
    # -------------------------------------------------- legs
    L = legs(f, R, P, S, 'nx_trouser', 'nx_boot')
    for s, lg in L.items():
        if lg['far'] and R.side:
            continue
        fx, fy = lg['fx'], lg['fy']
        if R.side:
            xo = fx + 1.0
        elif facing == 'S':
            xo = fx + (2.5 if fx > S['hx'] else -3.5)
        else:
            xo = fx - 0.5
        tr = f.rect(xo, fy - 16, xo + 1, fy - 11)
        if R.side:
            tr |= f.rect(xo - 1, fy - 11, xo + 1, fy - 10)
        f.detail(tr & lg['lo'], ('nx_glow', 1), z=lg['z'] + 0.1)
        f.detail(f.rect(xo, fy - 16, xo + 1, fy - 15) & lg['lo'], ('nx_glow', 2), z=lg['z'] + 0.1)
    tw_ = turn.Warp(f, R, (S['sx'] + S['hx']) / 2, 10.5, 8.0, 'N' if R.back else 'S') if R.diag else None
    if tw_:
        tw_.__enter__()
    if R.side:
        T.add(T.ell(0.5, -23.5 + b, 7.6, 4.0), 'nx_trouser', z=18, rl=1.8, rs=2.8, line='hard')
    else:
        T.add(T.rect(-9, -27 + b, 9, -21 + b) | T.ell(0, -21.5 + b, 9, 3.5), 'nx_trouser', z=13, rl=1.8, rs=3.0, vgrad=0.4,
              line='hard', tonemap=lambda X, Y, t: _crotch(X, Y, t, b))
    # -------------------------------------------------- torso
    if facing == 'S' or (R.diag and not R.back):
        torso_south(T, b, ub)
    elif facing == 'N' or R.diag:
        torso_north(T, b, ub)
    else:
        torso_side(T, b, ub)
    if tw_:
        tw_.__exit__(None, None, None)
    # -------------------------------------------------- arms
    sh3 = S['sh3']
    for key, lat, rest in (('R', 1, REST_R), ('L', -1, REST_L)):
        shp = add3(sh3, (0.5, -0.5, SHW * lat))
        h3 = add3(P['hand' + key] or rest, S['body_off'])
        f.anchor('hand_' + key, *R.p(h3))
        pole = P['pole' + key] or (-1.0, -0.2, 0.7 * lat)
        z = P['z' + key] if P['z' + key] is not None else R.zarm(h3)
        far = R.far(lat)
        dim = 1 if far else 0
        px, py = R.p(shp)
        if key == 'R':
            natural_arm(f, R, shp, h3, pole, z, dim)
            f.add(f.ell(px - 0.3, py - 1.1, 3.8, 3.2) & (f.Y < py - 0.0), 'nx_teal', z=(z + 1 if not far else z + 0.2),
                  rl=1.4, rs=2.0, dim=dim, line='soft')
        else:
            laser_arm(f, R, shp, h3, pole, z, dim, P['casing'], P['flare'])
            pauldron(f, px - 0.1, py - 2.0, (z + 2 if not far else z + 0.4), dim=dim, w=4.4 if R.side else 4.6)
    # -------------------------------------------------- head
    H, hy = S['H'], S['qy']
    if R.diag:
        head_3q(H, P, hy, R.back, facing in ('SW', 'NW'))
    elif facing == 'S':
        head_south(H, P, hy)
    elif facing == 'N':
        head_north(H, P, hy)
    else:
        head_side(H, P, hy, facing == 'W')


def _crotch(X, Y, t, b):
    out = t.copy()
    out[(abs(X) < 0.6) & (Y > -19 + b)] = 0
    return out


# ------------------------------------------------------------------------------------ torsos
def torso_south(f, b, ub):
    f.add(f.ell(0, -38 + ub, 9.6, 9) | f.rect(-9, -40 + ub, 9, -27 + b), 'nx_shirt', z=20, rl=1.6, rs=3.0, line='hard')
    f.add(f.rect(-8.5, -30 + b, 8.5, -27 + b), 'nx_wrap', z=21, rl=1, rs=1.2, line='soft')
    f.add(f.rect(-2, -31 + b, 2, -26 + b), 'gold', z=22, rl=1, rs=1.4, line='hard')
    f.dot(-1, -30 + b, ('gold', 4))
    for s in (-1, 1):
        panel = f.poly([(3.6 * s, -46 + ub), (10.2 * s, -45 + ub), (10.8 * s, -32 + b), (10.6 * s, -24.5 + b),
                        (5.0 * s, -24.5 + b), (4.6 * s, -31 + b)])
        f.add(panel, 'nx_teal', z=24, rl=2.0, rs=3.2, vgrad=0.3, line='hard',
              tonemap=(lambda X, Y, t, s=s: _pocket(X, Y, t, s, b)))
        f.add(f.cap(4.4 * s, -44 + ub, 4.9 * s, -26 + b, 0.7) & panel, 'nx_lining', z=24.5, flat=2, line=None)
    for s in (-1, 1):
        col = f.poly([(2.5 * s, -49 + ub), (7.5 * s, -48 + ub), (8.0 * s, -44 + ub), (4.0 * s, -42 + ub)])
        f.add(col, 'nx_teal', z=26, rl=1.4, rs=2.0, line='hard', cast=(0, 1, 1))
        f.add(f.poly([(2.5 * s, -49 + ub), (4.5 * s, -48.5 + ub), (4.2 * s, -44 + ub), (3.2 * s, -45 + ub)]),
              'nx_lining', z=26.5, rl=1, rs=1.2, line=None)
    f.add(f.cap(-2.6, -47 + ub, 2.6, -47 + ub, 2.2), 'skin', z=25, rl=1, rs=1.4, line='hard')


def _pocket(X, Y, t, s, b):
    out = t.copy()
    m = (Y > -30.6 + b) & (Y < -29.4 + b) & (abs(X - 8.0 * s) < 2.4)
    out[m & (t >= 1)] = 0
    return out


def torso_north(f, b, ub):
    jacket = f.ell(0, -38 + ub, 10.0, 9.2) | f.poly([(-10.2, -42 + ub), (10.2, -42 + ub), (10.8, -24.5 + b), (-10.8, -24.5 + b)])
    f.add(jacket, 'nx_teal', z=24, rl=2.0, rs=3.4, vgrad=0.35, line='hard', tonemap=lambda X, Y, t: _back_seams(X, Y, t, ub, b))
    f.add(f.poly([(-7.5, -50 + ub), (7.5, -50 + ub), (8.5, -44 + ub), (-8.5, -44 + ub)]), 'nx_teal', z=26, rl=1.4, rs=2.0,
          line='hard', cast=(0, 1, 1))
    f.add(f.cap(-2.6, -48 + ub, 2.6, -48 + ub, 2.4), 'skin', z=38, rl=1, rs=1.4, line='hard')


def _back_seams(X, Y, t, ub, b):
    out = t.copy()
    m = (abs(X) < 0.6) & (Y > -36 + ub)
    out[m & (t >= 1)] = 0
    m = (abs(Y - (-31 + b)) < 0.6) & (abs(X) < 8.5)
    out[m & (t >= 2)] = 1
    return out


def torso_side(f, b, ub):
    f.add(f.ell(0.8, -38 + ub, 7.6, 9) | f.rect(-6.8, -40 + ub, 8.2, -27 + b), 'nx_shirt', z=19, rl=1.6, rs=3, line='hard')
    f.add(f.rect(-6.5, -30 + b, 8.6, -27 + b), 'nx_wrap', z=20, rl=1, rs=1.2, line='soft')
    f.add(f.rect(6.6, -31 + b, 9.0, -26 + b), 'gold', z=21, rl=1, rs=1.4, line='hard')
    jacket = f.poly([(-6.8, -46 + ub), (3.5, -47 + ub), (5.6, -44 + ub), (5.2, -31 + b), (6.4, -24.5 + b),
                     (-8.4, -24.0 + b), (-7.6, -32 + b)])
    f.add(jacket, 'nx_teal', z=24, rl=2.0, rs=3.2, vgrad=0.3, line='hard',
          tonemap=lambda X, Y, t: _side_seams(X, Y, t, b))
    f.add(f.cap(5.2, -43 + ub, 5.6, -26 + b, 0.7) & f.poly([(4, -48 + ub), (7, -48 + ub), (7.4, -24 + b), (4.6, -24 + b)]),
          'nx_lining', z=24.5, flat=2, line=None)
    f.add(f.poly([(-5.5, -51 + ub), (-1.0, -50 + ub), (1.0, -45 + ub), (-6.0, -44 + ub)]), 'nx_teal', z=26, rl=1.4, rs=2.0,
          line='hard', cast=(0, 1, 1))
    f.add(f.poly([(3.0, -48 + ub), (6.4, -46.5 + ub), (5.6, -43 + ub), (3.4, -44 + ub)]), 'nx_teal', z=26, rl=1.2, rs=1.6,
          line='hard')
    f.add(f.rect(3.4, -47.5 + ub, 4.4, -44 + ub), 'nx_lining', z=26.5, flat=2, line=None)
    f.add(f.cap(1.0, -48 + ub, 3.0, -47 + ub, 2.4), 'skin', z=25, rl=1, rs=1.4, line='hard')


def _side_seams(X, Y, t, b):
    out = t.copy()
    m = (abs(Y - (-30.5 + b)) < 0.6) & (X > -2.0) & (X < 4.6)
    out[m & (t >= 1)] = 0
    return out


# ------------------------------------------------------------------------------------ heads
def _eyes(f, P, xs, ey):
    for x in xs:
        if P['face'] == 'shut':
            f.detail(f.rect(x - 1 + 1, ey + 1, x + 2, ey + 2), EYE)
        elif P['blink']:
            f.detail(f.rect(x, ey + 2, x + 2, ey + 3), EYE)
        else:
            eye(f, x, ey, 3)


def head_south(f, P, hy):
    f.add(f.ell(-8.4, hy + 1.8, 1.8, 2.6) | f.ell(8.4, hy + 1.8, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 1.6, 7.9, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    cap = f.ell(0, hy - 3.8, 9.6, 8.0) | f.ell(-8.8, hy - 0.5, 2.0, 4.0) | f.ell(8.7, hy - 2.0, 1.6, 3.0)
    cap &= ~(f.ell(0, hy + 2.0, 7.4, 6.4) & (f.Y > hy - 2.0))
    fringe = f.poly([(9.0, hy - 8), (7.2, hy - 3.0), (5.8, hy - 4.6), (3.6, hy - 1.8), (2.4, hy - 4.0), (-0.6, hy - 1.2),
                     (-2.2, hy - 3.6), (-5.0, hy - 0.8), (-6.0, hy - 3.0), (-8.6, hy + 1.6), (-10.6, hy - 3.5), (-8, hy - 10)])
    flick = f.poly([(-4.5, hy - 10.5), (-11.4, hy - 10.0), (-8.0, hy - 6.5)]) | f.poly([(1.0, hy - 10.5), (-5.4, hy - 11.6), (-2.0, hy - 8.4)])
    f.add(cap | fringe | flick, 'nx_hair', z=44, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _hair_strands_front(X, Y, t, hy))
    fringe = fringe | flick
    grey = (f.ell(8.0, hy - 2.0, 2.4, 4.0) | f.cap(7.6, hy - 4, 4.0, hy - 9.5, 1.3)) & (cap | fringe)
    f.add(grey, 'nx_temple', z=44.5, rl=1.2, rs=1.6, line=None)
    ey = hy + 0.6
    xs = (round(f._x(-5, ey)), round(f._x(3, ey)))
    _eyes(f.f, P, xs, ey)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(-6, ey - 2 + lift, -3, ey - 1 + lift), ('nx_hair', 2))
    f.detail(f.rect(3, ey - 2 + lift, 6, ey - 1 + lift), ('nx_hair', 2))
    f.detail(f.rect(-6, ey + 3, -5, ey + 4), ('skin', 1))
    f.detail(f.rect(5, ey + 3, 6, ey + 4), ('skin', 1))
    f.dot(0, hy + 4, ('skin', 3))
    f.detail(f.rect(0, hy + 5, 2, hy + 6), ('skin', 1))
    f.detail(f.rect(-1, hy + 7, 2, hy + 8), ('skin', 0))


def _hair_strands_front(X, Y, t, hy):
    out = t.copy()
    for x0, k in ((-3.0, 0.55), (2.5, 0.5), (6.0, 0.45)):
        m = (abs(X - x0 - (Y - hy + 8) * k) < 0.55) & (Y > hy - 9) & (Y < hy - 3)
        out[m & (t >= 2)] = 1
    return out


def head_north(f, P, hy):
    f.add(f.ell(-8.4, hy + 1.8, 1.8, 2.6) | f.ell(8.4, hy + 1.8, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
    back = f.ell(0, hy - 2.0, 9.6, 9.2) | f.ell(0, hy + 4.5, 7.0, 4.0)
    f.add(back, 'nx_hair', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _back_hair(X, Y, t, hy))
    grey = (f.ell(-8.4, hy - 0.5, 2.0, 3.6) | f.cap(-7.6, hy - 3, -4.5, hy - 8.5, 1.2)) & back
    f.add(grey, 'nx_temple', z=41.5, rl=1.2, rs=1.6, line=None)


def _back_hair(X, Y, t, hy):
    out = t.copy()
    for x0 in (-3.5, 1.0, 5.0):
        m = (abs(X - x0 - (Y - hy) * 0.18) < 0.55) & (Y > hy - 4) & (Y < hy + 6)
        out[m & (t >= 2)] = 1
    out[(Y > hy + 6.5) & (t >= 2)] = 1
    return out


def head_side(f, P, hy, west):
    f.add(f.ell(1.8, hy + 1.6, 7.2, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(8.5, hy + 3.6, 1.4, 1.5), 'skin', z=40.5, rl=1, rs=1, line='hard')
    f.add(f.ell(4.0, hy + 8.4, 3.6, 1.6), 'skin', z=40.2, rl=1, rs=1.4, line=None)
    cap = f.ell(-0.6, hy - 3.8, 9.2, 8.0) | f.ell(-6.6, hy + 0.5, 3.0, 5.0)
    cap &= ~(f.ell(4.8, hy + 3.0, 6.0, 6.6) & (f.Y > hy - 2.0))
    cap |= f.poly([(-9.0, hy - 2), (-11.2, hy + 1.5), (-8.4, hy + 1.0), (-9.6, hy + 4.5), (-6.0, hy + 4.0), (-5.0, hy - 1)])
    cap |= f.poly([(-3.0, hy - 10.0), (-10.4, hy - 10.6), (-7.0, hy - 6.0)])
    if west:
        fringe = f.poly([(0.5, hy - 8), (2.6, hy - 3.6), (4.6, hy - 5.0), (6.6, hy - 3.2), (8.0, hy - 5.4), (9.0, hy - 8.4), (5.0, hy - 9.6)])
    else:
        fringe = f.poly([(0.0, hy - 8), (1.4, hy - 1.0), (3.4, hy - 3.6), (5.4, hy - 0.8), (7.0, hy - 3.4), (8.8, hy - 2.4),
                         (9.6, hy - 7.0), (5.0, hy - 9.6)])
    f.add(cap | fringe, 'nx_hair', z=44, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _side_strands(X, Y, t, hy))
    if west:
        grey = (f.ell(0.6, hy - 1.0, 2.6, 3.6) | f.cap(1.2, hy - 3.0, 4.0, hy - 8.0, 1.3)) & (cap | fringe)
        f.add(grey, 'nx_temple', z=44.5, rl=1.2, rs=1.6, line=None)
    f.add(f.ell(-1.6, hy + 2.4, 1.7, 2.4), 'skin', z=45, rl=1, rs=1.2, line='hard')
    f.dot(-1.6, hy + 2.4, ('skin', 1))
    ey = hy + 0.6
    _eyes(f.f, P, (round(f._x(4, ey)),), ey)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(3, ey - 2 + lift, 7, ey - 1 + lift), ('nx_hair', 2))
    f.dot(3, ey + 3, ('skin', 1))
    f.detail(f.rect(6, hy + 7, 8, hy + 8), ('skin', 0))


def head_3q(f, P, hy, back, west):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW on the mirrored grid).  west: the
    mirrored facings, where his LEFT side (the grey streak) is the near one."""
    if back:
        f.add(f.ell(8.0, hy + 1.8, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(6.0, hy + 3.6, 3.0, 4.6), 'skin', z=39.5, rl=1, rs=1.4, line='hard')
        back_ = (f.ell(0.2, hy - 2.0, 9.6, 9.2) | f.ell(0.8, hy + 4.5, 7.0, 4.0)) & ~(f.ell(7.0, hy + 4.0, 2.8, 4.4) & (f.Y > hy + 1.0))
        f.add(back_, 'nx_hair', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1), tonemap=lambda X, Y, t: _back_hair(X, Y, t, hy))
        if west:
            f.add((f.ell(-8.0, hy - 0.5, 2.0, 3.6) | f.cap(-7.2, hy - 3, -4.2, hy - 8.5, 1.2)) & back_, 'nx_temple', z=41.5, rl=1.2, rs=1.6,
                  line=None)
        return
    f.add(f.ell(-5.4, hy + 1.8, 1.7, 2.5), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(1.2, hy + 1.6, 7.8, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    cap = f.ell(0.2, hy - 3.8, 9.6, 8.0) | f.ell(-7.4, hy - 0.5, 2.6, 4.4) | f.ell(9.2, hy - 2.0, 1.4, 3.0)
    cap &= ~(f.ell(2.0, hy + 2.0, 7.0, 6.4) & (f.Y > hy - 2.0))
    fringe = f.poly([(9.6, hy - 8), (8.2, hy - 3.0), (6.8, hy - 4.6), (4.8, hy - 1.8), (3.4, hy - 4.0), (0.6, hy - 1.2), (-1.0, hy - 3.6),
                     (-3.6, hy - 0.8), (-4.6, hy - 3.0), (-7.4, hy + 1.6), (-9.0, hy - 3.5), (-7, hy - 10)])
    flick = f.poly([(-3.5, hy - 10.5), (-10.0, hy - 10.0), (-7.0, hy - 6.5)]) | f.poly([(1.8, hy - 10.5), (-4.4, hy - 11.6), (-1.2, hy - 8.4)])
    f.add(cap | fringe | flick, 'nx_hair', z=44, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _hair_strands_front(X, Y, t, hy))
    if west:                                     # his left temple is the near side
        grey = (f.ell(-7.2, hy - 1.0, 2.4, 3.8) | f.cap(-6.6, hy - 3.5, -3.6, hy - 9.0, 1.3)) & (cap | fringe | flick)
    else:
        grey = (f.ell(8.8, hy - 2.0, 1.4, 3.6)) & (cap | fringe)
    f.add(grey, 'nx_temple', z=44.5, rl=1.2, rs=1.6, line=None)
    ey = hy + 0.6
    _eyes(f.f, P, (round(f._x(-1, ey)), round(f._x(5, ey))), ey)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(-2, ey - 2 + lift, 1, ey - 1 + lift), ('nx_hair', 2))
    f.detail(f.rect(5, ey - 2 + lift, 8, ey - 1 + lift), ('nx_hair', 2))
    f.dot(3, hy + 4, ('skin', 3))
    f.detail(f.rect(3, hy + 5, 5, hy + 6), ('skin', 1))
    f.detail(f.rect(2, hy + 7, 5, hy + 8), ('skin', 0))


def _side_strands(X, Y, t, hy):
    out = t.copy()
    for x0 in (-4.0, -0.5, 3.0):
        m = (abs(X - x0 - (Y - hy + 8) * 0.45) < 0.55) & (Y > hy - 9) & (Y < hy - 2.5)
        out[m & (t >= 2)] = 1
    return out


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True
    build(f, facing, P)
    return f

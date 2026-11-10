"""Velvet: adult coastal duellist.  Dark skin, short tousled silver hair, a narrow violet naval
coat cut away at the front with long divided tails behind, gold-piped lapels, cream cuffs and
cravat, restrained brass buttons, dark trousers, tall brown boots.  Gear, each exactly once:
  - one sabre in the LEFT hand (brass knuckle-bow guard closed round the fist) in every clip;
  - its black scabbard on the RIGHT hip (cross-draw for the left hand), hanging back; it stays
    there (the sabre is never sheathed in the clips, so the scabbard is always empty-looking
    from outside, as a scabbard is);
  - one black lantern held by its bail ring in the RIGHT hand in every clip.  lamp: 1 lit
    (amber), 2 flare (the secondary: shutter open, white-hot), 3 powered (shutter open, bright
    and steady).  The lantern's action changes, never its hand or identity.
About 76 px tall.

Pass 2: pose-driven on parts.Rig (as bramble.py), with designer 1's Shift kit from morel.py.
Equipment tags: sabre, lantern, scabbard."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, EYE, Rig, FLIP
import palette  # noqa: F401
import anim
from morel import Shift, add3, mul3, nrm, sdir, frame, legs, boot, arm_z, fist, up_z, reach

ID = 'velvet'
NAME = 'Velvet'
HEIGHT = 76
BAND = (70, 81)

mat('skin_v',  ['#2A1412', '#4A2820', '#6E3E2C', '#955A3C'])
mat('silver',  ['#6A6684', '#B2AFC8', '#CDCBE3', '#FAF9FF'])          # v2: shadow, base and light one material family, wide lit step (asset gate: volume)
mat('navy',    ['#22143A', '#38225E', '#563892', '#7C5EC0'])
mat('trouser_v', ['#1A1422', '#2A2236', '#3C324C', '#544868'])
mat('iron',    ['#101016', '#1E1E26', '#30303A', '#4A4A58', '#8A8A9A'])
mat('lamp',    ['#B05A10', '#E89020', '#FFC444', '#FFF0A8'])
mat('scab',    ['#120E14', '#221A22', '#342830', '#4C3C44'])
mat('blush_v', ['#5A2A24', '#8A4036', '#A85A48', '#C07A66'])        # dark-skin blush (tone 1)

SHW = 11.0
REST_R = (3.5, 23.5, 14.0)          # low enough that the lantern's base shows below the tails in W          # lantern hand
REST_L = (4.5, 25.0, -13.5)         # sabre hand
SAB0 = (0.75, -0.7, -0.25)          # sabre at rest: point down and forward, a little out
SCAB = (-1.5, 28.5, 10.0)           # scabbard frog on the right hip


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0,
             footR=(2.0, 0.0), footL=(-2.0, 0.0), stance=5.0,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             sab=SAB0, lamp=1, lsw=0.0, blink=False, brow=0, face=None)
    p.update(k)
    return p


# ------------------------------------------------------------------------------------ gear
def sabre(f, gx, gy, ang, z, dim=0, length=23):
    """Sabre gripped at (gx, gy); ang: blade direction, radians from straight down, + toward +x.
    The blade curves a little toward its back.  Returns the tip."""
    dx, dy = math.sin(ang), math.cos(ang)
    nx, ny = -dy, dx
    with f.tagging('sabre'):
        f.add(f.cap(gx - dx * 3.5, gy - dy * 3.5, gx + dx * 1.5, gy + dy * 1.5, 1.2), 'scab', z=z, flat=2, line='hard', dim=dim)
        f.add(f.ell(gx - dx * 4.2, gy - dy * 4.2, 1.5, 1.5), 'brass', z=z + 0.01, rl=1, rs=1, line='hard', dim=dim)
        m = None
        x0, y0 = gx + dx * 3.5, gy + dy * 3.5
        pts = []
        for i in range(13):
            u = i / 12
            c = 1.4 * u * u * min(1.0, length / 23)
            pts.append((x0 + dx * length * u + nx * c, y0 + dy * length * u + ny * c))
        for (ax, ay), (bx, by), i in zip(pts[:-1], pts[1:], range(12)):
            r = 1.15 if i < 10 else 1.15 - (i - 9) * 0.35
            cc = f.cap(ax, ay, bx, by, r, max(0.5, r - 0.2))
            m = cc if m is None else m | cc
        f.add(m, 'steel', z=z + 0.02, rl=1.0, rs=1.0, line='hard', dim=dim)
        f.add(f.cap(gx + dx * 2.6 - nx * 2.2, gy + dy * 2.6 - ny * 2.2, gx + dx * 2.6 + nx * 2.2, gy + dy * 2.6 + ny * 2.2, 1.0),
              'brass', z=z + 0.03, rl=1, rs=1, line='hard', dim=dim)
        if not dim and length > 8:
            tipx, tipy = pts[6]
            f.dot(tipx, tipy, ('steel', 4), solid=False, z=z + 0.04)
    return pts[-1]


def sabre_guard(f, gx, gy, ang, z, dim=0):
    """Brass knuckle bow from the cross guard round the front of the fist to the pommel."""
    dx, dy = math.sin(ang), math.cos(ang)
    nx, ny = -dy, dx
    pts = []
    for i in range(7):
        t = i / 6
        a = (dx * (2.6 - 6.8 * t), dy * (2.6 - 6.8 * t))
        bulge = 4.0 * math.sin(math.pi * t)
        pts.append((gx + a[0] + nx * bulge, gy + a[1] + ny * bulge))
    m = None
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        c = f.cap(ax, ay, bx, by, 0.85)
        m = c if m is None else m | c
    f.add(m, 'brass', z=z, flat=2 if not dim else 1, line='hard', tag='sabre')


def lantern(f, gx, gy, z, dim=0, lamp=1, sw=0.0):
    """v2: sw swings the lantern under its bail ring (whole px at its base, + toward +x)."""
    with f.tagging('lantern'):
        ring = f.ell(gx, gy + 0.5, 2.4, 3.0) & ~f.ell(gx, gy + 0.5, 1.4, 2.0)
        f.add(ring & (f.Y > gy - 1), 'iron', z=z, flat=2, line='hard', dim=dim)
    k = int(round(sw))
    _lantern_body(f, gx + k, gy, z, dim, lamp, k)


def _lantern_body(f, gx, gy, z, dim=0, lamp=1, lean=0.0):
    """Black iron lantern hanging from the fist by its bail ring at (gx, gy).  lamp 1: amber
    behind the glass; 2: flare (shutter open, white-hot core); 3: powered (shutter open,
    steady bright)."""
    with f.tagging('lantern'):
        cap = f.poly([(gx - 2, gy + 3), (gx + 2, gy + 3), (gx + 4, gy + 5.5), (gx - 4, gy + 5.5)])
        f.add(cap, 'iron', z=z + 0.01, rl=1.2, rs=1.4, line='hard', dim=dim)
        body = f.rect(gx - 3.6, gy + 5.5, gx + 3.6, gy + 13.5)
        f.add(body, 'iron', z=z + 0.02, rl=1.2, rs=1.6, line='hard', dim=dim)
        if lamp <= 1:
            glass = f.rect(gx - 2.2, gy + 6.5, gx + 2.2, gy + 12.5)
            f.add(glass, 'lamp', z=z + 0.03, rl=1.0, rs=1.6, line=None, dim=dim)
            f.detail(f.rect(gx - 1, gy + 8.5, gx + 1, gy + 11.5), ('lamp', 3 if not dim else 2), z=z + 0.04)
            f.dot(gx - 1, gy + 8.5, ('glow', 3) if not dim else ('lamp', 3), z=z + 0.05)
        else:
            # shutter open: the glass pane swings aside (a dark leaf at the right edge) and the
            # opening shows the flame directly
            glass = f.rect(gx - 2.6, gy + 6.2, gx + 2.6, gy + 12.8)
            f.add(glass, 'glow', z=z + 0.03, flat=2 if lamp == 3 else 3, line=None)
            core = f.rect(gx - 1.2, gy + 7.5, gx + 1.2, gy + 12) if lamp == 2 else f.rect(gx - 1, gy + 8.5, gx + 1, gy + 11.5)
            f.detail(core, ('glow', 3), z=z + 0.04)
            f.detail(f.rect(gx - 0.5, gy + 8.5, gx + 0.5, gy + 10.5), ('lamp', 3), z=z + 0.05)
            f.add(f.rect(gx + 3.6, gy + 6, gx + 5.2, gy + 13), 'iron', z=z + 0.035, flat=1, line='hard', dim=dim)
        f.add(f.rect(gx - 4.2, gy + 13.5, gx + 4.2, gy + 15), 'iron', z=z + 0.04, rl=1, rs=1, line='hard', dim=dim)
        if not dim:
            f.dot(gx - 3, gy + 4, ('iron', 4), solid=False, z=z + 0.05)


def scabbard(f, x, y, ang, z, dim=0, length=22):
    """Scabbard hanging from the belt frog at (x, y), tilted by ang (radians from down)."""
    dx, dy = math.sin(ang), math.cos(ang)
    ex, ey = x + dx * length, y + dy * length
    with f.tagging('scabbard'):
        f.add(f.cap(x, y, ex, ey, 1.8, 1.4), 'scab', z=z, rl=1.0, rs=1.4, line='hard', dim=dim)
        f.add(f.cap(x, y, x + dx * 2.5, y + dy * 2.5, 2.1), 'brass', z=z + 0.01, rl=1, rs=1, line='hard', dim=dim)
        f.add(f.cap(ex - dx * 3, ey - dy * 3, ex, ey, 1.8, 1.4), 'brass', z=z + 0.01, rl=1, rs=1, line='hard', dim=dim)
        f.add(f.cap(x - dx * 1, y - dy * 1 - 1.5, x, y, 1.0), 'scab', z=z - 0.01, flat=1, line='hard', dim=dim)


# ------------------------------------------------------------------------------------ head
def hair_mass(f, hx, hy, side, z=44):
    if side == 0:
        m = f.ell(hx, hy - 4.5, 9.6, 7.2) | f.ell(hx - 8.6, hy + 0.5, 2.2, 4.4) | f.ell(hx + 8.6, hy + 0.5, 2.2, 4.4)
        m &= ~(f.ell(hx, hy + 2.5, 7.4, 6.0) & (f.Y > hy - 2.5))
        m |= f.poly([(hx - 9, hy - 4), (hx - 7.5, hy + 0.5), (hx - 5, hy - 2.5), (hx - 2.5, hy - 0.5), (hx, hy - 3),
                     (hx + 3, hy - 1), (hx + 5.5, hy - 3), (hx + 8, hy + 0.5), (hx + 9.5, hy - 4)])
        m |= f.ell(hx - 2.5, hy - 10.5, 3.2, 2.2) | f.ell(hx + 4, hy - 10, 3.0, 2.0)
    elif side == 1:
        m = f.ell(hx - 0.5, hy - 4.0, 9.2, 7.6) | f.ell(hx - 6.0, hy + 1.0, 3.8, 6.0)
        m &= ~(f.ell(hx + 5.0, hy + 3.0, 6.0, 6.2) & (f.Y > hy - 2.0))
        m |= f.poly([(hx + 1, hy - 4.5), (hx + 3, hy - 0.5), (hx + 5, hy - 3), (hx + 7, hy - 1), (hx + 9.2, hy - 4.5), (hx + 8.4, hy - 7)])
        m |= f.ell(hx - 1.5, hy - 10.5, 3.4, 2.2) | f.ell(hx - 8.5, hy - 5.0, 2.6, 2.6)
    else:
        m = f.ell(hx, hy - 2.5, 9.8, 9.4) | f.ell(hx - 2.5, hy - 10.5, 3.2, 2.2) | f.ell(hx + 4, hy - 10, 3.0, 2.0)
        m |= f.poly([(hx - 8, hy + 4), (hx - 5, hy + 8.5), (hx - 2, hy + 5.5), (hx + 1, hy + 9), (hx + 4, hy + 5.5), (hx + 7, hy + 8.5), (hx + 8.5, hy + 4)])
    f.add(m, 'silver', z=z, rl=2.3, tl=0.34, rs=3.6, ts=0.26, vgrad=0.7, deep=True, line='hard', cast=(0, 1, 1),   # v2: lit, base, shadow and deep planes (volume)
          tonemap=lambda X, Y, t: _locks(X, Y, t, hx, hy, side))


def _locks(X, Y, t, hx, hy, side):
    out = t.copy()
    for k in (-5.5, -1.5, 2.5, 6.0):
        m = (np.abs((X - hx) - k - (Y - hy + 4) * 0.45) < 0.55) & (Y > hy - 8) & (Y < hy - 3)
        out[m & (t == 2)] = 1
    r = ((X - hx + 2.5) / 5.0) ** 2 + ((Y - hy + 7.5) / 2.2) ** 2
    out[(r < 1.0) & (t == 2)] = 3
    return out


def _eyes_shut(P):
    return P['blink'] or P['face'] == 'shut'


def head_south(f, P, hy):
    f.add(f.ell(-8.4, hy + 1.5, 1.8, 2.6) | f.ell(8.4, hy + 1.5, 1.8, 2.6), 'skin_v', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 1.2, 8.0, 9.0), 'skin_v', z=40, rl=2.0, rs=3.0, vgrad=0.35, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: lit_plane(f, X, Y, t, 0 - 3.0, hy + 3.5, 2.4, 2.6))   # v2: the lit cheek plane
    hair_mass(f, 0, hy, 0)
    ey = hy + 1
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    if _eyes_shut(P):
        f.detail(f.rect(-5, ey + 2, -3, ey + 3), EYE)
        f.detail(f.rect(3, ey + 2, 5, ey + 3), EYE)
    else:
        eye(f, -5, ey, 3)
        eye(f, 3, ey, 3)
    f.detail(f.rect(-6, ey - 2 + lift, -2, ey - 1 + lift), ('silver', 1))
    f.detail(f.rect(2, ey - 2 + lift, 6, ey - 1 + lift), ('silver', 1))
    f.detail(f.rect(-1, hy + 4, 1, hy + 5), ('skin_v', 3))
    f.detail(f.rect(0, hy + 5, 1, hy + 6), ('skin_v', 1))
    f.detail(f.rect(-1, hy + 7, 2, hy + 8), ('skin_v', 0))
    f.detail(f.rect(-7, hy + 5, -5, hy + 6), ('blush_v', 1))
    f.detail(f.rect(5, hy + 5, 7, hy + 6), ('blush_v', 1))
    f.dot(-8.5, hy + 3, ('gold', 3))


def head_side(f, P, hy, hx, west=False):
    f.add(f.ell(hx + 1.8, hy + 1.2, 7.2, 9.0), 'skin_v', z=40, rl=2.0, rs=3.0, vgrad=0.35, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: lit_plane(f, X, Y, t, (hx + 1.8) * (-1 if f.flip else 1) - 3.0, hy + 3.5, 2.4, 2.6))   # v2: the lit cheek plane
    f.add(f.ell(hx + 8.6, hy + 3.6, 1.3, 1.4), 'skin_v', z=40.5, rl=1, rs=1, line='hard')
    hair_mass(f, hx, hy, 1)
    f.add(f.ell(hx - 1.6, hy + 2.2, 1.7, 2.5), 'skin_v', z=45, rl=1, rs=1.2, line='hard')
    f.dot(hx - 1.6, hy + 2.2, ('skin_v', 1))
    if not west:
        f.dot(hx - 1.6, hy + 4, ('gold', 3))
    ey = hy + 1
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    if _eyes_shut(P):
        f.detail(f.rect(hx + 4, ey + 2, hx + 6, ey + 3), EYE)
    else:
        eye(f, hx + 4, ey, 3)
    f.detail(f.rect(hx + 3, ey - 2 + lift, hx + 7, ey - 1 + lift), ('silver', 1))
    f.detail(f.rect(hx + 6, hy + 7, hx + 8, hy + 8), ('skin_v', 0))
    f.detail(f.rect(hx + 3, hy + 5, hx + 5, hy + 6), ('blush_v', 1))


def head_north(f, P, hy):
    f.add(f.ell(-8.4, hy + 1.5, 1.8, 2.6) | f.ell(8.4, hy + 1.5, 1.8, 2.6), 'skin_v', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 1.2, 8.0, 9.0), 'skin_v', z=40, rl=2.0, rs=3.0, line='hard')
    hair_mass(f, 0, hy, 2)
    f.dot(8.5, hy + 3, ('gold', 3))


# ------------------------------------------------------------------------------------ torso
def torso_south(f, P, b, ub):
    tails = f.poly([(-9, -30 + b), (9, -30 + b), (12.5, -12 + b), (9, -11 + b), (-9, -11 + b), (-12.5, -12 + b)])
    f.add(tails, 'navy', z=5, rl=2.0, tl=0.34, rs=2.4, vgrad=0.5, line='hard')   # v2: shaded, not one dim tone (volume)
    body = f.ell(0, -38 + ub, 10.2, 10) | f.rect(-9.5, -40 + ub, 9.5, -29 + b)
    body |= f.poly([(-9.5, -29 + b), (-2.5, -29 + b), (-7, -22 + b), (-10.5, -21 + b)]) | f.poly([(9.5, -29 + b), (2.5, -29 + b), (7, -22 + b), (10.5, -21 + b)])
    f.add(body, 'navy', z=20, rl=2.8, rs=3.6, tl=0.34, vgrad=0.55, line='hard')
    V = f.poly([(-4, -48 + ub), (4, -48 + ub), (0, -38 + ub)])
    f.add(V, 'cream', z=21, rl=1.2, rs=1.6, line='hard')
    f.add(f.ell(0, -45.5 + ub, 2.0, 1.6) | f.poly([(-1.5, -45 + ub), (1.5, -45 + ub), (0.8, -41 + ub), (-0.8, -41 + ub)]), 'cream', z=21.2, rl=1, rs=1.2, line='soft')
    for s in (-1, 1):
        lap = f.poly([(4.2 * s, -48.5 + ub), (8.5 * s, -46 + ub), (6 * s, -41 + ub), (0.5 * s, -37.5 + ub)])
        f.add(lap, 'navy', z=22, rl=1.4, rs=2, line='soft')
        f.detail(f.seg(4.2 * s, -48 + ub, 0.5 * s, -38 + ub) | f.seg(8.2 * s, -46 + ub, 6 * s, -41.5 + ub), ('gold', 2), solid=False, z=22.1)
    for s in (-1, 1):
        for y in (-36, -33):
            f.add(f.rect(3.5 * s - 1, y + ub, 3.5 * s + 1, y + 1.6 + ub), 'brass', z=23, flat=3, line=None)
    f.add(f.rect(-10, -30.5 + b, 10, -27.5 + b), 'scab', z=24, rl=1, rs=1.2, line='soft')
    f.add(f.rect(-1.5, -31 + b, 1.5, -27 + b), 'brass', z=24.5, rl=1, rs=1.2, line='hard')
    col = f.ell(0, -47.5 + ub, 7.6, 3.0) & ~f.ell(0, -46.0 + ub, 4.8, 2.6)
    f.add(col, 'navy', z=36, rl=1.4, rs=2, line='hard', cast=(0, 1, 1))


def lit_plane(f, X, Y, t, cx, cy, rx, ry):
    """v2 (asset gate, volume): the plane of the back or shoulder that faces the upper-left light
    takes the light tone, so a broad cloth area shows lit, base and shadow planes.  cx is in
    screen terms (- = toward the light); the mirrored facings are handled."""
    sx = -1 if f.flip else 1
    m = (((X - cx * sx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0) & (t == 2)
    out = t.copy()
    out[m] = 3
    return out


def torso_north(f, P, b, ub):
    body = f.ell(0, -38 + ub, 10.2, 10) | f.rect(-9.5, -40 + ub, 9.5, -29 + b)
    f.add(body, 'navy', z=20, rl=2.8, rs=3.6, tl=0.34, vgrad=0.55, line='hard',
          tonemap=lambda X, Y, t: lit_plane(f, X, Y, np.where((np.abs(np.abs(X) - 4.5) < 0.5) & (Y > -45 + ub) & (Y < -31 + b) & (t >= 2), 1, t),
                                            -4.5, -41 + ub, 4.0, 4.5))
    lag = P['lag']
    for s in (-1, 1):
        tail = f.poly([(0.5 * s, -27 + b), (9.8 * s, -30 + b), (12.0 * s + lag * 0.3, -11.5 + b), (2.4 * s + lag * 0.3, -12.5 + b)])
        f.add(tail, 'navy', z=22, rl=2.6, tl=0.34, rs=3.0, vgrad=0.4, line='hard',
              tonemap=lambda X, Y, t, s=s: np.where((np.abs(X - 6 * s - (Y + 20 - b) * 0.08 * s) < 0.55) & (Y > -25 + b) & (Y < -13 + b) & (t >= 2), 1, t))
    f.add(f.rect(-10, -31.5 + b, 10, -28.5 + b), 'scab', z=24, rl=1, rs=1.2, line='soft')
    for s in (-1, 1):
        f.add(f.rect(2.5 * s - 1, -28 + b, 2.5 * s + 1, -26.4 + b), 'brass', z=24.5, flat=3, line=None)
    col = f.ell(0, -47.5 + ub, 7.6, 3.0)
    f.add(col, 'navy', z=36, rl=1.4, rs=2, line='hard')
    f.detail(f.rect(-6, -47 + ub, 6, -46 + ub), ('gold', 2), solid=False, z=36.1)


def torso_side(f, P, b, ub, tx, west):
    lag = P['lag']
    tail = f.poly([(-7.5 + tx, -31 + b), (-2.0, -29 + b), (-4.5, -12 + b), (-11.5 - lag, -11 + b), (-10.5 - lag * 0.5, -22 + b)])
    f.add(tail, 'navy', z=7, rl=1.6, rs=2.8, vgrad=0.4, dim=1, line='hard')
    tail2 = f.poly([(-7.0 + tx, -31 + b), (-1.0, -29 + b), (-2.5, -13 + b), (-8.5 - lag, -11.5 + b), (-9.5 - lag * 0.5, -22 + b)])
    f.add(tail2, 'navy', z=13, rl=2.6, tl=0.34, rs=3.0, vgrad=0.4, line='hard')
    body = f.ell(0.5 + tx, -38 + ub, 8.0, 10) | f.poly([(-7 + tx * 0.5, -29 + b), (-7.5 + tx, -40 + ub), (8 + tx, -40 + ub), (8.2 + tx * 0.5, -29 + b)])
    body |= f.poly([(-7 + tx * 0.5, -29 + b), (8.2, -29 + b), (3.0, -22 + b), (-6.5, -21 + b)])
    f.add(body, 'navy', z=20, rl=2.8, rs=3.6, tl=0.34, vgrad=0.55, line='hard')
    f.add(f.poly([(5.5 + tx, -48 + ub), (8.5 + tx, -46 + ub), (8.4 + tx, -39 + ub), (6.5 + tx, -38 + ub)]), 'cream', z=21, rl=1, rs=1.4, line='hard')
    lap = f.poly([(5.0 + tx, -48.5 + ub), (7.0 + tx, -45 + ub), (6.5 + tx, -37.5 + ub), (3.5 + tx, -41 + ub)])
    f.add(lap, 'navy', z=22, rl=1.4, rs=2, line='soft')
    f.detail(f.seg(5 + tx, -48 + ub, 6.5 + tx, -38 + ub), ('gold', 2), solid=False, z=22.1)
    for y in (-36, -33):
        f.add(f.rect(6.0 + tx, y + ub, 8.0 + tx, y + 1.6 + ub), 'brass', z=23, flat=3, line=None)
    f.add(f.poly([(-7.5, -30.5 + b), (8.6, -30.5 + b), (8.6, -27.5 + b), (-7.5, -27.5 + b)]), 'scab', z=24, rl=1, rs=1.2, line='soft')
    f.add(f.rect(6.6, -31 + b, 9.0, -27 + b), 'brass', z=24.5, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0.5 + tx, -47.5 + ub, 6.4, 2.8), 'navy', z=36, rl=1.4, rs=2, line='hard', cast=(0, 1, 1))


# ------------------------------------------------------------------------------------ build
def _leg(f, R, up, lo, kn3, foot3, lat, far, z):
    dim = 1 if far else 0
    f.add(up | lo, 'trouser_v', z=z, rl=1.6, rs=2.6, vgrad=0.2, dim=dim, line='hard')
    if R.diag:
        import surf
        surf.boot_3q(f, R, foot3, 'leather', z + 1, dim=dim, shaft=8, shade=dict(rl=2.2, tl=0.34, rs=2.0, vgrad=0.3))
    else:
        _boot(f, R, foot3, z, far)


def _lit(p, f=None, cx=None):
    if p is not None:
        p.rl, p.tl = 2.2, 0.34
        if f is not None:
            import surf
            p.tonemap = lambda X, Y, t: surf.cyl_highlight(f, X, Y, t, cx)
    return p


def _boot(f, R, foot3, z, far, shaft=8):
    import surf
    """Tall riding boot (v2: morel.boot with a wider lit edge and a darker foot, so the shaft
    reads as a cylinder: asset gate, volume)."""
    from parts import boot_side, boot_front
    fx, fy = R.p(foot3)
    dim = 1 if far else 0
    if R.side:
        _lit(boot_side(f, fx, fy, 'leather', z=z + 1, dim=dim), f, fx + 1.0)
        f.add(f.rect(fx - 3.6, fy - 7 - shaft, fx + 2.8, fy - 6), 'leather', z=z + 1.1, rl=2.2, tl=0.34, rs=2.0, vgrad=0.3, dim=dim, line='hard',
              tonemap=lambda X, Y, t: surf.cyl_highlight(f, X, Y, t, fx - 0.4))
        f.add(f.rect(fx - 4.0, fy - 7.5 - shaft, fx + 3.2, fy - 5.5 - shaft), 'leather', z=z + 1.2, flat=3 if not dim else 2, line='hard')
    else:
        _lit(boot_front(f, fx, fy, 'leather', z=z + 1, dim=dim), f, fx)
        f.add(f.rect(fx - 3.8, fy - 7 - shaft, fx + 3.8, fy - 6) | f.ell(fx, fy - 7 - shaft, 3.8, 1.6), 'leather', z=z + 1.1,
              rl=2.2, tl=0.34, rs=2.0, vgrad=0.3, dim=dim, line='hard',
              tonemap=lambda X, Y, t: surf.cyl_highlight(f, X, Y, t, fx - 0.4))
        f.add(f.rect(fx - 4.2, fy - 7.5 - shaft, fx + 4.2, fy - 5.5 - shaft), 'leather', z=z + 1.2, flat=3, line='hard')


def _arm(f, R, sh3, h3, pole, z, far):
    up, lo, el3 = R.limb(sh3, h3, 8.0, 8.4, 3.2, 3.0, 2.8, pole)
    dim = 1 if far else 0
    f.add(up, 'navy', z=up_z(R, z, far), rl=2.2, tl=0.34, rs=2.4, line='hard', dim=dim, cast=(1, 1, 1) if not dim else None)   # v2: a lit sleeve plane
    f.add(lo, 'navy', z=z - 0.05, rl=2.2, tl=0.34, rs=2.4, line='hard', dim=dim, cast=(1, 1, 1) if not dim else None)
    ex, ey = R.p(el3)
    cx, cy = R.p(h3)
    ux, uy = cx - ex, cy - ey
    L = math.hypot(ux, uy) or 1
    ux, uy = ux / L, uy / L
    k = min(1.0, L / 6.0)
    c = f.cap(cx - ux * 5.0 * k, cy - uy * 5.0 * k, cx - ux * 2.8 * k, cy - uy * 2.8 * k, 3.4)
    f.add(c, 'cream', z=z + 0.1, rl=1.2, rs=1.8, line='hard', dim=dim)
    return el3


def _sab_clear(h3, d3, L=23.0, margin=1.5):
    """v2: the sabre's point never goes into the ground (a crouch or a kneel lowers the hand):
    the point is lifted toward the horizontal until it clears."""
    import parts
    d = np.array(nrm(d3))
    for _ in range(30):
        tip = np.array(h3) + d * (L + 3.5)
        low = max(parts.proj(fc, tuple(tip))[1] for fc in parts.FACINGS8)   # stays in the cell in every facing
        if tip[1] >= margin and low <= 5.0:
            break
        d = np.array(nrm(tuple(d + np.array([0.0, 0.1, 0.0]))))
    return tuple(d)


def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    west = facing == 'W'
    hip3, sh3, head3 = frame(P, 23.0, 20.0, 16.0)
    body_off = (P['hipx'], -P['crouch'] - P['bob'], 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    b = hy + 23.0
    ub = sy + 43.0
    tx = sx - hx
    shR = add3(sh3, (0.0, -1.0, SHW))
    shL = add3(sh3, (0.0, -1.0, -SHW))
    hR = add3(P['handR'] or REST_R, body_off)
    hL = add3(P['handL'] or REST_L, body_off)
    hR = reach(shR, hR, 16.4)
    hL = reach(shL, hL, 16.4)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    # scabbard on the right hip, hanging back and down
    s3 = add3(SCAB, body_off)
    sd = (-0.62, -0.78, 0.08)
    if s3[1] < 20.0:                     # kneeling: the scabbard tip rests back along the ground
        sd = (-0.95, -0.25 * max(0.0, s3[1] - 6.0) / 14.0 - 0.02, 0.1)
    (ux, uy), Ls = sdir(R, s3, sd)
    sxp, syp = R.p(s3)
    zs = 25.0 if R.d(add3(s3, mul3(nrm(sd), 11.0))) > 2 else 4.0
    scabbard(f, sxp, syp, math.atan2(ux, uy), zs, dim=1 if R.far(1) else 0, length=max(6.0, 22 * Ls))
    legs(f, R, P, hip3, _leg, 8.9, 8.7)
    if R.diag:
        torso_3q(f, R, P, hip3, sh3)
    else:
      with Shift(f, hx, 0):
        if facing == 'S':
            torso_south(f, P, b, ub)
        elif facing == 'N':
            torso_north(f, P, b, ub)
        else:
            torso_side(f, P, b, ub, tx, west)
    out = {}
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        pole = P['pole' + key] or (-1.0, -0.25, 0.6 * lat)
        z = arm_z(R, P, key, hh)
        far = R.far(lat)
        el3 = _arm(f, R, sh, hh, pole, z, far)
        out[key] = (el3, hh, z, far)
    for key in ('R', 'L'):
        el3, hh, z, far = out[key]
        hxp, hyp = R.p(hh)
        dim = 1 if far else 0
        if key == 'R':
            lantern(f, hxp, hyp + 0.5, z + 0.3, dim=dim if P['lamp'] <= 1 else 0, lamp=P['lamp'], sw=P['lsw'])
            f.anchor('lantern', hxp, hyp + 10)
            fist(f, hxp, hyp, z + 0.8, 'skin_v', dim=dim, grip=(1.0, 0.0), r=3.0)
        else:
            d3 = _sab_clear(hh, P['sab'])
            (ux, uy), Ls = sdir(R, hh, d3)
            ang = math.atan2(ux, uy)
            tip = sabre(f, hxp, hyp, ang, z + 0.4, dim=dim, length=max(3.0, 23 * Ls))
            f.anchor('blade_tip', *tip)
            fist(f, hxp, hyp, z + 0.8, 'skin_v', dim=dim, grip=(ux, uy), r=3.0)
            sabre_guard(f, hxp, hyp, ang, z + 0.9, dim=dim)
    hx2, hy2 = R.p(head3)
    if R.diag:
        with Shift(f, hx2, 0):
            head_3q(f, P, hy2, R.back, stud=(facing in ('SE', 'NE')))
        return
    with Shift(f, hx2, 0):
        if facing == 'S':
            head_south(f, P, hy2)
        elif facing == 'N':
            head_north(f, P, hy2)
        else:
            head_side(f, P, hy2, 0.0, west)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in FLIP))
    f.despeckle = True               # v2: no lone rim or shade pixels
    build(f, facing, P)
    return f


# ================================================================== contract v2: 3/4 facings
# SE, NE (and the mirrored SW, NW) from the same 3D body (surf.py): the coat is a cylinder round
# the body axis; lapels, cravat, buttons, belt, cut-away fronts and the two tails are panels and
# points on it, drawn where they face the camera.  The head wraps the S and N heads' shapes onto
# a sphere.  The sabre (LEFT hand), lantern (RIGHT hand) and scabbard (RIGHT hip) come from the
# rig as in every facing.
CW, CD = 10.0, 8.0               # coat half width and half depth at the chest
WW, WD = 9.6, 7.6                # at the waist
HEAD_R = 9.2


def torso_3q(f, R, P, hip3, sh3):
    import surf
    hup, sup = hip3[1], sh3[1]
    cs, ch = (sh3[0], 0, 0), (hip3[0], 0, 0)
    sx, sy = R.p(sh3)
    hx, hy = R.p(hip3)
    lag = P['lag']
    back = R.back
    # tails: the coat's two tails hang from the back of the waist down to the knees
    for s in (1, -1):
        c = (hip3[0] - lag * 0.35, 0, 0)
        th0, th1 = s * (math.pi - 1.35), s * (math.pi - 0.06)
        m = surf.panel(f, R, c, th0, th1, hup + 7.0, max(1.0, hup - 11.5 - P['crouch'] * 0.3), WW + 0.4, WD + 0.4, flare=1.3)   # kneeling, the tails rest on the ground
        (tx_, ty_), tv = surf.ring(R, c, hup, WW, WD, s * (math.pi - 0.7))
        if back:
            z, dim = 22, 0
        elif R.d((0, 0, s)) > 0:      # the tail on the near side shows beside the near leg
            z, dim = 13, 0
        else:
            z, dim = 5, 1
        f.add(m, 'navy', z=z + (0.1 if s > 0 else 0), rl=2.6, tl=0.34, rs=3.0, vgrad=0.4, dim=dim, line='hard',
              tonemap=(lambda X, Y, t, m=m: surf.left_light(m, t)) if m is not None else None)
    # body
    x0, x1 = surf.extremes(R, cs, sup - 5, CW, CD)
    w0, w1 = surf.extremes(R, ch, hup + 6, WW, WD)
    body = f.ell((x0 + x1) / 2, sy + 5, (x1 - x0) / 2, 10) | f.poly([(x0 + 0.5, sy + 3), (x1 - 0.5, sy + 3), (w1, hy - 6), (w0, hy - 6)])
    body &= f.Y < hy - 5.5
    f.add(body, 'navy', z=20, rl=2.8, rs=3.6, tl=0.34, vgrad=0.55, line='hard',
          tonemap=(lambda X, Y, t: lit_plane(f, X, Y, _back_seams_3q(X, Y, t, R, cs, sup, hup), (x0 + x1) / 2 * (-1 if f.flip else 1) - 3.5, sy + 3, 3.6, 4.2))
          if back else (lambda X, Y, t: lit_plane(f, X, Y, t, (x0 + x1) / 2 * (-1 if f.flip else 1) - 3.0, sy + 4, 3.4, 4.6)))
    if not back:
        # cut-away fronts: the coat skirts flare over the hips, open at the front
        for s in (1, -1):
            m = surf.panel(f, R, ch, s * 0.28, s * 1.5, hup + 6.5, lambda th: hup - 1.5 + 2.5 * (1.5 - abs(th)), WW + 0.3, WD + 0.3,
                           flare=1.15, vmin=0.0)
            if m is not None:
                f.add(m, 'navy', z=20.5, rl=2.2, tl=0.34, rs=2.6, vgrad=0.3, line='hard')
        # cravat V and lapels
        (vx, vy), vv = surf.ring(R, cs, sup + 4.5, CW, CD, 0.0)
        if vv > 0.1:
            k = min(1.0, vv + 0.25)
            f.add(f.poly([(vx - 4 * k, vy - 0.5), (vx + 4 * k, vy - 0.5), (vx, vy + 10)]), 'cream', z=21, rl=1.2, rs=1.6, line='hard')
            f.add(f.ell(vx, vy + 2.0, 2.0 * k, 1.6) | f.poly([(vx - 1.5 * k, vy + 2.5), (vx + 1.5 * k, vy + 2.5), (vx + 0.8, vy + 6.5),
                                                              (vx - 0.8, vy + 6.5)]), 'cream', z=21.2, rl=1, rs=1.2, line='soft')
        for s in (1, -1):
            a = surf.ring(R, cs, sup + 5.0, CW + 0.3, CD + 0.3, s * 0.42)
            b = surf.ring(R, cs, sup + 3.0, CW + 0.3, CD + 0.3, s * 0.85)
            c = surf.ring(R, cs, sup - 2.0, CW + 0.3, CD + 0.3, s * 0.62)
            d = surf.ring(R, cs, sup - 5.5, CW + 0.3, CD + 0.3, s * 0.05)
            if min(a[1], d[1]) < -0.05:
                continue
            lap = f.poly([a[0], b[0], c[0], d[0]])
            f.add(lap, 'navy', z=22, rl=2.0, tl=0.34, rs=2, line='soft')
            f.detail(f.seg(a[0][0], a[0][1], d[0][0], d[0][1]) & lap, ('gold', 2), solid=False, z=22.1)
            if b[1] > 0.1:
                f.detail(f.seg(b[0][0], b[0][1], c[0][0], c[0][1]) & lap, ('gold', 2), solid=False, z=22.1)
        # buttons: two rows
        for s in (1, -1):
            for up in (sup - 7.0, sup - 10.0):
                (bx, by), bv = surf.ring(R, cs, up, CW + 0.3, CD + 0.3, s * 0.36)
                if bv > 0.2:
                    f.add(f.rect(bx - 1, by, bx + 1, by + 1.6), 'brass', z=23, flat=3, line=None)
    # belt and buckle
    belt = surf.band(f, R, ch, hup + 4.5, hup + 7.5, WW + 0.5, WD + 0.5)
    if belt is not None:
        f.add(belt, 'scab', z=24, rl=1, rs=1.2, line='soft')
    (bx, by), bv = surf.ring(R, ch, hup + 6.0, WW + 0.7, WD + 0.7, 0.0)
    if bv > 0.15:
        f.add(f.rect(bx - 1.5, by - 2, bx + 1.5, by + 2), 'brass', z=24.5, rl=1, rs=1.2, line='hard')
    if back:
        for s in (1, -1):
            (bx, by), bv = surf.ring(R, ch, hup + 3.5, WW + 0.7, WD + 0.7, s * (math.pi - 0.3))
            if bv > 0.1:
                f.add(f.rect(bx - 1, by, bx + 1, by + 1.6), 'brass', z=24.5, flat=3, line=None)
    # standing collar
    (cx, cy) = R.p((sh3[0], sup + 4.5, 0.0))
    col = f.ell(cx, cy, 7.4, 3.0)
    (vx, vy), vv = surf.ring(R, cs, sup + 4.5, 6.5, 5.0, 0.0)
    if vv > 0.2:
        col &= ~f.ell(vx, vy + 1.4, 3.6, 2.4)
    f.add(col, 'navy', z=36, rl=1.4, rs=2, line='hard', cast=(0, 1, 1))


def _back_seams_3q(X, Y, t, R, cs, sup, hup):
    import surf
    out = t.copy()
    for s in (1, -1):
        (x0, y0), v0 = surf.ring(R, cs, sup - 2, CW, CD, s * (math.pi - 0.45))
        (x1, y1), v1 = surf.ring(R, cs, hup + 7, CW, CD, s * (math.pi - 0.45))
        if min(v0, v1) < 0.1:
            continue
        L = math.hypot(x1 - x0, y1 - y0) or 1
        d = np.abs((X - x0) * (y1 - y0) - (Y - y0) * (x1 - x0)) / L
        m = (d < 0.55) & (Y > y0) & (Y < y1) & (t >= 2)
        out[m] = 1
    return out


def head_3q(f, P, hy, back, stud):
    """Velvet's head three-quarter (drawn round x = 0 inside Shift, the face toward +x): the
    profile head's skull and hair turned a quarter back toward the camera, so both eyes show
    (the far one near the cheek's edge), the nose sits inside the face and the near ear moves
    back.  From behind (NE): the back of the head with the near ear only."""
    if back:
        f.add(f.ell(7.6, hy + 1.8, 1.8, 2.6), 'skin_v', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(0.5, hy + 1.2, 8.0, 9.0), 'skin_v', z=40, rl=2.0, rs=3.0, line='hard')
        hair_mass(f, 0.5, hy, 2)
        if stud:
            f.dot(8.0, hy + 3.5, ('gold', 3))
        return
    f.add(f.ell(1.2, hy + 1.2, 7.8, 9.0), 'skin_v', z=40, rl=2.0, rs=3.0, vgrad=0.35, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: lit_plane(f, X, Y, t, (1.2) * (-1 if f.flip else 1) - 3.0, hy + 3.5, 2.4, 2.6))   # v2: the lit cheek plane
    hair_mass(f, -0.5, hy, 1)
    f.add(f.ell(-3.0, hy + 2.2, 1.7, 2.5), 'skin_v', z=45, rl=1, rs=1.2, line='hard')
    f.dot(-3.0, hy + 2.2, ('skin_v', 1))
    if stud:
        f.dot(-3.0, hy + 4, ('gold', 3))
    ey = hy + 1
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    for x in (1, 6):
        if _eyes_shut(P):
            f.detail(f.rect(x, ey + 2, x + 2, ey + 3), EYE)
        else:
            eye(f, x, ey, 3)
    f.detail(f.rect(0, ey - 2 + lift, 3, ey - 1 + lift), ('silver', 1))
    f.detail(f.rect(5, ey - 2 + lift, 8, ey - 1 + lift), ('silver', 1))
    f.detail(f.rect(4, hy + 4, 5, hy + 5), ('skin_v', 3))
    f.detail(f.rect(5, hy + 5, 6, hy + 6), ('skin_v', 1))
    f.detail(f.rect(3, hy + 7, 6, hy + 8), ('skin_v', 0))
    f.detail(f.rect(-1, hy + 5, 1, hy + 6), ('blush_v', 1))

"""Clack: older, broad human heavy gunner.  Bald tanned scalp with a short grey fringe, bushy grey
brows and a big grey walrus moustache, work goggles pushed up on the forehead, a teal work shirt
with rolled sleeves, blue work trousers with cargo pockets, black boots, a dark webbing shoulder
harness (two straps over the shoulders, an X across the back, a leather pad on the right shoulder).

Equipment, each exactly once:
  - the rocket launcher, carried on the RIGHT shoulder: gunmetal tube with orange bands, brass
    muzzle ring with the loaded rocket's nose in the bore, a flared exhaust bell at the rear that
    clears his back and head, and TWO attached grips under the tube ahead of the shoulder (the
    trigger grip, right hand, and the fore grip, left hand when aiming);
  - the pressure chamber: a separate brass cylinder with a gauge, clamped under the tube behind
    the shoulder;
  - the spare-rocket rack: a leather holder with two rockets on the front LEFT of the belt;
  - the loader and brace: a folding gunmetal frame carried flat on the harness on his back.
    The special (Loader Brace) unfolds it: the loader arm rises over the right shoulder and holds a
    rocket at the tube's breech, the brace strut props the tube's rear on the harness.  It stays
    attached to him and to the launcher, so he still walks; it folds back flat on exit.

Pass 2: one pose-driven build for all four facings (parts.Rig), like bramble.py.  The launcher is
placed in body space by its tube centre (lpos) and muzzle direction (ldir); the grips, chamber,
loader end, and the hands that hold them follow it.

Equipment tags: launcher, chamber, rack, loader.  Effects drawn in the body frame for one or two
drawings (tag fx): the rear backblast at the bell and the muzzle puff; they sit clear of the body."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, boot_side, boot_front, EYE, Rig
import palette  # noqa: F401
import anim
import turn
import surf
from brine import add3, nrm, shoulders

ID = 'clack'
NAME = 'Clack'
HEIGHT = 76
BAND = (72, 82)

mat('clack_teal',   ['#0E3640', '#155C68', '#228E9A', '#58C0C0'])
mat('clack_work',   ['#151E46', '#1C3676', '#2A54A2', '#4C7CC6'])
mat('clack_orange', ['#5E2408', '#A8480E', '#E2822A', '#FFBE5C', '#FFE6A8'])
mat('clack_web',    ['#1C1A1E', '#2C2A30', '#423E44', '#5E5860'])
mat('clack_skin',   ['#5E2E26', '#8E4E38', '#BC7A54', '#E0A47A'])
mat('clack_grey',   ['#4E4A58', '#807C88', '#B0ACAC', '#E2DED2'])
mat('clack_lens',   ['#101820', '#1C2C3A', '#2E4A5E', '#6A98B0'])
mat('clack_boot',   ['#141418', '#24242C', '#3A3A44', '#56565E'])

SHW = 12.0
ARM = (9.8, 9.3)
LPOS0 = (-0.5, 48.0, 13.0)          # tube centre resting on the right shoulder pad
LDIR0 = (1.0, 0.0, 0.0)
FIST_L = (2.0, 27.0, -16.5)          # left fist on the left hip


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0, blink=False, face=None, brow=0,
             footR=(0.5, 0.0), footL=(-1.5, 0.0), stance=6.5,
             lpos=None, ldir=None, handR=None, handL=None, lmode='hip', poleR=None, poleL=None, twist=None,
             rocket=True, rack=2, hrocket=False, loader=0.0, blast=0, puff=0, valve=False)
    p.update(k)
    return p


def frame3(d3):
    D = nrm(d3)
    w = np.array([0.0, -1.0, 0.0])
    Dn = w - D * w.dot(D)
    if np.linalg.norm(Dn) < 1e-3:
        Dn = np.array([-1.0, 0.0, 0.0])
    Dn = nrm(Dn)
    return D, Dn, np.cross(D, -Dn)


# ------------------------------------------------------------------------------------ face bits
def brows(f, x, y, w=5):
    f.detail(f.rect(x, y, x + w, y + 1), ('clack_grey', 2))
    f.detail(f.rect(x, y + 1, x + w, y + 2), ('clack_grey', 1))


def _scalp(X, Y, t, cx, hy):
    out = t.copy()
    r = ((X - cx + 3.0) / 3.6) ** 2 + ((Y - hy + 6.0) / 2.0) ** 2
    out[(r < 1) & (t >= 2)] = 3
    return out


def _whisk(X, Y, t, x0, hy):
    out = t.copy()
    for k in (-4.5, -1.5, 1.5, 4.5):
        m = (abs(X - x0 - k) < 0.55) & (Y > hy + 6.5)
        out[m & (t >= 2)] = 1
    return out


def head_south(f, P, x0, hy):
    f.add(f.ell(x0 - 9.4, hy + 1.5, 2.0, 3.0) | f.ell(x0 + 9.4, hy + 1.5, 2.0, 3.0), 'clack_skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy, 9.4, 9.8), 'clack_skin', z=40, rl=2.2, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _scalp(X, Y, t, x0, hy))
    for s in (-1, 1):
        f.add(f.ell(x0 + 8.6 * s, hy - 1.5, 2.0, 3.6), 'clack_grey', z=41, rl=1, rs=1.6, line='shade')
    f.add(f.rect(x0 - 9.4, hy - 6, x0 + 9.4, hy - 4) & f.ell(x0, hy, 9.4, 9.8), 'clack_web', z=42, flat=1, line=None)
    for s in (-1, 1):
        f.add(f.ell(x0 + 3.6 * s, hy - 5.5, 3.0, 2.4), 'brass', z=42.5, rl=1, rs=1.2, line='hard')
        f.add(f.ell(x0 + 3.6 * s, hy - 5.5, 1.8, 1.3), 'clack_lens', z=42.6, flat=2, line=None)
        f.dot(x0 + 3.6 * s - 1, hy - 6, ('clack_lens', 3), z=42.6)
    ey = hy + 0.5
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(x0 - 5, ey + 2, x0 - 3, ey + 3), EYE)
        f.detail(f.rect(x0 + 3, ey + 2, x0 + 5, ey + 3), EYE)
    else:
        eye(f, x0 - 5, ey, 3)
        eye(f, x0 + 3, ey, 3)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    brows(f, x0 - 7, ey - 2.5 + lift)
    brows(f, x0 + 2, ey - 2.5 + lift)
    f.add(f.ell(x0, hy + 4.0, 1.8, 1.6), 'clack_skin', z=43, rl=1, rs=1.2, line='hard')
    mo = f.ell(x0 - 3.2, hy + 6.6, 3.8, 2.0) | f.ell(x0 + 3.2, hy + 6.6, 3.8, 2.0) | f.ell(x0 - 6.2, hy + 8.0, 1.6, 2.4) | \
        f.ell(x0 + 6.2, hy + 8.0, 1.6, 2.4) | f.rect(x0 - 3, hy + 5.5, x0 + 3, hy + 8)
    f.add(mo, 'clack_grey', z=44, rl=1.4, rs=1.8, line='hard', tonemap=lambda X, Y, t: _whisk(X, Y, t, x0, hy))
    f.detail(f.rect(x0 - 6, hy + 2, x0 - 4, hy + 3), ('blush', 1))
    f.detail(f.rect(x0 + 4, hy + 2, x0 + 6, hy + 3), ('blush', 1))


def _back_hair(X, Y, t, x0, hy):
    """Combed strands in the back fringe: a few irregular strokes curving down toward the nape."""
    out = t.copy()
    for (sx, sy, k, L) in ((-6.0, -1.0, 0.35, 5), (-2.5, 0.5, 0.15, 6), (2.0, -1.5, -0.1, 5), (5.5, 1.0, -0.3, 4)):
        d = np.abs((X - x0 - sx) - k * (Y - hy - sy))
        m = (d < 0.5) & (Y - hy >= sy) & (Y - hy < sy + L) & (t >= 2)
        out[m] = t[m] - 1
    return out


def head_north(f, P, x0, hy):
    f.add(f.ell(x0 - 9.4, hy + 1.5, 2.0, 3.0) | f.ell(x0 + 9.4, hy + 1.5, 2.0, 3.0), 'clack_skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy, 9.4, 9.8), 'clack_skin', z=40, rl=2.2, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _scalp(X, Y, t, x0, hy))
    # 26 Oct (squint test): from behind the grey fringe covers the back of the skull from just under
    # the strap to the nape, and the strap is a thin mid-tone line high on the crown, so the back never
    # repeats the front's dark goggle band over a bare face over a grey beard
    fr = f.ell(x0, hy, 9.6, 9.9) & (f.Y > hy - 3.0)
    f.add(fr, 'clack_grey', z=41, rl=1.4, rs=2.4, line='shade', tonemap=lambda X, Y, t: _back_hair(X, Y, t, x0, hy))
    f.add(f.rect(x0 - 9.4, hy - 6.5, x0 + 9.4, hy - 5.5) & f.ell(x0, hy, 9.4, 9.8), 'clack_web', z=42, flat=2, line=None)
    f.add(f.rect(x0 - 1.5, hy - 7.0, x0 + 1.5, hy - 5.0), 'brass', z=42.5, rl=1, rs=1, line='hard')      # the strap's buckle
    for s in (-1, 1):
        f.add(f.ell(x0 + 7.6 * s, hy + 8.0, 1.6, 2.2) & ~f.ell(x0, hy, 9.4, 9.8), 'clack_grey', z=39.5, rl=1, rs=1.2, line='hard')


def head_side(f, P, hx, hy, z0=40):
    f.add(f.ell(hx + 1.5, hy, 8.6, 9.8), 'clack_skin', z=z0, rl=2.2, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _scalp(X, Y, t, hx, hy))
    f.add(f.ell(hx + 9.6, hy + 3.2, 2.0, 2.0), 'clack_skin', z=z0 + 0.5, rl=1, rs=1.2, line='hard')
    fr = f.ell(hx - 4.5, hy + 3.0, 4.6, 3.6) & f.ell(hx + 1.5, hy, 8.6, 9.8)
    f.add(fr, 'clack_grey', z=z0 + 1, rl=1.2, rs=2.0, line='shade')
    f.add(f.ell(hx - 1.5, hy + 1.5, 1.8, 2.6), 'clack_skin', z=z0 + 2, rl=1, rs=1.2, line='shade')
    f.add(f.rect(hx - 7, hy - 6.5, hx + 10, hy - 4.5) & f.ell(hx + 1.5, hy, 8.6, 9.8), 'clack_web', z=z0 + 2.5, flat=1, line=None)
    f.add(f.ell(hx + 7.5, hy - 6.0, 2.0, 2.6), 'brass', z=z0 + 3, rl=1, rs=1.2, line='hard')
    f.add(f.ell(hx + 8.6, hy - 6.0, 0.9, 1.6), 'clack_lens', z=z0 + 3.1, flat=2, line=None)
    ey = hy + 0.5
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(hx + 5, ey + 2, hx + 7, ey + 3), EYE)
    else:
        eye(f, hx + 5, ey, 3)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    brows(f, hx + 3.5, ey - 2.5 + lift)
    mo = f.ell(hx + 7.0, hy + 6.6, 3.8, 2.1) | f.ell(hx + 5.2, hy + 8.4, 1.8, 2.4)
    f.add(mo, 'clack_grey', z=z0 + 4, rl=1.4, rs=1.8, line='hard', cast=(0, 1, 1))
    f.detail(f.rect(hx + 3, hy + 2.5, hx + 5, hy + 3.5), ('blush', 1))


def head_3q(f, P, hx, hy, back):
    """Contract v2 three-quarter head (turn in-betweens; SE / NE drawn, SW / NW mirrored): the
    profile head turned a quarter toward the camera (front) or away (back)."""
    if back:
        f.add(f.ell(hx + 8.6, hy + 1.5, 2.0, 3.0), 'clack_skin', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(hx + 0.6, hy, 9.2, 9.8), 'clack_skin', z=40, rl=2.2, rs=3.2, line='hard', cast=(0, 2, 1),
              tonemap=lambda X, Y, t: _scalp(X, Y, t, hx + 0.6, hy))
        fr = f.ell(hx + 0.6, hy, 9.4, 9.9) & (f.Y > hy - 3.0)
        f.add(fr, 'clack_grey', z=41, rl=1.4, rs=2.4, line='shade', tonemap=lambda X, Y, t: _back_hair(X, Y, t, hx + 0.6, hy))
        f.add(f.rect(hx - 8.6, hy - 6.5, hx + 9.8, hy - 5.5) & f.ell(hx + 0.6, hy, 9.2, 9.8), 'clack_web', z=42, flat=2, line=None)
        f.add(f.ell(hx + 8.0, hy - 5.5, 1.6, 2.2), 'brass', z=42.5, rl=1, rs=1, line='hard')
        f.add(f.ell(hx + 8.0, hy + 8.0, 1.5, 2.1) & ~f.ell(hx + 0.6, hy, 9.2, 9.8), 'clack_grey', z=39.5, rl=1, rs=1.2, line='hard')
        return
    f.add(f.ell(hx + 1.0, hy, 9.0, 9.8), 'clack_skin', z=40, rl=2.2, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _scalp(X, Y, t, hx, hy))
    fr = f.ell(hx - 5.5, hy + 2.0, 3.6, 3.8) & f.ell(hx + 1.0, hy, 9.0, 9.8)                    # the near fringe
    f.add(fr, 'clack_grey', z=41, rl=1.2, rs=2.0, line='shade')
    f.add(f.ell(hx + 9.0, hy - 1.0, 1.3, 3.0) & ~f.ell(hx + 1.0, hy, 9.0, 9.8), 'clack_grey', z=39.5, rl=1, rs=1.2, line='shade')   # far fringe
    f.add(f.ell(hx - 3.2, hy + 1.5, 1.8, 2.6), 'clack_skin', z=42, rl=1, rs=1.2, line='shade')     # near ear
    f.add(f.rect(hx - 8, hy - 6.5, hx + 10, hy - 4.5) & f.ell(hx + 1.0, hy, 9.0, 9.8), 'clack_web', z=42.5, flat=1, line=None)
    for x, r in ((hx + 1.5, 2.6), (hx + 6.8, 2.1)):                                               # goggles on the strap
        f.add(f.ell(x, hy - 5.5, r, 2.2), 'brass', z=43, rl=1, rs=1.2, line='hard')
        f.add(f.ell(x, hy - 5.5, r - 1.0, 1.2), 'clack_lens', z=43.1, flat=2, line=None)
    ey = hy + 0.5
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(hx + 1, ey + 2, hx + 3, ey + 3), EYE)
        f.detail(f.rect(hx + 6, ey + 2, hx + 8, ey + 3), EYE)
    else:
        eye(f, hx + 1, ey, 3)
        eye(f, hx + 6, ey, 3)
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    brows(f, hx - 0.5, ey - 2.5 + lift, w=4)
    brows(f, hx + 5.0, ey - 2.5 + lift, w=4)
    f.add(f.ell(hx + 5.5, hy + 4.0, 1.8, 1.6), 'clack_skin', z=43.5, rl=1, rs=1.2, line='hard')
    mo = f.ell(hx + 2.8, hy + 6.6, 3.4, 2.0) | f.ell(hx + 7.6, hy + 6.6, 3.0, 2.0) | f.ell(hx + 0.2, hy + 8.0, 1.6, 2.4) | \
        f.ell(hx + 9.6, hy + 7.8, 1.2, 2.2) | f.rect(hx + 3, hy + 5.5, hx + 8, hy + 8)
    f.add(mo, 'clack_grey', z=44, rl=1.4, rs=1.8, line='hard', tonemap=lambda X, Y, t: _whisk(X, Y, t, hx + 5, hy))
    f.detail(f.rect(hx - 1, hy + 2, hx + 1, hy + 3), ('blush', 1))


# ------------------------------------------------------------------------------------ gear
def _ring(f, R, c3, D, r, mn=1.0):
    """A ring of radius r round the axis D at c3, as a screen ellipse (minor axis at least mn)."""
    cx, cy = R.p(c3)
    ux, uy = R.p(tuple(D))
    L = math.hypot(ux, uy)
    dz = abs(R.d(tuple(D)))
    if L < 0.05:
        return f.ell(cx, cy, r, r * (1 - 0.35 * 0)), (cx, cy)
    ang = math.atan2(uy, ux)
    minor = max(mn, r * min(1.0, dz + 0.15))
    return f.rell(cx, cy, minor, r, ang), (cx, cy)


def launcher(f, R, c3, d3, z, dim=0, rocket=True, near=True, zr=None):
    """The launcher, tube centre c3, muzzle along d3.  Returns 3D key points and screen anchors."""
    D, Dn, Rt = frame3(d3)
    C = np.array(c3, float)

    def p3(a, d=0.0, r=0.0):
        return tuple(C + D * a + Dn * d + Rt * r)

    def at(a, d=0.0, r=0.0):
        return R.p(p3(a, d, r))
    dz = R.d(tuple(D))                   # > 0: the muzzle comes toward the camera
    with f.tagging('launcher'):
        zr = z if zr is None else zr              # rear half's depth (differs when the tube crosses the body)
        tube = f.cap(*at(-16), *at(16), 3.6)
        if zr == z:
            f.add(tube, 'gunmetal', z=z, rl=1.6, rs=2.2, dim=dim, line='hard', cast=(0, 2, 1) if near else None)
        else:
            f.add(f.cap(*at(-1), *at(16), 3.6), 'gunmetal', z=z, rl=1.6, rs=2.2, dim=dim, line='hard')
            f.add(f.cap(*at(-16), *at(-1), 3.6), 'gunmetal', z=zr, rl=1.6, rs=2.2, dim=dim, line='hard', cast=(0, 2, 1))
        for a in (-11, 9):
            band = f.cap(*at(a), *at(a + 2.5), 3.65) & tube
            f.add(band, 'clack_orange', z=(zr if a < 0 else z) + 0.05, rl=1, rs=1.6, dim=dim, line=None)
        # exhaust bell at the rear: a flared, flat-ended cone, open at the back (AUDIT: it must not
        # read as a nose): the open end is always drawn as a rim with a dark throat
        bz = zr + (0.3 if dz < -0.3 else 0.1)
        bell = f.poly([at(-15.5, -3.8), at(-22, -6.0), at(-22, 6.0), at(-15.5, 3.8)]) | f.cap(*at(-15.5), *at(-16.5), 3.9)
        f.add(bell, 'gunmetal', z=bz, rl=1.2, rs=1.8, dim=dim, line='hard')
        ring, bc = _ring(f, R, p3(-22), D, 6.0, mn=2.6)
        f.add(ring, 'gunmetal', z=bz + 0.02, rl=1.2, rs=1.4, dim=dim, line='hard')
        if dz < 0.3:
            th, _ = _ring(f, R, p3(-22.3), D, 4.2, mn=1.4)
            f.add(th, 'clack_web', z=bz + 0.03, flat=0, dim=dim, line=None)
        # muzzle: a wide orange collar, an open brass-edged ring with a dark bore, the rocket nose in it
        mz = at(17.5)
        mzz = z + (0.3 if dz > 0.3 else 0.1)
        f.add(f.cap(*at(14), *at(17.5), 4.8), 'clack_orange', z=mzz, rl=1.2, rs=1.6, dim=dim, line='hard')
        mr, _ = _ring(f, R, p3(17.6), D, 4.8, mn=2.4)
        f.add(mr, 'brass', z=mzz + 0.01, rl=1, rs=1.2, dim=dim, line='hard')
        if dz > -0.6:
            br, _ = _ring(f, R, p3(17.8), D, 3.2, mn=1.3)
            f.add(br, 'clack_web', z=mzz + 0.02, flat=0, dim=dim, line=None)
        if rocket:
            nose = f.poly([at(17.5, -1.8), at(20.0), at(17.5, 1.8)])
            if dz > 0.3:
                nose |= f.ell(*at(18), 1.5, 1.4)
            f.add(nose, 'steel', z=mzz + 0.05, rl=1, rs=1.2, dim=dim, line='hard')
        # the two grips hang under the tube
        f.add(f.cap(*at(4.5, 3), *at(3.5, 8.5), 1.5), 'clack_web', z=z - 0.05, rl=1, rs=1.3, dim=dim, line='hard')
        f.add(f.cap(*at(5.5, 4.5), *at(7.5, 4.5), 0.8), 'gunmetal', z=z - 0.06, flat=0, dim=dim, line='hard')
        f.add(f.cap(*at(11.0, 3), *at(10.5, 8.5), 1.5), 'clack_web', z=z - 0.05, rl=1, rs=1.3, dim=dim, line='hard')
    with f.tagging('chamber'):
        f.add(f.cap(*at(-11.5, 3.2), *at(-10.5, 5.5), 1.0), 'gunmetal', z=zr - 0.02, flat=1, dim=dim, line='hard')
        ch = f.cap(*at(-16, 8), *at(-7, 8), 3.2)
        f.add(ch, 'brass', z=zr - 0.1, rl=1.4, rs=2.0, dim=dim, line='hard')
        g = at(-9.5, 8, 2.5 if R.d(tuple(Rt)) > 0 else -2.5)
        f.add(f.ell(g[0], g[1], 1.6, 1.6) & ch, 'string', z=zr - 0.08, flat=2, dim=dim, line='hard')
        f.dot(g[0] + 0.5, g[1] - 0.5, EYE, z=zr - 0.08)
    return dict(trig3=p3(3.6, 7.0), fore3=p3(10.5, 7.0), muzzle=mz, exhaust=at(-22), chamber3=p3(-11.5, 8.5),
                breech3=p3(-12.5, -3.5), brace3=p3(-6.0, 3.5), muzzle3=p3(19.0), exhaust3=p3(-24.0), D=D, Dn=Dn,
                rocket_load3=p3(-15.0, -6.0))


def rocket_item(f, R, base3, d3, z, dim=0, tag='launcher'):
    """A spare rocket held or cradled: body along d3 from base3, orange nose."""
    D = nrm(d3)
    a, b, c = R.p(tuple(base3)), R.p(tuple(np.array(base3) + D * 6)), R.p(tuple(np.array(base3) + D * 9.5)),
    with f.tagging(tag):
        f.add(f.cap(*a, *b, 2.0), 'gunmetal', z=z, rl=1, rs=1.4, dim=dim, line='hard')
        f.add(f.cap(*b, *c, 2.0, 0.8), 'clack_orange', z=z + 0.02, rl=1.2, rs=1.4, dim=dim, line='hard')


def rack(f, x, y, z, dim=0, side=False, n=2):
    """The spare-rocket rack on the belt: a leather holder with two rockets, noses up; (x, y) is
    the holder's top centre."""
    xs = (x - 2.4, x + 2.4) if not side else (x - 1.2, x + 1.6)
    with f.tagging('rack'):
        for i, rx in enumerate(xs[:n] if n < 2 else xs):
            if n == 1 and i == 0:
                continue
            f.add(f.cap(rx, y + 2, rx, y - 4, 2.1), 'gunmetal', z=z + i * 0.01, rl=1, rs=1.4, dim=dim, line='hard')
            f.add(f.poly([(rx - 2.1, y - 4), (rx + 2.1, y - 4), (rx + 1.0, y - 7.5), (rx, y - 8.5), (rx - 1.0, y - 7.5)]),
                  'clack_orange', z=z + 0.02 + i * 0.01, rl=1.2, rs=1.4, dim=dim, line='hard')
        w = 4.8 if not side else 3.8
        f.add(f.rect(x - w - 0.4, y - 2, x + w + 0.4, y + 4), 'leather', z=z + 0.1, rl=1, rs=1.6, dim=dim, line='hard')
        f.add(f.rect(x - 0.5, y - 1, x + 0.5, y + 3), 'brass', z=z + 0.11, flat=2, dim=dim, line=None)


def fist(f, x, y, z, dim=0, r=3.6):
    f.add(f.ell(x, y, r, r * 0.95), 'clack_skin', z=z, rl=1.4, rs=2.0, dim=dim, line='hard')
    f.add(f.rect(x - r + 0.5, y - r + 0.3, x + r - 0.5, y - r + 1.6) & f.ell(x, y, r, r), 'clack_web', z=z + 0.02, flat=1,
          dim=dim, line=None)


def strut(f, R, a3, b3, z, r=1.4, dim=0, mat_='gunmetal'):
    a, b = R.p(a3), R.p(b3)
    f.add(f.cap(*a, *b, r), mat_, z=z, rl=1, rs=1.4, dim=dim, line='hard')


def _crotch(X, Y, t, x0, y0, y1):
    out = t.copy()
    out[(abs(X - x0) < 0.6) & (Y > y0) & (Y < y1) & (t >= 1)] = 0
    return out


# ------------------------------------------------------------------------------------ build
def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    b, cr, lean = P['bob'], P['crouch'], P['lean']
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 21.0 + P['breath'], 0.0)
    hb = P.get('hback', 0.0)                       # v2: the head leans back from a tube aimed up
    head3 = (sh3[0] + lean * 0.35 + 0.5 - hb, sh3[1] + 20.0 - 0.3 * hb, 0.0)
    off = (P['hipx'] + lean, -cr - b + P['breath'], 0.0)
    offh = (P['hipx'], -cr - b, 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    # ---------------------------------------------------------------- launcher frame
    lpos = add3(P['lpos'] or LPOS0, off)
    ldir = P['ldir'] or LDIR0
    lfar = R.far(1) and lpos[2] > 4
    if R.diag and lfar:
        lz = 38.0              # on the far shoulder in a turn: behind the head, over the torso's far side
    elif R.back:
        lz = 46.0
    elif lfar:
        lz = 3.0
    else:
        lz = 46.0 if lpos[1] > 44 else 31.0
    tmp = Fig(8, 8)
    K = launcher(tmp, Rig(tmp, facing), lpos, ldir, lz)
    hR = add3(P['handR'], offh) if P['handR'] is not None else K['trig3']
    if P['lmode'] == 'fore':
        hL = K['fore3']
    elif P['lmode'] == 'chamber':
        hL = tuple(np.array(K['chamber3']) + K['Dn'] * 1.5)
    elif P['handL'] is not None:
        hL = add3(P['handL'], offh)
    else:
        hL = add3(FIST_L, offh)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    # ---------------------------------------------------------------- loader frame on the back
    base3 = add3(sh3, (-9.5, -5.0, 3.0))
    t = P['loader']
    fold_a = add3(base3, (0.5, 6.0, 4.0))            # folded: flat on the back
    fold_b = add3(base3, (0.5, -6.0, 6.0))
    up_a = add3(sh3, (-14.0, 27.0, 12.0))           # unfolded: hinge above and behind the right shoulder
    lj = tuple(np.array(fold_a) + (np.array(up_a) - np.array(fold_a)) * t)
    le = tuple(np.array(fold_b) + (np.array(K['breech3']) - np.array(fold_b)) * t)
    bj = tuple(np.array(add3(base3, (0.5, -2.0, -4.0))) + (np.array(K['brace3']) - np.array(add3(base3, (0.5, -2.0, -4.0)))) * t)
    loz = 28.5 if R.back else (1.5 if t < 0.3 else (lz - 0.4 if lz > 40 else 2.0))
    if (facing == 'S' or (R.diag and not R.back)) and t >= 0.3:
        loz = 2.0
    if side and t >= 0.3 and lz > 40:
        loz = 45.0
    with f.tagging('loader'):
        strut(f, R, base3, lj, loz, r=2.0, dim=1 if (facing == 'W' and t < 0.3) else 0)
        strut(f, R, lj, le, loz + 0.05, r=1.7)
        if t > 0.3:
            mid = tuple((np.array(lj) + np.array(le)) / 2)
            strut(f, R, mid, add3(mid, (1.5, -1.0, 0.0)), loz + 0.06, r=2.2, mat_='clack_orange')
        strut(f, R, base3, bj, loz - 0.05, r=1.2, mat_='clack_orange')
        jx, jy = R.p(lj)
        f.add(f.ell(jx, jy, 2.4, 2.4), 'brass', z=loz + 0.1, rl=1, rs=1, line='hard')
        bx_, by_ = R.p(base3)
        f.add(f.rect(bx_ - 3.5, by_ - 2, bx_ + 3.5, by_ + 2.5), 'gunmetal', z=loz + 0.12 if R.back else loz - 0.2, rl=1,
              rs=1.4, line='hard')
        if t > 0.6:       # the cradle at the breech holds the next rocket
            rocket_item(f, R, add3(le, (-6.0, 1.5, 0.0)), (1.0, 0.0, 0.0), loz + 0.08, tag='loader')
    # ---------------------------------------------------------------- legs
    for lat, key in ((P['stance'], 'footR'), (-P['stance'], 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.5, lat)
        hp3 = add3(hip3, (0.0, 0.0, lat * 0.95))
        up, lo, kn3 = R.limb(hp3, ank3, 8.2, 8.0, 5.4, 4.9, 4.6, (1.0, 0.0, 0.1 * np.sign(lat)))
        far = R.far(lat)
        dim = 1 if far else 0
        z = 9 + 0.1 * R.d(foot3)
        f.add(up | lo, 'clack_work', z=z, rl=1.8, rs=2.8, vgrad=0.3, dim=dim, line='hard')
        fx, fy = R.p(foot3)
        ax_, ay_ = R.p(ank3)
        f.add(f.cap(ax_, ay_ - 2, ax_, ay_, 5.0) & (up | lo), 'clack_work', z=z + 0.1, flat=1, dim=dim, line='soft')   # turn-up
        if side:
            boot_side(f, fx, fy, 'clack_boot', z=z + 1, dim=dim, toe=2.0)
            f.add(f.rect(fx - 3.6, fy - 2, fx + 7.0, fy) & f.ell(fx + 2.0, fy - 2.6, 5.6, 3.6), 'clack_boot', z=z + 1.2, flat=0,
                  dim=dim, line='soft')
            if not far:
                kx, ky = R.p(kn3)
                f.add(f.rect(hx - 1.5, hy + 4, hx + 5.5, hy + 11) & (up | lo), 'clack_work', z=z + 0.3, rl=1, rs=1.6, line='hard')
        elif R.diag:
            surf.boot_3q(f, R, foot3, 'clack_boot', z + 1, dim=dim, cuff=False, shade=dict(rl=1.6))
        else:
            boot_front(f, fx, fy, 'clack_boot', z=z + 1, dim=dim)
            f.add(f.rect(fx - 4.8, fy - 2, fx + 4.8, fy) & f.ell(fx, fy - 2.6, 5.0, 3.4), 'clack_boot', z=z + 1.2, flat=0, line='soft')
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    vf = ('N' if R.back else 'S') if R.diag else facing      # turn in-betweens: the S or N drawing turned onto the body
    tw = turn.Warp(f, R, (sx + hx) / 2, 13.5, 10.0, vf) if R.diag else None
    if tw:
        tw.__enter__()
    if side:
        f.add(f.ell(hx + 1.0, hy, 10.5, 4.5), 'clack_work', z=19, rl=2, rs=3, line='hard')
    else:
        f.add(f.rect(hx - 12, hy - 5, hx + 12, hy + 2) | f.ell(hx, hy + 1, 12, 4), 'clack_work', z=13, rl=2, rs=3.4, vgrad=0.4,
              line='hard', tonemap=lambda X, Y, tt: _crotch(X, Y, tt, hx, hy + 4, hy + 8))
    # ---------------------------------------------------------------- torso and harness
    if side:
        body = f.ell(sx + 1.0, sy + 7, 11.0, 13) | f.poly([(hx - 9.5, hy - 2), (sx - 9.5, sy + 1), (sx + 10, sy + 1), (hx + 12.0, hy - 4)])
        body |= f.ell(hx + 3.5, hy - 7, 9.5, 6)
        body &= f.Y < hy - 1
        f.add(body, 'clack_teal', z=20, rl=2.2, rs=4.0, vgrad=0.35, line='hard')
        f.add(f.rect(hx - 10, hy - 6, hx + 13, hy - 2), 'leather', z=22, rl=1, rs=1.2, line='soft')
        f.add(f.rect(hx + 10.5, hy - 7, hx + 13.5, hy - 1), 'brass', z=23, rl=1, rs=1.4, line='hard')
        f.add(f.poly([(sx + 1, sy - 6), (sx + 4.5, sy - 6), (hx + 9.5, hy - 6), (hx + 6, hy - 6)]) & body, 'clack_web', z=24, rl=1, rs=1.4,
              line='hard')
        f.add(f.poly([(sx - 5, sy - 6), (sx - 1.5, sy - 6), (hx - 6, hy - 6), (hx - 9.5, hy - 6)]) & body, 'clack_web', z=24, rl=1, rs=1.4,
              line='hard')
    else:
        body = f.ell(sx, sy + 7, 14.0, 13) | f.rect(sx - 13, sy + 1, sx + 13, sy + 8) | \
            f.poly([(sx - 13, sy + 4), (sx + 13, sy + 4), (hx + 13, hy - 3), (hx - 13, hy - 3)]) | f.ell(hx, hy - 6, 13.5, 5)
        body &= f.Y < hy - 1
        f.add(body, 'clack_teal', z=20, rl=2.2, rs=4.0, vgrad=0.35, line='hard')
        f.add(f.rect(hx - 13.5, hy - 6, hx + 13.5, hy - 2), 'leather', z=22, rl=1, rs=1.2, line='soft')
        if vf == 'S':
            f.add(f.rect(sx - 1, sy - 3, sx + 1, hy - 7), 'clack_teal', z=21, flat=1, line=None)
            f.add(f.rect(sx + 3, sy + 3, sx + 9, sy + 9), 'clack_teal', z=21, rl=1, rs=1.6, line='soft')
            f.add(f.rect(hx - 2, hy - 7, hx + 2, hy - 1), 'brass', z=23, rl=1, rs=1.4, line='hard')
            for s in (-1, 1):
                f.add(f.poly([(sx + 7 * s, sy - 6), (sx + 11 * s, sy - 6), (hx + 10 * s, hy - 6), (hx + 6.5 * s, hy - 6)]), 'clack_web',
                      z=24, rl=1, rs=1.6, line='hard')
            f.add(f.rect(sx - 11, sy + 6, sx + 11, sy + 8), 'clack_web', z=24.1, rl=1, rs=1.2, line='hard')
            for s in (-1, 1):
                f.add(f.ell(sx + 8.5 * s, sy + 7, 1.8, 1.8), 'brass', z=24.2, rl=1, rs=1, line='hard')
        else:
            for s in (-1, 1):
                f.add(f.poly([(sx + 8 * s, sy - 6), (sx + 11.5 * s, sy - 6), (hx - 9 * s, hy - 6), (hx - 12.5 * s, hy - 6)]), 'clack_web',
                      z=24, rl=1, rs=1.6, line='hard')
            f.add(f.ell((sx + hx) / 2 - 0.8, sy + 4.5, 2.4, 2.4), 'brass', z=24.5, rl=1, rs=1.2, line='hard')
            for s in (-1, 1):
                f.add(f.rect(hx + 3 * s - 2, hy + 1, hx + 3 * s + 2.5, hy + 6), 'clack_work', z=13.5, rl=1, rs=1.4, line='soft')
    if tw:
        tw.__exit__(None, None, None)
    # rack on the front left of the belt
    rk3 = add3(hip3, (9.5, 3.0, -7.5))
    rx, ry = R.p(rk3)
    if not R.back:
        rz = 26.0 if facing in ('S', 'W', 'SW') else (24.0 if facing == 'SE' else 19.0)
        rack(f, rx, ry, rz, dim=1 if facing in ('E', 'SE') else 0, side=side, n=2)
    ac3 = add3(hip3, (2.0, 0.5, -12.5))          # closed ammo case on the left hip: the reload's source
    ax, ay = R.p(ac3)
    if facing not in ('E', 'SE', 'NE'):
        az = 25.5 if facing in ('S', 'W', 'SW') else 27.0
        with f.tagging('rack'):
            f.add(f.rect(ax - (3.0 if side else 2.6), ay - 3, ax + (3.0 if side else 2.6), ay + 5), 'leather', z=az, rl=1, rs=1.6,
                  line='hard', cast=(1, 1, 1))
            f.add(f.rect(ax - (3.0 if side else 2.6), ay - 3, ax + (3.0 if side else 2.6), ay - 1), 'leather', z=az + 0.05, flat=1,
                  line='soft')
            f.dot(ax, ay - 1, ('brass', 3), z=az + 0.06)
    # ---------------------------------------------------------------- arms
    arms = []
    sRj, sLj, _ = shoulders(sh3, hR, hL, SHW, sum(ARM), P['twist'])
    for key, hh, lat, shp in (('R', hR, 1, sRj), ('L', hL, -1, sLj)):
        pole = P['pole' + key] or (-0.5, -1.0, 0.35 * lat)
        up, lo, el3 = R.limb(shp, hh, ARM[0], ARM[1], 4.2, 3.8, 3.4, pole)
        far = R.far(lat)
        dd = R.d(hh)
        grips = (key == 'R' and P['handR'] is None) or (key == 'L' and P['lmode'] in ('fore', 'chamber'))
        if grips:
            zl = lz + 0.5 if not (facing == 'N' and dd < 0.5) else 26.0
            if facing in 'EW' and far and lz < 10:
                zl = 3.6
        elif dd >= -3.5:
            zl = 30.0 + 0.05 * dd
        else:
            zl = 5.0 + 0.05 * dd
        if facing in 'EW' and far and not grips:
            zl = 4.0
        zu = zl - 0.3 if R.d(el3) > -3.5 or not far else 4.0
        if R.back:                  # from behind: a hand in front of him or across his body is hidden
            across = (hh[2] - sh3[2]) * lat < 0
            front = dd < (0.5 if grips else -3.5) or (across and dd < 2.0)
            zl = 5.0 if front else 26.0
            zu = 5.0 if (front and R.d(el3) < 0.5) else 26.0
        if facing in 'EW' and not far:
            zu = min(zu, 44.0)
        if facing in 'EW' and far:
            zu = 3.8
        arms.append((key, shp, hh, up, lo, el3, far, zu, zl))
    for key, shp, hh, up, lo, el3, far, zu, zl in arms:
        dim = 1 if far else 0
        f.add(up, 'clack_skin', z=zu, rl=1.6, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1) if not far else None)
        f.add(lo, 'clack_skin', z=zl, rl=1.6, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1) if not far else None)
        # rolled teal sleeve over the upper two thirds
        a, e = R.p(shp), R.p(el3)
        cx_, cy_ = a[0] + 0.62 * (e[0] - a[0]), a[1] + 0.62 * (e[1] - a[1])
        f.add(f.cap(a[0], a[1], cx_, cy_, 4.7, 4.5), 'clack_teal', z=zu + 0.05, rl=1.6, rs=2.4, dim=dim, line='hard')
        f.add(f.ell(cx_, cy_, 4.7, 1.6), 'clack_teal', z=zu + 0.06, rl=1, rs=1.4, dim=dim, line='soft')
        x2, y2 = R.p(hh)
        fist(f, x2, y2, zl + 0.3, dim=dim, r=3.5)
        if key == 'L' and P['hrocket']:
            rocket_item(f, R, add3(hh, (0.0, -1.0, 0.0)), P['hrocket'] if isinstance(P['hrocket'], tuple) else (1.0, 0.3, 0.0),
                        zl + 0.2, dim=dim, tag='rack')
    # right shoulder pad under the launcher
    rp = R.p(add3(sRj, (-0.5, 3.5, 1.5)))
    f.add(f.ell(rp[0], rp[1], 5.6 if not side else 6.0, 3.6 if not side else 3.0), 'leather',
          z=(34 if not side else 45) if not lfar else 3.5, rl=1.4, rs=2, line='hard', dim=1 if lfar else 0)
    # ---------------------------------------------------------------- head
    h2x, h2y = R.p(head3)
    if R.back:                     # the neck from behind, down into the collar (the head never floats)
        nx = h2x + (1.0 if R.diag else 0.0)
        f.add(f.rect(nx - 4.5, h2y + 5, nx + 4.5, h2y + 15), 'clack_skin', z=20.6, rl=1, rs=1.6, line='hard')
        f.add(f.rect(nx - 6.5, h2y + 12.5, nx + 6.5, h2y + 15.5) & f.ell(nx, h2y + 14.5, 7.0, 2.6), 'clack_teal', z=20.7, rl=1, rs=1.4,
              line='hard')
    if R.diag:
        head_3q(f, P, h2x, h2y, R.back)
    elif facing == 'S':
        head_south(f, P, h2x, h2y)
    elif facing == 'N':
        head_north(f, P, h2x, h2y)
    else:
        head_side(f, P, h2x, h2y)
    # ---------------------------------------------------------------- launcher (drawn last: over the head where nearer)
    zr = None
    if R.back and K['muzzle3'][1] < 44.0:             # tipped down in front of him: the front half is behind his back
        zr, lz = lz, 5.0
    k = launcher(f, R, lpos, ldir, lz, dim=1 if lfar else 0, rocket=P['rocket'], near=not lfar, zr=zr)
    f.anchor('muzzle', *k['muzzle'])
    f.anchor('exhaust', *k['exhaust'])
    # effects for a drawing or two: backblast clear of the rear, muzzle puff
    if P['blast']:
        e3 = np.array(k['exhaust3'])
        with f.tagging('fx'):
            for i, (a, r) in enumerate(((0, 3.5), (5, 5.0), (10, 6.0))):
                c = R.p(tuple(e3 - k['D'] * a * (0.7 if P['blast'] > 1 else 1.0)))
                bzz = 2.0 if R.d(tuple(-k['D'])) < -0.3 else 48.0   # v2: blowing away from the camera, the blast is behind him
                f.add(f.ell(c[0], c[1], r, r * 0.85), 'clack_grey' if (i > 0 or P['blast'] > 1) else 'clack_orange', z=bzz + i * 0.01,
                      rl=1.2, rs=2.0, line='soft')
    if P['puff']:
        m3 = np.array(k['muzzle3'])
        with f.tagging('fx'):
            for i, (a, r) in enumerate(((1, 3.0), (5, 4.2))):
                c = R.p(tuple(m3 + k['D'] * a))
                pz = 2.0 if R.d(tuple(k['D'])) < -0.3 else 48.0    # blowing away from the camera: behind him
                f.add(f.ell(c[0], c[1], r, r * 0.85), 'clack_grey', z=pz + i * 0.01, rl=1.2, rs=2.0, line='soft')


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f

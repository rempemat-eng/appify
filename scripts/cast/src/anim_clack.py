"""Clack's animation table (the anim_bramble.py pattern).  Poses list what differs from clack.P0.

Logic (Codex identity table): the launcher stays on the RIGHT shoulder with both grips; the
right hand stays on the trigger grip, the left takes the fore grip to aim.  Primary: brace, aim,
launch (the rocket leaves the muzzle; the backblast clears the rear of the bell, behind his head),
recoil kicks the tube up and back into the shoulder, then a readable reload: the left hand takes
a spare rocket from the rack on the front of the belt (one left in it) and feeds it into the
muzzle.  Secondary (pressure vent): the launcher levelled, the left hand opens the pressure
chamber's valve, a compressed-air blast at the muzzle.  Loader Brace (special): the carried
loader frame unfolds from his back over the right shoulder to the breech with the next rocket,
and its brace strut props the tube; it stays attached through the powered clips (he still walks)
and folds flat again on exit.  In the powered primary the loader feeds the breech, so there is no
hand reload.
"""
import math
import numpy as np
import anim
from clack import LPOS0, FIST_L, frame3

A_STRIDE = 9.0
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride (a quicker cadence)
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 6.5 / anim.STAIR_LOOP, 1)

BR = dict(footR=(0.0, 0.0), footL=(5.0, 0.0))                       # left foot forward, braced
BR1 = dict(footL=(5.0, 0.0))                                        # first step of the brace (one foot at a time)
AIM = dict(lpos=(0.5, 48.0, 10.5), ldir=(1.0, 0.03, -0.06), lmode='fore')
PW = dict(loader=1.0)

# reload pose: the tube tipped muzzle-down toward his left hip so the left hand can feed it
TIP = dict(lpos=(2.0, 42.0, 3.0), ldir=(0.45, -0.75, -0.5))
_D = tuple(frame3(TIP['ldir'])[0])
LOADH = tuple(TIP['lpos'][k] + _D[k] * 20.0 + (0.5 if k == 0 else 0.0) for k in range(3))


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


# --------------------------------------------------------------------------------- idle, walk
def idle(powered=False):
    """v2 idle, 12 drawings in 1.6 s: the launcher's weight rides on the breath: the tube settles a
    beat after the chest rises (it sags 1 px, the muzzle dips a little), the trigger hand with it."""
    keys = []
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    sag = [0.0, 0.0, 0.2, 0.4, 0.2, 0.0, -0.2, -0.4, -0.5, -0.4, -0.2, 0.0]   # the tube a beat behind the breath
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    base = dict(PW) if powered else {}
    for i in range(12):
        keys.append((K(base, breath=br[i], blink=(i == 10), handL=add(FIST_L, (0, 0.5 * br[i], 0)),
                       lpos=add(LPOS0, (0.0, sag[i], 0.0)), ldir=(1.0, 0.02 * sag[i], 0.0)), ms[i]))
    return keys


def walk(powered=False):
    """v2 walk, 12 drawings a stride: the heavy tube lands a drawing after each footfall (it drops
    1 px and its muzzle nods), the free left arm swings."""
    keys = []
    base = dict(PW) if powered else {}
    n = anim.WALK_N2
    gs = anim.gait(n, A_STRIDE, 3.0, bob=1.0)
    for i, g in enumerate(gs):
        s = g['swing']
        late = gs[(i - 1) % n]['bob']                        # the tube follows the body's bob a drawing late
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=0.8,
                       lpos=add(LPOS0, (0.0, -0.6 * late, 0.0)), ldir=(1.0, -0.03 * late + 0.02 * s, 0.0),
                       handL=add(FIST_L, (3.0 * s, 0.6 * abs(s), 0.5))),
                     WALK_LOOP2 * 1000 / n))
    return keys


# --------------------------------------------------------------------------------- idle fidgets (v2)
def fidget_gauge():
    """Taps the pressure chamber's gauge with a knuckle, watches the needle, nods."""
    return [(K(), 150), (K(handL=(0.0, 36.0, -2.0), lean=0.2), 110),
            (K(lmode='chamber', lean=0.4, brow=1), 120),
            (K(lmode='chamber', lean=0.5, brow=1, valve=True), 70),          # tap
            (K(lmode='chamber', lean=0.4, brow=1), 90),
            (K(lmode='chamber', lean=0.5, brow=1, valve=True), 70),          # tap
            (K(lmode='chamber', lean=0.4, brow=2), 220),                     # watches the needle
            (K(handL=(0.0, 34.0, -4.0), lean=0.2, blink=True), 120),
            (K(handL=add(FIST_L, (0.5, 1.0, 0.0))), 120), (K(), 170)]


def fidget_heave():
    """Shrugs the launcher higher on the shoulder pad: a dip, the heave, the tube settles back."""
    return [(K(), 150), (K(crouch=1.0, lpos=add(LPOS0, (0.0, -0.8, 0.0))), 110),
            (K(crouch=0.5, breath=1, lpos=add(LPOS0, (0.5, 2.2, -0.5)), ldir=(1.0, 0.06, 0.0), brow=1), 110),   # heave
            (K(breath=1, lpos=add(LPOS0, (0.3, 1.5, -0.3)), ldir=(1.0, 0.03, 0.0)), 100),
            (K(crouch=0.4, lpos=add(LPOS0, (0.0, -0.6, 0.0)), ldir=(1.0, -0.03, 0.0)), 110),                       # it lands
            (K(lpos=add(LPOS0, (0.0, 0.2, 0.0)), ldir=(1.0, 0.01, 0.0)), 120),
            (K(blink=True), 120), (K(), 170)]


def _wipe(dn):
    D, Dn, Rt = frame3((1.0, -0.35, -0.15))
    c = np.array(add(LPOS0, (2.0, -1.5, -1.5))) + D * 17.0 + Dn * 1.5 + Rt * dn
    return tuple(round(float(x), 3) for x in c)


def fidget_muzzle():
    """Tips the tube forward and wipes the muzzle ring with the heel of his hand."""
    T = dict(lpos=add(LPOS0, (2.0, -1.5, -1.5)), ldir=(1.0, -0.35, -0.15))
    return [(K(), 150), (K(lpos=add(LPOS0, (1.0, -0.7, -0.7)), ldir=(1.0, -0.17, -0.07), handL=(4.0, 33.0, -6.0)), 110),
            (K(T, handL=_wipe(1.5), brow=1), 110),
            (K(T, handL=_wipe(-1.5), brow=1), 80),                          # wipe
            (K(T, handL=_wipe(1.5), brow=1), 80),
            (K(T, handL=_wipe(-1.0), face='talk'), 160),                     # a puff of breath on it
            (K(lpos=add(LPOS0, (1.0, -0.7, -0.7)), ldir=(1.0, -0.17, -0.07), handL=(4.0, 33.0, -8.0)), 110),
            (K(handL=add(FIST_L, (1.0, 1.0, 0.0))), 120), (K(), 170)]


def stairs(up=True):
    keys = []
    for g in anim.gait(8, 6.5, 6.5 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(footR=fr, footL=fl, bob=g['bob'], lean=2.0 if up else -1.0, crouch=1.0 if up else 0.5,
                       handL=add(FIST_L, (2.5 * s, 0.5, 0))), 90))
    return keys


# --------------------------------------------------------------------------------- rocket
def launch(powered=False):
    b = dict(PW) if powered else {}
    A = K(b, BR, AIM)
    kick = dict(lpos=(-3.0, 48.5, 12.0), ldir=(1.0, 0.09, -0.06))
    if powered:
        return [
            (K(b), 50),
            (K(A, crouch=1.0), 50),                                                          # fore grip, brace
            (K(A, crouch=1.5, lean=0.5, brow=1), 60),                                        # aim
            (K(A, crouch=1.5, lean=0.5, brow=1), 30),
            (K(A, kick, rocket=False, blast=1, crouch=2.0, lean=-1.5, brow=1, face='shut'), 40),   # RELEASE
            (K(A, lpos=(-1.5, 48.8, 12.0), ldir=(1.0, 0.06, -0.06), rocket=False, blast=2, crouch=2.0, lean=-1.0), 60),
            (K(A, rocket=True, crouch=1.5, lean=0.0), 90),                                   # the loader feeds the breech
            (K(b, crouch=0.5), 110),
            (K(b), 130),
        ]
    return [
        (K(), 50),                                                                            # ready
        (K(BR1, crouch=0.5, handL=(8.0, 36.0, 4.0)), 45),                                     # left foot forward, left hand comes up
        (K(A, crouch=1.0), 45),                                                               # fore grip
        (K(A, crouch=1.5, lean=0.5, brow=1), 50),                                             # brace, aim (held)
        (K(A, crouch=1.5, lean=0.6, brow=1), 70),                                             # squeeze
        (K(A, kick, rocket=False, blast=1, crouch=2.0, lean=-1.5, brow=1, face='shut'), 35),  # RELEASE: launch, backblast
        (K(A, lpos=(-2.5, 48.9, 12.0), ldir=(1.0, 0.08, -0.06), rocket=False, blast=2, crouch=2.6, lean=-1.8, face='shut'), 40),  # the kick in the shoulder
        (K(A, lpos=(-1.0, 48.4, 11.5), ldir=(1.0, 0.03, -0.06), rocket=False, crouch=2.2, lean=-0.6), 55),   # absorbed: the body comes forward
        (K(A, lpos=(0.8, 47.8, 10.8), ldir=(1.0, 0.0, -0.06), rocket=False, crouch=1.6, lean=0.6), 55),     # settle past the aim
        (K(BR, rocket=False, crouch=1.0, handL=(2.5, 27.5, -12.0), poleL=(-0.3, -1.0, -0.8), lean=0.3,
           lpos=(1.0, 46.0, 9.0), ldir=(1.0, -0.4, -0.25)), 70),                                     # tube tips down; hand to the case
        (K(BR, rocket=False, crouch=1.0, handL=(5.0, 31.0, -8.0), hrocket=(0.3, 1.0, 0.3), lean=0.5, **TIP), 70),   # spare rocket out
        (K(BR1, rocket=False, crouch=1.0, handL=LOADH, hrocket=tuple(-x for x in _D), lean=0.5, **TIP), 70),       # into the muzzle
        (K(rocket=True, crouch=0.5, handL=(6.0, 30.0, -10.0), lpos=(0.5, 46.5, 10.0), ldir=(1.0, -0.2, -0.1)), 80),  # loaded, back up
        (K(), 120),                                                                                             # settle
    ]


# --------------------------------------------------------------------------------- pressure vent
def vent():
    """Pressure vent: the launcher levelled at the shoulder, the left hand squeezes the vent lever on
    the fore grip (the pressure chamber behind the shoulder feeds it), a compressed-air puff leaves
    the muzzle; the loaded rocket stays seated."""
    L = dict(lpos=(1.0, 46.0, 10.0), ldir=(1.0, -0.05, -0.08))
    return [
        (K(), 50),
        (K(BR, L, crouch=1.0, lmode='fore'), 60),                                               # fore grip
        (K(BR, L, crouch=1.5, lmode='fore', brow=1), 60),
        (K(BR, L, crouch=2.0, lmode='fore', lean=0.8, brow=1), 70),                             # squeeze (held)
        (K(BR, L, lpos=(-0.5, 46.5, 10.0), crouch=2.0, lmode='fore', puff=1, lean=-1.0, brow=1, face='shut'), 40),  # RELEASE
        (K(BR, L, crouch=1.5, lmode='fore', puff=2, lean=-0.5), 70),
        (K(BR, crouch=1.0, handL=(4.0, 32.0, -10.0)), 90),
        (K(crouch=0.5), 100),
        (K(), 120),
    ]


# --------------------------------------------------------------------------------- guard
def guard(powered=False):
    """Brace: feet set, launcher pulled tight on the shoulder and tilted to cover the head, the
    left forearm raised across the chest."""
    b = dict(PW) if powered else {}
    G = dict(lpos=(0.5, 48.0, 11.0), ldir=(1.0, 0.18, -0.25), handL=(7.0, 44.0, -2.0), poleL=(-0.3, -1.0, -0.6))
    B = dict(footR=(0.0, 0.0), footL=(3.5, 0.0))
    B1 = dict(footR=(0.0, 0.0))
    return [
        (K(b, B1, crouch=0.5, handL=(4.0, 33.0, -10.0)), 55),
        (K(b, B, crouch=1.5, handL=(6.0, 40.0, -6.0), lpos=(0.0, 48.0, 12.0), ldir=(1.0, 0.1, -0.12)), 55),
        (K(b, B, G, crouch=2.5, lean=1.0, brow=1), 55),
        (K(b, B, G, crouch=3.0, lean=1.5, brow=1), 55),
        (K(b, B, G, crouch=3.5, lean=1.5, brow=1), 120),                       # HOLD
        (K(b, B1, crouch=2.0, handL=(5.0, 36.0, -8.0), lpos=(0.0, 48.0, 12.0), ldir=(1.0, 0.08, -0.1)), 120),
        (K(b, crouch=0.5, handL=add(FIST_L, (1.0, 2.0, 0.0))), 120),
        (K(b), 120),
    ]


# --------------------------------------------------------------------------------- hit, defeat
def hit():
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2, handL=(-2.0, 30.0, -17.0), ldir=(1.0, 0.15, 0.0)), 35),
        (K(lean=-4.0, crouch=2.0, face='shut', brow=2, handL=(-3.0, 31.0, -17.5), ldir=(1.0, 0.2, 0.0)), 65),
        (K(lean=-2.5, crouch=3.0, brow=2, handL=(-1.0, 29.0, -17.0), ldir=(1.0, 0.1, 0.0)), 90),
        (K(lean=-1.0, crouch=2.0, brow=2), 120),
        (K(lean=0.5, crouch=1.0, brow=1), 130),
        (K(lean=0.3, crouch=0.5), 150),
        (K(), 160),
        (K(), 180),
    ]


def defeat():
    k1 = dict(footR=(6.0, 0.0), footL=(-6.0, 2.0))
    k2 = dict(footR=(6.5, 0.0), footL=(-8.0, 2.5))
    down = dict(lpos=(2.0, 40.0, 13.0), ldir=(1.0, -0.35, 0.0))
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2), 80),
        (K(lean=2.0, crouch=5.0, face='shut', brow=2, lpos=(0.5, 47.0, 13.0), ldir=(1.0, -0.15, 0.0), handL=(6.0, 26.0, -14.0)), 100),
        (K(k1, lean=3.0, crouch=8.0, brow=2, lpos=(1.0, 44.0, 13.0), ldir=(1.0, -0.25, 0.0), handL=(9.0, 26.0, -12.0)), 100),
        (K(k2, lean=4.0, crouch=11.0, brow=2, handL=(10.0, 25.0, -11.0), **down), 120),
        (K(k2, lean=5.0, crouch=12.0, brow=2, face='shut', handL=(10.0, 24.5, -11.0), **down), 150),
        (K(k2, lean=6.0, crouch=12.5, face='shut', handL=(10.0, 24.0, -11.0), **down), 180),
        (K(k2, lean=6.0, crouch=12.5, face='shut', handL=(10.0, 24.0, -11.0), **down), 240),
        (K(k2, lean=6.0, crouch=12.5, face='shut', handL=(10.0, 24.0, -11.0), **down), 300),
    ]


# --------------------------------------------------------------------------------- jump, dodge
def jump():
    return [
        (K(crouch=4.0, lean=2.0, handL=(0.0, 24.0, -17.0)), 80),
        (K(crouch=1.0, lean=1.0, footR=(1.5, 1.0), footL=(-1.5, 1.5), handL=(5.0, 34.0, -17.0)), 55),
        (K(footR=(2.5, 6.0), footL=(-2.0, 7.5), handL=(6.0, 38.0, -17.5), ldir=(1.0, 0.1, 0.0)), 80),
        (K(footR=(3.0, 7.5), footL=(-1.0, 8.5), handL=(6.0, 37.0, -17.5), ldir=(1.0, 0.05, 0.0)), 110),
        (K(footR=(2.0, 3.0), footL=(-2.5, 4.0), handL=(5.0, 38.0, -17.0), ldir=(1.0, -0.05, 0.0)), 110),
        (K(crouch=5.0, lean=2.5, footR=(2.5, 0.0), footL=(-2.5, 0.0), handL=(6.0, 25.0, -16.0), ldir=(1.0, -0.1, 0.0)), 80),
        (K(crouch=3.0, lean=1.5, footR=(2.0, 0.0), footL=(-2.0, 0.0)), 70),
        (K(), 115),
    ]


def dodge():
    return [
        (K(crouch=3.0, lean=3.0, footR=(3.0, 0.0), footL=(-4.0, 0.0)), 55),
        (K(crouch=5.0, lean=5.5, footR=(6.0, 2.0), footL=(-9.0, 0.0), handL=(-3.0, 26.0, -17.0)), 45),
        (K(crouch=7.0, lean=7.0, footR=(8.5, 1.0), footL=(-9.5, 0.0), handL=(-5.0, 27.0, -17.0), ldir=(1.0, -0.1, 0.0)), 40),
        (K(crouch=7.0, lean=7.0, footR=(8.5, 0.0), footL=(-8.5, 0.5), handL=(-4.0, 26.0, -17.0), ldir=(1.0, -0.1, 0.0)), 45),
        (K(crouch=6.0, lean=5.5, footR=(7.0, 0.0), footL=(-7.0, 1.5), handL=(-1.0, 25.0, -17.0)), 60),
        (K(crouch=4.0, lean=3.5, footR=(5.0, 0.0), footL=(-4.0, 0.0)), 70),
        (K(crouch=2.0, lean=2.0, footR=(3.0, 0.0), footL=(-3.0, 0.0)), 80),
        (K(), 100),
    ]


# --------------------------------------------------------------------------------- Loader Brace
def special():
    return [
        (K(), 80),
        (K(crouch=1.0, handL=(-6.0, 38.0, -10.0), poleL=(-0.5, -1.0, -0.6), brow=1), 80),     # reaches back to the release catch
        (K(crouch=1.5, handL=(-8.0, 42.0, -6.0), poleL=(-0.5, -1.0, -0.6), loader=0.25, brow=1), 80),
        (K(crouch=1.5, handL=(-6.0, 40.0, -8.0), poleL=(-0.5, -1.0, -0.6), loader=0.6, lean=0.5), 80),
        (K(BR, crouch=2.5, loader=1.0, lean=1.0, brow=1, ldir=(1.0, -0.05, 0.0)), 60),         # RELEASE: locked to the breech
        (K(BR, crouch=2.0, loader=1.0, lean=0.5, ldir=(1.0, 0.02, 0.0)), 80),
        (K(PW, crouch=1.0, handL=add(FIST_L, (2.0, 2.0, 0.0))), 100),
        (K(PW, crouch=0.5), 110),
        (K(PW), 110),
    ]


def powered_exit():
    return [
        (K(PW), 110),
        (K(PW, crouch=0.5, handL=(-6.0, 38.0, -10.0), poleL=(-0.5, -1.0, -0.6)), 100),
        (K(crouch=1.0, loader=0.8, handL=(-8.0, 42.0, -6.0), poleL=(-0.5, -1.0, -0.6)), 100),
        (K(crouch=1.0, loader=0.5, handL=(-8.0, 42.0, -6.0), poleL=(-0.5, -1.0, -0.6)), 100),
        (K(crouch=0.5, loader=0.2, handL=(-6.0, 38.0, -9.0), poleL=(-0.5, -1.0, -0.6)), 90),
        (K(loader=0.0, handL=(-2.0, 33.0, -12.0)), 90),
        (K(crouch=0.5), 110),
        (K(), 150),
    ]


TABLE = {
    'fidget_gauge': fidget_gauge(),
    'fidget_heave': fidget_heave(),
    'fidget_muzzle': fidget_muzzle(),
    'idle': idle(),
    'walk': walk(),
    'primary': launch(),
    'secondary': vent(),
    'special': special(),
    'guard': guard(),
    'hit': hit(),
    'defeat': defeat(),
    'jump': jump(),
    'stair_up': stairs(True),
    'stair_down': stairs(False),
    'dodge': dodge(),
    'powered_idle': idle(True),
    'powered_walk': walk(True),
    'powered_primary': launch(True),
    'powered_guard': guard(True),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ v2: in-betweens, no skating
from clack import P0 as _P0
_D0 = _P0()
FIDGETS = ['fidget_gauge', 'fidget_heave', 'fidget_muzzle']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_DENSE = {'primary': [0, 3], 'secondary': [1, 3, 5], 'special': [1, 4], 'guard': [], 'hit': [0, 2], 'dodge': [1, 4],
          'powered_primary': [1, 7], 'jump': [], 'defeat': [], 'powered_exit': [], 'powered_guard': []}
_SH = {}
for _c, _a in _DENSE.items():
    if _a:
        TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    TABLE[_c] = anim.unskate(TABLE[_c], _P0)       # no skating: a foot that moves more than 3 px is lifted
# powered variants of hit, dodge, jump, stairs and secondary (anim.add_powered)
POWERED = dict(loader=1.0)                # Loader Brace: loader and brace stay unfolded

RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 5, 'secondary': 4, 'special': 4, 'powered_primary': 4}.items()}
HOLDS = {'primary': [_SH['primary'](3)], 'powered_primary': [_SH['powered_primary'](2)]}     # the aim, held before the squeeze

# v2 weapon aim within the facing (CONTRACT V2.8): the launcher turns about the shoulder pad it rests on
# (pitch, then yaw); both grips, and so both hands, follow it.  The reload does not turn.
AIM_CLIPS = ('primary', 'powered_primary')
AIM_PIVOT = (0.0, 46.5, 12.0)
SLIDE_UP = 12.0
RAISE_UP = 3.0                 # px the tube is lifted (and pushed forward) on the shoulder at the steepest up aim
HBACK = 3.0                    # px the head leans back from it in E and W


def _turn(v, th, ps, about):
    x, y, z = np.subtract(v, about) if about is not None else np.array(v, float)
    x, y = x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th)
    x, z = x * math.cos(ps) - z * math.sin(ps), x * math.sin(ps) + z * math.cos(ps)
    out = np.array([x, y, z]) + (np.array(about) if about is not None else 0.0)
    return tuple(round(float(c), 3) for c in out)


def aim_table(clip, fc, deg):
    fwd, up, lat = anim.aim_level(fc, deg)        # the tube stays level in S and N (it only turns)
    th0, ps0 = math.atan2(up, math.hypot(fwd, lat)), math.atan2(lat, fwd)
    keys = TABLE[clip]
    fore = [P.get('lmode') == 'fore' for P, _ in keys]
    # aimed drawings (the fore grip held) turn fully; the drawing either side turns half way, so the
    # tube swings onto the aim and back off it instead of snapping
    ws = [1.0 if fore[i] else (0.5 if ((i > 0 and fore[i - 1]) or (i + 1 < len(keys) and fore[i + 1])) else 0.0) for i in range(len(keys))]
    out = []
    for (P, ms), w in zip(keys, ws):
        P = dict(P)
        if w:
            P['lpos'] = _turn(P.get('lpos') or LPOS0, th0 * w, ps0 * w, AIM_PIVOT)
            P['ldir'] = _turn(P.get('ldir') or (1.0, 0.0, 0.0), th0 * w, ps0 * w, None)
            if th0 > 0:            # aimed up: the tube rides forward on the pad so the muzzle clears his face
                k = math.sin(th0 * w) / math.sin(math.radians(45))
                sl = SLIDE_UP * k
                d = np.array(P['ldir'], float) / np.linalg.norm(P['ldir'])
                P['lpos'] = tuple(round(float(c), 3) for c in np.array(P['lpos']) + d * sl + np.array([1.0, 1.0, 0.0]) * RAISE_UP * k)
                if fc in ('E', 'W'):
                    P['hback'] = round(HBACK * k, 2)          # and he leans his head back from it
        out.append((P, ms))
    return out
ANCHOR_COVER = {'muzzle': ('loader',)}       # from behind, the loader frame on his back covers the muzzle
RELEASE_ANCHOR = {'primary': 'muzzle', 'secondary': 'muzzle', 'special': 'hand_R', 'powered_primary': 'muzzle'}

EQUIP = {
    'launcher': dict(always=True),
    'chamber': dict(always=True, may_hide={'S', 'N', 'W', 'E', 'SW'}),
    'rack': dict(always=True, may_hide={'N', 'E', 'NE', 'NW'}),
    'loader': dict(clips={'powered_idle': list(range(8)), 'powered_primary': list(range(8))}),
}

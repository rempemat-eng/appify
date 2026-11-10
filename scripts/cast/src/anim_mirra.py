"""Mirra's animation table (17 contract clips).  Water is a scene effect: the body sheets show
only the gestures that prepare, shape and release it, with open hands in every drawing.
  - primary (shaped water): both hands gather the water low at the right hip, circle it up and
    fling it forward with the palms; the release is the right palm at full reach.
  - secondary (spring seal): palms down, raised, then pressed forward and down toward the
    ground ahead where the seal appears; held, then recovered.
  - special: the arms open wide and rise, palms up (drawing the water), then settle into the
    powered stance: wide, low, palms open and turned out, which holds the seals' currents.
The headwrap tail, gem, hoops, wrist bands and shawl end are fixed in place by the rig.
"""
import math
import numpy as np
import anim
from mirra import REST_R, REST_L, SHW
from anim_morel import K, add, home_feet, spread_feet, powered_from, powered_entry, g_idle, g_walk, g_stairs, g_hit, g_defeat, g_jump, g_dodge

A_STRIDE = 9.0
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

UP = (0.2, 1.0, 0.0)
FWD = (1.0, 0.1, 0.0)
OUT_R, OUT_L = (0.5, -0.4, 0.75), (0.5, -0.4, -0.75)          # palms turned out, fingers down and out
PWH = dict(handR=(5.0, 29.0, 18.0), handL=(5.0, 29.0, -18.0), fingR=OUT_R, fingL=OUT_L,
           poleR=(-0.5, -0.6, 1.0), poleL=(-0.5, -0.6, -1.0))
PW = dict(PWH, crouch=1.5, stance=7.0, footR=(-1.0, 0.0), footL=(2.0, 0.0), lag=0.5)
ST = dict(footR=(-3.5, 0.0), footL=(4.5, 0.0))


# --------------------------------------------------------------------------------- v2 idle, walk, fidgets
def idle(base=None, RR=REST_R, RL=REST_L):
    """v2 idle, 12 drawings in 1.6 s: the breath, the shawl end and wrap tail half a beat behind,
    one blink."""
    base = base or {}
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    return [(K(base, breath=br[i], lag=lag[i], blink=(i == 10), handR=add(RR, (0, 0.5 * br[i], 0)), handL=add(RL, (0, 0.5 * br[i], 0))), ms[i])
            for i in range(12)]


def walk(base=None, RR=REST_R, RL=REST_L, armR=2.5, armL=3.5, lift=3.5):
    """v2 walk, 12 drawings a stride; the shawl end and the wrap tail trail."""
    base = base or {}
    n = anim.WALK_N2
    keys = []
    for g in anim.gait(n, A_STRIDE, lift, bob=1.0):
        s = g['swing']
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.2 + 0.8 * abs(s),
                       handR=add(RR, (-armR * s, 0.5 + 0.6 * abs(s), 0)), handL=add(RL, (armL * s, 0.6 * abs(s), 0))),
                     WALK_LOOP2 * 1000 / n))
    return keys


def fidget_water():
    """Cups her hands before her, turns them as if feeling the water in the air, lets it go."""
    C = dict(handR=(8.0, 34.0, 4.0), handL=(8.0, 34.0, -4.0), fingR=(0.6, 0.6, -0.4), fingL=(0.6, 0.6, 0.4))
    return [(K(), 150), (K(handR=(6.0, 31.0, 9.0), handL=(6.0, 31.0, -9.0), fingR=FWD, fingL=FWD), 110), (K(C, brow=1), 130),
            (K(C, fingR=(0.4, 0.7, -0.6), fingL=(0.4, 0.7, 0.6), face='shut'), 160), (K(C, fingR=(0.7, 0.5, -0.3), fingL=(0.7, 0.5, 0.3)), 130),
            (K(handR=(7.0, 31.0, 10.0), handL=(7.0, 31.0, -10.0), fingR=(0.5, -0.8, 0.3), fingL=(0.5, -0.8, -0.3), lag=0.4), 120),
            (K(lag=0.2, blink=True), 120), (K(), 170)]


def fidget_shawl():
    """Draws the shawl's end back over her left shoulder."""
    S = dict(handR=(4.0, 43.0, -6.0), fingR=(0.2, 1.0, -0.3))
    return [(K(), 150), (K(handR=(6.0, 33.0, 6.0)), 110), (K(S, brow=1), 120), (K(S, handR=(1.0, 44.0, -9.0), lag=0.8), 130),
            (K(handR=(4.0, 36.0, 4.0), lag=1.0), 110), (K(lag=0.5, blink=True), 120), (K(lag=0.1), 110), (K(), 170)]


def fling(base=None, fast=False):
    b = base or {}
    keys = [
        (K(b, ST, handR=(6.0, 30.0, 11.0), handL=(6.0, 31.0, 1.0), fingR=FWD, fingL=FWD, lean=0.3), 60),          # 0 hands meet
        (K(b, ST, handR=(-1.0, 28.0, 13.0), handL=(1.0, 33.0, 6.0), fingR=(0.3, 0.3, -0.9), fingL=(0.3, -0.3, 0.9),
           lean=-0.6, crouch=1.0), 50),                                                                             # 1 gather at the right hip
        (K(b, ST, handR=(-2.0, 29.0, 13.5), handL=(0.0, 35.0, 7.0), fingR=(0.3, 0.3, -0.9), fingL=(0.3, -0.3, 0.9),
           lean=-1.0, crouch=1.5, brow=1), 80),                                                                     # 2 load (held)
        (K(b, ST, handR=(4.0, 42.0, 10.0), handL=(6.0, 45.0, 2.0), fingR=UP, fingL=UP, lean=0.0, crouch=1.0, brow=1,
           zR=46.0, zL=46.0), 40),                                                                                  # 3 circle up
        (K(b, ST, handR=(14.0, 40.0, 7.0), handL=(12.0, 38.0, -4.0), fingR=FWD, fingL=FWD, lean=2.5, crouch=1.5, brow=1), 30),  # 4 drive
        (K(b, ST, handR=(18.0, 37.0, 6.0), handL=(15.0, 35.0, -5.0), fingR=(1.0, 0.25, 0.0), fingL=(1.0, 0.25, 0.0),
           lean=3.5, crouch=2.0, brow=1), 40),                                                                      # 5 release
        (K(b, ST, handR=(17.0, 32.0, 9.0), handL=(14.0, 30.0, -9.0), fingR=(1.0, -0.3, 0.3), fingL=(1.0, -0.3, -0.3),
           lean=3.0, crouch=2.0), 60),                                                                              # 6 follow-through: palms part
        (K(b, ST, handR=(9.0, 29.0, 13.0), handL=(8.0, 28.0, -13.0), fingR=(0.7, -0.7, 0.2), fingL=(0.7, -0.7, -0.2),
           lean=1.5, crouch=1.0), 70),                                                                              # 7 recover
        (K(b, handR=add(REST_R, (2, 2, 0)), handL=add(REST_L, (2, 2, 0))), 90),                                    # 8 settle
        (K(b), 120),
    ]
    if fast:
        keys = [keys[0], keys[2], keys[3], keys[5], keys[6], keys[7], keys[8], keys[9]]
        keys[-1] = (K(b, PW), 120)
    return keys


def seal():
    D = (1.0, -0.2, 0.0)
    return [
        (K(handR=(5.0, 31.0, 11.0), handL=(5.0, 31.0, -11.0), fingR=FWD, fingL=FWD), 60),                         # 0 palms down
        (K(handR=(6.0, 40.0, 9.0), handL=(6.0, 40.0, -9.0), fingR=FWD, fingL=FWD, lean=-0.5, breath=1), 60),       # 1 raise
        (K(handR=(6.0, 43.0, 8.0), handL=(6.0, 43.0, -8.0), fingR=(1.0, 0.3, 0.0), fingL=(1.0, 0.3, 0.0), lean=-0.8,
           brow=1, breath=1, zR=46.0, zL=46.0), 90),                                                               # 2 load
        (K(handR=(12.0, 32.0, 7.0), handL=(12.0, 32.0, -7.0), fingR=D, fingL=D, lean=2.0, crouch=2.0, brow=1,
           footR=(-3.0, 0.0), footL=(4.0, 0.0)), 35),                                                               # 3 press
        (K(handR=(15.0, 26.0, 6.0), handL=(15.0, 26.0, -6.0), fingR=(1.0, -0.5, 0.0), fingL=(1.0, -0.5, 0.0), lean=3.5,
           crouch=4.0, brow=1, footR=(-3.0, 0.0), footL=(4.0, 0.0)), 40),                                           # 4 seal set (release)
        (K(handR=(15.5, 26.0, 6.0), handL=(15.5, 26.0, -6.0), fingR=(1.0, -0.5, 0.0), fingL=(1.0, -0.5, 0.0), lean=3.5,
           crouch=4.0, footR=(-3.0, 0.0), footL=(4.0, 0.0)), 90),                                                   # 5 held
        (K(handR=(9.0, 28.0, 11.0), handL=(9.0, 28.0, -11.0), fingR=(0.6, -0.8, 0.0), fingL=(0.6, -0.8, 0.0), lean=1.5,
           crouch=2.0), 80),
        (K(handR=add(REST_R, (1, 2, 0)), handL=add(REST_L, (1, 2, 0)), crouch=0.5), 90),
        (K(), 110),
    ]


def special():
    WIDE = dict(stance=7.0, footR=(-1.0, 0.0), footL=(2.0, 0.0))
    return [
        (K(handR=(4.0, 27.0, 15.5), handL=(4.0, 27.0, -15.5), fingR=(0.4, -0.6, 0.6), fingL=(0.4, -0.6, -0.6)), 80),   # 0 open
        (K(WIDE, handR=(3.0, 38.0, 20.0), handL=(3.0, 38.0, -20.0), fingR=(0.3, 0.2, 1.0), fingL=(0.3, 0.2, -1.0),
           poleR=(-0.4, -1.0, 0.4), poleL=(-0.4, -1.0, -0.4), breath=1, lag=1.0), 80),                               # 1 arms rise
        (K(WIDE, handR=(3.0, 47.0, 18.0), handL=(3.0, 47.0, -18.0), fingR=(0.2, 1.0, 0.4), fingL=(0.2, 1.0, -0.4),
           poleR=(-0.4, -1.0, 0.4), poleL=(-0.4, -1.0, -0.4), breath=1, lag=1.5, face='shut', zR=46.0, zL=46.0), 110),   # 2 drawing up (held)
        (K(WIDE, handR=(4.0, 45.0, 18.5), handL=(4.0, 45.0, -18.5), fingR=(0.3, 0.6, 0.8), fingL=(0.3, 0.6, -0.8),
           poleR=(-0.4, -1.0, 0.4), poleL=(-0.4, -1.0, -0.4), brow=1, lag=1.0, zR=46.0, zL=46.0), 60),
        (K(PW, brow=1, handR=(5.0, 34.0, 19.0), handL=(5.0, 34.0, -19.0), crouch=2.0, lag=-0.5), 50),                # 4 down into the stance (release)
        (K(PW, crouch=2.0, lag=-0.8), 90),
        (K(PW, lag=0.0), 110),
        (K(PW), 120),
    ]


def powered_exit():
    return [
        (K(PW), 100),
        (K(PW, handR=(6.0, 32.0, 15.0), handL=(6.0, 32.0, -15.0), fingR=FWD, fingL=FWD, breath=1), 100),
        (K(PW, handR=(8.0, 36.0, 4.0), handL=(8.0, 36.0, -4.0), fingR=(0.5, 0.2, -0.8), fingL=(0.5, 0.2, 0.8),
           crouch=1.0, face='shut', poleR=None, poleL=None), 110),                                                    # palms gather before the chest
        (K(handR=(7.0, 33.0, 6.0), handL=(7.0, 33.0, -6.0), fingR=(0.6, -0.6, 0.0), fingL=(0.6, -0.6, 0.0), crouch=0.5,
           stance=6.0), 100),
        (K(handR=add(REST_R, (2, 3, -1)), handL=add(REST_L, (2, 3, 1)), stance=5.5), 100),
        (K(handR=add(REST_R, (1, 1, 0)), handL=add(REST_L, (1, 1, 0)), lag=0.5), 110),
        (K(lag=0.2), 120),
        (K(), 150),
    ]


def guard(base=None):
    b = base or {}
    G = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
    hold = dict(handR=(11.0, 44.0, 5.0), handL=(11.0, 44.0, -5.0), fingR=(0.0, 1.0, -0.2), fingL=(0.0, 1.0, 0.2),
                poleR=(-0.3, -1.0, 0.8), poleL=(-0.3, -1.0, -0.8), zR=46.0, zL=45.9)
    return [
        (K(b, handR=add(REST_R, (3, 5, -1)), handL=add(REST_L, (3, 5, 1)), fingR=FWD, fingL=FWD), 55),
        (K(b, G, handR=(8.0, 38.0, 8.0), handL=(8.0, 38.0, -8.0), fingR=UP, fingL=UP, crouch=0.5), 55),
        (K(b, G, hold, handR=(10.0, 42.0, 6.0), handL=(10.0, 42.0, -6.0), crouch=1.2, lean=-0.3, brow=1), 55),
        (K(b, G, hold, crouch=1.8, lean=-0.6, brow=1, lag=-0.5), 55),
        (K(b, G, hold, crouch=2.0, lean=-0.7, brow=1, lag=-0.8), 120),
        (K(b, G, handR=(7.0, 35.0, 10.0), handL=(7.0, 35.0, -10.0), fingR=UP, fingL=UP, crouch=1.0), 120),
        (K(b, handR=add(REST_R, (2, 3, 0)), handL=add(REST_L, (2, 3, 0)), fingR=(0.4, -1.0, 0.0), fingL=(0.4, -1.0, 0.0)), 120),
        (K(b, PW) if b else K(b), 120),
    ]


_PB = dict(lag=0.5)
TABLE = {
    'fidget_water': fidget_water(),
    'fidget_shawl': fidget_shawl(),
    'idle': idle(),
    'walk': walk(),
    'primary': fling(),
    'secondary': seal(),
    'special': special(),
    'guard': guard(),
    'hit': g_hit(REST_R, REST_L),
    'defeat': g_defeat(REST_R, REST_L),
    'jump': g_jump(REST_R, REST_L),
    'stair_up': g_stairs(REST_R, REST_L, True),
    'stair_down': g_stairs(REST_R, REST_L, False),
    'dodge': g_dodge(REST_R, REST_L),
    'powered_idle': idle(dict(PW), PWH['handR'], PWH['handL']),
    'powered_walk': walk(dict(fingR=OUT_R, fingL=OUT_L, poleR=PW['poleR'], poleL=PW['poleL'], stance=6.5), (5.0, 29.0, 17.0),
                         (5.0, 29.0, -17.0), armR=1.5, armL=1.5, lift=2.5),
    'powered_primary': fling(dict(stance=6.5), fast=True),
    'powered_guard': guard(dict(stance=6.5)),
    'powered_exit': powered_exit(),
}
import mirra as _m  # noqa: E402
home_feet(TABLE, _m.P0)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0)       # no skating: feet shuffle at most 3 px a drawing


FIDGETS = ['fidget_water', 'fidget_shawl']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = _m.P0()
_SH = {}
for _c, _a in {'primary': [2, 3, 6], 'secondary': [2, 5], 'special': [1, 3], 'powered_primary': [1, 4], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # v2: arc in-betweens
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 5, 'secondary': 4, 'special': 4, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](2)], 'secondary': [_SH['secondary'](2)]}     # the loads, held

# v2 aim within the facing (CONTRACT V2.8): the fling's palms swing about the shoulders onto the
# aim, so the water leaves along the shot's direction; the drawings either side turn half way.
AIM_CLIPS = ('primary', 'powered_primary')


def _rot(a, b):
    a, b = np.array(a, float) / np.linalg.norm(a), np.array(b, float) / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a.dot(b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def aim_table(clip, fc, deg):
    M = _rot((1.0, 0.0, 0.0), anim.aim_body(fc, deg))
    keys = TABLE[clip]
    aimed = [bool(P.get('handR')) and P['handR'][0] >= 12.0 for P, _ in keys]
    out = []
    for i, (P, ms) in enumerate(keys):
        w = 1.0 if aimed[i] else (0.5 if (i > 0 and aimed[i - 1]) or (i + 1 < len(keys) and aimed[i + 1]) else 0.0)
        if w:
            P = dict(P)
            for key, lat in (('R', 1), ('L', -1)):
                if P.get('hand' + key):
                    sh = np.array([P.get('lean', 0.0), 41.0 + P.get('breath', 0), SHW * lat])
                    h0 = np.array(P['hand' + key])
                    h1 = sh + M @ (h0 - sh)
                    P['hand' + key] = tuple(round(float(x), 3) for x in h0 + (h1 - h0) * w)
                    if P.get('fing' + key):
                        f0 = np.array(P['fing' + key], float)
                        f1 = M @ f0
                        fv = f0 + (f1 - f0) * w
                        P['fing' + key] = tuple(round(float(x), 3) for x in fv / np.linalg.norm(fv))
        out.append((P, ms))
    return out
RELEASE_ANCHOR = {'primary': 'palm_R', 'secondary': 'palm_R', 'special': 'hand_R', 'powered_primary': 'palm_R'}

# Powered variants of hit, dodge, jump, stairs and secondary, ending on the powered rest pose.
_PWF = lambda P: dict(P, stance=max(P.get('stance', 5.5), 6.5))   # noqa: E731
powered_from(TABLE, RELEASE, RELEASE_ANCHOR, _PWF, PW, (REST_R, REST_L))
for _c in ('powered_hit', 'powered_secondary', 'powered_dodge'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0)
powered_entry(TABLE, _PWF, PW, (REST_R, REST_L), _m.P0)

EQUIP = {
    'gem': dict(always=True, may_hide={'N', 'W', 'SW', 'NW'}),
    'tail': dict(always=True, may_hide={'S', 'E', 'SE'}),
    'shawl': dict(always=True),
    'bands': dict(always=True, may_hide={'N', 'W', 'E', 'S', 'SE', 'SW', 'NE', 'NW'}),
}

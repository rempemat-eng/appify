"""Tam's animation table (17 contract clips; the orange-robed male monk of the redesign).
Hands stay OPEN in every drawing: strikes land with the heel of the palm, fingers up; the frost
ridge is laid by both palms pressed flat on the ground ahead from a kneel (within reach,
never stretched).  Glacier Form (special) grows ice round the same forearms and shins
(P ice 0 -> 1); it stays through every powered clip and powered_exit clears it.
"""
import anim
from tam import REST_R, REST_L, HANG
from anim_morel import K, add, home_feet, spread_feet, powered_from, powered_entry, g_idle, g_walk, g_stairs, g_hit, g_defeat, g_jump, g_dodge

A_STRIDE = 9.0
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2) * 1.05, 1)        # drawn at tam.SCALE
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

UP = (0.2, 1.0, 0.0)                        # fingers up, palm forward
FWD = (1.0, 0.15, 0.0)                      # fingers forward, palm up (chambered at the hip)
ST = dict(footR=(-4.0, 0.0), footL=(5.0, 0.0))
PWH = dict(handR=(8.0, 37.0, 10.0), handL=(10.0, 40.0, -7.0), fingR=UP, fingL=UP)
PW = dict(PWH, ice=1.0, crouch=1.5, footR=(-3.0, 0.0), footL=(4.0, 0.0))


# --------------------------------------------------------------------------------- v2 idle, walk, fidgets
def idle(base=None, RR=REST_R, RL=REST_L):
    """v2 idle, 12 drawings in 1.6 s: a slow, deep breath (the monk's), the hands ride on it, the
    sash ends swing half a beat behind, one blink."""
    base = base or {}
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.9, 1.0, 0.9, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    sw = [0.0, 0.1, 0.2, 0.3, 0.4, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1, -0.05]      # v4: his weight settles onto the right leg and back
    return [(K(base, breath=br[i], lag=lag[i], blink=(i == 10), hipx=sw[i], handR=add(RR, (0, 0.5 * br[i], 0)),
               handL=add(RL, (0, 0.5 * br[i], 0))), ms[i]) for i in range(12)]


def walk(base=None, RR=REST_R, RL=REST_L, armR=2.5, armL=4.0):
    """v2 walk, 12 drawings a stride; the robe's end and sash trail."""
    base = base or {}
    n = anim.WALK_N2
    keys = []
    for g in anim.gait(n, A_STRIDE, 2.8, bob=1.0):     # v4: a lower lift keeps a foot down in the turned drawings
        s = g['swing']
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.2 + 0.8 * abs(s),
                       handR=add(RR, (-armR * s, 0.5 + 0.6 * abs(s), 0)), handL=add(RL, (armL * s, 0.6 * abs(s), 0))),
                     WALK_LOOP2 * 1000 / n))
    return keys


def fidget_beads():
    """Lifts the mala on his chest with the right hand and tells two beads with the thumb."""
    B = dict(handR=(6.0, 36.0, 4.0), fingR=(0.2, 1.0, -0.3), zR=27.0)
    return [(K(), 150), (K(handR=(5.0, 30.0, 9.0), fingR=(0.4, 0.2, -0.2)), 110),
            (K(B, brow=1), 120), (K(B, handR=(6.0, 35.0, 4.0), face='shut'), 160),          # one bead
            (K(B, face='shut'), 140), (K(B, handR=(6.0, 35.0, 4.0), face='shut'), 160),      # two
            (K(B), 130), (K(handR=(5.0, 30.0, 9.0), fingR=(0.4, -0.4, 0.0), blink=True), 110),
            (K(handR=add(REST_R, (1, 1, 0))), 120), (K(), 170)]


def fidget_shoulders():
    """v4: rolls his shoulders - up, back, down - with a slow breath out, the hands riding along."""
    up = lambda d: dict(handR=add(REST_R, (0, d, 0)), handL=add(REST_L, (0, d, 0)))
    return [(K(), 150), (K(up(1.0), breath=1, lean=0.2), 110), (K(up(2.0), breath=2, lean=-0.4, face='shut'), 140),     # up
            (K(up(1.5), breath=2, lean=-1.2, face='shut', lag=0.4), 140),                                            # back
            (K(up(-0.5), breath=-1, lean=-0.6, crouch=0.4, face='shut', lag=0.8), 150),                               # down, out
            (K(up(-0.5), breath=-1, lean=0.3, crouch=0.6, lag=1.0), 130), (K(lean=0.2, crouch=0.2, lag=0.5, blink=True), 120),
            (K(), 170)]


def strike(base=None, fast=False):
    b = base or {}
    G = dict(handL=(9.0, 38.0, -6.0), fingL=UP)
    keys = [
        (K(b, ST, G, handR=(3.0, 30.0, 12.0), fingR=FWD, lean=0.3), 60),                                     # 0 ready
        (K(b, ST, G, handR=(-2.5, 31.0, 11.5), fingR=FWD, lean=-0.6, crouch=1.0), 45),                       # 1 chamber
        (K(b, ST, G, handR=(-3.5, 31.5, 11.0), fingR=FWD, lean=-1.0, crouch=1.5, brow=1), 80),               # 2 load (held)
        (K(b, ST, G, handR=(8.0, 34.0, 9.5), fingR=(0.4, 1.0, 0.0), lean=1.5, crouch=1.5, brow=1), 30),      # 3 drive
        (K(b, ST, handR=(18.5, 34.5, 9.5), fingR=UP, handL=(1.0, 32.0, -12.0), fingL=FWD, lean=3.5, crouch=2.5,
           brow=1), 40),                                                                              # 4 contact (release)
        (K(b, ST, handR=(19.0, 34.5, 9.5), fingR=UP, handL=(0.5, 32.0, -12.0), fingL=FWD, lean=3.5, crouch=2.5,
           brow=1), 60),                                                                              # 5 held
        (K(b, ST, handR=(9.0, 38.0, 8.0), fingR=UP, handL=(5.0, 34.0, -10.0), fingL=UP, lean=2.0, crouch=1.5), 60),   # 6 withdraw
        (K(b, ST, handR=(4.0, 32.0, 12.0), fingR=(0.6, 0.4, 0.0), lean=1.0, crouch=1.0,
           handL=add(REST_L, (2, 4, 0)), fingL=(0.4, -1.0, 0.0)), 70),                                       # 7 recover
        (K(b, handR=add(REST_R, (1, 2, 0)), fingR=(0.3, -1.0, 0.0)), 90),                                   # 8 settle
        (K(b), 120),
    ]
    if fast:
        keys = [keys[0], keys[2], keys[3], keys[4], keys[6], keys[7], keys[8], keys[9]]
        keys[-1] = (K(b, PW), 120)
    return keys


def ridge():
    W = dict(footR=(6.0, 0.0), footL=(-6.0, 1.5))                       # going down on the left knee
    # v4 (26 Oct): a real kneel - the right foot planted ahead, the left knee down with the toes
    # tucked behind, the back long and leaning in, both palms flat on the ground ahead
    D = dict(footR=(8.0, 0.0), footL=(-9.5, 3.0), handR=(13.0, 19.0, 8.0), handL=(13.0, 19.0, -8.0),
             fingR=(1.0, -0.2, 0.0), fingL=(1.0, -0.2, 0.0), crouch=13.0, breath=-4, lean=9.0, brow=1)
    return [
        (K(handR=(6.0, 33.0, 9.0), handL=(6.0, 33.0, -9.0), fingR=FWD, fingL=FWD), 60),                                  # 0 palms up
        (K(handR=(5.0, 44.0, 9.0), handL=(5.0, 44.0, -9.0), fingR=UP, fingL=UP, lean=-0.5, zR=46.0, zL=46.0), 60),      # 1 lift
        (K(handR=(5.0, 46.0, 8.5), handL=(5.0, 46.0, -8.5), fingR=UP, fingL=UP, lean=-0.8, crouch=1.0, brow=1, zR=46.0, zL=46.0), 90),  # 2 load
        (K(W, handR=(11.0, 26.0, 9.0), handL=(11.0, 26.0, -9.0), fingR=(1.0, -0.6, 0.0), fingL=(1.0, -0.6, 0.0),
           crouch=9.0, breath=-2, lean=6.0, brow=1), 35),                                                                  # 3 drop
        (K(D, face='shut'), 40),                                                                                         # 4 palms to the ground (release)
        (K(D), 80),                                                                                                      # 5 held
        (K(W, handR=(10.0, 26.0, 10.0), handL=(10.0, 26.0, -10.0), fingR=(0.6, -1.0, 0.0), fingL=(0.6, -1.0, 0.0),
           crouch=9.0, breath=-2, lean=6.0), 70),                                                                           # 6 rise
        (K(handR=add(REST_R, (2, 2, 0)), handL=add(REST_L, (2, 2, 0)), crouch=2.0, lean=1.0), 80),
        (K(), 110),
    ]


def special():
    J = dict(handR=(8.0, 41.0, 2.5), handL=(8.0, 41.0, -2.5), fingR=(0.1, 1.0, -0.2), fingL=(0.1, 1.0, 0.2))
    S = dict(handR=(10.0, 29.0, 11.0), handL=(10.0, 29.0, -11.0), fingR=(1.0, -0.5, 0.2), fingL=(1.0, -0.5, -0.2))
    return [
        (K(J, crouch=0.5), 90),                                                                    # 0 palms together
        (K(J, crouch=1.0, breath=1, face='shut'), 90),                                             # 1 breath in
        (K(S, crouch=1.5, brow=1, ice=0.15, footR=(-2.0, 0.0), footL=(3.0, 0.0)), 70),            # 2 palms press down and out
        (K(S, crouch=2.0, brow=1, ice=0.4, footR=(-3.0, 0.0), footL=(4.0, 0.0)), 70),             # 3 the ice takes
        (K(PW, ice=0.7, brow=1), 60),                                                              # 4 up into the form (release)
        (K(PW, ice=0.9), 90),
        (K(PW, ice=1.0, breath=1), 110),
        (K(PW), 120),
    ]


def powered_exit():
    return [
        (K(PW), 100),
        (K(PW, crouch=2.0, handR=(8.0, 35.0, 11.0), handL=(9.0, 37.0, -9.0), brow=1), 90),
        (K(PW, ice=0.75, crouch=2.0, handR=(9.0, 30.0, 12.0), handL=(9.0, 30.0, -12.0), fingR=(1.0, -0.6, 0.0),
           fingL=(1.0, -0.6, 0.0)), 90),                                                            # ice cracking
        (K(PW, ice=0.45, crouch=1.5, handR=(7.0, 28.0, 13.0), handL=(7.0, 28.0, -13.0), fingR=(0.6, -1.0, 0.0),
           fingL=(0.6, -1.0, 0.0)), 90),
        (K(ice=0.2, crouch=1.0, handR=add(REST_R, (3, 2, 0)), handL=add(REST_L, (3, 2, 0)), fingR=(0.4, -1.0, 0.0),
           fingL=(0.4, -1.0, 0.0), footR=(-2.0, 0.0), footL=(3.0, 0.0)), 100),
        (K(ice=0.0, crouch=0.5, handR=add(REST_R, (1, 1, 0)), handL=add(REST_L, (1, 1, 0))), 110),
        (K(breath=1), 120),
        (K(), 150),
    ]


def guard(base=None):
    b = base or {}
    G = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
    hold = dict(handR=(10.0, 45.0, 4.5), handL=(9.0, 43.0, -5.0), fingR=(0.1, 1.0, -0.2), fingL=(0.1, 1.0, 0.2),
                poleR=(-0.3, -1.0, 0.8), poleL=(-0.3, -1.0, -0.8), zR=46.0, zL=45.9)
    return [
        (K(b, handR=add(REST_R, (3, 5, -1)), handL=add(REST_L, (3, 5, 1)), fingR=(0.6, 0.2, 0.0), fingL=(0.6, 0.2, 0.0)), 55),
        (K(b, G, handR=(8.0, 38.0, 8.0), handL=(8.0, 37.0, -8.0), fingR=UP, fingL=UP, crouch=0.5), 55),
        (K(b, G, hold, handR=(9.5, 43.0, 5.5), handL=(8.5, 41.0, -6.0), crouch=1.2, lean=-0.3, brow=1), 55),
        (K(b, G, hold, crouch=1.8, lean=-0.6, brow=1), 55),
        (K(b, G, hold, crouch=2.0, lean=-0.7, brow=1), 120),
        (K(b, G, handR=(7.0, 35.0, 10.0), handL=(7.0, 34.0, -10.0), fingR=UP, fingL=UP, crouch=1.0), 120),
        (K(b, handR=add(REST_R, (2, 3, 0)), handL=add(REST_L, (2, 3, 0)), fingR=(0.4, -1.0, 0.0), fingL=(0.4, -1.0, 0.0)), 120),
        (K(b, PW) if b else K(b), 120),
    ]


TABLE = {
    'fidget_beads': fidget_beads(),
    'fidget_shoulders': fidget_shoulders(),
    'idle': idle(),
    'walk': walk(),
    'primary': strike(),
    'secondary': ridge(),
    'special': special(),
    'guard': guard(),
    'hit': g_hit(REST_R, REST_L),
    'defeat': g_defeat(REST_R, REST_L, last=dict(fingR=(0.3, -1.0, 0.0), fingL=(0.3, -1.0, 0.0))),
    'jump': g_jump(REST_R, REST_L),
    'stair_up': g_stairs(REST_R, REST_L, True),
    'stair_down': g_stairs(REST_R, REST_L, False),
    'dodge': g_dodge(REST_R, REST_L),
    'powered_idle': idle(dict(PW), PWH['handR'], PWH['handL']),
    'powered_walk': walk(dict(ice=1.0, fingR=UP, fingL=UP), PWH['handR'], PWH['handL'], armR=1.5, armL=1.5),
    'powered_primary': strike(dict(ice=1.0), fast=True),
    'powered_guard': guard(dict(ice=1.0)),
    'powered_exit': powered_exit(),
}
import tam as _m  # noqa: E402
home_feet(TABLE, _m.P0)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0)       # no skating: feet shuffle at most 3 px a drawing


# v2: arc in-betweens after the key poses, the load held
FIDGETS = ['fidget_beads', 'fidget_shoulders']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = _m.P0()
_SH = {}
for _c, _a in {'primary': [2, 3, 6], 'secondary': [2, 3, 6], 'special': [1, 3], 'powered_primary': [1, 2]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)

_P = ['powered_idle', 'powered_walk', 'powered_primary', 'powered_guard']
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 4, 'secondary': 4, 'special': 4, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](2)], 'secondary': [_SH['secondary'](2)]}
RELEASE_ANCHOR = {'primary': 'palm_R', 'secondary': 'palm_L', 'special': 'hand_R', 'powered_primary': 'palm_R'}

# Powered variants of hit, dodge, jump, stairs and secondary, ending on the powered rest pose.
_PWF = lambda P: dict(P, ice=1.0)
powered_from(TABLE, RELEASE, RELEASE_ANCHOR, _PWF, PW, (REST_R, REST_L))
for _c in ('powered_hit', 'powered_secondary', 'powered_dodge'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0)
powered_entry(TABLE, _PWF, PW, (REST_R, REST_L), _m.P0)
_k = TABLE['powered_secondary'][3]
TABLE['powered_secondary'][3] = (dict(_k[0], footL=(_k[0]['footL'][0], 2.5)), _k[1])   # the left foot steps back (lifted) to kneel

EQUIP = {
    'beads': dict(always=True, may_hide={'N', 'NE', 'NW'}),
    'sash': dict(always=True),
    'robe': dict(always=True),
    'ice': dict(clips=dict({c: list(range(len(TABLE[c]))) for c in _P},
                           **{'powered_' + c: list(range(len(TABLE[c]))) for c in ('hit', 'dodge', 'jump', 'stair_up', 'stair_down', 'secondary')},
                           special=list(range(RELEASE['special'], len(TABLE['special']))), powered_exit=[0, 1, 2, 3])),
}

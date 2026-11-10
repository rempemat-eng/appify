"""Velvet's animation table (17 contract clips).  The sabre is in the LEFT hand and the lantern
in the RIGHT hand in every drawing of every clip; nothing is sheathed or put down.

  - primary (sabre): the left hand raises the sabre over the left shoulder, cuts diagonally down
    across the body to the right hip, follows through and returns the point forward; the lantern
    hand draws back to the right hip and stays there.
  - secondary (lantern flare): the right hand thrusts the lantern forward at chest height, the
    shutter snaps open at the release (lamp 2) and closes again; the sabre hand holds guard.
  - special: the lantern is lifted high and its shutter opened for good (lamp 3, the powered
    state) and the sabre comes up to en garde.  Powered clips keep both items and lamp 3.
  - powered_exit: the shutter closes (lamp 1) and both hands return to rest, still holding both.
"""
import numpy as np
import anim
from velvet import REST_R, REST_L, SAB0, P0 as _P0
from anim_morel import K, add, home_feet, spread_feet, powered_from, powered_entry, g_idle, g_walk, g_stairs, g_hit, g_defeat, g_jump, g_dodge

A_STRIDE = 9.5
# v2 (Matt 25 Oct): 15 % faster with the same stride, so a quicker cadence: 12 drawings in 0.487 s
WALK_SPEED = round(67.9 * 1.15, 1)                            # 78.1 px/s
WALK_LOOP = 4 * A_STRIDE / WALK_SPEED
FACINGS = anim.FACINGS8
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

PW = dict(lamp=3, handL=(9.0, 34.0, -9.0), sab=(0.7, 0.5, -0.5), handR=(9.0, 31.0, 12.0),
          footR=(-3.0, 0.0), footL=(4.0, 0.0))                         # powered: en garde, lantern open
ST = dict(footR=(-3.5, 0.0), footL=(5.0, 0.0))                         # duellist's stance: left foot forward


def idle(base=None, powered=False):
    """v2 breathing idle, 12 drawings in 1.6 s: the chest rises 1 px, the hands ride with it, the
    coat tails and the lantern answer half a beat later, one blink."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.7, 0.5, 0.3, 0.1, 0.0, -0.1]
    lsw = [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    if powered:
        RR, RL = PW['handR'], PW['handL']
        b = dict(lamp=3, footR=PW['footR'], footL=PW['footL'])
    else:
        RR, RL = REST_R, REST_L
        b = dict(base or {})
    keys = []
    for i in range(12):
        k = K(b, breath=br[i], lag=lag[i], lsw=lsw[i], blink=(i == 10),
              handR=add(RR, (0, 0.5 * br[i], 0)), handL=add(RL, (0, 0.5 * br[i], 0)))
        if powered:
            k['sab'] = (0.7, 0.5 + 0.04 * [0, 0, 1, 2, 2, 2, 1, 0, -1, -1, -1, 0][i], -0.5)
        keys.append((k, ms[i]))
    return keys


def walk(powered=False):
    """v2 walk: 12 drawings a stride, the lantern swings against the step, the tails bounce."""
    n = anim.WALK_N2
    keys = []
    RR, RL = (PW['handR'], PW['handL']) if powered else (REST_R, REST_L)
    arm = (1.0, 1.0) if powered else (2.5, 4.0)
    for i, g in enumerate(anim.gait(n, A_STRIDE, 3.5, bob=1.0)):
        s = g['swing']
        k = K(footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.6 + 0.8 * abs(s) + 0.4 * g['bob'],
              lsw=round(1.2 * s),
              handR=add(RR, (-arm[0] * s, 0.5 + 0.6 * abs(s), 0)), handL=add(RL, (arm[1] * s, 0.6 * abs(s), 0)))
        k.update(dict(lamp=3, sab=PW['sab']) if powered else dict(sab=(0.75 + 0.1 * s, -0.7, -0.25)))
        keys.append((k, WALK_LOOP * 1000 / n))
    return keys


# ---------------------------------------------------------------- idle fidgets (v2)
def fidget_glass():
    """Lifts the lantern to eye level, taps the glass with the sabre's knuckle-bow, watches the
    flame steady, lowers it."""
    up = (8.0, 44.0, 9.0)
    tap = (8.5, 42.0, 1.5)
    return [
        (K(), 150),
        (K(handR=(6.0, 34.0, 12.0), lsw=-1), 110),
        (K(handR=up, lsw=1, brow=1), 120),
        (K(handR=up, handL=(7.0, 36.0, -4.0), sab=(0.7, -0.3, -0.6), brow=1), 110),
        (K(handR=up, handL=tap, sab=(0.5, -0.6, -0.6), brow=1), 70),                       # tap
        (K(handR=add(up, (0.3, 0.3, 0)), handL=add(tap, (-1.0, -0.5, -1.5)), sab=(0.5, -0.6, -0.6), lsw=1), 70),
        (K(handR=up, handL=tap, sab=(0.5, -0.6, -0.6), lsw=-1), 70),                        # tap
        (K(handR=add(up, (0.3, 0.3, 0)), handL=(7.0, 36.0, -5.0), sab=(0.7, -0.4, -0.5), lsw=1), 160),
        (K(handR=up, handL=(6.0, 31.0, -10.0), face='shut'), 90),
        (K(handR=up, handL=(5.5, 28.0, -12.0)), 150),
        (K(handR=(6.0, 34.0, 12.0), lsw=1), 120),
        (K(lsw=-1), 110),
        (K(), 170),
    ]


def fidget_flourish():
    """Turns the sabre through a small flourish in front of her and brings it back to rest."""
    h = (9.0, 33.0, -8.0)
    dirs = [(1.0, 0.0, -0.3), (0.5, 1.0, -0.3), (-0.4, 0.8, -0.6), (-0.3, -0.4, -1.0), (0.6, -0.9, -0.4), (1.0, 0.2, -0.4)]
    keys = [(K(), 140), (K(handL=(7.0, 30.0, -11.0), sab=(0.85, -0.4, -0.3)), 100)]
    for i, d in enumerate(dirs):
        a = i * 1.05
        keys.append((K(handL=add(h, (0.8 * np.cos(a), 1.2 * np.sin(a), 0.0)), sab=d, lean=0.2, lag=0.3, brow=1 if i < 4 else 0), 60))
    keys += [(K(handL=(8.0, 31.0, -9.0), sab=(0.9, 0.3, -0.4), lean=0.3), 160),             # the point held up, a beat
             (K(handL=(6.0, 28.0, -12.0), sab=(0.8, -0.4, -0.3)), 120),
             (K(), 170)]
    return keys


def fidget_shoulders():
    """Rolls her shoulders and settles the coat: a lift, a shrug back, the tails swing."""
    return [
        (K(), 150),
        (K(breath=1, lean=-0.4, handR=add(REST_R, (0, 1.5, 0)), handL=add(REST_L, (0, 1.5, 0))), 120),
        (K(breath=2, lean=-0.9, handR=add(REST_R, (-1, 2.5, 0.5)), handL=add(REST_L, (-1, 2.5, -0.5)), lag=-0.5, face='shut'), 160),
        (K(breath=1, lean=-0.5, handR=add(REST_R, (-0.5, 1.0, 0.5)), handL=add(REST_L, (-0.5, 1.0, -0.5)), lag=1.2, lsw=-1), 110),
        (K(breath=0, lean=0.4, lag=1.8, lsw=0), 110),                  # (lsw 1 here hid the lantern behind her in NW)
        (K(lean=0.2, lag=-0.6, lsw=-1), 110),
        (K(lag=0.4, lsw=0), 120),
        (K(lag=-0.1), 120),
        (K(), 170),
    ]


def slash(powered=False):
    b = dict(lamp=3) if powered else {}
    LR = (-2.0, 30.0, 13.5)                                              # lantern drawn back to the right hip
    hi = (-4.0, 52.0, -10.0)
    keys = [
        (K(b, ST, handR=LR, handL=(8.0, 34.0, -10.0), sab=(0.8, 0.4, -0.4), lean=0.3), 60),                                   # 0 en garde
        (K(b, ST, handR=LR, handL=(2.0, 45.0, -11.0), sab=(0.3, 1.0, -0.2), lean=-0.5, poleL=(-0.4, -1.0, -0.6)), 45),       # 1 lift
        (K(b, ST, handR=LR, handL=hi, sab=(-0.8, 0.6, -0.3), lean=-1.5, crouch=1.0, brow=1, poleL=(-0.3, -1.0, -0.6)), 80),  # 2 load over the shoulder
        (K(b, ST, handR=LR, handL=add(hi, (-0.5, 1.0, 0)), sab=(-0.9, 0.5, -0.3), lean=-1.7, crouch=1.0, brow=1,
           poleL=(-0.3, -1.0, -0.6)), 40),                                                                                     # 3 held
        (K(b, ST, handR=LR, handL=(10.0, 48.0, -4.0), sab=(0.7, 0.8, 0.2), lean=1.5, brow=1, zL=46.0), 30),                  # 4 cut
        (K(b, ST, handR=LR, handL=(15.0, 36.0, 2.0), sab=(1.0, -0.4, 0.5), lean=3.5, crouch=2.0, brow=1, zL=31.0), 35),     # 5 contact (release)
        (K(b, ST, handR=LR, handL=(10.0, 27.0, 7.0), sab=(0.2, -1.0, 0.8), lean=3.0, crouch=2.5, zL=31.0), 55),             # 6 follow-through
        (K(b, ST, handR=LR, handL=(8.0, 30.0, -4.0), sab=(0.8, -0.5, -0.5), lean=2.0, crouch=1.5), 60),                       # 7 recover
        (K(b, ST, handR=add(REST_R, (-1, 1, 0)), handL=(7.0, 32.0, -9.0), sab=(0.8, 0.2, -0.4), lean=0.8), 80),               # 8 point forward
        (K(b, handL=add(REST_L, (1, 2, 0)), sab=(0.8, -0.5, -0.2)), 90),                                                     # 9 lower
        (K(b), 120),
    ]
    if powered:
        keys = [keys[0], keys[2], keys[3], keys[4], keys[5], keys[6], keys[7], keys[8]]
        keys[-1] = (K(b, PW), 120)
    return keys


def flare():
    G = dict(handL=(7.0, 32.0, -10.0), sab=(0.75, 0.35, -0.5), footR=(-2.0, 0.0), footL=(4.0, 0.0))
    return [
        (K(G, handR=add(REST_R, (-2, 2, 0)), lean=-0.3), 60),                                                  # 0 sabre to guard
        (K(G, handR=(-1.0, 36.0, 12.0), lean=-0.8, poleR=(-1.0, -0.5, 0.6)), 60),                             # 1 draw the lantern back
        (K(G, handR=(-2.0, 39.0, 11.5), lean=-1.0, brow=1, poleR=(-1.0, -0.5, 0.6)), 70),                     # 2 load
        (K(G, handR=(9.0, 41.0, 7.0), lean=1.0, brow=1), 35),                                                  # 3 thrust
        (K(G, handR=(15.0, 40.0, 5.0), lamp=2, lean=2.0, brow=1, face='shut'), 45),                           # 4 shutter open (release)
        (K(G, handR=(15.5, 40.0, 5.0), lamp=2, lean=2.0, brow=1), 70),                                        # 5 held
        (K(G, handR=(12.0, 37.0, 8.0), lamp=1, lean=1.0), 70),                                                # 6 shutter closed
        (K(G, handR=add(REST_R, (1, 3, 0)), lean=0.3), 80),                                                   # 7 lower
        (K(), 110),
    ]


def special():
    return [
        (K(handR=add(REST_R, (0, 3, 0)), handL=add(REST_L, (1, 2, 0)), crouch=0.5), 90),                                   # 0 gather
        (K(handR=(4.0, 44.0, 10.0), handL=(6.0, 30.0, -11.0), sab=(0.8, -0.3, -0.2), lean=-0.5, poleR=(-0.6, -1.0, 0.6)), 80),  # 1 lantern up
        (K(handR=(11.0, 47.0, 9.0), handL=(7.0, 31.0, -10.0), sab=(0.8, 0.0, -0.4), lean=-0.6, brow=1, zR=46.0), 90),     # 2 high
        (K(handR=(12.0, 47.5, 8.5), handL=(8.0, 32.0, -10.0), sab=(0.75, 0.3, -0.45), lean=-0.6, brow=1, zR=46.0), 70),      # 3 thumb on the shutter
        (K(handR=(12.5, 48.0, 8.5), lamp=3, handL=(8.5, 33.0, -9.5), sab=(0.7, 0.45, -0.5), lean=-0.4, brow=1, zR=46.0), 50),  # 4 open (release)
        (K(handR=(4.0, 46.0, 10.0), lamp=3, handL=(9.0, 34.0, -9.0), sab=(0.7, 0.5, -0.5), lean=-0.2,
           footR=(-2.0, 0.0), footL=(3.0, 0.0)), 90),                                                                       # 5 lower the light
        (K(PW, handR=(0.0, 34.0, 13.0)), 110),
        (K(PW), 120),
    ]


def powered_exit():
    return [
        (K(PW), 100),
        (K(PW, handR=(3.0, 40.0, 11.0), poleR=(-0.6, -1.0, 0.6)), 100),
        (K(PW, handR=(3.5, 41.0, 11.0), handL=(8.5, 33.0, -9.5), poleR=(-0.6, -1.0, 0.6)), 90),          # thumb on the shutter
        (K(lamp=1, handR=(3.5, 40.5, 11.0), handL=(8.0, 32.0, -10.0), sab=(0.75, 0.2, -0.45), poleR=(-0.6, -1.0, 0.6),
           footR=(-2.0, 0.0), footL=(3.0, 0.0)), 90),                                                         # closed
        (K(handR=add(REST_R, (0, 4, 0)), handL=(7.0, 30.0, -11.0), sab=(0.85, -0.3, -0.2)), 100),
        (K(handR=add(REST_R, (0, 1, 0)), handL=add(REST_L, (1, 1, 0))), 110),
        (K(breath=1), 80),
        (K(), 150),
    ]


def guard(powered=False):
    b = dict(lamp=3) if powered else {}
    G = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
    hold = dict(handL=(9.0, 40.0, -5.0), sab=(0.3, 1.0, -0.5), handR=(-3.0, 30.0, 13.5), poleL=(-0.4, -1.0, -0.6), zL=31.0)
    return [
        (K(b, handL=(6.0, 31.0, -11.0), sab=(0.8, 0.0, -0.5)), 55),
        (K(b, G, handL=(8.0, 35.0, -8.0), sab=(0.6, 0.6, -0.5), handR=(-1.0, 29.0, 13.5), crouch=0.5, zL=31.0), 55),
        (K(b, G, hold, handL=(9.0, 38.5, -5.0), crouch=1.2, lean=-0.4, brow=1), 55),
        (K(b, G, hold, crouch=1.8, lean=-0.7, brow=1), 55),
        (K(b, G, hold, crouch=2.0, lean=-0.8, brow=1), 120),
        (K(b, G, handL=(7.0, 33.0, -9.0), sab=(0.8, 0.3, -0.4), handR=add(REST_R, (-2, 2, 0)), crouch=1.0), 120),
        (K(b, handL=add(REST_L, (1, 2, 0)), sab=(0.8, -0.4, -0.2)), 120),
        (K(b, PW) if powered else K(b), 120),
    ]


def _sab_slump(i):
    return dict(sab=(0.9, -0.5, 0.3))


_slash, _sh = anim.densify(slash(), [1, 3, 5, 7, 8, 9], base=_P0())            # v2: in-betweens for anticipation and follow-through
_pslash, _psh = anim.densify(slash(True), [2, 4, 5, 6], base=_P0())
_flare, _fsh = anim.densify(flare(), [1, 2, 5, 6], base=_P0())
TABLE = {
    'idle': idle(),
    'walk': walk(),
    'primary': _slash,
    'secondary': _flare,
    'special': special(),
    'guard': guard(),
    'hit': g_hit(REST_R, REST_L),
    'defeat': g_defeat(REST_R, REST_L, last=dict(sab=(1.0, -0.15, 0.2), handR=(11.0, 30.5, 11.0))),
    'jump': g_jump(REST_R, REST_L),
    'stair_up': g_stairs(REST_R, REST_L, True),
    'stair_down': g_stairs(REST_R, REST_L, False),
    'dodge': g_dodge(REST_R, REST_L),
    'powered_idle': idle(powered=True),
    'powered_walk': walk(True),
    'powered_primary': _pslash,
    'powered_guard': guard(True),
    'powered_exit': powered_exit(),
    'fidget_glass': fidget_glass(),
    'fidget_flourish': fidget_flourish(),
    'fidget_shoulders': fidget_shoulders(),
}
_h, _ = anim.densify(TABLE['hit'], [0, 2], base=_P0())
TABLE['hit'] = _h
_d, _ = anim.densify(TABLE['dodge'], [1, 4], base=_P0())
TABLE['dodge'] = _d
# v2 secondary motion: tails trail the body (anim.follow); the lantern swings with them
for _c in ('primary', 'secondary', 'special', 'hit', 'dodge', 'defeat', 'powered_primary', 'powered_exit',
           'fidget_glass', 'fidget_flourish', 'fidget_shoulders'):
    TABLE[_c] = [(dict(P, lsw=round(P.get('lsw', 0) + 0.6 * (P['hair'] if 'hair' in P else 0))), ms)
                 for P, ms in anim.follow(TABLE[_c])]
    for P, _ in TABLE[_c]:
        P.pop('hair', None)
FIDGETS = ['fidget_glass', 'fidget_flourish', 'fidget_shoulders']
EXTRA = {c: dict(n=(9, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
for _i, (_P, _) in enumerate(TABLE['defeat']):
    # v2: she kneels with the sabre held point up against her shoulder (laid flat, the blade would
    # reach past the cell toward the camera in the three-quarter facings)
    if _i >= 1:
        _P['sab'] = [(0.8, -0.3, -0.4), (0.7, 0.2, -0.4)][_i - 1] if _i < 3 else (0.35, 0.9, -0.25)
for _P, _ in TABLE['jump']:
    _P['sab'] = (0.8, -0.25, -0.5)

import velvet as _m  # noqa: E402
home_feet(TABLE, _m.P0)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0)       # no skating: feet shuffle at most 3 px a drawing


RELEASE = {'primary': _sh(5), 'secondary': _fsh(4), 'special': 4, 'powered_primary': _psh(4)}
RELEASE_ANCHOR = {'primary': 'blade_tip', 'secondary': 'lantern', 'special': 'lantern', 'powered_primary': 'blade_tip'}

# Powered variants of hit, dodge, jump, stairs and secondary, ending on the powered rest pose.
_PWF = lambda P: dict(P, lamp=2 if P.get('lamp') == 2 else 3)
powered_from(TABLE, RELEASE, RELEASE_ANCHOR, _PWF, PW, (REST_R, REST_L))
for _c in ('powered_hit', 'powered_secondary', 'powered_dodge'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0)
powered_entry(TABLE, _PWF, PW, (REST_R, REST_L), _m.P0)
# v2 (cast.equipment): a powered drawing that names no hand between two that do would snap to
# the rest hand for one drawing (powered_hit 6: the lantern hid behind her in W); ease it instead
for _c, _keys in TABLE.items():
    for _h in ('handR', 'handL'):
        for _i in range(1, len(_keys) - 1):
            _a, _b, _n = _keys[_i - 1][0].get(_h), _keys[_i][0].get(_h), _keys[_i + 1][0].get(_h)
            if _b is None and _a is not None and _n is not None:
                _keys[_i][0][_h] = tuple((x + y) / 2 for x, y in zip(_a, _n))

EQUIP = {
    # v2: from behind on the sabre's far side (NE) her back hides the sabre as in N; NW hides the
    # lantern (far hand from behind) as W and N do; SW hides the scabbard on the far hip as S and W do
    'sabre': dict(always=True, may_hide={'N', 'NE'}),
    'lantern': dict(always=True, may_hide={'W', 'N', 'NW'}),
    'scabbard': dict(always=True, may_hide={'S', 'W', 'SW'}),
}


# v2 (26 Oct review: the strike is never hidden): from behind (N and its in-betweens) the cut and
# the lantern's flare happen beside her body instead of in front of it, where her body would cover
# them: the sabre hand and blade swing out to her left, the lantern out to her right.
def _out(P, hand, lat, dk=None):
    P = dict(P)
    h = P.get(hand)
    if h is not None:
        P[hand] = (h[0] - 2.0, h[1], lat * max(abs(h[2]), 13.0))
    if dk and P.get(dk) is not None:
        x, y, z = P[dk]
        z = lat * max(abs(z), 0.75)
        n = (x * x + y * y + z * z) ** 0.5
        P[dk] = (round(x / n, 3), round(y / n, 3), round(z / n, 3))
    return P


_BACK = {}


def facing_table(clip, fc):
    if fc not in ('N', 'NE', 'NW') or clip not in RELEASE or clip == 'special':
        return TABLE[clip]
    if clip not in _BACK:
        r = RELEASE[clip]
        hand, lat, dk = ('handR', 1, None) if clip.endswith('secondary') else ('handL', -1, 'sab')
        _BACK[clip] = [(_out(P, hand, lat, dk) if r - 1 <= i <= r + 2 else P, ms) for i, (P, ms) in enumerate(TABLE[clip])]
    return _BACK[clip]

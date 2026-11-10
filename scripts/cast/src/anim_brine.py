"""Brine's animation table (copy of the anim_bramble.py pattern).  Poses list what differs from
brine.P0; the rig renders S, N, E and W.  Timings are refitted to Codex's durations and release
times by anim.fit_timing.

Logic (Codex identity table): one breathing hose pack -> regulator -> helmet in every drawing; one
harpoon gun with its reel; the primary fires the harpoon (from the release drawing the harpoon is
out of the muzzle and its tether is a scene effect anchored at the 'muzzle' anchor); the
secondary cranks the reel on the same gun and the harpoon comes back into the muzzle.  Pressure
Brace (special): the right hand leaves the grip (the left hand holds the gun by the fore grip),
opens the regulator valve on the helmet, the glass lights and he settles into a braced stance.
"""
import math
import numpy as np
import anim
from brine import GRIP0, AIM0

A_STRIDE = 8.5
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 6.5 / anim.STAIR_LOOP, 1)

REG = (-1.0, 61.0, 13.5)                   # right hand at the regulator valve (helmet right rear)
SHOULDER = dict(grip=(6.0, 39.0, 6.0), aim=(1.0, 0.02, -0.08))     # gun up, stock at the shoulder
LOW = dict(grip=GRIP0, aim=AIM0)
HIP = dict(grip=(5.0, 31.0, 6.5), aim=(1.0, -0.02, -0.25))         # braced hip-fire (powered)
BR = dict(footR=(3.5, 0.0), footL=(-3.5, 0.0), stance=6.8)         # braced stance


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def mixp(a, b, t):
    return anim.lerp(a, b, t)


# --------------------------------------------------------------------------------- idle, walk
def idle(powered=False):
    """v2 idle, 12 drawings in 1.6 s: the breath lifts the gun, the hose sways half a beat behind."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    base = K(LOW, press=1.0) if powered else K(LOW)
    g = base['grip']
    return [(K(base, breath=br[i], lag=lag[i], grip=add(g, (0, 0.5 * br[i], 0))), ms[i]) for i in range(12)]


def walk(powered=False):
    """v2 walk, 12 drawings a stride: the heavy boots, the gun bobbing a drawing after the step."""
    keys = []
    base = K(LOW, press=1.0) if powered else K(LOW)
    n = anim.WALK_N2
    gs = anim.gait(n, A_STRIDE, 3.0, bob=1.0)
    for i, g in enumerate(gs):
        s = g['swing']
        late = gs[(i - 1) % n]
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.2 + 0.8 * abs(s),
                       grip=add(base['grip'], (0.6 * late['swing'], 0.4 * abs(late['swing']) - 0.4 * late['bob'], 0))),
                     WALK_LOOP2 * 1000 / n))
    return keys


def fidget_glass():
    """Wipes the faceplate glass with the back of his left glove, then peers out."""
    W = dict(lmode='free', handL=(9.0, 58.0, -2.0))
    return [(K(LOW), 150), (K(LOW, lmode='free', handL=(6.0, 40.0, -9.0)), 110), (K(LOW, W, brow=1), 110),
            (K(LOW, W, handL=(9.0, 58.0, 3.0)), 90), (K(LOW, W, handL=(9.0, 58.0, -3.0)), 90), (K(LOW, W, handL=(9.0, 58.5, 2.0)), 90),
            (K(LOW, lmode='free', handL=(6.0, 42.0, -8.0)), 110), (K(LOW, lean=0.6), 160), (K(LOW), 170)]


def fidget_reel():
    """Gives the reel a quarter turn to take up slack, listens to the click."""
    R = dict(grip=(3.0, 33.0, 5.5), aim=(1.0, -0.05, -0.5), lmode='reel')
    return [(K(LOW), 150), (K(R, crank=0.0), 120), (K(R, crank=0.12, lean=-0.3), 90), (K(R, crank=0.25, lean=-0.4), 90),
            (K(R, crank=0.25, brow=1), 180), (K(LOW, lean=0.2), 130), (K(LOW), 170)]


def stairs(up=True):
    keys = []
    for g in anim.gait(8, 6.5, 6.5 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(LOW, footR=fr, footL=fl, bob=g['bob'], lean=2.0 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
                       grip=add(GRIP0, (0.5 * s, 0.5, 0))), 90))
    return keys


# --------------------------------------------------------------------------------- harpoon shot
def shot(powered=False):
    S = K(SHOULDER, BR)
    if powered:
        S = K(S, crouch=1.5, press=1.0)
        G = S['grip']
        return [
            (K(LOW, press=1.0), 60),
            (K(S, grip=add(G, (-1.0, -1.0, 0))), 50),                                    # snap up
            (K(S, lean=0.5), 60),                                                          # aim
            (K(S, loaded=False, recoil=3.0, lean=-1.5, lag=-1.0), 40),                     # RELEASE
            (K(S, loaded=False, recoil=1.5, lean=-0.8, lag=-0.5), 60),
            (K(S, loaded=False, lean=0.0), 80),
            (K(LOW, press=1.0, loaded=False), 100),
            (K(LOW, press=1.0, loaded=False), 130),
        ]
    G = S['grip']
    return [
        (K(LOW), 50),                                                                      # ready
        (K(LOW, BR, crouch=0.5, grip=add(GRIP0, (0.5, 2.0, -0.5))), 45),                    # set the feet
        (K(BR, grip=(5.0, 34.0, 6.5), aim=(1.0, -0.08, -0.4), crouch=1.0), 40),             # raise
        (K(S, grip=add(G, (-0.5, -0.5, 0)), crouch=1.0), 40),                               # stock to the shoulder
        (K(S, crouch=1.5, lean=0.5), 50),                                                   # aim
        (K(S, crouch=1.5, lean=0.8), 40),                                                   # squeeze (hold)
        (K(S, crouch=1.5, lean=0.8), 30),
        (K(S, loaded=False, recoil=3.0, crouch=1.0, lean=-1.5, lag=-1.2), 35),              # RELEASE: the harpoon leaves
        (K(S, loaded=False, recoil=2.0, crouch=1.0, lean=-1.2, lag=-0.8), 60),              # recoil absorbed
        (K(S, loaded=False, recoil=0.5, crouch=1.0, lean=-0.3), 80),                         # follow-through, tether paying out
        (K(BR, loaded=False, grip=(5.0, 34.0, 6.5), aim=(1.0, -0.08, -0.4), crouch=0.5), 90),
        (K(LOW, loaded=False), 130),                                                         # settle
    ]


# --------------------------------------------------------------------------------- reel
def reel():
    R = K(BR, grip=(3.0, 35.0, 5.0), aim=(1.0, 0.05, -0.7), lmode='reel', loaded=False)
    return [
        (K(LOW, loaded=False), 60),
        (K(R, crank=0.0, crouch=1.0), 70),                                 # left glove finds the reel
        (K(R, crank=0.25, crouch=1.5, lean=-0.5), 60),                     # brace back
        (K(R, crank=0.5, crouch=2.0, lean=-1.5, lag=-0.6), 60),
        (K(R, crank=0.75, crouch=2.0, lean=-2.0, lag=-1.0), 40),           # RELEASE: the tether snaps taut, the pull
        (K(R, crank=1.0, crouch=2.0, lean=-1.5, lag=-0.6), 60),
        (K(R, crank=1.25, crouch=1.5, lean=-0.8, loaded=True), 80),        # the harpoon back in the muzzle
        (K(LOW, crouch=0.5), 100),
        (K(LOW), 120),
    ]


# --------------------------------------------------------------------------------- guard
def guard(powered=False):
    """Brace: the gun across the chest as a bar, both hands on it, a lowered weighted stance."""
    p = dict(press=1.0) if powered else {}
    X = K(BR, grip=(7.0, 40.0, 9.0), aim=(0.2, 0.0, -1.0), **p)
    base = K(LOW, press=1.0) if powered else K(LOW)
    return [
        (K(base, crouch=0.5), 55),
        (K(BR, grip=(6.0, 34.0, 8.0), aim=(0.6, 0.0, -0.8), crouch=1.0, **p), 55),
        (K(X, crouch=2.0, lean=0.5), 55),
        (K(X, crouch=2.5, lean=1.0), 55),
        (K(X, crouch=3.0, lean=1.2), 120),                                  # HOLD
        (K(BR, grip=(6.0, 34.0, 8.0), aim=(0.6, 0.0, -0.8), crouch=1.5, **p), 120),
        (K(base, crouch=0.5), 120),
        (K(base), 120),
    ]


# --------------------------------------------------------------------------------- hit, defeat
def hit():
    return [
        (K(LOW, lean=-3.0, crouch=1.0, lag=-1.5, grip=add(GRIP0, (-1.0, 2.0, 1.0))), 35),
        (K(LOW, lean=-4.0, crouch=2.0, lag=-2.0, grip=add(GRIP0, (-1.5, 3.0, 1.5))), 65),
        (K(LOW, lean=-2.5, crouch=3.0, lag=-1.0, grip=add(GRIP0, (-1.0, 1.0, 1.0))), 90),
        (K(LOW, lean=-1.0, crouch=2.0, lag=0.5), 120),
        (K(LOW, lean=0.5, crouch=1.0, lag=1.0), 130),
        (K(LOW, lean=0.3, crouch=0.5, lag=0.6), 150),
        (K(LOW, lag=0.2), 160),
        (K(LOW), 180),
    ]


def defeat():
    """Down on the left knee, the gun lowered across his lap, both hands still on it."""
    k1 = dict(footR=(6.0, 0.0), footL=(-6.0, 2.0))
    k2 = dict(footR=(6.5, 0.0), footL=(-8.0, 2.5))
    lap = dict(aim=(0.6, -0.15, -1.0))
    return [
        (K(LOW, lean=-3.0, crouch=1.0, lag=-1.0), 80),
        (K(lean=2.0, crouch=5.0, grip=(3.0, 30.0, 7.0), aim=(0.8, -0.3, -0.9)), 100),
        (K(k1, lean=3.0, crouch=8.0, grip=(3.5, 29.5, 6.5), **lap), 100),
        (K(k2, lean=4.0, crouch=11.0, grip=(3.5, 29.5, 6.0), lag=0.5, **lap), 120),
        (K(k2, lean=5.5, crouch=12.0, grip=(3.5, 29.5, 6.0), lag=1.0, **lap), 150),
        (K(k2, lean=6.5, crouch=12.5, grip=(3.5, 29.5, 6.0), lag=1.2, **lap), 180),
        (K(k2, lean=7.0, crouch=12.5, grip=(3.5, 29.5, 6.0), lag=1.0, **lap), 240),
        (K(k2, lean=7.0, crouch=12.5, grip=(3.5, 29.5, 6.0), lag=0.8, **lap), 300),
    ]


# --------------------------------------------------------------------------------- jump, dodge
def jump():
    return [
        (K(LOW, crouch=4.0, lean=2.0, lag=0.5), 80),
        (K(LOW, crouch=1.0, lean=1.0, footR=(1.5, 1.0), footL=(-1.5, 1.5), grip=add(GRIP0, (0, 3, 0))), 55),
        (K(LOW, footR=(2.5, 6.0), footL=(-2.0, 7.5), grip=add(GRIP0, (0, 4, 0)), lag=-1.5), 80),
        (K(LOW, footR=(3.0, 7.5), footL=(-1.0, 8.5), grip=add(GRIP0, (0, 3, 0)), lag=-0.5), 110),
        (K(LOW, footR=(2.0, 3.0), footL=(-2.5, 4.0), grip=add(GRIP0, (0, 4, 0)), lag=1.5), 110),
        (K(LOW, crouch=5.0, lean=2.5, footR=(2.5, 0.0), footL=(-2.5, 0.0), grip=add(GRIP0, (1, -1, 0)), lag=1.5), 80),
        (K(LOW, crouch=3.0, lean=1.5, footR=(2.0, 0.0), footL=(-2.0, 0.0), lag=1.0), 70),
        (K(LOW), 115),
    ]


def dodge():
    return [
        (K(LOW, crouch=3.0, lean=3.0, footR=(3.0, 0.0), footL=(-4.0, 0.0)), 55),
        (K(LOW, crouch=5.0, lean=5.5, footR=(6.0, 2.0), footL=(-9.0, 0.0), lag=2.0), 45),
        (K(LOW, crouch=7.0, lean=7.0, footR=(8.5, 1.0), footL=(-9.5, 0.0), lag=3.0), 40),
        (K(LOW, crouch=7.0, lean=7.0, footR=(8.5, 0.0), footL=(-8.5, 0.5), lag=3.0), 45),
        (K(LOW, crouch=6.0, lean=5.5, footR=(7.0, 0.0), footL=(-7.0, 1.5), lag=2.0), 60),
        (K(LOW, crouch=4.0, lean=3.5, footR=(5.0, 0.0), footL=(-4.0, 0.0), lag=1.5), 70),
        (K(LOW, crouch=2.0, lean=2.0, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 80),
        (K(LOW), 100),
    ]


# --------------------------------------------------------------------------------- Pressure Brace
FREE = dict(gun='left', lmode='fore', handL=(8.0, 30.0, -3.0), aim=(0.45, 0.85, 0.1))   # left hand holds it upright in front


def special():
    return [
        (K(LOW), 80),
        (K(FREE, handR=(1.0, 36.0, 13.0)), 70),                                  # right hand leaves the grip
        (K(FREE, handR=(-1.0, 47.0, 14.0), poleR=(-0.2, -1.0, 0.8)), 70),
        (K(FREE, handR=REG, poleR=(-0.2, -1.0, 0.8)), 80),                      # on the valve
        (K(FREE, handR=add(REG, (0.5, -0.5, 0.5)), poleR=(-0.2, -1.0, 0.8), press=1.0, crouch=0.5, lag=1.0), 60),  # RELEASE: turned
        (K(FREE, handR=(1.0, 40.0, 13.5), press=1.0, crouch=1.0, lag=1.5), 70),
        (K(LOW, press=1.0, crouch=1.0, lag=1.0), 80),                       # back on the grip, braced
        (K(LOW, press=1.0, crouch=0.5, lag=0.5), 100),
        (K(LOW, press=1.0), 110),
    ]


def powered_exit():
    return [
        (K(LOW, press=1.0), 110),
        (K(FREE, handR=(1.0, 38.0, 13.0), press=1.0, crouch=1.0), 100),
        (K(FREE, handR=REG, poleR=(-0.2, -1.0, 0.8), press=1.0, crouch=0.5), 100),
        (K(FREE, handR=add(REG, (0.5, -0.5, 0.5)), poleR=(-0.2, -1.0, 0.8), press=0.0, lag=-0.8), 100),   # valve shut
        (K(FREE, handR=(-1.0, 47.0, 14.0), poleR=(-0.2, -1.0, 0.8), lag=-0.4), 90),
        (K(FREE, handR=(1.0, 36.0, 13.0)), 90),
        (K(LOW, crouch=0.5), 110),
        (K(LOW), 150),
    ]


TABLE = {
    'fidget_glass': fidget_glass(),
    'fidget_reel': fidget_reel(),
    'idle': idle(),
    'walk': walk(),
    'primary': shot(),
    'secondary': reel(),
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
    'powered_primary': shot(True),
    'powered_guard': guard(True),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ audit fix pass (25 Oct)
# no skating: a foot that moves more than 3 px is lifted in that drawing (anim.unskate)
from brine import P0 as _P0
FIDGETS = ['fidget_glass', 'fidget_reel']
EXTRA = {c: dict(n=(7, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = _P0()
_SH = {}
for _c, _a in {'primary': [2, 4, 9], 'secondary': [1, 3], 'special': [1, 3], 'powered_primary': [1, 4], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # v2: arc in-betweens
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    _k = anim.unskate(TABLE[_c], _P0)
    _hi = (anim.CLIPS[_c]['n'][1]) + 4
    if len(_k) <= _hi:
        TABLE[_c] = _k
# powered variants of hit, dodge, jump, stairs and secondary (anim.add_powered)
POWERED = dict(press=1.0)                 # Pressure Brace: the glass stays lit

# Harpoon-out variants (AUDIT.md, Brine 1): the same drawings with the harpoon out of the muzzle,
# played while the tether entity exists (runtime rule: harpoon_out from primary's release until
# secondary's drawing 6).  Registered as extra clips for this character so export.py and checks.py
# pick them up (anim.EXTRA_CLIPS is read at export time; lead: please adopt in anim.py).
EMPTY = ['idle', 'walk', 'guard', 'hit', 'powered_idle', 'powered_walk', 'powered_guard']
for _c in EMPTY:
    TABLE[_c + '_empty'] = [(dict(P, loaded=False), ms) for P, ms in TABLE[_c]]
    anim.EXTRA_CLIPS.setdefault('brine', {})[_c + '_empty'] = dict(anim.CLIPS[_c])
for _c in ('jump', 'dodge', 'stair_up', 'stair_down', 'special', 'defeat', 'powered_exit'):
    TABLE[_c + '_empty'] = [(dict(P, loaded=False), ms) for P, ms in TABLE[_c]]
    anim.EXTRA_CLIPS['brine'][_c + '_empty'] = dict(anim.CLIPS[_c])
# powered versions of the generated clips (add_powered runs later, so they are built here)
for _c in ('hit', 'jump', 'dodge', 'stair_up', 'stair_down'):
    TABLE['powered_%s_empty' % _c] = [(dict(P, loaded=False, press=1.0), ms) for P, ms in TABLE[_c]]
    anim.EXTRA_CLIPS['brine']['powered_%s_empty' % _c] = dict(anim.CLIPS.get('powered_' + _c) or anim.CLIPS[_c])

RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 7, 'secondary': 4, 'special': 4, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](5)]}                                 # the squeeze, held
ANCHOR_TAG = {'muzzle': 'harpoon_gun'}
TURN_CLIPS = ('idle', 'walk', 'powered_idle', 'powered_walk', 'idle_empty', 'walk_empty', 'powered_idle_empty', 'powered_walk_empty',
              'primary', 'powered_primary')

# v2 weapon aim within the facing (CONTRACT V2.8): the shouldered harpoon gun turns about its stock
# (level in S and N, pitched in E and W, anim.aim_level); the drawings either side turn half way.
AIM_CLIPS = ('primary', 'powered_primary')
AIM_PIVOT = (2.0, 40.0, 6.0)


def _turn(v, th, ps, about):
    x, y, z = np.subtract(v, about) if about is not None else np.array(v, float)
    x, y = x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th)
    x, z = x * math.cos(ps) - z * math.sin(ps), x * math.sin(ps) + z * math.cos(ps)
    out = np.array([x, y, z]) + (np.array(about) if about is not None else 0.0)
    return tuple(round(float(c), 3) for c in out)


def aim_table(clip, fc, deg):
    # from behind (N) the gun is raised (anim.aim_body), so it shows over his shoulder at the shot
    fwd, up, lat = anim.aim_body(fc, deg) if fc == 'N' else anim.aim_level(fc, deg)
    th0, ps0 = math.atan2(up, math.hypot(fwd, lat)), math.atan2(lat, fwd)
    keys = TABLE[clip]
    sh = [tuple(P.get('aim') or ()) == tuple(SHOULDER['aim']) for P, _ in keys]
    ws = [1.0 if sh[i] else (0.5 if ((i > 0 and sh[i - 1]) or (i + 1 < len(keys) and sh[i + 1])) else 0.0) for i in range(len(keys))]
    out = []
    for (P, ms), w in zip(keys, ws):
        if w:
            P = dict(P)
            P['grip'] = _turn(P.get('grip') or GRIP0, th0 * w, ps0 * w, AIM_PIVOT)
            P['aim'] = _turn(P.get('aim') or AIM0, th0 * w, ps0 * w, None)
            if fc == 'N':          # from behind the gun is held out past the shoulder on the aim's side, clear of the helmet
                g = P['grip']
                P['grip'] = (g[0], g[1] + 2.0 * w, g[2] + (7.0 if deg >= 0 else -17.0) * w)
        out.append((P, ms))
    return out
RELEASE_ANCHOR = {'primary': 'muzzle', 'secondary': 'muzzle', 'special': 'hand_R', 'powered_primary': 'muzzle'}
RELEASE['special_empty'] = RELEASE['special']
RELEASE_ANCHOR['special_empty'] = RELEASE_ANCHOR['special']

EQUIP = {
    'harpoon_gun': dict(always=True, may_hide={'N', 'NE', 'NW'}),
    'hose': dict(always=True, may_hide={'SW', 'NE'}),   # turned away (SW) or behind the raised gun (NE): its rear run is covered
    'helmet': dict(always=True),
    'pack': dict(always=True, may_hide={'S', 'SE', 'SW'}),
    'regulator': dict(always=True, may_hide={'W', 'SW', 'NW'}),
}


# v2 (the strike is never hidden): from behind, the reel's pull is made with the gun held out past
# his right side, where the helmet and pack do not cover it.
_BACK = {}


def facing_table(clip, fc):
    if fc not in ('N', 'NE', 'NW') or clip not in ('secondary', 'powered_secondary'):
        return TABLE[clip]
    if clip not in _BACK:
        r = RELEASE[clip]
        out = []
        for i, (P, ms) in enumerate(TABLE[clip]):
            if r - 2 <= i <= r + 1 and P.get('grip') is not None:
                g = P['grip']
                P = dict(P, grip=(g[0], g[1] + 3.0, g[2] + 8.0), aim=(0.7, 0.55, 0.45))
            out.append((P, ms))
        _BACK[clip] = out
    return _BACK[clip]

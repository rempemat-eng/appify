"""Morel's animation table (all 17 contract clips; anim_bramble.py is the template).  The
generic clips at the top (idle, walk, stairs, hit, defeat, jump, dodge) take the character's
rest hands and a base dict of gear state, so velvet, tam and mirra reuse them.

Logic (Codex identity table and review):
  - primary: the RIGHT hand throws.  The flask is held by its neck through preparation, leaves
    the hand at the release drawing (the hand is open and empty from then on), and the right
    hand draws the next flask from the flask case on the right hip before settling.  The LEFT
    hand stays in one place through the throw.
  - secondary (catalyst): the LEFT hand lifts the catalyst on its strap from the left hip,
    points the bulb, flares it at the release and clips it back.  The flask hand stays.
  - special: the LEFT hand takes the one mask from the chest to the face (worn from the release
    on, and through every powered clip); powered_exit moves the same mask back to the chest.
"""
import anim
from morel import REST_R, REST_L

A_STRIDE = 9.0
WALK_SPEED = round(anim.walk_speed(A_STRIDE), 1)        # (Morel's v2 speed is set below; velvet, tam, mirra set their own)
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


# ================================================================= generic clips (designer 1)
def g_idle(RR, RL, base=None, sway=None, ms=(260, 180, 200, 260, 220, 180, 120, 180)):
    base = base or {}
    br = [0, 0, 1, 1, 1, 1, 0, 0]
    lag = [0.0, 0.3, 0.6, 0.8, 0.6, 0.3, 0.0, -0.2]
    keys = []
    for i in range(8):
        k = K(base, breath=br[i], lag=lag[i], blink=(i == 6),
              handR=add(RR, (0, 0.5 * br[i], 0)), handL=add(RL, (0, 0.5 * br[i], 0)))
        if sway:
            k.update(sway(i))
        keys.append((k, ms[i]))
    return keys


def g_walk(RR, RL, A, base=None, armR=2.5, armL=4.0, extra=None, lean=1.0):
    base = base or {}
    keys = []
    for i, g in enumerate(anim.gait(anim.WALK_N, A, 3.5, bob=1.0)):
        s = g['swing']
        k = K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=lean, lag=1.5 + 0.6 * abs(s),
              handR=add(RR, (-armR * s, 0.5 + 0.6 * abs(s), 0)), handL=add(RL, (armL * s, 0.6 * abs(s), 0)))
        if extra:
            k.update(extra(i, s))
        keys.append((k, int(anim.WALK_LOOP * 1000 / anim.WALK_N)))
    return keys


def g_stairs(RR, RL, up=True, base=None, extra=None):
    base = base or {}
    keys = []
    for i, g in enumerate(anim.gait(8, 7.0, 7.0 if up else 2.5, bob=1.0)):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        k = K(base, footR=fr, footL=fl, bob=g['bob'], lean=2.5 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
              handR=add(RR, (-2.0 * s, 0.5, 0)), handL=add(RL, (3.0 * s, 0.5, 0)))
        if extra:
            k.update(extra(i, s))
        keys.append((k, 90))
    return keys


def g_hit(RR, RL, base=None):
    base = base or {}
    o = (3.0, 4.0, 1.0)
    return [
        (K(base, lean=-3.0, crouch=1.0, face='shut', brow=2, handR=add(RR, (8, 5, 1)), handL=add(RL, (3, 6, -1)), lag=-1.0), 35),
        (K(base, lean=-4.0, crouch=2.0, face='shut', brow=2, handR=add(RR, (7, 6, 1.5)), handL=add(RL, (2, 7, -1.5)), lag=-1.5), 65),
        (K(base, lean=-2.5, crouch=3.0, brow=2, handR=add(RR, (6, 4, 1)), handL=add(RL, (4, 4, -1)), lag=-0.5), 90),
        (K(base, lean=-1.0, crouch=2.0, brow=2, lag=0.5, handR=add(RR, o), handL=add(RL, (2, 2, 0))), 120),
        (K(base, lean=0.5, crouch=1.0, brow=1, lag=1.0), 130),
        (K(base, lean=0.3, crouch=0.5, lag=0.6), 150),
        (K(base, lag=0.2), 160),
        (K(base), 180),
    ]


def g_defeat(RR, RL, base=None, last=None):
    """Down on the left knee, hands to the thighs, head bowed (hands in standing coordinates)."""
    base = base or {}
    k1 = dict(footR=(7.0, 0.0), footL=(-6.0, 2.0))
    k2 = dict(footR=(7.5, 0.0), footL=(-8.0, 2.5))
    keys = [
        (K(base, lean=-3.0, crouch=1.0, face='shut', brow=2, handL=add(RL, (-4, 4, -1))), 80),
        (K(base, lean=2.0, crouch=5.0, face='shut', brow=2, handR=(9.0, 25.0, 13.0), handL=(4.0, 26.0, -13.0)), 100),
        (K(base, k1, lean=3.0, crouch=9.0, brow=2, handR=(11.0, 26.0, 12.0), handL=(7.0, 28.0, -12.0)), 100),
        (K(base, k2, lean=4.0, crouch=12.0, brow=2, handR=(12.0, 28.0, 11.0), handL=(8.0, 30.0, -10.0)), 120),
        (K(base, k2, lean=6.0, crouch=13.0, brow=2, face='shut', handR=(13.0, 27.0, 10.5), handL=(8.0, 29.0, -10.0)), 150),
        (K(base, k2, lean=7.0, crouch=13.0, face='shut', handR=(12.0, 27.0, 10.5), handL=(8.0, 29.0, -10.0)), 180),
        (K(base, k2, lean=8.0, crouch=13.5, face='shut', handR=(11.0, 27.0, 10.5), handL=(8.0, 28.5, -10.0), lag=0.5), 240),
        (K(base, k2, lean=8.0, crouch=13.5, face='shut', handR=(11.0, 27.0, 10.5), handL=(8.0, 28.5, -10.0), lag=0.8), 300),
    ]
    if last:
        for i in range(4, 8):
            keys[i][0].update(last)
    return keys


def g_jump(RR, RL, base=None):
    base = base or {}
    return [
        (K(base, crouch=4.0, lean=2.0, handR=add(RR, (2, -2, 1)), handL=add(RL, (-4, -2, -1)), lag=0.5), 80),
        (K(base, crouch=1.0, lean=1.0, footR=(2.5, 1.0), footL=(-2.5, 1.5), handR=add(RR, (6, 10, 1)), handL=add(RL, (3, 12, -1))), 55),
        (K(base, footR=(3.0, 6.0), footL=(-2.0, 8.0), handR=add(RR, (7, 14, 2)), handL=add(RL, (4, 16, -2)), lag=-1.5), 80),
        (K(base, footR=(4.0, 8.0), footL=(-1.0, 9.0), handR=add(RR, (7, 12, 2.5)), handL=add(RL, (4, 14, -2.5)), lag=-0.5), 110),
        (K(base, footR=(3.0, 3.0), footL=(-3.0, 4.0), handR=add(RR, (6, 14, 2)), handL=add(RL, (2, 16, -2)), lag=1.5), 110),
        (K(base, crouch=5.0, lean=2.5, footR=(3.0, 0.0), footL=(-3.0, 0.0), handR=add(RR, (8, 0, 1)), handL=add(RL, (5, 0, -1)), lag=1.5), 80),
        (K(base, crouch=3.0, lean=1.5, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 70),
        (K(base), 115),                                   # recover = idle drawing 0 (no pop on the cut)
    ]


def g_dodge(RR, RL, base=None):
    base = base or {}
    return [
        (K(base, crouch=3.0, lean=3.0, footR=(3.0, 0.0), footL=(-4.0, 0.0)), 55),
        (K(base, crouch=5.0, lean=6.0, footR=(6.0, 2.0), footL=(-10.0, 1.5), handR=add(RR, (1, -2, 1)), handL=add(RL, (-9, 2, -1)), lag=2.0), 45),
        (K(base, crouch=7.0, lean=8.0, footR=(9.0, 1.0), footL=(-10.0, 0.0), handR=add(RR, (-3, 0, 2)), handL=add(RL, (-11, 4, -1)), lag=3.0), 40),
        (K(base, crouch=7.5, lean=8.0, footR=(9.0, 0.0), footL=(-9.0, 0.5), handR=add(RR, (-2, -1, 2)), handL=add(RL, (-10, 3, -1)), lag=3.0), 45),
        (K(base, crouch=6.0, lean=6.0, footR=(7.0, 0.0), footL=(-7.0, 1.5), handR=add(RR, (2, -2, 1)), handL=add(RL, (-6, 0, -1)), lag=2.0), 60),
        (K(base, crouch=4.0, lean=4.0, footR=(5.0, 0.0), footL=(-4.0, 0.0), lag=1.5), 70),
        (K(base, crouch=2.0, lean=2.0, footR=(4.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 80),
        (K(base), 100),                                   # = idle drawing 0
    ]


def home_feet(table, P0):
    """Guards stay 8 drawings: one foot comes home in drawing 5 and the other in 6, so the
    shared anim.unskate lifts each in turn without appending a drawing."""
    d0 = P0()
    for c in ('guard', 'powered_guard'):
        k = table[c]
        last = k[7][0]
        fR, fL = last.get('footR', d0['footR']), last.get('footL', d0['footL'])
        k[5] = (dict(k[5][0], footL=fL), k[5][1])
        k[6] = (dict(k[6][0], footR=fR, footL=fL), k[6][1])


def ground_lift(keys, P0, K=0.35):
    """S and N show depth as height: a planted foot behind the body (S) or in front of it (N)
    sits up to 1 px higher on screen, so a drawing with only that foot down would float off the
    pivot row in that facing.  Keep the lifted foot low enough there that its sole still meets
    the ground row (the lift stays visible in E and W)."""
    d0 = P0()
    out = []
    for P, ms in keys:
        P = dict(P)
        fr, fl = tuple(P.get('footR', d0['footR'])), tuple(P.get('footL', d0['footL']))
        for a, b, ka in ((fr, fl, 'footR'), (fl, fr, 'footL')):
            if a[1] > 0.5 and b[1] < 0.5:            # a lifted, b planted
                pf, lf, L = b[0], a[0], a[1]
                if pf < -1.2:
                    L = min(L, max(0.5, K * lf + 0.4))
                if pf > 1.2:
                    L = min(L, max(0.5, -K * lf + 0.4))
                P[ka] = (lf, L)
        out.append((P, ms))
    return out


def spread_feet(keys, P0, step=3.0):
    """No skating and no floating: a planted foot never moves more than step px between two
    drawings.  A larger stance change is spread over the neighbouring drawings (the foot
    shuffles in steps of at most 3 px, as the audit allows) instead of being lifted, so one sole
    is always on the pivot row in every facing (a lifted foot in S/N leaves only a planted
    foot that projects above the row).  The first and last drawings keep their feet."""
    d0 = P0()
    n = len(keys)
    out = [dict(P) for P, _ in keys]
    for k in ('footR', 'footL'):
        tgt = [tuple(P.get(k, d0[k])) for P in out]
        lifted = [i for i, t in enumerate(tgt) if t[1] > 0.5]
        s0 = (lifted[-1] + 1) if lifted else 0         # only the planted run after the last lifted step
        if s0 >= n - 1:
            continue
        p = [t[0] for t in tgt]
        for _ in range(4):
            for i in range(s0 + 1, n):                 # forward: lag behind a jump
                p[i] = min(max(p[i], p[i - 1] - step), p[i - 1] + step) if i < n - 1 else tgt[i][0]
            for i in range(n - 2, s0, -1):             # backward: lead into the last drawing
                p[i] = min(max(p[i], p[i + 1] - step), p[i + 1] + step)
        for i in range(s0 + 1, n - 1):
            if abs(p[i] - tgt[i][0]) > 1e-6:
                out[i][k] = (round(p[i], 2), 0.0)
    return [(P, ms) for P, (_, ms) in zip(out, keys)]


def powered_from(table, release, ranchor, flags, rest=None, hands=None):
    """Powered variants of hit, dodge, jump, stairs and secondary, written here rather than by
    anim.add_powered so that a non-looping one ends on the POWERED rest pose (powered_idle 0):
    its last three drawings ease from the base clip's ending into rest.  flags: a function
    pose -> pose that puts on the powered gear."""
    for base in ('hit', 'dodge', 'jump', 'stair_up', 'stair_down', 'secondary'):
        keys = [(flags(dict(P)), ms) for P, ms in table[base]]
        if rest is not None and base not in ('stair_up', 'stair_down'):
            n = len(keys)
            for j, t in zip(range(n - 3, n), (1 / 3, 2 / 3, 1.0)):
                P, ms = keys[j]
                P = dict(P)
                if hands:                              # spell out rest hands so they ease too
                    P['handR'] = P.get('handR') or hands[0]
                    P['handL'] = P.get('handL') or hands[1]
                keys[j] = (flags(anim.lerp(P, dict(P, **rest), t)), ms)
        table['powered_' + base] = keys
        if base in release:
            release['powered_' + base] = release[base]
        if base in ranchor:
            ranchor['powered_' + base] = ranchor[base]


def powered_entry(table, flags, rest, hands, P0,
                  clips=('powered_primary', 'powered_guard', 'powered_hit', 'powered_secondary', 'powered_dodge', 'powered_jump')):
    """Powered actions start where powered_idle is: drawing 0 is the powered rest pose and the
    next two ease out of it into the action (so entering from powered_idle never pops), then
    feet are spread so none skates.  For hit, dodge and jump, whose first drawing is already the
    reaction, the first drawing only goes most of the way."""
    for c in clips:
        keys = table[c]
        sched = (0.6, 0.3, 0.1) if c in ('powered_hit', 'powered_dodge', 'powered_jump') else (1.0, 0.5, 0.2)
        for j, t in enumerate(sched):
            P, ms = keys[j]
            P = dict(P)
            P['handR'] = P.get('handR') or hands[0]
            P['handL'] = P.get('handL') or hands[1]
            keys[j] = (flags(anim.lerp(P, dict(P, **rest), t)), ms)
        table[c] = spread_feet(keys, P0)


# ================================================================= Morel (contract v2)
import math  # noqa: E402
import numpy as np  # noqa: E402
import morel as _m  # noqa: E402

M = dict(mask='face')
ST = dict(footR=(-4.0, 0.0), footL=(5.0, 0.0))            # throwing stance: left foot forward
LFIX = (7.0, 33.0, -11.0)                                   # the left hand's fixed place in a throw
# v2 (Matt 25 Oct): 15 % faster with the same stride, so a quicker cadence (12 drawings a stride)
WALK_LOOP2 = anim.WALK_LOOP / 1.15
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2) * __import__('morel').SCALE, 1)   # drawn at morel.SCALE


def _sway(i, n=12):
    return 0.12 * math.sin(2 * math.pi * i / n)


def idle(base=None):
    """v2 breathing idle, 12 drawings in 1.6 s: the chest rises, the hands ride with it, the
    hanging flask turns a little on its neck, one blink."""
    base = base or {}
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    keys = []
    for i in range(12):
        keys.append((K(base, breath=br[i], blink=(i == 10), fdir=(_sway(i), -1.0, 0.0),
                       handR=add(REST_R, (0, 0.5 * br[i], 0)), handL=add(REST_L, (0, 0.5 * br[i], 0))), ms[i]))
    return keys


def walk(base=None):
    """v2 walk: 12 drawings a stride; the flask swings against the step a beat behind the hand."""
    base = base or {}
    n = anim.WALK_N2
    keys = []
    for i, g in enumerate(anim.gait(n, A_STRIDE, 3.5, bob=1.0)):
        s = g['swing']
        s_lag = anim.gait(n, A_STRIDE, 3.5)[(i - 1) % n]['swing']
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0,
                       handR=add(REST_R, (-2.5 * s, 0.5 + 0.6 * abs(s), 0)), handL=add(REST_L, (4.0 * s, 0.6 * abs(s), 0)),
                       fdir=(0.45 * s_lag, -1.0, 0.0)), WALK_LOOP2 * 1000 / n))
    return keys


def throw(base=None, fast=False):
    base = base or {}
    L = dict(handL=LFIX, poleL=(-0.6, -1.0, -0.4))
    keys = [
        (K(base, ST, L, handR=(5.0, 30.0, 13.0), fdir=(0.2, -1.0, 0.0), lean=0.3), 60),                       # 0 ready
        (K(base, ST, L, handR=(-2.0, 39.0, 13.0), fdir=(-0.3, -1.0, 0.0), lean=-0.8, poleR=(-1.0, -0.6, 0.6)), 45),   # 1 wind
        (K(base, ST, L, handR=(-7.5, 48.0, 11.5), fdir=(-0.9, -0.5, 0.0), lean=-2.0, crouch=1.0, brow=1,
           poleR=(-0.5, -1.0, 0.6)), 80),                                                                       # 2 load (held)
        (K(base, ST, L, handR=(-6.5, 50.0, 11.0), fdir=(-1.0, -0.2, 0.0), lean=-2.2, crouch=1.0, brow=1,
           poleR=(-0.5, -1.0, 0.6)), 45),                                                                       # 3 load settle
        (K(base, ST, L, handR=(3.0, 52.0, 9.0), fdir=(-1.0, 0.4, 0.0), lean=0.5, brow=1, poleR=(-0.3, -1.0, 0.6)), 30),  # 4 swing
        (K(base, ST, L, flask='none', fly=True, handR=(13.0, 46.0, 7.0), openR=(1.0, 0.3, 0.0), lean=3.0, crouch=1.5, brow=1), 35),   # 5 release: the flask just leaves the hand
        (K(base, ST, L, flask='none', handR=(15.0, 34.0, 5.0), openR=(0.6, -1.0, 0.0), lean=3.5, crouch=2.0), 55),          # 6 follow-through
        (K(base, ST, L, flask='none', handR=(8.0, 28.0, 10.0), openR=(0.2, -1.0, 0.0), lean=1.5, crouch=1.0), 60),          # 7 recover
        (K(base, flask='none', handR=(-4.0, 30.0, 13.5), openR=(0.0, -1.0, 0.0), lean=0.5, handL=add(REST_L, (2, 3, 0)),
           footR=(-1.0, 0.0), footL=(2.0, 0.0)), 70),                                                            # 8 hand to the case
        (K(base, handR=(-4.0, 31.5, 13.5), fdir=(0.0, -1.0, 0.0), handL=add(REST_L, (1, 1, 0))), 70),          # 9 next flask out
        (K(base, handR=add(REST_R, (0.5, 1.5, 0)), fdir=(0.15, -1.0, 0.0)), 90),                                 # 10 settle
        (K(base), 120),
    ]
    if fast:
        keys = [keys[0], keys[2], keys[4], keys[5], keys[6], keys[7], keys[8], keys[9], keys[10], keys[11]]
    return keys


AIM_CLIPS = ('primary', 'powered_primary')


def fidget_swirl():
    """Lifts the flask to eye level, swirls it and watches the reagent settle, lowers it."""
    up = (9.5, 50.0, 6.0)
    sw = [(0.35, -1.0, 0.0), (0.0, -1.0, 0.35), (-0.35, -1.0, 0.0), (0.0, -1.0, -0.35), (0.25, -1.0, 0.0)]
    keys = [(K(), 150), (K(handR=(6.0, 34.0, 12.0), fdir=(0.2, -1.0, 0.0)), 110), (K(handR=(8.5, 43.0, 9.0), fdir=(0.1, -1.0, 0.0)), 90),
            (K(handR=up, fdir=(0.1, -1.0, 0.0), brow=1), 110)]
    for d in sw:
        keys.append((K(handR=add(up, (0.4 * d[0], 0, 0.4 * d[2])), fdir=d, brow=1), 70))
    keys += [(K(handR=up, fdir=(0.0, -1.0, 0.0), brow=1), 200),                   # watches it settle
             (K(handR=up, fdir=(0.0, -1.0, 0.0), blink=True), 120),
             (K(handR=(8.0, 42.0, 9.5), fdir=(-0.15, -1.0, 0.0)), 100),
             (K(handR=(6.0, 33.0, 12.0), fdir=(-0.1, -1.0, 0.0)), 100),
             (K(fdir=(0.12, -1.0, 0.0)), 110),
             (K(), 170)]
    return keys


def fidget_mask():
    """Straightens the mask hanging on his chest with the left hand and tugs its strap."""
    on = (9.0, 38.5, -2.0)
    return [(K(), 150),
            (K(handL=(4.0, 33.0, -9.0), openL=(0.6, 1.0, 0.0), poleL=(-0.4, -1.0, -0.5)), 110),
            (K(handL=on, openL=(0.0, 1.0, 0.0), zL=36.5, poleL=(-0.4, -1.0, -0.6)), 120),                 # hand on the mask
            (K(handL=add(on, (0.0, 0.8, 0.6)), openL=(0.0, 1.0, 0.0), zL=36.5, poleL=(-0.4, -1.0, -0.6), brow=1), 110),
            (K(handL=add(on, (0.0, -0.4, -0.6)), openL=(0.0, 1.0, 0.0), zL=36.5, poleL=(-0.4, -1.0, -0.6)), 110),
            (K(handL=(6.0, 47.0, -6.5), openL=(0.0, 1.0, 0.0), poleL=(-0.4, -1.0, -0.6), breath=1), 120),  # tugs the strap
            (K(handL=(5.0, 45.0, -7.5), openL=(0.0, 1.0, 0.0), poleL=(-0.4, -1.0, -0.6), breath=1), 120),
            (K(handL=(3.0, 32.0, -11.0), breath=0), 120),
            (K(handL=add(REST_L, (0, 0.5, 0))), 120),
            (K(), 170)]


def fidget_catalyst():
    """Taps the catalyst's bulb at his left hip; it glows faintly and dims."""
    tap = (-1.5, 27.5, -11.5)
    return [(K(), 150),
            (K(handL=(0.5, 26.0, -13.0), openL=(0.2, -1.0, 0.0)), 110),
            (K(handL=add(tap, (0.0, 1.5, -0.5)), openL=(0.0, -1.0, 0.0), lean=0.3), 100),
            (K(handL=tap, openL=(0.0, -1.0, 0.0), lean=0.4, catglow=1, brow=1), 70),               # tap: the bulb lights
            (K(handL=add(tap, (0.0, 1.5, -0.5)), openL=(0.0, -1.0, 0.0), lean=0.4, catglow=1, brow=1), 140),
            (K(handL=add(tap, (0.0, 1.5, -0.5)), openL=(0.0, -1.0, 0.0), lean=0.3, catglow=1), 160),
            (K(handL=(0.5, 26.0, -13.0), lean=0.1), 120),                                        # it dims
            (K(), 170)]


def catalyst():
    hold = (-2.5, 21.5, -10.0)
    return [
        (K(handL=(-1.0, 25.0, -12.0), openL=(0.0, -1.0, 0.0)), 50),                                   # 0 reach
        (K(handL=hold, cat=(0.0, 1.0, 0.0)), 45),                                                      # 1 grip the chamber
        (K(handL=(4.0, 30.0, -10.0), cat=(0.5, 1.0, 0.0), lean=0.3), 45),                             # 2 lift on the strap
        (K(handL=(10.0, 38.0, -6.0), cat=(1.0, 0.4, 0.1), lean=0.8, brow=1, footL=(3.0, 0.0), footR=(-2.0, 0.0)), 70),   # 3 point
        (K(handL=(10.5, 38.5, -6.0), cat=(1.0, 0.45, 0.1), catglow=1, lean=0.8, brow=1, footL=(3.0, 0.0), footR=(-2.0, 0.0)), 60),  # 4 twist
        (K(handL=(11.0, 40.0, -6.0), cat=(1.0, 0.6, 0.1), catglow=2, lean=1.2, brow=1, footL=(3.0, 0.0), footR=(-2.0, 0.0)), 40),   # 5 flare (release)
        (K(handL=(10.5, 39.0, -6.0), cat=(1.0, 0.5, 0.1), catglow=1, lean=1.0, footL=(3.0, 0.0), footR=(-2.0, 0.0)), 70),          # 6 hold
        (K(handL=(4.0, 29.0, -10.0), cat=(0.4, 1.0, 0.0), lean=0.4), 70),                             # 7 lower
        (K(handL=hold, cat=(0.0, 1.0, 0.0)), 70),                                                      # 8 clipped back
        (K(handL=add(REST_L, (0, 1, 0))), 90),                                                         # 9 hand away
    ]


def special():
    return [
        (K(handL=(4.0, 33.0, -9.0), openL=(0.6, 1.0, 0.0), poleL=(-0.4, -1.0, -0.5)), 80),                         # 0 reach
        (K(handL=(9.0, 38.5, -2.0), openL=(0.0, 1.0, 0.0), zL=36.5, poleL=(-0.4, -1.0, -0.6)), 60),                 # 1 hand on the mask
        (K(mask='hand', handL=(9.5, 40.0, -1.5), zL=36.5, poleL=(-0.4, -1.0, -0.6)), 60),                           # 2 take it
        (K(mask='hand', handL=(10.0, 49.0, -1.0), zL=47.0, poleL=(-0.4, -1.0, -0.6), lean=-0.5), 70),             # 3 lift
        (K(mask='hand', handL=(9.0, 56.0, -1.0), zL=47.0, poleL=(-0.4, -1.0, -0.6), lean=-0.8, brow=1), 70),      # 4 to the face
        (K(mask='face', handL=(2.5, 58.0, -9.5), openL=(0.0, 1.0, 0.0), poleL=(-0.3, -1.0, -0.6), lean=-0.3, brow=1), 50),  # 5 on (release)
        (K(mask='face', handL=(1.5, 55.0, -11.0), openL=(0.0, 1.0, 0.0), poleL=(-0.3, -1.0, -0.6)), 90),         # 6 strap set
        (K(mask='face', handL=(1.0, 38.0, -13.5)), 100),                                                           # 7 lower
        (K(mask='face'), 120),                                                                                      # 8 settle
    ]


def powered_exit():
    return [
        (K(M), 100),
        (K(M, handL=(1.5, 50.0, -11.0), openL=(0.0, 1.0, 0.0), poleL=(-0.3, -1.0, -0.6)), 100),
        (K(M, handL=(8.5, 56.0, -2.0), openL=(0.0, 1.0, 0.0), zL=47.0, poleL=(-0.4, -1.0, -0.6)), 90),           # hand on the mask
        (K(mask='hand', handL=(10.0, 54.0, -1.0), zL=47.0, poleL=(-0.4, -1.0, -0.6), lean=-0.5), 90),            # off the face
        (K(mask='hand', handL=(10.0, 46.0, -1.0), zL=37.0, poleL=(-0.4, -1.0, -0.6)), 100),                      # lowered
        (K(mask='chest', handL=(9.0, 38.5, -2.0), openL=(0.0, 1.0, 0.0), zL=36.5, poleL=(-0.4, -1.0, -0.6)), 110),   # back on the chest
        (K(handL=(3.0, 30.0, -11.0)), 120),
        (K(), 150),
    ]


def guard(base=None):
    base = base or {}
    G = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
    up = (10.0, 47.0, -2.0)
    pl = (-0.2, -1.0, -0.8)
    return [
        (K(base, handL=(5.0, 34.0, -9.0), handR=add(REST_R, (-2, 1, 0)), poleL=pl), 55),
        (K(base, G, handL=(8.5, 41.0, -5.0), handR=(-2.5, 27.0, 13.5), poleL=pl, crouch=0.5), 55),
        (K(base, G, handL=(10.0, 45.0, -3.0), handR=(-5.0, 28.0, 13.5), poleL=pl, crouch=1.2, lean=-0.5, brow=1), 55),
        (K(base, G, handL=up, handR=(-5.0, 28.0, 13.5), poleL=pl, crouch=1.8, lean=-0.8, brow=1), 55),
        (K(base, G, handL=up, handR=(-5.0, 28.0, 13.5), poleL=pl, crouch=2.0, lean=-1.0, brow=1), 120),      # hold
        (K(base, G, handL=(7.0, 38.0, -8.0), handR=(-2.0, 26.0, 14.0), poleL=pl, crouch=1.0), 120),
        (K(base, handL=add(REST_L, (2, 4, 0)), handR=add(REST_R, (-1, 1, 0))), 120),
        (K(base), 120),
    ]


def flask_follow(keys, loop=False):
    """v2 secondary motion: the hanging flask trails the body (anim.follow's spring), a beat late."""
    out = []
    for P, ms in anim.follow(keys, loop=loop):
        P = dict(P)
        h = P.pop('hair', 0.0)
        fd = P.get('fdir')
        if P.get('flask', 'hand') == 'hand' and P.get('handR') is not None and (fd is None or fd[1] < -0.8):
            fd = fd or (0.0, -1.0, 0.0)
            P['fdir'] = (round(fd[0] - 0.18 * h, 3), fd[1], fd[2])
        out.append((P, ms))
    return out


_D = _m.P0()
THROW_SH = (0.0, 44.0, 12.0)                         # the throwing shoulder (body space)


def _v(a):
    return np.array(a, float)


def aimed(keys, d):
    """The throw turned to the aim d (CONTRACT V2.8, 26 Oct review): the arm cocks back along the
    aim (behind and above the shoulder, low for a downward aim), swings over the shoulder, releases
    with the arm out along the aim and follows through down past it.  The cocked hand stays outside
    the torso so the flask is in sight in S, E and W (only N's back may hide it)."""
    d = _v(d) / np.linalg.norm(d)
    sh = _v(THROW_SH)

    def out(p, lat_min=11.0):
        p = _v(p)
        p[2] = max(p[2], lat_min)
        return tuple(round(float(x), 3) for x in p)
    cocked = out(sh - d * 7.5 + (0.0, 5.0, 0.0))
    trail = tuple(round(float(x), 3) for x in (-d * 0.6 + (0.0, -0.8, 0.0)) / np.linalg.norm(-d * 0.6 + (0.0, -0.8, 0.0)))
    keys = [(dict(P), ms) for P, ms in keys]
    keys[1] = (dict(keys[1][0], handR=tuple((_v(keys[1][0]['handR']) + _v(cocked)) / 2), fdir=trail), keys[1][1])
    keys[2] = (dict(keys[2][0], handR=cocked, fdir=trail), keys[2][1])
    keys[3] = (dict(keys[3][0], handR=out(_v(cocked) + (0.0, 1.2, 0.0)), fdir=trail), keys[3][1])
    keys[4] = (dict(keys[4][0], handR=out(sh + d * 2.0 + (0.0, 7.0, 0.0)), fdir=tuple(-d)), keys[4][1])
    keys[5] = (dict(keys[5][0], handR=out(sh + d * 10.0 + (3.5, -1.5, 0.0), 6.0), openR=tuple(d)), keys[5][1])   # out in front, clear of his face
    fo = d * 0.4 + (0.0, -1.0, 0.0)
    keys[6] = (dict(keys[6][0], handR=out(sh + d * 8.0 + (0.0, -8.0, 0.0), 6.0), openR=tuple(fo / np.linalg.norm(fo))), keys[6][1])
    keys[7] = (dict(keys[7][0], handR=tuple((_v(keys[7][0]['handR']) + _v(keys[6][0]['handR'])) / 2)), keys[7][1])
    return keys


def throw_table(base=None, fast=False, d=None):
    """The throw for one aim (d None: the unaimed authored throw, used by the turn in-betweens):
    aimed keys, then in-betweens (anticipation, the smear, follow-through), feet spread, the flask's
    follow-through."""
    keys = throw(base, fast=False)
    if d is not None:
        keys = aimed(keys, d)
    if fast:
        keys = [keys[i] for i in (0, 2, 4, 5, 6, 7, 8, 9, 10, 11)]
    keys, sh = anim.densify(keys, [1, 3, 5] if fast else [1, 4, 6, 8], base=_D)
    s = sh(3 if fast else 5) - 1                 # the smear just before the release: the flask still in the hand
    if not keys[s][0].get('flask') == 'hand':
        fd = tuple(-np.array(d)) if d is not None else (-0.5, -0.9, 0.0)
        keys[s] = (dict(keys[s][0], flask='hand', fdir=fd, openR=None), keys[s][1])
    keys = spread_feet(keys, _m.P0, step=2.4)
    return flask_follow(keys), sh


_throw, _tsh = throw_table()
_pthrow, _ptsh = throw_table(M, fast=True)
_cat, _csh = anim.densify(catalyst(), [2, 5, 7], base=_D)
_spec, _ssh = anim.densify(special(), [0, 3, 6], base=_D)

TABLE = {
    'idle': idle(),
    'walk': walk(),
    'primary': _throw,
    'secondary': _cat,
    'special': _spec,
    'guard': guard(),
    'hit': anim.densify(g_hit(REST_R, REST_L), [0, 2], base=_D)[0],
    'defeat': g_defeat(REST_R, REST_L, last=dict(fdir=(0.3, -1.0, 0.0))),
    'jump': g_jump(REST_R, REST_L),
    'stair_up': g_stairs(REST_R, REST_L, True),
    'stair_down': g_stairs(REST_R, REST_L, False),
    'dodge': anim.densify(g_dodge(REST_R, REST_L), [1, 4], base=_D)[0],
    'powered_idle': idle(M),
    'powered_walk': walk(M),
    'powered_primary': _pthrow,
    'powered_guard': guard(M),
    'powered_exit': powered_exit(),
    'fidget_swirl': fidget_swirl(),
    'fidget_mask': fidget_mask(),
    'fidget_catalyst': fidget_catalyst(),
}
FIDGETS = ['fidget_swirl', 'fidget_mask', 'fidget_catalyst']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
home_feet(TABLE, _m.P0)
for _c in ('secondary', 'special', 'guard', 'hit', 'powered_guard', 'powered_exit'):
    TABLE[_c] = spread_feet(TABLE[_c], _m.P0, step=2.4)   # no skating: feet shuffle under 2.5 px a drawing
for _c in ('secondary', 'special', 'hit', 'dodge', 'defeat', 'powered_exit') + tuple(FIDGETS):
    TABLE[_c] = flask_follow(TABLE[_c])

# Powered variants (anim.add_powered): the mask stays on the face.
POWERED = dict(mask='face')

RELEASE = {'primary': _tsh(5), 'secondary': _csh(5), 'special': _ssh(5), 'powered_primary': _ptsh(3)}
HOLDS = {'primary': [3], 'powered_primary': [1]}           # v2 polish: the load is held
RELEASE_ANCHOR = {'primary': 'flask', 'secondary': 'catalyst', 'special': 'hand_L', 'powered_primary': 'flask'}


def aim_table(clip, fc, deg):
    """The throw drawn for one aim within one body facing (same timing and release drawing)."""
    return throw_table(M if clip == 'powered_primary' else None, clip == 'powered_primary', anim.aim_body(fc, deg))[0]


EQUIP = {
    'mask': dict(always=True, may_hide={'N', 'NE', 'NW'}),
    'catalyst': dict(always=True, may_hide={'E', 'S', 'N', 'SE', 'NE', 'NW', 'SW'}),
    'case': dict(always=True, may_hide={'W', 'S', 'SW', 'NW', 'SE'}),
    # the flask hand is the far hand in W (behind the body there), so W is exempt at rest; in
    # the throw the flask must show through the wind-up in every facing
    'flask': dict(always=True, may_hide={'W', 'NW', 'SW', 'NE'}, clips={'primary': [3, 4, 5], 'powered_primary': [1, 2, 3],
                                                       'special': [], 'secondary': [], 'guard': [], 'powered_guard': [],
                                                       'hit': [], 'defeat': [], 'jump': [], 'dodge': [], 'powered_exit': [],
                                                       'fidget_mask': [], 'fidget_catalyst': []}),
}


# v2 (26 Oct review: the strike is never hidden): from behind (N and its in-betweens) the catalyst
# is raised out beside his left side at the release instead of in front of his chest.
_BACK = {}


def facing_table(clip, fc):
    if fc not in ('N', 'NE', 'NW') or clip not in ('secondary', 'powered_secondary'):
        return TABLE[clip]
    if clip not in _BACK:
        r = RELEASE[clip]
        out = []
        for i, (P, ms) in enumerate(TABLE[clip]):
            if r - 1 <= i <= r + 1 and P.get('handL') is not None:
                x, y, z = P['handL']
                P = dict(P, handL=(x - 3.0, y + 2.0, -13.5))
            out.append((P, ms))
        _BACK[clip] = out
    return _BACK[clip]

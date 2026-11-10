"""Nix's animation table (copied from the anim_bramble.py pattern).  A pose names only what
differs from nix.P0; the rig renders it in S, N, E and W.  Timings are refitted to Codex's.

Body space: (fwd, up, lat), lat + = his RIGHT.  The laser arm is the LEFT arm (hand_L, lat < 0):
the beam leaves the lens at the end of the left forearm ('muzzle').  Afterimage (secondary)
leaves one stationary decoy at the activation origin: the decoy is the separate effect sprite
out/nix/fx/afterimage_<F>.png, never part of a body drawing.  Limit Release (special) opens the
same left forearm casing (casing = 1) and every powered clip keeps it open; powered_exit
closes it.

The generic clips (idle, walk, stairs, hit, defeat, jump, dodge) are shared with anim_rook and
anim_mote (designer 3)."""
import math
import numpy as np
import anim
from nix import REST_R, REST_L, SHW

A_STRIDE = 9.0
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    if a is None:
        return None
    return tuple(x + y for x, y in zip(a, b))


# ================================================================ generic clips (designer 3)
def idle(base, RR, RL, swayR=(0, 0.5, 0), swayL=(0, 0.5, 0)):
    keys = []
    br = [0, 0, 1, 1, 1, 1, 0, 0]
    lag = [0.0, 0.3, 0.6, 0.8, 0.6, 0.3, 0.0, -0.2]
    for i in range(8):
        k = br[i]
        keys.append((K(base, breath=k, lag=lag[i], blink=(i == 6),
                       handR=add(RR, tuple(v * k for v in swayR)), handL=add(RL, tuple(v * k for v in swayL))),
                     [260, 180, 200, 260, 220, 180, 120, 180][i]))
    return keys


def walk(base, RR, RL, A=A_STRIDE, swR=2.5, swL=3.5, lean=1.0, lift=3.5, armR=True, armL=True):
    keys = []
    for g in anim.gait(anim.WALK_N, A, lift, bob=1.0):
        s = g['swing']
        hr = add(RR, (-swR * s, 0.5, 0)) if armR else RR
        hl = add(RL, (swL * s, 0.8 * abs(s), 0)) if armL else RL
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=lean, lag=1.5 + 0.6 * abs(s),
                       handR=hr, handL=hl), int(anim.WALK_LOOP * 1000 / anim.WALK_N)))
    return keys


def stairs(base, RR, RL, up=True, armR=True, armL=True):
    keys = []
    for g in anim.gait(8, 7.0, 7.0 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (1.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (1.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(base, footR=fr, footL=fl, bob=g['bob'], lean=2.5 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
                       handR=add(RR, (-2.0 * s, 0.5, 0)) if armR else RR,
                       handL=add(RL, (3.5 * s, 0.5, 0)) if armL else RL), 90))
    return keys


def hit(base, w=14.0, hR=None, hL=None):
    hR = hR or [(12.0, 30.0, w), (11.0, 31.0, w + 0.5), (10.0, 28.0, w)]
    hL = hL or [(-5.0, 30.0, -w), (-6.0, 31.0, -w - 0.5), (-3.0, 28.0, -w)]
    return [
        (K(base, lean=-3.0, crouch=1.0, face='shut', brow=2, handR=hR[0], handL=hL[0], lag=-1.0), 35),
        (K(base, lean=-4.0, crouch=2.0, face='shut', brow=2, handR=hR[1], handL=hL[1], lag=-1.5), 65),
        (K(base, lean=-2.5, crouch=3.0, brow=2, handR=hR[2], handL=hL[2], lag=-0.5), 90),
        (K(base, lean=-1.0, crouch=2.0, brow=2, lag=0.5), 120),
        (K(base, lean=0.5, crouch=1.0, brow=1, lag=1.0), 130),
        (K(base, lean=0.3, crouch=0.5, lag=0.6), 150),
        (K(base, lag=0.2), 160),
        (K(base), 180),
    ]


def defeat(base, w=13.0, last=None, dy=0.0):
    k1 = dict(footR=(7.0, 0.0), footL=(-6.0, 2.0))
    k2 = dict(footR=(7.5, 0.0), footL=(-8.0, 2.5))
    end = K(base, k2, lean=8.0, crouch=13.5, face='shut', handR=(11.0, 27.0, w - 1), handL=(9.0, 28.5, -w + 3), lag=0.5)
    if last:
        end.update(last)
    keys = [
        (K(base, lean=-3.0, crouch=1.0, face='shut', brow=2, handL=(-4.0, 29.0, -w - 1)), 80),
        (K(base, lean=2.0, crouch=5.0, face='shut', brow=2, handR=(6.0, 26.0, w), handL=(3.0, 27.0, -w)), 100),
        (K(base, k1, lean=3.0, crouch=9.0, brow=2, handR=(8.0, 27.0, w - 1), handL=(6.0, 28.0, -w + 1)), 100),
        (K(base, k2, lean=4.0, crouch=12.0, brow=2, handR=(12.0, 28.0, w - 1), handL=(8.0, 30.0, -w + 2)), 120),
        (K(base, k2, lean=6.0, crouch=13.0, brow=2, face='shut', handR=(12.0, 27.0, w - 1), handL=(9.0, 29.0, -w + 3)), 150),
        (K(end, lean=7.0, crouch=13.0), 180),
        (K(end), 240),
        (K(end, lag=0.8), 300),
    ]
    for P, _ in keys:                    # dy raises the hands for a higher shoulder line
        for k in ('handR', 'handL'):
            if P.get(k):
                P[k] = (P[k][0], P[k][1] + dy, P[k][2])
    return keys


def jump(base, w=14.0, armR=True, armL=True, hR=None, hL=None):
    R = hR or [(4.0, 22.0, w), (9.0, 36.0, w), (10.0, 40.0, w + 1), (10.0, 38.0, w + 1.5), (9.0, 40.0, w + 1), (11.0, 24.0, w)]
    L = hL or [(-4.0, 22.0, -w), (4.0, 38.0, -w), (5.0, 42.0, -w - 1), (5.0, 40.0, -w - 1.5), (3.0, 42.0, -w - 1), (6.0, 24.0, -w)]

    def H(i):
        d = {}
        if armR:
            d['handR'] = R[i]
        if armL:
            d['handL'] = L[i]
        return d
    return [
        (K(base, H(0), crouch=4.0, lean=2.0, lag=0.5), 80),
        (K(base, H(1), crouch=1.0, lean=1.0, footR=(2.5, 1.0), footL=(-2.5, 1.5)), 55),
        (K(base, H(2), footR=(3.0, 6.0), footL=(-2.0, 8.0), lag=-1.5), 80),
        (K(base, H(3), footR=(4.0, 8.0), footL=(-1.0, 9.0), lag=-0.5), 110),
        (K(base, H(4), footR=(3.0, 3.0), footL=(-3.0, 4.0), lag=1.5), 110),
        (K(base, H(5), crouch=5.0, lean=2.5, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.5), 80),
        (K(base, crouch=3.0, lean=1.5, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 70),
        (K(base), 115),                                    # recover: idle drawing 0
    ]


def dodge(base, w=15.0, armR=True, armL=True, hR=None, hL=None):
    hR = hR or [(4.0, 22.0, w), (0.0, 24.0, w + 1), (1.0, 23.0, w + 1), (5.0, 22.0, w)]
    hL = hL or [(-8.0, 26.0, -w), (-10.0, 28.0, -w), (-9.0, 27.0, -w), (-5.0, 24.0, -w)]

    def H(r, l):
        d = {}
        if armR:
            d['handR'] = r
        if armL:
            d['handL'] = l
        return d
    return [
        (K(base, crouch=3.0, lean=3.0, footR=(3.0, 0.0), footL=(-4.0, 0.0)), 55),
        (K(base, H(hR[0], hL[0]), crouch=5.0, lean=6.0, footR=(6.0, 2.0), footL=(-10.0, 0.0), lag=2.0), 45),
        (K(base, H(hR[1], hL[1]), crouch=7.0, lean=8.0, footR=(9.0, 1.0), footL=(-10.0, 0.0), lag=3.0), 40),
        (K(base, H(hR[2], hL[2]), crouch=7.5, lean=8.0, footR=(9.0, 0.0), footL=(-9.0, 0.5), lag=3.0), 45),
        (K(base, H(hR[3], hL[3]), crouch=6.0, lean=6.0, footR=(7.0, 0.0), footL=(-7.0, 1.5), lag=2.0), 60),
        (K(base, crouch=4.0, lean=4.0, footR=(5.0, 0.0), footL=(-4.0, 0.0), lag=1.5), 70),
        (K(base, crouch=2.0, lean=2.0, footR=(4.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 80),
        (K(base), 100),                                    # recover: idle drawing 0
    ]


def guard_feet(keys, G, P0):
    """An 8-drawing guard whose stance G differs from the rest feet: each foot steps (lifted)
    in its own drawing, out in 0 and 1, home in 5 and 6; 7 is the idle pose."""
    d = P0()
    hr, hl = d['footR'], d['footL']
    gr, gl = G['footR'], G['footL']
    feet = [dict(footR=hr, footL=(gl[0], 2.5)), dict(footR=(gr[0], 2.0), footL=gl), G, G, G,
            dict(footR=(hr[0], 2.0), footL=gl), dict(footR=hr, footL=(hl[0], 2.5)), dict(footR=hr, footL=hl)]
    return [(dict(P, **feet[i]), ms) for i, (P, ms) in enumerate(keys)]


# ================================================================ Nix
ST = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))          # laser side (left) foot forward
AIM = (15.0, 41.0, -5.0)                                # left hand straight out at shoulder height
BRACE = (6.0, 33.0, 4.0)                                # right fist at the chest, bracing


def beam(c=0.0, fast=False):
    keys = [
        (K(casing=c, handL=(6.0, 32.0, -10.0), handR=(3.0, 30.0, 11.0), lean=0.4), 70),                  # weight shifts
        (K(casing=c, footL=(1.0, 2.5), handL=(10.0, 37.0, -8.0), handR=(4.0, 31.0, 9.0), lean=0.6, brow=1), 50),        # arm comes up, left foot steps
        (K(casing=c, footR=(-1.0, 1.5), footL=(4.0, 0.0), handL=(14.0, 40.5, -6.0), handR=BRACE, lean=0.3, brow=1), 40),   # level, right foot sets back
        (K(ST, casing=c, handL=AIM, handR=BRACE, lean=0.0, crouch=1.0, brow=1), 60),                       # aim
        (K(ST, casing=c, handL=AIM, handR=BRACE, lean=-0.3, crouch=1.0, brow=1), 50),                      # charge (hold)
        (K(ST, casing=c, handL=(13.0, 42.5, -5.0), handR=BRACE, lean=-1.2, crouch=1.0, brow=1, flare=True), 35),  # fire
        (K(ST, casing=c, handL=(12.5, 42.0, -5.5), handR=BRACE, lean=-1.0, crouch=1.0, brow=1), 55),      # recoil
        (K(ST, casing=c, handL=(13.5, 41.0, -5.5), handR=(5.0, 32.0, 6.0), lean=-0.5, crouch=0.5), 70),    # follow-through
        (K(casing=c, footR=(-0.5, 1.5), footL=(4.0, 0.0), handL=(9.0, 35.0, -8.5), handR=(3.0, 30.0, 10.0), lean=-0.2), 80),   # lower, right foot comes up
        (K(casing=c, footL=(1.0, 2.0), handL=(4.0, 30.0, -11.5)), 90),                                   # left foot steps back
        (K(casing=c), 120),                                                                                  # settle
    ]
    if fast:          # powered: the open casing fires from the hip-high snap, no long hold
        keys = [keys[1], keys[2], keys[3], keys[5], keys[6], keys[7], keys[8], keys[9], keys[10]]
    return keys


def afterimage():
    return [
        (K(handL=(3.0, 29.0, -12.0), handR=(2.0, 29.0, 12.0), crouch=1.0, lean=0.5), 70),                  # ready
        (K(handL=(7.0, 35.0, -6.0), handR=(5.0, 34.0, 5.0), crouch=3.0, lean=1.5, brow=1,
           footR=(-2.0, 0.0), footL=(2.0, 0.0)), 90),                                                       # coil: arms cross
        (K(handL=(9.0, 38.0, -3.0), handR=(8.0, 36.0, 3.0), crouch=3.5, lean=2.0, brow=1,
           footR=(-2.0, 0.0), footL=(2.0, 0.0)), 70),                                                       # load (hold)
        (K(handL=(-3.0, 31.0, -15.0), handR=(-3.0, 30.0, 15.0), crouch=0.0, lean=-2.0, hipx=-2.0,
           footR=(-1.0, 0.0), footL=(0.5, 0.0), face='shut'), 35),                                        # release: snaps away
        (K(handL=(-2.0, 30.0, -14.5), handR=(-2.0, 29.5, 14.5), crouch=1.0, lean=-1.5, hipx=-1.5,
           footR=(-1.0, 0.0), footL=(0.5, 0.0), lag=-1.0), 70),
        (K(handL=(0.0, 28.5, -13.5), handR=(0.0, 28.5, 13.0), crouch=1.0, lean=-0.5, hipx=-0.5,
           footR=(-0.5, 0.0), footL=(0.5, 0.0), lag=0.5), 90),
        (K(lean=0.2, lag=0.3), 110),
        (K(), 130),
    ]


def limit_release():
    up = (9.0, 45.0, -3.0)                                  # left forearm up before the face
    hold = (8.0, 40.0, 1.0)                                 # right hand grips the casing
    return [
        (K(handL=(5.0, 33.0, -10.0), handR=(3.0, 31.0, 10.0), crouch=1.0), 90),
        (K(handL=up, handR=(5.0, 34.0, 6.0), crouch=1.5, lean=0.5, brow=1, poleL=(-0.3, -1.0, -0.5)), 80),
        (K(handL=up, handR=hold, crouch=2.0, lean=0.8, brow=1, poleL=(-0.3, -1.0, -0.5)), 90),
        (K(handL=up, handR=hold, crouch=2.0, lean=0.8, brow=1, casing=0.35, poleL=(-0.3, -1.0, -0.5)), 120),
        (K(handL=(10.0, 47.0, -4.0), handR=(4.0, 33.0, 10.0), crouch=1.0, lean=-0.5, brow=1, casing=1.0,
           poleL=(-0.3, -1.0, -0.5)), 60),                                                                 # release: casing open
        (K(handL=(12.0, 40.0, -6.0), handR=(3.0, 31.0, 11.0), crouch=1.5, lean=-0.3, casing=1.0), 80),
        (K(handL=(7.0, 33.0, -10.0), casing=1.0, crouch=1.0), 100),
        (K(casing=1.0, lag=0.3), 110),
        (K(casing=1.0), 90),
    ]


def guard(c=0.0):
    G = dict(footR=(-2.0, 0.0), footL=(3.0, 0.0))
    up = (8.0, 44.0, -1.0)                                  # left forearm upright across the face
    P = (-0.4, -1.0, -0.5)
    return [
        (K(G, casing=c, handL=(5.0, 34.0, -9.0), crouch=0.5), 55),
        (K(G, casing=c, handL=(7.0, 39.0, -5.0), handR=(3.0, 31.0, 10.0), crouch=1.0, poleL=P), 55),
        (K(G, casing=c, handL=(8.0, 42.0, -2.0), handR=(4.0, 32.0, 8.0), crouch=1.5, lean=0.8, poleL=P, brow=1), 55),
        (K(G, casing=c, handL=up, handR=(5.0, 33.0, 6.0), crouch=2.0, lean=1.2, poleL=P, brow=1), 55),
        (K(G, casing=c, handL=up, handR=(5.0, 33.0, 6.0), crouch=2.5, lean=1.5, poleL=P, brow=1), 120),   # braced (hold)
        (K(G, casing=c, handL=(6.0, 37.0, -7.0), handR=(3.0, 31.0, 10.0), crouch=1.5, lean=0.5), 120),
        (K(casing=c, handL=(3.0, 30.0, -11.5), crouch=0.5), 120),
        (K(casing=c), 120),
    ]


def powered_exit():
    up = (9.0, 45.0, -3.0)
    hold = (8.0, 40.0, 1.0)
    PL = (-0.3, -1.0, -0.5)
    return [
        (K(casing=1.0), 110),
        (K(casing=1.0, handL=up, handR=(5.0, 34.0, 6.0), crouch=1.0, poleL=PL), 100),
        (K(casing=1.0, handL=up, handR=hold, crouch=1.5, poleL=PL), 100),
        (K(casing=0.6, handL=up, handR=hold, crouch=1.5, poleL=PL), 90),
        (K(casing=0.0, handL=up, handR=hold, crouch=1.5, poleL=PL, brow=1), 90),
        (K(casing=0.0, handL=(6.0, 36.0, -8.0), handR=(4.0, 32.0, 9.0), crouch=1.0), 100),
        (K(casing=0.0, handL=(3.0, 29.0, -12.0), crouch=0.5, lag=0.3), 120),
        (K(), 150),
    ]


# ================================================================ v2 (contract V2.3 to V2.11)
def idle2(base, RR=REST_R, RL=REST_L):
    """v2 idle, 12 drawings in 1.6 s: the breath, the heavy left arm settling a beat behind it, one
    blink."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    sag = [0.0, 0.0, 0.2, 0.4, 0.4, 0.2, 0.0, -0.2, -0.4, -0.4, -0.2, 0.0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    return [(K(base, breath=br[i], lag=lag[i], blink=(i == 10), handR=add(RR, (0, 0.5 * br[i], 0)), handL=add(RL, (0, sag[i], 0))), ms[i])
            for i in range(12)]


def walk2(base, RR=REST_R, RL=REST_L):
    """v2 walk, 12 drawings a stride: the heavy left arm swings less and a drawing late."""
    keys = []
    n = anim.WALK_N2
    gs = anim.gait(n, A_STRIDE, 3.5, bob=1.0)
    for i, g in enumerate(gs):
        s = g['swing']
        late = gs[(i - 1) % n]['swing']
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.5 + 0.6 * abs(s),
                       handR=add(RR, (-2.5 * s, 0.5, 0)), handL=add(RL, (2.5 * late, 0.6 * abs(late), 0))), WALK_LOOP2 * 1000 / n))
    return keys


def fidget_casing():
    """Taps the laser arm's casing with two fingers, listens, flexes the hand."""
    T = dict(handL=(7.0, 33.0, -6.0), handR=(8.0, 35.0, -2.0))
    return [(K(), 150), (K(handL=(6.0, 31.0, -9.0), handR=(5.0, 32.0, 6.0)), 110), (K(T, brow=1), 110),
            (K(T, handR=(8.5, 36.0, -2.5)), 70), (K(T, brow=1), 80), (K(T, handR=(8.5, 36.0, -2.5)), 70),
            (K(T, brow=2), 200), (K(handL=(6.0, 31.0, -9.0), handR=(4.0, 31.0, 8.0), blink=True), 110), (K(), 170)]


def fidget_flex():
    """Raises the laser hand, opens and closes it, rolls the shoulder."""
    U = dict(handL=(8.0, 38.0, -8.0))
    return [(K(), 150), (K(handL=(6.0, 32.0, -10.0)), 110), (K(U, brow=1), 120), (K(U, handL=(8.5, 39.0, -8.0)), 110),
            (K(U), 110), (K(handL=(5.0, 31.0, -11.0), lean=-0.3, breath=1), 130), (K(lean=0.2, blink=True), 120), (K(), 170)]


B0 = dict()
PW = dict(casing=1.0)
# hands within reach of short arms (audit reach2 <= 1.10)
HR_HIT = [(8.0, 31.0, 13.0), (7.0, 32.0, 13.5), (6.0, 30.0, 13.0)]
HL_HIT = [(-3.0, 31.0, -13.0), (-4.0, 32.0, -13.5), (-2.0, 30.0, -13.0)]
JR = [(3.0, 27.0, 12.0), (8.0, 36.0, 13.0), (9.0, 39.0, 13.5), (9.0, 38.0, 14.0), (8.0, 39.0, 13.5), (7.0, 29.0, 12.5)]
JL = [(-2.0, 27.0, -12.0), (4.0, 37.0, -13.0), (5.0, 40.0, -13.5), (5.0, 39.0, -14.0), (3.0, 40.0, -13.5), (4.0, 29.0, -12.5)]
DR = [(3.0, 28.0, 12.0), (1.0, 29.0, 12.5), (1.5, 28.5, 12.5), (4.0, 27.0, 12.0)]
DL = [(-5.0, 30.0, -12.0), (-5.0, 31.0, -12.0), (-4.5, 30.5, -12.0), (-2.5, 28.5, -12.0)]
TABLE = {
    'fidget_casing': fidget_casing(),
    'fidget_flex': fidget_flex(),
    'idle': idle2(B0),
    'walk': walk2(B0),
    'primary': beam(),
    'secondary': afterimage(),
    'special': limit_release(),
    'guard': guard_feet(guard(), dict(footR=(-2.0, 0.0), footL=(3.0, 0.0)), __import__('nix').P0),
    'hit': hit(B0, hR=HR_HIT, hL=HL_HIT),
    'defeat': defeat(B0),
    'jump': jump(B0, hR=JR, hL=JL),
    'stair_up': stairs(B0, REST_R, REST_L, True),
    'stair_down': stairs(B0, REST_R, REST_L, False),
    'dodge': dodge(B0, hR=DR, hL=DL),
    'powered_idle': idle2(PW),
    'powered_walk': walk2(PW),
    'powered_primary': beam(1.0, fast=True),
    'powered_guard': guard_feet(guard(1.0), dict(footR=(-2.0, 0.0), footL=(3.0, 0.0)), __import__('nix').P0),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ fix pass (audit, 25 Oct)
# no skating (anim.unskate) and the powered variants (anim.add_powered): the open casing stays
for _c in ('primary', 'secondary', 'special', 'hit', 'powered_primary', 'powered_exit'):
    TABLE[_c] = anim.unskate(TABLE[_c], __import__('nix').P0)
POWERED = dict(casing=1.0)

FIDGETS = ['fidget_casing', 'fidget_flex']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = __import__('nix').P0()
_SH = {}
for _c, _a in {'primary': [2, 6], 'special': [1, 4], 'powered_primary': [1, 4], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # v2: arc in-betweens
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 5, 'secondary': 3, 'special': 4, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](4)]}                                # the charge, held
ANCHOR_TAG = {'muzzle': 'laser'}

# v2 weapon aim within the facing (CONTRACT V2.8): the laser arm swings about its shoulder onto the
# aim; the drawings either side of the aimed ones turn half way.
AIM_CLIPS = ('primary', 'powered_primary')


def aim_table(clip, fc, deg):
    d = np.array(anim.aim_body(fc, deg))
    if fc == 'N' and deg > 0:                 # from behind, aimed across toward his right: raised over the head
        d = d + np.array([0.0, 0.5 * math.sin(math.radians(deg)), 0.0])
        d = d / np.linalg.norm(d)
    keys = TABLE[clip]
    aimed = [bool(P.get('handL')) and P['handL'][0] >= 12.0 for P, _ in keys]
    out = []
    for i, (P, ms) in enumerate(keys):
        w = 1.0 if aimed[i] else (0.5 if (i > 0 and aimed[i - 1]) or (i + 1 < len(keys) and aimed[i + 1]) else 0.0)
        if w and P.get('handL'):
            P = dict(P)
            sh = np.array([P.get('lean', 0.0) + 0.5, 40.5 + P.get('breath', 0), -SHW])
            h0 = np.array(P['handL'])
            L = float(np.linalg.norm(h0 - sh))
            h1 = sh + d * L
            if fc == 'N' and deg > 0:          # aimed across from behind: the arm stays out at his left so the lens clears his head
                h1 = h1 + np.array([0.0, 0.0, -8.0 * math.sin(math.radians(deg)) / math.sin(math.radians(45))])
            P['handL'] = tuple(round(float(x), 3) for x in h0 + (h1 - h0) * w)
        out.append((P, ms))
    return out
RELEASE_ANCHOR = {'primary': 'muzzle', 'secondary': 'origin', 'special': 'muzzle', 'powered_primary': 'muzzle'}

# The laser arm (casing, emitter, pauldron) is in every drawing; from behind (N) or turned
# away (E, far side) parts of it may be hidden by the body.
EQUIP = {
    'laser': dict(always=True, may_hide={'E', 'NE', 'SE'}),      # the far arm in E; it swings behind the body
}

EFFECTS = {
    'afterimage': dict(clip='secondary', release_frame=3, anchor='origin', files='fx/afterimage_<F>.png',
                       note='one stationary decoy at the activation origin (foot pivot); spawned once at release'),
}


# ================================================================ effect sprites (designer 3)
def write_effects(cid, sprites, meta):
    """Save separate effect sprites to out/<cid>/fx/ and record them in the manifest under
    'effects' (run after export.py, which rewrites the manifest).  sprites: {file: RGBA array},
    meta: {effect name: dict(...)}."""
    import os
    import json
    from ew import to_img
    od = os.path.join(anim.ROOT, 'out', cid)
    os.makedirs(os.path.join(od, 'fx'), exist_ok=True)
    for name, a in sprites.items():
        to_img(a).save(os.path.join(od, 'fx', name))
    mp = os.path.join(od, 'manifest.json')
    man = json.load(open(mp))
    man['effects'] = meta
    json.dump(man, open(mp, 'w'), indent=1)


def afterimage_sprites():
    """The decoy: Nix's idle drawing in each facing, recast in the cyan glow ramp by value, with
    every third row left out (a hologram read).  Hard alpha, palette tones only."""
    import numpy as np
    import nix
    from ew import MATS
    tones = np.array([[int(round(v)) for v in t] for t in MATS['nx_glow'].tones])
    out = {}
    for fc in anim.FACINGS:
        a = nix.draw(fc, nix.P0()).render().copy()
        op = a[..., 3] > 0
        lum = a[..., :3].astype(float) @ [0.3, 0.55, 0.15]
        k = np.clip((lum / 255.0 * 5.0).astype(int), 0, 3)
        a[..., :3][op] = tones[k[op]]
        rows = (np.arange(a.shape[0]) % 3) == 1
        a[rows, :, 3] = 0
        out['afterimage_%s.png' % fc] = a
    return out


if __name__ == '__main__':
    write_effects('nix', afterimage_sprites(), {
        'afterimage': dict(EFFECTS['afterimage'], frame_size=list(anim.CELL), foot_pivot=list(anim.PIVOT),
                           facings={fc: 'fx/afterimage_%s.png' % fc for fc in anim.FACINGS})})


# ================================================================ review media (designer 3)
ORDER = ['idle', 'walk', 'primary', 'secondary', 'special', 'powered_idle', 'powered_walk', 'powered_primary',
         'powered_guard', 'powered_exit', 'guard', 'hit', 'jump', 'stair_up', 'stair_down', 'dodge', 'defeat']


def actions_video(cid):
    """review/<cid>_actions.mp4: every clip once, east facing, in the woodland at 1920x1080
    (media.py's scene and encoder), with the separate effect sprites where the runtime spawns
    them (Nix's decoy, Rook's two turrets, Mote's three orbiting shards)."""
    import os
    import json
    import math
    import numpy as np
    from PIL import Image
    import media
    od = os.path.join(anim.ROOT, 'out', cid)
    media.OD = od
    media.MAN = json.load(open(os.path.join(od, 'manifest.json')))
    media._img = {}
    MAN = media.MAN
    fx = {}
    for name, e in MAN.get('effects', {}).items():
        files = e.get('facings', {}).get('E') or e.get('files')
        if isinstance(files, str):
            files = [files]
        fx[name] = (e, [np.array(Image.open(os.path.join(od, p)).convert('RGBA')) for p in files])
    tl, t, x, y = [], 0.0, 300.0, 352.0
    for c in ORDER:
        e = MAN['clips'][c]
        L = sum(e['durations']) * (2 if e['loop'] else 1)
        v = MAN['walk_speed'] if c in ('walk', 'powered_walk') else (150.0 if c == 'dodge' else 0.0)
        if c == 'secondary' and cid == 'rook':
            v = 120.0
        tl.append(dict(clip=c, t0=t, L=L, x0=x, v=v))
        t += L + 0.35
        x += v * L
        if x > 760:
            x = 300.0
    total = t + 1.0
    marks = []
    for s in tl:
        if s['clip'] == 'secondary' and cid == 'nix':
            marks.append(('afterimage', s['t0'] + MAN['clips']['secondary']['release_time'], s['t0'] + s['L'] + 2.5, s['x0']))
        if s['clip'] == 'special' and cid in ('rook', 'mote'):
            end = [q for q in tl if q['clip'] == 'powered_exit'][0]
            marks.append(('turrets' if cid == 'rook' else 'orbit_shards', s['t0'] + MAN['clips']['special']['release_time'],
                          end['t0'] + end['L'], s['x0']))

    def fn(tt):
        c = media.world()
        segs = [s for s in tl if s['t0'] <= tt]
        s = segs[-1]
        lt = tt - s['t0']
        e = MAN['clips'][s['clip']]
        if lt > s['L']:
            fr = e['facings']['E']['frames'][-1] if s['clip'] == 'defeat' else MAN['clips']['idle']['facings']['E']['frames'][0]
            lt = s['L']
        else:
            fr, i = media.frame_at(s['clip'], 'E', lt)
        px = s['x0'] + s['v'] * min(lt, s['L'])
        lift = 0
        d = e['durations']
        if s['clip'] == 'jump' or (s['clip'] == 'secondary' and cid == 'rook'):
            a, b = (sum(d[:2]), sum(d[:5])) if s['clip'] == 'jump' else (sum(d[:3]), sum(d[:6]))
            if a <= lt < b:
                u = (lt - a) / (b - a)
                lift = int(round(30 * 4 * u * (1 - u)))
            if s['clip'] == 'secondary':
                px = s['x0'] + (120.0 * min(max(0.0, lt - a), b - a))
        for name, t0, t1, ox in marks:
            if t0 <= tt < t1:
                e2, sprs = fx[name]
                if name == 'afterimage':
                    media.blit(c, sprs[0], int(ox) - anim.PIVOT[0], int(y) - anim.PIVOT[1])
                elif name == 'turrets':
                    for (dx, dy) in e2['offsets']:
                        media.shadow(c, ox + dx, y + dy, 8, 3)
                        media.blit(c, sprs[0], int(ox + dx) - 20, int(y + dy) - 32)
        media.shadow(c, px, y, 13 - lift * 0.1, 4.2)
        media.put(c, fr, px, y - lift)
        for name, t0, t1, ox in marks:
            if name == 'orbit_shards' and t0 <= tt < t1:
                e2, sprs = fx[name]
                for k in range(3):
                    ang = (tt - t0) * 1.7 + k * 2 * math.pi / 3
                    sx, sy = px + math.cos(ang) * 22, y - 42 + math.sin(ang) * 8
                    media.blit(c, sprs[k], int(sx) - 8, int(sy) - 8)
        return c, '%s  %s  east' % (MAN['name'], s['clip'])
    media.encode(os.path.join(anim.ROOT, 'review', '%s_actions.mp4' % cid), fn, int(total * media.FPS))


def facings_sheet(ids=('nix', 'rook', 'mote'), out='designer3_facings.png', z=3):
    """review/designer3_facings.png: each character's idle and powered idle in S, N, E, W."""
    import os
    from PIL import Image, ImageDraw, ImageFont
    from ew import zoom
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    rows = []
    for cid in ids:
        for clip in ('idle', 'powered_idle'):
            ims = [Image.open(os.path.join(anim.ROOT, 'out', cid, '%s_%s_00.png' % (clip, fc))).convert('RGBA').crop((30, 40, 130, 140))
                   for fc in anim.FACINGS]
            rows.append(('%s %s' % (cid, clip), ims))
    w, h = 100, 100
    bg = Image.new('RGBA', (w * 4 * 2, (h + 0) * 3), (126, 159, 80, 255))
    for r, (lab, ims) in enumerate(rows):
        for i, im in enumerate(ims):
            bg.alpha_composite(im, ((r % 2) * 4 * w + i * w, (r // 2) * h))
    big = zoom(bg, z)
    d = ImageDraw.Draw(big)
    for r, (lab, _) in enumerate(rows):
        d.text(((r % 2) * 4 * w * z + 6, (r // 2) * h * z + 4), lab + '   S  N  E  W', font=font, fill=(20, 20, 20))
    big.save(os.path.join(anim.ROOT, 'review', out))


# v2 (the strike is never hidden): from behind, Limit Release raises the laser forearm out at his
# left side instead of before his face, so the opened casing and the lens show past his head.
_BACK = {}


def facing_table(clip, fc):
    if fc not in ('N', 'NE', 'NW') or clip != 'special':
        return TABLE[clip]
    if clip not in _BACK:
        r = RELEASE[clip]
        out = []
        for i, (P, ms) in enumerate(TABLE[clip]):
            if r - 3 <= i <= r + 1 and P.get('handL') is not None:
                x, y, z = P['handL']
                P = dict(P, handL=(x - 1.0, y, min(z, -12.5)))
            out.append((P, ms))
        _BACK[clip] = out
    return _BACK[clip]

"""Pendle's animation table (Bramble template).  One revolver (right hip holster) and one
slung marksman rifle; the holster is empty whenever the revolver is in his hand.

primary   revolver: draw, aim, fire (flash at the muzzle), recoil, settle, holster.
secondary fan fire: revolver at the belt buckle, the left hand fans the hammer, three shots.
special   Longshot: the revolver is pushed home in its holster first, the left hand takes the
          rifle by the barrel over the left shoulder and swings it round (rifle='pull', rt
          0..1), the right hand takes the grip, and the rifle stays in both hands for the
          powered clips (aim, walk, fire with a lever cycle, guard) until powered_exit slings it.
reload    six rounds: draw, swing the cylinder out, tip the muzzle up and eject six cases, two
          loads from the belt loops, close, holster.
Body space: (fwd, up, lat), lat + = his RIGHT."""
import math
import numpy as np
import anim
from pendle import REST_R, REST_L, P0, SHW

A_STRIDE = 7.0
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 6.5 / anim.STAIR_LOOP, 1)

HOL = (-1.0, 28.0, 13.5)                  # right hand on the holstered revolver's grip
GUN = dict(revolver='hand')
# the rifle in both hands: right hand on the wrist of the stock (rgrip from the butt), left on
# the fore-end (rfore); shoulders turned so the left hand reaches it
def rpose(hR, hL, rgrip=10.0, **k):
    """Rifle in both hands: the right hand on the wrist of the stock at hR (rgrip from the
    butt), the left on the fore-end at hL; the rifle lies along the line through them."""
    d = [b - a for a, b in zip(hR, hL)]
    L = sum(x * x for x in d) ** 0.5
    return dict(rifle='hands', handR=hR, rdir=tuple(x / L for x in d), rgrip=rgrip, rfore=rgrip + L, **k)


READY = rpose((4.0, 30.0, 6.0), (10.0, 35.5, -2.0), twist=6.0)       # low ready: muzzle forward, up and across (a diagonal from the front)
SHOUL = dict(rifle='hands', handR=(6.0, 38.0, 6.0), rdir=(1.0, 0.02, -0.32), rgrip=10.0, rfore=19.0, twist=7.0)


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
    """v2 idle, 12 drawings in 1.6 s: a machine's slow breath (the chest plate rises), the duster
    and bandana half a beat behind, the lamps blink once."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    keys = []
    for i in range(12):
        if powered:
            P = K(READY, breath=br[i], lag=lag[i], blink=(i == 10), handR=add(READY['handR'], (0, 0.5 * br[i], 0)))
        else:
            P = K(breath=br[i], lag=lag[i], blink=(i == 10), handR=add(REST_R, (0, 0.5 * br[i], 0)), handL=add(REST_L, (0, 0.5 * br[i], 0)))
        keys.append((P, ms[i]))
    return keys


def walk(powered=False):
    """v2 walk, 12 drawings a stride: heavy steps, the duster's tails a drawing late."""
    keys = []
    n = anim.WALK_N2
    for g in anim.gait(n, A_STRIDE, 3.0, bob=1.0):
        s = g['swing']
        P = dict(footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=0.5, lag=1.5 + 0.8 * abs(s))
        if powered:
            P.update(READY, handR=add(READY['handR'], (0, 0.5 * abs(s), 0)))
        else:
            P.update(handR=add(REST_R, (-3.5 * s, 0.5, 0)), handL=add(REST_L, (3.5 * s, 0.5, 0)))
        keys.append((P, WALK_LOOP2 * 1000 / n))
    return keys


def fidget_hat():
    """Tips the hat's brim with two fingers of the left hand, the lamps dip."""
    B = dict(handL=(7.0, 55.0, -6.0))
    return [(K(), 150), (K(handL=(4.0, 36.0, -12.0)), 110), (K(B, brow=1), 120), (K(B, handL=(7.5, 54.0, -6.0), lean=0.4), 100),
            (K(B, lean=0.4, blink=True), 140), (K(handL=(4.0, 38.0, -12.0), lean=0.2), 110), (K(lag=0.3), 120), (K(), 170)]


def fidget_holster():
    """Rests the right hand on the holstered revolver's grip, taps it twice."""
    return [(K(), 150), (K(handR=add(HOL, (1.0, 2.0, 0.5))), 110), (K(handR=HOL, lean=-0.2), 120), (K(handR=add(HOL, (0, 1.0, 0))), 70),
            (K(handR=HOL), 80), (K(handR=add(HOL, (0, 1.0, 0))), 70), (K(handR=HOL, blink=True), 160), (K(handR=add(REST_R, (0, 1.0, 0))), 120),
            (K(), 170)]


def stairs(up=True):
    keys = []
    for g in anim.gait(8, 6.5, 7.0 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(footR=fr, footL=fl, bob=g['bob'], lean=2.0 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
                       handR=add(REST_R, (-2.0 * s, 0.5, 0)), handL=add(REST_L, (2.5 * s, 0.5, 0))), 90))
    return keys


# --------------------------------------------------------------------------------- revolver
def revolver():
    AIM = (13.0, 38.0, 8.0)
    D = (1.0, 0.0, -0.12)
    ST = dict(footR=(-2.5, 0.0), footL=(3.0, 0.0))
    return [
        (K(handR=HOL, lean=0.3), 50),                                                           # hand to the grip
        (K(GUN, ST, handR=(1.0, 31.0, 13.0), aim=(0.3, -1.0, 0.0)), 40),                         # draw: muzzle clears down
        (K(GUN, ST, handR=(7.0, 35.0, 11.0), aim=(1.0, -0.3, -0.05)), 35),                       # swing up
        (K(GUN, ST, handR=AIM, aim=D, lean=-0.5, handL=(2.0, 30.0, -13.0)), 60),                 # aim
        (K(GUN, ST, handR=AIM, aim=D, lean=-0.5, handL=(2.0, 30.0, -13.0)), 40),                 # steady
        (K(GUN, ST, handR=add(AIM, (0, 0.5, 0)), aim=D, flash=1, lean=-0.5), 30),                # fire (release)
        (K(GUN, ST, handR=(11.0, 41.0, 8.5), aim=(1.0, 0.5, -0.1), flash=2, lean=-1.2), 45),     # recoil
        (K(GUN, ST, handR=AIM, aim=D, lean=-0.6), 70),                                           # settle on aim
        (K(GUN, ST, handR=(6.0, 32.0, 12.0), aim=(1.0, -0.7, 0.0)), 70),                         # lower
        (K(handR=HOL), 70),                                                                      # holstered
        (K(), 100),
    ]


def fan():
    G = dict(GUN, handR=(7.0, 31.0, 5.0), aim=(1.0, 0.02, -0.08), footR=(-3.0, 0.0), footL=(3.5, 0.0), crouch=1.5, lean=1.0)
    UPL = (3.0, 35.5, -2.0)                  # left palm raised over the hammer
    DNL = (6.0, 32.5, -0.5)                  # palm swept across it
    kick = dict(handR=(6.5, 32.0, 5.0), aim=(1.0, 0.25, -0.08))
    return [
        (K(GUN, handR=(2.0, 31.0, 11.0), aim=(1.0, -0.3, 0.0)), 50),                            # draw
        (K(G, handL=UPL, crouch=1.0), 50),                                                       # to the buckle
        (K(G, handL=UPL, brow=1), 60),                                                           # set
        (K(G, handL=add(UPL, (0, 1.0, 0))), 40),                                                 # palm up
        (K(G, kick, handL=DNL, flash=1), 30),                                                    # shot 1 (release)
        (K(G, handL=UPL, flash=2), 35),
        (K(G, kick, handL=DNL, flash=1), 30),                                                    # shot 2
        (K(G, handL=UPL, flash=2), 35),
        (K(G, kick, handL=DNL, flash=1), 30),                                                    # shot 3
        (K(G, handL=(2.0, 30.0, -10.0), flash=2, footL=(-2.0, 0.0)), 60),
        (K(handR=HOL, crouch=0.5), 80),                                                          # holstered
        (K(), 100),
    ]


def reload():
    C = (10.0, 37.0, 6.0)                    # gun raised before the chest, clear of the coat
    LH = (10.0, 33.5, 1.0)                   # left hand under the open cylinder
    BELT = (0.0, 24.5, -10.0)                # left hand at the belt loops
    return [
        (K(handR=HOL), 70),
        (K(GUN, handR=(4.0, 31.0, 10.0), aim=(1.0, -0.2, -0.2)), 80),                             # draw
        (K(GUN, handR=C, aim=(0.8, 0.3, -0.5), handL=LH), 90),                                     # to the chest
        (K(GUN, handR=C, aim=(0.8, 0.3, -0.5), handL=LH, cyl=1.0, rounds=6, brow=1), 110),         # cylinder out (open)
        (K(GUN, handR=C, aim=(0.15, 1.0, -0.1), handL=(9.0, 31.0, -2.0), cyl=1.0, rounds=0, shells=(6, 0.15)), 90),  # muzzle up: eject
        (K(GUN, handR=C, aim=(0.5, 0.3, -0.4), handL=BELT, cyl=1.0, rounds=0, shells=(6, 1.0)), 100),  # cases fall, hand to belt
        (K(GUN, handR=C, aim=(0.7, -0.5, -0.3), handL=LH, cyl=1.0, rounds=3), 120),                # load three
        (K(GUN, handR=C, aim=(0.7, -0.5, -0.3), handL=BELT, cyl=1.0, rounds=3), 90),
        (K(GUN, handR=C, aim=(0.7, -0.5, -0.3), handL=LH, cyl=1.0, rounds=6), 120),                # load three more
        (K(GUN, handR=(8.0, 34.0, 6.0), aim=(1.0, 0.1, -0.2), handL=(3.0, 30.0, -10.0), cyl=0.0), 80),  # flick closed
        (K(handR=HOL), 100),                                                                       # holstered
        (K(), 140),
    ]


# --------------------------------------------------------------------------------- guard
def guard(powered=False):
    if powered:   # the rifle held up across the body as a bar
        Gd = dict(rifle='hands', handR=(7.0, 36.0, 9.0), rdir=(0.5, 0.7, -1.0), rgrip=10.0, rfore=25.0, twist=2.0)
        keys = [
            (K(READY), 55),
            (K(READY, handR=(5.0, 33.0, 9.0), rdir=(0.8, 0.3, -0.8), crouch=0.5), 55),
            (K(Gd, crouch=1.5), 55),
            (K(Gd, crouch=2.0, lean=1.0), 55),
            (K(Gd, crouch=2.5, lean=1.5), 120),
            (K(READY, handR=(5.0, 33.0, 9.0), rdir=(0.8, 0.3, -0.8), crouch=1.0), 120),
            (K(READY, crouch=0.5), 120),
            (K(READY), 120),
        ]
        return keys
    B = dict(footR=(-3.0, 0.0), footL=(3.5, 0.0))
    up_r, up_l = (8.0, 41.0, 5.0), (9.0, 39.0, -5.0)            # brass forearms crossed before the face
    return [
        (K(B, handR=(5.0, 32.0, 12.0), handL=(5.0, 31.0, -12.0), crouch=0.5), 55),
        (K(B, handR=(7.0, 37.0, 8.0), handL=(7.0, 36.0, -8.0), crouch=1.0), 55),
        (K(B, handR=up_r, handL=up_l, crouch=1.5, poleR=(-0.3, -1.0, 0.6), poleL=(-0.3, -1.0, -0.6)), 55),
        (K(B, handR=up_r, handL=up_l, crouch=2.0, lean=1.0, poleR=(-0.3, -1.0, 0.6), poleL=(-0.3, -1.0, -0.6)), 55),
        (K(B, handR=up_r, handL=up_l, crouch=2.5, lean=1.5, poleR=(-0.3, -1.0, 0.6), poleL=(-0.3, -1.0, -0.6)), 120),
        (K(handR=(7.0, 36.0, 8.0), handL=(7.0, 35.0, -8.0), footR=B['footR'], crouch=1.0), 120),   # left foot home first
        (K(handR=(4.0, 29.0, 14.0), handL=(3.0, 28.0, -14.0), crouch=0.5), 120),
        (K(), 120),
    ]


# --------------------------------------------------------------------------------- Longshot
def special():
    over = (-7.0, 47.0, -6.0)
    return [
        (K(handR=HOL, lean=0.3), 70),                                                             # revolver pushed home
        (K(handR=HOL, handL=(-3.0, 44.0, -10.0), poleL=(-0.3, -1.0, -0.6)), 70),                  # reach over the shoulder
        (K(rifle='pull', rt=0.0, rfore=31.0, handR=(2.0, 29.0, 13.0), poleL=(-0.3, -1.0, -0.6)), 70),   # grip the barrel
        (K(rifle='pull', rt=0.4, rfore=31.0, rdir=READY['rdir'], rgrip=10.0, handR=(2.0, 30.0, 11.0), twist=2.0), 60),  # swing it round
        (K(READY, rifle='pull', rt=0.8, rfore=19.0, twist=3.0), 50),
        (K(READY, crouch=1.0), 60),                                                               # in both hands (release)
        (K(READY, lever=1.0, handR=(1.0, 28.0, 9.0), crouch=1.0), 70),                            # work the lever
        (K(READY, crouch=0.5), 90),
        (K(READY), 110),
    ]


def powered_primary():
    return [
        (K(READY), 50),
        (K(SHOUL, handR=(4.0, 36.0, 7.0), crouch=0.5), 50),                                       # shoulder
        (K(SHOUL, crouch=1.0, lean=-0.3), 70),                                                    # aim, held
        (K(SHOUL, crouch=1.0, lean=-0.3, flash=1), 30),                                            # fire (release)
        (K(SHOUL, handR=(4.5, 39.0, 6.0), rdir=(1.0, 0.25, -0.32), crouch=1.0, lean=-1.2, flash=2), 50),  # recoil
        (K(SHOUL, handR=(5.0, 35.0, 6.5), rdir=(1.0, 0.1, -0.32), crouch=1.0, lean=-0.6), 60),     # lever down
        (K(SHOUL, crouch=1.0, lean=-0.3), 60),                                                    # lever up
        (K(READY, crouch=0.5), 80),
        (K(READY), 100),
    ]


def powered_exit():
    return [
        (K(READY), 90),
        (K(READY, rifle='pull', rt=0.8, rfore=19.0, twist=3.0), 90),
        (K(rifle='pull', rt=0.4, rfore=31.0, rdir=READY['rdir'], rgrip=10.0, handR=(2.0, 30.0, 11.0), twist=2.0), 100),
        (K(rifle='pull', rt=0.0, rfore=31.0, handR=(2.0, 29.0, 13.0), poleL=(-0.3, -1.0, -0.6)), 110),    # slung again
        (K(handL=(-3.0, 44.0, -10.0), poleL=(-0.3, -1.0, -0.6)), 110),
        (K(handL=(0.0, 33.0, -14.0)), 120),
        (K(lag=0.3), 120),
        (K(), 130),
    ]


# --------------------------------------------------------------------------------- hit, defeat, jump, dodge
def hit():
    return [
        (K(lean=-3.0, crouch=1.0, blink=True, handR=(5.0, 30.0, 18.0), handL=(-2.0, 30.0, -17.0), lag=-1.0), 35),
        (K(lean=-4.0, crouch=2.0, blink=True, handR=(4.0, 31.0, 18.5), handL=(-3.0, 31.0, -17.5), lag=-1.5), 65),
        (K(lean=-2.5, crouch=3.0, handR=(4.0, 28.0, 18.0), handL=(-1.0, 28.0, -17.0), lag=-0.5), 90),
        (K(lean=-1.0, crouch=2.0, lag=0.5), 120),
        (K(lean=0.5, crouch=1.0, lag=1.0), 130),
        (K(lean=0.3, crouch=0.5, lag=0.6), 150),
        (K(lag=0.2), 160),
        (K(), 180),
    ]


def defeat():
    k1 = dict(footR=(-6.0, 2.0), footL=(7.0, 0.0))
    k2 = dict(footR=(-8.0, 2.5), footL=(7.5, 0.0))
    return [
        (K(lean=-3.0, crouch=1.0, blink=True, handR=(5.0, 30.0, 17.0)), 80),
        (K(lean=2.0, crouch=5.0, handR=(8.0, 27.0, 15.0), handL=(6.0, 27.0, -15.0)), 100),
        (K(k1, lean=3.0, crouch=9.0, handR=(10.0, 26.0, 13.0), handL=(9.0, 26.0, -13.0)), 100),
        (K(k2, lean=4.0, crouch=12.0, handR=(11.0, 27.0, 12.0), handL=(10.0, 27.0, -12.0)), 120),
        (K(k2, lean=6.0, crouch=13.0, blink=True, handR=(12.0, 26.0, 12.0), handL=(11.0, 26.0, -12.0)), 150),
        (K(k2, lean=7.0, crouch=13.0, blink=True, handR=(12.0, 25.5, 12.0), handL=(11.0, 25.5, -12.0)), 180),
        (K(k2, lean=8.0, crouch=13.5, blink=True, handR=(12.0, 25.5, 12.0), handL=(11.0, 25.5, -12.0), lag=0.5), 240),
        (K(k2, lean=8.0, crouch=13.5, blink=True, handR=(12.0, 25.5, 12.0), handL=(11.0, 25.5, -12.0), lag=0.8), 300),
    ]


def jump():
    return [
        (K(crouch=4.0, lean=2.0, handR=(1.0, 23.0, 16.0), handL=(-1.0, 23.0, -16.0), lag=0.5), 80),
        (K(crouch=1.0, lean=1.0, footR=(2.0, 1.0), footL=(-2.0, 1.5), handR=(7.0, 34.0, 16.0), handL=(4.0, 35.0, -16.0)), 55),
        (K(footR=(2.5, 6.0), footL=(-1.5, 8.0), handR=(8.0, 38.0, 17.0), handL=(5.0, 39.0, -17.0), lag=-1.5), 80),
        (K(footR=(3.5, 8.0), footL=(-0.5, 9.0), handR=(8.0, 36.0, 17.5), handL=(5.0, 37.0, -17.5), lag=-0.5), 110),
        (K(footR=(2.5, 3.0), footL=(-2.5, 4.0), handR=(7.0, 38.0, 17.0), handL=(3.0, 39.0, -17.0), lag=1.5), 110),
        (K(crouch=5.0, lean=2.5, footR=(2.5, 0.0), footL=(-2.5, 0.0), handR=(8.0, 25.0, 16.0), handL=(6.0, 25.0, -16.0), lag=1.5), 80),
        (K(crouch=3.0, lean=1.5, footR=(2.5, 0.0), footL=(-2.5, 0.0), lag=1.0), 70),
        (K(), 115),                                                                       # recover = idle 0
    ]


def dodge():
    return [
        (K(crouch=3.0, lean=3.0, footR=(2.5, 0.0), footL=(-3.5, 0.0)), 55),
        (K(crouch=5.0, lean=6.0, footR=(5.0, 2.0), footL=(-8.5, 0.0), handR=(2.0, 25.0, 17.0), handL=(-3.0, 27.0, -16.0), lag=2.0), 45),
        (K(crouch=7.0, lean=8.0, footR=(8.0, 1.0), footL=(-8.5, 0.0), handR=(2.0, 27.0, 17.0), handL=(-2.0, 29.0, -16.0), lag=3.0), 40),
        (K(crouch=7.5, lean=8.0, footR=(8.0, 0.0), footL=(-8.0, 0.5), handR=(2.5, 26.0, 17.0), handL=(-2.0, 28.0, -16.0), lag=3.0), 45),
        (K(crouch=6.0, lean=6.0, footR=(6.0, 0.0), footL=(-6.0, 1.5), handR=(3.0, 25.0, 17.0), handL=(-1.0, 26.0, -16.0), lag=2.0), 60),
        (K(crouch=4.0, lean=4.0, footR=(4.0, 0.0), footL=(-3.5, 0.0), lag=1.5), 70),
        (K(crouch=2.0, lean=2.0, footR=(3.0, 0.0), footL=(-2.5, 0.0), lag=1.0), 80),
        (K(), 100),                                                                       # = idle 0
    ]


TABLE = {
    'fidget_hat': fidget_hat(),
    'fidget_holster': fidget_holster(),
    'idle': idle(),
    'walk': walk(),
    'primary': revolver(),
    'secondary': fan(),
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
    'powered_primary': powered_primary(),
    'powered_guard': guard(True),
    'powered_exit': powered_exit(),
    'reload': reload(),
}
# ------------------------------------------------------------------ fix pass (audit, 25 Oct)
# no skating: a foot that moves more than 3 px is lifted in that drawing (anim.unskate)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit', 'reload'):
    if _c in TABLE:
        TABLE[_c] = anim.unskate(TABLE[_c], P0)

# Powered variants: Longshot's rifle stays in both hands (low ready) through hit, dodge, jump and
# stairs.  Fan fire needs the revolver, so there is no powered secondary (runtime rule 5).


def POWERED(P, i):
    out = {k: v for k, v in P.items() if k not in ('handR', 'handL', 'revolver', 'aim', 'flash', 'poleL', 'poleR')}
    out.update(READY)
    return out


POWERED_SKIP = ('secondary',)

FIDGETS = ['fidget_hat', 'fidget_holster']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = P0()
_SH = {}
for _c, _a in {'primary': [2, 6], 'special': [5], 'powered_primary': [1, 4], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # v2: arc in-betweens
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 5, 'secondary': 4, 'special': 5, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](4)], 'powered_primary': [_SH['powered_primary'](2)]}     # the aim, held before the shot
ANCHOR_TAG = {'muzzle': 'revolver'}
ANCHOR_WITH = {'muzzle': ('rifle',)}             # Longshot and the powered shot fire the rifle
ANCHOR_COVER = {'muzzle': ('hat',)}             # aimed straight ahead from behind, the higher back brim is nearer the camera than the muzzle
WEAPON_TAG = {'special': 'rifle', 'powered_primary': 'rifle'}
WEAPON_WITH = {'primary': ('flash',), 'secondary': ('flash',), 'powered_primary': ('flash',)}   # the shot's flash at the muzzle shows the strike where the gun points at the camera

# v2 weapon aim within the facing (CONTRACT V2.8): the revolver arm swings about the right shoulder
# onto the aim (the arm points where the shot flies, anim.aim_body); the shouldered rifle turns
# about its stock like Brine's harpoon gun (level in S, raised from behind).
AIM_CLIPS = ('primary', 'powered_primary')
_AIMD = (1.0, 0.0, -0.12)
_RPIV = (2.0, 39.0, 6.0)


def _rot(a, b):
    a, b = np.array(a, float) / np.linalg.norm(a), np.array(b, float) / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a.dot(b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def aim_table(clip, fc, deg):
    keys = TABLE[clip]
    out = []
    if clip == 'primary':
        d = anim.aim_body(fc, deg)
        M = _rot(_AIMD, d)
        aimed = [P.get('revolver') == 'hand' and P.get('handR') is not None and P['handR'][0] >= 10.0 for P, _ in keys]
        for i, (P, ms) in enumerate(keys):
            w = 1.0 if aimed[i] else (0.5 if (i > 0 and aimed[i - 1]) or (i + 1 < len(keys) and aimed[i + 1]) else 0.0)
            if w and P.get('handR') and P.get('aim'):
                P = dict(P)
                sh = np.array([P.get('lean', 0.0) + 0.3, 39.5 + P.get('breath', 0), SHW])
                h0 = np.array(P['handR'])
                h1 = sh + M @ (h0 - sh)
                if fc == 'N' and deg < 0:      # from behind, aimed across to his left: raised at his right, past the hat's brim
                    h1 = sh + np.array([3.0, 13.0, 7.0])
                a1 = M @ np.array(P['aim'], float)
                P['handR'] = tuple(round(float(x), 3) for x in h0 + (h1 - h0) * w)
                a = np.array(P['aim'], float) + (a1 - np.array(P['aim'], float)) * w
                P['aim'] = tuple(round(float(x), 3) for x in a / np.linalg.norm(a))
            out.append((P, ms))
        return out
    d = anim.aim_body(fc, deg) if fc == 'N' else anim.aim_level(fc, deg)
    M = _rot(SHOUL['rdir'], d)
    aimed = [P.get('rdir') == SHOUL['rdir'] or (P.get('rifle') == 'hands' and P.get('handR', (0,))[0] >= 4.5 and P.get('rgrip') == 10.0
                                                and P.get('rfore') == 19.0) for P, _ in keys]
    for i, (P, ms) in enumerate(keys):
        w = 1.0 if aimed[i] else (0.5 if (i > 0 and aimed[i - 1]) or (i + 1 < len(keys) and aimed[i + 1]) else 0.0)
        if w and P.get('rdir'):
            P = dict(P)
            h0 = np.array(P['handR'])
            h1 = np.array(_RPIV) + M @ (h0 - np.array(_RPIV))
            r1 = M @ np.array(P['rdir'], float)
            if fc == 'N':                      # from behind: out past the shoulder on the aim's side, clear of the hat
                h1 = h1 + np.array([0.0, 2.0, 7.0 if deg >= 0 else -17.0])
            P['handR'] = tuple(round(float(x), 3) for x in h0 + (h1 - h0) * w)
            r = np.array(P['rdir'], float) + (r1 - np.array(P['rdir'], float)) * w
            P['rdir'] = tuple(round(float(x), 3) for x in r / np.linalg.norm(r))
        out.append((P, ms))
    return out
RELEASE_ANCHOR = {'primary': 'muzzle', 'secondary': 'muzzle', 'special': 'muzzle', 'powered_primary': 'muzzle'}
EQUIP = {
    'revolver': dict(always=True, may_hide={'W', 'N', 'S', 'E', 'SE', 'SW', 'NE', 'NW'}),   # one gun, holster or hand (by construction);
                                                                     # the aiming hand covers it head-on
    'holster': dict(always=True, may_hide={'W', 'N', 'SW', 'NW', 'NE'}),
    'rifle': dict(always=True),
    'hat': dict(always=True),
    'flash': dict(clips={'primary': [RELEASE['primary']], 'secondary': [4, 6, 8], 'powered_primary': [RELEASE['powered_primary']]},
                  may_hide={'N', 'NE', 'NW'}),   # the body hides it from behind
}


# v2 (the strike is never hidden): from behind, the fan fire is made with the revolver held out at
# his right hip, past the duster, instead of at the buckle.
_BACK = {}


def facing_table(clip, fc):
    if fc not in ('N', 'NE', 'NW') or clip != 'secondary':
        return TABLE[clip]
    if clip not in _BACK:
        out = []
        for i, (P, ms) in enumerate(TABLE[clip]):
            if P.get('revolver') == 'hand' and P.get('handR') is not None and 1 <= i <= 9:
                x, y, z = P['handR']
                P = dict(P, handR=(x - 1.0, y + 1.0, max(z, 13.0)))
                if P.get('handL') is not None:
                    lx, ly, lz = P['handL']
                    P['handL'] = (lx - 1.0, ly + 1.0, lz + 13.0)
            out.append((P, ms))
        _BACK[clip] = out
    return _BACK[clip]

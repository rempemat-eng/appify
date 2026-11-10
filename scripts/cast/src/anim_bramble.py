"""Bramble's animation table: every clip of the contract as keys (pose, ms).  The template the
other characters copy.  A pose only names what differs from bramble.P0; the rig renders it in
S, N, E and W.  Timings are authored in ms and refitted by anim.fit_timing to Codex's total
duration and release time.

The billhook is used by the RIGHT hand on purpose although he is left-handed (Codex's art and
pass 2): the right is his bow hand, so stowing the bow over the left shoulder frees exactly the
hand that then draws the billhook from the right hip, and the left (draw) hand stays free for
the off-hand guard; switching would put the blade in the hand still holding the bow.

Body space reminder: (fwd, up, lat), lat + = his RIGHT.  He holds the bow in his RIGHT hand and
draws with the LEFT; the quiver is over the LEFT shoulder; the billhook hangs at the RIGHT hip;
the folding buckler is the bracer on the RIGHT forearm.
"""
import math
import numpy as np
import anim
from bramble import REST_R, REST_L, P0

A_STRIDE = 9.5
# v2 (Matt 25 Oct: "a touch too slow"): 15 % faster.  The stride stays 4 x 9.5 = 38 px (longer
# would stretch the legs past 1.03 of their length), so the cadence rises: 12 drawings in 0.487 s.
WALK_SPEED = round(67.9 * 1.15, 1)                            # 78.1 px/s
WALK_LOOP = 4 * A_STRIDE / WALK_SPEED                         # 0.4866 s a stride
FACINGS = anim.FACINGS8
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

ST = dict(footR=(5.0, 0.0), footL=(-4.0, 0.0))               # archer's stance: bow-side foot forward
QUIVER = (-5.0, 49.0, -8.5)                                    # left hand at the quiver mouth


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


TW = 0.70                       # v2: shoulders turned 40 degrees at full draw (bow shoulder forward)
AIM_LAT = 1.0                   # the arrow line: straight ahead, in front of the chin


def aim(grip, nockp, draw, tw=TW, **k):
    """Bow up and aimed: right hand at grip, string (and arrow) at nockp held by the left hand.
    v2: the arrow lies along the facing (both points on the line lat = AIM_LAT), with the
    shoulders turned (twist) so both arms reach it, so the drawn arrow points where it flies in
    all eight facings."""
    grip = (grip[0], grip[1], AIM_LAT)
    nockp = (nockp[0], nockp[1], AIM_LAT)
    n = np.subtract(grip, nockp)
    n = tuple(n / np.linalg.norm(n))
    d = dict(ST, handR=grip, handL=nockp, bowu=(0.0, 1.0, 0.0), bown=n, draw=draw, nock='hand' if draw > 0.05 else None, arrow=True, twist=tw)
    d.update(k)
    return d


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


# --------------------------------------------------------------------------------- idle
def idle(briar=0.0):
    """v2 breathing idle, 12 drawings in 1.6 s: the chest rises 1 px and settles, the hands ride
    with it, the mantle and beard answer half a beat later, one blink."""
    keys = []
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.7, 0.5, 0.3, 0.1, 0.0, -0.1]
    hair = [0.0, 0.0, 0.0, 0.0, -0.3, -0.5, -0.6, -0.5, -0.3, 0.0, 0.0, 0.0]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    for i in range(12):
        keys.append((K(breath=br[i], lag=lag[i], hair=hair[i], blink=(i == 10), briar=briar,
                       handR=add(REST_R, (0, 0.5 * br[i], 0)), handL=add(REST_L, (0, 0.5 * br[i], 0))), ms[i]))
    return keys


# --------------------------------------------------------------------------------- walk
def walk(briar=0.0):
    """v2 walk: 12 drawings a stride (anim.gait), arms counter-swing, the mantle and quiver bounce
    with the bob, the beard trails."""
    keys = []
    n = anim.WALK_N2
    for i, g in enumerate(anim.gait(n, A_STRIDE, 3.5, bob=1.0)):
        s = g['swing']
        ph = 2 * np.pi * i / n
        keys.append((K(footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.2, lag=1.6 + 0.8 * abs(s) + 0.4 * g['bob'],
                       hair=-1.0 - 0.5 * np.cos(2 * ph),
                       handR=add(REST_R, (-2.5 * s, 0.5, 0)), handL=add(REST_L, (4.5 * s, 0.8 * abs(s), 0)), briar=briar),
                     WALK_LOOP * 1000 / n))
    return keys


# --------------------------------------------------------------------------------- fidgets (v2)
def fidget_string():
    """Checks the bowstring: lifts the bow, plucks the string with the draw hand, listens to it
    hum, nods and lowers the bow."""
    g = (10.0, 36.0, 9.0)
    s0 = (6.0, 37.5, 3.0)
    B = dict(handR=g, bowu=(0.1, 1.0, 0.15))
    return [
        (K(), 160),
        (K(handR=(9.5, 31.0, 12.0), bowu=(0.15, 1.0, 0.1), lean=0.2), 110),
        (K(B, handL=(3.0, 33.0, -6.0), lean=0.3), 110),
        (K(B, handL=s0, lean=0.4, brow=1), 120),
        (K(B, handL=add(s0, (-1.2, 0, -0.6)), draw=0.08, lean=0.4, brow=1), 90),          # pulls it
        (K(B, handL=add(s0, (-3.0, -1.0, -2.5)), draw=0.0, lean=0.2), 60),                 # lets go
        (K(B, handL=add(s0, (-3.5, -1.5, -3.0)), draw=0.04, lean=0.1, face='shut'), 70),   # it hums
        (K(B, handL=add(s0, (-3.5, -1.5, -3.0)), draw=0.0, lean=0.1, face='shut'), 70),
        (K(B, handL=add(s0, (-3.5, -1.5, -3.0)), draw=0.02, lean=0.0, face='shut'), 80),
        (K(B, handL=(2.0, 33.0, -8.0), lean=0.6, hair=0.6), 140),                          # nods
        (K(B, handL=(1.5, 29.0, -12.0), lean=0.2, hair=0.2), 120),
        (K(handR=(9.5, 31.0, 12.0), bowu=(0.15, 1.0, 0.1)), 130),
        (K(), 170),
    ]


def fidget_beard():
    """Scratches his beard with the draw hand, eyes shut, then smooths it."""
    b = (7.5, 49.0, -3.0)
    return [
        (K(), 150),
        (K(handL=(4.0, 37.0, -9.0)), 110),
        (K(handL=(7.0, 46.5, -4.5), lean=-0.2), 100),
        (K(handL=b, lean=-0.3, face='shut'), 90),
        (K(handL=add(b, (0.3, 1.6, 0.4)), lean=-0.3, face='shut', hair=0.4), 80),
        (K(handL=add(b, (0.0, -0.4, 0.0)), lean=-0.3, face='shut', hair=-0.2), 80),
        (K(handL=add(b, (0.3, 1.6, 0.4)), lean=-0.3, face='shut', hair=0.4), 80),
        (K(handL=add(b, (0.0, -0.4, 0.0)), lean=-0.3, face='shut', hair=-0.2), 80),
        (K(handL=add(b, (-0.5, -2.5, -0.5)), lean=-0.1, hair=0.3), 110),                     # smooths it down
        (K(handL=(4.0, 37.0, -9.0), lean=0.0), 110),
        (K(handL=(1.5, 28.0, -13.0)), 120),
        (K(), 160),
    ]


def fidget_quiver():
    """Reaches over his left shoulder, half draws an arrow to count what is left, slides it back
    and pats the quiver."""
    q = QUIVER
    return [
        (K(), 150),
        (K(handL=(-1.0, 38.0, -12.5), lean=-0.2, poleL=(-0.3, -1.0, -0.6)), 110),
        (K(handL=q, lean=-0.5, poleL=(-0.3, -1.0, -0.6), lag=0.5), 110),
        (K(handL=add(q, (1.0, 4.0, 0.8)), qarrow=True, lean=-0.6, poleL=(-0.3, -1.0, -0.6), lag=0.8), 140),
        (K(handL=add(q, (1.0, 4.0, 0.8)), qarrow=True, lean=-0.6, poleL=(-0.3, -1.0, -0.6), lag=0.6, brow=1), 160),
        (K(handL=q, lean=-0.5, poleL=(-0.3, -1.0, -0.6), lag=0.2), 100),
        (K(handL=add(q, (0.0, -2.0, 0.0)), lean=-0.4, poleL=(-0.3, -1.0, -0.6), lag=-0.4), 80),   # pat
        (K(handL=add(q, (0.0, -0.5, 0.0)), lean=-0.4, poleL=(-0.3, -1.0, -0.6), lag=0.3), 80),
        (K(handL=(-1.0, 38.0, -12.5), lean=-0.1), 110),
        (K(), 160),
    ]


def stairs(up=True):
    keys = []
    for g in anim.gait(8, 7.0, 7.0 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:     # the leading foot reaches down to the next tread
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(footR=fr, footL=fl, bob=g['bob'], lean=2.5 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
                       handR=add(REST_R, (-2.0 * s, 0.5, 0)), handL=add(REST_L, (3.5 * s, 0.5, 0))), 90))
    return keys


# --------------------------------------------------------------------------------- bow shot
def shot(briar=0.0, fast=False, d=None, cant=0.0):
    """v2 bow shot, 17 drawings in Codex's 0.64 s with the release still at 0.33 s: a dip of
    anticipation, the reach to the quiver, the arrow out and travelling to the string, raise,
    quarter, half and full draw, the anchor, the release (bow hand kicks forward, string hand
    flies back past the ear), the string's shiver, then the lowering and the settle.  The mantle,
    quiver and beard trail every move (anim.follow)."""
    G = (15.5, 46.0, 6.0)
    keys = [
        (K(ST, handR=(9.5, 31.0, 12.5), bowu=(0.15, 1.0, 0.0), crouch=0.6, lean=-0.3), 40),                     # 0 anticipation dip
        (K(ST, handR=(10.0, 33.0, 12.0), bowu=(0.15, 1.0, 0.0), lean=0.3), 30),                                   # 1 ready
        (K(ST, handR=(11.0, 35.0, 11.0), handL=QUIVER, poleL=(-0.3, -1.0, -0.6), lean=-0.4), 35),                # 2 reach back
        (K(ST, handR=(11.0, 36.0, 10.5), handL=(-3.0, 54.0, -7.0), qarrow=True, poleL=(-0.3, -1.0, -0.6)), 35),  # 3 arrow out
        (K(ST, handR=(11.5, 37.5, 9.5), handL=(0.0, 51.0, -5.0), qarrow=True, poleL=(-0.3, -1.0, -0.6), lean=-0.2, twist=TW * 0.2), 25),  # 4 arrow over
        (aim((12.0, 39.0, 8.0), (5.0, 41.0, 1.0), 0.0, tw=TW * 0.4, bob=1, bowu=(0.35, 1.0, 0.0)), 30),          # 5 nock
        (aim((15.0, 44.5, 6.5), (8.0, 45.5, 0.5), 0.1, tw=0.30), 28),                                       # 6 raise
        (aim(G, (6.5, 46.5, 0.0), 0.35, tw=0.45, bob=1), 26),                                                              # 7 quarter draw
        (aim(G, (4.0, 47.5, -0.6), 0.75, lean=-0.4), 28),                                                         # 8 half draw
        (aim(G, (2.5, 48.0, -1.0), 1.0, lean=-0.6, brow=1), 34),                                                  # 9 full draw
        (aim(G, (1.5, 48.0, -1.2), 1.0, lean=-0.7, brow=1), 30),                                                  # 10 anchor (hold)
        (K(ST, handR=(17.0, 45.5, AIM_LAT), handL=(-3.5, 51.0, -3.0), bowu=(0.3, 1.0, 0.0), bown=(1, 0, 0), lean=-1.0, brow=1, twist=TW), 35),   # 11 release
        (K(ST, handR=(17.5, 45.0, AIM_LAT), handL=(-4.0, 52.0, -4.0), bowu=(0.2, 1.0, 0.0), bown=(1, 0, 0), draw=0.06, lean=-0.8, twist=TW), 40),  # 12 string shivers
        (K(ST, handR=(17.0, 45.0, AIM_LAT + 0.5), handL=(-2.5, 48.0, -5.0), bowu=(0.15, 1.0, 0.0), bown=(1, 0, 0), lean=-0.5, twist=TW * 0.8), 55),  # 13 follow-through
        (K(ST, handR=(14.0, 40.0, 6.0), handL=(-2.0, 40.0, -9.0), bowu=(0.12, 1.0, 0.05), lean=-0.3, twist=TW * 0.4), 55),                         # 14 lowering
        (K(ST, handR=(12.0, 36.0, 10.0), handL=(-1.0, 32.0, -12.0), bowu=(0.1, 1.0, 0.0), lean=-0.2), 60),                         # 15 lower
        (K(footR=(3.0, 0.0), footL=(-3.0, 0.0), handR=add(REST_R, (0.5, 1.0, 0)), crouch=0.3), 60),                                # 16 settle
        (K(footR=(3.0, 0.0), footL=(-3.0, 0.0)), 90),                                                                               # 17 rest
    ]
    # aim weight per drawing: how far the drawing turns to the aim (the reach to the quiver does not)
    wts = [0, 0, 0, 0, 0.1, 0.5, 0.75, 1, 1, 1, 1, 1, 1, 1, 0.6, 0.25, 0, 0]
    if fast:      # Briarshot: the living bow nocks itself; skip the quiver reach
        sel = [0, 1, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17]
        keys = [keys[i] for i in sel]
        wts = [wts[i] for i in sel]
        wts[2] = 0.3
        keys[2] = (K(ST, handR=(12.0, 38.0, 9.5), handL=(4.0, 42.0, -3.0)), 45)   # v2: the briar sets the arrow; no quiver reach (no one-drawing arrow pop from behind)
    if d is not None:
        keys = [(orient(P, d, w, cant), ms) for (P, ms), w in zip(keys, wts)]
    for P, _ in keys:
        P['briar'] = briar
    return keys


AIM_PIVOT = (2.0, 46.0, 1.0)            # the archer turns the draw about his chest


def orient(P, d, w, cant=0.0):
    """Turn an aimed drawing (hands, bow, nock) about the chest from straight ahead to the aim d
    (body space, anim.aim_body), by the fraction w: pitch about the shoulders' axis, then yaw about
    the spine; the shoulders' twist follows the yaw so both arms keep their reach."""
    if w <= 0:
        return P
    fwd, up, lat = d
    th = math.atan2(up, math.hypot(fwd, lat)) * w
    ps = math.atan2(lat, fwd) * w
    def rot(v, about_pivot=True):
        x, y, z = (np.subtract(v, AIM_PIVOT) if about_pivot else np.array(v, float))
        x, y = x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th)
        x, z = x * math.cos(ps) - z * math.sin(ps), x * math.sin(ps) + z * math.cos(ps)
        out = np.array([x, y, z])
        return tuple(out + AIM_PIVOT) if about_pivot else tuple(out)
    P = dict(P)
    for k in ('handR', 'handL'):
        if P.get(k) is not None:
            P[k] = rot(P[k])
    for k in ('bowu', 'bown'):
        if P.get(k) is not None:
            P[k] = rot(P[k], False)
    if P.get('bow', 'hand') == 'hand' and P.get('bown') is None and w >= 1:
        P['bown'] = rot((1.0, 0.0, 0.0), False)
    P['twist'] = P.get('twist', 0.0) - ps
    if cant and P.get('bowu') is not None and P.get('bown') is not None:
        # cant the bow about the arrow line (top limb out to his right), so seen from behind or in
        # front it stands clear of his head instead of hiding behind it
        u, n = np.array(P['bowu'], float), np.array(P['bown'], float)
        n = n / np.linalg.norm(n)
        a = cant * w
        u = u * math.cos(a) + np.cross(n, u) * math.sin(a) + n * n.dot(u) * (1 - math.cos(a))
        P['bowu'] = tuple(u)
    return P


AIM_CLIPS = ('primary', 'powered_primary')
def cant_for(fc, deg):
    """Radians the bow is canted about the arrow line in the facings that look along it (N, S),
    toward the side where it stands clear of his head and body (measured: bow pixels per cant)."""
    if fc == 'N':
        return 1.0 if deg <= 0 else -1.0
    if fc == 'S':
        return -0.6 if deg <= 0 else 0.6
    return 0.0


def aim_table(clip, fc, deg):
    """The weapon clip drawn for one aim (anim.AIM_DEGS) in one body facing: the same timing and
    release drawing as the facing's own, the draw turned to anim.aim_body(fc, deg)."""
    d = anim.aim_body(fc, deg)
    cant = cant_for(fc, deg)
    keys = shot(1.0, fast=True, d=d, cant=cant) if clip == 'powered_primary' else shot(0.0, d=d, cant=cant)
    keys = anim.follow(keys)
    return anim.unskate(keys, P0)


# --------------------------------------------------------------------------------- billhook
def billhook():
    """v2 billhook cut, 16 drawings in 0.64 s with the contact still at 0.33 s: the bow goes over
    the shoulder, the right hand draws the billhook, winds up past the hip (anticipation), cuts
    through a smear in-between to the contact, overshoots low, recovers and puts both back."""
    W = dict(footR=(5.0, 0.0), footL=(-5.0, 0.0))
    return [
        (K(handR=(3.0, 47.0, 10.0), bowu=(-0.6, 1.0, -0.2), handL=(2.0, 28.0, -13.0)), 35),                  # 0 bow up to the shoulder
        (K(bow='back', handR=(-3.0, 45.0, 9.0), handL=(3.0, 28.0, -13.0)), 30),                               # 1 slung on the back
        (K(bow='back', handR=(-1.5, 27.0, 13.5), handL=(4.0, 29.0, -13.0)), 30),                              # 2 hand to the billhook
        (K(W, bow='back', hook='hand', handR=(-7.0, 45.0, 12.0), hookdir=(-0.4, 1.0, 0.0), handL=(6.0, 31.0, -12.0), lean=-0.8), 35),   # 3 draw, wind up
        (K(W, bow='back', hook='hand', handR=(-9.5, 50.0, 11.0), hookdir=(-0.8, 0.6, 0.0), handL=(8.0, 33.0, -11.0), lean=-1.2, crouch=1.0, brow=1), 55),  # 4 load
        (K(W, bow='back', hook='hand', handR=(-10.0, 51.0, 10.5), hookdir=(-0.9, 0.45, 0.0), handL=(8.5, 33.5, -11.0), lean=-1.4, crouch=1.2, brow=1), 45),  # 5 held
        (K(W, bow='back', hook='hand', handR=(10.0, 47.0, 6.0), hookdir=(0.9, 0.4, -0.1), handL=(3.0, 31.0, -13.0), lean=1.2, crouch=1.5, brow=1), 22),   # 6 smear (over the top of the arc, so the blade stays in sight in every facing)
        (K(W, bow='back', hook='hand', handR=(16.0, 34.0, 6.0), hookdir=(1.0, -0.25, 0.0), handL=(-3.0, 30.0, -14.0), lean=3.0, crouch=2.0, brow=1), 30),  # 7 contact
        (K(W, bow='back', hook='hand', handR=(12.5, 27.0, 7.5), hookdir=(0.7, -0.9, 0.0), handL=(-4.5, 29.0, -14.0), lean=3.2, crouch=2.4), 35),  # 8 overshoot
        (K(W, bow='back', hook='hand', handR=(9.0, 26.0, 8.5), hookdir=(0.5, -1.0, 0.0), handL=(-4.0, 29.0, -14.0), lean=2.5, crouch=2.0), 40),   # 9 follow-through
        (K(W, bow='back', hook='hand', handR=(4.0, 30.0, 12.0), hookdir=(0.2, 1.0, 0.0), lean=1.0, crouch=1.0), 45),   # 10 recover
        (K(bow='back', handR=(-1.5, 27.0, 13.5), lean=0.4), 45),                                                # 11 billhook back on the hip
        (K(bow='back', handR=(-3.0, 45.0, 9.0)), 45),                                                          # 12 reach for the bow
        (K(handR=(3.0, 42.0, 11.0), bowu=(-0.3, 1.0, 0.0)), 45),                                               # 13 bow back in hand
        (K(handR=add(REST_R, (0.5, 3.0, 0.0)), bowu=(0.1, 1.0, 0.0)), 50),                                     # 14 lowering
        (K(), 70),
    ]


# --------------------------------------------------------------------------------- guard (folding buckler)
def guard(briar=0.0):
    B = dict(footR=(4.0, 0.0), footL=(-4.0, 0.0))
    up = (11.0, 42.0, 8.0)
    keys = [
        (K(handR=(3.0, 47.0, 10.0), bowu=(-0.6, 1.0, -0.2)), 55),                                       # bow to the shoulder
        (K(B, bow='back', handR=(4.0, 38.0, 12.0), buckler=0.2, crouch=0.5), 55),                       # slung; arm comes round
        (K(B, bow='back', handR=(9.0, 41.0, 10.0), buckler=0.6, crouch=1.0, poleR=(-0.4, -1.0, 0.6)), 55),
        (K(B, bow='back', handR=up, buckler=0.9, crouch=1.5, lean=1.0, poleR=(-0.4, -1.0, 0.6), brow=1), 55),
        (K(B, bow='back', handR=up, buckler=1.0, crouch=2.0, lean=1.5, poleR=(-0.4, -1.0, 0.6), handL=(4.0, 30.0, -12.0), brow=1), 120),  # braced (hold)
        (K(B, bow='back', handR=(-3.0, 45.0, 9.0), buckler=0.3, crouch=1.0), 120),                      # fold, reach for the bow
        (K(handR=(3.0, 40.0, 11.0), bowu=(-0.3, 1.0, 0.0)), 120),                                       # bow in hand
        (K(), 120),                                                                                      # = idle 0 (the runtime cuts to idle)
    ]
    for P, _ in keys:
        P['briar'] = briar
    return keys


# --------------------------------------------------------------------------------- hit, defeat
def hit():
    """v2 hit, 10 drawings: the snap back (eyes shut), the recoil's low point, the beard and
    mantle whipping forward after it, the recovery and a breath before the rest pose."""
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2, handR=(12.0, 30.0, 15.0), handL=(-5.0, 30.0, -15.0)), 30),
        (K(lean=-4.2, crouch=2.0, face='shut', brow=2, handR=(11.0, 31.5, 15.5), handL=(-6.5, 31.5, -15.5)), 50),
        (K(lean=-3.6, crouch=2.8, face='shut', brow=2, handR=(10.5, 30.0, 15.2), handL=(-5.0, 30.0, -15.2)), 60),
        (K(lean=-2.5, crouch=3.0, brow=2, handR=(10.0, 28.0, 15.0), handL=(-3.0, 28.0, -15.0)), 80),
        (K(lean=-1.0, crouch=2.0, brow=2), 100),
        (K(lean=0.3, crouch=1.2, brow=1), 110),
        (K(lean=0.6, crouch=0.8, brow=1), 110),
        (K(lean=0.3, crouch=0.4), 130),
        (K(breath=1), 140),
        (K(), 150),
    ]


def defeat():
    # hands are in standing coordinates (the crouch lowers them), so a hand at up 27 with
    # crouch 13 sits 14 px above the ground
    k1 = dict(footR=(7.0, 0.0), footL=(-6.0, 2.0))         # going down on the left knee
    k2 = dict(footR=(7.5, 0.0), footL=(-8.0, 2.5))
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2, handL=(-4.0, 29.0, -15.0)), 80),
        (K(lean=2.0, crouch=5.0, face='shut', brow=2, handR=(11.0, 25.0, 15.0), bowu=(0.5, 1.0, 0.0), handL=(4.0, 26.0, -15.0)), 100),
        (K(k1, lean=3.0, crouch=9.0, brow=2, handR=(12.0, 26.0, 14.0), bowu=(0.8, 1.0, 0.0), handL=(7.0, 28.0, -13.0)), 100),
        (K(k2, lean=4.0, crouch=12.0, brow=2, handR=(12.5, 38.5, 11.0), bowu=(0.3, 1.0, 0.0), handL=(8.0, 30.0, -10.0)), 120),
        # v2: the bigger bow no longer lies on the ground (it would reach past the cell toward the
        # camera); he kneels leaning on it, planted upright beside his right knee
        (K(k2, lean=6.0, crouch=13.0, brow=2, face='shut', handR=(12.0, 40.5, 10.5), bowu=(0.14, 1.0, 0.0), handL=(8.0, 29.0, -10.0)), 150),
        (K(k2, lean=7.0, crouch=13.0, face='shut', handR=(12.0, 40.5, 10.0), bowu=(0.1, 1.0, 0.0), handL=(8.0, 29.0, -10.0)), 180),
        (K(k2, lean=8.0, crouch=13.5, face='shut', handR=(12.0, 41.0, 10.0), bowu=(0.1, 1.0, 0.0), handL=(8.0, 28.5, -10.0), lag=0.5), 240),
        (K(k2, lean=8.0, crouch=13.5, face='shut', handR=(12.0, 41.0, 10.0), bowu=(0.1, 1.0, 0.0), handL=(8.0, 28.5, -10.0), lag=0.8), 300),
    ]


# --------------------------------------------------------------------------------- jump, dodge
def jump():
    # roles by index (Codex's runtime picks them): load, push, rise, apex, fall, land, absorb, recover
    return [
        (K(crouch=4.0, lean=2.0, handR=(4.0, 22.0, 15.0), handL=(0.0, 24.0, -14.0), lag=0.5), 80),
        (K(crouch=1.0, lean=1.0, footR=(2.5, 1.0), footL=(-2.5, 1.5), handR=(9.0, 36.0, 15.0), handL=(4.0, 38.0, -15.0)), 55),
        (K(footR=(3.0, 6.0), footL=(-2.0, 8.0), handR=(10.0, 40.0, 16.0), handL=(5.0, 42.0, -16.0), lag=-1.5), 80),
        (K(footR=(4.0, 8.0), footL=(-1.0, 9.0), handR=(10.0, 38.0, 16.5), handL=(5.0, 40.0, -16.5), lag=-0.5), 110),
        (K(footR=(3.0, 3.0), footL=(-3.0, 4.0), handR=(9.0, 40.0, 16.0), handL=(3.0, 42.0, -16.0), lag=1.5), 110),
        (K(crouch=5.0, lean=2.5, footR=(3.0, 0.0), footL=(-3.0, 0.0), handR=(11.0, 24.0, 15.0), handL=(6.0, 24.0, -15.0), lag=1.5), 80),
        (K(crouch=3.0, lean=1.5, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 70),
        (K(), 115),                                                                                      # recover = idle 0
    ]


def dodge():
    """v2 dodge (in place; the runtime moves him), 10 drawings: a crouch of anticipation, the
    dive, the low tuck, the push back up, the catch, and the settle while the mantle and beard
    catch up."""
    return [
        (K(crouch=2.5, lean=2.0, footR=(3.0, 0.0), footL=(-3.0, 0.0)), 40),
        (K(crouch=3.5, lean=3.5, footR=(3.0, 0.0), footL=(-4.0, 0.0), handR=add(REST_R, (-1, -1, 0)), handL=add(REST_L, (-1, -1, 0))), 35),
        (K(crouch=5.0, lean=6.0, footR=(6.0, 2.0), footL=(-10.0, 0.0), handR=(4.0, 22.0, 15.0), handL=(-2.0, 27.0, -14.0)), 35),
        (K(crouch=7.0, lean=8.0, footR=(9.0, 1.0), footL=(-10.0, 0.0), handR=(0.0, 24.0, 16.0), handL=(-2.0, 29.0, -14.0)), 35),
        (K(crouch=7.5, lean=8.0, footR=(9.0, 0.0), footL=(-9.0, 0.5), handR=(1.0, 23.0, 16.0), handL=(-1.5, 28.5, -14.0)), 40),
        (K(crouch=6.5, lean=6.5, footR=(8.0, 0.0), footL=(-8.0, 1.5), handR=(4.0, 22.5, 15.0), handL=(-1.0, 27.0, -14.0)), 45),
        (K(crouch=5.0, lean=5.0, footR=(6.0, 0.0), footL=(-5.0, 1.5), handR=(5.0, 23.0, 15.0), handL=(0.0, 25.0, -14.0)), 50),
        (K(crouch=3.5, lean=3.5, footR=(5.0, 0.0), footL=(-4.0, 0.0)), 55),
        (K(crouch=1.5, lean=1.5, footR=(4.0, 0.0), footL=(-3.0, 0.0)), 70),
        (K(), 90),                                                                                       # = idle 0
    ]


# --------------------------------------------------------------------------------- Briarshot
def special():
    up = (12.0, 40.0, 6.0)
    keys = [
        (K(handR=(10.0, 34.0, 11.0), bowu=(0.1, 1.0, 0.0)), 90),
        (K(handR=up, bowu=(0.0, 1.0, 0.0), bown=(0.6, 0, 0.8), handL=(6.0, 30.0, -6.0), briar=0.0, brow=1), 80),
        (K(handR=up, bowu=(0.0, 1.0, 0.0), bown=(0.6, 0, 0.8), handL=(10.0, 35.0, -2.0), briar=0.25, brow=1), 90),
        (K(handR=up, bowu=(0.0, 1.0, 0.0), bown=(0.6, 0, 0.8), handL=(10.0, 43.0, -2.0), briar=0.55, brow=1), 120),
        (K(handR=(12.0, 46.0, 6.0), bowu=(0.0, 1.0, 0.0), bown=(0.6, 0, 0.8), handL=(6.0, 50.0, -6.0), briar=1.0, lean=-0.5, brow=1), 60),  # release: the briar takes
        (K(handR=(11.0, 50.0, 7.0), bowu=(0.05, 1.0, 0.0), bown=(0.6, 0, 0.8), handL=(2.0, 36.0, -12.0), briar=1.0, lean=-0.8), 80),
        (K(handR=(11.0, 44.0, 9.0), bowu=(0.1, 1.0, 0.0), handL=(1.0, 28.0, -14.0), briar=1.0, lean=-0.3), 100),
        (K(handR=(10.0, 34.0, 12.0), bowu=(0.1, 1.0, 0.0), briar=1.0), 110),
        (K(briar=1.0), 90),
    ]
    return keys


def powered_exit():
    up = (12.0, 40.0, 6.0)
    keys = [
        (K(briar=1.0), 110),
        (K(handR=(10.0, 34.0, 11.0), briar=1.0), 100),
        (K(handR=up, bown=(0.6, 0, 0.8), handL=(10.0, 44.0, -2.0), briar=1.0), 100),
        (K(handR=up, bown=(0.6, 0, 0.8), handL=(10.0, 38.0, -2.0), briar=0.7), 90),
        (K(handR=up, bown=(0.6, 0, 0.8), handL=(10.0, 31.0, -2.0), briar=0.4), 90),
        (K(handR=up, bown=(0.6, 0, 0.8), handL=(8.0, 27.0, -6.0), briar=0.15), 100),
        (K(handR=(10.0, 34.0, 11.0), briar=0.0), 120),
        (K(), 150),
    ]
    return keys


TABLE = {
    'idle': idle(),
    'walk': walk(),
    'primary': shot(),
    'secondary': billhook(),
    'special': special(),
    'guard': guard(),
    'hit': hit(),
    'defeat': defeat(),
    'jump': jump(),
    'stair_up': stairs(True),
    'stair_down': stairs(False),
    'dodge': dodge(),
    'powered_idle': idle(1.0),
    'powered_walk': walk(1.0),
    'powered_primary': shot(1.0, fast=True),
    'powered_guard': guard(1.0),
    'powered_exit': powered_exit(),
    'fidget_string': fidget_string(),
    'fidget_beard': fidget_beard(),
    'fidget_quiver': fidget_quiver(),
}
# v2 secondary motion: the mantle, quiver and beard trail every action (anim.follow)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'defeat', 'jump', 'dodge', 'powered_primary',
           'powered_guard', 'powered_exit', 'fidget_string', 'fidget_beard', 'fidget_quiver'):
    TABLE[_c] = anim.follow(TABLE[_c])
for _c in ('stair_up', 'stair_down'):
    TABLE[_c] = anim.follow(TABLE[_c], loop=True)
# no skating: a foot that moves more than 3 px is lifted in that drawing (anim.unskate)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'dodge', 'powered_primary', 'powered_guard', 'powered_exit'):
    if _c in TABLE:
        TABLE[_c] = anim.unskate(TABLE[_c], P0)

# idle fidgets (v2): the runtime plays one after FIDGET_AFTER s of idle (CONTRACT, "Idle life")
FIDGETS = ['fidget_string', 'fidget_beard', 'fidget_quiver']
EXTRA = {c: dict(n=(10, 13), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}

# Powered variants (anim.add_powered): the Briarshot vine stays on the bow in every clip.
POWERED = dict(briar=1.0)

RELEASE = {'primary': 11, 'secondary': 7, 'special': 4, 'powered_primary': 7}
HOLDS = {'primary': [10], 'powered_primary': [6]}          # v2 polish: the anchor at full draw is held
RELEASE_ANCHOR = {'primary': 'arrow_tip', 'secondary': 'strike', 'special': 'hand_R', 'powered_primary': 'arrow_tip'}

# Equipment that must be visible (tag -> clips where it may be hidden or absent).  checks.py reads
# this.  The bow is in every drawing (hand, back or ground); the quiver and billhook always;
# the buckler is the bracer, so it is always on the forearm (it may be occluded in some facings).
EQUIP = {
    # v2: SE shows his front, so the quiver on his back is behind him; NW shows his back with the
    # bow hand on the far side, so the body hides the bow (as in W and N)
    'bow': dict(always=True, may_hide={'W', 'N', 'NW'}),
    'quiver': dict(always=True, may_hide={'S', 'SE'}, **{'except': {'defeat': [2]}}),
    # (defeat 2: falling forward onto the knee, the mantle and head cover the quiver's top in E)
    'billhook': dict(always=True, may_hide={'N', 'W', 'S', 'NW', 'SW', 'SE'}),
    'buckler': dict(clips={'guard': [3, 4], 'powered_guard': [3, 4]}, may_hide={'NW'}),
    # aimed straight away from the camera (N), the arrow is behind his head: correct, so hidden
    # from the nock (drawing 5) to the anchor (10); while it comes out of the quiver behind his head
    # (3, 4) the head hides it in the profiles, as it should
    'arrow': dict(clips={'primary': [5, 6, 7, 8, 9, 10], 'powered_primary': [3, 4, 5, 6]}, may_hide={'NW', 'N', 'NE'}),
}

WEAPON_TAG = {'primary': 'bow', 'powered_primary': 'bow'}   # the held weapon at the release (the arrow has left; checks.py)

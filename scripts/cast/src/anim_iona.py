"""Iona's animation table (Bramble template).  One spear throughout: the right hand holds it at
sps from the butt; in two-handed actions the left hand grips the same shaft at gripL, so the
grips stay on one line and the shaft keeps its 92 px and its head.

primary   spear strike: rear-leg load, two-hand thrust, contact, return.
secondary storm-lance lunge: a long low lunge straight along the facing (the runtime moves the
          body along the same direction, so the thrust lies along the actual movement), with a
          storm crackle on the blade at contact.
special   Stormcall: the spear raised upright, lightning strikes the blade, the charge settles
          into the powered state (storm 1: blue rim and sparks on the same blade).
Body space: (fwd, up, lat), lat + = her RIGHT."""
import numpy as np
import anim
from iona import REST_R, REST_L, P0

A_STRIDE = 8.5
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

UP = (0.02, 1.0, 0.0)
CARRY = dict(lift=3.0)                      # spear carried 3 px off the ground


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def two(hR, hL, *bases, sps=32.0, **k):
    """Both hands on the one shaft: the right grip at hR (sps from the butt), the left at hL;
    the spear lies along the line through them."""
    d = np.subtract(hL, hR)
    L = float(np.linalg.norm(d))
    return K(*bases, handR=hR, spu=tuple(d / L), sps=sps, gripL=sps + L, **k)


LEAD = dict(footR=(-5.0, 0.0), footL=(6.0, 0.0))          # left foot leads, right (spear) foot back


# --------------------------------------------------------------------------------- idle, walk
def idle(storm=0.0):
    """v2 idle, 12 drawings in 1.6 s: the breath, the braid and scarf half a beat behind, one blink;
    the spear rides on the breath."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    return [(K(breath=br[i], lag=lag[i], blink=(i == 10), storm=storm, fx=i,
               handR=add(REST_R, (0, 0.5 * br[i], 0)), handL=add(REST_L, (0, 0.5 * br[i], 0))), ms[i]) for i in range(12)]


def walk(storm=0.0):
    """v2 walk, 12 drawings a stride: the spear's head sways a drawing behind the hand."""
    keys = []
    n = anim.WALK_N2
    gs = anim.gait(n, A_STRIDE, 3.5, bob=1.0)
    for i, g in enumerate(gs):
        s = g['swing']
        late = gs[(i - 1) % n]['swing']
        keys.append((K(CARRY, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.5 + 0.6 * abs(s),
                       handR=add(REST_R, (-1.5 * s, 1.0, 0)), spu=(0.08 - 0.05 * late, 1.0, 0.0),
                       handL=add(REST_L, (4.0 * s, 0.6 * abs(s), 0)), storm=storm, fx=i),
                     WALK_LOOP2 * 1000 / n))
    return keys


# --------------------------------------------------------------------------------- idle fidgets (v2)
def fidget_scarf():
    """Tugs her scarf up against the wind with the free hand, then settles it."""
    S = dict(handL=(4.0, 42.0, -5.0))
    return [(K(), 150), (K(handL=(3.0, 34.0, -10.0)), 110), (K(S, brow=1), 110), (K(S, handL=(4.0, 44.0, -4.0), lag=0.6), 130),
            (K(S, handL=(4.5, 43.0, -4.5), lag=0.9, blink=True), 140), (K(handL=(3.0, 35.0, -10.0), lag=0.5), 110),
            (K(lag=0.2), 120), (K(), 170)]


def fidget_spear():
    """Lifts the spear a hand's breadth, looks up along the blade, sets the butt down again."""
    return [(K(), 150), (K(handR=add(REST_R, (0, 2.0, 0)), lift=2.0, crouch=0.4), 110),
            (K(handR=add(REST_R, (1.0, 5.0, -1.0)), lift=5.0, spu=(0.1, 1.0, -0.05), brow=1), 120),
            (K(handR=add(REST_R, (1.0, 5.0, -1.0)), lift=5.0, spu=(0.1, 1.0, -0.05), brow=2, lag=0.3), 220),     # looks along it
            (K(handR=add(REST_R, (0.5, 2.0, 0)), lift=2.0, lag=0.5), 100),
            (K(handR=add(REST_R, (0, 0.0, 0)), lift=1.0, crouch=0.6, lag=0.6), 90),                               # the butt lands
            (K(crouch=0.2, lag=0.3, blink=True), 120), (K(), 170)]


def stairs(up=True):
    keys = []
    for g in anim.gait(8, 7.0, 7.0 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(footR=fr, footL=fl, bob=g['bob'], lean=2.5 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
                       handR=add(REST_R, (-1.5 * s, 2.0, 0)), lift=9.0 if up else 4.0, spu=(0.12, 1.0, 0.0),
                       handL=add(REST_L, (3.5 * s, 0.5, 0))), 90))
    return keys


# --------------------------------------------------------------------------------- spear strike
def strike(storm=0.0, powered=False):
    HOLD = ((2.0, 33.0, 9.0), (12.0, 36.0, 1.0))
    keys = [
        (K(handR=(6.0, 33.0, 12.0), spu=(0.35, 1.0, -0.1), lift=2.0, lean=0.3), 60),                     # spear tips forward
        (two(*HOLD, footR=(-2.0, 0.0), footL=(3.0, 0.0), twist=2.0), 55),                                 # two-hand hold
        (two((-4.0, 34.0, 9.0), (6.0, 36.0, 4.5), LEAD, crouch=2.0, lean=-1.5, twist=4.0, lag=0.5), 70),   # rear-leg load
        (two((-6.0, 34.5, 9.0), (4.0, 36.5, 4.5), LEAD, crouch=2.5, lean=-2.0, twist=4.5, lag=0.8, brow=1), 80),  # held load
        (two((0.0, 35.0, 8.5), (11.0, 36.0, 4.0), LEAD, crouch=2.0, lean=0.5, twist=4.5, brow=1), 30),    # drive
        (two((5.0, 36.0, 8.0), (16.0, 36.5, 4.0), LEAD, hipx=2.0, crouch=1.5, lean=3.0, twist=5.0, lag=-1.0, brow=1, face='shout'), 35),  # contact
        (two((5.5, 36.0, 8.0), (16.5, 36.5, 4.0), LEAD, hipx=2.0, crouch=1.5, lean=3.0, twist=5.0, lag=-1.5, brow=1), 45),   # extended
        (two((2.0, 35.0, 8.5), (13.0, 36.0, 4.0), LEAD, hipx=1.0, crouch=1.5, lean=1.5, twist=4.0, lag=-0.5), 60),           # follow-through
        (two(*HOLD, footR=(-2.0, 0.0), footL=(3.0, 0.0), crouch=0.5, lean=0.5, twist=2.0), 80),          # return
        (K(handR=(6.0, 32.0, 12.0), spu=(0.3, 1.0, -0.05), lift=2.0, lean=0.2), 90),                     # one hand
        (K(), 110),                                                                                       # settle upright
    ]
    if powered:   # from the upright powered_idle: the tilt drawing first, then the hold (no 90-degree pop)
        keys = keys[0:4] + keys[5:]
    for i, (P, _) in enumerate(keys):
        P['storm'] = storm
        P['fx'] = i
    if powered:
        keys[4][0]['arc'] = 1
        keys[5][0]['arc'] = 2
    return keys


# --------------------------------------------------------------------------------- storm-lance lunge
def lunge():
    D = dict(footR=(-9.0, 0.0), footL=(10.0, 0.0))            # a long lunge stance
    HOLD = ((2.0, 33.0, 9.0), (12.0, 36.0, 1.0))
    return [
        (two(*HOLD, twist=2.0), 50),                                                                       # two-hand hold
        (two((-6.0, 33.0, 9.0), (4.0, 35.0, 4.5), LEAD, crouch=3.5, lean=-2.0, twist=4.5, lag=1.0, storm=0.3, fx=1, brow=1), 80),   # coil low
        (two((-7.0, 32.5, 9.0), (3.0, 34.5, 4.5), LEAD, crouch=4.0, lean=-2.5, twist=5.0, lag=1.2, storm=0.6, fx=2, brow=1), 80),   # held, charge builds
        (two((2.0, 32.5, 8.5), (13.0, 33.5, 4.0), D, hipx=3.0, crouch=5.0, lean=3.5, twist=5.0, wind=1.0, storm=0.8, fx=3, brow=1), 30),  # spring
        (two((8.0, 32.0, 8.0), (19.0, 32.5, 4.0), D, hipx=4.0, crouch=6.0, lean=5.5, twist=5.5, wind=2.0, storm=1.0, arc=3, fx=4, brow=1, face='shout'), 40),  # contact
        (two((8.0, 32.0, 8.0), (19.0, 32.5, 4.0), D, hipx=4.0, crouch=6.0, lean=5.5, twist=5.5, wind=1.5, storm=0.7, arc=4, fx=5, brow=1), 50),
        (two((5.0, 32.5, 8.5), (16.0, 33.5, 4.0), D, hipx=3.0, crouch=5.0, lean=4.0, twist=4.5, wind=0.5, storm=0.3, fx=6), 70),   # follow-through
        (two((2.0, 33.0, 9.0), (12.0, 35.5, 4.0), LEAD, hipx=1.5, crouch=3.0, lean=1.5, twist=3.0, lag=-0.5), 80),               # recover
        (two(*HOLD, footR=(-2.0, 0.0), footL=(3.0, 0.0), crouch=1.0, lean=0.5, twist=2.0), 90),
        (K(handR=(6.0, 32.0, 12.0), spu=(0.3, 1.0, -0.05), lift=2.0), 90),
        (K(), 110),
    ]


# --------------------------------------------------------------------------------- Stormcall (special)
def special():
    hi = (5.0, 44.0, 12.0)
    return [
        (K(handR=(5.0, 31.0, 13.0), lift=2.0, crouch=0.5), 80),
        (K(handR=(5.0, 36.0, 13.0), lift=2.0, crouch=1.5, handL=(3.0, 33.0, -11.0), brow=1), 90),               # lift, knees bend
        (K(handR=hi, sps=36.0, crouch=1.0, handL=(4.0, 40.0, -10.0), brow=1, storm=0.2, fx=1), 90),             # spear up
        (K(handR=(5.0, 47.0, 12.0), sps=38.0, crouch=0.0, handL=(3.0, 45.0, -9.0), brow=1, storm=0.5, fx=2, lag=-0.5), 120),  # high, held
        (K(handR=(5.0, 47.0, 12.0), sps=38.0, handL=(3.0, 45.0, -9.0), storm=1.0, arc=5, fx=3, face='shout', wind=1.5), 50),  # strike (release)
        (K(handR=(5.0, 46.0, 12.0), sps=38.0, handL=(2.0, 40.0, -10.0), storm=1.0, arc=6, fx=4, wind=1.0, crouch=1.0), 70),
        (K(handR=hi, sps=36.0, handL=(1.5, 32.0, -12.0), storm=1.0, fx=5, wind=0.5, crouch=1.5), 90),
        (K(handR=(5.0, 33.0, 13.0), lift=2.0, storm=1.0, fx=6, crouch=0.5), 100),
        (K(storm=1.0, fx=7), 110),
    ]


def powered_exit():
    return [
        (K(storm=1.0, fx=0), 110),
        (K(handR=(5.0, 34.0, 13.0), lift=2.0, storm=1.0, fx=1, handL=(3.0, 30.0, -11.0)), 100),
        (K(handR=(5.0, 34.0, 13.0), lift=2.0, storm=0.8, fx=2, handL=(4.0, 34.0, -9.0)), 100),
        (K(handR=(5.0, 34.0, 13.0), lift=2.0, storm=0.55, fx=3, handL=(4.0, 34.0, -9.0)), 100),
        (K(handR=(5.0, 33.0, 13.0), lift=2.0, storm=0.3, fx=4, handL=(3.0, 31.0, -11.0)), 100),
        (K(handR=(5.0, 31.0, 13.0), lift=2.0, storm=0.1, fx=5), 110),
        (K(lag=0.3), 120),
        (K(), 120),
    ]


# --------------------------------------------------------------------------------- guard
def guard(storm=0.0):
    B = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
    keys = [
        (K(handR=(6.0, 31.0, 12.0), spu=(0.15, 1.0, -0.2), lift=2.0), 55),
        (two((7.0, 30.0, 10.0), (9.0, 40.0, 2.0), sps=29.0, crouch=0.5), 55),
        (two((8.0, 29.0, 8.5), (11.0, 43.0, -3.0), B, sps=29.0, crouch=1.5), 55),
        (two((8.5, 29.0, 8.0), (11.5, 44.0, -4.0), B, sps=29.0, crouch=2.0, lean=1.0, brow=1), 55),
        (two((8.5, 29.0, 8.0), (11.5, 44.0, -4.0), B, sps=29.0, crouch=2.5, lean=1.5, brow=1), 120),     # braced (hold)
        (two((7.0, 30.0, 10.0), (9.0, 40.0, 2.0), dict(footR=B['footR']), sps=29.0, crouch=1.0), 120),   # left foot home first
        (K(handR=(6.0, 31.0, 12.0), spu=(0.15, 1.0, -0.1), lift=2.0, crouch=0.5), 120),
        (K(), 120),
    ]
    for i, (P, _) in enumerate(keys):
        P['storm'] = storm
        P['fx'] = i
    return keys


# --------------------------------------------------------------------------------- hit, defeat
def hit():
    S = dict(lift=3.0)
    return [
        (K(S, lean=-3.0, crouch=1.0, face='shut', brow=2, handR=(2.0, 31.0, 14.0), spu=(-0.25, 1.0, 0.05), handL=(-4.0, 30.0, -14.0), lag=-1.0), 35),
        (K(S, lean=-4.0, crouch=2.0, face='shut', brow=2, handR=(1.0, 32.0, 14.5), spu=(-0.3, 1.0, 0.05), handL=(-5.0, 31.0, -14.5), lag=-1.5), 65),
        (K(S, lean=-2.5, crouch=3.0, brow=2, handR=(2.0, 30.0, 14.0), spu=(-0.2, 1.0, 0.0), handL=(-3.0, 28.0, -14.0), lag=-0.5), 90),
        (K(S, lean=-1.0, crouch=2.0, brow=2, handR=(4.0, 30.0, 13.5), spu=(-0.05, 1.0, 0.0), lag=0.5), 120),
        (K(S, lean=0.5, crouch=1.0, brow=1, lag=1.0), 130),
        (K(lean=0.3, crouch=0.5, lag=0.6, lift=1.0), 150),
        (K(lag=0.2), 160),
        (K(), 180),
    ]


def defeat():
    # she sinks onto the right knee, leaning on the spear planted beside her, both hands on it
    k1 = dict(footR=(-5.0, 2.0), footL=(6.0, 0.0))
    k2 = dict(footR=(-8.0, 2.5), footL=(7.0, 0.0))
    U = (0.1, 1.0, -0.05)

    def lean_on(hR, cr, **k):
        up = hR[1] - cr                       # grip height above the ground (the crouch lowers it)
        sps = up / float(np.linalg.norm(U)) * 0.995
        return K(handR=hR, crouch=cr, spu=U, sps=sps, gripL=sps + 4.0, twist=3.0, **k)
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2, lift=1.0), 80),
        (K(lean=1.5, crouch=5.0, face='shut', brow=2, handR=(8.0, 32.0, 10.0), spu=U, sps=26.5, handL=(4.0, 27.0, -12.0)), 100),
        (lean_on((9.0, 33.0, 4.0), 9.0, **k1, lean=3.0, brow=2), 100),
        (lean_on((10.0, 34.0, 3.5), 12.0, **k2, lean=4.0, brow=2), 120),
        (lean_on((10.0, 34.0, 3.5), 13.0, **k2, lean=5.0, face='shut', brow=2, lag=0.3), 150),
        (lean_on((10.0, 34.0, 3.0), 13.5, **k2, lean=6.0, face='shut', lag=0.6), 180),
        (lean_on((10.0, 34.0, 3.0), 13.5, **k2, lean=6.5, face='shut', lag=0.8), 240),
        (lean_on((10.0, 34.0, 3.0), 13.5, **k2, lean=6.5, face='shut', lag=0.8), 300),
    ]


# --------------------------------------------------------------------------------- jump, dodge
def jump():
    T = dict(spu=(0.3, 1.0, 0.0), lift=4.0)
    return [
        (K(T, crouch=4.0, lean=2.0, handR=(5.0, 28.0, 13.5), handL=(0.0, 26.0, -13.0), lag=0.5), 80),
        (K(T, crouch=1.0, lean=1.0, footR=(1.5, 1.0), footL=(-1.5, 1.5), handR=(7.0, 36.0, 13.5), handL=(3.0, 36.0, -14.0)), 55),
        (K(T, footR=(2.0, 6.0), footL=(-1.0, 8.0), handR=(7.0, 40.0, 14.0), handL=(4.0, 41.0, -15.0), lag=-1.5), 80),
        (K(T, footR=(3.0, 8.0), footL=(0.0, 9.0), handR=(7.0, 38.0, 14.0), handL=(4.0, 39.0, -15.0), lag=-0.5), 110),
        (K(T, footR=(2.0, 3.0), footL=(-2.0, 4.0), handR=(7.0, 39.0, 14.0), handL=(2.0, 41.0, -15.0), lag=1.5), 110),
        (K(T, crouch=5.0, lean=2.5, footR=(2.0, 0.0), footL=(-2.0, 0.0), handR=(8.0, 30.0, 13.5), handL=(6.0, 24.0, -14.0), lag=1.5), 80),
        (K(T, crouch=3.0, lean=1.5, footR=(2.0, 0.0), footL=(-2.0, 0.0), handR=(6.0, 30.0, 13.5), lag=1.0), 70),
        (K(), 115),                                                                       # recover = idle 0
    ]


def dodge():
    T = dict(spu=(-0.6, 1.0, 0.0), lift=6.0)        # spear tipped back, out of the way
    return [
        (K(T, crouch=3.0, lean=3.0, footR=(2.0, 0.0), footL=(-3.0, 0.0), handR=(4.0, 30.0, 13.5)), 55),
        (K(T, crouch=5.0, lean=6.0, footR=(5.0, 2.0), footL=(-9.0, 0.0), handR=(2.0, 30.0, 14.0), handL=(0.0, 30.0, -13.0), lag=2.0), 45),
        (K(T, crouch=7.0, lean=8.0, footR=(8.0, 1.0), footL=(-9.0, 0.0), handR=(0.0, 31.0, 14.5), handL=(1.0, 31.0, -13.0), lag=3.0), 40),
        (K(T, crouch=7.5, lean=8.0, footR=(8.0, 0.0), footL=(-8.0, 0.5), handR=(1.0, 31.0, 14.5), handL=(1.5, 30.5, -13.0), lag=3.0), 45),
        (K(T, crouch=6.0, lean=6.0, footR=(6.0, 0.0), footL=(-6.0, 1.5), handR=(3.0, 30.0, 14.0), handL=(1.0, 28.0, -13.0), lag=2.0), 60),
        (K(crouch=4.0, lean=4.0, footR=(4.0, 0.0), footL=(-3.0, 0.0), spu=(-0.3, 1.0, 0.0), lift=4.0, lag=1.5), 70),
        (K(crouch=2.0, lean=2.0, footR=(3.0, 0.0), footL=(-2.0, 0.0), spu=(-0.1, 1.0, 0.0), lift=2.0, lag=1.0), 80),
        (K(), 100),                                                                       # = idle 0
    ]


TABLE = {
    'fidget_scarf': fidget_scarf(),
    'fidget_spear': fidget_spear(),
    'idle': idle(),
    'walk': walk(),
    'primary': strike(),
    'secondary': lunge(),
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
    'powered_primary': strike(1.0, powered=True),
    'powered_guard': guard(1.0),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ fix pass (audit, 25 Oct)
# no skating: a foot that moves more than 3 px is lifted in that drawing (anim.unskate)
FIDGETS = ['fidget_scarf', 'fidget_spear']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = P0()
_SH = {}
for _c, _a in {'primary': [2, 4, 7], 'secondary': [1, 3, 6], 'special': [2, 5], 'powered_primary': [2, 6], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)     # v2: arc in-betweens
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit', 'reload'):
    if _c in TABLE:
        _k = anim.unskate(TABLE[_c], P0)
        if len(_k) <= anim.CLIPS[_c]['n'][1] + 4:
            TABLE[_c] = _k

# Powered variants: the same blade keeps its storm rim and sparks.
def POWERED(P, i):
    return dict(P, storm=1.0, fx=P.get('fx', i))


RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 5, 'secondary': 4, 'special': 4, 'powered_primary': 4}.items()}
HOLDS = {'primary': [_SH['primary'](3)], 'secondary': [_SH['secondary'](2)]}       # the loads, held
ANCHOR_TAG = {'spear_tip': 'spear'}
ANCHOR_WITH = {'spear_tip': ('storm',)}      # powered, the storm rim lies on the same blade
RELEASE_ANCHOR = {'primary': 'spear_tip', 'secondary': 'spear_tip', 'special': 'spear_tip', 'powered_primary': 'spear_tip'}
EQUIP = {
    'spear': dict(always=True),
    'braid': dict(always=True, may_hide={'S', 'SE', 'SW'}),
    'harness': dict(always=True),
    'storm': dict(clips={'special': [RELEASE['special'], RELEASE['special'] + 1], 'powered_primary': [RELEASE['powered_primary']]}),
}

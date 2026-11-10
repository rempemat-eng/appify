"""Ashe's animation table (the anim_bramble.py pattern).  Poses list what differs from ashe.P0.

Logic (Codex identity table): one sword, always in the RIGHT hand; one helm.  In the normal form
the helm is carried under the left arm (helm_t 0).  Cinderhelm (special) lifts the same helm along
one path onto the head (helm_t 0 -> 1); it leaves the hand only on the head, so there is never a
second helm, and the armour's seams light (ember=1) on the same plates.  The powered clips keep
it worn; powered_exit lifts it off and back under the arm while the seams cool.  The free left
hand joins the grip in the powered attacks and guard.
"""
import anim
from ashe import REST_R, REST_DIR

A_STRIDE = 9.0
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

ST = dict(footR=(4.5, 0.0), footL=(-4.0, 0.0), stance=6.2)
PW = dict(helm_t=1.0, ember=1.0)


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


# --------------------------------------------------------------------------------- idle, walk
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride (a quicker cadence)
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)


def idle(powered=False):
    """v2 idle, 12 drawings in 1.6 s: the breath lifts the plate and the sword hand; the cape follows
    half a beat behind; one blink."""
    keys = []
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.9, 1.0, 0.9, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    base = dict(PW) if powered else {}
    for i in range(12):
        keys.append((K(base, breath=br[i], lag=lag[i], blink=(i == 10), handR=add(REST_R, (0, 0.5 * br[i], 0))), ms[i]))
    return keys


def walk(powered=False):
    """v2 walk, 12 drawings a stride: the sword swings a little with the right arm, the cape trails."""
    keys = []
    base = dict(PW) if powered else {}
    n = anim.WALK_N2
    gs = anim.gait(n, A_STRIDE, 3.5, bob=1.0)
    for i, g in enumerate(gs):
        s = g['swing']
        late = gs[(i - 1) % n]['swing']                     # the blade's tip a drawing behind the hand
        k = K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.5 + 0.8 * abs(s),
              handR=add(REST_R, (-3.0 * s, 0.6 * abs(s), 0)), sdir=(0.45 - 0.2 * late, -0.85, 0.3))
        if powered:
            k['handL'] = (1.0 + 3.5 * s, 26.5 + 0.6 * abs(s), -14.0)
        keys.append((k, WALK_LOOP2 * 1000 / n))
    return keys


# --------------------------------------------------------------------------------- idle fidgets (v2)
def fidget_edge():
    """Lifts the sword in front of her, sights along the edge, turns it once, lowers it."""
    up = dict(handR=(10.0, 40.0, 12.5), sdir=(0.35, 0.9, 0.2))
    return [(K(), 150), (K(handR=(9.0, 33.0, 13.0), sdir=(0.6, 0.0, 0.3)), 110),
            (K(up, brow=1), 120),
            (K(up, brow=1, lean=0.4), 220),                                          # sights along it
            (K(handR=(10.0, 40.5, 12.0), sdir=(0.35, 0.9, -0.1), brow=1, lean=0.4), 120),   # turns it
            (K(handR=(10.0, 40.5, 12.0), sdir=(0.35, 0.9, -0.1), brow=2), 160),
            (K(handR=(9.0, 33.0, 13.0), sdir=(0.6, -0.4, 0.3), blink=True), 110),
            (K(handR=add(REST_R, (0.5, 0.5, 0))), 120), (K(), 170)]


def fidget_helm():
    """Hitches the helm higher under her arm, settles it, rolls her shoulder."""
    return [(K(), 150), (K(crouch=0.5, helm_t=0.04), 110),
            (K(breath=1, helm_t=0.1, brow=1), 110),                                 # hitch
            (K(breath=1, helm_t=0.08), 100),
            (K(helm_t=0.02, crouch=0.4), 110),                                        # it settles
            (K(twist=0.06, lag=0.6), 130), (K(twist=-0.04, lag=0.3, blink=True), 120),
            (K(lag=0.1), 120), (K(), 170)]


def stairs(up=True):
    keys = []
    for g in anim.gait(8, 7.0, 7.0 if up else 2.5, bob=1.0):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((K(footR=fr, footL=fl, bob=g['bob'], lean=2.5 if up else -1.0, crouch=1.0 if up else 0.5, lag=1.0,
                       handR=add(REST_R, (-2.5 * s, 0.5, 0))), 90))
    return keys


# --------------------------------------------------------------------------------- sword cut
def slash(powered=False):
    """v2 (26 Oct review): a one-handed diagonal cut that stays outside her silhouette.  The sword
    draws back low (anticipation), rises behind the right shoulder to the load, swings up beside her
    head on the near side, cuts forward and down to contact, and follows through low across her
    front; the blade continues the forearm line from the fist (guard at the gauntlet) all the way."""
    b = dict(PW) if powered else {}
    keys = [
        (K(b, ST, handR=(7.0, 33.0, 12.0), sdir=(1.0, 0.3, 0.0)), 50),                                         # 0 ready, blade up
        (K(b, ST, handR=(1.0, 40.0, 13.5), sdir=(-0.6, -0.5, 0.4), crouch=0.8, lean=-0.6), 45),                # 1 draw back low
        (K(b, ST, handR=(-3.0, 43.0, 13.5), sdir=(-0.85, 0.15, 0.5), crouch=1.2, lean=-1.0, brow=1), 45),      # 2 back beside the shoulder
        (K(b, ST, handR=(-7.0, 50.0, 13.0), sdir=(-0.5, 0.75, 0.4), crouch=1.5, lean=-1.5, lag=-0.5, brow=1), 70),   # 3 load (held), behind the shoulder
        (K(b, ST, handR=(16.5, 47.0, 10.0), sdir=(0.8, 0.55, 0.2), crouch=1.5, lean=0.5, brow=1), 30),        # 4 swing, up ahead of her face
        (K(b, ST, handR=(16.0, 44.0, 8.0), sdir=(1.0, 0.25, -0.3), crouch=2.0, lean=2.5, brow=1), 25),          # 5 smear, turning across
        (K(b, ST, handR=(15.0, 38.0, 5.0), sdir=(0.62, -0.3, -0.72), crouch=2.5, lean=3.5, lag=1.0, brow=1), 35),   # 6 CONTACT: the cut crosses her front, down to her left
        (K(b, ST, handR=(12.0, 32.0, 2.0), sdir=(0.45, -0.55, -0.72), crouch=3.0, lean=3.5, lag=1.5), 45),     # 7 follow-through, across
        (K(b, ST, handR=(9.0, 29.0, 1.0), sdir=(0.3, -0.72, -0.66), crouch=2.5, lean=2.5, lag=1.5), 60),
        (K(b, ST, handR=(7.0, 28.5, 7.0), sdir=(0.4, -0.85, -0.3), crouch=1.5, lean=1.5, lag=1.0), 80),
        (K(b, handR=add(REST_R, (1.0, 0.5, 0)), crouch=0.5, lean=0.5, lag=0.5), 100),
        (K(b), 130),
    ]
    return keys


def thrust():
    L = dict(footR=(9.0, 0.0), footL=(-5.0, 0.0), stance=6.2)
    return [
        (K(ST, handR=(4.0, 32.0, 12.0), sdir=(1.0, 0.1, -0.05)), 50),                                    # blade level
        (K(ST, handR=(-2.0, 35.0, 12.5), sdir=(1.0, 0.08, -0.1), crouch=1.5, lean=-1.5, brow=1), 60),    # draw back
        (K(ST, handR=(-4.0, 36.0, 12.0), sdir=(1.0, 0.05, -0.1), crouch=2.0, lean=-2.0, brow=1), 90),    # load (held)
        (K(L, handR=(8.0, 37.0, 8.0), sdir=(1.0, 0.0, -0.08), crouch=3.0, lean=2.5, brow=1, lag=1.0), 30),
        (K(L, handR=(18.0, 38.0, 4.0), sdir=(1.0, 0.0, -0.04), crouch=4.0, lean=5.0, brow=1, lag=2.0), 40),   # RELEASE: full reach
        (K(L, handR=(17.0, 37.0, 4.5), sdir=(1.0, -0.05, -0.04), crouch=4.0, lean=4.5, lag=2.0), 70),
        (K(L, handR=(10.0, 33.0, 8.0), sdir=(1.0, -0.4, 0.0), crouch=3.0, lean=3.0, lag=1.5), 80),
        (K(ST, handR=(7.0, 30.0, 11.0), sdir=(0.8, -0.9, 0.1), crouch=1.5, lean=1.0, lag=1.0), 100),
        (K(lag=0.5), 130),
    ]


# --------------------------------------------------------------------------------- guard
def guard(powered=False):
    b = dict(PW) if powered else {}
    G = dict(handR=(9.0, 40.0, 7.0), sdir=(0.15, 1.0, -0.45))
    B = dict(footR=(4.0, 0.0), footL=(-4.0, 0.0), stance=6.5)
    return [
        (K(b, handR=(6.0, 32.0, 11.0), sdir=(0.8, 0.4, -0.1)), 55),
        (K(b, B, handR=(8.0, 36.0, 9.0), sdir=(0.5, 0.9, -0.3), crouch=1.0), 55),
        (K(b, B, G, crouch=2.0, lean=0.5, brow=1), 55),
        (K(b, B, G, crouch=2.5, lean=1.0, brow=1), 55),
        (K(b, B, G, crouch=3.0, lean=1.5, brow=1), 120),                                  # HOLD
        (K(b, B, handR=(8.0, 34.0, 9.0), sdir=(0.7, 0.4, -0.2), crouch=1.5), 120),
        (K(b, handR=add(REST_R, (1.0, 1.0, 0)), crouch=0.5), 120),
        (K(PW) if powered else K(), 120),
    ]


# --------------------------------------------------------------------------------- hit, defeat
def hit():
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2, handR=(7.0, 31.0, 15.0), sdir=(0.7, -0.6, 0.25), lag=-1.0), 35),
        (K(lean=-4.0, crouch=2.0, face='shut', brow=2, handR=(6.0, 32.0, 15.5), sdir=(0.75, -0.55, 0.25), lag=-1.5), 65),
        (K(lean=-2.5, crouch=3.0, brow=2, handR=(6.0, 29.0, 14.5), sdir=(0.7, -0.6, 0.25), lag=-0.5), 90),
        (K(lean=-1.0, crouch=2.0, brow=2, lag=0.5), 120),
        (K(lean=0.5, crouch=1.0, brow=1, lag=1.0), 130),
        (K(lean=0.3, crouch=0.5, lag=0.6), 150),
        (K(lag=0.2), 160),
        (K(), 180),
    ]


def defeat():
    k1 = dict(footR=(7.0, 0.0), footL=(-6.0, 2.0))
    k2 = dict(footR=(7.5, 0.0), footL=(-8.0, 2.5))
    lean_on = dict(handR=(9.0, 38.0, 8.0), sdir=(0.25, -1.0, 0.05))      # point grounded, both knees giving
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2), 80),
        (K(lean=2.0, crouch=5.0, face='shut', brow=2, handR=(10.0, 33.0, 10.0), sdir=(0.5, -0.8, 0.2)), 100),
        (K(k1, lean=3.0, crouch=8.0, brow=2, handR=(12.0, 35.0, 9.0), sdir=(0.5, -0.9, 0.1)), 100),
        (K(k2, lean=4.0, crouch=11.0, brow=2, **lean_on), 120),
        (K(k2, lean=5.0, crouch=12.0, brow=2, face='shut', **lean_on), 150),
        (K(k2, lean=6.0, crouch=12.5, face='shut', **lean_on), 180),
        (K(k2, lean=6.5, crouch=12.5, face='shut', lag=0.5, **lean_on), 240),
        (K(k2, lean=6.5, crouch=12.5, face='shut', lag=0.8, **lean_on), 300),
    ]


# --------------------------------------------------------------------------------- jump, dodge
def jump():
    return [
        (K(crouch=4.0, lean=2.0, handR=(3.0, 26.0, 14.0), sdir=(0.8, -0.6, 0.4), lag=0.5), 80),
        (K(crouch=1.0, lean=1.0, footR=(1.5, 1.0), footL=(-1.5, 1.5), handR=(8.0, 34.0, 15.0)), 55),
        (K(footR=(2.5, 6.0), footL=(-2.0, 8.0), handR=(9.0, 38.0, 15.5), sdir=(1.0, -0.5, 0.2), lag=-1.5), 80),
        (K(footR=(3.5, 8.0), footL=(-1.0, 9.0), handR=(9.0, 37.0, 15.5), sdir=(1.0, -0.6, 0.2), lag=-0.5), 110),
        (K(footR=(2.5, 3.0), footL=(-2.5, 4.0), handR=(8.0, 38.0, 15.0), sdir=(1.0, -0.6, 0.2), lag=1.5), 110),
        (K(crouch=5.0, lean=2.5, footR=(2.5, 0.0), footL=(-2.5, 0.0), handR=(9.0, 28.0, 14.0), sdir=(0.8, -0.6, 0.4), lag=1.5), 80),
        (K(crouch=3.0, lean=1.5, footR=(2.0, 0.0), footL=(-2.0, 0.0), lag=1.0), 70),
        (K(), 115),
    ]


def dodge():
    return [
        (K(crouch=3.0, lean=3.0, footR=(3.0, 0.0), footL=(-4.0, 0.0)), 55),
        (K(crouch=5.0, lean=6.0, footR=(6.0, 2.0), footL=(-10.0, 0.0), handR=(2.0, 26.0, 15.0), sdir=(-1.0, -0.35, 0.3), lag=2.0), 45),
        (K(crouch=7.0, lean=8.0, footR=(9.0, 1.0), footL=(-10.0, 0.0), handR=(-2.0, 27.0, 15.5), sdir=(-1.0, -0.4, 0.3), lag=3.0), 40),
        (K(crouch=7.5, lean=8.0, footR=(9.0, 0.0), footL=(-9.0, 0.5), handR=(-1.0, 27.0, 15.5), sdir=(-1.0, -0.4, 0.3), lag=3.0), 45),
        (K(crouch=6.0, lean=6.0, footR=(7.0, 0.0), footL=(-7.0, 1.5), handR=(3.0, 26.0, 15.0), sdir=(-0.3, -1.0, 0.3), lag=2.0), 60),
        (K(crouch=4.0, lean=4.0, footR=(5.0, 0.0), footL=(-4.0, 0.0), lag=1.5), 70),
        (K(crouch=2.0, lean=2.0, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.0), 80),
        (K(), 100),
    ]


# --------------------------------------------------------------------------------- Cinderhelm
def cinderhelm():
    return [
        (K(), 90),
        (K(helm_t=0.2, crouch=0.5, brow=1), 80),                              # the helm comes up from under the arm
        (K(helm_t=0.5, crouch=0.5, brow=1, lean=-0.5), 80),                    # past the shoulder
        (K(helm_t=0.8, lean=-0.8, face='shut'), 80),                           # over the head
        (K(helm_t=1.0, ember=1.0, crouch=1.5, lean=0.5, handL=(3.0, 50.0, -10.0)), 60),   # RELEASE: on; the seams light
        (K(PW, crouch=2.0, lean=0.8, handL=(4.0, 42.0, -12.0), lag=1.0), 80),
        (K(PW, crouch=1.5, lean=0.5, handL=(2.0, 32.0, -14.0), lag=1.0), 90),
        (K(PW, crouch=0.5, lag=0.5), 100),
        (K(PW), 110),
    ]


def powered_exit():
    return [
        (K(PW), 110),
        (K(PW, handL=(3.0, 44.0, -11.0)), 100),
        (K(PW, crouch=0.5, handL=(3.0, 50.0, -10.0)), 100),                   # hand at the helm's side
        (K(helm_t=0.8, ember=0.0, lean=-0.5), 100),                            # lifted off: the seams cool
        (K(helm_t=0.5, lean=-0.3), 90),
        (K(helm_t=0.2), 90),
        (K(helm_t=0.0, crouch=0.5), 120),                                      # under the arm again
        (K(), 150),
    ]


TABLE = {
    'fidget_edge': fidget_edge(),
    'fidget_helm': fidget_helm(),
    'idle': idle(),
    'walk': walk(),
    'primary': slash(),
    'secondary': thrust(),
    'special': cinderhelm(),
    'guard': guard(),
    'hit': hit(),
    'defeat': defeat(),
    'jump': jump(),
    'stair_up': stairs(True),
    'stair_down': stairs(False),
    'dodge': dodge(),
    'powered_idle': idle(True),
    'powered_walk': walk(True),
    'powered_primary': slash(True),
    'powered_guard': guard(True),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ v2: in-betweens, held keys, no skating
from ashe import P0 as _P0
_D0 = _P0()
FIDGETS = ['fidget_edge', 'fidget_helm']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_DENSE = {'primary': [1, 2, 6], 'powered_primary': [1, 2, 6], 'secondary': [1, 3], 'special': [2], 'hit': [0]}
_SH = {}
for _c, _a in _DENSE.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    _k = anim.unskate(TABLE[_c], _P0)
    if len(_k) <= anim.CLIPS[_c]['n'][1]:
        TABLE[_c] = _k
# powered variants of hit, dodge, jump, stairs and secondary (anim.add_powered)
POWERED = dict(helm_t=1.0, ember=1.0)     # Cinderhelm: helm worn, seams lit

RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 6, 'secondary': 4, 'special': 4, 'powered_primary': 6}.items()}
HOLDS = {'primary': [_SH['primary'](3)], 'powered_primary': [_SH['powered_primary'](3)], 'secondary': [_SH['secondary'](2)]}   # the load, held
RELEASE_ANCHOR = {'primary': 'sword_tip', 'secondary': 'sword_tip', 'special': 'hand_L', 'powered_primary': 'sword_tip'}

EQUIP = {
    'sword': dict(always=True, may_hide={'N', 'W', 'NE', 'NW', 'SW'}),
    'helm': dict(always=True, may_hide={'E', 'SE', 'NE'}),
}

ANCHOR_TAG = {'sword_tip': 'sword'}              # the release anchor's held item (anim.anchor_gaps, checks)


# v2 (26 Oct review): seen from behind, the diagonal cut across her front is hidden by her body and
# cape, so in N (and in the NE / NW in-betweens) the strike is a downward cut on her right side,
# beside her body: the blade is in sight at the contact and through the follow-through.
_NCUT = {6: dict(handR=(13.0, 40.0, 13.0), sdir=(0.7, -0.35, 0.62)),
         7: dict(handR=(12.0, 34.0, 13.5), sdir=(0.55, -0.6, 0.58)),
         8: dict(handR=(10.0, 30.0, 14.0), sdir=(0.4, -0.75, 0.52)),
         9: dict(handR=(8.0, 29.0, 13.5), sdir=(0.35, -0.85, 0.4))}
_NTABLE = {}


def _thrust_out(P):
    P = dict(P)
    h = P.get('handR')
    if h is not None:
        P['handR'] = (h[0] - 2.0, h[1], max(h[2], 13.5))
    d = P.get('sdir') or REST_DIR
    x, y, z = d[0], d[1], max(d[2], 0.55)
    n = (x * x + y * y + z * z) ** 0.5
    P['sdir'] = (round(x / n, 3), round(y / n, 3), round(z / n, 3))
    return P


def facing_table(clip, fc):
    if fc not in ('N', 'NE', 'NW') or clip not in ('primary', 'powered_primary', 'secondary', 'powered_secondary'):
        return TABLE[clip]
    if clip.endswith('secondary'):            # the thrust goes out past her right side, beside her body
        if clip not in _NTABLE:
            r = RELEASE[clip]
            _NTABLE[clip] = [(_thrust_out(P) if r - 1 <= i <= r + 1 else P, ms) for i, (P, ms) in enumerate(TABLE[clip])]
        return _NTABLE[clip]
    if clip not in _NTABLE:
        keys = slash(clip == 'powered_primary')
        for i, over in _NCUT.items():
            keys[i] = (K(keys[i][0], over), keys[i][1])
        dk, _ = anim.densify(keys, _DENSE[clip], base=_D0)
        _NTABLE[clip] = anim.unskate(dk, _P0) if len(anim.unskate(dk, _P0)) == len(TABLE[clip]) else dk
    return _NTABLE[clip]

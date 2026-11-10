"""Cairn's animation table (Bramble template).  Fists are the hand points (fist centres, radius
about 13); the crouch lowers them with the body, so a fist on the ground is up = 14 + crouch.

primary   fist slam: both fists rise overhead (the shoulder and lower masses load), hold,
          snap down to the ground in front, chips and a short fissure, settle.
secondary boulder throw: the right fist digs in, both fists tear one boulder from the ground,
          lift it overhead, hurl it forward (released at the release drawing; the projectile is
          the runtime's), follow through, settle.
special   Old Growth: he braces; wooden splints and root bands grow along the SAME stone limbs
          (forearms and legs) and leaves bud from the shoulder turf; the powered clips keep them,
          powered_exit withers them back.
Body space: (fwd, up, lat), lat + = his RIGHT."""
import anim
from cairn import REST_R, REST_L, P0, SCALE

A_STRIDE = 6.0
WALK_MS = 80                      # a heavier, slower stride than the humans
WALK_LOOP2 = WALK_MS * anim.WALK_N / 1000 / 1.15                    # v2: 15 % faster, same stride
WALK_SPEED = round(4 * A_STRIDE * SCALE / WALK_LOOP2, 1)            # drawn at SCALE
STAIR_SPEED = round(4 * 5.5 * SCALE / anim.STAIR_LOOP, 1)


def K(*bases, **k):
    out = {}
    for b in bases:
        out.update(b)
    out.update(k)
    return out


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def fists(c, half, *bases, **k):
    """Both fists at c, half apart sideways (around a held boulder or meeting overhead)."""
    return K(*bases, handR=add(c, (0, 0, half)), handL=add(c, (0, 0, -half)), **k)


# --------------------------------------------------------------------------------- idle, walk
def idle(growth=0.0):
    """v2 idle, 12 drawings in 1.6 s: a slow, heavy breath lifts the shoulder stones and the fists
    a drawing later; the pebbles circle once; one blink."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    fh = [0, 0, 0, 0, 0.5, 1, 1, 1, 0.5, 0, 0, 0]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    return [(dict(breath=br[i] / SCALE, pebbles=i / 12, blink=(i == 10), growth=growth,
                  handR=add(REST_R, (0, 0.6 * fh[i], 0)), handL=add(REST_L, (0, 0.6 * fh[i], 0))), ms[i]) for i in range(12)]


def walk(growth=0.0):
    """v2 walk, 12 drawings a stride: a heavy stomp; the fists swing against the legs a little late."""
    n = anim.WALK_N2
    keys = []
    for i, g in enumerate(anim.gait(n, A_STRIDE, 3.0, bob=1.0)):     # v2: a lower lift keeps a foot down in the turned drawings
        s = g['swing']
        keys.append((dict(footR=g['footR'], footL=g['footL'], bob=g['bob'], pebbles=i / n, growth=growth,
                          handR=add(REST_R, (-2.5 * s, 0.5 * abs(s), 0)), handL=add(REST_L, (2.5 * s, 0.5 * abs(s), 0))),
                     WALK_LOOP2 * 1000 / n))
    return keys


def fidget_knuckles():
    """Brings the two great fists together before his belly and knocks them, twice, then lets them hang."""
    M = (17.0, 33.0, 0.0)
    return [(K(), 150), (K(crouch=0.5, handR=(18.0, 28.0, 18.0), handL=(10.0, 28.0, -18.0)), 120),
            (fists(M, 15.0, crouch=0.5, lean=5.0), 120), (fists(M, 11.0, crouch=1.0, lean=5.5, blink=True), 70),   # knock
            (fists(M, 13.5, crouch=0.5, lean=5.0), 90), (fists(M, 11.0, crouch=1.0, lean=5.5, blink=True), 70),      # knock
            (fists(M, 14.5, lean=5.0), 140), (K(handR=(19.0, 26.0, 22.0), handL=(-1.0, 26.0, -22.0)), 130), (K(), 170)]


def fidget_pebbles():
    """Raises his right fist beside the shoulder and nudges the circling pebbles back into orbit."""
    return [(K(pebbles=0.0), 150), (K(handR=(16.0, 40.0, 26.0), lean=4.0, pebbles=0.1), 130),
            (K(handR=(10.0, 60.0, 27.0), lean=3.0, pebbles=0.2), 140), (K(handR=(8.0, 66.0, 26.0), lean=2.5, pebbles=0.45), 120),   # nudge
            (K(handR=(8.0, 65.0, 26.5), lean=2.5, pebbles=0.75, blink=True), 140), (K(handR=(12.0, 50.0, 26.0), lean=3.5, pebbles=0.9), 130),
            (K(handR=(18.0, 30.0, 25.0), pebbles=1.0), 130), (K(pebbles=0.0), 170)]


def stairs(up=True):
    keys = []
    for i, g in enumerate(anim.gait(8, 5.5, 7.0 if up else 2.5, bob=1.0)):
        s = g['swing']
        fr, fl = g['footR'], g['footL']
        if not up:
            fr = (fr[0], fr[1] - (2.5 if fr[0] > 2 and fr[1] < 0.5 else 0))
            fl = (fl[0], fl[1] - (2.5 if fl[0] > 2 and fl[1] < 0.5 else 0))
        keys.append((dict(footR=fr, footL=fl, bob=g['bob'], lean=6.0 if up else 3.0, crouch=1.0, pebbles=i / 8,
                          handR=add(REST_R, (-2.0 * s, 1.0, 0)), handL=add(REST_L, (2.0 * s, 1.0, 0))), 130))
    return keys


# --------------------------------------------------------------------------------- fist slam
def slam(growth=0.0, short=False):
    ST = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
    keys = [
        (K(ST, crouch=1.5, handR=(12.0, 31.5, 22.0), handL=(4.0, 31.5, -22.0)), 90),                       # gather
        (fists((8.0, 50.0, 0.0), 18.0, lean=2.0), 110),                                                     # raise
        (fists((4.0, 74.0, 0.0), 12.0, lean=-1.0), 120),                                                    # overhead
        (fists((2.0, 78.0, 0.0), 10.0, lean=-2.0, brow=1), 140),                                            # loaded (hold)
        (fists((6.0, 78.0, 0.0), 10.0, crouch=2.0, lean=-1.0), 60),                                         # anticipation
        (fists((16.0, 50.0, 0.0), 10.0, crouch=5.0, lean=6.0), 40),                                         # snap down
        (fists((13.0, 23.5, 0.0), 11.0, crouch=9.5, lean=9.0, chips=0.0, crack=1.0), 50),                   # contact (release)
        (fists((13.0, 23.5, 0.0), 11.0, crouch=9.5, lean=9.0, chips=0.6, crack=1.0), 80),                   # impact
        (fists((13.0, 23.0, 0.0), 12.0, crouch=7.0, lean=8.0, chips=1.0, crack=0.7), 90),
        (K(handR=(14.0, 28.0, 20.0), handL=(6.0, 28.0, -20.0), crouch=3.0, lean=6.0), 110),                  # rise
        (K(handR=(17.0, 26.0, 24.0), handL=(-3.0, 26.0, -24.0), crouch=1.0), 130),                           # settle
        (K(), 150),
    ]
    for P in (p for p, _ in keys):
        P.setdefault('footR', ST['footR'])
        P.setdefault('footL', ST['footL'])
    if short:     # powered: the same slam, fewer drawings
        keys = [keys[0], keys[2], keys[3], keys[5], keys[6], keys[7], keys[9], keys[11]]
    for i, (P, _) in enumerate(keys):
        P['growth'] = growth
        P['pebbles'] = i / len(keys)
    return keys


# --------------------------------------------------------------------------------- boulder throw
def throw():
    ST = dict(footR=(-5.0, 0.0), footL=(6.0, 0.0))
    keys = [
        (K(ST, crouch=3.0, handR=(14.0, 26.0, 24.0), handL=(2.0, 28.0, -22.0), lean=6.0), 100),            # reach down
        (K(ST, crouch=6.0, handR=(11.0, 20.0, 22.0), handL=(4.0, 30.0, -22.0), lean=8.0, chips=0.3, crack=0.6), 110),  # dig in
        (fists((16.0, 34.0, 0.0), 13.0, ST, crouch=5.0, lean=7.0, rock=(16.0, 34.0, 0.0), chips=0.8, crack=0.6), 100),  # tear it free
        (fists((12.0, 52.0, 0.0), 13.0, ST, crouch=1.5, lean=3.0, rock=(12.0, 52.0, 0.0)), 100),            # to the chest
        (fists((6.0, 82.0, 0.0), 13.0, ST, lean=-3.0, rock=(6.0, 82.0, 0.0), brow=1), 140),                 # overhead, ahead of the head (hold)
        (fists((3.0, 84.0, 0.0), 13.0, ST, crouch=1.0, lean=-4.0, rock=(3.0, 84.0, 0.0), brow=1), 60),      # anticipation
        (fists((20.0, 68.0, 0.0), 13.0, ST, crouch=2.0, lean=6.0, rock=(20.0, 68.0, 0.0)), 30),             # hurl: the rock at the release point
        (fists((25.0, 56.0, 0.0), 10.0, ST, crouch=2.5, lean=8.0), 30),                                      # release: hands open, the rock has left
        (fists((24.0, 40.0, 0.0), 11.0, ST, crouch=3.0, lean=9.0), 70),                                      # follow-through
        (K(ST, handR=(20.0, 30.0, 22.0), handL=(8.0, 30.0, -22.0), crouch=2.0, lean=7.0), 110),
        (K(handR=(18.0, 25.0, 24.0), handL=(-3.0, 25.0, -24.0), crouch=0.5), 130),
        (K(), 150),
    ]
    for i, (P, _) in enumerate(keys):
        P['pebbles'] = i / len(keys)
    return keys


# --------------------------------------------------------------------------------- Old Growth
def special():
    B = dict(footR=(-4.0, 0.0), footL=(4.0, 0.0))
    return [
        (K(B, crouch=1.5, handR=(14.0, 40.0, 14.0), handL=(12.0, 40.0, -14.0)), 90),
        (fists((16.0, 46.0, 0.0), 9.0, B, crouch=2.0, lean=2.0, brow=1), 80),                              # fists meet
        (K(B, crouch=4.0, handR=(10.0, 24.0, 27.0), handL=(6.0, 24.0, -27.0), lean=1.0, growth=0.25), 100),  # brace down
        (K(B, crouch=4.5, handR=(10.0, 24.5, 28.0), handL=(6.0, 24.5, -28.0), lean=-1.0, growth=0.55, crack=0.5), 110),
        (K(B, crouch=3.5, handR=(12.0, 25.0, 28.0), handL=(6.0, 25.0, -28.0), lean=-2.0, growth=1.0, crack=0.8, chips=0.3), 60),  # rooted (release)
        (K(B, crouch=3.0, handR=(14.0, 25.0, 27.0), handL=(2.0, 25.0, -27.0), growth=1.0, chips=0.8), 90),
        (K(crouch=1.5, handR=(17.0, 25.0, 26.0), handL=(-3.0, 25.0, -26.0), growth=1.0), 110),
        (K(growth=1.0), 140),
    ]


def powered_exit():
    return [
        (K(growth=1.0), 110),
        (K(growth=1.0, crouch=1.0, handR=(16.0, 30.0, 25.0), handL=(-2.0, 30.0, -25.0)), 100),
        (K(growth=0.8, crouch=1.5, handR=(16.0, 32.0, 24.0), handL=(-2.0, 32.0, -24.0)), 100),
        (K(growth=0.55, crouch=1.5, handR=(16.0, 31.0, 24.0), handL=(-2.0, 31.0, -24.0)), 100),
        (K(growth=0.3, crouch=1.0), 110),
        (K(growth=0.1, crouch=0.5), 110),
        (K(lean=4.0), 110),
        (K(), 120),
    ]


# --------------------------------------------------------------------------------- guard
def guard(growth=0.0):
    B = dict(footR=(-4.0, 0.0), footL=(4.0, 0.0))
    up_r, up_l = (18.0, 62.0, -3.0), (17.0, 55.0, 4.0)             # fists crossed before the head
    keys = [
        (K(B, crouch=1.0, handR=(16.0, 36.0, 20.0), handL=(8.0, 36.0, -20.0)), 55),
        (K(B, crouch=2.0, handR=(17.0, 48.0, 10.0), handL=(14.0, 46.0, -10.0)), 55),
        (K(B, crouch=3.0, handR=up_r, handL=up_l, lean=6.0), 55),
        (K(B, crouch=3.5, handR=up_r, handL=up_l, lean=7.0, brow=1), 55),
        (K(B, crouch=4.0, handR=up_r, handL=up_l, lean=7.5, brow=1), 120),        # braced (hold)
        (K(crouch=2.5, handR=(17.0, 46.0, 10.0), handL=(14.0, 44.0, -10.0), footR=B['footR']), 120),   # left foot home first
        (K(crouch=1.0, handR=(18.0, 30.0, 22.0), handL=(-2.0, 30.0, -22.0)), 120),
        (K(), 120),
    ]
    for P, _ in keys:
        P['growth'] = growth
    return keys


# --------------------------------------------------------------------------------- hit, defeat
def hit():
    return [
        (K(lean=0.0, crouch=1.0, blink=True, handR=(16.0, 27.0, 28.0), handL=(-8.0, 27.0, -28.0)), 40),
        (K(lean=-1.0, crouch=2.0, blink=True, handR=(15.0, 28.0, 29.0), handL=(-9.0, 28.0, -29.0)), 70),
        (K(lean=0.5, crouch=3.0, handR=(16.0, 27.0, 27.0), handL=(-7.0, 27.0, -27.0)), 90),
        (K(lean=2.5, crouch=2.0), 110),
        (K(lean=4.0, crouch=1.0), 120),
        (K(lean=5.0, crouch=0.5), 130),
        (K(lean=4.5), 140),
        (K(), 160),
    ]


def defeat():
    k = dict(footR=(-6.0, 2.0), footL=(5.0, 0.0))
    return [
        (K(lean=1.0, crouch=1.0, blink=True), 80),
        (K(lean=6.0, crouch=5.0, handR=(15.0, 22.0, 24.0), handL=(8.0, 22.0, -24.0)), 100),
        (K(k, lean=9.0, crouch=10.0, handR=(15.0, 24.0, 22.0), handL=(11.0, 24.0, -22.0)), 110),
        (K(k, lean=11.0, crouch=13.0, blink=True, handR=(15.0, 27.0, 21.0), handL=(12.0, 27.0, -21.0)), 130),   # fists to the ground
        (K(k, lean=12.0, crouch=14.0, blink=True, handR=(15.0, 27.5, 21.0), handL=(12.0, 27.5, -21.0), pebbles=0.25), 160),
        (K(k, lean=12.5, crouch=14.5, blink=True, handR=(15.0, 28.0, 21.0), handL=(12.0, 28.0, -21.0), pebbles=0.5), 200),
        (K(k, lean=12.5, crouch=14.5, blink=True, handR=(15.0, 28.0, 21.0), handL=(12.0, 28.0, -21.0), pebbles=0.5), 260),
        (K(k, lean=12.5, crouch=14.5, blink=True, handR=(15.0, 28.0, 21.0), handL=(12.0, 28.0, -21.0), pebbles=0.5), 300),
    ]


# --------------------------------------------------------------------------------- jump, dodge
def jump():
    return [
        (K(crouch=5.0, lean=7.0, handR=(14.0, 30.0, 25.0), handL=(-4.0, 30.0, -25.0)), 90),
        (K(crouch=1.0, lean=5.0, footR=(1.0, 1.0), footL=(-1.0, 1.5), handR=(18.0, 34.0, 26.0), handL=(4.0, 34.0, -26.0)), 60),
        (K(footR=(2.0, 5.0), footL=(0.0, 6.0), handR=(18.0, 40.0, 27.0), handL=(6.0, 40.0, -27.0)), 80),
        (K(footR=(2.5, 6.0), footL=(0.5, 7.0), handR=(18.0, 42.0, 27.0), handL=(6.0, 42.0, -27.0)), 110),
        (K(footR=(1.5, 2.0), footL=(-0.5, 3.0), handR=(18.0, 36.0, 27.0), handL=(4.0, 36.0, -27.0)), 110),
        (K(crouch=6.0, lean=8.0, footR=(1.0, 0.0), footL=(-1.0, 0.0), handR=(18.0, 28.0, 27.0), handL=(2.0, 28.0, -27.0), chips=0.2), 80),
        (K(crouch=3.5, lean=6.0, footR=(1.0, 0.0), footL=(-1.0, 0.0), chips=0.6), 80),
        (K(), 110),                                                                       # recover = idle 0
    ]


def dodge():
    return [
        (K(crouch=3.0, lean=7.0, footR=(2.0, 0.0), footL=(-3.0, 0.0)), 60),
        (K(crouch=5.0, lean=9.0, footR=(4.0, 1.5), footL=(-6.0, 0.0), handR=(14.0, 26.0, 27.0), handL=(-6.0, 28.0, -26.0)), 50),
        (K(crouch=6.5, lean=10.0, footR=(6.0, 1.0), footL=(-6.0, 0.0), handR=(12.0, 27.0, 28.0), handL=(-8.0, 29.0, -27.0)), 45),
        (K(crouch=7.0, lean=10.0, footR=(6.0, 0.0), footL=(-6.0, 0.5), handR=(12.0, 27.0, 28.0), handL=(-8.0, 29.0, -27.0)), 50),
        (K(crouch=5.5, lean=8.0, footR=(4.5, 0.0), footL=(-4.5, 1.0), handR=(15.0, 26.0, 27.0), handL=(-6.0, 27.0, -26.0)), 60),
        (K(crouch=3.5, lean=6.5, footR=(3.0, 0.0), footL=(-2.5, 0.0)), 70),
        (K(crouch=1.5, lean=5.0, footR=(2.0, 0.0), footL=(-1.5, 0.0)), 80),
        (K(), 100),                                                                       # = idle 0
    ]


TABLE = {
    'fidget_knuckles': fidget_knuckles(),
    'fidget_pebbles': fidget_pebbles(),
    'idle': idle(),
    'walk': walk(),
    'primary': slam(),
    'secondary': throw(),
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
    'powered_primary': slam(1.0, short=True),
    'powered_guard': guard(1.0),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ fix pass (audit, 25 Oct)
# no skating: a foot that moves more than 3 px is lifted in that drawing (anim.unskate)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit', 'reload'):
    if _c in TABLE:
        TABLE[_c] = anim.unskate(TABLE[_c], P0)

# Powered variants: the Old Growth splints stay on the same limbs.
POWERED = dict(growth=1.0)

# ------------------------------------------------------------------ golem hands (26 Oct): open at rest, a fist to strike
_OPEN = 0.15
_GRIP = {'idle': _OPEN, 'powered_idle': _OPEN, 'fidget_pebbles': _OPEN, 'walk': 0.3, 'powered_walk': 0.3, 'stair_up': 0.3,
         'stair_down': 0.3, 'primary': 1.0, 'powered_primary': 1.0, 'guard': 1.0, 'powered_guard': 1.0, 'fidget_knuckles': 1.0,
         'secondary': 0.6, 'special': 0.1, 'powered_exit': 0.2, 'hit': 0.4, 'defeat': 0.2, 'jump': 0.5, 'dodge': 0.5}
for _c, _g in _GRIP.items():
    _k = TABLE[_c]
    for _i, (_P, _ms) in enumerate(_k):
        g = _g
        if _c in ('primary', 'powered_primary', 'guard', 'powered_guard', 'fidget_knuckles', 'secondary', 'hit', 'jump', 'dodge', 'defeat',
                  'special', 'powered_exit') and _i in (0, len(_k) - 1) and _c not in ('defeat',):
            g = 0.5 * (g + _OPEN) if _i == 0 else _OPEN          # out of and back into the idle's open hands
        if _c == 'fidget_knuckles' and _i in (0, len(_k) - 1):
            g = _OPEN
        _P.setdefault('gripR', g)
        _P.setdefault('gripL', g)
# the slam's contact (26 Oct, big-block hands): the fists come 1 px lower than the round fists'
# keys, so the knuckle blocks meet the ground (2 px over the ground row in E and W, on it in S,
# with the fissure and chips under them)
for _c in ('primary', 'powered_primary'):
    for _P, _ms in TABLE[_c]:
        if _P.get('crack') and _P.get('handR') and _P['handR'][1] < 26:
            _P['handR'] = (_P['handR'][0], _P['handR'][1] - 1.0, _P['handR'][2])
            _P['handL'] = (_P['handL'][0], _P['handL'][1] - 1.0, _P['handL'][2])

# the defeat's fists rest on the ground: the angular hands are longer than the round fists were
for _P, _ms in TABLE['defeat']:
    if _P.get('handR') and _P['handR'][1] < 30 and _P.get('crouch', 0) > 8:
        _P['handR'] = (_P['handR'][0], _P['handR'][1] + 3.5, _P['handR'][2])
        _P['handL'] = (_P['handL'][0], _P['handL'][1] + 3.5, _P['handL'][2])

# ------------------------------------------------------------------ v2: fidgets, in-betweens, held keys
FIDGETS = ['fidget_knuckles', 'fidget_pebbles']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = P0()
_SH = {}
for _c, _a in {'primary': [1, 4], 'secondary': [3, 5], 'special': [1], 'powered_primary': [2], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # arc in-betweens on the big moves
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 6, 'secondary': 7, 'special': 4, 'powered_primary': 4}.items()}
HOLDS = {'primary': [_SH['primary'](3)], 'secondary': [_SH['secondary'](4)], 'powered_primary': [_SH['powered_primary'](2)]}
RELEASE_ANCHOR = {'primary': 'fist_R', 'secondary': 'rock', 'special': 'fist_R', 'powered_primary': 'fist_R'}
EQUIP = {
    'fist': dict(always=True),
    'pebbles': dict(always=True),
    'rock': dict(clips={'secondary': [2, 3, 4, 5, 6]}, may_hide={'N'}),   # and never on the release drawing (7)   # held before him: the body hides it from behind
    'growth': dict(clips={'special': [4, 5, 6, 7], 'powered_idle': list(range(8)), 'powered_exit': [0, 1]}),
}

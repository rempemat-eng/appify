"""Mote's animation table.  A pose names only what differs from mote.P0.

Primary (glass): a glass shard forms in the right hand (glass 0..1) and leaves it at the
release; the projectile is the runtime's.  Secondary (gravity): both hands lift, then press
the field forward and down while the core pulses (glow).  Special (Aphelion): the hands part
the coat fronts and the SAME chest core is exposed and lit (aphelion = 1), held through every
powered clip and closed again by powered_exit.  The three orbiting shards of the powered state
are separate effect sprites (out/mote/fx/shard_<n>.png), never body parts.  The hem fragments
lag behind motion (lag) but stay attached."""
import numpy as np
import anim
from anim_nix import K, add, idle, walk, stairs, hit, defeat, jump, dodge, HR_HIT, HL_HIT, JR, JL, DR, DL
from mote import REST_R, REST_L, SHW

A_STRIDE = 8.0
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)
PW = dict(aphelion=1.0)


def idle2(base, RR=REST_R, RL=REST_L):
    """v2 idle, 12 drawings in 1.6 s: a slow breath, the hem fragments half a beat behind, the core's
    light swells once, one blink."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    gl = [0.0, 0.0, 0.1, 0.2, 0.3, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    return [(K(base, breath=br[i], lag=lag[i], glow=gl[i], blink=(i == 10), handR=add(RR, (0, 0.5 * br[i], 0)),
               handL=add(RL, (0, 0.5 * br[i], 0))), ms[i]) for i in range(12)]


def walk2(base, RR=REST_R, RL=REST_L):
    """v2 walk, 12 drawings a stride: a gliding walk, the hem trailing."""
    n = anim.WALK_N2
    keys = []
    for g in anim.gait(n, A_STRIDE, 3.0, bob=1.0):
        s = g['swing']
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=0.5, lag=1.5 + 0.6 * abs(s),
                       handR=add(RR, (-2.0 * s, 0.5, 0)), handL=add(RL, (2.0 * s, 0.6 * abs(s), 0))), WALK_LOOP2 * 1000 / n))
    return keys


def fidget_core():
    """Lays two fingers on the chest core; its light answers, then fades."""
    T = dict(handR=(5.0, 41.0, 2.0), poleR=(-0.6, -1.0, 0.5))
    return [(K(), 150), (K(handR=(4.0, 36.0, 7.0)), 110), (K(T, glow=0.2), 110), (K(T, glow=0.7, face='shut'), 160),
            (K(T, glow=1.0, face='shut'), 150), (K(T, glow=0.5), 120), (K(handR=(4.0, 35.0, 8.0), glow=0.2, blink=True), 120),
            (K(), 170)]


def fidget_hooks():
    """Rolls the shoulders back so the gold hooks lift, then settles; the hem sways."""
    return [(K(), 150), (K(lean=-0.6, breath=1, lag=0.4), 130), (K(lean=-1.0, breath=1, lag=0.7, face='shut'), 160),
            (K(lean=0.3, crouch=0.6, lag=1.0), 140), (K(lean=0.5, crouch=0.4, lag=0.8), 120), (K(lag=0.4, blink=True), 120),
            (K(lag=0.1), 110), (K(), 170)]


def glass(base, fast=False):
    keys = [
        (K(base, handR=(3.0, 35.0, 10.5), glass=0.2, lag=0.2), 80),                                   # the hand turns up
        (K(base, handR=(2.0, 41.0, 10.0), glass=0.5, lean=-0.3, lag=0.4), 70),                         # shard gathers
        (K(base, handR=(-1.0, 44.0, 12.0), glass=0.8, lean=-0.6, poleR=(-0.6, -1.0, 0.4), lag=0.6), 60),  # lifts
        (K(base, handR=(-7.5, 45.0, 12.0), glass=1.0, lean=-0.9, poleR=(-0.6, -1.0, 0.4), lag=0.8), 70),  # load (hold)
        (K(base, handR=(-8.0, 45.5, 12.0), glass=1.0, lean=-1.0, poleR=(-0.6, -1.0, 0.4), lag=0.8), 40),
        (K(base, handR=(8.0, 45.0, 6.0), glass=1.0, lean=0.8, footR=(3.0, 0.0), lag=0.0), 35),          # flick
        (K(base, handR=(14.0, 40.0, 4.0), glass=0.0, lean=1.5, footR=(3.0, 0.0), lag=-1.0), 40),        # release
        (K(base, handR=(13.0, 37.0, 5.0), lean=1.2, footR=(3.0, 0.0), lag=-1.2), 60),                    # follow-through
        (K(base, handR=(9.0, 34.0, 8.0), lean=0.6, footR=(2.5, 0.0), lag=-0.6), 80),
        (K(base, handR=(4.0, 32.0, 10.5), lean=0.2, lag=0.0), 90),
        (K(base, lag=0.2), 120),
    ]
    if fast:
        keys = [keys[1], keys[3], keys[5], keys[6], keys[7], keys[8], keys[9], keys[10]]
    return keys


def gravity():
    up = dict(handR=(7.0, 49.0, 7.5), handL=(7.0, 49.0, -7.5), poleR=(-0.5, -1.0, 0.6), poleL=(-0.5, -1.0, -0.6))
    return [
        (K(handR=(4.0, 36.0, 10.0), handL=(4.0, 36.0, -10.0), lag=0.2), 80),
        (K(up, lean=-0.5, glow=0.3, lag=0.5), 80),                                                       # palms up
        (K(up, handR=(6.0, 51.0, 8.0), handL=(6.0, 51.0, -8.0), lean=-0.8, glow=0.7, lag=0.8), 90),       # gather (hold)
        (K(up, handR=(6.0, 52.0, 8.0), handL=(6.0, 52.0, -8.0), lean=-0.9, glow=1.0, lag=0.8), 40),
        (K(handR=(13.0, 33.0, 7.0), handL=(13.0, 33.0, -7.0), lean=1.5, crouch=2.0, glow=1.0, lag=-1.0), 40),   # press: release
        (K(handR=(11.0, 31.0, 8.0), handL=(11.0, 31.0, -8.0), lean=1.4, crouch=2.5, glow=0.6, lag=-1.2), 70),
        (K(handR=(8.0, 31.0, 9.5), handL=(8.0, 31.0, -9.5), lean=0.8, crouch=1.5, lag=-0.5), 90),
        (K(handR=(3.0, 31.5, 11.0), handL=(3.0, 31.5, -11.0), lean=0.2, crouch=0.5, lag=0.1), 100),
        (K(lag=0.2), 110),
    ]


def aphelion():
    part = dict(handR=(5.0, 42.0, 5.5), handL=(5.0, 42.0, -5.5))           # hands at the coat fronts
    wide = dict(handR=(4.0, 40.0, 14.0), handL=(4.0, 40.0, -14.0))
    return [
        (K(handR=(3.0, 35.0, 10.0), handL=(3.0, 35.0, -10.0)), 90),
        (K(part, lean=-0.3, lag=0.3), 90),
        (K(part, lean=-0.5, aphelion=0.25, glow=0.5, lag=0.5), 100),
        (K(part, handR=(5.0, 41.0, 8.0), handL=(5.0, 41.0, -8.0), lean=-0.6, aphelion=0.5, glow=0.8, lag=0.7), 90),
        (K(wide, lean=-1.0, aphelion=1.0, glow=1.0, lag=1.2), 60),                                          # release: core open
        (K(wide, handR=(3.0, 38.0, 14.5), handL=(3.0, 38.0, -14.5), lean=-0.6, aphelion=1.0, lag=0.6), 90),
        (K(handR=(2.0, 34.0, 12.5), handL=(2.0, 34.0, -12.5), aphelion=1.0, lag=0.2), 100),
        (K(PW, lag=0.1), 100),
        (K(PW), 100),
    ]


def guard(base):
    cross = dict(handR=(7.0, 49.0, 5.0), handL=(7.0, 49.0, -5.0), poleR=(-0.4, -1.0, 0.7), poleL=(-0.4, -1.0, -0.7))
    return [
        (K(base, handR=(4.0, 35.0, 10.0), handL=(4.0, 35.0, -10.0), lag=0.2), 55),
        (K(base, handR=(6.0, 39.0, 6.0), handL=(6.0, 39.0, -6.0), crouch=0.5, lag=0.4), 55),
        (K(base, cross, handR=(7.0, 46.0, 7.0), handL=(7.0, 46.0, -7.0), crouch=1.0, lean=0.5, glow=0.4, lag=0.6), 55),
        (K(base, cross, crouch=1.5, lean=0.8, glow=0.8, lag=0.8), 55),
        (K(base, cross, crouch=2.0, lean=1.0, glow=1.0, lag=0.6), 120),                                    # braced (hold)
        (K(base, handR=(5.0, 37.0, 7.0), handL=(5.0, 37.0, -7.0), crouch=1.0, lean=0.4, lag=0.0), 120),
        (K(base, handR=(2.0, 33.0, 11.0), handL=(2.0, 33.0, -11.0), crouch=0.3, lag=0.2), 120),
        (K(base), 120),
    ]


def powered_exit():
    wide = dict(handR=(4.0, 40.0, 14.0), handL=(4.0, 40.0, -14.0))
    part = dict(handR=(5.0, 42.0, 5.5), handL=(5.0, 42.0, -5.5))
    return [
        (K(PW), 110),
        (K(PW, wide, lag=0.4), 100),
        (K(wide, aphelion=0.7, lag=0.6), 100),
        (K(part, handR=(5.0, 41.0, 8.0), handL=(5.0, 41.0, -8.0), aphelion=0.4, lag=0.6), 100),
        (K(part, aphelion=0.0, lag=0.4), 100),
        (K(handR=(3.0, 35.0, 10.0), handL=(3.0, 35.0, -10.0), lag=0.2), 110),
        (K(lag=0.1), 120),
        (K(), 140),
    ]


B0 = dict()
TABLE = {
    'fidget_core': fidget_core(),
    'fidget_hooks': fidget_hooks(),
    'idle': idle2(B0),
    'walk': walk2(B0),
    'primary': glass(B0),
    'secondary': gravity(),
    'special': aphelion(),
    'guard': guard(B0),
    'hit': hit(B0, hR=[(x - 1, y + 1, z - 1.5) for x, y, z in HR_HIT], hL=[(x, y + 1, z + 1.5) for x, y, z in HL_HIT]),
    'defeat': defeat(B0, w=10.5, dy=3.0),
    'jump': jump(B0, hR=[(x, y + 2, z - 1) for x, y, z in JR], hL=[(x, y + 2, z + 1) for x, y, z in JL]),
    'stair_up': stairs(B0, REST_R, REST_L, True),
    'stair_down': stairs(B0, REST_R, REST_L, False),
    'dodge': dodge(B0, hR=[(x, y + 2, z - 1) for x, y, z in DR], hL=[(x, y + 2, z + 1) for x, y, z in DL]),
    'powered_idle': idle2(PW),
    'powered_walk': walk2(PW),
    'powered_primary': glass(PW, fast=True),
    'powered_guard': guard(PW),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ fix pass (audit, 25 Oct)
for _c in ('primary', 'secondary', 'special', 'guard', 'hit', 'powered_primary', 'powered_guard', 'powered_exit'):
    if _c == 'secondary' and 'mote' == 'rook':
        continue                                   # the vault leaves the ground: its feet are runtime-driven
    TABLE[_c] = anim.unskate(TABLE[_c], __import__('mote').P0)
POWERED = dict(aphelion=1.0)                  # the exposed core stays open in every powered clip

FIDGETS = ['fidget_core', 'fidget_hooks']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = __import__('mote').P0()
_SH = {}
for _c, _a in {'primary': [2, 5, 7], 'secondary': [1, 4], 'special': [1, 3], 'powered_primary': [1, 4], 'hit': [0]}.items():
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # v2: arc in-betweens
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 6, 'secondary': 4, 'special': 4, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](3)], 'secondary': [_SH['secondary'](2)]}     # the loads, held

# v2 aim within the facing (CONTRACT V2.8): the throwing arm swings about its shoulder onto the aim
# from the flick on; the drawings either side turn half way.
AIM_CLIPS = ('primary', 'powered_primary')


def _rot(a, b):
    a, b = np.array(a, float) / np.linalg.norm(a), np.array(b, float) / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a.dot(b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def aim_table(clip, fc, deg):
    M = _rot((1.0, 0.0, 0.0), anim.aim_body(fc, deg))
    keys = TABLE[clip]
    aimed = [bool(P.get('handR')) and P['handR'][0] >= 8.0 and P['handR'][1] >= 36.0 for P, _ in keys]
    out = []
    for i, (P, ms) in enumerate(keys):
        w = 1.0 if aimed[i] else (0.5 if (i > 0 and aimed[i - 1]) or (i + 1 < len(keys) and aimed[i + 1]) else 0.0)
        if w and P.get('handR'):
            P = dict(P)
            sh = np.array([P.get('lean', 0.0) + 0.3, 44.0 + P.get('breath', 0), SHW])
            h0 = np.array(P['handR'])
            h1 = sh + M @ (h0 - sh)
            if fc == 'N':                  # from behind, the throwing hand stays out past the right shoulder, in sight
                h1 = np.array([h1[0] * 0.6, max(h1[1], 47.0), max(h1[2], SHW + 5.0)])
            P['handR'] = tuple(round(float(x), 3) for x in h0 + (h1 - h0) * w)
        out.append((P, ms))
    return out
RELEASE_ANCHOR = {'primary': 'hand_R', 'secondary': 'hand_R', 'special': 'core', 'powered_primary': 'hand_R'}

EQUIP = {
    'core': dict(always=True, may_hide={'N', 'E', 'W', 'NE', 'NW'}),   # in profile, forearms raised before the chest cover it
    'hooks': dict(always=True, may_hide=set(), **{'except': {'primary': [6], 'powered_primary': [3]}}),   # aimed low in E, the arm covers the near hook
    # the shard in the right hand: required where it shows in all four facings; in the wind-up
    # (primary 3-5) the right hand is behind the head facing W, and in front of the body facing N
    'glass': dict(clips={'primary': [1, 2, 3], 'powered_primary': [0]}, may_hide={'W', 'NE', 'NW'}),   # behind the head (W) or the body (turned away)
}

EFFECTS = {
    'orbit_shards': dict(clip='special', release_frame=4, anchor='core', count=3,
                         files='fx/shard_<n>.png', note='three separate glass shards orbit the body in the powered state; removed by powered_exit'),
}


def shard_sprites():
    from ew import Fig
    import mote
    out = {}
    for n, ang in enumerate((0.5, 1.4, 2.4)):
        f = Fig(16, 16, gx=8, gy=8)
        mote.shard(f, 0, 0, 1, s=1.0, ang=ang)
        out['shard_%d.png' % n] = f.render()
    return out


if __name__ == '__main__':
    from anim_nix import write_effects
    write_effects('mote', shard_sprites(), {
        'orbit_shards': dict(EFFECTS['orbit_shards'], frame_size=[16, 16], foot_pivot=[8, 8],
                             files=['fx/shard_%d.png' % n for n in range(3)])})

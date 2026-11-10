"""Rook's animation table.  A pose names only what differs from rook.P0.

Body space: (fwd, up, lat), lat + = his RIGHT.  The right hand holds the carbine's grip (handR
= the grip unless gpos pins the gun), the left hand is solved onto the fore-end.  One helmet:
'hip' (clipped at the right hip) in the base state, carried in the right hand ('hand') while
Orbital Rig puts it on, worn ('head') in every powered clip, and returned to the hip by
powered_exit.  Thruster Vault (secondary) fires from the two attached nozzles (thrust); the
runtime lifts the sprite (roles by index: 0-2 prepare, 3 launch/rise, 4 apex, 5 fall,
6-7 landing contact), so no height is baked in.  Orbital Rig's two turrets are separate effect
sprites (out/rook/fx/turret_<F>.png), spawned at the release."""
import math
import numpy as np
import anim
from anim_nix import K, add, idle, walk, stairs, hit, jump, dodge, guard_feet
from rook import REST_R, GUN

A_STRIDE = 8.5
WALK_LOOP2 = anim.WALK_LOOP / 1.15                       # v2: 15 % faster, same stride
WALK_SPEED = round(anim.walk_speed(A_STRIDE, WALK_LOOP2), 1)
STAIR_SPEED = round(4 * 7.0 / anim.STAIR_LOOP, 1)

PW = dict(helmet='head')
AIM = dict(footR=(-3.0, 0.0), footL=(4.0, 0.0))
SHOULDER = (6.5, 39.0, 3.5)                         # stock at the shoulder, eye down the barrel
LEVEL = (1.0, 0.02, -0.12)


# --------------------------------------------------------------------------------- v2 idle, walk, fidgets
def idle2(base):
    """v2 idle, 12 drawings in 1.6 s: the breath lifts the carbine a little, the pack's straps
    and quilting follow half a beat behind, one blink."""
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    lag = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.8, 0.6, 0.4, 0.1, -0.2, -0.1]
    ms = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]
    return [(K(base, breath=br[i], lag=lag[i], blink=(i == 10), handR=add(REST_R, (0, 0.5 * br[i], 0))), ms[i]) for i in range(12)]


def walk2(base):
    """v2 walk, 12 drawings a stride: the carbine carried at low ready swings a little, a drawing late."""
    keys = []
    n = anim.WALK_N2
    gs = anim.gait(n, A_STRIDE, 3.5, bob=1.0)
    for i, g in enumerate(gs):
        late = gs[(i - 1) % n]['swing']
        keys.append((K(base, footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=1.0, lag=1.5 + 0.6 * abs(g['swing']),
                       handR=add(REST_R, (-1.2 * late, 0.5, 0))), WALK_LOOP2 * 1000 / n))
    return keys


def fidget_stars():
    """The observatory moon-walker: shades his eyes with his left hand and looks up at the sky, then
    back to the carbine."""
    G = dict(gun='right', gdir=(0.55, -0.55, -0.6))
    S = dict(G, handL=(6.0, 51.0, -5.5), poleL=(-0.3, -1.0, -0.8), zL=46.0)
    return [(K(), 150), (K(G, handL=(4.0, 38.0, -9.0)), 110), (K(S, lean=-0.6, brow=1), 130), (K(S, lean=-1.2, brow=1), 220),   # looks up
            (K(S, lean=-1.0, blink=True), 120), (K(G, handL=(4.0, 38.0, -9.0), lean=-0.3), 110), (K(lean=0.1), 120), (K(), 170)]


def fidget_check():
    """Lifts the carbine, checks the charge window on its side, lowers it."""
    C = dict(handR=(5.5, 36.0, 3.0), gdir=(0.6, 0.3, -0.75))
    return [(K(), 150), (K(handR=(4.5, 33.5, 4.0), gdir=(0.65, 0.05, -0.75)), 110), (K(C, brow=1), 120), (K(C, gdir=(0.5, 0.35, -0.8), brow=1), 160),
            (K(C, gdir=(0.6, 0.3, -0.75), blink=True), 120), (K(handR=(4.0, 33.0, 4.5), gdir=(0.65, -0.05, -0.75)), 110), (K(), 170)]


def shot(base, fast=False):
    keys = [
        (K(base, handR=(4.0, 33.0, 6.0), gdir=(0.8, 0.0, -0.6), lean=0.3), 70),                        # lift
        (K(base, footR=(2.0, 0.0), footL=(1.0, 2.5), handR=(5.5, 37.0, 4.5), gdir=(0.95, 0.05, -0.3), lean=0.5, brow=1), 50),  # to the shoulder, left foot steps
        (K(base, footR=(-1.0, 1.5), footL=(4.0, 0.0), handR=SHOULDER, gdir=LEVEL, lean=0.8, crouch=1.0, brow=1), 50),  # aim, right foot sets back
        (K(base, AIM, handR=SHOULDER, gdir=LEVEL, lean=0.9, crouch=1.5, brow=1), 70),                    # hold
        (K(base, AIM, handR=SHOULDER, gdir=LEVEL, lean=1.0, crouch=1.5, brow=1), 40),                    # squeeze
        (K(base, AIM, handR=(5.5, 39.5, 3.5), gdir=(1.0, 0.18, -0.12), lean=0.0, crouch=1.5, brow=1, flash=True), 35),  # fire
        (K(base, AIM, handR=(5.0, 40.0, 3.5), gdir=(1.0, 0.25, -0.12), lean=-0.6, crouch=1.5, brow=1), 55),  # recoil
        (K(base, AIM, handR=(6.0, 39.0, 3.5), gdir=(1.0, 0.08, -0.12), lean=0.4, crouch=1.0), 70),       # recover aim
        (K(base, footR=(0.0, 1.5), footL=(4.0, 0.0), handR=(5.0, 35.0, 4.5), gdir=(0.9, -0.05, -0.4), lean=0.3, crouch=0.5), 80),  # lower, right foot comes up
        (K(base, footR=(2.0, 0.0), footL=(0.5, 2.0), handR=(4.0, 32.0, 5.5), gdir=(0.7, -0.15, -0.7)), 90),   # left foot steps back
        (K(base), 120),
    ]
    if fast:
        keys = [keys[1], keys[2], keys[4], keys[5], keys[6], keys[7], keys[8], keys[9], keys[10]]
    return keys


def vault():
    G = dict(handR=(5.0, 35.0, 4.5), gdir=(0.85, 0.25, -0.45))
    return [
        (K(G, crouch=3.0, lean=2.0, thrust=0.0), 70),                                                   # load
        (K(G, crouch=5.0, lean=3.0, thrust=0.25, brow=1, footR=(3.0, 0.0), footL=(-3.0, 0.0)), 70),     # ignite
        (K(G, crouch=2.0, lean=3.0, thrust=0.7, brow=1, footR=(3.0, 0.0), footL=(-3.0, 0.0)), 80),      # push (last contact)
        (K(G, crouch=0.0, lean=3.5, thrust=1.0, brow=1, footR=(2.0, 0.0), footL=(-5.0, 0.0), lag=-1.5), 110),   # launch / rise: legs hang straight, toes down
        (K(G, lean=2.5, thrust=0.6, footR=(3.0, 0.0), footL=(-4.0, 0.0), lag=-0.5), 40),                # apex
        (K(G, lean=1.5, thrust=0.25, footR=(4.0, 0.0), footL=(-2.0, 0.0), lag=1.5), 55),                # fall (braking puff), legs reach for the ground
        (K(G, crouch=5.0, lean=2.5, thrust=0.0, footR=(3.0, 0.0), footL=(-3.0, 0.0), lag=1.5), 85),     # land
        (K(), 130),                                                                                      # recover: the idle pose
    ]


def orbital_rig():
    G = dict(gpos=(2.0, 31.0, -2.0), gdir=(0.55, -0.55, -0.6))           # gun hangs in the left hand
    clip = (-1.0, 22.0, 13.0)                                            # right hand at the helmet clip
    return [
        (K(), 80),
        (K(G, handR=(0.0, 27.0, 13.5)), 80),                                                       # hand drops to the hip
        (K(G, handR=clip, helmet='hand', crouch=0.5), 70),                                          # unclips it
        (K(G, handR=(3.0, 42.0, 11.0), helmet='hand', poleR=(-0.5, -1.0, 0.6)), 80),                 # brings it up
        (K(G, handR=(-3.0, 57.0, 7.0), helmet='hand', poleR=(-0.2, 0.2, 1.0), brow=1), 90),            # over the head
        (K(G, handR=(2.0, 53.0, 9.5), helmet='head', poleR=(-0.2, 0.2, 1.0), crouch=1.0, thrust=0.15, brow=1), 60),  # seated: release
        (K(G, handR=(3.0, 42.0, 10.0), helmet='head', crouch=0.5, thrust=0.05), 90),
        (K(PW, handR=(3.0, 33.0, 6.0), gdir=(0.65, -0.3, -0.7)), 100),                                # hand back to the grip
        (K(PW), 110),
    ]


def powered_exit():
    G = dict(gpos=(2.0, 31.0, -2.0), gdir=(0.55, -0.55, -0.6))
    clip = (-1.0, 22.0, 13.0)
    return [
        (K(PW), 100),
        (K(PW, G, handR=(3.0, 44.0, 10.0)), 100),
        (K(PW, G, handR=(2.0, 53.0, 9.5), poleR=(-0.2, 0.2, 1.0)), 100),
        (K(G, handR=(-3.0, 57.0, 7.0), helmet='hand', poleR=(-0.2, 0.2, 1.0)), 100),                    # lifted off
        (K(G, handR=(3.0, 40.0, 11.0), helmet='hand', poleR=(-0.5, -1.0, 0.6)), 100),
        (K(G, handR=clip, helmet='hand'), 110),                                                          # clipped back on
        (K(G, handR=(0.0, 27.0, 13.5)), 110),
        (K(), 140),
    ]


def guard(base):
    B = dict(footR=(-2.0, 0.0), footL=(3.5, 0.0))
    up = (6.0, 41.0, 8.0)
    gd = (0.35, 0.3, -0.9)                                  # carbine raised across the chest as a bar
    return [
        (K(base, B, handR=(4.0, 34.0, 7.0), gdir=(0.6, 0.1, -0.8), crouch=0.5), 55),
        (K(base, B, handR=(5.0, 37.0, 7.5), gdir=(0.45, 0.2, -0.85), crouch=1.0), 55),
        (K(base, B, handR=(5.5, 39.5, 8.0), gdir=gd, crouch=2.0, lean=1.0, brow=1), 55),
        (K(base, B, handR=up, gdir=gd, crouch=2.5, lean=1.5, brow=1), 55),
        (K(base, B, handR=up, gdir=gd, crouch=3.0, lean=1.8, brow=1), 120),                         # braced (hold)
        (K(base, B, handR=(5.0, 36.0, 7.0), gdir=(0.5, 0.1, -0.85), crouch=1.5, lean=0.6), 120),
        (K(base, handR=(3.5, 32.0, 5.5), crouch=0.5), 120),
        (K(base), 120),
    ]


def defeat():
    k1 = dict(footR=(7.0, 0.0), footL=(-6.0, 2.0))
    k2 = dict(footR=(7.5, 0.0), footL=(-8.0, 2.5))
    dn = (0.75, -0.6, -0.25)                                  # carbine muzzle to the ground, still in hand
    return [
        (K(lean=-3.0, crouch=1.0, face='shut', brow=2, handR=(2.0, 31.0, 4.0)), 80),
        (K(lean=2.0, crouch=5.0, face='shut', brow=2, handR=(4.0, 30.0, 4.0), gdir=(0.6, -0.6, -0.5), handL=(3.0, 30.0, -9.5)), 100),
        (K(k1, lean=3.0, crouch=9.0, brow=2, handR=(6.0, 30.0, 6.0), gdir=(0.5, -0.8, -0.3), handL=(6.0, 31.0, -9.0)), 100),
        (K(k2, lean=4.0, crouch=12.0, brow=2, handR=(8.0, 30.0, 8.0), gdir=dn, handL=(7.0, 30.0, -9.0)), 120),
        (K(k2, lean=6.0, crouch=13.0, brow=2, face='shut', handR=(9.0, 30.0, 8.0), gdir=dn, handL=(8.0, 30.0, -9.0)), 150),
        (K(k2, lean=7.0, crouch=13.0, face='shut', handR=(9.0, 29.5, 8.0), gdir=dn, handL=(8.0, 29.5, -9.0)), 180),
        (K(k2, lean=8.0, crouch=13.5, face='shut', handR=(9.0, 29.0, 8.0), gdir=dn, handL=(8.0, 29.0, -9.0), lag=0.5), 240),
        (K(k2, lean=8.0, crouch=13.5, face='shut', handR=(9.0, 29.0, 8.0), gdir=dn, handL=(8.0, 29.0, -9.0), lag=0.8), 300),
    ]


GR = [(2.5, 30.0, 3.0), (2.0, 31.0, 3.0), (3.0, 30.5, 3.0)]
GL = [None, None, None]
JR = [(6.5, 31.0, 3.0), (4.0, 33.0, 3.5), (5.0, 36.0, 4.0), (5.0, 35.0, 4.0), (4.5, 35.5, 4.0), (7.0, 32.0, 3.0)]
B0 = dict()
TABLE = {
    'fidget_stars': fidget_stars(),
    'fidget_check': fidget_check(),
    'idle': idle2(B0),
    'walk': walk2(B0),
    'primary': shot(B0),
    'secondary': vault(),
    'special': orbital_rig(),
    'guard': guard_feet(guard(B0), dict(footR=(-2.0, 0.0), footL=(3.5, 0.0)), __import__('rook').P0),
    'hit': hit(B0, hR=GR, hL=GL),
    'defeat': defeat(),
    'jump': jump(B0, armL=False, hR=JR),
    'stair_up': stairs(B0, REST_R, None, True),
    'stair_down': stairs(B0, REST_R, None, False),
    'dodge': dodge(B0, armL=False, armR=False),
    'powered_idle': idle2(PW),
    'powered_walk': walk2(PW),
    'powered_primary': shot(PW, fast=True),
    'powered_guard': guard_feet(guard(PW), dict(footR=(-2.0, 0.0), footL=(3.5, 0.0)), __import__('rook').P0),
    'powered_exit': powered_exit(),
}
# ------------------------------------------------------------------ fix pass (audit, 25 Oct)
for _c in ('primary', 'secondary', 'special', 'hit', 'powered_primary', 'powered_exit'):
    if _c == 'secondary' and 'rook' == 'rook':
        continue                                   # the vault leaves the ground: its feet are runtime-driven
    TABLE[_c] = anim.unskate(TABLE[_c], __import__('rook').P0)
POWERED = dict(helmet='head')                 # the worn helmet stays on in every powered clip

# ------------------------------------------------------------------ v2: fidgets, in-betweens, held keys, aims
FIDGETS = ['fidget_stars', 'fidget_check']
EXTRA = {c: dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True) for c in FIDGETS}
_D0 = __import__('rook').P0()
_SH = {}
for _c, _a in {'primary': [0], 'special': [3, 4], 'hit': [0]}.items():     # (never between two steps: one foot is always down)
    TABLE[_c], _SH[_c] = anim.densify(TABLE[_c], _a, base=_D0)        # arc in-betweens on the big moves
RELEASE = {c: (_SH[c](r) if c in _SH else r) for c, r in {'primary': 5, 'secondary': 3, 'special': 5, 'powered_primary': 3}.items()}
HOLDS = {'primary': [_SH['primary'](3)], 'special': [_SH['special'](4)]}
RELEASE_ANCHOR = {'primary': 'muzzle', 'secondary': 'nozzle_R', 'special': 'pack_top', 'powered_primary': 'muzzle'}
ANCHOR_TAG = {'muzzle': 'carbine'}
WEAPON_TAG = {'primary': 'carbine', 'powered_primary': 'carbine'}

# v2 aim within the facing (CONTRACT V2.8): from the aim on, the carbine turns about his shoulder
# onto the aim (level in S and N, anim.aim_level; raised from behind, anim.aim_body), the
# drawings either side half way.
AIM_CLIPS = ('primary', 'powered_primary')
_PIV = (1.0, 40.0, 6.0)


def _rot(a, b):
    a, b = np.array(a, float) / np.linalg.norm(a), np.array(b, float) / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a.dot(b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def aim_table(clip, fc, deg):
    M = _rot(LEVEL, anim.aim_body(fc, deg) if fc == 'N' else anim.aim_level(fc, deg))
    keys = TABLE[clip]
    aimed = [bool(P.get('gdir')) and abs(P['gdir'][0] - 1.0) < 0.06 for P, _ in keys]
    out = []
    for i, (P, ms) in enumerate(keys):
        w = 1.0 if aimed[i] else (0.5 if (i > 0 and aimed[i - 1]) or (i + 1 < len(keys) and aimed[i + 1]) else 0.0)
        if w:
            P = dict(P)
            h0 = np.array(P.get('handR') or REST_R, float)
            h1 = np.array(_PIV) + M @ (h0 - np.array(_PIV))
            d0 = np.array(P.get('gdir') or LEVEL, float)
            d1 = M @ d0
            if fc == 'N':                      # from behind: held out past the shoulder on the aim's side, clear of the head
                h1 = h1 + np.array([0.0, 2.0, 7.0 if deg >= 0 else -17.0])
            P['handR'] = tuple(round(float(x), 3) for x in h0 + (h1 - h0) * w)
            dd = d0 + (d1 - d0) * w
            P['gdir'] = tuple(round(float(x), 3) for x in dd / np.linalg.norm(dd))
        out.append((P, ms))
    return out


EQUIP = {
    'carbine': dict(always=True, may_hide={'N', 'NE', 'NW'},
                    # the recoil drawing in S: the barrel points at the camera, end on
                    **{'except': {'primary': [RELEASE['primary'] + 1], 'powered_primary': [RELEASE['powered_primary'] + 1]}}),
    'helmet': dict(always=True, may_hide={'W', 'SW', 'NW'}),   # at the right hip it is behind him facing west
    'pack': dict(always=True, may_hide=set()),
    'exhaust': dict(clips={'secondary': [2, 3, 4]}),
}

EFFECTS = {
    'turrets': dict(clip='special', release_frame=5, anchor='origin', count=2,
                    offsets=[[-45, -8], [36, 14]], files='fx/turret_<F>.png',
                    note='exactly two separate turret entities, spawned at the release at Codex offsets; they stay until powered_exit'),
}


def turret_sprites():
    """One small orbital turret (separate entity): a gunmetal tripod pod, an orange dome with a
    cream stripe, a short barrel toward the facing, one cyan sensor."""
    from ew import Fig
    out = {}
    for fc in anim.FACINGS:
        f = Fig(40, 36, gx=20, gy=32, flip=(fc == 'W'))
        for dx in (-6, 0, 6):
            f.add(f.cap(0, -8, dx, 0, 1.2, 1.0), 'gunmetal', z=1 + (0.5 if dx == 0 else 0), rl=1, rs=1.2, line='hard')
        f.add(f.ell(0, -10, 6.5, 3.5), 'rk_pad', z=2, rl=1.2, rs=1.6, line='hard')
        dome = f.ell(0, -14, 6.0, 5.4) & (f.Y < -10.5)
        f.add(dome, 'rk_orange', z=3, rl=1.6, rs=2.2, line='hard')
        f.add(f.rect(-1, -19.5, 1, -11) & dome, 'rk_suit', z=3.1, flat=2, line=None)
        if fc in 'EW':
            f.add(f.cap(3, -14, 11, -14, 1.3), 'gunmetal', z=4, rl=1, rs=1, line='hard')
            f.dot(4, -16, ('nx_glow', 3), z=4)
        elif fc == 'S':
            f.add(f.ell(0, -13, 2.0, 2.0), 'gunmetal', z=4, rl=1, rs=1, line='hard')
            f.dot(0, -13, ('nx_glow', 3), z=5)
        else:
            f.add(f.cap(0, -15, 0, -17, 1.2), 'gunmetal', z=2.5, rl=1, rs=1, line='hard')
        out['turret_%s.png' % fc] = f.render()
    return out


if __name__ == '__main__':
    import nix  # noqa: F401  (registers nx_glow)
    from anim_nix import write_effects
    write_effects('rook', turret_sprites(), {
        'turrets': dict(EFFECTS['turrets'], frame_size=[40, 36], foot_pivot=[20, 32],
                        facings={fc: 'fx/turret_%s.png' % fc for fc in anim.FACINGS})})

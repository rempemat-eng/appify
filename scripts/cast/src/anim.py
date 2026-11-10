"""Animation contract and pose-key tooling (see CONTRACT.md).

A character's animation is a table: for each clip, a list of keys (pose, ms).  A pose is a dict
of the character module's P0 fields (body offsets, feet, hands in body space, gear states).
The same table renders all four facings, because the character's draw(facing, P) projects the
pose through parts.Rig.  This module holds the shared clip list, cell, pivot and timing rules,
the in-between and gait helpers, timing fitted to Codex's runtime, and the exporter that writes
out/<id>/<clip>_<F>_NN.png, out/<id>/manifest.json (Codex's manifest shape plus facings and
anchors) and out/<id>/frames.tres (a Godot SpriteFrames resource).
"""
from __future__ import annotations

import hashlib
import json
import math
import numpy as np
import os

CELL = (160, 144)
PIVOT = (80, 136)                  # foot pivot in the cell: the sole outline is row 135, so the
                                   # drawing's packed bounds end at y = 136 (as in Codex's frames)
FIG_GY = PIVOT[1] - 1              # the Fig ground line a character's draw() passes (gy)
FACINGS = ('S', 'N', 'E', 'W')
# Contract v2 (25 Oct): eight facings for the characters that set A.FACINGS = FACINGS8; the others
# keep the four.  Order: clockwise from the camera.
FACINGS8 = ('S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW')
# A runtime that only has four facings for a character maps a diagonal to the profile on its side
# (the profile reads the aim of a weapon best); one that has eight uses them directly.
CARDINAL = {'S': 'S', 'N': 'N', 'E': 'E', 'W': 'W', 'SE': 'E', 'NE': 'E', 'SW': 'W', 'NW': 'W'}
FACING_VEC = {'E': (1.0, 0.0), 'W': (-1.0, 0.0), 'S': (0.0, 1.0), 'N': (0.0, -1.0),
              'SE': (0.7071, 0.7071), 'SW': (-0.7071, 0.7071), 'NE': (0.7071, -0.7071), 'NW': (-0.7071, -0.7071)}
# Contract v2, 26 Oct (Matt: "4 directions if its smooth enough is probably fine (like eastward).
# the weapon might need to move in more directions"): the body ships in the four facings; a
# weapon clip (A.AIM_CLIPS) is also drawn at AIM_DEGS within each facing, so with four facings a
# ranged weapon aims in 16 directions (every 22.5 degrees).  Degrees are screen angles relative
# to the facing, + clockwise (E + is down the screen, S + is toward the screen left).
AIM_DEGS = (-45.0, -22.5, 0.0, 22.5, 45.0)
AIM_TAG = {-45.0: 'm45', -22.5: 'm22', 0.0: '0', 22.5: 'p22', 45.0: 'p45'}
AIM_LAT = 0.5                      # E / W: how far an aim down (up) the screen turns toward (away from) the camera


def aim_screen(fc, deg):
    """The screen direction (x right, y down) of an aim: the facing's direction turned by deg."""
    bx, by = FACING_VEC[fc]
    a = math.atan2(by, bx) + math.radians(deg)
    return (round(math.cos(a), 4), round(math.sin(a), 4))


def aim_body(fc, deg):
    """Body-space unit vector (fwd, up, lat) that draws along aim_screen(fc, deg) through the rig:
    the weapon is drawn pointing exactly where the projectile flies on the screen (the game's map
    is the picture plane), and its lateral part gives the depth (aiming toward the camera brings
    the arms in front of the body, away puts them behind).  E: fwd = cos, up = -sin (down the
    screen), lat = AIM_LAT sin; W mirrored; S: lat = sin, fwd = cos and up = -(1 - K) cos (so the
    foreshortened forward part plus the drop draws straight down the screen); N: up = cos and lat =
    (1 + K) sin (aimed away, the weapon is raised clear of the head and still draws along the aim)."""
    import parts
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if fc == 'E':
        v = (c, -s, AIM_LAT * s)
    elif fc == 'W':
        v = (c, s, AIM_LAT * s)
    elif fc == 'S':
        v = (c, -(1 - parts.K) * c, s)
    else:                              # N: raised more (45 degrees), so the weapon clears the head
        v = (c, c, (1 + parts.K) * s)     # and still draws exactly along the aim: screen (lat, -(up + K fwd))
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


def aim_level(fc, deg):
    """Like aim_body, for a weapon that is held level (a shoulder-fired tube, a gun at the hip): in
    S and N it only turns (no pitch), with the forward part stretched by 1/K so its foreshortened
    line still draws along aim_screen; in E and W it pitches as aim_body does."""
    import parts
    if fc in ('E', 'W'):
        return aim_body(fc, deg)
    a = math.radians(deg)
    v = (math.cos(a) / parts.K, 0.0, math.sin(a))
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


# v2 walk: 12 drawings a stride (Eastward-level smoothness)
WALK_N2 = 12
# Idle fidgets (v2): when the runtime has shown idle for FIDGET_AFTER seconds, it plays one fidget
# clip (from the manifest's idle_fidgets) at the next idle drawing 0, then returns to idle; the
# next one comes after a random FIDGET_EVERY seconds of idle.
# v2 turn in-betweens (Matt, 26 Oct, after Eastward's gameplay): the body shows four facings, but a
# facing change passes through the stored three-quarter drawing between them for a short beat
TURN_FACINGS = ('SE', 'NE', 'SW', 'NW')
TURN_BASE_CLIPS = ('idle', 'walk', 'powered_idle', 'powered_walk')
TURN_HOLD = 0.07                   # s on the in-between for a 90-degree turn
TURN_HOLD_180 = 0.055              # s on each of the three steps of a 180-degree turn
AIM_STEP = 0.04                    # s per aim step when the weapon angle changes within a clip
FIDGET_AFTER = 4.0
FIDGET_EVERY = (6.0, 10.0)
DEFAULT_FACING = 'E'               # Codex's runtime plays <clip> = the east facing
STUDIO = ('/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/c241/prototypes/'
          'mygame-animation-studio/assets/animated')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_SPEED = 92.0               # Codex's RosterStudyActor.SPEED (px/s on the 960x540 grid)

# Clip list (order = Codex's RosterStudyActor.CLIPS).  n: drawings we author (a range is
# allowed); dur: total seconds; rel: release time in seconds (actions); hold: guard hold
# drawing; ground: how the feet must sit on the pivot row ('exact' all drawings, 'stance' only
# the planted feet, None no rule); release_anchor: which anchor marks the release.
CLIPS = {
    'idle':            dict(n=(8, 8), loop=True, dur=1.6, ground='exact'),
    'walk':            dict(n=(10, 10), loop=True, dur=None, ground='stance', stride=True),
    'primary':         dict(n=(10, 12), loop=False, dur=0.64, rel=0.33, ground='exact'),
    'secondary':       dict(n=(8, 12), loop=False, dur=0.64, rel=0.33, ground='exact'),
    'special':         dict(n=(8, 10), loop=False, dur=0.82, rel=0.38, ground='exact'),
    'guard':           dict(n=(8, 8), loop=False, dur=0.70, hold=4, ground='exact'),
    'hit':             dict(n=(8, 8), loop=False, dur=0.93, ground='exact'),
    'defeat':          dict(n=(8, 10), loop=False, dur=1.27, ground=None),
    'jump':            dict(n=(8, 8), loop=False, dur=0.70, ground=None),
    'stair_up':        dict(n=(8, 8), loop=True, dur=0.72, ground=None),
    'stair_down':      dict(n=(8, 8), loop=True, dur=0.72, ground=None),
    'dodge':           dict(n=(8, 8), loop=False, dur=0.495, ground=None),
    'powered_idle':    dict(n=(8, 8), loop=True, dur=1.6, ground='exact'),
    'powered_walk':    dict(n=(10, 10), loop=True, dur=None, ground='stance', stride=True),
    'powered_primary': dict(n=(8, 12), loop=False, dur=0.64, rel=0.33, ground='exact'),
    'powered_guard':   dict(n=(8, 8), loop=False, dur=0.70, hold=4, ground='exact'),
    'powered_exit':    dict(n=(8, 8), loop=False, dur=0.86, ground='exact'),
    # powered variants of the remaining actions (25 Oct): the base clip's table rendered with
    # the character's powered equipment state (anim module POWERED), base timing and release
    'powered_hit':        dict(n=(8, 8), loop=False, dur=0.93, ground='exact', base='hit'),
    'powered_dodge':      dict(n=(8, 8), loop=False, dur=0.495, ground=None, base='dodge'),
    'powered_jump':       dict(n=(8, 8), loop=False, dur=0.70, ground=None, base='jump'),
    'powered_stair_up':   dict(n=(8, 8), loop=True, dur=0.72, ground=None, base='stair_up'),
    'powered_stair_down': dict(n=(8, 8), loop=True, dur=0.72, ground=None, base='stair_down'),
    'powered_secondary':  dict(n=(8, 12), loop=False, dur=0.64, rel=0.33, ground='exact', base='secondary'),
}
POWERED_FROM = {k: v['base'] for k, v in CLIPS.items() if 'base' in v}


def add_powered(A):
    """Fill A.TABLE with the powered variants from the base tables, if the anim module A defines
    POWERED: a dict of pose overrides (e.g. dict(briar=1.0)) or a function (pose, index) ->
    pose.  POWERED_SKIP (optional) names base clips that have no powered variant (an action the
    powered state does not allow).  Tables the module already wrote are kept.  RELEASE and
    RELEASE_ANCHOR are copied from the base clip.  Idempotent."""
    pw = getattr(A, 'POWERED', None)
    if pw is None:
        return
    skip = set(getattr(A, 'POWERED_SKIP', ()))
    for name, base in POWERED_FROM.items():
        if base in skip or base not in A.TABLE or name in A.TABLE:
            continue
        keys = []
        for i, (P, ms) in enumerate(A.TABLE[base]):
            keys.append((pw(dict(P), i) if callable(pw) else dict(P, **pw), ms))
        A.TABLE[name] = keys
        if base in A.RELEASE and name not in A.RELEASE:
            A.RELEASE[name] = A.RELEASE[base]
        ra = getattr(A, 'RELEASE_ANCHOR', {})
        if base in ra and name not in ra:
            ra[name] = ra[base]


def unskate(keys, P0, lift=2.5, limit=2.0):
    """A foot that moves more than limit px (2) between drawings with both soles down skates.  This
    lifts the moving foot (lift px) in the drawing where it moves, lets only one foot move per
    drawing (the other follows in the next drawing), and appends lifted in-betweens when the
    clip ends before both feet are planted.  Use it on non-loop clips with feet on the ground."""
    d0 = P0()
    feet = ('footR', 'footL')

    def ft(P, k):
        v = P.get(k, d0[k])
        return (float(v[0]), float(v[1]))
    out = []
    planted = {k: ft(keys[0][0], k) for k in feet}
    for i, (P, ms) in enumerate(keys):
        P = dict(P)
        want = {k: ft(keys[i][0], k) for k in feet}
        moving = [k for k in feet if want[k][1] < 0.5 and planted[k][1] < 0.5 and abs(want[k][0] - planted[k][0]) > limit]
        if moving:
            mover = max(moving, key=lambda k: abs(want[k][0] - planted[k][0]))
            for k in moving:
                if k != mover:
                    P[k] = planted[k]                      # waits a drawing
            P[mover] = (want[mover][0], lift)
            planted = {k: (ft(P, k)[0], 0.0) if k == mover else ft(P, k) for k in feet}
            planted[mover] = (want[mover][0], 0.0)
        else:
            planted = want
        out.append((P, ms))
    last = keys[-1][0]
    for k in feet:                                         # finish any deferred step
        w = ft(last, k)
        if abs(w[0] - planted[k][0]) > 0.5:
            out.append((dict(out[-1][0], **{k: (w[0], lift)}), 40))
            planted[k] = w
    if any(abs(ft(out[-1][0], k)[1] - ft(last, k)[1]) > 0.1 for k in feet):
        out.append((dict(last), 60))
    return out

EXTRA_CLIPS = {'pendle': {'reload': dict(n=(8, 12), loop=False, dur=1.11, ground='exact')}}
# village folk (Hale, Moss, Ada Fern): a talk gesture loop and one work loop each, beside the
# contract's idle and walk (they only use idle, walk, talk and work)
for _v in ('hale', 'moss', 'ada'):
    EXTRA_CLIPS[_v] = {'talk': dict(n=(8, 8), loop=True, dur=1.6, ground='exact'),
                       'work': dict(n=(8, 10), loop=True, dur=1.2, ground=None)}
# Brine's harpoon-out set (designer 2): the same tables with the harpoon out (CONTRACT rule 6)
EXTRA_CLIPS['brine'] = {}
for _b in ('idle', 'walk', 'guard', 'hit', 'jump', 'dodge', 'stair_up', 'stair_down', 'special', 'defeat',
           'powered_idle', 'powered_walk', 'powered_guard', 'powered_hit', 'powered_jump', 'powered_dodge',
           'powered_stair_up', 'powered_stair_down', 'powered_exit'):
    EXTRA_CLIPS['brine'][_b + '_empty'] = dict(CLIPS[_b])

# woodland creatures (shardstruck enemies): their own clip set (anim_critter.spec)
import anim_critter as _AC  # noqa: E402
for _c, _t in (('boarlet', 0.95), ('toad', 0.95), ('tortoise', 0.95), ('thornback', 0.65)):
    EXTRA_CLIPS[_c] = _AC.spec(telegraph=_t, attack=(0.5 if _c == 'toad' else 0.18))

# Jump drawings are picked by the runtime by index, so each index has a fixed meaning.
JUMP_ROLES = ['load', 'push', 'rise', 'apex', 'fall', 'land', 'absorb', 'recover']
GUARD_ROLES = ['raise', 'raise', 'raise', 'raise', 'hold', 'lower', 'lower', 'rest']

# Walk: drawings per stride and the cadence we want; the speed that keeps feet planted follows.
WALK_N = 10
WALK_LOOP = 0.56                  # seconds per stride (two steps)
STAIR_LOOP = 0.72


# ---------------------------------------------------------------------------------- pose keys
def lerp(a, b, t):
    """In-between of two poses: numbers and tuples are interpolated; anything else (gear states,
    flags) switches at the half-way mark."""
    out = dict(a)
    for k in set(a) | set(b):
        va, vb = a.get(k), b.get(k)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            out[k] = va + (vb - va) * t
        elif isinstance(va, tuple) and isinstance(vb, tuple) and len(va) == len(vb):
            out[k] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        else:
            out[k] = va if t < 0.5 and k in a else vb
    return out


# v2 polish (Matt, 26 Oct: arcs): in-betweens move hands round the shoulder and turn weapons and
# held things through their angle, so nothing travels in a straight line or shrinks on the way
SHOULDER = {'handR': (0.0, 44.0, 12.0), 'handL': (0.0, 44.0, -12.0)}
DIR_KEYS = ('sab', 'fdir', 'hammer', 'bowu', 'bown', 'openR', 'openL', 'cat', 'hookdir', 'u', 'harpoon', 'staff', 'blade', 'gun')


def _slerp(u, v, t):
    u, v = np.array(u, float), np.array(v, float)
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu < 1e-6 or nv < 1e-6:
        return tuple(u + (v - u) * t)
    a, b = u / nu, v / nv
    d = float(np.clip(a.dot(b), -1.0, 1.0))
    om = math.acos(d)
    if om < 1e-4 or om > math.pi - 1e-3:
        w = a + (b - a) * t
        w = w / (np.linalg.norm(w) or 1.0)
    else:
        w = (math.sin((1 - t) * om) * a + math.sin(t * om) * b) / math.sin(om)
    return tuple(float(x) for x in w * (nu + (nv - nu) * t))


def arc_lerp(a, b, t):
    """lerp, but hands swing on arcs about their shoulder and direction fields turn (slerp)."""
    out = lerp(a, b, t)
    for k, piv in SHOULDER.items():
        va, vb = a.get(k), b.get(k)
        if isinstance(va, tuple) and isinstance(vb, tuple) and len(va) == len(vb) == 3:
            r = _slerp(np.subtract(va, piv), np.subtract(vb, piv), t)
            out[k] = tuple(round(float(x + p), 3) for x, p in zip(r, piv))
    for k in DIR_KEYS:
        va, vb = a.get(k), b.get(k)
        if isinstance(va, tuple) and isinstance(vb, tuple) and len(va) == len(vb) == 3:
            out[k] = tuple(round(x, 4) for x in _slerp(va, vb, t))
    return out


def ease(t, kind='io'):
    if kind == 'in':
        return t * t
    if kind == 'out':
        return 1 - (1 - t) ** 2
    if kind == 'io':
        return 0.5 - 0.5 * math.cos(math.pi * t)
    return t


def gait(n, A, lift, bob=1.0, stance_lat=None):
    """A walk stride of n drawings: the planted foot travels back 2A over n/2 drawings while the
    swing foot arcs forward, so the body moves 4A per stride with no foot slide.  Returns one
    dict per drawing with footR, footL (fwd, lift), bob (+ = down) and swing (-1..1, the right
    foot's phase, for counter-swinging arms)."""
    out = []
    half = n / 2
    for i in range(n):
        ph = (i % half) / half                  # 0..1 within the step
        plant = A - 2 * A * ph
        swing = -A + 2 * A * ph
        sl = lift * math.sin(math.pi * ph)
        c = math.cos(2 * math.pi * (ph - 0.15))  # down just after contact (+), up at passing (-)
        b = int(round(bob * c)) if abs(c) > 0.55 else 0
        if i < half:
            fr, fl = (plant, 0.0), (swing, sl)
        else:
            fr, fl = (swing, sl), (plant, 0.0)
        s = fr[0] / A
        out.append(dict(footR=fr, footL=fl, bob=b, swing=s))
    return out


def walk_speed(A, loop=WALK_LOOP):
    return 4 * A / loop


# ---------------------------------------------------------------------------------- timing
def codex_clip(cid, clip):
    p = os.path.join(STUDIO, cid, 'manifest.json')
    if not os.path.exists(p):
        return None
    m = json.load(open(p))
    return m['clips'].get(clip) or m['clips'].get(POWERED_FROM.get(clip, ''))


def fit_timing(cid, clip, ms, rel_frame=None, spec=None):
    """Scale authored milliseconds so the clip keeps Codex's total duration and release time
    (the gameplay timing), keeping the authored proportions on each side of the release."""
    spec = spec or CLIPS.get(clip) or EXTRA_CLIPS.get(cid, {}).get(clip, {})
    if spec.get('authored'):                     # whole 60 fps frames, at least one
        return [round(max(1, round(m / 1000.0 / FRAME)) * FRAME, 4) for m in ms]
    cx = codex_clip(cid, clip)
    total = (cx or {}).get('duration') or spec.get('dur')
    relt = (cx or {}).get('release_time') or spec.get('rel')
    s = [m / 1000.0 for m in ms]
    if spec.get('stride') or total is None:
        return [round(x, 4) for x in s]
    if rel_frame is not None and relt is not None:
        a, b = sum(s[:rel_frame]), sum(s[rel_frame:])
        s = [x * relt / a for x in s[:rel_frame]] + [x * (total - relt) / b for x in s[rel_frame:]]
    else:
        k = total / sum(s)
        s = [x * k for x in s]
    return space(s, rel_frame, spec.get('holds', ()))


FRAME = 1.0 / 60.0


def space(s, rel=None, holds=()):
    """v2 polish (Matt, 26 Oct: spacing and easing): an action's drawings are held whole frames at
    60 fps, so no drawing flickers past in less than a frame or alternates one and two frames.
    Key poses are held: the release (contact) drawing and the one after it at least 3 frames, the
    longest-authored drawing on each side (the anticipation peak, the settle) at least 3, the last at
    least 3; other drawings at least 2, in-betweens shorter than the rest down to 1 when the clip has
    more drawings than frames.  The remaining frames follow the authored proportions, so the slow-in
    and slow-out stay uneven, not mechanical.  Each side of the release keeps its length to the frame."""
    n = len(s)
    segs = [(0, rel), (rel, n)] if rel else [(0, n)]
    out = [0.0] * n
    for a, b in segs:
        idx = list(range(a, b))
        if not idx:
            continue
        total = max(len(idx), int(round(sum(s[a:b]) / FRAME)))
        keys = {max(idx, key=lambda i: s[i])} | {i for i in holds if a <= i < b}
        if rel is not None:
            keys |= {i for i in (rel, rel + 1) if a <= i < b}
        if b == n:
            keys.add(n - 1)
        mins = {i: (3 if i in keys else 2) for i in idx}
        for i in sorted(idx, key=lambda i: s[i]):               # too many drawings: in-betweens to 1 frame
            if sum(mins.values()) <= total:
                break
            if i not in keys:
                mins[i] = 1
        for i in sorted(keys, key=lambda i: -s[i]):
            if sum(mins.values()) <= total:
                break
            mins[i] = 2
        fr = dict(mins)
        spare = total - sum(fr.values())
        if spare > 0:                                            # by the authored proportions, largest remainder
            want = {i: s[i] / sum(s[a:b]) * total for i in idx}
            extra = {i: max(0.0, want[i] - fr[i]) for i in idx}
            tot = sum(extra.values()) or 1.0
            share = {i: extra[i] / tot * spare for i in idx}
            add = {i: int(share[i]) for i in idx}
            left = spare - sum(add.values())
            for i in sorted(idx, key=lambda i: -(share[i] - add[i]))[:left]:
                add[i] += 1
            for i in idx:
                fr[i] += add[i]
        for i in idx:
            out[i] = round(fr[i] * FRAME, 4)
    return out


# ---------------------------------------------------------------------------------- export
def _job(args):
    """Render one clip in one facing (and aim) and save its PNGs (worker for export)."""
    cid, clip, fc, outdir = args[:4]
    aim = args[4] if len(args) > 4 else None
    import importlib
    import numpy as np
    mod = importlib.import_module(cid)
    A = importlib.import_module('anim_' + cid)
    add_powered(A)
    from ew import to_img
    flist = []
    if aim is not None:
        keys = A.aim_table(clip, fc, aim)
    elif hasattr(A, 'facing_table'):              # a module may pose a clip per facing (same count and timing)
        keys = A.facing_table(clip, fc)
    else:
        keys = A.TABLE[clip]
    from PIL import Image
    loop = bool(clip_specs(cid, A).get(clip, {}).get('loop'))
    figs, ims = [], []
    for i, (P, ms) in enumerate(keys):
        f = mod.draw(fc, mod.P0(**P))
        ims.append(np.array(to_img(f.render()).convert('RGBA')))
        figs.append(f)
    ims = deflicker(ims, loop, protect0=clip in ('idle', 'powered_idle'))
    for i, (f, im) in enumerate(zip(figs, ims)):
        name = ('%s_%s_%02d.png' % (clip, fc, i)) if aim is None else ('%s_%s_%s_%02d.png' % (clip, fc, AIM_TAG[aim], i))
        p = os.path.join(outdir, name)
        Image.fromarray(im).save(p)
        ys, xs = np.where(im[..., 3] > 0)
        flist.append(dict(path='res://assets/animated/%s/%s' % (cid, name), file=name,
                          packed_bounds=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                          anchors={k: [round(float(v[0]), 1), round(float(v[1]) + FIG_GY - PIVOT[1], 1)] for k, v in f.anchors.items()},
                          equipment={k: int(v) for k, v in f.tags.items()},
                          anchor_gap=anchor_gaps(f, A, back=fc in ('N', 'NE', 'NW')),
                          sha256=hashlib.sha256(open(p, 'rb').read()).hexdigest()))
    return (clip, fc) if aim is None else (clip, fc, aim), flist


# the held item each release anchor sits on (a module may extend it with ANCHOR_TAG)
ANCHOR_TAG = {'arrow_tip': 'arrow', 'flask': 'flask', 'muzzle': 'launcher', 'blade_tip': 'sabre', 'lantern': 'lantern',
              'catalyst': 'catalyst'}


def anchor_gaps(f, A, back=False):
    """v2 (release anchors on the held item): for each release anchor this drawing has, the
    distance in pixels from the anchor to the nearest visible pixel of its item (None when the
    item shows no pixels in this drawing).  From behind (back), a part the module names in
    ANCHOR_COVER[anchor] (gear on the back that is nearer the camera than the item) counts with
    the item: the anchor may sit on the part that covers it."""
    tags = dict(ANCHOR_TAG, **getattr(A, 'ANCHOR_TAG', {}))
    out = {}
    masks = getattr(f, 'tagmasks', {})
    for name in set(getattr(A, 'RELEASE_ANCHOR', {}).values()):
        tg = tags.get(name)
        if tg is None or name not in f.anchors:
            continue
        mk = masks.get(tg)
        if mk is not None:                           # parts of the item itself in some states (a storm rim on a blade)
            for ct in getattr(A, 'ANCHOR_WITH', {}).get(name, ()):
                if masks.get(ct) is not None:
                    mk = mk | masks[ct]
        if back and mk is not None:
            for ct in getattr(A, 'ANCHOR_COVER', {}).get(name, ()):
                if masks.get(ct) is not None:
                    mk = mk | masks[ct]
        if mk is None or not mk.any():
            out[name] = None
            continue
        ax, ay = f.anchors[name]
        ys, xs = np.nonzero(mk)
        px, py = f.gx + ax, f.gy + ay                  # anchors are stored scaled and in screen orientation
        out[name] = round(float(np.sqrt(((xs + 0.5 - px) ** 2 + (ys + 0.5 - py) ** 2).min())), 1)
    return out


def blinks(ims, loop, size=2):
    """Pixels that blink for one drawing: the drawing before and after agree there and this one
    differs, in a patch of at most `size` pixels (8-connected).  Returns [(index, mask)]."""
    from scipy import ndimage
    n = len(ims)
    out = []
    for i in range(n):
        if n < 3 or (not loop and (i == 0 or i == n - 1)):
            continue
        a, b, c = ims[i - 1], ims[i], ims[(i + 1) % n]
        m = (a == c).all(-1) & (a != b).any(-1)
        if not m.any():
            continue
        lab, k = ndimage.label(m, structure=np.ones((3, 3)))
        if k == 0:
            continue
        sizes = ndimage.sum(m, lab, range(1, k + 1))
        small = np.isin(lab, np.nonzero(sizes <= size)[0] + 1)
        if small.any():
            out.append((i, small))
    return out


def flicker(ims, loop):
    """[(drawing, n)]: one-drawing blinks that are specks in their own drawing (the pixel differs
    from what both neighbouring drawings show there, and that value fills at least three of its
    own 8 neighbours): flicker, as opposed to an edge that moves."""
    out = []
    for i, mask in blinks(ims, loop):
        cur, prev = ims[i], ims[i - 1]
        H, W = cur.shape[:2]
        n = 0
        for y, x in zip(*np.nonzero(mask)):
            v = prev[y, x]
            if int((cur[max(0, y - 1):y + 2, max(0, x - 1):x + 2] == v).all(-1).sum()) >= 3:
                n += 1
        if n:
            out.append((i, n))
    return out


def deflicker(ims, loop, protect0=True):
    """v2 polish (Matt, 26 Oct: clean pixels, no flicker): a blink of one or two pixels that shows
    for a single drawing takes the value its neighbouring drawings agree on, but only where that
    value matches at least three of the pixel's own 8 neighbours in this drawing (it is a speck
    here, so the fix blends in and never leaves a stray).  With protect0 drawing 0 is never changed
    (a fidget starts and ends on idle 0's exact pixels); a non-loop's ends never are."""
    orig = [im.copy() for im in ims]
    ims = [im.copy() for im in ims]
    H, W = ims[0].shape[:2]
    for _ in range(4):
        changed = 0
        for i, mask in blinks(ims, loop):
            if i == 0 and protect0:
                continue
            cur, prev = ims[i], ims[i - 1]
            ys, xs = np.nonzero(mask)
            for y, x in zip(ys, xs):
                v = prev[y, x]
                y0, y1, x0, x1 = max(0, y - 1), min(H, y + 2), max(0, x - 1), min(W, x + 2)
                same = int((cur[y0:y1, x0:x1] == v).all(-1).sum())
                if same >= 3:
                    cur[y, x] = v
                    changed += 1
        if not changed:
            break
    # 26 Oct (Cairn's scaled boulders): a fix can strand a neighbour as a lone pixel; where the four
    # neighbours of a pixel agree and it is lone only after the fixes, it takes their colour (the
    # fixes themselves are kept, so no blink comes back)
    for i in range(len(ims)):
        for _ in range(3):
            new = _lone_mask(ims[i]) & ~_lone_mask(orig[i])
            if not new.any():
                break
            ys, xs = np.nonzero(new)
            for y, x in zip(ys, xs):
                nb = [tuple(ims[i][yy, xx]) for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))]
                if len(set(nb)) == 1:
                    ims[i][y, x] = nb[0]
    return ims


def _lone_mask(a):
    """Opaque pixels whose colour differs from all four opaque orthogonal neighbours (checks.lone_pixels)."""
    key = (a[..., 0].astype(np.int64) << 24) | (a[..., 1].astype(np.int64) << 16) | (a[..., 2].astype(np.int64) << 8) | a[..., 3]
    op = a[..., 3] > 0
    out = np.zeros(op.shape, bool)
    k = key[1:-1, 1:-1]
    nb = [key[:-2, 1:-1], key[2:, 1:-1], key[1:-1, :-2], key[1:-1, 2:]]
    on = [op[:-2, 1:-1], op[2:, 1:-1], op[1:-1, :-2], op[1:-1, 2:]]
    m = op[1:-1, 1:-1] & on[0] & on[1] & on[2] & on[3]
    for n in nb:
        m &= n != k
    out[1:-1, 1:-1] = m
    return out


def tres(cid, clips_frames):
    """Godot 4 SpriteFrames: animation <clip> is the east facing (what Codex's runtime plays);
    <clip>_S, <clip>_N, <clip>_E and <clip>_W are the four facings."""
    ext, anims, ids = [], [], {}
    for name, loop, frames in clips_frames:
        items = []
        for path, dur in frames:
            if path not in ids:
                ids[path] = len(ids) + 1
                ext.append('[ext_resource type="Texture2D" path="res://assets/animated/%s/%s" id="f%d"]' % (cid, path, ids[path]))
            items.append('{"duration": %.6f, "texture": ExtResource("f%d")}' % (dur, ids[path]))
        anims.append('{"frames": [%s], "loop": %s, "name": &"%s", "speed": 1.0}' % (', '.join(items), 'true' if loop else 'false', name))
    head = '[gd_resource type="SpriteFrames" load_steps=%d format=3]\n\n' % (len(ids) + 1)
    return head + '\n'.join(ext) + '\n\n[resource]\nanimations = [\n' + ',\n'.join(anims) + '\n]\n'


def clip_specs(cid, A):
    """Every clip spec a character has: the contract's, the shared extras and its module's own
    (A.EXTRA, e.g. the v2 idle fidgets)."""
    out = dict(CLIPS)
    out.update(EXTRA_CLIPS.get(cid, {}))
    out.update(getattr(A, 'EXTRA', {}))
    return out


def export(mod, A, outdir=None, facings=None, clips=None, log=print):
    """Render and write every clip and facing of one character.  A is its anim module: TABLE
    (clip -> [(pose, ms)]), RELEASE (clip -> drawing index), RELEASE_ANCHOR (clip -> anchor
    name).  Returns the manifest dict."""
    cid = mod.ID
    add_powered(A)
    facings = facings or FACINGS                  # the shipped contract: four body facings (8 with export.py --facings 8)
    aims = [c for c in getattr(A, 'AIM_CLIPS', ())]
    specs = clip_specs(cid, A)
    outdir = outdir or os.path.join(ROOT, 'out', cid)
    os.makedirs(outdir, exist_ok=True)
    table = A.TABLE
    names = [c for c in specs if c in table and (clips is None or c in clips)]
    v2 = len(facings) == 8 or bool(getattr(A, 'FIDGETS', None)) or bool(getattr(A, 'AIM_CLIPS', None))
    man = dict(id=cid, name=mod.NAME, view='8dir' if len(facings) == 8 else 'SNEW', directions=list(facings), default_direction=DEFAULT_FACING,
               frame_size=list(CELL), foot_pivot=list(PIVOT), body_height_target=getattr(mod, 'HEIGHT', 74),
               walk_speed=getattr(A, 'WALK_SPEED', None), stair_speed=getattr(A, 'STAIR_SPEED', None),
               anchor_space='pixels relative to foot_pivot, screen orientation (x right, y down)',
               source='castwork/src/%s.py + anim_%s.py (procedural, reproducible)' % (cid, cid), clips={})
    if v2:
        man['contract'] = 2
        man['facing_vectors'] = {fc: list(FACING_VEC[fc]) for fc in facings}
        if len(facings) == 8:
            man['facing_fallback'] = dict(CARDINAL)      # for a runtime that only plays S, N, E, W
        man['facing_rule'] = ('pick the facing whose vector is nearest the aim (while acting or standing) or the '
                              'movement (while walking), with 10 degrees of hysteresis; keep the drawing index on a '
                              'facing change; a weapon clip also picks its aim within the facing (aim_rule)')
        fid = getattr(A, 'FIDGETS', None)
        if fid:
            man['idle_fidgets'] = dict(clips=list(fid), after=FIDGET_AFTER, every=list(FIDGET_EVERY),
                                       rule=('after idle has shown for `after` s, play one fidget (random, never the same '
                                             'twice running) when idle reaches drawing 0, then idle; the next after a random '
                                             '`every` s of idle; any other clip cancels it at once (fidgets start and end on idle 0)'))
    tres_clips = []
    from multiprocessing import Pool
    jobs = [(cid, clip, fc, outdir) for clip in names for fc in facings if clip not in aims]
    jobs += [(cid, clip, fc, outdir, d) for clip in names if clip in aims for fc in facings for d in AIM_DEGS]
    turn_clips = [c for c in getattr(A, 'TURN_CLIPS', TURN_BASE_CLIPS + tuple(aims)) if c in names] if len(facings) == 4 and v2 else []
    jobs += [(cid, clip, fc, outdir) for clip in turn_clips for fc in TURN_FACINGS]
    with Pool(os.cpu_count() or 2) as pool:
        done = {k: fl for k, fl in pool.imap_unordered(_job, jobs)}
    for clip in names:
        if clip in aims:                           # the facing's own drawings are its straight-ahead aim
            for fc in facings:
                done[(clip, fc)] = done[(clip, fc, 0.0)]
    for clip in names:
        spec = specs[clip]
        if getattr(A, 'HOLDS', {}).get(clip):               # the module's key poses, held (anim.space)
            spec = dict(spec, holds=tuple(A.HOLDS[clip]))
        rel = A.RELEASE.get(clip)
        durs = fit_timing(cid, clip, [ms for _, ms in table[clip]], rel, spec)
        relt = round(sum(durs[:rel]), 4) if rel is not None else None
        entry = dict(frame_count=len(durs), durations=durs, duration=round(sum(durs), 4), loop=spec['loop'],
                     release_frame=rel, release_time=relt, hold_frame=spec.get('hold'),
                     roles=JUMP_ROLES if 'jump' in clip else (GUARD_ROLES if 'guard' in clip else None),
                     facings={})
        for fc in facings:
            flist = done[(clip, fc)]
            fe = dict(frames=flist)
            ra = getattr(A, 'RELEASE_ANCHOR', {}).get(clip)
            if rel is not None and ra:
                an = flist[rel]['anchors'].get(ra) or flist[max(0, rel - 1)]['anchors'].get(ra)
                fe['release_anchor'] = an
                fe['release_anchor_name'] = ra
            if clip in aims:
                fe['aims'] = {}
                for d in AIM_DEGS:
                    al = done[(clip, fc, d)]
                    ae = dict(deg=d, screen=list(aim_screen(fc, d)), frames=al)
                    if rel is not None and ra:
                        ae['release_anchor'] = al[rel]['anchors'].get(ra) or al[max(0, rel - 1)]['anchors'].get(ra)
                    fe['aims'][AIM_TAG[d]] = ae
            entry['facings'][fc] = fe
            if clip in turn_clips and fc == facings[-1]:
                entry['turns'] = {d: dict(frames=done[(clip, d)]) for d in TURN_FACINGS}
            tres_clips.append(('%s_%s' % (clip, fc), spec['loop'], [(x['file'], dd) for x, dd in zip(flist, durs)]))
            if fc == DEFAULT_FACING:
                entry['frames'] = flist
                if 'release_anchor' in fe:
                    entry['release_anchor'] = fe['release_anchor']
                tres_clips.append((clip, spec['loop'], [(x['file'], dd) for x, dd in zip(flist, durs)]))
        log('%s %s: %d drawings x %d facings' % (cid, clip, len(durs), len(facings)))
        man['clips'][clip] = entry
    mp = os.path.join(outdir, 'manifest.json')
    if clips is not None and os.path.exists(mp):          # partial export: keep the other clips
        old = json.load(open(mp))
        merged = {c: man['clips'].get(c) or old['clips'].get(c) for c in specs
                  if c in man['clips'] or c in old.get('clips', {})}
        man['clips'] = merged
    tres_clips = []
    for clip, e in man['clips'].items():
        for fc in facings:
            fl = e['facings'][fc]['frames']
            tres_clips.append(('%s_%s' % (clip, fc), e['loop'], [(x['file'], d) for x, d in zip(fl, e['durations'])]))
            for tag, ae in e['facings'][fc].get('aims', {}).items():
                tres_clips.append(('%s_%s_%s' % (clip, fc, tag), e['loop'], [(x['file'], d) for x, d in zip(ae['frames'], e['durations'])]))
            if fc == DEFAULT_FACING:
                tres_clips.append((clip, e['loop'], [(x['file'], d) for x, d in zip(fl, e['durations'])]))
        for d, te in e.get('turns', {}).items():
            tres_clips.append(('%s_%s' % (clip, d), e['loop'], [(x['file'], dd) for x, dd in zip(te['frames'], e['durations'])]))
    man['pose_count'] = sum(c['frame_count'] for c in man['clips'].values()) * len(facings)
    if turn_clips:
        man['turn_inbetweens'] = dict(
            facings=list(TURN_FACINGS), clips=[c for c, e in man['clips'].items() if e.get('turns')], hold=TURN_HOLD, hold_180=TURN_HOLD_180,
            aim_step=AIM_STEP,
            rule=('turn in-betweens, not playable facings: when the body facing changes between S N E W during a clip '
                  'listed here, show turns[D] (the three-quarter drawing between the two facings) for `hold` s, keeping '
                  'the drawing index and the clip time; a 180-degree turn passes through one side (D1, the cardinal '
                  'between, D2; `hold_180` s each), the side the input rotates toward (S side on an exact reversal). A '
                  'weapon clip shows its straight-ahead drawing on the in-betweens. Within a facing the weapon aim steps '
                  'one aim_tag per `aim_step` s toward a new aim instead of jumping.'))
    if aims:
        man['aim_degrees'] = list(AIM_DEGS)
        man['aim_tags'] = {AIM_TAG[d]: d for d in AIM_DEGS}
        man['aim_rule'] = ('weapon clips listed in aim_clips are drawn at aim_degrees within each body facing (screen degrees, '
                           '+ clockwise from the facing); the runtime picks the facing from the aim (nearest of S N E W) and the '
                           'aim nearest the exact angle, plays <clip>_<F>_<tag>, spawns the projectile at that aim\'s release_anchor '
                           'and flies it along the exact aim')
        man['aim_clips'] = [c for c in aims if c in man['clips']]
    # separate effect entities (turrets, decoys, shards): a module hook A.effects() -> (sprites,
    # meta) writes them; without one, the previous manifest's 'effects' block is kept, so a
    # re-export never drops them (AUDIT-2)
    hook = getattr(A, 'effects', None)
    if callable(hook):
        sprites, meta = hook()
        os.makedirs(os.path.join(outdir, 'fx'), exist_ok=True)
        from ew import to_img
        for name, a in sprites.items():
            to_img(a).save(os.path.join(outdir, 'fx', name))
        man['effects'] = meta
    elif os.path.exists(mp):
        prev = json.load(open(mp)).get('effects')
        if prev:
            man['effects'] = prev
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1)
    open(os.path.join(outdir, 'frames.tres'), 'w').write(tres(cid, tres_clips))
    return man


# ---------------------------------------------------------------------------------- v2 helpers
def follow(keys, loop=False, gain=1.4, damp=0.55, keys_out=('lag', 'hair'), lag2=0.7, scale=(1.0, 0.8)):
    """Secondary motion (v2): cloth (lag) and hair (hair) trail the body.  From the shoulders'
    forward travel between drawings (lean + hipx, and the crouch for a drop), a damped spring
    gives a trailing offset that overshoots and settles: added to the authored lag and, one
    drawing later and a little weaker, to hair.  Loops are run round twice so they close."""
    def body(P):
        g = lambda k: P.get(k) or 0.0
        return g('lean') + g('hipx'), g('crouch') + g('bob')
    n = len(keys)
    rng = list(range(n)) * (3 if loop else 1)
    c = v = 0.0
    prev = body(keys[rng[0] - 1][0]) if loop else body(keys[0][0])
    trail = [0.0] * n
    for k in rng:
        b = body(keys[k][0])
        vel = (b[0] - prev[0]) + 0.5 * (b[1] - prev[1])
        prev = b
        # spring toward -gain * velocity
        tgt = -gain * vel
        v = v * damp + (tgt - c) * 0.6
        c = c + v
        trail[k] = c
    out = []
    for i, (P, ms) in enumerate(keys):
        P = dict(P)
        j = (i - 1) % n if loop else max(0, i - 1)
        if not loop and i == n - 1:          # a clip ends on its rest pose: nothing left trailing
            out.append((P, ms))
            continue
        P[keys_out[0]] = P.get(keys_out[0], 0.0) + scale[0] * trail[i]
        P[keys_out[1]] = P.get(keys_out[1], 0.0) + scale[1] * lag2 * trail[j] + scale[1] * (1 - lag2) * trail[i]
        out.append((P, ms))
    return out


def ease_keys(a, b, n, kind='io', ms=40):
    """n in-betweens from pose a to pose b (excluding a, including b)."""
    return [(lerp(a, b, ease((i + 1) / n, kind)), ms) for i in range(n)]


def densify(keys, after, t=0.5, base=None):
    """Insert an in-between after each drawing index in `after` (the midpoint pose, the drawing's
    time split between the two).  Returns (keys, shift) where shift(i) maps an old index (a
    release drawing) to the new one."""
    after = sorted(set(after))
    out = []
    for i, (P, ms) in enumerate(keys):
        if i in after and i + 1 < len(keys):
            out.append((P, ms * (1 - t)))
            a, b = P, keys[i + 1][0]
            if base is not None:                     # interpolate from full poses (missing = rest)
                a, b = dict(base, **a), dict(base, **b)
                mid = arc_lerp(a, b, t)
                mid = {k: v for k, v in mid.items() if k in P or k in keys[i + 1][0] or v != base.get(k)}
            else:
                mid = arc_lerp(a, b, t)
            out.append((mid, ms * t))
        else:
            out.append((P, ms))
    return out, (lambda i: i + sum(1 for a in after if a < i and a + 1 < len(keys)))

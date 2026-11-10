"""Shared table helpers for the village folk (anim_hale, anim_moss, anim_ada), contract v2:
a 12-drawing breathing idle, a 12-drawing walk 15 % faster with the same stride (a quicker
cadence, so the planted foot still travels exactly the body's distance), a 12-drawing talk loop,
and secondary motion (anim.follow: the apron, skirt and shawl trail the body)."""
import anim

SPEEDUP = 1.15                                 # v2 (Matt 25 Oct): walk 15 % faster
WALK_LOOP = anim.WALK_LOOP / SPEEDUP           # one stride in 0.487 s


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def walk_speed(A, scale):
    return round(anim.walk_speed(A, WALK_LOOP) * scale, 1)


IDLE_BR = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
IDLE_LAG = [0.0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.7, 0.5, 0.3, 0.1, 0.0, -0.1]
IDLE_MS = [150, 120, 120, 140, 150, 140, 130, 130, 140, 120, 90, 170]


def idle(rest_r, rest_l, extra=None):
    """v2 breathing idle, 12 drawings in 1.6 s: the chest rises 1 px, the hands ride with it, the
    cloth answers half a beat later, one blink."""
    keys = []
    for i in range(12):
        P = dict(breath=IDLE_BR[i], blink=(i == 10), lag=IDLE_LAG[i],
                 handR=add(rest_r, (0, 0.5 * IDLE_BR[i], 0)), handL=add(rest_l, (0, 0.5 * IDLE_BR[i], 0)))
        if extra:
            P.update(extra)
        keys.append((P, IDLE_MS[i]))
    return keys


def rest_pose(table):
    """idle drawing 0 (a fidget starts and ends on it, so the cut in and out never pops)."""
    return dict(table['idle'][0][0])


def walk(rest_r, rest_l, A, swing_r=3.0, swing_l=3.5, extra=None, keep_l=False):
    """v2 walk: 12 drawings a stride (anim.WALK_N2) in WALK_LOOP, arms counter-swing, the cloth
    trails the step (follow)."""
    n = anim.WALK_N2
    keys = []
    for g in anim.gait(n, A, 3.0, bob=1.0):
        s = g['swing']
        P = dict(footR=g['footR'], footL=g['footL'], bob=g['bob'], lean=0.8, lag=1.0 + 0.5 * abs(s),
                 handR=add(rest_r, (-swing_r * s, 0.5, 0)),
                 handL=rest_l if keep_l else add(rest_l, (swing_l * s, 0.5, 0)))
        if extra:
            P.update(extra)
        keys.append((P, WALK_LOOP * 1000 / n))
    return keys


def talk(rest_r, rest_l, hand='R', palm=(8.0, 33.0, 8.0), extra=None):
    """v2 talking loop, 12 drawings: the hand rises palm up (an anticipating dip first), makes two
    beats, settles past rest and back; the mouth moves; a breath with the words."""
    lift = [0.0, -0.08, 0.35, 0.8, 1.05, 0.9, 1.0, 1.08, 0.85, 0.45, 0.1, -0.04]
    beat = [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
    mouth = [None, None, 'talk', 'talk', None, 'talk', 'talk', None, 'talk', None, None, None]
    br = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    keys = []
    rest = rest_r if hand == 'R' else rest_l
    other = 'L' if hand == 'R' else 'R'
    for i in range(12):
        t = lift[i]
        h = tuple(r + (p - r) * t for r, p in zip(rest, palm))
        h = add(h, (0, -1.0 * beat[i], 0))
        P = dict(face=mouth[i], lean=0.4 * max(t, 0.0), breath=br[i])
        P['hand' + hand] = h
        P['hand' + other] = rest_l if hand == 'R' else rest_r
        if extra:
            P.update(extra)
        keys.append((P, 1600 / 12))
    return keys


def v2(keys, loop):
    """anim.follow for the folk: only cloth (lag) trails; there is no hair sway field."""
    out = []
    for P, ms in anim.follow(keys, loop=loop):
        P = dict(P)
        P.pop('hair', None)
        out.append((P, ms))
    return out


def fidget(table, steps, ms):
    """A fidget from idle 0 back to idle 0: steps are pose changes on top of the rest pose."""
    r = rest_pose(table)
    keys = [(dict(r), ms[0])]
    for s, t in zip(steps, ms[1:-1]):
        keys.append((dict(r, **s), t))
    keys.append((dict(r), ms[-1]))
    return keys


EXTRA_FIDGET = dict(n=(8, 14), loop=False, dur=None, ground='exact', authored=True)

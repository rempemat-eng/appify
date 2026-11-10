"""Shared clip tables for the woodland creatures (shardstruck enemies).  Clips: idle, move,
telegraph (the wind-up, read in the pose), attack, hurt, stagger (the recover window: dazed, open
to hits), freed (the shard pops out, the creature shakes itself, calms and stands) and freed_move
(calm, shardless, trotting off).  The runtime stretches telegraph to the role's windup_time."""
import math


def spec(telegraph=0.95, attack=0.18):
    return {'move':       dict(n=(8, 8), loop=True, dur=None, ground='stance', stride=True),
            'telegraph':  dict(n=(8, 8), loop=False, dur=telegraph, ground=None),
            'attack':     dict(n=(4, 6), loop=False, dur=attack, ground=None),
            'hurt':       dict(n=(4, 4), loop=False, dur=0.32, ground='exact'),
            'stagger':    dict(n=(6, 8), loop=False, dur=0.65, ground='exact'),
            'freed':      dict(n=(12, 16), loop=False, dur=1.8, ground=None),
            'freed_move': dict(n=(8, 8), loop=True, dur=None, ground='stance', stride=True)}


def idle(base=None, n=8, ms=200, breathe=0.6, nod=0.6):
    b = base or {}
    out = []
    for i in range(n):
        t = i / n
        s = math.sin(2 * math.pi * t)
        out.append((dict(b, bob=breathe * (0.5 + 0.5 * s), head=(0.0, nod * s), blink=(i == 5), fx=i), ms))
    return out


def move(base=None, n=8, ms=70, stride=5.0, lift=2.5, bob=0.8, extra=None):
    b = base or {}
    out = []
    for i in range(n):
        g = i / n
        k = dict(b, gait=g, stride=stride, lift=lift, bob=bob * (0.5 - 0.5 * math.cos(4 * math.pi * g)), fx=i,
                 head=(0.0, 0.6 * math.sin(4 * math.pi * g)))
        if extra:
            k.update(extra(g))
        out.append((k, ms))
    return out


def freed_move(base=None, **kw):
    return move(dict(base or {}, shard=1.0, calm=1.0), **kw)


def shard_rule(table, may_hide=('N',)):
    """The shard must show in every clip before freed."""
    return dict(clips={c: list(range(len(table[c]))) for c in ('idle', 'move', 'telegraph', 'attack', 'hurt', 'stagger') if c in table},
                may_hide=set(may_hide))

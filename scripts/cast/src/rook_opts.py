"""Rook redesign options for Matt (26 Oct): three astronauts drawn to fit the world, same kit
(pulse carbine, ONE helmet at the right hip / in hand / worn, the twin-thruster pack with its two
nozzle bells).  Static design proposals on the existing rig: `use(name)` restyles rook.py's
materials and swaps the helmet, the thruster tanks and a few suit details; nothing here is wired
into the export until Matt picks one.

  brass    Cogsworth-built: oiled canvas suit, riveted brass collar and chest plate, a round brass
           diving-style helmet with a porthole, hand-cranked oxygen tanks feeding the thrusters
           through a hose to the helmet.
  shard    the Company's shard-tech suit, worn by a defector: graphite shell, violet shard cells
           in the chest and the pack, a sleek visor raised over the brow, the Company mark on the
           shoulder scratched through.
  lantern  the observatory's moon-walker: quilted cream cloth with midnight-blue trim, a glass
           bubble helmet in a brass ring, two little lanterns on the chest straps and a rolled
           star chart strapped across the pack.
"""
import numpy as np
from ew import mat
from parts import Rig
import rook
from nix import skel
import turn

_orig = dict(build=rook.build, helmet_worn=rook.helmet_worn, helmet=rook.helmet, tank=rook.tank)
STYLE = None

PALS = {
    'brass': dict(
        rk_suit=['#4E4234', '#86745A', '#B6A282', '#DCCCA8'],                    # oiled canvas
        rk_orange=['#4E3014', '#86561E', '#C08A30', '#ECC060', '#FFEDB0'],       # brass
        rk_pad=['#1E140E', '#3A2618', '#5A3C26', '#7A5636'],                     # leather
        rk_visor=['#0E1A1C', '#1E3436', '#3A5C5A', '#7AA4A0', '#DFF2EE']),       # porthole glass
    'shard': dict(
        rk_suit=['#14161F', '#262A3C', '#3C4260', '#5E668C'],                    # graphite shell
        rk_orange=['#34125A', '#6228A0', '#9454DC', '#C490FF', '#F0DCFF'],       # shard violet
        rk_pad=['#0A0A10', '#17171F', '#262632', '#3A3A4E'],
        rk_visor=['#140A24', '#2C184C', '#4C2E7E', '#8C6ACA', '#EADCFF']),
    'lantern': dict(
        rk_suit=['#5C5048', '#9A8C7A', '#CEC2A8', '#F0E8D4'],                    # quilted cream cloth
        rk_orange=['#4E3014', '#86561E', '#C08A30', '#ECC060', '#FFEDB0'],       # observatory brass
        rk_pad=['#141A38', '#24305E', '#3A4C8A', '#5E74B6'],                     # midnight-blue pads
        rk_visor=['#2A3A4A', '#5A7A8E', '#9CC0D0', '#D4EEF6', '#FFFFFF']),       # bubble glass
}
_BASE = {k: None for k in ('rk_suit', 'rk_orange', 'rk_pad', 'rk_visor')}


def use(name):
    global STYLE
    STYLE = name
    for k, tones in PALS[name].items():
        mat(k, tones)
    rook.helmet_worn = helmet_worn
    rook.helmet = helmet
    rook.tank = tank
    rook.build = build


# ------------------------------------------------------------------------------------ helmets
def _rivets(f, pts, z, tone=('brass', 4)):
    for x, y in pts:
        f.dot(x, y, tone, z=z)


def helmet_worn(f, P, hy, facing):
    side = facing not in ('S', 'N')
    fx = 6.0 if side else 0.0                      # the face's centre in this view
    with f.tagging('helmet'):
        if STYLE == 'brass':
            shell = f.ell(0.4 if side else 0, hy - 1.0, 11.6, 11.8)
            port = None if facing == 'N' else f.ell(fx + (0.6 if side else 0), hy + 2.2, 5.6 if side else 6.4, 6.0)
            sm = shell & ~port if port is not None else shell
            f.add(sm, 'rk_orange', z=46, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1))
            if port is not None:
                rim = f.ell(fx + (0.6 if side else 0), hy + 2.2, (5.6 if side else 6.4) + 1.6, 7.6) & ~port
                f.add(rim, 'rk_orange', z=46.2, rl=1, rs=1.6, flat=None, line='hard')
                f.detail(f.rect(fx - 3.5, hy - 2.5, fx - 1.5, hy - 1.5) & port, ('rk_visor', 4), z=46.3)     # the glass's glint
                _rivets(f, [(fx - 7.5, hy + 2), (fx + 7.5 if not side else fx + 6.6, hy + 2), (fx, hy - 5.2)], 46.3)
            if side:
                f.add(f.ell(-4.0, hy + 0.5, 2.6, 2.6), 'rk_visor', z=46.3, rl=1, rs=1.2, line='hard')      # small side port
                f.add(f.ell(-4.0, hy + 0.5, 3.6, 3.6) & ~f.ell(-4.0, hy + 0.5, 2.6, 2.6), 'rk_orange', z=46.25, flat=1, line='hard')
            collar = f.rect(-9.5, hy + 8.5, 9.5, hy + 11.5) & f.ell(0, hy + 10, 10.5, 3.2)
            f.add(collar, 'rk_orange', z=46.4, rl=1, rs=1.6, line='hard')
            _rivets(f, [(x, hy + 10) for x in (-6, -2, 2, 6)], 46.5, ('rk_orange', 4))
            if facing == 'N':
                f.add(f.rect(-2.5, hy - 4, 2.5, hy + 1), 'rk_pad', z=46.2, rl=1, rs=1.2, line='hard')         # the air valve
        elif STYLE == 'shard':
            shell = f.ell(0.4 if side else 0, hy - 1.5, 10.8, 11.0)
            if facing == 'S':
                hole = f.ell(0, hy + 3.0, 6.8, 6.6) | f.rect(-6.8, hy + 3.0, 6.8, hy + 12)
                vis = f.ell(0, hy - 3.0, 8.6, 3.6) & ~hole
            elif facing == 'N':
                hole = f.rect(-20, hy + 7.5, 20, hy + 20)
                vis = None
            else:
                hole = f.ell(6.2, hy + 3.4, 5.4, 6.4) | f.rect(3.0, hy + 4.0, 12, hy + 12)
                vis = f.ell(6.0, hy - 3.0, 5.4, 3.4) & ~hole
            sm = shell & ~hole
            f.add(sm, 'rk_suit', z=46, rl=1.8, rs=2.8, line='hard', cast=(0, 1, 1))
            if vis is not None:
                f.add(vis & sm, 'rk_visor', z=46.2, rl=1.4, rs=1.6, tl=0.3, line='hard')
                gx = -4 if facing == 'S' else 4
                f.detail(f.rect(gx, hy - 4, gx + 3, hy - 3), ('rk_visor', 4), z=46.3)
            for s_ in ((-1, 1) if facing in 'SN' else (-1,)):                                    # shard cells at the temples
                cx = 9.6 * s_ if facing in 'SN' else -6.5
                f.add(f.rect(cx - 0.8, hy - 2, cx + 0.8, hy + 4) & sm, 'rk_orange', z=46.25, flat=3, line=None)
        else:                                       # glass bubble in a brass ring
            bub = f.ell(0.5 if side else 0, hy - 0.5, 12.6, 12.6)
            inner = f.ell(0.5 if side else 0, hy - 0.5, 11.4, 11.4)
            f.add(bub & ~inner, 'rk_visor', z=46, flat=2, line=None)
            f.detail(f.seg(-7, hy - 5, -3, hy - 9.5), ('rk_visor', 4), z=46.1)                    # the glass's glint, up-left
            f.detail(f.seg(-8.5, hy - 1, -8, hy - 3), ('rk_visor', 4), z=46.1)
            ring = f.rect(-10, hy + 8, 10, hy + 11.5) & f.ell(0, hy + 9.8, 10.8, 3.0)
            f.add(ring, 'brass', z=46.4, rl=1, rs=1.6, line='hard')


def helmet(f, x, y, z, dim=0, visor_dir=0, r=7.6):
    with f.tagging('helmet'):
        if STYLE == 'brass':
            shell = f.ell(x, y, r, r * 0.97)
            f.add(shell, 'rk_orange', z=z, rl=1.8, rs=2.8, dim=dim, line='hard', cast=(1, 1, 1))
            if visor_dir is not None:
                px = x + (r * 0.4 * visor_dir if visor_dir else 0)
                f.add(f.ell(px, y + 0.5, r * 0.46, r * 0.46), 'rk_visor', z=z + 0.1, rl=1, rs=1.4, dim=dim, line='hard')
                f.add(f.ell(px, y + 0.5, r * 0.62, r * 0.62) & ~f.ell(px, y + 0.5, r * 0.46, r * 0.46), 'rk_orange', z=z + 0.08, flat=1,
                      dim=dim, line='hard')
            f.add(f.ell(x, y + r * 0.8, r * 0.66, r * 0.26), 'rk_orange', z=z + 0.06, rl=1, rs=1.4, dim=dim, line='hard')
        elif STYLE == 'shard':
            _orig['helmet'](f, x, y, z, dim, visor_dir, r)
            f.add(f.rect(x - 1.0, y - r, x + 1.0, y - r * 0.4) & f.ell(x, y, r, r), 'rk_orange', z=z + 0.07, flat=3, dim=dim, line=None)
            return
        else:
            f.add(f.ell(x, y, r - 0.4, r - 0.4), 'rk_visor', z=z - 0.02, rl=1.6, rs=2.6, dim=dim, line=None)  # the glass, seen through (lit up-left)
            shade = f.ell(x, y, r - 0.4, r - 0.4) & ~f.ell(x - 1.6, y - 1.6, r - 0.8, r - 0.8)
            f.add(shade, 'rk_visor', z=z - 0.015, flat=0, dim=dim, line=None)                                  # the glass's dark lower-right crescent
            f.detail(f.seg(x - r * 0.6, y + r * 0.1, x - r * 0.45, y + r * 0.5), ('rk_visor', 3 if not dim else 2), z=z + 0.04)   # a low reflection
            f.add(f.ell(x, y, r + 0.6, r + 0.6) & ~f.ell(x, y, r - 0.4, r - 0.4), 'rk_visor', z=z, flat=2, dim=dim, line=None)
            f.detail(f.seg(x - 4, y - 3, x - 2, y - 5.5), ('rk_visor', 4), z=z + 0.05)
            f.add(f.rect(x - r, y + r * 0.6, x + r, y + r * 0.6 + 2.5) & f.ell(x, y + r * 0.7, r, 2.4), 'brass', z=z + 0.06, rl=1, rs=1.4,
                  dim=dim, line='hard')


def tank(f, x, top, bot, z, dim=0, w=2.8):
    if STYLE == 'shard':
        out = _orig['tank'](f, x, top, bot, z, dim, w)
        with f.tagging('pack'):
            f.add(f.rect(x - 0.9, top + 10, x + 0.9, bot - 4), 'rk_orange', z=z + 0.07, flat=3, dim=dim, line=None)    # shard cell
        return out
    out = _orig['tank'](f, x, top, bot, z, dim, w)
    with f.tagging('pack'):
        if STYLE == 'brass':
            for yy in (top + 4, bot - 4):
                f.dot(x - w + 1, yy, ('rk_orange', 4), z=z + 0.07)
                f.dot(x + w - 1, yy, ('rk_orange', 4), z=z + 0.07)
        else:
            f.add(f.rect(x - w, top + 3, x + w, top + 4.5) & f.cap(x, top + w, x, bot - 1.5, w), 'brass', z=z + 0.07, rl=1, rs=1.4, dim=dim,
                  line=None)
    return out


# ------------------------------------------------------------------------------------ suit details
def _lantern(f, x, y, z, dim=0):
    f.add(f.rect(x - 2.2, y - 2.8, x + 2.2, y + 2.8), 'brass', z=z, rl=1, rs=1.2, dim=dim, line='hard')
    f.add(f.rect(x - 1.2, y - 1.8, x + 1.2, y + 1.8), 'rk_flame', z=z + 0.05, flat=1, dim=dim, line=None)
    f.dot(x, y, ('rk_flame', 4), z=z + 0.06)
    f.dot(x, y - 3.5, ('brass', 1), z=z)


def build(f, facing, P):
    _orig['build'](f, facing, P)
    R = Rig(f, facing)
    R.body_half = 12.0
    S = skel(R, P)
    T, b, ub = S['T'], S['b'], S['ub']
    side = R.side
    vf = ('N' if R.back else 'S') if R.diag else facing          # turn in-betweens: the S or N details turned
    tw_ = turn.Warp(f, R, (S['sx'] + S['hx']) / 2, 11.5, 8.5, vf) if R.diag else None
    if tw_:
        tw_.__enter__()
    try:
        _details(f, T, b, ub, vf, side)
    finally:
        if tw_:
            tw_.__exit__(None, None, None)


def _details(f, T, b, ub, facing, side):
    if STYLE == 'brass':
        if facing == 'S':
            plate = T.rect(-6.5, -45 + ub, 6.5, -39 + ub) & T.ell(0, -42 + ub, 7.5, 4.0)
            T.add(plate, 'rk_orange', z=26.5, rl=1.2, rs=1.8, line='hard', cast=(0, 1, 1))
            _rivets(T, [(-5, -42 + ub), (5, -42 + ub), (0, -40 + ub)], 26.6, ('rk_orange', 4))
            T.add(T.cap(-10.5, -44 + ub, -6.0, -50 + ub, 1.4), 'rk_pad', z=26.4, rl=1, rs=1.2, line='hard')       # the air hose
        elif side:
            T.add(T.cap(-6.0, -46 + ub, 2.0, -50 + ub, 1.4), 'rk_pad', z=27, rl=1, rs=1.2, line='hard')
            T.add(T.rect(-12.5, -46 + ub, -11, -42 + ub), 'rk_orange', z=2.5, flat=2, line='hard', tag='pack')     # the crank's arm
            T.add(T.ell(-12.8, -41.5 + ub, 1.6, 1.6), 'rk_pad', z=2.6, rl=1, rs=1, line='hard', tag='pack')         # and its knob
        _rivets(T, [(x, -27.5 + b) for x in ((-9, -4, 4, 9) if not side else (-6, 0, 6))], 22.6, ('rk_orange', 4))
    elif STYLE == 'shard':
        if facing == 'S':
            T.add(T.rect(-2.0, -44 + ub, 2.0, -38 + ub), 'rk_orange', z=26.5, flat=3, line='hard')                   # the chest cell
            T.dot(0, -42 + ub, ('rk_orange', 4), z=26.6)
            T.add(T.rect(-12, -46 + ub, -8, -43 + ub), 'gunmetal', z=36, flat=2, line=None)                          # the mark ...
            T.detail(T.seg(-12, -46 + ub, -8.5, -43 + ub) | T.seg(-12, -43 + ub, -8.5, -46 + ub), ('rk_pad', 0), z=36.1)   # ... scratched out
        elif side:
            T.add(T.rect(4.5, -44 + ub, 7.0, -38 + ub), 'rk_orange', z=26.5, flat=3, line='hard')
    else:
        # quilting over the cloth, two lanterns on the chest straps, the star chart across the pack
        w = 12.0 if not side else 9.6
        tor = (T.ell(0, -37 + ub, w + 0.5, 10.5) | T.rect(-w, -40 + ub, w, -29 + b)) & (T.Y > -43.5 + ub)
        for k in range(6):                                   # quilted channels, stitched across the cloth
            y = -42 + ub + 3.0 * k
            if y < -29.5 + b:
                T.detail(T.rect(-w, y, w, y + 1) & tor, ('rk_suit', 1), z=20.5)
        if facing == 'S':
            for x in (-6.5, 6.5):
                _lantern(T, x, -40 + ub, 34.5)
        elif side:
            _lantern(T, 5.5, -40 + ub, 34.5)
            with f.tagging('pack'):
                T.add(T.ell(-12.5, -55 + ub, 3.0, 3.0), 'rk_suit', z=2.8, rl=1, rs=1.4, line='hard')          # the chart roll, end on
                T.add(T.ell(-12.5, -55 + ub, 1.4, 1.4), 'rk_orange', z=2.9, flat=2, line=None)
        else:
            with f.tagging('pack'):
                roll = T.cap(-11, -53 + ub, 11, -53 + ub, 2.8)
                T.add(roll, 'rk_suit', z=48, rl=1.2, rs=1.8, line='hard', cast=(1, 1, 1))
                T.add(T.rect(-3, -56 + ub, 3, -50 + ub) & roll, 'rk_orange', z=48.1, rl=1.2, rs=1.8, line=None)
                for x in (-7.0, 7.0):
                    T.add(T.rect(x - 0.6, -56 + ub, x + 0.6, -50 + ub), 'rk_pad', z=48.2, flat=1, line=None)

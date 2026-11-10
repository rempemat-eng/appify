"""The woodland camp's bramble den: a low mound of woven sticks and bramble canes around a dark
hollow, three Starfall shards stuck in the weave and glowing, a few leaves.  It is the camp's
prop set: the den (lit while shardstruck creatures are about; 'calm' once all are freed: the
shards are gone and the weave has a few flowers), and a small shard-lit bramble clump to place
around it.  Drawn from the same cast shading (upper-left light, lit top, mid and dark planes)
on the same 160x144 cell with the foot pivot at the den's front lip.

python3 den.py writes out/den/ (PNGs + manifest.json)."""
import json
import math
import os
import numpy as np
from ew import Fig, mat, to_img
import critter as C
import anim

mat('weave', ['#2A2018', '#4A3C2C', '#6E5E46', '#948262', '#B8A884'])
mat('bloom', ['#7A3A5A', '#B85E86', '#E88EB0', '#FFC8DA'])

ID = 'den'


def _weave(X, Y, t):
    out = t.copy()
    a = (np.floor(X + Y * 1.6) % 5 == 0)
    b = (np.floor(X - Y * 1.6) % 7 == 0)
    out[a & (t >= 1)] = t[a & (t >= 1)] - 1
    out[b & ~a & (t <= 3)] = t[b & ~a & (t <= 3)] + 1
    return out


def _sticks(X, Y, t):
    """Woven sticks: 4-px strokes laid in alternating slants, one tone down, with a lit end."""
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    row = yi // 3
    lx = (xi + row * 2) % 7
    ly = yi % 3
    slant = (row % 2) * 2 - 1
    out = t.copy()
    stroke = (ly == 1) & (lx <= 3) & (t >= 1) & (t <= 3)
    stroke |= (ly == 2) & (lx == np.where(slant > 0, 3, 0)) & (t >= 1) & (t <= 3)
    lit = (ly == 0) & (lx == 4) & (t >= 2) & (t <= 3)
    out[stroke] = t[stroke] - 1
    out[lit] = t[lit] + 1
    return out


def den(P):
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.despeckle = True
    gy = 0.0
    # the mound: a low dome of woven sticks, a darker skirt where it meets the ground
    # thickness: a steep woven wall in shade all round the front, under a domed top that catches the
    # light (lit upper-left plane, mid, and the shaded front edge where the top turns into the wall)
    wall = (f.ell(0, gy - 9, 35, 9) | f.ell(-16, gy - 7, 19, 7) | f.ell(17, gy - 7, 18, 7)) & (f.Y < gy - 1)
    f.add(wall, 'weave', z=9.5, flat=1, line='hard', tonemap=_sticks, tag='den')
    top = f.ell(0, gy - 18, 33, 15) | f.ell(-13, gy - 14, 17, 10) | f.ell(15, gy - 15, 16, 10)
    f.add(top, 'weave', z=10, rl=2.6, rs=2.2, vgrad=0.35, line='hard', deep=True, tonemap=C.planes(f, top, _sticks, lit=0.3, dark=0.8), tag='den')
    mound = wall | top
    # the hollow: a dark arched opening at the front
    hollow = (f.ell(2, gy - 8, 9.5, 9) & (f.Y < gy - 2))
    f.add(hollow, 'crack', z=11, flat=0, line='hard', tag='den')
    f.add(f.ell(2, gy - 9, 7, 5) & (f.Y < gy - 4), 'crack', z=11.1, flat=1, line=None)
    # sticks poking out of the weave and bramble canes arching over
    for x0, y0, x1, y1 in ((-30, -14, -38, -22), (26, -18, 36, -25), (-12, -29, -16, -37), (14, -29, 20, -36), (-6, -3, -12, 1)):
        f.add(f.cap(x0, gy + y0, x1, gy + y1, 1.2, 0.8), 'weave', z=12, rl=1, rs=1, line='hard')
    pts_sets = [[(-26 + 9 * i, gy - 22 - 9 * math.sin(math.pi * i / 6)) for i in range(7)],
                [(-20 + 7 * i, gy - 26 - 6 * math.sin(math.pi * i / 6)) for i in range(7)]]
    for pts in pts_sets:
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            f.add(f.cap(x0, y0, x1, y1, 1.0), 'thorn', z=13, rl=0.8, rs=1, line='hard')
        for (x, y) in pts[1:6:2]:
            f.add(f.poly([(x - 1.5, y), (x, y - 3), (x + 1.5, y)]), 'thorn', z=13.1, rl=0.8, rs=1, line='hard')
    for lx, ly in ((-22, -24), (8, -33), (24, -22), (-30, -8)):
        f.add(f.ell(lx, gy + ly, 2.6, 1.4), 'leafg', z=13.2, rl=1, rs=1, line='hard')
    if P.get('calm'):
        for bx, by in ((-14, -30), (10, -31), (27, -15), (-28, -14)):
            f.add(f.ell(bx, gy + by, 1.8, 1.6), 'bloom', z=13.3, rl=1, rs=1, line='hard')
            f.dot(bx, gy + by, ('gold', 3), z=13.4)
    else:
        # three shards stuck in the weave, glowing (the glow ring pulses with P['fx'])
        R = C.Rig(f, 'S')
        for (x, y, ax, sz) in ((-17, -20, -0.5, 10.0), (19, -22, 0.45, 11.0), (-3, -30, 0.1, 9.0)):
            Q = C.P0(fx=P.get('fx', 0))
            with f.tagging('shard'):
                C.shard(f, R, (0.0, -y - 1.0, x), (0.0, 1.0, ax), sz, Q, 20)
    return f


def clump(P):
    """A small shard-lit bramble clump to scatter around the camp."""
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.despeckle = True
    f.add((f.ell(0, -7, 13, 7.5) | f.ell(-7, -5, 7, 5)) & (f.Y < -1), 'leafg', z=10, rl=2.0, rs=2.8, vgrad=0.5, tonemap=_weave, line='hard', deep=True)
    for k in range(3):
        a = -0.9 + 0.9 * k
        pts = [(math.sin(a) * 12 * t, -8 - 12 * math.sin(math.pi * t * 0.8) * (1 - 0.3 * abs(a))) for t in [i / 5 for i in range(6)]]
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            f.add(f.cap(x0, y0, x1, y1, 0.9), 'thorn', z=12, rl=0.8, rs=1, line='hard')
    if not P.get('calm'):
        R = C.Rig(f, 'S')
        C.shard(f, R, (0.0, 9.0, 2.0), (0.0, 1.0, 0.3), 7.0, C.P0(fx=P.get('fx', 0)), 20)
    else:
        f.add(f.ell(3, -12, 1.8, 1.6), 'bloom', z=13, rl=1, rs=1, line='hard')
    return f


def seed(P):
    """The toad's spat thorn seed (the shot), pointing east; the game rotates it to its path."""
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.add(f.ell(0, -8, 3.4, 2.4), 'weave', z=10, rl=1, rs=1.4, line='hard')
    f.add(f.poly([(2.5, -9.5), (6.5, -8), (2.5, -6.5)]), 'thorn', z=11, rl=0.8, rs=1, line='hard')
    f.add(f.ell(-3.2, -9.4 + P.get('fx', 0) * 0.8, 1.8, 1.0), 'leafg', z=11, rl=1, rs=1, line='hard')
    return f


def shardfx(P):
    """The Starfall shard on its own, for the freed effect: the runtime lifts it out of the
    creature, tumbles it and fades it (finite; skipped under reduced motion)."""
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    R = C.Rig(f, 'S')
    C.shard(f, R, (0.0, 4.0, 0.0), (0.0, 1.0, 0.0), 8.0, C.P0(), 20)
    return f


# strips for the game (game/assets/enemies/): the cell cropped to a box, foot pivot inside it
CROPS = {'den': (24, 84, 136, 140), 'clump': (56, 110, 104, 140), 'seed': (70, 120, 90, 136), 'shard': (72, 118, 88, 134)}


def export(outdir=None):
    outdir = outdir or os.path.join(anim.ROOT, 'out', ID)
    os.makedirs(outdir, exist_ok=True)
    man = dict(id=ID, frame_size=list(anim.CELL), foot_pivot=list(anim.PIVOT), props={})
    for name, fn in (('den', den), ('clump', clump)):
        entry = {}
        for clip, frames in (('lit', [dict(fx=i) for i in range(3)]), ('calm', [dict(calm=True)])):
            files = []
            for i, P in enumerate(frames):
                a = fn(P).render()
                fn_ = '%s_%s_%02d.png' % (name, clip, i)
                to_img(a).save(os.path.join(outdir, fn_))
                files.append(fn_)
            entry[clip] = dict(frames=files, fps=6 if clip == 'lit' else 1, loop=True)
        man['props'][name] = entry
    from PIL import Image
    gdir = os.path.join(outdir, 'game')
    os.makedirs(gdir, exist_ok=True)
    for name, fn in (('den', den), ('clump', clump), ('seed', seed), ('shard', shardfx)):
        x0, y0, x1, y1 = CROPS[name]
        for clip, frames in (('lit', [dict(fx=i) for i in range(3)]), ('calm', [dict(calm=True)])):
            if name in ('seed', 'shard') and clip == 'calm':
                continue
            if name == 'seed':
                frames = [dict(fx=0), dict(fx=1)]
            if name == 'shard':
                frames = [dict()]
            ims = [Image.fromarray(fn(P).render()).crop((x0, y0, x1, y1)) for P in frames]
            strip = Image.new('RGBA', ((x1 - x0) * len(ims), y1 - y0), (0, 0, 0, 0))
            for i, im in enumerate(ims):
                strip.paste(im, (i * (x1 - x0), 0))
            strip.save(os.path.join(gdir, '%s_%s.png' % (name, clip) if name not in ('seed', 'shard') else name + '.png'))
        man['props'].setdefault(name, {})['crop'] = [x0, y0, x1, y1]
        man['props'][name]['pivot_in_crop'] = [anim.PIVOT[0] - x0, anim.PIVOT[1] - y0]
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1)
    return man


if __name__ == '__main__':
    print(export())

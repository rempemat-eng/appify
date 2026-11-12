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


# the den at its creatures' scale (10 Nov audit D1, 12 Nov D1r): an uneven heap about 132 x 78 px
# whose arch (52 x 56, about 51 px clear inside the lip cane) clears the tallest creature that lives
# in it (the boarlet from behind, 46 px) with a margin
DEN_W, DEN_H = 64.0, 76.0          # the heap's half width and its height above the ground
MOUTH = (-2.0, -28.0, 26.0, 28.0)  # centre x, centre y, half width, half height of the arch

mat('cane', ['#24121A', '#46222A', '#6C3A36', '#925A44', '#B47A56'])    # bramble canes: wine-brown, lit tan
mat('deadcane', ['#3A2E26', '#5E5040', '#857560', '#A89A80', '#C4B89C'])  # old canes, bleached
# the woodland's leaf ramps (art/house-palette.json 'leaf', 'leaf_warm'), tones 1 to 5
mat('wleaf', ['#194B28', '#3A6B3A', '#5C8A4C', '#83A15A', '#A8B471'])
mat('wleafw', ['#2B5120', '#4B712F', '#6D9041', '#93A751', '#B6BA6D'])
mat('dirt', ['#441F23', '#673D37', '#885C4B', '#A87C60', '#C39771', '#D6B187'])   # 'path'
mat('soil', ['#261118', '#432B2A', '#5F463D', '#7A6250', '#947B60', '#AA9373'])   # 'earth'
mat('turf', ['#234325', '#436333', '#648445', '#86A458', '#ACBC69', '#CFCF84'])   # 'grass': a shadow on the woodland's grass


def _heap_y(x):
    """The heap's top at x (pivot space, y up negative): highest left of centre, slumping to the
    east, uneven where canes bunch (no perfect shape, art-faults 3)."""
    u = x / DEN_W
    if abs(u) >= 1:
        return 0.0
    skew = 1.0 + 0.10 * (-u)                                   # higher on the left
    slump = 1.0 - 0.22 * max(0.0, u - 0.35) / 0.65             # the east end slumps
    bumps = 1.6 * math.sin(x * 0.21 + 1.0) + 1.1 * math.sin(x * 0.53)
    return -(DEN_H * math.cos(math.pi * u / 2) ** 0.55 * skew * slump + bumps * math.cos(math.pi * u / 2))


def _heap_mask(f):
    xs = f.X[0]
    tops = np.array([_heap_y(x) for x in xs])
    return (f.Y >= tops[None, :]) & (f.Y < -0.5) & (np.abs(f.X) < DEN_W)


def _cane(f, pts, r, z, tag='den', tm=None, m='cane'):
    """One woven bramble cane, 3 to 5 px wide along pts, lit on its top edge and dark under it; it
    drops a one-tone shade on the canes it lies over (so where one passes under another it darkens
    beside the crossing)."""
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts[:-1], pts[1:])):
        zz = z[k] if isinstance(z, (list, tuple)) else z
        f.add(f.cap(x0, y0, x1, y1, r, r * 0.95), m, z=zz, rl=1.6, rs=1.3, tl=0.15, vgrad=0.5, line='hard', deep=True,
              cast=(1, 1, 1), tag=tag, tonemap=tm)


def _rng(seed):
    return np.random.default_rng(seed)


def den(P):
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.despeckle = True
    heap = _heap_mask(f)
    # the ground: a 1 px contact line where the cane ends meet it and a cast shadow east and down
    # in two ramp steps (no plinth line)
    f.add(f.ell(8, 0.5, DEN_W + 3, 4.5) & ~heap & (f.Y > -2), 'turf', z=1, flat=1, line=None, noout=True)
    f.add(f.ell(6, 0.0, DEN_W + 1, 2.6) & ~heap & (f.Y > -2), 'turf', z=1.1, flat=0, line=None, noout=True)
    # the interior, seen only in small pockets between canes
    pl = C.planes(f, heap, None, lit=0.40, dark=0.60)
    f.add(heap, 'cane', z=9, flat=0, line='hard', tag='den')
    # canes laid in overlapping arcs that follow the heap: each a long wavy curve over part of it,
    # at a height through the heap, crossing its neighbours at shallow angles, over and under
    g = _rng(7)
    n = 0
    for row in range(15):
        h = 0.03 + 0.066 * row                                # how far up the heap (0 ground, 1 crest)
        u = -1.08 + 0.25 * g.random()
        while u < 1.0:
            span = 0.55 + 0.6 * g.random()
            tilt = (0.35 + 0.6 * g.random()) * (1 if (row + n) % 2 else -1)
            pts = []
            for t in np.linspace(0, 1, 9):
                uu = u + span * t
                x = uu * DEN_W
                if abs(uu) > 1.02:
                    continue
                y = _heap_y(x) * (1 - h) + (-1.5) * h + tilt * 8 * (t - 0.5) + 1.0 * math.sin(6 * t + n)
                pts.append((x, min(-2.0, max(y, _heap_y(x) + 1.5))))
            if len(pts) >= 3:
                zs = [10 + 0.3 * ((k + n) % 3) * 0.3 + 0.01 * n for k in range(len(pts) - 1)]
                _cane(f, pts, 1.6 + 0.45 * (n % 3), zs, tm=pl, m='deadcane' if n % 9 == 4 else 'cane')
            u += span * (0.55 + 0.25 * g.random())                 # the next cane overlaps this one
            n += 1
    # the crown: canes bunched along the top so the silhouette is cane, uneven
    top = [(x, _heap_y(x) + 2.0) for x in np.linspace(-DEN_W + 4, DEN_W - 4, 15)]
    _cane(f, top, 2.2, [11.0 + 0.2 * (k % 2) for k in range(14)], tm=pl)
    # the mouth: an arch round a dark hollow
    mx, my, mw, mh = MOUTH
    arch = f.ell(mx, my, mw, mh) & (f.Y < -0.5)
    f.add(arch, 'crack', z=12, flat=1, line='hard', tag='den')
    inner = arch & ~f.ell(mx - 5, my + 3, mw - 3, mh - 4) & (f.X > mx - 6) & (f.Y > my - mh + 6) & (f.Y < -7)
    f.add(inner, 'cane', z=12.1, rl=2.0, rs=2.5, vgrad=0.8, line=None, dim=1, tonemap=_sticks, tag='den')
    f.add(arch & (f.Y < my - mh + 8), 'crack', z=12.2, flat=0, line=None, tag='den')             # under the near lip
    # the trodden floor: lit at the threshold, darker going in, fading to the dark 6 to 8 px in
    def trodden(X, Y, t):
        # the floor's wear: scuffs a tone darker and a few lit grains, tied to the rows
        t = t.copy()
        xi, yi = np.floor(X * 1.0).astype(int), np.floor(Y).astype(int)
        scuff = ((xi * 5 + yi * 3) % 11 == 0)
        grain = ((xi * 7 + yi * 2) % 13 == 0)
        t[scuff & (t >= 1)] -= 1
        t[grain & (t <= 3)] += 1
        return t
    for y0, y1, m, tone in ((-1.5, 0.0, 'dirt', 4), (-3.5, -1.5, 'dirt', 3), (-6.0, -3.5, 'dirt', 2), (-8.5, -6.0, 'crack', 1)):
        f.add(arch & (f.Y >= y0) & (f.Y < y1), m, z=12.3, flat=tone, line=None, tag='den', tonemap=trodden if m == 'dirt' else None)
    for lx, ly, c in ((-10, -2, ('thorn', 2)), (-9, -2, ('thorn', 1)), (6, -4, ('wleafw', 2)), (7, -4, ('wleafw', 1))):
        f.dot(lx, ly, c, z=12.4)                                                                    # litter
    lip = [(mx + mw * math.cos(a), my - mh * math.sin(a) - 0.5) for a in np.linspace(0.04, math.pi - 0.04, 13)]
    _cane(f, lip, 2.3, [13.0 + 0.2 * (k % 2) for k in range(12)], tm=pl)
    # thorned canes arching out of the heap (they break the silhouette)
    for (x0, x1, lift, side) in ((-54, 10, 4.0, 1), (-8, 56, 3.0, -1), (40, 66, 6.0, 1)):
        pts = [(x0 + (x1 - x0) * t, min(_heap_y(x0 + (x1 - x0) * t), 0.0) - lift * math.sin(math.pi * t) + 1.0) for t in np.linspace(0, 1, 10)]
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            f.add(f.cap(a, b, c, d, 1.1, 1.0), 'thorn', z=14, rl=0.8, rs=1, line='hard', tag='den')
        for (x, y) in pts[1:9:2]:
            f.add(f.poly([(x - 1.6, y), (x + 0.6 * side, y - 3.5), (x + 1.6, y)]), 'thorn', z=14.1, rl=0.8, rs=1, line='hard', tag='den')
    # leaf clusters in three sizes and turns, from both leaf siblings, filling the gaps
    for k, (cx, cy, sc) in enumerate(((-44, -30, 1.3), (-24, -56, 1.0), (22, -50, 1.4), (46, -24, 0.8), (-54, -9, 0.9),
                                     (30, -12, 0.7), (-36, -46, 0.8), (6, -66, 0.9), (50, -8, 1.0))):
        m = 'wleaf' if k % 2 == 0 else 'wleafw'
        rot = 0.7 * k
        for (dx, dy, ang) in ((0, 0, 0.0), (-2.6, 1.2, 2.2), (2.6, 1.0, 0.9), (0.3, -2.4, 1.5)):
            cxx = cx + sc * (dx * math.cos(rot) - dy * math.sin(rot))
            cyy = cy + sc * (dx * math.sin(rot) + dy * math.cos(rot))
            f.add(f.rell(cxx, cyy, 2.8 * sc, 1.7 * sc, ang + rot), m, z=14.2 + 0.01 * k, rl=1, rs=1.2, line='hard', tag='den')
    # grass and fern at the foot
    for (gx, h, lean) in ((-60, 5, -1), (-57, 4, 0), (-47, 3, 1), (52, 5, 1), (58, 4, 0), (34, 3, -1)):
        for d in (0, 1):
            f.add(f.cap(gx + d, -0.5, gx + d + lean * (1 + d), -h + d, 0.55), 'wleafw', z=15, flat=2 + (d == 0), line=None)
    if P.get('calm'):
        for bx, by in ((-26, -58), (14, -60), (42, -36), (-48, -36)):
            f.add(f.ell(bx, by, 1.6, 1.6), 'bloom', z=15.3, rl=1, rs=1, line='hard')
            f.dot(bx, by, ('gold', 3), z=15.4)
    else:
        # three shards stuck in the weave, the glint on one facet changing over the three drawings
        R = C.Rig(f, 'S')
        for (x, y, ax, sz) in ((-32, -50, -0.5, 11.0), (34, -46, 0.45, 12.0), (2, -64, 0.1, 10.0)):
            Q = C.P0(fx=P.get('fx', 0))
            with f.tagging('shard'):
                C.shard(f, R, (0.0, -y - 1.0, x), (0.0, 1.0, ax), sz, Q, 20)
        gx, gy = ((-34, -56), (33, -53), (1, -70))[P.get('fx', 0) % 3]
        f.dot(gx, gy, ('shardglow', 4), z=21)
    return f


def clump(P):
    """A small shard-lit bramble clump to scatter around the camp (10 Nov audit L1, 12 Nov L1r):
    four domed leaf clusters of different sizes in the woodland's leaf ramps, each with a lit cap,
    a mid body and a dark U under it, dark gaps between them, a run of bumps about 1.8 times wider
    than tall; three thorned canes arching out (one bent back to the ground), a contact line and a
    cast shadow east and down."""
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.despeckle = True
    f.add(f.ell(3, 0.5, 19, 3.2) & (f.Y > -1.5), 'soil', z=1, flat=2, line=None, noout=True)      # cast shadow
    f.add(f.ell(1, 0.0, 15, 1.8) & (f.Y > -1.5), 'soil', z=1.1, flat=1, line=None, noout=True)    # contact line
    # canes: 2 px curves with a lit top edge and thorns along them
    for k, (pts, zc) in enumerate((([(-5, -7), (-8, -14), (-12, -18), (-16, -18)], 9.0),          # up and out, ending in the air
                                   ([(3, -8), (6, -16), (10, -19), (14, -18)], 9.0),
                                   ([(10, -4), (15, -8), (19, -7), (22, -2)], 12.5))):            # bent back to the ground
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            f.add(f.cap(x0, y0, x1, y1, 0.9, 0.8), 'thorn', z=zc, rl=0.9, rs=0.8, tl=0.2, line='hard')
        for (x, y) in pts[1:-1]:
            f.add(f.poly([(x - 1.0, y), (x + 0.3, y - 2.2), (x + 1.0, y)]), 'thorn', z=zc + 0.05, rl=0.8, rs=1, line='hard')
    # the leaf clusters, back to front
    for k, (cx, cy, rx, ry, m) in enumerate(((-1, -10.5, 5.5, 4.5, 'wleaf'), (-10, -5.0, 6.0, 4.6, 'wleafw'),
                                             (5, -5.2, 7.0, 5.0, 'wleaf'), (15, -3.4, 4.2, 3.2, 'wleafw'))):
        mm = f.ell(cx, cy, rx, ry) & (f.Y < -0.5)
        f.add(mm, m, z=10 + 0.2 * k, rl=2.2, rs=1.8, tl=0.3, vgrad=0.7, line='hard', deep=True, tonemap=_leaflets(cx, cy))
    gx, gy = 4, -9                                                                                # the glint on the biggest
    f.dot(gx, gy, ('wleaf', 4), z=13)
    f.dot(gx + 1, gy, ('wleaf', 4), z=13)
    if not P.get('calm'):
        R = C.Rig(f, 'S')
        C.shard(f, R, (0.0, 12.0, -2.0), (0.0, 1.0, 0.3), 7.0, C.P0(fx=P.get('fx', 0)), 20)
        sx, sy = ((-3, -18), (-2, -16), (-1, -17))[P.get('fx', 0) % 3]
        f.dot(sx, sy, ('shardglow', 4), z=21)
    else:
        for bx, by in ((-3, -14), (8, -9)):
            f.add(f.rect(bx, by, bx + 2, by + 2), 'bloom', z=13, flat=2, line='hard')
            f.dot(bx + 1, by + 1, ('bloom', 0), z=13.1)
    return f


def _leaflets(cx, cy):
    """Single leaves inside a cluster, on its mid plane only: a leaf is a 2 px stroke a tone down
    with a lit tip pixel a tone up, set on a loose ring round the cluster's centre (form, not grain)."""
    def tm(X, Y, t):
        t = t.copy()
        a = np.arctan2(Y - cy, X - cx)
        r = np.hypot(X - cx, (Y - cy) * 1.3)
        ring = (np.abs(r - 3.0) < 0.7) & (np.floor(a * 2.6) % 2 == 0)
        tip = (np.abs(r - 3.9) < 0.5) & (np.floor(a * 2.6) % 2 == 0) & (np.floor(a * 5.2) % 2 == 0)
        t[ring & (t == 2)] = 1
        t[tip & (t == 2)] = 3
        return t
    return tm


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
CROPS = {'den': (12, 50, 156, 140), 'clump': (56, 110, 104, 140), 'seed': (70, 120, 90, 136), 'shard': (72, 118, 88, 134)}


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

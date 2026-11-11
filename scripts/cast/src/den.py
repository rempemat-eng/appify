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


# the den at its creatures' scale (10 Nov audit, D1): a mound about 120 x 62 px whose mouth (46 x 38)
# a boarlet or a tortoise (40 to 45 px tall, 26 to 40 wide) can go through
DEN_W, DEN_H = 60.0, 50.0          # the dome's half width and its height above the lip line
MOUTH = (0.0, -19.0, 23.0, 19.5)   # centre x, centre y, half width, half height of the arch

mat('cane', ['#24121A', '#46222A', '#6C3A36', '#925A44', '#B47A56'])    # bramble canes: wine-brown, lit tan


def _cane(f, pts, r, z, tag='den', tm=None):
    """One woven bramble cane: a band 3 to 5 px wide along pts, shaded on its own (lit top edge,
    dark underside), its ends tapering; z per segment lets canes pass over and under each other."""
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts[:-1], pts[1:])):
        zz = z[k] if isinstance(z, (list, tuple)) else z
        f.add(f.cap(x0, y0, x1, y1, r, r), 'cane', z=zz, rl=1.8, rs=1.2, tl=0.12, vgrad=0.5, line='hard', deep=True, tag=tag, tonemap=tm)


def _dome_y(x, lift=0.0):
    """The mound's surface height at x (pivot space, y up negative)."""
    u = max(-1.0, min(1.0, x / DEN_W))
    return -2.0 - (DEN_H + lift) * math.cos(math.pi * u / 2) ** 0.6


def _dome_mask_y(f):
    u = np.clip(f.X / DEN_W, -1.0, 1.0)
    return np.where(np.abs(f.X) <= DEN_W, -2.0 - DEN_H * np.cos(np.pi * u / 2) ** 0.6, 1e9)


def den(P):
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.despeckle = True
    # the body of the mound under the canes: the dark gaps of the weave, shaded as one dome so the
    # back reads lit (upper left) and the front base sits in shade
    body = (f.Y < -1) & (f.Y >= _dome_mask_y(f))
    # the dome's planes (lit upper left, mid, shaded lower right) carried by every cane on it
    pl = C.planes(f, body, None, lit=0.38, dark=0.62)
    f.add(body, 'weave', z=9, rl=3.0, rs=4.0, vgrad=0.7, line='hard', deep=True, tonemap=lambda X, Y, t: np.maximum(pl(X, Y, t) - 1, 0), tag='den')
    # woven canes: two families crossing over the dome, over and under at alternate crossings (the
    # segment's z flips each step, so at a crossing one cane's edge line shows on the other: the dark gap)
    # each cane a gentle diagonal across the dome, bowing with its curve, 10 px apart
    for fam, sgn in ((0, 1), (1, -1)):
        for j in range(-9, 10):
            pts = []
            for x in np.linspace(-DEN_W - 2, DEN_W + 2, 25):
                y = -2.0 - 0.0 + sgn * 0.62 * x + j * 10.0 + 4.0 * fam - 0.18 * (_dome_y(x) + 2.0)
                inside = _dome_y(x) + 1.0 <= y <= -2.5
                if inside:
                    pts.append((x, y))
                elif pts:
                    break
            if len(pts) >= 2:
                zs = [10 + 0.2 * ((k + j + fam) % 2) + 0.05 * fam for k in range(len(pts) - 1)]
                _cane(f, pts, 1.7 + 0.5 * ((j + fam) % 2), zs, tm=pl)
    # thick rim canes framing the dome's top edge (the silhouette is cane, not a smooth curve)
    top = [(x, _dome_y(x) + 1.5) for x in np.linspace(-DEN_W + 2, DEN_W - 2, 16)]
    _cane(f, top, 2.2, [10.6] * 15, tm=pl)
    # the mouth: an arch of canes round a dark hollow
    mx, my, mw, mh = MOUTH
    arch = f.ell(mx, my, mw, mh) & (f.Y < -1)
    f.add(arch, 'crack', z=11, flat=1, line='hard', tag='den')
    # the inner wall on the far side catches the light coming in over the near lip from the upper
    # left: a lit crescent on the hollow's right and back
    inner = arch & ~f.ell(mx - 5, my + 3, mw - 3, mh - 4) & (f.X > mx - 6) & (f.Y > my - mh + 5)
    f.add(inner, 'cane', z=11.1, rl=2.0, rs=2.5, vgrad=0.8, line=None, dim=1, tonemap=_sticks, tag='den')
    # the near lip's shadow: a dark band under the arch's top, and the floor of the hollow
    f.add(arch & (f.Y < my - mh + 7), 'crack', z=11.2, flat=0, line=None, tag='den')
    f.add(arch & (f.Y > -6), 'crack', z=11.2, flat=0, line=None, tag='den')
    lip = [(mx + mw * math.cos(a), my - mh * math.sin(a) - 0.5) for a in np.linspace(0.05, math.pi - 0.05, 11)]
    _cane(f, lip, 2.4, [12.0 + 0.2 * (k % 2) for k in range(10)])
    # bramble canes arching over the mound with thorns that break the silhouette
    for (x0, x1, lift, side) in ((-50, 18, 1.5, 1), (-14, 52, 1.0, -1), (-58, -20, 0.5, 1)):
        pts = [(x0 + (x1 - x0) * t, _dome_y(x0 + (x1 - x0) * t, lift) + 1.0 - 1.5 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 9)]
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            f.add(f.cap(a, b, c, d, 1.1, 1.0), 'thorn', z=13, rl=0.8, rs=1, line='hard', tag='den')
        for (x, y) in pts[1:8:2]:
            f.add(f.poly([(x - 1.6, y), (x + 0.6 * side, y - 3.5), (x + 1.6, y)]), 'thorn', z=13.1, rl=0.8, rs=1, line='hard', tag='den')
    # leaves in clusters of three to four, each leaf lit on its upper left
    for cx, cy in ((-42, -30), (-18, -46), (28, -42), (46, -22), (-54, -8)):
        for dx, dy, ang in ((-2.5, 0.5, -2.5), (2.5, 0.5, -0.6), (0, -2.0, -1.57), (0.5, 1.8, 0.2)):
            f.add(f.rell(cx + dx, cy + dy, 2.8, 1.7, ang), 'leafg', z=13.2, rl=1, rs=1.2, line='hard', tag='den')
    if P.get('calm'):
        for bx, by in ((-24, -48), (14, -50), (40, -32), (-46, -34)):
            f.add(f.ell(bx, by, 1.8, 1.6), 'bloom', z=13.3, rl=1, rs=1, line='hard')
            f.dot(bx, by, ('gold', 3), z=13.4)
    else:
        # three shards stuck in the weave, glowing
        R = C.Rig(f, 'S')
        for (x, y, ax, sz) in ((-30, -40, -0.5, 11.0), (34, -38, 0.45, 12.0), (4, -50, 0.1, 10.0)):
            Q = C.P0(fx=P.get('fx', 0))
            with f.tagging('shard'):
                C.shard(f, R, (0.0, -y - 1.0, x), (0.0, 1.0, ax), sz, Q, 20)
    return f


def clump(P):
    """A small shard-lit bramble clump to scatter around the camp (10 Nov audit, L1): four or five
    leaf clusters with lit caps and dark undersides, bramble canes with thorns arching out of it,
    and a contact shadow at its foot."""
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY)
    f.despeckle = True
    f.add(f.ell(0, -1.5, 17, 2.6) & (f.Y < 0), 'crack', z=5, flat=1, line=None, noout=True)    # contact shadow
    # canes first, arching out of the clump (some behind the leaves, some in front)
    for k, (a, h, zc) in enumerate(((-1.0, 14, 9), (0.15, 17, 9), (0.95, 13, 9.2))):
        pts = [(math.sin(a) * 15 * t, -3 - h * math.sin(math.pi * t * 0.85) * (1 - 0.25 * abs(a))) for t in [i / 6 for i in range(7)]]
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            f.add(f.cap(x0, y0, x1, y1, 1.0, 0.9), 'thorn', z=zc, rl=0.8, rs=1, line='hard')
        for (x, y) in pts[2:7:2]:
            f.add(f.poly([(x - 1.3, y), (x + 0.4, y - 3.0), (x + 1.3, y)]), 'thorn', z=zc + 0.05, rl=0.8, rs=1, line='hard')
    # leaf clusters merged into one leafy mass, shaded as one volume (few value steps on so small a
    # thing), each cluster then given its lit cap (upper left) and the dark underside where it
    # overhangs the cluster below
    cl = ((-8, -6, 7.5, 5.5), (5, -7, 8.0, 6.0), (-1, -13, 7.0, 5.0), (12, -3.5, 5.5, 4.0), (-14, -3, 5.0, 3.6))
    ms = [f.ell(cx, cy, rx, ry) & (f.Y < -0.5) for cx, cy, rx, ry in cl]
    mass = ms[0] | ms[1] | ms[2] | ms[3] | ms[4]

    def caps(X, Y, t):
        t = t.copy()
        for k, ((cx, cy, rx, ry), m) in enumerate(zip(cl, ms)):
            if k < 3:                                   # the three big clusters: a lit cap
                cap = m & (((X - cx + 0.3 * rx) / (0.42 * rx)) ** 2 + ((Y - cy + 0.4 * ry) / (0.32 * ry)) ** 2 < 1.0)
                t[cap & (t == 2)] = 3
            if k == 2:                                  # the top cluster overhangs the two below it
                under = m & (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 > 0.7) & (Y > cy + 1)
                t[under & (t >= 2)] = 1
        return t
    f.add(mass, 'leafg', z=10, rl=1.6, rs=2.2, vgrad=0.5, line='hard', deep=True, tonemap=caps)
    if not P.get('calm'):
        R = C.Rig(f, 'S')
        C.shard(f, R, (0.0, 13.0, 1.0), (0.0, 1.0, 0.3), 7.0, C.P0(fx=P.get('fx', 0)), 20)
    else:
        f.add(f.ell(3, -15, 1.8, 1.6), 'bloom', z=13, rl=1, rs=1, line='hard')
        f.add(f.ell(-9, -9, 1.6, 1.4), 'bloom', z=13, rl=1, rs=1, line='hard')
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
CROPS = {'den': (16, 72, 144, 140), 'clump': (56, 110, 104, 140), 'seed': (70, 120, 90, 136), 'shard': (72, 118, 88, 134)}


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

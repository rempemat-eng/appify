"""Made and found things drawn natively at any density, in units (1 unit = 1 texel at 2x).

Each takes the density, a materials dict from the biome file ("materials") and its own size
parameters, and returns a flora.Drawn (image, foot anchor, shadow mask). Wood follows the house
wood recipe (lapped boards, a lit lip, a dark last row, butt joints with nails, grain streaks,
each length a sibling); stone is faceted (a lit top plane, a mid front, a dark right flank, a
crack, moss caps with drips); metal is plates with a sheen; lit glass is lit from inside.
"""
from __future__ import annotations

import math

import numpy as np

from . import raster as pk
from .flora import Drawn, done, sprite


def _rock(sp, name, cx, cy, w, h, fam, seed, n=11, base=3, z=1.0, moss=None, crack=True):
    g = sp.g
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + rng.uniform(-0.09, 0.09)
        pts.append((cx + math.cos(a) * w / 2 * r, cy + math.sin(a) * h / 2 * r))
    m = pk.round_mask(g.poly(pts), max(1, int(round(sp.s * 1.5))))
    sp.add(name, m, fam, base=base, lo=0, hi=5, z=z, k=1.0)
    sp.mark(name, g.ellipse(cx - w * 0.12, cy - h * 0.22, w * 0.32, h * 0.2) & m, 1)
    if crack:
        sp.mark(name, g.stroke([(cx + w * 0.12, cy - h * 0.35), (cx + w * 0.05, cy - h * 0.05), (cx + w * 0.18, cy + h * 0.2)], 0.6) & m, -2)
    if moss:
        cap = g.ellipse(cx - w * 0.1, cy - h * 0.42, w * 0.34, h * 0.16) & m
        sp.add(name + 'moss', cap, moss, base=3, lo=2, hi=4, z=z + 0.5, k=1.2)
        drip = g.capsule(cx - w * 0.3, cy - h * 0.35, cx - w * 0.32, cy - h * 0.16, 1.2) & m
        sp.add(name + 'drip', drip, moss, base=2, lo=1, hi=3, z=z + 0.4, flat=True)
    return m


def mossy_stone(d, mat, seed=31, w=24, h=16):
    """A field stone half sunk in the floor, lit on its top plane, moss on its crown."""
    sp = sprite(d, w * 2 + 8, h * 2 + 8, w + 4, 3)
    _rock(sp, 'rock', 0, -h, w * 2, h * 2, mat['stone'], seed, moss='moss')
    return done(sp)


def standing_stone(d, mat, seed=31, h=28, w=16):
    """A standing stone of the circle (size guide 20 to 36 tall, 8 to 20 wide): a tall slab,
    its west face lit, its east flank in shade, a moss cap with drips, lichen in clusters."""
    H, Wd = h * 2, w * 2
    sp = sprite(d, Wd + 10, H + 10, (Wd + 10) / 2, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    lean = rng.uniform(-1.5, 1.5)
    pts = [(-Wd * 0.42, -1), (-Wd * 0.5, -H * 0.45), (-Wd * 0.36 + lean, -H * 0.9), (-Wd * 0.1 + lean, -H),
           (Wd * 0.28 + lean, -H * 0.94), (Wd * 0.48 + lean * 0.5, -H * 0.6), (Wd * 0.46, -1)]
    m = pk.round_mask(g.poly(pts), max(1, int(round(sp.s * 1.5))))
    sp.add('slab', m, mat['stone'], base=3, lo=0, hi=5, z=1, mode='cyl', k=0.9)
    top = g.ellipse(-Wd * 0.05 + lean, -H * 0.93, Wd * 0.34, H * 0.07) & m
    sp.mark('slab', top, 1)
    for j in range(3):          # bedding marks across the slab, never full height
        y = -H * rng.uniform(0.25, 0.8)
        x = rng.uniform(-Wd * 0.3, Wd * 0.1)
        sp.mark('slab', g.rect(x, y, x + rng.uniform(3, 6), y + 1.0) & m, -1)
    sp.mark('slab', g.stroke([(Wd * 0.1, -H * 0.85), (Wd * 0.04, -H * 0.6), (Wd * 0.16, -H * 0.45)], 0.6) & m, -2)
    cap = (g.ellipse(-Wd * 0.08 + lean, -H * 0.94, Wd * 0.36, H * 0.09) | g.ellipse(-Wd * 0.3, -H * 0.84, Wd * 0.14, H * 0.08)) & m
    sp.add('moss', cap, 'moss', base=3, lo=2, hi=4, z=1.5, k=1.2)
    for x in (-Wd * 0.3, -Wd * 0.12):
        sp.add(f'drip{x}', g.capsule(x, -H * 0.88, x - 0.3, -H * 0.72, 1.1) & m, 'moss', base=2, lo=1, hi=3, z=1.4, flat=True)
    for j in range(4):          # lichen: pale clusters of 2 to 3 px
        x, y = rng.uniform(-Wd * 0.35, Wd * 0.25), -H * rng.uniform(0.2, 0.7)
        sp.add(f'li{j}', g.ellipse(x, y, 1.6, 1.0) & m, 'plaster_cool', base=3, lo=2, hi=4, z=1.3, flat=True)
    return done(sp)


def stone_seat(d, mat, seed=7, length=30):
    """A stone seat: a dressed slab on two block legs (size guide: bench 12 to 14 tall, 28 to 36
    long). Its top plane lit, its front a step down, the legs set back in shade, moss in the
    joint, a worn hollow where people sit."""
    L = length * 2
    sp = sprite(d, L + 12, 34, (L + 12) / 2, 3)
    g = sp.g
    for x in (-L * 0.34, L * 0.34):
        leg = g.rrect(x - 5, -13, x + 5, 0, 1.2)
        sp.add(f'leg{x}', leg, mat['stone'], base=2, lo=0, hi=3, z=1, k=0.9)
    top = g.rrect(-L / 2, -24, L / 2, -17, 1.6)
    sp.add('top', top, mat['seat_stone'], base=4, lo=2, hi=5, z=2, flat=True)
    sp.mark('top', g.rect(-L / 2 - 1, -24, L / 2 + 1, -23), 1)
    sp.mark('top', g.ellipse(-L * 0.18, -20.5, 6, 1.4), -1)
    sp.mark('top', g.ellipse(L * 0.2, -20.5, 6, 1.4), -1)
    front = g.rrect(-L / 2, -17.4, L / 2, -12, 1.0)
    sp.add('front', front, mat['seat_stone'], base=3, lo=1, hi=4, z=2.1, flat=True)
    sp.mark('front', g.rect(L * 0.25, -17.4, L / 2 + 1, -12), -1)
    sp.mark('front', g.rect(-L / 2 - 1, -13.2, L / 2 + 1, -12), -1)
    sp.add('moss', g.ellipse(-L / 2 + 4, -12.4, 5, 1.6) & ~top, 'moss', base=3, lo=2, hi=4, z=2.2, flat=True)
    return done(sp)


def lantern_post(d, mat, seed=8, lit=False, side=1):
    """A lantern on a timber post with an arm (size guide: lantern post 22 to 40; this one 36
    world px): post and cap, a braced arm, a hook, an iron hood, glass panes (lit: lamp tones
    from inside, brighter low in the middle) and an iron base. side 1 hangs it east."""
    sp = sprite(d, 36, 80, 10 if side > 0 else 26, 3)
    g = sp.g
    q = side
    post = g.rect(-2.4, -70, 2.4, 0) | g.rrect(-3.6, -4, 3.6, 0, 1)
    sp.add('post', post, mat['wood'], base=3, lo=1, hi=4, z=1, mode='cyl')
    sp.mark('post', g.rect(-5, -60, 5, -59), -1)
    sp.mark('post', g.rect(-5, -30, 5, -29), -1)
    sp.add('cap', g.rrect(-3.6, -73, 3.6, -69.6, 1.0), mat['wood'], base=4, lo=2, hi=5, z=1.5)
    x0, x1 = min(-1 * q, 16 * q), max(-1 * q, 16 * q)
    sp.add('arm', g.rect(x0, -66.5, x1, -63.8), mat['wood'], base=3, lo=1, hi=4, z=1.2, flat=True)
    sp.mark('arm', g.rect(x0, -66.5, x1, -65.6), 1)
    sp.add('brace', g.stroke([(2 * q, -56), (9 * q, -64.5)], 0.9), mat['wood'], base=2, lo=1, hi=3, z=1.1, flat=True)
    c = 13.1 * q
    sp.add('hook', g.rect(c - 0.5, -64, c + 0.5, -60.5), mat['iron'], base=2, z=2, flat=True)
    sp.add('roof', g.poly([(c, -61.5), (c + 5.9, -56.6), (c - 5.9, -56.6)]), mat['iron'], base=3, lo=1, hi=5, z=3)
    glass = g.rect(c - 4.5, -56.6, c + 4.5, -45.0)
    sp.add('glass', glass, mat['glass_lit'] if lit else mat['glass_day'], base=4 if lit else 2, lo=1, hi=5, z=2.5, flat=True, casts=False)
    if lit:
        sp.mark('glass', g.ellipse(c, -48.5, 3.2, 3.6), 1)
        sp.mark('glass', g.rect(c - 4.5, -56.6, c + 4.5, -54.6), -2)
    else:
        sp.mark('glass', g.stroke([(c - 3, -50), (c - 1, -54)], 0.6), 2)    # a glint by day
        sp.add('candle', g.rect(c - 1, -50.5, c + 1, -45.2), 'plaster', base=4, lo=3, hi=5, z=2.6, flat=True)
    frame = (g.rect(c - 5.1, -57.0, c - 3.9, -44.6) | g.rect(c + 3.9, -57.0, c + 5.1, -44.6) | g.rect(c - 0.5, -56.6, c + 0.5, -45.0))
    sp.add('frame', frame, mat['iron'], base=2, lo=1, hi=3, z=3.2, flat=True)
    sp.add('base', g.rrect(c - 5.7, -45.4, c + 5.7, -42.6, 0.8), mat['iron'], base=3, lo=1, hi=4, z=3.3)
    out = done(sp)
    out.meta['light'] = g.px(c, -50)          # the flame, image px
    out.meta['glass'] = (g.px(c - 4.5, -56.6), g.px(c + 4.5, -45.0))
    return out


def stump(d, mat, seed=61):
    """A cut stump (size guide 8 to 16 tall, 12 to 22 wide): bark sides, roots, a lit top with
    growth rings and a split."""
    sp = sprite(d, 44, 34, 22, 3)
    g = sp.g
    side = g.rrect(-13, -20, 13, -2, 3) | g.poly([(-13, -6), (-19, -1), (-9, -2)]) | g.poly([(13, -7), (18, -1), (9, -2)])
    side = pk.round_mask(side, 1)
    sp.add('bark', side, 'timber_cool', base=3, lo=0, hi=4, z=1, mode='cyl')
    rng = np.random.default_rng(seed)
    for x in (-8, -3, 4, 9):
        y0 = -16 + rng.uniform(-1, 2)
        sp.mark('bark', g.capsule(x, y0, x + rng.uniform(-0.5, 0.5), y0 + rng.uniform(5, 9), 0.6), -1)
    top = g.ellipse(0, -20, 13, 5.2)
    sp.add('top', top, mat['wood_cut'], base=3, lo=1, hi=4, z=2, flat=True)
    sp.mark('top', g.ellipse(0, -20, 9.0, 3.4) & ~g.ellipse(0, -20, 7.6, 2.6), -1)
    sp.mark('top', g.ellipse(0, -20, 4.6, 1.6) & ~g.ellipse(0, -20, 3.2, 1.0), -1)
    sp.mark('top', g.ellipse(-4, -21.6, 5.0, 1.4) & top, 1)
    sp.mark('top', g.stroke([(1, -20), (8, -17.6)], 0.5), -1)
    sp.add('moss', g.ellipse(-9, -6, 5, 2.4) & side, 'moss', base=3, lo=2, hi=4, z=1.5, k=1.2)
    return done(sp)


def chopping_block(d, mat, seed=12):
    """The forester's chopping block: a wide stump with an axe bitten into its top (iron head lit
    on its upper edge, an ash handle), chips round its foot."""
    out_sp = sprite(d, 48, 44, 22, 3)
    sp = out_sp
    g = sp.g
    side = pk.round_mask(g.rrect(-12, -18, 12, -2, 3) | g.poly([(-12, -5), (-17, -1), (-8, -2)]), 1)
    sp.add('bark', side, 'timber_cool', base=3, lo=0, hi=4, z=1, mode='cyl')
    top = g.ellipse(0, -18, 12, 4.8)
    sp.add('top', top, mat['wood_cut'], base=3, lo=1, hi=4, z=2, flat=True)
    sp.mark('top', g.ellipse(0, -18, 7.6, 2.8) & ~g.ellipse(0, -18, 6.2, 2.1), -1)
    sp.mark('top', g.stroke([(-6, -19), (4, -16.5)], 0.6), -2)          # cuts
    sp.add('handle', g.capsule(3, -20, 14, -36, 1.3, 1.1), mat['wood'], base=4, lo=2, hi=5, z=3, mode='cyl')
    head = g.poly([(-1, -19), (6, -24), (8, -21), (3, -17)])
    sp.add('head', head, mat['iron'], base=3, lo=1, hi=5, z=3.5)
    sp.mark('head', g.stroke([(-1, -19.5), (6, -24.3)], 0.5), 2)
    return done(sp)


def woodpile(d, mat, seed=11, length=40):
    """A stack of split logs under a lean-to: round and split ends of every size facing the
    viewer (rings, a lit rim, a dark split), laid in rough rows that settle unevenly, a few
    lengths sticking out; two posts carry a sloped bark-board roof (its front edge in shade, a
    moss line along it)."""
    L = length * 2
    sp = sprite(d, L + 18, 70, (L + 18) / 2, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    # the lean-to: posts at the front corners, the roof sloping up to the back
    for x in (-L / 2 - 2, L / 2 + 2):
        sp.add(f'post{x}', g.rect(x - 1.8, -46, x + 1.8, 0), mat['wood'], base=2, lo=0, hi=3, z=5, mode='cyl')
    k = 0
    y = -2.0
    for j in range(5):
        x = -L / 2 + rng.uniform(0, 3)
        while x < L / 2 - 3:
            r = rng.uniform(3.6, 5.8) * (0.9 if j > 2 else 1.0)
            if x + r > L / 2:
                break
            cy_ = y - r * 0.92 + rng.uniform(-0.8, 0.8)
            e = g.ellipse(x + r, cy_, r - 0.2, r * 0.9)
            nm = f'log{k}'
            sp.add(nm, e, ('timber_warm', 'timber', 'timber_cool')[int(rng.integers(0, 3))], base=2, lo=0, hi=3, z=2 + j * 0.1 + rng.uniform(0, 0.05), flat=True)
            face = g.ellipse(x + r - 0.3, cy_ - 0.2, r - 1.5, r * 0.9 - 1.3)
            split = rng.random() < 0.45
            if split:   # a split log: half round, its flat face lit
                face &= g.X < x + r + rng.uniform(-1, 1)
            sp.add(nm + 'f', face, mat['wood_cut'], base=3, lo=1, hi=4, z=2.05 + j * 0.1, flat=True)
            sp.mark(nm + 'f', g.ellipse(x + r - 0.3, cy_ - 0.2, r * 0.42, r * 0.38) & ~g.ellipse(x + r - 0.3, cy_ - 0.2, r * 0.24, r * 0.2), -1)
            sp.mark(nm + 'f', g.ellipse(x + r - 1.4, cy_ - 1.5, r * 0.45, r * 0.28) & face, 1)
            if rng.random() < 0.35:
                sp.mark(nm + 'f', g.stroke([(x + r - 0.3, cy_ - 0.2), (x + r + r * 0.6, cy_ + r * 0.4)], 0.5) & face, -2)
            x += 2 * r + rng.uniform(-0.6, 0.8)
            k += 1
        y -= rng.uniform(7.2, 8.6)
    top = y - 2
    roof = g.poly([(-L / 2 - 5, top + 3), (L / 2 + 5, top + 6), (L / 2 + 5, top - 4), (-L / 2 - 5, top - 9)])
    sp.add('roof', roof, 'timber_cool', base=3, lo=1, hi=5, z=6)
    for q in range(6):          # boards down the slope, each a sibling, a dark joint between
        bx = -L / 2 - 5 + (L + 10) * q / 6
        sp.mark('roof', g.rect(bx, top - 12, bx + 1.0, top + 8) & roof, -1)
        sp.mark('roof', g.rect(bx + 1.0, top - 12, bx + 2.4, top + 8) & roof, 1)
    edge = roof & ~g.poly([(-L / 2 - 5, top + 0.5), (L / 2 + 5, top + 3.5), (L / 2 + 5, top - 4), (-L / 2 - 5, top - 9)])
    sp.mark('roof', edge, -2)
    sp.add('moss', g.ellipse(-L * 0.15, top - 6, L * 0.2, 1.4) & roof, 'moss', base=3, lo=2, hi=4, z=6.2, flat=True)
    return done(sp)


def log(d, mat, seed=71, length=54):
    """A fallen mossy log lying east-west (size guide: log 8 to 18 tall, 30 to 64 long): a bark
    cylinder lit on top, a cut end facing west with rings, moss along its crown with drips."""
    L2 = length
    sp = sprite(d, L2 * 2 + 14, 30, L2 + 7, 3)
    g = sp.g
    L = L2
    body = g.rrect(-L + 2, -18, L, -2, 7)
    sp.add('bark', body, 'timber_cool', base=3, lo=0, hi=4, z=1)
    rng = np.random.default_rng(seed)
    for k in range(int(L / 6)):
        x = rng.uniform(-L + 8, L - 6)
        sp.mark('bark', g.capsule(x, -14 + rng.uniform(0, 2), x + rng.uniform(4, 8), -13 + rng.uniform(0, 3), 0.6), -1)
    end = g.ellipse(-L + 3, -10, 4.6, 8.0)
    sp.add('end', end, mat['wood_cut'], base=3, lo=1, hi=4, z=1.5, flat=True)
    sp.mark('end', g.ellipse(-L + 3, -10, 2.6, 4.6) & ~g.ellipse(-L + 3, -10, 1.3, 2.4), -1)
    moss = (g.ellipse(4, -17, L * 0.5, 3.2) | g.ellipse(-L * 0.4, -16.5, L * 0.22, 2.6)) & body
    sp.add('moss', moss, 'moss', base=3, lo=2, hi=5, z=2, k=1.1)
    for x in (-L * 0.1, L * 0.3, L * 0.5):
        sp.add(f'drip{x}', g.capsule(x, -16.5, x + 0.3, -12.5, 1.1) & body, 'moss', base=2, lo=1, hi=3, z=1.9, flat=True)
    return done(sp)


def footbridge(d, mat, seed=13, span=(288, 312), width=20):
    """A plank footbridge (world px: `span` the rows it crosses, `width` across): planks laid
    across the stream, each a sibling with a lit top row and a dark gap under it, two side
    stringers, posts at the corners standing in the banks. Its foot is the south end."""
    y0, y1 = span
    Lr = (y1 - y0) * 2 + 8
    Wd = width * 2
    sp = sprite(d, Wd + 12, Lr + 24, (Wd + 12) / 2, 2)
    g = sp.g
    rng = np.random.default_rng(seed)
    top = -Lr
    for k, ya in enumerate(np.arange(top + 2, -2, 5.0)):
        nm = f'plank{k}'
        m = g.rrect(-Wd / 2 + 2 + rng.uniform(-0.6, 0.6), ya, Wd / 2 - 2 + rng.uniform(-0.6, 0.6), ya + 4.4, 0.8)
        sp.add(nm, m, ('timber', 'timber_warm', 'timber_cool')[k % 3], base=3, lo=1, hi=5, z=2 + k * 0.01, flat=True, outline=True)
        sp.mark(nm, g.rect(-Wd, ya, Wd, ya + 1.0), 1)
        sp.mark(nm, g.rect(-Wd, ya + 3.4, Wd, ya + 4.4), -1)
        gx = rng.uniform(-Wd / 2 + 4, Wd / 2 - 10)
        sp.mark(nm, g.rect(gx, ya + 1.8, gx + rng.uniform(4, 8), ya + 2.8), -1)
        for x in (-Wd / 2 + 4, Wd / 2 - 5):
            sp.detail(g.rect(x, ya + 1.6, x + 1, ya + 2.6), pk.rgb('iron', 1))
    for x in (-Wd / 2 + 1, Wd / 2 - 1):
        sp.add(f'rail{x}', g.rect(x - 1.4, top, x + 1.4, 0), mat['wood'], base=2, lo=0, hi=3, z=3, flat=True)
        for y in (top, -2):
            sp.add(f'post{x}{y}', g.rrect(x - 2.4, y - 8, x + 2.4, y + 2, 1.0), mat['wood'], base=3, lo=1, hi=4, z=4, mode='cyl')
    return done(sp)


KINDS = {'mossy_stone': mossy_stone, 'standing_stone': standing_stone, 'stone_seat': stone_seat,
         'lantern_post': lantern_post, 'stump': stump, 'chopping_block': chopping_block, 'woodpile': woodpile,
         'log': log, 'footbridge': footbridge}


def make(kind: str, d: float, mat: dict, params: dict) -> Drawn:
    return KINDS[kind](d, mat, **params)

"""A screen from a layout and a biome: every layer, the objects, the walk and the animation.

    sc = screen.build(layout, density=2)
    sc.ground          RGBA texels: terrain, floor, light, shadows and ground plants baked in
    sc.objects         [(id, key, foot (world px), Drawn)]: what the game draws as zone objects
    sc.blocked         world px the terrain blocks (water, faces, the raised tier, boulders)
    sc.flow            (sheet, box texels, cols) of the moving water, or None
    sc.night           RGBA texels: the lit lantern and its pool, shown above the night tint
    sc.layers          name -> RGBA texels: ground, terrain, water, shadows, light, props (the
                       layer-separated export, for lifting pieces into kits)
    sc.preview(night)  everything composed as the game shows it (sorted by feet)

Nothing here is specific to the woodland: the layout module gives places and coordinates, the
biome file gives families, plants and numbers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import animate, flora, ground as GR, props as PR, terrain as TR
from . import biome as load_biome
from . import style as ST

cc = TR.cc


@dataclass
class Screen:
    L: object
    B: dict
    s: float
    ground: Image.Image
    objects: list
    blocked: set
    flow: object
    night: Image.Image
    layers: dict
    feet: dict = field(default_factory=dict)
    terrain: object = None
    overhead: list = field(default_factory=list)     # [(id, key, top-left (world px), image)]

    def preview(self, night=False, tint=(22, 28, 66, 0.42), chars=()):
        img = self.ground.copy()
        items = [(foot[1], d.img, d.anchor, foot) for (_i, _k, foot, d) in self.objects]
        for (fy, im, anc, foot) in chars:
            items.append((fy, im, anc, foot))
        items.sort(key=lambda t: t[0])
        for (_fy, im, anc, foot) in items:
            img.alpha_composite(im, (int(round(foot[0] * self.s - anc[0])), int(round(foot[1] * self.s - anc[1]))))
        for (_i, _k, (x, y), im) in self.overhead:
            img.alpha_composite(im, (int(round(x * self.s)), int(round(y * self.s))))
        if night:
            r, g, b, a = tint
            over = Image.new('RGBA', img.size, (r, g, b, int(round(a * 255))))
            img.alpha_composite(over)
            img.alpha_composite(self.night)
        return img


def _uniq(items):
    seen, out = set(), []
    for it in items:
        if it[0] not in seen:
            seen.add(it[0])
            out.append(it)
    return out


def _masked(img, m):
    a = np.asarray(img).copy()
    a[~m] = 0
    return Image.fromarray(a, 'RGBA')


def _key(prefix, name):
    return (prefix + '_' + name).replace('-', '_')


def _trunk_feet(kind, d: 'flora.Drawn', s):
    """The footing a thing blocks (sprite px at 1 world px, as zones.FEET): a trunk's width, a
    bush's spread, a stone's base; a footbridge none (it is walked on)."""
    w = d.img.width / s
    ax = d.anchor[0] / s
    h = d.img.height / s
    if kind == 'footbridge':
        return ()
    half = {'veteran_oak': 12, 'oak': 5, 'beech': 5, 'birch': 3, 'pine': 4, 'sapling': 2, 'lantern_post': 2}.get(kind)
    if half is not None:
        return ((int(ax - half), int(math.ceil(ax + half)), 6 if kind != 'veteran_oak' else 10),)
    depth = {'woodpile': 10, 'stone_seat': 6, 'log': 8, 'standing_stone': 6}.get(kind, 6)
    return ((2, int(w) - 2, depth),)


def build(L, density=2.0) -> Screen:
    B = load_biome(L.BIOME)
    ST.use(B)
    s = float(density)
    t = TR.build(L, s, L.stream_centre, L.stream_half)
    H, W = t.F.shape
    fl = GR.Floor(t, B)
    fl.calm()
    Fm = B['flora']
    mat = B['materials']
    # ---- places on the floor ------------------------------------------------------------------
    gx0, gy0, gx1, gy1 = L.GLADE
    glade = GR.blob((gx0 + gx1) / 2, (gy0 + gy1) / 2, (gx1 - gx0) / 2, (gy1 - gy0) / 2, (H, W), 66, 0.22, s)
    hue = cc.fbm2(fl.X, fl.Y, 40.0 * s, cc.hashu(L.SEED, 7), 2)
    fl.patch(glade, 'grass', 3, hue)
    rx0, ry0, rx1, ry1 = L.RING_IN
    ring_in = TR.rects_mask([L.RING_IN], (H, W), s, 0, int(4 * s), 0)
    fl.patch(ring_in, 'grass', 3, hue)
    fx, fy, frx, fry = L.FAIRY
    # the fairy ring: greener turf in a broken ring, its radius wandering (never a ruled circle)
    ang = np.arctan2((fl.Y - fy * s) / (fry * s), (fl.X - fx * s) / (frx * s))
    wob = 1 + 0.16 * np.sin(3 * ang + 1.3) + 0.09 * np.sin(5 * ang + 0.4)
    ell = np.sqrt(((fl.X - fx * s) / (frx * s)) ** 2 + ((fl.Y - fy * s) / (fry * s)) ** 2) / wob
    fairy = (ell > 0.78) & (ell < 1.16) & (np.sin(4 * ang + 2.0) > -0.55)
    fairy = ndi.binary_opening(fairy, iterations=1)
    fl.patch(fairy, 'moss_cool', 2)
    fl.locked |= fairy
    # ---- objects ------------------------------------------------------------------------------
    objects = []
    for (oid, kind, x, y, params) in L.OBJECTS:
        if kind in flora.TREES:
            dr = flora.TREES[kind](s, Fm, params.get('seed', 1), params.get('scale', 1.0))
        else:
            dr = PR.make(kind, s, mat, params)
        dr.meta['kind'] = kind
        dr.meta['params'] = dict(params)
        objects.append((oid, _key('wd', oid), (x, y), dr))
    placed = scatter(L, t, s, [(o[2][0], o[2][1]) for o in objects])
    counts = {}
    wood = []
    for (kind, x, y, scale, seed) in placed:
        counts[kind] = counts.get(kind, 0) + 1
        if kind in flora.SHRUBS:
            dr = flora.bush(s, Fm, seed, w=36 * scale, h=28 * scale, kind=kind)
        else:
            dr = flora.TREES[kind](s, Fm, seed, scale)
        dr.meta['kind'] = kind
        wood.append((f'{kind}-{counts[kind]}', _key('wd', f'{kind}{counts[kind]}'), (x, y), dr))
    # the belts are a dense wood with undergrowth: solid to the walker (its open places, the
    # kept-open ground and the stands stay open)
    k = int(s)
    feet_m = np.zeros((H // k, W // k), bool)
    for (_i, _k2, (x, y), dr) in wood:
        if 0 <= y < H // k and 0 <= x < W // k:
            feet_m[y, x] = True
    belts = np.zeros_like(feet_m)
    for ((x0, y0, x1, y1), _sp, _mix, _z) in L.BELTS:
        belts[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    wood_block = belts.copy()
    for (x0, y0, x1, y1) in list(getattr(L, 'KEEP_OPEN', [])) + [L.SEAT]:
        wood_block[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = False
    for (x, y) in L.STANDS.values():
        wood_block[max(0, y - 12):y + 12, max(0, x - 12):x + 12] = False
    keep_obj, baked_ground, baked_over = classify(L, t, s, objects, wood, wood_block)
    objects += keep_obj
    fl.banks(t.water, L.SEED + 5)
    # ---- shadows and contact lines ------------------------------------------------------------
    S = B['shadow']
    sh = np.zeros((H, W), bool)
    con = np.zeros((H, W), bool)
    every = objects + _uniq([e[0] for e in baked_ground + baked_over])
    for (_oid, _key_, (x, y), dr) in every:
        at = (x * s, y * s)
        if dr.meta.get('kind') == 'footbridge':
            continue
        sh |= GR.cast(dr.alpha, dr.anchor, at, W, H, s, S['kx'], S['ky'])
        con |= GR.contact_line(dr.alpha, dr.anchor, at, W, H, s)
    # the spur's trees throw onto the tier, the floor's onto the floor: one rule, the ground they fall on
    crowns = np.zeros((H, W), bool)
    for (_oid, _key_, (x, y), dr) in every:
        if dr.crown is not None and dr.meta.get('kind') in flora.TREES:
            crowns |= GR.cast(dr.crown, dr.anchor, (x * s, y * s), W, H, s, S['kx'], S['ky'])
    fl.masses()
    fl.mass_shadow(S['kx'], S['ky'])
    fl.shadow(sh & ~(t.kind == cc.FACEK), dapple=fl.dapple(crowns, L.SEED + 7))
    fl.contact(con)
    # ---- light: the glade in sun, dappled pools ---------------------------------------------------
    sun = glade & ~ndi.binary_dilation(sh, iterations=int(2 * s))
    for (x0, y0, x1, y1) in L.SUN[1:]:   # a few pools where a gap in the canopy lets the sun in
        sun |= GR.blob((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, (H, W), x0 + y0, 0.3, s) & ~sh
    fl.sun(sun & ~fl.locked)
    # ---- litter round the trees ---------------------------------------------------------------
    feet_pts = [foot for (_i, _k, foot, dr) in every if dr.meta.get('kind') in flora.TREES]
    fl.litter(feet_pts, L.SEED + 3)
    img = fl.image()
    # ---- ground plants (pasted: they stand on the floor) ------------------------------------------
    plants = []
    rng = np.random.default_rng(L.SEED + 11)
    stands = list(L.STANDS.values())

    def clear(x, y, r=10):
        return all((x - a) ** 2 + (y - b) ** 2 > r * r for a, b in stands)

    walk_t = t.walk
    def dry(x, y, r=4):
        xi, yi = int(x * s), int(y * s)
        sub = t.water[max(0, yi - int(r * s)):yi + 2, max(0, xi - int(r * s)):xi + int(r * s)]
        return 0 <= xi < W and 0 <= yi < H and not sub.any() and t.kind[yi, xi] == cc.TOP

    for k, (x, y) in enumerate(L.FERNS):
        if clear(x, y) and dry(x, y, 8):
            plants.append((y, flora.fern(s, Fm, 500 + k, 0.8 + 0.4 * rng.random()), (x, y)))
    for k, (x, y, kind, n) in enumerate(L.FLOWERS):
        if clear(x, y, 8) and dry(x, y):
            plants.append((y, flora.flowers(s, Fm, 600 + k, kind, n), (x, y)))
    for k, (x, y) in enumerate(L.MUSHROOMS):
        plants.append((y, flora.mushrooms(s, Fm, 700 + k, 2 + k % 2), (x, y)))
    # dressing in clumps across every open floor (Matt, 13:37: "no lawn area is empty", detail
    # in placed things, never speckle): two to four tufts, now and then flowers or pebbles
    k_ = int(s)
    open_w = t.walk[::k_, ::k_] & ~wood_block & ~ndi.binary_dilation(t.path[::k_, ::k_], iterations=3) & (t.z[::k_, ::k_] == 0)
    ev = ST.get('dressing', 'every_world', getattr(L, 'DRESS_EVERY', 28))
    kinds_f = list(Fm['flowers'])
    n_c = 0
    for gy in np.arange(ev / 2, H / s, ev):
        for gx in np.arange(ev / 2 + (ev / 2 if int(gy / ev) % 2 else 0), W / s, ev):
            x, y = gx + rng.uniform(-ev * 0.35, ev * 0.35), gy + rng.uniform(-ev * 0.35, ev * 0.35)
            xi, yi = int(x), int(y)
            if not (0 <= xi < W // k_ and 0 <= yi < H // k_) or not open_w[yi, xi] or not clear(x, y, 12) or rng.random() < ST.get('dressing', 'skip', 0.25):
                continue
            q = rng.random()
            n_c += 1
            fl_p, pb_p = ST.get('dressing', 'flowers', 0.18), ST.get('dressing', 'pebbles', 0.14)
            if q < fl_p:
                plants.append((y, flora.flowers(s, Fm, 1200 + n_c, kinds_f[int(rng.integers(0, len(kinds_f)))], int(rng.integers(2, 5))), (x, y)))
            elif q < fl_p + pb_p:
                plants.append((y, flora.pebbles(s, Fm, 1300 + n_c, int(rng.integers(2, 4))), (x, y)))
            for j in range(int(rng.integers(2, 4))):
                tx, ty = x + rng.uniform(-6, 6), y + rng.uniform(-2.5, 2.5)
                if open_w[min(H // k_ - 1, int(ty)), min(W // k_ - 1, max(0, int(tx)))]:
                    plants.append((ty - 0.5, flora.tuft(s, Fm, 1400 + n_c * 5 + j, 0.7 + 0.35 * rng.random()), (tx, ty)))
    # vegetation on and round the raised ground: shrubs and tufts along the shelf's rims (grass
    # creeping over the edge), ferns and tufts at the faces' feet
    face = t.kind == cc.FACEK
    rim = (t.kind == cc.TOP) & (t.z > 0) & np.vstack([face[1:], np.zeros((1, W), bool)])
    foot = (t.kind == cc.TOP) & (t.z == 0) & np.vstack([np.zeros((1, W), bool), face[:-1]]) & ~t.water
    for mask_, step_, what in ((rim, ST.get('dressing', 'rim_every_world', 22), 'rim'), (foot, ST.get('dressing', 'foot_every_world', 18), 'foot')):
        ys_, xs_ = np.nonzero(mask_)
        last = -999
        for i in np.argsort(xs_):
            x, y = xs_[i] / s, ys_[i] / s
            if x - last < step_ * rng.uniform(0.7, 1.3):
                continue
            last = x
            if what == 'rim':
                if rng.random() < 0.5:
                    plants.append((y + 0.2, flora.bush(s, Fm, 1500 + int(x), w=22, h=16, kind='bush'), (x, y + 2)))
                else:
                    plants.append((y + 0.2, flora.tuft(s, Fm, 1600 + int(x), 1.0), (x, y + 1)))
            elif dry(x, y + 2, 3) and clear(x, y, 10):
                plants.append((y + 1, flora.fern(s, Fm, 1700 + int(x), 0.8) if rng.random() < 0.45 else flora.tuft(s, Fm, 1800 + int(x), 0.9), (x, y + 2)))
    # ferns and tufts at the feet of the wood where it meets open floor
    for (_i, _k, (x, y), dr) in wood:
        xi, yi = int(x), int(y)
        if not (0 <= xi < W // k_ and 0 <= yi + 8 < H // k_) or not open_w[min(H // k_ - 1, yi + 6), xi]:
            continue
        if rng.random() < ST.get('dressing', 'wood_edge', 0.6) and clear(x, y, 12):
            plants.append((y + 2, flora.fern(s, Fm, 1900 + xi * 7 + yi, 0.7 + 0.3 * rng.random()) if rng.random() < 0.5
                           else flora.tuft(s, Fm, 2000 + xi * 7 + yi, 0.9), (x + rng.uniform(-6, 6), y + 3)))
    # the fairy ring's toadstools: a broken ring
    for k in range(11):
        a = 2 * math.pi * k / 11 + rng.uniform(-0.25, 0.25)
        if math.sin(4 * a + 2.0) < -0.55 or rng.random() < 0.15:
            continue          # the ring's gaps
        r = 1 + 0.16 * math.sin(3 * a + 1.3) + 0.09 * math.sin(5 * a + 0.4) + rng.uniform(-0.08, 0.08)
        x, y = fx + frx * r * math.cos(a), fy + fry * r * math.sin(a)
        plants.append((y, flora.mushrooms(s, Fm, 800 + k, 1 + (k % 3 == 0)), (x, y)))
    # tufts in clumps of two or three: at every tree's foot, along path edges every ~32 world px
    tuft_pts = []
    for (_i, _k, (x, y), dr) in objects + [e[0] for e in baked_ground]:
        kind = dr.meta.get('kind')
        if kind in ('footbridge', 'lantern_post'):
            continue
        for j in range(int(rng.integers(1, 3))):
            tuft_pts.append((x + rng.uniform(-10, 10), y + rng.uniform(0.5, 3)))
    pe = t.path & ~ndi.binary_erosion(t.path, iterations=2)
    ys, xs = np.nonzero(pe)
    order = rng.permutation(len(ys))
    taken = []
    every = B['rhythm']['edge_dressing_every_world']
    for i in order:
        x, y = xs[i] / s, ys[i] / s
        if any((x - a) ** 2 + (y - b) ** 2 < every ** 2 for a, b in taken):
            continue
        taken.append((x, y))
        for j in range(int(rng.integers(2, 4))):
            tuft_pts.append((x + rng.uniform(-4, 4), y + rng.uniform(-1, 2)))
    for k, (x, y) in enumerate(tuft_pts):
        xi, yi = int(x * s), int(y * s)
        if not (0 <= xi < W and 0 <= yi < H) or t.kind[yi, xi] != cc.TOP or t.water[yi, xi] or not clear(x, y, 6):
            continue
        plants.append((y - 0.5, flora.tuft(s, Fm, 900 + k, 0.7 + 0.35 * rng.random()), (x, y)))
    plants_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # the plants and the wood the walker only ever passes in front of, baked into the ground
    # back to front together
    items = [(y, dr.img, (int(round(x * s - dr.anchor[0])), int(round(y * s - dr.anchor[1]))), True) for (y, dr, (x, _y)) in plants]
    items += [(y, _masked(dr.img, m), (int(round(x * s - dr.anchor[0])), int(round(y * s - dr.anchor[1]))), False)
              for ((_i, _k, (x, y), dr), m) in baked_ground]
    items.sort(key=lambda it: it[0])
    for (_y, im, pos, is_plant) in items:
        img.alpha_composite(im, pos)
        if is_plant:
            plants_layer.alpha_composite(im, pos)
    # the wood the walker only ever passes behind: one canopy layer over everything, cut into
    # pieces round what it covers (zone objects drawn overhead)
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for ((_i, _k, (x, y), dr), m) in sorted(baked_over, key=lambda o: o[0][2][1]):
        over.alpha_composite(_masked(dr.img, m), (int(round(x * s - dr.anchor[0])), int(round(y * s - dr.anchor[1]))))
    overhead = pieces(over, s)
    # ---- what the terrain blocks, in world px ---------------------------------------------------
    walk_w = walk_t.reshape(H // int(s), int(s), W // int(s), int(s)).mean(axis=(1, 3)) >= 0.5
    bx0, bx1 = L.BRIDGE
    deck = np.zeros_like(walk_w)
    deck[280:320, bx0:bx1] = True
    walk_w |= deck & ~walk_w & (np.arange(walk_w.shape[0])[:, None] >= 280)
    walk_w &= ~wood_block
    blocked = {(x, y) for y, x in zip(*np.nonzero(~walk_w))}
    for (_i, _k, (fx_, fy_), dr) in _uniq([e[0] for e in baked_ground + baked_over]):
        for (a0, a1, dep) in _trunk_feet(dr.meta.get('kind'), dr, s):
            x0 = int(round(fx_ - dr.anchor[0] / s))
            for yy in range(fy_ - dep, fy_):
                for xx in range(x0 + a0, x0 + a1):
                    if 0 <= xx < W // int(s) and 0 <= yy < H // int(s):
                        blocked.add((xx, yy))
    # ---- water animation ----------------------------------------------------------------------
    still = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in _pool_boxes(t) + [tuple(int(v * s) for v in b) for b in getattr(L, 'STILL', [])]:
        still[y0:y1, x0:x1] = True
    still &= t.water
    frames = animate.water(fl.F, fl.T, t.water, still, s, TR.fall_box(t, L))
    flow = animate.pack(frames, B['animation']['water']['grid_cols'])
    # ---- night light ---------------------------------------------------------------------------
    night = _night(L, B, s, fl, objects, (H, W), over)
    # ---- layers ---------------------------------------------------------------------------------
    layers = {'ground': img, 'terrain': t.image.convert('RGBA'), 'plants': plants_layer, 'night': night}
    wl = np.zeros((H, W, 4), np.uint8)
    wl[t.water] = np.asarray(img)[t.water]
    layers['water'] = Image.fromarray(wl, 'RGBA')
    shl = np.zeros((H, W, 4), np.uint8)
    shl[..., 3] = np.where(fl.shadow_mask == 2, 150, np.where(fl.shadow_mask == 1, 80, np.where(fl.shadow_mask == 3, 220, 0)))
    shl[..., :3] = (33, 26, 34)
    layers['shadows'] = Image.fromarray(shl, 'RGBA')
    lil = np.zeros((H, W, 4), np.uint8)
    lil[fl.light_mask > 0] = (240, 200, 110, 160)
    layers['light'] = Image.fromarray(lil, 'RGBA')
    props_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (_i, _k, foot, dr) in sorted(objects, key=lambda o: o[2][1]):
        props_layer.alpha_composite(dr.img, (int(round(foot[0] * s - dr.anchor[0])), int(round(foot[1] * s - dr.anchor[1]))))
    for (_i, _k, (x, y), im) in overhead:
        props_layer.alpha_composite(im, (int(round(x * s)), int(round(y * s))))
    layers['props'] = props_layer
    layers['canopy'] = over
    feet = {key: _trunk_feet(dr.meta.get('kind'), dr, s) for (_i, key, _f, dr) in objects}
    return Screen(L, B, s, img, objects, blocked, flow, night, layers, feet, t, overhead)


def _pool_boxes(t):
    out = []
    for f in t.falls:
        rim_row = f['py'] - t.world.top - f['h']
        foot_row = rim_row + (f['h'] - f['h2'])
        c = (f['x0'] + f['x1']) // 2
        s = int(t.density)
        out.append((c - 20 * s, foot_row, c + 20 * s, foot_row + 20 * s))
    return out


def _night(L, B, s, fl, objects, shape, over=None):
    """The night light: each lit lantern's glass in lamp tones and its pool on the ground (the
    floor a tone up on its warm sibling, a checker at the fade), as an overlay shown above the
    night tint; texels behind a nearer thing are left out, so trees still hide the light."""
    H, W = shape
    out = np.zeros((H, W, 4), np.uint8)
    nearer = np.zeros((H, W), bool)
    for (oid, _key, (x, y), dr) in objects:
        if dr.meta.get('kind') != 'lantern_post':
            continue
        lit = PR.lantern_post(s, B['materials'], lit=True, side=dr.meta.get('params', {}).get('side', 1))
        ox, oy = int(round(x * s - lit.anchor[0])), int(round(y * s - lit.anchor[1]))
        # the pool on the ground round the post's foot, and on the water beside it
        Y, X = np.mgrid[0:H, 0:W]
        lx, ly = (ox + lit.meta['light'][0]), y * s + 2 * s
        e = ((X + 0.5 - lx) / (18 * s)) ** 2 + ((Y + 0.5 - ly) / (9 * s)) ** 2
        core = (e <= 0.7)
        ring = (e > 0.7) & (e <= 1.0) & (((X // 2) + (Y // 2)) % 2 == 0)
        pool = (core | ring) & (fl.t.kind == cc.TOP)
        # lamplight on the ground: the floor's value kept, its colour taken to the warm brass
        # ramp (amber), the core a tone up; the fade a checker of brass a tone down (dither only
        # for light)
        F2 = fl.F.copy()
        T2 = fl.T.copy()
        bw, bb = cc.FID[B['ground'].get('lamplight', 'brass') + '_warm'], cc.FID[B['ground'].get('lamplight', 'brass')]
        F2[core] = bw
        T2[core] = np.clip(fl.T[core] - 1, 1, 2)
        T2[core & (e <= 0.3)] = 3
        F2[ring] = bb
        T2[ring] = 1
        rgb = cc.LUT[F2, np.clip(T2, 0, 6)]
        out[pool, :3] = rgb[pool]
        out[pool, 3] = 255
        # the lantern itself, lit (its glass and frame over the day picture)
        la = np.asarray(lit.img)
        h, w = la.shape[:2]
        sub = out[max(0, oy):oy + h, max(0, ox):ox + w]
        src = la[max(0, -oy):max(0, -oy) + sub.shape[0], max(0, -ox):max(0, -ox) + sub.shape[1]]
        m = src[..., 3] > 0
        sub[m] = src[m]
        # left out: whatever a thing standing nearer than the lantern covers
        for (oid2, _k2, (x2, y2), dr2) in objects:
            if y2 <= y or oid2 == oid:
                continue
            a = dr2.alpha
            px, py = int(round(x2 * s - dr2.anchor[0])), int(round(y2 * s - dr2.anchor[1]))
            hh, ww = a.shape
            ys0, xs0 = max(0, py), max(0, px)
            ys1, xs1 = min(H, py + hh), min(W, px + ww)
            if ys0 < ys1 and xs0 < xs1:
                nearer[ys0:ys1, xs0:xs1] |= a[ys0 - py:ys1 - py, xs0 - px:xs1 - px]
    if over is not None:
        nearer |= np.asarray(over)[..., 3] > 0
    out[nearer] = 0
    return Image.fromarray(out, 'RGBA')


def scatter(L, t, s, taken):
    """The wood from the layout's belts: trees on a jittered grid at the belt's spacing (feet
    no closer than 0.8 of it), each kind by the belt's weights, standing only on the tier the
    belt names and never on water, a path, a face, a place kept open or within 22 px of a
    stand; then undergrowth (bush, bramble, holly, saplings) where a belt meets the open
    ground, about every 14 px along its edge. Returns [(kind, foot x, foot y, scale, seed)].
    Deterministic (seeded by the layout)."""
    rng = np.random.default_rng(L.SEED + 101)
    H, W = t.z.shape
    zw = t.z[::int(s), ::int(s)]
    kw = t.kind[::int(s), ::int(s)]
    water = ndi.binary_dilation(t.water[::int(s), ::int(s)], iterations=7)
    path = ndi.binary_dilation(t.path[::int(s), ::int(s)], iterations=4)
    face = ndi.binary_dilation(kw != cc.TOP, iterations=3)
    keep = np.zeros(zw.shape, bool)
    for (x0, y0, x1, y1) in list(getattr(L, 'KEEP_OPEN', [])) + [L.SEAT]:
        keep[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    gx0, gy0, gx1, gy1 = L.GLADE
    keep[gy0 + 4:gy1 - 4, gx0 + 4:gx1 - 4] = True
    (ax, ay), (bx, by) = L.ROUND
    keep[min(ay, by) - 14:max(ay, by) + 12, min(ax, bx) - 12:max(ax, bx) + 12] = True
    stands = list(L.STANDS.values())
    out = []
    feet = list(taken)
    vis = visible_mask(L, t, s)

    def hides(kind, x, y, sc):
        hw, top, bot = CROWN_BOX.get(kind, (18, 20, 0))
        x0, x1 = int(x - hw * sc), int(x + hw * sc)
        y0, y1 = int(y - top * sc), int(y - bot * sc) if bot else int(y)
        sub = vis[max(0, y0):max(0, y1), max(0, x0):max(0, x1)]
        return sub.size and sub.mean() > 0.06

    def ok(x, y, z, r):
        xi, yi = int(round(x)), int(round(y))
        if not (-16 <= xi < 320 + 16 and 4 <= yi < 576):
            return False
        cx, cy = min(max(xi, 0), zw.shape[1] - 1), min(max(yi, 0), zw.shape[0] - 1)
        if zw[cy, cx] != z or face[cy, cx] or water[cy, cx] or path[cy, cx] or keep[cy, cx]:
            return False
        if 0 <= xi < 320 and not (0 <= xi < zw.shape[1]):
            return False
        if any((x - a) ** 2 + (y - b) ** 2 < 22 ** 2 for a, b in stands):
            return False
        return all((x - a) ** 2 + (y - b) ** 2 >= r * r for a, b in feet)

    belt_mask = np.zeros(zw.shape, bool)
    for bi, ((x0, y0, x1, y1), sp_, mix, z) in enumerate(L.BELTS):
        kinds = list(mix)
        wts = np.array([mix[k] for k in kinds], float)
        wts /= wts.sum()
        belt_mask[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
        for gy in np.arange(y0 + sp_ * 0.5, y1, sp_ * 0.86):
            for gx in np.arange(x0 + (sp_ * 0.5 if int(gy) % 2 else 0), x1, sp_):
                x = gx + rng.uniform(-0.35, 0.35) * sp_
                y = gy + rng.uniform(-0.3, 0.3) * sp_
                if not ok(x, y, z, sp_ * 0.8):
                    continue
                kind = kinds[int(rng.choice(len(kinds), p=wts))]
                sc = round(float(rng.uniform(0.82, 1.08)), 2)
                if hides(kind, x, y, sc):
                    continue
                out.append((kind, int(round(x)), int(round(y)), sc, int(rng.integers(1, 10 ** 6))))
                feet.append((x, y))
    # undergrowth along the belts' edges (where a belt meets open ground)
    edge = belt_mask & ~ndi.binary_erosion(belt_mask, iterations=6)
    ys, xs = np.nonzero(edge)
    kinds = list(L.UNDER)
    wts = np.array([L.UNDER[k] for k in kinds], float)
    wts /= wts.sum()
    for i in rng.permutation(len(ys)):
        x, y = float(xs[i]), float(ys[i])
        z = int(zw[ys[i], xs[i]])
        if not ok(x, y, z, 12):
            continue
        kind = kinds[int(rng.choice(len(kinds), p=wts))]
        sc = round(float(rng.uniform(0.75, 1.05)), 2)
        if hides(kind, x, y, sc):
            continue
        out.append((kind, int(x), int(y), sc, int(rng.integers(1, 10 ** 6))))
        feet.append((x, y))
    return out


# approximate sprite boxes (world px at scale 1) used before a plant is drawn: (half width, top
# above the foot, bottom of the crown above the foot)
CROWN_BOX = {'oak': (37, 86, 30), 'beech': (37, 86, 30), 'pine': (23, 86, 12), 'birch': (19, 80, 40),
             'sapling': (16, 52, 24), 'bush': (18, 20, 0), 'bramble': (18, 20, 0), 'holly': (18, 20, 0)}


def visible_mask(L, t, s):
    """What the wood must not hide (world px): the ways, the water, the places and the stands."""
    H, W = t.z.shape
    k = int(s)
    v = (t.path | t.water)[::k, ::k].copy()
    for (x0, y0, x1, y1) in [L.GLADE, L.RING, L.SEAT]:
        v[max(0, y0 + 8):y1 - 8, max(0, x0 + 8):x1 - 8] = True
    for (x, y) in L.STANDS.values():
        v[max(0, y - 20):y + 4, max(0, x - 10):x + 10] = True
    return v


def classify(L, t, s, objects, wood, block=None):
    """Which of the wood stays a zone object and which is baked: a pixel of a tree can be
    overlapped by the walker (feet anywhere walkable within 8 px across and 30 px below it);
    if every such walker stands south of the tree's foot the pixel goes in the ground (the
    walker is always in front), if every one stands north of it, in the canopy layer drawn
    over everything (always behind); a tree with pixels of both kinds stays an object, sorted
    by depth in the game. A baked tree whose pixels overlap an object it would be drawn on the
    wrong side of stays an object too. Returns (objects, ground, overhead)."""
    k = int(s)
    walk = t.walk[::k, ::k] & (t.z[::k, ::k] == 0)
    if block is not None:
        walk = walk & ~block
    Hh, Ww = walk.shape
    rows = np.arange(Hh)[:, None] * np.ones((1, Ww), int)
    big = 10 ** 6
    lo = ndi.minimum_filter(np.where(walk, rows, big), size=(31, 17), origin=(-15, 0), mode='constant', cval=big)
    hi = ndi.maximum_filter(np.where(walk, rows, -1), size=(31, 17), origin=(-15, 0), mode='constant', cval=-1)

    def place(item):
        _i, _k, (x, y), d = item
        a = d.alpha[::k, ::k]
        return a, int(round(x - d.anchor[0] / s)), int(round(y - d.anchor[1] / s)), y

    def overlap(p, q):
        a, ax, ay, _ = p
        b, bx, by, _ = q
        x0, y0 = max(ax, bx), max(ay, by)
        x1, y1 = min(ax + a.shape[1], bx + b.shape[1]), min(ay + a.shape[0], by + b.shape[0])
        if x0 >= x1 or y0 >= y1:
            return False
        return bool((a[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & b[y0 - by:y1 - by, x0 - bx:x1 - bx]).any())

    keep, ground, over = [], [], []
    placed_objs = [place(o) for o in objects]
    pend = []
    for item in wood:
        p = place(item)
        a, x0, y0, y = p
        cls = np.zeros(a.shape, np.int8)          # 1 ground (walker always in front), 2 canopy (behind), 3 mixed
        ys, xs = np.nonzero(a)
        X, Y = np.clip(xs + x0, 0, Ww - 1), np.clip(ys + y0, 0, Hh - 1)
        l, h = lo[Y, X], hi[Y, X]
        none = h < 0
        front = none | (l > y)
        behind = ~none & (h < y)
        cls[ys, xs] = np.where(front, 1, np.where(behind, 2, 3))
        pend.append([item, p, cls])
    # a tree with a pixel the walker can stand both in front of and behind stays an object; so
    # does one whose baked pixels would cross an object on the wrong side; repeat until settled
    # every pixel is baked, none kept as an object: a pixel the walker can stand both in front
    # of and behind goes in the ground if it is in the tree's lowest 20 px (its trunk and
    # skirt, which the walker passes in front of) and in the canopy above that; a pixel that
    # would be drawn on the wrong side of a zone object goes to the side that is right there
    for e in pend:
        item, p, cls = e
        a, x0, y0, y = p
        rows = np.arange(a.shape[0])[:, None] + y0
        mixed = cls == 3
        cls[mixed & (rows > y - 20)] = 1
        cls[mixed & (rows <= y - 20)] = 2
        for q in placed_objs:
            sub = _overlap_mask(p, q)
            if sub is None:
                continue
            m, (ya, yb, xa, xb) = sub
            c = cls[ya:yb, xa:xb]
            if q[3] < y:
                c[(c == 1) & m] = 2       # a farther object must not draw over this nearer tree
            elif q[3] > y:
                c[(c == 2) & m] = 1       # this tree must not draw over a nearer object
    for e in pend:
        if e is None:
            continue
        item, p, cls = e
        big_cls = np.repeat(np.repeat(cls, k, 0), k, 1)[:item[3].alpha.shape[0], :item[3].alpha.shape[1]]
        if (big_cls == 1).any():
            ground.append((item, big_cls == 1))
        if (big_cls == 2).any():
            over.append((item, big_cls == 2))
    return keep, ground, over


def _overlap_mask(p, q):
    a, ax, ay, _ = p
    b, bx, by, _ = q
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + a.shape[1], bx + b.shape[1]), min(ay + a.shape[0], by + b.shape[0])
    if x0 >= x1 or y0 >= y1:
        return None
    m = b[y0 - by:y1 - by, x0 - bx:x1 - bx]
    if not m.any():
        return None
    return m, (y0 - ay, y1 - ay, x0 - ax, x1 - ax)


def pieces(over: Image.Image, s: float):
    """The canopy layer cut into pieces round what it covers (connected crowns), each cropped
    to whole world px: [(id, key, top-left (world px), image)]."""
    a = np.asarray(over)[..., 3] > 0
    if not a.any():
        return []
    lab, n = ndi.label(ndi.binary_dilation(a, iterations=2))
    out = []
    k = int(s)
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        y0, y1 = sl[0].start - sl[0].start % k, sl[0].stop + (-sl[0].stop) % k
        x0, x1 = sl[1].start - sl[1].start % k, sl[1].stop + (-sl[1].stop) % k
        im = over.crop((x0, y0, x1, y1))
        m = np.asarray(im).copy()
        sub = (lab[y0:y1, x0:x1] != i)
        m[sub] = 0
        out.append((f'canopy-{i}', f'wd_canopy{i}', (x0 // k, y0 // k), Image.fromarray(m, 'RGBA')))
    return out

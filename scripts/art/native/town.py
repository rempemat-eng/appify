"""A village zone for the game from its zone plan (game/data/plans/<id>.json), drawn with the
kit: the ground in palette codes (lawn, the paved square, worn roads and paths, dry-stone
retaining walls with their lips and feet, the gate stair, burnt lots, the crater, the green's
ring, the static cast shadows) and one picture per object (buildings, their damage overlays,
props, things and dressing), with every object's foot, its condition and its collision box.

    python3 -m scripts.art.native.town --plan game/data/plans/crossroads.json --density 3 \\
        --out game/zones/crossroads/art --preview DIR

writes <out>/ground.png, <out>/<picture>.png and <out>/../kit.json; with --preview, the whole zone
composed for each of the plan's stages (DIR/<zone>_<stage>.png). game/tools/gen_village.py reads
kit.json and writes the Godot scene. Units: plan positions are world px; pictures and kit.json
positions are texels (world px x density).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import ctx, load_biome, load_plan  # noqa: E402

# the kit's own sprites placed as dressing (foliage, the garden lantern, boulders): measured by the kit's
# golden scene, not by the village gate
KIT_SPRITES = ('oak', 'bush', 'kit_lantern', 'boulder')


# ------------------------------------------------------------------------------------------------
# conditions (the game's Quests.check subset the plans use)
# ------------------------------------------------------------------------------------------------
def holds(cond, state) -> bool:
    if not cond:
        return True
    rs, fl = set(state.get('restored', [])), set(state.get('flags', []))
    if any(r not in rs for r in cond.get('restored', [])):
        return False
    if any(r in rs for r in cond.get('not_restored', [])):
        return False
    if any(f not in fl for f in cond.get('flags', [])):
        return False
    if any(f in fl for f in cond.get('not_flags', [])):
        return False
    return True


def stage_states(plan) -> dict:
    """Each stage of the plan as the world state that reaches it (restores and flags)."""
    out = {}
    for st in plan.get('stages', []):
        c = st.get('if', {})
        out[st['id']] = dict(restored=list(c.get('restored', [])), flags=list(c.get('flags', [])))
    return out


# ------------------------------------------------------------------------------------------------
# what a drawn zone is made from (check.py compares it with kit.json's `inputs`)
INPUTS = ('village.py', 'town.py', 'palette.py', 'raster.py', 'props.py', 'foliage.py', 'compose.py', 'ctx.py',
          'terrain/sheets.py', 'masters/zones_props_oak.png', 'masters/zones_props_bush.png')


def input_hash(plan_path: str, density: float) -> str:
    import hashlib
    h = hashlib.sha256(('density %g\n' % density).encode())
    files = [os.path.join(HERE, f) for f in INPUTS] + [plan_path, os.path.join(ROOT, 'art', 'house-palette.json'),
                                                       os.path.join(ROOT, 'scripts', 'art', 'house_palette.py')]
    plan = json.load(open(plan_path))
    files.append(os.path.join(ROOT, 'scripts', 'art', 'biomes', plan.get('art', {}).get('biome', 'meadow') + '.json'))
    for f in files:
        h.update(os.path.relpath(f, ROOT).encode() + b'\0')
        h.update(open(f, 'rb').read())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------
def build(plan: dict, out_dir: str, preview: str | None = None) -> dict:
    from scripts.art.native import compose as CO
    from scripts.art.native import village as V
    from scripts.art.native.palette import C, FI, step, to_rgba
    from scripts.art.native.terrain import sheets

    D = ctx.D
    q = V.q
    bx, by, bw, bh = plan['box']
    W, H = q(bw), q(bh)
    rng = np.random.default_rng(plan.get('seed', 7))
    YY, XX = np.mgrid[0:H, 0:W]
    WX, WY = (XX + 0.5) / D, (YY + 0.5) / D           # world px at each texel

    def rect_m(r, grow=0.0):
        x, y, w, h = r
        return (WX >= x - grow) & (WX < x + w + grow) & (WY >= y - grow) & (WY < y + h + grow)

    def noise(sig, seed, amp=1.0):
        a = ndi.gaussian_filter(np.random.default_rng(seed).random((H // 3 + 2, W // 3 + 2)), sig * D / 3)
        a = (a - a.mean()) / (a.std() + 1e-9)
        return ndi.zoom(a, 3, order=1)[:H, :W] * amp

    # --- the lawn and the uplands ---------------------------------------------------------------
    cv = sheets.grass_field_d(bw, bh, seed=plan.get('lawn_seed', 3)).astype(np.int32)
    up = sheets.grass_field_d(bw, bh, seed=plan.get('lawn_seed', 3) + 1, base_tone=2, density=1.3).astype(np.int32)
    art = plan.get('art', {})
    upland = np.zeros((H, W), bool)
    for r in art.get('uplands', []):
        upland |= rect_m(r)
    cv[upland] = up[upland]
    dirt = sheets.path_sheet_d(bw, bh, seed=11).astype(np.int32)
    track = sheets.path_sheet_d(bw, bh, seed=12, body=3).astype(np.int32)

    def lone_fix(a, keep=None):
        V.tidy(a, passes=2, keep=keep)

    # --- the green's ring ------------------------------------------------------------------------
    for pl in plan.get('places', []):
        if pl['kind'] == 'green' and art.get('ring'):
            cx, cy, rx, ry, wd = art['ring']
            e = ((WX - cx) / rx) ** 2 + ((WY - cy) / ry) ** 2
            band = (e > (1 - wd / rx) ** 2) & (e < 1) & (noise(2.0, 51) > -0.7)
            cv[band] = np.where(noise(1.2, 52)[band] > 0.3, C('grass_warm', 3), C('path', 4))

    # --- roads and paths, worn at their edges ------------------------------------------------------
    def polyline_dist(pts):
        d = np.full((H, W), 1e9)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy or 1e-9
            t = np.clip(((WX - x0) * dx + (WY - y0) * dy) / L2, 0, 1)
            d = np.minimum(d, np.hypot(WX - x0 - t * dx, WY - y0 - t * dy))
        return d

    pathm = np.zeros((H, W), bool)
    for k, r in enumerate(plan.get('routes', [])):
        hw = r.get('width', 24) / 2 - (3 if r['kind'] == 'road' else 4)
        d = polyline_dist(r['points'])
        wob = noise(3.0, 60 + k, 1.4) + noise(1.0, 80 + k, 0.5)
        m = d < hw + wob
        src = dirt if r['kind'] == 'road' else track
        cv[m] = src[m]
        # ruts down a road: two worn lines a tone down
        if r['kind'] == 'road':
            for off in (-hw * 0.45, hw * 0.45):
                rut = (np.abs(d - abs(off)) < 0.9) & m & (noise(1.5, 90 + k) > -0.4)
                cv[rut] = step(cv[rut], -1)
        pathm |= m

    # --- places ------------------------------------------------------------------------------------
    # the paved square: rounded on the soft grid (cell 8 world px, corner radius one cell)
    pave = np.zeros((H, W), bool)
    for r in art.get('paving', []):
        x, y, w, h = r
        rad = 8.0
        cx_ = np.clip(WX, x + rad, x + w - rad)
        cy_ = np.clip(WY, y + rad, y + h - rad)
        pave |= rect_m(r) & ((WX - cx_) ** 2 + (WY - cy_) ** 2 <= rad * rad)
    if pave.any():
        # setts: small, irregular, worn; calm (few dark joints) so people and props read on top
        flags = np.full((H, W), C('stone_warm', 3), np.int32)
        y = 0
        while y < H:
            rh = q(rng.uniform(2.4, 3.2))
            x = -int(rng.integers(0, q(4)))
            while x < W:
                sw = q(rng.uniform(3.0, 5.6))
                fam = ('stone_warm', 'stone_warm', 'stone_warm', 'stone_cool')[int(rng.integers(0, 4))]
                t = int(rng.choice([4, 4, 4, 4, 4, 3, 5]))
                jx = int(rng.integers(0, 2))         # irregular joints: some setts butt tight
                V.blk(flags, x, y, x + sw - jx, y + rh - 1, fam, t, cut=1, top=1, left=0, bot=0, right=0)
                if rng.random() < 0.06:
                    V.fill(flags, x + 2, y + 2, x + 4, y + 4, C(fam, max(2, t - 1)))   # a worn dip
                x += sw
            y += rh
        # the joints a calm mid tone (not a dark grid), darker only in a few soft patches
        jm = flags == C('stone_warm', 3)
        flags[jm & (noise(2.5, 36) > 1.8)] = C('stone_warm', 2)
        cv[pave] = flags[pave]
        # worn smooth where feet go: paler soft patches
        wear = pave & (noise(5.0, 33) > 0.8) & (cv % 8 == 4)
        cv[wear] = cv[wear] + 1
        # a ring of setts round the well, the same size, laid in circles inside a kerb
        for sr in art.get('setts', []):
            cx, cy, r0, r1 = sr
            disc = (((WX - cx) / r1) ** 2 + ((WY - cy) / (r1 * 0.86)) ** 2) < 1.0
            cv[disc] = C('stone_warm', 3)
            rr = r0
            while rr < r1 - 2.5:
                n = max(8, int(2 * math.pi * rr / 4.4))
                ph = rng.uniform(0, 1)
                for k in range(n):
                    a0 = 2 * math.pi * (k + ph) / n
                    sx, sy = cx + math.cos(a0) * rr, cy + math.sin(a0) * rr * 0.86
                    V.blk(cv, q(sx - 1.9), q(sy - 1.2), q(sx + 1.9), q(sy + 1.2),
                          ('stone_warm', 'stone')[k % 2], int(rng.choice([3, 4, 4])), cut=1, top=1, left=0, bot=0, right=0)
                rr += 2.8
            kerb_r = disc & ~((((WX - cx) / (r1 - 2.0)) ** 2 + ((WY - cy) / ((r1 - 2.0) * 0.86)) ** 2) < 1.0)
            cv[kerb_r] = C('stone_warm', 4)
            cv[kerb_r & (WY > cy + 3)] = C('stone_warm', 3)
            rim_in = kerb_r & ~ndi.binary_erosion(disc, iterations=q(2.0) + 1)
            outer_line = disc & ~ndi.binary_erosion(disc, iterations=1)
            cv[outer_line] = C('stone', 2)
        # the kerb: a course of long edging stones round the square, lit on top, a dark front on the
        # south side, broken where a road comes in; grass creeping over it, worn spots outside
        edge_d = ndi.distance_transform_edt(pave) / D
        out_d = ndi.distance_transform_edt(~pave) / D
        kerb = pave & (edge_d < 3.4) & ~ndi.binary_dilation(pathm, iterations=q(2))
        gy, gx = np.gradient(edge_d)
        vertical = np.abs(gx) > np.abs(gy)
        kh = np.full((H, W), C('stone', 2), np.int32)
        kv = np.full((H, W), C('stone', 2), np.int32)
        x = 0
        while x < W:
            L_ = q(rng.uniform(6, 10))
            V.blk(kh, x, 0, x + L_ - 1, H, 'stone_warm', int(rng.choice([4, 4, 3])), cut=0, top=0, left=1, bot=0, right=-1)
            x += L_
        y = 0
        while y < H:
            L_ = q(rng.uniform(6, 10))
            V.blk(kv, 0, y, W, y + L_ - 1, 'stone_warm', int(rng.choice([4, 4, 3])), cut=0, top=1, left=0, bot=-1, right=0)
            y += L_
        kcode = np.where(vertical, kv, kh)
        cv[kerb] = kcode[kerb]
        inner = kerb & (edge_d >= 3.4 - 1.0 / D)
        cv[inner] = C('stone', 2)                              # the joint between kerb and setts
        south = kerb & (gy < -0.2) & (edge_d < 1.0)
        cv[south] = C('stone', 2)                              # the kerb's dark front
        # outside: a contact line on the lawn, grass tufts over the kerb, worn earth here and there
        contact = (out_d > 0) & (out_d < 1.4) & ~pathm
        cv[contact] = step(cv[contact], -2)
        tuft = pave & (edge_d < 4.5) & (noise(1.1, 37) > 0.85) & ~ndi.binary_dilation(pathm, iterations=q(2))
        cv[tuft] = C('grass', 3)
        cv[tuft & (noise(0.7, 38) > 0.5)] = C('grass_cool', 2)
        cv[tuft & (noise(0.7, 40) > 1.0)] = C('grass', 4)
        worn = (out_d > 0) & (out_d < 3.5) & (noise(2.0, 39) > 1.3) & ~pathm
        cv[worn] = C('path_warm', 4)
        cv[worn & (out_d > 2.5)] = C('grass_warm', 3)

    # puddles left by the storm: still water in a hollow, the sky in it, a dark north rim
    for k_, (px, py, prx, pry) in enumerate(art.get('puddles', [])):
        e = ((WX - px) / prx) ** 2 + ((WY - py) / pry) ** 2 + noise(1.2, 120 + k_, 0.12)
        m = e < 1.0
        cv[m] = C('water', 2)
        cv[m & (WY > py)] = C('water', 3)
        cv[m & (e < 0.35) & (WX < px)] = C('sky', 4)
        north = m & ~np.roll(m, q(1.2), axis=0)
        cv[north] = C('water_cool', 1)
        wet = (e >= 1.0) & (e < 1.5) & ~m
        cv[wet] = step(cv[wet], -1)

    for pl in plan.get('places', []):
        x, y, w, h = pl['rect']
        if pl['kind'] == 'crater':
            cx, cy, rx, ry = x + w / 2, y + h / 2, w / 2, h / 2
            e = np.sqrt(((WX - cx) / rx) ** 2 + ((WY - cy) / ry) ** 2)
            wob = noise(1.6, 41, 0.07)
            scorch = (e < 1.55 + wob * 3) & (e >= 1.0 + wob)
            cv[scorch & (noise(1.0, 42) > -0.2)] = C('earth', 2)
            cv[scorch & (noise(1.0, 43) > 0.6)] = C('earth_cool', 1)
            rim = (e < 1.0 + wob) & (e >= 0.72 + wob)
            north = WY < cy
            cv[rim & north] = C('earth', 4)
            cv[rim & ~north] = C('earth', 3)
            cv[rim & (WX > cx + rx * 0.3)] = C('earth', 2)
            pit = e < 0.72 + wob
            cv[pit] = C('earth_cool', 1)
            cv[pit & (WY < cy - ry * 0.2)] = C('earth_cool', 0)   # the north wall in shade
            cv[(e < 0.35) & pit] = C('earth', 1)
            for _ in range(14):
                a_ = rng.uniform(0, 2 * math.pi)
                rr = rng.uniform(1.15, 1.9)
                sx, sy = cx + math.cos(a_) * rx * rr, cy + math.sin(a_) * ry * rr
                V.blk(cv, q(sx), q(sy), q(sx) + q(rng.uniform(2, 4)), q(sy) + q(rng.uniform(1.6, 2.6)),
                      ('crag', 'crag_warm', 'stone')[int(rng.integers(0, 3))], int(rng.choice([2, 3])), cut=1)
        elif pl['kind'] == 'lot':
            pass

    for k_, lot in enumerate(plan.get('lots', [])):
        x, y, w, h = lot['rect']
        # the burnt ground: ash and soot in soft clusters, its edge frayed into the lawn
        e = np.maximum(np.abs(WX - (x + w / 2)) / (w / 2), np.abs(WY - (y + h / 2)) / (h / 2))
        m = e < 1.0 + noise(1.6, 70 + k_, 0.08)
        cv[m] = C('earth', 2)
        cv[m & (noise(1.8, 71 + k_) > 0.1)] = C('earth_cool', 2)
        cv[m & (noise(2.2, 72 + k_) > 0.7)] = C('earth_cool', 1)
        cv[m & (e > 0.82) & (noise(1.0, 75 + k_) > 0.4)] = C('grass_cool', 2)
        # the old footings: a course of stones round where the walls stood, broken in places
        tmp = np.full((H, W), -1, np.int32)
        V.rubble(tmp, q(x + 4), q(y + 4), q(x + w - 4), q(y + h - 4), rng, base=3, course=(3, 3.6), length=(4, 7), moss=0.3)
        ring = rect_m([x + 4, y + 4, w - 8, h - 8]) & ~rect_m([x + 8, y + 8, w - 16, h - 16])
        keep = ring & (noise(2.6, 73 + k_) > -0.6) & (tmp >= 0)
        cv[keep] = tmp[keep]
        # a chimney's stump in one corner, charred beams fallen across the floor
        V.rubble(cv, q(x + w - 18), q(y + 6), q(x + w - 6), q(y + 16), rng, base=3, course=(2.6, 3), length=(3, 5), moss=0)
        for k in range(3):
            x0, y0 = q(x + rng.uniform(10, w - 26)), q(y + rng.uniform(14, h - 10))
            V.bar(cv, x0, y0, x0 + q(rng.uniform(14, 22)), y0 + q(rng.uniform(-6, 6)), q(1.4), 'timber_cool', 1)
        for k in range(5):
            sx, sy = q(x + rng.uniform(10, w - 10)), q(y + rng.uniform(10, h - 8))
            V.blk(cv, sx, sy, sx + q(rng.uniform(2.5, 4)), sy + q(rng.uniform(1.6, 2.6)), 'stone', int(rng.choice([2, 3])), cut=1)

    # --- retaining walls (faces) and the gate stair ---------------------------------------------------
    stairs = plan.get('stairs', [])
    for f in art.get('walls', []):
        x, y, w, h = f
        x0, y0, x1, y1 = q(x), q(y), q(x + w), q(y + h)
        tmp = np.full((H, W), -1, np.int32)
        V.rubble(tmp, x0, y0, x1, y1, rng, base=3, course=(3.0, 4.6), length=(5, 11), moss=0.3)
        # the shade under the lip
        tmp[y0:y0 + q(2.2), x0:x1] = step(tmp[y0:y0 + q(2.2), x0:x1], -1)
        cut = np.zeros((H, W), bool)
        for st in stairs:
            sx, sy = st['at']
            sw = st.get('width', 40)
            cut |= rect_m([sx - sw / 2, y - 1, sw, h + 2])
        sel = (tmp >= 0) & ~cut
        cv[sel] = tmp[sel]
        # the lip: the lawn above ends in a darker row, tufts hang over the top course
        lip = rect_m([x, y - 1.0, w, 1.0]) & ~cut
        cv[lip] = step(cv[lip], -1)
        for k in range(int(w / 9)):
            tx = x + rng.uniform(0, w)
            if cut[min(H - 1, y0), min(W - 1, q(tx))]:
                continue
            tw, th = rng.uniform(3, 6), rng.uniform(1.6, 3.2)
            m = V.ellipse_mask((H, W), q(tx), y0, q(tw / 2), q(th))
            m &= (WY >= y - 1.5)
            cv[m] = C('grass', 3)
            cv[m & (WY >= y + th * 0.4)] = C('grass_cool', 2)
        # the foot: a damp dark band on the ground below, pebbles and weeds over it
        foot = rect_m([x, y + h, w, 2.6]) & ~cut
        cv[foot] = step(cv[foot], -1)
        foot2 = rect_m([x, y + h, w, 1.0]) & ~cut
        cv[foot2] = step(cv[foot2], -1)
        for k in range(int(w / 14)):
            px = x + rng.uniform(0, w)
            if cut[min(H - 1, y1 + 2), min(W - 1, q(px))]:
                continue
            V.blk(cv, q(px), y1 + q(0.5), q(px) + q(rng.uniform(2, 3.5)), y1 + q(2.2), 'stone', 3, cut=1)
    for st in stairs:
        sx, sy = st['at']
        sw = st.get('width', 40)
        wall = [f for f in art.get('walls', []) if f[0] <= sx <= f[0] + f[2] or abs(f[1] - sy) < 12]
        y0w = min(f[1] for f in wall) if wall else sy - 6
        y1w = max(f[1] + f[3] for f in wall) if wall else sy + 6
        x0, x1 = q(sx - sw / 2), q(sx + sw / 2)
        n = st.get('steps', 3)
        top = q(y0w) - q(3)
        bot = q(y1w) + q(1)
        hstep = (bot - top) / n
        for k in range(n):
            ya = int(top + k * hstep)
            yb = int(top + (k + 1) * hstep)
            tread = max(3, int(hstep * 0.45))
            xx = x0 + q(3)
            while xx < x1 - q(3):
                L_ = q(rng.uniform(8, 13))
                xe = min(xx + L_, x1 - q(3))
                V.blk(cv, xx, ya, xe - 1, ya + tread, ('stone_warm', 'stone')[k % 2], 4, cut=1)
                V.blk(cv, xx, ya + tread, xe - 1, yb, 'stone', 2, cut=0, top=0)
                xx = xe
        for (cx0, cx1, t) in ((x0, x0 + q(3.5), 3), (x1 - q(3.5), x1, 2)):
            V.rubble(cv, cx0, top - q(2), cx1, bot, rng, base=t, course=(2.6, 3.2), length=(3, 4), moss=0.2)
            V.blk(cv, cx0 - 1, top - q(3.5), cx1 + 1, top - q(1.5), 'stone_warm', 4, cut=1)
        # the path meets the stair head and foot
        pathm |= rect_m([sx - sw / 2 + 3, y0w - 6, sw - 6, y1w - y0w + 12])

    # --- objects ---------------------------------------------------------------------------------------
    objects = []      # dicts: id, png, foot (texels), anchor, if, solid (world rect), sort, kind, layer
    pics = {}

    def add_pic(name, img):
        pics[name] = img
        return name

    def cond_of(item):
        return item.get('if')

    looks = art.get('looks', {})
    for b in plan.get('buildings', []):
        look = dict(looks.get(b['id'], {}))
        x, y, w, h = b['rect']
        look.setdefault('w', w)
        look.setdefault('depth', h)
        built = V.building(look, seed=look.get('seed', sum(map(ord, b['id']))))
        foot = (q(x + w / 2), q(y + h))
        objects.append(dict(id=b['id'], kind='building', png=add_pic(b['id'], built.base.rgba()),
                            foot=foot, anchor=(built.base.ax, built.base.ay), alpha=built.base.alpha(),
                            solid=[x, y, w, h], cond=None, static=True))
        if built.damage is not None:
            dcond = {'not_restored': [b['restore']]} if b.get('restore') else None
            objects.append(dict(id=b['id'] + '_damage', kind='damage', png=add_pic(b['id'] + '_damage', built.damage.rgba()),
                                foot=(foot[0], foot[1] + 1), anchor=(built.damage.ax, built.damage.ay + 1),
                                alpha=built.damage.alpha(), solid=None, cond=dcond, static=False, of=b['id']))

    def inside_building(r):
        x, y, w, h = r
        for b in plan.get('buildings', []):
            bx_, by_, bw_, bh_ = b['rect']
            if bx_ <= x and x + w <= bx_ + bw_ and by_ <= y and y + h <= by_ + bh_ + 2:
                return b
        return None

    PROP_KIND = {'rubble': 'rubble', 'well': 'well', 'glow': 'glow', 'anvil': 'anvil', 'smoke': 'smoke', 'stall': 'stall'}
    for p in plan.get('props', []):
        x, y, w, h = p['rect']
        kind = p['kind']
        if p['id'] == 'well_choked':
            kind = 'well_choked'
        if kind == 'lantern':
            kind = 'lantern_lit' if 'lit' in p['id'] else 'lantern'
        if kind == 'beds':
            kind = 'beds_dug' if 'dug' in p['id'] else 'beds'
        host = inside_building(p['rect'])
        entry = dict(id=p['id'], kind=kind, cond=cond_of(p), solid=[x, y, w, h] if p.get('solid') else None,
                     static=not cond_of(p))
        if kind == 'boards' and host is not None:
            entry.update(png=None)          # drawn in the building's damage overlay
            objects.append(entry)
            continue
        pic = V.prop(kind, w, h, seed=sum(map(ord, p['id'])))
        foot = (q(x + w / 2), q(y + h))
        if host is not None and kind == 'glow':
            # the fire burns inside the forge's mouth: sort it just in front of the building
            hx, hy, hw_, hh_ = host['rect']
            foot = (q(x + w / 2), q(hy + hh_) + 2)
            entry['lift'] = q(hy + hh_) + 2 - q(y + h)
        entry.update(png=add_pic(p['id'], pic.rgba()), foot=foot, anchor=(pic.ax, pic.ay), alpha=pic.alpha())
        objects.append(entry)

    THING_KIND = {'notice_board': 'notice_board', 'waystone': 'waystone'}
    for t in plan.get('things', []):
        if t['speaker'] in THING_KIND:
            pic = V.prop(THING_KIND[t['speaker']], 10, 6, seed=5)
            x, y = t['at']
            objects.append(dict(id=t['id'], kind=t['speaker'], png=add_pic(t['id'], pic.rgba()), foot=(q(x), q(y)),
                                anchor=(pic.ax, pic.ay), alpha=pic.alpha(), cond=cond_of(t), solid=None, static=not cond_of(t)))

    tree_ex = dict(oak=dict(w=65, h=78, tw=11, ch=50), tree=dict(w=46, h=60, tw=8, ch=38))
    for k, dr in enumerate(art.get('dressing', [])):
        kind = dr['kind']
        x, y = dr['at']
        seed = dr.get('seed', 100 + k)
        if kind in ('oak', 'bush'):
            master = 'zones_props_oak.png' if kind == 'oak' else 'zones_props_bush.png'
            img, anc, a = CO.sprite_for(kind, master, D, seed, tree_ex.get(kind, {}))
            solid = [x - 4, y - 3, 8, 4] if kind == 'oak' else ([x - 8, y - 5, 16, 6] if dr.get('solid', True) else None)
        elif kind == 'kit_lantern':
            img, anc, a = CO.sprite_for('lantern', None, D, seed, {})
            solid = [x - 2, y - 2, 4, 3]
        elif kind == 'boulder':
            img, anc, a = CO.sprite_for('boulder', None, D, seed, {})
            solid = [x - 6, y - 4, 12, 5]
        else:
            w, h = dr.get('size', [12, 8])
            pic = V.prop(kind, w, h, seed=seed)
            img, anc, a = pic.rgba(), (pic.ax, pic.ay), pic.alpha()
            solid = [x - w / 2, y - h, w, h] if dr.get('solid', True) else None
        did = dr.get('id', f'{kind}_{k}')
        objects.append(dict(id=did, kind=kind, png=add_pic(did, img), foot=(q(x), q(y)), anchor=anc, alpha=a,
                            cond=dr.get('if'), solid=solid, static=not dr.get('if')))

    # --- static cast shadows into the ground, then tidy ---------------------------------------------
    kx, ky = CO.SHADOW
    rim = max(2, q(2))
    for o in objects:
        if not o.get('static') or o.get('png') is None or o['kind'] in ('glow', 'smoke', 'damage'):
            continue
        m = CO.shadow_mask(o['alpha'], o['anchor'], D, W, H, o['foot'], kx, ky)
        core = ndi.binary_erosion(m, iterations=rim)
        cv[m] = step(cv[m], -1)
        cv[core] = step(cv[core], -1)
    lone_fix(cv, keep=(cv % 8 >= 6))
    ground = Image.fromarray(to_rgba(cv), 'RGBA').convert('RGB')

    # --- write ---------------------------------------------------------------------------------------
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith('.png') and f != 'ground.png' and f[:-4] not in pics:
            os.remove(os.path.join(out_dir, f))
    ground.save(os.path.join(out_dir, 'ground.png'), optimize=True)
    for name, img in pics.items():
        img.save(os.path.join(out_dir, name + '.png'), optimize=True)
    doc = dict(zone=plan['id'], density=D, size=[W, H], inputs=plan.get('_inputs'),
               kit_drawn=sorted({o['png'] + '.png' for o in objects if o.get('png') and o['kind'] not in KIT_SPRITES}),
               objects=[])
    for o in objects:
        e = dict(id=o['id'], kind=o['kind'], png=(o['png'] + '.png') if o.get('png') else None,
                 foot=[int(o['foot'][0]), int(o['foot'][1])] if o.get('png') else None,
                 offset=[-int(o['anchor'][0]), -int(o['anchor'][1]) - int(o.get('lift', 0))] if o.get('png') else None,
                 cond=o.get('cond'), solid=o.get('solid'))
        if o.get('of'):
            e['of'] = o['of']
        doc['objects'].append(e)
    json.dump(doc, open(os.path.join(os.path.dirname(out_dir.rstrip('/')), 'kit.json'), 'w'), indent=1)

    if preview:
        os.makedirs(preview, exist_ok=True)
        for sid, state in stage_states(plan).items():
            img = ground.convert('RGBA')
            for o in sorted([o for o in objects if o.get('png')], key=lambda o: (o['foot'][1], o['kind'] == 'damage')):
                if not holds(o.get('cond'), state):
                    continue
                pic = pics[o['png']]
                X = int(o['foot'][0] - o['anchor'][0])
                Y = int(o['foot'][1] - o['anchor'][1] - o.get('lift', 0))
                sx, sy = max(0, -X), max(0, -Y)
                img.alpha_composite(pic.crop((sx, sy, pic.width, pic.height)), (X + sx, Y + sy))
            img.convert('RGB').save(os.path.join(preview, f"{plan['id']}_{sid}.png"))
    return dict(zone=plan['id'], size=[W, H], objects=len(objects), pictures=len(pics))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--density', type=float, default=3.0)
    ap.add_argument('--out', required=True)
    ap.add_argument('--preview', default=None)
    a = ap.parse_args(argv)
    plan = json.load(open(a.plan))
    biome = load_biome(plan.get('art', {}).get('biome', 'meadow'))
    # the kit's painters size their sheets from a plan at import: the pilot's (the village paints
    # its own ground and only borrows the lawn and dirt fields, the foliage and the shadow rule)
    ctx.configure(a.density, biome, load_plan('pilot'))
    plan['_inputs'] = input_hash(os.path.abspath(a.plan), a.density)
    res = build(plan, a.out, a.preview)
    print(json.dumps(res))
    return 0


if __name__ == '__main__':
    sys.exit(main())

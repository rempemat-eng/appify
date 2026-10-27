"""Bake a kit zone's ground with the painters that drew the hand-painted woodland (docs/world-editor.md,
"Baking the ground"). Matt, 27 Oct 17:00, on the woodland before and after: "i prefer the water,
paths, shadows of the trees before ... can you not create elements in the editor that mirror that
level of detail?"

The editor's tiles are the live preview while a zone is painted. What ships is this: each
material's whole outline, taken from the zone's cells on the soft grid (softgrid.shape, lumped
and rounded), painted by its own painter with its own parameters, the ones in its piece's
`terrain.paint` block:
- lawn: softground.lawn (the raised tiers' tops a calmer sibling, as the plateau swatch);
- path and worn ground: softground.dirt (the packed earth with its clods) and softground.sunken_edge
  (turf lobes, the shadow under the north lip, the lit south lip, tufts and stones);
- water: softground.water (the north bank's earth face under the grass lip, the light waterline,
  the depth band, ripples along the flow, lit shallows, rushes, bank stones) and tidy_bank;
- tiers: softground.ledge (the lit band, the rounded grass lip over the face, the under-lip shade,
  clods darker towards the foot, roots, the foot band with pebbles and weeds, side faces at the
  ends, the cast shadow), the plateau and cliff swatches' painter;
- scree: screen.scree.
Pieces with a `rendering.paint` block are painted into the ground where they stand: the waterfall
(rocks.face and rocks.fall, the woodland's cascade) and the log steps (softground.log_steps, cheeks,
treads with their noses and the risers' shade). Trees cast screen.tree_shadow_hd (the crown's shade
with sun flecks), everything else its sprite's own shadow (compose.shadow_mask), and the lawn takes
screen.ground_detail_hd and lawn_dressing_hd, as the woodland does.

    python3 -m scripts.art.kit.bake <zone>            # writes game/zones/<zone>/ground_baked.png
    python3 -m scripts.art.kit.bake --check            # exit 1 if a baked ground is stale
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.kit import surface as SF
from scripts.art.kit.schema import ROOT
from scripts.art.native import ctx
from scripts.art.native import compose as CO
from scripts.art.native import rocks as RK
from scripts.art.native import screen as SN
from scripts.art.native import softgrid as SG
from scripts.art.native import softground as GD
from scripts.art.native.palette import C, FI, is_fam

D = ctx.D
CELL = 24
ZONES = os.path.join(ROOT, 'game', 'kit', 'zones')
# the kit's own code: a change here makes a baked ground stale (check:kit). The native painters
# (softground, screen, rocks) are shared with every lane, so a change there is picked up at the
# next bake without failing anyone's check
SOURCES = ['scripts/art/kit/bake.py', 'scripts/art/kit/surface.py', 'scripts/art/kit/structures.py']


def _pieces_lib() -> dict:
    out = {}
    base = os.path.join(ROOT, 'game', 'kit', 'pieces')
    for kind in os.listdir(base):
        for f in os.listdir(os.path.join(base, kind)):
            if f.endswith('.json'):
                p = json.load(open(os.path.join(base, kind, f)))
                out[p['id']] = p
    return out


def out_path(zone: str) -> str:
    return os.path.join(ROOT, 'game', 'zones', zone, 'ground_baked.png')


def input_hash(plan: dict, lib: dict) -> str:
    h = hashlib.sha256()
    for s in SOURCES:
        h.update(open(os.path.join(ROOT, s), 'rb').read())
    keep = {k: plan.get(k) for k in ('legend', 'rows', 'tiers', 'pieces', 'variants', 'spawns', 'decor')}
    h.update(json.dumps(keep, sort_keys=True).encode())
    used = sorted(set(plan['legend'].values()) | {p['piece'] for p in plan.get('pieces', [])} | {'lawn', 'earth_face'})
    for u in used:
        if u in lib:
            h.update(json.dumps(lib[u], sort_keys=True).encode())
    return h.hexdigest()[:16]


def _shape(cells: np.ndarray, h: int, w: int, a: dict) -> np.ndarray:
    if not cells.any():
        return np.zeros((h, w), bool)
    kw = {}
    if 'amp' in a:
        kw['amp'] = tuple(a['amp'])
    if 'lump' in a:
        kw['lump'] = tuple(a['lump'])
    r_out = a.get('r_out', SG.R_TURN_OUT)
    r_in = a.get('r_in', SG.R_TURN_IN)
    m = SG.shape(cells, h, w, a.get('seed', 41), r_out=r_out, r_in=r_in, **kw)
    narrow_r = a.get('narrow_r', 0.45)
    if r_out > narrow_r:
        # width classes: a channel one or two cells wide keeps its own, smaller rounding (the
        # woodland's rill, r 0.45), where a wide body's rounding would close it
        narrow = cells & ~ndi.binary_opening(cells, structure=np.ones((3, 3), bool))
        if narrow.any():
            small = SG.shape(cells, h, w, a.get('seed', 41) + 1, r_out=narrow_r, r_in=narrow_r, **kw)
            zone = np.kron(ndi.binary_dilation(narrow, iterations=1), np.ones((CELL, CELL), bool))[:h, :w]
            # a narrow channel's lumps step a few texels at a time (the woodland's rill, gaussian 2.2)
            small = ndi.gaussian_filter(np.pad(small, 8, mode='edge').astype(float), 2.2)[8:-8, 8:-8] > 0.5
            m = m | (small & zone)
    if a.get('smooth'):
        # a worn track or a desire line follows its cells loosely: their staircase eased into a curve
        m = ndi.gaussian_filter(np.pad(m, 16, mode='edge').astype(float), float(a['smooth']))[16:-16, 16:-16] > 0.5
    return m


def _sprite(entry: dict, variant: str | None):
    v = entry['variants'].get(variant) if variant else None
    v = v or next(iter(entry['variants'].values()))
    img = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
    return img, tuple(v['foot'])


def _tree_ex(pid: str, img: Image.Image):
    """A tree's box for its crown shadow: the woodland recipe's master when the piece was seeded
    from one, else the sprite's own width."""
    kind = pid.split('_', 1)[1] if '_' in pid else pid
    rec = ctx.BIOME['recipes'].get(kind)
    if rec and rec.get('paint') == 'tree':
        ex = SN.tree_dims(rec['master'])
        if rec.get('trunk_w'):
            ex['tw'] = rec['trunk_w']
        return ex, kind
    a = np.asarray(img)[..., 3] > 0
    return dict(w=a.any(0).sum() / D, tw=6), kind


def bake(plan: dict, lib: dict | None = None):
    """(ground RGBA image, low items drawn) for a kit plan."""
    lib = lib or _pieces_lib()
    idx = json.load(open(os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')))
    rows = plan['rows']
    R, Cc = len(rows), len(rows[0])
    h, w = R * CELL, Cc * CELL
    mat = np.array([[plan['legend'].get(c, '') for c in r] for r in rows])
    tiers = np.array([[int(c) for c in r] for r in plan['tiers']]) if plan.get('tiers') else np.zeros((R, Cc), int)
    paint = {m: (lib[m]['terrain'].get('paint') or {}) for m in set(mat.ravel()) if m in lib}
    lawn_p = (lib['lawn']['terrain'].get('paint') or {}).get('args', {})
    cv = GD.lawn(h, w, lawn_p.get('seed', 977))
    face_h = int((lib['earth_face']['terrain'].get('paint') or {}).get('args', {}).get('face_px', 48))
    # the tiers' tops and the face bands under them (where nothing else is painted)
    tops, band = [], np.zeros((h, w), bool)
    # one ledge per level present, its face two cells for each tier it drops (a top two tiers over
    # the ground beside it shows a face four cells high, as the woodland's cascade)
    levels = sorted(int(v) for v in np.unique(tiers) if v > 0)
    drops = []
    for i, t in enumerate(levels):
        ea = (lib['earth_face']['terrain'].get('paint') or {}).get('args', {})
        tm = _shape(tiers >= t, h, w, dict(seed=ea.get('seed', 301) + t, r_out=ea.get('r_out', 0.65), r_in=ea.get('r_in', 0.4), amp=ea.get('amp', SG.AMP)))
        top = GD.lawn(h, w, 31 + t, base=3, lush=0.5, grain=0.6)      # the plateau swatch's calmer top
        cv[tm] = top[tm]
        fh = face_h * (t - (levels[i - 1] if i else 0))
        drops.append(fh)
        tops.append(tm)
        below = np.zeros_like(tm)
        for k in range(1, fh + 1):
            below[k:] |= tm[:-k]
        band |= below & ~tm
    # context per cell for the variants: trees, water, doors, routes
    pieces = plan.get('pieces', [])
    tree_c = np.zeros((R, Cc), bool)
    door_c = np.zeros((R, Cc), bool)
    for pc in pieces:
        e = idx.get(pc['piece']) or {}
        cx_, cy_ = int(pc['at'][0] // CELL), int((pc['at'][1] - 1) // CELL)
        if 0 <= cy_ < R and 0 <= cx_ < Cc:
            if 'mask' in (e.get('shadow') or {}):
                tree_c[cy_, cx_] = True
            if e.get('role') in ('door', 'gate', 'house'):
                door_c[cy_, cx_] = True
    for at in (plan.get('spawns') or {}).values():
        cx_, cy_ = int(at[0] // CELL), int(at[1] // CELL)
        if 0 <= cy_ < R and 0 <= cx_ < Cc:
            door_c[cy_, cx_] = True
    water_cells = np.isin(mat, [m for m, p in paint.items() if p.get('fn') == 'water'])
    route_cells = np.isin(mat, [m for m, p in paint.items() if p.get('fn') == 'dirt'])
    near = lambda c, n: ndi.binary_dilation(c, iterations=n) if c.any() else c  # noqa: E731
    ctx_ = {'tree': near(tree_c, 2), 'water': near(water_cells, 2), 'door': near(door_c, 1), 'route': near(route_cells, 1)}
    given = np.array([list(r) for r in plan['variants']]) if plan.get('variants') else None
    # routes and worn ground: packed earth, then (after the ledges) their sunken edges
    routes = []
    for m, p in sorted(paint.items(), key=lambda kv: kv[1].get('order', 0)):
        a = p.get('args', {})
        if p.get('fn') != 'dirt':
            continue
        net = _shape(mat == m, h, w, a.get('shape', {}))
        net &= ~band
        if a.get('foot_pad'):
            pass
        GD.dirt(cv, net, a.get('seed', 43), fam=a.get('fam', 'path'), cell=a.get('cell', 12), stones=a.get('stones', 1.0))
        # width classes and surface variants over the one painted surface
        cls = SF.path_class(SF.widths(mat == m))
        SF.path_widths(cv, net, SF.texels(cls), a.get('seed', 43) + 100, fam=a.get('fam', 'path'))
        var = SF.assign('dirt', mat == m, given, dict(ctx_, cls=cls), a.get('seed', 43) + 200)
        SF.path_variants(cv, net, var, a.get('seed', 43) + 300, fam=a.get('fam', 'path'))
        SF.tone_field(cv, net, a.get('seed', 43) + 400)
        routes.append((net, a))
    for m, p in paint.items():
        if p.get('fn') == 'scree':
            sc = _shape(mat == m, h, w, p.get('args', {}).get('shape', {}))
            SN.scree(cv, [int(sc[:, x * int(D)].sum() / D) for x in range(w // int(D))], ~sc)
    # the ledges, lowest first
    rng = np.random.default_rng(301)
    for t, (tm, fh) in enumerate(zip(tops, drops), start=1):
        _face, items, _lip = GD.ledge(cv, tm, fh, rng, seed=301 + t, kind='earth', shadow_px=15)
        # the back rim, so raised ground reads on every side: the top's last row lit, under it (to the
        # north, seen past the rim) a dark row of earth and a row of the lower turf in its shade
        back = tm & GD.down(~tm, 1)
        cv[back & (cv % 8 < 5)] = cv[back & (cv % 8 < 5)] + 1
        rim1 = ~tm & GD.down(tm, -1) & ~_face
        rim2 = ~tm & GD.down(tm, -2) & ~rim1 & ~_face
        cv[rim1 & (cv >= 0)] = C('earth_cool', 1)
        sel = rim2 & (cv >= 0) & (cv % 8 > 0) & (cv % 8 < 6)
        cv[sel] = cv[sel] - 1
        # the side bands kept their width all the way back (ledge narrows them to 2 px there): along
        # the top's west and east edges a wall 4 px across on the lower turf, the west one lit, the
        # east one in shade, a dark line outside, the top's edge column a lit lip
        turf_l = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & ~tm & ~_face
        for side, lit in ((-1, True), (1, False)):
            for k in range(1, 5):
                wall = turf_l & GD.right(tm, side * k)
                if k == 4:
                    cv[wall] = C('earth_cool', 0)
                else:
                    cv[wall] = C('earth_warm', 4 - k // 2) if lit else C('earth', 2 - k // 2)
            lipc = tm & ~GD.right(tm, -side)
            cv[lipc & (cv % 8 < 5)] = cv[lipc & (cv % 8 < 5)] + 1
        for img_, anc_, (fx_, fy_) in items:
            dec_ = SN.to_codes(img_)
            SN.DC.paste(cv, dec_, int(round(fx_ - anc_[0])), int(round(fy_ - anc_[1])), shadow=True, shadow_dx=SN.P(1), shadow_dy=SN.P(0.5))
    for k, (net, a) in enumerate(routes):
        turf = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & ~net & ~band
        GD.sunken_edge(cv, net, turf, np.random.default_rng(a.get('seed', 43) + 2), stones=a.get('edge_stones', 1.0))
    # the lawn's variants (clover, daisies, long grass, trampled beside routes)
    turf_v = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & ~band
    for net, _a in routes:
        turf_v &= ~ndi.binary_dilation(net, iterations=5)
    lawn_cells = mat == 'lawn'
    lvar = SF.assign('lawn', lawn_cells, given, ctx_, 977 + 200)
    for img_, anc_, (fx_, fy_) in SF.lawn_variants(cv, turf_v, lvar, 977 + 300):
        SN.DC.paste(cv, SN.to_codes(img_), int(round(fx_ - anc_[0])), int(round(fy_ - anc_[1])))
    # pieces painted into the ground: stairs
    for pc in pieces:
        rp = (lib.get(pc['piece'], {}).get('rendering') or {}).get('paint') or {}
        if rp.get('fn') == 'log_steps':
            half = lib[pc['piece']]['geometry']['size_cells'][0] * CELL // 2
            x, y = pc['at']
            GD.log_steps(cv, x - half, x + half, y - face_h - 1, y + 2, rp.get('args', {}).get('n', 4), np.random.default_rng(5))
    # water
    wm = np.zeros((h, w), bool)
    for m, p in paint.items():
        if p.get('fn') != 'water':
            continue
        a = p.get('args', {})
        wcells = mat == m
        wcls = SF.water_class(SF.widths(wcells))
        wm |= SF.taper(_shape(wcells, h, w, a.get('shape', {})), wcells, wcls)
        before = cv.copy()
        items = GD.water(cv, wm, a.get('seed', 402), bank_h=SN.P(a.get('bank_h', 3.4), 0), flow='auto', stones=a.get('stones', 0.0),
                         reeds=a.get('reeds', 0.8), rush_clumps=a.get('rush_clumps'), side_w=a.get('side_w', 5))
        narrow = (wcls >= 1) & (wcls <= 2)
        if narrow.any():
            # a rill's or a stream's banks: the narrow walls of the woodland's rill (side_w 3), not the
            # river's wide ones, which would eat a channel one or two cells across
            nb = before.copy()
            GD.water(nb, wm, a.get('seed', 402), bank_h=SN.P(a.get('bank_h', 3.4), 0), flow='auto', stones=0.0,
                     reeds=a.get('reeds', 0.8), rush_clumps=a.get('rush_clumps'), side_w=a.get('narrow_side_w', 3))
            zone = SF.texels(ndi.binary_dilation(narrow, iterations=1) & ~ndi.binary_dilation(wcls >= 3, iterations=1))[:h, :w]
            cv[zone] = nb[zone]
        nearw = ndi.binary_dilation(wm, iterations=SN.P(3)) & ~wm
        grassy_ = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 <= 2) & nearw
        cv[grassy_] = cv[grassy_] - cv[grassy_] % 8 + 3
        GD.tidy_bank(cv, wm)
        items += SF.water_widths(cv, wm, wcells, wcls, a.get('seed', 402) + 100)
        shore = ndi.binary_dilation(~wcells, iterations=1) & wcells
        wvar = SF.assign('water', wcells, given, dict(ctx_, cls=wcls, shore=shore), a.get('seed', 402) + 200)
        SF.water_variants(cv, wm, wvar, a.get('seed', 402) + 300)
        for (img_, anc_, (fx_, fy_)) in sorted(items, key=lambda it: it[2][1]):
            SN.DC.paste(cv, SN.to_codes(img_), int(round(fx_ - anc_[0])), int(round(fy_ - anc_[1])), shadow=True,
                        shadow_dx=SN.P(1), shadow_dy=SN.P(0.5))
    # crossings: footbridges on abutments in the banks, stepping stones over a rill or a stream
    for pc in pieces:
        rp = (lib.get(pc['piece'], {}).get('rendering') or {}).get('paint') or {}
        if rp.get('fn') not in ('footbridge', 'stepping_stones'):
            continue
        x, y = pc['at']
        ph = int(lib[pc['piece']]['geometry']['size_px'][1])
        local = np.zeros_like(wm)
        local[max(0, y - ph):y, :] = wm[max(0, y - ph):y, :]
        if rp['fn'] == 'footbridge':
            half = int(rp.get('args', {}).get('deck_px', 60)) // 2
            GD.footbridge(cv, x - half, x + half, local, np.random.default_rng(12))
        else:
            from scripts.art.kit import structures as ST
            ST.stones_into(cv, local, x, np.random.default_rng(rp.get('args', {}).get('seed', 41)))
    # falls where water crosses a rim (rules.water_fall places them): the cascade's rock face and fall
    for pc in pieces:
        rp = (lib.get(pc['piece'], {}).get('rendering') or {}).get('paint') or {}
        if rp.get('fn') == 'fall':
            cw = lib[pc['piece']]['geometry']['size_cells'][0] * CELL / D
            cx, foot = pc['at'][0] / D, pc['at'][1] / D
            rim = foot - rp.get('args', {}).get('face_px', face_h) / D
            seed = rp.get('args', {}).get('seed', 11)
            k = cw / 16.0                                   # the woodland's fall is a 16 world px channel
            # the cascade as the woodland painted it (screen.terrain): the rock face behind, then
            # the stepped slabs either side and the lip ledge, the rounded stones at their feet,
            # back to front; the sheet and its foam over them; the face scaled to this face's height
            RK.face(cv, cx - 18 * k, rim, cx + 18 * k, foot + 1, seed=seed + 3)
            q = (foot - rim) / 40.0
            heap = [(0, 6, 28, 10, 205, True), (-28, 10, 22, 13, 203, True), (28, 10, 22, 13, 204, True),
                    (-26, 28, 22, 15, 206, True), (26, 28, 20, 14, 207, True), (-46, 16, 12, 10, 201, False),
                    (-44, 34, 10, 8, 208, False), (-14, 38, 9, 6, 210, False), (15, 38, 8, 5, 211, False)]
            chan = wm.copy()
            chan[int(rim * D):] = False
            chan[:max(0, int((rim - 40) * D))] = False
            for (dx, dy, bw, bh, sd, slab) in sorted(heap, key=lambda b: b[1]):
                sc = 1.0 if q >= 0.75 else min(1.0, 0.55 + 0.45 * q)
                dec, anc = RK.rock(bw * sc * (k if dx == 0 else 1.0), bh * sc, sd, flat=slab, moss=0.6)
                X, Y = int(round((cx + dx * k) * D - anc[0])), int(round((rim + dy * q) * D - anc[1]))
                hh, ww = dec.shape
                sub = chan[max(0, Y):Y + hh, max(0, X):X + ww]
                dec[max(0, -Y):max(0, -Y) + sub.shape[0], max(0, -X):max(0, -X) + sub.shape[1]][sub] = -1
                SN.DC.paste(cv, dec, X, Y, shadow=True, shadow_dx=SN.P(2), shadow_dy=SN.P(1))
            SN.WA.wet_rock(cv, cx - cw / 2, cw, rim - 2, foot)
            # the falling sheet; its foam and rings inside the pool only (2 texels in from its bank)
            tmp = cv.copy()
            RK.fall(tmp, cx - cw / 2, cw, rim, foot + 4, seed=seed)
            ok = ndi.binary_erosion(wm, iterations=2)
            ok[int((rim - 2) * D):int(foot * D), max(0, int((cx - cw / 2 - 2) * D)):int((cx + cw / 2 + 2) * D)] = True
            cv[ok] = tmp[ok]
    # shadows and the lawn's detail (screen.build's order)
    casts, things, trees, objects = [], [], [], []
    for pc in pieces:
        e = idx.get(pc['piece'])
        if not e or ((lib.get(pc['piece'], {}).get('rendering') or {}).get('paint')):
            continue
        img, anc = _sprite(e, pc.get('variant'))
        at = (pc['at'][0], pc['at'][1])
        a = np.asarray(img)[..., 3] > 0
        fx, fy = at[0] / D, at[1] / D
        x0, y0, x1, y1 = CO._bbox(a)
        objects.append((pc['id'], pc['piece'].split('_', 1)[-1], fx - (x1 - x0) / D / 2, fy - (y1 - y0) / D, (x1 - x0) / D, (y1 - y0) / D))
        things.append((fy, img, anc, at))
        sh = e.get('shadow') or {}
        if 'mask' in sh:
            ex, kind = _tree_ex(pc['piece'], img)
            casts.append(SN.tree_shadow_hd(fx, fy, ex, w, h))
            trees.append((fx, fy, ex['w'], kind))
        elif sh:
            casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
    pl = {'objects': objects, 'paths': [], 'places': {'glade': {'at': [-10 ** 4, -10 ** 4], 'r': [1, 1]}}}
    # decals laid into the ground (the editor's decal brush): ferns, foxgloves, mushrooms, leaves
    from scripts.art.native import props as P4
    low = []
    lrng = np.random.default_rng(421)
    for dc in plan.get('decor', []):
        at = (dc['at'][0], dc['at'][1])
        if dc['kind'] in ('fern', 'foxglove'):
            sz = dc.get('size', 0.9)
            img, anc, a = (P4.foxglove_hd(D, seed=dc.get('seed', 1), size=min(1.1, 0.75 + sz * 0.2)) if dc['kind'] == 'foxglove' else
                           P4.fern_hd(D, seed=dc.get('seed', 1), size=min(1.15, 0.55 + sz * 0.3)))
            x0, y0, x1, y1 = CO._bbox(a)
            anc = ((x0 + x1) / 2, y1)
            low.append((at[1] / D, img, anc, at, True))
            casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
        elif dc['kind'] == 'mushrooms':
            img, anc, a = P4.mushrooms_hd(D, n=3 + dc.get('seed', 0) % 3, seed=dc.get('seed', 0), kind=dc.get('tint', 'brown'))
            low.append((at[1] / D, img, anc, at, True))
        elif dc['kind'] == 'leaf':
            limg = CO.fallen_leaf(D, lrng)
            low.append((at[1] / D - 30, limg, (limg.width / 2, limg.height), at, False))
    low += SN.lawn_dressing_hd(cv, pl, h, w)
    shade = np.zeros((h, w), bool)
    for m in casts:
        shade |= m
    SN.ground_detail_hd(cv, pl, trees, h, w, shade, soft=True)
    # in the trees' shade the turf grows long and dark (screen.ground_detail_hd's rule): tufts
    # stand closer there, so a crown's shadow is never a flat rug over the calm lawn
    srng = np.random.default_rng(613)
    turf_s = shade & ndi.binary_erosion(is_fam(cv, 'grass') | is_fam(cv, 'leaf'), iterations=3)
    sy, sx = np.nonzero(turf_s)
    for j in srng.permutation(len(sy))[: len(sy) // 140]:
        GD.stamp(cv, int(sy[j]), int(sx[j]), GD.tuft_shape(srng, srng.uniform(0.8, 1.4)), C('grass_cool', 2), turf_s)
    G = CO.ground_from_codes(cv, D)
    CO.cast_shadows(G, casts, [], things + [(l[0], l[1], l[2], l[3]) for l in low if l[4]], D)
    ground = G.rgba()
    for (_y, im, an, at_, _c) in sorted(low, key=lambda t: t[0]):
        CO.paste(ground, im, an, at_)
    return ground, wm


def baked_pieces(lib: dict | None = None) -> set:
    lib = lib or _pieces_lib()
    return {k for k, p in lib.items() if (p.get('rendering') or {}).get('paint')}


def write(zone: str) -> str:
    plan = json.load(open(os.path.join(ZONES, zone + '.json')))
    lib = _pieces_lib()
    img, _ = bake(plan, lib)
    p = out_path(zone)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.convert('RGB').save(p, optimize=True)
    json.dump({'zone': zone, 'hash': input_hash(plan, lib)}, open(p[:-4] + '.json', 'w'), indent=1)
    return p


def check() -> int:
    lib = _pieces_lib()
    bad = []
    for f in sorted(os.listdir(ZONES)):
        zone = f[:-5]
        plan = json.load(open(os.path.join(ZONES, f)))
        if not plan.get('bake'):
            continue
        meta = out_path(zone)[:-4] + '.json'
        if not os.path.exists(meta) or json.load(open(meta)).get('hash') != input_hash(plan, lib):
            bad.append(zone)
    if bad:
        print('bake: stale baked ground for %s (run python3 -m scripts.art.kit.bake %s)' % (', '.join(bad), ' '.join(bad)))
        return 1
    print('bake: baked grounds current')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('zones', nargs='*')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    for z in a.zones:
        print('bake:', write(z))
    return 0


if __name__ == '__main__':
    sys.exit(main())

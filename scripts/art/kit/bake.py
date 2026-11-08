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
from scripts.art.native import volume as VOL
from scripts.art.native.palette import C, FI, is_fam

D = ctx.D
CELL = 24
ZONES = os.path.join(ROOT, 'game', 'kit', 'zones')
# The shared soil body is a direct baked-material dependency: changing it must invalidate a bake,
# just as a recipe change does. Other native painters retain their existing next-bake behaviour.
SOURCES = ['scripts/art/kit/bake.py', 'scripts/art/kit/surface.py', 'scripts/art/kit/structures.py',
           'scripts/art/native/softground.py', 'scripts/art/native/volume.py']


def _lay(cv, dec, x, y):
    """A stone laid into the ground with its shadow (the water's stones, softground.seat_stone)."""
    SN.DC.paste(cv, dec, x, y, shadow=True, shadow_dx=SN.P(1), shadow_dy=SN.P(0.5))


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


def is_crown_mask(entry: dict) -> bool:
    """True when a prop's shadow mask is a tree's crown: a mask on a piece whose role is tree.

    The one test for every crown consumer (the variants' tree context, the drawing pass, the
    detail bar's crown-shadow region). It names trees rather than excluding the other masked
    roles, so a new masked prop (the mill wheel's silhouette, a house's volume) stays out until
    it is a tree."""
    return (entry or {}).get('role') == 'tree' and 'mask' in ((entry or {}).get('shadow') or {})


def crown_cells(pieces: list, idx: dict, R: int, Cc: int) -> np.ndarray:
    """The cells holding a tree's foot (is_crown_mask), which the variants read as tree context."""
    out = np.zeros((R, Cc), bool)
    for pc in pieces:
        if not is_crown_mask(idx.get(pc['piece'])):
            continue
        cx_, cy_ = int(pc['at'][0] // CELL), int((pc['at'][1] - 1) // CELL)
        if 0 <= cy_ < R and 0 <= cx_ < Cc:
            out[cy_, cx_] = True
    return out


def material_paints(materials, lib: dict) -> dict:
    """Canonical default/tie order, independent of Python's randomized string hashes.

    Descending ids retain the committed woodland's worn-ground-then-path layering. Explicit
    paint.order still takes precedence in the dirt pass. The other passes inherit this stable
    order too; no painter recipe or palette changes.
    """
    return {m: (lib[m]['terrain'].get('paint') or {}) for m in sorted(set(materials), reverse=True) if m in lib}


def bake(plan: dict, lib: dict | None = None):
    """(ground RGBA image, low items drawn) for a kit plan."""
    lib = lib or _pieces_lib()
    idx = json.load(open(os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')))
    rows = plan['rows']
    R, Cc = len(rows), len(rows[0])
    h, w = R * CELL, Cc * CELL
    mat = np.array([[plan['legend'].get(c, '') for c in r] for r in rows])
    tiers = np.array([[int(c) for c in r] for r in plan['tiers']]) if plan.get('tiers') else np.zeros((R, Cc), int)
    paint = material_paints(mat.ravel(), lib)
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
    tree_c = crown_cells(pieces, idx, R, Cc)
    door_c = np.zeros((R, Cc), bool)
    for pc in pieces:
        e = idx.get(pc['piece']) or {}
        cx_, cy_ = int(pc['at'][0] // CELL), int((pc['at'][1] - 1) // CELL)
        if 0 <= cy_ < R and 0 <= cx_ < Cc:
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
    dirt_groups = []
    for m, p in sorted(paint.items(), key=lambda kv: kv[1].get('order', 0)):
        a = p.get('args', {})
        if p.get('fn') != 'dirt':
            continue
        net = _shape(mat == m, h, w, a.get('shape', {}))
        net &= ~band
        if a.get('foot_pad'):
            pass
        cells = mat == m
        if a.get('soft_joints'):
            # A path and its adjoining worn yard share one material, including width/variant
            # treatment. Keep each existing outline, but do not introduce a texture reset or
            # a false material edge merely because their semantic material IDs differ.
            body_keys = ('seed', 'fam', 'cell', 'stones', 'joints', 'lit', 'blades',
                         'soft_joints', 'origin', 'period', 'edge_stones')
            # Numeric controls compare by value (14 and 14.0 are the same recipe), not their
            # JSON spelling. Origins are normalized to tuples for the same phase comparison.
            key = tuple(tuple(a.get(k, (0, 0))) if k == 'origin' else a.get(k) for k in body_keys)
            group = next((g for g in dirt_groups if g[0] == key), None)
            if group is not None:
                group[1] |= cells
                group[2] |= net
                continue
        else:
            key = None
        dirt_groups.append([key, cells, net, a])
    for _key, cells, net, a in dirt_groups:
        packed = a.get('soft_joints', False)
        body_args = {'fam': a.get('fam', 'path'), 'cell': a.get('cell', 12),
                     'stones': a.get('stones', 1.0)}
        if packed:
            # Packed recipes explicitly opt into the Crossroads providers. Legacy recipes
            # keep their original API, so editor tooling does not import unapproved art.
            body_args.update(joints=a.get('joints', 0.28), lit=a.get('lit', 0.4),
                             blades=a.get('blades', 1.0), soft_joints=True,
                             origin=tuple(a.get('origin', (0, 0))), period=a.get('period', 768))
        GD.dirt(cv, net, a.get('seed', 43), **body_args)
        # width classes and surface variants over the one painted surface
        cls = SF.path_class(SF.widths(cells))
        width_args = {'fam': a.get('fam', 'path')}
        if packed:
            width_args['packed'] = True
        SF.path_widths(cv, net, SF.texels(cls), a.get('seed', 43) + 100, **width_args)
        var = SF.assign('dirt', cells, given, dict(ctx_, cls=cls), a.get('seed', 43) + 200)
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
        # Each band is its own distance from the top's edge (a texel at k columns out, not within
        # k: the old loop let the last, darkest row overwrite the whole band, so the side read as a
        # lone black line across the lawn, Claude A 2 Nov). West: the lit side wall, warm earth
        # stepping down to its foot. East: the wall in shade, a dark foot, then the bank's shadow
        # thrown east over the lower turf, so the side reads as a bank with its lip and shadow.
        srng = np.random.default_rng(311 + t)
        jag = ndi.gaussian_filter(srng.random((h, 1)), 3.0)
        jag = np.round((jag - jag.mean()) / max(1e-6, jag.std())).astype(int).clip(-1, 1)
        for side, lit in ((-1, True), (1, False)):
            out_ = np.zeros((h, w), np.int32)
            for k in range(16, 0, -1):
                out_[GD.right(tm, side * k)] = k
            dist = np.where(turf_l, out_, 0) - np.where(out_ > 0, jag, 0)
            if lit:
                tones = {1: C('earth_warm', 4), 2: C('earth_warm', 3), 3: C('earth', 3), 4: C('earth', 2), 5: C('earth_cool', 1)}
            else:
                tones = {1: C('earth', 2), 2: C('earth', 2), 3: C('earth', 1), 4: C('earth_cool', 1), 5: C('earth_cool', 1), 6: C('earth_cool', 0)}
            for k, c in tones.items():
                cv[turf_l & (dist == k)] = c
            if not lit:
                shd = turf_l & (dist > 6) & (dist <= 14) & (cv % 8 > 0) & (cv % 8 < 6)
                cv[shd] = cv[shd] - 1
            # pebbles and roots in the wall
            wy, wx = np.nonzero(turf_l & (dist >= 2) & (dist <= 4))
            for j in srng.permutation(len(wy))[: len(wy) // 40]:
                cv[wy[j], wx[j]] = C('stone', 3) if srng.random() < 0.6 else C('timber_cool', 1)
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
    # water (the ground before it, so a fall's face beside its sheet keeps the cliff's own texture)
    pre_water = cv.copy()
    # each fall's sheet (texels: x0, width, rim row, foot row), known before the water is painted:
    # the channel feeding it runs straight into its lip at exactly its width (SF.fall_run_in)
    falls = []
    for pc in pieces:
        rp = (lib.get(pc['piece'], {}).get('rendering') or {}).get('paint') or {}
        if rp.get('fn') == 'fall':
            cw = lib[pc['piece']]['geometry']['size_cells'][0] * CELL / D
            cx, foot = pc['at'][0] / D, pc['at'][1] / D
            rim = foot - rp.get('args', {}).get('face_px', face_h) / D
            falls.append((int(round((cx - cw / 2) * D)), int(round(cw * D)), int(round(rim * D)), int(round(foot * D)),
                          rp.get('args', {}).get('seed', 11)))
    clear = np.zeros((h, w), bool)
    from scripts.art.native import rocks as RK_
    for (fx0, fw, fr0, fr1, _s) in falls:
        clear |= SF.run_in_zone(h, w, fx0, fw, fr0)
        # and the pool's inlet under the sheet: no bank stone, tongue or reed where it lands
        # (review round 3, K3-1: a seated stone stood as a pillar in the plunge)
        clear[max(0, fr1 - 2):min(h, fr1 + SN.P(10)), max(0, fx0 - RK_.PLUNGE_PAD - 4):min(w, fx0 + fw + RK_.PLUNGE_PAD + 4)] = True
    wm = np.zeros((h, w), bool)
    for m, p in paint.items():
        if p.get('fn') != 'water':
            continue
        a = p.get('args', {})
        wcells = mat == m
        wcls = SF.water_class(SF.widths(wcells))
        wm |= SF.taper(_shape(wcells, h, w, a.get('shape', {})), wcells, wcls)
        for (fx0, fw, fr0, fr1, _s) in falls:
            wm = SF.fall_run_in(wm, fx0, fw, fr0, fr1)
        # (Matt, 4 Nov) one painter for every width: only a north bank shows a face, the other
        # shores one rim (softground.water), so a rill, a stream and a river share their banks
        items = GD.water(cv, wm, a.get('seed', 402), bank_h=SN.P(a.get('bank_h', 3.4), 0), flow='auto', stones=a.get('stones', 0.0),
                         reeds=a.get('reeds', 0.8), rush_clumps=a.get('rush_clumps'), clear=clear)
        # a running channel (north-south, the rill) has no bank stones from the painter (they read
        # as debris, Claude A 2 Nov; surface.water_widths sets at most two); river and pool shores keep theirs
        lab_v = ndi.label(wcells, structure=[[0, 1, 0], [0, 1, 0], [0, 1, 0]])[0]
        lab_h = ndi.label(wcells, structure=[[0, 0, 0], [1, 1, 1], [0, 0, 0]])[0]
        vlen, hlen = np.bincount(lab_v.ravel())[lab_v], np.bincount(lab_h.ravel())[lab_h]
        chan = ndi.binary_dilation(wcells & (vlen > 2 * hlen) & (vlen >= 6), iterations=1)
        kept = []
        for it in sorted(items, key=lambda it: (it[2][1], it[2][0])):
            cy_, cx_ = int(it[2][1] // CELL), int(it[2][0] // CELL)
            if 0 <= cy_ < R and 0 <= cx_ < Cc and chan[cy_, cx_] and not (ndi.binary_dilation(wcells & ~chan, iterations=1)[cy_, cx_]):
                continue
            kept.append(it)
        items = kept
        nearw = ndi.binary_dilation(wm, iterations=SN.P(3)) & ~wm
        grassy_ = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 <= 2) & nearw
        cv[grassy_] = cv[grassy_] - cv[grassy_] % 8 + 3
        GD.tidy_bank(cv, wm)
        # no stream stone at a fall's lip: keep them off the cells over and just above a face
        bandc = band.reshape(R, CELL, Cc, CELL).any(axis=(1, 3))
        items += SF.water_widths(cv, wm, wcells, wcls, a.get('seed', 402) + 100, avoid=bandc)
        if chan.any():
            # the running channel's own one or two stones at its banks
            items += SF.water_widths(cv, wm, wcells, np.where(chan & wcells & (wcls >= 3), 2, 0), a.get('seed', 402) + 150, avoid=bandc)
        shore = ndi.binary_dilation(~wcells, iterations=1) & wcells
        wvar = SF.assign('water', wcells, given, dict(ctx_, cls=wcls, shore=shore), a.get('seed', 402) + 200)
        SF.water_variants(cv, wm, wvar, a.get('seed', 402) + 300)
        # running water: short broken glints along the flow (down a north-south channel, across an
        # east-west one), so a channel three cells wide or more is not a flat depth band
        frng_ = np.random.default_rng(a.get('seed', 402) + 400)
        vrun = np.zeros(wcells.shape, int)
        hrun = np.zeros(wcells.shape, int)
        for lab_, out_, ax_ in ((ndi.label(wcells, structure=[[0, 1, 0], [0, 1, 0], [0, 1, 0]])[0], vrun, 0),
                                (ndi.label(wcells, structure=[[0, 0, 0], [1, 1, 1], [0, 0, 0]])[0], hrun, 1)):
            sizes_ = np.bincount(lab_.ravel())
            out_[:] = np.where(lab_ > 0, sizes_[lab_], 0)
        vert = SF.texels(vrun > hrun)[:h, :w]
        inner_ = ndi.binary_erosion(wm, iterations=SN.P(2)) & SF.texels(wcls >= 3)[:h, :w]
        sy_, sx_ = np.nonzero(inner_ & (frng_.random((h, w)) < 0.004))
        for y_, x_ in zip(sy_, sx_):
            L_ = int(frng_.integers(4, 10))
            if vert[y_, x_]:
                seg = (slice(y_, min(h, y_ + L_)), slice(x_, x_ + 1))
            else:
                seg = (slice(y_, y_ + 1), slice(x_, min(w, x_ + L_)))
            sub_ = cv[seg]
            ok_ = inner_[seg] & (sub_ % 8 < 5)
            sub_[ok_] = sub_[ok_] + 1
        # no stone where a fall runs in or lands (its run-in and its pool's inlet, `clear`): the
        # inlet turns the bank under the sheet to water after these are laid (review round 3, K3-1)
        near_fall = ndi.binary_dilation(clear, iterations=SN.P(3))
        items = [it for it in items if not (0 <= int(it[2][1]) < h and 0 <= int(it[2][0]) < w and near_fall[int(it[2][1]), int(it[2][0])])]
        # stones at the water: each one that stands in it gets its wet contact (softground.seat_stone)
        GD.seat_stones(cv, wm, [(SN.to_codes(img_), int(round(fx_ - anc_[0])), int(round(fy_ - anc_[1])))
                                for (img_, anc_, (fx_, fy_)) in sorted(items, key=lambda it: it[2][1])], _lay)
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
            # Matt, 2 Nov: "the waterfall overlaps in an unrealistic way on the top bit". The fall
            # is the channel going over the rim: a rock face framing the drop a little wider than
            # the channel, from the rim to the pool and nothing above the rim; the sheet
            # (structures.fall_sheet, the piece's own painter) exactly the channel's columns from
            # the rim down, in front of the face; its plume and rings on the pool only. No lip
            # ledge or slabs standing over the banks or the stream above.
            from scripts.art.kit import structures as ST
            from scripts.art.native import props as P4
            r0, r1 = int(round(rim * D)), int(round(foot * D))
            sx0, sw = int(round((cx - cw / 2) * D)), int(round(cw * D))
            frng = np.random.default_rng(seed + 7)
            # the cliff beside the sheet is the cliff: the face as the ledge painted it, where the
            # water's mask ran down the face (no flat slabs, no water beside the sheet)
            span = np.zeros((h, w), bool)
            span[r0:r1, max(0, sx0 - SN.P(14)):sx0 + sw + SN.P(14)] = True
            # the sheet's own outline (structures.sheet_outline: its edges wander a texel in and swell
            # at the foot; review round 4, K4-1), the face showing where it wanders in
            sheet = ST.sheet_mask((h, w), sx0, sw, r0, r1, seed)
            cv[span & ~sheet] = pre_water[span & ~sheet]
            # wet rock near the sheet: darker, a ragged edge (no seam), sheen on the lit stone tops
            # and moss in the joints; spray darkening the foot of the face either side
            Yf, Xf = np.mgrid[0:h, 0:w]
            dx_ = np.where(Xf < sx0, sx0 - Xf, Xf - (sx0 + sw - 1))
            nz = ndi.gaussian_filter(frng.random((h, w)), 2.0)
            nz = (nz - nz.mean()) / max(1e-6, nz.std())
            face_px = span & ~sheet & (cv >= 0)
            wet = face_px & (dx_ < SN.P(7) + 4 * nz)
            spray = face_px & (Yf > r1 - SN.P(9) + 3 * nz) & (dx_ < SN.P(13) + 4 * nz)
            for m_ in (wet, spray, wet & (dx_ < SN.P(3) + 2 * nz)):
                sel = m_ & (cv % 8 > 0) & (cv % 8 < 6)
                cv[sel] = cv[sel] - 1
            # (no sheen of water-blue and white glints on the stone beside the sheet: they read as spray
            # on the face, against Matt's 2 Nov ruling; review round 7. The wet stone is its darker
            # tones and the moss.) The random field keeps its draw so the moss below is unchanged.
            frng.random((h, w))
            moss = (wet | spray) & (pre_water % 8 <= 1) & (nz > 0.6) & (frng.random((h, w)) < 0.5)
            cv[moss] = np.where(frng.random(moss.sum()) < 0.5, C('leaf', 2), C('leaf_cool', 2))
            # the sheet and its plume, rings and ripples on the pool
            above = np.zeros_like(wm)
            above[:r0] = True
            # the pool runs up to the sheet's foot (review round 3, K3-1): from the sheet's foot row,
            # under the sheet and the foam's reach, the pool's own north bank (its grass lip, rim and
            # earth face) gives way to water in its shade down to the open pool, the inlet's top
            # corners rounded 2 to 3 texels and the 5.3a rim (wet earth, the mid tone) down both
            # sides, so the white water lands on the pool and on nothing else
            from scripts.art.native import rocks as RK_
            waters_ = [GD.FI[n_] for n_ in ('water', 'water_warm', 'water_cool') if n_ in GD.FI]
            ix0, ix1 = max(0, sx0 - RK_.PLUNGE_PAD), min(w, sx0 + sw + RK_.PLUNGE_PAD)
            inlet = np.zeros((h, w), bool)
            for X in range(ix0, ix1):
                seg = np.isin(cv[r1:min(h, r1 + SN.P(10)), X] // 8, waters_) & wm[r1:min(h, r1 + SN.P(10)), X]
                if not seg.any():
                    continue
                # down to where the pool's own water runs on (four rows of it), so a sliver of bank
                # under a texel of water is not left standing as a pillar in the inlet
                run4 = np.array([seg[i_:i_ + 4].all() for i_ in range(len(seg))])
                stop = r1 + (int(np.argmax(run4)) if run4.any() else int(np.argmax(seg)))
                d_edge = min(X - ix0, ix1 - 1 - X)
                start = r1 + max(0, 3 - d_edge) if d_edge < 3 else r1      # rounded top corners
                inlet[start:stop, X] = True
            cv[inlet] = C('water', 1)
            # beside the sheet the face's foot meets the inlet as a north bank does: the light
            # waterline under it (5.3), the face's foot pebbles standing in it
            top_ = inlet & ~GD.down(inlet, 1)
            top_[:, sx0:sx0 + sw] = False
            cv[top_] = C('water', 5)
            wm = wm | inlet
            iys = np.nonzero(inlet.any(1))[0]
            for Y in iys:
                xs_ = np.nonzero(inlet[Y])[0]
                if len(xs_) < 4:
                    continue
                # its sides take the rim only where land lies beyond them (where the pool's own water
                # already runs on beside the inlet, a rim would stand as a pillar of earth in it)
                for (xe, xi, xo) in ((xs_[0], xs_[0] + 1, xs_[0] - 1), (xs_[-1], xs_[-1] - 1, xs_[-1] + 1)):
                    if 0 <= xo < w and cv[Y, xo] >= 0 and cv[Y, xo] // 8 in waters_:
                        continue
                    cv[Y, xe] = GD.rim_earth()
                    cv[Y, xi] = C('water', GD.RIM_LINE)
            # the inlet is part of the pool (review round 4, K4-4: the pool's north waterline and its
            # dark band ran on straight across the inlet's mouth, a sill under a basin a step up):
            # inside the inlet's sides they give way to the inlet's deep water, which runs on into
            # the pool's body; the waterline and the band end at the inlet's sides
            for X in range(ix0 + 1, ix1 - 1):
                col_ = np.nonzero(inlet[:, X])[0]
                if not len(col_):
                    continue
                Y = int(col_.max()) + 1
                for _k in range(6):
                    if not (Y < h and wm[Y, X] and cv[Y, X] >= 0 and cv[Y, X] // 8 in waters_ and cv[Y, X] % 8 in (0, 3, 4, 5)):
                        break
                    cv[Y, X] = C('water', 1)
                    Y += 1
            tmp = cv.copy()
            ST.fall_sheet(tmp, sx0, sw, r0, r1, seed=seed)
            ok = ndi.binary_erosion(wm, iterations=2) & ~above & ~span
            ok |= sheet
            # the channel's last rows fading into the glassy tongue above the rim, and the lit
            # streaks converging on the lip (rocks.sheet draws them on the channel's water; 5.3b)
            ok[max(0, r0 - 24):r0, sx0:sx0 + sw] |= wm[max(0, r0 - 24):r0, sx0:sx0 + sw]
            ok[r1:r1 + SN.P(14)] |= ndi.binary_erosion(wm, iterations=2)[r1:r1 + SN.P(14)]
            cv[ok] = tmp[ok]
            # lip stones on the rim beside the sheet, never over it: they sit on the top tier's
            # edge, each lit on its upper left with its shadow
            for side_, k_, w_ in ((-1, 0, 6.5), (1, 0, 5.5), (-1, 1, 3.8), (1, 1, 3.4)):
                img_, anc_, _a = P4.boulder4(D, w_, w_ * 0.62, seed=seed * 31 + k_ * 7 + side_, moss='top' if k_ == 0 else None)
                gap = SN.P(1) + int(img_.width / 2) + (SN.P(w_ + 1) if k_ else 0)
                fx_ = sx0 - gap if side_ < 0 else sx0 + sw + gap
                fy_ = r0 + SN.P(0.5) - (SN.P(2) if k_ else 0)
                SN.DC.paste(cv, SN.to_codes(img_), int(round(fx_ - anc_[0])), int(round(fy_ - anc_[1])), shadow=True,
                            shadow_dx=SN.P(1), shadow_dy=SN.P(0.5))
    # shadows and the lawn's detail (screen.build's order)
    casts, things, trees, objects = [], [], [], []
    vol = np.zeros((h, w), np.uint8)        # the houses' volume shadows, their steps 1/2/3
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
        if VOL.bake_cast(vol, e, at, w, h):
            continue
        if is_crown_mask(e):
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
    shade = vol > 0
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
    before = G.tone.copy()
    CO.cast_shadows(G, casts, [], things + [(l[0], l[1], l[2], l[3]) for l in low if l[4]], D)
    # a house's shadow keeps its authored bands (town.py, kit compose.shadows, terrain_ground.gd)
    VOL.lay_levels(G, before, vol)
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
    meta = p[:-4] + '.json'
    # A failed in-place write must never retain an earlier success marker.
    try:
        os.unlink(meta)
    except FileNotFoundError:
        pass
    try:
        img.convert('RGB').save(p, optimize=True)
        with Image.open(p) as output:
            if output.format != 'PNG':
                raise ValueError('Baked ground is not a PNG')
            output.verify()
        with open(meta, 'w') as marker:
            json.dump({'zone': zone, 'hash': input_hash(plan, lib)}, marker, indent=1)
    except BaseException:
        # A failed marker write/close is incomplete publication too.
        try:
            os.unlink(meta)
        except FileNotFoundError:
            pass
        raise
    return p


def check() -> int:
    lib = _pieces_lib()
    bad = []
    for f in sorted(os.listdir(ZONES)):
        zone = f[:-5]
        plan = json.load(open(os.path.join(ZONES, f)))
        if not plan.get('bake'):
            continue
        p = out_path(zone)
        meta = p[:-4] + '.json'
        try:
            with open(meta) as marker:
                if json.load(marker).get('hash') != input_hash(plan, lib):
                    bad.append(zone)
                    continue
            with Image.open(p) as output:
                if output.format != 'PNG':
                    bad.append(zone)
                    continue
                output.verify()
        except (OSError, ValueError, SyntaxError):
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

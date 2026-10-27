"""The scene gate's data half: a Godot zone read from its .tscn (and the base scene it
instances), its pictures, walk mask, kit.json and plan, composed into one picture of the
whole zone, and the logic checks that need to know what each thing is.

  occlusion     a sprite's sort point (its origin, which y-sort compares with the player's
                feet) is not at its drawn feet, so it draws over or under people wrongly
  intersect     two solid things share ground: their footprints overlap (a log run into a trunk)
  crown_cut     a tree stands inside the zone with most of its crown outside it (a bare trunk
                at the edge of the screen)
  reach         a bench, well, door, board or workplace with no walkable stand in front of it,
                or a bench whose front is lawn with no path or worn ground to it
  shadow        a cast shadow painted on the ground with no sprite standing at its head
  rows          the same drawing placed three or more times on one line at even spacing
  wiring        doors to zones or spawns that do not exist, quest events nobody can send,
                speakers with no dialogue, restore sites the plan does not know
"""
from __future__ import annotations

import glob
import json
import os
import re
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from .core import REPO, GAME_H, Finding, regions, slice_box, hsv, keys, lum
from . import construct as C
from . import detail as D

GAME = os.path.join(REPO, 'game')
SOLID = {'broadleaf', 'veteran_tree', 'conifer', 'birch', 'willow', 'log', 'standing_stone', 'boulder', 'stump',
         'bench', 'barrel', 'well', 'trough', 'small_machine', 'crate_stack', 'stall', 'handcart', 'smithy',
         'cottage', 'hut', 'woodpile', 'haystack', 'lamp', 'lantern_post', 'tall_sign', 'sapling', 'young_tree'}
TREES = {'broadleaf', 'veteran_tree', 'conifer', 'birch', 'willow', 'young_tree'}
NEEDS_FRONT = {'bench': 'path', 'well': 'stand', 'trough': 'stand', 'small_machine': 'stand', 'tall_sign': 'stand',
               'stall': 'stand', 'lantern_post': None}


# ------------------------------------------------------------------------------------------
# .tscn parsing (the subset the generators write)
_SEC = re.compile(r'^\[(\w+)(.*)\]\s*$')
_ATTR = re.compile(r'(\w+)=("[^"]*"|\S+)')


def _val(v: str):
    v = v.strip()
    m = re.match(r'Vector2\(([-\d.e]+),\s*([-\d.e]+)\)', v)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.match(r'(ExtResource|SubResource)\("([^"]+)"\)', v)
    if m:
        return (m.group(1), m.group(2))
    if v in ('true', 'false'):
        return v == 'true'
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    try:
        return float(v) if '.' in v or 'e' in v else int(v)
    except ValueError:
        return v


def parse_tscn(path: str) -> dict:
    ext, sub, nodes = {}, {}, []
    cur = None
    for line in open(path):
        line = line.rstrip('\n')
        m = _SEC.match(line)
        if m:
            kind, rest = m.group(1), m.group(2)
            attrs = {k: _val(v) for k, v in _ATTR.findall(rest)}
            if kind == 'ext_resource':
                ext[str(attrs.get('id'))] = attrs
                cur = None
            elif kind == 'sub_resource':
                cur = dict(attrs)
                sub[str(attrs.get('id'))] = cur
            elif kind == 'node':
                cur = dict(attrs)
                cur['props'] = {}
                nodes.append(cur)
            else:
                cur = None
            continue
        if cur is not None and '=' in line and not line.startswith(' '):
            k, v = line.split('=', 1)
            if 'props' in cur:
                cur['props'][k.strip()] = _val(v)
            else:
                cur[k.strip()] = _val(v)
    return dict(ext=ext, sub=sub, nodes=nodes)


def res_path(p: str) -> str:
    return os.path.join(GAME, p.replace('res://', ''))


@dataclass
class Sprite:
    name: str
    path: str
    origin: tuple            # global position (the y-sort point) in zone texels
    box: tuple               # drawn box (x0, y0, x1, y1)
    z: int
    ysort: bool
    rgba: np.ndarray
    parent: str
    kind: str = ''
    visible: bool = True


@dataclass
class Zone:
    id: str
    size: tuple
    ground: np.ndarray | None
    sprites: list = field(default_factory=list)
    doors: list = field(default_factory=list)
    spawns: dict = field(default_factory=dict)
    talkers: list = field(default_factory=list)
    camps: list = field(default_factory=list)
    restores: list = field(default_factory=list)
    walk: np.ndarray | None = None
    walk_cell: int = 12
    plan: dict | None = None


def _walk_nodes(tscn: dict, prefix: str, offset=(0.0, 0.0), ysort_parent=False, hidden=False, out=None):
    """Global positions for every node, following instanced scenes."""
    out = [] if out is None else out
    pos = {'.': offset}
    ys = {'.': ysort_parent}
    vis = {'.': not hidden}
    cond = {'.': []}
    for n in tscn['nodes']:
        parent = n.get('parent')
        name = n['name']
        key = '.' if parent is None else (name if parent == '.' else f'{parent}/{name}')
        pkey = '.' if parent in (None, '.') else parent
        p0 = pos.get(pkey, offset)
        lp = n['props'].get('position', (0.0, 0.0))
        g = (p0[0] + lp[0], p0[1] + lp[1]) if parent is not None else offset
        pos[key] = g
        ys[key] = bool(n['props'].get('y_sort_enabled', False))
        vis[key] = vis.get(pkey, True) and n['props'].get('visible', True) is not False
        cond[key] = list(cond.get(pkey, []))
        oi = n['props'].get('only_if')
        if isinstance(oi, str):
            try:                                       # a JSON object written as a Godot string ("{\"k\":...}")
                v_ = json.loads(oi.replace('\\"', '"'))
                cond[key].append(json.loads(v_) if isinstance(v_, str) else v_)
            except ValueError:
                pass
        full = prefix + ('' if key == '.' else key)
        inst = n.get('instance')
        if inst and inst[0] == 'ExtResource':
            sub = parse_tscn(res_path(tscn['ext'][inst[1]]['path']))
            _walk_nodes(sub, full + '/', g, ys.get(pkey, False), not vis[key], out)
        out.append(dict(node=n, key=full, pos=g, parent_ysort=ys.get(pkey, False), visible=vis[key], ext=tscn['ext'],
                        conds=cond[key]))
    return out


def load_zone(zone_id: str, stage: str | None = None) -> Zone:
    """The zone as placed. With `stage` (a stage id from the plan), only what that stage shows:
    every node under a Conditional (world/conditional.gd, its `only_if`) whose condition does not
    hold in the stage's state is hidden, as the game hides it."""
    zones = json.load(open(os.path.join(GAME, 'data', 'zones.json')))
    path = res_path(zones[zone_id])
    tscn = parse_tscn(path)
    nodes = _walk_nodes(tscn, '')
    state = None
    pp_ = os.path.join(GAME, 'data', 'plans', zone_id + '.json')
    if stage and os.path.exists(pp_):
        from scripts.art.native import town as TW
        state = TW.stage_states(json.load(open(pp_))).get(stage)
        if state is not None:
            for e in nodes:
                if not all(TW.holds(c, state) for c in e.get('conds', [])):
                    e['visible'] = False
    z = Zone(zone_id, (0, 0), None)
    for e in nodes:
        n, props = e['node'], e['node']['props']
        t = n.get('type')
        if t == 'Sprite2D' and 'texture' in props:
            tex = props['texture']
            if tex[0] != 'ExtResource':
                continue
            p = res_path(e['ext'][tex[1]]['path'])
            if not os.path.exists(p):
                continue
            rgba = np.asarray(Image.open(p).convert('RGBA'))
            hf = int(props.get('hframes', 1) or 1)
            if hf > 1:                                     # an animation strip shows one frame at a time
                rgba = rgba[:, :rgba.shape[1] // hf]
            off = props.get('offset', (0.0, 0.0))
            centered = props.get('centered', True)
            x0 = e['pos'][0] + off[0] - (rgba.shape[1] / 2 if centered else 0)
            y0 = e['pos'][1] + off[1] - (rgba.shape[0] / 2 if centered else 0)
            sp = Sprite(n['name'], os.path.relpath(p, REPO), e['pos'], (x0, y0, x0 + rgba.shape[1], y0 + rgba.shape[0]),
                        int(props.get('z_index', 0)), e['parent_ysort'], rgba, e['key'],
                        C.kind_of(os.path.splitext(os.path.basename(p))[0]), e['visible'])
            if n['name'] == 'Ground' or (sp.z < 0 and rgba.shape[0] > 500):
                if z.ground is None or rgba.shape[0] * rgba.shape[1] > z.ground.shape[0] * z.ground.shape[1]:
                    z.ground = rgba
                    z.size = (rgba.shape[1], rgba.shape[0])
                continue
            z.sprites.append(sp)
        elif t == 'Marker2D' and '/Spawns/' in '/' + e['key'] + '/' or (t == 'Marker2D' and e['key'].startswith('Spawns')):
            z.spawns[n['name']] = e['pos']
        if 'target_zone' in props:
            z.doors.append(dict(name=n['name'], zone=props['target_zone'], spawn=props.get('target_spawn', 'start'),
                                pos=e['pos'], key=e['key']))
        if 'speaker_id' in props:
            z.talkers.append(dict(speaker=props['speaker_id'], pos=e['pos'], key=e['key']))
        if 'camp_id' in props:
            z.camps.append(props['camp_id'])
        for k in ('restore_id', 'site_id'):
            if k in props:
                z.restores.append(props[k])
    wt = os.path.join(GAME, 'zones', zone_id, 'walk.txt')
    if os.path.exists(wt):
        rows = [l.rstrip('\n') for l in open(wt) if l.strip()]
        z.walk = np.array([[c != '#' for c in r] for r in rows], bool)
        if z.size[0]:
            z.walk_cell = int(round(z.size[0] / z.walk.shape[1]))
    pp = os.path.join(GAME, 'data', 'plans', zone_id + '.json')
    if os.path.exists(pp):
        z.plan = json.load(open(pp))
    return z


def composite(z: Zone, actors: bool = False) -> np.ndarray:
    """The whole zone in one picture: ground, then sprites by z and y-sort (origin y)."""
    W, H = z.size
    out = np.zeros((H, W, 3), float)
    if z.ground is not None:
        out[:] = z.ground[..., :3]
    order = sorted([s for s in z.sprites if s.visible and (actors or not s.parent.startswith('Actors'))],
                   key=lambda s: (s.z, s.origin[1] if s.ysort else -1e9, s.origin[0]))
    for s in order:
        x0, y0 = int(round(s.box[0])), int(round(s.box[1]))
        h, w = s.rgba.shape[:2]
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
        if dx1 <= dx0 or dy1 <= dy0:
            continue
        src = s.rgba[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0].astype(float)
        a = src[..., 3:4] / 255.0
        out[dy0:dy1, dx0:dx1] = out[dy0:dy1, dx0:dx1] * (1 - a) + src[..., :3] * a
    return np.dstack([out.astype(np.uint8), np.full((H, W), 255, np.uint8)])


def sprite_mask(s: Sprite, size):
    W, H = size
    m = np.zeros((H, W), bool)
    x0, y0 = int(round(s.box[0])), int(round(s.box[1]))
    a = s.rgba[..., 3] > 128
    h, w = a.shape
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
    if dx1 > dx0 and dy1 > dy0:
        m[dy0:dy1, dx0:dx1] = a[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    return m


# ------------------------------------------------------------------------------------------
def check_occlusion(z: Zone, H=GAME_H) -> list[Finding]:
    fs = []
    for s in z.sprites:
        if not s.ysort or s.parent.startswith('Actors') or 'damage' in s.path or 'fx' in s.path:
            continue
        a = s.rgba[..., 3] > 128
        if not a.any():
            continue
        ys = np.nonzero(a.any(1))[0]
        bottom = s.box[1] + ys.max() + 1
        gap = s.origin[1] - bottom
        if abs(gap) > 0.25 * H:
            fs.append(Finding('logic.occlusion', 'fault', tuple(int(v) for v in s.box),
                              f'{s.name} ({s.kind}): its y-sort point is {gap:+.0f} px from its drawn feet, so people '
                              f'{"behind it draw over it" if gap < 0 else "in front of it draw under it"}',
                              'put the node origin on the foot line (the bottom of the footprint, where it meets the '
                              'ground), or split overhanging parts into their own sorted sprite',
                              score=float(gap), threshold=0.25 * H, subject=s.name))
    return fs


def footprint(s: Sprite, size, H=GAME_H):
    """The ground a solid thing stands on: the lowest 0.12 H of its drawn pixels, column by
    column (a trunk's base, a log's underside, a bench's feet)."""
    m = sprite_mask(s, size)
    if not m.any():
        return m
    out = np.zeros_like(m)
    cols = np.nonzero(m.any(0))[0]
    band = max(3, int(0.12 * H))
    bottoms = {}
    for x in cols:
        ys = np.nonzero(m[:, x])[0]
        bottoms[x] = ys.max()
    gb = max(bottoms.values())
    for x, b in bottoms.items():
        if gb - b <= band:            # columns that reach the ground line (not the crown's overhang)
            out[max(0, b - band + 1):b + 1, x] = m[max(0, b - band + 1):b + 1, x]
    return out


def check_intersect(z: Zone, H=GAME_H) -> list[Finding]:
    fs = []
    sol = [s for s in z.sprites if s.kind in SOLID and s.visible and not s.parent.startswith('Actors')]
    fps = {id(s): footprint(s, z.size, H) for s in sol}
    for i, a in enumerate(sol):
        for b in sol[i + 1:]:
            if a.box[2] < b.box[0] or b.box[2] < a.box[0] or a.box[3] < b.box[1] or b.box[3] < a.box[1]:
                continue
            if _alternates(a, b):
                continue
            ov = fps[id(a)] & fps[id(b)]
            n = int(ov.sum())
            if n >= 0.006 * H * H:
                ys, xs = np.nonzero(ov)
                box = (int(min(a.box[0], b.box[0])), int(min(a.box[1], b.box[1])),
                       int(max(a.box[2], b.box[2])), int(max(a.box[3], b.box[3])))
                box = (int(xs.min()) - 20, int(ys.min()) - 40, int(xs.max()) + 20, int(ys.max()) + 10)
                fs.append(Finding('logic.intersect', 'fault', box,
                                  f'{a.name} ({a.kind}) and {b.name} ({b.kind}) stand in the same ground: their footprints '
                                  f'overlap by {n} px, so one is drawn through the other',
                                  'move one clear of the other (a log lies beside a trunk or ends against its root flare, '
                                  'never through it), or draw them as one piece that meets on purpose',
                                  score=float(n), threshold=0.006 * H * H, subject=f'{a.name} x {b.name}'))
    return fs


def _alternates(a: Sprite, b: Sprite) -> bool:
    """Two states of one thing (broken and restored, lit and dark, a damage overlay): never
    shown together, or meant to overlap."""
    if 'damage' in a.path or 'damage' in b.path or 'rubble' in a.path or 'rubble' in b.path:
        return True
    pa = [p for p in a.parent.split('/') if p.startswith('If_')]
    pb = [p for p in b.parent.split('/') if p.startswith('If_')]
    if (pa or pb) and pa != pb:
        return True
    return a.kind == b.kind and abs(a.origin[0] - b.origin[0]) < 4 and abs(a.origin[1] - b.origin[1]) < 4


def check_crowns(z: Zone, H=GAME_H) -> list[Finding]:
    fs = []
    W, Hh = z.size
    for s in z.sprites:
        if s.kind not in TREES or not s.visible:
            continue
        a = s.rgba[..., 3] > 128
        fam = D.family_map(s.rgba[..., :3])
        crown = a & (fam == 1)
        if crown.sum() < 0.2 * H * H:
            continue
        ys, xs = np.nonzero(crown)
        gx, gy = xs + s.box[0], ys + s.box[1]
        inside = ((gx >= 0) & (gx < W) & (gy >= 0) & (gy < Hh)).mean()
        foot_in = 0 <= s.origin[0] < W and 0 <= s.origin[1] < Hh
        if foot_in and inside < 0.7:
            fs.append(Finding('logic.crown_cut', 'fault', (max(0, int(s.box[0])), max(0, int(s.box[1])),
                                                           min(W, int(s.box[2])), min(Hh, int(s.box[3]))),
                              f'{s.name} ({s.kind}): the trunk stands in the zone but {1 - inside:.0%} of its crown is '
                              'outside it, so the screen edge shows a bare trunk',
                              'move the tree in until its crown is on screen, or move it out so the edge shows only '
                              'crown (a forest edge two or three trees deep, art-faults rule 13)',
                              score=float(inside), threshold=0.7, subject=s.name))
    return fs


def path_mask(img: np.ndarray, H=GAME_H) -> np.ndarray:
    """Paths, worn ground and paving in a ground picture: dirt and stone families in large
    connected fields."""
    fam = D.family_map(img[..., :3])
    m = np.isin(fam, (3, 5, 6, 7))
    h, s, v = hsv(img[..., :3])
    m &= ~((fam == 7) & (s > 0.5))          # not yellow grass tips
    m = ndi.binary_closing(m, structure=np.ones((3, 3)), iterations=2)
    lab, regs = regions(m, min_area=int(0.5 * H * H))
    out = np.zeros_like(m)
    for lid, sl, a in regs:
        out[sl] |= lab[sl] == lid
    return out


def check_reach(z: Zone, H=GAME_H) -> list[Finding]:
    fs = []
    if z.ground is None:
        return fs
    paths = path_mask(z.ground, H)
    reach = None
    if z.walk is not None and z.spawns:
        start = z.spawns.get('start') or next(iter(z.spawns.values()))
        c = z.walk_cell
        lab, n = ndi.label(z.walk)
        sy, sx = int(start[1] // c), int(start[0] // c)
        if 0 <= sy < lab.shape[0] and 0 <= sx < lab.shape[1] and lab[sy, sx]:
            reach = lab == lab[sy, sx]
    for s in z.sprites:
        need = NEEDS_FRONT.get(s.kind, 'skip')
        if need == 'skip' or need is None or not s.visible or s.parent.startswith('Actors'):
            continue
        a = s.rgba[..., 3] > 128
        if not a.any():
            continue
        ys, xs = np.nonzero(a)
        fx0, fx1 = int(s.box[0] + xs.min()), int(s.box[0] + xs.max() + 1)
        fy = int(s.box[1] + ys.max() + 1)
        depth = int(0.3 * H)
        apron = (max(0, fx0), min(z.size[1], fy + 2), min(z.size[0], fx1), min(z.size[1], fy + 2 + depth))
        if apron[3] <= apron[1] or apron[2] <= apron[0]:
            continue
        if reach is not None:
            c = z.walk_cell
            cells = reach[apron[1] // c:(apron[3] - 1) // c + 1, apron[0] // c:(apron[2] - 1) // c + 1]
            if cells.size and not cells.any():
                fs.append(Finding('logic.reach', 'blocker', apron,
                                  f'{s.name} ({s.kind}): no walkable stand in front of it that the player can reach from '
                                  'the zone start', 'open its apron in the walk mask and connect it to the paths '
                                  '(world-rules.md 6.6)', score=0.0, threshold=1.0, subject=s.name))
                continue
        if need == 'path':
            share = paths[apron[1]:apron[3], apron[0]:apron[2]].mean()
            if share < 0.3:
                fs.append(Finding('logic.reach', 'fault', apron,
                                  f'{s.name} ({s.kind}): its front is open lawn ({share:.0%} path or worn ground): no path '
                                  'leads to it and nobody has worn the grass where people sit',
                                  'lead a worn branch from the nearest path to the bench front, with a small apron of bare '
                                  'ground under the seat (the pilot golden does this), or face it onto the path',
                                  score=float(share), threshold=0.3, subject=s.name))
    return fs


def check_shadows(z: Zone, H=GAME_H) -> list[Finding]:
    """Painted cast shadows on the ground picture (which holds no sprites) must start at the
    foot of a sprite: a lawn-hued blob two ramp steps down with no sprite foot at its head
    (its north-west half) is a shadow without a caster."""
    if z.ground is None:
        return []
    g = z.ground[..., :3]
    k = keys(g, 32)
    vals, cnt = np.unique(k, return_counts=True)
    top = vals[np.argmax(cnt)]
    h, s, v = hsv(g)
    lm = k == top
    lh, lv = float(np.median(h[lm])), float(np.median(v[lm]))
    dh = np.abs(((h - lh) + 180) % 360 - 180)
    ratio = v / max(lv, 1e-3)
    cand = (ratio >= 0.45) & (ratio <= 0.8) & (dh <= 40) & (s >= 0.15)
    cand = ndi.binary_closing(cand, structure=np.ones((3, 3)), iterations=2)
    # a wall's own top (a vault's cut-away dark, a coping in shade) is not a shadow on the ground
    if z.plan and z.plan.get('walls') and z.plan.get('box'):
        d = z.size[0] / float(z.plan['box'][2])
        for w in z.plan['walls']:
            x, y, ww, hh = (int(round(v * d)) for v in w['rect'])
            cand[max(0, y):y + hh, max(0, x):x + ww] = False
    # what the player sees of it: not hidden under a sprite
    cover = np.zeros(cand.shape, bool)
    feet = np.zeros(cand.shape, bool)
    for sp in z.sprites:
        if not sp.visible:
            continue
        cover |= sprite_mask(sp, z.size)
        feet |= footprint(sp, z.size, H)
    vis = cand & ~cover
    rr = max(2, int(0.1 * H))
    disk = np.hypot(*np.mgrid[-rr:rr + 1, -rr:rr + 1]) <= rr
    vis = ndi.binary_opening(vis, structure=disk)
    dist = ndi.distance_transform_edt(~feet)
    lab, regs = regions(vis, min_area=int(0.35 * H * H))
    fs = []
    for lid, sl, area in regs:
        comp = lab == lid
        x0, y0, x1, y1 = slice_box(sl)
        bw, bh = x1 - x0, y1 - y0
        if area / max(1, bw * bh) < 0.4 or bw > 4 * H:
            continue          # forest-floor shade bands, not a cast shadow
        far = float((dist[comp] > 0.6 * H).mean())
        if far > 0.5:
            fs.append(Finding('logic.shadow_orphan', 'fault', (x0, y0, x1, y1),
                              f'a cast shadow {bw} x {bh} px lies in the open with nothing over it: {far:.0%} of it is '
                              f'more than 0.6 H from any foot, so it reads as a blob with no caster',
                              'a cast shadow joins the foot of what casts it and sits under it (a crown\'s shadow under '
                              'the crown, round the trunk base), thrown only a little east and down; move it under its '
                              'tree, shrink it to the caster, or remove it (eastward-edges.md 7)',
                              score=far, threshold=0.5, subject='shadow'))
    return fs


LIGHT_SOURCES = ('torch', 'brazier', 'lamp', 'lantern', 'candle', 'fire', 'hearth', 'forge', 'window', 'skylight')
POOL_RISE = 35.0          # L units: a pool stands this far over the ground's median (blurred at 0.2 H)
POOL_MIN = 0.25           # H^2
POOL_REACH = 1.4          # H: the pool's brightest point lies this near a source


def light_sources(z: Zone) -> list[tuple]:
    """Where light comes from: every visible sprite named as a light (torch, brazier, lamp, window,
    ...) at its foot, and the plan's skylight and stair hatch (zone texels)."""
    pts = []
    for sp in z.sprites:
        if sp.visible and any(k in (sp.name + ' ' + sp.path).lower() for k in LIGHT_SOURCES):
            pts.append((float(sp.origin[0]), float(sp.origin[1])))
    if z.plan and z.plan.get('box'):
        d = z.size[0] / float(z.plan['box'][2])
        sk = z.plan.get('skylight')
        if sk:
            pts.append((sk['at'][0] * d, sk['at'][1] * d))
        st = z.plan.get('stair')
        if st:
            x, y, w, h = st['rect']
            pts.append(((x + w) * d, (y + h / 2) * d))
    return pts


def check_light_sources(z: Zone, H=GAME_H) -> list[Finding]:
    """A pool of light painted on a dark ground (an interior, a night street) needs its source: a
    torch, brazier, lamp or window over it, or the opening it falls through. A bright patch at least
    POOL_RISE over the ground's median and POOL_MIN large, with no source within POOL_REACH of its
    brightest point, is a light from nowhere (Claude A's review of the Undercroft, 26 Oct)."""
    if z.ground is None:
        return []
    L = lum(z.ground[..., :3])
    floor = np.ones(L.shape, bool)
    if z.plan and z.plan.get('walls') and z.plan.get('box'):
        d = z.size[0] / float(z.plan['box'][2])
        for w in z.plan['walls']:
            x, y, ww, hh = (int(round(v * d)) for v in w['rect'])
            floor[max(0, y):y + hh, max(0, x):x + ww] = False
    if np.median(L[floor]) >= 90:
        return []                      # a daylit ground: its light is the sun's
    bl = ndi.gaussian_filter(L, 0.2 * H)
    pool = floor & (bl >= np.median(bl[floor]) + POOL_RISE)
    lab, regs = regions(pool, min_area=int(POOL_MIN * H * H))
    src = light_sources(z)
    fs = []
    for lid, sl, area in regs:
        comp = lab == lid
        yy, xx = np.nonzero(comp)
        k = int(np.argmax(bl[comp]))
        px, py = float(xx[k]), float(yy[k])
        near = min((np.hypot(px - sx, py - sy) for sx, sy in src), default=1e9)
        if near > POOL_REACH * H:
            fs.append(Finding('logic.light_source', 'fault', slice_box(sl),
                              f'a pool of light {area / (H * H):.1f} H^2 with no source: the nearest torch, lamp or '
                              f'opening is {near / H:.1f} H from its brightest point',
                              'hang a torch or brazier on the wall over the pool (or make it the skylight\'s pool with '
                              'its beam), or take the pool away; light never comes from nowhere (art-style.md)',
                              score=near / H, threshold=POOL_REACH, subject='light'))
    return fs


def check_rows(z: Zone, H=GAME_H) -> list[Finding]:
    """The same drawing three or more times on one line at even spacing."""
    fs = []
    by = {}
    for s in z.sprites:
        if s.parent.startswith('Actors') or not s.visible or s.kind in ('fence',):
            continue
        sig = (s.rgba.shape, hash(s.rgba.tobytes()))
        by.setdefault(sig, []).append(s)
    for sig, ss in by.items():
        if len(ss) < 3:
            continue
        for axis in (0, 1):
            ss2 = sorted(ss, key=lambda s: s.origin[axis])
            for i in range(len(ss2) - 2):
                trio = ss2[i:i + 3]
                other = [t.origin[1 - axis] for t in trio]
                d = np.diff([t.origin[axis] for t in trio])
                if max(other) - min(other) <= 0.1 * H and d.min() > 0 and d.max() - d.min() <= 0.15 * H and d.max() < 3 * H:
                    box = (int(min(t.box[0] for t in trio)), int(min(t.box[1] for t in trio)),
                           int(max(t.box[2] for t in trio)), int(max(t.box[3] for t in trio)))
                    fs.append(Finding('logic.prop_row', 'fault', box,
                                      f'the same drawing ({trio[0].kind}) placed {len(trio)} times on one line at even '
                                      f'spacing: {", ".join(t.name for t in trio)}',
                                      'vary the drawings (a sibling, flipped, a different size or state) and break the line '
                                      'unless people set them out so (world-rules.md 6.7)',
                                      score=3.0, threshold=3, subject=trio[0].kind))
                    break
    from .core import merge_findings
    return merge_findings(fs, 0.3)


def check_wiring(zone_ids=None) -> list[Finding]:
    """Doors, spawns, quests, dialogue and restore sites across every zone."""
    zones = json.load(open(os.path.join(GAME, 'data', 'zones.json')))
    loaded = {zid: load_zone(zid) for zid in zones}
    dialogue = {}
    for p in glob.glob(os.path.join(GAME, 'data', 'dialogue', '*.json')):
        dialogue.update(json.load(open(p)))
    fs = []
    speakers = {t['speaker'] for z in loaded.values() for t in z.talkers}
    camps = {c for z in loaded.values() for c in z.camps}
    for zid, z in loaded.items():
        if zone_ids and zid not in zone_ids:
            continue
        if 'start' not in z.spawns:
            fs.append(Finding('logic.wiring', 'blocker', (0, 0, 1, 1), f'{zid}: no spawn named start',
                              'add a Marker2D "start" under Spawns', subject=zid))
        for d in z.doors:
            x, y = d['pos']
            box = (int(x) - 20, int(y) - 20, int(x) + 20, int(y) + 20)
            if d['zone'] not in zones:
                fs.append(Finding('logic.wiring', 'polish', box,
                                  f'{zid}: door {d["name"]} leads to "{d["zone"]}", which is not in data/zones.json (the door '
                                  'is refused at runtime)', 'add the zone, or mark the door as waiting for its act in the '
                                  'plan and show a closed gate', subject=d['name']))
            elif d['spawn'] not in loaded[d['zone']].spawns:
                fs.append(Finding('logic.wiring', 'blocker', box,
                                  f'{zid}: door {d["name"]} sends the player to spawn "{d["spawn"]}" in {d["zone"]}, which '
                                  'has no such marker', f'add Spawns/{d["spawn"]} in {d["zone"]} or fix target_spawn',
                                  subject=d['name']))
        for t in z.talkers:
            if t['speaker'] not in dialogue:
                x, y = t['pos']
                fs.append(Finding('logic.wiring', 'fault', (int(x) - 20, int(y) - 40, int(x) + 20, int(y) + 10),
                                  f'{zid}: {t["key"]} speaks as "{t["speaker"]}", who has no dialogue entry',
                                  'add the speaker to data/dialogue/*.json', subject=t['speaker']))
    for p in glob.glob(os.path.join(GAME, 'data', 'quests', '*.json')):
        q = json.load(open(p))
        events = [q.get('start', {}).get('on')] + [s.get('on') for s in q.get('steps', [])]
        for ev in events:
            if not ev:
                continue
            kind, _, arg = ev.partition(':')
            ok = True
            if kind == 'talk':
                ok = arg in speakers
            elif kind == 'camp':
                ok = arg in camps
            elif kind == 'enter':
                ok = arg in zones
            elif kind == 'restore':
                ok = any(arg in json.dumps(z.plan or {}) for z in loaded.values())
            if not ok:
                fs.append(Finding('logic.wiring', 'blocker', (0, 0, 1, 1),
                                  f'quest {q["id"]}: event "{ev}" can never be sent (no {kind} "{arg}" in any zone)',
                                  'place the speaker, camp, zone or restore site, or fix the event name',
                                  subject=q['id']))
    return fs


GRID_CELL = 8.0          # world px: the soft grid's cell (eastward-edges.md 1.1)
GRID_CLUTTER = ('damage', 'smoke', 'fire', 'glow', 'rubble', 'debris', 'shadow', 'fx', 'boards', 'mushroom',
                'fern', 'flower', 'tuft', 'leaf')


def check_grid(z: Zone, H=GAME_H, tol: float = 0.5) -> list[Finding]:
    """logic.off_grid: every structure and prop stands on the soft grid (Matt, 26 Oct 10:42:
    "following the soft grid should also make world design and placement easier"; the board note
    to-all-grid-placement-1026). A sprite's foot (its y-sort origin) lies on a half-cell column (x a
    multiple of 4 world px) and a cell row (y a multiple of 8), within `tol` world px; clutter
    (rubble, debris, smoke and fire, damage overlays and shadows, low plants) may sit anywhere."""
    d = 3.0
    if z.plan and z.plan.get('box') and z.size[0]:
        d = z.size[0] / float(z.plan['box'][2])
    elif z.size[0]:
        d = 3.0
    fs = []
    for sp in z.sprites:
        if not sp.visible:
            continue
        nm = (sp.name + ' ' + sp.path).lower()
        if any(k in nm for k in GRID_CLUTTER):
            continue
        if any(k in sp.parent for k in ('Camp', 'Enem', 'People', 'Villager', 'Player')):
            continue                      # what walks (creatures, people) is not placed on the grid
        fx, fy = sp.origin[0] / d, sp.origin[1] / d
        ex = min(fx % (GRID_CELL / 2), GRID_CELL / 2 - fx % (GRID_CELL / 2))
        ey = min(fy % GRID_CELL, GRID_CELL - fy % GRID_CELL)
        if ex > tol or ey > tol:
            x0, y0, x1, y1 = (int(v) for v in sp.box)
            fs.append(Finding('logic.off_grid', 'fault', (x0, y0, x1, y1),
                              f'{sp.name}: its foot ({fx:.1f}, {fy:.1f}) world px is off the soft grid by '
                              f'{ex:.1f} across and {ey:.1f} down (a cell is {GRID_CELL:g} world px)',
                              'stand it on a cell: its foot on a multiple of 4 world px across and 8 down (python3 -m '
                              'scripts.art.grid_snap --write <zone> lays a plan on the grid, then regenerate the zone)',
                              score=max(ex, ey), threshold=tol, subject=sp.name))
    return fs


def review_zone(zone_id: str, H=GAME_H, wiring=True, stage: str | None = None) -> dict:
    z = load_zone(zone_id, stage)
    fs = []
    fs += check_occlusion(z, H)
    fs += check_intersect(z, H)
    fs += check_crowns(z, H)
    fs += check_reach(z, H)
    fs += check_shadows(z, H)
    fs += check_light_sources(z, H)
    fs += check_rows(z, H)
    fs += check_grid(z, H)
    from . import scale as S
    fs += S.check_zone(z, H)          # logic.scale: sizes against a person, doors, stairs, ground grain
    if wiring:
        fs += check_wiring([zone_id])
    return dict(zone=z, findings=fs)

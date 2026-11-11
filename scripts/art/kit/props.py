"""Prop and structure pieces as Godot scenes (docs/world-editor.md, "The kit: pieces").

    python3 -m scripts.art.kit.props        # writes game/kit/props/<id>.tscn and index.json

Each prop or structure piece becomes a scene: a KitPiece root (world/terrain/kit_piece.gd) at its
foot, its picture as a Sprite2D offset so the foot is the origin (the zone y-sorts by it), and its
solid box as a StaticBody2D on the walls layer. index.json carries what the game, the ground's
shadow pass and the validator read without opening the piece files: variants, foot, collision and
shadow in texels, role, approval. Generated: never edit the scenes by hand.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from scripts.art.kit.schema import PIECES, ROOT, piece_files

OUT = os.path.join(ROOT, 'game', 'kit', 'props')
D = 3


def _res(path: str) -> str:
    return path if path.startswith('res://') else 'res://' + os.path.relpath(path, os.path.join(ROOT, 'game'))


SQUASH, SHEAR, RIM = 0.3, 0.2, 6


def crown_shadow(png_res: str, foot, out_name: str):
    """A tree's cast shadow from its own silhouette (Claude A, 27 Oct: shaped from the crown, not
    an ellipse): every opaque texel at height h above the foot lands on the ground squashed to
    SQUASH of its height and pushed east by SHEAR of it (light from the upper left), its core two
    ramp steps down and its outer RIM texels one (house-style 6). Written as an R8 mask with its
    offset from the foot; TerrainGround and compose.shadows lay it like the ellipses."""
    from PIL import Image
    from scipy import ndimage as ndi
    a = np.asarray(Image.open(os.path.join(ROOT, 'game', png_res[len('res://'):])).convert('RGBA'))[..., 3] > 0
    H, W = a.shape
    fx, fy = foot
    ys, xs = np.nonzero(a)
    h = fy - ys - 0.5
    sx = np.round(xs + 0.5 + h * SHEAR - fx).astype(int)
    sy = np.round(h * -SQUASH).astype(int)
    x0, y0 = sx.min() - 2, sy.min() - 2
    m = np.zeros((sy.max() - y0 + 3, sx.max() - x0 + 3), bool)
    m[sy - y0, sx - x0] = True
    m = ndi.binary_closing(m, iterations=2)
    m = ndi.binary_fill_holes(m)
    core = ndi.binary_erosion(m, iterations=RIM)
    out = np.where(core, 2, np.where(m, 1, 0)).astype(np.uint8)
    Image.fromarray(out, 'L').save(os.path.join(OUT, 'art', out_name))
    return {'png': 'res://kit/props/art/' + out_name, 'offset': [int(x0), int(y0)]}


def _set_looks() -> dict:
    """{piece id: look} for the prop sets' buildings (scripts/art/kit/sets/looks.py)."""
    from scripts.art.kit.sets import looks as LK
    return LK.VOLUME_LOOKS


def volume_look(p: dict) -> dict | None:
    """The look a piece's body was drawn from by the house builder (houses.building), or None: a
    zone plan's building (the piece's audit source, part body) or a prop set's building
    (sets/looks.VOLUME_LOOKS, the Act 1 mill). Every such piece casts its volume's shadow
    (volume_shadow, bake's VOL.bake_cast) and no other: no structure draws two shadows."""
    looks = _set_looks()
    if p['id'] in looks:
        return dict(looks[p['id']])
    src = next((s for s in (p.get('audit') or {}).get('sources') or [] if s.get('part') == 'body'), None)
    plan_path = os.path.join(ROOT, 'game', 'data', 'plans', '%s.json' % (src or {}).get('zone'))
    if not src or not os.path.exists(plan_path):
        return None
    plan = json.load(open(plan_path))
    b = next((b for b in plan.get('buildings', []) if b['id'] == src.get('object')), None)
    if b is None:
        return None
    look = dict(plan.get('art', {}).get('looks', {}).get(b['id'], {}))
    look.setdefault('w', b['rect'][2])
    look.setdefault('depth', b['rect'][3])
    look.setdefault('seed', sum(map(ord, b['id'])))      # the zone painter's seed (town.py), so a front
    return look                                           # gable's stack stands where it was drawn


def volume_shadow(p: dict, out_name: str) -> dict | None:
    """A house's cast shadow from its volume (scripts/art/native/volume.py, eastward-edges 11.6): a
    column east of it shaped by its roof and stacks, from the look its body was drawn from (the
    piece's audit source in the zone plan, or a set's look in scripts/art/kit/sets/looks.py). Written
    as an R8 mask like a crown's (2 the core, 1 the rim) with its offset from the foot."""
    from PIL import Image
    from scripts.art.native import volume as VOL
    look = volume_look(p)
    if look is None:
        return None
    lv, ox, oy = VOL.house_cast(look, D)
    Image.fromarray(lv, 'L').save(os.path.join(OUT, 'art', out_name))
    return {'png': 'res://kit/props/art/' + out_name, 'offset': [int(ox), int(oy)]}


def _anim(rendering: dict, foot) -> dict | None:
    """The piece's looping strip (rendering.animations with a strip): where it is, its frames and
    rate, and its offset from the foot (a fall's frames cover its sheet; an animal's its whole
    picture, frame 0 being the still)."""
    for a in rendering.get('animations') or []:
        if a.get('strip') and a.get('frames', 0) > 1:
            region = a.get('region_px') or [0, 0] + list(a.get('frame_px') or [0, 0])
            return {'clip': a['clip'], 'strip': a['strip'], 'frames': int(a['frames']), 'fps': float(a.get('fps', 8)),
                    'offset': [region[0] - foot[0], region[1] - foot[1]], 'cover': not a.get('region_px'),
                    'reduced_motion': a.get('reduced_motion', 'hold:0')}
    return None


def entry(p: dict) -> dict:
    g = p.get('geometry', {})
    r = p.get('rendering', {})
    foot = g.get('foot') or [g['size_px'][0] / 2.0, g['size_px'][1]]
    col = g.get('collision') or {}
    rect = [v * D for v in col['rect']] if col.get('shape') == 'rect' and col.get('rect') else None
    # a round post (a sign's: geometry.collision {shape: circle, radius}, centred on the foot). The
    # index keeps `collision` a box for everything that reads boxes (the circle's bounding box) and
    # names the radius beside it: the scene's body is the circle and the walk mask blocks the cells
    # the circle touches (walk.py, walk.gd). It used to be dropped here, so a sign had no body in
    # its scene while the walk mask blocked its whole 2 by 2 footprint.
    radius = None
    if col.get('shape') == 'circle' and col.get('radius'):
        radius = round(col['radius'] * D, 3)
        radius = int(radius) if radius == int(radius) else radius
        rect = [-radius, -radius, 2 * radius, 2 * radius]
    cs = r.get('cast_shadow') or {}
    shadow = None
    if cs.get('shape') == 'ellipse' and cs.get('size'):
        shadow = {'size': [int(round(v * D)) for v in cs['size']], 'dir': [int(round(v * D)) for v in cs.get('dir', [0, 0])]}
    if (p['kind'] == 'structure' or p['id'] in _set_looks()) and p.get('variants'):
        # a building drawn by the house builder (houses.py), from a zone plan's look or a set's:
        # its volume's shadow, and only that one
        mk = volume_shadow(p, 'shadow_%s.png' % p['id'])
        shadow = {'mask': mk, 'kind': 'volume'} if mk else shadow
    if p.get('placement', {}).get('role') == 'tree' and p.get('variants'):
        v0 = p['variants'][0]
        shadow = {'mask': crown_shadow(v0['png'], v0.get('foot', foot), 'shadow_%s.png' % p['id'])}
    deck = p.get('gameplay', {}).get('deck')
    return {'kind': p['kind'], 'name': p['name'], 'foot': foot, 'collision': rect, 'shadow': shadow,
            'deck': [v * D for v in deck] if deck else None, 'z_sort': g.get('z_sort', 'foot'),
            'blocks_move': p.get('gameplay', {}).get('blocks_move', False),
            'requires': p.get('placement', {}).get('requires', []), 'forbids': p.get('placement', {}).get('forbids', []),
            'size_cells': g.get('size_cells'), 'footprint': g.get('footprint'), 'function': p.get('function', {}), 'story': p.get('story', {}),
            'role': p.get('placement', {}).get('role'), 'snap': p.get('placement', {}).get('snap', 'cell'),
            'approval': p['approval']['state'], 'painted': bool(r.get('paint')),
            **({'collision_circle': radius} if radius else {}),
            **({'sheet_px': g['sheet_px']} if g.get('sheet_px') else {}),
            **({'anim': _anim(r, foot)} if _anim(r, foot) else {}),
            'variants': {v['id']: {'png': v['png'], 'foot': v.get('foot', foot)} for v in p.get('variants', [])}}


def scene(pid: str, e: dict) -> str:
    v0 = next(iter(e['variants'].values()))
    lines = ['[gd_scene format=3]', '',
             '[ext_resource type="Script" path="res://world/terrain/kit_piece.gd" id="1"]',
             '[ext_resource type="Texture2D" path="%s" id="2"]' % v0['png'], '']
    # a box that blocks nobody (gameplay.blocks_move false: a landslip the way system holds shut, a cold
    # fire ring) is kept in the index for the ground's shadow pass and gets no body, so a zone built from
    # these scenes blocks exactly what the walk mask derived from the same records blocks
    solid = e['collision'] if e.get('blocks_move') else None
    circle = e.get('collision_circle') if solid else None
    if circle:
        lines += ['[sub_resource type="CircleShape2D" id="solid"]', 'radius = %g' % circle, '']
    elif solid:
        x, y, w, h = solid
        lines += ['[sub_resource type="RectangleShape2D" id="solid"]', 'size = Vector2(%g, %g)' % (w, h), '']
    lines += ['[node name="%s" type="Node2D"]' % ''.join(s.capitalize() for s in pid.split('_')),
              'script = ExtResource("1")', 'piece_id = "%s"' % pid, '',
              '[node name="Sprite" type="Sprite2D" parent="."]', 'texture = ExtResource("2")', 'centered = false',
              'offset = Vector2(%g, %g)' % (-v0['foot'][0], -v0['foot'][1]), '']
    an = e.get('anim')
    if an:
        # the loop (world/loop_fx.gd: only on screen and while the screen is active, frame 0 under
        # reduced motion). An animal's loop replaces its still (the still stays for the variant
        # picker, the bake and the shadow); a fall's lies over the sheet the bake drew.
        lines[3:3] = ['[ext_resource type="Script" path="res://world/loop_fx.gd" id="3"]',
                      '[ext_resource type="Texture2D" path="%s" id="4"]' % an['strip']]
        if an['cover']:
            i = lines.index('centered = false')
            lines[i:i] = ['visible = false']
        lines += ['[node name="%s" type="Sprite2D" parent="."]' % ('Idle' if an['cover'] else 'Flow'),
                  'script = ExtResource("3")', 'texture = ExtResource("4")', 'centered = false',
                  'offset = Vector2(%g, %g)' % tuple(an['offset']), 'hframes = %d' % an['frames'], 'fps = %g' % an['fps'], '']
    if solid:
        x, y, w, h = solid
        lines += ['[node name="Solid" type="StaticBody2D" parent="."]', 'collision_mask = 0', '',
                  '[node name="Shape" type="CollisionShape2D" parent="Solid"]',
                  'position = Vector2(%g, %g)' % (x + w / 2, y + h / 2), 'shape = SubResource("solid")', '']
    return '\n'.join(lines)


def build(check: bool = False) -> int:
    """Write every prop scene and the index; with check, write nothing and fail if a committed
    scene or the index is not what the pieces make (Claude A, 2 Nov: the index had drifted from
    the pieces since the schema migration)."""
    os.makedirs(OUT, exist_ok=True)
    index, scenes = {}, {}
    for f in piece_files():
        p = json.load(open(f))
        if p['kind'] not in ('prop', 'structure') or not p.get('variants'):
            continue
        e = entry(p)
        index[p['id']] = e
        scenes[p['id'] + '.tscn'] = scene(p['id'], e)
    text = json.dumps(index, indent=1, sort_keys=True)
    if check:
        stale = [n for n, t in scenes.items()
                 if not os.path.exists(os.path.join(OUT, n)) or open(os.path.join(OUT, n)).read() != t]
        if open(os.path.join(OUT, 'index.json')).read().rstrip('\n') != text:
            stale.append('index.json')
        if stale:
            print('props: stale %s (run python3 -m scripts.art.kit.props)' % ', '.join(sorted(stale)))
            return 1
        print('props: %d scenes and the index match the pieces' % len(index))
        return 0
    for n, t in scenes.items():
        open(os.path.join(OUT, n), 'w').write(t)
    open(os.path.join(OUT, 'index.json'), 'w').write(text)
    print('props: %d scenes' % len(index))
    return 0


if __name__ == '__main__':
    sys.exit(build(check='--check' in sys.argv[1:]))

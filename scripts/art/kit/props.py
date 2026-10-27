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


def entry(p: dict) -> dict:
    g = p.get('geometry', {})
    r = p.get('rendering', {})
    foot = g.get('foot') or [g['size_px'][0] / 2.0, g['size_px'][1]]
    col = g.get('collision') or {}
    rect = [v * D for v in col['rect']] if col.get('shape') == 'rect' and col.get('rect') else None
    cs = r.get('cast_shadow') or {}
    shadow = None
    if cs.get('shape') == 'ellipse' and cs.get('size'):
        shadow = {'size': [int(round(v * D)) for v in cs['size']], 'dir': [int(round(v * D)) for v in cs.get('dir', [0, 0])]}
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
            'variants': {v['id']: {'png': v['png'], 'foot': v.get('foot', foot)} for v in p.get('variants', [])}}


def scene(pid: str, e: dict) -> str:
    v0 = next(iter(e['variants'].values()))
    lines = ['[gd_scene format=3]', '',
             '[ext_resource type="Script" path="res://world/terrain/kit_piece.gd" id="1"]',
             '[ext_resource type="Texture2D" path="%s" id="2"]' % v0['png'], '']
    if e['collision']:
        x, y, w, h = e['collision']
        lines += ['[sub_resource type="RectangleShape2D" id="solid"]', 'size = Vector2(%g, %g)' % (w, h), '']
    lines += ['[node name="%s" type="Node2D"]' % ''.join(s.capitalize() for s in pid.split('_')),
              'script = ExtResource("1")', 'piece_id = "%s"' % pid, '',
              '[node name="Sprite" type="Sprite2D" parent="."]', 'texture = ExtResource("2")', 'centered = false',
              'offset = Vector2(%g, %g)' % (-v0['foot'][0], -v0['foot'][1]), '']
    if e['collision']:
        x, y, w, h = e['collision']
        lines += ['[node name="Solid" type="StaticBody2D" parent="."]', 'collision_mask = 0', '',
                  '[node name="Shape" type="CollisionShape2D" parent="Solid"]',
                  'position = Vector2(%g, %g)' % (x + w / 2, y + h / 2), 'shape = SubResource("solid")', '']
    return '\n'.join(lines)


def build() -> int:
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for f in piece_files():
        p = json.load(open(f))
        if p['kind'] not in ('prop', 'structure') or not p.get('variants'):
            continue
        e = entry(p)
        index[p['id']] = e
        open(os.path.join(OUT, p['id'] + '.tscn'), 'w').write(scene(p['id'], e))
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'), indent=1, sort_keys=True)
    print('props: %d scenes' % len(index))
    return 0


if __name__ == '__main__':
    sys.exit(build())

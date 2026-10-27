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

from scripts.art.kit.schema import PIECES, ROOT, piece_files

OUT = os.path.join(ROOT, 'game', 'kit', 'props')
D = 3


def _res(path: str) -> str:
    return path if path.startswith('res://') else 'res://' + os.path.relpath(path, os.path.join(ROOT, 'game'))


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
    deck = p.get('gameplay', {}).get('deck')
    return {'kind': p['kind'], 'name': p['name'], 'foot': foot, 'collision': rect, 'shadow': shadow,
            'deck': [v * D for v in deck] if deck else None, 'z_sort': g.get('z_sort', 'foot'),
            'blocks_move': p.get('gameplay', {}).get('blocks_move', False),
            'requires': p.get('placement', {}).get('requires', []), 'forbids': p.get('placement', {}).get('forbids', []),
            'size_cells': g.get('size_cells'), 'function': p.get('function', {}), 'story': p.get('story', {}),
            'role': p.get('placement', {}).get('role'), 'snap': p.get('placement', {}).get('snap', 'cell'),
            'approval': p['approval']['state'],
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

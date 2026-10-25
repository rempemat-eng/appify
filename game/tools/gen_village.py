#!/usr/bin/env python3
"""A drawn village zone from its zone plan: the kit's art, then the Godot scene.

    python3 game/tools/gen_village.py crossroads            render with the kit, then write the scene
    python3 game/tools/gen_village.py crossroads --no-render   rewrite the scene from the art already in the folder
    python3 game/tools/gen_village.py crossroads --preview DIR also write the whole zone per stage (review only)

Renders game/data/plans/<id>.json with `python3 -m scripts.art.native.town` (scripts/art/native/village.py
draws the buildings, their damage overlays and the props) into game/zones/<id>/art/ and kit.json, then writes
game/zones/<id>/<id>.tscn in place of the blockout (tools/gen_blockout.py), keeping its node names:

  Ground       the ground picture (lawn, square, roads, walls, stair, lots, crater, static shadows), z -10
  Walls        the box's edges, the faces (with the stair's gap), the building footprints and every solid
               object that never changes
  Props        y-sorted with the actors: one Sprite2D per building, prop, thing and dressing piece, its feet as
               its origin. An item with a condition sits in a Conditional (world/conditional.gd) named
               If_<id> with its own collision: a building's damage overlay (If_<id>_damage, shown until its
               restore), the plan's props (If_smithy_rubble, If_forge_fire, ...)
  Actors       people, things, restore sites and camps as in the blockout (Morel drawn from the cast)
  BuildingDoors, Spawns, RaidPads, Doors

Positions are world px times DENSITY (3 texels). Regenerate; never edit the scene by hand.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_blockout as GB  # noqa: E402

GAME = GB.GAME
ROOT = os.path.dirname(GAME)
DENSITY = GB.DENSITY
t, vec, pascal = GB.t, GB.vec, GB.pascal

# people drawn from the cast (game/assets/characters/<id>): idle, facing the player
CAST = {'morel': 'morel'}
MARKER = {'people': 82.0, 'notice_board': 108.0, 'waystone': 108.0}


def render(zid: str, preview: str | None) -> None:
    cmd = [sys.executable, '-m', 'scripts.art.native.town', '--plan', os.path.join(GAME, 'data', 'plans', zid + '.json'),
           '--density', str(DENSITY), '--out', os.path.join(GAME, 'zones', zid, 'art')]
    if preview:
        cmd += ['--preview', preview]
    subprocess.run(cmd, cwd=ROOT, check=True)


def build(plan: dict, kit: dict) -> str:
    s = GB.Scene()
    zid = plan['id']
    res = f'res://zones/{zid}/art/'
    bx, by, bw, bh = plan['box']
    ext_tex = {}

    def tex(png):
        if png not in ext_tex:
            ext_tex[png] = 't%d' % len(ext_tex)
        return ext_tex[png]

    s.node(pascal(zid), 'Node2D', None, {
        'y_sort_enabled': 'true', 'script': 'ExtResource("zone")', 'zone_id': '"%s"' % zid,
        'bounds': 'Rect2(0, 0, %g, %g)' % (t(bw), t(bh))})
    s.node('Ground', 'Sprite2D', '.', {'z_index': -10, 'texture': 'ExtResource("%s")' % tex('ground.png'), 'centered': 'false'})

    # walls: the box's edges, the faces, the buildings and the solid things that never change
    s.node('Walls', 'Node2D', '.')
    edge = 8
    for name, r in (('EdgeN', [bx, by - edge, bw, edge]), ('EdgeS', [bx, by + bh, bw, edge]),
                    ('EdgeW', [bx - edge, by, edge, bh]), ('EdgeE', [bx + bw, by, edge, bh])):
        s.solid(name, 'Walls', r)
    for f in plan.get('faces', []):
        s.solid('Face_' + f['id'], 'Walls', f['rect'])
    for b in plan.get('buildings', []):
        s.solid('Building_' + b['id'], 'Walls', b['rect'])
    for o in kit['objects']:
        if o.get('solid') and not o.get('cond') and o['kind'] != 'building':
            s.solid('Solid_' + o['id'], 'Walls', o['solid'])

    # every drawn thing, y-sorted with the actors by its feet
    s.node('Props', 'Node2D', '.', {'y_sort_enabled': 'true'})
    for o in kit['objects']:
        parent = 'Props'
        if o.get('cond'):
            parent = s.wrap('Props', {'if': o['cond']}, 'If_' + o['id'])
        if o.get('png'):
            fx, fy = o['foot']
            ox, oy = o['offset']
            s.node(pascal(o['id']), 'Sprite2D', parent, {
                'position': vec(fx, fy), 'texture': 'ExtResource("%s")' % tex(o['png']), 'centered': 'false',
                'offset': vec(ox, oy)})
        if o.get('solid') and o.get('cond'):
            s.solid(pascal(o['id']) + 'Body', parent, o['solid'])

    # actors: people, things, restore sites and camps (as the blockout, with the cast where it is drawn)
    s.node('Actors', 'Node2D', '.', {'y_sort_enabled': 'true'})
    cast_ext = {}
    for kind in ('people', 'things'):
        for p in plan.get(kind, []):
            parent = s.wrap('Actors', p, 'If_' + p['id'])
            x, y = p['at']
            name = pascal(p['id'])
            props = {'position': vec(t(x), t(y)), 'script': 'ExtResource("talk")', 'speaker_id': '"%s"' % p['speaker'],
                     'marker_height': MARKER.get(p['speaker'], MARKER['people'] if kind == 'people' else 40.0)}
            if 'verb' in p:
                props['verb'] = '"%s"' % p['verb']
            s.node(name, 'Area2D', parent, props)
            path = parent + '/' + name
            s.node('Shape', 'CollisionShape2D', path, {'shape': 'SubResource("%s")' % s.circle_shape(p.get('radius', 30))})
            col = p.get('colour', '#a0a0a0')
            if len(col) == 9 and col.endswith('00'):
                continue
            if kind == 'people':
                cid = CAST.get(p['speaker'])
                if cid:
                    sheet = f'res://assets/characters/{cid}/sheets/idle_S.png'
                    cast_ext.setdefault(sheet, 'c%d' % len(cast_ext))
                    s.node('Body', 'Sprite2D', path, {'texture': 'ExtResource("%s")' % cast_ext[sheet], 'centered': 'false',
                                                      'region_enabled': 'true', 'region_rect': 'Rect2(0, 0, 160, 144)',
                                                      'offset': vec(-80, -136)})
                else:
                    # not drawn yet: the blockout's marker and name
                    s.polygon('Body', path, [[-4, -16], [4, -16], [4, 0], [-4, 0]], GB.colour(col))
                    s.node('Name', 'Label', path, {'offset_left': -40, 'offset_top': -72, 'offset_right': 40,
                                                    'offset_bottom': -52, 'text': '"%s"' % p.get('name', p['id']),
                                                    'horizontal_alignment': 1})
            s.node('Post', 'StaticBody2D', path, {'collision_mask': 0})
            s.node('Shape', 'CollisionShape2D', path + '/Post', {'shape': 'SubResource("%s")' % s.circle_shape(5)})
    for site in plan.get('restore_sites', []):
        parent = s.wrap('Actors', site, 'If_' + site['id'])
        x, y = site['at']
        name = pascal(site['id'])
        s.node(name, 'Area2D', parent, {'position': vec(t(x), t(y)), 'script': 'ExtResource("site")',
                                         'restore_id': '"%s"' % site['restore'], 'verb': '"Restore"'})
        s.node('Shape', 'CollisionShape2D', parent + '/' + name, {'shape': 'SubResource("%s")' % s.circle_shape(30)})
    for camp in plan.get('camps', []):
        name = pascal(camp['id']) + 'Camp'
        s.node(name, 'Node2D', 'Actors', {'script': 'ExtResource("camp")', 'camp_id': '"%s"' % camp['id']})
        for i, (x, y) in enumerate(camp['enemies']):
            props = {'position': vec(t(x), t(y))}
            if camp.get('boss'):
                props['scale'] = 'Vector2(2, 2)'
            s.node('Enemy%d' % (i + 1), None, 'Actors/' + name, props, instance='enemy')

    s.node('BuildingDoors', 'Node2D', '.')
    for b in plan.get('buildings', []):
        if 'door' in b:
            s.node(pascal(b['id']), 'Marker2D', 'BuildingDoors', {'position': vec(t(b['door'][0]), t(b['door'][1])),
                                                                  'metadata/building': '"%s"' % b['id']})
    s.node('Spawns', 'Node2D', '.')
    for sp in plan.get('spawns', []):
        s.node(sp['id'], 'Marker2D', 'Spawns', {'position': vec(t(sp['at'][0]), t(sp['at'][1]))})
    s.node('RaidPads', 'Node2D', '.')
    for pad in plan.get('raid_pads', []):
        s.node(pad['id'], 'Marker2D', 'RaidPads', {'position': vec(t(pad['at'][0]), t(pad['at'][1])),
                                                   'metadata/stage': pad.get('stage', 0),
                                                   'metadata/lane': '"%s"' % pad.get('lane', '')})
    s.node('Doors', 'Node2D', '.')
    for d in plan.get('doors', []):
        x, y, w, h = d['rect']
        name = pascal(d['id'])
        props = {'position': vec(t(x + w / 2), t(y + h / 2)), 'script': 'ExtResource("door")',
                 'target_zone': '"%s"' % d['to'], 'target_spawn': '"%s"' % d.get('spawn', 'start')}
        if 'if' in d:
            props['only_if'] = json.dumps(json.dumps(d['if'], separators=(',', ':')))
        s.node(name, 'Area2D', 'Doors', props)
        s.node('Shape', 'CollisionShape2D', 'Doors/' + name, {'shape': 'SubResource("%s")' % s.rect_shape(t(w), t(h))})

    ext = ''.join('[ext_resource type="%s" path="%s" id="%s"]\n' % (typ, path, i) for i, typ, path in GB.EXT)
    ext += ''.join('[ext_resource type="Texture2D" path="%s%s" id="%s"]\n' % (res, png, i) for png, i in ext_tex.items())
    ext += ''.join('[ext_resource type="Texture2D" path="%s" id="%s"]\n' % (path, i) for path, i in cast_ext.items())
    return '[gd_scene format=3]\n\n' + ext + '\n' + '\n'.join(s.subs) + '\n' + '\n'.join(s.nodes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('zone')
    ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--preview', default=None)
    a = ap.parse_args(argv)
    zid = a.zone
    if not a.no_render:
        render(zid, a.preview)
    plan = json.load(open(os.path.join(GAME, 'data', 'plans', zid + '.json')))
    kit = json.load(open(os.path.join(GAME, 'zones', zid, 'kit.json')))
    out = os.path.join(GAME, 'zones', zid, zid + '.tscn')
    with open(out, 'w') as f:
        f.write(build(plan, kit))
    print('wrote', os.path.relpath(out, GAME), len(kit['objects']), 'objects')
    return 0


if __name__ == '__main__':
    sys.exit(main())

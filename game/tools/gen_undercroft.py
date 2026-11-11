#!/usr/bin/env python3
"""The Undercroft drawn: its art from the kit, then the Godot scene (in place of the blockout).

    python3 game/tools/gen_undercroft.py                 render the zone and the Thornback, then write the scene
    python3 game/tools/gen_undercroft.py --no-render     rewrite the scene from the art already in the folders
    python3 game/tools/gen_undercroft.py --preview DIR   also write the whole zone and the boss sheet (review only)

Renders game/data/plans/undercroft.json with `python3 -m scripts.art.native.undercroft` into
game/zones/undercroft/art/ and kit.json, the Thornback with `python3 -m scripts.art.native.thornback` into
game/bosses/thornback/art/, then writes game/zones/undercroft/undercroft.tscn with the blockout's node names:

  Ground       the ground picture (flagstones, the vault's tops and faces, the stair, light), z -10
  Floor        pictures that lie on the floor under everyone (the plate, the lit channel, the sunk slab), z -9
  WallFx       the torches on the wall faces (world/torch.gd), z -8, behind everyone
  Walls        the box's edges, every wall block of the plan (its top and face) and the solid props (a low
               one, under 64 texels, on layers 1 and 5 so arrows fly over it: tools/gen_physics.py)
  Props        y-sorted with the actors: props, torches (world/torch.gd), the lever, the sealed slab (with its
               collision, in a Conditional until the lever is pulled), Cairn in his alcove
  Actors       the things (the shard, Cairn), the plate (world/pressure_plate.gd), the lever (world/seal_lever.gd),
               the rooms' camp of Codex's enemies (enemies/slice_enemy.gd, dressed as the woodland's creatures by
               enemies/creature_dresser.gd, without its den) and the Thornback's camp
               (bosses/thornback.tscn, kept inside the plan's arena), the Thornback at rest once freed
  Spawns, Doors

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
import gen_physics as PH  # noqa: E402

GAME = GB.GAME
ROOT = os.path.dirname(GAME)
DENSITY = GB.DENSITY
t, vec, pascal = GB.t, GB.vec, GB.pascal
ZID = 'undercroft'

EXT = [
    ('zone', 'Script', 'res://world/zone.gd'),
    ('cond', 'Script', 'res://world/conditional.gd'),
    ('talk', 'Script', 'res://world/interactable.gd'),
    ('door', 'Script', 'res://world/door.gd'),
    ('camp', 'Script', 'res://world/camp.gd'),
    ('torch', 'Script', 'res://world/torch.gd'),
    ('plate', 'Script', 'res://world/pressure_plate.gd'),
    ('lever', 'Script', 'res://world/seal_lever.gd'),
    ('enemy', 'Script', 'res://enemies/slice_enemy.gd'),
    ('dresser', 'Script', 'res://enemies/creature_dresser.gd'),
    ('boss', 'PackedScene', 'res://bosses/thornback.tscn'),
    ('rest', 'Script', 'res://bosses/thornback_rest.gd'),
]


def render(preview):
    plan = os.path.join(GAME, 'data', 'plans', ZID + '.json')
    cmd = [sys.executable, '-m', 'scripts.art.native.undercroft', '--plan', plan, '--density', str(DENSITY),
           '--out', os.path.join(GAME, 'zones', ZID, 'art')]
    boss = [sys.executable, '-m', 'scripts.art.native.thornback', '--density', str(DENSITY),
            '--out', os.path.join(GAME, 'bosses', 'thornback', 'art')]
    if preview:
        cmd += ['--preview', preview]
        boss += ['--preview', preview]
    subprocess.run(cmd, cwd=ROOT, check=True)
    subprocess.run(boss, cwd=ROOT, check=True)


def cond_json(c):
    return json.dumps(json.dumps(c, separators=(',', ':')))


def build(plan: dict, kit: dict) -> str:
    s = GB.Scene()
    res = f'res://zones/{ZID}/art/'
    bx, by, bw, bh = plan['box']
    ext_tex = {}

    def tex(png):
        if png not in ext_tex:
            ext_tex[png] = 't%d' % len(ext_tex)
        return 'ExtResource("%s")' % ext_tex[png]

    s.node(pascal(ZID), 'Node2D', None, {'y_sort_enabled': 'true', 'script': 'ExtResource("zone")', 'zone_id': '"%s"' % ZID,
                                        'bounds': 'Rect2(0, 0, %g, %g)' % (t(bw), t(bh))})
    s.node('Ground', 'Sprite2D', '.', {'z_index': -10, 'texture': tex('ground.png'), 'centered': 'false'})

    def wrap(parent, cond, name):
        if not cond:
            return parent
        s.node(name, 'Node2D', parent, {'script': 'ExtResource("cond")', 'only_if': cond_json(cond)})
        return parent + '/' + name

    def sprite(o, parent):
        foot, offset = o['foot'], o['offset']
        if o['kind'] not in ('floor', 'torch'):
            # the y-sort point on the drawn feet (tools/gen_physics.py); the texels stay where they are
            foot, offset = PH.on_feet(os.path.join(GAME, 'zones', ZID, 'art', o['png']), foot, offset, o.get('frames') or 1)
        props = {'position': vec(*foot), 'texture': tex(o['png']), 'centered': 'false', 'offset': vec(*offset)}
        if o.get('frames'):
            props.update({'hframes': o['frames'], 'script': 'ExtResource("torch")'})
        s.node(pascal(o['id']), 'Sprite2D', parent, props)

    s.node('Floor', 'Node2D', '.', {'z_index': -9})
    for o in kit['objects']:
        if o['kind'] == 'floor':
            sprite(o, wrap('Floor', o.get('cond'), 'If_' + o['id']))

    s.node('Walls', 'Node2D', '.')
    edge = 8
    for name, r in (('EdgeN', [bx, by - edge, bw, edge]), ('EdgeS', [bx, by + bh, bw, edge]),
                    ('EdgeW', [bx - edge, by, edge, bh]), ('EdgeE', [bx + bw, by, edge, bh])):
        s.solid(name, 'Walls', r)
    for w in plan['walls']:
        s.solid('Wall_' + w['id'], 'Walls', w['rect'])
    def low(o):
        # the low rule (tools/gen_physics.py): rubble, roots and the urn stand under 64 texels, so an arrow
        # flies over them; the broken pillars, the lever and the sealed slab stop it
        frames = o.get('frames') or 1
        return PH.is_low(PH.rise(os.path.join(GAME, 'zones', ZID, 'art', o['png']), -o['offset'][1], frames))

    # kit.json's `solid` is the plan's `box` where a prop has one (measured on the picture), else the box its size gives
    for o in kit['objects']:
        if o.get('solid') and not o.get('cond'):
            s.solid('Solid_' + o['id'], 'Walls', o['solid'], low(o))

    # torches hang on the wall faces, behind everyone who can stand in the room: drawn with the walls,
    # not y-sorted (their feet would be the wall's foot, far below the bracket)
    s.node('WallFx', 'Node2D', '.', {'z_index': -8})
    for o in kit['objects']:
        if o['kind'] == 'torch':
            sprite(o, 'WallFx')
    s.node('Props', 'Node2D', '.', {'y_sort_enabled': 'true'})
    for o in kit['objects']:
        if o['kind'] in ('floor', 'torch'):
            continue
        parent = wrap('Props', o.get('cond'), 'If_' + o['id'])
        sprite(o, parent)
        if o.get('solid') and o.get('cond'):
            s.solid(pascal(o['id']) + 'Body', parent, o['solid'], low(o))

    s.node('Actors', 'Node2D', '.', {'y_sort_enabled': 'true'})
    for th in plan.get('things', []):
        parent = wrap('Actors', th.get('if'), 'If_' + th['id'])
        x, y = th['at']
        name = pascal(th['id'])
        s.node(name, 'Area2D', parent, {'position': vec(t(x), t(y)), 'script': 'ExtResource("talk")',
                                        'speaker_id': '"%s"' % th['speaker'], 'verb': '"%s"' % th.get('verb', 'Look'),
                                        'marker_height': 60.0})
        s.node('Shape', 'CollisionShape2D', parent + '/' + name, {'shape': 'SubResource("%s")' % s.circle_shape(30)})
    pz = plan.get('puzzle')
    if pz:
        pl = pz['plate']
        x, y = pl['at']
        w, h = pl['size']
        s.node('SealPlate', 'Area2D', 'Actors', {'position': vec(t(x), t(y)), 'script': 'ExtResource("plate")',
                                                 'flag': '"%s"' % pl['flag']})
        # Pressed when the feet stand anywhere on the drawn slab (scripts/art/native/undercroft.py p_plate: the
        # raised panel is t(w) square, its middle 4 texels above the plate's point). The area is met by the
        # body, a circle of r 9 centred 4 texels above the feet, so it is the panel moved up 4 and less 7 a side:
        # less 9 would leave the panel's four corners unpressed (the round body misses a square's corner), less
        # 7 is the least that covers them, and it reaches 2 texels past the panel's edges, into the frame's gap.
        s.node('Shape', 'CollisionShape2D', 'Actors/SealPlate', {'position': vec(0, -16),
                                                               'shape': 'SubResource("%s")' % s.rect_shape(t(w) - 14, t(h) - 14)})
        lv = pz['lever']
        x, y = lv['at']
        s.node('SealLever', 'Area2D', 'Actors', {'position': vec(t(x), t(y)), 'script': 'ExtResource("lever")',
                                                 'speaker_id': '"seal_lever"', 'verb': '"Pull"', 'marker_height': 60.0,
                                                 'needs_flag': '"%s"' % pl['flag'], 'flag': '"%s"' % lv['flag']})
        s.node('Shape', 'CollisionShape2D', 'Actors/SealLever', {'shape': 'SubResource("%s")' % s.circle_shape(30)})
    arena = plan.get('arena')
    for camp in plan.get('camps', []):
        name = pascal(camp['id']) + 'Camp'
        s.node(name, 'Node2D', 'Actors', {'script': 'ExtResource("camp")', 'camp_id': '"%s"' % camp['id']})
        if not camp.get('boss'):
            # the drawn creatures over Codex's roles, as the woodland camp (enemies/woodland_camp.tscn);
            # first in the camp so it sees each enemy enter; no bramble den in a stone vault
            s.node('Dresser', 'Node', 'Actors/' + name, {'script': 'ExtResource("dresser")', 'with_den': 'false'})
        for i, e in enumerate(camp['enemies']):
            x, y = e[0], e[1]
            if camp.get('boss'):
                ax, ay, aw, ah = arena
                s.node('Thornback', None, 'Actors/' + name, {'position': vec(t(x), t(y)),
                                                              'arena': 'Rect2(%g, %g, %g, %g)' % (t(ax), t(ay), t(aw), t(ah))},
                       instance='boss')
            else:
                role = e[2] if len(e) > 2 else 'rusher'
                s.node('%s%d' % (role.capitalize(), i + 1), 'CharacterBody2D', 'Actors/' + name,
                       {'position': vec(t(x), t(y)), 'script': 'ExtResource("enemy")', 'role': '"%s"' % role})
    if arena:
        x, y = plan.get('rest', plan['camps'][-1]['enemies'][0][:2])
        s.node('ThornbackAtRest', 'Node2D', 'Actors', {'position': vec(t(x), t(y)), 'script': 'ExtResource("rest")'})

    s.node('Spawns', 'Node2D', '.')
    for sp in plan.get('spawns', []):
        s.node(sp['id'], 'Marker2D', 'Spawns', {'position': vec(t(sp['at'][0]), t(sp['at'][1]))})
    s.node('Doors', 'Node2D', '.')
    for d in plan.get('doors', []):
        x, y, w, h = d['rect']
        name = pascal(d['id'])
        props = {'position': vec(t(x + w / 2), t(y + h / 2)), 'script': 'ExtResource("door")',
                 'target_zone': '"%s"' % d['to'], 'target_spawn': '"%s"' % d.get('spawn', 'start')}
        if 'if' in d:
            props['only_if'] = cond_json(d['if'])
        s.node(name, 'Area2D', 'Doors', props)
        s.node('Shape', 'CollisionShape2D', 'Doors/' + name, {'shape': 'SubResource("%s")' % s.rect_shape(t(w), t(h))})

    ext = ''.join('[ext_resource type="%s" path="%s" id="%s"]\n' % (typ, path, i) for i, typ, path in EXT)
    ext += ''.join('[ext_resource type="Texture2D" path="%s%s" id="%s"]\n' % (res, png, i) for png, i in ext_tex.items())
    return '[gd_scene format=3]\n\n' + ext + '\n' + '\n'.join(s.subs) + '\n' + '\n'.join(s.nodes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-render', action='store_true')
    ap.add_argument('--preview', default=None)
    a = ap.parse_args(argv)
    if not a.no_render:
        render(a.preview)
    plan = json.load(open(os.path.join(GAME, 'data', 'plans', ZID + '.json')))
    kit = json.load(open(os.path.join(GAME, 'zones', ZID, 'kit.json')))
    out = os.path.join(GAME, 'zones', ZID, ZID + '.tscn')
    with open(out, 'w') as f:
        f.write(build(plan, kit))
    print('wrote', os.path.relpath(out, GAME), len(kit['objects']), 'objects')
    return 0


if __name__ == '__main__':
    sys.exit(main())

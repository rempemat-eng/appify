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
               object that never changes. A solid's box is the plan's unless the kit library holds a reviewed
               one for the picture, and a low one (under 64 texels) is on layers 1 and 5 so arrows fly over
               it (solids(), tools/gen_physics.py, docs/physics.md)
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
import gen_physics as PH  # noqa: E402

GAME = GB.GAME
ROOT = os.path.dirname(GAME)
DENSITY = GB.DENSITY
t, vec, pascal = GB.t, GB.vec, GB.pascal

# people drawn from the cast (game/assets/characters/<id>) as Villagers (world/villager.gd): idle or
# their work loop, turning to talk when the player is near. Plan people may set "face" and "work".
CAST = {'morel': 'morel', 'hale': 'hale', 'moss': 'moss', 'ada_fern': 'ada'}
# looping effect strips (tools/gen_village_fx.py) that replace a kit picture: id -> (strip, drawings, fps)
LOOPS = {'forge_fire': ('fx/forge_fire_8.png', 8, 9.0)}
# chimney smoke over a building's pot while a condition holds: building id -> condition
# The forge burns once Hale is home to work the bellows (10 Nov): a forge paid for while she is still on
# the woodland path has only "an ember under the ash" (the mark's own line), so until the next zone load
# brings her home there is no flame and no smoke. The plan's own condition stays "restored" (the kit's
# pictures and the review's stages read that; every stage after the first has Hale home, game.gd apply_stage).
TENDED = {'forge_fire': {'flags': ['hale_walked_home']}}
# ... and in that wait the hearth is not empty (Matt, 11 Nov: "a dark hearth until she arrives", the ember
# drawing): the banked ash with its embers (tools/gen_village_fx.py), in the fire's own frame and foot,
# shown while the fire is untended. id -> (strip, drawings, fps, the extra condition)
BANKED = {'forge_fire': ('fx/forge_ember_8.png', 8, 3.0, {'not_flags': ['hale_walked_home']})}
SMOKE = {'smithy': {'restored': ['forge'], 'flags': ['hale_walked_home']}}
SMOKE_STRIP = ('fx/chimney_smoke_8.png', 8, 6.0, 32, 56)
MARKER = {'people': 82.0, 'notice_board': 108.0, 'waystone': 108.0}


def chimney_pot(zid: str, o: dict) -> tuple:
    """The top centre of a building picture's chimney, in texels: its first stack's pots as the house
    painter recorded them (kit.json `pots`; a front gable's stack stands in the slope, below the roof's
    back), else the picture's topmost opaque row."""
    if o.get('pots'):
        px, py = o['pots'][0]
        return o['foot'][0] + o['offset'][0] + px, o['foot'][1] + o['offset'][1] + py
    from PIL import Image
    import numpy as np
    a = np.array(Image.open(os.path.join(GAME, 'zones', zid, 'art', o['png'])).convert('RGBA'))[..., 3] > 0
    ys, xs = np.nonzero(a)
    top = ys.min()
    cx = (xs[ys == top].min() + xs[ys == top].max() + 1) / 2.0
    return o['foot'][0] + o['offset'][0] + cx, o['foot'][1] + o['offset'][1] + top


# kinds that lie flat on the ground and have no solid: people walk over them, so they are drawn on the
# ground's side of everyone (over the cast shadows at -9) instead of being y-sorted by their far edge
FLAT = {'beds', 'beds_dug', 'debris'}
# things people read whose only solid was the 5 px post of their talk area, 50 px narrower than what is drawn
THING_BASE = {'notice_board', 'waystone'}
# kinds drawn as part of something else, which sort where the kit put them: a building's damage overlay one
# texel in front of its building, the forge's fire in its mouth, a cast shadow and smoke on their own layers
SORTS_WITH_OWNER = {'building', 'damage', 'glow', 'shadow', 'smoke'}


def solids(plan: dict, kit: dict) -> dict:
    """Each solid object's rectangle and height class: id -> ([x, y, w, h] in world px, low).
    The plan's box (kit.json `solid`) stands unless the kit library knows the picture better
    (tools/gen_physics.py): an approved woodland picture takes that picture's box, and a box the library
    reviewed against the art (audit.overrides "collision") replaces the plan's. Low: the picture stands
    under 64 texels, so an arrow flies over it, unless its record says it stops shots all the same."""
    zid = plan['id']
    sprite = {}
    for k, dr in enumerate(plan.get('art', {}).get('dressing', [])):
        if dr.get('sprite', '').startswith('woodland/'):
            sprite[dr.get('id', '%s_%d' % (dr['kind'], k))] = 'woodland_' + dr['sprite'].split('/', 1)[1]
    out = {}
    for o in kit['objects']:
        if not o.get('solid') or o['kind'] == 'building':
            continue
        rect, piece = list(o['solid']), None
        fx, fy = o['foot'][0] / DENSITY, o['foot'][1] / DENSITY
        if o['id'] in sprite:
            piece = PH.pieces().get(sprite[o['id']])
        else:
            lib = PH.source_piece(zid, o['id'])
            piece = lib if lib is not None and PH.reviewed(lib) else None
        if piece is not None and PH.box(piece) is not None:
            bx, by, bw, bh = PH.box(piece)
            rect = [round(fx + bx, 4), round(fy + by, 4), bw, bh]
        stands = PH.rise(os.path.join(GAME, 'zones', zid, 'art', o['png']), -o['offset'][1]) if o.get('png') else PH.LOW_RISE
        # the record that knows this picture has the last word on shots (the stone rubble stops them)
        out[o['id']] = (rect, PH.is_low(stands, piece if piece is not None else PH.source_piece(zid, o['id'])))
    return out


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
    boxes = solids(plan, kit)
    for o in kit['objects']:
        if o['id'] in boxes and not o.get('cond'):
            s.solid('Solid_' + o['id'], 'Walls', *boxes[o['id']])
        elif o['kind'] in THING_BASE and o.get('png') and not o.get('cond'):
            # a board or a stone people read: its talk area's post (5 px) stands inside this, its drawn base
            s.solid('Solid_' + o['id'], 'Walls', PH.drawn_base(os.path.join(GAME, 'zones', zid, 'art', o['png']), o['foot'], o['offset']))

    # every drawn thing, y-sorted with the actors by its feet
    s.node('Props', 'Node2D', '.', {'y_sort_enabled': 'true'})
    for o in kit['objects']:
        parent = 'Props'
        if o.get('cond'):
            parent = s.wrap('Props', {'if': {**o['cond'], **TENDED.get(o['id'], {})}}, 'If_' + o['id'])
        if o.get('png') and o['id'] in BANKED:
            fx, fy = o['foot']
            ox, oy = o['offset']
            strip_png, n, fps, extra = BANKED[o['id']]
            bp = s.wrap('Props', {'if': {**(o.get('cond') or {}), **extra}}, 'If_%s_banked' % o['id'])
            s.node(pascal(o['id']) + 'Banked', 'Sprite2D', bp, {
                'position': vec(fx, fy), 'texture': 'ExtResource("%s")' % tex(strip_png), 'centered': 'false',
                'offset': vec(ox, oy), 'hframes': n, 'script': 'ExtResource("loopfx")', 'fps': fps})
        if o.get('png') and o['id'] in LOOPS:
            fx, fy = o['foot']
            ox, oy = o['offset']
            strip_png, n, fps = LOOPS[o['id']]
            s.node(pascal(o['id']), 'Sprite2D', parent, {
                'position': vec(fx, fy), 'texture': 'ExtResource("%s")' % tex(strip_png), 'centered': 'false',
                'offset': vec(ox, oy), 'hframes': n, 'script': 'ExtResource("loopfx")', 'fps': fps})
        elif o.get('png'):
            fx, fy = o['foot']
            ox, oy = o['offset']
            if o['kind'] not in SORTS_WITH_OWNER and o['kind'] not in FLAT:
                # the y-sort point on the drawn feet (tools/gen_physics.py); the texels stay where they are
                (fx, fy), (ox, oy) = PH.on_feet(os.path.join(GAME, 'zones', zid, 'art', o['png']), (fx, fy), (ox, oy))
            props = {'position': vec(fx, fy), 'texture': 'ExtResource("%s")' % tex(o['png']), 'centered': 'false',
                     'offset': vec(ox, oy)}
            if o['kind'] == 'shadow':
                props['z_index'] = -9      # the shadow of a prop that comes and goes: on the ground, under everything
            elif o['kind'] in FLAT and not o.get('solid'):
                props['z_index'] = -8      # lies flat and blocks nobody: walked over, never in front of anyone
            s.node(pascal(o['id']), 'Sprite2D', parent, props)
        if o['id'] in SMOKE and o.get('png'):
            px, py = chimney_pot(zid, o)
            sp = s.wrap('Props', {'if': SMOKE[o['id']]}, 'If_%s_smoke' % o['id'])
            strip_png, n, fps, w, h = SMOKE_STRIP
            s.node(pascal(o['id']) + 'Smoke', 'Sprite2D', sp, {
                'position': vec(px, py), 'texture': 'ExtResource("%s")' % tex(strip_png), 'centered': 'false',
                'offset': vec(-w // 2, -h), 'hframes': n, 'script': 'ExtResource("loopfx")', 'fps': fps,
                'z_index': 1})
        if o['id'] in boxes and o.get('cond'):
            s.solid(pascal(o['id']) + 'Body', parent, *boxes[o['id']])

    # actors: people, things, restore sites and camps (as the blockout, with the cast where it is drawn)
    s.node('Actors', 'Node2D', '.', {'y_sort_enabled': 'true'})
    cast_ext = {}
    for kind in ('people', 'things'):
        for p in plan.get(kind, []):
            parent = s.wrap('Actors', p, 'If_' + p['id'])
            x, y = p['at']
            name = pascal(p['id'])
            # a thing with "rest" is a place to rest (world/rest_spot.gd): full hearts and a save, for nothing
            props = {'position': vec(t(x), t(y)), 'script': 'ExtResource("%s")' % ('rest' if p.get('rest') else 'talk'),
                     'speaker_id': '"%s"' % p['speaker'],
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
                    s.node('Body', 'AnimatedSprite2D', path, {'script': 'ExtResource("villager")', 'character': '"%s"' % cid,
                                                              'facing_at_rest': '"%s"' % p.get('face', 'S'),
                                                              'work': 'true' if p.get('work') else 'false',
                                                              'centered': 'false', 'offset': vec(-80, -136)})
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
    ext += '[ext_resource type="Script" path="res://world/villager.gd" id="villager"]\n'
    ext += '[ext_resource type="Script" path="res://world/loop_fx.gd" id="loopfx"]\n'
    if any(p.get('rest') for p in plan.get('things', [])):
        ext += '[ext_resource type="Script" path="res://world/rest_spot.gd" id="rest"]\n'
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
    text = build(plan, kit)
    # the placement gate: no art reaches the zone without a passing review record
    # (scripts/review/gate.py; npm run review:asset -- <zone>/<name> --record)
    sys.path.insert(0, ROOT)
    from scripts.review.gate import refusals
    bad = refusals(zid, text=text)
    if bad:
        print('refused to place unreviewed or failing art:\n  ' + '\n  '.join(bad), file=sys.stderr)
        return 1
    with open(out, 'w') as f:
        f.write(text)
    print('wrote', os.path.relpath(out, GAME), len(kit['objects']), 'objects')
    return 0


if __name__ == '__main__':
    sys.exit(main())

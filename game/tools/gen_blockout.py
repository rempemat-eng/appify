#!/usr/bin/env python3
"""Blockout zone scenes from zone plans (docs/vision/vertical-slice.md).

    python3 game/tools/gen_blockout.py            # every plan in game/data/plans/
    python3 game/tools/gen_blockout.py crossroads

Reads game/data/plans/<id>.json (world px, the art/regions/*.json shape plus buildings, props, people,
things, restore_sites, camps, spawns, doors and raid_pads) and writes game/zones/<id>/<id>.tscn: flat
placeholder polygons for ground, buildings and props, merged walls for faces, buildings and the box's
edges, Interactables for people and things, RestoreSites, Camps of actors/enemy.tscn, Doors, Spawns and
raid pad markers (group "raid_pad"). An item with "if" is wrapped in a Conditional (world/conditional.gd)
so the one scene holds every stage. Positions are world px times DENSITY (3 texels). No art: replace the
scene with a kit-rendered base (tools/gen_zone.py) when Crossroads is drawn, keeping the node names.
"""
import json
import os
import sys

DENSITY = 3
GAME = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PLANS = os.path.join(GAME, 'data', 'plans')

EXT = [
    ('zone', 'Script', 'res://world/zone.gd'),
    ('cond', 'Script', 'res://world/conditional.gd'),
    ('talk', 'Script', 'res://world/interactable.gd'),
    ('site', 'Script', 'res://world/restore_site.gd'),
    ('door', 'Script', 'res://world/door.gd'),
    ('camp', 'Script', 'res://world/camp.gd'),
    ('enemy', 'PackedScene', 'res://actors/enemy.tscn'),
]


def t(v):
    return v * DENSITY


def colour(hexstr, alpha=1.0):
    h = hexstr.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    a = int(h[6:8], 16) / 255 if len(h) == 8 else alpha
    return 'Color(%.3f, %.3f, %.3f, %.3f)' % (r, g, b, a)


def vec(x, y):
    return 'Vector2(%g, %g)' % (x, y)


def poly(points):
    return 'PackedVector2Array(%s)' % ', '.join('%g, %g' % (t(x), t(y)) for x, y in points)


def rect_points(r):
    x, y, w, h = r
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def segment_quads(points, width):
    """A route as one quad per segment (axis-aligned or not), width in world px."""
    out = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dx, dy = x1 - x0, y1 - y0
        n = (dx * dx + dy * dy) ** 0.5 or 1
        ox, oy = -dy / n * width / 2, dx / n * width / 2
        out.append([[x0 + ox, y0 + oy], [x1 + ox, y1 + oy], [x1 - ox, y1 - oy], [x0 - ox, y0 - oy]])
    return out


class Scene:
    def __init__(self):
        self.subs = []
        self.nodes = []
        self.shapes = {}

    def rect_shape(self, w, h):
        key = ('r', w, h)
        if key not in self.shapes:
            sid = 's%d' % len(self.shapes)
            self.shapes[key] = sid
            self.subs.append('[sub_resource type="RectangleShape2D" id="%s"]\nsize = %s\n' % (sid, vec(w, h)))
        return self.shapes[key]

    def circle_shape(self, r):
        key = ('c', r)
        if key not in self.shapes:
            sid = 's%d' % len(self.shapes)
            self.shapes[key] = sid
            self.subs.append('[sub_resource type="CircleShape2D" id="%s"]\nradius = %g\n' % (sid, r))
        return self.shapes[key]

    def node(self, name, typ, parent, props=None, instance=None):
        head = '[node name="%s"' % name
        if typ:
            head += ' type="%s"' % typ
        if parent is not None:
            head += ' parent="%s"' % parent
        if instance:
            head += ' instance=ExtResource("%s")' % instance
        head += ']'
        lines = [head] + ['%s = %s' % (k, v) for k, v in (props or {}).items()]
        self.nodes.append('\n'.join(lines) + '\n')

    def polygon(self, name, parent, points, col, z=None):
        props = {'color': col, 'polygon': poly(points)}
        if z is not None:
            props['z_index'] = z
        self.node(name, 'Polygon2D', parent, props)

    def solid(self, name, parent, r):
        x, y, w, h = r
        self.node(name, 'StaticBody2D', parent, {'collision_mask': 0})
        self.node('Shape', 'CollisionShape2D', parent + '/' + name,
                  {'position': vec(t(x + w / 2), t(y + h / 2)), 'shape': 'SubResource("%s")' % self.rect_shape(t(w), t(h))})

    def wrap(self, parent, item, name):
        """A Conditional around an item with "if"; returns the parent path for its children."""
        if 'if' not in item:
            return parent
        self.node(name, 'Node2D', parent, {'script': 'ExtResource("cond")',
                                           'only_if': json.dumps(json.dumps(item['if'], separators=(',', ':')))})
        return parent + '/' + name

    def text(self, zone_name):
        ext = ''.join('[ext_resource type="%s" path="%s" id="%s"]\n' % (typ, path, i) for i, typ, path in EXT)
        return ('[gd_scene format=3]\n\n' + ext + '\n' + '\n'.join(self.subs) + '\n' + '\n'.join(self.nodes))


def pascal(s):
    return ''.join(p.capitalize() for p in s.replace('-', '_').split('_'))


def build(plan):
    s = Scene()
    zid = plan['id']
    bx, by, bw, bh = plan['box']
    s.node(pascal(zid), 'Node2D', None, {
        'y_sort_enabled': 'true', 'script': 'ExtResource("zone")', 'zone_id': '"%s"' % zid,
        'bounds': 'Rect2(0, 0, %g, %g)' % (t(bw), t(bh))})

    # ground: below everything, drawn in plan order
    s.node('Ground', 'Node2D', '.', {'z_index': -10})
    s.polygon('Void', 'Ground', rect_points(plan['box']), colour('#202020'))
    for tier in plan.get('tiers', []):
        s.polygon('Tier_' + tier['id'], 'Ground', tier['outline'], colour(tier.get('colour', '#808070')))
    for r in plan.get('routes', []):
        for i, q in enumerate(segment_quads(r['points'], r.get('width', 24))):
            s.polygon('Route_%s_%d' % (r['id'], i), 'Ground', q, colour('#b0a080', 0.55))
    for p in plan.get('places', []):
        if 'rect' in p:
            s.polygon('Place_' + p['id'], 'Ground', rect_points(p['rect']), colour(p.get('colour', '#a09880')))
    for st in plan.get('stairs', []):
        x, y = st['at']
        w = st.get('width', 32)
        s.polygon('Stair_' + st['id'], 'Ground', rect_points([x - w / 2, y - 8, w, 16]), colour('#c0b8a0'))
    for lot in plan.get('lots', []):
        s.polygon('Lot_' + lot['id'], 'Ground', rect_points(lot['rect']), colour('#3a3030'))
    for pad in plan.get('raid_pads', []):
        x, y = pad['at']
        z = pad.get('size', 20)
        alpha = 0.7 if pad.get('stage', 0) == 0 else 0.3
        s.polygon('Pad_' + pad['id'], 'Ground', rect_points([x - z / 2, y - z / 2, z, z]), colour('#d8d0b8', alpha))
    for f in plan.get('faces', []):
        s.polygon('Face_' + f['id'], 'Ground', rect_points(f['rect']), colour('#3c3a34'))
    for b in plan.get('buildings', []):
        s.polygon('Building_' + b['id'], 'Ground', rect_points(b['rect']), colour(b.get('colour', '#806850')))
        if 'door' in b:
            dx, dy = b['door']
            s.polygon('Door_' + b['id'], 'Ground', rect_points([dx - 6, dy - 4, 12, 4]), colour('#2a2018'))

    # walls: the box's edges, faces and buildings (a building's door is a mark, not a way in, for now)
    s.node('Walls', 'Node2D', '.')
    edge = 8
    for name, r in (('EdgeN', [bx, by - edge, bw, edge]), ('EdgeS', [bx, by + bh, bw, edge]),
                    ('EdgeW', [bx - edge, by, edge, bh]), ('EdgeE', [bx + bw, by, edge, bh])):
        s.solid(name, 'Walls', r)
    for f in plan.get('faces', []):
        s.solid('Face_' + f['id'], 'Walls', f['rect'])
    for b in plan.get('buildings', []):
        s.solid('Building_' + b['id'], 'Walls', b['rect'])

    # props: flat, above the ground, solid ones collide; conditional ones switch with the stage
    s.node('Props', 'Node2D', '.', {'z_index': -5})
    for p in plan.get('props', []):
        parent = s.wrap('Props', p, 'If_' + p['id'])
        if not p.get('colour', '').endswith('00') or len(p.get('colour', '')) != 9:
            s.polygon(pascal(p['id']), parent, rect_points(p['rect']), colour(p.get('colour', '#606060')))
        if p.get('solid'):
            s.solid(pascal(p['id']) + 'Body', parent, p['rect'])

    # actors: people, things, restore sites and camps, y-sorted with the player
    s.node('Actors', 'Node2D', '.', {'y_sort_enabled': 'true'})
    for kind in ('people', 'things'):
        for p in plan.get(kind, []):
            parent = s.wrap('Actors', p, 'If_' + p['id'])
            x, y = p['at']
            name = pascal(p['id'])
            props = {'position': vec(t(x), t(y)), 'script': 'ExtResource("talk")', 'speaker_id': '"%s"' % p['speaker']}
            if 'verb' in p:
                props['verb'] = '"%s"' % p['verb']
            s.node(name, 'Area2D', parent, props)
            path = parent + '/' + name
            s.node('Shape', 'CollisionShape2D', path, {'shape': 'SubResource("%s")' % s.circle_shape(p.get('radius', 30))})
            col = p.get('colour', '#a0a0a0')
            if not (len(col) == 9 and col.endswith('00')):
                if kind == 'people':
                    s.polygon('Body', path, [[-4, -16], [4, -16], [4, 0], [-4, 0]], colour(col))
                    s.node('Name', 'Label', path, {'offset_left': -40, 'offset_top': -72, 'offset_right': 40,
                                                    'offset_bottom': -52, 'text': '"%s"' % p.get('name', p['id']),
                                                    'horizontal_alignment': 1})
                else:
                    s.polygon('Body', path, [[-5, -10], [5, -10], [5, 0], [-5, 0]], colour(col))
                s.node('Post', 'StaticBody2D', path, {'collision_mask': 0})
                s.node('Shape', 'CollisionShape2D', path + '/Post', {'shape': 'SubResource("%s")' % s.circle_shape(5)})
    for site in plan.get('restore_sites', []):
        parent = s.wrap('Actors', site, 'If_' + site['id'])
        x, y = site['at']
        name = pascal(site['id'])
        s.node(name, 'Area2D', parent, {'position': vec(t(x), t(y)), 'script': 'ExtResource("site")',
                                         'restore_id': '"%s"' % site['restore'], 'verb': '"Restore"'})
        path = parent + '/' + name
        s.node('Shape', 'CollisionShape2D', path, {'shape': 'SubResource("%s")' % s.circle_shape(30)})
        s.polygon('Mark', path, [[-4, -1], [4, -1], [4, 1], [-4, 1]], colour('#f0d060'))
    for camp in plan.get('camps', []):
        name = pascal(camp['id']) + 'Camp'
        s.node(name, 'Node2D', 'Actors', {'script': 'ExtResource("camp")', 'camp_id': '"%s"' % camp['id']})
        for i, (x, y) in enumerate(camp['enemies']):
            props = {'position': vec(t(x), t(y))}
            if camp.get('boss'):
                props['scale'] = 'Vector2(2, 2)'
            s.node('Enemy%d' % (i + 1), None, 'Actors/' + name, props, instance='enemy')

    # labels for the blockout
    s.node('Labels', 'Node2D', '.', {'z_index': 5})
    for b in plan.get('buildings', []):
        x, y, w, h = b['rect']
        s.node('Label_' + b['id'], 'Label', 'Labels', {
            'offset_left': t(x), 'offset_top': t(y) + 6, 'offset_right': t(x + w), 'offset_bottom': t(y) + 30,
            'text': '"%s"' % b['name'], 'horizontal_alignment': 1, 'autowrap_mode': 3})

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
    return s.text(zid)


def main(ids):
    if not ids:
        ids = sorted(f[:-5] for f in os.listdir(PLANS) if f.endswith('.json'))
    for zid in ids:
        plan = json.load(open(os.path.join(PLANS, zid + '.json')))
        out_dir = os.path.join(GAME, 'zones', zid)
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, zid + '.tscn')
        with open(out, 'w') as f:
            f.write(build(plan))
        print('wrote', os.path.relpath(out, GAME))


if __name__ == '__main__':
    main(sys.argv[1:])

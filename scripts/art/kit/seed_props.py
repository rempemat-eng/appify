"""Seed the piece library with the woodland's and Crossroads' props and structures.

    python3 -m scripts.art.kit.seed_props [--force]

One piece per drawn design (`game/kit/pieces/<prop|structure>/<zone>_<kind>.json`), from what the
zones already know: the sprite's size, the foot and solid box in their kit.json, the stage
condition, the plan's restores. Everything a person must decide (the ground-rules role and its
relations, composition, story links not in the data) is listed in `audit.todo`; every seeded piece
is a `candidate` until it passes the library gate. An existing piece file is kept unless --force.
Refresh retains Claude-authored placement and
rendering decisions; source-backed geometry/function/story/gameplay are rebuilt. Unknown woodland
solid boxes remain null with a TODO, rather than being guessed from the kind. Attachments are
provenance on their owning design, never random picture variants.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

from PIL import Image

from scripts.art.kit.schema import PIECES, ROOT, errors, load_schema, piece_files

CELL_W = 8.0      # world px
D = 3             # texels per world px
def _base(kind: str) -> str:
    return re.sub(r'_\d+$', '', kind)


def _size(png: str):
    with Image.open(png) as im:
        bb = im.getbbox() if im.mode == 'RGBA' else None
        return im.size, bb


def _woodland_feet() -> dict:
    """Each woodland kind's foot in its picture (texels), from the base scene's sprite offsets."""
    with open(os.path.join(ROOT, 'game', 'zones', 'woodland', 'woodland_base.tscn')) as f:
        txt = f.read()
    out = {}
    for m in re.finditer(r'texture = ExtResource\("t_([a-z_]+)"\)\ncentered = false\noffset = Vector2\((-?[\d.]+), (-?[\d.]+)\)', txt):
        out.setdefault(m.group(1), (-float(m.group(2)), -float(m.group(3))))
    return out


def _read(path):
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)


def _scene(path):
    """Read the generated scene subset, retaining full node paths and resource references.

    This is metadata intake, not a general Godot parser. Only properties used below are read;
    positions in these scenes are translation-only and are expressed in art texels.
    """
    with open(os.path.join(ROOT, path)) as f:
        text = f.read()
    blocks = {}
    for m in re.finditer(r'^\[([^\n]+)\]\n(.*?)(?=^\[|\Z)', text, re.M | re.S):
        head, body = m.groups()
        attrs = dict(re.findall(r'(\w+)="([^"\n]*)"', head))
        props = dict(re.findall(r'^(\w+) = (.*)$', body, re.M))
        if head.startswith('node '):
            parent = attrs.get('parent', '')
            key = attrs['name'] if parent in ('', '.') else parent + '/' + attrs['name']
            blocks[key] = dict(attrs, props=props)
        elif head.startswith('ext_resource '):
            blocks['!' + attrs['id']] = dict(attrs, props=props)
        elif head.startswith('sub_resource '):
            blocks['@' + attrs['id']] = dict(attrs, props=props)
    return blocks


def _vector(value, default=(0.0, 0.0)):
    if value is None:
        return list(default)
    m = re.fullmatch(r'Vector2\(([-\d.e+]+), ([-\d.e+]+)\)', value)
    if not m:
        raise ValueError('unsupported vector: ' + value)
    return [float(v) for v in m.groups()]


def _snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def _interactions(scene):
    out = {}
    for path, node in scene.items():
        p = node['props']
        if node.get('type') != 'Area2D' or not ('speaker_id' in p or 'restore_id' in p):
            continue
        # Actors use local zero-origin wrappers; reject transformed wrappers rather than
        # silently interpreting a future scene's local coordinate as a global one.
        parent = node.get('parent', '')
        condition = {}
        while parent not in ('', '.'):
            pp = scene.get(parent, {}).get('props', {})
            if _vector(pp.get('position')) != [0.0, 0.0] or any(k in pp for k in ('scale', 'rotation', 'transform')):
                raise ValueError('transformed interaction parent: ' + parent)
            if 'only_if' in pp:
                inherited = json.loads(json.loads(pp['only_if']))
                for key, value in inherited.items():
                    if key in condition and condition[key] != value:
                        raise ValueError('conflicting interaction predicate: ' + path)
                    condition[key] = value
            parent = scene.get(parent, {}).get('parent', '')
        shape = scene.get(path + '/Shape', {}).get('props', {}).get('shape', '')
        match = re.fullmatch(r'SubResource\("([^"\n]+)"\)', shape)
        radius = scene.get('@' + match[1], {}).get('props', {}).get('radius') if match else None
        out[_snake(node['name'])] = dict(at=_vector(p.get('position')), verb=json.loads(p.get('verb', '"Talk"')),
            speaker=json.loads(p['speaker_id']) if 'speaker_id' in p else None,
            restore=json.loads(p['restore_id']) if 'restore_id' in p else None,
            radius=float(radius) if radius else None, path=path, condition=condition)
    return out


def _post_collision(scene, actor):
    p = scene.get(actor + '/Post/Shape', {}).get('props', {})
    match = re.fullmatch(r'SubResource\("([^"\n]+)"\)', p.get('shape', ''))
    if not match:
        return None
    shape = scene['@' + match[1]]
    if shape.get('type') == 'CircleShape2D':
        return {'shape': 'circle', 'radius': float(shape['props']['radius']) / D}
    return None


def footprint(rect):
    """Conservative intersected 8-world-px cells at a cell-aligned foot.

    The exact collision stays continuous. A one-texel post must not vanish through a half-area
    threshold. W4 must recompute at half/free snapped feet; these are reusable local cells,
    independent of the first source instance's old grid phase.
    """
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return []
    import math
    return [[cx, cy] for cy in range(math.floor(y / CELL_W), math.ceil((y + h) / CELL_W))
            for cx in range(math.floor(x / CELL_W), math.ceil((x + w) / CELL_W))]


def _source(zone, obj, part='body'):
    return {'zone': zone, 'object': obj['id'], 'part': part, 'condition': obj.get('cond')}


def _quest_refs(events):
    out = []
    for f in sorted(os.listdir(os.path.join(ROOT, 'game/data/quests'))):
        if not f.endswith('.json'):
            continue
        q = _read('game/data/quests/' + f)
        listened = {q.get('start', {}).get('on')} | {step.get('on') for step in q.get('steps', [])}
        if listened & events:
            out.append('res://data/quests/' + f)
    return out


def _existing(pid):
    for kind in ('prop', 'structure'):
        path = os.path.join(PIECES, kind, pid + '.json')
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    return None


def _enrich(authored, source):
    """Preserve authored optional fields; authoritative source scalars win on a shared key."""
    import copy
    if isinstance(authored, dict) and isinstance(source, dict):
        result = copy.deepcopy(authored)
        for key, value in source.items():
            result[key] = _enrich(result[key], value) if key in result else copy.deepcopy(value)
        return result
    if isinstance(authored, list) and isinstance(source, list):
        values = {json.dumps(v, sort_keys=True): copy.deepcopy(v) for v in authored + source}
        return [values[key] for key in sorted(values)]
    return copy.deepcopy(source)


def _source_variant_ids(zone):
    kit = _read('game/zones/' + zone + '/kit.json')
    return {os.path.splitext((o[1] + '.png') if isinstance(o, list) else (o.get('png') or ''))[0]
            for o in kit['objects']}


def _assemble(zone, base, objects, collision, pid=None, interactions=(), building=None, plan=None):
    """One reusable design per compatible collision, with per-variant feet.

    Existing Claude-authored placement/rendering decisions survive refresh. New designs retain
    TODOs rather than acquiring guessed roles, relations, owners, interactions or shadows.
    """
    import copy
    import math
    pid = pid or zone + '_' + base
    old = _existing(pid)
    variants = []
    sizes = []
    for obj in sorted(objects, key=lambda o: o.get('png') or o['id']):
        if not obj.get('png'):
            continue
        png_res = obj.get('png_res') or 'res://zones/' + zone + '/art/' + obj['png']
        path = os.path.join(ROOT, 'game', png_res[len('res://'):])
        size, _ = _size(path)
        sizes.append(size)
        variants.append({'id': os.path.splitext(obj['png'])[0], 'weight': 1.0,
                         'png': png_res, 'foot': obj['anchor']})
    variants = list({v['id']: v for v in variants}.values())
    if old:
        prior = {v['id']: v for v in old.get('variants', [])}
        for v in variants:
            # Weight/note are authored; source supplies the current texture and exact foot.
            if v['id'] in prior:
                extra = {k: val for k, val in prior[v['id']].items() if k not in ('id', 'png', 'foot')}
                v.update(extra)
        known = _source_variant_ids(zone) | {v['id'] for v in variants}
        variants += [copy.deepcopy(v) for v in old.get('variants', []) if v['id'] not in known]
    w, h = (max(s[0] for s in sizes), max(s[1] for s in sizes)) if sizes else (0, 0)
    g = {'size_px': [w, h], 'size_cells': [math.ceil(w / D / CELL_W), math.ceil(h / D / CELL_W)],
         'z_sort': 'foot', 'collision': collision}
    if variants:
        g['foot'] = variants[0]['foot']
    todo_circle = bool(collision and collision['shape'] == 'circle')
    if collision and collision['shape'] == 'rect':
        g['footprint'] = footprint(collision['rect'])
    elif collision and collision['shape'] == 'circle':
        r = collision['radius']
        g['footprint'] = footprint([-r, -r, 2 * r, 2 * r])
    else:
        g['footprint'] = []
    todo = ['composition role and clearance', 'review size-guide class and Eastward comparison before the library gate']
    if not old or not old.get('placement', {}).get('role'):
        todo.append('placement.role, requires and forbids (Claude design decision; ground-rules.md 6)')
    if collision is None:
        todo.append('object-local collision is unknown: woodland scene has only a merged terrain walk mask; Claude must author a solid box (no guessed tree/body collision)')
    if g['footprint']:
        todo.append('footprint is conservative positive-area coverage at a cell-aligned foot; W4 must derive exact runtime blocking from collision at the placed foot')
    if todo_circle:
        todo.append('source has a circle post; prop-scene generator currently emits rectangles only (W4/runtime support needed before placement)')
    if not variants:
        todo.append('procedural attachment has no standalone sprite; retain it with its source owner, not as a placeable design')
    p = {'schema': 'napattack.piece/1', 'id': pid, 'name': base.replace('_', ' ').capitalize(),
         'kind': 'structure' if building else 'prop', 'biomes': ['woodland' if zone == 'woodland' else 'village'],
         'version': old.get('version', 1) if old else 1, 'variants': variants,
         'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': None,
                      'note': 'Source metadata only; seeded designs still require the library gate and Matt approval.'},
         'geometry': g, 'placement': copy.deepcopy(old.get('placement', {})) if old else {},
         'rendering': copy.deepcopy(old.get('rendering', {})) if old else {},
         'function': {}, 'story': {'owner': old.get('story', {}).get('owner') if old else None},
         'gameplay': {}, 'audit': {'size_class': old.get('audit', {}).get('size_class') if old else None,
             'eastward_ref': old.get('audit', {}).get('eastward_ref') if old else None,
             'seeded_from': 'game/zones/' + zone + '/kit.json', 'sources': [_source(zone, o) for o in sorted(objects, key=lambda o: o['id'])], 'todo': todo}}
    if collision is not None:
        p['gameplay']['blocks_move'] = collision['shape'] != 'none'
        # Source StaticBody2D walls default to layer 1, tested by both actor and projectile masks.
        p['gameplay']['blocks_shots'] = collision['shape'] != 'none'
    conds = {json.dumps(o.get('cond'), sort_keys=True) for o in objects}
    if len(conds) == 1 and objects[0].get('cond'):
        p['story']['gating'] = {'if': objects[0]['cond']}
    events = set()
    points = []
    triggers = []
    for it in interactions:
        # Interaction offsets/radii are art texels; collision rects above remain world px.
        anchor = objects[0].get('at', [0, 0])
        point = {'id': it['id'], 'at': [round(it['at'][i] - anchor[i] * D, 4) for i in (0, 1)], 'verb': it['verb']}
        if it.get('condition'):
            point['if'] = it['condition']
        if it.get('radius') is not None:
            point['radius'] = it['radius']
        points.append(point)
        if it.get('speaker'):
            # Dialogue is stored by speaker in files whose filename need not match its id.
            ref = _dialogue_ref(it['speaker'], zone)
            if ref:
                triggers.append({'type': 'dialogue', 'ref': ref})
            else:
                todo.append('dialogue speaker ' + it['speaker'] + ' has no data record')
            events.add('talk:' + it['speaker'])
        if it.get('restore'):
            rid = it['restore']
            ref = 'res://data/plans/crossroads.json#/restores/' + str(next(i for i, r in enumerate(plan['restores']) if r['id'] == rid))
            triggers.append({'type': 'restore', 'ref': ref})
            p['function'].setdefault('saves', []).append('village.restored.' + rid)
            p['function'].setdefault('costs', []).append(ref + '/cost')
            p['story']['milestone'] = rid
            events.add('restore:' + rid)
    if points:
        g['interaction_points'] = points
        verb = interactions[0]['verb'].lower()
        p['function']['interact'] = {'verb': 'use' if verb == 'touch' else verb, 'triggers': triggers}
    if building:
        door = building.get('door')
        if door:
            at = objects[0]['at']
            g['door_cells'] = [[int((door[0] - at[0]) // CELL_W), int((door[1] - at[1]) // CELL_W)]]
            todo.append('door_cells mark the authored doorway, not a working interior/scene transition')
        rid = building.get('restore')
        if rid:
            p['story']['milestone'] = rid
            events.add('restore:' + rid)
            p['function'].setdefault('saves', []).append('village.restored.' + rid)
    quests = _quest_refs(events)
    if quests:
        p['story']['quests'] = quests
    dialogue = [t['ref'] for t in triggers if t['type'] == 'dialogue']
    if dialogue:
        p['story']['dialogue'] = dialogue
    for key in ('saves', 'costs'):
        if key in p['function']:
            p['function'][key] = sorted(set(p['function'][key]))
    if old:
        p['function'] = _enrich(old.get('function', {}), p['function'])
        p['story'] = _enrich(old.get('story', {}), p['story'])
        p['gameplay'] = _enrich(old.get('gameplay', {}), p['gameplay'])
        if collision is None:
            # An old heuristic is not evidence for an unknown woodland solid box.
            p['gameplay'].pop('blocks_move', None)
            p['gameplay'].pop('blocks_shots', None)
        for key in ('overhang', 'height_px'):
            if key in old.get('geometry', {}):
                g[key] = copy.deepcopy(old['geometry'][key])
        source_points = {point['id'] for point in points}
        extra_points = [copy.deepcopy(point) for point in old.get('geometry', {}).get('interaction_points', [])
                        if point['id'] not in source_points]
        if extra_points:
            g['interaction_points'] = points + extra_points
        for key, value in old.get('audit', {}).items():
            if key not in ('sources', 'todo', 'seeded_from'):
                p['audit'][key] = copy.deepcopy(value)
        # Keep a reviewer's open notes, but retire the replaced generator's known heuristic note.
        p['audit']['todo'] += [t for t in old.get('audit', {}).get('todo', [])
                               if 'first guesses by kind' not in t]
    return p


def _dialogue_ref(speaker, zone):
    files = sorted(os.listdir(os.path.join(ROOT, 'game/data/dialogue')))
    preferred = zone + '.json'
    files.sort(key=lambda f: (f != preferred, f))
    for f in files:
        if f.endswith('.json'):
            d = _read('game/data/dialogue/' + f)
            if isinstance(d, dict) and speaker in d:
                key = speaker.replace('~', '~0').replace('/', '~1')
                return 'res://data/dialogue/' + f + '#/' + key
    return None


def seed() -> list:
    out = []
    wk = _read('game/zones/woodland/kit.json')
    if wk.get('density') != D:
        raise ValueError('woodland source density differs from the pinned density 3 contract')
    feet = _woodland_feet()
    groups = {}
    for oid, kind, x, y, w, h in wk['objects']:
        # kit x/y are the picture's top left in world px, NOT its foot.
        png = os.path.join(ROOT, 'game/zones/woodland/art', kind + '.png')
        size, _ = _size(png)
        anchor = list(feet.get(kind, (size[0] / 2, size[1])))
        obj = {'id': oid, 'png': kind + '.png', 'anchor': anchor,
               'at': [x + anchor[0] / D, y + anchor[1] / D]}
        groups.setdefault(kind, []).append(obj)
    for kind, objects in groups.items():
        out.append(_assemble('woodland', kind, objects, None))
    # The woodland's actual quest sign lives in the gameplay scene, outside kit.json.
    woodland_scene = _scene('game/zones/woodland/woodland.tscn')
    sign = _interactions(woodland_scene)['stone_sign']
    sprite = woodland_scene[sign['path'] + '/Sprite']['props']
    texture_id = re.fullmatch(r'ExtResource\("([^"\n]+)"\)', sprite['texture'])[1]
    png_res = woodland_scene['!' + texture_id]['path']
    obj = {'id': 'StoneSign', 'png': os.path.basename(png_res), 'png_res': png_res,
           'anchor': [-v for v in _vector(sprite['offset'])], 'at': [v / D for v in sign['at']]}
    piece = _assemble('woodland', 'stone_sign', [obj], _post_collision(woodland_scene, sign['path']),
                      interactions=[dict(sign, id='stone_sign')])
    piece['audit']['seeded_from'] = 'game/zones/woodland/woodland.tscn'
    piece['audit']['todo'].append('placeholder artwork: replace through the library gate before use')
    out.append(piece)
    ck = _read('game/zones/crossroads/kit.json')
    if ck.get('density') != D:
        raise ValueError('crossroads source density differs from the pinned density 3 contract')
    plan = _read('game/data/plans/crossroads.json')
    scene = _scene('game/zones/crossroads/crossroads.tscn')
    interactions = _interactions(scene)
    buildings = {b['id']: b for b in plan['buildings']}
    # These two scene interaction ids differ from their actual drawn design ids. This explicit
    # crosswalk is reviewed against plan.things and their exact scene locations, never proximity.
    bindings = {'hut': ['hut_bed'], 'lantern_dark': ['shard_lantern'], 'lantern_lit': ['shard_lantern']}
    by_object = {}
    groups = {}
    attachments = []
    for obj in ck['objects']:
        obj = dict(obj)
        if obj.get('of') or obj['kind'] in ('boards', 'glow'):
            attachments.append(obj)
            continue
        base = _base(os.path.splitext(obj.get('png') or obj['id'])[0])
        obj['at'] = [v / D for v in (obj.get('foot') or (0, 0))]
        obj['anchor'] = [-v for v in (obj.get('offset') or (0, 0))]
        solid = obj.get('solid')
        col = {'shape': 'rect', 'rect': [round(solid[0] - obj['at'][0], 4), round(solid[1] - obj['at'][1], 4), *solid[2:]]} if solid else {'shape': 'none'}
        it = interactions.get(obj['id'])
        if it and col['shape'] == 'none':
            col = _post_collision(scene, it['path']) or col
        sig = json.dumps(col, sort_keys=True)
        groups.setdefault(base, {}).setdefault(sig, []).append(obj)
    for base, shapes in groups.items():
        shape_keys = sorted(shapes, key=lambda sig: (json.loads(sig)['shape'] == 'none', sig))
        for n, sig in enumerate(shape_keys):
            objects = shapes[sig]
            collision = json.loads(sig)
            pid = 'crossroads_' + base
            if n:
                suffix = 'nonblocking' if collision['shape'] == 'none' else 'shape_' + str(n + 1)
                pid += '_' + suffix
            source = objects[0]
            its = []
            ids = [source['id']] + bindings.get(source['id'], [])
            building = buildings.get(source['id'])
            if building and building.get('restore'):
                ids += [key for key, v in interactions.items() if v.get('restore') == building['restore']]
            for key in ids:
                if key in interactions:
                    its.append(dict(interactions[key], id=key))
            p = _assemble('crossroads', base, objects, collision, pid, its, building, plan)
            if source['kind'] in ('smoke', 'shadow'):
                p['geometry']['z_sort'] = 'ground' if source['kind'] == 'shadow' else 'above'
                p['audit']['todo'].append('source effect: preserve its authored condition and attach lifecycle/reduced-motion policy before use')
            for o in objects:
                by_object[o['id']] = p
            out.append(p)
    for obj in attachments:
        owner = obj.get('of')
        if owner is None:
            # boards and forge fire are owned by the building sharing their exact restore id.
            cond = obj.get('cond') or {}
            rids = cond.get('restored', []) + cond.get('not_restored', [])
            matches = [b['id'] for b in buildings.values() if b.get('restore') in rids]
            if len(matches) != 1:
                raise ValueError('no unambiguous source owner for ' + obj['id'])
            owner = matches[0]
        if owner not in by_object:
            raise ValueError('missing attachment owner ' + owner)
        part = {'damage': 'overlay', 'shadow': 'shadow', 'glow': 'effect', 'boards': 'procedural'}[obj['kind']]
        by_object[owner]['audit']['sources'].append(_source('crossroads', obj, part))
        by_object[owner]['audit']['todo'].append('retain ' + part + ' ' + obj['id'] + ' from source scene with its own condition and offset; not a standalone random variant')
    for p in out:
        p['audit']['sources'].sort(key=lambda item: (item['zone'], item['object']))
        p['audit']['todo'] = sorted(set(p['audit']['todo']))
    return sorted(out, key=lambda p: p['id'])


def source_index(pieces):
    """Every kit object id maps exactly once, including attachments with no standalone PNG."""
    out = {}
    if len({p['id'] for p in pieces}) != len(pieces):
        raise ValueError('duplicate generated piece id')
    for p in pieces:
        for source in p['audit'].get('sources', []):
            key = source['zone'], source['object']
            if key in out:
                raise ValueError('duplicate source object: ' + repr(key))
            out[key] = p['id']
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--force', action='store_true', help='refresh source fields; retain existing placement/rendering design decisions')
    a = ap.parse_args(argv)
    schema = load_schema()
    before = {}
    for path in piece_files(PIECES):
        with open(path, 'rb') as f:
            before[path] = f.read()
    pieces = seed()
    source_index(pieces)
    # Validate the whole batch before any file is replaced.
    for p in pieces:
        e = errors(p, schema)
        existing = _existing(p['id'])
        if a.force and existing and existing.get('approval', {}).get('state') in ('approved', 'gated', 'rejected', 'retired') and existing != p:
            e.append('refusing to overwrite reviewed piece without a new review')
        if e:
            print(p['id'], e)
            return 1
    for p in pieces:
        path = os.path.join(PIECES, p['kind'], p['id'] + '.json')
        if os.path.exists(path):
            with open(path, 'rb') as f:
                current = f.read()
        else:
            current = None
        if current != before.get(path):
            print('source changed while seeding: ' + path)
            return 1
    n = 0
    for p in pieces:
        d = os.path.join(PIECES, p['kind'])
        path = os.path.join(d, p['id'] + '.json')
        if os.path.exists(path) and not a.force:
            continue
        old = _existing(p['id'])
        if old == p:
            continue
        if old:
            if old.get('approval', {}).get('state') in ('approved', 'gated', 'rejected', 'retired'):
                raise ValueError('refusing to overwrite reviewed piece without a new review: ' + p['id'])
            compare = dict(p, version=old.get('version', 1))
            p['version'] = old.get('version', 1) + (compare != old)
        os.makedirs(d, exist_ok=True)
        # The directory and filenames stay stable; atomically replace each complete JSON file.
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=d, prefix='.' + p['id'], suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(p, f, indent=1)
                f.write('\n')
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        n += 1
    print('seeded %d pieces; %d source objects mapped' % (n, len(source_index(pieces))))
    return 0


if __name__ == '__main__':
    sys.exit(main())

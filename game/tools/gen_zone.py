"""Turn a kit zone into a Godot scene: game/zones/<zone>/<zone>_base.tscn.

    # 1. render the zone with the art kit at density 3 and copy its pictures and boxes in
    python3 game/tools/gen_zone.py woodland --render /path/to/kit-checkout --walk /path/to/kit-checkout/lib/zone-maps.ts
    # 2. later, rebuild the scene only (no render) from what step 1 stored in the zone folder
    python3 game/tools/gen_zone.py woodland

A kit zone is three things, all kept in game/zones/<zone>/ so the scene can be rebuilt without the kit:
    art/*.png    ground.png, one picture per object kind, flow.png (the moving water's frames), at density 3
    kit.json     the kit's export (scripts/art/native/zone.py): density, each object's [id, kind, x, y, w, h]
                 in world px, and the flow box and its column count
    walk.txt     the walk mask, one row per 4 world px cell row, '.' walkable and '#' blocked

The scene it writes holds the ground and the water below everything, the objects in a y-sorted node with
their feet as origins (so actors added to the zone's y-sorted Actors node sort against them), a
StaticBody2D whose rectangles are the blocked cells of the walk mask merged into runs, and a Marker2D per
named stand. One world px is DENSITY texels (Godot units). The playable scene (<zone>.tscn) instances this
base and adds doors, people, camps and quests by hand, so regenerating never touches authored work.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
CELL = 4  # world px per walk-mask cell


def unrle(s: str) -> str:
    return ''.join(c * (int(n) if n else 1) for n, c in re.findall(r'(\d*)([.#])', s))


def walk_from_zone_maps(path: str, zone: str):
    """Rows and stands of one zone from the app's lib/zone-maps.ts."""
    src = open(path).read()
    block = src[src.index(f'  {zone}: {{\n    objects'):]
    block = block[:block.index('\n  },')]
    w = block[block.index('walk: [') + 7: block.index('].map(unrle)')]
    rows = [unrle(s) for s in re.findall(r"'([^']*)'", w)]
    stands = {}
    m = re.search(r'stands: \{([^}]*)\}', block)
    if m:
        for name, x, y in re.findall(r'(\w+): \[([-\d.]+), ([-\d.]+)\]', m.group(1)):
            stands[name] = [float(x), float(y)]
    return rows, stands


def render(kit: str, zone: str, density: float, out: str) -> dict:
    """Run the kit's zone export and copy its pictures into out/art."""
    r = subprocess.run([sys.executable, '-m', 'scripts.art.native.zone', '--zone', zone, '--density', f'{density:g}'],
                       cwd=kit, check=True, capture_output=True, text=True)
    doc = json.loads(r.stdout.strip().split('\n')[-1])
    src = os.path.join(kit, 'assets', 'zones', zone, '2x')  # the kit's folder name, whatever the density
    art = os.path.join(out, 'art')
    os.makedirs(art, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if f.endswith('.png'):
            shutil.copy(os.path.join(src, f), os.path.join(art, f))
    return doc


def merge_blocked(rows):
    """Blocked runs per row, extended down while the same run repeats: (x0, y0, x1, y1) in cells."""
    width = max(len(r) for r in rows)
    rects, open_ = [], {}
    for y, row in enumerate(rows + ['.' * width]):
        runs, x = set(), 0
        while x < len(row):
            if row[x] == '#':
                x0 = x
                while x < len(row) and row[x] == '#':
                    x += 1
                runs.add((x0, x))
            else:
                x += 1
        for k in list(open_):
            if k not in runs:
                rects.append((k[0], open_.pop(k), k[1], y))
        for k in sorted(runs):
            open_.setdefault(k, y)
    return sorted(rects, key=lambda r: (r[1], r[0]))


def png_size(path: str):
    with open(path, 'rb') as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')


def num(v: float) -> str:
    return f'{round(v, 3):g}'


def write_scene(zone: str, out: str) -> dict:
    kit = json.load(open(os.path.join(out, 'kit.json')))
    D = float(kit['density'])
    rows = [r for r in open(os.path.join(out, 'walk.txt')).read().split('\n') if r]
    stands = kit.get('stands', {})
    res = f'res://zones/{zone}'
    ext = [f'[ext_resource type="Texture2D" path="{res}/art/ground.png" id="ground"]']
    if kit.get('flow'):
        ext.append(f'[ext_resource type="Texture2D" path="{res}/art/flow.png" id="flow"]')
        ext.append('[ext_resource type="Script" path="res://world/flow_anim.gd" id="flow_anim"]')
    kinds = sorted({o[1] for o in kit['objects']})
    for k in kinds:
        ext.append(f'[ext_resource type="Texture2D" path="{res}/art/{k}.png" id="t_{k}"]')
    nodes = [f'[node name="{zone.capitalize()}Base" type="Node2D"]\ny_sort_enabled = true',
             '[node name="Ground" type="Sprite2D" parent="."]\nz_index = -10\ntexture = ExtResource("ground")\ncentered = false']
    if kit.get('flow'):
        bx, by, bw, bh = kit['flow']['rect']
        cols = int(kit['flow']['cols'])
        fw, fh = png_size(os.path.join(out, 'art', 'flow.png'))
        vframes = max(1, round(fh / (bh * D)))
        nodes.append(f'[node name="Water" type="Sprite2D" parent="."]\nz_index = -9\nposition = Vector2({num(bx * D)}, {num(by * D)})\n'
                     f'texture = ExtResource("flow")\ncentered = false\nhframes = {cols}\nvframes = {vframes}\nscript = ExtResource("flow_anim")')
    nodes.append('[node name="Objects" type="Node2D" parent="."]\ny_sort_enabled = true')
    for oid, kind, x, y, w, h in kit['objects']:
        fx, fy = round((x + w / 2) * D), round((y + h) * D)
        tw, th = png_size(os.path.join(out, 'art', f'{kind}.png'))
        nodes.append(f'[node name="{oid}" type="Sprite2D" parent="Objects"]\nposition = Vector2({fx}, {fy})\n'
                     f'texture = ExtResource("t_{kind}")\ncentered = false\noffset = Vector2({-(tw // 2)}, {-th})')
    subs = []
    rects = merge_blocked(rows)
    nodes.append('[node name="Walls" type="StaticBody2D" parent="."]\ncollision_mask = 0')
    c = CELL * D
    for i, (x0, y0, x1, y1) in enumerate(rects):
        w, h = (x1 - x0) * c, (y1 - y0) * c
        subs.append(f'[sub_resource type="RectangleShape2D" id="r{i}"]\nsize = Vector2({num(w)}, {num(h)})')
        nodes.append(f'[node name="c{i}" type="CollisionShape2D" parent="Walls"]\n'
                     f'position = Vector2({num(x0 * c + w / 2)}, {num(y0 * c + h / 2)})\nshape = SubResource("r{i}")')
    nodes.append('[node name="Stands" type="Node2D" parent="."]')
    for name, (sx, sy) in sorted(stands.items()):
        nodes.append(f'[node name="{name}" type="Marker2D" parent="Stands"]\nposition = Vector2({num(sx * D)}, {num(sy * D)})')
    gw, gh = png_size(os.path.join(out, 'art', 'ground.png'))
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]'
    text = '\n\n'.join([head, '\n'.join(ext)] + subs + nodes) + '\n'
    # the placement gate: no art reaches the zone without a passing review record
    # (scripts/review/gate.py; npm run review:asset -- <zone>/<name> --record)
    sys.path.insert(0, os.path.dirname(GAME))
    from scripts.review.gate import refusals
    bad = refusals(zone, text=text)
    if bad:
        raise SystemExit('refused to place unreviewed or failing art:\n  ' + '\n  '.join(bad))
    open(os.path.join(out, f'{zone}_base.tscn'), 'w').write(text)
    return dict(zone=zone, objects=len(kit['objects']), wall_rects=len(rects), size=[gw, gh], density=D)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('zone')
    ap.add_argument('--render', metavar='KIT', help='a checkout of the art kit to render the zone from')
    ap.add_argument('--density', type=float, default=3.0)
    ap.add_argument('--walk', metavar='ZONE_MAPS_TS', help="the kit checkout's lib/zone-maps.ts (walk rows and stands)")
    a = ap.parse_args(argv)
    out = os.path.join(GAME, 'zones', a.zone)
    os.makedirs(out, exist_ok=True)
    if a.render:
        doc = render(a.render, a.zone, a.density, out)
        old = {}
        if os.path.exists(os.path.join(out, 'kit.json')):
            old = json.load(open(os.path.join(out, 'kit.json')))
        doc['stands'] = old.get('stands', {})
        json.dump(doc, open(os.path.join(out, 'kit.json'), 'w'), indent=1)
    if a.walk:
        rows, stands = walk_from_zone_maps(a.walk, a.zone)
        open(os.path.join(out, 'walk.txt'), 'w').write('\n'.join(rows) + '\n')
        kit = json.load(open(os.path.join(out, 'kit.json')))
        kit['stands'] = stands
        json.dump(kit, open(os.path.join(out, 'kit.json'), 'w'), indent=1)
    print(json.dumps(write_scene(a.zone, out)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

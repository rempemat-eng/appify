"""Rebuild W7's 1:1 Python reference images; --check refuses stale decoded pixels or metadata.

Run from the repository root: python3 game/test/fixtures/kit/generate.py [--check]
These fixtures exercise the live terrain renderer, including shadows and edge dressing.
They are not baked ground or pictures captured from Godot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.art.kit.build import Kit  # noqa: E402
from scripts.art.kit import compose  # noqa: E402
from scripts.art.native.palette import to_rgba  # noqa: E402

HERE = Path(__file__).resolve().parent


def render(plan, kit, *, shadows=True, dressing=True):
    legend = {symbol: kit.ids[name] for symbol, name in plan['legend'].items()}
    cells = np.array([[legend[symbol] for symbol in row] for row in plan['rows']], dtype=np.int32)
    tiers = np.array([[int(c) for c in row] for row in plan['tiers']]) if plan.get('tiers') else None
    return Image.fromarray(to_rgba(compose.render(cells, kit, dressing=dressing,
                                                pieces=plan.get('pieces') if shadows else None, tiers=tiers)), 'RGBA')


def expected():
    kit = Kit()
    cases = (
        ('kitlab', ROOT / 'game/kit/zones/kitlab.json', 'res://zones/kitlab/kitlab.tscn'),
        ('three_materials', HERE / 'three_materials.json', 'res://test/fixtures/kit/three_materials.json'),
    )
    images, records = {}, []
    for name, path, source in cases:
        plan = json.loads(path.read_text())
        image = render(plan, kit)
        images[name + '.png'] = image
        records.append({'id': name, 'source': source, 'plan': path.relative_to(ROOT).as_posix(), 'expected': name + '.png',
                        'size': list(image.size),
                        'plan_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'rgba_sha256': hashlib.sha256(image.tobytes()).hexdigest()})
    # A real hash-coordinate mutation: both ground profiles and dressing look up the wrong
    # cell edge. The normal Godot renderer must reject this independently rendered image.
    normal_profile = compose.profile
    with patch.object(compose, 'profile', lambda a, b, c, m, n=3: normal_profile(a + 1, b, c, m, n)):
        images['three_materials_shifted_profile.png'] = render(json.loads(cases[1][1].read_text()), kit)
    if images['three_materials.png'].tobytes() == images['three_materials_shifted_profile.png'].tobytes():
        raise ValueError('negative profile fixture must differ from the real reference')
    lab = json.loads(cases[0][1].read_text())
    rgba = np.asarray(images['kitlab.png'])
    features = {feature: int(np.any(rgba != np.asarray(render(lab, kit, **{feature: False})), axis=2).sum())
                for feature in ('shadows', 'dressing')}
    if not all(features.values()):
        raise ValueError('the kit lab must visibly exercise both shadows and dressing')
    inputs = {'scripts/art/kit/' + name for name in ('compose.py', 'edges.py', 'dressing.py', 'build.py')}
    inputs.update(('scripts/art/native/palette.py', 'scripts/art/house_palette.py',
                   'art/house-palette.json', 'scripts/art/native/accents.json',
                   'game/test/fixtures/kit/generate.py',
                   'game/kit/terrain/manifest.json', 'game/kit/props/index.json'))
    man = kit.man
    textures = [man['lut'], man['palette'], man.get('noise', 'noise.png')]
    textures += [m['fill'] for m in man['materials']] + [t['png'] for t in man['transitions']]
    textures += [d['png'] for d in man.get('decals', {}).values()]
    inputs.update('game/kit/terrain/' + name for name in textures)
    pieces = json.loads((ROOT / 'game/kit/props/index.json').read_text())
    for instance in lab.get('pieces', []):
        mask = (pieces[instance['piece']].get('shadow') or {}).get('mask')
        if mask:
            inputs.add('game/' + mask['png'].removeprefix('res://'))
    metadata = {'schema': 'napattack.kit-render-fixtures/1', 'scale': 1, 'cell_texels': kit.man['cell'],
                'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(inputs)},
                'feature_pixels': features, 'cases': records,
                'negative': {'file': 'three_materials_shifted_profile.png',
                             'rgba_sha256': hashlib.sha256(images['three_materials_shifted_profile.png'].tobytes()).hexdigest(),
                             'mutation': 'compose.profile(a + 1, b, c, material, count)'}}
    return images, (json.dumps(metadata, indent=1, sort_keys=True) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    images, metadata = expected()
    stale = []
    for filename, image in images.items():
        path = HERE / filename
        if args.check:
            try:
                with Image.open(path) as actual:
                    if actual.size != image.size or actual.convert('RGBA').tobytes() != image.tobytes():
                        stale.append(filename)
            except (OSError, ValueError):
                stale.append(filename)
        else:
            image.save(path)
    manifest = HERE / 'references.json'
    if args.check:
        if not manifest.exists() or manifest.read_bytes() != metadata:
            stale.append(manifest.name)
    else:
        manifest.write_bytes(metadata)
    print('kit render fixtures: ' + ('stale: ' + ', '.join(stale) if stale else '3 images and source hashes current'))
    return int(bool(stale))


if __name__ == '__main__':
    raise SystemExit(main())

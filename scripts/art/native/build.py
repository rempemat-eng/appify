"""Render a scene from its plan, its biome and the kit alone.

    python3 -m scripts.art.native.build --scene pilot --density 2
        writes .cache/kit/pilot/scene_2x.png (and lawn_mask_2x.png)
    ... --golden        also writes art/golden/pilot/ (the frozen picture and its manifest)
    ... --compare REF   lists every pixel that differs from REF, by region

The picture is restricted to the biome's palette (palette.restrict), so a colour the biome does
not hold cannot reach the screen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import ctx, load_biome, load_plan  # noqa: E402


def tag(d: float) -> str:
    return ('%g' % d).replace('.', '_') + 'x'


def inputs(scene: str, biome: str) -> list:
    """Every file the render reads: the kit's code and data, the biome, the plan, the house
    palette and the house rule."""
    files = []
    for base, _dirs, names in os.walk(HERE):
        if '__pycache__' in base:
            continue
        for n in sorted(names):
            if n.endswith(('.py', '.json', '.png')):
                files.append(os.path.join(base, n))
    files += [os.path.join(ROOT, 'scripts', 'art', 'biomes', biome + '.json'),
              os.path.join(ROOT, 'art', 'scenes', scene + '.json'),
              os.path.join(ROOT, 'art', 'house-palette.json'),
              os.path.join(ROOT, 'scripts', 'art', 'house_palette.py')]
    return sorted(f for f in files if os.path.exists(f))


def input_hash(scene: str, biome: str, d: float) -> str:
    h = hashlib.sha256()
    h.update(('density %g\n' % d).encode())
    for f in inputs(scene, biome):
        h.update(os.path.relpath(f, ROOT).encode() + b'\0')
        h.update(open(f, 'rb').read())
    return h.hexdigest()


def render(scene: str, d: float):
    plan = load_plan(scene)
    biome = load_biome(plan['biome'])
    ctx.configure(d, biome, plan)
    from scripts.art.native import compose, measure, palette  # noqa: E402  (painters size themselves now)
    img = compose.build(d)
    img, moved = palette.restrict(img, biome['palette'])
    mask = measure.lawn_mask(plan, d, compose.LAST['codes'])
    return img, mask, moved, plan, biome


def compare(img: Image.Image, ref_path: str) -> dict:
    a = np.asarray(img.convert('RGB')).astype(int)
    b = np.asarray(Image.open(ref_path).convert('RGB')).astype(int)
    if a.shape != b.shape:
        return dict(identical=False, size=[list(a.shape), list(b.shape)])
    diff = (np.abs(a - b).sum(-1) > 0)
    out = dict(identical=not diff.any(), pixels=int(diff.sum()))
    if diff.any():
        from scipy import ndimage as ndi
        lab, n = ndi.label(ndi.binary_dilation(diff, iterations=2))
        boxes = []
        for sl in ndi.find_objects(lab):
            ys, xs = sl
            boxes.append([xs.start, ys.start, xs.stop - xs.start, ys.stop - ys.start, int(diff[sl].sum())])
        out['regions'] = sorted(boxes, key=lambda b_: -b_[4])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', default='pilot')
    ap.add_argument('--density', type=float, default=2.0)
    ap.add_argument('--out', default=None)
    ap.add_argument('--golden', action='store_true', help='write art/golden/<scene>/')
    ap.add_argument('--compare', default=None, help='a reference PNG to diff against')
    a = ap.parse_args(argv)
    t0 = time.time()
    img, mask, moved, plan, biome = render(a.scene, a.density)
    out = a.out or os.path.join(ROOT, '.cache', 'kit', a.scene)
    os.makedirs(out, exist_ok=True)
    name = f'scene_{tag(a.density)}.png'
    img.convert('RGB').save(os.path.join(out, name), optimize=True)
    Image.fromarray((mask * 255).astype(np.uint8)).save(os.path.join(out, f'lawn_mask_{tag(a.density)}.png'))
    from scripts.art.native import measure  # noqa: E402
    m = measure.lawn(img, mask)
    print(f'{a.scene} at {a.density:g}x: {img.width} x {img.height}, {moved} px restricted to the biome palette, '
          f'lawn edge share {m["edge_share"]:.3f}, lone px {100 * m["lone_px"]:.1f} % ({time.time() - t0:.0f} s)')
    if a.golden:
        gd = os.path.join(ROOT, 'art', 'golden', a.scene)
        os.makedirs(gd, exist_ok=True)
        img.convert('RGB').save(os.path.join(gd, name), optimize=True)
        man_p = os.path.join(gd, 'manifest.json')
        man = json.load(open(man_p)) if os.path.exists(man_p) else {}
        man.update({
            '_about': ('The frozen golden scene: our own render of the perfected scene, never a reference '
                       'game picture. `inputs` is the hash of everything the render reads (build.inputs); '
                       'npm run check:kit rebuilds the scene when the inputs change and fails if a pixel differs.'),
            'scene': a.scene, 'biome': plan['biome'], 'kit': plan.get('kit'),
        })
        man.setdefault('renders', {})[tag(a.density)] = {
            'file': name, 'size': [img.width, img.height], 'inputs': input_hash(a.scene, plan['biome'], a.density),
            'lawn': {'edge_share': round(m['edge_share'], 4), 'lone_px': round(m['lone_px'], 4)},
        }
        json.dump(man, open(man_p, 'w'), indent=1)
        open(man_p, 'a').write('\n')
        print('golden written:', os.path.relpath(gd, ROOT))
    if a.compare:
        res = compare(img, a.compare)
        print(json.dumps(res if res.get('identical') else dict(res, regions=res.get('regions', [])[:40]), indent=None))
        return 0 if res.get('identical') else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

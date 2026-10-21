"""Write a zone drawn at density 2 for the game (#183's export contract).

    python3 -m scripts.art.native.zone --zone woodland      prints the zone's data as JSON

Writes, for a plan art/scenes/<zone>.json with "zone":
    assets/zones/<zone>/2x/ground.png    the ground, 2 image px a texel (4 a world px, the
                                         zones' scale), so measureDensity reads 2
    assets/zones/<zone>/2x/<kind>.png    one picture per object kind, the same scale
    assets/zones/<zone>/2x/flow.png      the moving water's frames, packed `cols` wide, 1
                                         image px a texel (the renderer stretches it)
The JSON gives each object's native box (world px; its foot is the 1x object's foot, so the
walk and the drawing order stay the zone's own), the flow box and the ground's size. The 1x
zone is untouched: the game shows this one where the art density is 2.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PIL import Image  # noqa: E402

from scripts.art.native import ctx, load_biome, load_plan  # noqa: E402

MAX_SIDE = 4096


def save(img: Image.Image, path: str, per: int) -> list:
    size = (img.width * per, img.height * per)
    assert max(size) <= MAX_SIDE, f'{path}: {size} passes {MAX_SIDE} px'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.resize(size, Image.NEAREST).save(path, optimize=True)
    return list(size)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--zone', required=True)
    ap.add_argument('--density', type=float, default=2.0)
    ap.add_argument('--preview', default=None, help='also write the composed zone here')
    a = ap.parse_args(argv)
    plan = load_plan(a.zone)
    biome = load_biome(plan['biome'])
    ctx.configure(a.density, biome, plan)
    from scripts.art.native import palette, screen
    z = screen.build()
    per = int(4 / a.density)
    out = os.path.join(ROOT, 'assets', 'zones', plan['zone'], '2x')
    moved = 0
    ground = z.ground
    if biome.get('palette'):
        ground, moved = palette.restrict(ground, biome['palette'])
    save(ground.convert('RGB'), os.path.join(out, 'ground.png'), per)
    sprites = {}
    for kind, img in sorted(z.sprites.items()):
        sprites[kind] = save(img, os.path.join(out, f'{kind}.png'), per)
    flow = None
    if z.flow:
        sheet, (bx, by, bw, bh), cols = z.flow
        save(sheet, os.path.join(out, 'flow.png'), 1)
        flow = dict(rect=[bx / a.density, by / a.density, bw / a.density, bh / a.density], cols=cols)
    if a.preview:
        screen.preview(z).save(a.preview)
    doc = dict(zone=plan['zone'], density=a.density, restricted=moved, kinds=sorted(sprites),
               objects=[[oid, kind, *[round(v, 2) for v in box]] for (oid, kind, box) in z.objects], flow=flow)
    print(json.dumps(doc))
    return 0


if __name__ == '__main__':
    sys.exit(main())

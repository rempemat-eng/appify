"""Render a kit zone's plan with the reference renderer (compose.py): the picture Godot draws for
its ground, shadows and dressing, without the pieces' sprites unless --sprites.

    python3 -m scripts.art.kit.render_zone <zone> OUT.png [--sprites] [--scale 3] [--crop x,y,w,h]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit.build import Kit
from scripts.art.kit import compose
from scripts.art.kit.schema import ROOT
from scripts.art.native.palette import to_rgba


def render(zone: str, sprites: bool = False) -> Image.Image:
    plan = json.load(open(os.path.join(ROOT, 'game', 'kit', 'zones', zone + '.json')))
    kit = Kit()
    leg = {k: kit.ids[v] for k, v in plan['legend'].items()}
    cells = np.array([[leg.get(c, 0) for c in r] for r in plan['rows']])
    tiers = np.array([[int(c) for c in r] for r in plan['tiers']]) if plan.get('tiers') else None
    img = Image.fromarray(to_rgba(compose.render(cells, kit, pieces=plan.get('pieces'), tiers=tiers)), 'RGBA')
    if sprites:
        idx = compose.piece_index()
        for pc in sorted(plan.get('pieces', []), key=lambda p: (idx[p['piece']].get('z_sort') != 'ground', p['at'][1])):
            e = idx[pc['piece']]
            v = e['variants'].get(pc.get('variant')) or next(iter(e['variants'].values()))
            sp = Image.open(os.path.join(ROOT, 'game', v['png'][len('res://'):])).convert('RGBA')
            img.alpha_composite(sp, (int(pc['at'][0] - v['foot'][0]), int(pc['at'][1] - v['foot'][1])))
    return img


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('zone')
    ap.add_argument('out')
    ap.add_argument('--sprites', action='store_true')
    ap.add_argument('--scale', type=int, default=1)
    ap.add_argument('--crop')
    a = ap.parse_args(argv)
    img = render(a.zone, a.sprites)
    if a.crop:
        x, y, w, h = map(int, a.crop.split(','))
        img = img.crop((x, y, x + w, y + h))
    if a.scale > 1:
        img = img.resize((img.width * a.scale, img.height * a.scale), Image.NEAREST)
    img.save(a.out)
    print('wrote', a.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())

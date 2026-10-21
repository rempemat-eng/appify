"""The shared 2x kit: one package every lane draws with (docs/vision/rules-system.md).

A rule is a technique in code here, a choice in data (a biome in scripts/art/biomes/<id>.json,
a plan in art/scenes/<id>.json or art/regions/<id>.json), and a measurement in a check
(`npm run check:kit`). Colour is a palette code (palette.py), never a literal RGB.

    palette.py     the one palette: house ramps, the kit's accents, codes, restrict()
    ctx.py         the render context: density, biome and plan (set once, before painting)
    raster.py      units, grids (mirrorable), sprites: form shading, contact, tidy, outlines
    foliage.py     crowns and bushes painted from their 1x master with leaf stamps
    props.py       bench, lantern, signpost, fence, gate, posts, stump, log, mushrooms,
                   boulder, fern, flowers, oak trunk
    chars.py       Bramble and the Mossling (the perfected design); rig.py the rig template
                   and the timing table every folk shares
    ground.py      the ground canvas in codes and the tuft sprite
    terrain/       the c-tiles terrain at any density: sheets (lawn, dirt, rock), autotiles
                   (tops, faces, stairs, water, feet), decals, and the plan-driven scene
    compose.py     a screen from plan + biome + kit: props, dressing, walkers, one shadow rule
    measure.py     the lawn measure (perfect/MEASURE.md)
    export.py      native pictures into the zone pipeline (export scale, 4096 px cap)
    animate.py     the world's animators (water flow, falls), finite loops of changed texels
    build.py       the command: python3 -m scripts.art.native.build --scene pilot --density 2
    check.py       npm run check:kit (palette codes only, the golden rebuild, the lawn band)

How a lane paints a region at 2x: write the plan (tiers, stairs, water, places, props with a
reason, dressing) as data, pick or write its biome (families and palette as codes, sheets,
lawn, shadow, plants with their masters, edges), and render with build.py. A technique the kit
lacks is added here, once, for every lane (never a per-region painter); a choice goes in the
biome; a frozen screen goes in art/golden/<scene>/ and check:kit keeps it.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(ART))


def load_biome(name: str) -> dict:
    return json.load(open(os.path.join(ART, 'biomes', name + '.json')))


def load_plan(name: str) -> dict:
    for folder in ('scenes', 'regions'):
        p = os.path.join(ROOT, 'art', folder, name + '.json')
        if os.path.exists(p):
            return json.load(open(p))
    raise FileNotFoundError(name)

"""How a native screen enters the zone pipeline (scripts/art/zones.py).

The pipeline works in world px: walk grids, feet, the lint, map tiles and the exported object
boxes. A NativeCanvas is a pixel.Canvas whose size and `img` are in world px (a nearest sample
of the texels, so the lint, the map tile and the world canvas read it as before) and whose
`save` writes the native texels at the folder's export scale (2 image px a texel at density 2
in a zone folder at 4 a world px). `measureDensity` then reads 2 from the file's pixels
(lib/art-density.ts).

    zone(L) -> (ground canvas, objects, stands, blocked, extras)   for valley_zones
    characters(out_dir) -> meta                                     the rig's sheets
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
if ART not in sys.path:
    sys.path.insert(0, ART)
from pixel import Canvas  # noqa: E402

from . import folk as FOLK  # noqa: E402
from . import rig  # noqa: E402
from . import screen as SCREEN  # noqa: E402


class NativeCanvas(Canvas):
    """A picture drawn at `density` texels a world px, standing in the pipeline at world size."""

    def __init__(self, hi: Image.Image, density: float):
        k = int(density)
        assert hi.width % k == 0 and hi.height % k == 0, 'a native picture is whole world px'
        super().__init__(hi.width // k, hi.height // k)
        self.hi = hi.convert('RGBA')
        self.native_density = density
        self.img = self.hi.resize((self.w, self.h), Image.NEAREST)

    def save(self, path: str, scale: int = 4):
        per = scale / self.native_density
        assert per == int(per) and per >= 1, f'{scale}x is not whole image px a texel at {self.native_density}'
        size = (self.hi.width * int(per), self.hi.height * int(per))
        assert max(size) <= 4096, f'{path}: {size} passes 4096 px'
        self.hi.resize(size, Image.NEAREST).save(path, optimize=True)


_CACHE = {}


def built(L, density=2.0):
    key = (L.NAME, density)
    if key not in _CACHE:
        _CACHE[key] = SCREEN.build(L, density)
    return _CACHE[key]


def zone(L, density=2.0):
    """The zone function's return for valley_zones: (ground, objects, stands, blocked) plus
    `extras`: sprites (key -> NativeCanvas), feet (key -> FEET), overhead keys, the moving water
    (sheet, box in world px, cols), the night light (image, box in world px)."""
    sc = built(L, density)
    s = sc.s
    k = int(s)
    ground = NativeCanvas(sc.ground, s)
    ground.native = True
    sprites, objects, feet, overhead = {}, [], {}, set()
    for (oid, key, (fx, fy), dr) in sc.objects:
        sprites[key] = NativeCanvas(dr.img, s)
        x = fx - dr.anchor[0] // k
        y = fy - dr.anchor[1] // k
        objects.append((oid, key, int(x), int(y)))
        feet[key] = sc.feet.get(key, ())
    for (oid, key, (x, y), im) in sc.overhead:
        sprites[key] = NativeCanvas(im, s)
        objects.append((oid, key, int(x), int(y)))
        overhead.add(key)
    flow = None
    if sc.flow:
        sheet, (bx, by, bw, bh), cols = sc.flow
        flow = (NativeCanvas(sheet, s), (bx // k, by // k, bw // k, bh // k), cols)
    night = None
    bb = sc.night.getbbox()
    if bb:
        x0, y0, x1, y1 = (bb[0] // k) * k, (bb[1] // k) * k, -(-bb[2] // k) * k, -(-bb[3] // k) * k
        night = (NativeCanvas(sc.night.crop((x0, y0, x1, y1)), s), (x0 // k, y0 // k, (x1 - x0) // k, (y1 - y0) // k))
    extras = dict(sprites=sprites, feet=feet, overhead=overhead, flow=flow, night=night, density=s)
    return ground, objects, dict(L.STANDS), set(sc.blocked), extras


def characters(out_dir: str, density=2.0) -> dict:
    """The rig's sheets for every folk and familiar at a density: <name>.png (2 image px a texel
    at 2x, so a frame is drawn at its world size like every other picture) and their meta."""
    os.makedirs(out_dir, exist_ok=True)
    meta = {}
    for name, f in FOLK.FOLK.items():
        img, m = rig.sheet(f, density)
        per = int(4 / density)
        img.resize((img.width * per, img.height * per), Image.NEAREST).save(os.path.join(out_dir, f'{name}.png'), optimize=True)
        k = density
        def w(v):
            v = v / k
            return int(v) if v == int(v) else v
        meta[name] = dict(frame=[w(m['frame'][0]), w(m['frame'][1])], anchor=[w(m['anchor'][0]), w(m['anchor'][1])],
                          rows=m['rows'], timing=m['timing'], density=density)
    with open(os.path.join(out_dir, 'meta.json'), 'w') as fh:
        json.dump(meta, fh, indent=1)
    return meta

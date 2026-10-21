"""How a native picture enters the game's pipelines (#183's export contract).

The pipelines work in world px: walk grids, feet, the lint, map tiles and object boxes. A
NativeCanvas is a pixel.Canvas whose size and `img` are in world px (a nearest sample of the
texels, so the lint and the map tile read it as before) and whose `save` writes the native
texels at the folder's export scale: zones 4 image px a world px, world tiles 2. At density 2
a zone picture is 2 image px a texel, so `measureDensity` reads 2 (lib/art-density.ts). No
picture passes 4096 px a side.

    NativeCanvas(img, density).save(path, scale=4)
    characters(out_dir, density=2) -> meta     the perfected folk's frame sheets
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

from . import chars  # noqa: E402
from .rig import TIMING  # noqa: E402

MAX_SIDE = 4096


class NativeCanvas(Canvas):
    """A picture drawn at `density` texels a world px, standing in the pipeline at world size."""

    def __init__(self, hi: Image.Image, density: float):
        k = int(density)
        assert k == density, 'a native picture in a world px pipeline has whole texels a world px'
        assert hi.width % k == 0 and hi.height % k == 0, 'a native picture is whole world px'
        super().__init__(hi.width // k, hi.height // k)
        self.hi = hi.convert('RGBA')
        self.native_density = density
        self.img = self.hi.resize((self.w, self.h), Image.NEAREST)

    def save(self, path: str, scale: int = 4):
        per = scale / self.native_density
        assert per == int(per) and per >= 1, f'{scale}x is not whole image px a texel at {self.native_density}'
        size = (self.hi.width * int(per), self.hi.height * int(per))
        assert max(size) <= MAX_SIDE, f'{path}: {size} passes {MAX_SIDE} px'
        self.hi.resize(size, Image.NEAREST).save(path, optimize=True)


# the facings the perfected design draws today; N and a drawn W (SB-03) are the rig's next step
FACINGS = ('S', 'E')
FOLK = {'bramble': chars.bramble, 'mossling': chars.mossling}


def characters(out_dir: str, density: float = 2.0) -> dict:
    """Each folk's frames in one sheet, a row per (facing, action), a column per frame, written
    at 2 image px a texel at 2x (a frame is drawn at its world size like every other picture),
    with the frame size, the foot anchor and the rig's timing in meta.json."""
    os.makedirs(out_dir, exist_ok=True)
    meta = {}
    per = int(4 / density)
    for name, fn in FOLK.items():
        rows = [(f, a) for f in FACINGS for a in TIMING]
        cols = max(TIMING[a]['frames'] for a in TIMING)
        probe = fn(density, 'idle', 'S', 0)
        fw, fh = probe.width, probe.height
        sheet = Image.new('RGBA', (cols * fw, len(rows) * fh), (0, 0, 0, 0))
        for r, (f, a) in enumerate(rows):
            for i in range(TIMING[a]['frames']):
                sheet.alpha_composite(fn(density, a, f, i), (i * fw, r * fh))
        assert max(sheet.width, sheet.height) * per <= MAX_SIDE
        sheet.resize((sheet.width * per, sheet.height * per), Image.NEAREST).save(
            os.path.join(out_dir, f'{name}.png'), optimize=True)
        meta[name] = dict(frame=[fw / density, fh / density], rows=[f'{f}_{a}' for f, a in rows],
                          timing=TIMING, density=density)
    with open(os.path.join(out_dir, 'meta.json'), 'w') as fh_:
        json.dump(meta, fh_, indent=1)
    return meta

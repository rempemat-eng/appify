"""Drawing in world units at any art density (Claude B, a-to-b-clusters part 2, 21 Oct).

The art is moving from 1 texel a world px to a finer density (to-all-density: most likely
2, with 1.5 as the floor; lib/art-density.ts on claude-a/art-density). World logic stays in
world px, so a prop must be drawn in world px too and rasterised at whatever density the
build asks for. `WorldCanvas` is that surface:

- Its coordinates are world px (floats allowed). Texel tx covers world [tx/d, (tx+1)/d).
- `set`, `rect`, `hline` and `vline` fill whole world px: at density 2 a world px is a
  2 x 2 block of texels. Use them for fills and for anything that must keep its world size.
- `hair_h`, `hair_v` and `dot` draw one texel: outlines, rims, creases, glints. At density 1
  a texel is a world px, so they draw exactly what `hline`, `vline` and `set` draw.
- `oval`, `disc` and `box` return texel masks, rasterised at the density (a 2x oval is a
  smoother oval, not a blocky 1x one); `put` and `paint` colour texel masks, and `paint`
  passes each texel's world position to the colour function.
- `tex` is the texel canvas (pixel.Canvas): the shared helpers that work on a mask and its
  neighbours (garden_props.plane, style.facet_stone, style.finalize, keep_foot) take it and a
  texel mask, and come out native at any density.

At density 1 every call does exactly what the same pixel.Canvas call did, in the same order,
so a prop ported to WorldCanvas stays byte-identical (npm run check:art-repro, and
`python3 scripts/art/density.py --check`, which compares each ported prop with its frozen
1x drawing). Noise that should make clusters, not speckle, is looked up at whole world px
(`int(x)`), so at 2x it makes 2 x 2 clusters (art-style: "detail in clusters of two or more").

Ported so far (world_props.py): bench (south, east, west), lamp, hedge, campfire, boulder
(big and small). The rest of lane B's props follow the same pattern when they are redrawn at
the density Matt picks; until then they draw at 1x only.
"""
from __future__ import annotations

import math
import os
import sys

import pixel
from pixel import Canvas

DENSITIES = (1, 1.5, 2)
EPS = 1e-9


class WorldCanvas:
    """A drawing surface in world px over a texel canvas at `density` texels a world px."""

    def __init__(self, w: float, h: float, pad: float = 0, density: float = 1):
        assert density in DENSITIES, f'density {density} is not one of {DENSITIES}'
        self.d = density
        self.w, self.h, self.pad = w, h, pad
        # the texel canvas carries its density (pixel.Canvas, lib/art-density.ts), so finalize and
        # save keep the world size
        self.tex = Canvas(self.t(w), self.t(h), pad=self.t(pad), density=density)

    # --- coordinates ----------------------------------------------------------------
    def t(self, v: float) -> int:
        """A world edge's texel edge."""
        return int(math.floor(v * self.d + EPS))

    def world(self, tx: int):
        """A texel's world position, measured at its centre the way a 1x pixel's integer
        coordinate is (so shapes stay centred at every density); an int at density 1."""
        return tx if self.d == 1 else (tx + 0.5) / self.d - 0.5

    def wpx(self, tx: int) -> int:
        """The world px a texel lies in: look noise and patterns up here, so they make
        world-px clusters (2 x 2 texels at 2x) instead of texel speckle."""
        return tx if self.d == 1 else int(math.floor(tx / self.d + EPS))

    def span(self, v: float, n: float = 1) -> range:
        """The texels that cover world [v, v + n)."""
        return range(self.t(v), self.t(v + n))

    # --- world-px strokes (whole world px) ---------------------------------------------
    def set(self, x: float, y: float, color, alpha: int | None = None):
        if self.d == 1:
            self.tex.set(x, y, color, alpha)
            return
        for ty in self.span(y):
            for tx in self.span(x):
                self.tex.set(tx, ty, color, alpha)

    def rect(self, x: float, y: float, w: float, h: float, color, alpha: int | None = None):
        if self.d == 1:
            self.tex.rect(x, y, w, h, color, alpha)
            return
        for ty in range(self.t(y), self.t(y + h)):
            for tx in range(self.t(x), self.t(x + w)):
                self.tex.set(tx, ty, color, alpha)

    def hline(self, x: float, y: float, w: float, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x: float, y: float, h: float, color):
        self.rect(x, y, 1, h, color)

    def get(self, x: float, y: float):
        return self.tex.get(self.t(x), self.t(y))

    # --- texel strokes (one texel thick) ---------------------------------------------
    def dot(self, x: float, y: float, color, alpha: int | None = None):
        self.tex.set(self.t(x), self.t(y), color, alpha)

    def hair_h(self, x: float, y: float, w: float, color, bottom: bool = False):
        """A line one texel thick along world row y (its top texel row, or its bottom)."""
        ty = self.t(y + 1) - 1 if bottom else self.t(y)
        for tx in range(self.t(x), self.t(x + w)):
            self.tex.set(tx, ty, color)

    def hair_v(self, x: float, y: float, h: float, color, right: bool = False):
        tx = self.t(x + 1) - 1 if right else self.t(x)
        for ty in range(self.t(y), self.t(y + h)):
            self.tex.set(tx, ty, color)

    # --- texel masks ----------------------------------------------------------------
    def oval(self, cx: float, cy: float, rx: float, ry: float) -> set:
        d = self.d
        return pixel.oval(cx * d, cy * d, rx * d, ry * d)

    def disc(self, cx: float, cy: float, r: float) -> set:
        d = self.d
        return pixel.disc(cx * d, cy * d, r * d)

    def box(self, x: float, y: float, w: float, h: float) -> set:
        return {(tx, ty) for ty in range(self.t(y), self.t(y + h)) for tx in range(self.t(x), self.t(x + w))}

    def clip(self, pts, x: float, y: float, w: float, h: float) -> set:
        """A mask kept to world [x, x + w) x [y, y + h)."""
        x0, x1, y0, y1 = self.t(x), self.t(x + w), self.t(y), self.t(y + h)
        return {(tx, ty) for (tx, ty) in pts if x0 <= tx < x1 and y0 <= ty < y1}

    def put(self, tx: int, ty: int, color, alpha: int | None = None):
        self.tex.set(tx, ty, color, alpha)

    def paint(self, pts, colour_at, order=None):
        """Colour each texel of a mask by colour_at(world x, world y) at the texel's centre
        (None leaves it)."""
        for (tx, ty) in (order(pts) if order else pts):
            c = colour_at(self.world(tx), self.world(ty))
            if c is not None:
                self.tex.set(tx, ty, c)

    def texels(self, x: float, y: float, w: float, h: float):
        """(texel x, texel y, world x, world y) over a world rect, row by row (world x and
        y at the texel's centre, as `world` gives them)."""
        for ty in range(self.t(y), self.t(y + h)):
            for tx in range(self.t(x), self.t(x + w)):
                yield tx, ty, self.world(tx), self.world(ty)


def flip_x(wc: WorldCanvas) -> WorldCanvas:
    """The canvas mirrored left to right about its nominal width (texel for texel)."""
    out = WorldCanvas(wc.w, wc.h, pad=wc.pad, density=wc.d)
    src, p, W = wc.tex.img.load(), wc.tex.pad, wc.tex.w
    for y in range(wc.tex.h + 2 * p):
        for x in range(wc.tex.w + 2 * p):
            c = src[x, y]
            if c[3]:
                out.tex.set(W - 1 - (x - p), y - p, c)
    return out


# --- the byte-identity check ------------------------------------------------------------

def ported() -> dict:
    """Each ported prop as a function of density."""
    import world_props as wp
    return {
        'bench': lambda d: wp.bench(density=d),
        'bench_east': lambda d: wp.bench('east', density=d),
        'bench_west': lambda d: wp.bench('west', density=d),
        'lamp': lambda d: wp.lamp(density=d),
        'hedge': lambda d: wp.hedge(96, density=d),
        'campfire': lambda d: wp.campfire(density=d),
        'boulder': lambda d: wp.boulder(True, density=d),
        'stone': lambda d: wp.boulder(False, density=d),
    }


def fingerprint(cv: Canvas) -> str:
    import hashlib
    return hashlib.sha256(cv.img.tobytes() + f'{cv.w}x{cv.h}+{cv.pad}:{cv.ox},{cv.oy}'.encode()).hexdigest()[:16]


FROZEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'density_frozen.json')


def check() -> list:
    """Each ported prop at density 1 matches its frozen 1x drawing (recorded from the
    drawing before it was ported); at 1.5 and 2 it draws, finalizes, and keeps its world
    size within a texel."""
    import json
    import style
    out = []
    with open(FROZEN) as fh:
        frozen = json.load(fh)
    for name, fn in ported().items():
        one = fn(1)
        if fingerprint(one) != frozen.get(name):
            out.append(f'{name}: at density 1 it no longer matches its 1x drawing')
        f1 = style.finalize(one, name=name)
        for d in DENSITIES[1:]:
            cv = fn(d)
            fd = style.finalize(cv, name=f'{name}@{d}')
            for a, b, what in ((f1.w, fd.w, 'width'), (f1.h, fd.h, 'height')):
                if abs(b - a * d) > d + 2:  # the 1 texel outline each side does not scale
                    out.append(f'{name}@{d}: {what} {b} texels for {a} world px')
    return out


def sheet(path: str):
    """The ported props at each density side by side, each at the same world size."""
    from PIL import Image
    import style
    from materials import MATERIALS
    G = MATERIALS['grass']
    cols = []
    for name, fn in ported().items():
        cols.append([style.finalize(fn(d), name=name) for d in DENSITIES])
    S = 4  # image px a world px
    pad = 6
    W = sum(max(int(c[i].w * S / d) for i, d in enumerate(DENSITIES)) for c in cols) + pad * S * (len(cols) + 1)
    H = sum(max(int(c[i].h * S / d) for c in cols) for i, d in enumerate(DENSITIES)) + pad * S * 4
    img = Image.new('RGBA', (W, H), tuple(int(G[2][i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    y = pad * S
    for i, d in enumerate(DENSITIES):
        x = pad * S
        rowh = max(int(c[i].h * S / d) for c in cols)
        for c in cols:
            cv = c[i]
            k = int(S / d) if S % d == 0 else S / d
            im = cv.img.resize((int(cv.w * k), int(cv.h * k)), Image.NEAREST)
            img.alpha_composite(im, (x, y + rowh - im.height))
            x += max(int(cc.w * S / dd) for cc, dd in zip(c, DENSITIES)) + pad * S
        y += rowh + pad * S
    img.save(path)
    return img.size


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    if '--freeze' in sys.argv:
        import json
        data = {name: fingerprint(fn(1)) for name, fn in ported().items()}
        with open(FROZEN, 'w') as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
            fh.write('\n')
        print('froze', len(data), 'props')
    elif '--check' in sys.argv:
        faults = check()
        for f in faults:
            print('FAULT', f)
        print(f'density: {len(ported())} ported props, {len(faults)} faults')
        sys.exit(1 if faults else 0)
    else:
        import tempfile
        p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), 'napattack-density.png')
        print('sheet', sheet(p), p)

"""Tiny pixel-art toolkit used to draw NapAttack's garden at native resolution.

Everything is drawn on an RGBA canvas one pixel at a time, then saved scaled up
with nearest-neighbour so the app can show crisp pixels on any screen.
"""
from __future__ import annotations

import functools
import math
import random
from PIL import Image


@functools.lru_cache(maxsize=8192)  # pure; called millions of times with a few hundred colours
def hex_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = value.lstrip('#')
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)


class Canvas:
    """An RGBA drawing surface in art pixels.

    `pad` adds invisible room on every side, so drawing that strays past the nominal
    w x h is kept rather than silently cut off. A padded canvas is only a working
    surface: style.finalize() trims it to its art and records the offset (ox, oy) of
    the trimmed top-left from the nominal origin, which placement code adds.
    """

    def __init__(self, w: int, h: int, pad: int = 0, density: float = 1):
        self.w, self.h = w, h
        # Art density (lib/art-density.ts): texels per world pixel. w and h are in texels;
        # a 2x picture of a 25 px adult is a 50 texel canvas. 1 for every picture today.
        self.density = density
        self.pad = pad
        self.ox, self.oy = 0, 0
        self.img = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        self._px = self.img.load()
        # unpadded canvases expose raw pixel access, as before
        self.px = self._px if pad == 0 else None

    # --- primitives -------------------------------------------------------
    def set(self, x: int, y: int, color, alpha: int | None = None):
        p = self.pad
        if -p <= x < self.w + p and -p <= y < self.h + p:
            x, y = x + p, y + p
            c = hex_rgba(color) if isinstance(color, str) else color
            if alpha is not None:
                c = (c[0], c[1], c[2], alpha)
            if c[3] == 255 or self._px[x, y][3] == 0:
                self._px[x, y] = c
            else:  # alpha blend onto what is there
                bx = self._px[x, y]
                a = c[3] / 255
                self._px[x, y] = (
                    round(c[0] * a + bx[0] * (1 - a)),
                    round(c[1] * a + bx[1] * (1 - a)),
                    round(c[2] * a + bx[2] * (1 - a)),
                    max(bx[3], c[3]),
                )

    def get(self, x: int, y: int):
        p = self.pad
        if -p <= x < self.w + p and -p <= y < self.h + p:
            return self._px[x + p, y + p]
        return (0, 0, 0, 0)

    def rect(self, x: int, y: int, w: int, h: int, color, alpha: int | None = None):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color, alpha)

    def hline(self, x: int, y: int, w: int, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x: int, y: int, h: int, color):
        self.rect(x, y, 1, h, color)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, color, alpha: int | None = None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.set(x, y, color, alpha)

    def shadow(self, cx: float, cy: float, rx: float, ry: float, alpha: int = 70):
        self.ellipse(cx, cy, rx, ry, (40, 52, 36, alpha))

    def paste(self, other: 'Canvas', x: int, y: int):
        for yy in range(other.h):
            for xx in range(other.w):
                c = other.get(xx, yy)
                if c[3]:
                    self.set(x + xx, y + yy, c)

    def outline(self, color: str, solid: set[tuple[int, int]] | None = None):
        """Draw a 1px outline outside every opaque pixel (classic sprite outline)."""
        pts = solid or {(x, y) for y in range(self.h) for x in range(self.w) if self.px[x, y][3] == 255}
        ring = set()
        for (x, y) in pts:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in pts:
                    ring.add(n)
        for (x, y) in ring:
            self.set(x, y, color)

    def _world(self, texels: int) -> float:
        v = texels / self.density
        return int(v) if v == int(v) else v

    @property
    def world_w(self) -> float:
        """Width in world pixels, for manifests (positions and sizes are always world px)."""
        return self._world(self.w)

    @property
    def world_h(self) -> float:
        return self._world(self.h)

    def save(self, path: str, scale: int = 4):
        """Save scaled by nearest neighbour to `scale` image px per WORLD pixel (the folder's
        export scale), so a finer canvas keeps its folder's file size: a 2x canvas at scale 4
        is 2 image px a texel. Each texel must be a whole number of image px, and no side may
        pass 4096 px (the texture limit every phone supports)."""
        assert self.pad == 0, 'finalize a padded canvas before saving it'
        per = scale / self.density
        assert per == int(per) and per >= 1, f'{scale}x is not whole image px a texel at {self.density}'
        size = (self.w * int(per), self.h * int(per))
        assert self.density == 1 or max(size) <= 4096, f'{path}: {size} passes 4096 px'
        self.img.resize(size, Image.NEAREST).save(path, optimize=True)


def shade_blob(cv: Canvas, pts: set[tuple[int, int]], dark: str, mid: str, light: str, hi: str,
               light_dir=(-1, -1)):
    """Fill a set of pixels with 3-tone shading lit from the top-left, plus highlight."""
    if not pts:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rx, ry = max(1, (max(xs) - min(xs)) / 2), max(1, (max(ys) - min(ys)) / 2)
    for (x, y) in pts:
        nx, ny = (x - cx) / rx, (y - cy) / ry
        d = nx * light_dir[0] + ny * light_dir[1]
        # pixels on the lit side get lighter; dither the band edges
        if d > 0.75:
            col = hi
        elif d > 0.15 or (d > 0.0 and (x + y) % 2 == 0):
            col = light
        elif d > -0.55 or (d > -0.7 and (x + y) % 2 == 0):
            col = mid
        else:
            col = dark
        cv.set(x, y, col)


def disc(cx: float, cy: float, r: float) -> set[tuple[int, int]]:
    return {(x, y) for y in range(int(cy - r) - 1, int(cy + r) + 2)
            for x in range(int(cx - r) - 1, int(cx + r) + 2)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def oval(cx: float, cy: float, rx: float, ry: float) -> set[tuple[int, int]]:
    return {(x, y) for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1}


def noise2(x: int, y: int, seed: int = 0) -> float:
    """Deterministic hash noise in [0, 1)."""
    v = math.sin(x * 12.9898 + y * 78.233 + seed * 37.719) * 43758.5453
    return v - math.floor(v)


@functools.lru_cache(maxsize=1 << 18)
def _lattice(x: int, y: int, seed: int) -> float:
    """noise2 at a lattice point, remembered: neighbouring pixels share their corners."""
    return noise2(x, y, seed)


def smooth_noise(x: float, y: float, scale: float, seed: int = 0) -> float:
    gx, gy = x / scale, y / scale
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _lattice(x0, y0, seed), _lattice(x0 + 1, y0, seed)
    c, d = _lattice(x0, y0 + 1, seed), _lattice(x0 + 1, y0 + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


rng = random.Random(7)

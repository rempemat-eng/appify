"""Measure the coarsest supported texel grid, matching lib/art-density.ts.

Export scale is image pixels per world pixel; density is texels per world pixel.
Never infer either from a colour run or declared drawing density. Every aligned
block must agree, with RGB ignored only when both pixels are fully transparent.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

DENSITIES = (1, 1.5, 2)


def measure_density(rgba: bytes, width: int, height: int, scale: float) -> float | None:
    """Python port of measureDensity(rgba, width, height, scale)."""
    pixels = np.frombuffer(rgba, dtype=np.uint8).reshape(height, width, 4)
    for density in DENSITIES:
        per = scale / density
        if not math.isfinite(per) or per < 1 or not per.is_integer():
            continue
        k = int(per)
        if width % k or height % k:
            continue
        if k == 1:
            return density
        blocks = pixels.reshape(height // k, k, width // k, k, 4)
        first = blocks[:, :1, :, :1, :]
        transparent = (blocks[..., 3] == 0) & (first[..., 3] == 0)
        same = np.all(blocks == first, axis=-1)
        if np.all(transparent | same):
            return density
    return None


def native_image(image: Image.Image, scale: float) -> tuple[Image.Image, float]:
    """Return one image pixel per measured texel and its world density.

    Off-grid data is rejected, not silently decimated. A 2x image keeps both
    texels in each world pixel; a coarser 1x image keeps the historical bytes.
    """
    rgba = image.convert('RGBA')
    density = measure_density(rgba.tobytes(), rgba.width, rgba.height, scale)
    if density is None:
        raise ValueError(f'image is on no supported texel grid at export scale {scale}')
    k = int(scale / density)
    if k == 1:
        return rgba, density
    return rgba.resize((rgba.width // k, rgba.height // k), Image.Resampling.NEAREST), density

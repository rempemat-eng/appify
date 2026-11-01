"""Value noise over world coordinates, identical at every density."""
import numpy as np


def vnoise(x, y, cell, seed):
    gx, gy = np.floor(x / cell).astype(np.int64), np.floor(y / cell).astype(np.int64)
    fx, fy = x / cell - gx, y / cell - gy

    def h(a, b):
        return (((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) & 0xffff) / 65535.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return (h(gx, gy) * (1 - sx) + h(gx + 1, gy) * sx) * (1 - sy) + (h(gx, gy + 1) * (1 - sx) + h(gx + 1, gy + 1) * sx) * sy


def _fmix(h):
    """murmur3's 32-bit finaliser: every input bit avalanches into every output bit."""
    h = h & 0xffffffff
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= h >> 16
    return h


def vnoise_hd(x, y, cell, seed):
    """Value noise like vnoise, with a hash that avalanches (26 Oct review of #288, B1: vnoise's
    xor-of-products hash is close to linear in its low bits, so its lattice values ran in rows and
    a thresholded field laid bands along the lattice lines). For density 3 and up; vnoise stays as
    it is for the 2x kit (the pilot golden)."""
    gx, gy = np.floor(x / cell).astype(np.int64), np.floor(y / cell).astype(np.int64)
    fx, fy = x / cell - gx, y / cell - gy

    def h(a, b):
        k = _fmix((a & 0xffffffff) * 0x9E3779B1 + 0x632BE5AB * seed)
        return _fmix(k ^ ((b & 0xffffffff) * 0x85EBCA77)) / 4294967295.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return (h(gx, gy) * (1 - sx) + h(gx + 1, gy) * sx) * (1 - sy) + (h(gx, gy + 1) * (1 - sx) + h(gx + 1, gy + 1) * sx) * sy

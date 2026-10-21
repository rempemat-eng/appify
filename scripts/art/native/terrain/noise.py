"""Value noise over world coordinates, identical at every density."""
import numpy as np


def vnoise(x, y, cell, seed):
    gx, gy = np.floor(x / cell).astype(np.int64), np.floor(y / cell).astype(np.int64)
    fx, fy = x / cell - gx, y / cell - gy

    def h(a, b):
        return (((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) & 0xffff) / 65535.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return (h(gx, gy) * (1 - sx) + h(gx + 1, gy) * sx) * (1 - sy) + (h(gx, gy + 1) * (1 - sx) + h(gx + 1, gy + 1) * sx) * sy

"""The map renders the same picture every run (art director, 4 Nov: two renders of one commit differed in 8 of 12 images).

The cause was iteration over a set of strings (map53.SMOOTH) to order the majority filter's classes: a set's order follows
the string hash, which Python randomises per process, so the filter's ties fell differently each run. This renders the
overview's ground classes for a small world twice, in two processes with different hash seeds, and compares the pictures.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BLOCKOUT = ROOT / 'docs/vision/research/blockout'

RENDER = r'''
import hashlib, sys
from types import SimpleNamespace
import numpy as np
sys.path.insert(0, sys.argv[1])
import geo5 as g
import map53 as M53, map54 as M54
R, ink = M53.load_palette(sys.argv[2])
rng = np.random.default_rng(7)
smooth = sorted(M53.SMOOTH)
kinds = smooth + ['sea', 'road']
K = rng.integers(0, len(smooth), (g.H, g.W)).astype(np.int16)       # every smoothed class, in even mixtures: the filter ties often
K[:, :3] = len(smooth); K[40:44, :] = len(smooth) + 1
S = {'kinds': kinds, 'K': K, 'land': K != len(smooth)}
M = SimpleNamespace(BUTTES={}, SALT_FLATS={})
cg, names, cid, cols = M54.class_grid(S, R, M)
pic = np.where(cg[..., None] >= 0, cols[np.maximum(cg, 0)], 0).astype(np.uint8)
print(hashlib.md5(pic.tobytes()).hexdigest(), int((cg >= 0).sum()))
'''


def render(seed):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    out = subprocess.run([sys.executable, '-s', '-c', RENDER, str(BLOCKOUT), str(ROOT)], env=env, capture_output=True, text=True,
                         timeout=600, cwd=str(ROOT))
    if out.returncode:
        raise AssertionError(out.stderr[-2000:])
    return out.stdout.split()


class MapDeterminism(unittest.TestCase):
    def test_ground_classes_render_the_same_under_any_hash_seed(self):
        first = render(0)
        for seed in (1, 2, 3):
            self.assertEqual(render(seed), first, f'the ground classes changed with PYTHONHASHSEED={seed}')

    def test_no_render_iterates_the_smoothed_set(self):
        import re
        for name in ('map53.py', 'map54.py'):
            src = (BLOCKOUT / name).read_text()
            self.assertIsNone(re.search(r'for \w+ in (M53\.)?SMOOTH\b', src), f'{name} orders by iterating a set')


if __name__ == '__main__':
    unittest.main()

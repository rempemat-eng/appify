"""Tests for the world editor's kit (docs/world-editor.md).

    python3 -m unittest scripts.art.kit.test_kit

The piece schema (valid pieces pass, each invalid fixture fails for its reason, the subset
validator agrees with `jsonschema` where installed), the kit's pictures are up to date with the
library, every fill tiles seamlessly, and every transition tile is canonical at its borders (so any
two tiles that share a border meet without a seam).
"""
from __future__ import annotations

import json
import os
import unittest

import numpy as np

from scripts.art.kit import build as B
from scripts.art.kit import edges as E
from scripts.art.kit import schema as S

FIX = os.path.join(S.ROOT, 'game', 'kit', 'schema', 'invalid')


class Schema(unittest.TestCase):
    def test_library_valid(self):
        bad = {p: e for p, e in S.check().items() if e}
        self.assertEqual(bad, {})

    def test_invalid_fixtures_fail(self):
        schema = S.load_schema()
        files = sorted(f for f in os.listdir(FIX) if f.endswith('.json'))
        self.assertGreaterEqual(len(files), 5)
        for f in files:
            case = json.load(open(os.path.join(FIX, f)))
            errs = S.errors(case['piece'], schema) + S.semantic(case['piece'])
            self.assertTrue(any(case['expect'] in e for e in errs), '%s: %s not in %s' % (f, case['expect'], errs))

    def test_agrees_with_jsonschema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        schema = S.load_schema()
        v = jsonschema.Draft202012Validator(schema)
        for p in S.piece_files():
            piece = json.load(open(p))
            self.assertEqual(bool(S.errors(piece, schema)), bool(list(v.iter_errors(piece))), p)
        for f in os.listdir(FIX):
            piece = json.load(open(os.path.join(FIX, f)))['piece']
            if json.load(open(os.path.join(FIX, f))).get('semantic'):
                continue
            self.assertEqual(bool(S.errors(piece, schema)), bool(list(v.iter_errors(piece))), f)


class Kit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kit = B.Kit()

    def test_built_and_current(self):
        self.assertEqual(B.build(check=True), 0)

    def test_fills_seamless(self):
        # across the wrap the fill changes no more than between neighbouring rows inside it
        for mid, f in self.kit.fills.items():
            self.assertEqual(f.shape, (self.kit.period, self.kit.period))
            across = np.mean(f[0] != f[-1]) + np.mean(f[:, 0] != f[:, -1])
            inside = np.mean(f[1] != f[0]) + np.mean(f[:, 1] != f[:, 0])
            self.assertLess(across, inside * 1.3, self.kit.names[mid])

    def test_tiles_canonical_at_borders(self):
        # within CALM texels of a border the coverage (upper or not) and the deltas depend only on
        # the border's side, which cells lie either side of it and the crossing's profile
        for tid, tiles in self.kit.over.items():
            seen = {}
            for idx, k, prof, v in E.layout(self.kit.variants):
                t = tiles[idx]
                q = [(k >> b) & 1 for b in range(4)]          # nw, ne, sw, se
                strips = {'n': (t[:E.CALM], (q[0], q[1])), 's': (t[-E.CALM:], (q[2], q[3])),
                          'w': (t[:, :E.CALM], (q[0], q[2])), 'e': (t[:, -E.CALM:], (q[1], q[3]))}
                for i, side in enumerate(E.SIDES):
                    strip, cells = strips[side]
                    key = (side, cells, prof[i])
                    sig = np.where(strip[..., 0] == E.OP_ABS, -1, strip[..., 0] * 1000 + strip[..., 1])
                    if key in seen:
                        np.testing.assert_array_equal(sig, seen[key][0], '%s: tile %d (%s) differs from tile %d at its %s border' % (tid, idx, key, seen[key][1], side))
                    else:
                        seen[key] = (sig, idx)

    def test_no_abs_feature_at_borders(self):
        for tid, tiles in self.kit.over.items():
            for t in tiles:
                rim = np.ones(t.shape[:2], bool)
                rim[E.CALM:-E.CALM, E.CALM:-E.CALM] = False
                self.assertFalse(((t[..., 0] == E.OP_ABS) & rim).any(), tid)

    def test_layout_matches_shader(self):
        # the shader computes each mask's base by the same rule
        base = E.mask_base(self.kit.variants)
        n = len(E.OFFS)
        b = 0
        for k in range(1, 15):
            self.assertEqual(base[k], b)
            b += n ** sum(E.crossings(k)) * self.kit.variants
        self.assertEqual(b, len(E.layout(self.kit.variants)))
        src = open(os.path.join(S.ROOT, 'game', 'world', 'terrain', 'terrain.gdshader')).read()
        for c in ('0x9E3779B1u', '0x85EBCA77u', '0xC2B2AE3Du', '0x27D4EB2Fu', '0x7FEB352Du',
                  '0x8DA6B343u', '0xD8163841u', '0xCB1AB31Fu', '0x2C1B3C6Du'):
            self.assertIn(c, src)


if __name__ == '__main__':
    unittest.main()

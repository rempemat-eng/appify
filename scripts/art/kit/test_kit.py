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
                    sig = strip[..., 0] * 100000 + strip[..., 1]
                    if key in seen:
                        np.testing.assert_array_equal(sig, seen[key][0], '%s: tile %d (%s) differs from tile %d at its %s border' % (tid, idx, key, seen[key][1], side))
                    else:
                        seen[key] = (sig, idx)

    def test_layout_matches_shader(self):
        # the shader computes each mask's base by the same rule
        base = E.mask_base(self.kit.variants)
        n = E.NPROF
        b = 0
        for k in range(1, 15):
            self.assertEqual(base[k], b)
            b += n ** sum(E.crossings(k)) * self.kit.variants
        self.assertEqual(b, len(E.layout(self.kit.variants)))
        src = open(os.path.join(S.ROOT, 'game', 'world', 'terrain', 'terrain.gdshader')).read()
        for c in ('0x1B873593', '0xCC9E2D51', '0x38B34AE5', '0xA1C9B2F7',):
            self.assertIn(c, open(os.path.join(S.ROOT, 'game', 'world', 'terrain', 'terrain_dressing.gd')).read())
        for c in ('0x9E3779B1u', '0x85EBCA77u', '0xC2B2AE3Du', '0x27D4EB2Fu', '0x7FEB352Du',
                  '0x8DA6B343u', '0xD8163841u', '0xCB1AB31Fu', '0x2C1B3C6Du'):
            self.assertIn(c, src)



class Rules(unittest.TestCase):
    """The validator on kit zones (scripts/review/kit_rules.py): each rule trips on a plan that
    breaks it and stays quiet on one that keeps it."""

    def plan(self, rows, pieces=()):
        return {'zone': 't', 'legend': {'.': 'lawn', '#': 'path', '~': 'water'}, 'rows': rows, 'pieces': list(pieces)}

    def faults(self, plan, check):
        from scripts.review import kit_rules as KR
        return [f for f in KR.check_zone(plan) if f['check'] == check]

    def test_lab_and_woodland_pass(self):
        from scripts.review import kit_rules as KR
        for z in ('kitlab', 'woodland_kit'):
            plan = json.load(open(os.path.join(KR.ZONES, z + '.json')))
            self.assertEqual([f for f in KR.check_zone(plan) if f['severity'] == 'fault'], [], z)

    def test_bench(self):
        rows = ['......', '......', '######', '......']
        on = {'id': 'b', 'piece': 'woodland_forest_bench', 'at': [72, 72]}        # its foot in the path's row
        beside = {'id': 'b', 'piece': 'woodland_forest_bench', 'at': [72, 48]}    # on the turf, the path south of it
        far = {'id': 'b', 'piece': 'woodland_forest_bench', 'at': [72, 24]}
        self.assertTrue(self.faults(self.plan(rows, [on]), 'rules.route_clear'))
        self.assertFalse(self.faults(self.plan(rows, [beside]), 'rules.route_clear'))
        self.assertFalse(self.faults(self.plan(rows, [beside]), 'rules.seating'))
        self.assertTrue(self.faults(self.plan(['......', '......', '......', '######'], [far]), 'rules.seating'))

    def test_route_into_water(self):
        self.assertTrue(self.faults(self.plan(['..#...', '..#...', '~~~~~~', '......']), 'rules.route_water'))
        self.assertFalse(self.faults(self.plan(['..#...', '......', '~~~~~~', '......']), 'rules.route_water'))

    def test_water_ends(self):
        self.assertTrue(self.faults(self.plan(['......', '.~~~..', '......', '......']), 'rules.water_end'))
        self.assertFalse(self.faults(self.plan(['......', '.~~~..', '.~~~..', '......']), 'rules.water_end'))   # a pool
        self.assertFalse(self.faults(self.plan(['~~~~~~', '......', '......', '......']), 'rules.water_end'))   # to the edge

    def test_tiers(self):
        rows = ['..##..', '..##..', '..##..', '..##..', '..##..', '..##..']
        tiers = ['111111', '111111', '000000', '000000', '000000', '000000']    # faces fall on rows 2 and 3
        plan = dict(self.plan(rows), tiers=tiers)
        self.assertTrue(self.faults(plan, 'rules.tier_route'))
        steps = {'id': 's', 'piece': 'log_steps', 'at': [72, 96], 'variant': 'w2'}   # the flight over the face, foot on row 4
        plan2 = dict(self.plan(rows, [steps]), tiers=tiers)
        self.assertFalse(self.faults(plan2, 'rules.tier_route'))
        self.assertFalse(self.faults(plan2, 'rules.stair'))
        wrong = dict(self.plan(rows, [dict(steps, at=[72, 144])]), tiers=tiers)    # a cell too low: half on the lawn
        self.assertTrue(self.faults(wrong, 'rules.stair'))

    def test_water_fall(self):
        rows = ['..~~..'] * 6
        tiers = ['111111', '111111', '000000', '000000', '000000', '000000']   # the faces on rows 2 and 3
        self.assertTrue(self.faults(dict(self.plan(rows), tiers=tiers), 'rules.water_fall'))
        fall = {'id': 'f', 'piece': 'waterfall_2', 'at': [72, 96], 'variant': 'w2'}
        self.assertFalse(self.faults(dict(self.plan(rows, [fall]), tiers=tiers), 'rules.water_fall'))
        aside = dict(fall, at=[24, 96])                                         # off the channel
        self.assertTrue(self.faults(dict(self.plan(rows, [aside]), tiers=tiers), 'rules.water_fall'))


class Crossings(unittest.TestCase):
    def test_stepping_stones_carry_a_footpath(self):
        from scripts.review import kit_rules as KR
        rows = ['..#...', '..#...', '~~~~~~', '~~~~~~', '..#...', '..#...']
        plan = {'zone': 't', 'legend': {'.': 'lawn', '#': 'path', '~': 'water'}, 'rows': rows, 'pieces': []}
        self.assertTrue([f for f in KR.check_zone(plan) if f['check'] == 'rules.route_water'])
        plan['pieces'] = [{'id': 's', 'piece': 'stepping_stones_2', 'at': [60, 120], 'variant': 'w2'}]
        self.assertFalse([f for f in KR.check_zone(plan) if f['check'] in ('rules.route_water', 'rules.deck')])


class Surface(unittest.TestCase):
    """Width classes and surface variants (scripts/art/kit/surface.py) and the baked grounds."""

    def test_widths(self):
        from scripts.art.kit import surface as SF
        c = np.zeros((10, 12), bool)
        c[4:6, :] = True            # a lane across
        c[:, 3:5] = True            # a lane down: their junction stays a lane
        c[0:3, 8:11] = True         # a road three cells across
        w = SF.widths(c)
        self.assertEqual(int(w[4, 0]), 2)
        self.assertEqual(int(w[4, 3]), 2)
        self.assertEqual(int(w[1, 9]), 3)
        self.assertEqual(list(SF.water_class(np.array([1, 2, 3, 5, 6, 8]))), [1, 2, 3, 3, 6, 6])

    def test_variants_never_repeat_a_neighbour(self):
        from scripts.art.kit import surface as SF
        c = np.ones((12, 16), bool)
        ctx = {k: np.zeros((12, 16), bool) for k in ('tree', 'water', 'door', 'route', 'shore')}
        for kind in ('dirt', 'lawn', 'water'):
            v = SF.assign(kind, c, None, dict(ctx, cls=np.full((12, 16), 2)), 5)
            self.assertFalse(((v[:, 1:] == v[:, :-1]) & (v[:, 1:] != 'b')).any(), kind)
            self.assertFalse(((v[1:] == v[:-1]) & (v[1:] != 'b')).any(), kind)
            given = np.full((12, 16), '.', '<U1')
            given[3, 4] = 's' if kind == 'dirt' else 'b'
            self.assertEqual(SF.assign(kind, c, given, dict(ctx, cls=np.full((12, 16), 2)), 5)[3, 4], given[3, 4])

    def test_baked_grounds_current(self):
        from scripts.art.kit import bake as BK
        self.assertEqual(BK.check(), 0)

    def test_woodland_reaches_the_painted_bar(self):
        from scripts.art.kit import detail_bar as DB
        res = DB.compare('woodland_kit', os.path.join(S.ROOT, 'game', 'zones', 'woodland', 'art', 'ground.png'))
        for name in ('water', 'path', 'shadow', 'lawn'):
            self.assertTrue(res[name]['pass'], (name, res[name]))


if __name__ == '__main__':
    unittest.main()

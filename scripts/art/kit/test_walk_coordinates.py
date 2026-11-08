"""Walk-output positions use W2's explicit cells/legacy texels contract."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from . import walk as W


class WalkCoordinates(unittest.TestCase):
    def setUp(self):
        self.materials = {
            'lawn': {'id': 'lawn', 'walkable': True},
            'water': {'id': 'water', 'walkable': False},
            'face': {'id': 'face', 'walkable': False, 'face': {'height_cells': 1}},
        }
        self.library = {
            'solid': {'blocks_move': True, 'collision': [0, 0, 12, 12]},
            'offset': {'blocks_move': True, 'collision': [-12, -24, 24, 12]},
            'deck': {'deck': [0, 0, 24, 24]},
            'bridge-solid': {'deck': [0, 0, 24, 24], 'blocks_move': True,
                             'collision': [0, 0, 12, 12]},
            'decoration': {'blocks_move': False, 'collision': [0, 0, 12, 12]},
        }
        loader = patch.object(W.KR, 'load_kit', return_value=(self.materials, self.library))
        loader.start()
        self.addCleanup(loader.stop)

    def plan(self, piece='solid', at=(1, 1), **extra):
        return dict(legend={'.': 'lawn', '~': 'water'}, rows=['..', '..'],
                    pieces=[{'piece': piece, 'at': list(at)}],
                    coordinate_space='cells', **extra)

    def test_cells_block_only_the_correct_review_cell(self):
        expected = np.zeros((4, 4), dtype=bool)
        expected[2, 2] = True
        np.testing.assert_array_equal(W.mask(self.plan()), expected)

    def test_legacy_and_explicit_texels_keep_their_positions(self):
        expected = np.zeros((4, 4), dtype=bool)
        expected[2, 2] = True
        for explicit in (False, True):
            plan = self.plan(at=(24, 24))
            plan.pop('coordinate_space')
            if explicit:
                plan['coordinate_space'] = 'texels'
            with self.subTest(explicit=explicit):
                np.testing.assert_array_equal(W.mask(plan), expected)

    def test_fractional_cells_are_not_rounded(self):
        expected = np.zeros((4, 4), dtype=bool)
        expected[3, 1] = True
        np.testing.assert_array_equal(W.mask(self.plan(at=(0.5, 1.5))), expected)

    def test_collision_offsets_and_dimensions_stay_in_texels(self):
        expected = np.zeros((4, 4), dtype=bool)
        expected[0, 1:3] = True
        np.testing.assert_array_equal(W.mask(self.plan(piece='offset')), expected)

    def test_negative_fractional_cells_clip_at_the_zone_boundary(self):
        expected = np.zeros((4, 4), dtype=bool)
        expected[2, 0] = True
        np.testing.assert_array_equal(W.mask(self.plan(at=(-0.25, 1))), expected)

    def test_deck_exemption_uses_the_same_converted_position(self):
        plan = self.plan(piece='deck', at=(1, 0))
        plan['rows'] = ['~~', '~~']
        expected = np.ones((4, 4), dtype=bool)
        expected[:2, 2:] = False
        np.testing.assert_array_equal(W.mask(plan), expected)

    def test_collision_remains_blocked_on_a_deck(self):
        plan = self.plan(piece='bridge-solid', at=(1, 0))
        plan['rows'] = ['~~', '~~']
        expected = np.ones((4, 4), dtype=bool)
        expected[:2, 2:] = False
        expected[0, 2] = True
        np.testing.assert_array_equal(W.mask(plan), expected)

    def test_terrain_and_tier_rows_are_not_scaled(self):
        plan = self.plan()
        plan.update(rows=['..', '..', '..'], tiers=['11', '00', '00'], pieces=[])
        expected = np.zeros((6, 4), dtype=bool)
        expected[2:4] = True
        np.testing.assert_array_equal(W.mask(plan), expected)

    def test_nonblocking_and_unknown_pieces_remain_ignored(self):
        plan = self.plan(piece='decoration')
        plan['pieces'].append({'piece': 'unknown', 'at': [1, 1]})
        np.testing.assert_array_equal(W.mask(plan), np.zeros((4, 4), dtype=bool))

    def test_plan_library_and_returned_mask_are_independent(self):
        plan = self.plan(piece='bridge-solid')
        plan['metadata'] = {'at': [7, 9]}
        before = copy.deepcopy((plan, self.library, self.materials))
        first = W.mask(plan)
        expected = first.copy()
        first[:] = ~first
        np.testing.assert_array_equal(W.mask(plan), expected)
        self.assertEqual((plan, self.library, self.materials), before)

    def test_unknown_coordinate_spaces_refuse(self):
        for space in ('world', None, 24, True):
            plan = self.plan()
            plan['coordinate_space'] = space
            with self.subTest(space=space), self.assertRaisesRegex(ValueError, 'coordinate_space'):
                W.mask(plan)

    def test_invalid_piece_coordinates_refuse(self):
        for space in ('cells', 'texels'):
            for at in (None, [], [1], [1, 2, 3], ['1', 1], [True, 1],
                       [float('nan'), 1], [1, float('inf')], [10 ** 400, 1]):
                plan = self.plan()
                plan['coordinate_space'] = space
                plan['pieces'][0]['at'] = at
                with self.subTest(space=space, at=at), self.assertRaisesRegex(ValueError, 'finite'):
                    W.mask(plan)
        with self.assertRaisesRegex(ValueError, 'finite'):
            W.mask(self.plan(at=(1e308, 1)))


class WalkCommand(unittest.TestCase):
    # Isolate only the CLI's plan/output root. The real kit registry stays at the
    # repository root, and runpy exercises the unchanged module entry point.
    launcher = '''import runpy, sys
from scripts.review import kit_rules
from scripts.art.kit import schema
schema.ROOT = sys.argv[1]
sys.argv = ['walk', sys.argv[2]]
runpy.run_module('scripts.art.kit.walk', run_name='__main__')
'''

    def run_walk(self, root, zone, plan):
        source = root / 'game/kit/zones' / (zone + '.json')
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(json.dumps(plan))
        output = root / 'game/zones' / zone / 'walk.txt'
        output.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([sys.executable, '-c', self.launcher, str(root), zone],
                                cwd=W.KR.ROOT, capture_output=True, text=True, timeout=20)
        return result, output

    def test_cli_writes_identical_tagged_and_legacy_walk_text(self):
        plan = {'legend': {'.': 'lawn'}, 'rows': ['....'] * 4,
                'coordinate_space': 'cells',
                'pieces': [{'piece': 'woodland_forest_bench', 'at': [2, 2]}]}
        legacy = copy.deepcopy(plan)
        legacy.pop('coordinate_space')
        legacy['pieces'][0]['at'] = [48, 48]
        with tempfile.TemporaryDirectory() as tmp:
            a, cells = self.run_walk(Path(tmp), 'cells', plan)
            b, texels = self.run_walk(Path(tmp), 'texels', legacy)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(b.returncode, 0, b.stderr)
            self.assertEqual(cells.read_bytes(), texels.read_bytes())
            self.assertEqual(len(cells.read_text().splitlines()), 8)
            self.assertIn('#', cells.read_text())
            self.assertIn('8 x 8', a.stdout)

    def test_cli_rejects_units_before_writing_output(self):
        plan = {'legend': {'.': 'lawn'}, 'rows': ['..', '..'],
                'pieces': [], 'coordinate_space': 'world'}
        with tempfile.TemporaryDirectory() as tmp:
            result, output = self.run_walk(Path(tmp), 'invalid', plan)
            self.assertEqual(result.returncode, 1)
            self.assertIn('coordinate_space', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse(output.exists())

    def test_cli_rejects_overflow_without_replacing_a_previous_mask(self):
        plan = {'legend': {'.': 'lawn'}, 'rows': ['..', '..'],
                'coordinate_space': 'cells',
                'pieces': [{'piece': 'woodland_forest_bench', 'at': [1e308, 1]}]}
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'game/zones/invalid/walk.txt'
            output.parent.mkdir(parents=True)
            output.write_text('previous mask\n')
            result, _ = self.run_walk(Path(tmp), 'invalid', plan)
            self.assertEqual(result.returncode, 1)
            self.assertIn('finite', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(output.read_text(), 'previous mask\n')

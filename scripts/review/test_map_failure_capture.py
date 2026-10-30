"""Focused NEW R6 contracts; no world/data_stage or historical suite replay.

These tests are authored first and executed only under the reviewed allocation.
The real-T inventory remains unavailable until the producer reaches that stage.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import runpy
import sys
import tempfile
import time
import unittest
import zipfile

SOURCE = Path(__file__).with_name('map_failure_capture.py')
M = runpy.run_path(str(SOURCE), run_name='new_R6_contract_source_never_main')


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        M['numeric']()
        import numpy as np
        cls.np = np

    def terrain(self, shape=(8, 8)):
        np = self.np
        T = {k: np.zeros(shape, dtype=bool) for k in M['REQUIRED']}
        T.update(K=np.full(shape, 'meadow', object), K0=np.full(shape, 'meadow', object),
                 ground0=np.full(shape, 'meadow', object), h=np.zeros(shape), slope=np.zeros(shape),
                 tiers_pre=np.zeros(shape, dtype=int), route_px={'actual': [(8, 8), (16, 16)]},
                 river_px={'actual': [(8, 16), (16, 8)]},
                 barriers={'sea': np.zeros(shape, bool)}, river_masks={'sea': np.zeros(shape, bool)})
        return T

    def test_all_three_known_object_fields_preserve_literal_values(self):
        for key in ('K', 'K0', 'ground0'):
            original = self.np.array([['meadow', self.np.str_('river')]], object)
            result = M['primitive'](original, key)
            self.assertFalse(result.dtype.hasobject)
            self.assertTrue(self.np.array_equal(result, original))
            self.assertEqual(original.dtype.kind, 'O')

    def test_unknown_and_nonliteral_objects_refuse_before_conversion(self):
        for key, value in [('unknown', 'meadow'), ('K', None), ('K0', 12), ('ground0', object())]:
            with self.assertRaises(M['CaptureError']):
                M['primitive'](self.np.array([[value]], object), key)

    def test_projected_unicode_bound_refuses_before_allocation(self):
        with patch.dict(M['primitive'].__globals__, MAX_RAW=8):
            with self.assertRaises(M['CaptureError']):
                M['primitive'](self.np.array([['long literal']], object), 'K')

    def test_real_inventory_preserves_container_key_identity(self):
        rows = M['inventory'](self.terrain())
        pairs = {(c, k) for c, k, _ in rows}
        self.assertIn(('barriers', 'sea'), pairs)
        self.assertIn(('river_masks', 'sea'), pairs)
        self.assertIn(('T', 'ground0'), pairs)
        self.assertEqual(len(pairs), len(rows))

    def test_missing_actual_key_or_nested_shape_fails(self):
        T = self.terrain(); del T['keepout']
        with self.assertRaises(M['MissingInput']):
            M['inventory'](T)
        T = self.terrain(); T['river_masks']['sea'] = self.np.zeros((2, 2), bool)
        with self.assertRaises(M['MissingInput']):
            M['inventory'](T)

    def test_primitive_archive_and_object_semantics_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-codec-') as name:
            folder = Path(name); meta = M['snapshot'](self.terrain(), (0, 0, 64, 64), folder / 'input.npz')
            self.assertTrue(M['validate_archive'](folder / 'input.npz', meta))
            restored = M['load_snapshot'](folder, meta)
            self.assertEqual(restored[('T', 'K')].dtype.kind, 'O')
            restored[('T', 'K')][0, 0] = 'a longer literal terrain name'
            self.assertEqual(restored[('T', 'K')][0, 0], 'a longer literal terrain name')
            self.assertIn(('barriers', 'sea'), restored)

    def test_snapshot_refuses_crop_leaving_actual_bounds(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-bounds-') as name:
            with self.assertRaises(M['MissingInput']):
                M['snapshot'](self.terrain(), (0, 0, 72, 64), Path(name) / 'bad.npz')

    def test_archive_hash_or_truncated_data_cannot_pass(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-truncated-') as name:
            folder = Path(name); path = folder / 'input.npz'
            meta = M['snapshot'](self.terrain(), (0, 0, 64, 64), path)
            path.write_bytes(path.read_bytes()[:-8])
            with self.assertRaises(M['CaptureError']):
                M['validate_archive'](path, meta)

    def test_atomic_json_budget_keeps_previous_partial_marker(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-atomic-') as name:
            path = Path(name) / 'capture.json'
            M['write_json'](path, {'complete': False})
            original = path.read_bytes()
            with patch.dict(M['write_json'].__globals__, MAX_JSON=8):
                with self.assertRaises(M['CaptureError']):
                    M['write_json'](path, {'complete': True, 'extra': 'x' * 20})
            self.assertEqual(path.read_bytes(), original)

    def test_portable_partial_bundle_is_retrievable_and_never_claims_handoff(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-portable-') as name:
            folder = Path(name) / 'partial'; folder.mkdir()
            M['write_json'](folder / 'capture.json', {'complete': False, 'world_state': 'FAILED'})
            (folder / 'worker.log').write_text('original failure\n')
            portable = M['bundle'](folder)
            self.assertFalse(portable['complete_handoff'])
            receipt = M['verify_bundle'](portable['file'], portable['sha256'])
            self.assertTrue(receipt['retrieved_bytes_verified'])
            with zipfile.ZipFile(portable['file']) as archive:
                self.assertFalse(json.loads(archive.read('PORTABLE-MANIFEST.json'))['complete_handoff'])

    def test_repeated_bundle_refuses_implicit_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-exclusive-') as name:
            folder = Path(name) / 'partial'; folder.mkdir()
            M['bundle'](folder)
            with self.assertRaises(M['CaptureError']):
                M['bundle'](folder)

    def test_actual_preview_rgb_path_executes_before_world_capture(self):
        image = M['diagnostic_image'](self.np.array([['meadow', 'river']], object),
            {'meadow': '#008000', 'river': '#0000ff'})
        self.assertEqual(image.getpixel((0, 0)), (0, 128, 0))
        self.assertEqual(image.getpixel((1, 0)), (0, 0, 255))
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-preview-') as name:
            path = Path(name) / 'tiny.png'
            image.save(path)
            self.assertGreater(path.stat().st_size, 0)

    def test_usage_identity_positive_measurement_and_terminal_contract(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-usage-') as name:
            folder = Path(name); clock = time.monotonic()
            record = {'pid': 123, 'nonce': 'SYNTHETIC', 'sequence': 1, 'monotonic': clock,
                'peak_rss_bytes': 1024, 'terminal': True}
            M['write_json'](folder / 'usage.json', record)
            self.assertEqual(M['usage_record'](folder, 123, 'SYNTHETIC', clock, terminal=True), record)
            with self.assertRaises(M['CaptureError']):
                M['usage_record'](folder, 124, 'SYNTHETIC', clock)
            record['terminal'] = False; M['write_json'](folder / 'usage.json', record)
            with self.assertRaises(M['CaptureError']):
                M['usage_record'](folder, 123, 'SYNTHETIC', clock, terminal=True)

    def test_usage_absent_stale_and_zero_are_not_coverage(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-usage-refuse-') as name:
            folder = Path(name); clock = time.monotonic()
            with self.assertRaises(M['CaptureError']):
                M['usage_record'](folder, 123, 'SYNTHETIC', clock)
            record = {'pid': 123, 'nonce': 'SYNTHETIC', 'sequence': 1, 'monotonic': clock - 6,
                'peak_rss_bytes': 1024, 'terminal': True}
            M['write_json'](folder / 'usage.json', record)
            with self.assertRaises(M['CaptureError']):
                M['usage_record'](folder, 123, 'SYNTHETIC', clock - 10)
            record.update(monotonic=clock, peak_rss_bytes=0); M['write_json'](folder / 'usage.json', record)
            with self.assertRaises(M['CaptureError']):
                M['usage_record'](folder, 123, 'SYNTHETIC', clock)

    def test_capture_observer_preserves_same_original_exception_on_snapshot_failure(self):
        np = self.np; original = ValueError('SYNTHETIC original consumer failure')
        class Town:
            def hand(self):
                return True
            def free(self):
                return True
            def fixed(self):
                return None
            def square(self):
                return None
            def yard(self):
                return None
        def fail(T, X):
            raise original
        tw = SimpleNamespace(_feedback_crossroads=fail, _feedback_rows=lambda *a: None,
            Town=Town, BUILDABLE={'meadow'}, H=8, W=8, CELL=8,
            band_mask=lambda *a: np.zeros((8, 8), bool), _lm=lambda *a: np.zeros((8, 8), bool))
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-identity-') as name:
            recorder = M['Recorder'](tw, Path(name))
            with self.assertRaises(ValueError) as caught:
                with recorder:
                    tw._feedback_crossroads(self.terrain(), None)
            self.assertIs(caught.exception, original)
            self.assertIs(tw._feedback_crossroads, fail)
            self.assertTrue(recorder.errors)
            self.assertFalse(recorder.core['complete'])

    def test_original_frontage_caller_and_hand_free_observation_execute_cheaply(self):
        # A bounded SYNTHETIC fixture through the receiving source functions,
        # specifically catching wrong caller-frame depths before any world run.
        sys.path.insert(0, str(M['BLOCKOUT']))
        import towns55 as tw
        T = self.terrain((48, 64))
        town = tw.Town(T, 'Crossroads', (120, 120), 'fixture', (1, 1), 'fixture', 'fixture', seed=101)
        town.streets = [{'name': 'fixture lane', 'cls': 'lane', 'width_cells': 3, 'width_px': 24,
            'pts': [[80, 120], [160, 120]], 'route': None, 'metric': 'cheb'}]
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-real-consumer-') as name:
            recorder = M['Recorder'](tw, Path(name))
            with patch.multiple(tw, H=48, W=64), recorder:
                recorder.target_active = True  # Synthetic entry at the real consumer boundary.
                result = tw._feedback_rows(town, [(8, 'cottage', 32, 24, [])], [('x', 120, 80, 160, 1, 'fixture lane')])
            self.assertEqual(result, ['crossroads-b008'])
            self.assertEqual(len(recorder.events), 1)
            self.assertEqual(recorder.errors, [])
            self.assertTrue(recorder.events[0]['return'])
            self.assertTrue(recorder.events[0]['free'][0]['return'])
            self.assertEqual(recorder.events[0]['row']['queue'], [8])

    def test_legacy_hand_calls_are_delegated_without_capture(self):
        class Town:
            def hand(self, *args, **kwargs):
                return 'literal legacy return'
            def free(self, *args):
                return True
            def fixed(self, *args):
                return None
            def square(self, *args):
                return None
            def yard(self, *args):
                return None
        tw = SimpleNamespace(_feedback_crossroads=lambda *a: None, _feedback_rows=lambda *a: [], Town=Town,
            BUILDABLE={'meadow'}, band_mask=lambda *a: None, _lm=lambda *a: None)
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-legacy-') as name:
            observer = M['Recorder'](tw, Path(name))
            with observer:
                self.assertEqual(Town().hand(1, 2, 3, 4), 'literal legacy return')
            self.assertEqual(observer.events, [])
            self.assertEqual(observer.errors, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)

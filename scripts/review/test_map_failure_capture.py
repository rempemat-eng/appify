"""Focused NEW R6 contracts; no world/data_stage or historical suite replay.

These tests are authored first and executed only under the reviewed allocation.
The real-T inventory remains unavailable until the producer reaches that stage.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import copy
import ast
import fcntl
import hashlib
import json
import os
import runpy
import sys
import struct
import tempfile
import threading
import time
import unittest
import zipfile

SOURCE = Path(__file__).with_name('map_failure_capture.py')
M = runpy.run_path(str(SOURCE), run_name='new_R6_contract_source_never_main')


def receiving_probe_boundary():
    coordination = json.loads(os.environ['MYGAME_OWNED_SAMPLING_COORDINATION'])
    return M['sampling_boundary'](coordination['path'], coordination['identity'], exclusive=True)


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
            g=SimpleNamespace(COL={'meadow': '#008000'}),
            band_mask=lambda *a: np.zeros((8, 8), bool), _lm=lambda *a: np.zeros((8, 8), bool))
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-identity-') as name:
            recorder = M['Recorder'](tw, Path(name))
            original_snapshot = M['snapshot']
            calls = []
            def snapshot_then_fail_after(*args, **kwargs):
                calls.append(Path(args[2]).name)
                if len(calls) == 3:
                    raise M['CaptureError']('SYNTHETIC optional-after snapshot refusal')
                return original_snapshot(*args, **kwargs)
            with patch.dict(M['Recorder'].begin.__globals__, CROSS=(0, 0, 64, 64), NEON=(0, 0, 64, 64), snapshot=snapshot_then_fail_after):
                with self.assertRaises(ValueError) as caught:
                    with recorder:
                        tw._feedback_crossroads(self.terrain(), None)
            self.assertIs(caught.exception, original)
            self.assertIs(tw._feedback_crossroads, fail)
            self.assertEqual(calls, ['before.npz', 'initial-neon.npz', 'after.npz'])
            self.assertEqual(recorder.errors, [{'type': 'CaptureError', 'message': 'SYNTHETIC optional-after snapshot refusal'}])
            self.assertFalse(recorder.core['complete'])
            core = json.loads((Path(name) / 'capture.json').read_text())
            self.assertEqual(core['stage'], 'FAILURE_CORE_PARTIAL')
            self.assertEqual(core['producer_outcome']['message'], str(original))
            self.assertIn('before', core)
            self.assertIn('initial_neon', core)
            self.assertEqual(core['trials']['sha256'], M['sha'](Path(name) / 'trials.json'))
            self.assertTrue((Path(name) / 'trials.json').is_file())

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


class ReviewRegressions(unittest.TestCase):
    """Three new STDlib-only RED cases; no numeric imports or producer process."""
    def test_atomic_temp_fault_preserves_marker_and_allows_later_write(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-temp-retry-') as name:
            path = Path(name) / 'capture.json'
            M['write_json'](path, {'complete': False, 'stage': 'durable partial'})
            previous = path.read_bytes()
            with patch.object(M['write_json'].__globals__['os'], 'fsync', side_effect=OSError('SYNTHETIC fsync failure')):
                with self.assertRaises(OSError):
                    M['write_json'](path, {'complete': True})
            self.assertEqual(path.read_bytes(), previous)
            self.assertFalse(path.with_name('capture.json.tmp').exists())
            M['write_json'](path, {'complete': False, 'stage': 'later core'})
            self.assertEqual(json.loads(path.read_text())['stage'], 'later core')

    def valid_primitive_archive(self, folder):
        """SYNTHETIC canonical tinyNPZ, constructed without importing NumPy."""
        records = []
        path = folder / 'before.npz'
        pairs = [('T', k) for k in M['REQUIRED']] + [('barriers', 'sea'), ('river_masks', 'the Sleepwater')]
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as output:
            for i, (container, key) in enumerate(pairs):
                if key in ('K', 'K0'):
                    dtype = '<U6'; raw = 'meadow'.encode('utf-32-le') * 4; source_dtype = 'object'
                elif key in ('h', 'slope'):
                    dtype = '<f8'; raw = struct.pack('<dddd', 0, 0, 0, 0); source_dtype = 'float64'
                elif key == 'tiers_pre':
                    dtype = '<i8'; raw = bytes(32); source_dtype = 'int64'
                else:
                    dtype = '|b1'; raw = bytes(4); source_dtype = 'bool'
                header = repr({'descr': dtype, 'fortran_order': False, 'shape': (2, 2)}).encode('latin1')
                header += b' ' * ((64 - (10 + len(header) + 1) % 64) % 64) + b'\n'
                value = b'\x93NUMPY\x01\x00' + struct.pack('<H', len(header)) + header + raw
                key_name = f'a{i:03d}'
                output.writestr(key_name + '.npy', value)
                records.append({'archive_key': key_name, 'container': container, 'source_key': key,
                    'shape': [2, 2], 'dtype': dtype, 'source_dtype': source_dtype,
                    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        return path, {'kind': 'consumer', 'file': path.name, 'bytes': path.stat().st_size,
            'sha256': M['sha'](path), 'box_px': [0, 0, 16, 16], 'global_shape': [2, 2],
            'raw_bytes': sum(r['bytes'] for r in records), 'arrays': records}

    def test_archive_semantic_inventory_and_crop_context_refuse_before_load(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-semantic-') as name:
            folder = Path(name); path, valid = self.valid_primitive_archive(folder)
            self.assertTrue(M['validate_archive'](path, valid))
            changes = []
            duplicate = copy.deepcopy(valid); duplicate['arrays'][1]['source_key'] = 'K'; changes.append(('duplicate', duplicate))
            missing = copy.deepcopy(valid); missing['arrays'][1]['source_key'] = 'renamed'; changes.append(('required', missing))
            crop = copy.deepcopy(valid); crop['box_px'] = [0, 0, 24, 16]; changes.append(('crop', crop))
            global_shape = copy.deepcopy(valid); global_shape['global_shape'] = [1, 2]; changes.append(('global', global_shape))
            for label, metadata in changes:
                with self.subTest(label=label):
                    with self.assertRaises(M['CaptureError']):
                        M['validate_archive'](path, metadata)
            load = Mock(side_effect=AssertionError('N.load must not be reached for duplicate semantic keys'))
            with patch.dict(M['load_snapshot'].__globals__, N=SimpleNamespace(load=load)):
                with self.assertRaises(M['CaptureError']):
                    M['load_snapshot'](folder, duplicate)
            load.assert_not_called()

    def test_postmkdir_setup_failure_still_creates_verified_partial_without_child(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-R6-setup-') as name:
            root = Path(name); out = root / 'phase'; allocation = root / 'allocation.json'
            guard = {'head': 'SYNTHETIC', 'source_sha256': {}}
            allocation.write_text(json.dumps({'go_id': 'SYNTHETIC', 'phase': 'capture', 'out': str(out.resolve()),
                'head': guard['head'], 'source_sha256': guard['source_sha256']}))
            globals_ = M['run_capture'].__globals__
            with patch.dict(globals_, source_guard=Mock(return_value=guard), source_files=Mock(side_effect=OSError('SYNTHETIC setup source-copy failure'))):
                with patch.object(globals_['subprocess'], 'Popen') as start:
                    try:
                        M['run_capture'](allocation, out)
                    except OSError:
                        pass  # The original setup error may escape, but partial evidence must survive.
                    start.assert_not_called()
            artifact = out.with_name(out.name + '.zip')
            self.assertTrue(artifact.is_file())
            self.assertTrue(M['verify_bundle'](artifact, M['sha'](artifact))['retrieved_bytes_verified'])
            self.assertFalse(json.loads((out / 'capture.json').read_text())['complete'])

class OwnedSampling(unittest.TestCase):
    """Real owned filesystem regressions; no world, numeric import or child."""
    def probe_boundary(self):
        return receiving_probe_boundary()

    def test_owned_usage_temp_disappears_at_real_metadata_boundary(self):
        with tempfile.TemporaryDirectory(prefix='R6-owned-disappearance-') as name:
            folder = Path(name); marker = folder / 'capture.json'; transient = folder / 'usage.json.tmp'
            M['write_json'](marker, {'complete': False, 'stage': 'before'})
            transient.write_bytes(b'actual owned usage temp\n')
            original_stat = Path.stat
            observed = []
            def actual_stat(path, *args, **kwargs):
                if path == transient:
                    observed.append(kwargs.get('follow_symlinks', True))
                    # Old two-probe sampler: is_file has observed the real file,
                    # then it vanishes before stat. A single lstat sampler sees
                    # the same actual disappearance before its only observation.
                    if kwargs.get('follow_symlinks', True) is False or len(observed) == 2:
                        transient.unlink()
                return original_stat(path, *args, **kwargs)
            with patch.object(Path, 'stat', actual_stat):
                M['write_json'](marker, {'complete': False, 'stage': 'after'})
            self.assertTrue(observed)
            self.assertFalse(transient.exists())
            self.assertEqual(json.loads(marker.read_text())['stage'], 'after')
            self.assertFalse(marker.with_name('capture.json.tmp').exists())

    def test_real_unreadable_owned_directory_remains_permission_refusal(self):
        # A supported nonroot receiver is required; no fabricated PermissionError
        # or skipped success stands in for a real filesystem denial.
        self.assertNotEqual(os.geteuid(), 0, 'permission control requires an unprivileged receiver')
        with tempfile.TemporaryDirectory(prefix='R6-owned-permission-') as name:
            folder = Path(name); marker = folder / 'capture.json'; blocked = folder / 'unreadable'
            M['write_json'](marker, {'complete': False, 'stage': 'before'})
            previous = marker.read_bytes()
            blocked.mkdir(); (blocked / 'actual.bin').write_bytes(b'owned unreadable input\n')
            with self.probe_boundary():
                blocked.chmod(0)
                try:
                    with self.assertRaises(PermissionError):
                        M['write_json'](marker, {'complete': False, 'stage': 'must refuse'})
                finally:
                    blocked.chmod(0o700)
            self.assertEqual(marker.read_bytes(), previous)
            self.assertFalse(marker.with_name('capture.json.tmp').exists())

    def test_real_allocated_budget_and_dangling_symlink_remain_refusals(self):
        with tempfile.TemporaryDirectory(prefix='R6-owned-budget-') as name:
            folder = Path(name); marker = folder / 'capture.json'
            M['write_json'](marker, {'complete': False})
            with self.subTest(refusal='real allocated budget'):
                budget = 64 * 1024
                with patch.dict(M['write_json'].__globals__, MAX_PACKET=budget):
                    M['write_json'](marker, {'complete': False, 'stage': 'same budget baseline fits'})
                    previous = marker.read_bytes()
                    actual = folder / 'allocated.bin'; actual.write_bytes(b'x' * (128 * 1024))
                    self.assertGreater(actual.stat().st_blocks * 512, budget)
                    with self.assertRaises(M['CaptureError']):
                        M['write_json'](marker, {'complete': True})
                self.assertEqual(marker.read_bytes(), previous)
            with self.subTest(refusal='owned dangling symlink'):
                link = folder / 'link'
                with self.probe_boundary():
                    link.symlink_to(folder / 'missing-owned-target')
                    try:
                        with self.assertRaises(M['CaptureError']):
                            M['write_json'](marker, {'complete': True})
                        self.assertEqual(marker.read_bytes(), previous)
                    finally:
                        link.unlink()  # Refusal and restoration precede the shared monitor's next sample.
            self.assertFalse(marker.with_name('capture.json.tmp').exists())


class SamplingCoordination(unittest.TestCase):
    """Actual file locks/threads, strict real probes; no producer or child process."""
    def lock(self, folder):
        path = folder / 'probe-sampling.lock'
        with path.open('xb') as handle:
            handle.write(b'R6-PROBE\n')
        metadata = path.lstat()
        return path, [metadata.st_dev, metadata.st_ino]

    def test_shared_sample_waits_for_restored_real_symlink_probe(self):
        with tempfile.TemporaryDirectory(prefix='R6-coordinated-probe-') as name:
            folder = Path(name); lock, identity = self.lock(folder)
            (folder / 'actual.bin').write_bytes(b'owned bytes must still count\n')
            expected = M['owned_blocks'](folder)
            entered = threading.Event(); result = []; errors = []
            original_flock = fcntl.flock
            def observed_flock(fd, operation):
                if operation == fcntl.LOCK_SH | fcntl.LOCK_NB:
                    entered.set()
                return original_flock(fd, operation)
            def monitor():
                try:
                    result.append(M['coordinated_owned_blocks'](folder, lock, identity))
                except BaseException as error:
                    errors.append(error)
            thread = threading.Thread(target=monitor)
            link = folder / 'deliberate-invalid-probe'
            with patch.object(fcntl, 'flock', observed_flock):
                try:
                    # The local lock is the actual regression domain. The
                    # receiving lock only shields this deliberate bad fixture
                    # from the independently running all-evidence monitor.
                    with receiving_probe_boundary(), M['sampling_boundary'](lock, identity, exclusive=True):
                        link.symlink_to(folder / 'absent-target')
                        try:
                            with self.assertRaises(M['CaptureError']):
                                M['owned_blocks'](folder)
                            thread.start()
                            self.assertTrue(entered.wait(.1), 'real monitor never attempted shared flock')
                            self.assertEqual(result, [], 'an invalid interval was accepted as a clean sample')
                        finally:
                            link.unlink()
                finally:
                    if thread.ident is not None:
                        thread.join(1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(result, [expected])
            self.assertEqual(M['coordinated_owned_blocks'](folder, lock, identity), expected)

    def test_uncoordinated_real_permission_and_symlink_still_refuse(self):
        self.assertNotEqual(os.geteuid(), 0, 'permission control requires an unprivileged receiver')
        with tempfile.TemporaryDirectory(prefix='R6-uncoordinated-invalid-') as name:
            folder = Path(name); lock, identity = self.lock(folder)
            blocked = folder / 'unreadable'; blocked.mkdir()
            (blocked / 'actual.bin').write_bytes(b'real uncoordinated bad state\n')
            with receiving_probe_boundary():
                blocked.chmod(0)
                try:
                    with self.assertRaises(PermissionError):
                        M['coordinated_owned_blocks'](folder, lock, identity)
                finally:
                    blocked.chmod(0o700)
            link = folder / 'dangling'
            with receiving_probe_boundary():
                link.symlink_to(folder / 'missing')
                try:
                    with self.assertRaises(M['CaptureError']):
                        M['coordinated_owned_blocks'](folder, lock, identity)
                finally:
                    link.unlink()
            self.assertEqual(M['coordinated_owned_blocks'](folder, lock, identity), M['owned_blocks'](folder))

    def test_missing_replaced_and_contended_lock_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix='R6-lock-refusal-') as name:
            folder = Path(name); lock, identity = self.lock(folder)
            with self.assertRaises((M['CaptureError'], FileNotFoundError)):
                M['coordinated_owned_blocks'](folder, folder / 'missing-lock', identity)
            with self.assertRaises(M['CaptureError']):
                M['coordinated_owned_blocks'](folder, lock, [identity[0], identity[1] + 1])
            alias = folder / 'alias'
            with receiving_probe_boundary():
                alias.symlink_to(lock)
                try:
                    with self.assertRaises((M['CaptureError'], OSError)):
                        M['coordinated_owned_blocks'](folder, alias, identity)
                finally:
                    alias.unlink()
            ready = threading.Event(); release = threading.Event(); held_errors = []
            def holder():
                try:
                    with M['sampling_boundary'](lock, identity, exclusive=True):
                        ready.set()
                        if not release.wait(1):
                            raise AssertionError('test did not release actual holder')
                except BaseException as error:
                    held_errors.append(error)
            thread = threading.Thread(target=holder); thread.start()
            try:
                self.assertTrue(ready.wait(1))
                started = time.monotonic()
                with self.assertRaisesRegex(M['CaptureError'], 'deadline'):
                    M['coordinated_owned_blocks'](folder, lock, identity)
                self.assertLess(time.monotonic() - started, 1)
            finally:
                release.set(); thread.join(1)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(held_errors), 1, 'the actual overlong exclusive interval must also refuse')
            self.assertIsInstance(held_errors[0], M['CaptureError'])
            self.assertIn('held beyond deadline', str(held_errors[0]))
            lock.rename(folder / 'retained-old-lock'); lock.write_bytes(b'replacement inode\n')
            with self.assertRaises(M['CaptureError']):
                M['coordinated_owned_blocks'](folder, lock, identity)

    def test_terminal_sample_error_remains_explicit_failure_data(self):
        path = M['REPO'] / '.github/workflows/map-recovery-contracts.yml'
        lines = path.read_text().splitlines()
        start = lines.index('          import json, os, resource, runpy, selectors, signal, subprocess, sys, time')
        end = lines.index('          PY', start)
        tree = ast.parse('\n'.join(line[10:] for line in lines[start:end]))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'final_owned_sample')
        with tempfile.TemporaryDirectory(prefix='R6-terminal-sample-') as name:
            folder = Path(name); lock, identity = self.lock(folder)
            namespace = {'owned': lambda: M['coordinated_owned_blocks'](folder, lock, identity)}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), str(path), 'exec'), namespace)
            link = folder / 'unrestored'
            with receiving_probe_boundary():
                link.symlink_to(folder / 'missing')
                try:
                    allocated, error = namespace['final_owned_sample']()
                    self.assertIsNone(allocated)
                    self.assertIn('symlink', error)
                finally:
                    link.unlink()
            self.assertEqual(namespace['final_owned_sample'](), (M['owned_blocks'](folder), None))


class PreflightInputs(unittest.TestCase):
    """SYNTHETIC negative receiver, real failing unittest/owned file cleanup."""
    def fail_real_receiving_fixture(self, folder, observation):
        temporary = folder / 'private/tmp'
        temporary.mkdir(parents=True)
        class ActualFailure(unittest.TestCase):
            def test_owned_input_fails(self):
                with tempfile.TemporaryDirectory(dir=temporary, prefix='actual-failed-fixture-') as name:
                    observation['original'] = Path(name)
                    (Path(name) / 'actual-fixture.bin').write_bytes(b'actual failing fixture bytes\n')
                    self.fail('SYNTHETIC original prerequisite assertion')
        guard = {'head': 'SYNTHETIC', 'source_sha256': {}}
        # Substitute only outer source/numeric/discovery prerequisites. The
        # unittest failure, TemporaryDirectory lifecycle and bytes stay real;
        # no success verdict is replaced and failure must stop before producer.
        with patch.dict(M['worker'].__globals__, source_guard=Mock(return_value=guard),
                numeric=Mock(return_value={}), runpy=SimpleNamespace(run_path=lambda *a, **k: {'Contracts': ActualFailure})):
            with patch.dict(os.environ, TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary)):
                with self.assertRaisesRegex(M['CaptureError'], 'cheap R6 prerequisites failed'):
                    M['worker'](folder, dict(head=guard['head'], source_sha256={}, versions={}, phase='capture'))

    def test_failing_receiving_fixture_survives_original_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='R6-negative-receiver-') as name:
            folder = Path(name); observed = {}
            self.fail_real_receiving_fixture(folder, observed)
            kept = list(folder.rglob('actual-fixture.bin'))
            self.assertTrue(kept)
            self.assertTrue(all(p.read_bytes() == b'actual failing fixture bytes\n' for p in kept))
            self.assertFalse(observed['original'].exists())
            result = json.loads((folder / 'cheap-preflight.json').read_text())
            self.assertFalse(result['passed'])
            self.assertEqual(result['ran'], 1)

    def test_receiving_copy_failure_retains_original_partial_and_error(self):
        with tempfile.TemporaryDirectory(prefix='R6-negative-copy-') as name:
            folder = Path(name); observed = {}
            def partial_copy_then_fail(source, target):
                target.mkdir(parents=True)
                (target / 'partial.bin').write_bytes(b'real partial copy\n')
                observed['partial'] = target
                raise OSError('SYNTHETIC injected copy failure after partial bytes')
            copy = Mock(side_effect=partial_copy_then_fail)
            with patch.dict(M['worker'].__globals__, shutil=SimpleNamespace(copytree=copy)):
                self.fail_real_receiving_fixture(folder, observed)
            self.assertTrue((observed['original'] / 'actual-fixture.bin').is_file())
            self.assertEqual((observed['original'] / 'actual-fixture.bin').read_bytes(), b'actual failing fixture bytes\n')
            copy.assert_called_once()
            self.assertEqual((observed['partial'] / 'partial.bin').read_bytes(), b'real partial copy\n')
            result = json.loads((folder / 'cheap-preflight.json').read_text())
            self.assertFalse(result['passed'])
            self.assertTrue(result.get('input_retention_errors'))


class CaptureWorkflowContract(unittest.TestCase):
    def test_expected_baseline_requires_all_four_literal_true_flags(self):
        # SOURCE-only acceptance predicate from the actual workflow, not an
        # invented successful world result or a captured-world equality claim.
        path = M['REPO'] / '.github/workflows/map-recovery-capture.yml'
        lines = path.read_text().splitlines()
        start = lines.index('          import hashlib, json, os, runpy')
        end = lines.index('          PY', start)
        tree = ast.parse('\n'.join(line[10:] for line in lines[start:end]))
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'expected_failure' for t in n.targets))
        expression = ast.fix_missing_locations(ast.Expression(assignment.value))
        code = compile(expression, str(path) + ':expected-baseline', 'eval')
        keys = ('trial125', 'records19', 'queue20_23', 'original_error')
        def evaluate(flags):
            env = {'__builtins__': {'all': all}, 'core': {'comparison_target': flags}}
            return eval(code, env, env)
        generator = compile("all(core.get('comparison_target', {}).get(key) is True for key in ('trial125', 'records19', 'queue20_23', 'original_error'))", str(path) + ':namespace-probe', 'eval')
        env = {'__builtins__': {'all': all}, 'core': {'comparison_target': dict.fromkeys(keys, True)}}
        self.assertTrue(eval(generator, env, env))  # Execute a real generator in this restricted namespace.
        self.assertTrue(evaluate(dict.fromkeys(keys, True)))
        self.assertFalse(evaluate({}))
        for key in keys:
            with self.subTest(missing_flag=key):
                flags = dict.fromkeys(keys, True); del flags[key]
                self.assertFalse(evaluate(flags))
            for value in (False, 1, None):
                with self.subTest(flag=key, value=value):
                    flags = dict.fromkeys(keys, True); flags[key] = value
                    self.assertFalse(evaluate(flags))


class LifetimeSourceContract(unittest.TestCase):
    def test_unreaped_anchor_signal_reap_and_acceptance_source_contract(self):
        # SOURCE-ONLY scenario: leader exits while an owned descendant still
        # holds the pipe. Require WNOWAIT anchoring, last group signal BEFORE
        # destructive wait4, then group absence for success. This does not
        # start a child or prove a real leak/cleanup on this operating system.
        tree = ast.parse(SOURCE.read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_capture')
        calls = [n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name) and n.func.value.id == 'os']
        observes = [n for n in calls if n.func.attr == 'waitid']
        destructive = [n for n in calls if n.func.attr == 'wait4']
        signals = [n for n in calls if n.func.attr == 'killpg' and len(n.args) > 1
            and not (isinstance(n.args[1], ast.Constant) and n.args[1].value == 0)]
        with self.subTest(contract='nonreaping-leader-anchor'):
            self.assertTrue(observes)
            self.assertTrue(any(isinstance(n, ast.Attribute) and n.attr == 'WNOWAIT' for call in observes for n in ast.walk(call)))
        with self.subTest(contract='last-owned-group-signal-before-destructive-reap'):
            self.assertTrue(destructive and signals)
            self.assertGreater(min(n.lineno for n in destructive), max(n.lineno for n in signals))
        self.assertIsInstance(function.body[-1], ast.Return)
        expression = ast.fix_missing_locations(ast.Expression(function.body[-1].value))
        code = compile(expression, str(SOURCE) + ':terminal-predicate', 'eval')
        facts = {'phase': 'preview', 'raw': 0, 'complete': True, 'reason': None,
                 'before': {'source': 'SYNTHETIC'}, 'after': {'source': 'SYNTHETIC'}, 'group_absent': True}
        with self.subTest(contract='group-absence-required-for-acceptance'):
            self.assertEqual(eval(code, {'__builtins__': {}}, facts), 0)
            facts['group_absent'] = False
            self.assertNotEqual(eval(code, {'__builtins__': {}}, facts), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)

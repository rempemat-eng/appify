"""Focused real persistence/publication regressions; AUTHORED, NOT RUN.

Select Canary before fault methods. Requires PERSISTENCE_OUT = NEW private retained
directory. CLI also needs GODOT = lead-reviewed copied 4.7.2 engine and
PERSISTENCE_GAME = imported DISPOSABLE exact-source project. Never point at a donor.
No dependency setup, import, full bake or cleanup is performed here.
All evidence survives unittest failure; outer allocation collects/reaps/uploads it.
"""
from __future__ import annotations

import builtins
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import unittest
from unittest.mock import patch
import uuid


FIXTURE = Path(__file__).resolve().parents[3] / 'game/test/fixtures/editor_persistence.json'


def evidence(label):
    base = Path(os.environ['PERSISTENCE_OUT']).resolve(strict=True)
    path = base / (label + '-' + uuid.uuid4().hex)
    path.mkdir(mode=0o700)
    print('persistence evidence:', path, flush=True)
    return path


class InjectedWriteError(OSError):
    pass


class BrokenWriter:
    """Delegate real encoder/dumper writes to a real file, failing after N bytes."""
    def __init__(self, stream, budget):
        self.stream, self.remaining = stream, budget
        self.triggered = False

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def write(self, data):
        if len(data) > self.remaining:
            self.stream.write(data[:self.remaining])
            self.stream.flush()
            self.remaining = 0
            self.triggered = True
            raise InjectedWriteError('injected disk write failure')
        self.remaining -= len(data)
        return self.stream.write(data)


class BakeBoundary(unittest.TestCase):
    def setUp(self):
        # The actual module/painters are imported only during allocated execution.
        from scripts.art.kit import bake
        self.b = bake
        self.original_root = Path(bake.ROOT)
        self.lib = bake._pieces_lib()
        self.base = evidence(self.id().rsplit('.', 1)[-1])
        self.root = self.base / 'publication'
        self.zones = self.root / 'game/kit/zones'
        self.zones.mkdir(parents=True)
        # Only actual hash inputs + empty-piece index needed by the tiny real bake.
        for name in bake.SOURCES + ['game/kit/props/index.json']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.original_root / name).read_bytes())
        self.plan = json.loads(FIXTURE.read_text())
        self.plan['bake'] = True
        self.plan['zone'] = 'probe_a'
        self.plan['doors'] = []
        self.plan['spawns'] = {}
        self.plan['pieces'] = []
        self.plans = {}
        for name in ('probe_a', 'probe_b'):
            plan = copy.deepcopy(self.plan)
            plan['zone'] = name
            self.plans[name] = plan
            (self.zones / (name + '.json')).write_text(json.dumps(plan))
        # Redirect paths only; real bake, hash, encoder, dump, sequential main/check execute.
        # Library is the actual immutable library already read from exact candidate.
        self.addCleanup(patch.stopall)
        patch.object(bake, 'ROOT', str(self.root)).start()
        patch.object(bake, 'ZONES', str(self.zones)).start()
        # _pieces_lib reads real library files, not a fabricated verdict or painter.
        original_loader = bake._pieces_lib
        def actual_library():
            with patch.object(bake, 'ROOT', str(self.original_root)):
                return original_loader()
        patch.object(bake, '_pieces_lib', actual_library).start()

    def _write(self, zone):
        return Path(self.b.write(zone))

    def _fault(self, target, budget):
        actual_open = builtins.open
        writers = []
        def opening(file, mode='r', *args, **kwargs):
            stream = actual_open(file, mode, *args, **kwargs)
            if isinstance(file, (str, bytes, os.PathLike)) and Path(file) == target and 'w' in mode:
                stream = BrokenWriter(stream, budget)
                writers.append(stream)
            return stream
        return patch('builtins.open', opening), writers

    def _not_current(self):
        try:
            result = self.b.check()
        except (OSError, ValueError):
            return  # Explicit read failure is fail-closed, not an advertised success.
        self.assertNotEqual(result, 0, 'failed publication was advertised current')

    def _snapshot(self, label):
        rows = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}
        (self.base / (label + '.json')).write_text(json.dumps(rows, indent=2))
        return rows


class Canary(BakeBoundary):
    def test_real_tiny_bake_and_current_check(self):
        for zone in self.plans:
            path = self._write(zone)
            with self.b.Image.open(path) as image:
                image.load()
                self.assertEqual(image.size, (192, 192))
            self.assertEqual(json.loads(path.with_suffix('.json').read_text())['hash'],
                             self.b.input_hash(self.plans[zone], self.lib))
        self.assertEqual(self.b.check(), 0)
        self._snapshot('canary')


class PublicationFaults(BakeBoundary):
    def test_failed_png_write_cannot_remain_current(self):
        path = self._write('probe_a')
        self._write('probe_b')
        self.assertEqual(self.b.check(), 0, 'prerequisite: baseline is not current')
        before = path.read_bytes()
        self._snapshot('before')
        fault, writers = self._fault(path, 32)
        with fault, self.assertRaises(InjectedWriteError):
            self.b.write('probe_a')  # Real same-input encoder, real truncated file.
        self.assertTrue(any(w.triggered for w in writers), 'fault boundary was not reached')
        self._snapshot('after')
        if path.read_bytes() != before:
            self._not_current()

    def test_failed_second_bake_does_not_advertise_mixed_generation(self):
        for zone in self.plans:
            self._write(zone)
        self._snapshot('before')
        # Change a genuine hash and painter input in BOTH zones.
        for zone, plan in self.plans.items():
            plan['rows'][3] = '        '
            (self.zones / (zone + '.json')).write_text(json.dumps(plan))
        target = Path(self.b.out_path('probe_b')).with_suffix('.json')
        fault, writers = self._fault(target, 10)
        with fault, self.assertRaises(InjectedWriteError):
            self.b.main(['probe_a', 'probe_b'])
        self.assertTrue(any(w.triggered for w in writers), 'second sidecar fault was not reached')
        self._snapshot('after')
        self._not_current()


class ExportCLI(unittest.TestCase):
    def setUp(self):
        self.base = evidence(self.id().rsplit('.', 1)[-1])
        self.outputs = self.base / 'outputs'
        self.outputs.mkdir()
        self.game = Path(os.environ['PERSISTENCE_GAME']).resolve(strict=True)
        self.engine = str(Path(os.environ['GODOT']).resolve(strict=True))
        self.plan = json.loads(FIXTURE.read_text())
        self.source = self.base / 'input.json'
        self.source.write_text(json.dumps(self.plan))
        self.scene = self.base / 'authored.tscn'
        self.calls = 0

    def _cli(self, argument, out, file_limit=None):
        self.calls += 1
        env = dict(os.environ)
        for key in ('XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'TMPDIR'):
            folder = self.base / str(self.calls) / key
            folder.mkdir(parents=True)
            env[key] = str(folder)
        command = [self.engine, '--headless', '--audio-driver', 'Dummy', '--path',
                   str(self.game), '--script', 'res://tools/kit_zone.gd', '--',
                   argument, '--out=' + str(out)]
        def limits():
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            if file_limit is not None:
                resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
                signal.signal(signal.SIGXFSZ, signal.SIG_DFL)
        # One actual child, reaped by subprocess even on timeout. No shell / retries.
        try:
            result = subprocess.run(command, env=env, capture_output=True, timeout=20,
                                    preexec_fn=limits)
        except subprocess.TimeoutExpired as error:
            (self.base / ('call-%s.timeout.json' % self.calls)).write_text(
                json.dumps({'argv': command, 'timeout': 20}))
            (self.base / ('call-%s.stdout' % self.calls)).write_bytes(error.stdout or b'')
            (self.base / ('call-%s.stderr' % self.calls)).write_bytes(error.stderr or b'')
            raise
        (self.base / ('call-%s.json' % self.calls)).write_text(json.dumps({
            'argv': command, 'returncode': result.returncode, 'file_limit': file_limit}))
        (self.base / ('call-%s.stdout' % self.calls)).write_bytes(result.stdout)
        (self.base / ('call-%s.stderr' % self.calls)).write_bytes(result.stderr)
        return result

    def _ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertIsNone(re.search(rb'SCRIPT ERROR|^ERROR:', result.stdout + result.stderr, re.M))

    def test_cli_canary_build_export_rebuild(self):
        self._ok(self._cli('--plan=' + str(self.source), self.scene))
        exported = self.outputs / 'zone.json'
        self._ok(self._cli('--export=' + str(self.scene), exported))
        self.assertEqual(json.loads(exported.read_text()), self.plan)
        rebuilt = self.base / 'rebuilt.tscn'
        self._ok(self._cli('--plan=' + str(exported), rebuilt))
        again = self.outputs / 'again.json'
        self._ok(self._cli('--export=' + str(rebuilt), again))
        self.assertEqual(json.loads(again.read_text()), self.plan)

    def test_rejected_export_preserves_previous_valid_document(self):
        self._ok(self._cli('--plan=' + str(self.source), self.scene))
        output = self.outputs / 'zone.json'
        self._ok(self._cli('--export=' + str(self.scene), output))
        before = output.read_bytes()
        # Real saved scene edit: invalid root zone ID, template retained.
        text = self.scene.read_text()
        needle = 'zone_id = "persistence_probe"'
        self.assertEqual(text.count(needle), 1, 'prerequisite: scene format changed')
        self.scene.write_text(text.replace(needle, 'zone_id = " "'))
        rejected = self._cli('--export=' + str(self.scene), output)
        self.assertNotEqual(rejected.returncode, 0, 'invalid export accepted')
        self.assertEqual(output.read_bytes(), before, 'rejection overwrote valid output')

    def test_kernel_interrupted_export_preserves_or_recovers_document(self):
        self._ok(self._cli('--plan=' + str(self.source), self.scene))
        output = self.outputs / 'zone.json'
        self._ok(self._cli('--export=' + str(self.scene), output))
        prior = json.loads(output.read_text())
        # Extension data is supported and exceeds the kernel's actual output limit.
        self.plan['future']['padding'] = 'x' * 65536
        self.source.write_text(json.dumps(self.plan))
        self._ok(self._cli('--plan=' + str(self.source), self.scene))
        result = self._cli('--export=' + str(self.scene), output, file_limit=4096)
        self.assertNotEqual(result.returncode, 0, 'kernel fault did not interrupt export')
        self.assertTrue(any(p.stat().st_size == 4096 for p in self.outputs.iterdir()
                            if p.is_file()), 'prerequisite: intended file boundary not reached')
        recoverable = []
        # Only actual production output/recovery files count, not test input/evidence.
        for path in self.outputs.iterdir():
            if path.is_file():
                try:
                    value = json.loads(path.read_text())
                except (ValueError, OSError, UnicodeError):
                    continue
                if value == prior or value == self.plan:
                    recoverable.append(path.name)
        self.assertTrue(recoverable, 'no previous valid document or recoverable published document')


if __name__ == '__main__':
    unittest.main()

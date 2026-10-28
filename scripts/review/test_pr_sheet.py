"""PR-sheet contracts exercised against real Git history and isolated gate CLIs.

The fixture producers stand in for the existing asset/scene command boundary;
they do not reproduce or test the art detectors.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from . import pr_sheet


GATE_PRODUCER = r'''
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

scene_gate = __spec__.name.endswith('.run')
ap = argparse.ArgumentParser()
ap.add_argument('target')
ap.add_argument('--out', required=True)
ap.add_argument('--spawn', action='append')
ap.add_argument('--no-sheet', action='store_true')
a = ap.parse_args()
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
mode = os.environ.get('PR_SHEET_FIXTURE_SCENE' if scene_gate else 'PR_SHEET_FIXTURE_ASSET', 'pass')
(out / 'argv.txt').write_text(json.dumps(sys.argv[1:]), encoding='utf-8')
print('fixture gate stdout')
print('fixture gate stderr', file=sys.stderr)
if mode == 'crash':
    print('fixture command failed before its report', file=sys.stderr)
    raise SystemExit(7)
if mode == 'missing':
    raise SystemExit(0)
counts = {'blocker': 0, 'fault': int(mode == 'fail'), 'polish': 0}
findings = ([{'detector': 'detail.fixture', 'severity': 'fault', 'box': [0, 0, 1, 1],
              'message': 'fixture finding', 'fix': 'fixture fix', 'score': 0.2,
              'threshold': 0.9, 'subject': a.target}] if mode == 'fail' else [])
fault = {'detector': 'detail.fixture', 'severity': 'fault', 'box': [0, 0, 1, 1],
         'message': 'fixture finding', 'fix': 'fixture fix'}
if scene_gate:
    zone = a.target
    png = Path('game/zones/woodland/art/prop.png')
    names = [zone + '_zone']
    if mode not in ('missing_capture', 'composite_spawn'):
        names.append(zone + '_start')
    for name in names:
        shutil.copyfile(png, out / (name + '_boxed.png'))
    shutil.copyfile(png, out / (zone + '_zone.png'))
    if mode not in ('missing_capture', 'composite_spawn'):
        shutil.copyfile(png, out / (zone + '_start.png'))
    pictures = [{'picture': zone + '_zone', 'size': [3, 2], 'scale': 1, 'H': 74,
                 'findings': findings, 'grid': []}]
    if mode not in ('missing_capture', 'composite_spawn'):
        pictures.append({'picture': zone + '_start', 'size': [3, 2], 'scale': 2, 'H': 74,
                         'findings': [], 'grid': []})
    report = {'target': zone, 'generated': 'fixture', 'pictures': pictures,
              'scene': {'zone': zone, 'size': [3, 2], 'sprites': 1,
                        'spawns': ['zone'] if mode == 'composite_spawn' else ['start'],
                        'doors': [], 'findings': []}, 'counts': counts}
    if mode == 'scene_bad_finding':
        report['scene']['findings'] = [None]
    if mode == 'picture_bad_finding':
        pictures[0]['findings'] = [None]
    if mode in ('scene_count_mismatch', 'scene_double'):
        report['scene']['findings'] = [dict(fault)]
        pictures[0]['findings'] = [dict(fault)]
        if mode == 'scene_double':
            counts['fault'] = 2
    if mode == 'grid_escape':
        pictures[0]['grid'] = [str(png.resolve())]
    if mode == 'grid_symlink':
        (out / 'grid-link.png').symlink_to(png.resolve())
        pictures[0]['grid'] = ['grid-link.png']
    if mode == 'wrong_target':
        report['target'] = 'another-zone'
    if mode == 'logged_error':
        print('  godot errors at start: [SCRIPT ERROR: fixture]', file=sys.stderr)
    dest = out / 'report.json'
else:
    path = Path(a.target).resolve()
    rel = path.relative_to(Path.cwd()).as_posix()
    parts = Path(rel).parts
    zone = parts[parts.index('zones') + 1] if 'zones' in parts else path.parent.name
    name = path.stem
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {'id': zone + '/' + name, 'file': rel, 'sha256': digest,
              'kind': 'prop', 'biome': 'woodland', 'H': 74, 'density': 3,
              'size': [3, 2], 'status': 'fail' if mode == 'fail' else 'pass',
              'counts': counts, 'detail_bar': {'ours': {'tones': 30, 'shapes': 60},
                  'band': {'tones': 27, 'shapes': 50}, 'ratio': 1.1, 'passed': True},
              'findings': findings}
    if mode == 'wrong_hash':
        report['sha256'] = '0' * 64
    if mode == 'wrong_file':
        report['file'] = 'game/zones/woodland/art/someone-else.png'
    if mode == 'bad_counts':
        report['counts'] = {'blocker': -1, 'fault': 0, 'polish': 0}
    if mode == 'html_metadata':
        report['kind'] = '<svg/onload="fixture()">'
    if mode == 'null_finding':
        report['findings'] = [None]
    if mode == 'missing_finding_field':
        report['findings'] = [{k: v for k, v in fault.items() if k != 'fix'}]
    if mode == 'unknown_finding_severity':
        report['findings'] = [dict(fault, severity='warning')]
    if mode == 'finding_count_mismatch':
        report['findings'] = [dict(fault)]
    if mode == 'bad_finding_box':
        report['findings'] = [dict(fault, box=[0, 0, 1])]
    if mode == 'blank_finding_text':
        report['findings'] = [dict(fault, message='', fix='', score={'opaque': True})]
        counts['fault'] = 1
        report['status'] = 'fail'
    dest = out / (zone + '__' + name + '.json')
    if not a.no_sheet:
        shutil.copyfile(path, dest.with_suffix('.png'))
        if mode == 'sheet_cache':
            cache = Path('artifacts/review/kit/generated-fixture.png')
            cache.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, cache)
if mode == 'malformed':
    dest.write_text('{ not json', encoding='utf-8')
else:
    dest.write_text(json.dumps(report, ensure_ascii=True), encoding='utf-8')
if mode == 'stale':
    os.utime(dest, (1, 1))
if mode == 'nonzero_pass':
    raise SystemExit(9)
if mode == 'checkout':
    subprocess.run(['git', 'checkout', os.environ['PR_SHEET_FIXTURE_CHECKOUT']],
                   check=True, capture_output=True)
if mode == 'dirty_source':
    Path('README.md').write_text('fixture gate changed tracked source\n', encoding='utf-8')
raise SystemExit(1 if mode in ('fail', 'scene_double', 'blank_finding_text') else 0)
'''


GODOT_PRODUCER = '''#!/usr/bin/env python3
import os
import sys
mode = os.environ.get('PR_SHEET_FIXTURE_IMPORT', 'pass')
print('Godot Engine fixture import')
if mode == 'error':
    print('SCRIPT ERROR: Parse Error: fixture import error', file=sys.stderr)
if mode == 'nonzero':
    print('fixture import process failed', file=sys.stderr)
    raise SystemExit(7)
'''


def png_bytes(colour: int = 100) -> bytes:
    """A small genuine RGBA PNG, using only the standard library."""
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack('!I', len(payload)) + kind + payload + struct.pack(
            '!I', zlib.crc32(kind + payload) & 0xffffffff)
    raw = b''.join(b'\0' + bytes((colour, 80, 40, 255)) * 3 for _ in range(2))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 3, 2, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


class PRSheetContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pr-sheet-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'subject repository'
        self.repo.mkdir()
        self.out = self.root / 'review bundle'
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        self.env.pop('PR_SHEET_FIXTURE_ASSET', None)
        self.env.pop('PR_SHEET_FIXTURE_SCENE', None)
        self.env.pop('PR_SHEET_FIXTURE_IMPORT', None)
        self.env.pop('PR_SHEET_FIXTURE_CHECKOUT', None)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'PR sheet fixture')
        self.git('config', 'user.email', 'pr-sheet@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.hooksPath', str(self.root / 'no-hooks'))
        self.write('scripts/__init__.py', '')
        self.write('scripts/review/__init__.py', '')
        self.write('scripts/review/assets.py', GATE_PRODUCER)
        self.write('scripts/review/run.py', GATE_PRODUCER)
        godot = self.write('tools/fake_godot.py', GODOT_PRODUCER)
        godot.chmod(0o755)
        self.env['GODOT'] = str(godot)
        shutil.copyfile(Path(pr_sheet.__file__), self.repo / 'scripts/review/pr_sheet.py')
        self.write('README.md', 'fixture repository\n')
        self.write('art/catalogue/sentinel.json', '{"reviewer":"unchanged"}\n')
        self.write('game/data/zones.json', json.dumps({
            'woodland': 'res://zones/woodland/woodland.tscn'}))
        self.write('game/zones/woodland/woodland.tscn',
                   '[gd_scene format=3]\n\n[node name="Woodland" type="Node2D"]\n'
                   '\n[node name="Spawns" type="Node2D" parent="."]\n'
                   '\n[node name="start" type="Marker2D" parent="Spawns"]\n')
        self.write('game/zones/woodland/art/prop.png', png_bytes())
        self.base = self.commit('baseline')
        self.git('branch', 'base', self.base)
        self.head = self.base

    def git(self, *args: str, check: bool = True) -> str:
        p = subprocess.run(['git', *args], cwd=self.repo, env=self.env,
                           capture_output=True, text=True, check=check, timeout=15)
        return p.stdout.strip()

    def write(self, path: str, content: str | bytes) -> Path:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding='utf-8')
        return target

    def commit(self, message: str) -> str:
        self.git('add', '-A')
        self.git('commit', '-m', message)
        self.head = self.git('rev-parse', 'HEAD')
        return self.head

    def change_asset(self, path='game/zones/woodland/art/new.png') -> str:
        self.write(path, png_bytes(130))
        self.commit('changed art')
        return path

    def cli(self, *args: str, mode: str | None = None,
            scene_mode: str | None = None, import_mode: str | None = None,
            checkout: str | None = None) -> subprocess.CompletedProcess:
        env = dict(self.env)
        if mode:
            env['PR_SHEET_FIXTURE_ASSET'] = mode
        if scene_mode:
            env['PR_SHEET_FIXTURE_SCENE'] = scene_mode
        if import_mode:
            env['PR_SHEET_FIXTURE_IMPORT'] = import_mode
        if checkout:
            env['PR_SHEET_FIXTURE_CHECKOUT'] = checkout
        return subprocess.run([sys.executable, '-m', 'scripts.review.pr_sheet',
                               '--repo', str(self.repo), '--base', 'base',
                               '--out', str(self.out), *args], cwd=self.repo, env=env,
                              capture_output=True, text=True, timeout=30)

    def read_bundle(self) -> dict:
        manifest = json.loads((self.out / 'manifest.json').read_text(encoding='utf-8'))
        self.assertTrue((self.out / 'index.html').is_file())
        self.assertEqual(manifest['manual_review'], 'not_assessed')
        self.assertRegex((self.out / 'index.html').read_text(encoding='utf-8').lower(),
                         r'not.assessed|pending')
        self.assertEqual(manifest['base'], self.base)
        self.assertEqual(manifest['head'], self.head)
        self.assertEqual(manifest['head_tree'], self.git('rev-parse', self.head + '^{tree}'))
        self.assertIn('changes', manifest)
        return manifest

    def assert_report_link(self, row: dict):
        rel = row['evidence']['report']
        self.assertFalse(Path(rel).is_absolute())
        report = self.out / rel
        self.assertTrue(report.resolve().is_relative_to(self.out.resolve()))
        self.assertTrue(report.is_file())
        self.assertEqual(row['report_sha256'], hashlib.sha256(report.read_bytes()).hexdigest())
        for stream in ('stdout', 'stderr'):
            self.assertTrue((self.out / row['evidence'][stream]).is_file())

    def test_collect_changes_pins_refs_and_preserves_add_modify_rename_delete(self):
        self.write('old-name.txt', 'distinct rename content\n')
        self.write('deleted.txt', 'will disappear\n')
        self.base = self.commit('rename baseline')
        self.git('branch', '-f', 'base', self.base)
        self.git('mv', 'old-name.txt', 'new-name.txt')
        (self.repo / 'deleted.txt').unlink()
        self.write('README.md', 'modified\n')
        self.write('added.txt', 'added\n')
        self.commit('all change kinds')
        result = pr_sheet.collect_changes(self.repo, 'base', 'HEAD')
        self.assertEqual(result['base'], self.base)
        self.assertEqual(result['head'], self.head)
        self.assertEqual(result['merge_base'], self.base)
        rows = {r['path']: r for r in result['changes']}
        self.assertEqual(rows['added.txt']['status'][0], 'A')
        self.assertEqual(rows['README.md']['status'][0], 'M')
        self.assertEqual(rows['deleted.txt']['status'][0], 'D')
        self.assertEqual(rows['new-name.txt']['status'][0], 'R')
        self.assertEqual(rows['new-name.txt']['old_path'], 'old-name.txt')

    def test_three_dot_diff_omits_upstream_only_changes(self):
        self.change_asset()
        subject_head = self.head
        self.git('checkout', '-b', 'upstream', self.base)
        self.write('game/zones/woodland/art/upstream-only.png', png_bytes(180))
        upstream = self.commit('upstream artwork')
        self.git('checkout', 'main')
        self.head = subject_head
        changes = pr_sheet.collect_changes(self.repo, upstream, 'HEAD')
        self.assertEqual(changes['base'], upstream)
        self.assertEqual(changes['merge_base'], self.base)
        self.assertEqual([c['path'] for c in changes['changes']],
                         ['game/zones/woodland/art/new.png'])

    def test_no_art_bundle_is_explicit_not_human_approval(self):
        self.write('README.md', 'documentation only\n')
        self.commit('documentation')
        returned = pr_sheet.build_sheet(self.repo, 'base', 'HEAD', self.out, pr='PR fixture')
        manifest = self.read_bundle()
        self.assertEqual(returned, manifest)
        self.assertEqual(manifest['scope'], 'no_art')
        self.assertTrue(manifest['complete'])
        self.assertEqual(manifest['exit_code'], 0)
        self.assertEqual(manifest['assets'], [])
        self.assertEqual(manifest['scenes'], [])
        self.assertTrue(manifest['other_changes'])

    def test_asset_cli_carries_real_hash_command_report_and_preserves_source(self):
        path = self.change_asset()
        before = {p.relative_to(self.repo).as_posix(): p.read_bytes()
                  for p in self.repo.rglob('*') if p.is_file() and '.git' not in p.parts}
        result = self.cli('--pr', 'fixture #42')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertTrue(manifest['complete'])
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(manifest['exit_code'], 0)
        self.assertEqual(len(manifest['assets']), 1)
        row = manifest['assets'][0]
        self.assertEqual(row['path'], path)
        self.assertEqual(row['status'], 'pass')
        self.assertEqual(row['returncode'], 0)
        self.assertEqual(row['input_sha256'], hashlib.sha256((self.repo / path).read_bytes()).hexdigest())
        self.assertEqual(row['counts'], {'blocker': 0, 'fault': 0, 'polish': 0})
        self.assertIn('scripts.review.assets', row['command'])
        self.assertIn(str(self.repo / path), row['command'])
        self.assertNotIn('--record', row['command'])
        self.assertIn('--no-sheet', row['command'])
        self.assertIsNone(row['evidence']['gate_sheet'])
        self.assert_report_link(row)
        after = {p.relative_to(self.repo).as_posix(): p.read_bytes()
                 for p in self.repo.rglob('*') if p.is_file() and '.git' not in p.parts}
        self.assertEqual(after, before)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=no'), '')

    def test_unchanged_requested_png_is_context_and_not_a_git_change(self):
        path = 'game/zones/woodland/art/prop.png'
        result = self.cli('--asset', path, '--asset', str(self.repo / path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['changes'], [])
        self.assertTrue(manifest['complete'])
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(len(manifest['assets']), 1)
        row = manifest['assets'][0]
        self.assertEqual(row['path'], path)
        self.assertEqual(row['change']['status'], 'requested')
        self.assertEqual(row['status'], 'pass')
        self.assertEqual(row['input_sha256'], hashlib.sha256((self.repo / path).read_bytes()).hexdigest())
        self.assert_report_link(row)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=no'), '')

    def test_asset_context_never_generates_legacy_sheet_cache_in_source(self):
        path = 'game/zones/woodland/art/prop.png'
        result = self.cli('--asset', path, mode='sheet_cache')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        row = manifest['assets'][0]
        self.assertIn('--no-sheet', row['command'])
        self.assertIsNone(row['evidence']['gate_sheet'])
        self.assertFalse((self.repo / 'artifacts/review/kit').exists())

    def test_git_blob_replacement_cannot_change_pinned_preview_or_hash(self):
        path = self.change_asset()
        canonical_bytes = (self.repo / path).read_bytes()
        canonical_blob = self.git('rev-parse', 'HEAD:' + path)
        replacement = self.root / 'replacement.png'
        replacement.write_bytes(png_bytes(190))
        replacement_blob = self.git('hash-object', '-w', str(replacement))
        self.git('replace', canonical_blob, replacement_blob)
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        row = manifest['assets'][0]
        self.assertTrue(manifest['complete'])
        self.assertEqual(row['input_blob'], canonical_blob)
        self.assertEqual(row['input_sha256'], hashlib.sha256(canonical_bytes).hexdigest())
        self.assertEqual((self.out / row['evidence']['preview']).read_bytes(), canonical_bytes)
        self.assertEqual((self.repo / path).read_bytes(), canonical_bytes)
        self.assertIn(canonical_blob, self.git('replace', '-l').splitlines())

    def test_gate_metadata_is_escaped_in_html_but_retained_in_manifest(self):
        self.change_asset()
        result = self.cli(mode='html_metadata')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['assets'][0]['metrics']['kind'], '<svg/onload="fixture()">')
        html = (self.out / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('<svg/onload=', html)
        self.assertIn('&lt;svg/onload=', html)

    def test_unusual_filename_is_nul_safe_and_html_escaped(self):
        path = self.change_asset('game/zones/woodland/art/<script>& "café"\nnew.png')
        collected = pr_sheet.collect_changes(self.repo, 'base', 'HEAD')
        self.assertEqual([r['path'] for r in collected['changes']], [path])
        result = self.cli('--pr', '<script>alert("label")</script>')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['assets'][0]['path'], path)
        html = (self.out / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('<script>alert("label")</script>', html)
        self.assertNotIn('<script>&', html)
        self.assertIn('&lt;script&gt;', html)

    def test_removed_asset_is_visible_and_not_a_detector_pass(self):
        (self.repo / 'game/zones/woodland/art/prop.png').unlink()
        self.commit('remove artwork')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'][0]['status'], 'removed')
        self.assertIsNone(manifest['assets'][0]['counts'])

    def test_renamed_asset_retains_old_path_and_reviews_new_bytes(self):
        old = 'game/zones/woodland/art/prop.png'
        new = 'game/zones/woodland/art/renamed prop.png'
        self.git('mv', old, new)
        self.commit('rename artwork')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['assets'][0]['path'], new)
        self.assertEqual(manifest['assets'][0]['change']['old_path'], old)
        self.assertEqual(manifest['assets'][0]['status'], 'pass')

    def test_png_renamed_to_text_remains_visible_unsupported_art(self):
        old = 'game/zones/woodland/art/prop.png'
        new = 'game/zones/woodland/art/prop.txt'
        self.git('mv', old, new)
        self.commit('rename image extension')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(len(manifest['assets']), 1)
        row = manifest['assets'][0]
        self.assertEqual(row['path'], new)
        self.assertEqual(row['change']['old_path'], old)
        self.assertEqual(row['status'], 'unsupported')

    def test_registered_scene_renamed_to_text_cannot_be_no_art_success(self):
        old = 'game/zones/woodland/woodland.tscn'
        new = 'notes/moved-scene.txt'
        (self.repo / 'notes').mkdir()
        self.git('mv', old, new)
        self.commit('move registered scene out of art paths')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(manifest['changes'][0]['path'], new)
        self.assertEqual(manifest['changes'][0]['old_path'], old)
        self.assertTrue(any(row['path'] == new and row['status'] != 'not_art'
                            for row in manifest['other_changes']))

    def test_art_source_renamed_outside_art_prefix_remains_source_only(self):
        old = 'scripts/art/source_fixture.py'
        new = 'tools/moved_source.py'
        self.write(old, '# unchanged generator fixture\n')
        self.base = self.commit('generator baseline')
        self.git('branch', '-f', 'base', self.base)
        self.git('mv', old, new)
        self.commit('move generator outside art prefix')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertTrue(any(row['path'] == new and row['status'] == 'source_only'
                            and row['change']['old_path'] == old
                            for row in manifest['other_changes']))

    def test_unsupported_image_is_visible_and_incomplete(self):
        self.write('game/zones/woodland/art/prop.svg', '<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.commit('unsupported artwork')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertTrue(any(r['status'] == 'unsupported' for r in manifest['assets']))

    def test_art_generator_only_change_is_visible_and_incomplete(self):
        self.write('scripts/art/fixture_prop.py', '# generator has no reviewed output yet\n')
        self.commit('generator source only')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        rows = manifest['assets'] + manifest['other_changes']
        self.assertTrue(any(r.get('path') == 'scripts/art/fixture_prop.py' and
                            r.get('status') == 'source_only' for r in rows))

    def test_symlink_art_is_not_external_detector_evidence(self):
        external = self.root / 'external.png'
        external.write_bytes(png_bytes(170))
        path = self.repo / 'game/zones/woodland/art/linked.png'
        path.symlink_to(external)
        self.commit('linked artwork')
        result = self.cli()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertNotEqual(manifest['assets'][0]['status'], 'pass')
        self.assertEqual(external.read_bytes(), png_bytes(170))

    def test_detector_findings_are_retained_in_failed_bundle(self):
        self.change_asset()
        result = self.cli(mode='fail')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        row = manifest['assets'][0]
        self.assertEqual(row['status'], 'fail')
        self.assertEqual(row['returncode'], 1)
        self.assertEqual(row['counts']['fault'], 1)
        self.assert_report_link(row)

    def test_bad_asset_evidence_cannot_pass_even_when_command_returns_zero(self):
        self.change_asset()
        for mode in ('missing', 'malformed', 'wrong_hash', 'wrong_file', 'bad_counts', 'stale'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli(mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['assets'][0]['status'], 'incomplete')

    def test_malformed_or_count_inconsistent_asset_findings_cannot_pass(self):
        self.change_asset()
        for mode in ('null_finding', 'missing_finding_field', 'unknown_finding_severity',
                     'finding_count_mismatch', 'bad_finding_box'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli(mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['assets'][0]['status'], 'incomplete')

    def test_blank_finding_text_and_opaque_optional_metadata_remain_valid(self):
        self.change_asset()
        result = self.cli(mode='blank_finding_text')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        row = manifest['assets'][0]
        self.assertEqual(row['status'], 'fail')
        self.assertEqual(row['counts']['fault'], 1)
        self.assert_report_link(row)

    def test_command_failure_is_not_overridden_by_a_passing_report(self):
        self.change_asset()
        for mode in ('crash', 'nonzero_pass'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli(mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['assets'][0]['status'], 'incomplete')
                self.assertNotEqual(manifest['assets'][0]['returncode'], 0)

    def test_explicit_scene_adds_requested_capture_evidence(self):
        self.write('README.md', 'scene requested independently of art diff\n')
        self.commit('scene request')
        result = self.cli('--scene', 'woodland')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertTrue(manifest['complete'])
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(len(manifest['scenes']), 1)
        row = manifest['scenes'][0]
        self.assertEqual(row['status'], 'pass')
        self.assertIn('scripts.review.run', row['command'])
        self.assertIn('woodland', row['command'])
        self.assert_report_link(row)

    def test_scene_missing_capture_or_bad_report_is_incomplete(self):
        self.write('README.md', 'scene requested\n')
        self.commit('scene request')
        for mode in ('missing_capture', 'wrong_target', 'missing', 'malformed', 'crash', 'logged_error'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli('--scene', 'woodland', scene_mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['scenes'][0]['status'], 'incomplete')

    def test_zone_named_spawn_cannot_turn_composite_into_capture_evidence(self):
        result = self.cli('--scene', 'woodland', '--spawn', 'zone', scene_mode='composite_spawn')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scenes'][0]['status'], 'incomplete')

    def test_malformed_or_count_inconsistent_scene_findings_cannot_pass(self):
        for mode in ('scene_bad_finding', 'picture_bad_finding', 'scene_count_mismatch'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli('--scene', 'woodland', scene_mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['scenes'][0]['status'], 'incomplete')

    def test_valid_scene_occurrences_keep_composite_and_scene_counts(self):
        result = self.cli('--scene', 'woodland', scene_mode='scene_double')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        row = manifest['scenes'][0]
        self.assertFalse(manifest['complete'])
        self.assertEqual(row['status'], 'fail')
        self.assertEqual(row['counts']['fault'], 2)
        self.assert_report_link(row)

    def test_escaping_or_symlink_grid_is_not_accepted_as_bundle_evidence(self):
        self.write('README.md', 'scene requested\n')
        self.commit('scene request')
        original = (self.repo / 'game/zones/woodland/art/prop.png').read_bytes()
        for mode in ('grid_escape', 'grid_symlink'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli('--scene', 'woodland', scene_mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                manifest = self.read_bundle()
                row = manifest['scenes'][0]
                self.assertFalse(manifest['complete'])
                self.assertEqual(row['status'], 'incomplete')
                for evidence in row['evidence']['pictures']:
                    self.assertTrue((self.out / evidence).resolve().is_relative_to(self.out.resolve()))
                    self.assertFalse((self.out / evidence).is_symlink())
                self.assertEqual((self.repo / 'game/zones/woodland/art/prop.png').read_bytes(), original)

    def test_malformed_zone_registry_is_clean_incomplete_evidence(self):
        for registry in ('{ not json', '[]', 'null', '{"woodland":123}'):
            with self.subTest(registry=registry):
                shutil.rmtree(self.out, ignore_errors=True)
                self.write('game/data/zones.json', registry)
                self.commit('malformed zone registry')
                result = self.cli('--scene', 'woodland')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['scenes'][0]['status'], 'incomplete')

    def test_unknown_scene_never_uses_runtime_fallback_or_imports_project(self):
        result = self.cli('--scene', 'not-a-registered-zone')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        row = manifest['scenes'][0]
        self.assertEqual(row['path'], 'not-a-registered-zone')
        self.assertEqual(row['status'], 'incomplete')
        self.assertEqual(row['command'], [])
        self.assertIsNone(row['returncode'])
        self.assertIsNone(manifest['preflight'])

    def test_unregistered_scene_source_is_visible_and_incomplete(self):
        path = 'game/zones/unregistered/unregistered.tscn'
        self.write(path, '[gd_scene format=3]\n[node name="Unregistered" type="Node2D"]\n')
        self.commit('unregistered scene source')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scenes'], [])
        self.assertTrue(any(row['path'] == path and row['status'] == 'source_only'
                            for row in manifest['other_changes']))

    def test_other_scene_in_registered_folder_is_not_reviewed_by_folder_guess(self):
        path = 'game/zones/woodland/unreferenced.tscn'
        self.write(path, '[gd_scene format=3]\n[node name="Unreferenced" type="Node2D"]\n')
        self.commit('different scene in registered folder')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scenes'], [])
        self.assertTrue(any(row['path'] == path and row['status'] == 'source_only'
                            for row in manifest['other_changes']))

    def test_changed_registered_scene_infers_its_exact_registered_target(self):
        path = 'game/zones/woodland/woodland.tscn'
        current = (self.repo / path).read_text(encoding='utf-8')
        self.write(path, current + '\n; changed registered scene fixture\n')
        self.commit('registered scene source')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertTrue(manifest['complete'])
        self.assertEqual(len(manifest['scenes']), 1)
        self.assertEqual(manifest['scenes'][0]['path'], 'woodland')
        self.assertEqual(manifest['scenes'][0]['status'], 'pass')
        self.assertTrue(any(row['path'] == path and row['status'] == 'scene_source'
                            for row in manifest['other_changes']))

    def test_scene_detector_failure_remains_failure(self):
        self.change_asset()
        result = self.cli('--scene', 'woodland', scene_mode='fail')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['scenes'][0]['status'], 'fail')
        self.assertEqual(manifest['scenes'][0]['counts']['fault'], 1)

    def test_scene_import_errors_cannot_be_hidden_by_a_passing_gate(self):
        self.write('README.md', 'scene requested\n')
        self.commit('scene request')
        for mode in ('error', 'nonzero'):
            with self.subTest(mode=mode):
                shutil.rmtree(self.out, ignore_errors=True)
                result = self.cli('--scene', 'woodland', import_mode=mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                manifest = self.read_bundle()
                self.assertFalse(manifest['complete'])
                self.assertEqual(manifest['scenes'][0]['status'], 'incomplete')

    def test_gate_checkout_move_prevents_success_and_is_not_reset(self):
        self.change_asset()
        frozen_head = self.head
        result = self.cli(mode='checkout', checkout=self.base)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=no'), '')
        if (self.out / 'manifest.json').exists():
            manifest = json.loads((self.out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['head'], frozen_head)
            self.assertFalse(manifest['complete'])
            self.assertNotEqual(manifest['exit_code'], 0)

    def test_gate_tracked_edit_prevents_success_and_is_not_reset(self):
        self.change_asset()
        result = self.cli(mode='dirty_source')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual((self.repo / 'README.md').read_text(),
                         'fixture gate changed tracked source\n')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        if (self.out / 'manifest.json').exists():
            manifest = json.loads((self.out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertFalse(manifest['complete'])
            self.assertNotEqual(manifest['exit_code'], 0)

    def test_unknown_requested_spawn_is_rejected_without_false_capture_pass(self):
        self.write('README.md', 'scene requested\n')
        self.commit('scene request')
        result = self.cli('--scene', 'woodland', '--spawn', 'missing')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        if (self.out / 'manifest.json').exists():
            manifest = self.read_bundle()
            self.assertFalse(manifest['complete'])

    def test_bad_ref_cli_is_clean_nonzero(self):
        result = self.cli('--base', 'does-not-exist')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertTrue((result.stdout + result.stderr).strip())

    def test_unrelated_histories_are_not_no_art_success(self):
        original = self.head
        self.git('checkout', '--orphan', 'unrelated')
        self.git('rm', '-rf', '.')
        self.write('unrelated.txt', 'no shared ancestor\n')
        unrelated = self.commit('unrelated history')
        self.git('checkout', 'main')
        self.head = original
        result = self.cli('--base', unrelated)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_dirty_tracked_source_is_rejected_without_changing_it(self):
        self.change_asset()
        for staged in (False, True):
            with self.subTest(staged=staged):
                self.write('README.md', 'local edit must survive\n')
                if staged:
                    self.git('add', 'README.md')
                result = self.cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                self.assertEqual((self.repo / 'README.md').read_text(), 'local edit must survive\n')
                self.git('reset', '--hard', self.head)

    def assert_hidden_index_edit_is_preserved(self, flag: str):
        self.change_asset()
        self.git('update-index', flag, '--', 'README.md')
        self.write('README.md', 'hidden tracked edit must survive\n')
        hidden_flag = self.git('ls-files', '-v', '--', 'README.md')
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=no'), '')
        result = self.cli()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual((self.repo / 'README.md').read_text(), 'hidden tracked edit must survive\n')
        self.assertEqual(self.git('ls-files', '-v', '--', 'README.md'), hidden_flag)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_assume_unchanged_edit_is_rejected_and_preserved(self):
        self.assert_hidden_index_edit_is_preserved('--assume-unchanged')

    def test_skip_worktree_edit_is_rejected_and_preserved(self):
        self.assert_hidden_index_edit_is_preserved('--skip-worktree')

    def test_requested_head_must_match_checked_out_head(self):
        self.change_asset()
        result = self.cli('--head', self.base)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_existing_nonempty_output_is_never_reused_or_deleted(self):
        self.change_asset()
        self.out.mkdir()
        sentinel = self.out / 'manifest.json'
        sentinel.write_text('{"stale":"must survive"}\n', encoding='utf-8')
        result = self.cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(sentinel.read_text(), '{"stale":"must survive"}\n')

    def test_existing_empty_output_directory_is_supported(self):
        self.change_asset()
        self.out.mkdir()
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.read_bundle()['complete'])

    def test_output_below_git_metadata_is_rejected_before_any_files_are_written(self):
        git_dir = Path(self.git('rev-parse', '--absolute-git-dir'))
        for output in (git_dir / 'new-review', git_dir / 'objects' / 'new-review'):
            with self.subTest(output=str(output)):
                self.assertFalse(output.exists())
                result = self.cli('--out', str(output))
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
                self.assertFalse(output.exists())
                self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)


if __name__ == '__main__':
    unittest.main()

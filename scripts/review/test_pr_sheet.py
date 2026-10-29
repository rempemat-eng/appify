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
if mode == 'metadata_tamper':
    for evidence in (out.parents[1] / 'sources').glob('*.txt'):
        evidence.write_bytes(b'fixture changed bundled context evidence')
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
        shutil.copyfile(Path(pr_sheet.owned_launch.__file__), self.repo / 'scripts/review/owned_launch.py')
        representation = Path(pr_sheet.__file__).with_name('kit_representation.py')
        if representation.exists():
            shutil.copyfile(representation, self.repo / 'scripts/review/kit_representation.py')
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

    def kit_metadata(self):
        """Tiny authored metadata, never production artwork or a material acceptance fixture."""
        terrain = {'materials': [{'id': 'lawn', 'fill': 'encoded.png'}],
                   'transitions': [{'id': 'edge', 'png': 'ops.png', 'upper': 'lawn', 'lower': '*'}],
                   'decals': {'tuft': {'png': 'decal.png', 'anchor': [0, 1]}},
                   'lut': 'lut.png', 'noise': 'noise.png', 'palette': 'palette.png'}
        props = {'tree': {'kind': 'prop', 'role': 'tree',
                         'variants': {'v': {'png': 'res://kit/props/art/visible.png', 'foot': [0, 1]}},
                         'shadow': {'mask': {'png': 'res://kit/props/art/operation.png', 'offset': [-1, 0]}}}}
        self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
        self.write('game/kit/props/index.json', json.dumps(props))
        return terrain, props

    def test_bound_kit_fill_requires_context_despite_raw_gate_pass(self):
        self.kit_metadata()
        path = self.change_asset('game/kit/terrain/encoded.png')
        result = self.cli()
        manifest = self.read_bundle()
        row = next(r for r in manifest['assets'] if r['path'] == path)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(manifest['complete'])
        self.assertEqual(row['status'], 'incomplete')
        self.assertIsNone(row['counts'])
        self.assertEqual(row['command'], [])
        context = row['representation_inputs'][0]
        self.assertEqual(context['side'], 'after')
        self.assertEqual(context['classification'], 'context_required')
        self.assertEqual(context['representation'], 'palette_codes')
        self.assertEqual(context['owners'], ['lawn'])
        self.assertEqual(context['freshness'], 'not_assessed')
        self.assertTrue(context['obligations'])
        helper = Path(pr_sheet.__file__).with_name('kit_representation.py')
        self.assertEqual(manifest['representation_tool_sha256'], hashlib.sha256(helper.read_bytes()).hexdigest())
        metadata = context['metadata_inputs'][0]
        self.assertEqual(metadata['ref'], self.head)
        self.assertEqual((self.out / metadata['evidence']).read_bytes(),
                         (self.repo / metadata['path']).read_bytes())
        self.assertIn('context', (self.out / 'index.html').read_text().lower())

    def test_all_direct_terrain_bindings_are_incomplete_context(self):
        self.kit_metadata()
        for name in ('encoded', 'ops', 'decal', 'lut', 'noise', 'palette'):
            self.write('game/kit/terrain/' + name + '.png', png_bytes())
        self.commit('encoded terrain inputs')
        self.assertEqual(self.cli().returncode, 1)
        rows = self.read_bundle()['assets']
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r['status'] == 'incomplete' and not r['command'] for r in rows))
        self.assertEqual({r['representation_inputs'][0]['representation'] for r in rows},
                         {'palette_codes', 'transition_operations', 'decal_codes', 'palette_lut',
                          'noise_data', 'editor_palette'})

    def test_indexed_shadow_mask_is_context_and_physical_sprite_keeps_detector(self):
        self.kit_metadata()
        for name in ('operation', 'visible'):
            self.write('game/kit/props/art/' + name + '.png', png_bytes())
        self.commit('mask and physical sprite')
        self.assertEqual(self.cli().returncode, 1)
        rows = {r['path']: r for r in self.read_bundle()['assets']}
        mask = rows['game/kit/props/art/operation.png']
        physical = rows['game/kit/props/art/visible.png']
        self.assertEqual(mask['status'], 'incomplete')
        self.assertEqual(mask['representation_inputs'][0]['owners'], ['tree'])
        self.assertEqual(physical['status'], 'pass')
        self.assertTrue(physical['command'])
        self.assert_report_link(physical)

    def test_unbound_kit_png_and_indirect_tier_stay_incomplete(self):
        self.kit_metadata()
        for name in ('unbound', 'tiers'):
            self.write('game/kit/terrain/' + name + '.png', png_bytes())
        self.commit('unknown kit inputs')
        self.assertEqual(self.cli().returncode, 1)
        for row in self.read_bundle()['assets']:
            self.assertEqual(row['status'], 'incomplete')
            self.assertEqual(row['representation_inputs'][0]['classification'], 'unresolved')
            self.assertTrue(row['representation_inputs'][0]['errors'])

    def test_missing_malformed_and_duplicate_metadata_cannot_pass(self):
        for metadata in (None, b'[]', b'{broken',
                         b'{"materials":[],"materials":[],"transitions":[],"decals":{}}'):
            with self.subTest(metadata=metadata):
                if self.out.exists():
                    shutil.rmtree(self.out)
                path = self.repo / 'game/kit/terrain/manifest.json'
                if metadata is None:
                    path.unlink(missing_ok=True)
                else:
                    self.write('game/kit/terrain/manifest.json', metadata)
                self.change_asset('game/kit/terrain/encoded.png')
                self.assertEqual(self.cli().returncode, 1)
                row = self.read_bundle()['assets'][0]
                self.assertEqual(row['status'], 'incomplete')
                self.assertTrue(row['representation_inputs'][-1]['errors'])

    def test_bad_metadata_paths_types_and_ownership_are_fail_closed(self):
        for bad in ('../encoded.png', '/encoded.png', 'sub/encoded.png', 'bad\\encoded.png', True):
            with self.subTest(bad=bad):
                if self.out.exists():
                    shutil.rmtree(self.out)
                terrain, _ = self.kit_metadata()
                terrain['materials'][0]['fill'] = bad
                self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
                self.change_asset('game/kit/terrain/encoded.png')
                self.assertEqual(self.cli().returncode, 1)
                self.assertEqual(self.read_bundle()['assets'][0]['status'], 'incomplete')
        shutil.rmtree(self.out)
        terrain, _ = self.kit_metadata()
        terrain['materials'].append({'id': 'other', 'fill': 'encoded.png'})
        self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
        self.change_asset('game/kit/terrain/encoded.png')
        self.assertEqual(self.cli().returncode, 1)
        self.assertIn('ambiguous', str(self.read_bundle()['assets'][0]['representation_inputs']))

    def test_physical_and_operation_ownership_conflict_is_not_exempt(self):
        _, props = self.kit_metadata()
        props['tree']['shadow']['mask']['png'] = 'res://kit/props/art/visible.png'
        self.write('game/kit/props/index.json', json.dumps(props))
        self.change_asset('game/kit/props/art/visible.png')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['assets'][0]
        self.assertEqual(row['status'], 'incomplete')
        self.assertIn('ambiguous', str(row['representation_inputs']))

    def test_metadata_symlink_is_recorded_without_reading_external_target(self):
        external = self.root / 'outside-metadata.json'
        external.write_text('do not read or bundle this sentinel')
        path = self.repo / 'game/kit/terrain/manifest.json'
        path.parent.mkdir(parents=True)
        path.symlink_to(external)
        self.change_asset('game/kit/terrain/encoded.png')
        self.assertEqual(self.cli().returncode, 1)
        context = self.read_bundle()['assets'][0]['representation_inputs'][0]
        self.assertTrue(context['errors'])
        self.assertEqual(context['metadata_inputs'][0]['mode'], '120000')
        self.assertEqual((self.out / context['metadata_inputs'][0]['evidence']).read_text(), str(external))
        self.assertNotIn('do not read or bundle', (self.out / 'index.html').read_text())

    def test_metadata_anchor_types_are_not_silently_coerced(self):
        _, props = self.kit_metadata()
        props['tree']['shadow']['mask']['offset'] = [True, 0]
        self.write('game/kit/props/index.json', json.dumps(props))
        self.change_asset('game/kit/props/art/operation.png')
        self.assertEqual(self.cli().returncode, 1)
        self.assertTrue(self.read_bundle()['assets'][0]['representation_inputs'][0]['errors'])

    def test_data_rename_outside_kit_retains_before_metadata_obligation(self):
        self.kit_metadata()
        self.change_asset('game/kit/terrain/encoded.png')
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        self.git('mv', 'game/kit/terrain/encoded.png', 'game/zones/woodland/art/renamed.png')
        self.commit('data renamed to ordinary artwork path')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['assets'][0]
        self.assertEqual(row['status'], 'incomplete')
        self.assertEqual(row['representation_inputs'][0]['side'], 'before')
        self.assertEqual(row['representation_inputs'][0]['ref'], self.base)
        self.assertEqual(row['representation_inputs'][0]['path'], 'game/kit/terrain/encoded.png')
        self.assertEqual(row['representation_inputs'][0]['metadata_inputs'][0]['ref'], self.base)
        self.assertEqual(row['detector_status'], 'pass')
        self.assertTrue(row['command'])

    def test_data_rename_to_nonimage_retains_before_metadata(self):
        self.kit_metadata()
        self.change_asset('game/kit/terrain/encoded.png')
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        self.git('mv', 'game/kit/terrain/encoded.png', 'README-art.txt')
        self.commit('data renamed to nonimage suffix')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['assets'][0]
        self.assertEqual(row['status'], 'unsupported')
        self.assertEqual(row['representation_inputs'][0]['ref'], self.base)
        self.assertEqual(row['representation_inputs'][0]['representation'], 'palette_codes')

    def test_removed_data_retains_old_blob_and_metadata(self):
        self.kit_metadata()
        self.change_asset('game/kit/terrain/encoded.png')
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        self.git('rm', 'game/kit/terrain/encoded.png')
        self.commit('remove encoded input')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['assets'][0]
        self.assertEqual(row['status'], 'removed')
        self.assertTrue((self.out / row['evidence']['preview']).is_file())
        self.assertEqual(row['representation_inputs'][0]['ref'], self.base)

    def test_encoded_file_replaced_by_symlink_retains_both_context_sides(self):
        self.kit_metadata()
        self.change_asset('game/kit/terrain/encoded.png')
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        target = self.root / 'external-target.png'
        target.write_bytes(b'never read external image bytes')
        path = self.repo / 'game/kit/terrain/encoded.png'
        path.unlink()
        path.symlink_to(target)
        self.commit('encoded regular file becomes symlink')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['assets'][0]
        self.assertEqual(row['status'], 'unsupported')
        contexts = row['representation_inputs']
        self.assertEqual([c['side'] for c in contexts], ['before', 'after'])
        self.assertEqual([c['metadata_inputs'][0]['ref'] for c in contexts], [self.base, self.head])
        self.assertEqual(contexts[0]['image_inputs'][0]['mode'], '100644')
        image = contexts[1]['image_inputs'][0]
        self.assertEqual(image['mode'], '120000')
        self.assertEqual((self.out / image['evidence']).read_bytes(), str(target).encode())
        self.assertNotIn(b'never read external image bytes', b''.join(p.read_bytes() for p in self.out.rglob('*') if p.is_file()))

    def test_metadata_versions_are_pinned_separately_after_binding_changes(self):
        terrain, _ = self.kit_metadata()
        self.change_asset('game/kit/terrain/encoded.png')
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        terrain['materials'][0]['id'] = 'changed_owner'
        terrain['transitions'][0]['upper'] = 'changed_owner'
        self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
        self.write('game/kit/terrain/encoded.png', png_bytes(140))
        self.commit('change metadata and image')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['assets'][0]
        contexts = row['representation_inputs']
        self.assertEqual([c['owners'] for c in contexts], [['lawn'], ['changed_owner']])
        self.assertNotEqual(contexts[0]['metadata_inputs'][0]['blob'], contexts[1]['metadata_inputs'][0]['blob'])

    def test_stale_owner_binding_remains_unresolved_not_a_freshness_pass(self):
        terrain, _ = self.kit_metadata()
        terrain['transitions'][0]['upper'] = 'removed_owner'
        self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
        self.change_asset('game/kit/terrain/encoded.png')
        self.assertEqual(self.cli().returncode, 1)
        context = self.read_bundle()['assets'][0]['representation_inputs'][0]
        self.assertEqual(context['classification'], 'unresolved')
        self.assertEqual(context['freshness'], 'not_assessed')
        self.assertTrue(context['errors'])

    def test_context_ownership_is_escaped_in_html_and_retained_in_manifest(self):
        terrain, _ = self.kit_metadata()
        owner = '<owner&"fixture">'
        terrain['materials'][0]['id'] = owner
        terrain['transitions'][0]['upper'] = owner
        self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
        self.change_asset('game/kit/terrain/encoded.png')
        self.assertEqual(self.cli().returncode, 1)
        self.assertEqual(self.read_bundle()['assets'][0]['representation_inputs'][0]['owners'], [owner])
        html = (self.out / 'index.html').read_text()
        self.assertNotIn(owner, html)
        self.assertIn('&lt;owner&amp;', html)

    def test_context_evidence_link_label_escapes_committed_filename(self):
        terrain, _ = self.kit_metadata()
        name = '<img onerror="fixture()">.png'
        terrain['materials'][0]['fill'] = name
        self.write('game/kit/terrain/manifest.json', json.dumps(terrain))
        self.change_asset('game/kit/terrain/' + name)
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['assets'][0]['path'], 'game/kit/terrain/' + name)
        html = (self.out / 'index.html').read_text()
        self.assertNotIn(name, html)
        self.assertIn('&lt;img onerror=', html)

    def test_tampered_pinned_context_evidence_is_not_rewritten_or_accepted(self):
        self.kit_metadata()
        self.write('game/kit/terrain/encoded.png', png_bytes())
        self.commit('existing committed metadata and image')
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        self.write('game/kit/terrain/encoded.png', png_bytes(140))
        self.write('game/zones/woodland/art/later.png', png_bytes())
        self.commit('changed data then ordinary gate')
        self.assertEqual(self.cli(mode='metadata_tamper').returncode, 1)
        row = next(r for r in self.read_bundle()['assets'] if r['path'].startswith('game/kit/'))
        self.assertTrue(any('changed' in e for e in row['errors']))
        evidence = row['representation_inputs'][0]['metadata_inputs'][0]['evidence']
        self.assertEqual((self.out / evidence).read_bytes(), b'fixture changed bundled context evidence')

    def test_misleading_external_names_still_run_ordinary_gate(self):
        for name in ('fill_lawn', 'shadow_tree', 'decal_tuft'):
            self.write('game/zones/woodland/art/' + name + '.png', png_bytes())
        self.commit('ordinary artwork with data-like names')
        self.assertEqual(self.cli().returncode, 0)
        self.assertTrue(all(r['status'] == 'pass' and r['command'] for r in self.read_bundle()['assets']))

    def test_kit_named_fixture_stays_fixture_but_move_into_production_does_not(self):
        self.write('game/test/fixtures/kit/fill_lawn.png', png_bytes())
        self.commit('test evidence')
        self.assertEqual(self.cli().returncode, 0)
        self.assertEqual(self.read_bundle()['scope'], 'test_evidence')
        shutil.rmtree(self.out)
        self.base = self.head
        self.git('branch', '-f', 'base', self.base)
        self.write('game/kit/terrain/.keep', '')
        self.git('mv', 'game/test/fixtures/kit/fill_lawn.png', 'game/kit/terrain/fill_lawn.png')
        self.commit('fixture moved into production')
        self.assertEqual(self.cli().returncode, 1)
        self.assertEqual(self.read_bundle()['assets'][0]['status'], 'incomplete')

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

    def test_town_kit_and_cast_sources_cannot_be_no_art(self):
        paths = [
            'docs/vision/research/blockout/towns/cinderwick.json',
            'game/data/kit/concepts/frontier_lava_run.json',
            'art/characters/bodies/ashe.json',
            'docs/vision/characters/designs/ashe.json',
            'docs/characters/cast-retiming-60hz.json',
            'scripts/characters/review_cast_v2.py',
            'game/assets/characters/ashe/manifest.json',
            'castwork/ashe/rig.py',
            'game/data/progression/ashe.json',
            'docs/codex/fire-country-kit.md',
        ]
        for path in paths:
            self.write(path, '{"schema":"deliberately missing-or-wrong"}\n')
        self.commit('production source categories')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'], [])
        rows = {row['path']: row for row in manifest['other_changes']}
        self.assertEqual(set(rows), set(paths))
        for path in paths:
            row = rows[path]
            self.assertEqual(row['status'], 'source_only')
            self.assertIn(row['category'], ('town_plan', 'kit_concept', 'cast_source'))
            self.assertEqual(row['inputs'][0]['side'], 'after')
            self.assertEqual(row['inputs'][0]['ref'], self.head)
            self.assertEqual(row['inputs'][0]['sha256'], hashlib.sha256(
                (self.repo / path).read_bytes()).hexdigest())
            source = self.out / row['inputs'][0]['evidence']
            self.assertEqual(source.read_bytes(), (self.repo / path).read_bytes())
            self.assertEqual(manifest['files'][row['inputs'][0]['evidence']],
                             row['inputs'][0]['sha256'])

    def test_blockout_generators_are_source_only_with_exact_bytes(self):
        paths = ['docs/vision/research/blockout/' + name for name in
                 ('towns55.py', 'town_plans.py', 'geo55.py')]
        for path in paths:
            self.write(path, b'# production map authoring source\nnot valid Python\xff')
        self.commit('known map generators')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'], [])
        self.assertEqual(len(manifest['other_changes']), 3)
        for row in manifest['other_changes']:
            self.assertEqual((row['status'], row['category']), ('source_only', 'art_source'))
            source = row['inputs'][0]
            data = (self.repo / row['path']).read_bytes()
            self.assertEqual(source['ref'], self.head)
            self.assertEqual(source['blob'], self.git('rev-parse', self.head + ':' + row['path']))
            self.assertEqual(source['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual((self.out / source['evidence']).read_bytes(), data)

    def test_blockout_generator_plus_passing_png_remains_incomplete(self):
        path = 'docs/vision/research/blockout/towns55.py'
        self.write(path, '# pinned generator source\n')
        self.change_asset()
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'][0]['status'], 'pass')
        row = manifest['other_changes'][0]
        self.assertEqual((row['path'], row['status'], row['category']),
                         (path, 'source_only', 'art_source'))
        source = row['inputs'][0]
        self.assertEqual(source['ref'], self.head)
        self.assertEqual((self.out / source['evidence']).read_bytes(), (self.repo / path).read_bytes())
        self.assertEqual(source['sha256'], hashlib.sha256((self.repo / path).read_bytes()).hexdigest())

    def test_nonimage_source_renamed_to_png_keeps_source_and_raster_evidence(self):
        old, new = 'game/data/kit/concepts/malformed-source.json', 'assets/recovered.png'
        data = png_bytes()
        self.write(old, data)
        self.base = self.commit('malformed known production source with PNG bytes')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / 'assets').mkdir()
        self.git('mv', old, new)
        self.commit('rename production source to PNG')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['changes'][0]['status'], 'R100')
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['manual_review'], 'not_assessed')
        self.assertEqual(manifest['assets'][0]['status'], 'pass')
        self.assertEqual(manifest['assets'][0]['path'], new)
        self.assertEqual(len(manifest['other_changes']), 1)
        row = manifest['other_changes'][0]
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual([v['side'] for v in row['inputs']], ['before', 'after'])
        self.assertEqual([v['path'] for v in row['inputs']], [old, new])
        self.assertEqual([v['ref'] for v in row['inputs']], [self.base, self.head])
        for source in row['inputs']:
            self.assertEqual(source['mode'], '100644')
            self.assertEqual(source['blob'], self.git('rev-parse', source['ref'] + ':' + source['path']))
            self.assertEqual(source['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual((self.out / source['evidence']).read_bytes(), data)

    def test_regional_kit_requirements_cannot_be_no_art(self):
        paths = ['docs/codex/' + name + '-kit.md' for name in
                 ('frostline', 'brackens', 'cogsworth', 'lull')]
        for path in paths:
            self.write(path, '# Unapproved regional requirements\n' + path + '\n')
        self.commit('regional kit requirements')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'], [])
        rows = {row['path']: row for row in manifest['other_changes']}
        self.assertEqual(set(rows), set(paths))
        for path in paths:
            row = rows[path]
            self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
            self.assertEqual([v['side'] for v in row['inputs']], ['after'])
            version = row['inputs'][0]
            self.assertEqual(version['ref'], self.head)
            self.assertEqual(version['blob'], self.git('rev-parse', self.head + ':' + path))
            raw = (self.repo / path).read_bytes()
            self.assertEqual(version['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual((self.out / version['evidence']).read_bytes(), raw)
            self.assertEqual(manifest['files'][version['evidence']], version['sha256'])

    def test_future_regional_kit_keeps_raw_bytes_and_escaped_name(self):
        path = 'docs/codex/<mist&isles>-kit.md'
        raw = b'Unapproved requirements; raw bytes are evidence, not Markdown validation.\xff\n'
        self.write(path, raw)
        self.commit('future kit requirements with unusual source bytes')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        row = manifest['other_changes'][0]
        self.assertEqual(row['category'], 'kit_concept')
        self.assertEqual((self.out / row['inputs'][0]['evidence']).read_bytes(), raw)
        page = (self.out / 'index.html').read_text()
        self.assertIn('&lt;mist&amp;isles&gt;-kit.md', page)
        self.assertNotIn('<mist&isles>', page)

    def test_kit_requirement_namespace_does_not_capture_other_documentation(self):
        paths = ['docs/codex/kit-notes.md', 'docs/codex/frostline-kit.md.backup',
                 'docs/codex/notes/lull-kit.md', 'docs/reference/brackens-kit.md',
                 'docs/codex/bank-edge-diagnosis.md',
                 'docs/codex/painted-structure-context-plan.md.backup',
                 'docs/codex/notes/painted-structure-context-plan.md',
                 'docs/reference/painted-structure-context-plan.md']
        for path in paths:
            self.write(path, 'Ordinary documentation outside the requirements-file namespace.\n')
        self.commit('other documentation')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'no_art')
        self.assertTrue(manifest['complete'])
        self.assertEqual({row['path'] for row in manifest['other_changes']}, set(paths))
        self.assertTrue(all(row['status'] == 'not_art' for row in manifest['other_changes']))

    def test_painted_structure_context_proposal_cannot_be_no_art(self):
        path = 'docs/codex/painted-structure-context-plan.md'
        raw = b'# Unapproved context proposal\nSix bridge faults remain.\xff\n'
        self.write(path, raw)
        self.commit('painted structure context proposal')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['exit_code'], 1)
        self.assertEqual(manifest['assets'], [])
        self.assertEqual(manifest['scenes'], [])
        self.assertIsNone(manifest['preflight'])
        row = manifest['other_changes'][0]
        self.assertEqual((row['path'], row['status'], row['category']),
                         (path, 'source_only', 'kit_concept'))
        version = row['inputs'][0]
        self.assertEqual((version['side'], version['ref'], version['path']),
                         ('after', self.head, path))
        self.assertEqual(version['blob'], self.git('rev-parse', self.head + ':' + path))
        self.assertEqual(version['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual((self.out / version['evidence']).read_bytes(), raw)
        self.assertEqual(manifest['files'][version['evidence']], version['sha256'])

    def test_context_proposal_rename_outside_docs_keeps_both_source_versions(self):
        old = 'docs/codex/painted-structure-context-plan.md'
        new = 'notes/retained-context-proposal.txt'
        raw = b'Unapproved painted structure context; no placement acceptance.\n'
        self.write(old, raw)
        self.base = self.commit('context proposal baseline')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / 'notes').mkdir()
        self.git('mv', old, new)
        self.commit('context proposal renamed outside docs')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        row = manifest['other_changes'][0]
        self.assertEqual(row['change']['status'], 'R100')
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual([v['path'] for v in row['inputs']], [old, new])
        self.assertEqual([v['ref'] for v in row['inputs']], [self.base, self.head])
        for version in row['inputs']:
            self.assertEqual((self.out / version['evidence']).read_bytes(), raw)

    def test_deleted_context_proposal_retains_missing_head_source_obligation(self):
        path = 'docs/codex/painted-structure-context-plan.md'
        raw = b'Context proposal source retained for deletion review.\n'
        self.write(path, raw)
        self.base = self.commit('context proposal before deletion')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / path).unlink()
        self.commit('remove context proposal')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        row = manifest['other_changes'][0]
        self.assertEqual(row['change']['status'], 'D')
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual([v['side'] for v in row['inputs']], ['before'])
        self.assertEqual(row['inputs'][0]['ref'], self.base)
        self.assertEqual((self.out / row['inputs'][0]['evidence']).read_bytes(), raw)

    def test_context_proposal_fixture_renamed_into_production_loses_exemption(self):
        old = 'tests/fixtures/painted-structure-context-plan.md'
        new = 'docs/codex/painted-structure-context-plan.md'
        raw = b'Invalid proposal fixture becomes production review input.\xff\n'
        self.write(old, raw)
        self.base = self.commit('context proposal fixture baseline')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / new).parent.mkdir(parents=True)
        self.git('mv', old, new)
        self.commit('fixture moved into known proposal path')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        row = manifest['other_changes'][0]
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual([v['path'] for v in row['inputs']], [old, new])
        for version in row['inputs']:
            self.assertEqual((self.out / version['evidence']).read_bytes(), raw)

    def test_context_proposal_named_fixture_stays_test_evidence(self):
        path = 'tests/fixtures/docs/codex/painted-structure-context-plan.md'
        raw = b'Invalid fixture, not a production proposal.\xff\n'
        self.write(path, raw)
        self.commit('known proposal basename inside fixture namespace')
        self.assertEqual(self.cli().returncode, 0)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'test_evidence')
        self.assertTrue(manifest['complete'])
        self.assertEqual(manifest['assets'], [])
        self.assertEqual(manifest['scenes'], [])
        row = manifest['other_changes'][0]
        self.assertEqual((row['status'], row['category']), ('test_evidence', 'test_fixture'))
        self.assertEqual((self.out / row['inputs'][0]['evidence']).read_bytes(), raw)

    def test_context_proposal_renamed_to_png_retains_source_obligation(self):
        old = 'docs/codex/painted-structure-context-plan.md'
        new = 'game/zones/woodland/art/recovered-context.png'
        raw = png_bytes()  # Malformed proposal bytes still require source review.
        self.write(old, raw)
        self.base = self.commit('context proposal with malformed PNG bytes')
        self.git('branch', '-f', 'base', self.base)
        self.git('mv', old, new)
        self.commit('context proposal renamed to PNG')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'][0]['status'], 'pass')
        row = manifest['other_changes'][0]
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual([v['path'] for v in row['inputs']], [old, new])
        self.assertEqual([v['ref'] for v in row['inputs']], [self.base, self.head])
        for version in row['inputs']:
            self.assertEqual((self.out / version['evidence']).read_bytes(), raw)

    def test_regional_kit_source_keeps_passing_raster_bundle_incomplete(self):
        path = 'docs/codex/brackens-kit.md'
        self.write(path, '# Unapproved Brackens requirements\n')
        image = self.change_asset()
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'][0]['path'], image)
        self.assertEqual(manifest['assets'][0]['status'], 'pass')
        row = next(row for row in manifest['other_changes'] if row['path'] == path)
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual((self.out / row['inputs'][0]['evidence']).read_bytes(),
                         (self.repo / path).read_bytes())

    def test_regional_kit_renamed_to_png_keeps_before_source_obligation(self):
        old = 'docs/codex/frostline-kit.md'
        new = 'game/zones/woodland/art/recovered-regional.png'
        raw = png_bytes()
        self.write(old, raw)  # Deliberately malformed requirements are still production source.
        self.base = self.commit('regional source baseline')
        self.git('branch', '-f', 'base', self.base)
        self.git('mv', old, new)
        self.commit('regional source moved to a PNG')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['assets'][0]['status'], 'pass')
        row = next(row for row in manifest['other_changes'] if row['status'] == 'source_only')
        self.assertEqual(row['category'], 'kit_concept')
        self.assertEqual(row['change']['old_path'], old)
        self.assertEqual([v['side'] for v in row['inputs']], ['before', 'after'])
        self.assertEqual([v['ref'] for v in row['inputs']], [self.base, self.head])
        self.assertEqual([v['path'] for v in row['inputs']], [old, new])
        for version in row['inputs']:
            self.assertEqual(version['blob'], self.git('rev-parse', self.base + ':' + old))
            self.assertEqual((self.out / version['evidence']).read_bytes(), raw)

    def test_regional_kit_rename_and_delete_keep_exact_source_versions(self):
        old = 'docs/codex/lull-kit.md'
        removed = 'docs/codex/cogsworth-kit.md'
        new = 'notes/retained-lull-proposal.txt'
        self.write(old, 'Lull source content distinct from the removed requirements.\n')
        self.write(removed, 'Cogsworth requirements source before deletion.\n')
        self.base = self.commit('regional requirements baseline')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / 'notes').mkdir()
        self.git('mv', old, new)
        (self.repo / removed).unlink()
        self.commit('move and remove regional requirements')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'source_only')
        self.assertFalse(manifest['complete'])
        rows = {row['path']: row for row in manifest['other_changes']}
        self.assertEqual(rows[new]['category'], 'kit_concept')
        self.assertEqual([v['side'] for v in rows[new]['inputs']], ['before', 'after'])
        self.assertEqual([v['path'] for v in rows[new]['inputs']], [old, new])
        self.assertEqual([v['side'] for v in rows[removed]['inputs']], ['before'])
        self.assertEqual(rows[removed]['inputs'][0]['path'], removed)
        for row in rows.values():
            for version in row['inputs']:
                raw = subprocess.run(['git', 'show', version['ref'] + ':' + version['path']],
                                     cwd=self.repo, env=self.env, check=True,
                                     capture_output=True, timeout=15).stdout
                self.assertEqual((self.out / version['evidence']).read_bytes(), raw)

    def test_regional_kit_fixture_rename_into_production_loses_exemption(self):
        old = 'tests/fixtures/frostline-kit.md'
        new = 'docs/codex/frostline-kit.md'
        self.write(old, 'Intentionally invalid requirements fixture.\n')
        self.base = self.commit('regional fixture baseline')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / new).parent.mkdir(parents=True)
        self.git('mv', old, new)
        self.commit('regional fixture moved into production requirements')
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        row = self.read_bundle()['other_changes'][0]
        self.assertEqual((row['status'], row['category']), ('source_only', 'kit_concept'))
        self.assertEqual([v['path'] for v in row['inputs']], [old, new])

    def test_regional_kit_named_fixture_stays_test_evidence(self):
        path = 'tests/fixtures/docs/codex/frostline-kit.md'
        self.write(path, b'Intentionally invalid requirements fixture.\xff\n')
        self.commit('nested kit-named fixture')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'test_evidence')
        self.assertEqual(manifest['assets'], [])
        row = manifest['other_changes'][0]
        self.assertEqual((row['status'], row['category']), ('test_evidence', 'test_fixture'))
        self.assertEqual((self.out / row['inputs'][0]['evidence']).read_bytes(),
                         (self.repo / path).read_bytes())

    def test_malformed_production_source_and_fixture_named_subdirectory_stay_visible(self):
        path = 'game/data/kit/concepts/fixtures/invalid.json'
        self.write(path, b'not-json\xff')
        self.commit('malformed source is still review source')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['other_changes'][0]
        self.assertEqual(row['status'], 'source_only')
        self.assertEqual(row['category'], 'kit_concept')
        self.assertEqual(row['inputs'][0]['sha256'], hashlib.sha256(b'not-json\xff').hexdigest())

    def test_deliberately_invalid_fixture_images_are_test_evidence(self):
        paths = ['game/test/fixtures/kit/bad.png',
                 'game/kit/schema/invalid/bad.json',
                 'scripts/review/fixtures/cast-invalid.svg']
        for path in paths:
            self.write(path, 'intentionally invalid test input\n')
        self.commit('invalid fixtures')
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'test_evidence')
        self.assertEqual(manifest['assets'], [])
        self.assertTrue(all(row['status'] == 'test_evidence'
                            for row in manifest['other_changes']))
        self.assertTrue(all(row['inputs'] for row in manifest['other_changes']))
        self.assertIn('not a production art pass', (self.out / 'index.html').read_text())

    def test_explicit_fixture_asset_cannot_be_reclassified_as_production_art(self):
        path = 'game/test/fixtures/kit/bad.png'
        self.write(path, 'not a PNG on purpose')
        self.commit('fixture asset context')
        result = self.cli('--asset', path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'test_evidence')
        self.assertEqual(manifest['assets'], [])
        self.assertEqual(len(manifest['other_changes']), 1)

    def test_source_rename_and_delete_keep_before_and_after_provenance(self):
        old = 'docs/vision/research/blockout/towns/example.json'
        self.write(old, '{"original":true}\n')
        self.base = self.commit('town baseline')
        self.git('branch', '-f', 'base', self.base)
        new = 'notes/moved source.txt'
        (self.repo / 'notes').mkdir()
        self.git('mv', old, new)
        self.commit('move town outside bounded directory')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['other_changes'][0]
        self.assertEqual(row['category'], 'town_plan')
        self.assertEqual([v['side'] for v in row['inputs']], ['before', 'after'])
        self.assertEqual(row['inputs'][0]['ref'], self.base)
        self.assertEqual(row['inputs'][1]['ref'], self.head)
        self.assertEqual(row['inputs'][0]['blob'], row['inputs'][1]['blob'])
        shutil.rmtree(self.out)
        self.git('checkout', '-b', 'deleted-town', self.base)
        (self.repo / old).unlink()
        self.commit('remove production source')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['other_changes'][0]
        self.assertEqual(row['category'], 'town_plan')
        self.assertEqual([v['side'] for v in row['inputs']], ['before'])

    def test_fixture_rename_into_production_cannot_exempt_source(self):
        old = 'game/test/fixtures/example.json'
        new = 'game/data/kit/concepts/example.json'
        self.write(old, '{"not_approved":true}\n')
        self.base = self.commit('fixture baseline')
        self.git('branch', '-f', 'base', self.base)
        (self.repo / new).parent.mkdir(parents=True)
        self.git('mv', old, new)
        self.commit('fixture promoted without approval')
        self.assertEqual(self.cli().returncode, 1)
        row = self.read_bundle()['other_changes'][0]
        self.assertEqual(row['status'], 'source_only')
        self.assertEqual(row['category'], 'kit_concept')

    def test_cast_png_still_runs_raster_gate(self):
        path = self.change_asset('game/assets/characters/ashe/sheets/idle_S.png')
        self.assertEqual(self.cli().returncode, 0)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(manifest['assets'][0]['path'], path)
        self.assertEqual(manifest['assets'][0]['status'], 'pass')

    def test_mixed_raster_and_source_cannot_hide_missing_source_coverage(self):
        self.write('docs/vision/research/blockout/towns/example.json', '{}\n')
        self.change_asset()
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(manifest['assets'][0]['status'], 'pass')
        self.assertFalse(manifest['complete'])
        self.assertEqual(manifest['other_changes'][0]['status'], 'source_only')

    def test_source_classification_and_provenance_are_deterministic_and_escaped(self):
        path = 'docs/vision/research/blockout/towns/<odd&town>.json'
        self.write(path, '{}\n')
        self.commit('unusual production name')
        self.assertEqual(self.cli().returncode, 1)
        first = self.read_bundle()
        body = (self.out / 'index.html').read_text()
        self.assertIn('&lt;odd&amp;town&gt;.json', body)
        self.assertNotIn('<odd&town>', body)
        shutil.rmtree(self.out)
        self.assertEqual(self.cli().returncode, 1)
        second = self.read_bundle()
        self.assertEqual(first['other_changes'], second['other_changes'])
        self.assertEqual(first['changes'], second['changes'])
        self.assertEqual(first['head_tree'], second['head_tree'])

    def test_source_and_fixture_symlinks_are_incomplete_without_external_reads(self):
        target = self.root / 'external-secret.json'
        target.write_text('external bytes must not become input evidence')
        paths = ['game/test/fixtures/linked.json',
                 'game/data/kit/concepts/linked.json']
        for path in paths:
            file = self.repo / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.symlink_to(target)
        self.commit('nonregular source and fixture')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertFalse(manifest['complete'])
        for row in manifest['other_changes']:
            self.assertTrue(row['errors'])
            self.assertEqual(row['inputs'][0]['mode'], '120000')
            self.assertEqual(row['inputs'][0]['sha256'], hashlib.sha256(
                str(target).encode()).hexdigest())
        self.assertNotIn('external bytes must not', (self.out / 'manifest.json').read_text())

    def test_fixture_modification_attests_both_versions_and_nonfixture_png_is_not_exempt(self):
        path = 'game/test/fixtures/town.json'
        self.write(path, '{"old":true}\n')
        self.base = self.commit('old fixture')
        self.git('branch', '-f', 'base', self.base)
        self.write(path, '{"new":true}\n')
        self.write('game/assets/characters/fixtures/not-production.png', 'invalid PNG')
        self.commit('fixture change and misleading production name')
        self.assertEqual(self.cli().returncode, 1)
        manifest = self.read_bundle()
        self.assertEqual(manifest['scope'], 'detector_evidence')
        self.assertEqual(manifest['assets'][0]['status'], 'incomplete')
        row = manifest['other_changes'][0]
        self.assertEqual(row['status'], 'test_evidence')
        self.assertEqual([v['side'] for v in row['inputs']], ['before', 'after'])
        self.assertNotEqual(row['inputs'][0]['blob'], row['inputs'][1]['blob'])

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
        self.assertEqual(manifest['scope'], 'source_only')
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
        self.assertEqual(manifest['scope'], 'source_only')
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


class OwnedAdapterControls(unittest.TestCase):
    """Y47 tiny adapter controls: SOURCE PREPARED, NOT EXECUTED."""

    def test_managed_git_keeps_binary_argv_environment_and_parent(self):
        from unittest import mock
        from .owned_broker import Broker
        with tempfile.TemporaryDirectory(prefix='owned-git-') as temporary:
            root = Path(temporary)
            fake = root / 'git'
            fake.write_text('#!' + sys.executable + '\nimport os,sys,json\n'
                            "sys.stdout.buffer.write(json.dumps({'argv':sys.argv[1:],'parent':os.getppid(),"
                            "'literal':os.environ['GIT_NO_REPLACE_OBJECTS']}).encode())\n")
            fake.chmod(0o700)
            with Broker(root / 'broker') as broker:
                env = broker.environment(dict(os.environ, PATH=str(root)))
                with mock.patch.dict(os.environ, env, clear=True):
                    value = json.loads(pr_sheet._git(root, 'for-each-ref'))
                self.assertEqual(value['argv'], ['--literal-pathspecs', '-C', str(root), 'for-each-ref'])
                self.assertEqual(value['parent'], os.getpid())
                self.assertEqual(value['literal'], '1')

    def test_managed_detector_exit_one_keeps_logs_hashes_and_wait_receipt(self):
        from unittest import mock
        from .owned_broker import Broker
        with tempfile.TemporaryDirectory(prefix='owned-command-') as temporary:
            root = Path(temporary)
            with Broker(root / 'broker') as broker:
                with mock.patch.dict(os.environ, broker.environment(), clear=True):
                    result = pr_sheet._command(root, root, root / 'logs',
                                               [sys.executable, '-c', "import sys;print('finding');print('detail',file=sys.stderr);sys.exit(1)"],
                                               timeout=3)
                self.assertEqual(result['returncode'], 1)
                self.assertIsNone(result['error'])
                self.assertEqual((root / result['stdout']).read_bytes(), b'finding\n')
                self.assertEqual(result['stdout_sha256'], hashlib.sha256(b'finding\n').hexdigest())
                self.assertTrue(result['owned_receipt']['waited'])

    def test_managed_python_runner_binds_subject_paths_not_subject_code(self):
        from unittest import mock
        from . import owned_launch
        from .owned_broker import Broker
        with tempfile.TemporaryDirectory(prefix='owned-tool-routing-') as temporary:
            root = Path(temporary)
            subject, tools = root / 'subject', root / 'reviewed-tools'
            marker = root / 'wrong-runner'
            for base in (subject, tools):
                package = base / 'scripts' / 'review'
                package.mkdir(parents=True)
                (base / 'scripts' / '__init__.py').write_text('')
                (package / '__init__.py').write_text('')
            package = tools / 'scripts' / 'review'
            helper = package / 'owned_launch.py'
            helper.write_text(Path(owned_launch.__file__).read_text())
            (package / 'core.py').write_text("REPO = 'WRONG_TOOL_DATA_ROOT'\n")
            (package / 'scene.py').write_text("from .core import REPO\nfrom pathlib import Path\nGAME = str(Path(REPO) / 'game')\n")
            producer = ("from .core import REPO\nfrom .scene import GAME\nfrom . import owned_launch\n"
                        "import json,os,sys\nfrom pathlib import Path\n"
                        "engine = owned_launch.run([sys.executable, '-c', 'import os,json;print(json.dumps(dict(cwd=os.getcwd(),parent=os.getppid())))'], cwd=REPO, text=True, timeout=3)\n"
                        "print(json.dumps(dict(repo=REPO,game=GAME,catalogue=str(Path(REPO)/'art'/'catalogue'),engine=json.loads(engine.stdout),argv=sys.argv[1:])))\n")
            for module in ('run', 'assets'):
                (package / (module + '.py')).write_text(producer)
                (subject / 'scripts' / 'review' / (module + '.py')).write_text(
                    f"from pathlib import Path;Path({str(marker)!r}).touch()")
            with Broker(root / 'broker') as broker:
                with mock.patch.dict(os.environ, broker.environment(), clear=True), \
                        mock.patch.object(pr_sheet, 'REPO', tools), \
                        mock.patch.object(owned_launch, '__file__', str(helper)):
                    for module in ('run', 'assets'):
                        result = pr_sheet._command(subject, root, root / module,
                                                   [sys.executable, '-m', 'scripts.review.' + module, 'literal space'], timeout=5)
                        self.assertEqual(result['returncode'], 0, result['stderr_text'])
                        value = json.loads(result['stdout_text'])
                        self.assertEqual(value['repo'], str(subject))
                        self.assertEqual(value['game'], str(subject / 'game'))
                        self.assertEqual(value['catalogue'], str(subject / 'art' / 'catalogue'))
                        self.assertEqual(value['engine'], dict(cwd=str(subject), parent=os.getpid()))
                        self.assertEqual(value['argv'], ['literal space'])
                        self.assertEqual(result['command'][1:3], ['-I', '-B'])
                        self.assertIn(str(subject), result['command'])
            self.assertFalse(marker.exists())

    def test_managed_timeout_remains_124_and_partial_logs_are_retained(self):
        from unittest import mock
        from .owned_broker import Broker
        with tempfile.TemporaryDirectory(prefix='owned-timeout-') as temporary:
            root = Path(temporary)
            with Broker(root / 'broker') as broker:
                with mock.patch.dict(os.environ, broker.environment(), clear=True):
                    result = pr_sheet._command(root, root, root / 'logs',
                                               [sys.executable, '-c', "import time;print('prefix',flush=True);time.sleep(10)"],
                                               timeout=0.3)
                self.assertEqual(result['returncode'], 124)
                self.assertIn('timed out', result['error'])
                self.assertIn('prefix', result['stdout_text'])

    def test_managed_engine_error_at_zero_exit_is_still_rejected(self):
        from unittest import mock
        from .owned_broker import Broker
        from . import run
        with tempfile.TemporaryDirectory(prefix='owned-engine-log-') as temporary:
            root = Path(temporary)
            with Broker(root / 'broker') as broker:
                env = broker.environment(dict(os.environ, GODOT=sys.executable, DISPLAY=':CONTROL_ONLY'))
                with mock.patch.object(run, 'REPO', root):
                    with self.assertRaises(run.RenderError):
                        run._godot_command([sys.executable, '-c', "print('SCRIPT ERROR: fake engine')"],
                                           env, str(root / 'engine.log'), 3)
                self.assertIn('SCRIPT ERROR', (root / 'engine.log').read_text())

    def test_managed_missing_inputs_and_stripped_credentials_never_launch_locally(self):
        from unittest import mock
        from . import run
        from .owned_launch import SOCKET_ENV, TOKEN_ENV
        env = {SOCKET_ENV: '/absent/socket', TOKEN_ENV: 'control-only'}
        with tempfile.TemporaryDirectory(prefix='owned-refusal-') as temporary:
            root = Path(temporary)
            with mock.patch.dict(os.environ, env, clear=True), \
                    mock.patch('subprocess.run') as local_run, mock.patch('subprocess.Popen') as local_popen:
                with self.assertRaises(pr_sheet.ReviewError):
                    pr_sheet._import_project(root, root)
                with self.assertRaises(run.RenderError):
                    run.godot_bin()
                with self.assertRaises(run.RenderError):
                    run.start_xvfb()
                with self.assertRaises(run.RenderError):
                    run._godot_command(['no-local-engine'], {'GODOT': 'fake', 'DISPLAY': ':CONTROL_ONLY'},
                                       str(root / 'refusal.log'), 1)
                local_run.assert_not_called()
                local_popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()

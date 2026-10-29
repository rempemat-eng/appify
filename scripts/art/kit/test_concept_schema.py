"""Corpus regressions for W0 concepts combined with W1's existing semantic validator.

Run: python3 -m unittest scripts.art.kit.test_concept_schema -v
The 129 records are the unchanged W0 review corpus, not runtime pieces or art approval.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.art.kit import schema as S


ROOT = Path(S.ROOT)
CONCEPTS = ROOT / 'game/data/kit/concepts'


def runtime_allocations(value, path='$'):
    """Audit W0's no-allocation promise, not a new global piece-schema restriction."""
    found = []
    if isinstance(value, dict):
        for key, nested in value.items():
            location = '%s.%s' % (path, key)
            if key in ('png', 'material_id', 'painter', 'module', 'fn', 'paint', 'texture'):
                found.append(location)
            found.extend(runtime_allocations(nested, location))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found.extend(runtime_allocations(nested, '%s[%d]' % (path, index)))
    return found


class ConceptCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(CONCEPTS.glob('*.json'))
        cls.records = {path: json.loads(path.read_bytes()) for path in cls.paths}

    def test_actual_129_record_corpus_passes_without_runtime_allocation(self):
        self.assertEqual(len(self.paths), 129)
        self.assertEqual(S.check([str(path) for path in self.paths]),
                         {str(path): [] for path in self.paths})
        self.assertEqual(sum(p['kind'] == 'terrain' for p in self.records.values()), 22)
        self.assertEqual(sum(p['kind'] == 'transition' for p in self.records.values()), 8)
        for path, record in self.records.items():
            with self.subTest(piece=path.stem):
                self.assertEqual(record['id'], path.stem)
                self.assertEqual(record['approval']['state'], 'concept')
                self.assertNotIn('terrain', record)
                self.assertNotIn('transition', record)
                self.assertLessEqual(set(record.get('rendering', {})), {'contact_ao', 'cast_shadow'})
                self.assertEqual(runtime_allocations(record), [])

    def test_corpus_allocation_audit_catches_nested_assets_without_changing_schema(self):
        record = copy.deepcopy(next(p for p in self.records.values() if p.get('variants')))
        record['variants'][0]['png'] = 'res://fixture-only.png'
        self.assertEqual(S.errors(record, S.load_schema()) + S.semantic(record), [])
        self.assertEqual(runtime_allocations(record), ['$.variants[0].png'])

    def test_actual_corpus_agrees_with_independent_jsonschema(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest('jsonschema not installed; independent structural proof not supplied')
        schema = S.load_schema()
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for path, record in self.records.items():
            with self.subTest(piece=path.stem):
                self.assertEqual(list(validator.iter_errors(record)), [])
                self.assertEqual(S.errors(record, schema), [])
        original = next(iter(self.records.values()))
        for key, value in [('approval', []), ('id', []), ('kind', 'unknown-kind'),
                           ('terrain', {'typo': True}), ('unexpected_key', 'typo')]:
            record = {**original, key: value}
            with self.subTest(malformed=key):
                self.assertTrue(list(validator.iter_errors(record)))
                self.assertTrue(S.errors(record, schema))

    def test_every_deferred_runtime_block_remains_required_after_concept(self):
        deferred = [p for p in self.records.values() if p['kind'] in ('terrain', 'transition')]
        self.assertEqual(len(deferred), 30)
        for original in deferred:
            for state in ('candidate', 'gated', 'approved', 'rejected', 'retired'):
                with self.subTest(piece=original['id'], state=state):
                    record = copy.deepcopy(original)
                    record['approval'] = {'state': state}
                    self.assertTrue(any('"%s" block' % record['kind'] in message
                                        for message in S.semantic(record)))
                    with self.assertRaisesRegex(ValueError, 'needs a'):
                        S.migrate_piece(record)
                    self.assertEqual(original['approval']['state'], 'concept')

    def test_current_schema_migration_preserves_all_concept_bytes_and_mtimes(self):
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in self.paths}
        result = S.migrate_files([str(path) for path in self.paths])
        self.assertEqual(result, {str(path): False for path in self.paths})
        self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns)
                                  for path in self.paths})

    def test_real_corpus_cli_passes_without_promoting_any_record(self):
        result = subprocess.run([sys.executable, '-m', 'scripts.art.kit.schema',
                                 *map(str, self.paths)], cwd=ROOT, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('129 checked, 0 with errors', result.stdout)
        self.assertTrue(all(json.loads(path.read_bytes())['approval']['state'] == 'concept'
                            for path in self.paths))

    def test_malformed_concept_records_are_reported_not_accepted_or_crashed(self):
        original = next(p for p in self.records.values() if p['kind'] == 'terrain')
        malformed = []
        for value in ([original], None, True):
            malformed.append(value)
        for key, value in [('approval', []), ('approval', None), ('id', []),
                           ('kind', 'unknown-kind'), ('geometry', {'size_cells': [True, 1]}),
                           ('terrain', {'typo': True}), ('unexpected_key', 'typo')]:
            record = copy.deepcopy(original)
            record[key] = value
            malformed.append(record)
        with tempfile.TemporaryDirectory(prefix='MyGame malformed concept ') as temporary:
            path = Path(temporary) / (original['id'] + '.json')
            for index, record in enumerate(malformed):
                with self.subTest(case=index):
                    path.write_text(json.dumps(record))
                    self.assertTrue(S.check([str(path)])[str(path)])
                    with self.assertRaises(ValueError):
                        S.migrate_piece(record)
                    result = subprocess.run([sys.executable, '-m', 'scripts.art.kit.schema',
                                             str(path)], cwd=ROOT, capture_output=True,
                                            text=True, timeout=30)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_supplied_terrain_and_transition_blocks_remain_structurally_strict(self):
        for kind in ('terrain', 'transition'):
            original = next(p for p in self.records.values() if p['kind'] == kind)
            record = copy.deepcopy(original)
            record[kind] = {'typo': True}
            with self.subTest(kind=kind):
                self.assertTrue(S.errors(record, S.load_schema()))
                with self.assertRaisesRegex(ValueError, 'invalid'):
                    S.migrate_piece(record)

    def test_live_library_and_existing_invalid_controls_remain_strict(self):
        live = S.check()
        self.assertGreaterEqual(len(live), 106)
        self.assertFalse({path: errors for path, errors in live.items() if errors})
        invalid = ROOT / 'game/kit/schema/invalid'
        cases = sorted(invalid.glob('*.json'))
        self.assertGreaterEqual(len(cases), 5)
        for path in cases:
            case = json.loads(path.read_bytes())
            problems = S.errors(case['piece'], S.load_schema()) + S.semantic(case['piece'])
            self.assertTrue(any(case['expect'] in message for message in problems), path.name)

    def test_build_intake_excludes_the_entire_concept_directory(self):
        from scripts.art.kit import build
        library = build.load_library()
        live_ids = {json.loads(Path(path).read_bytes())['id'] for path in S.piece_files()}
        concept_ids = {record['id'] for record in self.records.values()}
        self.assertEqual(set(library), live_ids)
        self.assertFalse(set(library) & concept_ids)

    def test_even_complete_concepts_cannot_enter_the_live_library_or_migration(self):
        live_paths = S.piece_files()
        sources = [json.loads(Path(path).read_bytes()) for path in live_paths]
        # Reuse actual complete runtime metadata so rejection cannot be credited to missing fields.
        for kind in ('terrain', 'transition', 'prop', 'structure'):
            original = next(p for p in sources if p['kind'] == kind)
            record = copy.deepcopy(original)
            record['approval'] = {'state': 'concept'}
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                live = Path(temporary) / 'live'
                live.mkdir()
                path = live / (record['id'] + '.json')
                path.write_text(json.dumps(record))
                before = path.read_bytes()
                self.assertEqual(S.errors(record, S.load_schema()) + S.semantic(record), [])
                with patch.object(S, 'PIECES', str(live)):
                    self.assertTrue(any('non-buildable/non-placeable' in message
                                        for message in S.check([str(path)])[str(path)]))
                    with self.assertRaisesRegex(ValueError, 'non-buildable/non-placeable'):
                        S.migrate_files([str(path)])
                self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

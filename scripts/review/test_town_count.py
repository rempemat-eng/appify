"""Regression controls for existing town counting metadata, not layout approval."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review.town_plan import check_plan, count_buildings

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/vision/research/blockout'


class TownCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((SOURCE / 'towns/canalside.json').read_text())
        cls.blockout = json.loads((SOURCE / 'blockout-v55.json').read_text())

    def tiny(self, **fields):
        return {'buildings': [{'id': 'test', 'counted': True, **fields}],
                'buildings_counted': fields.get('counts_as', 1)}

    def test_existing_row_boundaries(self):
        for fronts, expected in [(1, 1), (2, 1), (3, 1), (5, 1), (6, 2), (10, 2), (11, 3)]:
            with self.subTest(fronts=fronts):
                self.assertEqual(count_buildings(self.tiny(fronts=fronts, counts_as=expected)), (expected, []))

    def test_landmarks_and_uncounted_contribute_zero(self):
        for fields in [{'landmark': True}, {'counted': False}, {'counted': False, 'landmark': True}]:
            with self.subTest(fields=fields):
                self.assertEqual(count_buildings(self.tiny(counts_as=0, **fields)), (0, []))
                self.assertTrue(count_buildings(self.tiny(counts_as=1, **fields))[1])

    def test_legacy_counted_only_fallback(self):
        for counted in [False, True]:
            plan = self.tiny(counted=counted, fronts=11)
            plan['buildings_counted'] = int(counted)
            self.assertEqual(count_buildings(plan), (int(counted), []))

    def test_explicit_contribution_types_and_negative_values(self):
        for value in [-1, True, False, 0.5, 1.0, '1', [], None]:
            with self.subTest(value=value):
                total, findings = count_buildings(self.tiny(counts_as=value))
                self.assertIs(type(total), int)
                self.assertTrue(any('counts_as must' in f for f in findings))

    def test_summary_types_and_negative_values(self):
        for value in [-1, True, False, 0.5, 1.0, '1', [], None]:
            plan = self.tiny(counts_as=1)
            plan['buildings_counted'] = value
            with self.subTest(value=value):
                self.assertTrue(any('buildings_counted must' in f for f in count_buildings(plan)[1]))

    def test_counted_is_boolean(self):
        for value in [0, 1, 'true', [], None]:
            with self.subTest(value=value):
                self.assertTrue(any('counted must' in f for f in count_buildings(self.tiny(counted=value))[1]))

    def test_fronts_are_positive_integer_for_explicit_house_counts(self):
        for value in [-1, 0, True, 1.0, 0.5, '3', [], None]:
            with self.subTest(value=value):
                self.assertTrue(any('fronts must' in f for f in count_buildings(self.tiny(fronts=value, counts_as=1))[1]))

    def test_integer_count_must_match_authored_convention(self):
        for fields in [{'counts_as': 0}, {'fronts': 6, 'counts_as': 1}, {'fronts': 3, 'counts_as': 2}]:
            with self.subTest(fields=fields):
                self.assertTrue(any('existing convention' in f for f in count_buildings(self.tiny(**fields))[1]))

    def test_all_current_count_metadata_unchanged(self):
        paths = sorted((SOURCE / 'towns').glob('*.json'))
        self.assertEqual(len(paths), 21)
        for path in paths:
            with self.subTest(town=path.stem):
                plan = json.loads(path.read_text())
                before = copy.deepcopy(plan)
                self.assertEqual(count_buildings(plan), (plan['buildings_counted'], []))
                self.assertEqual(plan, before)

    def test_real_canalside_and_built_zone_path_reject_false_passes(self):
        baseline = copy.deepcopy(self.plan)
        self.assertEqual(check_plan(baseline, self.blockout)[0], [])
        self.assertEqual(baseline, self.plan)
        for built in [False, True]:
            for value, summary in [(-1, 8), (True, 10), (0.5, 9.5)]:
                plan = copy.deepcopy(self.plan)
                plan['buildings'][0]['counts_as'] = value
                plan['buildings_counted'] = summary
                if built:
                    plan['buildings'][0]['from_zone_plan'] = True
                before = copy.deepcopy(plan)
                with self.subTest(built=built, value=value):
                    fails, _, counted = check_plan(plan, self.blockout)
                    self.assertTrue(any('counts_as must' in f for f in fails))
                    self.assertIs(type(counted), int)
                    self.assertEqual(plan, before)

    def test_existing_warning_and_failure_boundaries(self):
        for target, fail, warning in [([11, 12], False, True), ([14, 15], True, False)]:
            plan = copy.deepcopy(self.plan)
            plan['target'] = target
            failures, notes, _ = check_plan(plan, self.blockout)
            self.assertEqual(any('more than 25 %' in f for f in failures), fail)
            self.assertEqual(any('count (warning)' in n for n in notes), warning)

    def test_real_cli_refuses_without_crashing_or_writing_inputs(self):
        cases = [(None, None, False, 0), (-1, 8, False, 1), (True, 10, False, 1),
                 (0.5, 9.5, False, 1), (-1, 8, True, 1), (True, 10, True, 1),
                 (0.5, 9.5, True, 1)]
        for value, summary, built, code in cases:
            with self.subTest(value=value, built=built), tempfile.TemporaryDirectory(prefix='town count ') as tmp:
                plan = copy.deepcopy(self.plan)
                if value is not None:
                    plan['buildings'][0]['counts_as'] = value
                    plan['buildings_counted'] = summary
                if built:
                    plan['buildings'][0]['from_zone_plan'] = True
                path = Path(tmp) / 'canalside.json'
                path.write_text(json.dumps(plan), encoding='utf-8')
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                run = subprocess.run([sys.executable, str(ROOT / 'scripts/review/town_plan.py'),
                                      '--dir', tmp, '--town', 'canalside'],
                                     capture_output=True, text=True, timeout=30, cwd=ROOT)
                self.assertEqual(run.returncode, code, run.stdout + run.stderr)
                self.assertIn('PASS canalside' if code == 0 else 'counts_as must', run.stdout)
                self.assertNotIn('Traceback', run.stderr)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
                self.assertEqual(list(Path(tmp).iterdir()), [path])


if __name__ == '__main__':
    unittest.main()

"""Shared placement verdicts plus public API invariants, without renderer dependencies."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from . import relations as R

CASES = Path(__file__).resolve().parents[3] / 'game/kit/schema/relations.cases.json'


class Relations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CASES.open() as stream:
            cls.cases = json.load(stream)['cases']

    def test_shared_verdicts_and_messages(self):
        self.assertEqual(len({c['id'] for c in self.cases}), len(self.cases))
        for case in self.cases:
            with self.subTest(case=case['id']):
                if case.get('mode') == 'placement':
                    actual = R.check_placement(case['plan'], case['candidate'], case['library'], case['materials'])
                else:
                    actual = R.check_zone(case['plan'], case['library'], case['materials'])
                self.assertEqual(actual, case['expected'])

    def test_all_schema_predicates_have_manual_cases(self):
        predicates = {r['rel'] for case in self.cases for p in case['library'].values()
                      for field in ('requires', 'forbids') for r in p.get('placement', {}).get(field, [])}
        self.assertTrue(R.RELATIONS <= predicates)

    def test_shared_cases_do_not_mutate_inputs(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                before = copy.deepcopy(case)
                if case.get('mode') == 'placement':
                    result = R.check_placement(case['plan'], case['candidate'], case['library'], case['materials'])
                else:
                    result = R.check_zone(case['plan'], case['library'], case['materials'])
                if result and isinstance(result[0]['at'], list):
                    result[0]['at'].append('mutating the result must not modify the plan')
                self.assertEqual(case, before)

    def test_equivalent_units_have_equivalent_rule_outcomes(self):
        for case in self.cases:
            if case.get('mode') == 'placement' or case['plan'].get('coordinate_space') != 'cells':
                continue
            if not all(isinstance(p, dict) and isinstance(p.get('piece'), str) for p in case['plan']['pieces']):
                continue
            scaled = copy.deepcopy(case['plan'])
            scaled.pop('coordinate_space')
            for item in scaled['pieces'] + scaled.get('anchors', []):
                item['at'] = [v * R.CELL for v in item['at']]
            a = R.check_zone(case['plan'], case['library'], case['materials'])
            b = R.check_zone(scaled, case['library'], case['materials'])
            with self.subTest(case=case['id']):
                self.assertEqual([(f['check'], f['message']) for f in a], [(f['check'], f['message']) for f in b])

    def test_empty_injected_registries_do_not_load_defaults(self):
        case = self.cases[0]
        result = R.check_zone(case['plan'], {}, case['materials'])
        self.assertEqual(result[0]['check'], 'rules.unknown_piece')
        result = R.check_zone(case['plan'], case['library'], {})
        self.assertEqual(result[0]['message'], 'lawn: material is not in the library')

    def test_real_registry_loading_is_source_only_and_fresh(self):
        library = R.default_library()
        materials = R.default_materials()
        self.assertIn('woodland_forest_bench', library)
        self.assertEqual(library['woodland_forest_bench']['placement']['role'], 'seat')
        self.assertIn('lawn', materials)
        library['woodland_forest_bench']['placement']['role'] = 'changed by caller'
        self.assertEqual(R.default_library()['woodland_forest_bench']['placement']['role'], 'seat')
        # Concept briefs are not runtime library intake.
        self.assertFalse(any(p.get('approval', {}).get('state') == 'concept' for p in library.values()))

    def test_invalid_position_numbers_refuse(self):
        case = self.cases[0]
        for value in (float('nan'), float('inf'), True, '1'):
            plan = copy.deepcopy(case['plan'])
            plan['pieces'][0]['at'][0] = value
            with self.subTest(value=value):
                self.assertEqual(R.check_zone(plan, case['library'], case['materials'])[0]['check'], 'rules.position')

    def test_no_implicit_coordinate_or_shape_guessing(self):
        case = self.cases[0]
        for patch in ({'coordinate_space': 'world'}, {'rows': ['..', '.']}, {'tiers': ['not digits']}, {'anchors': None}):
            plan = copy.deepcopy(case['plan'])
            plan.update(patch)
            with self.subTest(patch=patch):
                self.assertEqual(R.check_zone(plan, case['library'], case['materials'])[0]['check'], 'rules.plan')
        self.assertEqual(R.check_zone(None, {}, {})[0]['check'], 'rules.plan')


if __name__ == '__main__':
    unittest.main()

"""Real-metadata first-slice receiving guards (SLICE-KIT/r1).

This source candidate has NOT RUN. Execute only under the lead's bounded GO:
    python3 -B -m unittest scripts.review.test_first_slice_prop_intake -v

The compiled-index freshness canary intentionally fails closed on the frozen
parent's source mismatch. Do not repair it by changing expectations, injecting
approved metadata, mocking verdicts, regenerating an index or replaying #388.
No engine, image decoder, seeder, painter, bake or subprocess is used here.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.art.kit import relations, schema
from scripts.review import kit_scene


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'game/test/fixtures/first_slice_prop_intake.json'
PIECES = ('crossroads_bench', 'crossroads_kit_lantern', 'crossroads_well')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


class FirstSlicePropIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = read_json(FIXTURE)
        cls.library = {pid: read_json(ROOT / 'game/kit/pieces/prop' / (pid + '.json'))
                       for pid in PIECES}
        cls.materials = relations.default_materials()
        cls.guide = read_json(ROOT / 'scripts/art/size_guide.json')

    def receiver(self):
        return copy.deepcopy(self.fixture['receiving_plan'])

    def case_input(self, case):
        plan = self.receiver()
        candidate = next(copy.deepcopy(p) for p in plan['pieces'] if p['id'] == case['subject'])
        self.assertLessEqual(set(case['edit']), {'at', 'facing', 'stage'})
        candidate.update(copy.deepcopy(case['edit']))
        plan['pieces'] = [p for p in plan['pieces'] if p['id'] != case['subject']]
        rows = [list(row) for row in plan['rows']]
        for paint in case.get('paint', []):
            x, y, width, height = paint['rect']
            self.assertIn(paint['glyph'], plan['legend'])
            for yy in range(y, y + height):
                for xx in range(x, x + width):
                    rows[yy][xx] = paint['glyph']
        plan['rows'] = [''.join(row) for row in rows]
        trial = copy.deepcopy(plan)
        trial['pieces'].append(copy.deepcopy(candidate))
        return plan, candidate, trial

    def test_source_pins_and_frozen_scope(self):
        self.assertEqual(self.fixture['base']['commit'],
                         'baab31aeba5817e146fe6931263c2b5a0eb518dd')
        self.assertEqual(self.fixture['base']['tree'],
                         'b2cc638bb47276ab62c6166cfdd0a819e0382009')
        self.assertEqual(set(self.fixture['contracts']), set(PIECES))
        seen = set()
        for pin in self.fixture['source_pins']:
            with self.subTest(path=pin['path']):
                self.assertNotIn(pin['path'], seen)
                seen.add(pin['path'])
                path = ROOT / pin['path']
                self.assertTrue(path.is_file())
                self.assertEqual(git_blob(path.read_bytes()), pin['git_blob'])
        self.assertTrue({f'game/kit/pieces/prop/{pid}.json' for pid in PIECES} <= seen)

    def test_real_piece_schema_and_metadata_contracts(self):
        paths = [str(ROOT / 'game/kit/pieces/prop' / (pid + '.json')) for pid in PIECES]
        self.assertEqual(schema.check(paths), dict.fromkeys(paths, []))
        for pid, piece in self.library.items():
            with self.subTest(piece=pid):
                expected = self.fixture['contracts'][pid]
                self.assertEqual(piece['id'], pid)
                self.assertEqual(piece['approval']['state'], expected['approval'])
                self.assertEqual(piece['approval']['state'], 'candidate')
                self.assertIsNone(piece['approval']['by'])
                self.assertIsNone(piece['approval']['at'])
                self.assertEqual([{k: v[k] for k in ('id', 'png', 'foot')}
                                  for v in piece['variants']], expected['variants'])
                self.assertEqual(piece['geometry']['foot'], expected['foot_art'])
                self.assertEqual(piece['geometry']['footprint'], expected['footprint_cells'])
                self.assertEqual(piece['geometry']['collision'], expected['collision'])
                for key in ('snap', 'requires', 'forbids', 'stages'):
                    self.assertEqual(piece['placement'].get(key, []), expected[key])
                self.assertEqual(piece['story'], expected['story'])
                self.assertEqual(piece['rendering']['cast_shadow'], expected['cast_shadow'])
                self.assertEqual(piece['rendering']['contact_ao'], expected['contact_ao'])
                self.assertEqual(piece['audit']['sources'], expected['source_objects'])

    def test_compiled_receiver_matches_real_metadata(self):
        # This tests the REAL committed receiver. There is no private replacement
        # index and no assertion that an expected stale index constitutes success.
        index = read_json(ROOT / 'game/kit/props/index.json')
        mismatches = []
        for pid, piece in self.library.items():
            compiled = index[pid]
            expected = {
                'footprint': piece['geometry']['footprint'],
                'size_cells': piece['geometry']['size_cells'],
                'story': piece['story'],
                'approval': piece['approval']['state'],
            }
            for key, value in expected.items():
                if compiled.get(key) != value:
                    mismatches.append({'piece': pid, 'field': key,
                                       'source': value, 'receiver': compiled.get(key)})
            self.assertEqual(compiled['variants'],
                             {v['id']: {k: v[k] for k in ('png', 'foot')}
                              for v in piece['variants']})
        self.assertEqual(mismatches, [],
                         'Receiving index needs its owner\'s exact refresh/reservation: '
                         + json.dumps(mismatches, sort_keys=True))

    def test_fixture_is_outside_the_registered_catalogue(self):
        self.assertEqual(self.fixture['scope'], 'test_fixture_only')
        self.assertTrue(self.fixture['candidate_only'])
        self.assertFalse(self.fixture['registered'])
        self.assertEqual(FIXTURE.parent, ROOT / 'game/test/fixtures')
        self.assertFalse((ROOT / 'game/kit/zones/first_slice_prop_intake.json').exists())
        registry = read_json(ROOT / 'game/data/zones.json')
        self.assertNotIn(self.fixture['receiving_plan']['zone'], registry)
        self.assertTrue(self.fixture['receiving_plan']['lab'])
        self.assertFalse(self.fixture['receiving_plan']['ship'])

    def test_real_receiving_materials_and_anchors(self):
        plan = self.receiver()
        self.assertEqual(set(plan['legend'].values()), {'lawn', 'path', 'water'})
        self.assertEqual({len(row) for row in plan['rows']}, {24})
        self.assertEqual(len(plan['rows']), 16)
        self.assertEqual(plan['rows'][7:9], ['#' * 24, '#' * 24])
        for mid in plan['legend'].values():
            self.assertIn(mid, self.materials)
            self.assertEqual(self.materials[mid]['approval'], 'candidate')
        self.assertTrue(self.materials['path']['route'])
        self.assertIsNotNone(self.materials['water']['water'])
        self.assertEqual(plan['anchors'][0]['at'], plan['spawns']['scale_reference'])
        self.assertEqual(len({p['id'] for p in plan['pieces']}), len(plan['pieces']))
        self.assertEqual({p['variant'] for p in plan['pieces']},
                         {'bench_28', 'bench_58', 'kit_lantern_24', 'kit_lantern_25', 'well'})

    def test_real_validators_for_receiving_cases(self):
        seen = set()
        for case in self.fixture['cases']:
            with self.subTest(case=case['id']):
                self.assertNotIn(case['id'], seen)
                seen.add(case['id'])
                plan, candidate, trial = self.case_input(case)
                before = copy.deepcopy((plan, candidate, trial, self.library, self.materials))
                placement = relations.check_placement(plan, candidate, self.library, self.materials)
                full = kit_scene.check_zone(trial, self.library, self.materials, self.guide)
                self.assertEqual({f['check'] for f in placement},
                                 set(case['expect']['placement_checks']), placement)
                self.assertEqual({f['check'] for f in full if f['severity'] == 'fault'},
                                 set(case['expect']['zone_fault_checks']), full)
                self.assertTrue(set(case['expect'].get('zone_advice_checks', [])) <=
                                {f['check'] for f in full if f['severity'] == 'advice'}, full)
                self.assertEqual((plan, candidate, trial, self.library, self.materials), before)
        self.assertEqual(len(seen), 17)

    def test_complete_receiver_is_editable_not_approved(self):
        plan = self.receiver()
        self.assertEqual(relations.check_zone(plan, self.library, self.materials), [])
        findings = kit_scene.check_zone(plan, self.library, self.materials, self.guide)
        self.assertEqual([f for f in findings if f['severity'] == 'fault'], [])
        for entry in plan['pieces']:
            self.assertTrue(any(f['check'] == 'rules.unapproved' and
                                f['severity'] == 'advice' and
                                f['message'].startswith(entry['id'] + ': ')
                                for f in findings), findings)
        self.assertTrue(any(f['check'] == 'rules.scale' and f['severity'] == 'advice'
                            for f in findings), findings)
        plan['ship'] = True
        ship = kit_scene.check_zone(plan, self.library, self.materials, self.guide)
        self.assertTrue(any(f['check'] == 'rules.unapproved' and f['severity'] == 'fault'
                            for f in ship), ship)
        self.assertTrue(all(p['approval']['state'] == 'candidate'
                            for p in self.library.values()))

    def test_overlap_and_snap_are_distinct_receiving_boundaries(self):
        cases = {c['id']: c for c in self.fixture['cases']}
        overlap = cases['bench-solid-overlap-full-zone-only']['expect']
        self.assertEqual(overlap['placement_checks'], [])
        self.assertEqual(overlap['zone_fault_checks'], ['rules.overlap'])
        for name in ('well-half-y-placement-refusal', 'well-quarter-x-placement-refusal'):
            expected = cases[name]['expect']
            self.assertEqual(expected['placement_checks'], ['rules.off_grid'])
            self.assertEqual(expected['zone_fault_checks'], [])
            self.assertEqual(expected['zone_advice_checks'], ['rules.off_grid'])

    def test_no_numeric_clearance_rule_is_invented(self):
        for pid, piece in self.library.items():
            self.assertNotIn('clearance', piece['placement'])
            self.assertIsNone(self.fixture['contracts'][pid]['clearance_cells'])
        # These real records cannot prove a numeric clearance refusal. Solid
        # overlap and source-unclassified visual space are separate obligations.
        findings = kit_scene.check_zone(self.receiver(), self.library, self.materials, self.guide)
        self.assertFalse(any(f['check'] == 'rules.clearance' for f in findings))

    def test_json_and_real_normalization_preserve_identity_and_story(self):
        original = self.receiver()
        roundtrip = json.loads(json.dumps(original, allow_nan=False))
        self.assertEqual(roundtrip, original)
        normalized = kit_scene.normalize(roundtrip)
        self.assertEqual(normalized['coordinate_space'], 'texels')
        self.assertEqual(normalized['rows'], original['rows'])
        for before, after in zip(original['pieces'], normalized['pieces']):
            expected = copy.deepcopy(before)
            expected['at'] = [value * 24 for value in before['at']]
            self.assertEqual(after, expected)
        self.assertEqual(roundtrip, original)
        well = next(p for p in normalized['pieces'] if p['piece'] == 'crossroads_well')
        self.assertEqual(well['stage'], 'restored')
        self.assertEqual(well['if'], {'flags': ['shard_home:woodland']})

    def test_story_flag_is_metadata_not_a_physical_unlock(self):
        well = self.library['crossroads_well']
        self.assertEqual(well['placement']['stages'], ['restored'])
        self.assertEqual(well['story']['gating']['if'], {'flags': ['shard_home:woodland']})
        self.assertEqual(well['audit']['sources'][0]['condition'], well['story']['gating']['if'])
        case = next(c for c in self.fixture['cases'] if c['id'] == 'well-restored')
        plan, candidate, trial = self.case_input(case)
        baseline = relations.check_placement(plan, candidate, self.library, self.materials)
        self.assertEqual(baseline, [])
        without_condition = copy.deepcopy(candidate)
        without_condition.pop('if')
        self.assertEqual(relations.check_placement(plan, without_condition,
                                                 self.library, self.materials), baseline)
        self.assertEqual(candidate['if'], {'flags': ['shard_home:woodland']})
        self.assertEqual(well['story']['gating']['if'], candidate['if'])
        # Equality means this PHYSICAL API ignores the story predicate. It does
        # not authorise placing/unlocking the well without the runtime flag.

    def test_source_shadow_context_and_preview_scale_stay_unapproved(self):
        context = self.fixture['shadow_reference']
        objects = {obj['id']: obj for obj in
                   read_json(ROOT / 'game/zones/crossroads/kit.json')['objects']}
        body, shadow = objects[context['body']], objects[context['companion']]
        self.assertEqual(body['foot'], context['body_foot_art'])
        self.assertEqual(shadow['foot'], context['companion_foot_art'])
        self.assertEqual([b - a for a, b in zip(body['foot'], shadow['foot'])],
                         context['relative_foot_art'])
        self.assertEqual(shadow['offset'], context['companion_offset_art'])
        self.assertEqual(shadow['cond'], context['condition'])
        self.assertEqual(shadow['of'], 'well')
        self.assertFalse(context['assembled'])
        preview = self.fixture['preview_plan']
        self.assertEqual(preview['world_cell_px'], self.guide['unit']['cell'])
        self.assertEqual(preview['texels_per_cell'], 24)
        self.assertEqual(preview['art_density'], 3)
        reference = preview['character']
        manifest = read_json(ROOT / reference['manifest'])
        frame = manifest['clips']['idle']['facings']['S']['frames'][3]
        self.assertEqual(frame['region'], reference['region'])
        self.assertEqual(frame['packed_bounds'], reference['packed_bounds'])
        self.assertEqual(manifest['foot_pivot'], reference['foot_pivot'])
        self.assertEqual(frame['packed_bounds'][3] - frame['packed_bounds'][1], 74)
        self.assertFalse(reference['png_height_measured'])
        self.assertEqual(preview['status'], 'NOT_RUN_REQUIRES_BOUNDED_GO')
        self.assertEqual(self.fixture['execution_plan']['reservation'], 'NONE')


if __name__ == '__main__':
    unittest.main()

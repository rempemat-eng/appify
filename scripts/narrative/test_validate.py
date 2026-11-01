"""Y5 regression cases for the authored quest/dialogue validator.

Fixtures exercise the existing sequential quest and first-match dialogue formats.
They do not introduce a closed registry of external flags or event producers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from .validate import validate


REPO = Path(__file__).resolve().parents[2]
GAME = REPO / 'game'


def quest(identifier='quest_a'):
    return {
        'id': identifier,
        'title': 'A path home',
        'kind': 'main',
        'start': {'on': 'talk:guide'},
        'steps': [
            {'id': 'collect', 'text': 'Find the token', 'on': 'pickup:token'},
            {'id': 'return', 'text': 'Return to the guide', 'on': 'talk:guide'},
        ],
        'rewards': {'glint': 5, 'flags': [identifier + '_done']},
    }


def speaker(entries=None):
    return {
        'guide': {
            'name': 'Guide',
            'entries': entries if entries is not None else [{'lines': ['Welcome home.']}],
        },
    }


class NarrativeValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='narrative_fixture_')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'game'
        (self.root / 'data/quests').mkdir(parents=True)
        (self.root / 'data/dialogue').mkdir(parents=True)
        self.write('quests/quest_a.json', quest())
        self.write('dialogue/speakers.json', speaker())

    def write(self, relative, value):
        path = self.root / 'data' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return path

    def findings(self):
        values = validate(self.root)
        self.assertIsInstance(values, list)
        for value in values:
            for field in ('file', 'path', 'code', 'message'):
                self.assertIsInstance(getattr(value, field), str)
                self.assertTrue(getattr(value, field), (field, value))
        return values

    def assert_fault(self, relative=None, location=None):
        findings = self.findings()
        self.assertTrue(findings, 'The malformed authored data was accepted')
        matches = [f for f in findings if relative is None or relative in f.file]
        self.assertTrue(matches, findings)
        if location:
            self.assertTrue(any(location in f.path for f in matches), findings)
        return findings

    def cli(self, root=None, seed='1', extra_env=None):
        environment = dict(os.environ, PYTHONHASHSEED=seed)
        environment.update(extra_env or {})
        return subprocess.run(
            [sys.executable, '-m', 'scripts.narrative.validate', '--root', str(root or self.root)],
            cwd=REPO, env=environment, capture_output=True, text=True, timeout=15,
        )

    def test_real_authored_data_is_all_validated_without_modification(self):
        quest_files = sorted((GAME / 'data/quests').glob('*.json'))
        dialogue_files = sorted((GAME / 'data/dialogue').glob('*.json'))
        # The initial corpus is 20 quests, 6 dialogue documents and 35 speakers;
        # future legitimate additions must not require changing these tests.
        self.assertGreaterEqual(len(quest_files), 20)
        self.assertGreaterEqual(len(dialogue_files), 6)
        names = {name for path in dialogue_files for name in json.loads(path.read_text())}
        self.assertGreaterEqual(len(names), 35)
        before = {path: path.read_bytes() for path in quest_files + dialogue_files}
        self.assertEqual(validate(GAME), [])
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_valid_unknown_events_flags_and_opaque_metadata_stay_possible(self):
        value = quest()
        value['start'] = {'on': 'future_event:gate', 'if': {'flags': ['external:signal']}}
        value['steps'][0]['on'] = 'some_new_event:token'
        value['steps'][0]['if'] = {'not_flags': ['external:blocked']}
        value['extension'] = {'future': [None, 'opaque', 4.5]}
        self.write('quests/quest_a.json', value)
        self.assertEqual(self.findings(), [])

    def test_malformed_json_reports_the_actual_source_file(self):
        (self.root / 'data/quests/broken.json').write_text('{"id":', encoding='utf-8')
        self.assert_fault('broken.json')

    def test_only_immediate_regular_json_files_match_the_runtime_loader(self):
        # DirAccess.get_files_at loads neither a directory named *.json nor
        # authored JSON nested inside a subdirectory.
        for kind in ('quests', 'dialogue'):
            (self.root / 'data' / kind / 'directory.json').mkdir()
            nested = self.root / 'data' / kind / 'nested'
            nested.mkdir()
            (nested / 'ignored.json').write_text('{', encoding='utf-8')
            (self.root / 'data' / kind / 'ignored.JSON').write_text('{', encoding='utf-8')
        self.assertEqual(self.findings(), [])

    def test_duplicate_json_object_keys_are_not_silently_overwritten(self):
        cases = {
            'quests/quest_a.json': json.dumps(quest()).replace(
                '"id": "quest_a"', '"id": "quest_a", "id": "quest_b"', 1),
            'dialogue/speakers.json': (
                '{"guide":{"entries":[{"lines":["First."]}]},'
                '"guide":{"entries":[{"lines":["Overwritten."]}]}}'),
        }
        for relative, content in cases.items():
            with self.subTest(relative=relative):
                # Reset the other document so each duplicate independently
                # fails an otherwise valid complete corpus.
                self.write('quests/quest_a.json', quest())
                self.write('dialogue/speakers.json', speaker())
                (self.root / 'data' / relative).write_text(content, encoding='utf-8')
                self.assert_fault(Path(relative).name)

    def test_malformed_quest_containers_fail_closed(self):
        for value in (None, [], {}, dict(quest(), steps=None), dict(quest(), steps=[]),
                      dict(quest(), steps=[None]), dict(quest(), start=[])):
            with self.subTest(value=value):
                self.write('quests/quest_a.json', value)
                self.assert_fault('quest_a.json')

    def test_duplicate_quest_ids_across_files_are_rejected(self):
        self.write('quests/other.json', quest())
        self.assert_fault(location='id')

    def test_duplicate_step_ids_are_rejected(self):
        value = quest()
        value['steps'][1]['id'] = value['steps'][0]['id']
        self.write('quests/quest_a.json', value)
        self.assert_fault('quest_a.json', 'steps')

    def test_missing_speaker_in_start_and_step_events_is_reported(self):
        for field in ('start', 'step'):
            with self.subTest(field=field):
                value = quest()
                entry = value['start'] if field == 'start' else value['steps'][0]
                entry['on'] = 'talk:missing_guide'
                self.write('quests/quest_a.json', value)
                findings = self.assert_fault('quest_a.json', 'start' if field == 'start' else 'steps')
                self.assertTrue(any('missing_guide' in f.message for f in findings), findings)

    def test_missing_quest_and_step_references_have_locations(self):
        for condition in ({'done': ['missing_quest']}, {'active': ['missing_quest']},
                          {'not_started': ['missing_quest']}, {'step': ['missing_quest', 'collect']},
                          {'step': ['quest_a', 'missing_step']}):
            with self.subTest(condition=condition):
                self.write('dialogue/speakers.json', speaker([
                    {'if': condition, 'lines': ['Conditional.']}, {'lines': ['Default.']},
                ]))
                self.assert_fault('speakers.json', 'entries')

    def test_malformed_conditions_are_not_silently_accepted(self):
        for condition in ({'flags': 'flag'}, {'done': [None]}, {'step': ['quest_a']},
                          {'step': ['quest_a', 1]}, {'glint_at_least': 'many'}):
            with self.subTest(condition=condition):
                self.write('dialogue/speakers.json', speaker([
                    {'if': condition, 'lines': ['Conditional.']}, {'lines': ['Default.']},
                ]))
                self.assert_fault('speakers.json', 'entries')

    def test_integral_json_numbers_match_godot_conversion_in_known_fields(self):
        for field in ('priority', 'threshold', 'reward'):
            numbers = (0, 1.0, -1.0, 2**53, -2**53)
            if field != 'priority':
                numbers += (-(2**63),)
            for number in numbers:
                with self.subTest(field=field, number=number):
                    value = quest()
                    entry = {'lines': ['Known integral numeric field.']}
                    if field == 'priority':
                        entry['priority'] = number
                    elif field == 'threshold':
                        entry['if'] = {'glint_at_least': number}
                    else:
                        value['rewards']['glint'] = number
                    self.write('quests/quest_a.json', value)
                    self.write('dialogue/speakers.json', speaker([entry]))
                    self.assertEqual(self.findings(), [])

    def test_unsafe_numeric_fields_do_not_silently_round_or_overflow(self):
        invalid = (True, False, 1.25, float('nan'), float('inf'), -float('inf'),
                   2**53 + 1, 2**63 - 1, 2**63, -(2**63) - 1, 10**400)
        for field in ('priority', 'threshold', 'reward'):
            for number in invalid:
                with self.subTest(field=field, number=number):
                    value = quest()
                    entry = {'lines': ['Unsafe numeric field.']}
                    if field == 'priority':
                        entry['priority'] = number
                    elif field == 'threshold':
                        entry['if'] = {'glint_at_least': number}
                    else:
                        value['rewards']['glint'] = number
                    self.write('quests/quest_a.json', value)
                    self.write('dialogue/speakers.json', speaker([entry]))
                    self.assert_fault('quest_a.json' if field == 'reward' else 'speakers.json')

    def test_minimum_int64_priority_cannot_wrap_its_negated_sort_key(self):
        self.write('dialogue/speakers.json', speaker([
            {'priority': 0, 'if': {'flags': ['a']}, 'lines': ['Conditional.']},
            {'priority': -(2**63), 'lines': ['Overflowing sort key.']},
        ]))
        self.assert_fault('speakers.json', 'priority')

    def test_opaque_numeric_metadata_is_not_given_runtime_integer_constraints(self):
        value = quest()
        value['extension'] = {'fraction': 1.25, 'large_integer': 2**53 + 1}
        self.write('quests/quest_a.json', value)
        self.assertEqual(self.findings(), [])

    def test_unknown_condition_operator_is_reported_instead_of_ignored(self):
        self.write('dialogue/speakers.json', speaker([
            {'if': {'flgas': ['returned']}, 'lines': ['A misspelt flag guard.']},
        ]))
        findings = self.assert_fault('speakers.json', 'entries')
        self.assertTrue(any('flgas' in f.path or 'flgas' in f.message for f in findings), findings)

    def test_contradictory_flags_states_and_restorations_are_rejected(self):
        impossible = [
            {'flags': ['same'], 'not_flags': ['same']},
            {'done': ['quest_a'], 'active': ['quest_a']},
            {'active': ['quest_a'], 'not_started': ['quest_a']},
            {'done': ['quest_a'], 'not_started': ['quest_a']},
            {'restored': ['well'], 'not_restored': ['well']},
        ]
        for condition in impossible:
            with self.subTest(condition=condition):
                self.write('dialogue/speakers.json', speaker([
                    {'if': condition, 'lines': ['Impossible.']}, {'lines': ['Default.']},
                ]))
                self.assert_fault('speakers.json', 'entries')

    def test_quest_cannot_require_its_own_active_or_finished_state_to_start(self):
        for condition in ({'active': ['quest_a']}, {'done': ['quest_a']},
                          {'step': ['quest_a', 'collect']}):
            with self.subTest(condition=condition):
                value = quest()
                value['start']['if'] = condition
                self.write('quests/quest_a.json', value)
                self.assert_fault('quest_a.json', 'start')

    def test_not_started_self_condition_is_a_valid_start_guard(self):
        value = quest()
        value['start']['if'] = {'not_started': ['quest_a']}
        self.write('quests/quest_a.json', value)
        self.assertEqual(self.findings(), [])

    def test_quest_without_a_declared_start_can_be_started_by_the_public_api(self):
        value = quest()
        value.pop('start')
        self.write('quests/quest_a.json', value)
        self.assertEqual(self.findings(), [])

    def test_finished_dependency_cycle_without_an_entry_is_unreachable(self):
        first, second = quest(), quest('quest_b')
        first['start']['if'] = {'done': ['quest_b']}
        second['start']['if'] = {'done': ['quest_a']}
        self.write('quests/quest_a.json', first)
        self.write('quests/quest_b.json', second)
        self.assert_fault(location='start')

    def test_forward_dependency_chain_can_start(self):
        first, second = quest(), quest('quest_b')
        first['start']['if'] = {'done': ['quest_b']}
        self.write('quests/quest_a.json', first)
        self.write('quests/quest_b.json', second)
        self.assertEqual(self.findings(), [])

    def test_step_without_any_completion_route_is_rejected(self):
        value = quest()
        value['steps'][0].pop('on')
        self.write('quests/quest_a.json', value)
        self.assert_fault('quest_a.json', 'steps')

    def test_sequential_step_cannot_require_another_current_step_or_done_self(self):
        for condition in ({'done': ['quest_a']}, {'step': ['quest_a', 'return']}):
            with self.subTest(condition=condition):
                value = quest()
                value['steps'][0]['if'] = condition
                self.write('quests/quest_a.json', value)
                self.assert_fault('quest_a.json', 'steps')

    def test_possible_done_if_keeps_an_alternate_completion_route(self):
        value = quest()
        value['steps'][0]['if'] = {'done': ['quest_a']}
        value['steps'][0]['done_if'] = {'flags': ['token_already_found']}
        self.write('quests/quest_a.json', value)
        self.assertEqual(self.findings(), [])

    def test_eventless_step_with_possible_done_if_is_valid(self):
        value = quest()
        value['steps'][0].pop('on')
        value['steps'][0]['done_if'] = {'flags': ['token_already_found']}
        self.write('quests/quest_a.json', value)
        self.assertEqual(self.findings(), [])

    def test_dialogue_root_entry_and_line_shapes_are_checked(self):
        for value in (None, [], {'guide': None}, {'guide': {'entries': None}},
                      {'guide': {'entries': [None]}}, speaker([{'lines': 'a line'}]),
                      speaker([{'lines': [None]}])):
            with self.subTest(value=value):
                self.write('dialogue/speakers.json', value)
                self.assert_fault('speakers.json')

    def test_blank_dialogue_strings_remain_valid_runtime_data(self):
        path = self.write('dialogue/speakers.json', speaker([
            {'lines': ['', '  ', '\t', 'A spoken line.']},
        ]))
        before = path.read_bytes()
        self.assertEqual(self.findings(), [])
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_unconditional_dialogue_branch_shadows_later_entries(self):
        self.write('dialogue/speakers.json', speaker([
            {'lines': ['Always first.']},
            {'if': {'flags': ['returned']}, 'lines': ['Never selected.']},
        ]))
        self.assert_fault('speakers.json', 'entries')

    def test_prior_branch_union_can_shadow_a_later_branch(self):
        self.write('dialogue/speakers.json', speaker([
            {'if': {'flags': ['a']}, 'lines': ['A is set.']},
            {'if': {'not_flags': ['a']}, 'lines': ['A is not set.']},
            {'if': {}, 'lines': ['Covered by the two prior branches.']},
        ]))
        self.assert_fault('speakers.json', 'entries')

    def test_empty_condition_does_not_cover_negative_legacy_glint(self):
        # Quests.check({}) still applies its default glint_at_least=0.
        # The later branch can therefore be selected when legacy Glint is -1.
        self.write('dialogue/speakers.json', speaker([
            {'if': {}, 'lines': ['Nonnegative Glint.']},
            {'if': {'glint_at_least': -1}, 'lines': ['One negative Glint.']},
        ]))
        self.assertEqual(self.findings(), [])

    def test_missing_condition_is_true_even_for_negative_legacy_glint(self):
        # A missing condition goes through Quests.check(null), which returns
        # before the numeric threshold and genuinely covers every later branch.
        self.write('dialogue/speakers.json', speaker([
            {'lines': ['Always selected.']},
            {'if': {'glint_at_least': -1}, 'lines': ['Unreachable.']},
        ]))
        self.assert_fault('speakers.json', 'entries')

    def test_weaker_earlier_condition_shadows_its_stricter_later_branch(self):
        for first, second in (
                ({'flags': ['a']}, {'flags': ['a', 'b']}),
                ({'not_flags': ['a']}, {'not_flags': ['a', 'b']}),
                ({'glint_at_least': 5}, {'glint_at_least': 10}),
                ({'active': ['quest_a']}, {'step': ['quest_a', 'return']})):
            with self.subTest(first=first, second=second):
                self.write('dialogue/speakers.json', speaker([
                    {'if': first, 'lines': ['Earlier.']},
                    {'if': second, 'lines': ['Unreachable.']},
                    {'lines': ['Default.']},
                ]))
                self.assert_fault('speakers.json', 'entries')

    def test_stricter_earlier_branch_leaves_the_weaker_fallback_reachable(self):
        self.write('dialogue/speakers.json', speaker([
            {'if': {'step': ['quest_a', 'return']}, 'lines': ['Return.']},
            {'if': {'active': ['quest_a']}, 'lines': ['Still collecting.']},
            {'lines': ['Default.']},
        ]))
        self.assertEqual(self.findings(), [])

    def test_overlapping_conditions_are_not_necessarily_dead_branches(self):
        self.write('dialogue/speakers.json', speaker([
            {'if': {'flags': ['a']}, 'lines': ['A.']},
            {'if': {'flags': ['b']}, 'lines': ['B without A.']},
            {'lines': ['Default.']},
        ]))
        self.assertEqual(self.findings(), [])

    def test_duplicate_speaker_files_merge_using_priority_not_raw_file_order(self):
        (self.root / 'data/dialogue/speakers.json').unlink()
        self.write('dialogue/a_base.json', speaker([{'lines': ['Base fallback.']}]))
        self.write('dialogue/z_extra.json', speaker([
            {'priority': 10, 'if': {'flags': ['returned']}, 'lines': ['New conditional.']},
        ]))
        self.assertEqual(self.findings(), [])

    def test_equal_priority_file_order_can_prove_a_cross_file_dead_branch(self):
        (self.root / 'data/dialogue/speakers.json').unlink()
        self.write('dialogue/a_base.json', speaker([{'lines': ['Base fallback.']}]))
        self.write('dialogue/z_extra.json', speaker([
            {'if': {'flags': ['returned']}, 'lines': ['Unreachable extra.']},
        ]))
        self.assert_fault('z_extra.json', 'entries')

    def test_validation_diagnostics_are_deterministic_and_inputs_unchanged(self):
        value = quest()
        value['steps'][0]['on'] = 'talk:missing'
        value['steps'][1]['if'] = {'done': ['missing_quest']}
        self.write('quests/quest_a.json', value)
        before = {p: p.read_bytes() for p in (self.root / 'data').rglob('*.json')}
        fields = lambda f: (f.file, f.path, f.code, f.message)
        self.assertEqual([fields(f) for f in self.findings()], [fields(f) for f in self.findings()])
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_real_cli_accepts_valid_data(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_real_cli_rejects_missing_speaker_with_source_and_location(self):
        value = quest()
        value['start']['on'] = 'talk:missing_guide'
        self.write('quests/quest_a.json', value)
        result = self.cli()
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn('quest_a.json', output)
        self.assertIn('start', output)
        self.assertIn('missing_guide', output)
        self.assertNotIn('Traceback', output)

    def test_real_cli_malformed_json_is_a_clean_nonzero_diagnostic(self):
        (self.root / 'data/dialogue/broken.json').write_text('{', encoding='utf-8')
        result = self.cli()
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn('broken.json', output)
        self.assertNotIn('Traceback', output)

    def test_real_cli_deep_json_never_escapes_as_a_recursion_traceback(self):
        source = json.dumps(quest())[:-1]
        path = self.root / 'data/quests/quest_a.json'
        for depth in (500, 995):
            with self.subTest(depth=depth):
                path.write_text(source + ',"extension":' + '{"key":' * depth
                                + '0' + '}' * depth + '}', encoding='utf-8')
                result = self.cli()
                output = result.stdout + result.stderr
                self.assertNotIn('Traceback', output)
                if depth == 500:
                    self.assertEqual(result.returncode, 0, output)
                else:
                    self.assertNotEqual(result.returncode, 0, output)
                    self.assertIn('quest_a.json', output)

    def test_real_cli_surrogate_condition_key_produces_an_escaped_diagnostic(self):
        value = speaker([{'if': {'\ud800': []}, 'lines': ['Malformed operator.']}])
        path = self.root / 'data/dialogue/speakers.json'
        path.write_text(json.dumps(value, ensure_ascii=True), encoding='utf-8')
        result = self.cli()
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn('speakers.json', output)
        self.assertIn(r'\ud800', output.lower())
        self.assertNotIn('Traceback', output)

    def test_real_cli_ascii_stdout_preserves_unicode_diagnostics_by_escaping(self):
        (self.root / 'data/dialogue/speakers.json').unlink()
        value = quest()
        value['start']['on'] = 'talk:guía'
        self.write('quests/quest_a.json', value)
        self.write('dialogue/réponse.json', {
            'guía': {'entries': [{'if': {'flágz': []}, 'lines': ['An invalid guard.']}]},
        })
        result = self.cli(extra_env={'PYTHONIOENCODING': 'ascii'})
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertNotIn('Traceback', output)
        self.assertIn('ponse.json', output)
        self.assertRegex(output, r'\\(?:xe9|u00e9)')
        output.encode('ascii')

    def test_real_cli_missing_game_root_fails_closed(self):
        result = self.cli(self.root / 'missing')
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_real_cli_output_is_stable_across_hash_seeds(self):
        value = quest()
        value['start']['on'] = 'talk:missing_guide'
        value['steps'][0]['if'] = {'done': ['missing_quest']}
        self.write('quests/quest_a.json', value)
        first, second = self.cli(seed='1'), self.cli(seed='42')
        self.assertNotEqual(first.returncode, 0)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, second.stderr)


if __name__ == '__main__':
    unittest.main()

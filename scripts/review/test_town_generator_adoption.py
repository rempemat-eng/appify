"""Exact source-authored additions, refusal controls and unchanged default exports.

Committed JSON is a test oracle only. Production authoring lives in towns55.py.
Fetch the pinned proposal commits before running this offline suite.
"""
import ast
import copy
import hashlib
import json
import inspect
from pathlib import Path
import subprocess
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from scripts.review.test_highgarth_export import ROOT, inputs
import town_plans as tp
import towns55 as tw
import numpy as np


DEPENDENCY = '96215d5b1d6f395e4aa4fbdac207ff6a4ef384d3'


def git_bytes(commit, path):
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT, timeout=30)


def proposal(pid):
    pin = tw.PROPOSED_ADOPTIONS[pid]['source']
    return json.loads(git_bytes(pin['commit'], pin['path']))


def fixture(pid):
    source, args = inputs(pid)
    args = list(args)
    t = tw.Town.__new__(tw.Town)
    t.__dict__.update(args[3][0].__dict__)
    T = args[0]
    t.T = T; t.level = 1; t.slope_max = 0.016; t.cap = source['target'][1]
    T['h'] = np.zeros(T['K'].shape)
    T['taken'] = np.zeros(T['K'].shape, dtype=bool)
    T['used'] = np.zeros(T['K'].shape, dtype=bool)
    T['keepout'] = np.zeros(T['K'].shape, dtype=bool)
    T['barrier'] = np.isin(T['K'], tp.BARRIER_K)
    T['street'] = np.zeros(T['K'].shape, dtype=bool)
    for e in args[4].elems:
        T['street'][args[7]] |= e['mask']
    args[4].mask = T['street'][args[7]].copy()
    for b in t.buildings:
        x, y, w, h = [b[k] // tw.CELL for k in ('x', 'y', 'w', 'h')]
        T['taken'][y:y+h, x:x+w] = True
    args[3] = [t]
    tw.H, tw.W = T['K'].shape
    return source, args, t


class TownGeneratorAdoption(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = ModuleType('unchanged_331_exporter')
        exec(compile(git_bytes(DEPENDENCY, 'docs/vision/research/blockout/town_plans.py'),
                     'pinned-331-town_plans.py', 'exec'), cls.legacy.__dict__)

    def test_every_static_packet_matches_exact_git_sources(self):
        for pid, packet in tw.PROPOSED_ADOPTIONS.items():
            tp.validate_authored_packet(packet, pid)
            for key in ('source', 'baseline'):
                pin = packet[key]; raw = git_bytes(pin['commit'], pin['path'])
                blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                self.assertEqual(blob, pin['blob'])
            original = json.loads(git_bytes(packet['baseline']['commit'], packet['baseline']['path']))
            expected = proposal(pid)
            ids = {b['id'] for b in original['buildings']}
            self.assertEqual(packet['buildings'], [b for b in expected['buildings'] if b['id'] not in ids])
            self.assertEqual(original['terrain'], expected['terrain'])
            self.assertEqual(packet['terrain_box_cells'], original['terrain']['box_cells'])
            old_districts = {d['id'] for d in original['districts']}
            expected_districts = {d['id']: d for d in expected['districts']}
            original_districts = {d['id']: d for d in original['districts']}
            self.assertEqual(packet['districts'], [{k: v for k, v in d.items() if k not in ('buildings', 'mix')}
                                                   for d in expected['districts'] if d['id'] not in old_districts])
            for ident, fields in packet['district_descriptions'].items():
                for field, value in fields.items():
                    self.assertEqual(value, expected_districts[ident][field])
            for ident in original_districts:
                for field in ('declared', 'function'):
                    if original_districts[ident].get(field) != expected_districts[ident].get(field):
                        self.assertEqual(packet['district_descriptions'].get(ident, {}).get(field),
                                         expected_districts[ident][field])
            self.assertEqual(packet['open_uses'], [o for o in expected['open_uses'] if o not in original['open_uses']])
            if 'site_authored' in packet:
                self.assertEqual(packet['site_authored'], expected['site']['authored'])
            if original['site']['authored'] != expected['site']['authored']:
                self.assertEqual(packet.get('site_authored'), expected['site']['authored'])

    def test_required_source_metadata_cannot_be_silently_omitted(self):
        for field in ('district_descriptions', 'site_authored'):
            packet = copy.deepcopy(tw.PROPOSED_ADOPTIONS['cinderwick'])
            if field == 'district_descriptions': packet[field] = {}
            else: del packet[field]
            with patch.dict(tw.PROPOSED_ADOPTIONS, {'cinderwick': packet}):
                with self.assertRaises(AssertionError):
                    self.test_every_static_packet_matches_exact_git_sources()

    def test_all_21_default_record_exports_are_byte_identical_to_331(self):
        paths = sorted((ROOT / 'docs/vision/research/blockout/towns').glob('*.json'))
        self.assertEqual(len(paths), 21)
        for path in paths:
            with self.subTest(town=path.stem):
                _, args = inputs(path.stem)
                normal = tp._record(*args)
                previous = self.legacy._record(*args)
                self.assertEqual(json.dumps(normal, sort_keys=True), json.dumps(previous, sort_keys=True))

    def test_factory_default_source_flow_is_unchanged_from_331(self):
        """Source/wiring preservation, not a raw-world regeneration assertion."""
        old = ast.parse(git_bytes(DEPENDENCY, 'docs/vision/research/blockout/towns55.py'))
        current = ast.parse(Path(tw.__file__).read_text())
        entrypoints = {'lay_all': ({'cinderwick', 'hearthold'}, 'cinderwick'),
                       'hearthold': ({'hearthold'}, 'hearthold'),
                       'launch_cape': ({'launch-cape'}, 'launch-cape')}
        for name, (allowed, pid) in entrypoints.items():
            with self.subTest(entrypoint=name):
                param = inspect.signature(getattr(tw, name)).parameters['authored']
                self.assertEqual(param.kind, inspect.Parameter.KEYWORD_ONLY)
                self.assertIsNone(param.default)
                node = copy.deepcopy(next(n for n in current.body if isinstance(n, ast.FunctionDef) and n.name == name))
                baseline = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == name)
                self.assertFalse(any(isinstance(n, ast.Name) and n.id == 'PROPOSED_ADOPTIONS' for n in ast.walk(node)))
                setup = node.body.pop(1)
                self.assertEqual(ast.unparse(setup.targets[0]), 'authored')
                self.assertEqual(ast.unparse(setup.value.func), '_authored_inputs')
                self.assertEqual(ast.unparse(setup.value.args[0]), 'authored')
                self.assertEqual(ast.literal_eval(setup.value.args[1]), allowed)
                dispatches = [n for n in node.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                              and isinstance(n.value.func, ast.Name) and n.value.func.id == '_adopt_requested']
                self.assertEqual(len(dispatches), 1)
                self.assertEqual([ast.unparse(n) for n in dispatches[0].value.args[:2]], ['t', 'authored'])
                self.assertEqual(ast.literal_eval(dispatches[0].value.args[2]), pid)
                node.body.remove(dispatches[0])
                node.args.kwonlyargs = []; node.args.kw_defaults = []
                for call in [n for n in ast.walk(node) if isinstance(n, ast.Call)
                             and isinstance(n.func, ast.Name) and n.func.id == 'hearthold']:
                    self.assertEqual(len(call.keywords), 1)
                    self.assertEqual(call.keywords[0].arg, 'authored')
                    expected = ast.parse("{k: v for k, v in authored.items() if k == 'hearthold'}", mode='eval').body
                    self.assertEqual(ast.dump(call.keywords[0].value), ast.dump(expected))
                    call.keywords = []  # an empty selection forwarded to the child is its default
                self.assertEqual(ast.dump(node), ast.dump(baseline))
        self.assertEqual(git_bytes(DEPENDENCY, 'docs/vision/research/blockout/geo55.py'),
                         (ROOT / 'docs/vision/research/blockout/geo55.py').read_bytes())

    def test_default_selector_and_dispatch_never_read_or_adopt_proposals(self):
        class UnreadableProposals:
            def __getattribute__(self, key):
                raise AssertionError('default flow read proposed authoring data')
            def __contains__(self, key):
                raise AssertionError('default flow read proposed authoring data')
        with patch.object(tw, 'PROPOSED_ADOPTIONS', UnreadableProposals()):
            for pid in ('cinderwick', 'hearthold', 'launch-cape'):
                for empty in (None, {}):
                    town = Mock()
                    selected = tw._authored_inputs(empty, {pid})
                    self.assertEqual(selected, {})
                    tw._adopt_requested(town, selected, pid)
                    town.adopt.assert_not_called()

    def test_actual_factory_entrypoints_reject_unknown_keys_and_wrong_targets(self):
        for name, pid in [('lay_all', 'cinderwick'), ('hearthold', 'hearthold'), ('launch_cape', 'launch-cape')]:
            entrypoint = getattr(tw, name)
            with self.subTest(entrypoint=name):
                for value in ([], {'unknown-town': tw.PROPOSED_ADOPTIONS[pid]}):
                    with self.assertRaisesRegex(ValueError, 'unknown authored town key'):
                        entrypoint(None, None, authored=value)
                other = 'hearthold' if pid != 'hearthold' else 'cinderwick'
                with self.assertRaisesRegex(ValueError, 'source path mismatch'):
                    entrypoint(None, None, authored={pid: tw.PROPOSED_ADOPTIONS[other]})

    def test_explicit_opt_in_dispatch_keeps_geometry_and_target_refusals(self):
        for blocked in (False, True):
            with self.subTest(blocked=blocked):
                _, args, town = fixture('hearthold')
                packet = tw.PROPOSED_ADOPTIONS['hearthold']
                selected = tw._authored_inputs({'hearthold': packet}, {'hearthold'})
                before = len(town.buildings)
                if blocked:
                    c, r, _, _ = packet['buildings'][0]['footprint_cells']
                    args[0]['barrier'][r, c] = True
                    with self.assertRaisesRegex(ValueError, 'blocked ground'):
                        tw._adopt_requested(town, selected, 'hearthold')
                    self.assertEqual(len(town.buildings), before)
                else:
                    tw._adopt_requested(town, selected, 'hearthold')
                    self.assertEqual(len(town.buildings), before + len(packet['buildings']))
                with self.assertRaisesRegex(ValueError, 'target town mismatch'):
                    tw._adopt_requested(town, selected, 'cinderwick')

    def test_real_hand_forms_and_export_reproduce_clear_hearthold_and_cape_records(self):
        for pid, packet in tw.PROPOSED_ADOPTIONS.items():
            if pid == 'cinderwick':
                continue  # Lossy r-as-road fixture refusal is tested below; raw generation remains separate.
            with self.subTest(town=pid):
                source, args, town = fixture(pid)
                original = tp._record(*args)
                tiers = args[0]['tiers_pre'].copy(); heights = args[0]['h'].copy()
                town.adopt(packet)
                expected = proposal(pid)
                args[8] = [min(source['footprint_px'][0], *(b['rect_px'][0] for b in packet['buildings'])),
                           min(source['footprint_px'][1], *(b['rect_px'][1] for b in packet['buildings'])),
                           max(source['footprint_px'][2], *(b['rect_px'][0]+b['rect_px'][2] for b in packet['buildings'])),
                           max(source['footprint_px'][3], *(b['rect_px'][1]+b['rect_px'][3] for b in packet['buildings']))]
                out = tp._record(*args)
                new_ids = {b['id'] for b in packet['buildings']}
                self.assertEqual([b for b in out['buildings'] if b['id'] in new_ids], packet['buildings'])
                self.assertEqual([b for b in out['buildings'] if b['id'] not in new_ids], original['buildings'])
                self.assertEqual(out['districts'], expected['districts'])
                for field in ('buildings_counted', 'fronts', 'footprint_px', 'size_table_px'):
                    self.assertEqual(out[field], expected[field])
                self.assertEqual(out['game_layout']['screens'], expected['game_layout']['screens'])
                self.assertTrue(np.array_equal(tiers, args[0]['tiers_pre']))
                self.assertTrue(np.array_equal(heights, args[0]['h']))
                for old, retained in zip(original['buildings'], out['buildings']):
                    self.assertEqual(old, retained)

    def test_cinderwick_lossy_route_as_road_fixture_is_refused_without_relocation(self):
        _, args, town = fixture('cinderwick')
        before = copy.deepcopy(town.buildings)
        rec = tw.PROPOSED_ADOPTIONS['cinderwick']['buildings'][1]
        c, r, w, h = rec['footprint_cells']
        self.assertEqual(int(np.count_nonzero(args[0]['K'][r:r+h, c:c+w] == 'road')), 3)
        with self.assertRaisesRegex(ValueError, 'cinderwick-b015.*blocked ground'):
            town.adopt(tw.PROPOSED_ADOPTIONS['cinderwick'])
        self.assertEqual(town.buildings, before)

    def test_duplicate_or_unmatched_ids_are_refused(self):
        packet = copy.deepcopy(tw.PROPOSED_ADOPTIONS['hearthold'])
        packet['buildings'].append(copy.deepcopy(packet['buildings'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            tp.validate_authored_packet(packet, 'hearthold')
        _, args, town = fixture('hearthold')
        town.authored_plan = copy.deepcopy(tw.PROPOSED_ADOPTIONS['hearthold'])
        with self.assertRaisesRegex(ValueError, 'unmatched'):
            tp._record(*args)

    def test_missing_district_and_geometry_override_are_refused(self):
        for field, value, message in [('district', 'missing-district', 'district'),
                                      ('rect_px', [2024, 5648, 88, 48], 'footprint')]:
            with self.subTest(field=field):
                _, args, town = fixture('hearthold')
                packet = copy.deepcopy(tw.PROPOSED_ADOPTIONS['hearthold'])
                packet['buildings'][0][field] = value
                with self.assertRaisesRegex(ValueError, message):
                    town.adopt(packet)
                    tp._record(*args)

    def test_source_pin_unknown_fields_and_count_fabrication_are_refused(self):
        for change in [lambda p: p['source'].update(commit='HEAD'),
                       lambda p: p.update(new_rule=True),
                       lambda p: p['buildings'][0].update(counts_as=2),
                       lambda p: p['buildings'][0].update(counted=1)]:
            p = copy.deepcopy(tw.PROPOSED_ADOPTIONS['hearthold']); change(p)
            with self.assertRaises(ValueError):
                tp.validate_authored_packet(p, 'hearthold')

    def test_real_tier_barrier_and_clipped_plot_failures_are_not_hidden(self):
        for kind in ('tier', 'barrier', 'plot'):
            with self.subTest(kind=kind):
                _, args, town = fixture('hearthold')
                packet = tw.PROPOSED_ADOPTIONS['hearthold']; rec = packet['buildings'][0]
                c, r, _, _ = rec['footprint_cells']
                if kind == 'tier': args[0]['tiers_pre'][r, c] = 1
                elif kind == 'barrier': args[0]['barrier'][r, c] = True
                else:
                    c, r, _, _ = rec['plot_cells']; args[0]['keepout'][r, c] = True
                with self.assertRaises(ValueError):
                    town.adopt(packet)

    def test_explicit_doors_still_require_real_street_access(self):
        source, args, town = fixture('hearthold')
        town.adopt(tw.PROPOSED_ADOPTIONS['hearthold'])
        pas = tp._passable(args[0], args[7], [town])
        tp._authored_access([town], args[4], args[6], pas)
        town.buildings[-1]['faces'] = 'missing-street'
        with self.assertRaisesRegex(ValueError, 'street'):
            tp._authored_access([town], args[4], args[6], pas)

    def test_existing_plots_and_named_uses_are_reserved_but_padding_is_not(self):
        for kind in ('plot', 'named yard', 'padding'):
            with self.subTest(kind=kind):
                _, args, town = fixture('hearthold')
                packet = tw.PROPOSED_ADOPTIONS['hearthold']; rec = packet['buildings'][0]
                c, r, w, h = rec['footprint_cells']
                if kind == 'plot':
                    town.buildings[0]['plot'] = [c, r, w, h, 'yard']
                elif kind == 'named yard':
                    x, y, wpx, hpx = rec['rect_px']
                    town.yard(x, y, x+wpx, y+hpx, name='an existing named yard', why='preserved source use')
                else:
                    args[0]['used'][r:r+h, c:c+w] = True
                if kind == 'padding':
                    town.adopt(packet)
                else:
                    with self.assertRaisesRegex(ValueError, 'blocked ground'):
                        town.adopt(packet)

    def test_authored_rear_plot_must_fit_the_selected_terrain_window(self):
        _, args, town = fixture('hearthold')
        packet = copy.deepcopy(tw.PROPOSED_ADOPTIONS['hearthold'])
        packet['terrain_box_cells'] = list(packet['buildings'][0]['footprint_cells'])
        with self.assertRaisesRegex(ValueError, 'plot.*terrain window'):
            town.adopt(packet)

    def test_barrier_only_door_approach_is_refused(self):
        _, args, town = fixture('hearthold')
        town.adopt(tw.PROPOSED_ADOPTIONS['hearthold'])
        b = town.buildings[-3]; dc, dr = b['door']; c0, r0, _, _ = args[6]
        self.assertFalse(args[4].mask[dr-r0, dc-c0])
        pas = tp._passable(args[0], args[7], [town])
        self.assertTrue(pas[dr-r0, dc-c0])
        args[0]['barrier'][dr, dc] = True
        with self.assertRaisesRegex(ValueError, 'real barrier'):
            tp._authored_access([town], args[4], args[6], pas)

    def test_unknown_nested_authoring_fields_are_refused(self):
        for pid, field in [('launch-cape', 'districts'), ('cinderwick', 'open_uses')]:
            packet = copy.deepcopy(tw.PROPOSED_ADOPTIONS[pid]); packet[field][0]['new_rule'] = True
            with self.assertRaisesRegex(ValueError, 'unsupported authored'):
                tp.validate_authored_packet(packet, pid)
        packet = copy.deepcopy(tw.PROPOSED_ADOPTIONS['hearthold']); packet['site_authored'] = False
        with self.assertRaisesRegex(ValueError, 'site description'):
            tp.validate_authored_packet(packet, 'hearthold')


if __name__ == '__main__':
    unittest.main()

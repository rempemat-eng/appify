"""Exact source-authored additions, refusal controls and unchanged default exports.

Committed JSON is a test oracle only. Production authoring lives in towns55.py.
Fetch the pinned proposal commits before running this offline suite.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from types import ModuleType
import unittest

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

    def test_all_21_default_record_exports_are_byte_identical_to_331(self):
        paths = sorted((ROOT / 'docs/vision/research/blockout/towns').glob('*.json'))
        self.assertEqual(len(paths), 21)
        for path in paths:
            with self.subTest(town=path.stem):
                _, args = inputs(path.stem)
                normal = tp._record(*args)
                previous = self.legacy._record(*args)
                self.assertEqual(json.dumps(normal, sort_keys=True), json.dumps(previous, sort_keys=True))

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


if __name__ == '__main__':
    unittest.main()

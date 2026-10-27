"""Physical regression fixtures for exported kit plans, also consumed by GdUnit."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from . import ground_rules
from . import kit_scene as KS


def materials():
    return {
        'lawn': dict(id='lawn', walkable=True, surface='turf', approval='approved'),
        'path': dict(id='path', walkable=True, surface='earth', route=True, approval='approved'),
        'water': dict(id='water', walkable=False, surface='water', water={'body': 'river'}, approval='approved'),
        'face': dict(id='face', walkable=False, surface='earth', face={'height_cells': 1}, approval='approved'),
    }


def library():
    def piece(role, blocks=False):
        return dict(approval={'state': 'approved'}, placement={'role': role, 'snap': 'free'},
                    geometry={'collision': {'shape': 'rect', 'rect': [-4, -8, 8, 8]}},
                    gameplay={'blocks_move': blocks})
    return {'box': piece('structure', True), 'hearth': piece('hearth'), 'fire': piece('fire'),
            'rubble': piece('debris'), 'bridge': dict(piece('bridge'), gameplay={'blocks_move': False, 'deck': [-4, -24, 8, 24]}),
            'stair': dict(piece('stair'), gameplay={'blocks_move': False, 'deck': [-4, -8, 8, 8]})}


def plan():
    return dict(zone='w6_fixture', coordinate_space='cells', legend={'.': 'lawn', '#': 'path', '~': 'water'},
                rows=['......'] * 6, lab=True, pieces=[], spawns={'start': [.5, .5]})


def instance(piece='box', at=(3.5, 3), **fields):
    return dict(dict(id=piece, piece=piece, at=list(at)), **fields)


def _row(p, y, value):
    p['rows'][y] = value


def cases():
    """Each expected list is an independently specified set of fatal checks."""
    out = []
    def add(name, p, expected=(), lib=None, mats=None, guide=None):
        c = dict(id=name, plan=p, library=lib or library(), materials=mats or materials(), expected_checks=list(expected))
        if guide is not None:
            c['size_guide'] = guide
        out.append(c)
    add('open-ground', plan())
    p = plan(); _row(p, 2, '..##..'); p['pieces'] = [instance(at=(3.5, 3))]
    add('structure-on-path', p, ['rules.route_clear'])
    p = plan(); _row(p, 2, '..##..'); p['pieces'] = [instance(at=(4.5, 3))]
    add('structure-beside-path', p)
    p = plan(); p['pieces'] = [instance('fire')]
    add('fire-without-hearth', p, ['rules.fire_hearth'])
    p = plan(); p['pieces'] = [instance('fire'), instance('hearth')]
    add('fire-on-hearth', p)
    p = plan(); p['stages'] = ['broken', 'restored']; p['pieces'] = [instance('rubble')]
    add('debris-in-all-stages', p, ['rules.stage_debris'])
    p = plan(); p['stages'] = ['broken', 'restored']; p['pieces'] = [instance('rubble', stage='broken')]
    add('debris-broken-only', p)
    p = plan(); p['spawns']['start'] = [1.5, .5]; p['rows'] = ['~.....', '~.....', '~.....', '~.....', '~.....', '~.....']; p['tiers'] = ['000000', '100000', '100000', '100000', '100000', '100000']; p['flow'] = ['v.....'] + ['......'] * 5
    add('water-uphill', p, ['rules.water_uphill'])
    p = copy.deepcopy(p); p['flow'] = ['......'] + ['^.....'] + ['......'] * 4
    add('water-downhill', p)
    p = plan(); p['flow'] = ['>.....'] + ['......'] * 5
    add('flow-on-dry-ground', p, ['rules.water_flow'])
    p = plan(); _row(p, 2, '..~...')
    add('water-dead-end', p, ['rules.water_end'])
    p = plan(); _row(p, 2, '..~~..'); _row(p, 3, '..~~..')
    add('water-pool', p)
    p = plan(); _row(p, 2, '~~#...')
    add('path-into-water', p, ['rules.route_water'])
    p = plan(); p['rows'] = ['......', '......', '~.....', '~.....', '......', '......']; p['pieces'] = [instance('bridge', at=(.5, 5))]; lib = library(); lib['bridge']['gameplay']['deck'] = [-4, -32, 8, 32]
    add('bridge-with-dry-landings', p, lib=lib)
    p = plan(); p['pieces'] = [instance('bridge')]
    add('bridge-without-water', p, ['rules.deck'])
    p = plan(); _row(p, 0, '~.....')
    add('spawn-on-water', p, ['rules.walk'])
    p = plan(); p['pieces'] = [instance(at=(3.5, 3)), instance(at=(3.5, 3), id='other')]
    add('solid-overlap', p, ['rules.overlap'])
    p = plan(); p['pieces'] = [instance(at=(3.5, 3)), instance(at=(4.5, 3), id='other')]
    add('solids-touch', p)
    p = plan(); _row(p, 2, '######'); _row(p, 3, '######'); p['tiers'] = ['000000', '000000', '000000', '111111', '111111', '111111']
    add('route-tier-without-stair', p, ['rules.tier_route'])
    p = plan(); p['pieces'] = [instance('stair')]
    add('stair-without-face', p, ['rules.stair'])
    p = plan(); p['tiers'] = ['111111', '111111', '000000', '000000', '000000', '000000']; p['pieces'] = [instance('stair', at=(3.5, 3))]
    add('stair-with-head-and-foot', p)
    p = plan(); p['pieces'] = [instance()]; lib = library(); lib['box']['audit'] = {'size_class': 'custom'}; lib['box']['geometry']['size_px'] = [24, 24]; lib['box']['geometry']['size_cells'] = [1, 1]
    guide = {'tolerance': 0, 'kinds': {'custom': {'w': [8, 8], 'h': [8, 8]}}}
    add('declared-scale-good', p, lib=lib, guide=guide)
    lib = copy.deepcopy(lib); lib['box']['geometry']['size_px'] = [240, 24]
    add('declared-scale-bad', p, ['rules.scale'], lib=lib, guide=guide)
    p = plan(); p['pieces'] = [instance()]; lib = library(); lib['box']['approval']['state'] = 'concept'
    add('concept-even-in-lab', p, ['rules.unapproved'], lib=lib)
    p = plan(); p['pieces'] = [instance()]; lib = library(); lib['box']['approval']['state'] = 'candidate'
    add('candidate-in-lab-is-advice', p, lib=lib)
    p = copy.deepcopy(p); p['ship'] = True
    add('candidate-shipping-is-fault', p, ['rules.unapproved'], lib=lib)
    p = plan(); p['pieces'] = [instance('unknown')]
    add('unknown-piece', p, ['rules.unknown_piece'])
    p = plan(); p['legend']['.'] = 'unknown'
    add('unknown-material', p, ['rules.unknown_piece'])
    p = plan(); p['spawns']['start'] = [2.5, .5]; _row(p, 0, '~.....'); p['tiers'] = ['100000'] + ['000000'] * 5
    add('rim-without-fall', p, ['rules.water_fall'])
    lib = library(); lib['fall'] = dict(approval={'state': 'approved'}, geometry={'footprint': [[0, 0]]}, placement={'role': 'waterfall', 'snap': 'free'}, gameplay={'blocks_move': False})
    p = copy.deepcopy(p); p['pieces'] = [instance('fall', at=(.5, 1))]
    add('rim-covered-by-fall', p, lib=lib)
    p = plan(); _row(p, 2, '######'); _row(p, 3, '######')
    add('route-stays-on-one-tier', p)
    lib = library(); lib['bench'] = dict(approval={'state': 'approved'}, placement={'role': 'seat', 'snap': 'free', 'requires': [{'rel': 'adjacent', 'what': 'route_edge', 'cells': 2, 'facing': True}], 'forbids': [{'rel': 'on', 'what': 'route'}]}, geometry={'collision': {'shape': 'rect', 'rect': [-4, -8, 8, 8]}}, gameplay={'blocks_move': True})
    p = plan(); _row(p, 2, '..###.'); p['pieces'] = [instance('bench')]
    add('bench-on-path', p, ['rules.route_clear', 'rules.seating'], lib=lib)
    p = plan(); _row(p, 3, '..###.'); p['pieces'] = [instance('bench', facing='s')]
    add('bench-facing-path', p, lib=lib)
    p = plan(); p['doors'] = [{'id': 'door', 'rect': [2, 2, 1, 1]}]; p['pieces'] = [instance(at=(2.5, 3))]
    add('door-entirely-blocked', p, ['rules.walk'])
    p = plan(); p['doors'] = [{'id': 'door', 'rect': [2, 2, 1, 1]}]
    add('door-open', p)
    p = plan(); p['stages'] = ['broken', 'restored']; p['pieces'] = [instance('rubble', stage='restored')]; lib = library(); lib['rubble']['placement']['stages'] = ['broken', 'restored']
    add('debris-multiple-stages-is-not-broken-only', p, ['rules.stage_debris'], lib=lib)
    p = copy.deepcopy(p); p['pieces'][0]['stage'] = 'restored'; lib = library(); lib['rubble']['placement']['stages'] = ['broken']
    add('restored-debris-not-overridden-by-library-stage', p, ['rules.stage', 'rules.stage_debris'], lib=lib)
    p = plan(); p['pieces'] = [instance()]; lib = library(); lib['box']['audit'] = {'size_class': 'hut'}
    add('declared-scale-without-dimensions', p, ['rules.scale'], lib=lib)
    p = plan(); _row(p, 2, '..###.'); p['pieces'] = [instance('weed', at=(3.5, 2.5))]; lib = library(); lib['weed'] = dict(approval={'state': 'approved'}, placement={'role': 'clutter', 'snap': 'free'}, geometry={}, gameplay={'blocks_move': False})
    add('nonblocking-clutter-on-route', p, ['rules.clutter'], lib=lib)
    p = copy.deepcopy(p); p['pieces'][0]['at'] = [1.5, 2.5]
    add('nonblocking-clutter-beside-route', p, lib=lib)
    p = plan(); _row(p, 0, '~.....'); p['spawns']['start'] = [2.5, .5]; p['flow'] = ['>.....'] + ['......'] * 5
    add('water-flow-into-dry-land', p, ['rules.water_flow'])
    p = copy.deepcopy(p); p['flow'][0] = '<.....'
    add('water-flow-out-of-zone', p)
    p = plan(); p['rows'] = ['......', '......', '~.....', '~.....', '......', '......']; p['pieces'] = [instance('bridge', at=(0, 5))]; lib = library(); lib['bridge']['gameplay']['deck'] = [-4, -32, 8, 32]
    add('bridge-clipped-at-zone-edge', p, ['rules.deck'], lib=lib)
    p = plan(); p['tiers'] = ['111111', '111111', '000000', '000000', '000000', '000000']; p['pieces'] = [instance('stair', at=(5.5, 3))]; lib = library(); lib['stair']['gameplay']['deck'] = [-4, -8, 16, 8]
    add('stair-clipped-at-zone-edge', p, ['rules.stair'], lib=lib)
    p = plan(); p['spawns']['start'] = [5.5, 5.5]; p['pieces'] = [instance(at=(.5, 1))]; lib = library(); lib['box']['geometry']['collision']['rect'] = [-12, -8, 24, 8]
    add('solid-body-crosses-zone-boundary', p, ['rules.bounds'], lib=lib)
    p = copy.deepcopy(p); p['pieces'][0]['at'] = [1.5, 1]
    add('solid-body-touches-zone-boundary', p, lib=lib)
    return out


class KitSceneTests(unittest.TestCase):
    def test_shared_physical_cases(self):
        for case in cases():
            with self.subTest(case=case['id']):
                findings = KS.check_zone(case['plan'], case['library'], case['materials'], case.get('size_guide'))
                actual = sorted({f['check'] for f in findings if f['severity'] == 'fault'})
                self.assertEqual(actual, sorted(case['expected_checks']), findings)

    def test_real_kitlab_has_no_fatal_finding(self):
        findings = KS.check_zone(KS.load_plan('kitlab'))
        self.assertFalse([f for f in findings if f['severity'] == 'fault'], findings)
        self.assertTrue(any(f['check'] == 'rules.scale' and f['severity'] == 'advice' for f in findings))

    def test_units_round_trip_without_input_mutation(self):
        original = plan(); original['pieces'] = [instance()]; original['doors'] = [{'id': 'east', 'rect': [5, 1, 1, 2], 'to': 'next'}]
        before = copy.deepcopy(original)
        texels = KS.normalize(original)
        self.assertEqual(original, before)
        self.assertEqual(texels['pieces'][0]['at'], [84.0, 72.0])
        self.assertEqual(texels['doors'][0]['rect'], [5, 1, 1, 2])
        self.assertEqual(KS.check_zone(original, library(), materials()), KS.check_zone(texels, library(), materials()))
        converted = KS.to_ground_plan(original, library(), materials())
        self.assertEqual(converted['doors'][0]['rect'], [40.0, 8.0, 8.0, 16.0])
        self.assertEqual(converted['stands']['start'], [4.0, 4.0])

    def test_adapter_preserves_raster_and_authored_paths(self):
        p = plan(); _row(p, 2, '.##...'); p['paths'] = [{'id': 'authored', 'points': [[0, 8], [48, 8]], 'radius': 4}]
        result = KS.to_ground_plan(p, library(), materials())
        self.assertEqual(result['paths'], p['paths'])
        self.assertEqual(result['cell_regions']['route'], [[1, 2], [2, 2]])
        self.assertEqual(result['cell_regions']['water'], [])
        self.assertNotIn('routes', result)

    def test_multicell_footprint_blocks_path_away_from_anchor(self):
        p = plan(); _row(p, 2, '..#...'); p['pieces'] = [instance(at=(4.5, 3))]
        lib = library(); lib['box']['geometry'] = {'footprint': [[-2, -1]], 'collision': {'shape': 'cells'}}
        findings = KS.check_zone(p, lib, materials())
        self.assertIn('rules.route_clear', {f['check'] for f in findings if f['severity'] == 'fault'})

    def test_spawn_uses_precise_body_instead_of_entire_cell(self):
        p = plan(); p['pieces'] = [instance(at=(3.5, 3))]; p['spawns'] = {'start': [3.1, 2.1]}
        lib = library(); lib['box']['geometry']['collision']['rect'] = [-1, -1, 2, 1]
        self.assertNotIn('rules.walk', {f['check'] for f in KS.check_zone(p, lib, materials())})
        p['spawns']['start'] = [3.5, 2.95]
        self.assertIn('rules.walk', {f['check'] for f in KS.check_zone(p, lib, materials())})

    def test_two_small_solids_share_a_cell_without_physical_overlap(self):
        p = plan(); p['pieces'] = [instance(at=(3.2, 3)), instance(at=(3.8, 3), id='other')]
        lib = library(); lib['box']['geometry']['collision']['rect'] = [-.5, -.5, 1, .5]
        self.assertNotIn('rules.overlap', {f['check'] for f in KS.check_zone(p, lib, materials())})
        p['pieces'][1]['at'] = [3.21, 3]
        self.assertIn('rules.overlap', {f['check'] for f in KS.check_zone(p, lib, materials())})

    def test_invalid_inputs_return_findings(self):
        for p in [None, {}, dict(plan(), coordinate_space='guess'), dict(plan(), rows=['x']), dict(plan(), pieces=[{'piece': 'box', 'at': [float('nan'), 0]}]), dict(plan(), flow=['?'] * 6)]:
            with self.subTest(plan=p):
                self.assertTrue(KS.check_zone(p, library(), materials()))

    def test_concept_material_cannot_enter_lab(self):
        mats = materials(); mats['lawn']['approval'] = 'concept'
        findings = KS.check_zone(plan(), library(), mats)
        self.assertIn('rules.unapproved', {f['check'] for f in findings if f['severity'] == 'fault'})

    def test_exact_cell_union_shared_boundary_and_concave_corner(self):
        p = {'cell_regions': {'cell': 8, 'route': [[0, 0], [1, 0], [0, 1]], 'water': [[2, 0]]}}
        self.assertTrue(ground_rules._on_route((8, 4), p, shrink=1))
        self.assertFalse(ground_rules._on_route((7.75, 7.75), p, shrink=1))
        self.assertTrue(ground_rules._on_route((4, 4), p, shrink=1))
        self.assertTrue(ground_rules._on_water((15.5, 4), p, pad=1))
        self.assertFalse(ground_rules._on_water((14.5, 4), p, pad=1))

    def test_old_painted_path_helpers_remain_unchanged(self):
        p = {'paths': [{'id': 'road', 'points': [[0, 8], [40, 8]], 'radius': 4}]}
        self.assertEqual(ground_rules._on_route((10, 8), p), ['road'])
        self.assertEqual(ground_rules._on_route((10, 13), p), [])

    def test_cli_json_exit_status_and_no_scientific_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bad.json'
            p.write_text('{"zone":"bad","rows":["x"],"legend":{"x":"unknown"}}')
            result = subprocess.run([sys.executable, '-S', '-m', 'scripts.review.kit_scene', str(p), '--check', '--json'], cwd=KS.ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['findings'][0]['check'], 'rules.unknown_piece')

    def test_shared_fixture_is_current(self):
        path = KS.ROOT / 'game/test/fixtures/kit/validation.cases.json'
        self.assertEqual(json.loads(path.read_text()), {'version': 1, 'provenance': 'Engineering physical cases, not art approval.', 'cases': cases()})

    def test_review_scene_json_runs_real_adapter_and_sets_exit_status(self):
        from . import run
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'export.json'
            valid = KS.load_plan('kitlab')
            source.write_text(json.dumps(valid))
            output = Path(tmp) / 'valid'
            self.assertEqual(run.main([str(source), '--no-render', '--out', str(output)]), 0)
            report = json.loads((output / 'report.json').read_text())
            self.assertIn('kit', report)
            self.assertEqual(report['counts']['fault'], 0)
            invalid = copy.deepcopy(valid)
            # The actual lab bench's physical box spans row7 near col10.
            row = invalid['rows'][7]; invalid['rows'][7] = row[:10] + '#' + row[11:]
            source.write_text(json.dumps(invalid))
            output = Path(tmp) / 'invalid'
            self.assertEqual(run.main([str(source), '--no-render', '--out', str(output)]), 1)
            report = json.loads((output / 'report.json').read_text())
            self.assertGreater(report['counts']['fault'], 0)
            self.assertTrue(any(f.get('check') == 'rules.route_clear' for f in report['kit']['findings']))

    def test_review_scene_malformed_json_fails_closed(self):
        from . import run
        with tempfile.TemporaryDirectory() as tmp:
            for i, text in enumerate(('{', 'null', '[]', '{}', None)):
                with self.subTest(text=text):
                    source = Path(tmp) / ('bad%s.json' % i)
                    if text is not None:
                        source.write_text(text)
                    output = Path(tmp) / ('report%s' % i)
                    self.assertEqual(run.main([str(source), '--no-render', '--out', str(output)]), 1)
                    report = json.loads((output / 'report.json').read_text())
                    self.assertGreater(report['counts']['fault'], 0)
                    self.assertIn('rules.plan', {f['check'] for f in report['kit']['findings']})


if __name__ == '__main__':
    unittest.main()

"""Y46: real seed assembly/writes in disposable metadata destinations only.

Image dimensions are injected from the pinned piece metadata; no PNG is opened,
drawn or copied. World-wide source discovery is replaced by a bounded assembly
batch, while _assemble, main, schema checks and relation predicates remain real.
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.art.kit import relations as R
from scripts.art.kit import seed_props as S

ROOT = Path(__file__).resolve().parents[2]
IDS = ('crossroads_crates', 'crossroads_trough')


class SeedPropPhases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='y46-metadata-')
        self.addCleanup(self.temp.cleanup)
        self.dest = Path(self.temp.name)
        self.original = {
            pid: json.loads((ROOT / 'game/kit/pieces/prop' / (pid + '.json')).read_text())
            for pid in IDS
        }
        self.source_bytes = {
            pid: (ROOT / 'game/kit/pieces/prop' / (pid + '.json')).read_bytes()
            for pid in IDS
        }
        self.addCleanup(self.assert_source_unchanged)
        self.scope = patch.object(S, 'PIECES', str(self.dest))
        self.scope.start()
        self.addCleanup(self.scope.stop)

    def assert_source_unchanged(self):
        for pid, data in self.source_bytes.items():
            self.assertEqual((ROOT / 'game/kit/pieces/prop' / (pid + '.json')).read_bytes(), data)

    def write(self, piece):
        path = self.dest / piece['kind'] / (piece['id'] + '.json')
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(piece, indent=1) + '\n')
        return path

    def assemble(self, pid, collision='source'):
        source = self.original[pid]
        objects = [dict(id=v['id'], png=v['id'] + '.png', anchor=v['foot'])
                   for v in source['variants']]
        col = copy.deepcopy(source['geometry']['collision']) if collision == 'source' else collision
        with patch.object(S, '_size', return_value=(source['geometry']['size_px'], None)), \
                patch.object(S, '_source_variant_ids', return_value={v['id'] for v in source['variants']}), \
                patch.object(S, '_quest_refs', return_value=[]):
            return S._assemble('crossroads', pid.removeprefix('crossroads_'), objects, col)

    def run_batch(self, ids=IDS, force=True, hook=None):
        def batch():
            pieces = [self.assemble(pid) for pid in ids]
            # Same final normalization as seed(); discovery alone is substituted.
            for p in pieces:
                p['audit']['sources'].sort(key=lambda item: (item['zone'], item['object']))
                p['audit']['todo'] = sorted(set(p['audit']['todo']))
            if hook:
                hook()
            return pieces
        with patch.object(S, 'seed', side_effect=batch), contextlib.redirect_stdout(io.StringIO()) as output:
            code = S.main(['--force'] if force else [])
        return code, output.getvalue()

    def generated(self, pid):
        return json.loads((self.dest / 'prop' / (pid + '.json')).read_text())

    def test_force_keeps_six_cells_for_both_crate_variants(self):
        self.write(self.original['crossroads_crates'])
        self.assertEqual(self.run_batch(('crossroads_crates',))[0], 0)
        p = self.generated('crossroads_crates')
        self.assertEqual(p['geometry']['footprint'], [[x, y] for y in (-2, -1) for x in (-1, 0, 1)])
        self.assertEqual(p['variants'], self.original[p['id']]['variants'])
        self.assertEqual(p['geometry']['collision'], self.original[p['id']]['geometry']['collision'])

    def test_force_keeps_trough_coverage(self):
        self.write(self.original['crossroads_trough'])
        self.assertEqual(self.run_batch(('crossroads_trough',))[0], 0)
        p = self.generated('crossroads_trough')
        self.assertEqual(p['geometry'], self.original[p['id']]['geometry'])
        self.assertEqual(p['variants'], self.original[p['id']]['variants'])

    def test_force_output_covers_continuous_rect_at_signed_phases(self):
        for p in self.original.values():
            self.write(p)
        self.assertEqual(self.run_batch()[0], 0)
        for pid in IDS:
            p = self.generated(pid)
            x, y, w, h = p['geometry']['collision']['rect']
            for variant in p['variants']:
                for ax in (-3, -0.5, 0, 0.5, 2, 2.5):
                    for ay in (-2, 0, 3):
                        with self.subTest(pid=pid, variant=variant['id'], at=(ax, ay)):
                            # Independent half-open collider/cell intersection oracle.
                            actual = {(cx, cy) for cx in range(-8, 9) for cy in range(-8, 9)
                                      if max(cx * 8, ax * 8 + x) < min((cx + 1) * 8, ax * 8 + x + w)
                                      and max(cy * 8, ay * 8 + y) < min((cy + 1) * 8, ay * 8 + y + h)}
                            entry = dict(piece=pid, variant=variant['id'], at=[ax * 24, ay * 24])
                            self.assertTrue(actual <= R._occupied(entry, p, {}), actual)

    def plan(self, p, at=(6.5, 6), target=None):
        rows = [list('.' * 16) for _ in range(12)]
        if target:
            rows[4][7] = target
        return dict(coordinate_space='cells', rows=[''.join(r) for r in rows],
                    legend={'.': 'earth', '~': 'water', '=': 'path'},
                    pieces=[dict(piece=p['id'], at=list(at))])

    def findings(self, p, **kwargs):
        materials = {'earth': {'surface': 'earth'}, 'water': {'surface': 'water', 'water': True},
                     'path': {'surface': 'path', 'route': True}}
        return R.check_zone(self.plan(p, **kwargs), {p['id']: p}, materials)

    def test_force_output_refuses_water_and_route_in_former_missing_column(self):
        self.write(self.original['crossroads_crates'])
        self.assertEqual(self.run_batch(('crossroads_crates',))[0], 0)
        p = self.generated('crossroads_crates')
        for target in ('~', '='):
            with self.subTest(target=target):
                self.assertTrue(any(f['check'] == 'rules.forbids' for f in self.findings(p, target=target)))

    def test_force_output_keeps_existing_grid_refusals(self):
        for pid in IDS:
            self.write(self.original[pid])
        self.assertEqual(self.run_batch()[0], 0)
        for pid in IDS:
            p = self.generated(pid)
            for at in ((6, 6), (6.5, 6)):
                self.assertEqual(self.findings(p, at=at), [])
            for at in ((6.25, 6), (6.5, 6.5)):
                self.assertIn('rules.off_grid', [f['check'] for f in self.findings(p, at=at)])

    def test_cell_phase_boundaries_exclude_touching_and_empty_boxes(self):
        for rect, expected in [([0, 0, 4, 8], [[0, 0]]),
                               ([-4, -8, 4, 8], [[-1, -1], [0, -1]]),
                               ([0, 0, 4.0001, 8], [[0, 0], [1, 0]]),
                               ([0, 0, 0, 8], []), ([0, 0, 8, -1], [])]:
            old = copy.deepcopy(self.original['crossroads_crates'])
            self.write(old)
            p = self.assemble(old['id'], {'shape': 'rect', 'rect': rect})
            self.assertEqual(p['geometry']['footprint'], expected, rect)

    def test_default_skip_keeps_existing_bytes_and_unrelated_files(self):
        paths = [self.write(p) for p in self.original.values()]
        unrelated = self.dest / 'prop/unrelated.json'
        unrelated.write_text('{"schema":"unrelated-fixture"}\n')
        before = {p: p.read_bytes() for p in paths + [unrelated]}
        self.assertEqual(self.run_batch(force=False)[0], 0)
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_force_preserves_authored_fields_and_is_idempotent(self):
        old = copy.deepcopy(self.original['crossroads_crates'])
        old['variants'][0].update(weight=2, note='authored fixture')
        old['geometry'].update(overhang=[[2, -1]], height_px=30)
        old['audit']['todo'].append('retain this fixture note')
        old['function']['saves'] = ['fixture.state']
        path = self.write(old)
        self.assertEqual(self.run_batch(('crossroads_crates',))[0], 0)
        p = self.generated(old['id'])
        for key in ('placement', 'rendering', 'approval', 'variants', 'function', 'story', 'gameplay'):
            self.assertEqual(p[key], old[key], key)
        for key in ('overhang', 'height_px'):
            self.assertEqual(p['geometry'][key], old['geometry'][key])
        self.assertIn('retain this fixture note', p['audit']['todo'])
        before = path.read_bytes()
        self.assertEqual(self.run_batch(('crossroads_crates',))[0], 0)
        self.assertEqual(path.read_bytes(), before)

    def test_reviewed_states_refuse_entire_batch_before_writing(self):
        for state in ('approved', 'gated', 'rejected', 'retired'):
            with self.subTest(state=state):
                paths = [self.write(p) for p in self.original.values()]
                reviewed = copy.deepcopy(self.original['crossroads_trough'])
                reviewed['approval']['state'] = state
                self.write(reviewed)
                before = {p: p.read_bytes() for p in paths}
                code, output = self.run_batch()
                self.assertEqual(code, 1)
                self.assertIn('refusing to overwrite reviewed piece', output)
                self.assertEqual({p: p.read_bytes() for p in paths}, before)

    def test_concurrent_edit_is_refused(self):
        p = self.write(self.original['crossroads_crates'])
        changed = p.read_text() + ' '
        code, output = self.run_batch(('crossroads_crates',), hook=lambda: p.write_text(changed))
        self.assertEqual(code, 1)
        self.assertIn('source changed while seeding', output)
        self.assertEqual(p.read_text(), changed)

    def test_unsupported_snap_and_collision_cases_keep_existing_derivation(self):
        for snap in (None, 'half', 'free'):
            for col in (None, {'shape': 'none'}, {'shape': 'circle', 'radius': 3},
                        {'shape': 'rect', 'rect': [-6, -10, 12, 10]}):
                old = copy.deepcopy(self.original['crossroads_crates'])
                if snap is None:
                    old['placement'].pop('snap')
                else:
                    old['placement']['snap'] = snap
                self.write(old)
                p = self.assemble(old['id'], col)
                expected = S.footprint(col['rect']) if col and col['shape'] == 'rect' else (
                    S.footprint([-3, -3, 6, 6]) if col and col['shape'] == 'circle' else [])
                self.assertEqual(p['geometry']['footprint'], expected)
                self.assertEqual(p['placement'], old['placement'])
        self.write(self.original['crossroads_crates'])
        for col, expected in [(None, []), ({'shape': 'none'}, []),
                              ({'shape': 'circle', 'radius': 3}, S.footprint([-3, -3, 6, 6]))]:
            self.assertEqual(self.assemble('crossroads_crates', col)['geometry']['footprint'], expected)


if __name__ == '__main__':
    unittest.main()

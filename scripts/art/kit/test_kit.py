"""Tests for the world editor's kit (docs/world-editor.md).

    python3 -m unittest scripts.art.kit.test_kit

The piece schema (valid pieces pass, each invalid fixture fails for its reason, the subset
validator agrees with `jsonschema` where installed), the kit's pictures are up to date with the
library, every fill tiles seamlessly, and every transition tile is canonical at its borders (so any
two tiles that share a border meet without a seam).
"""
from __future__ import annotations

import json
import os
import unittest

import numpy as np

from scripts.art.kit import build as B
from scripts.art.kit import edges as E
from scripts.art.kit import schema as S

FIX = os.path.join(S.ROOT, 'game', 'kit', 'schema', 'invalid')


class Schema(unittest.TestCase):
    def test_library_valid(self):
        bad = {p: e for p, e in S.check().items() if e}
        self.assertEqual(bad, {})

    def test_invalid_fixtures_fail(self):
        schema = S.load_schema()
        files = sorted(f for f in os.listdir(FIX) if f.endswith('.json'))
        self.assertGreaterEqual(len(files), 5)
        for f in files:
            case = json.load(open(os.path.join(FIX, f)))
            errs = S.errors(case['piece'], schema) + S.semantic(case['piece'])
            self.assertTrue(any(case['expect'] in e for e in errs), '%s: %s not in %s' % (f, case['expect'], errs))

    def test_agrees_with_jsonschema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        schema = S.load_schema()
        v = jsonschema.Draft202012Validator(schema)
        for p in S.piece_files():
            piece = json.load(open(p))
            self.assertEqual(bool(S.errors(piece, schema)), bool(list(v.iter_errors(piece))), p)
        for f in os.listdir(FIX):
            piece = json.load(open(os.path.join(FIX, f)))['piece']
            if json.load(open(os.path.join(FIX, f))).get('semantic'):
                continue
            self.assertEqual(bool(S.errors(piece, schema)), bool(list(v.iter_errors(piece))), f)


class Kit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kit = B.Kit()

    def test_built_and_current(self):
        self.assertEqual(B.build(check=True), 0)

    def test_fills_seamless(self):
        # across the wrap the fill changes no more than between neighbouring rows inside it
        for mid, f in self.kit.fills.items():
            self.assertEqual(f.shape, (self.kit.period, self.kit.period))
            across = np.mean(f[0] != f[-1]) + np.mean(f[:, 0] != f[:, -1])
            inside = np.mean(f[1] != f[0]) + np.mean(f[:, 1] != f[:, 0])
            self.assertLess(across, inside * 1.3, self.kit.names[mid])

    def test_tiles_canonical_at_borders(self):
        # within CALM texels of a border the coverage (upper or not) and the deltas depend only on
        # the border's side, which cells lie either side of it and the crossing's profile
        for tid, tiles in self.kit.over.items():
            seen = {}
            for idx, k, prof, v in E.layout(self.kit.variants):
                t = tiles[idx]
                q = [(k >> b) & 1 for b in range(4)]          # nw, ne, sw, se
                strips = {'n': (t[:E.CALM], (q[0], q[1])), 's': (t[-E.CALM:], (q[2], q[3])),
                          'w': (t[:, :E.CALM], (q[0], q[2])), 'e': (t[:, -E.CALM:], (q[1], q[3]))}
                for i, side in enumerate(E.SIDES):
                    strip, cells = strips[side]
                    key = (side, cells, prof[i])
                    sig = strip[..., 0] * 100000 + strip[..., 1]
                    if key in seen:
                        np.testing.assert_array_equal(sig, seen[key][0], '%s: tile %d (%s) differs from tile %d at its %s border' % (tid, idx, key, seen[key][1], side))
                    else:
                        seen[key] = (sig, idx)

    def test_layout_matches_shader(self):
        # the shader computes each mask's base by the same rule
        base = E.mask_base(self.kit.variants)
        n = E.NPROF
        b = 0
        for k in range(1, 15):
            self.assertEqual(base[k], b)
            b += n ** sum(E.crossings(k)) * self.kit.variants
        self.assertEqual(b, len(E.layout(self.kit.variants)))
        src = open(os.path.join(S.ROOT, 'game', 'world', 'terrain', 'terrain.gdshader')).read()
        for c in ('0x1B873593', '0xCC9E2D51', '0x38B34AE5', '0xA1C9B2F7',):
            self.assertIn(c, open(os.path.join(S.ROOT, 'game', 'world', 'terrain', 'terrain_dressing.gd')).read())
        for c in ('0x9E3779B1u', '0x85EBCA77u', '0xC2B2AE3Du', '0x27D4EB2Fu', '0x7FEB352Du',
                  '0x8DA6B343u', '0xD8163841u', '0xCB1AB31Fu', '0x2C1B3C6Du'):
            self.assertIn(c, src)



class Rules(unittest.TestCase):
    """The validator on kit zones (scripts/review/kit_rules.py): each rule trips on a plan that
    breaks it and stays quiet on one that keeps it."""

    def plan(self, rows, pieces=()):
        return {'zone': 't', 'legend': {'.': 'lawn', '#': 'path', '~': 'water'}, 'rows': rows, 'pieces': list(pieces)}

    def faults(self, plan, check):
        from scripts.review import kit_rules as KR
        return [f for f in KR.check_zone(plan) if f['check'] == check]

    def test_lab_and_woodland_pass(self):
        from scripts.review import kit_rules as KR
        for z in ('kitlab', 'woodland_kit'):
            plan = json.load(open(os.path.join(KR.ZONES, z + '.json')))
            self.assertEqual([f for f in KR.check_zone(plan) if f['severity'] == 'fault'], [], z)

    def test_bench(self):
        rows = ['......', '......', '######', '......']
        on = {'id': 'b', 'piece': 'woodland_forest_bench', 'at': [72, 72]}        # its foot in the path's row
        beside = {'id': 'b', 'piece': 'woodland_forest_bench', 'at': [72, 48]}    # on the turf, the path south of it
        far = {'id': 'b', 'piece': 'woodland_forest_bench', 'at': [72, 24]}
        self.assertTrue(self.faults(self.plan(rows, [on]), 'rules.route_clear'))
        self.assertFalse(self.faults(self.plan(rows, [beside]), 'rules.route_clear'))
        self.assertFalse(self.faults(self.plan(rows, [beside]), 'rules.seating'))
        self.assertTrue(self.faults(self.plan(['......', '......', '......', '######'], [far]), 'rules.seating'))

    def test_route_into_water(self):
        self.assertTrue(self.faults(self.plan(['..#...', '..#...', '~~~~~~', '......']), 'rules.route_water'))
        self.assertFalse(self.faults(self.plan(['..#...', '......', '~~~~~~', '......']), 'rules.route_water'))

    def test_water_ends(self):
        self.assertTrue(self.faults(self.plan(['......', '.~~~..', '......', '......']), 'rules.water_end'))
        self.assertFalse(self.faults(self.plan(['......', '.~~~..', '.~~~..', '......']), 'rules.water_end'))   # a pool
        self.assertFalse(self.faults(self.plan(['~~~~~~', '......', '......', '......']), 'rules.water_end'))   # to the edge

    def test_tiers(self):
        rows = ['..##..', '..##..', '..##..', '..##..', '..##..', '..##..']
        tiers = ['111111', '111111', '000000', '000000', '000000', '000000']    # faces fall on rows 2 and 3
        plan = dict(self.plan(rows), tiers=tiers)
        self.assertTrue(self.faults(plan, 'rules.tier_route'))
        steps = {'id': 's', 'piece': 'log_steps', 'at': [72, 96], 'variant': 'w2'}   # the flight over the face, foot on row 4
        plan2 = dict(self.plan(rows, [steps]), tiers=tiers)
        self.assertFalse(self.faults(plan2, 'rules.tier_route'))
        self.assertFalse(self.faults(plan2, 'rules.stair'))
        wrong = dict(self.plan(rows, [dict(steps, at=[72, 144])]), tiers=tiers)    # a cell too low: half on the lawn
        self.assertTrue(self.faults(wrong, 'rules.stair'))

    def test_water_fall(self):
        rows = ['..~~..'] * 6
        tiers = ['111111', '111111', '000000', '000000', '000000', '000000']   # the faces on rows 2 and 3
        self.assertTrue(self.faults(dict(self.plan(rows), tiers=tiers), 'rules.water_fall'))
        fall = {'id': 'f', 'piece': 'waterfall_2', 'at': [72, 96], 'variant': 'w2'}
        self.assertFalse(self.faults(dict(self.plan(rows, [fall]), tiers=tiers), 'rules.water_fall'))
        aside = dict(fall, at=[24, 96])                                         # off the channel
        self.assertTrue(self.faults(dict(self.plan(rows, [aside]), tiers=tiers), 'rules.water_fall'))
        # Matt, 2 Nov: the fall continues its channel: a three-cell channel over a two-cell fall,
        # or a fall with no pool under its face, is a fault
        wide = ['.~~~..', '.~~~..', '..~~..', '..~~..', '..~~..', '..~~..']
        self.assertTrue(self.faults(dict(self.plan(wide, [fall]), tiers=tiers), 'rules.water_fall'))
        dry = ['..~~..', '..~~..', '..~~..', '..~~..', '......', '......']
        self.assertTrue(self.faults(dict(self.plan(dry, [fall]), tiers=tiers), 'rules.water_fall'))

    def test_waterfall_pictures_start_at_the_rim(self):
        """Each waterfall picture draws nothing above the rim and, above the pool, nothing outside
        its sheet: the sheet is the channel's width (sheet_px) and starts on the face's top edge."""
        from PIL import Image
        from scripts.art.kit.schema import ROOT
        for c in (1, 2, 3, 4):
            for tall in ('', '_tall'):
                pc = json.load(open(os.path.join(ROOT, 'game', 'kit', 'pieces', 'structure', 'waterfall_%d%s.json' % (c, tall))))
                x0, x1, y0, y1 = pc['geometry']['sheet_px']
                self.assertEqual(x1 - x0, 24 * c)
                self.assertEqual((pc['geometry']['foot'][0] - x0) * 2, x1 - x0)
                self.assertEqual(pc['geometry']['foot'][1], y1)
                a = np.asarray(Image.open(os.path.join(ROOT, 'game', pc['variants'][0]['png'][len('res://'):])))[..., 3] > 0
                self.assertFalse(a[:y0].any(), pc['id'])
                above = a[:y1 - 5].copy()
                above[:, x0:x1] = False
                self.assertFalse(above.any(), pc['id'])
                self.assertTrue(a[y0, x0:x1].all(), pc['id'])


class Crossings(unittest.TestCase):
    def test_stepping_stones_carry_a_footpath(self):
        from scripts.review import kit_rules as KR
        rows = ['..#...', '..#...', '~~~~~~', '~~~~~~', '..#...', '..#...']
        plan = {'zone': 't', 'legend': {'.': 'lawn', '#': 'path', '~': 'water'}, 'rows': rows, 'pieces': []}
        self.assertTrue([f for f in KR.check_zone(plan) if f['check'] == 'rules.route_water'])
        plan['pieces'] = [{'id': 's', 'piece': 'stepping_stones_2', 'at': [60, 120], 'variant': 'w2'}]
        self.assertFalse([f for f in KR.check_zone(plan) if f['check'] in ('rules.route_water', 'rules.deck')])


class Surface(unittest.TestCase):
    """Width classes and surface variants (scripts/art/kit/surface.py) and the baked grounds."""

    def test_widths(self):
        from scripts.art.kit import surface as SF
        c = np.zeros((10, 12), bool)
        c[4:6, :] = True            # a lane across
        c[:, 3:5] = True            # a lane down: their junction stays a lane
        c[0:3, 8:11] = True         # a road three cells across
        w = SF.widths(c)
        self.assertEqual(int(w[4, 0]), 2)
        self.assertEqual(int(w[4, 3]), 2)
        self.assertEqual(int(w[1, 9]), 3)
        self.assertEqual(list(SF.water_class(np.array([1, 2, 3, 5, 6, 8]))), [1, 2, 3, 3, 6, 6])

    def test_variants_never_repeat_a_neighbour(self):
        from scripts.art.kit import surface as SF
        c = np.ones((12, 16), bool)
        ctx = {k: np.zeros((12, 16), bool) for k in ('tree', 'water', 'door', 'route', 'shore')}
        for kind in ('dirt', 'lawn', 'water'):
            v = SF.assign(kind, c, None, dict(ctx, cls=np.full((12, 16), 2)), 5)
            self.assertFalse(((v[:, 1:] == v[:, :-1]) & (v[:, 1:] != 'b')).any(), kind)
            self.assertFalse(((v[1:] == v[:-1]) & (v[1:] != 'b')).any(), kind)
            given = np.full((12, 16), '.', '<U1')
            given[3, 4] = 's' if kind == 'dirt' else 'b'
            self.assertEqual(SF.assign(kind, c, given, dict(ctx, cls=np.full((12, 16), 2)), 5)[3, 4], given[3, 4])

    def test_baked_grounds_current(self):
        from scripts.art.kit import bake as BK
        self.assertEqual(BK.check(), 0)

    def test_woodland_reaches_the_painted_bar(self):
        from scripts.art.kit import detail_bar as DB
        res = DB.compare('woodland_kit', os.path.join(S.ROOT, 'game', 'zones', 'woodland', 'art', 'ground.png'))
        for name in ('water', 'path', 'shadow', 'lawn'):
            self.assertTrue(res[name]['pass'], (name, res[name]))




class SchemaMigrationTooling(unittest.TestCase):
    """Migrations follow declared schema ids and never guess from piece revision numbers."""

    def piece(self, ident='fixture'):
        return {'schema': S.load_schema()['$id'], 'id': ident, 'name': 'Fixture', 'kind': 'decal',
                'version': 17, 'approval': {'state': 'candidate'}}

    def steps(self):
        target = S.load_schema()['$id']
        return {'test.piece/old': (target, lambda p: dict(p, schema=target))}

    def write_piece(self, directory, piece):
        path = os.path.join(directory, piece['id'] + '.json')
        with open(path, 'w') as handle:
            json.dump(piece, handle)
        return path

    def test_concept_is_valid_but_not_approval(self):
        piece = self.piece()
        piece['approval']['state'] = 'concept'
        self.assertEqual(S.errors(piece, S.load_schema()) + S.semantic(piece), [])
        try:
            import jsonschema
        except ImportError:
            jsonschema = None
        if jsonschema is not None:
            self.assertEqual(list(jsonschema.Draft202012Validator(S.load_schema()).iter_errors(piece)), [])
        piece['approval']['state'] = 'approved'
        self.assertTrue(S.semantic(piece))  # adding concept did not weaken the approved gate

    def test_current_is_a_deep_copy_and_preserves_piece_revision(self):
        original = self.piece()
        result = S.migrate_piece(original)
        self.assertEqual(result, original)
        self.assertIsNot(result['approval'], original['approval'])
        self.assertEqual(result['version'], 17)

    def test_unknown_schema_is_refused_without_guessing(self):
        piece = dict(self.piece(), schema='test.piece/unknown', version=1)
        with self.assertRaisesRegex(ValueError, 'no migration'):
            S.migrate_piece(piece)

    def test_registered_chain_preserves_fields_and_input(self):
        import copy
        target = S.load_schema()['$id']
        piece = dict(self.piece(), schema='test.piece/first', story={'owner': 'Hale'})
        original = copy.deepcopy(piece)
        steps = {'test.piece/first': ('test.piece/second', lambda p: dict(p, schema='test.piece/second')),
                 'test.piece/second': (target, lambda p: dict(p, schema=target))}
        result = S.migrate_piece(piece, migrations=steps)
        self.assertEqual(piece, original)
        self.assertEqual(result, dict(piece, schema=target))
        self.assertEqual(result['version'], 17)

    def test_broken_and_cyclic_migrations_are_refused(self):
        piece = dict(self.piece(), schema='test.piece/old')
        with self.assertRaisesRegex(ValueError, 'must produce schema'):
            S.migrate_piece(piece, migrations={'test.piece/old': ('test.piece/next', lambda p: p)})
        cycle = {'test.piece/old': ('test.piece/other', lambda p: dict(p, schema='test.piece/other')),
                 'test.piece/other': ('test.piece/old', lambda p: dict(p, schema='test.piece/old'))}
        with self.assertRaisesRegex(ValueError, 'cycle'):
            S.migrate_piece(piece, migrations=cycle)
        with self.assertRaisesRegex(ValueError, 'invalid'):
            S.migrate_piece(piece, migrations={'test.piece/old': (S.load_schema()['$id'],
                            lambda p: dict(p, schema=S.load_schema()['$id'], version=0))})

    def test_current_file_is_byte_and_mtime_identical(self):
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_piece(directory, self.piece())
            before = pathlib.Path(path).read_bytes(), os.stat(path).st_mtime_ns
            self.assertEqual(S.migrate_files([path]), {path: False})
            self.assertEqual((pathlib.Path(path).read_bytes(), os.stat(path).st_mtime_ns), before)

    def test_batch_refusal_leaves_all_originals(self):
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            first = self.write_piece(directory, dict(self.piece('first'), schema='test.piece/old'))
            second = self.write_piece(directory, dict(self.piece('second'), schema='test.piece/unknown'))
            before = [pathlib.Path(p).read_bytes() for p in (first, second)]
            with self.assertRaisesRegex(ValueError, 'no migration'):
                S.migrate_files([first, second], migrations=self.steps())
            self.assertEqual([pathlib.Path(p).read_bytes() for p in (first, second)], before)
            self.assertFalse(any(f.startswith('.piece-migrate-') for f in os.listdir(directory)))

    def test_conversion_dry_run_and_permissions(self):
        import pathlib
        import stat
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            old = dict(self.piece(), schema='test.piece/old', story={'owner': 'Hale'})
            path = self.write_piece(directory, old)
            os.chmod(path, 0o640)
            before = pathlib.Path(path).read_bytes()
            self.assertEqual(S.migrate_files([path], migrations=self.steps(), dry_run=True), {path: True})
            self.assertEqual(pathlib.Path(path).read_bytes(), before)
            self.assertEqual(S.migrate_files([path], migrations=self.steps()), {path: True})
            self.assertEqual(json.loads(pathlib.Path(path).read_text()), dict(old, schema=S.load_schema()['$id']))
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)
            self.assertFalse(any(f.startswith('.piece-migrate-') for f in os.listdir(directory)))

    def test_later_replace_failure_rolls_back_the_batch(self):
        import pathlib
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as directory:
            paths = [self.write_piece(directory, dict(self.piece(name), schema='test.piece/old'))
                     for name in ('first', 'second')]
            before = [pathlib.Path(p).read_bytes() for p in paths]
            replace = os.replace
            calls = []

            def fail_second(source, target):
                calls.append(target)
                if len(calls) == 2:
                    raise OSError('fixture replacement failure')
                return replace(source, target)

            with mock.patch.object(S.os, 'replace', side_effect=fail_second):
                with self.assertRaisesRegex(OSError, 'fixture replacement failure'):
                    S.migrate_files(paths, migrations=self.steps())
            self.assertEqual([pathlib.Path(p).read_bytes() for p in paths], before)
            self.assertFalse(any(f.startswith('.piece-migrate-') for f in os.listdir(directory)))

    def test_filename_and_duplicate_identity_are_checked_before_writes(self):
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_piece(directory, dict(self.piece(), schema='test.piece/old'))
            before = pathlib.Path(path).read_bytes()
            with self.assertRaisesRegex(ValueError, 'also in'):
                S.migrate_files([path, path], migrations=self.steps())
            self.assertEqual(pathlib.Path(path).read_bytes(), before)
            renamed = os.path.join(directory, 'other.json')
            os.rename(path, renamed)
            with self.assertRaisesRegex(ValueError, 'differs from its file name'):
                S.migrate_files([renamed], migrations=self.steps())
            self.assertEqual(pathlib.Path(renamed).read_bytes(), before)

    def test_concurrent_edit_is_preserved(self):
        import pathlib
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_piece(directory, dict(self.piece(), schema='test.piece/old'))
            stage = S._stage_bytes
            concurrent = b'{"authored": "concurrent change"}\n'

            def edit_while_staging(*args):
                tmp = stage(*args)
                pathlib.Path(path).write_bytes(concurrent)
                return tmp

            with mock.patch.object(S, '_stage_bytes', side_effect=edit_while_staging):
                with self.assertRaisesRegex(ValueError, 'changed while migration'):
                    S.migrate_files([path], migrations=self.steps())
            self.assertEqual(pathlib.Path(path).read_bytes(), concurrent)
            self.assertFalse(any(f.startswith('.piece-migrate-') for f in os.listdir(directory)))

    def test_failed_rollback_retains_original_for_recovery(self):
        import pathlib
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as directory:
            paths = [self.write_piece(directory, dict(self.piece(name), schema='test.piece/old'))
                     for name in ('first', 'second')]
            original = pathlib.Path(paths[0]).read_bytes()
            replace = os.replace
            calls = []

            def fail_after_first(source, target):
                calls.append(target)
                if len(calls) > 1:
                    raise OSError('fixture disk failure')
                return replace(source, target)

            with mock.patch.object(S.os, 'replace', side_effect=fail_after_first):
                with self.assertRaisesRegex(OSError, 'original retained at'):
                    S.migrate_files(paths, migrations=self.steps())
            retained = [os.path.join(directory, f) for f in os.listdir(directory)
                        if f.startswith('.piece-migrate-')]
            self.assertEqual(len(retained), 1)
            self.assertEqual(pathlib.Path(retained[0]).read_bytes(), original)

    def test_source_bindings_are_closed_and_match_jsonschema(self):
        import copy
        try:
            import jsonschema
        except ImportError:
            self.skipTest('jsonschema not installed')
        piece = self.piece()
        piece['audit'] = {'sources': [{'zone': 'woodland', 'object': 'tree01', 'part': 'body',
                                      'condition': {'flag': 'woodland_restored'}}]}
        validator = jsonschema.Draft202012Validator(S.load_schema())
        self.assertEqual(S.errors(piece, S.load_schema()), [])
        self.assertEqual(list(validator.iter_errors(piece)), [])
        for bad in ({'zone': 'woodland', 'object': 'tree01'},
                    {'zone': 'woodland', 'object': 'tree01', 'part': 'unknown'},
                    {'zone': 'woodland', 'object': 'tree01', 'part': 'body', 'typo': True}):
            invalid = copy.deepcopy(piece)
            invalid['audit']['sources'] = [bad]
            self.assertTrue(S.errors(invalid, S.load_schema()))
            self.assertTrue(list(validator.iter_errors(invalid)))


class SeedCompleteness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.art.kit import seed_props as seed
        cls.seed = seed
        cls.pieces = seed.seed()
        cls.index = seed.source_index(cls.pieces)
        cls.by_id = {p['id']: p for p in cls.pieces}

    def test_every_source_id_including_attachments_is_mapped_once(self):
        expected = set()
        for zone in ('woodland', 'crossroads'):
            kit = self.seed._read('game/zones/' + zone + '/kit.json')
            expected.update((zone, o[0] if isinstance(o, list) else o['id']) for o in kit['objects'])
        self.assertEqual(set(self.index), expected | {('woodland', 'StoneSign')})
        self.assertEqual(len(expected), 183)
        self.assertEqual(len(self.by_id), len(self.pieces))

    def test_attachment_ids_are_on_their_owners_with_exact_conditions(self):
        kit = self.seed._read('game/zones/crossroads/kit.json')
        objects = {o['id']: o for o in kit['objects']}
        for oid, owner in [('smithy_damage', 'smithy'), ('smithy_boards', 'smithy'),
                           ('forge_fire', 'smithy'), ('fern_boards', 'fern_cottage'),
                           ('well_shadow', 'well')]:
            with self.subTest(object=oid):
                pid = self.index['crossroads', oid]
                self.assertEqual(pid, self.index['crossroads', owner])
                p = self.by_id[pid]
                source = next(s for s in p['audit']['sources'] if s['object'] == oid)
                self.assertEqual(source['condition'], objects[oid]['cond'])
                self.assertNotIn(oid, [v['id'] for v in p['variants']])

    def test_blocking_and_nonblocking_bushes_cannot_share_collision(self):
        solid = self.by_id[self.index['crossroads', 'bush_7']]
        clear = self.by_id[self.index['crossroads', 'bush_14']]
        self.assertNotEqual(solid['id'], clear['id'])
        self.assertTrue(solid['gameplay']['blocks_move'])
        self.assertFalse(clear['gameplay']['blocks_move'])
        self.assertEqual(clear['geometry']['collision'], {'shape': 'none'})

    def test_all_authored_boxes_recover_from_reusable_local_geometry(self):
        kit = self.seed._read('game/zones/crossroads/kit.json')
        for obj in kit['objects']:
            if not obj.get('solid'):
                continue
            p = self.by_id[self.index['crossroads', obj['id']]]
            if 'collision' in p['audit'].get('overrides', []):
                continue                    # reviewed against the art and the size guide (farm.REVIEWED_BOXES)
            r = p['geometry']['collision']['rect']
            actual = [r[0] + obj['foot'][0] / 3, r[1] + obj['foot'][1] / 3, *r[2:]]
            np.testing.assert_allclose(actual, obj['solid'], atol=0.00001, err_msg=obj['id'])

    def test_per_variant_anchors_match_source_offsets(self):
        kit = self.seed._read('game/zones/crossroads/kit.json')
        for obj in kit['objects']:
            if not obj.get('png') or obj['kind'] in ('shadow', 'damage', 'glow', 'smoke'):
                continue
            p = self.by_id[self.index['crossroads', obj['id']]]
            if 'variants' in p['audit'].get('overrides', []):
                continue                    # redrawn in the kit (farm.REDRAWN); the source keeps its own picture
            v = next(v for v in p['variants'] if v['id'] == os.path.splitext(obj['png'])[0])
            self.assertEqual(v['foot'], [-n for n in obj['offset']], obj['id'])

    def test_unknown_woodland_collision_is_not_fabricated(self):
        # the seeder never guesses a woodland box: a piece has none (and says so) unless Claude
        # authored one, which a refresh keeps (2 Nov, from the shipped prop scenes)
        for p in self.pieces:
            if p['id'].startswith('woodland_') and p['id'] != 'woodland_stone_sign':
                if p['geometry']['collision'] is None:
                    self.assertNotIn('blocks_move', p['gameplay'])
                    self.assertTrue(any('unknown' in t for t in p['audit']['todo']))
                else:
                    self.assertTrue(any('authored by Claude A' in t for t in p['audit']['todo']), p['id'])

    def test_thin_and_negative_local_collisions_keep_coverage(self):
        self.assertEqual(self.seed.footprint([-1, -1, 2, 2]), [[-1, -1], [0, -1], [-1, 0], [0, 0]])
        self.assertEqual(self.seed.footprint([-8, -8, 8, 8]), [[-1, -1]])
        self.assertEqual(self.seed.footprint([0, 0, 0, 1]), [])

    def test_restore_links_use_explicit_building_mapping(self):
        smithy = self.by_id['crossroads_smithy']
        self.assertEqual(smithy['story']['milestone'], 'forge')
        self.assertIn('village.restored.forge', smithy['function']['saves'])
        self.assertIn('res://data/quests/cold_forge.json', smithy['story']['quests'])
        triggers = smithy['function']['interact']['triggers']
        self.assertTrue(any(t['type'] == 'restore' and '#/restores/0' in t['ref'] for t in triggers))
        self.assertNotIn('milestone', self.by_id['crossroads_library']['story'])
        self.assertNotIn('interact', self.by_id['crossroads_library']['function'])

    def test_authored_interactions_preserve_actual_speakers(self):
        board = self.by_id['crossroads_notice_board']
        self.assertEqual(board['function']['interact']['verb'], 'read')
        self.assertEqual(board['geometry']['collision']['shape'], 'circle')
        self.assertEqual(board['function']['interact']['triggers'],
                         [{'type': 'dialogue', 'ref': 'res://data/dialogue/crossroads.json#/notice_board'}])
        stone = self.by_id['crossroads_waystone']
        self.assertEqual(stone['function']['interact']['verb'], 'use')
        self.assertEqual(stone['geometry']['interaction_points'][0]['verb'], 'Touch')
        self.assertNotIn('dialogue', self.by_id['crossroads_well']['story'])

    def test_generated_batch_is_valid_and_deterministic(self):
        self.assertEqual(self.seed.seed(), self.pieces)
        for p in self.pieces:
            self.assertEqual(S.errors(p, S.load_schema()) + S.semantic(p), [], p['id'])
            with open(os.path.join(S.PIECES, p['kind'], p['id'] + '.json')) as f:
                saved = json.load(f)
            self.assertEqual(saved, p, p['id'])

    def test_restore_interactions_keep_source_predicates_on_points(self):
        smithy = self.by_id['crossroads_smithy']
        fern = self.by_id['crossroads_fern_cottage']
        self.assertEqual(smithy['geometry']['interaction_points'][0]['if'], {'not_restored': ['forge']})
        self.assertEqual(fern['geometry']['interaction_points'][0]['if'],
                         {'flags': ['shard_home:woodland'], 'not_restored': ['fern_cottage']})
        self.assertNotIn('gating', smithy['story'])
        self.assertNotIn('gating', fern['story'])

    def test_source_order_cannot_change_piece_ids_or_provenance(self):
        from unittest.mock import patch
        read = self.seed._read
        def reversed_kit(path):
            data = read(path)
            if path.endswith('/kit.json'):
                data['objects'].reverse()
            return data
        with patch.object(self.seed, '_read', side_effect=reversed_kit):
            self.assertEqual(self.seed.seed(), self.pieces)

    def test_scene_only_quest_sign_is_seeded_with_real_source_behavior(self):
        sign = self.by_id['woodland_stone_sign']
        self.assertEqual(sign['audit']['seeded_from'], 'game/zones/woodland/woodland.tscn')
        self.assertEqual(sign['geometry']['foot'], [16.0, 40.0])
        self.assertEqual(sign['geometry']['collision'], {'shape': 'circle', 'radius': 5 / 3})
        self.assertEqual(sign['function']['interact']['triggers'],
                         [{'type': 'dialogue', 'ref': 'res://data/dialogue/woodland.json#/stone_sign'}])
        self.assertIn('res://data/quests/woodland_stones.json', sign['story']['quests'])
        self.assertTrue(any('placeholder' in t for t in sign['audit']['todo']))

    def test_force_cannot_resurrect_or_overwrite_reviewed_pieces(self):
        import copy
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import contextlib
        import io
        for state in ('approved', 'gated', 'rejected', 'retired'):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                p = copy.deepcopy(self.pieces[0])
                old = copy.deepcopy(p)
                old['approval'].update(state=state, by='reviewer', at='2026-10-27')
                target = Path(tmp) / old['kind'] / (old['id'] + '.json')
                target.parent.mkdir()
                target.write_text(json.dumps(old))
                before = target.read_bytes()
                with patch.object(self.seed, 'PIECES', tmp), patch.object(self.seed, 'seed', return_value=[p]), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(self.seed.main(['--force']), 1)
                self.assertEqual(target.read_bytes(), before)

    def test_refresh_preserves_authored_variants_and_nested_metadata(self):
        import copy
        from unittest.mock import patch
        lookup = self.seed._existing
        authored = copy.deepcopy(self.by_id['crossroads_notice_board'])
        authored['variants'].append(dict(authored['variants'][0], id='curated_board', note='reviewed alternate'))
        authored['function']['interact']['triggers'].append({'type': 'menu', 'ref': 'journal'})
        authored['story'].update(lore='Authored lore', quests=['res://data/quests/home_again.json'])
        authored['geometry']['overhang'] = [[0, -1]]
        def existing(pid):
            return copy.deepcopy(authored) if pid == authored['id'] else lookup(pid)
        with patch.object(self.seed, '_existing', side_effect=existing):
            refreshed = next(p for p in self.seed.seed() if p['id'] == authored['id'])
        self.assertIn('curated_board', [v['id'] for v in refreshed['variants']])
        self.assertIn({'type': 'menu', 'ref': 'journal'}, refreshed['function']['interact']['triggers'])
        self.assertEqual(refreshed['story']['lore'], 'Authored lore')
        self.assertIn('res://data/quests/home_again.json', refreshed['story']['quests'])
        self.assertEqual(refreshed['geometry']['overhang'], [[0, -1]])

    def test_concurrent_seed_edit_is_refused_before_writes(self):
        import copy
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            p = copy.deepcopy(self.pieces[0])
            target = Path(tmp) / p['kind'] / (p['id'] + '.json')
            target.parent.mkdir()
            target.write_text(json.dumps(p))
            authored = dict(p, name='Concurrent authored change')
            edited = json.dumps(authored)
            def prepare():
                target.write_text(edited)
                return [p]
            with patch.object(self.seed, 'PIECES', tmp), patch.object(self.seed, 'seed', side_effect=prepare), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.seed.main(['--force']), 1)
            self.assertEqual(target.read_text(), edited)


class ConceptIntake(unittest.TestCase):
    def concept(self, kind):
        return {'schema': 'napattack.piece/1', 'id': 'concept_fixture', 'name': 'Concept',
                'kind': kind, 'version': 1, 'approval': {'state': 'concept'}}

    def test_pre_art_concepts_can_defer_runtime_blocks(self):
        for kind in ('terrain', 'transition', 'prop', 'structure'):
            with self.subTest(kind=kind):
                p = self.concept(kind)
                self.assertEqual(S.errors(p, S.load_schema()) + S.semantic(p), [])
                p['approval']['state'] = 'candidate'
                self.assertTrue(S.semantic(p))

    def test_supplied_concept_blocks_are_still_strict(self):
        p = self.concept('terrain')
        p['terrain'] = {'typo': True}
        self.assertTrue(S.errors(p, S.load_schema()))

    def test_concepts_are_valid_outside_and_refused_in_live_library(self):
        from pathlib import Path
        from unittest.mock import patch
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            live = Path(tmp) / 'live'
            live.mkdir()
            outside = Path(tmp) / 'concept_fixture.json'
            inside = live / 'concept_fixture.json'
            data = json.dumps(self.concept('terrain'))
            outside.write_text(data)
            inside.write_text(data)
            with patch.object(S, 'PIECES', str(live)):
                self.assertEqual(S.check([str(outside)])[str(outside)], [])
                self.assertEqual(S.migrate_files([str(outside)]), {str(outside): False})
                with self.assertRaisesRegex(ValueError, 'non-buildable/non-placeable'):
                    S.migrate_files([str(inside)])
                self.assertTrue(any('non-buildable/non-placeable' in e for e in S.check([str(inside)])[str(inside)]))


class BakeMaterialOrder(unittest.TestCase):
    def test_real_plan_order_is_stable_across_process_hash_seeds(self):
        import subprocess
        import sys
        code = """import json,numpy as np
from scripts.art.kit import bake as B
plan=json.load(open('game/kit/zones/woodland_kit.json'))
mat=np.array([[plan['legend'][c] for c in row] for row in plan['rows']])
paint=B.material_paints(mat.ravel(),B._pieces_lib())
print(json.dumps([m for m,p in sorted(paint.items(),key=lambda item:item[1].get('order',0)) if p.get('fn')=='dirt']))
"""
        results = []
        for seed in ('0', '2', '7', '42'):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            results.append(json.loads(subprocess.check_output([sys.executable, '-c', code], cwd=S.ROOT, env=env)))
        self.assertEqual(results, [['worn', 'path']] * len(results))

    def test_authored_paint_order_overrides_the_canonical_tie(self):
        from scripts.art.kit import bake as B
        lib = {'path': {'terrain': {'paint': {'fn': 'dirt', 'order': 0}}},
               'worn': {'terrain': {'paint': {'fn': 'dirt', 'order': 2}}}}
        paint = B.material_paints(['worn', 'path', 'worn'], lib)
        self.assertEqual(list(paint), ['worn', 'path'])
        self.assertEqual([m for m,p in sorted(paint.items(),key=lambda item:item[1].get('order',0))], ['path', 'worn'])


class FencesAndFarm(unittest.TestCase):
    """The fence cells close loops, the farmyard pieces carry what the enclosure rules read, the
    farm study built from kit pieces passes every check, and the pictures are what the painters
    draw (scripts/art/kit/fences.py, farm.py, enclosures.py, farm_study.py; 3 Nov)."""

    @classmethod
    def setUpClass(cls):
        from scripts.art.kit import enclosures as EN
        from scripts.art.kit import farm_study as FS
        cls.EN, cls.FS = EN, FS
        cls.lib = EN.library()
        cls.plan = FS.plan()

    def test_pictures_are_what_the_painters_draw(self):
        from scripts.art.kit import farm, fences
        self.assertEqual(fences.check(), 0)
        self.assertEqual(farm.check(), 0)

    def test_every_fence_cell_and_gate_exists_in_both_styles(self):
        for style in ('wattle', 'picket', 'rail'):
            for mask in range(1, 16):
                jn = ''.join(c for i, c in enumerate('nesw') if mask & (1 << i))
                b = self.lib['fence_%s_%s' % (style, jn)]['placement']['boundary']
                self.assertEqual(''.join(b['joins']), jn)
                self.assertFalse(b['gate'])
            for ax in ('ew', 'ns'):
                g = self.lib['fence_%s_gate_%s' % (style, ax)]
                self.assertTrue(g['placement']['boundary']['gate'])
                self.assertIn({'rel': 'on', 'what': 'route', 'note': g['placement']['requires'][0]['note']}, g['placement']['requires'])
                self.assertFalse(g['gameplay']['blocks_move'])

    def test_farm_pieces_carry_purpose_collision_and_enclosure(self):
        for pid in ('farm_hen_white', 'farm_hen_brown', 'farm_hen_speckled', 'farm_sheep', 'farm_sheep_graze', 'farm_sheep_lie',
                    'farm_coop', 'farm_shelter', 'garden_flower_border', 'crossroads_trough', 'crossroads_beds_dug',
                    'farm_cow', 'farm_calf', 'farm_horse', 'farm_pig', 'farm_goat', 'farm_goat_b', 'farm_sty', 'farm_wallow'):
            p = self.lib[pid]
            self.assertIn('purpose', p['placement'], pid)
            self.assertIn('enclosure', p['placement'], pid)
            self.assertIn('collision', p['geometry'], pid)
            self.assertIn('size_px', p['geometry'], pid)

    def test_the_farm_study_passes_every_check(self):
        from scripts.art.kit import relations as RL
        from scripts.review import kit_rules as KR
        self.assertEqual([f for f in KR.check_zone(self.plan) if f['severity'] == 'fault'], [])
        self.assertEqual(RL.check_zone(self.plan), [])
        self.assertEqual(self.EN.check_zone(self.plan, self.lib), [])
        from scripts.art.kit import placement_audit as PA
        self.assertEqual(PA.check_plan(self.plan), [])

    def test_the_farm_study_is_staged_clear(self):
        # every animal a cell inside its fence and off the gateway; nothing drawn over a fence
        # behind it or over another piece (Claude A's review of #430)
        self.assertEqual(self.FS.layout_faults(self.plan), [])

    def test_open_runs_empty_pens_and_missing_needs_are_caught(self):
        import copy

        def without(*ids):
            q = copy.deepcopy(self.plan)
            q['pieces'] = [x for x in q['pieces'] if x['id'] not in ids and not any(x['id'].startswith(i + '*') for i in ids)]
            return [f['message'] for f in self.EN.check_zone(q, self.lib)]
        self.assertTrue(any('meets no run' in m for m in without('run_9_12')))
        self.assertTrue(any('no coop' in m for m in without('coop')))
        self.assertTrue(any('holds nothing' in m for m in without('sheep_1', 'sheep_2', 'sheep_3', 'trough', 'hay', 'shelter')))
        self.assertTrue(any('meets no run' in m for m in without('fold_gate')))

    def test_paddocks_sties_and_goat_pens_need_what_their_stock_needs(self):
        # round 3: a paddock needs water and a field shelter, a sty's run a wallow and a trough
        # (the sty's own, in its wall), a goat pen a shelter and water
        import copy

        def without(*ids):
            q = copy.deepcopy(self.plan)
            q['pieces'] = [x for x in q['pieces'] if x['id'] not in ids]
            return [f['message'] for f in self.EN.check_zone(q, self.lib)]
        self.assertTrue(any('holds cattle but has no shelter' in m for m in without('pd_shelter')))
        self.assertTrue(any('holds horses but has no trough' in m for m in without('pd_trough')))
        self.assertTrue(any('holds pigs but has no wallow' in m for m in without('wallow')))
        # the sty is the run's north side: without it the run's end posts stand free
        self.assertTrue(any('sty_66_8' in m and 'standing free' in m for m in without('sty')))
        self.assertTrue(any('holds goats but has no shelter' in m for m in without('gt_shelter')))

    def test_a_stile_keeps_stock_in_and_stands_on_its_footpath(self):
        import copy
        from scripts.art.kit import relations as RL
        for sid in ('fence_rail_stile_ns', 'fence_rail_stile_ew'):
            st = self.lib[sid]
            self.assertTrue(st['placement']['boundary']['stile'])
            self.assertFalse(st['placement']['boundary']['gate'])
            self.assertFalse(st['gameplay']['blocks_move'])
        # the study's stile is in the paddock's north rails, on the footpath down column 44
        q = copy.deepcopy(self.plan)
        q['pieces'] = [x for x in q['pieces'] if x['id'] != 'paddock_44_2']
        self.assertTrue(any('meets no run' in f['message'] for f in self.EN.check_zone(q, self.lib)))
        q = copy.deepcopy(self.plan)
        q['rows'][2] = q['rows'][2][:44] + '.' + q['rows'][2][45:]
        self.assertTrue(any(f['message'].startswith('paddock_44_2: requires on route') for f in RL.check_zone(q)))

    def test_rail_fences_keep_cattle_and_hurdles_do_not(self):
        import copy
        q = copy.deepcopy(self.plan)
        for pc in q['pieces']:
            if pc['id'].startswith('paddock_') and pc['piece'].startswith('fence_rail_') and 'stile' not in pc['piece']:
                pc['piece'] = pc['piece'].replace('fence_rail_', 'fence_wattle_')
                pc.pop('variant', None)
        msgs = [f['message'] for f in self.EN.check_zone(q, self.lib)]
        self.assertTrue(any('holds cattle' in m and 'wattle fence' in m for m in msgs), msgs)

    def test_a_mixed_run_is_judged_stretch_by_stretch(self):
        # the Codex lead's review of #430: a sheep fold of wattle with one side in picket must
        # fault, though wattle alone would keep the sheep
        import copy
        q = copy.deepcopy(self.plan)
        swapped = 0
        for pc in q['pieces']:
            if pc['id'].startswith('fold_20_') and pc['piece'].startswith('fence_wattle_'):
                pc['piece'] = pc['piece'].replace('fence_wattle_', 'fence_picket_')
                swapped += 1
        self.assertGreater(swapped, 3)
        msgs = [f['message'] for f in self.EN.check_zone(q, self.lib)]
        self.assertTrue(any('holds sheep' in m and 'picket fence' in m for m in msgs), msgs)
        self.assertFalse(any('holds sheep' in m and 'picket fence' in m for m in
                             (f['message'] for f in self.EN.check_zone(self.plan, self.lib))))

    def test_kit_zones_have_no_enclosure_faults(self):
        zdir = os.path.join(S.ROOT, 'game', 'kit', 'zones')
        for f in sorted(os.listdir(zdir)):
            plan = json.load(open(os.path.join(zdir, f)))
            self.assertEqual(self.EN.check_zone(plan, self.lib), [], f)

    def test_the_loops_scenes_play_the_strip_over_or_instead_of_the_still(self):
        idx = json.load(open(os.path.join(S.ROOT, 'game', 'kit', 'props', 'index.json')))
        for pid, node in (('farm_hen_white', 'Idle'), ('farm_sheep_graze', 'Idle'), ('farm_cow', 'Idle'), ('farm_pig', 'Idle'),
                          ('waterfall_3_tall', 'Flow'), ('waterfall_1', 'Flow')):
            self.assertIn('anim', idx[pid], pid)
            with open(os.path.join(S.ROOT, 'game', 'kit', 'props', pid + '.tscn')) as f:
                text = f.read()
            self.assertIn('[node name="%s" type="Sprite2D" parent="."]' % node, text)
            self.assertIn('res://world/loop_fx.gd', text)
            self.assertIn('hframes = 8', text)
            self.assertEqual(idx[pid]['anim']['reduced_motion'], 'hold:0')

    def test_a_falls_first_frame_is_the_still_the_bake_draws(self):
        from scripts.art.kit import structures as ST
        from scripts.art.native.palette import C
        for c, drop in ((3, 2), (1, 1)):
            strip, (x0, y0, w, h) = ST.fall_frames(c, drop)
            wpx, face = c * 24, 48 * drop
            base = np.full((12 + face + 34, wpx + 48), C('water', 2), np.int32)
            ST.fall_sheet(base, 24, wpx, 12, 12 + face, seed=9 + c, rings=False)
            f0 = strip[:, :w]
            m = f0 >= 0
            np.testing.assert_array_equal(f0[m], base[y0:y0 + h, x0:x0 + w][m])
            self.assertEqual(strip.shape[1], w * ST.FALL_FRAMES)
            # every frame covers the same pixels (the loop never uncovers the baked pool)
            for k in range(1, ST.FALL_FRAMES):
                np.testing.assert_array_equal(strip[:, k * w:(k + 1) * w] >= 0, m)



class VillageCommons(unittest.TestCase):
    """The commons carry where they belong (needs, faces, avoid, points), the audit catches each
    one put in the wrong place, and the village-green study built from kit pieces passes every
    check (scripts/art/kit/commons.py, placement_audit.check_plan, village_study.py; 3 Nov)."""

    @classmethod
    def setUpClass(cls):
        from scripts.art.kit import placement_audit as PA
        from scripts.art.kit import village_study as VS
        cls.PA, cls.VS = PA, VS
        cls.plan = VS.plan()

    def _msgs(self, plan):
        return [f['message'] for f in self.PA.check_plan(plan)]

    def _moved(self, pid, at, **kw):
        import copy
        q = copy.deepcopy(self.plan)
        for pc in q['pieces']:
            if pc['id'] == pid:
                pc['at'] = list(at)
                pc.update(kw)
        return q

    def test_pictures_are_what_the_painter_draws(self):
        from scripts.art.kit import commons
        self.assertEqual(commons.check(), 0)

    def test_the_village_study_passes_every_check(self):
        from scripts.art.kit import enclosures as EN
        from scripts.art.kit import relations as RL
        from scripts.review import kit_rules as KR
        self.assertEqual([f for f in KR.check_zone(self.plan) if f['severity'] == 'fault'], [])
        self.assertEqual(RL.check_zone(self.plan), [])
        self.assertEqual(EN.check_zone(self.plan), [])
        self.assertEqual(self.PA.check_plan(self.plan), [])
        self.assertEqual(self.VS.layout_faults(self.plan), [])

    def test_washing_hangs_in_a_back_yard_not_before_the_door(self):
        # south of the cottage (before its door) it is within reach of the home but not its yard
        self.assertTrue(any(m.startswith('washing: needs a home') and 'yard' in m for m in self._msgs(self._moved('washing', (396, 312)))))
        self.assertTrue(any(m.startswith('washing: needs a home') for m in self._msgs(self._moved('washing', (396, 672)))))

    def test_firewood_needs_a_hearth(self):
        self.assertTrue(any(m.startswith('woodpile: needs a hearth') for m in self._msgs(self._moved('woodpile', (300, 672)))))
        self.assertTrue(any(m.startswith('block: needs a hearth') for m in self._msgs(self._moved('block', (300, 672)))))

    def test_a_bench_faces_something(self):
        self.assertTrue(any(m.startswith('bench: faces n') for m in self._msgs(self._moved('bench', (708, 432), facing='n'))))

    def test_a_fingerpost_points_along_its_junction(self):
        import copy
        q = copy.deepcopy(self.plan)
        for pc in q['pieces']:
            if pc['id'] == 'fingerpost':
                pc['piece'] = 'commons_fingerpost_esw'
        self.assertTrue(any('its arms point esw but the routes leave the junction nesw' in m for m in self._msgs(q)))
        self.assertTrue(any(m.startswith('fingerpost: a signpost stands at no junction') for m in self._msgs(self._moved('fingerpost', (204, 720)))))

    def test_lamps_and_lines_stay_out_of_wild_woods(self):
        import copy
        q = copy.deepcopy(self.plan)
        q['pieces'] = [pc for pc in q['pieces'] if pc['id'] not in ('cottage', 'herbalist', 'hut')]
        for k, (x, y) in enumerate(((300, 600), (372, 600), (300, 672), (372, 672))):
            q['pieces'].append({'id': 'tree_%d' % k, 'piece': 'woodland_oak', 'at': [x, y]})
        for pc in q['pieces']:
            if pc['id'] == 'lantern':
                pc['at'] = [348, 648]
        self.assertTrue(any(m.startswith('lantern: stands in wild woods') for m in self._msgs(q)))

    def test_existing_pieces_provide_what_the_logic_reads(self):
        lib = self.PA._files()
        for pid, tags in (('crossroads_fern_cottage', {'home', 'hearth'}), ('crossroads_smithy', {'hearth'}),
                          ('crossroads_well', {'feature', 'water'}), ('commons_pump', {'feature', 'water'})):
            self.assertTrue(tags <= set(json.load(open(lib[pid]))['placement'].get('provides', [])), pid)



class Thresholds(unittest.TestCase):
    """Doors, door paths, gates on paths and where fences meet buildings (thresholds.py; Matt's
    review of the farm study, 4 Nov): each rule catches its fault, and the fixed layout (the farm
    and village studies) passes."""

    @classmethod
    def setUpClass(cls):
        from scripts.art.kit import build as _B  # noqa: F401
        from scripts.art.kit import farm_study as FS
        from scripts.art.kit import thresholds as TH
        from scripts.art.kit import village_study as VS
        cls.FS, cls.TH, cls.VS = FS, TH, VS
        cls.plan = FS.plan()

    def _q(self, cells=(), pieces=None, drop=()):
        """The farm study with ground cells set ((col, row, letter), ...), pieces replaced by id and
        some removed."""
        import copy
        q = copy.deepcopy(self.plan)
        rows = [list(r) for r in q['rows']]
        for c, r, ch in cells:
            rows[r][c] = ch
        q['rows'] = [''.join(r) for r in rows]
        by = {pc['id']: pc for pc in (pieces or [])}
        q['pieces'] = [by.pop(pc['id'], pc) for pc in q['pieces'] if pc['id'] not in drop] + list(by.values())
        return q

    def _faults(self, q, check):
        return [f['message'] for f in self.TH.check_plan(q) if f['check'] == check]

    def test_the_studies_pass(self):
        self.assertEqual(self.TH.check_plan(self.plan), [])
        self.assertEqual(self.TH.check_plan(self.VS.plan()), [])

    def test_houses_carry_their_doors(self):
        from scripts.art.kit import enclosures as EN
        lib = EN.library()
        for pid in ('crossroads_hut', 'crossroads_bakery', 'crossroads_herbalist', 'crossroads_library', 'crossroads_north_cottages',
                    'crossroads_smithy', 'crossroads_fern_cottage'):
            ds = lib[pid]['geometry']['doors']
            self.assertTrue(ds and all(d['x'][0] < d['x'][1] for d in ds), pid)
            # a foot on the 4 world px grid (12 texels): every door's centre on the half-cell grid
            for d in ds:
                self.assertTrue(self.TH.on_half_grid(708 + (d['x'][0] + d['x'][1]) / 2.0), pid)

    def test_every_house_door_is_drawn_on_the_half_cell_grid(self):
        # the rule is in the drawing (houses.doors_on_grid in houses.building; Matt, 4 Nov: redesign the
        # doors, keep the houses): every look in every zone plan, its doors and a forge's mouth a whole
        # number of half cells (4 world px) from the front's middle, each moved at most 2 world px
        import glob
        from scripts.art.native import houses as HS
        seen = 0
        for f in sorted(glob.glob(os.path.join(S.ROOT, 'game', 'data', 'plans', '*.json'))):
            with open(f) as fh:
                p = json.load(fh)
            looks = (p.get('art') or {}).get('looks') or {}
            for b in p.get('buildings', []):
                if b['id'] not in looks:
                    continue
                look = dict(looks[b['id']], w=b['rect'][2], depth=b['rect'][3])
                s = HS.doors_on_grid(look)
                was = [look['door']] if isinstance(look.get('door'), (int, float)) else [d[0] for d in look.get('doors', [])]
                now = [s['door']] if isinstance(s.get('door'), (int, float)) else [d[0] for d in s.get('doors', [])]
                for a, b_ in zip(was, now):
                    seen += 1
                    self.assertEqual((b_ - look['w'] / 2.0) % 4, 0, b['id'])
                    self.assertLessEqual(abs(b_ - a), 2, b['id'])
        self.assertGreaterEqual(seen, 8)
        # and the drawing puts them there: the two that moved, built (centres in texels from the foot)
        from scripts.art.native import village as V
        with open(os.path.join(S.ROOT, 'game', 'data', 'plans', 'crossroads.json')) as fh:
            p = json.load(fh)
        rects = {b['id']: b['rect'] for b in p['buildings']}
        for bid in ('fern_cottage', 'smithy'):
            look = dict(p['art']['looks'][bid], w=rects[bid][2], depth=rects[bid][3])
            built = V.building(look, seed=look.get('seed', sum(map(ord, bid))), hd=True)
            self.assertTrue(built.info['doors'] and all(c % 12 == 0 for c in built.info['doors']), (bid, built.info['doors']))

    def test_a_door_path_is_centred_and_runs_straight_out(self):
        # one cell east of the door's centre line (the farm study's cottage path is columns 26 and 27)
        shifted = [(26, r, '.') for r in range(12, 19)] + [(28, r, '#') for r in range(12, 19)]
        self.assertTrue(any('the path from its door is centred at x=672' in m for m in self._faults(self._q(shifted), 'rules.door_path')))
        # centred at the door, but bending east in the first cell out
        bent = [(c, 13, '.') for c in (26, 27)] + [(28, 13, '#'), (29, 13, '#')]
        self.assertTrue(any('bends before it is a cell out' in m for m in self._faults(self._q(bent), 'rules.door_path')))
        # a door drawn off the half-cell grid (the fern cottage's before 4 Nov, 6 texels west) is told so
        import copy
        from scripts.art.kit import relations as RL
        lib = copy.deepcopy(RL.default_library())
        lib['crossroads_fern_cottage']['geometry']['doors'][0]['x'] = [v - 6 for v in lib['crossroads_fern_cottage']['geometry']['doors'][0]['x']]
        self.assertTrue(any('off the half-cell grid' in f['message'] for f in self.TH.check_plan(self.plan, lib)))

    def test_a_door_stays_clear(self):
        tub = {'id': 'tub', 'piece': 'crossroads_flower_tub', 'at': [648, 312]}
        self.assertTrue(any(m.startswith('tub stands in the doorway of cottage') for m in self._faults(self._q(pieces=[tub]), 'rules.door_clear')))
        bed = {'id': 'border_1', 'piece': 'garden_flower_border', 'at': [648, 312]}
        self.assertTrue(any(m.startswith('border_1 stands in the doorway') for m in self._faults(self._q(pieces=[bed]), 'rules.door_clear')))
        # beside the door (the study's borders) is clear
        self.assertEqual(self._faults(self.plan, 'rules.door_clear'), [])

    def test_a_gate_is_centred_on_its_path_and_paths_cross_only_at_gates(self):
        # the way to the chicken run one cell wide (column 5): its centre is half a cell off the gate's
        one = [(4, r, '.') for r in range(12, 19)]
        self.assertTrue(any(m.startswith('run_gate: the gate is centred at x=120, the path through it at x=132')
                            for m in self._faults(self._q(one), 'rules.gate_path')))
        # four cells wide: it runs through the fence beside the gate
        four = [(c, r, '#') for c in (6, 7) for r in range(12, 19)]
        self.assertTrue(any(m.startswith('run_7_12: a path runs through the fence') for m in self._faults(self._q(four), 'rules.path_through_fence')))
        # a path across the fold's west hurdles with no gate
        across = [(c, 6, '#') for c in range(6, 13)]
        self.assertTrue(any(m.startswith('fold_10_5: a path runs through the fence') or m.startswith('fold_10_6: a path runs through the fence')
                            for m in self._faults(self._q(across), 'rules.path_through_fence')))
        # a stile in a north-south run with a one-cell path across it: the run's cells centre on row lines
        stile = {'id': 'paddock_50_7', 'piece': 'fence_rail_stile_ns', 'at': [1212, 192], 'variant': 'plain'}
        path = [(c, 7, '#') for c in range(49, 53)]
        self.assertTrue(any('an even number of cells wide' in m for m in self._faults(self._q(path, [stile]), 'rules.gate_path')))

    def test_a_fence_meets_a_building_at_its_corners(self):
        # the v6 garden: its east side run three cells inside the cottage's east corner, before the façade
        inner = [dict(pc, id=pc['id'].replace('garden_34', 'garden_31'), at=[31 * 24, pc['at'][1]])
                 for pc in self.plan['pieces'] if pc['id'].startswith('garden_34_')]
        q = self._q(pieces=inner, drop=[pc['id'] for pc in self.plan['pieces'] if pc['id'].startswith('garden_34_')])
        self.assertTrue(any(m.startswith('garden_31_11: drawn in front of the façade of cottage') for m in self._faults(q, 'rules.fence_wall')))
        # its west side run a cell short of the west wall: a gap
        short = [dict(pc, id=pc['id'].replace('garden_25', 'garden_24'), at=[24 * 24, pc['at'][1]])
                 for pc in self.plan['pieces'] if pc['id'].startswith('garden_25_')]
        q = self._q(pieces=short, drop=[pc['id'] for pc in self.plan['pieces'] if pc['id'].startswith('garden_25_')])
        self.assertTrue(any(m.startswith('garden_24_11: its end post stands 24 texels off the wall') for m in self._faults(q, 'rules.fence_wall')))
        # at the corners (the study) they pass
        self.assertEqual(self._faults(self.plan, 'rules.fence_wall'), [])


class ToneAndNoise(unittest.TestCase):
    """No tone target met with speckle (Claude A's review of the v4 images): every farm and commons
    picture keeps isolated pixels at 4 % or less, and the animals and the commons keep their runs of
    3 pixels or fewer at 15 % or less (scripts/art/kit/tone_audit.py). Hens, 10 world px long,
    are drawn in 1 to 3 pixel features (an eye, a comb, a beak) and are not held to the speck share."""

    def test_no_picture_is_speckled(self):
        from scripts.art.kit import tone_audit as TA
        for p in TA.pictures():
            r = TA.measure(p)
            name = os.path.basename(p)
            self.assertLessEqual(r['isolated'], TA.ISOLATED_MAX, name)
            if ('commons' in p or name.startswith(('farm_cow', 'farm_calf', 'farm_horse', 'farm_pig', 'farm_goat', 'farm_sheep'))):
                self.assertLessEqual(r['specks'], TA.SPECKS_MAX, name)


if __name__ == '__main__':
    unittest.main()

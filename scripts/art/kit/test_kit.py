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
            r = p['geometry']['collision']['rect']
            actual = [r[0] + obj['foot'][0] / 3, r[1] + obj['foot'][1] / 3, *r[2:]]
            np.testing.assert_allclose(actual, obj['solid'], atol=0.00001, err_msg=obj['id'])

    def test_per_variant_anchors_match_source_offsets(self):
        kit = self.seed._read('game/zones/crossroads/kit.json')
        for obj in kit['objects']:
            if not obj.get('png') or obj['kind'] in ('shadow', 'damage', 'glow', 'smoke'):
                continue
            p = self.by_id[self.index['crossroads', obj['id']]]
            v = next(v for v in p['variants'] if v['id'] == os.path.splitext(obj['png'])[0])
            self.assertEqual(v['foot'], [-n for n in obj['offset']], obj['id'])

    def test_unknown_woodland_collision_is_not_fabricated(self):
        for p in self.pieces:
            if p['id'].startswith('woodland_') and p['id'] != 'woodland_stone_sign':
                self.assertIsNone(p['geometry']['collision'])
                self.assertNotIn('blocks_move', p['gameplay'])
                self.assertTrue(any('unknown' in t for t in p['audit']['todo']))

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


if __name__ == '__main__':
    unittest.main()

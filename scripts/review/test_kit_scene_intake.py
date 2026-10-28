"""Read-only scene intake regressions; no kit artwork, approvals or painters are changed.

    python3 -m unittest scripts.review.test_kit_scene_intake
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

from scripts.review import scene as SN
from scripts.review import run


ROOT = Path(SN.REPO)
KIT_ZONES = ('kitlab', 'kitlab_tiers', 'kitlab_widths', 'woodland_kit')


def packed(cells):
    data = b'\0\0' + b''.join(struct.pack('<hhHHHH', x, y, 0, ax, 0, 0) for x, y, ax in cells)
    return 'PackedByteArray("' + base64.b64encode(data).decode() + '")'


class RealSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.zones = {name: SN.load_zone(name) for name in KIT_ZONES}

    def test_all_four_registered_zones_have_real_grid_extents_and_baked_pixels(self):
        registered = json.loads((ROOT / 'game/data/zones.json').read_text())
        for name, z in self.zones.items():
            with self.subTest(zone=name):
                self.assertIn(name, registered)
                plan = json.loads((ROOT / f'game/kit/zones/{name}.json').read_text())
                self.assertEqual(z.size, (24 * len(plan['rows'][0]), 24 * len(plan['rows'])))
                baked = np.asarray(Image.open(ROOT / f'game/zones/{name}/ground_baked.png').convert('RGBA'))
                np.testing.assert_array_equal(z.ground, baked)
                composite = SN.composite(z)
                self.assertEqual(composite.shape, (z.size[1], z.size[0], 4))
                self.assertGreater(np.unique(composite[..., :3].reshape(-1, 3), axis=0).shape[0], 20)

    def test_freshness_digest_matches_authoritative_bake_function_for_all_zones(self):
        from scripts.art.kit import bake
        lib = bake._pieces_lib()
        for name in KIT_ZONES:
            plan = json.loads((ROOT / f'game/kit/zones/{name}.json').read_text())
            self.assertEqual(SN._bake_hash(plan, lib), bake.input_hash(plan, lib))

    def test_actual_rock_variant_and_runtime_foot_override(self):
        z = self.zones['kitlab']
        sp = next(s for s in z.sprites if s.parent == 'Props/rock-1/Sprite')
        entry = json.loads((ROOT / 'game/kit/props/index.json').read_text())['woodland_boulder']['variants']['b4']
        expected = np.asarray(Image.open(SN.res_path(entry['png'])).convert('RGBA'))
        np.testing.assert_array_equal(sp.rgba, expected)
        self.assertEqual(sp.origin, (860, 96))
        self.assertEqual(sp.box[:2], tuple(np.floor(np.array([860, 96]) - entry['foot'] + 0.5).astype(int)))
        self.assertTrue(sp.ysort)

    def test_actual_painted_structures_are_hidden_not_pasted_twice(self):
        expected = {'kitlab_tiers': 2, 'kitlab_widths': 2, 'woodland_kit': 2}
        for name, count in expected.items():
            z = self.zones[name]
            hidden = [s for s in z.sprites if not s.visible and s.parent.startswith('Props/')]
            self.assertEqual(len(hidden), count, name)
            before = SN.composite(z)
            original = z.sprites
            try:
                z.sprites = [s for s in original if s.visible]
                np.testing.assert_array_equal(SN.composite(z), before)
                z.sprites = [s for s in original if s.visible or s is hidden[0]]
                hidden[0].visible = True
                self.assertTrue(np.any(SN.composite(z) != before), name)
            finally:
                hidden[0].visible = False
                z.sprites = original

    def test_legacy_woodland_and_crossroads_are_byte_unchanged(self):
        expected = {
            'woodland': 'df4bade2c300319709c35a1b491ed3922e61502761312e10b045d3c68ca07934',
            'crossroads': 'f90ca3ebcdd13319346922b5bd83fe03311c110437d69b604800332230a5bdbd',
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256(SN.composite(SN.load_zone(name)).tobytes()).hexdigest(), digest)


class IntakeFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / 'game'
        self.patch = mock.patch.object(SN, 'GAME', str(self.game))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        for path in ('data', 'world/terrain', 'kit/terrain', 'kit/zones', 'kit/props', 'kit/pieces/material', 'zones/example'):
            (self.game / path).mkdir(parents=True, exist_ok=True)
        (self.root / 'scripts/art/kit').mkdir(parents=True)
        for name in ('bake.py', 'surface.py', 'structures.py'):
            shutil.copyfile(ROOT / 'scripts/art/kit' / name, self.root / 'scripts/art/kit' / name)
        (self.game / 'world/terrain/terrain_ground.gd').write_text('@export var grid_size := Vector2i(3, 2)\n')
        self.write('data/zones.json', {'example': 'res://zones/example/example.tscn'})
        self.write('kit/terrain/manifest.json', {'cell': 24, 'materials': [{'id': 'lawn'}, {'id': 'path'}]})
        self.lib = {'lawn': {'id': 'lawn'}, 'earth_face': {'id': 'earth_face'}, 'test_piece': {'id': 'test_piece'}}
        for name, data in self.lib.items():
            self.write('kit/pieces/material/' + name + '.json', data)
        self.index = {'test_piece': {'painted': False, 'variants': {
            'small': {'png': 'res://kit/props/small.png', 'foot': [1, 2]},
            'large': {'png': 'res://kit/props/large.png', 'foot': [2, 4]},
        }}}
        self.write('kit/props/index.json', self.index)
        a = np.zeros((2, 2, 4), np.uint8)
        a[:] = (220, 30, 40, 255)
        a[0, 0] = (10, 210, 40, 255)
        Image.fromarray(a).save(self.game / 'kit/props/small.png')
        Image.fromarray(np.repeat(np.repeat(a, 2, 0), 2, 1)).save(self.game / 'kit/props/large.png')
        Image.new('RGB', (72, 48), (10, 20, 30)).save(self.game / 'zones/example/ground_baked.png')
        (self.game / 'kit/props/test_piece.tscn').write_text('''[gd_scene format=3]
[ext_resource type="Script" path="res://world/terrain/kit_piece.gd" id="script"]
[ext_resource type="Texture2D" path="res://kit/props/small.png" id="art"]
[node name="TestPiece" type="Node2D"]
script = ExtResource("script")
piece_id = "test_piece"
[node name="Sprite" type="Sprite2D" parent="."]
texture = ExtResource("art")
centered = false
offset = Vector2(-1, -2)
''')
        self.plan = {'zone': 'example', 'bake': True, 'legend': {'.': 'lawn'}, 'rows': ['...', '...'],
                     'pieces': [{'id': 'rock', 'piece': 'test_piece', 'at': [24, 24], 'variant': 'large'}],
                     'spawns': {'start': [36, 24]}}
        self.text = '''[gd_scene format=4]
[ext_resource type="Script" path="res://world/terrain/terrain_ground.gd" id="ground"]
[ext_resource type="Texture2D" path="res://zones/example/ground_baked.png" id="bake"]
[ext_resource type="PackedScene" path="res://kit/props/test_piece.tscn" id="piece"]
[node name="Example" type="Node2D"]
y_sort_enabled = true
[node name="Ground" type="Node2D" parent="."]
z_index = -10
script = ExtResource("ground")
grid_size = Vector2i(3, 2)
baked = ExtResource("bake")
[node name="Cells" type="TileMapLayer" parent="Ground"]
tile_map_data = CELL_DATA
[node name="Props" type="Node2D" parent="."]
y_sort_enabled = true
[node name="rock" parent="Props" instance=ExtResource("piece")]
position = Vector2(24, 24)
variant = "large"
[node name="Spawns" type="Node2D" parent="."]
[node name="start" type="Marker2D" parent="Spawns"]
position = Vector2(36, 24)
'''.replace('CELL_DATA', packed([(x, y, 0) for y in range(2) for x in range(3)]))
        self.flush()

    def write(self, path, data):
        (self.game / path).write_text(json.dumps(data) + '\n')

    def flush(self, stamp=True):
        (self.game / 'zones/example/example.tscn').write_text(self.text)
        self.write('kit/zones/example.json', self.plan)
        if stamp:
            self.write('zones/example/ground_baked.json', {'zone': 'example', 'hash': SN._bake_hash(self.plan, self.lib)})

    def fails(self, fragment):
        with self.assertRaisesRegex(SN.SceneIntakeError, fragment):
            SN.load_zone('example')

    def test_vector2i_default_and_nonempty_extent(self):
        self.assertEqual(SN._val('Vector2i(-2, 3)'), (-2, 3))
        self.assertEqual(SN.load_zone('example').size, (72, 48))
        self.text = self.text.replace('grid_size = Vector2i(3, 2)\n', '')
        self.flush()
        self.assertEqual(SN.load_zone('example').size, (72, 48))

    def test_missing_texture_stamp_and_unbaked_fail_closed(self):
        for name in ('ground_baked.png', 'ground_baked.json'):
            with self.subTest(missing=name):
                path = self.game / 'zones/example' / name
                content = path.read_bytes()
                path.unlink()
                self.fails(name)
                path.write_bytes(content)
        self.text = self.text.replace('baked = ExtResource("bake")\n', '')
        self.flush()
        self.fails('unbaked TerrainGround')

    def test_stale_stamp_or_changed_bake_source_is_rejected(self):
        self.write('zones/example/ground_baked.json', {'zone': 'example', 'hash': 'old'})
        self.fails('stale baked-ground input hash')
        self.flush()
        with (self.root / 'scripts/art/kit/surface.py').open('a') as f:
            f.write('\n# changed producer\n')
        self.fails('stale baked-ground input hash')

    def test_baked_texture_extent_must_match_grid(self):
        Image.new('RGB', (72, 24)).save(self.game / 'zones/example/ground_baked.png')
        self.fails('texture extent')

    def test_material_change_without_export_cannot_reuse_old_plan_stamp(self):
        self.text = self.text.replace(packed([(x, y, 0) for y in range(2) for x in range(3)]),
                                      packed([(x, y, 1 if (x, y) == (1, 1) else 0) for y in range(2) for x in range(3)]))
        self.flush()
        self.fails('scene/plan material differs at 1,1')

    def test_missing_logical_cells_or_unknown_packed_format_is_rejected(self):
        old = packed([(x, y, 0) for y in range(2) for x in range(3)])
        for data in ('PackedByteArray()', 'PackedByteArray("AQ==")'):
            with self.subTest(data=data):
                original = self.text
                self.text = original.replace(old, data)
                self.flush()
                self.fails('material differs|packed format')
                self.text = original

    def test_tiers_surface_variants_and_spawn_changes_are_stale(self):
        original = self.text
        alterations = [
            ('[node name="Props"', '[node name="Tiers" type="TileMapLayer" parent="Ground"]\ntile_map_data = ' + packed([(1, 1, 1)]) + '\n[node name="Props"', 'tiers differ'),
            ('grid_size = Vector2i(3, 2)', 'grid_size = Vector2i(3, 2)\nvariant_rows = PackedStringArray("a..", "...")', 'surface variants differ'),
            ('position = Vector2(36, 24)', 'position = Vector2(48, 24)', 'spawn differs'),
        ]
        for before, after, error in alterations:
            with self.subTest(error=error):
                self.text = original.replace(before, after)
                self.flush()
                self.fails(error)

    def test_piece_move_variant_and_inventory_changes_are_stale(self):
        original = self.text
        for before, after, error in [
            ('position = Vector2(24, 24)', 'position = Vector2(48, 24)', 'piece transform differs'),
            ('variant = "large"', 'variant = "small"', 'piece variant differs'),
            ('[node name="rock"', '[node name="renamed"', 'piece identity differs'),
        ]:
            with self.subTest(error=error):
                self.text = original.replace(before, after)
                self.flush()
                self.fails(error)

    def test_selected_variant_and_foot_replace_instanced_sprite_defaults(self):
        sp = SN.load_zone('example').sprites[0]
        self.assertEqual(sp.rgba.shape, (4, 4, 4))
        self.assertEqual(sp.origin, (24, 24))
        self.assertEqual(sp.box, (22, 20, 26, 24))
        self.assertTrue(sp.path.endswith('large.png'))
        self.assertTrue(sp.ysort)

    def test_inherited_scene_and_descendant_sprite_override_preserve_resource_tables(self):
        path = self.game / 'kit/props/test_piece.tscn'
        (self.game / 'kit/props/base.tscn').write_text(path.read_text())
        path.write_text('''[gd_scene format=3]
[ext_resource type="PackedScene" path="res://kit/props/base.tscn" id="base"]
[node name="TestPiece" instance=ExtResource("base")]
[node name="Sprite" parent="."]
flip_h = true
''')
        sp = SN.load_zone('example').sprites[0]
        self.assertEqual(sp.box, (22, 20, 26, 24))
        with Image.open(self.game / 'kit/props/large.png') as img:
            expected = np.asarray(img.convert('RGBA'))[:, ::-1]
        np.testing.assert_array_equal(sp.rgba, expected)

    def test_unknown_variant_or_missing_index_never_falls_back(self):
        self.plan['pieces'][0]['variant'] = 'unknown'
        self.text = self.text.replace('variant = "large"', 'variant = "unknown"')
        self.flush()
        self.fails('unknown KitPiece variant')
        self.write('kit/props/index.json', {})
        self.fails('piece missing from KitPiece index')

    def test_parent_transform_and_index_foot_are_applied_in_source_geometry(self):
        self.text = self.text.replace('y_sort_enabled = true\n[node name="rock"',
                                      'y_sort_enabled = true\nposition = Vector2(5, 7)\nscale = Vector2(-2, 3)\n[node name="rock"')
        self.flush()
        nodes = SN._kit_nodes(SN.parse_tscn(str(self.game / 'zones/example/example.tscn')))
        piece = next(e for e in nodes if e['key'] == 'Props/rock')
        entry = next(e for e in nodes if e['key'] == 'Props/rock/Sprite')
        sp = SN._kit_sprite(entry, self.index, {'Props/rock': piece})
        self.assertEqual(sp.origin, (-43, 79))
        self.assertEqual(sp.box, (-47, 67, -39, 79))
        expected = np.asarray(Image.open(self.game / 'kit/props/large.png'))[:, ::-1]
        expected = np.repeat(np.repeat(expected, 3, 0), 2, 1)
        np.testing.assert_array_equal(sp.rgba, expected)
        # A transform omitted from the bake plan cannot silently reuse its old shadows.
        self.fails('piece transform differs')

    def test_quarter_turn_supported_but_skew_and_fractional_rotation_fail_closed(self):
        self.text = self.text.replace('position = Vector2(24, 24)', 'position = Vector2(24, 24)\nrotation_degrees = 90')
        self.flush()
        nodes = SN._kit_nodes(SN.parse_tscn(str(self.game / 'zones/example/example.tscn')))
        piece = next(e for e in nodes if e['key'] == 'Props/rock')
        entry = next(e for e in nodes if e['key'] == 'Props/rock/Sprite')
        sp = SN._kit_sprite(entry, self.index, {'Props/rock': piece})
        self.assertEqual(sp.box, (24, 22, 28, 26))
        np.testing.assert_array_equal(sp.rgba, np.rot90(np.asarray(Image.open(self.game / 'kit/props/large.png')), -1))
        self.text = self.text.replace('rotation_degrees = 90', 'rotation_degrees = 30')
        self.flush()
        self.fails('piece transform differs')
        self.text = self.text.replace('rotation_degrees = 30', 'skew = 0.1')
        self.flush()
        self.fails('unsupported explicit transform')

    def test_painted_visibility_is_runtime_index_driven(self):
        self.index['test_piece']['painted'] = True
        self.write('kit/props/index.json', self.index)
        z = SN.load_zone('example')
        self.assertFalse(z.sprites[0].visible)
        np.testing.assert_array_equal(SN.composite(z), z.ground)

    def test_ancestor_modulation_and_unsupported_ground_layer_fail_closed(self):
        original = self.text
        for before, after, reason in [
            ('[node name="Example" type="Node2D"]',
             '[node name="Example" type="Node2D"]\nmodulate = Color(1, 0, 0, 1)', 'inherited material or modulation'),
            ('[node name="Props" type="Node2D" parent="."]',
             '[node name="Props" type="Node2D" parent="."]\nself_modulate = Color(1, 0, 0, 1)', 'inherited material or modulation'),
            ('z_index = -10', 'z_index = 100', 'TerrainGround draw order'),
            ('position = Vector2(24, 24)', 'position = Vector2(24, 24)\nz_index = -20', 'TerrainGround draw order'),
        ]:
            with self.subTest(reason=reason):
                self.text = original.replace(before, after)
                self.flush()
                self.fails(reason)

    def test_nonopaque_bake_is_not_silently_composited_as_opaque(self):
        Image.new('RGBA', (72, 48), (10, 20, 30, 100)).save(self.game / 'zones/example/ground_baked.png')
        self.fails('opaque RGB')

    def test_missing_scene_instance_and_invalid_registry_are_intake_errors(self):
        (self.game / 'kit/props/test_piece.tscn').unlink()
        self.fails('test_piece.tscn')
        (self.game / 'data/zones.json').write_text('{invalid')
        self.fails('incomplete scene intake')

    def test_equal_y_kit_overlap_retains_scene_order_without_changing_legacy_tie(self):
        # The right-hand piece is authored first, then the left-hand one. X sorting
        # would reverse the intended last draw at their shared overlap pixel.
        ground = np.zeros((8, 8, 4), np.uint8)
        red = np.full((3, 3, 4), (255, 0, 0, 255), np.uint8)
        green = np.full((3, 3, 4), (0, 255, 0, 255), np.uint8)
        right = SN.Sprite('right', 'right', (4, 6), (3, 3, 6, 6), 0, True, red, 'Props/right', draw_order=0)
        left = SN.Sprite('left', 'left', (3, 6), (2, 3, 5, 6), 0, True, green, 'Props/left', draw_order=1)
        z = SN.Zone('ties', (8, 8), ground, [right, left])
        np.testing.assert_array_equal(SN.composite(z)[4, 4, :3], (0, 255, 0))
        right.draw_order = left.draw_order = None
        np.testing.assert_array_equal(SN.composite(z)[4, 4, :3], (255, 0, 0))

    def test_unsupported_ground_and_empty_composite_fail_closed(self):
        self.text = self.text.replace('terrain_ground.gd', 'another_ground.gd')
        self.flush()
        self.fails('no supported ground')
        with self.assertRaisesRegex(SN.SceneIntakeError, 'invalid composite extent'):
            SN.composite(SN.Zone('empty', (0, 0), None))

    def test_runner_writes_incomplete_report_and_exit_one_before_any_picture(self):
        out = self.root / 'report'
        err = SN.SceneIntakeError('kitlab', 'stale baked-ground input hash')
        with mock.patch.object(SN, 'load_zone', side_effect=err), contextlib.redirect_stderr(io.StringIO()):
            code = run.main(['kitlab', '--no-render', '--out', str(out)])
        report = json.loads((out / 'report.json').read_text())
        self.assertEqual(code, 1)
        self.assertFalse(report['complete'])
        self.assertFalse(report['scene']['complete'])
        self.assertIn('stale baked-ground', report['scene']['error'])
        self.assertEqual(report['pictures'], [])
        self.assertEqual(list(out.glob('*.png')), [])

    def test_runner_registry_failure_writes_incomplete_report(self):
        out = self.root / 'bad-registry-report'
        for content in ('{invalid', '[]'):
            with self.subTest(registry=content):
                with mock.patch.object(run, 'REPO', str(self.root)), contextlib.redirect_stderr(io.StringIO()):
                    (self.game / 'data/zones.json').write_text(content)
                    code = run.main(['example', '--no-render', '--out', str(out)])
                report = json.loads((out / 'report.json').read_text())
                self.assertEqual(code, 1)
                self.assertFalse(report['complete'])
                self.assertIn('cannot read zone registry', report['scene']['error'])
                self.assertEqual(report['pictures'], [])


if __name__ == '__main__':
    unittest.main()

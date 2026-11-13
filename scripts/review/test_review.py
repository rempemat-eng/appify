"""Regression tests for the review detectors, on small synthetic pictures (no screenshots).

    python3 -m unittest scripts.review.test_review        (npm run check:review)

Each detector gets a picture that must trip it and one that must not, so a threshold change
that loses a calibration fault, or starts flagging clean art, fails here first.
"""
from __future__ import annotations

import datetime
import json
import hashlib
import os
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

from scripts.review import core, water, screen, construct as C, detail as D, scene as SN, gate, assets as A
from scripts.review import edges as E
from scripts.review import scale as SZ
from scripts.review import run as R
from scipy import ndimage as ndi

H = 74
GRASS = (150, 166, 92)
GRASS2 = (140, 160, 96)
BLUE = (60, 100, 170)
OUT = (30, 25, 23)


def lawn(w=400, h=300):
    rng = np.random.default_rng(1)
    a = np.zeros((h, w, 4), np.uint8)
    a[..., :3] = GRASS
    a[rng.random((h, w)) < 0.3, :3] = GRASS2
    a[..., 3] = 255
    return a


class Scale(unittest.TestCase):
    def test_fractional_upscale_is_recovered(self):
        rng = np.random.default_rng(0)
        art = (rng.integers(0, 6, (60, 90))[..., None] * 40).repeat(3, -1).astype(np.uint8)
        big = Image.fromarray(art).resize((round(90 * 3.14), round(60 * 3.14)), Image.NEAREST)
        s, px, py = core.estimate_scale(np.asarray(big))
        self.assertAlmostEqual(s, 3.14, delta=0.05)
        nat, s2, _ = core.to_native(big)
        self.assertLess(abs(nat.shape[1] - 90), 3)

    def test_native_art_stays_native(self):
        rng = np.random.default_rng(0)
        art = (rng.integers(0, 255, (80, 120, 3))).astype(np.uint8)
        self.assertEqual(core.estimate_scale(art)[0], 1.0)


class Occlusion(unittest.TestCase):
    def test_a_ground_layer_piece_is_not_sorted_against_people(self):
        # (woodland review, round 7) a sprite whose y-sort point is far from its drawn feet is a
        # fault, unless it lies on a layer under the people (z_index below 0: a fall's loop, a bridge)
        a = np.zeros((60, 20, 4), np.uint8)
        a[:, :, 3] = 255
        from scripts.review import scene as SC
        z = SC.Zone('t', (100, 100), None)
        z.sprites = [SC.Sprite('fall', 'kit/props/art/waterfall_3_tall_flow.png', (50, 30), (40, 0, 60, 60), -5, True, a, 'Props'),
                     SC.Sprite('tree', 'zones/woodland/art/oak.png', (50, 30), (40, 0, 60, 60), 0, True, a, 'Props')]
        names = [f.subject for f in SC.check_occlusion(z)]
        self.assertEqual(names, ['tree'])

    def test_a_scene_sprite_takes_its_parents_z(self):
        # (round 8, L8-1) outside the kit too, a sprite's z is its effective z: a floor plate under
        # a Node2D at z_index -9 is on the ground layer, as Godot draws it, including through an
        # instanced scene, unless a node sets z_as_relative false
        import tempfile
        from scripts.review import scene as SC
        with tempfile.TemporaryDirectory() as d:
            png = os.path.join(d, 'plate.png')
            Image.fromarray(np.full((8, 8, 4), 255, np.uint8)).save(png)
            sub = os.path.join(d, 'piece.tscn')
            with open(sub, 'w') as f:
                f.write('[gd_scene format=3]\n\n[ext_resource type="Texture2D" path="%s" id="t"]\n\n'
                        '[node name="Piece" type="Node2D"]\nz_index = 1\n\n'
                        '[node name="Deck" type="Sprite2D" parent="."]\ntexture = ExtResource("t")\n\n'
                        '[node name="Top" type="Sprite2D" parent="."]\ntexture = ExtResource("t")\n'
                        'z_index = 4\nz_as_relative = false\n' % png)
            top = os.path.join(d, 'zone.tscn')
            with open(top, 'w') as f:
                f.write('[gd_scene format=3]\n\n[ext_resource type="PackedScene" path="%s" id="p"]\n\n'
                        '[node name="Zone" type="Node2D"]\n\n'
                        '[node name="Floor" type="Node2D" parent="."]\nz_index = -9\n\n'
                        '[node name="If_up" type="Node2D" parent="Floor"]\n\n'
                        '[node name="Plate" type="Sprite2D" parent="Floor/If_up"]\nz_index = 2\n\n'
                        '[node name="Bridge" parent="Floor" instance=ExtResource("p")]\n' % sub)
            nodes = {e['key']: e['z'] for e in SC._walk_nodes(SC.parse_tscn(top), '')}
        self.assertEqual(nodes['Floor/If_up/Plate'], -7)
        self.assertEqual(nodes['Floor/Bridge'], -8)        # the instance's root keeps its own z_index 1
        self.assertEqual(nodes['Floor/Bridge/Deck'], -8)
        self.assertEqual(nodes['Floor/Bridge/Top'], 4)

    def test_overlapping_ground_layer_pieces_sort_sensibly(self):
        # (round 8, L8-1) two ground-layer pieces that overlap: the one drawn over the other must not
        # stand behind it. A deck whose y-sort point is far below its feet draws over a foam patch that
        # lies in front of it, a fault; with its point on its foot line it sorts under the foam, clean.
        # One piece's own parts (one y-sort point) and two states of one thing are not compared
        from scripts.review import scene as SC
        a = np.zeros((40, 40, 4), np.uint8)
        a[..., 3] = 255
        z = SC.Zone('t', (200, 200), None)
        deck = SC.Sprite('deck', 'kit/props/art/footbridge.png', (60, 150), (40, 20, 80, 60), -5, True, a, 'Props/deck/Sprite')
        foam = SC.Sprite('foam', 'kit/props/art/waterfall_3_flow.png', (60, 100), (40, 60 - 10, 80, 90), -5, True, a, 'Props/fall/Flow')
        z.sprites = [deck, foam]
        self.assertEqual([f.detector for f in SC.check_ground_layer(z)], ['logic.ground_order'])
        deck.origin = (60, 60)
        self.assertEqual(SC.check_ground_layer(z), [])
        deck.origin = (60, 150)
        foam.z = -6                                        # meant to lie under: a lower z, clean
        self.assertEqual(SC.check_ground_layer(z), [])
        foam.z, foam.origin = -5, (60, 150)                # one piece's parts keep their scene order
        self.assertEqual(SC.check_ground_layer(z), [])


class Water(unittest.TestCase):
    def test_a_fall_is_scored_against_its_house_sibling(self):
        # (woodland water review, round 5, W5-1) no official Eastward shot shows a falling sheet, and
        # 37's box is mist over a lawn: a fall is scored against the woodland's sheet (groups.fall),
        # and the mist is not a water band; other kinds keep theirs
        from scripts.review import bands as B
        groups = B.load_bands()['groups']
        self.assertNotIn('water', groups)
        self.assertIn('mist', groups)
        self.assertEqual((groups['fall']['tones'], groups['fall']['shapes']), (17.0, 39.5))
        rgb = np.zeros((40, 40, 3), np.uint8)
        alpha = np.ones((40, 40), bool)
        self.assertEqual(A.group_of('waterfall', rgb, alpha), 'fall')
        self.assertEqual(A.group_of('bench', rgb, alpha), 'prop')
        self.assertEqual(A.group_of('boulder', rgb, alpha), 'stone')

    def test_a_falls_grain_runs_down(self):
        # (round 5, K5-1) streaks falling pass the direction check; a chip mosaic fails it
        from scripts.review import bands as B
        rng = np.random.default_rng(3)
        lanes = rng.integers(60, 200, (1, 30))
        streaks = np.repeat(np.repeat(lanes, 60, 0)[..., None], 3, 2).astype(np.uint8)
        streaks[::20] = 255
        chips = np.repeat(np.repeat(rng.integers(60, 200, (30, 15)), 2, 0), 2, 1)
        chips = np.repeat(chips[..., None], 3, 2).astype(np.uint8)
        m = np.ones((60, 30), bool)
        self.assertTrue(B.fall_grain(streaks, m)['passed'])
        self.assertFalse(B.fall_grain(chips, m)['passed'])
        # (round 6, K6-1) and its value: a lit sheet of varied streaks passes, the same sheet a third
        # darker (a blue curtain) fails
        # (round 7, K7-1: and wide in range, with dark streaks through its east third)
        cols = [(250, 150, 245, 130, 240)[x % 5] if x < 20 else (60, 245, 240, 200, 250)[x % 5] for x in range(30)]
        lit = np.repeat(np.repeat(np.array([cols]), 60, 0)[..., None], 3, 2).astype(np.uint8)
        self.assertTrue(B.fall_value(lit, m)['passed'], B.fall_value(lit, m))
        self.assertFalse(B.fall_value((lit * 0.66).astype(np.uint8), m)['passed'])

    def test_staircase_bank(self):
        a = lawn()
        for y in range(300):
            x0 = 100 + (y // 8) * 4          # 4 px risers every 8 rows: equal teeth
            a[y, x0:x0 + 30, :3] = BLUE
        self.assertTrue(any(f.detector == 'logic.water_staircase' for f in water.check_banks(a, H)))

    def test_meandering_bank_is_clean(self):
        a = lawn()
        for y in range(300):
            x0 = int(150 + 25 * np.sin(y / 40))
            a[y, x0:x0 + 30, :3] = BLUE
        self.assertFalse(any(f.detector == 'logic.water_staircase' for f in water.check_banks(a, H)))

    def test_ruler_channel(self):
        a = lawn(400, 400)
        for y in range(400):
            x0 = 50 + int(y * 0.4)
            a[y, x0:x0 + 25, :3] = BLUE
        self.assertTrue(any(f.detector == 'logic.water_straight' for f in water.check_banks(a, H)))

    def test_short_bridge(self):
        a = lawn(400, 200)
        a[80:120, :, :3] = BLUE
        a[78:122, 180:210, :3] = (120, 80, 40)       # a deck that barely passes the banks
        self.assertTrue(any(f.detector == 'logic.bridge_span' for f in water.check_bridges(a, H)))
        b = lawn(400, 200)
        b[80:120, :, :3] = BLUE
        b[60:140, 180:210, :3] = (120, 80, 40)       # lands 20 px on each bank
        self.assertFalse(any(f.detector == 'logic.bridge_span' for f in water.check_bridges(b, H)))

    def test_flat_foam_plate_is_caught(self):
        # the woodland's plunge foam the auditor failed on 4 Nov (calibration W15): a 118 x 19 plate in
        # two tones at the foot of a streaked sheet, which check_falls (tall bands only) never saw
        p = Path(core.REPO) / 'scripts' / 'review' / 'calibration' / 'woodland_plunge_foam_4881fee7.png'
        a = np.asarray(Image.open(p).convert('RGBA'))
        fs = [f for f in water.check_foam(a, 74) if f.detector == 'detail.foam_flat']
        self.assertEqual(len(fs), 1)
        x0, y0, x1, y1 = fs[0].box
        self.assertGreaterEqual(x1 - x0, 100)
        self.assertLessEqual(y1 - y0, 24)

    def test_broken_plunge_foam_passes(self):
        # rocks.plunge: broken clumps in 4 to 5 tones with the pool between them, within the foot
        from scripts.art.native import ctx, load_biome
        ctx.configure(3.0, load_biome('woodland'), {})
        from scripts.art.native import rocks as RK
        from scripts.art.native.palette import C as CC, LUT
        cv = np.full((120, 200), CC('water', 2), np.int32)
        cv[:40, 70:132] = CC('water', 3)                  # the sheet's foot
        foam = RK.plunge(cv, 70, 132, 40, seed=65)
        rgb = LUT[cv]
        a = np.dstack([rgb, np.full(cv.shape, 255, np.uint8)])
        self.assertFalse(any(f.detector == 'detail.foam_flat' for f in water.check_foam(a, 74)))
        ys, xs = np.nonzero(foam)
        self.assertGreaterEqual(int(xs.min()), 70 - RK.PLUNGE_PAD)
        self.assertLess(int(xs.max()), 132 + RK.PLUNGE_PAD)
        self.assertLessEqual(int(ys.max()), 40 + 10)
        self.assertGreaterEqual(len(np.unique(cv[foam])), 4, 'four or more tones in the foam')


class Screen(unittest.TestCase):
    def test_dotted_line(self):
        a = lawn()
        for y in range(60, 140, 8):
            a[y:y + 4, 200:203, :3] = (230, 180, 60)
        self.assertTrue(any(f.detector == 'logic.stray_line' for f in screen.artefacts(a, H, np.zeros(a.shape[:2], bool))))

    def test_debug_overlay(self):
        a = lawn()
        a[100:220, 100:260, :3] = (230, 140, 50)
        self.assertTrue(screen.debug_overlay(a, H, np.zeros(a.shape[:2], bool)))

    def test_falloff_only_indoors(self):
        a = lawn()
        self.assertTrue(screen.falloff(a, H, np.zeros(a.shape[:2], bool), 'cellar'))
        self.assertFalse(screen.falloff(a, H, np.zeros(a.shape[:2], bool), 'woodland'))


def sprite(w, h):
    return np.zeros((h, w, 4), np.uint8)


class Asset(unittest.TestCase):
    def test_floating_crown(self):
        s = sprite(80, 160)
        s[10:80, 10:70] = (60, 120, 50, 255)
        s[100:158, 35:45] = (110, 70, 40, 255)
        self.assertTrue(C.floating_parts(s[..., 3] > 0, H, 'x/beech'))

    def test_mesh_crown_and_green_paint(self):
        # a crown of outlined blobs with gaps trips; the same green as door and shutter paint on a
        # mostly stone building does not (fix queue 2: the hut's green woodwork)
        s = sprite(160, 120)
        for cy in range(10, 110, 22):
            for cx in range(10, 150, 22):
                yy, xx = np.mgrid[0:120, 0:160]
                m = (xx - cx) ** 2 + (yy - cy) ** 2 <= 80
                s[m] = (60, 120, 50, 255)
                s[m & ((xx - cx) ** 2 + (yy - cy) ** 2 > 60)] = (20, 40, 20, 255)
        self.assertTrue(C.crown_holes(s[..., :3], s[..., 3] > 0, H, 'x/oak'))
        b = sprite(300, 200)
        b[:, :] = (140, 130, 120, 255)
        b[...] = (140, 130, 120, 255)
        for x0 in (20, 120, 220):
            for k in range(0, 50, 6):
                b[100:190, x0 + k:x0 + k + 5] = (60, 120, 50, 255)
        self.assertFalse(C.crown_holes(b[..., :3], b[..., 3] > 0, H, 'crossroads/hut'))
        self.assertFalse(C.crown_holes(s[..., :3], s[..., 3] > 0, H, 'crossroads/library_damage'))

    def test_bush_on_stilts(self):
        s = sprite(100, 90)
        s[5:70, 5:95] = (70, 130, 60, 255)
        for x in (25, 45, 65):
            s[70:88, x:x + 6] = (110, 70, 40, 255)
        self.assertTrue(C.stilts(s[..., :3], s[..., 3] > 0, H, 'x/bush'))

    def test_rosette_in_temperate_wood(self):
        s = sprite(60, 50)
        cx, cy = 30, 48
        for ang in np.linspace(0.25, np.pi - 0.25, 7):
            for r in range(0, 40):
                x, y = int(cx + r * np.cos(ang)), int(cy - r * np.sin(ang))
                w = max(0, 3 - r // 14)
                s[max(0, y - 1):y + 1, max(0, x - w):x + w + 1] = (60, 120, 70, 255)
        self.assertTrue(C.biome_form(s[..., :3], s[..., 3] > 0, H, 'kit/fern', 'woodland'))
        self.assertFalse(C.biome_form(s[..., :3], s[..., 3] > 0, H, 'kit/fern', 'desert'))

    def test_flat_part_and_volume(self):
        s = sprite(60, 60)
        s[5:55, 5:55] = (140, 100, 60, 255)
        fs, _ = D.judge_object(s[..., :3], s[..., 3] > 0, H, 'x/crate')
        kinds = {f.detector for f in fs}
        self.assertIn('detail.flat', kinds)
        self.assertIn('detail.volume', kinds)

    def test_shaded_part_passes_volume(self):
        s = sprite(60, 60)
        for x in range(5, 55):
            for y in range(5, 55):
                s[y, x, :3] = np.clip(200 - 2 * x - y + ((x * 7 + y * 3) % 5) * 6, 0, 255)
        s[5:55, 5:55, 3] = 255
        fs, _ = D.judge_object(s[..., :3], s[..., 3] > 0, H, 'x/stone')
        self.assertNotIn('detail.volume', {f.detector for f in fs})

    def test_half_disc_water(self):
        s = sprite(60, 60)
        s[10:55, 5:55] = (120, 120, 120, 255)
        yy, xx = np.mgrid[0:60, 0:60]
        disc = ((xx - 30) ** 2 + (yy - 30) ** 2 <= 18 ** 2) & (yy >= 30)
        s[disc] = (*BLUE, 255)
        self.assertTrue(C.water_shape(s[..., :3], s[..., 3] > 0, H, 'x/well'))

    def test_well_hood_outline_is_not_the_beam(self):
        # a slate hood's dark lower outline is wider than the windlass beam; the crank past the beam must count
        s = sprite(100, 100)
        s[4:10, 5:95] = (70, 90, 140, 255)          # slate hood
        s[10, 5:95] = (20, 20, 24, 255)             # its dark outline
        s[11:90, 30:34] = (130, 85, 45, 255)        # posts
        s[11:90, 66:70] = (130, 85, 45, 255)
        s[30:33, 30:70] = (150, 100, 55, 255)       # beam
        s[33:35, 70:78] = (60, 60, 66, 255)         # iron crank arm, below the beam end
        s[35:40, 76:78] = (60, 60, 66, 255)         # handle
        s[60:90, 20:80] = (128, 128, 128, 255)      # well ring
        fs = C.construction(s[..., :3], s[..., 3] > 0, 100, 'x/well', 'well')
        self.assertEqual([], [f.detector for f in fs])

    def test_building_detail_bar_is_a_blocker(self):
        # a flat building (one fill, an outline) is held back as a blocker; a flat prop only a fault
        from scripts.review import assets as A
        s = sprite(120, 120)
        s[10:110, 10:110] = (150, 140, 130, 255)
        s[10, 10:110] = s[109, 10:110] = (30, 30, 30, 255)
        self.assertTrue(A.is_building('crossroads/bakery'))
        self.assertFalse(A.is_building('crossroads/bakery_damage'))
        fs, sc = A.review_rgba(s, 'crossroads/bakery', 'bakery', 'valley')
        bar = [f for f in fs if f.detector == 'detail.bar']
        self.assertTrue(bar and bar[0].severity == 'blocker')
        fs, sc = A.review_rgba(s, 'crossroads/crate', 'crate', 'valley')
        self.assertNotIn('blocker', [f.severity for f in fs if f.detector == 'detail.bar'])

    def test_cylinder(self):
        s = sprite(40, 100)
        s[10:95, 8:32] = (150, 150, 150, 255)
        self.assertTrue(C.cylinder(s[..., :3], s[..., 3] > 0, H, 'x/pillar'))
        for x in range(8, 32):
            t = (x - 8) / 24
            s[10:95, x, :3] = int(170 - 90 * t + 40 * np.exp(-((t - 0.3) / 0.12) ** 2))
        self.assertFalse(C.cylinder(s[..., :3], s[..., 3] > 0, H, 'x/pillar'))

    def test_scale_against_guide(self):
        s = sprite(60, 200)
        s[5:198, 10:50, 3] = 255
        self.assertTrue(C.scale(s[..., 3] > 0, H, 'barrel', 'x/barrel', 3.0))

    def test_signpost_boards_are_not_a_shaft(self):
        s = sprite(60, 120)
        s[10:30, 5:55] = (150, 110, 70, 255)
        s[10:30, 5:10] = (210, 170, 120, 255)
        s[30:118, 27:33] = (120, 85, 55, 255)
        self.assertFalse(C.cylinder(s[..., :3], s[..., 3] > 0, H, 'kit/signpost'))

    def test_scale_of_spread_pieces_and_rubble(self):
        # a ring of small mushrooms is judged by each mushroom's height, not by the ring's depth;
        # one mushroom 17 px tall still trips. A building's rubble is a pile, not the building.
        s = np.zeros((60, 140), bool)
        for k in range(10):
            a = 2 * np.pi * k / 10
            x, y = int(70 + 55 * np.cos(a)), int(30 + 22 * np.sin(a))
            s[y:y + 9, x:x + 6] = True
        self.assertFalse(C.scale(s, H, 'mushroom_ring', 'kit/mushroom_ring', 3.0))
        s[5:56, 60:66] = True
        self.assertTrue(C.scale(s, H, 'mushroom_ring', 'kit/mushroom_ring', 3.0))
        self.assertEqual(C.kind_of('smithy_rubble'), 'pile')
        self.assertEqual(C.kind_of('smithy'), 'smithy')


class Scene(unittest.TestCase):
    def test_tscn_parser_positions(self):
        t = tempfile.NamedTemporaryFile('w', suffix='.tscn', delete=False)
        t.write('[gd_scene format=3]\n\n[node name="Z" type="Node2D"]\n\n'
                '[node name="A" type="Node2D" parent="."]\nposition = Vector2(10, 20)\n\n'
                '[node name="B" type="Marker2D" parent="A"]\nposition = Vector2(5, 5)\n')
        t.close()
        nodes = SN._walk_nodes(SN.parse_tscn(t.name), '')
        pos = {e['key']: e['pos'] for e in nodes}
        self.assertEqual(pos['A/B'], (15.0, 25.0))
        os.unlink(t.name)


class Gate(unittest.TestCase):
    """The placement gate (Matt, 8 Nov 00:05: only reviewed art is placeable): a reviewer pass places,
    the seeded fix queue places, everything else is refused; the detectors' status never decides."""
    ZONE, NAME = 'woodland', 'stump'

    def setUp(self):
        self.old = gate.CATALOGUE, gate.QUEUE
        self.real_queue = gate.QUEUE
        gate.TODAY = datetime.date(2026, 11, 9)
        self.d = tempfile.mkdtemp()
        gate.CATALOGUE = self.d
        gate.QUEUE = os.path.join(self.d, 'fix-queue.json')
        self.png = os.path.join(gate.GAME, 'zones', self.ZONE, 'art', self.NAME + '.png')
        self.sha = A.sha256(self.png)
        os.makedirs(os.path.join(self.d, self.ZONE))

    def tearDown(self):
        gate.CATALOGUE, gate.QUEUE = self.old
        gate.TODAY = None
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)

    def put(self, status='pass', reviewer=None, sha=None, findings=()):
        rec = {'id': f'{self.ZONE}/{self.NAME}', 'sha256': sha or self.sha, 'status': status,
               'findings': list(findings)}
        if reviewer is not None:
            rec['reviewer'] = reviewer
        Path(os.path.join(self.d, self.ZONE, self.NAME + '.json')).write_text(json.dumps(rec))

    def refused(self):
        return gate.refusals(self.ZONE, [self.NAME])

    def queue_it(self, **over):
        """A complete queue entry for the asset (Claude A, 9 Nov), with fields overridden or (None) dropped."""
        e = {'id': f'{self.ZONE}/{self.NAME}', 'sha256': self.sha, 'queued': '2026-11-09',
             'reason': 'placed before the 25 Oct seed', 'clears_when': 'redrawn and passed', 'review_by': '2026-11-30'}
        e.update(over)
        e = {k: v for k, v in e.items() if v is not None}
        Path(gate.QUEUE).write_text(json.dumps({'queue': [e]}))

    def test_no_record_refused(self):
        self.assertIn('no review record', self.refused()[0])

    def test_pass_places(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pass'})
        self.assertEqual(self.refused(), [])

    def test_pending_refused(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pending'})
        bad = self.refused()
        self.assertEqual(len(bad), 1)
        self.assertIn(f'{self.ZONE}/{self.NAME}', bad[0])
        self.assertIn('pending', bad[0])
        self.assertIn('detail-auditor', bad[0])

    def test_missing_reviewer_refused(self):
        self.put(reviewer=None)
        self.assertIn('no reviewer verdict', self.refused()[0])
        self.put(reviewer={'agent': 'detail-auditor'})
        self.assertIn('no reviewer verdict', self.refused()[0])

    def test_fail_refused(self):
        # a reviewer fail refuses even when every detector passed
        self.put(status='pass', reviewer={'agent': 'detail-auditor', 'verdict': 'fail'})
        self.assertIn('failed independent review', self.refused()[0])

    def test_unknown_verdict_refused(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pass with fixes'})
        self.assertIn('is not "pass"', self.refused()[0])

    def test_fix_queue_places(self):
        self.put(status='fail', reviewer={'agent': 'detail-auditor', 'verdict': 'pending'},
                 findings=[{'detector': 'logic.scale', 'severity': 'fault'}])
        self.assertTrue(self.refused())
        self.queue_it()
        self.assertEqual(self.refused(), [])
        self.put(reviewer=None)                                       # queued, no reviewer at all
        self.assertEqual(self.refused(), [])

    def test_rejected_detector_finding_with_reviewer_pass_places(self):
        # the Act 1 bitt and net: the detectors' fail stays in `status`, the reviewer rejected the finding
        self.put(status='fail', findings=[{'detector': 'detail.cluster_noise', 'severity': 'fault'}],
                 reviewer={'agent': 'detail-auditor', 'verdict': 'pass',
                           'note': 'the detail.cluster_noise fault is rejected as structure'})
        self.assertEqual(self.refused(), [])

    def test_detector_pass_alone_refused(self):
        self.put(status='pass', reviewer={'agent': 'detail-auditor', 'verdict': 'pending'})
        self.assertTrue(self.refused())

    def test_stale_refused_even_when_passed_or_queued(self):
        self.put(sha='x', reviewer={'agent': 'detail-auditor', 'verdict': 'pass'})
        self.assertIn('changed since its record', self.refused()[0])
        self.queue_it()
        self.assertIn('changed since its record', self.refused()[0])

    # the queue's own rules (Claude A, 9 Nov): an entry places its asset only while it holds

    def test_queued_picture_that_changed_is_refused(self):
        # the record is current but the queue entry holds other bytes: a queue entry never covers a new picture
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pending'})
        self.queue_it(sha256='0' * 64)
        self.assertIn('changed since it was queued', self.refused()[0])

    def test_queue_entry_missing_a_field_is_refused(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pending'})
        for field in ('queued', 'reason', 'clears_when', 'review_by', 'sha256'):
            with self.subTest(field=field):
                self.queue_it(**{field: None})
                bad = self.refused()
                self.assertEqual(len(bad), 1)
                self.assertIn('lacks', bad[0])
                self.assertIn(field, bad[0])

    def test_expired_queue_entry_is_refused(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pending'})
        self.queue_it(review_by='2026-11-30')
        self.assertEqual(self.refused(), [])
        gate.TODAY = datetime.date(2026, 11, 30)                      # the due date itself still holds
        self.assertEqual(self.refused(), [])
        gate.TODAY = datetime.date(2026, 12, 1)
        self.assertIn('expired on 2026-11-30', self.refused()[0])
        self.queue_it(review_by='end of November')
        self.assertIn('not a date', self.refused()[0])

    def test_failed_asset_is_queued_only_with_its_fix_list(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'fail', 'note': 'the tub body is undrawn'})
        self.queue_it()
        self.assertIn('fix_list', self.refused()[0])
        self.queue_it(fix_list=[])
        self.assertIn('fix_list', self.refused()[0])
        self.queue_it(fix_list=['the tub body is undrawn: draw its staves'])
        self.assertEqual(self.refused(), [])

    def test_queued_asset_that_passes_is_advised_out(self):
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pending'})
        self.queue_it()
        self.assertEqual(gate.advisories(), [])
        self.put(reviewer={'agent': 'detail-auditor', 'verdict': 'pass'})
        self.assertEqual(self.refused(), [])
        adv = gate.advisories()
        self.assertEqual(len(adv), 1)
        self.assertIn(f'{self.ZONE}/{self.NAME}', adv[0])
        self.assertIn('remove it from', adv[0])

    def test_the_real_queue_entries_are_complete(self):
        # every entry in art/catalogue/fix-queue.json states what the gate requires
        # (an empty queue is the end state the queue is for: every placed-before-seed asset reviewed;
        # the file must still hold a queue list)
        doc = json.load(open(self.real_queue))
        self.assertIsInstance(doc.get('queue'), list)
        entries = doc['queue']
        for e in entries:
            with self.subTest(id=e.get('id')):
                for k in gate.REQUIRED:
                    self.assertTrue(e.get(k), k)
                datetime.date.fromisoformat(e['queued'])
                datetime.date.fromisoformat(e['review_by'])


class Record(unittest.TestCase):
    """review:asset --record keeps an independent verdict while the bytes are unchanged."""

    def setUp(self):
        self.old = A.CATALOGUE
        self.d = tempfile.mkdtemp()
        A.CATALOGUE = self.d
        self.path = os.path.join(self.d, 'woodland', 'stump.json')

    def tearDown(self):
        A.CATALOGUE = self.old
        import shutil
        shutil.rmtree(self.d, ignore_errors=True)

    def report(self, sha, status='fail'):
        return {'id': 'woodland/stump', 'sha256': sha, 'status': status,
                'findings': [{'detector': 'detail.cluster_noise', 'severity': 'fault', 'box': [0, 0, 4, 4],
                              'message': 'm', 'fix': 'f', 'score': 0.6}]}

    def verdict(self):
        return json.loads(Path(self.path).read_text())['reviewer']

    def test_first_record_is_pending(self):
        A.record(self.report('a' * 64))
        self.assertEqual(self.verdict()['verdict'], 'pending')

    def test_unchanged_bytes_keep_the_pass(self):
        A.record(self.report('a' * 64))
        rec = json.loads(Path(self.path).read_text())
        passed = {'agent': 'detail-auditor', 'verdict': 'pass', 'date': '2026-11-08', 'note': 'round 1'}
        rec['reviewer'] = passed
        Path(self.path).write_text(json.dumps(rec))
        A.record(self.report('a' * 64))
        self.assertEqual(self.verdict(), passed)
        self.assertEqual(json.loads(Path(self.path).read_text())['status'], 'fail')  # the detectors' result is kept as is

    def test_unchanged_bytes_keep_a_fail(self):
        A.record(self.report('a' * 64))
        rec = json.loads(Path(self.path).read_text())
        rec['reviewer'] = {'agent': 'detail-auditor', 'verdict': 'fail'}
        Path(self.path).write_text(json.dumps(rec))
        A.record(self.report('a' * 64))
        self.assertEqual(self.verdict()['verdict'], 'fail')

    def test_changed_bytes_reset_to_pending(self):
        A.record(self.report('a' * 64))
        rec = json.loads(Path(self.path).read_text())
        rec['reviewer'] = {'agent': 'detail-auditor', 'verdict': 'pass', 'note': 'round 1'}
        Path(self.path).write_text(json.dumps(rec))
        A.record(self.report('b' * 64))
        self.assertEqual(self.verdict()['verdict'], 'pending')

    def test_explicit_reviewer_wins(self):
        A.record(self.report('a' * 64))
        A.record(self.report('a' * 64), reviewer={'agent': 'detail-auditor', 'verdict': 'pass'})
        self.assertEqual(self.verdict()['verdict'], 'pass')


def dungeon_floor(kind: str, seed: int = 3) -> np.ndarray:
    """A lawn (the screen's ground palette) beside a stone floor 240 x 400 px (17 H^2): 'calm' is an
    Eastward-like dungeon floor (dark irregular flags, joints a step under them, soft wear, pits and
    grit in two-pixel clusters, dirt in some joints); 'flat' the same area in two flat tones with ruled
    joints; 'bright' the calm floor's drawing on bright slabs of very different values (the terrazzo
    floor Matt flagged, U1)."""
    from scipy import ndimage as ndi
    rng = np.random.default_rng(seed)
    a = np.zeros((400, 640, 4), np.uint8)
    a[..., 3] = 255
    a[:, :400, :3] = GRASS
    a[:, :400][rng.random((400, 400)) < 0.3, :3] = GRASS2
    F = a[:, 400:, :3]
    fh, fw = F.shape[:2]
    if kind == 'flat':
        F[:] = (70, 66, 74)
        F[:, fw // 2:] = (78, 74, 80)
        F[::30, :] = (52, 48, 60)
        F[:, ::30] = (52, 48, 60)
        return a
    ids = np.zeros((fh, fw), int)
    y = k = 0
    while y < fh:
        hh = int(rng.integers(18, 40))
        x = int(rng.integers(-20, 0))
        while x < fw:
            ww = int(rng.integers(18, 44))
            k += 1
            ids[y:y + hh, max(0, x):x + ww] = k
            x += ww
        y += hh
    tones = [(68, 64, 72), (74, 70, 76), (64, 62, 74)] if kind == 'calm' else \
        [(150, 144, 138), (84, 78, 82), (118, 112, 110)]
    for i in range(1, k + 1):
        F[ids == i] = tones[int(rng.integers(0, 3))]
    j = np.zeros((fh, fw), bool)
    j[:-1] |= ids[:-1] != ids[1:]
    j[:, :-1] |= ids[:, :-1] != ids[:, 1:]
    F[j] = (48, 44, 56)
    wear = ndi.gaussian_filter(rng.random((fh, fw)), 2.5)
    worn = (wear > np.quantile(wear, 0.8)) & ~j
    F[worn] = F[worn] - 6
    for _ in range(2600):
        yy, xx = int(rng.integers(0, fh - 2)), int(rng.integers(0, fw - 3))
        F[yy:yy + 2, xx:xx + int(rng.integers(2, 4))] = (52, 48, 60) if rng.random() < 0.6 else (84, 80, 84)
    dirt = ndi.binary_dilation(j, iterations=1) & (ndi.gaussian_filter(rng.random((fh, fw)), 6) > 0.53)
    F[dirt] = (66, 46, 48)
    return a


class GroundPlane(unittest.TestCase):
    """detail.flat on ground planes (round 4 of the Undercroft): a calm, dark floor drawn to
    Eastward's ground band (eastward_bands.json, groups.ground) is not flat; a flat one, or a
    bright floor of contrasting slabs, still is."""

    def flat(self, kind):
        p = dungeon_floor(kind)
        ign = np.zeros(p.shape[:2], bool)
        return [f for f in screen.flat_objects(p[..., :3], H, ign) + screen.flats(p[..., :3], H, ign)
                if f.detector == 'detail.flat']

    def test_calm_eastward_like_floor_passes(self):
        self.assertEqual(self.flat('calm'), [])

    def test_flat_floor_trips(self):
        self.assertTrue(self.flat('flat'))

    def test_bright_contrasting_floor_trips(self):
        self.assertTrue(self.flat('bright'))


class LightSource(unittest.TestCase):
    """logic.light_source: a warm pool on a dark floor needs a torch (or an opening) over it."""

    def zone(self, torch):
        a = np.zeros((300, 400, 4), np.uint8)
        a[..., :3] = (52, 48, 70)
        a[..., 3] = 255
        Y, X = np.mgrid[0:300, 0:400]
        a[((X - 200) / 60.0) ** 2 + ((Y - 150) / 40.0) ** 2 < 1, :3] = (170, 150, 120)
        sprites = []
        if torch:
            sprites.append(SN.Sprite('Torch_1', 'res://zones/x/art/torch.png', (200, 100), (190, 60, 210, 100), 0,
                                     False, np.zeros((40, 20, 4), np.uint8), 'WallFx'))
        return SN.Zone('x', (400, 300), a, sprites=sprites)

    def test_pool_without_source(self):
        self.assertTrue(SN.check_light_sources(self.zone(False), H))

    def test_pool_under_a_torch(self):
        self.assertEqual(SN.check_light_sources(self.zone(True), H), [])


class RaggedEdge(unittest.TestCase):
    """detail.ragged_edge (edges.py): a dirt path whose edge is per-pixel noise trips; the same path
    on the soft grid passes (Matt, 26 Oct 10:19); a bench's thin legs are not teeth."""
    DIRT = (150, 110, 80)

    def path(self, ragged):
        a = lawn(400, 300)[..., :3].copy()
        Y, X = np.mgrid[0:300, 0:400]
        hw = 40 + 6 * np.sin(Y / 23.0)                          # a slow wander: soft-grid runs
        m = np.abs(X - 200 - 25 * np.sin(Y / 40.0)) < hw
        if ragged:
            rng = np.random.default_rng(5)
            edge = m & ~ndi.binary_erosion(m, iterations=1)
            near = ndi.binary_dilation(m, iterations=1) & ~m
            m = (m & ~(edge & (rng.random(m.shape) < 0.35))) | (near & (rng.random(m.shape) < 0.35))
        a[m] = self.DIRT
        return a

    def test_ragged_path_trips(self):
        fs = E.ragged_ground(self.path(True), H, 'test')
        self.assertTrue(any(f.detector == 'detail.ragged_edge' for f in fs))

    def test_soft_grid_path_passes(self):
        self.assertEqual(E.ragged_ground(self.path(False), H, 'test'), [])

    def river(self, tips):
        a = lawn(400, 300)[..., :3].copy()
        Y, X = np.mgrid[0:300, 0:400]
        c = 150 + 12 * np.sin(X / 37.0)
        water = np.abs(Y - c) < 40
        bank = (np.abs(Y - c) < 46) & ~water
        a[water] = BLUE
        a[bank] = (70, 45, 42)
        if tips:                                                # one-texel grass tips every 3 texels
            comb = bank & (X % 3 == 0) & (np.abs(Y - c) >= 46 - 1 - (X * 7) % 4)    # one-texel tips of turf
            a[comb] = GRASS
        return a

    def test_bank_with_tips_trips(self):
        self.assertTrue(any('bank' in f.message for f in E.ragged_ground(self.river(True), H, 'test')))

    def test_soft_bank_passes(self):
        self.assertEqual(E.ragged_ground(self.river(False), H, 'test'), [])

    def test_sprite_thin_legs_pass(self):
        al = np.zeros((60, 90), bool)
        al[10:30, 5:85] = True                                  # a seat
        for x in (10, 11, 78, 79):
            al[30:55, x] = True                                 # legs one or two texels wide
        self.assertEqual(E.ragged(al, H, 'bench', min_area=0.02, sprite=True), [])


class CornerRadius(unittest.TestCase):
    # Matt, 26 Oct 15:36: blocky plans, "not sharp like minecraft": a plan of whole cells drawn with
    # square corners trips; the same plan rounded (outer 0.4, inner 0.25 of a cell) and lumped
    # passes, as does an organic outline with no plan corners
    def _plan(self):
        c = 24
        m = np.zeros((360, 480), bool)
        for (x, y, w, h) in ((2, 2, 11, 5), (13, 2, 6, 3), (3, 7, 5, 3), (5, 10, 15, 2)):
            m[y * c:(y + h) * c, x * c:(x + w) * c] = True
        return m

    def test_square_corners_trip(self):
        self.assertTrue(E.corner_radius(self._plan(), H, 'x/ground (dirt)'))

    def test_rounded_corners_pass(self):
        m = self._plan()
        p = 12
        mp = np.pad(m, p)
        dil = lambda a, r: ndi.distance_transform_edt(~a) <= r
        ero = lambda a, r: ndi.distance_transform_edt(a) > r
        mp = ero(dil(mp, 6), 6)
        mp = dil(ero(mp, 9.6), 9.6)
        self.assertFalse(E.corner_radius(mp[p:-p, p:-p], H, 'x/ground (dirt)'))

    def test_organic_outline_passes(self):
        yy, xx = np.mgrid[0:360, 0:480]
        ang = np.arctan2(yy - 180, xx - 240)
        r = 140 + 12 * np.sin(5 * ang) + 5 * np.sin(13 * ang)
        m = np.hypot((xx - 240), (yy - 180) * 1.5) < r
        self.assertFalse(E.corner_radius(m, H, 'x/ground (dirt)'))


class OnGrid(unittest.TestCase):
    """logic.off_grid: props and structures stand on the soft grid (8 world px, 24 texels at density
    3); clutter may sit anywhere in a cell."""

    def zone(self, x, y, name='Bench_1'):
        sp = SN.Sprite(name, 'res://zones/x/art/bench.png', (x, y), (x - 30, y - 40, x + 30, y), 0, True,
                       np.zeros((40, 60, 4), np.uint8), 'Props')
        return SN.Zone('x', (960, 960), np.zeros((960, 960, 4), np.uint8), sprites=[sp])

    def test_on_grid_passes(self):
        self.assertEqual(SN.check_grid(self.zone(12 * 24 + 12, 10 * 24)), [])

    def test_off_grid_trips(self):
        self.assertTrue(SN.check_grid(self.zone(12 * 24 + 7, 10 * 24 + 5)))

    def test_clutter_may_sit_anywhere(self):
        self.assertEqual(SN.check_grid(self.zone(12 * 24 + 7, 10 * 24 + 5, 'DebrisA')), [])

class SizeTable(unittest.TestCase):
    """logic.scale (scale.py, sizes.json): sizes against a person, doors, stairs, grain, cast."""

    def test_classes_from_names(self):
        self.assertEqual(SZ.class_of('crossroads/smithy_rubble'), 'rubble')
        self.assertEqual(SZ.class_of('crossroads/flower_tub_9'), 'flower_tub')
        self.assertEqual(SZ.class_of('crossroads/kit_lantern_24'), 'lamp')
        self.assertEqual(SZ.class_of('undercroft/stump_nw'), 'pillar_stump')
        self.assertIsNone(SZ.class_of('woodland/flow'))
        self.assertIsNone(SZ.class_of('crossroads/bakery_damage'))

    def test_a_piece_is_measured_against_its_own_spec(self):
        self.assertEqual(SZ.spec_ranges('shelter (eave 2.7 m; art px: 150 to 180 tall, 120 to 160 wide)'),
                         {'tall': (150.0, 180.0), 'wide': (120.0, 160.0)})
        self.assertEqual(SZ.spec_ranges('cairn (size-guide: 12 to 28 tall in world px)'), {})
        s = sprite(60, 200)
        s[150:198, 10:50, 3] = 255                     # 48 tall: a third of the shelter it claims to be
        f = SZ.check_spec(s, 'shelter (art px: 150 to 180 tall, 30 to 50 wide)', 'x/shelter')
        self.assertIn('logic.size_spec', [x.detector for x in f])
        s[20:198, 10:50, 3] = 255
        self.assertNotIn('logic.size_spec', [x.detector for x in SZ.check_spec(s, 'shelter (art px: 150 to 180 tall, 30 to 50 wide)', 'x/shelter')])

    def test_a_piece_is_measured_against_the_size_guide_kind_it_names(self):
        """Round 5 of the Act 1 detail audit (R5-13): the v6 mill met its own spec (160 to 190 tall)
        and was half the size guide's water mill; a spec naming the guide's kind is measured there too."""
        v6 = _png(os.path.join(os.path.dirname(FIX_V3), 'act1_v6', 'mill_wheel.png'))
        spec = 'water_mill (the mill; art px: 160 to 190 tall, 115 to 135 wide)'
        f = SZ.check_spec(v6, spec, 'act1/mill_wheel')
        self.assertIn('logic.size_guide', [x.detector for x in f])
        self.assertNotIn('logic.size_spec', [x.detector for x in f])
        s = sprite(340, 380)
        s[4:380, 4:330, 3] = 255                        # 376 x 326: inside the guide's 312 to 432 x 288 to 384
        self.assertEqual(SZ.check_spec(s, 'water_mill (art px: 310 to 432 tall, 288 to 384 wide)', 'x/mill'), [])
        self.assertEqual(SZ.guide_kind('shelter (art px: 150 to 180 tall)')[0], 'shelter')

    def test_a_size_spec_naming_no_kind_fails_loudly(self):
        """Claude A's ruling on 5 Nov: a head word that is no kind in sizes.json or the size guide is a
        fault, not a silent skip; a piece no kind fits says so with 'unsized (why ...)'."""
        s = sprite(60, 60)
        s[20:58, 10:50, 3] = 255                        # 38 x 40: inside its own spec
        self.assertEqual(SZ.guide_kind('platform (art px: 30 to 44 tall)'), ('platform', False))
        f = SZ.check_spec(s, 'platform (art px: 30 to 44 tall, 36 to 44 wide)', 'x/platform')
        self.assertEqual([x.detector for x in f], ['logic.size_guide'])
        self.assertEqual(f[0].severity, 'fault')
        self.assertIn('"platform"', f[0].message)
        self.assertEqual(SZ.guide_kind('unsized (a cell of a run; art px: 30 to 44 tall)'), ('unsized', None))
        self.assertEqual(SZ.check_spec(s, 'unsized (a cell of a run; art px: 30 to 44 tall, 36 to 44 wide)', 'x/edge'), [])
        self.assertIsNone(SZ.guide_kind(''))

    def test_the_creel_stack_and_platform_lamp_are_kinds(self):
        # Claude A's ruling on 5 Nov: both pieces are right-sized for what they are, so the guide gains them
        self.assertEqual(SZ.guide_kind('creel_stack (art px: 40 to 50 tall)')[1],
                         {'tall': (14, 55.0), 'wide': (20, 66.0)})
        self.assertEqual(SZ.guide_kind('platform_lamp (art px: 130 to 140 tall)')[1],
                         {'tall': (105.3, 152.9), 'wide': (9, 34)})
        lamp = sprite(30, 145)
        lamp[4:142, 5:25, 3] = 255                      # 138 x 20, as drawn
        self.assertEqual(SZ.check_spec(lamp, 'platform_lamp (art px: 130 to 145 tall, 14 to 24 wide)', 'x/lamp'), [])
        lamp[4:20, :, 3] = 0
        lamp[100:142, 5:25, 3] = 255
        lamp[:100, :, 3] = 0                            # 42 tall: a bollard, not a platform lamp
        self.assertIn('logic.size_guide', [x.detector for x in SZ.check_spec(lamp, 'platform_lamp (a lamp)', 'x/lamp')])

    def test_an_unsized_spec_with_a_kind_that_fits_is_caught(self):
        """Round 6 of the Act 1 detail audit (R6-3, R6-12): the v7 bitt said unsized but was the guide's
        bollard, and the v7 semaphore said unsized but was its pole (a signal mast); a justified
        unsized spec (the churn stand, ruled in sizes.json) is left alone."""
        fx = os.path.join(os.path.dirname(FIX_V3), 'act1_v7')
        bitt = ("unsized (a mooring bitt with its hawser's coil on the quay: the guide's bollard is the post alone; "
                "0.45 m, its line coiled beside it; art px: 16 to 26 tall, 32 to 50 wide)")
        f = SZ.check_spec(_png(os.path.join(fx, 'coast_mooring_bitt.png')), bitt, 'act1/coast_mooring_bitt')
        self.assertEqual([x.detector for x in f], ['logic.size_unsized'])
        self.assertIn('bollard', f[0].message)
        sema = 'unsized (a semaphore signal: no kind in the guide; a semaphore post 3 m; art px: 125 to 160 tall, 30 to 50 wide)'
        f = SZ.check_spec(_png(os.path.join(fx, 'halt_semaphore.png')), sema, 'act1/halt_semaphore')
        self.assertIn('pole', [m for x in f for m in [x.message.split("guide's ")[1].split(' ')[0]]])
        self.assertTrue(all(x.detector == 'logic.size_unsized' for x in f))
        stand = ("unsized (a churn stand with its churns: the churns kind is the churns alone; deck 0.65 m; "
                 "art px: 60 to 80 tall, 56 to 80 wide)")
        self.assertEqual(SZ.unsized_fits(stand, {'tall': 68, 'wide': 66}), [])
        self.assertEqual(SZ.unsized_fits('unsized (a chambered barrow, a landmark; art px: 160 to 190 tall)',
                                         {'tall': 177, 'wide': 326}), [])
        self.assertEqual(SZ.unsized_fits('bollard (art px: 16 to 26 tall)', {'tall': 21, 'wide': 42}), [])

    def test_the_asset_gate_measures_a_kit_piece_against_its_spec(self):
        """R6-12: logic.size_spec and logic.size_guide ran only in test_act1; the asset gate now reads a
        kit picture's audit.size_class and runs check_spec, so the reviewer's sheet shows it."""
        lamp = os.path.join(REPO_ROOT, 'game', 'kit', 'props', 'art', 'act1', 'halt_platform_lamp.png')
        self.assertTrue(SZ.kit_spec(lamp).startswith('platform_lamp ('))
        self.assertIsNone(SZ.kit_spec(os.path.join(REPO_ROOT, 'game', 'kit', 'props', 'art', 'act1', 'coast_buoy_loop.png')))
        s = sprite(60, 60)
        s[10:58, 10:50, 3] = 255                                   # 48 x 40: a third of a water mill
        f, _ = A.review_rgba(s, 'x/mill', 'mill', 'valley', size_class='water_mill (art px: 300 to 400 tall)')
        got = [x.detector for x in f]
        self.assertIn('logic.size_guide', got)
        self.assertIn('logic.size_spec', got)
        f, _ = A.review_rgba(s, 'x/mill', 'mill', 'valley')
        self.assertNotIn('logic.size_guide', [x.detector for x in f])

    def test_a_drying_net_is_not_read_as_a_crown(self):
        """R6-12: construct.crown_holes read the v7 net rack's green twine as a see-through crown; a net
        is mostly air (R3-6), so a piece named as a net is skipped. A bush with the same pixels still trips."""
        im = _png(os.path.join(os.path.dirname(FIX_V3), 'act1_v7', 'coast_net_rack.png'))
        rgb, alpha = A.on_ground(im, A.NEUTRAL), im[..., 3] > 128
        self.assertEqual(C.crown_holes(rgb, alpha, 74, 'act1/coast_net_rack'), [])
        self.assertEqual(C.crown_holes(rgb, alpha, 74, 'x/fishing_net'), [])
        self.assertEqual([x.detector for x in C.crown_holes(rgb, alpha, 74, 'x/bush')], ['detail.mesh'])
        self.assertEqual([x.detector for x in C.crown_holes(rgb, alpha, 74, 'x/nettle_bed')], ['detail.mesh'])

    def test_every_kit_picture_meets_its_spec(self):
        """Round 7 of the Act 1 detail audit (R7-2): the asset gate's check_spec raised 93 false faults
        on fence and drystone-wall cells measured as whole fences. Every kit picture is swept through
        check_spec as the gate runs it (its piece's spec and, for a cell of a run, its run), and none may
        fault outside KNOWN (empty: the Brackens fire rings and fold were re-headed)."""
        KNOWN = set()
        idx = json.load(open(os.path.join(REPO_ROOT, 'game', 'kit', 'props', 'index.json')))
        faults, n, runs = [], 0, 0
        for pid, e in sorted(idx.items()):
            for vid, v in (e.get('variants') or {}).items():
                p = os.path.join(REPO_ROOT, 'game', v['png'][len('res://'):])
                spec = SZ.kit_spec(p)
                if not spec or not os.path.exists(p):
                    continue
                n += 1
                run = SZ.kit_run(p)
                runs += run is not None
                for f in SZ.check_spec(_png(p), spec, 'kit/%s/%s' % (pid, vid), run=run):
                    if '%s/%s' % (pid, vid) not in KNOWN:
                        faults.append(f.message)
        self.assertGreater(n, 150)
        self.assertGreater(runs, 80)
        self.assertEqual(faults, [])
        # a north-south fence cell is the run's length down the screen, not a fence's height
        ns = os.path.join(REPO_ROOT, 'game', 'kit', 'props', 'art', 'fence', 'fence_rail_ns_plain.png')
        if os.path.exists(ns):
            self.assertIn('logic.size_guide', [f.detector for f in SZ.check_spec(_png(ns), 'fence (a rail fence)', 'x/ns')])
            self.assertEqual(SZ.check_spec(_png(ns), 'fence (a rail fence)', 'x/ns', run=SZ.kit_run(ns)), [])

    def test_a_class_name_counts_only_where_a_word_starts(self):
        # the detail audit of 4 Nov: "urn" inside "churn" sized the churn stand as a barrel
        self.assertNotEqual(SZ.class_of('kit/halt_churn_stand'), 'barrel')
        self.assertNotEqual(SZ.class_of('kit/halt_timetable_board'), 'table')
        self.assertEqual(SZ.class_of('kit/farm_churns'), 'churns')
        self.assertEqual(SZ.class_of('kit/fingerpost_nesw'), 'sign')
        self.assertEqual(SZ.class_of('x/haystack'), 'haystack')

    def test_barrel_too_tall_trips_and_true_size_passes(self):
        s = sprite(48, 80)
        s[20:73, 8:40, 3] = 255                       # 53 art px: 0.72 A
        fs = SZ.check_sprite(s[..., 3] > 0, 'x/barrel_1')
        self.assertTrue(any(f.severity == 'fault' for f in fs))
        s[:, :, 3] = 0
        s[33:73, 10:38, 3] = 255                      # 40 art px: 0.54 A
        self.assertEqual(SZ.check_sprite(s[..., 3] > 0, 'x/barrel_1'), [])

    def test_specks_do_not_count(self):
        s = sprite(48, 80)
        s[33:73, 10:38, 3] = 255
        s[2:4, 2:4, 3] = 255                          # a 4 px speck far above
        self.assertEqual(SZ.check_sprite(s[..., 3] > 0, 'x/barrel_1'), [])

    def _house(self, door_h):
        stone, leaf = (142, 135, 130), (178, 70, 90)
        a = np.zeros((200, 160, 4), np.uint8)
        a[20:197, 12:148] = stone + (255,)
        B = 196
        cx = 12 + 60
        a[B - door_h + 1:B + 1, cx - 22:cx + 22] = leaf + (255,)
        return a, {'kind': 'cottage', 'door': 20, 'overhang': 3, 'wall_h': 40, 'roof_h': 40}

    def test_door_opening_measured(self):
        a, look = self._house(92)
        m = SZ.measure_opening(a, 12 + 60, 196)
        self.assertAlmostEqual(m['h'], 92, delta=2)
        self.assertAlmostEqual(m['w'], 44, delta=2)
        fs = SZ.check_building(a, 'x', 'cottage', look)
        self.assertFalse([f for f in fs if 'door' in f.subject])

    def test_small_door_trips(self):
        a, look = self._house(52)
        fs = SZ.check_building(a, 'x', 'cottage', look)
        self.assertTrue(any('door' in f.subject and f.severity == 'fault' for f in fs))

    def test_stair_pitch(self):
        rgb = np.full((60, 120, 3), 150, np.uint8)
        for y in range(0, 60, 16):
            rgb[y + 4:y + 12] = 90                    # 8 px dark riser, 16 px pitch
        m = SZ.stair_pitch(rgb, (0, 0, 120, 60))
        self.assertEqual(m['pitch'], 16)

    def test_speckled_ground_trips_and_clumped_passes(self):
        rng = np.random.default_rng(3)
        g = np.zeros((300, 600, 3), np.uint8)
        g[:] = GRASS
        speck = g.copy()
        for _ in range(3000):                         # many 2 px dark ticks
            y, x = rng.integers(0, 298), rng.integers(0, 598)
            speck[y:y + 2, x] = (90, 110, 50)
        self.assertTrue(any(f.severity == 'fault' for f in SZ.check_grain(speck, H, 'x/ground', jpeg=False)))
        calm = g.copy()
        for _ in range(140):                          # fewer 6 px tufts
            y, x = rng.integers(0, 292), rng.integers(0, 592)
            calm[y:y + 6, x:x + 5] = (100, 120, 60)
        self.assertFalse(any(f.severity == 'fault' for f in SZ.check_grain(calm, H, 'x/ground', jpeg=False)))

    def test_body_height_ignores_a_spear(self):
        a = np.zeros((144, 160), bool)
        a[62:137, 70:90] = True                       # a 75 px body
        a[30:137, 95:97] = True                       # a spear, 2 px wide
        a[60:62, 90:95] = True                        # the hand that holds it
        self.assertEqual(SZ.body_height(a, 136), 75)


class CropSheet(unittest.TestCase):
    def setUp(self):
        self.native = np.arange(32 * 40 * 3, dtype=np.uint8).reshape(32, 40, 3)

    def finding(self, box):
        return core.Finding('test.crop', 'fault', box, 'message', 'fix', subject='piece')

    def test_integer_output_is_unchanged(self):
        with tempfile.TemporaryDirectory() as out:
            path = os.path.join(out, 'crops.png')
            core.crop_sheet(self.native, [self.finding((8, 7, 15, 14))], path, cell=80, cols=1)
            with Image.open(path) as image:
                self.assertEqual(hashlib.sha256(image.tobytes()).hexdigest(),
                                 '54f240ac50e0e537f63be3d726d076e1e65e1fa5e0e1a4dba1a627fcad9373ff')

    def test_fractional_crop_covers_padded_box_without_mutating_finding(self):
        finding = self.finding((8.25, 7.5, 15.75, 14.25))
        before = finding.to_json(scale=2.5, origin=(1.5, 3.25))
        original = Image.fromarray
        with tempfile.TemporaryDirectory() as out, patch.object(core.Image, 'fromarray', wraps=original) as capture:
            core.crop_sheet(self.native, [finding], os.path.join(out, 'crops.png'), cell=80, cols=1)
            np.testing.assert_array_equal(capture.call_args.args[0], self.native[3:19, 4:20])
        self.assertEqual(finding.box, (8.25, 7.5, 15.75, 14.25))
        self.assertEqual(finding.to_json(scale=2.5, origin=(1.5, 3.25)), before)

    def test_fractional_edges_clip_to_image(self):
        original = Image.fromarray
        for box, expected in [((-2.5, -1.25, 1.5, 2.25), self.native[:7, :6]),
                              ((38.5, 30.5, 42.25, 35.75), self.native[26:, 34:])]:
            with self.subTest(box=box), tempfile.TemporaryDirectory() as out:
                with patch.object(core.Image, 'fromarray', wraps=original) as capture:
                    core.crop_sheet(self.native, [self.finding(box)], os.path.join(out, 'crops.png'))
                    np.testing.assert_array_equal(capture.call_args.args[0], expected)

    def test_invalid_empty_and_outside_boxes_have_labelled_placeholders(self):
        boxes = [(float('nan'), 1, 3, 4), (1, 1, float('inf'), 4), (8, 8, 2, 2),
                 (1, 1, 1, 4), (-2, 1, -1, 4), (40, 1, 41, 4), (1, 32, 4, 33)]
        for box in boxes:
            with self.subTest(box=box), tempfile.TemporaryDirectory() as out:
                with patch.object(core.Image, 'fromarray') as crop, patch.object(core.ImageDraw.ImageDraw, 'text') as text:
                    path = os.path.join(out, 'crops.png')
                    core.crop_sheet(self.native, [self.finding(box)], path)
                    crop.assert_not_called()
                    self.assertTrue(any('No crop:' in str(call) for call in text.call_args_list))
                    self.assertTrue(os.path.isfile(path))

    def test_extreme_finite_box_remains_bounded(self):
        with tempfile.TemporaryDirectory() as out:
            core.crop_sheet(self.native, [self.finding((-1e308, -1e308, 1e308, 1e308))],
                            os.path.join(out, 'crops.png'))


class RenderHarness(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.out = self.folder.name
        self.calls = []
        self.mode = 'ok'
        self.xv = Mock()
        self.enterContext(patch.dict(os.environ, {'DISPLAY': 'localhost:96.0', 'XAUTHORITY': '/caller/auth'}))
        self.godot = self.enterContext(patch.object(R, 'godot_bin', return_value='/fake/godot'))
        self.xvfb_fallback = R.start_xvfb
        self.display = self.enterContext(patch.object(R, 'start_xvfb', return_value=(self.xv, ':97')))
        self.process = self.enterContext(patch.object(R.subprocess, 'run', side_effect=self.engine))

    def engine(self, args, **kwargs):
        self.calls.append((args, kwargs))
        self.assertEqual(kwargs['env'].get('XAUTHORITY'), os.environ.get('XAUTHORITY'))
        self.assertEqual('XAUTHORITY' in kwargs['env'], 'XAUTHORITY' in os.environ)
        self.assertNotEqual(kwargs['env']['XDG_CONFIG_HOME'], os.environ.get('XDG_CONFIG_HOME'))
        self.assertNotEqual(kwargs['env']['XDG_DATA_HOME'], os.environ.get('XDG_DATA_HOME'))
        is_import = '--import' in args
        failed = self.mode.endswith('import') == is_import and self.mode != 'ok'
        if failed and self.mode.startswith('timeout'):
            raise subprocess.TimeoutExpired(args, 180, output=b'partial stdout', stderr=b'partial stderr')
        if failed and self.mode.startswith('oserror'):
            raise OSError('engine unavailable')
        shot = next((arg.removeprefix('--shot=') for arg in args if arg.startswith('--shot=')), None)
        if shot and self.mode not in ('missing-render', 'prior-render'):
            if self.mode == 'invalid-render':
                with open(shot, 'w') as handle:
                    handle.write('not a PNG')
            else:
                Image.new('RGB', (12, 8), (30, 60, 90)).save(shot)
            if self.mode == 'stale-render':
                os.utime(shot, (1, 1))
        return subprocess.CompletedProcess(args, 9 if failed and self.mode.startswith('exit') else 0,
                                           'stdout diagnostic\n', '  ERROR: render broken\n' if failed and
                                           self.mode.startswith('error') else 'stderr diagnostic\n')

    def render(self):
        return R.render('woodland', ['stones'], self.out, stage='homecoming', at='1,2', wait=1.5)

    def assert_user_cleanup(self):
        for _, kwargs in self.calls:
            for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME'):
                self.assertFalse(os.path.exists(os.path.dirname(kwargs['env'][key])))

    def test_external_display_and_auth_are_preserved_without_ownership(self):
        self.assertEqual(self.render(), [os.path.join(self.out, 'woodland_stones.png')])
        self.display.assert_not_called()
        self.xv.terminate.assert_not_called()
        self.assertTrue(all(kwargs['env']['DISPLAY'] == 'localhost:96.0' for _, kwargs in self.calls))
        args = self.calls[-1][0]
        for argument in ['--fresh', '--resolution', '1920x1080', '--stage=homecoming', '--at=1,2', '--wait=1.5']:
            self.assertIn(argument, args)
        self.assertEqual(os.environ['DISPLAY'], 'localhost:96.0')
        self.assertEqual(os.environ['XAUTHORITY'], '/caller/auth')
        self.assert_user_cleanup()

    def test_fallback_display_is_owned_and_reaped(self):
        with patch.dict(os.environ, {'DISPLAY': ''}):
            self.render()
        self.display.assert_called_once_with()
        self.assertTrue(all(kwargs['env']['DISPLAY'] == ':97' for _, kwargs in self.calls))
        self.xv.terminate.assert_called_once_with()
        self.xv.wait.assert_called_once()
        self.assert_user_cleanup()

    def test_borrowed_display_preserves_empty_and_absent_authority(self):
        for authority in ('', None):
            with self.subTest(authority=authority), patch.dict(os.environ):
                if authority is None:
                    os.environ.pop('XAUTHORITY', None)
                else:
                    os.environ['XAUTHORITY'] = authority
                self.render()
        self.display.assert_not_called()
        self.xv.terminate.assert_not_called()

    def test_failures_keep_diagnostics_and_never_return_evidence(self):
        for mode in ('exit-import', 'error-import', 'exit-render', 'error-render', 'missing-render',
                     'stale-render', 'invalid-render', 'timeout-import', 'timeout-render', 'oserror-render'):
            with self.subTest(mode=mode):
                self.mode = mode
                self.calls.clear()
                with self.assertRaisesRegex(RuntimeError, 'Godot|capture'):
                    self.render()
                self.assert_user_cleanup()
                self.xv.terminate.assert_not_called()
                if mode.endswith('import'):
                    self.assertEqual(len(self.calls), 1)
                logs = ''.join(Path(self.out, name).read_text() for name in os.listdir(self.out)
                               if name.endswith('.log'))
                self.assertIn('partial stdout' if mode.startswith('timeout') else 'diagnostic', logs)

    def test_prior_capture_is_removed_before_render_and_not_accepted(self):
        path = os.path.join(self.out, 'woodland_stones.png')
        Image.new('RGB', (12, 8)).save(path)
        self.mode = 'prior-render'
        with self.assertRaisesRegex(RuntimeError, 'capture'):
            self.render()
        self.assertFalse(os.path.exists(path))

    def test_owned_display_cleanup_on_render_exception(self):
        self.mode = 'timeout-render'
        with patch.dict(os.environ, {'DISPLAY': ''}), self.assertRaises(RuntimeError):
            self.render()
        self.xv.terminate.assert_called_once_with()
        self.xv.wait.assert_called_once()
        self.assert_user_cleanup()

    def test_setup_failure_does_not_allocate_or_leak_display(self):
        with patch.dict(os.environ, {'DISPLAY': ''}), \
                patch.object(R.tempfile, 'TemporaryDirectory', side_effect=OSError('temp unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'temp unavailable'):
                self.render()
        self.display.assert_not_called()
        self.process.assert_not_called()

    def test_engine_error_variants_fail_before_capture(self):
        for error in ('SCRIPT ERROR: bad', ' ERROR: bad', ' Parse Error: bad',
                      ' Failed loading resource: bad', ' Cannot open file: bad'):
            with self.subTest(error=error):
                self.process.side_effect = None
                self.process.return_value = subprocess.CompletedProcess([], 0, error, '')
                self.process.reset_mock()
                with self.assertRaisesRegex(RuntimeError, 'Godot'):
                    self.render()
                self.assertEqual(self.process.call_count, 1)

    def test_partial_multiple_spawns_never_return_success(self):
        def partial(args, **kwargs):
            self.mode = 'missing-render' if '--spawn=second' in args else 'ok'
            return self.engine(args, **kwargs)
        self.process.side_effect = partial
        with self.assertRaisesRegex(RuntimeError, 'capture'):
            R.render('woodland', ['stones', 'second'], self.out)
        self.assertTrue(os.path.isfile(os.path.join(self.out, 'woodland_stones.png')))
        self.assert_user_cleanup()

    def test_prior_success_report_is_invalidated_before_producer_failure(self):
        report = Path(self.out, 'report.json')
        report.write_text('{"counts":{"blocker":0,"fault":0,"polish":0}}')
        with patch.object(R.SN, 'load_zone', side_effect=ValueError('source unavailable')):
            with self.assertRaisesRegex(ValueError, 'source unavailable'):
                R.main(['woodland', '--out', self.out])
        self.assertFalse(report.exists())

    def test_registry_failure_replaces_prior_success_with_incomplete_report(self):
        subject = Path(self.out, 'subject')
        registry = subject / 'game' / 'data' / 'zones.json'
        registry.parent.mkdir(parents=True)
        output = Path(self.out, 'registry-report')
        output.mkdir()
        report = output / 'report.json'
        real_load = json.load
        for name, content in (('missing', None), ('malformed', '{invalid'), ('nonobject', '[]')):
            with self.subTest(registry=name):
                if registry.exists():
                    registry.unlink()
                if content is not None:
                    registry.write_text(content)
                report.write_text('{"complete":true,"counts":{"blocker":0,"fault":0,"polish":0}}')

                def load_current_registry(handle):
                    self.assertFalse(report.exists())
                    return real_load(handle)

                with patch.object(R, 'REPO', str(subject)), \
                        patch.object(R.json, 'load', side_effect=load_current_registry) as load:
                    self.assertEqual(R.main(['woodland', '--out', str(output)]), 1)
                self.assertEqual(load.call_count, 0 if content is None else 1)
                current = json.loads(report.read_text())
                self.assertFalse(current['complete'])
                self.assertFalse(current['scene']['complete'])
                self.assertIn('cannot read zone registry', current['scene']['error'])
                self.assertEqual(current['pictures'], [])
                self.assertNotIn('counts', current)
                self.process.assert_not_called()
                self.godot.assert_not_called()

    def test_cli_keeps_findings_but_reports_incomplete_on_render_failure(self):
        finding = core.Finding('test.scene', 'fault', (1, 1, 3, 3), 'fault remains', 'fix')
        zone = SimpleNamespace(size=(8, 8), sprites=[], spawns={'stones': (1, 1)}, doors=[])
        picture = dict(picture='woodland_zone', findings=[finding.to_json()], grid=[])
        self.mode = 'exit-import'
        with patch.object(R.SN, 'load_zone', return_value=zone), \
                patch.object(R.SN, 'review_zone', return_value={'findings': [finding]}), \
                patch.object(R.SN, 'composite', return_value=np.zeros((8, 8, 3), np.uint8)), \
                patch.object(R, 'review_picture', return_value=picture):
            self.assertEqual(R.main(['woodland', '--out', self.out]), 2)
        with open(os.path.join(self.out, 'report.json')) as handle:
            report = json.load(handle)
        self.assertTrue(report['incomplete'])
        self.assertTrue(report['errors'])
        self.assertEqual(report['scene']['findings'], [finding.to_json()])
        self.assertEqual(report['counts']['fault'], 2)

    def test_exhausted_fallback_writes_incomplete_cli_report_and_keeps_findings(self):
        finding = core.Finding('test.scene', 'fault', (1, 1, 3, 3), 'fault remains', 'fix')
        zone = SimpleNamespace(size=(8, 8), sprites=[], spawns={'stones': (1, 1)}, doors=[])
        picture = dict(picture='woodland_zone', findings=[finding.to_json()], grid=[])
        exists = os.path.exists
        temporary = tempfile.TemporaryDirectory
        user_folders = []
        def disposable(**kwargs):
            folder = temporary(**kwargs)
            user_folders.append(folder.name)
            return folder
        self.display.side_effect = self.xvfb_fallback
        with patch.dict(os.environ, {'DISPLAY': ''}), \
                patch.object(R.os.path, 'exists', side_effect=lambda p: str(p).startswith('/tmp/.X11-unix/X') or exists(p)), \
                patch.object(R.subprocess, 'Popen') as xvfb, \
                patch.object(R.tempfile, 'TemporaryDirectory', side_effect=disposable), \
                patch.object(R.SN, 'load_zone', return_value=zone), \
                patch.object(R.SN, 'review_zone', return_value={'findings': [finding]}), \
                patch.object(R.SN, 'composite', return_value=np.zeros((8, 8, 3), np.uint8)), \
                patch.object(R, 'review_picture', return_value=picture):
            self.assertEqual(R.main(['woodland', '--out', self.out]), 2)
        xvfb.assert_not_called()
        self.process.assert_not_called()
        self.xv.terminate.assert_not_called()
        self.assertTrue(user_folders)
        self.assertTrue(all(not exists(path) for path in user_folders))
        report = json.loads(Path(self.out, 'report.json').read_text())
        self.assertTrue(report['incomplete'])
        self.assertIn('no free X display', report['errors'][0])
        self.assertEqual(report['scene']['findings'], [finding.to_json()])
        self.assertEqual(report['pictures'], [picture])
        self.assertEqual(report['counts']['fault'], 2)


class GodotAcquisition(unittest.TestCase):
    def test_failed_empty_and_missing_engine_results_are_explicit(self):
        with patch.dict(os.environ, {'GODOT': ''}), patch.object(R.subprocess, 'run') as command:
            for result in (subprocess.CompletedProcess([], 1, '', 'download failed'),
                           subprocess.CompletedProcess([], 0, '', ''),
                           subprocess.CompletedProcess([], 0, '/missing/godot\n', '')):
                with self.subTest(result=result):
                    command.return_value = result
                    with self.assertRaisesRegex(RuntimeError, 'Godot'):
                        R.godot_bin()
        with patch.dict(os.environ, {'GODOT': '/missing/godot'}), patch.object(R.subprocess, 'run') as command:
            with self.assertRaisesRegex(RuntimeError, 'Godot'):
                R.godot_bin()
            command.assert_not_called()


# the Undercroft's craft guards (8 Nov audit): run with check:review
from .test_undercroft_craft import SpeckScatter, StagedBoundaries, RealFloorTint, SceneUnmoved, PoolsAndShade, ChannelSpill, LightColourAndDrawing, OverlayLoneSplit  # noqa: E402,F401


if __name__ == '__main__':
    unittest.main()


class Composition(unittest.TestCase):
    """logic.composition (Matt, 26 Oct 19:35: "the square needs better centring with the objects on
    top of it")."""

    def square(self, well_x=240, bench2=True, x1=384):
        props = [dict(kind='well', x=well_x, y=170, w=54), dict(kind='bench', x=132, y=110, w=66)]
        if bench2:
            props.append(dict(kind='bench', x=348, y=110, w=66))
        return dict(id='square', rect=[96, 48, x1, 264], props=props, entries=[dict(x=240, w=72)])

    def test_composed_square_passes(self):
        from scripts.review import composition as CP
        self.assertEqual(CP.check([self.square()]), [])

    def test_off_centre_well_trips(self):
        from scripts.review import composition as CP
        fs = CP.check([self.square(well_x=252)])
        self.assertTrue(any('centrepiece' in f.message for f in fs))

    def test_lone_bench_trips(self):
        from scripts.review import composition as CP
        fs = CP.check([self.square(bench2=False)])
        self.assertTrue(any('twin' in f.message for f in fs))

    def test_uneven_margins_trip(self):
        from scripts.review import composition as CP
        fs = CP.check([self.square(x1=432)])
        self.assertTrue(any('margins' in f.message or 'centrepiece' in f.message for f in fs))


class Tiers(unittest.TestCase):
    """logic.tiers (Matt, 26 Oct 19:42: "make sure the logic is correct")."""

    def plan(self, face=48, y_top=120, y_foot=168, x0=120, x1=192, below=0):
        return dict(density=3, cell=8, tiers=[dict(id='plateau', level=16, below=below, face_px=face,
                                                   rects=[[0, 0, 160, 40], [104, 40, 40, 16]])],
                    stairs=[dict(tier='plateau', x0=x0, x1=x1, y_top=y_top, y_foot=y_foot)])

    def test_consistent_plan_passes(self):
        from scripts.review import tiers as TI
        self.assertEqual(TI.check(self.plan()), [])

    def test_face_of_another_height_trips(self):
        from scripts.review import tiers as TI
        self.assertTrue(TI.check(self.plan(face=36)))

    def test_stair_head_off_the_rim_trips(self):
        from scripts.review import tiers as TI
        self.assertTrue(any('head' in f.message for f in TI.check(self.plan(y_top=100, y_foot=148))))

    def test_stair_across_a_turn_trips(self):
        from scripts.review import tiers as TI
        self.assertTrue(any('straddles' in f.message for f in TI.check(self.plan(x0=288, x1=336))))


class GroundRules(unittest.TestCase):
    """docs/vision/ground-rules.md: each rule has a plan that passes and one that trips it."""

    def plan(self):
        return {
            'screen': {'w': 320, 'h': 320},
            'stands': {'glade': [160, 40]},
            'places': {'bridge': {'x0': 152, 'w': 16, 'y0': 184, 'y1': 216}},
            'paths': [{'points': [[160, 320], [160, 40]], 'radius': 8}],
            'water': {'fall': {'x0': 72, 'w': 16, 'y0': 96, 'y1': 136, 'face': [60, 96, 100, 132]},
                      'soft': {'river': {'points': [[80, 200], [336, 200]], 'cells': 3},
                               'pool': [[56, 128, 48, 80]],
                               'rill': {'points': [[80, -8], [80, 96]], 'cells_plan': 2}}},
            'rock': {'heap': [{'at': [50, 120], 'size': [16, 12]}, {'at': [110, 120], 'size': [16, 12]}]},
            'objects': [['bench', 'forest_bench', 112, 157, 32, 11]],
            'dressing': {'ferns': [[200, 100, 1, 1.0]]},
        }

    def names(self, p):
        from scripts.review import ground_rules as GR
        return {f['check'] for f in GR.check_plan(p)}

    def test_good_plan_passes(self):
        self.assertEqual(self.names(self.plan()), set())

    def test_fall_off_centre_and_not_flush(self):
        p = self.plan()
        p['water']['fall']['x0'] = 76
        p['water']['soft']['rill']['points'][-1] = [80, 104]
        self.assertIn('rules.water_fall', self.names(p))

    def test_dead_end_water(self):
        p = self.plan()
        p['water']['soft']['river']['points'] = [[80, 200], [240, 200]]
        self.assertIn('rules.water_end', self.names(p))

    def test_slanting_path_and_stair_steps(self):
        p = self.plan()
        p['paths'][0]['points'] = [[160, 320], [160, 240], [168, 240], [168, 40]]
        self.assertIn('rules.route_grid', self.names(p))
        p['paths'][0]['points'] = [[160, 320], [176, 40]]
        self.assertIn('rules.route_grid', self.names(p))

    def test_path_under_water_off_the_bridge(self):
        p = self.plan()
        p['places']['bridge']['x0'] = 200
        self.assertIn('rules.ground_water', self.names(p))

    def test_bench_on_the_path(self):
        p = self.plan()
        p['objects'][0] = ['bench', 'forest_bench', 144, 157, 32, 11]
        n = self.names(p)
        self.assertIn('rules.route_clear', n)
        self.assertIn('rules.seating', n)

    def test_rocks_overlapping(self):
        p = self.plan()
        p['rock']['heap'][1]['at'] = [58, 124]
        self.assertIn('rules.rock_overlap', self.names(p))
        p['rock']['heap'][1]['stacked'] = True
        self.assertNotIn('rules.rock_overlap', self.names(p))

    # Matt, 13 Nov: the lantern's plinth stood on the well's ring of setts, under its crank
    def square(self, lantern, extra=()):
        plan = {'places': [{'id': 'square', 'kind': 'square', 'rect': [200, 200, 240, 176]}],
                'art': {'paving': [[200, 200, 240, 176]], 'setts': [[288, 316, 14, 23]],
                        'dressing': [{'kind': 'barrel', 'at': [360, 256], 'with': 'stall'}]}}
        kit = {'objects': [
            {'id': 'well_choked', 'kind': 'well_choked', 'solid': [278, 304, 20, 16], 'cond': {'not_flags': ['home']}},
            {'id': 'well', 'kind': 'well', 'solid': [278, 304, 20, 16], 'cond': {'flags': ['home']}},
            {'id': 'lantern_dark', 'kind': 'lantern', 'solid': lantern, 'cond': {'not_flags': ['home']}},
            {'id': 'lantern_lit', 'kind': 'lantern_lit', 'solid': lantern, 'cond': {'flags': ['home']}},
            {'id': 'stall', 'kind': 'stall', 'solid': [366, 240, 36, 16], 'cond': None},
            {'id': 'barrel_0', 'kind': 'barrel', 'solid': [355, 248, 10, 8], 'cond': None},
            {'id': 'bakery', 'kind': 'building', 'solid': [112, 240, 72, 48], 'cond': None},
            *extra]}
        return kit, plan

    def clearance(self, lantern, extra=()):
        from scripts.review import ground_rules as GR
        kit, plan = self.square(lantern, extra)
        return [(f['check'], f['message']) for f in GR.prop_clearance(kit, plan)]

    def test_the_lantern_on_the_wells_apron_trips(self):
        # as Matt saw it: the plinth (305 to 319, 307 to 312) on the ring's east edge (x 311)
        found = self.clearance([305, 307, 14, 5])
        on = [m for c, m in found if c == 'rules.prop_apron']
        self.assertTrue(on and all('stands on the apron of well' in m for m in on), found)
        # each state of the lantern against the ring, never the dark lantern against the lit one
        self.assertEqual(len(on), 2)
        # and 7 px from the well's drum, where no body passes: the dark lantern by the choked well, the lit by the clear
        self.assertEqual(len([m for c, m in found if c == 'rules.prop_gap']), 2)
        self.assertFalse(any('lantern_dark and lantern_lit' in m for _, m in found))

    def test_the_lantern_clear_of_the_well_passes(self):
        self.assertEqual(self.clearance([344, 314, 16, 6]), [])

    def test_a_plinth_just_off_the_apron_is_still_too_near(self):
        # 3 px east of the ring's edge (x 311): nobody walks between them
        found = self.clearance([314, 312, 16, 6])
        self.assertTrue(any(c == 'rules.prop_apron' and 'px from the apron' in m for c, m in found), found)

    def test_two_props_sharing_ground_trip(self):
        found = self.clearance([344, 314, 16, 6], [{'id': 'crate', 'kind': 'crates', 'solid': [356, 316, 12, 10], 'cond': None}])
        self.assertIn('rules.prop_overlap', {c for c, _ in found})

    def test_a_gap_no_body_fits_on_open_ground_trips_but_not_against_a_wall_or_with_its_stall(self):
        # 4 px between two free-standing props in the square
        found = self.clearance([344, 314, 16, 6], [{'id': 'crate', 'kind': 'crates', 'solid': [364, 314, 12, 10], 'cond': None}])
        self.assertIn('rules.prop_gap', {c for c, _ in found})
        # the stall's own barrel stands 1 px from it by the plan's `with`: a group, not a gap
        self.assertFalse(any('barrel_0' in m for _, m in found), found)
        # clutter against a wall (within a body of the bakery) is not free-standing
        found = self.clearance([344, 314, 16, 6], [
            {'id': 'tub_a', 'kind': 'flower_tub', 'solid': [186, 250, 10, 8], 'cond': None},
            {'id': 'tub_b', 'kind': 'flower_tub', 'solid': [186, 262, 10, 8], 'cond': None}])
        self.assertEqual(found, [])

    def test_nothing_stands_in_front_of_a_door(self):
        from scripts.review import ground_rules as GR
        kit, plan = self.square([344, 314, 16, 6], [{'id': 'notice_board', 'kind': 'notice_board', 'solid': [225.5, 220, 21, 4], 'offset': [-48, -126], 'cond': None}])
        plan['buildings'] = [{'id': 'library', 'rect': [200, 160, 96, 40], 'door': [248, 200]}]
        kit['objects'].append({'id': 'library', 'kind': 'building', 'solid': [200, 160, 96, 40], 'cond': None})
        # as it stood: the board's foot 20 px out from the door, the board 42 px tall, so it hid the door
        found = [(f['check'], f['message']) for f in GR.prop_clearance(kit, plan)]
        self.assertTrue(any(c == 'rules.prop_door' and 'notice_board' in m and 'library' in m for c, m in found), found)
        # west of the door, it passes
        kit['objects'][-2]['solid'] = [205.5, 228, 21, 4]
        self.assertEqual([c for c, _ in ((f['check'], f['message']) for f in GR.prop_clearance(kit, plan)) if c == 'rules.prop_door'], [])
        # the rubble a restore clears lies at its door by the story
        kit['objects'].append({'id': 'fern_rubble', 'kind': 'rubble', 'solid': [240, 202, 30, 14], 'cond': {'not_restored': ['fern_cottage']}})
        self.assertEqual([f['check'] for f in GR.prop_clearance(kit, plan) if f['check'] == 'rules.prop_door'], [])

    def test_states_that_never_meet_are_not_compared(self):
        from scripts.review import ground_rules as GR
        self.assertFalse(GR._coexist({'flags': ['home']}, {'not_flags': ['home']}))
        self.assertFalse(GR._coexist({'not_restored': ['forge']}, {'restored': ['forge']}))
        self.assertTrue(GR._coexist({'flags': ['home']}, None))
        self.assertTrue(GR._coexist({'flags': ['home']}, {'restored': ['forge']}))

    def test_crossroads_holds_the_clearance(self):
        from scripts.review import ground_rules as GR
        root = GR.ROOT
        plan = json.load(open(os.path.join(root, 'game', 'data', 'plans', 'crossroads.json')))
        kit = json.load(open(os.path.join(root, 'game', 'zones', 'crossroads', 'kit.json')))
        self.assertTrue(plan.get('prop_clearance'), 'Crossroads holds rules.prop_* (ground_rules --check)')
        self.assertEqual(GR.prop_clearance(kit, plan, GR.scene_boxes('crossroads', plan, kit)), [])
        # the well and the shard lantern each stand on a ring of their own
        self.assertEqual(len(plan['art']['setts']), 2)

    def test_route_to_nowhere_and_clutter_on_route(self):
        p = self.plan()
        p['paths'].append({'points': [[160, 240], [240, 240]], 'radius': 8})
        p['dressing']['ferns'].append([160, 260, 2, 1.0])
        n = self.names(p)
        self.assertIn('rules.route_ends', n)
        self.assertIn('rules.clutter', n)


class ClusterNoise(unittest.TestCase):
    """detail.cluster_noise (cluster_noise.py): random value grain in 2 x 2 clusters, against a calm
    form lit across its face (the detail audit of the Act 1 props, 4 Nov, finding 4)."""

    def test_calm_form_passes_and_terrazzo_trips(self):
        from scripts.review import cluster_noise as CN
        s = sprite(64, 64)
        s[4:60, 4:60, 3] = 255
        x = np.arange(64)[None, :] + np.zeros((64, 1))
        base = (190 - 1.6 * x).astype(np.uint8)                     # lit west, shaded east, in steps
        s[..., 0] = s[..., 1] = s[..., 2] = (base // 12) * 12
        self.assertLess(CN.share(s[..., :3], s[..., 3] > 0)[0], CN.CALM)
        self.assertEqual(CN.check(s[..., :3], s[..., 3] > 0, H, 'x/slab'), [])
        rng = np.random.default_rng(1)
        g = rng.random((32, 32))
        step = np.where(g > 0.72, 24, np.where(g < 0.28, -24, 0)).repeat(2, 0).repeat(2, 1)   # 56 % of cells step
        n = np.clip(s[..., :3].astype(int) + step[..., None], 0, 255).astype(np.uint8)
        s[..., :3] = n
        f = CN.check(s[..., :3], s[..., 3] > 0, H, 'x/slab')
        self.assertTrue(f and f[0].detector == 'detail.cluster_noise' and f[0].severity == 'fault')

    def test_the_grid_phase_spread_is_reported(self):
        """Round 7 of the Act 1 detail audit (R7-6), a documented instability: the verdict is on the grid
        at the picture's corner, so the same pixels one texel over can score differently (the v7 bitt
        48.9 to 59.5 %). The finding reports the four phases' spread, for information; it does not
        average them (Claude A's ruling: averaging diluted the terrazzo above into polish)."""
        from scripts.review import cluster_noise as CN
        im = _png(os.path.join(os.path.dirname(FIX_V3), 'act1_v7', 'coast_mooring_bitt.png'))
        ph = CN.phases(im[..., :3], im[..., 3] > 128)
        self.assertEqual(len(ph), 4)
        self.assertAlmostEqual(ph[0], CN.share(im[..., :3], im[..., 3] > 128)[0], places=9)
        self.assertGreater(max(ph) - min(ph), 0.05)                    # the instability, documented
        shifted = np.pad(im, ((0, 0), (1, 0), (0, 0)))
        self.assertAlmostEqual(CN.phases(shifted[..., :3], shifted[..., 3] > 128)[1], ph[0], places=9)
        for sub in (im, shifted):
            f = CN.check(sub[..., :3], sub[..., 3] > 128, H, 'x/bitt')
            self.assertTrue(f)
            self.assertEqual(len(f[0].extra['phases']), 4)
            self.assertIn('four phases give', f[0].message)
            self.assertAlmostEqual(f[0].score, CN.share(sub[..., :3], sub[..., 3] > 128)[0], places=9)

    def test_the_outline_is_not_material(self):
        from scripts.review import cluster_noise as CN
        s = sprite(40, 40)
        s[4:36, 4:36] = (150, 150, 150, 255)
        s[4, 4:36] = s[35, 4:36] = (20, 20, 20, 255)
        s[4:36, 4] = s[4:36, 35] = (20, 20, 20, 255)
        self.assertLess(CN.share(s[..., :3], s[..., 3] > 0)[0], 0.05)          # only where a corner's outline outvotes the fill


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIX_V3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'act1_v3')


def _png(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert('RGBA'))


class FlatCylinder(unittest.TestCase):
    """detail.flat_cylinder (flat_cylinder.py): a log or pipe painted as a strip, a flat lit band that
    drops hard into its shadow (the detail audit of the Act 1 props, round 2, R2-1: the v3 birch)."""

    def test_the_v3_birch_trips_and_a_shaded_cylinder_passes(self):
        from scripts.review import flat_cylinder as FC
        a = _png(os.path.join(FIX_V3, 'mill_landslip.png'))
        f = FC.check(a[..., :3], a[..., 3] > 128, H, 'act1/mill_landslip')
        self.assertTrue(f and f[0].detector == 'detail.flat_cylinder' and f[0].severity == 'fault')
        s = sprite(80, 30)
        s[8:20, 5:75, 3] = 255
        ramp = [243, 233, 233, 212, 212, 188, 143, 143, 118, 88, 70, 59]     # five steps, no hard drop
        for j, v in enumerate(ramp):
            s[8 + j, 5:75, :3] = v
        self.assertEqual(FC.check(s[..., :3], s[..., 3] > 0, H, 'x/log'), [])
        flat = [243, 233, 233, 233, 211, 211, 211, 87, 87, 57, 57, 57]           # the v3 profile
        for j, v in enumerate(flat):
            s[8 + j, 5:75, :3] = v
        self.assertTrue(FC.check(s[..., :3], s[..., 3] > 0, H, 'x/log'))

    def test_character_sheets_are_not_measured(self):
        """Props and scenery only: the v3 birch's strip under a character subject gives nothing."""
        from scripts.review import flat_cylinder as FC
        a = _png(os.path.join(FIX_V3, 'mill_landslip.png'))
        self.assertEqual(FC.check(a[..., :3], a[..., 3] > 128, H, 'characters/fidget_knuckles_N'), [])

    def test_the_current_birch_passes(self):
        from scripts.review import flat_cylinder as FC
        p = os.path.join(REPO_ROOT, 'game', 'kit', 'props', 'art', 'act1', 'mill_landslip.png')
        a = _png(p)
        self.assertEqual(FC.check(a[..., :3], a[..., 3] > 128, H, 'act1/mill_landslip'), [])


class CheckerDither(unittest.TestCase):
    """detail.dither (checker_dither.py): a 1-texel checker on a sprite (the detail audit of the Act 1
    props, round 2, R2-6: the v3 net rack's foot)."""

    def test_the_v3_net_trips_and_a_mesh_of_diamonds_passes(self):
        from scripts.review import checker_dither as CD
        f = CD.check(_png(os.path.join(FIX_V3, 'coast_net_rack.png')), H, 'act1/coast_net_rack')
        self.assertTrue(f and f[0].detector == 'detail.dither')
        s = sprite(40, 40)
        y, x = np.mgrid[0:40, 0:40]
        line = (((x + y) % 4) == 0) | (((x - y) % 4) == 0)                       # twine in diamonds, holes between
        s[line] = (60, 120, 60, 255)
        self.assertEqual(CD.check(s, H, 'x/net'), [])
        chk = ((x + y) % 2 == 0) & (x > 10) & (x < 26) & (y > 10) & (y < 26)
        s[(x > 10) & (x < 26) & (y > 10) & (y < 26)] = (90, 90, 90, 255)
        s[chk] = (140, 140, 140, 255)
        self.assertTrue(CD.check(s, H, 'x/patch'))

    def test_a_small_checker_patch_trips_and_a_smaller_one_passes(self):
        """The second fixture: a stone whose shade is a 3 x 5 texel checker (8 windows, under the
        old threshold of 9) trips; the same patch cut to 3 x 4 (6 windows, the highest clean sprite
        in the repo sweep) passes."""
        from scripts.review import checker_dither as CD
        im = _png(os.path.join(os.path.dirname(FIX_V3), 'dither', 'stone_small_checker.png'))
        f = CD.check(im, H, 'x/stone')
        self.assertTrue(f and f[0].detector == 'detail.dither' and f[0].score == 8.0)
        cut = im.copy()
        cut[11:14, 15] = cut[11:14, 16]
        self.assertEqual(CD.check(cut, H, 'x/stone'), [])

    def test_the_current_net_passes(self):
        from scripts.review import checker_dither as CD
        p = os.path.join(REPO_ROOT, 'game', 'kit', 'props', 'art', 'act1', 'coast_net_rack.png')
        self.assertEqual(CD.check(_png(p), H, 'act1/coast_net_rack'), [])


# ------------------------------------------------------------------------------------------
# Matt's 12 Nov Frostline misses (forms.py, kit_overlap.py; calibration F1 to F13)
SNOW = (236, 238, 242)
LEAF = (60, 120, 50)


def _crown(w=110, h=200):
    a = np.zeros((h, w, 4), np.uint8)
    a[..., :3] = LEAF
    a[..., 3] = 255
    rng = np.random.default_rng(3)
    a[..., 1] = np.clip(a[..., 1].astype(int) + rng.integers(-10, 10, (h, w)), 0, 255)
    return a


def _chips(a, shape_of):
    """Twenty snow chips laid on the crown on a loose grid."""
    k = 0
    for y in range(10, a.shape[0] - 12, 36):
        for x in range(8, a.shape[1] - 12, 24):
            m = shape_of(k)
            hh, ww = m.shape
            a[y:y + hh, x:x + ww, :3][m] = SNOW
            k += 1
    return a


def _wedge(k):
    w = np.array([6, 5, 3, 2])
    return np.array([[c < w[r] for c in range(6)] for r in range(4)])


def _clump(k):
    # an irregular load: a bump in the middle row, a ragged underside, different from chip to chip
    m = np.zeros((4, 6), bool)
    m[0, 1:4 + k % 2] = True
    m[1, 0:6] = True
    m[2, 1 + k % 3:5] = True
    m[3, 2:4] = True
    return m


class Forms(unittest.TestCase):
    def test_stamped_snow_chips_trip(self):
        from scripts.review import forms as F
        a = _chips(_crown(), _wedge)
        fs = F.snow_stamp(a[..., :3], a[..., 3] > 0, H, 'kit/frost_pine')
        self.assertEqual([f.detector for f in fs], ['detail.snow_stamp'])

    def test_varied_snow_loads_pass(self):
        from scripts.review import forms as F
        a = _chips(_crown(), _clump)
        self.assertEqual(F.snow_stamp(a[..., :3], a[..., 3] > 0, H, 'kit/frost_pine'), [])

    def test_stamped_chips_on_a_screen_trip(self):
        from scripts.review import forms as F
        s = np.zeros((300, 260, 4), np.uint8)
        s[..., :3] = SNOW
        s[..., 3] = 255
        s[40:240, 60:170] = _chips(_crown(), _wedge)
        fs = F.snow_stamp_screen(s, H, np.zeros(s.shape[:2], bool))
        self.assertEqual([f.detector for f in fs], ['detail.snow_stamp'])

    def _tree(self, h):
        a = np.zeros((h + 30, 90, 4), np.uint8)
        a[:h, :, :3] = LEAF
        a[:h, :, 3] = 255
        a[h:, 38:52, :3] = (110, 70, 40)
        a[h:, 38:52, 3] = 255
        return a

    def test_a_pole_of_a_tree_trips(self):
        from scripts.review import forms as F
        a = self._tree(240)                       # 270 tall, 90 wide: 3.0
        fs = F.tree_pole(a[..., :3], a[..., 3] > 0, H, 'kit/frost_spruce')
        self.assertEqual([f.detector for f in fs], ['logic.tree_pole'])

    def test_an_approved_proportion_passes(self):
        from scripts.review import forms as F
        a = self._tree(180)                       # 210 tall, 90 wide: 2.33, as the approved birch
        self.assertEqual(F.tree_pole(a[..., :3], a[..., 3] > 0, H, 'kit/frost_spruce'), [])
        b = self._tree(240)
        self.assertEqual(F.tree_pole(b[..., :3], b[..., 3] > 0, H, 'kit/frost_snow_pole'), [],
                         'only trees are judged')

    def _deck(self, upright):
        a = np.zeros((60, 120, 4), np.uint8)
        a[..., :3] = (150, 100, 60)
        a[..., 3] = 255
        if upright:
            a[:, ::7, :3] = (70, 45, 25)          # boards standing the full face
        else:
            a[::6, :, :3] = (70, 45, 25)          # boards across the walk, a top plane
        return a

    def test_a_deck_drawn_front_on_trips(self):
        from scripts.review import forms as F
        a = self._deck(True)
        fs = F.deck_upright(a[..., :3], a[..., 3] > 0, H, 'kit/frost_footbridge')
        self.assertEqual([f.detector for f in fs], ['logic.deck_upright'])

    def test_a_deck_seen_from_above_passes(self):
        from scripts.review import forms as F
        a = self._deck(False)
        self.assertEqual(F.deck_upright(a[..., :3], a[..., 3] > 0, H, 'kit/frost_footbridge'), [])
        b = self._deck(True)
        self.assertEqual(F.deck_upright(b[..., :3], b[..., 3] > 0, H, 'crossroads/fence_0'), [],
                         'only bridges and decks are judged')

    def test_a_brick_grid_rock_face_trips(self):
        from scripts.review import forms as F
        a = np.zeros((114, 144, 4), np.uint8)
        a[..., :3] = (120, 122, 130)
        a[..., 3] = 255
        for r, y in enumerate(range(0, 114, 14)):
            a[y:y + 2, :, :3] = 30
            for x in range((r % 2) * 12, 144, 24):
                a[y:y + 14, x:x + 2, :3] = 30
        fs = F.masonry_rock(a[..., :3], a[..., 3] > 0, H, 'kit/frost_rockface_plain')
        self.assertIn('detail.masonry_rock', [f.detector for f in fs])
        self.assertEqual(F.masonry_rock(a[..., :3], a[..., 3] > 0, H, 'brackens/wall_drystone_ew_a'), [],
                         'worked stone may be coursed')

    def test_pillow_stones_trip(self):
        from scripts.review import forms as F
        a = np.zeros((114, 144, 4), np.uint8)
        a[..., :3] = 40
        a[..., 3] = 255
        yy, xx = np.mgrid[0:114, 0:144]
        for cy in range(10, 114, 22):
            for cx in range(12, 144, 24):
                d = ((yy - cy) / 10.0) ** 2 + ((xx - cx) / 11.0) ** 2
                lit = np.clip(170 - 40 * ((yy - cy + 4) ** 2 + (xx - cx + 4) ** 2) / 120.0, 90, 170)
                a[..., :3][d < 1] = lit[d < 1, None].astype(np.uint8)
        fs = F.masonry_rock(a[..., :3], a[..., 3] > 0, H, 'kit/frost_rockface_plain')
        self.assertIn('detail.masonry_rock', [f.detector for f in fs])

    def test_irregular_rock_passes(self):
        from scripts.review import forms as F
        rng = np.random.default_rng(5)
        field = ndi.gaussian_filter(rng.normal(0, 1, (114, 144)), 9)
        field = (field - field.min()) / (field.max() - field.min())
        a = np.zeros((114, 144, 4), np.uint8)
        a[..., :3] = (70 + 100 * field)[..., None].astype(np.uint8)
        a[..., 3] = 255
        self.assertEqual(F.masonry_rock(a[..., :3], a[..., 3] > 0, H, 'kit/frost_crag_a'), [])

    def _stair(self, tread, riser, steps=7, bond=False):
        T = tread + riser
        a = np.zeros((T * steps, 120, 4), np.uint8)
        a[..., 3] = 255
        for k in range(steps):
            y = k * T
            a[y:y + tread, :, :3] = 170
            a[y + tread:y + T, :, :3] = 60
            if bond:
                for x in range(20 + (k % 2) * 20, 110, 40):
                    a[y:y + T, x:x + 1, :3] = 20
        return a

    def test_a_ladder_of_strips_trips(self):
        from scripts.review import forms as F
        a = self._stair(13, 3)
        fs = F.stair_read(a[..., :3], a[..., 3] > 0, H, 'kit/frost_rock_stair')
        self.assertEqual([f.detector for f in fs], ['detail.stair_read'])
        self.assertIn('ladder', fs[0].message)

    def test_a_brick_bond_stair_trips(self):
        from scripts.review import forms as F
        a = self._stair(9, 7, bond=True)
        fs = F.stair_read(a[..., :3], a[..., 3] > 0, H, 'kit/frost_rock_stair')
        self.assertEqual(['wall' in f.message for f in fs], [True])

    def test_treads_and_risers_pass(self):
        from scripts.review import forms as F
        a = self._stair(9, 7)                     # Eastward's stairs: risers 43 to 53 % of the pitch
        self.assertEqual(F.stair_read(a[..., :3], a[..., 3] > 0, H, 'kit/frost_rock_stair'), [])

    def test_a_rectangular_fall_trips(self):
        from scripts.review import forms as F
        al = np.ones((111, 96), bool)
        self.assertEqual([f.detector for f in F.fall_slab(al, H, 'kit/frost_icefall')], ['detail.fall_slab'])

    def test_a_fall_over_a_lip_passes(self):
        from scripts.review import forms as F
        al = np.zeros((111, 96), bool)
        for y in range(111):
            w = 30 + int(12 * np.sin(y / 9.0)) + y // 6
            al[y, 48 - w // 2 - (y % 7 == 0):48 + w // 2] = True
        self.assertEqual(F.fall_slab(al, H, 'kit/frost_icefall'), [])

    def _winter(self, ice_rows=None, rim=0):
        s = np.zeros((300, 300, 4), np.uint8)
        s[..., :3] = SNOW
        s[..., 3] = 255
        s[:, 100:180, :3] = (63, 99, 149)         # open water
        if ice_rows:
            s[ice_rows, 100:180, :3] = (150, 180, 215)
        if rim:
            s[:, 100:100 + rim, :3] = (150, 180, 215)
            s[:, 180 - rim:180, :3] = (150, 180, 215)
        return s

    def test_a_frozen_section_beside_open_water_trips(self):
        from scripts.review import forms as F
        s = self._winter(ice_rows=slice(0, 130))
        fs = F.water_state(s, H, np.zeros(s.shape[:2], bool))
        self.assertEqual([f.detector for f in fs], ['logic.water_state'])

    def test_open_water_with_shore_ice_passes(self):
        from scripts.review import forms as F
        s = self._winter(rim=12)
        self.assertEqual(F.water_state(s, H, np.zeros(s.shape[:2], bool)), [])
        s2 = self._winter(ice_rows=slice(0, 130))
        s2[..., :3] = np.where((s2[..., :3] == SNOW).all(-1)[..., None], np.array(GRASS, np.uint8), s2[..., :3])
        self.assertEqual(F.water_state(s2, H, np.zeros(s2.shape[:2], bool)), [], 'judged in winter scenes only')


class KitOverlap(unittest.TestCase):
    def _items(self, dx):
        hut = np.ones((120, 200), bool)
        tree = np.ones((240, 80), bool)
        return [('col_hut', 'house', 0, 0, hut), ('spruce', 'tree', dx, -100, tree), ('pine', 'tree', dx + 40, -90, tree)]

    def test_a_tree_over_the_house_trips(self):
        from scripts.review import kit_overlap as K
        with patch.object(K, 'layout', return_value=self._items(150)):
            fs = K.check('frostline')
        self.assertEqual(sorted((f.detector, f.severity) for f in fs),
                         [('logic.tree_overlap', 'fault'), ('logic.tree_overlap', 'fault'), ('logic.tree_overlap', 'polish')])

    def test_trees_clear_of_the_house_pass(self):
        from scripts.review import kit_overlap as K
        with patch.object(K, 'layout', return_value=self._items(240)):
            fs = K.check('frostline')
        self.assertEqual([f.severity for f in fs], ['polish'], 'two crowns overlapping is advice only')


class FormsThroughTheGate(unittest.TestCase):
    """#481 audit B1: a picture trimmed to its opaque box (alpha > 0.97) takes the ground branch of
    assets.review_rgba; the name-keyed form checks must still judge it."""

    def _dets(self, rgba, subject):
        fs, _ = A.review_rgba(rgba, subject, '', 'woodland')
        return [f.detector for f in fs if f.severity in ('fault', 'blocker')]

    def test_a_fully_opaque_rectangular_icefall_trips(self):
        a = np.zeros((111, 96, 4), np.uint8)
        a[..., :3] = (210, 228, 240)
        a[:, ::9, :3] = (150, 180, 215)
        a[..., 3] = 255
        self.assertIn('detail.fall_slab', self._dets(a, 'kit/frost_icefall'))

    def test_a_fully_opaque_brick_grid_rock_face_trips(self):
        a = np.zeros((114, 144, 4), np.uint8)
        a[..., :3] = (120, 122, 130)
        a[..., 3] = 255
        for r, y in enumerate(range(0, 114, 14)):
            a[y:y + 2, :, :3] = 30
            for x in range((r % 2) * 12, 144, 24):
                a[y:y + 14, x:x + 2, :3] = 30
        self.assertIn('detail.masonry_rock', self._dets(a, 'kit/x_rockface'))

    def test_a_fully_opaque_ground_picture_is_not_judged_by_name_checks(self):
        a = np.zeros((114, 144, 4), np.uint8)
        a[..., :3] = GRASS
        a[..., 3] = 255
        dets = self._dets(a, 'woodland/ground')
        self.assertFalse({'detail.fall_slab', 'detail.masonry_rock', 'detail.stair_read'} & set(dets))


class FormNames(unittest.TestCase):
    def test_whole_name_parts_only(self):
        from scripts.review import forms as F
        self.assertTrue(F.is_tree('kit/frost_pine_squat'))
        self.assertTrue(F.is_tree('woodland/oak_13'))
        self.assertTrue(F.is_tree('kit/lombardy_poplar') and F.is_tree('kit/cypress_b'))
        for name in ('kit/brackens_fire_ring_cold', 'commons/washing_line', 'kit/cloak', 'kit/frost_snow_pole'):
            self.assertFalse(F.is_tree(name), name)
        self.assertTrue(F.named('kit/frost_rockface_plain_b', F.ROCK_WORDS))
        self.assertTrue(F.named('kit/rock_face_west', F.ROCK_WORDS))
        self.assertFalse(F.named('kit/shadow_frost_crag__b', F.ROCK_WORDS), 'shadow pictures are not rock')
        self.assertFalse(F.named('kit/surface_cracks', F.ROCK_WORDS))
        self.assertTrue(F.named('kit/log_steps_3', F.STAIR_WORDS))
        self.assertTrue(F.named('kit/waterfall_2_tall', F.FALL_WORDS))
        self.assertFalse(F.named('kit/landfall_marker', F.FALL_WORDS))


class KitOverlapReading(unittest.TestCase):
    """kit_overlap reads a plan, the props index (role, variant, foot, res:// path) and the pictures."""

    def test_a_tiny_plan(self):
        import io as _io
        from scripts.review import kit_overlap as K

        def png(w, h):
            b = _io.BytesIO()
            Image.new('RGBA', (w, h), (90, 90, 90, 255)).save(b, 'PNG')
            return b.getvalue()
        files = {
            'game/kit/zones/tiny.json': json.dumps({'pieces': [
                {'id': 'hut', 'piece': 'hut', 'at': [300, 300]},
                {'id': 'fir_1', 'piece': 'fir', 'at': [250, 260], 'variant': 'tall'},
                {'id': 'bench', 'piece': 'bench', 'at': [280, 290]}]}).encode(),
            'game/kit/props/index.json': json.dumps({
                'hut': {'role': 'house', 'variants': {'still': {'png': 'res://kit/props/art/hut.png', 'foot': [50, 40]}}},
                'fir': {'role': 'tree', 'foot': [0, 0], 'variants': {
                    'still': {'png': 'res://kit/props/art/missing.png'},
                    'tall': {'png': 'res://kit/props/art/fir.png', 'foot': [10, 60]}}},
                'bench': {'role': 'prop', 'variants': {'still': {'png': 'res://kit/props/art/hut.png'}}}}).encode(),
            'game/kit/props/art/hut.png': png(100, 40),
            'game/kit/props/art/fir.png': png(20, 60),
        }
        with patch.object(K, 'reader', return_value=lambda rel: files[rel]):
            items = K.layout('tiny')
            fs = K.check('tiny')
        self.assertEqual([(i[0], i[1], i[2], i[3], i[4].shape) for i in items],
                         [('hut', 'house', 250, 260, (40, 100)), ('fir_1', 'tree', 240, 200, (60, 20))])
        # the fir (x 240..260, y 200..260) meets the hut (x 250..350, y 260..300) only at its foot row: no overlap
        self.assertEqual(fs, [])
        files['game/kit/zones/tiny.json'] = files['game/kit/zones/tiny.json'].replace(b'[250, 260]', b'[270, 290]')
        with patch.object(K, 'reader', return_value=lambda rel: files[rel]):
            fs = K.check('tiny')
        self.assertEqual([(f.detector, f.severity) for f in fs], [('logic.tree_overlap', 'fault')])


class CalibrationOpenFaults(unittest.TestCase):
    def test_only_f4_to_f6_are_open_and_each_says_why(self):
        with open(os.path.join(os.path.dirname(A.__file__), 'calibration_set.json')) as f:
            cal = json.load(f)
        opened = {f['id']: f['open'] for f in cal['faults'] if f.get('open')}
        self.assertEqual(sorted(opened), ['F4', 'F5', 'F6'],
                         'an "open" fault leaves the recall gate: only Claude A or Matt may add one, with its measurements')
        for fid, why in opened.items():
            self.assertIsInstance(why, str)
            self.assertRegex(why, r'\d', f'{fid}: the reason must give what was measured')


class FormNamesRound2(unittest.TestCase):
    """#481 audit round 2: walk frames, terrain code maps, animation sheets, landing stages."""

    def _brick_face(self):
        a = np.zeros((114, 144, 4), np.uint8)
        a[..., :3] = (120, 122, 130)
        a[..., 3] = 255
        for r, y in enumerate(range(0, 114, 14)):
            a[y:y + 2, :, :3] = 30
            for x in range((r % 2) * 12, 144, 24):
                a[y:y + 14, x:x + 2, :3] = 30
        return a

    def test_a_walk_frame_is_not_a_stair(self):
        from scripts.review import forms as F
        for name in ('props/cat_step1', 'props/heron_e_step2', 'props/lamb_left_step1'):
            self.assertFalse(F.named(name, F.STAIR_WORDS), name)
        for name in ('kit/log_steps_3', 'kit/frost_rock_stair', 'x/step_2', 'x/stair2'):
            self.assertTrue(F.named(name, F.STAIR_WORDS), name)

    def test_an_opaque_terrain_code_map_named_face_is_not_judged_as_rock(self):
        a = self._brick_face()
        for subject in ('terrain/over_lawn_over_earth_face', 'game/kit/terrain/fill_earth_face'):
            fs, _ = A.review_rgba(a, subject, '', 'woodland')
            self.assertNotIn('detail.masonry_rock', [f.detector for f in fs], subject)
        fs, _ = A.review_rgba(a, 'kit/earth_face_cutout', '', 'woodland')
        self.assertIn('detail.masonry_rock', [f.detector for f in fs], 'the same picture as a prop is judged')

    def test_a_character_sheet_is_not_a_stair(self):
        from scripts.review import forms as F
        for subject in ('sheets/stair_up_S', 'game/assets/characters/bramble/sheets/powered_stair_down_N'):
            self.assertFalse(F.named(subject, F.STAIR_WORDS), subject)

    def test_a_landing_stage_is_a_deck_and_a_pier_ladder_is_not(self):
        from scripts.review import forms as F
        self.assertTrue(F.named('kit/riverside_landing_stage', F.BRIDGE_WORDS))
        a = np.zeros((60, 120, 4), np.uint8)
        a[..., :3] = (150, 100, 60)
        a[..., 3] = 255
        a[:, ::7, :3] = (70, 45, 25)
        self.assertEqual([f.detector for f in F.deck_upright(a[..., :3], a[..., 3] > 0, H, 'kit/riverside_landing_stage')],
                         ['logic.deck_upright'])
        self.assertEqual(F.deck_upright(a[..., :3], a[..., 3] > 0, H, 'props/pier_ladder'), [])

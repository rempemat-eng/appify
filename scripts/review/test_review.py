"""Regression tests for the review detectors, on small synthetic pictures (no screenshots).

    python3 -m unittest scripts.review.test_review        (npm run check:review)

Each detector gets a picture that must trip it and one that must not, so a threshold change
that loses a calibration fault, or starts flagging clean art, fails here first.
"""
from __future__ import annotations

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


class Water(unittest.TestCase):
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
    def test_refusals(self):
        old_cat, old_queue = gate.CATALOGUE, gate.QUEUE
        d = tempfile.mkdtemp()
        try:
            gate.CATALOGUE = d
            gate.QUEUE = os.path.join(d, 'fix-queue.json')
            zone = 'woodland'
            name = 'stump'
            png = os.path.join(gate.GAME, 'zones', zone, 'art', name + '.png')
            self.assertTrue(gate.refusals(zone, [name]))                 # no record
            os.makedirs(os.path.join(d, zone))
            sha = A.sha256(png)
            json.dump({'sha256': sha, 'status': 'fail', 'findings': []}, open(os.path.join(d, zone, name + '.json'), 'w'))
            self.assertTrue(gate.refusals(zone, [name]))                 # failing and not queued
            json.dump({'queue': [{'id': f'{zone}/{name}'}]}, open(gate.QUEUE, 'w'))
            self.assertFalse(gate.refusals(zone, [name]))                # queued
            json.dump({'sha256': 'x', 'status': 'pass'}, open(os.path.join(d, zone, name + '.json'), 'w'))
            self.assertTrue(gate.refusals(zone, [name]))                 # stale
        finally:
            gate.CATALOGUE, gate.QUEUE = old_cat, old_queue



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
        for producer, name in ((R.SN, 'load_zone'), (R.json, 'load')):
            with self.subTest(producer=name):
                report = Path(self.out, 'report.json')
                report.write_text('{"counts":{"blocker":0,"fault":0,"polish":0}}')
                with patch.object(producer, name, side_effect=ValueError('source unavailable')):
                    with self.assertRaisesRegex(ValueError, 'source unavailable'):
                        R.main(['woodland', '--out', self.out])
                self.assertFalse(report.exists())

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


if __name__ == '__main__':
    unittest.main()

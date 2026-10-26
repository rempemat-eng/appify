"""Regression tests for the review detectors, on small synthetic pictures (no screenshots).

    python3 -m unittest scripts.review.test_review        (npm run check:review)

Each detector gets a picture that must trip it and one that must not, so a threshold change
that loses a calibration fault, or starts flagging clean art, fails here first.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest

import numpy as np
from PIL import Image

from scripts.review import core, water, screen, construct as C, detail as D, scene as SN, gate, assets as A
from scripts.review import edges as E
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

if __name__ == '__main__':
    unittest.main()

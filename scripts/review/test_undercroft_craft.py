"""Guards for the fault classes the 8 Nov detail audit found in the Undercroft
(docs/reviews/2026-11-08-undercroft-woodland-placed.md): a terrazzo of pale specks on the six flat
stone pieces and the floor (G-2, P-2, SE-2, L-3; specks.py is a pin for these, not a detector), the
floor's light drawn as contour bands or rugs (G-1, G-1r), its hue cutting across the flags in arcs
(G-7, checked on the real floor painted from the plan), and a picture whose size or foot drifts from
the scene's (game/zones/undercroft/undercroft.tscn is written from kit.json).

    python3 -m unittest scripts.review.test_undercroft_craft
"""
import json
import os
import unittest

import numpy as np
from PIL import Image

from scripts.review.specks import speck_scatter, dark_speck_scatter, LIMIT

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(ROOT, 'game', 'zones', 'undercroft', 'art')
STONE_PIECES = ('plate_up', 'plate_down', 'lever_up', 'lever_down', 'seal_slab', 'seal_sunk')


def _rgba(name):
    return np.asarray(Image.open(os.path.join(ART, name + '.png')).convert('RGBA'))


class SpeckScatter(unittest.TestCase):
    def test_terrazzo_fixture_is_caught(self):
        # a calm stone field with an even scatter of tan 2 x 3 specks: Matt's U1 terrazzo
        a = np.zeros((60, 60, 4), np.uint8)
        a[..., :3] = (142, 135, 130)
        a[..., 3] = 255
        for y in range(4, 56, 7):
            for x in range(4 + (y % 2) * 3, 56, 7):
                a[y:y + 2, x:x + 3, :3] = (190, 160, 110)
        self.assertGreater(speck_scatter(a), LIMIT)

    def test_sparse_terrazzo_just_over_the_limit_is_caught(self):
        # pale 2 x 2 specks every 20 px: about 2.5 a 1000 px, just over the limit
        a = np.zeros((100, 100, 4), np.uint8)
        a[..., :3] = (142, 135, 130)
        a[..., 3] = 255
        for y in range(6, 96, 20):
            for x in range(6, 96, 20):
                a[y:y + 2, x:x + 2, :3] = (171, 161, 148)
        self.assertGreater(speck_scatter(a), LIMIT)

    def test_a_few_pale_clusters_in_a_drift_pass(self):
        # pale clusters (a tone up, so they could count) gathered in one drift touch each other: texture
        a = np.zeros((100, 100, 4), np.uint8)
        a[..., :3] = (142, 135, 130)
        a[..., 3] = 255
        a[20:30, 20:34, :3] = (171, 161, 148)
        for y, x in ((22, 24), (25, 29), (27, 22)):
            a[y:y + 2, x:x + 2, :3] = (142, 135, 130)
        self.assertLessEqual(speck_scatter(a), LIMIT)

    def test_snow_specks_on_stone_count(self):
        # snow is a material: pale snow dots on stone are terrazzo, not glow
        a = np.zeros((100, 100, 4), np.uint8)
        a[..., :3] = (142, 135, 130)
        a[..., 3] = 255
        for y in range(6, 96, 14):
            for x in range(6, 96, 14):
                a[y:y + 2, x:x + 2, :3] = (230, 234, 236)
        self.assertGreater(speck_scatter(a), LIMIT)

    def test_undercroft_stone_pieces_carry_no_terrazzo(self):
        for name in STONE_PIECES:
            with self.subTest(name=name):
                self.assertLessEqual(speck_scatter(_rgba(name)), LIMIT, name)

    def test_round3_pools_earth_grit_is_caught(self):
        # the round 3 floor (b50caa14): room 1's warm pool, its heart full of earth grit a tone under it (G-16)
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r3_pool.png')).convert('RGBA'))
        self.assertGreater(dark_speck_scatter(a), LIMIT)

    def test_undercroft_floor_carries_no_dark_grit(self):
        g = _rgba('ground')
        self.assertLessEqual(dark_speck_scatter(g[160:600]), LIMIT)
        self.assertLessEqual(dark_speck_scatter(g[150:273, 60:211]), LIMIT)   # room 1's pool, the fixture's box

    def test_a_dither_checker_is_not_terrazzo(self):
        # a 2 x 2 checker band (a light fade) touches at its corners: one run, not specks
        a = np.zeros((60, 60, 4), np.uint8)
        a[..., :3] = (51, 48, 81)
        a[..., 3] = 255
        Y, X = np.mgrid[0:60, 0:60]
        band = (Y > 20) & (Y < 30) & (((X // 2 + Y // 2) % 2) == 0)
        a[band, :3] = (37, 35, 64)
        self.assertLessEqual(dark_speck_scatter(a), LIMIT)

    def test_undercroft_floor_carries_no_terrazzo(self):
        g = _rgba('ground')
        self.assertLessEqual(speck_scatter(g[160:600]), LIMIT)       # the whole floor, rooms' north to south


class StepsByFlag(unittest.TestCase):
    def setUp(self):
        from scripts.art.native import ctx
        if not ctx._configured:
            ctx.configure(3.0, {}, {})
        from scripts.art.native import undercroft as U
        self.U = U
        # a 10 x 8 grid of 12 x 12 flags with one-texel joints, lit by one pool at the top left
        H, W = 96, 120
        slab = np.zeros((H, W), np.int32)
        k = 0
        for j in range(0, H, 12):
            for i in range(0, W, 12):
                k += 1
                slab[j:j + 11, i:i + 11] = k
        self.slab, self.n = slab, k
        Y, X = np.mgrid[0:H, 0:W]
        d = np.hypot(X - 20, Y - 16) / 70
        self.level = U.FLOOR_AMBIENT + U.POOL_HEART * np.clip(1 - d, 0, 1) ** 1.3 + U.POOL_SPILL * np.clip(1 - d / 2.2, 0, 1)

    def test_a_pool_climbs_at_most_three_rungs(self):
        r = self.U.flag_rungs(self.level + 3, self.slab, self.n, np.random.default_rng(0), split=np.ones(self.slab.shape, bool))
        self.assertLessEqual(r[self.slab > 0].max(), self.U.FLOOR_AMBIENT + self.U.POOL_STEPS)

    def test_each_flag_is_one_rung_or_two_straight_halves(self):
        r = self.U.flag_rungs(self.level, self.slab, self.n, np.random.default_rng(0), split=np.ones(self.slab.shape, bool))
        for f in range(1, self.n + 1):
            m = self.slab == f
            vals = np.unique(r[m])
            self.assertLessEqual(len(vals), 2, f'flag {f} has {len(vals)} rungs (a contour band runs through it)')
            if len(vals) == 2:
                sub = r[m].reshape(11, 11)
                rows_one = all(len(np.unique(row)) == 1 for row in sub)
                cols_one = all(len(np.unique(col)) == 1 for col in sub.T)
                self.assertTrue(rows_one or cols_one, f'flag {f} is split along a ragged or slanted line')

    def test_shade_flags_are_whole(self):
        r = self.U.flag_rungs(self.level, self.slab, self.n, np.random.default_rng(0), split=None)
        for f in range(1, self.n + 1):
            self.assertEqual(len(np.unique(r[self.slab == f])), 1)

    def test_light_falls_off_from_the_source(self):
        r = self.U.flag_rungs(self.level, self.slab, self.n, np.random.default_rng(0))
        near, far = r[16, 20], r[90, 110]
        self.assertGreater(near, far)


class RealFloorTint(unittest.TestCase):
    """G-7 on the real floor: paint the Undercroft from its plan (in memory, into a scratch folder) and
    check that no flag carries both warm and cool light in its body (an arc of another hue across it)."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        from scripts.art.native import ctx
        plan_path = os.path.join(ROOT, 'game', 'data', 'plans', 'undercroft.json')
        plan = json.load(open(plan_path))
        ctx.configure(3.0, {}, plan)
        from scripts.art.native import undercroft as U
        plan['_inputs'] = U.input_hash(plan_path, 3.0)
        cls.f = {}
        with tempfile.TemporaryDirectory() as d:
            U.build(plan, os.path.join(d, 'art'), fields=cls.f)
            cls.painted = np.asarray(Image.open(os.path.join(d, 'art', 'ground.png')).convert('RGB'))

    def test_it_is_the_committed_floor(self):
        self.assertTrue(np.array_equal(self.painted, _rgba('ground')[..., :3]),
                        'the committed ground.png is not what the painter draws from the plan')

    def test_the_tint_is_decided_per_flag(self):
        # G-7: the warm and cool tint masks the painter paints with are whole flags, never arcs across one
        from scipy import ndimage as ndi
        slab = self.f['slab']
        for name in ('tint_warm', 'tint_cool'):
            t = self.f[name]
            split = []
            for f, sl in enumerate(ndi.find_objects(slab), start=1):
                if sl is None:
                    continue
                v = t[sl][slab[sl] == f]
                if v.any() and not v.all():
                    split.append(f)
            self.assertFalse(split, f'{name}: {len(split)} flags are split by the tint: {split[:5]}')

    def test_no_flag_holds_warm_and_cool(self):
        from scipy import ndimage as ndi
        slab, paint = self.f['slab'], self.f['paint']
        rgb = self.painted.astype(int)
        warm = (rgb[..., 0] - rgb[..., 2]) > 14                 # amber, earth, sand light
        lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        # the skylight's lit blue (not moss, and not the shade's own blue-violet, which a pool falls off into)
        cool = ((rgb[..., 2] - rgb[..., 0]) > 18) & (rgb[..., 2] > rgb[..., 1] + 10) & (lum >= 72)
        bad = []
        for f, sl in enumerate(ndi.find_objects(slab), start=1):
            if sl is None:
                continue
            m = (slab[sl] == f) & paint[sl]
            m = ndi.binary_erosion(m, iterations=2)             # the body, not its lips and joints
            n = int(m.sum())
            if n < 40:
                continue
            w, c = int(warm[sl][m].sum()), int(cool[sl][m].sum())
            if w > 0.04 * n and c > 0.04 * n:
                bad.append((f, w, c, n))
        self.assertFalse(bad, f'{len(bad)} flags carry both warm and cool light (arcs across them): {bad[:5]}')


class SceneUnmoved(unittest.TestCase):
    def test_pictures_keep_the_scenes_sizes_and_feet(self):
        # the sizes the scene was written for (undercroft.tscn offsets = -anchor from kit.json); round 3 changed
        # only channel_lit, with its offset, in the scene
        sizes = {'cairn_alcove': (108, 100), 'channel_lit': (260, 134), 'lever_down': (54, 72), 'lever_up': (54, 72),
                 'plate_down': (66, 66), 'plate_up': (66, 72), 'roots_corridor': (144, 48), 'roots_hall': (150, 54),
                 'rubble_chamber': (84, 69), 'rubble_corridor': (84, 69), 'rubble_hall': (108, 82), 'rubble_seal': (72, 44),
                 'seal_slab': (54, 270), 'seal_sunk': (52, 148), 'shard': (90, 126), 'stump_nw': (84, 104),
                 'stump_se': (84, 104), 'torch': (120, 66), 'urn_seal': (48, 60)}
        for name, wh in sizes.items():
            with self.subTest(name=name):
                self.assertEqual(Image.open(os.path.join(ART, name + '.png')).size, wh)
        kit = json.load(open(os.path.join(ROOT, 'game', 'zones', 'undercroft', 'kit.json')))
        offs = {o['id']: tuple(o['offset']) for o in kit['objects']}
        self.assertEqual(offs['cairn_alcove'], (-54, -99))
        self.assertEqual(offs['channel_lit'], (-10, -124))         # round 3: the overlay lights the lips (scene changed)


if __name__ == '__main__':
    unittest.main()

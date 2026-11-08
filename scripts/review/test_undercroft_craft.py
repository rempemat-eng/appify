"""Guards for the fault classes the 8 Nov detail audit found in the Undercroft
(docs/reviews/2026-11-08-undercroft-woodland-placed.md): a terrazzo of pale specks on stone (G-2,
P-2, SE-2, L-3), floor light pools drawn as posterised contour bands (G-1), and a picture whose size
or foot drifts from the scene's (the scene, game/zones/undercroft/undercroft.tscn, is written from
kit.json and must not move under a redraw).

    python3 -m unittest scripts.review.test_undercroft_craft
"""
import json
import os
import unittest

import numpy as np
from PIL import Image

from scripts.review.specks import speck_scatter, LIMIT

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

    def test_clusters_in_drifts_pass(self):
        # sibling clusters at the same value gathered in one drift are texture, not terrazzo
        a = np.zeros((60, 60, 4), np.uint8)
        a[..., :3] = (142, 135, 130)
        a[..., 3] = 255
        rng = np.random.default_rng(1)
        for _ in range(30):
            y, x = rng.integers(8, 24, 2)
            a[y:y + 2, x:x + 2, :3] = (135, 125, 120)
        self.assertLessEqual(speck_scatter(a), LIMIT)

    def test_undercroft_stone_pieces_carry_no_terrazzo(self):
        for name in STONE_PIECES:
            with self.subTest(name=name):
                self.assertLessEqual(speck_scatter(_rgba(name)), LIMIT, name)

    def test_undercroft_floor_carries_no_terrazzo(self):
        g = _rgba('ground')
        self.assertLessEqual(speck_scatter(g[160:440]), LIMIT)


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


class SceneUnmoved(unittest.TestCase):
    def test_pictures_keep_the_scenes_sizes_and_feet(self):
        # the sizes the scene was written for (undercroft.tscn offsets = -anchor from kit.json)
        sizes = {'cairn_alcove': (108, 100), 'channel_lit': (218, 10), 'lever_down': (54, 72), 'lever_up': (54, 72),
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
        self.assertEqual(offs['channel_lit'], (-1, -5))


if __name__ == '__main__':
    unittest.main()

"""Guards for the fault classes the 8 Nov detail audit found in the Undercroft
(docs/reviews/2026-11-08-undercroft-woodland-placed.md): a terrazzo of pale specks on the six flat
stone pieces and the floor (G-2, P-2, SE-2, L-3; specks.py is a pin for these, not a detector), the
floor's light drawn as contour bands or rugs (G-1, G-1r), its hue cutting across the flags in arcs
(G-7, checked on the real floor painted from the plan), a picture whose size or foot drifts from
the scene's (game/zones/undercroft/undercroft.tscn is written from kit.json), and round 4's faults:
pools of hard steps that are not calm by the ground band (G-19, G-20, with round 4's pool as the
failing fixture), a shade floor far under Eastward 06's value (G-21), dark 1 px hatching on the flags
(G-22, with round 4's shade as the failing fixture) and a lit channel that lights no floor (C-4).

    python3 -m unittest scripts.review.test_undercroft_craft
"""
import json
import os
import unittest

import numpy as np
from PIL import Image

from scripts.review.specks import speck_scatter, dark_speck_scatter, LIMIT
from scripts.review.bands import contrast

CALM = 11.9          # the ground band's calm limit, 1.15 x 10.34 L (bands.ground_plane)

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

    def test_a_pool_climbs_at_most_two_rungs(self):
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

    def test_a_pool_climbs_two_rungs_at_most(self):
        # G-19: the heart and one rim over the ambient, no more
        from scripts.art.native import undercroft as U
        r = self.f['rung'][self.f['paint'] & (self.f['slab'] > 0)]
        self.assertLessEqual(int(r.max()), U.FLOOR_AMBIENT + U.POOL_STEPS)

    def test_no_dark_hatching_on_the_flags(self):
        # G-22: the run breaker's nicks in the joint colour stood on the calm flags as clustered 1 px dark
        # strokes, 3 to 12 texels tall; a flag's body (off its joints and marks) holds none
        from scipy import ndimage as ndi
        f = self.f
        body = f['paint'] & (f['slab'] > 0) & ~f['joint'] & (f['off'] == 0)
        body = ndi.binary_erosion(body, iterations=1)
        self.assertLessEqual(_strokes(self.painted, body), 3)

    def test_the_round4_hatching_is_caught(self):
        # the guard sees the fault: round 4's shade by room 1's south door (a8185aca), 51 strokes in the audit
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r4_hatch.png')).convert('RGB'))
        self.assertGreater(_strokes(a, np.ones(a.shape[:2], bool)), 10)

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


def _strokes(rgb, where):
    """Clustered 1 px dark strokes (G-22): texels darker by 8 L than both their east and west neighbours,
    in vertical runs 3 to 12 texels tall, inside `where`."""
    from scipy import ndimage as ndi
    c = rgb[..., :3].astype(float)
    lum = 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]
    thin = (lum < np.roll(lum, 1, 1) - 8) & (lum < np.roll(lum, -1, 1) - 8) & where
    thin[:, 0] = thin[:, -1] = False
    lab, n = ndi.label(thin, structure=np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]]))
    k = 0
    for sl in ndi.find_objects(lab):
        if sl is not None and 3 <= sl[0].stop - sl[0].start <= 12:
            k += 1
    return k


def _oklab_L(rgb):
    c = rgb[..., :3].astype(float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    l_ = 0.4122214708 * c[..., 0] + 0.5363325363 * c[..., 1] + 0.0514459929 * c[..., 2]
    m_ = 0.2119034982 * c[..., 0] + 0.6806995451 * c[..., 1] + 0.1073969566 * c[..., 2]
    s_ = 0.0883024619 * c[..., 0] + 0.2817188376 * c[..., 1] + 0.6299787005 * c[..., 2]
    return 0.2104542553 * np.cbrt(l_) + 0.7936177850 * np.cbrt(m_) - 0.0040720342 * np.cbrt(s_)


class PoolsAndShade(unittest.TestCase):
    """Round 4's audit (G-19 to G-22) on the committed floor: the pools calm by the ground band (no
    target rings of hard steps), the shade floor at Eastward 06's value, and no dark hatching on its flags."""

    BOXES = {'room 1 pool': (60, 150, 211, 273), 'room 1 heart': (110, 170, 230, 215),
             'skylight': (1900, 300, 2051, 423), 'skylight heart': (1870, 360, 1960, 425), 'stair': (40, 320, 200, 480)}

    def test_the_pools_are_calm(self):
        g = _rgba('ground')[..., :3]
        for name, (x0, y0, x1, y1) in self.BOXES.items():
            with self.subTest(box=name):
                c = g[y0:y1, x0:x1]
                self.assertLess(contrast(c, np.ones(c.shape[:2], bool), 74), CALM, name)

    def test_the_round4_pool_was_not_calm(self):
        # the guard sees the fault: round 4's room 1 pool (a8185aca), whose steps were hard rings (15.4 L)
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r4_pool.png')).convert('RGB'))
        self.assertGreater(contrast(a, np.ones(a.shape[:2], bool), 74), CALM)

    def test_the_shade_floor_sits_at_eastwards_value(self):
        # G-21: Eastward 06's shade floor is OKLab L 0.36 to 0.37; round 4's was 0.274, near the void (0.21)
        g = _rgba('ground')
        for (x0, y0, x1, y1) in ((200, 430, 310, 512), (250, 380, 387, 490)):
            L = float(np.median(_oklab_L(g[y0:y1, x0:x1])))
            self.assertGreaterEqual(L, 0.33)
            self.assertLessEqual(L, 0.40)


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


class ChannelSpill(unittest.TestCase):
    def test_the_lit_channel_lights_the_floor_beyond_its_far_wall(self):
        # C-4: round 4's spill never reached the floor (its checker flipped phase every two rows and each row
        # had to 4-touch the last). The overlay's rows past the lit far wall (the groove's middle is its foot
        # row, 124; its far lip is 7 rows north) must carry light over four rows, fading, along the main run
        a = _rgba('channel_lit')[..., 3] > 0
        foot = 124
        run = a[foot - 2, :].nonzero()[0]                           # the main run's columns (its groove floor)
        x0, x1 = int(run.min()), int(run.max())
        share = [float(a[foot - 7 - k, x0:x1].mean()) for k in range(4)]
        self.assertGreater(share[0], 0.6, share)
        self.assertGreater(share[1], 0.25, share)
        self.assertGreater(share[2], 0.25, share)
        self.assertGreater(share[3], 0.05, share)
        self.assertTrue(share[0] > share[1] >= share[3] * 0.9, share)


if __name__ == '__main__':
    unittest.main()

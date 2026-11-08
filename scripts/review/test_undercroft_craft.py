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
        self.assertLessEqual(dark_speck_scatter(g[150:273, 60:211]), LIMIT)   # room 1's pool, the fixture's box (round 9:
        #                                                                      no mask; the pool's body is solid steps)

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


class StagedBoundaries(unittest.TestCase):
    """Round 6 (G-24): a pool's boundaries follow its light's own curve as a wide staged 2 x 2 dither, so the
    light crosses the flags; round 4's flag-by-flag steps made blocks of lit paving."""

    def setUp(self):
        from scripts.art.native import ctx
        if not ctx._configured:
            ctx.configure(3.0, {}, {})
        from scripts.art.native import undercroft as U
        self.U = U
        H, W = 80, 160
        self.Y, self.X = np.mgrid[0:H, 0:W]
        self.field = 4.0 - self.X / 40.0                        # light falling off from the west, a rung every 40 texels

    def test_a_boundary_is_a_staged_dither_six_texels_wide_or_more(self):
        up = self.U.staged(self.field, 2.5, 12, self.Y, self.X)
        col = up.mean(axis=0)
        share = np.convolve(col, np.ones(4) / 4, mode='same')       # coverage over a 4-texel window (a Bayer cell)
        mixed = np.nonzero((share > 0.1) & (share < 0.9))[0]
        self.assertGreaterEqual(len(mixed), 6, 'the boundary is a hard step')
        self.assertLessEqual(len(mixed), 14)
        stages = sorted(set(np.round(share[mixed] * 4).astype(int)))
        self.assertTrue({1, 2, 3} <= set(stages), stages)       # a quarter, a half, three quarters

    def test_a_boundary_crosses_a_flag(self):
        slab = np.zeros(self.field.shape, np.int32)
        slab[:, 40:100] = 1                                      # one wide flag the boundary (x 60) crosses
        up = self.U.staged(self.field, 2.5, 12, self.Y, self.X)
        v = up[slab == 1]
        self.assertTrue(v.any() and not v.all(), 'the light stops at the flag')

    def test_whole_flags_stop_the_edge_at_their_joint(self):
        slab = np.zeros(self.field.shape, np.int32)
        slab[:, 40:100] = 1
        whole = np.array([False, True])
        up = self.U.staged(self.field, 2.5, 12, self.Y, self.X, whole=whole, slab=slab)
        v = up[slab == 1]
        self.assertTrue(v.all() or not v.any())


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

    def test_the_heart_outline_is_not_ruled(self):
        # G-24: round 5's hearts were whole flags, 64 % of their outline in straight runs of 10 px or more
        # (the round 5 pool, picture: test_the_round5_heart_was_ruled); the heart's own texel edge now
        from scipy import ndimage as ndi
        from scripts.art.native import undercroft as U
        f = self.f
        keep = ndi.binary_erosion(f['paint'], iterations=2)            # its own edge, not the wall it meets
        for tint, top in (('tint_warm', 3), ('tint_cool', 2)):                       # a torch's heart is its third band
            heart = (f['rung'] >= U.FLOOR_AMBIENT + top) & f['paint'] & f[tint]     # its texels (a staged dither)
            curve = (f['light'] >= U.FLOOR_AMBIENT + top - 0.5) & f['paint'] & f[tint]   # the light's curve
            self.assertTrue(heart.any())
            self.assertLess(_straight_share(heart, keep), 0.30, tint)
            self.assertLess(_straight_share(curve, keep), 0.30, tint)

    def test_damp_is_whole_flags_by_the_walls(self):
        # G-25: round 5's blotches were curves across 15 to 47 flags out in the rooms' middles
        from scipy import ndimage as ndi
        f = self.f
        damp, slab = f['damp'], f['slab']
        self.assertTrue(damp.any())
        for fl, sl in enumerate(ndi.find_objects(slab), start=1):
            if sl is None:
                continue
            v = damp[sl][slab[sl] == fl]
            if v.any():
                self.assertTrue(v.all(), f'flag {fl} is only partly damp')
                self.assertLessEqual(float(np.mean(f['dfl'][sl][slab[sl] == fl])), 48, f'damp flag {fl} in the open')

    def test_the_far_shade_steps_down(self):
        # G-27: round 5's floor was 0.359 from 20 px off the walls to the far corners in every room
        from scripts.art.native import undercroft as U
        f = self.f
        L = _oklab_L(self.painted)
        body = f['paint'] & (f['slab'] > 0) & ~f['joint'] & (f['off'] == 0)
        A = U.FLOOR_AMBIENT
        near, far = float(np.median(L[body & (f['rung'] == A)])), float(np.median(L[body & (f['rung'] == A - 1)]))
        self.assertTrue(0.33 <= near <= 0.40, near)
        self.assertTrue(0.30 <= far <= 0.33, far)
        for x0, x1 in ((48, 600), (648, 1200), (1248, 1680), (1728, 2256)):
            m = body & (np.arange(body.shape[1])[None, :] >= x0) & (np.arange(body.shape[1])[None, :] < x1)
            self.assertGreater((m & (f['rung'] == A - 1)).sum() / max(1, (m & (f['rung'] <= A)).sum()), 0.08)

    def test_no_colour_holds_half_the_flags(self):
        # G-26: round 5's shade flags were 77.7 % one colour
        f = self.f
        from scripts.art.native import undercroft as U
        body = f['paint'] & (f['slab'] > 0) & ~f['joint'] & (f['off'] == 0) & (f['rung'] <= U.FLOOR_AMBIENT)
        _, cnt = np.unique(f['codes'][body], return_counts=True)
        self.assertLessEqual(cnt.max() / cnt.sum(), 0.5)

    def test_the_torchlight_falls_off_through_the_stone(self):
        # G-29: lamplit on 25 to 55 % of a torch pool, never against the slate shade; the darkest 15 % violet;
        # at least 20 % in-between texels (hue 320 to 35) in the band 8 texels either side of its edge. G-32
        # (round 8): the light reaching 1.1 to 1.4 H below the wall's foot, as Eastward 06's fire bowls (round 7's
        # 1.4 to 2.0 H came from 05's six-bulb lamp post; its pool reached 1.78 H)
        from scipy import ndimage as ndi
        from scripts.art.native.palette import FI
        from scripts.art.native import undercroft as U
        f = self.f
        A = U.FLOOR_AMBIENT
        L, C, h = _oklch(self.painted)
        pool = f['tint_warm'] & f['paint'] & (f['rung'] > A)
        lamp = np.isin(f['codes'] // 8, [FI['lamplit'], FI['lamplit_warm'], FI['lamplit_cool']])
        self.assertTrue(0.25 <= lamp[pool].mean() <= 0.55, lamp[pool].mean())
        shade = f['paint'] & (f['rung'] <= A)
        self.assertEqual(int((lamp & f['paint'] & ndi.binary_dilation(shade)).sum()), 0)
        d = pool & (L <= np.quantile(L[pool], 0.15))
        self.assertGreaterEqual(np.mean((h[d] >= 290) & (h[d] <= 350)), 0.8)
        lit = f['paint'] & (f['rung'] > A)
        hem = f['paint'] & ndi.binary_dilation(pool, iterations=10) & ~f['tint_cool'] & (
            ((ndi.distance_transform_edt(lit) > 0) & (ndi.distance_transform_edt(lit) <= 8)) |
            ((ndi.distance_transform_edt(~lit) > 0) & (ndi.distance_transform_edt(~lit) <= 8)))
        between = (h >= 320) | (h <= 35)
        self.assertGreaterEqual(between[hem].mean(), 0.20)
        col = f['rung'][168:600, 160:176].max(1)                  # below torch 1
        reach = int(np.nonzero(col > A)[0].max())
        self.assertTrue(1.1 * 74 <= reach <= 1.4 * 74, reach)
        a, fl, cx, foot = _r7_torch1()                            # round 7's torch 1, by the picture: 1.45 H
        self.assertFalse(1.1 <= _torch_light(a, fl, cx, foot)['reach'] <= 1.4)

    def test_a_pool_climbs_three_rungs_at_most(self):
        # G-19, G-29: the in-between band, the warm band and the heart over the ambient, no more
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
        # G-7: no flag's lit body holds both torchlight (the lamplit ramps) and daylight (the slate ramps lit
        # by the skylight or the hatch); a flag's hue is decided once
        from scipy import ndimage as ndi
        from scripts.art.native.palette import FI
        from scripts.art.native import undercroft as U
        f = self.f
        slab, paint, codes = f['slab'], f['paint'], f['codes']
        lit = f['rung'] > U.FLOOR_AMBIENT
        warm = np.isin(codes // 8, [FI['lamplit'], FI['lamplit_warm'], FI['lamplit_cool']]) & lit
        cool = np.isin(codes // 8, [FI['slate'], FI['slate_warm'], FI['slate_cool']]) & (codes % 8 >= 2) & lit
        bad = []
        for fl, sl in enumerate(ndi.find_objects(slab), start=1):
            if sl is None:
                continue
            m = (slab[sl] == fl) & paint[sl]
            n = int(m.sum())
            if n < 40:
                continue
            w, c = int(warm[sl][m].sum()), int(cool[sl][m].sum())
            if w > 0.04 * n and c > 0.04 * n:
                bad.append((fl, w, c, n))
        self.assertFalse(bad, f'{len(bad)} flags carry both warm and cool light: {bad[:5]}')

    def test_the_pools_are_solid_steps(self):
        # G-37 (round 9): a torch pool's body is solid tone steps following the flags, with one narrow dither band at its
        # rim; at most 25 % of its lit texels stand in a 2 x 2 halftone (a block lighter or darker than all four
        # neighbours). Round 8's abutting fades put 30 % of its pools' lit texels in one
        f = self.f
        Y, X = np.mgrid[0:f['rung'].shape[0], 0:f['rung'].shape[1]]
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                lit = f['paint'] & (f['rung'] > 2) & f['tint_warm'] & (np.hypot(X - cx, Y - foot) < 1.5 * 74)
                self.assertLessEqual(_halftone(self.painted, lit), 0.25)
        a, fl, cx, foot = _r8_torch1()
        self.assertGreater(_halftone(a, _pool_body(a, fl, cx, foot)), 0.25)

    def test_the_torches_light_only_their_own_kerb(self):
        # G-35 (round 9): no lamplit texel on a kerb (off the floor, within 18 texels of it) farther than 0.8 H from a
        # flame. Round 8 lit every south kerb under a torch, 3.45 to 6.69 H from the flame
        from scipy import ndimage as ndi
        from scripts.art.native.palette import FI
        f = self.f
        kerb = (ndi.distance_transform_edt(~f['paint']) <= 18) & ~f['paint']
        lamp = np.isin(f['codes'] // 8, [FI['lamplit'], FI['lamplit_warm'], FI['lamplit_cool']])
        Y, X = np.mgrid[0:lamp.shape[0], 0:lamp.shape[1]]
        near = np.zeros(lamp.shape, bool)
        for cx, foot in self._torches():
            near |= np.hypot(X - cx, Y - (foot - 63)) <= 0.8 * 74
        self.assertEqual(int((kerb & lamp & ~near).sum()), 0)
        for g, name in ((self.painted[560:615, 100:560], 'r9'),
                        (np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r8_south_kerb.png')).convert('RGB')), 'r8')):
            L, C, h = _oklch(g[40:])                                   # room 1's south kerb, under torches 1 and 2
            n = int(((h >= 35) & (h <= 100) & (C > 0.045)).sum())      # (the lamp's colour, not stone 5's lit edge)
            (self.assertEqual if name == 'r9' else self.assertGreater)(n, 0, name)

    def test_the_lit_kerb_keeps_its_marks(self):
        # G-36 (round 9; Claude A's round 10 ruling): the kerb's lit top edge under each cup (the plinth's top row, 67
        # texels) steps from the flame and keeps its marks: no colour over 35 % of it. (The plinth's face below keeps the
        # painter's own drawing, which unlit already holds 34 to 58 % in one code.) Round 8's edge by torch 8 was one tan
        # code over all of it
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                self.assertLessEqual(_kerb_strip(self.painted[foot - 15:foot - 14, cx - 33:cx + 34])[0], 0.35)
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r8_kerb_t8.png')).convert('RGB'))
        self.assertGreater(_kerb_strip(a[13:14, 7:74])[0], 0.35)

    def test_the_middle_band_is_warm_stone(self):
        # G-38 (Claude A's round 10 ruling): the pool's middle band (0.65 to 1.05 H below the wall's foot) at median OKLCH C
        # 0.030 to 0.045, on lamplit_dusk; band by band (0.1 H) from the heart out to the shade its per-texel median C
        # stays at 0.025 or more and the hue of its mean colour walks the short way, down through about 20 and 346,
        # never by a neutral grey. Round 8's middle band was grey stone (C 0.018) and fails
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                C, _ = _middle_band(self.painted, self.f['paint'], cx, foot)
                self.assertTrue(0.030 <= C <= 0.045, C)
                walk = _hue_walk(self.painted, self.f['paint'], cx, foot)
                self.assertGreaterEqual(min(c for _, c, _ in walk), 0.025, walk)
                hs = [hh for _, _, hh in walk]
                steps = [((a - b + 180) % 360) - 180 for a, b in zip(hs, hs[1:])]
                self.assertTrue(all(-5 < st_ < 90 for st_ in steps), walk)   # down the hue circle, the short way
                warm = [i for i, hh in enumerate(hs) if 5 <= hh <= 40]
                self.assertTrue(warm and any(hh >= 300 for hh in hs[warm[0]:]), walk)   # through about 20, then 346
        a, fl, cx, foot = _r8_torch1()
        C, _ = _middle_band(a, fl, cx, foot)
        self.assertLess(C, 0.030, C)

    def _torches(self):
        plan = json.load(open(os.path.join(ROOT, 'game', 'data', 'plans', 'undercroft.json')))
        return [(3 * tx, 3 * ty) for tx, ty in plan['torches']]           # the cup's x and the wall's foot, texels

    def test_each_torch_has_a_glowing_heart(self):
        # G-32 (round 8): under each cup a heart of 0.5 to 0.8 H2 at Eastward 06's floor by a fire bowl: median OKLCH
        # C 0.06 to 0.08, hue 55 to 75 (of its mean colour), blurred L 0.50 to 0.56. Round 7's torch 1 had none
        # (0.004 H2 over L 0.50, C 0.043 at the kerb)
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                t = _torch_light(self.painted, self.f['paint'], cx, foot)
                self.assertTrue(0.45 <= t['heart_area'] <= 0.85, t)
                self.assertTrue(0.06 <= t['heart_C'] <= 0.08, t)
                self.assertTrue(55 <= t['heart_hue'] <= 75, t)
                self.assertTrue(0.50 <= t['heart_L'] <= 0.56, t)
        a, fl, cx, foot = _r7_torch1()
        t = _torch_light(a, fl, cx, foot)
        self.assertFalse(0.45 <= t['heart_area'] <= 0.85 and 0.06 <= t['heart_C'] <= 0.08, t)

    def test_the_light_falls_with_no_shelf_and_stays_small(self):
        # G-32 (round 8): from the heart (its blurred L 0.52 and over) to the rim the blurred value falls at least
        # 0.01 in every 0.15 H step; the lift (0.02 L over the shade) reaches 1.1 to 1.4 H below the wall's foot,
        # each pool at most 2.5 H2, its colour-only band (lift under 0.03 L) at most 25 %. Round 7's torch 1 sat on a
        # shelf (0.434, 0.432, 0.433) over 3.0 H2
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                t = _torch_light(self.painted, self.f['paint'], cx, foot)
                self.assertGreaterEqual(t['shelf'], 0.01, t)
                self.assertTrue(1.1 <= t['reach'] <= 1.4, t)
                self.assertLessEqual(t['area'], 2.5, t)
                self.assertLessEqual(t['colour_only'], 0.25, t)
        a, fl, cx, foot = _r7_torch1()
        t = _torch_light(a, fl, cx, foot)
        self.assertLess(t['shelf'], 0.01, t)
        self.assertGreater(t['area'], 2.5, t)
        self.assertGreater(t['reach'], 1.4, t)

    def test_the_lamp_colour_thins_with_distance(self):
        # G-32 (round 8): lamplit by each texel's own distance from the cup's foot: at least 70 % of the floor within
        # 0.4 H, at most 15 % at 0.8 to 1.1 H and none beyond, and its median chroma falling band by band
        from scripts.art.native.palette import FI
        f = self.f
        L, C, h = _oklch(self.painted)
        lamp = np.isin(f['codes'] // 8, [FI['lamplit'], FI['lamplit_warm'], FI['lamplit_cool']])
        Y, X = np.mgrid[0:lamp.shape[0], 0:lamp.shape[1]]
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                d = np.hypot(X - cx, Y - foot) / 74
                share, chroma = [], []
                for a0, a1 in ((0, 0.4), (0.4, 0.8), (0.8, 1.1), (1.1, 1.6)):
                    m = f['paint'] & (Y >= foot) & (d >= a0) & (d < a1)
                    share.append(float(lamp[m].mean()))
                    chroma.append(float(np.median(C[m & (f['rung'] > 2)])) if (m & (f['rung'] > 2)).any() else 0.0)
                self.assertGreaterEqual(share[0], 0.70, share)
                self.assertLess(share[1], share[0], share)
                self.assertLessEqual(share[2], 0.15, share)
                self.assertEqual(share[3], 0.0, share)
                self.assertTrue(chroma[0] >= 0.06 and chroma[0] >= chroma[1] >= chroma[2], chroma)

    def test_the_torches_light_their_wall_block_by_block(self):
        # G-33 (round 8): against the wall as drawn before the torches light it (the painter's own), the face within
        # 0.3 H of a cup rises 0.045 L or more on the mean, less over 0.3 to 0.6 H, and nothing past 0.8 H
        from scripts.art.native.palette import LUT
        f = self.f
        L, _, _ = _oklch(self.painted)
        w0 = f['wall0']
        L0, _, _ = _oklch(np.where((w0 >= 0)[..., None], LUT[np.maximum(w0, 0)], 0).astype(np.uint8))
        Y, X = np.mgrid[0:L.shape[0], 0:L.shape[1]]
        for cx, foot in self._torches():
            with self.subTest(torch=cx):
                d = np.hypot(X - cx, Y - (foot - 48)) / 74
                wall = ~f['paint'] & (Y < foot - 1) & (w0 >= 0)
                lift = [float(np.mean((L - L0)[wall & (d >= a0) & (d < a1)])) for a0, a1 in ((0, 0.3), (0.3, 0.6), (0.8, 1.2))]
                self.assertGreaterEqual(lift[0], 0.045, lift)
                self.assertTrue(0 < lift[1] < lift[0], lift)
                self.assertLess(abs(lift[2]), 0.01, lift)


def _blur_on(L, m, k=19):
    """OKLab L box-blurred over `m` only (0.25 H at 74 texels a character), as a pool reads at 1x."""
    from scipy import ndimage as ndi
    w = ndi.uniform_filter(m.astype(float), k)
    return np.where(m, ndi.uniform_filter(np.where(m, L, 0.0), k) / np.maximum(w, 1e-6), 0.0)


def _torch_light(rgb, floor, cx, foot, shade=0.355):
    """G-32's measures of one torch's pool in a picture, from the cup's x and the wall's foot (texels), on the floor
    texels `floor`: the pool (blurred L 0.02 over Eastward 06's shade, the part joined to the wall under the cup,
    opened by 7 x 7) as reach and width in H, area in H2 and its colour-only share (lift under 0.03); the heart
    (blurred L 0.50 and over, joined to the kerb under the cup) as area, median C, the hue of its mean colour and
    median blurred L; and the shelf, the least fall of the blurred median per 0.15 H step (within 55 degrees of
    straight down from the flame, 63 texels over the foot) from the heart to the rim."""
    from scipy import ndimage as ndi
    L, C, h = _oklch(rgb)
    Lb = _blur_on(L, floor)
    Y, X = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    rf = np.hypot(X - cx, Y - foot) / 74
    lab, _ = ndi.label(floor & (Lb >= shade + 0.02) & (rf < 2.0))
    pool = ndi.binary_opening(lab == lab[foot + 10, cx], structure=np.ones((7, 7), bool))
    ys, xs = np.nonzero(pool)
    out = dict(reach=(ys.max() - foot) / 74, width=(xs.max() - xs.min() + 1) / 74, area=pool.sum() / 74 ** 2,
               colour_only=float((pool & (Lb < shade + 0.03)).sum() / pool.sum()))
    lab, _ = ndi.label(floor & (Lb >= 0.50) & (rf < 1.3))
    ids = np.unique(lab[foot + 1:foot + 20, cx - 10:cx + 10])
    heart = np.isin(lab, ids[ids > 0])
    a_, b_ = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    out.update(heart_area=heart.sum() / 74 ** 2, heart_C=float(np.median(C[heart])) if heart.any() else 0.0,
               heart_hue=float(np.degrees(np.arctan2(b_[heart].mean(), a_[heart].mean())) % 360) if heart.any() else 0.0,
               heart_L=float(np.median(Lb[heart])) if heart.any() else 0.0)
    fy = foot - 63
    d = np.hypot(X - cx, Y - fy) / 74
    cone = floor & (Y > fy) & (np.degrees(np.arctan2(np.abs(X - cx), np.maximum(Y - fy, 1e-6))) <= 55)
    st = np.array([np.median(Lb[cone & (np.abs(d - c0) < 0.075)]) for c0 in np.arange(0.925, 2.6, 0.15)])
    rim = np.nonzero(st < shade + 0.02)[0]
    end = int(rim[0]) if len(rim) else len(st) - 1
    top = np.nonzero(st[:end + 1] >= 0.52)[0]
    start = int(top[-1]) if len(top) else int(np.argmax(st[:end + 1]))
    out['shelf'] = float((st[start:end] - st[start + 1:end + 1]).min()) if end > start else -1.0
    out['steps'] = [round(float(v), 3) for v in st[:end + 1]]
    return out


def _halftone(rgb, region, step=0.03):
    """G-37's measure: the share of `region`'s texels in 2 x 2 blocks (on any of the four alignments) whose mean OKLab L
    stands 0.03 or more above or below all four neighbouring blocks: a dither's dots and checkers."""
    L = _oklch(rgb)[0]
    hit = np.zeros(L.shape, bool)
    for oy in (0, 1):
        for ox in (0, 1):
            l_ = L[oy:, ox:]
            Hh, Ww = l_.shape[0] // 2 * 2, l_.shape[1] // 2 * 2
            B = l_[:Hh, :Ww].reshape(Hh // 2, 2, Ww // 2, 2).mean((1, 3))
            P = np.pad(B, 1, mode='edge')
            nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
            dot = ((B - nb) >= step).all(0) | ((nb - B) >= step).all(0)
            hit[oy:oy + Hh, ox:ox + Ww] |= np.kron(dot, np.ones((2, 2), bool))
    return float(hit[region].mean()) if region.any() else 0.0


def _pool_body(rgb, floor, cx, foot, shade=0.355):
    """A torch pool's lit texels in a picture: blurred L 0.02 over the shade, within 1.5 H of the wall's foot."""
    L = _oklch(rgb)[0]
    Y, X = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    return floor & (_blur_on(L, floor) >= shade + 0.02) & (np.hypot(X - cx, Y - foot) < 1.5 * 74)


def _middle_band(rgb, floor, cx, foot):
    """G-38's measure: the median OKLCH C and the hue of the mean colour of the floor 0.65 to 1.05 H from the wall's foot
    under the cup (the lower half-disc)."""
    L, C, h = _oklch(rgb)
    Y, X = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    d = np.hypot(X - cx, Y - foot) / 74
    m = floor & (Y >= foot) & (d >= 0.65) & (d < 1.05)
    a_, b_ = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    return float(np.median(C[m])), float(np.degrees(np.arctan2(b_[m].mean(), a_[m].mean())) % 360)


def _hue_walk(rgb, floor, cx, foot):
    """(distance, per-texel median C, hue of the mean colour) for 0.1 H bands of floor from 0.55 to 1.15 H below the
    wall's foot under the cup (G-38's walk from the heart to the shade)."""
    L, C, h = _oklch(rgb)
    Y, X = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    d = np.hypot(X - cx, Y - foot) / 74
    a_, b_ = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    out = []
    for c0 in np.arange(0.55, 1.16, 0.1):
        m = floor & (Y >= foot) & (np.abs(d - c0) < 0.05)
        out.append((round(float(c0), 2), float(np.median(C[m])), float(np.degrees(np.arctan2(b_[m].mean(), a_[m].mean())) % 360)))
    return out


def _kerb_strip(rgb):
    """G-36's measures of a kerb strip: the share of its commonest colour and of the lamp's colour (hue 35 to 100, C
    over 0.045, so stone's own lit edges do not count)."""
    key = (rgb[..., 0].astype(np.int64) << 16) | (rgb[..., 1].astype(np.int64) << 8) | rgb[..., 2]
    _, n = np.unique(key, return_counts=True)
    L, C, h = _oklch(rgb)
    return float(n.max() / n.sum()), float(np.mean((h >= 35) & (h <= 100) & (C > 0.045)))


def _r8_torch1():
    """Round 8's torch 1 (41d62d92, the ground's 40..420 x 60..330): the picture, its floor, the cup's x, the foot."""
    a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r8_torch1.png')).convert('RGB'))
    fl = np.zeros(a.shape[:2], bool)
    fl[109:, 12:] = True
    return a, fl, 128, 108


def _r7_torch1():
    """Round 7's torch 1 (80159712, the ground's 40..420 x 60..330): the picture, its floor, the cup's x, the foot."""
    a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r7_torch1.png')).convert('RGB'))
    fl = np.zeros(a.shape[:2], bool)
    fl[109:, 12:] = True
    return a, fl, 128, 108


def _wall_light(rgb, cx, cy):
    """G-33's picture measures round a torch's cup: the mean OKLCH C within 0.3 H, and the 2 x 2 checkers of
    lamp-coloured blocks (hue 35 to 100, C over 0.03) within 0.6 H, as round 7's staged wall light drew them."""
    L, C, h = _oklch(rgb)
    Y, X = np.mgrid[0:L.shape[0], 0:L.shape[1]]
    d = np.hypot(X - cx, Y - cy) / 74
    lamp = (h >= 35) & (h <= 100) & (C > 0.03) & (d < 0.6)
    H2, W2 = L.shape[0] // 2 * 2, L.shape[1] // 2 * 2
    B = lamp[:H2, :W2].reshape(H2 // 2, 2, W2 // 2, 2).all((1, 3))
    chk = (B[:-1, :-1] & ~B[:-1, 1:] & ~B[1:, :-1] & B[1:, 1:]) | (~B[:-1, :-1] & B[:-1, 1:] & B[1:, :-1] & ~B[1:, 1:])
    return float(np.mean(C[d < 0.3])), int(chk.sum())


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


def _straight_share(mask, keep):
    """The share of a region's outline (inside `keep`) lying in straight horizontal or vertical runs of 10 px
    or more (G-24's measure of a ruled edge)."""
    from scipy import ndimage as ndi
    o = mask & ~ndi.binary_erosion(mask) & keep
    run = np.zeros_like(o)
    for st in (np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]]), np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]])):
        lab, n = ndi.label(o, structure=st)
        if n:
            sz = ndi.sum(o, lab, range(1, n + 1))
            run |= np.concatenate([[False], sz >= 10])[lab]
    return run.sum() / max(1, o.sum())


def _oklch(rgb):
    c = rgb[..., :3].astype(float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    l_ = np.cbrt(0.4122214708 * c[..., 0] + 0.5363325363 * c[..., 1] + 0.0514459929 * c[..., 2])
    m_ = np.cbrt(0.2119034982 * c[..., 0] + 0.6806995451 * c[..., 1] + 0.1073969566 * c[..., 2])
    s_ = np.cbrt(0.0883024619 * c[..., 0] + 0.2817188376 * c[..., 1] + 0.6299787005 * c[..., 2])
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720342 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360


def _warm_light(rgb):
    """The median OKLCH chroma and hue of a picture's lit warm texels (R over B, L 0.40 and up)."""
    L, C, h = _oklch(rgb)
    c = rgb[..., :3].astype(int)
    m = (c[..., 0] > c[..., 2] + 4) & (L >= 0.40)
    return float(np.median(C[m])), float(np.median(h[m])), int(m.sum())


def _spill(floor, overlay, foot=(10, 124), t_col=214, end_col=250, reach=30):
    """C-6's measure: the share of floor texels the lit overlay changes, by distance past the groove's carved
    lips, on each side of the main run and of the branch. `floor` is the floor under the overlay's canvas
    (same origin), `overlay` the picture; the plate, the lever and the T are left out."""
    H, W = overlay.shape[:2]
    comp = floor[:H, :W, :3].copy()
    on = overlay[..., 3] > 0
    comp[on] = overlay[on][:, :3]
    ch = np.abs(comp.astype(int) - floor[:H, :W, :3].astype(int)).sum(2) > 0
    ch = np.pad(ch, ((0, max(0, floor.shape[0] - H)), (0, 0)))
    fx, gy = foot
    cols = np.arange(fx + 14, t_col - 36)                    # the main run, clear of the plate and the branch's own light
    rows_b = np.arange(30, gy - 40)                          # the branch, clear of the lever and the main run's light
    out = {}                                                  # the carved groove and its lips reach d -8 .. +8: floor from 9 on
    out['north'] = [float(ch[gy - 9 - k, cols].mean()) for k in range(reach)]
    out['south'] = [float(ch[gy + 9 + k, cols].mean()) if gy + 9 + k < ch.shape[0] else 0.0 for k in range(reach)]
    out['west'] = [float(ch[rows_b, t_col - 9 - k].mean()) for k in range(reach)]
    out['east'] = [float(ch[rows_b, t_col + 9 + k].mean()) for k in range(reach)]
    return out


def _pool_character(rgb):
    """G-29's measure of a torch pool in a picture: the median and 90th percentile OKLCH chroma of its texels (all
    but the slate shade round it) and the share of its darkest 15 % that stay violet (hue 290 to 350)."""
    L, C, h = _oklch(rgb)
    lit = (L >= 0.25) & ~((h >= 250) & (h <= 300))
    d = lit & (L <= np.quantile(L[lit], 0.15))
    return float(np.median(C[lit])), float(np.quantile(C[lit], 0.9)), float(np.mean((h[d] >= 290) & (h[d] <= 350)))


def _knots(rgb):
    """G-31: small fully dark 2 x 2 blocks in the joint colours, alone (not part of a dark area)."""
    from scipy import ndimage as ndi
    c = rgb[..., :3].astype(int)
    dark = np.zeros(c.shape[:2], bool)
    for cc in ((37, 35, 64), (44, 36, 51), (32, 25, 59)):
        dark |= (np.abs(c - np.array(cc)).sum(2) == 0)
    b = dark[:-1, :-1] & dark[1:, :-1] & dark[:-1, 1:] & dark[1:, 1:]
    return int(ndi.label(b & (ndi.uniform_filter(dark.astype(float), 6)[:-1, :-1] < 0.4))[1])


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


class LightColourAndDrawing(unittest.TestCase):
    """Round 5's audit (G-24, G-26) on the committed floor, each with round 5's picture as the failing fixture."""

    SHADE_BOXES = ((200, 430, 310, 512), (250, 380, 387, 490), (300, 360, 520, 520), (1290, 450, 1440, 570))

    def test_the_torchlight_is_light_on_stone(self):
        # G-29 (Claude A's round 7 ruling): light on stone, its darkest texels violet, never a rug: the pool's median
        # OKLCH C at most 0.05. G-32 (round 8): its heart glows at Eastward 06's floor by a fire bowl (C 0.07 to 0.08),
        # so its top tenth reaches C 0.055. Round 5's pools were grey (C 0.018 throughout); round 6's an ochre rug
        # (median C 0.063, the darkest texels ochre): both fail
        g = _rgba('ground')[..., :3]
        for (x0, y0, x1, y1) in ((60, 168, 300, 300), (640, 312, 850, 420), (1760, 168, 1950, 300)):
            with self.subTest(box=(x0, y0, x1, y1)):
                C, p90, violet = _pool_character(g[y0:y1, x0:x1])
                self.assertLessEqual(C, 0.05, C)
                self.assertGreaterEqual(p90, 0.055, p90)
                self.assertGreaterEqual(violet, 0.8)
        for name in ('undercroft_r5_pool.png', 'undercroft_r6_pool.png'):
            a = np.asarray(Image.open(os.path.join(FIXTURES, name)).convert('RGB'))
            C, p90, violet = _pool_character(a)
            self.assertFalse(C <= 0.05 and p90 >= 0.055 and violet >= 0.8, name)

    def test_the_wall_light_is_whole_blocks(self):
        # G-33 (round 8): the face round each cup carries the lamp's colour in whole blocks (mean OKLCH C 0.035 or
        # more within 0.3 H), never a 2 x 2 checker. Round 7's staged wall light drew 194 checkers by torch 1 at
        # C 0.014; round 6's wall held no warm texel
        g = _rgba('ground')[..., :3]
        plan = json.load(open(os.path.join(ROOT, 'game', 'data', 'plans', 'undercroft.json')))
        for tx, ty in plan['torches']:
            with self.subTest(torch=tx):
                c, chk = _wall_light(g, 3 * tx, 3 * (ty - 16))
                self.assertGreaterEqual(c, 0.035)
                self.assertLessEqual(chk, 4)
        a, _, cx, foot = _r7_torch1()
        c, chk = _wall_light(a, cx, foot - 48)
        self.assertFalse(c >= 0.035 and chk <= 4, (c, chk))
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r6_wall.png')).convert('RGB'))
        self.assertLess(_wall_light(a, 48, 30)[0], 0.035)

    def test_no_knots_at_the_junctions(self):
        # G-31: round 6's shade held a dark 2 x 2 knot at most of its junctions
        g = _rgba('ground')[..., :3]
        self.assertLess(_knots(g[380:490, 250:387]), 10)
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r6_shade.png')).convert('RGB'))
        self.assertGreater(_knots(a), 40)

    def test_the_round5_pool_was_grey(self):
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r5_pool.png')).convert('RGB'))
        self.assertLess(_warm_light(a)[0], 0.045)

    def test_the_round5_heart_was_ruled(self):
        # round 5's hearts: whole lit flags, L 0.51, cut on the joints
        from scipy import ndimage as ndi
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r5_pool.png')).convert('RGB'))
        L = _oklab_L(a)
        heart = ndi.binary_opening((L >= 0.48) & (a[..., 0].astype(int) > a[..., 2]), np.ones((3, 3)))
        keep = np.zeros(heart.shape, bool)
        keep[22:-2, 2:-2] = True                                 # off the wall's foot and the box's edge
        self.assertGreater(_straight_share(heart, keep), 0.30)

    def test_the_shade_is_drawn(self):
        # G-26: the ground band's drawn test (tones and shapes a patch) on the audit's four shade boxes, and the skylight's
        from scripts.review.bands import ground_plane
        g = _rgba('ground')
        for (x0, y0, x1, y1) in self.SHADE_BOXES + ((1900, 300, 2051, 423),):
            with self.subTest(box=(x0, y0, x1, y1)):
                c = g[y0:y1, x0:x1]
                r = ground_plane(c, np.ones(c.shape[:2], bool), 74)
                self.assertTrue(r['drawn'], r['ours'])
                self.assertTrue(r['calm'], r['contrast'])

    def test_the_round5_shade_was_not_drawn(self):
        from scripts.review.bands import ground_plane
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r5_shade.png')).convert('RGBA'))
        self.assertFalse(ground_plane(a, np.ones(a.shape[:2], bool), 74)['drawn'])

    def test_no_colour_holds_half_a_shade_box(self):
        g = _rgba('ground')[..., :3]
        for (x0, y0, x1, y1) in self.SHADE_BOXES:
            _, cnt = np.unique(g[y0:y1, x0:x1].reshape(-1, 3), axis=0, return_counts=True)
            self.assertLessEqual(cnt.max() / cnt.sum(), 0.40)
        a = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r5_shade.png')).convert('RGB'))
        _, cnt = np.unique(a.reshape(-1, 3), axis=0, return_counts=True)
        self.assertGreater(cnt.max() / cnt.sum(), 0.40)               # round 5's: one fill a flag


class OverlayLoneSplit(unittest.TestCase):
    """Claude A's C-8 ruling (round 9): a floor overlay that copies the ground is judged in two parts, its texels
    identical to the ground at the same place against the ground's 2 %, its own against the drawn pictures' 1 %."""

    def _pics(self, own, copied):
        rng = np.random.default_rng(3)
        g = np.zeros((60, 60, 4), np.uint8)
        g[..., :3] = (60, 60, 90)
        g[..., 3] = 255
        o = g.copy()
        o[..., :3] = (90, 70, 120)
        cells = [(y, x) for y in range(4, 56, 3) for x in range(4, 56, 3)]
        idx = rng.permutation(len(cells))
        n = 56 * 56
        k_own, k_copy = int(round(own * n)), int(round(copied * n))
        for y, x in [cells[i] for i in idx[:k_own]]:
            o[y, x, :3] = (200, 180, 150)
        for y, x in [cells[i] for i in idx[k_own:k_own + k_copy]]:
            g[y, x, :3] = (30, 30, 40)
            o[y, x, :3] = (30, 30, 40)
        return Image.fromarray(o, 'RGBA'), Image.fromarray(g, 'RGBA')

    def test_a_prop_with_its_own_lone_pixels_still_fails(self):
        from scripts.art.native import raster
        o, g = self._pics(0.015, 0.0)
        own, same = raster.lone_split(o, g, 0, 0)
        self.assertGreater(own, 0.01)

    def _lifted(self, fam_o, tone_shift, n_lone=60):
        """A ground of slate 1 with lone slate 2 marks, and an overlay of the ground lifted a tone (slate 2, marks slate 3)
        whose marks are drawn on `fam_o` `tone_shift` tones over the ground's."""
        from scripts.art.native import palette as PAL
        g = np.zeros((60, 60, 4), np.uint8)
        g[..., :3] = PAL.rgb('slate', 1)
        g[..., 3] = 255
        o = g.copy()
        o[..., :3] = PAL.rgb('slate', 2)
        cells = [(y, x) for y in range(4, 56, 3) for x in range(4, 56, 3)][:n_lone]
        for y, x in cells:
            g[y, x, :3] = PAL.rgb('slate', 2)
            o[y, x, :3] = PAL.rgb(fam_o, 2 + tone_shift)
        return Image.fromarray(o, 'RGBA'), Image.fromarray(g, 'RGBA')

    def test_the_grounds_marks_lifted_a_rung_count_as_copied(self):
        from scripts.art.native import raster
        o, g = self._lifted('slate', 1)
        own, same = raster.lone_split(o, g, 0, 0, lift=1)
        self.assertLessEqual(own, 0.01)
        self.assertGreater(same, 0.01)

    def test_marks_of_another_family_or_lift_are_the_overlays_own(self):
        from scripts.art.native import raster
        for fam, shift in (('dusk', 1), ('slate', 2)):
            with self.subTest(family=fam, shift=shift):
                o, g = self._lifted(fam, shift)
                own, same = raster.lone_split(o, g, 0, 0, lift=1)
                self.assertGreater(own, 0.01)

    def test_the_grounds_own_marks_count_against_the_ground(self):
        from scripts.art.native import raster
        o, g = self._pics(0.004, 0.012)
        own, same = raster.lone_split(o, g, 0, 0)
        self.assertLessEqual(own, 0.01)
        self.assertTrue(0.01 < same <= 0.02, same)
        self.assertGreater(raster.lone_share(o), 0.01)              # (judged whole, it would fail)


class SceneUnmoved(unittest.TestCase):
    def test_pictures_keep_the_scenes_sizes_and_feet(self):
        # the sizes the scene was written for (undercroft.tscn offsets = -anchor from kit.json); round 3 changed
        # only channel_lit, with its offset, in the scene
        sizes = {'cairn_alcove': (108, 100), 'channel_lit': (260, 155), 'lever_down': (54, 72), 'lever_up': (54, 72),
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
        self.assertEqual(offs['channel_lit'], (-10, -124))         # round 3: the overlay lights the lips; round 6 grows it south only


class ChannelSpill(unittest.TestCase):
    """C-6: the lit channel lights 0.25 to 0.35 H (18 to 26 texels) of real floor on both sides of the main run
    and of the branch, measured by a composite diff on floor texels only, past the groove's lips."""

    def _check(self, sp):
        for side in ('north', 'south', 'west', 'east'):
            v = sp[side]
            with self.subTest(side=side):
                self.assertGreater(np.mean(v[0:6]), 0.8, v)            # 18 to 26 texels (0.25 to 0.35 H) of floor
                self.assertGreater(np.mean(v[6:14]), 0.35, v)
                self.assertGreater(np.mean(v[14:18]), 0.05, v)
                self.assertLess(np.mean(v[24:30]), 0.05, v)          # and no further
                self.assertGreater(np.mean(v[0:6]), np.mean(v[14:18]))

    def test_the_lit_channel_lights_the_floor_round_it(self):
        g = _rgba('ground')
        floor = g[284:284 + 155, 1430:1430 + 260]                   # under the overlay (its offset in kit.json)
        self._check(_spill(floor, _rgba('channel_lit')))

    def test_the_round5_spill_reached_two_rows(self):
        floor = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r5_channel_floor.png')).convert('RGBA'))
        ov = np.asarray(Image.open(os.path.join(FIXTURES, 'undercroft_r5_channel_lit.png')).convert('RGBA'))
        sp = _spill(floor, ov)
        self.assertLess(np.mean(sp['north'][2:10]), 0.05, sp['north'])
        self.assertLess(np.mean(sp['south'][0:8]), 0.05, sp['south'])


if __name__ == '__main__':
    unittest.main()

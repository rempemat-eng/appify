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
        for tint in ('tint_warm', 'tint_cool'):
            heart = (f['rung'] >= U.FLOOR_AMBIENT + 2) & f['paint'] & f[tint]       # its texels (a staged dither)
            curve = (f['light'] >= U.FLOOR_AMBIENT + 1.5) & f['paint'] & f[tint]    # the light's curve it follows
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

    def test_the_torchlight_is_gold(self):
        # Eastward 06's floor by the fire: OKLCH C 0.062 at hue 65; round 5's pools were C 0.018 (greige)
        g = _rgba('ground')
        for (x0, y0, x1, y1) in ((60, 150, 211, 273), (700, 312, 851, 400), (1800, 168, 1950, 260)):
            C, h, n = _warm_light(g[y0:y1, x0:x1])
            self.assertGreater(n, 500)
            self.assertGreaterEqual(C, 0.045)
            self.assertTrue(55 <= h <= 80, h)

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

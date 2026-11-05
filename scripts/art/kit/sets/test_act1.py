"""The Act 1 set (scripts/art/kit/sets/act1.py), its coast ground (sets/coast.py) and its two studies
(sets/act1_study.py): the pictures are what the painters draw, every piece carries what the rules
read, the loops are finite and hold frame 0, the pictures are clean (tone_audit), and both studies
stay at 0 faults on every rule check."""
from __future__ import annotations

import glob
import json
import os
import unittest

import numpy as np
from PIL import Image

from scripts.art.kit.schema import ROOT

IDX = os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')
PURPOSES = ('contain', 'cross', 'water', 'live', 'mark', 'rest', 'guide', 'store', 'light', 'grow', 'work')


def _img(res):
    return np.asarray(Image.open(os.path.join(ROOT, 'game', res[len('res://'):])).convert('RGBA'))


class Act1Set(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from scripts.art.kit import enclosures as EN
        from scripts.art.kit.sets import act1 as A
        from scripts.art.kit.sets import act1_study as AS
        cls.A, cls.AS = A, AS
        cls.lib = EN.library()
        with open(IDX) as f:
            cls.idx = json.load(f)
        cls.ids = [pid for pid, _v, _k in A.jobs()]
        cls.plans = AS.plans()

    def test_pictures_are_what_the_painters_draw(self):
        self.assertEqual(self.A.check(), 0)

    def test_every_piece_carries_what_the_rules_read(self):
        self.assertGreaterEqual(len(self.ids), 15)
        for pid in self.ids:
            p = self.lib[pid]
            pl = p['placement']
            self.assertIn(pl['purpose'], PURPOSES, pid)
            self.assertTrue(pl.get('role'), pid)
            self.assertTrue(pl.get('requires') or pl.get('forbids'), pid)
            self.assertIn('collision', p['geometry'], pid)
            self.assertIn(pid, self.idx, pid)
            self.assertEqual(p['approval']['state'], 'candidate', pid)
            self.assertTrue(p['audit']['eastward_ref'], pid)

    def test_loops_are_finite_and_hold_frame_0(self):
        loops = [pid for pid in self.ids if self.idx[pid].get('anim')]
        self.assertEqual(sorted(loops), ['coast_buoy', 'coast_harbour_light', 'halt_platform_lamp', 'mill_wheel'])
        for pid in loops:
            an = self.idx[pid]['anim']
            self.assertEqual(an['frames'], 8, pid)
            self.assertEqual(an['reduced_motion'], 'hold:0', pid)
            strip = _img(an['strip'])
            w = strip.shape[1] // an['frames']
            still = _img(next(iter(self.idx[pid]['variants'].values()))['png'])
            np.testing.assert_array_equal(strip[:, :w], still)          # the strip replaces the still
            self.assertFalse(all(np.array_equal(strip[:, :w], strip[:, k * w:(k + 1) * w]) for k in range(1, 8)), pid)
            with open(os.path.join(ROOT, 'game', 'kit', 'props', pid + '.tscn')) as f:
                text = f.read()
            self.assertIn('res://world/loop_fx.gd', text)
            self.assertIn('hframes = 8', text)

    def test_platform_cells_meet(self):
        # two platform cells side by side, as the zone draws them by foot: no open column between
        e = self.idx['halt_platform_edge']['variants']
        canvas = np.zeros((60, 24 * 4, 4), np.uint8)
        for k, vid in enumerate(('a', 'b', 'a')):
            im = _img(e[vid]['png'])
            fx, fy = e[vid]['foot']
            x0, y0 = 12 + 24 * k - int(fx), 50 - int(fy)
            sub = canvas[y0:y0 + im.shape[0], x0:x0 + im.shape[1]]
            m = im[..., 3] > 0
            sub[m] = im[m]
        self.assertTrue((canvas[50 - 12:50 - 2, 12:12 + 48, 3] > 0).all(), 'a column of the platform front is open')

    def test_no_picture_is_speckled(self):
        from scripts.art.kit import tone_audit as TA
        for p in sorted(glob.glob(os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'act1', '*.png'))):
            r = TA.measure(p)
            self.assertLessEqual(r['isolated'], TA.ISOLATED_MAX, os.path.basename(p))
            self.assertLessEqual(r['specks'], TA.SPECKS_MAX, os.path.basename(p))

    def test_every_picture_meets_its_own_size_spec(self):
        # the detail audit of 4 Nov: the shelter at a third of its height, the millstones at 0.74 m of
        # their 1.2 m, the barrow's portal a third of its own size; each piece now states its box in art
        # px and every picture is measured against it (scripts/review/scale.py, check_spec)
        from scripts.review import scale as SZ
        for pid in self.ids:
            spec = self.lib[pid]['audit']['size_class']
            self.assertTrue(SZ.spec_ranges(spec), '%s states no art px box: %s' % (pid, spec))
            for vid, v in self.idx[pid]['variants'].items():
                self.assertEqual([f.message for f in SZ.check_spec(_img(v['png']), spec, pid + '/' + vid)], [])

    def test_the_set_is_calm(self):
        # finding 4: random 2 x 2 value grain (the set's median was 44.8 % of blocks at 8f560abf, against
        # Eastward's 29 % and the anchors' 28 to 30 %); the grain is now sibling swaps and form-tied steps
        from scripts.review import cluster_noise as CN
        shares = []
        for pid in self.ids:
            for v in self.idx[pid]['variants'].values():
                a = _img(v['png'])
                shares.append(CN.share(a[..., :3], a[..., 3] > 128)[0])
        # (R7-6) the share is now the mean of the 2 x 2 grid's four phases, which reads thin pieces
        # higher: the same 27 pictures at d13634b8 measure a median of 36.6 % on one grid and 40.3 % as
        # the mean, so the cap moved from 40 to 42 % with no picture changed
        self.assertLessEqual(float(np.median(shares)), 0.42)
        self.assertLessEqual(max(shares), 0.60)

    def test_the_wheel_loop_wraps_at_an_even_step(self):
        # finding 19: frame 8 to frame 1 changed 2557 px against 1560 to 1680 for the other steps
        an = self.idx['mill_wheel']['anim']
        strip = _img(an['strip'])
        w = strip.shape[1] // an['frames']
        fr = [strip[:, k * w:(k + 1) * w] for k in range(an['frames'])]
        steps = [int((fr[k] != fr[(k + 1) % len(fr)]).any(-1).sum()) for k in range(len(fr))]
        self.assertLessEqual(max(steps), 1.25 * float(np.median(steps)), steps)

    def test_the_barrow_can_be_entered(self):
        # finding 8: the portal at least 40 x 74 art px (the door class), the mound 300 or more long
        g = self.lib['barrow_entrance']['geometry']
        x0, x1 = g['doors'][0]['x']
        self.assertGreaterEqual(x1 - x0, 40)
        a = _img(next(iter(self.idx['barrow_entrance']['variants'].values()))['png'])
        self.assertGreaterEqual(a.shape[1], 300)

    def test_the_studies_pass_every_check(self):
        for p in self.plans:
            self.assertEqual(self.AS.faults(p), [], p['zone'])

    def test_the_studies_use_every_piece_of_the_set(self):
        used = {pc['piece'] for p in self.plans for pc in p['pieces']}
        self.assertEqual(set(self.ids) - used, set())

    def test_misplaced_pieces_are_caught(self):
        import copy
        q = copy.deepcopy(self.plans[0])
        for x in q['pieces']:
            if x['id'] == 'buoy_1':
                x['at'] = [6 * 24 + 12, 6 * 24]                         # a buoy up on the quay
        self.assertTrue(any(m.startswith('relations: buoy_1') for m in self.AS.faults(q)))
        q = copy.deepcopy(self.plans[1])
        for x in q['pieces']:
            if x['id'] == 'kerb_1':
                x['at'] = [40 * 24 + 12, 2 * 24]                        # a kerb stone far from its barrow
        self.assertTrue(any(m.startswith('relations: kerb_1') for m in self.AS.faults(q)))

    def test_the_coast_ground_is_additive(self):
        from scripts.art.kit import bake as BK
        lib = BK._pieces_lib()
        for m in ('shingle', 'quay'):
            self.assertIn(m, lib)
            self.assertEqual(lib[m]['terrain']['paint']['fn'], 'dirt', m)    # baked by the kit's own earth painter
        self.assertFalse(lib['quay']['terrain']['route'])                      # a quay meets water: not a route

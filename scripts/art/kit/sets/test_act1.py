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
                x['at'] = [36 * 24 + 12, 2 * 24]                        # a kerb stone far from its barrow
        self.assertTrue(any(m.startswith('relations: kerb_1') for m in self.AS.faults(q)))

    def test_the_coast_ground_is_additive(self):
        from scripts.art.kit import bake as BK
        lib = BK._pieces_lib()
        for m in ('shingle', 'quay'):
            self.assertIn(m, lib)
            self.assertEqual(lib[m]['terrain']['paint']['fn'], 'dirt', m)    # baked by the kit's own earth painter
        self.assertFalse(lib['quay']['terrain']['route'])                      # a quay meets water: not a route

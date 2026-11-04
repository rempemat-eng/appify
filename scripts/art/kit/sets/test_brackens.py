"""The Brackens set (scripts/art/kit/sets/brackens.py) and its study: the pictures are what the
painters draw, the pieces carry what the editor's rules read, the wall cells tile without a gap, the
loops are finite and hold frame 0, and the study built from kit pieces stays at 0 faults.

    python3 -m unittest scripts.art.kit.sets.test_brackens      (run by check:review through test_kit)
"""
from __future__ import annotations

import json
import os
import unittest

import numpy as np
from PIL import Image

from scripts.art.kit.schema import ROOT

IDX = os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')


def _img(res):
    return np.asarray(Image.open(os.path.join(ROOT, 'game', res[len('res://'):])).convert('RGBA'))


class BrackensSet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from scripts.art.kit import enclosures as EN
        from scripts.art.kit.sets import brackens as B
        from scripts.art.kit.sets import brackens_study as BS
        cls.B, cls.BS, cls.EN = B, BS, EN
        cls.lib = EN.library()
        cls.idx = json.load(open(IDX))
        cls.ids = [pid for pid, _v, _k in B.jobs()]
        cls.plan = BS.plan()
        cls.lab = BS.wall_lab()

    def test_pictures_are_what_the_painters_draw(self):
        self.assertEqual(self.B.check(), 0)

    def test_every_piece_carries_what_the_rules_read(self):
        for pid in self.ids:
            p = self.lib[pid]
            pl = p['placement']
            self.assertIn(pl['purpose'], ('contain', 'cross', 'water', 'live', 'mark', 'rest', 'guide', 'store', 'light', 'grow'), pid)
            self.assertTrue(pl.get('role'), pid)
            self.assertTrue(pl.get('requires') or pl.get('forbids'), pid)
            self.assertIn('collision', p['geometry'], pid)
            self.assertEqual(len(p['geometry']['size_px']), 2, pid)
            self.assertIn(pid, self.idx, pid)
            self.assertEqual(p['approval']['state'], 'candidate', pid)

    def test_wall_cells_close_loops_and_keep_sheep(self):
        # every way a cell can join: straights, corners, Ts, the cross and the ends
        for jn in ('ew', 'ns', 'es', 'sw', 'ne', 'nw', 'nes', 'esw', 'nsw', 'new', 'nesw', 'n', 'e', 's', 'w'):
            b = self.lib['wall_drystone_' + jn]['placement']['boundary']
            self.assertEqual(''.join(b['joins']), jn)
            self.assertIn('sheep', b['encloses'])
        for gid, joins in (('wall_drystone_gate_ew', ['e', 'w']), ('wall_drystone_gate_ns', ['n', 's'])):
            g = self.lib[gid]
            self.assertTrue(g['placement']['boundary']['gate'], gid)
            self.assertEqual(sorted(g['placement']['boundary']['joins']), sorted(joins), gid)
            self.assertFalse(g['gameplay']['blocks_move'], gid)
        st = self.lib['wall_drystone_stile_ew']
        self.assertFalse(st['placement']['boundary']['gate'])           # the flock stays behind it
        self.assertTrue(st['placement']['boundary']['stile'])
        self.assertFalse(st['gameplay']['blocks_move'])                  # walkers cross
        self.assertIn('route', [r['what'] for r in st['placement']['requires']])

    def test_a_run_of_straights_has_no_gap(self):
        # three straight cells side by side, as the zone draws them by foot: every column of the run
        # covered from the foot of the wall to the top of the coping, nothing open between the cells
        e = self.idx['wall_drystone_ew']['variants']
        W = 24 * 3
        canvas = np.zeros((90, W + 48, 4), np.uint8)
        for k, vid in enumerate(('a', 'b', 'a')):
            im = _img(e[vid]['png'])
            fx, fy = e[vid]['foot']
            x0, y0 = 24 + 12 + 24 * k - int(fx), 80 - int(fy)
            sub = canvas[y0:y0 + im.shape[0], x0:x0 + im.shape[1]]
            m = im[..., 3] > 0
            sub[m] = im[m]
        body = canvas[80 - 38:80 - 4, 24 + 12:24 + 12 + 48, 3] > 0     # foot node to foot node: the wall's face
        self.assertTrue(body.all(), 'a column of the wall face is open between cells')

    def test_loops_are_finite_and_hold_frame_0(self):
        for pid in ('brackens_drove_well', 'brackens_fire_ring_lit', 'brackens_shepherds_hut'):
            an = self.idx[pid]['anim']
            self.assertEqual(an['frames'], 8, pid)
            self.assertEqual(an['reduced_motion'], 'hold:0', pid)
            strip = _img(an['strip'])
            w = strip.shape[1] // an['frames']
            self.assertEqual(strip.shape[1], w * 8, pid)
            with open(os.path.join(ROOT, 'game', 'kit', 'props', pid + '.tscn')) as f:
                text = f.read()
            self.assertIn('res://world/loop_fx.gd', text)
            self.assertIn('hframes = 8', text)
            if an['cover']:
                # the strip replaces the still: its first frame is the still
                still = _img(next(iter(self.idx[pid]['variants'].values()))['png'])
                np.testing.assert_array_equal(strip[:, :w], still)
            else:
                # the smoke lies over the still, which has none where it plays
                self.assertGreater((strip[:, :w, 3] > 0).sum(), 0)

    def test_the_study_passes_every_check(self):
        from scripts.art.kit import relations as RL
        from scripts.review import kit_rules as KR
        self.assertEqual([f for f in KR.check_zone(self.plan) if f['severity'] == 'fault'], [])
        self.assertEqual(RL.check_zone(self.plan), [])
        self.assertEqual(self.EN.check_zone(self.plan, self.lib), [])
        self.assertEqual(self.BS.layout_faults(self.plan), [])
        from scripts.art.kit import placement_audit as PA
        self.assertEqual(PA.check_plan(self.plan), [])                  # needs (the peat's hearth), faces, avoid, points

    def test_the_wall_lab_passes_every_check(self):
        # the yard of four folds (corners, Ts, the cross, gates along x and y) and the walls ending
        # against houses (the end cells), checked as a zone is
        from scripts.art.kit import relations as RL
        from scripts.review import kit_rules as KR
        from scripts.art.kit import placement_audit as PA
        self.assertEqual([f for f in KR.check_zone(self.lab) if f['severity'] == 'fault'], [])
        self.assertEqual(RL.check_zone(self.lab), [])
        self.assertEqual(self.EN.check_zone(self.lab, self.lib), [])
        self.assertEqual(self.BS.layout_faults(self.lab), [])
        self.assertEqual(PA.check_plan(self.lab), [])

    def test_every_fold_in_the_lab_has_its_own_gate(self):
        # Claude A, round 5: each of the yard's four pens is its own enclosure and needs its own gate;
        # take any one gate away and enclosures names that pen
        import copy
        for gid in ('gate_x', 'gate_y', 'gate_y_ne', 'gate_y_nw'):
            q = copy.deepcopy(self.lab)
            q['pieces'] = [x for x in q['pieces'] if x['id'] != gid]
            msgs = [f['message'] for f in self.EN.check_zone(q, self.lib)]
            self.assertTrue(any('has no gate' in m or 'meets no run' in m for m in msgs), gid)

    def test_every_door_has_a_path_straight_out(self):
        # each door's cells, one row out from the foot, are a route (a path or the road)
        for p in (self.plan, self.lab):
            legend = p['legend']
            from scripts.art.kit import bake as BK
            mats = BK._pieces_lib()
            for pc in p['pieces']:
                dc = (self.lib[pc['piece']].get('geometry') or {}).get('door_cells')
                if not dc:
                    continue
                x, y = pc['at']
                for dx, dy in dc:
                    c, r = int(x // 24) + dx, int(y // 24) + dy
                    mat = legend[p['rows'][r][c]]
                    self.assertTrue(mats[mat]['terrain'].get('route'), '%s: door cell %s is %s' % (pc['id'], (c, r), mat))

    def test_the_study_and_the_lab_use_every_piece_of_the_set(self):
        used = {pc['piece'] for pc in self.plan['pieces'] + self.lab['pieces']}
        self.assertEqual(set(self.ids) - used, set())

    def test_the_study_stands_on_moor(self):
        legend = set(self.plan['legend'].values())
        self.assertTrue({'heath', 'peat', 'drove'} <= legend)
        for m in ('heath', 'peat', 'drove'):
            self.assertIn(m, self.lib_terrain(), m)

    def lib_terrain(self):
        from scripts.art.kit import bake as BK
        return {k for k, v in BK._pieces_lib().items() if v.get('terrain')}

    def test_no_picture_is_speckled(self):
        # Claude A, round 2: clean 2 to 4 px clusters, isolated pixels at 4 % or less, runs of 3 or
        # fewer at 15 % or less (scripts/art/kit/tone_audit.py), every still and every loop strip
        import glob
        from scripts.art.kit import tone_audit as TA
        for p in sorted(glob.glob(os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'brackens', '*.png'))):
            r = TA.measure(p)
            self.assertLessEqual(r['isolated'], TA.ISOLATED_MAX, os.path.basename(p))
            self.assertLessEqual(r['specks'], TA.SPECKS_MAX, os.path.basename(p))

    def test_open_folds_and_misplaced_pieces_are_caught(self):
        import copy
        from scripts.art.kit import relations as RL
        q = copy.deepcopy(self.plan)
        q['pieces'] = [x for x in q['pieces'] if x['id'] != 'fold_10_8']
        self.assertTrue(any('meets no run' in f['message'] for f in self.EN.check_zone(q, self.lib)))
        q = copy.deepcopy(self.plan)
        for x in q['pieces']:
            if x['id'] == 'cairn':
                x['at'] = [372, 144]                 # out in the heather, far from any way
        self.assertTrue(any(f['message'].startswith('cairn:') for f in RL.check_zone(q)))
        from scripts.art.kit import placement_audit as PA
        q = copy.deepcopy(self.plan)
        q['pieces'] = [x for x in q['pieces'] if x['id'] != 'cairn_toppled']
        self.assertTrue(any('seat: faces' in f['message'] for f in PA.check_plan(q)))
        from scripts.art.kit import placement_audit as PA
        q = copy.deepcopy(self.plan)
        q['pieces'] = [x for x in q['pieces'] if x['id'] != 'hut']
        self.assertTrue(any('needs a hearth' in f['message'] for f in PA.check_plan(q)))
        q = copy.deepcopy(self.plan)
        q['pieces'] = [x for x in q['pieces'] if x['id'] != 'trough']
        self.assertTrue(any('no trough' in f['message'] for f in self.EN.check_zone(q, self.lib)))


if __name__ == '__main__':
    unittest.main()

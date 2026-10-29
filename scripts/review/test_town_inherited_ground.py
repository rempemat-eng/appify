"""Physical checks shared by authored and inherited town footprints.

Uses the real check_plan entry point with small literal terrain windows; no map
producer, historical terrain reconstruction or renderer is involved.
"""
import copy
import unittest

from scripts.review.town_plan import check_plan


def building(identifier='built', inherited=True, footprint=None):
    cells = footprint or [2, 2, 2, 2]
    c, r, w, h = cells
    return {'id': identifier, 'type': 'cottage', 'form': 'cottage',
            'from_zone_plan': inherited, 'footprint_cells': cells,
            'rect_px': [c * 8, r * 8, w * 8, h * 8], 'counted': True,
            'counts_as': 1, 'door_cells': [c, r + h], 'faces': 'zone-road'}


def plan(buildings=None, origin=(0, 0)):
    buildings = buildings if buildings is not None else [building()]
    c, r = origin
    return {'id': 'physical-fixture', 'terrain': {'box_cells': [c, r, 12, 12],
            'rows': ['12.'] * 12}, 'streets': [], 'squares': [],
            'buildings': buildings, 'size': 'small', 'target': [1, 4],
            'buildings_counted': len(buildings), 'arrivals': [], 'site': {},
            'game_layout': {'landmarks': []}, 'footprint_px': [c*8, r*8, (c+12)*8, (r+12)*8],
            'size_table_px': {'cottage': [[16, 32], [16, 32]]},
            'theme': {'waystone': {'xy_px': [(c+8)*8, (r+8)*8]},
                      'sightline': {}, 'crater': {}, 'moss': {}, 'company': {}, 'tech': {}}}


def terrain_cell(p, c, r, value):
    # The fixture begins as one run per row; expand only this literal row.
    c0, r0, w, _ = p['terrain']['box_cells']
    p['terrain']['rows'][r-r0] = '.' * (c-c0) + value + '.' * (w-(c-c0)-1)


class InheritedGround(unittest.TestCase):
    def findings(self, p):
        before = copy.deepcopy(p)
        result = check_plan(p, {})
        self.assertEqual(p, before, 'checking must not mutate the input')
        return result[0]

    def test_dry_inherited_footprint_passes_and_count_is_preserved(self):
        p = plan()
        self.assertEqual(self.findings(p), [])
        _, notes, count = check_plan(p, {})
        self.assertEqual(count, 1)
        self.assertTrue(any('built zone' in n for n in notes))

    def test_inherited_water_is_rejected_at_every_footprint_cell(self):
        for c in (2, 3):
            for r in (2, 3):
                with self.subTest(cell=(c, r)):
                    p = plan(); terrain_cell(p, c, r, '~')
                    self.assertIn('off_water: building built stands on water', self.findings(p))

    def test_inherited_barrier_is_rejected(self):
        p = plan(); terrain_cell(p, 3, 3, '#')
        self.assertIn('off_water: building built stands on a barrier', self.findings(p))

    def test_inherited_pairs_overlap_in_both_orders(self):
        for reverse in (False, True):
            bs = [building('a'), building('b', footprint=[3, 3, 2, 2])]
            if reverse: bs.reverse()
            with self.subTest(reverse=reverse):
                self.assertTrue(any('overlaps another building' in f for f in self.findings(plan(bs))))

    def test_mixed_pairs_overlap_in_both_orders(self):
        for reverse in (False, True):
            bs = [building('inherited'), building('authored', False, [3, 3, 2, 2])]
            if reverse: bs.reverse()
            with self.subTest(reverse=reverse):
                self.assertTrue(any('overlaps another building' in f for f in self.findings(plan(bs))))

    def test_touching_edges_do_not_overlap(self):
        self.assertEqual(self.findings(plan([building('a'), building('b', footprint=[4, 2, 2, 2])])), [])

    def test_every_outside_edge_and_wholly_outside_footprint_is_rejected(self):
        for cells in ([-1, 2, 2, 2], [11, 2, 2, 2], [2, -1, 2, 2],
                      [2, 11, 2, 2], [-4, 2, 2, 2], [14, 2, 2, 2]):
            with self.subTest(cells=cells):
                self.assertTrue(any('outside terrain bounds' in f for f in self.findings(plan([building(footprint=cells)]))))

    def test_fractional_and_empty_footprints_fail_without_crashing(self):
        for cells in ([2.5, 2, 2, 2], [2, 2, 0, 2], [2, 2, 2, -1]):
            with self.subTest(cells=cells):
                self.assertTrue(any(f.startswith('cells: building built') for f in self.findings(plan([building(footprint=cells)]))))

    def test_nonzero_terrain_origin_and_exact_boundary(self):
        p = plan([building(footprint=[20, 30, 2, 2])], (20, 30))
        self.assertEqual(self.findings(p), [])
        terrain_cell(p, 21, 31, '~')
        self.assertIn('off_water: building built stands on water', self.findings(p))
        self.assertEqual(self.findings(plan([building(footprint=[30, 40, 2, 2])], (20, 30))), [])

    def test_inherited_zone_keeps_road_and_door_authority(self):
        p = plan()
        p['streets'] = [{'id': 'town-road', 'class': 'arrival', 'width_cells': 2,
                         'vertices_px': [[0, 24], [80, 24]]}]
        p['buildings'][0]['door_cells'] = [100, 100]
        self.assertFalse(any(f.startswith(('off_streets:', 'reach:')) for f in self.findings(p)))

    def test_authored_buildings_still_check_roads_and_doors(self):
        p = plan([building(inherited=False)])
        p['streets'] = [{'id': 'town-road', 'class': 'arrival', 'width_cells': 2,
                         'vertices_px': [[0, 24], [80, 24]]}]
        fails = self.findings(p)
        self.assertTrue(any(f.startswith('off_streets:') for f in fails))
        self.assertTrue(any(f.startswith('reach:') for f in fails))

    def test_authored_water_and_barrier_checks_are_preserved(self):
        for value, description in (('~', 'water'), ('#', 'a barrier')):
            with self.subTest(value=value):
                p = plan([building(inherited=False)])
                terrain_cell(p, 3, 3, value)
                self.assertIn(f'off_water: building built stands on {description}', self.findings(p))

    def test_authored_bounds_and_overlap_are_preserved(self):
        p = plan([building('a', False), building('b', False, [3, 3, 2, 2])])
        self.assertTrue(any('overlaps another building' in f for f in self.findings(p)))
        p = plan([building(inherited=False, footprint=[11, 2, 2, 2])])
        self.assertTrue(any('outside terrain bounds' in f for f in self.findings(p)))

    def test_whole_number_float_coordinates_do_not_crash(self):
        self.assertEqual(self.findings(plan([building(footprint=[2.0, 2.0, 2.0, 2.0])])), [])

    def test_literal_road_bridge_and_grass_are_not_water_or_barrier(self):
        for value in ('r', 'b', 'g'):
            with self.subTest(value=value):
                p = plan(); terrain_cell(p, 2, 2, value)
                self.assertFalse(any(f.startswith('off_water:') for f in self.findings(p)))


if __name__ == '__main__':
    unittest.main()

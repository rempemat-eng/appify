"""W7 intake regressions; run with python3 -m unittest discover -s game/test/fixtures/kit."""
import copy
import unittest

from generate import pieces_in_texels, render, Kit


class PlanCoordinates(unittest.TestCase):
    def test_positions_only_and_no_mutation(self):
        plan = {'coordinate_space': 'cells', 'pieces': [
            {'piece': 'woodland_forest_bench', 'at': [-0.5, 1.25], 'variant': 'existing'}]}
        before = copy.deepcopy(plan)
        self.assertEqual(pieces_in_texels(plan, 24), [
            {'piece': 'woodland_forest_bench', 'at': [-12, 30], 'variant': 'existing'}])
        self.assertEqual(plan, before)
        for units in ('texels', None):
            if units:
                plan['coordinate_space'] = units
            else:
                plan.pop('coordinate_space')
            self.assertEqual(pieces_in_texels(plan, 24)[0]['at'], [-0.5, 1.25])

    def test_invalid_inputs(self):
        for at in (None, [], [1], [1, 2, 3], [True, 1], ['1', 1], [float('nan'), 1],
                   [float('inf'), 1], [1e100, 1], [2e37, 1]):
            with self.subTest(at=at), self.assertRaises(ValueError):
                pieces_in_texels({'coordinate_space': 'cells', 'pieces': [{'at': at}]}, 24)
        for units in ('meters', None, [], {}):
            with self.subTest(units=units), self.assertRaises(ValueError):
                pieces_in_texels({'coordinate_space': units}, 24)

    def test_equivalent_real_renders_and_visible_shadow(self):
        kit = Kit()
        plan = {'coordinate_space': 'cells', 'legend': {'g': 'lawn'}, 'rows': ['gggg'] * 4,
                'pieces': [{'piece': 'woodland_forest_bench', 'at': [1, 1]}]}
        texels = copy.deepcopy(plan)
        texels['coordinate_space'] = 'texels'
        texels['pieces'][0]['at'] = [24, 24]
        self.assertEqual(render(plan, kit).tobytes(), render(texels, kit).tobytes())
        self.assertNotEqual(render(plan, kit).tobytes(), render(plan, kit, shadows=False).tobytes())


if __name__ == '__main__':
    unittest.main()

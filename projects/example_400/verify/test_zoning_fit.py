"""400 Oak against arkitect/codes/columbus/fit.py, the shared zoning check a new address runs.

The massing is READ from src/sitework.py. Oak requests no variance; its one rule not met
is lot width, which it states as the lot split, and the check must find exactly that and
agree with the figures C-102 prints.
"""
import unittest

from projects.example_400.verify import enter, leave

ROWS = []


def setUpModule():
    enter()
    from arkitect.codes.columbus.fit import Massing, fit
    from src import sitework as S
    b1, b2 = S.SITE_BLDG
    x0, y0, x1, y1 = S.STAIR
    m = Massing(
        lot={'width': S.SITE_W, 'depth': S.SITE_D, 'corner': False, 'alley': True,
             'alley_width': S.ALLEY_W, 'front_line': S.FRONT_YARD},
        buildings=[{'name': b1[4], 'role': 'principal', 'x': b1[0], 'y': b1[1], 'width': b1[2],
                    'depth': b1[3], 'storeys': 2, 'height': S.PRINCIPAL_HEIGHT,
                    'dwellings': [{'name': 'UNIT 1', 'area_sf': S.PRINCIPAL_SF}]},
                   {'name': b2[4], 'role': 'adu', 'x': b2[0], 'y': b2[1], 'width': b2[2],
                    'depth': b2[3], 'storeys': 2, 'height': S.ADU_HEIGHT,
                    'dwellings': [{'name': 'UNIT 2', 'area_sf': S.ADU_SF},
                                  {'name': 'UNIT 3', 'area_sf': S.ADU_SF}]}],
        structures=[{'name': 'UNIT 3 STAIR', 'x': x0, 'y': y0, 'width': x1-x0, 'depth': y1-y0}],
        parking={'stalls': S.PARK_N, 'x0': S.PARK_X0, 'width': S.PARK_X1-S.PARK_X0, 'depth': S.PARK_D},
        relief={'lot_width': 'BY THE LOT SPLIT OF %s' % S.PARCEL})
    ROWS[:] = fit(m)


def tearDownModule():
    leave()


class ZoningFitTests(unittest.TestCase):

    def test_lot_width_is_the_one_rule_not_met_and_the_lot_split_is_its_basis(self):
        from arkitect.codes.columbus import fit
        self.assertEqual([r.rule for r in ROWS if r.ok is False], ['lot_width'])
        self.assertEqual(fit.failing(ROWS), [])

    def test_the_figures_agree_with_the_zoning_table(self):
        from src import sitework as S
        by = {r.rule: r for r in ROWS}
        self.assertEqual(by['rear_yard'].provided, '{:,.0f} SF'.format(S.REAR_PROV))
        self.assertIn('%.1f%%' % S.ADU_REAR_PCT, by['adu_share'].provided)
        self.assertIn('{:,.0f} SF'.format(S.COVERAGE), by['coverage'].provided)
        self.assertEqual(by['maneuvering'].status, 'MEETS')

    def test_nothing_is_left_unchecked_for_a_modelled_project(self):
        self.assertEqual([r.rule for r in ROWS if r.ok is None], [])


if __name__ == '__main__':
    unittest.main()

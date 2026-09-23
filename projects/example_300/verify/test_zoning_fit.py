"""300 S Elm against arkitect/codes/columbus/fit.py, the shared zoning check a new address runs.

The massing is READ from src/sitework.py, never typed, and the check must find exactly
the five rules this project asks the Board to vary -- section for section, the list
VARIANCES holds -- and agree with the figures C-102 prints. If the two disagree, either
the shared rule or this project's tabulation is wrong, and a new address would inherit
whichever one it is.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def massing():
    from arkitect.codes.columbus.fit import Massing
    from src import sitework as S
    from src.building1 import U3_LAND_LO, U3_STOOP_HI
    from src.building2 import U5_LAND_D, U5_LAND_X1, U5_STOOP_X0
    b1, b2 = S._B1, S._B2
    unit = lambda u: {'name': 'UNIT %d' % u, 'area_sf': S.NET_SF[u]}
    stair_x0, stair_x1 = S.SITE_STAIR
    return Massing(
        lot={'width': S.SITE_W, 'depth': S.SITE_D, 'corner': True, 'side_street': 'left',
             'alley': True, 'alley_width': S.ALLEY_W, 'front_line': b1[1],
             'side_street_line': S.SAFF_WALL_X},
        buildings=[{'name': b1[4], 'role': 'principal', 'x': b1[0], 'y': b1[1], 'width': b1[2],
                    'depth': b1[3], 'storeys': 2, 'height': S.PRINCIPAL_HEIGHT,
                    'dwellings': [unit(1), unit(2), unit(3)]},
                   {'name': b2[4], 'role': 'adu', 'x': b2[0], 'y': b2[1], 'width': b2[2],
                    'depth': b2[3], 'storeys': 2, 'height': S.ADU_HEIGHT,
                    'dwellings': [unit(4), unit(5)]}],
        structures=[{'name': 'UNIT 3 STAIR', 'x': stair_x0, 'y': b1[1]+U3_LAND_LO,
                     'width': stair_x1-stair_x0, 'depth': U3_STOOP_HI-U3_LAND_LO},
                    {'name': 'UNIT 5 STAIR', 'x': b2[0]+U5_STOOP_X0, 'y': b2[1]-U5_LAND_D,
                     'width': U5_LAND_X1-U5_STOOP_X0, 'depth': U5_LAND_D}],
        parking={'stalls': S.PARK_N, 'x0': S.PARK_X0, 'width': S.PARK_N*9.0, 'depth': S.PARK_D},
        relief={'lot_width': 'VARIANCE REQUESTED', 'parking': 'VARIANCE REQUESTED',
                'side_street': 'VARIANCE REQUESTED', 'maneuvering': 'VARIANCE REQUESTED',
                'street_vision': 'VARIANCE REQUESTED'})


class ZoningFitTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from arkitect.codes.columbus import fit
        cls.fit = fit
        cls.rows = fit.fit(massing())
        cls.by = {r.rule: r for r in cls.rows}

    def test_the_rules_not_met_are_exactly_the_variances_requested(self):
        from src.sitework import VARIANCES
        self.assertEqual({r.citation for r in self.rows if r.ok is False},
                         {sec for sec, _what in VARIANCES})

    def test_every_rule_not_met_states_its_relief(self):
        self.assertEqual(self.fit.failing(self.rows), [])

    def test_the_figures_agree_with_the_zoning_table(self):
        from src import sitework as S
        self.assertEqual(self.by['rear_yard'].provided, '{:,.0f} SF'.format(S.REAR_PROV))
        self.assertIn('%.1f%%' % S.ADU_REAR_PCT, self.by['adu_share'].provided)
        self.assertIn('{:,.0f} SF'.format(S.COVERAGE), self.by['coverage'].provided)
        self.assertIn('2\'-0"', self.by['street_vision'].note)       # C-102: 2'-0" inside

    def test_nothing_is_left_unchecked_for_a_modelled_project(self):
        self.assertEqual([r.rule for r in self.rows if r.ok is None], [])


if __name__ == '__main__':
    unittest.main()

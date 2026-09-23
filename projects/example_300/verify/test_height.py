"""Roof heights: the ridge on S-103's raised heel, and the height C.C. 3303.08 measures."""
import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class RoofHeightTests(unittest.TestCase):

    def test_the_ridge_stands_on_the_raised_heel(self):
        from lib.units import fmt
        from src import levels
        from src.roof import HEEL_NOM
        self.assertAlmostEqual(levels.EAVE, levels.ROOF_PLATE+HEEL_NOM)
        self.assertAlmostEqual(levels.ridge(26.0), levels.ROOF_PLATE+HEEL_NOM+13.0*levels.ROOF_PITCH)
        self.assertEqual((fmt(levels.EAVE), fmt(levels.ridge(26.0))), ('21\'-0-1/4"', '25\'-4-1/4"'))

    def test_height_is_the_mean_of_eave_and_ridge(self):
        from lib.units import fmt
        from src import levels
        self.assertAlmostEqual(levels.height(26.0), (levels.EAVE+levels.ridge(26.0))/2.0)
        self.assertEqual(fmt(levels.height(26.0)), '23\'-2-1/4"')

    def test_the_zoning_table_states_the_mean_and_what_it_is_the_mean_of(self):
        from src import sitework as s
        rows = dict(s.zoning_rows())
        self.assertEqual(rows['ADU height, 3332.355(B)(3)'], '23\'-2-1/4"  (25\'-0" MAX)')
        self.assertEqual(rows['  Mean of eave and ridge, 3303.08'], '21\'-0-1/4" / 25\'-4-1/4"')
        self.assertFalse(any('RIDGE' in v for v in rows.values()))

    def test_check_height_holds_the_adu_to_25_feet_and_the_principal_dwelling(self):
        from src import sitework as s
        with contextlib.redirect_stdout(io.StringIO()) as out:
            s.check_height()
        self.assertIn('Building 2 ridge +25\'-4-1/4", height +23\'-2-1/4" (25\'-0" max)', out.getvalue())
        self.assertLessEqual(s.ADU_HEIGHT, s.PRINCIPAL_HEIGHT)


if __name__ == '__main__':
    unittest.main()

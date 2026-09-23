"""The zoning tabulation: the figures G-001, C-101 and C-102 all print.

src/sitework.py had no dedicated test file. It is the module the zoning table, the
variance list, the lot coverage and the ADU ratio come from, and C-102 is the one
document that goes to the Board of Zoning Adjustment on its own -- so these are the
numbers a hearing turns on.

The three checks it owns (check_fsd, check_height, check_wheel_stops) run from
check_model(); check_site_clearances, check_b1_service and check_b2_service run at DRAW
time from C-101. These hold the TABULATION, which no check owned.
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

from src import sitework as S


class LotTests(unittest.TestCase):

    def test_the_lot_is_the_one_on_the_survey(self):
        self.assertEqual(S.SITE_W, 40.0)
        self.assertEqual(S.SITE_D, 126.0)

    def test_the_lot_area_is_derived_from_its_dimensions(self):
        """Typed, it would survive a change to either dimension."""
        self.assertAlmostEqual(S.LOT_AREA, S.SITE_W*S.SITE_D)

    def test_coverage_is_a_fraction_of_the_lot_and_includes_more_than_the_buildings(self):
        self.assertGreater(S.COVERAGE, S.COVERAGE_BLDG,
                           'coverage that equals the building footprints counts no stoops')
        self.assertLess(S.COVERAGE, S.LOT_AREA)

    def test_the_building_footprint_matches_the_two_buildings(self):
        """COVERAGE_BLDG is the two footprints. Building 1's is read from the building
           model rather than typed, so this also catches the two disagreeing."""
        want = sum(b[2]*b[3] for b in S.SITE_BLDG)
        self.assertAlmostEqual(S.COVERAGE_BLDG, want)


class DwellingTests(unittest.TestCase):

    def test_there_are_five_dwellings(self):
        self.assertEqual(sorted(S.NET_SF), [1, 2, 3, 4, 5])

    def test_the_stacked_pairs_are_equal(self):
        """Units 2 and 3 are one plan stacked, and so are 4 and 5. If a pair ever
           differs, one of them was edited and the other was not."""
        self.assertEqual(S.NET_SF[2], S.NET_SF[3])
        self.assertEqual(S.NET_SF[4], S.NET_SF[5])

    def test_net_area_is_less_than_framed_area_for_every_unit(self):
        """NET_SF is FRAMED_SF less a typed deduction. A net area at or above the framed
           one means the deduction went missing."""
        for u in S.NET_SF:
            self.assertLess(S.NET_SF[u], S.FRAMED_SF[u], 'unit %s' % u)

    def test_unit_1_is_the_principal_dwelling(self):
        for u in (2, 3, 4, 5):
            self.assertLess(S.NET_SF[u], S.NET_SF[1], 'unit %s is not smaller than Unit 1' % u)

    def test_each_ADU_is_inside_the_ratio_C_C_3332_355_allows(self):
        """C.C. 3332.355(B)(3): an ADU against the principal dwelling."""
        for u in (4, 5):
            self.assertLessEqual(S.NET_SF[u]/S.NET_SF[1], S.ADU_PCT_MAX,
                                 'unit %s is over the ADU ratio' % u)


class VarianceTests(unittest.TestCase):

    def test_every_variance_names_a_code_section_and_a_subject(self):
        self.assertTrue(S.VARIANCES)
        for section, subject in S.VARIANCES:
            with self.subTest(subject):
                self.assertTrue(section.startswith('C.C. '), section)
                self.assertTrue(subject.strip())

    def test_the_parking_variance_is_there_because_the_maneuvering_is_short(self):
        """MANEUVER_HAVE is the alley right of way; 3312.25 asks MANEUVER. The variance
           list and the geometry have to tell the same story."""
        self.assertLess(S.MANEUVER_HAVE, S.MANEUVER)
        self.assertTrue(any('3312' in s for s, _subj in S.VARIANCES),
                        'the maneuvering is short and no parking variance is listed')

    def test_no_variance_is_listed_twice(self):
        subjects = [subj for _s, subj in S.VARIANCES]
        self.assertEqual(len(subjects), len(set(subjects)), subjects)


class ParkingTests(unittest.TestCase):

    def test_the_stalls_are_full_length(self):
        self.assertEqual(S.PARK_N, 3)
        self.assertEqual(S.PARK_D, 18.0)

    def test_the_street_vision_triangle_is_C_C_3321_05(self):
        self.assertEqual(S.VISION_ST, 30.0)


if __name__ == '__main__':
    unittest.main()

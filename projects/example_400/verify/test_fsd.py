"""400 Oak's RCO 302.1 imaginary line: where src/fsd.py stands it in the 15'-0"
   courtyard, and each way of moving it or the buildings that breaks Table 302.1(1)."""
import importlib
import unittest

from projects.example_400.verify import enter, leave
from codes.ohio.rco import fire_separation as T


def setUpModule():
    enter()


def tearDownModule():
    fresh()
    leave()


def fresh():
    from src import fsd, sitework
    return importlib.reload(fsd), importlib.reload(sitework)


class ImaginaryLineTests(unittest.TestCase):

    def tearDown(self):
        fresh()

    def test_the_courtyard_passes(self):
        fresh()[1].check_fsd()

    def test_the_line_and_what_it_leaves(self):
        f, s = fresh()
        self.assertEqual((f.GAP, f.OFF_B1, f.OFF_B2), (15.0, 6.25, 8.75))
        self.assertEqual(s.COURT, f.GAP)
        self.assertEqual(f.stair_clear(), 5.25)                  # the stair and the rear rake split the slack
        self.assertEqual(f.OFF_B1-f.RAKE_OVERHANG, 5.25)
        self.assertEqual(T.wall_rating(f.OFF_B1), 'NONE')
        self.assertIsNone(T.opening_max(f.OFF_B1))
        self.assertEqual(T.projection_rating(f.stair_clear()), 'NONE')

    def test_the_rear_rake_inside_five_feet_over_a_vented_gable_fails(self):
        f, s = fresh()
        bad = f.fsd_violations(s.REAR_LINE, s.B2_Y, s.rear_storeys(), rear_rake=1.0, off_b1=5.0, rear_gable_vent=True)
        self.assertTrue(any("rear rake" in v for v in bad), bad)

    def test_an_eave_that_is_not_fireblocked_fails(self):
        f, s = fresh()
        edges = [e[:4]+(False,)+e[5:] if e[1] == T.EAVE else e for e in s.roof_edges()]
        self.assertEqual(T.edge_violations(s.roof_edges()), [])
        self.assertEqual(len(T.edge_violations(edges)), 4)

    def _violations(self, **kw):
        f, s = fresh()
        return f.fsd_violations(s.REAR_LINE, s.B2_Y, s.rear_storeys(), **kw)



    def test_a_line_drawn_for_another_courtyard_fails(self):
        f, s = fresh()
        f.GAP = 12.0
        with self.assertRaises(AssertionError):
            s.check_fsd()

    def test_the_rear_wall_is_measured_from_the_plans(self):
        f, s = fresh()
        l1, l2 = s.rear_storeys()
        self.assertAlmostEqual(l1[0], 2.67*(6.0+8.0/12.0))    # the back door, the Level 1 rear wall's one opening
        self.assertEqual(l2[0], 36.0)                # Bedrooms 1 and 3's W-As

    def test_the_midline_leaves_the_stair_too_close(self):
        v = self._violations(off_b1=7.5)
        self.assertTrue(any("Unit 3 stair" in m for m in v), v)

    def test_a_line_under_five_feet_rates_building_1s_rear_wall(self):
        v = self._violations(off_b1=4.5)
        self.assertTrue(any("Building 1's rear wall stands" in m for m in v), v)


class TableTests(unittest.TestCase):
    """Table 302.1(1) came over from 300 unchanged; its rows are pinned here too."""

    def test_the_rows(self):
        f, _s = fresh()
        self.assertEqual(T.WALLS, ((0.0, '1 HOUR'), (5.0, 'NONE')))
        self.assertEqual([d for d, _v in T.PROJECTIONS], [0.0, 2.0, 5.0])
        self.assertEqual(T.OPENINGS, ((0.0, 0.0), (3.0, 0.25), (5.0, None)))


if __name__ == '__main__':
    unittest.main()

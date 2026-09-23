"""RCO Chapter 15's figures and lookups, on cases worked by hand."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)



class MechanicalRuleTests(unittest.TestCase):

    def test_m1505_4_3_1_rows(self):
        """Spot checks down the transcribed table: the two rows this project lands on
           and the corners around them."""
        from codes.ohio.rco.mechanical import whole_house_cfm
        self.assertEqual(whole_house_cfm(2, 624), 45)
        self.assertEqual(whole_house_cfm(4, 1248), 60)
        self.assertEqual(whole_house_cfm(1, 1000), 30)
        self.assertEqual(whole_house_cfm(3, 1500), 45)
        self.assertEqual(whole_house_cfm(3, 1501), 60)
        self.assertEqual(whole_house_cfm(6, 5000), 120)
        self.assertEqual(whole_house_cfm(8, 8000), 165)

    def test_route_length_and_elbows(self):
        from codes.ohio.rco.mechanical import DRYER_ELBOW, dryer_equivalent, route_length
        pts = [(0, 0, 0), (0, 0, 3), (4, 0, 3), (4, 1, 3)]
        L, n = route_length(pts)
        self.assertAlmostEqual(L, 8.0); self.assertEqual(n, 2)
        self.assertAlmostEqual(dryer_equivalent(pts), 8.0+2*DRYER_ELBOW)
        # a straight run has no elbow, and a repeated point is not a segment
        self.assertEqual(route_length([(0, 0), (0, 0), (5, 0)]), (5.0, 0))

    def test_the_gap_is_along_the_wall_from_the_caps_opening(self):
        from codes.ohio.rco.mechanical import CAP_R, odu_gap
        self.assertAlmostEqual(odu_gap(10.0, 2.75, 5.0), 10.0-(5.0+CAP_R))
        self.assertAlmostEqual(odu_gap(10.0, 2.75, 16.0), (16.0-CAP_R)-12.75)
        self.assertEqual(odu_gap(10.0, 2.75, 11.0), 0.0)       # over or under the unit
        self.assertEqual(odu_gap(10.0, 2.75, 12.9), 0.0)       # the cap's opening overlaps its end


if __name__ == '__main__':
    unittest.main()

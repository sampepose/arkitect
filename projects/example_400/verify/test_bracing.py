"""400 Oak's wall bracing: every line passes RCO 602.10 from the plans' openings, the
   tables read as transcribed, and the rules fire."""
import unittest

from lib.units import IN
from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class BracingTests(unittest.TestCase):

    def test_the_bracing_passes(self):
        from src import bracing as b
        b.check_bracing()
        self.assertEqual(len(b.LINES), 16)
        self.assertEqual(b.bracing_violations(b.LINES), [])


    def test_no_hold_down_and_one_portal_frame(self):
        from src import bracing as b
        self.assertEqual([e for ln in b.LINES for e in ln.ends if e.hold_down is not None], [])
        pf = [(ln.building, ln.level, ln.wall) for ln in b.LINES for _p, _o in b.portal_openings(ln)]
        self.assertEqual(pf, [("BUILDING 2", 1, "COURTYARD WALL")])

    def test_building_2s_rear_corners_are_panels_on_both_levels(self):
        from src import bracing as b
        for lv in (1, 2):
            ln = next(l for l in b.LINES if l.building == "BUILDING 2" and l.level == lv and l.wall == "REAR WALL")
            self.assertEqual(len(ln.panels), 3)

    def test_a_wall_with_no_opening_is_two_panels_and_a_long_segment_is_one(self):
        from src import bracing as b
        from codes.ohio.rco import bracing as rco_bracing
        whole = [b.Panel(0.0, 33.0, rco_bracing.METHOD, IN(27), 33.0)]
        self.assertEqual(b.location_violations(33.0, whole), [])
        beside_a_door = [b.Panel(5.0, 20.0, rco_bracing.METHOD, IN(27), 15.0)]
        self.assertTrue(any("1 braced wall panel" in v for v in b.location_violations(20.0, beside_a_door)))

    def test_a_wide_window_in_the_front_wall_fails(self):
        from src import bracing as b
        runs = b.wall_runs()
        i = next(k for k, r in enumerate(runs) if r.building == "BUILDING 1" and r.level == 1 and r.name == "FRONT WALL")
        runs[i] = runs[i]._replace(openings=(b.Opening(1.0, 19.0, 4.0, "W-X"),))
        bad = b.bracing_violations(b.build_lines(runs))
        self.assertTrue(any("BUILDING 1 L1 BWL 1" in v for v in bad), bad)

    def test_w1r_is_building_2_level_1(self):
        from src import bracing as b
        self.assertEqual({(l.building, l.level) for l in b.w1r_lines()}, {("BUILDING 2", 1)})
        self.assertEqual(len(b.w1r_lines()), 4)


if __name__ == '__main__':
    unittest.main()

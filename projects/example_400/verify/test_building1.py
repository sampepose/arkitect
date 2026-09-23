"""400 Oak's house, Building 1: the checks build.py runs before drawing A-101, and proof
   that each one fires when the plan breaks the rule it guards."""
import importlib
import os
import unittest

from projects.example_400.verify import PROJ, enter, leave


def setUpModule():
    enter()


def fresh():
    """Building 1 as authored. Reloaded for every test, so a patch made by one test
       cannot leak into the next."""
    from src import building1
    return importlib.reload(building1)


def tearDownModule():
    fresh()             # nothing patched here reaches the build test_site.py runs
    leave()


class ThisProjectTests(unittest.TestCase):

    def test_src_is_dana_not_wayne(self):
        b = fresh()
        self.assertTrue(os.path.realpath(b.__file__).startswith(os.path.realpath(PROJ)),
                        b.__file__)


class InsideTests(unittest.TestCase):

    def test_the_plan_passes(self):
        fresh().check_b1_inside()

    def test_a_fitting_past_a_wall_is_named(self):
        b = fresh()
        b.F_L2.append((19.0, 20.0, 2.0, 2.0, 'wd'))
        self.assertEqual(b.b1_outside(), [(2, 'wd')])
        with self.assertRaises(AssertionError):
            b.check_b1_inside()


class GlazingTests(unittest.TestCase):

    def test_the_plan_passes(self):
        fresh().check_b1_glazing()

    def test_each_window_serves_the_space_it_opens_into(self):
        gl = fresh().b1_glazing()
        self.assertEqual(sorted(gl), ["BEDROOM 1", "BEDROOM 2", "BEDROOM 3", "LIVING / KITCHEN"])
        self.assertEqual(sorted(gl["LIVING / KITCHEN"][2]), ["B", "B", "C"])
        for n in ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3"):   # a W-A in the end wall and a W-B in the side wall
            self.assertEqual(sorted(gl[n][2]), ["A", "B"], n)

    def test_the_living_room_without_its_front_window_fails(self):
        b = fresh()
        b.L1_WINS[:] = [w for w in b.L1_WINS if w[4] != "C"]
        with self.assertRaises(AssertionError):
            b.check_b1_glazing()

    def test_a_bedroom_without_a_w_a_fails_even_with_enough_glass(self):
        b = fresh()
        b.L2_WINS[0] = b.L2_WINS[0][:4]+("B",)      # Bedroom 2: a W-B is 12 SF, over 8%
        with self.assertRaises(AssertionError) as e:
            b.check_b1_glazing()
        self.assertIn("W-A", str(e.exception))


class StairTests(unittest.TestCase):

    def test_the_plan_passes(self):
        fresh().check_b1_stair()

    def test_the_figures(self):
        f = fresh().b1_stair()
        self.assertAlmostEqual(f['riser']*12, 8.0)
        self.assertAlmostEqual(f['tread']*12, 9.25)
        self.assertEqual((f['risers'], f['treads']), (15, 14))
        self.assertGreaterEqual(f['clear'], 3.0)
        self.assertAlmostEqual(f['top'], 3.0, places=5)     # the landing off the front wall
        self.assertGreaterEqual(f['foot'], 3.0)             # kitchen floor at the foot
        self.assertEqual(f['in_foot'], [])
        self.assertGreaterEqual(f['hall'], 3.0)
        self.assertEqual(f['overhead'], [])
        self.assertEqual(f['column'][0], f['column'][1])

    def _fails(self, **kw):
        b = fresh()
        s = b.B1_STAIR
        args = dict(risers=s.risers, treads=s.treads, tread=s.tread,
                    stud_width=s.stud_width, foot_landing=s.foot_landing,
                    top_landing=s.top_landing, rise=s.rise)
        args.update(kw)
        b.B1_STAIR = type(s)(**args)
        with self.assertRaises(AssertionError):
            b.check_b1_stair()

    def test_a_tread_under_nine_inches_fails(self):
        self._fails(tread=8.875/12.0)

    def test_fourteen_risers_are_over_eight_and_a_quarter_inches(self):
        self._fails(risers=14, treads=13)

    def test_a_top_landing_under_36_inches_fails(self):
        b = fresh()
        b.Y_TOP_RISER = 2.9
        with self.assertRaises(AssertionError):
            b.check_b1_stair()

    def test_a_fitting_on_the_foot_landing_fails(self):
        b = fresh()
        b.F_L1.append((b.X_ST+0.5, b.Y_FOOT_RISER+0.5, 2.0, 2.0, 'counter'))
        with self.assertRaises(AssertionError) as e:
            b.check_b1_stair()
        self.assertIn("foot landing", str(e.exception))

    def test_a_corridor_under_three_feet_fails(self):
        b = fresh()
        b.X_COR0 = b.X_COR1-2.8
        with self.assertRaises(AssertionError) as e:
            b.check_b1_stair()
        self.assertIn("311.6", str(e.exception))

    def test_a_level_2_room_over_the_flight_fails(self):
        b = fresh()
        b.L2_ROOMS.append((b.X_ST, 6.0, 3.0, 3.0, "CL."))
        with self.assertRaises(AssertionError) as e:
            b.check_b1_stair()
        self.assertIn("over the flight", str(e.exception))


class DryerTests(unittest.TestCase):

    def test_the_plan_passes(self):
        fresh().check_b1_dryer()

    def test_a_rear_window_beside_the_w_d_fails(self):
        b = fresh()
        wd = next(f for f in b.F_L1 if f[4] == 'wd')
        b.L1_WINS.append((wd[0]+wd[2]+1.0, b.Y_REAR, 3.0, 'h', "B"))
        with self.assertRaises(AssertionError):
            b.check_b1_dryer()


class Bath1VanityTests(unittest.TestCase):

    def test_a_24_inch_vanity_fits(self):
        b = fresh()
        b.check_b1_vanity()
        v = b.b1_vanity()
        self.assertGreaterEqual(v['width']*12, 24.0-1e-9)      # its face, along the left wall
        self.assertGreaterEqual(v['to_shower'], 0.0)

    def test_a_vanity_that_runs_into_the_shower_fails(self):
        b = fresh()
        lav = next(f for f in b.F_L1 if f[4] == 'lav')
        b.F_L1[b.F_L1.index(lav)] = lav[:3]+(lav[3]+1/12.0,)+lav[4:]
        with self.assertRaises(AssertionError) as e:
            b.check_b1_vanity()
        self.assertIn("shower", str(e.exception))

    def test_a_vanity_44_inches_deep_would_stand_in_the_door_swing(self):
        b = fresh()
        lav = next(f for f in b.F_L1 if f[4] == 'lav')
        i = b.F_L1.index(lav)
        x = b.PLAN_B1_L1.inv_x(b.PLAN_B1_L1.x(19.5, b.Y_RB)-44/12.0, b.Y_RB)
        b.F_L1[i] = (x, lav[1], 44/12.0, lav[3], 'lav', 'w')
        with self.assertRaises(AssertionError) as e:
            b.check_b1_vanity()
        self.assertIn("swing", str(e.exception))


class Building2InsideTests(unittest.TestCase):
    """Building 2's fit check now goes through geom.beyond(); it still names a fitting
       placed past the wall, the case that first made it necessary."""

    def test_a_w_d_past_the_wall_is_named(self):
        from src import building2
        b2 = importlib.reload(building2)
        b2.F_B2.append((19.0, 14.0, 2.83, 2.25, 'wd'))
        self.assertEqual(b2.b2_outside(), ['wd'])
        importlib.reload(building2)


if __name__ == '__main__':
    unittest.main()

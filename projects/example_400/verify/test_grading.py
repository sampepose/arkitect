"""400 Oak's grading: check_grading() passes, and each rule fires — a concrete gutter may not reach
   Oak, a walk may not pass 1 in 20, a step may not pass 8-1/4", a yard under the exception
   keeps 401.3's rate, and a splash block stays off paving."""
import importlib
import unittest

from lib.units import IN
from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


def G():
    from src import grading
    return importlib.reload(grading)


class GradingTests(unittest.TestCase):

    def test_the_grading_passes(self):
        G().check_grading()

    def test_the_scheme_is_graded_lawn_and_one_walk_edge(self):
        g = G()
        self.assertEqual({x.kind for x in g.GUTTERS}, {"swale", "walk"})
        self.assertFalse(hasattr(g, "INLET"))
        self.assertEqual([(x.mark, x.to) for x in g.GUTTERS if x.kind == "swale"],
                         [("S-1", "S-3"), ("S-2", "S-3"), ("S-3", "OAK"), ("S-4", "ALLEY")])
        self.assertAlmostEqual(g.FRONT_LOT, g.S3.end)

    def test_a_flat_swale_fails(self):
        g = G()
        flat = g.Gutter("S-9", (g.GX, 60.0), (g.GX, 0.0), -IN(3), "OAK", slope=0.005)
        self.assertTrue(any("under 1.0%" in v for v in g.gutter_violations([flat])))

    def test_a_gutter_to_dana_fails(self):
        g = G()
        bad = g.gutter_violations([g.Gutter("G-9", (g.GX, 60.0), (g.GX, 0.0), -g.FALL, "OAK", slope=0.005, w=1.0, kind="gutter")])
        self.assertTrue(any("concentrated flow" in v for v in bad), bad)

    def test_a_steep_walk_edge_fails(self):
        g = G()
        w = g.Gutter("W-9", (g.SX, 25.0), (g.SX, 0.0), -IN(2), "OAK", slope=0.06, kind="walk", w=0.0)
        self.assertTrue(any("1 in 20" in v for v in g.gutter_violations([w])))

    def test_a_flat_exception_yard_fails(self):
        g = G()
        b = next(b for b in g.BANDS if b.to == "S-4")
        flat = g.Gutter("S-4", g.S4.a, g.S4.b, -IN(0.5), "ALLEY")
        band = b._replace(section=lambda s: [(0.0, g.G0, None), (g.S4X-g.B2X1, flat.grade_at(g.S4X, s), "lawn")])
        bad = g.band_violations(band, [flat])
        self.assertTrue(any("a swale yard keeps" in v for v in bad), bad)

    def test_a_high_step_fails(self):
        g = G()
        st = g.STEPS[0]._replace(top=g.LANDING_TOP+IN(2))
        self.assertTrue(any("a step of" in v for v in g.step_violations([st])))

    def test_a_splash_block_on_the_pad_fails(self):
        g = G()
        ld = g.LEADERS[3]._replace(block=(g.PAD.x1-1.0, g.PAD.y0, g.PAD.x1, g.PAD.y0+2.0))
        self.assertTrue(any("splash block is on the PARKING PAD" in v for v in g.leader_violations([ld]+g.LEADERS[:3])))

    def test_only_the_back_door_landing_goes_without_a_walk(self):
        g = G()
        self.assertEqual(g.NO_WALK, ("UNIT 1 REAR LANDING",))
        g.NO_WALK = ()
        self.assertTrue(any("UNIT 1 REAR LANDING: steps down onto no walk" in v for v in g.access_violations()))

    def test_ds3_clears_the_parking_walk(self):
        g = G()
        ds3 = next(l for l in g.LEADERS if l.mark == "DS-3")
        self.assertIn("DS-3", g.SLEEVED)
        self.assertLessEqual(ds3.block[2], g.PARK_WALK.x0)
        on_walk = ds3._replace(block=(g.PARK_WALK.x0, ds3.block[1], g.PARK_WALK.x1, ds3.block[3]))
        self.assertTrue(any("PARKING WALK" in v for v in g.leader_violations([on_walk])))

    def test_unit_2s_landing_meets_the_courtyard_walk(self):
        g = G()
        self.assertEqual(g.access_violations(), [])
        self.assertAlmostEqual(g.U2_LANDING.y0, g.COURT_WALK.y1)


if __name__ == '__main__':
    unittest.main()

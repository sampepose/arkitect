"""The downspout model: one leader at the end of each eave gutter, clear of what stands on
its wall and in its yard, onto lawn that drains to a site gutter or the alley. Each rule
the checker enforces is broken once here, so a checker that stopped looking would fail."""
import io
import os
import sys
import contextlib
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class RealModelTests(unittest.TestCase):

    def test_the_real_model_passes(self):
        from src import downspouts as ds
        self.assertEqual(ds.downspout_violations(), [])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ds.check_downspouts()
        self.assertIn("DS-4", out.getvalue())

    def test_each_eave_carries_half_its_roof(self):
        """Half the roof in plan to the dripline: 14'-0" of the 28'-0" across the eaves,
           times 49'-6" (Building 1, rakes 12" and 6") or 30'-0" (Building 2)."""
        from src import downspouts as ds
        self.assertEqual([e.area for e in ds.EAVES], [693.0, 693.0, 420.0, 420.0])
        self.assertEqual(sorted(d.eave.name for d in ds.DOWNSPOUTS), sorted(e.name for e in ds.EAVES))

    def test_nothing_is_aimed_at_a_sidewalk(self):
        from src import downspouts as ds
        tos = {d.mark: ds.discharge(d).to for d in ds.DOWNSPOUTS}
        self.assertTrue(all(t not in ds.SIDEWALK_STREETS for t in tos.values()), tos)
        self.assertEqual(tos["DS-3"], "ALLEY")

    def test_no_leader_on_a_safford_face(self):
        """The stair and the Unit 3 walk: both Sage gutters turn the rear corner."""
        from src import downspouts as ds
        for d in ds.DOWNSPOUTS:
            self.assertNotEqual(d.face.side, "SAGE FACE")

    def test_every_leader_outlet_is_six_inches(self):
        """With no gas on any wall, every outlet elbow is at OUTLET_Z."""
        from lib.units import IN
        from src import downspouts as ds
        for d in ds.DOWNSPOUTS:
            self.assertEqual(ds.discharge(d).outlet_z, IN(6))

    def test_the_sizing_figures(self):
        """Transcribed from OPC Tables 1106.3 and 1106.6; the rate is Columbus's."""
        from src import downspouts as ds
        self.assertEqual((ds.RAIN, ds.GUTTER_IN, ds.GUTTER_PITCH), (2.8, 5, 1/8.0))
        self.assertEqual(ds.T1106_6[(5, 1/8.0)], 74)
        self.assertEqual((ds.T1106_3['2 x 2'], ds.T1106_3['2 x 4']), (30, 92))
        self.assertNotIn(ds.LEADER, ds.T1106_3)
        self.assertAlmostEqual(ds.flow(624.0), 18.157, places=2)
        self.assertAlmostEqual(ds.flow(364.0), 10.591, places=2)

    def test_cb1_takes_no_more_roof_than_it_is_sized_for(self):
        """CB-1's pipes are sized on grading.tributary(); the leaders must not send it more."""
        from src import downspouts as ds
        self.assertEqual(ds.roof_to("CB-1"), 1806.0)
        self.assertEqual(ds.roof_to("ALLEY"), 420.0)
        self.assertLessEqual(ds.roof_to("CB-1"), ds.G.tributary()[1])

    def test_the_gutter_runs(self):
        from src import downspouts as ds
        self.assertEqual([ds.gutter_run(d) for d in ds.DOWNSPOUTS], [49.0, 48.0, 29.0, 28.0])


class MutationTests(unittest.TestCase):

    def setUp(self):
        from src import downspouts as ds
        self.ds = ds

    def swap(self, i, **kw):
        out = list(self.ds.DOWNSPOUTS); out[i] = out[i]._replace(**kw); return out

    def fails(self, needle, dss):
        v = self.ds.downspout_violations(dss)
        self.assertTrue(any(needle in x for x in v), "%r not in %r" % (needle, v[:4]))

    def test_a_missing_leader_fails(self):
        self.fails("0 leaders", self.ds.DOWNSPOUTS[1:])

    def test_a_leader_under_the_unit_3_stair_fails(self):
        g = self.ds.G
        self.fails("under the UNIT 3 STAIR", self.swap(0, face=g.F_B1_SAFF, s=g.B1Y1-self.ds.CORNER))

    def test_a_leader_onto_the_unit_3_walk_fails(self):
        g = self.ds.G
        self.fails("on the UNIT 3 WALK", self.swap(2, face=g.F_B2_SAFF, s=g.B2Y1-self.ds.CORNER))

    def test_a_leader_toward_safford_fails(self):
        g = self.ds.G
        self.fails("toward the SAGE sidewalk", self.swap(0, face=g.F_B1_SAFF, s=g.B1Y0+self.ds.CORNER))

    def test_a_leader_in_front_of_a_window_fails(self):
        g = self.ds.G
        self.fails("W-C", self.swap(0, s=g.B1X0+4.0))

    def test_a_splash_block_over_the_sewer_trench_fails(self):
        g = self.ds.G
        self.fails("from the BUILDING SEWER", self.swap(0, s=g.B1X0+6.0))

    def test_a_leader_away_from_its_gutter_fails(self):
        g = self.ds.G
        self.fails("not at the end of its gutter", self.swap(0, s=g.B1X0+13.0))

    def test_a_leader_by_a_service_box_fails(self):
        from src.sitework import SVC_EQUIP
        em1 = next(e for e in SVC_EQUIP if e[0] == "EM-1")
        self.fails("of EM-1", self.swap(1, s=em1[2]+em1[4]+0.5))

    def test_a_storm_over_the_leader_fails(self):
        v = self.ds.downspout_violations(rain=20.0)
        self.assertTrue(any("Table 1106.3" in x for x in v), v[:4])

    def test_a_storm_over_the_gutter_fails(self):
        v = self.ds.downspout_violations(rain=12.0)
        self.assertTrue(any("Table 1106.6" in x for x in v), v[:4])

    def test_cb1_sized_for_less_roof_fails(self):
        v = self.ds.downspout_violations(roof_cap=1000.0)
        self.assertTrue(any("CB-1" in x for x in v), v[:4])

    def test_a_splash_block_behind_a_wheel_stop_fails(self):
        from src.sitework import WHEEL_STOPS
        x0, _y0, x1, _y1 = WHEEL_STOPS[0]
        self.fails("wheel stop 1", self.swap(2, s=(x0+x1)/2.0))

    def test_a_splash_block_on_the_pad_fails(self):
        g = self.ds.G
        self.fails("on the PARKING PAD", self.swap(3, face=g.F_B2_REAR, s=g.B2X1-self.ds.CORNER))


class GutterGuardTests(unittest.TestCase):
    """A guard the full length of every eave gutter, rated for the lot's short-duration
       intensity and not merely OPC 1106.1's hourly rate."""

    def test_every_gutter_is_guarded(self):
        from src import downspouts as ds
        self.assertEqual(ds.guard_violations(), [])
        self.assertEqual(sorted(ds.GUARDED), sorted(e.name for e in ds.EAVES))

    def test_the_rating_is_the_five_minute_intensity(self):
        from src import downspouts as ds, grading as g
        self.assertEqual(ds.GUARD_RATE_MIN, g.RAIN_I)
        self.assertGreater(ds.GUARD_RATE_MIN, ds.RAIN)

    def test_an_unguarded_gutter_fails(self):
        from src import downspouts as ds
        v = ds.guard_violations(guarded=ds.GUARDED[:-1])
        self.assertEqual(v, ["%s: no gutter guard" % ds.EAVES[-1].name])

    def test_an_hourly_rating_fails(self):
        from src import downspouts as ds
        self.assertTrue(ds.guard_violations(rate_min=ds.RAIN))


if __name__ == "__main__":
    unittest.main()

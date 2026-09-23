"""The RCO 302.1 imaginary line in the courtyard, src/fsd.py.

The table rows are transcribed from RCO Table 302.1(1) and pinned here, because a
summary of that table is what gets a rating wrong. The rest of the file is about the
one equation the courtyard is: the line may stand from 3'-0" to 3'-6" off Building 1
and nowhere else, and these tests hold both ends of that window.
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


def _site():
    from src.mirror import B1_W
    from src.roof import B1_ROOF, gable_vented, rake
    from src.sitework import B1_REAR_Y, B2_COURT_Y, L2_STOREY, U3_STOOP_Y1
    return dict(b1_rear_y=B1_REAR_Y, b2_court_y=B2_COURT_Y, b1_width=B1_W,
                storey_h=L2_STOREY, rear_rake=rake(B1_ROOF, 'REAR'), stoop_y1=U3_STOOP_Y1,
                rear_gable_vent=gable_vented(B1_ROOF, 'REAR'))










class LineTests(unittest.TestCase):

    def test_the_model_passes(self):
        from src import fsd
        self.assertEqual(fsd.fsd_violations(**_site()), [])

    def test_the_line_is_three_feet_off_building_one(self):
        from src import fsd
        self.assertAlmostEqual(fsd.OFF_B1, 3.0)
        self.assertAlmostEqual(fsd.OFF_B2, 9.0)
        self.assertAlmostEqual(fsd.OFF_B1+fsd.OFF_B2, fsd.GAP)

    def test_the_courtyard_is_one_equation(self):
        """Building 1's share, the stair's width and the stair's clearance spend the gap."""
        from src import fsd
        self.assertAlmostEqual(fsd.OFF_B1+fsd.STAIR_W+fsd.U5_CLEAR, fsd.GAP)

    def test_the_stair_keeps_six_inches_over_its_minimum(self):
        from src import fsd
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertAlmostEqual(fsd.U5_CLEAR, 5.5)
        self.assertAlmostEqual(fsd.U5_CLEAR-rco_fsd.PROJ_FREE, 0.5)
        self.assertEqual(rco_fsd.projection_rating(fsd.U5_CLEAR), 'NONE')

    def test_the_rear_wall_is_rated_and_its_openings_fit(self):
        """38 SF in a 26'-0" x 9'-0" story, 16.2 percent against 25."""
        from src import fsd
        from codes.ohio.rco import fire_separation as rco_fsd
        from src.sitework import L2_STOREY, REAR_OPEN_PCT
        from src.mirror import B1_W
        self.assertEqual(rco_fsd.wall_rating(fsd.OFF_B1), '1 HOUR')
        self.assertAlmostEqual(fsd.REAR_OPEN_SF, 38.0)
        self.assertAlmostEqual(L2_STOREY, 9.0)
        self.assertAlmostEqual(fsd.rear_wall_sf(B1_W, L2_STOREY), 234.0)
        self.assertAlmostEqual(REAR_OPEN_PCT, 38.0/234.0)
        self.assertLess(REAR_OPEN_PCT, rco_fsd.opening_max(fsd.OFF_B1))

    def test_building_two_is_clear_of_the_table(self):
        from src import fsd
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertEqual(rco_fsd.wall_rating(fsd.OFF_B2), 'NONE')
        self.assertIsNone(rco_fsd.opening_max(fsd.OFF_B2))


class WindowTests(unittest.TestCase):
    """The line has exactly six inches of travel, and both ends of it are a hard stop."""

    def _at(self, off):
        from src import fsd
        return fsd.fsd_violations(off_b1=off, **_site())




    def test_the_stair_may_grow_by_exactly_the_slack_and_no_more(self):
        """The six inches are the stair's whichever way it spends them: wider, or
           further out from Building 2's face."""
        from src import fsd
        from codes.ohio.rco import fire_separation as rco_fsd
        self.assertAlmostEqual(fsd.stair_clear(fsd.OFF_B2, fsd.STAIR_W+0.5), rco_fsd.PROJ_FREE)
        self.assertLess(fsd.stair_clear(fsd.OFF_B2, fsd.STAIR_W+0.5+1.0/12.0), rco_fsd.PROJ_FREE)

    def test_three_feet_is_the_near_end(self):
        self.assertEqual(self._at(3.0), [])
        bad = self._at(3.0-1.0/12.0)
        self.assertTrue(any('begins to permit an opening' in b for b in bad), bad)

    def test_three_feet_six_is_the_far_end(self):
        self.assertEqual(self._at(3.5), [])
        bad = self._at(3.5+1.0/12.0)
        self.assertTrue(any('Unit 5 stair leaves' in b for b in bad), bad)

    def test_everything_between_passes(self):
        for n in range(7):
            off = 3.0+n/12.0
            self.assertEqual(self._at(off), [], 'the line fails at %.4f' % off)


class ProjectionTests(unittest.TestCase):

    def test_the_rear_rake_is_six_inches_over_an_unvented_gable(self):
        from src import fsd
        from codes.ohio.rco import fire_separation as rco_fsd
        from src.roof import B1_ROOF, gable_vented, rake
        self.assertAlmostEqual(rake(B1_ROOF, 'REAR')*12, 6.0)
        self.assertFalse(gable_vented(B1_ROOF, 'REAR'))
        self.assertAlmostEqual(fsd.OFF_B1-rake(B1_ROOF, 'REAR'), 2.5)
        self.assertEqual(rco_fsd.underside(2.5, rco_fsd.RAKE, gable_vent=False), '0 HOURS, FOOTNOTE b')

    def test_a_twelve_inch_rear_rake_has_no_tolerance_left(self):
        """12" leaves exactly 2'-0": permitted, and 1/4" more is not."""
        from src import fsd
        self.assertEqual(fsd.fsd_violations(**dict(_site(), rear_rake=1.0)), [])
        bad = fsd.fsd_violations(**dict(_site(), rear_rake=1.0+0.25/12.0))
        self.assertTrue(any('permits a projection at all' in b for b in bad), bad)

    def test_a_gable_vent_under_the_rear_rake_fails(self):
        from src import fsd
        bad = fsd.fsd_violations(**dict(_site(), rear_gable_vent=True))
        self.assertTrue(any('over a vented gable' in b for b in bad), bad)

    def test_the_unit_three_stoop_stops_short_of_the_line(self):
        from src.sitework import FSD_LINE_Y, U3_STOOP_Y1
        self.assertLess(U3_STOOP_Y1, FSD_LINE_Y)
        self.assertAlmostEqual(FSD_LINE_Y-U3_STOOP_Y1, 71.0-70.03125)

    def test_a_stoop_that_crossed_the_line_fails(self):
        from src import fsd
        from src.sitework import FSD_LINE_Y
        bad = fsd.fsd_violations(**dict(_site(), stoop_y1=FSD_LINE_Y+0.5))
        self.assertTrue(any('past the imaginary line' in b for b in bad), bad)


class LeaderTests(unittest.TestCase):
    """DS-1 is the one thing standing on Building 1's rear wall. It is a conductor, not
       a projection with an underside, but its figure belongs on the record."""

    def test_ds1_is_on_that_wall_and_clears_the_projection_floor(self):
        from src import fsd
        from codes.ohio.rco import fire_separation as rco_fsd
        from src.downspouts import DOWNSPOUTS, LEADER_D
        from src.sitework import B1_REAR_Y
        on = [d.mark for d in DOWNSPOUTS
              if d.face.building == 'BUILDING 1' and abs(d.face.at-B1_REAR_Y) < 1e-9]
        self.assertEqual(on, ['DS-1'])
        self.assertAlmostEqual(LEADER_D*12, 2.0)
        self.assertGreater(fsd.OFF_B1-LEADER_D, rco_fsd.PROJ_MIN)

    def test_a_leader_deep_enough_to_reach_the_line_fails(self):
        from src import fsd
        bad = fsd.fsd_violations(**dict(_site(), leaders=[('DS-1', 1.5)]))
        self.assertTrue(any('permits a projection at all' in b for b in bad), bad)


class EdgeTests(unittest.TestCase):
    """Every eave and rake of both buildings, sitework.roof_edges()."""

    def test_the_model_passes(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        from src.sitework import roof_edges
        self.assertEqual(rco_fsd.edge_violations(roof_edges()), [])

    def test_eight_edges_and_what_they_leave(self):
        from src.sitework import roof_edges
        got = {n: (None if w is None else round((w-o)*12, 6)) for n, _k, w, o, _b, _v in roof_edges()}
        self.assertEqual(got, {
            'BUILDING 1 SAGE EAVE': None, 'BUILDING 1 ADJACENT-PARCEL EAVE': 60.0,
            'BUILDING 1 S ELM RAKE': None, 'BUILDING 1 REAR RAKE': 30.0,
            'BUILDING 2 SAGE EAVE': None, 'BUILDING 2 ADJACENT-PARCEL EAVE': 60.0,
            'BUILDING 2 COURTYARD RAKE': 96.0, 'BUILDING 2 ALLEY RAKE': 204.0})

    def test_the_parcel_eaves_would_need_their_fireblock_an_inch_further_out(self):
        from codes.ohio.rco import fire_separation as rco_fsd
        from src.sitework import roof_edges
        edges = [(n, k, w, o+(1.0/12.0 if 'PARCEL' in n else 0.0), False, v) for n, k, w, o, _b, v in roof_edges()]
        bad = rco_fsd.edge_violations(edges)
        self.assertEqual(len(bad), 2, bad)
        edges = [(n, k, w, o+1.0/12.0, True, v) for n, k, w, o, _b, v in roof_edges()]
        self.assertEqual([b for b in rco_fsd.edge_violations(edges) if 'PARCEL' in b], [])



class GapTests(unittest.TestCase):

    def test_a_courtyard_that_changed_width_fails(self):
        from src import fsd
        bad = fsd.fsd_violations(**dict(_site(), b2_court_y=_site()['b1_rear_y']+11.0))
        self.assertTrue(any('measures' in b for b in bad), bad)

    def test_the_line_lands_where_c101_draws_it(self):
        from src import fsd
        from src.sitework import B1_REAR_Y, FSD_LINE_Y
        self.assertAlmostEqual(FSD_LINE_Y, 71.0)
        self.assertAlmostEqual(FSD_LINE_Y, fsd.line_y(B1_REAR_Y))


if __name__ == '__main__':
    unittest.main()

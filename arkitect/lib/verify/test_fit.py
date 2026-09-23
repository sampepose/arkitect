"""arkitect/lib/model/fit.py: the checks that measure the room a thing has to stand in."""
import unittest

from arkitect.lib.model import fit
from arkitect.lib.units import IN


class HeaderFitTests(unittest.TestCase):

    def test_lumber_depths_are_dressed_sizes(self):
        self.assertEqual(fit.lumber_depth('2-2x6'), IN(5.5))
        self.assertEqual(fit.lumber_depth('3-2x10'), IN(9.25))
        self.assertEqual(fit.lumber_depth('2-2x12'), IN(11.25))

    def test_the_room_is_the_plate_less_the_highest_head_less_the_plates(self):
        """An 8'-0" head under an 8'-9" plate leaves 6" below a double top plate."""
        self.assertAlmostEqual(fit.header_room(8.75, [8.0, 6.0+8/12.0]), IN(6.0))
        self.assertAlmostEqual(fit.header_room(9.0, [8.0]), IN(9.0))

    def test_a_2x12_does_not_stand_in_six_inches_and_a_2x6_does(self):
        room = fit.header_room(8.75, [8.0])
        self.assertFalse(fit.header_fit(fit.lumber_depth('2-2x12'), room))
        self.assertFalse(fit.header_fit(fit.lumber_depth('3-2x10'), room))
        self.assertTrue(fit.header_fit(fit.lumber_depth('2-2x6'), room))

    def test_an_lvl_is_checked_in_bending_shear_and_deflection(self):
        kw = dict(width=IN(3.5), depth=IN(5.5), fb=2600.0, fv=285.0, e=2.0e6)
        self.assertEqual(fit.lvl_violations(1100.0, 3.0, **kw), [])
        self.assertEqual(fit.lvl_violations(550.0, 5.0, **kw), [])
        bad = fit.lvl_violations(1100.0, 8.0, **kw)
        self.assertTrue(any('bending' in v for v in bad) and any('deflection' in v for v in bad), bad)
        self.assertTrue(any('shear' in v for v in fit.lvl_violations(6000.0, 1.0, **kw)))


class AlongAWallTests(unittest.TestCase):
    OPS = [fit.Opening(10.0, 13.0, 2.7, 8.7, 'L1 W-A'), fit.Opening(10.0, 13.0, 12.7, 18.7, 'L2 W-A'),
           fit.Opening(20.0, 23.0, 0.7, 7.4, 'L1 DOOR')]

    def test_openings_are_sorted_to_their_storey(self):
        self.assertEqual([o.name for o in fit.on_level(self.OPS, 0.7, 10.0)], ['L1 W-A', 'L1 DOOR'])
        self.assertEqual([o.name for o in fit.on_level(self.OPS, 10.7, 9.0)], ['L2 W-A'])

    def test_a_thing_along_the_wall_may_not_share_it_with_an_opening(self):
        l1 = fit.on_level(self.OPS, 0.7, 10.0)
        self.assertEqual([o.name for o in fit.across_opening(12.5, 2.7, l1)], ['L1 W-A'])
        self.assertEqual(fit.across_opening(15.0, 2.7, l1), [])
        self.assertEqual([o.name for o in fit.across_opening(14.5, 2.7, l1, clear=0.25)], ['L1 W-A'])   # within the casing

    def test_a_thing_that_rises_meets_every_level(self):
        self.assertEqual([o.name for o in fit.rises_at_opening(11.0, self.OPS)], ['L1 W-A', 'L2 W-A'])
        self.assertEqual(fit.rises_at_opening(14.0, self.OPS), [])
        self.assertEqual([o.name for o in fit.rises_at_opening(13.2, self.OPS, clear=0.3)], ['L1 W-A', 'L2 W-A'])

    def test_the_gap_along_a_wall(self):
        self.assertAlmostEqual(fit.along_wall_gap(14.07, 14.82), 0.75)


class CavityTests(unittest.TestCase):
    """A DWV line in a stud cavity, against what the assembly schedule fills that cavity with.
       The numbers below are the real case: a 3" stack is 3-1/2" across and its hub 4-1/2", a
       2x6 cavity is 5-1/2" deep, an R-21 batt is the whole 5-1/2", and the foam that replaces
       it in that one bay is 2"."""

    def bay(self, **kw):
        d = dict(name='STACK F', od=IN(3.5), fitting=IN(4.5), depth=IN(5.5), added=IN(1.5),
                 fill=IN(2.0), fill_name='CLOSED-CELL FOAM')
        d.update(kw)
        return fit.InCavity(**d)

    def test_the_deepened_bay_holds_the_fitting_and_the_fill(self):
        b = self.bay()
        self.assertAlmostEqual(fit.cavity_depth(b)*12, 7.0)
        self.assertAlmostEqual(fit.cavity_clear(b)*12, 0.5)
        self.assertEqual(fit.cavity_violations([b]), [])

    def test_the_stud_cavity_alone_does_not(self):
        """The reviewer's finding: 2" of fill and a 4-1/2" hub want 6-1/2" of a 5-1/2" bay."""
        b = self.bay(added=0.0)
        self.assertAlmostEqual(fit.cavity_clear(b)*12, -1.0)
        v = fit.cavity_violations([b])
        self.assertEqual(len(v), 1)
        self.assertIn('STACK F', v[0])
        self.assertIn('Deepen', v[0])
        self.assertAlmostEqual(fit.cavity_deepening_needed(b)*12, 1.0)

    def test_measuring_the_straight_pipe_passes_the_bay_the_fitting_fails(self):
        """The regression this check was rewritten for. Measured at the 3-1/2" PIPE the stud
           cavity closes exactly -- 2 + 3-1/2 = 5-1/2 -- so the first version of this check
           certified a bay with no room for a hub. A DWV line is governed by its fittings."""
        as_pipe = self.bay(added=0.0, fitting=IN(3.5))
        as_built = self.bay(added=0.0)
        self.assertAlmostEqual(fit.cavity_clear(as_pipe)*12, 0.0)
        self.assertEqual(fit.cavity_violations([as_pipe]), [])
        self.assertEqual(len(fit.cavity_violations([as_built])), 1)

    def test_the_batt_the_schedule_names_does_not_fit_behind_it(self):
        v = fit.cavity_violations([self.bay(fill=IN(5.5), fill_name='R-21 BATT')])
        self.assertEqual(len(v), 1)
        self.assertIn('R-21 BATT', v[0])

    def test_a_hub_narrower_than_its_pipe_is_refused(self):
        v = fit.cavity_violations([self.bay(fitting=IN(3.0))])
        self.assertEqual(len(v), 1)
        self.assertIn('never narrower', v[0])

    def test_deepening_needed_is_zero_where_the_cavity_already_holds_it(self):
        self.assertAlmostEqual(fit.cavity_deepening_needed(self.bay(depth=IN(7.25)))*12, 0.0)

    def test_a_two_inch_stack_and_its_hub_fit_the_stud_cavity_undeepened(self):
        from arkitect.lib.model import pipe
        ok = self.bay(added=0.0, od=pipe.od('2', 'IPS'), fitting=pipe.fitting_od('2'),
                      fill=IN(2.0))
        self.assertAlmostEqual(ok.fitting*12, 3.375)
        self.assertAlmostEqual(fit.cavity_clear(ok)*12, 0.125)
        self.assertEqual(fit.cavity_violations([ok]), [])


class DoorSwingTests(unittest.TestCase):
    """A door leaf against what stands on the floor it swings over. Synthetic geometry only:
       the projects hand this their own doors and appliances."""

    def leaf(self, x=0.0, y=0.0, ln=2.0, o='h', swing=-1, far=False):
        return fit.leaf_quadrant(x, y, ln, o, swing, far)._replace(name='THE LEAF')

    def box(self, x0, y0, x1, y1):
        return fit.Obstruction('THE WASHER', x0, y0, x1, y1)

    def test_a_horizontal_leaf_swings_to_increasing_plan_y_when_swing_is_negative(self):
        """The sign is the DRAWING's, in canvas sense, because that is what a sheet passes in."""
        lf = self.leaf(swing=-1)
        self.assertEqual((lf.y0, lf.y1), (0.0, 2.0))
        self.assertEqual((lf.x0, lf.x1), (0.0, 2.0))
        self.assertEqual(self.leaf(swing=1).y0, -2.0)

    def test_far_hangs_the_leaf_on_the_other_jamb(self):
        self.assertEqual(self.leaf(far=True).hinge_x, 2.0)
        self.assertEqual(self.leaf(far=False).hinge_x, 0.0)

    def test_something_beyond_the_leaf_is_never_touched(self):
        v = fit.door_swing_violations([self.leaf()], [self.box(2.5, 0.5, 4.0, 2.0)])
        self.assertEqual(v, [])

    def test_something_in_the_quadrant_but_outside_the_radius_is_never_touched(self):
        """The quadrant's BOX is not the quadrant: a corner of it is 2.83 leaf-lengths out."""
        lf = self.leaf(ln=2.0)
        self.assertAlmostEqual(fit.leaf_overlap(lf, self.box(1.9, 1.9, 2.0, 2.0)), 0.0)

    def test_a_washer_standing_in_the_opening_stops_the_leaf(self):
        """A real mechanical / laundry pair: the appliance across the last 9-1/2\" of the
           opening, its face 3\" off the wall centreline."""
        lf = self.leaf(ln=2.0+2.0/12)
        v = fit.door_swing_violations([lf], [self.box(-2.0, 0.25, 0.7917, 2.5)])
        self.assertEqual(len(v), 1)
        self.assertIn('THE WASHER', v[0])
        self.assertIn('THE LEAF', v[0])

    def test_swinging_it_the_other_way_clears_the_same_washer(self):
        lf = self.leaf(ln=2.0+2.0/12, swing=1)
        self.assertEqual(fit.door_swing_violations([lf], [self.box(-2.0, 0.25, 0.7917, 2.5)]), [])

    def test_an_inch_of_slack_is_not_a_finding(self):
        lf = self.leaf(ln=2.0)
        near = self.box(1.94, 0.0, 3.0, 1.0)          # 3/4" inside the arc
        self.assertGreater(fit.leaf_overlap(lf, near), 0.0)
        self.assertEqual(fit.door_swing_violations([lf], [near]), [])
        self.assertEqual(len(fit.door_swing_violations([lf], [near], tol=0.0)), 1)

    def test_a_vertical_leaf_reads_its_swing_the_other_way_round(self):
        """'v' is the orientation the original pair is drawn in, and its sign is the mirror's."""
        self.assertEqual(self.leaf(o='v', swing=1).x1, 2.0)
        self.assertEqual(self.leaf(o='v', swing=-1).x0, -2.0)



if __name__ == '__main__':
    unittest.main()

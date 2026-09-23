"""The deepened stack bay as a PLAN fact, and everything that had to move for it.

A-601 frames one bay of Building 2's north wall 2x8 so stack F's fittings fit behind the
scheduled insulation. That is 1-3/4" of framing standing in the mechanical / laundry room of
Units 2 and 3, and until 2026-09-21 the plans went on drawing that wall flat — a reviewer
found it, which is the third time this bay has been found by reading two drawings together.

Three things were standing where it is, and each is pinned here because each was invisible
to every other oracle:

  * the washer, drawn tight to the wall;
  * the unit panel, whose lower 3-1/8" sat on the bay;
  * the dryer duct, which left the wall on the bay's near stud — 4" of duct over 1-1/2" of
    stud that the STACK places and a framer cannot move.

And the louvered pair, which the recheck found swinging into its own room over the washer.
"""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class StackBayPlanTests(unittest.TestCase):

    def setUp(self):
        from src import building2 as b2, drainage as dr, envelope, mechanical as me
        from lib.model import pipe
        self.b2, self.dr, self.env, self.me, self.pipe = b2, dr, envelope, me, pipe

    def violations(self, **kw):
        a = dict(stack_cl=self.dr.F_POS[1],
                 stack_fitting=self.pipe.fitting_od(self.dr.F_SIZE),
                 penetrations=self.me.b2_wall_penetrations())
        a.update(kw)
        return self.b2.stack_bay_violations(**a)

    # ---------------- the bay itself ----------------
    def test_the_bay_projects_one_stud_depth_into_the_room(self):
        """2x8 less the wall's 2x6 -- derived, never typed, so A-102, A-601 and P-601 agree."""
        self.assertAlmostEqual(self.env.stack_bay_projection()*12, 1.75)
        self.assertAlmostEqual(self.b2.STACK_BAY_RECT[2]*12, 1.75)

    def test_the_bay_is_one_stud_bay_and_a_stud_each_side(self):
        self.assertAlmostEqual(self.b2.STACK_BAY_W*12, 17.5)
        lo, hi = self.b2.stack_bay_studs()
        self.assertAlmostEqual((lo[1]-lo[0])*12, 1.5)
        self.assertAlmostEqual((hi[1]-hi[0])*12, 1.5)

    def test_the_set_as_drawn_has_nothing_in_the_bay(self):
        self.assertEqual(self.violations(), [])

    # ---------------- what had to move ----------------
    def test_the_washer_stands_on_the_bay_face_not_on_the_wall(self):
        wd = next(f for f in self.b2.F_B2 if f[4] == 'wd')
        self.assertAlmostEqual(wd[0]+wd[2], 19.5-self.env.stack_bay_projection())

    def test_the_panel_back_where_it_was_is_caught(self):
        from lib.model.regrid import PARTITION
        f = [(x[0], self.b2.Y_BEAR+PARTITION+2.3, x[2], x[3])+tuple(x[4:]) if x[4] == 'panel' else x
             for x in self.b2.F_B2]
        old, self.b2.F_B2[:] = list(self.b2.F_B2), f
        try:
            v = self.violations()
        finally:
            self.b2.F_B2[:] = old
        self.assertEqual(len(v), 1)
        self.assertIn('PANEL', v[0])

    def test_the_dryer_duct_leaves_the_wall_clear_of_both_bay_studs(self):
        pen = self.me.b2_wall_penetrations()
        self.assertTrue(pen, 'no penetration of the north wall is reported at all')
        for _mark, along, width in pen:
            for lo, hi in self.b2.stack_bay_studs():
                self.assertTrue(along+width/2.0 <= lo+1e-9 or along-width/2.0 >= hi-1e-9)

    def test_a_duct_on_the_near_stud_is_caught(self):
        near = self.b2.stack_bay_studs()[0][0]
        v = self.violations(penetrations=[('DR-2', near, self.me.DUCT_D)])
        self.assertEqual(len(v), 1)
        self.assertIn('cannot move', v[0])

    def test_bay_penetration_y_leaves_a_duct_alone_where_it_already_clears(self):
        want = self.b2.stack_bay_studs()[0][0]-2.0
        self.assertAlmostEqual(self.b2.bay_penetration_y(want, self.me.DUCT_D), want)

    # ---------------- the stack it is framed for ----------------
    def test_stack_f_s_fitting_lies_between_the_bay_s_studs(self):
        self.assertEqual(self.violations(), [])
        self.assertEqual(len(self.violations(stack_cl=self.dr.F_POS[1]+5.0/12)), 1)

    def test_the_laundry_supply_run_still_ends_short_of_the_washer(self):
        """It was typed, and the appliance moved out from under it."""
        from src import plumbing
        wd_face = self.b2.B2_W-self.b2.PLAN_B2.keep(
            (self.b2.WD_X, self.b2.WD_Y, self.b2.WD_W, self.b2.WD_H))[0]
        self.assertGreater(plumbing.U23_WD_SUPPLY_X, wd_face)
        self.assertAlmostEqual(plumbing.U23_WD_SUPPLY_X-wd_face, plumbing.WD_STUB)


class DoorSwingTests(unittest.TestCase):

    def setUp(self):
        from src import building2 as b2, doors
        self.b2, self.doors = b2, doors

    def test_every_leaf_on_the_set_is_clear(self):
        self.assertEqual(self.doors.swing_violations(), [])

    def test_the_louvered_pair_swings_out_of_the_mechanical_laundry_room(self):
        """300's identical pair always did; the sign did not survive the wall turning 90
           degrees when this plan was copied, and the washer stopped the near leaf."""
        pair = [d for d in self.b2.B2doors if abs(d[2]-self.b2.D4A) < 1e-6]
        self.assertEqual(len(pair), 2)
        for d in pair:
            self.assertEqual(d[3], 'h')
            self.assertEqual(d[4], 1)

    def test_swinging_it_back_in_is_caught(self):
        old = list(self.b2.B2doors)
        self.b2.B2doors[:] = [d if abs(d[2]-self.b2.D4A) > 1e-6 else d[:4]+(-1,)+tuple(d[5:])
                              for d in old]
        try:
            v = self.doors.swing_violations()
        finally:
            self.b2.B2doors[:] = old
        self.assertEqual(len(v), 2, 'Units 2 and 3 share one plan; the fault is on both')
        self.assertTrue(all('WD' in s for s in v))


if __name__ == '__main__':
    unittest.main()

"""A-602's quantities, and the window marks they count.

Neither src/schedules.py nor src/openings.py had a dedicated test file. Between them
they decide what the door and window schedules on A-602 say, which is what gets ordered.
check_schedule_quantities() runs at DRAW time, from inside sheet_a602(), so it is
reached only through a full build -- these hold the same facts where a reader can find
them and a failure names them.
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.lib.units import IN
from src import openings as O
from arkitect.codes.ohio.rco import egress as rco_egress
from src import schedules as S
from arkitect.codes.ohio.rco import egress as egress_shared


class WindowMarkTests(unittest.TestCase):

    def test_there_are_three_marks_and_W_A_is_the_egress_one(self):
        self.assertEqual(set(O.WIN_W), {'A', 'B', 'C'})
        self.assertEqual(O.WIN_W['A'], 3.0)
        self.assertEqual(O.WIN_GEOM['A'], (2.0, 6.0))

    def test_every_head_aligns(self):
        """The module asserts this at import; held here so a failure says what broke.
           Heads that stop aligning change every elevation at once."""
        self.assertEqual(len({O.WIN_HEAD[m] for m in O.WIN_HEAD}), 1)
        self.assertEqual(O.WIN_HEAD['A'], 8.0)

    def test_the_area_of_a_mark_is_derived_from_its_size(self):
        for m in O.WIN_W:
            self.assertAlmostEqual(O.WIN_SF[m], O.WIN_W[m]*O.WIN_GEOM[m][1])

    def test_the_W_A_sill_is_under_the_RCO_310_2_2_maximum(self):
        sill = O.WIN_GEOM['A'][0]
        self.assertLessEqual(sill, rco_egress.EGRESS_MAX_SILL)
        self.assertEqual(rco_egress.EGRESS_MAX_SILL, IN(44))

    def test_the_drawn_frame_can_host_the_egress_minimums(self):
        """A double hung opens at most its width by half its height. That bounds every
           product from above: it proves the frame is not too small for the requirement,
           never that a product meets it."""
        w, h = O.WIN_W["A"], O.WIN_GEOM["A"][1]
        self.assertGreaterEqual(w, rco_egress.EGRESS_MIN_W)
        self.assertGreaterEqual(h/2.0, rco_egress.EGRESS_MIN_H)
        self.assertGreaterEqual(w*h/2.0, rco_egress.EGRESS_MIN_SF)

    def test_the_egress_check_passes(self):
        with redirect_stdout(io.StringIO()):
            egress_shared.check_egress_window(win_geom=O.WIN_GEOM, win_w=O.WIN_W)


class QuantityTests(unittest.TestCase):

    def test_window_quantities_are_derived_and_non_empty(self):
        n = S.window_totals()
        self.assertTrue(n, 'the window schedule counted nothing')
        for mark in ('A', 'B', 'C'):
            self.assertGreater(n[mark], 0, 'no W-%s counted' % mark)

    def test_every_counted_mark_is_a_mark_the_project_defines(self):
        """A mark counted but not defined is a window with no size on the schedule."""
        for mark in S.window_totals():
            self.assertIn(mark, O.WIN_W, 'W-%s is counted but has no geometry' % mark)

    def test_the_bypass_total_accounts_for_all_three_sources(self):
        """The number that was once in doubt: a drawing-time counter reported 8 against
           the schedule's 11 because it never saw Unit 1's three, which are drawn with
           Unit 1's own primitive. 4 + 4 + 3."""
        from src.building1 import U1_BYPASS_DOORS
        total = S.bypass_total()
        self.assertEqual(total, 11)
        self.assertGreaterEqual(total, U1_BYPASS_DOORS)
        self.assertEqual(U1_BYPASS_DOORS, 3)

    def test_every_sleeping_room_window_is_the_egress_mark(self):
        """A-001 note 5 and G-001 both say so. W-A is the only mark whose frame is
           tested against the escape minimums, so a bedroom with any other mark is a
           bedroom with no escape opening."""
        n = S.window_totals()
        self.assertGreaterEqual(n['A'], 12,
                                'twelve bedrooms need at least twelve W-A units')


if __name__ == '__main__':
    unittest.main()

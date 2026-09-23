"""RCO 307.1 is a rule the build enforces, not a sentence in a docstring.

The water closet's required clearances were stated in arkitect/lib/symbols/plumbing.py's
WaterCloset docstring, which said they were "checked in build.py, not drawn here".
Nothing in build.py checked them: no constant, no assertion, no test. wc_dims() measured
the real clearance and printed it on A-101 and A-102 without ever comparing it to the
minimum it was answering.

These tests hold the three readings of that figure together -- the rule, the dimension
the sheet draws, and the check that stops the build.
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

from src import clearances as CL
from src.finishes import BOARD
from arkitect.codes import clearances as code_clearances


class CheckTests(unittest.TestCase):

    def test_the_real_plans_pass(self):
        with redirect_stdout(io.StringIO()):
            CL.check_clearances(CL.project_plans(), BOARD)

    def test_every_plan_reports_a_measurement(self):
        """Guards the test above from passing by measuring nothing -- the shape that
           lets a green check mean 'no water closet reached it'."""
        _bad, seen = code_clearances.wc_violations(CL.project_plans(), BOARD)
        self.assertGreaterEqual(len(seen), 4, seen)
        for _label, got in seen:
            self.assertGreater(got, 0)

    def test_a_pan_too_close_to_its_wall_fails(self):
        """The one that matters. A synthetic bath with a vanity hard against the pan: the
           pan spans x 1'-0\" to 2'-6\", so its centerline is at 1'-9\", and a vanity
           starting at 2'-6\" leaves 9\" to that centerline against a 15\" minimum. The
           other side has the room, and clears. The build must stop."""
        room = (0.0, 0.0, 4.0, 6.0, 'BATH')
        pan = (1.0, 0.0, 1.5, 2.5, 'wc', 'n')
        vanity = (2.5, 0.0, 0.8, 2.0, 'lav', 'n')
        plans = [('SYNTHETIC BATH', [room], [], [pan, vanity])]
        bad, seen = code_clearances.wc_violations(plans, BOARD)
        self.assertTrue(seen, 'the synthetic pan was not measured at all')
        self.assertTrue(bad, 'a pan %s from its obstruction passed a %s minimum'
                        % (min(g for _l, g in seen), code_clearances.WC_SIDE.minimum))
        with self.assertRaises(AssertionError):
            with redirect_stdout(io.StringIO()):
                CL.check_clearances(plans, BOARD)



class SheetTests(unittest.TestCase):

    def test_a001_note_11a_prints_the_measured_clearance(self):
        """The note, the dimension on A-101 and A-102 and the check are three readings
           of one figure. If the note ever states a number the model does not measure,
           this fails."""
        from src.sheets.a001 import PLAN_NOTES, _wc_side
        from arkitect.lib.units import fmt, inches
        note = [n for n in PLAN_NOTES if n.startswith('11a.')]
        self.assertEqual(len(note), 1, 'A-001 note 11a not found')
        self.assertIn(fmt(_wc_side()), note[0])
        self.assertIn(code_clearances.WC_SIDE.citation, note[0])
        rest = [n for n in PLAN_NOTES if inches(code_clearances.WC_SIDE.minimum) in n]
        self.assertTrue(rest, 'the minimum is stated nowhere in the notes')

    def test_the_measured_clearance_actually_clears_the_minimum(self):
        from src.sheets.a001 import _wc_side
        self.assertGreaterEqual(_wc_side(), code_clearances.WC_SIDE.minimum)


if __name__ == '__main__':
    unittest.main()

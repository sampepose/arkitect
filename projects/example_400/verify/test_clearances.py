"""RCO 307.1 at 400 Oak, and the deduction that makes the figure true.

Bath 1's pan was centered in the band between the hall wall's STUD face and the shower.
That read 15-1/4" to each side and the sheet printed it, but a stud face is not a wall:
with the room's 1/2" board on it the pan stood 14-3/4" off the drywall, under the 15"
A-001 note 7 quoted three lines below the number. The other 15-1/4" was to the shower,
which needs no deduction and was true as drawn -- so the fault was in exactly one of the
six clearances this set measures, and every oracle was green on it.

These tests hold the three readings together -- the rule, the dimension the sheet draws,
and the check that stops the build -- AND pin the deduction itself, because a measurement
that silently stops taking the finish off is the way this comes back.
"""
import io
import unittest
from contextlib import redirect_stdout

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class CheckTests(unittest.TestCase):

    def test_the_real_plans_pass(self):
        from src import clearances as CL
        from src.finishes import BOARD
        with redirect_stdout(io.StringIO()):
            CL.check_clearances(CL.project_plans(), BOARD)

    def test_every_plan_reports_a_measurement(self):
        """Guards the test above from passing by measuring nothing -- the shape that
           lets a green check mean 'no water closet reached it'."""
        from src import clearances as CL
        from src.finishes import BOARD
        from arkitect.codes import clearances as code_clearances
        _bad, seen = code_clearances.wc_violations(CL.project_plans(), BOARD)
        self.assertGreaterEqual(len(seen), 6, seen)
        for _label, got in seen:
            self.assertGreater(got, 0)

    def test_bath_1_clears_the_minimum_to_its_drywall(self):
        """Unit 1's Level 1 pan, the one that did not. Measured with the board on, both
           sides clear 15"; the margin is small, so this states it rather than leaving
           the next reader to find it in a build log."""
        from src import clearances as CL
        from src.finishes import BOARD
        from arkitect.codes.clearances import WC_SIDE
        from arkitect.lib.model.dimensions import wc_clearances
        got = [min(m['cl'] - m['lo'], m['hi'] - m['cl'])
               for lab, r, po, fu in CL.project_plans() if lab == 'UNIT 1 LEVEL 1'
               for m in wc_clearances(r, po, fu, BOARD)]
        self.assertEqual(len(got), 1, got)
        self.assertGreaterEqual(got[0], WC_SIDE.minimum)

    def test_the_finish_is_actually_deducted_from_a_wall(self):
        """The pin. A synthetic bath whose pan is centered in the STUD band with exactly
           the code minimum each side: measured to the studs it passes, measured to the
           finished wall it cannot. If the deduction is ever dropped, this goes green
           for the wrong reason and fails."""
        from arkitect.codes import clearances as code_clearances
        from arkitect.lib.units import IN
        m = code_clearances.WC_SIDE.minimum
        room = (0.0, 0.0, 2 * m, 6.0, 'BATH')
        pan = (m - 0.5, 0.0, 1.0, 2.5, 'wc', 'n')      # centerline at exactly m
        plans = [('SYNTHETIC BATH', [room], [], [pan])]
        bad, seen = code_clearances.wc_violations(plans, 0.0)
        self.assertFalse(bad, 'to the studs this pan keeps its %s exactly' % m)
        self.assertEqual(len(seen), 2)
        bad, _seen = code_clearances.wc_violations(plans, IN(0.5))
        self.assertEqual(len(bad), 2,
                         'both sides lost 1/2" of wall and neither was reported')

    def test_a_fixture_takes_no_finish_deduction(self):
        """The other half of the rule, and why the ADU's 15-1/4" to its tub was never
           wrong: a fixture stands in the room with its finished face where it is drawn,
           so the deduction applies to the wall behind it and not to the fixture."""
        from arkitect.codes import clearances as code_clearances
        from arkitect.lib.units import IN
        m = code_clearances.WC_SIDE.minimum
        room = (0.0, 0.0, 10.0, 6.0, 'BATH')
        pan = (4.0, 0.0, 1.0, 2.5, 'wc', 'n')          # centerline at 4.5
        tub = (4.5 - m - 2.5, 0.0, 2.5, 5.0, 'tub')    # its face exactly m from that
        plans = [('SYNTHETIC BATH', [room], [], [pan, tub])]
        for finish in (0.0, IN(0.5)):
            bad, seen = code_clearances.wc_violations(plans, finish)
            self.assertTrue(seen)
            self.assertFalse(bad, 'the tub side moved when the wall finish changed')


class SheetTests(unittest.TestCase):

    def test_a001_says_this_dimension_is_to_finished_surfaces(self):
        """A-001 note 1 puts every dimension on the sheet at the face of stud. The water
           closet clearances are the one exception, and a reader who applies note 1 to
           them would deduct the board a second time -- so the exception is stated where
           the convention is."""
        from src.sheets import a001
        note = [n for n in a001.plan_notes() if n.startswith('1a.')]
        self.assertEqual(len(note), 1, 'A-001 note 1a not found')
        self.assertIn('FINISHED SURFACES', note[0])
        self.assertIn('NOTE 7', note[0])

    def test_note_7_prints_the_measured_clearance(self):
        from src.sheets import a001
        from arkitect.codes import clearances as code_clearances
        from arkitect.lib.units import inches
        note = [n for n in a001.plan_notes() if n.startswith('7.')]
        self.assertEqual(len(note), 1, 'A-001 note 7 not found')
        self.assertIn(inches(a001._wc_side()), note[0])
        self.assertIn(inches(code_clearances.WC_SIDE.minimum), note[0])

    def test_the_measured_clearance_actually_clears_the_minimum(self):
        from src.sheets import a001
        from arkitect.codes import clearances as code_clearances
        self.assertGreaterEqual(a001._wc_side(), code_clearances.WC_SIDE.minimum)


if __name__ == '__main__':
    unittest.main()

"""400 Oak's A-603: the Unit 3 stair's figures are the model's, and no 300 vocabulary is
   left on the sheet."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class StairSheetTests(unittest.TestCase):

    def test_the_risers_make_the_rise_from_the_stoop(self):
        from src.sheets import a603
        from src import levels, stairs
        s = stairs.EXT_STAIR
        self.assertAlmostEqual(a603.RISER*s.risers, levels.FF2-s.stoop_above_grade)
        self.assertLessEqual(a603.RISER, 8.25/12.0)
        self.assertGreaterEqual(a603.TREAD, 9.0/12.0)

    def test_the_notes_are_this_lots(self):
        from src.sheets import a603
        from src import stairs
        from arkitect.lib.units import fmt
        text = " ".join(a603.NOTES)
        for stale in ("A-001", "A-604", "UNIT 5", "BOTH STAIRS", "BOTH EXTERIOR", "13a"):
            self.assertNotIn(stale, text)
        # The total rise is what a stringer is laid out from: 15 risers of the sixteenth-inch
        # figure, 8-1/16", would be 120-15/16", not the 120-1/2" the stoop and Level 2 leave.
        self.assertIn(fmt(stairs.EXT_STAIR.rise), text)
        self.assertIn("8-1/32\"", text)
        self.assertNotIn("8-1/16\"", text)
        self.assertIn("UNIT 3", text)

    def test_the_projection_limit_is_the_lines(self):
        from src.sheets import a603
        from src import fsd
        from arkitect.lib.units import fmt
        self.assertIn(fmt(fsd.PROJ_MAX), a603.NOTES[6])
        self.assertGreaterEqual(fsd.PROJ_MAX, a603.WIDTH)


if __name__ == '__main__':
    unittest.main()

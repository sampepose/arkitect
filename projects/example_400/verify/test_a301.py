"""400 Oak's A-301: the section's stair is building1's, its headroom the checked one, and
   the stacking diagram's areas are G-001's."""
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class SectionTests(unittest.TestCase):

    def test_the_headroom_is_the_checked_one(self):
        from src.sheets import a301
        from src.building1 import HEADROOM_MIN, b1_stair
        self.assertEqual(a301.STAIR['headroom'], b1_stair()['headroom'])
        self.assertGreaterEqual(a301.STAIR['headroom'], HEADROOM_MIN)

    def test_the_stacking_areas_are_g001s(self):
        from src.sheets import a301, g001
        for u in g001.UNITS:
            self.assertIn("{:,.0f} SF".format(g001.gross_sf(u)), a301._unit(int(u[0])))

    def test_the_sheet_is_in_the_set(self):
        from src.sheets.g001 import SHEET_INDEX
        self.assertIn("A-301", [n for n, _t in SHEET_INDEX])


if __name__ == '__main__':
    unittest.main()

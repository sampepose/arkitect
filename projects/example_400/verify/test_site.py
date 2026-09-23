"""400 Oak's site: the checks src/sitework.py holds C-102 to, each proved to fire, and
   C-102 built as its own document."""
import importlib
import os
import tempfile
import unittest

from projects.example_400.verify import PROJ, enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


def fresh():
    from src import sitework
    return importlib.reload(sitework)


class SiteTests(unittest.TestCase):

    def tearDown(self):
        fresh()             # put back whatever a test patched, before the build test runs

    def test_the_site_passes(self):
        fresh().check_site()

    def test_the_figures(self):
        s = fresh()
        self.assertEqual((s.SITE_W, s.SITE_D, s.ALLEY_W), (30.0, 124.0, 20.0))
        self.assertEqual(s.COURT, 15.0)
        self.assertEqual(s.LOT_AREA, 3720.0)
        self.assertEqual(s.REAR_PROV, 1980.0)
        self.assertAlmostEqual(s.ADU_REAR_PCT, 100.0/3.0)
        self.assertEqual(s.MANEUVER_HAVE, 20.0)
        self.assertEqual(s.VARIANCES, [])

    def _fails(self, words, **patch):
        s = fresh()
        for k, v in patch.items():
            setattr(s, k, v)
        bad = s.site_violations()
        self.assertTrue(any(words in b for b in bad), bad)

    def test_a_building_in_the_front_yard_fails(self):
        self._fails("front yard", FRONT_YARD=26.0)

    def test_too_few_stalls_fails(self):
        self._fails("stalls", PARK_N=1)

    def test_a_short_alley_fails_maneuvering(self):
        self._fails("maneuvering", MANEUVER_HAVE=19.8)

    def test_building_2_over_55_percent_of_the_rear_yard_fails(self):
        self._fails("55 percent", ADU_REAR_PCT=56.0)

    def test_a_walk_that_stops_short_of_dana_fails(self):
        s = fresh()
        self._fails("Oak", WALK_SIDE=(s.WALK_SIDE[0], 1.0)+s.WALK_SIDE[2:])

    def test_the_parking_walk_joins_the_pad_to_the_courtyard_walk(self):
        s = fresh()
        self.assertIn(s.WALK_PARK, s.WALKS)
        self.assertEqual(s.WALK_PARK[3], s.PARK_Y0)
        self._fails("does not start at the pad", WALK_PARK=s.WALK_PARK[:3]+(s.PARK_Y0-2.0,))
        self._fails("does not reach the courtyard walk", WALK_PARK=(s.WALK_PARK[0], s.WALK_COURT[1]+4.0)+s.WALK_PARK[2:])

    def test_a_courtyard_walk_that_misses_the_stoop_fails(self):
        s = fresh()
        self._fails("stoop", WALK_COURT=(s.STAIR[0]+2.0,)+s.WALK_COURT[1:])


class ZoningSheetTests(unittest.TestCase):

    def test_c102_is_its_own_document(self):
        from lib import buildscript
        b = buildscript.load(os.path.join(PROJ, "build.py"))
        self.assertEqual([f.__name__ for f in b.DOCUMENTS], ["build_set", "build_zoning_sheet"])
        with tempfile.TemporaryDirectory() as d:
            out = b.build_zoning_sheet(output_path=os.path.join(d, "c102.pdf"))
            self.assertGreater(os.path.getsize(out), 1000)


if __name__ == '__main__':
    unittest.main()

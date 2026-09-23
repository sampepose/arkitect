"""400 Oak's foundations: check_foundation() passes, and fires when a strip leaves the
   wall it carries or a pad leaves the building face it serves."""
import importlib
import unittest

from projects.example_400.verify import enter, leave


def setUpModule():
    enter()


def tearDownModule():
    fresh()
    leave()


def fresh():
    from src import foundation
    return importlib.reload(foundation)


class FoundationTests(unittest.TestCase):

    def tearDown(self):
        fresh()

    def test_the_foundations_pass(self):
        fresh().check_foundation()

    def test_the_house_strip_is_under_the_stair_wall(self):
        f = fresh()
        x0, y0, x1, y1, nm = f.B1.strips[0]
        from src.building1 import STAIR_WALL
        self.assertAlmostEqual((x0+x1)/2.0, (STAIR_WALL[0]+STAIR_WALL[2])/2.0)
        self.assertEqual(nm, "UNIT 1 STAIR WALL")

    def test_a_strip_off_its_wall_fails(self):
        f = fresh()
        x0, y0, x1, y1, nm = f.B1.strips[0]
        f.B1.strips[0] = (x0+1.0, y0, x1+1.0, y1, nm)
        with self.assertRaises(AssertionError):
            f.check_foundation()

    def test_a_pad_off_the_building_face_fails(self):
        f = fresh()
        x0, y0, x1, y1, nm = f.B1.pads[0]
        f.B1.pads[0] = (x0, y0-1.0, x1, y1-1.0, nm)
        with self.assertRaises(AssertionError):
            f.check_foundation()


class BearingTests(unittest.TestCase):

    def tearDown(self):
        fresh()

    def test_every_footing_strip_and_pier_is_under_the_soil(self):
        f = fresh()
        rows = f.bearing()
        names = [r[0] for r in rows]
        for nm in ("B1 SIDE WALLS", "B1 STAIR WALL", "B2 BEARING WALL", "PIER P1", "PIER P4"):
            self.assertIn(nm, names)
        from arkitect.codes.ohio.columbus import criteria
        self.assertTrue(all(q <= criteria.SOIL_BEARING for _n, _l, _w, q in rows))

    def test_a_heavier_floor_overloads_the_side_walls(self):
        f = fresh()
        f.FLOOR_PSF = 150
        with self.assertRaises(AssertionError) as e:
            f.check_bearing()
        self.assertIn("B1 SIDE WALLS", str(e.exception))

    def test_a_pier_off_the_stair_fails(self):
        f = fresh()
        x, y, d, mk = f.B2.piers[0]
        f.B2.piers[0] = (x+10.0, y, d, mk)
        with self.assertRaises(AssertionError):
            f.check_foundation()


class RevealTests(unittest.TestCase):
    """The foundation stands 8" out of finished grade, over RCO 404.1.6's 6", and every
       exterior pad and the Unit 3 stoop step down to grade the same 7-3/4"."""

    def test_the_slab_top_is_8_inches_above_grade(self):
        from src import levels, stairs
        self.assertAlmostEqual((levels.SLAB_TOP-levels.GRADE)*12, 8.0)
        self.assertAlmostEqual(stairs.STOOP_TOP*12, 7.75)
        self.assertLessEqual(stairs.EXT_STAIR.riser*12, 8.25)

    def test_a_reveal_under_6_inches_fails(self):
        from src import levels
        levels = importlib.reload(levels)
        try:
            levels.SLAB_TOP = levels.GRADE+5.75/12.0
            with self.assertRaises(AssertionError):
                levels.check()
        finally:
            importlib.reload(levels)


if __name__ == '__main__':
    unittest.main()

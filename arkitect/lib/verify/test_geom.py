"""arkitect/lib/model/geom.py's two model-space helpers: which room a point falls in, and what
   reaches past a building's walls."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from arkitect.lib.model import geom

# An L: a 10 x 10 square with its upper-right 5 x 5 quarter taken out.
L = [(0, 0), (5, 0), (5, 5), (10, 5), (10, 10), (0, 10)]


class InsideTests(unittest.TestCase):

    def test_a_point_in_the_l_is_inside(self):
        self.assertTrue(geom.inside((2, 2), L))
        self.assertTrue(geom.inside((8, 8), L))

    def test_a_point_in_the_notch_is_not(self):
        self.assertFalse(geom.inside((8, 2), L))

    def test_a_point_off_the_polygon_is_not(self):
        self.assertFalse(geom.inside((11, 5), L))


class BeyondTests(unittest.TestCase):

    def test_everything_inside_names_nothing(self):
        rooms = [(1, 1, 2, 2, "BATH")]
        polys = [(L, [(2, 2, "LIVING")])]
        furn = [(1, 1, 1, 1, 'wc')]
        self.assertEqual(geom.beyond(rooms, polys, furn, 0, 10, 0, 10), [])

    def test_each_kind_that_crosses_a_wall_is_named(self):
        rooms = [(9, 1, 2, 2, "BATH")]
        polys = [([(0, 0), (12, 0), (12, 4), (0, 4)], [(2, 2, "LIVING")])]
        furn = [(1, 9.5, 1, 1, 'wc')]
        self.assertEqual(geom.beyond(rooms, polys, furn, 0, 10, 0, 10),
                         ["BATH", "LIVING", "wc"])


if __name__ == '__main__':
    unittest.main()

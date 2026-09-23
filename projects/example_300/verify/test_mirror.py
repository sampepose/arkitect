"""The two mirrors: the sheet flip, and the Units 2/3 reflection about the centerline.

src/mirror.py had no dedicated test and zero of its function statements ran during the
suite. It is the module CLAUDE.md names as the costliest trap in the project -- every
sheet is flipped left to right and Units 2/3 are reflected again, so a source literal is
pre-mirror and anything read back is post-mirror -- and the whole point of doing it in
one place is that a mirror has to reach EVERYTHING at once. The danger is not that one
map is wrong; it is that one kind of object gets left out and lands on the far side of
the plan from everything else.

So these test the property that matters: an involution that carries handedness with
position, applied to every kind of object the model carries.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from src import mirror as M


class AxisTests(unittest.TestCase):

    def test_the_reflection_axis_is_the_building_centerline(self):
        self.assertEqual(M.B1_W, 26.0)

    def test_rx_reflects_about_it(self):
        self.assertAlmostEqual(M.rx(0.0), 26.0)
        self.assertAlmostEqual(M.rx(26.0), 0.0)
        self.assertAlmostEqual(M.rx(13.0), 13.0, msg='the centerline is its own image')

    def test_rx_is_an_involution(self):
        for v in (0.0, 0.5, 9.1, 13.0, 25.5, 26.0):
            self.assertAlmostEqual(M.rx(M.rx(v)), v)

    def test_rxw_reflects_a_span_by_its_low_edge(self):
        """A rectangle's low edge is not its reflected low edge -- the width has to come
           off, or everything w wide lands w to the right of where it belongs."""
        lo, w = 9.1, 5.0
        self.assertAlmostEqual(M.rxw(lo, w), M.rx(lo+w))
        self.assertAlmostEqual(M.rxw(lo, w)+w, M.rx(lo))

    def test_rspan_keeps_lo_below_hi(self):
        lo, hi = M.rspan(4.0, 9.0)[:2]
        self.assertLess(lo, hi)
        self.assertAlmostEqual(lo, M.rx(9.0))
        self.assertAlmostEqual(hi, M.rx(4.0))

    def test_rspan_carries_its_extra_fields_through(self):
        out = M.rspan(4.0, 9.0, 'HOLD', 7)
        self.assertEqual(out[2:], ('HOLD', 7))

    def test_rpts_reflects_x_and_leaves_y(self):
        pts = [(0.5, 24.45), (8.7, 24.45), (8.7, 31.95)]
        out = M.rpts(pts)
        self.assertEqual([y for _x, y in out], [y for _x, y in pts])
        self.assertEqual([x for x, _y in out], [M.rx(x) for x, _y in pts])

    def test_rjoist_reflects_a_span_end_for_end(self):
        a, y, b, label = 4.0, 30.0, 9.0, 'F1'
        ra, ry, rb, rlabel = M.rjoist((a, y, b, label))
        self.assertEqual((ry, rlabel), (y, label))
        self.assertLess(ra, rb, 'a reflected span still runs low to high')
        self.assertAlmostEqual(rb-ra, b-a, msg='reflection is not a scaling')


class WrapperTests(unittest.TestCase):
    """Every kind of model object has an r* wrapper, and each one must move its own
       handedness with it."""

    def test_a_room_reflects_and_keeps_its_size(self):
        r = (9.1, 24.45, 5.0, 7.1, 'BATH')
        out = M.rrooms([r])[0]
        self.assertAlmostEqual(out[2], r[2])
        self.assertAlmostEqual(out[3], r[3])
        self.assertAlmostEqual(out[0], M.rxw(r[0], r[2]))
        self.assertAlmostEqual(out[1], r[1], msg='y does not move in this mirror')
        self.assertEqual(out[4], 'BATH')

    def test_a_reflected_room_reflects_back(self):
        r = (9.1, 24.45, 5.0, 7.1, 'BATH')
        back = M.rrooms(M.rrooms([r]))[0]
        for i in range(4):
            self.assertAlmostEqual(back[i], r[i])

    def test_furniture_facing_flips_with_its_position(self):
        """A fitting facing east must face west on the other side of the axis, or it is
           drawn against the wrong wall."""
        f = (1.0, 30.0, 2.0, 1.5, 'lav', 'e')
        out = M.rfurn([f])[0]
        self.assertEqual(out[5], 'w')
        self.assertAlmostEqual(out[0], M.rxw(f[0], f[2]))
        self.assertEqual(M.rfurn(M.rfurn([f]))[0][5], 'e')

    def test_a_north_or_south_facing_fitting_does_not_flip(self):
        """The mirror is left-right. A fitting on a horizontal wall keeps its facing."""
        for face in ('n', 's'):
            out = M.rfurn([(1.0, 30.0, 2.0, 1.5, 'lav', face)])[0]
            self.assertEqual(out[5], face)

    def test_loose_furniture_survives_the_reflection(self):
        """rfurn passes drop_loose=False: the studies' loose furniture is reflected with
           everything else, because the dimensioning code needs the same set."""
        out = M.rfurn([(1.0, 30.0, 3.0, 2.0, 'sofa', 'w')])
        self.assertEqual(len(out), 1)

    def test_every_r_wrapper_exists_for_a_kind_the_model_carries(self):
        for name in ('rrooms', 'rdoors', 'rwins', 'rops', 'rnotes', 'rtags',
                     'rpoly', 'rfurn'):
            self.assertTrue(callable(getattr(M, name)), name)


class OrientationTests(unittest.TestCase):
    """The words the sheets print for which side is which. Swap these and the notes
       describe the building back to front while the geometry stays put."""

    def test_the_living_side_is_safford_and_the_bedrooms_face_the_parcel(self):
        self.assertEqual(M.LIVE_SIDE, 'SAGE')
        self.assertEqual(M.BED_SIDE, 'ADJACENT-PARCEL')
        self.assertNotEqual(M.LIVE_SIDE, M.BED_SIDE)

    def test_the_side_street_yard_is_the_8_foot_building_line(self):
        self.assertIn("8'-0", M.LIVE_SIDE_YARD)


if __name__ == '__main__':
    unittest.main()

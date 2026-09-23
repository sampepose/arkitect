"""Wheel stops in the three stalls behind Building 2, C.C. 3312.45, and the Unit 4 escape openings they leave clear."""
import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class WheelStopTests(unittest.TestCase):

    def test_one_stop_centred_in_each_stall_two_and_a_half_feet_off_the_wall(self):
        from src import sitework as s
        self.assertEqual(len(s.WHEEL_STOPS), s.PARK_N)
        for i, (x0, y0, x1, y1) in enumerate(s.WHEEL_STOPS):
            self.assertAlmostEqual((x0+x1)/2.0, s.PARK_X0+(i+0.5)*s.PARK_PITCH)
            self.assertAlmostEqual(x1-x0, 6.0)
            self.assertAlmostEqual(y0-s.PARK_Y0, 2.5)
        self.assertAlmostEqual(s.WSTOP_H, 5/12.0)

    def test_the_stops_leave_the_stalls_and_the_zoning_figures_alone(self):
        from src import sitework as s
        self.assertEqual((s.PARK_X0, s.PARK_N, s.PARK_D), (s.VISION, 3, 18.0))
        self.assertAlmostEqual(s.PARK_Y1-s.PARK_Y0, s.PARK_D)
        self.assertEqual(len(s.VARIANCES), 5)

    def test_the_maneuvering_request_is_two_and_a_half_feet(self):
        # The alley right-of-way is 17'-6" (the designer, 2026-09-16) and the pad gives nothing past
        # 18'-0", so C.C. 3312.25's 20'-0" is short by 2'-6" — the figure the request states.
        from src import sitework as s
        self.assertAlmostEqual(s.ALLEY_W, 17.5)
        self.assertAlmostEqual(s.MANEUVER_HAVE, 17.5)
        self.assertAlmostEqual(s.MANEUVER-s.MANEUVER_HAVE, 2.5)
        self.assertAlmostEqual(s.MANEUVER_SHORT, 2.5)

    def test_the_rear_openings_stand_one_over_each_stall(self):
        from src import sitework as s
        rear = sorted((o for o in s.b2_openings() if o[2] == "REAR"), key=lambda o: o[3])
        self.assertEqual([(o[0], o[1]) for o in rear], [("BEDROOM 2", "A"), ("BATH", "B"), ("BEDROOM 1", "A")])
        for i, o in enumerate(rear):
            self.assertTrue(s.PARK_X0+i*s.PARK_PITCH <= o[3] and o[4] <= s.PARK_X0+(i+1)*s.PARK_PITCH)

    def test_each_bedroom_has_a_side_wall_w_a_short_of_the_pad(self):
        from src import sitework as s
        side = {o[0]: o for o in s.b2_openings() if o[1] == "A" and o[2] in ("SAGE", "ADJACENT-PARCEL")}
        self.assertEqual(side["BEDROOM 1"][2], "ADJACENT-PARCEL")
        self.assertEqual(side["BEDROOM 2"][2], "SAGE")
        self.assertTrue(all(o[4] <= s.PARK_Y0 for o in side.values()))

    def test_check_wheel_stops_prints_each_stall(self):
        from src import sitework as s
        with contextlib.redirect_stdout(io.StringIO()) as out:
            s.check_wheel_stops()
        text = out.getvalue()
        self.assertIn('3 x 6\'-0" LONG, 5" HIGH MIN, 2\'-6" OFF BUILDING 2\'S REAR WALL', text)
        self.assertIn("REAR OPENING OVER IT: BATH W-B", text)
        self.assertIn("UNIT 4 BEDROOM 2 ESCAPE OPENING, RCO 310.1: W-A ON THE SAGE WALL", text)

    def test_a_stop_moved_onto_the_wall_stops_the_build(self):
        from src import sitework as s
        was = s.WHEEL_STOPS[0]
        s.WHEEL_STOPS[0] = (was[0], s.PARK_Y0+1.0, was[2], s.PARK_Y0+1.5)
        try:
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(AssertionError):
                s.check_wheel_stops()
        finally:
            s.WHEEL_STOPS[0] = was


if __name__ == '__main__':
    unittest.main()

"""src/exterior.py: the street-face trim, Unit 1's door surround and the screening shrubs."""
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


class TrimTests(unittest.TestCase):

    def test_sams_picks(self):
        """The designer, 2026-09-16: Craftsman flat trim on the street faces, shake in the S Elm
           gable, black frames with no grilles, a flat surround and no canopy at Unit 1."""
        from src import exterior as X
        self.assertEqual(set(X.STREET_FACES), {(1, 'S ELM WALL'), (1, 'SAGE WALL'), (2, 'SAGE WALL')})
        self.assertIn(('BUILDING 1', 'S ELM AVENUE'), X.GABLE_ACCENT)
        self.assertIn('BLACK', X.WINDOW_COLOUR)
        self.assertIsNone(X.WINDOW_GRILLES)

    def test_the_surround_leaves_siding_at_the_corner(self):
        from src import exterior as X
        from src.building1 import ENTRY_LEFT
        self.assertGreaterEqual(X.door_surround_fits(26.0-ENTRY_LEFT, 26.0), X.SIDING_MIN-1e-9)
        keep = X.SURROUND_PILASTER
        try:
            X.SURROUND_PILASTER = keep+3.0/12.0          # a pilaster 3" wider would not fit
            self.assertLess(X.door_surround_fits(26.0-ENTRY_LEFT, 26.0), X.SIDING_MIN)
        finally:
            X.SURROUND_PILASTER = keep


class ScreeningTests(unittest.TestCase):

    def test_every_placed_shrub_is_legal(self):
        from src import exterior as X
        for s in X.SHRUBS:
            self.assertEqual(X.violations(s.bldg, s.wall, s.along), [], s)

    def test_nothing_in_front_of_a_meter_or_an_outdoor_unit(self):
        from src import exterior as X
        for bldg, wall, run in X.groups():
            for b in run:
                self.assertTrue(X.violations(bldg, wall, (b.lo+b.hi)/2.0), b.mark)

    def test_a_shrub_under_an_egress_window_or_by_a_dryer_cap_fails(self):
        from src import exterior as X
        from src.mechanical import TERMS, WALLS
        wa = next(o for o in WALLS[1]['ADJACENT-PARCEL WALL'].openings if 'W-A' in o.name and o.zlo < 8)
        self.assertTrue(any('in front of' in v for v in X.violations(1, 'ADJACENT-PARCEL WALL', (wa.lo+wa.hi)/2.0)))
        dr = next(t for t in TERMS[1]['SAGE WALL'] if t.mark == 'DR-1')
        self.assertTrue(any('DR-1' in v for v in X.violations(1, 'SAGE WALL', dr.along)))

    def test_the_unscreened_ends_are_reported_not_forced(self):
        from src import exterior as X
        self.assertEqual(len(X.SHRUBS)+len(X.DROPPED), 2*len(X.groups()))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            X.check_exterior()
        self.assertEqual(out.getvalue().count('   --  '), len(X.DROPPED))


if __name__ == '__main__':
    unittest.main()

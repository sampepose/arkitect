"""The floor levels, the two floor build-ups, and the F1 listing they answer to.

src/levels.py had no dedicated test file. Every height in the set stands on it: the two
finished floors, both plate heights, the ceilings A-301 draws and the F1 assembly A-601
schedules. It carries a check() that check_model() runs, which pins the RELATIONSHIPS;
what had nothing was the listing -- the constants that say which assembly the set is
built to, and which the F1 checks then measure against.
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

from arkitect.lib.units import IN
from src import levels as L


class LevelTests(unittest.TestCase):

    def test_the_slab_sits_eight_inches_above_grade(self):
        """The designer, 2026-09-18: +5-3/4\" was under RCO 404.1.6's 6\"; the finished floor is +8-1/4\"."""
        self.assertEqual(L.GRADE, 0.0)
        self.assertEqual(L.FF1, IN(8.25))
        self.assertAlmostEqual(L.SLAB_TOP-L.GRADE, IN(8))
        self.assertGreaterEqual(L.SLAB_TOP-L.GRADE, L.REVEAL_MIN)

    def test_the_floors_are_ten_feet_apart(self):
        self.assertEqual(L.FLOOR_RISE, IN(120.0))
        self.assertAlmostEqual(L.FF2, L.FF1+L.FLOOR_RISE)

    def test_the_finished_floors_sit_above_their_structure(self):
        """A quarter inch of floor finish at both levels, allowed for in A-001 note 3b."""
        self.assertEqual(L.FLOOR_FINISH, IN(.25))
        self.assertAlmostEqual(L.SLAB_TOP, L.FF1-L.FLOOR_FINISH)
        self.assertAlmostEqual(L.SUBFLOOR_TOP, L.FF2-L.FLOOR_FINISH)

    def test_a_floor_depth_is_its_joist_plus_its_subfloor(self):
        """F1_DEPTH and F2_DEPTH are joist plus subfloor and NOT the floor finish --
           CLAUDE.md names F2_DEPTH as a constant to check before assuming."""
        self.assertAlmostEqual(L.F1_DEPTH, L.F1_JOIST+L.SUBFLOOR)
        self.assertAlmostEqual(L.F2_DEPTH, L.F2_JOIST+L.SUBFLOOR)
        self.assertLess(L.F1_DEPTH, L.F2_DEPTH, 'F1 is the shallower floor')

    def test_the_joists_are_the_depths_S102_schedules(self):
        self.assertEqual(L.F1_JOIST, IN(11.875))
        self.assertEqual(L.F2_JOIST, IN(14.0))


class F1ListingTests(unittest.TestCase):
    """The rated floor-ceiling between stacked units. Every one of these is a condition
       of the listing: change one and the assembly drawn is not the assembly tested."""

    def test_the_assembly_is_ESR_1153_assembly_F(self):
        self.assertEqual(L.F1_LISTING, 'ICC-ES ESR-1153 ASSEMBLY F')

    def test_assembly_F_is_a_single_layer_of_type_C(self):
        """It replaced a two-layer assembly. A-001 note 4a, A-601 and the F1 submittal
           list all read these."""
        self.assertEqual(L.F1_LAYERS, 1)
        self.assertEqual(L.F1_LAYER, IN(.625))
        self.assertEqual(L.F1_BOARD, 'TYPE C')
        self.assertNotIn('X', L.F1_BOARD, 'Type X is not what this listing tests')
        self.assertAlmostEqual(L.F1_GYPSUM, L.F1_LAYERS*L.F1_LAYER)

    def test_the_channels_are_at_the_spacing_the_listing_states(self):
        self.assertEqual(L.F1_CHANNEL_OC, IN(16))
        self.assertEqual(L.F1_CHANNEL, IN(.5))

    def test_the_mineral_wool_is_the_thickness_and_density_it_specifies(self):
        self.assertEqual(L.F1_INSUL_T, IN(1.5))
        self.assertEqual(L.F1_INSUL_PCF, 2.5)

    def test_the_joist_flange_is_a_nominal_2x4(self):
        """The listing is tested with nominal 2x4 flanges; src/framing.py checks every
           F1 joist against this and test_limits.py pins the check's own limit."""
        from src.framing import F1_MIN_FLANGE_W
        self.assertEqual(L.F1_FLANGE_W, IN(3.5))
        self.assertGreaterEqual(L.F1_FLANGE_W, F1_MIN_FLANGE_W)


class CheckTests(unittest.TestCase):

    def test_the_model_check_passes(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            L.check()


if __name__ == '__main__':
    unittest.main()

"""The checkers' own limits, pinned to the code sections they come from.

The suite constrained the model's VALUES against the checkers and the checkers' LIMITS
against nothing. So a checker could be told to permit what the code forbids and every
oracle stayed green: ESR-1153's flange minimum went from 3-1/2" to 2-1/2", RCO M1502.3's
dryer clearance from 3'-0" to 1'-0", R602.10.5's minimum braced panel from 48" to 24",
and each one passed the whole suite. The checks still ran, still measured, still
reported -- against a number that no longer meant anything.

A test that pins a limit is not testing arithmetic. It is testing that the number in the
code and the number in the code section are the same number, which is the one thing a
checker cannot check about itself.

Each pin names its source. If a limit here is wrong, the fix is to correct the citation
and the limit together, in one commit, having read the section.
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


class FramingLimits(unittest.TestCase):

    def test_the_F1_joist_flange_minimum_is_the_listing_s(self):
        """ESR-1153 Assembly F is tested with joists whose flanges are a nominal 2x4.
           CLAUDE.md records that as one of the F1 conditions; check_f1_listing()
           enforces it and nothing enforced the number it enforced."""
        from src.framing import F1_MIN_FLANGE_W
        self.assertEqual(F1_MIN_FLANGE_W, IN(3.5), 'nominal 2x4 is 3-1/2 inches')


class MechanicalLimits(unittest.TestCase):

    def test_the_dryer_termination_clearance_is_RCO_M1502_3(self):
        """3'-0" from a dryer termination to any opening into the building."""
        from src.building1 import DR_TERM_MIN
        self.assertEqual(DR_TERM_MIN, 3.0)


class BracingLimits(unittest.TestCase):

    def test_the_minimum_braced_panel_is_R602_10_5(self):
        """48 inches, for the method this project braces with."""
        from arkitect.codes.ohio.rco.bracing import ONE_PANEL_MIN
        self.assertEqual(ONE_PANEL_MIN, IN(48))

    def test_the_wind_speed_still_matches_the_transcribed_tables(self):
        """bracing.py's tables ARE the Vult <= 115 mph Exposure B columns. The module
           asserts this at import; this is the same claim held where a reader looks for
           it."""
        from src import bracing
        from arkitect.codes.ohio.columbus import criteria
        self.assertLessEqual(criteria.WIND_VULT, 115)
        self.assertEqual(criteria.WIND_EXPOSURE, 'B')
        self.assertIn(str(criteria.WIND_VULT), bracing.WIND)


class SiteLimits(unittest.TestCase):

    def test_a_landing_shares_a_full_door_width_with_its_walk(self):
        """ACCESS_MIN: the least edge a landing or stoop shares with the walk it steps
           onto, which is the door."""
        from src.grading import ACCESS_MIN
        self.assertEqual(ACCESS_MIN, 3.0)

    def test_a_shrub_keeps_clear_of_a_wall_cap(self):
        from src.exterior import CAP_CLR
        self.assertEqual(CAP_CLR, IN(36))

    def test_a_downspout_leader_keeps_clear_of_every_opening(self):
        from src.downspouts import LEADER_CLR
        self.assertEqual(LEADER_CLR, IN(6))


class ClearanceLimits(unittest.TestCase):

    def test_the_water_heater_working_space_is_RCO_M1305_1(self):
        from src.plumbing import WH_WORK
        self.assertEqual(WH_WORK, IN(30))

    def test_the_clearance_rules_agree_with_the_constants_that_check_them(self):
        """src/clearances.py is the index of every clearance rule in the project. Where
           a rule names a checker that owns its own constant, the two must be the same
           number -- otherwise the table documents one rule and the build enforces
           another."""
        from arkitect.codes import clearances as code_clearances
        from src.plumbing import WH_WORK
        wh = [r for r in code_clearances.RULES['wh'] if 'M1305.1' in r.citation]
        self.assertEqual(len(wh), 1)
        self.assertEqual(wh[0].minimum, WH_WORK)


class EgressLimits(unittest.TestCase):

    def test_the_emergency_escape_minimums_are_RCO_310_1(self):
        """5.7 SF net clear, 24 inches high, 20 inches wide. A-602 and G-001 both print
           these and every W-A product has to meet them."""
        from arkitect.codes.ohio.rco.egress import EGRESS_MIN_SF, EGRESS_MIN_H, EGRESS_MIN_W
        self.assertAlmostEqual(EGRESS_MIN_SF, 5.7)
        self.assertEqual(EGRESS_MIN_H, IN(24))
        self.assertEqual(EGRESS_MIN_W, IN(20))


class FoundationLimits(unittest.TestCase):

    def test_the_frost_depth_is_Columbus_s(self):
        """CIC-09 and RCO 403.1.4.1: the bottom of a footing 32 inches below grade."""
        from src.foundation import FROST_DEPTH
        self.assertEqual(FROST_DEPTH, IN(32))

    def test_the_presumed_soil_bearing_is_the_one_G001_prints(self):
        from arkitect.codes.ohio.columbus.criteria import SOIL_BEARING
        self.assertEqual(SOIL_BEARING, 1500)


if __name__ == '__main__':
    unittest.main()

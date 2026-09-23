"""The exterior stair spec, pinned to what the set says it is.

src/stairs.py was referenced by no test at all. Changing MATERIAL to 'GALVANIZED STEEL'
passed the whole suite, the build, pyflakes and the trace comparison, and printed on two
issued sheets -- G-001's scope of work and A-604 note 1. CLAUDE.md names that exact
change as one not to make without the designer's say-so, and nothing mechanical defended it.

These tests are value pins, deliberately. The words in that module ARE the deliverable:
three sheets describe one stair and read their wording from it, so a change there is a
change to the specification of a thing that gets built, not a refactor. Pinning them
means such a change has to be made on purpose, with this file edited in the same commit.
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

from src import stairs


class SpecTests(unittest.TestCase):

    def test_both_stairs_are_prescriptive_wood(self):
        """The 2026-09-15 decision. They were galvanized steel, drawn as a deferred
           fabricator's package, because Unit 5's underside had to be a listed 1-hour
           assembly. Moving the RCO 302.1 imaginary line removed the rating and with it
           the only reason either stair was steel."""
        self.assertEqual(stairs.MATERIAL, 'PRESSURE-TREATED WOOD')
        self.assertEqual(stairs.DESIGN, 'PRESCRIPTIVELY')
        self.assertIn('311.7', stairs.CODE)
        self.assertIn('507', stairs.CODE)

    def test_no_part_of_the_stair_is_steel_or_a_listed_assembly(self):
        """The retired vocabulary, swept. A wood prescriptive stair delegates nothing to
           a fabricator's engineer and is not a listed assembly."""
        words = ' '.join([stairs.MATERIAL, stairs.STRINGERS, stairs.LANDING,
                          stairs.TREADS, stairs.GUARDS, stairs.CODE, stairs.DESIGN,
                          stairs.SUBMITTAL, stairs.SPEC] + list(stairs.DETAILS)).upper()
        for banned in ('STEEL', 'GALVANIZED STEEL', 'UL ', 'LISTED', 'I504',
                       'FABRICATOR', 'DEFERRED', 'SEALED'):
            self.assertNotIn(banned, words, 'the stair spec says %r' % banned)

    def test_the_members_are_the_ones_A604_details(self):
        self.assertEqual(stairs.STRINGERS, 'PT 2x12 STRINGERS')
        self.assertIn('PT 2x8', stairs.LANDING)
        self.assertIn('LEDGER', stairs.LANDING)
        self.assertEqual(stairs.TREADS, 'COMPOSITE TREADS')
        self.assertIn('HANDRAILS', stairs.GUARDS)

    def test_SPEC_is_built_from_the_parts_and_not_typed(self):
        """One line for a note with room for one line. If it is ever typed out, a member
           can change above and the note keep the old word."""
        for part in (stairs.MATERIAL, stairs.STRINGERS, stairs.LANDING,
                     stairs.TREADS, stairs.GUARDS):
            self.assertIn(part, stairs.SPEC)

    def test_A604_details_four_things_in_the_order_it_draws_them(self):
        self.assertEqual(len(stairs.DETAILS), 4)
        self.assertIn('STRINGERS', stairs.DETAILS[0])
        self.assertIn('GUARD POST', stairs.DETAILS[1])
        self.assertIn('LEDGER', stairs.DETAILS[2])
        self.assertIn('PIER', stairs.DETAILS[3])


class GeometryTests(unittest.TestCase):

    def test_the_flight_is_the_one_every_sheet_prints(self):
        """15 risers and 14 treads at 9-1/4\". A-001 note 13a, A-604 and the plans all
           state this; the dead note block deleted from plans.py still said 14 risers at
           7-15/16\", which is what an unpinned spec drifting looks like."""
        s = stairs.EXT_STAIR
        self.assertEqual(s.risers, 15)
        self.assertEqual(s.treads, 14)
        self.assertAlmostEqual(s.tread, 9.25/12.0)
        self.assertEqual(s.risers, s.treads+1, 'a flight has one more riser than treads')

    def test_the_riser_height_is_inside_the_code_maximum(self):
        """RCO 311.7.5.1: 8-1/4\" maximum riser for this occupancy in Ohio."""
        s = stairs.EXT_STAIR
        rise = (s.deck-s.stoop_above_grade)/s.risers
        self.assertLessEqual(rise, 8.25/12.0+1e-9,
                             'riser %.4f ft is over the Ohio maximum' % rise)
        self.assertGreater(rise, 0)

    def test_the_flight_is_wide_enough(self):
        """RCO 311.7.1: 36\" minimum clear width."""
        self.assertGreaterEqual(stairs.EXT_STAIR.width, 3.0)

    def test_the_stair_pitches_away_from_the_wall(self):
        """A-001 note 13a, and grading.stair_violations() measures it."""
        self.assertGreater(stairs.EXT_STAIR.pitch, 0)
        self.assertLessEqual(stairs.EXT_STAIR.pitch, 0.02+1e-9)


if __name__ == '__main__':
    unittest.main()

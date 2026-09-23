"""Columbus City Code Title 33, as numbers with their sections attached.

These were inside one project's sitework module, among that lot's own figures. They are
true of every lot in the district, and a new project needs them before any geometry exists --
whether a program fits a lot has to be answerable before there is a drawing to check.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from codes.columbus import zoning as Z


class RuleTests(unittest.TestCase):

    def test_the_rules_are_the_ones_the_first_set_was_tabulated_against(self):
        self.assertEqual(Z.COVERAGE_MAX, 0.65)
        self.assertEqual(Z.REAR_YARD_MIN, 0.25)
        self.assertEqual(Z.ADU_PCT_MAX, 0.65)
        self.assertEqual(Z.VISION_TRIANGLE_ST, 30.0)
        self.assertEqual(Z.MANEUVER_MIN, 20.0)
        self.assertEqual(Z.STALL_D, 18.0)

    RULES = ('COVERAGE_MAX', 'REAR_YARD_MIN', 'ADU_PCT_MAX',
             'VISION_TRIANGLE_ST', 'MANEUVER_MIN', 'STALL_D')

    def test_every_rule_is_either_cited_or_declared_unverified(self):
        """A number without its section cannot be checked or corrected safely -- but a
           GUESSED section is worse than none, because a citation printed beside a
           number reads as verified. So a rule either carries a section a permit set
           actually uses, or it is listed in UNVERIFIED with the reason. Never both,
           never neither."""
        for name in self.RULES:
            with self.subTest(name):
                cited = name in Z.CITATIONS
                unverified = name in Z.UNVERIFIED
                self.assertTrue(cited != unverified,
                                '%s must be in exactly one of CITATIONS or UNVERIFIED' % name)

    def test_every_citation_is_a_city_code_section(self):
        for name, section in Z.CITATIONS.items():
            with self.subTest(name):
                self.assertTrue(section.startswith('C.C. '), section)

    def test_every_unverified_rule_says_why(self):
        """An unexplained gap gets filled with a guess by the next person in a hurry."""
        for name, reason in Z.UNVERIFIED.items():
            with self.subTest(name):
                self.assertGreater(len(reason.strip()), 20, reason)

    def test_citation_never_invents_a_section(self):
        """citation() is what a fit check prints. For an unverified rule it must say so in
           words, not produce something shaped like a section number."""
        for name in self.RULES:
            with self.subTest(name):
                c = Z.citation(name)
                if name in Z.UNVERIFIED:
                    self.assertEqual(c, Z.SECTION_UNVERIFIED)
                    self.assertNotIn('C.C.', c)
                else:
                    self.assertEqual(c, Z.CITATIONS[name])

    def test_the_fractions_are_fractions(self):
        for name in ('COVERAGE_MAX', 'REAR_YARD_MIN', 'ADU_PCT_MAX'):
            with self.subTest(name):
                self.assertGreater(getattr(Z, name), 0.0)
                self.assertLessEqual(getattr(Z, name), 1.0)


# That a project reads these constants rather than its own copies is that project's claim,
# held by its own test.

"""The clearance rules and the water-closet check, on rooms built for the test."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


from lib.units import IN
from codes import clearances as code_clearances
from lib.model.dimensions import wc_clearances


class ClearanceRuleTests(unittest.TestCase):

    def test_the_side_rule_is_the_code_minimum(self):
        self.assertEqual(code_clearances.WC_SIDE.minimum, IN(15))
        self.assertEqual(code_clearances.WC_SIDE.citation, 'RCO 307.1')

    def test_the_front_rule_is_recorded_even_though_it_is_not_checked(self):
        """The model carries no obstruction in front of a pan, so there is nothing to
           measure. The rule is in the table anyway, with a note saying so: an
           unchecked rule that is written down is a known gap, and one that is left out
           is an invisible one."""
        self.assertEqual(code_clearances.WC_FRONT.minimum, IN(21))
        self.assertIn('NOT CHECKED', code_clearances.WC_FRONT.note)

    def test_every_rule_names_who_checks_it_or_why_nobody_does(self):
        for kind, rules in code_clearances.RULES.items():
            for r in rules:
                with self.subTest('%s %s' % (kind, r.citation)):
                    self.assertTrue(r.checked_by or r.note,
                                    'rule states neither a checker nor a reason')
                    self.assertGreater(r.minimum, 0)
                    self.assertTrue(r.measured, 'rule does not say how it is measured')

    def test_a_pan_in_no_room_raises_rather_than_being_skipped(self):
        """It used to `continue`: a water closet the measurement could not place got no
           dimension on the sheet and no check, in silence."""
        pan = (1.0, 0.0, 1.5, 2.5, 'wc', 'n')
        with self.assertRaises(AssertionError):
            wc_clearances([], [], [pan])


if __name__ == '__main__':
    unittest.main()

"""inches32(): the print a divided rise needs when its sixteenth would not multiply back.

   Every helper here takes FEET, as the models do, and prints inches."""
import unittest

from arkitect.lib.units import IN, fmt, inches, inches16, inches32


class Inches32Tests(unittest.TestCase):

    def test_a_divided_rise_prints_to_the_thirty_second(self):
        riser = IN(120.5)/15                       # a real Unit 3 stair, A-603 note 2
        self.assertEqual(inches32(riser), '8-1/32"')
        self.assertEqual(inches16(riser), '8-1/16"')      # 15 of these are 120-15/16"
        self.assertEqual(inches(riser), '8"')             # and 15 of these are 120", 1/2" short
        self.assertEqual(inches32(IN(8.0)), '8"')                # no fraction, no "-0/32"
        self.assertEqual(inches32(IN(0.03125)), '1/32"')         # under an inch, no leading 0-
        self.assertEqual(inches32(IN(8.0625)), '8-1/16"')        # reduced, not 8-2/32"
        self.assertEqual(inches32(IN(8.5), sep=" "), '8 1/2"')



class NegativeTests(unittest.TestCase):

    def test_the_sign_stands_ahead_of_the_figure(self):
        # divmod floors a negative, so -1/2" used to print -1-1/2" and -16-3/4" -17-1/4"
        self.assertEqual(inches(-IN(0.5)), '-1/2"')
        self.assertEqual(inches(-IN(16.75)), '-16-3/4"')
        self.assertEqual(inches16(-IN(8.0625)), '-8-1/16"')
        self.assertEqual(inches32(-IN(0.03125)), '-1/32"')
        self.assertEqual(fmt(-1.5), '-1\'-6"')
        self.assertEqual(inches(-IN(0.01)), '0"')                 # under 1/16" rounds to nothing, unsigned

if __name__ == '__main__':
    unittest.main()

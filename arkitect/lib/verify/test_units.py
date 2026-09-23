"""inches32(): the print a divided rise needs when its sixteenth would not multiply back.

   Every helper here takes FEET, as the models do, and prints inches."""
import unittest

from arkitect.lib.units import IN, inches, inches16, inches32


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


if __name__ == '__main__':
    unittest.main()

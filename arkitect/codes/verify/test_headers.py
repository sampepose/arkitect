"""RCO Tables 602.7(1), 602.7(2) and 602.7.5, pinned cell by cell.

This pin lived in one project's tests while two projects carried the table. The table has
one home now, arkitect/codes/ohio/rco/headers.py, and so does its pin.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.codes.ohio.rco import headers as f


class HeaderTableTests(unittest.TestCase):

    def test_the_table_rows_as_printed(self):
        """Pins the transcription of Tables 602.7(1), (2) and 602.7.5, 30 psf / 36 ft columns."""
        # footnote f's 0.70 applies to 2x8 and up; 2x4 and 2x6 rows are not factored
        self.assertEqual(f.header_for('ROOF AND CEILING', 3.0)[:2], ('2-2x6', 1))
        self.assertEqual(f.header_for('ROOF AND CEILING', 5.0)[:2], ('3-2x10', 2))        # 2-2x12 6-10 x 0.70 = 4-9
        self.assertEqual(f.header_for('ROOF, CEILING AND ONE CENTER-BEARING FLOOR', 3.0)[:2], ('2-2x6', 2))
        self.assertEqual(f.header_for('ROOF, CEILING AND ONE CENTER-BEARING FLOOR', 4.0)[:2], ('3-2x10', 2))
        self.assertEqual(f.header_for('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 3.0)[:2], ('2-2x12', 3))   # 2-2x10 4-2 x 0.70 = 2-11
        self.assertEqual(f.header_for('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 4.0)[:2], ('3-2x12', 2))
        self.assertEqual(f.header_for('ONE FLOOR ONLY', 5.0)[:2], ('3-2x12', 2))
        self.assertEqual(f.header_for('ONE FLOOR ONLY', 2.67)[:2], ('2-2x6', 1))
        self.assertAlmostEqual(f.header_for('ONE FLOOR ONLY', 5.0)[3], (7+9/12.0)*0.70, places=6)   # the factored span
        with self.assertRaises(ValueError):
            f.header_for('ROOF, CEILING AND ONE CLEAR-SPAN FLOOR', 4.5)
        self.assertEqual(f.full_height_studs(3.0), 1); self.assertEqual(f.full_height_studs(9.0), 2)
        # the cells themselves, so a retyped table cannot drift
        self.assertEqual([(s, round(sp*12)) for s, sp, j in f.HEADER_TABLE['ROOF AND CEILING']],
                         [('2-2x4', 31), ('2-2x6', 46), ('2-2x8', 58), ('2-2x10', 69), ('2-2x12', 82), ('3-2x8', 73), ('3-2x10', 87), ('3-2x12', 102)])
        self.assertEqual([(s, round(sp*12)) for s, sp, j in f.HEADER_TABLE['ROOF, CEILING AND ONE CENTER-BEARING FLOOR']],
                         [('2-2x4', 26), ('2-2x6', 39), ('2-2x8', 49), ('2-2x10', 58), ('2-2x12', 68), ('3-2x8', 61), ('3-2x10', 73), ('3-2x12', 86)])
        self.assertEqual([(s, round(sp*12)) for s, sp, j in f.HEADER_TABLE['ROOF, CEILING AND ONE CLEAR-SPAN FLOOR']],
                         [('2-2x4', 22), ('2-2x6', 34), ('2-2x8', 43), ('2-2x10', 50), ('2-2x12', 59), ('3-2x8', 53), ('3-2x10', 63), ('3-2x12', 74)])
        self.assertEqual([(s, round(sp*12)) for s, sp, j in f.HEADER_TABLE['ONE FLOOR ONLY']],
                         [('2-2x4', 28), ('2-2x6', 42), ('2-2x8', 53), ('2-2x10', 63), ('2-2x12', 75), ('3-2x8', 67), ('3-2x10', 79), ('3-2x12', 93)])


if __name__ == '__main__':
    unittest.main()

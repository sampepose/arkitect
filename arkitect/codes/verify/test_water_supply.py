"""IPC Appendix E and OPC Table 604.5, pinned against the table text. One transcription, one pin."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.codes.ohio import water_supply


class WaterSupplyTableTests(unittest.TestCase):

    def test_e103_3_2_private_rows(self):
        """Table E103.3(2), private occupancy: (cold, hot, total) WSFU."""
        self.assertEqual(water_supply.WSFU['tub'], (1.0, 1.0, 1.4))
        self.assertEqual(water_supply.WSFU['lav'], (0.5, 0.5, 0.7))
        self.assertEqual(water_supply.WSFU['wc'], (2.2, 0.0, 2.2))
        self.assertEqual(water_supply.WSFU['sink'], (1.0, 1.0, 1.4))
        self.assertEqual(water_supply.WSFU['dw'], (0.0, 1.4, 1.4))
        self.assertEqual(water_supply.WSFU['wd'], (1.0, 1.0, 1.4))
        self.assertEqual(water_supply.BATH_GROUP, (2.7, 1.5, 3.6))

    def test_e201_1_rows(self):
        """Table E201.1, the rows the buildings can use, at every developed length."""
        self.assertEqual(water_supply.LENGTHS, (40, 60, 80, 100, 150, 200, 250, 300, 400, 500))
        rows = {(blk, m, d): v for blk, rs in water_supply.E201_1.items() for m, d, v in rs}
        self.assertEqual(rows[('50 TO 60', '3/4', '3/4')], (9.5, 9.5, 9.5, 8.5, 6.5, 5, 4.5, 4, 3, 2.5))
        self.assertEqual(rows[('50 TO 60', '3/4', '1')], (32, 32, 32, 32, 25, 18.5, 14.5, 12, 9.5, 8))
        self.assertEqual(rows[('50 TO 60', '1', '1')], (32, 32, 32, 32, 30, 22, 16.5, 13, 10, 8))
        self.assertEqual(rows[('50 TO 60', '1', '1-1/4')], (80, 80, 80, 80, 80, 68, 57, 48, 35, 28))
        self.assertEqual(rows[('40 TO 49', '3/4', '3/4')], (9.5, 9.5, 8.5, 7, 5.5, 4.5, 3.5, 3, 2.5, 2))
        self.assertEqual(rows[('40 TO 49', '1', '1')], (32, 32, 32, 32, 21, 15, 11.5, 9.5, 7.5, 6.5))
        self.assertEqual(rows[('OVER 60', '3/4', '1')], (32, 32, 32, 32, 32, 24, 19.5, 15.5, 11.5, 9.5))
        self.assertEqual(rows[('OVER 60', '1', '1-1/4')], (80, 80, 80, 80, 80, 80, 69, 60, 46, 36))
        for blk in water_supply.E201_1:
            self.assertEqual([(m, d) for m, d, _v in water_supply.E201_1[blk]],
                             [('3/4', '1/2'), ('3/4', '3/4'), ('3/4', '1'), ('1', '1'), ('3/4', '1-1/4'), ('1', '1-1/4')])
            for _m, _d, v in water_supply.E201_1[blk]:
                self.assertEqual(len(v), 10)
                self.assertEqual(list(v), sorted(v, reverse=True))   # a longer run never carries more

    def test_604_5_minimum_fixture_supplies(self):
        self.assertEqual(water_supply.MIN_SUPPLY, {'lav': '3/8', 'wc': '3/8', 'tub': '1/2', 'shower': '1/2',
                                                   'sink': '1/2', 'dw': '1/2', 'wd': '1/2'})

    def test_a_shower_is_a_row(self):
        self.assertEqual(water_supply.WSFU['wc'], (2.2, 0.0, 2.2))
        self.assertEqual(water_supply.WSFU['shower'], (1.0, 1.0, 1.4))
        self.assertEqual(water_supply.BATH_GROUP, (2.7, 1.5, 3.6))

    def test_row_for_reads_the_length_at_or_above_and_the_smallest_meter_first(self):
        W = water_supply
        self.assertEqual(W.row_for(24.9, 156, '50 TO 60'), ('3/4', '1-1/4'))        # the 200 ft column: 18.5, 22, then 32
        self.assertEqual(W.row_for(24.9, 100, '50 TO 60'), ('3/4', '1'))            # 32 at 100 ft
        self.assertEqual(W.row_for(9.0, 60, '50 TO 60', meter='3/4'), ('3/4', '3/4'))
        self.assertEqual(W.row_for(40.0, 40, '50 TO 60'), ('1', '1-1/4'))           # past 32: the 1" meter
        with self.assertRaises(ValueError): W.row_for(10.0, 501, '50 TO 60')       # off the table's lengths
        with self.assertRaises(ValueError): W.row_for(81.0, 40, '50 TO 60')        # past the transcribed rows
        self.assertLess(W.pipe_size('3/4'), W.pipe_size('1'))


if __name__ == '__main__':
    unittest.main()

"""OPC Tables 709.1, 710.1(1) and 710.1(2), pinned against the table text. One transcription, one pin."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class DrainageTableTests(unittest.TestCase):

    def test_709_1_rows(self):
        """Table 709.1: drainage fixture units and trap sizes for the fixtures this
           project has, water closets at 1.6 gpf."""
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.DFU, {'wc': 3, 'lav': 1, 'tub': 2, 'shower': 2, 'sink': 2, 'wd': 2})
        self.assertEqual(opc_drainage.BATH_GROUP, 5)
        self.assertEqual(opc_drainage.TRAP, {'wc': '3', 'lav': '1-1/4', 'tub': '1-1/2', 'shower': '2', 'sink': '1-1/2', 'wd': '2'})
        self.assertEqual(opc_drainage.GROUP, ('wc', 'lav', 'tub'))

    def test_406_2_washer(self):
        """406.2, IPC 2021 as OAC 4101:3-4-01 eff. 10-15-2025 adopts it unmodified: the washer's
           trap and fixture drain 2\" at least, into a 3\" or larger fixture branch or stack."""
        from collections import namedtuple
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual((opc_drainage.WASHER_DRAIN_MIN, opc_drainage.WASHER_RECEIVER_MIN), ('2', '3'))
        St = namedtuple('St', 'name size serves')
        B = namedtuple('B', 'name stacks pens runs')
        on = lambda size: [B('B', [St('F', size, (('U', 1, ('wd',)),))], [], [])]
        self.assertEqual(opc_drainage.washer_violations(on('3')), [])
        self.assertEqual(len(opc_drainage.washer_violations(on('2'))), 1)

    def test_704_1_slopes(self):
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.SLOPE, {'1-1/2': 0.25, '2': 0.25, '3': 0.125, '4': 0.125})
        self.assertEqual(opc_drainage.SLOPES, (1/16.0, 1/8.0, 1/4.0, 1/2.0))

    def test_710_1_1_rows(self):
        """Table 710.1(1), building drains and sewers, at 1/16, 1/8, 1/4 and 1/2."""
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.T710_1_1['1-1/2'], (None, None, 3, 3))
        self.assertEqual(opc_drainage.T710_1_1['2'], (None, None, 21, 26))
        self.assertEqual(opc_drainage.T710_1_1['3'], (None, 36, 42, 50))
        self.assertEqual(opc_drainage.T710_1_1['4'], (None, 180, 216, 250))
        for row in opc_drainage.T710_1_1.values():
            vals = [v for v in row if v is not None]
            self.assertEqual(vals, sorted(vals))            # a steeper drain never carries less

    def test_710_1_2_rows(self):
        """Table 710.1(2), horizontal fixture branches and stacks, and the 3" footnote."""
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.T710_1_2['1-1/2'], (3, 2, 4, 8))
        self.assertEqual(opc_drainage.T710_1_2['2'], (6, 6, 10, 24))
        self.assertEqual(opc_drainage.T710_1_2['3'], (20, 20, 48, 72))
        self.assertEqual(opc_drainage.T710_1_2['4'], (160, 90, 240, 500))
        self.assertEqual((opc_drainage.WC_PER_INTERVAL_3, opc_drainage.WC_PER_STACK_3), (2, 6))
        self.assertEqual(opc_drainage.WC_MIN, '3')
        self.assertEqual(opc_drainage.SIZES, ('1-1/2', '2', '3', '4'))

    def test_table_709_1_and_710_1(self):
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.DFU, {'wc': 3, 'lav': 1, 'tub': 2, 'shower': 2, 'sink': 2, 'wd': 2})
        self.assertEqual(opc_drainage.BATH_GROUP, 5)
        self.assertEqual(opc_drainage.T710_1_1['3'], (None, 36, 42, 50))
        self.assertEqual(opc_drainage.T710_1_2['2'], (3+3, 6, 10, 24))

    def test_an_interval_is_a_group_when_it_has_all_three(self):
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.interval_dfu(('lav', 'wc', 'tub')), 5)
        self.assertEqual(opc_drainage.interval_dfu(('lav', 'wc', 'tub', 'sink')), 7)
        self.assertEqual(opc_drainage.interval_dfu(('lav', 'tub')), 3)
        self.assertEqual(opc_drainage.interval_dfu(('wc',)), 3)
        self.assertEqual(opc_drainage.interval_dfu(('sink', 'wd')), 4)
        self.assertEqual(opc_drainage.interval_dfu(()), 0)

    def test_a_shower_makes_a_group(self):
        from arkitect.codes.ohio import opc_drainage as opc_drainage
        self.assertEqual(opc_drainage.interval_dfu(('wc', 'lav', 'shower')), 5)
        self.assertEqual(opc_drainage.interval_dfu(('lav', 'lav', 'wc', 'tub')), 6)


if __name__ == '__main__':
    unittest.main()

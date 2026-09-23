"""NEC 220: the dwelling and service load methods, on figures worked by hand.

The two projects' copies of these had drifted apart — one had no single-dwelling service,
the other no house feeder. arkitect/codes/nec/load.py is their union, and each branch is held here.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.codes.nec import load as L

# name, SF, range, dryer, dishwasher, water heater, heat pump at MCA, panel A
UNIT = ('U', 1000, 12000, 5000, 1200, 4500, 4800, 125)


def _service(n, house_va=0, positions=(('U1', 125, 'UNIT 1'),)):
    return dict(units=[UNIT]*n, house_va=house_va, positions=list(positions), mark='EM-1')


class LoadTests(unittest.TestCase):

    def test_220_82_one_dwelling(self):
        r = L.nec220_82(*UNIT[1:7])
        self.assertEqual(r['sub'], 3000+3000+1500+12000+5000+1200+4500)      # 30,200 VA
        self.assertEqual(r['rem'], 0.4*20200)                                # over 10 kVA at 40 %
        self.assertEqual(r['tot'], 10000+8080+4800)                          # the heat pump at 100 %
        self.assertAlmostEqual(r['amps'], 22880/240.0)

    def test_part_iii_standard_method(self):
        d = L.service_load_standard([UNIT], 0)
        self.assertEqual(d['lighting'], 3000+0.35*4500)                      # Table 220.45 on 7,500 VA
        self.assertEqual(d['ranges'], 8000)                                  # Table 220.55 column C, one range
        self.assertEqual(d['appliances'], 5700)                              # two appliances: 100 %
        self.assertEqual(d['motor'], 1200)                                   # 220.50, a quarter of the largest
        self.assertEqual(d['va'], 29275)
        four = L.service_load_standard([UNIT, UNIT], 0)
        self.assertEqual(four['appliances'], 0.75*11400)                     # four appliances: 220.53's 75 %

    def test_a_one_dwelling_service_takes_220_82_and_is_never_under_its_panel(self):
        std, opt, gov, size = L.service_loads(_service(1))
        self.assertEqual(opt['method'], 'NEC 220.82'); self.assertIs(gov, opt)
        self.assertEqual(L.service_size(gov['amps']), 100)                   # 95 A would take a 100 A service
        self.assertEqual(size, 125)                                          # but the panel it feeds is 125 A
        small = _service(1, positions=(('U1', 60, 'UNIT 1'),))
        self.assertEqual(L.service_loads(small)[3], 100)                     # 230.79(C): never under 100 A

    def test_two_dwellings_take_220_85(self):
        std, opt, gov, size = L.service_loads(_service(2))
        self.assertEqual(opt['va'], 0.45*3*35000)                            # three units each equal to the larger
        self.assertIn('220.85', opt['method']); self.assertIs(gov, opt)
        self.assertEqual((std['va'], size), (47550, 200))

    def test_three_to_five_dwellings_take_220_84(self):
        std, opt, gov, size = L.service_loads(_service(3, house_va=1500))
        self.assertEqual(opt['va'], 0.45*105000+1500)
        self.assertEqual(opt['method'], 'NEC 220.84, 3 UNITS AT 45 %')
        self.assertEqual((std['va'], size), (68750, 225))
        with self.assertRaises(AssertionError):
            L.service_load_220_84([UNIT]*6, 0)

    def test_the_governing_load_is_the_lesser(self):
        for n in (1, 2, 3):
            std, opt, gov, _size = L.service_loads(_service(n))
            self.assertEqual(gov['va'], min(std['va'], opt['va']))

    def test_feeders_a_unit_takes_310_12_and_a_house_feeder_310_16(self):
        s = _service(1, positions=(('U1', 125, 'UNIT 1'), ('H', 60, 'HOUSE')))
        unit, house, service = L.feeders(s)
        self.assertEqual(unit[:4], ('U1', 'UNIT 1', 125, '#2'))              # Table 310.12(A) at 83 %
        self.assertEqual(house[:4], ('H', 'HOUSE', 60, '#6'))                # Table 310.16 at 100 %
        self.assertEqual((unit[6], house[6]), ('#6', '#10'))                 # 250.122 equipment grounds
        self.assertEqual(service[:4], ('SERVICE', 'EM-1', 125, '#1'))
        self.assertEqual((unit[4], service[4]), (4, 3))                      # a feeder's neutral is isolated

    def test_no_standard_rating_is_an_error(self):
        with self.assertRaises(ValueError):
            L.service_size(10000)


if __name__ == '__main__':
    unittest.main()

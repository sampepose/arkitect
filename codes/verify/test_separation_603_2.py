"""OPC 603.2 on a building drawn for the test: one 3" drain up the middle of a 20 x 30 slab,
one water service across it, one strip, one sewer outside. Each answer worked by hand."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from lib.units import IN
from lib.model.drains import Building, Run
from codes.ohio import opc_separation as S

RUN = Run('3', [(10.0, 5.0), (10.0, 25.0)])
B = Building('B', 1, 20.0, 30.0, [], [], [RUN], (0.0, 0.0))
SERVICE = [(-40.0, 15.0), (15.0, 15.0)]


def ground(cover=IN(20), service=SERVICE, sewer_invert=-4.0):
    return S.Ground(cover=cover, wall_t=IN(8), water_bed=IN(8), frost_depth=IN(32),
                    water_below=lambda b: [((0.0, 15.0), (15.0, 15.0))],
                    water_lines=lambda b: [('SERVICE', service)],
                    strips=lambda b: [((0.0, 14.0, 20.0, IN(16)), 'STRIP')],
                    sewers=lambda: [('SEWER', [(-10.0, 0.0), (-10.0, 40.0)], lambda t: sewer_invert, '4')],
                    service_size=lambda b: '1-1/4',
                    ftg_t=IN(8), bar_dia=IN(0.5), bar_cover=IN(3), slab_top=IN(8),
                    bury=IN(38), service_series='CTS')


class SeparationTests(unittest.TestCase):

    def test_where_the_drain_meets_the_water_and_the_strip(self):
        self.assertEqual(S.crossings(B, ground()), [(RUN, (10.0, 15.0))])
        [(r, nm, pt)] = S.strip_crossings(B, ground())
        self.assertEqual((nm, pt), ('STRIP', (10.0, 14.0+IN(16)/2.0)))

    def test_a_deep_drain_lets_the_water_lie_above_it(self):
        # 20" of cover: the 3" drain's top within 5 ft of the crossing is 1.72 ft down, and the
        # water needs 8" of bed plus 12" clear = 1.67 ft
        [(r, nm, x, kind)] = S.water_crossings(B, ground())
        self.assertEqual((nm, x, kind), ('SERVICE', (10.0, 15.0), 'above'))
        self.assertAlmostEqual(-S.highest_top_near(B, RUN, x, ground()), IN(20)+0.125/12.0*5.0, places=6)
        self.assertEqual(S.sleeves(B, ground(sewer_invert=-5.0)), [])

    def test_a_shallow_drain_sleeves_the_water_five_feet_either_side(self):
        g = ground(cover=IN(12))
        self.assertEqual(S.water_crossings(B, g)[0][3], 'sleeved')
        self.assertEqual(S.sleeves(B, ground(cover=IN(12), sewer_invert=-5.0)), [('SERVICE', 45.0, 55.0)])   # it stops at the riser

    def test_water_that_leaves_the_wall_within_five_feet_is_sleeved_however_deep_the_drain(self):
        near_wall = Building('B', 1, 20.0, 30.0, [], [], [Run('3', [(2.0, 5.0), (2.0, 25.0)])], (0.0, 0.0))
        self.assertEqual(S.water_crossings(near_wall, ground(cover=IN(40)))[0][3], 'sleeved')

    def test_the_service_over_the_sewer_outside_the_wall(self):
        # the service's bottom is 32" + 1-1/4" down; a 4" sewer with its invert 4 ft down tops out
        # at 3.67 ft, under 12" below it: sleeved. At 5 ft down it clears.
        [(nm, x, top, kind)] = S.site_crossings(B, ground())
        self.assertEqual((nm, x, kind), ('SEWER', (-10.0, 15.0), 'sleeved'))
        self.assertAlmostEqual(top, -4.0+IN(4))
        self.assertEqual(S.site_crossings(B, ground(sewer_invert=-5.0))[0][3], 'above')
        self.assertEqual(S.sleeves(B, ground()), [('SERVICE', 25.0, 35.0)])


if __name__ == '__main__':
    unittest.main()

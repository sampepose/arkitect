"""OPC 305.2 / 305.3 / 305.4 and RCO 403.1.5 on a foundation drawn for the test: Columbus's
32" frost depth, a 16" x 8" footing with 2-#4 at 3" clear, a 4" slab 8" out of grade on
4" of aggregate, and a 1" service. Every answer worked by hand.

Two faults are pinned here, both carried by both sets and both found by review. A service
buried below the frost line cannot be sleeved "through the foundation wall", because on a
slab the wall starts at the footing's TOP, a footing thickness above the pipe. And the
burial is OPC 305.4's -- 6 inches UNDER the frost line, and never less than 12 inches down
-- not the frost line itself, and not the deleted 305.4.1, which was sewer depth.

Sizes are names: the cover under the sleeve is taken off its 1.900 in OUTSIDE diameter,
not off the 1.5 it is called."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from arkitect.lib.units import IN
from arkitect.codes.ohio import opc_service_entry as E

FROST = IN(32)
BURY = IN(38)                       # 32 + 6, OPC 305.4
ARGS = dict(service='1', bury=BURY, frost_depth=FROST, ftg_t=IN(8), bar_dia=IN(0.5),
            bar_cover=IN(3), cover=IN(3), slab_top=IN(8), water_bed=IN(8))


class BurialTests(unittest.TestCase):

    def test_six_inches_under_the_frost_line(self):
        # OPC 305.4, Freezing. NOT 305.4.1, which Ohio deletes and which was sewer depth.
        self.assertAlmostEqual(E.bury_depth(FROST), IN(38), places=9)
        self.assertAlmostEqual(E.BELOW_FROST, IN(6), places=9)

    def test_never_less_than_twelve_inches_down(self):
        # a shallow frost line does not let the service come up to meet it
        self.assertAlmostEqual(E.bury_depth(IN(4)), IN(12), places=9)
        self.assertAlmostEqual(E.MIN_COVER, IN(12), places=9)


class SleeveSizeTests(unittest.TestCase):

    def test_two_sizes_larger(self):
        # OPC 305.3, along the nominal ladder: 1 -> 1-1/4 -> 1-1/2
        self.assertEqual(E.sleeve_size('1'), '1-1/2')
        self.assertEqual(E.sleeve_size('3/4'), '1-1/4')
        self.assertEqual(E.sleeve_size('1-1/4'), '2')

    def test_a_size_nobody_makes_is_refused(self):
        self.assertRaises(AssertionError, E.sleeve_size, '1-1/8')
        self.assertRaises(AssertionError, E.sleeve_size, '4')


class EntryTests(unittest.TestCase):

    def test_the_wall_starts_a_footing_thickness_above_the_service(self):
        e = E.entry(**ARGS)
        # the footing's bottom is the frost depth, so its top -- where the wall starts --
        # is 24" down; the service's top is 38", so 14" of ground lies between them
        self.assertAlmostEqual(e.ftg_top, -IN(24), places=9)
        self.assertAlmostEqual(e.pipe_top, -IN(38), places=9)
        self.assertTrue(e.sleeve_top < e.ftg_top)

    def test_the_sizes_are_outside_diameters_not_names(self):
        e = E.entry(**ARGS)
        self.assertAlmostEqual(e.pipe_od, IN(1.125), places=9)       # 1" CTS: the name plus 1/8
        self.assertAlmostEqual(e.sleeve_od, IN(1.900), places=9)     # 1-1/2" Sch 40, ASTM D1785
        self.assertAlmostEqual(e.pipe_bot, -IN(39.125), places=9)
        # concentric about the pipe, whose centre is 38 + 1.125/2 down
        self.assertAlmostEqual(e.sleeve_top, -IN(37.6125), places=9)
        self.assertAlmostEqual(e.sleeve_bot, -IN(39.5125), places=9)
        self.assertAlmostEqual(e.sleeve_top-e.sleeve_bot, IN(1.900), places=9)

    def test_the_footing_is_thickened_to_carry_the_sleeve(self):
        e = E.entry(**ARGS)
        self.assertAlmostEqual(e.deep_bot, -IN(42.5125), places=9)   # 39.5125 + 3" of cover
        self.assertAlmostEqual(e.drop, IN(10.5125), places=9)
        self.assertAlmostEqual(e.thick, IN(18.5125), places=9)       # 42.5125 - 24
        self.assertAlmostEqual(e.run, IN(105.125), places=9)         # the drop at one in ten
        self.assertAlmostEqual(e.run/e.drop, 10.0, places=9)

    def test_the_sleeve_is_inside_the_concrete_not_under_it(self):
        # the detail is titled "through the thickened footing" and this is why
        e = E.entry(**ARGS)
        self.assertTrue(e.deep_bot < e.sleeve_bot < e.sleeve_top < e.ftg_top,
                        'the sleeve no longer lies within the footing')

    def test_the_bottom_bars_run_straight_through_above_the_sleeve(self):
        e = E.entry(**ARGS)
        self.assertAlmostEqual(e.bar_bot, -IN(29), places=9)         # 3" clear of the TYPICAL bottom
        self.assertAlmostEqual(e.bar_clear, IN(8.6125), places=9)
        self.assertTrue(e.bar_clear >= E.BAR_CLEAR)

    def test_the_service_rises_into_the_aggregate_under_the_slab(self):
        e = E.entry(**ARGS)
        self.assertAlmostEqual(e.bed, 0.0, places=9)                 # 8" of slab-and-gravel under a +8" top
        self.assertTrue(e.bed > e.pipe_top)

    def test_a_good_entry_has_nothing_to_say(self):
        self.assertEqual(E.entry_violations(E.entry(**ARGS), frost_depth=FROST, cover=IN(3)), [])


class ViolationTests(unittest.TestCase):

    def _bad(self, **kw):
        a = dict(ARGS); a.update(kw)
        return E.entry_violations(E.entry(**a), frost_depth=FROST, cover=IN(3))

    def test_burying_the_service_at_the_frost_line_is_refused(self):
        # what both sets did before review: the frost line itself, 6" short of OPC 305.4
        v = self._bad(bury=FROST)
        self.assertTrue(any('OPC 305.4' in t and '38"' in t for t in v), v)

    def test_a_service_under_twelve_inches_is_refused(self):
        v = E.entry_violations(E.entry(**dict(ARGS, bury=IN(9), frost_depth=IN(2))),
                               frost_depth=IN(2), cover=IN(3))
        self.assertTrue(any('12"' in t for t in v), v)

    def test_a_footing_founded_below_the_service_is_a_different_detail(self):
        # founded 4'-0" down on a deeper bearing stratum: the wall itself reaches past the
        # sleeve, so the service comes THROUGH the wall and nothing is deepened
        v = self._bad(ftg_bot=-IN(48))
        self.assertTrue(any('THROUGH the wall' in t for t in v), v)

    def test_no_cover_under_the_sleeve(self):
        v = self._bad(cover=0.0)
        self.assertTrue(any('not deepened' in t or 'not below the sleeve' in t for t in v), v)

    def test_a_shallow_service_crowds_the_bottom_bars(self):
        # the guard only bites where the sleeve rises near the bars, which a burial at
        # OPC 305.4's depth never does -- it is here for a footing founded deeper, or a
        # frost line shallower, than this project's
        v = self._bad(bury=IN(30))
        self.assertTrue(any('bottom bars' in t for t in v), v)

    def test_the_sleeve_must_be_two_sizes_larger(self):
        e = E.entry(**ARGS)._replace(sleeve='1-1/4')
        v = E.entry_violations(e, frost_depth=FROST, cover=IN(3))
        self.assertTrue(any('OPC 305.3' in t for t in v), v)



class ZoneTests(unittest.TestCase):
    """thickened_zone(): the return measured along the footing's centreline, turning a corner."""
    LOOP = [(0.0, 0.0), (20.0, 0.0), (20.0, 33.0), (0.0, 33.0)]

    def test_a_crossing_mid_wall_is_straight(self):
        e = E.entry(**ARGS)
        z = E.thickened_zone(e, self.LOOP, (0.0, 16.5))
        self.assertEqual(z.corners, [])
        self.assertAlmostEqual(sum(z.legs), 2*e.run, places=9)
        self.assertEqual(E.zone_violations(e, self.LOOP, z), [])

    def test_a_crossing_near_a_corner_turns_it(self):
        e = E.entry(**ARGS)
        z = E.thickened_zone(e, self.LOOP, (0.0, 28.0))
        self.assertEqual(z.corners, [(0.0, 33.0)])
        short, long_ = sorted(z.legs)                                  # in the loop's own direction
        self.assertAlmostEqual(short, e.run-5.0, places=9)            # around the corner
        self.assertAlmostEqual(long_, e.run+5.0, places=9)            # along the wall, both sides of the crossing
        self.assertEqual(E.zone_violations(e, self.LOOP, z), [])

    def test_a_return_that_meets_itself_fails(self):
        e = E.entry(**ARGS)
        tiny = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
        z = E.thickened_zone(e, tiny, (0.0, 2.0))
        self.assertTrue(E.zone_violations(e, tiny, z))

    def test_a_crossing_off_the_centreline_is_refused(self):
        with self.assertRaises(ValueError):
            E.thickened_zone(E.entry(**ARGS), self.LOOP, (1.0, 16.5))


if __name__ == '__main__':
    unittest.main()

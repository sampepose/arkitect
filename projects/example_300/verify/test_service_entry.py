"""The water service gets into each building UNDER its footing, not through its wall.

The set buries the service below Columbus's 32" frost line and founds the footing's
bottom at that same 32", so the foundation wall standing on it begins a footing thickness
higher than the pipe. P-102 / P-103 note 2 used to say "sleeve through the foundation
wall" and no sheet drew the entry; these hold the resolved geometry, the check that stops
the build, and the sheets that now print it."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class ServiceEntryTests(unittest.TestCase):

    def setUp(self):
        from arkitect.codes.ohio.opc_service_entry import entry_for
        from src import drainage as dr
        self.dr = dr
        self.e = entry_for(dr.BUILDING_1, dr.GROUND)

    def test_both_buildings_take_the_same_entry(self):
        # P-601 draws one detail and asserts this; if the services ever differ in size the
        # sheet has to draw two
        from arkitect.codes.ohio.opc_service_entry import entry_for
        self.assertEqual(entry_for(self.dr.BUILDING_2, self.dr.GROUND), self.e)

    def test_the_wall_begins_above_the_service(self):
        from arkitect.lib.units import IN
        self.assertAlmostEqual(self.e.pipe_top, -IN(38), places=9)   # OPC 305.4: 32 + 6
        self.assertAlmostEqual(self.e.ftg_top, -IN(24), places=9)
        self.assertTrue(self.e.sleeve_top < self.e.ftg_top,
                        'the service would pass through the wall, which this set cannot draw')

    def test_the_figures_the_sheets_print(self):
        from arkitect.lib.units import IN
        self.assertEqual((self.e.service, self.e.sleeve), ('1', '1-1/2'))
        self.assertAlmostEqual(self.e.bury, IN(38), places=9)
        self.assertAlmostEqual(self.e.sleeve_od, IN(1.900), places=9)
        self.assertAlmostEqual(self.e.drop, IN(10.5125), places=9)
        self.assertAlmostEqual(self.e.run, IN(105.125), places=9)
        self.assertAlmostEqual(self.e.thick, IN(18.5125), places=9)
        self.assertAlmostEqual(self.e.deep_bot, -IN(42.5125), places=9)
        self.assertAlmostEqual(self.e.bar_clear, IN(8.6125), places=9)

    def test_the_model_is_clean(self):
        from arkitect.codes.ohio.opc_service_entry import entries_violations
        self.assertEqual(entries_violations(self.dr.BUILDINGS, self.dr.GROUND), [])

    def test_a_bigger_service_moves_the_footing_and_the_build_says_so(self):
        # the sleeve grows with the service, so the deepening and its 1-in-10 run grow too
        from arkitect.codes.ohio import opc_service_entry as E
        from arkitect.lib.units import IN
        big = E.entry(service='2', bury=E.bury_depth(IN(32)), frost_depth=IN(32), ftg_t=IN(8),
                      bar_dia=IN(0.5), bar_cover=IN(3), cover=IN(3), slab_top=IN(8), water_bed=IN(8))
        self.assertEqual(big.sleeve, '3')
        self.assertTrue(big.drop > self.e.drop and big.run > self.e.run)
        self.assertEqual(E.entry_violations(big, frost_depth=IN(32), cover=IN(3)), [])


BUILD = os.path.join(PROJ, 'build.py')
STRINGS = {}


def setUpModule():
    from arkitect.lib.verify import sheet_text as st
    for no, items in st.recorded(BUILD).items():
        STRINGS[no] = [t.text for t in items]


class SheetTextTests(unittest.TestCase):
    """No sheet may send the water service through the foundation wall again."""

    def _strings(self):
        return STRINGS

    def test_no_sheet_sleeves_the_service_through_the_wall(self):
        for no, texts in self._strings().items():
            for t in texts:
                up = t.upper()
                if 'SERVICE' in up and 'THROUGH THE FOUNDATION WALL' in up:
                    self.fail('%s still sends the service through the wall: %r' % (no, t))
                if 'SLEEVED THROUGH THE WALL' in up:
                    self.fail('%s still says the service is sleeved through the wall: %r' % (no, t))

    def test_p601_draws_the_entry_and_the_others_cite_it(self):
        pages = self._strings()
        self.assertTrue(any('WATER SERVICE ENTRY' in t for t in pages['P-601']),
                        'P-601 no longer draws the service entry')
        for no in ('P-102', 'P-103', 'P-101', 'S-101'):
            self.assertTrue(any('P-601' in t for t in pages[no]), '%s no longer cites P-601' % no)

    def test_p601_prints_the_derived_figures(self):
        from arkitect.codes.ohio.opc_service_entry import entry_for
        from src import drainage as dr
        from arkitect.lib.units import fmt, inches
        e = entry_for(dr.BUILDING_1, dr.GROUND)
        joined = ' | '.join(self._strings()['P-601'])
        for figure in (inches(e.drop), fmt(e.run), inches(-e.deep_bot), inches(-e.pipe_top)):
            self.assertIn(figure, joined, 'P-601 no longer prints %s' % figure)


if __name__ == '__main__':
    unittest.main()

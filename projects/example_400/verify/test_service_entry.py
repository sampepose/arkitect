"""The water supply gets into each building UNDER its footing, not through its wall.

Same fault, same figures as 300 S Elm: the supply is buried below Columbus's 32" frost
line and the footing's bottom is founded at that same 32", so the foundation wall on it
begins a footing thickness higher than the pipe. P-102 / P-103 note 2 used to say "sleeve
through the foundation wall" and no sheet drew the entry. The rule is
arkitect/codes/ohio/opc_service_entry.py and the section is arkitect/lib/draw/plumbing_kit.py's; these hold
what THIS set does with them."""
import os
import unittest

from projects.example_400.verify import enter, leave

BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build.py')
STRINGS = {}


def setUpModule():
    enter()
    from arkitect.lib.verify import sheet_text as st
    for no, items in st.read(BUILD).items():
        STRINGS[no] = [t.text for t in items]


def tearDownModule():
    leave()


class ServiceEntryTests(unittest.TestCase):

    def setUp(self):
        from arkitect.codes.ohio.opc_service_entry import entry_for
        from src import drainage as dr
        self.dr = dr
        self.e = entry_for(dr.BUILDING_1, dr.GROUND)

    def test_both_buildings_take_the_same_entry(self):
        # P-601 draws one detail and asserts this
        from arkitect.codes.ohio.opc_service_entry import entry_for
        self.assertEqual(entry_for(self.dr.BUILDING_2, self.dr.GROUND), self.e)

    def test_the_wall_begins_above_the_supply(self):
        from arkitect.lib.units import IN
        self.assertAlmostEqual(self.e.pipe_top, -IN(38), places=9)   # OPC 305.4: 32 + 6
        self.assertAlmostEqual(self.e.ftg_top, -IN(24), places=9)
        self.assertTrue(self.e.sleeve_top < self.e.ftg_top,
                        'the supply would pass through the wall, which this set cannot draw')

    def test_the_figures_the_sheets_print(self):
        from arkitect.lib.units import IN
        self.assertEqual((self.e.service, self.e.sleeve), ('1', '1-1/2'))
        self.assertAlmostEqual(self.e.bury, IN(38), places=9)
        self.assertAlmostEqual(self.e.sleeve_od, IN(1.900), places=9)
        self.assertAlmostEqual(self.e.drop, IN(10.5125), places=9)
        self.assertAlmostEqual(self.e.run, IN(105.125), places=9)
        self.assertAlmostEqual(self.e.deep_bot, -IN(42.5125), places=9)

    def test_the_thickened_footing_is_located_and_turns_building_1s_corner(self):
        """A reviewer found Building 1's 8'-9-1/8" return running into the rear corner 7'-3" away.
           It is measured on the footing's centreline and carries on around the corner; S-101
           hatches it."""
        z1 = self.dr.thickened_footing(self.dr.BUILDING_1)
        z2 = self.dr.thickened_footing(self.dr.BUILDING_2)
        self.assertEqual(len(z1.corners), 1)
        self.assertEqual(z2.corners, [])
        for z in (z1, z2):
            self.assertAlmostEqual(sum(z.legs), 2*self.e.run, places=9)
        self.assertLess(z1.legs[0], self.e.run)          # the leg around the corner is the short one

    def test_the_model_is_clean(self):
        from arkitect.codes.ohio.opc_service_entry import entries_violations
        self.assertEqual(entries_violations(self.dr.BUILDINGS, self.dr.GROUND), [])


class SheetTextTests(unittest.TestCase):
    """No sheet may send the supply through the foundation wall again."""

    def test_no_sheet_sleeves_the_supply_through_the_wall(self):
        for no, texts in STRINGS.items():
            for t in texts:
                up = t.upper()
                if ('SUPPLY' in up or 'SERVICE' in up) and 'THROUGH THE FOUNDATION WALL' in up:
                    self.fail('%s still sends the water through the wall: %r' % (no, t))

    def test_p601_draws_the_entry_and_the_others_cite_it(self):
        self.assertTrue(any('WATER SERVICE ENTRY' in t for t in STRINGS['P-601']),
                        'P-601 no longer draws the service entry')
        for no in ('P-102', 'P-103', 'P-101', 'S-101'):
            self.assertTrue(any('P-601' in t for t in STRINGS[no]), '%s no longer cites P-601' % no)

    def test_p601_prints_the_derived_figures(self):
        from arkitect.codes.ohio.opc_service_entry import entry_for
        from arkitect.lib.units import fmt, inches
        from src import drainage as dr
        e = entry_for(dr.BUILDING_1, dr.GROUND)
        joined = ' | '.join(STRINGS['P-601'])
        for figure in (inches(e.drop), fmt(e.run), inches(-e.deep_bot), inches(-e.pipe_top)):
            self.assertIn(figure, joined, 'P-601 no longer prints %s' % figure)


if __name__ == '__main__':
    unittest.main()

"""G-001's scope of work: the four trades the City of Columbus asks for, and every figure
   in them read from the model rather than typed beside it."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class ScopeOfWorkTests(unittest.TestCase):

    def setUp(self):
        from src.sheets.g001 import scope_of_work
        self.scope = scope_of_work()
        self.sheets = {h: s for h, s, _i in self.scope}
        self.text = {h: " ".join(i) for h, _s, i in self.scope}

    def test_the_four_trades_in_the_order_columbus_lists_them(self):
        self.assertEqual([h for h, _s, _i in self.scope],
                         ['STRUCTURAL', 'ELECTRICAL', 'MECHANICAL', 'PLUMBING'])
        for h, s, items in self.scope:
            self.assertTrue(s, h)
            self.assertTrue(items, h)

    def test_each_trade_names_the_sheets_it_is_drawn_on(self):
        for sh in ('S-101', 'S-102', 'S-103', 'S-104'):
            self.assertIn(sh, self.sheets['STRUCTURAL'])
        for sh in ('E-101', 'E-102'):
            self.assertIn(sh, self.sheets['ELECTRICAL'])
        for sh in ('M-101', 'M-102'):
            self.assertIn(sh, self.sheets['MECHANICAL'])
        for sh in ('P-101', 'P-102', 'P-103', 'P-601'):
            self.assertIn(sh, self.sheets['PLUMBING'])

    def test_structural_figures_are_the_foundation_framing_and_roof_models(self):
        from lib.units import inches
        from src.foundation import FROST_DEPTH, FTG_T, FTG_W, STRIP_W
        from src.framing import F1_JOIST, F2_JOIST, JOIST_OC
        from src.roof import ROOF_PITCH, TRUSS_OC
        t = self.text['STRUCTURAL']
        for v in (FTG_W, FTG_T, FROST_DEPTH, STRIP_W, F1_JOIST, F2_JOIST, JOIST_OC, TRUSS_OC):
            self.assertIn(inches(v), t)
        self.assertIn('%d:12' % round(ROOF_PITCH*12), t)
        # the exterior wood stairs are framed prescriptively and take a shop drawing;
        # no engineer is named for them anywhere in the set
        self.assertIn('SHOP DRAWING', t)
        # the wall bracing is the bracing model's: its method, portals and hold-downs
        from src import bracing
        from codes.ohio.rco import bracing as rco_bracing
        self.assertIn('METHOD %s' % rco_bracing.METHOD, t)
        n = sum(len(bracing.portal_openings(ln)) for ln in bracing.LINES)
        self.assertIn('%d CS-PF PORTAL FRAME%s ' % (n, '' if n == 1 else 'S'), t)
        self.assertIn('%d HOLD-DOWNS' % sum(1 for ln in bracing.LINES for e in ln.ends if e.hold_down is not None), t)
        self.assertNotIn('ENGINEER', " ".join(self.text.values()))

    def test_each_service_and_panel_rating_is_the_electrical_models(self):
        from src.electrical import SERVICES
        from codes.nec.load import service_loads
        t = self.text['ELECTRICAL']
        for s in SERVICES:
            self.assertIn('%d A AT METER BANK %s' % (service_loads(s)[3], s['mark']), t)
            for _pos, amps, _name in s['positions']:
                self.assertIn('%d A' % amps, t)

    def test_heat_pumps_and_heads_are_the_mechanical_models(self):
        from src.mechanical import outdoor_units
        rows = outdoor_units()
        t = self.text['MECHANICAL']
        self.assertIn('%s TO %s' % (rows[0]['mark'], rows[-1]['mark']), t)
        self.assertIn('%d WALL HEADS' % sum(len(r['heads']) for r in rows), t)

    def test_plumbing_figures_are_the_water_and_drainage_models(self):
        from lib.units import fmt
        from src import drainage, plumbing
        t = self.text['PLUMBING']
        for b in plumbing.BUILDINGS:
            self.assertIn('%s"' % plumbing.sizes(b)['service'], t)
        heaters = sum(1 for b in plumbing.BUILDINGS for u in b.units
                      for f in u.fixtures if f.kind == 'wh')
        self.assertIn('%d ELECTRIC STORAGE WATER HEATERS' % heaters, t)
        self.assertIn('%d STACKS' % sum(len(b.stacks) for b in drainage.BUILDINGS), t)
        self.assertIn(fmt(drainage.sewer()['on_lot']), t)

    def test_no_trade_mentions_fuel_gas(self):
        """The set is all-electric: no scope item names gas, a gas meter or P-104."""
        for trade, t in self.text.items():
            self.assertNotIn('GAS', t, trade)
            self.assertNotIn('P-104', t, trade)


if __name__ == '__main__':
    unittest.main()

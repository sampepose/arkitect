"""W-A's net clear opening is a requirement on the product, RCO 310.2.1, not a size read
   off a nominal double hung: the minimums, the check that the drawn frame can host them,
   and the A-602 / G-001 text that holds a product to them."""
import os
import sys
import unittest
from arkitect.codes.ohio.rco import egress as egress_shared

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class EgressMinimumTests(unittest.TestCase):

    def test_the_minimums_are_rco_310_2_1_and_310_2_2(self):
        from arkitect.codes.ohio.rco import egress as rco_egress
        self.assertEqual(rco_egress.EGRESS_MIN_SF, 5.7)
        self.assertAlmostEqual(rco_egress.EGRESS_MIN_W*12, 20.0)
        self.assertAlmostEqual(rco_egress.EGRESS_MIN_H*12, 24.0)
        self.assertAlmostEqual(rco_egress.EGRESS_MAX_SILL*12, 44.0)

    def test_the_drawn_frame_passes(self):
        from src.openings import WIN_GEOM, WIN_W
        from arkitect.codes.ohio.rco.egress import check_egress_window
        check_egress_window(win_geom=WIN_GEOM, win_w=WIN_W)

    def _fails_with(self, name, value):
        # restored before returning, so each call patches exactly one figure
        # the minimums are the code's, arkitect/codes/ohio/rco/egress.py; the frame is this project's
        from src import openings as o
        old = getattr(egress_shared, name)
        setattr(egress_shared, name, value)
        try:
            with self.assertRaises(AssertionError, msg=name):
                egress_shared.check_egress_window(win_geom=o.WIN_GEOM, win_w=o.WIN_W)
        finally:
            setattr(egress_shared, name, old)

    def test_a_minimum_the_frame_cannot_host_fails_the_build(self):
        from arkitect.lib.units import IN
        # a 3'-0" x 6'-0" double hung opens at most 36" x 36" = 9.0 SF
        self._fails_with('EGRESS_MIN_H', IN(37))
        self._fails_with('EGRESS_MIN_W', IN(37))
        self._fails_with('EGRESS_MIN_SF', 9.1)

    def test_a_sill_over_44_inches_fails_the_build(self):
        from src import openings as o
        geom = dict(o.WIN_GEOM)
        self.addCleanup(setattr, o, 'WIN_GEOM', o.WIN_GEOM)
        geom['A'] = (3.75, geom['A'][1])
        o.WIN_GEOM = geom
        with self.assertRaises(AssertionError):
            egress_shared.check_egress_window(win_geom=o.WIN_GEOM, win_w=o.WIN_W)


class EgressSheetTextTests(unittest.TestCase):

    MINIMUMS = ('5.7 SF', '20"', '24"')
    ASSUMED = ('7.3', '33"', '32" x')

    def _requires_the_product(self, text):
        for s in self.MINIMUMS:
            self.assertIn(s, text)
        self.assertIn("MANUFACTURER'S PRODUCT DATA", text)
        for s in self.ASSUMED:
            self.assertNotIn(s, text)

    def test_a602_schedule_cell_states_the_minimums_and_fits_its_column(self):
        from reportlab.lib.units import inch
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src.sheets.a602 import wa_net_clear
        cell = wa_net_clear()
        self.assertTrue(cell.startswith('MIN '))
        for s in self.MINIMUMS:
            self.assertIn(s, cell)
        # NET CLEAR OPENING is 2.2" wide at 8.2 pt; leave a gap before EGRESS
        self.assertLess(stringWidth(cell, 'Helvetica', 8.2), 2.2*inch - 8)

    def test_a602_notes_require_product_data_at_submittal_and_inspection(self):
        from src.sheets.a602 import wa_notes
        lines = wa_notes()
        self.assertEqual(len(lines), 3)      # line for line: nothing below moves
        t = " ".join(lines)
        self._requires_the_product(t)
        for s in ('NET CLEAR OPENING AREA, WIDTH AND HEIGHT', 'BUILDING OFFICIAL',
                  'BEFORE', 'FRAMING INSPECTION', 'DO NOT INSTALL',
                  'RCO 310.2.1', 'NORMAL OPERATION FROM INSIDE', '5.0 SF'):
            self.assertIn(s, t)
        self.assertNotIn('VERIFY', t)

    def test_a602_life_safety_cites_the_minimums_and_does_not_restate_them(self):
        # The requirement has one home, G-001 note 8, and the product requirement one
        # more, the window schedule notes on this sheet. A third copy in the summary is
        # a figure that can drift from both, so the summary carries neither.
        from src.sheets.a602 import wa_life_safety
        lines = wa_life_safety()
        self.assertEqual(len(lines), 2)
        t = " ".join(lines)
        self.assertIn('G-001 NOTE 8', t)
        self.assertIn('WINDOW SCHEDULE NOTES', t)
        for s in self.MINIMUMS:
            self.assertNotIn(s, t)
        for s in self.ASSUMED:
            self.assertNotIn(s, t)

    def test_a602_lines_are_no_wider_than_their_blocks_already_ran(self):
        # A-602 asserts no column; these are the widest lines each block had before
        # (the RCO 308.4.5 W-B / W-C note at 8.0 pt, the smoke alarm line at 8.6 pt)
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src.sheets.a602 import wa_life_safety, wa_notes
        for t in wa_notes():
            self.assertLessEqual(stringWidth(t, 'Helvetica', 8.0), 731.0, t)
        for t in wa_life_safety():
            self.assertLessEqual(stringWidth(t, 'Helvetica', 8.6), 711.0, t)

    def test_g001_note_8a_holds_the_product_to_the_minimums(self):
        from src.sheets.g001 import note_8a
        lines = note_8a()
        self.assertEqual(len(lines), 2)      # G-001 has no vertical room
        self.assertTrue(lines[0].startswith('8a. '))
        t = " ".join(lines)
        self._requires_the_product(t)
        self.assertIn('A-602', t)

    def test_no_sheet_source_prints_the_assumed_opening(self):
        for mod in ('a602', 'g001', 'a001'):
            with open(os.path.join(HERE, 'projects', 'example_300', 'src', 'sheets', mod + '.py')) as f:
                src = f.read()
            self.assertNotIn('7.3 SF', src, mod)
            self.assertNotIn('33\\" x 32\\"', src, mod)
            self.assertNotIn('32\\" x 33\\"', src, mod)


class FallProtectionCitationTests(unittest.TestCase):
    """Ohio's RCO 312.2 requires no window fall protection and governs a device only where
       one is provided (ASTM F2090, 312.2.1; release, 312.2.2.2). 310.2.3 is window wells."""

    def _source(self, mod):
        with open(os.path.join(HERE, 'projects', 'example_300', 'src', 'sheets', mod + '.py')) as f:
            return f.read()

    def test_no_sheet_cites_window_wells_for_a_limiter(self):
        for mod in ('a001', 'a602', 'g001'):
            self.assertNotIn('310.2.3', self._source(mod), mod)

    def test_no_sheet_states_the_irc_sill_trigger_as_ohio(self):
        for mod in ('a001', 'a602'):
            src = self._source(mod)
            for s in ('312.2.1 ATTACHES', 'BEGINS TO REQUIRE', 'NOT CLEAR OF IT'):
                self.assertNotIn(s, src, mod)
            self.assertIn('RCO 312.2 REQUIRES NO WINDOW FALL PROTECTION', src, mod)
            self.assertIn('F2090', src, mod)

    def test_a602_fall_protection_lines_cite_ohio_and_fit_their_block(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src.sheets.a602 import wa_fall_protection
        lines = wa_fall_protection()
        self.assertEqual(len(lines), 2)
        t = " ".join(lines)
        for s in ('312.2.1', '312.2.2.2', 'A-001 NOTE 5b'):
            self.assertIn(s, t)
        for ln in lines:
            self.assertLessEqual(stringWidth(ln, 'Helvetica', 8.6), 711.0, ln)


if __name__ == '__main__':
    unittest.main()

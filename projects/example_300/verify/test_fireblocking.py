"""Fireblocking, RCO 302.11, and draftstopping, 302.12: each W4 wall's floor-line block,
   the W5 chase spacing, the floor areas, and the A-601 / A-001 text that states them."""
import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class FireblockingModelTests(unittest.TestCase):

    def test_the_code_figures(self):
        from src import fireblocking as fb
        self.assertAlmostEqual(fb.W5_BLOCK_MAX, 10.0)
        self.assertAlmostEqual(fb.BLOCK_T*12, 1.5)
        self.assertAlmostEqual(fb.BATT_BLOCK_H*12, 16.0)
        self.assertEqual(fb.DRAFTSTOP_SF, 1000.0)

    def test_the_note_ids_other_sheets_cite_are_fixed(self):
        # A-603's W4 sections cite these; renumbering one breaks a cross-reference
        from src import fireblocking as fb
        self.assertEqual(list(fb.FB.values()), ['FB-%d' % n for n in range(1, 10)])
        self.assertEqual((fb.FB['W4'], fb.FB['W5'], fb.FB['LINES'], fb.FB['PENETRATIONS']),
                         ('FB-1', 'FB-2', 'FB-3', 'FB-4'))
        self.assertEqual(fb.TAGS['W4_FLOOR'],
                         'FIREBLOCK — PLATES AND RIM, EACH W4 WALL AT ITS OWN FLOOR LINE, A-601 FB-1')
        self.assertEqual(fb.TAGS['PLATE_HOLE'], 'SEAL ANNULAR SPACE, A-601 FB-4')

    def test_each_wall_is_closed_at_its_own_floor_line(self):
        """W4A and W4B are separate walls: each cavity is closed from its own top plate to
           its own Level 2 sole plate, and no zone spans both."""
        from lib.units import fmt
        from src import fireblocking as fb, levels
        self.assertEqual(list(fb.W4_BLOCK_ZONES), ['W4A', 'W4B'])
        self.assertEqual(fb.W4_BLOCK_ZONES['W4A'], (levels.F2_PLATE, levels.SUBFLOOR_TOP))
        self.assertEqual(fb.W4_BLOCK_ZONES['W4B'], (levels.F1_PLATE, levels.SUBFLOOR_TOP))
        self.assertEqual([(fmt(lo), fmt(hi)) for lo, hi in fb.W4_BLOCK_ZONES.values()],
                         [('9\'-5-1/4"', '10\'-8"'), ('9\'-7-3/8"', '10\'-8"')])

    def test_w5_blocks_never_leave_more_than_ten_feet(self):
        from src.fireblocking import w5_blocks
        self.assertEqual(w5_blocks(10.0), (0, 10.0))
        n, sp = w5_blocks(10.01)
        self.assertEqual(n, 1); self.assertAlmostEqual(sp, 5.005)
        n, sp = w5_blocks(25.0 + 1/12.0)
        self.assertEqual(n, 2); self.assertLessEqual(sp, 10.0)

    def test_every_floor_ceiling_is_under_1000_sf(self):
        from src.fireblocking import floor_areas
        areas = floor_areas()
        self.assertEqual(list(areas), ['UNIT 1', 'UNITS 2 / 3', 'UNITS 4 / 5'])
        for sf in areas.values():
            self.assertLess(sf, 1000.0)

    def test_the_check_prints_one_line(self):
        from src import fireblocking as fb
        with contextlib.redirect_stdout(io.StringIO()) as out:
            fb.check_fireblocking()
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('FIREBLOCKING, RCO 302.11: each W4 wall closed at its own floor line, '
                                            'W4A +9\'-5-1/4" to +10\'-8"; W4B +9\'-7-3/8" to +10\'-8"'))

    def test_a_floor_line_with_no_depth_fails_the_build(self):
        from lib.units import IN
        from src import fireblocking as fb
        self.addCleanup(setattr, fb, 'W4_BLOCK_ZONES', fb.W4_BLOCK_ZONES)
        fb.W4_BLOCK_ZONES = dict(fb.W4_BLOCK_ZONES, W4B=(10.0, 10.0+IN(1)))
        with self.assertRaises(AssertionError), contextlib.redirect_stdout(io.StringIO()):
            fb.check_fireblocking()

    def test_a_floor_over_1000_sf_fails_the_build(self):
        from src import fireblocking as fb
        from src.framing import Bay, Floor
        big = Floor('TEST', 40.0, 30.0, bays=[Bay('UNIT 9 F1', 0.0, 0.0, 40.0, 30.0, 'h', 1.0, ('A', 'B'))], wells=[], rated_rims=[])
        self.addCleanup(setattr, fb, 'FLOORS', fb.FLOORS)
        fb.FLOORS = fb.FLOORS + (big,)
        with self.assertRaises(AssertionError), contextlib.redirect_stdout(io.StringIO()):
            fb.check_fireblocking()


class FireblockingSheetTextTests(unittest.TestCase):

    def test_a601_notes_run_fb1_to_fb9_in_order_and_quote_the_model(self):
        from src.sheets.a601 import _fireblocking_notes
        notes = _fireblocking_notes()
        self.assertEqual([n.split()[0] for n in notes], ['FB-%d' % k for k in range(1, 10)])
        text = ' '.join(notes)
        for s in ('W4A', 'W4B', '+9\'-5-1/4"', '+9\'-7-3/8"', '+10\'-8"', '10\'-0" MAXIMUM', '2 IN A 25\'-1" RUN',
                  'SF, UNDER 1,000 SF', 'A-001 NOTE 4a', 'RCO 302.7, A-001 NOTE 8b', 'P-601 NOTE 1aa', 'ITEM 6', '16"'):
            self.assertIn(s, text)
        # the listing is not where penetrations go, and neither unit's framing reaches the
        # other's wall (302.2.6): a rim is fastened to its OWN wall, never across
        self.assertNotIn('F1 LISTING', text)
        self.assertNotIn('FASTENED TO W4 ', text)

    def test_a001_4c_is_two_lines_no_wider_than_the_sheet_already_runs(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src.sheets.a001 import PLAN_NOTES
        i = next(k for k, t in enumerate(PLAN_NOTES) if t.startswith('4c.'))
        self.assertTrue(PLAN_NOTES[i-2].startswith('4b.'))
        self.assertTrue(PLAN_NOTES[i+2].startswith('5.'))
        self.assertTrue(PLAN_NOTES[i+1].endswith('SEE A-601 FB-1 TO FB-9.'))
        others = [t for k, t in enumerate(PLAN_NOTES) if k not in (i, i+1)]
        widest = max(stringWidth(t, 'Helvetica', 8.2) for t in others)
        for t in PLAN_NOTES[i:i+2]:
            self.assertLess(stringWidth(t, 'Helvetica', 8.2), widest)


if __name__ == '__main__':
    unittest.main()

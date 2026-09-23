"""lib/verify/sheet_text.py: the recorder keeps what is drawn where, and the sweeps find
   a string on a string, a sheet nobody drew and a note nobody printed."""
import os
import tempfile
import unittest

from reportlab.lib.colors import Color, black
from reportlab.pdfgen import canvas

from lib.verify import sheet_text as st


def _pages(draw):
    with tempfile.TemporaryDirectory() as tmp:
        r = st.Recorder(canvas.Canvas(os.path.join(tmp, 'x.pdf'), pagesize=(400, 300)))
        draw(r)
        return r.pages


class RecorderTests(unittest.TestCase):

    def test_a_string_on_a_string_is_found(self):
        def draw(c):
            st._CUR[0] = 'S-101'
            c.setFillColor(black); c.setFont('Helvetica', 8)
            c.drawString(50, 100, '10. THE LAST NOTE OF THE COLUMN')
            c.drawString(60, 101, 'TREATED 2x6 SILL')
            c.drawString(50, 60, 'CLEAR OF BOTH')
            c.showPage()
        hits = st.overlaps(_pages(draw)['S-101'])
        self.assertEqual([(a, b) for _area, a, b in hits], [('10. THE LAST NOTE OF THE COLUMN', 'TREATED 2x6 SILL')])

    def test_adjacent_lines_are_not_an_overlap(self):
        def draw(c):
            st._CUR[0] = 'A-001'
            c.setFont('Helvetica', 8)
            for k in range(4): c.drawString(50, 200-k*9.6, 'A NOTE LINE AT ITS OWN LEADING')
            c.showPage()
        self.assertEqual(st.overlaps(_pages(draw)['A-001']), [])

    def test_grey_and_rotated_text_are_kept_but_not_compared(self):
        def draw(c):
            st._CUR[0] = 'E-101'
            c.setFont('Helvetica', 8)
            c.setFillColor(Color(0.5, 0.5, 0.5)); c.drawString(50, 100, 'KITCHEN / DINING')
            c.setFillColor(black); c.drawString(52, 100, 'GFCI RECEPTACLE')
            c.saveState(); c.translate(54, 96); c.rotate(90); c.drawString(0, 0, 'ROTATED LABEL'); c.restoreState()
            c.showPage()
        page = _pages(draw)['E-101']
        self.assertEqual(len(page), 3)
        self.assertEqual(st.overlaps(page), [])

    def test_a_translated_string_is_placed_on_the_page(self):
        def draw(c):
            st._CUR[0] = 'A-101'
            c.setFont('Helvetica', 10)
            c.saveState(); c.translate(100, 50); c.drawCentredString(0, 0, 'MOVED'); c.restoreState()
            c.drawString(0, 0, 'HOME')
            c.showPage()
        moved, home = _pages(draw)['A-101']
        self.assertAlmostEqual((moved.x0+moved.x1)/2.0, 100.0, places=3)
        self.assertAlmostEqual(home.x0, 0.0)


class ReferenceTests(unittest.TestCase):

    def _set(self, **sheets):
        return {no.replace('_', '-'): [st.Text(0, 0, 1, 1, t, 6, True, True) for t in lines] for no, lines in sheets.items()}

    def test_a_sheet_nobody_drew(self):
        pages = self._set(A_101=['SEE A-604 AND S-101.', 'FINISH PER GA-214.'], S_101=['1.  FOUNDATION'])
        self.assertEqual(st.sheet_references(pages), [('A-101', 'A-604')])          # GA is no discipline of this set

    def test_a_note_nobody_printed(self):
        pages = self._set(A_101=["A-001 NOTE 13a AND S-101 NOTES 2, 9 AND 11; S-103 NOTE 9, 10'-0\" FROM"],
                          A_001=['13a.UNIT 3 STAIR', '13. STAIRS'], S_101=['2.  SLAB', '9.  BEARING'], S_103=['9. ROOF PENETRATIONS'])
        self.assertEqual(st.note_references(pages), [('A-101', 'S-101', '11')])


if __name__ == '__main__':
    unittest.main()

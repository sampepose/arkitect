"""riser(vent_label_clear=): a slab vent's label, in a stack that ends at its branch, stands
right of that vent's own dashed takeoff instead of across it; the default is unchanged."""
import io
import unittest

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas

from arkitect.codes.ohio import opc_vents_draw as D
from arkitect.lib.draw.context import document

LABEL = 'V-A  2"  INDIVIDUAL VENT — TIES INTO V-G IN THE ATTIC, 905.4'


class Recording(Canvas):
    def __init__(self):
        super().__init__(io.BytesIO())
        self.dashed, self.strings, self._on = [], [], False

    def setDash(self, *a, **k):
        self._on = bool(a and a[0])
        return super().setDash(*a, **k)

    def line(self, x1, y1, x2, y2):
        if self._on:
            self.dashed.append((x1, y1, x2, y2))
        return super().line(x1, y1, x2, y2)

    def drawString(self, x, y, text, *a, **k):
        self.strings.append((x, y, text, self._fontname, self._fontsize))
        return super().drawString(x, y, text, *a, **k)


def cell():
    floor = D.Floor(2, 'V-G', '3"', 'HORIZONTAL WET VENT', (
        D.Fix('LAV', '', ('V-G', '3"')), D.Fix('WC', ''), D.Fix('TUB', '')), 'THROUGH THE ROOF')
    slab = D.Slab('V-A', '2"', 'INDIVIDUAL VENT', (D.Fix('KITCHEN SINK', ''),), 'TIES INTO V-G IN THE ATTIC, 905.4')
    return D.Cell('STACK A', '3"', False, '3" VTR', {1: 'LEVEL 1', 2: 'LEVEL 2'}, (), (slab,),
                  None, None, None, None, (floor,), True)


def draw(**kw):
    cv = Recording()
    with document(cv):
        D.riser(72.0, 72.0, cell(), **kw)
    return cv


def label_lines(cv):
    words = set(LABEL.split())
    return [s for s in cv.strings if s[3] == 'Helvetica-Bold' and set(s[2].split()) <= words]


def crossed(cv):
    """The label lines some vertical dashed segment runs through."""
    out = []
    for x, y, text, font, size in label_lines(cv):
        wd = pdfmetrics.stringWidth(text, font, size)
        for x1, y1, x2, y2 in cv.dashed:
            if abs(x1-x2) < 1e-6 and x <= x1 <= x+wd and min(y1, y2) <= y <= max(y1, y2):
                out.append(text)
    return out


class VentLabelClear(unittest.TestCase):
    def test_the_default_still_sets_the_label_across_its_takeoff(self):
        cv = draw()
        self.assertTrue(label_lines(cv))
        self.assertTrue(crossed(cv))

    def test_opted_in_no_label_line_is_crossed_by_a_dashed_vent(self):
        cv = draw(vent_label_clear=True)
        self.assertTrue(label_lines(cv))
        self.assertEqual(crossed(cv), [])

    def test_opted_in_the_top_line_stays_where_it_was(self):
        top = max(s[1] for s in label_lines(draw()))
        self.assertAlmostEqual(max(s[1] for s in label_lines(draw(vent_label_clear=True))), top)

    def test_opted_in_every_word_is_still_printed(self):
        text = ' '.join(s[2] for s in sorted(label_lines(draw(vent_label_clear=True)), key=lambda s: -s[1]))
        self.assertEqual(text.split(), LABEL.split())


if __name__ == "__main__":
    unittest.main()

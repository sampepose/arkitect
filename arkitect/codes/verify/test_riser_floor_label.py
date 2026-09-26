"""riser(floor_label_clear=): a floor branch's label, in a stack that ends at that branch,
stands right of the head vent's dashed riser instead of across it; the default is unchanged."""
import unittest

from reportlab.pdfbase import pdfmetrics

from arkitect.codes.verify.test_riser_vent_label import draw

LABEL = 'HORIZONTAL WET VENT — THROUGH THE ROOF'


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


class FloorLabelClear(unittest.TestCase):
    def test_the_default_still_sets_the_label_across_the_head_vent(self):
        cv = draw()
        self.assertTrue(label_lines(cv))
        self.assertTrue(crossed(cv))

    def test_opted_in_no_label_line_is_crossed_by_a_dashed_vent(self):
        cv = draw(floor_label_clear=True)
        self.assertTrue(label_lines(cv))
        self.assertEqual(crossed(cv), [])

    def test_opted_in_the_bottom_line_stays_where_it_was(self):
        low = min(s[1] for s in label_lines(draw()))
        self.assertAlmostEqual(min(s[1] for s in label_lines(draw(floor_label_clear=True))), low)

    def test_opted_in_every_word_is_still_printed(self):
        text = ' '.join(s[2] for s in sorted(label_lines(draw(floor_label_clear=True)), key=lambda s: -s[1]))
        self.assertEqual(text.split(), LABEL.split())


if __name__ == "__main__":
    unittest.main()

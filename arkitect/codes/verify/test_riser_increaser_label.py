"""riser(increaser_label_clear=): the 903.2 increaser's label, in a stack that ends at its
floor branch, stands right of the last dry vent rising beside the head vent instead of across
that vent's dashed riser; the default is unchanged."""
import unittest

from reportlab.pdfbase import pdfmetrics

from arkitect.codes.ohio import opc_vents_draw as D
from arkitect.codes.verify.test_riser_vent_label import Recording
from arkitect.lib.draw.context import document

INCREASER = '2" x 3" INCREASER, NOTE 1d'


def cell():
    floor = D.Floor(2, 'V-G', '3"', 'HORIZONTAL WET VENT', (
        D.Fix('LAV', '', ('V-G', '3"')), D.Fix('LAV', '', ('V-H', '1-1/2"')), D.Fix('WC', ''), D.Fix('TUB', '')),
        'THROUGH THE ROOF')
    return D.Cell('STACK A', '3"', False, '3" VTR', {1: 'LEVEL 1', 2: 'LEVEL 2'}, (), (),
                  None, None, None, INCREASER, (floor,), True)


def draw(**kw):
    cv = Recording()
    with document(cv):
        D.riser(72.0, 72.0, cell(), increaser_below_ceiling=True, **kw)
    return cv


def crossed(cv):
    """Whether a vertical dashed segment runs through the increaser's label."""
    (x, y, text, font, size), = [s for s in cv.strings if s[2] == INCREASER]
    wd = pdfmetrics.stringWidth(text, font, size)
    return any(abs(x1-x2) < 1e-6 and x <= x1 <= x+wd and min(y1, y2) <= y <= max(y1, y2)
               for x1, y1, x2, y2 in cv.dashed)


class IncreaserLabelClear(unittest.TestCase):
    def test_the_default_still_sets_the_label_across_the_dry_vent(self):
        self.assertTrue(crossed(draw()))

    def test_opted_in_no_dashed_vent_runs_through_the_label(self):
        self.assertFalse(crossed(draw(increaser_label_clear=True)))

    def test_opted_in_the_label_keeps_its_height(self):
        at = lambda cv: [s[1] for s in cv.strings if s[2] == INCREASER]
        self.assertEqual(at(draw()), at(draw(increaser_label_clear=True)))


if __name__ == '__main__':
    unittest.main()

"""arkitect/codes/zoning_sheets.py and arkitect/lib/buildkit.py: the two day-one sheets build for an
interior lot and a corner lot, check the model before drawing, and print no string on
another (arkitect/lib/verify/sheet_text.py's overlap rule, read through a recording canvas)."""
import os
import tempfile
import unittest

from reportlab.pdfgen import canvas as _rl

from arkitect.codes.ohio import columbus as J
from arkitect.codes.ohio.columbus import fit as F
from arkitect.codes.zoning_sheets import cover_sheet, zoning_rows, zoning_site_plan
from arkitect.harness import intake as I
from arkitect.harness.verify.fixtures import example
from arkitect.lib.buildkit import documents
from arkitect.lib.verify import sheet_text as ST


def corner():
    d = example()
    d['lot'].update(corner=True, side_street='left', side_street_line=5.0)
    d['side_street_name'] = 'SIDE STREET'
    d['relief']['street_vision'] = 'VARIANCE REQUESTED'
    d['parking']['x0'] = 10.0
    return d


def build(d, calls=None):
    """Draw both documents to a scratch directory through sheet_text's Recorder."""
    m = I.massing(d)
    recs = []
    check = (lambda: calls.append('check')) if calls is not None else (lambda: None)
    docs = documents([(None, [d['address'], d['city_line']])], check,
                     [cover_sheet(d, m, [('G-001', 'COVER SHEET'), ('C-102', 'ZONING SITE PLAN')])],
                     None, zoning_site_plan(d, m), None)

    def make(*a, **k):
        r = ST.Recorder(_rl.Canvas(*a, **k))
        recs.append(r)
        return r
    with tempfile.TemporaryDirectory() as t:
        for doc in docs:
            doc(os.path.join(t, doc.__name__ + '.pdf'), make_canvas=make)
    pages = {}
    for r in recs:
        for no, items in r.pages.items():
            pages.setdefault(no, []).extend(items)
    return pages


class DayOneSheetTests(unittest.TestCase):

    def test_both_documents_build_and_check_the_model_first(self):
        calls = []
        pages = build(example(), calls)
        self.assertEqual(sorted(pages), ['C-102', 'G-001'])
        self.assertEqual(calls, ['check', 'check'])            # one per document

    def test_no_string_stands_on_another(self):
        for d in (example(), corner()):
            pages = build(d)
            for no, items in pages.items():
                self.assertEqual(ST.overlaps(items), [], no)

    def test_the_corner_lot_names_its_side_street(self):
        text = ' '.join(t.text for t in build(corner())['C-102'])
        self.assertIn('SIDE STREET', text)
        self.assertIn('VARIANCE REQUESTED', text)

    def test_a_rule_not_yet_checkable_prints_pending_not_a_figure(self):
        rows = dict(zoning_rows(F.fit(I.massing(example())), J))
        self.assertEqual(rows['Building height, 3332.29'], 'PENDING DESIGN')

    def test_an_unverified_section_is_not_printed_as_one(self):
        labels = [a for a, _b in zoning_rows(F.fit(I.massing(example())), J)]
        self.assertFalse([a for a in labels if 'UNVERIFIED' in a])
        self.assertIn('Lot coverage', labels)                 # printed with no section


if __name__ == '__main__':
    unittest.main()

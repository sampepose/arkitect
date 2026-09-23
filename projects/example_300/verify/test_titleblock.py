"""The title block's CONTENT: who the sheets say is building this, and whether every line
   it prints fits the column it prints in.

   `Sheet.frame()` already asserts the width, but only while drawing, and only for the
   lines a build happens to reach — so the guard is real and untested, and a block nobody
   draws in a given run is unmeasured. These tests read `src.project.TITLEBLOCK` directly
   and measure every line of every block at the font and size frame() draws it with, on
   every page size the project uses.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _block(heading):
    from src.project import TITLEBLOCK
    for head, body in TITLEBLOCK:
        if head == heading:
            return body
    raise AssertionError("no %r block in TITLEBLOCK" % (heading,))


def _every_line(titleblock):
    """(text, font, size) for each line, matching what Sheet.frame() sets before it draws.

       The first block has no heading and carries the larger type: body[0] at
       Helvetica-Bold 13, the rest at Helvetica 9.5. Every later block draws its heading
       at Helvetica-Bold 8.5 and its body at Helvetica 9."""
    for i, (head, body) in enumerate(titleblock):
        if i == 0:
            yield body[0], "Helvetica-Bold", 13
            for ln in body[1:]:
                yield ln, "Helvetica", 9.5
        else:
            yield head, "Helvetica-Bold", 8.5
            for ln in body:
                yield ln, "Helvetica", 9


class ContractorTests(unittest.TestCase):
    """Example Construction LLC, City of Columbus general contractor registration
       G00000 (the designer, 2026-09-15). LIC-APP0000000 was the portal's Application record and
       is retired."""

    def test_the_contractor_block_names_the_company_the_role_and_the_registration(self):
        self.assertEqual(_block("CONTRACTOR"),
                         ["EXAMPLE CONSTRUCTION LLC",
                          "COLUMBUS GENERAL CONTRACTOR",
                          "REGISTRATION NO. G00000"])

    def test_the_registration_number_prints_once_and_only_in_the_contractor_block(self):
        from src.project import TITLEBLOCK
        hits = [(head, ln) for head, body in TITLEBLOCK for ln in body if "G00000" in ln]
        self.assertEqual(hits, [("CONTRACTOR", "REGISTRATION NO. G00000")])

    def test_the_application_number_is_gone(self):
        """CLAUDE.md's fifth oracle, as a test: the trace sees a string change and cannot
           say it is wrong, and the other three oracles are blind to a stale word."""
        from src.project import TITLEBLOCK
        flat = " ".join(ln for head, body in TITLEBLOCK for ln in ([head or ""] + list(body)))
        for retired in ("LIC-APP", "2605015", "REGISTRATION PENDING"):
            self.assertNotIn(retired, flat)


class WidthTests(unittest.TestCase):

    def _avail(self, page):
        from reportlab.lib.units import inch
        return page.TBW - 0.44 * inch          # frame(): avail = TBW - 0.44*inch

    def test_every_line_fits_every_page_size(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.lib.units import inch
        from lib.draw import page as pg
        from src.project import TITLEBLOCK
        for name in ("ARCH_C", "ANSI_B"):
            page = getattr(pg, name)
            avail = self._avail(page)
            for text, font, size in _every_line(TITLEBLOCK):
                w = pdfmetrics.stringWidth(text, font, size)
                self.assertLessEqual(
                    w, avail,
                    "%s: %r needs %.2f in of a %.2f in column"
                    % (name, text, w / inch, avail / inch))

    def test_the_registration_line_is_not_what_governs_the_column(self):
        """If this ever fails the contractor line has become the widest thing in the
           block, and the margin the other tests rely on is gone."""
        from reportlab.pdfbase import pdfmetrics
        from src.project import TITLEBLOCK
        widths = {text: pdfmetrics.stringWidth(text, font, size)
                  for text, font, size in _every_line(TITLEBLOCK)}
        widest = max(widths, key=widths.get)
        self.assertNotIn("G00000", widest)


if __name__ == "__main__":
    unittest.main()

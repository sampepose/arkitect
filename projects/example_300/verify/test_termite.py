"""Termite protection, RCO 318: Table 301.2(1)'s entry for Columbus, the 318.1 method the
   set uses, the 318.4 foam check, and the sheet text that specifies the method."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


class TermiteBasisTests(unittest.TestCase):

    def test_columbus_is_moderate_to_heavy_and_the_method_is_soil_treatment(self):
        from src import foundation as f
        self.assertEqual(f.TERMITE, "MODERATE TO HEAVY")
        self.assertEqual(f.TERMITE_SCALE,
                         ("NONE TO SLIGHT", "SLIGHT TO MODERATE", "MODERATE TO HEAVY", "VERY HEAVY"))
        self.assertEqual(sorted(f.TERMITE_METHODS), [1, 2, 3, 4, 5, 6])     # 318.1 items 1-6
        self.assertEqual(f.TERMITE_METHOD, 1)
        self.assertIn("318.2", f.TERMITE_METHODS[1])
        self.assertEqual(f.TERMITE_TREATMENT, "SOIL TREATMENT")

    def test_the_set_passes(self):
        from src import foundation as f
        f.check_termite()
        f.check_basis()

    def _fails_with(self, **patch):
        from src import foundation as f
        old = {k: getattr(f, k) for k in patch}
        for k, v in patch.items():
            setattr(f, k, v)
        try:
            with self.assertRaises(AssertionError, msg=patch):
                f.check_basis()
        finally:
            for k, v in old.items():
                setattr(f, k, v)

    def test_an_entry_off_the_scale_fails(self):
        self._fails_with(TERMITE="MODERATE")

    def test_an_area_subject_to_damage_without_a_method_fails(self):
        self._fails_with(TERMITE_METHOD=None)
        self._fails_with(TERMITE="SLIGHT TO MODERATE", TERMITE_METHOD=7)

    def test_very_heavy_with_the_xps_below_grade_fails_318_4(self):
        from src import foundation as f
        from src import levels
        self.assertLess(levels.SLAB_TOP - f.EDGE_INSUL_RUN, levels.GRADE)   # it does run below grade
        self._fails_with(TERMITE="VERY HEAVY")
        # and the check is the foam's depth, not the entry alone
        old = (f.TERMITE, f.EDGE_INSUL_RUN)
        f.TERMITE, f.EDGE_INSUL_RUN = "VERY HEAVY", levels.SLAB_TOP - levels.GRADE
        try:
            f.check_termite()
        finally:
            f.TERMITE, f.EDGE_INSUL_RUN = old

    def test_check_foundation_prints_the_termite_row(self):
        import io, contextlib
        from src import foundation as f
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            f.check_foundation()
        row = [ln for ln in out.getvalue().splitlines() if ln.startswith("TERMITE")]
        self.assertEqual(len(row), 1)
        self.assertIn("MODERATE TO HEAVY", row[0])
        self.assertIn("318.4 FOAM BAR NOT TRIGGERED", row[0])


class S101TermiteBlockTests(unittest.TestCase):

    def _width(self):
        from reportlab.lib.units import inch
        from lib.draw.kit import Q, X0
        from src.foundation import B1
        # the gap from the Building 1 plan's origin to Building 2's column, as sheet_s101 sets it
        return (X0+1.1*inch+B1.W*Q+2.3*inch) - 0.3*inch - (X0+1.1*inch)

    def test_the_block_specifies_the_method_the_model_names(self):
        from src import foundation as f
        from src.sheets.s101 import termite_notes
        t = " ".join(termite_notes(self._width()))
        for s in (f.TERMITE, "RCO 318.1 ITEM %d" % f.TERMITE_METHOD, f.TERMITE_METHODS[f.TERMITE_METHOD],
                  f.TERMITE_TREATMENT, "318.2", "STRICT ACCORDANCE WITH THE TERMITICIDE LABEL",
                  "OHIO DEPARTMENT OF AGRICULTURE", "TERMITE CONTROL",
                  "BEFORE THE VAPOR RETARDER", "SLAB PENETRATION", "UNDER EACH PAD", "AFTER FINISHED GRADING",
                  "CERTIFICATE", "EPA REGISTRATION NUMBER", "BUILDING OFFICIAL", "BEFORE EACH SLAB IS POURED"):
            self.assertIn(s, t)
        # notes instruct: nothing argues why the foam bar does not apply
        self.assertNotIn("318.4", t)
        self.assertNotIn("NOTE 10", t)

    def test_the_labels_run_t1_to_t4_and_every_line_fits(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src.sheets.s101 import TERMITE_SIZE, termite_notes
        W = self._width()
        lines = termite_notes(W)
        self.assertEqual([ln[:3] for ln in lines if not ln.startswith(" ")], ["T1.", "T2.", "T3.", "T4."])
        for ln in lines:
            self.assertLessEqual(stringWidth(ln, "Helvetica", TERMITE_SIZE), W, ln)

    def test_the_notes_cited_are_the_ones_s101_prints(self):
        with open(os.path.join(HERE, "projects", "example_300", "src", "sheets", "s101.py")) as fh:
            src = fh.read()
        for label, word in (("2.  SLAB", "SLAB"), ("4.  INTERIOR BEARING STRIPS", "STRIPS"), ("5.  PADS", "PADS"),
                            ("6.  ANCHOR BOLTS", "SILL PLATES PRESERVATIVE TREATED"), ("8.  UNDER-SLAB PLUMBING", "PLUMBING")):
            self.assertIn(label, src)
            self.assertIn(word, src)


class G001TermiteRowTests(unittest.TestCase):

    def test_the_row_reads_the_model_and_points_to_s101(self):
        with open(os.path.join(HERE, "projects", "example_300", "src", "sheets", "g001.py")) as fh:
            src = fh.read()
        self.assertIn('("Termite","%s — %s, S-101"%(TERMITE,TERMITE_TREATMENT))', src)
        self.assertNotIn('("Termite","MODERATE TO HEAVY")', src)

    def test_the_row_fits_its_block(self):
        from reportlab.lib.units import inch
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src.foundation import TERMITE, TERMITE_TREATMENT
        value = "%s — %s, S-101" % (TERMITE, TERMITE_TREATMENT)
        self.assertEqual(value, "MODERATE TO HEAVY — SOIL TREATMENT, S-101")
        # the DESIGN CRITERIA block is 4.6" at 8.6 pt, label left, value right; leave a gap
        self.assertLess(stringWidth("Termite", "Helvetica", 8.6) + stringWidth(value, "Helvetica", 8.6) + 12,
                        4.6*inch)


if __name__ == "__main__":
    unittest.main()

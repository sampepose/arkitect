"""The interior paint systems A-602's room finish schedule names."""
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


class FinishTests(unittest.TestCase):

    def test_model_is_clean(self):
        from src import finishes as f
        self.assertEqual(f.finish_violations(), [])
        with contextlib.redirect_stdout(io.StringIO()):
            f.check_finishes()

    def test_living_walls_are_scrubbable_eggshell_not_semigloss(self):
        from src import finishes as f
        rooms = {r.name: r for r in f.ROOMS}
        for n in ("LIVING / DINING", "BEDROOMS", "KITCHEN", "HALLS AND STAIRS"):
            p = f.PAINT[rooms[n].wall]
            self.assertEqual(p.sheen, "EGGSHELL", n)
            self.assertGreaterEqual(p.scrub, 1000, n)

    def test_wet_rooms_are_mildew_resistant_semigloss(self):
        from src import finishes as f
        for r in f.ROOMS:
            if r.wet:
                for tag in (r.wall, r.ceiling):
                    self.assertTrue(f.PAINT[tag].mildew, r.name)
                    self.assertEqual(f.PAINT[tag].mpi, 5, r.name)

    def test_a_semigloss_kitchen_wall_fails_because_the_kitchen_is_open(self):
        from src import finishes as f
        old = f.ROOMS
        try:
            f.ROOMS = tuple(r._replace(wall="PT-2") if r.name == "KITCHEN" else r for r in old)
            bad = f.finish_violations()
            self.assertTrue(any("open spaces" in b for b in bad), bad)
        finally:
            f.ROOMS = old

    def test_a_wall_system_under_the_scrub_floor_fails(self):
        from src import finishes as f
        old = f.PAINT
        try:
            f.PAINT = dict(old, **{"PT-1": old["PT-1"]._replace(scrub=400)})
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(AssertionError):
                    f.check_finishes()
        finally:
            f.PAINT = old

    def test_flat_on_a_bathroom_fails(self):
        from src import finishes as f
        old = f.ROOMS
        try:
            f.ROOMS = tuple(r._replace(ceiling="PT-3") if r.name == "BATHROOMS" else r for r in old)
            self.assertTrue(f.finish_violations())
        finally:
            f.ROOMS = old

    def test_every_cell_and_note_fits_its_column(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from src import finishes as f
        from src.sheets.a602 import FINISH_WIDTHS, FINISH_NOTE_W
        for row in f.schedule_rows():
            for v, w in zip(row, FINISH_WIDTHS):
                self.assertLess(stringWidth(v, "Helvetica", 8.2), w * 72 - 6, v)
        for t in f.notes():
            self.assertLessEqual(stringWidth(t, "Helvetica", 8.0), FINISH_NOTE_W, t)


if __name__ == "__main__":
    unittest.main()

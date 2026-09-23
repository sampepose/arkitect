"""The interior vapor retarder of the exterior frame walls, RCO 702.7."""
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


class VapourRetarderTests(unittest.TestCase):

    def test_class_ii_is_over_a_tenth_and_not_over_one_perm(self):
        from src import envelope as e
        self.assertEqual(e.VR_CLASS_PERMS['II'], (0.1, 1.0))
        self.assertEqual(e.VR_CLASS, 'II')
        self.assertEqual(e.perm_text(), '1.0 PERM')

    def test_check_prints_the_class_and_the_walls(self):
        from src import envelope as e
        with contextlib.redirect_stdout(io.StringIO()) as out:
            e.check_vapor_retarder()
        self.assertEqual(out.getvalue().strip(),
                         'VAPOR RETARDER  climate zone 5, RCO 702.7: Class II, 1.0 PERM max, interior of W1 / W1R')

    def test_class_iii_fails_in_climate_zone_5(self):
        from src import envelope as e
        old = e.VR_CLASS, e.VR_PERM
        try:
            e.VR_CLASS, e.VR_PERM = 'III', 5.0
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(AssertionError):
                    e.check_vapor_retarder()
        finally:
            e.VR_CLASS, e.VR_PERM = old

    def test_a_rating_outside_its_class_fails(self):
        from src import envelope as e
        old = e.VR_PERM
        try:
            e.VR_PERM = 1.2
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(AssertionError):
                    e.check_vapor_retarder()
        finally:
            e.VR_PERM = old

    def test_a601_rows_end_with_the_retarder(self):
        from src import envelope as e
        from src.sheets.a601 import wall_rows
        rows = wall_rows()
        e.check_wall_rows(rows)
        for t in e.EXTERIOR_FRAME_WALLS:
            self.assertTrue(rows[t].endswith(' / CLASS II VAPOR RETARDER PRIMER'), t)

    def test_a_wall_row_without_the_retarder_fails(self):
        from src import envelope as e
        from src.sheets.a601 import wall_rows
        rows = wall_rows()
        rows['W1R'] = rows['W1R'][:-len(' / ' + e.vr_layer())]
        with self.assertRaises(AssertionError):
            e.check_wall_rows(rows)

    def test_a601_rows_fit_the_assembly_column(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.lib.units import inch
        from src.sheets.a601 import ASM_WIDTHS, wall_rows
        for t, s in wall_rows().items():
            self.assertLessEqual(pdfmetrics.stringWidth(s, 'Helvetica', 8.4), (ASM_WIDTHS[1]-0.25)*inch, t)

    def test_a601_note_states_class_rating_and_submittal(self):
        from src.sheets.a601 import vr_note
        s = vr_note()
        for part in ('W1 / W1R', 'CLASS II', 'RCO 702.7', 'CLIMATE ZONE 5', '1.0 PERM OR LESS',
                     'ASTM E96 PROCEDURE A', 'INTERIOR GYPSUM', '702.7.2'):
            self.assertIn(part, s)

    def test_a602_energy_row(self):
        from src.sheets.a602 import wall_vr_row
        self.assertEqual(wall_vr_row(), ('WALL VAPOR RETARDER, RCO 702.7', 'CLASS I OR II, INTERIOR SIDE',
                                         'CLASS II PRIMER, 1.0 PERM MAX, ON THE GYPSUM OF W1 / W1R — A-601'))


if __name__ == '__main__':
    unittest.main()

"""400 Oak's cover and site plan: G-001's index is the set build_set binds, its figures
   are the model's, and the whole set (G-001 and C-101 included) builds."""
import os
import tempfile
import unittest

from projects.example_400.verify import PROJ, enter, leave


def setUpModule():
    enter()


def tearDownModule():
    leave()


class CoverTests(unittest.TestCase):

    def test_the_index_is_what_the_set_binds(self):
        from lib import buildscript
        b = buildscript.load(os.path.join(PROJ, "build.py"))
        from src.sheets.g001 import SEPARATE, SHEET_INDEX
        bound = ['%s-%s' % (f.__name__[6].upper(), f.__name__[7:]) for f in b.SHEETS]
        self.assertEqual(bound, [n for n, _t in SHEET_INDEX if n not in SEPARATE])
        self.assertEqual(bound[:2], ["G-001", "C-101"])

    def test_the_figures_are_the_models(self):
        from src.sheets import g001
        from src import sitework
        self.assertEqual(g001.GROSS_SF, sum(b[2]*b[3] for b in sitework.SITE_BLDG)*2)
        self.assertEqual(g001.BEDROOMS, 7)
        self.assertEqual([u[5] for u in g001.UNITS], [sitework.PRINCIPAL_SF, sitework.ADU_SF, sitework.ADU_SF])

    def test_the_scope_of_work_reads_the_electrical_model(self):
        from src.sheets import g001
        scope = dict((t, items) for t, _w, items in g001.scope_of_work())
        self.assertIn("HP-1 TO HP-3", scope["MECHANICAL"][0])
        self.assertIn("3 ELECTRIC WATER HEATERS", scope["PLUMBING"][0])
        self.assertIn('14" OPEN-WEB WOOD FLOOR TRUSSES', scope["STRUCTURAL"][3])

    def test_the_set_builds(self):
        from lib import buildscript
        b = buildscript.load(os.path.join(PROJ, "build.py"))
        with tempfile.TemporaryDirectory() as d:
            out = b.build_set(output_path=os.path.join(d, "set.pdf"))
            self.assertGreater(os.path.getsize(out), 1000)


if __name__ == '__main__':
    unittest.main()

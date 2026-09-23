"""arkitect/harness/catalog.py: every guard is a real module, the per-building expansion is right, and
a sheet's references are found in whatever projects the checkout holds. That a complete set
actually RUNS every guard is a claim about a project, so it is that project's test
(its own verify/test_catalog_guards.py)."""
import importlib
import os
import tempfile
import unittest

from arkitect.harness import catalog
from arkitect.harness.verify.fixtures import example


class CatalogTests(unittest.TestCase):

    def test_every_guard_is_an_importable_module_in_every_jurisdiction(self):
        from arkitect.codes import jurisdiction
        for name in jurisdiction.available():
            for _no, _title, guards in catalog.SHEETS:
                for g in catalog.guards_for(guards, name):
                    with self.subTest(jurisdiction=name, guard=g):
                        importlib.import_module(g)

    def test_a_guard_names_its_jurisdiction_only_by_zoning_and_state(self):
        import string
        for _no, _title, guards in catalog.SHEETS:
            for g in guards:
                fields = {f for _t, f, _s, _c in string.Formatter().parse(g) if f}
                self.assertLessEqual(fields, {'zoning', 'state'}, g)
                self.assertFalse('columbus' in g or 'ohio' in g, g)

    def test_the_catalog_names_no_project(self):
        for entry in catalog.SHEETS:
            self.assertEqual(len(entry), 3, entry)                      # number, title, guards
            self.assertFalse([t for t in (entry[0], entry[1]) + tuple(entry[2])
                              if 'projects/' in t], entry)

    def test_references_are_found_by_the_sheet_function_they_define(self):
        with tempfile.TemporaryDirectory() as root:
            for slug, f, body in (('one', 'a101.py', 'def sheet_a101():\n    pass\n'),
                                  ('two', 'plans.py', 'def sheet_a101():\n    pass\n'),
                                  ('two', 'other.py', 'def sheet_a1010():\n    pass\n')):
                d = os.path.join(root, 'projects', slug, 'src', 'sheets')
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, f), 'w') as fh:
                    fh.write(body)
            self.assertEqual(catalog.references('A-101', root),
                             ['projects/one/src/sheets/a101.py', 'projects/two/src/sheets/plans.py'])
            self.assertEqual(catalog.references('A-101', root, exclude='one'),
                             ['projects/two/src/sheets/plans.py'])
            self.assertEqual(catalog.references('S-104', root), [])

    def test_features_expand_per_building_in_binding_order(self):
        ids = [f['id'] for f in catalog.features(example())]
        self.assertEqual(ids[:6], ['G-001', 'C-101', 'C-103', 'A-001', 'A-101', 'A-102'])
        self.assertIn('P-103', ids)                       # water supply, second building
        self.assertEqual(ids[-1], 'C-102')
        self.assertEqual(len(ids), len(set(ids)))

    def test_day_one_sheets_start_drawn_and_the_rest_pending(self):
        st = {f['id']: f['status'] for f in catalog.features(example())}
        self.assertEqual(st['G-001'], 'drawn')
        self.assertEqual(st['C-102'], 'drawn')
        self.assertEqual(st['A-101'], 'pending')


if __name__ == '__main__':
    unittest.main()

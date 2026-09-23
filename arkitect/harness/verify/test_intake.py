"""arkitect/harness/intake.py: an intake is valid, or every problem with it is named."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from arkitect.harness import intake as I
from arkitect.harness.verify.fixtures import example

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ValidateTests(unittest.TestCase):

    def test_the_example_is_valid(self):
        self.assertEqual(I.validate(example()), [])

    def test_the_slug_is_an_identifier(self):
        self.assertTrue(any('slug' in p for p in I.validate(example(slug='100-example'))))
        self.assertEqual(I.slug_for('42 N OAK ST'), 'oak_42')
        self.assertEqual(I.slug_for('7 ELM AVE'), 'elm_7')

    def test_another_city_is_research_not_a_flag(self):
        bad = I.validate(example(jurisdiction='cleveland'))
        self.assertTrue(any('code-research' in p for p in bad), bad)

    def test_one_principal_building(self):
        d = example()
        d['buildings'][1]['role'] = 'principal'
        self.assertTrue(any('exactly one' in p for p in I.validate(d)))

    def test_a_building_off_the_lot_or_on_another(self):
        d = example()
        d['buildings'][1]['x'] = 20.0                         # 20 + 22 > 35
        self.assertTrue(any('leaves the lot' in p for p in I.validate(d)))
        d = example()
        d['buildings'][1]['y'] = 40.0                         # into Building 1
        self.assertTrue(any('overlap' in p for p in I.validate(d)))

    def test_the_pad_must_clear_the_buildings(self):
        d = example()
        d['parking']['depth'] = 30.0                          # reaches Building 2
        self.assertTrue(any('parking pad' in p for p in I.validate(d)))

    def test_a_corner_lot_names_its_side_street(self):
        d = example()
        d['lot']['corner'] = True
        bad = I.validate(d)
        self.assertTrue(any('side_street' in p for p in bad))
        self.assertTrue(any('side_street_name' in p for p in bad))

    def test_relief_names_a_rule(self):
        self.assertTrue(any('not a rule' in p for p in I.validate(example(relief={'lotwidth': 'x'}))))

    def test_every_dwelling_has_bedrooms(self):
        d = example()
        del d['buildings'][0]['dwellings'][0]['bedrooms']
        self.assertTrue(any('bedrooms' in p for p in I.validate(d)))


class CommandTests(unittest.TestCase):

    def run_on(self, d, *flags):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, 'intake.json')
            with open(p, 'w') as fh:
                json.dump(d, fh)
            return subprocess.run([sys.executable, '-m', 'arkitect.harness.intake', p] + list(flags),
                                  cwd=ROOT, capture_output=True, text=True)

    def test_valid_and_fitting_is_0(self):
        r = self.run_on(example())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('RELIEF STATED', r.stdout)

    def test_invalid_is_1_with_every_problem(self):
        r = self.run_on(example(slug='Bad Slug', jurisdiction='x'))
        self.assertEqual(r.returncode, 1)
        self.assertIn('slug', r.stdout)
        self.assertIn('jurisdiction', r.stdout)

    def test_a_program_that_does_not_fit_is_2_and_names_the_rules(self):
        r = self.run_on(example(relief={}), '--json')
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)['unmet'], ['lot_width'])


if __name__ == '__main__':
    unittest.main()

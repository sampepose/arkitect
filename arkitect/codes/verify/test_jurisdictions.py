"""The jurisdiction contract, held to every jurisdiction encoded -- and proved by a second one.

Every package `arkitect jurisdiction list` finds must meet arkitect/codes/jurisdiction.py's
contract and answer a sample lot. Then a scratch copy of the engine is given a second city
with `arkitect jurisdiction new`, and an address there goes from intake to a scaffolded project
that passes the gate, printing that city's words and not Columbus's -- the proof that nothing
on the way assumes the reference jurisdiction.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path: sys.path.insert(0, HERE)
from arkitect.codes import jurisdiction
from arkitect.harness import intake
from arkitect.harness import jurisdiction as tool


class ContractTests(unittest.TestCase):

    def test_there_is_a_reference_jurisdiction(self):
        self.assertIn('columbus', jurisdiction.available())

    def test_every_jurisdiction_meets_the_contract(self):
        for name in jurisdiction.available():
            with self.subTest(name):
                bad, rows = tool.check(name)
                self.assertEqual(bad, [])
                self.assertTrue(rows)

    def test_a_jurisdiction_rephrases_only_questions_the_intake_asks(self):
        paths = {p for p, _q, _w in intake.QUESTIONS}
        for name in jurisdiction.available():
            with self.subTest(name):
                self.assertLessEqual(set(jurisdiction.load(name).QUESTION_TEXT), paths)

    def test_the_generic_questions_name_no_place(self):
        for path, q, why in intake.QUESTIONS:
            for word in ('Columbus', 'Franklin', 'Auditor', 'C.C.', 'Ohio'):
                self.assertNotIn(word, q + why, path)

    def test_an_unknown_jurisdiction_is_a_sentence_not_a_crash(self):
        with self.assertRaises(LookupError):
            jurisdiction.load('atlantis')
        with open(os.path.join(HERE, 'projects', 'example_100', 'intake.json')) as fh:
            d = json.load(fh)
        d['jurisdiction'] = 'atlantis'
        self.assertTrue(any('atlantis' in p for p in intake.validate(d)))


@unittest.skipUnless(shutil.which('git'), 'needs git')
class SecondJurisdictionTests(unittest.TestCase):
    """Dayton, in a scratch copy of the engine: a skeleton, refused until verified, then an
       address that scaffolds and passes the gate in Dayton's words."""

    @classmethod
    def setUpClass(cls):
        cls.t = tempfile.mkdtemp(prefix='jurisdiction-')
        cls.engine = os.path.join(cls.t, 'arkitect')
        shutil.copytree(HERE, cls.engine, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '.verify-cache', '*.egg-info', 'build', '*.pdf', '*.dxf'))
        cls.env = dict(os.environ, PYTHONPATH=cls.engine, HOME=os.path.join(cls.t, 'home'),
                       GIT_AUTHOR_NAME='j', GIT_AUTHOR_EMAIL='j@example.com',
                       GIT_COMMITTER_NAME='j', GIT_COMMITTER_EMAIL='j@example.com')
        cls.env.pop('ARKITECT_WORKSPACE', None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.t, True)

    def run_(self, *args, cwd=None):
        return subprocess.run([sys.executable, '-m', 'arkitect.harness.cli'] + list(args),
                              cwd=cwd or self.engine, capture_output=True, text=True, env=self.env,
                              timeout=600)

    def test_a_second_city_from_skeleton_to_a_project_that_passes(self):
        r = self.run_('jurisdiction', 'new', 'dayton', '--name', 'Dayton, Ohio', '--state', 'arkitect.codes.ohio')
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_('jurisdiction', 'check', 'dayton')
        self.assertEqual(r.returncode, 1, r.stdout)                     # a skeleton is not verified
        self.assertIn('has not been verified', r.stdout)

        init = os.path.join(self.engine, 'arkitect', 'codes', 'dayton', '__init__.py')
        with open(init) as fh:
            text = fh.read()
        text = (text.replace('VERIFIED_ON = None', "VERIFIED_ON = '2026-09-23'")
                    .replace('VERIFIED_AGAINST = None', "VERIFIED_AGAINST = 'a test'")
                    .replace("PARCEL_LABEL = 'PARCEL'", "PARCEL_LABEL = 'MONTGOMERY COUNTY PARCEL'")
                    .replace("REVIEWER = 'TO BE ENCODED: who reviews a residential set here'",
                             "REVIEWER = 'City of Dayton residential plan reviewer'"))
        with open(init, 'w') as fh:
            fh.write(text)
        r = self.run_('jurisdiction', 'check', 'dayton')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        ws = os.path.join(self.t, 'ws')
        os.makedirs(os.path.join(ws, 'projects', 'maple_9'))
        open(os.path.join(ws, 'projects', '__init__.py'), 'w').close()
        with open(os.path.join(HERE, 'projects', 'example_100', 'intake.json')) as fh:
            d = json.load(fh)
        d.update(slug='maple_9', address='9 MAPLE ST', city_line='DAYTON, OHIO 45400',
                 jurisdiction='dayton', relief={}, owner=['MAPLE OWNER LLC', 'DAYTON, OH 45400'])
        with open(os.path.join(ws, 'projects', 'maple_9', 'intake.json'), 'w') as fh:
            json.dump(d, fh, indent=1)
        subprocess.run(['git', 'init', '-q'], cwd=ws, check=True)
        r = self.run_('intake', 'projects/maple_9/intake.json', cwd=ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)          # every rule NOT CHECKED
        r = self.run_('scaffold', 'projects/maple_9/intake.json', cwd=ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.run_('gate', cwd=ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        with open(os.path.join(ws, 'projects', 'maple_9', 'build.py')) as fh:
            build = fh.read()
        self.assertIn('from arkitect.codes.dayton import fit', build)
        self.assertNotIn('columbus', build)
        code = ('import sys; sys.path[:0] = [%r, %r]; from src import project; print(project.TITLEBLOCK)'
                % (os.path.join(ws, 'projects', 'maple_9'), ws))
        r = subprocess.run([sys.executable, '-c', code], cwd=ws, capture_output=True, text=True, env=self.env)
        self.assertIn('MONTGOMERY COUNTY PARCEL TBD', r.stdout, r.stderr)
        self.assertIn('ZONING: DAYTON', r.stdout)
        self.assertIn('NO SEAL REQUIRED', r.stdout)                    # Ohio's, carried by its state
        self.assertNotIn('COLUMBUS', r.stdout)
        self.assertNotIn('FRANKLIN', r.stdout)


if __name__ == '__main__':
    unittest.main()

"""arkitect/harness/scaffold.py and arkitect/harness/progress.py, end to end, on a throwaway repository: the
shared layers and no project, then a synthetic address scaffolded into it.

A scaffold is only worth having if what it writes passes every oracle on its first day, a
second address copies nothing from the first, and the feature list cannot claim what the
build does not do. Each is tested here by running the real commands.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from arkitect.harness.verify.fixtures import example

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _git(root, *args):
    r = subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t'] + list(args),
                       cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


class ScaffoldTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = root = os.path.join(cls._tmp.name, 'repo')
        skip = shutil.ignore_patterns('__pycache__', '.DS_Store')
        shutil.copytree(os.path.join(HERE, 'arkitect'), os.path.join(root, 'arkitect'), ignore=skip)
        os.makedirs(os.path.join(root, 'projects'))
        shutil.copy(os.path.join(HERE, 'projects', '__init__.py'), os.path.join(root, 'projects'))
        shutil.copy(os.path.join(HERE, '.gitignore'), root)
        _git(root, 'init', '-q')
        _git(root, 'add', '-A')
        _git(root, 'commit', '-q', '-m', 'base')
        cls.scaffold_out = cls.scaffold(example())
        _git(root, 'add', '-A')
        _git(root, 'commit', '-q', '-m', 'scaffold')

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    @classmethod
    def run_(cls, *args):
        return subprocess.run([sys.executable] + list(args), cwd=cls.root, capture_output=True,
                              text=True, timeout=600)

    @classmethod
    def scaffold(cls, d):
        proj = os.path.join(cls.root, 'projects', d['slug'])
        os.makedirs(proj, exist_ok=True)
        with open(os.path.join(proj, 'intake.json'), 'w') as fh:
            json.dump(d, fh)
        return cls.run_('-m', 'arkitect.harness.scaffold', os.path.join('projects', d['slug'], 'intake.json'))

    def tearDown(self):
        _git(self.root, 'checkout', '-q', '--', '.')
        _git(self.root, 'clean', '-qfd', '--', 'projects')

    # ------------------------------------------------------------ day one passes

    def test_the_scaffold_passes_the_gate_on_its_first_day(self):
        self.assertEqual(self.scaffold_out.returncode, 0, self.scaffold_out.stderr)
        r = self.run_('arkitect/lib/verify/gate.py', '--json')
        rep = json.loads(r.stdout)
        self.assertTrue(rep['ok'], rep['failures'] + rep['errors'])
        p = rep['projects']['example_100']
        self.assertEqual(p['progress']['next'], 'G-001')
        self.assertEqual(p['progress']['counts'], {'passes': 0, 'drawn': 2, 'pending': 22})

    def test_its_own_tests_pass(self):
        r = self.run_('-m', 'unittest', 'projects.example_100.verify.test_project')
        self.assertEqual(r.returncode, 0, r.stderr[-1500:])

    def test_it_is_wired_into_the_suite_and_the_deliverables(self):
        with open(os.path.join(self.root, 'projects', 'example_100', 'verify', 'FLOOR')) as fh:
            self.assertEqual(fh.read(), '5\n')
        for n in ('100-Example-permit-set.pdf', '100-Example-zoning-site-plan.pdf',
                  '100-Example-floor-plans.dxf'):
            r = subprocess.run(['git', 'check-ignore', '-q', 'projects/example_100/' + n],
                               cwd=self.root)
            self.assertEqual(r.returncode, 1, n + ' is ignored; a deliverable is tracked')
        r = subprocess.run(['git', 'check-ignore', '-q', 'projects/example_100/scratch.pdf'],
                           cwd=self.root)
        self.assertEqual(r.returncode, 0, 'a scratch PDF is not ignored')

    def test_a_second_address_copies_nothing_from_the_first(self):
        d = example(slug='example_200', address='200 EXAMPLE ST')
        r = self.scaffold(d)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_('arkitect/lib/verify/twins.py')
        self.assertIn('TOTAL 0', r.stdout)

    # ------------------------------------------------------------ claims are proved

    def test_set_accepts_a_proved_claim_and_refuses_an_unproved_one(self):
        r = self.run_('-m', 'arkitect.harness.progress', 'set', 'example_100', 'G-001', 'passes')
        self.assertEqual(r.returncode, 0, r.stderr)                 # arkitect.codes.ohio.columbus.fit ran
        r = self.run_('-m', 'arkitect.harness.progress', 'set', 'example_100', 'A-101', 'drawn')
        self.assertEqual(r.returncode, 1)
        self.assertIn('does not bind', r.stderr)

    def test_a_hand_written_false_claim_fails_verify_and_the_gate(self):
        path = os.path.join(self.root, 'projects', 'example_100', 'progress.json')
        with open(path) as fh:
            data = json.load(fh)
        for f in data['features']:
            if f['id'] == 'C-102':
                f['status'] = 'passes'               # its guard ran: a true claim
            if f['id'] == 'S-102':
                f['status'] = 'passes'               # never drawn: false
        with open(path, 'w') as fh:
            json.dump(data, fh)
        r = self.run_('-m', 'arkitect.harness.progress', 'verify', 'example_100')
        self.assertEqual(r.returncode, 1)
        self.assertIn('S-102 is claimed passes', r.stdout)
        self.assertNotIn('C-102 is claimed', r.stdout)
        rep = json.loads(self.run_('arkitect/lib/verify/gate.py', '--json').stdout)
        self.assertFalse(rep['ok'])
        self.assertTrue(any('claims what the build does not prove' in f for f in rep['failures']))

    def test_add_and_drop_shape_the_list_and_keep_the_reason(self):
        r = self.run_('-m', 'arkitect.harness.progress', 'add', 'example_100', 'A-604', 'STAIR DETAILS',
                      '--after', 'A-602', '--guard', 'arkitect.codes.ohio.rco.site_steps')
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_('-m', 'arkitect.harness.progress', 'add', 'example_100', 'A-605', 'X',
                      '--guard', 'arkitect.codes.no_such_rule')
        self.assertEqual(r.returncode, 1)                           # a guard that can never run
        r = self.run_('-m', 'arkitect.harness.progress', 'drop', 'example_100', 'A-301')
        self.assertEqual(r.returncode, 1)                           # no reason given
        r = self.run_('-m', 'arkitect.harness.progress', 'drop', 'example_100', 'A-301',
                      '--note', 'one storey, no section needed')
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.root, 'projects', 'example_100', 'progress.json')) as fh:
            data = json.load(fh)
        ids = [f['id'] for f in data['features']]
        self.assertEqual(ids[ids.index('A-602')+1], 'A-604')
        self.assertNotIn('A-301', ids)
        self.assertEqual(data['dropped'][0]['why'], 'one storey, no section needed')

    # ------------------------------------------------------------ what it refuses

    def test_it_refuses_a_project_that_exists(self):
        r = self.scaffold(example())
        self.assertEqual(r.returncode, 1)
        self.assertIn('already has a build.py', r.stderr)

    def test_it_refuses_a_program_that_does_not_fit(self):
        r = self.scaffold(example(slug='example_300', relief={}))
        self.assertEqual(r.returncode, 1)
        self.assertIn('does not fit: lot_width', r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.root, 'projects', 'example_300', 'build.py')))

    def test_it_refuses_an_intake_outside_its_project(self):
        path = os.path.join(self.root, 'intake.json')
        with open(path, 'w') as fh:
            json.dump(example(slug='example_400'), fh)
        try:
            r = self.run_('-m', 'arkitect.harness.scaffold', 'intake.json')
        finally:
            os.remove(path)
        self.assertEqual(r.returncode, 1)
        self.assertIn('projects/example_400/intake.json', r.stderr)


if __name__ == '__main__':
    unittest.main()

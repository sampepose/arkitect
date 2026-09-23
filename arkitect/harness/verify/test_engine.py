"""arkitect/harness/engine.py says which engine a Python finds; arkitect/harness/cli.py is the
one command."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from arkitect import __version__
from arkitect.harness import cli, engine
from arkitect.lib import workspace


class EngineTests(unittest.TestCase):

    def setUp(self):
        self.site = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.site, True)

    def test_unlink_takes_away_the_old_link(self):
        with open(engine.pth_path(self.site), 'w') as fh:
            fh.write(workspace.ENGINE + '\n')
        self.assertEqual(engine.linked(self.site), workspace.ENGINE)
        engine.unlink(self.site)
        self.assertIsNone(engine.linked(self.site))


class CliTests(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp()                    # a user who has not seen the notice
        self.addCleanup(shutil.rmtree, self.home, True)

    def run_(self, *args):
        env = dict(os.environ, PYTHONPATH=workspace.ENGINE, HOME=self.home)
        return subprocess.run([sys.executable, '-m', 'arkitect.harness.cli'] + list(args),
                              cwd=workspace.ENGINE, capture_output=True, text=True, env=env)

    def test_version(self):
        r = self.run_('--version')
        self.assertEqual((r.returncode, r.stdout.strip()), (0, 'arkitect ' + __version__))

    def test_every_tool_is_a_module_that_exists(self):
        import importlib.util
        for name, module in cli.TOOLS.items():
            with self.subTest(name):
                self.assertIsNotNone(importlib.util.find_spec(module), module)

    def test_a_tool_runs_with_its_own_arguments_and_exit_status(self):
        r = self.run_('decisions', 'pending')
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_('hook', 'nope')
        self.assertEqual(r.returncode, 2)

    def test_the_disclaimer_is_shown_once_on_stderr_and_never_in_json(self):
        from arkitect.harness import disclaimer
        first = self.run_('decisions', 'pending', '--json')
        self.assertIn('not the work of a licensed architect', first.stderr)
        self.assertNotIn('licensed', first.stdout)
        import json
        json.loads(first.stdout)                           # stdout is still only the object
        again = self.run_('decisions', 'pending', '--json')
        self.assertNotIn('licensed', again.stderr)
        self.assertTrue(os.path.exists(disclaimer.record_path(self.home)))

    def test_the_disclaimer_on_request(self):
        r = self.run_('disclaimer')
        self.assertEqual(r.returncode, 0)
        self.assertIn('not thereby code-compliant', r.stdout)

    def test_an_unknown_tool_is_an_error(self):
        self.assertEqual(self.run_('nope').returncode, 2)


if __name__ == '__main__':
    unittest.main()

"""arkitect/lib/workspace.py: the engine and the projects in two directories, and the gate measuring
a projects repository from outside it."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if HERE not in sys.path: sys.path.insert(0, HERE)
from arkitect.lib import workspace


class FindTests(unittest.TestCase):

    def setUp(self):
        self.t = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.t, True)

    def test_the_environment_wins(self):
        self.assertEqual(workspace.find(self.t, {workspace.ENV: self.t}), os.path.abspath(self.t))

    def test_the_nearest_directory_holding_projects(self):
        deep = os.path.join(self.t, 'projects', 'oak_42', 'src')
        os.makedirs(deep)
        self.assertEqual(workspace.find(deep, {}), self.t)

    def test_nothing_above_means_the_engine(self):
        self.assertEqual(workspace.find(self.t, {}), workspace.ENGINE)

    def test_separate(self):
        self.assertFalse(workspace.separate(workspace.ENGINE))
        self.assertTrue(workspace.separate(self.t))

    def test_env_leaves_the_workspace_to_the_cwd_and_puts_the_engine_first(self):
        e = workspace.env(self.t, base={workspace.ENV: '/elsewhere',
                                        'PYTHONPATH': os.pathsep.join(['/x', workspace.ENGINE])})
        self.assertNotIn(workspace.ENV, e)
        self.assertEqual(e['PYTHONPATH'].split(os.pathsep), [workspace.ENGINE, '/x'])

    def test_setting_reads_the_workspace_toml(self):
        self.assertEqual(workspace.setting('verify', 'twins_ceiling', 0, self.t), 0)
        with open(os.path.join(self.t, 'arkitect.toml'), 'w') as fh:
            fh.write('[verify]\ntwins_ceiling = 12\n')
        self.assertEqual(workspace.setting('verify', 'twins_ceiling', 0, self.t), 12)


def _git(cwd, *args):
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false']
                   + list(args), cwd=cwd, check=True, capture_output=True)


class SeparateGateTests(unittest.TestCase):
    """A projects repository holding one copy of an example, measured by this engine's gate."""

    @classmethod
    def setUpClass(cls):
        cls.t = tempfile.mkdtemp(prefix='ws-')
        cls.ws = os.path.join(cls.t, 'projects-repo')
        os.makedirs(os.path.join(cls.ws, 'projects'))
        shutil.copyfile(os.path.join(HERE, 'projects', '__init__.py'),
                        os.path.join(cls.ws, 'projects', '__init__.py'))
        shutil.copytree(os.path.join(HERE, 'projects', 'example_100'),
                        os.path.join(cls.ws, 'projects', 'oak_42'),
                        ignore=shutil.ignore_patterns('__pycache__', '*.pdf', '*.dxf'))
        os.makedirs(os.path.join(cls.ws, 'decisions'))
        os.makedirs(os.path.join(cls.ws, '.claude'))            # what hooks install commits there
        os.symlink(os.path.join(workspace.ENGINE, '.claude', 'skills'),
                   os.path.join(cls.ws, '.claude', 'skills'))
        with open(os.path.join(cls.ws, '.gitignore'), 'w') as fh:
            fh.write('.verify-cache/\n__pycache__/\n*.pdf\n*.dxf\n')
        _git(cls.ws, 'init', '-q')
        _git(cls.ws, 'add', '.gitignore', 'projects', 'decisions', '.claude/skills')
        _git(cls.ws, 'commit', '-qm', 'one project')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.t, True)

    def _gate(self, *args):
        env = dict(os.environ)
        env.pop(workspace.ENV, None)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'arkitect', 'lib', 'verify', 'gate.py'), '--json']
                           + list(args), cwd=self.ws, capture_output=True, text=True, env=env,
                           timeout=600)
        return r.returncode, json.loads(r.stdout), r.stderr

    def test_the_gate_measures_the_workspace_it_is_run_in(self):
        code, rep, err = self._gate()
        self.assertEqual(list(rep['projects']), ['oak_42'], err)
        self.assertEqual(code, 0, rep['failures'] + rep['errors'])
        self.assertEqual(rep['projects']['oak_42']['sheets_moved'], [])     # the base built
        self.assertTrue(os.path.isdir(os.path.join(self.ws, '.verify-cache')))

    def test_an_engine_base_needs_a_separate_workspace_and_is_measured(self):
        code, rep, _err = self._gate('--engine-base', 'HEAD', '--expect-unchanged')
        self.assertEqual(code, 0, rep['failures'] + rep['errors'])
        self.assertIn('engine HEAD', rep['base'])

    def test_the_hooks_it_installs_name_the_engine_by_path(self):
        env = dict(os.environ, **{workspace.ENV: self.ws})
        r = subprocess.run([sys.executable, '-m', 'arkitect.harness.hooks', 'install'], cwd=HERE, env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.ws, '.claude', 'settings.json')) as fh:
            cmds = [h['command'] for gs in json.load(fh)['hooks'].values()
                    for g in gs for h in g['hooks']]
        self.assertEqual(len(cmds), 4)
        for c in cmds:
            self.assertRegex(c, r'^python3 -m arkitect\.harness\.hook [a-z_]+$')     # names no path
            self.assertNotIn(workspace.ENGINE, c)
        for rel in ('skills', 'agents'):
            self.assertEqual(os.path.realpath(os.path.join(self.ws, '.claude', rel)),
                             os.path.realpath(os.path.join(workspace.ENGINE, '.claude', rel)))


class HookRunnerTests(unittest.TestCase):

    def test_a_hook_runs_by_name_through_the_import_path(self):
        env = dict(os.environ, PYTHONPATH=workspace.ENGINE)
        r = subprocess.run([sys.executable, '-m', 'arkitect.harness.hook', 'guard_bash'], cwd=tempfile.gettempdir(),
                           input=json.dumps({'tool_input': {'command': 'git add -A'}}),
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2, r.stderr)                    # refused, as by path
        self.assertIn('git add -A', r.stderr)

    def test_an_unknown_hook_is_an_error(self):
        env = dict(os.environ, PYTHONPATH=workspace.ENGINE)
        r = subprocess.run([sys.executable, '-m', 'arkitect.harness.hook', 'nope'], capture_output=True,
                           text=True, env=env, cwd=tempfile.gettempdir())
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()

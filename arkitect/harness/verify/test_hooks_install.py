"""arkitect/harness/hooks.py: installing merges, a second install changes nothing, uninstall keeps
every setting that is not the template's."""
import json
import os
import shutil
import tempfile
import unittest

from arkitect.harness import hooks

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class HooksInstallTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        os.makedirs(os.path.join(self.root, '.claude', 'hooks'))
        shutil.copy(os.path.join(HERE, hooks.TEMPLATE), os.path.join(self.root, hooks.TEMPLATE))

    def tearDown(self):
        self._tmp.cleanup()

    def settings(self):
        with open(os.path.join(self.root, hooks.SETTINGS)) as fh:
            return json.load(fh)

    def test_nothing_is_wired_until_installed(self):
        self.assertEqual(hooks.status(self.root), 'not installed')

    def test_install_is_idempotent_and_keeps_other_settings(self):
        mine = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'echo mine'}]}
        with open(os.path.join(self.root, hooks.SETTINGS), 'w') as fh:
            json.dump({'model': 'x', 'hooks': {'PreToolUse': [mine]}}, fh)
        hooks.install(self.root)
        once = self.settings()
        hooks.install(self.root)
        self.assertEqual(self.settings(), once)
        self.assertEqual(hooks.status(self.root), 'installed')
        self.assertEqual(once['model'], 'x')
        self.assertIn(mine, once['hooks']['PreToolUse'])
        hooks.uninstall(self.root)
        self.assertEqual(self.settings(), {'model': 'x', 'hooks': {'PreToolUse': [mine]}})
        self.assertEqual(hooks.status(self.root), 'not installed')

    def test_a_changed_template_reads_out_of_date(self):
        hooks.install(self.root)
        cfg = self.settings()
        cfg['hooks']['Stop'][0]['hooks'][0]['timeout'] = 1
        with open(os.path.join(self.root, hooks.SETTINGS), 'w') as fh:
            json.dump(cfg, fh)
        self.assertEqual(hooks.status(self.root), 'out of date')


if __name__ == '__main__':
    unittest.main()

"""harness/release.py on a scratch repository: what is withheld, what ships, what the public
overlay replaces, and that the snapshot is a fresh repository of one commit. (Running the
whole suite inside a snapshot is `python3 -m harness.release check`; it is not run from here,
where it would test a snapshot of a snapshot.)"""
import os
import subprocess
import tempfile
import unittest

from harness import release as REL


def _git(root, *args):
    return subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t'] + list(args),
                          cwd=root, capture_output=True, text=True, check=True).stdout


class ReleaseTests(unittest.TestCase):

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = os.path.join(t.name, 'repo')
        self.out = os.path.join(t.name, 'public')
        files = {
            'lib/a.py': 'engine\n',
            'projects/mine_1/build.py': 'private\n',
            'projects/example_1/build.py': 'public\n',
            'decisions/D-001.md': 'private record\n',
            'README.md': 'the private readme\n',
            'release/private.txt': '# comment\nprojects/mine_1/\ndecisions/D-*.md\nREADME.md\n',
            'release/public/README.md': 'the public readme\n',
            'release/public/decisions/README.md': 'empty ledger\n',
        }
        for p, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(self.root, p)), exist_ok=True)
            with open(os.path.join(self.root, p), 'w') as fh:
                fh.write(text)
        _git(self.root, 'init', '-q')
        _git(self.root, 'add', '-A')
        _git(self.root, 'commit', '-q', '-m', 'private history')

    def test_the_split(self):
        ship, hold = REL.split(self.root)
        self.assertEqual(sorted(ship), ['lib/a.py', 'projects/example_1/build.py'])
        self.assertIn('projects/mine_1/build.py', hold)
        self.assertIn('decisions/D-001.md', hold)
        self.assertIn('release/private.txt', hold)          # release/ never ships

    def test_a_directory_pattern_is_a_prefix_not_a_substring(self):
        pats = ['projects/mine_1/']
        self.assertTrue(REL.is_private('projects/mine_1/x.py', pats))
        self.assertFalse(REL.is_private('projects/mine_10/x.py', pats))

    def test_the_snapshot_is_the_engine_the_overlay_and_one_fresh_commit(self):
        written = REL.snapshot(self.out, self.root)
        self.assertEqual(written, ['README.md', 'decisions/README.md', 'lib/a.py',
                                   'projects/example_1/build.py'])
        with open(os.path.join(self.out, 'README.md')) as fh:
            self.assertEqual(fh.read(), 'the public readme\n')
        self.assertFalse(os.path.exists(os.path.join(self.out, 'projects', 'mine_1')))
        log = _git(self.out, 'log', '--oneline')
        self.assertEqual(len(log.splitlines()), 1)             # none of the private history
        self.assertNotIn('private history', log)

    def test_the_snapshot_refuses_an_existing_directory(self):
        os.makedirs(self.out)
        with self.assertRaises(ValueError):
            REL.snapshot(self.out, self.root)

    def test_names_are_the_private_projects(self):
        self.assertEqual(REL.names(self.root), ['mine_1'])


if __name__ == '__main__':
    unittest.main()

"""arkitect/harness/release.py on scratch repositories: an engine with one commit, and a workspace
beside it whose arkitect.toml names the private words. A word in a tracked file fails, a word in
a commit message fails, a word only in the author's name passes. (The gate half of `check` is
`arkitect gate --full`, which the suite is already inside; these run with run_gate=False.)"""
import os
import subprocess
import tempfile
import unittest

from arkitect.harness import release as REL
from arkitect.lib import workspace

WORD = 'Zorblat'


def _git(root, *args, name='t', email='t@t'):
    # The identity goes in the environment, which outranks both -c user.* and CI's own
    # GIT_AUTHOR_* variables: the author test must commit as WORD everywhere it runs.
    env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email,
               GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email)
    return subprocess.run(['git', '-c', 'commit.gpgsign=false'] + list(args), cwd=root, env=env,
                          capture_output=True, text=True, check=True).stdout


def _write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as fh:
        fh.write(text)


class ReleaseTests(unittest.TestCase):

    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.engine = os.path.join(t.name, 'engine')
        self.ws = os.path.join(t.name, 'workspace')
        _write(self.engine, 'arkitect/lib/a.py', 'engine\n')
        _write(self.engine, 'README.md', 'a public readme\n')
        _git(self.engine, 'init', '-q')
        _git(self.engine, 'add', 'arkitect/lib/a.py', 'README.md')
        _git(self.engine, 'commit', '-q', '-m', 'the first commit')
        _write(self.ws, 'arkitect.toml', '[identity]\nprivate_words = ["%s"]\n' % WORD)
        _write(self.ws, 'projects/secret_9/src/__init__.py', '')

    def check(self):
        return REL.check(root=self.engine, ws=self.ws, run_gate=False)

    def commit(self, rel, text, message, **who):
        _write(self.engine, rel, text)
        _git(self.engine, 'add', rel)
        _git(self.engine, 'commit', '-q', '-m', message, **who)

    def test_a_clean_engine_is_ready(self):
        status, lines = self.check()
        self.assertEqual(status, 0, '\n'.join(lines))

    def test_the_words_are_the_workspaces_and_its_project_slugs(self):
        self.assertEqual(REL.words(self.ws), [WORD, 'secret_9'])

    def test_the_engine_as_its_own_workspace_has_no_words(self):
        self.assertEqual(REL.words(workspace.ENGINE), [])

    def test_a_private_word_in_a_file_fails(self):
        self.commit('docs/x.md', 'one\nmade for %s\n' % WORD, 'docs')
        status, lines = self.check()
        self.assertEqual(status, 1)
        self.assertIn('  docs/x.md:2: %s' % WORD, lines)

    def test_a_project_slug_in_a_file_fails(self):
        self.commit('docs/x.md', 'see projects/secret_9\n', 'docs')
        self.assertEqual(REL.file_hits(self.engine, REL.words(self.ws)), ['docs/x.md:1: secret_9'])

    def test_a_word_is_matched_whole(self):
        self.commit('docs/x.md', '%sian\n' % WORD, 'docs')
        self.assertEqual(self.check()[0], 0)

    def test_a_private_word_in_a_commit_message_fails(self):
        self.commit('docs/x.md', 'clean\n', 'docs\n\nas %s asked' % WORD)
        status, lines = self.check()
        self.assertEqual(status, 1)
        h = _git(self.engine, 'rev-parse', '--short=10', 'HEAD').strip()
        self.assertIn('  %s docs: %s' % (h, WORD), lines)

    def test_a_private_word_in_the_author_or_committer_passes(self):
        self.commit('docs/x.md', 'clean\n', 'docs', name=WORD, email='%s@example.com' % WORD)
        self.assertEqual(_git(self.engine, 'log', '-1', '--format=%an %ae %cn'),
                         '%s %s@example.com %s\n' % (WORD, WORD, WORD))
        status, lines = self.check()
        self.assertEqual(status, 0, '\n'.join(lines))

    def test_an_untracked_file_is_not_scanned(self):
        _write(self.engine, 'scratch.txt', WORD)
        self.assertEqual(self.check()[0], 0)

    def test_not_a_repository(self):
        self.assertEqual(REL.check(root=self.ws, ws=self.ws, run_gate=False)[0], 2)


if __name__ == '__main__':
    unittest.main()

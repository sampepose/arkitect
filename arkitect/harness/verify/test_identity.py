"""Nothing the engine tracks names the people, companies, numbers or projects of the
installation that built it: every word of the workspace's arkitect.toml [identity]
private_words, and every private project's slug, is absent from every file `git ls-files`
lists in the engine (arkitect/harness/release.py, whose `check` also scans the commit
messages).

A private workspace lists its words in its own arkitect.toml, which is never in the engine;
the engine's own arkitect.toml lists none, so run inside the engine this test has nothing to
find. Run it inside your workspace.
"""
import unittest

from arkitect.harness import release
from arkitect.lib import workspace


class IdentityTests(unittest.TestCase):

    def test_nothing_shipped_names_the_installation(self):
        ws = release.words()
        if not ws:
            self.skipTest('no private words configured')
        found = release.file_hits(workspace.ENGINE, ws)
        self.assertEqual(found, [], '\n' + '\n'.join(found[:40]))


if __name__ == '__main__':
    unittest.main()

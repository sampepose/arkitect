"""Nothing that ships names the people, companies, numbers or projects of the installation
that built it: every word of harness/config.py's [identity] private_words, and every private
project's slug, is absent from every file the public snapshot gets (harness/release.py).

A private installation lists its words in its own arkitect.toml, which never ships; a
public checkout lists none, so there this test has nothing to find.
"""
import os
import re
import unittest

from harness import config, release

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def shipped_text(root=HERE):
    """(relative path, text) for every shipped file that reads as text."""
    ship, _hold = release.split(root)
    pub = os.path.join(root, release.PUBLIC)
    for d, _dirs, files in os.walk(pub):
        ship += [os.path.relpath(os.path.join(d, f), root) for f in files]
    for rel in ship:
        try:
            with open(os.path.join(root, rel), errors='strict') as fh:
                yield rel, fh.read()
        except (UnicodeDecodeError, OSError):
            continue


class IdentityTests(unittest.TestCase):

    def test_nothing_shipped_names_the_installation(self):
        words = list(config.get('identity.private_words', root=HERE)) + release.names(HERE)
        if not words:
            self.skipTest('no private words configured')
        pat = re.compile(r'\b(%s)\b' % '|'.join(re.escape(w) for w in words))
        found = []
        for rel, text in shipped_text():
            for n, line in enumerate(text.splitlines(), 1):
                m = pat.search(line)
                if m:
                    found.append('%s:%d: %s' % (rel, n, m.group(1)))
        self.assertEqual(found, [], '\n' + '\n'.join(found[:40]))


if __name__ == '__main__':
    unittest.main()

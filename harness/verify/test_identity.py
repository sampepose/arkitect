"""Nothing that ships names the people, companies, numbers or projects of the installation
that built it: every word of harness/config.py's [identity] private_words, and every private
project's slug, is absent from every file the public snapshot gets (harness/release.py).

A private installation lists its words in its own arkitect.toml, which never ships; a
public checkout lists none, so there this test has nothing to find.
"""
import os
import re
import subprocess
import unittest

from harness import config, release
from lib import workspace

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _engine_files(root):
    r = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, check=True)
    return [p for p in r.stdout.decode().split('\0') if p]


def shipped_text(root=HERE):
    """(relative path, text) for every shipped file that reads as text: with the projects in
       a repository of their own (lib/workspace.py), every file the engine tracks; in one
       repository holding both, what harness/release.py's snapshot would get."""
    if workspace.separate():
        ship = _engine_files(root)
    else:
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


def words():
    """The workspace's private words (its arkitect.toml, which never ships) and its private
       projects' slugs: every project the workspace holds when it is separate, else the ones
       release/private.txt withholds."""
    ws = workspace.WORKSPACE
    out = list(config.get('identity.private_words', root=ws))
    if workspace.separate():
        base = os.path.join(ws, 'projects')
        out += sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d, 'src')))
    else:
        out += release.names(HERE)
    return out


class IdentityTests(unittest.TestCase):

    def test_nothing_shipped_names_the_installation(self):
        ws = words()
        if not ws:
            self.skipTest('no private words configured')
        pat = re.compile(r'\b(%s)\b' % '|'.join(re.escape(w) for w in ws))
        found = []
        for rel, text in shipped_text():
            for n, line in enumerate(text.splitlines(), 1):
                m = pat.search(line)
                if m:
                    found.append('%s:%d: %s' % (rel, n, m.group(1)))
        self.assertEqual(found, [], '\n' + '\n'.join(found[:40]))


if __name__ == '__main__':
    unittest.main()

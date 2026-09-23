"""This project's drawing, pinned to a digest committed beside it.

The trace is otherwise a run-versus-run comparison inside one session: it cannot see a
change made by a previous session, and with two projects it cannot see damage done from
the other side of the repository. That is the entire risk of a shared layer -- a change
made for one project silently altering the other's drawing.

When this fails, do not update the digest to make it pass. Run the trace, diff it
against the previous one, find out which sheets moved and whether you meant them to.
THEN update the digest, in the same commit, and say in the message which sheets moved.
"""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from arkitect.lib import workspace                                    # noqa: E402  the engine, wherever it is
TRACE = os.path.join(workspace.ENGINE, 'arkitect', 'lib', 'verify', 'trace.py')
BUILD = os.path.join(PROJ, 'build.py')
DIGEST = os.path.join(PROJ, 'trace.md5')


class TraceDigestTests(unittest.TestCase):

    def test_the_drawing_matches_the_committed_digest(self):
        self.assertTrue(os.path.exists(DIGEST), 'no trace.md5 committed for this project')
        want = open(DIGEST).read().split()[0]
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, 'trace.txt')
            r = subprocess.run([sys.executable, TRACE, dest, BUILD],
                               capture_output=True, text=True, cwd=HERE)
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            got = hashlib.md5(open(dest, 'rb').read()).hexdigest()
        self.assertEqual(got, want,
                         'the drawing changed. Diff the trace, find which sheets moved, '
                         'and update trace.md5 deliberately in the same commit.')

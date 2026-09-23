"""300 S Elm's own binding order, asserted against its own cover sheet.

    python3 lib/verify/run_tests.py       # the project's test command; see that file

This was one test in lib/verify/test_trace.py, kept there because that file tests the
tracing harness. But asserting the 300 S Elm set binds in the order ITS G-001 lists is
a project fact, not a harness fact, so it moves here with the project. The three helpers
below are copied from lib/verify/test_trace.py's HarnessTestCase rather than imported --
a project test does not reach back into the engine's test directory for plumbing."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from lib import workspace                                    # noqa: E402  the engine, wherever it is
TRACE = os.path.join(workspace.ENGINE, 'lib', 'verify', 'trace.py')
BUILD = os.path.join(HERE, 'projects', 'example_300', 'build.py')


class SheetIndexTests(unittest.TestCase):

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.tmp = scratch.name

    def trace(self, dest, build):
        return subprocess.run([sys.executable, TRACE, dest, build],
                              capture_output=True, text=True, cwd=HERE)

    def read(self, path):
        """Closed explicitly: unittest runs with warnings enabled, and a screenful of
           ResourceWarning is how a real failure goes unread."""
        with open(path) as fh:
            return fh.read()

    def pages_of(self, trace_file):
        """Every PAGES record in the trace: one tuple of sheet numbers per document."""
        recs = [ln for ln in self.read(trace_file).splitlines() if ln.startswith("PAGES\t")]
        return [eval(r.split("\t", 1)[1]) for r in recs] or None

    def require_build(self):
        if not os.path.exists(BUILD):
            self.skipTest("no build.py")

    def test_the_real_set_binds_in_index_order(self):
        """Integration, and the one project-specific test here: the 300 S Elm set must
           bind in the order G-001 lists, which is what a stale page-tree edit broke, and
           the zoning sheet must stay a separate document."""
        self.require_build()
        dest = os.path.join(self.tmp, 'real.txt')
        r = self.trace(dest, BUILD)
        self.assertTrue(r.returncode == 0, r.stderr[-300:])
        if r.returncode:
            return
        bound = self.pages_of(dest)
        self.assertTrue(bound and not any('?' in d for d in bound), str(bound))
        if not bound:
            return
        # Against G-001's OWN index, not against a copy of it typed here. The copy was
        # the whole weakness of this check: it could only ever say the set binds the way
        # it bound last time, never that it binds the way the cover sheet says it does.
        # C-102 comes out because it is the second document, asserted just below.
        sys.path.insert(0, HERE)
        from src.sheets.g001 import SHEET_INDEX
        self.assertEqual(bound[0], tuple(a for a, _b in SHEET_INDEX if a != 'C-102'),
                         "%s\n  index: %s" % (bound[:1], tuple(a for a, _b in SHEET_INDEX if a != 'C-102')))
        # C-102 is the zoning site plan, its own 11 x 17 document per G-001 note 15. It is a
        # SECOND file, so it must be a second record -- if it ever merges into the set's page
        # tree the sheet has silently changed size.
        self.assertEqual(bound[1:], [('C-102',)], str(bound[1:]))


if __name__ == '__main__':
    unittest.main(verbosity=2)

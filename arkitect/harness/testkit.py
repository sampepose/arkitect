"""The tests every project needs on its first day, to IMPORT rather than copy.

The first projects each wrote their own: `verify/__init__.py`'s enter() / leave(), test_trace_digest.py,
test_sheet_text.py. A scaffolded project gets the same guard rails from here, so a fix to
one of them reaches every project, and a new project's verify/ holds nothing but its name.

    isolation(project_dir) -> (enter, leave)
        Every project's model package is named `src` and run_tests.py runs them all in one
        process, so each project's tests put their own `src` first and restore the others'
        after, so one project's tests never import another project's model.

    ProjectTests
        A mixin: set PROJ, ENTER and LEAVE on a unittest.TestCase that inherits it. It
        holds the drawing to trace.md5, the drawn text to arkitect/lib/verify/sheet_text.py's rules,
        and progress.json to what the build proves (arkitect/harness/progress.py).
"""
import hashlib
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))     # the engine


def workspace_of(proj):
    """The directory holding projects/<slug>: the engine itself, or a projects repository."""
    return os.path.dirname(os.path.dirname(os.path.abspath(proj)))


def isolation(proj):
    """(enter, leave) for one project's tests: its `src` loaded first, the others' kept.
       Its workspace comes before the engine, so `projects.<slug>` is this project's package
       and never the engine's examples."""
    stash = {}
    ours = lambda name: name == 'src' or name.startswith('src.')

    def enter():
        stash.clear()
        for k in [k for k in sys.modules if ours(k)]:
            stash[k] = sys.modules.pop(k)
        first = [proj] + [p for p in (workspace_of(proj), ROOT) if p != proj]
        first = [p for i, p in enumerate(first) if p not in first[:i]]
        for p in first:
            while p in sys.path:
                sys.path.remove(p)
        sys.path[:0] = first

    def leave():
        for k in [k for k in sys.modules if ours(k)]:
            del sys.modules[k]
        sys.modules.update(stash)
        stash.clear()
        while proj in sys.path:
            sys.path.remove(proj)
    return enter, leave


class ProjectTests:
    """Mix into a unittest.TestCase with PROJ (the project directory), ENTER and LEAVE
       (staticmethods, from isolation()). Not a TestCase itself, so discovery never runs it
       without a project."""
    PROJ = None
    ENTER = LEAVE = None
    EXCUSED_OVERLAPS = ()          # (sheet, text prefix) pairs a project names one by one

    @classmethod
    def setUpClass(cls):
        cls.ENTER()
        from arkitect.lib.verify import sheet_text
        cls.PAGES = sheet_text.recorded(os.path.join(cls.PROJ, 'build.py'))

    @classmethod
    def tearDownClass(cls):
        cls.LEAVE()

    def test_the_drawing_matches_the_committed_digest(self):
        """Do not update the digest to make this pass: `python3 arkitect/lib/verify/gate.py` names the
           sheets that moved, and `gate.py accept` writes it once they are meant to."""
        digest = os.path.join(self.PROJ, 'trace.md5')
        self.assertTrue(os.path.exists(digest), 'no trace.md5 committed for this project')
        with open(digest) as fh:
            want = fh.read().split()[0]
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, 'trace.txt')
            r = subprocess.run([sys.executable, os.path.join(ROOT, 'arkitect', 'lib', 'verify', 'trace.py'),
                                dest, os.path.join(self.PROJ, 'build.py')],
                               capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            with open(dest, 'rb') as fh:
                got = hashlib.md5(fh.read()).hexdigest()
        self.assertEqual(got, want, 'the drawing moved; see python3 arkitect/lib/verify/gate.py')

    def test_no_string_stands_on_another(self):
        from arkitect.lib.verify import sheet_text
        bad = [(no, a[:50], b[:50]) for no, items in self.PAGES.items()
               for _area, a, b in sheet_text.overlaps(items)
               if not any(no == s and (a.startswith(t) or b.startswith(t))
                          for s, t in self.EXCUSED_OVERLAPS)]
        self.assertEqual(bad, [])

    def test_every_sheet_cited_is_bound(self):
        from arkitect.lib.verify import sheet_text
        self.assertEqual(sheet_text.sheet_references(self.PAGES), [])

    def test_every_note_cited_is_printed(self):
        from arkitect.lib.verify import sheet_text
        self.assertEqual(sheet_text.note_references(self.PAGES), [])

    def test_every_progress_claim_is_proved_by_the_build(self):
        from arkitect.harness import progress
        v = progress.verify(os.path.basename(self.PROJ), workspace_of(self.PROJ))
        self.assertEqual(v['false'], [])

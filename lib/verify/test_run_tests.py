"""Tests for the test command itself.

Circular only in appearance: nothing else in the project can tell you whether the
thing that decides "did tests run" is working. Both standard runners answer that
question wrongly — `unittest discover` with a mistyped pattern prints NO TESTS RAN
and exits 0, and pytest exits 0 after deselecting everything — so this is the guard
that stops a green light meaning nothing at all.
"""
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from lib import workspace
from lib.verify import run_tests


def _write(d, name, body):
    with open(os.path.join(d, name), "w") as fh:
        fh.write(body)


PASSES = "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): pass\n"
FAILS = "import unittest\nclass T(unittest.TestCase):\n    def test_no(self): assert False\n"
BROKEN = "import a_module_that_does_not_exist_xyz\n"


class RunnerTests(unittest.TestCase):
    _n = 0

    def run_on(self, files, pattern="test_*.py"):
        """main() against a throwaway tree; returns (exit status, what it printed).

        The probe modules get a unique name per call and are dropped from sys.modules
        afterwards. Reusing `test_a` across two temp directories makes unittest find the
        first one cached and raise "module incorrectly imported"; and the directory is
        realpath'd because on macOS tempfile hands back /var/... while the import system
        reports /private/var/..., which that same check rejects."""
        RunnerTests._n += 1
        tag = "probe%d" % RunnerTests._n
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            for name, body in files.items():
                _write(d, name.replace("test_", "test_%s_" % tag, 1), body)
            out, err = io.StringIO(), io.StringIO()
            so, se = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = out, err
            try:
                code = run_tests.main(root=d, pattern=pattern, stream=out)
            finally:
                sys.stdout, sys.stderr = so, se
                for m in [k for k in sys.modules if tag in k]:
                    del sys.modules[m]
                if d in sys.path:
                    sys.path.remove(d)
            return code, out.getvalue() + err.getvalue()

    def test_zero_collected_is_a_failure(self):
        """The whole point. An empty tree must not read as a pass."""
        code, said = self.run_on({})
        self.assertEqual(code, 1, said)
        self.assertIn("no tests were collected", said)

    def test_a_mistyped_pattern_is_a_failure(self):
        """How this actually happens: the files are there, the pattern is wrong."""
        code, said = self.run_on({"test_a.py": PASSES}, pattern="tests_*.py")
        self.assertEqual(code, 1, said)

    def test_tests_that_pass_are_a_pass(self):
        code, said = self.run_on({"test_a.py": PASSES})
        self.assertEqual(code, 0, said)
        self.assertIn("collected 1 tests", said)

    def test_a_failing_test_is_a_failure(self):
        code, said = self.run_on({"test_a.py": FAILS})
        self.assertEqual(code, 1, said)

    def test_an_unimportable_module_is_a_failure(self):
        """unittest turns this into a synthetic failing test rather than a loader
           error, so it must fail through the result, not the error branch."""
        code, said = self.run_on({"test_a.py": BROKEN})
        self.assertEqual(code, 1, said)

    def test_the_real_suite_collects_something(self):
        """Guards the repository itself: if this ever reports 0, the command above is
           lying to everyone who runs it."""
        _suite, n, errors = run_tests.collect(workspace.WORKSPACE)
        self.assertEqual(errors, [])
        self.assertGreater(n, 0)

    def test_the_verdict_is_the_last_thing_on_stdout(self):
        """The runner's summary goes to stderr; the model checks print to stdout, which
           block-buffers to a pipe and flushes at exit. `run_tests.py 2>&1 | tail` used
           to end on a water heater table with FAILED scrolled away above it, and a
           pipeline's exit status is the last command's -- so a failing suite read as a
           clean one at the one place anyone reads it. The verdict must be last, and it
           must say which way it went."""
        for body, word in ((PASSES, "PASSED"), (FAILS, "FAILED")):
            with self.subTest(word):
                code, said = self.run_on({"test_a.py": body})
                self.assertEqual(code, 0 if word == "PASSED" else 1, said)
                lines = [ln for ln in said.splitlines() if ln.strip()]
                self.assertTrue(lines[-1].startswith(word),
                                "last line was %r" % (lines[-1] if lines else None))
                self.assertIn("failure(s)", lines[-1])

    def test_a_test_file_that_was_never_collected_is_a_failure(self):
        """unittest does not recurse into a directory without an __init__.py, and
           namespace-package discovery went away in 3.11. A whole folder of tests can
           be added and skipped in silence -- the same failure this file exists to
           prevent, one level up. Discovery cannot report it, so the run compares what
           it collected against the test_*.py actually on disk."""
        RunnerTests._n += 1
        tag = "probe%d" % RunnerTests._n
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            _write(d, "test_%s_seen.py" % tag, PASSES)
            sub = os.path.join(d, "newtests")
            os.makedirs(sub)
            _write(sub, "test_%s_unseen.py" % tag, FAILS)   # no __init__.py beside it
            out, err = io.StringIO(), io.StringIO()
            so, se = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = out, err
            try:
                code = run_tests.main(root=d, stream=out)
            finally:
                sys.stdout, sys.stderr = so, se
                for m in [k for k in sys.modules if tag in k]:
                    del sys.modules[m]
                if d in sys.path:
                    sys.path.remove(d)
            said = out.getvalue() + err.getvalue()
        self.assertEqual(code, 1, said)
        self.assertIn("never collected", said)
        self.assertIn("__init__.py", said)

    def test_no_root_floor_is_above_what_it_collects(self):
        """Each root's floor catches a test file going missing from THAT root, which is
           what a parallel merge does to one. It only works while it sits under the real
           count: a floor above it fails every run and gets lowered to nothing by the
           first person in a hurry. Raise a root's floor in ROOTS when you add tests to
           it, and keep this passing."""
        for root, floor in run_tests.floors().items():
            with self.subTest(root):
                _suite, n, _errors = run_tests.collect(root)
                self.assertLessEqual(floor, n,
                                     "floor %d for %s is above the %d tests that actually "
                                     "collect there" % (floor, root, n))

    def test_every_test_root_has_its_own_floor(self):
        """One floor over three roots cannot tell you which one lost its tests: a
           project could lose every test it has and the total still clear a number set
           when the engine's tests alone exceeded it."""
        self.assertTrue(hasattr(run_tests, 'ROOTS'), 'run_tests has no ROOTS')
        for root, floor in run_tests.floors().items():
            with self.subTest(root):
                self.assertTrue(os.path.isdir(root), root)
                self.assertGreater(floor, 0, 'a floor of 0 is not a floor')

    def test_the_engine_names_no_project(self):
        """A project's floor lives in the project, so the engine can ship without it."""
        self.assertFalse([r for r in run_tests.ROOTS if r.startswith('projects')])

    def test_a_project_with_tests_and_no_floor_is_an_error(self):
        with tempfile.TemporaryDirectory() as t:
            v = os.path.join(t, 'projects', 'demo', 'verify')
            os.makedirs(v)
            open(os.path.join(v, '__init__.py'), 'w').close()
            with self.assertRaises(RuntimeError):
                run_tests.project_floors(t)
            with open(os.path.join(v, 'FLOOR'), 'w') as fh:
                fh.write('7\n')
            self.assertEqual(run_tests.project_floors(t), {os.path.join('projects', 'demo'): 7})

    def test_each_root_collects_at_least_its_floor(self):
        for root, floor in run_tests.floors().items():
            with self.subTest(root):
                _suite, n, errors = run_tests.collect(root, run_tests.PATTERN)
                self.assertEqual(errors, [])
                self.assertGreaterEqual(n, floor,
                                        '%s collects %d, floor is %d' % (root, n, floor))


if __name__ == "__main__":
    unittest.main(verbosity=2)

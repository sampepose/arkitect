"""The project's test command.

    python3 lib/verify/run_tests.py         # everything
    python3 lib/verify/run_tests.py -v      # one line per check

In a projects repository that uses this engine from outside it (lib/workspace.py),
`python3 ../arkitect/lib/verify/run_tests.py` runs the engine's layers AND that
repository's projects, each held to its own floor: the engine's tests read the workspace's
ledger, settings and projects, so they are the workspace's checks as much as the engine's.

It exists because BOTH standard runners report success after running nothing:

    $ python3 -m unittest discover -s lib/verify -p 'tests_*.py'   # note the typo
    NO TESTS RAN
    $ echo $?
    0

    $ python3 -m pytest lib/verify -k nothing-matches-this
    8 deselected
    $ echo $?
    0

A mistyped pattern, a renamed file or a moved directory therefore reads as a clean
run. That is the same failure this harness was built to stop: trace.py used to leave
the last good trace in place when a build crashed, so the next diff compared it
against itself and printed nothing. A green light for work that did not happen is
worse than a red one, and it is worse precisely because nobody looks twice.

So discovery is counted, and zero is an error. Collection errors are an error too —
unittest turns an unimportable test module into a synthetic failing test, but a
loader error from a bad start directory is not a test and would otherwise vanish.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATTERN = "test_*.py"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from lib import workspace                                   # noqa: E402


ROOTS = {
    'lib': 147,
    'codes': 163,
    'harness': 79,
}
"""The engine's test roots and the least each must collect. RAISE ONE when you add tests
   to it. A PROJECT's floor is not here: it is the number in projects/<slug>/verify/FLOOR,
   so the engine names no project and a project carries its own guard (all_roots()).

   A single total over three roots cannot say which root lost its tests: a project could
   lose every test it has while the total still cleared a number the engine's tests
   alone exceeded. Renaming test_grading.py away -- 47 tests -- is the shape this
   catches, and it only catches it per root.

   Each floor sits a little under its real count so ordinary work does not trip it.

   A layer appears here only once it HAS tests. codes/ exists from Task 1 but gets its
   first test in Task 5, and the check below skips a root only when its directory is
   absent -- so listing codes/ with a floor of 1 before then would collect 0 against 1
   and fail the suite. Task 5 adds it."""


FLOOR = 'FLOOR'


def project_floors(root=None):
    """{projects/<slug>: floor} for every project with a verify/ package. A project with
       tests and no FLOOR is an error, not a pass: it is exactly the root that could lose
       every test it has without anything noticing."""
    root = root or ROOT
    base = os.path.join(root, 'projects')
    out = {}
    for slug in sorted(os.listdir(base)) if os.path.isdir(base) else ():
        verify = os.path.join(base, slug, 'verify')
        if not os.path.isfile(os.path.join(verify, '__init__.py')):
            continue
        path = os.path.join(verify, FLOOR)
        if not os.path.exists(path):
            raise RuntimeError('projects/%s/verify has tests but no FLOOR file: write the '
                               'number of tests it collects into %s' % (slug, path))
        with open(path) as fh:
            out[os.path.join('projects', slug)] = int(fh.read().split()[0])
    return out


def all_roots(root=None):
    """The engine's ROOTS and every project's floor."""
    return dict(ROOTS, **project_floors(root))


def floors():
    """{absolute directory: floor} for the run this checkout makes: the engine's layers, and
       the projects of the workspace (lib/workspace.py), which is the engine itself unless a
       projects repository uses it from outside."""
    ws = workspace.WORKSPACE
    out = {os.path.join(ROOT, sub): f for sub, f in ROOTS.items()}
    out.update({os.path.join(ws, sub): f for sub, f in project_floors(ws).items()})
    return out


def _tests(suite):
    """Every TestCase in a suite, however deeply the loader nested it."""
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            for sub in _tests(t):
                yield sub
        else:
            yield t


def test_files_on_disk(root):
    """Every test_*.py under root, by module name.

       Dot-directories are skipped, which is not tidiness: .claude/worktrees holds a
       whole checkout per branch, each with its own copy of this suite, and walking
       into them would compare this run against seventy others. unittest's own
       discovery skips them too, since a leading dot is not a package name."""
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith('.') and d != '__pycache__']
        for f in filenames:
            if f.startswith('test_') and f.endswith('.py'):
                out.add(f[:-3])
    return out


def _under(path, base):
    """True if path is base itself or sits somewhere beneath it."""
    path = os.path.realpath(os.path.abspath(path))
    base = os.path.realpath(os.path.abspath(base))
    return path == base or path.startswith(base + os.sep)


def collect(root=None, pattern=None):
    """(suite, count, errors). Discovery from the repository root, so a test added
       anywhere in a PACKAGE — lib/, src/, beside a build script — is found without a
       new command.

       Not anywhere at all: unittest will not recurse into a directory that has no
       __init__.py, and namespace-package discovery was removed in 3.11. A new folder
       of tests without one is skipped in silence — the same failure this file exists
       to prevent, one level up — so main() compares what was collected against the
       test_*.py actually on disk rather than trusting that claim.

       The defaults are read HERE rather than in the signature: a default argument is
       bound once when the function is defined, which would make ROOT and PATTERN
       decorative and this module's own zero-collection test impossible to write.

       top_level_dir tracks start_dir only when start_dir is OUTSIDE the repository —
       a throwaway tree a test points this at, which is self-contained and has nothing
       to collide with. A start_dir INSIDE the repository (one entry of ROOTS, checked
       on its own so a lost file can be pinned to its layer) keeps top_level_dir at the
       repository root instead: lib/verify/ and projects/<slug>/verify/ are both
       named `verify`, and discovering one with the other's directory as its own
       top-level package registers a bare `verify` module in sys.modules that the next
       call's `verify.test_whatever` then resolves against — silently the wrong
       directory, in the same process, for the rest of the run."""
    start = root or ROOT
    ws = workspace.WORKSPACE
    top = ROOT if _under(start, ROOT) else ws if _under(start, ws) else start
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start, pattern=pattern or PATTERN,
                            top_level_dir=top)
    return suite, suite.countTestCases(), list(loader.errors)


def _separate(argv, stream):
    """The engine's layers from ROOT and the projects from the workspace, as one run."""
    ws = workspace.WORKSPACE

    def first():
        # the workspace's `projects` package, never the engine's examples -- and again before
        # every discovery, because discover() puts its top-level directory back in front
        for p in (ws, ROOT):
            while p in sys.path:
                sys.path.remove(p)
        sys.path[:0] = [ws, ROOT]
    first()
    starts = [(os.path.join(ROOT, sub), ROOT) for sub in sorted(ROOTS)]
    starts.append((os.path.join(ws, 'projects'), ws))
    suite, n, on_disk = unittest.TestSuite(), 0, set()
    for start, top in starts:
        if not os.path.isdir(start):
            continue
        first()
        loader = unittest.TestLoader()
        part = loader.discover(start_dir=start, pattern=PATTERN, top_level_dir=top)
        if loader.errors:
            for e in loader.errors:
                print(e, file=sys.stderr)
            print("collection failed: %d error(s) above" % len(loader.errors), file=sys.stderr)
            return 1
        suite.addTest(part)
        n += part.countTestCases()
        on_disk |= test_files_on_disk(start)
    if n == 0:
        print("no tests were collected from %s or %s: nothing ran." % (ROOT, ws), file=sys.stderr)
        return 1
    found = {type(t).__module__.rsplit(".", 1)[-1] for t in _tests(suite)}
    skipped = sorted(on_disk - found)
    if skipped:
        print("%d test file(s) on disk were never collected: %s" % (len(skipped), ", ".join(skipped)),
              file=sys.stderr)
        return 1
    try:
        floors = [(os.path.join(ROOT, sub), f, ROOT) for sub, f in ROOTS.items()] + \
                 [(os.path.join(ws, sub), f, ws) for sub, f in project_floors(ws).items()]
    except (RuntimeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    for here, floor, top in sorted(floors):
        if not os.path.isdir(here):
            continue
        first()
        loader = unittest.TestLoader()
        got = loader.discover(start_dir=here, pattern=PATTERN, top_level_dir=top).countTestCases()
        if loader.errors or got < floor:
            print("%s collected %d tests against a floor of %d." % (here, got, floor), file=sys.stderr)
            return 1
    first()
    print("collected %d tests from %s and %s" % (n, ROOT, ws), flush=True)
    result = unittest.TextTestRunner(stream=stream,
                                     verbosity=2 if "-v" in argv else 1).run(suite)
    ok = result.wasSuccessful()
    print("%s: %d test(s), %d failure(s), %d error(s)"
          % ("PASSED" if ok else "FAILED", result.testsRun,
             len(result.failures), len(result.errors)), flush=True)
    return 0 if ok else 1


def main(argv=(), root=None, pattern=None, stream=None):
    """Exit status for the whole suite: 0 only if tests were found AND all passed.

    root/pattern are arguments so lib/verify/test_run_tests.py can point this at a
    throwaway directory and check the guard actually fires. Testing the thing that
    decides whether tests ran is not circular — it is the one check nothing else can
    make for you."""
    # The workspace is read once, above. A test that runs a tool in a scratch repository must
    # get that repository, so no test inherits the variable that would point it back here.
    os.environ.pop(workspace.ENV, None)
    if root is None and pattern is None and workspace.separate():
        return _separate(argv, stream)
    root = root or ROOT
    pattern = pattern or PATTERN
    if root not in sys.path:
        sys.path.insert(0, root)
    suite, n, errors = collect(root, pattern)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print("collection failed: %d error(s) above" % len(errors), file=sys.stderr)
        return 1
    if n == 0:
        print("no tests were collected from %s matching %r.\n"
              "That is a failure, not a pass: nothing ran." % (root, pattern),
              file=sys.stderr)
        return 1
    if pattern == PATTERN:
        found = set()
        for t in _tests(suite):
            found.add(type(t).__module__.rsplit(".", 1)[-1])
        skipped = sorted(test_files_on_disk(root) - found)
        if skipped:
            print("%d test file(s) on disk were never collected: %s\n"
                  "A directory of tests needs an __init__.py or unittest walks past "
                  "it without a word." % (len(skipped), ", ".join(skipped)),
                  file=sys.stderr)
            return 1
    if root == ROOT and pattern == PATTERN:
        try:
            roots = all_roots(root)
        except (RuntimeError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        for sub, floor in sorted(roots.items()):
            here = os.path.join(root, sub)
            if not os.path.isdir(here):
                continue
            _s, got, errs = collect(here, pattern)
            if errs or got < floor:
                print("%s collected %d tests against a floor of %d.\n"
                      "Tests have gone missing from that layer -- a deleted or renamed "
                      "file, or a module that stopped being discovered. If you removed "
                      "them on purpose, lower its floor (ROOTS, or the project's "
                      "verify/FLOOR) and say so in the commit." % (sub, got, floor),
                      file=sys.stderr)
                return 1
    # flushed, because the runner below writes to stderr: unflushed stdout would put
    # this line AFTER the results, which is the one place it is no use
    print("collected %d tests from %s" % (n, root), flush=True)
    result = unittest.TextTestRunner(stream=stream,
                                     verbosity=2 if "-v" in argv else 1).run(suite)
    ok = result.wasSuccessful()
    # THE LAST LINE, on stdout, flushed. The runner's own summary goes to stderr while
    # the model checks print to stdout, and stdout block-buffers to a pipe and flushes
    # at exit -- so `run_tests.py 2>&1 | tail` used to end on a water heater table with
    # the words FAILED (failures=1) scrolled away above it, and the exit status of a
    # pipeline is the last command's, so it read 0. A failing suite looked like a clean
    # one at the one place the result is actually read. Flushing here empties everything
    # buffered before it, which puts this line after all of it.
    print("%s: %d test(s), %d failure(s), %d error(s)"
          % ("PASSED" if ok else "FAILED", result.testsRun,
             len(result.failures), len(result.errors)), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

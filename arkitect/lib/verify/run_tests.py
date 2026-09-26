"""The project's test command.

    python3 arkitect/lib/verify/run_tests.py         # everything
    python3 arkitect/lib/verify/run_tests.py -v      # one line per check

In a projects repository that uses this engine from outside it (arkitect/lib/workspace.py),
`python3 ../arkitect/lib/verify/run_tests.py` runs the engine's layers AND that
repository's projects, each held to its own floor: the engine's tests read the workspace's
ledger, settings and projects, so they are the workspace's checks as much as the engine's.

It exists because BOTH standard runners report success after running nothing:

    $ python3 -m unittest discover -s arkitect/lib/verify -p 'tests_*.py'   # note the typo
    NO TESTS RAN
    $ echo $?
    0

    $ python3 -m pytest arkitect/lib/verify -k nothing-matches-this
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATTERN = "test_*.py"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from arkitect.lib import workspace                                   # noqa: E402


ROOTS = {
    os.path.join('arkitect', 'lib'): 165,
    os.path.join('arkitect', 'codes'): 163,
    os.path.join('arkitect', 'harness'): 79,
    os.path.join('arkitect', 'web'): 10,
}
"""The engine's test roots and the least each must collect. RAISE ONE when you add tests
   to it. A PROJECT's floor is not here: it is the number in projects/<slug>/verify/FLOOR,
   so the engine names no project and a project carries its own guard (all_roots()).

   A single total over three roots cannot say which root lost its tests: a project could
   lose every test it has while the total still cleared a number the engine's tests
   alone exceeded. Renaming test_grading.py away -- 47 tests -- is the shape this
   catches, and it only catches it per root.

   Each floor sits a little under its real count so ordinary work does not trip it.

   A layer appears here only once it HAS tests. arkitect/codes/ exists from Task 1 but gets its
   first test in Task 5, and the check below skips a root only when its directory is
   absent -- so listing arkitect/codes/ with a floor of 1 before then would collect 0 against 1
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
       the projects of the workspace (arkitect/lib/workspace.py), which is the engine itself unless a
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
       anywhere in a PACKAGE — arkitect/lib/, src/, beside a build script — is found without a
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
       repository root instead: arkitect/lib/verify/ and projects/<slug>/verify/ are both
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
    return _run(suite, n, argv, stream, list(sys.path))


# ---------------------------------------------------------------- running, on every core
#
# The suite is a hundred seconds of CPU, most of it a few modules that start processes of
# their own (test_gate builds a scratch repository per test), and one process ran it all on
# one core. _run() hands it to a pool: every test on its own, except a class with a
# setUpClass or a module with a setUpModule, which go whole so the fixture is built once --
# longest first, by the durations the last run kept. The count still rules: a parallel run
# whose tests do not add up to the number collected is a failure, whatever they reported.

TIMES = 'test-times.json'


def _jobs(argv):
    """-j N from argv; -v (one line per test, in order) and -j 1 run in this process."""
    if "-v" in argv:
        return 1
    for i, a in enumerate(argv):
        if a == "-j" and i + 1 < len(argv):
            return max(1, int(argv[i + 1]))
        if a.startswith("-j") and a[2:].isdigit():
            return max(1, int(a[2:]))
    return os.cpu_count() or 1


def _fixture(cls, *names):
    """True if cls, or a base of it short of unittest.TestCase, defines one of `names`."""
    return any(name in vars(b) for b in cls.__mro__
               if b not in (unittest.TestCase, object) for name in names)


def _units(suite):
    """[[test id, ...], ...]: what one worker runs in one go."""
    units, whole = [], {}
    for t in _tests(suite):
        cls = type(t)
        mod = sys.modules.get(cls.__module__)
        if mod is not None and (hasattr(mod, 'setUpModule') or hasattr(mod, 'tearDownModule')):
            key = cls.__module__
        elif _fixture(cls, 'setUpClass', 'tearDownClass'):
            key = (cls.__module__, cls.__qualname__)
        else:
            units.append([t.id()])
            continue
        if key not in whole:
            whole[key] = []
            units.append(whole[key])
        whole[key].append(t.id())
    return units


def _times_path():
    return os.path.join(workspace.WORKSPACE, '.verify-cache', TIMES)


def _read_times():
    import json
    try:
        with open(_times_path()) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _write_times(times):
    import json, tempfile
    try:
        d = os.path.dirname(_times_path())
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=TIMES)
        with os.fdopen(fd, 'w') as fh:
            json.dump(times, fh)
        os.replace(tmp, _times_path())
    except OSError:
        pass                                  # an order for next time, never a result


_WORKER = {}


def _worker_init(path, modules):
    """Only keeps its arguments: an initializer that raises makes the pool start another
       process in its place, forever, and the run hangs instead of failing."""
    _WORKER.update(path=path, modules=modules)
    os.environ.pop(workspace.ENV, None)       # as main() does, now the import has read it


def _prepare():
    """Stand a pool process where the serial run stands when its first test starts: every
       test module imported, each with the collection's sys.path in front. Test modules move
       sys.path as they import (test_gate.py puts the engine first) and the collection put it
       back before each root; a module imported after the engine went first would find the
       engine's example `projects` package instead of the workspace's. Returns the traceback
       of a module that will not import, every time it is asked."""
    if 'error' not in _WORKER:
        import importlib, traceback
        _WORKER['error'] = None
        try:
            for name in _WORKER['modules']:
                sys.path[:] = _WORKER['path']
                importlib.import_module(name)
        except Exception:
            _WORKER['error'] = traceback.format_exc()
    sys.path[:] = _WORKER['path']
    return _WORKER['error']


def _worker(ids):
    """Run one unit in a pool process: its counts, its failures as text, its duration."""
    import io, time, traceback
    t0 = time.time()
    result = unittest.TextTestResult(unittest.runner._WritelnDecorator(io.StringIO()), True, 0)
    broken = _prepare()
    if broken:
        return {'ids': ids, 'run': 0, 'failures': [], 'unexpected': 0,
                'errors': [('importing the test modules for %s' % ', '.join(ids), broken)],
                'seconds': time.time() - t0}
    try:
        suite = unittest.TestLoader().loadTestsFromNames(ids)
    except Exception:
        return {'ids': ids, 'run': 0, 'failures': [], 'unexpected': 0,
                'errors': [('loading %s' % ', '.join(ids), traceback.format_exc())],
                'seconds': time.time() - t0}
    suite.run(result)
    fmt = lambda pairs: [(str(t), text) for t, text in pairs]
    return {'ids': ids, 'run': result.testsRun, 'failures': fmt(result.failures),
            'errors': fmt(result.errors), 'unexpected': len(result.unexpectedSuccesses),
            'seconds': time.time() - t0}


def _run(suite, n, argv, stream, path, keep_times=True):
    """Run the collected suite, in this process or on a pool; print THE LAST LINE; exit status.
       keep_times=False leaves the order the next run takes alone (the runner's own tests)."""
    jobs = _jobs(argv)
    if jobs == 1:
        result = unittest.TextTestRunner(stream=stream,
                                         verbosity=2 if "-v" in argv else 1).run(suite)
        ok = result.wasSuccessful()
        # THE LAST LINE, on stdout, flushed: see main()
        print("%s: %d test(s), %d failure(s), %d error(s)"
              % ("PASSED" if ok else "FAILED", result.testsRun,
                 len(result.failures), len(result.errors)), flush=True)
        return 0 if ok else 1

    import concurrent.futures as cf, multiprocessing, time
    stream = stream or sys.stderr
    times = _read_times()
    units = sorted(_units(suite), key=lambda u: -sum(times.get(i, 0.0) for i in u))
    procs = min(jobs, len(units))
    t0 = time.time()
    sys.stdout.flush()
    # a worker must find the workspace this process found; _worker_init clears it after
    had = os.environ.get(workspace.ENV)
    os.environ[workspace.ENV] = workspace.WORKSPACE
    try:
        modules = list(dict.fromkeys(type(t).__module__ for t in _tests(suite)))
        # not multiprocessing.Pool: its workers are daemons, which may start no process of their
        # own (a test that runs this runner could not), and it replaces a worker that dies
        # instead of saying so. An executor's worker that dies breaks the run, loudly.
        with cf.ProcessPoolExecutor(procs, multiprocessing.get_context('spawn'), _worker_init,
                                    (path, modules)) as pool:
            done = list(pool.map(_worker, units))
    finally:
        if had is None:
            os.environ.pop(workspace.ENV, None)
        else:
            os.environ[workspace.ENV] = had
    run = sum(d['run'] for d in done)
    failures = [f for d in done for f in d['failures']]
    errors = [e for d in done for e in d['errors']]
    unexpected = sum(d['unexpected'] for d in done)
    if run != n:
        errors.append(('the count', '%d tests were collected and %d ran: a test was lost '
                                    'between them.' % (n, run)))
    for label, items in (('FAIL', failures), ('ERROR', errors)):
        for name, text in items:
            stream.write('=' * 70 + '\n%s: %s\n' % (label, name) + '-' * 70 + '\n' + text + '\n')
    stream.write('Ran %d tests in %.3fs on %d processes\n' % (run, time.time() - t0, procs))
    stream.flush()
    ok = not failures and not errors and not unexpected
    if ok and keep_times:
        _write_times({i: d['seconds'] / len(d['ids']) for d in done for i in d['ids']})
    # THE LAST LINE, on stdout, flushed: see main()
    print("%s: %d test(s), %d failure(s), %d error(s)"
          % ("PASSED" if ok else "FAILED", run, len(failures), len(errors)), flush=True)
    return 0 if ok else 1


def main(argv=(), root=None, pattern=None, stream=None):
    """Exit status for the whole suite: 0 only if tests were found AND all passed.

    root/pattern are arguments so arkitect/lib/verify/test_run_tests.py can point this at a
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
    if root == ROOT and pattern == PATTERN:
        return _run(suite, n, argv, stream, list(sys.path))
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

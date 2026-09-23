"""400 OAK AVE's own tests.

BOTH PROJECTS' MODEL PACKAGES ARE NAMED `src`, and run_tests.py runs every project's tests
in one process. Whichever project imports `src` first owns sys.modules['src'] for the rest
of the run, so a Oak test that simply did `from src import building1` would get 300 S
Elm's Building 1 — the three-dwelling one — and pass or fail against the wrong house.

So every test module here calls `enter()` from setUpModule and `leave()` from
tearDownModule. enter() sets aside whatever `src` is loaded and puts this project first on
sys.path; leave() drops Oak's modules and puts the others back, so 300's tests, which run
after these, find their own.
"""
import os
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(PROJ))

_stash = {}


def _ours(name):
    return name == 'src' or name.startswith('src.')


def enter():
    """Load `src` from this project for the tests that follow."""
    _stash.clear()
    for k in [k for k in sys.modules if _ours(k)]:
        _stash[k] = sys.modules.pop(k)
    for p in (ROOT, PROJ):
        while p in sys.path:
            sys.path.remove(p)
    sys.path[:0] = [PROJ, ROOT]


def leave():
    """Unload this project's `src` and restore whatever was loaded before enter()."""
    for k in [k for k in sys.modules if _ours(k)]:
        del sys.modules[k]
    sys.modules.update(_stash)
    _stash.clear()
    while PROJ in sys.path:
        sys.path.remove(PROJ)

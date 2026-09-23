"""Make this engine importable from anywhere, so a projects repository beside it can use it.

    python3 -m harness.engine status     # which engine `import lib` finds, and from where
    python3 -m harness.engine link       # this checkout, for every script this Python runs
    python3 -m harness.engine unlink

A projects repository holds projects/, decisions/ and arkitect.toml and no engine
(lib/workspace.py). Its build scripts do `from lib ...`, and `python3 -m harness.decisions`
needs `harness`, so the engine has to be on sys.path wherever that repository is. `link`
writes one line, this checkout's path, into arkitect.pth in the user's site-packages -- the
file `pip install -e` would write, without the packaging (a later phase adds that).

An engine script puts its own checkout first on sys.path, so an engine WORKTREE still runs
its own code; the link is only what a script outside any engine falls back to. To run a
projects repository against a worktree instead, set PYTHONPATH to it.
"""
import os
import site
import sys

from lib import workspace

PTH = 'arkitect.pth'


def pth_path(user_site=None):
    return os.path.join(user_site or site.getusersitepackages(), PTH)


def linked(user_site=None):
    """The engine the link names, or None."""
    p = pth_path(user_site)
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return fh.read().strip() or None


def link(engine=None, user_site=None):
    p = pth_path(user_site)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as fh:
        fh.write((engine or workspace.ENGINE) + '\n')
    return p


def unlink(user_site=None):
    p = pth_path(user_site)
    if os.path.exists(p):
        os.remove(p)
    return p


def main(argv):
    if not argv or argv[0] not in ('status', 'link', 'unlink'):
        print(__doc__)
        return 1
    if argv[0] == 'link':
        if not site.ENABLE_USER_SITE:
            print('this Python ignores user site-packages; set PYTHONPATH=%s instead'
                  % workspace.ENGINE, file=sys.stderr)
            return 1
        print('linked: %s -> %s' % (link(), workspace.ENGINE))
    elif argv[0] == 'unlink':
        print('removed %s' % unlink())
    else:
        print('this engine: %s' % workspace.ENGINE)
        print('linked:      %s (%s)' % (linked() or 'nothing', pth_path()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

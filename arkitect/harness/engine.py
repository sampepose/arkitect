"""Which engine a Python finds, and how it got there.

    arkitect engine status     # the version, the checkout `import arkitect` resolves to, how
    arkitect engine unlink     # remove the one-line link that stood in for an install before
                               # the engine was a package

A projects repository holds projects/, decisions/ and arkitect.toml and no engine
(arkitect/lib/workspace.py); its build scripts do `from arkitect.lib ...`, so the engine is
installed where that repository's Python finds it:

    python3 -m pip install -e path/to/arkitect      # editable: the checkout IS the engine

An engine script puts its own checkout first on sys.path, so an engine worktree still runs its
own code; to run a projects repository against a worktree, install that worktree or set
PYTHONPATH to it.
"""
import os
import site
import sys

from arkitect.lib import workspace

PTH = 'arkitect.pth'          # the link's file, from before the engine was a package


def pth_path(user_site=None):
    return os.path.join(user_site or site.getusersitepackages(), PTH)


def linked(user_site=None):
    """The engine the old link names, or None."""
    p = pth_path(user_site)
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return fh.read().strip() or None


def unlink(user_site=None):
    p = pth_path(user_site)
    if os.path.exists(p):
        os.remove(p)
    return p


def installed():
    """How this Python has the engine: 'editable', 'installed', or None (found by path only)."""
    try:
        from importlib import metadata
        dist = metadata.distribution('arkitect')
    except Exception:
        return None
    direct = dist.read_text('direct_url.json') or ''
    return 'editable' if '"editable": true' in direct else 'installed'


def main(argv):
    if not argv or argv[0] not in ('status', 'unlink'):
        print(__doc__)
        return 1
    if argv[0] == 'unlink':
        print('removed %s' % unlink())
        return 0
    from arkitect import __version__
    print('arkitect %s' % __version__)
    print('engine:   %s' % workspace.ENGINE)
    print('install:  %s' % (installed() or 'none (found by path)'))
    old = linked()
    if old:
        print('old link: %s -> %s (arkitect engine unlink, once installed)' % (pth_path(), old))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

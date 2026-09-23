"""Run one of the engine's hooks by name, from wherever the engine is installed.

    python3 -m arkitect.harness.hook stop_gate        # reads the hook's JSON on stdin, as Claude Code sends it

A projects repository outside the engine (arkitect/lib/workspace.py) wires its hooks this way, so its
committed .claude/settings.json names no path: the engine is found the way any import is,
through `arkitect engine link`. If it is not linked, Python fails with "No module
named harness" -- loudly, never a hook that silently did nothing.

Inside the engine the hooks keep their path form, so a worktree runs its own copies.
"""
import os
import runpy
import sys

from arkitect.lib import workspace

HOOKS = os.path.join(workspace.ENGINE, '.claude', 'hooks')


def names():
    return sorted(f[:-3] for f in os.listdir(HOOKS)
                  if f.endswith('.py') and f != 'hooklib.py' and not f.startswith('_'))


def main(argv):
    if len(argv) != 1 or argv[0] not in names():
        print('usage: python3 -m arkitect.harness.hook {%s}' % ','.join(names()), file=sys.stderr)
        return 2
    sys.argv = [os.path.join(HOOKS, argv[0] + '.py')]
    runpy.run_path(sys.argv[0], run_name='__main__')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

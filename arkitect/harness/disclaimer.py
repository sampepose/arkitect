"""What the engine's output is not, said once to every user and on request.

    arkitect disclaimer        # print it

`arkitect` shows it the first time a user runs any tool, on stderr -- never in the JSON a
program reads from stdout -- and records that it did in ~/.config/arkitect/, beside the
user's config.toml, so it is shown once per person, not once per command. If that record
cannot be written, the text is shown and nothing else changes.

The README states the same thing in its opening lines. The sheets carry no disclaimer: a
title block says only what is true of the drawing.
"""
import os
import sys

TEXT = """\
arkitect -- please read this once.

What arkitect produces is not the work of a licensed architect or engineer. It generates
drawings from a model and checks them against the rules it encodes; a set that passes every
check is not thereby code-compliant, and the building official decides what is. Who may
prepare and submit residential drawings is set by your state.

arkitect is licensed for noncommercial use (PolyForm Noncommercial 1.0.0; the documentation
CC BY-NC 4.0). Commercial use needs a written grant from the maintainer.

This notice is shown once; `arkitect disclaimer` prints it again.
"""


def record_path(home=None):
    home = home if home is not None else os.path.expanduser('~')
    return os.path.join(home, '.config', 'arkitect', 'disclaimer-shown')


def first_run(stream=None, home=None):
    """Show TEXT on `stream` (stderr) if this user has not seen it; True if it was shown."""
    p = record_path(home)
    if os.path.exists(p):
        return False
    print(TEXT, file=stream or sys.stderr, flush=True)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w') as fh:
            fh.write('shown\n')
    except OSError:
        pass                                   # shown; a read-only home only means shown again
    return True


def main(argv):
    print(TEXT, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

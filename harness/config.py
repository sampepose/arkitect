"""Who and what an installation is: the designer of record, the title block's owner and
contractor, the design defaults, the house style, the hook policy, and the words that must
never appear in the shipped engine. Everything personal lives here, not in the engine.

    python3 -m harness.config show [--project <slug>]    # the merged settings, as TOML-ish text
    python3 -m harness.config get designer.name          # one value

Three files, each overriding the one before, all optional:

    ~/.config/arkitect/config.toml      the user's
    arkitect.toml                       the workspace's (lib/workspace.py): a private
                                        projects repository keeps its own
    projects/<slug>/arkitect.toml       one project's

Read with the standard library's tomllib. `arkitect.example.toml` shows every key.
"""
import copy
import os
import sys
import tomllib

from lib import workspace

ROOT = workspace.WORKSPACE             # the installation's own settings sit with its projects

DEFAULTS = {
    'designer': {
        'name': 'the designer of record',     # who confirms a decision (harness/decisions.py)
        'role': 'designer of record',
    },
    'titleblock': {
        'owner': [],                          # offered as the default owner block for a new address
        'contractor': [],
    },
    'defaults': {
        'design': [],                         # design preferences a new address starts from
    },
    'style': {
        'house': os.path.join('style', 'house-style.md'),
    },
    'hooks': {
        # The Stop hook (.claude/hooks/stop_gate.py), once hooks are installed
        # (python3 -m harness.hooks install): what a turn ending on work does.
        'green_uncommitted': 'block',         # block | advise | off
        'red': 'block-unattended',            # block | block-unattended | advise | off
    },
    'identity': {
        'private_words': [],                  # never in a shipped file (harness/verify/test_identity.py)
    },
    'verify': {
        'twins_ceiling': 0,                   # lines two projects may share (lib/verify/test_twins.py)
    },
}
CHOICES = {
    ('hooks', 'green_uncommitted'): ('block', 'advise', 'off'),
    ('hooks', 'red'): ('block', 'block-unattended', 'advise', 'off'),
}


def paths(project=None, root=ROOT, home=None):
    home = home if home is not None else os.path.expanduser('~')
    out = [os.path.join(home, '.config', 'arkitect', 'config.toml'), os.path.join(root, 'arkitect.toml')]
    if project:
        out.append(os.path.join(root, 'projects', project, 'arkitect.toml'))
    return out


def _merge(base, over, where):
    for k, v in over.items():
        if k not in base:
            raise ValueError('%s: unknown setting %r' % (where, k))
        if isinstance(base[k], dict):
            if not isinstance(v, dict):
                raise ValueError('%s: %s must be a table' % (where, k))
            _merge(base[k], v, where)
        else:
            if isinstance(base[k], list) and not isinstance(v, list):
                raise ValueError('%s: %s must be a list' % (where, k))
            base[k] = v


def load(project=None, root=ROOT, home=None):
    """The merged settings: DEFAULTS, then each file that exists, in order."""
    cfg = copy.deepcopy(DEFAULTS)
    for p in paths(project, root, home):
        if os.path.exists(p):
            with open(p, 'rb') as fh:
                _merge(cfg, tomllib.load(fh), p)
    for (sec, key), allowed in CHOICES.items():
        if cfg[sec][key] not in allowed:
            raise ValueError('%s.%s is %r; it must be one of %s'
                             % (sec, key, cfg[sec][key], ', '.join(allowed)))
    return cfg


def get(dotted, project=None, root=ROOT, home=None):
    sec, _dot, key = dotted.partition('.')
    return load(project, root, home)[sec][key]


def _show(cfg):
    out = []
    for sec, table in cfg.items():
        out.append('[%s]' % sec)
        for k, v in table.items():
            out.append('%s = %r' % (k, v))
        out.append('')
    return '\n'.join(out)


def main(argv):
    if not argv or argv[0] not in ('show', 'get'):
        print(__doc__)
        return 1
    proj = argv[argv.index('--project')+1] if '--project' in argv else None
    try:
        if argv[0] == 'show':
            print(_show(load(proj)))
        else:
            v = get(argv[1], proj)
            print('\n'.join(v) if isinstance(v, list) else v)
    except (ValueError, KeyError, IndexError, tomllib.TOMLDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

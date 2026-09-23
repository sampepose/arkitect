"""The machine interface: what `arkitect <tool> ... --json` prints, for a program to read.

Every JSON output is one object, and its first keys are always:

    schema      SCHEMA, this file's number. Within one number a field may be ADDED, never
                removed, renamed or given another meaning; anything else raises the number.
    kind        what the object describes: 'gate', 'progress', 'decisions', 'review', ...
    engine      the engine version that produced it (arkitect/__init__.py)
    workspace   the workspace it describes (arkitect/lib/workspace.py)

docs/interface.md lists every kind and its fields. A tool writes its object with emit(), so a
change to the envelope reaches every tool at once.
"""
import json
import os
import re

from arkitect.lib import workspace

SCHEMA = 1


def engine_version():
    """Read as text, never imported: a .pyc is trusted on size and mtime to the second."""
    p = os.path.join(workspace.ENGINE, 'arkitect', '__init__.py')
    with open(p) as fh:
        m = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", fh.read(), re.M)
    return m.group(1) if m else None


def envelope(kind, data, ws=None):
    """`data` with the four keys first. A key of data never overrides them."""
    out = {'schema': SCHEMA, 'kind': kind, 'engine': engine_version(),
           'workspace': ws or workspace.WORKSPACE}
    out.update({k: v for k, v in data.items() if k not in out})
    return out


def emit(kind, data, ws=None):
    print(json.dumps(envelope(kind, data, ws), indent=1, sort_keys=False))

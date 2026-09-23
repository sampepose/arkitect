"""Write projects/<slug>/ from its intake: a project that builds, traces, tests and passes
the gate on its first day, with nothing in it but what is its own.

    python3 -m arkitect.harness.scaffold projects/<slug>/intake.json

The intake must be valid and must fit -- every zoning rule it does not meet states the
relief the designer chose (`python3 -m arkitect.harness.intake` first). It refuses a project that exists.

WHAT IT WRITES, and why each is the shape it is:

    build.py            DOCUMENTS from arkitect/lib/buildkit.py; G-001 and C-102 from
                        arkitect/codes/columbus/zoning_sheets.py; check_model() runs the zoning fit.
                        Draws nothing at import.
    src/project.py      the title block (arkitect/codes/columbus.titleblock) and the output names
    src/sitework.py     INTAKE and MASSING, read from intake.json: ONE definition of the lot
    src/sheets/         empty: a project's own sheets go here, one feature at a time
    verify/             isolation and ProjectTests from arkitect/harness/testkit.py -- imported, so
                        the second new address copies nothing from the first
    progress.json       the feature list, arkitect/harness/catalog.py expanded for this program
    CLAUDE.md           only what differs here from the root CLAUDE.md
    trace.md5           written by arkitect/lib/verify/gate.py accept, the one sanctioned writer

Its three deliverables are tracked by .gitignore's suffix rules, so nothing outside the
project is written. Its test floor is verify/FLOOR, which arkitect/lib/verify/run_tests.py reads. Every generated src/ definition is
under three lines or an import, so arkitect/lib/verify/twins.py finds nothing to count.
"""
import datetime
import os
import sys

from arkitect.harness import catalog, intake as I, progress
from arkitect.lib import workspace

ROOT = workspace.WORKSPACE             # a new project is written into the workspace


def _stem(d):
    """'100 EXAMPLE ST' -> '100-Example': the stem of the deliverables' names."""
    words = d['address'].split()
    num = next((w for w in words if w.isdigit()), '')
    name = next((w for w in words if not w.isdigit() and w.upper() not in ('N', 'S', 'E', 'W')), 'Site')
    return '%s-%s' % (num, name.capitalize()) if num else name.capitalize()


BUILD = '''"""{address} — what the project writes, in what order, and what must hold first.

Scaffolded by arkitect/harness/scaffold.py from intake.json on {date}. The set grows one feature
at a time: `python3 -m arkitect.harness.progress next {slug}`. Importing this module draws nothing,
writes nothing and prints nothing.
"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))        # this project
ROOT = os.path.dirname(os.path.dirname(HERE))            # the repository
for _p in (ROOT, HERE):                                  # arkitect/lib/ and arkitect/codes/, then src/
    if _p not in sys.path:
        sys.path.insert(0, _p)
from arkitect.codes.columbus import fit
from arkitect.codes.columbus.zoning_sheets import cover_sheet, zoning_site_plan
from arkitect.lib.buildkit import documents
from src import project, sitework

_CHECKED = False


def check_model():
    """What the sheets depend on, checked before a line is drawn."""
    global _CHECKED
    if not __debug__:
        raise SystemExit("refusing to build: python -O removes every assert, and every "
                         "model check here is one.")
    if _CHECKED:
        return
    fit.check(sitework.MASSING)
    _CHECKED = True


# The set in binding order; G-001's index lists it, and C-102, bound separately.
INDEX = [("G-001", "COVER SHEET"), ("C-102", "ZONING SITE PLAN — 11 x 17, ISSUED SEPARATELY")]
SHEETS = (cover_sheet(sitework.INTAKE, sitework.MASSING, INDEX),)

# Read by arkitect/lib/export/dxf.py, which may not import a project.
DXF_OUT = os.path.join(HERE, project.DXF_OUT)

DOCUMENTS = documents(project.TITLEBLOCK, check_model, SHEETS, os.path.join(HERE, project.PDF_OUT),
                      zoning_site_plan(sitework.INTAKE, sitework.MASSING),
                      os.path.join(HERE, project.ZONING_OUT))
build_set, build_zoning_sheet = DOCUMENTS


if __name__ == "__main__":
    for _doc in DOCUMENTS:
        print("saved", _doc())
'''

PROJECT = '''"""{address} — the title block and the output names. Everything else it knows comes
from intake.json through src/sitework.py."""
from arkitect.codes.columbus import titleblock
from src.sitework import INTAKE

ADDRESS = INTAKE["address"]
TITLEBLOCK = titleblock(INTAKE)

PDF_OUT = "{stem}-permit-set.pdf"
ZONING_OUT = "{stem}-zoning-site-plan.pdf"
DXF_OUT = "{stem}-floor-plans.dxf"
'''

SITEWORK = '''"""{address} — the lot and what stands on it, read from intake.json: the ONE definition of
the program. Change the program in intake.json and run `python3 -m arkitect.harness.intake
projects/{slug}/intake.json` before anything else; the build's zoning check reads this.

Coordinates are arkitect/codes/columbus/fit.py's: feet, x from the LEFT side lot line looking from
{street}, y from the front lot line toward the rear.
"""
import json
import os

from arkitect.codes.columbus.fit import Massing

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "intake.json")) as _fh:
    INTAKE = json.load(_fh)
MASSING = Massing.from_intake(INTAKE)
'''

PACKAGE = '''"""{address} — this lot, and nothing else. Import from here: `from src.sitework import
MASSING`, never `import sitework`: a bare module name shares one namespace with the
standard library, and a module here called `site.py` would resolve to CPython's own."""
'''

SHEETS_PKG = '''"""{address}'s own sheets, one module per sheet, added one feature at a time
(progress.json). G-001 and C-102 are drawn by arkitect/codes/columbus/zoning_sheets.py until a
sheet here replaces them."""
'''

VERIFY = '''"""{address}'s own tests. Both the isolation and the tests every project needs are
arkitect/harness/testkit.py's, imported rather than copied."""
import os

from arkitect.harness.testkit import isolation

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
enter, leave = isolation(PROJ)
'''

TEST = '''"""{address}: the drawing against trace.md5, its text against arkitect/lib/verify/sheet_text.py,
and progress.json against what the build proves."""
import unittest

from arkitect.harness.testkit import ProjectTests
from projects.{slug}.verify import PROJ, enter, leave


class {cls}(ProjectTests, unittest.TestCase):
    PROJ = PROJ
    ENTER = staticmethod(enter)
    LEAVE = staticmethod(leave)


if __name__ == "__main__":
    unittest.main()
'''

CLAUDE = '''# {address} — working notes for agents

{program} Scaffolded from `intake.json` on {date} by `arkitect/harness/scaffold.py`. The repo-level
`CLAUDE.md` governs house style, the oracles and the working rules. **This file is only
what is different here.**

## The loop

```sh
python3 -m arkitect.harness.progress next {slug}      # the next feature: its guards, its references
python3 -m arkitect.lib.verify.gate                   # every oracle; names the sheets that moved
python3 -m arkitect.lib.verify.gate render --moved    # look at what moved
python3 -m arkitect.lib.verify.gate accept            # write trace.md5 once the move is meant
python3 -m arkitect.harness.progress set {slug} <id> passes   # refused unless the build proves it
```

`intake.json` is the program and the ONE definition of the lot; `src/sitework.py` reads it.
Change it, then `python3 -m arkitect.harness.intake projects/{slug}/intake.json`, then build.

## Zoning, as scaffolded

```
{fit}
```

## Open — from the intake

{open}
'''


def _program(d):
    parts = []
    for b in d['buildings']:
        units = ', '.join('%s (%d BR)' % (u['name'], u['bedrooms']) for u in b['dwellings'])
        parts.append('%s, %s, %s x %s, %d storey%s: %s' % (
            b['name'], 'principal' if b['role'] == 'principal' else 'ADU',
            _ft(b['width']), _ft(b['depth']), b['storeys'], '' if b['storeys'] == 1 else 's', units))
    lot = d['lot']
    return ('A permit set for %s: %s on a %s x %s %s lot%s.' % (
        d['address'], '; '.join(parts), _ft(lot['width']), _ft(lot['depth']),
        'corner' if lot.get('corner') else 'interior',
        ' with a %s alley' % _ft(lot['alley_width']) if lot.get('alley') else ''))


def _ft(v):
    from arkitect.lib.units import fmt
    return fmt(v)


def _open(d, rows):
    from arkitect.codes.columbus import fit as F
    items = []
    if not d['lot'].get('survey'):
        items.append('- **No survey.** The lot is the Auditor\'s GIS; C-102 says so.')
    if d['parcel'].upper() == 'TBD':
        items.append('- **Parcel number TBD** on the title block.')
    for r in rows:
        if r.status == F.RELIEF:
            items.append('- **%s** (%s): %s. Stated in intake.json `relief`, not granted.'
                         % (r.label, r.citation, r.note.split(';')[0]))
        elif r.status == F.NOT_CHECKED:
            items.append('- %s: not checked yet (%s).' % (r.label, r.note or 'needs the model'))
    for r in rows:
        if r.citation == F.CITE['density'] and r.status != F.NOT_CHECKED:
            items.append('- %s is held to a figure whose section is unverified.' % r.label)
    return '\n'.join(items) or '- Nothing yet.'


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write(text)


def _add_floor(slug, floor, root):
    """The project's test floor, verify/FLOOR: a lost test file then fails the suite."""
    with open(os.path.join(root, 'projects', slug, 'verify', 'FLOOR'), 'w') as fh:
        fh.write('%d\n' % floor)


def scaffold(intake_path, root=ROOT, accept=True):
    """Write the project. Returns (slug, [paths written]). Raises ValueError on an intake
       that is invalid, does not fit, or names a project that exists."""
    from arkitect.codes.columbus import fit as F
    d = I.load(intake_path)
    bad = I.validate(d)
    if bad:
        raise ValueError('intake invalid:\n  - ' + '\n  - '.join(bad))
    rows = F.fit(I.massing(d))
    unmet = F.failing(rows)
    if unmet:
        raise ValueError('the program does not fit: %s. Redesign it, or record the relief the designer '
                         'chooses in "relief".' % ', '.join(r.rule for r in unmet))
    slug = d['slug']
    proj = os.path.join(root, 'projects', slug)
    if os.path.abspath(os.path.dirname(intake_path)) != os.path.abspath(proj):
        raise ValueError('put the intake at projects/%s/intake.json' % slug)
    if os.path.exists(os.path.join(proj, 'build.py')):
        raise ValueError('projects/%s already has a build.py; the scaffold writes new projects only'
                         % slug)
    date = datetime.date.today().isoformat()
    fmt = dict(address=d['address'], slug=slug, date=date, stem=_stem(d), street=d['street'],
               cls=''.join(w.capitalize() for w in slug.split('_')) + 'Tests')
    files = {
        '__init__.py': '"""%s."""\n' % d['address'],
        'build.py': BUILD.format(**fmt),
        'src/__init__.py': PACKAGE.format(**fmt),
        'src/project.py': PROJECT.format(**fmt),
        'src/sitework.py': SITEWORK.format(**fmt),
        'src/sheets/__init__.py': SHEETS_PKG.format(**fmt),
        'verify/__init__.py': VERIFY.format(**fmt),
        'verify/test_project.py': TEST.format(**fmt),
        'CLAUDE.md': CLAUDE.format(program=_program(d), fit=F.summary(rows), open=_open(d, rows),
                                   **fmt),
    }
    written = []
    for rel, text in files.items():
        _write(os.path.join(proj, rel), text)
        written.append(os.path.join('projects', slug, rel))
    progress.save(slug, {'project': slug, 'address': d['address'], 'scaffolded': date,
                         'features': catalog.features(d)}, root)
    written.append(os.path.join('projects', slug, 'progress.json'))
    _add_floor(slug, len(_test_names()), root)
    written.append(os.path.join('projects', slug, 'verify', 'FLOOR'))
    if accept:
        from arkitect.lib.verify import gate
        lines, ok = gate.accept(only=[slug])
        if not ok:
            raise RuntimeError('the scaffolded build does not build:\n' + '\n'.join(lines))
        written.append(os.path.join('projects', slug, 'trace.md5'))
    return slug, written


def _test_names():
    from arkitect.harness.testkit import ProjectTests
    return [n for n in dir(ProjectTests) if n.startswith('test_')]


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    try:
        slug, written = scaffold(argv[0])
    except (ValueError, RuntimeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print('scaffolded projects/%s:' % slug)
    for w in written:
        print('  ' + w)
    print('\nNext: python3 -m arkitect.lib.verify.gate; then python3 -m arkitect.harness.progress next %s' % slug)
    print('Commit these files by name, with intake.json.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

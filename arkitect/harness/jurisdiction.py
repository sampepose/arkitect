"""Jurisdictions: which are encoded, whether one meets the contract, and a skeleton for a new one.

    arkitect jurisdiction list                          # every one, with its state and verification
    arkitect jurisdiction check columbus                # the contract, and its fit on a sample lot
    arkitect jurisdiction new dayton --name "Dayton, Ohio" --state arkitect.codes.ohio

`new` writes arkitect/codes/<name>/ with every name the contract asks for (arkitect/codes/
jurisdiction.py, docs/jurisdictions.md) and a fit whose every rule is NOT CHECKED -- and with
VERIFIED_ON empty, so no intake may name it until someone has encoded its rules, checked them
against a real permit set and recorded that. A skeleton is where the research goes, never a
jurisdiction that quietly passes everything.
"""
import os
import sys

from arkitect.codes import jurisdiction
from arkitect.lib import workspace

INIT = '''"""{name}.

Encodes: TO BE ENCODED -- the zoning code (and its edition), and the state codes {state}
already holds. Verified: NOT YET. Until VERIFIED_ON is set, no intake may name this
jurisdiction (arkitect/codes/jurisdiction.py); docs/jurisdictions.md says what setting it means.
"""
import {state} as _STATE

NAME = {name!r}
CITY = {city!r}                             # as its zoning line prints it
STATE = {state!r}
CODES = ('TO BE ENCODED: the zoning code, with its edition',)
VERIFIED_ON = None                          # the date its rules were checked against a real permit set
VERIFIED_AGAINST = None                     # what they were checked against
REVIEWER = 'TO BE ENCODED: who reviews a residential set here'
PARCEL_LABEL = 'PARCEL'                     # the title block's line before the number: 'FRANKLIN COUNTY PARCEL'
LOT_SOURCE = "TO BE ENCODED: where an unsurveyed lot's figures come from"
LOT_SOURCE_SHORT = 'TO BE ENCODED'
ZONING_CODE = 'TO BE ENCODED'               # how its zoning sections are cited before the number: 'C.C.'

# {{intake path: question}}, only where this jurisdiction can phrase a question better
QUESTION_TEXT = {{}}

# the state's code lines, this city's zoning line, and the state's seal line if it has one (Ohio does)
TITLEBLOCK_CODE = (list(_STATE.TITLEBLOCK_CODE) + ["ZONING: " + CITY + " %s"]
                   + ([_STATE.SEAL_LINE] if getattr(_STATE, 'SEAL_LINE', None) else []))


def titleblock(d):
    """The whole title block, from an intake."""
    n_units = sum(len(b['dwellings']) for b in d['buildings'])
    n_bldg = len(d['buildings'])
    return [
        (None, [d['address'], d['city_line'], '%s %s' % (PARCEL_LABEL, d['parcel']),
                'NEW CONSTRUCTION \\u2014 %d DWELLING UNIT%s' % (n_units, '' if n_units == 1 else 'S'),
                '%d DETACHED RESIDENTIAL BUILDING%s' % (n_bldg, '' if n_bldg == 1 else 'S')]),
        ('OWNER', list(d['owner'])),
        ('CONTRACTOR', list(d['contractor'])),
        ('CODE', [t % d['district'] if '%s' in t else t for t in TITLEBLOCK_CODE]),
    ]
'''

FIT = '''"""Does a program fit a {name} lot? TO BE ENCODED.

Every rule below is NOT CHECKED until its figure and its section are encoded from the zoning
code's own text. arkitect/codes/columbus/fit.py is the worked example: a figure beside the line
that sources it, SECTION UNVERIFIED where the text has not been obtained, RELIEF STATED where
the project names a basis.
"""
from arkitect.codes.massing import NOT_CHECKED, Row
from arkitect.codes import massing as _massing

UNVERIFIED = 'SECTION UNVERIFIED'

# {{rule: section}} -- every rule fit() answers, and the relief an intake may name
CITE = {{
    'lot_width': UNVERIFIED,
    'units': UNVERIFIED,
    'front_yard': UNVERIFIED,
    'side_yard': UNVERIFIED,
    'rear_yard': UNVERIFIED,
    'coverage': UNVERIFIED,
    'height': UNVERIFIED,
    'parking': UNVERIFIED,
}}
LABELS = {{'lot_width': 'Lot width', 'units': 'Dwelling units', 'front_yard': 'Front yard',
          'side_yard': 'Side yards', 'rear_yard': 'Rear yard', 'coverage': 'Lot coverage',
          'height': 'Building height', 'parking': 'Parking'}}


def fit(massing):
    """One row per rule, every one NOT CHECKED until it is encoded."""
    return [Row(rule, LABELS[rule], 'TO BE ENCODED', '', None, NOT_CHECKED, CITE[rule],
                'the rule is not encoded yet') for rule in CITE]


failing = _massing.failing
summary = _massing.summary


def check(massing):
    rows = fit(massing)
    print('ZONING FIT:')
    for line in summary(rows).split('\\n'):
        print('   ' + line)
    bad = failing(rows)
    assert not bad, 'the massing does not meet %s' % ', '.join(r.rule for r in bad)
    return rows
'''


def _sample(name):
    """A plausible intake in `name` for the check: a lot and one house on it."""
    return {'jurisdiction': name, 'address': '1 SAMPLE ST', 'city_line': 'SAMPLE', 'parcel': 'TBD',
            'street': 'SAMPLE STREET', 'district': 'SAMPLE', 'owner': ['OWNER'], 'contractor': ['CONTRACTOR'],
            'lot': {'width': 40.0, 'depth': 120.0, 'corner': False, 'alley': False, 'front_line': 20.0},
            'buildings': [{'name': 'BUILDING 1', 'role': 'principal', 'x': 5.0, 'y': 25.0,
                           'width': 26.0, 'depth': 40.0, 'storeys': 2,
                           'dwellings': [{'name': 'UNIT 1', 'bedrooms': 3}]}]}


def check(name):
    """Sentences: every way `name` falls short, then what its fit says of a sample lot."""
    import importlib
    from arkitect.codes.massing import Massing, Row
    try:
        module = importlib.import_module('arkitect.codes.' + name)
    except ImportError as exc:
        return ['arkitect/codes/%s does not import: %s' % (name, exc)], []
    bad = jurisdiction.problems(module)
    try:
        fit = importlib.import_module('arkitect.codes.%s.fit' % name)
        rows = fit.fit(Massing.from_intake(_sample(name)))
    except Exception as exc:
        return bad + ['its fit fails on a sample lot: %s: %s' % (exc.__class__.__name__, exc)], []
    bad += ['fit returned a %s, not a Row' % type(r).__name__ for r in rows if not isinstance(r, Row)]
    rules = {r.rule for r in rows}
    # a rule may apply only to some lots (a corner lot's side street); every one answered is cited
    bad += ['fit answers %r, which CITE does not name' % r for r in sorted(rules - set(fit.CITE))]
    try:
        tb = module.titleblock(_sample(name))
        if [h for h, _l in tb] != [None, 'OWNER', 'CONTRACTOR', 'CODE']:
            bad.append('titleblock() must give the address block, OWNER, CONTRACTOR and CODE, in that order')
    except Exception as exc:
        bad.append('titleblock() fails on a sample intake: %s: %s' % (exc.__class__.__name__, exc))
    return bad, rows


def new(name, place, state, root=None):
    """Write the skeleton; the paths written."""
    if not name.isidentifier() or name != name.lower():
        raise ValueError('a jurisdiction is a lowercase Python identifier: %r' % name)
    d = os.path.join(root or workspace.ENGINE, 'arkitect', 'codes', name)
    if os.path.exists(d):
        raise ValueError('arkitect/codes/%s exists' % name)
    city = place.split(',')[0].strip().upper()
    os.makedirs(d)
    written = []
    for rel, text in (('__init__.py', INIT), ('fit.py', FIT)):
        p = os.path.join(d, rel)
        with open(p, 'w') as fh:
            fh.write(text.format(name=place, city=city, state=state))
        written.append(p)
    return written


def main(argv):
    if not argv or argv[0] not in ('list', 'check', 'new'):
        print(__doc__)
        return 1
    if argv[0] == 'list':
        import importlib
        for name in jurisdiction.available():
            m = importlib.import_module('arkitect.codes.' + name)
            print('%-12s %-24s %-22s %s' % (name, getattr(m, 'NAME', '?'), getattr(m, 'STATE', '?'),
                                            'verified %s' % m.VERIFIED_ON if getattr(m, 'VERIFIED_ON', None)
                                            else 'NOT VERIFIED'))
        return 0
    if argv[0] == 'check':
        if len(argv) < 2:
            print('which jurisdiction? arkitect jurisdiction check <name>', file=sys.stderr)
            return 2
        bad, rows = check(argv[1])
        for r in rows:
            print('  %-15s %-20s %s' % (r.status, r.label, r.citation))
        if bad:
            print('%s does NOT meet the contract:\n  - %s' % (argv[1], '\n  - '.join(bad)))
            return 1
        print('%s meets the contract (docs/jurisdictions.md)' % argv[1])
        return 0
    opt = lambda f: argv[argv.index(f)+1] if f in argv else None
    if len(argv) < 2 or not opt('--name') or not opt('--state'):
        print('arkitect jurisdiction new <name> --name "City, State" --state arkitect.codes.<state>',
              file=sys.stderr)
        return 2
    try:
        for p in new(argv[1], opt('--name'), opt('--state')):
            print('wrote', p)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    print('Now encode its rules, check them against a real permit set, and set VERIFIED_ON:\n'
          '  arkitect jurisdiction check %s' % argv[1])
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

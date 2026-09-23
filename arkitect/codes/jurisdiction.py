"""The jurisdiction contract: what a city package must give the engine, and the one way to
find one. docs/jurisdictions.md is the prose; this is what the tools and the shared tests
check (arkitect/codes/verify/test_jurisdictions.py).

A jurisdiction is a city package inside its state's, `arkitect/codes/<state>/<city>/`, named by
its path -- `"ohio/columbus"`, the reference -- in an intake's `"jurisdiction"`, since a city's
name alone is not unique. The state package (`arkitect/codes/ohio`) holds the building,
plumbing and electrical codes the state adopts; the city adds its zoning, its title block and
the words its reviewers use.

    load('ohio/columbus')   the package, or LookupError naming what is missing
    available()             every city package under arkitect/codes, as 'state/city'
    problems(module)        every way a package falls short, as sentences
"""
import importlib
import os
import pkgutil

# What the package itself exports. (name, what it is.)
ATTRIBUTES = (
    ('NAME', "the place, as a sentence names it: 'Columbus, Ohio'"),
    ('CITY', "the city as its zoning line prints it: 'COLUMBUS'"),
    ('STATE', "the state package it builds on: 'arkitect.codes.ohio'"),
    ('CODES', 'the codes it encodes, one string each, editions included'),
    ('VERIFIED_ON', 'the date it was last checked against a real permit set'),
    ('VERIFIED_AGAINST', 'what it was checked against'),
    ('REVIEWER', "who reviews a set here, as the plan-review brief says it"),
    ('PARCEL_LABEL', "the title block's parcel line before the number"),
    ('LOT_SOURCE', "where an unsurveyed lot's dimensions come from, in prose; a sheet prints it in capitals"),
    ('LOT_SOURCE_SHORT', "the same, short, as a table cell says it: \"Auditor's GIS\""),
    ('ZONING_CODE', "how its zoning sections are cited before the number: 'C.C.'"),
    ('WATER_UTILITY', "the water utility a service note defers to: 'COLUMBUS DPU'"),
    ('QUESTION_TEXT', "{intake path: question} for what only this city can phrase"),
    ('TITLEBLOCK_CODE', "the title block's CODE lines; '%s' takes the zoning district"),
    ('titleblock', 'titleblock(intake) -> [(heading, [lines])], the whole title block'),
)
# What its `fit` module exports: the zoning check every new address runs.
FIT = (
    ('fit', 'fit(massing) -> [Row], one per rule (arkitect/codes/massing.py)'),
    ('failing', 'failing(rows) -> the rows not met and with no relief stated'),
    ('summary', 'summary(rows) -> the rows as text, for the intake to print'),
    ('check', 'check(massing): raise AssertionError if a rule fails with no relief stated'),
    ('CITE', "{rule: section}: every rule fit() answers, and the relief an intake may name"),
)
# What the state package exports.
STATE_ATTRIBUTES = (
    ('NAME', "the state: 'Ohio'"),
    ('TITLEBLOCK_CODE', "the title block's lines for the state's codes"),
)


def problems(module):
    """Every way `module` falls short of the contract, as sentences; [] when it meets it."""
    out = ['%s has no %s (%s)' % (module.__name__, n, why) for n, why in ATTRIBUTES
           if not hasattr(module, n)]
    try:
        fit = importlib.import_module(module.__name__ + '.fit')
    except ImportError as exc:
        return out + ['%s has no fit module: %s' % (module.__name__, exc)]
    out += ['%s.fit has no %s (%s)' % (module.__name__, n, why) for n, why in FIT
            if not hasattr(fit, n)]
    if hasattr(module, 'VERIFIED_ON') and not module.VERIFIED_ON:
        out.append('%s has not been verified: VERIFIED_ON is empty. Record when and against what '
                   'real permit set it was checked (VERIFIED_ON, VERIFIED_AGAINST) before an intake '
                   'may name it' % module.__name__)
    state = getattr(module, 'STATE', None)
    if state and state != module.__name__.rsplit('.', 1)[0]:
        out.append('%s names STATE %s but sits in %s' % (module.__name__, state,
                                                         module.__name__.rsplit('.', 1)[0]))
    if state:
        try:
            st = importlib.import_module(state)
            out += ['%s has no %s (%s)' % (state, n, why) for n, why in STATE_ATTRIBUTES
                    if not hasattr(st, n)]
        except ImportError as exc:
            out.append('%s names STATE %s, which does not import: %s' % (module.__name__, state, exc))
    return out


def module_name(name):
    """'ohio/columbus' -> 'arkitect.codes.ohio.columbus'; ValueError for anything else."""
    parts = (name or '').split('/')
    if len(parts) != 2 or not all(p.isidentifier() and p == p.lower() for p in parts):
        raise ValueError('a jurisdiction is named state/city, lowercase: %r' % name)
    return 'arkitect.codes.' + '.'.join(parts)


def name_of(module):
    """The 'state/city' name of a jurisdiction package."""
    return module.__name__[len('arkitect.codes.'):].replace('.', '/')


def load(name):
    """The jurisdiction package for 'state/city', meeting the contract."""
    try:
        path = module_name(name)
    except ValueError:
        raise LookupError('no jurisdiction %r: an intake names one of %s, as state/city'
                          % (name, ', '.join(available())))
    try:
        module = importlib.import_module(path)
    except ImportError:
        raise LookupError('no jurisdiction %r: arkitect/codes/%s/ does not exist; the ones encoded are %s '
                          '(docs/jurisdictions.md says how to add one)' % (name, name, ', '.join(available())))
    bad = problems(module)
    if bad:
        raise LookupError('jurisdiction %r does not meet the contract:\n  ' % name + '\n  '.join(bad))
    return module


def fit(name):
    """The jurisdiction's zoning fit module."""
    return importlib.import_module(load(name).__name__ + '.fit')


def fit_of(module):
    """The fit module of a jurisdiction package already loaded."""
    return importlib.import_module(module.__name__ + '.fit')


def available():
    """Every city package under a state package, as 'state/city': a package with a fit module
       one level inside arkitect/codes/<state>/. A state's own rule packages (ohio/rco) have none."""
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    for state in pkgutil.iter_modules([here]):
        if not state.ispkg or state.name == 'verify':
            continue
        for city in pkgutil.iter_modules([os.path.join(here, state.name)]):
            if city.ispkg and os.path.exists(os.path.join(here, state.name, city.name, 'fit.py')):
                out.append('%s/%s' % (state.name, city.name))
    return sorted(out)

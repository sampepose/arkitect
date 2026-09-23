"""The jurisdiction contract: what a city package must give the engine, and the one way to
find one. docs/jurisdictions.md is the prose; this is what the tools and the shared tests
check (arkitect/codes/verify/test_jurisdictions.py).

A jurisdiction is a package `arkitect.codes.<name>` -- `columbus` is the reference -- named by
an intake's `"jurisdiction"`. It builds on a STATE package (`arkitect.codes.ohio`) that holds
the building, plumbing and electrical codes the state adopts; the city adds its zoning, its
title block and the words its reviewers use.

    load('columbus')        the package, or LookupError naming what is missing
    available()             every package under arkitect/codes that meets the contract
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
    state = getattr(module, 'STATE', None)
    if state:
        try:
            st = importlib.import_module(state)
            out += ['%s has no %s (%s)' % (state, n, why) for n, why in STATE_ATTRIBUTES
                    if not hasattr(st, n)]
        except ImportError as exc:
            out.append('%s names STATE %s, which does not import: %s' % (module.__name__, state, exc))
    return out


def load(name):
    """The jurisdiction package `arkitect.codes.<name>`, meeting the contract."""
    if not name or not name.isidentifier():
        raise LookupError('no jurisdiction %r: an intake names one of %s' % (name, ', '.join(available())))
    try:
        module = importlib.import_module('arkitect.codes.' + name)
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


def available():
    """Every package under arkitect/codes that is a jurisdiction: it has a fit module and a
       STATE. A state package, or a package of shared rules, is not one."""
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    for info in pkgutil.iter_modules([here]):
        if not info.ispkg or info.name in ('verify',):
            continue
        if os.path.exists(os.path.join(here, info.name, 'fit.py')):
            out.append(info.name)
    return sorted(out)

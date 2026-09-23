"""Columbus, Ohio.

Encodes: the Residential Code of Ohio as amended 2024, the Ohio Plumbing Code, NEC 2023,
and Columbus City Code Title 33. Verified against a 27-sheet Columbus permit set, 2026-09-17.

The reference jurisdiction: docs/jurisdictions.md is the contract every city package meets,
and this one is its worked example. A second belongs beside it, and may not be added without
the same record: which editions it encodes, when it was verified, and against what. Adding a
city is a code-research deliverable, not a software change.
"""

from arkitect.codes import ohio as STATE_CODES

NAME = 'Columbus, Ohio'
CITY = 'COLUMBUS'                         # as its zoning line prints it
STATE = 'arkitect.codes.ohio'           # the state package this city builds on
REVIEWER = 'City of Columbus residential plan reviewer'
PARCEL_LABEL = 'FRANKLIN COUNTY PARCEL'
LOT_SOURCE = "the Franklin County Auditor's GIS"      # where an unsurveyed lot's dimensions come from
LOT_SOURCE_SHORT = "Auditor's GIS"
ZONING_CODE = 'C.C.'                     # how this city's zoning sections are cited: "C.C. 3332.05"

# What the intake asks that only this city can phrase: {path: question} over the generic
# ones (arkitect/harness/intake.py QUESTIONS).
QUESTION_TEXT = {
    'city_line': 'City, state and ZIP line (e.g. "COLUMBUS, OHIO 43205")?',
    'parcel': 'Franklin County parcel number, or TBD?',
    'district': 'Zoning district (e.g. R-4)?',
    'lot.survey': "Is there a boundary survey, or are the dimensions from the Auditor's GIS?",
    'lot.front_line': 'Front building line for this street, in feet (C.C. 3332.21; the line '
                      'established for this street, which differs street to street -- ask, do not assume)?',
}

CODES = ('Residential Code of Ohio, as amended 2024',
         'Ohio Plumbing Code',
         'NEC 2023',
         'Columbus City Code Title 33')
VERIFIED_ON = '2026-09-17'
VERIFIED_AGAINST = 'a Columbus permit set, 27 sheets'

# The CODE block every set's title block prints, word for word (each project's src/project.py).
TITLEBLOCK_CODE = STATE_CODES.TITLEBLOCK_CODE + ["ZONING: " + CITY + " %s", STATE_CODES.SEAL_LINE]


def titleblock(d):
    """A title block from an intake: the address block, owner, contractor and code, in the
       shape both existing projects' src/project.py spell out by hand."""
    n_units = sum(len(b['dwellings']) for b in d['buildings'])
    n_bldg = len(d['buildings'])
    return [
        (None, [d['address'], d['city_line'], '%s %s' % (PARCEL_LABEL, d['parcel']),
                'NEW CONSTRUCTION \u2014 %d DWELLING UNIT%s' % (n_units, '' if n_units == 1 else 'S'),
                '%d DETACHED RESIDENTIAL BUILDING%s' % (n_bldg, '' if n_bldg == 1 else 'S')]),
        ('OWNER', list(d['owner'])),
        ('CONTRACTOR', list(d['contractor'])),
        ('CODE', [t % d['district'] if '%s' in t else t for t in TITLEBLOCK_CODE]),
    ]

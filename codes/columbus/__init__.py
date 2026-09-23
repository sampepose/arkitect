"""Columbus, Ohio.

Encodes: the Residential Code of Ohio as amended 2024, the Ohio Plumbing Code, NEC 2023,
and Columbus City Code Title 33. Verified against a 27-sheet Columbus permit set, 2026-09-17.

A second jurisdiction belongs beside this one, and may not be added without the same
record: which editions it encodes, when it was verified, and against what. Adding a city
is a code-research deliverable, not a software change.
"""

NAME = 'Columbus, Ohio'
CODES = ('Residential Code of Ohio, as amended 2024',
         'Ohio Plumbing Code',
         'NEC 2023',
         'Columbus City Code Title 33')
VERIFIED_ON = '2026-09-17'
VERIFIED_AGAINST = 'a Columbus permit set, 27 sheets'

# The CODE block every set's title block prints, word for word (each project's src/project.py).
TITLEBLOCK_CODE = ["RESIDENTIAL CODE OF OHIO 2019",
                   "OAC 4101:8, EFF. 7-1-2019, AS AMENDED:",
                   "CH. 4 FOUNDATIONS, EFF. 3-1-2024",
                   "CH. 34 ELECTRICAL, EFF. 4-15-2024",
                   "CH. 44 STANDARDS, EFF. 4-15-2024",
                   "ELECTRICAL: NFPA 70, 2023 NEC",
                   "BASE: 2018 IRC FIRST PRINTING",
                   "ZONING: COLUMBUS %s",
                   "NO SEAL REQUIRED \u2014 ORC 3791.04(A)(2)(b)"]


def titleblock(d):
    """A title block from an intake: the address block, owner, contractor and code, in the
       shape both existing projects' src/project.py spell out by hand."""
    n_units = sum(len(b['dwellings']) for b in d['buildings'])
    n_bldg = len(d['buildings'])
    return [
        (None, [d['address'], d['city_line'], 'FRANKLIN COUNTY PARCEL %s' % d['parcel'],
                'NEW CONSTRUCTION \u2014 %d DWELLING UNIT%s' % (n_units, '' if n_units == 1 else 'S'),
                '%d DETACHED RESIDENTIAL BUILDING%s' % (n_bldg, '' if n_bldg == 1 else 'S')]),
        ('OWNER', list(d['owner'])),
        ('CONTRACTOR', list(d['contractor'])),
        ('CODE', [t % d['district'] if '%s' in t else t for t in TITLEBLOCK_CODE]),
    ]

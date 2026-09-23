"""RCO Tables 602.7(1) and 602.7(2), headers in bearing walls, and Table 602.7.5.

One transcription for every project. It lived, word for word, in each project's framing
model until 2026-09-18, and only one project's tests pinned it.
"""
from arkitect.lib.units import fmt

# RCO Tables R602.7(1) (exterior bearing walls) and R602.7(2) (interior bearing walls),
# 2018 IRC, the 30 psf ground-snow and 36 ft building-width columns — the conservative
# side of this lot's 20 psf and 26 ft. Two-ply headers only. Spans in feet, jack studs
# at each end. Transcribed from the printed tables and pinned by test_framing.py.
def _fi(ft, inch):
    return ft + inch/12.0

HEADER_TABLE = {
    'ROOF AND CEILING': [('2-2x4', _fi(2, 7), 1), ('2-2x6', _fi(3, 10), 1), ('2-2x8', _fi(4, 10), 2),
                         ('2-2x10', _fi(5, 9), 2), ('2-2x12', _fi(6, 10), 2),
                         ('3-2x8', _fi(6, 1), 1), ('3-2x10', _fi(7, 3), 2), ('3-2x12', _fi(8, 6), 2)],
    'ROOF, CEILING AND ONE CENTER-BEARING FLOOR': [('2-2x4', _fi(2, 2), 1), ('2-2x6', _fi(3, 3), 2), ('2-2x8', _fi(4, 1), 2),
                                                   ('2-2x10', _fi(4, 10), 2), ('2-2x12', _fi(5, 8), 2),
                                                   ('3-2x8', _fi(5, 1), 2), ('3-2x10', _fi(6, 1), 2), ('3-2x12', _fi(7, 2), 2)],
    'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR': [('2-2x4', _fi(1, 10), 1), ('2-2x6', _fi(2, 10), 2), ('2-2x8', _fi(3, 7), 2),
                                               ('2-2x10', _fi(4, 2), 2), ('2-2x12', _fi(4, 11), 3),
                                               ('3-2x8', _fi(4, 5), 2), ('3-2x10', _fi(5, 3), 2), ('3-2x12', _fi(6, 2), 2)],
    'ONE FLOOR ONLY': [('2-2x4', _fi(2, 4), 1), ('2-2x6', _fi(3, 6), 1), ('2-2x8', _fi(4, 5), 2),
                       ('2-2x10', _fi(5, 3), 2), ('2-2x12', _fi(6, 3), 2),
                       ('3-2x8', _fi(5, 7), 1), ('3-2x10', _fi(6, 7), 2), ('3-2x12', _fi(7, 9), 2)],
}
# Footnote f of Table R602.7(1): the spans assume the header's top laterally braced by
# perpendicular framing; cripple studs bearing on it are the footnote's example of
# unbraced, and the openings here have cripples above them, so every 2x8, 2x10 and 2x12
# header's span is multiplied by 0.70. 2x4 and 2x6 headers are not factored.
UNBRACED_FACTOR = 0.70
def _factor(size):
    return UNBRACED_FACTOR if size.split('x')[1] in ('8', '10', '12') else 1.0
HEADER_BRACING = ('CRIPPLES BEAR ON THE HEADERS: 2x8 AND DEEPER SPANS x %.2f, TABLE 602.7(1) NOTE f'
                  % UNBRACED_FACTOR)
TABLE_OF = {'ONE FLOOR ONLY': 'TABLE 602.7(2)'}
# Table R602.7.5, full-height studs at each end of an exterior header, <= 115 mph
# Exposure B (G-001), studs at 16" o.c.: (up to span, studs); between rows, the larger span's.
FULL_HEIGHT_STUDS = [(8.0, 1), (18.0, 2)]


def header_for(load_case, width):
    """(size, jacks, row, factored span): the smallest header whose factored span covers
       the opening, in the order 2-2x4 .. 2-2x12, 3-2x8 .. 3-2x12."""
    rows = HEADER_TABLE[load_case]
    for size, span, jacks in rows:
        if span*_factor(size) >= width-1e-9:
            return size, jacks, '%s, %s' % (TABLE_OF.get(load_case, 'TABLE 602.7(1)'), load_case), span*_factor(size)
    raise ValueError('%s of %s: past the last row of the table' % (load_case, fmt(width)))


def full_height_studs(width):
    for span, n in FULL_HEIGHT_STUDS:
        if width <= span+1e-9: return n
    raise ValueError('header span %s past Table 602.7.5' % fmt(width))

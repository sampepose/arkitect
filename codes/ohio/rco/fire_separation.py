"""RCO Table 302.1(1), exterior walls by fire separation distance: the wall, projection,
opening and penetration rows, footnotes a and b, and the check every eave and rake is
held to.

One transcription for every project, pinned by codes/verify/test_fire_separation.py. Where
the imaginary line stands, and what stands near it, is the project's.
"""
from lib.units import fmt, inches

# ---------------- RCO Table 302.1(1), EXTERIOR WALLS ----------------
# Transcribed from the table, not from a summary, and pinned by lib/verify/test_fsd.py.
# Each row is (minimum fire separation distance, what the table requires at it); a row
# applies from its distance up to the next one's.
WALLS = ((0.0, '1 HOUR'),          # tested to ASTM E119 / UL 263, exposure from both sides
         (5.0, 'NONE'))
PROJECTIONS = ((0.0, 'NOT ALLOWED'),
               (2.0, '1 HOUR ON THE UNDERSIDE, OR HEAVY TIMBER, OR FIRE-RETARDANT-TREATED WOOD'),
               (5.0, 'NONE'))
# The projections row's two footnotes, verbatim. Each reduces the rated row to 0 hours.
FOOTNOTE_A = ('The fire-resistance rating shall be permitted to be reduced to 0 hours on the underside '
              'of the eave overhang if fireblocking is provided from the wall top plate to the underside '
              'of the roof sheathing.')
FOOTNOTE_B = ('The fire-resistance rating shall be permitted to be reduced to 0 hours on the underside '
              'of the rake overhang where gable vent openings are not installed.')
EAVE, RAKE = 'EAVE', 'RAKE'
OPENINGS = ((0.0, 0.0),            # not allowed
            (3.0, 0.25),           # 25 percent maximum of the wall area
            (5.0, None))           # unlimited
PENETRATIONS = ((0.0, 'COMPLY WITH RCO 302.4'),
                (3.0, 'NONE REQUIRED'))

RATED_MAX  = 5.0           # under this a wall is rated, and a projection's underside with it
PROJ_FREE  = 5.0           # at or over this a projection needs no rating: what the stairs now hold
PROJ_MIN   = 2.0           # under this a projection is not permitted at all
OPEN_MIN   = 3.0           # under this an opening is not permitted at all
OPEN_MAX   = 0.25          # from OPEN_MIN to RATED_MAX, the most of a wall that may be opening
SECTION    = 'RCO TABLE 302.1(1)'


def _row(table, fsd):
    """The row of one of the tables above that governs at this fire separation distance."""
    hit = [v for d, v in table if fsd >= d-1e-9]
    return hit[-1]


def wall_rating(fsd):
    """What Table 302.1(1) requires of an exterior WALL at this distance."""
    return _row(WALLS, fsd)


def projection_rating(fsd):
    """...of a PROJECTION: an eave, a cornice, a stair landing and its flight."""
    return _row(PROJECTIONS, fsd)


def underside(fsd, kind, fireblocked=False, gable_vent=True):
    """What the table asks of a roof edge's underside at this distance, footnotes applied:
       NOT ALLOWED, NONE, 0 HOURS under footnote a or b, or the rated row."""
    r = projection_rating(fsd)
    if r in ('NOT ALLOWED', 'NONE'):
        return r
    if kind == EAVE and fireblocked:
        return '0 HOURS, FOOTNOTE a'
    if kind == RAKE and not gable_vent:
        return '0 HOURS, FOOTNOTE b'
    return r


def opening_max(fsd):
    """The fraction of the wall its openings may be, or None for unlimited."""
    return _row(OPENINGS, fsd)


def penetration_rule(fsd):
    """What the table asks of a PENETRATION. Note that this is the table's rule for an
       unrated wall; a penetration of a RATED wall goes to RCO 302.4 whatever the
       distance, which is what A-001 note 2a says and why it needs no distance in it."""
    return _row(PENETRATIONS, fsd)


def rated(fsd):
    return fsd < RATED_MAX-1e-9


# ---------------- every roof edge ----------------
# Edge: one eave or rake. `wall` is its wall's fire separation distance, or None on a
# street side, where RCO 202 takes it to the street centreline and the table never
# engages; `overhang` is the roof edge's projection past that wall.
def edge_violations(edges):
    """Every eave and rake of both buildings against Table 302.1(1) and its footnotes.
       edges: [(name, kind, wall, overhang, fireblocked, gable_vent), ...]"""
    v = []
    for name, kind, wall, over, blocked, vent in edges:
        if wall is None:
            continue
        reach = wall-over
        rating = underside(reach, kind, blocked, vent)
        if rating == 'NOT ALLOWED':
            v.append('%s projects %s, leaving %s, under the %s at which %s permits a projection at all'
                     % (name, inches(over), fmt(reach), fmt(PROJ_MIN), SECTION))
        elif rating == projection_rating(RATED_MAX-1e-6):
            v.append('%s projects %s, leaving %s, so its underside needs %s of %s; the set carries none'
                     % (name, inches(over), fmt(reach), rating, SECTION))
    return v


# ---------------- RCO 202: the face the distance is measured FROM ----------------
# "FIRE SEPARATION DISTANCE. The distance measured from the building face to one of the
# following: 1. The closest interior lot line ... The distance shall be measured at right
# angles from the face of the wall."
#
# The face is the wall's OUTSIDE face, and the plans are not dimensioned to it: G-001
# note 5 puts every dimension on the face of the STUD, so a site plan's yard is a
# FRAMING dimension and the distance this table takes is that figure less everything the
# assembly carries outside its studs -- sheathing, any exterior gypsum, the WRB and the
# cladding.
#
# The difference decides a row. 5'-0" of framing with 7/16" of sheathing on it is a
# 4'-11-9/16" fire separation distance, which WALLS makes 1 HOUR and OPENINGS limits to
# 25 percent, where 5'-0" is 0 hours with openings unlimited. A zoning yard is measured
# to the same face, so one function serves both and a project passes it whichever
# minimum governs that wall.
FACE = 'the outside face of the exterior wall, RCO 202'


def face_distance(framing, build_out):
    """The distance Table 302.1(1) and a zoning yard both take, from the dimension the
       plans carry. `framing` is to the outside face of the stud; `build_out` is the
       assembly's thickness outside it."""
    return framing-build_out


def wall_violations(walls, minimum):
    """Every exterior wall held to a lot line, measured at the face RCO 202 names.
       walls: [(name, framing, build_out), ...]. `minimum` is the distance those walls
       are held to -- RATED_MAX where the table governs, a zoning yard where that is
       larger. A wall whose FRAMING clears the minimum but whose FACE does not is the
       one this catches, and it is the one a site plan cannot show."""
    v = []
    for name, framing, build_out in walls:
        d = face_distance(framing, build_out)
        if d < minimum-1e-9:
            v.append('%s is dimensioned %s to the face of its framing and carries %s outside it, '
                     'so at %s it stands %s, under the %s it is held to'
                     % (name, fmt(framing), inches(build_out), FACE, fmt(d), fmt(minimum)))
    return v

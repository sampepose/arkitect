"""The RCO 302.1 imaginary line in the courtyard, and Table 302.1(1) as a table.

400 Oak's two buildings stand on one lot with 15'-0" between them (src/sitework.py,
COURT). RCO 302.1 measures fire separation distance for each of them to an IMAGINARY LINE
between them, and where that line is drawn is the designer's, not the code's.

The courtyard is one equation, as it was on 300 S Elm, where this module came from:

    OFF_B1 + the stair's width + the stair's clearance = GAP

with two floors under it:

    the stair clear  >= PROJ_FREE (5'-0")   or the Unit 3 stair needs a rated underside
    OFF_B1           >= RATED_MAX (5'-0")   or Building 1's rear wall is a rated wall,
                                            its openings capped at 25 percent

300 had 12'-0" and had to rate its Building 1 rear wall to make the stair fit. Oak has
three feet more, so NEITHER wall and not the stair is rated: the line may stand anywhere
from 5'-0" to 6'-6" off Building 1. That is 1'-6" of slack, and OFF_B1 gives all of it to
the stair, which is built last and in the field, as 300 did. Building 1's rear wall
stands exactly on the 5'-0" with no margin; it is laid out off the foundation.

The midline does NOT work: 7'-6" each side leaves the stair 4'-0" to the line.

OFF_B1 is the one number. Building 2's stair rating (src/building2.py) and the site
check (src/sitework.py, check_fsd()) read it. Roof edges are not checked against the
line yet: neither building's roof is modelled for this lot.

Distances are in FEET. Site y increases toward the rear, as everywhere else.
"""
from arkitect.lib.units import fmt, inches
from src.stairs import EXT_STAIR

# ---------------- the courtyard ----------------
# The courtyard the line is drawn in. Stated, not derived — the site is built from the
# buildings, which read this module — and src/sitework.py's check_fsd() holds it to the
# courtyard the site actually leaves.
GAP = 15.0

# THE DECISION. 6'-3" off Building 1. Two projections reach toward the line and each wants
# 5'-0" of it left, or its underside is rated: Building 1's rear rake, 12" past its wall
# (placed when its gable was vented; with no gable vent, footnote b would let it come to
# 2'-0", but the line was left where it stood), and the Unit 3 stair, 3'-6" past
# Building 2's. 15'-0" less the two leaves 6", and the line splits it: 5'-3" to each. It
# stood 5'-0" off Building 1 until the roof's overhang was counted (2026-09-18), which put
# the rake 4'-0" from it.
RAKE_OVERHANG = 1.0        # the rakes' and eaves' overhang; check_fsd() holds it to foundation.ROOF_OVERHANG
OFF_B1 = 6.25

OFF_B2 = GAP-OFF_B1        # 8'-9" — Building 2's courtyard wall is clear of the table entirely


# RCO Table 302.1(1), EXTERIOR WALLS: shared, see arkitect/codes/ohio/rco/fire_separation.py
from arkitect.codes.ohio.rco.fire_separation import (OPEN_MIN, PROJ_FREE, PROJ_MIN, RAKE, RATED_MAX, SECTION,
                                            opening_max, projection_rating, rated, underside)


# ---------------- Building 1's rear wall ----------------
# The house's rear wall: nothing on Level 1, Bedrooms 1 and 3's W-As on Level 2. The
# caller measures each storey from the plans and hands in (opening SF, wall SF) per
# storey; the gable is left out of the wall area, the conservative way round.
def rear_open_ratio(storeys):
    """The largest share of any storey of the wall that is opening."""
    return max(o/w for o, w in storeys)


# ---------------- the two stairs ----------------
STAIR_W = EXT_STAIR.width

# What the Unit 3 stair, the only one measured to this line, keeps clear of it. (The
# names are 300's: the stair was that project's Unit 5's, and building2.py's U5_* too.)
U5_CLEAR = OFF_B2-STAIR_W

# The most ANY part of that stair may project from Building 2's courtyard face and still
# leave PROJ_FREE to the line — guard, canopy fascia, a stringer end, a fastener head.
# The stair is drawn at STAIR_W, so the difference is the construction tolerance the
# line's position bought, and C-101 prints it as the limit rather than as a margin:
# a limit is a thing to build to, a margin is a thing to spend.
PROJ_MAX = OFF_B2-PROJ_FREE
TOLERANCE = PROJ_MAX-STAIR_W


def stair_clear(off_b2=None, width=None):
    return (OFF_B2 if off_b2 is None else off_b2)-(STAIR_W if width is None else width)


def line_y(b1_rear_y):
    """The line in site feet, from Building 1's rear wall."""
    return b1_rear_y+OFF_B1


def fsd_violations(b1_rear_y, b2_court_y, rear_storeys, rear_rake=0.0,
                   off_b1=None, leaders=(), rear_gable_vent=True):
    """Every way the courtyard leaves RCO 302.1 and its table. Arguments override the
       model so a test can ask what a change would do."""
    off = OFF_B1 if off_b1 is None else off_b1
    off2 = (b2_court_y-b1_rear_y)-off
    v = []
    if abs((b2_court_y-b1_rear_y)-GAP) > 1e-9:
        v.append('the courtyard measures %s between the buildings, against the %s the line is drawn in'
                 % (fmt(b2_court_y-b1_rear_y), fmt(GAP)))
    if off < OPEN_MIN-1e-9:
        v.append("the line stands %s off Building 1's rear wall, under the %s at which %s begins to "
                 'permit an opening in it; that wall has %g SF of them'
                 % (fmt(off), fmt(OPEN_MIN), SECTION, max(o for o, _w in rear_storeys)))
    ratio = rear_open_ratio(rear_storeys)
    cap = opening_max(off)
    if cap is not None and ratio > cap+1e-9:
        v.append("Building 1's rear wall opens %.1f%% of a story where %s permits %.0f%% at %s"
                 % (100*ratio, SECTION, 100*cap, fmt(off)))
    if rear_rake > 1e-9:
        reach = off-rear_rake
        rating = underside(reach, RAKE, gable_vent=rear_gable_vent)
        if rating == 'NOT ALLOWED':
            v.append("the rear rake projects %s, leaving %s to the line, under the %s at which %s permits "
                     'a projection at all' % (inches(rear_rake), fmt(reach), fmt(PROJ_MIN), SECTION))
        elif rating == projection_rating(RATED_MAX-1e-6):
            v.append("the rear rake projects %s, leaving %s to the line, over a vented gable, so its underside "
                     'needs %s of %s; the set carries none' % (inches(rear_rake), fmt(reach), rating, SECTION))
    # Anything else standing on that wall and reaching toward the line. A rainwater
    # leader is not a projection in the sense of the table's row — it is a conductor
    # with no underside to protect, not a cornice — but it IS the only thing attached to
    # this face, so the set carries its figure rather than leaving the next reader to
    # find out for themselves that DS-1 comes down it.
    for mark, d in leaders:
        if off-d < PROJ_MIN-1e-9:
            v.append('%s projects %s off the rear wall, leaving %s to the line, under the %s at which '
                     '%s permits a projection at all' % (mark, inches(d), fmt(off-d), fmt(PROJ_MIN), SECTION))
    if rated(off):
        v.append("Building 1's rear wall stands %s from the line, inside the %s of %s, and the set "
                 'rates no wall on that face' % (fmt(off), fmt(RATED_MAX), SECTION))
    clear = stair_clear(off2)
    if clear < PROJ_FREE-1e-9:
        v.append('the Unit 3 stair leaves %s to the line, under the %s at which %s asks nothing of a '
                 "projection's underside; the set carries no rated underside for it"
                 % (fmt(clear), fmt(PROJ_FREE), SECTION))
    if rated(off2):
        v.append("Building 2's courtyard wall stands %s from the line, inside the %s of %s, and the set "
                 'rates no wall on that face' % (fmt(off2), fmt(RATED_MAX), SECTION))
    return v

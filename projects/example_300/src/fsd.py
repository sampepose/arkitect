"""The RCO 302.1 imaginary line in the courtyard, and Table 302.1(1) as a table.

Two buildings stand on one lot with 12'-0" between them. RCO 302.1 measures fire
separation distance for each of them to an IMAGINARY LINE between them, and where that
line is drawn is the designer's, not the code's. It used to be the midline, 6'-0" each
face, which rated nothing on either wall and put the Unit 5 stair 2'-6" from it — inside
the 5'-0" of Table 302.1(1), so its underside was a listed 1-hour assembly.

The gap is fully spent, and the whole design is one equation:

    OFF_B1 + the stair's width + the stair's clearance = GAP

with two floors under it and nothing else:

    the stair clear  >= PROJ_FREE (5'-0")   or the projection needs a rated underside
    OFF_B1           >= OPEN_MIN  (3'-0")   or the rear wall may have NO opening at all

So the line may stand anywhere from 3'-0" to 3'-6" off Building 1 and nowhere else.
There are six inches of slack in the courtyard and OFF_B1 decides who gets them: the
wood stair, which is built last and in the field, or Building 1's rear wall, which is
laid out off the foundation survey. It goes to the stair.

OFF_B1 is the one number. The rear wall's rating, its opening ratio, the stair's
rating, every dimension and note on C-101, A-001, A-201, A-202, A-601 and A-604, and
the braced-wall nail at Level 2 all read from here. Set it to 3.5 and the line returns
to the midline's other option, 3'-6" off Building 1, and everything follows.

Distances are in FEET. Site y increases toward the rear, as everywhere else.
"""
from lib.units import fmt, inches
from src.openings import WIN_SF
from src.stairs import EXT_STAIR

# ---------------- the courtyard ----------------
GAP = 12.0                 # clear between Building 1's rear wall and Building 2's courtyard face

# THE DECISION. 3'-0" off Building 1, so the stair keeps 5'-6" to the line where it
# needs 5'-0" — six inches of construction tolerance in the thing that is field built.
# The cost is that the rear wall sits exactly on the 3'-0" at which Table 302.1(1)
# begins to permit an opening, with no margin. The designer's call; see the design note.
OFF_B1 = 3.0

OFF_B2 = GAP-OFF_B1        # 9'-0" — Building 2's courtyard wall is clear of the table entirely


# RCO Table 302.1(1), EXTERIOR WALLS: shared, see codes/ohio/rco/fire_separation.py
from codes.ohio.rco.fire_separation import (OPEN_MIN, PROJ_FREE, PROJ_MIN, RAKE, RATED_MAX, SECTION,
                                            opening_max, projection_rating, rated, underside)


# ---------------- Building 1's rear wall ----------------
# The wall the line now rates. Units 2 and 3 stack, so both storeys carry the same two
# openings: the kitchen W-A and the rear living W-C. The gable over Level 2 is rated
# with the wall and has no opening in it; it is left out of the denominator, which is
# the conservative way round — adding its area would only lower the percentage.
REAR_MARKS = ('A', 'C')                      # the marks in Building 1's rear wall, each storey
REAR_OPEN_SF = sum(WIN_SF[m] for m in REAR_MARKS)


def rear_wall_sf(width, storey):
    return width*storey


def rear_open_ratio(width, storey):
    return REAR_OPEN_SF/rear_wall_sf(width, storey)


# ---------------- the two stairs ----------------
STAIR_W = EXT_STAIR.width

# What the Unit 5 stair, which is the only one measured to this line, keeps clear of it.
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


def fsd_violations(b1_rear_y, b2_court_y, b1_width, storey_h, rear_rake,
                   stoop_y1, off_b1=None, leaders=(), rear_gable_vent=True):
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
                 'permit an opening in it; that wall has %g SF of them' % (fmt(off), fmt(OPEN_MIN), SECTION, REAR_OPEN_SF))
    ratio = rear_open_ratio(b1_width, storey_h)
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
    clear = stair_clear(off2)
    if clear < PROJ_FREE-1e-9:
        v.append('the Unit 5 stair leaves %s to the line, under the %s at which %s asks nothing of a '
                 "projection's underside; the set carries no rated underside for it"
                 % (fmt(clear), fmt(PROJ_FREE), SECTION))
    if rated(off2):
        v.append("Building 2's courtyard wall stands %s from the line, inside the %s of %s, and the set "
                 'rates no wall on that face' % (fmt(off2), fmt(RATED_MAX), SECTION))
    if stoop_y1 > b1_rear_y+off-1e-9:
        v.append('the Unit 3 stoop reaches site %s, past the imaginary line at site %s'
                 % (fmt(stoop_y1), fmt(b1_rear_y+off)))
    return v

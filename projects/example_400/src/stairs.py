"""400 Oak's exterior stair, Unit 3's — the spec carried from 300 S Elm, whose history follows.

The class is arkitect/lib/model/stairs.py; this is this lot's instance of it. Unit 5's stair is
this one with a longer top landing, which is what with_landing() is for.

Both stairs are PRESCRIPTIVE WOOD as of 2026-09-15. They were galvanized steel, drawn
as a deferred fabricator's shop-drawing package, because Unit 5's underside had to be a
listed 1-hour assembly and steel was the way to hang one. Moving the RCO 302.1
imaginary line to 3'-0" off Building 1 (src/fsd.py) put that stair 5'-6" from the line
where Table 302.1(1) asks 5'-0", so the rated underside went — and with it the only
reason either stair was steel. A wood exterior stair is a prescriptive design: RCO
311.7 gives the flight, and the 507 deck provisions give the stringers, the ledger and
its flashing, the posts and the guard post attachment. Nothing here is delegated to a
fabricator's engineer and nothing is a listed assembly.

The words below are the ones the sheets print. They are here rather than typed into
A-001, A-601 and A-604 separately, because three sheets describing one stair in three
sets of words is how a set ends up specifying two different stairs.
"""
from arkitect.lib.units import IN
from src import levels
from arkitect.lib.model.stairs import ExteriorStair


# What the stair is made of, and the code it is designed to. A-001 notes 13a / 13b,
# A-601's fire separation rows, A-604's details and G-001's scope all read these.
MATERIAL   = 'PRESSURE-TREATED WOOD'
STRINGERS  = 'PT 2x12 STRINGERS'
LANDING    = 'PT 2x8 LANDING FRAMING ON A PT LEDGER'
TREADS     = 'COMPOSITE TREADS'
GUARDS     = 'PT OR ALUMINUM GUARDS AND HANDRAILS'
CODE       = 'RCO 311.7 AND THE 507 DECK PROVISIONS'
DESIGN     = 'PRESCRIPTIVELY'
SUBMITTAL  = 'SHOP DRAWING'
# The four things A-604 details, in the order it draws them.
DETAILS    = ('STAIR SECTION — STRINGERS, TREADS AND RISERS',
              'GUARD POST ATTACHMENT',
              'LEDGER AND FLASHING AT THE W1R WALL',
              'PIER CONNECTION')

# One line for a note that has room for one line.
SPEC = '%s: %s, %s, %s, %s' % (MATERIAL, STRINGERS, LANDING, TREADS, GUARDS)


# The stair both buildings use. Unit 5's is this one with a longer top landing; see
# arkitect/lib/model/stairs.py for why that relationship is an object and not six assignments.
# The stoop's top is where every exterior pad's is, 1/2" under a threshold (S-101 note 5),
# so it steps down to grade like the landings, and the flight above it keeps ~8" risers
# whatever the floor's height above grade.
STOOP_TOP = levels.FF1-IN(0.5)
EXT_STAIR = ExteriorStair(risers=15, treads=14, tread=9.25/12.0, width=3.5,
                          landing_len=3.5, landing_depth=3.5, stoop_above_grade=STOOP_TOP,
                          deck=levels.FF2, framing=10.0/12.0,
                          pitch=0.02)   # 2% away from the wall, as the stoop falls: A-001 13a, grading.stair_violations()


class InteriorStair:
    """A straight interior flight between the two floors, and the landings at each end.

    Sizes are what the plan draws: `stud_width` is the column stud face to stud face, and
    the two landings the finished floor each end must give in the direction of travel.
    The riser height is not a figure of its own; it is the floor-to-floor rise shared by
    the risers."""
    def __init__(s, risers, treads, tread, stud_width, foot_landing, top_landing, rise):
        s.risers, s.treads, s.tread = risers, treads, tread
        s.stud_width, s.foot_landing, s.top_landing, s.rise = stud_width, foot_landing, top_landing, rise

    @property
    def run(s):
        return s.treads*s.tread

    @property
    def riser(s):
        return s.rise/s.risers


# 400 Oak's house: 15 risers at 8" and 14 treads at 9-1/4" in a 3'-6" column against the
# left wall (the designer's mockup, 2026-09-17), rising toward the front wall to a 3'-0" landing
# there, its foot in the kitchen (reversed, the designer, 2026-09-18).
B1_STAIR = InteriorStair(risers=15, treads=14, tread=9.25/12.0, stud_width=3.5,
                         foot_landing=3.0, top_landing=3.0, rise=levels.FLOOR_RISE)

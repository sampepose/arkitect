"""The exterior stair, as a thing rather than as eight loose constants.

Both buildings have one and it is the SAME stair: a straight pressure-treated wood
flight from a 6" concrete stoop up to a Level 2 landing, 15 risers at 8" and 14 treads
at 9-1/4", 3'-6" overall for 3'-0" clear between the guards. Unit 3's runs down
Building 1's street face and Unit 5's runs across Building 2's courtyard face, turned
through ninety degrees.

That sameness used to be six assignments of the form `U5_RUN = U3_RUN`, scattered down
build.py, which made Building 2 depend on Building 1 for no reason other than where the
numbers happened to be typed. It is one object now, and Unit 5's stair says what it
actually is: the same stair with a longer top landing.

What is NOT here is placement. Where a stair starts along its wall depends on the plan
behind it — Unit 3's landing is set by the end of the kitchen counter, Unit 5's by the
door jamb — and so do the rating, the fire separation distance and the tag, which
depend on which line the stair is measured to. Those stay with the building.
"""


class ExteriorStair:
    """Straight run, stoop at the bottom, landing at the top, guards both sides.

    risers / treads    one more riser than tread, as always for a straight flight
    tread              going, nosing to nosing
    width              overall projection from the wall, guards included
    landing_len        the top landing's run ALONG the wall
    landing_depth      its projection, and both dimensions of the stoop
    stoop_above_grade  top of the concrete bottom landing
    deck               finished level of the top landing, = the floor it serves
    framing            landing framing depth, deck down to soffit. A wood figure now:
                       a 2x8 joist spanning the 3'-6" landing plus composite decking is
                       8-1/4", inside the 10" the steel package was allowed, so the
                       soffit and every head clearance under it are where they were.
    pitch              the fall of every tread and landing away from the wall, parallel
                       to the stoop's, so each riser is equal at both stringers
    """

    def __init__(s, risers, treads, tread, width, landing_len, landing_depth,
                 stoop_above_grade, deck, framing, pitch):
        s.risers, s.treads, s.tread = risers, treads, tread
        s.width, s.landing_len, s.landing_depth = width, landing_len, landing_depth
        s.stoop_above_grade, s.deck, s.framing, s.pitch = stoop_above_grade, deck, framing, pitch
        assert treads == risers - 1, "a straight flight has one more riser than treads"

    def with_landing(s, landing_len):
        """The same stair with a longer or shorter top landing.

        The landing is the only part either building is free to change: it is set by
        what the landing has to cover — a door alone, or a door and a window — and
        changing it moves the foot of the flight, which is what check_u3_stair_inside
        and check_u5_stair_clear are about.
        """
        return ExteriorStair(s.risers, s.treads, s.tread, s.width, landing_len,
                             s.landing_depth, s.stoop_above_grade, s.deck, s.framing, s.pitch)

    @property
    def run(s):
        """True horizontal length of the flight, nosing of the top tread to the stoop."""
        return s.treads * s.tread

    @property
    def rise(s):
        """Stoop to deck."""
        return s.deck - s.stoop_above_grade

    @property
    def riser(s):
        return s.rise / s.risers

    @property
    def soffit(s):
        """Underside of the top landing deck. Anything below it has to clear it by 6"."""
        return s.deck - s.framing



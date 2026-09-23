"""Finished grading: which way every yard falls, and by how much. C-103 draws it.

RCO 401.3 (the 2018 IRC text): the grade falls not fewer than 6" within the first
10'-0" of a foundation; where lot lines, walls, slopes or other physical barriers
prohibit that, drains or swales carry the water away from the structure; impervious
surfaces within 10'-0" slope not less than 2 percent away from the building.

This lot is 30'-0" wide with 5'-0" side yards, so only Building 1's Oak face and
Building 2's rear face have 10'-0". Every face is described as BANDS — a length of wall
with the same surfaces in front of it — and each band as a SECTION outward from the wall:
points (distance, grade, surface) that end at what receives the water:

  S-1 to S-3   grass swales at 1%: down the north side yard (S-1 beside Building 2, S-3
               beside Building 1 and on across the front yard) with S-2 across the
               courtyard into them, to the Oak lot line.
  W-1          the low edge of the Units 2 and 3 walk, south of Building 1. A walk and a
               swale do not both fit in 5'-0", so the walk falls 2% across to its outer
               edge and 0.5% along it to the Oak sidewalk, carrying only its own yard.
  S-4          a grass swale south of Building 2, to the alley. That yard is a pocket:
               the courtyard walk stands across its way forward, held up by the one
               step off the stoop. The parking pad stands against the NORTH lot line to
               leave it 3'-0", which is also why Building 2's north yard runs forward.

THE CHEAPEST SCHEME THE CODE ALLOWS (the designer, 2026-09-18: "as minimal and as cheap as
possible whilst still following code"). 401.3's exception asks only for swales that carry
the water away, so everything here is graded lawn: no concrete gutter, no inlet, no pipe,
no work in the right-of-way. The first version copied 300 S Elm's concrete gutters to a
catch basin with curb outlets, which answered a Public Service comment on THAT lot, not
the code. A swale yard keeps 2% from the wall, the least any surface here falls; the 6"
is had only where 10'-0" is, at the Oak face. The price of grass is depth: 1% where
concrete ran 0.5%, so the Oak lot line stands about 13-3/4" under the datum, and Unit
1's walk is at 4.9% of its 5%. If the survey puts the sidewalk higher than that, the
buildings come up or S-3 becomes concrete.

Grades are FEET relative to finished grade at the foundation wall, levels.GRADE, and
negative down. The lot has no survey: the lot-line grades here are what the Oak
sidewalk, its curb and the alley must stand at or below, and C-103 says so.

Site feet throughout, as C-101 draws them: x from the north lot line (396 Oak), y from
the Oak lot line toward the alley.
"""
import math
from collections import namedtuple
from arkitect.lib.units import IN, fmt, inches
from src import levels
from src.building2 import U5_FLIGHT_X0, U5_LAND_D, U5_LAND_X0, U5_STAIR
from src.foundation import B1 as B1_FOUNDATION, B2 as B2_FOUNDATION, FLATWORK, FLATWORK_KINDS, LANDING, ROOF_OVERHANG
from src.sitework import (B1_X, B1_Y, B2_X, B2_Y, PARK_X0, PARK_X1, PARK_Y0, PARK_Y1, SITE_BLDG, SITE_D,
                          SITE_W, WALK_COURT, WALK_PARK, WALK_SIDE, WALK_U1)
from src.stairs import STOOP_TOP as _PAD_TOP
from arkitect.lib.model.grade import (Band, LANDING_MAX, TOL, _overlaps, _split, _touch, grade_along, point, signed,
                             stations)
from arkitect.codes.ohio.rco.site_steps import RISER_MAX, feet, stair_risers, stair_violations, step_summary

# ---------------- the rules ----------------
FALL, FALL_RUN = IN(6), 10.0          # R401.3: 6" within the first 10'-0"
FALL_RATE      = FALL/FALL_RUN        # and its rate
IMPERVIOUS_MIN = 0.02                 # R401.3: impervious surfaces within 10'-0", away
WALK_MAX       = 0.05                 # 1 in 20: steeper, and a walk to an egress door reads as a ramp, R311.8
LAWN_MAX       = 1.0/3.0              # 3:1, the steepest bank that can be mowed and will hold seed

# ---------------- the design ----------------
GUTTER_SLOPE = 0.005                  # W-1: concrete holds a flatter line than turf
SWALE_SLOPE = 0.01                    # grass
EXC_RATE = IMPERVIOUS_MIN             # a swale yard's ground at the wall: 401.3's exception names no figure
SWALE_LOT_CLR = 0.5                   # no flowline nearer a side lot line
# The back door is not the required egress door (RCO 311.2): its landing, 311.3, steps onto
# lawn, and no walk crosses swale S-2 to it.
NO_WALK = ("UNIT 1 REAR LANDING",)
ACCESS_MIN = 3.0                      # the least edge a landing or stoop shares with its walk: the door
LANDING_TOP = _PAD_TOP                # 1/2" under the threshold, S-101 note 5
STOOP_TOP   = U5_STAIR.stoop_above_grade
# One step off the stoop and off Unit 2's landing onto the courtyard walk, which puts
# the walk just under finished grade so the ground beside it still falls to it.
STOOP_STEP  = IN(7.75)
U1_WALK_STEP = IN(7.75)               # Unit 1's walk starts one step below its landing
LANDING_SHELF = 2.0                   # beside Unit 1's landing the lawn is held at 2%, so its sides are one step

B1 = next(b for b in SITE_BLDG if b[4] == "BUILDING 1")
B2 = next(b for b in SITE_BLDG if b[4] == "BUILDING 2")
B1X0, B1Y0, B1X1, B1Y1 = B1[0], B1[1], B1[0]+B1[2], B1[1]+B1[3]
B2X0, B2Y0, B2X1, B2Y1 = B2[0], B2[1], B2[0]+B2[2], B2[1]+B2[3]
NORTH_OPEN  = B1X0                    # 5'-0"
SOUTH_OPEN  = SITE_W-B1X1             # 5'-0"
COURT_OPEN  = B2Y0-B1Y1               # 15'-0"
FRONT_OPEN  = B1Y0                    # 25'-0"
REAR_OPEN   = SITE_D-B2Y1             # 18'-0"
GX      = 0.75                        # the north flowline, off the lot line: 1'-3" of lawn past the parking walk
SX      = WALK_SIDE[2]                # W-1: the walk's outer edge
S4X     = SITE_W-1.0                  # S-4's flowline, off the south lot line

STREETS = ("OAK", "ALLEY")

# ---------------- paving: the rectangles C-101 draws ----------------
Rect = namedtuple("Rect", "name kind x0 y0 x1 y1")
def _pad(b, bx, by, name):
    x0, y0, x1, y1, _n = next(q for q in b.pads if q[4] == name)
    return bx+x0, by+y0, bx+x1, by+y1
U1_LANDING = Rect("UNIT 1 LANDING", "landing", *_pad(B1_FOUNDATION, B1_X, B1_Y, "UNIT 1 LANDING"))
U1_REAR    = Rect("UNIT 1 REAR LANDING", "landing", *_pad(B1_FOUNDATION, B1_X, B1_Y, "UNIT 1 REAR LANDING"))
U1_WALK    = Rect("UNIT 1 WALK", "walk", WALK_U1[0], WALK_U1[1], WALK_U1[2], U1_LANDING.y0)
U2_LANDING = Rect("UNIT 2 LANDING", "landing", *_pad(B2_FOUNDATION, B2_X, B2_Y, "UNIT 2 LANDING"))
U3_STOOP   = Rect("UNIT 3 STOOP", "stoop", *_pad(B2_FOUNDATION, B2_X, B2_Y, "UNIT 3 STOOP"))
COURT_WALK = Rect("UNITS 2 AND 3 COURTYARD WALK", "walk", WALK_COURT[0], WALK_COURT[1], WALK_SIDE[0], WALK_COURT[3])
SIDE_WALK  = Rect("UNITS 2 AND 3 WALK", "walk", *WALK_SIDE)
PARK_WALK  = Rect("PARKING WALK", "walk", *WALK_PARK)
PAD        = Rect("PARKING PAD", "pad", PARK_X0, PARK_Y0, PARK_X1, PARK_Y1)
PAVED = [U1_LANDING, U1_REAR, U1_WALK, U2_LANDING, U3_STOOP, COURT_WALK, SIDE_WALK, PARK_WALK, PAD]
assert abs(U1_LANDING.x0-WALK_U1[0]) < TOL and abs(U1_LANDING.x1-WALK_U1[2]) < TOL, "Unit 1's walk is not its landing's width"
assert abs(SIDE_WALK.x1-SX) < TOL, "W-1 is the Units 2 and 3 walk's outer edge"
# a flight has no headroom under it: no walk and no landing may lie there
FLIGHTS = [("UNIT 3 FLIGHT", B2X0+U5_FLIGHT_X0, B2Y0-U5_LAND_D, B2X0+U5_LAND_X0, B2Y0)]

# S-2 crosses the courtyard 5'-0" off Building 1, 3'-6" of lawn clear of the courtyard walk.
COURT_Y = B1Y1+5.0
assert COURT_WALK.y0-COURT_Y >= 1.5-TOL, COURT_Y

# ---------------- gutters ----------------
class Gutter:
    """A straight flowline from its head `a` to its foot `b`, falling `slope` from `start`
       at the head, discharging `to` another's mark or a lot line. `kind`: 'swale', grass;
       'walk', the low edge of a walk; 'gutter', a concrete valley gutter, which this lot
       has none of and which may reach no right-of-way (Public Service, on 300 S Elm)."""
    def __init__(s, mark, a, b, start, to, slope=SWALE_SLOPE, w=0.0, kind="swale"):
        s.mark, s.a, s.b, s.start, s.to, s.slope, s.w, s.kind = mark, a, b, start, to, slope, w, kind
    @property
    def length(s): return math.hypot(s.b[0]-s.a[0], s.b[1]-s.a[1])
    @property
    def end(s): return s.start-s.slope*s.length
    def along(s, x, y):
        dx, dy = s.b[0]-s.a[0], s.b[1]-s.a[1]
        return ((x-s.a[0])*dx+(y-s.a[1])*dy)/s.length
    def off(s, x, y):
        dx, dy = s.b[0]-s.a[0], s.b[1]-s.a[1]
        return abs((x-s.a[0])*dy-(y-s.a[1])*dx)/s.length
    def grade_at(s, x, y): return s.start-s.slope*s.along(x, y)
    def box(s):
        h = s.w/2.0
        return (min(s.a[0], s.b[0])-(h if s.a[1] != s.b[1] else 0.0),
                min(s.a[1], s.b[1])-(h if s.a[0] != s.b[0] else 0.0),
                max(s.a[0], s.b[0])+(h if s.a[1] != s.b[1] else 0.0),
                max(s.a[1], s.b[1])+(h if s.a[0] != s.b[0] else 0.0))

# The north swales start EXC_RATE below the wall at Building 2's rear corner, where the pad
# closes the yard, and the courtyard's likewise at Building 1's south corner.
S1 = Gutter("S-1", (GX, B2Y1), (GX, COURT_Y), -EXC_RATE*(B2X0-GX), "S-3")
S2 = Gutter("S-2", (B1X1, COURT_Y), (GX, COURT_Y), -FALL_RATE*(COURT_Y-B1Y1), "S-3")
S3 = Gutter("S-3", (GX, COURT_Y), (GX, 0.0), min(S1.end, S2.end), "OAK")
FRONT_LOT = S3.end                    # the Oak lot line: what the sidewalk must stand at or below
# W-1: the walk's outer edge. Its head is where the courtyard walk hands over, 2% below
# that walk's far edge; 0.5% beside Building 1, then to the Oak line with the front yard.
_walk_in = STOOP_TOP-U5_LAND_D*LANDING_MAX-STOOP_STEP
_w1_head = _walk_in-2*(COURT_WALK.y1-COURT_WALK.y0)*IMPERVIOUS_MIN
W1A = Gutter("W-1", (SX, COURT_WALK.y0), (SX, B1Y0), _w1_head, "W-1 FRONT", slope=GUTTER_SLOPE, kind="walk")
_w1_front = (W1A.end-(FRONT_LOT-(SIDE_WALK.x1-SIDE_WALK.x0)*IMPERVIOUS_MIN))/B1Y0
W1B = Gutter("W-1 FRONT", (SX, B1Y0), (SX, 0.0), W1A.end, "OAK", slope=_w1_front, kind="walk")
S4 = Gutter("S-4", (S4X, B2Y0), (S4X, SITE_D), -FALL_RATE*(S4X-B2X1), "ALLEY")
GUTTERS = [S1, S2, S3, W1A, W1B, S4]
_G = {g.mark: g for g in GUTTERS}


# ---------------- faces, bands and sections ----------------
# A face runs along `axis` ('x': the wall is a line of constant y) at `at`, and the
# yard in front of it lies toward `sign`. `open` is the room to the lot line or the
# other building.
Face = namedtuple("Face", "building side axis at sign open")

F_B1_FRONT = Face("BUILDING 1", "OAK FACE", "x", B1Y0, -1, FRONT_OPEN)
F_B1_NORTH = Face("BUILDING 1", "NORTH FACE", "y", B1X0, -1, NORTH_OPEN)
F_B1_SOUTH = Face("BUILDING 1", "SOUTH FACE", "y", B1X1, +1, SOUTH_OPEN)
F_B1_REAR  = Face("BUILDING 1", "FACE TO BUILDING 2", "x", B1Y1, +1, COURT_OPEN)
F_B2_FRONT = Face("BUILDING 2", "FACE TO BUILDING 1", "x", B2Y0, -1, COURT_OPEN)
F_B2_NORTH = Face("BUILDING 2", "NORTH FACE", "y", B2X0, -1, NORTH_OPEN)
F_B2_SOUTH = Face("BUILDING 2", "SOUTH FACE", "y", B2X1, +1, SOUTH_OPEN)
F_B2_REAR  = Face("BUILDING 2", "REAR FACE", "x", B2Y1, +1, REAR_OPEN)
FACES = [F_B1_FRONT, F_B1_NORTH, F_B1_SOUTH, F_B1_REAR, F_B2_FRONT, F_B2_NORTH, F_B2_SOUTH, F_B2_REAR]

G0 = levels.GRADE

def _five(d):
    """The lawn grade `d` out on a face that takes 6" in 10'-0"."""
    return G0-FALL*d/FALL_RUN

def _to_swale(face, swale, lead=()):
    """A section that ends on `swale`: whatever `lead` puts in front of the wall, then
       lawn to the flowline."""
    def section(s):
        off = abs((GX if face.axis == "y" else COURT_Y)-face.at)
        return (list(lead) or [(0.0, G0, None)])+[(off, swale.grade_at(*point(face, s, off)), "lawn")]
    return section

def _landing(top, depth=LANDING):
    return [(0.0, top, None), (depth, top-depth*LANDING_MAX, "landing")]

def _landing_edge(depth=LANDING):
    """A landing's outer edge, after its 2% fall."""
    return LANDING_TOP-depth*LANDING_MAX

# The courtyard walk, out from Building 2: its near edge is held one step below the
# stoop's edge, and it falls 2% across to the lawn before S-2.
_walk_d0, _walk_d1 = B2Y0-COURT_WALK.y1, B2Y0-COURT_WALK.y0
_walk = [(_walk_d1, _walk_in-(_walk_d1-_walk_d0)*IMPERVIOUS_MIN, "walk")]
assert abs(U2_LANDING.y0-COURT_WALK.y1) < TOL and abs(U3_STOOP.y0-COURT_WALK.y1) < TOL, \
    "Unit 2's landing and the stoop step down onto the courtyard walk"

def _shelf(*rest):
    return lambda s: [(0.0, G0, None), (LANDING, G0-LANDING*IMPERVIOUS_MIN, "lawn")]+list(rest)

_front_lawn = lambda s: [(0.0, G0, None), (FALL_RUN, _five(FALL_RUN), "lawn"), (FRONT_OPEN, FRONT_LOT, "lawn")]
_front_shelf = _shelf((FALL_RUN, _five(FALL_RUN), "lawn"), (FRONT_OPEN, FRONT_LOT, "lawn"))

_rear_shelf = [(0.0, G0, None), (LANDING, G0-LANDING*IMPERVIOUS_MIN, "lawn")]

def _south_walk(s):
    """South of Building 1: a strip of lawn, then the walk falling 2% to W-1 at its edge."""
    g = W1A.grade_at(SX, s)
    w = SIDE_WALK.x1-SIDE_WALK.x0
    return [(0.0, G0, None), (SIDE_WALK.x0-B1X1, g+w*IMPERVIOUS_MIN, "lawn"), (SX-B1X1, g, "walk")]

BANDS = [
    # Oak: 6" in 10'-0", then to the lot line. Unit 1's walk runs out from its landing, a
    # shelf of lawn beside it on each side.
    *_split(F_B1_FRONT, B1X0, U1_LANDING.x0, U1_LANDING.x0-LANDING_SHELF, U1_LANDING.x0,
            _front_lawn, _front_shelf, "OAK"),
    Band(F_B1_FRONT, U1_LANDING.x0, U1_LANDING.x1,
         lambda s: _landing(LANDING_TOP)+[(LANDING, _landing_edge()-U1_WALK_STEP, "step"), (FRONT_OPEN, FRONT_LOT, "walk")], "OAK"),
    *_split(F_B1_FRONT, U1_LANDING.x1, B1X1, U1_LANDING.x1, U1_LANDING.x1+LANDING_SHELF,
            _front_lawn, _front_shelf, "OAK"),
    # The north side yards: swales S-3 and S-1, the 401.3 exception.
    Band(F_B1_NORTH, B1Y0, B1Y1, _to_swale(F_B1_NORTH, S3), "S-3"),
    # Building 2's carries the parking walk against the wall, level along it and falling 2%
    # across, then lawn to S-1.
    Band(F_B2_NORTH, B2Y0, B2Y1,
         _to_swale(F_B2_NORTH, S1, [(0.0, G0, None), (B2X0-PARK_WALK.x0, G0-(B2X0-PARK_WALK.x0)*IMPERVIOUS_MIN, "walk")]), "S-1"),
    # The south side yards: the walk's edge beside Building 1, the swale beside Building 2.
    Band(F_B1_SOUTH, B1Y0, B1Y1, _south_walk, "W-1"),
    Band(F_B2_SOUTH, B2Y0, B2Y1, lambda s: [(0.0, G0, None), (S4X-B2X1, S4.grade_at(S4X, s), "lawn")], "S-4"),
    # Between the buildings: swale S-2. Building 2's side crosses the courtyard walk first: the
    # stoop and Unit 2's landing step down onto it, and the ground under the flight and
    # at each end of the face is held to it.
    # Unit 1's back door steps off its landing onto lawn held one step below it, a shelf
    # of the same lawn beside it on each side, and on to the swale.
    *_split(F_B1_REAR, B1X0, U1_REAR.x0, U1_REAR.x0-LANDING_SHELF, U1_REAR.x0,
            _to_swale(F_B1_REAR, S2), _to_swale(F_B1_REAR, S2, _rear_shelf), "S-2"),
    Band(F_B1_REAR, U1_REAR.x0, U1_REAR.x1,
         _to_swale(F_B1_REAR, S2, _landing(LANDING_TOP)+[(LANDING, _landing_edge()-U1_WALK_STEP, "step")]), "S-2"),
    *_split(F_B1_REAR, U1_REAR.x1, B1X1, U1_REAR.x1, U1_REAR.x1+LANDING_SHELF,
            _to_swale(F_B1_REAR, S2), _to_swale(F_B1_REAR, S2, _rear_shelf), "S-2"),
    Band(F_B2_FRONT, B2X0, U3_STOOP.x0,
         _to_swale(F_B2_FRONT, S2, [(0.0, G0, None), (_walk_d0, _walk_in, "lawn")]+_walk), "S-2"),
    Band(F_B2_FRONT, U3_STOOP.x0, U3_STOOP.x1,
         _to_swale(F_B2_FRONT, S2, [(0.0, STOOP_TOP, None), (U5_LAND_D, STOOP_TOP-U5_LAND_D*LANDING_MAX, "stoop"),
                                     (U5_LAND_D, _walk_in, "step")]+_walk), "S-2"),
    Band(F_B2_FRONT, U3_STOOP.x1, U2_LANDING.x0,
         _to_swale(F_B2_FRONT, S2, [(0.0, G0, None), (_walk_d0, _walk_in, "lawn")]+_walk), "S-2"),
    Band(F_B2_FRONT, U2_LANDING.x0, U2_LANDING.x1,
         _to_swale(F_B2_FRONT, S2, _landing(LANDING_TOP, _walk_d0)+[(_walk_d0, _walk_in, "step")]+_walk), "S-2"),
    Band(F_B2_FRONT, U2_LANDING.x1, B2X1,
         _to_swale(F_B2_FRONT, S2, [(0.0, G0, None), (_walk_d0, _walk_in, "lawn")]+_walk), "S-2"),
    # Behind Building 2: the pad to the alley, and the lawn beside it over S-4.
    Band(F_B2_REAR, B2X0, min(PAD.x1, B2X1),
         lambda s: [(0.0, G0, None), (REAR_OPEN, G0-REAR_OPEN*IMPERVIOUS_MIN, "pad")], "ALLEY"),
    *([Band(F_B2_REAR, PAD.x1, B2X1,
            lambda s: [(0.0, G0, None), (FALL_RUN, _five(FALL_RUN), "lawn"), (REAR_OPEN, _five(FALL_RUN)-IN(1), "lawn")], "ALLEY")]
      if PAD.x1 < B2X1-TOL else []),
]


# ---------------- the step off every landing and stoop ----------------
# A band sees a landing's or a stoop's step only square to its own face. People step off
# every open side, so each is sampled here: the nosing top on the edge and the grade just
# outside it. The wall side is not open, nor the side a flight lands on. Unit 3's stoop
# straddles Building 1's rear corner, so its side toward Building 2 is open only past
# the wall, and past the wall no face bands the yard: there its foot is held STOOP_STEP
# below its surface. `walk` is the side its walk leaves from, where C-103 spots the foot.
Step = namedtuple("Step", "rect face top edges walk")
_all = (None, None)
STEPS = [
    Step(U1_LANDING, F_B1_FRONT, LANDING_TOP, {"x0": _all, "x1": _all, "y0": _all}, "y0"),
    Step(U1_REAR, F_B1_REAR, LANDING_TOP, {"x0": _all, "x1": _all, "y1": _all}, "y1"),
    Step(U3_STOOP, F_B2_FRONT, STOOP_TOP, {"x0": _all, "y0": _all}, "y0"),
    Step(U2_LANDING, F_B2_FRONT, LANDING_TOP, {"x0": _all, "x1": _all, "y0": _all}, "y0"),
]


def step_violations(steps=None, bands=None):
    v = []
    for st, side, x, y, top, foot, held in feet(steps or STEPS, bands or BANDS, STOOP_STEP):
        at = "%s %s side at %s, %s" % (st.rect.name, side, fmt(x), fmt(y))
        if foot is None:
            v.append("%s: no finished grade at the foot of its step" % at); continue
        if not (0.0 < top-foot <= RISER_MAX+TOL):
            v.append("%s: a step of %s%s (311.7.5.1: over 0 and not over %s)"
                     % (at, "-" if top < foot else "", inches(abs(top-foot)), inches(RISER_MAX)))
    return v


# ---------------- the stairs over the stoops ----------------
# Each stoop falls 2% away from its wall, which is ACROSS the foot of its flight. A level
# bottom tread over it rose 8" at the wall stringer and 8-7/8" at the outer one — past
# 8-1/4" and the 3/8" RCO 311.7.5.1 allows between risers. So every tread and landing of
# the wood stair pitches the same way by the same amount (R311.7.7 allows 2%), and each
# riser is equal at both stringers. The designer's choice; A-001 13a puts it in the shop drawings.
# (name, stair, its stoop, the side of the stoop its flight lands on)
STAIRS = [("UNIT 3 STAIR", U5_STAIR, U3_STOOP, "x1")]


def on_street(name, x, y):
    return {"OAK": abs(y) < TOL, "ALLEY": abs(y-SITE_D) < TOL}.get(name, False)


# ---------------- the checker ----------------
def band_violations(band, gutters=None):
    gutters = {g.mark: g for g in (gutters or GUTTERS)}
    f = band.face; who = "%s %s %s..%s" % (f.building, f.side, fmt(band.s0), fmt(band.s1))
    v = []
    for s in stations(band):
        pts = band.section(s)
        at = "%s at %s" % (who, fmt(s))
        if abs(pts[0][0]) > TOL:
            v.append("%s: the section does not start at the wall" % at); continue
        first = pts[1][2] if len(pts) > 1 else None
        if first in ("landing", "stoop"):
            if pts[0][1] <= G0+TOL: v.append("%s: a %s that is not above grade" % (at, first))
        elif abs(pts[0][1]-G0) > TOL:
            v.append("%s: grade at the foundation is %s, not the finished grade FROST_DEPTH is measured from"
                     % (at, inches(abs(pts[0][1]-G0))))
        earth = False
        for (d0, g0, _a), (d1, g1, kind) in zip(pts, pts[1:]):
            run, fall = d1-d0, g0-g1
            if kind in ("step", "edge"):
                # A step is the one people take off a landing onto its walk; an edge is
                # the side of a pad standing over the lawn, which nobody walks off.
                if abs(run) > TOL: v.append("%s: a %s with a run" % (at, kind))
                if kind == "edge":
                    if fall <= 0.0: v.append("%s: a pad edge below the grade beside it" % at)
                elif not (0.0 < fall <= RISER_MAX+TOL):
                    v.append("%s: a step of %s at %s out (311.7.5.1: over 0 and not over %s)"
                             % (at, inches(abs(fall)), fmt(d0), inches(RISER_MAX)))
                continue
            if run <= TOL:
                v.append("%s: a %s with no run" % (at, kind)); continue
            slope = fall/run
            if slope <= TOL:
                v.append("%s: the %s from %s to %s does not fall away" % (at, kind, fmt(d0), fmt(d1))); continue
            if kind in ("walk", "pad", "gutter") and slope < IMPERVIOUS_MIN-TOL:
                v.append("%s: the %s falls %.1f%%, under the 2%% of 401.3" % (at, kind, 100*slope))
            if kind == "walk" and slope > WALK_MAX+TOL:
                v.append("%s: the walk falls %.1f%%, steeper than 1 in 20" % (at, 100*slope))
            if kind == "lawn" and slope > LAWN_MAX+TOL:
                v.append("%s: the lawn from %s to %s falls %.0f%%, steeper than the 3:1 a bank can be mown at"
                         % (at, fmt(d0), fmt(d1), 100*slope))
            if kind in ("landing", "stoop") and not (IMPERVIOUS_MIN-TOL <= slope <= LANDING_MAX+TOL):
                v.append("%s: the %s falls %.1f%%, not 2%%: 401.3 and 311.3" % (at, kind, 100*slope))
            if kind == "lawn" and d0 < FALL_RUN-TOL: earth = True
        reach = min(FALL_RUN, pts[-1][0])
        if band.to in gutters:
            # 401.3's exception: a swale or drain carries the water away, and the ground at
            # the wall still falls to it
            (d0, g0), (d1, g1, kind) = pts[0][:2], pts[1]
            if kind == "lawn" and (g0-g1)/(d1-d0) < EXC_RATE-TOL:
                v.append("%s: the lawn at the wall falls %.1f%%, under the %.0f%% a swale yard keeps" % (at, 100*(g0-g1)/(d1-d0), 100*EXC_RATE))
        elif earth and G0-grade_along(pts, reach) < FALL-TOL:
            v.append("%s: %s of fall in the first %s, under the 6\" of 401.3"
                     % (at, inches(max(0.0, G0-grade_along(pts, reach))), fmt(reach)))
        # what receives it
        end = point(f, s, pts[-1][0])
        if band.to in STREETS:
            if not on_street(band.to, *end):
                v.append("%s: the section ends at %s, not on the %s lot line" % (at, end, band.to))
        elif band.to in gutters:
            g = gutters[band.to]
            if g.off(*end) > TOL or not (-TOL <= g.along(*end) <= g.length+TOL):
                v.append("%s: the section ends off %s" % (at, band.to))
            elif abs(pts[-1][1]-g.grade_at(*end)) > TOL:
                v.append("%s: the section ends above or below %s's flowline" % (at, band.to))
        else:
            v.append("%s: it drains to %s, which is neither a street, the alley nor a gutter" % (at, band.to))
        if pts[-1][0] < FALL_RUN-TOL and band.to not in STREETS and band.to not in gutters:
            v.append("%s: under 10'-0\" and no drain or swale, 401.3" % at)
    return v


def gutter_violations(gutters=None, paved=None):
    gutters = list(gutters or GUTTERS); paved = PAVED if paved is None else paved
    by = {g.mark: g for g in gutters}
    v = []
    def clashes(name, box):
        for r in paved:
            if _overlaps(box, (r.x0, r.y0, r.x1, r.y1)): v.append("%s: runs through the %s" % (name, r.name))
    for g in gutters:
        least = SWALE_SLOPE if g.kind == "swale" else GUTTER_SLOPE
        if g.slope < least-TOL: v.append("%s: falls %.2f%%, under %.1f%%" % (g.mark, 100*g.slope, 100*least))
        if g.kind == "walk" and g.slope > WALK_MAX+TOL: v.append("%s: the walk falls %.1f%%, steeper than 1 in 20" % (g.mark, 100*g.slope))
        if g.a[0] != g.b[0] and g.a[1] != g.b[1]: v.append("%s: not square to the lot" % g.mark)
        x0, y0, x1, y1 = g.box()
        if x1 > SITE_W-SWALE_LOT_CLR+TOL or x0 < SWALE_LOT_CLR-TOL: v.append("%s: reaches a side lot line" % g.mark)
        if y0 < -TOL or y1 > SITE_D+TOL: v.append("%s: leaves the lot" % g.mark)
        if g.to in by:
            h = by[g.to]
            if math.hypot(g.b[0]-h.a[0], g.b[1]-h.a[1]) > TOL: v.append("%s: does not end at the head of %s" % (g.mark, g.to))
            elif g.end < h.start-TOL: v.append("%s: arrives below the head of %s" % (g.mark, g.to))
        elif g.to in STREETS:
            # Public Service, on 300: no concrete gutter's concentrated flow across a
            # sidewalk or into the alley. Grass and a walk's own runoff reach the lot line.
            if g.kind == "gutter":
                v.append("%s: discharges concentrated flow onto the %s right-of-way" % (g.mark, g.to))
            elif not on_street(g.to, *g.b):
                v.append("%s: does not reach the %s lot line" % (g.mark, g.to))
        else:
            v.append("%s: discharges to %s" % (g.mark, g.to))
        if g.kind != "walk":                       # W-1 is its walk's own edge
            clashes(g.mark, (x0, y0, x1, y1))
    # every flowline reaches a lot line
    for g in gutters:
        seen, h = set(), g
        while h.to in by and h.mark not in seen:
            seen.add(h.mark); h = by[h.to]
        if h.to not in STREETS: v.append("%s: never reaches Oak or the alley" % g.mark)
    return v


def access_violations(paved=None, flights=None):
    """Every landing and stoop steps down onto a walk along ACCESS_MIN of an edge, every
       walk joins other paving, and no walk or landing lies under a stair's flight."""
    paved = PAVED if paved is None else paved
    flights = FLIGHTS if flights is None else flights
    walks = [r for r in paved if r.kind == "walk"]
    v = []
    for r in paved:
        if r.kind in ("landing", "stoop") and r.name not in NO_WALK and max([_touch(r, w) for w in walks] or [0.0]) < ACCESS_MIN-TOL:
            v.append("%s: steps down onto no walk" % r.name)
        if r.kind == "walk" and not any(_touch(r, o) > TOL for o in paved if o is not r):
            v.append("%s: joins no other paving" % r.name)
        if r.kind in ("walk", "landing"):
            for nm, x0, y0, x1, y1 in flights:
                if _overlaps((r.x0, r.y0, r.x1, r.y1), (x0, y0, x1, y1)):
                    v.append("%s: runs under the %s" % (r.name, nm))
    return v


def concrete_violations(paved=None, gutters=None):
    """Every paved rectangle and every gutter is a kind S-101's concrete schedule gives a
       strength to. A new kind of site concrete is not silently poured to nothing."""
    v = []
    for r in (PAVED if paved is None else paved):
        if r.kind not in FLATWORK_KINDS:
            v.append("%s: a %s is outside S-101's %s concrete (%s)"
                     % (r.name, r.kind, FLATWORK.psi, ", ".join(FLATWORK_KINDS)))
    if [g for g in (gutters or GUTTERS) if g.kind == "gutter"] and "gutter" not in FLATWORK_KINDS:
        v.append("the gutters are outside S-101's concrete schedule")
    return v


# ---------------- roof drainage: one leader per eave ----------------
# The trusses bear on the side walls, so each building has a north and a south eave. Each
# gutter falls to ONE leader, placed so its splash block lands on lawn that drains to a
# receiver on the lot: Building 1's south eave cannot use its own side yard, which is the
# walk's, so its leader turns the rear corner into the courtyard.
Leader = namedtuple("Leader", "mark eave x y block to")
SPLASH_W, SPLASH_L = 1.0, 2.0
RAIN_LEADER = 2.8                     # in/h, OPC Appendix B, Columbus, 100-year 1-hour
LEADER, LEADER_GPM = "2 x 3", 30     # OPC Table 1106.3, taken at its 2 x 2 row
EAVE_GUTTER, EAVE_GUTTER_GPM = '5"', 74   # OPC Table 1106.6, semicircular at 1/8" per foot
_h = SPLASH_W/2.0
LEADERS = [
    Leader("DS-1", "BUILDING 1, NORTH EAVE", B1X0, B1Y1-1.0, (B1X0-SPLASH_L, B1Y1-1.0-_h, B1X0, B1Y1-1.0+_h), "S-3"),
    Leader("DS-2", "BUILDING 1, SOUTH EAVE", B1X1-1.0, B1Y1, (B1X1-1.0-_h, B1Y1, B1X1-1.0+_h, B1Y1+SPLASH_L), "S-2"),
    # DS-3 stands over the parking walk: it runs under it in a sleeve to a block on the lawn
    Leader("DS-3", "BUILDING 2, NORTH EAVE", B2X0, B2Y0+1.0, (GX, B2Y0+1.0-_h, PARK_WALK.x0, B2Y0+1.0+_h), "S-1"),
    Leader("DS-4", "BUILDING 2, SOUTH EAVE", B2X1, B2Y1-1.0, (B2X1, B2Y1-1.0-_h, B2X1+SPLASH_L, B2Y1-1.0+_h), "S-4"),
]
SLEEVED = ("DS-3",)       # under a walk in a sleeve, C-103 note 6


def eave_area(ld):
    """The roof one leader drains, SF: half its building's plan to the dripline."""
    b = B1 if ld.eave.startswith("BUILDING 1") else B2
    return (b[2]+2*ROOF_OVERHANG)*(b[3]+2*ROOF_OVERHANG)/2.0


def leader_gpm(ld):
    return eave_area(ld)*RAIN_LEADER/96.23


def leader_violations(leaders=None, paved=None, gutters=None):
    v = []
    by = {g.mark: g for g in (gutters or GUTTERS)}
    for ld in (LEADERS if leaders is None else leaders):
        if ld.to not in by:
            v.append("%s: drains to %s, which is no flowline" % (ld.mark, ld.to)); continue
        x0, y0, x1, y1 = ld.block
        if x0 < -TOL or x1 > SITE_W+TOL or y0 < -TOL or y1 > SITE_D+TOL:
            v.append("%s: its splash block leaves the lot" % ld.mark)
        for r in (PAVED if paved is None else paved):
            if _overlaps(ld.block, (r.x0, r.y0, r.x1, r.y1)): v.append("%s: its splash block is on the %s" % (ld.mark, r.name))
        for g in by.values():
            if g.kind == "gutter" and _overlaps(ld.block, g.box()): v.append("%s: its splash block is on %s" % (ld.mark, g.mark))
        for nm, fx0, fy0, fx1, fy1 in FLIGHTS:
            if fx0-TOL <= ld.x <= fx1+TOL and fy0-TOL <= ld.y <= fy1+TOL: v.append("%s: stands under the %s" % (ld.mark, nm))
        if leader_gpm(ld) > min(LEADER_GPM, EAVE_GUTTER_GPM)+TOL:
            v.append("%s: %.1f gpm, over its leader or gutter, OPC 1106" % (ld.mark, leader_gpm(ld)))
    eaves = sorted(ld.eave for ld in (LEADERS if leaders is None else leaders))
    if eaves != sorted("BUILDING %d, %s EAVE" % (n, sd) for n in (1, 2) for sd in ("NORTH", "SOUTH")):
        v.append("the eaves do not have one leader each: %s" % eaves)
    return v


def grading_violations(bands=None, gutters=None, paved=None):
    v = []
    v += concrete_violations(paved, gutters)
    for b in (bands or BANDS): v += band_violations(b, gutters)
    v += step_violations(None, bands)
    v += stair_violations(STAIRS, STEPS)
    v += gutter_violations(gutters, paved)
    v += access_violations(paved)
    v += leader_violations(None, paved, gutters)
    # every face is banded end to end, once
    for f in FACES:
        bs = sorted((b for b in (bands or BANDS) if b.face == f), key=lambda b: b.s0)
        lo, hi = ((B1X0, B1X1) if f.building == "BUILDING 1" else (B2X0, B2X1)) if f.axis == "x" else \
                 ((B1Y0, B1Y1) if f.building == "BUILDING 1" else (B2Y0, B2Y1))
        edge = lo
        for b in bs:
            if abs(b.s0-edge) > TOL: v.append("%s %s: not banded from %s to %s" % (f.building, f.side, fmt(edge), fmt(b.s0)))
            edge = b.s1
        if abs(edge-hi) > TOL: v.append("%s %s: not banded from %s to %s" % (f.building, f.side, fmt(edge), fmt(hi)))
    return v


# ---------------- what the sheet and the notes read ----------------


def face_summary(f, bands=None):
    """(room, fall range within the reach, method) for one face."""
    bs = [b for b in (bands or BANDS) if b.face == f]
    falls, kinds, tos = [], set(), set()
    for b in bs:
        tos.add(b.to)
        for s in stations(b):
            pts = b.section(s)
            kinds |= {k for _d, _g, k in pts[1:]}
            reach = min(FALL_RUN, pts[-1][0])
            if any(k == "lawn" and d0 < FALL_RUN for (d0, _g0, _a), (_d1, _g1, k) in zip(pts, pts[1:])):
                falls.append((G0-grade_along(pts, reach), reach))
    lo = min(falls) if falls else None; hi = max(falls) if falls else None
    gut = sorted(t for t in tos if t not in STREETS)
    if gut:
        kinds_to = {_G[t].kind for t in gut if t in _G}
        method = "401.3 EXCEPTION — %s %s" % ("WALK EDGE" if kinds_to == {"walk"} else "SWALE", " / ".join(gut))
    elif f.open < FALL_RUN-TOL:
        method = "6\" TO THE %s LOT LINE" % " / ".join(sorted(tos))
    else:
        method = "6\" IN %s" % fmt(FALL_RUN)
    if "pad" in kinds: method += "; PAD 2%"
    elif kinds & {"walk", "landing", "stoop"}: method += "; PAVING 2%"
    if lo is None: fall = "2% PAVED"
    elif abs(lo[0]-hi[0]) < IN(1)/16.0: fall = "%s IN %s" % (inches(lo[0]), fmt(lo[1]))
    else: fall = "%s TO %s IN %s" % (inches(lo[0]), inches(hi[0]), fmt(max(lo[1], hi[1])))
    return fmt(f.open), fall, method


def check_grading():
    """Every band of every face falls away at 401.3's rate to Oak, the alley or a flowline;
       every flowline reaches a lot line; nothing drains onto either neighbor."""
    print("GRADING — RCO 401.3, FROM FINISHED GRADE AT THE FOUNDATION (FF %s):" % signed(levels.FF1))
    for f in FACES:
        room, fall, method = face_summary(f)
        print("   %-10s %-22s %-8s open  %-22s %s" % (f.building, f.side, room, fall, method))
    print("   ONE STEP OFF EACH LANDING AND STOOP, NOT OVER %s (RCO 311.7.5.1):" % inches(RISER_MAX))
    for name, top, nose, foot, step, _w in step_summary(STEPS, BANDS, STOOP_STEP):
        print("   %-18s top %-8s nosing %s..%s  foot %s..%s  step %s..%s"
              % (name, signed(top), signed(nose[0]), signed(nose[1]), signed(foot[0]), signed(foot[1]),
                 inches(step[0]), inches(step[1])))
    for name, pitch, rs in stair_risers(STAIRS, STEPS):
        print("   %-18s treads and landings pitch %.0f%% away from the wall, as its stoop; bottom riser %s..%s"
              % (name, 100*pitch, inches(min(rs)), inches(max(rs))))
    for g in GUTTERS:
        print("   %s  %s .. %s at %.1f%%, %s long, to %s"
              % (g.mark, signed(g.start), signed(g.end), 100*g.slope, fmt(g.length), g.to))
    for ld in LEADERS:
        print("   %s  %-24s %.0f SF, %.1f gpm at %g in/h, to %s" % (ld.mark, ld.eave, eave_area(ld), leader_gpm(ld), RAIN_LEADER, ld.to))
    v = grading_violations()
    assert not v, "grading: %s" % v[:6]

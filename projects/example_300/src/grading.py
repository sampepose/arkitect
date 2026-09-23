"""Finished grading: which way every yard falls, and by how much. C-103 draws it.

RCO 401.3 (the 2018 IRC text): the grade falls not fewer than 6" within the first
10'-0" of a foundation; where lot lines, walls, slopes or other physical barriers
prohibit that, drains or swales carry the water away from the structure; impervious
surfaces within 10'-0" slope not less than 2 percent away from the building.

S-101 note 7 used to state the first sentence for every face of both buildings, and
three kinds of face on this lot cannot have it: the adjacent-parcel faces are 6'-0"
from a lot line that must take no water, the faces between the buildings are 12'-0"
apart, and the Sage faces are 8'-0" from the right-of-way. A plan reviewer said so.

So every face is described here as BANDS — a length of wall with the same surfaces in
front of it — and each band as a SECTION outward from the wall: points (distance,
grade, surface) that end at what receives the water. The adjacent-parcel faces and the
faces between the buildings end at a concrete valley gutter (G-1 to G-3), which is the
401.3 exception, and the gutters end at inlet CB-1 on the lot: Public Service takes no
concentrated flow across a sidewalk, so no gutter may reach a street lot line, and the
lawn past the inlet rises to the S Elm line. The Sage faces take the whole 6" on
the lot and end at the right-of-way, where the new public sidewalk carries on; the S
Elm face and the lawn
behind Building 2 take 6" in 10'-0"; every walk, landing, stoop and the parking pad is
impervious and sloped. check_grading() samples every band at every foot.

Grades are FEET relative to finished grade at the foundation wall, levels.GRADE, and
negative down. FROST_DEPTH is measured from that grade, which is why no earth section
may start below it. The set has no topographic survey: the lot-line grades here are
what the sidewalks and the alley must stand at or below, and C-103 says so.

Site feet throughout, as C-101 draws them: x from the Sage lot line toward the
adjacent parcel, y from the S Elm lot line toward the alley.
"""
import math
from collections import namedtuple
from lib.units import IN, fmt, inches
from src import levels
from src.building1 import ENTRY_LEFT, PLAN_L1, U2_ENTRY, U2_LANDING_DROP, U3_FLIGHT_HI, U3_LAND_HI, U3_STAIR, U3_STOOP_HI, U3_STOOP_Z
from src.building2 import U5_FLIGHT_X0, U5_LAND_D, U5_LAND_X0, U5_STAIR, U5_STOOP_X0, U5_STOOP_Z
from src.drainage import BUILDINGS as DRAIN_BUILDINGS, SEWER_SLOPE, sewer
from lib.model.drains import exit_site
from codes.ohio.opc_drainage import SIZE_IN
from src.foundation import B2 as B2_FOUNDATION, FLATWORK, FLATWORK_KINDS, LANDING
from src.sitework import (PARK_X0, PARK_X1, PARK_Y0, PARK_Y1, SAN_CROSS, SAN_X, SITE_BLDG, SITE_D,
                          SITE_LIVE_X, SITE_STAIR, SITE_W, TREE_R, TREE_X, TREE_Y)
from lib.model.grade import (Band, LANDING_MAX, TOL, _overlaps, _split, _touch, grade_along, point, signed,
                             stations, top_at)
from codes.ohio.rco.site_steps import RISER_MAX, feet, stair_risers, stair_violations, step_summary

# ---------------- the rules ----------------
FALL, FALL_RUN = IN(6), 10.0          # R401.3: 6" within the first 10'-0"
IMPERVIOUS_MIN = 0.02                 # R401.3: impervious surfaces within 10'-0", away
WALK_MAX       = 0.05                 # 1 in 20: steeper, and a walk to an egress door reads as a ramp, R311.8
LAWN_MAX       = 1.0/3.0              # 3:1, the steepest bank that can be mowed and will hold seed

# ---------------- the design ----------------
# A 2'-0" concrete valley gutter, 1-1/2" deep at its flowline, falling 0.5% at least.
# The slope is a design figure, not a code one: concrete holds a flatter line than turf,
# and at the 1% a grass swale needs, G-3 would reach the S Elm lot line about 19"
# below grade.
GUTTER_W, GUTTER_DEPTH, GUTTER_SLOPE = 2.0, IN(1.5), 0.005
# G-1 is narrower. The courtyard is 12'-0" and holds the Unit 3 stoop, which reaches
# 1'-7-3/4" past Building 1's rear wall, and the Units 4 / 5 walk against the Unit 5
# stair's projection: a 2'-0" gutter between them leaves banks no one can mow. The designer's
# choice, 2026-09-15, relayed by the merge coordinator.
COURT_W = 1.0
GUTTER_STOOP_CLR = IN(14)             # G-1's near edge past the Unit 3 stoop's corner
GUTTER_WALK_CLR = 1.0                 # and the lawn it leaves against the walk
STOOP_SHELF = 2.0                     # how far along Building 1's rear face the stoop's shelf runs
GUTTER_T = IN(4)                      # concrete, on compacted subgrade
GUTTER_LOT_CLR = 0.5                  # its far edge short of the adjacent-parcel lot line
INLET_W = GUTTER_W                    # CB-1's square grate, as wide as the gutter it ends
INLET_Y = 5.0                         # CB-1's centre, back from the S Elm lot line
# CB-1's outlet: pipe roof drains to the S Elm curb, Columbus Department of Public
# Service Standard Drawing 2320 — 3" minimum inside diameter PVC at 1.56% under the walk,
# through a core-drilled opening in the curb, parallel 3" pipes where one will not do.
STD2320_D, STD2320_SLOPE = IN(3), 0.0156
PIPE_N     = 0.011                    # Manning's n for PVC, the rough end of its range
INLET_DROP = IN(6)                    # CB-1's rim to its outlet invert: grate, frame and pipe
CURB_OUT   = 10.0                     # the S Elm lot line to the curb face, assumed: no survey
RAIN_I     = 6.85                     # in/hr, NOAA Atlas 14, 10-year 5-minute, at the lot
RUNOFF_C   = 1.0                      # every square foot the gutters gather taken as roof
FRONT_LOT   = -IN(9)                  # the S Elm lot line, 20'-0" out
SAFFORD_LOT = -FALL                   # the Sage lot line: the whole 6" in 8'-0"
U2_WALK_END = -IN(4.5)                # the Unit 2 walk where it meets the public sidewalk
ALLEY_LAWN  = -IN(7)                  # the lawn beside the pad at the alley lot line
ACCESS_MIN  = 3.0                     # the least edge a landing or stoop shares with its walk: the door
LANDING_TOP = levels.FF1-U2_LANDING_DROP
assert math.isclose(U3_STOOP_Z, U5_STOOP_Z), "the two stoops are no longer the same height"
STOOP_TOP   = U3_STOOP_Z
# The one step off each stoop, which A-001 13a, C-101 and both stair elevations print.
# The stoop height is the stair's, 1/2" under a threshold like the landings' (stairs.
# STOOP_TOP), so the grade at the foot is held at finished grade, the stoop's whole
# height below its surface, rather than a second riser added.
STOOP_STEP  = STOOP_TOP-levels.GRADE

# ---------------- the lot ----------------
B1 = next(b for b in SITE_BLDG if b[4] == "BUILDING 1")
B2 = next(b for b in SITE_BLDG if b[4] == "BUILDING 2")
B1X0, B1Y0, B1X1, B1Y1 = B1[0], B1[1], B1[0]+B1[2], B1[1]+B1[3]
B2X0, B2Y0, B2X1, B2Y1 = B2[0], B2[1], B2[0]+B2[2], B2[1]+B2[3]
assert B1X0 == B2X0 and B1X1 == B2X1, "the buildings no longer share their side faces"
# The Unit 2 walk, the Unit 3 stair and its walk are on Sage. If the sheet mirror
# puts them on the adjacent-parcel side, every band on both side faces is wrong.
assert math.isclose(SITE_LIVE_X, B1X0) and SITE_STAIR[1] <= B1X0+TOL, \
    "the Unit 2 / Unit 3 entries are no longer on the Sage face: re-band src/grading.py"
SAFF_OPEN   = B1X0                    # 8'-0"
PARCEL_OPEN = SITE_W-B1X1             # 6'-0"
COURT_OPEN  = B2Y0-B1Y1               # 12'-0"
FRONT_OPEN  = B1Y0                    # 20'-0"
REAR_OPEN   = SITE_D-B2Y1             # 18'-0"
GX      = SITE_W-GUTTER_LOT_CLR-GUTTER_W/2.0   # the parcel-side flowline, 4'-6" off the faces

STREETS = ("S ELM", "SAGE", "ALLEY")

# Everything paved in the yards, as C-101 draws it. (name, kind, x0, y0, x1, y1)
Rect = namedtuple("Rect", "name kind x0 y0 x1 y1")
_u1x = B1X0+ENTRY_LEFT
U1_LANDING = Rect("UNIT 1 LANDING", "landing", _u1x, B1Y0-LANDING, _u1x+LANDING, B1Y0)
U1_WALK    = Rect("UNIT 1 WALK", "walk", _u1x, 0.0, _u1x+3.0, B1Y0-LANDING)
_u2c = B1Y0+PLAN_L1.y(U2_ENTRY[1])+U2_ENTRY[2]/2.0          # centred on the Unit 2 door
U2_LANDING = Rect("UNIT 2 LANDING", "landing", B1X0-LANDING, _u2c-LANDING/2, B1X0, _u2c+LANDING/2)
U2_WALK    = Rect("UNIT 2 WALK", "walk", 0.0, _u2c-LANDING/2, B1X0-LANDING, _u2c+LANDING/2)
U3_STOOP   = Rect("UNIT 3 STOOP", "stoop", SITE_STAIR[0], B1Y0+U3_FLIGHT_HI, SITE_STAIR[1], B1Y0+U3_STOOP_HI)
U3_WALK    = Rect("UNIT 3 WALK", "walk", SITE_STAIR[0]+0.25, B1Y0+U3_STOOP_HI, SITE_STAIR[0]+3.25, B2Y1)
U5_STOOP   = Rect("UNIT 5 STOOP", "stoop", B2X0+U5_STOOP_X0, B2Y0-U5_LAND_D, B2X0+U5_FLIGHT_X0, B2Y0)
# Unit 4's landing is the pad S-101 casts, out to the edge of the Unit 5 top landing.
_u4 = {nm: (x0, y0, x1, y1) for x0, y0, x1, y1, nm in B2_FOUNDATION.pads}["UNIT 4 LANDING"]
U4_LANDING = Rect("UNIT 4 LANDING", "landing", B2X0+_u4[0], B2Y0+_u4[1], B2X0+_u4[2], B2Y0+_u4[3])
# The Units 4 and 5 walk runs beside the Unit 5 stair, against its projection, from the
# Unit 3 walk to the far side of Unit 4's landing. Under the stair it had no headroom:
# the flight's soffit falls to the stoop. Unit 5's walk joins its stoop to the Unit 3 walk.
U45_WALK   = Rect("UNITS 4 AND 5 WALK", "walk", U3_WALK.x1, U5_STOOP.y0-3.0, U4_LANDING.x1, U5_STOOP.y0)
U5_WALK    = Rect("UNIT 5 WALK", "walk", U3_WALK.x1, U5_STOOP.y0, U5_STOOP.x0, B2Y0)
assert abs(U4_LANDING.y0-U5_STOOP.y0) < TOL, "Unit 4's landing no longer reaches the edge of the Unit 5 stair"
PAD        = Rect("PARKING PAD", "pad", PARK_X0, PARK_Y0, PARK_X1, PARK_Y1)
PAVED = [U1_LANDING, U1_WALK, U2_LANDING, U2_WALK, U3_STOOP, U3_WALK, U5_STOOP, U5_WALK, U45_WALK, U4_LANDING, PAD]
assert PAD.y0 == B2Y1 and B2X0 < PAD.x0 < B2X1, "the parking pad no longer starts at Building 2's rear face"
# Each exterior stair's flight in plan, (name, x0, y0, x1, y1): nothing walked on goes under one.
FLIGHTS = [("UNIT 3 FLIGHT", SITE_STAIR[0], B1Y0+U3_LAND_HI, SITE_STAIR[1], B1Y0+U3_FLIGHT_HI),
           ("UNIT 5 FLIGHT", B2X0+U5_FLIGHT_X0, B2Y0-U5_LAND_D, B2X0+U5_LAND_X0, B2Y0)]
# G-1's flowline: midway between Building 1's rear face and the Units 4 and 5 walk, which
# takes the 3'-0" beside the Unit 5 stair, so G-1 cannot run midway between the buildings.
# G-1 stands clear of the Unit 3 stoop's corner rather than midway between Building 1 and
# the walk: midway left its edge 1-1/4" off that corner, where the ground fell 10-1/4" off
# the stoop. Read from the stoop, so moving the stoop moves the gutter.
COURT_Y = U3_STOOP.y1+GUTTER_STOOP_CLR+COURT_W/2.0
assert U45_WALK.y0-(COURT_Y+COURT_W/2.0) >= GUTTER_WALK_CLR-TOL, \
    "G-1 leaves under %s of lawn against the Units 4 / 5 walk" % fmt(GUTTER_WALK_CLR)

# The four cleanouts, where C-101 draws them: outside the Building 1 exit, at the bend
# into the side yard, at Building 2's junction and short of the rear lot line.
_x1, _y1 = exit_site(DRAIN_BUILDINGS[0]); _x2, _y2 = exit_site(DRAIN_BUILDINGS[1])
CLEANOUTS = [(_x1, _y1+1.0), (SAN_X, SAN_CROSS), (SAN_X, _y2), (SAN_X, 115.0)]
CO_R = 0.55


# ---------------- gutters ----------------
class Gutter:
    """A straight concrete valley gutter from its head `a` to its foot `b`, falling
       `slope` from `start` at the head, discharging `to` another gutter's mark or a
       street lot line."""
    def __init__(s, mark, a, b, start, to, slope=GUTTER_SLOPE, w=GUTTER_W):
        s.mark, s.a, s.b, s.start, s.to, s.slope, s.w = mark, a, b, start, to, slope, w
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

G1 = Gutter("G-1", (B1X0, COURT_Y), (GX, COURT_Y), -FALL, "G-3", w=COURT_W)
G2 = Gutter("G-2", (GX, B2Y1), (GX, COURT_Y), -FALL, "G-3")
G3 = Gutter("G-3", (GX, COURT_Y), (GX, INLET_Y), min(G1.end, G2.end), "CB-1")
GUTTERS = [G1, G2, G3]
_G = {g.mark: g for g in GUTTERS}

# The gutters' one outlet: a grated inlet on the lot at G-3's foot, its rim at the
# flowline. `at` is its centre, `size` its square grate.
Inlet = namedtuple("Inlet", "mark at size rim")
INLET = Inlet("CB-1", G3.b, INLET_W, G3.end)
INLETS = [INLET]

def inlet_box(i):
    h = i.size/2.0
    return (i.at[0]-h, i.at[1]-h, i.at[0]+h, i.at[1]+h)


def tributary():
    """(yard, roof) in SF, taken whole: the adjacent-parcel yard from CB-1 to Building 2's
       rear face, the yard between the buildings, and both buildings' roof plans to the
       dripline wherever their downspouts land."""
    from src.roof import ROOFS, plan_area
    yard = (SITE_W-B1X1)*(B2Y1-INLET.at[1])+(B1X1-B1X0)*(B2Y0-B1Y1)
    return yard, sum(plan_area(r) for r in ROOFS)


def outlet(pipes=None, slope=STD2320_SLOPE, d=STD2320_D, inlet=None):
    """CB-1's pipe roof drains to the S Elm curb: the flow on the tributary (cfs, C i A),
       what one pipe carries full (Manning), how many that takes, and the invert at CB-1,
       the crown at the lot line and the invert at the curb face — feet from the datum."""
    i = inlet or INLET
    area = sum(tributary())
    flow = RUNOFF_C*RAIN_I/12.0/3600.0*area
    q_pipe = 1.486/PIPE_N*(math.pi*d*d/4.0)*(d/4.0)**(2.0/3.0)*math.sqrt(slope)
    need = int(math.ceil(flow/q_pipe-TOL))
    inv = i.rim-INLET_DROP
    return dict(area=area, flow=flow, q_pipe=q_pipe, need=need, pipes=need if pipes is None else pipes,
                invert_inlet=inv, crown_lot=inv-slope*i.at[1]+d, invert_curb=inv-slope*(i.at[1]+CURB_OUT))


def outlet_violations(walk=None, **kw):
    """The pipes against Standard Drawing 2320, the flow, and the sidewalk over them."""
    o = outlet(**kw); walk = FRONT_LOT if walk is None else walk
    d, slope = kw.get("d", STD2320_D), kw.get("slope", STD2320_SLOPE)
    v = []
    if d < STD2320_D-TOL:
        v.append('CB-1 outlet: a %s pipe, under the 3" minimum of Standard Drawing 2320' % inches(d))
    if abs(slope-STD2320_SLOPE) > TOL:
        v.append("CB-1 outlet: pipes at %.2f%%, not the 1.56%% of Standard Drawing 2320" % (100*slope))
    if o["pipes"]*o["q_pipe"] < o["flow"]-TOL:
        v.append("CB-1 outlet: %d pipes carry %.2f cfs, under the %.2f cfs on %.0f SF"
                 % (o["pipes"], o["pipes"]*o["q_pipe"], o["flow"], o["area"]))
    if o["crown_lot"] >= walk-TOL:
        v.append("CB-1 outlet: the pipe has no cover under the S ELM sidewalk at the lot line")
    return v


# ---------------- faces, bands and sections ----------------
# A face runs along `axis` ('x': the wall is a line of constant y) at `at`, and the
# yard in front of it lies toward `sign`. `open` is the room to the lot line or the
# other building.
Face = namedtuple("Face", "building side axis at sign open")

F_B1_FRONT  = Face("BUILDING 1", "S ELM FACE", "x", B1Y0, -1, FRONT_OPEN)
F_B1_SAFF   = Face("BUILDING 1", "SAGE FACE", "y", B1X0, -1, SAFF_OPEN)
F_B1_PARCEL = Face("BUILDING 1", "ADJACENT-PARCEL FACE", "y", B1X1, +1, PARCEL_OPEN)
F_B1_REAR   = Face("BUILDING 1", "FACE TO BUILDING 2", "x", B1Y1, +1, COURT_OPEN)
F_B2_FRONT  = Face("BUILDING 2", "FACE TO BUILDING 1", "x", B2Y0, -1, COURT_OPEN)
F_B2_SAFF   = Face("BUILDING 2", "SAGE FACE", "y", B2X0, -1, SAFF_OPEN)
F_B2_PARCEL = Face("BUILDING 2", "ADJACENT-PARCEL FACE", "y", B2X1, +1, PARCEL_OPEN)
F_B2_REAR   = Face("BUILDING 2", "REAR FACE", "x", B2Y1, +1, REAR_OPEN)
FACES = [F_B1_FRONT, F_B1_SAFF, F_B1_PARCEL, F_B1_REAR, F_B2_FRONT, F_B2_SAFF, F_B2_PARCEL, F_B2_REAR]

G0 = levels.GRADE

def _five(d):
    """The lawn grade `d` out on a face that takes 6" in 10'-0"."""
    return G0-FALL*d/FALL_RUN

def _to_gutter(face, gutter, lead=()):
    """A section that ends on `gutter`: whatever `lead` puts in front of the wall, then
       lawn to the gutter's edge and down its side to the flowline."""
    def section(s):
        off = abs((GX if face.axis == "y" else COURT_Y)-face.at)
        g = gutter.grade_at(*point(face, s, off))
        pts = list(lead) or [(0.0, G0, None)]
        return pts+[(off-gutter.w/2.0, g+GUTTER_DEPTH, "lawn"), (off, g, "gutter")]
    return section

def _landing(top, depth=LANDING):
    return [(0.0, top, None), (depth, top-depth*LANDING_MAX, "landing")]

def _landing_edge(depth=LANDING):
    """A landing's outer edge, after its 2% fall."""
    return LANDING_TOP-depth*LANDING_MAX

# The walks off the two Building 1 landings start where the one step off the landing
# leaves them (the floor stands +8-1/4", the designer 2026-09-18, so following the lawn's 6"-in-10'
# line from the wall stepped 8-7/8" and 9-1/4"). Unit 1's is held a 7-3/4" step below its
# landing and falls to the S Elm lot line; Unit 2's, 5'-0" long to the public sidewalk,
# starts as high as the walk's 1 in 20 allows back from the sidewalk (step 8").
U1_WALK_STEP = IN(7.75)

_stoop_d = B1X0-U3_STOOP.x0
_u3_walk_d = B2X0-U3_WALK.x0
# The Units 4 and 5 walk, out from Building 2: its near edge is held one stoop step below
# the Unit 5 stoop's edge, and it falls 2% across to the lawn before G-1.
_walk_d0, _walk_d1 = B2Y0-U45_WALK.y1, B2Y0-U45_WALK.y0
_walk_in = STOOP_TOP-U5_LAND_D*LANDING_MAX-STOOP_STEP
_walk = [(_walk_d1, _walk_in-(_walk_d1-_walk_d0)*IMPERVIOUS_MIN, "walk")]

# Beside each Building 1 landing the lawn is held on a SHELF for LANDING_SHELF along the
# face: it falls 2% for the landing's depth, as the landing does, and only then goes on to
# 6" at 10'-0" -- so every open side of the landing is one step, not over 8-1/4", with the
# floor at +8-1/4" (the designer, 2026-09-18). Unit 4's landing has held its lawn the same way.
LANDING_SHELF = 2.0

def _shelf(*rest):
    return lambda s: [(0.0, G0, None), (LANDING, G0-LANDING*IMPERVIOUS_MIN, "lawn")]+list(rest)

_front_lawn = lambda s: [(0.0, G0, None), (FALL_RUN, _five(FALL_RUN), "lawn"), (FRONT_OPEN, FRONT_LOT, "lawn")]
_front_shelf = _shelf((FALL_RUN, _five(FALL_RUN), "lawn"), (FRONT_OPEN, FRONT_LOT, "lawn"))
_saff_lawn = lambda s: [(0.0, G0, None), (SAFF_OPEN, SAFFORD_LOT, "lawn")]
_saff_shelf = _shelf((SAFF_OPEN, SAFFORD_LOT, "lawn"))

BANDS = [
    # S Elm: 6" in 10'-0", then to the lot line. Unit 1's walk runs out from its landing,
    # a shelf of lawn beside it on each side.
    *_split(F_B1_FRONT, B1X0, U1_LANDING.x0, U1_LANDING.x0-LANDING_SHELF, U1_LANDING.x0,
            _front_lawn, _front_shelf, "S ELM"),
    Band(F_B1_FRONT, U1_LANDING.x0, U1_LANDING.x1,
         lambda s: _landing(LANDING_TOP)+[(LANDING, _landing_edge()-U1_WALK_STEP, "step"), (FRONT_OPEN, FRONT_LOT, "walk")], "S ELM"),
    *_split(F_B1_FRONT, U1_LANDING.x1, B1X1, U1_LANDING.x1, U1_LANDING.x1+LANDING_SHELF,
            _front_lawn, _front_shelf, "S ELM"),
    # Sage, Building 1: the whole 6" in the 8'-0" to the lot line. Unit 2's landing
    # and walk, and the foot of the Unit 3 stair, interrupt the lawn.
    *_split(F_B1_SAFF, B1Y0, U2_LANDING.y0, U2_LANDING.y0-LANDING_SHELF, U2_LANDING.y0,
            _saff_lawn, _saff_shelf, "SAGE"),
    Band(F_B1_SAFF, U2_LANDING.y0, U2_LANDING.y1,
         lambda s: _landing(LANDING_TOP)+[(LANDING, U2_WALK_END+WALK_MAX*(SAFF_OPEN-LANDING), "step"),
                                           (SAFF_OPEN, U2_WALK_END, "walk")], "SAGE"),
    *_split(F_B1_SAFF, U2_LANDING.y1, U3_STOOP.y0, U2_LANDING.y1, U2_LANDING.y1+LANDING_SHELF,
            _saff_lawn, _saff_shelf, "SAGE"),
    Band(F_B1_SAFF, U3_STOOP.y0, B1Y1,
         lambda s: [(0.0, STOOP_TOP, None), (_stoop_d, STOOP_TOP-_stoop_d*LANDING_MAX, "stoop"),
                    (_stoop_d, STOOP_TOP-_stoop_d*LANDING_MAX-STOOP_STEP, "step"), (SAFF_OPEN, SAFFORD_LOT, "lawn")], "SAGE"),
    # The adjacent parcel takes nothing: G-3 and G-2, the R401.3 exception.
    Band(F_B1_PARCEL, B1Y0, B1Y1, _to_gutter(F_B1_PARCEL, G3), "G-3"),
    Band(F_B2_PARCEL, B2Y0, B2Y1, _to_gutter(F_B2_PARCEL, G2), "G-2"),
    # Between the buildings: G-1, midway between Building 1 and the Units 4 and 5 walk.
    # Building 2's side crosses the walk first: Unit 5's walk falls to it, the stoop and
    # Unit 4's landing step down onto it, and the ground under the flight falls to it.
    # The Unit 3 stoop stands in the Sage end of this yard: beside it the ground falls
    # at the paving's 2% as far out as the stoop reaches, so the stoop's side is one step,
    # and then to G-1. Past the stoop the yard runs straight to the gutter — carrying the
    # shelf along the whole face would bank the rest of it steeper than 3:1.
    Band(F_B1_REAR, B1X0, B1X0+STOOP_SHELF,
         _to_gutter(F_B1_REAR, G1, [(0.0, G0, None),
                                    (U3_STOOP.y1-B1Y1, G0-(U3_STOOP.y1-B1Y1)*IMPERVIOUS_MIN, "lawn")]), "G-1"),
    Band(F_B1_REAR, B1X0+STOOP_SHELF, B1X1, _to_gutter(F_B1_REAR, G1), "G-1"),
    Band(F_B2_FRONT, B2X0, U5_STOOP.x0,
         _to_gutter(F_B2_FRONT, G1, [(0.0, G0, None), (_walk_d0, _walk_in, "walk")]+_walk), "G-1"),
    Band(F_B2_FRONT, U5_STOOP.x0, U5_STOOP.x1,
         _to_gutter(F_B2_FRONT, G1, [(0.0, STOOP_TOP, None), (U5_LAND_D, STOOP_TOP-U5_LAND_D*LANDING_MAX, "stoop"),
                                     (U5_LAND_D, _walk_in, "step")]+_walk), "G-1"),
    Band(F_B2_FRONT, U5_STOOP.x1, U4_LANDING.x0,
         _to_gutter(F_B2_FRONT, G1, [(0.0, G0, None), (_walk_d0, _walk_in, "lawn")]+_walk), "G-1"),
    Band(F_B2_FRONT, U4_LANDING.x0, U4_LANDING.x1,
         _to_gutter(F_B2_FRONT, G1, _landing(LANDING_TOP, _walk_d0)+[(_walk_d0, _walk_in, "step")]+_walk), "G-1"),
    # Beside Unit 4's landing the ground is held at the walk's grade out to the landing's
    # edge, so the landing's side is no higher a step than its front.
    Band(F_B2_FRONT, U4_LANDING.x1, B2X1,
         _to_gutter(F_B2_FRONT, G1, [(0.0, G0, None), (_walk_d0, _walk_in, "lawn")]), "G-1"),
    # Sage, Building 2: the Unit 3 walk along the wall at 2%, then lawn to the lot line.
    Band(F_B2_SAFF, B2Y0, B2Y1,
         lambda s: [(0.0, G0, None), (_u3_walk_d, G0-_u3_walk_d*IMPERVIOUS_MIN, "walk"),
                    (SAFF_OPEN, SAFFORD_LOT, "lawn")], "SAGE"),
    # Behind Building 2: the lawn strip on the Sage side, and the pad to the alley.
    Band(F_B2_REAR, B2X0, PAD.x0,
         lambda s: [(0.0, G0, None), (FALL_RUN, _five(FALL_RUN), "lawn"), (REAR_OPEN, ALLEY_LAWN, "lawn")], "ALLEY"),
    Band(F_B2_REAR, PAD.x0, B2X1,
         lambda s: [(0.0, G0, None), (REAR_OPEN, G0-REAR_OPEN*IMPERVIOUS_MIN, "pad")], "ALLEY"),
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
    Step(U2_LANDING, F_B1_SAFF, LANDING_TOP, {"x0": _all, "y0": _all, "y1": _all}, "x0"),
    Step(U3_STOOP, F_B1_SAFF, STOOP_TOP, {"x0": _all, "y1": _all, "x1": (B1Y1, None)}, "y1"),
    Step(U5_STOOP, F_B2_FRONT, STOOP_TOP, {"x0": _all, "y0": _all}, "x0"),
    Step(U4_LANDING, F_B2_FRONT, LANDING_TOP, {"x0": _all, "x1": _all, "y0": _all}, "y0"),
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
        if held and foot <= SAFFORD_LOT+TOL:
            v.append("%s: a held foot at %s cannot fall to the Sage lot line" % (at, signed(foot)))
    # The Unit 3 walk leaves its stoop past Building 1's rear wall, where its head is held,
    # and runs on along Building 2's Sage face, where a band grades it: the two agree.
    b2 = next((b for b in (bands or BANDS) if b.face == F_B2_SAFF), None)
    u3 = next((s for s in (steps or STEPS) if s.rect is U3_STOOP), None)
    if b2 is not None and u3 is not None:
        for x in (U3_WALK.x0, U3_WALK.x1):
            head = top_at(u3, x, U3_STOOP.y1)-STOOP_STEP
            if abs(head-grade_along(b2.section(B2Y0), B2X0-x)) > TOL:
                v.append("UNIT 3 WALK at %s: its head at the stoop is not level with its section along Building 2" % fmt(x))
    return v


# ---------------- the stairs over the stoops ----------------
# Each stoop falls 2% away from its wall, which is ACROSS the foot of its flight. A level
# bottom tread over it rose 8" at the wall stringer and 8-7/8" at the outer one — past
# 8-1/4" and the 3/8" RCO 311.7.5.1 allows between risers. So every tread and landing of
# the wood stair pitches the same way by the same amount (R311.7.7 allows 2%), and each
# riser is equal at both stringers. The designer's choice; A-001 13a puts it in the shop drawings.
# (name, stair, its stoop, the side of the stoop its flight lands on)
STAIRS = [("UNIT 3 STAIR", U3_STAIR, U3_STOOP, "y0"), ("UNIT 5 STAIR", U5_STAIR, U5_STOOP, "x1")]


def on_street(name, x, y):
    return {"S ELM": abs(y) < TOL, "SAGE": abs(x) < TOL, "ALLEY": abs(y-SITE_D) < TOL}.get(name, False)


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
        if earth and G0-grade_along(pts, reach) < FALL-TOL:
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


def gutter_violations(gutters=None, paved=None, inlets=None):
    gutters = list(gutters or GUTTERS); paved = PAVED if paved is None else paved
    by = {g.mark: g for g in gutters}
    inl = {i.mark: i for i in (inlets or INLETS)}
    v = []
    def clashes(name, box):
        for r in paved:
            if _overlaps(box, (r.x0, r.y0, r.x1, r.y1)): v.append("%s: runs through the %s" % (name, r.name))
        if _overlaps(box, (TREE_X-TREE_R, TREE_Y-TREE_R, TREE_X+TREE_R, TREE_Y+TREE_R)):
            v.append("%s: runs under the tree canopy" % name)
        for cx, cy in CLEANOUTS:
            if box[0]-CO_R < cx < box[2]+CO_R and box[1]-CO_R < cy < box[3]+CO_R:
                v.append("%s: over the cleanout at %s, %s" % (name, fmt(cx), fmt(cy)))
    for g in gutters:
        if g.slope < GUTTER_SLOPE-TOL: v.append("%s: falls %.2f%%, under %.1f%%" % (g.mark, 100*g.slope, 100*GUTTER_SLOPE))
        if g.a[0] != g.b[0] and g.a[1] != g.b[1]: v.append("%s: not square to the lot" % g.mark)
        x0, y0, x1, y1 = g.box()
        if x1 > SITE_W-GUTTER_LOT_CLR+TOL: v.append("%s: reaches the adjacent-parcel lot line" % g.mark)
        if x0 < -TOL or y0 < -TOL or y1 > SITE_D+TOL: v.append("%s: leaves the lot" % g.mark)
        if g.to in by:
            h = by[g.to]
            if math.hypot(g.b[0]-h.a[0], g.b[1]-h.a[1]) > TOL: v.append("%s: does not end at the head of %s" % (g.mark, g.to))
            elif g.end < h.start-TOL: v.append("%s: arrives below the head of %s" % (g.mark, g.to))
        elif g.to in inl:
            i = inl[g.to]
            if math.hypot(g.b[0]-i.at[0], g.b[1]-i.at[1]) > TOL: v.append("%s: does not end at inlet %s" % (g.mark, g.to))
            elif abs(g.end-i.rim) > TOL: v.append("%s: arrives above or below the rim of %s" % (g.mark, g.to))
        elif g.to in STREETS:
            # Public Service: no concentrated flow across the sidewalk or into the alley.
            v.append("%s: discharges concentrated flow onto the %s right-of-way" % (g.mark, g.to))
        else:
            v.append("%s: discharges to %s" % (g.mark, g.to))
        clashes(g.mark, (x0, y0, x1, y1))
    # every gutter reaches an inlet
    for g in gutters:
        seen, h = set(), g
        while h.to in by and h.mark not in seen:
            seen.add(h.mark); h = by[h.to]
        if h.to not in inl: v.append("%s: never reaches an inlet" % g.mark)
    # each inlet sits on the lot, and the lawn past it rises to the street it stands short of
    for i in inl.values():
        x0, y0, x1, y1 = inlet_box(i)
        if x0 < -TOL or y0 < TOL or y1 > SITE_D+TOL: v.append("%s: leaves the lot" % i.mark)
        if x1 > SITE_W-GUTTER_LOT_CLR+TOL: v.append("%s: reaches the adjacent-parcel lot line" % i.mark)
        if FRONT_LOT-(i.rim+GUTTER_DEPTH) <= TOL:
            v.append("%s: the lawn past it does not rise to the S ELM lot line (rim %s, lot line %s)"
                     % (i.mark, signed(i.rim), signed(FRONT_LOT)))
        clashes(i.mark, (x0, y0, x1, y1))
    return v


def sewer_crossings(gutters=None):
    """Where a gutter crosses the building sewer or Building 2's lateral: the point, the
       flowline and the cover from it to the crown. Feet."""
    sw = sewer()
    out = []
    def walk(path, inv0, slope):
        run = 0.0
        for (ax, ay), (bx, by) in zip(path, path[1:]):
            seg = math.hypot(bx-ax, by-ay)
            for g in (gutters or GUTTERS):
                x0, y0, x1, y1 = g.a[0], g.a[1], g.b[0], g.b[1]
                if ax == bx and y0 == y1 and min(x0, x1)-TOL <= ax <= max(x0, x1)+TOL and min(ay, by)-TOL <= y0 <= max(ay, by)+TOL:
                    p = (ax, y0)
                elif ay == by and x0 == x1 and min(y0, y1)-TOL <= ay <= max(y0, y1)+TOL and min(ax, bx)-TOL <= x0 <= max(ax, bx)+TOL:
                    p = (x0, ay)
                else:
                    continue
                crown = inv0-slope*(run+math.hypot(p[0]-ax, p[1]-ay))+IN(SIZE_IN['4'])
                out.append((g.mark, p, g.grade_at(*p), g.grade_at(*p)-crown))
            run += seg
    walk(sw['route'], sw['exit1'], SEWER_SLOPE/12.0)
    walk(sw['lateral'], sw['exit2'], sw['lateral_fall']/math.hypot(*[a-b for a, b in zip(*sw['lateral'])]))
    return out


def access_violations(paved=None, flights=None):
    """Every landing and stoop steps down onto a walk along ACCESS_MIN of an edge, every
       walk joins other paving, and no walk or landing lies under a stair's flight."""
    paved = PAVED if paved is None else paved
    flights = FLIGHTS if flights is None else flights
    walks = [r for r in paved if r.kind == "walk"]
    v = []
    for r in paved:
        if r.kind in ("landing", "stoop") and max([_touch(r, w) for w in walks] or [0.0]) < ACCESS_MIN-TOL:
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
    if list(gutters or GUTTERS) and "gutter" not in FLATWORK_KINDS:
        v.append("the gutters are outside S-101's concrete schedule")
    return v


def grading_violations(bands=None, gutters=None, paved=None, inlets=None):
    v = []
    v += concrete_violations(paved, gutters)
    for b in (bands or BANDS): v += band_violations(b, gutters)
    v += step_violations(None, bands)
    v += stair_violations(STAIRS, STEPS)
    v += gutter_violations(gutters, paved, inlets)
    v += outlet_violations()
    v += access_violations(paved)
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
        method = "401.3 EXCEPTION — GUTTER %s" % " / ".join(gut)
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
    """Every band of every face falls away at 401.3's rate or goes to a gutter or a
       street; every gutter falls to a street; nothing drains onto the adjacent parcel."""
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
    for i in INLETS:
        print("   %s  rim %s, %s off the S Elm lot line; the lawn rises %s to it"
              % (i.mark, signed(i.rim), fmt(i.at[1]), inches(FRONT_LOT-i.rim)))
    o = outlet()
    print("   CB-1 outlet  %d x %s pipe roof drains at %.2f%%, Std Dwg 2320: %.2f cfs on %s SF (C %.1f, %.2f in/hr),"
          " %.2f cfs each; invert %s at CB-1, %s at a curb %s out"
          % (o["pipes"], inches(STD2320_D), 100*STD2320_SLOPE, o["flow"], "{:,.0f}".format(o["area"]), RUNOFF_C,
             RAIN_I, o["q_pipe"], signed(o["invert_inlet"]), signed(o["invert_curb"]), fmt(CURB_OUT)))
    for mark, p, flow, cover in sewer_crossings():
        print("   %s over the building sewer at %s, %s: %s from the flowline to the crown"
              % (mark, fmt(p[0]), fmt(p[1]), inches(cover)))
        assert cover > GUTTER_DEPTH, "%s cuts into the building sewer's cover" % mark
    v = grading_violations()
    assert not v, "grading: %s" % v[:6]

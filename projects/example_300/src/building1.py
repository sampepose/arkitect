"""Building 1 — Unit 1 at the front, Units 2 and 3 stacked behind it, 26'-0" x 48'-0".

PLAN FEET on the site grid, like every other model in src/. An inch dimension is written
IN(5.5) where it is defined.

Unit 1's PLANS are not here — they are drawn by src/sheets/plans.py, on the same sheets
as Units 2 and 3, by a supplied study that paints straight onto the canvas rather than
going through PlanDraw and the regrid. What that study knows that the BUILDING needs is
here with the rest of the model.

There was a src/unit1.py holding both halves until the asymmetry was noticed: there was
no unit2.py or unit4.py, because no other dwelling arrived as a separate study. A file
named for one dwelling among five was recording how the code arrived rather than what it
is. The mechanism difference is real; a module named after a unit was not the way to say
so.

This is the model in the order it has to be built. Unlike Building 2 this is two
dwellings' worth of geometry sharing one coordinate system, and the sharing is not
incidental:

  * Unit 1's wall faces are here as U1L1 / U1L2 / OA_U1 / CIRC_L2 even though Unit 1 is
    DRAWN by src/sheets/plans.py and none of these is ever put on a sheet. The regrid builds its
    axis map from the rooms in every Zone, so the Unit 1 half has to contribute its
    faces or Units 2 and 3 land somewhere else. They are a coordinate scaffold. Delete
    one and the building moves.
  * PLAN_L1 and PLAN_L2 are per LEVEL, not per building, because Unit 1's partitions sit
    in different places on the two floors and one map cannot put both levels' walls at
    3-1/2".
  * Units 2 and 3 are authored ONCE, from the Unit 1 end, and reflected as a block by
    the r* wrappers from src/mirror.py.

Then the things that depend on all of that: the Unit 3 stair and the Unit 2 entry, whose
positions are set by the end of the kitchen counter; the rear-wall terminations and the
bays they sit in; and the glazing and clear-rectangle figures the notes quote.
"""
import math
from src import fsd, levels
from arkitect.lib.units import IN, fmt
from arkitect.lib.model.records import PlanLevel
from arkitect.codes.columbus.legends import CLEARANCE_CAPTIONS
from src.finishes import BOARD     # the finish on a stud face, for the clear figures
from src.openings import WIN_HEAD, WIN_SF
from arkitect.lib.symbols import LOOSE
from arkitect.lib.model import geom
from arkitect.lib.model.regrid import EXT_STUD, PART_STUD, Zone, Plan, snap
from src.partywall import SEP_STUD, W4_CORE, W4_STUD
from arkitect.lib.model.dimensions import net_areas, strings, wall_faces, carve, unbridge, drop
from src.stairs import EXT_STAIR, THRESHOLD_DROP
from src.mirror import B1_W, BED_SIDE, LIVE_SIDE, rdoors, rfurn, rjoist, rnotes, rops, rpoly, rpts, rrooms, rspan, rwins, rx

# ---------------- Unit 1's geometry ----------------
# Unit 1 is DRAWN by src/sheets/plans.py, from a supplied study with its own
# primitives. What the study knows that the BUILDING needs is here, with the rest
# of the model: the stud-to-stud envelope, the origin that maps it onto the site
# grid, the stair the sections dimension, and the headroom the notes quote.
#
# It lived in a src/unit1.py of its own until the asymmetry was noticed: there was
# no unit2.py or unit4.py, because no other dwelling arrived as a separate study.
# Provenance is not structure, and a file named for one dwelling among five was
# describing how the code arrived rather than what it is.
# ============================================================================
# PART 1 — UNIT 1'S PLANS.  PLAN FEET, origin at the Sage / front stud faces.
# x: 0 = inside face of SAGE (left) wall, 301 = inside face of the
#    ADJACENT-PARCEL (right) wall (25'-1").
# y: 0 = inside face of S ELM (front) wall, 278.5 = face of the 2-HR COMMON
#    WALL (23'-2 1/2").
# ============================================================================
W_STUD, D_STUD = IN(301.0), IN(278.5)          # stud-to-stud: 25'-1" across S Elm face, 23'-2 1/2" front wall to common wall


EXT = IN(5.5)                    # exterior wall: 26'-0" out-to-out less 25'-1" stud-to-stud = 5 1/2" each side


# ================================================================ GRID (inches, framing)
# EVERY VALUE IN THIS SECTION IS DEFINED ONCE. Seven of them — FZ, B0, TREAD, NT, RUN,
# YT and YB — used to be written here and then written again thirty lines down, under
# the LEVEL 2 banner, where the second copy won. Both blocks read as live, and this one
# read as the more authoritative of the two because of the banner above it. Editing the
# tread here to widen the stair was a no-op that every oracle called a success: the
# build went green, the trace came back byte-identical, the tests passed, and the sheets
# went on printing 9-1/4". If a value below ever needs a second form, derive it under a
# new name rather than reassigning this one.
FZ = IN(121.0)          # front zone depth (living / BR2 / BR3); a 36" finished hall
                        # needs 37" between stud faces


B0, B1 = IN(124.5), IN(161.5)   # L2 hall band (open floor at L1)


R0 = IN(165.0)          # rear zone starts


# The stair. Shortening the tread spacing moves the bottom riser rearward and gains
# headroom without moving any room.
YT = D_STUD - IN(37.25)  # top riser; held at 36-5/8" clear to W4A's one 5/8" unit-face
                         # layer (36" behind W4's former two)
NT = 14
TREAD = IN(9.25)
RUN = NT * TREAD
YB = YT - RUN


NOSING = IN(1.0)
LB = YB - NOSING - IN(36.0)   # 36 in clear to the first tread nosing;
                              # check_unit1_stair measures it


# ================================================================ LEVEL 2
# Unit 1's three bypass closet fronts, drawn by level2 below. Named so the A-602 D-5
# quantity can be derived rather than assumed: Unit 1 draws its own, so a counter on the
# shared p.bypass() path cannot see them.
U1_BYPASS_DOORS = 3


# Keep the shared floor levels and top landing.
FLOOR_RISE = levels.FLOOR_RISE


# The north-south faces the A-102 string is dimensioned to, front stud face to the
# face of the common wall. The sheet draws this tuple and check_unit1_stair() closes
# it, so the printed segments cannot add up to anything but the overall. Note what is
# NOT in it: the partition between the bath and the closet at y 250..253.5 lies INSIDE
# Bedroom 4's depth, beside the string rather than along it. Chaining the room labels
# instead of reading the string counts it a second time and lands 2-1/2" over.
NS_FACES = (0.0, FZ, B0, B1, R0, D_STUD)


HEADER_FACE = IN(.5)


WELL_EDGE = B0 + HEADER_FACE


RISER = FLOOR_RISE / (NT + 1)


def nosing_height(y):
    return RISER + (y - (YB - NOSING)) / TREAD * RISER


HEADROOM = levels.F2_CEILING - levels.FF1 - nosing_height(WELL_EDGE)


HEADROOM_LABEL = '84-1/8"'  # conservative eighth-inch rounding of 84.1757 inches


# Preserve the existing front stud face and common-wall position exactly.
Y_OFFSET = IN(5.5)


X_OFFSET = IN(5.5)


def site_x(x): return x + X_OFFSET


def site_y(y): return y + Y_OFFSET


# ---------------- Unit 1's stair, in PLAN FEET, for everything outside this file ----
# Part 1 is drawn in inches, which is the right unit for an interior laid out on an
# eighth. Everything that READS Unit 1 works in plan feet, though, and it used to read
# the inch names directly and divide: A-301's section stair carried TR_IN/12.0,
# RISER_IN/12, NOSING_IN/12, HEADER_FINISH_IN/12 and four site_y() calls, so the unit
# boundary was not at the edge of this file at all — it was scattered through the
# consumer, eight lines of it, each one an opportunity to forget.
#
# These are the same quantities in feet, converted once, here. The inch names stay for
# Part 1's own use. A name crossing this line is now feet, like every other model in src.
U1_WELL_Y       = site_y(B0)          # the stair well / hall band edge


U1_STAIR_TOP_Y  = site_y(YT)          # top riser


U1_STAIR_BOT_Y  = site_y(YB)          # bottom riser


U1_WELL_EDGE_Y  = site_y(WELL_EDGE)   # finished header face


# The two Part 1 study constants the foundation needs, moved here from the sheet that
# drew them so the model never reads a sheet. Values unchanged.
P  = IN(3.5)                          # 2x4 partition, Unit 1 study
SX = IN(41.75)                        # stair enclosure width, Unit 1 study

# The rest of the study's partition lines, in its inches from the Sage stud face and
# the S Elm stud face. The plans draw to them and the electrical model places its
# devices against them, so they are the model's.
#
# The side walls are 2x6, type W1. They were 2x8 — type W1A — and when they thinned the
# OUTSIDE face was held: the building is 26'-0" over studs for its whole length either
# way. So both inside faces moved 1-3/4" outward, and this frame's origin moved with the
# Sage face. NOTHING INSIDE THE BUILDING MOVED. Every partition line below therefore
# reads 1-3/4" larger than it did while standing in the same place on the site, and the
# two rooms at the ends — the stair enclosure and Bedroom 1 / Bedroom 4 — each gained
# that 1-3/4". Anything mounted ON a side wall is written against 0 or W_STUD instead,
# so it follows its wall rather than holding still.
MX0, MX1 = IN(45.25), IN(88.25)    # mech strip (L1) / hall strip (L2)
WET = IN(5.5)                      # 2x6 wet wall
# The wet wall is the one the baths share with MECH (L1) and the hall (L2), so Stack B
# and the upstairs closet bend stay out of the Bedroom 1 / Bedroom 4 wall. The 2x6 takes
# its extra 2" from the far wall, now a 2x4: the bath keeps 61" and BR_X does not move.
WW0, WW1 = MX1, MX1 + WET          # 2x6 wet wall 86.5 .. 92, shared with MECH
BX0, BX1 = WW1, WW1 + IN(61.0)     # bath 93-3/4 .. 154-3/4 (61" framed = 60" clear)
BR_X = IN(158.25)                  # BR1 / BR4 west face
assert math.isclose(BX1 + P, BR_X), "bath / Bedroom 1 partition is not a 2x4"
BY1 = IN(250.0)                    # bath south face: 85" framed = 84" finished for 24+15+15+30
PK0 = BY1 + P                      # pocket (closet / linen) to D_STUD
KX = IN(221.25)                    # kitchen column west edge
DEM0, DEM1 = IN(148.75), IN(152.25)  # BR2/BR3 demising wall
NX = IN(198.75)                    # band east wall (L2)
CS = IN(249.75)                    # closet split in the notch
# The Unit 1 attic hatch, in the Level 2 hall strip: 30" along the trusses, 22" across
# them, RCO R807.1. A-102 draws it and S-103 checks it against the roof and draws it
# again, from this one place, so the two cannot disagree.
U1_ATTIC       = (IN(55.75), IN(212), IN(85.75), IN(234))    # x0 y0 x1 y1, study inches
U1_ATTIC_LABEL = (IN(66.75), IN(236))

# The Level 1 stair wall, which carries the double trimmer at the well and is framed
# as bearing with blocking to the slab (A-101 note 3). S-101 casts a thickened strip
# under it, so the wall is named once, in feet, in final sheet coordinates.
U1_STAIR_WALL = (site_x(SX), site_y(LB), site_x(SX+P), site_y(YT))


U1_TREAD        = TREAD


U1_RISER        = RISER


U1_NOSING       = NOSING


U1_HEADER_FACE  = HEADER_FACE


U1_TREADS       = NT + 1                 # 15 risers, 14 treads plus the landing nosing


def u1_nosing_height(y_ft):
    """Height of the stair nosing above Level 1, in feet, at a SITE y in feet."""
    return nosing_height(y_ft - Y_OFFSET)


def windows(level):
    """Sheet coordinates in feet, shared by plan and generated elevations."""
    # Stack the entry W-A directly below the front second-floor Sage W-A.
    front_safford=(site_x(-EXT/2),site_y(IN(30)),3,'v','A')
    out=[(site_x(IN(63.25)),site_y(-Y_OFFSET/2),3,'h','A'),
         (site_x(IN(201.75)),site_y(-Y_OFFSET/2),3,'h','A'),
         (site_x(W_STUD+EXT/2),site_y(IN(170)),3,'v','A')]
    if level==1:
        out.append((site_x(W_STUD+EXT/2),site_y(IN(69)),3,'v','B'))
        out.append(front_safford)
    else:
        out.extend([front_safford,
                    (site_x(-EXT/2),site_y(IN(238)),3,'v','A'),
                    (site_x(W_STUD+EXT/2),site_y(IN(69)),3,'v','A')])
    return out


ENTRY_LEFT=site_x(IN(5.75))


ENTRY_WIDTH=3.0


# ---------------- Unit 1's two Sage-wall terminations ----------------
# The heater vent and the dryer duct of the Level 1 mechanical room both leave through
# the Sage wall: the dryer duct goes straight out behind the W/D
# DR-1 goes straight out behind the stacked W/D. A-101 draws the route, A-201 the cap
# and C-101 measures it to the Unit 2 door — and until they were named here each sheet
# typed its own copy of the same number. In the study's feet from the S Elm stud face
# (site_y() puts them on the sheet); the height is feet above grade. The storage heater
# vents nothing, so this wall carries one cap where it used to carry two.
U1_DR_TERM   = IN(260.9)
U1_DR_TERM_Z = 4.5
# The route, as a polyline in study feet: the duct from the back of the dryer to the
# outside face of the Sage wall.
U1_DR_DUCT   = [(IN(4),U1_DR_TERM),(IN(-5.5),U1_DR_TERM)]


# ============================================================================
# PART 2 — THE BUILDING, on the site grid.
# ============================================================================
# ============================= FURNITURE AND FIXTURES =====================
# (x,y,w,h,kind,face) in plan feet.  Reference only, not in contract.
# Units 2 / 3 fittings. Authored in the UNMIRRORED frame and reflected as a block by
# rfurn, so the counters, the sink under its window, the range on the separation run,
# the fridge and its hinge, the W/D, the heater and the panel all swap sides together
# and the 'e'/'w' facings swap with them. THE SIDE NAMES IN THE COMMENTS BELOW ARE THE
# SIDES THESE COORDINATES FACE BEFORE THE REFLECTION; as drawn, read them swapped.
F_U23=rfurn([(0.500,24.45,5.700,2.00,'counter'),
       (3.300,24.45,2.500,2.00,'range','n'),
       (6.200,24.45,2.500,3.00,'fridge','n','w'),
       # The Sage leg carries the sink and the dishwasher. It runs 5'-9" so that a
       # full 2'-0" machine fits under the counter directly below the sink bowl, which
       # is where its drain and hot supply are: at the 5'-1-1/4" it used to be there
       # was 1'-3" of counter above the sink and 1'-4-1/4" below, and neither takes a
       # dishwasher of any size. The sink does not move — it is centred under W-A, and
       # sliding it up to make room would have thrown it a foot off the window.
       (0.500,26.45,2.000,5.75,'counter'),
       (0.500,27.700,2.000,2.50,'sink'),
       (0.500,30.200,2.000,2.00,'dw'),
       # Standard economical alcove tub: end drain at the plumbing/wet-wall end,
       # shared by Units 2 and 3. Final rough-in follows the selected tub submittal.
       (9.100,24.45,5.000,2.50,'tub','n','w'),
       # the wc centred in the clear band between tub and vanity, and the vanity
       # tight to the wall — raw values chosen so both land where intended after
       # the regrid, which moves a fixture's position but keeps its size
       (9.100,27.4917,2.3333,1.66667,'wc','e'),
       (9.100,29.7000,1.750,2.00,'lav','w'),
       # Units 2/3 MECH: W/D tight to the rear/adjacent-parcel corner. Its
       # Sage edge is exactly 36" from the opposite side wall, leaving the
       # panel working depth clear across the closet. The panel mounts on that
       # Sage side wall; the heater stands on the floor against the rear wall.
       (8.850,44.67,2.250,2.83,'wd'),
       # The 40-gallon storage heater, an 18" cylinder drawn on its 18" square
       # footprint, standing on the rear wall CENTRED in the 3'-0" bay left when
       # the old 1'-8-1/2" heater bay and 1'-3-1/2" spare bay merged: 9" each side,
       # against P-601 note 6's 2" minimum. Its back is on the rear wall's room face
       # and its front lands 1-1/8" CLEAR of the panel's working space below, which
       # is the whole reason the tank is 18" and not 22" — see plumbing.WH_TANKS.
       # THESE FOUR NUMBERS ARE SOLVED, not measured: the stud grid stretches this
       # band about half a percent, so a typed 18.0/12.0 comes out an eighth over.
       # plumbing.check_working_spaces() is what proves they still land right.
       (11.844750,46.041350,1.500000,1.443500,'wh'),
       (13.850,44.45,0.250,1.20,'panel','w'),
       # The panel's NEC 110.26(A) space, 36" deep off its wall and 30" wide, exactly
       # where it has always been drawn: the 18" tank clears it without it moving.
       (11.100,43.45,3.000,2.50,'clear'),
       # The heater service space starts at the appliance face, not the wall, and
       # projects 30" toward / through the open door plane. Solved a shade OVER 30"
       # so that what the grid finally draws can never read short of RCO M1305.1.
       (11.323950,43.458250,2.531300,2.583100,'whclear'),
       # Both beds head on a wall with no opening in it. Bedroom 1's is W4, which has
       # none by definition. Bedroom 2's used to be the rear wall, directly under the
       # rear W-A; with one window off the BED_SIDE wall the bedroom partition is clear
       # for its whole width, so the bed turns end for end onto that instead and the
       # rear window is left at the foot of the room where it lights it.
       (18.500,24.45,5.000,6.6667,'bed','n'),
       (18.500,36.15,5.000,6.6667,'bed','n'),
       (6.500,36.25,4.000,2.50,'table'),
       (6.900,34.85,1.300,1.30,'chair'),
       (8.800,34.85,1.300,1.30,'chair'),
       (6.900,38.75,1.300,1.30,'chair'),
       (8.800,38.75,1.300,1.30,'chair'),
       (0.500,32.45,3.000,6.50,'sofa','w'),
       (4.800,33.95,1.500,3.50,'table')])

T98   = 9.875/12.0   # legacy regrid scaffold's quarter-turn stair tread, 9-7/8"
LSTX1 = 4.0+4*T98                    # 7.292  east end of the rear leg
LST_LONG  = (0.5,12.65,3.5,9*T98,9)  # ascends toward S Elm (-y)
LST_SHORT = (4.0,20.05,4*T98,3.5,4)  # ascends toward the adjacent-parcel wall (-x)
LST_ARROW = [(LSTX1-0.4,21.80),(2.25,21.80),(2.25,13.15)]
STAIR_POLY= [(0.5,12.65),(4.0,12.65),(4.0,20.05),(LSTX1,20.05),(LSTX1,23.55),(0.5,23.55)]
HALL_L1   = [(4.0,15.8),(10.5,15.8),(10.5,23.55),(LSTX1,23.55),(LSTX1,20.05),(4.0,20.05)]
HALL_L2   = [(0.5,10.05),(16.2,10.05),(16.2,12.9),(13.5,12.9),(13.5,14.15),
             (4.0,14.15),(4.0,12.65),(0.5,12.65)]

# Unit 1's LEGACY shapes. These are not drawn — Part 1 above draws Unit 1 directly
# from inch coordinates onto the canvas. What is left here is
# a coordinate scaffold: the regrid builds its axis map from the rooms in each Zone, and
# the Unit 1 half of Building 1 still has to contribute its wall faces so that Units 2
# and 3 land where they do. Every name below is used once, in the Zone() calls that
# build PLAN_L1 and PLAN_L2, and nowhere else. Change one and Units 2/3 move.
U1L1=[(0.5,0.5,11.6,9.5,"BEDROOM 1"),(12.5,0.5,2.0,6.0,"CL."),(12.5,6.9,2.0,3.1,"STOR."),
      (10.9,15.8,5.0,7.75,"BATH 1")]
U1L2=[(10.8,0.5,2.0,4.0,"CL."),(13.2,0.5,2.0,4.0,"CL."),
      (13.9,13.3,2.3,10.25,"CL."),(8.5,14.55,5.0,9.0,"BATH 2"),
      (4.4,14.55,3.35,5.1,"MECH")]
# Units 2 / 3 rooms and both bedroom outlines, authored in the unmirrored frame and
# reflected together. Reflecting the rects and the polygons as one block is what keeps
# the bath, the two reach-ins and the mechanical closet in the same relation to each
# other; only which side of the building they land on changes.
U23=rrooms([(9.1,24.45,5.0,7.1,"BATH",(1.0,0.0)),(14.5,24.45,2.0,6.5,"CL."),
     (14.5,41.0,2.0,6.5,"CL."),(8.85,44.30,5.25,3.2,"MECH",(-0.45,0.4),"compact","nolabel")])
BR1_U23=rpts([(14.5,24.45),(25.5,24.45),(25.5,35.75),(14.5,35.75),(14.5,31.35),(16.5,31.35),(16.5,24.45)])

# ONE W-A per sleeping room on the BED_SIDE wall, not two. Two apiece glazed Bedroom 1
# at 31 percent and Bedroom 2 — with its rear W-A as well — at 46, against the 8 of RCO
# 303.1, and paid for it three times over: four extra units in the schedule, no solid
# wall in either room long enough to head a bed against, and a BED_SIDE wall so cut up
# that the widest gap in it was 3'-4", which is why Units 2 and 3 lost their wall
# brackets and went to grade pads out past the building corner (C-101 note 5b).
#
# The two kept are the OUTER pair, at the W4 end of Bedroom 1 and the rear end of
# Bedroom 2. That is what leaves the solid wall in the MIDDLE, one 14'-6-1/2" run
# spanning the bedroom partition, which is the only place on this elevation that takes
# both outdoor units with 3'-0" clear to a window on each side AND stands clear of both
# building corners and of the rear-wall dryer and water-heater caps. Keeping the inner
# pair instead would leave two 7'-0" runs at the corners, one of them 1'-6" from the
# dryer cap; keeping one of each would leave a single 9'-0" gap that takes one unit.
# Each room also keeps 7'-1"+ of solid wall inboard of its window for a bed.
U23WIN=rwins([(0.5,27.45,3.0,'v',"A"),          # centred on the kitchen sink
              (19.53,47.5,3.0,'h',"A"),         # centred on BR2's clear rear wall:
                                                # 19'-5-1/2" .. 22'-5-1/2", 3'-1" each side
              (25.5,25.95,3.0,'v',"A"),          # BEDROOM 1, at the W4 end
              (25.5,42.95,3.0,'v',"A")])         # BEDROOM 2, at the rear end
LIVE_WALL_X=rx(0.5)      # interior stud face of the wall the living side now faces
U3_STAIR = EXT_STAIR                    # Unit 3 takes it as it is
U3_STAIR_W  = U3_STAIR.width       # overall projection of the stair and both landings
U3_LAND_D   = U3_STAIR.landing_depth
U3_STOOP_Z  = U3_STAIR.stoop_above_grade
U3_RISERS   = U3_STAIR.risers
U3_TREADS   = U3_STAIR.treads
U3_TREAD    = U3_STAIR.tread
U3_RUN      = U3_STAIR.run         # 10'-9-1/2" true horizontal flight length
U3_LAND_LEN = U3_STAIR.landing_len # the top landing's run ALONG the wall
# ---- the stair's fire separation distance, and what that costs.
# On the adjacent parcel the lot line is the measuring point and 2'-6" of clearance
# buys a listed 1-hour underside. On a STREET side, RCO 202 measures fire separation
# distance to the CENTRELINE of the street, so a stair 4'-6" off the right-of-way line
# is nowhere near the 5'-0" threshold of RCO Table 302.1(1) and its underside is
# unrated. That is the whole reason the mirror is worth doing to the mechanical work.
U3_YARD        = 8.0                            # the side yard the stair projects into
U3_STAIR_CLR   = U3_YARD-U3_STAIR_W             # what is left beyond the stair
# On a street side fire separation distance is taken to the CENTRELINE of the street,
# RCO 202, so Table 302.1(1) never engages and the underside needs no listed assembly.
U3_STAIR_RATED = False
U3_STAIR_LINE  = "%s RIGHT-OF-WAY"%LIVE_SIDE
U3_STAIR_TAG   = ("%s TO %s R.O.W. — FSD TO STREET CENTERLINE — UNRATED"%(fmt(U3_STAIR_CLR),LIVE_SIDE)
                  if not U3_STAIR_RATED else
                  "%s TO LOT LINE · 1-HR UNDERSIDE"%fmt(U3_STAIR_CLR))

# The top landing deck is the Unit 3 floor; its framing is what hangs below it. An
# opening may stand under the DECK, never under the flight: item 12's rule is that the
# soffit clears the head by 6", and the flight's soffit drops 8" a tread.
U3_LAND_DECK   = U3_STAIR.deck                  # +10'-6", level with the Unit 3 floor
U3_LAND_FRAME  = U3_STAIR.framing               # steel landing framing depth allowance
U3_LAND_SOFFIT = U3_STAIR.soffit                # +9'-8" above finished grade
BR2_U23=rpts([(14.5,36.15),(25.5,36.15),(25.5,47.50),(16.5,47.50),(16.5,40.60),(14.5,40.60)])

BED4_L2=[(16.6,10.05),(25.5,10.05),(25.5,23.55),(16.6,23.55)]
BED2_L2=[(0.5,0.5),(10.4,0.5),(10.4,4.9),(12.8,4.9),(12.8,9.65),(0.5,9.65)]
BED3_L2=[(15.6,0.5),(25.5,0.5),(25.5,9.65),(13.2,9.65),(13.2,4.9),(15.6,4.9)]
# ONLY THE NAME IS READ from these labels -- src/electrical.py's room lookup takes
# l[2] and nothing else. The dimension and area fields carried figures for years
# ("114 SF", "192 SF", "12'-4-5/8\" x 9'-4\""), and not one of them appeared among the
# 8,049 strings a full build draws: Unit 1's plans are drawn by src/sheets/plans.py from
# inch coordinates, and its room() derives every label it prints. A maintainer told to
# update Unit 1's areas would have edited these and watched the set not change. The
# fields stay, empty, because the tuple shape is what the regrid maps; the figures do
# not, because a number nobody prints is a number nobody checks.
CIRC_L2=[(STAIR_POLY,[]),
         (BED2_L2,[(5.4,8.0,"BEDROOM 2","","")]),
         (BED3_L2,[(20.4,8.0,"BEDROOM 3","","")]),
         (BED4_L2,[(21.1,17.0,"BEDROOM 4","","")]),
         (HALL_L2,[(7.0,11.6,"HALL","","")])]
OA_U1=[(STAIR_POLY,[]),
       (HALL_L1,[(8.0,19.4,"HALL","","")]),
       ([(14.9,0.5),(25.5,0.5),(25.5,23.55),(16.3,23.55),
         (16.3,15.4),(4.0,15.4),(4.0,12.65),(0.5,12.65),(0.5,10.4),(14.9,10.4)],
        [(23.9,1.4,"ENTRY","",""),
         (20.6,5.4,"LIVING / DINING","",""),
         (21.9,17.6,"KITCHEN","","")])]
# The open kitchen / living / dining outline is reflected; the two bedroom outlines are
# already reflected above, so their labels are reflected on their own and paired back.
OA_U23=rpoly([([(0.5,24.45),(8.7,24.45),(8.7,31.95),(14.1,31.95),(14.1,43.90),
          (8.45,43.90),(8.45,47.5),(0.5,47.5)],
         [(4.6,29.25,"KITCHEN","","63 SF"),
          (7.3,37.90,"LIVING / DINING","","194 SF")])]) + [
        (BR1_U23,rnotes([(20.5,33.55,"BEDROOM 1",None,"AUTO SF")])),
        (BR2_U23,rnotes([(20.5,45.05,"BEDROOM 2",None,"AUTO SF")]))]

# Hold Unit 1's stud face and its stair. W4 is W4A and W4B, two U305 walls back to back,
# 8-1/4" stud to stud; Units 2/3 give up the depth, 4-3/4" more than a single stud row took.
Y_SEP_TOP = snap(site_y(D_STUD))
Y_SEP_BOT = snap(Y_SEP_TOP+SEP_STUD)
B1_UNIT   = snap(48.0-EXT_STUD-Y_SEP_BOT)  # rear-unit framed depth

# Units 2 and 3: hold both bedrooms at an exact 11'-2" wide. Their west face is the
# closet band at raw 14.5; pinning 14.1 with it keeps that partition at 3-1/2" and lets
# the kitchen and living space west of the bath absorb the difference.
BR_WIDTH = 11.0+2.0/12.0
# Pins are authored in the unmirrored frame like the geometry they hold, and both the
# key (a model face) and the value (where that face lands) go through the same
# reflection. Reflecting only one of the two silently moves the bedrooms instead.
U23_XPINS = {rx(k): rx(v) for k,v in
            {14.5: (26.0-EXT_STUD)-BR_WIDTH,
             14.1: (26.0-EXT_STUD)-BR_WIDTH-PART_STUD,
             # Hold the expanded MECH's living-side face exactly 5'-3" from its
             # fixed bedroom-side face; otherwise an overlapping nominal 0.40-ft wall
             # span steals 7/8" during the stud-grid rebuild.
             8.85: (26.0-EXT_STUD)-BR_WIDTH-PART_STUD-(5.0+3.0/12.0)}.items()}

# and split the zone evenly between the two bedrooms: what is left after the dividing
# partition, halved. The 4-1/2" recovered at W4 adds 2-1/4" to each bedroom.
BR_DEPTH  = (B1_UNIT-PART_STUD)/2.0
U23_YPINS = {35.75: Y_SEP_BOT+BR_DEPTH,
             36.15: Y_SEP_BOT+BR_DEPTH+PART_STUD}

# Both bedroom reach-ins are 6'-6" of bypass door. That is a chosen size, the same as
# the 2'-0" depth, so the run is held too: unheld the slack stretched one to 6'-8-3/4"
# and the other to 6'-7", and the two bedrooms did not match.
#
# The bath and the mechanical closet are held with them, at the sizes they already
# carry. Lengthening a closet has to take its space from somewhere, and the y map is
# one function across the whole zone width: without this the bath gave up 2-3/4" and
# the MECH 1/2", though neither shares a column with either closet. Held, the space
# comes off the open bedroom floor below the closet, which is what actually happens
# when you run a closet further into a room.
U23_BATH_DEPTH = 7.25                # 7'-3", the tub, wc and lav run with room to spare
U23_MECH_DEPTH = 3.0+3.625/12.0      # 3'-3-5/8", set by the washer/dryer and heater
U23_YHOLD = {(r[1],r[1]+r[3]) for r in U23 if r[4]=="CL."} | {
             (24.45,31.55,U23_BATH_DEPTH), (44.30,47.5,U23_MECH_DEPTH)}
# and 5'-0" across, which is the tub. Unheld the slack left it 4'-11-3/4" — a quarter
# inch short of the tub drawn in it, so the fixture overhung the wall it sits against.
U23_BATH_WIDTH = 5.0
# MECH is 5'-3" wide, expanded 11" into the living bay while its living-side wall,
# appliances and rear-wall termination cluster remain fixed.
U23_MECH_WIDTH = 5.0+3.0/12.0
U23_XHOLD = {rspan(9.1,14.1,U23_BATH_WIDTH), rspan(8.85,14.1,U23_MECH_WIDTH)}

PLAN_L1 = Plan([Zone(U1L1,OA_U1,0.5,23.55,26.0,EXT_STUD,Y_SEP_TOP),
                Zone(U23,OA_U23,24.45,47.5,26.0,Y_SEP_BOT,48.0-EXT_STUD,U23_XPINS,U23_YPINS,U23_YHOLD,U23_XHOLD)],26.0,48.0)
PLAN_L2 = Plan([Zone(U1L2,CIRC_L2,0.5,23.55,26.0,EXT_STUD,Y_SEP_TOP),
                Zone(U23,OA_U23,24.45,47.5,26.0,Y_SEP_BOT,48.0-EXT_STUD,U23_XPINS,U23_YPINS,U23_YHOLD,U23_XHOLD)],26.0,48.0)

# ---------------- Units 2 / 3 rear-wall terminations ----------------
# Every clearance stated for these terminations is measured here, off the regridded
# plan, from the same fixtures and openings the plans draw. The notes used to promise
# 4'-0" horizontally from the water-heater terminal to the Unit 2 entry door. That
# figure was taken on the raw model and to a point chosen inside the bay; measured
# properly, to the near edge of the bay where the cap can actually land, it is short
# of 4'-0" to both the door below and the Unit 3 W-C above. The bay is what is left
# of the closet's rear wall between the stacked washer/dryer and the heater,
# so the washer fixes the near edge and no installer can bring the cap closer to the
# door than this. Deriving it means the promise cannot drift from the drawing again.
# ---------------- Units 2 / 3 entries and the Unit 3 stair ----------------
# These come AFTER the regrid, and are the only geometry in the set that does.
#
# The stair is a pressure-treated wood stair standing outside the building, framed
# prescriptively to RCO R311.7 and the R507 deck provisions; src/stairs.py holds the
# material. Its own dimensions are
# TRUE and must not go through the stud-grid map: that map stretches this band of the
# plan by 8 percent, and running the stair through it drew the old 3'-6" top landing
# 3'-7-7/8" long and the 10'-9-1/2" flight 10'-11-5/8". Both landings, the flight and
# the entry door the top landing serves are therefore laid out in FINAL SHEET FEET,
# and the door is authored back into the model with inv_y so that its drawn jambs
# land exactly where the design puts them.
# Both flats enter off LIVE_SIDE now, one at grade and one off the stair.
#
# THE ELEVATED STAIR MUST NOT PASS THE REAR WALL. Along the LIVE_SIDE face the
# governing line is the street and fire separation distance is taken to its
# CENTRELINE, RCO 202, so the underside is unrated. Past the rear wall that stops
# being true: the stair is then in the courtyard between the two buildings, where
# the governing line is the RCO 302.1 imaginary line — and a 7'-0" landing pushed
# the foot of the flight 1'-2-3/4" beyond the wall, inside the 5'-0" of RCO Table
# 302.1(1). The blanket "unrated" claim did not hold for that stub, and the line
# stands closer to this wall now than it did then: 3'-0", not 6'-0", so a stub that
# passes the wall has less room than ever. check_u3_stair_inside() asserts it cannot
# recur, and measures to the model's line rather than to a literal.
#
# So the landing goes back to 3'-6" square, holding the door alone with 3" of
# framed wall each side, and Unit 2's living W-A is deleted: at 3'-6" there is no
# deck left to stand it under, and under the FLIGHT the soffit falls 8" a tread and
# is below an 8'-0" head within two of them. Unit 3 loses the same window, because
# the two flats stack and a window there would look straight onto the stringer.
# The open living space keeps the kitchen W-A and the rear W-C.
U23_JAMB   = 4.0/12.0                 # framed wall between the kitchen and the door
U23_KITCHEN_END = PLAN_L1.y(26.45+5.75)
U3_DOOR_LO = U23_KITCHEN_END+U23_JAMB
U3_LAND_LO = U3_DOOR_LO-(U3_LAND_LEN-3.0)/2.0      # door centred on the landing
U2_LIVING_WIN=U3_LIVING_WIN=None
# Unit 2's door sits directly under Unit 3's, as the two flats stack everywhere else.
U2_ENTRY=(LIVE_WALL_X,PLAN_L1.inv_y(U3_DOOR_LO),3.0,'v',-1,"ext")
U3_ENTRY=U2_ENTRY
# The rear living bay is door-free in both flats now, so both take the W-C that
# only Unit 3 used to have, and the two flats glaze alike.
#
# It is set as the mirror of Bedroom 2's rear W-A about the middle of the wall, as
# drawn, so the rear elevation is symmetric: the W-A is centred on its bedroom's clear
# wall and does not move. The 4'-0" this window used to keep from the water heater's
# spare bay was a vent terminal's clearance; the heaters are electric storage and vent
# nothing, and check_u23_terms() holds the dryer cap's 3'-0" to it instead.
_u23_rear_wa = PLAN_L1.span(next(w for w in U23WIN if w[3]=='h' and abs(w[1]-47.5)<1e-6))
U2_REAR_LIVING_WIN=(PLAN_L1.inv_x(B1_W-(_u23_rear_wa[0]+_u23_rear_wa[2]/2.0)-5.0/2.0,47.5),47.5,5.0,'h',"C")
U3_REAR_LIVING_WIN=U2_REAR_LIVING_WIN
# Unit 2's door landing. RCO 311.3.1 allows an exterior landing 7-3/4" below the
# threshold where the door does not swing over it, and D-1 swings in — but this
# project holds the stricter 1-1/2", so the landing is a poured pad like the Unit 3
# stoop rather than a slab at grade: top stairs.THRESHOLD_DROP below the threshold, one
# step down to the walk.
U2_THRESHOLD_Z = levels.FF1                 # top of the threshold
U2_LANDING_DROP= THRESHOLD_DROP
U2_LANDING_Z   = U2_THRESHOLD_Z-U2_LANDING_DROP
U2_LANDING_MAX = 1.5/12.0                        # the project's own limit, RCO 311.3.1

# The stair itself, in final sheet feet from the top landing down to the stoop.
U3_LAND_HI   = U3_LAND_LO+U3_LAND_LEN
U3_FLIGHT_HI = U3_LAND_HI+U3_RUN
U3_STOOP_HI  = U3_FLIGHT_HI+U3_LAND_D
U23WIN_U2=list(U23WIN)+[w for w in (U2_LIVING_WIN,U2_REAR_LIVING_WIN) if w]
U23WIN_U3=list(U23WIN)+[w for w in (U3_LIVING_WIN,U3_REAR_LIVING_WIN) if w]

REAR_Y = 47.5

def _f23(kind): return PLAN_L1.keep(next(f for f in F_U23 if f[4]==kind))
_wd23, _wh23   = _f23('wd'), _f23('wh')
_wd_span       = (_wd23[0], _wd23[0]+_wd23[2])
_wh_span       = (_wh23[0], _wh23[0]+_wh23[2])
U23_MECH_X     = tuple(sorted((PLAN_L1.x(rx(8.85),REAR_Y), PLAN_L1.x(rx(14.10),REAR_Y))))
# The laundry stands tight in one corner of the closet; the heater bay is the whole of
# the rear wall left over. There is no spare bay any more — it existed to carry the
# concentric vent cap of the tankless, and a storage heater vents nothing, so the two
# merged into one 3'-0" bay. Which corner the laundry is in swaps with the mirror, so
# take it from the appliance rather than naming a side.
def _corner_bay(span):
    lo,hi = U23_MECH_X
    return (lo,span[1]) if abs(span[0]-lo) < abs(hi-span[1]) else (span[0],hi)
U23_LAUNDRY_BAY= _corner_bay(_wd_span)
U23_HEATER_BAY = ((U23_LAUNDRY_BAY[1],U23_MECH_X[1]) if abs(U23_LAUNDRY_BAY[0]-U23_MECH_X[0])<1e-9
                  else (U23_MECH_X[0],U23_LAUNDRY_BAY[0]))
BAY = lambda b: b[1]-b[0]
# Which end of the building each side is, in plan x. The mirror swaps them, and that
# is the whole point of it: nothing below may assume low plan x is one side or other.
BED_END_X, LIVE_END_X = 0.0, B1_W
# The three bays named in the order a reader walking the rear wall from the BED_SIDE
# end to the LIVE_SIDE end meets them. Note 15 prints this, so it cannot go stale.
U23_BAYS = sorted([("LAUNDRY",U23_LAUNDRY_BAY),("HEATER",U23_HEATER_BAY)],
                  key=lambda t:abs(t[1][0]-BED_END_X))

# ---- every opening in the rear wall of either flat, regridded, as (lo,hi,name).
# The mirror changes which openings are in this wall at all — Unit 2's entry left it
# and both flats gained a living W-C — so the clearances are taken from the opening
# lists rather than from two jambs named in advance.
def _rear_openings():
    out=[]
    for nm,P,ws,ds in (("UNIT 2",PLAN_L1,U23WIN_U2,[U2_ENTRY]),
                       ("UNIT 3",PLAN_L2,U23WIN_U3,[U3_ENTRY])):
        for w in ws:
            if w[3]!='h' or abs(w[1]-REAR_Y)>1e-6: continue
            a=P.x(w[0],REAR_Y); out.append((a,a+w[2],"%s W-%s"%(nm,w[4])))
        for d in ds:
            if d[3]!='h' or abs(d[1]-REAR_Y)>1e-6: continue
            a=P.x(d[0],REAR_Y); out.append((a,a+d[2],"%s DOOR"%nm))
    seen={}
    for a,b,n in out: seen.setdefault((round(a,4),round(b,4)),[]).append(n)
    return sorted((a,b," / ".join(ns)) for (a,b),ns in seen.items())
U23_REAR_OPENINGS = _rear_openings()
def rear_gap(v,op):
    a,b,_n = op
    return 0.0 if a-1e-9<=v<=b+1e-9 else min(abs(v-a),abs(v-b))
def rear_nearest(v):
    o=min(U23_REAR_OPENINGS,key=lambda o:rear_gap(v,o)); return rear_gap(v,o),o[2]
# ---- the two rear-wall services, derived. The heater used to be a third: its
# concentric vent terminated over the spare bay, and both went when the heaters became
# electric storage.
# Dryer: high at whichever end of the closet's rear segment is further from the nearest
# opening, with the cap held 5" in from that end. The duct rises at the laundry and
# runs the length of the rear wall to it.
_dr_end        = max(U23_MECH_X,key=lambda v:rear_nearest(v)[0])
U23_DR_TERM    = _dr_end + (5.0/12.0 if _dr_end==U23_MECH_X[0] else -5.0/12.0)
DR_CLR, DR_CLR_NEAR = rear_nearest(U23_DR_TERM)
U23_DUCT_RISE  = sum(_wd_span)/2.0             # over the washer/dryer
# Stack E rises in the same wall and goes through the roof. It was put midway between
# the two caps this wall used to carry, and it does NOT move now that the heater's cap
# has gone: P-101 draws its foot under the slab, the drainage model carries its branch
# and S-103 its roof penetration, and none of that should shift because a vent was
# deleted. Held as the offset from the dryer cap it has always had, with an assert that
# it still stands in the heater bay and clear of the cap.
E_RISER_OFF    = 0.96875                        # 11-5/8" from the dryer cap
U23_E_RISER    = U23_DR_TERM + (E_RISER_OFF if U23_DR_TERM<sum(U23_MECH_X)/2.0 else -E_RISER_OFF)
assert min(U23_HEATER_BAY)-1e-9 <= U23_E_RISER <= max(U23_HEATER_BAY)+1e-9, \
    "stack E's riser has left the heater bay"
# Which side of the building each of the three services ends up on, as a token, so the
# prose notes follow the derivation rather than repeating a side name someone typed.
_side_of = lambda v: LIVE_SIDE if abs(v-LIVE_END_X)<abs(v-BED_END_X) else BED_SIDE
DR_END_SIDE   = _side_of(U23_DR_TERM)

# ---------------- Units 2 / 3 glazing, for plan note 5a ----------------
# Derived from the same window lists the plans draw and the same room areas the plan
# labels print, so note 5a cannot drift from either. The mirror moves every one of
# these windows and turns Unit 2's rear W-A into a W-C, so nothing here may be typed.
# Off the REGRIDDED polygons and through net_areas, so the denominator here is the same
# number the plan label prints. The bedrooms are net of their reach-ins; the open
# kitchen / living / dining keeps the typed split between its two labels, because that
# split is a design statement and not something the one polygon can be asked for.
# Units 2/3's open area: BOTH figures derived, the way Units 4/5's are.
#
# They were typed -- "63 SF" and "194 SF" -- because net_areas() only rewrites a label
# when its polygon carries exactly one, and this polygon carries two: the split between
# kitchen and living is a design statement and the model cannot invent it. What the model
# CAN do is measure each side of a split it is told, which is what src/building2.py has
# always done for Units 4 and 5. Nothing checked the sum, and both had gone stale: 63 +
# 194 = 257 against a polygon of 255.56, drifting when the W4 two-wall change moved these
# units and carried the derived bedroom areas with it but not these.
#
# The split is y = 31.896 in page space, which is a step in the polygon itself -- the
# line where the kitchen's narrower run opens into the living width -- and it sits
# between the two labels.
_u23_poly, _u23_labs = PLAN_L1.poly([OA_U23[0]])[0]
U23_KITCHEN_SF, U23_LIVING_SF = geom.split(_u23_poly, PLAN_L1.y(31.95), 'y')
assert abs(U23_KITCHEN_SF+U23_LIVING_SF-geom.area(_u23_poly)) < 1e-6, \
    "the Units 2/3 open-area split does not account for the whole polygon"
_U23_SF = {"KITCHEN": U23_KITCHEN_SF, "LIVING / DINING": U23_LIVING_SF}
OA_U23[0] = (OA_U23[0][0],
             [l[:4]+("%d SF"%round(_U23_SF[l[2]]),) if l[2] in _U23_SF else l
              for l in OA_U23[0][1]])

U23_LABELS = {l[2]: l for (_p,labs) in net_areas(PLAN_L1.poly(OA_U23)) for l in labs}
U23_AREA = {name: float(l[4].split()[0]) for name,l in U23_LABELS.items()
            if len(l)>4 and str(l[4]).endswith(("SF","CLOSET"))}
_BR2_REAR = [p[0] for p in BR2_U23 if abs(p[1]-REAR_Y)<1e-6]
def u23_glazing(wins):
    """percent glazed for one flat: the open kitchen/living/dining, then each bedroom"""
    bw = rx(25.5)                                    # the BED_SIDE wall
    side = lambda w: w[3]=='v' and abs(w[0]-bw)<1e-6
    rear_br2 = lambda w: (w[3]=='h' and abs(w[1]-REAR_Y)<1e-6
                          and min(_BR2_REAR)<=w[0] and w[0]+w[2]<=max(_BR2_REAR))
    b1 = [w for w in wins if side(w) and w[1]<36.0]
    b2 = [w for w in wins if (side(w) and w[1]>=36.0) or rear_br2(w)]
    op = [w for w in wins if w not in b1 and w not in b2]
    sf = lambda ws: sum(WIN_SF[w[4]] for w in ws)
    open_area = U23_AREA["KITCHEN"]+U23_AREA["LIVING / DINING"]
    return {'open':100*sf(op)/open_area, 'br1':100*sf(b1)/U23_AREA["BEDROOM 1"],
            'br2':100*sf(b2)/U23_AREA["BEDROOM 2"],
            # what is left if the window under the stair landing is discounted entirely
            'open_less_stair':100*(sf(op)-WIN_SF['A'])/open_area}
def _inside(poly, X, Y):
    """Even-odd ray test: which of the points (X, Y) fall inside the closed polygon.

    This was matplotlib.path.Path.contains_points, the last thing in the project that
    needed matplotlib — for eight vertices and a convex-ish room. Cast a ray in +x from
    each point and count the edges it crosses; odd means inside. Vectorized because the
    grid below is 185,409 points and numpy is already here for the rest of the function.

    Checked against matplotlib on exactly that grid before the swap: 0 disagreements,
    150,295 points inside either way. No grid center can land on an edge — the polygon's
    faces are eighths of a foot and the centers are odd multiples of 1/48 — so the two
    conventions for a point ON the boundary never come up."""
    import numpy as np
    inside = np.zeros(X.shape, dtype=bool)
    for i in range(len(poly)):
        x0, y0 = poly[i-1]; x1, y1 = poly[i]
        straddles = (y0 > Y) != (y1 > Y)          # the edge spans this row
        with np.errstate(divide='ignore', invalid='ignore'):
            crossing = (x1-x0)*(Y-y0)/(y1-y0) + x0
        inside ^= straddles & (X < crossing)      # a horizontal edge never straddles
    return inside


def u23_clear_rect():
    """Largest clear rectangle in the Units 2/3 common room, measured off the drawn
       fittings plus the two zones the design reserves: the landing inside the entry
       door and the clearance the mechanical closet borrows in front of its louvered
       pair. A-001's capacity note printed it until the 2026-09-16 note trim; nothing
       prints it now, and it stays as the model's measure of the room."""
    import numpy as np
    pts=[(PLAN_L1.x(a,b),PLAN_L1.y(b)) for (a,b) in OA_U23[0][0]]
    F=[(PLAN_L1.x(f[0],f[1]),PLAN_L1.y(f[1]),f[2],f[3]) for f in F_U23 if f[4] not in LOOSE]
    wall=PLAN_L1.x(LIVE_WALL_X,U2_ENTRY[1]) if U2_ENTRY[3]=='v' else None
    if wall is not None:
        d0=PLAN_L1.y(U2_ENTRY[1]); dw=U2_ENTRY[2]
        inward=-1.0 if _inside(pts,np.array([wall-0.25]),np.array([d0+dw/2]))[0] else 1.0
        F.append((min(wall,wall+5.0*inward),d0,5.0,dw))
    F.append((U23_MECH_X[0],PLAN_L1.y(44.30)-2.0,U23_MECH_X[1]-U23_MECH_X[0],2.0))
    S=1/24.0
    xs=np.arange(min(p[0] for p in pts),max(p[0] for p in pts),S)
    ys=np.arange(min(p[1] for p in pts),max(p[1] for p in pts),S)
    XX,YY=np.meshgrid(xs,ys)
    free=_inside(pts,XX.ravel()+S/2,YY.ravel()+S/2).reshape(XX.shape)
    for (x,y,w,h) in F:
        free &= ~((XX+S/2>=x)&(XX+S/2<x+w)&(YY+S/2>=y)&(YY+S/2<y+h))
    H=np.zeros(free.shape[1],dtype=int); best=(0,0,0)
    for row in free:
        H=np.where(row,H+1,0); stack=[]
        for i,h in enumerate(list(H)+[0]):
            start=i
            while stack and stack[-1][1]>=h:
                s,hh=stack.pop()
                if hh*(i-s)>best[0]: best=(hh*(i-s),hh,i-s)
                start=s
            stack.append((start,h))
    return "%s x %s"%(fmt(best[1]*S),fmt(best[2]*S))
U23_CLEAR_RECT = u23_clear_rect()

GL_U2, GL_U3 = u23_glazing(U23WIN_U2), u23_glazing(U23WIN_U3)
# The two flats glaze alike only once Unit 2's entry leaves the rear wall. Say which
# it is rather than assuming, so the note is right in both states of the flag.
GL_OPEN_TEXT = ("%d PERCENT IN THE OPEN LIVING, DINING AND KITCHEN SPACE"
                %int(min(GL_U2['open'],GL_U3['open']))
                if abs(GL_U2['open']-GL_U3['open'])<0.05 else
                "%d PERCENT IN THE OPEN LIVING, DINING AND KITCHEN SPACE OF UNIT 2 AND %d PERCENT OF UNIT 3"
                %(int(GL_U2['open']),int(GL_U3['open'])))
GL_MIN = min(GL_U2['open'],GL_U3['open'],GL_U2['br1'],GL_U2['br2'])

WD_SIDE       = _side_of(sum(_wd_span)/2.0)

# ---------------- what this building has to keep true ----------------
# These run at import, next to the geometry they measure. A check that lives
# beside its model is one that gets updated when the model moves.

def check_unit1_stair():
    """Fail the build if finished headroom / hall / landing clearance regresses."""
    assert math.isclose(FLOOR_RISE, IN(120)) and NT == 14
    assert math.isclose(RUN,IN(129.5)) and math.isclose(TREAD,IN(9.25))
    assert HEADROOM >= IN(84), 'Unit 1 design headroom must remain at least 84 inches'
    assert math.floor(HEADROOM*12*8)/8 == 84.125, 'Update the published headroom dimensions'
    # The L2 cross hall is dimensioned stud to stud like everything else, but RCO 311.6
    # is a FINISHED clearance, so the band is 37" framed to give 36" between the two
    # 1/2" gypsum faces. Print both so the sheet's 3'-1" and the note's 36" reconcile.
    assert B1-B0-IN(1) >= IN(36), 'Unit 1 finished cross hall'
    assert D_STUD-YT-IN(1.25) >= IN(36), 'Unit 1 finished top landing'
    assert YB-NOSING-LB >= IN(36), 'Unit 1 finished bottom landing'
    # The A-102 north-south string is drawn to NS_FACES_IN. Close the same tuple the
    # sheet draws, not a hand-written one, and print the segments so the closure can be
    # checked against the sheet without re-chaining the room labels — which is how a
    # reviewer lands 2-1/2" over: the bath / closet partition at y 250..253.5 is inside
    # Bedroom 4's depth, and the hall band is 3'-1" framed where A-001 says 36" clear.
    faces=NS_FACES
    assert faces[0]==0 and faces[-1]==D_STUD
    segs=[b-a for a,b in zip(faces,faces[1:])]
    assert math.isclose(sum(segs),D_STUD) and math.isclose(D_STUD,IN(278.5))
    print('UNIT 1 STAIR CHECK: %.3f inches finished headroom; hall / landings >= 36 inches'%(HEADROOM*12))
    print('UNIT 1 L2 CHECK: cross hall %.0f in framed = %.0f in clear between finished faces'
          %((B1-B0)*12,(B1-B0-IN(1))*12))
    print('   A-102 NORTH-SOUTH STRING  %s  =  %s'
          %(' + '.join(fmt(v) for v in segs),fmt(sum(segs))))

# Building 1's rear wall in the building's own y, and the RCO 302.1 imaginary line
# beyond it. The line is fsd.OFF_B1 out; nothing here types where it is.
REAR_WALL   = 48.0
LINE_LOCAL  = REAR_WALL+fsd.OFF_B1


def check_u3_stair_inside():
    """No part of the ELEVATED stair may pass the rear wall.

    Along the LIVE_SIDE face fire separation distance is measured to the centerline of
    the street, RCO 202, and the underside is unrated. Beyond the rear wall the stair
    stands in the courtyard between the buildings instead, where the governing line is
    the RCO 302.1 imaginary line — and anything within 5'-0" of it needs a 1-hour
    underside under Table 302.1(1). The concrete stoop may pass: it is a slab on the
    ground, not a projection with an underside to protect."""
    over = U3_FLIGHT_HI-REAR_WALL
    gap  = LINE_LOCAL-U3_FLIGHT_HI           # to the imaginary line
    print("UNIT 3 STAIR vs THE REAR WALL: foot of the flight at %s, %s %s the wall;"
          " stoop reaches %s past it, %s from the imaginary line %s out"
          %(fmt(U3_FLIGHT_HI),fmt(abs(over)),"past" if over>0 else "inside",
            fmt(U3_STOOP_HI-REAR_WALL),fmt(LINE_LOCAL-U3_STOOP_HI),fmt(fsd.OFF_B1)))
    assert over<=0, ("the elevated Unit 3 stair passes the rear wall by %s and is %s from the "
                     "imaginary line — inside the 5'-0\" of RCO Table 302.1(1), so its "
                     "underside would need a rating the set says it does not have"
                     %(fmt(over),fmt(gap)))

DR_TERM_MIN = 3.0                # RCO M1502.3, a dryer termination to any opening


def check_u23_terms():
    """The rear wall's one remaining termination against RCO M1502.3's 3'-0" to any
       opening. The heater's concentric vent was the other; an electric storage heater
       terminates nothing, so the bay it vented through merged into the heater bay."""
    rows=[("DR  cap 5\" in from the %s end"%DR_END_SIDE,DR_CLR,DR_CLR_NEAR)]
    floor = DR_TERM_MIN
    print("U23 REAR-WALL TERMINATIONS (minimum %s to an opening, RCO M1502.3):"%fmt(floor))
    for nm,v,near in rows:
        print("   %-32s %-11s to %s%s"%(nm,fmt(v),near,
              "" if v>=floor-1e-9 else "   <-- SHORT OF %s"%fmt(floor)))
    print("   %-32s %-11s from DR, in the %s heater bay"%("E   riser through the roof",
          fmt(abs(U23_E_RISER-U23_DR_TERM)),fmt(BAY(U23_HEATER_BAY))))
    assert all(v>=floor-1e-9 for _n,v,_k in rows), \
        "rear-wall termination clearance short of %s"%fmt(floor)
    assert abs(U23_E_RISER-U23_DR_TERM)>0.5,\
        "stack E riser is not clear of the dryer cap"

def check_u23_beds():
    """Every Units 2/3 sleeping room keeps an egress window, and every drawn bed heads on
       a wall with no opening in it. The beds are not in the contract, note 9a, but the
       claim that the rooms take one is — and Bedroom 2's used to head on the rear wall
       directly under the rear W-A, which is part of what the second window per room was
       paying for. Both are read off the opening lists, so deleting another window, or
       sliding a bed onto one, fails the build instead of the review."""
    TOL=1.0/6.0
    ov=lambda a0,a1,b0,b1: a0<b1-1e-9 and b0<a1-1e-9
    out=[]
    for nm,poly,ylo,yhi in (("BEDROOM 1",BR1_U23,24.45,35.75),("BEDROOM 2",BR2_U23,36.15,47.5)):
        xs=[q[0] for q in poly]
        egress=[w for w in U23WIN_U2 if w[4]=='A' and (
                (w[3]=='v' and abs(w[0]-rx(25.5))<1e-6
                 and ylo-TOL<=w[1] and w[1]+w[2]<=yhi+TOL)
                or (w[3]=='h' and ylo-TOL<=w[1]<=yhi+TOL
                    and min(xs)-TOL<=w[0] and w[0]+w[2]<=max(xs)+TOL))]
        assert egress, "%s has no W-A egress window"%nm
        out.append("%s %d W-A"%(nm,len(egress)))
    for (bx,by,bw,bh,kind,head) in [f for f in F_U23 if f[4]=='bed']:
        if head in 'ns':
            wy = by if head=='n' else by+bh
            bad=[w for w in U23WIN_U2 if w[3]=='h' and abs(w[1]-wy)<=TOL
                 and ov(w[0],w[0]+w[2],bx,bx+bw)]
        else:
            wx = bx if head=='w' else bx+bw
            bad=[w for w in U23WIN_U2 if w[3]=='v' and abs(w[0]-wx)<=TOL
                 and ov(w[1],w[1]+w[2],by,by+bh)]
        assert not bad, "a Units 2/3 bed heads on a wall with a W-%s in it"%bad[0][4]
    print("UNITS 2 / 3 SLEEPING ROOMS: %s; both beds head on a wall with no opening"
          %", ".join(out))

def check_u3_stair_clear():
    """Item 12. Nothing may stand under the FLIGHT — its soffit falls 8" a tread and is
       below an 8'-0" head within two of them. An opening under the top landing DECK is
       fine provided the soffit clears its head by 6"."""
    L0,L1,F1 = U3_LAND_LO,U3_LAND_HI,U3_FLIGHT_HI
    ff1   = levels.FF1
    heads = [(w,ff1+WIN_HEAD[w[4]],"W-"+w[4]) for w in U23WIN_U2 if w[3]=='v']+ \
            [(d,ff1+6.0+8.0/12.0,"D-1") for d in [U2_ENTRY] if d[3]=='v']
    print("UNIT 3 STAIR, LEVEL 1 OPENINGS ON THE %s WALL  (landing deck soffit +%s):"
          %(LIVE_SIDE,fmt(U3_LAND_SOFFIT)))
    bad=[]
    for o,head,mk in sorted(heads,key=lambda t:t[0][1]):
        if abs(o[0]-LIVE_WALL_X)>1e-6: continue
        a,b = PLAN_L1.y(o[1]), PLAN_L1.y(o[1])+o[2]
        if b<=L0+1e-6 or a>=F1-1e-6: where="clear of the stair"
        elif b<=L1+1e-6:
            slack=U3_LAND_SOFFIT-head
            where="under the landing deck — %s over its %s head"%(fmt(slack),fmt(head))
            if slack<0.5-1e-9: bad.append((mk,"soffit less than 6\" over the head"))
        else:
            where="UNDER THE FLIGHT"; bad.append((mk,"stands under the flight"))
        print("   %-5s y %-11s .. %-11s %s"%(mk,fmt(a),fmt(b),where))
    assert not bad, "Unit 3 stair fouls an opening: %s"%bad

# ---------------- what the plans are made of ----------------
# The sheets draw these; they do not invent them. All of it used to be assigned
# inside sheet_a101 and read by A-102 and the elevations through module scope, so
# the drawing order was load-bearing and the ownership was invisible.

# The interior doors, the two bypass openings and the mechanical closet's louvered pair
# are authored in the unmirrored frame and reflected; the entry door already carries the
# mirror in its own definition, because the mirror is what moves it to another wall.
U23_INT_DOORS=[(11.4,31.55,2.67,'h',1,"far"),
               (14.5,32.75,2.67,'v',1,"far"),(14.5,36.55,2.67,'v',1),
               (8.85,44.30,2.625,'h',1),(11.475,44.30,2.625,'h',1,"far")]

U23_OPENINGS=[(16.5,24.45,6.5,'v'),(16.5,41.0,6.5,'v')]

# interior strings, derived from the rooms and open areas above. Unit 1 reads across
# the top, Units 2 and 3 across the bottom, and the two side strings split at the
# central band so neither has to describe two different layouts at once.
# The vertical strings' positions are chosen, not derived — see the README. The mirror
# swaps which walls reach which exterior face, so each string's GROUP and its position
# have to swap together or a string ends up on the far side of the plan from the band
# it describes, which is silent: every number stays arithmetically right.
_SWAP={'lo':'hi','hi':'lo'}

def rplan(entries):
    return [(_SWAP.get(g,g),rx(at),-sd,_SWAP.get(side,side)) for (g,at,sd,side) in entries]

CH_IN_AT    = rx(17.65)      # the interior sweep, clear of the D-5 leaves

CH_CARVE_AT = rx(8.3)        # the carved mechanical-closet depth, on its own line

def b1_chains(top_r,top_p,all_r,all_p,ytop,furn,bottom_at=48.85):
    """A-101 / A-102. Horizontal strings serve one unit band each — Unit 1 off the top,
       Units 2 and 3 off the bottom. Vertical strings serve the walls that reach the low
       plan x face, those that reach the high one, and one further out for the partitions
       that reach neither."""
    ch =strings(wall_faces(top_r,top_p,0,(0.5,23.55),(0.5,25.5)),(0.5,25.5),(0.5,23.55),'h',
                [('lo',-0.85,1,'lo'),('in',ytop,1,'near')])
    ch+=strings(wall_faces(U23,OA_U23,0,(24.45,47.5),(0.5,25.5)),(0.5,25.5),(24.45,47.5),'h',
                [('hi',bottom_at,-1,'hi'),('in',31.0,-1,'near')])
    vf =wall_faces(all_r,all_p,1,(0.5,25.5),(0.5,47.5))
    ch+=strings(vf,(0.5,47.5),(0.5,25.5),'v',
                rplan([('lo',-7.0,-1,'lo'),('hi',27.4,1,'hi'),('in',17.65,1,'near')]))
    # MECH's top face and the kitchen/living notch's corner fall, by y-coordinate alone,
    # inside Bedroom 2's own closet opening (41.0-47.5) — three rooms away in x, but the
    # sweep can't tell. Give them their own line.
    ch=carve(ch,'v',41.0,47.5,CH_CARVE_AT,vf)
    ch=unbridge(ch,vf,'v')
    ch=drop(ch,'v',CH_IN_AT,(31.55,31.95))
    # MECH's top wall, same treatment: 3-1/2" of ordinary partition, marked with two
    # ticks and two witness rails for a stub of line carrying no number. Keep the face
    # MECH's own 3'-3-5/8" is measured from and let the other derive from it.
    #
    # The closet jamb goes with it. carve kept it as the cut's upper anchor, so this
    # string ran from a jamb in the bedroom, across the partition, to MECH's top wall —
    # 3'-2-3/8" between two walls with nothing to do with each other. It is already
    # ticked on the closet's own 6'-6", and MECH's top is located by the 3'-3-5/8" to
    # the rear wall, so the string is complete without it.
    ch=drop(ch,'v',CH_CARVE_AT,(43.9,41.0))
    # The remaining carved string is the Units 2/3 mechanical-closet depth.
    # Put its label on the living-space side of the line, clear of the closet wall.
    return [(cs,o,at,(-sd if o=='v' and abs(at-CH_CARVE_AT)<1e-6 else sd),ml,mk,la)
            for (cs,o,at,sd,ml,mk,la) in ch]

CTX_B1=("S ELM AVENUE  —  FRONT OF LOT  ·  20'-0\" BUILDING LINE",
        ("SAGE AVENUE","SIDE STREET  ·  8'-0\" BUILDING LINE, C.C. 3332.22(a)(1)"),
        ("ADJACENT PARCEL","6'-0\" INTERIOR SIDE YARD  ·  NOT A STREET"),
        "REAR YARD  —  12'-0\" TO BUILDING 2, PARKING AND ALLEY BEYOND")

# The two levels' opening lists, which both the plans and the elevations read.
L1_WINS, L1_DOORS = list(U23WIN_U2), [U2_ENTRY]+rdoors(U23_INT_DOORS)
L2_WINS, L2_DOORS = list(U23WIN_U3), [U3_ENTRY]+rdoors(U23_INT_DOORS)
L1_OPENINGS = L2_OPENINGS = rops(U23_OPENINGS)


# ---------------- the two levels, as the plan sheets take them ----------------
# Everything that is the same on both levels is written once here, which is the point:
# the A-101 and A-102 calls used to pass eighteen arguments each, twelve of them
# identical, with nothing checking that the pair stayed in step.
# NOT DRAWN. This is the joist bay layout as MODEL DATA: U23_BEARING_WALL below is
# derived from it, so S-101's strip follows the bays, and src/framing.py's B1_FLOOR
# takes the same wall. The span arrows these used to print on A-101 / A-102 are gone —
# S-102 owns floor framing and states it once. The "F1 I-JOISTS" strings are the arrow
# prefixes draw_the_annotation would have used; they are kept so the tuple still reads
# as what it is, and so restoring the arrows is a one-word change at the sheet call.
_B1_JOISTS = [rjoist(j) for j in [(0.5,39.8,14.1,"F1 I-JOISTS"),
                                  (14.5,34.9,25.5,"F1 I-JOISTS")]]
# The wall the two F1 joist bays meet on: the Units 2/3 floor bears on it, so S-101
# casts a strip under it. Derived from the joist plan above rather than typed, in final
# sheet coordinates, the full depth of the grouping — W4's grouping face to the rear
# stud face. The reflected model runs the opposite way to the sheet, hence B1_W - x.
_bays = sorted((j[0], j[2]) for j in _B1_JOISTS)
U23_BEARING_WALL = (B1_W-PLAN_L1.x(_bays[1][0], 30.0), Y_SEP_BOT,
                    B1_W-PLAN_L1.x(_bays[0][1], 30.0), 48.0-EXT_STUD)
# The overall vertical dimension goes beyond the Unit 3 stair, whichever side that is;
# the two redundant 24'-0" strings are omitted. A raw x beyond the building extrapolates
# off the end of the regrid map, so -9.8 and rx(-9.8) both land 9'-9-5/8" clear.
_B1_DIMS   = [(0,26,'h',-2.2,None),(0,48,'v',rx(-9.8),"48'-0\"")]

# Which regrid, which openings. One row per level, so the three things that have to
# agree — the map, the doors and the windows — are chosen together and cannot be
# mismatched by a call site. PLAN_L1 and PLAN_L2 differ because Unit 1's partitions sit
# in different places on the two floors, so handing a sheet Level 1's doors with Level
# 2's map would draw every Units 2/3 opening at the wrong y.
_B1_LEVELS = {1: (PLAN_L1, L1_DOORS, L1_WINS),
              2: (PLAN_L2, L2_DOORS, L2_WINS)}


def _b1_level(level, notes, chains, fixed_chains, units, tags=None, u3stair=False,
              draw_u3_stair=None, draw_u3_landing_label=None, draw_unit1=None,
              annotate=True):
    """One Building 1 level, chosen by its number and nothing else.

    The level number picks the regrid AND the opening lists together. It used to take
    the plan as well, which meant the pairing was the caller's to get right while this
    docstring claimed it was not — the promise and the signature disagreed, and the
    signature would have won.
    """
    assert level in _B1_LEVELS, "Building 1 has levels %s, not %r"%(
        sorted(_B1_LEVELS), level)
    plan, doors, wins = _B1_LEVELS[level]
    # This project's own drawing, at all three of the moments the library offers, and
    # WHICH moment is load-bearing for each.
    #
    # Unit 1 draws a whole plan of its own, starting with an opaque white rectangle over
    # its half of the building -- it is authored in inches straight onto the canvas, so
    # it has to clear whatever the library drew there. That makes it a PLAN, and it used
    # to run at over_dims, after the dimension strings: anything the annotation had put
    # inside Unit 1's area was painted out. One casualty was real and on the issued
    # sheets -- the 5'-0" label of the Units 2/3 interior string, pushed to an outer row
    # that lands 1.4 pt inside Unit 1's rectangle, so A-101 and A-102 each printed that
    # dimension nowhere. At over_plan the rectangle still covers the library's drawing,
    # which is its job, and the dimensions land on top of the finished plan, which is
    # where dimensions go.
    #
    # The Unit 3 exterior stair stays at over_dims: it must go OVER the strings or their
    # label masks cut into its landing annotation. The landing label is last of all so
    # nothing can cover it.
    def _over_plan(pp):  draw_unit1(pp, level, annotate)
    def _over_dims(pp):  draw_u3_stair(pp, 26, plan, above=u3stair, annotate=annotate)
    def _over_all(pp):   draw_u3_landing_label(pp, 26, plan)
    return PlanLevel(plan=plan, W=26, D=48,
                     captions=CLEARANCE_CAPTIONS, wall_finish=BOARD,
                     over_plan=_over_plan, over_dims=_over_dims, over_all=_over_all,
                     stair_side=3.0,
                     rooms=list(U23), openareas=OA_U23, furn=F_U23,
                     doors=doors, wins=wins, openings=L1_OPENINGS,   # same both levels
                     dims=list(_B1_DIMS), joists=(), sep=Y_SEP_TOP, sep_rows=(W4_STUD, W4_CORE, W4_STUD),   # framing: S-102
                     notes=notes, tags=tags, chains=chains, fixed_chains=fixed_chains,
                     units=units, ctx=CTX_B1)


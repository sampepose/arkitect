"""Building 2 — Units 2 and 3, the two stacked ADUs, 20'-0" x 33'-0" at the rear of the lot.

400 Oak Ave's rear building, squeezed from 300 S Elm's 26'-0" x 28'-0" Building 2.
Everything it IS, in the order it has to be built: the rooms, the open areas the plan is
punched out of, PLAN_B2 to regrid them, the Unit 3 stair placed against the courtyard
face, and then the openings.

THE PLAN. Three bands, courtyard to alley, on one bearing wall behind the front band.

  * The front band is one open room: the kitchen along the courtyard wall and down the
    side wall to the sink, the living space and the entry at the other side. The
    mechanical / laundry room opens off the kitchen through a louvered pair in the
    bearing wall, so its dryer duct goes straight out its side wall.
  * The middle band is the bath, the hall and the mechanical / laundry room. The hall
    opens to the front band through the bearing wall and runs on into a short
    vestibule between the bedrooms, so nothing is entered through the living space.
  * The rear band is the two bedrooms, side by side, each entered from the vestibule,
    with its reach-in on the partition between them and its egress W-A in its side
    wall — the rear wall faces the parking pad.
  * The floor is F1 open-web floor trusses in two bays, courtyard wall to the bearing wall and the
    bearing wall to the rear. NOT CHECKED for this building yet (no framing model runs).

NUMBERING. Unit 1 is the house (Building 1); Unit 2 is Level 1 here and Unit 3 is Level 2.
Every PRINTED string uses that. The identifiers keep 300's numbering — U5_* is Unit 3's
stair, U45_* and GL_U45 are Units 2 and 3 — because the copied 300 modules not yet in
this build import them by those names.

Model coordinates are PRE-mirror: x runs from one neighbour's side (x 0) to the other's
(x B2_W, 300's Sage side), y from the courtyard face to the rear. The sheet mirror
puts the x = B2_W side on the left.

What is NOT here: the drawing, which is A-102, and the stair check, which needs the canvas.
"""
from src.openings import WIN_GEOM, WIN_HEAD, WIN_SF, WIN_W
from arkitect.lib.model import geom
from src import envelope, fsd, levels
from src.finishes import BOARD as GYP     # the finish on a stud face, as Building 1 reads it
from arkitect.codes.ohio.rco import fire_separation as rco_fsd
from arkitect.lib.units import IN, fmt
from arkitect.lib.model.records import PlanLevel
from arkitect.codes.columbus.legends import CLEARANCE_CAPTIONS
from arkitect.lib.model.regrid import EXT_STUD, PARTITION, Zone, Plan
from arkitect.lib.model.dimensions import strings, wall_faces
from src.stairs import EXT_STAIR

# 400 Oak Ave's rear building: 20'-0" x 33'-0", squeezed from 300's 26'-0" x 28'-0".
# At 20'-0" 300's plan — both bedrooms across the width either side of a 5'-0" bath
# column — leaves each bedroom 6'-9", under RCO 304.2's 7'-0". So the same rooms are
# laid front to back instead (the designer's option A, 2026-09-17): the open living / kitchen
# band at the courtyard, a middle band of bath, hall and mechanical / laundry room,
# and the two bedrooms side by side at the alley end, entered from a short vestibule
# the hall runs into. Model x runs from one neighbour's side (x 0) to the other's
# (x B2_W, which 300 called Sage); y from the courtyard face to the rear.
B2_W, B2_D = 20.0, 33.0

# ---------------- the rooms ----------------
# The ONE bay of the north wall that is framed deeper, because stack F's fittings do not fit
# a 2x6 (A-601's section, `envelope.stack_bay_*`). It is a plan fact as much as a section
# one: its face stands into the mechanical / laundry room of both units, so the plans draw
# and dimension it and nothing may be drawn inside it.
STACK_BAY_PROJ = envelope.stack_bay_projection()
STACK_BAY_W = envelope.STUD_OC+envelope.STUD_T        # the bay and the stud each side of it
BAY_PEN_CLR = IN(2)                   # a duct or a pipe through this wall, clear of a bay stud

Y_BEAR = 12.5                    # front face of the bearing wall, model y
Y_MID1 = 18.4                    # the middle band's rear face
X_MECH_HALL = 12.1               # the mechanical / laundry room's hall-side face
# Unit 2's bath ceiling is a SOFFIT, framed and boarded below the rated F1 membrane and not part
# of it: UL L528 gives this floor no ceiling damper and no recessed luminaire (src/framing.py), so
# the bath's fan, its duct to the south wall and its light hang in the soffit and the membrane over
# them is whole. The whole room, so nobody has to find an edge.
U2_SOFFIT_ROOMS = ('BATH',)
U2_SOFFIT_DROP = IN(8)           # below the F1 ceiling: a 4" duct, the fan's housing and 2x framing
Y_REAR = 32.5                    # the rear wall's inside face
X_HALL0, X_HALL1 = 8.3, 11.7     # the hall, and the vestibule it runs on into
Y_VEST = 22.3                    # the vestibule's end, between the two bedrooms
X_BR   = 9.8                     # the partition between the bedrooms, its Bedroom 1 face

CL_RUN     = 6.0                 # 6'-0" of bypass door on each reach-in
CL_Y0      = Y_REAR-CL_RUN

B2U=[(X_HALL0,Y_BEAR+PARTITION,X_HALL1-X_HALL0,Y_VEST-Y_BEAR-PARTITION,"HALL"),
     (0.5,Y_BEAR+PARTITION,7.4,Y_MID1-Y_BEAR-PARTITION,"BATH",(0.0,-0.9)),
     (X_MECH_HALL,Y_BEAR+PARTITION,7.4,Y_MID1-Y_BEAR-PARTITION,"MECH / LAUNDRY",(0.0,0.0),"compact"),
     (X_BR-2.0,CL_Y0,2.0,CL_RUN,"CL."),
     (X_BR+PARTITION,CL_Y0,2.0,CL_RUN,"CL.")]

# The open front band; the two bedrooms, each wrapping the vestibule at its front and
# notched at the rear for its reach-in. A closet's opening face is the room's edge.
Y_BR = Y_MID1+PARTITION
OPEN_B2=[(0.5,0.5),(19.5,0.5),(19.5,Y_BEAR),(0.5,Y_BEAR)]
BR1_B2=[(0.5,Y_BR),(X_HALL0-PARTITION,Y_BR),(X_HALL0-PARTITION,Y_VEST+PARTITION),
        (X_BR,Y_VEST+PARTITION),(X_BR,CL_Y0),(X_BR-2.0,CL_Y0),(X_BR-2.0,Y_REAR),(0.5,Y_REAR)]
BR2_B2=[(X_HALL1+PARTITION,Y_BR),(19.5,Y_BR),(19.5,Y_REAR),(X_BR+PARTITION+2.0,Y_REAR),
        (X_BR+PARTITION+2.0,CL_Y0),(X_BR+PARTITION,CL_Y0),(X_BR+PARTITION,Y_VEST+PARTITION),
        (X_HALL1+PARTITION,Y_VEST+PARTITION)]

# The living / kitchen split is a design statement, not a wall: the living side ends
# where the fridge does. Its two areas are computed from the regridded polygon below
# and written back into the labels, so the figures on the sheet are measured.
X_SPLIT = 6.7

def _open_labels(living_sf="", kitchen_sf=""):
    return [(3.4,7.0,"LIVING","",living_sf),
            (13.0,7.0,"KITCHEN / DINING","",kitchen_sf)]

OA_B2=[(OPEN_B2,_open_labels()),
       (BR1_B2,[(4.0,22.4,"BEDROOM 1",None,"AUTO SF")]),
       (BR2_B2,[(16.0,22.4,"BEDROOM 2",None,"AUTO SF")])]

B2_YHOLD={(CL_Y0,Y_REAR,CL_RUN)}

PLAN_B2 = Plan([Zone(B2U,OA_B2,0.5,Y_REAR,B2_W,EXT_STUD,B2_D-EXT_STUD,
                     yhold=B2_YHOLD)],B2_W,B2_D)

_area = geom.area          # the local name this module already uses in places
_open_r = PLAN_B2.poly([OA_B2[0]])[0][0]
LIVING_SF, KITCHEN_SF = geom.split(_open_r, PLAN_B2.x(X_SPLIT,5.0), 'x')
assert abs(LIVING_SF+KITCHEN_SF-geom.area(_open_r)) < 1e-6
OA_B2[0]=(OPEN_B2,_open_labels("%d SF"%round(LIVING_SF),"%d SF"%round(KITCHEN_SF)))

# ---------------- fittings ----------------
# (x,y,w,h,kind,face) in plan feet. Beds are drawn to show each sleeping room takes one
# with its door swing and egress window clear and its head on the bearing wall, which
# carries no opening behind either bed; loose seating and dining are listed for the
# capacity study and not drawn.
# The washer and the bay behind it, stated ONCE and before anything is placed against
# either: the stack stands 5" in from the far side of the W/D, as src/drainage.py takes it,
# so the bay's centreline follows the appliance and the plan and the riser cannot disagree.
WD_W, WD_H = 2.83, 2.25
WD_X, WD_Y = 16.67-STACK_BAY_PROJ, Y_BEAR+PARTITION
STACK_BAY_CL = WD_Y+WD_H-IN(5)
STACK_BAY_Y0 = STACK_BAY_CL-STACK_BAY_W/2.0
STACK_BAY_Y1 = STACK_BAY_CL+STACK_BAY_W/2.0
# The panel begins past the bay's far stud. It stood 3-1/8" on the bay, which would have
# put a flush panel can across the 2x8 framing; moving it ALONG the wall costs nothing.
PANEL_CLR = IN(2)
_PANEL_Y = STACK_BAY_Y1+PANEL_CLR
_PANEL_SPACE_LEAD = 0.25              # how far the 110.26(A)(2) band starts ahead of the can

F_B2=[# bath, 7'-5" x 5'-6": the tub across the exterior-wall end, the pan and the vanity
      # on the rear partition facing the door, which enters from the hall at the far end
      (0.5,Y_BEAR+PARTITION,2.5,5.0,'tub','n','n'),
      (3.4,Y_MID1-2.33,1.67,2.33,'wc','s'),          # tank on the rear partition
      (5.6,Y_MID1-1.5,2.0,1.5,'lav','n'),
      # kitchen: the run along the courtyard wall, under the Unit 3 flight where Unit 2's
      # wall can carry no window; the sink on the side-wall leg under W-A
      (9.8,0.5,7.7,2.0,'counter'),(13.0,0.5,2.5,2.0,'range','s'),
      (6.7,0.5,3.0,2.5,'fridge','n'),
      (17.5,2.5,2.0,6.0,'counter'),(17.5,3.25,2.0,2.5,'sink'),
      # dining at the kitchen end — 4'-0" table
      (10.5,5.5,4.0,2.5,'table'),
      (11.0,4.2,1.3,1.3,'chair'),(12.9,4.2,1.3,1.3,'chair'),
      (11.0,8.0,1.3,1.3,'chair'),(12.9,8.0,1.3,1.3,'chair'),
      (1.0,9.4,6.0,2.6,'sofa','n'),
      # mechanical closet: the stacked W/D in the corner at the top, then the panel,
      # then the 40-gallon storage heater at the far end of the same 5'-6" Sage wall
      # — 2'-3" + 1'-2-3/8" + 1'-6", which is 4'-11-3/8" of 5'-6". The tank's 30" x 30"
      # working space is borrowed through the open louvered pair, as the tankless's was.
      # The four tank numbers are SOLVED against the stud grid, which stretches this
      # band, so that what is finally drawn is 18" square; check_working_spaces() proves
      # it.
      #
      # 400 OAK: the room is 7'-5" x 5'-6" against the side wall, so the W/D, the panel
      # and the heater stand along that wall in the same order. These figures are PLACED,
      # not solved against the stud grid as 300's were; check_working_spaces() is not
      # run for this building yet.
      # Held OFF the north wall by the deepened stack bay behind it: A-601 frames that bay
      # 2x8 for stack F's fittings, so its face stands STACK_BAY_PROJ into the room and an
      # appliance drawn to the wall would sit inside it. `stack_bay_violations()` says so.
      (WD_X,WD_Y,WD_W,WD_H,'wd'),
      # The heater stands in the room's REAR HALL-SIDE corner, off the north wall: on that
      # wall its tank stood 6-5/8" inside the panel's 30" band, which plumbing's
      # check_working_spaces() refuses. Its own 30" x 30" is beside it, toward the panel's.
      (X_MECH_HALL,Y_MID1-1.5,1.52,1.49,'wh'),
      (X_MECH_HALL+1.52,Y_MID1-2.55,2.55,2.55,'whclear'),
      # the 100 A panel on the same Sage wall, in the gap between the W/D and the
      # heater; its 30" x 36" working space reaches across the closet from the W/D's
      # edge (NEC 110.26(A)(2) does not centre it) and overlaps the heater's, as Units
      # 2/3's does. E-102 wires it.
      #
      # THIS CLOSET CANNOT GIVE THAT SPACE A CLEAR FLOOR, and never could: it is
      # 3'-4-3/4" deep, so everything in it stands inside the panel's 36", and 2'-3" of
      # W/D plus 2'-6" of 110.26(A)(2) band plus 1'-6" of tank is 6'-3" on a 5'-6" wall.
      # Nine inches has to sit inside the band whatever the tank's diameter — it would
      # still be nine with no tank at all. The 18" tank leaves 0.94 SF of itself in the
      # band against the 0.89 SF the tankless already leaves, so the condition the set
      # carries does not get worse, and nothing here moves. Recorded for the designer in
      # CLAUDE.md and pinned by plumbing.PANEL_SPACE_EXCEPTION.
      # Held clear of the deepened stack bay ALONG the wall: the bay's face stands 1-3/4"
      # into the room over the stack, and the panel's lower 3-1/8" sat on it. Derived from
      # the bay so it cannot drift back into it.
      (19.25,_PANEL_Y,0.25,1.2,'panel','w'),
      (16.25,_PANEL_Y-_PANEL_SPACE_LEAD,3.0,2.5,'clear','n'),
      # beds: head on the rear wall, clear of the side-wall egress window
      (1.4,Y_REAR-6.6667,5.0,6.6667,'bed','s'),
      (13.6,Y_REAR-6.6667,5.0,6.6667,'bed','s')]

# ---------------- Unit 3 exterior stair, Building 2 ----------------
# Units 2 and 3 stack exactly and share one door position, so the top landing has to
# be at that door and the flight can only run one way along the face it is on.
#
# FACE. Two are possible and they trade the same way 300's Unit 3 stair did.
#   SAGE   — fire separation distance is measured to the street centreline, RCO 202,
#               so the underside is unrated; but the stair projects 3'-6" into the same
#               8'-0" side-street building line that is already with Zoning Clearance
#               for 300's Unit 3, and Unit 3's door would have to leave Unit 2's face.
#   COURTYARD — the RCO 302.1 imaginary line stands 10'-0" off this face on 400 Oak's
#               15'-0" courtyard (src/fsd.py), so a 3'-6" projection leaves 6'-6" to
#               it, past the 5'-0" of Table 302.1(1): the underside is unrated here too. No building line reaches
#               the courtyard: there is no zoning question at all, and both flats keep
#               the same door.
# The courtyard is chosen, and now it costs nothing at all. It used to buy a listed
# 1-hour underside — the line was the courtyard midline, 6'-0" out, and the stair left
# 2'-6" to it. Flip U5_STAIR_COURTYARD to move it, and the rating, the notes and the
# schedule row follow; move fsd.OFF_B1 and the clearance does.
U5_STAIR_COURTYARD = True

# 400 OAK: the standard 3'-6" top landing. 300's 7'-0" landing covered the Unit 2 door
# AND a W-A, but stoop, flight and that landing run 21'-3-1/2" along the face, and this
# building is 20'-0" wide; at 3'-6" they run 17'-9-1/2". The landing now covers the
# door only, so the courtyard face takes no W-A.
U5_STAIR     = EXT_STAIR

U5_STAIR_W   = U5_STAIR.width

U5_LAND_LEN  = U5_STAIR.landing_len

U5_LAND_D    = U5_STAIR.landing_depth

U5_RISERS, U5_TREADS, U5_TREAD = U5_STAIR.risers, U5_STAIR.treads, U5_STAIR.tread

U5_RUN       = U5_STAIR.run

U5_STOOP_Z   = U5_STAIR.stoop_above_grade

U5_JAMB      = 4.0/12.0

# Unit 2 / Unit 3's door: 2'-0" of wall from the adjacent-parcel corner to the jamb,
# authored through Plan.inv_x so the regrid cannot move it, and read back in FINAL
# SHEET coordinates on the courtyard face.
_b2door      = (PLAN_B2.inv_x(2.0,0.5),0.5,3.0,'h',-1,"ext")

_b2door_r    = PLAN_B2.span(_b2door)

U5_DOOR_X0   = B2_W-(_b2door_r[0]+_b2door_r[2])

U5_DOOR_X1   = B2_W-_b2door_r[0]

# Landing pushed hard against the adjacent-parcel end, so the flight gets the long
# side of the face. True feet, like 300's Unit 3 stair, not regridded.
U5_LAND_X1   = U5_DOOR_X1+U5_JAMB

U5_LAND_X0   = U5_LAND_X1-U5_LAND_LEN

U5_FLIGHT_X0 = U5_LAND_X0-U5_RUN

U5_STOOP_X0  = U5_FLIGHT_X0-U5_LAND_D

# What the stair leaves to the line it is measured to, and whether Table 302.1(1) asks
# anything of its underside at that distance. Both are DERIVED — the distance from
# src/fsd.py, the rating from the table — because getting this the wrong way round
# prints the opposite of the truth on four sheets.
U5_FSD         = fsd.OFF_B2 if U5_STAIR_COURTYARD else 8.0

U5_STAIR_CLR   = U5_FSD-U5_STAIR_W

U5_STAIR_RATED = rco_fsd.projection_rating(U5_STAIR_CLR) != 'NONE' if U5_STAIR_COURTYARD else False

U5_STAIR_LINE  = "IMAGINARY LINE BETWEEN THE BUILDINGS" if U5_STAIR_COURTYARD else "SAGE RIGHT-OF-WAY"

U5_STAIR_TAG   = ("%s TO THE %s · 1-HR UNDERSIDE"%(fmt(U5_STAIR_CLR),"IMAGINARY LINE")
                  if U5_STAIR_RATED else
                  "%s TO THE IMAGINARY LINE — UNRATED"%fmt(U5_STAIR_CLR)
                  if U5_STAIR_COURTYARD else
                  "%s TO SAGE R.O.W. — FSD TO STREET CENTERLINE — UNRATED"%fmt(U5_STAIR_CLR))

# There is no rated underside on this stair any more. The listed assembly it used to
# carry — UL Design I504, three layers of 5/8" Type X on steel studs hung under the
# landing frame — was the whole reason the stair was steel: a wood stair has nothing
# convenient to fasten a runner to. On 400 Oak the stair stands 6'-6" from the line
# (src/fsd.py), Table 302.1(1) asks nothing of a projection at 5'-0" or more, and the
# membrane and the steel both go.
# docs/superpowers/specs/2026-09-15-imaginary-line-wood-stairs-design.md
U5_UNDERSIDE   = None

# A rated underside hangs BELOW the landing framing, so Unit 2's head clearance is what
# pays for it, and check_u5_stair_clear() measures from the membrane rather than from the
# framing. There is none now, and Unit 2's door and its W-A get the 5-1/2" back: the
# soffit rises from +9'-2-1/2" to +9'-8". The conditional stays because it is what would
# put the membrane back if the stair ever came within 5'-0" of the line.
U5_MEMBRANE    = IN(3.625)+3*IN(0.625) if U5_STAIR_RATED else 0.0

U5_LAND_SOFFIT = U5_STAIR.soffit-U5_MEMBRANE

# ---------------- the openings ----------------
# The courtyard face carries the Unit 3 stair for 17'-9-1/2" of its 20'-0", and its
# landing covers only the door, so Level 1 takes no window on that face.

# The x = B2_W side wall, north: the kitchen's window over the sink, and Bedroom 2's egress
# W-A ahead of the foot of the bed. The sink's is a W-B (400 Oak, 2026-09-18): 300 drew a
# W-A there, whose 2'-0" sill stands a foot below the counter in front of it.
_b2_sink = next(f for f in F_B2 if f[4] == 'sink')
B2_SAFF_WIN  = (B2_W-0.5,_b2_sink[1]+_b2_sink[3]/2.0-WIN_W["B"]/2.0,WIN_W["B"],'v',"B")
# Stack E's furred chase, P-101 / P-601: the two kitchen sinks stand under this window on both
# levels, so their stack cannot rise behind them. It stands at the back of the counter just past
# the window's rear jamb and its casing, against the north wall, the same on both levels.
CHASE = IN(8)
STACK_E_CHASE = (B2_W-0.5-CHASE,B2_SAFF_WIN[1]+B2_SAFF_WIN[2]+IN(5),CHASE,CHASE,'chase')
F_B2.append(STACK_E_CHASE)
assert WIN_GEOM["B"][0] >= 3.0+IN(6), "the sink's window sill is not clear of the counter and its backsplash"
B2_BR2_WIN   = (B2_W-0.5,Y_BR+1.2,3.0,'v',"A")

# Building 2, as drawn on C-101, and the openings in the wall its own service goes on.
# Units 2 and 3 used to be metered at Building 1 with a feeder each run back underground
# — two feeders supplying one structure, which NEC 225.30 allows only by special
# permission, and a buried gas line for their two heaters that no sheet drew. Building 2
# takes its own service instead, so both questions go away and the 39'-6" of trench with
# them. Its exterior lighting goes on a Building 2 house meter for the same reason: a
# house circuit brought over from Building 1 would be a second supply to this structure.
B2_X0, B2_Y0 = 8.0, 80.0

B2_PARCEL_X = B2_X0+B2_W

# Building 2's parcel-wall openings, named here rather than inside B2win on A-102,
# because C-101 places the service against them and is drawn long before A-102 is:
# the living space's W-C, and Bedroom 1's egress W-A past the foot of the bed.
B2_PARCEL_WIN = [(0.5,3.0,5.0,'v',"C"),(0.5,Y_BR+1.2,3.0,'v',"A")]

B2_WALL_OPEN = sorted((B2_Y0+w[1], B2_Y0+w[1]+w[2], w[4]) for w in B2_PARCEL_WIN)

# Rear wall: each bedroom's second W-A, over the head of its bed. Bedroom 2's is set
# as the mirror of Bedroom 1's about the middle of the wall, as drawn.
# 2.52, not 300's 2.4: the corner beside it is then 30", a CS-WSP panel at Level 2's 9'-0-1/4" wall
# height (Table 602.10.5's 10 ft column), so the rear line has three panels on both levels (S-104).
_b2w_rear_br1 = (2.52,Y_REAR,3.0,'h',"A")
_b2w_rear_br2 = PLAN_B2.inv_x(B2_W-PLAN_B2.x(_b2w_rear_br1[0],Y_REAR)-3.0,Y_REAR)
B2_REAR_WIN  = [_b2w_rear_br1,(_b2w_rear_br2,Y_REAR,3.0,'h',"A")]

B2win=[B2_SAFF_WIN,B2_PARCEL_WIN[0],
       B2_PARCEL_WIN[1],B2_BR2_WIN]+B2_REAR_WIN

# Unit 3's kitchen window, Level 2 only: a W-C in the courtyard wall over the counter,
# centred between the fridge and the range as the plan draws them — the designer's pick over the
# W-B first drawn there; its 5'-0" runs 1/2" past that 4'-11" of counter each side. Unit 2
# cannot take it
# — below, that wall is under the Unit 3 flight and stoop, check_u5_stair_clear() — but
# Unit 3's sill stands some 11'-0" over the treads beside it, so it is no stair glazing
# under RCO 308.4.6, and the courtyard face is 9'-0" from the imaginary line, where Table
# 302.1(1) sets no opening limit. B2win stays the list both levels share.
_b2_fridge = next(f for f in F_B2 if f[4] == 'fridge')
_b2_range  = next(f for f in F_B2 if f[4] == 'range')
_b2_kit_mid = (PLAN_B2.x(_b2_fridge[0],0.5)+_b2_fridge[2]+PLAN_B2.x(_b2_range[0],0.5))/2.0
# A W-B on this lot (2026-09-18): Building 2 is 20'-0" here, not 300's 26'-0", and the
# counter between the fridge and the range is 3'-2"; the W-C carried over from 300 stood
# 11" behind the fridge and 11" over the range.
_b2_kit_mark = "B"
B2_U5_KITCHEN_WIN = (PLAN_B2.inv_x(_b2_kit_mid-WIN_W[_b2_kit_mark]/2.0,0.5),0.5,WIN_W[_b2_kit_mark],'h',_b2_kit_mark)

_kw0 = PLAN_B2.x(B2_U5_KITCHEN_WIN[0],0.5)
assert PLAN_B2.x(_b2_fridge[0],0.5)+_b2_fridge[2] <= _kw0+1e-6 and _kw0+B2_U5_KITCHEN_WIN[2] <= PLAN_B2.x(_b2_range[0],0.5)+1e-6, \
    "Unit 3's kitchen window stands behind the fridge or over the range"

def b2_wins(level):
    """Building 2's windows on one level: the shared list, and Unit 3's kitchen W-C above."""
    return B2win+([B2_U5_KITCHEN_WIN] if level == 2 else [])

# The entry; the bath door and the two bedroom doors off the hall and its vestibule;
# and the louvered pair, D-4A, from the kitchen into the mechanical / laundry room
# through the bearing wall.
D4A = 2.0+2.0/12.0
_WALL_X0 = X_HALL0-PARTITION/2.0          # the hall's two side walls, on their centrelines
_WALL_X1 = X_HALL1+PARTITION/2.0
B2doors=[_b2door,
         (_WALL_X0,Y_BEAR+PARTITION+0.4,2.67,'v',-1),
         (_WALL_X0,Y_BR+0.4,2.67,'v',-1),(_WALL_X1,Y_BR+0.4,2.67,'v',1),
         # The pair swings OUT, into the kitchen. It swung into the room until 2026-09-21,
         # where the washer stands across the last 9-1/2" of the opening and stopped the near
         # leaf at about 17 degrees. 300's pair, which this is a copy of, always swung out; the
         # sign did not survive the wall being turned through ninety degrees ('v' to 'h', and
         # `mirror.mdoors` flips a vertical door's swing and not a horizontal one's).
         (13.0,Y_BEAR+PARTITION/2.0,D4A,'h',1),(13.0+D4A,Y_BEAR+PARTITION/2.0,D4A,'h',1,"far")]

# The hall's opening in the bearing wall, and the two D-5 bypass fronts.
B2op=[(X_HALL0,Y_BEAR+PARTITION/2.0,X_HALL1-X_HALL0,'h'),
      (X_BR-2.0,CL_Y0,CL_RUN,'v'),(X_BR+PARTITION+2.0,CL_Y0,CL_RUN,'v')]

U45_HALL_OPEN = B2op[0][2]

B2dims=[(0,B2_W,'h',-5.6,None),(0,B2_D,'v',-3.4,None)]

# The floor: F1 floor trusses in two bays spanning courtyard to rear, meeting on the
# bearing wall between the living space and the middle band. NOT DRAWN — model data.
# 400 OAK: the rear bay spans about 20'-0", and no framing check runs yet.
_B2_JOISTS=[(0.5,6.0,Y_BEAR,"F1 FLOOR TRUSSES",'v'),(Y_BEAR+PARTITION,6.0,Y_REAR,"F1 FLOOR TRUSSES",'v')]

# The wall the two bays meet on, in final sheet coordinates, the full width of the
# building like W4's strip. Derived from the joist plan, not typed, so moving a bay
# moves the strip S-101 casts under it.
_b2_bays = sorted((j[0], j[2]) for j in _B2_JOISTS)
U45_BEARING_WALL = (0.0, PLAN_B2.y(_b2_bays[0][1]), B2_W, PLAN_B2.y(_b2_bays[1][0]))

B2notes=[(17.9,Y_BEAR+1.55,"W/D",5.2)]

# ---------------- the dimension strings ----------------
# Horizontal: the walls that reach the rear wall, off the bottom of the plan. Nothing
# but the exterior reaches the courtyard face, so there is no top string.
_hf = wall_faces(B2U,OA_B2,0,(0.5,Y_REAR),(0.5,B2_W-0.5))
CH_B2 = strings(_hf,(0.5,B2_W-0.5),(0.5,Y_REAR),'h',
                [('hi',Y_REAR+1.35,-1,'hi')])
# Vertical: the two side strings.
_vf = wall_faces(B2U,OA_B2,1,(0.5,B2_W-0.5),(0.5,Y_REAR))
CH_B2 += strings(_vf,(0.5,Y_REAR),(0.5,B2_W-0.5),'v',
                 [('lo',-1.4,-1,'lo'),('hi',B2_W+1.4,1,'hi')])

# ---------------- what this building has to keep true ----------------
# These run at import, next to the geometry they measure. A check that lives
# beside its model is one that gets updated when the model moves.

def check_u5_stair_clear():
    """Same rule for Building 2: nothing under the flight, 6" of soffit over anything
       under the landing deck. Units 2 and 3 stack, so it is Unit 2's openings that
       matter — its door and one W-A are the only things on this face."""
    ff1 = levels.FF1
    items = [(B2_W-(PLAN_B2.x(w[0],0.5)+w[2]),B2_W-PLAN_B2.x(w[0],0.5),
              ff1+WIN_HEAD[w[4]],"W-"+w[4])
             for w in B2win if w[3]=='h' and abs(w[1]-0.5)<1e-6]
    items+= [(B2_W-(PLAN_B2.x(d[0],0.5)+d[2]),B2_W-PLAN_B2.x(d[0],0.5),
              ff1+6.0+8.0/12.0,"D-1")
             for d in B2doors if d[3]=='h' and abs(d[1]-0.5)<1e-6 and "ext" in d[5:]]
    print("UNIT 3 STAIR, LEVEL 1 OPENINGS ON THE COURTYARD FACE  (landing deck soffit +%s):"
          %fmt(U5_LAND_SOFFIT))
    bad=[]
    for a,b,head,mk in sorted(items):
        if b<=U5_STOOP_X0+1e-6 or a>=U5_LAND_X1-1e-6: where="clear of the stair"
        elif a>=U5_LAND_X0-1e-6:
            slack=U5_LAND_SOFFIT-head
            where="under the landing deck — %s over its %s head"%(fmt(slack),fmt(head))
            if slack<0.5-1e-9: bad.append((mk,"soffit less than 6\" over the head"))
        else:
            where="UNDER THE FLIGHT OR STOOP"; bad.append((mk,"stands under the flight"))
        print("   %-5s page x %-12s .. %-12s %s"%(mk,fmt(a),fmt(b),where))
    assert not bad, "Unit 3 stair fouls an opening: %s"%bad


# The one termination through the Sage wall, measured off the regridded plan against
# the openings in that wall. The dryer cap can land anywhere over the W/D, so it is
# taken at the edge of that bay nearer the opening — the worst case, which is what a
# drawing has to promise. 3'-0" is RCO M1502.3. The water heater used to be a second
# termination here and is not one any more: it is electric storage and vents nothing.
DR_TERM_CLR_MIN = 3.0

def _saff_openings():
    return sorted((PLAN_B2.y(w[1]),PLAN_B2.y(w[1])+w[2],"W-"+w[4])
                  for w in B2win if w[3]=='v' and abs(w[0]-(B2_W-0.5))<1e-6)

def _bay(kind):
    f = PLAN_B2.keep(next(f for f in F_B2 if f[4]==kind))
    return (f[1], f[1]+f[3])

def _gap(bay,openings):
    return min((a-bay[1]) if a>=bay[1] else ((bay[0]-b) if bay[0]>=b else -1.0)
               for a,b,_m in openings)

B2_DR_BAY = _bay('wd')

# ---------------- the deepened stack bay, in plan ----------------
# A-601 sections it; these are the same figures in plan, so A-102 can draw and dimension it
# and a check can hold everything else out of it.
STACK_BAY_RECT = (19.5-STACK_BAY_PROJ, STACK_BAY_Y0, STACK_BAY_PROJ, STACK_BAY_W)


def stack_bay_rect():
    """The deepened bay as the plans draw it: `keep()` so the regrid moves its corner and
       leaves its size, the way a chase or an appliance is mapped."""
    return PLAN_B2.keep(STACK_BAY_RECT)


def stack_bay_studs():
    """The two studs of the deepened bay, as page-feet (lo, hi) pairs. They are the only studs
       in the set whose POSITION is fixed — the stack decides them — so anything that has to
       pass through this wall passes between them or not at all."""
    _, y0, _, h = stack_bay_rect()
    return ((y0, y0+envelope.STUD_T), (y0+h-envelope.STUD_T, y0+h))


def bay_penetration_y(preferred, width, toward=-1.0):
    """Where something `width` across may pass through the north wall, wanting `preferred`.

       Returns `preferred` where it already clears both studs of the deepened bay, else the
       nearest point in the direction `toward` that does. The dryer duct exits this wall at the
       dryer's own centreline, and the bay put a 2x8 exactly there: 4" of duct over 1-1/2" of
       stud, with nothing in the set measuring a duct against a stud because every other stud
       on the job can be moved to suit."""
    for lo, hi in stack_bay_studs():
        if preferred+width/2.0 > lo-1e-9 and preferred-width/2.0 < hi+1e-9:
            edge = lo if toward < 0 else hi
            return edge-width/2.0-BAY_PEN_CLR if toward < 0 else edge+width/2.0+BAY_PEN_CLR
    return preferred


def stack_bay_violations(stack_cl=None, stack_fitting=0.0, penetrations=()):
    """Nothing may stand in the deepened bay, no opening of that wall may cross it, and the
       stack's widest FITTING must lie between its two studs.

       The bay is 1-3/4" of framing that exists only in a section until a plan draws it, and
       the washer in front of it was drawn tight to the wall for as long as the bay did not
       exist. That is the whole class of fault here: a detail deepens a wall and the plans go
       on showing it flat.

       `stack_cl` and `stack_fitting` are stack F's page centreline and hub diameter, which the
       caller reads from `src/drainage.py` — this module cannot import it without a cycle. The
       bay is laid out from the washer and the stack is placed from the plumbing model's copy
       of that washer, and the two mappings differ by a quarter inch (`Plan.rect()` shrinks a
       rectangle, `keep()` does not), so what is worth checking is not that they are concentric
       but that the fitting is inside the framing with the studs clear of it.

       `penetrations` are (name, along the wall, width) for anything passing THROUGH this
       wall — the caller reads them from `src/mechanical.py`. See `bay_penetration_y()`."""
    x0, y0, w, h = STACK_BAY_RECT
    v = []
    if stack_cl is not None:
        _, by, _, bh = stack_bay_rect()                 # page feet, as A-102 draws it
        lo, hi = by+envelope.STUD_T, by+bh-envelope.STUD_T
        if stack_cl-stack_fitting/2.0 < lo-1e-9 or stack_cl+stack_fitting/2.0 > hi+1e-9:
            v.append('BUILDING 2: stack F\'s %s fitting does not lie between the deepened '
                     'bay\'s studs' % fmt(stack_fitting))
    for nm, along, width in penetrations:
        for slo, shi in stack_bay_studs():
            if along+width/2.0 > slo-1e-9 and along-width/2.0 < shi+1e-9:
                v.append('BUILDING 2: %s passes through the north wall at %s, on a stud of the '
                         'deepened stack bay — that stud is placed by the stack and cannot move'
                         % (nm, fmt(along)))
    for f in F_B2:
        fx, fy, fw, fh = f[0], f[1], f[2], f[3]
        if fx < x0+w-1e-9 and fx+fw > x0+1e-9 and fy < y0+h-1e-9 and fy+fh > y0+1e-9:
            v.append('BUILDING 2: the %s stands in the deepened stack bay, which projects %s '
                     'into the room' % (str(f[4]).upper(), fmt(STACK_BAY_PROJ)))
    for a, b, mark in _saff_openings():
        if a < PLAN_B2.y(y0+h)+1e-9 and b > PLAN_B2.y(y0)-1e-9:
            v.append('BUILDING 2: %s is in the wall the deepened stack bay is framed in' % mark)
    return v
B2_DR_TERM_CLR = _gap(B2_DR_BAY,_saff_openings())

def check_b2_terms():
    print("BUILDING 2 NORTH WALL TERMINATIONS  (openings: %s):"
          %", ".join("%s %s..%s"%(m,fmt(a),fmt(b)) for a,b,m in _saff_openings()))
    for nm,bay,clr,need in (("dryer cap",B2_DR_BAY,B2_DR_TERM_CLR,DR_TERM_CLR_MIN),):
        print("   %-9s over y %s .. %s   %s to the nearest opening (%s required)"
              %(nm,fmt(bay[0]),fmt(bay[1]),fmt(clr),fmt(need)))
        assert clr>=need-1e-9, "Building 2 %s is %s from an opening, under %s"%(nm,fmt(clr),fmt(need))


# RCO 303.1 glazing, from the same window list the plan draws: each habitable room's
# windows against its net floor area. The open living / kitchen space counts the
# courtyard, Sage and adjacent-parcel units in the front band; each bedroom its
# two W-A. Percentages, so the note that quotes them reads against the 8 of the code.
def u45_glazing():
    polys = PLAN_B2.poly(OA_B2)
    areas = {"open": _area(polys[0][0]), "br1": _area(polys[1][0]), "br2": _area(polys[2][0])}
    def room(w):
        x,y = PLAN_B2.x(w[0],w[1]), PLAN_B2.y(w[1])
        if y < U45_BEARING_WALL[1]: return "open"
        return "br1" if x < PLAN_B2.x(X_BR+PARTITION/2.0,Y_REAR) else "br2"
    glass = {k:0.0 for k in areas}
    for w in B2win:
        r = room(w)
        if r in glass: glass[r] += WIN_SF[w[4]]
    return {k: 100.0*glass[k]/areas[k] for k in areas}

GL_U45 = u45_glazing()
GL_U45_MIN = min(GL_U45.values())

def b2_outside():
    """Every room, open area and fitting that reaches past the building's inside faces,
       in model feet — geom.beyond(), which says why this has to be checked."""
    return geom.beyond(B2U, OA_B2, F_B2, 0.5, B2_W-0.5, 0.5, Y_REAR)


def check_b2_inside():
    bad = b2_outside()
    print("BUILDING 2 ROOMS AND FITTINGS INSIDE THE WALLS: %s"
          % ("all %d" % (len(B2U)+len(OA_B2)+len(F_B2)) if not bad else bad))
    assert not bad, "Building 2: past the inside face of its walls: %s" % bad


def check_b2_glazing():
    print("UNITS 2 / 3 GLAZING, RCO 303.1: %s"
          %", ".join("%s %d%%"%(k,round(v)) for k,v in sorted(GL_U45.items())))
    assert GL_U45_MIN >= 8.0, "a Units 2/3 habitable space is under the 8 percent of RCO 303.1"
    assert GL_U45_MIN/2.0 >= 4.0, "openable area under the 4 percent of RCO 303.1"


# ---------------- the level, as the plan sheet takes it ----------------
# One level's plan, drawn twice. Units 2 and 3 are identical and stack exactly — that is
# the whole point of the building — except for Unit 3's kitchen window, so `level` is
# required: every caller says which unit's walls it is drawing.
def b2_level(level, tags=None):
    """Building 2, as A-102 draws it, with the closet depths, the bypass-leaf widths
       and the RCO 307.1 dimension at the pan, like Building 1's levels. `tags` is the
       caller's to set: Level 1 of A-102 tags the Units 2/3 bearing wall W3, Level 2's
       wall above it is a non-bearing partition and gets none, and the overlay path
       (E-102, S-102) draws no tags either way."""
    return PlanLevel(plan=PLAN_B2, W=B2_W, D=B2_D,
                     captions=CLEARANCE_CAPTIONS, wall_finish=GYP,
                     rooms=B2U, openareas=OA_B2, furn=F_B2,
                     doors=B2doors, wins=b2_wins(level), openings=B2op,
                     dims=B2dims, notes=B2notes, chains=CH_B2, joists=(),  # framing: S-102
                     tags=tags)

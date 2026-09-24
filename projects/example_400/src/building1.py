"""Building 1 — Unit 1, the single-family house, 20'-0" x 33'-0" at the front of the lot.

400 Oak Ave's front building: a two-story, 3 bedroom / 2 bath house, 25'-0" back from
the Oak Avenue lot line, laid out from the designer's mockup of 2026-09-17 ("Building A") at the
footprint he set earlier the same day. The mockup is 32'-0" deep; the foot it does not
have is the kitchen's (the designer's call), so the kitchen / dining band is 11'-0".

THE PLAN, as the sheet reads it — Oak Avenue at the top, the adjacent house on the left:

  * The stair runs along the left wall from a 3'-0" landing at the entry, rising toward
    the rear, 15 risers at 8" (src/stairs.py, B1_STAIR). A full-height wall beside the
    flight carries Bedroom 2's wall above; a short wall at the top riser closes the
    space under the stair off from the kitchen, so it cannot be entered (RCO 302.7).
  * Level 1: the living room beside the stair, open to the kitchen / dining behind it;
    a rear band of Bath 1, a hall, the mechanical / laundry room and a walk-in pantry.
  * Level 2: the stair well against the left wall; Bedroom 2 with its walk-in and Bath 2
    across the front; a cross-hall at the top riser, which is the stair's top landing;
    Bedrooms 3 and 1 side by side at the rear, each with a reach-in off the hall wall
    and its egress W-A in the rear wall.

Model coordinates are PRE-mirror, as Building 2's: x runs from the right-hand
neighbour's side (x 0) to the left-hand one's (x B1_W), y from the street face (y 0) to
the rear (y B1_D). The sheet mirror puts x = B1_W on the left, so the stair column is at
high x. The two levels differ, so each has its own regrid; the stair column and the top
riser are PINNED so both levels put them on the same line.

What is NOT here: the stair drawing (A-101) and the framing, the working spaces, the
bath fans and the plumbing, none of which is modelled for this building yet.
"""
from arkitect.codes.clearances import WC_SIDE
from arkitect.codes.ohio.legends import CLEARANCE_CAPTIONS
from arkitect.lib.model import geom
from arkitect.lib.model.dimensions import strings, wall_faces
from arkitect.lib.model.records import PlanLevel
from arkitect.lib.model.regrid import EXT_STUD, PARTITION, PART_STUD, Zone, Plan
from arkitect.lib.units import IN, fmt, inches
from src import levels
# the finish on a stud face, for the clear figures: A-601 W2's board, defined once where
# A-602's schedule prints it
from src.finishes import BOARD as GYP
from src.openings import WIN_GEOM, WIN_SF, WIN_W
from src.stairs import B1_STAIR

B1_W, B1_D = 20.0, 33.0
LEVELS = (1, 2)                   # two stories

# ---------------- the stair, in SHEET feet ----------------
# The flight rises TOWARD THE FRONT WALL (the designer, 2026-09-18, reversed from rising to the
# rear): its top riser is a 3'-0" landing off the front wall on Level 2, its foot lands in
# the kitchen on Level 1. Placed from the front wall's stud face, not regridded: the top
# landing is 3'-0" of finished floor, and fourteen 9-1/4" treads are 10'-9-1/2".
Y_TOP_RISER  = EXT_STUD + GYP + B1_STAIR.top_landing     # the top riser: Level 2's landing edge
Y_FOOT_RISER = Y_TOP_RISER + B1_STAIR.run                # the bottom riser, in the kitchen
# The column's stair-wall face, regridded but before the mirror (the left wall is at
# B1_W - EXT_STUD there); A-101 draws the column from EXT_STUD on the page.
STAIR_X0 = B1_W - EXT_STUD - B1_STAIR.stud_width

# ---------------- the model's lines ----------------
X_SW  = 15.6                     # the stair wall, its living-room face (model x)
X_ST  = X_SW + PARTITION         # the stair wall's stair face: the column is X_ST .. 19.5
# Bath 1 is as deep as its shower and its vanity, end to end along the left wall, and a
# half inch: 60" + 24" + 1/2" (the designer, 2026-09-18: the vanity's 24" face toward the door).
# The kitchen gives up what that takes -- an inch, so 10'-11" where the designer asked 11'-0".
BATH1_SHOWER = 5.0
BATH1_SHOWER_W = 2.5             # and 30" across, its alcove the right wall
FRIDGE_W, COUNTER_D = 3.0, 2.0
BATH1_VANITY = (2.0, IN(22))     # Bath 1's vanity: 24" along the left wall, 22" deep (the designer)
BATH1_D = BATH1_SHOWER+BATH1_VANITY[0]+IN(0.5)
# pinned in sheet feet: the rear wall's stud face, less Bath 1, less the partition
Y_KIT = round(B1_D-EXT_STUD-BATH1_D-PART_STUD, 4)   # the kitchen's rear partition, its kitchen face
Y_RB  = round(Y_KIT + PARTITION, 4)       # the rear band's front face
Y_REAR = B1_D - 0.5              # the rear wall's inside face

# Both levels pin the stair wall and the two risers, so the column and the well stack.
_XPINS = {X_ST: STAIR_X0}

# ================ LEVEL 1 ================
# The rear band, left to right on the sheet (high model x to low): Bath 1, the hall,
# the mechanical / laundry room and the pantry.
X_BATH1 = 14.4                   # Bath 1 is X_BATH1 .. 19.5
# ...and its hall wall is PINNED on the page, because what stands between that wall and
# the shower is a CODE figure and not whatever slack the rear band has left over. RCO
# 307.1 measures 15" each side of the pan's centerline to a FINISHED surface; the room
# rectangle is this wall's STUD face, the convention every other string on the plan is
# drawn in, so the bay is that minimum twice, plus this wall's own board, plus 1/2" so
# the dimension is not drawn on the minimum. Unpinned the room stretched to 30-1/2" stud
# to shower, which is 30" finished: the pan centered in it kept 15" to each side with
# nothing to spare, and centered in the STUD band -- as it was until 2026-09-20 -- it
# read 15-1/4" each side and stood 14-3/4" off the drywall.
# X_ST's pin already fixes page x at the right wall, so the shower's face is fixed too
# and the bay runs from this pin to it. LEVEL 1 ONLY: _XPINS is shared with Level 2,
# which has no wall here.
BATH1_BAY = GYP + 2*WC_SIDE.minimum + IN(0.5)
BATH1_WALL_X = B1_W - EXT_STUD - BATH1_SHOWER_W - BATH1_BAY
X_HALL1 = X_BATH1 - PARTITION    # the hall is X_HALL0 .. X_HALL1
X_HALL0 = X_HALL1 - 3.5
X_MECH1 = X_HALL0 - PARTITION    # mech / laundry is X_MECH0 .. X_MECH1
X_MECH0 = X_MECH1 - 5.0
X_PANT1 = X_MECH0 - PARTITION    # the pantry is 0.5 .. X_PANT1

# The coat closet at the entry, under the stair's high end: 5'-0" of it has the full
# headroom a closet wants (A-101 note: RCO 302.7, 1/2" gypsum on its walls and soffit,
# as enclosed accessible space under a stair). The rest of the column is the flight,
# open at its foot to the kitchen.
Y_CL = 5.5                       # the coat closet is 0.5 .. Y_CL

# ---------------- Unit 1's ducted heat pump ----------------
# The designer, 2026-09-19: one two-zone system, an air handler per level concealed in that level's
# hall soffit, in place of four wall heads. Both air handlers and every duct stay INSIDE
# the thermal envelope -- nothing in the attic -- which is what keeps RCO 1103.3's duct
# test off this set (A-602). M-101 places the units, the registers and the runs.
U1_SOFFIT_ROOMS = {1: ('HALL',), 2: ('HALL',)}
U1_SOFFIT_DROP  = IN(12)          # the 8" cabinet, its supply plenum and 2x framing
U1_AHU = {1: (12.25, 30.0), 2: (5.0, 17.375)}     # model feet, each in its hall's soffit, U1_SOFFIT

L1_ROOMS=[(X_BATH1,Y_RB,19.5-X_BATH1,Y_REAR-Y_RB,"BATH 1",(-0.8,-0.3)),
          (X_HALL0,Y_RB,X_HALL1-X_HALL0,Y_REAR-Y_RB,"HALL"),
          (X_MECH0,Y_RB,X_MECH1-X_MECH0,Y_REAR-Y_RB,"MECH / LAUNDRY",(0.0,-2.75),"compact"),
          (0.5,Y_RB,X_PANT1-0.5,Y_REAR-Y_RB,"PANTRY"),
          (X_ST,0.5,19.5-X_ST,Y_CL-0.5,"CL."),
          # the flight below the closet, white so the poche does not fill it; A-101
          # draws the treads
          (X_ST,Y_CL+PARTITION,19.5-X_ST,Y_FOOT_RISER-Y_CL-PARTITION,"")]

# The living room and the kitchen / dining are one space. The stair wall runs the column
# from the front wall to the foot, where the flight opens onto the kitchen; its 3'-0" foot
# landing is kitchen floor against the left wall.
OPEN_L1=[(0.5,0.5),(X_SW,0.5),(X_SW,Y_FOOT_RISER),(19.5,Y_FOOT_RISER),(19.5,Y_KIT),(0.5,Y_KIT)]

def _open_labels(living=("",""), kitchen=("","")):
    return [(8.0,7.2,"LIVING")+living, (8.0,16.4,"KITCHEN / DINING")+kitchen]

OA_L1=[(OPEN_L1,_open_labels())]

PLAN_B1_L1 = Plan([Zone(L1_ROOMS,OA_L1,0.5,Y_REAR,B1_W,EXT_STUD,B1_D-EXT_STUD,
                        xpins={**_XPINS, X_BATH1: BATH1_WALL_X},
                        ypins={Y_FOOT_RISER:Y_FOOT_RISER,Y_KIT:Y_KIT})],
                  B1_W,B1_D)

# The living / kitchen split is the foot of the stair. Both halves are measured on the regridded
# polygon and written back into the labels, with the living room's clear size.
_open_r = PLAN_B1_L1.poly([OA_L1[0]])[0][0]
LIVING_SF, KITCHEN_SF = geom.split(_open_r, Y_FOOT_RISER, 'y')
assert abs(LIVING_SF+KITCHEN_SF-geom.area(_open_r)) < 1e-6
LIVING_W = PLAN_B1_L1.x(X_SW,7.0)-PLAN_B1_L1.x(0.5,7.0)
LIVING_D = Y_FOOT_RISER-PLAN_B1_L1.y(0.5)
KITCHEN_W = PLAN_B1_L1.x(19.5,20.0)-PLAN_B1_L1.x(0.5,20.0)
KITCHEN_D = PLAN_B1_L1.y(Y_KIT)-Y_FOOT_RISER
OA_L1[0]=(OPEN_L1,_open_labels(
    ("%s x %s"%(fmt(LIVING_W),fmt(LIVING_D)),"%d SF"%round(LIVING_SF)),
    ("%s x %s"%(fmt(KITCHEN_W),fmt(KITCHEN_D)),"%d SF"%round(KITCHEN_SF))))

# Fittings, (x,y,w,h,kind,face) in model feet. A water closet's 'n' / 's' names the side
# its TANK is on (low y / high y); arkitect/lib/symbols/plumbing.py. The kitchen is a run on the right wall —
# the sink under its W-B, the dishwasher, the range — into the rear corner, the pantry
# door beside it. The fridge stands centred on the mechanical / laundry room's
# wall, to close the work triangle with the sink and the range (the designer,
# 2026-09-18: on the left wall behind the stair it was too far from both, and the counter
# run there went with it). Bath 1's shower is on the left wall. The mechanical / laundry room: the
# stacked W/D in the rear corner away from the door, its dryer out the rear wall; the
# 50-gallon tank in the other rear corner; the panel on the pantry-side wall.

# The pantry door, off the kitchen: in L1_DOORS, and the counter beside the fridge runs
# to its jamb. It stands between the right-wall run, which turns the corner into the
# pantry's partition (the designer, 2026-09-21), and the mech / laundry wall, centred in what the
# two leave, and is hung on the mech jamb so it folds back against that wall. A 2'-8"
# leaf does not fit there: the pantry is 4'-4-1/8" clear and the counter takes 2'-0".
D_PANTRY_W = 2.0
D_PANTRY = (PLAN_B1_L1.inv_x((PLAN_B1_L1.x(0.5, Y_KIT)+COUNTER_D+PLAN_B1_L1.x(X_PANT1, Y_KIT)
                              -D_PANTRY_W)/2.0, Y_KIT),
            Y_KIT+PARTITION/2.0, D_PANTRY_W, 'h', -1, "far")


def _fridge_x0():
    """The fridge's left edge on the regridded plan: centred on the mech / laundry wall."""
    return (PLAN_B1_L1.x(X_MECH0, Y_KIT)+PLAN_B1_L1.x(X_MECH1, Y_KIT)-FRIDGE_W)/2.0


def _fridge_counters():
    """The two runs of counter beside the fridge on the mech / laundry wall, on the
       regridded plan: from the fridge to the pantry door's jamb, and from the fridge to
       the hall's cased opening. Mapped back to model feet, since a fitting keeps its size."""
    P, y = PLAN_B1_L1, Y_KIT
    f0 = _fridge_x0()
    pantry = P.x(D_PANTRY[0], y)+D_PANTRY[2]     # the pantry door's far jamb
    hall = P.x(X_HALL0, y)                       # where the hall's opening starts
    y0 = P.inv_y(P.y(y)-COUNTER_D)
    return [(P.inv_x(pantry, y), y0, f0-pantry, COUNTER_D, 'counter'),
            (P.inv_x(f0+FRIDGE_W, y), y0, hall-(f0+FRIDGE_W), COUNTER_D, 'counter')]


# The right-wall run starts at the front of the kitchen, at the foot of the stair (the designer,
# 2026-09-18), and runs past the range to the pantry partition (the designer, 2026-09-21).
RUN0 = Y_FOOT_RISER
# Stack A's furred chase, P-101 / P-601: against the south wall at the FRONT end of the kitchen
# run, ahead of the first base cabinet, on the solid wall between the two side windows.
CHASE = IN(8)
STACK_A_CHASE = (0.5,RUN0-CHASE,CHASE,CHASE,'chase')
F_L1=[STACK_A_CHASE,(0.5,RUN0,2.0,Y_KIT-RUN0,'counter'),(0.5,RUN0+1.3,2.0,2.5,'sink'),(0.5,RUN0+3.8,2.0,2.0,'dw'),
      (0.5,RUN0+5.8,2.0,2.5,'range'),
      # the fridge centred on the mech / laundry room's wall (the designer, 2026-09-18), flush to it,
      # both as the regridded plan draws them
      (PLAN_B1_L1.inv_x(_fridge_x0(),Y_KIT),
       PLAN_B1_L1.inv_y(PLAN_B1_L1.y(Y_KIT)-2.5),FRIDGE_W,2.5,'fridge','s'),
      # counters either side of the fridge, 24" deep, each out to the opening beside it:
      # the pantry door's jamb on one side, the hall's cased opening on the other
      *_fridge_counters(),
      # Bath 1
      # Bath 1's walk-in shower, 60" x 30", in the tub's alcove: one tub in the house,
      # upstairs in the bedrooms' bath (the designer, 2026-09-18, for resale)
      # flush to the rear wall as the regridded plan draws it (a fitting keeps its size
      # and only its origin is mapped)
      (PLAN_B1_L1.inv_x(PLAN_B1_L1.x(19.5,Y_REAR)-BATH1_SHOWER_W,Y_REAR),
       PLAN_B1_L1.inv_y(PLAN_B1_L1.y(Y_REAR)-BATH1_SHOWER),BATH1_SHOWER_W,BATH1_SHOWER,'shower'),
      # the pan, tank on the rear wall, centred in the band RCO 307.1 MEASURES, on the
      # REGRIDDED plan (the regrid moves a fitting's origin, not its size): from the hall
      # wall's FINISHED face to the shower. The room rectangle is the wall's STUD face --
      # that is the convention every other string on the plan is drawn in -- and 307.1
      # measures to the wall, so the pan's band starts a board's thickness in. The shower
      # needs no such deduction: it stands in the room with its finished face where it is
      # drawn. Centred in the stud band instead, the pan read 15-1/4" to each side and
      # stood 14-3/4" off the hall wall's drywall, under the 15" A-001 note 7 quotes.
      # The band is 30" finished, so each side is 15" exactly: check_clearances() holds it
      # and there is no slack to give away. Widening Bath 1 takes it from the pantry.
      (PLAN_B1_L1.inv_x((PLAN_B1_L1.x(X_BATH1,Y_REAR)+GYP
                        +PLAN_B1_L1.x(19.5,Y_REAR)-BATH1_SHOWER_W-1.67)/2.0,Y_REAR),
       PLAN_B1_L1.inv_y(PLAN_B1_L1.y(Y_REAR)-2.33),1.67,2.33,'wc','s'),
      # Bath 1's vanity against the left wall in the corner by the front wall, its 24"
      # face toward the door (the designer, 2026-09-18), 22" deep, between the front wall and the
      # shower's end; placed on the regridded wall. check_b1_vanity() holds it.
      (PLAN_B1_L1.inv_x(PLAN_B1_L1.x(19.5,Y_RB)-BATH1_VANITY[1],Y_RB),Y_RB,
       BATH1_VANITY[1],BATH1_VANITY[0],'lav','w'),
      # mechanical / laundry
      (X_MECH0,Y_REAR-2.83,2.25,2.83,'wd'),
      (X_MECH1-1.67,Y_REAR-1.67,1.67,1.67,'wh'),
      (X_MECH1-2.5,Y_REAR-1.67-2.5,2.5,2.5,'whclear'),
      (X_MECH0,Y_RB+1.0,0.25,1.2,'panel','e'),
      (X_MECH0,Y_RB+0.8,3.0,2.5,'clear','n')]

# Doors: the entry just right of the stair column, swinging in; the coat closet in the
# stair wall beside it, hung to swing clear of the entry door; Bath 1 and the mech room
# off the hall; the pantry off the kitchen. The hall opens to the kitchen.
D_ENTRY = (X_SW-3.4,0.5,3.0,'h',-1,"ext")
# The back door, at the end of the hall (the designer, 2026-09-18): 2'-8", centered in a hall too
# narrow to frame 3'-0" with its studs. The entry is the required egress door, RCO 311.2.
D_REAR_W = 2.67
D_REAR = (round((X_HALL0+X_HALL1)/2.0-D_REAR_W/2.0, 4), Y_REAR, D_REAR_W, 'h', 1, "ext")
L1_DOORS=[D_ENTRY, D_REAR,
          (X_SW+PARTITION/2.0,Y_CL-0.1-2.5,2.5,'v',-1,"far"),
          (X_HALL1+PARTITION/2.0,Y_RB+0.3,2.67,'v',1),
          (X_HALL0-PARTITION/2.0,Y_RB+0.3,2.67,'v',-1),
          D_PANTRY]
L1_OPS=[(X_HALL0,Y_KIT+PARTITION/2.0,X_HALL1-X_HALL0,'h')]

# In FINAL SHEET feet (mirrored, as A-101 and S-101 draw them), for the site and the
# foundation: the entry door's left jamb, and the stair wall S-101 puts a bearing strip
# under. The Level 2 floor is assumed to span side wall to side wall (19'-1" clear), so
# the stair wall -- which carries the trimmer at the well -- is the house's one interior
# bearing line. The floor framing is not modelled yet; S-101 note 4 says what it assumes.
ENTRY_X = B1_W-(PLAN_B1_L1.x(D_ENTRY[0],D_ENTRY[1])+D_ENTRY[2])
REAR_DOOR_X = B1_W-(PLAN_B1_L1.x(D_REAR[0],D_REAR[1])+D_REAR[2])      # the back door's left jamb
STAIR_WALL = (B1_W-STAIR_X0, EXT_STUD, B1_W-(STAIR_X0-PART_STUD), Y_FOOT_RISER)   # x0 y0 x1 y1

# Windows (x,y,len,o,mark), on the inside face of their wall: the living room's W-C in
# the front wall and W-B in the right wall; the W-B over the kitchen sink.
_sink = next(f for f in F_L1 if f[4]=='sink')
L1_WINS=[(3.6,0.5,5.0,'h',"C"),                 # re-placed on the Oak face's left bay, below
         (0.5,5.9,3.0,'v',"B"),
         (0.5,_sink[1]+_sink[3]/2.0-1.5,3.0,'v',"B")]

# ================ LEVEL 2 ================
# The stair arrives at a 3'-0" landing against the front wall. From it a corridor runs
# back beside the well, behind a guard wall, to a cross-hall at the well's far end that
# serves the two rear bedrooms. Right of the corridor: Bedroom 2 at the front, with a
# reach-in by its door, and Bath 2 behind it. Bedrooms 3 and 1 at the rear, as before.
X_COR1  = X_SW                   # the corridor's guard-wall face (the guard stands on the stair wall)
X_COR0  = round(X_COR1-3.2, 4)   # its other face: a 3'-2" corridor, 36" clear finished
X_FR1   = round(X_COR0-PARTITION, 4)  # Bedroom 2 and Bath 2 are 0.5 .. X_FR1
Y_WELL  = round(Y_FOOT_RISER, 4)      # the well's far end, where its guard wall stands
# The cross-hall stands 1'-6" past the well, so the rear bedrooms give Bedroom 2 1'-6" of
# depth (the designer, 2026-09-18, a foot and then a half foot more); the hall floor between the
# well and it is floor.
Y_HALL0 = round(Y_WELL+1.5, 4)        # the cross-hall's front face
Y_FR1   = round(Y_HALL0-PARTITION, 4) # Bath 2's rear face
BATH2_D = 5.0                    # Bath 2, stud to stud: the 5'-0" an alcove tub needs
Y_BR2   = round(Y_FR1-PARTITION-BATH2_D, 4)   # Bedroom 2 is 0.5 .. Y_BR2; Bath 2 behind it
Y_HALL  = round(Y_HALL0+IN(38), 4)    # the cross-hall's rear face, 3'-2"
Y_BRR   = round(Y_HALL+PARTITION, 4)  # the rear bedrooms' front face
X_MID   = 9.8                    # the partition between the rear bedrooms, its Bedroom 1 face
CL_W, CL_D = 4.0, 2.0            # the reach-ins: the rear two on the hall wall beside X_MID
# The rear bedrooms are the same width: X_MID is pinned so the partition is centred.
_MID = B1_W/2.0-PART_STUD/2.0
# Bedroom 2's reach-in, in its back corner by the door
BR2_CL = (X_FR1-CL_W, Y_BR2-CL_D, CL_W, CL_D)

L2_ROOMS=[(0.5,Y_BR2+PARTITION,X_FR1-0.5,Y_FR1-Y_BR2-PARTITION,"BATH 2"),
          BR2_CL+("CL.",),
          (X_MID-CL_W,Y_BRR,CL_W,CL_D,"CL."),
          (X_MID+PARTITION,Y_BRR,CL_W,CL_D,"CL."),
          # the well over the flight, white; its far end is a guard wall over the foot
          (X_ST,Y_TOP_RISER,19.5-X_ST,Y_WELL-PARTITION-Y_TOP_RISER,"")]

# The landing, the corridor and the cross-hall are one space.
HALL_L2=[(X_COR0,0.5),(19.5,0.5),(19.5,Y_TOP_RISER),(X_COR1,Y_TOP_RISER),(X_COR1,Y_WELL),
         (19.5,Y_WELL),(19.5,Y_HALL),(0.5,Y_HALL),(0.5,Y_HALL0),(X_COR0,Y_HALL0)]
BR2_L2=[(0.5,0.5),(X_FR1,0.5),(X_FR1,BR2_CL[1]),(BR2_CL[0],BR2_CL[1]),(BR2_CL[0],Y_BR2),
        (0.5,Y_BR2)]
BR1_L2=[(0.5,Y_BRR),(X_MID-CL_W,Y_BRR),(X_MID-CL_W,Y_BRR+CL_D),(X_MID,Y_BRR+CL_D),
        (X_MID,Y_REAR),(0.5,Y_REAR)]
BR3_L2=[(X_MID+PARTITION,Y_BRR+CL_D),(X_MID+PARTITION+CL_W,Y_BRR+CL_D),
        (X_MID+PARTITION+CL_W,Y_BRR),(19.5,Y_BRR),(19.5,Y_REAR),(X_MID+PARTITION,Y_REAR)]

OA_L2=[(HALL_L2,[(8.0,Y_HALL0+1.55,"HALL","","")]),
       (BR2_L2,[(9.4,5.5,"BEDROOM 2",None,"AUTO SF")]),
       (BR1_L2,[(5.15,23.2,"BEDROOM 1",None,"AUTO SF")]),
       (BR3_L2,[(14.85,23.2,"BEDROOM 3",None,"AUTO SF")])]

PLAN_B1_L2 = Plan([Zone(L2_ROOMS,OA_L2,0.5,Y_REAR,B1_W,EXT_STUD,B1_D-EXT_STUD,
                        xpins={**_XPINS, X_MID:_MID},
                        ypins={Y_TOP_RISER:Y_TOP_RISER,Y_FOOT_RISER:Y_FOOT_RISER},
                        xhold={(X_MID-CL_W,X_MID,CL_W),(X_MID+PARTITION,X_MID+PARTITION+CL_W,CL_W)},
                        yhold={(Y_BRR,Y_BRR+CL_D,CL_D)})],
                  B1_W,B1_D)

# The regrid can squeeze a room by an eighth; Bath 2 may not print under its tub.
assert PLAN_B1_L2.y(Y_FR1)-PLAN_B1_L2.y(Y_BR2+PARTITION) >= BATH2_D-1e-6, \
    "Bath 2 is under 5'-0\" stud to stud; the alcove tub does not fit"

# Bath 2's HALL wall, as the regridded plan puts it (a fitting keeps its size and only its
# origin is mapped, so everything here is laid out on the drawn wall and mapped back): the
# tub across the right-wall end, a 72" double vanity against the corridor wall, and the
# pan centred in what is left between them (the designer, 2026-09-18). The wet wall is the hall's,
# not Bedroom 2's (the designer, 2026-09-21): the flush and the drains stay off the bedroom, the tub
# valve is reached from the hall, and the branch runs on stack A's line.
VANITY_W, VANITY_D = 6.0, 1.75
_b2y = Y_BR2+PARTITION                                      # the bath's Bedroom 2 face
def _on_hall(d):
    """The model y of a fitting d deep standing against Bath 2's hall wall."""
    return PLAN_B1_L2.inv_y(PLAN_B1_L2.y(Y_FR1)-d)
_tub_edge = PLAN_B1_L2.x(0.5,_b2y)+2.5
_van0 = PLAN_B1_L2.x(X_FR1,_b2y)-VANITY_W
_wc_cl = (_tub_edge+_van0)/2.0
_WC_D = 2.33

F_L2=[(0.5,_b2y,2.5,Y_FR1-_b2y,'tub','s','s'),
      (PLAN_B1_L2.inv_x(_wc_cl-1.67/2.0,_b2y),_on_hall(_WC_D),1.67,_WC_D,'wc','s'),     # tank on the wall
      (PLAN_B1_L2.inv_x(_van0,_b2y),_on_hall(VANITY_D),VANITY_W/2.0,VANITY_D,'lav','n'),
      (PLAN_B1_L2.inv_x(_van0+VANITY_W/2.0,_b2y),_on_hall(VANITY_D),VANITY_W/2.0,VANITY_D,'lav','n'),
      # beds: Bedroom 2's head on the right wall, the rear bedrooms' on the partition
      # between them, each clear of its door and its egress window
      (0.5,1.4,6.6667,5.0,'bed','w'),
      (X_MID-6.6667,24.5,6.6667,5.0,'bed','e'),
      (X_MID+PARTITION,24.5,6.6667,5.0,'bed','w')]

L2_DOORS=[(X_COR0-PARTITION/2.0,1.2,2.67,'v',-1),                     # Bedroom 2
          (X_COR0-PARTITION/2.0,_b2y+0.3,2.67,'v',-1),                # Bath 2, at its Bedroom 2 end
          (1.6,Y_HALL+PARTITION/2.0,2.67,'h',-1),                    # Bedroom 1
          (15.6,Y_HALL+PARTITION/2.0,2.67,'h',-1)]                   # Bedroom 3
L2_OPS=[(BR2_CL[0],BR2_CL[1],CL_W,'h'),
        (X_MID-CL_W,Y_BRR+CL_D,CL_W,'h'),(X_MID+PARTITION,Y_BRR+CL_D,CL_W,'h')]

def _centred(x0,x1,mark,w=3.0):
    return (x0+x1)/2.0-w/2.0

# THE OAK FACE STACKS IN TWO BAYS, mirrored about its centerline (the designer, 2026-09-18, option 1
# of three). The right bay is as near the entry's center as the plan lets a window stand
# over it: the landing window starts 1/2" clear of the corridor partition, which leaves the
# door 3" off the bay, under a surround wider than the casing above it. The left bay is its
# mirror, and Bedroom 2's W-A and the living room's W-C are centered on it. All through
# the regrid, none typed: move the corridor and all three windows follow.
_land_front = (X_COR0+IN(0.5),0.5,3.0,'h',"A")           # the stair landing; safety glazing, A-101
BAY_R = PLAN_B1_L2.x(_land_front[0],0.5)+_land_front[2]/2.0        # sheet feet from 404 Oak
BAY_L = B1_W-BAY_R
_br2_front = (PLAN_B1_L2.inv_x(BAY_L-1.5,0.5),0.5,3.0,'h',"A")     # Bedroom 2
assert 0.5 <= _br2_front[0] and _br2_front[0]+3.0 <= BR2_CL[0], "Bedroom 2's front window leaves its free wall"
assert _land_front[0]+3.0 <= 19.5, "the landing window leaves the landing's front wall"
_entry_c = PLAN_B1_L1.x(D_ENTRY[0],0.5)+D_ENTRY[2]/2.0
assert abs(_entry_c-BAY_R) <= IN(4), "the entry is %.1f in off its bay" % (12*abs(_entry_c-BAY_R))
L1_WINS[0] = (PLAN_B1_L1.inv_x(BAY_L-L1_WINS[0][2]/2.0,0.5),)+L1_WINS[0][1:]     # the living room's W-C
assert L1_WINS[0][0]+L1_WINS[0][2] <= D_ENTRY[0]-1.0, "the living room's W-C reaches the entry"
L2_WINS=[_br2_front, _land_front,
         (_centred(0.5,X_MID,"A"),Y_REAR,3.0,'h',"A"),               # Bedroom 1, rear
         (_centred(X_MID+PARTITION,19.5,"A"),Y_REAR,3.0,'h',"A")]    # Bedroom 3, rear
# THE SOUTH FACE, Level 2 mirrored about its middle (the designer, 2026-09-18: "missing symmetry",
# then "pantry doesn't need a window. function over form"). Level 1 keeps the two windows
# its rooms want: the living room's where it was, and the sink's. Level 2 has a W-B over
# the living room's, in Bedroom 2, and its mirror in Bedroom 1; Bedroom 3's, in the north
# wall, mirrors Bedroom 1's. No window is placed for the elevation alone. All through the
# regrid, none typed but the living room's.
_wb = WIN_W["B"]
_living_side = next(w for w in L1_WINS if w[3] == 'v' and w[1] < RUN0)
SIDE_BAY_FRONT = PLAN_B1_L1.y(_living_side[1])+_wb/2.0          # sheet feet from the Oak face
SIDE_BAY_REAR = B1_D-SIDE_BAY_FRONT
_y_front, _y_rear = (PLAN_B1_L2.inv_y(c-_wb/2.0) for c in (SIDE_BAY_FRONT, SIDE_BAY_REAR))
assert 0.5 <= _y_front and _y_front+_wb <= Y_BR2, "Bedroom 2's side window leaves the bedroom"
assert Y_BRR <= _y_rear and _y_rear+_wb <= Y_REAR, "the rear bedrooms' side windows leave the bedrooms"
L2_WINS += [(0.5,_y_front,_wb,'v',"B"),                                # Bedroom 2, south
            (0.5,_y_rear,_wb,'v',"B"),                                 # Bedroom 1, south
            (B1_W-0.5,_y_rear,_wb,'v',"B"),                            # Bedroom 3, north
            # Over the stair (the designer, 2026-09-18): daylight down the well, a FIXED unit. Opposite Bedroom 2's,
            # so the north face's Level 2 mirrors as the south's does. Its 4'-0" sill above the
            # Level 2 floor is more than 36" over every tread, so RCO 308.4.6 does not reach it.
            (B1_W-0.5,_y_front,WIN_W["D"],'v',"D")]            # W-D: fixed, out of reach over the well
assert Y_TOP_RISER <= _y_front and _y_front+_wb <= Y_WELL-PARTITION, "the stair window leaves the well"

# ---------------- dimension strings ----------------
def _chains(rooms,oa):
    hf = wall_faces(rooms,oa,0,(0.5,Y_REAR),(0.5,B1_W-0.5))
    out = strings(hf,(0.5,B1_W-0.5),(0.5,Y_REAR),'h',[('hi',Y_REAR+1.35,-1,'hi')])
    vf = wall_faces(rooms,oa,1,(0.5,B1_W-0.5),(0.5,Y_REAR))
    out += strings(vf,(0.5,Y_REAR),(0.5,B1_W-0.5),'v',
                   [('lo',-1.4,-1,'lo'),('hi',B1_W+1.4,1,'hi')])
    return out

B1dims = [(0, B1_W, 'h', -3.4, None), (0, B1_D, 'v', -3.4, None)]

LEVEL = {1: dict(plan=PLAN_B1_L1, rooms=L1_ROOMS, openareas=OA_L1, furn=F_L1,
                 doors=L1_DOORS, wins=L1_WINS, openings=L1_OPS),
         2: dict(plan=PLAN_B1_L2, rooms=L2_ROOMS, openareas=OA_L2, furn=F_L2,
                 doors=L2_DOORS, wins=L2_WINS, openings=L2_OPS)}
for _lv in LEVEL.values():
    _lv['chains'] = _chains(_lv['rooms'],_lv['openareas'])

# Each level's hall soffit, as rectangles (x0, y0, x1, y1) in model feet: the ceiling
# dropped U1_SOFFIT_DROP under the air handler and the runs that leave it. Level 1's is the
# whole hall; its runs leave it up into the floor trusses. Level 2 has the attic over it,
# where no duct may go (A-602), so its soffit carries every run to its room's hall wall: the
# cross-hall, where the air handler hangs, and the corridor from the cross-hall to Bedroom
# 2's wall, stopping Y_COR_SOFFIT from the front face -- 6" past the truss at 6'-0" that
# frames the attic hatch's bay, so the hatch keeps the full ceiling.
Y_COR_SOFFIT = 6.5
U1_SOFFIT = {1: ((X_HALL0, Y_RB, X_HALL1, Y_REAR),),
             2: ((0.5, Y_HALL0, 19.5, Y_HALL), (X_COR0, Y_COR_SOFFIT, X_COR1, Y_HALL0))}


def soffit_pages(level):
    """A level's hall soffit in page feet, one (x0, y0, x1, y1) per rectangle: its corners
       are wall faces, so they go through the plan's regrid as the walls do, then the sheet
       mirror."""
    P = LEVEL[level]['plan']
    out = []
    for x0, y0, x1, y1 in U1_SOFFIT[level]:
        xa, xb = B1_W-P.x(x0, y0), B1_W-P.x(x1, y1)
        out.append((min(xa, xb), P.y(y0), max(xa, xb), P.y(y1)))
    return out


def soffit_outline(level):
    """The outline of a level's soffit in page feet, one closed rectilinear polygon (or
       more) traced round the union of its rectangles: two rectangles that meet read as
       one soffit, with no line where they join."""
    rects = soffit_pages(level)
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    ys = sorted({v for r in rects for v in (r[1], r[3])})
    def filled(i, j):
        if not (0 <= i < len(xs)-1 and 0 <= j < len(ys)-1): return False
        cx, cy = (xs[i]+xs[i+1])/2.0, (ys[j]+ys[j+1])/2.0
        return any(r[0] < cx < r[2] and r[1] < cy < r[3] for r in rects)
    edges = {}                                  # grid edge start -> end, the region on its left
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            if not filled(i, j): continue
            for (a, b), out in ((((i, j), (i+1, j)), filled(i, j-1)), (((i+1, j), (i+1, j+1)), filled(i+1, j)),
                                (((i+1, j+1), (i, j+1)), filled(i, j+1)), (((i, j+1), (i, j)), filled(i-1, j))):
                if not out: edges[a] = b
    loops = []
    while edges:
        start = next(iter(edges)); loop = [start]; k = edges.pop(start)
        while k != start:
            loop.append(k); k = edges.pop(k)
        pts = [(xs[i], ys[j]) for i, j in loop]
        n = len(pts)                            # keep the corners only
        loops.append([pts[k] for k in range(n)
                      if (pts[k-1][0] == pts[k][0]) != (pts[k][0] == pts[(k+1) % n][0])])
    return loops


def b1_level(level):
    """One level of the house as a plan sheet takes it. A-101 adds the stair."""
    assert level in LEVELS, level
    m = LEVEL[level]
    return PlanLevel(plan=m['plan'], W=B1_W, D=B1_D, captions=CLEARANCE_CAPTIONS,
                     wall_finish=GYP,
                     rooms=m['rooms'], openareas=m['openareas'], furn=m['furn'],
                     doors=m['doors'], wins=m['wins'], openings=m['openings'],
                     dims=B1dims, notes=[], chains=m['chains'], joists=(), tags=None)


# ---------------- what this building has to keep true ----------------
# Checked before anything is drawn (build.py's check_model()), beside the geometry they
# measure. Each is a function the tests call with the model patched.

def b1_outside():
    """Every room, open area and fitting past the house's inside faces, on either level,
       measured as the sheet draws them: regridded, against the stud faces. (Measured in
       model feet a fitting placed flush from the regridded wall reads as past it, because
       the regrid maps a fitting's origin and keeps its size.)"""
    out = []
    for lv, m in sorted(LEVEL.items()):
        P = m['plan']
        out += [(lv, n) for n in geom.beyond([P.rect(r) for r in m['rooms']], P.poly(m['openareas']),
                                             [P.keep(f) for f in m['furn']],
                                             EXT_STUD, B1_W-EXT_STUD, EXT_STUD, B1_D-EXT_STUD)]
    return out


def b1_vanity():
    """Bath 1's vanity as drawn, and what it has to clear: the room's walls, the shower,
       and the swing of the door off the hall. Regridded, as the sheet draws them."""
    P = PLAN_B1_L1
    room = P.rect(next(r for r in L1_ROOMS if r[4] == "BATH 1"))
    van = P.keep(next(f for f in F_L1 if f[4] == 'lav'))
    sh = P.keep(next(f for f in F_L1 if f[4] == 'shower'))
    door = P.span(next(d for d in L1_DOORS if d[3] == 'v' and abs(d[0]-(X_HALL1+PARTITION/2.0)) < 1e-6))
    hx, hy, leaf = door[0], door[1], door[2]
    # the nearest point of the vanity to the door's hinge, against the leaf's reach
    nx = min(max(hx, van[0]), van[0]+van[2]); ny = min(max(hy, van[1]), van[1]+van[3])
    return dict(width=van[3], depth=van[2],          # along the left wall, and out from it
                inside=(room[0]-1e-6 <= van[0] and van[0]+van[2] <= room[0]+room[2]+1e-6 and
                        room[1]-1e-6 <= van[1] and van[1]+van[3] <= room[1]+room[3]+1e-6),
                to_shower=sh[1]-(van[1]+van[3]),
                to_swing=((nx-hx)**2+(ny-hy)**2)**0.5-leaf)


def check_b1_vanity():
    v = b1_vanity()
    print("UNIT 1 BATH 1 VANITY: %s x %s;  %s to the shower;  %s clear of the door swing"
          % (inches(v['width']), inches(v['depth']), inches(v['to_shower']), inches(v['to_swing'])))
    assert v['width'] >= IN(24)-1e-9, "Bath 1's vanity is under 24\""
    assert v['inside'], "Bath 1's vanity is past its walls"
    assert v['to_shower'] >= -1e-9, "Bath 1's vanity runs into the shower"
    assert v['to_swing'] >= -1e-9, "Bath 1's vanity is in the door's swing"


def check_b1_inside():
    bad = b1_outside()
    n = sum(len(m['rooms'])+len(m['openareas'])+len(m['furn']) for m in LEVEL.values())
    print("BUILDING 1 ROOMS AND FITTINGS INSIDE THE WALLS: %s" % ("all %d" % n if not bad else bad))
    assert not bad, "Building 1: past the inside face of its walls: %s" % bad


# RCO 303.1: each habitable space's glazing against its net floor area, 8 percent glazed
# and half that openable; RCO 310.1: every sleeping room has an emergency escape opening,
# and W-A is the one unit that is. A window serves the space its centre falls in once it
# is moved a few inches off its wall into the room.
HABITABLE = {1: ("LIVING / KITCHEN",), 2: ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3")}


def _space_name(labels):
    return "LIVING / KITCHEN" if len(labels) > 1 else labels[0][2]


def _served(win, level):
    """The model polygon a window opens into, by name, or None."""
    x, y, ln, o = win[:4]
    into = 0.3
    pt = ((x+ln/2.0, y+(into if y < B1_D/2.0 else -into)) if o == 'h' else
          (x+(into if x < B1_W/2.0 else -into), y+ln/2.0))
    for poly, labels in LEVEL[level]['openareas']:
        if geom.inside(pt, poly):
            return _space_name(labels)
    return None


def b1_glazing():
    """{space: (glazed SF, net SF, [marks])} for every habitable space, on the regridded
       polygons the sheet draws."""
    out = {}
    for lv, names in sorted(HABITABLE.items()):
        m = LEVEL[lv]
        polys = m['plan'].poly(m['openareas'])
        for (poly, labels), (rpoly, _l) in zip(m['openareas'], polys):
            nm = _space_name(labels)
            if nm in names:
                out[nm] = [0.0, geom.area(rpoly), []]
        for w in m['wins']:
            nm = _served(w, lv)
            if nm in out:
                out[nm][0] += WIN_SF[w[4]]; out[nm][2].append(w[4])
    return {k: tuple(v) for k, v in out.items()}


def check_b1_glazing():
    gl = b1_glazing()
    print("UNIT 1 GLAZING, RCO 303.1 / ESCAPE, 310.1: %s"
          % ", ".join("%s %d%% (%s)" % (k, round(100.0*g/a), " ".join("W-"+mk for mk in mks))
                      for k, (g, a, mks) in sorted(gl.items())))
    missing = [n for names in HABITABLE.values() for n in names if n not in gl]
    assert not missing, "Unit 1: no such space on the plan: %s" % missing
    for k, (g, a, mks) in gl.items():
        assert g >= 0.08*a - 1e-9, "Unit 1 %s: %.1f SF of glass is under 8%% of %.0f SF" % (k, g, a)
        assert g/2.0 >= 0.04*a - 1e-9, "Unit 1 %s: openable area under 4%% of its floor" % k
        if k.startswith("BEDROOM"):
            assert "A" in mks, "Unit 1 %s has no W-A, the emergency escape opening" % k


# RCO 311.7, on the regridded plans: the flight the spec describes, in a column both
# levels put in the same place, a landing at each end, and nothing overhead but the well;
# and RCO 311.6's 3'-0" hallway, which the Level 2 corridor beside the well has to be.
RISER_MAX, TREAD_MIN, STAIR_CLR_MIN, LANDING_MIN, HEADROOM_MIN, HALL_MIN = (
    IN(8.25), IN(9.0), 3.0, 3.0, IN(80.0), 3.0)


def _rect_hits(r, x0, y0, x1, y1):
    return r[0] < x1-1e-6 and r[0]+r[2] > x0+1e-6 and r[1] < y1-1e-6 and r[1]+r[3] > y0+1e-6


def b1_stair():
    """The stair's figures as the plans put them, in feet."""
    P1, P2 = PLAN_B1_L1, PLAN_B1_L2
    s = B1_STAIR
    col = [(P.x(X_ST, Y_FOOT_RISER), P.x(19.5, Y_FOOT_RISER)) for P in (P1, P2)]
    # the foot landing: kitchen floor past the bottom riser, clear of every fitting
    land = (X_ST, Y_FOOT_RISER, 19.5, Y_FOOT_RISER+s.foot_landing)
    in_foot = [f[4] for f in F_L1 if _rect_hits(f, *land)]
    # the flight's footprint, and what Level 2 puts over it: a room other than the well,
    # or a floor (an open area) anywhere across it
    fl = (X_ST, Y_TOP_RISER, 19.5, Y_FOOT_RISER)
    over = [r[4] for r in L2_ROOMS if r[4] and _rect_hits(r, *fl)]
    over += [_space_name(l) for poly, l in OA_L2
             if any(geom.inside((X_ST+dx, y), poly) for dx in (0.1, 1.5, 3.4)
                    for y in (Y_TOP_RISER+0.1, (Y_TOP_RISER+Y_FOOT_RISER)/2.0, Y_FOOT_RISER-PARTITION-0.1))]
    # headroom: under Level 2's ceiling over the well, and under the Level 2 floor edge the
    # guard wall stands on at the well's far end, over the lowest treads
    edge = Y_WELL-PARTITION
    k = -(-(Y_FOOT_RISER-edge)//s.tread)                  # risers climbed under that edge
    head = min(levels.UPPER_CEILING-(levels.FF2-s.riser),
               levels.F2_CEILING-(levels.FF1+k*s.riser))
    return dict(
        riser=s.riser, tread=s.tread, risers=s.risers, treads=s.treads,
        column=col, clear=col[0][1]-col[0][0]-2*GYP,
        top=P2.y(Y_TOP_RISER)-(P2.y(0.5)+GYP),
        foot=P1.y(Y_KIT)-GYP-P1.y(Y_FOOT_RISER), in_foot=in_foot,
        riser_ys=(P2.y(Y_TOP_RISER), P1.y(Y_FOOT_RISER), P2.y(Y_FOOT_RISER)),
        headroom=head, overhead=over,
        hall=P2.x(X_COR1, 5.0)-P2.x(X_COR0, 5.0)-2*GYP)


def check_b1_stair():
    f = b1_stair()
    print("UNIT 1 STAIR, RCO 311.7: %dR @ %s / %dT @ %s, rising to the front;  clear %s;  "
          "landings %s top, %s foot;  headroom %s;  Level 2 corridor %s clear"
          % (f['risers'], inches(f['riser']), f['treads'], inches(f['tread']), fmt(f['clear']),
             fmt(f['top']), fmt(min(f['foot'], B1_STAIR.foot_landing)), fmt(f['headroom']),
             fmt(f['hall'])))
    assert f['treads'] == f['risers']-1, "a straight flight has one tread fewer than risers"
    assert abs(f['riser']*f['risers']-levels.FLOOR_RISE) < 1e-9, "the risers do not make the floor rise"
    assert f['riser'] <= RISER_MAX+1e-9, "riser over the 8-1/4\" of RCO 311.7.5.1"
    assert f['tread'] >= TREAD_MIN-1e-9, "tread under the 9\" of RCO 311.7.5.2"
    assert f['column'][0] == f['column'][1], "the stair column moves between the levels: %s" % f['column']
    assert f['clear'] >= STAIR_CLR_MIN-1e-9, "stair clear width under the 36\" of RCO 311.7.1"
    assert abs(f['riser_ys'][0]-Y_TOP_RISER) < 1e-6 and abs(f['riser_ys'][1]-Y_FOOT_RISER) < 1e-6 \
        and abs(f['riser_ys'][2]-Y_FOOT_RISER) < 1e-6, "the plans do not put the risers where the stair is"
    assert f['top'] >= LANDING_MIN-1e-9, "top landing under the 36\" of RCO 311.7.6"
    assert f['foot'] >= LANDING_MIN-1e-9, "foot landing under the 36\" of RCO 311.7.6"
    assert not f['in_foot'], "something stands on the foot landing: %s" % f['in_foot']
    assert not f['overhead'], "Level 2 floor over the flight: %s" % f['overhead']
    assert f['headroom'] >= HEADROOM_MIN-1e-9, "headroom under the 6'-8\" of RCO 311.7.2"
    assert f['hall'] >= HALL_MIN-1e-9, "Level 2 corridor under the 3'-0\" of RCO 311.6"


# RCO M1502.3: the dryer cap 3'-0" from every opening in its wall, in any direction. The
# cap can land anywhere over the W/D, so it is taken at the edge of that bay nearer each
# opening, DR_CAP_Z above the Level 1 floor. Only the rear wall's openings count.
DR_CLR_MIN = 3.0
DR_CAP_Z = 4.5


def b1_dryer():
    """[(opening, distance)] from the dryer cap to every opening in the rear wall."""
    wd = next(f for f in F_L1 if f[4] == 'wd')
    P1 = PLAN_B1_L1
    bay = (P1.x(wd[0], Y_REAR), P1.x(wd[0], Y_REAR)+wd[2])
    cap_z = levels.FF1+DR_CAP_Z
    out = []
    for lv, ff in ((1, levels.FF1), (2, levels.FF2)):
        m = LEVEL[lv]
        ops = [(w[0], w[2], ff+WIN_GEOM[w[4]][0], ff+sum(WIN_GEOM[w[4]]), "L%d W-%s" % (lv, w[4]))
               for w in m['wins'] if w[3] == 'h' and abs(w[1]-Y_REAR) < 1e-6]
        ops += [(d[0], d[2], ff, ff+6.0+8.0/12.0, "L%d DOOR" % lv)
                for d in m['doors'] if d[3] == 'h' and abs(d[1]-Y_REAR) < 1e-6]
        for x, ln, z0, z1, nm in ops:
            a = m['plan'].x(x, Y_REAR); b = a+ln
            dx = max(0.0, a-bay[1], bay[0]-b)
            dz = max(0.0, z0-cap_z, cap_z-z1)
            out.append((nm, (dx*dx+dz*dz)**0.5))
    return out


def check_b1_dryer():
    d = b1_dryer()
    print("UNIT 1 DRYER CAP, REAR WALL, M1502.3: %s"
          % (", ".join("%s %s" % (nm, fmt(v)) for nm, v in d) or "no openings"))
    for nm, v in d:
        assert v >= DR_CLR_MIN-1e-9, "Unit 1 dryer cap is %s from %s, under 3'-0\"" % (fmt(v), nm)

"""Building 2 — Units 4 and 5, the two ADUs, 26'-0" x 28'-0" at the rear of the lot.

Everything Building 2 IS, in the order it has to be built: the rooms, the open areas the
plan is punched out of, PLAN_B2 to regrid them, the Unit 5 stair placed against the
courtyard face, and then the openings — which cannot come earlier, because two of the
windows are placed by the stair.

THE PLAN. Two bands, front and rear, on one bearing wall across the building.

  * The front band, courtyard wall to the bearing wall, is one open room: the kitchen
    and dining on the Sage side, the living space and the entry on the adjacent-
    parcel side. The mechanical closet stands in the Sage corner against the
    bearing wall, its louvered pair opening into the kitchen, so its water-heater vent
    and dryer duct go straight out the Sage wall — A-001 note 16.
  * The rear band is the two bedrooms, equal, one each side of a 5'-0" column that
    holds the hall at the front and the bath at the rear. The hall opens to the front
    band through the bearing wall and serves both bedrooms and the bath, so nothing
    is entered through the living space — A-001 note 14.
  * Each bedroom's reach-in is on its hall-side wall, backing the bath. Stack D
    rises in the bath's adjacent-parcel wall with a closet on the far side of it, so
    no drain runs in a bedroom wall — the rule P-601 note 1a states for Unit 1.
  * The floor is F1 I-joists in two bays, courtyard wall to the bearing wall and the
    bearing wall to the rear, so the only opening in the bearing line is the hall's.

Building 2 shares nothing with Building 1 but the site and the stair spec. The stair
both buildings use is EXT_STAIR in src/stairs.py, and Unit 5's is that stair with a
longer top landing.

Model coordinates are PRE-mirror: low x is the adjacent-parcel side, high x is Sage,
y runs from the courtyard face to the rear. The sheet mirror puts Sage on the left.

What is NOT here: the drawing, which is A-103 and the elevations, and the stair check,
which needs the canvas.
"""
from src.finishes import BOARD     # the finish on a stud face, for the clear figures
from src.openings import WIN_HEAD, WIN_SF, WIN_W
from arkitect.lib.model import geom
from src import fsd, levels
from arkitect.codes.ohio.rco import fire_separation as rco_fsd
from arkitect.lib.units import IN, fmt
from arkitect.lib.model.records import PlanLevel
from arkitect.codes.columbus.legends import CLEARANCE_CAPTIONS
from arkitect.lib.model.regrid import EXT_STUD, PART_STUD, PARTITION, Zone, Plan
from arkitect.lib.model.dimensions import strings, wall_faces
from src.stairs import EXT_STAIR

# The same width as Building 1, so the two buildings share both side yards.
B2_W, B2_D = 26.0, 28.0

# ---------------- the rooms ----------------
Y_BEAR = 15.0                    # front face of the bearing wall, model y
X_COL0, X_COL1 = 10.5, 15.5      # the hall / bath column between the bedrooms

# Sizes the design names, held through the regrid rather than left to the slack.
MECH_DEPTH = 3.0+4.0/12.0        # 3'-4" off the Sage wall: a 34" stacked W/D plus room to stand
MECH_RUN   = 5.5                 # 5'-6" along it: W/D, then the heater in its own bay
BATH_WIDTH = 5.0                 # the tub
BATH_DEPTH = 8.0
CL_RUN     = 6.0                 # 6'-0" of bypass door on each reach-in
BR_WIDTH   = ((B2_W-2*EXT_STUD)-BATH_WIDTH-2*PART_STUD)/2.0   # what the column leaves, halved

B2U=[(X_COL0,15.4,5.0,3.5,"HALL"),
     (X_COL0,19.3,5.0,8.2,"BATH",(1.5,-0.9)),
     (22.1,9.5,3.4,5.5,"MECH",(0.0,0.0),"compact","nolabel"),
     (8.1,21.5,2.0,6.0,"CL."),
     (15.9,21.5,2.0,6.0,"CL.")]

# The open front band, notched for the mechanical closet; the two bedrooms, each
# notched for its own reach-in. A closet's opening face is the room's edge — there is
# no wall on that side, only the D-5 leaves in the plane.
OPEN_B2=[(0.5,0.5),(25.5,0.5),(25.5,9.1),(21.7,9.1),(21.7,Y_BEAR),(0.5,Y_BEAR)]
BR1_B2=[(0.5,15.4),(10.1,15.4),(10.1,21.1),(8.1,21.1),(8.1,27.5),(0.5,27.5)]
BR2_B2=[(15.9,15.4),(25.5,15.4),(25.5,27.5),(17.9,27.5),(17.9,21.1),(15.9,21.1)]

# The living / kitchen split is a design statement, not a wall: the living side ends
# where the fridge does. Its two areas are computed from the regridded polygon below
# and written back into the labels, so the figures on the sheet are measured.
X_SPLIT = 12.7

def _open_labels(living_sf="", kitchen_sf=""):
    return [(6.5,6.5,"LIVING","",living_sf),
            (18.6,6.0,"KITCHEN / DINING","",kitchen_sf)]

OA_B2=[(OPEN_B2,_open_labels()),
       (BR1_B2,[(3.8,24.6,"BEDROOM 1",None,"AUTO SF")]),
       (BR2_B2,[(22.2,24.6,"BEDROOM 2",None,"AUTO SF")])]

B2_XHOLD={(22.1,25.5,MECH_DEPTH),(X_COL0,X_COL1,BATH_WIDTH),
          (0.5,10.1,BR_WIDTH),(15.9,25.5,BR_WIDTH)}
B2_YHOLD={(9.5,Y_BEAR,MECH_RUN),(19.3,27.5,BATH_DEPTH),(21.5,27.5,CL_RUN)}

PLAN_B2 = Plan([Zone(B2U,OA_B2,0.5,27.5,B2_W,EXT_STUD,B2_D-EXT_STUD,
                     yhold=B2_YHOLD,xhold=B2_XHOLD)],B2_W,B2_D)

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
F_B2=[# bath: vanity beside the door on the wall the stack rises in, facing across the
      # bath into the clear strip beside the door swing rather than down at the pan; the
      # pan on that same wall, the tub across the rear end draining at it
      (X_COL0,19.3,1.5,2.0,'lav','e'),
      (X_COL0,22.5,2.33,1.67,'wc','e'),
      (X_COL0,25.0,5.0,2.5,'tub','w','w'),
      # kitchen: the run along the courtyard wall, under the Unit 5 flight where Unit 4's
      # wall can carry no window (Unit 5's, above the flight, takes a W-B over the counter
      # between the fridge and the range); the sink on the Sage leg under W-A
      (15.8,0.5,9.7,2.0,'counter'),(20.5,0.5,2.5,2.0,'range','s'),
      (12.7,0.5,3.0,2.5,'fridge','n'),
      (23.5,2.5,2.0,6.0,'counter'),(23.5,3.25,2.0,2.5,'sink'),
      # dining at the kitchen end — 4'-0" table, five places
      (12.5,5.0,4.0,2.5,'table'),
      (13.0,3.7,1.3,1.3,'chair'),(14.9,3.7,1.3,1.3,'chair'),
      (13.0,7.5,1.3,1.3,'chair'),(14.9,7.5,1.3,1.3,'chair'),
      (11.2,5.9,1.3,1.3,'chair'),
      (2.5,10.0,6.0,2.6,'sofa','n'),
      # mechanical closet: the stacked W/D in the corner at the top, then the panel,
      # then the 40-gallon storage heater at the far end of the same 5'-6" Sage wall
      # — 2'-3" + 1'-2-3/8" + 1'-6", which is 4'-11-3/8" of 5'-6". The tank's 30" x 30"
      # working space is borrowed through the open louvered pair, as the tankless's was.
      # The four tank numbers are SOLVED against the stud grid, which stretches this
      # band, so that what is finally drawn is 18" square; check_working_spaces() proves
      # it.
      (22.67,9.5,2.83,2.25,'wd'),
      (23.985600,13.494750,1.520050,1.489600,'wh'),
      (21.339400,12.463550,2.646550,2.531200,'whclear'),
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
      (25.25,11.78,0.25,1.2,'panel','w'),(22.25,11.75,3.0,2.5,'clear','n'),
      (0.5,15.4,5.0,6.6667,'bed','n'),
      (20.5,15.4,5.0,6.6667,'bed','n')]

# ---------------- Unit 5 exterior stair, Building 2 ----------------
# Units 4 and 5 stack exactly and share one door position, so the top landing has to
# be at that door and the flight can only run one way along the face it is on.
#
# FACE. Two are possible and they trade the same way Unit 3's did.
#   SAGE   — fire separation distance is measured to the street centreline, RCO 202,
#               so the underside is unrated; but the stair projects 3'-6" into the same
#               8'-0" side-street building line that is already with Zoning Clearance
#               for Unit 3, and Unit 5's door would have to leave Unit 4's face.
#   COURTYARD — the RCO 302.1 imaginary line stands 9'-0" off this face (src/fsd.py),
#               so a 3'-6" projection leaves 5'-6" to it, past the 5'-0" of Table
#               302.1(1): the underside is unrated here too. No building line reaches
#               the courtyard: there is no zoning question at all, and both flats keep
#               the same door.
# The courtyard is chosen, and now it costs nothing at all. It used to buy a listed
# 1-hour underside — the line was the courtyard midline, 6'-0" out, and the stair left
# 2'-6" to it. Flip U5_STAIR_COURTYARD to move it, and the rating, the notes and the
# schedule row follow; move fsd.OFF_B1 and the clearance does.
U5_STAIR_COURTYARD = True

# The same stair, with a 7'-0" top landing instead of 3'-6" — long enough to cover the
# Unit 4 door AND a W-A, which is the one thing Unit 3's could not do once its flight
# had to stop short of Building 1's rear wall.
U5_STAIR     = EXT_STAIR.with_landing(7.0)

U5_STAIR_W   = U5_STAIR.width

U5_LAND_LEN  = U5_STAIR.landing_len

U5_LAND_D    = U5_STAIR.landing_depth

U5_RISERS, U5_TREADS, U5_TREAD = U5_STAIR.risers, U5_STAIR.treads, U5_STAIR.tread

U5_RUN       = U5_STAIR.run

U5_STOOP_Z   = U5_STAIR.stoop_above_grade

U5_JAMB      = 4.0/12.0

# Unit 4 / Unit 5's door: 2'-0" of wall from the adjacent-parcel corner to the jamb,
# authored through Plan.inv_x so the regrid cannot move it, and read back in FINAL
# SHEET coordinates on the courtyard face.
_b2door      = (PLAN_B2.inv_x(2.0,0.5),0.5,3.0,'h',-1,"ext")

_b2door_r    = PLAN_B2.span(_b2door)

U5_DOOR_X0   = B2_W-(_b2door_r[0]+_b2door_r[2])

U5_DOOR_X1   = B2_W-_b2door_r[0]

# Landing pushed hard against the adjacent-parcel end, so the flight gets the long
# side of the face. True feet, like the Unit 3 stair, not regridded.
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
# convenient to fasten a runner to. With the line at 3'-0" off Building 1 the stair
# stands 5'-6" from it, Table 302.1(1) asks nothing of a projection at 5'-0" or more,
# and the membrane and the steel both go.
# docs/superpowers/specs/2026-09-15-imaginary-line-wood-stairs-design.md
U5_UNDERSIDE   = None

# A rated underside hangs BELOW the landing framing, so Unit 4's head clearance is what
# pays for it, and check_u5_stair_clear() measures from the membrane rather than from the
# framing. There is none now, and Unit 4's door and its W-A get the 5-1/2" back: the
# soffit rises from +9'-2-1/2" to +9'-8". The conditional stays because it is what would
# put the membrane back if the line ever moved past 3'-6".
U5_MEMBRANE    = IN(3.625)+3*IN(0.625) if U5_STAIR_RATED else 0.0

U5_LAND_SOFFIT = U5_STAIR.soffit-U5_MEMBRANE

# ---------------- the openings ----------------
# The courtyard face carries the Unit 5 stair for 21'-3-1/2" of its 26'-0", and the
# rest of it is under the flight, so the face takes exactly what the landing deck
# covers: the door and one W-A beside it, 4" jambs each side.
_b2w_deck    = PLAN_B2.inv_x(B2_W-(U5_LAND_X0+U5_JAMB+3.0),0.5)
B2_COURT_WIN = (_b2w_deck,0.5,3.0,'h',"A")

# Sage wall: the kitchen's W-A over the sink, and Bedroom 2's beyond the bed.
B2_SAFF_WIN  = (B2_W-0.5,3.0,3.0,'v',"A")
B2_BR2_WIN   = (B2_W-0.5,22.5,3.0,'v',"A")

# Building 2, as drawn on C-101, and the openings in the wall its own service goes on.
# Units 4 and 5 used to be metered at Building 1 with a feeder each run back underground
# — two feeders supplying one structure, which NEC 225.30 allows only by special
# permission, and a buried gas line for their two heaters that no sheet drew. Building 2
# takes its own service instead, so both questions go away and the 39'-6" of trench with
# them. Its exterior lighting goes on a Building 2 house meter for the same reason: a
# house circuit brought over from Building 1 would be a second supply to this structure.
B2_X0, B2_Y0 = 8.0, 80.0

B2_PARCEL_X = B2_X0+B2_W

# Building 2's parcel-wall openings, named here rather than inside B2win on A-103,
# because C-101 places the service against them and is drawn long before A-103 is:
# the living space's W-C, and Bedroom 1's egress W-A past the foot of the bed.
B2_PARCEL_WIN = [(0.5,3.0,5.0,'v',"C"),(0.5,22.5,3.0,'v',"A")]

B2_WALL_OPEN = sorted((B2_Y0+w[1], B2_Y0+w[1]+w[2], w[4]) for w in B2_PARCEL_WIN)

# Rear wall: each bedroom's second W-A centred on its clear run of wall, and a W-B
# over the tub — tempered, RCO 308.4.5, its sill under 60" above the tub floor. The
# regrid stretches the two bedrooms differently, which left the rear elevation 1-1/8"
# off symmetric; Bedroom 2's is set as the mirror of Bedroom 1's about the middle of the
# wall, as drawn, and is still within an inch of the middle of its own run.
_b2w_rear_br1 = (2.8,27.5,3.0,'h',"A")
_b2w_rear_br2 = PLAN_B2.inv_x(B2_W-PLAN_B2.x(_b2w_rear_br1[0],27.5)-3.0,27.5)
B2_REAR_WIN  = [_b2w_rear_br1,(11.5,27.5,3.0,'h',"B"),(_b2w_rear_br2,27.5,3.0,'h',"A")]

B2win=[B2_COURT_WIN,B2_SAFF_WIN,B2_PARCEL_WIN[0],
       B2_PARCEL_WIN[1],B2_BR2_WIN]+B2_REAR_WIN

# Unit 5's kitchen window, Level 2 only: a W-C in the courtyard wall over the counter,
# centred between the fridge and the range as the plan draws them — the designer's pick over the
# W-B first drawn there; its 5'-0" runs 1/2" past that 4'-11" of counter each side. Unit 4
# cannot take it
# — below, that wall is under the Unit 5 flight and stoop, check_u5_stair_clear() — but
# Unit 5's sill stands some 11'-0" over the treads beside it, so it is no stair glazing
# under RCO 308.4.6, and the courtyard face is 9'-0" from the imaginary line, where Table
# 302.1(1) sets no opening limit. B2win stays the list both levels share.
_b2_fridge = next(f for f in F_B2 if f[4] == 'fridge')
_b2_range  = next(f for f in F_B2 if f[4] == 'range')
_b2_kit_mid = (PLAN_B2.x(_b2_fridge[0],0.5)+_b2_fridge[2]+PLAN_B2.x(_b2_range[0],0.5))/2.0
_b2_kit_mark = "C"
B2_U5_KITCHEN_WIN = (PLAN_B2.inv_x(_b2_kit_mid-WIN_W[_b2_kit_mark]/2.0,0.5),0.5,WIN_W[_b2_kit_mark],'h',_b2_kit_mark)

def b2_wins(level):
    """Building 2's windows on one level: the shared list, and Unit 5's kitchen W-C above."""
    return B2win+([B2_U5_KITCHEN_WIN] if level == 2 else [])

# The entry; the two bedroom doors off the hall, each hung to open back against the
# bearing wall; the bath door hung on the far jamb so it folds against the wall away
# from the vanity; and the louvered pair on the mechanical closet, D-4A.
D4A = 2.0+2.0/12.0
B2doors=[_b2door,
         (10.3,15.7,2.67,'v',-1),(15.7,15.7,2.67,'v',1),
         (12.6,19.1,2.67,'h',-1,"far"),
         (21.9,10.08,D4A,'v',-1),(21.9,10.08+D4A,D4A,'v',-1,"far")]

# The hall's opening in the bearing wall, and the two D-5 bypass fronts.
B2op=[(X_COL0,Y_BEAR+PARTITION/2.0,5.0,'h'),(8.1,21.5,CL_RUN,'v'),(17.9,21.5,CL_RUN,'v')]

U45_HALL_OPEN = B2op[0][2]

B2dims=[(0,B2_W,'h',-5.6,None),(0,B2_D,'v',-3.4,None)]

# The floor: F1 I-joists in two bays spanning courtyard to rear, meeting on the
# bearing wall between the living space and the bedrooms. NOT DRAWN — this is model
# data. U45_BEARING_WALL below is derived from it and S-102 draws the bays; A-103 no
# longer prints span arrows over them.
_B2_JOISTS=[(0.5,11.5,Y_BEAR,"F1 I-JOISTS",'v'),(Y_BEAR+PARTITION,5.9,27.5,"F1 I-JOISTS",'v')]

# The wall the two bays meet on, in final sheet coordinates, the full width of the
# building like W4's strip. Derived from the joist plan, not typed, so moving a bay
# moves the strip S-101 casts under it.
_b2_bays = sorted((j[0], j[2]) for j in _B2_JOISTS)
U45_BEARING_WALL = (0.0, PLAN_B2.y(_b2_bays[0][1]), B2_W, PLAN_B2.y(_b2_bays[1][0]))

B2notes=[(24.085,9.95,"W/D",5.2),(22.55,12.45,"MECH",5.0)]

# ---------------- the dimension strings ----------------
# Horizontal: the walls that reach the rear wall, off the bottom of the plan; the
# mechanical closet's front wall, which reaches neither face, on a short string
# inside the closet. Nothing but the exterior reaches the courtyard face, so there
# is no top string.
_hf = wall_faces(B2U,OA_B2,0,(0.5,27.5),(0.5,B2_W-0.5))
CH_B2 = strings(_hf,(0.5,B2_W-0.5),(0.5,27.5),'h',
                [('hi',28.85,-1,'hi'),('in',12.0,-1,'near')])
# Vertical: the two side strings, and the bath's depth off its own front wall, run
# through the one clear strip of the bath between the door swing and the pan. Built
# by hand: the wall it starts on reaches neither side face, so a derived 'in' string
# would also sweep up the closet end walls three rooms over. The hall's depth is on
# its label.
_vf = wall_faces(B2U,OA_B2,1,(0.5,B2_W-0.5),(0.5,27.5))
CH_B2 += strings(_vf,(0.5,27.5),(0.5,B2_W-0.5),'v',
                 [('lo',-1.4,-1,'lo'),('hi',B2_W+1.4,1,'hi')])
CH_IN_X = 13.2
CH_B2 += [([(f,CH_IN_X) for f in (18.9,19.3,27.5)],'v',CH_IN_X,1,PARTITION,True,None)]

# ---------------- what this building has to keep true ----------------
# These run at import, next to the geometry they measure. A check that lives
# beside its model is one that gets updated when the model moves.

def check_u5_stair_clear():
    """Same rule for Building 2: nothing under the flight, 6" of soffit over anything
       under the landing deck. Units 4 and 5 stack, so it is Unit 4's openings that
       matter — its door and one W-A are the only things on this face."""
    ff1 = levels.FF1
    items = [(B2_W-(PLAN_B2.x(w[0],0.5)+w[2]),B2_W-PLAN_B2.x(w[0],0.5),
              ff1+WIN_HEAD[w[4]],"W-"+w[4])
             for w in B2win if w[3]=='h' and abs(w[1]-0.5)<1e-6]
    items+= [(B2_W-(PLAN_B2.x(d[0],0.5)+d[2]),B2_W-PLAN_B2.x(d[0],0.5),
              ff1+6.0+8.0/12.0,"D-1")
             for d in B2doors if d[3]=='h' and abs(d[1]-0.5)<1e-6 and "ext" in d[5:]]
    print("UNIT 5 STAIR, LEVEL 1 OPENINGS ON THE COURTYARD FACE  (landing deck soffit +%s):"
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
    assert not bad, "Unit 5 stair fouls an opening: %s"%bad


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
B2_DR_TERM_CLR = _gap(B2_DR_BAY,_saff_openings())

def check_b2_terms():
    print("BUILDING 2 SAGE WALL TERMINATIONS  (openings: %s):"
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
        if w[3]=='h' and abs(w[1]-27.5)<1e-6 and w[4]=="B": return "bath"
        return "br1" if x < PLAN_B2.x(X_COL0,20.0) else "br2"
    glass = {k:0.0 for k in areas}
    for w in B2win:
        r = room(w)
        if r in glass: glass[r] += WIN_SF[w[4]]
    return {k: 100.0*glass[k]/areas[k] for k in areas}

GL_U45 = u45_glazing()
GL_U45_MIN = min(GL_U45.values())

def check_b2_glazing():
    print("UNITS 4 / 5 GLAZING, RCO 303.1: %s"
          %", ".join("%s %d%%"%(k,round(v)) for k,v in sorted(GL_U45.items())))
    assert GL_U45_MIN >= 8.0, "a Units 4/5 habitable space is under the 8 percent of RCO 303.1"
    assert GL_U45_MIN/2.0 >= 4.0, "openable area under the 4 percent of RCO 303.1"


# ---------------- the level, as the plan sheet takes it ----------------
# One level's plan, drawn twice. Units 4 and 5 are identical and stack exactly — that is
# the whole point of the building — except for Unit 5's kitchen window, so `level` is
# required: every caller says which unit's walls it is drawing.
def b2_level(level, tags=None):
    """Building 2, as A-103 draws it, with the closet depths, the bypass-leaf widths
       and the RCO 307.1 dimension at the pan, like Building 1's levels. `tags` is the
       caller's to set: Level 1 of A-103 tags the Units 4/5 bearing wall W3, Level 2's
       wall above it is a non-bearing partition and gets none, and the overlay path
       (E-102, S-102) draws no tags either way."""
    return PlanLevel(plan=PLAN_B2, W=B2_W, D=B2_D,
                     captions=CLEARANCE_CAPTIONS, wall_finish=BOARD,
                     rooms=B2U, openareas=OA_B2, furn=F_B2,
                     doors=B2doors, wins=b2_wins(level), openings=B2op,
                     dims=B2dims, notes=B2notes, chains=CH_B2, joists=(),  # framing: S-102
                     tags=tags)

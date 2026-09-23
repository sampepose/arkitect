"""The lot: what stands in the yards, and the clearances that decide where.

Named sitework, not site: `site` is a standard library module that Python has already
imported and cached by the time this one would load, so `from site import *` silently
gives you the interpreter's own module and nothing here.

Service equipment belongs to neither building and to both. Each building is served at
itself, by ONE utility service to ONE meter bank on its adjacent-parcel wall — a meter
per account, four positions on Building 1 and three on Building 2 — with every heat
pump on the wall of the building it serves. A service is the utility's supply into a
building; a meter is one customer's; NEC 230.2 is what makes a second service to one
building the exception. This is the one module that reads both buildings, and neither
of them reads it.

SVC_EQUIP is the single table the site plan draws, the checks measure and the notes
describe. Those three used to disagree: the check declared two boxes a full box-length
further back than the plan drew them, and four notes said every meter bank and all five
heat pumps were on the parcel side when one has always been on Sage.

SIDE_YARD is everything standing in the 8'-0" side street yard, which C.C. 3332.22(a)(1)
governs and which G-001 and C-101 both tabulate from here.
"""
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import IN, fmt, inches
from arkitect.codes.columbus import zoning as ZONING
from src import envelope, fsd, levels
from arkitect.codes.ohio.rco import fire_separation as rco_fsd
from src import roof as ROOF
from src.mirror import B1_W, rx
from src.building1 import D_STUD, PLAN_L1, REAR_WALL, U1_DR_TERM, U23WIN_U2, U2_ENTRY, U3_LAND_LO, U3_STAIR_W, U3_STOOP_HI, W_STUD, Y_SEP_TOP, Y_SEP_BOT, site_y, windows
from src.building2 import B2_X0, B2_Y0, B2_W, B2_D, B2_PARCEL_X, B2_WALL_OPEN, U5_LAND_D, U5_LAND_X1, U5_STOOP_X0
from src.building2 import B2win, PLAN_B2, U45_BEARING_WALL, X_COL0

# Heat-pump outdoor units, one per dwelling unit, on the adjacent-parcel side, ALL FIVE
# wall-bracketed. Units 2 and 3 were the exception: with two egress windows per sleeping
# room this wall carried four 3'-0" W-A units in 23'-7" and its widest gap was 3'-4", so
# a 2'-9" unit could not stand anywhere on it and hold 3'-0" to a window on each side.
# They went to grade-mounted pads out past the building corner instead. One window per
# room, the outer one of each pair, puts a single 14'-6-1/2" solid run in the middle of
# the wall and the pads are no longer needed — which is the whole of C-101 note 5b's old
# second half. The run is found rather than assumed: it is the widest gap between
# consecutive windows on the wall, so deleting or moving a window moves the units or
# fails the build, and it is measured on the LEVEL 1 openings because those are the ones
# at the height of an outdoor unit.
#
# Both stay inside Units 2/3's own length of wall, past the W4 separation, so neither
# line set crosses it — A-001 note 19. Both also stand clear of the rear corner, where
# the dryer and water-heater caps come through the rear wall a few inches round it.
# Exterior service equipment, as data. The site plan draws this, the clearance check
# measures it and the notes describe it, because those three had drifted apart: the
# check declared HP-1 and the Unit 1 meters a full box-length further to the rear than
# the plan drew them, and four separate notes said every meter bank and all five heat
# pumps were on the adjacent-parcel side when HP-1 has always been on SAGE.
#
# Building 1 takes one service: EM-1 is a four-position meter bank — Units 1, 2 and 3
# and the house meter — on Unit 1's length of the parcel wall, just ahead of the W4
# separation, the one run there that is clear of every window. Unit 1's feeder enters
# its own wall; Units 2 and 3's run in conduit on the exterior face past the W4 line
# into their own length of wall, so nothing penetrates the separation. It replaced two
# services — a Unit 1 meter-main on Sage (which also stood in the side-street yard
# the variance is about) and a Units 2/3 stack here — that NEC 230.2 would have needed
# special permission for. Unit 1's panel is 125 A: its 220.82 load is 107 A, P-601.
# HP-1 stays on Sage, on the wall its panel is on. check_b1_service() holds this.
# HP-1 stands toward S Elm of Unit 1's two Sage caps, outside the stair: at site y
# 39.95 DR-1 discharged inside its length, and W4 leaves no room past it.
# check_mechanical() holds it ODU_TERM_CLR along the wall from the cap.
#   mark, site x of the near face, site y of the near end, depth out, length, what it is
SVC_EQUIP = [("HP-1",  6.90, 34.90, 1.10, 2.75, "HEAT-PUMP OUTDOOR UNIT — UNIT 1")]
SVC_B1 = [("EM-1", 34.20, 37.90, 1.60, 5.50,
           "ELECTRIC METER BANK, 4 POSITIONS — UNITS 1, 2 AND 3 AND THE BUILDING 1 HOUSE METER")]
SVC_EQUIP += SVC_B1
SAFF_WALL_X, PARCEL_WALL_X, LOT_W = 8.0, 34.0, 40.0
SVC_SAFFORD = [e for e in SVC_EQUIP if e[1]<SAFF_WALL_X]
SVC_PARCEL  = [e for e in SVC_EQUIP if e[1]>=SAFF_WALL_X]
# How far each Sage-side item reaches into the 8'-0" side street yard. The Unit 3
# stair is tabulated there under C.C. 3332.22(a)(1); HP-1 stands in the same yard and
# the zoning table names it for the same reason.
SIDE_YARD = sorted(([("STAIR",U3_STAIR_W)]
                    +[(n, SAFF_WALL_X-x) for n,x,_y,_d,_l,_s in SVC_SAFFORD]), key=lambda t:-t[1])
SIDE_YARD_TEXT = "; ".join("%s %s"%(fmt(pr),n) for n,pr in SIDE_YARD)
SY = dict(SIDE_YARD)
HP_LEN, HP_DEP = 2.75, 1.1      # outdoor unit on its bracket, in plan
HP_WIN_CLR  = 3.0               # clear to an operable window, each side
HP_PAIR_GAP = 2.0               # between the two, for coil air and service access
def _bed_wall_windows():
    wall = rx(25.5)
    return sorted((20+PLAN_L1.y(w[1]), 20+PLAN_L1.y(w[1])+w[2])
                  for w in U23WIN_U2 if w[3]=='v' and abs(w[0]-wall)<1e-6)
_bw = _bed_wall_windows()
HP_NEED = 2*HP_LEN+HP_PAIR_GAP
# The widest solid run on the sleeping-room wall, and what is left of it once each end
# gives up its 3'-0" to a window. Measured in both states of the flag — a note that
# quotes it is built into a note, and the f-string that builds that note is
# evaluated first, so these have to be real numbers either way.
HP_RUN = max(((a[1],b[0]) for a,b in zip(_bw,_bw[1:])), key=lambda r:r[1]-r[0])
HP_USE = (HP_RUN[0]+HP_WIN_CLR, HP_RUN[1]-HP_WIN_CLR)
assert HP_USE[1]-HP_USE[0] >= HP_NEED-1e-9, (
    "the BED_SIDE wall no longer holds both Units 2/3 outdoor units: %s clear "
    "between windows, %s needed"%(fmt(HP_USE[1]-HP_USE[0]),fmt(HP_NEED)))
HP_U23_Y0 = HP_USE[0]+((HP_USE[1]-HP_USE[0])-HP_NEED)/2.0   # centred in the run
HP_U23 = [HP_U23_Y0, HP_U23_Y0+HP_LEN+HP_PAIR_GAP]
def _hp_gap(y0,y1,w0,w1):
    return w0-y1 if w0>=y1 else (y0-w1 if y0>=w1 else -1.0)
HP_WIN_NEAR = min(_hp_gap(y,y+HP_LEN,w0,w1) for y in HP_U23 for w0,w1 in _bw)
HP_CORNER   = 20+PLAN_L1.y(47.5)-(HP_U23[-1]+HP_LEN)

def _check_wall(title, items, openings, spans):
    """Every box on a wall stands within one of the wall's `spans` (site y ranges — a
       building's, or one grouping's length of it), in front of no opening, and at the
       clearance its kind needs: a heat pump 3'-0" from an egress window, an electric
       meter bank only clear. Prints what it holds."""
    print("%s  (%s):"%(title, ", ".join("%s .. %s"%(fmt(a),fmt(b)) for a,b in spans)))
    for a,b,mk in openings:
        print("   W-%-4s %s .. %s%s"%(mk,fmt(a),fmt(b),"   EGRESS" if mk=='A' else ""))
    bad=[]
    for m,x,y0,d,l,_desc in sorted(items,key=lambda e:e[2]):
        y1=y0+l
        if not any(a-1e-9<=y0 and y1<=b+1e-9 for a,b in spans):
            bad.append((m,"runs past its length of wall"))
        near=None
        for a,b,mk in openings:
            gap = a-y1 if a>=y1 else (y0-b if y0>=b else -1.0)
            if gap<0: bad.append((m,"stands in front of the W-%s"%mk))
            need = HP_WIN_CLR if m.startswith("HP-") and mk=='A' else 0.0
            if 0<=gap<need-1e-9: bad.append((m,"inside %s of the W-%s"%(fmt(need),mk)))
            near = gap if near is None else min(near,gap)
        print("   %-5s %s .. %s   %s to the nearest opening"%(m,fmt(y0),fmt(y1),fmt(near)))
    assert not bad, "%s: %s"%(title,bad)

# Building 1's parcel-wall openings, in site y: Unit 1's from its study (both levels,
# the wall at page x 26) and Units 2/3's from the bedroom wall, regridded. A meter bank
# on this wall used to be measured against nothing.
B1_WALL_OPEN = sorted({(20.0+y, 20.0+y+ln, mk) for lv in (1,2)
                       for x,y,ln,o,mk in windows(lv) if o=='v' and x>13.0}
                      | {(20.0+PLAN_L1.y(w[1]), 20.0+PLAN_L1.y(w[1])+w[2], w[4])
                         for w in U23WIN_U2 if w[3]=='v' and abs(w[0]-rx(25.5))<1e-6})
# The two lengths of that wall: Unit 1's, front corner to the W4 studs, and Units 2/3's.
B1_WALL_SPANS = [(20.0, 20.0+Y_SEP_TOP), (20.0+Y_SEP_BOT, 68.0)]

def check_b1_service():
    """Building 1's parcel wall, held to the rule Building 2's has been held to. The
       Units 2/3 meter stack once stood a hand's breadth off Unit 1's Level 1 W-A and
       nothing measured it."""
    _check_wall("BUILDING 1 PARCEL WALL", SVC_B1+[e for e in SVC_EQUIP if e[0] in ("HP-2","HP-3")],
                B1_WALL_OPEN, B1_WALL_SPANS)

def check_b2_service():
    """Everything on Building 2's parcel wall stands on the wall, inside it, clear of
       every opening, and at its kind's clearance. Nothing measured this face before:
       HP-4 and HP-5 were drawn 2'-1-1/4" off the wall and in front of the two windows
       in it, HP-5 square on the Unit 5 bedroom's egress W-A.

       Selected by the list that places them, not by their x: Building 2's parcel wall
       is on the same line as Building 1's, so an x test also picks up HP-2 and HP-3."""
    _check_wall("BUILDING 2 PARCEL WALL", list(SVC_B2), B2_WALL_OPEN, [(B2_Y0, B2_Y0+B2_D)])

# Every outdoor unit is HP-n for the unit it serves, so the ones on the parcel side stop
# being identical boxes all marked "HP". Units 2 and 3 stack on Building 1.
SVC_EQUIP += [("HP-%d"%u, PARCEL_WALL_X, _y, HP_DEP, HP_LEN,
               "HEAT-PUMP OUTDOOR UNIT — UNIT %d"%u)
              for u,_y in zip((2,3),HP_U23)]
# Building 2's four boxes, ON its wall. HP-4 and HP-5 used to stand 2'-1-1/4" clear of it
# — called wall-bracketed and drawn floating in the yard — and, worse, in front of its
# windows: HP-5 sat square on the Unit 5 bedroom's egress W-A. The three clear runs on
# this wall are derived from B2_WALL_OPEN below and check_b2_service() holds everything
# inside them, so the same thing cannot be drawn again.
#
# All three stand as one group, centred in the widest run — between the living W-C and
# Bedroom 1's egress W-A — at the Units 2 / 3 pair's 2'-0" apart, so the elevation reads
# as one composed set rather than a unit tucked into the corner beside the W-C. The meter
# bank takes the W-A end: an outdoor unit keeps HP_WIN_CLR from an egress window and a
# meter bank does not.
B2_METER_LEN = 2.75
_b2_run = max(((a[1],b[0]) for a,b in zip(B2_WALL_OPEN,B2_WALL_OPEN[1:])), key=lambda r:r[1]-r[0])
_b2_lens = (HP_LEN, HP_LEN, B2_METER_LEN)
_b2_y = [(_b2_run[0]+_b2_run[1]-(sum(_b2_lens)+HP_PAIR_GAP*(len(_b2_lens)-1)))/2.0]
for _l in _b2_lens[:-1]:
    _b2_y.append(_b2_y[-1]+_l+HP_PAIR_GAP)
SVC_B2 = [
    ("HP-4", B2_PARCEL_X, _b2_y[0], HP_DEP, HP_LEN, "HEAT-PUMP OUTDOOR UNIT — UNIT 4"),
    ("HP-5", B2_PARCEL_X, _b2_y[1], HP_DEP, HP_LEN, "HEAT-PUMP OUTDOOR UNIT — UNIT 5"),
    ("EM-3", B2_PARCEL_X, _b2_y[2], 1.60, B2_METER_LEN,
     "ELECTRIC METER BANK, 3 POSITIONS — UNITS 4 AND 5 AND THE BUILDING 2 HOUSE METER")]
SVC_EQUIP += SVC_B2

# Heights above finished grade for the boxes an elevation draws — both buildings'
# adjacent-parcel faces, A-202 and A-203. The table above is plan only; these are the
# set's own figures until the utilities approve the banks and the outdoor units are
# selected:
#   mark: (underside, height)
# EM-1's meters are centred 5'-0" up. HP-2 and HP-3 keep the +2'-6" underside they were
# given when the Units 2 / 3 gas branches ran this face below them; with the gas gone
# nothing but C-101 note 5b's 4" minimum sets it, and the height was left where it is
# rather than re-drawn. Building 2's boxes take Building 1's figures, so the two parcel
# faces read alike; none of them stands beside a window any more.
# check_faces() in src/faces.py holds them.
HP_Z, HP_H = 2.5, 2.5
METER_Z, METER_H = 3.5, 3.0
SVC_Z = {"EM-1": (METER_Z, METER_H), "HP-2": (HP_Z, HP_H), "HP-3": (HP_Z, HP_H),
         "EM-3": (METER_Z, METER_H), "HP-4": (HP_Z, HP_H), "HP-5": (HP_Z, HP_H)}

SVC_HP_MARKS = [m for m,*_r in SVC_EQUIP if m.startswith("HP-")]
# What note 5d quotes: how close Building 2's meter bank comes to the Unit 5 egress
# window, and how much of that building's adjacent-parcel yard is left in front of the
# deepest box on its wall.
_b2m = [e for e in SVC_B2 if not e[0].startswith("HP-")]
_b2a = [(a,b) for a,b,mk in B2_WALL_OPEN if mk=='A']
B2_METER_CLR = min(min(abs(a-(y+l)),abs(y-b)) for _m,_x,y,_d,l,_s in _b2m for a,b in _b2a)
B2_YARD_LEFT = LOT_W-(B2_PARCEL_X+max(e[3] for e in SVC_B2))


def check_site_clearances():
    """The clearances C-101 promises and nothing else measures: the Units 2/3 heat pumps
       to the bedroom egress windows they now stand BETWEEN — so both sides count, not
       just the one below them — and Unit 1's own LIVE_SIDE equipment to the Unit 2 door
       and landing."""
    print("C-101 SITE CLEARANCES:")
    print("   UNITS 2 / 3 HEAT PUMPS   %-10s to the nearest bedroom egress window"%fmt(HP_WIN_NEAR))
    print("   %-24s %-10s between the two, %s to the rear corner"
          %("",fmt(HP_U23[1]-HP_U23[0]-HP_LEN),fmt(HP_CORNER)))
    assert HP_CORNER>=1.0-1e-9, "a Units 2/3 heat pump is at the rear corner, under the caps"
    door0 = 20+PLAN_L1.y(U2_ENTRY[1]); door1 = door0+U2_ENTRY[2]
    for nm,y0,y1 in ([(e[0],e[2],e[2]+e[4]) for e in SVC_SAFFORD]
                     +[("DR-1",20+site_y(U1_DR_TERM)-1.0,20+site_y(U1_DR_TERM)+1.0)]):
        d = min(abs(door0-y1),abs(y0-door1)) if (y1<door0 or y0>door1) else 0.0
        print("   %-24s %-10s to the Unit 2 door and landing"%(nm,fmt(d)))
        assert d>=4.0-1e-9, "%s is inside 4'-0\" of the Unit 2 door"%nm
    # The street-corner clear vision triangle, C.C. 3321.05(B)(2): its hypotenuse is the
    # line x+y = VISION_ST from the lot corner, and Building 1's front Sage corner is
    # at x+y = 28 — request 7.
    print("   S ELM / SAGE TRIANGLE %-10s Building 1's front corner inside its %s hypotenuse, %.0f SF — request %d"
          %(fmt(VISION_ST_IN), fmt(VISION_ST), VISION_ST_AREA, REQ_NO["C.C. 3321.05(B)(2)"]))
    # Each request that is geometry is still needed, and every condition that needs one
    # has one: a request the drawing no longer shows, or a condition the table no longer
    # lists, is the half-disclosure the set is not allowed to make.
    _sections = [s for s,_n in VARIANCES]
    for _sec,_needed in (("C.C. 3312.27", PARK_SETBACK < PARK_SETBACK_REQ-1e-9),
                         ("C.C. 3321.05(B)(1)", VISION_CLR < VISION-1e-9),
                         ("C.C. 3312.25", MANEUVER_HAVE < MANEUVER-1e-9),
                         ("C.C. 3321.05(B)(2)", VISION_ST_IN > 1e-9)):
        assert (_sec in _sections) == _needed, (
            "%s: the drawing %s a variance and VARIANCES %s one"
            %(_sec, "needs" if _needed else "no longer needs", "lists" if _sec in _sections else "does not list"))
    # The parking pad against the Sage line and the alley, C.C. 3312.27, 3321.05(B)(1)
    # and 3312.25. The first two are variance requests 4 and 5 and are printed for the
    # record; the third is printed because the pad head is where the maneuvering shortfall
    # has to be made up, and until it is, the figure is what zoning will measure.
    print("   PARKING PAD              %-10s off the Sage line, %s the parking setback line, C.C. 3312.27"
          %(fmt(PARK_SETBACK), fmt(PARK_SETBACK_REQ)))
    print("   SAGE / ALLEY TRIANGLE %-10s stays clear of the pad, of the %s of C.C. 3321.05(B)(1)"
          %(fmt(VISION_CLR), fmt(VISION)))
    print("   ALLEY                    %-10s right-of-way; maneuvering %s of the %s of C.C. 3312.25 — %s"
          %(fmt(ALLEY_W), fmt(MANEUVER_HAVE), fmt(MANEUVER),
            "request %d"%REQ_NO["C.C. 3312.25"] if MANEUVER_HAVE<MANEUVER-1e-9 else "clear"))
    assert HP_WIN_NEAR>=HP_WIN_CLR-1e-9, "a Units 2/3 heat pump is inside 3'-0\" of an egress window"


# ---------------- the zoning tabulation ----------------
# C-101 draws this and C-102 must carry the SAME one, with the same status wording —
# G-001 note 15, which also says that nothing on C-102 may contradict C-101. Written
# once and read by both, so "the same" is a fact about the code rather than an
# instruction to whoever draws the second sheet. Functions, not constants, because the
# rows interpolate SIDE_YARD and values the model derives.
def _yard_label(n):
    """The table's rows are sentence case, so SIDE_YARD's names are title-cased into it.
       A MARK is not a word, though: "HP-1".title() is "Hp-1", which is not what the
       plan draws beside that box or what note 5c calls it. Anything carrying a digit
       is a mark and is left exactly as it is."""
    return " ".join(w if any(ch.isdigit() for ch in w) else w.title() for w in n.split())


def zoning_rows():
    """(label, value) for every row of the zoning compliance table."""
    return [("Lot area","{:,.0f} SF".format(LOT_AREA)),("Lot type","CORNER"),
     ("Lot width req'd","50'-0\", C.C. 3332.05"),("Lot width existing","40'-0\" — VARIANCE REQUESTED"),
     ("Units permitted","5 MAX, C.C. 3332.355"),
     ("Units proposed","5"),("Lot area req'd, 3-unit","4,500 SF @ 1,500/UNIT"),("Density area avail.","4,800 SF, 3332.18(C)"),
     ("Front building line","20'-0\", C.C. 3332.21"),("Side street line","8'-0\", C.C. 3332.22(a)(1)"),
     # Everything standing in the 8'-0" side street yard, under one variance request.
     # The stair is there only when the mirror puts it on Sage; HP-1 is there in both
     # states, because Unit 1 does not move and its panel is on the stair wall.
     # Tabulating the stair alone left a reviewer to walk that yard and find more in it
     # than the sheet had mentioned.
     ("Side street yard, 3332.22(a)(1)","VARIANCE REQUESTED"),
     *[("  "+_yard_label(n),"%s PROJ. — %s TO R.O.W."%(fmt(pr),fmt(SAFF_WALL_X-pr)))
       for n,pr in SIDE_YARD],
     ("Interior side yard","%s  (%s MIN)"%(fmt(SIDE_PARCEL),fmt(SIDE_MIN))),
     ("Combined side yards","%s  (%s MIN)"%(fmt(SIDE_COMB),fmt(SIDE_COMB_MIN))),
     ("Rear yard required","{:,.0f} SF  (25% OF LOT)".format(REAR_REQ)),
     ("Rear yard provided","{:,.0f} SF".format(REAR_PROV)),
     # Building 2's share of the total rear yard of the principal dwelling, against the
     # 55 percent two adjoining detached ADUs may take under C.C. 3332.355(C)(3).
     ("ADU in rear yard, 3332.355(C)(3)","{:,.0f} SF = {:.1f}%  ({:.0f}% MAX)"
      .format(ADU_IN_REAR,ADU_REAR_PCT,ADU_REAR_MAX)),
     # The two figures the city's ADU zoning review asks its data table for — living area
     # of the primary dwelling and of the proposed ADU — and the ratio 3332.355(B)(3)(a)
     # limits. Net floor area for living quarters, G-001's NET SF column, is the measure
     # the section names; both ADUs are the same size, so one row states both.
     ("Principal living area","{:,} SF NET — UNITS 1, 2 AND 3".format(PRINCIPAL_NET)),
     ("ADU living area, 3332.355(B)(3)","{:,} SF EACH = {:.1f}%  ({:.0f}% MAX)"
      .format(ADU_NET,100.0*ADU_NET/PRINCIPAL_NET,100*ADU_PCT_MAX)),
     # Buildings AND both exterior stairs — stoop, flight and top landing, the whole of
     # what each one stands over. The two sub-rows say what the figure is made of, so a
     # reviewer who scales the footprints and gets the building figure is not left to
     # wonder where the rest came from.
     ("Lot coverage","{:,.0f} SF = {:.1f}%".format(COVERAGE,100*COVERAGE/LOT_AREA)),
     ("  Buildings","{:,.0f} SF".format(COVERAGE_BLDG)),
     ("  Exterior stairs, Units 3 and 5","{:,.0f} SF".format(COVERAGE_STAIR)),
     ("Coverage permitted","65% WITH ADU"),("Building height","UNDER 35', C.C. 3332.29"),
     # C.C. 3332.355(B)(3)(b): an ADU no taller than the principal dwelling, or 25 feet.
     # The figure is Building 2's height as C.C. 3303.08 measures a pitched roof — the
     # mean of the eave and the ridge the elevations draw on the raised heel — and the
     # sub-row gives the two it is the mean of, so a reviewer who reads the ridge off
     # A-202 sees why a ridge over 25'-0" complies. check_height() holds both limits.
     ("ADU height, 3332.355(B)(3)","%s  (%s MAX)"%(fmt(ADU_HEIGHT),fmt(ADU_HEIGHT_MAX))),
     ("  Mean of eave and ridge, 3303.08","%s / %s"%(fmt(levels.EAVE),fmt(levels.ridge(B2_W)))),
     ("Parking required","6, C.C. 3312.49  (ADUs EXEMPT)"),
     ("Parking provided","%d — VARIANCE REQUESTED"%PARK_N),
     # The pad against the Sage right-of-way, the north lot line, and the alley
     # triangle it leaves at that corner. Both are read from the pad, above, and both
     # are met: zoning asked for each and the three-stall pad answers each.
     ("Parking setback, 3312.27","%s  (%s MIN)"%(fmt(PARK_SETBACK),fmt(PARK_SETBACK_REQ))),
     ("Alley vision triangle, 3321.05(B)(1)","%s x %s CLEAR"%(fmt(VISION_CLR),fmt(VISION_CLR))),
     # Backing into the alley: the whole right-of-way is what 3312.25 measures.
     ("Maneuvering, 3312.25","VARIANCE REQUESTED"),
     ("  Alley R.O.W. behind the stalls","%s  (%s REQ'D)"%(fmt(MANEUVER_HAVE),fmt(MANEUVER))),
     # The street corner: Building 1's corner is inside the 30'-0" hypotenuse.
     ("Street vision triangle, 3321.05(B)(2)","VARIANCE REQUESTED"),
     ("  Clear of Building 1","%s x %s  (%s REQ'D)"%(fmt(VISION_ST_CLR),fmt(VISION_ST_CLR),fmt(VISION_ST)))]
     # Three rows end here that used to follow, and the same test removed all of them:
     # the table is headed ZONING COMPLIANCE — COLUMBUS R-4 and none was an R-4 matter.
     #
     # Gas connected load and foundation type are permit and construction data, carried
     # where they belong — G-001's project data as SLAB ON GRADE — NO BASEMENT, and
     # P-601 note 7, which breaks the gas load down per meter bank and calls it
     # APPROXIMATELY 799,000 where this table stated 799,000 flat.
     #
     # FEMA flood zone said VERIFY FIRM PANEL, which is a task and not a compliance
     # statement. A tabulation that answers every other line and leaves one saying
     # "verify" invites the reviewer to ask what else went unchecked. Floodplain is
     # C.C. Chapter 1150, Title 11, and the building permit — not an R-4 standard — so the
     # row did not belong here whatever the zone turns out to be. The determination is
     # still open and CLAUDE.md carries it; when it is made it belongs on G-001 with the
     # code data, as a stated zone and panel rather than an instruction to go and look.


def zoning_relief():
    """What relief is being asked for, under the table. The designer's wording and the designer's layout.

       Lines of (text, bold) runs, not strings: the heading, the count line, and each
       request's number and name are bold while the rest of the line is not, so a line
       is more than one font and src/sheets/common.py draw_runs() sets it.

       Sentence case, which the rest of the sheet is not — but the zoning table directly
       above it labels its rows in sentence case too, so the block reads with the table
       it belongs to rather than with the all-caps notes elsewhere.

       "measured from the building face" was the one clause of C-102's old note 1 that the
       zoning table did not already carry; the rest of that note restated the table's own
       sub-rows, projection and clearance both, a few inches away. It belongs here, with
       the projections it qualifies.

       Every figure is derived: the lot width from SITE_W, the yard from SAFF_WALL_X and
       the two projections from SY. 50'-0", 4 and 6 stay typed, being ordinance figures
       and counts rather than geometry.

       Fractions are written 3/8, not the single glyph. Helvetica's WinAnsi encoding has
       no U+215C: reportlab draws a capital I in its place and the sheet would have read
       1'-2I". A quarter and a half do exist there, but mixing the two forms in one list
       would be worse than using the one the whole set already uses.

       Hand-wrapped: both sheets draw these lines as given, C-101 at 7.2 pt and C-102 at
       6.2, and draw_runs asserts every line against RELIEF_W in src/sheets/common.py.
       The width is a drawing dimension and is kept there — this module is the model and
       is in feet."""
    B = lambda t: (t, True)
    R = lambda t: (t, False)
    BULLET = "       \u2022 "
    lines = [[B("ZONING RELIEF REQUESTED")],
            [R("Zoning relief is requested and has not been granted. Building permit")],
            [R("cannot issue until the Board acts.")],
            [],
            [B("%s VARIANCES REQUESTED UNDER ONE BZA APPLICATION:"%VARIANCE_WORD)],
            [],
            [B("1.  Lot width"),
             R(" \u2014 %s existing where 50'-0\" is required, C.C. 3332.05."%fmt(SITE_W))],
            [B("2.  Parking"),
             R(" \u2014 %d spaces provided where 6 are required, C.C. 3312.49."%PARK_N)],
            [B("3.  Side street yard"),
             R(" \u2014 C.C. 3332.22(a)(1), measured from the building face:")],
            [R(BULLET+"Unit 3 stair projects %s into the required %s yard."
               %(fmt(SY["STAIR"]),fmt(SAFF_WALL_X)))],
            [R(BULLET+"HP-1 projects %s."%fmt(SY["HP-1"]))],
            [B("4.  Maneuvering"),
             R(" \u2014 %s across the alley right-of-way into the stalls, where"%fmt(MANEUVER_HAVE))],
            [R("     C.C. 3312.25 requires %s."%fmt(MANEUVER))],
            [B("5.  Street vision triangle"),
             R(" \u2014 %s x %s at the S Elm / Sage corner,"%(fmt(VISION_ST_CLR),fmt(VISION_ST_CLR)))],
            [R("     where C.C. 3321.05(B)(2) requires %s x %s; Building 1's corner"
               %(fmt(VISION_ST),fmt(VISION_ST)))],
            [R("     stands %s past the hypotenuse along each right-of-way, %.0f SF in it."
               %(fmt(VISION_ST_IN),VISION_ST_AREA))],
            [],
            [R("Statement of hardship in the BZA application.")]]
    # Every request in VARIANCES is numbered here, in its order, and nothing else is.
    numbered = [runs[0][0] for runs in lines if runs and runs[0][1] and runs[0][0][:1].isdigit()]
    assert numbered == ["%d.  %s"%(i+1,n) for i,(_s,n) in enumerate(VARIANCES)], numbered
    return lines



# ---------------- the lot, as drawn ----------------
# C-101 and C-102 draw the same site at different scales, and note 15 says C-102 shall
# not depart from the geometry C-101 draws. These are read by both and owned by neither,
# so the two sheets cannot be made to disagree by editing one of them.
#
# Site coordinates: x across the lot from the Sage right-of-way, y from the S Elm
# line, both in feet, y increasing toward the alley. Building 1 occupies site x 8 .. 34
# with Sage on the LEFT of the sheet, so a Building 1 plan x maps to site x 34 - plan
# x. That is the one place the sheet mirror has to be written out; everywhere else it is
# a token.
SITE_W, SITE_D = 40.0, 126.0
# (x, y, width, depth, name, sub-label, dwelling type). Building 1 is the east building
# — the lot's S Elm end — and Building 2 the west, at the alley.
# Building 1's size is READ FROM THE BUILDING, not typed here. It used to be the
# literals 26 and 48, and only the width was tethered -- through mirror.B1_W, which
# check_framing() holds to a bearing line. The depth was tied to nothing: moving this
# footprint to 49 ft built clean, moved the lot-coverage rows on G-001, C-101 and C-102,
# and left every plan, foundation, framing and roof sheet still drawing 48'-0". The
# sub-label derives too, the way Building 2's on the next line always has.
SITE_BLDG = [(8,20,B1_W,REAR_WALL,"BUILDING 1",
              "UNITS 1, 2 AND 3 · %s x %s"%(fmt(B1_W),fmt(REAR_WALL)),"3-UNIT DWELLING"),
             (B2_X0,B2_Y0,B2_W,B2_D,"BUILDING 2",
              "UNITS 4 AND 5 (ADUs) · %s x %s"%(fmt(B2_W),fmt(B2_D)),"2-UNIT DWELLING")]
# The footprint dimensions run inside each outline, this far off the face.
BLDG_DIM_IN = 1.5
# front yard, Building 1, the gap between the buildings, Building 2, rear yard
SITE_BANDS = [(0,20,"20'-0\""),(20,68,"48'-0\""),(68,80,"12'-0\""),(80,108,"28'-0\""),
              (108,126,"18'-0\"")]

# ---------------- the rear yard, and why this project does not need relief on it ----
# All of these were typed into the zoning table and nothing measured them against the
# lot they describe.
#
# The rear yard is measured behind the PRINCIPAL building. Building 2 is a detached ADU
# and C.C. 3332.355(C)(2) exempts it from the rear yard requirement of 3332.27, so it
# does not set the rear line; it stands IN the rear yard under 3332.355(C). That is the
# whole reason this project does not need the C.C. 3332.27 variance the previous
# application on this parcel did: behind Building 1 the yard is 46% of the lot, and
# behind Building 2 it would be 14.3% — worse than the 16.7% that application had to ask
# for. If zoning ever reads Building 2 as a second principal building, this tabulation
# is wrong and a rear yard variance joins the other three.
_B1 = next(b for b in SITE_BLDG if b[4]=="BUILDING 1")
_B2 = next(b for b in SITE_BLDG if b[4]=="BUILDING 2")
LOT_AREA   = SITE_W*SITE_D
REAR_REQ   = ZONING.REAR_YARD_MIN*LOT_AREA       # C.C. 3332.27, 25 percent of the lot
REAR_LINE  = _B1[1]+_B1[3]                       # Building 1's rear wall
REAR_PROV  = (SITE_D-REAR_LINE)*SITE_W           # the total rear yard, behind that wall
# C.C. 3332.355(C)(3), ORD 2526-2025 Exhibit A: "One detached ADU may occupy up to 45
# percent of the total rear yard of the principal dwelling. Two separate or adjoining
# detached ADUs may occupy up to 55 percent of the total rear yard." Building 2 is two
# adjoining ADUs, Units 4 and 5, so the share is 55, and the yard it is a share OF is
# the whole yard behind Building 1 — not the 25 percent yard 3332.27 requires, which
# this table once measured a 693 SF allowance against with no section to cite.
#
# 3332.355(C)(1) puts a detached ADU in the rear yard area of the principal dwelling, so
# the part of Building 2 that counts is the part behind REAR_LINE, and the first assert
# holds it to be all of it. Its whole footprint is 728 SF of the 2,320 SF yard, 31.4%.
# The building only: the Unit 5 stair is lot coverage, below, not the dwelling unit.
ADU_IN_REAR = max(0.0, min(_B2[1]+_B2[3],SITE_D)-max(_B2[1],REAR_LINE))*_B2[2]
ADU_REAR_PCT = 100.0*ADU_IN_REAR/REAR_PROV
ADU_REAR_MAX = 55.0
COVERAGE_BLDG = sum(b[2]*b[3] for b in SITE_BLDG)
# Both exterior stairs count toward coverage: each is a structure standing on the lot
# from its 6" stoop to its top landing, and C-101 draws each one over exactly this
# ground. Unit 3's runs down Building 1's street face — U3_STAIR_W out from the face,
# U3_LAND_LO to U3_STOOP_HI along it; Unit 5's runs across Building 2's courtyard face
# — U5_LAND_D out, U5_STOOP_X0 to U5_LAND_X1 along. Site x of the Unit 3 stair is
# SITE_STAIR, defined below with the rest of the site tokens, so its width is taken
# from the stair itself here rather than from where the mirror put it.
COVERAGE_STAIR = (U3_STAIR_W*(U3_STOOP_HI-U3_LAND_LO)
                  +U5_LAND_D*(U5_LAND_X1-U5_STOOP_X0))
COVERAGE   = COVERAGE_BLDG+COVERAGE_STAIR
# C.C. 3332.18(D) counts what a building occupies, the footprint above. The roofs overhang
# it (src/roof.py), and 3332.28(B) keeps a cornice in a yard; counted to the dripline
# instead, coverage must still be under the 65 percent the table prints.
COVERAGE_PERMITTED = ZONING.COVERAGE_MAX
COVERAGE_ROOF = sum(ROOF.plan_area(r) for r in ROOF.ROOFS)+COVERAGE_STAIR
assert COVERAGE_ROOF <= COVERAGE_PERMITTED*LOT_AREA, (
    "lot coverage counted to the roof dripline is %.0f SF, %.1f%%, over the 65%% C-101 prints"
    %(COVERAGE_ROOF,100*COVERAGE_ROOF/LOT_AREA))
assert REAR_PROV >= REAR_REQ, (
    "rear yard is under the 25 percent of C.C. 3332.27: %.0f SF behind Building 1, "
    "%.0f SF required — this project now needs a rear yard variance"%(REAR_PROV,REAR_REQ))
assert _B2[1] >= REAR_LINE, (
    "Building 2 starts at y %.2f, forward of Building 1's rear wall at y %.2f — a detached "
    "ADU must be in the rear yard area, C.C. 3332.355(C)(1)"%(_B2[1],REAR_LINE))
assert ADU_REAR_PCT <= ADU_REAR_MAX, (
    "Building 2 takes %.1f%% of the rear yard, over the %.0f%% two adjoining detached ADUs "
    "may occupy, C.C. 3332.355(C)(3)"%(ADU_REAR_PCT,ADU_REAR_MAX))

# ---------------- the ADUs against the principal dwelling, C.C. 3332.355(B)(3) -------
# "An ADU must not exceed 65 percent of the minimum net floor area of the principal
# dwelling with which it is associated, or 1,000 square feet, whichever is greater, but
# in no case shall the ADU exceed the size of the principal dwelling." (Ord. 2526-2025,
# eff. 11-24-2025.) The principal dwelling is Building 1, Units 1, 2 and 3 together; each
# of Units 4 and 5 is an ADU and is measured on its own.
#
# Net floor area for living quarters per unit, C.C. 3332.17 — above grade, no porch,
# utility room or garage. G-001's AREA TABULATION prints this column from here, so the
# figure the zoning table divides is the one the cover states.
#
# DERIVED, less one typed part. FRAMED_SF is the zone each dwelling occupies stud face to
# stud face, straight from the model — the same faces the plans are dimensioned to — so a
# wall that moves moves the printed area. NET_DEDUCT is the part the geometry cannot tell
# us: the interior partitions, Unit 1's stair, and the finishes net floor area is measured
# to. It was calibrated on 2026-09-15 against the areas this set carried before W4 became
# two walls (1,007 / 565 / 656), and it is what a reviewer would challenge, so keep it
# small, stable and explained rather than retyping NET_SF after a geometry change.
FRAMED_SF = {1: W_STUD*D_STUD*2.0,                                      # two levels
             2: (B1_W-2*EXT_STUD)*(48.0-EXT_STUD-Y_SEP_BOT),
             4: (B2_W-2*EXT_STUD)*(B2_D-2*EXT_STUD)}
FRAMED_SF[3] = FRAMED_SF[2]      # Unit 3 stacks on Unit 2
FRAMED_SF[5] = FRAMED_SF[4]      # Unit 5 on Unit 4
NET_DEDUCT = {1: 143.75, 2: 26.55, 3: 26.55, 4: 23.34, 5: 23.34}
NET_SF = {u: int(round(FRAMED_SF[u]-NET_DEDUCT[u])) for u in sorted(FRAMED_SF)}
for _u, _d in NET_DEDUCT.items():
    assert 0.02 <= _d/FRAMED_SF[_u] <= 0.25, (
        "unit %d's net floor area deducts %.1f SF from a %.1f SF framed zone: re-measure it "
        "against the plans rather than leaving it typed" % (_u, _d, FRAMED_SF[_u]))
PRINCIPAL_NET = NET_SF[1]+NET_SF[2]+NET_SF[3]
ADU_NET       = NET_SF[4]
ADU_PCT_MAX   = ZONING.ADU_PCT_MAX
ADU_NET_MAX   = max(ADU_PCT_MAX*PRINCIPAL_NET, 1000.0)
assert NET_SF[4]==NET_SF[5], "Units 4 and 5 stack; the zoning table states one ADU size"
assert ADU_NET <= ADU_NET_MAX and ADU_NET <= PRINCIPAL_NET, (
    "an ADU of %d SF net is over the %.0f SF C.C. 3332.355(B)(3)(a) allows against a "
    "%d SF principal dwelling"%(ADU_NET,ADU_NET_MAX,PRINCIPAL_NET))


# ---------------- the side yards, at the face a yard is measured to ----------------
# Every dimension on this set is to the face of the stud (G-001 note 5), and C-101's
# side yard figures are no exception: they are FRAMING dimensions. A yard, and the fire
# separation distance of RCO 202, are measured to the building's outside face. The
# figure that has to clear the minimum is therefore the dimension less what the wall
# carries outside its studs, and the difference is the tolerance the wall really has.
#
# Nothing measured this until 2026-09-20. It matters because Table 302.1(1) changes row
# at exactly 5'-0": a wall that clears it in framing and misses it in siding is 1 HOUR
# with its openings limited to 25 percent, and no site plan drawn to face of stud can
# show that. Here both side walls have most of a foot in hand, which is the answer to
# the question, but the answer is now derived instead of assumed.
SIDE_MIN      = rco_fsd.RATED_MAX    # 5'-0": under it Table 302.1(1) rates the wall and
                                     # limits its openings to 25 percent. NOT the zoning
                                     # minimum, which C.C. 3332.26 puts at 3'-0" on a lot
                                     # 40'-0" wide or less -- see CLAUDE.md. This is the
                                     # figure that actually binds these walls.
SIDE_COMB_MIN = 8.0                  # the two side yards together, as the zoning table states it
# The governing assembly on each wall, which is the THICKEST it carries: both parcel
# walls and both Sage walls run W1R where they support F1 (A-601), and W1R stands a
# further 5/8" out than W1 on the exterior Type X of UL U305.
SIDE_WALL_TYPE = 'W1R'
# (name, framing dimension to its line, the minimum that line holds it to). The parcel
# walls are read from the buildings, not typed; the Sage walls are at the side street
# building line C.C. 3332.22(a)(1) sets, which SAFF_WALL_X already is.
SIDE_WALLS = [("BUILDING 1 ADJACENT-PARCEL WALL", LOT_W-(_B1[0]+_B1[2]), SIDE_MIN),
              ("BUILDING 2 ADJACENT-PARCEL WALL", LOT_W-(_B2[0]+_B2[2]), SIDE_MIN),
              ("BUILDING 1 SAGE WALL",         _B1[0],                SIDE_MIN),
              ("BUILDING 2 SAGE WALL",         _B2[0],                SIDE_MIN)]
SIDE_PARCEL = LOT_W-(_B1[0]+_B1[2])          # the interior side yard the zoning table prints
SIDE_COMB   = SIDE_PARCEL+SAFF_WALL_X        # both side yards
SIDE_BUILD_OUT = envelope.build_out(SIDE_WALL_TYPE)
SIDE_FACE   = rco_fsd.face_distance(SIDE_PARCEL, SIDE_BUILD_OUT)


def check_setbacks():
    """Every wall held to a side lot line, at the face RCO 202 and a zoning yard are
       both measured to. Prints the framing dimension C-101 draws, what the wall stands
       outside it, and what is left — the construction tolerance the wall has."""
    print("SIDE YARDS  (dimensioned to face of stud, G-001 note 5; measured to %s;" % rco_fsd.FACE)
    print("            held to %s, %s, not to a zoning yard):" % (fmt(SIDE_MIN), rco_fsd.SECTION))
    for name, framing, minimum in SIDE_WALLS:
        face = rco_fsd.face_distance(framing, SIDE_BUILD_OUT)
        print("   %-34s %-9s framing  %-9s at the wall face  %s over the %s minimum"
              % (name, fmt(framing), fmt(face), inches(face-minimum), fmt(minimum)))
    bad = rco_fsd.wall_violations([(n, d, SIDE_BUILD_OUT) for n, d, _m in SIDE_WALLS], SIDE_MIN)
    assert not bad, "side yards, at the wall face:\n  " + "\n  ".join(bad)
    assert SIDE_COMB >= SIDE_COMB_MIN-1e-9, \
        "the combined side yards are %s, under the %s minimum" % (fmt(SIDE_COMB), fmt(SIDE_COMB_MIN))


# C.C. 3332.355(B)(3)(b): an ADU no taller than the principal dwelling, or 25 feet; C.C.
# 3332.29: 35 feet in R-4. Height as C.C. 3303.08 measures a pitched roof, the mean of
# the eave and the point of the gable, read through the raised heel (levels.height).
ADU_HEIGHT_MAX   = 25.0
R4_HEIGHT_MAX    = 35.0
ADU_HEIGHT       = levels.height(B2_W)
PRINCIPAL_HEIGHT = levels.height(B1_W)


def check_height():
    """The ADU against 25'-0" and the principal dwelling, Building 1 against 35'-0"."""
    assert ADU_HEIGHT <= ADU_HEIGHT_MAX+1e-9, "Building 2 is %s high, over the %s of C.C. 3332.355" % (fmt(ADU_HEIGHT), fmt(ADU_HEIGHT_MAX))
    assert ADU_HEIGHT <= PRINCIPAL_HEIGHT+1e-9, "Building 2 is %s high, over the principal dwelling's %s" % (fmt(ADU_HEIGHT), fmt(PRINCIPAL_HEIGHT))
    assert PRINCIPAL_HEIGHT < R4_HEIGHT_MAX, "Building 1 is %s high, over the %s of C.C. 3332.29" % (fmt(PRINCIPAL_HEIGHT), fmt(R4_HEIGHT_MAX))
    print("ZONING HEIGHT, C.C. 3303.08: eave +%s; Building 1 ridge +%s, height +%s; Building 2 ridge +%s, height +%s (%s max)"
          % (fmt(levels.EAVE), fmt(levels.ridge(B1_W)), fmt(PRINCIPAL_HEIGHT), fmt(levels.ridge(B2_W)), fmt(ADU_HEIGHT), fmt(ADU_HEIGHT_MAX)))

# ---------------- the RCO 302.1 imaginary line in the courtyard ----------------
# Building 1's rear wall and Building 2's courtyard face, read off the site bands rather
# than typed again, and the Unit 3 stoop's far edge — the only thing of Building 1's that
# stands past that wall. src/fsd.py holds the line itself and Table 302.1(1).
B1_REAR_Y  = _B1[1]+_B1[3]                   # site y 68.0
B2_COURT_Y = _B2[1]                          # site y 80.0
U3_STOOP_Y1 = _B1[1]+U3_STOOP_HI             # the stoop's far edge, out in the courtyard
FSD_LINE_Y = fsd.line_y(B1_REAR_Y)           # where C-101 draws it
L2_STOREY  = levels.ROOF_PLATE-levels.FF2    # 9'-0", finished Level 2 floor to roof plate
REAR_OPEN_PCT = fsd.rear_open_ratio(B1_W, L2_STOREY)


def check_fsd():
    """The courtyard against RCO 302.1 and its table: where the line stands, what that
       rates on each face, and that nothing of Building 1's reaches it."""
    # src.downspouts reaches back here through grading and drainage, so it is imported
    # at call time rather than at module scope. check_fsd() runs from check_model(),
    # long after every module is loaded.
    from src.downspouts import DOWNSPOUTS, LEADER_D
    leaders = [(d.mark, LEADER_D) for d in DOWNSPOUTS
               if d.face.building == 'BUILDING 1' and abs(d.face.at-B1_REAR_Y) < 1e-9]
    rear_rake = ROOF.rake(ROOF.B1_ROOF, 'REAR')
    rear_vent = ROOF.gable_vented(ROOF.B1_ROOF, 'REAR')
    bad = fsd.fsd_violations(B1_REAR_Y, B2_COURT_Y, B1_W, L2_STOREY, rear_rake, U3_STOOP_Y1,
                             leaders=leaders, rear_gable_vent=rear_vent)
    edges = roof_edges()
    bad += rco_fsd.edge_violations(edges)
    print("RCO 302.1 IMAGINARY LINE — %s COURTYARD, LINE %s OFF BUILDING 1 AND %s OFF BUILDING 2, AT SITE %s"
          % (fmt(fsd.GAP), fmt(fsd.OFF_B1), fmt(fsd.OFF_B2), fmt(FSD_LINE_Y)))
    print("   BUILDING 1 REAR WALL   FSD %-8s WALL %-8s OPENINGS %g SF / %g SF = %.1f%% (%.0f%% MAX), EACH STORY"
          % (fmt(fsd.OFF_B1), rco_fsd.wall_rating(fsd.OFF_B1), fsd.REAR_OPEN_SF,
             fsd.rear_wall_sf(B1_W, L2_STOREY), 100*REAR_OPEN_PCT, 100*rco_fsd.opening_max(fsd.OFF_B1)))
    print("   BUILDING 2 COURTYARD   FSD %-8s WALL %-8s OPENINGS UNLIMITED" % (fmt(fsd.OFF_B2), rco_fsd.wall_rating(fsd.OFF_B2)))
    print("   UNIT 5 STAIR           %s TO THE LINE, %s REQUIRED; UNDERSIDE %s"
          % (fmt(fsd.U5_CLEAR), fmt(rco_fsd.PROJ_FREE), rco_fsd.projection_rating(fsd.U5_CLEAR)))
    print("   REAR RAKE              PROJECTS %s, %s TO THE LINE; UNDERSIDE %s"
          % (inches(rear_rake), fmt(fsd.OFF_B1-rear_rake),
             rco_fsd.underside(fsd.OFF_B1-rear_rake, rco_fsd.RAKE, gable_vent=rear_vent)))
    for mark, d in leaders:
        print("   %-22s PROJECTS %s OFF THAT WALL, %s TO THE LINE; A CONDUCTOR, NOT A PROJECTION WITH AN UNDERSIDE"
              % (mark, inches(d), fmt(fsd.OFF_B1-d)))
    print("   UNIT 3 STOOP           REACHES SITE %s, %s SHORT OF THE LINE; A SLAB ON GRADE IS NOT A PROJECTION"
          % (fmt(U3_STOOP_Y1), fmt(FSD_LINE_Y-U3_STOOP_Y1)))
    print("ROOF EDGES, RCO TABLE 302.1(1) — OVERHANG TO THE OUTSIDE OF THE TRIM, WHAT IT LEAVES, ITS UNDERSIDE")
    for name, kind, wall, over, blocked, vent in edges:
        left = "STREET SIDE, RCO 202" if wall is None else "%s TO %s" % (fmt(wall-over), EDGE_LINE[name])
        rating = "NONE" if wall is None else rco_fsd.underside(wall-over, kind, blocked, vent)
        print("   %-36s %-6s %-5s %-44s %s" % (name, inches(over), kind, left, rating))
    assert not bad, "RCO 302.1 imaginary line:\n  " + "\n  ".join(bad)


# What each edge's distance is measured to, for the printout. The walls' own distances
# are read from the site: the parcel line at LOT_W, the alley line at SITE_D, the line.
EDGE_LINE = {}


def roof_edges():
    """Every eave and rake of both buildings, as fsd.edge_violations() takes them."""
    out = []
    for r, (x0, y0, w, d) in ((ROOF.B1_ROOF, _B1[:4]), (ROOF.B2_ROOF, _B2[:4])):
        b = r.name
        rows = [("%s SAGE EAVE" % b, rco_fsd.EAVE, None, ROOF.EAVE_OVERHANG, None, "SAGE"),
                ("%s ADJACENT-PARCEL EAVE" % b, rco_fsd.EAVE, LOT_W-(x0+w), ROOF.EAVE_OVERHANG, None, "THE LOT LINE")]
        for gy, g in r.gables:
            if b == "BUILDING 1" and gy < 1e-9:
                rows.append(("%s S ELM RAKE" % b, rco_fsd.RAKE, None, ROOF.rake(r, g), g, "S ELM"))
            elif b == "BUILDING 1":
                rows.append(("%s REAR RAKE" % b, rco_fsd.RAKE, fsd.OFF_B1, ROOF.rake(r, g), g, "THE IMAGINARY LINE"))
            elif gy < 1e-9:
                rows.append(("%s COURTYARD RAKE" % b, rco_fsd.RAKE, fsd.OFF_B2, ROOF.rake(r, g), g, "THE IMAGINARY LINE"))
            else:
                rows.append(("%s ALLEY RAKE" % b, rco_fsd.RAKE, SITE_D-(y0+d), ROOF.rake(r, g), g, "THE LOT LINE"))
        for name, kind, wall, over, g, line in rows:
            EDGE_LINE[name] = line
            vent = ROOF.gable_vented(r, g) if g else True
            out.append((name, kind, wall, over, ROOF.EAVE_FIREBLOCKED if kind == rco_fsd.EAVE else False, vent))
    return out

B1_SITE     = lambda v: 34.0-v
SITE_LIVE_X = B1_SITE(26.0)                  # the face the Unit 3 stair is on
SITE_STAIR  = sorted((SITE_LIVE_X, SITE_LIVE_X-U3_STAIR_W))
SITE_WALK   = 4.0                            # new public sidewalk, in the right-of-way
SAN_X, SAN_CROSS, SAN_MAIN_Y = 1.0, 77.0, 126.6      # building sewer, and the alley main
VISION      = 10.0                           # clear vision triangle leg at the alley, C.C. 3321.05(B)(1)
VISION_ST   = ZONING.VISION_TRIANGLE_ST       # and at the S Elm / Sage street corner, C.C. 3321.05(B)(2)
# Building 1 stands at the 20'-0" front building line and the 8'-0" side street line, so
# its S Elm / Sage corner is at x+y = 28 and the 30'-0" triangle's hypotenuse,
# x+y = 30, passes 2'-0" inside it along each right-of-way. What stays clear of the
# building is the triangle through the corner; the encroachment is the right triangle
# between the two hypotenuses, VISION_ST_IN on a side. Request 7, the designer's call, 2026-09-14.
VISION_ST_CLR  = min(VISION_ST, _B1[0]+_B1[1])       # 28'-0", the triangle clear of Building 1
VISION_ST_IN   = VISION_ST-VISION_ST_CLR             # 2'-0" along each right-of-way
VISION_ST_AREA = 0.5*VISION_ST_IN*VISION_ST_IN       # 2 SF of footprint in the triangle
TREE_X, TREE_Y, TREE_R = SITE_W-9.5, 10.0, 2.6   # the one tree, C.C. 3321.07, and its canopy
# Three stalls, not four, and the pad 10'-0" off the Sage line — the designer's call,
# 2026-09-14. Four 9'-0" stalls in a 40'-0" lot stood 2'-0" off that line, inside the
# 8'-0" parking setback of C.C. 3312.27 and the 10'-0" clear vision triangle of
# 3321.05(B)(1), and each was a variance request. Three stand at PARK_X0 = VISION, clear
# of both, with 3'-0" left to the adjacent-parcel line.
PARK_X0, PARK_PITCH, PARK_Y0, PARK_Y1 = 10.0, 9.0, 108.0, 126.0
PARK_N = 3                                   # stalls
PARK_D = ZONING.STALL_D                      # the stall depth C.C. 3312.49 counts
PARK_X1 = PARK_X0+PARK_N*PARK_PITCH          # the pad's adjacent-parcel edge

# ---------------- the alley, and what the pad owes it ----------------
# The public alley at the rear is a 17'-6" right-of-way, lot line to far line — the whole
# right-of-way, not the pavement, which is what C.C. 3312.25 measures maneuvering in.
# Typed: it is the plat's figure, measured on the county GIS by the designer on 2026-09-14 at
# zoning's request, and nothing in the model can derive it. The set first carried it as
# 17'-0"; the designer corrected it to 17'-6" on 2026-09-16, making the request 2'-6", not 3'-0".
ALLEY_W  = 17.5
MANEUVER = ZONING.MANEUVER_MIN                # C.C. 3312.25, into a 90-degree stall
# What the alley cannot give, the lot would have to: zoning's reading (2026-09-14) is
# that the pad head is set back from the rear lot line by the shortfall, paved, so the
# aisle is 20'-0" between the far right-of-way line and the head of the stall. Here the
# pad head is Building 2's rear wall, so the 2'-6" is variance request 6 instead — the designer's
# decision, 2026-09-14 — and MANEUVER_HAVE is the figure the request states.
MANEUVER_SHORT = MANEUVER-ALLEY_W
MANEUVER_HAVE  = ALLEY_W+(PARK_Y1-PARK_Y0)-PARK_D    # the alley plus whatever the pad gives past 18'-0"

# ---------------- the parking setback and the alley vision triangle ----------------
# The pad stands PARK_X0 off the Sage line — the north lot line — where C.C. 3312.27
# puts the parking setback line at the 8'-0" side street building line, and the 10'-0"
# triangle of C.C. 3321.05(B)(1) at the Sage / alley corner reaches to x = 10. What
# stays clear of the pad is the triangle whose hypotenuse passes through the pad's corner
# nearest the lot corner, (PARK_X0, PARK_Y1): legs of PARK_X0 + (SITE_D - PARK_Y1). Both
# figures are read from the pad and tabulated; check_site_clearances() holds that each
# is a variance request exactly when the pad makes it one.
PARK_SETBACK_REQ = SAFF_WALL_X               # C.C. 3312.27, the side street building line
PARK_SETBACK     = PARK_X0                   # what the pad gives the Sage right-of-way
VISION_CLR       = min(VISION, PARK_X0+(SITE_D-PARK_Y1))   # the alley triangle the pad leaves
assert PARK_X1 <= SITE_W, "the parking pad runs past the adjacent-parcel line"

# ---------------- wheel stops ----------------
# One precast concrete stop in each stall, centred on it — the designer's choice, 2026-09-15, of
# the two placements in docs/superpowers/specs/2026-09-15-c101-wheel-stops-design.md. The
# figures are C.C. 3312.45's: 5" high at least, and 2'-6" at least from a building, read
# to the device's near face. Three stalls are not a "parking lot" under C.C. 3303.16, so
# the section does not bind; the set adopts it. The stalls keep the full PARK_D from the
# rear face to the alley line, so a car's front overhang still reaches about to the wall:
# the stops keep wheels off the wall and its footing, and each Unit 4 bedroom's escape
# opening, RCO R310.1, is its W-A on a side wall, which no stall stands in front of.
WSTOP_L, WSTOP_W, WSTOP_H = 6.0, IN(6), IN(5)     # length, base as drawn, height
WSTOP_H_MIN, WSTOP_SET = IN(5), 2.5               # C.C. 3312.45
B2_REAR_Y = B2_Y0+B2_D                            # Building 2's rear face, the head of every stall
WHEEL_STOPS = [(PARK_X0+(_i+0.5)*PARK_PITCH-WSTOP_L/2.0, B2_REAR_Y+WSTOP_SET,
                PARK_X0+(_i+0.5)*PARK_PITCH+WSTOP_L/2.0, B2_REAR_Y+WSTOP_SET+WSTOP_W)
               for _i in range(PARK_N)]          # (x0, y0, x1, y1), site feet, stall order

def b2_openings():
    """Building 2's windows in site feet, as (room, mark, wall, s0, s1): s0..s1 is the span
       along the wall — site x on the rear and courtyard faces, site y on the sides. The
       rooms are classified as u45_glazing() does; the sheet mirror puts plan x 0 on the
       adjacent-parcel side."""
    col = PLAN_B2.x(X_COL0, 20.0)
    out = []
    for w in B2win:
        x, y = PLAN_B2.x(w[0], w[1]), PLAN_B2.y(w[1])
        if y < U45_BEARING_WALL[1]: room = "LIVING"
        elif w[3] == 'h' and w[4] == "B": room = "BATH"
        else: room = "BEDROOM 1" if x < col else "BEDROOM 2"
        if w[3] == 'h':
            wall = "REAR" if y > B2_D/2.0 else "COURTYARD"
            s0, s1 = B2_X0+B2_W-(x+w[2]), B2_X0+B2_W-x
        else:
            wall = "ADJACENT-PARCEL" if x < B2_W/2.0 else "SAGE"
            s0, s1 = B2_Y0+y, B2_Y0+y+w[2]
        out.append((room, w[4], wall, s0, s1))
    return out

def check_wheel_stops():
    """Each stop inside its stall, its near face WSTOP_SET off Building 2's rear face, at
       least C.C. 3312.45's height; the pad still PARK_D deep; and each Unit 4 bedroom with
       a side-wall W-A that ends short of the pad. Prints each stall with the rear opening
       over it."""
    assert abs(PARK_Y0-B2_REAR_Y) < 1e-9, "the parking pad no longer starts at Building 2's rear face"
    assert PARK_Y1-PARK_Y0 >= PARK_D-1e-9, "the wheel stops' stalls are short of %s to the alley line" % fmt(PARK_D)
    assert WSTOP_H >= WSTOP_H_MIN-1e-9, "the wheel stops are under the %s of C.C. 3312.45" % inches(WSTOP_H_MIN)
    assert len(WHEEL_STOPS) == PARK_N, "a stall has no wheel stop"
    opens = b2_openings()
    print("WHEEL STOPS, C.C. 3312.45: %d x %s LONG, %s HIGH MIN, %s OFF BUILDING 2'S REAR WALL; STALLS %s TO THE ALLEY LINE"
          % (len(WHEEL_STOPS), fmt(WSTOP_L), inches(WSTOP_H), fmt(WSTOP_SET), fmt(PARK_Y1-PARK_Y0)))
    for i, (x0, y0, x1, y1) in enumerate(WHEEL_STOPS):
        a, b = PARK_X0+i*PARK_PITCH, PARK_X0+(i+1)*PARK_PITCH
        assert a-1e-9 <= x0 and x1 <= b+1e-9 and PARK_Y0 <= y0 and y1 <= PARK_Y1, "wheel stop %d leaves its stall" % (i+1)
        assert y0-B2_REAR_Y >= WSTOP_SET-1e-9, "wheel stop %d is inside %s of Building 2" % (i+1, fmt(WSTOP_SET))
        over = [o for o in opens if o[2] == "REAR" and o[3] < b and a < o[4]]
        print("   STALL %d   STOP %s .. %s, %s OFF THE WALL;  REAR OPENING OVER IT: %s"
              % (i+1, fmt(x0), fmt(x1), fmt(y0-B2_REAR_Y), ", ".join("%s W-%s" % (o[0], o[1]) for o in over) or "NONE"))
    for bed in ("BEDROOM 1", "BEDROOM 2"):
        side = [o for o in opens if o[0] == bed and o[1] == "A" and o[2] in ("SAGE", "ADJACENT-PARCEL")
                and o[4] <= PARK_Y0+1e-9]
        assert side, "Unit 4 %s has no side-wall W-A short of the pad: its escape opening faces a stall" % bed
        print("   UNIT 4 %s ESCAPE OPENING, RCO 310.1: W-A ON THE %s WALL, %s .. %s, %s SHORT OF THE PAD"
              % (bed, side[0][2], fmt(side[0][3]), fmt(side[0][4]), fmt(PARK_Y0-side[0][4])))

# ---------------- every variance, in the order the sheets number them ----------------
# G-001's table, C-101 and C-102's relief block and G-001 note 15 all state the count,
# and they stated it separately: a fourth request added to one of them would have left
# the others saying three. One list, its length, and the word for it.
VARIANCES = [("C.C. 3332.05","Lot width"),
             ("C.C. 3312.49","Parking"),
             ("C.C. 3332.22(a)(1)","Side street yard"),
             ("C.C. 3312.25","Maneuvering"),
             ("C.C. 3321.05(B)(2)","Street vision triangle")]
N_VARIANCES   = len(VARIANCES)
NUM_WORD      = {1:"ONE",2:"TWO",3:"THREE",4:"FOUR",5:"FIVE",6:"SIX",7:"SEVEN"}
VARIANCE_WORD = NUM_WORD[N_VARIANCES]
# A note that says "request 4" reads the number from here, so a request that leaves the
# list — the two the three-stall pad retired — cannot leave a stale number on a sheet.
REQ_NO  = {s: i+1 for i,(s,_n) in enumerate(VARIANCES)}
ORDINAL = {1:"FIRST",2:"SECOND",3:"THIRD",4:"FOURTH",5:"FIFTH",6:"SIXTH",7:"SEVENTH"}

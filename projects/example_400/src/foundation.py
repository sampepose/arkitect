"""The foundations of both buildings, as S-101 draws them.

Both buildings are slab on grade inside a CONCRETE FOUNDATION WALL on a CONTINUOUS
TRENCH FOOTING bearing below the frost line: a 16" x 8" footing with its bottom 32"
below finished grade — Columbus CIC-09, the depth RCO 403.1.4.1 asks for — an 8"
poured wall on it, and the 4" slab poured inside the wall. Not a frost-protected
shallow foundation; the set carried one for a day and it was taken out on purpose.

Slab-edge insulation is the energy code's, not frost protection: R-10 for 2'-0" on the
INTERIOR face of the wall, from slab top down, so nothing is exposed and nothing bears
on it. Insulation is a material, checked at its nominal value against the code.

Coordinates: FINAL SHEET x (the plans' left edge, the 396 Oak side) and plan y, in feet,
as A-101 and A-102 draw the buildings. Nothing here is mirrored.

400 Oak: the design basis, the sizes, the concrete and the termite protection are 300 S
Elm's, unchanged -- same city, same code. The two buildings below are Oak's.
"""
from arkitect.codes.ohio.columbus import criteria as JUR_CRIT
from collections import namedtuple
from arkitect.lib.units import IN, fmt
from src import levels
from math import pi
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.codes.ohio.columbus import criteria
from src.building1 import B1_W, B1_D, D_REAR_W, ENTRY_X, REAR_DOOR_X, STAIR_WALL
from src.building2 import (B2_W, B2_D, U45_BEARING_WALL, U5_DOOR_X0, U5_STOOP_X0, U5_FLIGHT_X0,
                           U5_LAND_D, U5_LAND_LEN, U5_LAND_X0, U5_LAND_X1, U5_RUN, U5_STAIR_W)

# ---------------- design basis ----------------
FROST_DEPTH = IN(JUR_CRIT.FROST_DEPTH)   # bottom of footing below finished grade: the jurisdiction's (CIC-09, RCO R403.1.4.1)
FTG_W, FTG_T = IN(16), IN(8)  # continuous footing; Table R403.1(1) asks 12" for two storeys at 1,500 psf
WALL_T = IN(8)                # poured concrete foundation wall, RCO R404
FTG_PROJ = (FTG_W-WALL_T)/2.0 # the footing's projection past each face of the wall

# Slab-edge insulation, RCO Table 1102.1.2, climate zone 5: R-10 for 2 ft. Extruded
# polystyrene, ASTM C578 Type IV, 2 inches at the product's nominal 5.0 per inch, on
# the interior face of the wall from slab top down the run.
INSUL_NAME   = "XPS, ASTM C578 TYPE IV"
INSUL_T      = IN(2)
INSUL_R_NOM  = 5.0 * 2
ENERGY_R     = 10
EDGE_INSUL_RUN = 2.0

# ---------------- sizes ----------------
# The footing's two continuous bottom bars, and the cover a bar -- or anything else cast
# into concrete placed against earth -- takes to the earth below it. THE ONE DEFINITION:
# S-101's notes 1 and 4, its wall detail's label and P-601's service-entry section all
# print these, and the section's deepened footing is measured from them.
FTG_BAR  = "#4"
FTG_BAR_DIA = IN(0.5)
BAR_COVER = IN(3)
STRIP_W = IN(16)      # interior bearing strip, thickened in the slab
STRIP_D = IN(12)
SLAB_T  = IN(4)       # A-601 S1
GRAVEL_T = IN(4)      # A-601 S1, the clean aggregate under the vapour retarder
RETARDER_MIL = 10     # A-601 S1, the polyethylene vapour retarder on the aggregate
PAD_T   = IN(6)       # landings and stoops, floating
PAD_EDGE = IN(12)     # their thickened edge
LANDING = 3.0         # a landing pad is 3'-0" along its face and out
                      # THE ONE DEFINITION. src/grading.py imports it rather than
                      # repeating it: the pad S-101 draws and the rectangle C-103 grades
                      # are the same piece of concrete, and while each module typed its
                      # own 3.0 the two could be moved apart without a word -- grading
                      # at 3'-6" against foundation at 3'-0" built clean, and the
                      # one-step-off-the-landing check then ran against the wrong edge.


# ---------------- termites ----------------
# RCO Table 301.2(1) for Columbus reads MODERATE TO HEAVY, on the scale of Figure
# 301.2(7). 318.1 then requires protection by one or a combination of its six methods;
# this set uses item 1, chemical termiticide treatment, as soil treatment per 318.2
# (Ohio deletes 318.1.2 field treatment). 318.4's bar on foam plastic below grade binds
# only where the figure reads VERY HEAVY, and the slab-edge XPS runs below grade.
TERMITE_SCALE = ("NONE TO SLIGHT", "SLIGHT TO MODERATE", "MODERATE TO HEAVY", "VERY HEAVY")
TERMITE = "MODERATE TO HEAVY"
TERMITE_METHODS = {1: "CHEMICAL TERMITICIDE TREATMENT, 318.2",
                   2: "TERMITE-BAITING SYSTEM, PER THE LABEL",
                   3: "PRESSURE-PRESERVATIVE-TREATED WOOD, 317.1",
                   4: "NATURALLY DURABLE TERMITE-RESISTANT WOOD",
                   5: "PHYSICAL BARRIERS, 318.3",
                   6: "COLD-FORMED STEEL FRAMING"}
TERMITE_METHOD = 1
TERMITE_TREATMENT = "SOIL TREATMENT"

def check_termite():
    assert TERMITE in TERMITE_SCALE, "termite entry %r is not on the Figure 301.2(7) scale" % (TERMITE,)
    if TERMITE != TERMITE_SCALE[0]:
        assert TERMITE_METHOD in TERMITE_METHODS, (
            "Table 301.2(1) reads %s and no RCO 318.1 method is named" % TERMITE)
    if TERMITE == "VERY HEAVY":
        assert levels.SLAB_TOP - EDGE_INSUL_RUN >= levels.GRADE - 1e-9, (
            "RCO 318.4: %s runs %s below grade where termite infestation is very heavy"
            % (INSUL_NAME, fmt(levels.GRADE - (levels.SLAB_TOP - EDGE_INSUL_RUN))))

def check_basis():
    assert INSUL_R_NOM >= ENERGY_R - 1e-9, (
        "insulation gives R-%.1f nominal against the R-%d of Table 1102.1.2" % (INSUL_R_NOM, ENERGY_R))
    assert FTG_W >= IN(12) - 1e-9, "footing narrower than Table 403.1(1)'s 12 inches"
    assert FTG_PROJ >= 0.0, "the footing is narrower than the wall on it"
    assert FROST_DEPTH >= IN(32) - 1e-9, "footing bottom above Columbus's 32-inch frost line"
    assert EDGE_INSUL_RUN <= FROST_DEPTH + levels.SLAB_TOP - FTG_T + 1e-9, (
        "the slab-edge insulation runs below the top of the footing")
    check_termite()


# concrete, RCO Table R402.2: shared, see arkitect/codes/ohio/rco/concrete.py
from arkitect.codes.ohio.rco.concrete import (Concrete, INTERIOR_SLAB, NOT_EXPOSED, PORCH_STEPS, VERTICAL_EXPOSED,
                                     psi, table_violations)


# ---------------- what this set specifies ----------------
# The weathering potential of Table R301.2(1), which G-001's design criteria print.
WEATHERING = "SEVERE"
# What the set specifies, S-101's concrete schedule: each element on its table row with
# its strength and air — "AE" always air-entrained, "c" only where footnote c applies.
# The footings take the walls' mix, above the table's 2,500; the walks, pad and C-103's
# gutters take the porch-and-steps row with the stoops and landings.
FOOTINGS = Concrete("FOOTINGS", NOT_EXPOSED, 3000, "AE")
WALLS    = Concrete("FOUNDATION WALLS", VERTICAL_EXPOSED, 3000, "AE")
SLAB     = Concrete("SLAB AND BEARING STRIPS", INTERIOR_SLAB, 3000, "c")
FLATWORK = Concrete("STOOPS, LANDINGS, WALKS, PARKING PAD", PORCH_STEPS, 3500, "AE")
# Every kind of site concrete FLATWORK's row covers. src/grading.py holds its own paving
# and gutters to this list, so a new kind of paved rectangle cannot reach the lot without
# a strength. CB-1's grate and frame and the precast wheel stops are products, not site
# concrete poured to this schedule, and are not in it.
FLATWORK_KINDS = ("landing", "stoop", "walk", "pad", "gutter")
CONCRETE = (FOOTINGS, WALLS, SLAB, FLATWORK)


def concrete_violations(concrete=CONCRETE, weathering=WEATHERING):
    """Each element at or above its Table 402.2 cell for the weathering potential,
       air-entrained wherever the cell carries footnote d, footnote c carried wherever
       the cell does, and the foundation wall on the exposed row while it stands above
       finished grade."""
    return table_violations(concrete, weathering, WALLS.element, levels.SLAB_TOP-levels.GRADE)


def check_concrete():
    print("CONCRETE — TABLE 402.2, %s WEATHERING: %s" % (WEATHERING, "; ".join(
        "%s %s%s" % (e.element, psi(e.psi), {"AE": " AIR-ENTRAINED", "c": " (c)"}[e.air]) for e in CONCRETE)))
    bad = concrete_violations()
    assert not bad, "concrete: %s" % bad


# ---------------- the two buildings ----------------
Building = namedtuple("Building", "name W D strips pads piers")
# piers: (x, y, diameter, mark), feet, the pier's centre; round, bottom at FROST_DEPTH.
# strips and pads: (x0, y0, x1, y1, label), feet, final sheet x / plan y.

def _strip_h(cy, W, label):
    return (0.0, cy-STRIP_W/2.0, W, cy+STRIP_W/2.0, label)

def _strip_v(cx, y0, y1, label):
    return (cx-STRIP_W/2.0, y0, cx+STRIP_W/2.0, y1, label)

# Building 1, the house: the perimeter, and a strip under the stair wall, which carries the
# trimmer at the Level 2 well; the Level 2 floor spans side wall to side wall (building1's
# STAIR_WALL says so). Its one pad is the landing at the entry. Pads are floating slabs,
# isolated from the building by an expansion joint.
_sw_x0, _sw_y0, _sw_x1, _sw_y1 = STAIR_WALL
B1 = Building("BUILDING 1", B1_W, B1_D,
              strips=[_strip_v((_sw_x0+_sw_x1)/2.0, _sw_y0, _sw_y1, "UNIT 1 STAIR WALL")],
              pads=[(ENTRY_X, -LANDING, ENTRY_X+LANDING, 0.0, "UNIT 1 LANDING"),
                    # the back door's, RCO 311.3: 3'-0" wide, centered on the 2'-8" door
                    (REAR_DOOR_X+D_REAR_W/2.0-LANDING/2.0, B1_D, REAR_DOOR_X+D_REAR_W/2.0+LANDING/2.0, B1_D+LANDING,
                     "UNIT 1 REAR LANDING")],
              piers=[])

# Building 2. Its floor is two F1 joist bays spanning courtyard to rear and meeting on
# the bearing wall between the living space and the middle band, which building2 derives
# from its joist plan; the strip runs the full width. Unit 2's landing is under the Unit 3
# stair's top landing, at the door; the stair's stoop is at the foot of its flight.
_uw_x0, _uw_y0, _uw_x1, _uw_y1 = U45_BEARING_WALL
B2 = Building("BUILDING 2", B2_W, B2_D,
              strips=[_strip_h((_uw_y0+_uw_y1)/2.0, B2_W, "UNITS 2 AND 3 BEARING WALL")],
              pads=[(U5_DOOR_X0, -U5_LAND_D, U5_DOOR_X0+LANDING, 0.0, "UNIT 2 LANDING"),   # as deep as the top landing over it, to meet the courtyard walk
                    (U5_STOOP_X0, -U5_LAND_D, U5_FLIGHT_X0, 0.0, "UNIT 3 STOOP")],
              piers=None)                                  # set below, from the stair

# The Unit 3 stair's piers. The top landing's inner edge is ledgered to Building 2's
# courtyard wall; its outer corners stand on posts (P1 at the flight, P2 at the far end),
# and the foot of each stringer on its own pier (P3 outer, P4 at the wall), clear of the
# floating stoop. Each post is centred POST_IN inside the stair's edges. The stoop and
# Unit 2's landing pad are poured around them with an isolation joint.
PIER_DIA = IN(12)
POST_IN = IN(3)
B2 = B2._replace(piers=[
    (U5_LAND_X0+POST_IN, -U5_LAND_D+POST_IN, PIER_DIA, "P1"),
    (U5_LAND_X1-POST_IN, -U5_LAND_D+POST_IN, PIER_DIA, "P2"),
    (U5_FLIGHT_X0+POST_IN, -U5_LAND_D+POST_IN, PIER_DIA, "P3"),
    (U5_FLIGHT_X0+POST_IN, -POST_IN-PIER_DIA/2.0, PIER_DIA, "P4")])

BUILDINGS = (B1, B2)


def check_foundation():
    """Every strip inside its building, every pad outside it and against one face, each
       bearing strip under the wall its plan draws, and the design basis consistent."""
    check_basis()
    f = lambda v: ("-"+fmt(-v)) if v < -1e-9 else fmt(v)      # fmt() has no sign of its own
    print("FOUNDATION — %s x %s FOOTING, BOTTOM %s BELOW GRADE (CIC-09), %s WALL; %s %s R-%d AT THE SLAB EDGE, %s RUN"
          % (fmt(FTG_W), fmt(FTG_T), fmt(FROST_DEPTH), fmt(WALL_T), fmt(INSUL_T), INSUL_NAME, int(INSUL_R_NOM), fmt(EDGE_INSUL_RUN)))
    check_concrete()
    print("TERMITE — TABLE 301.2(1) %s; RCO 318.1 ITEM %d, %s (%s); 318.4 FOAM BAR %s"
          % (TERMITE, TERMITE_METHOD, TERMITE_METHODS[TERMITE_METHOD], TERMITE_TREATMENT,
             "APPLIES" if TERMITE == "VERY HEAVY" else "NOT TRIGGERED"))
    bad = []
    for b in BUILDINGS:
        for x0, y0, x1, y1, nm in b.strips:
            inside = x0 >= -1e-9 and y0 >= -1e-9 and x1 <= b.W+1e-9 and y1 <= b.D+1e-9
            print("   %-10s strip %-18s x %s .. %s   y %s .. %s" % (b.name, nm, f(x0), f(x1), f(y0), f(y1)))
            if not inside: bad.append((b.name, nm, "strip runs outside the slab"))
        for x0, y0, x1, y1, nm in b.pads:
            against = (abs(x1) < 1e-9 or abs(x0-b.W) < 1e-9 or abs(y1) < 1e-9 or abs(y0-b.D) < 1e-9)
            print("   %-10s pad   %-18s x %s .. %s   y %s .. %s" % (b.name, nm, f(x0), f(x1), f(y0), f(y1)))
            if not against: bad.append((b.name, nm, "pad does not touch a face"))
    # A strip is centred on its wall and runs its length: a wall along y is matched on
    # x centre and y extent, a wall along x the other way about.
    for b, st, wall, nm in ((B1, B1.strips[0], STAIR_WALL, "UNIT 1 STAIR WALL"),
                            (B2, B2.strips[0], U45_BEARING_WALL, "UNITS 2 AND 3 BEARING WALL")):
        wx0, wy0, wx1, wy1 = wall
        if (wx1-wx0) < (wy1-wy0):
            under = (abs((st[0]+st[2])/2.0 - (wx0+wx1)/2.0) < 1e-9 and abs(st[1]-wy0) < 1e-9 and abs(st[3]-wy1) < 1e-9)
        else:
            under = (abs((st[1]+st[3])/2.0 - (wy0+wy1)/2.0) < 1e-9 and abs(st[0]-wx0) < 1e-9 and abs(st[2]-wx1) < 1e-9)
        if not under:
            bad.append((b.name, nm, "strip is not under the wall"))
    for x, y, d, mk in B2.piers:
        print("   %-10s pier  %-18s x %s   y %s   %s DIA." % (B2.name, mk, f(x), f(y), fmt(d)))
        if y+d/2.0 > 1e-9:
            bad.append((B2.name, mk, "pier is under the building"))
        if not (U5_STOOP_X0-1e-9 <= x <= U5_LAND_X1+1e-9 and -U5_LAND_D-1e-9 <= y <= 1e-9):
            bad.append((B2.name, mk, "pier is not under the Unit 3 stair"))
    assert not bad, "foundation: %s" % bad
    check_bearing()


# ---------------- bearing: each footing's pressure on the soil ----------------
# Line loads from the model's own spans, against criteria.SOIL_BEARING. Assumed loads,
# stated here and nowhere else: floors 10 dead + 40 live (RCO Table 301.5, habitable),
# the roof 15 dead + the ground snow, exterior stairs 10 dead + 40 live, exterior walls
# 12 psf and interior walls 8 psf of wall face, concrete 150 pcf. Roof trusses span side
# wall to side wall on both buildings with ROOF_OVERHANG each side (no roof is modelled
# for this lot yet); the house's Level 2 floor spans side to side (building1.STAIR_WALL),
# Building 2's floor front to back on its bearing wall (building2's joist bays).
FLOOR_PSF, ROOF_PSF, STAIR_PSF = 10+40, 15+criteria.GROUND_SNOW, 10+40
EXT_WALL_PSF, INT_WALL_PSF, CONC_PCF = 12.0, 8.0, 150.0
ROOF_OVERHANG = 1.0


def bearing():
    """[(footing, plf or lb, bearing width or area, psf)] for every footing, strip and pier."""
    ext_wall = EXT_WALL_PSF*(levels.EAVE-levels.SLAB_TOP)
    int_wall = INT_WALL_PSF*(levels.F1_PLATE-levels.FF1)
    fdn = CONC_PCF*WALL_T*(FROST_DEPTH-FTG_T+levels.SLAB_TOP) + CONC_PCF*FTG_W*FTG_T
    strip = CONC_PCF*STRIP_W*(STRIP_D-SLAB_T)
    roof = ROOF_PSF*(B1_W/2.0+ROOF_OVERHANG)
    clear1 = B1_W-2*EXT_STUD
    sw0, sw1 = STAIR_WALL[0]-EXT_STUD, B1_W-EXT_STUD-STAIR_WALL[2]      # spans either side
    bw = U45_BEARING_WALL
    front, rear = bw[1]-EXT_STUD, B2_D-EXT_STUD-bw[3]                    # Building 2's bays
    landing = U5_LAND_LEN*U5_LAND_D*STAIR_PSF
    flight = U5_RUN*U5_STAIR_W*STAIR_PSF
    lines = [
        ("B1 SIDE WALLS",     FLOOR_PSF*clear1/2.0+roof+ext_wall+fdn, FTG_W),
        ("B1 FRONT / REAR",   ext_wall+fdn, FTG_W),
        ("B1 STAIR WALL",     FLOOR_PSF*(sw0+sw1)/2.0+2*int_wall+strip, STRIP_W),
        ("B2 SIDE WALLS",     roof+ext_wall+fdn, FTG_W),
        ("B2 COURTYARD WALL", FLOOR_PSF*front/2.0+landing/2.0/U5_LAND_LEN+ext_wall+fdn, FTG_W),
        ("B2 REAR WALL",      FLOOR_PSF*rear/2.0+ext_wall+fdn, FTG_W),
        ("B2 BEARING WALL",   FLOOR_PSF*(front+rear)/2.0+2*int_wall+strip, STRIP_W),
    ]
    out = [(nm, plf, w, plf/w) for nm, plf, w in lines]
    area = pi*PIER_DIA**2/4.0
    own = CONC_PCF*area*FROST_DEPTH
    share = {"P1": landing/4.0+flight/4.0, "P2": landing/4.0, "P3": flight/4.0, "P4": flight/4.0}
    out += [("PIER "+mk, share[mk]+own, area, (share[mk]+own)/area) for _x, _y, _d, mk in B2.piers]
    return out


def check_bearing():
    rows = bearing()
    print("BEARING — %s PRESUMED; FLOORS %d, ROOF %d, STAIR %d PSF:" % (criteria.psf(criteria.SOIL_BEARING),
          FLOOR_PSF, ROOF_PSF, STAIR_PSF))
    for nm, load, w, q in rows:
        unit = "LB" if nm.startswith("PIER") else "PLF"
        print("   %-18s %6.0f %s   %4.0f PSF   %3.0f%%" % (nm, load, unit, q, 100.0*q/criteria.SOIL_BEARING))
    over = [nm for nm, _l, _w, q in rows if q > criteria.SOIL_BEARING+1e-9]
    assert not over, "footings over the %s soil: %s" % (criteria.psf(criteria.SOIL_BEARING), over)

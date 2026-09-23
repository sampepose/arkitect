"""The foundations of both buildings, as S-101 draws them.

Both buildings are slab on grade inside a CONCRETE FOUNDATION WALL on a CONTINUOUS
TRENCH FOOTING bearing below the frost line: a 16" x 8" footing with its bottom 32"
below finished grade — Columbus CIC-09, the depth RCO 403.1.4.1 asks for — an 8"
poured wall on it, and the 4" slab poured inside the wall. Not a frost-protected
shallow foundation; the set carried one for a day and it was taken out on purpose.

Slab-edge insulation is the energy code's, not frost protection: R-10 for 2'-0" on the
INTERIOR face of the wall, from slab top down, so nothing is exposed and nothing bears
on it. Insulation is a material, checked at its nominal value against the code.

Coordinates: FINAL SHEET x (from the Sage face) and plan y, in feet — the system
C-101 draws the pads in and Unit 1's study is authored in. Nothing here is mirrored.
"""
from collections import namedtuple
from arkitect.lib.units import IN, fmt
from src import levels
from src.mirror import B1_W
from src.building1 import (Y_SEP_TOP, Y_SEP_BOT, U1_STAIR_WALL, U23_BEARING_WALL, ENTRY_LEFT, PLAN_L1,
                           U2_ENTRY, U3_FLIGHT_HI, U3_STOOP_HI, U3_STAIR_W)
from src.building2 import B2_W, B2_D, U45_BEARING_WALL, U5_DOOR_X0, U5_STOOP_X0, U5_FLIGHT_X0, U5_LAND_D

# ---------------- design basis ----------------
FROST_DEPTH = IN(32)          # bottom of footing below finished grade: CIC-09, RCO R403.1.4.1
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
# S-101's note 1, its note 4, its wall detail's label and P-601's service-entry section
# all print these, and the section's deepened footing is measured from them.
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
LANDING = 3.0         # a landing pad is 3'-0" along its face and out, but Unit 4's; C-101 note 5a
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
FLATWORK = Concrete("STOOPS, LANDINGS, WALKS, PARKING PAD, GUTTERS", PORCH_STEPS, 3500, "AE")
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
Building = namedtuple("Building", "name W D strips pads")
# strips and pads: (x0, y0, x1, y1, label), feet, final sheet x / plan y.

def _strip_h(cy, W, label):
    return (0.0, cy-STRIP_W/2.0, W, cy+STRIP_W/2.0, label)

def _strip_v(cx, y0, y1, label):
    return (cx-STRIP_W/2.0, y0, cx+STRIP_W/2.0, y1, label)

# Building 1. W4 is two 1-hour walls, W4A and W4B (UL U305 each), on one strip — a shared
# foundation is RCO 302.2.6 exception 1 — drawn foundation to roof on
# A-301; the Units 2/3 floor bears on the wall its two F1 joist bays meet on, which
# building1 derives from the joist plan A-101 prints; Unit 1's stair wall carries the
# double trimmer at the well (A-101 note 3).
_w4_cy = (Y_SEP_TOP+Y_SEP_BOT)/2.0
_sw_x0, _sw_y0, _sw_x1, _sw_y1 = U1_STAIR_WALL
_bw_x0, _bw_y0, _bw_x1, _bw_y1 = U23_BEARING_WALL
# Pads are the rectangles C-101 draws, in sheet coordinates (site x - 8, site y - 20).
# Every pad is a floating slab, isolated from the building by an expansion joint; the
# stairs' stringers bear on their own frost-depth piers, S-101 note 5 and A-604 detail 4.
_u2_y = PLAN_L1.y(U2_ENTRY[1]) + U2_ENTRY[2]/2.0 - LANDING/2.0
B1 = Building("BUILDING 1", B1_W, 48.0,
              strips=[_strip_h(_w4_cy, B1_W, "W4"),
                      _strip_v((_sw_x0+_sw_x1)/2.0, _sw_y0, _sw_y1, "UNIT 1 STAIR WALL"),
                      _strip_v((_bw_x0+_bw_x1)/2.0, _bw_y0, _bw_y1, "UNITS 2 AND 3 BEARING WALL")],
              pads=[(ENTRY_LEFT, -LANDING, ENTRY_LEFT+LANDING, 0.0, "UNIT 1 LANDING"),
                    (-LANDING, _u2_y, 0.0, _u2_y+LANDING, "UNIT 2 LANDING"),
                    (-U3_STAIR_W, U3_FLIGHT_HI, 0.0, U3_STOOP_HI, "UNIT 3 STOOP")])

# Building 2. Its floor is two F1 joist bays spanning courtyard to rear and meeting on
# the bearing wall between the living space and the bedrooms, which building2 derives
# from its joist plan; the strip runs the full width like W4's. Site y - 80.
_uw_x0, _uw_y0, _uw_x1, _uw_y1 = U45_BEARING_WALL
B2 = Building("BUILDING 2", B2_W, B2_D,
              strips=[_strip_h((_uw_y0+_uw_y1)/2.0, B2_W, "UNITS 4 AND 5 BEARING WALL")],
              # Unit 4's landing runs out to the edge of the Unit 5 top landing over it, so
              # its step lands on the Units 4 and 5 walk beside the stair, not under it.
              pads=[(U5_DOOR_X0, -U5_LAND_D, U5_DOOR_X0+LANDING, 0.0, "UNIT 4 LANDING"),
                    (U5_STOOP_X0, -U5_LAND_D, U5_FLIGHT_X0, 0.0, "UNIT 5 STOOP")])

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
    for b, st, wall, nm in ((B1, B1.strips[1], U1_STAIR_WALL, "UNIT 1 STAIR WALL"),
                            (B1, B1.strips[2], U23_BEARING_WALL, "UNITS 2 AND 3 BEARING WALL"),
                            (B2, B2.strips[0], U45_BEARING_WALL, "UNITS 4 AND 5 BEARING WALL")):
        wx0, wy0, wx1, wy1 = wall
        if (wx1-wx0) < (wy1-wy0):
            under = (abs((st[0]+st[2])/2.0 - (wx0+wx1)/2.0) < 1e-9 and abs(st[1]-wy0) < 1e-9 and abs(st[3]-wy1) < 1e-9)
        else:
            under = (abs((st[1]+st[3])/2.0 - (wy0+wy1)/2.0) < 1e-9 and abs(st[0]-wx0) < 1e-9 and abs(st[2]-wx1) < 1e-9)
        if not under:
            bad.append((b.name, nm, "strip is not under the wall"))
    assert not bad, "foundation: %s" % bad

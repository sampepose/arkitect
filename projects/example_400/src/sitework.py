"""400 Oak Ave — the lot, what stands on it, and the zoning it answers to.

The site C-102 draws and tabulates, and the checks that hold it. It replaces the copy of
300 S Elm's sitework.py this project started from, which was a 40' corner lot on
Sage with five variance requests; that original stays in projects/example_300.

THE LOT. 30'-0" x 124'-0", an interior lot on Oak Avenue with a public alley at the
rear, split from Franklin County parcel 010-000400-00 (the designer, 2026-09-17, from the
Auditor's GIS). There is no survey yet; the figures are assumed until one is made
(the designer, 2026-09-18), and C-102 says so. The alley is 20'-0" (the designer, 2026-09-18: "20' in
reality"; the GIS scales 19.8'). R-4, H-35.

TRUE NORTH. The Oak and alley lot lines run about N 10 deg W, so the side lot lines
run toward Oak about 10 deg north of east (the designer, 2026-09-18, "roughly 80 degrees if 90
is north and 0 is west"). North is the 396 Oak side.

SITE COORDINATES, in feet: x across the lot from the north lot line (the 396 Oak side),
y from the Oak right-of-way line toward the alley. The plan sheets draw Oak at the top
with the north side on the LEFT, so a plan's page x is site x less the side yard, and a
plan's page y is site y less the building's front face.

From Oak to the alley: the 25'-0" front yard, Building 1 (the house), the courtyard,
Building 2 (the two stacked ADUs) and an 18'-0" parking pad against the alley. The
depth left after the three fixed ones is the courtyard's, so it is derived, never typed.
"""
from arkitect.codes.ohio.columbus import zoning as ZONING
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import IN, fmt
from src import fsd, levels
from arkitect.codes.ohio.rco import fire_separation as rco_fsd
from src.building1 import B1_STAIR, B1_W, B1_D, D_ENTRY, ENTRY_X, LEVEL, Y_FOOT_RISER, Y_REAR, Y_TOP_RISER
from src.openings import WIN_SF
from src.building2 import B2_W, B2_D, U5_DOOR_X0, U5_DOOR_X1, U5_LAND_D, U5_LAND_X1, U5_STOOP_X0

# ---------------- the lot ----------------
SITE_W, SITE_D = 30.0, 124.0          # assumed from the Auditor's GIS; no survey
ALLEY_W = 20.0                        # the public alley right-of-way
LOT_AREA = SITE_W*SITE_D
TRUE_NORTH = 10.0                     # degrees: true north is this far clockwise from
                                      # the Oak lot line, looking north along it
PARCEL = "010-000400-00"
NORTH_NEIGHBOUR = ("396 OAK AVE", "PARCEL 010-000396")
SOUTH_NEIGHBOUR = ("404 OAK AVE", "REMAINDER OF PARCEL %s" % PARCEL)

# ---------------- what stands on it ----------------
FRONT_YARD = 25.0                     # Oak right-of-way to Building 1's front face
SIDE_YARD  = 5.0                      # each side, both buildings

PARK_N     = 3                        # stalls (the designer, 2026-09-18)
PARK_PITCH = 9.0                      # stall width
PARK_D     = ZONING.STALL_D           # 18'-0"
PAD_D      = PARK_D                   # the pad, Building 2's rear wall to the alley line
# Against the north lot line, not centered: the 3'-0" left on the south is swale S-2's,
# Building 2's south yard having nowhere else to drain (src/grading.py, C-103).
PARK_X0    = 0.0
PARK_X1    = PARK_X0+PARK_N*PARK_PITCH
PARK_Y1    = SITE_D
PARK_Y0    = PARK_Y1-PAD_D

# (x, y, width, depth, name, label, dwelling type)
B1_X, B1_Y = SIDE_YARD, FRONT_YARD
B2_X, B2_Y = SIDE_YARD, PARK_Y0-B2_D
SITE_BLDG = [(B1_X, B1_Y, B1_W, B1_D, "BUILDING 1", "UNIT 1", "SINGLE-FAMILY DWELLING"),
             (B2_X, B2_Y, B2_W, B2_D, "BUILDING 2", "UNITS 2 AND 3", "TWO STACKED ADUs")]
COURT = B2_Y-(B1_Y+B1_D)              # between the buildings: 15'-0"

# Building 2's exterior stair on its courtyard face. A-102's page coordinates are site x
# less the side yard, as on A-101.
STAIR = (B2_X+U5_STOOP_X0, B2_Y-U5_LAND_D, B2_X+U5_LAND_X1, B2_Y)     # x0, y0, x1, y1
STAIR_AREA = (STAIR[2]-STAIR[0])*(STAIR[3]-STAIR[1])

# ---------------- walks: each dwelling to Oak Avenue ----------------
# Unit 1: straight in from Oak to its entry, the door's own width. The entry is read
# from the plan: regridded, then mirrored, then placed.
WALK_W = 3.0
WALK_T = IN(4)                        # walks, C-101 note 3
PARK_T = IN(6)                        # the parking pad, C-101 note 3
ENTRY_X0 = B1_X+ENTRY_X
WALK_U1 = (ENTRY_X0, 0.0, ENTRY_X0+D_ENTRY[2], B1_Y)
# Units 2 and 3: down the south side yard, then across the courtyard along the outer edge
# of the Unit 3 stair, from Unit 2's door under the landing to Unit 3's stoop.
# 1'-3" off the buildings: the lawn strip between falls to the walk, and at 1'-0" it banked
# past 3:1 at Building 1's front corner (src/grading.py).
WALK_SIDE = (SITE_W-SIDE_YARD+1.25, 0.0, SITE_W-SIDE_YARD+1.25+WALK_W, STAIR[1])
# From the parking pad to the courtyard, against Building 2's NORTH wall (the designer, 2026-09-18:
# the pad had no way to either entrance). North because it lands at the stoop, and because
# the south yard's swale runs deepest at the pad, where no walk could stand beside it.
WALK_PARK = (B2_X-WALK_W, STAIR[1]-WALK_W, B2_X, PARK_Y0)
WALK_COURT = (B2_X, STAIR[1]-WALK_W, WALK_SIDE[2], STAIR[1])
WALKS = [WALK_U1, WALK_SIDE, WALK_COURT, WALK_PARK]
U2_DOOR = (B2_X+U5_DOOR_X0, B2_X+U5_DOOR_X1)

# ---------------- the zoning figures ----------------
REAR_LINE  = B1_Y+B1_D                              # Building 1's rear wall
REAR_REQ   = ZONING.REAR_YARD_MIN*LOT_AREA          # C.C. 3332.27, 25 percent of the lot
REAR_PROV  = (SITE_D-REAR_LINE)*SITE_W              # the total rear yard behind it
ADU_IN_REAR = B2_W*B2_D
ADU_REAR_PCT = 100.0*ADU_IN_REAR/REAR_PROV
ADU_REAR_MAX = 55.0                                 # C.C. 3332.355(C)(3), two adjoining ADUs

COVERAGE_BLDG = sum(b[2]*b[3] for b in SITE_BLDG)
COVERAGE = COVERAGE_BLDG+STAIR_AREA
COVERAGE_MAX = ZONING.COVERAGE_MAX

# Living area, stud face to stud face on every floor. The house loses its stair well on
# Level 2, which is open to below; each ADU is one floor of Building 2. The measuring
# convention is not settled for this project; stud to stud is stated with the figures.
def _stud_sf(w, d):
    return (w-2*EXT_STUD)*(d-2*EXT_STUD)
PRINCIPAL_SF = 2*_stud_sf(B1_W, B1_D)-B1_STAIR.stud_width*(Y_FOOT_RISER-Y_TOP_RISER)
ADU_SF       = _stud_sf(B2_W, B2_D)
ADU_SF_MAX   = max(ZONING.ADU_PCT_MAX*PRINCIPAL_SF, 1000.0)   # C.C. 3332.355(B)(3)(a)

PRINCIPAL_HEIGHT = levels.height(B1_W)
ADU_HEIGHT       = levels.height(B2_W)
ADU_HEIGHT_MAX   = 25.0                             # C.C. 3332.355(B)(3)(b)
HEIGHT_MAX       = 35.0                             # the H-35 height district

PARK_REQ   = 2                                      # the principal dwelling; ADUs exempt
MANEUVER   = ZONING.MANEUVER_MIN                    # C.C. 3312.25, into a 90-degree stall
MANEUVER_HAVE = ALLEY_W+(PAD_D-PARK_D)              # the alley, plus any pad past a stall

VARIANCES = []                                      # none requested


def zoning_rows():
    """(label, value) for every row of C-102's zoning table."""
    return [
        ("Lot area", "{:,.0f} SF  ({} x {})".format(LOT_AREA, fmt(SITE_W), fmt(SITE_D))),
        ("Lot type", "INTERIOR"),
        ("Lot width", "%s — BY THE LOT SPLIT OF %s" % (fmt(SITE_W), PARCEL)),
        ("Dwelling units", "3 — ONE DWELLING AND TWO ADUs"),
        ("  Permitted", "TWO ADUs, 5 UNITS MAX, C.C. 3332.355(B)(2)"),
        ("Front yard", "%s TO BUILDING 1" % fmt(FRONT_YARD)),
        ("Side yards", "%s EACH SIDE, %s COMBINED" % (fmt(SIDE_YARD), fmt(2*SIDE_YARD))),
        ("Rear yard required", "{:,.0f} SF  (25% OF LOT), C.C. 3332.27".format(REAR_REQ)),
        ("Rear yard provided", "{:,.0f} SF".format(REAR_PROV)),
        ("ADU in rear yard, 3332.355(C)(3)", "{:,.0f} SF = {:.1f}%  ({:.0f}% MAX)"
         .format(ADU_IN_REAR, ADU_REAR_PCT, ADU_REAR_MAX)),
        ("Principal living area", "{:,.0f} SF — UNIT 1, STUD TO STUD".format(PRINCIPAL_SF)),
        ("ADU living area, 3332.355(B)(3)", "{:,.0f} SF EACH  ({:,.0f} SF MAX)"
         .format(ADU_SF, ADU_SF_MAX)),
        ("Lot coverage", "{:,.0f} SF = {:.1f}%  ({:.0f}% MAX WITH ADU)"
         .format(COVERAGE, 100*COVERAGE/LOT_AREA, 100*COVERAGE_MAX)),
        ("  Buildings", "{:,.0f} SF".format(COVERAGE_BLDG)),
        ("  Unit 3 exterior stair", "{:,.0f} SF".format(STAIR_AREA)),
        ("Building height", "%s  (%s MAX, H-35)" % (fmt(PRINCIPAL_HEIGHT), fmt(HEIGHT_MAX))),
        ("ADU height, 3332.355(B)(3)", "%s  (%s MAX, NOT OVER BUILDING 1)"
         % (fmt(ADU_HEIGHT), fmt(ADU_HEIGHT_MAX))),
        ("  Mean of eave and ridge, 3303.08", "%s / %s" % (fmt(levels.EAVE), fmt(levels.ridge(B2_W)))),
        ("Parking required", "%d, C.C. 3312.49  (ADUs EXEMPT)" % PARK_REQ),
        ("Parking provided", "%d" % PARK_N),
        ("Maneuvering, 3312.25", "%s ALLEY R.O.W.  (%s REQ'D)" % (fmt(MANEUVER_HAVE), fmt(MANEUVER))),
    ]


# ---------------- what the site has to keep true ----------------
def site_violations():
    """Every way the site as modelled breaks a rule this sheet tabulates."""
    bad = []
    for (x, y, w, d, nm, _l, _k) in SITE_BLDG:
        if x < SIDE_YARD-1e-9 or x+w > SITE_W-SIDE_YARD+1e-9:
            bad.append("%s is in a side yard" % nm)
        if y < FRONT_YARD-1e-9:
            bad.append("%s is in the front yard" % nm)
    if B2_Y < REAR_LINE+1e-9:
        bad.append("Building 2 is not in the rear yard, C.C. 3332.355(C)(1)")
    if STAIR[1] < REAR_LINE+1e-9:
        bad.append("the Unit 3 stair reaches Building 1")
    if PARK_X0 < -1e-9 or PARK_X1 > SITE_W+1e-9 or PARK_Y0 < B2_Y+B2_D-1e-9:
        bad.append("the parking pad leaves the lot or runs under Building 2")
    if REAR_PROV < REAR_REQ-1e-9:
        bad.append("rear yard under 25 percent of the lot, C.C. 3332.27")
    if ADU_REAR_PCT > ADU_REAR_MAX+1e-9:
        bad.append("Building 2 over 55 percent of the rear yard, C.C. 3332.355(C)(3)")
    if COVERAGE > COVERAGE_MAX*LOT_AREA+1e-9:
        bad.append("lot coverage over 65 percent")
    if ADU_SF > ADU_SF_MAX+1e-9:
        bad.append("an ADU is over the area C.C. 3332.355(B)(3)(a) allows")
    if ADU_HEIGHT > min(PRINCIPAL_HEIGHT, ADU_HEIGHT_MAX)+1e-9:
        bad.append("Building 2 is taller than Building 1 or 25'-0\"")
    if PRINCIPAL_HEIGHT > HEIGHT_MAX+1e-9:
        bad.append("Building 1 is over the H-35 district's 35'-0\"")
    if PARK_N < PARK_REQ:
        bad.append("fewer stalls than C.C. 3312.49 requires")
    if MANEUVER_HAVE < MANEUVER-1e-9:
        bad.append("maneuvering under the 20'-0\" of C.C. 3312.25")
    # every dwelling reaches Oak: each walk starts at the right-of-way or on the walk
    # before it, and ends at its door
    if WALK_U1[1] > 1e-9 or abs(WALK_U1[3]-B1_Y) > 1e-9:
        bad.append("Unit 1's walk does not run from Oak to its door")
    if WALK_SIDE[1] > 1e-9 or abs(WALK_SIDE[3]-WALK_COURT[3]) > 1e-9:
        bad.append("the Units 2 and 3 walk does not reach the courtyard from Oak")
    if WALK_COURT[0] > STAIR[0]+1e-9 or not (STAIR[0] <= U2_DOOR[0] and U2_DOOR[1] <= WALK_COURT[2]):
        bad.append("the courtyard walk misses Unit 3's stoop or Unit 2's door")
    if abs(WALK_PARK[3]-PARK_Y0) > 1e-9 or not (PARK_X0 <= WALK_PARK[0] and WALK_PARK[2] <= PARK_X1):
        bad.append("the parking walk does not start at the pad")
    if abs(WALK_PARK[2]-WALK_COURT[0]) > 1e-9 or WALK_PARK[1] > WALK_COURT[1]+1e-9:
        bad.append("the parking walk does not reach the courtyard walk")
    if WALK_SIDE[0] < SITE_W-SIDE_YARD-1e-9 or WALK_SIDE[2] > SITE_W+1e-9:
        bad.append("the side walk leaves the side yard")
    return bad


def check_site():
    print("SITE, C-102: lot %s x %s; front yard %s; courtyard %s; pad %s; coverage %.1f%%; "
          "rear yard %.0f SF, Building 2 %.1f%% of it"
          % (fmt(SITE_W), fmt(SITE_D), fmt(FRONT_YARD), fmt(COURT), fmt(PAD_D),
             100*COVERAGE/LOT_AREA, REAR_PROV, ADU_REAR_PCT))
    bad = site_violations()
    assert not bad, "400 Oak site: %s" % "; ".join(bad)


DOOR_H = 6.0+8.0/12.0

# ---------------- the RCO 302.1 imaginary line in the courtyard ----------------
# src/fsd.py places the line; this measures the site against it. Building 1's rear wall
# is measured storey by storey from the plans' own window lists: (opening SF, wall SF),
# the gable left out.
FSD_LINE_Y = fsd.line_y(REAR_LINE)


def rear_storeys():
    heights = {1: levels.FLOOR_RISE, 2: levels.ROOF_PLATE-levels.FF2}
    rear = lambda o: o[3] == 'h' and abs(o[1]-Y_REAR) < 1e-6
    return [(sum(WIN_SF[w[4]] for w in LEVEL[lv]['wins'] if rear(w))
             + sum(d[2]*DOOR_H for d in LEVEL[lv]['doors'] if rear(d) and "ext" in d[5:]),
             B1_W*heights[lv]) for lv in sorted(LEVEL)]


EAVE_FIREBLOCKED = True        # every eave, top plate to roof sheathing: Table 302.1(1) footnote a
GABLE_VENTS = False            # no gable is vented: the eave intake and ridge vent are the attic's
                               # only vents, as the ridge-vent makers require (S-103 note 6)


def roof_edges():
    """(name, kind, its wall's fire separation distance, overhang, fireblocked, gable vent)
       for all eight roof edges. Oak and the alley are public ways: RCO 202 measures to
       their centerlines, and the table never engages (None)."""
    from src.foundation import ROOF_OVERHANG as o
    return [("BUILDING 1 OAK RAKE", rco_fsd.RAKE, None, o, False, GABLE_VENTS),
            ("BUILDING 1 REAR RAKE", rco_fsd.RAKE, fsd.OFF_B1, o, False, GABLE_VENTS),
            ("BUILDING 1 NORTH EAVE", rco_fsd.EAVE, SIDE_YARD, o, EAVE_FIREBLOCKED, False),
            ("BUILDING 1 SOUTH EAVE", rco_fsd.EAVE, SIDE_YARD, o, EAVE_FIREBLOCKED, False),
            ("BUILDING 2 COURTYARD RAKE", rco_fsd.RAKE, fsd.OFF_B2, o, False, GABLE_VENTS),
            ("BUILDING 2 ALLEY RAKE", rco_fsd.RAKE, None, o, False, GABLE_VENTS),
            ("BUILDING 2 NORTH EAVE", rco_fsd.EAVE, SIDE_YARD, o, EAVE_FIREBLOCKED, False),
            ("BUILDING 2 SOUTH EAVE", rco_fsd.EAVE, SIDE_YARD, o, EAVE_FIREBLOCKED, False)]


def check_fsd():
    st = rear_storeys()
    rated = lambda r: "unrated" if r == 'NONE' else r.lower()
    cap = rco_fsd.opening_max(fsd.OFF_B1)
    print("IMAGINARY LINE, RCO 302.1: %s off Building 1 (rear wall %s, openings %s, %.1f%% of a storey), "
          "%s off Building 2; the Unit 3 stair %s clear, underside %s"
          % (fmt(fsd.OFF_B1), rated(rco_fsd.wall_rating(fsd.OFF_B1)),
             "unlimited" if cap is None else "%.0f%% max" % (100*cap),
             100*fsd.rear_open_ratio(st), fmt(fsd.OFF_B2), fmt(fsd.stair_clear()),
             rated(rco_fsd.projection_rating(fsd.stair_clear()))))
    from src.foundation import ROOF_OVERHANG
    assert abs(fsd.RAKE_OVERHANG-ROOF_OVERHANG) < 1e-9, "fsd.py places the line for a %s rake" % fmt(fsd.RAKE_OVERHANG)
    v = fsd.fsd_violations(REAR_LINE, B2_Y, st, rear_rake=ROOF_OVERHANG, rear_gable_vent=GABLE_VENTS)
    v += rco_fsd.edge_violations(roof_edges())
    print("   roof edges: rear rake %s to the line, side eaves %s to the lot lines, fireblocked (footnote a)"
          % (fmt(fsd.OFF_B1-ROOF_OVERHANG), fmt(SIDE_YARD-ROOF_OVERHANG)))
    # the stair Building 2 draws is the one fsd measures
    if abs((STAIR[3]-STAIR[1])-fsd.STAIR_W) > 1e-9:
        v.append("the Unit 3 stair projects %s, not the %s the line is set for"
                 % (fmt(STAIR[3]-STAIR[1]), fmt(fsd.STAIR_W)))
    assert not v, "400 Oak courtyard: %s" % "; ".join(v)

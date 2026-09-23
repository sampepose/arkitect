"""Shared vertical dimensions, in FEET above finished grade.

Feet because everything else is: fmt() takes feet, the plan grid is feet, the drawn
scales are points per foot. This module used to be inches, which did not remove the
conversion, it moved it to every reader — build.py wrote fmt(levels.F2_PLATE/12)
twenty-three times, and each one was a place to forget the /12.

IN(n) writes an inch dimension where it is defined; from then on it is feet.

Finish thicknesses are design allowances. F1's ceiling is its listed assembly's, ICC-ES
ESR-1153 Assembly F: RC-1 resilient channels, a mineral wool blanket on them and ONE
5/8" Type C layer. src/framing.py holds the framing to that listing; changing a layer
updates ceiling elevations.
Bearing means TOP of wall plate / UNDERSIDE of joist, not ceiling or stud length.
"""
from arkitect.lib.units import IN

GRADE = 0.0
# Level 1's finished floor, 8-1/4" above finished grade at the wall, so the slab top and
# the foundation wall under the plate stand 8" out of the ground (the designer, 2026-09-18). RCO
# 404.1.6 asks 6" where there is no masonry veneer, and the slab stood 5-3/4"; 8" also
# keeps the siding and sheathing off the ground, leaves the termite inspector a visible
# band of concrete, and gives the 6" of fall away from the wall room. Every height in
# the set is read from here.
FF1 = IN(8.25)
REVEAL_MIN = IN(6)            # RCO 404.1.6: the foundation above finished grade
FLOOR_RISE = IN(120.0)
FF2 = FF1 + FLOOR_RISE
FLOOR_FINISH = IN(.25)
SLAB_TOP = FF1 - FLOOR_FINISH
SUBFLOOR_TOP = FF2 - FLOOR_FINISH
SUBFLOOR = IN(.75)
F1_JOIST = IN(11.875)
F2_JOIST = IN(14.0)
F1_DEPTH = F1_JOIST + SUBFLOOR
F2_DEPTH = F2_JOIST + SUBFLOOR
# F1 is ICC-ES ESR-1153 Figure 3F, Assembly F: the report's only single-layer
# floor-ceiling that needs no suspended grid (A-601).
F1_LISTING = 'ICC-ES ESR-1153 ASSEMBLY F'
F1_CHANNEL = IN(.5)          # RC-1 resilient channel depth
F1_CHANNEL_OC = IN(16)       # perpendicular to the joists; Assembly F states 16" flat
F1_LAYERS = 1                # Assembly F is a single layer
F1_LAYER = IN(.625)          # 5/8" Type C gypsum board
# Assembly F names two proprietary Type C boards. Generic Type X to ASTM C1396 is what
# Assembly B took and is NOT an alternate here; the sheets must not offer it.
F1_BOARD = 'TYPE C'
F1_GYPSUM = F1_LAYERS * F1_LAYER
# The blanket is a fire/sound product, not thermal insulation: F1 is between dwellings.
F1_INSUL_T = IN(1.5)         # mineral wool, on the channels between the bottom flanges
F1_INSUL_PCF = 2.5           # minimum density
# Assembly F tests "nominal 2x4 or larger flanges" -- a TJI 560-class joist. A-601 draws it.
F1_FLANGE_W = IN(3.5)
F1_FLANGE_T = IN(1.5)
F2_GYPSUM = IN(.5)
F1_PLATE = SUBFLOOR_TOP - F1_DEPTH
F2_PLATE = SUBFLOOR_TOP - F2_DEPTH
F1_CEILING = F1_PLATE - F1_CHANNEL - F1_GYPSUM
F2_CEILING = F2_PLATE - F2_GYPSUM
ROOF_PLATE = FF2 + IN(108.0)
UPPER_GYPSUM = IN(.625)
UPPER_CEILING = ROOF_PLATE - UPPER_GYPSUM
ROOF_PITCH = 4 / 12          # a ratio, not a length: rise over run
# The raised (energy) heel S-103 detail 1 draws: top of plate to the top of the heel at
# the wall line, which is the eave the set's datums and C.C. 3303.08's height are taken
# at. The fascia of the 12" overhang (roof.EAVE_OVERHANG) is 4" lower, so a height
# measured from here is the higher figure.
ROOF_HEEL = IN(16)
EAVE = ROOF_PLATE + ROOF_HEEL

def ridge(span_feet):
    """Nominal drawn roof profile: the eave, then the pitch over half the span."""
    return EAVE + span_feet / 2 * ROOF_PITCH

def height(span_feet):
    """C.C. 3303.08, a pitched roof: the mean between the point of the gable and the
       eaves, from finished grade — never less than the code's figure, which measures
       from the curb where the curb is higher."""
    return (EAVE + ridge(span_feet)) / 2

def check():
    import math
    for plate, depth in ((F1_PLATE,F1_DEPTH),(F2_PLATE,F2_DEPTH)):
        assert math.isclose(plate + depth + FLOOR_FINISH, FF2)
    assert math.isclose(SLAB_TOP + FLOOR_FINISH, FF1)
    assert math.isclose(F1_PLATE-F2_PLATE,IN(2.125))
    assert math.isclose(F2_CEILING-FF1,IN(104.5))
    assert math.isclose(F1_CEILING-FF1,IN(106.0))
    assert math.isclose(UPPER_CEILING-FF2,IN(107.375))
    assert math.isclose(FF2-FF1, FLOOR_RISE) and math.isclose(FLOOR_RISE, IN(120))
    assert SLAB_TOP-GRADE >= REVEAL_MIN-1e-9, (
        "the foundation stands %g in above finished grade, under RCO 404.1.6's %g"
        % ((SLAB_TOP-GRADE)*12, REVEAL_MIN*12))
    # the same line this has always printed, derived rather than typed
    print('HEIGHT CHECK: F2 plate +%g in / F1 plate +%g in; floor rise %g in'
          % (F2_PLATE*12, F1_PLATE*12, FLOOR_RISE*12))

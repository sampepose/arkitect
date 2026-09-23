"""Shared vertical dimensions, in FEET above finished grade.

Feet because everything else is: fmt() takes feet, the plan grid is feet, the drawn
scales are points per foot. This module used to be inches, which did not remove the
conversion, it moved it to every reader — build.py wrote fmt(levels.F2_PLATE/12)
twenty-three times, and each one was a place to forget the /12.

IN(n) writes an inch dimension where it is defined; from then on it is feet.

Finish thicknesses are design allowances. F1's ceiling is its listed assembly's, UL Design
L528: resilient channels and ONE 5/8" Type C layer under open-web floor trusses.
src/framing.py holds the framing to that listing; changing a layer updates ceiling
elevations.
Bearing means TOP of wall plate / UNDERSIDE of joist, not ceiling or stud length.
"""
from arkitect.lib.units import IN

GRADE = 0.0
# Level 1's finished floor, 8-1/4" above finished grade at the wall, so the slab top and
# the foundation wall under the plate stand 8" out of the ground (the designer, 2026-09-18). RCO
# 404.1.6 asks 6" where there is no masonry veneer, and the slab stood 5-3/4"; 8" also
# keeps the siding and sheathing off the ground, leaves the termite inspector a visible
# band of concrete, and gives the 6" of fall away from the wall room on a 5' side yard.
# Every height in the set is read from here.
FF1 = IN(8.25)
REVEAL_MIN = IN(6)            # RCO 404.1.6: the foundation above finished grade
FLOOR_RISE = IN(120.0)
FF2 = FF1 + FLOOR_RISE
FLOOR_FINISH = IN(.25)
SLAB_TOP = FF1 - FLOOR_FINISH
SUBFLOOR_TOP = FF2 - FLOOR_FINISH
SUBFLOOR = IN(.75)
# Both floors on 14" OPEN-WEB FLOOR TRUSSES (the designer, 2026-09-18: "let's go with trusses,
# whatever is more dummy proof"), from the plant that builds the roof trusses. 14" and not
# deeper: the plate is SUBFLOOR_TOP less this depth, and the Level 1 window heads at 8'-0"
# leave only 6" under it for a header. The two plates are one height.
F1_JOIST = IN(14.0)
F2_JOIST = IN(14.0)
F1_DEPTH = F1_JOIST + SUBFLOOR
F2_DEPTH = F2_JOIST + SUBFLOOR
# F1 is UL Design L528, read from UL Product iQ's text of 2025-06-30: parallel-chord wood
# trusses of nominal 2x4 lumber at 24" o.c. maximum, 12" deep minimum; flooring System No. 1,
# 23/32" T&G subfloor glued and nailed; Item 3A resilient channels at 16" o.c.; Item 4, ONE
# layer of 5/8" board of a type the design lists. Its base build-up has NO insulation in the
# cavity, and none may be added except as the design's own items allow (A-601 item B).
F1_LISTING = 'UL DESIGN L528'
F1_CHANNEL = IN(.5)          # resilient channel depth
F1_CHANNEL_OC = IN(16)       # Item 3A: 16" o.c., perpendicular to the trusses
F1_LAYERS = 1                # Item 4 is a single layer
F1_LAYER = IN(.625)          # 5/8" Type C gypsum board
# Item 4 lists Type C from every major maker (USG C, CertainTeed C, National Gypsum FSW-C,
# Georgia-Pacific TG-C, American AG-C, PABCO C). Generic Type X to ASTM C1396 is NOT listed.
F1_BOARD = 'TYPE C'
F1_GYPSUM = F1_LAYERS * F1_LAYER
# The trusses' chords: nominal 2x4, flat, which is what L528 tests and A-601 draws.
F1_CHORD_W = IN(3.5)
F1_CHORD_T = IN(1.5)
F2_GYPSUM = IN(.625)         # the trusses are at 24" o.c.: 5/8" ceiling board, as the roof's
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
    assert math.isclose(F1_PLATE, F2_PLATE)
    assert math.isclose(F2_CEILING-FF1,IN(104.375))   # 5/8" board under the 24" o.c. trusses
    assert math.isclose(F1_CEILING-FF1,IN(103.875))
    assert math.isclose(UPPER_CEILING-FF2,IN(107.375))
    assert math.isclose(FF2-FF1, FLOOR_RISE) and math.isclose(FLOOR_RISE, IN(120))
    assert SLAB_TOP-GRADE >= REVEAL_MIN-1e-9, (
        "the foundation stands %g in above finished grade, under RCO 404.1.6's %g"
        % ((SLAB_TOP-GRADE)*12, REVEAL_MIN*12))
    # the same line this has always printed, derived rather than typed
    print('HEIGHT CHECK: F2 plate +%g in / F1 plate +%g in; floor rise %g in; slab top +%g in above grade'
          % (F2_PLATE*12, F1_PLATE*12, FLOOR_RISE*12, (SLAB_TOP-GRADE)*12))

"""The street face's exterior finish: Building 1's Oak Avenue face.

Carried from 300 S Elm, where the designer picked it on 2026-09-16 from a list of low-cost ways to
make the buildings look better: flat casings round every window and door, a head casing
with a drip cap, a frieze board under the eaves, corner boards, and a flat door surround at
Unit 1's entry — pilasters and a crosshead on the wall, nothing projecting into the front
yard. The frieze, corner boards and surround are the street face's alone; the casings are
on every opening of both buildings. Black window frames and no grilles on every face.

Sizes are the set's own, not a product's. 300's equipment screening is not carried: this
project has no service-equipment model yet.
"""
from arkitect.lib.units import IN

# (building, face) as src/sheets/elevations.py names them.
STREET_FACES = ((1, 'FRONT'),)
# EVERY window and door on every face of both buildings is cased (the designer, 2026-09-18): flat
# casings, a head casing and a drip cap. The frieze, the corner boards and the entry's
# surround stay the street face's.
CASE_ALL_OPENINGS = True
CASING_W     = IN(3.5)       # 1x4 flat casing, sides and sill
HEAD_CASING  = IN(5.5)       # 1x6 head casing
HEAD_EAR     = IN(0.75)      # the head casing runs past each side casing
DRIP_CAP     = IN(1.5)       # metal drip cap over the head casing
FRIEZE       = IN(7.25)      # 1x8 frieze board under the soffit
CORNER_BOARD = IN(3.5)       # 1x4 each side of a street-face corner
TRIM_MATERIAL = 'CELLULAR PVC'
SHAKE_COURSE = IN(7)         # a gable accent's exposure; no face takes one here

# ---------------- Unit 1's door surround ----------------
SURROUND_PILASTER  = IN(4.5)
SURROUND_CROSSHEAD = IN(9.25)    # 1x10 crosshead
SURROUND_CAP_EAR   = IN(1.5)     # the crosshead's cap past each pilaster

# ---------------- windows ----------------
WINDOW_COLOUR = 'BLACK EXTERIOR FRAME AND SASH'

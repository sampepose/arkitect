"""Columbus City Code Title 33: the zoning rules a residential infill lot answers to.

Each number carries the section it comes from, because a figure without its citation can
be neither checked nor corrected safely by the next person. Verified against a
Columbus permit set's zoning tabulation, 2026-09-17.
"""

COVERAGE_MAX = 0.65          # of the lot, buildings and permanent structures
REAR_YARD_MIN = 0.25         # of the lot area, behind the principal building
ADU_PCT_MAX = 0.65           # an accessory dwelling against the principal dwelling
VISION_TRIANGLE_ST = 30.0    # feet along each right of way at a street corner
MANEUVER_MIN = 20.0          # feet of backing space into a 90-degree stall
STALL_D = 18.0               # feet, the depth of a parking stall

# Sections the first project's set actually cites for each rule. Each was traced to the
# line in its sitework.py that states it; none is inferred.
CITATIONS = {
    'REAR_YARD_MIN':      'C.C. 3332.27',          # sitework.py:453
    'ADU_PCT_MAX':        'C.C. 3332.355(B)(3)',
    'VISION_TRIANGLE_ST': 'C.C. 3321.05(B)(2)',    # sitework.py:638
    'MANEUVER_MIN':       'C.C. 3312.25',          # sitework.py:664
}

# Rules whose section that set does NOT establish. Listed, not guessed: a section
# printed beside a number reads as verified, so an invented one is worse than none.
# Research these and move each into CITATIONS with the line that sources it.
UNVERIFIED = {
    'COVERAGE_MAX': ("The first set's zoning table prints '65% WITH ADU' and cites no section "
                     "for the coverage limit."),
    'STALL_D': ("The first set cites C.C. 3312.27 for the parking SETBACK and C.C. 3312.49 for "
                "the number of spaces required; neither sets the 18'-0\" stall depth."),
}

SECTION_UNVERIFIED = 'SECTION UNVERIFIED'


def citation(rule):
    """The section to print beside a rule: the one the set cites, or a plain statement
       that none has been established. Never something shaped like a section number
       that nobody checked."""
    if rule in CITATIONS:
        return CITATIONS[rule]
    assert rule in UNVERIFIED, 'no such zoning rule: %r' % rule
    return SECTION_UNVERIFIED


# ---------------- side yards, C.C. 3332.25 and 3332.26 ----------------
# Researched 2026-09-20, answering a plan review that asked what the "exact 5'-0" side
# setbacks" were measured to. The answer changed the question: on a NARROW lot the
# minimum side yard is not 5'-0" at all.
#
# C.C. 3332.26, Minimum side yard permitted, is "the least dimension between any part of
# the building or structure and the side lot line", and its cases include:
#   - 7-1/2 ft in the R-rural, LRR, RRR and RR districts
#   - 5 ft for a lot OVER 40 ft wide in the SR, R-1, R-2, R-2F, R-3 and R-4 districts
#   - 3 ft on a lot 40 ft wide OR LESS, in any district
# C.C. 3332.25, Maximum side yards required, is 20 percent of the lot width, with the
# total required on a lot 40 ft wide or less capped at 6 ft.
#
# Sources: the City of Columbus Building and Zoning Services handout "General Development
# Standards for Residential Zoning Districts", 2026, columbus.gov/bzs, which states all
# five figures; and the section titles confirmed against Columbus Legistar ordinance text
# (CV25-023, ORD 1364-2025, which cites "Section 3332.26, Minimum side yard permitted").
#
# WHY NOTHING PRINTS THESE YET. The verbatim, ORDERED text of 3332.26 was not obtained --
# municode renders by script and elaws timed out -- and the order matters: there is also a
# case for "a two-, three-, or four-family dwelling on a lot 50 feet wide or more", and
# a three-unit dwelling is exactly that case's subject. Which case governs a 3-unit dwelling on a
# 40 ft lot depends on how the provisos are sequenced. Both projects currently print a
# STRICTER minimum than these figures and comply with it, which is the safe direction; a
# set that printed 3'-0" on this research and was wrong would understate a requirement.
# Confirm at the counter -- BZS offers a preliminary residential zoning clearance review --
# then move these into CITATIONS and let the tables read them.
SIDE_YARD_UNVERIFIED = {
    'NARROW_LOT_MIN': 3.0,       # ft, a lot 40 ft wide or less, any district, C.C. 3332.26
    'WIDE_LOT_MIN': 5.0,         # ft, a lot over 40 ft wide, SR/R-1/R-2/R-2F/R-3/R-4
    'COMBINED_PCT': 0.20,        # of lot width, C.C. 3332.25
    'COMBINED_CAP_NARROW': 6.0,  # ft, the most required on a lot 40 ft wide or less
}

# What a yard is measured TO, which the review actually asked. 3332.26 says "any part of
# the building or structure", so the CLADDING counts -- a yard is not measured to the
# framing. RCO 202 measures a fire separation distance to "the building face ... at a
# right angle from the face of the wall" and leaves "face" undefined, while separately
# defining EXTERIOR WALL COVERING as material "applied on the exterior side of exterior
# walls", which reads as though the wall's face is under its covering. That one is
# arguable and is the building official's call, not this file's.
YARD_MEASURED_TO = 'any part of the building or structure, C.C. 3332.26'

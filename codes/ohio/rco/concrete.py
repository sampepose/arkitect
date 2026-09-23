"""RCO Table 402.2, minimum specified compressive strength of concrete, and the check an
element schedule is held to.

One transcription for every project, pinned by codes/verify/test_concrete_table.py. A
project keeps what it SPECIFIES — which element stands on which row, at what strength and
air — and hands that, with its weathering potential, to table_violations().
"""
from collections import namedtuple
from lib.units import fmt

# ---------------- concrete, RCO Table R402.2 ----------------
WEATHERINGS = ("NEGLIGIBLE", "MODERATE", "SEVERE")
# Table R402.2, minimum specified compressive strength at 28 days in psi, one column per
# weathering potential, each cell (psi, its footnotes), transcribed from OAC 4101:8-4-01
# eff. 3-1-2024, which prints it as Table 402.2 and matches the 2018 IRC word for word.
#   c  subject to freezing and thawing during construction: air-entrained per d
#   d  air-entrained, total air AIR_MIN to AIR_MAX by volume
#   e  Section R402.2: fly ash, other pozzolans, silica fume, slag or blended cements
#      within ACI_DEICING where exposed to deicing chemicals
#   f  garage floors with a steel-troweled finish (none here)
NOT_EXPOSED, INTERIOR_SLAB, VERTICAL_EXPOSED, PORCH_STEPS = range(4)
T_R402_2 = (
    ((2500, ""), (2500, ""),    (2500, "c")),      # basement walls, foundations and other concrete not exposed to the weather
    ((2500, ""), (2500, ""),    (2500, "c")),      # basement slabs and interior slabs on grade, except garage floor slabs
    ((2500, ""), (3000, "d"),   (3000, "d")),      # basement, foundation and exterior walls, other vertical work exposed to the weather
    ((2500, ""), (3000, "def"), (3500, "def")),    # porches, carport slabs and steps exposed to the weather, garage floor slabs
)
AIR_MIN, AIR_MAX = 0.05, 0.07
ACI_DEICING = "ACI 318 SECTION 19.3.3.4"

Concrete = namedtuple("Concrete", "element row psi air")


def psi(v):
    return "{:,} PSI".format(v)


def table_violations(concrete, weathering, wall_element, wall_above_grade):
    """Each element at or above its Table 402.2 cell for the weathering potential,
       air-entrained wherever the cell carries footnote d, footnote c carried wherever
       the cell does, and `wall_element` on the exposed row while it stands `wall_above_grade`
       feet above finished grade."""
    col = WEATHERINGS.index(weathering)
    bad = []
    for e in concrete:
        need, notes = T_R402_2[e.row][col]
        if e.psi < need:
            bad.append((e.element, "%s under the %s of Table 402.2" % (psi(e.psi), psi(need))))
        if "d" in notes and e.air != "AE":
            bad.append((e.element, "not air-entrained, Table 402.2 footnote d"))
        if "c" in notes and e.air not in ("AE", "c"):
            bad.append((e.element, "Table 402.2 footnote c not carried"))
        if e.element == wall_element and wall_above_grade > 0 and e.row != VERTICAL_EXPOSED:
            bad.append((e.element, "stands %s above finished grade, so it is exposed to the weather"
                        % fmt(wall_above_grade)))
    return bad

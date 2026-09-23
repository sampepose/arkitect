"""M-101 — Building 1 mechanical plans: Level 1 and Level 2 side by side, greyed, with
the heads, fans, ducts, caps and line sets on them; the legend, the schedules and the
notes."""
from lib.draw.page import Sheet, end_plans
from lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import _b1_level
from src.mechanical import B1_LEVELS
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.m_common import (grey_context, notes, outdoor_schedule, place, termination_schedule, title,
                                 ventilation_schedule)
from lib.draw.mechanical_kit import legend
from src.sheets.m_common import DUCTLESS
from src.sheets.plans import B1_DRAWING


def _level(k, ox, oy):
    """One Building 1 level as a mechanical background, its work on it: Unit 1's level
       and Unit 2 (Level 1) or Unit 3 (Level 2)."""
    lv = _b1_level(k, [], [], [], units=[], u3stair=(k == 1), annotate=False, **B1_DRAWING)
    def work(p):
        for m in B1_LEVELS:
            if m.level == k: place(p, m)
        grey_context(p, 26, 48, 'S ELM AVENUE', 'REAR YARD  ·  BUILDING 2 BEYOND',
                     'SAGE AVENUE', 'ADJACENT PARCEL')
    lv.overlay = work
    return draw_level(c, lv, ox, oy)


def sheet_m101():
    sh = Sheet(c, "M-101", "Building 1 — mechanical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-48*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+26*Q+1.0*inch
    _level(1, ox1, oy)
    p2 = _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 1 — MECHANICAL PLAN  ·  UNIT 1 BELOW, UNIT 2')
    title(ox2, oy, 'BUILDING 1 — LEVEL 2 — MECHANICAL PLAN  ·  UNIT 1 ABOVE, UNIT 3')
    # the right column: legend, then the three schedules
    rx = ox2+26*Q+0.45*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, rw, kinds=DUCTLESS)-6
    ry = outdoor_schedule(rx, ry, rw, 1)
    ry = ventilation_schedule(rx, ry, rw, 1)
    ry = termination_schedule(rx, ry, rw, 1)
    assert ry > Y0, 'M-101 right column runs off the sheet'
    # under the plans: the notes across the width the plans take
    by = oy-1.22*inch
    nb = notes(ox1, by, rx-0.3*inch-ox1)
    assert nb > Y0, 'M-101 notes run off the sheet'
    c.showPage()

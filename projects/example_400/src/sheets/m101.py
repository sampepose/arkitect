"""M-101 — Building 1 mechanical plans: Unit 1's two levels side by side, greyed, with
the heads, fans, ducts, caps and line sets on them; the legend, the schedules and the
notes."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import B1_D, B1_W, b1_level
from src.mechanical import B1_LEVELS
from src.sheets.a101 import draw_b1_stair
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.m_common import legend_kinds
from src.sheets.m_common import (grey_context, notes, outdoor_schedule, place, termination_schedule, title,
                                 ventilation_schedule)
from arkitect.lib.draw.mechanical_kit import legend


def _level(k, ox, oy):
    """One level of the house as a mechanical background, its work on it."""
    lv = b1_level(k)
    lv.over_plan = lambda pp: draw_b1_stair(pp, k)
    def work(p):
        for m in B1_LEVELS:
            if m.level == k: place(p, m)
        grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'BUILDING 2 AND THE ALLEY BEYOND',
                     '396 OAK AVE', '404 OAK AVE', side_at=(8.0, None))     # HP-1 holds the wall's middle
    lv.overlay = work
    return draw_level(c, lv, ox, oy)


def sheet_m101():
    sh = Sheet(c, "M-101", "Building 1 — mechanical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.75*inch-B1_D*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+B1_W*Q+1.2*inch
    _level(1, ox1, oy)
    p2 = _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 1 — MECHANICAL PLAN  ·  UNIT 1')
    title(ox2, oy, 'BUILDING 1 — LEVEL 2 — MECHANICAL PLAN  ·  UNIT 1')
    # the right column: legend, then the three schedules
    rx = ox2+B1_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, rw, kinds=legend_kinds(1))-6
    ry = outdoor_schedule(rx, ry, rw, 1)
    ry = ventilation_schedule(rx, ry, rw, 1)
    ry = termination_schedule(rx, ry, rw, 1)
    assert ry > Y0, 'M-101 right column runs off the sheet'
    # under the plans: the notes across the width the plans take
    by = oy-1.22*inch
    nb = notes(ox1, by, rx-0.3*inch-ox1)
    assert nb > Y0, 'M-101 notes run off the sheet'
    c.showPage()

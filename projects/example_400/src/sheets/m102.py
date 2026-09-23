"""M-102 — Building 2 mechanical plans: Unit 2 and Unit 3 side by side, greyed, with
the heads, fans, ducts, caps and line sets on them; the legend, the schedules and the
notes."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building2 import B2_D, B2_W, b2_level
from src.mechanical import B2_LEVELS
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.m_common import legend_kinds
from src.sheets.m_common import (grey_context, notes, outdoor_schedule, place, termination_schedule, title,
                                 ventilation_schedule)
from arkitect.lib.draw.mechanical_kit import legend
from src.sheets.a102 import draw_u5_stair


def _level(k, ox, oy):
    """One Building 2 level as a mechanical background, its work on it. k is 0 for
       Unit 2 at grade, 1 for Unit 3 above; the Unit 3 stair is drawn on both as A-102
       draws it."""
    lv = b2_level(k+1)
    lv.over_plan = lambda pp, above=(k == 0): draw_u5_stair(pp, B2_W, above=above)
    def work(p):
        for m in B2_LEVELS:
            if m.level == k+1: place(p, m)
        grey_context(p, B2_W, B2_D, 'COURTYARD  ·  FACES BUILDING 1  ·  OAK AVENUE BEYOND',
                     'PARKING AND ALLEY', '396 OAK AVE', '404 OAK AVE', top_off=5.6, side_at=(None, 25.0))   # HP-2 / HP-3
    lv.overlay = work
    return draw_level(c, lv, ox, oy)


def sheet_m102():
    sh = Sheet(c, "M-102", "Building 2 — mechanical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-0.9*inch-B2_D*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+B2_W*Q+1.2*inch
    _level(0, ox1, oy)
    p2 = _level(1, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 2 — LEVEL 1 — MECHANICAL PLAN  ·  UNIT 2')
    title(ox2, oy, 'BUILDING 2 — LEVEL 2 — MECHANICAL PLAN  ·  UNIT 3')
    rx = ox2+B2_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, rw, kinds=legend_kinds(2))-6
    ry = outdoor_schedule(rx, ry, rw, 2)
    ry = ventilation_schedule(rx, ry, rw, 2)
    ry = termination_schedule(rx, ry, rw, 2)
    assert ry > Y0, 'M-102 right column runs off the sheet'
    by = oy-1.22*inch
    nb = notes(ox1, by, rx-0.3*inch-ox1, see='M-101')
    assert nb > Y0, 'M-102 notes run off the sheet'
    c.showPage()

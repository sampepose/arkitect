"""M-101 — Building 1 mechanical plans: Unit 1's two levels side by side, greyed, with
the heads, fans, ducts, caps and line sets on them; the legend, the schedules and the
notes."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import B1_D, B1_W, LEVEL
from src.mechanical import B1_LEVELS, ahu_panel
from reportlab.pdfbase import pdfmetrics
from src.sheets.a101 import COMPASS, b1_trade_level, draw_north
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.roof import B1_ROOF
from src.sheets.common import draw_attic_hatch
from src.sheets.m_common import draw_drop, draw_panel, legend_kinds
from reportlab.lib.colors import black
from src.sheets.m_common import (grey_context, notes, outdoor_schedule, place, termination_schedule, title,
                                 ventilation_schedule)
from arkitect.lib.draw.mechanical_kit import legend


def _hall_label_off(k):
    """Level 1's hall label, moved up the hall to stand clear of AHU-1's cabinet, which
       fills the hall's middle: its last line 3 pt over the cabinet's access panel, as the plan
       sets a three-line label (7.2 pt name 5 pt over the point, the area 11 pt under)."""
    lv = next(m for m in B1_LEVELS if m.level == k)
    x, y, _room = lv.ahus[0]
    head = ahu_panel(k, x, y)[1]                        # its access panel's edge nearer the front
    room = next(r for r in LEVEL[k]['rooms'] if r[4] == "HALL")
    ry, rh = LEVEL[k]['plan'].rect(room)[1:4:2]
    return (0.0, head-(11+1.5+3)/Q-(ry+rh/2.0))


def _level(k, ox, oy):
    """One level of the house as a mechanical background, its work on it."""
    lv = b1_trade_level(k)
    if k == 1:
        lv.rooms = [r[:5]+(_hall_label_off(k),)+r[6:] if r[4] == "HALL" else r for r in lv.rooms]
    def work(p):
        for m in B1_LEVELS:
            if m.level == k: place(p, m)
        if k == 2:                              # the attic hatch, clear of the soffit and its runs
            for h in B1_ROOF.hatches: draw_attic_hatch(p, h)
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
    for ox, t in ((ox1, 'BUILDING 1 — LEVEL 1 — MECHANICAL PLAN  ·  UNIT 1'),
                  (ox2, 'BUILDING 1 — LEVEL 2 — MECHANICAL PLAN  ·  UNIT 1')):
        title(ox, oy, t)
        # true north beside the title, as A-101 gives each of its plans: the schedules and
        # the notes name walls by the compass
        draw_north(ox+pdfmetrics.stringWidth(t, 'Helvetica-Bold', 11)+0.1*inch+COMPASS/2.0, oy-0.72*inch)
    # the right column: legend, then the three schedules
    rx = ox2+B1_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, rw, kinds=legend_kinds(1))
    # what this sheet draws that the engine's legend has no row for, set as its rows are
    for sample, text in ((lambda pt: draw_panel(p2, None, page=pt),
                          'ACCESS PANEL IN THE SOFFIT, REMOVABLE, AROUND THE AIR HANDLER IT PASSES: NOTE 8'),
                         (lambda pt: draw_drop(p2, None, page=pt),
                          'LINE SETS PASSING BETWEEN LEVELS INSIDE THE WALL, NOTE 2')):
        sample((rx+7, ry+5.6*0.36))
        c.setFillColor(black); c.setFont('Helvetica', 5.6); c.drawString(rx+20, ry, text)
        ry -= 13.0
    ry -= 6
    ry = outdoor_schedule(rx, ry, rw, 1)
    ry = ventilation_schedule(rx, ry, rw, 1)
    ry = termination_schedule(rx, ry, rw, 1)
    assert ry > Y0, 'M-101 right column runs off the sheet'
    # under the plans: the notes across the width the plans take
    by = oy-1.22*inch
    nb = notes(ox1, by, rx-0.3*inch-ox1)
    assert nb > Y0, 'M-101 notes run off the sheet'
    c.showPage()

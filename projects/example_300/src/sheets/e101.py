"""E-101 — Building 1 electrical plans: Level 1 and Level 2 side by side, greyed, with
every device on them; the legend, the panel schedules, the one-line and the notes."""
from lib.draw.page import Sheet, end_plans
from lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import PLAN_L1, PLAN_L2, _b1_level
from src.electrical import (CIRCUITS_HOUSE, CIRCUITS_U1, CIRCUITS_U23, E_HOUSE_1, E_U1_L1, E_U1_L2, E_U23,
                            NEC_UNITS, SERVICES)
from src.mirror import B1_W
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context, legend, notes, one_line, schedule
from lib.draw.electrical_kit import place
from lib.draw.kit import title
from src.sheets.plans import B1_DRAWING


def _level(k, ox, oy):
    """One Building 1 level as an electrical background, its devices on it."""
    plan = PLAN_L1 if k == 1 else PLAN_L2
    lv = _b1_level(k, [], [], [], units=[], u3stair=(k == 1), annotate=False, **B1_DRAWING)
    def devices(p):
        place(p, E_U23, plan, B1_W)                       # Unit 2 on Level 1, Unit 3 on Level 2
        place(p, E_U1_L1 if k == 1 else E_U1_L2)          # Unit 1, in its own page feet
        if k == 1: place(p, E_HOUSE_1)
        grey_context(p, 26, 48, 'S ELM AVENUE', 'REAR YARD  ·  BUILDING 2 BEYOND',
                     'SAGE AVENUE', 'ADJACENT PARCEL')
    lv.overlay = devices
    return draw_level(c, lv, ox, oy)


def sheet_e101():
    sh = Sheet(c, "E-101", "Building 1 — electrical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-48*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+26*Q+1.0*inch
    _level(1, ox1, oy)
    p2 = _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 1 — ELECTRICAL PLAN  ·  UNIT 1 BELOW, UNIT 2')
    title(ox2, oy, 'BUILDING 1 — LEVEL 2 — ELECTRICAL PLAN  ·  UNIT 1 ABOVE, UNIT 3')
    # the right column: legend, then the schedules
    rx = ox2+26*Q+0.45*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, E_U1_L1+E_U1_L2+E_U23+E_HOUSE_1, rw)-6
    ry = schedule(rx, ry, 'UNIT 1 — PANEL U1, 125 A', CIRCUITS_U1, E_U1_L1+E_U1_L2, rw, NEC_UNITS[0], 125)
    ry = schedule(rx, ry, 'UNITS 2 AND 3 — PANELS U2 AND U3, 100 A EACH', CIRCUITS_U23, E_U23, rw, NEC_UNITS[1], 100)
    ry = schedule(rx, ry, 'BUILDING 1 HOUSE — PANEL H, 60 A', CIRCUITS_HOUSE, E_HOUSE_1, rw)
    # Under the plans: the one-line at the left, the notes at the right. Both used to
    # start at oy-1.22 in and ran off the bottom of the drawing area -- the one-line
    # ended at 44.8 and the notes at 45.8 against a Y0 of 54.0, on the issued sheet.
    # They start higher now, which the title above them has room for: its lowest line is
    # the scale at oy-0.94 in.
    by = oy-1.06*inch
    lw = 6.9*inch
    ly = one_line(ox1, by, SERVICES[0], lw)
    nx = ox1+lw+0.3*inch
    ny = notes(nx, by, rx-0.3*inch-nx)
    # M-101, M-102, P-102 and P-103 have carried these asserts all along; the two E
    # sheets never had them, and they carry the most model-driven height in the set --
    # the schedules size themselves from CIRCUITS_*, so one more circuit grows the
    # column. Without this, the block simply walks off the sheet and the build says
    # nothing.
    assert ry > Y0, 'E-101 right column runs off the sheet'
    assert ly > Y0, 'E-101 one-line diagram runs off the sheet'
    assert ny > Y0, 'E-101 notes run off the sheet'
    c.showPage()

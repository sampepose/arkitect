"""E-102 — Building 2 electrical plans: Unit 4 and Unit 5 side by side, greyed, with
every device on them; the legend, the panel schedules, the one-line and the notes."""
from lib.draw.page import Sheet, end_plans
from lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building2 import B2_W, PLAN_B2, b2_level
from src.electrical import CIRCUITS_HOUSE, CIRCUITS_U45, E_HOUSE_2, E_U45, E_U4_ONLY, LEVEL_U4, NEC_UNITS, SERVICES
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context, legend, notes, one_line, schedule
from lib.draw.electrical_kit import place
from lib.draw.kit import title
from src.sheets.plans import draw_u5_stair


def _level(k, ox, oy):
    """One Building 2 level as an electrical background, its devices on it. k is 0 for
       Unit 4 at grade, 1 for Unit 5 above; the Unit 5 stair is drawn on both as A-103
       draws it."""
    lv = b2_level(k+1)
    lv.over_plan = lambda pp, above=(k == 0): draw_u5_stair(pp, B2_W, above=above)
    def devices(p):
        place(p, E_U45+(E_U4_ONLY if k == 0 else []), PLAN_B2, B2_W)
        if k == 0: place(p, E_HOUSE_2)
        grey_context(p, B2_W, 28, 'COURTYARD  ·  FACES BUILDING 1  ·  S ELM AVENUE BEYOND',
                     'PARKING AND ALLEY', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=5.6)
    lv.overlay = devices
    return draw_level(c, lv, ox, oy)


def sheet_e102():
    sh = Sheet(c, "E-102", "Building 2 — electrical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-1.35*inch-28*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+26*Q+1.0*inch
    _level(0, ox1, oy)
    p2 = _level(1, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 2 — LEVEL 1 — ELECTRICAL PLAN  ·  UNIT 4')
    title(ox2, oy, 'BUILDING 2 — LEVEL 2 — ELECTRICAL PLAN  ·  UNIT 5')
    rx = ox2+26*Q+0.45*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, E_U45+E_U4_ONLY+E_HOUSE_2, rw)-6
    ry = schedule(rx, ry, 'UNITS 4 AND 5 — PANELS U4 AND U5, 100 A EACH', CIRCUITS_U45, LEVEL_U4.devices, rw, NEC_UNITS[2], 100)
    ry = schedule(rx, ry, 'BUILDING 2 HOUSE — PANEL H, 60 A', CIRCUITS_HOUSE, E_HOUSE_2, rw)
    # Same start as E-101's, for the same reason: Building 2's one-line is the same
    # drawing with three meter positions instead of four, and the two sheets of a pair
    # read wrong if their blocks sit at different heights.
    by = oy-1.06*inch
    lw = 6.9*inch
    ly = one_line(ox1, by, SERVICES[1], lw)
    nx = ox1+lw+0.3*inch
    ny = notes(nx, by, rx-0.3*inch-nx, see='E-101')
    # E-102's notes are only the SEE E-101 pointer, so they have slack today. The
    # assert is not about today's slack: it is the one this sheet never had while its
    # schedules sized themselves from the circuit lists.
    assert ry > Y0, 'E-102 right column runs off the sheet'
    assert ly > Y0, 'E-102 one-line diagram runs off the sheet'
    assert ny > Y0, 'E-102 notes run off the sheet'
    c.showPage()

"""E-102 — Building 2 electrical plans: Unit 2 and Unit 3 side by side, greyed, with
every device on them; the legend, the panel schedule and the one-line. The notes are
E-101's."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building2 import B2_D, B2_W, PLAN_B2, b2_level
from src.electrical import CIRCUITS_U23, E_B2, E_U2_ONLY, E_U3_ONLY, LEVEL_U2, NEC_UNITS, SERVICES
from src.sheets.a102 import draw_u5_stair
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context, legend, notes, one_line, schedule
from arkitect.lib.draw.electrical_kit import place
from arkitect.lib.draw.kit import title


def _level(k, ox, oy):
    """One Building 2 level as an electrical background, its devices on it. k is 0 for
       Unit 2 at grade, 1 for Unit 3 above; the Unit 3 stair is drawn on both as A-102
       draws it."""
    lv = b2_level(k+1)
    lv.over_plan = lambda pp, above=(k == 0): draw_u5_stair(pp, B2_W, above=above)
    def devices(p):
        place(p, E_B2+(E_U2_ONLY if k == 0 else E_U3_ONLY), PLAN_B2, B2_W)
        grey_context(p, B2_W, B2_D, 'COURTYARD  ·  FACES BUILDING 1  ·  OAK AVENUE BEYOND',
                     'PARKING AND ALLEY', '396 OAK AVE', '404 OAK AVE', top_off=5.6)
    lv.overlay = devices
    return draw_level(c, lv, ox, oy)


def sheet_e102():
    sh = Sheet(c, "E-102", "Building 2 — electrical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-0.9*inch-B2_D*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+B2_W*Q+1.2*inch
    _level(0, ox1, oy)
    p2 = _level(1, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 2 — LEVEL 1 — ELECTRICAL PLAN  ·  UNIT 2')
    title(ox2, oy, 'BUILDING 2 — LEVEL 2 — ELECTRICAL PLAN  ·  UNIT 3')
    rx = ox2+B2_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, E_B2+E_U2_ONLY+E_U3_ONLY, rw)-6
    ry = schedule(rx, ry, 'UNITS 2 AND 3 — PANELS U2 AND U3, %d A EACH' % NEC_UNITS[1][7], CIRCUITS_U23,
                  LEVEL_U2.devices, rw, NEC_UNITS[1], NEC_UNITS[1][7])
    by = oy-1.06*inch
    lw = 4.6*inch
    ly = one_line(ox1, by, SERVICES[1], lw)
    nx = ox1+lw+0.3*inch
    ny = notes(nx, by, rx-0.3*inch-nx, see='E-101')
    assert ry > Y0, 'E-102 right column runs off the sheet'
    assert ly > Y0, 'E-102 one-line diagram runs off the sheet'
    assert ny > Y0, 'E-102 notes run off the sheet'
    c.showPage()

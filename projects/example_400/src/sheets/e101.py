"""E-101 — Building 1 electrical plans: Unit 1's two levels side by side, greyed, with
every device on them; the legend, the panel schedule, the one-line and the notes."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import B1_D, B1_W, LEVEL, b1_level
from src.electrical import CIRCUITS_U1, E_U1_L1, E_U1_L2, NEC_UNITS, SERVICES
from src.sheets.a101 import draw_b1_stair
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context, legend, notes, one_line, schedule
from arkitect.lib.draw.electrical_kit import place
from arkitect.lib.draw.kit import title


def _level(k, ox, oy):
    """One level of the house as an electrical background, its devices on it."""
    lv = b1_level(k)
    lv.over_plan = lambda pp: draw_b1_stair(pp, k)
    def devices(p):
        place(p, E_U1_L1 if k == 1 else E_U1_L2, LEVEL[k]['plan'], B1_W)
        grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'BUILDING 2 AND THE ALLEY BEYOND',
                     '396 OAK AVE', '404 OAK AVE')
    lv.overlay = devices
    return draw_level(c, lv, ox, oy)


def sheet_e101():
    sh = Sheet(c, "E-101", "Building 1 — electrical plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.75*inch-B1_D*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+B1_W*Q+1.2*inch
    _level(1, ox1, oy)
    p2 = _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 1 — ELECTRICAL PLAN  ·  UNIT 1')
    title(ox2, oy, 'BUILDING 1 — LEVEL 2 — ELECTRICAL PLAN  ·  UNIT 1')
    rx = ox2+B1_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(p2, rx, ry, E_U1_L1+E_U1_L2, rw)-6
    ry = schedule(rx, ry, 'UNIT 1 — PANEL U1, %d A' % NEC_UNITS[0][7], CIRCUITS_U1, E_U1_L1+E_U1_L2, rw,
                  NEC_UNITS[0], NEC_UNITS[0][7])
    by = oy-1.06*inch
    lw = 3.4*inch
    ly = one_line(ox1, by, SERVICES[0], lw)
    nx = ox1+lw+0.3*inch
    ny = notes(nx, by, rx-0.3*inch-nx)
    assert ry > Y0, 'E-101 right column runs off the sheet'
    assert ly > Y0, 'E-101 one-line diagram runs off the sheet'
    assert ny > Y0, 'E-101 notes run off the sheet'
    c.showPage()

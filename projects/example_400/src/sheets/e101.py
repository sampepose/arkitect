"""E-101 — Building 1 electrical plans: Unit 1's two levels side by side, greyed, with
every device on them; the legend, the panel schedule, the one-line and the notes."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import B1_D, B1_W, LEVEL
from src.electrical import (CIRCUITS_U1, E_U1_L1, E_U1_L2, NEC_UNITS, SERVICES, SERVICE_REACH,
                            hp1_disconnect, hp1_service_receptacle)
from src.mechanical import B1_LEVELS
from arkitect.lib.draw.page import LAY
from arkitect.lib.symbols import mechanical as ms
from arkitect.lib.units import fmt
from reportlab.lib.colors import black, white
from src.sheets.a101 import b1_trade_level
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import place, grey_context, legend, notes, one_line, schedule
from arkitect.lib.draw.kit import title


def draw_disconnect(p, box=None, page=None):
    """A disconnect on the outside face of a wall: a small box, its handle a bar across it.
       `page` draws the legend's sample at a page point."""
    LAY('E-POWR'); cc = p.c
    cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.6)
    if page is not None:
        X, Y = page; w, h = 4.5, 7.0
    else:
        x0, y0, x1, y1 = box
        X, Y, w, h = p.X((x0+x1)/2.0), p.Y((y0+y1)/2.0), (x1-x0)*p.sc, (y1-y0)*p.sc
    cc.rect(X-w/2.0, Y-h/2.0, w, h, fill=1, stroke=1)
    cc.line(X-w/2.0, Y, X+w/2.0, Y)


def _hp1(p):
    """HP-1 outside the north wall as M-101 draws it, its disconnect beside it and, along
       the wall, where its 210.63 receptacle is."""
    m = next(m for m in B1_LEVELS if m.level == 1)
    ms.draw_odu(p, m.hp_box, m.hp)
    a0, a1, dp = hp1_disconnect()
    draw_disconnect(p, (-dp, a0, 0.0, a1))
    wp, run = hp1_service_receptacle()
    assert run <= SERVICE_REACH, 'E-101 would print a 210.63 receptacle out of reach'
    x, y, w, h = m.hp_box
    LAY('E-ANNO-TEXT'); cc = p.c; cc.setFillColor(black); cc.setFont('Helvetica', 4.2)
    cc.saveState(); cc.translate(p.X(x)-13.0, p.Y((y+a1)/2.0)); cc.rotate(90)
    cc.drawCentredString(0, -1.5, "%s'S DISCONNECT BESIDE IT, NOTE 4 \u00b7 NEC 210.63 SERVICE RECEPTACLE: THE REAR WP, %s ALONG THE WALLS"
                         % (m.hp, fmt(run)))
    cc.restoreState()


def _level(k, ox, oy):
    """One level of the house as an electrical background, its devices on it."""
    lv = b1_trade_level(k)
    def devices(p):
        place(p, E_U1_L1 if k == 1 else E_U1_L2, LEVEL[k]['plan'], B1_W)
        if k == 1:
            _hp1(p)
        grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'BUILDING 2 AND THE ALLEY BEYOND',
                     '396 OAK AVE', '404 OAK AVE', side_at=(8.0, None))     # HP-1 holds the wall's middle
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
    ry = legend(p2, rx, ry, E_U1_L1+E_U1_L2, rw)
    # what this sheet draws that the device legend has no row for, set as its rows are
    for sample, text in ((lambda pt: ms.draw_odu(p2, None, '', page=pt), 'HEAT PUMP OUTDOOR UNIT, M-101'),
                         (lambda pt: draw_disconnect(p2, page=pt), 'DISCONNECT, WITHIN SIGHT OF ITS OUTDOOR UNIT, NOTE 4')):
        sample((rx+6, ry+5.6*0.36))
        c.setFillColor(black); c.setFont('Helvetica', 5.6); c.drawString(rx+20, ry, text)
        ry -= 14.0
    ry -= 6
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

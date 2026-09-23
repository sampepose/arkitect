"""Placing an electrical device on a plan: the symbol, stood off its wall, and its home-run arrow.

Plan feet in, page points out, through the PlanDraw or the canvas stand-in it is handed; what is
drawn where is the project's. It was word for word in each project's copy of the sheet.
"""
import math
from reportlab.lib.colors import black
from lib.draw.page import LAY
from lib.symbols import electrical as es


# a dedicated circuit's device carries a short home-run arrow toward its panel
HOME_RUN = ('range', 'dryer', 'dw', 'fridge', 'wh', 'head')


_SWAP = {'e': 'w', 'w': 'e'}


def _arrow(p, X0, Y0, X1, Y1):
    LAY('E-POWR'); cc = p.c
    cc.setStrokeColor(black); cc.setLineWidth(0.5); cc.line(X0, Y0, X1, Y1)
    an = math.atan2(Y1-Y0, X1-X0)
    for dd in (0.45, -0.45):
        cc.line(X1, Y1, X1-4.5*math.cos(an+dd), Y1-4.5*math.sin(an+dd))


def place(p, devs, plan=None, W=None):
    """Draw a device list on PlanDraw p. With `plan` and `W` the list is in a regridded,
       mirrored unit's model feet (Units 2/3, 4/5) and goes through the same map as its
       rooms: page x = W - plan.x, and a wall to the device's east is now to its west.
       Without them the list is already in page feet (Unit 1, the house lists)."""
    pts = []
    for d in devs:
        if plan is not None:
            x, y = W-plan.x(d.x, d.y), plan.y(d.y)
            m = _SWAP.get(d.mount, d.mount)
        else:
            x, y, m = d.x, d.y, d.mount
        es.draw_device(p, x, y, d.kind, m, d.tag, d.circuit)
        sx, sy = es.stand_off(x, y, m)
        pts.append((d.kind, p.X(sx), p.Y(sy)))
    panel = [(X, Y) for k, X, Y in pts if k == 'panel']
    if panel:
        PX, PY = panel[0]
        for k, X, Y in pts:
            if k in HOME_RUN:
                dx, dy = PX-X, PY-Y; L = math.hypot(dx, dy)
                if L > 1: _arrow(p, X+dx/L*5.5, Y+dy/L*5.5, X+dx/L*16, Y+dy/L*16)

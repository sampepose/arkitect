"""The mechanical symbols, for M-101 and M-102.

Two kinds of thing. The EQUIPMENT — indoor heads, outdoor units, fans — is drawn at its
real size in plan feet, because a 32" wall head is something the framer leaves room
for. The RUNS — ducts and line sets — and the caps that end them are line work with
weights and dashes in points, so they read the same at any scale, like the electrical
devices. Everything is placed in page feet through the PlanDraw; nothing here knows
which unit it is drawing.
"""
import math
from lib.draw.page import LAY
from reportlab.lib.colors import black, white

# what each symbol on the sheet is, in the order the legend lists them
KINDS = [
    ('head',   'HEAT-PUMP INDOOR WALL HEAD, ONE PER BEDROOM AND LIVING SPACE'),
    ('ahu',    'HEAT-PUMP AIR HANDLER, CONCEALED IN THE SOFFIT DRAWN'),
    ('reg',    'SUPPLY REGISTER; A RETURN GRILLE IS MARKED RA'),
    ('tstat',  'THERMOSTAT OR WALL CONTROL, ONE PER SYSTEM'),
    ('odu',    'HEAT-PUMP OUTDOOR UNIT ON ITS WALL BRACKET, AS C-101 PLACES IT'),
    ('fanc',   'BATH FAN, CONTINUOUS DUTY: THE WHOLE-DWELLING VENTILATION FAN'),
    ('fan',    'BATH EXHAUST FAN, INTERMITTENT, SWITCHED'),
    ('duct',   'EXHAUST DUCT, 4" SMOOTH RIGID METAL UNLESS MARKED ON THE RUN'),
    ('cap',    'WALL CAP WITH BACKDRAFT DAMPER; THE MARK IS THE SCHEDULE\'S'),
    ('roof',   'ROOF CAP WITH BACKDRAFT DAMPER, FLASHED'),
    ('ls',     'REFRIGERANT LINE SET AND CONDENSATE DRAIN, CONCEALED, DIAGRAMMATIC'),
    ('sleeve', 'LINE-SET SLEEVE THROUGH THE WALL ABOVE THE OUTDOOR UNIT, SEALED'),
]
LAYER = {'head': 'M-HVAC-EQPM', 'ahu': 'M-HVAC-EQPM', 'reg': 'M-HVAC-DUCT', 'tstat': 'M-HVAC-EQPM',
         'odu': 'M-HVAC-EQPM',
         'fanc': 'M-HVAC-EQPM', 'fan': 'M-HVAC-EQPM',
         'duct': 'M-EXHS-DUCT', 'cap': 'M-EXHS-DUCT', 'roof': 'M-EXHS-DUCT',
         'ls': 'M-HVAC-PIPE', 'sleeve': 'M-HVAC-PIPE'}
HEAD_L, HEAD_D = 2.7, 0.75          # a wall head in plan feet: about 32" long, 9" deep
AHU_L, AHU_D = 3.75, 2.0            # a concealed air handler: about 45" long, 24" deep, 8" tall
REG_L, REG_D = 1.0, 0.5             # a supply register, 12" x 6"
R = 3.6                             # the fan circle, points


def _text(c, X, Y, t, size, bold=False):
    c.setFillColor(black); c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawCentredString(X, Y-size*0.36, t)


def draw_head(p, x, y, mount, page=None):
    """The head flush to its wall, its length along the wall, its depth into the room."""
    LAY(LAYER['head']); c = p.c
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    if page is not None:
        X, Y = page; c.rect(X-7, Y-2.2, 14, 4.4, fill=1, stroke=1); _text(c, X, Y, 'IDU', 3.0, True); return
    if mount in ('n', 'w5'):   rx, ry, rw, rh = x-HEAD_L/2, y, HEAD_L, HEAD_D
    elif mount in ('s', 'w5s'): rx, ry, rw, rh = x-HEAD_L/2, y-HEAD_D, HEAD_L, HEAD_D
    elif mount == 'w':          rx, ry, rw, rh = x, y-HEAD_L/2, HEAD_D, HEAD_L
    else:                       rx, ry, rw, rh = x-HEAD_D, y-HEAD_L/2, HEAD_D, HEAD_L
    c.rect(p.X(rx), p.Y(ry+rh), rw*p.sc, rh*p.sc, fill=1, stroke=1)
    cx, cy = p.X(rx+rw/2), p.Y(ry+rh/2)
    if rw >= rh: _text(c, cx, cy, 'IDU', 3.4, True)
    else:
        c.saveState(); c.translate(cx, cy); c.rotate(90); _text(c, 0, 0, 'IDU', 3.4, True); c.restoreState()


def draw_ahu(p, x, y, mark='', horiz=True, page=None):
    """A concealed air handler, hung in the soffit drawn: its cabinet in plan, dashed,
       with its mark. It is above the ceiling, so the outline is what the soffit hides."""
    LAY(LAYER['ahu']); c = p.c
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    if page is not None:
        X, Y = page; c.rect(X-8, Y-3, 16, 6, fill=1, stroke=1); _text(c, X, Y, 'AHU', 3.0, True); return
    w, d = (AHU_L, AHU_D) if horiz else (AHU_D, AHU_L)
    c.setDash(3, 2)
    c.rect(p.X(x-w/2.0), p.Y(y+d/2.0), w*p.sc, d*p.sc, fill=1, stroke=1)
    c.setDash()
    if mark: _text(c, p.X(x), p.Y(y), mark, 3.6, True)


def draw_register(p, x, y, mark='', horiz=True, page=None):
    """A supply register in the ceiling, or a return grille where the mark says RA."""
    LAY(LAYER['reg']); c = p.c
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.6)
    if page is not None:
        X, Y = page
        c.rect(X-6, Y-3, 12, 6, fill=1, stroke=1)
        for k in (-2, 0, 2): c.line(X+k, Y-3, X+k, Y+3)
        return
    w, d = (REG_L, REG_D) if horiz else (REG_D, REG_L)
    c.rect(p.X(x-w/2.0), p.Y(y+d/2.0), w*p.sc, d*p.sc, fill=1, stroke=1)
    n = 3
    for k in range(1, n):                      # the blades, across the register's length
        if horiz:
            xx = p.X(x-w/2.0+w*k/n); c.line(xx, p.Y(y-d/2.0), xx, p.Y(y+d/2.0))
        else:
            yy = p.Y(y-d/2.0+d*k/n); c.line(p.X(x-w/2.0), yy, p.X(x+w/2.0), yy)
    if mark: _text(c, p.X(x), p.Y(y)-5.0, mark, 3.0)


def draw_tstat(p, x, y, page=None):
    """The thermostat on its wall: a small square with a T, as the E sheets draw it."""
    LAY(LAYER['tstat']); c = p.c
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.6)
    if page is not None:
        X, Y = page; c.rect(X-3, Y-3, 6, 6, fill=1, stroke=1); _text(c, X, Y, 'T', 3.4, True); return
    s = 0.55
    c.rect(p.X(x-s/2.0), p.Y(y+s/2.0), s*p.sc, s*p.sc, fill=1, stroke=1)
    _text(c, p.X(x), p.Y(y), 'T', 3.4, True)


def draw_odu(p, rect, mark, page=None):
    """The outdoor unit as a box outside the wall with its fan, and its C-101 mark."""
    LAY(LAYER['odu']); c = p.c
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    if page is not None:
        X, Y = page; c.rect(X-7, Y-4, 14, 8, fill=1, stroke=1); c.circle(X, Y, 2.6, fill=0, stroke=1); return
    x, y, w, h = rect
    c.rect(p.X(x), p.Y(y+h), w*p.sc, h*p.sc, fill=1, stroke=1)
    cx, cy = p.X(x+w/2), p.Y(y+h/2)
    c.circle(cx, cy, min(w, h)*p.sc*0.38, fill=0, stroke=1)
    # the mark on the box's OUTER face, away from the wall and whatever is labelled on it
    LAY('M-ANNO-TEXT'); c.setFont('Helvetica-Bold', 4.6); c.setFillColor(black)
    if w >= h: c.drawCentredString(cx, p.Y(y+h)-6.5, mark)
    else:
        c.saveState(); c.translate(p.X(x+w)+4.5 if x > 5 else p.X(x)-4.5, cy); c.rotate(90)
        c.drawCentredString(0, -1.6, mark); c.restoreState()


def draw_fan(p, x, y, cont, mark='', page=None):
    LAY(LAYER['fanc' if cont else 'fan']); c = p.c
    X, Y = page if page is not None else (p.X(x), p.Y(y))
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.6)
    c.circle(X, Y, R, fill=1, stroke=1)
    c.line(X-R, Y, X+R, Y); c.line(X, Y-R, X, Y+R)
    _text(c, X+R+3.6, Y+2.2, 'EF', 3.4, True)
    if cont:
        c.setFont('Helvetica-Bold', 3.2); c.drawRightString(X-R-1.0, Y+2.4, 'C')
    if mark:
        LAY('M-ANNO-TEXT'); c.setFont('Helvetica', 3.4); c.setFillColor(black)
        c.drawString(X+R+1.6, Y-4.6, mark)


def _polyline(c, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        c.line(x0, y0, x1, y1)


def draw_duct(p, pts, kind='duct', size='', page=None):
    """A duct (solid, heavy) or a line set (dash-dot) along a polyline in page feet;
       `size` is written beside its longest leg. The concentric vent this also drew went
       with the fuel gas: an electric storage heater vents nothing."""
    LAY(LAYER[kind]); c = p.c
    P = pts if page else [(p.X(q[0]), p.Y(q[1])) for q in pts]
    c.setStrokeColor(black); c.setFillColor(black)
    if kind == 'ls':
        c.setLineWidth(0.6); c.setDash([5, 1.6, 1.2, 1.6], 0); _polyline(c, P); c.setDash()
    else:
        c.setLineWidth(1.3); _polyline(c, P)
    if size and len(P) > 1:
        (x0, y0), (x1, y1) = max(zip(P, P[1:]), key=lambda s: math.hypot(s[1][0]-s[0][0], s[1][1]-s[0][1]))
        LAY('M-ANNO-TEXT'); c.setFont('Helvetica', 3.4); c.setFillColor(black)
        mx, my = (x0+x1)/2, (y0+y1)/2
        if abs(x1-x0) >= abs(y1-y0): c.drawCentredString(mx, my+2.6, size)
        else:
            c.saveState(); c.translate(mx-2.6, my); c.rotate(90); c.drawCentredString(0, 0, size); c.restoreState()




def draw_cap(p, x, y, orient, mark, page=None):
    """A wall cap on the wall line: a small hood pointing out of the building. `orient`
       is 'v' for a side wall (the hood points in x) or 'h' (in y); which way out is
       read from which edge of the plan the point is on."""
    LAY(LAYER['cap']); c = p.c
    if page is not None:
        X, Y = page; dx, dy = 1.0, 0.0
    else:
        X, Y = p.X(x), p.Y(y)
        dx, dy = ((1.0 if x > p.W/2 else -1.0), 0.0) if orient == 'v' else (0.0, (-1.0 if y > p.D/2 else 1.0))
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    s = 4.2
    pth = c.beginPath()
    pth.moveTo(X-dy*s, Y+dx*s); pth.lineTo(X+dx*s*1.4, Y+dy*s*1.4); pth.lineTo(X+dy*s, Y-dx*s); pth.close()
    c.drawPath(pth, fill=1, stroke=1)
    if mark:
        # 26 pt out: past an outdoor unit bracketed to the same wall (1'-1" deep) and past
        # the grey context string that stands 1'-0" off every plan
        LAY('M-ANNO-TEXT'); c.setFont('Helvetica-Bold', 4.0); c.setFillColor(black)
        tx, ty = X+dx*26, Y+dy*(s*1.4+3)
        if dx > 0: c.drawString(tx, ty-1.5, mark)
        elif dx < 0: c.drawRightString(tx, ty-1.5, mark)
        else: c.drawCentredString(tx, ty-(4.5 if dy < 0 else 0.0), mark)


def draw_roofcap(p, x, y, mark, page=None):
    LAY(LAYER['roof']); c = p.c
    X, Y = page if page is not None else (p.X(x), p.Y(y))
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    c.circle(X, Y, 4.0, fill=1, stroke=1)
    c.line(X-2.8, Y-2.8, X+2.8, Y+2.8); c.line(X-2.8, Y+2.8, X+2.8, Y-2.8)
    if mark:
        LAY('M-ANNO-TEXT'); c.setFont('Helvetica-Bold', 4.0); c.setFillColor(black)
        c.drawString(X+5.5, Y-1.5, mark)


def draw_sleeve(p, x, y, label='', page=None, below=False):
    LAY(LAYER['sleeve']); c = p.c
    X, Y = page if page is not None else (p.X(x), p.Y(y))
    c.setStrokeColor(black); c.setFillColor(black); c.setLineWidth(0.6)
    c.circle(X, Y, 2.2, fill=1, stroke=1)
    if label:
        LAY('M-ANNO-TEXT'); c.setFont('Helvetica', 3.4); c.setFillColor(black)
        if below: c.drawCentredString(X, Y-7.0, label)
        elif x > p.W/2: c.drawRightString(X-4, Y-1.2, label)
        else: c.drawString(X+4, Y-1.2, label)


def legend(p, x, y, size=5.6, lead=13.0, kinds=None):
    """The legend, one row per kind from the page point (x, y) down; returns the next y.
       `kinds` is what this project draws: a set has no row for a symbol it never uses."""
    c = p.c
    c.setFillColor(black); c.setFont('Helvetica-Bold', size+2.4)
    c.drawString(x, y, 'MECHANICAL LEGEND'); y -= lead+3
    for k, text in ([kt for kt in KINDS if kt[0] in kinds] if kinds is not None else KINDS):
        pt = (x+7, y+size*0.36)
        if k == 'head': draw_head(p, 0, 0, 'n', page=pt)
        elif k == 'ahu': draw_ahu(p, 0, 0, page=pt)
        elif k == 'reg': draw_register(p, 0, 0, page=pt)
        elif k == 'tstat': draw_tstat(p, 0, 0, page=pt)
        elif k == 'odu': draw_odu(p, None, '', page=pt)
        elif k in ('fanc', 'fan'): draw_fan(p, 0, 0, k == 'fanc', page=pt)
        elif k in ('duct', 'ls'): draw_duct(p, [(pt[0]-7, pt[1]), (pt[0]+7, pt[1])], k, page=True)
        elif k == 'cap': draw_cap(p, 0, 0, 'v', '', page=(pt[0]-3, pt[1]))
        elif k == 'roof': draw_roofcap(p, 0, 0, '', page=pt)
        elif k == 'sleeve': draw_sleeve(p, 0, 0, page=pt)
        c.setFillColor(black); c.setFont('Helvetica', size); c.drawString(x+20, y, text)
        y -= lead
    return y

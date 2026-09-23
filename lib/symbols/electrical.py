"""Electrical equipment inside the units, and the working space it requires.

The exterior equipment — the meter banks and the heat-pump outdoor units — is not
drawn with these: it is site work, laid out and checked on C-101 from SVC_EQUIP.
"""
from .base import Symbol, ClearSpace, symbol
from reportlab.lib.colors import black


@symbol
class Panel(Symbol):
    """Load center, marked along its length because the box is only inches deep."""
    kinds = ('panel',)

    def draw(s):
        c, X, Y, W, H = s.c, s.X, s.Y, s.W, s.H
        s.box()
        c.setFillColor(black); c.setFont('Helvetica-Bold', 4.8)
        c.saveState(); c.translate(X + W / 2, Y + H / 2); c.rotate(90)
        c.drawCentredString(0, -1.7, 'PANEL'); c.restoreState()


@symbol
class PanelClearance(ClearSpace):
    """Electrical-panel working space: long-dash boundary.

    30" wide by 36" deep from the panel face, and nothing may be run through it —
    NEC 110.26(A) for the space, 110.26(E) for keeping piping out of it.
    """
    kinds = ('clear',)
    dash = (6, 2.5)
    caption_at = 0.60


# ---------------- the device symbols, for E-101 and E-102 ----------------
# Points, not rectangles, so they do not go through the registry above. Their sizes are
# in POINTS so a receptacle reads the same at any plan scale, like the concrete stipple.
# A device is placed at a plan point and a MOUNT: which side of it the wall is on ('n'
# is the smaller-y edge, the plan being y-down; 's', 'e', 'w' likewise), 'c' for the
# ceiling, or 'w5' / 'w5s' for the furred chase face at Building 1's separation, which
# is a wall to the device's north (Units 2/3) or south (Unit 1) that is not W4. Wall
# devices stand OFF into the room.
from lib.draw.page import LAY
from reportlab.lib.colors import white

R = 3.0            # the receptacle and alarm circle radius, points
OFF = 0.30         # a wall device stands this far into the room, plan feet

_KIND_NAMES = ('dup', 'gfci', 'wp', 'range', 'dryer', 'dw', 'fridge', 'wh', 'head', 'ahu', 'tstat',
               'sw', 'sw3', 'lt', 'rec', 'fanc', 'fan', 'ext', 'sd', 'co', 'panel', 'jbox')
_LIGHT = ('sw', 'sw3', 'lt', 'rec', 'fanc', 'fan', 'ext', 'head', 'ahu', 'tstat')
LAYER = {k: ('E-LITE' if k in _LIGHT else 'E-ALRM' if k in ('sd', 'co') else 'E-POWR')
         for k in _KIND_NAMES}
# which way a mount stands the device off its wall, in plan feet
STANDOFF = {'n': (0, OFF), 's': (0, -OFF), 'e': (-OFF, 0), 'w': (OFF, 0),
            'w5': (0, OFF), 'w5s': (0, -OFF), 'c': (0, 0)}


def stand_off(x, y, mount):
    dx, dy = STANDOFF[mount]
    return x+dx, y+dy


def _text(c, X, Y, t, size, bold=False):
    c.setFillColor(black); c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawCentredString(X, Y-size*0.36, t)


def _disc(c, X, Y, r):
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.55)
    c.circle(X, Y, r, fill=1, stroke=1)


def draw_device(p, x, y, kind, mount, tag='', circuit=None, page=None, label=True):
    """One device at plan (x, y) with the given mount, or at page point `page`.

    The tag (a letter pairing a switch with what it controls) goes upper right of the
    symbol and the circuit number lower right; a switch shows only its tag."""
    LAY(LAYER[kind])
    c = p.c
    if page is None:
        sx, sy = stand_off(x, y, mount)
        X, Y = p.X(sx), p.Y(sy)
    else:
        X, Y = page
    horiz = mount in ('e', 'w')          # the wall runs north-south: duplex bars lie flat
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.55)
    if kind in ('dup', 'gfci', 'wp', 'dw', 'fridge', 'wh'):
        _disc(c, X, Y, R)
        for s in (-1.05, 1.05):           # the two bars of a duplex, across the wall line
            if horiz: c.line(X-R-1.3, Y+s, X+R+1.3, Y+s)
            else:     c.line(X+s, Y-R-1.3, X+s, Y+R+1.3)
        lab = {'gfci': 'GFCI', 'wp': 'WP', 'dw': 'DW', 'fridge': 'REF', 'wh': 'WH'}.get(kind)
        if lab and label: _text(c, X, Y-R-4.2, lab, 3.0)
    elif kind in ('range', 'dryer'):
        c.rect(X-R, Y-R, 2*R, 2*R, fill=1, stroke=1)
        _text(c, X, Y, 'R' if kind == 'range' else 'D', 3.8, bold=True)
    elif kind == 'head':
        c.rect(X-2*R, Y-0.7*R, 4*R, 1.4*R, fill=1, stroke=1)
        _text(c, X, Y, 'HP', 3.2, bold=True)
    elif kind == 'ahu':                   # a concealed air handler, hung in a soffit
        c.rect(X-2.4*R, Y-0.9*R, 4.8*R, 1.8*R, fill=1, stroke=1)
        _text(c, X, Y, 'AHU', 3.2, bold=True)
    elif kind == 'tstat':                 # the system's thermostat or wall control
        c.rect(X-R, Y-R, 2*R, 2*R, fill=1, stroke=1)
        _text(c, X, Y, 'T', 3.8, bold=True)
    elif kind in ('sw', 'sw3'):
        _text(c, X, Y, 'S', 5.2, bold=True)
        if kind == 'sw3':
            c.setFont('Helvetica', 3.4); c.drawString(X+2.0, Y-3.4, '3')
    elif kind == 'lt':
        _disc(c, X, Y, R)
        c.line(X-R, Y, X+R, Y); c.line(X, Y-R, X, Y+R)
    elif kind == 'rec':
        _disc(c, X, Y, R)
        c.setFillColor(black); c.circle(X, Y, 1.0, fill=1, stroke=0)
    elif kind in ('fanc', 'fan'):
        _disc(c, X, Y, R+0.6)
        _text(c, X, Y, 'F', 3.8, bold=True)
        if kind == 'fanc':
            c.setFont('Helvetica-Bold', 3.2); c.drawRightString(X-R-1.2, Y+2.4, 'C')
    elif kind == 'ext':
        import math
        c.setFillColor(white)
        pth = c.beginPath(); pth.moveTo(X-R, Y)
        for i in range(1, 9):                       # a half disc, as eight chords
            a = math.pi*(1-i/8.0); pth.lineTo(X+R*math.cos(a), Y+R*math.sin(a))
        pth.close(); c.drawPath(pth, fill=1, stroke=1)
    elif kind == 'sd':
        _disc(c, X, Y, R+1.0); _text(c, X, Y, 'SD', 3.0, bold=True)
    elif kind == 'co':
        _disc(c, X, Y, R+1.0); _text(c, X, Y, 'CO', 3.0, bold=True)
    elif kind == 'jbox':
        c.rect(X-R, Y-R, 2*R, 2*R, fill=1, stroke=1)
        _text(c, X, Y, 'J', 3.8, bold=True)
    elif kind == 'panel':
        c.setFillColor(black)
        if horiz: c.rect(X-1.3, Y-1.6*R, 2.6, 3.2*R, fill=1, stroke=1)
        else:     c.rect(X-1.6*R, Y-1.3, 3.2*R, 2.6, fill=1, stroke=1)
    else:
        raise KeyError('no such device kind %r' % kind)
    LAY('E-ANNO-TEXT'); c.setFillColor(black); c.setFont('Helvetica', 3.4)
    if tag:
        c.drawString(X+R+1.6, Y+1.8, str(tag))
    if circuit is not None and kind not in ('sw', 'sw3', 'panel'):
        c.drawString(X+R+1.6, Y-4.4, str(circuit))


def legend(p, x, y, kinds, descriptions, size=5.6, lead=14.0):
    """The legend, one row per kind from the page point (x, y) down; returns the next y.

       `descriptions` maps a kind to the sentence printed beside it. It is supplied
       rather than held here: the symbol is the same in every jurisdiction and the
       sentence is not.
    """
    c = p.c
    c.setFillColor(black); c.setFont('Helvetica-Bold', size+2.4)
    c.drawString(x, y, 'ELECTRICAL LEGEND'); y -= lead+3
    for k in kinds:
        draw_device(p, 0, 0, k, 'n' if k not in ('panel',) else 'e', page=(x+6, y+size*0.36))
        c.setFillColor(black); c.setFont('Helvetica', size)
        c.drawString(x+20, y, descriptions[k])
        y -= lead
    return y

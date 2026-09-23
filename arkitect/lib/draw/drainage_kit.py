"""The under-slab drainage sheet's drawing vocabulary: a drain line, a sleeve, a flow arrow,
a stack's tag, a slab penetration, a cleanout, a bearing strip's band, a dimension between
two points. Plan feet in, page points out, through the PlanDraw it is handed.
"""
import math
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from arkitect.lib.model import drains
from arkitect.lib.draw.plumbing_kit import UNDER_DASH
from arkitect.lib.draw.page import GREY, LAY, LGREY
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.draw.kit import c, _fits


WIDTH = {'1-1/2': 0.9, '2': 1.1, '3': 1.5, '4': 2.0}      # a drain's pen, by size


def _P(p, xy):
    return p.X(xy[0]), p.Y(xy[1])


def _text(cc, X, Y, t, size, bold=False, anchor='c', col=black):
    LAY('P-ANNO-TEXT'); cc.setFillColor(col); cc.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    if anchor == 'c': cc.drawCentredString(X, Y, t)
    elif anchor == 'l': cc.drawString(X, Y, t)
    else: cc.drawRightString(X, Y, t)


def drain_line(cc, pts, size):
    LAY('P-SANR-UNDR'); cc.setStrokeColor(black); cc.setLineWidth(WIDTH[size]); cc.setDash()
    for a, b in zip(pts, pts[1:]): cc.line(a[0], a[1], b[0], b[1])


def flow_arrow(cc, a, b, at=0.62, size=4.2):
    """A filled arrowhead on segment a -> b, pointing the way the drain falls."""
    LAY('P-SANR-UNDR')
    dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy)
    if L < 1e-6: return
    ux, uy = dx/L, dy/L
    tx, ty = a[0]+dx*at, a[1]+dy*at
    pth = cc.beginPath()
    pth.moveTo(tx+ux*size, ty+uy*size)
    pth.lineTo(tx-uy*size*0.55, ty+ux*size*0.55)
    pth.lineTo(tx+uy*size*0.55, ty-ux*size*0.55)
    pth.close()
    cc.setFillColor(black); cc.setStrokeColor(black); cc.setLineWidth(0.3); cc.drawPath(pth, fill=1, stroke=1)


def junction(cc, X, Y):
    LAY('P-SANR-UNDR'); cc.setFillColor(black); cc.circle(X, Y, 1.6, fill=1, stroke=0)


def pen_mark(cc, X, Y, mark):
    """A numbered circle: the slab penetration schedule's key."""
    LAY('P-SANR-FIXT'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.7); cc.setDash()
    cc.circle(X, Y, 4.6, fill=1, stroke=1)
    _text(cc, X, Y-1.3, str(mark), 3.8, bold=True)


def stack_tag(cc, X, Y, name):
    """A hexagon with the stack's letter, at the stack in its wall."""
    LAY('P-SANR-FIXT'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.8); cc.setDash()
    r = 5.2
    pth = cc.beginPath()
    for k in range(6):
        a = math.pi/6+k*math.pi/3
        (pth.moveTo if k == 0 else pth.lineTo)(X+r*math.cos(a), Y+r*math.sin(a))
    pth.close(); cc.drawPath(pth, fill=1, stroke=1)
    _text(cc, X, Y-1.5, name, 4.4, bold=True)


def box_out(cc, X, Y, W, H):
    LAY('P-SANR-FIXT'); cc.setStrokeColor(black); cc.setLineWidth(0.6); cc.setDash(3, 1.5)
    cc.rect(X, Y, W, H, fill=0, stroke=1); cc.setDash()


def cleanout(cc, X, Y):
    LAY('P-SANR-FIXT'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.7); cc.setDash()
    cc.circle(X, Y, 4.6, fill=1, stroke=1)
    _text(cc, X, Y-1.2, 'CO', 3.2, bold=True)


def strip_band(p, rect, label):
    """One of S-101's thickened strips, light grey with its name, so the drains' clearances read."""
    LAY('S-FNDN'); cc = p.c
    x, y, w, h = rect
    cc.setFillColor(LGREY); cc.setStrokeColor(GREY); cc.setLineWidth(0.5); cc.setDash(3, 2)
    cc.rect(p.X(x), p.Y(y+h), w*p.sc, h*p.sc, fill=1, stroke=1); cc.setDash()
    cx, cy = p.X(x+w/2.0), p.Y(y+h/2.0)
    if w >= h:
        _text(cc, cx, cy-1.4, label, 4.0, col=GREY)
    else:
        cc.saveState(); cc.translate(cx, cy); cc.rotate(90); _text(cc, 0, -1.4, label, 4.0, col=GREY); cc.restoreState()
    cc.setFillColor(black); cc.setStrokeColor(black)


def sleeve_line(cc, pts, half=2.4):
    """A water line's sleeve at a crossing, OPC 603.2: a grey casing either side of the
       line, closed at both ends."""
    LAY('P-DOMW-UNDR'); cc.setStrokeColor(GREY); cc.setLineWidth(0.5); cc.setDash()
    def normal(a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy)
        return -dy/L*half, dx/L*half
    for a, b in zip(pts, pts[1:]):
        nx, ny = normal(a, b)
        cc.line(a[0]+nx, a[1]+ny, b[0]+nx, b[1]+ny); cc.line(a[0]-nx, a[1]-ny, b[0]-nx, b[1]-ny)
    for a, b in ((pts[0], pts[1]), (pts[-1], pts[-2])):
        nx, ny = normal(a, b)
        cc.line(a[0]+nx, a[1]+ny, a[0]-nx, a[1]-ny)
    cc.setStrokeColor(black)


def _at(line, t):
    """The point `t` feet along a polyline."""
    for a, b in zip(line, line[1:]):
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        if t <= L+1e-9: return (a[0]+(b[0]-a[0])*t/L, a[1]+(b[1]-a[1])*t/L)
        t -= L
    return line[-1]


def _between(line, lo, hi):
    """The polyline between two distances along it."""
    pts, acc = [_at(line, lo)], 0.0
    for a, b in zip(line, line[1:]):
        acc += math.hypot(b[0]-a[0], b[1]-a[1])
        if lo < acc < hi: pts.append(b)
    return pts+[_at(line, hi)]


def _dim(cc, A, B, Y, t):
    """A small grey dimension along the water, A to B at page height Y."""
    LAY('P-ANNO-DIMS'); cc.setStrokeColor(GREY); cc.setLineWidth(0.3); cc.setDash()
    cc.line(A, Y, B, Y); cc.line(A, Y-1.5, A, Y+1.5); cc.line(B, Y-1.5, B, Y+1.5)
    cc.setStrokeColor(black)
    _text(cc, (A+B)/2.0, Y+1.2, t, 2.8, col=GREY)


S = 5.6                                   # the text size the legend, tables and notes share


def notes(x, y, width, cols=2, size=S, lead=7.4, *, notes_text):
    LAY('P-ANNO-TEXT')
    gap = 0.18*inch
    cw = (width-gap*(cols-1))/cols
    lines = wrap_notes(notes_text(), cw, size)
    per = -(-len(lines)//cols)
    _text(c, x, y, 'SANITARY NOTES', 7.2, bold=True, anchor='l'); y -= 3
    c.setLineWidth(0.6); c.setStrokeColor(black); c.line(x, y, x+width, y); y -= lead+2
    c.setFont('Helvetica', size); c.setFillColor(black)
    top = y
    for k in range(cols):
        yy = top
        for t in lines[k*per:(k+1)*per]:
            _fits(t, 'Helvetica', size, cw, 'sanitary note')
            c.drawString(x+k*(cw+gap), yy, t); yy -= lead
    return top-per*lead


def _serves_text(b, pn, *, fix):
    if pn.kind == 'stack':
        s = drains.stack_by_name(b, pn.serves)
        units = sorted({u for u, _l, _k in s.serves}, key=lambda t: int(t.split()[-1]))
        return 'STACK %s — %s' % (s.name, ' AND '.join(units) if len(units) < 3 else 'UNITS '+', '.join(u.split()[-1] for u in units))
    if pn.kind == 'co': return 'BUILDING DRAIN, AT ITS TURN'
    if pn.kind == 'exit': return 'BUILDING DRAIN'
    parts = []
    for u, _l, kinds in pn.serves:
        parts.append('%s %s' % (u, ' + '.join(fix[k] for k in kinds)))
    return '; '.join(parts)


def water_line(cc, pts):
    """The water below the slab, P-102 / P-103's, in grey: here to be kept off, not built."""
    LAY('P-DOMW-UNDR'); cc.setStrokeColor(GREY); cc.setLineWidth(0.8); cc.setDash(UNDER_DASH, 0)
    for a, b in zip(pts, pts[1:]): cc.line(a[0], a[1], b[0], b[1])
    cc.setDash(); cc.setStrokeColor(black)

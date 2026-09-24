"""The water-supply sheets' drawing vocabulary: cold, hot and under-slab lines, a riser, a
valve, a meter, a manifold, a run's label. Plan feet in, page points out, through the
PlanDraw it is handed; what is drawn where is the project's.
"""
import math
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
from arkitect.lib.draw.page import LAY
from arkitect.lib.model import water


HOT_DASH = [3, 1.5]


UNDER_DASH = [7, 2, 1.5, 2]


def _poly(cc, pts):
    for a, b in zip(pts, pts[1:]):
        cc.line(a[0], a[1], b[0], b[1])


def cold_line(cc, pts, width=0.8):
    LAY('P-DOMW-COLD'); cc.setStrokeColor(black); cc.setLineWidth(width); cc.setDash()
    _poly(cc, pts)


def hot_line(cc, pts):
    """Beside the cold line, a hair up and to the right, so a bundle reads as a pair."""
    LAY('P-DOMW-HOTW'); cc.setStrokeColor(black); cc.setLineWidth(0.6); cc.setDash(HOT_DASH, 0)
    _poly(cc, [(X+1.4, Y+1.4) for X, Y in pts]); cc.setDash()


def under_line(cc, pts):
    LAY('P-DOMW-UNDR'); cc.setStrokeColor(black); cc.setLineWidth(1.1); cc.setDash(UNDER_DASH, 0)
    _poly(cc, pts); cc.setDash()


def _text(cc, X, Y, t, size, bold=False, anchor='c'):
    LAY('P-ANNO-TEXT'); cc.setFillColor(black); cc.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    if anchor == 'c': cc.drawCentredString(X, Y, t)
    elif anchor == 'l': cc.drawString(X, Y, t)
    else: cc.drawRightString(X, Y, t)


def riser(cc, X, Y, tag='', side=1):
    """A pipe rising through the floor: a ring with a dot; its tag to the right, or
       to the left with side=-1."""
    LAY('P-EQPM'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.7); cc.setDash()
    cc.circle(X, Y, 3.4, fill=1, stroke=1)
    cc.setFillColor(black); cc.circle(X, Y, 1.3, fill=1, stroke=0)
    if tag: _text(cc, X+4.6*side, Y-1.6, tag, 3.6, anchor='l' if side > 0 else 'r')


def valve(cc, X, Y, along='h'):
    """A full-open valve: the bowtie, across the pipe it sits on."""
    LAY('P-EQPM'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.6); cc.setDash()
    r = 2.6
    pth = cc.beginPath()
    if along == 'h':
        pth.moveTo(X-r, Y-r); pth.lineTo(X+r, Y+r); pth.lineTo(X+r, Y-r); pth.lineTo(X-r, Y+r)
    else:
        pth.moveTo(X-r, Y-r); pth.lineTo(X+r, Y+r); pth.lineTo(X-r, Y+r); pth.lineTo(X+r, Y-r)
    pth.close(); cc.drawPath(pth, fill=1, stroke=1)


def meter(cc, X, Y, tag='WM'):
    LAY('P-EQPM'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.7); cc.setDash()
    cc.circle(X, Y, 4.4, fill=1, stroke=1)
    _text(cc, X, Y-1.4, tag, 3.6, bold=True)


def manifold(cc, X, Y, W, H):
    """The cold and hot manifolds, one box on the wall, split down its length."""
    LAY('P-EQPM'); cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.7); cc.setDash()
    cc.rect(X, Y, W, H, fill=1, stroke=1)
    if W >= H:
        cc.line(X, Y+H/2.0, X+W, Y+H/2.0)
        _text(cc, X+W/2.0, Y+H/2.0+1.0, 'C', 3.0, bold=True); _text(cc, X+W/2.0, Y+0.6, 'H', 3.0, bold=True)
    else:
        cc.line(X+W/2.0, Y, X+W/2.0, Y+H)
        _text(cc, X+W/4.0, Y+H/2.0-1.0, 'C', 3.0, bold=True); _text(cc, X+3*W/4.0, Y+H/2.0-1.0, 'H', 3.0, bold=True)


SHORT = 36.0        # a run whose longest segment is under this many points takes no label


def longest(pts):
    """The index of a polyline's longest segment: where its label goes."""
    return max(range(len(pts)-1), key=lambda i: math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]))


def run_label(cc, pts, text, size=3.8, always=False, flip=False):
    """On the longest segment of a polyline, at its middle, masked, along it. A short
       run — a stub in a closet — takes none: its fixture code says what it is and the
       supply diagram gives its count. `flip` puts it on the other side of the line:
       below a run along x, right of one along y."""
    i = longest(pts); a, b = pts[i], pts[i+1]
    if not always and math.hypot(b[0]-a[0], b[1]-a[1]) < SHORT: return
    mx, my = (a[0]+b[0])/2.0, (a[1]+b[1])/2.0
    w = pdfmetrics.stringWidth(text, 'Helvetica', size)
    LAY('P-ANNO-TEXT'); cc.setFillColor(white)
    if abs(b[0]-a[0]) >= abs(b[1]-a[1]):
        dy = -(size+4.4) if flip else 0.0
        cc.rect(mx-w/2.0-1.5, my+2.2+dy, w+3, size+1.6, fill=1, stroke=0)
        _text(cc, mx, my+3.4+dy, text, size)
    else:
        dx = size+7.0 if flip else 0.0
        cc.rect(mx-size-4.6+dx, my-w/2.0-1.5, size+1.6, w+3, fill=1, stroke=0)
        cc.saveState(); cc.translate(mx-3.8+dx, my); cc.rotate(90)
        _text(cc, 0, 0, text, size); cc.restoreState()


def _P(p, xy):
    return p.X(xy[0]), p.Y(xy[1])


def _label_for(run, cold, hot, *, pm):
    if run.fixtures == ('wh',):
        return '%s: %s" C + %s" H' % (run.group, pm.HEATER_CONN, pm.HEATER_CONN)
    if not hot:                      # a cold-only line: an ice maker's
        return '%s: %dC %s" PEX' % (run.group, cold, pm.HOME_RUN)
    return '%s: %dC + %dH %s" PEX' % (run.group, cold, hot, pm.HOME_RUN)


CODE = {'tub': 'TUB', 'shower': 'SH', 'wc': 'WC', 'lav': 'LAV', 'sink': 'KS', 'dw': 'DW', 'wd': 'CW', 'wh': 'WH', 'fridge': 'REF'}


def fixture_end(cc, X, Y, kind, side=1):
    LAY('P-DOMW-COLD'); cc.setFillColor(black); cc.setStrokeColor(black); cc.setLineWidth(0.4)
    cc.circle(X, Y, 1.5, fill=1, stroke=0)
    _text(cc, X+2.6*side, Y-1.3, CODE[kind], 3.4, anchor='l' if side > 0 else 'r')


TAG_CLEAR = 4.6    # points: a code set off its run, on the fixture's side, past the hot line


def draw_unit(p, u, tag_riser=None, riser_side=1, *, pm, tags_clear=False):
    """The manifolds, the valve and submeter, the riser and every home-run bundle of one
       unit on PlanDraw p. Fixtures come out of src/plumbing.py in page feet.

       With `tags_clear`, a fixture whose edge lies on or beside its run takes its code on the
       fixture's side of the run, clear of the hot line, and the run's label is drawn first
       so no mask covers a code."""
    cc = p.c
    for r in u.runs:
        fx = water.run_fixtures(r, u)
        cold, hot = water.run_lines(r, u.fixtures)
        pts = [_P(p, q) for q in r.path]
        cold_line(cc, pts)
        if hot: hot_line(cc, pts)
        if tags_clear:
            # the label on the side of its segment AWAY from the fixtures that connect to it
            L = longest(pts); a, b = pts[L], pts[L+1]
            along_x = abs(b[0]-a[0]) >= abs(b[1]-a[1])
            side = [(_P(p, (f.x+f.w/2.0, f.y+f.h/2.0))[1] > a[1]) if along_x else
                    (_P(p, (f.x+f.w/2.0, f.y+f.h/2.0))[0] < a[0])
                    for f in fx if water.stub(r, f, where=True)[2] == L]
            run_label(cc, pts, _label_for(r, cold, hot, pm=pm), flip=any(side))
        for f in fx:
            q, e, i = water.stub(r, f, where=True)
            Q, E = _P(p, q), _P(p, e)
            if Q != E:
                cold_line(cc, [Q, E], width=0.6)
                if f.kind != 'wc' and hot: hot_line(cc, [Q, E])
            F = _P(p, (f.x+f.w/2.0, f.y+f.h/2.0))
            if tags_clear and math.hypot(E[0]-Q[0], E[1]-Q[1]) < 6.0 and abs(F[1]-E[1]) >= abs(F[0]-E[0]):
                # the fixture stands across the run from its dot: its code centered over the
                # dot, on the fixture's side, clear of the hot line
                LAY('P-DOMW-COLD'); cc.setFillColor(black); cc.circle(E[0], E[1], 1.5, fill=1, stroke=0)
                _text(cc, E[0], E[1]-TAG_CLEAR-2.4 if F[1] < E[1] else E[1]+TAG_CLEAR, CODE[f.kind], 3.4)
            else:
                fixture_end(cc, E[0], E[1], f.kind, side=1 if e[0] >= q[0] else -1)
        if not tags_clear:
            run_label(cc, pts, _label_for(r, cold, hot, pm=pm))
    if u.manifold is not None:
        mx, my, mw, mh = u.manifold
        manifold(cc, p.X(mx), p.Y(my+mh), mw*p.sc, mh*p.sc)
    if u.valve is not None:
        # the stem from the riser or the trunk up to the manifolds carries the valve
        # and the submeter; drawn from the one to the other so the pipe is there too
        V, M = _P(p, u.valve), _P(p, u.submeter)
        cold_line(cc, [V, M], width=1.0)
        valve(cc, V[0], V[1], along='v' if abs(V[0]-M[0]) < abs(V[1]-M[1]) else 'h')
        meter(cc, M[0], M[1], 'SM')
    if u.riser is not None:
        X, Y = _P(p, u.riser)
        riser(cc, X, Y, tag_riser if tag_riser is not None else 'FROM BELOW', side=riser_side)

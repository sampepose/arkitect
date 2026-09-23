"""What a detail sheet draws with: a scaled section window with a column of labels either
side, each on a leader (_Det); a small detail at its own scale with leaders (_D); their
titles; and diagonal hatching clipped by arithmetic, since the recording canvases carry no
clip path. One copy: it began in one project's wall-section and roof sheets and was lifted,
by hand, into the next project's."""
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from lib.draw.page import GREY, LAY
from lib.draw.kit import c


def _hatch_band(cc, X0_, Y0_, X1_, Y1_, step=5.0):
    """Diagonal hatching inside a page rectangle, clipped by arithmetic rather than a
       clip path, which the recording canvases do not carry."""
    x0, x1 = sorted((X0_, X1_)); y0, y1 = sorted((Y0_, Y1_))
    k = (x0-y1)-((x0-y1) % step)
    while k < x1-y0:
        # the line x - y = k, inside the box
        pts = []
        for x in (x0, x1):
            y = x-k
            if y0-1e-9 <= y <= y1+1e-9: pts.append((x, y))
        for y in (y0, y1):
            x = y+k
            if x0-1e-9 <= x <= x1+1e-9: pts.append((x, y))
        pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
        if len(pts) >= 2:
            cc.line(pts[0][0], pts[0][1], pts[-1][0], pts[-1][1])
        k += step


class _Det:
    """One section: a window in feet, x either side of its own origin and z up, drawn at a
       scale under a top edge, with a column of labels either side, each on a leader to
       its point."""
    def __init__(s, cx, top, sc, xw, zlo, zhi, left, right, size=5.6, gap=10.0, sheet='', origin=0.0):
        # origin: the x that stands on cx, for a section that does not straddle its own zero
        s.cx, s.top, s.sc, s.xw, s.zlo, s.zhi, s.origin = cx, top, sc, xw, zlo, zhi, origin
        s.oy = top-(zhi-zlo)*sc
        s.left, s.right, s.size, s.gap, s.sheet = left, right, size, gap, sheet
        s.labels = []; s.lo = s.oy
    def X(s, x): return s.cx+(x-s.origin)*s.sc
    def Y(s, z): return s.oy+(z-s.zlo)*s.sc
    def rect(s, x0, z0, x1, z1, fill=white, lw=0.5, dash=None):
        c.setStrokeColor(black); c.setLineWidth(lw)
        if fill is not None: c.setFillColor(fill)
        if dash: c.setDash(*dash)
        c.rect(s.X(min(x0, x1)), s.Y(min(z0, z1)), abs(x1-x0)*s.sc, abs(z1-z0)*s.sc,
               fill=0 if fill is None else 1, stroke=1)
        if dash: c.setDash()
    def line(s, x0, z0, x1, z1, lw=0.5, dash=None):
        c.setStrokeColor(black); c.setLineWidth(lw)
        if dash: c.setDash(*dash)
        c.line(s.X(x0), s.Y(z0), s.X(x1), s.Y(z1))
        if dash: c.setDash()
    def poly(s, pts, fill=white, lw=0.5):
        c.setFillColor(fill); c.setStrokeColor(black); c.setLineWidth(lw)
        pth = c.beginPath(); pth.moveTo(s.X(pts[0][0]), s.Y(pts[0][1]))
        for x, z in pts[1:]: pth.lineTo(s.X(x), s.Y(z))
        pth.close(); c.drawPath(pth, fill=1, stroke=1)
    def circle(s, x, z, r):
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
        c.circle(s.X(x), s.Y(z), r*s.sc, fill=1, stroke=1)
    def hatch(s, x0, z0, x1, z1, step=3.2):
        c.setStrokeColor(GREY); c.setLineWidth(0.3)
        _hatch_band(c, s.X(x0), s.Y(z0), s.X(x1), s.Y(z1), step=step)
        c.setStrokeColor(black)
    def lab(s, px, pz, side, lines):
        s.labels.append((px, pz, side, tuple(lines)))
    def flush(s, where):
        size, lead = s.size, s.size+1.4
        c.setFillColor(black); c.setFont('Helvetica', size)
        for side in ('L', 'R'):
            y_next = s.top
            for px, pz, _sd, lines in sorted((l for l in s.labels if l[2] == side), key=lambda l: -l[1]):
                h = (len(lines)-1)*lead
                ty = min(s.Y(pz)+h/2.0, y_next)
                y_next = ty-h-lead-3.0
                lgap, rgap = s.gap if isinstance(s.gap, tuple) else (s.gap, s.gap)
                ex = s.X(s.origin-s.xw)-lgap if side == 'L' else s.X(s.origin+s.xw)+rgap
                for i, t in enumerate(lines):
                    w = pdfmetrics.stringWidth(t, 'Helvetica', size)
                    if side == 'L':
                        assert ex-2-w >= s.left-0.5, "%s %s: a left label overruns its column: %r" % (s.sheet, where, t)
                        c.drawRightString(ex-2, ty-i*lead, t)
                    else:
                        assert ex+2+w <= s.right+0.5, "%s %s: a right label overruns its column: %r" % (s.sheet, where, t)
                        c.drawString(ex+2, ty-i*lead, t)
                c.setStrokeColor(black); c.setLineWidth(0.3)
                c.line(s.X(px), s.Y(pz), ex, ty-h/2.0+size*0.35)
                c.circle(s.X(px), s.Y(pz), 0.8, fill=1, stroke=0)
                s.lo = min(s.lo, ty-h-size)
        s.labels = []
        return s.lo


def _title(x, y, n, name, scale):
    c.setFillColor(black); c.setFont('Helvetica-Bold', 9); c.drawString(x, y, '%d   %s' % (n, name))
    c.setFont('Helvetica', 7); c.drawString(x, y-10, 'SCALE: %s' % scale)
    c.setStrokeColor(black); c.setLineWidth(0.9); c.line(x, y+11, x+3.4*inch, y+11)


class _D:
    """One detail: a drawing scale, an origin and the small vocabulary every detail
       uses — rectangles in feet, hatched insulation, leaders with labels."""
    def __init__(s, ox, oy, sc, slot_w):    # slot_w: the page x the labels must stay inside
        s.ox, s.oy, s.sc, s.slot_w = ox, oy, sc, slot_w
        s.lo = oy; s.labels = []
    def X(s, v): return s.ox+v*s.sc
    def Y(s, v): return s.oy+v*s.sc
    def rect(s, x0, y0, x1, y1, fill=white, lw=0.6, dash=None):
        c.setFillColor(fill); c.setStrokeColor(black); c.setLineWidth(lw)
        if dash: c.setDash(*dash)
        c.rect(s.X(min(x0, x1)), s.Y(min(y0, y1)), abs(x1-x0)*s.sc, abs(y1-y0)*s.sc, fill=1, stroke=1)
        if dash: c.setDash()
        s.lo = min(s.lo, s.Y(min(y0, y1)))
    def poly(s, pts, fill=white, lw=0.6):
        c.setFillColor(fill); c.setStrokeColor(black); c.setLineWidth(lw)
        pth = c.beginPath(); pth.moveTo(s.X(pts[0][0]), s.Y(pts[0][1]))
        for x, y in pts[1:]: pth.lineTo(s.X(x), s.Y(y))
        pth.close(); c.drawPath(pth, fill=1, stroke=1)
        s.lo = min([s.lo]+[s.Y(y) for _x, y in pts])
    def line(s, x0, y0, x1, y1, lw=0.6, dash=None):
        c.setStrokeColor(black); c.setLineWidth(lw)
        if dash: c.setDash(*dash)
        c.line(s.X(x0), s.Y(y0), s.X(x1), s.Y(y1))
        if dash: c.setDash()
    def insul(s, x0, y0, x1, y1):
        """Blown or batt insulation: a light diagonal hatch inside the rectangle."""
        c.setStrokeColor(GREY); c.setLineWidth(0.3)
        _hatch_band(c, s.X(x0), s.Y(y0), s.X(x1), s.Y(y1), step=3.2)
        c.setStrokeColor(black)
    def lab(s, px, py, tx, ty, lines, size=4.6):
        """A leader from the detail point (px, py) to the label at (tx, ty), both in
           feet from the detail origin; the label is a tuple of lines."""
        s.labels.append((s.X(px), s.Y(py), s.X(tx), s.Y(ty), lines, size))
    def flush(s, where):
        LAY('S-ANNO-TEXT')
        for X, Y, tx, ty, lines, size in s.labels:
            c.setStrokeColor(black); c.setLineWidth(0.3); c.line(X, Y, tx, ty)
            c.setFillColor(black); c.setFont('Helvetica', size)
            for i, t in enumerate(lines):
                assert tx+1.5+pdfmetrics.stringWidth(t, 'Helvetica', size) <= s.slot_w+0.5, "%s overruns its slot: %r" % (where, t)
                c.drawString(tx+1.5, ty-1.6-i*(size+1.2), t)
            s.lo = min(s.lo, ty-1.6-(len(lines)-1)*(size+1.2)-size)
        s.labels = []


def _detail_title(x, y, n, name, scale):
    LAY('S-ANNO-TEXT')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.4); c.drawString(x, y, '%d   %s' % (n, name))
    c.setFont('Helvetica', 6.2); c.drawString(x, y-9, 'SCALE: %s' % scale)
    c.setLineWidth(0.9); c.setStrokeColor(black); c.line(x, y+9, x+1.6*inch, y+9)


# A member cut off mid-length, so a detail does not have to draw three feet of post to
# say the post is there. Two short strokes across it, as a break is always drawn.
def _break(d, x0, x1, z, lw=0.7):
    c.setStrokeColor(black); c.setLineWidth(lw); c.setFillColor(white)
    w = (x1-x0)
    c.rect(d.X(x0), d.Y(z)-3.0, w*d.sc, 6.0, fill=1, stroke=0)
    for dz in (-1.6, 1.6):
        pth = c.beginPath(); pth.moveTo(d.X(x0), d.Y(z)+dz-1.2)
        pth.lineTo(d.X(x0+w*0.35), d.Y(z)+dz+1.2)
        pth.lineTo(d.X(x0+w*0.65), d.Y(z)+dz-1.2)
        pth.lineTo(d.X(x1), d.Y(z)+dz+1.2)
        c.drawPath(pth, fill=0, stroke=1)

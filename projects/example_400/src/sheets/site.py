"""The lot as the two site sheets draw it: C-101, the construction site plan, and C-102,
the zoning site plan. One drawing, so the two cannot show different sites.

Both turn the plan so true north is up the sheet: the alley on the left, Oak Avenue on
the right, 396 Oak above and 404 Oak below. `k` scales the lettering, which C-102 sets
for 1/16" = 1'-0" and C-101 enlarges at 1" = 10'-0".
"""
from math import cos, radians, sin

from arkitect.lib.draw.context import LAY, current_layer
from arkitect.lib.draw.page import GREY, PlanDraw
from arkitect.lib.units import fmt
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
from arkitect.lib.draw.kit import c
from src.sitework import (ALLEY_W, FRONT_YARD, NORTH_NEIGHBOUR, PARK_D, PARK_N, PARK_PITCH,
                          PARK_X0, PARK_X1, PARK_Y0, PARK_Y1, SIDE_YARD, SITE_BLDG, SITE_D,
                          SITE_W, SOUTH_NEIGHBOUR, STAIR, TRUE_NORTH, WALKS)

# The plan's own frame has Oak at the top and the north lot line on the left. Turning it
# 90 degrees clockwise puts the north lot line up; the lot lines run 10 degrees off true
# north, so it turns back that much.
TURN = -(90.0-TRUE_NORTH)


def frame(sc, context, x0, y0, x1, y1, where):
    """(p, CX, CY, extent): a PlanDraw at sc points per foot, and the page point the turned
       plan is centred on in the box x0..x1, y0..y1 — the lot, the street and alley out to
       `context` feet past it, all inside the box or the build stops."""
    pts = [(x, y) for x in (-context, SITE_W+context) for y in (-context, SITE_D+ALLEY_W+context)]
    ct, st = cos(radians(TURN)), sin(radians(TURN))
    p = PlanDraw(c, -SITE_W/2.0*sc, -SITE_D/2.0*sc, sc, SITE_W, SITE_D)

    def turned(x, y):
        fx, fy = p.X(x), p.Y(y)
        return (fx*ct-fy*st, fx*st+fy*ct)
    t = [turned(x, y) for x, y in pts]
    CX = (x0+x1)/2.0-(min(q[0] for q in t)+max(q[0] for q in t))/2.0
    CY = (y0+y1)/2.0-(min(q[1] for q in t)+max(q[1] for q in t))/2.0
    ext = [(CX+a, CY+b) for a, b in t]
    assert min(q[0] for q in ext) >= x0 and max(q[0] for q in ext) <= x1, \
        "%s plan is wider than the drawing area" % where
    assert min(q[1] for q in ext) >= y0 and max(q[1] for q in ext) <= y1, \
        "%s plan runs into the band under it or off the top" % where
    return p, CX, CY, ext


def draw_site(p, sc, context, k=1.0, labels=None, extra=None):
    """The lot and everything on it, inside c's turned frame. `labels(nm)` may add lines
       under a building's own; `extra(p)` draws a sheet's own layer before the dimensions."""

    def _break(x, y, along):
        # a short zig-zag across the end of a line that stops because the sheet does
        px, py = p.X(x), p.Y(y)
        path = c.beginPath()
        if along == 'v':
            path.moveTo(px-3, py); path.lineTo(px-1, py+1.5); path.lineTo(px+1, py-1.5); path.lineTo(px+3, py)
        else:
            path.moveTo(px, py-3); path.lineTo(px+1.5, py-1); path.lineTo(px-1.5, py+1); path.lineTo(px, py+3)
        c.drawPath(path, fill=0, stroke=1)

    # ---- around the lot: the Oak line, the alley's two lines, the side lot lines ----
    _far = SITE_D+ALLEY_W
    c.setStrokeColor(black); c.setLineWidth(0.6)
    for (x0, y0, x1, y1) in ((-context, 0, SITE_W+context, 0),             # Oak right-of-way
                             (-context, SITE_D, SITE_W+context, SITE_D),   # alley, lot side
                             (-context, _far, SITE_W+context, _far)):      # alley, far side
        c.line(p.X(x0), p.Y(y0), p.X(x1), p.Y(y1))
        _break(x0, y0, 'h'); _break(x1, y1, 'h')
    c.setStrokeColor(GREY); c.setLineWidth(0.5); c.setDash([6, 2, 1, 2])
    for xx in (0, SITE_W):                                                 # shared parcel lines
        c.line(p.X(xx), p.Y(0), p.X(xx), p.Y(SITE_D))
    c.setDash(); c.setStrokeColor(black)

    # ---- the lot ----
    c.setLineWidth(1.4); c.setFillColor(white)
    c.rect(p.X(0), p.Y(SITE_D), SITE_W*sc, SITE_D*sc, fill=1, stroke=1)

    # ---- the front yard and side yard lines, dashed, to the head of the pad ----
    c.setStrokeColor(GREY); c.setLineWidth(0.6); c.setDash(3, 2)
    for (a, b, cc, d) in ((0, FRONT_YARD, SITE_W, FRONT_YARD),
                          (SIDE_YARD, FRONT_YARD, SIDE_YARD, PARK_Y0),
                          (SITE_W-SIDE_YARD, FRONT_YARD, SITE_W-SIDE_YARD, PARK_Y0)):
        c.line(p.X(a), p.Y(b), p.X(cc), p.Y(d))
    c.setDash(); c.setStrokeColor(black)
    c.setFillColor(GREY); c.setFont("Helvetica", 3.6*k)
    c.drawString(p.X(0.6), p.Y(FRONT_YARD-0.7), "FRONT YARD %s" % fmt(FRONT_YARD))
    c.setFillColor(black)

    # ---- the buildings, hatched, with their dwelling units ----
    def _along(x, y, lines):
        # lines of (font, size, text) centred on a site point, reading along the lot, on a
        # white ground so the hatch does not run through them
        lead = [s*1.25 for _f, s, _t in lines]
        tall = sum(lead); wide = max(pdfmetrics.stringWidth(t, f, s) for f, s, t in lines)
        c.saveState(); c.translate(p.X(x), p.Y(y)); c.rotate(90)
        c.setFillColor(white); c.rect(-wide/2-1.5*k, -tall/2-1.5*k, wide+3*k, tall+3*k, fill=1, stroke=0)
        c.setFillColor(black); yy = tall/2
        for (f, s, t), ld in zip(lines, lead):
            yy -= ld; c.setFont(f, s); c.drawCentredString(0, yy+0.25*s, t)
        c.restoreState()
    for (bx, by, bw, bd, nm, units, kind) in SITE_BLDG:
        c.setFillColor(white); c.setStrokeColor(GREY); c.setLineWidth(0.3)
        c.rect(p.X(bx), p.Y(by+bd), bw*sc, bd*sc, fill=1, stroke=0)
        yy = by+1.0
        while yy < by+bd:
            c.line(p.X(bx), p.Y(yy), p.X(bx+bw), p.Y(yy)); yy += 1.0
        c.setStrokeColor(black); c.setLineWidth(1.0)
        c.rect(p.X(bx), p.Y(by+bd), bw*sc, bd*sc, fill=0, stroke=1)
        _along(bx+bw/2.0, by+bd/2.0,
               [("Helvetica-Bold", 6.5*k, units), ("Helvetica-Bold", 6.0*k, nm),
                ("Helvetica", 4.2*k, kind), ("Helvetica", 4.2*k, "%s x %s" % (fmt(bw), fmt(bd)))]
               + [("Helvetica", 4.2*k, t) for t in (labels(nm) if labels else ())])

    # ---- the Unit 3 stair, and the walks from every dwelling to Oak ----
    c.setStrokeColor(black); c.setLineWidth(0.8); c.setFillColor(white)
    c.rect(p.X(STAIR[0]), p.Y(STAIR[3]), (STAIR[2]-STAIR[0])*sc, (STAIR[3]-STAIR[1])*sc, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Helvetica", 3.4*k)
    c.drawCentredString(p.X((STAIR[0]+STAIR[2])/2.0), p.Y((STAIR[1]+STAIR[3])/2.0)-1.2*k,
                        "UNIT 3 STAIR — %s PROJECTION" % fmt(STAIR[3]-STAIR[1]))
    c.setStrokeColor(GREY); c.setLineWidth(0.6)
    for (x0, y0, x1, y1) in WALKS:
        c.rect(p.X(x0), p.Y(y1), (x1-x0)*sc, (y1-y0)*sc, fill=0, stroke=1)
        p.concrete(x0, y0, x1, y1)
    c.setStrokeColor(black)

    # ---- parking: the pad, its stalls numbered, kept clear of the stipple ----
    _plab = "%s x %s" % (fmt(PARK_PITCH), fmt(PARK_D))
    _sny, _ply = PARK_Y0+4.0, PARK_Y0+10.0
    _clear = []
    for _i in range(PARK_N):
        _cx = PARK_X0+(_i+0.5)*PARK_PITCH
        for _t2, _f, _s, _y in ((str(_i+1), "Helvetica-Bold", 5.0*k, _sny), (_plab, "Helvetica", 3.6*k, _ply)):
            _w = pdfmetrics.stringWidth(_t2, _f, _s)
            _clear.append((p.X(_cx)-0.8*_s-1.2, p.Y(_y)-_w/2-1.2, p.X(_cx)+0.25*_s+1.2, p.Y(_y)+_w/2+1.2))
    c.setStrokeColor(black); c.setLineWidth(0.8); c.setFillColor(white)
    c.rect(p.X(PARK_X0), p.Y(PARK_Y1), (PARK_X1-PARK_X0)*sc, (PARK_Y1-PARK_Y0)*sc, fill=1, stroke=1)
    p.concrete(PARK_X0, PARK_Y0, PARK_X1, PARK_Y1, clear=_clear)
    c.setStrokeColor(black); c.setLineWidth(0.6)
    for i in range(1, PARK_N):
        xx = PARK_X0+i*PARK_PITCH
        c.line(p.X(xx), p.Y(PARK_Y1), p.X(xx), p.Y(PARK_Y0))
    c.setFillColor(black)
    for i in range(PARK_N):
        _cx = PARK_X0+(i+0.5)*PARK_PITCH
        for _t2, _f, _s, _y in ((str(i+1), "Helvetica-Bold", 5.0*k, _sny), (_plab, "Helvetica", 3.6*k, _ply)):
            c.saveState(); c.translate(p.X(_cx), p.Y(_y)); c.rotate(90)
            c.setFont(_f, _s); c.drawCentredString(0, 0, _t2); c.restoreState()

    if extra:
        extra(p)

    # ---- dimensions, and what lies around the lot ----
    _was = current_layer()
    for a, b in ((0, SIDE_YARD), (SIDE_YARD, SITE_W-SIDE_YARD), (SITE_W-SIDE_YARD, SITE_W)):
        p.dim(a, b, 'h', -2.5)
    p.dim(0, SITE_W, 'h', -5.5)
    _bands = [0.0, FRONT_YARD]+[v for b in SITE_BLDG for v in (b[1], b[1]+b[3])][1:]+[SITE_D]
    _bands = sorted(set(round(v, 6) for v in _bands))
    for a, b in zip(_bands, _bands[1:]):
        p.dim(a, b, 'v', SITE_W+3.0)
    p.dim(0, SITE_D, 'v', -3.0)
    p.dim(SITE_D, _far, 'v', -3.0)
    LAY(_was)
    p.note(SITE_W/2.0, -context+0.6, "OAK AVENUE", 7.0*k, bold=True)
    p.note(SITE_W/2.0, SITE_D+ALLEY_W/2.0+1.0, "PUBLIC ALLEY", 5.4*k, bold=True)
    p.vnote(-context+2.0, SITE_D/2.0, NORTH_NEIGHBOUR[0], NORTH_NEIGHBOUR[1], 5.4*k)
    p.vnote(SITE_W+context/2.0+3.0, SITE_D/2.0, SOUTH_NEIGHBOUR[0], SOUTH_NEIGHBOUR[1], 5.4*k)

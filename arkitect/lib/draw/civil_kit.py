"""The grading sheet's drawing vocabulary: a flow arrow, a legend swatch, a slope as a percentage.

Plan feet in, page points out, through the PlanDraw or the canvas stand-in it is handed; what is
drawn where is the project's. It was word for word in each project's copy of the sheet.
"""
import math
from reportlab.lib.colors import black
from arkitect.lib.model import grade as grade_model
from arkitect.lib.draw.kit import c


ARROW_SIZE = 4.4


class _Swatch:
    """Feet to points for a legend sample, as PlanDraw maps them, without being one: every
       PlanDraw announces itself as a plan frame and the DXF exports each frame."""
    def __init__(s, ox, oy, sc, D):
        s.ox, s.oy, s.sc, s.D = ox, oy, sc, D
    def X(s, v): return s.ox+v*s.sc
    def Y(s, v): return s.oy+(s.D-v)*s.sc


def _pct(slope):
    v = round(100.0*slope, 1)
    return ("%d%%" % v) if abs(v-round(v)) < 1e-9 else ("%.1f%%" % v)


def _arrow(p, a, b, label=None, size=ARROW_SIZE, head=3.0):
    """A drainage arrow from site point a to b, the slope written beside it: above a
       horizontal arrow, to the right of a vertical one, reading along it."""
    ax, ay, bx, by = p.X(a[0]), p.Y(a[1]), p.X(b[0]), p.Y(b[1])
    c.setStrokeColor(black); c.setFillColor(black); c.setLineWidth(0.6)
    c.line(ax, ay, bx, by)
    t = math.atan2(by-ay, bx-ax); ct, st = math.cos(t), math.sin(t)
    hp = c.beginPath(); hp.moveTo(bx, by)
    hp.lineTo(bx-head*ct+0.45*head*st, by-head*st-0.45*head*ct)
    hp.lineTo(bx-head*ct-0.45*head*st, by-head*st+0.45*head*ct)
    hp.close(); c.drawPath(hp, fill=1, stroke=0)
    if label:
        c.setFont("Helvetica", size)
        mx, my = (ax+bx)/2.0, (ay+by)/2.0
        if abs(ay-by) < 1e-6:
            c.drawCentredString(mx, my+2.0, label)
        else:
            c.saveState(); c.translate(mx+2.0+size*0.72, my); c.rotate(90)
            c.drawCentredString(0, 0, label); c.restoreState()


def _band_arrows(p, band, *, min_arrow, g):
    """One arrow per surface of the section at the middle of the band, each labeled with
       its own slope. Steps, edges and gutter sides take none."""
    s = (band.s0+band.s1)/2.0
    pts = band.section(s)
    for (d0, g0, _a), (d1, g1, kind) in zip(pts, pts[1:]):
        if kind in ("step", "edge", "gutter") or d1-d0 < min_arrow-1e-9:
            continue
        inset = min(0.4, (d1-d0)/6.0)
        _arrow(p, grade_model.point(band.face, s, d0+inset), grade_model.point(band.face, s, d1-inset), _pct((g0-g1)/(d1-d0)))


SPOT_SIZE = 4.4


def _spot(p, x, y, grade, dx=3.0, dy=-1.6, anchor="l", prefix="", *, g):
    """A spot grade: a small cross on the point and its grade in inches from the datum."""
    px, py = p.X(x), p.Y(y)
    c.setStrokeColor(black); c.setLineWidth(0.5)
    c.line(px-2.0, py-2.0, px+2.0, py+2.0); c.line(px-2.0, py+2.0, px+2.0, py-2.0)
    c.setFillColor(black); c.setFont("Helvetica", SPOT_SIZE)
    txt = prefix+grade_model.signed(grade)
    {"l": c.drawString, "r": c.drawRightString, "c": c.drawCentredString}[anchor](px+dx, py+dy, txt)


def _walk_slope(face, s0, *, g):
    """The walk segment's slope in the band that starts at s0 on `face`."""
    b = next(b for b in g.BANDS if b.face == face and abs(b.s0-s0) < 1e-9)
    pts = b.section((b.s0+b.s1)/2.0)
    return next((g0-g1)/(d1-d0) for (d0, g0, _a), (d1, g1, k) in zip(pts, pts[1:]) if k == "walk")

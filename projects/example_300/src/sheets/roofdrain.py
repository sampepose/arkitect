"""The downspouts as the sheets draw them: in plan on C-101 and C-103, and as leaders on
the elevations that show their faces. Every position, outlet and splash block is
src/downspouts.py's; this module places marks and nothing else.

A plan mark sits beside its leader on lawn. Where it sits is chosen per leader, because
each corner has something different beside it — the Unit 3 stoop at DS-1, the parking
pad at DS-3 — and the choice is asserted clear of the paving and the stairs, so a moved
walk fails the build rather than printing a mark across it."""
from lib.draw.page import GREY
from lib.units import fmt
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
from src import downspouts as DS
from src import grading as G
from lib.model import grade as grade
from src import levels
from src.roof import EAVE_OVERHANG
from lib.draw.kit import knockout
from lib.draw.kit import c

SYM = 0.5                 # the plan symbol, feet square, on the wall line
MARK_SIZE = 4.2
# Each mark's baseline start, in site feet, and which way it reads from there.
MARK_AT = {"DS-1": (9.75, 69.2, "l"),       # in the lawn strip between the wall and G-1, clear of the stoop
           "DS-2": (34.35, 66.0, "l"),      # along the parcel wall, toward S Elm
           "DS-3": (8.3, 109.7, "r"),       # off the pad, below the end of the Unit 3 walk
           "DS-4": (34.35, 106.0, "l")}


def _mark_box(p, sc, mark):
    x, y, anchor = MARK_AT[mark]
    w = pdfmetrics.stringWidth(mark, "Helvetica-Bold", MARK_SIZE)/sc
    x0 = x if anchor == "l" else x-w
    return (x0, y-MARK_SIZE*0.72/sc, x0+w, y)


def plan(p, sc, splash=True):
    """Every leader as a square on its wall with its mark; with `splash`, its splash block
       and an arrow along it to its receiver."""
    assert set(MARK_AT) == {d.mark for d in DS.DOWNSPOUTS}, "a downspout has no plan mark position"
    for d in DS.DOWNSPOUTS:
        x = DS.discharge(d)
        box = _mark_box(p, sc, d.mark)
        for r in G.PAVED:
            assert not grade._overlaps(box, (r.x0, r.y0, r.x1, r.y1)), "%s's mark prints on the %s" % (d.mark, r.name)
        for nm, r in DS.STAIRS.items():
            assert not grade._overlaps(box, r), "%s's mark prints on the %s" % (d.mark, nm)
        for g in G.GUTTERS:
            assert not grade._overlaps(box, g.box()), "%s's mark prints on %s" % (d.mark, g.mark)
        if splash:
            sx0, sy0, sx1, sy1 = x.splash
            c.setStrokeColor(GREY); c.setLineWidth(0.5); c.setFillColor(white)
            c.rect(p.X(sx0), p.Y(sy1), (sx1-sx0)*sc, (sy1-sy0)*sc, fill=1, stroke=1)
            a, b = grade.point(d.face, d.s, 0.25), grade.point(d.face, d.s, max(x.length, 0.9))
            ax, ay, bx, by = p.X(a[0]), p.Y(a[1]), p.X(b[0]), p.Y(b[1])
            c.setStrokeColor(black); c.setFillColor(black); c.setLineWidth(0.5)
            c.line(ax, ay, bx, by)
            ux, uy = (bx-ax), (by-ay); n = (ux*ux+uy*uy)**0.5; ux, uy = ux/n, uy/n
            hp = c.beginPath(); hp.moveTo(bx, by)
            hp.lineTo(bx-2.4*ux+1.1*uy, by-2.4*uy-1.1*ux); hp.lineTo(bx-2.4*ux-1.1*uy, by-2.4*uy+1.1*ux)
            hp.close(); c.drawPath(hp, fill=1, stroke=0)
        lx, ly = grade.point(d.face, d.s, 0.0)
        c.setStrokeColor(black); c.setLineWidth(0.6); c.setFillColor(black)
        c.rect(p.X(lx)-SYM*sc/2.0, p.Y(ly)-SYM*sc/2.0, SYM*sc, SYM*sc, fill=1, stroke=1)
        mx, my, anchor = MARK_AT[d.mark]
        c.setFont("Helvetica-Bold", MARK_SIZE)
        (c.drawString if anchor == "l" else c.drawRightString)(p.X(mx), p.Y(my), d.mark)


def schedule_rows():
    """(line 1 left, line 1 right, line 2) for each leader, as C-103 prints them."""
    rows = []
    for d in DS.DOWNSPOUTS:
        x = DS.discharge(d)
        lo, hi = DS.extent(d.face)
        if d.face.axis == "x":
            corner = "SAGE" if d.s-lo < hi-d.s else "ADJACENT-PARCEL"
        else:
            corner = ("S ELM" if d.face.building == "BUILDING 1" else "COURTYARD") if d.s-lo < hi-d.s else "REAR"
        off = min(d.s-lo, hi-d.s)
        to = "THE ALLEY LOT LINE" if x.to == "ALLEY" else x.to
        l1 = "%s  %s, %s SF OF ROOF" % (d.mark, d.eave.name, "{:,.0f}".format(d.eave.area))
        r1 = "%s OF GUTTER   ·   %.1f GPM" % (fmt(x.run), DS.flow(d.eave.area))
        l2 = "     LEADER ON THE %s, %s FROM THE %s CORNER   ·   OUTLET %s   ·   %s SPLASH TO %s" % (
            x.wall, fmt(off), corner, DS.height(x.outlet_z), fmt(x.length), to)
        rows.append((l1, r1, l2))
    return rows


GUTTER_FACE = 5.0/12.0       # the gutter's face below the drip edge, as an elevation shows it
GUTTER_W = 5.0/12.0          # and its depth out from the fascia, S-103 detail 1
# The gutter hangs on the fascia, at the eave overhang, which is lower than the eave at the
# wall line by the overhang at the pitch.
FASCIA = levels.EAVE-EAVE_OVERHANG*levels.ROOF_PITCH+5.0/12.0
LABEL_SIZE = 5.2


def gutter(Xp, Yp, x0, x1, label=None, label_at=None):
    """An eave gutter along the top of the wall from elevation x x0 to x1, and what it
       falls to, written above it on the roof."""
    ev = FASCIA
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    c.rect(Xp(min(x0, x1)), Yp(ev-GUTTER_FACE), Xp(max(x0, x1))-Xp(min(x0, x1)), Yp(ev)-Yp(ev-GUTTER_FACE), fill=1, stroke=1)
    if label:
        c.setFillColor(black); c.setFont("Helvetica", LABEL_SIZE)
        knockout(Xp(label_at), Yp(ev)+3.0, label, "Helvetica", LABEL_SIZE, "c")


def elevation(Xp, Yp, ex, d, corner=None):
    """A leader on an elevation at elevation x `ex`, from the eave to its outlet, with its
       splash block at grade. `corner`, on a gable face, is the elevation x of the corner
       its gutter ends at: the gutter's end is drawn there and the leader offset to it.
       The mark and what the leader does run up beside it, so the label keeps to the
       strip between the leader and the nearest opening."""
    x = DS.discharge(d)
    ev = FASCIA
    top = ev-GUTTER_FACE
    w = DS.LEADER_W
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.7)
    if corner is not None:
        out = -1.0 if ex > corner else 1.0             # the gutter stands its eave's overhang outside the corner
        end = corner+out*(EAVE_OVERHANG+GUTTER_W)
        c.rect(Xp(min(end, corner+out*EAVE_OVERHANG)), Yp(top), abs(Xp(end)-Xp(corner+out*EAVE_OVERHANG)), Yp(ev)-Yp(top), fill=1, stroke=1)
        c.line(Xp((end+corner+out*EAVE_OVERHANG)/2.0), Yp(top), Xp(ex), Yp(top-0.6))
        top -= 0.6
    c.rect(Xp(ex-w/2.0), Yp(x.outlet_z), Xp(ex+w/2.0)-Xp(ex-w/2.0), Yp(top)-Yp(x.outlet_z), fill=1, stroke=1)
    c.setStrokeColor(GREY); c.setLineWidth(0.6)
    c.rect(Xp(ex-DS.SPLASH_W/2.0), Yp(0.0), Xp(ex+DS.SPLASH_W/2.0)-Xp(ex-DS.SPLASH_W/2.0), Yp(2.0/12.0)-Yp(0.0), fill=0, stroke=1)
    txt = "%s — LEADER TO SPLASH BLOCK, C-103" % d.mark
    c.setFillColor(black); c.setFont("Helvetica", LABEL_SIZE)
    c.saveState(); c.translate(Xp(ex+w/2.0)+LABEL_SIZE*0.9, Yp(x.outlet_z+0.8)); c.rotate(90)
    knockout(0, 0, txt, "Helvetica", LABEL_SIZE, "l"); c.restoreState()
    return Xp(ex+w/2.0)+LABEL_SIZE*0.9+1.0                # the label's far edge, page points

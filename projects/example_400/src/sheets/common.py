"""What every sheet needs: somewhere to draw, and the corners to draw between.

`c` is a stand-in, not a canvas. Every renderer reads it as a module global — some 610
drawing calls — and each read resolves to the canvas of the document THIS THREAD is
drawing, so build_set() and build_zoning_sheet() can run at the same time. See
arkitect/lib/draw/context.py for why that is a ContextVar rather than a module attribute.

The corners come from the ARCH C drawing area. A sheet on a different page size takes
its own from `Page.DA` — C-102 does, because it is 11 x 17 — so these are the set's,
not a universal truth.
"""
import math
from arkitect.lib.draw.page import LAY
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from arkitect.lib.draw.kit import c
from arkitect.lib.units import fmt

# The width C-101 and C-102 both wrap zoning_relief() to. The lines are hand-wrapped in
# src/sitework.py and nothing measured them: a long one would have run out of the zoning
# table on C-101 and into the notes column on C-102. Both sheets assert it now, each at
# its own type size, so one wrap has to satisfy the tighter of the two.
RELIEF_W = 3.60 * inch


def tag_half_width(mark):
    """Half the width of a door mark's oval, in page points."""
    return 5.2+2.1*len(mark)


def draw_door_tags(p, plan, W, tags, nudge=None):
    """Door marks on a plan: an oval with the A-602 mark, on white. `tags` are model points,
       src/schedules.door_tags(); they go through the plan's regrid and the sheet mirror.
       `nudge`, if given, maps a tag to the page point its oval moves to, for a sheet whose
       own strings leave no room at the tag's usual place."""
    LAY('A-ANNO-IDEN')            # the identifier layer the engine and the DXF exporter know
    for x, y, mark in tags:
        X, Y = p.X(W-plan.x(x, y)), p.Y(plan.y(y))
        if nudge: X, Y = nudge((x, y, mark), X, Y)
        w = tag_half_width(mark)
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
        c.ellipse(X-w, Y-4.2, X+w, Y+4.2, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold", 4.6); c.drawCentredString(X, Y-1.6, mark)


def draw_soffit(p, level, ahu=True, mark_y=None):
    """Unit 1's hall soffit on a plan of that level: its outline dashed, traced round
       src/building1.U1_SOFFIT's rectangles, named in its first corner, and -- where the
       sheet does not draw the air handler itself -- the cabinet it hides, dashed and
       unfilled, with its mark, as M-101 places it, its mark at the cabinet's middle or at
       page point `mark_y`. Drawn before the door tags, which sit on it."""
    from src.building1 import B1_W, LEVEL, U1_AHU, soffit_outline, soffit_pages
    from src.mechanical import AHU_MARK, ahu_box
    LAY("A-ANNO")
    c.saveState()
    c.setStrokeColor(black); c.setLineWidth(0.5); c.setDash(6, 2)
    ins = 0.12                                     # in off the wall face, so the dash reads
    for loop in soffit_outline(level):
        n = len(loop)
        # each corner moved in along both its edges' inward normals, which point to the
        # side of the first edge the soffit is on
        def normal(a, b, sign=1.0):
            dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy)
            return (-sign*dy/L, sign*dx/L)
        (a, b), t = loop[:2], normal(*loop[:2])
        mx, my = (a[0]+b[0])/2.0+0.01*t[0], (a[1]+b[1])/2.0+0.01*t[1]
        sign = 1.0 if any(r[0] < mx < r[2] and r[1] < my < r[3] for r in soffit_pages(level)) else -1.0
        pts = []
        for k in range(n):
            n0, n1 = normal(loop[k-1], loop[k], sign), normal(loop[k], loop[(k+1) % n], sign)
            pts.append((loop[k][0]+ins*(n0[0]+n1[0]), loop[k][1]+ins*(n0[1]+n1[1])))
        path = c.beginPath(); path.moveTo(p.X(pts[0][0]), p.Y(pts[0][1]))
        for q in pts[1:]: path.lineTo(p.X(q[0]), p.Y(q[1]))
        path.close(); c.drawPath(path, fill=0, stroke=1)
    x0, y0 = min(soffit_outline(level)[0])        # the name in the corner nearest the plan's origin
    if ahu:
        P = LEVEL[level]['plan']
        ax, ay = U1_AHU[level]
        px, py = B1_W-P.x(ax, ay), P.y(ay)
        bx0, by0, bx1, by1 = ahu_box(level, px, py)
        c.setLineWidth(0.6); c.setDash(3, 2)
        c.rect(p.X(bx0), p.Y(by1), (bx1-bx0)*p.sc, (by1-by0)*p.sc, fill=0, stroke=1)
    c.setDash(); c.setFillColor(black)
    LAY("A-ANNO-TEXT")
    c.setFont("Helvetica", 3.5); c.drawString(p.X(x0+ins)+2.0, p.Y(y0+ins)-5.0, "SOFFIT")
    if ahu:
        c.setFont("Helvetica-Bold", 4.6); c.drawCentredString(p.X(px), (p.Y(py) if mark_y is None else mark_y)-1.6, AHU_MARK[(1, level)])
    c.restoreState()


def draw_attic_hatch(p, h, size=3.5, split=False):
    """An attic hatch of src/roof.py on a plan drawn in page feet: a dashed rectangle
       and the two-line label Unit 1's has always carried on A-102. A-102 draws Unit
       3's, A-103 Unit 5's and S-103 all three, from the same record."""
    from arkitect.lib.draw.page import LAY
    x0, y0, x1, y1 = h.page
    LAY("A-ANNO-TEXT")
    c.saveState()
    c.setStrokeColor(black); c.setLineWidth(0.4); c.setDash(3, 2)
    c.rect(p.X(x0), p.Y(y1), (x1-x0)*p.sc, (y1-y0)*p.sc, fill=0, stroke=1)
    c.setDash(); c.setFillColor(black); c.setFont("Helvetica", size)
    # over the box, not in it: the hall's own name stands where the hatch is. `split` sets
    # it in two lines, for a sheet that gives it a size its hall is too narrow to take in one
    lines = ("ATTIC ACCESS", "22x30 IN CLG") if split else ("ATTIC ACCESS, 22x30 IN CLG",)
    for i, t in enumerate(reversed(lines)):
        c.drawCentredString(p.X((x0+x1)/2.0), p.Y(y0)+1.8+i*(size+0.8), t)
    c.restoreState()



def draw_landings(p, pads, sheet):
    """The landing outside each exterior door, RCO 311.3: the pads S-101 pours and C-103
       grades, from src/foundation.py, which gives them in page feet. C-103 note 5 is
       the rule's home, so the plan draws the pad, sizes it and cites that note."""
    LAY("A-ANNO")
    c.saveState(); c.setStrokeColor(black); c.setLineWidth(0.5)
    for x0, y0, x1, y1, _nm in pads:
        c.rect(p.X(x0), p.Y(y1), (x1-x0)*p.sc, (y1-y0)*p.sc, fill=0, stroke=1)
        LAY("A-ANNO-TEXT"); c.setFillColor(black)
        lines = ("LANDING", "%s x %s" % (fmt(x1-x0), fmt(y1-y0)), "C-103 NOTE 5")
        # stacked on the pad's middle, clear of its outline; a rear pad's middle is
        # past the room-width string that runs across its near half
        cy = p.Y((y0+y1)/2.0) - (0.25*(y1-y0)*p.sc if y0 > 0 else 0.0)
        for i, t in enumerate(lines):
            c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 4.6)
            assert c.stringWidth(t, "Helvetica-Bold", 4.6) < (x1-x0)*p.sc-4, "%s: %r overruns its landing" % (sheet, t)
            c.drawCentredString(p.X((x0+x1)/2.0), cy+5.5-5.5*i, t)
        LAY("A-ANNO")
    c.restoreState()


def stoop_lines():
    """The Unit 3 stair's stoop, as A-102 and A-202 both describe it: its slab (S-101
       note 5 pours it), its top over grade at the wall, and the one step C-103 grades
       off it -- thickness and step stated apart, so neither reads as the other."""
    from arkitect.lib.units import inches
    from src import grading as G
    from src.building2 import U5_STOOP_Z
    from src.foundation import PAD_T
    return ("CONCRETE STOOP, %s SLAB, TOP +%s" % (inches(PAD_T), inches(U5_STOOP_Z)),
            "ONE %s STEP DOWN TO THE WALK, C-103" % inches(G.STOOP_STEP))

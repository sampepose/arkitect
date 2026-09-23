"""What every sheet needs: somewhere to draw, and the corners to draw between.

`c` is a stand-in, not a canvas. Every renderer reads it as a module global — some 610
drawing calls — and each read resolves to the canvas of the document THIS THREAD is
drawing, so build_set() and build_zoning_sheet() can run at the same time. See
lib/draw/context.py for why that is a ContextVar rather than a module attribute.

The corners come from the ARCH C drawing area. A sheet on a different page size takes
its own from `Page.DA` — C-102 does, because it is 11 x 17 — so these are the set's,
not a universal truth.
"""
from lib.draw.page import LAY
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from lib.draw.kit import c

# The width C-101 and C-102 both wrap zoning_relief() to. The lines are hand-wrapped in
# src/sitework.py and nothing measured them: a long one would have run out of the zoning
# table on C-101 and into the notes column on C-102. Both sheets assert it now, each at
# its own type size, so one wrap has to satisfy the tighter of the two.
RELIEF_W = 3.60 * inch


def draw_door_tags(p, plan, W, tags):
    """Door marks on a plan: an oval with the A-602 mark, on white. `tags` are model points,
       src/schedules.door_tags(); they go through the plan's regrid and the sheet mirror."""
    LAY('A-ANNO-IDEN')            # the identifier layer the engine and the DXF exporter know
    for x, y, mark in tags:
        X, Y = p.X(W-plan.x(x, y)), p.Y(plan.y(y))
        w = 5.2+2.1*len(mark)
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
        c.ellipse(X-w, Y-4.2, X+w, Y+4.2, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold", 4.6); c.drawCentredString(X, Y-1.6, mark)


def draw_attic_hatch(p, h):
    """An attic hatch of src/roof.py on a plan drawn in page feet: a dashed rectangle
       and the two-line label Unit 1's has always carried on A-102. A-102 draws Unit
       3's, A-103 Unit 5's and S-103 all three, from the same record."""
    from lib.draw.page import LAY
    x0, y0, x1, y1 = h.page
    LAY("A-ANNO-TEXT")
    c.saveState()
    c.setStrokeColor(black); c.setLineWidth(0.4); c.setDash(3, 2)
    c.rect(p.X(x0), p.Y(y1), (x1-x0)*p.sc, (y1-y0)*p.sc, fill=0, stroke=1)
    c.setDash(); c.setFillColor(black); c.setFont("Helvetica", 3.5)
    # one line over the box, not in it: the hall's own name stands where the hatch is
    c.drawCentredString(p.X((x0+x1)/2.0), p.Y(y0)+1.8, "ATTIC ACCESS, 22x30 IN CLG")
    c.restoreState()


"""What every sheet needs: somewhere to draw, and the corners to draw between.

`c` is a stand-in, not a canvas. Every renderer reads it as a module global — some 610
drawing calls — and each read resolves to the canvas of the document THIS THREAD is
drawing, so build_set() and build_zoning_sheet() can run at the same time. See
arkitect/lib/draw/context.py for why that is a ContextVar rather than a module attribute.

The corners come from the ARCH C drawing area. A sheet on a different page size takes
its own from `Page.DA` — C-102 does, because it is 11 x 17 — so these are the set's,
not a universal truth.
"""
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from arkitect.lib.draw.kit import c

# The width C-101 and C-102 both wrap zoning_relief() to. The lines are hand-wrapped in
# src/sitework.py and nothing measured them: a long one would have run out of the zoning
# table on C-101 and into the notes column on C-102. Both sheets assert it now, each at
# its own type size, so one wrap has to satisfy the tighter of the two.
RELIEF_W = 3.60 * inch


def draw_attic_hatch(p, h):
    """An attic hatch of src/roof.py on a plan drawn in page feet: a dashed rectangle
       and the two-line label Unit 1's has always carried on A-102. A-102 draws Unit
       3's, A-103 Unit 5's and S-103 all three, from the same record."""
    from arkitect.lib.draw.page import LAY
    x0, y0, x1, y1 = h.page
    LAY("A-ANNO-TEXT")
    c.saveState()
    c.setStrokeColor(black); c.setLineWidth(0.4); c.setDash(3, 2)
    c.rect(p.X(x0), p.Y(y1), (x1-x0)*p.sc, (y1-y0)*p.sc, fill=0, stroke=1)
    c.setDash(); c.setFillColor(black); c.setFont("Helvetica", 3.5)
    cx, cy = p.X((x0+x1)/2.0), p.Y((y0+y1)/2.0)
    c.drawCentredString(cx, cy+0.9, "ATTIC ACCESS"); c.drawCentredString(cx, cy-3.0, "22x30 IN CLG")
    c.restoreState()


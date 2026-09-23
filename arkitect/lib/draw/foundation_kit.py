"""The foundation sheet's drawing vocabulary: a bearing strip's band under the slab.
"""
from reportlab.lib.colors import black, white
from arkitect.lib.draw.page import LAY


def _band(p, x0, y0, x1, y1, label=None, size=4.6):
    """A piece of foundation concrete: outlined, stippled, labeled along its center."""
    LAY("S-FNDN")
    cc = p.c
    cc.setStrokeColor(black); cc.setLineWidth(0.9); cc.setFillColor(white)
    cc.rect(p.X(x0), p.Y(y1), (x1-x0)*p.sc, (y1-y0)*p.sc, fill=1, stroke=1)
    p.concrete(x0, y0, x1, y1)
    if label:
        LAY("S-ANNO-TEXT")
        cc.setFillColor(black); cc.setFont("Helvetica-Bold", size)
        cx, cy = p.X((x0+x1)/2.0), p.Y((y0+y1)/2.0)
        if (x1-x0) >= (y1-y0):
            cc.drawCentredString(cx, cy-size/3.0, label)
        else:
            cc.saveState(); cc.translate(cx, cy); cc.rotate(90); cc.drawCentredString(0, -size/3.0, label); cc.restoreState()

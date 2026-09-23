"""The mechanical sheets' schedule and legend rows.

Plan feet in, page points out, through the PlanDraw or the canvas stand-in it is handed; what is
drawn where is the project's. It was word for word in each project's copy of the sheet.
"""
from reportlab.lib.colors import black
from lib.draw.kit import c, _fits
from lib.symbols import mechanical as ms
from lib.draw.text import wrap_notes


S, LEAD = 5.6, 7.6


def legend(p, x, y, width, kinds=None):
    for k, text in ms.KINDS:
        if kinds is not None and k not in kinds: continue
        _fits(text, 'Helvetica', S, width-20, 'legend line')
    return ms.legend(p, x, y, kinds=kinds)


def _room(nm):
    return 'LIVING' if 'LIVING' in nm else nm.replace('BEDROOM ', 'BR ')


def _head(x, y, t, width):
    # A schedule title was never measured, and the ventilation one had grown to within
    # 3/4 pt of the sheet edge -- a longer citation would have printed off it in silence.
    _fits(t, 'Helvetica-Bold', 7.2, width, 'schedule title')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, t); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y)
    return y-LEAD-1


def _row(x, y, cols, cells, width, bold=False):
    """One schedule row; every cell is measured against its column, the last against
       what is left of the block's width."""
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', S)
    for i, (cx, t) in enumerate(zip(cols, cells)):
        nxt = cols[i+1] if i+1 < len(cols) else width
        _fits(t, 'Helvetica-Bold' if bold else 'Helvetica', S, nxt-cx-3, 'schedule cell')
        c.drawString(x+cx, y, t)
    return y-LEAD


def _para(x, y, text, width, size=S-0.6, lead=LEAD-0.8):
    """A footnote under a schedule, wrapped to the block's width."""
    c.setFont('Helvetica', size)
    for t in wrap_notes([text], width, size, indent=''):
        _fits(t, 'Helvetica', size, width, 'schedule note'); c.drawString(x, y, t); y -= lead
    return y

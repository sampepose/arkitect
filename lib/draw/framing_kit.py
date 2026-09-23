"""The floor-framing sheet's drawing vocabulary: schedule columns, a cut mark, the typical-joist callout, a hanger.

Plan feet in, page points out, through the PlanDraw or the canvas stand-in it is handed; what is
drawn where is the project's. It was word for word in each project's copy of the sheet.
"""
from reportlab.lib.colors import black, white
from reportlab.pdfbase import pdfmetrics
from lib.draw.page import LAY
from lib.units import inches
from lib.draw.kit import c
from reportlab.lib.units import inch


def _typical(p, b):
    """The joists drawn are the typical layout; the manufacturer's layout governs."""
    LAY('S-ANNO-TEXT'); cc = p.c; cc.setFillColor(black); cc.setFont('Helvetica', 4.6)
    x, y = (b.x0+0.4, b.y0+0.5) if b.run == 'h' else (b.x0+0.5, b.y0+0.4)
    cc.drawString(p.X(x), p.Y(y)-5, 'TYPICAL LAYOUT — THE MANUFACTURER\'S LAYOUT GOVERNS')


def _cut(floor, bay, x0, y0, x1, y1):
    """A joist line with the well taken out of it: the tails start at the header's far face."""
    for w in floor.wells:
        if bay.run == 'h' and w.y0 < y0 < w.y1 and x0 <= w.x0 and x1 >= w.x1:
            return [(w.header_x1, y0, x1, y1)]
    return [(x0, y0, x1, y1)]


def _hanger(p, x, y):
    cc = p.c; cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.5)
    cc.rect(p.X(x)-1.8, p.Y(y)-1.8, 3.6, 3.6, fill=1, stroke=1)


_CARRIES_ABBR = {
    'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR': 'R+C+1CS',
    'ROOF, CEILING AND ONE CENTER-BEARING FLOOR': 'R+C+1CB',
    'ROOF AND CEILING': 'R+C',
    'ONE FLOOR ONLY': '1 FLR',
}


_SCHED_COLS = ('TAG', 'B/L', 'WALL', 'CARRIES', 'WD', 'HEADER', 'J/F', 'SPAN', 'TABLE', 'OPEN.')


def _sched_cols(size, rows):
    """[x offset] and [width] per column, each sized to its widest cell — the header row
       included — so every cell is guaranteed to fit the column that holds it."""
    widths = []
    for i, head in enumerate(_SCHED_COLS):
        w = pdfmetrics.stringWidth(head, 'Helvetica-Bold', size)
        for row in rows:
            w = max(w, pdfmetrics.stringWidth(row[i], 'Helvetica', size))
        widths.append(w)
    pad = 1.5
    offsets = [0.0]
    for w in widths[:-1]:
        offsets.append(offsets[-1]+w+pad)
    return offsets, widths


def _in0(v):
    """inches(), without the leading "0-" inches() prints for a fraction under 1"."""
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


def _header_tags(p, building, *, header_positions):
    """H1.. at each Level 1 opening, on the wall at the opening's center; the schedule
       says the rest, and the Level 2 tags are the same openings a story up."""
    LAY('S-ANNO-TEXT'); cc = p.c
    for tag, x, y in header_positions(building):
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.5)
        cc.circle(p.X(x), p.Y(y), 5.5, fill=1, stroke=1)
        cc.setFillColor(black); cc.setFont('Helvetica-Bold', 3.8); cc.drawCentredString(p.X(x), p.Y(y)-1.4, tag)


def _plan_title(ox, oy, text):
    LAY('S-ANNO-TEXT')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 9.5); c.drawString(ox, oy-0.62*inch, text)
    c.setFont('Helvetica', 7.5); c.drawString(ox, oy-0.77*inch, 'SCALE: 1/8" = 1\'-0"')
    c.setLineWidth(1.0); c.setStrokeColor(black); c.line(ox, oy-0.46*inch, ox+2.2*inch, oy-0.46*inch)

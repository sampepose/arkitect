"""What every sheet module needs: somewhere to draw, and the corners to draw between.

`c` is a stand-in, not a canvas. Every renderer reads it as a module global and each read
resolves to the canvas of the document THIS THREAD is drawing (lib/draw/context.py), so
it is stateless and one of it serves every project. The corners are the ARCH C drawing
area; a sheet on another page size takes its own from `Page.DA`.

A drawing helper that a second project needs goes in this package, reading these — never
into that project's copy of a sheet module.
"""
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from lib.draw.page import DA, GREY, LAY, canvas_proxy
from lib.draw.text import wrap_notes
from lib.units import fmt

c = canvas_proxy()

X0, Y0, X1, Y1 = DA
DW, DH = X1 - X0, Y1 - Y0

Q = 18.0      # 1/4" = 1'-0"  -> 18 pt per foot
E = 9.0       # 1/8" = 1'-0"


def knockout(x, y, text, font, size, align="l", pad=1.0):
    """Draw a label on a white ground. The elevations are rendered — siding courses, roof
       tone, grade hatch — and a label that lands on that texture would lose contrast, so
       it is lifted off it. `align` is l, c or r, as drawString, drawCentredString and
       drawRightString take their x."""
    w = pdfmetrics.stringWidth(text, font, size)
    x0 = x if align == "l" else (x-w/2.0 if align == "c" else x-w)
    c.saveState(); c.setFillColor(white)
    c.rect(x0-pad, y-size*0.25, w+2*pad, size*1.0, fill=1, stroke=0)
    c.restoreState()
    c.setFont(font, size)
    {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[align](x, y, text)


def draw_runs(x, y, lines, size, lead, limit=None, where=""):
    """Draw lines built of (text, bold) runs from (x, y) downward, one `lead` per line,
       and return the y after the last one. An empty list is a blank line.

       A line whose weight changes partway cannot be one drawString: the block under the
       zoning table sets its heading, its numbers and each request's name in bold and the
       rest of the line regular, so each run is drawn where the run before it ended.

       `limit` is the column width. It is checked against the sum of the runs, which is
       the only width that means anything once a line is more than one font."""
    for runs in lines:
        if limit is not None:
            w = sum(pdfmetrics.stringWidth(t, _relief_font(b), size) for t, b in runs)
            assert w <= limit, ("%s line is %.2f in wide in a %.2f in column: %r"
                                % (where or "runs", w/inch, limit/inch,
                                   "".join(t for t, _ in runs)))
        rx = x
        for t, bold in runs:
            c.setFont(_relief_font(bold), size)
            c.drawString(rx, y, t)
            rx += pdfmetrics.stringWidth(t, _relief_font(bold), size)
        y -= lead
    return y


def _relief_font(bold):
    return "Helvetica-Bold" if bold else "Helvetica"


def fmt_in(v):
    """Feet-and-inches, but drop the 0'- from a margin small enough to read in inches."""
    return fmt(v).split("-", 1)[1] if 0 < v < 1 else fmt(v)


# Level datums, the one piece of drawing more than one sheet does: A-301's sections
# and the elevations both label the same heights, and a datum that disagreed between
# them would be a defect no single sheet could show you.
def datum_labels(Xp,Yp,end,items,lead_from=None):
    """Exact-level leaders with separated labels for closely spaced F1/F2 plates.
       lead_from pushes the labels clear of something standing off the end of the
       elevation — the Unit 3 stair — while the leader still starts at the wall."""
    c.setFont("Helvetica",6.2); c.setFillColor(black); c.setStrokeColor(GREY); c.setLineWidth(.35)
    lf = end if lead_from is None else lead_from
    previous=-1e9
    for lv,lb in sorted(items):
        yy=max(Yp(lv)-2,previous+10)
        c.line(Xp(lf),Yp(lv),Xp(end)+8,Yp(lv))
        c.line(Xp(end)+8,Yp(lv),Xp(end)+16,yy+2)
        c.drawString(Xp(end)+19,yy,lb)
        previous=yy


def _fits(t, font, size, limit, where):
    assert pdfmetrics.stringWidth(t, font, size) <= limit, '%s runs out of its column: %r' % (where, t)


def title(ox, oy, text):
    c.setFillColor(black); c.setFont('Helvetica-Bold', 11); c.drawString(ox, oy-0.78*inch, text)
    c.setFont('Helvetica', 8); c.drawString(ox, oy-0.94*inch, 'SCALE: 1/4" = 1\'-0"')
    c.setLineWidth(1.2); c.setStrokeColor(black); c.line(ox, oy-0.58*inch, ox+2.6*inch, oy-0.58*inch)


def notes_block(x, y, width, notes, heading, layer, what, cols=2, size=5.6, lead=7.4, gap=0.18*inch, see=None):
    """A discipline's numbered notes under their heading, re-flowed into `cols` columns of the
       given total width; returns the y it ended on. `see` names the sheet that carries the block
       when this one only points to it. `what` names the note in the overrun message."""
    if see:
        # The second sheet of the pair carries no copy of the block, only the pointer.
        c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
        c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= lead+2
        c.setFont('Helvetica', size); c.drawString(x, y, 'SEE %s.' % see)
        return y-lead
    LAY(layer)
    cw = (width-gap*(cols-1))/cols
    lines = wrap_notes(notes, cw, size)
    per = -(-len(lines)//cols)
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= lead+2
    c.setFont('Helvetica', size)
    top = y
    for k in range(cols):
        yy = top
        for t in lines[k*per:(k+1)*per]:
            _fits(t, 'Helvetica', size, cw, what)
            c.drawString(x+k*(cw+gap), yy, t); yy -= lead
    return top-per*lead

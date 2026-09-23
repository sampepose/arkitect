"""A drain standing in an exterior wall's stud cavity, drawn: the pipe, what is left behind
it, and what protects it where it passes framing.

It lives here rather than in lib/draw because every label on it names a section -- OPC 305.4
for the freezing the insulation outboard of the pipe prevents, RCO 602.6.1 for the plate a
bored hole weakens, RCO 302.4 where the wall is rated -- and lib/ is code-neutral
(lib/verify/test_neutrality.py).

Why it exists (a plan reviewer's comment, 2026-09-20): "Stack F now explicitly
occupies the exterior-wall stud cavity, while the wall assembly still specifies R-21 cavity
insulation ... Show the insulation arrangement, floor-line protection and pipe fittings in
section. Simply specifying insulation behind the pipe does not reconcile the two details."

He was right, and the arithmetic is the model's own: a "3 inch" DWV pipe is 3-1/2" across, a
2x6 cavity is 5-1/2" deep, and the batt the schedule names is the whole 5-1/2". A plumbing
note and an assembly schedule each looked right alone and neither sheet could see the other.
lib/model/fit.py's cavity_violations() is the check; this is the drawing it answers to.
"""
from reportlab.lib.colors import black, white

from lib.draw.kit import c, knockout
from lib.draw.page import GREY
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics

SUB = 5.8
TITLE = 8.4


def _vdim(x, y0, y1, text, size=SUB, tick=2.4):
    """A dimension between two heights, its figure to the left of it. The wall is drawn in
       PLAN with the exterior at the top, so every thickness on it reads vertically."""
    c.setStrokeColor(black); c.setLineWidth(0.5)
    c.line(x, y0, x, y1)
    for yy in (y0, y1):
        c.line(x-tick, yy, x+tick, yy)
    c.setFillColor(black)              # knockout draws in the CURRENT fill, and the section
    knockout(x-3.5, (y0+y1)/2.0-2.0, text, "Helvetica", size, align='r')   # leaves it white


def stack_in_cavity(x, y, width, wall, pipe, fill, dims, sheet_scale, title, sub,
                    extra_label='RATED EXTERIOR LAYER', added_label='DEEPER FRAMING AT THIS BAY',
                    notes=(), plate_note=''):
    """The plan section, and under it the plate the stack is bored through.

       `wall` is (sheathing, extra, cavity, added, finish) in FEET, exterior to interior --
       `extra` being the rated exterior layer where there is one and `added` whatever gives
       this bay more depth than the wall's typical cavity. Where the wall is a listed
       assembly whose board fastens to its studs, that is DEEPER STUDS and not furring. `pipe` is (pipe OD, FITTING OD, label): the
       section is cut through the FITTING, because that is the widest thing on the line and
       the only one a bay has to clear. `fill` is (thickness, label), and `dims` carries the
       figures the finding turns on, already formatted by the caller. Everything is drawn from
       those figures, so the detail cannot disagree with the model that made them.

       Returns the y it finished at."""
    sheathing, extra, cavity, added, finish = wall
    od, fitting, pipe_label = pipe
    fill_t, fill_label = fill
    total = sheathing+extra+cavity+added+finish
    s = sheet_scale                                  # points per foot

    # ---- the plan section: exterior at the top, interior at the bottom
    c.setFillColor(black); c.setFont("Helvetica-Bold", TITLE)
    c.drawString(x, y, title); y -= 0.13*inch
    c.setFont("Helvetica", SUB); c.setFillColor(black)
    c.drawString(x, y, sub); y -= 0.20*inch

    bay = 0.75                                       # ft of wall drawn, a stud each side
    stud = 1.5/12.0
    x0 = x+0.80*inch                                 # room for the dimension strings at the left
    top = y
    bot = top-total*s

    def Y(d):                                        # d feet in from the EXTERIOR face
        return top-d*s

    # sheathing, and the rated layer where there is one
    c.setLineWidth(0.7); c.setStrokeColor(black)
    c.setFillColor(GREY)
    c.rect(x0, Y(sheathing), bay*s, sheathing*s, fill=1, stroke=1)
    if extra > 0:
        c.setFillColor(white)
        c.rect(x0, Y(sheathing+extra), bay*s, extra*s, fill=1, stroke=1)
    # the two studs bounding the bay, drawn their WHOLE depth: where the bay is deeper than
    # the wall, that is one deeper stud, not a stud with something added to its face
    c.setFillColor(GREY)
    for sx in (x0, x0+bay*s-stud*s):
        c.rect(sx, Y(sheathing+extra+cavity+added), stud*s, (cavity+added)*s, fill=1, stroke=1)
    # what fills the cavity behind the line, against the sheathing
    fx0 = x0+stud*s
    fw = bay*s-2*stud*s
    c.setFillColor(GREY)
    c.rect(fx0, Y(sheathing+extra+fill_t), fw, fill_t*s, fill=1, stroke=1)
    # The FITTING, cut through: the sanitary tee at the connection, which is what the bay has
    # to clear. The pipe it receives is drawn inside it dashed, so both read at once and the
    # difference between them -- the hub -- is the thing this detail exists to show.
    cx = x0+bay*s/2.0
    cy = Y(sheathing+extra+fill_t+fitting/2.0)
    c.setFillColor(white); c.setLineWidth(1.3); c.setStrokeColor(black)
    c.circle(cx, cy, fitting*s/2.0, fill=1, stroke=1)
    c.setLineWidth(0.8); c.setDash(2.4, 1.8)
    c.circle(cx, cy, od*s/2.0, fill=0, stroke=1)
    c.setDash()
    # the interior finish, on the furring, and the steel plate that protects the line
    c.setFillColor(white); c.setLineWidth(0.7)
    c.rect(x0, Y(total), bay*s, finish*s, fill=1, stroke=1)
    c.setLineWidth(1.6); c.setStrokeColor(black)
    c.line(cx-fitting*s/2.0-3.0, Y(sheathing+extra+cavity+added),
           cx+fitting*s/2.0+3.0, Y(sheathing+extra+cavity+added))

    # ---- the figures the reviewer's arithmetic turns on, at the left
    _vdim(x0-0.50*inch, Y(sheathing+extra), Y(sheathing+extra+cavity), dims['cavity'])
    if added > 0:
        _vdim(x0-0.50*inch, Y(sheathing+extra+cavity),
              Y(sheathing+extra+cavity+added), dims['added'])
    _vdim(x0-0.14*inch, Y(sheathing+extra), Y(sheathing+extra+fill_t), dims['fill'])
    _vdim(x0-0.14*inch, Y(sheathing+extra+fill_t),
          Y(sheathing+extra+fill_t+fitting), dims['fitting'])

    # ---- the parts, numbered on the section and keyed under it. The labels do not stand
    # beside it: this block is 4-3/4 in wide and a leader long enough to name a layer runs
    # into whatever is in the next column.
    rows = [(Y(sheathing/2.0), 'SHEATHING'),
            (Y(sheathing+extra+fill_t/2.0), fill_label),
            (cy, pipe_label),
            (Y(total-finish/2.0), 'INTERIOR FINISH, AND A STEEL PROTECTION PLATE OVER THE LINE')]
    if added > 0:
        rows.insert(3, (Y(sheathing+extra+cavity+added/2.0), added_label))
    if extra > 0:
        rows.insert(1, (Y(sheathing+extra/2.0), extra_label))
    nx = x0+bay*s+0.10*inch
    for i, (yy, _t) in enumerate(rows, 1):
        c.setStrokeColor(black); c.setLineWidth(0.4)
        c.line(x0+bay*s+2.0, yy, nx-1.0, yy)
        c.setFillColor(black)
        knockout(nx, yy-2.0, '%d' % i, "Helvetica-Bold", SUB)
    y = bot-0.26*inch
    for i, (_yy, t) in enumerate(rows, 1):
        line = '%d.  %s' % (i, t)
        # The notes under this block are wrapped to `width`; the keys were not, and a key
        # long enough to name a fitting ran past it into the next column. Nothing sees that
        # but the eye, so it is asserted here.
        assert pdfmetrics.stringWidth(line, "Helvetica", SUB) <= width, \
            'a stack-bay key overruns its %.2f in block: %r' % (width/inch, line)
        c.setFillColor(black); c.setFont("Helvetica", SUB)
        c.drawString(x, y, line)
        y -= 0.125*inch
    y -= 0.08*inch

    # ---- the plate, under it
    if plate_note:
        c.setFillColor(black); c.setFont("Helvetica-Bold", SUB)
        c.drawString(x, y, plate_note); y -= 0.15*inch
    for t in notes:
        c.setFillColor(black); c.setFont("Helvetica", SUB)
        c.drawString(x, y, t); y -= 0.125*inch
    return y

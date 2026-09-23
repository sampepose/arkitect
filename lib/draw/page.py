"""Permit drawing set — plain line work on a titled sheet.

Most of a set is one size, but not all of it: a zoning site plan is submitted at
11 x 17 because the reviewing department asks for that, so the sheet size cannot be
four module constants. `Page` holds one size and the areas derived from it; ARCH_C is
this set's, and the module-level PW / PH / DA are ARCH_C's, kept because that is how
every sheet already reads them."""
from reportlab.lib.units import inch
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics

# ---------------- the document being drawn ----------------
# The canvas, the current layer, the observers and the colours moved to
# lib/draw/context.py — unchanged, and re-exported here, because lib/draw/plan.py needs
# them too and cannot import this module: page.py re-exports PlanDraw, just below, so
# an import back the other way is a cycle. page.observe, page.LAY,
# page.POCHE and the rest still resolve here, which is where every caller reads them.
from lib.draw import context as _ctx
from lib.draw.context import current, live_canvas, _announce
GREY, LGREY, POCHE = _ctx.GREY, _ctx.LGREY, _ctx.POCHE
BuildContext = _ctx.BuildContext
document = _ctx.document
canvas_proxy = _ctx.canvas_proxy
DEFAULT_OBSERVERS = _ctx.DEFAULT_OBSERVERS
observe = _ctx.observe
unobserve = _ctx.unobserve
LAY = _ctx.LAY


def end_plans():
    """Announce that the sheet's plans are drawn and what follows is sheet-level —
       schedules, legends, notes. The DXF exporter stops recording at this; the trace
       does not care. A sheet whose text sits within a few feet of a plan calls it."""
    _announce('plan_end', None)
current_layer = _ctx.current_layer

# The plan drawn inside the frame moved to lib/draw/plan.py — it was half of this
# module, and a plan is not the sheet it sits on. Re-exported so that every existing
# `from lib.draw.page import PlanDraw` keeps working. plan.py takes the layer and the
# colours from context.py, not from here, so this import runs in one direction only.
from lib.draw import plan as _plan
PlanDraw = _plan.PlanDraw


class Page:
    """One sheet size, and the drawing area left after its margin and title block.

    W, H    the sheet
    MARG    border margin
    TBW     title block width, down the right-hand edge
    DA      (x0, y0, x1, y1) of the drawing area, inset a further 1/4 in
    """
    def __init__(s, w, h, tbw=3.4*inch, marg=0.5*inch):
        s.W, s.H, s.TBW, s.MARG = w, h, tbw, marg
        s.DA = (marg+0.25*inch, marg+0.25*inch,
                w-marg-tbw-0.25*inch, h-marg-0.25*inch)
    @property
    def size(s):
        return (s.W, s.H)


ARCH_C = Page(24*inch, 18*inch)                              # the set
ANSI_B = Page(17*inch, 11*inch, tbw=3.4*inch, marg=0.35*inch)  # the 11 x 17 zoning sheet

PW, PH = ARCH_C.W, ARCH_C.H
TBW  = ARCH_C.TBW                   # title block width
MARG = ARCH_C.MARG
DA   = ARCH_C.DA                    # drawing area


# The title block a sheet carries when it is not given one. It belongs to the document
# being drawn, so drawing() passes the project's in and Sheet reads it from there.
# build.py used to install it by assigning `page.TITLEBLOCK = project.TITLEBLOCK` at
# import — one module reaching into another to configure it, which meant importing two
# build scripts in one process left whichever imported last in charge of both.
#
# The module-level value stays as the fallback for a Sheet made with no document open,
# which is how the observer test builds one.
TITLEBLOCK = ()      # see src/project.py for the real one

def current_titleblock():
    ctx = current()
    return (ctx.titleblock if ctx is not None and ctx.titleblock else TITLEBLOCK)


class Sheet:
    def __init__(s,c,no,title,scale,notes="",titleblock=(),page=None):
        s.c=live_canvas(c); s.no=no; s.title=title; s.scale=scale; s.notes=notes
        s.titleblock=titleblock or current_titleblock()
        s.page=page or ARCH_C
        _announce('sheet', s)
    def frame(s):
        c=s.c
        PW, PH, TBW, MARG = s.page.W, s.page.H, s.page.TBW, s.page.MARG
        c.setStrokeColor(black); c.setLineWidth(2)
        c.rect(MARG,MARG,PW-2*MARG,PH-2*MARG)
        x0=PW-MARG-TBW
        c.setLineWidth(1); c.line(x0,MARG,x0,PH-MARG)
        # The title block's CONTENT belongs to a project, not to this library. It is a
        # list of (heading, lines) — heading None for the first block, which is the
        # address and carries the larger type. src/project.py holds the real one.
        # The block is the same on every sheet, but the column it sits in is not: a
        # smaller sheet gets the same text in whatever TBW it was given. Measure it.
        # "FRANKLIN COUNTY PARCEL 010-078120-00" is 2.65 in at 9.5 pt and overran a
        # 2.4 in column the moment an 11 x 17 existed, with nothing to say so.
        avail = TBW-0.44*inch
        def fit(t,fnt,sz):
            assert pdfmetrics.stringWidth(t,fnt,sz)<=avail, (
                "title block line needs %.2f in of a %.2f in column: %r"
                %(pdfmetrics.stringWidth(t,fnt,sz)/inch, avail/inch, t))
            return t
        y=PH-MARG-0.45*inch
        for i,(head,body) in enumerate(s.titleblock):
            if i:
                y-=0.12*inch
                if i==1: c.setLineWidth(0.7)     # set once, as the hand-written block did
                c.line(x0+0.15*inch,y,PW-MARG-0.15*inch,y); y-=0.24*inch
                c.setFont("Helvetica-Bold",8.5); c.drawString(x0+0.22*inch,y,fit(head,"Helvetica-Bold",8.5))
                y-=0.17*inch
                c.setFont("Helvetica",9); step=0.16*inch; fnt,sz="Helvetica",9
            else:
                c.setFont("Helvetica-Bold",13); c.drawString(x0+0.22*inch,y,fit(body[0],"Helvetica-Bold",13))
                y-=0.22*inch; c.setFont("Helvetica",9.5); step=0.17*inch; fnt,sz="Helvetica",9.5
                body=body[1:]
            for ln in body:
                c.drawString(x0+0.22*inch,y,fit(ln,fnt,sz)); y-=step
        # bottom of title block
        yb=MARG+0.3*inch
        c.setFont("Helvetica",8.5)
        c.drawString(x0+0.22*inch,yb+0.95*inch,"SCALE:  "+s.scale)
        c.line(x0+0.15*inch,yb+0.78*inch,PW-MARG-0.15*inch,yb+0.78*inch)
        # fit(), like every other line in this block. It used to be sliced to 34
        # characters, which is not a shorter title but a DIFFERENT one: A-604's
        # "EXTERIOR STAIR SECTIONS AND DETAILS" is 35 characters and printed as
        # "...AND DETAIL", singular, against a G-001 index and a sheet heading that both
        # said DETAILS. The slice was load-bearing without anyone knowing -- at 34
        # characters the title measured 2.93 in of this 2.96 in column, so the real
        # string would have overrun -- which is exactly why it must assert: a title too
        # long for the block is a thing to shorten deliberately, not to truncate mid
        # word on the issued sheet.
        c.setFont("Helvetica-Bold",10.5)
        c.drawString(x0+0.22*inch,yb+0.5*inch,fit(s.title.upper(),"Helvetica-Bold",10.5))
        c.setFont("Helvetica-Bold",26)
        c.drawRightString(PW-MARG-0.22*inch,yb+0.06*inch,fit(s.no,"Helvetica-Bold",26))

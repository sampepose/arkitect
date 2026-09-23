"""The DRAIN, WASTE AND VENT riser both projects' P-601 draws, beside the rules it draws.

It lives here rather than in lib/draw because every label on it names a code section --
OPC 905.4, 909.1, 912.1, 912.1.1, 913 -- and lib/ is code-neutral
(lib/verify/test_neutrality.py); codes/ohio/opc_service_entry_draw.py and
codes/ohio/rco/bracing_draw.py are the same shape.

What it has to show, which a line per stack does not (a plan reviewer's comment,
2026-09-20: "a coordinated drawing should show the traps, vent takeoffs, drain
connections, and vent reconnections. Conventional venting, bathroom wet venting, and
waste-stack venting have different requirements"):

  * every TRAP, drawn where it stands -- on the fixture's arm above the floor, or hanging
    under the slab where the fixture drains below it;
  * every DRAIN CONNECTION, in the order the pipe makes them and at the height it makes
    them, because the order is what 912.1.1 rules on: the water closets lowest, every
    other fixture over them, each connection independent;
  * every VENT TAKEOFF, at the fixture the vent stands on -- 912.2.1 allows one fixture
    upstream of it and 912.2.2 none -- and
  * every VENT RECONNECTION, at the height it is made, which is what 905.4 rules on.

A cell is one riser. Its stack is drawn solid where it carries waste and dashed where it
is a vent, so the height the one becomes the other -- the highest fixture connection -- is
read off the drawing rather than taken on trust. Nothing here decides anything:
opc_vents.py checks the arrangement, and the project builds the Cell from its own model,
so neither project carries a copy of the drawing.
"""
from collections import namedtuple

from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics

from lib.draw.kit import c, knockout
from lib.draw.page import GREY

# A fixture at a connection: what prints, and the small note under it -- the height the
# connection is made at, which is the fact 912.1.1 turns on. `vent` is (mark, size) where
# that fixture's TRAP STANDS ABOVE the floor the branch runs in and so takes a dry vent of
# its own, above its weir and before its drop (909.2); None where the branch is its vent.
Fix = namedtuple('Fix', 'label sub vent')
Fix.__new__.__defaults__ = (None,)
# What hangs on the stack at one level, its fixes LOWEST CONNECTION FIRST, and the name of
# the arrangement that vents them (blank where the level above carries the label).
Hang = namedtuple('Hang', 'level method fixes')
# A branch below the slab and the dry vent standing in it: the vent's mark and size, the
# arrangement, the fixtures IN THE DIRECTION OF FLOW, and where the vent reconnects --
# None where the riser drawn in this cell IS that vent, carried to the roof.
Slab = namedtuple('Slab', 'mark size method fixes tie')
# One riser. `span` brackets the lowest and highest connection of a waste stack vent and
# makes its offset draw at the foot, `note` is the line under the cell, and `increaser` is
# the label for the size change 903.2 asks for where a vent is smaller than the roof takes
# -- drawn on the vent, inside the thermal envelope, because a note that says "at the
# increaser drawn" has to have one to point at.
Cell = namedtuple('Cell', 'title size vent_only vtr levels hangs slabs span note foot increaser floors')
Cell.__new__.__defaults__ = ((),)
# A branch IN A FLOOR above the first -- a bathroom group draining horizontally through the
# floor framing into the TOP of the stack below it, 912.1's horizontal wet vent at an upper
# level: the level it hangs under, the dry vent's mark and size, the arrangement, the
# fixtures in the direction of flow, and where the vent reconnects.
Floor = namedtuple('Floor', 'level mark size method fixes tie')
FLOOR_BR = 0.30                    # the branch under its level's line, inches
FLOOR_PITCH = 0.25                 # one fixture on it to the next
TRAP_OVER = 0.17                   # a trap that STANDS ON that floor, over its line
VENT_STAGGER = 0.19                # one floor vent's reconnection to the next, so the marks clear

W, H = 3.20, 4.55                  # the cell, inches
TITLE, LEVEL, FIX, SUB, METHOD = 8.6, 7.6, 7.2, 7.0, 7.0
STEP = 0.22                        # one connection to the next on a stack
ROW = 0.47                         # one branch below the slab to the next
DOT = 2.3


def _dash(on=True, pat=(3.2, 2.2)):
    c.setDash(*pat) if on else c.setDash()


def _trap(x, y, rise=0.13, w=0.09, dip=0.065, lw=1.0):
    """A P-trap at the end of an arm that arrives at (x, y): the seal dips, and the fixture
       leg rises `rise` to the ticked outlet. Returns the leg's x."""
    c.setLineWidth(lw); c.setStrokeColor(black)
    c.line(x, y, x, y-dip*inch)
    c.line(x, y-dip*inch, x+w*inch, y-dip*inch)
    c.line(x+w*inch, y-dip*inch, x+w*inch, y+rise*inch)
    c.line(x+w*inch-2.0, y+rise*inch, x+w*inch+2.0, y+rise*inch)
    return x+w*inch


def _drop_trap(x, top, y_br, w=0.09, dip=0.065, arm=0.14, lw=1.0):
    """A fixture that drains BELOW a slab: its drop from the floor at `top`, the trap under
       the slab, and the trap arm out and down into the branch at `y_br`. Returns the x the
       connection is made at, which stands off the fixture by the trap and its arm, as it is
       built -- the arm the TRAP ARMS schedule measures."""
    y_arm = y_br+0.20*inch
    y_seal = y_arm-dip*inch
    cx = x+(w+arm)*inch
    c.setLineWidth(lw); c.setStrokeColor(black)
    c.line(x-2.0, top, x+2.0, top)                       # the fixture's outlet, on the floor
    c.line(x, top, x, y_seal)                            # the drop through the slab
    c.line(x, y_seal, x+w*inch, y_seal)                  # the seal
    c.line(x+w*inch, y_seal, x+w*inch, y_arm)
    c.line(x+w*inch, y_arm, cx, y_arm)                   # the trap arm
    c.line(cx, y_arm, cx, y_br)                          # into the branch
    return cx


def _dot(x, y):
    c.setFillColor(black); c.setLineWidth(0.8)
    c.circle(x, y, DOT, fill=1)


def _arrow(x, y, dx=5.0):
    c.setLineWidth(0.9); c.setStrokeColor(black)
    c.line(x, y, x+dx, y)
    c.line(x+dx-3.0, y+2.0, x+dx, y)
    c.line(x+dx-3.0, y-2.0, x+dx, y)


def _cell_label(ox, y, text, w, size=None, lead=0.115, gap=0.10, font="Helvetica-Bold"):
    """A label over a riser, wrapped to the CELL so it cannot run into the next one.

       At 5.4 pt these lines fitted on one line and nothing checked that they did. Raising
       them to something a trade can read in the field (a plan reviewer, 2026-09-20:
       "several plumbing annotations are approximately 5-6-point text at full sheet size,
       which is difficult to use in the field") made three of them overflow into the
       neighbouring riser, so the width is now enforced rather than hoped for."""
    size = SUB if size is None else size
    room = (w-gap)*inch
    words, lines, cur = text.split(' '), [], ''
    for word in words:
        trial = (cur+' '+word).strip()
        if cur and pdfmetrics.stringWidth(trial, font, size) > room:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    for i, ln in enumerate(lines):
        assert pdfmetrics.stringWidth(ln, font, size) <= room+0.5, \
            'a riser label does not fit its cell at %.1f pt: %r' % (size, ln[:48])
        knockout(ox, y+(len(lines)-1-i)*lead*inch, ln, font, size)
    return y+(len(lines)-1)*lead*inch


def _bracket(x, y0, y1, label, tick=0.05):
    """A span down the left of the stack, its label turned out at the middle."""
    c.setStrokeColor(black); c.setLineWidth(0.6); _dash(False)
    c.line(x, y0, x, y1)
    for y in (y0, y1):
        c.line(x, y, x+tick*inch, y)
    knockout(x-2.0, (y0+y1)/2.0-1.5, label, "Helvetica-Bold", SUB, align="r")


def riser(ox, oy, cell, w=W, h=H):
    """One riser cell, drawn from its bottom-left corner. Returns the top of its title."""
    xs = ox+0.46*w*inch                          # the stack
    x_end = ox+0.85*w*inch                       # where the drain leaves the cell
    y_note = oy+0.02*inch
    y_lv = {1: oy+1.30*inch, 2: oy+2.70*inch}
    y_ft = oy+1.16*inch                          # the stack's foot, under the lowest branch's traps
    y_top = oy+h*inch-0.30*inch

    # ---- what the stack carries, and the height from which it is only a vent ----
    conns = []
    for hg in cell.hangs:
        for i, fx in enumerate(hg.fixes):
            conns.append((y_lv[hg.level]+0.16*inch+i*STEP*inch, fx))
    highest = max((y for y, _f in conns), default=y_lv[1])
    for fl in cell.floors:                       # a branch in a floor ends the waste at its junction
        highest = max(highest, y_lv[fl.level]-FLOOR_BR*inch)
    # a slab vent reconnects above every fixture the stack carries, which a floor's group stands over
    vent_base = max([highest]+[y_lv[fl.level]+0.62*inch for fl in cell.floors])

    c.setFillColor(black); c.setFont("Helvetica-Bold", TITLE)
    c.drawString(ox, oy+h*inch, cell.title)
    c.setStrokeColor(black); c.setLineWidth(1.9)
    if cell.vent_only:
        _dash(); c.line(xs, oy+0.85*inch, xs, y_top); _dash(False)
    else:
        c.line(xs, y_ft, xs, highest)            # waste
        _dash(); c.line(xs, highest, xs, y_top); _dash(False)   # the stack vent over it
    c.setLineWidth(1.0)
    c.line(xs-3.0, y_top, xs+4.0, y_top+5.0)                    # the roof
    c.setFillColor(black); c.setFont("Helvetica", SUB)
    c.drawString(xs+6.0, y_top+3.0, cell.vtr)
    if cell.increaser:                           # 903.2, where the roof takes more than the pipe
        iy = y_top-0.30*inch
        c.setLineWidth(0.9); c.setStrokeColor(black)
        c.line(xs-0.07*inch, iy, xs+0.07*inch, iy)
        c.setFillColor(black); c.setFont("Helvetica", SUB)
        c.drawString(xs+0.10*inch, iy-2.0, cell.increaser)

    # ---- the levels ----
    for lv, label in sorted(cell.levels.items()):
        c.setStrokeColor(GREY); c.setLineWidth(0.7)
        c.line(ox, y_lv[lv], ox+0.94*w*inch, y_lv[lv])
        c.setStrokeColor(black)
        knockout(ox, y_lv[lv]+3.0, label, "Helvetica-Bold", LEVEL)

    # ---- every fixture ON the stack: its connection, its arm, its trap ----
    for y, fx in conns:
        _dot(xs, y)
        c.setStrokeColor(black); c.setLineWidth(1.0)
        c.line(xs, y, xs+0.30*inch, y)
        tx = _trap(xs+0.30*inch, y, 0.12)
        c.setFillColor(black); c.setFont("Helvetica", FIX)
        c.drawString(tx+5.0, y-1.0, fx.label)
        if fx.sub:
            c.setFont("Helvetica", SUB)
            c.drawString(tx+5.0, y-8.0, fx.sub)
    for hg in cell.hangs:
        if hg.method:
            # right of the stack, where nothing else runs: the dry vents rise at the left
            knockout(ox+0.94*w*inch, y_lv[hg.level]-8.0, hg.method, "Helvetica-Bold", METHOD,
                     align="r")
    if cell.span is not None and conns:
        _bracket(xs-0.13*inch, min(y for y, _f in conns), max(y for y, _f in conns), cell.span)

    # ---- the branches below the slab, and the dry vent standing in each ----
    for n, sl in enumerate(cell.slabs):
        y_br = oy+(0.85-ROW*n)*inch
        # the dry vent stands on the HEAD fixture's connection, so the branch is set out
        # from it: where this cell's riser is that vent, the head lands on the riser.
        x0 = xs-0.23*inch if sl.tie is None else ox+0.05*w*inch
        made = []
        for i, fx in enumerate(sl.fixes):
            fx_x = x0+i*0.46*inch
            cx = _drop_trap(fx_x, y_lv[1], y_br)
            made.append(cx)
            c.setFillColor(black); c.setFont("Helvetica", SUB)
            c.drawCentredString(fx_x+3.0, y_br-0.13*inch, fx.label)
        head = made[0]
        c.setStrokeColor(black); c.setLineWidth(1.4)
        c.line(head, y_br, x_end, y_br)                  # the branch, in the direction of flow
        _arrow(x_end, y_br)
        for cx in made:
            _dot(cx, y_br)
        # the takeoff, at the fixture the vent stands on, and where it reconnects
        c.setStrokeColor(black); c.setLineWidth(1.3); _dash()
        if sl.tie is None:                       # this cell's riser IS that vent
            _dash(False)
            knockout(xs+6.0, y_lv[2]+0.34*inch, '%s  %s  %s' % (sl.mark, sl.size, sl.method),
                     "Helvetica-Bold", SUB)
        else:
            top = vent_base+0.10*inch+n*0.20*inch
            c.line(head, y_br, head, top)
            c.line(head, top, xs, top)
            _dash(False); _dot(xs, top)
            _cell_label(ox, top+3.0, '%s  %s  %s — %s' % (sl.mark, sl.size, sl.method, sl.tie), w)

    # ---- a branch in a floor, into the stack's top, and the dry vents that protect it ----
    # A fixture whose trap hangs IN this floor (a closet bend, a tub) is vented by the branch
    # itself, 912.1. A fixture whose trap STANDS ON the floor is not: 909.2 keeps the vent
    # connection within the drain's diameter of the weir and a drop through a floor is feet of
    # it, so each such fixture carries its own vent up from its arm. Drawing them alike said
    # the lavatories were vented from under the floor they stand on, which is the thing the
    # section forbids.
    for fl in cell.floors:
        y_fl = y_lv[fl.level]
        y_br = y_fl-FLOOR_BR*inch
        y_arm = y_fl+TRAP_OVER*inch
        x0 = ox+0.14*w*inch                      # clear of a slab vent rising at the cell's left edge
        top = y_top-0.44*inch
        made, risers = [], []
        for i, fx in enumerate(fl.fixes):
            fx_x = x0+i*FLOOR_PITCH*inch
            if fx.vent:
                _trap(fx_x, y_arm)                       # its trap, on its arm over the floor
                c.setStrokeColor(black); c.setLineWidth(1.0)
                c.line(fx_x, y_arm, fx_x, y_br)          # and its drain, down through the floor
                made.append(fx_x)
                risers.append((fx_x, fx.vent))
            else:
                made.append(_drop_trap(fx_x, y_fl, y_br, arm=0.05))
            c.setFillColor(black); c.setFont("Helvetica", SUB)
            c.drawCentredString(made[-1], y_br-0.13*inch, fx.label)       # under its connection
        head = made[0]
        c.setStrokeColor(black); c.setLineWidth(1.4)
        c.line(head, y_br, xs, y_br)                     # the branch, in the direction of flow
        for cx in made:
            _dot(cx, y_br)
        _dot(xs, y_br)                                   # into the stack's top
        # Each vent up from its own fixture's arm -- the takeoff is above the weir -- and over
        # to the stack's vent, each at its OWN height: two vents a quarter inch apart in plan
        # cannot carry two labels side by side once the type is big enough to read. Every LINE
        # first and the marks after them, because a knockout the run is drawn over afterwards
        # is a label with a dash through it.
        c.setStrokeColor(black); c.setLineWidth(1.3); _dash()
        for i, (rx, _v) in enumerate(risers):
            c.line(rx, y_arm, rx, top-i*VENT_STAGGER*inch)
            c.line(rx, top-i*VENT_STAGGER*inch, xs, top-i*VENT_STAGGER*inch)
        if not risers:
            c.line(head, top, xs, top)
        _dash(False); _dot(xs, top)
        for i, (rx, (mark, size)) in enumerate(risers):
            c.setFillColor(black)
            knockout(rx+2.0, top-i*VENT_STAGGER*inch+2.2, '%s %s' % (mark, size),
                     "Helvetica-Bold", SUB)
        _cell_label(ox, top+0.17*inch, '%s — %s' % (fl.method, fl.tie), w)

    # ---- the foot: the offset a waste stack makes to it is drawn, 913.2 ----
    if cell.foot:
        c.setStrokeColor(black); c.setLineWidth(1.6)
        if cell.span is not None:
            jog = 0.30*inch
            c.line(xs, y_ft+0.14*inch, xs+jog, y_ft+0.14*inch)
            c.line(xs+jog, y_ft+0.14*inch, xs+jog, y_ft)
            c.line(xs+jog, y_ft, x_end, y_ft)
        else:
            c.line(xs, y_ft, x_end, y_ft)
        _arrow(x_end, y_ft)
        c.setFillColor(black); c.setFont("Helvetica", SUB)
        c.drawRightString(x_end, y_ft-9.0, cell.foot)     # under the line: the level's
        #                                                    method label rides over it
    if cell.note:
        # wrapped to its own cell: at 5.4 pt this fitted on one line, and at a size a trade
        # can read two neighbouring cells' notes ran into one another. sheet_text.py did not
        # see it -- the strings share a baseline but it pairs only what it is looking for.
        c.setFillColor(black)
        _cell_label(ox, y_note, cell.note, w, font="Helvetica")
    return oy+h*inch


def legend(x, y, width, lead=0.128):
    """How to read it: the two line weights and the two marks."""
    c.setFillColor(black); c.setFont("Helvetica-Bold", 7.2)
    c.drawString(x, y, "HOW TO READ THE RISER"); y -= 3
    c.setStrokeColor(black); c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= 0.16*inch
    rows = [(1.9, False, ["SOLID: WASTE, BELOW THE STACK'S",
                          "HIGHEST FIXTURE CONNECTION."]),
            (1.9, True,  ["DASHED: VENT. NOTHING DRAINS IN."]),
            (None, None, ["A CONNECTION, MADE WHERE DRAWN;",
                          "ITS HEIGHT PRINTS BESIDE IT."]),
            ('trap', None, ["A TRAP, ON ITS FIXTURE'S ARM."])]
    indent = 0.30*inch
    for kind, dashed, lines in rows:
        if kind == 'trap':
            _trap(x+0.04*inch, y+2.0, 0.10)
        elif kind is None:
            _dot(x+0.11*inch, y+2.0)
        else:
            c.setStrokeColor(black); c.setLineWidth(kind)
            _dash(dashed); c.line(x, y+2.0, x+0.22*inch, y+2.0); _dash(False)
        c.setFillColor(black); c.setFont("Helvetica", SUB)
        for t in lines:
            # the legend sits in the last column on the sheet, so a line that outgrows it
            # runs into the frame rather than into another drawing, where it is easy to miss
            assert pdfmetrics.stringWidth(t, "Helvetica", SUB) <= width-indent, \
                'the riser legend does not fit its column at %.1f pt: %r' % (SUB, t)
            c.drawString(x+indent, y, t)
            y -= lead*inch
        y -= 0.03*inch
    return y


# ---------------------------------------------------------------- the isometric
# A riser is one vertical line per stack: it can say WHICH pipe vents a trap and at what
# height, and it cannot say where either stands in the room. An ISOMETRIC can, which is why a
# reviewer asked for one where "the actual bathroom connections remain schematic" (2026-09-20). It carries the fact a plan and a riser both lose: whether a vent leaves the
# fixture's drain ABOVE the weir of its trap, which is 909.2 and is the whole difference
# between a vented lavatory and an unvented one.
#
# The projection is the ordinary plumbing isometric -- the two horizontal axes at 30 degrees,
# the vertical true -- taken straight off the model's own feet, so what is drawn is a
# PROJECTION of the model and not a diagram beside it. It is not to scale the way a plan is;
# every length, size and height that a trade builds to is printed.
ISO_COS30 = 0.8660254037844387
ISO_SIN30 = 0.5
ISEG_W = {1.5: 0.9, 2.0: 1.3, 3.0: 2.1, 4.0: 2.6}      # a nominal size to a line weight

# a length of pipe between two points in feet, (x, y, z), z positive UP from the floor datum
ISeg = namedtuple('ISeg', 'a b size kind')             # kind: 'drain' | 'vent'
# something AT a point: a trap, a fitting, a plain connection, or the break a pipe runs off at
INode = namedtuple('INode', 'at sym text side')        # sym: 'trap' 'tee' 'bend' 'wye' 'dot' 'break'
INode.__new__.__defaults__ = ('', 'r')
ILabel = namedtuple('ILabel', 'at text side bold')
ILabel.__new__.__defaults__ = ('r', False)


def _iso_pt(p):
    """Model feet -> the isometric's own plane, before it is fitted to a box."""
    x, y, z = p
    return ((x-y)*ISO_COS30, z-(x+y)*ISO_SIN30)


def _iso_fit(pts, x, y, w, h, pad):
    """The scale and origin that put every point inside the box, with room for labels."""
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]
    dx = max(xs)-min(xs) or 1.0
    dz = max(zs)-min(zs) or 1.0
    s = min((w-2*pad*inch)/dx, (h-2*pad*inch)/dz)
    ox = x+pad*inch-min(xs)*s+((w-2*pad*inch)-dx*s)/2.0
    oy = y+pad*inch-min(zs)*s+((h-2*pad*inch)-dz*s)/2.0
    return s, ox, oy


def _iso_sym(sym, px, py, s):
    """The trap or fitting at a point. A trap is drawn as the seal it is; a fitting is a tick
       across the run, because what a plumber reads is the fitting NAMED beside it."""
    c.setStrokeColor(black); c.setFillColor(black)
    if sym == 'dot':
        c.circle(px, py, 2.1, fill=1, stroke=0)
    elif sym == 'trap':
        d = 0.075*s
        c.setLineWidth(1.1)
        c.line(px, py, px, py-d)
        c.line(px, py-d, px+d*ISO_COS30, py-d-d*ISO_SIN30)
        c.line(px+d*ISO_COS30, py-d-d*ISO_SIN30, px+d*ISO_COS30, py+d*0.9-d*ISO_SIN30)
    elif sym == 'break':
        c.setLineWidth(1.0)
        c.line(px-3.0, py-2.2, px+3.0, py-0.6)
        c.line(px-3.0, py+0.6, px+3.0, py+2.2)
    else:                                   # tee, bend, wye: a tick square across the run
        c.setLineWidth(1.2)
        c.line(px-3.0, py-1.7, px+3.0, py+1.7)


def _iso_span(px, text, side, bold, size):
    """The x range a label will occupy, so the caller can prove it stays on the sheet."""
    font = "Helvetica-Bold" if bold else "Helvetica"
    w = pdfmetrics.stringWidth(text, font, size)
    dx = {'l': -5.0, 'r': 5.0}.get(side, 0.0)
    if side == 'l':
        return (px+dx-w, px+dx)
    if side in ('u', 'd'):
        return (px-w/2.0, px+w/2.0)
    return (px+dx, px+dx+w)


def _iso_text(px, py, text, side, bold, size):
    if not text:
        return
    c.setFillColor(black)              # knockout draws in the CURRENT fill: say which
    font = "Helvetica-Bold" if bold else "Helvetica"
    dx = {'l': -5.0, 'r': 5.0}.get(side, 0.0)
    dy = {'u': 5.0, 'd': -8.5}.get(side, -2.2)
    align = 'r' if side == 'l' else ('c' if side in ('u', 'd') else 'l')
    knockout(px+dx, py+dy, text, font, size, align=align)


def isometric(x, y, w, h, segs, nodes, labels, title, sub, caption=(), size=6.8, pad=0.30):
    """One bathroom group in three dimensions, in the box (x, y) to (x+w, y+h).

       `segs` is the pipe, `nodes` the traps and fittings on it, `labels` what prints beside
       it -- all in the model's own feet, which is what makes this a projection of the model
       rather than a picture drawn next to one. A drain is solid and weighted by its size, a
       vent dashed, so the takeoff -- the height the one becomes the other -- is read off the
       drawing instead of taken on trust."""
    cap_h = len(caption)*0.115*inch
    pts = [_iso_pt(p) for sg in segs for p in (sg.a, sg.b)]
    pts += [_iso_pt(n.at) for n in nodes]+[_iso_pt(lb.at) for lb in labels]
    s, ox, oy = _iso_fit(pts, x, y, w, h-cap_h, pad)

    def P(p):
        px, py = _iso_pt(p)
        return (ox+px*s, oy+cap_h+py*s)

    c.setFillColor(black); c.setFont("Helvetica-Bold", TITLE)
    c.drawString(x, y+h+0.10*inch, title)
    c.setFillColor(black); c.setFont("Helvetica", SUB)
    c.drawString(x, y+h+0.01*inch, sub)
    cy = y+cap_h-0.09*inch                            # the figures, under the drawing
    for ln in caption:
        c.setFillColor(black); c.setFont("Helvetica", size)
        c.drawString(x, cy, ln)
        cy -= 0.115*inch
    for want in ('drain', 'vent'):                    # the drains first, the vents over them
        for sg in segs:
            if sg.kind != want:
                continue
            a, b = P(sg.a), P(sg.b)
            c.setStrokeColor(black); c.setLineWidth(ISEG_W.get(sg.size, 1.2))
            _dash(want == 'vent')
            c.line(a[0], a[1], b[0], b[1])
            _dash(False)
    # A label that runs off the box lands in whatever is beside it -- on P-601 that is the
    # title block, where it printed once. Nothing else on the sheet can see that: the trace
    # records the string wherever it went and sheet_text.py only pairs overlapping strings.
    for n in nodes:
        px, py = P(n.at)
        _iso_sym(n.sym, px, py, s)
        lo, hi = _iso_span(px, n.text, n.side, True, size)
        assert not n.text or (lo >= x-1.0 and hi <= x+w+1.0), \
            'the isometric label %r runs %.2f in off its box' % (n.text[:40], max(x-lo, hi-x-w)/inch)
        _iso_text(px, py, n.text, n.side, True, size)
    for lb in labels:
        px, py = P(lb.at)
        lo, hi = _iso_span(px, lb.text, lb.side, lb.bold, size)
        assert lo >= x-1.0 and hi <= x+w+1.0, \
            'the isometric label %r runs %.2f in off its box' % (lb.text[:40], max(x-lo, hi-x-w)/inch)
        _iso_text(px, py, lb.text, lb.side, lb.bold, size)
    return y

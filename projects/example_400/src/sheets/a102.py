"""A-102 — Building 2's floor plans: Units 2 and 3, and the Unit 3 exterior stair.

Bound as A-102, after the house's A-101 (the designer, 2026-09-18); on 300, where this code comes
from, it was A-103. Moved out of src/sheets/plans.py (300's plan module) so that drawing
Building 2 no longer loads 300's Building 1 plan code. The two functions are unchanged.
"""
from arkitect.lib.draw.page import GREY, LAY, POCHE, Sheet
from arkitect.lib.draw.sheets import draw_level
from arkitect.lib.units import fmt, inches, inches32
from src.stairs import EXT_STAIR
from arkitect.lib.model.water import _mirror
from src import envelope, levels
from src.building2 import B2U, B2_U5_KITCHEN_WIN, F_B2, KITCHEN_WD, LIVING_WD, U2_SOFFIT_DROP, U2_SOFFIT_ROOMS, stack_bay_rect
from arkitect.lib.model.mirror import mwins
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from src.building2 import (B2_W, PLAN_B2, U5_FLIGHT_X0, U5_LAND_D, U5_LAND_LEN, U5_LAND_X0,
                           U5_LAND_X1, U5_STOOP_X0, U5_TREADS, Y_BEAR, b2_level,
                           check_u5_stair_clear)
from src.schedules import door_tags
from src.sheets.common import draw_door_tags, draw_landings, stoop_lines
from src.sheets.a101 import draw_north
from src.foundation import B2 as B2_FOUNDATION
from arkitect.lib.draw.kit import Q, X0, X1, Y1, _fits, c


def draw_u5_stair(p,W,above=False,landing_label=True):
    """Unit 3's exterior stair, along Building 2's courtyard face.

    The same stair as 300's Unit 3's turned through ninety degrees: travel runs in x, so the
    treads are vertical lines and the projection is in -y. 15 risers at 8" from a 6"
    stoop to Level 2, 14 treads at 9-1/4", a 7'-0" x 3'-6" top landing at the door the
    two flats share, and a 3'-6" square stoop. Dashed on Level 1, solid on Level 2.
    """
    LAY("A-FLOR-STRS")
    cc=p.c
    y0,y1 = -U5_LAND_D, 0.0                 # outer face of the stair, then the wall
    cc.saveState()
    cc.setStrokeColor(GREY if above else black); cc.setLineWidth(0.75)
    if above: cc.setDash(4,2)
    for a,b in ((U5_LAND_X0,U5_LAND_X1),(U5_FLIGHT_X0,U5_LAND_X0)):
        cc.rect(p.X(a),p.Y(y1),(b-a)*p.sc,(y1-y0)*p.sc,fill=0,stroke=1)
    for i in range(1,U5_TREADS):
        xx=U5_LAND_X0-(U5_LAND_X0-U5_FLIGHT_X0)*i/U5_TREADS
        cc.line(p.X(xx),p.Y(y0),p.X(xx),p.Y(y1))
    # Outer guard runs the length of landing and flight; the inner handrail only beside
    # the flight, where there is no wall to carry it. The landing's far end is closed.
    cc.setLineWidth(1.25)
    cc.line(p.X(U5_FLIGHT_X0),p.Y(y0+0.12),p.X(U5_LAND_X1),p.Y(y0+0.12))
    cc.line(p.X(U5_FLIGHT_X0),p.Y(y1-0.12),p.X(U5_LAND_X0),p.Y(y1-0.12))
    cc.line(p.X(U5_LAND_X1),p.Y(y0),p.X(U5_LAND_X1),p.Y(y1))
    if above: cc.setDash()
    # Six-inch concrete stoop, hatched to tell the poured pad from the steel above it.
    cc.setStrokeColor(black); cc.setLineWidth(0.9)
    cc.rect(p.X(U5_STOOP_X0),p.Y(y1),(U5_FLIGHT_X0-U5_STOOP_X0)*p.sc,(y1-y0)*p.sc,fill=0,stroke=1)
    hatch=0.55; q=U5_STOOP_X0-U5_LAND_D
    while q<U5_FLIGHT_X0:
        xa=max(U5_STOOP_X0,q); xb=min(U5_FLIGHT_X0,q+U5_LAND_D)
        ya=y1-max(0.0,U5_STOOP_X0-q); yb=y1-(xb-q)
        cc.line(p.X(xa),p.Y(ya),p.X(xb),p.Y(yb)); q+=hatch
    # Dashed canopy over the door and the whole top landing.
    cc.setStrokeColor(GREY); cc.setLineWidth(0.65); cc.setDash(3,2)
    cc.rect(p.X(U5_LAND_X0-0.5),p.Y(y1+0.5),(U5_LAND_LEN+1.0)*p.sc,(U5_LAND_D+1.0)*p.sc,fill=0,stroke=1)
    cc.setDash(); cc.setFillColor(black); cc.setFont("Helvetica-Bold",4.8)
    cc.drawCentredString(p.X((U5_LAND_X0+U5_LAND_X1)/2.0),p.Y(y0-0.75),"CANOPY ABOVE")
    # Direction arrow: from grade on Level 1 it points uphill, from the stoop toward the
    # Unit 3 landing; on Level 2 it is DN, from the landing toward the stoop.
    ay=p.Y((y0+y1)/2.0); xa=p.X(U5_FLIGHT_X0+0.4); xb=p.X(U5_LAND_X0-0.4)
    if not above: xa, xb = xb, xa
    back=5 if xb > xa else -5
    cc.setStrokeColor(black); cc.setLineWidth(1.1); cc.line(xa,ay,xb,ay)
    cc.line(xb,ay,xb-back,ay-3.2); cc.line(xb,ay,xb-back,ay+3.2)
    cc.setFont("Helvetica-Bold",5.8)
    if not above: cc.drawCentredString(p.X((U5_FLIGHT_X0+U5_LAND_X0)/2.0),ay+4,"DN")
    if landing_label:                       # A-102's Level 1 names Unit 2's landing pad there instead
        cc.setFont("Helvetica",5.0)
        cc.drawCentredString(p.X((U5_LAND_X0+U5_LAND_X1)/2.0),p.Y((y0+y1)/2.0)-8,
                             "%s x %s TOP LANDING"%(fmt(U5_LAND_LEN),fmt(U5_LAND_D)))
    cc.setFont("Helvetica",4.6)
    for i,t in enumerate(stoop_lines()):            # A-202 prints the same two lines
        cc.drawCentredString(p.X((U5_STOOP_X0+U5_FLIGHT_X0)/2.0),p.Y(y0-0.75)+6.0-6.0*i,t)
    cc.restoreState()



# The left margin of each plan, in plan feet off the wall: the overall dimension chain stands
# at about -1.5, so the bay's own string goes inboard of it and its callout between the two.
BAY_DIM_X, BAY_TAG_X, BAY_TAG = -0.35, -0.95, 4.6
BAY_TAG_OFF = 0.45          # down off the bay's middle, clear of the chain's extension lines
NOTE_PAD = 0.3              # inches left at the frame; the note block runs X0 to X1


def draw_stack_bay(p, W):
    """The one bay of the north wall A-601 frames 2x8, so stack F's fittings fit: drawn in
       plan on BOTH levels, because it stands in the mechanical / laundry room of each unit.

       Until now the plans showed that wall flat while the section deepened it, which is the
       same class of fault the section was drawn to close. Every figure is the model's
       (`building2.STACK_BAY_RECT`, from `envelope.stack_bay_*`), so the plan cannot say one
       projection and the detail another.
    """
    bx, by, bw, bh = _mirror(stack_bay_rect(), W)[:4]
    cc = p.c; cc.saveState()
    LAY("A-WALL")
    cc.setFillColor(POCHE); cc.setStrokeColor(black); cc.setLineWidth(0.9)
    cc.rect(p.X(bx), p.Y(by+bh), bw*p.sc, bh*p.sc, fill=1, stroke=1)   # face and both returns
    # Both figures go in the left margin: the mechanical / laundry room has the washer, the
    # panel and two working spaces in it and no room for a string, and 1-3/4" is 1/25 inch on
    # this sheet — too small to tick, so the projection is called out rather than strung.
    p.dim(by, by+bh, "v", BAY_DIM_X, sd=1)
    LAY("A-ANNO-TEXT")
    cc.setFillColor(black); cc.setLineWidth(0.5)
    cc.setFont("Helvetica-Bold", BAY_TAG)
    cc.saveState(); cc.translate(p.X(BAY_TAG_X), p.Y(by+bh/2.0+BAY_TAG_OFF)); cc.rotate(90)
    cc.drawCentredString(0, 0, "%s BAY, PROJECTS %s — A-601"
                               % (envelope.STACK_BAY_STUD,
                                  inches(envelope.stack_bay_projection())))
    cc.restoreState()
    cc.restoreState()


def u3_stair_line():
    """The Unit 3 exterior stair in one line, from the stair model: A-102's note under the
       plans, as A-101 prints its own stair. A-603 builds it."""
    s = EXT_STAIR
    return ("UNIT 3 EXTERIOR STAIR: %dR @ %s / %dT @ %s  \u00b7  %s WIDE  \u00b7  RUN %s  \u00b7  "
            "TOP LANDING %s x %s  \u00b7  RCO 311.7; A-603."
            % (s.risers, inches32(s.riser), s.treads, inches(s.tread), fmt(s.width), fmt(s.run),
               fmt(U5_LAND_LEN), fmt(U5_LAND_D)))


CLOSET_TAG_DROP = 12.0     # page points: the D-5 oval under the closet's own name


def _closet_tag_nudge(p):
    """Each bedroom closet here opens along its whole side wall, so the room's string for
       that opening runs down the doors' line, just outside them, and the D-5 oval printed
       on its figure. The oval goes inside the closet it marks instead, under the closet's
       name, clear of the string."""
    closets = [r for r in B2U if str(r[4]).startswith("CL.")]

    def nudge(tag, X, Y):
        if tag[2] != "D-5":
            return X, Y
        x, y = tag[:2]
        cl = min(closets, key=lambda r: abs(r[0]+r[2]/2.0-x)+abs(r[1]+r[3]/2.0-y))
        cx, cy, cw, ch = _mirror(PLAN_B2.rect(cl), B2_W)[:4]
        return p.X(cx+cw/2.0), p.Y(cy+ch/2.0) - CLOSET_TAG_DROP
    return nudge


# Level 1's W3 bubble stands on the kitchen side of the bearing wall, its edge at the wall's
# face: on the wall's centerline it sat on the bath's width string under it. Plan feet; the
# bubble is 9 pt across its radius, 1/2 ft at this scale.
W3_TAG_OFF = 0.55


def _sink_window(w):
    """The kitchen window in the side wall behind the sink: the plan's mark for a side-wall
       window stands inside the room, which here is across the sink bowl."""
    sx, sy, sw, sh = next(f for f in F_B2 if f[4] == 'sink')[:4]
    return w[3] == 'v' and abs(w[0]-(sx+sw)) < 1e-6 and w[1] < sy+sh and sy < w[1]+w[2]


def _mark_moved(w):
    """The windows A-102 marks itself: the sink's, and Unit 3's courtyard kitchen window,
       whose mark the plan sets outside the wall, on the treads of the stair."""
    return w == B2_U5_KITCHEN_WIN or _sink_window(w)


def draw_moved_windows(p, wins):
    """Each of `wins` (model feet) as the plan draws a window, its mark set where it reads:
       a courtyard window's inside the room, on the counter under it; a side wall's outside
       the building, clear of the sink."""
    for w in mwins([PLAN_B2.span(w) for w in wins], B2_W):
        x, y, ln, o, mark = w
        p.window(x, y, ln, o, "")
        t = (y if y < p.D/2 else p.D-y) if o == 'h' else (x if x < p.W/2 else p.W-x)
        T = t*p.sc
        LAY("A-GLAZ"); c.setFillColor(black); c.setFont("Helvetica", 5.2)
        assert (o == 'h' and y < p.D/2) or (o == 'v' and x < p.W/2), "A-102: W-%s is on a wall its mark was not placed for" % mark
        if o == 'h':
            c.drawCentredString(p.X(x+ln/2.0), p.Y(t/2.0)-T/2.0-3.0-5.2*0.72, "W-"+mark)
        else:
            c.drawRightString(p.X(t/2.0)-T/2.0-2.0, p.Y(y+ln/2.0), "W-"+mark)


def _sized(label):
    """An open-area label with its size under the name, as every room on the plan has:
       the living and the kitchen / dining halves of the one open room, from building2."""
    x, y, name, dm, area = label
    wd = {"LIVING": LIVING_WD, "KITCHEN / DINING": KITCHEN_WD}.get(name)
    if not wd:
        return label
    # a line taller than the plan's name-and-area pair, so it stands higher, clear of the unit's box
    return (x, y-OPEN_LABEL_RISE, name, "%s x %s" % (fmt(wd[0]), fmt(wd[1])), area)


OPEN_LABEL_RISE = 0.7      # plan feet


HATCH_TYPE = 4.6       # pt: the attic hatch's label, the size of the landings' and the door marks'
HALL_LABEL_CLEAR = 0.95   # plan feet from the hatch's near edge to the label's center: its name's cap line is 10 pt over it


def _hall_below_hatch(room):
    """Unit 3's hall with its label set below the attic hatch S-103 places, handed back as
       the offset a room label takes."""
    from src.roof import B2_ROOF
    (h,) = B2_ROOF.hatches
    _x, y, _w, hh = PLAN_B2.rect(room)[:4]
    return room[:5]+((0.0, h.page[3]+HALL_LABEL_CLEAR-(y+hh/2.0)),)+room[6:]


def sheet_a102():
    sh=Sheet(c,"A-102","Building 2 — floor plans","1/4\" = 1'-0\""); sh.frame()
    # The Unit 3 stair now stands 3'-6" off the courtyard face, so the overall dimension
    # and the context note above it move out beyond it rather than through it.
    check_u5_stair_clear()

    for k,(no,ttl,oxx) in enumerate([("L1","LEVEL 1 — UNIT 2",X0+1.9*inch),("L2","LEVEL 2 — UNIT 3",X0+11.3*inch)]):
        oy=Y1-28*Q-4.30*inch
        lv=b2_level(k+1, tags=[(4.0, Y_BEAR-W3_TAG_OFF, "W3")] if k == 0 else None)
        lv.openareas = [(pts, [_sized(l) for l in labs]) for pts, labs in lv.openareas]
        if k == 1:                      # Unit 3's hall label goes below the attic hatch, not through it
            lv.rooms = [_hall_below_hatch(r) if r[4] == "HALL" else r for r in lv.rooms]
        moved = [w for w in lv.wins if _mark_moved(w)]
        lv.wins = [w for w in lv.wins if not _mark_moved(w)]
        lv.over_plan=lambda pp,above=(k==0),moved=moved: (draw_moved_windows(pp, moved),
                                                         draw_u5_stair(pp,B2_W,above=above,landing_label=not above))
        p=draw_level(c,lv,oxx,oy)
        draw_door_tags(p, PLAN_B2, B2_W, door_tags(2, k+1), nudge=_closet_tag_nudge(p))   # the marks A-602 schedules
        draw_stack_bay(p, B2_W)                              # the same bay on both levels: stack F rises through both
        if k == 0:                                           # Unit 2's landing at D-1, under the stair's top landing
            draw_landings(p, [pd for pd in B2_FOUNDATION.pads if pd[4] == "UNIT 2 LANDING"], "A-102")
        if k == 0:                                           # Unit 2's bath: the soffit under the rated ceiling
            from arkitect.lib.model.water import _mirror
            for r in B2U:
                if r[4] in U2_SOFFIT_ROOMS:
                    x, y, w, h = _mirror(PLAN_B2.rect(r), B2_W)[:4]
                    off = r[5] if len(r) > 5 else (0.0, 0.0)
                    # two short lines under the room's area, where the plan sets its label,
                    # above the fixtures: the note under the plans carries the rest
                    cx, cy = p.X(x+w/2.0), p.Y(y+h/2.0+off[1])
                    LAY("A-ANNO-TEXT"); c.setFillColor(black); c.setFont("Helvetica", 4.6)
                    for i, t in enumerate(("SOFFIT", "CLG %s" % fmt(levels.F1_CEILING-U2_SOFFIT_DROP-levels.FF1))):
                        c.drawCentredString(cx, cy-17.5-5.0*i, t)
        if k == 1:
            from src.roof import B2_ROOF            # Unit 3's attic hatch, as S-103 places it, RCO 807.1
            from src.sheets.common import draw_attic_hatch
            for h in B2_ROOF.hatches: draw_attic_hatch(p, h, size=HATCH_TYPE, split=True)
        p.note(B2_W/2.0,PLAN_B2.y(-6.6),"FACES BUILDING 1  ·  OAK AVENUE BEYOND",6.6)
        p.note(B2_W/2.0,PLAN_B2.y(35.3),("UNIT 3 ENTRY: EXTERIOR STAIR ON THE COURTYARD FACE" if k==1
                                   else "ENTRY AT GRADE — UNIT 3'S STAIR AND LANDING PASS OVERHEAD, SHOWN DASHED")
                       +"   ·   PARKING AND ALLEY TO THE REAR",6.0)
        p.note(B2_W/2.0,PLAN_B2.y(36.4),"5'-0\" SIDE YARD EACH SIDE",6.0)
        # in FINAL SHEET coordinates: in the living space, over the sofa that is not drawn
        p.unitbox(B2_W-PLAN_B2.x(8.0,8.0),PLAN_B2.y(8.0),"UNIT %d"%(2+k),"2 BR / 1 BA",1.75,0.42)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12); c.drawString(oxx,oy-1.50*inch,ttl)
        c.setFont("Helvetica",9); c.drawString(oxx,oy-1.68*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(oxx,oy-1.22*inch,oxx+2.6*inch,oy-1.22*inch)
        draw_north(oxx+3.4*inch, oy-1.45*inch)                    # beside the plan's title, as A-101
    c.setFont("Helvetica",8.4); c.setFillColor(black)
    for i,t in enumerate([
        "UNITS 2 AND 3 STACK: THE BEARING WALL, THE WET WALLS AND THE ENTRY DOORS ALIGN.",
        u3_stair_line(),
        "UNIT 3'S KITCHEN TAKES A WINDOW THAT UNIT 2 DOES NOT.",
        "UNIT 2'S BATH CEILING IS A SOFFIT AT %s, %s BELOW THE RATED F1 CEILING, WHICH IS WHOLE OVER IT: THE FAN, ITS DUCT AND THE LIGHT HANG IN THE SOFFIT. A-601 F1 ITEM C."
        % (fmt(levels.F1_CEILING-U2_SOFFIT_DROP-levels.FF1), inches(U2_SOFFIT_DROP)),
        "THE %s BAY BEHIND THE WASHER IS FRAMED PLATE TO PLATE ON BOTH LEVELS AND PROJECTS %s INTO THE ROOM. CARRY THE ROOM'S GYPSUM ACROSS ITS FACE AND RETURN IT TO THE WALL AT EACH END. A-601."
        % (envelope.STACK_BAY_STUD, inches(envelope.stack_bay_projection()))]):
        # Nothing was holding these to a width; the third one is already 11 inches long.
        _fits(t, "Helvetica", 8.4, X1-NOTE_PAD*inch-X0, "A-102 note %d" % (i+1))
        c.drawString(X0,oy-(2.15+0.16*i)*inch,t)
    c.showPage()


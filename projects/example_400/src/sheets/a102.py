"""A-102 — Building 2's floor plans: Units 2 and 3, and the Unit 3 exterior stair.

Bound as A-102, after the house's A-101 (the designer, 2026-09-18); on 300, where this code comes
from, it was A-103. Moved out of src/sheets/plans.py (300's plan module) so that drawing
Building 2 no longer loads 300's Building 1 plan code. The two functions are unchanged.
"""
from arkitect.lib.draw.page import GREY, LAY, POCHE, Sheet
from arkitect.lib.draw.sheets import draw_level
from arkitect.lib.units import fmt, inches
from arkitect.lib.model.water import _mirror
from src import envelope, levels
from src.building2 import B2U, U2_SOFFIT_DROP, U2_SOFFIT_ROOMS, stack_bay_rect
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from arkitect.lib.model.regrid import PARTITION
from src.building2 import (B2_W, PLAN_B2, U5_FLIGHT_X0, U5_LAND_D, U5_LAND_LEN, U5_LAND_X0,
                           U5_LAND_X1, U5_STOOP_X0, U5_TREADS, Y_BEAR, b2_level,
                           check_u5_stair_clear)
from src.schedules import door_tags
from src.sheets.common import draw_door_tags
from arkitect.lib.draw.kit import Q, X0, X1, Y1, _fits, c


def draw_u5_stair(p,W,above=False):
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
    # Direction arrow points uphill, from the stoop toward the Unit 3 landing.
    ay=p.Y((y0+y1)/2.0); xa=p.X(U5_FLIGHT_X0+0.4); xb=p.X(U5_LAND_X0-0.4)
    cc.setStrokeColor(black); cc.setLineWidth(1.1); cc.line(xa,ay,xb,ay)
    cc.line(xb,ay,xb-5,ay-3.2); cc.line(xb,ay,xb-5,ay+3.2)
    cc.setFont("Helvetica-Bold",5.8)
    if not above: cc.drawCentredString(p.X((U5_FLIGHT_X0+U5_LAND_X0)/2.0),ay+4,"DN")
    cc.setFont("Helvetica",5.0)
    cc.drawCentredString(p.X((U5_LAND_X0+U5_LAND_X1)/2.0),p.Y((y0+y1)/2.0)-8,
                         "%s x %s TOP LANDING"%(fmt(U5_LAND_LEN),fmt(U5_LAND_D)))
    cc.setFont("Helvetica",4.6)
    cc.drawCentredString(p.X((U5_STOOP_X0+U5_FLIGHT_X0)/2.0),p.Y(y0-0.75),
                         "6\" CONCRETE STOOP · ONE STEP DOWN")
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


def sheet_a102():
    sh=Sheet(c,"A-102","Building 2 — floor plans","1/4\" = 1'-0\""); sh.frame()
    # The Unit 3 stair now stands 3'-6" off the courtyard face, so the overall dimension
    # and the context note above it move out beyond it rather than through it.
    check_u5_stair_clear()

    for k,(no,ttl,oxx) in enumerate([("L1","LEVEL 1 — UNIT 2",X0+1.9*inch),("L2","LEVEL 2 — UNIT 3",X0+11.3*inch)]):
        oy=Y1-28*Q-4.30*inch
        lv=b2_level(k+1, tags=[(4.0, Y_BEAR+PARTITION/2.0, "W3")] if k == 0 else None)
        lv.over_plan=lambda pp,above=(k==0): draw_u5_stair(pp,B2_W,above=above)
        p=draw_level(c,lv,oxx,oy)
        draw_door_tags(p, PLAN_B2, B2_W, door_tags(2, k+1))                        # the marks A-602 schedules
        draw_stack_bay(p, B2_W)                              # the same bay on both levels: stack F rises through both
        if k == 0:                                           # Unit 2's bath: the soffit under the rated ceiling
            from arkitect.lib.model.water import _mirror
            for r in B2U:
                if r[4] in U2_SOFFIT_ROOMS:
                    x, y, w, h = _mirror(PLAN_B2.rect(r), B2_W)[:4]
                    LAY("A-ANNO-TEXT"); c.setFillColor(black); c.setFont("Helvetica", 4.2)
                    c.drawCentredString(p.X(x+w/2.0), p.Y(y+h)+3.0, "SOFFIT, CLG %s — A-601 F1 ITEM C" % fmt(levels.F1_CEILING-U2_SOFFIT_DROP-levels.FF1))
        if k == 1:
            from src.roof import B2_ROOF            # Unit 3's attic hatch, as S-103 places it, RCO 807.1
            from src.sheets.common import draw_attic_hatch
            for h in B2_ROOF.hatches: draw_attic_hatch(p, h)
        p.note(B2_W/2.0,PLAN_B2.y(-6.6),"FACES BUILDING 1  ·  OAK AVENUE BEYOND",6.6)
        p.note(B2_W/2.0,PLAN_B2.y(35.3),("ENTRY FROM UNIT 3'S OWN EXTERIOR STAIR ON THIS FACE — PRIVATE, NOT SHARED" if k==1
                                   else "ENTRY AT GRADE — UNIT 3'S STAIR AND LANDING PASS OVERHEAD, SHOWN DASHED")
                       +"   ·   PARKING AND ALLEY TO THE REAR",6.0)
        p.note(B2_W/2.0,PLAN_B2.y(36.4),"5'-0\" SIDE YARD EACH SIDE",6.0)
        # in FINAL SHEET coordinates: in the living space, over the sofa that is not drawn
        p.unitbox(B2_W-PLAN_B2.x(8.0,8.0),PLAN_B2.y(8.0),"UNIT %d"%(2+k),"2 BR / 1 BA",1.75,0.42)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12); c.drawString(oxx,oy-1.50*inch,ttl)
        c.setFont("Helvetica",9); c.drawString(oxx,oy-1.68*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(oxx,oy-1.22*inch,oxx+2.6*inch,oy-1.22*inch)
    c.setFont("Helvetica",8.4); c.setFillColor(black)
    for i,t in enumerate([
        "UNITS 2 AND 3 STACK: THE BEARING WALL, THE WET WALLS AND THE ENTRY DOORS ALIGN.",
        "UNIT 3'S KITCHEN TAKES A WINDOW THAT UNIT 2 DOES NOT.",
        "UNIT 2'S BATH CEILING IS A SOFFIT AT %s, %s BELOW THE RATED F1 CEILING, WHICH IS WHOLE OVER IT: THE FAN, ITS DUCT AND THE LIGHT HANG IN THE SOFFIT. A-601 F1 ITEM C."
        % (fmt(levels.F1_CEILING-U2_SOFFIT_DROP-levels.FF1), inches(U2_SOFFIT_DROP)),
        "THE %s BAY BEHIND THE WASHER IS FRAMED PLATE TO PLATE ON BOTH LEVELS AND PROJECTS %s INTO THE ROOM. CARRY THE ROOM'S GYPSUM ACROSS ITS FACE AND RETURN IT TO THE WALL AT EACH END. A-601."
        % (envelope.STACK_BAY_STUD, inches(envelope.stack_bay_projection()))]):
        # Nothing was holding these to a width; the third one is already 11 inches long.
        _fits(t, "Helvetica", 8.4, X1-NOTE_PAD*inch-X0, "A-102 note %d" % (i+1))
        c.drawString(X0,oy-(2.15+0.16*i)*inch,t)
    c.showPage()


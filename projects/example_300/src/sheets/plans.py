"""A-101, A-102 and A-103 — the floor plans, and the stairs drawn on them.

   The exterior stairs are here rather than with the model because they are DRAWN in
   true feet, outside the regrid: the stud-grid map stretches that band of the plan
   by 8 percent, which drew a 3'-6" landing 3'-7-7/8" long."""
from arkitect.lib.draw.page import GREY, LAY, POCHE, Sheet
from arkitect.lib.draw.sheets import draw_level, plan_sheet
from arkitect.lib.units import fmt
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.building1 import F_U23, LIVE_WALL_X, LST_ARROW, LST_LONG, LST_SHORT, OA_U23, PLAN_L1, PLAN_L2, U23, U2_ENTRY, U3_ENTRY, U3_FLIGHT_HI, U3_LAND_D, U3_LAND_HI, U3_LAND_LEN, U3_LAND_LO, U3_STAIR_RATED, U3_STAIR_W, U3_STOOP_HI, U3_TREADS, _b1_level, b1_chains
from src.building2 import B2_W, PLAN_B2, U5_FLIGHT_X0, U5_LAND_D, U5_LAND_LEN, U5_LAND_X0, U5_LAND_X1, U5_STOOP_X0, U5_TREADS, Y_BEAR, b2_level, check_u5_stair_clear
from arkitect.lib.model.regrid import PARTITION
from src.mirror import LIVE_SIDE, rnotes, rtags
import math
from src.building1 import (LB, B0, B1, D_STUD, EXT, FZ, NOSING, NS_FACES, NT, P, R0, SX, TREAD, W_STUD,
                           YB, YT, X_OFFSET, Y_OFFSET, site_x, site_y, windows,
                           MX0, MX1, WET, WW0, WW1, BX0, BX1, BR_X, BY1, PK0, KX, DEM0, DEM1, NX, CS,
                           U1_ATTIC, U1_ATTIC_LABEL,
                           U1_DR_DUCT, U1_DR_TERM)
from reportlab.lib.colors import Color
from arkitect.lib.units import IN
from arkitect.lib.units import inches
from src import levels
from src.grading import STOOP_STEP, STOOP_TOP
from src.sheets.common import draw_attic_hatch
from arkitect.lib.draw.kit import Q, X0, Y1, c
from src.roof import HATCHES


# ============================= helpers =============================
def draw_lstair(p,W,label):
    """Quarter-turn stair for Unit 1, drawn in mirrored sheet coordinates.
       The arrowhead always marks the direction of ASCENT, on both plans."""
    LAY("A-FLOR-STRS")
    cc=p.c; cc.setStrokeColor(black); cc.setLineWidth(0.55)
    x,y,w,d,n = PLAN_L1.rect(LST_LONG)[:4]+(LST_LONG[4],)
    for i in range(n+1):
        yy=y+i*(d/n); cc.line(p.X(W-x-w),p.Y(yy),p.X(W-x),p.Y(yy))
    x,y,w,d,n = PLAN_L1.rect(LST_SHORT)[:4]+(LST_SHORT[4],)
    for i in range(n+1):
        xx=x+i*(w/n); cc.line(p.X(W-xx),p.Y(y),p.X(W-xx),p.Y(y+d))
    pp=[(p.X(W-PLAN_L1.x(a,bb)),p.Y(PLAN_L1.y(bb))) for (a,bb) in LST_ARROW]
    cc.setLineWidth(1.2); cc.setLineCap(1)
    for i in range(len(pp)-1): cc.line(pp[i][0],pp[i][1],pp[i+1][0],pp[i+1][1])
    (ax,ay),(bx,by)=pp[-2],pp[-1]; an=math.atan2(by-ay,bx-ax)
    for dd in (0.40,-0.40): cc.line(bx,by,bx-8*math.cos(an+dd),by-8*math.sin(an+dd))
    cc.setLineCap(0); cc.setFont("Helvetica-Bold",6.6)
    # the label lands on open floor on Level 1 but in the poche between the mech closet
    # and Bath 2 on Level 2, where black on black is invisible. Mask behind it.
    lx,ly = pp[0][0]-15, pp[0][1]-3
    lw = pdfmetrics.stringWidth(label,"Helvetica-Bold",6.6)
    cc.setFillColor(white); cc.rect(lx-lw/2-1.5,ly-1.5,lw+3,6.6+1.5,fill=1,stroke=0)
    cc.setFillColor(black); cc.drawCentredString(lx,ly,label)


def u3_stair_x(W):
    """(wall face, outer face) of the stair in FINAL SHEET coordinates. The mirror puts
       it on the LIVE_SIDE of the building, which is the sheet's left when it is on."""
    return (0.0,-U3_STAIR_W)


def draw_u3_stair(p,W,P,above=False,annotate=True):
    """Straight exterior egress stair down the LIVE_SIDE face of Building 1.

    Overall width is 3'-6" with rails mounted to preserve the RCO 311.7.1 clear
    width. The 10'-0" rise from the 6" concrete stoop to Level 2 takes 15 equal
    8" risers and 14 9-1/4" treads, for a true 10'-9-1/2" run. The top landing runs
    U3_LAND_LEN along the wall and U3_LAND_D out from it; the stoop is 3'-6" square.
    The flight is dashed on Level 1 and solid on Level 2; the stoop remains solid on
    both plans because it is at grade.
    """
    LAY("A-FLOR-STRS")
    cc=p.c
    y0,y1,y2,y3 = U3_LAND_LO,U3_LAND_HI,U3_FLIGHT_HI,U3_STOOP_HI
    xin,xout=u3_stair_x(W); out=1.0 if xout>xin else -1.0
    x0,x1=min(xin,xout),max(xin,xout)
    cc.saveState()
    cc.setStrokeColor(GREY if above else black); cc.setLineWidth(0.75)
    if above: cc.setDash(4,2)
    # Elevated top landing and straight flight.
    for ya,yb in ((y0,y1),(y1,y2)):
        cc.rect(p.X(x0),p.Y(yb),(x1-x0)*p.sc,(yb-ya)*p.sc,fill=0,stroke=1)
    for i in range(1,U3_TREADS):
        yy=y1+(y2-y1)*i/U3_TREADS
        cc.line(p.X(x0),p.Y(yy),p.X(x1),p.Y(yy))
    # Rails/guards on the elevated work: outer guard the length of landing and flight,
    # inner handrail only beside the flight, where the wall is not there to carry it.
    cc.setLineWidth(1.25)
    cc.line(p.X(xout-0.12*out),p.Y(y0),p.X(xout-0.12*out),p.Y(y2))
    cc.line(p.X(xin+0.12*out),p.Y(y1),p.X(xin+0.12*out),p.Y(y2))
    cc.line(p.X(x0),p.Y(y0),p.X(x1),p.Y(y0))
    if above: cc.setDash()
    # Six-inch-high concrete bottom stoop, wholly beyond the rear wall. Diagonal
    # hatching distinguishes the poured pad from the elevated wood stair.
    cc.setStrokeColor(black); cc.setLineWidth(0.9)
    cc.rect(p.X(x0),p.Y(y3),(x1-x0)*p.sc,(y3-y2)*p.sc,fill=0,stroke=1)
    hatch=0.55
    q=y2-hatch
    while q<y3:
        ya=max(y2,q); yb=min(y3,q+U3_STAIR_W)
        xa=x0+max(0.0,y2-q); xb=x0+(yb-q)
        cc.line(p.X(xa),p.Y(ya),p.X(xb),p.Y(yb)); q+=hatch
    # Dashed canopy footprint covers the Unit 3 door and entire top landing.
    cc.setStrokeColor(GREY); cc.setLineWidth(0.65); cc.setDash(3,2)
    can_x0=x0-0.5; can_x1=x1+0.5
    can_y0=y0-0.5; can_y1=y1+0.5
    cc.rect(p.X(can_x0),p.Y(can_y1),(can_x1-can_x0)*p.sc,(can_y1-can_y0)*p.sc,fill=0,stroke=1)
    cc.setDash(); cc.setFillColor(black); cc.setFont("Helvetica-Bold",4.8)
    cc.drawCentredString(p.X((can_x0+can_x1)/2),p.Y(can_y0)-6,"CANOPY ABOVE")
    # Direction arrow points uphill, from grade toward the Unit 3 landing.
    ax=p.X((x0+x1)/2); ya=p.Y(y2-0.4); yb=p.Y(y1+0.4)
    cc.setLineWidth(1.1); cc.line(ax,ya,ax,yb)
    cc.line(ax,yb,ax-3.2,yb-5); cc.line(ax,yb,ax+3.2,yb-5)
    cc.setFillColor(black); cc.setFont("Helvetica-Bold",5.8)
    if not above: cc.drawCentredString(ax,p.Y((y1+y2)/2)-3,"DN")
    # Put the complete elevation note beside the pad; it is too long to remain
    # legible inside a 3'-6" square at this scale.
    # Sit below the rear-wall dimension rows while remaining alongside the pad.
    stoop_cy=p.Y((y2+y3)/2.0)-10
    cc.setFont("Helvetica",5.0)
    # The note goes on whichever side of the stoop is open sheet: away from the stair
    # when it stands at the sheet's right, and back under the plan when it is at the
    # left, where the overall dimension and the unit brackets are.
    side=-1.0
    anchor=x0
    note_x=p.X(anchor)+5*side
    stoop_note=(("BOTTOM LANDING",10.5),
                ("CONCRETE STOOP",3.5),
                ("TOP %s ABOVE FINISHED GRADE"%inches(STOOP_TOP),-3.5),
                ("ONE %s STEP DOWN TO GRADE"%inches(STOOP_STEP),-10.5))
    if annotate:
        cc.setFillColor(black)
        for txt,dy in stoop_note:
            cc.drawRightString(note_x,stoop_cy+dy,txt)
        cc.setLineWidth(0.45); cc.line(note_x-2*side,stoop_cy,p.X(anchor),stoop_cy)
    cc.restoreState()


def draw_u3_landing_label(p,W,P):
    """Draw last so plan masks and annotation backgrounds cannot clip this label."""
    xin,xout=u3_stair_x(W)
    ax=p.X((xin+xout)/2.0)
    land_cy=p.Y((U3_LAND_LO+U3_LAND_HI)/2.0)
    # Plain drawString, not a text object: the DXF recording proxy wraps the three
    # drawString calls and passes beginText straight through to the real canvas, so
    # this label was drawn on the PDF and dropped from the DXF every build. The
    # setTextRenderMode(0) it used to carry was the reportlab default anyway; what
    # actually keeps the label off the plan masks is being drawn last.
    c.saveState(); c.setFillColor(black); c.setFont("Helvetica",5.2)
    for txt,yy in (("%s x %s"%(fmt(U3_LAND_LEN),fmt(U3_LAND_D)),land_cy+3),
                   ("TOP LANDING",land_cy-4)):
        c.drawCentredString(ax,yy,txt)
    c.restoreState()


def draw_u5_stair(p,W,above=False):
    """Unit 5's exterior stair, along Building 2's courtyard face.

    The same stair as Unit 3's turned through ninety degrees: travel runs in x, so the
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
    # Direction arrow points uphill, from the stoop toward the Unit 5 landing.
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


# The three pieces of drawing Building 1 adds to a plan that the library cannot know
# about: Unit 1's plans, and the Unit 3 exterior stair with its landing label.
B1_DRAWING = dict(draw_u3_stair=lambda p,W,plan,above,annotate=True: draw_u3_stair(p,W,plan,above=above,annotate=annotate),
                  draw_u3_landing_label=lambda p,W,plan: draw_u3_landing_label(p,W,plan),
                  draw_unit1=lambda p,level,annotate=True: draw(p,level,annotate))


# ============================= A-101 =============================
def sheet_a101():

    CH_L1=b1_chains([],[],U23,OA_U23,16.0,F_U23,49.25)
    # Unit 2's door under the top landing, jamb to jamb, against the wall. The landing
    # is 3'-6" and the door 3'-0", so the framed wall each side is 3" and has to be
    # readable as a number rather than scaled off.
    _ux=PLAN_L1.x(LIVE_WALL_X,U2_ENTRY[1])
    _ud=PLAN_L1.y(U2_ENTRY[1])
    _ul,_ue=U3_LAND_LO,U3_LAND_HI
    CH_L1_OPENINGS=[([(_ul,_ux),(_ud,_ux),(_ud+U2_ENTRY[2],_ux),(_ue,_ux)],
                     'v',_ux-1.05,-1,0.0,True,None)]
    notes=rnotes([(13,24.30,"W4A / W4B — TWO UL U305 WALLS — 1 HOUR EACH — SEE A-601",5.0,"c",False,True),
           (13,-3.0,"UNIT 1: 15R @ 8\" / 14T @ 9-1/4\" / RUN 10'-9-1/2\" / RISE 10'-0\"",5.4),
           (13,51.2,"UNIT 3 EXTERIOR STAIR AT %s SIDE — %s UNDERSIDE, SEE A-102"
                    %(LIVE_SIDE,"1-HR RATED" if U3_STAIR_RATED else "UNRATED"),6.0),
           (13,52.1,"15R @ 8\"  ·  14T @ 9-1/4\"  ·  RUN 10'-9-1/2\"  ·  3'-6\" OVERALL, 3'-0\" MIN CLEAR",6.0)]
    # what the two boxes in the mechanical closet are, tagged on the symbols themselves
         +[(9.975,46.08,"W/D",5.2,"c"),(1.450,31.45,"DW",5.2)])
    plan_sheet(c,_b1_level(1, notes, CH_L1, CH_L1_OPENINGS,
                         units=[(0,24,"UNIT 1","4 BR / 2 BA  ·  1,248 SF  ·  TWO STORIES"),
                                (24,48,"UNIT 2","2 BR / 1 BA  ·  624 SF  ·  GRADE ENTRY")],
                         tags=rtags([(14.30,38.05,"W3")]), u3stair=True, **B1_DRAWING),
               "A-101","Building 1 — Level 1 Floor Plan","1/4\" = 1'-0\"")
    c.showPage()


# ============================= A-102 =============================
def sheet_a102():
    # all fields, not just the first five: a rect can carry a label offset after its
    # name, and rebuilding it five-wide silently dropped that on this sheet only
    notes=rnotes([(13,24.30,"W4A / W4B — TWO UL U305 WALLS — 1 HOUR EACH — SEE A-601",5.0,"c",False,True),
           # The rear wall is rated for the courtyard, not for what it carries: it stands
           # fsd.OFF_B1 from the RCO 302.1 imaginary line, inside the 5'-0" of Table
           # 302.1(1). Level 1's is W1R already because it supports F1 (note 2); this is
           # the storey where the tag is news, and the rating runs on up through the gable.
           # On the wall's poche and reversed out, the way the W4 tag above it is: a wall
           # tag belongs on its wall, and the band between this wall and its dimension
           # string is 7 points deep. rev is not decoration — off the poche it prints
           # white on white paper, and on it black would be black on black.
           (13,47.78,"REAR WALL — W1R, 1 HOUR, THROUGH THE GABLE — SEE A-601",5.0,"c",False,True),
           (13,-3.0,"UNIT 1: 15R @ 8\" / 14T @ 9-1/4\" / RUN 10'-9-1/2\" / RISE 10'-0\"",5.4),
           (13,51.2,"UNIT 3 PRIVATE EXTERIOR STAIR ALONG %s SIDE, DESCENDING TOWARD REAR YARD"%LIVE_SIDE,6.0),
           (13,52.1,"15R @ 8\"  ·  14T @ 9-1/4\"  ·  RUN 10'-9-1/2\"  ·  3'-6\" OVERALL, 3'-0\" MIN CLEAR",6.0)]
         +[(9.975,46.08,"W/D",5.2,"c"),(1.450,31.45,"DW",5.2)])
    CH_L2=b1_chains([],[],U23,OA_U23,13.0,F_U23)
    # The same string on Level 2: Unit 3's door stacks on Unit 2's and shares the wall
    # and the landing with it.
    _ux=PLAN_L2.x(LIVE_WALL_X,U3_ENTRY[1])
    _ud=PLAN_L2.y(U3_ENTRY[1])
    _ul,_ue=U3_LAND_LO,U3_LAND_HI
    CH_L2_OPENINGS=[([(_ul,_ux),(_ud,_ux),(_ud+U3_ENTRY[2],_ux),(_ue,_ux)],
                     'v',_ux-1.05,-1,0.0,True,None)]
    lv=_b1_level(2, notes, CH_L2, CH_L2_OPENINGS,
                 units=[(0,24,"UNIT 1","4 BR / 2 BA  ·  SLEEPING LEVEL"),
                        (24,48,"UNIT 3","2 BR / 1 BA  ·  624 SF  ·  STAIR ENTRY")],
                 **B1_DRAWING)
    # Unit 3's attic hatch, from the roof model; Unit 1's is drawn with its plan above.
    _over_dims=lv.over_dims
    lv.over_dims=lambda pp: (_over_dims(pp), draw_attic_hatch(pp, HATCHES[1]))
    plan_sheet(c,lv,"A-102","Building 1 — Level 2 Floor Plan","1/4\" = 1'-0\"")
    c.showPage()


# ============================= A-103 BUILDING 2 =============================
def sheet_a103():
    sh=Sheet(c,"A-103","Building 2 — floor plans","1/4\" = 1'-0\""); sh.frame()
    # The Unit 5 stair now stands 3'-6" off the courtyard face, so the overall dimension
    # and the context note above it move out beyond it rather than through it.
    check_u5_stair_clear()

    for k,(no,ttl,oxx) in enumerate([("L1","LEVEL 1 — UNIT 4",X0+1.9*inch),("L2","LEVEL 2 — UNIT 5",X0+11.3*inch)]):
        oy=Y1-28*Q-4.30*inch
        lv=b2_level(k+1, tags=[(6.0, Y_BEAR+PARTITION/2.0, "W3")] if k == 0 else None)
        # Unit 5's attic hatch, from the roof model, on the Level 2 plan only
        lv.over_plan=lambda pp,above=(k==0),hatch=(HATCHES[2] if k==1 else None): (
            draw_u5_stair(pp,B2_W,above=above), hatch and draw_attic_hatch(pp,hatch))
        p=draw_level(c,lv,oxx,oy)
        p.note(B2_W/2.0,PLAN_B2.y(30.0),"STACK D IN THE BATH'S ADJACENT-PARCEL WALL, STACK F IN THE MECHANICAL CLOSET'S SAGE WALL — SEE P-601",6.0)
        p.note(B2_W/2.0,PLAN_B2.y(-6.6),"FACES BUILDING 1  ·  12'-0\" SEPARATION  ·  S ELM AVENUE BEYOND",6.6)
        p.note(B2_W/2.0,PLAN_B2.y(30.9),("ENTRY FROM UNIT 5'S OWN EXTERIOR STAIR ON THIS FACE — PRIVATE, NOT SHARED" if k==1
                                   else "ENTRY AT GRADE — UNIT 5'S STAIR AND LANDING PASS OVERHEAD, SHOWN DASHED")
                       +"   ·   PARKING AND ALLEY TO THE REAR",6.0)
        p.note(B2_W/2.0,PLAN_B2.y(31.8),"SAGE AVENUE ON THE LEFT (8'-0\" SIDE STREET BUILDING LINE)  ·  ADJACENT PARCEL ON THE RIGHT (6'-0\" SIDE YARD)",6.0)
        # in FINAL SHEET coordinates: in the living space, over the sofa that is not drawn
        p.unitbox(B2_W-PLAN_B2.x(6.5,12.3),PLAN_B2.y(12.3),"UNIT %d"%(4+k),"2 BR / 1 BA  ·  728 SF",1.75,0.42)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12); c.drawString(oxx,oy-1.50*inch,ttl)
        c.setFont("Helvetica",9); c.drawString(oxx,oy-1.68*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(oxx,oy-1.22*inch,oxx+2.6*inch,oy-1.22*inch)
    c.setFont("Helvetica",8.4); c.setFillColor(black)
    for i,t in enumerate([
        "UNITS 4 AND 5 STACK: STACKS D AND F, THE BEARING WALL AND THE ENTRY DOORS ALIGN. F1 FRAMING: S-102. BEARING STRIP: S-101. STACKS: P-601.",
        "UNIT 5 EXTERIOR STAIR: A-001 NOTE 13b, A-604. UNIT 5'S KITCHEN TAKES A W-C THAT UNIT 4 DOES NOT."]):
        c.drawString(X0,oy-(2.15+0.16*i)*inch,t)
    c.showPage()


# ---------------- Unit 1's plans ----------------
# Unit 1 appears on A-101 and A-102 like Units 2 and 3, but it is drawn by a
# different mechanism: a supplied study that paints its own shapes straight onto the
# canvas instead of going through PlanDraw and the regrid. That difference is real
# and is why this code looks unlike the rest of the file — it is not a reason for a
# module named after one of five dwellings.

# ---------------- the study's three shapes, without matplotlib ----------------
# The supplied study built its plans as matplotlib patches, and nothing ever rendered
# them with matplotlib: PlanArtist.flush() reads their geometry back and draws it on the
# reportlab canvas. So the library was a large third-party dependency serving as three
# structs and a colour lookup, imported at module scope with a backend selected for a
# renderer never used.
#
# These are those structs, with matplotlib's accessor names so flush() reads them
# unchanged — and matplotlib's values, INCLUDING the defaults it supplied silently. Two
# of those matter and neither is obvious: a patch given no linewidth is 1.0 wide, and an
# Arc's face colour defaults to matplotlib's C0 blue at zero alpha, which the canvas
# faithfully records with setFillColor before deciding not to fill with it. Substituting
# black there is invisible on the sheet and changes the drawing calls.
#
# "poche" is not one of matplotlib's names. It is here because a WALL is not black: it
# is the poche the library fills a footprint with and punches rooms out of, and the two
# have to be the same colour or the set has two wall greys. They differ by 0.15 on the
# architectural sheets, which nobody can see, and by the width of GREY to LGREY once a
# trade sheet draws the plan through GreyPen, which is how Unit 1 came to print 60%
# darker than Units 2 to 5 on eight sheets. Taken from POCHE rather than typed, so a
# change to the set's poche carries here and cannot drift.
_RGBA = {"black": (0.0, 0.0, 0.0, 1.0),
         "white": (1.0, 1.0, 1.0, 1.0),
         "poche": (POCHE.red, POCHE.green, POCHE.blue, 1.0),
         "none":  (0.0, 0.0, 0.0, 0.0)}


_C0_UNFILLED = (0.12156862745098039, 0.4666666666666667, 0.7058823529411765, 0)


def to_rgba(v):
    return _RGBA[v] if isinstance(v, str) else tuple(v)


class _Patch:
    """A shape waiting to be drawn. The defaults are the ones matplotlib applied to the
       calls in this file: an Arc passes neither fc nor ec, everything else passes both."""
    def __init__(s, fc=_C0_UNFILLED, ec="black", lw=1.0, ls="solid", zorder=1, **inert):
        # `inert` is styling matplotlib accepted and flush() never read — joinstyle on
        # the bed outline is the only one. It never reached the canvas; taking it here
        # keeps the call site honest about that rather than deleting it silently.
        s._fc, s._ec = to_rgba(fc), to_rgba(ec)
        s._lw, s._ls, s._z = lw, ls, zorder
    def get_facecolor(s):  return s._fc
    def get_edgecolor(s):  return s._ec
    def get_linewidth(s):  return s._lw
    def get_linestyle(s):  return s._ls
    def get_zorder(s):     return s._z


class Rectangle(_Patch):
    def __init__(s, xy, w, h, **kw):
        _Patch.__init__(s, **kw); s._xy = list(xy); s._w = w; s._h = h
    def get_xy(s):     return tuple(s._xy)
    def get_x(s):      return s._xy[0]
    def get_y(s):      return s._xy[1]
    def get_width(s):  return s._w
    def get_height(s): return s._h
    def set_x(s, x):   s._xy[0] = x


class Ellipse(_Patch):
    def __init__(s, center, w, h, **kw):
        _Patch.__init__(s, **kw); s.center = center; s.width = w; s.height = h


class Arc(Ellipse):
    def __init__(s, center, w, h, angle=0.0, theta1=0.0, theta2=360.0, **kw):
        Ellipse.__init__(s, center, w, h, **kw)
        s.angle = angle; s.theta1 = theta1; s.theta2 = theta2




# ---------------------------------------------------------------- helpers
def fi(v):
    """Feet and inches the way Unit 1's supplied study wrote them: the fraction spaced
       off the whole inches (10'-1 3/4"), and no leading 0'- under a foot (3-1/2").

       It used to be thirteen lines of its own arithmetic. It is the library's two
       formatters with sep=" ", which is the only thing that ever differed. The study
       also dropped the whole-inches zero under ONE INCH (1/8" rather than 0 1/8");
       nothing in this project draws a label that small — the smallest of the 62 calls a
       build makes is 3-1/2" — so that branch went with the rest."""
    return (fmt if abs(v) >= 1.0 else inches)(v, sep=" ")


def wall(ax, x0, y0, x1, y1, fill="poche"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fill, ec="black", lw=0.3, zorder=3))


def rect(ax, x0, y0, x1, y1, lw=0.6, ls="-", fc="none", ec="black", z=4):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))


def txt(ax, x, y, s, size=7, ha="center", va="center", rot=0, weight="normal", z=6):
    ax.text(x, y, s, fontsize=size, ha=ha, va=va, rotation=rot, family="DejaVu Sans",
            weight=weight, zorder=z)


def door(ax, hx, hy, w, d, n, leaf=True):
    """hinge (hx,hy); d = unit vector along wall hinge->latch; n = unit normal into room (swing)."""
    dx, dy = d
    nx, ny = n
    ax.plot([hx, hx + w * nx], [hy, hy + w * ny], color="black", lw=0.8, zorder=5)
    a_n = math.degrees(math.atan2(ny, nx)) % 360
    a_d = math.degrees(math.atan2(dy, dx)) % 360
    if (a_d - a_n) % 360 == 90:
        t1, t2 = a_n, a_d
    else:
        t1, t2 = a_d, a_n
    ax.add_patch(Arc((hx, hy), 2 * w, 2 * w, angle=0, theta1=t1, theta2=t2, lw=0.4, zorder=5))


def opening_h(ax, x0, x1, yc, t):
    """cut an opening in a horizontal wall: white rect over wall band."""
    ax.add_patch(Rectangle((x0, yc - t / 2), x1 - x0, t, fc="white", ec="none", zorder=3.5))
    ax.plot([x0, x0], [yc - t / 2, yc + t / 2], color="black", lw=0.4, zorder=4)
    ax.plot([x1, x1], [yc - t / 2, yc + t / 2], color="black", lw=0.4, zorder=4)


def opening_v(ax, y0, y1, xc, t):
    ax.add_patch(Rectangle((xc - t / 2, y0), t, y1 - y0, fc="white", ec="none", zorder=3.5))
    ax.plot([xc - t / 2, xc + t / 2], [y0, y0], color="black", lw=0.4, zorder=4)
    ax.plot([xc - t / 2, xc + t / 2], [y1, y1], color="black", lw=0.4, zorder=4)


# Unit 1's windows were drawn here, as three lines centred in the wall with a jamb tick
# at each end and the mark set out in model inches — a symbol of this file's own, which
# is why they printed unlike every other window in the set. They are the library's
# `PlanDraw.window()` now; draw_windows() below is all that is left of them.


def dim_h(ax, x0, x1, y, label=None, size=6, off=0):
    ax.plot([x0, x1], [y, y], color="black", lw=0.4, zorder=5)
    for x in (x0, x1):
        ax.plot([x - IN(1.5), x + IN(1.5)], [y + IN(1.5), y - IN(1.5)], color="black", lw=0.5, zorder=5)
    txt(ax, (x0 + x1) / 2, y - IN(2.5) + off, label or fi(x1 - x0), size, va="bottom")


def dim_v(ax, y0, y1, x, label=None, size=6, off=0):
    ax.plot([x, x], [y0, y1], color="black", lw=0.4, zorder=5)
    for y in (y0, y1):
        ax.plot([x + IN(1.5), x - IN(1.5)], [y - IN(1.5), y + IN(1.5)], color="black", lw=0.5, zorder=5)
    txt(ax, x - IN(2.5) + off, (y0 + y1) / 2, label or fi(y1 - y0), size, rot=90, va="bottom")


# ---------------------------------------------------------------- fixtures
def bed(ax, x0, y0, x1, y1, head):
    """head: 'W','E','N','S' side of the rectangle where the headboard is."""
    rect(ax, x0, y0, x1, y1, lw=0.5)
    if head == "W":
        rect(ax, x0 + IN(2), y0 + IN(4), x0 + IN(12), (y0 + y1) / 2 - IN(2), lw=0.4)
        rect(ax, x0 + IN(2), (y0 + y1) / 2 + IN(2), x0 + IN(12), y1 - IN(4), lw=0.4)
        ax.plot([x0 + IN(20), x0 + IN(20)], [y0, y1], color="black", lw=0.3)
    elif head == "E":
        rect(ax, x1 - IN(12), y0 + IN(4), x1 - IN(2), (y0 + y1) / 2 - IN(2), lw=0.4)
        rect(ax, x1 - IN(12), (y0 + y1) / 2 + IN(2), x1 - IN(2), y1 - IN(4), lw=0.4)
        ax.plot([x1 - IN(20), x1 - IN(20)], [y0, y1], color="black", lw=0.3)
    txt(ax, (x0 + x1) / 2, (y0 + y1) / 2, f"BED {fi(min(x1-x0,y1-y0))} x {fi(max(x1-x0,y1-y0))}", 5)


def tub(ax, x0, y0, x1, y1, drain_end="E"):
    rect(ax, x0, y0, x1, y1, lw=0.6)
    ax.add_patch(Rectangle((x0 + IN(3), y0 + IN(3)), x1 - x0 - IN(6), y1 - y0 - IN(6), fc="none", ec="black",
                           lw=0.4, zorder=4, joinstyle="round"))
    dx = x1 - IN(6) if drain_end == "E" else x0 + IN(6)
    ax.add_patch(Ellipse((dx, (y0 + y1) / 2), IN(3), IN(3), fc="none", ec="black", lw=0.4, zorder=5))
    txt(ax, (x0 + x1) / 2, (y0 + y1) / 2, "TUB 60x30", 5)


def wc(ax, cx, cy, wall_side="E"):
    # tank against wall, bowl projecting 28" from finished wall
    s = 1 if wall_side == "E" else -1
    tank = sorted((cx + s * IN(10), cx + s * IN(18)))
    rect(ax, tank[0], cy - IN(9), tank[1], cy + IN(9), lw=0.5)
    ax.add_patch(Ellipse((cx - s * IN(1), cy), IN(20), IN(14), fc="none", ec="black", lw=0.5, zorder=4))
    txt(ax, cx - s * IN(1), cy, "WC", 5)


def lav(ax, x0, y0, x1, y1):
    rect(ax, x0, y0, x1, y1, lw=0.5)
    ax.add_patch(Ellipse(((x0 + x1) / 2, (y0 + y1) / 2), IN(14), IN(11), fc="none", ec="black", lw=0.4, zorder=4))
    txt(ax, (x0 + x1) / 2, y1 + IN(4), "LAV 24\"", 5)


def base(ax, x0, y0, x1, y1, label=None):
    rect(ax, x0, y0, x1, y1, lw=0.5)
    if label:
        txt(ax, (x0 + x1) / 2, (y0 + y1) / 2, label, 5)


def sink(ax, cx, cy):
    ax.add_patch(Ellipse((cx - IN(7), cy), IN(12), IN(14), fc="none", ec="black", lw=0.4, zorder=4))
    ax.add_patch(Ellipse((cx + IN(7), cy), IN(12), IN(14), fc="none", ec="black", lw=0.4, zorder=4))


def range_(ax, x0, y0, x1, y1):
    rect(ax, x0, y0, x1, y1, lw=0.5)
    for (a, b) in ((0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)):
        ax.add_patch(Ellipse((x0 + a * (x1 - x0), y0 + b * (y1 - y0)), IN(6), IN(6), fc="none", ec="black", lw=0.3, zorder=4))


def rod(ax, x0, y0, x1, y1):
    ax.plot([x0, x1], [y0, y1], color="black", lw=0.5, ls="--", zorder=4)


def bypass(ax, x0, x1, yc, t):
    opening_h(ax, x0, x1, yc, t)
    m = (x0 + x1) / 2
    rect(ax, x0, yc - IN(1.5), m + IN(1), yc - IN(0.3), lw=0.4, fc="white")
    rect(ax, m - IN(1), yc + IN(0.3), x1, yc + IN(1.5), lw=0.4, fc="white")








# ================================================================ LEVEL 1
# `fig` and `fr` are the standalone matplotlib study's figure and text frame. Neither
# is used: draw() passes None for both. They stay in the signature because that study
# is how these two functions are still read against the original drawings.
def level1(fig, fr):
    ax = plan_axes(fig, 1.2, 2.6, (-70, W_STUD + 70), (-70, D_STUD + 60))
    shell(ax, 1)
    draw_windows(ax, 1)
    draw_stair(ax, "UP 14R")
    txt(ax, IN(21.75), LB + IN(18), f"LANDING\n{fi(SX)} x 3'-0\"", 5)
    ax.plot([IN(2), IN(38)], [IN(170), IN(236)], color="black", lw=0.3, ls=":")
    txt(ax, IN(29), IN(205), "UNDER-STAIR CLOSET\n1'-10\" DOOR OFF MECH\n1/2\" GWB U/S (302.7)", 4.2, rot=90)
    rect(ax, IN(0), IN(185), IN(18), IN(216), lw=0.4, ls="-.")
    txt(ax, IN(9), IN(200), "SHELVING 18\" D", 4, rot=90)
    opening_v(ax, YT - IN(24), YT, SX + P / 2, P)
    door(ax, SX, YT, IN(22), (0, -1), (-1, 0))
    # front door
    opening_h(ax, IN(2.75), IN(40.75), -EXT / 2, EXT)
    door(ax, IN(2.75), IN(0), IN(36), (1, 0), (0, 1))
    txt(ax, IN(21.75), IN(40), "ENTRY", 6, weight="bold", rot=90)
    txt(ax, IN(21.75), IN(56), "D-1\n3'-0\" x 6'-8\"", 5, rot=90)
    # doors on the rear-zone north wall
    opening_h(ax, IN(47.75), IN(81.75), B1 + P / 2, P)
    door(ax, IN(47.75), B1, IN(32), (1, 0), (0, -1))               # mech out-swing
    opening_h(ax, BX1 - IN(35.5), BX1 - IN(3.5), B1 + P / 2, P)
    door(ax, BX1 - IN(3.5), R0, IN(30), (-1, 0), (0, 1))           # bath 1, hinged in the east corner, clear of the fixtures
    opening_h(ax, IN(161.75), IN(195.75), B1 + P / 2, P)
    door(ax, IN(161.75), R0, IN(32), (1, 0), (0, 1))               # BR1
    opening_v(ax, PK0 + IN(1), D_STUD - IN(1), BX1 + P / 2, P)          # closet door in the east 2x4, 1'-10"
    door(ax, BR_X, D_STUD - IN(1), IN(22), (0, -1), (1, 0))
    # rooms
    room(ax, MX0, IN(0), KX, B1, "LIVING / DINING", dy=-IN(20))
    room(ax, KX, IN(0), W_STUD, B1, "KITCHEN", dy=-IN(25))
    room(ax, MX0, R0, MX1, D_STUD, "MECH", 6, dy=IN(8))
    room(ax, BX0, R0, BX1, BY1, "BATH 1", 6, dy=-IN(22))
    room(ax, BX0, PK0, BX1, D_STUD, "CLOSET (BR1)", 5, dy=-IN(3))   # up, off the ROD + SHELF line
    room(ax, BR_X, R0, W_STUD, D_STUD, "BEDROOM 1", dy=-IN(30))
    # mech fixtures
    rect(ax, MX0, IN(174), MX0 + IN(4), IN(188.5), lw=0.6)
    txt(ax, IN(51.75), IN(181), "PNL", 5, ha="left")
    # The tank and both working spaces are the plumbing model's (src/plumbing.py), which
    # check_working_spaces() holds to NEC 110.26(A) and RCO M1305.1. They were typed here
    # and kept the wall-hung tankless's 11-1/2" x 18-1/2" after the model took the 50-gallon
    # 20" storage tank; drawing them from the model is what stops that recurring.
    from src.plumbing import HEATER_RECT, HEATER_SPACE, PANEL_SPACE
    def _study(r):
        return r[0]-X_OFFSET, r[1]-Y_OFFSET, r[0]-X_OFFSET+r[2], r[1]-Y_OFFSET+r[3]
    px0, py0, px1, py1 = _study(PANEL_SPACE["UNIT 1"])
    rect(ax, px0, py0, px1, py1, lw=0.5, ls="--")
    txt(ax, (px0+px1)/2, py1-IN(5), "36\" x 30\" NEC 110.26", 4)
    tx0, ty0, tx1, ty1 = _study(HEATER_RECT["UNIT 1"])
    rect(ax, tx0, ty0, tx1, ty1, lw=0.6)
    ax.add_patch(Ellipse(((tx0+tx1)/2, (ty0+ty1)/2), tx1-tx0-IN(1), ty1-ty0-IN(1), fc="none", ec="black", lw=0.3, zorder=4))
    txt(ax, (tx0+tx1)/2, (ty0+ty1)/2, "WH", 5)
    hx0, hy0, hx1, hy1 = _study(HEATER_SPACE["UNIT 1"])
    rect(ax, hx0, hy0, hx1, hy1, lw=0.5, ls="--")
    txt(ax, (hx0+hx1)/2, hy0+IN(5), "30\" x 30\" RCO M1305.1", 4)
    rect(ax, IN(4), D_STUD - IN(31.5), IN(36), D_STUD - IN(4.5), lw=0.6)
    txt(ax, IN(20), D_STUD - IN(18), "W/D\n27\" x 32\"\nFACES SOUTH", 5)
    rect(ax, IN(0), D_STUD - IN(31.5), IN(4), D_STUD - IN(4.5), lw=0.3, ls=":")
    rect(ax, MX1 - IN(12), YT + IN(1.5), MX1, D_STUD, lw=0.4, ls="-.")
    txt(ax, MX1 - IN(6), YT + IN(18), "SHELF 12\" D", 4, rot=90)
    txt(ax, IN(61.75), YT + IN(17), "LAUNDRY\nLOADING\n3'-7\" x 3'-0\"", 5)
    bath_fixtures(ax)
    # kitchen
    base(ax, W_STUD - IN(24), IN(15), W_STUD, IN(45)); range_(ax, W_STUD - IN(24), IN(15), W_STUD, IN(45)); txt(ax, W_STUD - IN(12), IN(30), "RANGE", 4.5)
    base(ax, W_STUD - IN(24), IN(45), W_STUD, IN(69), "DW")
    base(ax, W_STUD - IN(24), IN(69), W_STUD, IN(105)); sink(ax, W_STUD - IN(12), IN(87)); txt(ax, W_STUD - IN(12), IN(100), "SINK", 4.5)
    base(ax, W_STUD - IN(24), IN(105), W_STUD, IN(137.5), "CORNER")
    base(ax, KX, B1 - IN(30), KX + IN(36), B1, "REF 36x30")
    base(ax, KX + IN(36), B1 - IN(24), W_STUD, B1, "PANTRY / BASE")
    # bedroom 1
    bed(ax, W_STUD - IN(80), IN(215), W_STUD, IN(275), "E")
    rod(ax, BX0 + IN(3), D_STUD - IN(5), BX1 - IN(3), D_STUD - IN(5))
    txt(ax, IN(121.75), D_STUD - IN(7.5), "ROD + SHELF", 4.5)


def level2(fig, fr):
    ax = plan_axes(fig, 1.2, 2.6, (-70, W_STUD + 70), (-70, D_STUD + 60))
    shell(ax, 2)
    draw_windows(ax, 2)
    wall(ax, DEM0, IN(0), DEM1, FZ)
    # BR2 projecting closet
    wall(ax, IN(47.75), IN(94.5), IN(51.25), FZ); wall(ax, IN(99.25), IN(94.5), IN(102.75), FZ); wall(ax, IN(47.75), IN(94.5), IN(102.75), IN(98))
    bypass(ax, IN(53.25), IN(95.5), IN(96.25), P); rod(ax, IN(53.25), FZ - IN(3), IN(97.25), FZ - IN(3))
    # notch closets
    bypass(ax, IN(203.75), IN(247.75), B1 + P / 2, P); rod(ax, NX + IN(6), B0 + IN(5), CS - IN(3), B0 + IN(5))
    txt(ax, (NX + CS) / 2 + IN(2), B0 + IN(15), f"CLOSET BR4\n{fi(CS-NX-P)} x 3'-0\"", 4.8)
    bypass(ax, CS + IN(5), W_STUD - IN(3), FZ + P / 2, P); rod(ax, CS + IN(6), B1 - IN(5), W_STUD - IN(3), B1 - IN(5))
    txt(ax, (CS + W_STUD) / 2 + IN(2), B0 + IN(15), f"CLOSET BR3\n{fi(W_STUD-CS-P)} x 3'-0\"", 4.8)
    # stair well
    ax.add_patch(Rectangle((IN(0), B0), SX, YT - B0, fc="white", ec="none", zorder=2))
    draw_stair(ax, "UP")
    ax.plot([IN(0), SX], [B0, B0], color="black", lw=0.8, zorder=5)
    txt(ax, IN(21.75), IN(190), f"OPEN TO BELOW\nWELL {fi(SX)} x 9'-9\"", 5, rot=90)
    txt(ax, IN(21.75), D_STUD - IN(18), f"LANDING\n{fi(MX0)} x 3'-0\"", 5)
    # doors
    opening_h(ax, IN(102.75), IN(136.75), FZ + P / 2, P); door(ax, IN(102.75), FZ, IN(32), (1, 0), (0, -1))     # BR2
    opening_h(ax, IN(155.75), IN(189.75), FZ + P / 2, P); door(ax, IN(155.75), FZ, IN(32), (1, 0), (0, -1))     # BR3
    opening_h(ax, IN(161.75), IN(195.75), B1 + P / 2, P); door(ax, IN(161.75), R0, IN(32), (1, 0), (0, 1))      # BR4
    opening_h(ax, BX1 - IN(35.5), BX1 - IN(3.5), B1 + P / 2, P); door(ax, BX1 - IN(3.5), R0, IN(30), (-1, 0), (0, 1))   # bath 2, off the cross hall, over bath 1
    opening_v(ax, PK0 + IN(1), D_STUD - IN(1), WW0 + WET / 2, WET); door(ax, WW0, D_STUD - IN(1), IN(22), (0, -1), (-1, 0))        # linen
    # rooms
    room(ax, IN(0), IN(0), DEM0, FZ, "BEDROOM 2", dy=-IN(30))
    room(ax, DEM1, IN(0), W_STUD, FZ, "BEDROOM 3", dy=-IN(30))
    room(ax, MX0, B0, NX, B1, "HALL", 6)
    room(ax, MX0, R0, MX1, D_STUD, "HALL", 6, dy=-IN(18))
    room(ax, BX0, R0, BX1, BY1, "BATH 2", 6, dy=-IN(22))
    room(ax, BX0, PK0, BX1, D_STUD, "LINEN", 5)
    room(ax, BR_X, R0, W_STUD, D_STUD, "BEDROOM 4", dy=-IN(30))
    bath_fixtures(ax)
    bed(ax, IN(68.75), IN(20), DEM0, IN(80), "E")
    bed(ax, DEM1, IN(20), DEM1 + IN(80), IN(80), "W")
    bed(ax, W_STUD - IN(80), IN(215), W_STUD, IN(275), "E")
    txt(ax, U1_ATTIC_LABEL[0], U1_ATTIC_LABEL[1], "ATTIC ACCESS\n22x30 IN CLG", 4.5)
    rect(ax, U1_ATTIC[0], U1_ATTIC[1], U1_ATTIC[2], U1_ATTIC[3], lw=0.4, ls="--")






F2_DEPTH = levels.F2_DEPTH  # joist + subfloor only; floor finish is separate


CEILING = levels.F2_GYPSUM


def _color(v):
    r,g,b,a = to_rgba(v)
    return Color(r,g,b), a


class PlanArtist:
    """Small plotting facade for the supplied helpers, with explicit draw order."""
    def __init__(self, p):
        self.p = p
        self.items = []
    def add_patch(self, patch):
        self.items.append((patch.get_zorder(), 'patch', patch))
    def plot(self, xs, ys, **kw):
        self.items.append((kw.get('zorder', 2), 'line', (xs,ys,kw)))
    def text(self, x, y, s, **kw):
        self.items.append((kw.get('zorder', 6), 'text', (x,y,s,kw)))
    def window(self, x, y, ln, o, mark):
        """The library's own plan window, in PLAN feet, deferred like everything else.

           It has to be deferred: `PlanDraw.window()` draws the moment it is called,
           and Unit 1's walls are painted by flush() afterwards, which would bury it.
           3.6 puts it over the walls at 3 and the door punches at 3.5 and under the
           fittings at 4 — the order the library draws them in on every other plan."""
        self.items.append((3.6, 'window', (x,y,ln,o,mark)))
    def annotate(self, s, xy, xytext, **kw):
        self.plot([xytext[0],xy[0]], [xytext[1],xy[1]], zorder=5, lw=.6)
        dx,dy=xy[0]-xytext[0],xy[1]-xytext[1]
        length=math.hypot(dx,dy); dx/=length; dy/=length
        for sign in (-1,1):
            self.plot([xy[0],xy[0]-IN(6)*dx+sign*IN(2.5)*dy],
                      [xy[1],xy[1]-IN(6)*dy-sign*IN(2.5)*dx],zorder=5,lw=.6)
    def flush(self):
        p=self.p; c=p.c
        X=lambda x:p.X(site_x(x)); Y=lambda y:p.Y(site_y(y))
        scale=p.sc
        for z,kind,data in sorted(self.items,key=lambda v:v[0]):
            if kind=='window':
                # The library's own symbol. It takes plan feet, sets its own A-GLAZ and
                # needs none of the state below, so it is handed the canvas untouched:
                # what it draws here has to be what it draws on every other plan, down
                # to the calls, or Unit 1's windows would differ again in some detail.
                p.window(*data); continue
            c.saveState()
            LAY('A-WALL' if z<=3.5 else 'A-FURN')
            if kind=='patch':
                a=data
                c.setStrokeColor(Color(*a.get_edgecolor()[:3]))
                c.setFillColor(Color(*a.get_facecolor()[:3]))
                c.setLineWidth(a.get_linewidth())
                ls=a.get_linestyle()
                if ls=='--': c.setDash(3,2)
                elif ls=='-.': c.setDash([5,2,1,2])
                elif ls==':': c.setDash(1,2)
                fill=int(a.get_facecolor()[3]>0); stroke=int(a.get_edgecolor()[3]>0)
                if isinstance(a,Rectangle):
                    x,y=a.get_xy()
                    c.rect(X(x),Y(y+a.get_height()),a.get_width()*scale,a.get_height()*scale,fill=fill,stroke=stroke)
                elif isinstance(a,Arc):
                    x,y=a.center; w,h=a.width*scale/2,a.height*scale/2
                    c.arc(X(x)-w,Y(y)-h,X(x)+w,Y(y)+h,startAng=-a.theta2,extent=(a.theta2-a.theta1)%360)
                elif isinstance(a,Ellipse):
                    x,y=a.center; w,h=a.width*scale/2,a.height*scale/2
                    c.ellipse(X(x)-w,Y(y)-h,X(x)+w,Y(y)+h,fill=fill,stroke=stroke)
                else:
                    raise TypeError('Unsupported Unit 1 primitive: '+type(a).__name__)
            elif kind=='line':
                xs,ys,kw=data
                c.setStrokeColor(_color(kw.get('color','black'))[0]); c.setLineWidth(kw.get('lw',.5))
                ls=kw.get('ls','-')
                if ls=='--': c.setDash(3,2)
                elif ls=='-.': c.setDash([5,2,1,2])
                elif ls==':': c.setDash(1,2)
                for i in range(len(xs)-1): c.line(X(xs[i]),Y(ys[i]),X(xs[i+1]),Y(ys[i+1]))
            else:
                LAY('A-ANNO-TEXT')
                x,y,s,kw=data
                s=s.replace('UP 14R','UP 15R')
                if 'NEC 110.26' in s: s='PANEL 36 x 30\nNEC 110.26(A)'
                if 'RCO M1305.1' in s: s='HEATER 30 x 30\nRCO M1305.1'
                if 'OPEN TO BELOW' in s: s='OPEN TO BELOW'
                size=max(3.5,kw.get('fontsize',7)*.72)
                c.translate(X(x),Y(y)); c.rotate(kw.get('rotation',0))
                c.setFillColor(black); c.setFont('Helvetica-Bold' if kw.get('weight')=='bold' else 'Helvetica',size)
                lines=s.split('\n'); leading=size*1.12
                baseline=(len(lines)-1)*leading/2-size*.32
                fn={'left':c.drawString,'right':c.drawRightString}.get(kw.get('ha','center'),c.drawCentredString)
                for i,line in enumerate(lines): fn(0,baseline-i*leading,line)
            c.restoreState()


def shell(ax, level):
    # The host supplies the common wall. The new shell meets its existing face.
    wall(ax,-EXT,-Y_OFFSET,W_STUD+EXT,IN(0))
    wall(ax,-EXT,IN(0),IN(0),D_STUD)
    wall(ax,W_STUD,IN(0),W_STUD+EXT,D_STUD)
    # L1 remains the bearing wall under the trimmer. L2 has a guard along the
    # hall-side open edge; retain only the short bedroom partition return.
    wall(ax,SX,LB if level==1 else FZ,SX+P,YT if level==1 else B0)
    if level==2:
        wall(ax,IN(0),FZ,SX,B0)
        wall(ax,MX0,FZ,W_STUD,B0)
        wall(ax,NX,B0,NX+P,R0)
        wall(ax,CS,B0,CS+P,B1)
    wall(ax,MX1,B1,W_STUD,R0)
    if level==1: wall(ax,MX0,B1,MX1,R0)
    wall(ax,WW0,R0,WW1,D_STUD)   # 2x6 wet wall, shared with MECH / the L2 hall
    wall(ax,BX1,R0,BR_X,D_STUD)  # 2x4 to Bedroom 1 / Bedroom 4
    wall(ax,BX0,BY1,BX1,PK0)


def room(ax,x0,y0,x1,y1,name,size=7,dy=0):
    # EVERY FIGURE IN THE LABEL IS DERIVED from the rectangle, below. This used to
    # take a `sub` string as well and never read it, so the square footage typed at
    # all thirteen call sites was inert -- along with two cross-references and a
    # "STACKED OVER BATH 1". What printed was derived and right; what was written was
    # decoration, and a maintainer correcting an area there would have seen nothing
    # change. Do not reintroduce it: correct the rectangle, not a caption.
    cx,cy=(x0+x1)/2,(y0+y1)/2+dy
    if name.startswith('BATH'): cy=(R0+BY1)/2-IN(3); cx=BX1-IN(19)  # the open east side
    if name=='MECH': return  # equipment and clearance labels identify the room
    if name=='HALL':
        if (y0,y1)==(B0,B1):
            # RCO 311.6 is a FINISHED clear width; every dimension on this sheet is
            # stud to stud. Print both, derived, so the 3'-1" segment in the A-102
            # north-south string and the 36" in A-001 reconcile on the drawing rather
            # than in a note on another sheet. Clear = framed less two 1/2" faces.
            w=y1-y0
            txt(ax,cx,cy-IN(3),'HALL',5)
            txt(ax,cx,cy+IN(4.5),
                      f'{fi(w)} FRAMED / {fi(w-IN(1))} CLEAR FIN.',4.2)
            return
        txt(ax,cx,cy,'HALL',5); return
    txt(ax,cx,cy-IN(5),name,max(size,8.5),weight='bold')
    label=f'{fi(x1-x0)} x {fi(y1-y0)}'
    if name.startswith('BEDROOM'):
        # Bedroom 2's reach-in is recessed out of the room, so its bounding box and its
        # floor area differ. Say which figure is being given rather than leaving the
        # reader to multiply the dimensions beside it and get 10 SF more.
        gross=(x1-x0)*(y1-y0)
        area=gross-(IN(55)*(FZ-IN(94.5)) if name=='BEDROOM 2' else 0.0)
        label+=f' / {area:.0f} SF' + (' NET OF CLOSET' if area < gross-0.5 else '')
    txt(ax,cx,cy+IN(5),label,max(size-1,6.5))


def _room_face(v,t,extent):
    """A wall CENTER, stepped half a wall to the room face on the inward side.

       `PlanDraw.window()` is given the room face, the way doors and cased openings are,
       because that is the face everything else on the plan is dimensioned to, and it
       measures the wall back from there to the plan edge behind it to find its
       thickness. src/building1.py's `windows()` gives each unit at its wall center, so
       the step is from the center toward the middle of the plan."""
    return v+t/2 if v < extent/2 else v-t/2


def draw_windows(ax,level):
    """Unit 1's windows, in plan feet, drawn by the library symbol like every other.

       Unit 1's four walls run out to the plan edge — site x 0 and 26, site y 0 — which
       is what lets the library derive EXT and Y_OFFSET from the face alone. The mark
       carries the W- prefix the plans, the A-602 schedule and the elevations share."""
    for x,y,length,o,mark in windows(level):
        if o=='h': ax.window(x,_room_face(y,Y_OFFSET,ax.p.D),length,'h','W-'+mark)
        else:      ax.window(_room_face(x,EXT,ax.p.W),y,length,'v','W-'+mark)


# Give the front door a full jamb-framing margin from the Sage corner.
_opening_h=opening_h


def opening_h(ax,x0,x1,yc,t):
    if x0==IN(2.75) and x1==IN(40.75) and yc<0:
        x0,x1,yc,t=IN(5.75),IN(43.75),-Y_OFFSET/2,Y_OFFSET
    return _opening_h(ax,x0,x1,yc,t)


_door=door


def door(ax,hx,hy,w,d,n,leaf=True):
    if hx==IN(2.75) and hy==0 and w==IN(36): hx=IN(5.75)
    if ax.level==2 and hx==IN(102.75) and hy==FZ and w==IN(32):
        hx+=w
        d=(-1,0)
    return _door(ax,hx,hy,w,d,n,leaf)


def draw_stair(ax,label):
    for i in range(NT+1):
        yy=YB+i*TREAD-NOSING
        if ax.level==2 and yy<B0: continue
        ax.plot([IN(0),SX],[yy,yy],lw=.4,zorder=4)
    start=max(YB+IN(4),B0+IN(4)) if ax.level==2 else YB+IN(4)
    ax.annotate('',xy=(SX/2.0,YT-IN(8)),xytext=(SX/2.0,start),zorder=5)
    txt(ax,SX/2.0,YT-IN(14) if ax.level==2 else start+IN(14),
          'DN' if ax.level==2 else 'UP',5,rot=90)


def draw_well_guard(ax):
    """36-inch guard in the former L2 wall footprint; leave top entry open."""
    for x in (SX+IN(.5),SX+P-IN(.5)):
        ax.plot([x,x],[B0,YT],lw=.8,zorder=5)
    bays=math.ceil((YT-B0)/IN(36))
    for i in range(bays+1):
        y=B0+IN(1.75)+(YT-B0-IN(3.5))*i/bays
        rect(ax,SX,y-IN(1.75),SX+P,y+IN(1.75),fc='white',lw=.6)
    ax.plot([SX+P,IN(66.75)],[IN(143),IN(143)],lw=.5,zorder=5)
    txt(ax,IN(84.75),IN(143),'36" HIGH GUARD\nAT WELL EDGE',4.5)


def bath_fixtures(ax):
    # Fixtures are measured from finished faces, half an inch inside the studs.
    # All three on the west wall, the 2x6 shared with MECH; see WW0.
    lav(ax,BX0+IN(.5),R0+IN(.5),BX0+IN(.5)+IN(21),R0+IN(24.5))
    wc(ax,BX0+IN(.5)+IN(18),R0+IN(39.5),'W')
    tub(ax,BX0+IN(.5),BY1-IN(30.5),BX1-IN(.5),BY1-IN(.5),'W')


def shift_bedroom2_closet(ax):
    """Move the reference closet's complete 55-inch enclosure to Sage.

    Only primitives wholly within its original bounds move: the three walls,
    bypass opening/leaves, jamb lines and rod. The bedroom entry stays put.
    """
    left,right,front,back=IN(47.75),IN(102.75),IN(94.5),FZ
    for _,kind,data in ax.items:
        if kind=='patch' and isinstance(data,Rectangle):
            x,y=data.get_xy()
            if left<=x and x+data.get_width()<=right and front<=y and y+data.get_height()<=back:
                data.set_x(x-left)
        elif kind=='line':
            xs,ys,kw=data
            if all(left<=x<=right for x in xs) and all(front<=y<=back for y in ys):
                xs[:]=[x-left for x in xs]


_ARTIST={'ax':None}


def plan_axes(*a,**k):
    """The study built a matplotlib axes per sheet; draw() builds one PlanArtist and
       every plan function shares it."""
    return _ARTIST['ax']


def draw(p,level,annotate=True):
    """Unit 1's plan. annotate=False leaves out what an electrical sheet does not
       want under its devices: the door and wall marks, the vent routes and the
       dimension strings. The rooms, fixtures and clearances stay."""
    c=p.c
    LAY('A-WALL'); c.setFillColor(white)
    c.rect(p.X(0),p.Y(site_y(D_STUD)),26*p.sc,site_y(D_STUD)*p.sc,fill=1,stroke=0)
    ax=PlanArtist(p)
    ax.level=level
    # level1 and level2 ask for their axes the way the standalone study did. There is
    # one artist per sheet and it is made here, so plan_axes just hands it back; the
    # holder is what lets a function called two frames down reach it.
    _ARTIST['ax']=ax
    # Both take (fig, fr) from the matplotlib study they came from and use neither.
    # A SimpleNamespace whose .text() did nothing used to stand in for the frame, and
    # it swallowed 21 general notes and two area takeoffs that read, in source, as
    # though they printed on A-101 and A-102. They printed nowhere for years and went
    # stale where no oracle could see them: gas serving the water heater, a gas meter
    # on the Sage wall, 'the common wall', and a 14-riser stair against the 15 the
    # set prints. They are deleted rather than revived -- every rule they stated has a
    # home sheet already, which is where the house style says it belongs.
    (level1 if level==1 else level2)(None,None)
    if level==2:
        shift_bedroom2_closet(ax)
        draw_well_guard(ax)
    # Correct the two service rectangles: measure depth from appliance face.
    ax.items=[item for item in ax.items if not (
        item[1]=='patch' and isinstance(item[2],Rectangle)
        and item[2].get_linestyle()=='--' and
        ((abs(item[2].get_x()-MX0)<.01 and abs(item[2].get_y()-IN(166.25))<.01)
         or (abs(item[2].get_x()-IN(46.75))<.01 and abs(item[2].get_y()-IN(196.25))<.01)))]
    if level==1:
        rect(ax,IN(49.25),IN(166.25),IN(85.25),IN(196.25),lw=.5,ls='--')
        rect(ax,IN(46.75),IN(196.25),IN(76.75),IN(226.25),lw=.5,ls='-.')
    if not annotate:
        ax.flush()
        return
    if level==1:
        # Schedule follows the drawn 32-inch mech leaf (34-inch rough opening).
        txt(ax,IN(65.75),IN(154),'D-7 / 2\'-8"',4.5)
        txt(ax,BX1-IN(19.5),IN(156),'D-8 / 2\'-6"',4.5)
        txt(ax,IN(186.75),IN(158),'D-2',4.5)
        txt(ax,IN(176.75),IN(270),'D-9',4.5)
        txt(ax,IN(35.75),IN(231),'D-10',4.5)
        # The dryer duct straight out behind the W/D. The route is the model's
        # (src/building1.py): M-101 draws the same one. The storage heater vents nothing.
        ax.plot([q[0] for q in U1_DR_DUCT],[q[1] for q in U1_DR_DUCT],lw=.6,ls='--',zorder=5)
        txt(ax,-IN(13),U1_DR_TERM,'DR-1',4.5,ha='right')
    else:
        for x,y,mark in ((IN(120.75),IN(115),'D-2'),(IN(175.75),IN(115),'D-2'),(IN(181.75),IN(171),'D-2'),
                         (BX1-IN(19.5),IN(156),'D-8'),(IN(80.75),IN(266),'D-9')): txt(ax,x,y,mark,4.5)
        for x,y in ((IN(28.75),IN(102)),(IN(226.75),IN(154)),(IN(273.75),IN(116))): txt(ax,x,y,'D-5',4.5)
    for x,y,mark in ((-IN(9.25),IN(115),'W1'),(W_STUD+IN(9.25),IN(115),'W1'),(IN(155.75),IN(245),'W6')):
        txt(ax,x,y,mark,5,rot=90)
    # Overall clear width and the principal room widths, to actual stud faces.
    dim_h(ax,IN(0),W_STUD,-IN(20),label=f'{fi(W_STUD)} STUD TO STUD',size=6)
    # The closet / linen between MX1 and BR_X takes no segment: it is 2'-1" deep, its own
    # caption already prints this width from the same rectangle, and the figure printed on it.
    for a,b in ((IN(0),SX),(MX0,MX1),(BR_X,W_STUD)):
        dim_h(ax,a,b,D_STUD-IN(6),size=5)
    # North-south string, stud to stud like everything else on the sheet, drawn on L2
    # because that is the level the cross hall splits. Every segment label is derived
    # from NS_FACES, so the string closes on the overall by construction.
    if level==2:
        for a,b in zip(NS_FACES,NS_FACES[1:]): dim_v(ax,a,b,-IN(21),size=5)
    dim_v(ax,IN(0),D_STUD,-IN(32) if level==2 else -IN(23),size=6)
    dim_v(ax,R0,BY1,W_STUD+IN(24),size=5)
    dim_v(ax,YT,D_STUD,-IN(12),label='36" FIN. LANDING',size=5)
    txt(ax,IN(11.75),IN(178),'15R @ 8" / 14T @ 9-1/4"',4.5,rot=90)
    ax.flush()
    # Unit 1's F2 joist direction used to be declared here as a span arrow on BOTH plan
    # sheets, labelled 'F2 I-JOISTS / 24'-9-1/2" CLEAR SPAN' with the span TYPED. It is
    # gone, and so are the F1 arrows on A-101 / A-102 / A-103 (building1._B1_JOISTS and
    # building2._B2_JOISTS are still the model data those bays come from — they are now
    # passed to the sheet as joists=()). S-102 owns floor framing: it draws every bay as
    # real joist lines at 16" o.c. with rims, wells, trimmers and headers, under labels
    # whose spans come from bay_span(). The set states framing once, on the framing plan.
    #
    # Nothing on an architectural sheet may point at a span arrow again. A-001 note 1b
    # sends the reader to S-102, and P-601 note 1e and the A-103 paragraph above were
    # repointed with this change. If the arrows ever come back, they come back on all
    # three plan sheets or on none — half the building framed and half not is worse on
    # paper than either, because it reads as an omission rather than a division of work.

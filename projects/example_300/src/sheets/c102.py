"""C-102 — the 11 x 17 zoning site plan, G-001 note 15.

   A separate document at the size Building and Zoning Services asks for, drawn from
   the same SITE_* geometry and the same zoning_rows()/zoning_relief() as C-101. It
   carries no construction information, deliberately."""
from math import cos, radians, sin

from arkitect.lib import assets
from arkitect.lib.draw import page
from arkitect.lib.draw.context import LAY, current_layer
from arkitect.lib.draw.page import GREY, PlanDraw, Sheet
from arkitect.lib.draw.text import table
from arkitect.lib.units import fmt
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.building1 import PLAN_L1, U2_ENTRY, U3_LAND_LO, U3_STAIR_W, U3_STOOP_HI, Y_SEP_BOT, Y_SEP_TOP
from src.building2 import U5_LAND_D, U5_LAND_X1, U5_STOOP_X0
from src.sitework import ALLEY_W, BLDG_DIM_IN, MANEUVER, PARK_D, PARK_N, PARK_PITCH, PARK_SETBACK, PARK_X1, REQ_NO, PARK_SETBACK_REQ, PARK_X0, PARK_Y0, PARK_Y1, SITE_BANDS, SITE_BLDG, SITE_D, SITE_LIVE_X, SITE_STAIR, SITE_W, SITE_WALK, TREE_R, TREE_X, TREE_Y, VISION, VISION_CLR, VISION_ST, VISION_ST_AREA, VISION_ST_CLR, VISION_ST_IN, zoning_relief, zoning_rows
from src.building1 import ENTRY_LEFT
from src import grading as G
from src.sheets.common import RELIEF_W
from arkitect.lib.draw.kit import draw_runs
from arkitect.lib.draw.kit import c


# The drawing is turned so true north is up the sheet, as a zoning site plan is read.
# Site coordinates put S Elm up the page and true north 14 degrees clockwise from
# sheet-left, so the plan turns 76 degrees clockwise: Sage to the top, S Elm to the
# right, the alley to the left and the adjacent parcel below. The compass art's native
# north is up, so it is drawn unturned.
TURN = -76.0

# The parcel the lot shares its south line with, as the county numbers it.
PARCEL_SOUTH = "010-000302"

# How far the streets, the alley and the parcels beyond them are drawn past the lot
# before they are broken off. Nothing past the right-of-way lines is measured, so none of
# it is dimensioned: the street names say what is there.
CONTEXT = 12.0


# ---------------- C-102's callouts ----------------
# What the zoning sheet has to say that C-101 does not, set on the plan beside what it
# describes, as a zoning site plan is annotated. Everything quantified here is read from
# the model, so it cannot drift from what C-101 tabulates.
def c102_callouts():
    _court = SITE_BANDS[2][1]-SITE_BANDS[2][0]
    assert VISION_CLR == VISION, "the alley vision triangle callout says the pad stands clear of it"
    return {
     # No fire separation distance and no 1-hour underside. Both are construction and
     # code, decided by RCO 302.1 and not by zoning, and both are carried where they are
     # decided — A-001 for the distance and A-601 for the listed assembly. What zoning
     # needs from this stair is that it projects, and that what it projects into is not a
     # yard the code requires.
     "stair": ["UNIT 5 STAIR PROJECTS %s INTO THE" % fmt(U5_LAND_D),
               "%s COURTYARD BETWEEN BUILDINGS." % fmt(_court),
               "THE COURTYARD IS NOT A REQUIRED ZONING YARD."],
     "access": ["ALL DWELLING UNITS HAVE PEDESTRIAN",
                "ACCESS TO A PUBLIC STREET."],
     "street": ["CLEAR VISION TRIANGLE %s x %s" % (fmt(VISION_ST), fmt(VISION_ST)),
                "C.C. 3321.05(B)(2), ALONG BOTH R.O.W. LINES.",
                "BUILDING 1'S CORNER IS %s INSIDE THE" % fmt(VISION_ST_IN),
                "HYPOTENUSE, %.0f SF; %s x %s IS CLEAR" % (VISION_ST_AREA, fmt(VISION_ST_CLR), fmt(VISION_ST_CLR)),
                "OF THE BUILDING — REQUEST %d." % REQ_NO["C.C. 3321.05(B)(2)"]],
     # short lines: the callout stands in the corner beside the alley, left of its far line
     "alley": ["CLEAR VISION TRIANGLE",
               "%s x %s," % (fmt(VISION), fmt(VISION)),
               "C.C. 3321.05(B)(1),",
               "CLEAR OF THE PAD."],
     # The pad, the alley it backs to and the setback line it stands inside — request 4.
     # The alley's width is what zoning measures maneuvering in, C.C. 3312.25.
     "parking": ["%d PARKING SPACES @ %s x %s, BACKING TO THE PUBLIC ALLEY."
                   % (PARK_N, fmt(PARK_PITCH), fmt(PARK_D)),
                 "PAD %s OFF THE SAGE R.O.W., OUTSIDE THE %s PARKING"
                   % (fmt(PARK_SETBACK), fmt(PARK_SETBACK_REQ)),
                 "SETBACK LINE OF C.C. 3312.27. THE ALLEY R.O.W. IS %s WIDE"
                   % fmt(ALLEY_W),
                 "WHERE C.C. 3312.25 REQUIRES %s OF MANEUVERING — REQUEST %d."
                   % (fmt(MANEUVER), REQ_NO["C.C. 3312.25"])],
     "tree": ["TREE — C.C. 3321.07"],
    }


# ============================= C-102 ZONING SITE PLAN =============================
def sheet_c102():
    """The 11 x 17 zoning site plan, G-001 note 15.

    A separate document at the size Building and Zoning Services asks for, drawn from
    the same SITE_* geometry and the same zoning_rows() / zoning_relief() as C-101, so
    the two cannot be made to disagree by editing one of them. Note 15 requires exactly
    that, and requires the status wording to be carried unchanged: RELIEF IS REQUESTED,
    NOT GRANTED.

    Laid out as a zoning site plan is: the lot turned to true north across the top of
    the sheet with the streets, the alley and the adjacent parcel around it, the
    buildings hatched and divided into their dwelling units, the vision triangles
    cross-hatched, and the notes set on the plan beside what they describe. The zoning
    tabulation and the relief requested run in columns under it.

    What it adds is what zoning reviews and a construction sheet does not foreground —
    the required yards and building lines with what stands in them, both stairs and
    their projections, the walk from every dwelling unit to the public way, the vision
    triangles and the tree. What it leaves out is everything about how the thing is
    built. C-102 stands on its own.
    """
    PG = page.ANSI_B
    sh=Sheet(c,"C-102","Zoning site plan","1/16\" = 1'-0\"",page=PG); sh.frame()
    ZX0,ZY0,ZX1,ZY1 = PG.DA
    sc = 4.5                                   # 1/16" = 1'-0", so 126'-0" is 7-7/8"

    # ---- the frame: site feet -> the turned plan -> page points ----
    # The plan is drawn by PlanDraw in a frame whose origin is the middle of the lot,
    # turned by TURN about the page point (CX, CY). site() maps a site point to the page
    # the same way, so callouts, leaders and the layout asserts can be written in page
    # terms against the drawing they point into.
    CX, CY = ZX0+6.25*inch, ZY0+6.33*inch
    _ct, _st = cos(radians(TURN)), sin(radians(TURN))
    p = PlanDraw(c,-SITE_W/2.0*sc,-SITE_D/2.0*sc,sc,SITE_W,SITE_D)
    def site(x,y):
        fx,fy = p.X(x),p.Y(y)
        return (CX+fx*_ct-fy*_st, CY+fx*_st+fy*_ct)
    BAND_TOP = ZY0+2.95*inch                   # the tabulation band under the plan
    _extent = [site(x,y) for x in (-SITE_WALK-9.0, SITE_W+CONTEXT)
                         for y in (-CONTEXT, SITE_D+ALLEY_W+CONTEXT)]
    assert min(q[0] for q in _extent) >= ZX0, "C-102 plan runs off the left of the drawing area"
    assert max(q[0] for q in _extent) <= ZX1, "C-102 plan runs off the right of the drawing area"
    assert max(q[1] for q in _extent) <= ZY1, "C-102 plan runs off the top of the drawing area"
    assert min(q[1] for q in _extent) >= BAND_TOP, ("C-102 plan runs %.2f in into the zoning table"
                                                  % ((BAND_TOP-min(q[1] for q in _extent))/inch))

    c.saveState(); c.translate(CX,CY); c.rotate(TURN)

    # ---- what is around the lot: the alley, the parcels, the street lines ----
    # The right-of-way lines the lot is measured from, carried past it and broken off.
    # The far lines of the two streets are not drawn: nothing on this sheet is measured
    # to them. The alley's is, because its width is what C.C. 3312.25 measures.
    def _break(x,y,along):
        # a short zig-zag across the end of a line that stops because the sheet does
        px,py = p.X(x),p.Y(y)
        path=c.beginPath()
        if along=='v':
            path.moveTo(px-3,py); path.lineTo(px-1,py+1.5); path.lineTo(px+1,py-1.5); path.lineTo(px+3,py)
        else:
            path.moveTo(px,py-3); path.lineTo(px+1.5,py-1); path.lineTo(px-1.5,py+1); path.lineTo(px,py+3)
        c.drawPath(path,fill=0,stroke=1)
    _alley_far = SITE_D+ALLEY_W
    c.setStrokeColor(black); c.setLineWidth(0.6)
    for (x0,y0,x1,y1) in ((0,SITE_D,0,_alley_far+CONTEXT),                 # Sage line, across the alley
                          (0,SITE_D,SITE_W+CONTEXT,SITE_D),                # alley, lot side
                          (0,_alley_far,SITE_W+CONTEXT,_alley_far),        # alley, far side
                          (SITE_W,0,SITE_W+CONTEXT,0)):                    # S Elm line, past the parcel
        c.line(p.X(x0),p.Y(y0),p.X(x1),p.Y(y1))
    _break(0,_alley_far+CONTEXT,'h')
    for yy in (SITE_D,_alley_far,0): _break(SITE_W+CONTEXT,yy,'v')
    c.setStrokeColor(GREY); c.setLineWidth(0.5); c.setDash([6,2,1,2])
    c.line(p.X(SITE_W),p.Y(SITE_D),p.X(SITE_W),p.Y(0))                     # the shared parcel line
    c.setDash(); c.setStrokeColor(black)

    # ---- the lot ----
    c.setStrokeColor(black); c.setLineWidth(1.4); c.setFillColor(white)
    c.rect(p.X(0),p.Y(SITE_D),SITE_W*sc,SITE_D*sc,fill=1,stroke=1)

    # ---- required yards, as dashed lines with the code section that sets each ----
    # The front building line and the side street line are the two this project is
    # measured against; the interior side yard is drawn for completeness. One coordinate
    # per required yard line, and every figure on this sheet that states a yard is
    # measured from them: the dashed line, its label and the tick below it cannot then
    # disagree. Typed figures here would be the only ones on the sheet not derived.
    #
    # The two side lines stop at the head of the parking pad. They used to run to the
    # rear lot line, through the stalls, with a third dashed line along the pad head, and
    # zoning asked for the pad clear of dashed lines so it could be read. The side street
    # line's encroachment is stated where it is measured — the pad callout and the
    # C.C. 3312.27 rows of the table — not by a line through the stalls.
    FBL, SSL, ISL = 20.0, 8.0, 34.0
    c.setStrokeColor(GREY); c.setLineWidth(0.6); c.setDash(3,2)
    for _a,_b,_c2,_d in ((0,FBL,SITE_W,FBL),(SSL,0,SSL,PARK_Y0),(ISL,0,ISL,PARK_Y0)):
        c.line(p.X(_a),p.Y(_b),p.X(_c2),p.Y(_d))
    c.setDash(); c.setStrokeColor(black)
    c.setFillColor(GREY); c.setFont("Helvetica",3.6)
    # A building line is a line and its label sits on it. A yard is a piece of ground, so
    # its label is centred in the ground it names — and each is set beside the building
    # its figure is measured to, which is not the same building for the two of them.
    # Clear of the Unit 1 landing, which occupies x 8'-11-1/4" to 11'-11-1/4" in this band
    c.drawString(p.X(12.4),p.Y(19.3),"FRONT BUILDING LINE %s — C.C. 3332.21"%fmt(FBL))
    _ssy="SIDE STREET YARD %s — C.C. 3332.22(a)(1)"%fmt(SSL)
    # Between the street-corner vision triangle, whose hypotenuse crosses this line at
    # 26'-0", and the Unit 2 walk at 52'-1-1/4"; below that the yard is stair, walk,
    # and the alley vision triangle.
    c.saveState(); c.translate(p.X(SSL/2.0),p.Y(38.0)); c.rotate(90)
    c.drawCentredString(0,0,_ssy); c.restoreState()
    # Beside Building 1. Both buildings are 26'-0" wide and stop at ISL, so the 6'-0" is
    # the same yard beside either of them.
    _isy="INTERIOR SIDE YARD %s"%fmt(SITE_W-ISL)
    c.saveState(); c.translate(p.X((ISL+SITE_W)/2.0),p.Y(44.0)); c.rotate(90)
    c.drawCentredString(0,0,_isy); c.restoreState()
    c.setFillColor(black)

    # ---- the clear vision triangles, cross-hatched ----
    # Each is a right triangle with its legs on the two right-of-way lines, so the hatch
    # is a grid parallel to those lines clipped to the hypotenuse by arithmetic.
    def _vision(cx0,cy0,sx,sy,leg):
        c.setStrokeColor(black); c.setLineWidth(0.25)
        k=1.5
        while k < leg:
            c.line(p.X(cx0+sx*k),p.Y(cy0),p.X(cx0+sx*k),p.Y(cy0+sy*(leg-k)))
            c.line(p.X(cx0),p.Y(cy0+sy*k),p.X(cx0+sx*(leg-k)),p.Y(cy0+sy*k))
            k+=1.5
        c.setLineWidth(0.7)
        t=c.beginPath(); t.moveTo(p.X(cx0),p.Y(cy0)); t.lineTo(p.X(cx0+sx*leg),p.Y(cy0))
        t.lineTo(p.X(cx0),p.Y(cy0+sy*leg)); t.close(); c.drawPath(t,fill=0,stroke=1)
    _vision(0,SITE_D,1,-1,VISION_CLR)          # Sage / alley
    _vision(0,0,1,1,VISION_ST)                 # S Elm / Sage; the 28'-0" clear is in the callout

    # ---- the buildings, hatched and divided into their dwelling units ----
    # Building 1 is Unit 1 at the S Elm end and Units 2 and 3, stacked, behind the W4
    # separation; Building 2 is Units 4 and 5, stacked. The labels read along the lot.
    _w4 = 20.0+(PLAN_L1.y(Y_SEP_TOP)+PLAN_L1.y(Y_SEP_BOT))/2.0
    def _along(x,y,lines):
        # lines of (font, size, text) centred on a site point, reading along the lot,
        # first line on top, on a white ground so the hatch does not run through them
        lead=[s*1.25 for _f,s,_t in lines]
        tall=sum(lead); wide=max(pdfmetrics.stringWidth(t,f,s) for f,s,t in lines)
        c.saveState(); c.translate(p.X(x),p.Y(y)); c.rotate(90)
        c.setFillColor(white); c.rect(-wide/2-1.5,-tall/2-1.5,wide+3,tall+3,fill=1,stroke=0)
        c.setFillColor(black); yy=tall/2
        for (f,s,t),ld in zip(lines,lead):
            yy-=ld; c.setFont(f,s); c.drawCentredString(0,yy+0.25*s,t)
        c.restoreState()
    for (bx,by,bw,bd,nm,_sub,kind) in SITE_BLDG:
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.0)
        c.rect(p.X(bx),p.Y(by+bd),bw*sc,bd*sc,fill=1,stroke=1)
        c.setStrokeColor(GREY); c.setLineWidth(0.3)
        yy=by+1.0
        while yy < by+bd:
            c.line(p.X(bx),p.Y(yy),p.X(bx+bw),p.Y(yy)); yy+=1.0
        c.setStrokeColor(black); c.setLineWidth(1.0)
        c.rect(p.X(bx),p.Y(by+bd),bw*sc,bd*sc,fill=0,stroke=1)
    _b1 = next(b for b in SITE_BLDG if b[4]=="BUILDING 1")
    _b2 = next(b for b in SITE_BLDG if b[4]=="BUILDING 2")
    assert _b1[1] < _w4 < _b1[1]+_b1[3], "the W4 separation is not inside Building 1"
    c.setStrokeColor(black); c.setLineWidth(1.0)
    c.line(p.X(_b1[0]),p.Y(_w4),p.X(_b1[0]+_b1[2]),p.Y(_w4))
    def _name(b):
        return [("Helvetica-Bold",6.0,b[4]),("Helvetica",4.2,b[6]),
                ("Helvetica",4.2,"%s x %s"%(fmt(b[2]),fmt(b[3])))]
    # Building 1's name on the W4 line between its two dwellings; Building 2 is one
    # stacked pair, so its units head its name.
    _along(_b1[0]+_b1[2]/2.0,_w4,_name(_b1))
    _along(_b1[0]+_b1[2]/2.0,(_b1[1]+_w4)/2.0-2.0,[("Helvetica-Bold",6.5,"UNIT 1")])
    _along(_b1[0]+_b1[2]/2.0,(_w4+_b1[1]+_b1[3])/2.0+2.0,[("Helvetica-Bold",6.5,"UNITS 2 AND 3")])
    _along(_b2[0]+_b2[2]/2.0,_b2[1]+_b2[3]/2.0,[("Helvetica-Bold",6.5,"UNITS 4 AND 5")]+_name(_b2))
    # One width and one depth per footprint, inside the outline as on C-101 — the yards
    # here are the same yards, with the same stairs, walks and labels in them.
    _was=current_layer()
    for (bx,by,bw,bd,_nm,_sub,_kind) in SITE_BLDG:
        p.dim(bx,bx+bw,'h',by+BLDG_DIM_IN,sd=-1)       # front face: the width
        p.dim(by,by+bd,'v',bx+BLDG_DIM_IN,sd=-1)       # Sage face: the depth
    LAY(_was)

    # ---- both exterior stairs, and the yard each projects into ----
    # These are the two items zoning has to see: the Unit 3 stair stands in the 8'-0"
    # side street yard under the C.C. 3332.22(a)(1) variance request, and the Unit
    # 5 stair projects into the 12'-0" gap between the buildings, which is not a yard
    # zoning regulates but is what sets that stair's fire separation distance.
    c.setStrokeColor(black); c.setLineWidth(0.8); c.setFillColor(white)
    _s0,_s3 = 20+U3_LAND_LO, 20+U3_STOOP_HI
    c.rect(p.X(SITE_STAIR[0]),p.Y(_s3),(SITE_STAIR[1]-SITE_STAIR[0])*sc,(_s3-_s0)*sc,fill=1,stroke=1)
    c.rect(p.X(8.0+U5_STOOP_X0),p.Y(80.0),(U5_LAND_X1-U5_STOOP_X0)*sc,U5_LAND_D*sc,fill=1,stroke=1)
    c.setFillColor(black); c.setFont("Helvetica",3.6)
    c.saveState(); c.translate(p.X((SITE_STAIR[0]+SITE_STAIR[1])/2.0),p.Y((_s0+_s3)/2)); c.rotate(90)
    c.drawCentredString(0,0,"UNIT 3 STAIR — %s PROJECTION"%fmt(U3_STAIR_W)); c.restoreState()

    # ---- walks and landings: how each dwelling unit reaches the public way ----
    c.setStrokeColor(GREY); c.setLineWidth(0.6); c.setFillColor(white)
    _u2_ly = 20.0+PLAN_L1.y(U2_ENTRY[1]); _u2_lc = _u2_ly+U2_ENTRY[2]/2.0-1.5
    c.rect(p.X(0),p.Y(_u2_lc+3.0),SITE_LIVE_X*sc,3.0*sc,fill=0,stroke=1)          # Unit 2
    c.rect(p.X(SITE_STAIR[0]+0.25),p.Y(108.0),3.0*sc,(108.0-_s3)*sc,fill=0,stroke=1)  # Unit 3
    c.rect(p.X(8+ENTRY_LEFT),p.Y(17.0),3.0*sc,17.0*sc,fill=0,stroke=1)            # Unit 1 walk
    # and its landing, y 17 to the building face at 20, so the Unit 1 walk reaches the
    # building it serves as every other walk here does.
    c.rect(p.X(8+ENTRY_LEFT),p.Y(20.0),3.0*sc,3.0*sc,fill=0,stroke=1)             # Unit 1 landing
    # Units 4 and 5: Unit 4's landing under the Unit 5 top landing, the walk beside the
    # stair from it to the Unit 3 walk, and Unit 5's walk from its stoop, all the grading
    # model's rectangles, as C-101 draws them.
    for _r in (G.U4_LANDING, G.U45_WALK, G.U5_WALK):
        c.rect(p.X(_r.x0),p.Y(_r.y1),(_r.x1-_r.x0)*sc,(_r.y1-_r.y0)*sc,fill=0,stroke=1)
    p.concrete(G.U45_WALK.x0,G.U45_WALK.y0,G.U45_WALK.x1,G.U45_WALK.y1)
    p.concrete(G.U5_WALK.x0,G.U5_WALK.y0,G.U5_WALK.x1,G.U5_WALK.y1)
    p.concrete(0.0,_u2_lc,SITE_LIVE_X,_u2_lc+3.0)
    p.concrete(SITE_STAIR[0]+0.25,_s3,SITE_STAIR[0]+3.25,108.0)
    p.concrete(8+ENTRY_LEFT,0.0,8+ENTRY_LEFT+3.0,17.0)
    c.setStrokeColor(black)

    # ---- the new public sidewalk, in the right-of-way ----
    c.setStrokeColor(GREY); c.setLineWidth(0.6)
    c.rect(p.X(-SITE_WALK),p.Y(SITE_D),SITE_WALK*sc,SITE_D*sc,fill=0,stroke=1)
    _swl="NEW %s PUBLIC SIDEWALK — FULL %s SAGE FRONTAGE"%(fmt(SITE_WALK),fmt(SITE_D))
    p.concrete(-SITE_WALK,0.0,0.0,SITE_D,clear=[p.vlabel_box(-SITE_WALK/2.0,40.0,_swl,"Helvetica",3.8)])
    c.setFillColor(black); c.setFont("Helvetica",3.8)
    c.saveState(); c.translate(p.X(-SITE_WALK/2.0),p.Y(40.0)); c.rotate(90)
    c.drawCentredString(0,0,_swl); c.restoreState()
    c.setStrokeColor(black)

    # ---- parking ----
    # The paved pad with a black outline and dividers and the stalls numbered, as on
    # C-101; each stall's figure is kept clear of the stipple.
    _plab="%s x %s"%(fmt(PARK_PITCH),fmt(PARK_D))
    _sny, _ply = PARK_Y0+3.0, PARK_Y0+9.0
    _clear=[]
    for _i in range(PARK_N):
        _cx=PARK_X0+(_i+0.5)*PARK_PITCH
        for _t,_f,_s,_y in ((str(_i+1),"Helvetica-Bold",5.0,_sny),(_plab,"Helvetica",3.6,_ply)):
            _w=pdfmetrics.stringWidth(_t,_f,_s)
            # read along the lot, as the building labels are: a box turned with the text
            _clear.append((p.X(_cx)-0.8*_s-1.2,p.Y(_y)-_w/2-1.2,p.X(_cx)+0.25*_s+1.2,p.Y(_y)+_w/2+1.2))
    c.setStrokeColor(black); c.setLineWidth(0.8); c.setFillColor(white)
    c.rect(p.X(PARK_X0),p.Y(PARK_Y1),(PARK_X1-PARK_X0)*sc,(PARK_Y1-PARK_Y0)*sc,fill=1,stroke=1)
    p.concrete(PARK_X0,PARK_Y0,PARK_X1,PARK_Y1,clear=_clear)
    c.setStrokeColor(black); c.setLineWidth(0.6)
    for i in range(1,PARK_N):
        xx=PARK_X0+i*PARK_PITCH
        c.line(p.X(xx),p.Y(PARK_Y1),p.X(xx),p.Y(PARK_Y0))
    c.setFillColor(black)
    for i in range(PARK_N):
        _cx=PARK_X0+(i+0.5)*PARK_PITCH
        for _t,_f,_s,_y in ((str(i+1),"Helvetica-Bold",5.0,_sny),(_plab,"Helvetica",3.6,_ply)):
            c.saveState(); c.translate(p.X(_cx),p.Y(_y)); c.rotate(90)
            c.setFont(_f,_s); c.drawCentredString(0,0,_t); c.restoreState()

    # ---- the tree, C.C. 3321.07 ----
    c.setLineWidth(0.6); c.setFillColor(white)
    c.circle(p.X(TREE_X),p.Y(TREE_Y),TREE_R*sc,fill=0,stroke=1)
    c.setFillColor(black); c.circle(p.X(TREE_X),p.Y(TREE_Y),0.45*sc,fill=1,stroke=1)

    # No sanitary. Zoning does not review it and no easement carries it, so a buried pipe
    # is "how the thing is built" — the one category this sheet exists to leave out. The
    # run went down the Sage side yard, which is the yard request 3 is about. C-101
    # note 4 and 4a-4d carry the size, the fall, the cleanouts and the tap question.

    # ---- dimensions and the streets ----
    # Both directions are dimensioned the same way: a band string against the plan and the
    # overall outside it. The chain closes on the overall, and its ticks fall on the heads
    # of the two dashed building lines.
    for a,b in ((0,SSL),(SSL,ISL),(ISL,SITE_W)):
        p.dim(a,b,'h',-2.5)
    p.dim(0,SITE_W,'h',-6.5); p.dim(0,SITE_D,'v',-SITE_WALK-2.5)
    for (a,b,t) in SITE_BANDS: p.dim(a,b,'v',43.0,t)
    # the alley, lot line to far right-of-way line, the width C.C. 3312.25 measures
    p.dim(SITE_D,_alley_far,'v',-SITE_WALK-2.5)          # in line with the lot depth
    p.note(20,-13.0,"S ELM AVENUE",7.0,bold=True)
    p.note(20,SITE_D+ALLEY_W/2.0+1.0,"PUBLIC ALLEY",5.4,bold=True)
    p.vnote(-SITE_WALK-9.0,100,"SAGE AVENUE","SIDE STREET",7.0)
    p.vnote(SITE_W+9.5,32,"PARCEL %s"%PARCEL_SOUTH,"ADJACENT PARCEL — NOT A STREET",5.4)
    c.restoreState()

    # ---- the callouts, set level on the sheet with a leader to what each describes ----
    CS, CL = 5.0, 6.2                          # callout type size and line spacing, pt
    _callouts = c102_callouts()
    _boxes = []
    def callout(key,tx,ty,target,side="l"):
        """Lines from page (tx, ty) down, the leader from the first line's `side` end to
           the site point `target`, with a dot on it."""
        lines=_callouts[key]; f="Helvetica"
        w=max(pdfmetrics.stringWidth(t,f,CS) for t in lines)
        c.setFillColor(black); c.setFont(f,CS)
        for i,t in enumerate(lines): c.drawString(tx,ty-i*CL,t)
        _boxes.append((key,tx,ty-(len(lines)-1)*CL-1.5,tx+w,ty+CS))
        gx,gy = site(*target)
        lx = tx-2.0 if side=="l" else tx+w+2.0
        c.setStrokeColor(black); c.setLineWidth(0.4)
        c.line(lx,ty+CS*0.35,gx,gy); c.circle(gx,gy,0.9,fill=1,stroke=0)
    I = inch
    callout("stair",   ZX0+4.35*I, ZY1-1.20*I, (8.0+(U5_STOOP_X0+U5_LAND_X1)/2.0, 80.0-U5_LAND_D/2.0))
    callout("access",  ZX0+7.05*I, ZY1-0.75*I, (SITE_LIVE_X/2.0, _u2_lc+1.5))
    callout("street",  ZX0+9.95*I, ZY1-0.12*I, (3.0, 4.0), side="l")
    callout("alley",   ZX0+0.05*I, ZY0+5.45*I, (2.0, SITE_D-3.0), side="r")
    callout("parking", ZX0+3.10*I, ZY0+3.55*I, (PARK_X1-4.5, PARK_Y1-2.0), side="l")
    callout("tree",    ZX0+10.95*I, ZY0+6.00*I, (TREE_X+TREE_R*0.7, TREE_Y+TREE_R*0.7), side="l")
    for key,x0,y0,x1,y1 in _boxes:
        assert ZX0 <= x0 and x1 <= ZX1 and BAND_TOP <= y0 and y1 <= ZY1, \
            "C-102 callout %r runs off the drawing area" % key

    # True north up the sheet, the compass art's own orientation, in the top right corner
    # beside the S Elm / Sage corner, clear of the plan and the street callout.
    _cs=0.60*inch
    _ccx, _ccy = ZX1-_cs/2.0, ZY1-_cs/2.0
    assert all(not (x0 < _ccx+_cs/2 and _ccx-_cs/2 < x1 and y0 < _ccy+_cs/2 and _ccy-_cs/2 < y1)
               for _k,x0,y0,x1,y1 in _boxes), "C-102 compass stands on a callout"
    c.drawImage(assets.image("compass.png"),_ccx-_cs/2,_ccy-_cs/2,width=_cs,height=_cs,
                mask="auto",preserveAspectRatio=True)

    # ---- the zoning tabulation, the SAME one C-101 draws, in two columns under the plan ----
    # then the relief requested beside it, then the drawing title and a graphic scale.
    # Each column is measured against the next and against the drawing area.
    TW, GAP = 3.3*inch, 0.30*inch
    t1x = ZX0
    t2x = t1x+TW+GAP
    rx  = t2x+TW+GAP
    assert rx+RELIEF_W <= ZX1, ("C-102 zoning relief runs %.2f in past the drawing area"
                                % ((rx+RELIEF_W-ZX1)/inch))
    rows = zoning_rows()
    # split at a top-level row, never between a row and the indented rows under it
    half = len(rows)//2
    while half < len(rows) and rows[half][0].startswith(" "): half += 1
    TOP = BAND_TOP-0.12*inch
    c.setFillColor(black)
    _kw = dict(size=6.4,lead=0.138*inch,title_size=8.0,gap=0.20*inch)
    y1=table(c,t1x,TOP,"ZONING COMPLIANCE — COLUMBUS R-4",rows[:half],TW,**_kw)
    y2=table(c,t2x,TOP,"ZONING COMPLIANCE — CONTINUED",rows[half:],TW,**_kw)
    for _y,_n in ((y1,"first"),(y2,"second")):
        assert _y >= ZY0, ("C-102 zoning table's %s column overruns the sheet by %.2f in"
                           % (_n,(ZY0-_y)/inch))
    ry=draw_runs(rx,TOP,zoning_relief(),6.0,0.112*inch,RELIEF_W,"C-102 zoning relief")
    TTY = ZY0+0.10*inch
    assert ry >= TTY+0.55*inch, ("C-102 zoning relief runs %.2f in into the drawing title"
                                 % ((TTY+0.55*inch-ry)/inch))

    c.setFillColor(black)
    c.setFont("Helvetica-Bold",9.5); c.drawString(rx,TTY+0.26*inch,"ZONING SITE PLAN")
    c.setFont("Helvetica",6.0); c.drawString(rx,TTY+0.13*inch,"SCALE: 1/16\" = 1'-0\"")
    # the graphic scale: 0, 8, 16 and 32 feet, alternate bars filled
    _gx, _gy, _gh = rx+1.55*inch, TTY+0.28*inch, 3.0
    c.setLineWidth(0.5); c.setStrokeColor(black)
    for (a,b,fill) in ((0,8,1),(8,16,0),(16,32,1)):
        c.setFillColor(black if fill else white)
        c.rect(_gx+a*sc,_gy,(b-a)*sc,_gh,fill=1,stroke=1)
    c.setFillColor(black); c.setFont("Helvetica",4.6)
    for v in (0,8,16,32):
        c.drawCentredString(_gx+v*sc,_gy+_gh+1.8,"%d'"%v)
    assert _gx+32*sc <= ZX1, "C-102 graphic scale runs past the drawing area"
    c.showPage()

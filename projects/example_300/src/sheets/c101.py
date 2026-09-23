"""C-101 — the site plan, and the sheet that governs the work on the lot.

   Drawn at 1/8" = 1'-0" from the SITE_* geometry in src/sitework.py, which C-102
   also reads: nothing here may contradict that sheet because neither owns the lot."""
from lib import assets
from lib.draw.context import LAY, current_layer
from lib.draw.page import GREY, PlanDraw, Sheet
from lib.draw.text import table
from lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.building1 import PLAN_L1, U2_ENTRY, U2_LANDING_DROP, U2_LANDING_MAX, U3_FLIGHT_HI, U3_LAND_HI, U3_LAND_LO, U3_STAIR_TAG, U3_STAIR_W, U3_STOOP_HI, U3_STOOP_Z, U3_TREADS
from src.building2 import U5_FLIGHT_X0, U5_LAND_D, U5_LAND_X0, U5_LAND_X1, U5_STAIR_TAG, U5_STOOP_X0, U5_STOOP_Z, U5_TREADS
from src.foundation import B2 as B2_FOUNDATION
from src import exterior as X, fsd, grading as G
from codes.ohio.rco import fire_separation as rco_fsd
from src.mirror import LIVE_SIDE
from src.mechanical import ODU_TERM_CLR
from src.sitework import ALLEY_W, HP_WIN_CLR, MANEUVER, PARK_X1, REQ_NO, SAFF_WALL_X, SIDE_FACE, SIDE_MIN, SIDE_PARCEL, BLDG_DIM_IN, PARK_D, PARK_N, PARK_PITCH, PARK_SETBACK, PARK_SETBACK_REQ, PARK_X0, PARK_Y0, PARK_Y1, SAN_CROSS, SAN_MAIN_Y, SAN_X, SITE_BANDS, SITE_BLDG, SITE_D, SITE_LIVE_X, SITE_STAIR, SITE_W, SITE_WALK, SVC_EQUIP, SVC_HP_MARKS, SVC_SAFFORD, TREE_R, TREE_X, TREE_Y, VISION, VISION_CLR, VISION_ST, VISION_ST_AREA, VISION_ST_CLR, VISION_ST_IN, check_b1_service, check_b2_service, check_site_clearances, zoning_relief, zoning_rows
from src.building1 import ENTRY_LEFT
from src.sitework import B1_REAR_Y, B2_COURT_Y, FSD_LINE_Y
from src.sitework import WHEEL_STOPS, WSTOP_H, WSTOP_L, WSTOP_SET, b2_openings
from src.drainage import BUILDINGS as DRAIN_BUILDINGS, sewer, total_dfu
from lib.model.drains import exit_site
from codes.ohio.opc_drainage import SLOPES as DRAIN_SLOPES, T710_1_1
from src.grading import STOOP_STEP, U5_STOOP
from src.sheets import roofdrain
from src.roof import B1_ROOF, rake
from src.sheets.common import RELIEF_W
from lib.draw.kit import draw_runs, fmt_in
from lib.draw.kit import DH, E, X0, X1, Y0, Y1, c

_REAR_RAKE = rake(B1_ROOF, 'REAR')


# ============================= C-101 SITE PLAN =============================
def sheet_c101():
    sh=Sheet(c,"C-101","Site plan","1/8\" = 1'-0\""); sh.frame()
    sc=E; W,D=SITE_W,SITE_D
    ox=X0+1.7*inch; oy=Y0+(DH-D*sc)/2-0.2*inch
    p=PlanDraw(c,ox,oy,sc,W,D)
    c.setStrokeColor(black); c.setLineWidth(1.6); c.setFillColor(white)
    c.rect(p.X(0),p.Y(D),W*sc,D*sc,fill=1,stroke=1)
    for (bx,by,bw,bd,nm,sub,kind) in SITE_BLDG:
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.2)
        c.rect(p.X(bx),p.Y(by+bd),bw*sc,bd*sc,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold",9)
        c.drawCentredString(p.X(bx+bw/2),p.Y(by+bd/2)+3,nm)
        c.setFont("Helvetica",7); c.drawCentredString(p.X(bx+bw/2),p.Y(by+bd/2)-7,kind)
        c.drawCentredString(p.X(bx+bw/2),p.Y(by+bd/2)-16,sub)
    c.setFillColor(black)
    # Each footprint carries one width and one depth — it is a rectangle, and a figure
    # on the opposite face said nothing the first had not. The strings run inside the
    # outline, 1'-6" off the front and Sage faces with the figure toward the middle,
    # because every yard outside is spoken for: the Unit 3 stair and its stoop note on
    # the Sage side, the meter and heat pump bank on the parcel side, the separation
    # note and the Unit 5 stair between the buildings, the landing label in front.
    _was=current_layer()
    for (bx,by,bw,bd,_nm,_sub,_kind) in SITE_BLDG:
        p.dim(bx,bx+bw,'h',by+BLDG_DIM_IN,sd=-1)       # front face: the width
        p.dim(by,by+bd,'v',bx+BLDG_DIM_IN,sd=-1)       # Sage face: the depth
    LAY(_was)
    # Unit 3 exterior stair: 3'-6" overall projection into the side yard, descending toward
    # the rear and landing in the 12'-0" rear yard.
    _s0=20+U3_LAND_LO; _s1=20+U3_LAND_HI
    _s2=20+U3_FLIGHT_HI; _s3=20+U3_STOOP_HI
    _sx0,_sx1=SITE_STAIR
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setFillColor(white)
    for _a,_b in ((_s0,_s1),(_s1,_s2),(_s2,_s3)):
        c.rect(p.X(_sx0),p.Y(_b),(_sx1-_sx0)*sc,(_b-_a)*sc,fill=1,stroke=1)
    for i in range(1,U3_TREADS):
        _yy=_s1+(_s2-_s1)*i/U3_TREADS
        c.line(p.X(_sx0),p.Y(_yy),p.X(_sx1),p.Y(_yy))
    _scx=(_sx0+_sx1)/2.0
    c.setFillColor(black); c.setFont("Helvetica",4.8)
    c.saveState(); c.translate(p.X(_scx),p.Y((_s1+_s2)/2)); c.rotate(90)
    c.drawCentredString(0,0,"UNIT 3 EXTERIOR STAIR — A-001 NOTE 13a, A-604"); c.restoreState()
    c.drawCentredString(p.X(_scx),p.Y(_s3)-6,U3_STAIR_TAG)
    c.saveState(); c.translate(p.X(_scx),p.Y((_s0+_s1)/2)); c.rotate(90)
    c.drawCentredString(0,0,"UNIT 3 TOP LANDING"); c.restoreState()
    # The stoop note goes on the side of the stair away from the building.
    _stoop_cy=p.Y((_s2+_s3)/2)
    _out = _sx0
    _stoop_note_x=p.X(_out-0.3)
    c.setFont("Helvetica",3.4)
    _put = c.drawRightString
    _put(_stoop_note_x,_stoop_cy+2,"CONCRETE STOOP — TOP %s ABOVE FINISHED GRADE"%inches(G.STOOP_TOP))
    _put(_stoop_note_x,_stoop_cy-2.5,"ONE %s STEP DOWN TO FINISHED GRADE"%inches(STOOP_STEP))
    c.setLineWidth(0.35)
    c.line(_stoop_note_x+1,_stoop_cy,p.X(_out),_stoop_cy)
    # Unit 5's exterior stair, on Building 2's courtyard face. Site x = 8 + page x, since
    # Building 2 spans site 8..34 with Sage on the sheet's left; it projects 3'-6" toward
    # smaller site y — plan north, up the page, which is EAST on the ground — from the face
    # at site y 80 into the 12'-0" gap between the buildings.
    _u5x = lambda v: 8.0+v
    _u5_y1, _u5_y0 = 80.0, 80.0-U5_LAND_D
    # Unit 4's landing is the pad S-101 casts, at its door under the top landing (A-103),
    # and out to that landing's edge, where it steps down onto the Units 4 and 5 walk.
    _u4 = {nm: (x0, y0, x1, y1) for x0, y0, x1, y1, nm in B2_FOUNDATION.pads}["UNIT 4 LANDING"]
    assert U5_LAND_X0 <= _u4[0] and _u4[2] <= U5_LAND_X1 and abs(_u4[1]+U5_LAND_D) < 1e-9 and abs(_u4[3]) < 1e-9, \
        "C-101 Unit 4 landing %r no longer fills the Unit 5 top landing's depth over %r" % (_u4, (U5_LAND_X0, U5_LAND_X1))
    assert abs(G.U4_LANDING.x0-_u5x(_u4[0])) < 1e-9 and abs(G.U45_WALK.y1-_u5_y0) < 1e-9, \
        "C-101 and the grading model no longer draw the same Unit 4 landing and walk"
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setFillColor(white)
    for _a,_b in ((U5_STOOP_X0,U5_FLIGHT_X0),(U5_FLIGHT_X0,U5_LAND_X0),(U5_LAND_X0,U5_LAND_X1)):
        c.rect(p.X(_u5x(_a)),p.Y(_u5_y1),(_b-_a)*sc,U5_LAND_D*sc,fill=1,stroke=1)
    for i in range(1,U5_TREADS):
        _xx=U5_LAND_X0-(U5_LAND_X0-U5_FLIGHT_X0)*i/U5_TREADS
        c.line(p.X(_u5x(_xx)),p.Y(_u5_y0),p.X(_u5x(_xx)),p.Y(_u5_y1))
    c.setFillColor(black); c.setFont("Helvetica",4.8)
    c.drawCentredString(p.X(_u5x((U5_FLIGHT_X0+U5_LAND_X0)/2.0)),p.Y(_u5_y0)+5,
                        "UNIT 5 EXTERIOR STAIR — A-001 NOTE 13b, A-604")
    # Centred on the length of landing short of the Unit 4 pad, so the label and the pad's
    # edge do not print through each other.
    c.saveState(); c.translate(p.X(_u5x((U5_LAND_X0+_u4[0])/2.0)),p.Y((_u5_y0+_u5_y1)/2.0)); c.rotate(90)
    c.drawCentredString(0,0,"UNIT 5 TOP LANDING"); c.restoreState()
    c.setFont("Helvetica",4.2)
    c.saveState(); c.translate(p.X(_u5x((U5_STOOP_X0+U5_FLIGHT_X0)/2.0)),p.Y((_u5_y0+_u5_y1)/2.0)); c.rotate(90)
    c.drawCentredString(0,0,"6\" STOOP"); c.restoreState()
    c.drawCentredString(p.X(_u5x((U5_FLIGHT_X0+U5_LAND_X1)/2.0)),p.Y(_u5_y0)+12,U5_STAIR_TAG)
    # The Units 4 and 5 walk, beside the stair and outside its projection, from Unit 4's
    # landing to the Unit 3 walk, and Unit 5's walk from its stoop to the same. Both are the
    # grading model's rectangles. The stair's run label and tag sit on the walk, above
    # the stair's edge, so the stipple leaves them bare, and the walk's own label below them.
    _u45 = G.U45_WALK
    _u45l = "%s WALK  —  UNITS 4 AND 5 TO THE UNIT 3 WALK" % fmt(_u45.y1-_u45.y0)
    # Centred on the length of walk past the building sewer, which crosses it from Building
    # 1's drain exit, so the label and the sewer's dashes do not print through each other.
    _u45_sewer_x = exit_site(DRAIN_BUILDINGS[0])[0]
    _u45lw = pdfmetrics.stringWidth(_u45l,"Helvetica",5.0)/sc
    _u45lx, _u45ly = (_u45_sewer_x+_u45.x1)/2.0, p.Y(_u45.y1)+19.0
    assert _u45ly+0.75*5.0 < p.Y(_u45.y0) and _u45_sewer_x+0.5 < _u45lx-_u45lw/2.0 and _u45lx+_u45lw/2.0 < _u45.x1, \
        "C-101 Units 4 and 5 walk label does not fit on the walk clear of the building sewer"
    def _cbox(cx,by,txt,size,pad=1.5):
        """The page box a centered horizontal string covers, for the stipple to leave bare."""
        w=pdfmetrics.stringWidth(txt,"Helvetica",size)
        return (p.X(cx)-w/2.0-pad,by-pad,p.X(cx)+w/2.0+pad,by+0.75*size+pad)
    _u45_clear=[_cbox(_u5x((U5_FLIGHT_X0+U5_LAND_X0)/2.0),p.Y(_u5_y0)+5,"UNIT 5 EXTERIOR STAIR — A-001 NOTE 13b, A-604",4.8),
                _cbox(_u5x((U5_FLIGHT_X0+U5_LAND_X1)/2.0),p.Y(_u5_y0)+12,U5_STAIR_TAG,4.2),
                _cbox(_u45lx,_u45ly,_u45l,5.0)]
    c.setStrokeColor(GREY); c.setLineWidth(0.7)
    for _r in (G.U5_WALK,_u45):
        c.rect(p.X(_r.x0),p.Y(_r.y1),(_r.x1-_r.x0)*sc,(_r.y1-_r.y0)*sc,fill=0,stroke=1)
    p.concrete(G.U5_WALK.x0,G.U5_WALK.y0,G.U5_WALK.x1,G.U5_WALK.y1)
    p.concrete(_u45.x0,_u45.y0,_u45.x1,_u45.y1,clear=_u45_clear)
    c.setFillColor(black); c.setFont("Helvetica",5.0)
    c.drawCentredString(p.X(_u45lx),_u45ly,_u45l)
    c.setStrokeColor(black)
    # parking. The pad is drawn as the paved surface it is — C.C. 3312.25 wants a hard
    # surface — with a black outline, black dividers and the stalls numbered; the label,
    # the setback text and the compass are kept clear of the stipple. Grey dividers on
    # bare lawn did not read as parking. The compass is placed here, ahead of its
    # drawing further down, because the stipple has to know where it will stand.
    _compass_size=1.15*inch
    _cr=_compass_size/2.0/sc                        # feet
    _ccx,_ccy=PARK_X1-3.5,PARK_Y1-5.0               # site feet: the last stall, below the label
    _plab="PARKING — %d SPACES @ %s x %s, BACKING TO ALLEY"%(PARK_N,fmt(PARK_PITCH),fmt(PARK_D))
    _plx, _ply = (PARK_X0+PARK_X1)/2.0, 116.2            # centred on the pad, under the setback text
    _sby = PARK_Y0+4.0                                   # the setback dimension, below the numbers
    _cvx = PARK_X0+0.45
    _sbl = [("Helvetica-Bold","%s TO SAGE R.O.W."%fmt(PARK_SETBACK)),
            ("Helvetica","NORTH LOT LINE"),
            ("Helvetica","PARKING SETBACK LINE %s, C.C. 3312.27"%fmt(PARK_SETBACK_REQ))]
    _sny = PARK_Y0+2.2                                   # stall numbers, at the head
    def _hbox(x,y,w,size,pad=1.5,centred=False):
        """The page box a horizontal label covers, for the stipple to leave bare."""
        px,py=p.X(x),p.Y(y); bx=px-w/2.0 if centred else px
        return (bx-pad,py-pad,bx+w+pad,py+0.75*size+pad)
    _clear=[_hbox(_plx,_ply,pdfmetrics.stringWidth(_plab,"Helvetica",6.4),6.4,centred=True)]
    _clear+=[_hbox(_cvx,_sby+0.45+0.75*_i,pdfmetrics.stringWidth(_t,_f,3.8),3.8)
             for _i,(_f,_t) in enumerate(_sbl)]
    _clear+=[_hbox(PARK_X0+(_i+0.5)*PARK_PITCH,_sny,pdfmetrics.stringWidth(str(_i+1),"Helvetica-Bold",7.0),7.0,centred=True)
             for _i in range(PARK_N)]
    _clear+=[(p.X(_ccx-_cr)-1,p.Y(_ccy+_cr)-1,p.X(_ccx+_cr)+1,p.Y(_ccy-_cr)+1)]
    # The wheel stops, stall 1's stop dimensioned from the wall beside it and stall 2's
    # tagged under it — note 2c. Neither the dimension nor the tag reaches a stall number.
    _wst="WHEEL STOP, NOTE 2c"
    _wsx,_wsy=(WHEEL_STOPS[1][0]+WHEEL_STOPS[1][2])/2.0,WHEEL_STOPS[1][3]+0.45
    _wdx,_wdm=WHEEL_STOPS[0][0]-0.5,(PARK_Y0+WHEEL_STOPS[0][1])/2.0
    _clear+=[(p.X(_x0)-1,p.Y(_y1)-1,p.X(_x1)+1,p.Y(_y0)+1) for _x0,_y0,_x1,_y1 in WHEEL_STOPS]
    _clear+=[_hbox(_wsx,_wsy,pdfmetrics.stringWidth(_wst,"Helvetica",3.8),3.8,centred=True)]
    _clear+=[p.vlabel_box(_wdx+(3.0+6.4*0.72)/sc,_wdm,fmt(WSTOP_SET),"Helvetica",6.4)]
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setFillColor(white)
    c.rect(p.X(PARK_X0),p.Y(PARK_Y1),(PARK_X1-PARK_X0)*sc,(PARK_Y1-PARK_Y0)*sc,fill=1,stroke=1)
    p.concrete(PARK_X0,PARK_Y0,PARK_X1,PARK_Y1,clear=_clear)
    c.setStrokeColor(black); c.setLineWidth(0.7)
    for i in range(1,PARK_N):
        xx=PARK_X0+i*PARK_PITCH
        c.line(p.X(xx),p.Y(PARK_Y1),p.X(xx),p.Y(PARK_Y0))
    c.setFillColor(black); c.setFont("Helvetica-Bold",7.0)
    for i in range(PARK_N):
        c.drawCentredString(p.X(PARK_X0+(i+0.5)*PARK_PITCH),p.Y(_sny),str(i+1))
    c.setFont("Helvetica",6.4)
    c.drawCentredString(p.X(_plx),p.Y(_ply),_plab)
    c.setStrokeColor(black); c.setLineWidth(0.6); c.setFillColor(white)
    for _x0,_y0,_x1,_y1 in WHEEL_STOPS:
        c.rect(p.X(_x0),p.Y(_y1),(_x1-_x0)*sc,(_y1-_y0)*sc,fill=1,stroke=1)
    _was=current_layer()
    p.dim(PARK_Y0,WHEEL_STOPS[0][1],'v',_wdx,sd=-1)
    LAY(_was)
    c.setFillColor(black); c.setFont("Helvetica",3.8)
    c.drawCentredString(p.X(_wsx),p.Y(_wsy),_wst)
    # Clear vision triangle at the Sage / alley corner, C.C. 3321.05(B)(1): VISION_CLR
    # on each right-of-way line from their intersection, which is the whole 10'-0" now
    # that the pad starts at x 10. The label sits inside it, off the sewer at x 1.
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setDash(2.5,2)
    _vt=c.beginPath(); _vt.moveTo(p.X(0),p.Y(SITE_D)); _vt.lineTo(p.X(VISION_CLR),p.Y(SITE_D))
    _vt.lineTo(p.X(0),p.Y(SITE_D-VISION_CLR)); _vt.close(); c.drawPath(_vt,fill=0,stroke=1)
    c.setDash(); c.setFillColor(black)
    # The label steps down the outside of the hypotenuse, each line starting a constant
    # distance past it, in the strip between the triangle and the pad: a block inside
    # the triangle sat by the sewer and did not read as the line's label. Each line is
    # held off the hypotenuse, x = y - (SITE_D - VISION_CLR), and short of the pad.
    _avl = [("Helvetica-Bold","CLEAR VISION"),
            ("Helvetica","%s x %s"%(fmt(VISION_CLR),fmt(VISION_CLR))),
            ("Helvetica","C.C. 3321.05(B)(1)")]
    for _i,(_f,_t) in enumerate(_avl):
        _yy = SITE_D-VISION_CLR+2.0+_i*1.2
        _xx = _yy-(SITE_D-VISION_CLR)+0.7
        _x1 = _xx+pdfmetrics.stringWidth(_t,_f,3.8)/sc
        assert _x1+0.5 <= PARK_X0, "C-101 alley clear vision label runs onto the pad: %r"%_t
        c.setFont(_f,3.8); c.drawString(p.X(_xx),p.Y(_yy),_t)
    # The pad off the Sage right-of-way — the north lot line — which zoning asked to
    # see dimensioned. The run goes from the lot line to the first stall line; its figure
    # sits to the right rather than over the line, because the building sewer runs at
    # x 1 and a figure centred on the run would print on it.
    c.setStrokeColor(black); c.setLineWidth(0.5)
    c.line(p.X(0),p.Y(_sby),p.X(PARK_X0),p.Y(_sby))
    for _xv in (0.0,PARK_X0): c.line(p.X(_xv)-3,p.Y(_sby)-3,p.X(_xv)+3,p.Y(_sby)+3)
    for _i,(_f,_t) in enumerate(_sbl):
        c.setFont(_f,3.8); c.drawString(p.X(_cvx),p.Y(_sby+0.45+0.75*_i),_t)
    # And the 30'-0" one at the S Elm / Sage corner, C.C. 3321.05(B)(2), drawn the
    # same way and for the same reason: its hypotenuse crosses Building 1's front corner
    # and the Unit 1 landing, and the drawing should say so.
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setDash(2.5,2)
    _vs=c.beginPath(); _vs.moveTo(p.X(0),p.Y(0)); _vs.lineTo(p.X(VISION_ST),p.Y(0))
    _vs.lineTo(p.X(0),p.Y(VISION_ST)); _vs.close(); c.drawPath(_vs,fill=0,stroke=1)
    # Only the 30'-0" triangle is drawn: it is the requirement, and the 2'-0" of building
    # inside it is what request 7 is for. The 28'-0" one clear of the building is stated
    # in the label, not drawn — a second dashed line through the corner read as clutter.
    c.setDash(); c.setFillColor(black)
    # The label sits beside the middle of the hypotenuse, in the open yard above it,
    # between the Unit 1 walk and the line — not in the corner, where it read as part of
    # the sidewalk. Every line is held clear of the hypotenuse, x + y = VISION_ST.
    _cvl = [("Helvetica-Bold","CLEAR VISION"),
            ("Helvetica","%s x %s"%(fmt(VISION_ST),fmt(VISION_ST))),
            ("Helvetica","C.C. 3321.05(B)(2)"),
            ("Helvetica","%s x %s CLEAR OF BUILDING 1"%(fmt(VISION_ST_CLR),fmt(VISION_ST_CLR))),
            ("Helvetica","VARIANCE REQUESTED")]
    _cvx0, _cvy0, _cvp = 8+ENTRY_LEFT+3.0+0.8, 4.2, 1.0       # off the walk; first baseline; pitch
    for _i,(_f,_t) in enumerate(_cvl):
        _yy = _cvy0+_i*_cvp
        _x1 = _cvx0+pdfmetrics.stringWidth(_t,_f,4.6)/sc
        assert _x1+0.8 <= VISION_ST-_yy, "C-101 clear vision label runs onto the hypotenuse: %r"%_t
        c.setFont(_f,4.6); c.drawString(p.X(_cvx0),p.Y(_yy),_t)
    # Sanitary. One 4" building sewer for both buildings, down the 2'-0" strip beside the
    # parking bay to the 8" main in the alley. The Sage side is the only clear route:
    # the adjacent-parcel side already carries the side walk, the Unit 3 stair, the meter
    # bank, the heat pumps and the underground branch to Building 2.
    c.setStrokeColor(black); c.setLineWidth(1.15); c.setDash(5,2.5); c.setFillColor(black)
    # The lateral crosses the rear yard at y 77 rather than 74: the Unit 3 stoop now lands
    # on this side of the building and a 6" concrete pad with a thickened edge has no
    # business sitting 1'-3" off a sewer trench. At 77 it clears the stoop by 4'-3" and
    # still leaves 3'-0" to Building 2.
    # Where each building drain comes through its wall is P-101's: the Building 1 exit
    # starts the sewer, the Building 2 exit starts its lateral, and the two cleanouts
    # outside them follow. The site offsets are the model's too.
    _x1,_y1 = exit_site(DRAIN_BUILDINGS[0]); _x2,_y2 = exit_site(DRAIN_BUILDINGS[1])
    _sp=c.beginPath(); _sp.moveTo(p.X(_x1),p.Y(_y1))
    for _x,_y in [(_x1,SAN_CROSS),(SAN_X,SAN_CROSS),(SAN_X,SAN_MAIN_Y)]: _sp.lineTo(p.X(_x),p.Y(_y))
    c.drawPath(_sp,fill=0,stroke=1)
    _sb=c.beginPath(); _sb.moveTo(p.X(_x2),p.Y(_y2)); _sb.lineTo(p.X(SAN_X),p.Y(_y2))
    c.drawPath(_sb,fill=0,stroke=1)
    # The main. It runs in the alley, off the lot: the sheet has 12 pt of margin below the
    # rear line, so the label goes to the right-hand end of the line rather than under it.
    c.setLineWidth(1.5); c.setDash(8,3.5)
    c.line(p.X(-4.0),p.Y(SAN_MAIN_Y),p.X(40.0),p.Y(SAN_MAIN_Y))
    c.setDash()
    _CO=[(_x1,_y1+1.0),(SAN_X,SAN_CROSS),(SAN_X,_y2),(SAN_X,115.0)]
    c.setLineWidth(0.7)
    for _cx,_cy in _CO:
        c.setFillColor(white); c.circle(p.X(_cx),p.Y(_cy),0.55*sc,fill=1,stroke=1)
    c.setFillColor(black); c.setFont("Helvetica",3.2)
    for _cx,_cy in _CO: c.drawCentredString(p.X(_cx),p.Y(_cy)-1.2,"CO")
    c.setFont("Helvetica",5.0)
    c.saveState(); c.translate(p.X(3.0),p.Y(88.0)); c.rotate(90)
    c.drawCentredString(0,0,"4\" BUILDING SEWER TO THE ALLEY MAIN"); c.restoreState()
    p.note(41.0,126.95,"PUBLIC ALLEY  —  REAR   ·   %s RIGHT-OF-WAY   ·   8\" SANITARY SEWER"%fmt(ALLEY_W),
           7.5,anchor="l",bold=True)
    # The alley's width, dimensioned. Its far right-of-way line is 17'-6" past the rear lot
    # line and the sheet has 12 pt there, so the string is a stub continuing the 126'-0"
    # depth string at x -6: the run from the rear lot line toward the far line, a break
    # where the drawing area ends, and the figure beside it, clear of the sewer main that
    # crosses the alley at SAN_MAIN_Y. C-102 draws the whole alley; this is the same ALLEY_W.
    _ax, _ay1 = -6.0, SITE_D+(oy-Y0)/sc-0.1        # as far as the drawing area allows
    assert _ay1 < SITE_D+ALLEY_W, "C-101 has room for the whole alley; draw it as C-102 does"
    c.setStrokeColor(black); c.setLineWidth(0.5); c.setFillColor(black)
    c.line(p.X(_ax),p.Y(SITE_D),p.X(_ax),p.Y(_ay1))
    c.line(p.X(_ax)-2.5,p.Y(_ay1)+2.5,p.X(_ax)+2.5,p.Y(_ay1)-0.5)   # the break
    c.setFont("Helvetica",4.6)
    c.drawRightString(p.X(_ax)-3,p.Y(_ay1)+0.5,"%s ALLEY R.O.W."%fmt(ALLEY_W))
    p.dim(0,40,'h',-2.0); p.dim(0,126,'v',-6.0)          # outboard of the new Sage walk
    for (a,b,t) in SITE_BANDS:
        p.dim(a,b,'v',42.5,t)
    p.note(20,-3.4,"S ELM AVENUE",9.5,bold=True)
    p.note(3.4,44,fmt(SAFF_WALL_X),6); p.note(37.5,33,fmt(SIDE_PARCEL),6)
    # ---- the RCO 302.1 imaginary line, drawn where src/fsd.py puts it ----
    # It is not the midline any more, so it has to be a LINE on the sheet and not a
    # sentence: the whole design is which side of the courtyard it stands on. The two
    # offsets are DIMENSIONED, outboard on the parcel side where the courtyard is clear,
    # rather than written into the note — a site plan states a distance with a string.
    # The band immediately under Building 1's rear wall already carries the Unit 3 stair
    # tag, centred on that stair and running most of the width of the sheet, so the note
    # keeps the y the old one had: under the line, not over it.
    c.setStrokeColor(black); c.setLineWidth(0.8); c.setDash(9,4)
    c.line(p.X(5.0),p.Y(FSD_LINE_Y),p.X(37.0),p.Y(FSD_LINE_Y))
    c.setDash()
    p.dim(B1_REAR_Y,FSD_LINE_Y,'v',35.6)                 # 3'-0" to Building 1's rear wall
    p.dim(FSD_LINE_Y,B2_COURT_Y,'v',35.6)                # 9'-0" to Building 2's courtyard face
    # The stair's edge to the line, and the minimum it is holding, past the landing's
    # parcel-side end where the courtyard has nothing else in it.
    p.dim(FSD_LINE_Y,U5_STOOP.y0,'v',33.0,
          "%s  (%s MIN)"%(fmt(U5_STOOP.y0-FSD_LINE_Y),fmt(rco_fsd.PROJ_FREE)),sd=-1)
    # Clear of the line itself: at 71.4 the dashes strike through the type. The band
    # between the line and the Units 4 / 5 walk at 73.5 is the only empty one here.
    p.note(24,72.2,"%s BETWEEN BUILDINGS — RCO 302.1 IMAGINARY LINE"%fmt(fsd.GAP),5.6)
    p.vnote(-9.7,63,"SAGE AVENUE","SIDE STREET",9.5)
    p.vnote(44.4,63,"ADJACENT PARCEL","NOT A STREET",9.5)
    # All exterior service equipment, drawn and marked ONE way. It used to be drawn three
    # ways: a box on the parcel side that did not say whose, a "UNIT 1 METERS" box on the
    # Sage side that named a unit but not a service, and four identical boxes all
    # marked "HP". Now every box carries a mark, and every mark is in note 5c with the
    # service and the units it serves.
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.9)
    for _m,_x,_y,_d,_l,_desc in SVC_EQUIP:
        c.rect(p.X(_x),p.Y(_y+_l),_d*sc,_l*sc,fill=1,stroke=1)
    c.setFillColor(black)
    _tight=[m for m,_x,_y,_d,_l,_ds in SVC_EQUIP
            if pdfmetrics.stringWidth(m,"Helvetica-Bold",4.0) > _l*sc-2]
    assert not _tight, "C-101 service mark does not fit its box: %r"%_tight
    for _m,_x,_y,_d,_l,_desc in SVC_EQUIP:
        c.saveState(); c.translate(p.X(_x+_d/2.0),p.Y(_y+_l/2.0)); c.rotate(90)
        c.setFont("Helvetica-Bold",4.0); c.drawCentredString(0,-1.4,_m); c.restoreState()
    # The screening shrubs beside the equipment, src/exterior.py, note 5f: a circle at the
    # maintained diameter with a small centre ring.
    c.setStrokeColor(black); c.setLineWidth(0.5)
    for _s in X.SHRUBS:
        c.circle(p.X(_s.x),p.Y(_s.y),X.SHRUB_D/2.0*sc,fill=0,stroke=1)
        c.circle(p.X(_s.x),p.Y(_s.y),X.SHRUB_D/8.0*sc,fill=0,stroke=1)
    # No caption for the equipment: each box carries its mark and note 5c lists every mark.
    # The tree's canopy is in the front yard with the landing label. Boxes in site feet.
    def _on_canopy(x0,x1,y0,y1):
        return x0<TREE_X+TREE_R and x1>TREE_X-TREE_R and y0<TREE_Y+TREE_R and y1>TREE_Y-TREE_R
    # Downspouts, each at its gutter's corner with its mark; C-103 gives the splash blocks.
    roofdrain.plan(p, sc, splash=False)
    check_site_clearances()
    check_b1_service()
    check_b2_service()
    # Unit 1's exterior equipment is beside its Sage stair, on the same wall as
    # the panel it serves; it is drawn and marked by the same loop as everything else.
    # The heat pumps take no caption either: five marks captioned beside the two that are
    # in that side yard read as a callout on those two. Note 5c gives HP-1 TO HP-5.
    # The underground run to Building 2 is gone with the feeders it carried: Building 2 is
    # served at Building 2 now, so nothing crosses the rear yard between the two.
    c.setStrokeColor(black)

    # New public sidewalk, full Sage frontage. It sits in the right-of-way, outside
    # the lot line, so it takes no lot area and moves no number in the zoning table. The
    # depth dimension and the street name were pushed outboard of it rather than over it.
    c.setStrokeColor(GREY); c.setLineWidth(0.7); c.setFillColor(white)
    c.rect(p.X(-SITE_WALK),p.Y(SITE_D),SITE_WALK*sc,SITE_D*sc,fill=0,stroke=1)
    _swl="NEW 4'-0\" PUBLIC SIDEWALK  —  FULL 126'-0\" SAGE FRONTAGE, IN THE RIGHT-OF-WAY"
    p.concrete(-SITE_WALK,0.0,0.0,SITE_D,clear=[p.vlabel_box(-1.35,63.0,_swl,"Helvetica",5.0)])
    c.setFillColor(black); c.setFont("Helvetica",5.0)
    c.saveState(); c.translate(p.X(-1.35),p.Y(63.0)); c.rotate(90)
    c.drawCentredString(0,0,_swl)
    c.restoreState()
    # Unit 2's entry is on the LIVE_SIDE wall now, so its landing and walk go to the new
    # public sidewalk on that street rather than down the far side yard. The stoop at the
    # foot of the Unit 3 stair connects to the rear yard and the parking.
    #
    # The 3'-0" side walk down the adjacent-parcel yard is deleted with the entry it
    # served: that yard is 6'-0" wide and also carries the meter bank, the heat pumps and
    # the underground branch to Building 2, and nothing now has to reach a door down it.
    _u2_ly = 20.0+PLAN_L1.y(U2_ENTRY[1])            # site y of the Unit 2 door's near jamb
    _u2_lw = 3.0                                    # landing, 3'-0" square, at the threshold
    _u2_lc = _u2_ly+U2_ENTRY[2]/2.0-_u2_lw/2.0      # centred on the door
    _walk_x0, _walk_x1 = sorted((SITE_LIVE_X, 0.0)) # landing face out to the lot line
    c.setStrokeColor(GREY); c.setLineWidth(0.7); c.setFillColor(white)
    # 3'-0" walk from the public sidewalk to the landing, and the landing at the door.
    c.rect(p.X(_walk_x0),p.Y(_u2_lc+_u2_lw),(_walk_x1-_walk_x0-_u2_lw)*sc,_u2_lw*sc,fill=0,stroke=1)
    _u2l="3'-0\" WALK AND LANDING — UNIT 2 ENTRY"
    # No elevation label on the landing: note 5a gives its drop and step, and in plan the
    # pad sits under the Unit 3 top landing, so any label beside it lands on the stair.
    p.concrete(_walk_x0,_u2_lc,_walk_x1-_u2_lw,_u2_lc+_u2_lw,
               clear=[p.vlabel_box(_walk_x0+1.5,_u2_lc-1.0,_u2l,"Helvetica",5.0)])
    c.setStrokeColor(black); c.setLineWidth(0.9)
    c.rect(p.X(_walk_x1-_u2_lw),p.Y(_u2_lc+_u2_lw),_u2_lw*sc,_u2_lw*sc,fill=0,stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica",5.0); c.saveState(); c.translate(p.X(_walk_x0+1.5),p.Y(_u2_lc-1.0)); c.rotate(90)
    c.drawCentredString(0,0,_u2l); c.restoreState()
    # The Unit 3 stoop is what reaches the rear yard and the parking now that the side
    # walk down the far yard is gone. A 3'-0" walk carries on from it to the stalls.
    _sw0=SITE_STAIR[0]+0.25
    c.setStrokeColor(GREY); c.setLineWidth(0.7)
    c.rect(p.X(_sw0),p.Y(108.0),3.0*sc,(108.0-(20.0+U3_STOOP_HI))*sc,fill=0,stroke=1)
    _u3l="3'-0\" WALK  —  UNIT 3 STOOP TO THE REAR YARD AND PARKING"
    p.concrete(_sw0,20.0+U3_STOOP_HI,_sw0+3.0,108.0,clear=[p.vlabel_box(_sw0+1.5,92.0,_u3l,"Helvetica",5.0)])
    c.setFillColor(black); c.setFont("Helvetica",5.0)
    c.saveState(); c.translate(p.X(_sw0+1.5),p.Y(92.0)); c.rotate(90)
    c.drawCentredString(0,0,_u3l); c.restoreState()
    c.setStrokeColor(black)
    # Unit 4's landing at its courtyard door, under the top landing and out to its edge, so
    # it is dashed; its step lands on the Units 4 and 5 walk drawn with the stair. Unit 5's
    # own landing is the stoop at the foot of its stair.
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setFillColor(white); c.setDash(2.5,2)
    _u4_lx, _u4_lx1 = 8.0+_u4[0], 8.0+_u4[2]
    _u4_ly0, _u4_ly1 = 80.0+_u4[1], 80.0+_u4[3]
    c.rect(p.X(_u4_lx),p.Y(_u4_ly1),(_u4_lx1-_u4_lx)*sc,(_u4_ly1-_u4_ly0)*sc,fill=0,stroke=1)
    c.setDash()
    # The label names the landing and its size, along the face by out from it. A bare
    # "UNIT 4" on the pad reads as the name of the square, and the square is under the
    # Unit 5 landing, so the label is set out beside the landing's far end at the pad's
    # depth. Two lines, because the landing ends close enough to the interior lot line
    # that one line runs past it.
    c.setFillColor(black); c.setFont("Helvetica",4.2)
    _u4lx, _u4ly = _u5x(U5_LAND_X1)+0.4, (_u4_ly0+_u4_ly1)/2.0
    _u4size = "%s x %s LANDING" % (fmt(_u4_lx1-_u4_lx), fmt(_u4_ly1-_u4_ly0))
    for _u4l,_dy in ((_u4size,1.3),("UNIT 4 ENTRY BELOW",-3.9)):   # centred on the pad
        assert _u4lx+pdfmetrics.stringWidth(_u4l,"Helvetica",4.2)/sc <= SITE_W, \
            "C-101 Unit 4 landing label runs past the interior side lot line"
        c.drawString(p.X(_u4lx),p.Y(_u4ly)+_dy,_u4l)
    c.setStrokeColor(black)
    c.setStrokeColor(GREY); c.setLineWidth(0.7)
    c.rect(p.X(8+ENTRY_LEFT),p.Y(17.0),3.0*sc,17.0*sc,fill=0,stroke=1)          # walk, sidewalk to landing
    p.concrete(8+ENTRY_LEFT,0.0,8+ENTRY_LEFT+3.0,17.0)
    c.setStrokeColor(black); c.setLineWidth(0.9)
    c.rect(p.X(8+ENTRY_LEFT),p.Y(20.0),3.0*sc,3.0*sc,fill=0,stroke=1)           # landing at the door
    # Same for Unit 1: the landing carries its size and whose door it serves. It goes in
    # the front lawn because 3'-0" at 1/8" is 27 pt and no such label fits inside the box.
    c.setFillColor(black); c.setFont("Helvetica",4.6)
    _u1l="3'-0\" x 3'-0\" LANDING — UNIT 1 ENTRY"
    _u1lx, _u1ly = 8+ENTRY_LEFT+3.4, 18.5+1.6/sc    # centred on the box it labels
    _u1lw = pdfmetrics.stringWidth(_u1l,"Helvetica",4.6)/sc
    assert not _on_canopy(_u1lx,_u1lx+_u1lw,_u1ly-4.6/sc,_u1ly), \
        "C-101 Unit 1 landing label prints across the tree canopy"
    c.drawString(p.X(_u1lx),p.Y(_u1ly),_u1l)
    c.setFont("Helvetica",5.0); c.saveState(); c.translate(p.X(8+ENTRY_LEFT+3.6),p.Y(6.0)); c.rotate(90)
    c.drawCentredString(0,0,"3'-0\" FRONT WALK TO UNIT 1"); c.restoreState()
    # One tree, C.C. 3321.07. Front yard on the adjacent-parcel side, 9'-6" off that lot
    # line and 10'-0" back from the front line, across the lawn from the Unit 1 front walk.
    c.setStrokeColor(black); c.setLineWidth(0.7); c.setFillColor(white)
    c.circle(p.X(TREE_X),p.Y(TREE_Y),TREE_R*sc,fill=0,stroke=1)
    c.setFillColor(black); c.circle(p.X(TREE_X),p.Y(TREE_Y),0.45*sc,fill=1,stroke=1)
    # label above the canopy, on the S Elm side of it
    c.setFont("Helvetica",4.6); c.drawCentredString(p.X(TREE_X),p.Y(5.6),"TREE — C.C. 3321.07")
    # True north is 14 degrees clockwise from sheet-left, toward the S Elm corner.
    # The artwork's native north is up, so rotate it 76 degrees counterclockwise.
    # On the plan, over the parking stall at the adjacent-parcel end — the one stall the
    # parking label and the clear vision triangle leave open. The artwork is transparent,
    # so the stall lines read through it. Its letters sit on its axes, half the artwork's
    # side from the centre, and that radius is what is held inside the bay and the lot and
    # clear of the label and every service box.
    _plw=pdfmetrics.stringWidth(_plab,"Helvetica",6.4)/sc
    def _compass_clear(x0,y0,x1,y1):
        dx=max(x0-_ccx,0.0,_ccx-x1); dy=max(y0-_ccy,0.0,_ccy-y1)
        return dx*dx+dy*dy >= _cr*_cr
    assert PARK_Y0<=_ccy-_cr and _ccy+_cr<=PARK_Y1 and _ccx+_cr<=SITE_W, \
        "C-101 compass runs out of the parking bay"
    assert _compass_clear(_plx-_plw/2,_ply-6.4/sc,_plx+_plw/2,_ply), \
        "C-101 compass prints over the parking label"
    assert all(_compass_clear(_x,_y,_x+_d,_y+_l) for _m,_x,_y,_d,_l,_s in SVC_EQUIP), \
        "C-101 compass prints over a service box"
    nx,ny=p.X(_ccx),p.Y(_ccy)
    c.saveState(); c.translate(nx,ny); c.rotate(76)
    c.drawImage(assets.image("compass.png"),-_compass_size/2,-_compass_size/2,
                width=_compass_size,height=_compass_size,mask="auto",preserveAspectRatio=True)
    c.restoreState()
    # zoning table
    tx=X1-4.9*inch; ty=Y1-2.2*inch
    ty=table(c,tx,ty,"ZONING COMPLIANCE — COLUMBUS R-4",zoning_rows(),3.6*inch,
             size=8,lead=0.165*inch,title_size=9.5,gap=0.22*inch)
    ty-=0.06*inch
    ty=draw_runs(tx,ty,zoning_relief(),7.2,0.135*inch,RELIEF_W,"C-101 zoning relief")
    # Site notes go in the empty field between the plan and the zoning table. They cannot
    # go on the plan: 126 ft at 1/8" leaves 54 pt of margin for both streets together.
    # Under the orientation note, which grew when Building 1 turned round.
    snx,sny=X0+7.6*inch,Y1-2.7*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold",9.5)
    c.drawString(snx,sny,"SITE UTILITIES, SIDEWALK AND LANDSCAPING")
    c.setLineWidth(0.7); c.line(snx,sny-4,snx+6.4*inch,sny-4); sny-=0.24*inch
    c.setFont("Helvetica",7.0)
    # These notes are hand-wrapped, and the column has a table hard against its right edge:
    # one line 30 characters long overran it and printed through the zoning table's
    # "Interior side yard" row. Nothing was measuring it. SNW is the ruled width of the
    # heading above, so the check and the drawn rule cannot drift apart.
    SNW=6.4*inch
    _sewer = sewer()          # P-101's figures for the building sewer, quoted in notes 4a and 4b
    # Note 5a states one stoop size and one stoop height for both stairs, read from the
    # stairs as drawn: Unit 3's across its Sage projection and along its run, Unit 5's
    # along the courtyard face and out from it.
    _u3_stoop = (U3_STAIR_W, U3_STOOP_HI-U3_FLIGHT_HI)
    _u5_stoop = (U5_FLIGHT_X0-U5_STOOP_X0, U5_LAND_D)
    assert all(abs(a-b) < 1e-9 for a, b in zip(_u3_stoop, _u5_stoop)) and abs(U3_STOOP_Z-U5_STOOP_Z) < 1e-9, \
        "C-101 note 5a gives one stoop for both stairs: Unit 3 %r at %r, Unit 5 %r at %r" % (_u3_stoop, U3_STOOP_Z, _u5_stoop, U5_STOOP_Z)
    # A-001 note 5 names the walls the Unit 4 bedrooms' escape openings are on (it was
    # this sheet's note 2c until 2026-09-16); the model fact is held here, beside the pad.
    _side = sorted({o[2] for o in b2_openings() if o[0].startswith("BEDROOM") and o[1] == "A" and o[2] != "REAR"})
    assert _side == ["ADJACENT-PARCEL", "SAGE"], "A-001 note 5: the Unit 4 bedrooms' side-wall W-As are on %r" % _side
    # Note 2 says the alley triangle is clear. The two things on the Sage side that
    # could reach it — HP-1 and the Unit 3 stair at its stoop — are held short of it here
    # (they used to be recited in the note).
    assert SITE_D-VISION-max(e[2]+e[4] for e in SVC_SAFFORD) > 0, "HP-1 reaches the alley clear vision triangle"
    assert SITE_D-(20.0+U3_STOOP_HI) > 0, "the Unit 3 stoop reaches the alley clear vision triangle"
    SNOTES=[
     "1.  NEW PUBLIC SIDEWALK — 4'-0\" WIDE, THE FULL 126'-0\" SAGE FRONTAGE, IN THE RIGHT-OF-WAY OUTSIDE THE",
     "     LOT LINE. CONCRETE ON COMPACTED SUBGRADE PER THE CITY OF COLUMBUS STANDARD DRAWING. PERMIT AND",
     "     INSPECTION BY THE DEPARTMENT OF PUBLIC SERVICE, SEPARATE FROM THE BUILDING PERMIT.",
     # The 10'-0" triangle. What could reach it is measured above, not recited here.
     f"2.  CLEAR VISION TRIANGLE — {fmt(VISION)} x {fmt(VISION)} AT THE SAGE / ALLEY CORNER, MEASURED ALONG THE TWO",
     f"     RIGHT-OF-WAY LINES FROM THEIR INTERSECTION, C.C. 3321.05(B)(1). THE PARKING PAD STANDS {fmt(PARK_SETBACK)} OFF THE",
     "     SAGE LINE, CLEAR OF IT. NO FENCE, WALL, HEDGE, SIGN, PLANTING, EQUIPMENT OR STRUCTURE STANDS IN IT.",
     f"2a. CLEAR VISION TRIANGLE — {fmt(VISION_ST)} x {fmt(VISION_ST)} AT THE S ELM / SAGE CORNER, MEASURED ALONG THE TWO",
     f"     RIGHT-OF-WAY LINES FROM THEIR INTERSECTION, C.C. 3321.05(B)(2). BUILDING 1'S S ELM / SAGE CORNER STANDS {fmt(VISION_ST_IN)}",
     f"     INSIDE THE HYPOTENUSE ALONG EACH RIGHT-OF-WAY, {VISION_ST_AREA:.0f} SF OF FOOTPRINT; {fmt(VISION_ST_CLR)} x {fmt(VISION_ST_CLR)} IS CLEAR — VARIANCE REQUEST {REQ_NO['C.C. 3321.05(B)(2)']}.",
     # The pad, the setback it keeps, and the alley it backs to.
     f"2b. PARKING — {PARK_N} SPACES @ {fmt(PARK_PITCH)} x {fmt(PARK_D)} IN THE REAR YARD, BACKING TO THE PUBLIC ALLEY, WHOSE RIGHT-OF-WAY IS",
     f"     {fmt(ALLEY_W)} WIDE, LOT LINE TO LOT LINE. THE PAD STANDS {fmt(PARK_SETBACK)} OFF THE SAGE RIGHT-OF-WAY, THE NORTH LOT LINE, OUTSIDE",
     f"     THE {fmt(PARK_SETBACK_REQ)} PARKING SETBACK LINE OF C.C. 3312.27 AND CLEAR OF THE ALLEY TRIANGLE. THE STALLS BACK INTO THAT {fmt(ALLEY_W)}",
     f"     RIGHT-OF-WAY, WHERE C.C. 3312.25 REQUIRES {fmt(MANEUVER)} OF MANEUVERING — VARIANCE REQUEST {REQ_NO['C.C. 3312.25']}.",
     f"2c. WHEEL STOPS — ONE PRECAST CONCRETE STOP IN EACH STALL, {fmt(WSTOP_L)} LONG, NOT LESS THAN {inches(WSTOP_H)} HIGH, PINNED TO",
     f"     THE PAD WITH TWO STEEL PINS, CENTERED ON THE STALL, ITS NEAR FACE {fmt(WSTOP_SET)} OFF BUILDING 2'S REAR WALL, C.C. 3312.45.",
     # The basis every yard on this sheet is drawn to, and the one figure that has to
     # clear its minimum once the wall is clad. Both are read from the model; a plan
     # review asked how the side yards related to framing, sheathing and the wall face.
     "2d. SETBACKS — EVERY BUILDING LINE AND YARD ON THIS SHEET IS DIMENSIONED TO THE FACE OF STUD, G-001 NOTE 5.",
     f"     SHEATHING, THE WEATHER-RESISTIVE BARRIER AND SIDING STAND OUTSIDE THAT FACE, SO THE {fmt(SIDE_PARCEL)} INTERIOR SIDE",
     f"     YARD IS {fmt(SIDE_FACE)} AT THE FINISHED WALL, OVER THE {fmt(SIDE_MIN)} OF RCO TABLE 302.1(1). SET EACH FOUNDATION",
     "     SO THE FINISHED WALL HOLDS THE YARD. ROOF OVERHANGS AND GUTTERS PROJECT PAST IT, C.C. 3332.28(B).",
     "3.  TREE — ONE TREE ON THE LOT, C.C. 3321.07(B): ONE PER TEN DWELLING UNITS. IN THE S ELM FRONT YARD ON",
     f"     THE ADJACENT-PARCEL SIDE, {fmt(SITE_W-TREE_X)} OFF THE INTERIOR SIDE LOT LINE AND {fmt(TREE_Y)} BACK FROM THE FRONT LINE.",
     "     MINIMUM SIZE AT PLANTING, C.C. 3321.13(C): 2\" CALIPER DECIDUOUS, 1-1/2\" CALIPER ORNAMENTAL, 4'-0\" EVERGREEN.",
     "4.  SANITARY — 8\" SANITARY SEWER IN THE PUBLIC ALLEY AT THE REAR. ONE 4\" BUILDING SEWER SERVES BOTH",
     "     BUILDINGS: IT LEAVES BUILDING 1 AT THE REAR WALL, TURNS DOWN THE SAGE SIDE IN THE 2'-0\" STRIP",
     "     BESIDE THE PARKING BAY, 1'-0\" OFF THE SAGE LOT LINE, TAKES BUILDING 2'S DRAIN IN THE SAME TRENCH",
     "     AND CROSSES THE REAR LOT LINE TO THE MAIN. NO CLEANOUT FALLS UNDER A WALK OR A STOOP.",
     f"4a. SIZE — {total_dfu()} DRAINAGE FIXTURE UNITS FOR BOTH BUILDINGS, OPC TABLE 709.1, TALLIED ON P-101 (UNITS 4 AND 5",
     f"     ARE DRAWN WITHOUT A DISHWASHER). A 4\" DRAIN AT 1/8\" PER FOOT CARRIES {T710_1_1['4'][DRAIN_SLOPES.index(1/8.0)]}, OPC TABLE 710.1(1).",
     "     IT MATCHES THE 4\" AT THE FOOT OF EVERY STACK ON P-601.",
     f"4b. FALL — THE RUN IS {fmt(_sewer['on_lot'])} ON THE LOT AND ABOUT {fmt(_sewer['to_main'])} TO THE MAIN; AT THE 1/8\" PER FOOT MINIMUM THAT",
     f"     IS {inches(_sewer['fall'])} OF FALL, WHICH PUTS THE MAIN'S INVERT AT OR BELOW {inches(-_sewer['main_max'])} BELOW FINISHED GRADE. VERIFY THE MAIN'S",
     "     SIZE, LOCATION AND INVERT BEFORE EITHER SLAB IS POURED — IT SETS THE DEPTH OF EVERY DRAIN ON P-101.",
     "4c. CLEANOUTS — FOUR: WHERE BUILDING 1'S DRAIN LEAVES THE BUILDING, AT THE BEND INTO THE SIDE YARD, AT",
     "     BUILDING 2'S JUNCTION AND SHORT OF THE REAR LOT LINE, RCO P3005.2. ALL FOUR SIT IN THE 2'-0\" STRIP",
     "     OR THE SIDE YARD — NONE IN A PARKING SPACE, NONE IN EITHER VISION TRIANGLE.",
     "4d. VERIFY WITH THE COLUMBUS SEWER PERMIT DESK, 614-645-7490 (P-601 NOTE 5), WHETHER ONE TAP MAY SERVE",
     "     BOTH BUILDINGS BEFORE UNDER-SLAB WORK. SET THE SAGE SIDEWALK AND THE UNIT 2, PARKING AND",
     "     COURTYARD WALKS AFTER THE TRENCH IS BACKFILLED AND COMPACTED.",
     f"4e. DOWNSPOUTS — {roofdrain.DS.DOWNSPOUTS[0].mark} TO {roofdrain.DS.DOWNSPOUTS[-1].mark}, ONE PER EAVE GUTTER, DRAWN AT THEIR CORNERS. SPLASH BLOCKS,",
     "     RECEIVERS AND SIZES ARE ON C-103 NOTE 7. NO LEADER CONNECTS TO THE BUILDING SEWER, C.C. 1145.84.",
     "5.  WALKS AND ENTRIES — ALL THREE BUILDING 1 ENTRIES ARE ON A PUBLIC STREET. UNIT 1 ENTERS FROM S ELM.",
     f"     UNIT 2 HAS A 3'-0\" x 3'-0\" LANDING AT ITS {LIVE_SIDE} DOOR AND A 3'-0\" WALK TO THE NEW PUBLIC SIDEWALK;",
     "     UNIT 3 ENTERS OFF ITS STAIR ON THE SAME FACE, AND ITS STOOP CARRIES A 3'-0\" WALK BACK TO THE REAR YARD",
     f"     AND THE PARKING. NO WALK RUNS IN THE ADJACENT-PARCEL YARD; ITS {fmt(SIDE_PARCEL)} CARRIES BUILDING 1'S",
     f"     METER BANK AND TWO OF ITS HEAT PUMPS. UNITS 4 AND 5 ENTER FROM THE COURTYARD: A {fmt(G.U45_WALK.y1-G.U45_WALK.y0)}",
     f"     WALK RUNS BESIDE THE UNIT 5 STAIR, OUTSIDE ITS {fmt(U5_LAND_D)} PROJECTION, FROM UNIT 4'S LANDING AND THE UNIT 5",
     "     STOOP TO THE UNIT 3 WALK. NO WALK RUNS UNDER THE FLIGHT.",
     f"5a. LANDINGS, RCO 311.3 — 3'-0\" x 3'-0\" AT THE UNIT 1 AND 2 DOORS, {fmt(G.U4_LANDING.x1-G.U4_LANDING.x0)} x {fmt(G.U4_LANDING.y1-G.U4_LANDING.y0)} AT UNIT 4'S. EACH IS A POURED PAD WITH ITS TOP",
     f"     {inches(U2_LANDING_DROP)} MAX BELOW THE THRESHOLD, WITHIN THE {inches(U2_LANDING_MAX)} LIMIT OF RCO 311.3.1, AND ONE STEP DOWN TO THE WALK — NOT A",
     f"     SLAB AT GRADE. UNIT 1: 3'-0\" x 3'-0\" LANDING ONLY. UNITS 3 AND 5 LAND AT THE FOOT OF THEIR STAIRS ON {fmt(_u3_stoop[0])} x {fmt(_u3_stoop[1])} CONCRETE",
     f"     STOOPS, TOP {fmt_in(U3_STOOP_Z)} ABOVE FINISHED GRADE, WITH ONE {fmt_in(U3_STOOP_Z)} STEP DOWN TO GRADE.",
     "5b. HEAT PUMPS — ONE OUTDOOR UNIT PER DWELLING UNIT, ALL FIVE WALL-BRACKETED, 4\" MINIMUM ABOVE GRADE, EACH",
     "     ON A WALL OF THE BUILDING IT SERVES: HP-1 ON BUILDING 1'S SAGE WALL BESIDE THE UNIT 1 STAIR, HP-2 AND",
     "     HP-3 ON ITS ADJACENT-PARCEL WALL WITHIN UNITS 2 AND 3'S OWN LENGTH OF IT, HP-4 AND HP-5 ON BUILDING 2'S",
     f"     ADJACENT-PARCEL WALL. HOLD {fmt(HP_WIN_CLR)} FROM EVERY EGRESS WINDOW AND {fmt(ODU_TERM_CLR)} ALONG THE WALL FROM ANY",
     "     DRYER CAP, M-101 NOTE 8. NO LINE SET CROSSES W4 — A-001 NOTE 19. NO GRADE-MOUNTED PAD.",
     "5c. SERVICE EQUIPMENT —",
     *["     %-5s %s."%(m,d) for m,_x,_y,_dp,_l,d in SVC_EQUIP if not m.startswith("HP-")],
     "     %s TO %s  HEAT-PUMP OUTDOOR UNIT, ONE PER DWELLING UNIT, NUMBERED BY THE UNIT IT SERVES."
       %(SVC_HP_MARKS[0],SVC_HP_MARKS[-1]),
     "     ONE UTILITY SERVICE PER BUILDING, ONE METER PER ACCOUNT. EM-1 IS A FOUR-POSITION BANK — UNITS 1, 2",
     "     AND 3 AND THE BUILDING 1 HOUSE METER — ON UNIT 1'S LENGTH OF THE PARCEL WALL, JUST AHEAD OF THE TYPE W4",
     "     SEPARATION. UNIT 1'S FEEDER ENTERS ITS OWN WALL; UNITS 2 AND 3'S RUN IN CONDUIT ON THE EXTERIOR FACE",
     "     PAST THE W4 LINE INTO THEIR OWN LENGTH OF WALL, A-001 NOTE 4.",
     "5d. BUILDING 2 SHALL HAVE ITS OWN ELECTRIC SERVICE AT EM-3, ON ITS OWN WALL, NEC 225.30 TO 225.32. NO FEEDER",
     "     OR HOUSE CIRCUIT SHALL RUN BETWEEN THE BUILDINGS. EM-3 IS A THREE-POSITION BANK — UNITS 4 AND 5 AND THE",
     "     BUILDING 2 HOUSE METER. THE HOUSE METER FEEDS THE COMMON SITE LIGHTING; EACH UNIT'S OWN ENTRY AND STAIR",
     "     LIGHTS ARE ON ITS PANEL, SWITCHED FROM INSIDE THE UNIT.",
     "     COORDINATE BOTH SERVICES, THE BANKS AND THEIR METER POSITIONS WITH AEP OHIO BEFORE ROUGH-IN.",
     f"5e. THE RCO 302.1 IMAGINARY LINE — {fmt(fsd.GAP)} BETWEEN THE BUILDINGS, THE LINE DRAWN {fmt(fsd.OFF_B1)} OFF BUILDING 1'S REAR",
     f"     WALL AND {fmt(fsd.OFF_B2)} OFF BUILDING 2'S COURTYARD FACE, BOTH DIMENSIONED. THE UNIT 5 STAIR PROJECTS {fmt(U5_LAND_D)} AND",
     f"     LEAVES {fmt(fsd.U5_CLEAR)} TO THE LINE WHERE RCO TABLE 302.1(1) ASKS {fmt(rco_fsd.PROJ_FREE)}. NO PART OF THAT STAIR — GUARD, CANOPY",
     f"     FASCIA OR STRINGER — SHALL PROJECT PAST {fmt(fsd.PROJ_MAX)} FROM THE COURTYARD FACE. BUILDING 1'S REAR WALL",
     f"     STANDS {fmt(fsd.OFF_B1)} FROM THE LINE AND IS TYPE W1R FOR ITS FULL HEIGHT, GABLE INCLUDED; SEE A-601 AND A-102.",
     f"     ITS RAKE SHALL PROJECT NO MORE THAN {inches(_REAR_RAKE)} TO THE OUTSIDE OF THE TRIM, LEAVING {fmt(fsd.OFF_B1-_REAR_RAKE)}; S-103 NOTE 5.",
     f"5f. SCREEN SHRUBS, THE {len(X.SHRUBS)} CIRCLES BESIDE THE SERVICE EQUIPMENT — {X.SHRUB_SPECIES}, MAINTAINED {fmt(X.SHRUB_D)} ACROSS AND",
     f"     {fmt(X.SHRUB_H_MAX)} HIGH. PLANT BESIDE THE EQUIPMENT, NEVER IN FRONT OF IT: {fmt(X.BOX_CLEAR['EM'][0])} CLEAR IN FRONT OF A METER BANK,",
     f"     {fmt(X.BOX_CLEAR['HP'][0])} IN FRONT OF AND {fmt(X.BOX_CLEAR['HP'][1])} EACH SIDE OF AN OUTDOOR UNIT; NONE IN FRONT OF A LEVEL 1 EGRESS WINDOW OR",
     f"     A DOOR, OR WITHIN {fmt(X.CAP_CLR)} OF A DRYER OR RANGE HOOD CAP. OMIT A SHRUB WHERE THESE CLEARANCES CANNOT BE KEPT.",
    ]
    _over=[t for t in SNOTES if pdfmetrics.stringWidth(t,"Helvetica",7.0)>SNW]
    assert not _over, "C-101 note line overruns the column into the zoning table: %r"%_over[:1]
    for t in SNOTES:
        c.drawString(snx,sny,t); sny-=0.135*inch
    # The notes column shares the sheet with the zoning table above it and ends above the
    # sheet border. Note 5c added nine lines; measure it rather than hoping.
    assert sny >= Y0+0.10*inch, ("C-101 notes column overruns the sheet by %.2f in"
                                 %((Y0+0.10*inch-sny)/inch))

    TTX,TTY = X0+7.6*inch, Y1-0.9*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold",12); c.drawString(TTX,TTY,"SITE PLAN")
    c.setFont("Helvetica",9); c.drawString(TTX,TTY-0.18*inch,"SCALE: 1/8\" = 1'-0\"")
    c.setLineWidth(1.2); c.line(TTX,TTY+0.20*inch,TTX+2.6*inch,TTY+0.20*inch)
    c.setFont("Helvetica",7.2)
    # The set's one orientation statement: G-001 no longer carries one and C-103
    # points here. The compass and the NORTH LOT LINE label carry the true directions.
    c.drawString(TTX,TTY-0.52*inch,"ORIENTATION: S ELM AVENUE IS AT THE TOP OF THIS SHEET; SAGE")
    c.drawString(TTX,TTY-0.68*inch,"AVENUE ON THE LEFT, THE ADJACENT PARCEL ON THE RIGHT, THE ALLEY")
    c.drawString(TTX,TTY-0.84*inch,"AT THE REAR. C-102 IS DRAWN TRUE NORTH UP.")
    c.showPage()

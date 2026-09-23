"""A-301 — building sections and the unit stacking diagram.

Both sections are LONGITUDINAL, front to rear along the ridge, which runs that way on both
roofs: x is feet from the building's front face. Building 1's is cut through the stair at
the north wall, so it shows the flight, the well and the headroom under the well's far
edge, all from src/building1.py's b1_stair(). Building 2's shows the rated floor F1 between
Units 2 and 3 on its bearing wall, and the Unit 3 stair's landing end-on at the courtyard
face. Every height is src/levels.py's.
"""
from lib.draw.page import GREY, POCHE, Sheet
from lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src import levels
from src.building1 import B1_D, B1_W, PLAN_B1_L2, Y_FOOT_RISER, Y_TOP_RISER, Y_WELL, b1_stair
from src.building2 import B2_D, B2_W, U45_BEARING_WALL, U5_LAND_D
from src.foundation import FROST_DEPTH, FTG_PROJ, FTG_T, FTG_W, SLAB_T, WALL_T
from lib.model.regrid import PARTITION
from src.roof import B1_ROOF, B2_ROOF, rake
from lib.draw.kit import datum_labels
from lib.draw.kit import Q, X0, Y1, c
from src.sheets.g001 import UNITS, gross_sf
from src.stairs import B1_STAIR

STAIR = b1_stair()
ROOF_EDGE = 5.0/12.0         # sheathing and shingles over the top chord, as the section shows the roof


def _in(v):
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


def _unit(n):
    u = next(u for u in UNITS if u[0] == str(n))
    return "%s · %s SF" % (u[3].replace(" / ", " / "), "{:,.0f}".format(gross_sf(u)))


def sheet_a301():
    sh=Sheet(c,"A-301","Building sections and stacking","1/4\" = 1'-0\""); sh.frame()
    GR,SL,FF2,PL2 = levels.GRADE,levels.FF1,levels.FF2,levels.ROOF_PLATE

    def section(ox,oy,L,span,title,rakes,body,plates,sc=Q):
        ridge=levels.ridge(span)
        Xp=lambda v: ox+v*sc; Yp=lambda v: oy+v*sc
        def floor_band(a,b,mark):
            plate=getattr(levels,mark+'_PLATE'); ceiling=getattr(levels,mark+'_CEILING'); gypsum=getattr(levels,mark+'_GYPSUM')
            bands=[(plate,levels.SUBFLOOR_TOP-levels.SUBFLOOR,POCHE),
                   (levels.SUBFLOOR_TOP-levels.SUBFLOOR,levels.SUBFLOOR_TOP,POCHE),
                   (levels.SUBFLOOR_TOP,levels.FF2,white),(ceiling,ceiling+gypsum,white)]
            if mark=='F1': bands.append((ceiling+gypsum,plate,white))
            c.setStrokeColor(black); c.setLineWidth(.3)
            for lo,hi,color in bands:
                c.setFillColor(color); c.rect(Xp(a),Yp(lo),(b-a)*sc,(hi-lo)*sc,fill=1,stroke=1)
        c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(1.3)
        c.rect(Xp(0),Yp(SL),L*sc,(PL2-SL)*sc,fill=1,stroke=1)
        c.rect(Xp(0),Yp(PL2),L*sc,(ridge-PL2)*sc,fill=1,stroke=1)
        c.rect(Xp(-rakes[0]),Yp(ridge),(L+rakes[0]+rakes[1])*sc,ROOF_EDGE*sc,fill=1,stroke=1)   # the roof at the ridge, past each gable by its rake
        c.setFillColor(POCHE); c.setLineWidth(0.8)
        c.rect(Xp(0),Yp(levels.SLAB_TOP-SLAB_T),L*sc,SLAB_T*sc,fill=1,stroke=1)
        for _x in (0.0, L-WALL_T):                      # the foundation wall and footing at each end, S-101
            c.rect(Xp(_x),Yp(-(FROST_DEPTH-FTG_T)),WALL_T*sc,(levels.SLAB_TOP+FROST_DEPTH-FTG_T)*sc,fill=1,stroke=1)
            c.rect(Xp(_x-FTG_PROJ),Yp(-FROST_DEPTH),FTG_W*sc,FTG_T*sc,fill=1,stroke=1)
        c.setFillColor(white); c.setLineWidth(.3)
        c.rect(Xp(0),Yp(levels.SLAB_TOP),L*sc,levels.FLOOR_FINISH*sc,fill=1,stroke=1)
        c.rect(Xp(0),Yp(levels.UPPER_CEILING),L*sc,levels.UPPER_GYPSUM*sc,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica",6)
        c.drawString(Xp(L)+0.62*sc,Yp(-1.4),"%s FROST DEPTH — CIC-09" % inches(FROST_DEPTH))
        c.setStrokeColor(black); c.setLineWidth(1.8); c.line(Xp(-4.5),Yp(GR),Xp(L+1.5),Yp(GR))
        body(Xp,Yp,floor_band,sc)
        c.setStrokeColor(black); c.setLineWidth(0.4); c.setFont("Helvetica",6.2); c.setFillColor(black)
        datum_labels(Xp,Yp,L,[(GR,"GRADE  0'-0\""),(SL,"FIN. FLOOR L1  +%s"%fmt(SL)),
                             (levels.SLAB_TOP,"SLAB TOP  +%s"%fmt(levels.SLAB_TOP))]
                             +[(getattr(levels,m+'_PLATE'),"%s TOP PLATE  +%s"%(m,fmt(getattr(levels,m+'_PLATE')))) for m in plates]
                             +[(FF2,"FIN. FLOOR L2  +%s"%fmt(FF2)),(PL2,"ROOF PLATE  +%s"%fmt(PL2)),
                               (levels.EAVE,"EAVE, TOP OF HEEL  +%s"%fmt(levels.EAVE)),(ridge,"NOM. RIDGE  +%s"%fmt(ridge))])
        c.setFont("Helvetica-Bold",10); c.drawString(ox,oy-1.10*inch,title)
        c.setFont("Helvetica",8); c.drawString(ox,oy-1.26*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.0); c.line(ox,oy-0.88*inch,ox+2.4*inch,oy-0.88*inch)

    def room_label(Xp,Yp,x,z0,z1,t1,t2):
        c.setFillColor(black); c.setFont("Helvetica-Bold",9); c.drawCentredString(Xp(x),Yp((z0+z1)/2)+4,t1)
        c.setFont("Helvetica",6.8); c.drawCentredString(Xp(x),Yp((z0+z1)/2)-6,t2)

    def house(Xp,Yp,floor_band,sc):
        s = B1_STAIR
        edge = PLAN_B1_L2.y(Y_WELL-PARTITION)                  # the well's far edge, over the low treads
        floor_band(0.0, Y_TOP_RISER, 'F2'); floor_band(edge, B1_D, 'F2')
        c.setStrokeColor(GREY); c.setLineWidth(0.5)
        for i in range(s.treads+1):                            # the flight, rising toward the front wall
            x = Y_FOOT_RISER-i*s.tread; z = SL+(i+1)*s.riser
            c.line(Xp(x),Yp(z-s.riser),Xp(x),Yp(z))
            if i < s.treads: c.line(Xp(x+1/12.0),Yp(z),Xp(x-s.tread),Yp(z))
        k = -(-(Y_FOOT_RISER-edge)//s.tread)                    # risers climbed under that edge, as b1_stair() counts
        nz = SL+k*s.riser; hz = levels.F2_CEILING
        assert abs((hz-nz)-STAIR['headroom']) < 1e-6 or STAIR['headroom'] <= hz-nz+1e-6, "A-301 draws a headroom b1_stair() does not give"
        c.setStrokeColor(black); c.setLineWidth(.35)
        c.line(Xp(edge),Yp(nz),Xp(edge),Yp(hz))
        for z in (nz,hz): c.line(Xp(edge)-3,Yp(z)-2,Xp(edge)+3,Yp(z)+2)
        c.saveState(); c.translate(Xp(edge)+7,Yp((nz+hz)/2)); c.rotate(90)
        c.setFillColor(black); c.setFont("Helvetica",6)
        c.drawCentredString(0,0,"%s HEADROOM; 6'-8\" MIN, RCO 311.7.2" % fmt(hz-nz)); c.restoreState()
        c.setStrokeColor(GREY); c.setLineWidth(.45)             # the guard wall beside the well, beyond
        c.line(Xp(Y_TOP_RISER),Yp(FF2+3),Xp(edge),Yp(FF2+3))
        for x in (Y_TOP_RISER, edge): c.line(Xp(x),Yp(FF2),Xp(x),Yp(FF2+3))
        c.setFillColor(black); c.setFont("Helvetica",6)
        c.drawCentredString(Xp((Y_TOP_RISER+edge)/2),Yp(FF2+3.4),"36\" GUARD AT THE WELL, RCO 312.1")
        c.drawString(Xp(edge+1),Yp(FF2+.35),"F2: %s FLOOR TRUSSES / %s FLOOR TO FLOOR" % (_in(levels.F2_JOIST), _in(levels.FLOOR_RISE)))
        c.drawCentredString(Xp((Y_TOP_RISER+Y_FOOT_RISER)/2),Yp(SL+1.0),"%dR @ %s, %dT @ %s — A-101" % (s.risers, _in(s.riser), s.treads, _in(s.tread)))
        room_label(Xp,Yp,24.0,SL,levels.F2_CEILING,"UNIT 1 — LEVEL 1",_unit(1)+" · TWO STORIES")
        room_label(Xp,Yp,24.0,FF2,levels.UPPER_CEILING,"UNIT 1 — LEVEL 2","")

    def adu(Xp,Yp,floor_band,sc):
        floor_band(0.0, B2_D, 'F1')
        y0, y1 = U45_BEARING_WALL[1], U45_BEARING_WALL[3]
        c.setFillColor(POCHE); c.setStrokeColor(black); c.setLineWidth(0.6)
        c.rect(Xp(y0),Yp(SL),(y1-y0)*sc,(levels.F1_CEILING-SL)*sc,fill=1,stroke=1)          # W3 under F1
        c.setFillColor(white); c.rect(Xp(y0),Yp(FF2),(y1-y0)*sc,(levels.UPPER_CEILING-FF2)*sc,fill=1,stroke=1)   # the partition over it
        c.setFillColor(black); c.setFont("Helvetica",6)
        c.drawString(Xp(y1)+3,Yp(SL+1.0),"W3 BEARING WALL, 1 HOUR, A-601")
        c.drawString(Xp(y1)+3,Yp(FF2+.35),"F1: 1-HOUR FLOOR-CEILING, RCO 302.3, A-601")
        # the Unit 3 stair's top landing, end-on at the courtyard face
        c.setStrokeColor(black); c.setLineWidth(0.9)
        c.line(Xp(-U5_LAND_D),Yp(FF2),Xp(0),Yp(FF2)); c.line(Xp(-U5_LAND_D),Yp(FF2-10/12.0),Xp(0),Yp(FF2-10/12.0))
        c.line(Xp(-U5_LAND_D),Yp(FF2-10/12.0),Xp(-U5_LAND_D),Yp(FF2+3)); c.line(Xp(-U5_LAND_D),Yp(FF2+3),Xp(-U5_LAND_D+.1),Yp(FF2+3))
        c.setLineWidth(0.5); c.line(Xp(-U5_LAND_D+0.25),Yp(GR),Xp(-U5_LAND_D+0.25),Yp(FF2-10/12.0))
        c.setFont("Helvetica",6); c.drawRightString(Xp(-U5_LAND_D)-3,Yp(FF2+1.2),"UNIT 3 STAIR")
        c.drawRightString(Xp(-U5_LAND_D)-3,Yp(FF2+0.5),"LANDING, A-603")
        room_label(Xp,Yp,23.0,SL,levels.F1_CEILING,"UNIT 2",_unit(2))
        room_label(Xp,Yp,23.0,FF2,levels.UPPER_CEILING,"UNIT 3",_unit(3))

    sx=X0+1.2*inch
    section(sx, Y1-7.0*inch, B1_D, B1_W, "BUILDING 1 — LONGITUDINAL SECTION AT THE STAIR, LOOKING SOUTH",
            (rake(B1_ROOF,'OAK AVENUE'), rake(B1_ROOF,'REAR')), house, ('F2',))
    section(sx, Y1-15.0*inch, B2_D, B2_W, "BUILDING 2 — LONGITUDINAL SECTION, LOOKING SOUTH",
            (rake(B2_ROOF,'COURTYARD'), rake(B2_ROOF,'REAR')), adu, ('F1',))
    c.setFont("Helvetica",6.4); c.setFillColor(black)
    for oy, a, b in ((Y1-7.0*inch, "OAK AVENUE", "COURTYARD"), (Y1-15.0*inch, "COURTYARD", "PARKING AND ALLEY")):
        yy = oy+(levels.ridge(B1_W)+1.1)*Q                # above the roof, clear of the footings and the datums
        c.drawString(sx, yy, "< "+a); c.drawRightString(sx+B1_D*Q, yy, b+" >")

    # stacking key
    kx=X0+11.7*inch; ky=Y1-5.0*inch
    c.setFont("Helvetica-Bold",12); c.drawString(kx,ky+3.05*inch,"UNIT STACKING DIAGRAM")
    c.setLineWidth(0.9); c.line(kx,ky+2.95*inch,kx+7.4*inch,ky+2.95*inch)
    def keybox(x,y,w,h,t1,t2):
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.1)
        c.rect(x,y,w,h,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold",10); c.drawCentredString(x+w/2,y+h/2+3,t1)
        c.setFont("Helvetica",7.2); c.drawCentredString(x+w/2,y+h/2-9,t2)
    U=1.05*inch
    c.setFont("Helvetica-Bold",9); c.drawString(kx,ky+2.80*inch,"BUILDING 1  \u2014  %s x %s  \u2014  1 UNIT" % (fmt(B1_W), fmt(B1_D)))
    keybox(kx, ky+1.0*inch, 3.2*inch, 1.5*U, "UNIT 1", _unit(1)+" · TWO STORIES")
    kx2=kx+4.1*inch
    c.setFont("Helvetica-Bold",9); c.drawString(kx2,ky+2.80*inch,"BUILDING 2  \u2014  %s x %s  \u2014  2 UNITS" % (fmt(B2_W), fmt(B2_D)))
    keybox(kx2, ky+1.0*inch+0.75*U, 3.2*inch, 0.75*U, "UNIT 3", _unit(3)+" · LEVEL 2")
    keybox(kx2, ky+1.0*inch, 3.2*inch, 0.75*U, "UNIT 2", _unit(2)+" · LEVEL 1")
    c.setFont("Helvetica",6.6); c.setFillColor(black)
    c.drawCentredString(kx2+1.6*inch, ky+1.0*inch+0.75*U-9, "1-HOUR FLOOR F1, RCO 302.3")
    c.drawString(kx, ky+0.72*inch, "OAK AVENUE  ·  THE HOUSE, DETACHED")
    c.drawString(kx2, ky+0.72*inch, "TWO STACKED ADUs, C.C. 3332.355")

    hx=X0+11.7*inch; hy=Y1-9.6*inch
    c.setFillColor(black); c.setStrokeColor(black); c.setFont("Helvetica-Bold",10)
    c.drawString(hx,hy,"HEIGHT SCHEDULE — FINISHED DATUMS / TOP OF BEARING PLATES")
    hy-=.14*inch; c.setLineWidth(.7); c.line(hx,hy,hx+7.4*inch,hy); hy-=.22*inch
    cols=[0,2.2,4.0,5.6]
    c.setFont("Helvetica-Bold",7.5)
    for pos,label in zip(cols,("DIMENSION","UNIT 1 LEVEL 1 / F2","UNIT 2 / F1","ALL UPPER LEVELS")):
        c.drawString(hx+pos*inch,hy,label)
    hy-=.18*inch; c.setFont("Helvetica",7.5)
    for label,values,elevation in [
        ("FINISHED FLOOR",(levels.FF1,levels.FF1,levels.FF2),True),
        ("TOP BEARING PLATE",(levels.F2_PLATE,levels.F1_PLATE,levels.ROOF_PLATE),True),
        ("FINISHED CEILING",(levels.F2_CEILING,levels.F1_CEILING,levels.UPPER_CEILING),True),
        ("FLOOR TO PLATE",(levels.F2_PLATE-levels.FF1,levels.F1_PLATE-levels.FF1,levels.ROOF_PLATE-levels.FF2),False),
        ("FLOOR ASSEMBLY DEPTH",(levels.F2_DEPTH,levels.F1_DEPTH,None),False),
        ("CLEAR CEILING HEIGHT",(levels.F2_CEILING-levels.FF1,levels.F1_CEILING-levels.FF1,levels.UPPER_CEILING-levels.FF2),False)]:
        c.drawString(hx,hy,label)
        for pos,val in zip(cols[1:],values):
            c.drawString(hx+pos*inch,hy,"—" if val is None else ('+' if elevation else '')+fmt(val))
        hy-=.16*inch
    hy-=.06*inch
    # The arithmetic that showed the two floors landing on one Level 2 came off on
    # 2026-09-16: the schedule carries the figures and A-202 states the plate step. The
    # figures are still one derivation (src/levels.py), so they cannot disagree.
    assert abs((levels.F2_PLATE+levels.F2_DEPTH+levels.FLOOR_FINISH)-levels.FF2) < 1e-9 and \
           abs((levels.F1_PLATE+levels.F1_DEPTH+levels.FLOOR_FINISH)-levels.FF2) < 1e-9, \
        "A-301: the two floors no longer land on one Level 2"
    c.setFont("Helvetica",7)
    for t in ("1/4\" FLOOR FINISH INCLUDED. F1 CEILING: RESILIENT CHANNELS AND %d LAYER %s %s, %s, A-601."
              % (levels.F1_LAYERS, _in(levels.F1_LAYER), levels.F1_BOARD, levels.F1_LISTING),
              "TRUSS BOTTOM-CHORD UNDERSIDE AT THE ROOF PLATE, S-103.",
              "UNIT 1 STAIR HEADROOM: %s AS DRAWN; 80\" RCO 311.7.2 MINIMUM." % fmt(STAIR['headroom'])):
        c.drawString(hx,hy-.05*inch,t); hy-=.15*inch
    c.showPage()

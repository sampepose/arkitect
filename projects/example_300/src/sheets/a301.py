"""A-301 — building sections and the unit-stacking diagram."""
from arkitect.lib.draw.page import GREY, POCHE, Sheet
from src.partywall import W4_CORE, W4_FACE, W4_STUD
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src import levels
from src.building1 import Y_SEP_BOT, Y_SEP_TOP
from src.foundation import FROST_DEPTH, FTG_PROJ, FTG_T, FTG_W, SLAB_T, WALL_T
from src.building2 import B2_W
from src.roof import B1_ROOF, B2_ROOF, rake
from src.building1 import HEADROOM_LABEL, U1_HEADER_FACE, U1_NOSING, U1_RISER, U1_STAIR_BOT_Y, U1_STAIR_TOP_Y, U1_TREAD, U1_TREADS, U1_WELL_EDGE_Y, U1_WELL_Y, u1_nosing_height
import math
from arkitect.lib.draw.kit import datum_labels
from arkitect.lib.draw.kit import Q, X0, Y1, c



def _in(v):
    """Inches as the notes write them: 5/8", 14-5/8" — inches() without its "0-"."""
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


ROOF_EDGE = 5.0/12.0         # sheathing and shingles over the top chord, as the section shows the roof


# ============================= A-301 SECTION AND STACKING =============================
def sheet_a301():
    sh=Sheet(c,"A-301","Building sections and stacking","1/4\" = 1'-0\""); sh.frame()
    def section(ox,oy,L,split,units,title,rakes,sc=Q,roof_span=26):
        GR,SL,FF2,PL2 = levels.GRADE,levels.FF1,levels.FF2,levels.ROOF_PLATE
        ridge=levels.ridge(roof_span)
        Xp=lambda v: ox+v*sc; Yp=lambda v: oy+v*sc
        def floor_band(a,b,mark):
            plate=getattr(levels,mark+'_PLATE')
            ceiling=getattr(levels,mark+'_CEILING')
            gypsum=getattr(levels,mark+'_GYPSUM')
            bands=[(plate,levels.SUBFLOOR_TOP-levels.SUBFLOOR,POCHE),
                   (levels.SUBFLOOR_TOP-levels.SUBFLOOR,levels.SUBFLOOR_TOP,POCHE),
                   (levels.SUBFLOOR_TOP,levels.FF2,white),
                   (ceiling,ceiling+gypsum,white)]
            if mark=='F1': bands.append((ceiling+gypsum,plate,white))
            c.setStrokeColor(black); c.setLineWidth(.3)
            for lo,hi,color in bands:
                c.setFillColor(color)
                c.rect(Xp(a),Yp(lo),(b-a)*sc,(hi-lo)*sc,fill=1,stroke=1)
        c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(1.3)
        c.rect(Xp(0),Yp(SL),L*sc,(PL2-SL)*sc,fill=1,stroke=1)
        c.rect(Xp(0),Yp(PL2),L*sc,(ridge-PL2)*sc,fill=1,stroke=1)
        # The roof at the ridge, past each gable by its rake, S-103 note 5; W4 is drawn
        # over it below, to the deck.
        c.rect(Xp(-rakes[0]),Yp(ridge),(L+rakes[0]+rakes[1])*sc,ROOF_EDGE*sc,fill=1,stroke=1)
        c.setFillColor(POCHE); c.setStrokeColor(black); c.setLineWidth(0.8)
        # The slab inside its foundation wall, and the trench footing under the wall at
        # each end, S-101. The 32" label beside it is the footing's bottom.
        c.rect(Xp(0),Yp(levels.SLAB_TOP-SLAB_T),L*sc,SLAB_T*sc,fill=1,stroke=1)
        for _x in (0.0, L-WALL_T):
            c.rect(Xp(_x),Yp(-(FROST_DEPTH-FTG_T)),WALL_T*sc,(levels.SLAB_TOP+FROST_DEPTH-FTG_T)*sc,fill=1,stroke=1)
            c.rect(Xp(_x-FTG_PROJ),Yp(-FROST_DEPTH),FTG_W*sc,FTG_T*sc,fill=1,stroke=1)
        c.setFillColor(white); c.setLineWidth(.3)
        c.rect(Xp(0),Yp(levels.SLAB_TOP),L*sc,levels.FLOOR_FINISH*sc,fill=1,stroke=1)
        # Upper ceiling board beneath the truss bottom chord / roof-bearing datum.
        c.rect(Xp(0),Yp(levels.UPPER_CEILING),L*sc,levels.UPPER_GYPSUM*sc,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica",6)
        c.drawString(Xp(L)+0.62*sc,Yp(-1.4),"32\" FROST DEPTH — CIC-09")
        c.setStrokeColor(black); c.setLineWidth(1.8); c.line(Xp(-1.5),Yp(GR),Xp(L+1.5),Yp(GR))
        for (a,bnd,lvl,lab,sub) in units:
            c.setStrokeColor(GREY); c.setLineWidth(0.5)
            if lvl=="both":
                y0,y1=SL,PL2
                # Unit 1's F2 floor is within the dwelling, at the shared Level 2
                # datum, and includes its straight stair on the Sage side.
                for fa,fb in ((a,U1_WELL_Y),(U1_STAIR_TOP_Y,bnd)):
                    floor_band(fa,fb,'F2')
                sx0=U1_STAIR_BOT_Y
                for i in range(U1_TREADS):
                    sx=sx0+i*U1_TREAD; z=SL+(i+1)*U1_RISER
                    c.line(Xp(sx),Yp(z-8/12.0),Xp(sx),Yp(z))
                    c.line(Xp(sx-U1_NOSING),Yp(z),Xp(sx+(U1_TREAD if i<U1_TREADS-1 else 0)),Yp(z))
                # Finished header face and vertical headroom to the nosing line.
                hx=U1_WELL_EDGE_Y
                hz=levels.F2_CEILING
                nz=SL+u1_nosing_height(U1_WELL_EDGE_Y)
                c.setFillColor(white); c.setLineWidth(.35)
                c.rect(Xp(U1_WELL_Y),Yp(hz),U1_HEADER_FACE*sc,(FF2-hz)*sc,fill=1,stroke=1)
                c.line(Xp(hx),Yp(nz),Xp(hx),Yp(hz))
                for z in (nz,hz): c.line(Xp(hx)-3,Yp(z)-2,Xp(hx)+3,Yp(z)+2)
                c.saveState(); c.translate(Xp(hx)-5,Yp((nz+hz)/2)); c.rotate(90)
                c.setFillColor(black); c.setFont("Helvetica",6)
                c.drawCentredString(0,0,HEADROOM_LABEL+" CALCULATED / 84\" DESIGN MIN")
                c.restoreState()
                # Hall-side guard projected in section; it does not cross stair entry.
                ga=U1_WELL_Y; gb=U1_STAIR_TOP_Y
                c.setStrokeColor(GREY); c.setLineWidth(.45)
                c.line(Xp(ga),Yp(FF2+3),Xp(gb),Yp(FF2+3))
                bays=math.ceil((gb-ga)*12/4)
                for i in range(bays+1):
                    gx=ga+(gb-ga)*i/bays
                    c.line(Xp(gx),Yp(FF2),Xp(gx),Yp(FF2+3))
                c.setFillColor(black); c.setFont("Helvetica",6)
                c.drawCentredString(Xp((ga+gb)/2),Yp(FF2+3.45),"36\" HIGH HALL-SIDE GUARD; RCO 312.1")
                c.setStrokeColor(black)
                c.setFillColor(black); c.setFont("Helvetica",6.0)
                c.drawString(Xp(1),Yp(FF2+.35),"F2: 14\" I-JOISTS / 120\" FLOOR TO FLOOR")
                c.drawString(Xp(1),Yp(levels.F2_CEILING)-10,"F2 TOP PLATE +%s"%fmt(levels.F2_PLATE))
                c.setFont("Helvetica-Bold",8)
                c.drawCentredString(Xp((a+bnd)/2),Yp(15.5),"UNIT 1 — UPPER LEVEL")
                y0,y1=SL,levels.F2_CEILING
            elif lvl=="L1":
                y0,y1=SL,levels.F1_CEILING
                floor_band(a,bnd,'F1')
            else:
                y0,y1=FF2,levels.UPPER_CEILING
            c.setFillColor(black); c.setFont("Helvetica-Bold",9)
            label_x=4.5 if lvl=="both" else (a+bnd)/2
            c.drawCentredString(Xp(label_x),Yp((y0+y1)/2)+4,lab)
            c.setFont("Helvetica",6.8); c.drawCentredString(Xp(label_x),Yp((y0+y1)/2)-6,sub)
        if split:
            c.setFillColor(POCHE); c.setStrokeColor(black); c.setLineWidth(0.9)
            # W4A and W4B: each wall's stud row poche, with its inner layer at the joint
            # and its own unit face; the two inner layers touch on the centreline.
            half=W4_CORE/2.0
            for x0 in (split-half-W4_STUD,split+half):
                c.rect(Xp(x0),Yp(levels.SLAB_TOP),W4_STUD*sc,(ridge-levels.SLAB_TOP)*sc,fill=1,stroke=1)
            c.setFillColor(white); c.setLineWidth(.3)
            for x0,w in ((split-half,half),(split,half),
                         (split-half-W4_STUD-W4_FACE,W4_FACE),(split+half+W4_STUD,W4_FACE)):
                c.rect(Xp(x0),Yp(levels.SLAB_TOP),w*sc,(ridge-levels.SLAB_TOP)*sc,fill=1,stroke=1)
            wf1=split-half-W4_STUD-W4_FACE; wf2=split+half+W4_STUD+W4_FACE
            c.setLineWidth(3); c.line(Xp(wf1-4),Yp(ridge)+2,Xp(wf2+4),Yp(ridge)+2)
            c.setLineWidth(.4); c.setFillColor(black); c.setFont("Helvetica",6)
            for a,b in ((wf1-4,wf1),(wf2,wf2+4)):
                c.line(Xp(a),Yp(ridge+1),Xp(b),Yp(ridge+1))
                for v in (a,b): c.line(Xp(v),Yp(ridge+.8),Xp(v),Yp(ridge+1.2))
                c.drawCentredString(Xp((a+b)/2),Yp(ridge+1.2),"4'-0\" MIN")
            c.setFillColor(black); c.setStrokeColor(black); c.setLineWidth(0.4)
            c.line(Xp(wf2+4),Yp(ridge),Xp(split+6),Yp(ridge+2.2))
            c.setFont("Helvetica",6.4)
            for i,t in enumerate(("W4A / W4B — TWO UL U305 WALLS, 1 HOUR EACH; SEE A-601",
                                  "FRT ROOF SHEATHING / NO OPENINGS IN 4'-0\" BANDS",
                                  "CLASS C MINIMUM ROOF; RCO 302.2.4 EXCEPTION")):
                c.drawString(Xp(split+6.2),Yp(ridge+2.2)-i*9,t)
        c.setStrokeColor(black); c.setLineWidth(0.4); c.setFont("Helvetica",6.2); c.setFillColor(black)
        datum_labels(Xp,Yp,L,[(GR,"GRADE  0'-0\""),(SL,"FIN. FLOOR L1  +%s"%fmt(SL)),
                             (levels.SLAB_TOP,"SLAB TOP  +%s"%fmt(levels.SLAB_TOP)),
                             (levels.F1_PLATE,"F1 TOP PLATE  +%s"%fmt(levels.F1_PLATE)),
                             (FF2,"FIN. FLOOR L2  +%s"%fmt(FF2)),(PL2,"ROOF PLATE  +%s"%fmt(PL2)),
                             (ridge,"NOM. RIDGE  +%s"%fmt(ridge))])
        c.setFont("Helvetica-Bold",10); c.drawString(ox,oy-1.10*inch,title)
        c.setFont("Helvetica",8); c.drawString(ox,oy-1.26*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.0); c.line(ox,oy-0.88*inch,ox+2.4*inch,oy-0.88*inch)

    section(X0+0.4*inch, Y1-7.0*inch, 48, (Y_SEP_TOP+Y_SEP_BOT)/2,
      [(0,Y_SEP_TOP-W4_FACE,"both","UNIT 1","4BR / 2BA · TWO STORIES · 1,248 SF"),
       (Y_SEP_BOT+W4_FACE,48,"L1","UNIT 2","2BR / 1BA · 624 SF"),
       (Y_SEP_BOT+W4_FACE,48,"L2","UNIT 3","2BR / 1BA · 624 SF")],
      "BUILDING 1 — LONGITUDINAL SECTION", (rake(B1_ROOF,'S ELM AVENUE'), rake(B1_ROOF,'REAR')))
    c.setFont("Helvetica",6.4); c.setFillColor(black)
    c.drawString(X0+14.4*inch, Y1-7.0*inch+10.2*Q, "1-HOUR FLOOR TYPE F1")
    c.drawString(X0+14.4*inch, Y1-7.0*inch+9.5*Q, "WITHIN THE GROUPING, RCO 302.2")
    section(X0+0.4*inch, Y1-15.0*inch, 28, None,
      [(0,28,"L1","UNIT 4","2BR / 1BA · 728 SF"),
       (0,28,"L2","UNIT 5","2BR / 1BA · 728 SF")],
      "BUILDING 2 — LONGITUDINAL SECTION", (rake(B2_ROOF,'COURTYARD'), rake(B2_ROOF,'REAR')), roof_span=B2_W)
    c.setFont("Helvetica",6.4)
    c.drawString(X0+0.4*inch+14*Q, Y1-15.0*inch+(levels.FF2+.5)*Q, "F1: 1-HOUR FLOOR / RCO 302.3")

    # stacking key
    kx=X0+10.0*inch; ky=Y1-13.2*inch
    c.setFont("Helvetica-Bold",12); c.drawString(kx,ky+3.05*inch,"UNIT STACKING DIAGRAM")
    c.setLineWidth(0.9); c.line(kx,ky+2.95*inch,kx+9.0*inch,ky+2.95*inch)
    def keybox(x,y,w,h,t1,t2,hatch=False):
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.1)
        c.rect(x,y,w,h,fill=1,stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold",10)
        c.drawCentredString(x+w/2,y+h/2+3,t1)
        c.setFont("Helvetica",7.2); c.drawCentredString(x+w/2,y+h/2-9,t2)
    U=1.05*inch
    c.setFont("Helvetica-Bold",9); c.drawString(kx,ky+2.80*inch,"BUILDING 1  \u2014  26 x 48 FT  \u2014  3 UNITS")
    keybox(kx, ky+1.0*inch, 2.6*inch, 1.5*U, "UNIT 1","4BR / 2BA · 1,248 SF · TWO STORIES")
    keybox(kx+2.66*inch, ky+1.0*inch+0.75*U, 2.6*inch, 0.75*U, "UNIT 3","2BR · 624 SF · LEVEL 2")
    keybox(kx+2.66*inch, ky+1.0*inch, 2.6*inch, 0.75*U, "UNIT 2","2BR · 624 SF · LEVEL 1")
    c.setFont("Helvetica",6.6); c.setFillColor(black)
    c.drawCentredString(kx+2.63*inch, ky+1.0*inch+1.53*U+4, "TWO 1-HOUR WALLS, W4A / W4B  (RCO 302.2)")
    c.drawCentredString(kx+3.96*inch, ky+1.0*inch+0.75*U-9, "1-HOUR FLOOR")
    c.drawString(kx, ky+0.72*inch, "FRONT OF LOT / PRIMARY STREET")
    c.drawRightString(kx+5.26*inch, ky+0.72*inch, "REAR OF LOT / ALLEY")
    kx2=kx+6.2*inch
    c.setFont("Helvetica-Bold",9); c.drawString(kx2,ky+2.80*inch,"BUILDING 2  \u2014  26 x 28 FT  \u2014  2 UNITS")
    keybox(kx2, ky+1.0*inch+0.75*U, 2.6*inch, 0.75*U, "UNIT 5","2BR · 728 SF · LEVEL 2")
    keybox(kx2, ky+1.0*inch, 2.6*inch, 0.75*U, "UNIT 4","2BR · 728 SF · LEVEL 1")
    c.setFont("Helvetica",6.6)
    c.drawCentredString(kx2+1.3*inch, ky+1.0*inch+0.75*U-9, "1-HOUR FLOOR")
    # One caption; the paragraph that used to explain the diagram came off on 2026-09-16.
    c.setFont("Helvetica",8.4)
    c.drawString(kx, ky+0.35*inch, "FIVE DWELLING UNITS: THREE IN BUILDING 1, TWO IN BUILDING 2, C.C. 3332.355. 1-HOUR F1 FLOORS BETWEEN THE STACKED UNITS.")

    # Moved up to make room for the reconciliation below the schedule; the stacking
    # diagram above ends at Y1-13.36in.
    hx=X0+10*inch; hy=Y1-13.6*inch
    c.setFillColor(black); c.setStrokeColor(black); c.setFont("Helvetica-Bold",10)
    c.drawString(hx,hy,"HEIGHT SCHEDULE — FINISHED DATUMS / TOP OF BEARING PLATES")
    hy-=.14*inch; c.setLineWidth(.7); c.line(hx,hy,hx+8.8*inch,hy); hy-=.22*inch
    cols=[0,2.6,4.6,6.7]
    c.setFont("Helvetica-Bold",7.5)
    for pos,label in zip(cols,("DIMENSION","UNIT 1 L1 / F2","UNITS 2 & 4 / F1","ALL UPPER LEVELS")):
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
    for t in ("1/4\" FLOOR FINISH INCLUDED. F1 CEILING: RC-1 CHANNELS AND %d LAYER %s %s, %s, A-601."
              % (levels.F1_LAYERS, _in(levels.F1_LAYER), levels.F1_BOARD, levels.F1_LISTING),
              "TRUSS BOTTOM-CHORD UNDERSIDE AT ROOF PLATE; SEE A-202. UNIT 1 STAIR HEADROOM: %s CALCULATED; 84\" PROJECT MINIMUM; 80\" RCO 311.7.2 MINIMUM."
              % HEADROOM_LABEL):
        c.drawString(hx,hy-.05*inch,t); hy-=.15*inch
    c.showPage()

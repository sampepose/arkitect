"""A-201, A-202 and A-203 — the eight exterior elevations, and what they are drawn from.

   They share elev() and face(), which is why they share a module: opposite faces of
   a building read in opposite directions, and getting that wrong stays invisible
   until two elevations disagree about which end a window is on. It has happened."""
from arkitect.lib.draw.page import GREY, Sheet
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import IN, fmt, inches
from reportlab.lib.colors import Color, black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.building1 import U1_DR_TERM, U1_DR_TERM_Z, site_y, U23_DR_TERM, U3_FLIGHT_HI, U3_LAND_HI, U3_LAND_LO, U3_RISERS, U3_STAIR_CLR, U3_STAIR_TAG, U3_STOOP_HI, U3_STOOP_Z, U3_TREADS, Y_SEP_BOT, Y_SEP_TOP
from src.faces import DRAWN_BOXES, face_boxes, face_terms
from src.mechanical import U23_DR_CAP_UP, WALLS
from src.building2 import B2_D, B2_W, U5_FLIGHT_X0, U5_LAND_X0, U5_LAND_X1, U5_RISERS, U5_STAIR_CLR, U5_STAIR_TAG, U5_STOOP_X0, U5_STOOP_Z, U5_TREADS
from src import exterior as X, levels
from src.openings import WIN_GEOM
from src.roof import B1_ROOF, B2_ROOF, EAVE_OVERHANG, rake
from src.grading import STOOP_STEP
from src.schedules import B1, B2
from src.sheets import roofdrain
from arkitect.lib.draw.kit import datum_labels, knockout
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c


RY1, RY2 = Y1-6.4*inch, Y1-14.6*inch


LC, RC   = X0+0.35*inch, X0+9.25*inch


FF={1:levels.FF1, 2:levels.FF2}


FASCIA_DROP=1.25/12.0      # the fascia trim below the soffit, S-103 detail 1
ROOF_EDGE=5.0/12.0         # the tail, sheathing and shingles above it, as the edge shows


GEOM=dict(WIN_GEOM)          # sill above floor, height — defined with the marks, above


# Rendering. Every texture is a light grey laid BEHIND the linework, and a label that lands
# on one is knocked out in white (common.knockout), so shading adds depth without taking
# contrast from anything a reviewer reads. Clipping is arithmetic, as S-103's hatching is:
# the recording canvases carry no clip path.
TONE_SIDING = Color(.80,.80,.80)    # lap siding courses
TONE_SHADOW = Color(.91,.91,.91)    # the shadow the eave or the rake throws on the wall
TONE_ROOF   = Color(.87,.87,.87)    # the roof face on an eave elevation, the rake band on a gable
TONE_COURSE = Color(.70,.70,.70)    # shingle courses
TONE_GLASS  = Color(.92,.92,.92)    # glazing
TONE_FOUND  = Color(.93,.93,.93)    # exposed foundation, grade to slab top
TONE_EARTH  = Color(.45,.45,.45)    # the hatch under grade
SIDING_COURSE  = IN(8)       # one line per D4 double course
SHINGLE_COURSE = IN(10)      # as the roof face reads in elevation
SHADOW_D       = IN(9)       # how far below the eave or rake the shadow reaches
EARTH_D        = IN(5)       # depth of the grade hatch
EARTH_PITCH    = 4.0         # points between hatch strokes


def elev(ox,oy,w,ops,title,span,sc=Q,gable=True,terms=(),bearing_runs=None,label_at=None,boxes=(),rakes=None,
         trim=False,accent=None,surround=False):
    GR=levels.GRADE; FF1=levels.FF1; FF2=levels.FF2; PL2=levels.ROOF_PLATE
    EV=levels.EAVE; RG=levels.ridge(span); HT=levels.height(span)
    if bearing_runs is None: bearing_runs=[(0,w,'F1')]
    plates={'F1':levels.F1_PLATE,'F2':levels.F2_PLATE}
    Xp=lambda v: ox+v*sc; Yp=lambda v: oy+v*sc
    c.setStrokeColor(black); c.setLineWidth(1.2); c.setFillColor(white)
    # The wall face runs past the roof plate and up the raised heel to the eave at the wall
    # line, S-103 detail 1. The roof edge stands out past it: the eaves EAVE_OVERHANG each
    # side of a gable face, falling at the pitch to the fascia; on an eave face the roof
    # runs past each end by that end's rake, `rakes` (left, right) as the face is read.
    EO=EAVE_OVERHANG; SOF=EV-EO*levels.ROOF_PITCH       # the soffit at the fascia
    c.rect(Xp(0),Yp(GR),w*sc,(EV-GR)*sc,fill=1,stroke=1)
    c.setFillColor(white)
    def wall_texture():
        """The exposed foundation, the shadow under the eave or the rakes, and the siding
           courses, clipped to the wall and, on a gable face, to the gable."""
        wall_top = EV if gable else SOF-FASCIA_DROP
        c.setFillColor(TONE_FOUND)
        c.rect(Xp(0),Yp(GR),w*sc,(levels.SLAB_TOP-GR)*sc,fill=1,stroke=0)
        c.setFillColor(TONE_SHADOW)
        if gable:
            sp=c.beginPath(); sp.moveTo(Xp(0),Yp(EV)); sp.lineTo(Xp(w/2),Yp(RG)); sp.lineTo(Xp(w),Yp(EV))
            sp.lineTo(Xp(w),Yp(EV-SHADOW_D)); sp.lineTo(Xp(w/2),Yp(RG-SHADOW_D)); sp.lineTo(Xp(0),Yp(EV-SHADOW_D)); sp.close()
            c.drawPath(sp,fill=1,stroke=0)
        else:
            c.rect(Xp(0),Yp(wall_top-SHADOW_D),w*sc,SHADOW_D*sc,fill=1,stroke=0)
        c.setStrokeColor(TONE_SIDING); c.setLineWidth(0.22)
        top = RG if (gable and not accent) else wall_top
        zz = levels.SLAB_TOP+SIDING_COURSE
        while zz < top-1e-9:
            if zz <= wall_top:
                c.line(Xp(0),Yp(zz),Xp(w),Yp(zz))
            else:
                hw=(RG-zz)/(RG-EV)*(w/2.0)
                c.line(Xp(w/2.0-hw),Yp(zz),Xp(w/2.0+hw),Yp(zz))
            zz += SIDING_COURSE
        c.setStrokeColor(black); c.setLineWidth(1.2); c.setFillColor(white)
    if gable:
        pth=c.beginPath(); pth.moveTo(Xp(0),Yp(EV)); pth.lineTo(Xp(w/2),Yp(RG)); pth.lineTo(Xp(w),Yp(EV)); pth.close()
        c.drawPath(pth,fill=1,stroke=1)
        wall_texture()
        pth=c.beginPath(); pth.moveTo(Xp(-EO),Yp(SOF-FASCIA_DROP)); pth.lineTo(Xp(w/2),Yp(RG))
        pth.lineTo(Xp(w+EO),Yp(SOF-FASCIA_DROP)); pth.lineTo(Xp(w+EO),Yp(SOF+ROOF_EDGE))
        pth.lineTo(Xp(w/2),Yp(RG+ROOF_EDGE+FASCIA_DROP)); pth.lineTo(Xp(-EO),Yp(SOF+ROOF_EDGE)); pth.close()
        c.setFillColor(TONE_ROOF)
        c.drawPath(pth,fill=1,stroke=1)                  # the rake and eave edge, both sides
        c.setFillColor(white)
        for a,b in ((-EO,0.0),(w,w+EO)): c.line(Xp(a),Yp(SOF),Xp(b),Yp(SOF))   # the soffits
        if accent:
            # The gable's accent siding, src/exterior.py: its courses, clipped to the gable.
            c.setStrokeColor(GREY); c.setLineWidth(0.35)
            zz=EV+X.SHAKE_COURSE
            while zz < RG-X.SHAKE_COURSE:
                hw=(RG-zz)/(RG-EV)*(w/2.0)
                c.line(Xp(w/2.0-hw),Yp(zz),Xp(w/2.0+hw),Yp(zz)); zz+=X.SHAKE_COURSE
            c.setFillColor(black)
            knockout(Xp(w/2),Yp(EV)+4,accent,"Helvetica",4.8,"c")
            c.setStrokeColor(black)
    else:
        left,right=rakes
        wall_texture()
        c.rect(Xp(-left),Yp(SOF-FASCIA_DROP),(w+left+right)*sc,(RG+ROOF_EDGE-SOF+FASCIA_DROP)*sc,fill=1,stroke=1)
        c.setFillColor(TONE_ROOF)
        c.rect(Xp(-left),Yp(SOF+ROOF_EDGE),(w+left+right)*sc,(RG-SOF)*sc,fill=1,stroke=0)
        c.setStrokeColor(TONE_COURSE); c.setLineWidth(0.3)
        zz=SOF+ROOF_EDGE+SHINGLE_COURSE
        while zz < RG+ROOF_EDGE-1e-9:
            c.line(Xp(-left),Yp(zz),Xp(w+right),Yp(zz)); zz+=SHINGLE_COURSE
        c.setStrokeColor(black); c.setLineWidth(1.2); c.setFillColor(white)
        c.rect(Xp(-left),Yp(SOF-FASCIA_DROP),(w+left+right)*sc,(RG+ROOF_EDGE-SOF+FASCIA_DROP)*sc,fill=0,stroke=1)
        c.line(Xp(-left),Yp(SOF+ROOF_EDGE),Xp(w+right),Yp(SOF+ROOF_EDGE))   # the fascia's top
    c.setStrokeColor(GREY); c.setLineWidth(0.4)
    for lv in (FF1,FF2,PL2): c.line(Xp(-0.6),Yp(lv),Xp(w+0.6),Yp(lv))
    for a,b,mark in bearing_runs:
        c.line(Xp(a),Yp(plates[mark]),Xp(b),Yp(plates[mark]))
    c.setStrokeColor(black); c.setLineWidth(1.6); c.line(Xp(-1.2),Yp(GR),Xp(w+1.2),Yp(GR))
    c.setStrokeColor(TONE_EARTH); c.setLineWidth(0.35)
    hx=Xp(-1.2)+EARTH_D*sc
    while hx <= Xp(w+1.2)+1e-9:
        c.line(hx,Yp(GR),hx-EARTH_D*sc,Yp(GR)-EARTH_D*sc); hx+=EARTH_PITCH
    c.setStrokeColor(black)
    if trim:
        # A street face's trim, src/exterior.py: the frieze under the eave or the soffit, and
        # a corner board at each end up to it.
        fz=(EV if gable else SOF-FASCIA_DROP)
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
        c.rect(Xp(0),Yp(fz-X.FRIEZE),w*sc,X.FRIEZE*sc,fill=1,stroke=1)
        for a in (0.0, w-X.CORNER_BOARD):
            c.rect(Xp(a),Yp(GR),X.CORNER_BOARD*sc,(fz-X.FRIEZE-GR)*sc,fill=1,stroke=1)
    for (x,ww,sill,hh,mk,kind) in ops:
        top=sill+hh; mark_y=Yp(top)+3
        if trim:
            c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.5)
            if kind=="d" and surround:
                P,CH,CE,DC=X.SURROUND_PILASTER,X.SURROUND_CROSSHEAD,X.SURROUND_CAP_EAR,X.DRIP_CAP
                for a in (x-P, x+ww):
                    c.rect(Xp(a),Yp(sill),P*sc,hh*sc,fill=1,stroke=1)
                c.rect(Xp(x-P),Yp(top),(ww+2*P)*sc,CH*sc,fill=1,stroke=1)
                c.rect(Xp(x-P-CE),Yp(top+CH),(ww+2*(P+CE))*sc,DC*sc,fill=1,stroke=1)
                mark_y=Yp(top)+(CH*sc-5.2*0.72)/2.0
            else:
                CW,HC,EAR,DC=X.CASING_W,X.HEAD_CASING,X.HEAD_EAR,X.DRIP_CAP
                bot=sill-CW if kind=="w" else sill
                c.rect(Xp(x-CW),Yp(bot),(ww+2*CW)*sc,(top-bot)*sc,fill=1,stroke=1)
                c.rect(Xp(x-CW-EAR),Yp(top),(ww+2*(CW+EAR))*sc,HC*sc,fill=1,stroke=1)
                c.rect(Xp(x-CW-EAR),Yp(top+HC),(ww+2*(CW+EAR))*sc,DC*sc,fill=1,stroke=1)
                mark_y=Yp(top)+(HC*sc-5.2*0.72)/2.0
        c.setFillColor(TONE_GLASS if kind=="w" else white); c.setStrokeColor(black); c.setLineWidth(0.9)
        c.rect(Xp(x),Yp(sill),ww*sc,hh*sc,fill=1,stroke=1)
        if kind=="w":
            c.setLineWidth(0.5); c.line(Xp(x),Yp(sill+hh/2),Xp(x+ww),Yp(sill+hh/2))
        c.setFillColor(black)
        knockout(Xp(x+ww/2),mark_y,mk,"Helvetica",5.2,"c")   # in the head casing on a trimmed face
    # The equipment standing in front of the face. One meter drawn per position; an
    # outdoor unit shows its fan. Each box states its underside.
    for (x0,x1,z0,z1,mk,n) in boxes:
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.8)
        c.rect(Xp(x0),Yp(z0),(x1-x0)*sc,(z1-z0)*sc,fill=1,stroke=1)
        c.setLineWidth(0.5)
        if n:
            pitch=(x1-x0)/n
            for k in range(n):
                c.circle(Xp(x0+pitch*(k+0.5)),Yp((z0+z1)/2),min(pitch,z1-z0)*sc*0.28,fill=0,stroke=1)
        else:
            c.circle(Xp(x0+(x1-x0)*0.42),Yp((z0+z1)/2),min(x1-x0,z1-z0)*sc*0.36,fill=0,stroke=1)
        c.setFillColor(black)
        knockout(Xp((x0+x1)/2),Yp(z1)+3,mk,"Helvetica-Bold",6.0,"c")
        knockout(Xp((x0+x1)/2),Yp(z0)-6,"U/S +%s"%fmt(z0),"Helvetica",4.8,"c")
    # Draw every specified through-siding termination on the face where it
    # actually occurs. Roof-only vents are intentionally excluded.
    for (tx,tz,lab,tkind) in terms:
        xx,yy=Xp(tx),Yp(tz)
        c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.75)
        if tkind == "dryer":
            c.rect(xx-4.2,yy-3.2,8.4,6.4,fill=1,stroke=1)
            c.line(xx-4.2,yy-3.2,xx+4.2,yy+3.2)
        elif tkind == "exh":
            c.rect(xx-3.6,yy-3.6,7.2,7.2,fill=1,stroke=1)
            c.line(xx-3.6,yy-1.2,xx+3.6,yy-1.2)
        else:
            c.circle(xx,yy,4.0,fill=1,stroke=1)
            c.circle(xx,yy,1.6,fill=0,stroke=1)
        c.setFillColor(black)
        knockout(xx,yy+6.5,lab,"Helvetica-Bold",6.0,"c")
    c.setFillColor(black); c.setFont("Helvetica",6.2)
    la = (w+(EO if gable else rakes[1])) if label_at is None else label_at
    plate_items=[(plates[m],"L1 PLATE / %s   +%s"%(m,fmt(plates[m]))) for m in sorted({r[2] for r in bearing_runs})]
    datum_labels(Xp,Yp,la,[(FF1,"FIN. FLOOR L1   +%s"%fmt(FF1)),(FF2,"FIN. FLOOR L2   +%s"%fmt(FF2)),
                         (PL2,"ROOF PLATE   +%s"%fmt(PL2)),(EV,"EAVE, TOP OF HEEL   +%s"%fmt(EV)),
                         (HT,"HEIGHT, C.C. 3303.08   +%s"%fmt(HT)),(RG,"NOM. RIDGE   +%s"%fmt(RG))]+plate_items,
                 lead_from=w)
    c.drawString(Xp(la)+8,Yp(GR)-11,"GRADE   0'-0\"")
    c.setFont("Helvetica-Bold",10); c.drawString(ox,oy-0.42*inch,title)
    c.setFont("Helvetica",8); c.drawString(ox,oy-0.58*inch,"SCALE: 1/4\" = 1'-0\"")
    if trim:
        c.drawString(ox,oy-0.74*inch,"STREET FACE: FLAT %s TRIM, FRIEZE AND CORNER BOARDS%s — A-202 ELEVATION NOTES"
                     %(X.TRIM_MATERIAL,", DOOR SURROUND" if surround else ""))
    c.setLineWidth(1.0); c.line(ox,oy-0.20*inch,ox+2.0*inch,oy-0.20*inch)


def u3_stair_elev(ox,oy,sc=Q,flip=True):
    """Side elevation of the Unit 3 stair, coordinated with its plan.
       flip is for a face read from the side that reverses the plan's y axis — the
       same flip face() takes below. The Sage face is read unflipped."""
    Xp=lambda v: ox+v*sc; Yp=lambda v: oy+v*sc
    tr=(lambda y: 48.0-y) if flip else (lambda y: y)
    a=tr(U3_LAND_LO); b=tr(U3_LAND_HI)
    d=tr(U3_FLIGHT_HI); e=tr(U3_STOOP_HI)
    dn=1.0 if e>d else -1.0                  # the direction the flight descends in
    top=levels.FF2; bottom=U3_STOOP_Z; rise=(top-bottom)/U3_RISERS
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(1.0)
    c.line(Xp(a),Yp(top),Xp(b),Yp(top))
    # Exact stair profile: 15 equal 8" risers and 14 equal 9-1/4" treads.
    x=b; z=top
    path=c.beginPath(); path.moveTo(Xp(x),Yp(z))
    for i in range(U3_RISERS):
        z-=rise; path.lineTo(Xp(x),Yp(z))
        if i<U3_TREADS:
            x=b+(d-b)*(i+1)/U3_TREADS; path.lineTo(Xp(x),Yp(z))
    c.drawPath(path,fill=0,stroke=1)
    # Six-inch concrete stoop and its one step down to grade.
    c.setLineWidth(1.2)
    c.line(Xp(d),Yp(bottom),Xp(e),Yp(bottom))
    c.line(Xp(e),Yp(bottom),Xp(e),Yp(0))
    c.line(Xp(e),Yp(0),Xp(e+1.5*dn),Yp(0))
    # Guard/handrail and supports. Neither stair's underside is rated: A-601 schedules
    # both as none, and the tag drawn below states each one's distance to its line.
    c.setLineWidth(1.4)
    c.line(Xp(a),Yp(top+3.0),Xp(b),Yp(top+3.0))
    c.line(Xp(b),Yp(top+3.0),Xp(d),Yp(bottom+3.0))
    for xx,zz in ((a,top),(b,top),(d,bottom)):
        c.line(Xp(xx),Yp(zz),Xp(xx),Yp(zz+3.0))
    c.setStrokeColor(GREY); c.setLineWidth(0.8)
    c.line(Xp(b),Yp(top-0.45),Xp(d),Yp(bottom-0.45))
    # Simple shed canopy over the door and full top landing. It sits just above the
    # door head, not at 18'-0" where it used to be drawn — that is 6" BELOW the head.
    clo=min(a,b)-0.5; chi=max(a,b)+0.5; cz=levels.FF2+8.4
    c.setStrokeColor(black); c.setLineWidth(1.0)
    c.line(Xp(clo),Yp(cz-0.2),Xp(chi),Yp(cz))
    c.line(Xp(clo),Yp(cz-0.2),Xp(clo),Yp(cz-0.45))
    c.line(Xp(chi),Yp(cz),Xp(chi),Yp(cz-0.25))
    c.setStrokeColor(black); c.setFillColor(black); c.setFont("Helvetica",5.3)
    put = (lambda x,y,t: knockout(x,y,t,"Helvetica",5.3,"l")) if dn>0 else (lambda x,y,t: knockout(x,y,t,"Helvetica",5.3,"r"))
    back= (lambda x,y,t: knockout(x,y,t,"Helvetica",5.3,"r")) if dn>0 else (lambda x,y,t: knockout(x,y,t,"Helvetica",5.3,"l"))
    put(Xp(b+1.0*dn),Yp(top+3.25),"36\" GUARD · 34–38\" GRASPABLE HANDRAIL")
    # Above the flight, not beside it: descending to the right the tag would otherwise
    # be written straight across the stringer.
    put(Xp(b+2.0*dn),Yp(top+5.1 if dn>0 else 5.1),U3_STAIR_TAG)
    knockout(Xp((clo+chi)/2),Yp(cz+0.25),"CANOPY OVER DOOR / TOP LANDING","Helvetica",5.3,"c")
    # Below the grade line, not above it: the stoop now straddles the rear corner, so a
    # note beside it at stoop height would be written across the building.
    _stx = e-0.2 if dn>0 else e-1.4      # clear of the datum-label column beyond it
    back(Xp(_stx),Yp(-0.75),"CONCRETE STOOP — TOP %s ABOVE FINISHED GRADE"%inches(U3_STOOP_Z))
    back(Xp(_stx),Yp(-1.05),"ONE %s STEP DOWN TO FINISHED GRADE"%inches(STOOP_STEP))


def u5_stair_elev(ox,oy,sc=Q):
    """Unit 5's stair on Building 2's courtyard elevation.

    The openings on this face come from face() in plan coordinates, adjacent parcel at
    the left, which is how someone standing in the courtyard sees it. The stair's
    constants are final SHEET coordinates, Sage at the left, so they are flipped
    here to land the landing over the door they cover on A-103: elevation x is
    B2_W minus sheet x, and the flight descends to the right."""
    Xp=lambda v: ox+(B2_W-v)*sc; Yp=lambda v: oy+v*sc
    a,b = U5_LAND_X1, U5_LAND_X0          # landing, far end to the head of the flight
    d,e = U5_FLIGHT_X0, U5_STOOP_X0       # foot of the flight, then the stoop
    top=levels.FF2; bottom=U5_STOOP_Z; rise=(top-bottom)/U5_RISERS
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(1.0)
    c.line(Xp(a),Yp(top),Xp(b),Yp(top))
    x=b; z=top
    path=c.beginPath(); path.moveTo(Xp(x),Yp(z))
    for i in range(U5_RISERS):
        z-=rise; path.lineTo(Xp(x),Yp(z))
        if i<U5_TREADS:
            x=b+(d-b)*(i+1)/U5_TREADS; path.lineTo(Xp(x),Yp(z))
    c.drawPath(path,fill=0,stroke=1)
    c.setLineWidth(1.2)
    c.line(Xp(d),Yp(bottom),Xp(e),Yp(bottom))
    c.line(Xp(e),Yp(bottom),Xp(e),Yp(0))
    c.line(Xp(e),Yp(0),Xp(e-1.5),Yp(0))
    c.setLineWidth(1.4)
    c.line(Xp(a),Yp(top+3.0),Xp(b),Yp(top+3.0))
    c.line(Xp(b),Yp(top+3.0),Xp(d),Yp(bottom+3.0))
    for xx,zz in ((a,top),(b,top),(d,bottom)):
        c.line(Xp(xx),Yp(zz),Xp(xx),Yp(zz+3.0))
    c.setStrokeColor(GREY); c.setLineWidth(0.8)
    c.line(Xp(b),Yp(top-0.45),Xp(d),Yp(bottom-0.45))
    clo=min(a,b)-0.5; chi=max(a,b)+0.5; cz=levels.FF2+8.4
    c.setStrokeColor(black); c.setLineWidth(1.0)
    c.line(Xp(chi),Yp(cz-0.2),Xp(clo),Yp(cz))
    c.line(Xp(chi),Yp(cz-0.2),Xp(chi),Yp(cz-0.45))
    c.line(Xp(clo),Yp(cz),Xp(clo),Yp(cz-0.25))
    c.setStrokeColor(black); c.setFillColor(black); c.setFont("Helvetica",5.3)
    # the flight now descends to the right, so its labels hang off the head of the
    # flight to the right and the stoop's sit to the left of the stoop
    knockout(Xp(b-1.0),Yp(top+3.25),"36\" GUARD · 34–38\" GRASPABLE HANDRAIL","Helvetica",5.3,"l")
    knockout(Xp((clo+chi)/2),Yp(cz+0.25),"CANOPY OVER DOOR / TOP LANDING","Helvetica",5.3,"c")
    knockout(Xp(e+0.2),Yp(-0.75),"CONCRETE STOOP — TOP %s ABOVE FINISHED GRADE"%inches(U5_STOOP_Z),"Helvetica",5.3,"r")
    knockout(Xp(e+0.2),Yp(-1.05),"ONE %s STEP DOWN TO FINISHED GRADE"%inches(STOOP_STEP),"Helvetica",5.3,"r")
    # Under the stoop's lines, not above the flight: Unit 5's kitchen W-C stands there now.
    knockout(Xp(e+0.2),Yp(-1.35),U5_STAIR_TAG,"Helvetica",5.3,"r")


def face(orient,wall,levels,flip=None):
    """levels = [(level, wins, doors), ...] -> elevation opening list.
       flip = wall length, for the two faces seen from the opposite side. Opposite
       faces of a building read in opposite directions; without this two of the four
       elevations come out mirrored and an opening lands on the wrong end."""
    out=[]
    for (lv,ws,ds) in levels:
        ff=FF[lv]
        for w in ws:
            x,y,ln,o = w[:4]; mk=w[4]
            if o!=orient: continue
            if abs((x if o=='v' else y)-wall)>1e-6: continue
            sill,h = GEOM[mk]
            pos=(y if o=='v' else x)
            out.append((flip-(pos+ln) if flip else pos, ln, ff+sill, h, "W-"+mk, "w"))
        for d in ds:
            if "ext" not in d[5:]: continue
            x,y,ln,o = d[:4]
            if o!=orient: continue
            if abs((x if o=='v' else y)-wall)>1e-6: continue
            pos=(y if o=='v' else x)
            out.append((flip-(pos+ln) if flip else pos, ln, ff, 6.67, "D-1", "d"))
    return out


_KIND = {'DRYER EXHAUST': 'dryer', 'HEATER VENT': 'wh'}


def face_items(bldg, wall, flip=None):
    """(terms, boxes) on a wall as elev() takes them, from src/faces.py, mapped along
       the elevation with the flip face() gives the same wall's openings."""
    X = (lambda a: flip-a) if flip else (lambda a: a)
    terms = [(X(t.along), t.z, t.mark, _KIND.get(t.what, 'exh')) for t in face_terms(bldg, wall)]
    boxes = [(min(X(b.lo), X(b.hi)), max(X(b.lo), X(b.hi)), b.zlo, b.zhi, b.mark, b.positions)
             for b in (face_boxes(bldg, wall) if (bldg, wall) in DRAWN_BOXES else [])]
    return terms, boxes


def placed(typed, bldg, wall, flip=None):
    """A face's typed caps, held to the caps src/mechanical.py places on that wall: a cap
       on a drawn wall that the face does not draw, or draws elsewhere, stops the build."""
    model = sorted(face_items(bldg, wall, flip)[0], key=lambda t: t[2])
    mine = sorted(typed, key=lambda t: t[2])
    assert [t[2:] for t in mine] == [t[2:] for t in model] and all(
        abs(a[0]-b[0]) < 1e-6 and abs(a[1]-b[1]) < 1e-6 for a, b in zip(mine, model)), (
        "%s building %d: drawn caps %s, placed %s" % (wall, bldg, mine, model))
    return typed


# ============================= A-201 ELEVATIONS =============================
def sheet_a201():


    sh=Sheet(c,"A-201","Building 1 — exterior elevations","1/4\" = 1'-0\""); sh.frame()
    # Elevations are generated from the plan window and door lists, so they cannot
    # drift from A-101 / A-102 / A-103. Heads are all at 8'-0" above the floor.


    # The Unit 3 stair stands off whichever side face the mirror put it on, and runs past
    # the rear wall to its stoop. Push that face's datum labels clear of it.
    STAIR_END = U3_STOOP_HI+0.8
    elev(LC, RY1, 48, face('v',26.0-EXT_STUD,B1),
         "BUILDING 1 — SAGE AVENUE ELEVATION",26,gable=False,
         rakes=(rake(B1_ROOF,'S ELM AVENUE'),rake(B1_ROOF,'REAR')),
         bearing_runs=[(0,Y_SEP_TOP,'F2'),(Y_SEP_BOT,48,'F1')],
         label_at=STAIR_END,trim=(1,'SAGE WALL') in X.STREET_FACES,
         terms=placed([(site_y(U1_DR_TERM),U1_DR_TERM_Z,"DR-1","dryer")],
                      1,'SAGE WALL'))
    u3_stair_elev(LC,RY1,flip=False)
    # A face is seen from outside, so its elevation reads the plan's left and right the
    # way someone standing in front of it does. S Elm is at the top of every plan, so
    # an observer on S Elm faces down the sheet and the plan's left hand — Sage —
    # falls on their right; G-001 note 16 says exactly that. The rear observer faces the
    # other way and the plan's left stays on their left. It is the S Elm and rear faces
    # that need opposite treatment from each other, not the two side faces.
    elev(LC, RY2, 26, face('h',EXT_STUD,B1),
         "BUILDING 1 — S ELM AVENUE ELEVATION",26,bearing_runs=[(0,26,'F2')],
         trim=(1,'S ELM WALL') in X.STREET_FACES,accent=X.GABLE_ACCENT.get((B1_ROOF.name,'S ELM AVENUE')),
         surround=True,terms=placed([],1,'S ELM WALL'))
    elev(RC, RY2, 26, face('h',48.0-EXT_STUD,B1,flip=26),
         "BUILDING 1 — REAR ELEVATION  (STAIR TO UNIT 3 NOT SHOWN)",26,
         # Same derived terminal locations the A-202 diagram and note 16d use, flipped
         # onto this face. They were raw model values, about an inch off the openings
         # around them, which are drawn regridded.
         terms=placed([(26-U23_DR_TERM,levels.FF1+U23_DR_CAP_UP,"DR-2","dryer"),
                       (26-U23_DR_TERM,levels.FF2+U23_DR_CAP_UP,"DR-3","dryer")],
                      1,'REAR WALL'))
    # The rear wall's rating, under its own elevation. It is the only face of either
    # building that Table 302.1(1) rates, and it is rated for where it STANDS rather than
    # for what it carries, so the reason goes on the face: A-601 alone would leave a
    # reviewer wondering why this gable is 1 hour and the other three are not.
    c.setFont("Helvetica",7.2); c.setFillColor(black)
    # Under the title AND under elev()'s "SCALE: 1/4" = 1'-0"" line, which sits at -0.58.
    c.drawString(RC,RY2-0.74*inch,"W1R — 1 HOUR, FULL HEIGHT INCLUDING THE GABLE. SEE A-601.")
    # Roof drainage, src/downspouts.py. The Sage gutter falls the length of its eave to
    # DS-1, which turns the rear corner and comes down the rear face; on the rear elevation
    # elevation x is site x less the Sage face, so the corner is at 0.
    _ds1 = next(d for d in roofdrain.DS.DOWNSPOUTS if d.eave.face == roofdrain.G.F_B1_SAFF)
    assert _ds1.face == roofdrain.G.F_B1_REAR, "A-201 draws %s on the rear elevation; the model has moved it" % _ds1.mark
    roofdrain.gutter(lambda v: LC+v*Q, lambda v: RY1+v*Q, -rake(B1_ROOF,'S ELM AVENUE'), 48.0+rake(B1_ROOF,'REAR'),
                     "EAVE GUTTER — FALLS TO %s ON THE REAR FACE" % _ds1.mark, 40.0)
    roofdrain.elevation(lambda v: RC+v*Q, lambda v: RY2+v*Q, _ds1.s-roofdrain.G.B1X0, _ds1, corner=0.0)
    c.showPage()


# ============================= A-202 ELEVATIONS (CONT.) =============================
def sheet_a202():
    sh=Sheet(c,"A-202","Building 1 — parcel face, notes","1/4\" = 1'-0\""); sh.frame()
    # Room at the left for the stair and its bottom landing beyond the rear, where the
    # mirror leaves them on this face rather than on Sage.
    ADJ_OX=LC
    # The wall that carries Building 1's services: the three caps src/mechanical.py
    # places on it, the meter bank and the Units 2/3 outdoor units, all read from
    # src/faces.py.
    p_ops=face('v',EXT_STUD,B1,flip=48)
    p_terms,p_boxes=face_items(1,'ADJACENT-PARCEL WALL',flip=48)
    elev(ADJ_OX, RY1, 48, p_ops,
         "BUILDING 1 — ADJACENT-PARCEL ELEVATION",26,gable=False,
         rakes=(rake(B1_ROOF,'REAR'),rake(B1_ROOF,'S ELM AVENUE')),
         bearing_runs=[(0,48-Y_SEP_BOT,'F1'),(48-Y_SEP_TOP,48,'F2')],
         terms=p_terms,boxes=p_boxes)
    # Roof drainage, src/downspouts.py: the parcel gutter falls to DS-2 at the rear corner.
    # This elevation reads from the rear, so elevation x is Building 1's rear face less
    # site y, and the rear corner is at 0.
    _ds2 = next(d for d in roofdrain.DS.DOWNSPOUTS if d.eave.face == roofdrain.G.F_B1_PARCEL)
    assert _ds2.face == roofdrain.G.F_B1_PARCEL, "A-202 draws %s on the parcel elevation; the model has moved it" % _ds2.mark
    roofdrain.gutter(lambda v: ADJ_OX+v*Q, lambda v: RY1+v*Q, -rake(B1_ROOF,'REAR'), 48.0+rake(B1_ROOF,'S ELM AVENUE'),
                     "EAVE GUTTER — FALLS TO %s AT THE REAR CORNER" % _ds2.mark, 40.0)
    roofdrain.elevation(lambda v: ADJ_OX+v*Q, lambda v: RY1+v*Q, roofdrain.G.B1Y1-_ds2.s, _ds2)
    # Building 2's courtyard face is on A-203 with its other three.
    c.setFillColor(black); c.setFont("Helvetica-Bold",10)
    # The note block grew when the mirror put all three entries on a street and took the
    # rated underside off the stair. It starts higher and sets a touch tighter so it still
    # clears the termination diagram below it.
    NX=X0+9.2*inch; yy=Y1-7.15*inch
    c.drawString(NX,yy,"ELEVATION NOTES"); yy-=0.26*inch
    c.setFont("Helvetica",7.8)
    for t in ["EXTERIOR FINISH: VINYL SIDING, D4 DOUBLE PROFILE, OVER HOUSE WRAP AND 7/16\" OSB SHEATHING. TRIM AT ALL",
     "CORNERS AND OPENINGS. ROOF: 30-YEAR ARCHITECTURAL ASPHALT SHINGLE, 4:12 PITCH, ICE BARRIER AT EAVES PER",
     f"COLUMBUS CIC-09. PREFABRICATED TRUSSES AT 24\" O.C. WITH A {inches(levels.ROOF_HEEL)} RAISED HEEL, S-103 DETAIL 1, BOTH BUILDINGS.",
     f"EAVE +{fmt(levels.EAVE)}, NOMINAL RIDGE +{fmt(levels.ridge(B2_W))}; HEIGHT +{fmt(levels.height(B2_W))}, THE MEAN OF EAVE AND RIDGE, C.C. 3303.08.",
     "ROOF BEARING PLATE +19'-6\"; TRUSS BOTTOM-CHORD UNDERSIDE AT THIS DATUM. MAINTAIN CEILING HEIGHTS ON A-301.",
     "L1 PLATES STEP AT W4: F2 +9'-3\", F1 +9'-5-1/8\"; FINISHED L2 FLOOR REMAINS LEVEL AT +10'-6\".",
     "",
     "THE THREE STREET-FACING ELEVATIONS — BUILDING 1'S S ELM AVENUE AND BOTH BUILDINGS' SAGE AVENUE — CARRY AN",
     "ALLOWANCE FOR FIBER CEMENT OR ENGINEERED WOOD SIDING IF REQUIRED BY THE AREA COMMISSION. THE",
     "ADJACENT-PARCEL, COURTYARD AND REAR ELEVATIONS ARE VINYL THROUGHOUT.",
     "",
     f"STREET-FACE TRIM, THE SAME THREE FACES: FLAT {X.TRIM_MATERIAL} — {inches(X.CASING_W)} CASINGS AT EVERY WINDOW, SILL INCLUDED, AND EVERY DOOR;",
     f"A {inches(X.HEAD_CASING)} HEAD CASING OVER EACH WITH A METAL DRIP CAP; A {inches(X.FRIEZE)} FRIEZE BOARD UNDER THE EAVES; {inches(X.CORNER_BOARD)} CORNER",
     f"BOARDS; {X.GABLE_ACCENT[(B1_ROOF.name,'S ELM AVENUE')]} IN BUILDING 1'S S ELM GABLE. UNIT 1'S S ELM ENTRY TAKES A FLAT SURROUND,",
     f"{inches(X.SURROUND_PILASTER)} PILASTERS AND A {inches(X.SURROUND_CROSSHEAD)} CROSSHEAD WITH A DRIP CAP, NOTHING PROJECTING FROM THE WALL. THE OTHER",
     f"FACES TAKE THE SIDING MANUFACTURER'S STANDARD TRIM. EVERY WINDOW: {X.WINDOW_COLOUR}, NO GRILLES; A-602.",
     "",
     f"ENTRIES / EXTERIOR STAIRS: SEE A-001 NOTES 13a / 13b, A-604 AND C-101. UNIT 3 STAIR FSD {fmt(U3_STAIR_CLR)} TO THE STREET CENTERLINE;",
     f"UNIT 5 STAIR FSD {fmt(U5_STAIR_CLR)} TO THE IMAGINARY LINE. UNDERSIDES UNRATED; A-601. SERVICE EQUIPMENT: C-101 NOTE 5c.",
     "",
     "",
     "BUILDING 1'S REAR WALL IS W1R FOR ITS FULL HEIGHT, GABLE INCLUDED, AND ITS RAKE IS HELD TO S-103 NOTE 5: SEE A-601. PROTECT EVERY",
     "PENETRATION OF IT PER A-001 NOTE 2a — THE DRYER DUCT AT BOTH LEVELS, DR-2 AND DR-3. STACK E RISES WITHIN IT AND LEAVES THROUGH",
     "THE ROOF, P-601 NOTE 1d AND S-103.",
     "",
     "THROUGH-SIDING PROJECTIONS ARE SHOWN ON THEIR ACTUAL ELEVATION FACES: DR = DRYER EXHAUST HOOD / BACKDRAFT DAMPER;",
     "EF = BATH EXHAUST AND RH = RANGE HOOD WALL CAPS; EM AND HP = C-101 NOTE 5c. ROOF VENTS AND CAPS ARE NOT SHOWN.",
     "",
     "DR-2 / DR-3: SEE A-001 NOTE 16a."]:
        c.drawString(NX,yy,t); yy-=0.145*inch
    assert yy >= Y0, "A-202's elevation notes run under the drawing area by %.2f in" % ((Y0-yy)/inch)

    c.showPage()


def same_wall(ops, bldg, wall, flip=None):
    """The openings face() gives an elevation, held to the ones src/mechanical.py measures
       that wall's caps against, mapped with the same flip. The caps and boxes are placed
       in mechanical's frame and the openings in the plans', so if the two ever read a
       wall differently a cap would print beside the wrong window; this stops the build
       first."""
    X = (lambda a: flip-a) if flip else (lambda a: a)
    mine = sorted((round(x, 4), round(x+ln, 4), round(z, 4)) for x, ln, z, _h, _mk, _k in ops)
    model = sorted((round(min(X(o.lo), X(o.hi)), 4), round(max(X(o.lo), X(o.hi)), 4), round(o.zlo, 4))
                   for o in WALLS[bldg][wall].openings)
    assert mine == model, "building %d %s: elevation openings %s, mechanical %s" % (bldg, wall.lower(), mine, model)
    return ops


# ============================= A-203 ELEVATIONS (CONT.) =============================
def sheet_a203():
    """All four faces of Building 2: its two 28'-0" eave faces over its two 26'-0" gables."""
    sh=Sheet(c,"A-203","Building 2 — exterior elevations","1/4\" = 1'-0\""); sh.frame()
    # Two 28'-0" eave faces share the top row, where A-201's columns hold 26'-0" ones: the
    # right column stands far enough over that the Sage face's datum labels end short
    # of the parcel face's roof edge, and the parcel face's own labels inside the frame.
    RC2=X0+9.75*inch
    widest=max(pdfmetrics.stringWidth(t,"Helvetica",6.2) for t in
               ("HEIGHT, C.C. 3303.08   +%s"%fmt(levels.height(B2_W)),"NOM. RIDGE   +%s"%fmt(levels.ridge(B2_W)),
                "EAVE, TOP OF HEEL   +%s"%fmt(levels.EAVE),"L1 PLATE / F1   +%s"%fmt(levels.F1_PLATE)))
    labels_end=lambda ox,right_rake: ox+(B2_D+right_rake)*Q+19+widest
    assert labels_end(LC,rake(B2_ROOF,'REAR'))+12 <= RC2-rake(B2_ROOF,'REAR')*Q, "A-203: the Sage labels reach the parcel elevation"
    assert labels_end(RC2,rake(B2_ROOF,'COURTYARD')) <= X1, "A-203: the parcel elevation's labels run out of the drawing area"
    # Sage is an eave face read from the street: the courtyard end is on the observer's
    # left, as it is for Building 1's Sage face, and elevation x is page y unflipped.
    s_terms,_ = face_items(2,'SAGE WALL')
    elev(LC, RY1, B2_D, same_wall(face('v',B2_W-EXT_STUD,B2),2,'SAGE WALL'),
         "BUILDING 2 — SAGE AVENUE ELEVATION  (UNIT 5 STAIR NOT SHOWN)",B2_W,gable=False,
         rakes=(rake(B2_ROOF,'COURTYARD'),rake(B2_ROOF,'REAR')),terms=s_terms,
         trim=(2,'SAGE WALL') in X.STREET_FACES)
    # The parcel face is read from the adjacent parcel, which puts the rear on the left.
    p_ops=same_wall(face('v',EXT_STUD,B2,flip=B2_D),2,'ADJACENT-PARCEL WALL',flip=B2_D)
    p_terms,p_boxes=face_items(2,'ADJACENT-PARCEL WALL',flip=B2_D)
    elev(RC2, RY1, B2_D, p_ops,
         "BUILDING 2 — ADJACENT-PARCEL ELEVATION  (UNIT 5 STAIR NOT SHOWN)",B2_W,gable=False,
         rakes=(rake(B2_ROOF,'REAR'),rake(B2_ROOF,'COURTYARD')),terms=p_terms,boxes=p_boxes)
    # The bottom row holds the two 26'-0" gable faces in the same columns, so the rear
    # face's labels have more room than the Sage face's above them; held all the same.
    assert labels_end(LC,EAVE_OVERHANG)-(B2_D-B2_W)*Q+12 <= RC2-EAVE_OVERHANG*Q, "A-203: the rear labels reach the courtyard elevation"
    # The rear gable is read from the alley, the way Building 1's rear face is: Sage on
    # the left, so elevation x is page x and the mechanical frame needs no flip for caps.
    r_terms,_ = face_items(2,'REAR WALL')
    elev(LC, RY2, B2_W, same_wall(face('h',B2_D-EXT_STUD,B2,flip=B2_W),2,'REAR WALL'),
         "BUILDING 2 — REAR ELEVATION",B2_W,terms=r_terms)
    # The courtyard face looks back at Building 1 and S Elm beyond, so it is the same
    # orientation as Building 1's S Elm face: the adjacent parcel on the left, which is
    # mechanical's frame read backwards. The Unit 5 stair stands on this face and runs past
    # neither end of it, so the datum labels stay where they are; only the stair is added.
    elev(RC2, RY2, B2_W, same_wall(face('h',EXT_STUD,B2),2,'COURTYARD WALL',flip=B2_W),
         "BUILDING 2 — COURTYARD ELEVATION",B2_W,terms=placed([],2,'COURTYARD WALL'))
    u5_stair_elev(RC2,RY2)
    # Roof drainage, src/downspouts.py. The Sage gutter turns the rear corner to DS-3 on
    # the rear face, off the Unit 3 walk, as Building 1's does to DS-1 on A-201; the
    # parcel gutter falls to DS-4 at the rear corner, as Building 1's does to DS-2.
    _ds3 = next(d for d in roofdrain.DS.DOWNSPOUTS if d.eave.face == roofdrain.G.F_B2_SAFF)
    assert _ds3.face == roofdrain.G.F_B2_REAR, "A-203 draws %s on the rear elevation; the model has moved it" % _ds3.mark
    roofdrain.gutter(lambda v: LC+v*Q, lambda v: RY1+v*Q, -rake(B2_ROOF,'COURTYARD'), B2_D+rake(B2_ROOF,'REAR'),
                     "EAVE GUTTER — FALLS TO %s ON THE REAR FACE" % _ds3.mark, B2_D/2.0)
    roofdrain.elevation(lambda v: LC+v*Q, lambda v: RY2+v*Q, _ds3.s-roofdrain.G.B2X0, _ds3, corner=0.0)
    _ds4 = next(d for d in roofdrain.DS.DOWNSPOUTS if d.eave.face == roofdrain.G.F_B2_PARCEL)
    assert _ds4.face == roofdrain.G.F_B2_PARCEL, "A-203 draws %s on the parcel elevation; the model has moved it" % _ds4.mark
    roofdrain.gutter(lambda v: RC2+v*Q, lambda v: RY1+v*Q, -rake(B2_ROOF,'REAR'), B2_D+rake(B2_ROOF,'COURTYARD'),
                     "EAVE GUTTER — FALLS TO %s AT THE REAR CORNER" % _ds4.mark, B2_D/2.0)
    roofdrain.elevation(lambda v: RC2+v*Q, lambda v: RY1+v*Q, roofdrain.G.B2Y1-_ds4.s, _ds4)
    c.showPage()

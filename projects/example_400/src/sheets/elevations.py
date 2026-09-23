"""A-201 and A-202 — the exterior elevations: four faces of each building at 1/4" = 1'-0".

Every opening is read from the window and door lists the plans draw, through the same
regrid, so an elevation cannot show a window the plan does not have. Heights are
src/levels.py's. The roofs are 4:12 gables on trusses bearing on the side walls, so each
building's front and rear faces are its gables and its side faces its eaves. Each face is
drawn as someone standing in front of it sees it:

  front (Oak, or the courtyard for Building 2)   404 Oak on the left: elevation x = plan x
  rear                                            396 Oak on the left: flipped
  north (396 Oak side)                           the front on the left: elevation x = plan y
  south (404 Oak side)                           the rear on the left: flipped
"""
from arkitect.lib.draw.page import GREY, Sheet
from arkitect.lib.units import IN, fmt, inches
from reportlab.lib.colors import Color, black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import building1 as B1M, building2 as B2M, exterior as X, grading as G, levels, services
from src.building2 import (B2_D, B2_W, U5_FLIGHT_X0, U5_LAND_X0, U5_LAND_X1, U5_RISERS, U5_STAIR_TAG,
                           U5_STOOP_X0, U5_STOOP_Z, U5_TREADS)
from src.building1 import B1_D, B1_W
from src.foundation import ROOF_OVERHANG
from src.framing import TRUSS_OC
from src.openings import WIN_FIXED, WIN_GEOM
from arkitect.lib.draw.kit import datum_labels, knockout
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c

EAVE_OVERHANG = ROOF_OVERHANG            # eaves and rakes alike
DOOR_H = 6.0+8.0/12.0

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
         trim=False,accent=None,surround=False,cased=()):
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
        if trim or mk in cased:
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
        if kind=="w" and mk[2:] not in WIN_FIXED:          # a fixed unit has no meeting rail
            c.setLineWidth(0.5); c.line(Xp(x),Yp(sill+hh/2),Xp(x+ww),Yp(sill+hh/2))
        c.setFillColor(black)
        knockout(Xp(x+ww/2),mark_y,mk,"Helvetica",5.2,"c")   # in the head casing on a trimmed face
    # The equipment standing in front of the face. One meter drawn per position; an
    # outdoor unit shows its fan. Each box states its underside.
    for (x0,x1,z0,z1,mk,n) in boxes:
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(0.8)
        c.rect(Xp(x0),Yp(z0),(x1-x0)*sc,(z1-z0)*sc,fill=1,stroke=1)
        c.setLineWidth(0.5)
        if n < 0:
            pass                                                # a plain box: telecom
        elif n:
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
        c.drawString(ox,oy-0.74*inch,"STREET FACE: FLAT %s TRIM, FRIEZE AND CORNER BOARDS%s — NOTE 5"
                     %(X.TRIM_MATERIAL,", DOOR SURROUND" if surround else ""))
    c.setLineWidth(1.0); c.line(ox,oy-0.20*inch,ox+2.0*inch,oy-0.20*inch)


def u3_stair_elev(ox,oy,sc=Q):
    """The Unit 3 stair on Building 2's courtyard elevation. Its constants are final SHEET
       coordinates, 396 Oak at the left; the face is read from the courtyard with 404 Oak
       at the left, so they are flipped, and the flight descends to the right."""
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
    knockout(Xp(e+0.2),Yp(-0.75),"CONCRETE STOOP — TOP +%s"%inches(U5_STOOP_Z),"Helvetica",5.3,"r")
    knockout(Xp(e+0.2),Yp(-1.05),"ONE %s STEP DOWN TO THE WALK, C-103"%inches(G.STOOP_STEP),"Helvetica",5.3,"r")
    knockout(Xp(e+0.2),Yp(-1.35),U5_STAIR_TAG,"Helvetica",5.3,"r")



# ---------------- the faces ----------------
FACES = ('FRONT', 'REAR', 'NORTH', 'SOUTH')


def face(plans, W, D, which, rear_y):
    """One face's openings as elev() takes them: (x, width, sill, height, mark, kind), read
       from every level's window and exterior-door lists through that level's regrid."""
    out = []
    for lv, (P, wins, doors) in plans.items():
        ff = FF[lv]
        ops = [(w[0], w[1], w[2], w[3], "W-"+w[4], "w") for w in wins]
        ops += [(d[0], d[1], d[2], d[3], "D-1" if d[2] >= 3.0 else "D-2", "d") for d in doors if "ext" in d[5:]]
        for x, y, ln, o, mk, kind in ops:
            on = {'FRONT': o == 'h' and y < 1.0, 'REAR': o == 'h' and abs(y-rear_y) < 1e-6,
                  'SOUTH': o == 'v' and x < 1.0, 'NORTH': o == 'v' and x > W-1.0}[which]
            if not on: continue
            pos = P.x(x, y) if o == 'h' else P.y(y)
            if which == 'REAR':  pos = W-pos-ln
            if which == 'SOUTH': pos = D-pos-ln
            sill, h = (GEOM[mk[2:]][0], GEOM[mk[2:]][1]) if kind == "w" else (0.0, DOOR_H)
            out.append((pos, ln, ff+sill, h, mk, kind))
    return sorted(out)


def _plans(n):
    if n == 1:
        return B1_W, B1_D, B1M.Y_REAR, {lv: (m['plan'], m['wins'], m['doors']) for lv, m in B1M.LEVEL.items()}
    return B2_W, B2_D, B2M.Y_REAR, {lv: (B2M.PLAN_B2, B2M.b2_wins(lv), B2M.B2doors) for lv in (1, 2)}


def openings(n, which):
    W, D, rear_y, plans = _plans(n)
    return face(plans, W, D, which, rear_y)


def check_elevations():
    """Every window and exterior door on the plans stands on exactly one face."""
    for n in (1, 2):
        W, D, rear_y, plans = _plans(n)
        want = sum(len(wins)+sum(1 for d in doors if "ext" in d[5:]) for _P, wins, doors in plans.values())
        have = sum(len(openings(n, f)) for f in FACES)
        assert have == want, "Building %d: %d openings on the plans, %d on the elevations" % (n, want, have)
        for f in FACES:
            ln = W if f in ('FRONT', 'REAR') else D
            for x, w, sill, h, mk, _k in openings(n, f):
                assert -1e-6 <= x and x+w <= ln+1e-6, "Building %d %s: %s runs off the face" % (n, f, mk)
                assert sill+h <= (levels.F1_PLATE if sill < levels.FF2 else levels.ROOF_PLATE)+1e-6, \
                    "Building %d %s: %s passes its plate" % (n, f, mk)
    # the stair is drawn from sheet feet and the doors from the plan: Unit 3's door stands
    # on the top landing, or one of the two is flipped
    door = next(o for o in openings(2, 'FRONT') if o[5] == "d" and o[2] >= levels.FF2-1e-6)
    assert B2_W-U5_LAND_X1-1e-6 <= door[0] and door[0]+door[1] <= B2_W-U5_LAND_X0+1e-6, \
        "A-202: Unit 3's door is not on the stair's top landing"


def _leader(ox, oy, x, mark, sc=Q):
    """A roof leader on a face: from the soffit to its elbow, C-103."""
    sof = levels.EAVE-EAVE_OVERHANG*levels.ROOF_PITCH-FASCIA_DROP
    w = IN(3)
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(0.6)
    c.rect(ox+(x-w/2)*sc, oy+0.5*sc, w*sc, (sof-0.5)*sc, fill=1, stroke=1)
    c.setFillColor(black)
    knockout(ox+x*sc, oy+(levels.FF1+4.2)*sc, mark, "Helvetica-Bold", 5.0, "c")


def _leader_x(ld, n, which):
    """Where a C-103 leader stands along a face, as that face is read."""
    bx, by, W, D = (G.B1X0, G.B1Y0, B1_W, B1_D) if n == 1 else (G.B2X0, G.B2Y0, B2_W, B2_D)
    px, py = ld.x-bx, ld.y-by                      # page feet: 396 Oak at x 0, the front at y 0
    return {'FRONT': W-px, 'REAR': px, 'NORTH': py, 'SOUTH': D-py}[which]


def _leader_face(ld, n):
    bx, by, W, D = (G.B1X0, G.B1Y0, B1_W, B1_D) if n == 1 else (G.B2X0, G.B2Y0, B2_W, B2_D)
    px, py = ld.x-bx, ld.y-by
    if abs(py-D) < 1e-6: return 'REAR'
    if abs(py) < 1e-6: return 'FRONT'
    return 'NORTH' if abs(px) < 1e-6 else 'SOUTH'


def notes(n):
    span = B1_W if n == 1 else B2_W
    return [
     f"1.  HEIGHTS ARE ABOVE FINISHED GRADE AT THE FOUNDATION WALL, 0'-0\", C-103. THE FOUNDATION STANDS {inches(levels.SLAB_TOP-levels.GRADE)} OUT OF GRADE, S-101. BUILDING HEIGHT IS THE MEAN OF EAVE AND RIDGE, C.C. 3303.08: +{fmt(levels.height(span))}.",
     f"2.  ROOF: {round(levels.ROOF_PITCH*12)}:12 GABLE, PREFABRICATED WOOD TRUSSES AT {inches(TRUSS_OC)} O.C. BEARING ON THE SIDE WALLS, {inches(EAVE_OVERHANG)} OVERHANG AT EAVES AND RAKES. EAVE GUTTERS AND LEADERS DS-1 TO DS-4 PER C-103.",
     "3.  OPENINGS ARE MARKED AS THE PLANS MARK THEM. EVERY W-A GIVES THE NET CLEAR OPENING OF G-001 NOTE 8a. W-D, OVER THE UNIT 1 STAIR, IS FIXED.",
     f"4.  WINDOWS: {X.WINDOW_COLOUR}, NO GRILLES.",
     f"5.  TRIM, FLAT {X.TRIM_MATERIAL}: EVERY WINDOW AND DOOR ON EVERY FACE HAS CASINGS AND A HEAD CASING WITH A DRIP CAP. BUILDING 1'S OAK AVENUE FACE ALSO HAS A FRIEZE BOARD, CORNER BOARDS AND A FLAT SURROUND AT THE ENTRY.",
    ]+(["6.  SERVICE EQUIPMENT ON BUILDING 1'S NORTH FACE: HEAT PUMP OUTDOOR UNIT HP-1 ON A WALL BRACKET, METER-MAIN EM-1 (E-101) AND TELECOM BOX TC-1, UNDERSIDES AS SHOWN; 3'-0\" CLEAR IN FRONT OF EM-1, NEC 110.26(A).",
        "7.  WALL CAPS: DRYER DR-1 ON THE REAR FACE AND BATH EXHAUST EF-1A ON THE NORTH FACE, PLACED AND SCHEDULED ON M-101."] if n == 1 else
       ["6.  SERVICE EQUIPMENT: TWO-METER BANK EM-2 (E-102) AND TELECOM BOX TC-2 ON THE NORTH FACE, THE PARKING WALK EM-2'S 3'-0\" WORKING SPACE, NEC 110.26(A); HEAT PUMP OUTDOOR UNITS HP-2 AND HP-3 ON WALL BRACKETS ON THE SOUTH FACE.",
        "7.  UNIT 3 STAIR: PER S-101 NOTE 5 AND C-101 NOTE 5; 36\" GUARDS, 34\" TO 38\" GRASPABLE HANDRAIL, RCO 311.7 AND 312.",
        "8.  WALL CAPS: DRYERS DR-2 AND DR-3 ON THE NORTH FACE AND BATH EXHAUST EF-2 ON THE SOUTH FACE, PLACED AND SCHEDULED ON M-102."] if n == 2 else [])


def face_terms(n, which):
    """The wall caps src/mechanical.py puts on this face, as elev() takes them: a cap is
       placed in page feet along its wall and each face reads its own way."""
    from src import mechanical as M
    W, D, _r, _p = _plans(n)
    wall = {'NORTH': 'NORTH WALL', 'SOUTH': 'SOUTH WALL', 'FRONT': M.FRONT_NAME[n], 'REAR': 'REAR WALL'}[which]
    at = {'NORTH': lambda a: a, 'SOUTH': lambda a: D-a, 'FRONT': lambda a: W-a, 'REAR': lambda a: a}[which]
    return [(at(t.along), t.z, t.mark, 'dryer' if t.what == 'DRYER EXHAUST' else 'exh') for t in M.TERMS[n].get(wall, [])]


def _sheet(n, no, names):
    W, D, _r, _p = _plans(n)
    sh = Sheet(c, no, "Building %d — exterior elevations" % n, "1/4\" = 1'-0\""); sh.frame()
    widest = max(pdfmetrics.stringWidth(t, "Helvetica", 6.2) for t in
                 ("HEIGHT, C.C. 3303.08   +%s" % fmt(levels.height(W)), "EAVE, TOP OF HEEL   +%s" % fmt(levels.EAVE)))
    lc = X0+0.3*inch+EAVE_OVERHANG*Q
    ends = lc+(D+EAVE_OVERHANG)*Q+19+widest                  # where the eave face's labels end
    rc = ends+0.3*inch+EAVE_OVERHANG*Q
    assert rc+(W+EAVE_OVERHANG)*Q+19+widest <= X1, "%s: the gable elevation's labels run out of the drawing area" % no
    run = [(W, 'F2' if n == 1 else 'F1')]
    leaders = [ld for ld in G.LEADERS if ld.eave.startswith("BUILDING %d" % n)]
    for (which, ox, oy) in (('NORTH', lc, RY1), ('FRONT', rc, RY1), ('SOUTH', lc, RY2), ('REAR', rc, RY2)):
        gable = which in ('FRONT', 'REAR')
        ln = W if gable else D
        street = (n, which) in X.STREET_FACES
        elev(ox, oy, ln, openings(n, which), "BUILDING %d — %s" % (n, names[which]), W, gable=gable,
             rakes=None if gable else (EAVE_OVERHANG, EAVE_OVERHANG), bearing_runs=[(0, ln, run[0][1])],
             trim=street, surround=street, terms=face_terms(n, which),
             cased={o[4] for o in openings(n, which)} if X.CASE_ALL_OPENINGS else (),
             boxes=[((b.along0, b.along1) if which == 'NORTH' else (ln-b.along1, ln-b.along0))
                    + (b.z0, b.z1, b.mark, services.POSITIONS.get(b.mark, 0 if b.kind == 'odu' else -1))
                    for b in services.on(n, which)])
        for ld in leaders:
            if _leader_face(ld, n) == which:
                _leader(ox, oy, _leader_x(ld, n, which), ld.mark)
        if n == 2 and which == 'FRONT':
            u3_stair_elev(ox, oy)
    c.setFillColor(black); c.setFont("Helvetica-Bold", 8); c.drawString(X0+0.3*inch, Y0+1.0*inch, "ELEVATION NOTES")
    c.setFont("Helvetica", 6.4); y = Y0+0.87*inch
    for t in notes(n):
        assert pdfmetrics.stringWidth(t, "Helvetica", 6.4) <= X1-X0-0.4*inch, "%s note overruns the sheet: %r" % (no, t[:40])
        c.drawString(X0+0.3*inch, y, t); y -= 0.108*inch
    assert y >= Y0-0.02*inch, "%s notes run off the sheet" % no
    c.showPage()


def sheet_a201():
    _sheet(1, "A-201", {'FRONT': "OAK AVENUE ELEVATION", 'REAR': "REAR ELEVATION, TO THE COURTYARD",
                        'NORTH': "NORTH ELEVATION, TO 396 OAK AVE", 'SOUTH': "SOUTH ELEVATION, TO 404 OAK AVE"})


def sheet_a202():
    _sheet(2, "A-202", {'FRONT': "COURTYARD ELEVATION", 'REAR': "REAR ELEVATION, TO THE ALLEY",
                        'NORTH': "NORTH ELEVATION, TO 396 OAK AVE  (UNIT 3 STAIR NOT SHOWN)",
                        'SOUTH': "SOUTH ELEVATION, TO 404 OAK AVE  (UNIT 3 STAIR NOT SHOWN)"})

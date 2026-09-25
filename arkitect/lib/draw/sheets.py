"""Drawing a plan sheet: the stages a level passes through on its way to a page.

    regrid          model coordinates onto the stud-to-stud 1/8 in grid
    dimension       derive every string, and suppress the ticks a closet
                    should not put on a wall
    mirror          flip the whole level together, so nothing is left behind
    draw the plan   poche first, rooms punched out of it, then everything over
    annotate        what is written on the plan
    surround        context, unit brackets, title block

The order is not arrangeable. Dimensions are derived on the regridded model but BEFORE
the mirror, so a string describes the wall it belongs to and flips with it; and the
mirror is one call because a kind of object left out of it lands on the far side of the
plan from everything else.

Nothing here knows about a particular building. Where a project has its own drawing to
add — a stair, a unit's plans — it hands in a callable on the PlanLevel, at one of the
three moments PlanLevel documents.
"""
from reportlab.pdfbase import pdfmetrics
from arkitect.lib.model.mirror import (mrooms, mpoly, mdoors, mwins, mops, mdims, mnotes,
                              mtags, mchains, mfurn)
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white
from arkitect.lib import symbols
from arkitect.lib.units import fmt
# PlanDraw and Sheet are re-exported into this module's namespace on purpose:
# arkitect/lib/export/dxf.py and arkitect/lib/verify/trace.py monkeypatch sheets.PlanDraw.__init__ and
# sheets.Sheet.__init__ by that path. Do not drop them even if unused here.
from arkitect.lib.draw.page import DA, GREY, LAY, LGREY, POCHE, PlanDraw, Sheet
from arkitect.lib.model.regrid import PARTITION, PART_STUD
from arkitect.lib.model.records import Geometry
from arkitect.lib.model.dimensions import (regrid_all, net_areas, wall_faces, room_dims,
                                  closet_dims, closet_opening_dims, wc_dims)

X0,Y0,X1,Y1 = DA
DW = X1-X0
Q  = 18.0        # 1/4" = 1'-0", in points per foot


def is_closet(op,rooms,tol=PARTITION/2+0.05):
    """An opening on a face of a closet is that closet's bypass door, type D-5. Derived
       rather than listed, so a closet that moves keeps its door. The tolerance is half a
       partition: some openings are given on the closet face and some on the centerline
       of the wall the closet is recessed into."""
    x,y,ln,o = op[0],op[1],op[2],op[3]
    for r in rooms:
        if len(r)<5 or not str(r[4]).startswith("CL."): continue
        rx,ry,rw,rh = r[0],r[1],r[2],r[3]
        if o=='v' and min(abs(x-rx),abs(x-(rx+rw)))<=tol \
           and ry-0.05<=y and y+ln<=ry+rh+0.05: return True
        if o=='h' and min(abs(y-ry),abs(y-(ry+rh)))<=tol \
           and rx-0.05<=x and x+ln<=rx+rw+0.05: return True
    return False


def draw_openings(p,openings,flags):
    for op,isc in zip(openings,flags):
        if isc:
            p.bypass(*op)
        else:
            p.opening(*op)


def draw_joist_span(p,a,at,b,label,o='h'):
    """Double-headed clear-span arrow; its axis is the joist direction.

    o='h': the joists run in x, from a to b, and the arrow is drawn at y = at.
    o='v': the joists run in y, from a to b, and the arrow is drawn at x = at, its
           label turned to read along it. A joist entry is (a, at, b, prefix[, o]).
    """
    p.c.saveState(); p.c.setStrokeColor(black); p.c.setFillColor(black); p.c.setLineWidth(0.65)
    ah=5.0
    tw=pdfmetrics.stringWidth(label,"Helvetica-Bold",5.6)
    if o=='h':
        x0,x1=p.X(min(a,b)),p.X(max(a,b)); yy=p.Y(at)
        p.c.line(x0,yy,x1,yy)
        for xx,sgn in ((x0,1),(x1,-1)):
            p.c.line(xx,yy,xx+sgn*ah,yy+2.7)
            p.c.line(xx,yy,xx+sgn*ah,yy-2.7)
        p.c.setFont("Helvetica-Bold",5.6)
        cx=(x0+x1)/2.0
        p.c.setFillColor(white); p.c.rect(cx-tw/2-2,yy+2,tw+4,7,fill=1,stroke=0)
        p.c.setFillColor(black); p.c.drawCentredString(cx,yy+3.5,label)
    else:
        # plan y runs down the page, so the LOW plan y is the HIGH page y
        y0,y1=p.Y(max(a,b)),p.Y(min(a,b)); xx=p.X(at)
        p.c.line(xx,y0,xx,y1)
        for yy,sgn in ((y0,1),(y1,-1)):
            p.c.line(xx,yy,xx+2.7,yy+sgn*ah)
            p.c.line(xx,yy,xx-2.7,yy+sgn*ah)
        p.c.setFont("Helvetica-Bold",5.6)
        cy=(y0+y1)/2.0
        p.c.setFillColor(white); p.c.rect(xx-9,cy-tw/2-2,7,tw+4,fill=1,stroke=0)
        p.c.setFillColor(black)
        p.c.translate(xx-3.5,cy); p.c.rotate(90); p.c.drawCentredString(0,0,label)
    p.c.restoreState()


def closet_ticks_removed(chains,rooms,openareas,openings,bypass_flags):
    """Drop the dimension ticks a closet should not put on a wall string.

    Two faces, for the same reason: the string reads better as one number to the jamb
    than as room-less-closet plus closet, and the closet's own depth dimension locates
    it anyway.

    THE OPENING FACE. A closet's opening face is not a wall, so it has no business
    breaking a wall string. Dropping that tick lets the room close as one overall, and
    room_dims then finds the room already dimensioned and adds nothing inside it.

    THE STUD WALL CLOSING THE RUN. 3-1/2" of ordinary partition whose position follows
    from the clear opening beside it, so marking it only put a bare stub of dimension
    line between two witness rails. Only a wall no wider than the closet itself
    qualifies; the separation is also a partition away from a jamb.
    """
    # wall_faces() rounds every face to 3 decimals -- it uses the face as a dict key to
    # merge coincident walls, so the rounding is load-bearing and stays. What has to
    # match it is the tolerance HERE. 1e-6 was exact on the 0.1 ft model grid, which is
    # where every other caller runs; this one runs on REGRIDDED coordinates, multiples of
    # 1/96 ft, where rounding to 3 decimals moves a face by up to 5e-4 -- 166 times the
    # tolerance it was being compared at. The effect was two stray tick crosses beside
    # the Units 2/3 closet on A-101 and A-102: dimchain suppressed the 3-1/2" line and
    # its label as shorter than a partition, and drew the ticks and witness lines anyway,
    # which is precisely the artifact this function exists to prevent.
    #
    # A wall face is never within 1e-3 ft (a hundredth of an inch) of a DIFFERENT wall
    # face -- the nearest real distinction is a stud width -- so this separates what it
    # must and tolerates what the rounding does.
    FACE_TOL = 1e-3
    ofx={o[0] for o,b in zip(openings,bypass_flags) if b and o[3]=='v'}
    ofy={o[1] for o,b in zip(openings,bypass_flags) if b and o[3]=='h'}
    sw=set()
    for r in rooms:
        if r[4]!="CL." or not r[2]<r[3]: continue
        x,y,w,h=r[:4]
        for (f,lo,hi) in wall_faces(rooms,openareas,1,(x,x+w),(-1e9,1e9)):
            if lo>x-0.05 and hi<x+w+0.05 and any(abs(f-(j+e*PART_STUD))<FACE_TOL
                                                 for (j,e) in ((y,-1),(y+h,1))):
                sw.add(f)
    def keep(cs,o):
        # a closet stud wall goes even where it is a chain's own end — unbridge can
        # leave it there, and it is exactly the face we decided carries no dimension
        drop = ofx if o=='h' else ofy
        gone = sw if o=='v' else set()
        return [pt for k,pt in enumerate(cs)
                if not any(abs(pt[0]-f)<FACE_TOL for f in gone)
                and (k in (0,len(cs)-1) or not any(abs(pt[0]-f)<1e-6 for f in drop))]
    out=[(keep(cs,o),o,at,sd,ml,mk,la) for (cs,o,at,sd,ml,mk,la) in chains]
    return [ch for ch in out if len(ch[0])>1]


def mirror_everything(W,rooms,openareas,doors,wins,openings,dims,notes,tags,
                      chains,joists):
    """Put a whole level through the sheet mirror in one place.

    Every kind of object needs its own map — a door's handedness, a chain's 'lo'/'hi'
    groups and a fitting's 'e'/'w' facing all have to swap WITH their positions — so the
    danger is not that a map is wrong but that one object gets left out and lands on the
    far side of the plan from everything else. Doing them together is what makes a
    missing line visible. Joists are the one kind with no wrapper: a span arrow is two
    x values and a label, so it flips inline.
    """
    return (mrooms(rooms,W),
            mpoly(openareas,W) if openareas else openareas,
            mdoors(doors,W), mwins(wins,W), mops(openings,W),
            mdims(dims,W), mnotes(notes,W),
            mtags(tags,W) if tags else tags,
            mchains(chains,W),
            # a vertical arrow keeps its run in y and mirrors only the x it stands at
            [((a,W-at,b,prefix,'v') if j[4:5]==('v',) else (W-b,at,W-a,prefix))
             for j in joists for (a,at,b,prefix) in (j[:4],)])


def draw_the_plan(p,W,sc,g,sep,bypass_flags,over_plan=None,captions=None,sep_rows=None,marks_last=False):
    """The plan itself, in the order the drawing has to be built.

    The poche goes down first and every room is punched white out of it, so THE WALL IS
    THE BLACK LEFT BETWEEN TWO WHITE ROOMS — there is no wall object. Everything after
    that is drawn over the holes: the separation, the openings, the fittings, the
    labels. Order is not a style choice here; a room drawn after a door erases it.
    """
    assert g.space=='sheet', "draw wants page coordinates, got %s"%g.space
    rooms,openareas,doors = g.rooms,g.openareas,g.doors
    openings,wins,furn = g.openings,g.wins,g.furn
    p.shell()
    for (pts,labs) in (openareas or []): p.poly(pts,labs)
    p.rooms(rooms)
    if sep:
        # A wall drawn across the whole plan at `sep`, as the rows the project hands over:
        # solid, open, solid ... A double stud wall is (stud, the layers between, stud), its
        # stud rows poched and the gap left white.
        assert sep_rows, "a level with a separation says what rows it is drawn as (sep_rows)"
        p.c.setFillColor(POCHE); p.c.setStrokeColor(black); p.c.setLineWidth(0.8)
        y0 = sep
        for i, t in enumerate(sep_rows):
            if i % 2 == 0: p.c.rect(p.X(0),p.Y(y0+t),W*sc,t*sc,fill=1,stroke=1)
            y0 = y0+t
    for d in doors: p.door(*d[:4],swing=d[4],ext=("ext" in d[5:]),far=("far" in d[5:]))
    draw_openings(p,openings,bypass_flags)
    # A-602's schedule row, the elevations and A-001's notes all call the window W-A, so
    # the plans do too. The bare letter stays the MODEL's key — src/schedules.py counts
    # the A-602 quantities by it — and the prefix is put on here, at the one place a plan
    # draws a window, the way src/sheets/elevations.py puts it on to tag a face.
    if furn: symbols.draw(p,mfurn(furn,W),captions)
    p.labels(rooms)
    # LAST of the plan. The mark is placed toward +x/+y off the opening whichever side
    # of the room the wall is on, so on 13 sheets it landed under casework, a fitting or
    # a device drawn after it and was painted out -- 39 of 287 marks, measured. Drawing
    # the windows after the furniture puts every mark on top of what shares its square
    # inch; the glazing itself sits in the wall, where nothing else is drawn.
    for (x,y,ln,o,mark) in wins: p.window(x,y,ln,o,'' if marks_last else 'W-'+mark)
    if over_plan: over_plan(p)


def draw_the_annotation(p,W,plan,g,over_dims=None):
    """What is written ON the plan: dimensions, notes, wall tags, joist spans.

    A unit authored in INCHES, straight onto the canvas rather than through the regrid,
    draws itself here by way of the level's own draw_unit1 hook — lib does not know which
    project has one or where it lives. The exterior stair comes AFTER the
    dimension strings: their label masks would otherwise erase the centered landing
    annotation on the solid Level 2 stair.
    """
    assert g.space=='sheet', "draw wants page coordinates, got %s"%g.space
    dims,chains,notes,tags,joists = g.dims,g.chains,g.notes,g.tags,g.joists
    for d in dims: p.dim(*d)
    for ch in chains: p.dimchain(*ch)
    if over_dims: over_dims(p)
    for n in notes: p.note(*n)
    for j in joists:
        a,at,b,prefix=j[:4]
        draw_joist_span(p,a,at,b,"%s · %s CLEAR SPAN"%(prefix,fmt(abs(b-a))),
                        o=('v' if j[4:5]==('v',) else 'h'))
    # LAY() rather than whatever note() happened to leave in force a line above.
    for (tx,ty,t) in (tags or []):
        LAY('A-ANNO-IDEN')
        p.c.setFillColor(white); p.c.setStrokeColor(black); p.c.setLineWidth(0.8)
        p.c.circle(p.X(tx),p.Y(ty),9,fill=1,stroke=1)
        p.c.setFillColor(black); p.c.setFont("Helvetica-Bold",8.5)
        p.c.drawCentredString(p.X(tx),p.Y(ty)-3,t)


def draw_the_surround(p,W,D,ox,oy,title,scale,ctx,units,stair_side,over_all=None):
    """What sits AROUND the plan: the context strings, the unit brackets, the title.

    Context is which street or neighbor each face of the building looks at, drawn in
    final sheet coordinates. On a corner lot drawn with the front street at the top of
    every sheet, the side street is on the sheet's LEFT and the adjacent parcel on its
    RIGHT.
    """
    if ctx:
        fr,lf,rt,re = ctx
        # Building 1's exterior stair and its stoop fill one side yard and run past the
        # rear wall. Shift the rear label away from whichever side that is, and keep the
        # side label on that side beyond the relocated exterior dimension strings.
        stair = stair_side
        if fr: p.note(W/2.0,-3.9,fr,7.6,bold=True)
        if re: p.note(W/2.0+stair,D+2.3,re,7.6,bold=True)
        if lf: p.vnote(-(17.5 if not stair else 20.5),D/2.0,lf[0],lf[1],9.0)
        if rt: p.vnote(W+7.5,D/2.0,rt[0],rt[1],9.0)
    for (y0,y1,nm,sub) in (units or []): p.unitbracket(-5.0,y0,y1,nm,sub)
    # The sheet's own furniture -- its title, scale and note reference. It is not
    # model geometry and it had no layer of its own, so it inherited whatever the
    # last plan call left behind: the identical 'SCALE: 1/4" = 1'-0"' string came out
    # of the exporter on A-ANNO-DIMS, A-ANNO-IDEN and A-ANNO-TEXT depending only on
    # which sheet drew it.
    LAY('A-ANNO-TEXT')
    p.c.setFillColor(black); p.c.setFont("Helvetica-Bold",12)
    p.c.drawString(ox, oy-1.45*inch, title.upper())
    p.c.setFont("Helvetica",9); p.c.drawString(ox, oy-1.63*inch, "SCALE: "+scale)
    p.c.setLineWidth(1.2); p.c.line(ox,oy-1.17*inch,ox+2.6*inch,oy-1.17*inch)
    p.c.setFont("Helvetica",8.5)
    p.c.drawString(ox, oy-1.81*inch, "SEE A-001 FOR GENERAL PLAN NOTES.")
    if over_all: over_all(p)


def plan_sheet(c,lv,no,title,scale):
    """Draw one PlanLevel on its own sheet, in stages.

    draw_level handles the geometry and drawing stages; this adds the sheet frame
    and surroundings:

        regrid          model coordinates onto the stud-to-stud 1/8 in grid
        dimension       derive every string, and suppress the ticks a closet
                        should not put on a wall
        mirror          flip the whole level together, so nothing is left behind
        draw the plan   poche first, rooms punched out of it, then everything over
        annotate        what is written on the plan
        surround        context, unit brackets, title block

    The order is not arrangeable. Dimensions are derived on the regridded model but
    BEFORE the mirror, so a string describes the wall it belongs to and flips with it;
    the mirror is one call because a kind of object left out of it lands on the far
    side of the plan from everything else. Schedule quantities are calculated
    separately from the model's opening lists."""
    sh=Sheet(c,no,title,scale); sh.frame()
    ox = lv.pos[0] if lv.pos else X0+(DW-lv.W*Q)/2+1.35*inch
    oy = lv.pos[1] if lv.pos else Y1 - lv.D*Q - 1.85*inch
    p = draw_level(c,lv,ox,oy)
    draw_the_surround(p,lv.W,lv.D,ox,oy,title,scale,lv.ctx,lv.units,lv.stair_side,lv.over_all)
    return p


class GreyPen:
    """A canvas that draws black as grey and the poche lighter still.

    The electrical sheets draw the architectural plan through it, so the devices read
    over a greyed background. Every call still reaches the real canvas, colors changed
    and nothing else, so the trace and the DXF see the same drawing.
    """
    def __init__(s, c): s._c = c
    def __getattr__(s, n): return getattr(s._c, n)
    @staticmethod
    def _g(col):
        if col == black: return GREY
        if col == POCHE: return LGREY
        return col
    def setFillColor(s, col, *a, **k):   return s._c.setFillColor(s._g(col), *a, **k)
    def setStrokeColor(s, col, *a, **k): return s._c.setStrokeColor(s._g(col), *a, **k)


def draw_level(c,lv,ox,oy,sc=Q):
    """Regrid, dimension, mirror and draw one level at a place on the page.

    Separate from plan_sheet because A-103 puts two levels side by side on one sheet:
    the sheet is framed once and this runs twice. Everything that is true of drawing a
    level is here; everything that is true of giving it a sheet of its own is there.

    `sc` is points per foot: the set's 1/4" unless a sheet asks for another. S-103
    draws its roof plans at 1/8" over the same greyed level the trade sheets use.
    """
    W,D,plan = lv.W,lv.D,lv.plan
    sep = lv.sep
    p=PlanDraw(c,ox,oy,sc,W,D)
    g = Geometry.from_level(lv)
    # Map the custom framing annotations with the same stud-face grid as the plan.
    # Their stated span is the actual clear distance between the mapped bearing faces.
    # A vertical entry (a, x, b, prefix, 'v') maps its run through the y map and the
    # x it stands at through the x map of the band it crosses.
    g = g.replace(joists=[((plan.y(a),plan.x(at,(a+b)/2.0),plan.y(b),prefix,'v')
                           if j[4:5]==('v',) else
                           (plan.x(a,at),plan.y(at),plan.x(b,at),prefix))
                          for j in g.joists for (a,at,b,prefix) in (j[:4],)])
    # IN THE MODEL'S OWN COORDS, which is why it is taken before the regrid and carried
    # through both transforms: is_closet compares an opening against the rooms it was
    # authored beside, and after the regrid those have moved apart by a stud face.
    bypass_flags=[is_closet(o,g.rooms) for o in g.openings]
    g = g.regridded(plan,regrid_all)
    # Some chains dimension nominal-size objects rather than mapped wall faces. Their
    # starts follow the stud grid, but a 3'-0" door or window remains exactly 3'-0";
    # add those already-gridded chains here so their far edges are not stretched again.
    g = g.replace(openareas=net_areas(g.openareas),
                  chains=list(g.chains)+list(lv.fixed_chains))
    rooms,openareas,openings,furn,doors = g.rooms,g.openareas,g.openings,g.furn,g.doors
    chains,dims = g.chains,g.dims
    if lv.full_dims:
        chains = closet_ticks_removed(chains,rooms,openareas,openings,bypass_flags)
    _skip = {} if not lv.room_dim_skip else dict(skip=('CL.','STOR.','MECH','STORAGE','HALL')+lv.room_dim_skip)
    chains = list(chains)+room_dims(rooms,openareas,chains,furn,doors,**_skip)
    if lv.full_dims:
        chains = (list(chains)
                  + (closet_dims(rooms,openareas,chains) if lv.closet_dims else [])
                  + closet_opening_dims(rooms,openareas,chains,openings))
        # in plan coordinates still, so mdims mirrors it with everything else
        dims = list(dims)+wc_dims(rooms,openareas,furn,lv.wall_finish)
    g = g.replace(chains=chains,dims=dims).mirrored(W,mirror_everything)
    if lv.overlay:
        # the background of a trade plan: the plan and the project's own drawing
        # in grey, none of the annotation, then the trade's work with the real pen
        p.c = GreyPen(c)
        draw_the_plan(p,W,sc,g,sep,bypass_flags,lv.over_plan,lv.captions,lv.sep_rows,lv.marks_last)
        if lv.over_dims: lv.over_dims(p)
        p.c = c
        lv.overlay(p)
        if lv.labels_last:
            p.c = GreyPen(c); p.labels(g.rooms, ground=True); p.c = c
        if lv.marks_last:
            p.c = GreyPen(c); _marks(p,g.wins); p.c = c
        return p
    draw_the_plan(p,W,sc,g,sep,bypass_flags,lv.over_plan,lv.captions,lv.sep_rows,lv.marks_last)
    draw_the_annotation(p,W,plan,g,lv.over_dims)
    if lv.marks_last: _marks(p,g.wins)
    return p


def _marks(p,wins):
    """Every window's mark on a white ground, drawn last (Level.marks_last)."""
    for (x,y,ln,o,mark) in wins: p.window_mark(x,y,ln,o,'W-'+mark,ground=True)

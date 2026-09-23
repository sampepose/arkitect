"""Dimension strings: turning a regridded plan into the lines that get printed.

A dimension string is not a list of numbers — it is a chain that has to CLOSE, run to
real faces, and not collide with what it dimensions. This module is the machinery for
that, and it is deliberately ignorant of this project: every function takes rects,
polygons and faces and returns spans.

    wall_faces / _spans   find the faces on one axis that a string should stop at
    strings               build the chain, dropping segments that cannot be shown
    carve / reanchor      split a chain around something in the way and re-anchor it
    unbridge / drop       remove a segment that bridges two faces, or one too small
    regrid_all            push a whole sheet's worth of geometry through a Plan
    room_dims             per-room overall dimensions, placed clear of the fittings
    closet_dims           reach-in depth and width
    closet_opening_dims   the D-5 bypass leaf, which reaches past the opening it slides on
    wc_dims               RCO 307.1, dimensioned the way the code measures it: ONE line
                          through the pan centerline to the obstruction on each side
"""
from arkitect.lib.units import fmt, inches
from arkitect.lib.model.regrid import PARTITION, PART_STUD
from arkitect.lib.symbols import LOOSE

# ---------------- dimension chains ----------------
REF       = 10.0      # how far an interior string may run to reach an exterior wall for

BYPASS_REACH = 0.15+0.13/2   # how far a D-5 leaf is drawn past the opening face it slides on

def _inside(pts,v,a,b,axis):
    return any(lo-1e-6<=a and b<=hi+1e-6 for (lo,hi) in _spans(pts,v,axis))

                      # reference. Beyond this the tick-free run stops reading as a
                      # dimension and starts reading as a stray line across the plan.
# Interior dimension strings are DERIVED from the same room rectangles and open-area
# polygons the plan is drawn from, so a wall cannot move without its dimension moving
# with it. `wall_faces` collects every wall face that crosses the given band; the chain
# then runs face to face, to face of stud, as plan note 1 requires.
def wall_faces(rects,polys,axis,band,ends):
    """(face, lo, hi) for every wall face on `axis` crossing `band` — the face, and the
       full extent of the wall that makes it. The extent is what tells a string whether
       that wall actually reaches the exterior beside it, and where to run the witness
       line back to."""
    ext={}
    def add(face,e0,e1):
        face=round(face,3)
        if face in ext:
            lo,hi=ext[face]; ext[face]=(min(lo,e0),max(hi,e1))
        else: ext[face]=(e0,e1)
    lo,hi=band
    for r in rects:
        a0,a1 = (r[0],r[0]+r[2]) if axis==0 else (r[1],r[1]+r[3])
        b0,b1 = (r[1],r[1]+r[3]) if axis==0 else (r[0],r[0]+r[2])
        if b1>lo+1e-6 and b0<hi-1e-6: add(a0,b0,b1); add(a1,b0,b1)
    for (pts,_l) in polys:
        for i,(px,py) in enumerate(pts):
            qx,qy=pts[(i+1)%len(pts)]
            if axis==0 and abs(px-qx)<1e-6 and max(py,qy)>lo+1e-6 and min(py,qy)<hi-1e-6:
                add(px,min(py,qy),max(py,qy))
            if axis==1 and abs(py-qy)<1e-6 and max(px,qx)>lo+1e-6 and min(px,qx)<hi-1e-6:
                add(py,min(px,qx),max(px,qx))
    lo_e,hi_e=min(ends),max(ends)
    return sorted((f,)+ext[f] for f in ext if lo_e-1e-6<=f<=hi_e+1e-6)

def _spans(pts,v,axis):
    """the intervals the polygon covers along `axis` at position v, even-odd"""
    xs=[]; n=len(pts)
    for i in range(n):
        a,b=pts[i],pts[(i+1)%n]
        p0,q0 = (a[1],b[1]) if axis==0 else (a[0],b[0])     # the cutting axis
        p1,q1 = (a[0],b[0]) if axis==0 else (a[1],b[1])     # the measured axis
        if p0==q0: continue
        if min(p0,q0)<=v<max(p0,q0): xs.append(p1+(v-p0)*(q1-p1)/(q0-p0))
    xs.sort()
    return [(xs[i],xs[i+1]) for i in range(0,len(xs)-1,2)]

def reanchor(cs,faces,at,tol=0.15):
    """A witness line runs from the tick out to the wall it marks. strings() works that
       out for the line it is building — nearest end of the wall, or none at all where
       the line already crosses it. Move the line afterwards and those anchors still
       point where they did: the witness reaches past the near end of the wall to the
       far one, and one gets drawn for a wall the new line sits on top of."""
    ext={round(f,4):(lo,hi) for (f,lo,hi) in faces}
    out=[]
    for (v,e) in cs:
        lo,hi = ext.get(round(v,4),(e,e))
        out.append((v, at if lo-tol<=at<=hi+tol else (lo if abs(lo-at)<abs(hi-at) else hi)))
    return out

def carve(ch,o,cut_lo,cut_hi,new_at,faces=()):
    """An 'in' sweep string sorts every wall face that reaches neither end onto one
       line by coordinate alone, with no regard for which column of the plan each
       face actually belongs to. Two faces that are architecturally unrelated — a
       closet's own jamb and some other wall three rooms over — can still land
       next to each other on it whenever their positions happen to coincide, and
       the reader has no way to tell that from a witness line alone: it reads as
       if the far wall's face broke the closet's own opening into two pieces.

       Pull whatever sits strictly between cut_lo and cut_hi off onto its own line
       at new_at instead. cut_lo and cut_hi themselves — the run's own two ends —
       stay on the original, which now closes on them directly: one span, stud to
       stud, same as if nothing else had ever shared its row."""
    lo,hi=round(cut_lo,4),round(cut_hi,4)
    out=[]
    for (cs,co,at,sd,ml,mk,la) in ch:
        if co!=o:
            out.append((cs,co,at,sd,ml,mk,la)); continue
        idx={round(f,4):k for k,(f,_e) in enumerate(cs)}
        if lo not in idx or hi not in idx or idx[hi]-idx[lo]<2:
            out.append((cs,co,at,sd,ml,mk,la)); continue
        i0,i1=idx[lo],idx[hi]
        out.append((cs[:i0+1]+cs[i1:],co,at,sd,ml,mk,la))
        out.append((reanchor(cs[i0:i1+1],faces,new_at),co,new_at,sd,ml,mk,la))
    return out

def unbridge(ch,faces,o,tol=0.15):
    """An interior string ticks only the walls in its own group, so a gap between two
       of its ticks can still have a wall standing across it. The number then spans a
       wall the string does not show: 10'-8-7/8" ran from a Unit 1 partition across the
       2-hour separation to a closet jamb, and 9'-2-1/8" from the bath wall across the
       bedroom demising wall to the other closet. Both true, neither of any use — you
       cannot lay out from either one.

       Split the string at those crossings instead, into runs that each stay on one
       side of every wall that crosses them. A wall that does not reach the string's
       own column is not a crossing: MECH's top face shares a y with Bedroom 2's
       closet run but stands three rooms west of it, and must not break that run."""
    out=[]
    for (cs,co,at,sd,ml,mk,la) in ch:
        if co!=o or not mk:
            out.append((cs,co,at,sd,ml,mk,la)); continue
        parts=[]; start=0
        for i in range(len(cs)-1):
            a,b=cs[i][0],cs[i+1][0]
            if any(a+1e-6<f<b-1e-6 and lo-tol<=at<=hi+tol for (f,lo,hi) in faces):
                parts.append(cs[start:i+1]); start=i+1
        parts.append(cs[start:])
        out+=[(p,co,at,sd,ml,mk,la) for p in parts if len(p)>1]
    return out

def drop(ch,o,at,faces,tol=1e-6):
    """Take named faces off one string, where another dimension already gives them and
       this string could only reach them across a room it does not serve. The bath's
       south wall is the case: its position is the bath's own 7'-3", and the interior
       string reached it with a 3'-6" witness over the bedroom, printing the leftover —
       0'-8-7/8" from the closet jamb to a wall in another room. The far face of that
       wall is a partition beyond a dimensioned one and derives from it, the same as a
       closet's stud wall."""
    out=[]
    for (cs,co,cat,sd,ml,mk,la) in ch:
        if co==o and abs(cat-at)<1e-6:
            cs=[p for p in cs if not any(abs(p[0]-f)<tol for f in faces)]
        if len(cs)>1: out.append((cs,co,cat,sd,ml,mk,la))
    return out

def strings(faces,ends,span,o,plan,tol=0.15):
    """Build the dimension strings for one axis.
       faces  (face, lo, hi) — the wall face and the extent of the wall that makes it.
       ends   the two exterior faces; every string terminates on them, so every string
              closes on the overall.
       span   the extremes across the string's axis — how far a wall must run to count
              as reaching the exterior.
       plan   (group, at, sd, side) entries. group is 'lo', 'hi' or 'in': walls that
              reach the low end, the high end, or neither. side says which end the
              string sits beyond, and so which end of a wall its witness line runs to.
       A group not asked for falls into 'in'; a string carrying nothing but the two
       exterior faces is not drawn."""
    E={round(e,3) for e in ends}
    endf=[fr for fr in faces if round(fr[0],3) in E]
    s0,s1=min(span),max(span); want={p[0] for p in plan}
    grp={'lo':[fr for fr in faces if fr[1]<=s0+tol] if 'lo' in want else [],
         'hi':[fr for fr in faces if fr[2]>=s1-tol] if 'hi' in want else []}
    grp['in']=[fr for fr in faces if fr not in grp['lo'] and fr not in grp['hi']]
    out=[]
    for (which,at,sd,side) in plan:
        items=sorted(set(grp[which])|set(endf))
        if len(items)<=len(endf): continue
        if side=='near':
            # the string runs INSIDE the plan: measure to whichever end of the wall is
            # nearer, and to the string itself for the walls it crosses, which is most
            # of them. Those ticks need no witness line at all.
            pick=lambda l,h,a=at: a if l-tol<=a<=h+tol else (l if abs(l-a)<abs(h-a) else h)
        else:
            pick=(lambda l,h: l) if side=='lo' else (lambda l,h: h)
        if side=='near':
            # an interior string closes on an exterior wall for reference, but only the
            # nearer one when the other is a long empty run across unrelated rooms
            inner=[x for x in items if round(x[0],3) not in E]
            if inner:
                gl=min(x[0] for x in inner)-items[0][0]
                gr=items[-1][0]-max(x[0] for x in inner)
                if max(gl,gr)>REF: items=items[:-1] if gr>gl else items[1:]
        out.append(([(f,pick(l,h)) for (f,l,h) in items],o,at,sd,PARTITION,side=='near',None))
    return out

def regrid_all(P,rooms=(),polys=(),doors=(),wins=(),ops=(),dims=(),notes=(),tags=None,
               furn=(),chains=()):
    return (tuple(P.rect(r) for r in rooms), P.poly(polys), tuple(P.span(d) for d in doors),
            tuple(P.span(w) for w in wins), tuple(P.span(o) for o in ops),
            tuple(P.dim(d) for d in dims), tuple(P.note(n) for n in notes),
            tuple(P.note(t) for t in tags) if tags else tags,
            tuple(P.keep(f) for f in furn),
            [P.chain(c) for c in chains])

def room_dims(rects,polys,chains,furn=(),doors=(),skip=("CL.","STOR.","MECH","STORAGE","HALL")):
    """A string dimensions every WALL. It does not necessarily dimension every ROOM: a
       run across a room is subdivided wherever another wall meets it at some other
       depth, so a bedroom 11'-0" wide behind a 2'-0" closet recess reads as 2'-0" plus
       9'-0" and never as 11'-0". This finds the rooms whose overall width or depth no
       string gives and returns a short dimension for each, drawn inside the room.
       The dimension is only emitted where the line actually lies within the room, so an
       L-shaped hall does not get a bounding-box depth it never has. Closets, stores and
       mechanical closets are skipped — their sizes are in the labels and plan note 15."""
    seg={'h':set(),'v':set()}
    for (cs,o,at,sd,ml,mk,la) in chains:
        for i in range(len(cs)-1): seg[o].add((round(cs[i][0],2),round(cs[i+1][0],2)))
    rooms=[]
    for r in rects:
        if len(r)>4 and r[4]:
            x0,y0,x1,y1 = r[0],r[1],r[0]+r[2],r[1]+r[3]
            rooms.append((r[4],x0,x1,y0,y1,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]))
    for (pts,labs) in polys:
        if len(labs)!=1: continue          # more than one label means an open area, and
        xs=[p[0] for p in pts]             # its bounding box is not a room
        ys=[p[1] for p in pts]
        rooms.append((labs[0][2],min(xs),max(xs),min(ys),max(ys),list(pts)))
    F=[f for f in furn if f[4] not in LOOSE]
    LBL=[]
    for r in rects:
        if len(r)>4 and r[4]:
            off = r[5] if len(r)>5 and isinstance(r[5],tuple) else (0.0,0.0)
            cx,cy=(r[0]+r[2]/2.0+off[0]),(r[1]+r[3]/2.0+off[1])
            LBL.append((cx-1.15,cy-0.42,2.30,0.84,'label'))
    for (pts,labs) in polys:
        for l in labs:
            LBL.append((l[0]-1.35,l[1]-0.55,2.70,1.10,'label'))
    # A doorway is not a fitting but it is not floor to put a number on either: the
    # bath's 5'-0" landed in its own entry, the one place on that line the fixtures
    # left clear. Block the approach on both sides so the label goes somewhere a
    # person is not walking.
    DR=[]
    for d in doors:
        dx,dy,dln,do = d[0],d[1],d[2],d[3]
        # the leaf's own length either side: that is the floor it sweeps, and on the
        # other side the floor you stand on to use it
        if do=='h': DR.append((dx,dy-dln,dln,2*dln,'door'))
        else:       DR.append((dx-dln,dy,2*dln,dln,'door'))
    F=list(F)+LBL+DR
    def clear(v,a,b,axis,m=0.45):
        for (fx,fy,fw,fh,*_r) in F:
            c0,c1 = (fy,fy+fh) if axis==0 else (fx,fx+fw)
            d0,d1 = (fx,fx+fw) if axis==0 else (fy,fy+fh)
            if c0-m<=v<=c1+m and not(d1<a-m or d0>b+m): return False
        return True
    def freeruns(v,a,b,axis):
        """the stretches of the line at v that no fitting sits on"""
        blocked=[]
        for (fx,fy,fw,fh,*_r) in F:
            c0,c1 = (fy,fy+fh) if axis==0 else (fx,fx+fw)
            d0,d1 = (fx,fx+fw) if axis==0 else (fy,fy+fh)
            if c0-0.45<=v<=c1+0.45: blocked.append((d0-0.3,d1+0.3))
        free=[]; cur=a
        for (b0,b1) in sorted(blocked):
            if b0>cur: free.append((cur,min(b0,b)))
            cur=max(cur,b1)
        if cur<b: free.append((cur,b))
        return [f for f in free if f[1]>f[0]]

    out=[]
    for (nm,x0,x1,y0,y1,pts) in rooms:
        if not nm or any(nm.startswith(k) for k in skip): continue
        for axis,a,b,lo,hi,o,sd in ((0,x0,x1,y0,y1,'h',1),(1,y0,y1,x0,x1,'v',-1)):
            if (round(a,2),round(b,2)) in seg[o]: continue
            span=hi-lo
            # from each wall inward, then across the room. Score every position that is
            # inside the room by the longest run of it clear of fittings, and take the
            # best — a bathroom is lined with fixtures, so the position that leaves room
            # for the number is not usually the first one that fits.
            best=None
            for i,v in enumerate([hi-0.6,lo+0.6,hi-1.0,lo+1.0,hi-1.6,lo+1.6,
                                  lo+span/3.0,lo+2*span/3.0,lo+span/2.0]):
                if not(lo<v<hi) or not _inside(pts,v,a,b,axis): continue
                runs=freeruns(v,a,b,axis)
                score=max((r[1]-r[0] for r in runs),default=0.0)
                if best is None or score>best[0]+1e-6: best=(score,i,v,runs)
            # A small wet room can have no good position at all — fixtures down one
            # side, the door swing across the other, its own label in the middle. The
            # bath's 5'-0" had nowhere to go but its own doorway. Fall back to just
            # outside the room, where a dimension for a room like that usually goes.
            if best is None or best[0]<1.6:
                for v in (hi+0.6,lo-0.6):
                    runs=freeruns(v,a,b,axis)
                    score=max((r[1]-r[0] for r in runs),default=0.0)
                    if score>=1.6 and (best is None or score>best[0]+1e-6):
                        best=(score,99,v,runs)
            if best is None: continue
            score,_i,v,runs = best
            labat=None
            # only slide the label when the line runs THROUGH the room and has to dodge
            # something. A line placed outside it reads as the room's overall, and the
            # number belongs centred on it.
            if _i!=99 and score < b-a-1e-6 and runs:      # the line crosses something
                w0,w1=max(runs,key=lambda r:r[1]-r[0])
                if w1-w0>1.3: labat=(w0+w1)/2.0
            out.append(([(a,v),(b,v)],o,v,sd,0.0,True,labat))
    return out

def closet_dims(rects,polys,chains=()):
    """A reach-in closet is casework, so it carries no room label and room_dims skips it.
       Its depth still has to be legible AT the closet rather than only on the outer
       string, so give each one its own short dimension across its shallow axis, set
       just clear of the stud wall that forms it and on the side the room is. The label
       then falls on the far side of the line from the wall.

       Skipped where a wall string already gives the same span close enough to read as
       the same dimension — printing it twice a few points apart is just two numbers on
       top of each other. A copy out on the far ring is not a duplicate: that is the
       whole reason for putting one at the closet.

       Placed where the neighbouring space is a real room: a closet stacked against
       another closet (Unit 1's CL. over its STOR.) has nowhere to put the line and gets
       none — its depth still reads on the outer string."""
    # PROBE clears a 3-1/2" partition but not a 5-1/2" exterior wall or the 8"
    # separation, so a closet face that sits on a rated or exterior assembly finds no
    # room on that side and the line never lands in the neighbouring unit.
    OFF, PROBE, NEAR = PART_STUD+0.10, 0.44, 1.5
    have=set()
    for (cs,o,at,sd,ml,mk,la) in chains:
        for i in range(len(cs)-1):
            have.add((o,round(cs[i][0],3),round(cs[i+1][0],3),round(at,3)))
    solid=[r for r in rects if r[4] not in ("CL.","STOR.")]
    def inside(px,py):
        for (x,y,w,h,*_) in solid:
            if x-1e-6<=px<=x+w+1e-6 and y-1e-6<=py<=y+h+1e-6: return True
        for (pts,_l) in polys:
            n=len(pts); k=False
            for i in range(n):
                x0,y0=pts[i]; x1,y1=pts[(i+1)%n]
                if (y0>py)!=(y1>py) and px < x0+(py-y0)*(x1-x0)/(y1-y0): k=not k
            if k: return True
        return False
    out=[]
    for r in rects:
        if r[4]!="CL.": continue
        x,y,w,h=r[:4]
        cx=x+w/2.0
        for (f,d) in ((y,-1),(y+h,1)):
            if not inside(cx,f+d*PROBE): continue
            at=f+d*OFF                       # clear of the stud wall, not of the closet
            if not inside(cx,at): continue   # the wall is thicker than a partition here
            if any(o=='h' and abs(a0-x)<1e-3 and abs(b0-(x+w))<1e-3 and abs(t-at)<NEAR
                   for (o,a0,b0,t) in have): break
            out.append(([(x,at),(x+w,at)],'h',at,-d,0.0,True,None))
            break
    return out

def closet_opening_dims(rects,polys,chains=(),openings=()):
    """closet_dims gives a reach-in's depth its own reading at the closet. The
       bypass door's own width — the run along the closet's long axis, jamb to
       jamb — needs the same treatment: without it, a reader has to add numbers
       off two different strings to find a figure that never appears on the
       drawing as one. Worse, an 'in' sweep string sorts its faces by coordinate
       alone, so an unrelated wall three rooms over can land between those two
       jambs purely by coincidence and read as if it broke the opening in half.

       Skipped, like closet_dims, where a string already gives the same span within
       1.5 ft — which is how the two Units 2/3 bedrooms end up reading off one line:
       Bedroom 2's run is on the interior string, Bedroom 1's is not, so only Bedroom 1
       needs its own, and OFF puts it on top of the string Bedroom 2 uses."""
    # clear of the DOOR, not just of the wall: the D-5 leaves are drawn past the
    # opening face by BYPASS_REACH, and a line set only clear of the stud lands in
    # the slot between the two panels, reading as part of the door assembly.
    OFF, PROBE, NEAR = BYPASS_REACH+3*PART_STUD, 0.44, 1.5
    have=set()
    for (cs,o,at,sd,ml,mk,la) in chains:
        for i in range(len(cs)-1):
            have.add((o,round(cs[i][0],3),round(cs[i+1][0],3),round(at,3)))
    solid=[r for r in rects if r[4] not in ("CL.","STOR.")]
    def inside(px,py):
        for (x,y,w,h,*_) in solid:
            if x-1e-6<=px<=x+w+1e-6 and y-1e-6<=py<=y+h+1e-6: return True
        for (pts,_l) in polys:
            n=len(pts); k=False
            for i in range(n):
                x0,y0=pts[i]; x1,y1=pts[(i+1)%n]
                if (y0>py)!=(y1>py) and px < x0+(py-y0)*(x1-x0)/(y1-y0): k=not k
            if k: return True
        return False
    def door_sides(x,y,w,h,tol=PART_STUD/2+0.05):
        """which face of this closet carries its bypass door, as +1 east / -1 west.
           A blind side can face a real room too — Bedroom 1's closet backs onto the
           bath — so the room probe alone would happily dimension the wrong face."""
        s=[]
        for op in openings:
            if len(op)<4 or op[3]!='v': continue
            ox,oy,ln=op[0],op[1],op[2]
            if oy<y-0.05 or oy+ln>y+h+0.05: continue
            if   abs(ox-x)     <=tol: s.append(-1)
            elif abs(ox-(x+w))<=tol: s.append(1)
        return s
    out=[]
    for r in rects:
        if r[4]!="CL.": continue
        x,y,w,h=r[:4]
        if not w<h: continue             # only closets whose long axis is the opening
        cy=y+h/2.0
        for d in door_sides(x,y,w,h):
            f = x if d<0 else x+w
            if not inside(f+d*PROBE,cy): continue
            at=f+d*OFF
            if not inside(at,cy): continue
            if any(o=='v' and abs(a0-y)<1e-3 and abs(b0-(y+h))<1e-3 and abs(t-at)<NEAR
                   for (o,a0,b0,t) in have): break
            # label to the same side as the interior string this line shares, so two
            # identical closets do not read with their numbers on opposite sides of it
            out.append(([(y,at),(y+h,at)],'v',at,d,0.0,True,None))
            break
    return out

def wc_dims(rects,polys,furn=(),finish=0.0):
    """RCO 307.1 wants 15" from a water closet's centerline to any wall or fixture
       either side. Dimension it the way the code measures it: ONE line, from the
       obstruction on one side, through the centerline, to the obstruction on the
       other. Two separate lines cannot show a centerline — they show two, a stagger
       apart, and the reader has to take on faith that they are the same one.

       The line runs THROUGH the pan, over its own symbol, which is where a reader
       looks for it and how it is drawn by hand. The pan's symbol is symmetric about
       its footprint, so the middle of the footprint is the centerline. Obstructions
       are whatever else stands along the same wall — the tub and the vanity here —
       falling back to the room if nothing does.

       THIS ONE DIMENSION IS TO FINISHED SURFACES, not to the stud faces the rest of
       the plan is dimensioned to: `finish` is the wall's finish thickness and
       wc_clearances() takes it off a wall bound. The sheet's general note says which,
       because a reader who applies the sheet's own stud-face convention to this line
       would deduct the finish a second time.

       Written in inches, not feet and inches: the minimum it answers to is quoted as
       15", so 16-1/2" reads against it and 1'-4-1/2" does not. Two dims sharing one
       `at` draw as a single line with a tick at each end and at the centerline they
       meet on; in inches the numbers are short enough to sit on their own segments."""
    out=[]
    for m in wc_clearances(rects,polys,furn,finish):
        out.append((m['lo'],m['cl'],m['o'],m['at'],inches(m['cl']-m['lo'])))
        out.append((m['cl'],m['hi'],m['o'],m['at'],inches(m['hi']-m['cl'])))
    return out


def wc_clearances(rects,polys,furn=(),finish=0.0):
    """What RCO 307.1 actually measures, for every water closet in `furn`.

       ONE MEASUREMENT, two readers. wc_dims() turns these into the dimension the sheet
       prints and src/clearances.py asserts the same numbers against the code minimum.
       They used to be different things: the sheet measured and printed a figure, the
       code minimum lived in prose, and nothing ever compared the two -- the water
       closet symbol's own docstring said the clearances were "checked in build.py, not
       drawn here" and nothing in build.py checked them.

       Each entry: the fixture, the pan centerline `cl`, the obstruction `lo` and `hi`
       either side of it along its wall, and where the dimension runs. The two
       clearances RCO 307.1 asks for are cl-lo and hi-cl.

       `finish` IS WHY A ROOM RECTANGLE IS NOT AN OBSTRUCTION. A room rectangle is the
       stud face -- that is the convention the rest of the plan is dimensioned in -- and
       307.1 measures to the wall, which is the stud face plus its finish. A fixture
       needs no such deduction: it stands in the room with its finished face where the
       model draws it. So each side starts at the FINISHED wall face and a fixture takes
       it in from there, whichever is tighter. With `finish` left at 0 this measures what
       it measured before: the caller that passes nothing gets stud faces, and a project
       that has a finish passes it. A second project's Bath 1 was the case that made the
       difference matter -- a pan centered in the stud band read 15-1/4" to the hall
       wall and stood 14-3/4" off its drywall, under the 15" the sheet quoted beside it,
       while the 15-1/4" on its other side was to a shower and was true as drawn.

       A water closet in a room this cannot measure RAISES rather than being skipped. It
       used to `continue`, so a pan in a polygon room -- an open plan -- silently got no
       dimension and no check at all, which is the failure this whole function exists to
       prevent. `polys` is searched too now; it was accepted and ignored, while the
       caller passed the real open areas and believed they were looked at.
    """
    out=[]
    for f in furn:
        if len(f)<5 or f[4]!='wc': continue
        x,y,w,h = f[:4]
        face = f[5] if len(f)>5 else 'e'
        vert = face in ('e','w')                       # against a vertical wall
        lo0,hi0 = (y,y+h) if vert else (x,x+w)         # the pan, along its wall
        cl = (lo0+hi0)/2.0
        room=[r for r in rects if len(r)>4 and r[0]-1e-6<=x and x+w<=r[0]+r[2]+1e-6
                              and r[1]-1e-6<=y and y+h<=r[1]+r[3]+1e-6]
        if room:
            r=room[0]
            lo,hi = (r[1],r[1]+r[3]) if vert else (r[0],r[0]+r[2])
        else:
            box=[_poly_box(pts) for (pts,_l) in (polys or [])
                 if _poly_holds(pts,x,y,w,h)]
            assert box, (
                "a water closet at (%.3f, %.3f) stands in no room this can measure, so "
                "its required clearance can be neither dimensioned nor checked" % (x,y))
            bx0,by0,bx1,by1 = box[0]
            lo,hi = (by0,by1) if vert else (bx0,bx1)
        lo,hi = lo+finish, hi-finish       # the wall's finished face, not its stud face
        for g in furn:
            if g is f or len(g)<5: continue
            a0,a1 = (g[1],g[1]+g[3]) if vert else (g[0],g[0]+g[2])
            b0,b1 = (g[0],g[0]+g[2]) if vert else (g[1],g[1]+g[3])
            c0,c1 = (x,x+w) if vert else (y,y+h)              # the pan, off its wall
            if not (b0<c1-1e-6 and b1>c0+1e-6): continue      # not on this wall
            if a1<=lo0+1e-6: lo=max(lo,a1)
            if a0>=hi0-1e-6: hi=min(hi,a0)
        assert hi-lo>1e-6, (
            "a water closet at (%.3f, %.3f) has no measurable clear band" % (x,y))
        at = (x+w/2.0) if vert else (y+h/2.0)          # down the middle of the pan
        out.append({'fixture':f,'vert':vert,'cl':cl,'lo':lo,'hi':hi,
                    'at':at,'o':'v' if vert else 'h'})
    return out


def _poly_box(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return (min(xs),min(ys),max(xs),max(ys))


def _poly_holds(pts,x,y,w,h):
    x0,y0,x1,y1 = _poly_box(pts)
    return x0-1e-6<=x and x+w<=x1+1e-6 and y0-1e-6<=y and y+h<=y1+1e-6


def net_areas(polys):
    """Put the TRUE area on any open-area label that is alone on its polygon.

    A bedroom with a recessed reach-in is drawn as the room MINUS the closet and its
    framing — that is the "walls are gaps" convention — so its bounding box and its
    area differ by the closet and its framing. Printing the overall dimensions beside
    a gross area invites the reader to multiply, get a different number, and not know
    which is wrong. Where a polygon
    carries more than one label the split between them is a design statement rather
    than a measurement, so those are left exactly as written. A None dimension label
    requests overall dimensions from the same regridded polygon as the area.
    """
    out=[]
    for (pts,labs) in polys:
        if len(labs)==1 and len(labs[0])>4 and str(labs[0][4]).endswith("SF"):
            n=len(pts)
            a=abs(sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1] for i in range(n)))/2.0
            width=max(p[0] for p in pts)-min(p[0] for p in pts)
            depth=max(p[1] for p in pts)-min(p[1] for p in pts)
            bb=width*depth
            l=labs[0]
            dimensions="%s x %s"%(fmt(width),fmt(depth)) if l[3] is None else l[3]
            labs=[tuple(l[:3])+(dimensions,"%d SF%s"%(round(a)," NET OF CLOSET" if bb-a>1.0 else ""))
                  +tuple(l[5:])]
        out.append((pts,labs))
    return out

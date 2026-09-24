"""The stud-to-stud regrid: how a plan laid out on a 0.1 ft grid becomes framing.

The model is drawn on a 0.1 ft (1.2 in) grid with walls of 0.40 / 0.50 / 0.90 ft. Those
are finish-to-finish figures and none of them is a real assembly — the grouping
separation came out 10.8 in against a scheduled 9-1/4 in stud to stud. Plans are drawn
and dimensioned STUD TO STUD, so every wall face has to move in to its stud face and
land on a 1/8 in grid, with the rooms absorbing exactly what the walls give up so the
building keeps its overall size.

`Plan` is the result: a mapping from model coordinates to sheet coordinates, built per
ZONE rather than per building, because Unit 1's partitions sit in different places on
Level 1 and Level 2 and one map per building cannot put both levels' walls at 3-1/2".
Zones are pinned at the boundaries they share — the exterior walls and the separation —
so they compose into one consistent building.

Nothing here knows about this project. It takes rooms and polygons, and returns a map.
`_interp` goes model -> sheet; `_inv` goes back, for the few things that have to be
authored against geometry the regrid has already moved.
"""

PARTITION = 0.40      # interior partition thickness in the plan model, Type W2 on A-601

# ---------------- stud-to-stud regrid, 1/8 in ----------------
# Plans are drawn and dimensioned STUD TO STUD: framing is what is drawn, finishes are
# not. The model was laid out on a 0.1 ft (1.2 in) grid with walls of 0.40 / 0.50 / 0.90
# ft — finish-to-finish figures, none of them a real assembly. axis_map() rebuilds every
# coordinate so each wall is exactly its framing thickness and every face lands on a
# 1/8 in grid, with the rooms absorbing what the walls give up.
#
# The map is per ZONE, not per building: Unit 1's partitions sit in different places on
# Level 1 and Level 2, so one map per building cannot put both levels' walls at 3-1/2".
# Zones are pinned at the boundaries they share — the exterior walls and the separation —
# so they compose into one consistent building.
GRID      = 1.0/96.0     # 1/8 inch

EXT_STUD  = 5.5/12.0     # 2x6

PART_STUD = 3.5/12.0     # 2x4

def snap(v): return round(round(v/GRID)*GRID,6)

def axis_map(C,new_lo,new_hi,pins=None,tol=0.02,hold=()):
    """With pins, the axis is cut into independent runs at the pinned coordinates and
       each run is rebuilt on its own. That is how a room can be held at an exact size
       while the rest of the axis still absorbs what the walls give up."""
    if pins:
        C=sorted(set(round(c,4) for c in C))
        anchors=[(C[0],new_lo)]+[(round(k,4),v) for k,v in sorted(pins.items())]+[(C[-1],new_hi)]
        out={}
        for (a_old,a_new),(b_old,b_new) in zip(anchors,anchors[1:]):
            sub=[c for c in C if a_old-1e-9<=c<=b_old+1e-9]
            out.update(_axis_run(sub,a_new,b_new,tol,hold))
        return out
    return _axis_run(C,new_lo,new_hi,tol,hold)

def _axis_run(C,new_lo,new_hi,tol=0.02,hold=()):
    """Rebuild one axis of one zone. C is the sorted face list; a 0.40 ft gap is a
       partition and becomes PART_STUD exactly; every other gap is floor and takes a
       share of the slack. Cumulative positions are snapped, walls kept exact.

       `hold` names gaps that are a designed size rather than floor — a reach-in closet
       is 2'-0" deep because someone chose 2'-0", so it is held exact like a partition
       and takes no share of the slack. Without this the regrid stretches it to whatever
       the arithmetic leaves over, and the plan disagrees with the notes."""
    C=sorted(set(round(c,4) for c in C))
    gaps=[C[i+1]-C[i] for i in range(len(C)-1)]
    new=list(gaps); fixed=[False]*len(gaps)
    # Both a partition and a closet depth are SPANS to hold, not necessarily single
    # gaps: a wall serving another row of the zone can put a face between the two faces
    # of this one, and closets on different rows interleave. So hold the span total and
    # re-proportion the gaps it covers. Shortest first, and a span never disturbs a gap
    # an earlier one settled — that is what lets two walls that overlap in y both come
    # out 3-1/2", and two interleaved closets both come out 2'-0".
    spans =[(C[i],C[j],PART_STUD) for i in range(len(C)) for j in range(i+1,len(C))
            if abs(C[j]-C[i]-0.40)<tol]
    # a hold is (lo,hi) to keep the span at its own model size, or (lo,hi,target) to
    # keep it at a size the design names — a room whose fixtures set it, say, which the
    # model carries only nominally and the slack would otherwise be free to resize.
    spans+=[(h[0],h[1],snap(h[2] if len(h)>2 else h[1]-h[0])) for h in hold]
    for (ha,hb,target) in sorted(spans,key=lambda t:(t[1]-t[0],t[0])):
        idx=[i for i in range(len(gaps)) if ha-1e-9<=C[i] and C[i+1]<=hb+1e-9]
        free=[i for i in idx if not fixed[i]]
        if not idx or not free: continue
        remain=target-sum(new[i] for i in idx if fixed[i])
        share=sum(gaps[i] for i in free)
        if remain<=1e-9 or share<=1e-9: continue
        for i in free[:-1]: new[i]=snap(gaps[i]*remain/share)
        new[free[-1]]=snap(remain-sum(new[i] for i in free[:-1]))
        for i in free: fixed[i]=True
    slack=(new_hi-new_lo)-sum(new)
    floor=sum(gp for gp,f in zip(new,fixed) if not f)
    if floor>1e-9:
        new=[gp if f else gp+slack*gp/floor for gp,f in zip(new,fixed)]
    out={C[0]:snap(new_lo)}
    for i,gp in enumerate(gaps):
        out[C[i+1]] = snap(out[C[i]]+new[i])
    # land the far end exactly, taking any snapping residue out of the last floor gap
    if abs(out[C[-1]]-snap(new_hi))>1e-9:
        for i in range(len(gaps)-1,-1,-1):
            if not fixed[i]:
                d=snap(new_hi)-out[C[-1]]
                for j in range(i+1,len(C)): out[C[j]]=snap(out[C[j]]+d)
                break
    return out

def zone_faces(rects,polys,axis,lo,hi):
    """faces on `axis` belonging to geometry that lies inside [lo,hi] on the other axis"""
    out=set()
    for r in rects:
        o0,o1=(r[1],r[1]+r[3]) if axis==0 else (r[0],r[0]+r[2])
        if o1<=lo+1e-6 or o0>=hi-1e-6: continue
        out.update([r[axis],r[axis]+r[axis+2]])
    for (pts,_l) in polys:
        o=[p[1-axis] for p in pts]
        if max(o)<=lo+1e-6 or min(o)>=hi-1e-6: continue
        for p in pts: out.add(p[axis])
    return out

class Zone:
    def __init__(s,rects,polys,ylo,yhi,W,new_ylo,new_yhi,xpins=None,ypins=None,yhold=(),xhold=()):
        xs=zone_faces(rects,polys,0,ylo,yhi) | {0.5,W-0.5}
        ys=zone_faces(rects,polys,1,0.5,W-0.5) | {ylo,yhi}
        s.ylo,s.yhi=ylo,yhi
        # a closet's depth is casework at a chosen size, not leftover floor: hold it
        # so the slack cannot stretch a 2'-0" reach-in. The run is held only where the
        # design names it — yhold — because elsewhere it is genuinely whatever the two
        # walls either end of it leave.
        hx={(r[0],r[0]+r[2]) for r in rects if r[4]=="CL." and r[2]<r[3]} | set(xhold)
        hy={(r[1],r[1]+r[3]) for r in rects if r[4]=="CL." and r[3]<r[2]} | set(yhold)
        s.xm=axis_map({c for c in xs if 0.5<=c<=W-0.5},EXT_STUD,W-EXT_STUD,xpins,hold=hx)
        s.ym=axis_map({c for c in ys if ylo<=c<=yhi},new_ylo,new_yhi,ypins,hold=hy)
        s.xm[0.0]=0.0; s.xm[W]=W

def _inv(m,v):
    """the inverse of _interp: the model coordinate whose mapped position is v. The map
       is monotonic, so this is well defined. Anything placed against something the
       regrid has already moved — the exterior stair, and the openings under it — has to
       be authored through this or the map stretches it along with the rooms."""
    K=sorted(m); V=[m[k] for k in K]
    if v<=V[0]:  return round(K[0]-(V[0]-v),6)
    if v>=V[-1]: return round(K[-1]+(v-V[-1]),6)
    for i in range(len(K)-1):
        a,b=V[i],V[i+1]
        if a<=v<=b:
            t=(v-a)/(b-a) if b>a else 0.0
            return round(K[i]+t*(K[i+1]-K[i]),6)
    return v

def _interp(m,v):
    v=round(v,4)
    if v in m: return m[v]
    K=sorted(m)
    if v<K[0]:  return snap(m[K[0]]-(K[0]-v))
    if v>K[-1]: return snap(m[K[-1]]+(v-K[-1]))
    for i in range(len(K)-1):
        a,b=K[i],K[i+1]
        if a<=v<=b:
            t=(v-a)/(b-a) if b>a else 0.0
            return snap(m[a]+t*(m[b]-m[a]))
    return v

class Plan:
    """The zones of one drawing, plus the merged y map that spans them."""
    def __init__(s,zones,W,D):
        s.zones=zones; s.W=W; s.D=D
        s.ym={0.0:0.0, D:D}
        for z in zones: s.ym.update(z.ym)
    def zone(s,y):
        for z in s.zones:
            if z.ylo-0.5<=y<=z.yhi+0.5: return z
        return min(s.zones,key=lambda z:min(abs(y-z.ylo),abs(y-z.yhi)))
    def y(s,v):   return _interp(s.ym,v)
    def inv_y(s,v): return _inv(s.ym,v)
    def inv_x(s,v,y): return _inv(s.zone(y).xm,v)
    def x(s,v,y): return _interp(s.zone(y).xm,v)
    def rect(s,r):
        y0,y1=s.y(r[1]),s.y(r[1]+r[3]); x0=s.x(r[0],r[1]); x1=s.x(r[0]+r[2],r[1])
        return (x0,y0,x1-x0,y1-y0)+tuple(r[4:])
    def poly(s,pa):
        out=[]
        for (pts,labs) in pa:
            out.append(([(s.x(a,b),s.y(b)) for (a,b) in pts],
                        [(s.x(l[0],l[1]),s.y(l[1]))+tuple(l[2:]) for l in labs]))
        return out
    def span(s,o):   return (s.x(o[0],o[1]),s.y(o[1]),o[2],o[3])+tuple(o[4:])
    def keep(s,f):   return (s.x(f[0],f[1]),s.y(f[1]))+tuple(f[2:])
    def note(s,n):   return (s.x(n[0],n[1]),s.y(n[1]))+tuple(n[2:])
    def dim(s,d):
        a,b,o,at,t=d[:5]                 # past the figure: dim()'s side and mask, carried as they are
        if o=="h": return (s.x(a,at),s.x(b,at),o,s.y(at),t)+tuple(d[5:])
        return (s.y(a),s.y(b),o,s.x(at,(a+b)/2.0),t)+tuple(d[5:])
    def chain(s,c):
        cs,o,at,sd,ml,mk,la=c
        if o=='h':
            cs2=[(s.x(f,at),s.y(e)) for (f,e) in cs]; at2=s.y(at)
            la2=None if la is None else s.x(la,at)
        else:
            cs2=[(s.y(f),s.x(e,f)) for (f,e) in cs]; at2=s.x(at,(cs[0][0]+cs[-1][0])/2.0)
            la2=None if la is None else s.y(la)
        # Suppress every partition-scale remainder through 4.8". Regridding can
        # make a nominal stud-wall gap read 4-3/8"; it is still wall construction,
        # not a usable opening dimension, and must not print as a stale segment.
        return (cs2,o,at2,sd,PARTITION,mk,la2)

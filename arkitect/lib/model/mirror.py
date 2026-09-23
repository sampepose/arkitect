"""Mirroring a model, one kind of object at a time.

A mirror has to reach everything at once — a door's handedness, a fridge's hinged edge,
the 'e'/'w' facing of a fitting, the 'lo'/'hi' ends of a dimension chain — so the danger
is never that a map is wrong, it is that one KIND of object gets left out and lands on
the far side of the plan from everything else. One wrapper per kind, and a caller that
uses them together, is what makes a missing one visible.

`on` defaults to mirroring. Which way a particular sheet faces is the project's to say;
this module only knows how to turn each kind of thing around.
"""
from arkitect.lib.symbols import LOOSE

def mrooms(rs,W,on=None):
    if not (True if on is None else on): return rs
    out=[]
    for r in rs:
        t=(W-(r[0]+r[2]),r[1],r[2],r[3])+tuple(r[4:])
        if len(t)>5 and isinstance(t[5],tuple): t=t[:5]+((-t[5][0],t[5][1]),)+t[6:]
        out.append(t)
    return out
def mdoors(ds,W,on=None):
    if not (True if on is None else on): return ds
    out=[]
    for d in ds:
        x,y,ln,o=d[0],d[1],d[2],d[3]; sw=d[4]; rest=tuple(d[5:])
        if o=='h':
            # A left-right mirror swaps which jamb is which, so the leaf hangs on the
            # other one — "far" has to toggle. Without it every horizontal door came
            # out with reversed handedness, and both leaves of a pair hinged on the
            # same jamb and were drawn one on top of the other.
            r = tuple(f for f in rest if f!="far") if "far" in rest else rest+("far",)
            out.append((W-(x+ln),y,ln,o,sw)+r)
        else:
            # a vertical door hinges along y, which a left-right mirror does not touch
            out.append((W-x,y,ln,o,-sw)+rest)
    return out
def mops(os_,W,on=None):
    if not (True if on is None else on): return os_
    return [((W-(o[0]+o[2]),o[1],o[2],o[3]) if o[3]=='h' else (W-o[0],o[1],o[2],o[3])) for o in os_]
def mwins(ws,W,on=None):
    if not (True if on is None else on): return ws
    return [((W-(w[0]+w[2]),w[1],w[2],w[3])+tuple(w[4:]) if w[3]=='h'
             else (W-w[0],w[1],w[2],w[3])+tuple(w[4:])) for w in ws]
def mnotes(ns,W,on=None):
    if on is not None and not on: return ns
    return [(W-n[0],)+tuple(n[1:]) for n in ns]
def mdims(ds,W,on=True):
    if not on: return ds
    out=[]
    for d in ds:
        a,bb,o,at,t=d
        out.append((W-bb,W-a,o,at,t) if o=='h' else (a,bb,o,W-at,t))
    return out
def mtags(ts,W,on=None):
    if on is not None and not on: return ts
    return [(W-t[0],t[1],t[2]) for t in ts]
def mpoly(pa,W,on=None):
    if on is not None and not on: return pa
    return [([ (W-x,y) for (x,y) in pts ],[ (W-l[0],)+tuple(l[1:]) for l in labs ]) for (pts,labs) in pa]
FL={'e':'w','w':'e'}
# Loose seating and dining are NOT drawn. They are the tenant's, not the contract's,
# and showing them invites the plan reviewer to read them as fixed. Beds stay because
# they prove a sleeping room takes a bed with its door swing clear; casework, appliances
# and plumbing fixtures stay because they are in the contract.
def mfurn(fs,W,on=None,drop_loose=True):
    if drop_loose: fs=[f for f in fs if f[4] not in LOOSE]
    if not (True if on is None else on): return fs
    # anything past field 5 names an edge the same way field 5 does — a fridge hinge —
    # so it mirrors on the same map. Rebuilding six fields wide silently dropped it.
    return [(W-(f[0]+f[2]),f[1],f[2],f[3],f[4],
             FL.get(f[5],f[5]) if len(f)>5 else 'n')
            + tuple(FL.get(v,v) for v in f[6:]) for f in fs]
def mchains(chs,W,on=True):
    """A horizontal chain mirrors its coordinates; a vertical chain keeps them but
       changes which side of the plan it sits on, so its label side flips too."""
    if not on: return chs
    out=[]
    for (cs,o,at,sd,ml,mk,la) in chs:
        # a horizontal string mirrors its faces but not its witness lines, which run
        # in y; a vertical string mirrors its witness lines but not its faces
        if o=='h': out.append((sorted((W-v,e) for (v,e) in cs),o,at,sd,ml,mk,None if la is None else W-la))
        else:      out.append(([(v,W-e) for (v,e) in cs],o,W-at,-sd,ml,mk,la))
    return out

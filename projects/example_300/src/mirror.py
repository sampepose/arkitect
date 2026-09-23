"""The two mirrors, and the wrappers that carry a whole model through them.

MIRROR is about the SHEET. Sage is the side street and S Elm is drawn at the top of
every plan, so a viewer standing in S Elm faces down the sheet and their right hand is
the sheet's left — which puts Sage on the left of every plan. Page x = 26 - raw x.

The Units 2/3 REFLECTION is about the BUILDING. It reflects every Units 2/3 x
coordinate about Building 1's centerline, so the living space, the kitchens, both
entries and the Unit 3 stair land on Sage and the two bedrooms land against the
adjacent parcel. Unit 1, the W4 common wall and Building 2 do not move.

The point of doing it here rather than by re-typing coordinates is that a mirror has to
reach everything at once: door handedness, fridge hinges, the 'e'/'w' facings of
fittings, the 'lo'/'hi' ends of a dimension chain. The m* wrappers apply a mirror to one
kind of model object; the r* wrappers are the same maps applied about Building 1's
centerline, so Units 2/3 are authored once from one end and reflected as a block.
"""
# Only the kinds that have an r* wrapper below. mdims, mchains and mstair used to be
# imported here too but no rdims/rchains/rstair was ever written, so they were dead.
from arkitect.lib.model.mirror import (mrooms, mdoors, mwins, mops, mnotes, mtags, mpoly,
                              mfurn)

# ---------------- orientation ----------------
# Sage Ave (side street) on the LEFT, adjacent parcel on the RIGHT,
# S Elm Ave at the FRONT (top of sheet), alley at the REAR (bottom).
# The sheet mirror is not a switch. S Elm is at the top of every plan, so a viewer
# standing in it faces DOWN the sheet and their right hand is the sheet's LEFT — which
# puts Sage, the side street on their right, on the LEFT of every plan. Setting it
# the other way does not give an alternative drawing, it gives a wrong one, so
# arkitect.lib.model.mirror simply mirrors and this project does not carry a flag for it.
# ---------------- Units 2 / 3 left-right reflection ----------------
# Units 2 and 3 are authored from the Unit 1 end of Building 1 and reflected about its
# centreline, so the living / dining, the kitchen L, both entries and the Unit 3 stair
# land on SAGE and the two bedrooms against the ADJACENT PARCEL. Unit 1, the W4
# common wall and Building 2 do not move.
#
# This used to be a REAR_MIRROR flag with an unmirrored alternative behind it, on the
# grounds that the decision might be reversed. It has not been and will not be: a 2024
# BZA case on this parcel (BZA24-080 — another applicant, another building; precedent
# only, see G-001) has Planning asking for street-facing entries and a stoop on the
# Sage facade, and Traffic Management requiring a new public sidewalk there. Fire
# separation distance on a street side is measured to the street centreline, RCO 202,
# so the stair on Sage needs no rated underside. The set is issued on that basis.
#
# The reflection stays because it is how these coordinates are WRITTEN — once, from one
# end, rather than twice — but it is no longer a switch, and nothing downstream asks
# which way round the building is.
B1_W = 26.0                        # Building 1 width; the reflection axis is B1_W/2
LIVE_SIDE = "SAGE"
BED_SIDE  = "ADJACENT-PARCEL"
LIVE_SIDE_YARD = "8'-0\" SIDE-STREET BUILDING LINE"
# ---- the Units 2 / 3 reflection, applied to the model before anything else sees it.
# Same maps as the sheet mirror above, so door handedness, fridge hinges and furniture
# facings all flip with the geometry rather than being re-authored by hand.
rrooms = lambda rs: mrooms(rs,B1_W,True)
rdoors = lambda ds: mdoors(ds,B1_W,True)
rwins  = lambda ws: mwins(ws,B1_W,True)
rops   = lambda os_: mops(os_,B1_W,True)
rnotes = lambda ns: mnotes(ns,B1_W,True)
rtags  = lambda ts: mtags(ts,B1_W,True)
rpoly  = lambda pa: mpoly(pa,B1_W,True)
rfurn  = lambda fs: mfurn(fs,B1_W,True,drop_loose=False)
def rx(v):
    """a single x coordinate — a wall face, a pin, a note anchor"""
    return B1_W-v
def rxw(v,w):
    """the low edge of something w wide whose low edge is at v"""
    return B1_W-v-w
def rpts(pts):
    """a bare polygon point list, no labels"""
    return [(B1_W-a,b) for (a,b) in pts]
def rspan(lo,hi,*rest):
    """a (lo,hi) or (lo,hi,target) hold span"""
    return (B1_W-hi,B1_W-lo)+rest
def rjoist(j):
    a,y,b,label = j
    return (B1_W-b,y,B1_W-a,label)

"""Does the thing that is scheduled FIT where it is drawn?

The model checks in a project answer to code tables: a header is the size its table gives,
a cap is three feet from an opening. None of that says the header is shallower than the
wall over its window. Two projects scheduled 2-2x12 and 3-2x10 headers over openings whose
heads left six inches under the double top plate, for days, with every oracle green —
because each check measured the rule and none measured the room.

These are the checks that measure the room. They are pure geometry and know no project,
no jurisdiction and no sheet: a project hands them its own figures and prints what comes
back. Feet throughout, as everywhere else.

    header_fit()        a header's depth against the height between the opening's head and
                        the underside of the top plates
    lvl_violations()    a laminated-veneer header's bending, shear and deflection under a
                        line load — a plausibility check, never the design
    across_opening()    something mounted along a wall (a wall head, a cabinet) against the
                        openings of its own level
    rises_at_opening()  something rising in or at a wall (a stack, a riser) against the
                        openings of every level it passes
    along_wall_gap()    two things on one wall, along it
    cavity_clear()      what a bay has left once its widest FITTING and its insulation are
                        in it -- never measured at the straight pipe, which is not the
                        widest thing on any DWV line
    cavity_violations() whether the detail closes, and how much deeper the bay must be
"""
from collections import namedtuple
from lib.units import IN

# Dressed depths of sawn lumber, by the nominal size a header schedule names.
LUMBER_DEPTH = {'2x4': IN(3.5), '2x6': IN(5.5), '2x8': IN(7.25), '2x10': IN(9.25), '2x12': IN(11.25)}
TOP_PLATES = IN(3.0)                 # a double top plate
FLAT_2X4 = IN(1.5)                   # the single flat member a non-bearing opening takes

# An opening as these checks see it: along its wall, and above the datum the caller uses.
Opening = namedtuple('Opening', 'lo hi zlo zhi name')


def lumber_depth(size):
    """'2-2x10' or '3-2x12' -> the depth of one ply."""
    return LUMBER_DEPTH[size.split('-')[-1]]


def header_room(plate, heads, top_plates=TOP_PLATES):
    """The least height between an opening's head and the underside of the top plates.
       `plate` is the top of the wall's plate and `heads` the openings' heads, all above
       the same floor."""
    return plate-max(heads)-top_plates


def header_fit(depth, room, tol=1e-9):
    """True when a header `depth` deep stands in `room`."""
    return depth <= room+tol


def lvl_violations(plf, opening, width, depth, fb, fv, e, deflection=360, bearing=IN(1.5)):
    """Every way a rectangular engineered header `width` x `depth` (feet) fails under a
       uniform `plf` over `opening` plus `bearing` at each end: allowable bending `fb` and
       shear `fv` in psi, modulus `e` in psi, total-load deflection L/`deflection`."""
    L = opening+2*bearing
    b, d = width*12.0, depth*12.0
    S, A, I = b*d*d/6.0, b*d, b*d**3/12.0
    v = []
    if plf*L*L/8.0*12.0 > fb*S:
        v.append('bending %.0f ft-lb over %.0f' % (plf*L*L/8.0, fb*S/12.0))
    if plf*L/2.0 > fv*A*2.0/3.0:
        v.append('shear %.0f lb over %.0f' % (plf*L/2.0, fv*A*2.0/3.0))
    defl = 5.0*(plf/12.0)*(L*12.0)**4/(384.0*e*I)
    if defl > L*12.0/deflection:
        v.append('deflection %.2f" over L/%d' % (defl, deflection))
    return v


def across_opening(center, length, openings, clear=0.0):
    """The openings a thing `length` long, centered at `center` along the wall, shares
       wall with, holding `clear` off each jamb. Pass the openings of ITS level only."""
    lo, hi = center-length/2.0, center+length/2.0
    return [op for op in openings if lo < op.hi+clear-1e-9 and op.lo-clear < hi-1e-9]


def rises_at_opening(along, openings, clear=0.0):
    """The openings, on any level, that a thing rising at `along` on the wall would pass
       through or within `clear` of."""
    return [op for op in openings if op.lo-clear-1e-9 < along < op.hi+clear+1e-9]


def on_level(openings, floor, storey):
    """The openings whose sill or threshold stands in the storey that starts at `floor`."""
    return [op for op in openings if floor-1e-6 <= op.zlo < floor+storey-1e-6]


def along_wall_gap(a, b):
    """The distance along a wall between two positions on it."""
    return abs(a-b)


# A pipe standing in a stud cavity, and what the assembly schedule says fills that cavity.
# `od` is the pipe's OUTSIDE diameter, not the size it is called: a "3 inch" DWV pipe is
# 3-1/2" across, which is most of a 2x6. `fitting` is the widest thing on that line -- a hub,
# a coupling, the sanitary tee at a connection -- which is what the bay actually has to clear
# and is ALWAYS the governing figure; `added` is any depth this bay has beyond the wall's typical cavity -- deeper
# studs, not furring, where the wall is a listed assembly whose board attaches to its studs;
# `fill` is the thickness of what the schedule puts behind the pipe and `fill_name` what to
# call it in the finding.
InCavity = namedtuple('InCavity', 'name od fitting depth added fill fill_name')


def cavity_depth(item):
    """The bay's whole depth, the stud cavity plus anything furred on the room side."""
    return item.depth+item.added


def cavity_clear(item):
    """What is left over once the FITTING and the fill are in the bay. Negative means the
       detail does not close: something has to give, and furring is usually what."""
    return cavity_depth(item)-item.fill-item.fitting


def cavity_deepening_needed(item):
    """The least a bay must be deepened beyond the wall's typical cavity to hold its fill and
       its widest fitting. Zero where the typical cavity already does."""
    return max(0.0, item.fill+item.fitting-item.depth)


def cavity_violations(items):
    """Whether the widest fitting on each pipe fits its bay alongside what the assembly
       schedule puts behind it.

       This is the gap between two drawings that each look right alone: a plumbing note puts a
       stack in an exterior wall "with the cavity insulation between it and the sheathing", an
       assembly schedule fills that wall with a batt as thick as the whole cavity, and neither
       sheet can see the other. Nothing in a code table is violated -- the pipe is allowed
       there and the batt is the right batt -- so only the room says so.

       Measured at the FITTING and not the straight pipe, because the first version of this
       check measured the pipe and certified a bay with no room for a hub: 2" of insulation
       plus 3-1/2" of pipe is exactly a 2x6, which accommodates straight pipe and nothing
       else. A DWV line is mostly straight pipe and entirely governed by its fittings."""
    v = []
    for it in items:
        if it.fitting+1e-9 < it.od:
            v.append('%s: its fitting is given as %.2f in and its pipe as %.2f in; a hub is '
                     'never narrower than the pipe it receives' % (it.name, it.fitting*12, it.od*12))
            continue
        room = cavity_clear(it)
        if room < -1e-9:
            v.append('%s: its %.2f in fitting and the %.2f in %s behind it need %.2f in, and '
                     'the bay is %.2f in (%.2f in typical cavity, %.2f in added). Deepen it '
                     '%.2f in more, or take one of the two.'
                     % (it.name, it.fitting*12, it.fill*12, it.fill_name,
                        (it.fill+it.fitting)*12, cavity_depth(it)*12, it.depth*12,
                        it.added*12, (cavity_deepening_needed(it)-it.added)*12))
    return v


# ---------------------------------------------------------------- a door leaf and what it hits
# A door's SWING is the last piece of plan geometry nothing measured. A plan draws the arc and
# a reader sees it cross an appliance without registering it, because an arc crossing a
# rectangle is what a door symbol always looks like. The leaf is taken as a quarter disc
# centred on the hinge, radius the leaf's length, between the wall and perpendicular -- the
# whole region it passes through, not just where it ends up.
Leaf = namedtuple('Leaf', 'name hinge_x hinge_y x0 x1 y0 y1 length')
Obstruction = namedtuple('Obstruction', 'name x0 y0 x1 y1')


def leaf_quadrant(x, y, length, o, swing, far):
    """One leaf of a door drawn at (x, y) running `length` along `o` ('h' in x, 'v' in y), as a
       Leaf: the hinge and the box its quarter disc lies in. `swing` and `far` are the drawing's
       own, and `swing` is in CANVAS sense -- negative is increasing plan y -- because that is
       what a sheet passes in and a second convention here would only be a second bug."""
    if o == 'h':
        hx = x+length if far else x
        hy = y
        x0, x1 = (hx-length, hx) if far else (hx, hx+length)
        y0, y1 = (hy, hy+length) if swing < 0 else (hy-length, hy)
    else:
        hx = x
        hy = y+length if far else y
        y0, y1 = (hy-length, hy) if far else (hy, hy+length)
        x0, x1 = (hx, hx+length) if swing > 0 else (hx-length, hx)
    return Leaf('', hx, hy, x0, x1, y0, y1, length)


def leaf_overlap(leaf, obs):
    """How far into `obs` the leaf reaches, measured from the point of the obstruction nearest
       the hinge. Zero where the leaf never touches it."""
    ax0, ay0 = max(leaf.x0, obs.x0), max(leaf.y0, obs.y0)
    ax1, ay1 = min(leaf.x1, obs.x1), min(leaf.y1, obs.y1)
    if ax0 >= ax1-1e-9 or ay0 >= ay1-1e-9:
        return 0.0
    nx = min(max(leaf.hinge_x, ax0), ax1)
    ny = min(max(leaf.hinge_y, ay0), ay1)
    r = ((nx-leaf.hinge_x)**2+(ny-leaf.hinge_y)**2)**0.5
    return max(0.0, leaf.length-r)


def door_swing_violations(leaves, obstructions, tol=IN(1.0)):
    """Every leaf against everything standing on the floor it swings over.

       `tol` is the slack a plan may carry before it is worth saying -- an inch, because a
       symbol's arc and an appliance's drawn outline are both nominal. A working space is not
       an obstruction and the caller leaves it out: NEC 110.26 and RCO M1305.1 are about
       reaching the equipment, and an open door is not what they bar.

       One project's mechanical / laundry pair swung INTO its room over the washer, which
       stands across the last 9-1/2" of the opening, so the near leaf stopped at about 17
       degrees. The identical pair in the project it was copied from always swung out; the
       sign did not survive the wall being turned through ninety degrees when the plan was
       copied, and five oracles saw a door symbol."""
    v = []
    for leaf in leaves:
        for obs in obstructions:
            over = leaf_overlap(leaf, obs)
            if over > tol:
                v.append('%s sweeps %s by %.2f in: the leaf stops there'
                         % (leaf.name, obs.name, over*12))
    return v

"""RCO Chapter 15 (mechanical) as the dwellings here use it: Table M1505.4.3(1)'s whole-house
ventilation rates, M1502.4.5's dryer exhaust length with its elbow allowance, and the
distances a termination keeps from an opening (M1504.3, M1502.3) and from an outdoor unit.

A project hands these its own walls, openings, routes and unit types.
"""
import math
from arkitect.lib.units import IN


# RCO Table M1505.4.3(1): continuous whole-house mechanical ventilation, CFM, by the
# dwelling's floor area and bedroom count. Transcribed row by row.
_M1505_AREAS = (1500, 3000, 4500, 6000, 7500)


_M1505_ROWS = [(30, 45, 60, 75, 90), (45, 60, 75, 90, 105), (60, 75, 90, 105, 120),
               (75, 90, 105, 120, 135), (90, 105, 120, 135, 150), (105, 120, 135, 150, 165)]


def whole_house_cfm(bedrooms, area_sf):
    row = next((r for a, r in zip(_M1505_AREAS, _M1505_ROWS) if area_sf <= a), _M1505_ROWS[-1])
    col = 0 if bedrooms <= 1 else 1 if bedrooms <= 3 else 2 if bedrooms <= 5 else 3 if bedrooms <= 7 else 4
    return row[col]


# RCO M1502.4.5.1: 35'-0" of dryer duct, less Table M1502.4.5.1's allowance per fitting —
# 5'-0" for a 4" radius mitered 90-degree elbow, the conservative row.
DRYER_MAX, DRYER_ELBOW = 35.0, 5.0


CAP_R = IN(4)              # half an 8" wall cap: the clearance is to its opening, not its centre


def _dist(along, z, op):
    """Distance in the wall's plane from a point to the nearest point of an opening."""
    dx = max(op.lo-along, 0.0, along-op.hi)
    dz = max(op.zlo-z, 0.0, z-op.zhi)
    return math.hypot(dx, dz)


def nearest_opening(wall, along, z):
    """(distance, name) of the opening nearest a point on the wall."""
    return min(((_dist(along, z, op), op.name) for op in wall.openings), default=(float('inf'), 'no opening'))


def route_length(pts):
    """(physical length, elbows) of a polyline; a 2-D point is at z 0."""
    p3 = [tuple(q)+(0.0,)*(3-len(q)) for q in pts]
    segs = [tuple(b[i]-a[i] for i in range(3)) for a, b in zip(p3, p3[1:])]
    segs = [s for s in segs if math.hypot(*s) > 1e-9]
    length = sum(math.hypot(*s) for s in segs)
    elbows = 0
    for a, b in zip(segs, segs[1:]):
        cos = sum(x*y for x, y in zip(a, b))/(math.hypot(*a)*math.hypot(*b))
        if cos < 1-1e-6: elbows += 1
    return length, elbows


def dryer_equivalent(pts):
    L, n = route_length(pts)
    return L+n*DRYER_ELBOW


def dwelling(ut):
    """The levels of ONE dwelling of a unit type: a stacked type (Units 2/3, 4/5) lists
       one level per dwelling, Unit 1 both of its own."""
    return ut.levels[:1] if ut.stacked else ut.levels


def bedrooms(ut):
    """Sleeping rooms of one dwelling of a unit type, from its rooms and polygons."""
    names = [nm for lv in dwelling(ut) for nm in ([r[4] for r in lv.rooms]+[nm for _p, nm in lv.polys])]
    return [n for n in names if 'BEDROOM' in n.upper()]


# An outdoor unit draws its coil air through the back, against the wall, so a dryer cap
# on that wall drops lint into it from above and blows into it from beside. No RCO
# section sets a distance; the project holds ODU_TERM_CLR along the wall, whatever the
# height, and the manufacturer's clearance where greater.
def odu_gap(y0, length, along):
    """Along the wall, from a cap's opening at `along` to the nearer end of an outdoor
       unit standing from y0 for `length`; zero when the cap is over or under it."""
    return max(y0-(along+CAP_R), (along-CAP_R)-(y0+length), 0.0)


def terminations(*, levels, walls):
    """Every termination with its clearance to the nearest opening, and for a dryer its
       physical and equivalent lengths — the schedule M-101 and M-102 print."""
    rows = []
    for m in levels:
        for d in m.ducts:
            t = d.term
            if t.wall == 'ROOF':
                clr, near = None, 'ROOF CAP'
            else:
                clr, near = nearest_opening(walls[m.bldg][t.wall], t.along, t.z)
            L, n = route_length(d.pts)
            rows.append(dict(term=t, bldg=m.bldg, level=m.level, clr=clr, near=near, length=L, elbows=n,
                             equiv=(L+n*DRYER_ELBOW) if t.what == 'DRYER EXHAUST' else None, size=d.size))
    return rows


# ---------------- the controls, RCO 1103.1 ----------------
# 1103.1: at least one thermostat for each separate heating and cooling system. 1103.1.1:
# where the system is forced air, that thermostat is programmable. A control reads the air
# of the space it serves, so it stands on an interior wall of a served room and off the
# supply air; the geometry is each project's, this is the rule the projects call.
CONTROL_REG_CLR = 3.0             # a control off a supply register or a return grille
PROGRAMMABLE = 'PROGRAMMABLE, RCO 1103.1.1'


def control_violations(systems):
    """One control per system, in a room that system serves, on an interior wall, clear of
       its own supply air. Each system is a dict:
         name      what the sheets call it
         controls  [(x, y, room, on_exterior_wall)] -- the project's own coordinates
         served    the room names that system conditions
         air       [(x, y)] its registers and grilles, empty where it is ductless
    """
    v = []
    for s in systems:
        cs = s['controls']
        if len(cs) != 1:
            v.append('%s: %d thermostats, RCO 1103.1 asks one per system' % (s['name'], len(cs)))
        for x, y, room, on_exterior in cs:
            if room not in s['served']:
                v.append('%s: its thermostat stands in %s, which it does not serve'
                         % (s['name'], room or 'the open'))
            if on_exterior:
                v.append('%s: its thermostat stands on an exterior wall' % s['name'])
            for ax, ay in s.get('air', ()):
                if (x-ax)**2 + (y-ay)**2 < CONTROL_REG_CLR**2 - 1e-9:
                    v.append('%s: its thermostat is under %.1f ft of a register or grille'
                             % (s['name'], CONTROL_REG_CLR))
                    break
    return v

"""The mechanical model: what M-101 and M-102 draw, and the checks that run before they do.

Heating and cooling are by ductless heat pump — one outdoor unit per dwelling, a wall
head in every bedroom and living space — so there is no supply or return duct anywhere
in the project. What a mechanical plan has to PLACE here is exhaust: the bath fans that
also carry each unit's RCO 303.4 whole-house ventilation, the dryer ducts and Unit 1's
range hood. The water heaters are electric storage and vent nothing. Every termination
ends through a wall or the roof, and the code puts a distance between a termination and
the nearest opening — RCO M1504.3 for an exhaust opening and M1502.3 for a dryer, 3'-0"
to any opening into the building. The wall caps are placed BY that rule rather than
typed on a sheet, and check_mechanical() measures every one of them against every
opening on both levels of its wall before anything draws.

Heads, fans and rooms are read from src/electrical.py, so M-101 and E-101 cannot
disagree about where a device is; the dryer positions are the ones A-201, A-202 and A-203
already draw. Coordinates are FINAL SHEET FEET — page x = 26 minus the regridded
model x for Units 2/3 and Building 2, Unit 1's own page feet — and heights are feet
above finished grade, the elevations' datum.
"""
import math
from collections import namedtuple
from arkitect.lib.model import fit
from arkitect.lib.units import IN, fmt
from src import levels
from src.openings import WIN_GEOM
from src.electrical import (LEVEL_U1_L1, LEVEL_U1_L2, LEVEL_U23, LEVEL_U4, LEVEL_U5, NEC_UNITS, UNIT_1,
                            UNIT_23, UNIT_45)
from arkitect.codes.nec.dwelling import HABITABLE, room_of
from src.building1 import (ENTRY_LEFT, ENTRY_WIDTH, F_U23, LIVE_WALL_X, PLAN_L1, PLAN_L2,
                           REAR_Y, U1_DR_DUCT, U1_DR_TERM_Z, U23WIN_U2, U23WIN_U3,
                           U23_DR_TERM, U23_DUCT_RISE, U2_ENTRY, U3_ENTRY, W_STUD, Y_SEP_BOT,
                           Y_SEP_TOP, site_x, site_y, windows)
from arkitect.codes.ohio.rco import mechanical as rco_mech
from src.building2 import (B2_D, B2_DR_BAY, B2_W, F_B2, PLAN_B2, U5_DOOR_X0, U5_DOOR_X1, b2_wins)
from src.sitework import LOT_W, PARCEL_WALL_X, SAFF_WALL_X, SITE_BLDG, SITE_D, SVC_EQUIP
from arkitect.codes.ohio.rco.mechanical import (CAP_R, DRYER_ELBOW, DRYER_MAX, _dist, bedrooms, dwelling, odu_gap,
                                       whole_house_cfm)
from arkitect.codes.ohio.rco.mechanical import terminations


# ================================ the tables ================================


# RCO Table M1505.4.4: local exhaust rates, intermittent and continuous.
LOCAL_CFM = {'BATH': (50, 20), 'KITCHEN': (100, 25)}
# The boost the continuous fan's wall switch gives it — a design choice, at or over the
# bath's intermittent rate; Unit 1's fans are 80 CFM units. A-001 note 11 states these.
BOOST_CFM = {'UNIT 1': 80, 'UNITS 2 / 3': 50, 'UNITS 4 / 5': 50}
DRYER_PHYS_MAX = 12.0      # what A-001 note 16a promises of every unit's run
DRYER_OUT_Z = 4.0          # the stacked dryer's outlet above its floor — design assumption, M-101 says so
EXH_CLR = 3.0              # M1504.3 exhaust openings, M1502.3 dryer terminations
TERM_GAP = 3.0             # between two terminations on one wall, A-001 note 17's separation as a floor
ODU_TERM_CLR = EXH_CLR     # a dryer cap to an outdoor unit on its wall, along the wall: M-101 note 8
W4_ROOF_BAND = 4.0         # RCO 302.2.4 exception: no roof opening within 4'-0" of W4
CAV_Z = IN(6)              # a duct in the floor cavity leaves the wall this far above the top plate
SLEEVE_Z = 1.5             # the line-set sleeve above the outdoor unit's floor level
LINE_OFF = 0.6             # a line set or duct stands this far off its wall in plan

# ================================ the types ================================
# An opening in a wall, in feet ALONG the wall and feet above grade; a wall, by its
# name, which way it runs ('v' along page y at page x `at`, 'h' along page x), and its
# openings on both levels.
Opening = namedtuple('Opening', 'lo hi zlo zhi name')
Wall = namedtuple('Wall', 'name orient at lo hi openings')
# A termination: the mark printed beside it, what it is, the unit it serves, its wall
# (or 'ROOF'), its position along the wall (a plan point for a roof cap) and its height.
Term = namedtuple('Term', 'mark what unit wall along z')
# A run drawn on the plan: the termination it ends at and its polyline in page feet,
# each point (x, y) or (x, y, z); `size` is printed beside it.
Duct = namedtuple('Duct', 'term pts size')


def _win(lo, ln, ff, mk, name):
    sill, h = WIN_GEOM[mk]
    return Opening(lo, lo+ln, ff+sill, ff+sill+h, name)


def _door(lo, ln, ff, name):
    return Opening(lo, lo+ln, ff, ff+6.67, name)


def cap_position(wall, z, want, clr, taken=()):
    """The position along `wall` nearest `want` at which a cap at height z is at least
       `clr` from every opening in the wall and TERM_GAP from every termination already
       on it (`taken`, positions along the wall), inside the wall's extent. Raises when
       the wall has no such point — which is how the Units 4/5 rear wall answered."""
    lo, hi = wall.lo+CAP_R, wall.hi-CAP_R
    def legal(a):
        return (lo-1e-9 <= a <= hi+1e-9
                and all(_dist(a, z, op) >= clr+CAP_R-1e-9 for op in wall.openings)
                and all(abs(a-t) >= TERM_GAP-1e-9 for t in taken))
    cands = [want]
    for op in wall.openings:
        dz = max(op.zlo-z, 0.0, z-op.zhi)
        h = math.sqrt(max((clr+CAP_R)**2-dz*dz, 0.0))
        cands += [op.lo-h, op.hi+h]
    for t in taken:
        cands += [t-TERM_GAP, t+TERM_GAP]
    ok = [a for a in cands if legal(a)]
    if not ok:
        raise ValueError('%s: no position for a cap at %s that is %s from every opening' % (wall.name, fmt(z), fmt(clr)))
    return min(ok, key=lambda a: abs(a-want))


# ================================ the walls ================================
FF = {1: levels.FF1, 2: levels.FF2}


def b1_walls():
    """Building 1's four exterior walls and every opening in them, both levels."""
    saff, parcel, front, rear = [], [], [], []
    for lv in (1, 2):
        ff = FF[lv]
        for x, y, ln, o, mk in windows(lv):
            nm = 'UNIT 1 L%d W-%s' % (lv, mk)
            if o == 'v': (saff if x < 13 else parcel).append(_win(y, ln, ff, mk, nm))
            else: front.append(_win(x, ln, ff, mk, nm))
    front.append(_door(ENTRY_LEFT, ENTRY_WIDTH, FF[1], 'UNIT 1 DOOR'))
    for unit, plan, wins, door in ((2, PLAN_L1, U23WIN_U2, U2_ENTRY), (3, PLAN_L2, U23WIN_U3, U3_ENTRY)):
        ff = FF[unit-1]
        for x, y, ln, o, mk in wins:
            nm = 'UNIT %d W-%s' % (unit, mk)
            if o == 'v':
                (saff if abs(x-LIVE_WALL_X) < 1e-6 else parcel).append(_win(plan.y(y), ln, ff, mk, nm))
            elif abs(y-REAR_Y) < 1e-6:
                a = plan.x(x, REAR_Y); rear.append(_win(26.0-a-ln, ln, ff, mk, nm))
        saff.append(_door(plan.y(door[1]), door[2], ff, 'UNIT %d DOOR' % unit))
    return {'SAGE WALL': Wall('SAGE WALL', 'v', 0.0, 0.0, 48.0, sorted(saff)),
            'ADJACENT-PARCEL WALL': Wall('ADJACENT-PARCEL WALL', 'v', 26.0, 0.0, 48.0, sorted(parcel)),
            'S ELM WALL': Wall('S ELM WALL', 'h', 0.0, 0.0, 26.0, sorted(front)),
            'REAR WALL': Wall('REAR WALL', 'h', 48.0, 0.0, 26.0, sorted(rear))}


def b2_walls():
    saff, parcel, court, rear = [], [], [], []
    for unit, lv in ((4, 1), (5, 2)):
        ff = FF[lv]
        for x, y, ln, o, mk in b2_wins(lv):
            nm = 'UNIT %d W-%s' % (unit, mk)
            if o == 'v':
                (saff if x > 13 else parcel).append(_win(PLAN_B2.y(y), ln, ff, mk, nm))
            else:
                a = PLAN_B2.x(x, y)
                (court if y < 13 else rear).append(_win(B2_W-a-ln, ln, ff, mk, nm))
        court.append(_door(U5_DOOR_X0, U5_DOOR_X1-U5_DOOR_X0, ff, 'UNIT %d DOOR' % unit))
    return {'SAGE WALL': Wall('SAGE WALL', 'v', 0.0, 0.0, B2_D, sorted(saff)),
            'ADJACENT-PARCEL WALL': Wall('ADJACENT-PARCEL WALL', 'v', B2_W, 0.0, B2_D, sorted(parcel)),
            'COURTYARD WALL': Wall('COURTYARD WALL', 'h', 0.0, 0.0, B2_W, sorted(court)),
            'REAR WALL': Wall('REAR WALL', 'h', B2_D, 0.0, B2_W, sorted(rear))}


# How far each wall stands from the lot line it faces, for M1504.3's 3'-0" to a property
# line. Building 1's rear faces the 12'-0" gap and Building 2's the rear yard.
WALL_TO_LINE = {
    (1, 'SAGE WALL'): SAFF_WALL_X, (1, 'ADJACENT-PARCEL WALL'): LOT_W-PARCEL_WALL_X,
    (1, 'S ELM WALL'): SITE_BLDG[0][1], (1, 'REAR WALL'): SITE_D-(SITE_BLDG[0][1]+SITE_BLDG[0][3]),
    (2, 'SAGE WALL'): SAFF_WALL_X, (2, 'ADJACENT-PARCEL WALL'): LOT_W-PARCEL_WALL_X,
    (2, 'COURTYARD WALL'): SITE_BLDG[1][1]-(SITE_BLDG[0][1]+SITE_BLDG[0][3]),
    (2, 'REAR WALL'): SITE_D-(SITE_BLDG[1][1]+SITE_BLDG[1][3]),
}


# ================================ the units ================================
# One entry per dwelling unit AS DRAWN — Units 2 and 3 share one electrical level and
# differ only in their regrid and their floor; Units 4 and 5 likewise.
#   unit, name, building, level, the electrical Level, the regrid (None: already page
#   feet), the UnitType, the outdoor unit's mark, how its bath exhausts
# A Level 1 bath exhausts through a wall from the floor cavity above it; a Level 2 bath
# rises into the attic to a roof cap, at the offset given from the fan, away from W4.
EXHAUST = {
    1: ('WALL', 'ADJACENT-PARCEL WALL'),   # Bath 1: east through Bedroom 1's ceiling — the Sage wall here is the stair well
    2: ('WALL', 'ADJACENT-PARCEL WALL'),   # the solid run between the two bedroom windows, where HP-2 / HP-3 stand
    4: ('WALL', 'SAGE WALL'),           # between Bedroom 2's W-A and the closet's two caps
    3: ('ROOF', (0.0, 3.0)),               # toward the rear, away from W4
    5: ('ROOF', (0.0, -2.0)),
    6: ('ROOF', (0.0, -1.5)),              # Unit 1 Level 2, Bath 2: toward S Elm, away from W4
}
_UNITS = [
    # unit, name, building, level, elec level, plan, unit type, outdoor unit
    (1, 'UNIT 1 LEVEL 1', 1, 1, LEVEL_U1_L1, None, UNIT_1, 'HP-1'),
    (1, 'UNIT 1 LEVEL 2', 1, 2, LEVEL_U1_L2, None, UNIT_1, 'HP-1'),
    (2, 'UNIT 2', 1, 1, LEVEL_U23, PLAN_L1, UNIT_23, 'HP-2'),
    (3, 'UNIT 3', 1, 2, LEVEL_U23, PLAN_L2, UNIT_23, 'HP-3'),
    (4, 'UNIT 4', 2, 1, LEVEL_U4, PLAN_B2, UNIT_45, 'HP-4'),
    (5, 'UNIT 5', 2, 2, LEVEL_U5, PLAN_B2, UNIT_45, 'HP-5'),
]
_SWAP = {'e': 'w', 'w': 'e'}
_W = {1: 26.0, 2: B2_W}


def _pg(plan, W, x, y):
    """A regridded, mirrored unit's model point in page feet."""
    return (W-plan.x(x, y), plan.y(y))


def _box(mark, bldg):
    """An outdoor unit's C-101 rectangle in its building's page feet: (x, y, w, h)."""
    e = next(e for e in SVC_EQUIP if e[0] == mark)
    bx, by = SITE_BLDG[bldg-1][:2]
    return (e[1]-bx, e[2]-by, e[3], e[4])


class MLevel:
    """One dwelling unit's level, ready to draw: heads, fans, ducts, terminations,
       line sets and the outdoor unit, all in page feet."""
    def __init__(s, unit, name, bldg, level, elec, plan, utype, hp):
        s.unit, s.name, s.bldg, s.level, s.elec, s.plan, s.utype, s.hp = unit, name, bldg, level, elec, plan, utype, hp
        s.W = _W[bldg]
        s.ff = FF[level]
        s.heads, s.fans, s.ducts, s.terms, s.linesets, s.roofcaps = [], [], [], [], [], []
        s.hp_box = _box(hp, bldg)
        s.sleeve = None
        s.drop = None                      # where Level 2 line sets go down to a Level 1 sleeve

    def pg(s, x, y, mount=None):
        if s.plan is None:
            return (x, y) if mount is None else (x, y, mount)
        X, Y = _pg(s.plan, s.W, x, y)
        return (X, Y) if mount is None else (X, Y, _SWAP.get(mount, mount))


def _place_devices(m):
    for d in m.elec.devices:
        if d.kind == 'head':
            x, y, mt = m.pg(d.x, d.y, d.mount)
            m.heads.append((x, y, mt, room_of(d, m.elec)))
        elif d.kind in ('fanc', 'fan'):
            x, y = m.pg(d.x, d.y)
            m.fans.append((x, y, d.kind, room_of(d, m.elec), d.tag))


def _bath_exhaust(m, walls, marks):
    """Each bath fan's duct to its cap: through a wall for a Level 1 bath, through the
       roof for a Level 2 one. Returns the wall caps placed, by wall, for TERM_GAP."""
    how, where = EXHAUST[6 if (m.unit == 1 and m.level == 2) else m.unit]
    plate = levels.F2_PLATE if m.unit == 1 else levels.F1_PLATE
    for i, (fx, fy, kind, room, tag) in enumerate(sorted(m.fans, key=lambda f: f[4])):
        mark = 'EF-%d%s' % (m.unit, ('AB'[m.level-1] if len(m.fans) == 1 else 'AB'[i]) if m.unit == 1 else '')
        if how == 'WALL':
            wall = walls[where]
            z = plate+CAV_Z
            taken = [t.along for t in marks.get(where, [])]
            a = cap_position(wall, z, fy if wall.orient == 'v' else fx, EXH_CLR, taken)
            t = Term(mark, 'BATH EXHAUST', m.unit, where, a, z)
            pts = ([(fx, fy), (fx, a), (wall.at, a)] if wall.orient == 'v' else [(fx, fy), (a, fy), (a, wall.at)])
        else:
            dx, dy = where
            t = Term(mark, 'BATH EXHAUST', m.unit, 'ROOF', (fx+dx, fy+dy), None)
            pts = [(fx, fy), (fx+dx, fy+dy)]
            m.roofcaps.append(t)
        m.terms.append(t); marks.setdefault(t.wall, []).append(t)
        m.ducts.append(Duct(t, pts, '4"'))


def _b1_closet_x(m):
    """Units 2/3: page x of the dryer duct's rise (the model's, over the W/D, as A-202
       draws it), of the heater's center, and the rear wall's room face."""
    wh = next(f for f in F_U23 if f[4] == 'wh')
    a, b = m.pg(wh[0], wh[1])[0], m.pg(wh[0]+wh[2], wh[1])[0]
    return 26.0-U23_DUCT_RISE, (a+b)/2.0, m.plan.y(REAR_Y)


# How far over its floor the Units 2 / 3 dryer cap stands, high on the rear wall; A-201
# draws DR-2 and DR-3 from this, not from a typed height.
U23_DR_CAP_UP = 7.5


def _appliance_exhaust(m, marks):
    """The dryer duct of the unit's mechanical closet, to the cap the elevations already
       draw. The heaters are electric storage and vent nothing."""
    ff = m.ff; u = m.unit
    if u in (2, 3):
        x_rise, _x_wh, y_face = _b1_closet_x(m)
        x_cap = 26.0-U23_DR_TERM
        y_in = y_face-IN(5)                            # the duct on the room side of the rear wall
        z0, z1 = ff+DRYER_OUT_Z, ff+U23_DR_CAP_UP       # A-202: the dryer cap high on the wall
        dr = Term('DR-%d' % u, 'DRYER EXHAUST', u, 'REAR WALL', x_cap, z1)
        m.ducts.append(Duct(dr, [(x_rise, y_in-0.4, z0), (x_rise, y_in, z0), (x_rise, y_in, z1), (x_cap, y_in, z1), (x_cap, 48.0, z1)], '4"'))
    elif u in (4, 5):
        wdf = next(f for f in F_B2 if f[4] == 'wd')
        xa, xb = m.pg(wdf[0], wdf[1])[0], m.pg(wdf[0]+wdf[2], wdf[1])[0]
        x_mid = (xa+xb)/2.0
        y_cap = B2_DR_BAY[0]; z0 = ff+DRYER_OUT_Z
        dr = Term('DR-%d' % u, 'DRYER EXHAUST', u, 'SAGE WALL', y_cap, z0)
        m.ducts.append(Duct(dr, [(x_mid, y_cap+0.5, z0), (x_mid, y_cap, z0), (min(xa, xb), y_cap, z0), (0.0, y_cap, z0)], '4"'))
    else:                                              # Unit 1, Level 1: the model's route
        if m.level != 1: return
        dr = Term('DR-1', 'DRYER EXHAUST', 1, 'SAGE WALL', site_y(U1_DR_DUCT[0][1]), U1_DR_TERM_Z)
        m.ducts.append(Duct(dr, [(site_x(a), site_y(b), U1_DR_TERM_Z) for a, b in U1_DR_DUCT], '4"'))
    m.terms.append(dr); marks.setdefault(dr.wall, []).append(dr)


def _range_hood(m, walls, marks):
    """Unit 1's hood, straight through the adjacent-parcel wall behind the range; the
       other kitchens take recirculating hoods, M1503.3 exception."""
    if not (m.unit == 1 and m.level == 1): return
    wall = walls['ADJACENT-PARCEL WALL']
    y0, y1 = site_y(IN(15)), site_y(IN(45))            # the range, A-101
    z = m.ff+6.5
    a = cap_position(wall, z, (y0+y1)/2.0, EXH_CLR, [t.along for t in marks.get(wall.name, [])])
    assert y0 <= a <= y1, 'the Unit 1 hood cap is not behind its range'
    t = Term('RH-1', 'RANGE HOOD', 1, wall.name, a, z)
    m.terms.append(t); marks.setdefault(t.wall, []).append(t)
    m.ducts.append(Duct(t, [(site_x(W_STUD)-1.0, a), (wall.at, a)], '6"'))


def _linesets(m, sleeve_of):
    """Each head's line set to the unit's sleeve: off its wall, along to the trunk line
       on the sleeve's side, along that to the sleeve's position, out. Unit 1's Level 2
       heads end at the drop beside the stair, where Level 1 picks them up."""
    x, y, w, h = m.hp_box
    on_left = x < m.W/2.0
    sx = 0.0 if on_left else m.W
    sy = y+h/2.0
    m.sleeve = (sx, sy)
    inner = (IN(5.5) if m.unit == 1 else 0.5)
    tx = inner+LINE_OFF if on_left else m.W-inner-LINE_OFF
    off = {'n': (0, LINE_OFF), 's': (0, -LINE_OFF), 'e': (-LINE_OFF, 0), 'w': (LINE_OFF, 0),
           'w5': (0, LINE_OFF), 'w5s': (0, -LINE_OFF)}
    for hx, hy, mt, room in m.heads:
        dx, dy = off[mt]
        pts = [(hx, hy), (hx+dx, hy+dy), (tx, hy+dy), (tx, sy)]
        if m.unit == 1 and m.level == 2:
            m.drop = (tx, sy)
        else:
            pts.append((sx, sy))
        m.linesets.append([p for i, p in enumerate(pts) if i == 0 or math.hypot(p[0]-pts[i-1][0], p[1]-pts[i-1][1]) > 1e-9])
    if m.unit == 1 and m.level == 1:
        m.drop = (tx, sy)


def build():
    """Every level of every unit, placed and routed; the walls; the terminations by
       building. Runs once at import."""
    walls = {1: b1_walls(), 2: b2_walls()}
    marks = {1: {}, 2: {}}
    out = []
    for row in _UNITS:
        m = MLevel(*row)
        _place_devices(m)
        _appliance_exhaust(m, marks[m.bldg])
        _range_hood(m, walls[m.bldg], marks[m.bldg])
        _bath_exhaust(m, walls[m.bldg], marks[m.bldg])
        _linesets(m, None)
        out.append(m)
    return out, walls, marks


LEVELS, WALLS, TERMS = build()
B1_LEVELS = [m for m in LEVELS if m.bldg == 1]
B2_LEVELS = [m for m in LEVELS if m.bldg == 2]


# ================================ the schedules ================================
def _hp_circuit(ut):
    return next(c for c in ut.circuits if c.kind == 'hp')


def floor_area(ut):
    return next(u[1] for u in NEC_UNITS if u[0] == ut.name)


def outdoor_units():
    """One row per outdoor unit: mark, the unit it serves, its wall, MCA, MOCP, heads
       with their rooms. Units 2/3 and 4/5 share a circuit and a head list."""
    rows = []
    for m in LEVELS:
        if m.unit == 1 and m.level == 2: continue
        heads = [h for lv in (LEVELS if m.unit == 1 else [m]) if lv.unit == m.unit for h in lv.heads]
        ck = _hp_circuit(m.utype)
        x = m.hp_box[0]
        wall = 'SAGE' if x < 0 else 'ADJACENT PARCEL'
        rows.append(dict(mark=m.hp, unit=m.unit, wall=wall, mca=ck.mca, mocp=ck.mocp,
                         heads=[h[3] for h in heads]))
    return rows


def ventilation():
    """One row per unit type: bedrooms, area, the whole-house rate required and the
       continuous fan's rate, the boost, the bath intermittent minimum."""
    rows = []
    for ut in (UNIT_1, UNIT_23, UNIT_45):
        n = len(bedrooms(ut)); a = floor_area(ut)
        req = whole_house_cfm(n, a)
        rows.append(dict(name=ut.name, bedrooms=n, area=a, required=req, continuous=req,
                         boost=BOOST_CFM[ut.name], bath=LOCAL_CFM['BATH'][0]))
    return rows




def odu_clearances():
    """(outdoor unit, termination, gap) for every dryer cap on the wall of every
       outdoor unit, in that unit's building."""
    rows = []
    for m in LEVELS:
        if m.unit == 1 and m.level == 2: continue
        x, y, w, h = m.hp_box
        wall = 'SAGE WALL' if x < 0 else 'ADJACENT-PARCEL WALL'
        for t in TERMS[m.bldg].get(wall, []):
            if t.what == 'DRYER EXHAUST':
                rows.append((m.hp, t, odu_gap(y, h, t.along)))
    return rows


# ================================ the checks ================================
HEAD_CLR = IN(3)           # a head's end off a window's or door's rough opening, for the casing


EXT_FACE = 0.75                   # within this of an outside stud face is an exterior wall


def _systems():
    """RCO 1103.1's systems here: every dwelling is ductless, so each is one system with
       one wall control -- Unit 1's two levels included. The rule is arkitect/codes/ohio/rco."""
    from arkitect.codes.nec import dwelling as nec_dwelling
    out = {}
    for m in LEVELS:
        lv, W = m.elec, _W[m.bldg]
        D = 48.0 if m.bldg == 1 else B2_D
        s = out.setdefault(m.unit, dict(name='UNIT %d' % m.unit, controls=[], served=[], air=[]))
        s['served'] += [nm for _p, nm in lv.polys]+[r[4] for r in lv.rooms]
        for d in lv.devices:
            if d.kind != 'tstat': continue
            outer = (d.x <= 0.5+EXT_FACE or d.x >= W-0.5-EXT_FACE
                     or d.y <= 0.5+EXT_FACE or d.y >= D-0.5-EXT_FACE)
            at = nec_dwelling.stand_off(d.x, d.y, d.mount)
            s['controls'].append((d.x, d.y, nec_dwelling._room_at(at, lv) or '', outer))
    return [out[u] for u in sorted(out)]


def head_violations(levs=None):
    """A wall head hangs above 7'-0" and the window heads stand at 8'-0": a head on an exterior
       wall cannot share its length of wall with an opening on its own level. Seven did, until
       400 Oak's copy of this check was run here (2026-09-18). arkitect/lib/model/fit.py measures."""
    from arkitect.lib.symbols.mechanical import HEAD_L
    bad = []
    for m in (LEVELS if levs is None else levs):
        for hx, hy, _mt, room in m.heads:
            for wall in WALLS[m.bldg].values():
                off = abs((hx if wall.orient == 'v' else hy)-wall.at)
                if off > 1.0: continue                     # not on this wall
                along = hy if wall.orient == 'v' else hx
                mine = fit.on_level(wall.openings, m.ff, levels.FLOOR_RISE)
                for op in fit.across_opening(along, HEAD_L, mine, HEAD_CLR):
                    bad.append('%s %s: the head stands across %s in the %s' % (m.name, room, op.name, wall.name.lower()))
    return bad


def check_mechanical():
    """Every rule the model answers to, printed and asserted."""
    bad = head_violations()
    bad += rco_mech.control_violations(_systems())
    for ut in (UNIT_1, UNIT_23, UNIT_45):
        n = len(bedrooms(ut)); a = floor_area(ut); req = whole_house_cfm(n, a)
        fancs = [d for lv in dwelling(ut) for d in lv.devices if d.kind == 'fanc']
        heads = [d for lv in dwelling(ut) for d in lv.devices if d.kind == 'head']
        if len(fancs) != 1: bad.append('%s: %d continuous fans' % (ut.name, len(fancs)))
        if BOOST_CFM[ut.name] < LOCAL_CFM['BATH'][0]:
            bad.append('%s: boost %d CFM under Table M1505.4.4' % (ut.name, BOOST_CFM[ut.name]))
        # a head in every sleeping room and living space, A-001 note 18
        for lv in ut.levels:
            spaces = [nm for _p, nm in lv.polys]+[r[4] for r in lv.rooms]
            for nm in spaces:
                if not any(k in nm.upper() for k in HABITABLE): continue
                if not any(d.kind == 'head' and room_of(d, lv) == nm for d in lv.devices):
                    bad.append('%s %s: no heat-pump head' % (lv.name, nm))
            for pts, nm in [(p, n) for p, n in lv.polys]+[(None, r[4]) for r in lv.rooms]:
                if 'BATH' in nm.upper() and not any(d.kind in ('fanc', 'fan') and room_of(d, lv) == nm for d in lv.devices):
                    bad.append('%s %s: no exhaust fan' % (lv.name, nm))
        ck = _hp_circuit(ut)
        print("MECHANICAL %-12s %d BR, %s SF: whole-house %d CFM continuous, boost %d; %d heads on %s, MCA %d A / MOCP %d A"
              % (ut.name, n, '{:,}'.format(a), req, BOOST_CFM[ut.name], len(heads),
                 '/'.join(sorted({m.hp for m in LEVELS if m.utype is ut})), ck.mca, ck.mocp))
    print("MECHANICAL TERMINATIONS (exhaust %s and dryers %s to any opening; dryer ducts %s less %s an elbow):"
          % (fmt(EXH_CLR), fmt(EXH_CLR), fmt(DRYER_MAX), fmt(DRYER_ELBOW)))
    for r in terminations(levels=LEVELS, walls=WALLS):
        t = r['term']
        if t.wall == 'ROOF':
            x, y = t.along
            w4 = None
            if r['bldg'] == 1:
                w4 = min(abs(y-Y_SEP_TOP), abs(y-Y_SEP_BOT))
                if w4 < W4_ROOF_BAND-1e-9: bad.append('%s: roof cap %s from W4' % (t.mark, fmt(w4)))
            print("   %-6s %-14s %-21s at (%s, %s)%s" % (t.mark, t.what, 'ROOF', fmt(x), fmt(y),
                                                       '  %s from W4' % fmt(w4) if w4 is not None else ''))
            continue
        need = EXH_CLR
        if r['clr'] < need-1e-9:
            bad.append('%s: %s from %s, under %s' % (t.mark, fmt(r['clr']), r['near'], fmt(need)))
        if WALL_TO_LINE[(r['bldg'], t.wall)] < EXH_CLR-1e-9:
            bad.append('%s: %s wall is under %s from the lot line' % (t.mark, t.wall, fmt(EXH_CLR)))
        extra = ''
        if t.what == 'DRYER EXHAUST':
            extra = '  duct %s, %d elbows, %s equivalent' % (fmt(r['length']), r['elbows'], fmt(r['equiv']))
            if r['equiv'] > DRYER_MAX+1e-9: bad.append('%s: %s equivalent, over %s' % (t.mark, fmt(r['equiv']), fmt(DRYER_MAX)))
            if r['length'] > DRYER_PHYS_MAX+1e-9: bad.append('%s: %s of duct, over the %s A-001 note 16a states' % (t.mark, fmt(r['length']), fmt(DRYER_PHYS_MAX)))
            pts = [q for q in next(d.pts for m in LEVELS for d in m.ducts if d.term is t)]
            if any(b[2] < a[2]-1e-9 for a, b in zip(pts, pts[1:])): bad.append('%s: the dryer duct runs downward' % t.mark)
        print("   %-6s %-14s %-21s at %s, %s up   %s to %s%s"
              % (t.mark, t.what, t.wall, fmt(t.along), fmt(t.z), fmt(r['clr']), r['near'], extra))
    print("MECHANICAL OUTDOOR UNITS (dryer caps %s along their wall from the unit, at any height):"
          % fmt(ODU_TERM_CLR))
    for hp, t, gap in odu_clearances():
        if gap < ODU_TERM_CLR-1e-9:
            bad.append('%s: %s along the %s from %s, under %s' % (t.mark, fmt(gap), t.wall, hp, fmt(ODU_TERM_CLR)))
        print("   %-6s %-6s %s along the %s" % (hp, t.mark, fmt(gap), t.wall))
    # terminations on one wall keep TERM_GAP between them
    for bldg in (1, 2):
        for wall, ts in TERMS[bldg].items():
            if wall == 'ROOF': continue
            for i, a in enumerate(ts):
                for b in ts[i+1:]:
                    if abs(a.along-b.along) < TERM_GAP-1e-9 and abs(a.z-b.z) < TERM_GAP-1e-9 and a.unit == b.unit:
                        bad.append('%s and %s are %s apart on the %s' % (a.mark, b.mark, fmt(math.hypot(a.along-b.along, a.z-b.z)), wall))
    assert not bad, "mechanical:\n  " + "\n  ".join(bad)

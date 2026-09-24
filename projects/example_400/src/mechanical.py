"""The mechanical model: what M-101 and M-102 draw, and the checks that run before they do.

Heating and cooling are by ductless heat pump — one outdoor unit per dwelling, a wall
head in every bedroom and living space — so there is no supply or return duct anywhere
in the project. What a mechanical plan has to PLACE here is exhaust: the bath fans, one of
which in each dwelling also carries its RCO 303.4 whole-house ventilation, and the dryer
ducts. The water heaters are electric storage and vent nothing; the range hoods
recirculate, because the only wall behind Unit 1's range stands over the Units 2 / 3 walk.
Every termination ends through a wall or the roof, and the code puts a distance between a
termination and the nearest opening — RCO M1504.3 for an exhaust opening and M1502.3 for
a dryer, 3'-0" to any opening into the building. The wall caps are placed BY that rule
rather than typed on a sheet, and check_mechanical() measures every one of them against
every opening on both levels of its wall before anything draws.

Heads, fans and rooms are read from src/electrical.py, so M-101 and E-101 cannot
disagree about where a device is; the outdoor units are src/services.py's, the boxes
C-101 and the elevations draw. Coordinates are PAGE FEET — x = W minus the regridded
model x, so 396 Oak (north) is at x 0 and 404 Oak (south) at x W; y from the front
face — and heights are feet above finished grade, the elevations' datum.
"""
import math
from collections import namedtuple
from arkitect.lib.model import fit
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import IN, fmt
from arkitect.lib.symbols.mechanical import HEAD_L
from src import building1 as B1M, building2 as B2M, levels, services
from src.openings import WIN_GEOM
from src.electrical import LEVEL_U1_L1, LEVEL_U1_L2, LEVEL_U2, LEVEL_U3, NEC_UNITS, UNIT_1, UNIT_23
from arkitect.codes.nec.dwelling import HABITABLE, room_of
from src.sitework import COURT, DOOR_H, FRONT_YARD, PARK_D, SIDE_YARD
from arkitect.codes.ohio.rco.mechanical import (CAP_R, DRYER_ELBOW, DRYER_MAX, _dist, bedrooms, dwelling, odu_gap,
                                       whole_house_cfm)
from arkitect.codes.ohio.rco.mechanical import terminations
from arkitect.codes.ohio.rco import mechanical as rco_mech


# ================================ the tables ================================


# RCO Table M1505.4.4: local exhaust rates, intermittent and continuous.
LOCAL_CFM = {'BATH': (50, 20), 'KITCHEN': (100, 25)}
# The boost the continuous fan's wall switch gives it — a design choice, at or over the
# bath's intermittent rate; Unit 1's fans are 80 CFM units. The ventilation schedule prints these.
BOOST_CFM = {'UNIT 1': 80, 'UNITS 2 / 3': 50}
DRYER_OUT_Z = 4.0          # the stacked dryer's outlet above its floor — design assumption, M-101 says so
DUCT_D, DUCT_SIZE = IN(4), '4"'   # RCO M1502.4.1: 4" round, and the one place the set says so
B2_DR_CAP_Z = 7.5          # Units 2 / 3: the cap above its floor, over the heads of people on the parking walk
EXH_CLR = 3.0              # M1504.3 exhaust openings, M1502.3 dryer terminations
TERM_GAP = 3.0             # between two terminations of one unit on one wall
ODU_TERM_CLR = services.ODU_DRYER_CLR   # a dryer cap to an outdoor unit on its wall, along the wall: M-101 note 8
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
    return Opening(lo, lo+ln, ff, ff+DOOR_H, name)


def cap_position(wall, z, want, clr, taken=()):
    """The position along `wall` nearest `want` at which a cap at height z is at least
       `clr` from every opening in the wall and TERM_GAP from every termination already
       on it (`taken`, positions along the wall), inside the wall's extent. Raises when
       the wall has no such point."""
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


def _plans(n):
    if n == 1:
        return B1M.B1_W, B1M.B1_D, B1M.Y_REAR, {lv: (m['plan'], m['wins'], m['doors']) for lv, m in B1M.LEVEL.items()}
    return B2M.B2_W, B2M.B2_D, B2M.Y_REAR, {lv: (B2M.PLAN_B2, B2M.b2_wins(lv), B2M.B2doors) for lv in (1, 2)}


FRONT_NAME = {1: 'FRONT WALL', 2: 'COURTYARD WALL'}


def walls(n):
    """Building n's four exterior walls and every window and exterior door in them, both
       levels, through each level's regrid — the lists the elevations read."""
    W, D, rear_y, plans = _plans(n)
    ops = {'NORTH WALL': [], 'SOUTH WALL': [], FRONT_NAME[n]: [], 'REAR WALL': []}
    for lv, (P, wins, doors) in plans.items():
        ff = FF[lv]
        for w in wins:
            x, y, ln, o, mk = w[:5]
            nm = 'L%d W-%s' % (lv, mk)
            if o == 'v':
                ops['NORTH WALL' if x > W-1.0 else 'SOUTH WALL'].append(_win(P.y(y), ln, ff, mk, nm))
            else:
                ops[FRONT_NAME[n] if y < 1.0 else 'REAR WALL'].append(_win(W-P.x(x, y)-ln, ln, ff, mk, nm))
        for d in doors:
            if 'ext' not in d[5:]: continue
            x, y, ln = d[:3]
            assert d[3] == 'h', "an exterior door in a side wall: walls() has no case for it"
            ops[FRONT_NAME[n] if y < 1.0 else 'REAR WALL'].append(_door(W-P.x(x, y)-ln, ln, ff, 'L%d DOOR' % lv))
    return {'NORTH WALL': Wall('NORTH WALL', 'v', 0.0, 0.0, D, sorted(ops['NORTH WALL'])),
            'SOUTH WALL': Wall('SOUTH WALL', 'v', W, 0.0, D, sorted(ops['SOUTH WALL'])),
            FRONT_NAME[n]: Wall(FRONT_NAME[n], 'h', 0.0, 0.0, W, sorted(ops[FRONT_NAME[n]])),
            'REAR WALL': Wall('REAR WALL', 'h', D, 0.0, W, sorted(ops['REAR WALL']))}


# How far each wall stands from the lot line it faces, for M1504.3's 3'-0" to a property
# line. Building 1's rear and Building 2's front face the courtyard.
WALL_TO_LINE = {
    (1, 'NORTH WALL'): SIDE_YARD, (1, 'SOUTH WALL'): SIDE_YARD, (1, 'FRONT WALL'): FRONT_YARD, (1, 'REAR WALL'): COURT,
    (2, 'NORTH WALL'): SIDE_YARD, (2, 'SOUTH WALL'): SIDE_YARD, (2, 'COURTYARD WALL'): COURT, (2, 'REAR WALL'): PARK_D,
}


# ================================ the units ================================
# One entry per level AS DRAWN. How each bath exhausts: a Level 1 bath through the wall
# named, from the floor cavity above it; a Level 2 bath straight up to a roof cap over the
# fan, where src/roof.py already breaks the ridge vent for it and S-103 draws it.
#   Unit 1's Bath 1 is against the north wall, which has no Level 1 opening and faces the
#   side yard nothing walks in. Unit 2's tub is against the south wall, over swale S-4.
EXHAUST = {
    (1, 1): ('WALL', 'NORTH WALL'),
    (1, 2): ('ROOF', None),
    (2, 1): ('WALL', 'SOUTH WALL'),
    (3, 2): ('ROOF', None),
}
FAN_MARK = {(1, 1): 'EF-1A', (1, 2): 'EF-1B', (2, 1): 'EF-2', (3, 2): 'EF-3'}
_UNITS = [
    # unit, name, building, level, elec level, plan, unit type, outdoor unit
    (1, 'UNIT 1 LEVEL 1', 1, 1, LEVEL_U1_L1, B1M.LEVEL[1]['plan'], UNIT_1, 'HP-1'),
    (1, 'UNIT 1 LEVEL 2', 1, 2, LEVEL_U1_L2, B1M.LEVEL[2]['plan'], UNIT_1, 'HP-1'),
    (2, 'UNIT 2', 2, 1, LEVEL_U2, B2M.PLAN_B2, UNIT_23, 'HP-2'),
    (3, 'UNIT 3', 2, 2, LEVEL_U3, B2M.PLAN_B2, UNIT_23, 'HP-3'),
]
_SWAP = {'e': 'w', 'w': 'e'}
_W = {1: B1M.B1_W, 2: B2M.B2_W}
_D = {1: B1M.B1_D, 2: B2M.B2_D}


def _pg(plan, W, x, y):
    """A regridded, mirrored unit's model point in page feet."""
    return (W-plan.x(x, y), plan.y(y))


def _box(mark):
    """An outdoor unit's rectangle outside its wall, in its building's page feet:
       (x, y, w, h), from src/services.py's box."""
    b = next(b for b in services.EQUIPMENT if b.mark == mark)
    assert b.wall in ('NORTH', 'SOUTH'), "%s: _box() knows the side walls only" % mark
    x = -b.depth if b.wall == 'NORTH' else _W[b.building]
    return (x, b.along0, b.depth, b.along1-b.along0)


# ---------------- Unit 1's ducted zones ----------------
# The designer, 2026-09-19: one two-zone system in Unit 1, an air handler concealed in each level's
# hall soffit (src/building1.py). Every room it serves takes a supply register, and each
# level's hall takes the return at the air handler. Model feet, as the plans are authored;
# check_mechanical() holds each one inside the room it names, so a moved wall fails here.
AHU_L, AHU_D = 3.75, 2.0          # the cabinet arkitect.lib.symbols.mechanical draws, plan feet
DUCTED = (1,)                     # the units whose supply is ducted, not a head per room
AHU_MARK = {(1, 1): 'AHU-1', (1, 2): 'AHU-2'}      # one zone per level, M-101
# Level 2's registers are HIGH SIDEWALL registers, each in its room's hall wall, fed through
# that wall from the hall soffit: Level 2 has the attic over it, and nothing goes there
#. Each stands 0.3 ft into its room, clear of the door in that wall, and 3'-0"
# off the thermostat, RCO 1103.1's CONTROL_REG_CLR. Level 1's are ceiling registers, fed
# through the floor trusses over it.
_SW = 0.3                         # a sidewall register's centre off its wall's stud face
# Bedroom 2's register stands on its corridor wall between the closet and this point, 6" past
# the truss at 6'-0" that frames the attic hatch's bay, so its run ends short of the hatch's
# chase (roof.soffit_violations(), a recorded decision)
Y_BR2_REG_FROM = 6.5
REGISTERS = {
    (1, 1): [(6.0, 4.5,  'LIVING / KITCHEN / DINING'), (6.5, 19.5, 'LIVING / KITCHEN / DINING'),
             (18.05, 27.5, 'BATH 1'), (12.25, 26.07, 'HALL', 'RA')],     # the RA at the hall's head, M-101's label under it
    (1, 2): [(B1M.X_FR1-_SW, (Y_BR2_REG_FROM+B1M.BR2_CL[1])/2.0, 'BEDROOM 2'),   # its corridor wall, past the closet
             (5.03, B1M.Y_BRR+_SW, 'BEDROOM 1'), (18.9, B1M.Y_BRR+_SW, 'BEDROOM 3'),
             (6.7, B1M.Y_FR1-_SW, 'BATH 2'),
             (B1M.U1_AHU[2][0]-AHU_L/2.0-0.8, B1M.U1_AHU[2][1], 'HALL', 'RA')],   # at the air handler's end, off the hall's label
}
SIDEWALL = {(1, 2)}               # the ducted levels whose supply registers are in a wall
RA = 'RA'                         # what a return grille is marked


def registers(unit, level, returns=False):
    """The supply registers of a level, or its return grilles."""
    return [r for r in REGISTERS.get((unit, level), []) if (len(r) > 3) == bool(returns)]


HALL_CEILING_MIN = 7.0            # RCO 305.1: a hall, like a habitable room, keeps 7'-0"


def ahu_horiz(level):
    """Does a level's air handler lie across the building (its length along x)? Where the
       soffit it hangs in is too narrow for that -- Level 1's hall, 3'-6" across -- it lies
       along it."""
    ax, ay = B1M.U1_AHU[level]
    rects = B1M.U1_SOFFIT[level]                  # the one it hangs in; a cut soffit, the first
    x0, _y0, x1, _y1 = next((r for r in rects if r[0] <= ax <= r[2] and r[1] <= ay <= r[3]), rects[0])
    return x1-x0 >= AHU_L


def _overlap(a, b):
    """The area two rectangles (x0, y0, x1, y1) share."""
    return max(0.0, min(a[2], b[2])-max(a[0], b[0]))*max(0.0, min(a[3], b[3])-max(a[1], b[1]))


def in_soffit(level, box):
    """Is a rectangle wholly inside a level's soffit? Its rectangles do not overlap, so the
       area they share with it adds up to its own."""
    return sum(_overlap(box, r) for r in B1M.U1_SOFFIT[level]) >= (box[2]-box[0])*(box[3]-box[1])-1e-6


def ahu_box(level, x, y):
    """The cabinet's rectangle (x0, y0, x1, y1) about its center, in the frame x, y are in."""
    w, d = (AHU_L, AHU_D) if ahu_horiz(level) else (AHU_D, AHU_L)
    return (x-w/2.0, y-d/2.0, x+w/2.0, y+d/2.0)


# Each air handler is reached through a removable panel in its soffit's underside, sized to
# lower the unit out whole in its auxiliary pan, over a working space on the hall floor.
AHU_PAN = IN(3)                   # RCO M1411.3.1: the pan 3" larger than the unit each way
AHU_PANEL = AHU_PAN+IN(1)         # the panel over the cabinet each way: the pan, and 1/2" a side
AHU_WORK = IN(30)                 # RCO M1305.1: 30" x 30" of level working space at the unit


def ahu_panel(level, x, y):
    """A level's access panel (x0, y0, x1, y1) about its air handler's center."""
    x0, y0, x1, y1 = ahu_box(level, x, y)
    g = AHU_PANEL/2.0
    return (x0-g, y0-g, x1+g, y1+g)


def ahu_work(level):
    """The hall floor under a level's air handler, finished face to finished face: the
       soffit rectangle it hangs in, less the board on each wall."""
    ax, ay = B1M.U1_AHU[level]
    x0, y0, x1, y1 = next((r for r in B1M.U1_SOFFIT[level] if r[0] <= ax <= r[2] and r[1] <= ay <= r[3]),
                          B1M.U1_SOFFIT[level][0])
    return (x1-x0-2*B1M.GYP, y1-y0-2*B1M.GYP)


def soffit_clear(level):
    """What a level's hall soffit leaves under it, floor to the soffit's face."""
    ceiling = levels.F2_CEILING-levels.FF1 if level == 1 else levels.UPPER_CEILING-levels.FF2
    return ceiling-B1M.U1_SOFFIT_DROP


def ducted_violations(ut, unit_no=1):
    """Unit 1's two zones: one air handler per level in its hall soffit, one return with it,
       every register inside the room it names, and the soffit still a legal ceiling."""
    from arkitect.codes.nec import dwelling as nec_dwelling
    bad = []
    for level, lv in enumerate(ut.levels, 1):
        ahus = [d for d in lv.devices if d.kind == 'ahu']
        if len(ahus) != 1:
            bad.append('%s: %d air handlers, one zone per level' % (lv.name, len(ahus)))
        for d in ahus:
            room = room_of(d, lv) or ''
            if room not in B1M.U1_SOFFIT_ROOMS[level]:
                bad.append('%s: the air handler stands in %s, not the soffit of %s'
                           % (lv.name, room or 'the open', ', '.join(B1M.U1_SOFFIT_ROOMS[level])))
            if not in_soffit(level, ahu_box(level, d.x, d.y)):
                bad.append("%s: the air handler's cabinet leaves the soffit" % lv.name)
            if not in_soffit(level, ahu_panel(level, d.x, d.y)):
                bad.append("%s: the air handler's access panel leaves the soffit" % lv.name)
            if min(ahu_work(level)) < AHU_WORK-1e-9:
                bad.append("%s: the hall under the air handler is %s wide, under RCO M1305.1's %s"
                           % (lv.name, fmt(min(ahu_work(level))), fmt(AHU_WORK)))
        if len(registers(unit_no, level, returns=True)) != 1:
            bad.append('%s: the return grille is not one' % lv.name)
        for r in REGISTERS.get((unit_no, level), []):
            at = nec_dwelling._room_at((r[0], r[1]), lv)
            if at != r[2]:
                bad.append('%s: the register named %s stands in %s' % (lv.name, r[2], at or 'the open'))
        clear = soffit_clear(level)
        if clear < HALL_CEILING_MIN-1e-9:
            bad.append("%s: the hall soffit leaves %s, under RCO 305.1's %s"
                       % (lv.name, fmt(clear), fmt(HALL_CEILING_MIN)))
        if B1M.U1_SOFFIT_DROP < IN(10)-1e-9:
            bad.append('%s: a %s soffit does not hide the air handler and its plenum'
                       % (lv.name, fmt(B1M.U1_SOFFIT_DROP)))
    return bad


class MLevel:
    """One dwelling unit's level, ready to draw: heads, fans, ducts, terminations,
       line sets and the outdoor unit, all in page feet."""
    def __init__(s, unit, name, bldg, level, elec, plan, utype, hp):
        s.unit, s.name, s.bldg, s.level, s.elec, s.plan, s.utype, s.hp = unit, name, bldg, level, elec, plan, utype, hp
        s.W = _W[bldg]
        s.ff = FF[level]
        s.heads, s.fans, s.ducts, s.terms, s.linesets, s.roofcaps = [], [], [], [], [], []
        s.ahus, s.regs = [], []            # the ducted zones: air handlers and their registers
        s.runs = []                        # (register, polyline): each supply run, diagrammatic
        s.hp_box = _box(hp)
        s.sleeve = None
        s.drop = None                      # where Level 2 line sets go down to a Level 1 sleeve

    def pg(s, x, y, mount=None):
        X, Y = _pg(s.plan, s.W, x, y)
        return (X, Y) if mount is None else (X, Y, _SWAP.get(mount, mount))


def _place_devices(m):
    for d in m.elec.devices:
        if d.kind == 'head':
            x, y, mt = m.pg(d.x, d.y, d.mount)
            m.heads.append((x, y, mt, room_of(d, m.elec)))
        elif d.kind == 'ahu':
            x, y = m.pg(d.x, d.y)
            m.ahus.append((x, y, room_of(d, m.elec)))
        elif d.kind in ('fanc', 'fan'):
            x, y = m.pg(d.x, d.y)
            m.fans.append((x, y, d.kind, room_of(d, m.elec), d.tag))


def _place_registers(m):
    """Every register of a ducted level, in page feet: (x, y, room, mark)."""
    for r in REGISTERS.get((m.unit, m.level), []):
        x, y = m.pg(r[0], r[1])
        m.regs.append((x, y, r[2], r[3] if len(r) > 3 else ''))


def _supply_runs(m):
    """Each supply run, air handler to register, in page feet. A level fed through the
       floor trusses runs square across to its register's line and along it. A sidewall
       level runs inside its soffit: along the rectangle the air handler hangs in, then,
       for a register on another rectangle, up that one beside the wall the register is
       in, and last through the wall to the register."""
    for ax, ay, _room in m.ahus:
        for reg in m.regs:
            rx, ry, _rm, mark = reg
            if mark: continue
            pts = [(ax, ay), (rx, ay), (rx, ry)]
            yb = m.plan.y(B1M.Y_RB) if m.unit == 1 and m.level == 1 else None
            if yb is not None and ry < yb and rx > ax:
                # a run to the front leaves the rear band up the mechanical room's hall
                # side, at the heater's working space, and over the band's wall: the room's
                # label is in the patch past it, between the panel's space and the W/D
                xr = _fit(m, B1M.F_L1, 'whclear')[2]-0.15
                pts = [(ax, ay), (xr, ay), (xr, yb-0.3), (rx, yb-0.3), (rx, ry)]
            if (m.unit, m.level) in SIDEWALL:
                rects = B1M.soffit_pages(m.level)
                home = next(r for r in rects if r[0] <= ax <= r[2] and r[1] <= ay <= r[3])
                near = min(rects, key=lambda r: math.hypot(max(r[0]-rx, 0, rx-r[2]), max(r[1]-ry, 0, ry-r[3])))
                if near is not home:
                    xc = near[2]-_SW if abs(rx-near[2]) < abs(rx-near[0]) else near[0]+_SW
                    pts = [(ax, ay), (xc, ay), (xc, ry), (rx, ry)]
            m.runs.append((reg, pts))


def run_violations(levs=None):
    """A sidewall level's runs stay in its soffit: every point of each run, but for
       its last reach through the wall to the register, inside the soffit, and every
       register within that reach of it -- so a register moved off its hall wall, or a
       soffit cut back, stops the build."""
    from arkitect.lib.model.runs import in_rect, points
    bad = []
    for m in (LEVELS if levs is None else levs):
        if (m.unit, m.level) not in SIDEWALL: continue
        rects = B1M.soffit_pages(m.level)
        for (rx, ry, room, _mk), pts in m.runs:
            if not any(math.hypot(max(r[0]-rx, 0, rx-r[2]), max(r[1]-ry, 0, ry-r[3])) <= SW_REACH for r in rects):
                bad.append('%s %s: the register is not in a wall of the soffit' % (m.name, room))
            for q in points(pts):
                if math.hypot(q[0]-rx, q[1]-ry) <= SW_REACH: continue
                if not any(in_rect(q, (r[0], r[1], r[2]-r[0], r[3]-r[1])) for r in rects):
                    bad.append('%s %s: the supply run leaves the soffit' % (m.name, room)); break
    return bad


def reg_horiz(m, reg):
    """Does a register lie along x? A ceiling register does; a sidewall register lies along
       its wall, which is the soffit face it is nearest."""
    rx, ry = reg[0], reg[1]
    if (m.unit, m.level) not in SIDEWALL or reg[3]: return True
    r = min(B1M.soffit_pages(m.level), key=lambda r: math.hypot(max(r[0]-rx, 0, rx-r[2]), max(r[1]-ry, 0, ry-r[3])))
    return max(r[0]-rx, 0, rx-r[2]) <= max(r[1]-ry, 0, ry-r[3])


SW_REACH = _SW+B1M.PARTITION+0.05  # a sidewall register's reach: through its wall, to the soffit's face


def _bath_exhaust(m, walls, marks):
    """Each bath fan's duct to its cap: through a wall for a Level 1 bath, up through the
       roof for a Level 2 one."""
    how, where = EXHAUST[(m.unit, m.level)]
    assert len(m.fans) == 1, "%s: %d bath fans, FAN_MARK names one" % (m.name, len(m.fans))
    fx, fy, _kind, _room, _tag = m.fans[0]
    mark = FAN_MARK[(m.unit, m.level)]
    if how == 'WALL':
        wall = walls[where]
        # Unit 1's duct runs through the floor trusses over its bath; Unit 2's in its bath's soffit,
        # UNDER the rated F1 membrane, which it does not pierce (src/framing.py, A-601 F1 item C)
        z = levels.F1_PLATE+CAV_Z if m.bldg == 1 else levels.F1_CEILING-B2M.U2_SOFFIT_DROP/2.0
        taken = [t.along for t in marks.get(where, [])]
        a = cap_position(wall, z, fy if wall.orient == 'v' else fx, EXH_CLR, taken)
        t = Term(mark, 'BATH EXHAUST', m.unit, where, a, z)
        pts = ([(fx, fy), (fx, a), (wall.at, a)] if wall.orient == 'v' else [(fx, fy), (a, fy), (a, wall.at)])
    else:
        t = Term(mark, 'BATH EXHAUST', m.unit, 'ROOF', (fx, fy), None)
        pts = [(fx, fy), (fx, fy)]
        m.roofcaps.append(t)
    m.terms.append(t); marks.setdefault(t.wall, []).append(t)
    m.ducts.append(Duct(t, pts, DUCT_SIZE))


def _fit(m, fixtures, kind):
    """A fitting's page rectangle (x0, y0, x1, y1): its origin regridded, its size kept."""
    f = m.plan.keep(next(f for f in fixtures if f[4] == kind))
    return m.W-f[0]-f[2], f[1], m.W-f[0], f[1]+f[3]


def _wd(m, fixtures):
    """The washer / dryer's page rectangle (x0, y0, x1, y1)."""
    f = m.plan.keep(next(f for f in fixtures if f[4] == 'wd'))     # its origin regridded, its size kept
    return m.W-f[0]-f[2], f[1], m.W-f[0], f[1]+f[3]


def _appliance_exhaust(m, marks):
    """The dryer duct, from the stacked dryer's outlet up the wall behind it and out. The
       heaters are electric storage and vent nothing."""
    ff = m.ff; z0 = ff+DRYER_OUT_Z
    if m.unit == 1:
        if m.level != 1: return
        x0, _y0, x1, _y1 = _wd(m, B1M.F_L1)                  # against the rear wall
        xc = (x0+x1)/2.0; D = _D[1]; y_in = D-0.5-IN(5)
        z1 = levels.FF1+B1M.DR_CAP_Z
        dr = Term('DR-1', 'DRYER EXHAUST', 1, 'REAR WALL', xc, z1)
        pts = [(xc, y_in-0.4, z0), (xc, y_in, z0), (xc, y_in, z1), (xc, D, z1)]
    else:
        _x0, y0, _x1, y1 = _wd(m, B2M.F_B2)                  # against the north wall
        assert abs(y0-B2M.B2_DR_BAY[0]) < 1e-6 and abs(y1-B2M.B2_DR_BAY[1]) < 1e-6, "the dryer is not in B2_DR_BAY"
        yc = (y0+y1)/2.0; x_in = 0.5+IN(5)
        z1 = ff+B2_DR_CAP_Z
        # The duct rises behind the dryer at the dryer's own centreline and steps toward the
        # courtyard to pass between studs: the stack's deepened bay puts a 2x8 on that
        # centreline (A-601), and that stud cannot move. One more elbow, still well inside
        # M1502.4.5.1. Derived from the bay, so moving the stack moves the cap.
        ye = B2M.bay_penetration_y(yc, DUCT_D)
        dr = Term('DR-%d' % m.unit, 'DRYER EXHAUST', m.unit, 'NORTH WALL', ye, z1)
        pts = [(x_in+0.4, yc, z0), (x_in, yc, z0), (x_in, yc, z1)]
        if abs(ye-yc) > 1e-9: pts.append((x_in, ye, z1))
        pts.append((0.0, ye, z1))
    m.ducts.append(Duct(dr, pts, DUCT_SIZE))
    m.terms.append(dr); marks.setdefault(dr.wall, []).append(dr)


LS_DROP = 0.5                     # Unit 1's drop in the north wall, this far along it from the sleeve


def dx_wall(sx):
    """The middle of the exterior wall whose outer face is at page x sx: the cavity a set
       drops through between levels."""
    return sx+EXT_STUD/2.0 if sx < 1.0 else sx-EXT_STUD/2.0


def _linesets(m):
    """Each head's line set to the unit's sleeve: off its wall, along to the trunk line
       on the sleeve's side, along that to the sleeve's position, out. Unit 1's Level 2
       heads end at the drop inside the north wall, where Level 1 picks them up."""
    x, y, w, h = m.hp_box
    on_left = x < m.W/2.0
    sx = 0.0 if on_left else m.W
    sy = y+h/2.0
    m.sleeve = (sx, sy)
    tx = 0.5+LINE_OFF if on_left else m.W-0.5-LINE_OFF
    off = {'n': (0, LINE_OFF), 's': (0, -LINE_OFF), 'e': (-LINE_OFF, 0), 'w': (LINE_OFF, 0)}
    # An air handler's set leaves it off the supply trunk's line, which runs out of the
    # cabinet along y = its centre: LINE_OFF toward the rear where the cabinet lies across
    # the house, and at its rear end, LINE_OFF in, where it lies along its hall (R-033).
    for a in m.ahus:
        off[('ahu', a)] = (0.0, LINE_OFF if ahu_horiz(m.level) else AHU_L/2.0-LINE_OFF)
    for hx, hy, mt, room in m.heads+[(a[0], a[1], ('ahu', a), a[2]) for a in m.ahus]:
        dx, dy = off.get(mt, (0.0, 0.0))
        pts = [(hx, hy), (hx+dx, hy+dy), (tx, hy+dy), (tx, sy)]
        if m.unit == 1 and m.level == 2:
            # into the north wall at the set's own line, along the cavity to the drop
            m.drop = (dx_wall(sx), sy-LS_DROP)
            pts = [(hx, hy), (hx+dx, hy+dy), (m.drop[0], hy+dy), m.drop]
        else:
            pts.append((sx, sy))
        m.linesets.append([q for i, q in enumerate(pts) if i == 0 or math.hypot(q[0]-pts[i-1][0], q[1]-pts[i-1][1]) > 1e-9])
    if m.unit == 1 and m.level == 1:
        # Level 2's sets come down the same cavity and along it to this level's sleeve
        m.drop = (dx_wall(sx), sy-LS_DROP)
        m.linesets.append([m.drop, (m.drop[0], sy), (sx, sy)])


def build():
    """Every level of every unit, placed and routed; the walls; the terminations by
       building. Runs once at import."""
    wl = {1: walls(1), 2: walls(2)}
    marks = {1: {}, 2: {}}
    out = []
    for row in _UNITS:
        m = MLevel(*row)
        _place_devices(m)
        _place_registers(m)
        _supply_runs(m)
        _appliance_exhaust(m, marks[m.bldg])
        _bath_exhaust(m, wl[m.bldg], marks[m.bldg])
        _linesets(m)
        out.append(m)
    return out, wl, marks


LEVELS, WALLS, TERMS = build()
B1_LEVELS = [m for m in LEVELS if m.bldg == 1]
B2_LEVELS = [m for m in LEVELS if m.bldg == 2]


# ================================ the schedules ================================
def _hp_circuit(ut):
    return next(c for c in ut.circuits if c.kind == 'hp')


def floor_area(ut):
    return next(u[1] for u in NEC_UNITS if u[0] == ut.name)


def outdoor_units():
    """One row per outdoor unit: mark, the unit it serves, its wall, MCA, MOCP, and the
       indoor units it carries -- a head with its room, or a ducted zone with its mark."""
    rows = []
    for m in LEVELS:
        if m.unit == 1 and m.level == 2: continue
        heads = [h for lv in (LEVELS if m.unit == 1 else [m]) if lv.unit == m.unit for h in lv.heads]
        ck = _hp_circuit(m.utype)
        x = m.hp_box[0]
        wall = 'NORTH' if x < 0 else 'SOUTH'
        indoor = [h[3] for h in heads]
        if m.unit in DUCTED:
            indoor = ['%s (LEVEL %d)' % (AHU_MARK[(m.unit, lv)], lv)
                      for lv in sorted(l for (u, l) in AHU_MARK if u == m.unit)]
        rows.append(dict(mark=m.hp, unit=m.unit, wall=wall, mca=ck.mca, mocp=ck.mocp,
                         heads=indoor))
    return rows


def ventilation():
    """One row per unit type: bedrooms, area, the whole-house rate required and the
       continuous fan's rate, the boost, the bath intermittent minimum."""
    rows = []
    for ut in (UNIT_1, UNIT_23):
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
        wall = 'NORTH WALL' if x < 0 else 'SOUTH WALL'
        for t in TERMS[m.bldg].get(wall, []):
            if t.what == 'DRYER EXHAUST':
                rows.append((m.hp, t, odu_gap(y, h, t.along)))
    return rows


def lineset_lengths():
    """{unit: plan feet of line set as drawn}, head to sleeve. Diagrammatic, but it is what
       a head's place costs: the heads stand on or toward their outdoor unit's wall."""
    out = {}
    for m in LEVELS:
        for ls in m.linesets:
            out[m.unit] = out.get(m.unit, 0.0)+sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(ls, ls[1:]))
    return out


# ================================ the checks ================================
HEAD_CLR = IN(3)           # a head's end off a window's or door's rough opening, for the casing

EXT_FACE = 0.75                   # within this of an outside stud face is an exterior wall


def _systems():
    """What RCO 1103.1 counts as a system here, ready for arkitect.codes.ohio.rco.mechanical's rule:
       each of Unit 1's two ducted zones, and each ADU's one ductless system."""
    from arkitect.codes.nec import dwelling as nec_dwelling
    out = []
    for m in LEVELS:
        lv, W, D = m.elec, _W[m.bldg], B1M.Y_REAR if m.bldg == 1 else B2M.Y_REAR
        ducted = m.unit in DUCTED
        spaces = [nm for _p, nm in lv.polys]+[r[4] for r in lv.rooms]
        controls = []
        for d in lv.devices:
            if d.kind != 'tstat': continue
            outer = (d.x <= 0.5+EXT_FACE or d.x >= W-0.5-EXT_FACE
                     or d.y <= 0.5+EXT_FACE or d.y >= D-0.5-EXT_FACE)
            # the device stands ON its wall line; the room it reads is the one it faces
            at = nec_dwelling.stand_off(d.x, d.y, d.mount)
            controls.append((d.x, d.y, nec_dwelling._room_at(at, lv) or '', outer))
        out.append(dict(name='%s%s' % (m.name, ' ZONE' if ducted else ''), controls=controls,
                        served=[r[2] for r in REGISTERS.get((m.unit, m.level), [])] if ducted else spaces,
                        air=[(r[0], r[1]) for r in REGISTERS.get((m.unit, m.level), [])]))
    return out


def head_violations(levs=None):
    """A wall head hangs above 7'-0" and the window heads stand at 8'-0": a head on an
       exterior wall cannot share its length of wall with an opening on its own level."""
    bad = []
    for m in (LEVELS if levs is None else levs):
        W, D = m.W, _D[m.bldg]
        for hx, hy, _mt, room in m.heads:
            wall, a = ((FRONT_NAME[m.bldg], hx) if hy < 1.0 else ('REAR WALL', hx) if hy > D-1.0 else
                       ('NORTH WALL', hy) if hx < 1.0 else ('SOUTH WALL', hy) if hx > W-1.0 else (None, None))
            if wall is None: continue                   # on a partition
            mine = [op for op in WALLS[m.bldg][wall].openings if op.name.startswith('L%d ' % m.level)]
            for op in fit.across_opening(a, HEAD_L, mine, HEAD_CLR):
                bad.append('%s %s: the head stands across %s in the %s' % (m.name, room, op.name, wall.lower()))
    return bad


def check_mechanical():
    """Every rule the model answers to, printed and asserted."""
    bad = []
    for ut in (UNIT_1, UNIT_23):
        n = len(bedrooms(ut)); a = floor_area(ut); req = whole_house_cfm(n, a)
        fancs = [d for lv in dwelling(ut) for d in lv.devices if d.kind == 'fanc']
        heads = [d for lv in dwelling(ut) for d in lv.devices if d.kind == 'head']
        if len(fancs) != 1: bad.append('%s: %d continuous fans' % (ut.name, len(fancs)))
        if BOOST_CFM[ut.name] < LOCAL_CFM['BATH'][0]:
            bad.append('%s: boost %d CFM under Table M1505.4.4' % (ut.name, BOOST_CFM[ut.name]))
        # A-001 note 15: every sleeping room and living space is served -- by its own head
        # where the unit is ductless, by a supply register where it is ducted.
        unit_no = 1 if ut is UNIT_1 else 2
        ducted = unit_no in DUCTED
        for level, lv in enumerate(ut.levels, 1):
            spaces = [nm for _p, nm in lv.polys]+[r[4] for r in lv.rooms]
            served = [r[2] for r in registers(unit_no, level)] if ducted else \
                     [room_of(d, lv) for d in lv.devices if d.kind == 'head']
            for nm in spaces:
                if not any(k in nm.upper() for k in HABITABLE): continue
                if nm not in served:
                    bad.append('%s %s: no %s' % (lv.name, nm, 'supply register' if ducted else 'heat-pump head'))
        if ducted:
            bad += ducted_violations(ut, unit_no)
            bad += run_violations([m for m in LEVELS if m.unit == unit_no])
            for pts, nm in [(p, n) for p, n in lv.polys]+[(None, r[4]) for r in lv.rooms]:
                if 'BATH' in nm.upper() and not any(d.kind in ('fanc', 'fan') and room_of(d, lv) == nm for d in lv.devices):
                    bad.append('%s %s: no exhaust fan' % (lv.name, nm))
        ck = _hp_circuit(ut)
        indoor = ('%d ducted zones' % len([k for k in AHU_MARK if k[0] == unit_no])) if ducted \
                 else ('%d heads' % len(heads))
        print("MECHANICAL %-12s %d BR, %s SF: whole-house %d CFM continuous, boost %d; %s on %s, MCA %d A / MOCP %d A"
              % (ut.name, n, '{:,}'.format(a), req, BOOST_CFM[ut.name], indoor,
                 '/'.join(sorted({m.hp for m in LEVELS if m.utype is ut})), ck.mca, ck.mocp))
    print("MECHANICAL TERMINATIONS (exhaust %s and dryers %s to any opening; dryer ducts %s less %s an elbow):"
          % (fmt(EXH_CLR), fmt(EXH_CLR), fmt(DRYER_MAX), fmt(DRYER_ELBOW)))
    for r in terminations(levels=LEVELS, walls=WALLS):
        t = r['term']
        if t.wall == 'ROOF':
            x, y = t.along
            print("   %-6s %-14s %-21s at (%s, %s)" % (t.mark, t.what, 'ROOF', fmt(x), fmt(y)))
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
    bad += head_violations()
    bad += rco_mech.control_violations(_systems())
    print("MECHANICAL LINE SETS, plan feet as drawn: %s" % ", ".join("UNIT %d %s" % (u, fmt(v)) for u, v in sorted(lineset_lengths().items())))
    # S-103 draws the roof caps from src/roof.py: the same fans, the same marks
    from src import roof
    theirs = sorted((round(x, 6), round(y, 6), nm) for rf in roof.ROOFS for x, y, nm in roof.penetrations(rf) if 'ROOF CAP' in nm)
    mine = sorted((round(t.along[0], 6), round(t.along[1], 6), '%s ROOF CAP' % t.mark) for m in LEVELS for t in m.roofcaps)
    if theirs != mine: bad.append('roof caps: S-103 has %s, the mechanical model %s' % (theirs, mine))
    # no service box over a cap, and every opening the elevations draw is in a wall here
    for bldg in (1, 2):
        for wall, ts in TERMS[bldg].items():
            for t in ts:
                if wall == 'ROOF': continue
                for b in services.on(bldg, wall.split()[0]):
                    if b.along0-CAP_R < t.along < b.along1+CAP_R and b.z0-CAP_R < t.z < b.z1+CAP_R:
                        bad.append('%s: under %s' % (t.mark, b.mark))
        _W_, _D_, _ry, plans = _plans(bldg)
        want = sum(len(wins)+sum(1 for d in doors if 'ext' in d[5:]) for _P, wins, doors in plans.values())
        have = sum(len(w.openings) for w in WALLS[bldg].values())
        if want != have: bad.append('Building %d: %d openings on the plans, %d in the walls' % (bldg, want, have))
    assert not bad, "mechanical:\n  " + "\n  ".join(bad)


def b2_wall_penetrations():
    """Everything of this model's that passes THROUGH Building 2's north wall, as
       (mark, position along the wall, width) — what `building2.stack_bay_violations()`
       measures against the deepened bay's two studs, which the stack places and a framer
       cannot move. The interlock is deliberate: `bay_penetration_y()` steps each duct clear,
       and this is what proves it still is."""
    return [(t.mark, t.along, DUCT_D)
            for m in B2_LEVELS for t in m.terms if t.wall == 'NORTH WALL']

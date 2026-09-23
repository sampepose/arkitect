"""The water supply model: what P-102 and P-103 draw, checked before anything draws.

The fixtures are the model's — the furniture lists the floor plans draw — so a tub that
moves on A-101 moves here. The service, the manifolds and the home runs are authored here
in PAGE FEET (396 Oak, north, at x 0; the front face at y 0; y toward the alley), each
building in its own, and the fixtures are brought into them through the regrid and the
sheet mirror, the way their symbols reach the page.

ONE service feeds both buildings. It comes from Oak Avenue down the NORTH side yard,
which keeps it the width of a building away from the sewer in the south yard (OPC 603.2);
a branch enters Building 1 and the line goes on to Building 2. The DPU meter is taken in
a pit at the right-of-way line and every dwelling has its own valve and submeter — the
basis shown, which Columbus DPU may change (P-601 note 5).

Sizing is IPC Appendix E: water supply fixture units from Table E103.3(2), private
occupancy, the bathroom group taken as a group; the service, the meter and each trunk
from Table E201.1 at an assumed static pressure and the developed length measured off
the drawn runs plus an assumed distance to the public main. Appendix E is the
accepted engineering practice OPC 604.1 asks for; Ohio adopts IPC chapters 2 to 15 by
reference and not the appendices. Both assumptions print on the sheet.

Drainage is src/drainage.py's. Nothing here draws.
"""
import math
from collections import namedtuple
from arkitect.lib.units import IN, fmt
from src import levels

# ================================ the tables: shared, see arkitect/codes/ohio/water_supply.py
from arkitect.codes.ohio.water_supply import (BATH_GROUP, FIXTURE_KINDS, MIN_SUPPLY, SUPPLY_KINDS, WSFU, pipe_size,
                                     row_for)
from arkitect.lib.model.water import (_inside_any, _length, _mirror, _one, _overlap, _overlap_box, _rects,
                             run_fixtures, stub, unit_names)


# ================================ this project's choices ================================
HOME_RUN = '1/2'
HEATER_CONN = '3/4'               # the storage heater's cold inlet and hot outlet

# ================================ the storage heaters ================================
# One electric storage heater per dwelling, P-601 notes 6 and 7, SIZED BY BEDROOM COUNT:
# 40 gallons for the two two-bedroom, one-bath units and 50 for Unit 1's three bedrooms
# and two baths. Both take two 4,500 W non-simultaneous elements, so every electrical
# figure in the set is the same whichever a dwelling gets.
#
# THE DIAMETER IS THE DESIGN CONSTRAINT, not the gallons. A tank stands on the floor and
# eats depth, and NEC 110.26(A) wants 36" clear in front of each unit panel in the same
# room. A 40-gallon tall tank is 18" across (Rheem, A.O. Smith and Bradford White all run
# 18" x about 61") and a 50-gallon 20"; check_working_spaces() holds each tank out of its
# panel's space at those diameters, so a bigger tank is not a substitute.
WH_TANKS     = {'UNIT 1': (50, IN(20)), 'UNITS 2 / 3': (40, IN(18))}
WH_GALLONS   = 40                 # what Units 2 and 3 take; Unit 1's is WH_TANKS
WH_DIAM      = IN(18)
WH_CLR       = IN(2)              # framing clearance each side of the tank
WH_WORK      = IN(30)             # RCO M1305.1, 30" x 30" at the control side
WH_UEF       = 0.92               # the minimum uniform energy factor specified
WH_ELEMENT_W = 4500               # two non-simultaneous elements, the calculated load
WH_VOLTS     = 240
WH_CIRCUIT   = (30, 2, '#10')     # amps, poles, copper — E-101 / E-102 schedule it
# P2801.6: a pan under a heater standing where a leak would damage what is below it.
# Units 3 and 5 are the two that stand over another dwelling; the other three are on
# slab. P2801.6.2 sets the pan drain at 1" minimum, run full size to daylight.
WH_PAN_UNITS = ('UNIT 3',)
WH_PAN_DRAIN = '1'
WH_PAN_MARGIN = IN(2)             # the pan larger in diameter than the tank it catches
# P2804.6.1: the relief discharge, full size, downward, ending outside between these
# heights above grade, with no trap, valve or threaded end.
WH_TP_LO, WH_TP_HI = IN(6), IN(24)

# ---------------------------- the mixing valve ----------------------------
# The designer's instruction of 2026-09-15: store at 140 F and mix down to 120 F at the tank
# outlet with a thermostatic mixing valve. It buys three things at about $150 a unit —
#
#   CAPACITY. A gallon stored at 140 F makes more than a gallon of 120 F water, because
#   the draw is blended with cold. `usable_factor()` is that ratio and it is a mass
#   balance, not a rule of thumb: (store - cold) / (deliver - cold). At the assumed
#   inlet it is about 1.29, so the 40-gallon tanks deliver like 51 and Unit 1's 50 like
#   64. This is DELIVERED volume, not first-hour rating: the recovery rate is the
#   element's and does not change.
#
#   LEGIONELLA. Growth runs roughly 77 F to 113 F and 140 F storage sits clear above it.
#   Storing AT 120 F would have put the tank at the top of that band.
#
#   SCALD PROTECTION IS NOT WEAKENED. The valve holds the distribution at 120 F, and
#   P-102 / P-103 note 9 keeps the tub and shower valves limited to 120 F under OPC
#   424.3 downstream of it, so the fixture limit does not depend on this valve alone.
#
# ASSE 1017 is the standard for a mixing valve serving a water DISTRIBUTION system,
# which is this one at the tank outlet; ASSE 1070 is the point-of-use device at a
# fixture and is not a substitute here.
WH_STORE_F   = 140                # thermostat setting at the tank
WH_DELIVER_F = 120                # what the valve passes to the distribution
WH_TMV_STD   = 'ASSE 1017'
# The cold inlet is an assumption and prints on the sheet with the others: Columbus
# mains run near this in winter, which is the case that sizes the uplift. A warmer
# inlet gives a LARGER factor, so 50 F is the conservative figure to quote.
WH_COLD_F    = 50


def usable_factor(store=None, deliver=None, cold=None):
    """How many gallons of `deliver` a gallon stored at `store` makes, blended with
       water at `cold`. A mass balance on the mixing valve."""
    store = WH_STORE_F if store is None else store
    deliver = WH_DELIVER_F if deliver is None else deliver
    cold = WH_COLD_F if cold is None else cold
    assert cold < deliver <= store, 'the mixing valve cannot deliver %s F from %s F stored at %s F cold' % (deliver, store, cold)
    return (store-cold)/float(deliver-cold)


def effective_gallons(unit):
    """The delivered-equivalent capacity of a dwelling's tank, to the nearest gallon."""
    return int(round(WH_TANKS[unit][0]*usable_factor()))


def pan_required(unit_name):
    """RCO P2801.6: does this dwelling's heater stand over another dwelling?"""
    return unit_name in WH_PAN_UNITS
# ================================ the assumptions ================================
# Both print on the sheets with the rule to resize if either fails. Columbus DPU has
# not stated a static pressure at the tap or where the main is; P-601 note 5 holds the
# tap question open.
PRESSURE = '50 TO 60'             # psi, static, at the main
MAIN_TO_LOT = 30.0                # feet of service from the main to the Oak lot line, assumed


def pipe_for(wsfu, length_ft, meter=None, pressure=None):
    """Table E201.1 at this project's assumed pressure: (meter, pipe). See row_for()."""
    return row_for(wsfu, length_ft, pressure or PRESSURE, meter)


# ================================ the types ================================
Fixture = namedtuple('Fixture', 'x y w h kind')            # page feet
# A run is one bundle from the manifolds to a group of fixtures: `fixtures` names the
# kinds it reaches, `path` is the polyline it follows, in page feet, from the manifold.
Run = namedtuple('Run', 'group fixtures path')
# One dwelling unit on one level. `closets` are the rectangles its equipment must stand
# in; `manifold` is the cold and hot manifolds' rectangle, or None on a level fed from
# the dwelling's own manifolds below; `riser` is where its supply arrives from the level
# below, or None at grade; `valve` and `submeter` are the dwelling's full-open valve and
# its submeter, or None on a level that has them below.
Unit = namedtuple('Unit', 'name level fixtures closets clears manifold riser valve submeter runs')
# One building: its supply under its north wall to a riser inside, and the trunks
# from that riser: (the dwellings it feeds, the polyline, under) — `under` runs below
# the slab. A trunk ending at a riser point feeds the dwellings stacked over it.
Building = namedtuple('Building', 'name number W D entry riser units trunks')


def _fixtures(items, plan, W, kinds=SUPPLY_KINDS):
    """A furniture list's supply fixtures as the page rectangles its sheet draws."""
    return [Fixture(*(_mirror(plan.rect(f), W)[:4]+(f[4],))) for f in items if f[4] in kinds]


def tally(fixtures):
    """(cold, hot, total, rows): the WSFU of a level's fixtures, every (wc, lav, tub)
       triple taken as one bathroom group. rows are (label, count, cold, hot, total)."""
    n = {}
    for f in fixtures:
        if f.kind in FIXTURE_KINDS: n[f.kind] = n.get(f.kind, 0)+1
    groups = min(n.get('wc', 0), n.get('lav', 0), n.get('tub', 0)+n.get('shower', 0))
    rows = []
    if groups:
        rows.append(('BATHROOM GROUP, FLUSH TANK WC', groups)+tuple(v*groups for v in BATH_GROUP))
        for k in ('wc', 'lav'): n[k] -= groups
        tubs = min(groups, n.get('tub', 0))                  # a group takes a tub first, else a shower
        n['tub'] = n.get('tub', 0)-tubs
        n['shower'] = n.get('shower', 0)-(groups-tubs)
    for k, label in (('wc', 'WATER CLOSET, FLUSH TANK'), ('lav', 'LAVATORY'), ('tub', 'BATHTUB'), ('shower', 'SHOWER'),
                     ('sink', 'KITCHEN SINK'), ('dw', 'DISHWASHER'), ('wd', 'CLOTHES WASHER')):
        if n.get(k, 0):
            rows.append((label, n[k])+tuple(v*n[k] for v in WSFU[k]))
    cold = sum(r[2] for r in rows); hot = sum(r[3] for r in rows); tot = sum(r[4] for r in rows)
    return cold, hot, tot, rows


# ================================ Building 1: Unit 1 ================================
# Page feet: 396 Oak (north) at x 0, the front face at y 0. The mechanical / laundry room
# is on the rear wall between the hall and the pantry; its front wall, the kitchen's rear
# wall, is the one length in it outside the panel's and the heater's working spaces and
# the door's swing, so the riser, the valve, the submeter and the manifolds stand on it.
# The branch comes under the north wall and the slab along that wall's line, ahead of
# Bath 1's fixtures. Bath 2 is fed up the same wall and along the bedrooms' partition to
# its wet wall, the hall's.
from src import building1 as B1M, building2 as B2M
from src.sitework import B1_Y, B2_Y, FRONT_YARD

B1_W, B1_D = B1M.B1_W, B1M.B1_D
B2_W, B2_D = B2M.B2_W, B2M.B2_D
_P1, _P2 = B1M.LEVEL[1]['plan'], B1M.LEVEL[2]['plan']

_U1_Y        = 25.76                      # the line of the mechanical room's front wall
B1_ENTRY     = (-1.5, _U1_Y)
B1_RISER     = (10.6, _U1_Y)
U1_VALVE     = (10.85, _U1_Y)
U1_SUBMETER  = (11.1, _U1_Y)
U1_MANIFOLD  = (11.35, 25.62, 1.2, 0.3)
_U1_UP       = (10.05, _U1_Y)             # where Bath 2's lines rise: in the manifolds' wall, under the bedrooms' partition
U1_RUNS_L1 = [
    # down the hall-side wall to the heater in the rear corner
    Run('HEATER',  ('wh',), [(11.4, 25.9), (10.1, 25.9), (10.1, 30.7)]),
    # down the room, clear of the panel's space, to the W/D on the rear wall
    Run('LAUNDRY', ('wd',), [(11.6, 25.9), (11.6, 29.5), (12.6, 29.5)]),
    # through the hall's ceiling to the wall between the hall and Bath 1, and down it
    Run('BATH 1',  ('lav', 'wc', 'shower'), [(11.35, 25.7), (5.8, 25.7), (5.8, 31.3)]),
    # along the kitchen's rear wall to the south wall's cabinets, and forward inside them
    Run('KITCHEN', ('sink', 'dw'), [(12.5, 25.7), (12.5, 25.35), (18.8, 25.35), (18.8, 16.8)]),
]
# up under the bedrooms' partition and forward to Bath 2's wet wall, the hall's, along it
_U1_BATH2_Y  = round(_P2.y(B1M.Y_FR1)-0.2, 4)       # 2-3/8" inside the hall partition's bath face
U1_RUNS_L2 = [Run('BATH 2', ('lav', 'lav', 'wc', 'tub'), [_U1_UP, (10.05, _U1_BATH2_Y), (18.5, _U1_BATH2_Y)])]


def _closet(rooms, plan, W):
    """The mechanical / laundry room's page rectangle, from the plan's room list."""
    return [_mirror(plan.rect(r), W)[:4] for r in rooms if r[4] == 'MECH / LAUNDRY']

UNIT_1_L1 = Unit('UNIT 1', 1, _fixtures(B1M.F_L1, _P1, B1_W), _closet(B1M.L1_ROOMS, _P1, B1_W),
                 _rects(B1M.F_L1, _P1, B1_W, ('clear', 'whclear')), U1_MANIFOLD, None, U1_VALVE, U1_SUBMETER, U1_RUNS_L1)
UNIT_1_L2 = Unit('UNIT 1', 2, _fixtures(B1M.F_L2, _P2, B1_W), _closet(B1M.L1_ROOMS, _P1, B1_W),
                 [], None, _U1_UP, None, None, U1_RUNS_L2)

BUILDING_1 = Building('BUILDING 1', 1, B1_W, B1_D, B1_ENTRY, B1_RISER,
                      units=[UNIT_1_L1, UNIT_1_L2],
                      trunks=[(('UNIT 1',), [B1_RISER, (U1_MANIFOLD[0], _U1_Y)], False)])

# ================================ Building 2: Units 2 and 3 ================================
# Page feet: 396 Oak at x 0, the courtyard face at y 0, the bearing wall at Y_BEAR. The
# mechanical / laundry room is against the north wall behind the bearing wall: the W/D and
# the panel on that wall, the heater in the rear hall-side corner, the louvered pair in its
# front. The line comes under the north wall and the room to a riser on the hall-side wall
# ahead of the heater, outside both working spaces. Unit 3 stacks over Unit 2 and its supply rises there.
U23_RISER    = (7.3, 16.6)
U23_VALVE    = (7.3, 16.3)
U23_SUBMETER = (7.3, 16.0)
U23_MANIFOLD = (7.45, 14.4, 0.3, 1.4)
# The laundry run ends a short reach short of the washer, and the drawing takes it the rest of
# the way. That reach was typed until 2026-09-21, when the stack bay moved the appliance
# 1-3/4" into the room and the run's end went INSIDE it: the connector vanished and its CW
# label printed on the hot line. It is read from the washer now, so the appliance carries it.
WD_STUB = IN(1.5)
_U23_WD = B2M.PLAN_B2.keep((B2M.WD_X, B2M.WD_Y, B2M.WD_W, B2M.WD_H))
U23_WD_SUPPLY_X = B2_W-_U23_WD[0]+WD_STUB

U23_RUNS = [
    # forward along the hall-side wall, then along the room's front wall to the W/D
    Run('LAUNDRY', ('wd',), [(7.5, 14.45), (7.5, 13.15), (U23_WD_SUPPLY_X, 13.15)]),
    # back along the same wall to the heater in the corner
    Run('HEATER',  ('wh',), [(7.6, 15.75), (7.6, 16.85)]),
    # out through the bearing wall's louvered opening side into the kitchen's ceiling,
    # to the north wall's cabinets and forward inside them to the sink
    Run('KITCHEN', ('sink',), [(7.65, 14.45), (7.65, 12.2), (1.2, 12.2), (1.2, 5.2)]),
    # across the hall's ceiling and along the wall between the bath and Bedroom 1
    Run('BATH',    ('lav', 'wc', 'tub'), [(7.75, 15.0), (8.1, 15.0), (8.1, 18.6), (18.2, 18.6)]),
]


def _u23(level):
    return Unit('UNIT %d' % (level+1), level,
                fixtures=_fixtures(B2M.F_B2, B2M.PLAN_B2, B2_W),
                closets=_closet(B2M.B2U, B2M.PLAN_B2, B2_W),
                clears=_rects(B2M.F_B2, B2M.PLAN_B2, B2_W, ('clear', 'whclear')),
                manifold=U23_MANIFOLD, riser=U23_RISER if level == 2 else None,
                valve=U23_VALVE, submeter=U23_SUBMETER, runs=U23_RUNS)


B2_ENTRY = (-1.5, U23_RISER[1])
BUILDING_2 = Building('BUILDING 2', 2, B2_W, B2_D, B2_ENTRY, U23_RISER,
                      units=[_u23(1), _u23(2)],
                      # both units are fed at the riser itself: no trunk
                      trunks=[(('UNIT 2', 'UNIT 3'), [U23_RISER], False)])

BUILDINGS = [BUILDING_1, BUILDING_2]

# ================================ the one service ================================
# From the main to each building's wall, down the north side yard: the assumed run to the
# Oak lot line, the front yard, and along the building to its entry. Building 2's goes on
# past Building 1's branch, so its length is the longer and sizes the service.
YARD_X = -2.5                       # the line in the north side yard, feet off the buildings' north walls
def site_water():
    """C-101's water, site feet: the service down the north side yard from the Oak lot line
       to Building 2's supply, each building's supply to its wall, and the meter pit."""
    from src.sitework import B1_X, B2_X
    x = B1_X+YARD_X
    y1, y2 = B1_Y+B1_ENTRY[1], B2_Y+B2_ENTRY[1]
    return dict(service=[(x, 0.0), (x, y2)], supplies=[[(x, y1), (B1_X, y1)], [(x, y2), (B2_X, y2)]], pit=(x, 2.0))


UPSTREAM = {1: MAIN_TO_LOT+FRONT_YARD+B1_ENTRY[1]+abs(YARD_X),
            2: MAIN_TO_LOT+FRONT_YARD+(B2_Y-B1_Y)+B2_ENTRY[1]+abs(YARD_X)}


# ================================ the working spaces ================================
# Two spaces stand in every mechanical closet and they answer to different codes: the
# panel's, NEC 110.26(A) — 36" deep off the panel face, 30" wide or the equipment's,
# whichever is greater — and the heater's, RCO M1305.1's 30" x 30" at its control side.
# They may overlap each other; what may NOT happen is equipment standing in one of them.
#
# A storage tank is the deepest thing in the room, so this is the rule it pushes hardest.
# the conversion pushes hardest. `clears` above mixes the two rectangles together for
# the manifold check; these keep them apart so check_working_spaces() can name which is
# which. Unit 1's are authored directly, the panel's first.
PANEL_SPACE = {'UNIT 1': _one(B1M.F_L1, _P1, B1_W, 'clear'), 'UNITS 2 / 3': _one(B2M.F_B2, B2M.PLAN_B2, B2_W, 'clear')}
HEATER_SPACE = {'UNIT 1': _one(B1M.F_L1, _P1, B1_W, 'whclear'), 'UNITS 2 / 3': _one(B2M.F_B2, B2M.PLAN_B2, B2_W, 'whclear')}
HEATER_RECT = {'UNIT 1': _one(B1M.F_L1, _P1, B1_W, 'wh'), 'UNITS 2 / 3': _one(B2M.F_B2, B2M.PLAN_B2, B2_W, 'wh')}
CLOSET = {'UNIT 1': UNIT_1_L1.closets[0], 'UNITS 2 / 3': BUILDING_2.units[0].closets[0]}
# SF of tank allowed inside a panel's working space: none.
PANEL_SPACE_EXCEPTION = {}
# The stud grid maps a typed rectangle corner by corner, so a 30" space comes back a
# sixteenth or an eighth either side of 30". Every figure below is the DRAWN one and is
# printed; this is the slack the asserts allow it, not a relaxation of the code minimum.
GRID_SLACK = IN(0.25)
# Unit 1's room has a swing door: both of its spaces stay inside it. Units 2 / 3 borrow
# theirs through the open louvered pair.
U1_SPACES_IN_ROOM = ('UNIT 1',)


def working_space_violations():
    v, lines = [], []
    for nm in ('UNIT 1', 'UNITS 2 / 3'):
        tank, panel, work, closet = HEATER_RECT[nm], PANEL_SPACE[nm], HEATER_SPACE[nm], CLOSET[nm]
        w, h = _overlap_box(tank, panel)
        area = w*h
        cap = PANEL_SPACE_EXCEPTION.get(nm, 0.0)
        if area > cap+1e-6:
            v.append('%s: the water heater stands %s x %s inside the panel working space%s'
                     % (nm, fmt(w), fmt(h), '' if not cap else ', over the %.2f SF recorded' % cap))
        # the heater's own space has to REACH its appliance — it starts at the control
        # face, so it touches the tank rather than overlapping it
        gap = max(work[0]-(tank[0]+tank[2]), tank[0]-(work[0]+work[2]),
                  work[1]-(tank[1]+tank[3]), tank[1]-(work[1]+work[3]))
        if gap > GRID_SLACK:
            v.append('%s: the heater working space stands %s off the heater' % (nm, fmt(gap)))
        if min(work[2], work[3]) < WH_WORK-GRID_SLACK:
            v.append('%s: the heater working space is under %s square' % (nm, fmt(WH_WORK)))
        # Unit 1's room has no louvered pair to borrow through: both of its working spaces
        # stay inside the room. Units 2 to 5 borrow the heater's through the open pair.
        if nm in U1_SPACES_IN_ROOM:
            for label, sp in (('panel', panel), ('heater', work)):
                sw, sh = _overlap_box(sp, closet)
                if abs(sw-sp[2]) > GRID_SLACK or abs(sh-sp[3]) > GRID_SLACK:
                    v.append('%s: the %s working space leaves the mechanical room' % (nm, label))
        # and it may project through a door, but the tank itself may not leave its closet
        ow, oh = _overlap_box(tank, closet)
        if abs(ow-tank[2]) > GRID_SLACK or abs(oh-tank[3]) > GRID_SLACK:
            v.append('%s: the water heater leaves its mechanical closet' % nm)
        lines.append('   %-12s %d gal, tank %s x %s; %s in the panel space; working space %s x %s'
                     % (nm, WH_TANKS[nm][0], fmt(tank[2]), fmt(tank[3]),
                        'clear' if area <= 1e-9 else '%s x %s' % (fmt(w), fmt(h)),
                        fmt(work[2]), fmt(work[3])))
    return v, lines


def check_working_spaces():
    """From check_plumbing(): no water heater stands in a panel's NEC 110.26(A) working
       space, every heater keeps RCO M1305.1's 30" x 30" at its control side, and no
       tank leaves its room."""
    v, lines = working_space_violations()
    print('MECHANICAL CLOSETS — ELECTRIC STORAGE HEATERS, NEC 110.26(A) AND RCO M1305.1:')
    for ln in lines:
        print(ln)
    assert not v, 'WORKING SPACES:\n  '+'\n  '.join(v)


# ================================ sizing ================================
def unit_wsfu(b, name):
    """A dwelling's tally across its levels — Unit 1 has two, the others one."""
    fx = [f for u in b.units if u.name == name for f in u.fixtures]
    return tally(fx)


def developed_length(b, name):
    """From the main to the dwelling's most remote outlet: the assumed run to the wall,
       the service inside, the trunk, the rise to a Level 2 unit, and its longest run."""
    L = UPSTREAM[b.number]+_length([b.entry, b.riser])
    L += sum(_length(path) for names, path, _under in b.trunks if name in names)
    longest = 0.0
    for u in b.units:
        if u.name != name: continue
        if u.level == 2: L += levels.FLOOR_RISE
        for r in u.runs:
            for f in run_fixtures(r, u):
                q, e, i = stub(r, f, where=True)
                longest = max(longest, _length(r.path[:i+1]+[q])+math.hypot(e[0]-q[0], e[1]-q[1]))
    return L+longest


def building_length(b):
    return max(developed_length(b, n) for n in unit_names(b))


def service():
    """The one service and its meter: every dwelling's fixture units at the longest
       developed length on the lot."""
    total = sum(unit_wsfu(b, n)[2] for b in BUILDINGS for n in unit_names(b))
    length = max(building_length(b) for b in BUILDINGS)
    meter, pipe = pipe_for(total, length)
    return dict(total=total, length=length, meter=meter, service=pipe)


def sizes(b):
    """A building's supply — its branch off the one service, sized on the service's meter
       for the building's own fixture units and length — and each unit trunk on that meter."""
    sv = service()
    total = sum(unit_wsfu(b, n)[2] for n in unit_names(b))
    supply = pipe_for(total, building_length(b), meter=sv['meter'])[1]
    trunks = {n: pipe_for(unit_wsfu(b, n)[2], developed_length(b, n), meter=sv['meter'])[1] for n in unit_names(b)}
    return dict(total=total, length=building_length(b), meter=sv['meter'], service=supply, trunks=trunks)


# ================================ the checker ================================


def plumbing_violations():
    v = []
    check_working_spaces()
    for b in BUILDINGS:
        for u in b.units:
            who = '%s %s level %d' % (b.name, u.name, u.level)
            have = sorted(f.kind for f in u.fixtures)
            reached = sorted(k for r in u.runs for k in r.fixtures)
            for k in set(have)|set(reached):
                if have.count(k) != reached.count(k):
                    v.append('%s: %d %s fixture(s) but %d reached by a run' % (who, have.count(k), k, reached.count(k)))
            for r in u.runs:
                if u.manifold is not None:
                    at = [(u.manifold[0]-0.3, u.manifold[1]-0.3, u.manifold[2]+0.6, u.manifold[3]+0.6)]
                else:
                    at = [(u.riser[0]-0.3, u.riser[1]-0.3, 0.6, 0.6)] if u.riser else []
                if not _inside_any(r.path[0], at):
                    v.append('%s: run %s does not start at the manifolds' % (who, r.group))
                if pipe_size(HOME_RUN) < max(pipe_size(MIN_SUPPLY.get(k, '1/2')) for k in r.fixtures):
                    v.append('%s: run %s home run is under Table 604.5' % (who, r.group))
            for what, pt in (('the manifolds', u.manifold and u.manifold[:2]), ('the valve', u.valve),
                             ('the submeter', u.submeter), ('the riser', u.riser)):
                if pt is not None and not _inside_any(pt, u.closets):
                    v.append('%s: %s at (%.2f, %.2f) is outside the mechanical closet' % (who, what, pt[0], pt[1]))
            for cl in u.clears:
                if u.manifold is not None and _overlap(u.manifold, cl):
                    v.append('%s: the manifolds stand in a working space' % who)
            if u.level == 1 and (u.manifold is None or u.valve is None or u.submeter is None):
                v.append('%s: a Level 1 unit without manifolds, a valve and a submeter' % who)
            if u.level == 2 and u.riser is None:
                v.append('%s: a Level 2 unit with no riser' % who)
        if not b.entry[0] < 0 <= b.riser[0]:
            v.append('%s: the supply does not come through the north wall' % b.name)
        for names, path, under in b.trunks:
            for n in names:
                if n not in unit_names(b):
                    v.append('%s: a trunk to %s, which it has no unit of' % (b.name, n))
            if path[0] != b.riser:
                v.append('%s: the trunk to %s does not start at the service riser' % (b.name, ' / '.join(names)))
        for n in unit_names(b):
            fed = [t for t in b.trunks if n in t[0]]
            if len(fed) != 1:
                v.append('%s: %d trunks to %s' % (b.name, len(fed), n))
        try:
            s = sizes(b)
        except ValueError as e:
            v.append('%s: %s' % (b.name, e)); continue
        if pipe_size(s['service']) < pipe_size('3/4'):
            v.append('%s: service under the 3/4" minimum' % b.name)
        if pipe_size(HEATER_CONN) < pipe_size('3/4'):
            v.append('%s: heater connections under 3/4"' % b.name)
        if abs(s['total']-sum(tally(u.fixtures)[2] for u in b.units)) > 1e-9:
            v.append('%s: the building tally is not the sum of its units' % b.name)
    sv = service()
    if pipe_size(sv['service']) < pipe_size('3/4'):
        v.append('the service is under the 3/4" minimum')
    if any(pipe_size(sizes(b)['service']) > pipe_size(sv['service']) for b in BUILDINGS):
        v.append("a building's supply is larger than the service it comes off")
    return v


def check_plumbing():
    """From build.check_model(): every unit tallied and every building sized, or the
       build stops with the unit and the rule named."""
    v = plumbing_violations()
    assert not v, 'PLUMBING: %d violation(s):\n  ' % len(v)+'\n  '.join(v)
    for b in BUILDINGS:
        s = sizes(b)
        for n in unit_names(b):
            c, h, t, rows = unit_wsfu(b, n)
            print('PLUMBING %s %-6s %d fixtures  %.1f WSFU (%.1f cold, %.1f hot)  trunk %s"  %s developed'
                  % (b.name, n, sum(r[1] for r in rows), t, c, h, s['trunks'][n], fmt(developed_length(b, n))))
        print('PLUMBING %s: %.1f WSFU, %s developed: %s" supply off the service' % (b.name, s['total'], fmt(s['length']), s['service']))
    sv = service()
    print('PLUMBING SERVICE: %.1f WSFU, %s developed, %s psi assumed: %s" service and meter %s", Table E201.1'
          % (sv['total'], fmt(sv['length']), PRESSURE, sv['service'], sv['meter']))

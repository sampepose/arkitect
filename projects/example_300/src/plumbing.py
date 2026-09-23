"""The water supply model: what P-102 and P-103 draw, checked before anything draws.

The fixtures are the model's — the furniture lists the floor plans draw, and Unit 1's
from the study constants its bath and kitchen are drawn from — so a tub that moves on
A-101 moves here. The service, the manifolds and the home runs are authored here in
PAGE FEET (Sage on the left, S Elm at the top, y down), the system the electrical
model uses for Unit 1 and the house lists; the Units 2/3 and 4/5 fixtures are brought
into it through the regrid and the sheet mirror, the way their symbols reach the page.

Sizing is IPC Appendix E: water supply fixture units from Table E103.3(2), private
occupancy, the bathroom group taken as a group; the service, the meter and each trunk
from Table E201.1 at an assumed static pressure and the developed length measured off
the drawn runs plus an assumed distance to the public main. Appendix E is the
accepted engineering practice OPC 604.1 asks for; Ohio adopts IPC chapters 2 to 15 by
reference and not the appendices. Both assumptions print on the sheet.

Drainage is P-601's. Nothing here draws.
"""
import math
from collections import namedtuple
from lib.units import IN, fmt
from src import levels

# ================================ the tables: shared, see codes/ohio/water_supply.py
from codes.ohio.water_supply import (BATH_GROUP, FIXTURE_KINDS, MIN_SUPPLY, SUPPLY_KINDS, WSFU, pipe_size,
                                     row_for)
from lib.model.water import (_inside_any, _length, _mirror, _one, _overlap, _overlap_box, _rects,
                             run_fixtures, stub, unit_names)


# ================================ this project's choices ================================
HOME_RUN = '1/2'
HEATER_CONN = '3/4'               # the storage heater's cold inlet and hot outlet

# ================================ the storage heaters ================================
# One electric storage heater per dwelling, P-601 notes 6 and 7, SIZED BY BEDROOM COUNT:
# 40 gallons for the four two-bedroom, one-bath flats and 50 for Unit 1's four bedrooms
# and two baths. Both take two 4,500 W non-simultaneous elements, so every electrical
# figure in the set is the same whichever a dwelling gets.
#
# THE DIAMETER IS THE DESIGN CONSTRAINT, not the gallons. A tankless hung 11" off a
# wall; a tank stands on the floor and eats depth, and these closets are barely deeper
# than the 36" NEC 110.26(A) wants in front of a panel. A 40-gallon tall tank is 18"
# across (Rheem, A.O. Smith and Bradford White all run 18" x about 61"), and that 18"
# is what lets Units 2/3 and Unit 1 keep their panels' working spaces wholly clear with
# nothing moved. A 22" tank does not: it lands 2-3/4" inside the Units 2/3 band and
# 1'-7" x 1'-1" inside Units 4/5's. Unit 1 has the room for the 50-gallon's 20".
WH_TANKS     = {'UNIT 1': (50, IN(20)), 'UNITS 2 / 3': (40, IN(18)), 'UNITS 4 / 5': (40, IN(18))}
WH_GALLONS   = 40                 # what four of the five take; Unit 1's is WH_TANKS
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
WH_PAN_UNITS = ('UNIT 3', 'UNIT 5')
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
MAIN_TO_WALL = 40.0               # feet of service from the main to the building wall, assumed


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
# One building: the service through its Sage wall to a riser inside, and the trunks
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
    groups = min(n.get('wc', 0), n.get('lav', 0), n.get('tub', 0))
    rows = []
    if groups:
        rows.append(('BATHROOM GROUP, FLUSH TANK WC', groups)+tuple(v*groups for v in BATH_GROUP))
        for k in ('wc', 'lav', 'tub'): n[k] -= groups
    for k, label in (('wc', 'WATER CLOSET, FLUSH TANK'), ('lav', 'LAVATORY'), ('tub', 'BATHTUB'),
                     ('sink', 'KITCHEN SINK'), ('dw', 'DISHWASHER'), ('wd', 'CLOTHES WASHER')):
        if n.get(k, 0):
            rows.append((label, n[k])+tuple(v*n[k] for v in WSFU[k]))
    cold = sum(r[2] for r in rows); hot = sum(r[3] for r in rows); tot = sum(r[4] for r in rows)
    return cold, hot, tot, rows


# ================================ Units 2 and 3 ================================
# Building 1, page feet: Sage x 0, the rear wall y 48, W4 at Y_SEP_TOP. The kitchen
# is on the Sage wall, the bath's wet wall is its Sage-side wall, and the
# mechanical closet stands on the rear wall with the W/D at its Sage end and the
# heater in its bay at the other. The two closets stack, so Unit 3's supply rises in
# Unit 2's closet and its runs are Unit 2's, one level up.
from src.building1 import (BX0, BX1, BY1, D_STUD, F_U23, MX0, MX1, PLAN_L1, PLAN_L2, R0, U23,
                           W_STUD, YT, Y_SEP_BOT, Y_SEP_TOP, site_x, site_y)
from src.building2 import B2U, B2_W, F_B2, PLAN_B2

# The riser and the manifolds stand in the strip of rear wall between the W/D and the
# heater's bay, the one part of the closet outside both working spaces.
U23_RISER    = (11.30, 46.95)
U23_VALVE    = (11.30, 46.50)
U23_SUBMETER = (11.30, 46.05)
U23_MANIFOLD = (11.45, 47.15, 0.85, 0.32)
U23_RUNS = [
    Run('LAUNDRY', ('wd',),  [(11.45, 47.35), (11.15, 47.35)]),
    Run('HEATER',  ('wh',),  [(12.30, 47.35), (12.6, 47.35)]),
    # north through the closet's front wall and the living-room ceiling to the bath's
    # south wall, then along its wet wall past the lav, the wc and the tub
    Run('BATH',    ('lav', 'wc', 'tub'), [(11.98, 47.15), (11.98, 44.24), (11.98, 31.6), (9.35, 31.6), (9.35, 24.5)]),
    # the same way to the kitchen's end of the living room, then to the Sage wall
    # and up it, under the sink and the dishwasher
    Run('KITCHEN', ('sink', 'dw'), [(11.78, 47.15), (11.78, 44.24), (11.78, 33.2), (1.2, 33.2), (1.2, 27.5)]),
]


def _u23(level):
    plan = PLAN_L1 if level == 1 else PLAN_L2
    return Unit('UNIT %d' % (level+1), level,
                fixtures=_fixtures(F_U23, plan, 26.0),
                closets=_rects(U23, plan, 26.0, ('MECH',)),
                clears=_rects(F_U23, plan, 26.0, ('clear', 'whclear')),
                manifold=U23_MANIFOLD, riser=U23_RISER if level == 2 else None,
                valve=U23_VALVE, submeter=U23_SUBMETER, runs=U23_RUNS)


# ================================ Unit 1 ================================
# The study's inches through site_x / site_y, as the electrical model places its
# devices. The mechanical strip is between the stair enclosure and the wet wall; the
# laundry nook is under the Level 2 landing against Sage; the under-stair closet is
# entered from the strip and has full height under the top of the flight. The heater
# stands on the wet wall opposite the panel, the two baths on its other side, one above
# the other.
_I = IN


def _u1r(x, y, w, h, kind):
    return Fixture(site_x(x), site_y(y), w, h, kind)


_U1_BATH = [_u1r(BX0+_I(.5), R0+_I(.5), _I(21), _I(24), 'lav'),
            Fixture(site_x(BX0+_I(18.5))-_I(14), site_y(R0+_I(39.5))-_I(10), _I(28), _I(20), 'wc'),
            _u1r(BX0+_I(.5), BY1-_I(30.5), BX1-BX0-_I(1), _I(30), 'tub')]
U1_L1_FIXTURES = _U1_BATH+[
    _u1r(W_STUD-_I(24), _I(69), _I(24), _I(36), 'sink'),
    _u1r(W_STUD-_I(24), _I(45), _I(24), _I(24), 'dw'),
    _u1r(_I(4), D_STUD-_I(31.5), _I(32), _I(27), 'wd'),
    _u1r(MX1-_I(20), _I(202), _I(20), _I(20), 'wh'),
]
U1_L2_FIXTURES = list(_U1_BATH)
# where Unit 1's equipment may stand: the mechanical strip, the laundry nook under the
# landing, and the under-stair closet
U1_CLOSETS = [(site_x(MX0), site_y(R0), MX1-MX0, D_STUD-R0),
              (site_x(0), site_y(YT), MX0, D_STUD-YT),
              (site_x(_I(2)), site_y(_I(170)), _I(36), _I(66))]
# The panel's NEC 110.26(A) space is unchanged: the 50-gallon tank stands 5-3/4" past
# the end of its 30" width band, which is why the tank is opposite the panel rather than
# beside it. The tank's own 30" x 30" is taken off the control side facing UP the strip,
# not across it: the strip is 3'-7" wide and 20" of tank plus 30" of space is 4'-2",
# which taken across would run 7" into the stair enclosure wall. Along the strip it is
# held FLUSH TO THE STRIP'S EAST WALL (MX1), across the tank's whole 20" face: it used to
# start at the tank's west edge and so ran 10" past MX1, through the partition into Bath
# 1, which nothing checked. `U1_SPACES_IN_ROOM` now does. It stops short of the
# manifolds, which check_plumbing() holds out of both spaces.
U1_CLEARS = [(site_x(_I(49.25)), site_y(_I(166.25)), _I(36), _I(30)),    # the panel's, NEC 110.26(A)
             (site_x(MX1-_I(30)), site_y(_I(172)), _I(30), _I(30))]      # the heater's, RCO M1305.1
# The service rises in the under-stair closet; Unit 1's manifolds are on the wet wall
# under the heater's bay, past its working space, where the run to Bath 1 is a wall away.
B1_ENTRY     = (-1.5, 17.4)
B1_RISER     = (1.3, 17.4)
U1_MANIFOLD  = (7.45, 19.45, 0.35, 0.9)
_U1_M        = (7.6, 19.9)
U1_RUNS_L1 = [
    Run('HEATER',  ('wh',), [_U1_M, (7.6, 18.9)]),
    Run('LAUNDRY', ('wd',), [_U1_M, (7.6, 20.9), (2.3, 20.9)]),
    Run('BATH 1',  ('lav', 'wc', 'tub'), [_U1_M, (8.1, 19.9), (8.1, 14.6)]),
    # north up the strip, across the living-room ceiling with the F2 joists, then to the
    # counter on the parcel wall
    Run('KITCHEN', ('sink', 'dw'), [_U1_M, (7.6, 13.6), (23.2, 13.6), (23.2, 5.0)]),
]
U1_RUNS_L2 = [Run('BATH 2', ('lav', 'wc', 'tub'), [_U1_M, (8.1, 19.9), (8.1, 14.6)])]

# the valve and submeter on the trunk as it reaches the strip; Level 2 has neither —
# Bath 2's five lines rise in the wet wall from the Level 1 manifolds
UNIT_1_L1 = Unit('UNIT 1', 1, U1_L1_FIXTURES, U1_CLOSETS, U1_CLEARS, U1_MANIFOLD, None, (6.7, 19.8), (6.15, 19.8), U1_RUNS_L1)
UNIT_1_L2 = Unit('UNIT 1', 2, U1_L2_FIXTURES, U1_CLOSETS, U1_CLEARS, None, _U1_M, None, None, U1_RUNS_L2)

BUILDING_1 = Building('BUILDING 1', 1, 26.0, 48.0, B1_ENTRY, B1_RISER,
                      units=[UNIT_1_L1, UNIT_1_L2, _u23(1), _u23(2)],
                      # Unit 1's line through the stair wall into the strip; Units 2/3's
                      # under the slab along Sage and across to their closet's riser
                      trunks=[(('UNIT 1',), [B1_RISER, (1.3, 19.8), (7.45, 19.8)], False),
                              (('UNIT 2', 'UNIT 3'), [B1_RISER, (1.3, 46.95), U23_RISER], True)])

# ================================ Units 4 and 5 ================================
# Building 2, page feet: Sage x 0, the courtyard y 0, the bearing wall at y 15. The
# mechanical closet is in the Sage corner of the front band: W/D across its front,
# the panel and the heater on the Sage wall, its louvered pair on the kitchen side.
# The service comes under the Sage wall straight into it; the riser and the
# manifolds are on the closet's far wall beside the W/D, the one place outside the
# panel's and the heater's working spaces. Unit 5 stacks over Unit 4 and its supply
# rises in the same closet.
U45_RISER    = (3.72, 12.2)
U45_VALVE    = (3.72, 11.85)
U45_SUBMETER = (3.72, 11.45)
U45_MANIFOLD = (3.45, 9.95, 0.3, 1.2)
U45_RUNS = [
    Run('LAUNDRY', ('wd',), [(3.45, 10.55), (3.3, 10.55)]),
    # down beside the W/D, then along the wall to the heater's inlet and outlet
    Run('HEATER',  ('wh',), [(3.45, 10.85), (3.3, 10.85), (3.3, 13.6), (1.5, 13.6)]),
    Run('KITCHEN', ('sink',), [(3.55, 10.55), (3.55, 4.66), (2.6, 4.66)]),
    # north out of the closet, along the front band's ceiling to the hall opening in the
    # bearing wall, through it, and down the hall's and the bath's parcel-side wall
    Run('BATH',    ('lav', 'wc', 'tub'), [(3.68, 10.55), (3.68, 9.3), (15.2, 9.3), (15.2, 26.3)]),
]


def _u45(level):
    return Unit('UNIT %d' % (level+3), level,
                fixtures=_fixtures(F_B2, PLAN_B2, B2_W),
                closets=_rects(B2U, PLAN_B2, B2_W, ('MECH',)),
                clears=_rects(F_B2, PLAN_B2, B2_W, ('clear', 'whclear')),
                manifold=U45_MANIFOLD, riser=U45_RISER if level == 2 else None,
                valve=U45_VALVE, submeter=U45_SUBMETER, runs=U45_RUNS)


B2_ENTRY = (-1.5, 12.2)
BUILDING_2 = Building('BUILDING 2', 2, 26.0, 28.0, B2_ENTRY, U45_RISER,
                      units=[_u45(1), _u45(2)],
                      # both units are fed at the service riser itself: no trunk
                      trunks=[(('UNIT 4', 'UNIT 5'), [U45_RISER], False)])

BUILDINGS = [BUILDING_1, BUILDING_2]


# ================================ the working spaces ================================
# Two spaces stand in every mechanical closet and they answer to different codes: the
# panel's, NEC 110.26(A) — 36" deep off the panel face, 30" wide or the equipment's,
# whichever is greater — and the heater's, RCO M1305.1's 30" x 30" at its control side.
# They may overlap each other; what may NOT happen is equipment standing in one of them.
#
# A 22" storage tank is 11" deeper than the tankless it replaced, so this is the rule
# the conversion pushes hardest. `clears` above mixes the two rectangles together for
# the manifold check; these keep them apart so check_working_spaces() can name which is
# which. Unit 1's are authored directly, the panel's first.
PANEL_SPACE = {'UNITS 2 / 3': _one(F_U23, PLAN_L1, 26.0, 'clear'),
               'UNITS 4 / 5': _one(F_B2, PLAN_B2, B2_W, 'clear'),
               'UNIT 1': U1_CLOSETS and U1_CLEARS[0]}
HEATER_SPACE = {'UNITS 2 / 3': _one(F_U23, PLAN_L1, 26.0, 'whclear'),
                'UNITS 4 / 5': _one(F_B2, PLAN_B2, B2_W, 'whclear'),
                'UNIT 1': U1_CLEARS[1]}
HEATER_RECT = {'UNITS 2 / 3': _one(F_U23, PLAN_L1, 26.0, 'wh'),
               'UNITS 4 / 5': _one(F_B2, PLAN_B2, B2_W, 'wh'),
               'UNIT 1': tuple(next(f for f in U1_L1_FIXTURES if f.kind == 'wh')[:4])}
CLOSET = {'UNITS 2 / 3': _rects(U23, PLAN_L1, 26.0, ('MECH',))[0],
          'UNITS 4 / 5': _rects(B2U, PLAN_B2, B2_W, ('MECH',))[0],
          'UNIT 1': U1_CLOSETS[0]}
# Units 4 and 5 CANNOT keep the tank out of the panel's space: the closet is 3'-4-3/4"
# deep, so everything in it is inside the panel's 36", and 2'-3" of W/D plus 2'-6" of
# 110.26(A)(2) band plus 1'-10" of tank is 6'-7" on a 5'-6" wall. The overlap is named
# and pinned here so it cannot silently grow, and it is an open item for the designer, not a
# thing the model pretends away.
PANEL_SPACE_EXCEPTION = {'UNITS 4 / 5': 0.95}     # SF of tank inside the panel space
# The stud grid maps a typed rectangle corner by corner, so a 30" space comes back a
# sixteenth or an eighth either side of 30". Every figure below is the DRAWN one and is
# printed; this is the slack the asserts allow it, not a relaxation of the code minimum.
GRID_SLACK = IN(0.25)
U1_SPACES_IN_ROOM = ('UNIT 1',)


def working_space_violations():
    v, lines = [], []
    for nm in ('UNIT 1', 'UNITS 2 / 3', 'UNITS 4 / 5'):
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
       tank leaves its closet. Units 4/5 carry a named, pinned exception."""
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
    L = MAIN_TO_WALL+_length([b.entry, b.riser])
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


def sizes(b):
    """The building's service and meter, and each unit trunk on that meter."""
    total = sum(unit_wsfu(b, n)[2] for n in unit_names(b))
    meter, service = pipe_for(total, building_length(b))
    trunks = {n: pipe_for(unit_wsfu(b, n)[2], developed_length(b, n), meter=meter)[1] for n in unit_names(b)}
    return dict(total=total, length=building_length(b), meter=meter, service=service, trunks=trunks)


# ================================ the checker ================================


def _crosses_band(path, lo, hi):
    return any(min(a[1], b[1]) < hi and max(a[1], b[1]) > lo for a, b in zip(path, path[1:]))


def plumbing_violations():
    v = []
    check_working_spaces()
    for b in BUILDINGS:
        sep = (Y_SEP_TOP, Y_SEP_BOT) if b.number == 1 else None
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
                if sep and _crosses_band(r.path, *sep):
                    v.append('%s: run %s crosses the W4 separation' % (who, r.group))
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
            v.append('%s: the service does not come through the Sage wall' % b.name)
        for names, path, under in b.trunks:
            for n in names:
                if n not in unit_names(b):
                    v.append('%s: a trunk to %s, which it has no unit of' % (b.name, n))
            if path[0] != b.riser:
                v.append('%s: the trunk to %s does not start at the service riser' % (b.name, ' / '.join(names)))
            if sep and _crosses_band(path, *sep) and not under:
                v.append('%s: the trunk to %s crosses W4 above the slab' % (b.name, ' / '.join(names)))
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
    # Unit 1's rectangles are the electrical model's, so the two trade models agree
    from src.electrical import LEVEL_U1_L1
    for kind, rects in (('lav', LEVEL_U1_L1.lavs), ('sink', LEVEL_U1_L1.sinks), ('wd', LEVEL_U1_L1.wds)):
        mine = [f[:4] for f in U1_L1_FIXTURES if f.kind == kind]
        if [tuple(round(v, 6) for v in r) for r in mine] != [tuple(round(v, 6) for v in r[:4]) for r in rects]:
            v.append('Unit 1 %s rectangle differs from the electrical model' % kind)
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
        print('PLUMBING %s: %.1f WSFU, %s developed, %s psi assumed: %s" service and meter %s", Table E201.1'
              % (b.name, s['total'], fmt(s['length']), PRESSURE, s['service'], s['meter']))

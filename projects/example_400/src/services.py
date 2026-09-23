"""Service equipment on the outside walls: meters, outdoor units, the telecom demarcations.

BUILDING 1's is on its NORTH wall (the designer, 2026-09-18), which has no Level 1 opening and
faces 396 Oak across the 5'-0" side yard and swale S-3: nothing walks there, and nothing
is seen from Oak or the courtyard. The boxes stand on the length of wall behind the
dining area — not on the stair, whose wall a feeder cannot cross, nor on Bath 1, whose
shower is against that wall inside.

BUILDING 2's meters are on its NORTH wall and its outdoor units on its SOUTH. The meter
bank stands outside the mechanical / laundry rooms, back to back with both unit panels,
and the parking walk in front of it is its NEC 110.26(A) working space. An outdoor unit
would stand 14" into that 3'-0" walk, so both hang on the south wall, over swale S-4's
yard, between the living room's W-C and Bedroom 1's egress W-A.

`along` is feet from the building's front face along the wall (Oak for Building 1, the
courtyard for Building 2); `z` is above finished grade. Heights are the set's own, not AEP
Ohio's or a selected unit's. Outdoor units hang on wall brackets: the yards under them are
swale banks, and a bracket keeps them out of snow.
"""
from collections import namedtuple
from arkitect.lib.units import IN, fmt
from src import building1 as B1M, building2 as B2M, levels
from src.openings import WIN_GEOM
from src.sitework import SIDE_YARD

Box = namedtuple("Box", "mark kind building wall along0 along1 z0 z1 depth name")

METER_Z = (4.0, 6.0)          # a meter's center above grade, the range utilities take
WORK_D, WORK_W = 3.0, IN(30)  # NEC 110.26(A): clear in front of a meter, and its width
BOX_GAP = 1.0                 # between boxes along a wall
GRADE_CLR = IN(4)             # the least any box stands above finished grade
LEADER_CLR = 1.0              # off a roof leader
ODU_EGRESS_CLR = 3.0          # an outdoor unit off a W-A, the bedrooms' escape opening
ODU_DRYER_CLR = 3.0           # and off a dryer cap's bay, along the wall
CAP_CLR = 1.0                 # any other box off a dryer cap's bay
ODU_W, ODU_Z, ODU_D = 3.0, (2.5, 5.0), IN(14)

# Building 1: the wall behind the dining area, past the stair's foot landing, short of Bath 1.
_run0 = B1M.PLAN_B1_L1.y(B1M.Y_FOOT_RISER+B1M.B1_STAIR.foot_landing)
B1_NORTH_RUN = (_run0, B1M.PLAN_B1_L1.y(B1M.Y_KIT))
RUNS = {(1, "NORTH"): B1_NORTH_RUN}

# Building 2: the dryer's bay on the north wall, which the meter bank stands just past; the
# units between the south wall's two windows.
_dr = B2M.B2_DR_BAY
_s_wins = sorted(B2M.PLAN_B2.y(w[1]) for w in B2M.B2win if w[3] == 'v' and w[0] < 1.0)
_wc_end = _s_wins[0]+B2M.B2_PARCEL_WIN[0][2]

EQUIPMENT = [
    Box("HP-1", "odu", 1, "NORTH", _run0+0.2, _run0+0.2+ODU_W, ODU_Z[0], ODU_Z[1], ODU_D, "HEAT PUMP OUTDOOR UNIT, ON A WALL BRACKET"),
    Box("EM-1", "meter", 1, "NORTH", _run0+4.7, _run0+4.7+IN(14), 3.75, 6.25, IN(6), "METER-MAIN, E-101"),
    Box("TC-1", "telecom", 1, "NORTH", _run0+6.87, _run0+7.87, 3.75, 4.75, IN(4), "TELECOM / CABLE DEMARCATION"),
    Box("TC-2", "telecom", 2, "NORTH", _dr[0]-CAP_CLR-1.5, _dr[0]-CAP_CLR-0.5, 3.75, 4.75, IN(4), "TELECOM / CABLE DEMARCATION"),
    Box("EM-2", "meter", 2, "NORTH", _dr[1]+CAP_CLR, _dr[1]+CAP_CLR+IN(28), 3.5, 6.5, IN(6), "TWO-METER BANK, E-102"),
    Box("HP-2", "odu", 2, "SOUTH", _wc_end+1.5, _wc_end+1.5+ODU_W, ODU_Z[0], ODU_Z[1], ODU_D, "UNIT 2 HEAT PUMP OUTDOOR UNIT, ON A WALL BRACKET"),
    Box("HP-3", "odu", 2, "SOUTH", _wc_end+1.5+ODU_W+BOX_GAP, _wc_end+1.5+2*ODU_W+BOX_GAP, ODU_Z[0], ODU_Z[1], ODU_D, "UNIT 3 HEAT PUMP OUTDOOR UNIT, ON A WALL BRACKET"),
]
METERS = {"meter": 1}
POSITIONS = {"EM-1": 1, "EM-2": 2}          # meters drawn in each


def on(building, wall):
    return [b for b in EQUIPMENT if b.building == building and b.wall == wall]


def wall_length(building):
    return B1M.B1_D if building == 1 else B2M.B2_D


def openings(building, wall):
    """(along0, along1, z0, z1, mark) of every window in a side wall, all levels."""
    W = B1M.B1_W if building == 1 else B2M.B2_W
    if building == 1:
        levs = [(lv, m['plan'], m['wins']) for lv, m in B1M.LEVEL.items()]
    else:
        levs = [(lv, B2M.PLAN_B2, B2M.b2_wins(lv)) for lv in (1, 2)]
    out = []
    for lv, P, wins in levs:
        ff = {1: levels.FF1, 2: levels.FF2}[lv]
        for w in wins:
            if w[3] == 'v' and (w[0] > W-1.0 if wall == "NORTH" else w[0] < 1.0):
                y = P.y(w[1]); sill, h = WIN_GEOM[w[4]]
                out.append((y, y+w[2], ff+sill, ff+sill+h, "W-"+w[4]))
    return out


def dryer_bays(building, wall):
    """Lengths of wall a dryer cap may stand on. Building 1's is on its rear wall."""
    return [B2M.B2_DR_BAY] if (building, wall) == (2, "NORTH") else []


def leaders_on(building, wall):
    from src import grading as G
    x0, y0, W = (G.B1X0, G.B1Y0, B1M.B1_W) if building == 1 else (G.B2X0, G.B2Y0, B2M.B2_W)
    side = x0 if wall == "NORTH" else x0+W
    return [(ld.mark, ld.y-y0) for ld in G.LEADERS if ld.eave.startswith("BUILDING %d" % building) and abs(ld.x-side) < 1e-6]


def service_violations(equipment=None, leaders=None):
    eq = EQUIPMENT if equipment is None else equipment
    v = []
    for b in eq:
        same = [o for o in eq if o is not b and o.building == b.building and o.wall == b.wall]
        run = RUNS.get((b.building, b.wall))
        if run and not (run[0]-1e-9 <= b.along0 and b.along1 <= run[1]+1e-9):
            v.append("%s: off the wall behind the dining area (%s to %s along the north wall)" % (b.mark, fmt(run[0]), fmt(run[1])))
        if not (0.0 <= b.along0 and b.along1 <= wall_length(b.building)):
            v.append("%s: runs off the wall" % b.mark)
        if b.z0 < levels.GRADE+GRADE_CLR-1e-9:
            v.append("%s: under %s above finished grade" % (b.mark, fmt(GRADE_CLR)))
        if b.kind == "meter":
            zc = (b.z0+b.z1)/2.0
            if not (METER_Z[0]-1e-9 <= zc <= METER_Z[1]+1e-9):
                v.append("%s: its center is %s above grade, outside %s to %s" % (b.mark, fmt(zc), fmt(METER_Z[0]), fmt(METER_Z[1])))
            if SIDE_YARD < WORK_D-1e-9:
                v.append("%s: the side yard is under the %s working space of NEC 110.26(A)" % (b.mark, fmt(WORK_D)))
            c = (b.along0+b.along1)/2.0
            half = max(WORK_W, b.along1-b.along0)/2.0
            for o in same:
                if o.depth > b.depth+1e-9 and o.along0 < c+half-1e-9 and c-half < o.along1-1e-9:
                    v.append("%s: %s stands in its working space" % (b.mark, o.mark))
        for o in same:
            if o.mark > b.mark and b.along0 < o.along1+BOX_GAP-1e-9 and o.along0 < b.along1+BOX_GAP-1e-9:
                v.append("%s and %s: under %s apart" % (b.mark, o.mark, fmt(BOX_GAP)))
        for a0, a1, z0, z1, mk in openings(b.building, b.wall):
            if b.along0 < a1-1e-9 and a0 < b.along1-1e-9 and b.z0 < z1-1e-9 and z0 < b.z1-1e-9:
                v.append("%s: covers %s" % (b.mark, mk))
            if b.kind == "odu" and mk == "W-A" and b.along0 < a1+ODU_EGRESS_CLR-1e-9 and a0-ODU_EGRESS_CLR < b.along1-1e-9:
                v.append("%s: within %s of a W-A, the bedroom's escape opening" % (b.mark, fmt(ODU_EGRESS_CLR)))
        for a0, a1 in dryer_bays(b.building, b.wall):
            clr = ODU_DRYER_CLR if b.kind == "odu" else CAP_CLR
            if b.along0 < a1+clr-1e-9 and a0-clr < b.along1-1e-9:
                v.append("%s: within %s of the dryer cap's bay" % (b.mark, fmt(clr)))
        for mk, y in (leaders_on(b.building, b.wall) if leaders is None else leaders):
            if b.along0-LEADER_CLR < y < b.along1+LEADER_CLR:
                v.append("%s: within %s of leader %s" % (b.mark, fmt(LEADER_CLR), mk))
    return v


def check_services():
    for b in EQUIPMENT:
        print("SERVICE %-5s BUILDING %d %s WALL, %s to %s along it, +%s to +%s — %s"
              % (b.mark, b.building, b.wall, fmt(b.along0), fmt(b.along1), fmt(b.z0), fmt(b.z1), b.name))
    bad = service_violations()
    assert not bad, "service equipment: %s" % "; ".join(bad)
    from src.electrical import SERVICES
    for s in SERVICES:
        mine = [b for b in EQUIPMENT if b.kind == "meter" and b.building == s['building']]
        assert [b.mark for b in mine] == [s['mark']], "Building %d's meter is not %s" % (s['building'], s['mark'])
        assert POSITIONS[s['mark']] == len(s['positions']), "%s draws %d meters for %d positions" % (s['mark'], POSITIONS[s['mark']], len(s['positions']))
    units = sum(1 for b in EQUIPMENT if b.kind == "odu")
    assert units == sum(len(s['positions']) for s in SERVICES), "one outdoor unit per dwelling: %d" % units

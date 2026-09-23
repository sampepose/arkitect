"""The drainage model: what P-101 draws — every drain below either slab, every hole
through it and the feet of the six stacks — checked before anything draws.

P-601 says which fixture is on which stack and C-101 where the one 4" building sewer
goes. Between the foot of a stack and the wall there was nothing: no drawing located
a drain penetration in either slab. This module holds that — in PAGE FEET (Sage on
the left, S Elm or the courtyard at the top, y down), the system src/plumbing.py
authors the water in — and the sheet draws it.

The fixtures are src/plumbing.py's, the rectangles the floor plans and the water
supply plans draw, so a tub that moves on A-101 moves here and a closet flange that
no longer sits inside its water closet fails the build. The stacks, the penetrations
and the runs are AUTHORED here; check_drainage() verifies them against the fixtures,
S-101's strips, the slab edge, the water below the slab and the code tables, then
derives every figure the sheet and C-101 print: the fixture units, each pipe's load,
the inverts, the sewer's fall and the invert the alley main must be at or below.

Code basis is the Ohio Plumbing Code 2024 (the 2021 IPC with Ohio amendments), as
P-102 / P-103 cite it: Table 709.1 for drainage fixture units and trap sizes, 704.1
for slope, Table 710.1(1) for the building drains and their branches, Table 710.1(2)
for the stacks, 708.1 for cleanouts. Water closets are taken at 1.6 gpf or less.

Nothing here draws.
"""
import math
from lib.model import fit
from lib.units import IN, fmt, inches
from src import criteria as crit
from src import levels
from src import plumbing as pm
from lib.model import water as water
from src.building1 import BX0, EXT_STUD, PLAN_L1, U23_E_RISER, WET, WW0, site_x
from src.foundation import (B1 as FDN_B1, B2 as FDN_B2, BAR_COVER, FROST_DEPTH, FTG_BAR_DIA, FTG_T,
                            GRAVEL_T, INSUL_T, SLAB_T, WALL_T)
from src.mirror import B1_W
from src.sitework import ALLEY_W, SAN_CROSS, SAN_X, SITE_BLDG, SITE_D
from lib.model.runs import (grow as _grow, in_rect as _inside, length as _len, on_path as _on_path,
                            rects_overlap as _overlap, parallel as _parallel, points as _points,
                            pt_rect_dist as _pt_rect_dist, pt_seg_dist as _pt_seg_dist, same_point as _same,
                            seg_rect_dist as _seg_rect_dist)

# the tables: shared, see codes/ohio/opc_drainage.py
from codes.ohio.opc_drainage import (DRAIN_KINDS, SIZES, SIZE_IN, SLOPES, T710_1_1, T710_1_2, WC_MIN,
                                     WC_PER_INTERVAL_3, WC_PER_STACK_3)
from lib.model.drains import (Building, Pen, Run, Stack, _cy, _need, _strip_rect, _to_site, drain_name,
                              exit_pen, exit_run, exit_site, feeds, fixture, receiver, run_kinds)
from codes.ohio.opc_drainage import slope_of, fall, tail_invert, invert_at, exit_invert
from codes.ohio.opc_drainage import interval_dfu, run_dfu, stack_dfu
from codes.ohio.opc_drainage import DFU
from codes.ohio import opc_vents
from codes.ohio.opc_service_entry import bury_depth, entries_violations, entry_for
from collections import namedtuple


# ================================ the assumptions ================================
# The highest pipe below either slab has this much cover over its TOP; every invert
# follows from it, the drawn lengths and the slopes. Prints on the sheet with the rule
# that the alley main's invert governs and everything deepens together if it is lower.
# Held to FINISHED GRADE, not to the slab: the highest pipe's crown is 6-1/4" below grade,
# where it was when the slab stood +5-3/4" with 12" of cover. The floor rose to +8-1/4"
# (the designer, 2026-09-18) and the drains did not rise with it -- the building sewer outside is
# already shallow (C-103 note 6) -- so the cover under the slab is what grew, to 14-1/4".
CROWN_BELOW_GRADE = IN(6.25)
COVER = levels.SLAB_TOP-levels.GRADE+CROWN_BELOW_GRADE
SEWER_SLOPE = 1/8.0               # the building sewer, C-101 note 4b, inches per foot
STRIP_CLEAR = IN(6)               # pipe edge to the edge of a thickened strip, and to the slab edge
WATER_CLEAR = 1.0                 # centreline to centreline, a drain parallel to water below the slab
DROP_CLEAR = IN(6)                # a penetration to any water line below the slab
EDGE_IN = 1.0                     # a penetration is at least this far inside an outside face

# ================================ the types ================================


# ================================ geometry ================================
TOL = 1e-6


# ================================ the fixtures ================================
def _pm(b):
    return pm.BUILDINGS[b.number-1]


# ================================ fixture units ================================


def unit_names(b):
    return water.unit_names(_pm(b))


def building_dfu(b):
    return sum(unit_dfu(_pm(b), n)[0] for n in unit_names(b))


def total_dfu():
    return sum(building_dfu(b) for b in BUILDINGS)


# ================================ the network ================================


# Inverts: codes/ohio/opc_drainage.py, from the COVER this project states.


def below_grade(v):
    """A depth below slab top as a depth below finished grade (both negative)."""
    return v+levels.SLAB_TOP


def water_below(b):
    """The water piping below the slab, from src/plumbing.py: the service and every
       trunk flagged under, as segments."""
    pb = _pm(b)
    segs = [(pb.entry, pb.riser)]
    for _names, path, under in pb.trunks:
        if under: segs += list(zip(path, path[1:]))
    return segs


def strips(b):
    return [(_strip_rect(s), s[4]) for s in (FDN_B1 if b.number == 1 else FDN_B2).strips]


# ================================ Building 1 ================================
# Page feet: Sage x 0, S Elm y 0, the rear wall y 48, W4 at Y_SEP_TOP. Unit 1 in
# front of W4, Units 2 and 3 behind it. The one exit is through the rear wall, where
# C-101 starts the building sewer.
_B1 = pm.BUILDING_1
U1_KS, U1_WC, U1_TUB, U1_WD = (_need(_B1, 'UNIT 1', 1, k) for k in ('sink', 'wc', 'tub', 'wd'))
U2_KS, U2_WC, U2_TUB = (_need(_B1, 'UNIT 2', 1, k) for k in ('sink', 'wc', 'tub'))

# The trunk runs under Unit 1's mechanical strip: the one north-south line clear of the
# stair-wall strip (x 3'-5" to 4'-9"), the wet wall, the Units 2/3 bearing strip and
# the Units 2/3 water trunk down the Sage side at x 1'-4".
TRUNK_X = 6.0
B1_EXIT = (TRUNK_X, 48.0)
# Unit 1. The 2x6 wet wall's centre, 91" from the Sage stud face — stack B rises
# in it at the tub, P-601 note 1a. The closet flange is 12" off the finished wall; the
# tub drains 4" from its wet-wall end into a box-out that abuts the stack's foot.
U1_WET_X = site_x(WW0+WET/2.0)
B_POS = (U1_WET_X, _cy(U1_TUB))
WC1 = (site_x(BX0)+1.0, _cy(U1_WC))
TUB1 = (U1_TUB.x+IN(4), _cy(U1_TUB))
# The kitchen sink drops in its cabinet at the parcel wall; vent A rises in that wall.
# 7-3/4" off the stud face, not the 6" the cabinet would suggest: the side wall is a 2x6
# now, so 6" off the studs is only 11-1/2" inside the outside face and EDGE_IN wants a
# foot. At 7-3/4" the drop is 1'-1-1/4" in — exactly where it sat under the old 2x8, so
# the slab layout below did not move when the wall thinned.
KS1 = (U1_KS.x+U1_KS.w-IN(7.75), _cy(U1_KS))
# Vent A rises in that wall to the attic, and Unit 1's W-B (Level 1) and W-A (Level 2) both stand
# over the sink: behind the sink the vent would pass through two windows. It stands just past
# their rear jamb instead, a trap arm's reach from the sink (stack_violations(), found 2026-09-18
# by the check 400 Oak's Stack E taught).
from src.building1 import windows as _u1_windows
from codes.ohio.opc_drainage import unit_dfu
from codes.ohio.opc_separation import (Ground, SEWER_SEP, highest_top_near, site_crossings, sleeves,
                                       water_crossings)
_A_WINS = [w for lv in (1, 2) for w in _u1_windows(lv) if w[3] == 'v' and w[0] > B1_W/2.0 and w[1] <= KS1[1] <= w[1]+w[2]]
STACK_CLEAR = IN(3)                # a stack off a window's or door's jamb, for the casing
A_Y = max(w[1]+w[2] for w in _A_WINS)+STACK_CLEAR+IN(2) if _A_WINS else KS1[1]
A_POS = (B1_W-EXT_STUD/2.0, A_Y)
# the laundry standpipe against the stair-side partition of the nook under the landing;
# its dry vent rises in that wall to B, P-601 note 1b
CW1 = (U1_WD.x+U1_WD.w+IN(3), _cy(U1_WD))
CO1 = (TRUNK_X, WC1[1])
# Units 2 and 3. Stack C rises in the bath's Sage-side 2x4 wall, behind the water
# closet; the tub drains 4" from that end. Unit 2's sink drops in its cabinet 2'-0" off
# the Sage face, past the water trunk at 1'-4", and its branch shares the trunk
# junction with the bath collector. Stack E is in the rear wall where the roof model
# puts its vent; its foot offsets inboard past the foundation wall, and its branch runs
# a foot inboard of the water trunk along that wall.
C_POS = (U2_WC.x-IN(1.75), _cy(U2_WC))
WC2 = (U2_WC.x+1.0, _cy(U2_WC))
TUB2 = (U2_TUB.x+IN(4), _cy(U2_TUB))
KS2 = (2.0, WC2[1])
STACK_E_X = B1_W-PLAN_L1.x(U23_E_RISER, 47.5)
E_POS = (STACK_E_X, 48.0-EXT_STUD/2.0)
E_FOOT = (STACK_E_X, 46.4)
E_RUN_Y = 45.9

B1_STACKS = [
    Stack('A', A_POS, '2', (), None),                 # vent only: the sink drains below the slab at 1
    Stack('B', B_POS, '3', (('UNIT 1', 1, ('lav',)), ('UNIT 1', 2, ('lav', 'wc', 'tub'))), 4),
    Stack('C', C_POS, '3', (('UNIT 2', 1, ('lav',)), ('UNIT 3', 2, ('lav', 'wc', 'tub', 'sink'))), 10),
    Stack('E', E_POS, '2', (('UNIT 2', 1, ('wd',)), ('UNIT 3', 2, ('wd',))), 11),
]
B1_PENS = [
    Pen(1,  'drop',  KS1,     '2',     (('UNIT 1', 1, ('sink',)),), None),
    Pen(2,  'wc',    WC1,     '3',     (('UNIT 1', 1, ('wc',)),),   None),
    Pen(3,  'tub',   TUB1,    '1-1/2', (('UNIT 1', 1, ('tub',)),),  (TUB1[0]-IN(4), TUB1[1]-0.5, 1.0, 1.0)),
    Pen(4,  'stack', B_POS,   '3',     'B', None),
    Pen(5,  'drop',  CW1,     '2',     (('UNIT 1', 1, ('wd',)),),   None),
    Pen(6,  'co',    CO1,     '4',     (), None),
    Pen(7,  'drop',  KS2,     '2',     (('UNIT 2', 1, ('sink',)),), None),
    # the box-out starts STRIP_CLEAR past the W4 strip's rear edge, which moves with the wall
    Pen(8,  'tub',   TUB2,    '1-1/2', (('UNIT 2', 1, ('tub',)),),
        (TUB2[0]-IN(4), [s for s in FDN_B1.strips if s[4] == 'W4'][0][3]+STRIP_CLEAR, 1.0, 1.0)),
    Pen(9,  'wc',    WC2,     '3',     (('UNIT 2', 1, ('wc',)),),   None),
    Pen(10, 'stack', C_POS,   '3',     'C', None),
    Pen(11, 'stack', E_FOOT,  '2',     'E', None),
    Pen(12, 'exit',  B1_EXIT, '4',     (), None),
]
B1_RUNS = [
    Run('2', [KS1, (KS1[0], WC1[1]), WC1]),           # the kitchen, south along the parcel wall then west
    Run('3', [WC1, CO1]),                              # the water closet and the kitchen into the trunk
    Run('3', [TUB1, B_POS, (TRUNK_X, B_POS[1])]),      # the tub trap and stack B's foot
    Run('2', [CW1, (TRUNK_X, CW1[1])]),                # the laundry standpipe
    Run('4', [CO1, B1_EXIT]),                          # the trunk, below W4's strip, to the exit
    Run('3', [WC2, C_POS, (TRUNK_X, WC2[1])]),         # Unit 2's water closet and stack C's foot
    Run('2', [TUB2, (TUB2[0], WC2[1])]),               # Unit 2's tub trap arm to that collector
    Run('2', [KS2, (TRUNK_X, KS2[1])]),                # Unit 2's kitchen sink, from the Sage side
    Run('2', [E_FOOT, (E_FOOT[0], E_RUN_Y), (TRUNK_X, E_RUN_Y)]),   # stack E's foot
]
BUILDING_1 = Building('BUILDING 1', 1, 26.0, 48.0, B1_STACKS, B1_PENS, B1_RUNS, SITE_BLDG[0][:2])

# ================================ Building 2 ================================
# Page feet: Sage x 0, the courtyard y 0, the bearing wall at y 15. The bath is in
# the column between the bedrooms with its fixtures on the parcel-side wall, stack D in
# that wall with a closet behind it. The mechanical closet is in the Sage corner
# with stack F in the Sage wall behind the washer. The exit is through the Sage
# wall behind the bearing wall, where C-101's lateral leaves.
_B2 = pm.BUILDING_2
U4_LAV, U4_WC, U4_TUB, U4_KS, U4_WD = (_need(_B2, 'UNIT 4', 1, k) for k in ('lav', 'wc', 'tub', 'sink', 'wd'))
D_WALL_X = U4_WC.x+U4_WC.w                         # the stack wall's bath face
D_POS = (D_WALL_X+IN(1.75), _cy(U4_WC))
WC4 = (D_WALL_X-1.0, _cy(U4_WC))
TUB4 = (U4_TUB.x+U4_TUB.w-IN(4), _cy(U4_TUB))
COLL_X = TUB4[0]                                  # the collector, 4" inside the stack wall
B2_DRAIN_Y = 17.0                                 # behind the bearing wall, its strip 8" clear
CO4 = (COLL_X, B2_DRAIN_Y)
B2_EXIT = (0.0, B2_DRAIN_Y)
F_POS = (EXT_STUD/2.0, _cy(U4_WD))
F_FOOT = (1.5, _cy(U4_WD))

B2_STACKS = [
    Stack('D', D_POS, '3', (('UNIT 4', 1, ('lav',)), ('UNIT 5', 2, ('lav', 'wc', 'tub'))), 3),
    Stack('F', F_POS, '3', (('UNIT 4', 1, ('sink', 'wd')), ('UNIT 5', 2, ('sink', 'wd'))), 5),
]
B2_PENS = [
    Pen(1, 'tub',   TUB4,    '1-1/2', (('UNIT 4', 1, ('tub',)),), (D_WALL_X-1.0, TUB4[1]-0.5, 1.0, 1.0)),
    Pen(2, 'wc',    WC4,     '3',     (('UNIT 4', 1, ('wc',)),),  None),
    Pen(3, 'stack', D_POS,   '3',     'D', None),
    Pen(4, 'co',    CO4,     '4',     (), None),
    Pen(5, 'stack', F_FOOT,  '3',     'F', None),
    Pen(6, 'exit',  B2_EXIT, '4',     (), None),
]
B2_RUNS = [
    Run('3', [TUB4, CO4]),                             # the collector under the bath, tub to the cleanout
    Run('3', [WC4, (COLL_X, WC4[1])]),                 # the closet bend
    Run('3', [D_POS, (COLL_X, D_POS[1])]),             # stack D's foot
    Run('4', [CO4, B2_EXIT]),                          # the building drain behind the bearing wall
    Run('3', [F_FOOT, (F_FOOT[0], B2_DRAIN_Y)]),       # stack F's foot, below the bearing strip
]
BUILDING_2 = Building('BUILDING 2', 2, 26.0, 28.0, B2_STACKS, B2_PENS, B2_RUNS, SITE_BLDG[1][:2])

BUILDINGS = [BUILDING_1, BUILDING_2]


# ================================ the sewer ================================


def sewer():
    """C-101's route from the Building 1 exit to the alley: its on-lot length, the
       length to a main taken at the alley's centerline, the fall at SEWER_SLOPE, the
       invert where Building 2's lateral joins and the invert the main must be at or
       below — all below finished grade, in feet, negative down."""
    b1, b2 = BUILDINGS
    x1, y1 = exit_site(b1); x2, y2 = exit_site(b2)
    route = [(x1, y1), (x1, SAN_CROSS), (SAN_X, SAN_CROSS), (SAN_X, SITE_D)]
    lateral = [(x2, y2), (SAN_X, y2)]
    on_lot = _len(route)
    to_main = on_lot+ALLEY_W/2.0
    inv1 = below_grade(exit_invert(b1, cover=COVER)); inv2 = below_grade(exit_invert(b2, cover=COVER))
    to_junction = (SAN_CROSS-y1)+(x1-SAN_X)+(y2-SAN_CROSS)
    junction = inv1-SEWER_SLOPE/12.0*to_junction
    lateral_needs = junction+SEWER_SLOPE/12.0*_len(lateral)
    return dict(route=route, lateral=lateral, on_lot=on_lot, to_main=to_main,
                fall=SEWER_SLOPE/12.0*to_main, exit1=inv1, exit2=inv2, junction=junction,
                lateral_needs=lateral_needs, lateral_fall=inv2-junction,
                main_max=inv1-SEWER_SLOPE/12.0*to_main)


FOOTING_TOP = -(FROST_DEPTH-FTG_T)                 # below finished grade, feet


# ================================ water and drain crossings ================================
# OPC 603.2 as Ohio replaces it, OAC 4101:3-6-01(C): where a water service crosses a
# sewer it is sleeved to a point 5'-0" horizontally from the sewer's centreline on both
# sides, or its bottom, within 5'-0" of the sewer, is 12" above the highest point of the
# sewer's top. The set holds every crossing of water and drain to one of the two, below
# the slab as on the lot; P-101 note 9 and P-102 / P-103 note 2 print it.
# Water that passes above a drain lies in A-601 S1's gravel under the slab: its bottom,
# sleeve and all, is no deeper than this below slab top.
WATER_BED = SLAB_T+GRAVEL_T


def water_lines(b):
    """The water that is in the ground, as (name, polyline) in plan feet: the service from
       the main, MAIN_TO_WALL out and square to its wall, to its riser; then each trunk
       below the slab, riser to riser."""
    pb = _pm(b)
    assert abs(pb.entry[1]-pb.riser[1]) < TOL, '%s: the service is not square to its wall' % b.name
    out = [('SERVICE', [(-pm.MAIN_TO_WALL, pb.entry[1]), pb.riser])]
    for names, path, under in pb.trunks:
        if under:
            who = names[0] if len(names) == 1 else 'UNITS '+' AND '.join(n.split()[-1] for n in names)
            out.append(('%s TRUNK' % who, list(path)))
    return out


def _sewers():
    """C-101's building sewer and Building 2's lateral in site feet: (name, path, invert
       below grade at a distance along it, size)."""
    s = sewer(); b1, b2 = BUILDINGS
    L = _len(s['lateral'])
    return [('BUILDING SEWER', s['route'], lambda t: s['exit1']-SEWER_SLOPE/12.0*t, exit_run(b1).size),
            ('BUILDING 2 LATERAL', s['lateral'], lambda t: s['exit2']-(s['exit2']-s['junction'])*t/L, exit_run(b2).size)]


# What OPC 603.2 is checked against here: codes/ohio/opc_separation.py reads nothing else.
GROUND = Ground(cover=COVER, wall_t=WALL_T, water_bed=WATER_BED, frost_depth=FROST_DEPTH,
                water_below=water_below, water_lines=water_lines, strips=strips, sewers=_sewers,
                service_size=lambda b: pm.sizes(_pm(b))['service'],
                ftg_t=FTG_T, bar_dia=FTG_BAR_DIA, bar_cover=BAR_COVER, slab_top=levels.SLAB_TOP,
                bury=bury_depth(FROST_DEPTH), service_series='CTS')


def service_sleeve(b):
    """The service's sleeve as (feet out from the wall's outside face, feet in from it), or None."""
    sp = [(lo, hi) for nm, lo, hi in sleeves(b, GROUND) if nm == 'SERVICE']
    if not sp: return None
    assert len(sp) == 1, '%s: the service has more than one sleeve' % b.name
    return (pm.MAIN_TO_WALL-sp[0][0], sp[0][1]-pm.MAIN_TO_WALL)


def service_to_sewer(b):
    """The nearest the service comes to the building sewer or the lateral between the main
       and the wall, feet."""
    line = water_lines(b)[0][1]
    wall = [(p[0], p[1]) for p in _points([line[0], (0.0, line[0][1])])]
    return min(_pt_seg_dist(_to_site(b, q), a, bb) for q in wall for _nm, path, _i, _s in _sewers()
               for a, bb in zip(path, path[1:]))


# ================================ the checker ================================
def stack_violations():
    """A stack rises through every level, so it may not stand at a wall where ANY level has an
       opening. lib/model/fit.py measures; src/mechanical.py has the walls' openings."""
    from src import mechanical as M
    v = []
    for b in BUILDINGS:
        for s in b.stacks:
            for wall in M.WALLS[b.number].values():
                off = abs((s.pos[0] if wall.orient == 'v' else s.pos[1])-wall.at)
                if off > 1.5: continue                     # not at this wall
                along = s.pos[1] if wall.orient == 'v' else s.pos[0]
                for op in fit.rises_at_opening(along, wall.openings, STACK_CLEAR):
                    v.append('%s: stack %s stands at the %s where %s is' % (b.name, s.name, wall.name.lower(), op.name))
    return v


DUCT_CLEAR = IN(6)                 # a standpipe or laundry stack off the dryer duct's centerline, along their wall


def laundry_violations():
    """The washer's drain and the dryer's duct share a wall behind the stacked pair: M-101 / M-102
       place the duct's cap, and a laundry stack or standpipe at that wall keeps DUCT_CLEAR from it."""
    from src import mechanical as M
    v = []
    for b in BUILDINGS:
        mine = [(s.name, s.pos) for s in b.stacks if any('wd' in ks for _u, _l, ks in s.serves)]
        mine += [('penetration %d' % p.mark, p.pos) for p in b.pens if p.kind == 'drop' and any('wd' in ks for _u, _l, ks in p.serves)]
        for wall_name, terms in M.TERMS[b.number].items():
            if wall_name == 'ROOF': continue
            wall = M.WALLS[b.number][wall_name]
            for t in terms:
                if t.what != 'DRYER EXHAUST': continue
                for nm, pos in mine:
                    if abs((pos[0] if wall.orient == 'v' else pos[1])-wall.at) > 3.0: continue    # not at this wall
                    gap = fit.along_wall_gap(pos[1] if wall.orient == 'v' else pos[0], t.along)
                    if gap < DUCT_CLEAR-TOL:
                        v.append('%s: %s stands %s from dryer duct %s along the %s, under %s' % (b.name, nm, inches(gap), t.mark, wall_name.lower(), inches(DUCT_CLEAR)))
    return v


def drainage_violations():
    v = stack_violations()+laundry_violations()+vent_violations()
    for b in BUILDINGS:
        pb = _pm(b)
        who = b.name
        slab = (WALL_T+INSUL_T, WALL_T+INSUL_T, b.W-2*(WALL_T+INSUL_T), b.D-2*(WALL_T+INSUL_T))
        inner = (EDGE_IN, EDGE_IN, b.W-2*EDGE_IN, b.D-2*EDGE_IN)
        strs = strips(b)
        water = water_below(b)
        ex = exit_pen(b)
        if ex is None:
            v.append('%s: not exactly one exit' % who); continue
        on_face = abs(ex.pos[0]) < TOL or abs(ex.pos[0]-b.W) < TOL or abs(ex.pos[1]) < TOL or abs(ex.pos[1]-b.D) < TOL
        if not on_face: v.append('%s: the exit is not on an outside face' % who)
        # ---- every fixture served once ----
        served = {}
        for s in b.stacks:
            for unit, level, kinds in s.serves:
                for k in kinds: served[(unit, level, k)] = served.get((unit, level, k), 0)+1
        for p in b.pens:
            if p.kind in ('drop', 'wc', 'tub'):
                for unit, level, kinds in p.serves:
                    for k in kinds: served[(unit, level, k)] = served.get((unit, level, k), 0)+1
        have = {}
        for u in pb.units:
            for f in u.fixtures:
                if f.kind in DRAIN_KINDS: have[(u.name, u.level, f.kind)] = have.get((u.name, u.level, f.kind), 0)+1
        for key in sorted(set(have)|set(served)):
            if have.get(key, 0) != served.get(key, 0):
                v.append('%s: %s level %d has %d %s fixture(s) but %d served' % (who, key[0], key[1], have.get(key, 0), key[2], served.get(key, 0)))
        # ---- stacks ----
        for s in b.stacks:
            if s.size not in SIZES: v.append('%s: stack %s size %r' % (who, s.name, s.size)); continue
            if s.foot is None:
                if s.serves: v.append('%s: stack %s serves fixtures but has no foot' % (who, s.name))
                continue
            feet = [p for p in b.pens if p.mark == s.foot]
            if len(feet) != 1 or feet[0].kind != 'stack' or feet[0].serves != s.name:
                v.append('%s: stack %s foot is not penetration %r' % (who, s.name, s.foot)); continue
            if math.hypot(feet[0].pos[0]-s.pos[0], feet[0].pos[1]-s.pos[1]) > 2.0:
                v.append('%s: stack %s foot is over 2\'-0" from the stack' % (who, s.name))
            if feet[0].size != s.size:
                v.append('%s: stack %s is %s" but its foot %s"' % (who, s.name, s.size, feet[0].size))
            if len(s.serves) > 3:
                v.append('%s: stack %s has more than three branch intervals' % (who, s.name))
            per, tot = T710_1_2[s.size][1], T710_1_2[s.size][2]
            for unit, level, kinds in s.serves:
                d = interval_dfu(kinds)
                if d > per: v.append('%s: stack %s %s level %d puts %d DFU into one branch interval, Table 710.1(2) allows %d' % (who, s.name, unit, level, d, per))
                if 'wc' in kinds and SIZES.index(s.size) < SIZES.index(WC_MIN):
                    v.append('%s: stack %s carries a water closet at %s"' % (who, s.name, s.size))
                if 'wc' in kinds and s.size == '3' and kinds.count('wc') > WC_PER_INTERVAL_3:
                    v.append('%s: stack %s has over %d water closets in one interval' % (who, s.name, WC_PER_INTERVAL_3))
            if stack_dfu(s) > tot: v.append('%s: stack %s carries %d DFU, Table 710.1(2) allows %d' % (who, s.name, stack_dfu(s), tot))
            if s.size == '3' and sum(kinds.count('wc') for _u, _l, kinds in s.serves) > WC_PER_STACK_3:
                v.append('%s: stack %s has over %d water closets' % (who, s.name, WC_PER_STACK_3))
        for p in b.pens:
            if p.kind == 'stack' and not any(s.foot == p.mark for s in b.stacks):
                v.append('%s: penetration %d is a stack foot no stack claims' % (who, p.mark))
        # ---- penetrations ----
        marks = [p.mark for p in b.pens]
        if len(set(marks)) != len(marks): v.append('%s: penetration marks repeat' % who)
        for p in b.pens:
            if p.kind == 'exit': continue
            if not _inside(p.pos, inner):
                v.append('%s: penetration %d at (%.2f, %.2f) is under %s of an outside face' % (who, p.mark, p.pos[0], p.pos[1], fmt(EDGE_IN)))
            half = IN(SIZE_IN[p.size])/2.0
            for rect, nm in strs:
                if _pt_rect_dist(p.pos, rect) < STRIP_CLEAR+half-TOL:
                    v.append('%s: penetration %d is within %s of the %s strip' % (who, p.mark, inches(STRIP_CLEAR), nm))
            if p.box is not None:
                if not _inside(p.pos, p.box): v.append('%s: penetration %d is outside its box-out' % (who, p.mark))
                if not _inside(p.box[:2], slab) or not _inside((p.box[0]+p.box[2], p.box[1]+p.box[3]), slab):
                    v.append('%s: penetration %d box-out leaves the slab' % (who, p.mark))
                for rect, nm in strs:
                    if _overlap(_grow(p.box, STRIP_CLEAR), rect):
                        v.append('%s: penetration %d box-out is within %s of the %s strip' % (who, p.mark, inches(STRIP_CLEAR), nm))
            if p.kind in ('drop', 'wc', 'tub'):
                for unit, level, kinds in p.serves:
                    for k in kinds:
                        f = fixture(pb, unit, level, k)
                        if f is None: v.append('%s: penetration %d serves a %s %s has not got' % (who, p.mark, k, unit)); continue
                        if not _inside(p.pos, _grow((f.x, f.y, f.w, f.h), 1.0 if p.kind == 'drop' else 0.25)):
                            v.append('%s: penetration %d is not at the %s %s it serves' % (who, p.mark, unit, k))
                if p.kind == 'wc' and SIZES.index(p.size) < SIZES.index(WC_MIN):
                    v.append('%s: penetration %d is a water closet at %s"' % (who, p.mark, p.size))
                if p.kind == 'tub' and p.box is None: v.append('%s: penetration %d is a tub trap with no box-out' % (who, p.mark))
                for c, d in water:
                    if _pt_seg_dist(p.pos, c, d) < DROP_CLEAR-TOL:
                        v.append('%s: penetration %d is within %s of the water below the slab' % (who, p.mark, inches(DROP_CLEAR)))
            loads = [r for r in b.runs if _on_path(p.pos, r.path) and not _same(p.pos, r.path[-1])]
            if len(loads) != 1:
                v.append('%s: penetration %d is on %d run(s)' % (who, p.mark, len(loads)))
        # ---- runs ----
        for i, r in enumerate(b.runs):
            tag = '%s run %d (%s")' % (who, i+1, r.size)
            if r.size not in SIZES: v.append('%s: size %r' % (tag, r.size)); continue
            if len(r.path) < 2: v.append('%s: has no length' % tag); continue
            for a, bb in zip(r.path, r.path[1:]):
                if abs(a[0]-bb[0]) > TOL and abs(a[1]-bb[1]) > TOL: v.append('%s: a segment is not axis-aligned' % tag)
                if _same(a, bb): v.append('%s: a zero-length segment' % tag)
                half = IN(SIZE_IN[r.size])/2.0
                for rect, nm in strs:
                    ain, bin_ = _inside(a, rect), _inside(bb, rect)
                    if ain or bin_:
                        v.append('%s: ends in the %s strip' % (tag, nm)); continue
                    if _seg_rect_dist(a, bb, rect) < TOL:
                        horiz_strip = rect[2] >= rect[3]
                        if horiz_strip != (abs(a[0]-bb[0]) < TOL):
                            v.append('%s: crosses the %s strip along it, not at a right angle' % (tag, nm))
                    elif _seg_rect_dist(a, bb, rect) < STRIP_CLEAR+half-TOL:
                        v.append('%s: runs within %s of the %s strip' % (tag, inches(STRIP_CLEAR), nm))
                for c, d in water:
                    par, dist = _parallel(a, bb, c, d)
                    if par and dist < WATER_CLEAR-TOL:
                        v.append('%s: runs parallel to the water below the slab within %s' % (tag, fmt(WATER_CLEAR)))
            rec = receiver(b, r)
            if rec is None: v.append('%s: its tail is on no run and not at the exit' % tag)
            elif rec == 'ambiguous': v.append('%s: its tail is on more than one run' % tag)
            elif rec != 'exit' and SIZES.index(rec.size) < SIZES.index(r.size):
                v.append('%s: drains into a smaller %s" run' % (tag, rec.size))
            load = run_dfu(b, r)
            col = SLOPES.index(slope_of(r))
            cap = T710_1_1[r.size][col]
            if cap is None: v.append('%s: Table 710.1(1) has no value at 1/%d" per foot' % (tag, round(1/slope_of(r))))
            elif load > cap: v.append('%s: carries %d DFU, Table 710.1(1) allows %d' % (tag, load, cap))
            if 'wc' in run_kinds(b, r) and SIZES.index(r.size) < SIZES.index(WC_MIN):
                v.append('%s: carries a water closet' % tag)
            # every branch enters from above
            for f in feeds(b, r):
                if not _same(f.path[-1], r.path[0]):
                    if tail_invert(b, f, cover=COVER) < invert_at(b, r, f.path[-1], cover=COVER)-TOL:
                        v.append('%s: a %s" branch enters it below its invert' % (tag, f.size))
        xr = exit_run(b)
        if xr is None: v.append('%s: not exactly one run ends at the exit' % who)
        else:
            if run_dfu(b, xr) != building_dfu(b):
                v.append('%s: the building drain carries %d DFU, the fixture tally is %d' % (who, run_dfu(b, xr), building_dfu(b)))
            if xr.size != max(b.runs, key=lambda r: SIZES.index(r.size)).size:
                v.append('%s: the exit run is not the largest' % who)
            if below_grade(tail_invert(b, xr, cover=COVER)) < FOOTING_TOP+IN(1):
                v.append('%s: the exit invert is below the footing top; sleeve through the wall is not possible' % who)
    s = sewer()
    if s['exit2'] < s['lateral_needs']-TOL:
        v.append('BUILDING 2: its exit is below the sewer where the lateral joins it')
    # ---- water and drain crossings, OPC 603.2 ----
    for b in BUILDINGS:
        lines = dict(water_lines(b))
        spans = sleeves(b, GROUND)
        for nm, lo, hi in spans:
            if lo < -TOL: v.append('%s: the %s sleeve reaches the main' % (b.name, nm.lower()))
        # between the main and the wall the service keeps SEWER_SEP from the sewer and
        # the lateral, or is in its sleeve
        line = lines['SERVICE']
        cover = [(lo, hi) for nm, lo, hi in spans if nm == 'SERVICE']
        for q in _points([line[0], (0.0, line[0][1])]):
            t = q[0]-line[0][0]
            near = [nm for nm, path, _i, _s in _sewers()
                    if min(_pt_seg_dist(_to_site(b, q), a, bb) for a, bb in zip(path, path[1:])) < SEWER_SEP-TOL]
            if near and not any(lo-TOL <= t <= hi+TOL for lo, hi in cover):
                v.append('%s: the service is within %s of the %s outside the wall, unsleeved' % (b.name, fmt(SEWER_SEP), near[0].lower()))
                break
    return v


def check_drainage():
    """From build.check_model(): every fixture drained, every pipe sized and every
       invert derived, or the build stops with the building and the rule named."""
    v = drainage_violations()
    assert not v, 'DRAINAGE: %d violation(s):\n  ' % len(v)+'\n  '.join(v)
    v = entries_violations(BUILDINGS, GROUND)
    assert not v, 'SERVICE ENTRY: %d violation(s):\n  ' % len(v)+'\n  '.join(v)
    for b in BUILDINGS:
        for s in b.stacks:
            print('DRAINAGE %s stack %s %s" at (%.2f, %.2f): %s' % (b.name, s.name, s.size, s.pos[0], s.pos[1],
                  'vent only' if s.foot is None else '%d DFU, foot at %d' % (stack_dfu(s), s.foot)))
        for i, r in enumerate(b.runs):
            print('DRAINAGE %s run %d: %s" at 1/%d" per foot, %s long, %d DFU, falls %s' % (
                b.name, i+1, r.size, round(1/slope_of(r)), fmt(_len(r.path)), run_dfu(b, r), inches(fall(r))))
        print('DRAINAGE %s: %d DFU by unit, %d on the drain; exit invert %s below slab top, %s below grade' % (
            b.name, building_dfu(b), run_dfu(b, exit_run(b)), inches(-exit_invert(b, cover=COVER)), inches(-below_grade(exit_invert(b, cover=COVER)))))
    s = sewer()
    print('DRAINAGE sewer: %s on the lot, %s to the main, %s of fall; main invert at or below %s below grade; %d DFU in all' % (
        fmt(s['on_lot']), fmt(s['to_main']), inches(s['fall']), inches(-s['main_max']), total_dfu()))
    for b in BUILDINGS:
        for r, nm, x, kind in water_crossings(b, GROUND):
            print('DRAINAGE %s: the %s crosses the %s" %s at (%s, %s), %s' % (
                b.name, nm.lower(), r.size, drain_name(b, r).lower(), fmt(x[0]), fmt(x[1]),
                'above it, %s over its top within %s' % (inches(-highest_top_near(b, r, x, GROUND)-WATER_BED), fmt(SEWER_SEP))
                if kind == 'above' else 'below it, sleeved'))
        for nm, x, top, kind in site_crossings(b, GROUND):
            print('DRAINAGE %s: the service crosses the %s on the lot at (%s, %s), its top %s below grade; %s' % (
                b.name, nm.lower(), fmt(x[0]), fmt(x[1]), inches(-top),
                'the service above it' if kind == 'above' else 'the service below frost, sleeved'))
        ss = service_sleeve(b)
        print('DRAINAGE %s: the service %s' % (b.name, 'keeps %s from the sewer outside the wall' % fmt(service_to_sewer(b))
              if ss is None else 'is sleeved from %s outside the wall to %s inside it' % (fmt(ss[0]), fmt(ss[1]))))
    for b in BUILDINGS:
        e = entry_for(b, GROUND)
        print('DRAINAGE %s: the %s" service enters through the footing, top %s below grade (%s under the %s '
              'frost line), in a %s" sleeve %s outside; the footing is thickened to %s there, its bottom %s '
              'lower, and returns over %s each side' % (
                  b.name, e.service, inches(e.bury), inches(e.bury-e.frost), inches(e.frost), e.sleeve,
                  inches(e.sleeve_od), inches(e.thick), inches(e.drop), fmt(e.run)))


# ================================ venting, OPC Chapter 9 ================================
# A stack that carries the level above is not a vent for the level below: 912 wet vents two
# bathroom groups on ONE floor level, and 913's waste stack vent -- the arrangement that does
# serve several floors -- takes no water closet. B, C and D each carry one. So every Level 1
# fixture on them keeps its own DRY vent, up its group's wet wall and into that stack's vent
# above everything on the stack, at 905.4's 6" over the highest flood rim.
#
# Two of these were already right and are only written down here: V-A, the kitchen sink's
# vent stack, and V-L, the laundry's dry vent in the stair wall -- P-601 notes 1e and 1b have
# had both joining stack B in the attic from the start.
#
# E and F carry no water closet, so they ARE 913 waste stack vents, and P-601 now says so:
# no offset between their lowest and highest fixture connection, and the load inside Table
# 913.4. `vent_violations()` holds all of it.
DryVent = namedtuple('DryVent', 'mark building at size serves ties_into at_fixture')

V_B1 = (B_POS[0], 15.6)            # U1 Level 1 bath, in the 2x6 wet wall at the lavatory
V_C1 = (C_POS[0], 30.4)            # Units 2/3 bath, the same wall, at Unit 2's lavatory
V_K2 = (0.4, 29.0)                 # Unit 2's kitchen sink, in the wall it drops at
V_D1 = (D_POS[0], 22.0)            # Unit 4's bath, between its lavatory and its tub
V_L1 = (4.08, 20.45)               # the laundry, in the stair wall: P-601 note 1b

DRY_VENTS = [
    DryVent('V-A', 1, A_POS, '2', (('UNIT 1', 1, ('sink',)),),              'B', 'sink'),
    DryVent('V-L', 1, V_L1,  '2', (('UNIT 1', 1, ('wd',)),),                'B', 'wd'),
    DryVent('V-B', 1, V_B1,  '2', (('UNIT 1', 1, ('lav', 'wc', 'tub')),),   'B', 'lav'),
    DryVent('V-C', 1, V_C1,  '2', (('UNIT 2', 1, ('lav', 'wc', 'tub')),),   'C', 'lav'),
    DryVent('V-K', 1, V_K2,  '2', (('UNIT 2', 1, ('sink',)),),              'C', 'sink'),
    DryVent('V-D', 2, V_D1,  '2', (('UNIT 4', 1, ('lav', 'wc', 'tub')),),   'D', 'lav'),
]

WASTE_STACKS = ('E', 'F')          # 913: no water closet on either, and no offset drawn
TRAP_SIZE = {'wc': 3.0, 'tub': 1.5, 'shower': 2.0, 'lav': 1.5, 'sink': 2.0, 'wd': 2.0}
_OD = {'1-1/2': IN(1.9), '2': IN(2.375), '3': IN(3.5), '4': IN(4.5)}      # DWV, ASTM D2665
# Each tie stands 4'-0" over the Level 2 floor: clear of every rim on these stacks by more
# than 905.4's 6", the highest being a kitchen sink's 3'-0" on stack C. Typed, not derived,
# so that raising a fixture or lowering a tie is caught rather than followed.
TIE_Z = {m: levels.FLOOR_RISE+IN(48) for m in ('V-A', 'V-L', 'V-B', 'V-C', 'V-K', 'V-D')}


def _fixture_at(b, unit, level, kind):
    """Where a fixture's trap stands: its slab penetration, or the fixture itself where it
       drains into a stack above the floor."""
    for pen in b.pens:
        if pen.kind in ('stack', 'exit', 'co'):
            continue
        for u, l, ks in pen.serves:
            if (u, l) == (unit, level) and kind in ks:
                return pen.pos
    f = _need(_B1 if b.number == 1 else _B2, unit, level, kind)
    return (f.x+f.w/2.0, f.y+f.h/2.0) if f is not None else None


def trap_arms():
    """[(building, Arm)] -- every fixture a dry vent serves, its trap size and the developed
       length to that riser. The branch turns square, so it is measured that way."""
    out = []
    for b in BUILDINGS:
        for dv in DRY_VENTS:
            if dv.building != b.number:
                continue
            for unit, level, kinds in dv.serves:
                for k in kinds:
                    at = _fixture_at(b, unit, level, k)
                    if at is None:
                        continue
                    run = abs(at[0]-dv.at[0])+abs(at[1]-dv.at[1])
                    out.append((b, opc_vents.Arm('%s %s %s' % (b.name, unit, k.upper()),
                                                 TRAP_SIZE[k], run)))
    return out


def vent_ties():
    """Each dry vent's tie: (mark, its height, the highest flood rim it must clear), from
       Level 1's finished floor."""
    out = []
    for dv in DRY_VENTS:
        b = next(x for x in BUILDINGS if x.number == dv.building)
        stack = next(st for st in b.stacks if st.name == dv.ties_into)
        rims = [levels.FLOOR_RISE*(l-1)+opc_vents.FLOOD_RIM[k] for _u, l, ks in stack.serves for k in ks]
        rims += [levels.FLOOR_RISE*(l-1)+opc_vents.FLOOD_RIM[k] for _u, l, ks in dv.serves for k in ks]
        out.append((dv.mark, TIE_Z[dv.mark], max(rims)))
    return out


def waste_stacks():
    """E and F as 913 reads them: their load by branch interval and in all."""
    out = []
    for b in BUILDINGS:
        for st in b.stacks:
            if st.name not in WASTE_STACKS:
                continue
            by = [sum(DFU[k] for k in ks) for _u, _l, ks in st.serves]
            wc = any(k == 'wc' for _u, _l, ks in st.serves for k in ks)
            out.append((st.name, float(st.size), wc, by, stack_dfu(st), False))
    return out


# Stack A is a vent that joins stack B in the attic, P-601 note 1e, so it never reaches a
# roof: one roof penetration per stack, less this one. P-601's riser diagram reads it too,
# Stack A is a vent that joins stack B in the attic, P-601 note 1e, so it never reaches a
# roof: one roof penetration per stack, less this one. P-601's riser diagram reads it too,
# rather than typing 'VENT TO B' beside a pipe the model thought went outside.
ATTIC_TIES = {'A': 'B'}


def vent_violations():
    """Every venting rule: what may vent what (912 / 913), the trap arms of Table 909.1,
       905.4's rise, and 903.2's size at the roof. A fixture on a stack that drains the
       level above keeps its own dry vent."""
    v = opc_vents.roof_vent_violations(
        opc_vents.roof_vents(BUILDINGS, ATTIC_TIES, crit.WINTER_DESIGN_LO), crit.WINTER_DESIGN_LO)
    for b in BUILDINGS:
        served = {(u, l, k) for dv in DRY_VENTS if dv.building == b.number
                  for u, l, ks in dv.serves for k in ks}
        slab = [(u, l, k) for p in b.pens if p.kind in ('drop', 'wc', 'tub')
                for u, l, ks in p.serves for k in ks]
        missing = [f for f in slab if f not in served]
        if missing:
            v.append('%s: nothing vents %s, which drains below the slab' % (b.name, missing))
        for dv in DRY_VENTS:
            if dv.building == b.number and dv.ties_into not in [st.name for st in b.stacks]:
                v.append('%s: vent %s ties into stack %s, which it has not got' % (b.name, dv.mark, dv.ties_into))
        for st in b.stacks:
            drains = [('%s %s' % (u, k.upper()), l) for u, l, ks in st.serves for k in ks]
            wc = any(k == 'wc' for _u, _l, ks in st.serves for k in ks)
            # nothing is stack-vented here: every Level 1 fixture has a dry vent, and E
            # and F answer to 913 below instead
            v += opc_vents.stack_vent_violations([(st.name, wc, drains, [])])
    v += opc_vents.trap_arm_violations([a for _b, a in trap_arms()])
    v += opc_vents.dry_vent_rise_violations(vent_ties())
    v += opc_vents.waste_stack_violations(waste_stacks())
    for dv in DRY_VENTS:                          # the riser stands clear of the stack it joins
        b = next(x for x in BUILDINGS if x.number == dv.building)
        st = next(x for x in b.stacks if x.name == dv.ties_into)
        gap = math.hypot(dv.at[0]-st.pos[0], dv.at[1]-st.pos[1])
        need = (_OD[dv.size]+_OD[st.size])/2.0
        if gap < need-1e-9:
            v.append('%s: vent %s stands %s from stack %s, inside the two pipes\' %s'
                     % (b.name, dv.mark, fmt(gap), st.name, fmt(need)))
    return v

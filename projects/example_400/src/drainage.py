"""The drainage model: what P-101 draws — every drain below either slab, every hole
through it and the feet of the stacks — checked before anything draws.

In PAGE FEET (396 Oak, north, at x 0; the front face at y 0; y toward the alley), the
system src/plumbing.py authors the water in. The water comes down the NORTH side yard and
the sewer goes out down the SOUTH one, so each building has ONE exit, through its south
wall, and the two never share a trench (OPC 603.2).

The fixtures are src/plumbing.py's, the rectangles the floor plans and the water
supply plans draw, so a tub that moves on A-101 moves here and a closet flange that
no longer sits inside its water closet fails the build. The stacks, the penetrations
and the runs are AUTHORED here; check_drainage() verifies them against the fixtures,
S-101's strips, the slab edge, the water below the slab and the code tables, then
derives every figure the sheet and C-101 print: the fixture units, each pipe's load,
the inverts, the sewer's fall and the invert the Oak Avenue main must be at or below.

Code basis is the Ohio Plumbing Code 2024 (the 2021 IPC with Ohio amendments), as
P-102 / P-103 cite it: Table 709.1 for drainage fixture units and trap sizes, 704.1
for slope, Table 710.1(1) for the building drains and their branches, Table 710.1(2)
for the stacks, 708.1 for cleanouts. Water closets are taken at 1.6 gpf or less.

Nothing here draws.
"""
import math
from collections import namedtuple
from arkitect.codes.ohio import opc_vents
from arkitect.lib.model import fit
from arkitect.lib.model import pipe
from arkitect.lib.units import IN, fmt, inches
from src import envelope
from arkitect.codes.ohio.columbus import criteria as crit
from src import levels
from src import building2 as B2M
from src import plumbing as pm
from arkitect.lib.model import water as water
from src.building1 import LEVEL as _B1_LEVEL, STACK_A_CHASE, X_HALL0 as _X_HALL0
from src.foundation import (B1 as FDN_B1, B2 as FDN_B2, BAR_COVER, FROST_DEPTH, FTG_BAR_DIA, FTG_T,
                            GRAVEL_T, INSUL_T, SLAB_T, WALL_T)
from src.sitework import B1_X, B1_Y, B2_X, B2_Y, SIDE_YARD, SITE_W
from arkitect.lib.model.runs import (along as _along, grow as _grow, in_rect as _inside, length as _len, on_path as
                            _on_path, rects_overlap as _overlap, parallel as _parallel, points as _points,
                            pt_rect_dist as _pt_rect_dist, pt_seg_dist as _pt_seg_dist, same_point as _same,
                            seg_rect_dist as _seg_rect_dist)

# the tables: shared, see arkitect/codes/ohio/opc_drainage.py
from arkitect.codes.ohio.opc_drainage import (DFU, DRAIN_KINDS, SIZES, SIZE_IN, SLOPE, SLOPES, T710_1_1, T710_1_2, WC_MIN,
                                     WC_PER_INTERVAL_3, WC_PER_STACK_3)
from arkitect.lib.model.drains import (Building, Pen, Run, Stack, _cy, _need, _strip_rect, _to_site, drain_name,
                              exit_pen, exit_run, exit_site, feeds, fixture, receiver, run_kinds)
from arkitect.codes.ohio.opc_drainage import slope_of, fall, tail_invert, invert_at, exit_invert
from arkitect.codes.ohio.opc_drainage import interval_dfu, run_dfu, stack_dfu
from arkitect.codes.ohio.opc_service_entry import (bury_depth, entries_violations, entry_for, thickened_zone,
                                          zone_violations)
from arkitect.codes.ohio.opc_drainage import unit_dfu, washer_violations
from arkitect.codes.ohio.opc_separation import (Ground, SEWER_SEP, highest_top_near, site_crossings, sleeves,
                                       water_crossings)


# ================================ the assumptions ================================
# The highest pipe below either slab has this much cover over its TOP; every invert
# follows from it, the drawn lengths and the slopes. Prints on the sheet with the rule
# that the Oak Avenue main's invert governs and everything deepens together if it is lower.
# 20": as deep as the exits can go and still pass through the foundation wall above its
# footing. The lot falls about 14" to Oak Avenue (C-103), and the sewer has to stay under it.
COVER = IN(20)
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


# Inverts: arkitect/codes/ohio/opc_drainage.py, from the COVER this project states.


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
# Page feet: 396 Oak x 0, the front face y 0, the rear wall y B1_D. Bath 1 and the
# laundry are along the rear; the kitchen sink is on the south wall and Bath 2 is over
# it. One trunk gathers the rear, runs forward under the pantry and the kitchen's
# cabinets a foot and a half inside the south wall, takes the sink and stack A's foot,
# and leaves through the south wall under the solid length between its windows.
_B1 = pm.BUILDING_1
B1_W, B1_D = _B1.W, _B1.D
_B1_PLAN = _B1_LEVEL[1]['plan']
U1_KS, U1_WC, U1_SH, U1_LAV, U1_WD = (_need(_B1, 'UNIT 1', 1, k) for k in ('sink', 'wc', 'shower', 'lav', 'wd'))
TRUNK_X = B1_W-IN(17)                               # inside the south wall, under the cabinets
COLL_Y = U1_SH.y+U1_SH.h/2.0                        # the rear collector, through the shower's drain
SH1 = (U1_SH.x+U1_SH.w/2.0, COLL_Y)
LAV1 = (U1_LAV.x+U1_LAV.w/2.0, U1_LAV.y+1.0)
WC1 = (U1_WC.x+U1_WC.w/2.0, U1_WC.y+U1_WC.h-IN(14))   # the closet flange, 12" off the finished rear wall
CW1 = (U1_WD.x+IN(5), U1_WD.y+U1_WD.h-IN(9))        # the standpipe at the rear wall, at the bay's north end: the dryer's duct is at its middle
KS1 = (TRUNK_X, _cy(U1_KS))
# Stack A: Bath 2's, in the furred chase A-101 draws at the front end of the kitchen run
# (building1.STACK_A_CHASE); its foot is on the trunk. Stack B is Bath 1's and the laundry's vent, in the bath's hall-side wall.
_CHASE = water._mirror(_B1_PLAN.rect(STACK_A_CHASE), B1_W)       # A-101's chase, in page feet
A_Y = _CHASE[1]+_CHASE[3]/2.0
A_POS = (_CHASE[0]+_CHASE[2]/2.0, A_Y)             # in the chase, inside the wall's insulation
A_FOOT = (TRUNK_X, A_Y)
B_POS = (LAV1[0]+IN(15), U1_LAV.y+IN(2))   # in Bath 1's front partition beside the lavatory:
                                           # 909.1 measures the lavatory's trap arm to here, and
                                           # its drain wet-vents the closet and the shower, 912
X_MECH_P = B1_W-_X_HALL0                    # the mech room's hall partition, in these page feet
B1_TURN = (TRUNK_X, A_Y-IN(10))
B1_EXIT = (B1_W, B1_TURN[1])

B1_STACKS = [
    Stack('A', A_POS, '3', (('UNIT 1', 2, ('lav', 'lav', 'wc', 'tub')),), 5),
    Stack('B', B_POS, '2', (), None),                 # vent only: Bath 1 and the laundry drain below the slab
]
B1_PENS = [
    Pen(1, 'drop',  LAV1,    '2',     (('UNIT 1', 1, ('lav',)),),    None),
    Pen(2, 'tub',   SH1,     '2',     (('UNIT 1', 1, ('shower',)),), (SH1[0]-0.5, SH1[1]-0.5, 1.0, 1.0)),
    Pen(3, 'wc',    WC1,     '3',     (('UNIT 1', 1, ('wc',)),),     None),
    Pen(4, 'drop',  CW1,     '2',     (('UNIT 1', 1, ('wd',)),),     None),
    Pen(5, 'stack', A_FOOT,  '3',     'A', None),
    Pen(6, 'drop',  KS1,     '2',     (('UNIT 1', 1, ('sink',)),),   None),
    Pen(7, 'exit',  B1_EXIT, '4',     (), None),
]
_B1_HEAD = (WC1[0], COLL_Y)
B1_RUNS = [
    Run('2', [LAV1, (LAV1[0], COLL_Y), _B1_HEAD]),    # the lavatory, then the shower's trap, to the collector's head
    Run('3', [WC1, _B1_HEAD]),                        # the closet bend
    Run('3', [_B1_HEAD, (TRUNK_X, COLL_Y), B1_TURN]), # the collector along the rear, then the trunk forward
    Run('2', [CW1, (CW1[0], COLL_Y)]),                # the laundry standpipe
    Run('4', [B1_TURN, B1_EXIT]),                     # the building drain through the south wall
]
BUILDING_1 = Building('BUILDING 1', 1, B1_W, B1_D, B1_STACKS, B1_PENS, B1_RUNS, (B1_X, B1_Y))

# ================================ Building 2 ================================
# Page feet: 396 Oak x 0, the courtyard face y 0, the bearing wall's strip across the
# building. The bath is against the south wall behind the bearing wall, stack D in its rear
# wall behind the water closet. The kitchen sink and the washer are on the NORTH wall, one
# either side of the bearing wall, and Unit 3's stand over them: stacks E and F, in that
# wall, feet inboard. The sink's branch passes below the strip at a right angle; one
# collector crosses the building behind the strip to the exit in the south wall.
_B2 = pm.BUILDING_2
B2_W, B2_D = _B2.W, _B2.D
U2_WC, U2_TUB, U2_KS, U2_WD, U2_LAV = (_need(_B2, 'UNIT 2', 1, k) for k in ('wc', 'tub', 'sink', 'wd', 'lav'))
_STRIP_Y1 = FDN_B2.strips[0][3]
B2_DRAIN_Y = pm.U23_RISER[1]-IN(13)                 # the collector: 13" ahead of the water below the slab
_E_CHASE = water._mirror(B2M.PLAN_B2.rect(B2M.STACK_E_CHASE), B2_W)    # A-102's chase, past the kitchen window
E_POS = (_E_CHASE[0]+_E_CHASE[2]/2.0, _E_CHASE[1]+_E_CHASE[3]/2.0)
E_FOOT = (1.5, E_POS[1])
# F is behind the washer at its REAR end: the dryer's duct climbs the same wall at the bay's middle.
# It is 3" because it takes the washers (OPC 406.2), and it stands in the north wall's stud
# cavity with the cavity insulation between it and the sheathing (OPC 305.4) -- the one drain
# in an exterior wall, P-601 notes 1aa and 2. That bay is framed DEEPER, because a 2x6 cavity
# does not hold the insulation and a FITTING: envelope.STACK_BAY_STUD.
F_SIZE = '3'
# Set by the bay, not by the stud face: the fill goes against the sheathing and the widest
# FITTING sits in front of it, so the stack's centreline is one fill plus half a hub in from
# the exterior stud face. Held to the stud face instead, a hub stood 1/2" proud of the framing
# and left the fill 1/2" short, and nothing said so -- the check measured the straight pipe.
F_POS = (envelope.STACK_BAY_FILL+pipe.fitting_od(F_SIZE)/2.0, U2_WD.y+U2_WD.h-IN(5))
F_FOOT = (E_FOOT[0]+IN(5), F_POS[1])
D_POS = (U2_WC.x+U2_WC.w/2.0, U2_WC.y+U2_WC.h+IN(2))   # in the bath's rear wall
WC2 = (D_POS[0], D_POS[1]-IN(15))
TUB2 = (U2_TUB.x+U2_TUB.w/2.0, WC2[1])
# Unit 2's bath is a 912.1 HORIZONTAL WET VENT below the slab, so its lavatory drops
# through the slab at the lavatory and its drain from there carries the rest of the group:
# the closet bend first, the tub -- the most downstream fixture -- last, because the tub's
# waste stands at the tub's own centre, past the closet. V-D takes off at the lavatory,
# the head of the branch, with nothing upstream of it (912.2.1). Stack D carries Unit 3
# only and discharges into the building drain DOWNSTREAM of the whole group, 912.1.
LAV2 = (U2_LAV.x+U2_LAV.w/2.0, U2_LAV.y+U2_LAV.h-IN(6))    # under the lavatory, off the wall behind it
WET_Y = WC2[1]                                             # the branch, on the closet flange's line
B2_TURN = (B2_W-IN(17), B2_DRAIN_Y)
B2_EXIT = (B2_W, B2_DRAIN_Y)
D_FOOT_X = B2_W-IN(12)                                     # stack D comes east of the tub's trap box-out

B2_STACKS = [
    Stack('D', D_POS, '3', (('UNIT 3', 2, ('lav', 'wc', 'tub')),), 4),
    Stack('E', E_POS, '2', (('UNIT 2', 1, ('sink',)), ('UNIT 3', 2, ('sink',))), 5),
    Stack('F', F_POS, F_SIZE, (('UNIT 2', 1, ('wd',)), ('UNIT 3', 2, ('wd',))), 6),
]
B2_PENS = [
    Pen(1, 'drop',  LAV2,    '2',     (('UNIT 2', 1, ('lav',)),), None),
    Pen(2, 'wc',    WC2,     '3',     (('UNIT 2', 1, ('wc',)),),  None),
    Pen(3, 'tub',   TUB2,    '1-1/2', (('UNIT 2', 1, ('tub',)),), (TUB2[0]-0.5, TUB2[1]-0.5, 1.0, 1.0)),
    Pen(4, 'stack', D_POS,   '3',     'D', None),
    Pen(5, 'stack', E_FOOT,  '2',     'E', None),
    Pen(6, 'stack', F_FOOT,  '3',     'F', None),
    Pen(7, 'exit',  B2_EXIT, '4',     (), None),
]
B2_RUNS = [
    Run('2', [E_FOOT, (E_FOOT[0], B2_DRAIN_Y)]),      # stack E's foot, below the bearing strip, to the collector's head
    Run('3', [(E_FOOT[0], B2_DRAIN_Y), B2_TURN]),     # the collector across the building
    Run('3', [F_FOOT, (F_FOOT[0], B2_DRAIN_Y)]),      # stack F's foot, 3" because it takes the washers (OPC 406.2)
    Run('2', [LAV2, (LAV2[0], WET_Y), WC2]),          # the lavatory's drain: the head of the wet vent
    Run('3', [WC2, TUB2, (TUB2[0], B2_DRAIN_Y)]),     # the closet bend, then the tub, then the collector
    Run('3', [D_POS, (D_FOOT_X, D_POS[1]), (D_FOOT_X, B2_DRAIN_Y)]),   # stack D, into the drain past the group
    Run('4', [B2_TURN, B2_EXIT]),                     # the building drain through the south wall
]
BUILDING_2 = Building('BUILDING 2', 2, B2_W, B2_D, B2_STACKS, B2_PENS, B2_RUNS, (B2_X, B2_Y))

BUILDINGS = [BUILDING_1, BUILDING_2]

# ---------------- the dry vents, OPC 905.4 / 909.1 / 912 / 913 ----------------
# A fixture on Level 1 cannot be vented by a stack that drains Level 2 into it: 912's wet
# venting is two bathroom groups on ONE floor, and 913's waste stack vent -- the arrangement
# that does serve several floors -- takes no water closet, which both A and D carry. So each
# Level 1 group keeps its OWN dry vent, up beside its stack in the same chase or wall, tying
# into that stack's vent above every fixture on it: 905.4's 6" over the highest flood rim.
# Stack B was always this and stays; V-A and V-D are the two the riser used to leave out.
#
# A vent stands clear of its stack by both pipes' radii, and inside the chase or the wall
# that carries it -- `vent_violations()` measures all of it.
# `at_fixture` is the fixture the dry vent stands at -- a lavatory or a sink, never a water
# closet: its trap arm measures to the riser, and its drain from there is the group's wet
# vent (912, one floor). Every other fixture of the group measures its own branch to where
# that branch meets the wet vent.
DryVent = namedtuple('DryVent', 'mark building at size serves ties_into at_fixture')
V_A_POS = (A_POS[0]+IN(2.1), A_POS[1]+IN(2.1))       # the far corner of stack A's 8" chase
V_C_POS = (X_MECH_P, CW1[1])                         # the laundry's own vent, in the hall partition
V_D_POS = (U2_LAV.x+U2_LAV.w+IN(1.5), D_POS[1])      # the bath's rear wall, beside the lavatory it stands at

# ---------------- Bath 2: a horizontal wet vent IN THE LEVEL 2 FLOOR ----------------
# Stack A rises in the Level 1 kitchen chase to a point under Bath 2's TUB, and the two
# lavatories stand 6'-8" and 9'-8" from it along the hall wall -- past Table 909.1's
# 6'-0" for a 1-1/2" trap -- so the stack cannot be their vertical wet vent: nothing
# vertical stands at them. The group drains the way P-601 note 1a routes it, through the
# floor trusses' open webs: ONE branch on the closet flange's line from the far lavatory,
# past the near lavatory, the closet and the tub, to stack A's top. That is 912.1's
# HORIZONTAL wet vent, and V-E, in the hall partition behind the far lavatory, is its
# dry vent (912.2.1: nothing upstream of it). P-102 draws it enlarged.
_BATH2 = [f for u in _B1.units if (u.name, u.level) == ('UNIT 1', 2) for f in u.fixtures]
_LAVS2 = sorted((f for f in _BATH2 if f.kind == 'lav'), key=lambda f: abs(f.x+f.w/2.0-A_POS[0]), reverse=True)
_WC2, _TUB2 = (next(f for f in _BATH2 if f.kind == k) for k in ('wc', 'tub'))
BATH2_WALL_Y = max(f.y+f.h for f in _LAVS2+[_WC2])          # the hall partition's bath face, stud
BATH2_BR_Y = BATH2_WALL_Y-IN(12.5)                           # the closet flange: 12" off the finished wall
V_E_POS = (_LAVS2[0].x+_LAVS2[0].w/2.0, BATH2_WALL_Y+IN(1.75))   # in the partition, behind the far lavatory
V_F_POS = (_LAVS2[1].x+_LAVS2[1].w/2.0, BATH2_WALL_Y+IN(1.75))   # and behind the near one, the same partition
_TUB2_DRAIN = (_TUB2.x+_TUB2.w/2.0, BATH2_BR_Y)              # at the tub's valve end, which is this wall's
# The branch in the direction of flow, and each fixture's connection on it, with the size
# of the section DOWNSTREAM of that connection: the far lavatory's drain drops in the wall
# under V-E and turns into the floor; 2" to the closet, 3" from it (709.1).
BATH2_BRANCH = [V_E_POS, (V_E_POS[0], BATH2_BR_Y), _TUB2_DRAIN, (A_POS[0], BATH2_BR_Y), A_POS]
BATH2_CONNS = [('lav', V_E_POS, '2'),
               ('lav', (_LAVS2[1].x+_LAVS2[1].w/2.0, BATH2_BR_Y), '2'),
               ('wc',  (_WC2.x+_WC2.w/2.0, BATH2_BR_Y), '3'),
               ('tub', _TUB2_DRAIN, '3')]
FLOOR_BRANCHES = {'A': ('V-E', 'UNIT 1', 2)}               # stack -> the dry vent of the group draining to its top
TRUSS_CHORD = IN(1.5)                                      # a 4x2 floor truss's chord, top and bottom, S-102
BRANCH_TOP = TRUSS_CHORD                                   # the head's crown under the top chord, in the webs

# BOTH lavatory traps stand 18" over the Level 2 floor and the branch runs INSIDE that floor,
# so neither trap can be vented by the branch: OPC 909.2 keeps a vent connection within the
# drain's own diameter of the weir, and a drop through a floor is two feet of it. The branch
# is still the wet vent of the closet (excepted by the section) and the tub (its trap hangs in
# the webs and is set to the branch), but each lavatory takes a dry vent in the partition
# BEHIND IT, above its weir and before its drop -- V-E at the far one, V-F at the near one.
# `weir_violations()` is the rule; keyed by each fixture's index in BATH2_CONNS.
BATH2_VENTS = {0: 'V-E', 1: 'V-F'}
FLOOR_VENTS = tuple(BATH2_VENTS.values())                  # drawn with the branch, not on a riser


# Stack F is the one drain standing in an exterior wall's stud cavity. The inset is DERIVED
# from where the stack stands, so moving it, or making it bigger, moves what is left behind
# it -- and `cavity_violations()` says whether what A-601 fills that wall with still fits.
CAVITY_STACKS = ('F',)


def cavity_runs():
    """Every drain standing in an exterior wall's stud cavity, as arkitect/lib/model/fit.py sees it:
       the pipe's OUTSIDE diameter (a "3 inch" stack is 3-1/2" across), the cavity's depth,
       how far the pipe stands off the cavity's interior face, and what the bay is filled
       with behind it. A-601 draws the section and prints the fill beside its wall rows."""
    out = []
    for b in BUILDINGS:
        for st in b.stacks:
            if st.name not in CAVITY_STACKS:
                continue
            out.append(fit.InCavity('STACK %s' % st.name, pipe.od(st.size, 'IPS'),
                                    pipe.fitting_od(st.size), envelope.STUD_CAVITY,
                                    fit.lumber_depth(envelope.STACK_BAY_STUD)-envelope.STUD_CAVITY,
                                    envelope.STACK_BAY_FILL, envelope.STACK_BAY_MATERIAL))
    return out


def cavity_violations():
    return fit.cavity_violations(cavity_runs())


def web_clear():
    """The clear depth between a floor truss's chords: the truss less BOTH chords, which is
       what a pipe in the webs has to fit inside. A-601's F1 section draws it. Not to be
       confused with the gate below, which is a depth under the SUBFLOOR: the subfloor and
       the top chord stand above the webs, so the two figures differ by both of them."""
    return levels.F2_JOIST-2*TRUSS_CHORD


def _branch_along(pt):
    """Feet along BATH2_BRANCH, in the direction of flow, to a point on it."""
    t = 0.0
    for a, b in zip(BATH2_BRANCH, BATH2_BRANCH[1:]):
        if _on_path(pt, [a, b]):
            return t+abs(pt[0]-a[0])+abs(pt[1]-a[1])
        t += abs(b[0]-a[0])+abs(b[1]-a[1])
    raise ValueError('%r is not on the Bath 2 branch' % (pt,))


def floor_branch_sections():
    """[(size, length)] of the Bath 2 branch, head to stack: each section takes the size
       below the last connection upstream of it."""
    marks = [(_branch_along(p), size) for _k, p, size in BATH2_CONNS]
    total = _branch_along(BATH2_BRANCH[-1])
    out = [('2', marks[0][0])] if marks[0][0] > 0 else []
    for (a, size), nxt in zip(marks, marks[1:]+[(total, None)]):
        out.append((size, nxt[0]-a))
    return out


def floor_branch_crown(at):
    """How far under Level 2's SUBFLOOR the Bath 2 branch's crown lies, `at` feet along the
       branch in the direction of flow: the subfloor, BRANCH_TOP at the head, then the fall of
       each section at 704.1's slope. The crown does not step where the branch goes 2" to 3" --
       that step is taken crown to crown, which is why only the BOTTOM moves there."""
    d = levels.SUBFLOOR+BRANCH_TOP
    run = 0.0
    for size, length in floor_branch_sections():
        d += min(length, max(0.0, at-run))*SLOPE[size]/12.0
        run += length
        if run >= at-1e-9:
            break
    return d


def _bath2_legs():
    """Each Bath 2 fixture in the direction of flow: (index, kind, a name, its trap, the point
       its trap arm runs TO, the connection on the branch). The arm goes to the vent standing
       at that fixture where one does (BATH2_VENTS) and otherwise to the branch, which 912.1
       makes its vent. Each trap is taken at its fixture's middle, which overstates the arm."""
    fx = {'lav': list(_LAVS2), 'wc': [_WC2], 'tub': [_TUB2]}
    out = []
    for i, (k, at, _size) in enumerate(BATH2_CONNS):
        f = fx[k].pop(0)
        n = [c[0] for c in BATH2_CONNS[:i]].count(k)
        name = '%s%s' % (k.upper(), ' %d' % (n+1) if n else '')
        to = _vent_pos(BATH2_VENTS[i]) if i in BATH2_VENTS else at
        out.append((i, k, name, (f.x+f.w/2.0, f.y+f.h/2.0), to, at))
    return out


def _vent_pos(mark):
    return next(dv.at for dv in DRY_VENTS if dv.mark == mark)


def bath2_weirs():
    """Every Bath 2 fixture against OPC 909.2: its trap's weir and the height its vent
       connects at, both on Level 2's FINISHED floor, positive up.

       A lavatory's vent stands in the partition behind it, so its connection is under the weir
       only by the fall of its own trap arm -- which Table 909.1 already holds inside the
       drain's diameter. Every other fixture's vent is the branch itself (912.1), and the branch
       is in the floor: legal for the closet, which the section excepts, and for the tub, whose
       trap hangs in the webs and is set to the branch it drains to. Neither has a TRAP_WEIR
       entry, so `weir_violations()` says it skipped them rather than measuring a guess."""
    out = []
    for i, k, name, trap, to, at in _bath2_legs():
        size = TRAP_SIZE[k]
        weir = opc_vents.TRAP_WEIR.get(k)
        if i in BATH2_VENTS and weir is not None:
            arm = abs(trap[0]-to[0])+abs(trap[1]-to[1])
            vent_at = weir-arm*opc_vents.TRAP_ARM[size][0]/12.0
        else:
            vent_at = -(levels.FLOOR_FINISH+floor_branch_crown(_branch_along(at)))
        out.append(opc_vents.Weir('UNIT 1 L2 %s' % name, k, size,
                                  weir if weir is not None else 0.0, vent_at))
    return out


def floor_branch_bottom():
    """How far under Level 2's SUBFLOOR the Bath 2 branch's pipe bottom reaches at stack A:
       the subfloor, BRANCH_TOP, the head's pipe, the fall of each section at 704.1's slope,
       and the step from 2" to 3" taken crown to crown. The datum is the subfloor's top,
       which is the deck the pipe is roughed in from and FLOOR_FINISH under the finished
       floor; P-102 says SUBFLOOR for that reason."""
    d = levels.SUBFLOOR+BRANCH_TOP+_od('2')
    for size, length in floor_branch_sections():
        d += length*SLOPE[size]/12.0
    return d+(_od('3')-_od('2'))


DRY_VENTS = [
    DryVent('V-A', 1, V_A_POS, '2', (('UNIT 1', 1, ('sink',)),),                'A', 'sink'),
    DryVent('V-B', 1, B_POS,   '2', (('UNIT 1', 1, ('lav', 'wc', 'shower')),),  None, 'lav'),
    DryVent('V-C', 1, V_C_POS, '2', (('UNIT 1', 1, ('wd',)),),                  'B', 'wd'),
    DryVent('V-D', 2, V_D_POS, '2', (('UNIT 2', 1, ('lav', 'wc', 'tub')),),     'D', 'lav'),
    DryVent('V-E', 1, V_E_POS, '2', (('UNIT 1', 2, ('lav', 'lav', 'wc', 'tub')),), 'A', 'lav'),
    DryVent('V-F', 1, V_F_POS, '1-1/2', (('UNIT 1', 2, ('lav',)),), 'A', 'lav'),
]

# What each below-slab fixture's trap arm runs to its vent, and the trap that measures it:
# Table 909.1 is by TRAP size, which is the branch the fixture drops in.
TRAP_SIZE = {'wc': 3.0, 'tub': 1.5, 'shower': 2.0, 'lav': 1.5, 'sink': 2.0, 'wd': 2.0}

# ---------------- where each drain MEETS its stack, and what that makes the stack ----------------
# A riser diagram has to say where a fixture connects, not only that it does: OPC 912.1.1
# makes the stack itself the vent for the group hanging on it -- a VERTICAL WET VENT --
# only where the water closets connect lowest, every other fixture connects at or above
# them, each connection is independent, and the stack is carried full size above the
# highest of them as the dry vent (912.2.2). So the closet bend drops to the bottom of the
# floor its level stands on and the rest come in over it. Feet over that level's finished
# floor, + up; CONN_STEP keeps a second fixture of one kind off the first. Typed, because
# each is a decision a plumber builds to, and check_drainage() measures the result.
CONN_Z = {'wc': -IN(12), 'tub': -IN(6), 'shower': -IN(6), 'lav': IN(16), 'sink': IN(16), 'wd': IN(18)}
CONN_STEP = IN(4)
assert -CONN_Z['wc'] <= levels.F1_DEPTH-IN(1), 'the closet bend no longer fits the floor it drops through'

# Stacks E and F carry no water closet and serve both levels, so they are 913 WASTE STACK
# VENTS: the stack IS the vent for everything on it. 913.2 forbids any offset between the
# lowest and the highest fixture connection -- each of these two offsets to its foot at the
# slab, under every connection on it, which is where STACK_OFFSET_Z holds them.
WASTE_STACKS = ('E', 'F')
STACK_OFFSET_Z = 0.0


DUCT_CLEAR = IN(6)                 # a standpipe or laundry stack off the dryer duct's centerline, along their wall


def laundry_violations():
    """The washer's drain and the dryer's duct share a wall behind the stacked pair: M-101 /
       M-102 place the duct, and the standpipe or its stack keeps DUCT_CLEAR along the wall."""
    from src import mechanical as M
    v = []
    for b, along in ((BUILDING_1, 0), (BUILDING_2, 1)):
        ducts = [t for ts in M.TERMS[b.number].values() for t in ts if t.what == 'DRYER EXHAUST']
        mine = [p.pos for p in b.pens if p.kind == 'drop' and any('wd' in ks for _u, _l, ks in p.serves)]
        mine += [s.pos for s in b.stacks if any('wd' in ks for _u, _l, ks in s.serves)]
        for pos in mine:
            for t in ducts:
                if fit.along_wall_gap(pos[along], t.along) < DUCT_CLEAR-TOL:
                    v.append('%s: the washer drain stands %s from dryer duct %s along their wall, under %s' % (b.name, inches(abs(pos[along]-t.along)), t.mark, inches(DUCT_CLEAR)))
    return v


STACK_CLEAR = IN(3)                # a stack off a window's or door's jamb, for the casing


def stack_violations():
    """A stack rises through every level, so it may not stand at a wall where ANY level has an
       opening: Building 2's Stack E was drawn behind the sinks, under the kitchen windows of both
       units, for a day."""
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


_OD = {'1-1/2': IN(1.9), '2': IN(2.375), '3': IN(3.5), '4': IN(4.5)}      # DWV, ASTM D2665


def _od(size):
    return _OD[size]


# Where each dry vent ties into its stack's vent, from Level 1's finished floor: clear of
# every fixture on the stack by 905.4's 6", which puts it in the Level 2 wall.
TIE_Z = {'V-A': levels.FLOOR_RISE+IN(37),   # over Bath 2's lavatory rim, in the Level 2 wall
         'V-C': IN(48),                     # over the standpipe's own rim, in the Level 1 wall
         'V-D': levels.FLOOR_RISE+IN(37),   # over Unit 3's lavatory rim
         'V-E': levels.ROOF_PLATE-levels.FF1+IN(12),   # in the attic, where stack A's vent comes up
         'V-F': levels.ROOF_PLATE-levels.FF1+IN(12)}   # beside it: the near lavatory's own vent


def _fixture_at(b, unit, level, kind):
    """Where a below-slab fixture's trap drops through the slab, from the penetrations."""
    for pen in b.pens:
        if pen.kind in ('stack', 'exit'):
            continue
        for u, l, ks in pen.serves:
            if (u, l) == (unit, level) and kind in ks:
                return pen.pos
    f = _need(_B1 if b.number == 1 else _B2, unit, level, kind)      # on a stack, not the slab
    return (f.x+f.w/2.0, f.y+f.h/2.0) if f is not None else None


def trap_arm_rows():
    """[(building, the vent's mark, Arm)] -- every below-slab fixture, its trap size and the
       developed length from that trap to its vent: to the riser for the fixture the vent
       stands at, and for the rest of the group the branch that carries them to that
       fixture's drain, which is the wet vent (912). The mark ties each row of P-601's
       schedule to the riser the arm is drawn on."""
    out = []
    for b in BUILDINGS:
        for dv in DRY_VENTS:
            if dv.building != b.number:
                continue
            if dv.mark in FLOOR_VENTS:
                # the branch's head vent brings the WHOLE group's arms, its own and the other
                # floor vents'; the rest have no below-slab fixture to look up
                if dv.mark in [m for m, _u, _l in FLOOR_BRANCHES.values()]:
                    out += _floor_arms(b, dv)
                continue
            for unit, level, kinds in dv.serves:
                for k in kinds:
                    at = _fixture_at(b, unit, level, k)
                    if at is None:                      # it drains into a stack, not the slab
                        continue
                    run = abs(at[0]-dv.at[0])+abs(at[1]-dv.at[1])     # the branch turns square
                    out.append((b, dv.mark, opc_vents.Arm('%s %s %s' % (b.name, unit, k.upper()),
                                                          TRAP_SIZE[k], run)))
    return out


def _floor_arms(b, _dv):
    """Bath 2's arms: each lavatory's to the vent in the partition behind it (909.2 -- neither
       can be vented by a branch below its own floor); the closet's and the tub's to where they
       meet the branch, which is their wet vent (912.1). The mark is the vent each arm is
       measured to, so P-601's schedule and its riser agree on which pipe protects which trap."""
    out = []
    for i, k, name, trap, to, _at in _bath2_legs():
        mark = BATH2_VENTS.get(i, FLOOR_BRANCHES['A'][0])
        out.append((b, mark, opc_vents.Arm('%s UNIT 1 L2 %s' % (b.name, name), TRAP_SIZE[k],
                                           abs(trap[0]-to[0])+abs(trap[1]-to[1]))))
    return out


def trap_arms():
    """[(building, Arm)], for the rules that do not care which vent it is."""
    return [(b, a) for b, _mark, a in trap_arm_rows()]


def vent_ties():
    """Each dry vent that joins a stack: (mark, the height it ties in at, the highest flood
       level rim on that stack), from the first floor's finished floor. 905.4 wants 6\"."""
    out = []
    for dv in DRY_VENTS:
        if dv.ties_into is None:                        # V-B goes to the roof on its own
            continue
        b = next(x for x in BUILDINGS if x.number == dv.building)
        stack = next(st for st in b.stacks if st.name == dv.ties_into)
        rims = [levels.FLOOR_RISE*(l-1)+opc_vents.FLOOD_RIM[k]
                for _u, l, ks in stack.serves for k in ks]
        rims += [levels.FLOOR_RISE*(l-1)+opc_vents.FLOOD_RIM[k]
                 for _u, l, ks in dv.serves for k in ks]
        out.append((dv.mark, TIE_Z[dv.mark], max(rims)))
    return out


# ---------------- the three arrangements, as the code reads them ----------------
# Each has its own requirements, so each is built from the model separately and checked
# separately: 912.1.1 on the groups hanging on a stack, 912.1 on the groups below the slab
# that a dry vent stands in, 913 on the two waste stacks, and Table 909.1 on every trap.


def _from(path, at):
    """The part of a polyline from a point on it to its tail."""
    for i, (a, bb) in enumerate(zip(path, path[1:])):
        if _on_path(at, [a, bb]):
            return [at]+list(path[i+1:])
    return list(path)


def _walk(b, start):
    """The drain a discharge takes from a point, as [(run, its path from there)]: the run
       it stands on, then the run that receives that one, and so on to the exit."""
    out = []
    r = next((x for x in b.runs if _on_path(start, x.path) and not _same(start, x.path[-1])), None)
    at = start
    while r is not None and len(out) < 32:
        out.append((r, _from(r.path, at)))
        rec = receiver(b, r)
        at = r.path[-1]
        r = rec if isinstance(rec, Run) else None
    return out


def _flow_line(walk):
    pts = []
    for _r, seg in walk:
        pts += seg if not pts else seg[1:]
    return pts


def _size_after(walk, d):
    """The size of the pipe carrying the flow just past `d` feet along the walk: the
       section Table 912.3 sizes below a connection made there."""
    t = 0.0
    for r, seg in walk:
        t += _len(seg)
        if d < t-TOL:
            return SIZE_IN[r.size]
    return SIZE_IN[walk[-1][0].size]


def _join_at(b, line, pos):
    """How far along `line` the drain from `pos` joins it, or None if it never does."""
    if _on_path(pos, line):
        return _along(line, pos)
    for _r, seg in _walk(b, pos):
        for q in seg:
            if _on_path(q, line):
                return _along(line, q)
    return None


def _conns_on(st):
    """Every fixture connection on a stack: (unit, level, Conn), the height measured over
       LEVEL 1's finished floor so the whole stack is in one datum."""
    out = []
    for unit, level, kinds in st.serves:
        seen = {}
        for k in kinds:
            n = seen.get(k, 0); seen[k] = n+1
            z = levels.FLOOR_RISE*(level-1)+CONN_Z[k]+n*CONN_STEP
            out.append((unit, level, opc_vents.Conn('%s %s' % (unit, k.upper()), k, DFU[k], z, SIZE_IN[st.size])))
    return out


def vertical_wet_groups():
    """The bathroom groups that hang on a stack, as OPC 912.1.1 reads them: the stack is
       their vent from where it stops carrying drainage down to the lowest fixture drain.
       (name, the stack's size, [Conn] on it, the height the stack becomes a vent at)."""
    out = []
    for b in BUILDINGS:
        for st in b.stacks:
            if st.foot is None or st.name in WASTE_STACKS or st.name in FLOOR_BRANCHES:
                continue
            on_it = _conns_on(st)
            if not on_it:
                continue
            vent_from = max(c.at for _u, _l, c in on_it)
            for unit, level in sorted({(u, l) for u, l, _c in on_it}):
                conns = [c for u, l, c in on_it if (u, l) == (unit, level)]
                out.append(('%s stack %s, %s' % (b.name, st.name, unit), SIZE_IN[st.size], conns, vent_from))
    return out


def _pen_name(b, p):
    if p.kind == 'stack':
        return 'stack %s' % p.serves
    return ', '.join('%s %s' % (u, k.upper()) for u, _l, ks in p.serves for k in ks) or 'penetration %d' % p.mark


def horizontal_wet_groups():
    """The groups a dry vent stands in below the slab, as OPC 912.1 reads them: the fixtures
       in the direction of flow from the one the vent stands at, each with the section of
       branch below it, and anything else that connects to the same branch upstream of the
       most downstream of them. A vent serving ONE fixture is an individual vent, not this."""
    out = []
    for stack, (mark, unit, level) in FLOOR_BRANCHES.items():
        b = next(x for x in BUILDINGS if any(s.name == stack for s in x.stacks))
        conns = []
        for i, (k, at, size) in enumerate(BATH2_CONNS):
            conns.append(opc_vents.Conn('%s %s%s' % (unit, k.upper(), ' 2' if [c[0] for c in BATH2_CONNS[:i]].count(k) else ''),
                                        k, DFU[k], _branch_along(at), SIZE_IN[size]))
        out.append(('%s %s' % (b.name, mark), conns, conns[0].name, []))
    for dv in DRY_VENTS:
        served = [(u, l, k) for u, l, ks in dv.serves for k in ks]
        if len(served) < 2 or dv.mark in [m for m, _u, _l in FLOOR_BRANCHES.values()]:
            continue
        b = next(x for x in BUILDINGS if x.number == dv.building)
        head = next((_fixture_at(b, u, l, k) for u, l, k in served if k == dv.at_fixture), None)
        walk = _walk(b, head) if head is not None else []
        if not walk:
            out.append(('%s %s' % (b.name, dv.mark), [], dv.at_fixture.upper(), []))
            continue
        line = _flow_line(walk)
        conns = []
        for u, l, k in served:
            at = _fixture_at(b, u, l, k)
            d = _join_at(b, line, at)
            if d is None:
                continue
            conns.append(opc_vents.Conn('%s %s' % (u, k.upper()), k, DFU[k], d, _size_after(walk, d)))
        conns.sort(key=lambda c: c.at)
        mine = [_fixture_at(b, u, l, k) for u, l, k in served]
        last = max(c.at for c in conns) if conns else 0.0
        extras = []
        for p in b.pens:
            if p.kind == 'exit' or any(_same(p.pos, q) for q in mine):
                continue
            d = _join_at(b, line, p.pos)
            if d is not None and d < last-TOL:
                extras.append((_pen_name(b, p), d))
        head_name = next(c.name for c in conns if abs(c.at) < TOL)
        out.append(('%s %s' % (b.name, dv.mark), conns, head_name, extras))
    return out


def individual_vents():
    """The dry vents that serve ONE fixture: the kitchen sink and the laundry. Nothing wet
       vents anything here -- the vent stands on that fixture's own trap arm, Table 909.1."""
    return [dv for dv in DRY_VENTS if sum(len(ks) for _u, _l, ks in dv.serves) == 1]


def waste_stacks():
    """E and F as 913 reads them: (name, size, takes a water closet, the load at each branch
       interval, the load in all, and whether an offset lies between the lowest and the
       highest fixture connection -- 913.2 forbids that one, not the offset to the foot)."""
    out = []
    for b in BUILDINGS:
        for st in b.stacks:
            if st.name not in WASTE_STACKS:
                continue
            zs = [c.at for _u, _l, c in _conns_on(st)]
            foot = next(p for p in b.pens if p.mark == st.foot)
            offset = (not _same(foot.pos, st.pos)) and min(zs)-TOL <= STACK_OFFSET_Z <= max(zs)+TOL
            by = [sum(DFU[k] for k in ks) for _u, _l, ks in st.serves]
            wc = any(k == 'wc' for _u, _l, ks in st.serves for k in ks)
            out.append((st.name, SIZE_IN[st.size], wc, by, stack_dfu(st), offset))
    return out


# Every stack reaches a roof here: no vent joins another in the attic, the dry vents ride
# Every stack reaches a roof here: no vent joins another in the attic, the dry vents ride
# the stack they tie into, and V-B goes up on stack B. One roof penetration per stack.
ATTIC_TIES = {}


def vent_violations():
    """Every venting rule the set answers to: what each vent may serve (OPC 912 / 913), how
       far a trap stands from it (Table 909.1), how high it rises before it joins the stack
       vent (905.4) and its size at the roof (903.2). Its geometry too: inside its chase,
       clear of its stack."""
    v = opc_vents.roof_vent_violations(
        opc_vents.roof_vents(BUILDINGS, ATTIC_TIES, crit.WINTER_DESIGN_LO), crit.WINTER_DESIGN_LO)
    for b in BUILDINGS:
        slab = sorted((u, l, k) for p in b.pens if p.kind in ('drop', 'wc', 'tub') for u, l, ks in p.serves for k in ks)
        vented = {(u, l, k) for dv in DRY_VENTS if dv.building == b.number
                  for u, l, ks in dv.serves for k in ks}
        missing = [f for f in slab if f not in vented]
        if missing:
            v.append('%s: nothing vents %s, which drains below the slab' % (b.name, missing))
        for dv in DRY_VENTS:
            if dv.building == b.number and dv.ties_into and dv.ties_into not in [s.name for s in b.stacks]:
                v.append('%s: vent %s ties into stack %s, which it has not got' % (b.name, dv.mark, dv.ties_into))
    # 912 / 913: nothing on a lower level is vented BY a stack that drains a level above it.
    # A waste stack vent is the one thing that does vent every fixture on it, so E and F
    # are handed over to 913 by name -- drop either from WASTE_STACKS and this rule fails
    # the build instead, because their Level 1 fixtures have no dry vent of their own.
    stacks = []
    for b in BUILDINGS:
        dry = {(u, l, k) for dv in DRY_VENTS if dv.building == b.number
               for u, l, ks in dv.serves for k in ks}
        for st in b.stacks:
            drains = [('%s %s' % (u, k.upper()), l) for u, l, ks in st.serves for k in ks]
            wc = any(k == 'wc' for _u, _l, ks in st.serves for k in ks)
            # a fixture on the stack with no dry vent of its own is being vented BY the stack
            vented = [('%s %s' % (u, k.upper()), l) for u, l, ks in st.serves for k in ks
                      if (u, l, k) not in dry]
            stacks.append((st.name, wc, drains, vented))
    assert sorted(n for n, *_rest in waste_stacks()) == sorted(WASTE_STACKS), \
        'a stack is claimed under 913 and not checked against it'
    v += opc_vents.stack_vent_violations(stacks, claimed_913=WASTE_STACKS)
    v += opc_vents.trap_arm_violations([a for _b, a in trap_arms()])
    v += opc_vents.weir_violations(bath2_weirs())
    v += opc_vents.dry_vent_rise_violations(vent_ties())
    v += opc_vents.vertical_wet_violations(vertical_wet_groups())
    v += opc_vents.horizontal_wet_violations(horizontal_wet_groups())
    # Bath 2's branch runs in the Level 2 floor's webs, between the chords, all the way down.
    # `room` is where the BOTTOM chord starts, measured from the subfloor's top: the subfloor
    # and the top chord stand above the webs, so it is not the clear depth -- web_clear() is.
    room = levels.F2_DEPTH-TRUSS_CHORD
    if floor_branch_bottom() > room+1e-9:
        v.append('BUILDING 1: Bath 2\'s branch reaches %s under the subfloor at stack A, into the '
                 'bottom chord at %s' % (inches(floor_branch_bottom()), inches(room)))
    v += opc_vents.waste_stack_violations(waste_stacks())
    # the pipe has to fit where it is drawn: clear of its stack, inside the chase that holds it
    for dv in DRY_VENTS:
        if dv.ties_into is None:
            continue
        b = next(x for x in BUILDINGS if x.number == dv.building)
        st = next(x for x in b.stacks if x.name == dv.ties_into)
        gap = math.hypot(dv.at[0]-st.pos[0], dv.at[1]-st.pos[1])
        need = (_od(dv.size)+_od(st.size))/2.0
        if gap < need-1e-9:
            v.append('%s: vent %s stands %s from stack %s, inside the two pipes\' %s'
                     % (b.name, dv.mark, fmt(gap), st.name, fmt(need)))
    return v



# ================================ the sewer ================================
# One 4" building sewer in the south side yard, midway between the buildings and the lot
# line, under the Units 2 / 3 walk: from Building 2's exit to Oak Avenue, Building 1's
# lateral joining it on the way. The main is taken MAIN_TO_LOT past the Oak lot line, as
# the water's is; Columbus DPU locates both.
SEWER_X = SITE_W-SIDE_YARD/2.0
SEWER_COVER_MIN = 1.0              # earth over the sewer's crown anywhere on the lot; the set's own floor
MAIN_TO_LOT = pm.MAIN_TO_LOT


def sewer():
    """C-101's route from the Building 2 exit to Oak Avenue: its on-lot length, the
       length to the main, the fall at SEWER_SLOPE, the invert where Building 1's lateral
       joins and the invert the main must be at or below — all below finished grade, in
       feet, negative down."""
    b1, b2 = BUILDINGS
    x1, y1 = exit_site(b1); x2, y2 = exit_site(b2)
    route = [(x2, y2), (SEWER_X, y2), (SEWER_X, 0.0)]
    lateral = [(x1, y1), (SEWER_X, y1)]
    on_lot = _len(route)
    to_main = on_lot+MAIN_TO_LOT
    inv1 = below_grade(exit_invert(b1, cover=COVER)); inv2 = below_grade(exit_invert(b2, cover=COVER))
    to_junction = (SEWER_X-x2)+(y2-y1)
    junction = inv2-SEWER_SLOPE/12.0*to_junction
    lateral_needs = junction+SEWER_SLOPE/12.0*_len(lateral)
    return dict(route=route, lateral=lateral, on_lot=on_lot, to_main=to_main,
                fall=SEWER_SLOPE/12.0*to_main, exit1=inv1, exit2=inv2, junction=junction,
                lateral_needs=lateral_needs, lateral_fall=inv1-junction,
                main_max=inv2-SEWER_SLOPE/12.0*to_main)


def cleanouts():
    """C-101's exterior cleanouts, site feet: where each building drain meets the sewer, and
       just inside the Oak lot line."""
    s = sewer()
    return [s['route'][1], s['lateral'][1], (SEWER_X, 2.0)]


def sewer_cover():
    """The least earth over the sewer's crown on the lot, feet, and where: the lot falls to
       Oak Avenue as C-103 grades it, from finished grade at the walls to FRONT_LOT at the
       lot line, taken straight-line along the south yard."""
    from src.grading import FRONT_LOT
    s = sewer()
    y2 = s['route'][1][1]
    worst = None
    for k in range(0, 101):
        y = y2*(1-k/100.0)
        inv = s['exit2']-SEWER_SLOPE/12.0*((SEWER_X-s['route'][0][0])+(y2-y))
        ground = FRONT_LOT*(1.0-min(1.0, y/B1_Y)) if y < B1_Y else 0.0
        cover = ground-(inv+IN(SIZE_IN['4']))
        if worst is None or cover < worst[0]: worst = (cover, y)
    return worst


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
       the main in Oak Avenue, down the north side yard, to its riser; then each trunk
       below the slab, riser to riser."""
    pb = _pm(b)
    assert abs(pb.entry[1]-pb.riser[1]) < TOL, '%s: the supply is not square to its wall' % b.name
    # from the main in Oak Avenue down the north side yard, then square through the wall
    out = [('SERVICE', [(pm.YARD_X, -(b.site[1]+pm.MAIN_TO_LOT)), (pm.YARD_X, pb.entry[1]), pb.riser])]
    for names, path, under in pb.trunks:
        if under:
            who = names[0] if len(names) == 1 else 'UNITS '+' AND '.join(n.split()[-1] for n in names)
            out.append(('%s TRUNK' % who, list(path)))
    return out


def _outside(line):
    """The part of a service line outside its building's north wall, and its length."""
    wall = (0.0, line[-1][1])
    return list(line[:-1])+[wall], _along(line, wall)


def _sewers():
    """C-101's building sewer and Building 2's lateral in site feet: (name, path, invert
       below grade at a distance along it, size)."""
    s = sewer(); b1, b2 = BUILDINGS
    L = _len(s['lateral'])
    return [('BUILDING SEWER', s['route'], lambda t: s['exit2']-SEWER_SLOPE/12.0*t, exit_run(b2).size),
            ('BUILDING 1 LATERAL', s['lateral'], lambda t: s['exit1']-(s['exit1']-s['junction'])*t/L, exit_run(b1).size)]


# What OPC 603.2 is checked against here: arkitect/codes/ohio/opc_separation.py reads nothing else.
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
    out = _outside(water_lines(b)[0][1])[1]
    return (out-sp[0][0], sp[0][1]-out)


def service_to_sewer(b):
    """The nearest the service comes to the building sewer or the lateral between the main
       and the wall, feet."""
    line = water_lines(b)[0][1]
    wall = list(_points(_outside(line)[0]))
    return min(_pt_seg_dist(_to_site(b, q), a, bb) for q in wall for _nm, path, _i, _s in _sewers()
               for a, bb in zip(path, path[1:]))


# ================================ the checker ================================
def drainage_violations():
    v = (vent_violations()+laundry_violations()+stack_violations()
         +washer_violations(BUILDINGS)+cavity_violations())
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
    if s['exit1'] < s['lateral_needs']-TOL:
        v.append('BUILDING 1: its exit is below the sewer where its lateral joins it')
    cover, at = sewer_cover()
    if cover < SEWER_COVER_MIN-TOL:
        v.append('the sewer has %s of earth over it %s from Oak Avenue, under %s' % (inches(cover), fmt(at), inches(SEWER_COVER_MIN)))
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
        for q in _points(_outside(line)[0], step=0.5):
            t = _along(line, q)
            near = [nm for nm, path, _i, _s in _sewers()
                    if min(_pt_seg_dist(_to_site(b, q), a, bb) for a, bb in zip(path, path[1:])) < SEWER_SEP-TOL]
            if near and not any(lo-TOL <= t <= hi+TOL for lo, hi in cover):
                v.append('%s: the service is within %s of the %s outside the wall, unsleeved' % (b.name, fmt(SEWER_SEP), near[0].lower()))
                break
    return v


def footing_centreline(b):
    """The continuous footing's centreline, under the foundation wall's: a closed loop."""
    h = WALL_T/2.0
    return [(h, h), (b.W-h, h), (b.W-h, b.D-h), (h, b.D-h)]


def thickened_footing(b):
    """Where the footing is thickened for this building's water service (P-601 details 1 and
       2), located on its centreline for S-101: the service runs square to its wall from the
       entry to the riser, so it crosses the centreline on that line."""
    pb = _pm(b)
    x, y = pb.entry
    loop = footing_centreline(b)
    xs = sorted({p[0] for p in loop}); ys = sorted({p[1] for p in loop})
    if abs(y-pb.riser[1]) < TOL:                     # square to an x-wall
        cx = xs[0] if x < xs[0] else xs[-1]
        crossing = (cx, y)
    else:
        cy = ys[0] if y < ys[0] else ys[-1]
        crossing = (x, cy)
    return thickened_zone(entry_for(b, GROUND), loop, crossing)


def check_drainage():
    """From build.check_model(): every fixture drained, every pipe sized and every
       invert derived, or the build stops with the building and the rule named."""
    v = drainage_violations()
    assert not v, 'DRAINAGE: %d violation(s):\n  ' % len(v)+'\n  '.join(v)
    v = entries_violations(BUILDINGS, GROUND)
    v += ['%s: %s' % (b.name, t) for b in BUILDINGS
          for t in zone_violations(entry_for(b, GROUND), footing_centreline(b), thickened_footing(b))]
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
    print('DRAINAGE sewer cover: %s over its crown at the least, %s from Oak Avenue' % (inches(sewer_cover()[0]), fmt(sewer_cover()[1])))
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
        z = thickened_footing(b)
        print('DRAINAGE %s: the thickened footing runs %s on its centreline%s' % (
            b.name, ' + '.join(fmt(l) for l in z.legs),
            ', turning %d corner%s' % (len(z.corners), '' if len(z.corners) == 1 else 's') if z.corners else ', straight'))

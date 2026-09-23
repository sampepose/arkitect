"""Wall bracing of both buildings, RCO 602.10, derived: what S-104 draws.

Page feet, the system S-101 and S-102 use: x from the north face (396 Oak), y from the
front face (Oak for Building 1, the courtyard for Building 2), both out to out.

Every exterior wall is a braced wall line and nothing else is: the house's stair wall,
Building 2's bearing wall and the partitions carry no bracing. The openings in each line
are read from the same opening lists the plans, the elevations and the header schedule
read, through the same regrid, so a window moved on A-101 moves a braced wall panel here.
"""
from collections import namedtuple
from lib.units import fmt
from src import levels
from src.openings import WIN_GEOM
from codes.ohio.rco.bracing import corner_segment, end_condition, factor, provided, segments
from codes.ohio.rco.bracing import roof_connection
from codes.ohio.rco.bracing import header_depth

HEEL_NOM = levels.ROOF_HEEL
FRONT = {'BUILDING 1': 'FRONT WALL', 'BUILDING 2': 'COURTYARD WALL'}

# ---------------- the opening lists, in page feet along each wall ----------------
DOOR_HEIGHT = 6.0+8.0/12.0          # D-1 and D-2, 6'-8", A-602: every exterior door

Opening = namedtuple('Opening', 'a b height mark')      # along the wall, page feet; clear height, feet
WallRun = namedtuple('WallRun', 'building level name o at length openings')
# o 'x': the wall runs along page x at page y `at`; o 'y': along page y at page x `at`.


def _openings(building, level):
    """{wall name: [Opening]} for one building at one level, from the plans' own window and
       exterior-door lists through that level's regrid. Model x runs from the SOUTH wall,
       so page x is W less it."""
    from src import building1 as B1, building2 as B2
    from src import schedules
    if building == 'BUILDING 1':
        m = B1.LEVEL[level]; P, W, rear = m['plan'], B1.B1_W, B1.Y_REAR
        wins, doors, mark = m['wins'], m['doors'], schedules._b1_mark
    else:
        P, W, rear = B2.PLAN_B2, B2.B2_W, B2.Y_REAR
        wins, doors, mark = B2.b2_wins(level), B2.B2doors, schedules._b2_mark
    items = [(w[:4], WIN_GEOM[w[4]][1], 'W-'+w[4]) for w in wins]
    items += [(d[:4], DOOR_HEIGHT, mark(d)) for d in doors if 'ext' in d[5:]]
    out = {}
    for (x, y, ln, o), h, mk in items:
        if o == 'h':
            wall = FRONT[building] if y < 1.0 else 'REAR WALL'
            assert y < 1.0 or abs(y-rear) < 1e-6, '%s L%d: %s is on no exterior wall' % (building, level, mk)
            a = W-P.x(x, y)-ln
        else:
            wall = 'SOUTH WALL' if x < 1.0 else 'NORTH WALL'
            assert x < 1.0 or x > W-1.0, '%s L%d: %s is on no exterior wall' % (building, level, mk)
            a = P.y(y)
        out.setdefault(wall, []).append(Opening(a, a+ln, h, mk))
    return out


def wall_runs():
    """The four exterior walls of each building, level by level, with their openings
       sorted along the wall."""
    from src.building1 import B1_D, B1_W
    from src.building2 import B2_D, B2_W
    runs = []
    for building, W, D in (('BUILDING 1', B1_W, B1_D), ('BUILDING 2', B2_W, B2_D)):
        for level in (1, 2):
            ops = _openings(building, level)
            for name, o, at, length in ((FRONT[building], 'x', 0.0, W), ('REAR WALL', 'x', D, W),
                                        ('NORTH WALL', 'y', 0.0, D), ('SOUTH WALL', 'y', W, D)):
                runs.append(WallRun(building, level, name, o, at, length,
                                    tuple(sorted(ops.get(name, ()), key=lambda op: op.a))))
    return runs


# ---------------- heights the tables are entered with ----------------
# Wall height: bottom of the sole plate to the top of the double top plate, per storey.
WALL_HEIGHT = {
    ('BUILDING 1', 1): max(levels.F1_PLATE, levels.F2_PLATE)-levels.SLAB_TOP,
    ('BUILDING 1', 2): levels.ROOF_PLATE-levels.SUBFLOOR_TOP,
    ('BUILDING 2', 1): levels.F1_PLATE-levels.SLAB_TOP,
    ('BUILDING 2', 2): levels.ROOF_PLATE-levels.SUBFLOOR_TOP,
}
# Story height, R301.3: Level 1 is the floor-to-floor rise; Level 2 the plate height.
STORY_HEIGHT = {1: levels.FF2-levels.FF1, 2: levels.ROOF_PLATE-levels.SUBFLOOR_TOP}


def eave_to_ridge(span):
    """Roof eave-to-ridge height: the 4:12 rise over half the span, on the raised heel,
       which the ridge carries."""
    return levels.ridge(span)-levels.ROOF_PLATE


# RCO R602.10, transcribed: shared, see codes/ohio/rco/bracing.py
from codes.ohio.rco.bracing import (CS_PF_CREDIT, EXPOSURE, FIRST_PANEL_MAX, F_EAVE_RIDGE, F_EXPOSURE,
                                    F_LINES, F_STORY_HEIGHT, GYP_SHEATHING_T, HOLD_DOWN_LB, MAX_SPACING,
                                    METHOD, NAIL, NAIL_LENGTH, NAIL_PENETRATION, NAIL_W1R, ONE_PANEL_MIN,
                                    PANEL_GAP_MAX, PORTAL_HEADER, PORTAL_MAX_HEADER_HEIGHT,
                                    PORTAL_MAX_PER_LINE, PORTAL_OPENING, REQ_LENGTH, SHEATHING_T, STORY,
                                    TWO_PANEL_LINE, cs_pf_min, cs_wsp_min, interp, strap_lb)


from src.criteria import WIND, WIND_VULT, WIND_EXPOSURE
from codes.ohio.rco.bracing import require_column
# The shared tables are ONE column of Table 602.10.3(1) and Table 602.10.6.4; this project's
# design criteria have to be that column before a figure from them is printed.
require_column(WIND_VULT, WIND_EXPOSURE, WIND)

# ---------------- panels and lines ----------------
Panel = namedtuple('Panel', 'a b method min_len credit')  # page feet along the wall; credit, feet
Line = namedtuple('Line', 'tag building level wall o at length spacing story factors base required panels ends wall_height openings')

TAG = {'FRONT WALL': '1', 'COURTYARD WALL': '1', 'REAR WALL': '2', 'NORTH WALL': 'A', 'SOUTH WALL': 'B'}


def panels(run, wall_height, portal=False):
    """The segments that are braced wall panels. A segment is CS-WSP where it meets Table
       602.10.5 for its taller adjacent opening; with `portal`, a segment beside a door
       that is short of that but meets the CS-PF minimum is a portal frame."""
    out = []
    for s in segments(run):
        near = [o for o in (s.left, s.right) if o is not None]
        need = cs_wsp_min(wall_height, max([o.height for o in near] or [0.0]))
        length = s.b-s.a
        if length >= need-1e-9:
            out.append(Panel(s.a, s.b, METHOD, need, length))
        elif portal and any(o.mark.startswith('D-') for o in near) and length >= cs_pf_min(wall_height)-1e-9:
            out.append(Panel(s.a, s.b, 'CS-PF', cs_pf_min(wall_height), CS_PF_CREDIT*length))
    return out


def location_violations(length, ps):
    """602.10.2.2 and 602.10.2.3 for one line's panels."""
    if not ps:
        return ['no braced wall panel']
    v = []
    if ps[0].a > FIRST_PANEL_MAX+1e-9:
        v.append('the first panel begins %s from the start of the line' % fmt(ps[0].a))
    if length-ps[-1].b > FIRST_PANEL_MAX+1e-9:
        v.append('the last panel ends %s from the end of the line' % fmt(length-ps[-1].b))
    for p, q in zip(ps, ps[1:]):
        if q.a-p.b > PANEL_GAP_MAX+1e-9:
            v.append('%s between the panels at %s and %s' % (fmt(q.a-p.b), fmt(p.b), fmt(q.a)))
    # A line with no opening in it is braced from corner to corner: the house's north wall at
    # Level 1, one 33'-0" length. It stands for two panels. A long segment BESIDE an opening
    # still counts once, as 300 S Elm counts it, which is what puts the portal frame beside
    # Unit 2's entry.
    whole = len(ps) == 1 and ps[0].a < 1e-9 and ps[0].b > length-1e-9 and length >= 2*ONE_PANEL_MIN
    count = 2 if whole else len(ps)
    if count < 2 and (length > TWO_PANEL_LINE+1e-9 or ps[0].b-ps[0].a < ONE_PANEL_MIN-1e-9):
        v.append('%d braced wall panel on a %s line' % (len(ps), fmt(length)))
    return v


def _corner_run(run, side, by):
    """The perpendicular wall at this run's `side`, and which of its ends meets it."""
    b, lv = run.building, run.level
    if run.o == 'x':
        other = by[(b, lv, 'NORTH WALL' if side == 'lo' else 'SOUTH WALL')]
    else:
        other = by[(b, lv, FRONT[b] if side == 'lo' else 'REAR WALL')]
    return other, ('lo' if run.at < 1e-9 else 'hi')


def build_lines(runs):
    by = {(r.building, r.level, r.name): r for r in runs}
    out = []
    for r in runs:
        W = by[(r.building, r.level, 'REAR WALL')].length
        D = by[(r.building, r.level, 'NORTH WALL')].length
        spacing = D if r.o == 'x' else W
        story = STORY[r.level]
        n = sum(1 for q in runs if q.building == r.building and q.level == r.level and q.o == r.o)
        wall_height = WALL_HEIGHT[(r.building, r.level)]
        factors = (('EXPOSURE %s' % EXPOSURE, F_EXPOSURE[EXPOSURE]),
                   ('EAVE TO RIDGE %s' % fmt(eave_to_ridge(W)), interp(F_EAVE_RIDGE[story], eave_to_ridge(W))),
                   ('STORY HEIGHT %s' % fmt(STORY_HEIGHT[r.level]), interp(F_STORY_HEIGHT, STORY_HEIGHT[r.level])),
                   ('%d BRACED WALL LINES' % n, interp(F_LINES, n)))
        base = interp(REQ_LENGTH[story], spacing)
        required = base
        for _nm, f in factors:
            required *= f
        ps = panels(r, wall_height)
        if location_violations(r.length, ps):
            ps = panels(r, wall_height, portal=True)
        ends = []
        if ps:
            for side in ('lo', 'hi'):
                other, oside = _corner_run(r, side, by)
                ends.append(end_condition(r, side, ps, corner_segment(other, oside)))
        out.append(Line(TAG[r.name], r.building, r.level, r.name, r.o, r.at, r.length, spacing, story,
                        factors, base, required, tuple(ps), tuple(ends), wall_height, r.openings))
    return out


LINES = build_lines(wall_runs())


# W1R puts 7/16" OSB over 5/8" Type X exterior gypsum, which is why those walls take the
# longer nail. On this lot W1R is every Level 1 exterior wall of Building 2, the
# construction that supports F1 (A-601, RCO 302.3.1).
def w1r_lines():
    return tuple(ln for ln in LINES if ln.building == 'BUILDING 2' and ln.level == 1)


def w1r_text():
    return 'EVERY BRACED WALL LINE OF BUILDING 2 AT LEVEL 1'


def portal_openings(line):
    """[(panel, opening)] for each CS-PF panel of the line: the door it stands beside,
       or None."""
    out = []
    for p in line.panels:
        if p.method != 'CS-PF':
            continue
        door = [o for o in line.openings if o.mark.startswith('D-') and (abs(o.b-p.a) < 1e-6 or abs(o.a-p.b) < 1e-6)]
        out.append((p, door[0] if door else None))
    return out


def schedule_header(line, opening):
    """The S-102 header over this opening: src/framing.py HEADERS, matched by building,
       level, wall and width. None where the schedule has no such row."""
    from src.framing import HEADERS
    hs = [h for h in HEADERS if h.building == line.building and h.level == line.level and h.wall == line.wall
          and abs(h.width-(opening.b-opening.a)) < 1e-6]
    return hs[0] if hs else None


# ---------------- connections ----------------
# The floors: which way the joists run, from src/framing.py, decides R602.10.8 item 1 or
# item 2 for each wall. The roof: which way the trusses run decides
# which walls R602.10.8.2 reaches, and the heel decides the item.
def joist_run(building):
    from src.framing import FLOORS
    (fl,) = [f for f in FLOORS if f.name == building]
    runs = {'x' if b.run == 'h' else 'y' for b in fl.bays}
    assert len(runs) == 1, '%s: joists run both ways, %s' % (building, runs)
    return runs.pop()


def floor_connection(line):
    """602.10.8 item at this wall's floor: 1 where the joists are perpendicular to it,
       2 where they are parallel."""
    return 2 if joist_run(line.building) == line.o else 1




def truss_perpendicular(line):
    """Do the trusses cross this wall? They span x, side wall to side wall, on both roofs
       (S-102 note 7), so they bear on the north and south walls."""
    return line.o == 'y'


# ---------------- the checks ----------------
def bracing_violations(lines):
    v = []
    for ln in lines:
        nm = '%s L%d BWL %s' % (ln.building, ln.level, ln.tag)
        if ln.spacing > MAX_SPACING+1e-9:
            v.append('%s: %s spacing past the %s of Table 602.10.1.3' % (nm, fmt(ln.spacing), fmt(MAX_SPACING)))
        if provided(ln)+1e-9 < ln.required:
            v.append('%s: %.2f ft of bracing where %.2f ft is required' % (nm, provided(ln), ln.required))
        v += ['%s: %s' % (nm, x) for x in location_violations(ln.length, list(ln.panels))]
        if len(ln.ends) != 2:
            v.append('%s: its ends are not resolved' % nm)
        for e in ln.ends:
            if e.condition is None:
                v.append('%s: no 602.10.7 end condition at its %s end' % (nm, e.side))
        pf = portal_openings(ln)
        if len(pf) > PORTAL_MAX_PER_LINE:
            v.append('%s: %d CS-PF panels, over the %d of 602.10.6.4' % (nm, len(pf), PORTAL_MAX_PER_LINE))
        for p, o in pf:
            if o is None:
                v.append('%s: the CS-PF panel at %s stands beside no door' % (nm, fmt(p.a)))
                continue
            w = o.b-o.a
            if not PORTAL_OPENING[0]-1e-9 <= w <= PORTAL_OPENING[1]+1e-9:
                v.append('%s: a %s opening beside a CS-PF panel, outside %s to %s' % (nm, fmt(w), fmt(PORTAL_OPENING[0]), fmt(PORTAL_OPENING[1])))
            if ln.wall_height > PORTAL_MAX_HEADER_HEIGHT+1e-9:
                v.append('%s: a CS-PF header %s up, over the %s of Figure 602.10.6.4' % (nm, fmt(ln.wall_height), fmt(PORTAL_MAX_HEADER_HEIGHT)))
            try:
                strap_lb(ln.wall_height, w)
            except ValueError as ex:
                v.append('%s: %s' % (nm, ex))
            h = schedule_header(ln, o)
            if h is not None and header_depth(h.size) > PORTAL_HEADER[1]+1e-9:
                v.append('%s: the S-102 header %s over the portal is deeper than its %s portal header'
                         % (nm, h.size, fmt(PORTAL_HEADER[1])))
    for name in sorted({ln.building for ln in lines}):
        for level in sorted({ln.level for ln in lines if ln.building == name}):
            for o in ('x', 'y'):
                if sum(1 for ln in lines if ln.building == name and ln.level == level and ln.o == o) != 2:
                    v.append('%s L%d: not two braced wall lines along %s' % (name, level, o))
    for nail, through in ((NAIL, SHEATHING_T), (NAIL_W1R, SHEATHING_T+GYP_SHEATHING_T)):
        if NAIL_LENGTH[nail]-through < NAIL_PENETRATION-1e-9:
            v.append('%s penetrates %s into the framing, under %s' % (nail, fmt(NAIL_LENGTH[nail]-through), fmt(NAIL_PENETRATION)))
    return v


def check_bracing():
    for ln in LINES:
        print('BRACING %s L%d BWL %s %-22s %s spacing, %s: %.2f x %.3f = %.2f FT REQUIRED; %d PANELS, %.2f FT (%s); ENDS %s'
              % (ln.building, ln.level, ln.tag, ln.wall, fmt(ln.spacing), ln.story, ln.base, factor(ln), ln.required,
                 len(ln.panels), provided(ln), ', '.join('%s %s' % (fmt(p.b-p.a), p.method) for p in ln.panels),
                 ' / '.join('%s%s' % (e.condition, ' + %d LB HOLD-DOWN' % HOLD_DOWN_LB if e.hold_down is not None else '')
                            for e in ln.ends)))
    print('BRACING roof connection where the trusses cross the wall: 602.10.8.2 %s, heel %s' % (roof_connection(heel_nom=HEEL_NOM), fmt(HEEL_NOM)))
    bad = bracing_violations(LINES)
    assert not bad, 'bracing:\n  ' + '\n  '.join(bad)

"""The floor framing of both buildings, derived: what S-102 draws.

Everything is in FINAL SHEET feet, the system S-101 and C-101 use. The bays are the
joist bays S-102 prints and S-101 casts strips under (the architectural plans used to
print them as span arrows too, and no longer do); the
Unit 1 well is the stair's own constants; nothing is typed that another sheet prints.
The I-joists themselves are the manufacturer's, sized to the loads stated here.
"""
from collections import namedtuple
from arkitect.lib.units import IN, fmt, inches
from arkitect.lib.model import fit
from arkitect.lib.model.regrid import EXT_STUD
from src.openings import WIN_HEAD
from src import levels
from src.building1 import (B0, D_STUD, SX, U1_STAIR_WALL, U23_BEARING_WALL, W_STUD, YT, Y_SEP_BOT,
                           site_x, site_y)
from src.building2 import B2_D, B2_W, U45_BEARING_WALL, Y_BEAR
from src.mirror import B1_W
from arkitect.codes.ohio.rco.floor_checks import floor_violations, bay_span

# ---------------- basis ----------------
JOIST_OC = IN(16)
F1_JOIST = levels.F1_JOIST          # 11-7/8" I-joists, the rated floor
F2_JOIST = levels.F2_JOIST          # 14" I-joists, Unit 1's floor
SUBFLOOR = levels.SUBFLOOR          # 3/4" T&G, glued and screwed
MAX_SPAN = {F1_JOIST: 16.0, F2_JOIST: 26.0}   # a bay that grows past this fails; not a sizing

# RCO Table R301.5 live loads and RCO R301.7 deflection: the joist and truss submittals
# are designed to these. Dead loads are this set's assemblies (A-601).
LIVE_LOADS = [("SLEEPING AREAS", 30), ("ALL OTHER FLOOR AREAS", 40), ("STAIRS", 40)]
GUARD_LOAD = 200                    # lb, concentrated, any direction
DEAD_LOADS = [("F1, THE RATED CEILING INCLUDED", 15), ("F2", 12)]

# F1's listing, ICC-ES ESR-1153 Figure 3F (Assembly F): TJI joists with nominal 2x4 or
# larger flanges, at most 24" o.c. in a floor-ceiling; RC-1 channels at 16" o.c.; a
# 1-1/2" mineral wool blanket, 2-1/2 pcf minimum, friction-fitted on the channels; ONE
# layer of 5/8" Type C. Transcribed from the report, not from a summary.
#
# Assembly F states 16" o.c. for the channels flat. It does NOT carry Assembly B's
# "24" o.c. where the joists are at 16" o.c." allowance -- do not put that back.
F1_MAX_JOIST_OC = IN(24)
F1_MAX_CHANNEL_OC = IN(16)
F1_MIN_FLANGE_W = IN(3.5)       # nominal 2x4
F1_MIN_INSUL_T = IN(1.5)
F1_MIN_INSUL_PCF = 2.5


def f1_listing_violations(joist_oc=None, flange_w=None, layers=None, layer=None,
                          board=None, channel_oc=None, insul_t=None, insul_pcf=None):
    """Every way the F1 framing and build-up leave ESR-1153 Assembly F. Arguments override
       the model, so a test can ask what a change would do."""
    joist_oc = JOIST_OC if joist_oc is None else joist_oc
    flange_w = levels.F1_FLANGE_W if flange_w is None else flange_w
    layers = levels.F1_LAYERS if layers is None else layers
    layer = levels.F1_LAYER if layer is None else layer
    board = levels.F1_BOARD if board is None else board
    channel_oc = levels.F1_CHANNEL_OC if channel_oc is None else channel_oc
    insul_t = levels.F1_INSUL_T if insul_t is None else insul_t
    insul_pcf = levels.F1_INSUL_PCF if insul_pcf is None else insul_pcf
    i = lambda v: '%g"' % round(v*12, 4)
    v = []
    if joist_oc > F1_MAX_JOIST_OC+1e-9:
        v.append('F1 joists at %s o.c. exceed the %s of %s' % (i(joist_oc), i(F1_MAX_JOIST_OC), levels.F1_LISTING))
    if flange_w < F1_MIN_FLANGE_W-1e-9:
        v.append('F1 joist flanges %s are under the nominal 2x4 (%s) %s tests' % (i(flange_w), i(F1_MIN_FLANGE_W), levels.F1_LISTING))
    if layers != 1 or abs(layer-IN(.625)) > 1e-9:
        v.append('F1 membrane %d x %s is not the one 5/8" layer of %s' % (layers, i(layer), levels.F1_LISTING))
    if board != 'TYPE C':
        v.append('F1 board %s is not the Type C of %s; Type X is not an alternate' % (board, levels.F1_LISTING))
    if channel_oc > F1_MAX_CHANNEL_OC+1e-9:
        v.append('F1 channels at %s o.c. exceed the %s of %s' % (i(channel_oc), i(F1_MAX_CHANNEL_OC), levels.F1_LISTING))
    if insul_t < F1_MIN_INSUL_T-1e-9:
        v.append('F1 mineral wool %s is under the %s of %s' % (i(insul_t), i(F1_MIN_INSUL_T), levels.F1_LISTING))
    if insul_pcf < F1_MIN_INSUL_PCF-1e-9:
        v.append('F1 mineral wool %g pcf is under the %g pcf of %s' % (insul_pcf, F1_MIN_INSUL_PCF, levels.F1_LISTING))
    return v
DEFLECTION = "L/360 LIVE LOAD"
from src.criteria import GROUND_SNOW   # RCO Table 301.2(1); S-102 and S-103 print it

# ---------------- the floors ----------------
Bay = namedtuple('Bay', 'name x0 y0 x1 y1 run joist bearing')     # run 'h': joists run in x
Well = namedtuple('Well', 'x0 y0 x1 y1 header_x0 header_x1')
Floor = namedtuple('Floor', 'name W D bays wells rated_rims outline_sf', defaults=(None,))
# rated_rims: (x0, y0, x1, y1, label) — a floor edge along a wall PARALLEL to the joists
# that carries a wall above; the rim board or full-depth blocking there is rated by the
# manufacturer for that wall's load (Building 2's side walls carry its roof).
# outline_sf: the floor's own Level 2 plate outline, SF, for the tile check below to
# compare against — None (a synthetic test floor) falls back to the generic exterior-
# stud rectangle, computed from the floor's own W and D rather than a real building's.

_bw = U23_BEARING_WALL
_BW_TOL = 0.05      # ft, ~5/8"; the regrid is not perfectly linear across the wall's width
# Unit 1's stud faces are the study's, which are now the same 2x6 faces as everyone
# else's, and the Units 2/3 bearing-wall sliver between the two F1 bays is wall, not
# floor, so it comes back out of the sum.
_B1_OUTLINE_SF = ((site_x(W_STUD)-site_x(0))*(site_y(D_STUD)-site_y(0))
                  + (B1_W-2*EXT_STUD)*(48.0-EXT_STUD-Y_SEP_BOT)
                  - (_bw[2]-_bw[0])*(48.0-EXT_STUD-Y_SEP_BOT))
B1_FLOOR = Floor("BUILDING 1", B1_W, 48.0,
    bays=[Bay('UNIT 1 F2', site_x(0), site_y(0), site_x(W_STUD), site_y(D_STUD), 'h', F2_JOIST,
              ('SAGE WALL, W1', 'ADJACENT-PARCEL WALL, W1')),
          Bay('UNITS 2 / 3 F1, SAGE BAY', EXT_STUD, Y_SEP_BOT, _bw[0], 48.0-EXT_STUD, 'h', F1_JOIST,
              ('SAGE WALL, W1R', 'UNITS 2 AND 3 BEARING WALL, W3')),
          Bay('UNITS 2 / 3 F1, PARCEL BAY', _bw[2], Y_SEP_BOT, B1_W-EXT_STUD, 48.0-EXT_STUD, 'h', F1_JOIST,
              ('UNITS 2 AND 3 BEARING WALL, W3', 'ADJACENT-PARCEL WALL, W1R'))],
    # the well at the Sage end of Unit 1's bay: its header stands on the stair wall
    wells=[Well(site_x(0), site_y(B0), site_x(SX), site_y(YT), U1_STAIR_WALL[0], U1_STAIR_WALL[2])],
    rated_rims=[],     # Building 1's front and rear walls, parallel to the joists, carry nothing above
    outline_sf=_B1_OUTLINE_SF)

_uw = U45_BEARING_WALL
# Building 2's bearing-wall sliver between its two bays is wall, not floor, so it too
# comes back out of the full exterior-stud rectangle.
_B2_OUTLINE_SF = (B2_W-2*EXT_STUD)*(B2_D-2*EXT_STUD) - (B2_W-2*EXT_STUD)*(_uw[3]-_uw[1])
B2_FLOOR = Floor("BUILDING 2", B2_W, B2_D,
    bays=[Bay('UNITS 4 / 5 F1, COURTYARD BAY', EXT_STUD, EXT_STUD, B2_W-EXT_STUD, _uw[1], 'v', F1_JOIST,
              ('COURTYARD WALL, W1R', 'UNITS 4 AND 5 BEARING WALL, W3')),
          Bay('UNITS 4 / 5 F1, REAR BAY', EXT_STUD, _uw[3], B2_W-EXT_STUD, B2_D-EXT_STUD, 'v', F1_JOIST,
              ('UNITS 4 AND 5 BEARING WALL, W3', 'REAR WALL, W1R'))],
    wells=[],
    rated_rims=[(EXT_STUD, EXT_STUD, EXT_STUD, B2_D-EXT_STUD, 'RIM RATED FOR THE ROOF-BEARING WALL ABOVE'),
                (B2_W-EXT_STUD, EXT_STUD, B2_W-EXT_STUD, B2_D-EXT_STUD, 'RIM RATED FOR THE ROOF-BEARING WALL ABOVE')],
    outline_sf=_B2_OUTLINE_SF)

FLOORS = (B1_FLOOR, B2_FLOOR)




# ---------------- the checks ----------------
def _bearing_lines(floor):
    """The lines a joist may end on: the exterior stud faces, and the strips S-101 casts."""
    from src.foundation import B1, B2
    b = B1 if floor.name == "BUILDING 1" else B2
    lines = [(EXT_STUD, 0.0, EXT_STUD, floor.D, 'SAGE WALL'), (floor.W-EXT_STUD, 0.0, floor.W-EXT_STUD, floor.D, 'ADJACENT-PARCEL WALL'),
             (0.0, EXT_STUD, floor.W, EXT_STUD, 'FRONT WALL'), (0.0, floor.D-EXT_STUD, floor.W, floor.D-EXT_STUD, 'REAR WALL')]
    for x0, y0, x1, y1, nm in b.strips:
        lines.append((x0, y0, x1, y1, nm))
    return lines




def framing_violations():
    v = []
    for fl in FLOORS:
        v += floor_violations(fl, max_span=MAX_SPAN, _bearing_lines=_bearing_lines)
    v += header_violations()
    # load path: a header in a bearing wall has to land on a strip that actually carries
    # it down to the footing — foundation.py casts one strip per bearing wall, named the
    # same as the wall here, and moving a bearing wall without moving its strip is a
    # foundation defect, not a framing one, so this only checks the names line up.
    from src.foundation import B1, B2
    strip_names = {nm for b in (B1, B2) for x0, y0, x1, y1, nm in b.strips}
    for h in HEADERS:
        if h.wall in ('UNITS 2 AND 3 BEARING WALL', 'UNITS 4 AND 5 BEARING WALL'):
            if h.wall not in strip_names:
                v.append('%s: bearing wall %s has no strip in foundation.py' % (h.tag, h.wall))
    return v


def check_framing():
    for fl in FLOORS:
        for b in fl.bays:
            print("FRAMING %-10s %-30s %s I-JOISTS AT %s O.C., %s CLEAR SPAN, %s TO %s"
                  % (fl.name, b.name, fmt(b.joist), fmt(JOIST_OC), fmt(bay_span(b)), b.bearing[0], b.bearing[1]))
        for w in fl.wells:
            print("FRAMING %-10s well %s x %s, header on the stair wall at x %s" % (fl.name, fmt(w.x1-w.x0), fmt(w.y1-w.y0), fmt(w.header_x0)))
    for h in HEADERS:
        print("FRAMING %-4s %-10s L%d %-28s %-45s %s: %s, %d JACK, %d FULL-HEIGHT — %s"
              % (h.tag, h.building, h.level, h.wall, h.load_case, fmt(h.width), h.size, h.jacks, h.full_height_studs, h.row))
    print("FRAMING loads: live %s; dead %s; guards %d lb concentrated; deflection %s; ground snow %d psf"
          % (", ".join("%s %d psf" % l for l in LIVE_LOADS), ", ".join("%s %d psf" % d for d in DEAD_LOADS), GUARD_LOAD, DEFLECTION, GROUND_SNOW))
    _i = lambda v: inches(v)[2:] if inches(v).startswith('0-') else inches(v)
    print("FRAMING F1 %s: %s I-JOISTS AT %s O.C., %s FLANGES, %s MINERAL WOOL AT %g PCF, RC-1 AT %s O.C., %d LAYER %s %s"
          % (levels.F1_LISTING, _i(F1_JOIST), _i(JOIST_OC), _i(levels.F1_FLANGE_W), _i(levels.F1_INSUL_T),
             levels.F1_INSUL_PCF, _i(levels.F1_CHANNEL_OC), levels.F1_LAYERS, _i(levels.F1_LAYER), levels.F1_BOARD))
    bad = framing_violations() + f1_listing_violations()
    assert not bad, "framing:\n  " + "\n  ".join(bad)


# ---------------- headers ----------------
# RCO Tables 602.7(1), (2) and 602.7.5 are arkitect/codes/ohio/rco/headers.py: one transcription, one pin.
from arkitect.codes.ohio.rco.headers import header_for, full_height_studs


Header = namedtuple('Header', 'tag building level wall load_case width size jacks full_height_studs row openings unit room table_size',
                    defaults=(None, None))
# room: the height between the opening's head and the underside of the double top plate — what a
# header has to fit in; table_size: the table's header, where it did not fit and an LVL stands in
# openings: the (x, y, ln, o) raw openings this condition covers, in the coordinates of
# the plan that draws them — Level 1's are tagged on the framing plan; unit: which
# unit's wall it is, for the coordinate system of those openings.

# What each wall carries, by storey. The trusses bear on the side walls of both buildings
# (A-202); the front and rear walls of Building 1 carry nothing; Building 2's courtyard
# and rear walls carry its centre-bearing floor at Level 1 and nothing at Level 2; the
# interior bearing walls one floor at Level 1, and the walls above them are partitions.
LOAD_CASE = {
    ('BUILDING 1', 'UNIT 1', 'SIDE', 1): 'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR',
    ('BUILDING 1', 'UNIT 1', 'SIDE', 2): 'ROOF AND CEILING',
    ('BUILDING 1', 'UNITS 2 / 3', 'SIDE', 1): 'ROOF, CEILING AND ONE CENTER-BEARING FLOOR',
    ('BUILDING 1', 'UNITS 2 / 3', 'SIDE', 2): 'ROOF AND CEILING',
    ('BUILDING 1', 'ANY', 'END', 1): 'NON-BEARING', ('BUILDING 1', 'ANY', 'END', 2): 'NON-BEARING',
    ('BUILDING 1', 'UNITS 2 / 3', 'BEARING', 1): 'ONE FLOOR ONLY', ('BUILDING 1', 'UNITS 2 / 3', 'BEARING', 2): 'NON-BEARING',
    ('BUILDING 2', 'ANY', 'SIDE', 1): 'ROOF AND CEILING', ('BUILDING 2', 'ANY', 'SIDE', 2): 'ROOF AND CEILING',
    ('BUILDING 2', 'ANY', 'END', 1): 'ROOF, CEILING AND ONE CENTER-BEARING FLOOR', ('BUILDING 2', 'ANY', 'END', 2): 'NON-BEARING',
    ('BUILDING 2', 'ANY', 'BEARING', 1): 'ONE FLOOR ONLY', ('BUILDING 2', 'ANY', 'BEARING', 2): 'NON-BEARING',
}


# ---------------- does the header FIT? ----------------
# A header stands between the opening's head and the double top plate. The window heads are at
# 8'-0" and a Level 1 plate is SUBFLOOR_TOP less its floor's depth, so that room is 6" under Unit
# 1's F2, 8-1/8" under F1 and 9" on Level 2 — and Table 602.7's answer for a loaded opening can be
# 9-1/4" or 11-1/4" deep. Found on 400 Oak on 2026-09-18 and here the same day: H1, H3, H15 and
# H21 had been scheduled deeper than the wall over their windows, with every oracle green, because
# each check measured the table and none measured the room. The measuring is arkitect/lib/model/fit.py's.
# Where the table's header does not fit the schedule takes an LVL of a 2x6's depth (the designer, on Oak:
# "do lvl and add the checks so we don't miss this again").
TOP_PLATES = fit.TOP_PLATES
NONBEARING_HEADER = fit.FLAT_2X4     # RCO 602.7.4: a single flat 2x4
LVL = '2-PLY LVL'                    # S-102's HEADER column is narrow here; note 4a has the section
LVL_PLIES, LVL_PLY, LVL_DEPTH = 2, IN(1.75), IN(5.5)
LVL_FB, LVL_FV, LVL_E = 2600.0, 285.0, 2.0e6        # 2.0E LVL, allowable stresses, psi
LVL_DEFLECTION = 360                 # total load, L over this
WALL_PSF = 10.0                      # a framed, sheathed and sided wall, per SF of its face
BEARING_EACH_END = IN(1.5)
DOOR_HEAD = 6.0+8.0/12.0             # every door and cased opening, A-602
_HEAD = {}                           # (building, level, x, y, o) -> the opening's head above its floor


def header_depth(size):
    return LVL_DEPTH if size == LVL else fit.lumber_depth(size)


def _key(building, level, raw):
    # no unit in the key: a condition gathers one wall's openings across the units that share it
    return (building, level, round(raw[0], 4), round(raw[1], 4), raw[3])


def header_room(building, unit, level, openings):
    """The least height between an opening's head and the underside of the double top plate.
       Unit 1's Level 1 walls stop under F2's plate, every other Level 1 wall under F1's."""
    if level == 2: top = levels.ROOF_PLATE-levels.FF2
    else: top = (levels.F2_PLATE if unit == 'UNIT 1' else levels.F1_PLATE)-levels.FF1
    return fit.header_room(top, [_HEAD[_key(building, level, raw)] for raw in openings], TOP_PLATES)


def _line_load(case, building):
    """Pounds per foot on a header, from this set's own loads: what the LVL is checked against.
       A PLAUSIBILITY check — the LVL maker's header table sizes it, S-102 note 4a."""
    from src.roof import EAVE_OVERHANG
    W = B1_W if building == 'BUILDING 1' else B2_W
    live = max(v for _n, v in LIVE_LOADS); dead = max(v for _n, v in DEAD_LOADS)
    roof = (max(GROUND_SNOW, 20)+10+10)*(W/2.0+EAVE_OVERHANG)
    wall = WALL_PSF*9.0
    return {'ROOF AND CEILING': roof+wall,
            'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR': roof+wall+(live+dead)*W/2.0,
            'ROOF, CEILING AND ONE CENTER-BEARING FLOOR': roof+wall+(live+dead)*W/4.0,
            'ONE FLOOR ONLY': (live+dead)*W/2.0}[case]


def lvl_violations(case, building, width):
    return fit.lvl_violations(_line_load(case, building), width, LVL_PLIES*LVL_PLY, LVL_DEPTH,
                              LVL_FB, LVL_FV, LVL_E, LVL_DEFLECTION, BEARING_EACH_END)


def _make(tag, building, level, wall, unit, kind, width, openings):
    case = LOAD_CASE[(building, unit, kind, level)] if (building, unit, kind, level) in LOAD_CASE else LOAD_CASE[(building, 'ANY', kind, level)]
    room = header_room(building, unit, level, openings)
    if case == 'NON-BEARING':
        return Header(tag, building, level, wall, case, width, 'PER 602.7.4', 0, 0, '602.7.4', openings, unit, room)
    size, jacks, row, _fs = header_for(case, width)
    fh = full_height_studs(width) if kind != 'BEARING' else 0
    table_size = None
    if not fit.header_fit(header_depth(size), room):   # the table's header does not fit over this opening
        table_size, size, row = size, LVL, "LVL MANUFACTURER'S TABLE, %s" % case
    return Header(tag, building, level, wall, case, width, size, jacks, fh, row, openings, unit, room, table_size)


def _openings():
    """(building, level, wall, unit, kind, width, sort key, raw opening) for every window
       and door in a wall, read from the opening lists the plans draw."""
    from src.building1 import L1_DOORS, L1_WINS, L2_DOORS, L2_WINS, PLAN_L1, windows, ENTRY_LEFT, ENTRY_WIDTH
    from src.building2 import B2doors, B2op, b2_wins
    out = []
    # Building 1, Units 2/3 (reflected model feet: x 25.5 is Sage, 0.5 the parcel, y 47.5 the rear, x 11.5 the bearing wall)
    for level, wins in ((1, L1_WINS), (2, L2_WINS)):
        for x, y, ln, o, mark in wins:
            _HEAD[_key('BUILDING 1', level, (x, y, ln, o))] = WIN_HEAD[mark]
            wall, kind = _b1_u23_wall(x, y, o)
            out.append(('BUILDING 1', level, wall, 'UNITS 2 / 3', kind, ln, (level, 1, wall, x, y), (x, y, ln, o)))
    for level, doors in ((1, L1_DOORS), (2, L2_DOORS)):
        for d in doors:
            x, y, ln, o = d[:4]
            # exterior doors and doors in the bearing wall are scheduled; every other
            # interior door is skipped before the wall classifier sees it — it raises
            # on a horizontal interior door and would otherwise misfile the mechanical-
            # closet pair (also horizontal, at the rear's y) as the rear wall. The
            # bearing-wall bound comes from U23_BEARING_WALL itself (_bw, final sheet
            # feet): a door's x is reflected-model feet, pre-regrid, so it is carried
            # through the same PLAN_L1.x regrid and B1_W - x flip U23_BEARING_WALL was
            # built with before the two are compared.
            on_bearing = o == 'v' and _bw[0]-_BW_TOL <= B1_W-PLAN_L1.x(x, y) <= _bw[2]+_BW_TOL
            if not ('ext' in d[5:] or on_bearing):
                continue
            wall, kind = _b1_u23_wall(x, y, o)
            _HEAD[_key('BUILDING 1', level, (x, y, ln, o))] = DOOR_HEAD
            out.append(('BUILDING 1', level, wall, 'UNITS 2 / 3', kind, ln, (level, 1, wall, x, y), (x, y, ln, o)))
    # Building 1, Unit 1 (page feet: x 0.3 Sage, 25.7 parcel, y 0.23 S Elm)
    for level in (1, 2):
        for x, y, ln, o, mark in windows(level):
            _HEAD[_key('BUILDING 1', level, (x, y, ln, o))] = WIN_HEAD[mark]
            wall, kind = ('SAGE WALL', 'SIDE') if o == 'v' and x < 13 else ('ADJACENT-PARCEL WALL', 'SIDE') if o == 'v' else ('S ELM WALL', 'END')
            out.append(('BUILDING 1', level, wall, 'UNIT 1', kind, ln, (level, 0, wall, x, y), (x, y, ln, o)))
    _HEAD[_key('BUILDING 1', 1, (ENTRY_LEFT, site_y(0), ENTRY_WIDTH, 'h'))] = DOOR_HEAD
    out.append(('BUILDING 1', 1, 'S ELM WALL', 'UNIT 1', 'END', ENTRY_WIDTH, (1, 0, 'S ELM WALL', 0.0, 0.0),
                (ENTRY_LEFT, site_y(0), ENTRY_WIDTH, 'h')))
    # Building 2 (model feet: x 25.5 Sage, 0.5 parcel, y 0.5 courtyard, 27.5 rear, y 15.2 the bearing wall)
    for level in (1, 2):
        for x, y, ln, o, mark in b2_wins(level):
            _HEAD[_key('BUILDING 2', level, (x, y, ln, o))] = WIN_HEAD[mark]
            wall, kind = _b2_wall(x, y, o)
            out.append(('BUILDING 2', level, wall, 'ANY', kind, ln, (level, 2, wall, x, y), (x, y, ln, o)))
        # Every door and every bearing-wall / D-5 opening, not just the entry and the
        # hall opening: an opening on an exterior wall or the interior bearing wall is
        # scheduled, everything else is an ordinary partition and is skipped — today
        # that is the two bedroom doors, the bath door, the D-4A louvered pair and the
        # two D-5 bypass fronts.
        for d in list(B2doors) + list(B2op):
            x, y, ln, o = d[:4]
            if not _b2_scheduled(x, y, o):
                continue
            wall, kind = _b2_wall(x, y, o)
            _HEAD[_key('BUILDING 2', level, (x, y, ln, o))] = DOOR_HEAD
            key_wall = kind if kind == 'BEARING' else wall
            out.append(('BUILDING 2', level, wall, 'ANY', kind, ln, (level, 2, key_wall, x, y), (x, y, ln, o)))
    return sorted(out, key=lambda r: (r[0], r[6]))


def _b1_u23_wall(x, y, o):
    if o == 'v' and x > 20: return 'SAGE WALL', 'SIDE'
    if o == 'v' and x < 1: return 'ADJACENT-PARCEL WALL', 'SIDE'
    if o == 'v': return 'UNITS 2 AND 3 BEARING WALL', 'BEARING'
    if y > 40: return 'REAR WALL', 'END'
    raise ValueError('an opening on no wall: %r' % ((x, y, o),))


def _b2_wall(x, y, o):
    if o == 'v' and x > 20: return 'SAGE WALL', 'SIDE'
    if o == 'v': return 'ADJACENT-PARCEL WALL', 'SIDE'
    if y < 1: return 'COURTYARD WALL', 'END'
    if y > 20: return 'REAR WALL', 'END'
    return 'UNITS 4 AND 5 BEARING WALL', 'BEARING'


def _b2_scheduled(x, y, o):
    """Is this Building 2 door or bearing-wall opening one the schedule covers? An
       opening on an exterior wall (a 'v' opening near the Sage or parcel face, an
       'h' one near the courtyard or rear face) or on the interior bearing wall (an 'h'
       opening at Y_BEAR) is; an ordinary partition opening is not."""
    if o == 'v': return abs(x-0.5) < 0.6 or abs(x-25.5) < 0.6
    if o == 'h': return abs(y-0.5) < 0.6 or abs(y-27.5) < 0.6 or abs(y-Y_BEAR) < 0.6
    return False


def _load_case(building, unit, kind, level):
    key = (building, unit, kind, level)
    return LOAD_CASE[key] if key in LOAD_CASE else LOAD_CASE[(building, 'ANY', kind, level)]


def _conditions():
    """The distinct (building, level, wall, load case, width) among the openings, each
       with the openings it covers, in the order the openings sort — every condition,
       NON-BEARING included, keyed by width: a 3'-0" and a 5'-0" opening in the same
       non-bearing wall are two rows, each scheduled 'PER 602.7.4' independently.

       Building 1's Sage and Adjacent-Parcel walls run the full depth of the building
       — Unit 1's portion and Units 2/3's are the same wall assembly — so where both
       units land on the same wall, level and width under the SAME load case (Level 2,
       roof and ceiling only — Level 1's differs, clear-span for Unit 1 against
       center-bearing for Units 2/3), the openings share one condition and one header
       tag. unit is kept from the first opening seen; it is read only for a Level 1 tag
       position (see header_for's callers on S-102, once that sheet exists), where no
       condition spans two units, so which of the two units' openings happens to be
       first never matters — and it does not itself gate the grouping."""
    out = []; seen = {}; units = {}
    for b, lv, wall, unit, kind, w, key, raw in _openings():
        case = _load_case(b, unit, kind, lv)
        k = (b, lv, wall, case, round(w, 3))
        if k not in seen:
            seen[k] = len(out); out.append([b, lv, wall, unit, kind, w, []]); units[k] = set()
        out[seen[k]][6].append(raw)
        units[k].add(unit)
    # header_positions reads h.unit — the first opening's — to pick a Level 1 tag's
    # coordinate transform; that is only safe if every opening in a Level 1 condition
    # is in fact the same unit, which this asserts rather than assumes.
    for k, u in units.items():
        if k[1] == 1:
            assert len(u) == 1, '%s L%d %s: a Level 1 condition spans units %s' % (k[0], k[1], k[2], sorted(u))
    return out


HEADERS = [_make('H%d' % (i+1), b, lv, wall, unit, kind, w, opens) for i, (b, lv, wall, unit, kind, w, opens) in enumerate(_conditions())]


def header_violations(headers=None):
    """A scheduled header is the table's, or an LVL where the table's does not fit — and whichever it
       is FITS between its opening's head and the double top plate."""
    v = []
    for h in (HEADERS if headers is None else headers):
        room = header_room(h.building, h.unit, h.level, h.openings)
        if h.load_case == 'NON-BEARING':                    # 602.7.4: a flat 2x4 still has to fit
            if room < NONBEARING_HEADER-1e-9:
                v.append('%s, %s L%d %s: %s over the opening, under the %s a 602.7.4 header takes' % (h.tag, h.building, h.level, h.wall, inches(room), inches(NONBEARING_HEADER)))
            continue
        if not fit.header_fit(header_depth(h.size), room):
            v.append('%s, %s L%d %s: a %s header is %s deep and only %s stands between the opening\'s head and the double top plate'
                     % (h.tag, h.building, h.level, h.wall, h.size, inches(header_depth(h.size)), inches(room)))
        size, jacks, row, _fs = header_for(h.load_case, h.width)
        if h.size == LVL:
            if fit.header_fit(header_depth(size), room):
                v.append('%s: an LVL scheduled where the table\'s %s fits' % (h.tag, size))
            v += ['%s: the LVL under %s at %s: %s' % (h.tag, h.load_case, fmt(h.width), t)
                  for t in lvl_violations(h.load_case, h.building, h.width)]
        elif size != h.size:
            v.append('%s: %s scheduled, table says %s' % (h.tag, h.size, size))
    return v


def header_positions(building):
    """[(tag, x, y)] in PAGE feet: every Level 1 opening of a building, tagged with its
       condition, at the opening's center on its wall, through the same regrid and
       mirror as the plan that draws it. Several openings share a tag."""
    from src.building1 import PLAN_L1
    from src.building2 import PLAN_B2
    out = []
    for h in HEADERS:
        if h.building != building or h.level != 1: continue
        for x, y, ln, o in h.openings:
            cx, cy = (x+ln/2.0, y) if o == 'h' else (x, y+ln/2.0)
            if h.unit == 'UNIT 1':                           px, py = cx, cy                                  # page feet already
            elif h.building == 'BUILDING 1':                 px, py = B1_W-PLAN_L1.x(cx, cy), PLAN_L1.y(cy)  # reflected model feet
            else:                                            px, py = B2_W-PLAN_B2.x(cx, cy), PLAN_B2.y(cy)
            out.append((h.tag, px, py))
    return out

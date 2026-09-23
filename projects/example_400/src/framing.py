"""The floor framing of both buildings, derived: what S-102 draws.

Everything is in FINAL SHEET feet, the system S-101 uses: x from the plans' left edge
(the 396 Oak side, north), y from the front face. The bays are the joist bays S-102
prints and S-101 casts strips under; the house's well is the stair's own constants;
nothing is typed that another sheet prints. The floor trusses themselves are the
truss manufacturer's, designed to the loads stated here.
"""
from collections import namedtuple
from arkitect.lib.units import IN, fmt, inches
from arkitect.lib.model import fit
from arkitect.lib.model.regrid import EXT_STUD, PARTITION
from src import levels
from src.building1 import B1_D, B1_W, PLAN_B1_L2, STAIR_WALL, Y_TOP_RISER, Y_WELL
from src.building2 import B2_D, B2_W, U45_BEARING_WALL, Y_BEAR
from src.openings import WIN_HEAD
from src.sitework import DOOR_H
from arkitect.codes.ohio.rco.bracing import PORTAL_HEADER, portal_header_size
from arkitect.codes.ohio.rco.floor_checks import floor_violations, bay_span

# ---------------- basis ----------------
# Floor trusses at 24" o.c. (the designer, 2026-09-19, a cost saving: a third fewer trusses). UL L528
# allows 24" and S-102 had carried it as the manufacturer's alternate since the trusses went in.
# The spacing sets MAX_SPAN below, and it is why F2's ceiling board is 5/8" (levels.F2_GYPSUM).
JOIST_OC = IN(24)
TRUSS_OC = IN(24)                   # the roof trusses, bearing on the side walls
F1_JOIST = levels.F1_JOIST          # 14" open-web trusses, Building 2's rated floor
F2_JOIST = levels.F2_JOIST          # 14" open-web trusses, the house's floor
FRAMING = 'OPEN-WEB FLOOR TRUSSES'  # what the sheets call the floor framing
SUBFLOOR = levels.SUBFLOOR          # 3/4" T&G, glued and screwed
# By depth AT JOIST_OC: a bay past this fails. Not a sizing -- the plant's sealed design is.
# Alpine Engineered Products' floor truss span table, 4x2 chords, 40 psf live / 55 psf total,
# L/480, 24" o.c.: 14" 19'-9", 16" 21'-7". At 16" o.c. they were 22'-7" and 24'-11".
MAX_SPAN = {IN(14.0): 19.75, IN(16.0): 21.583}

# RCO Table R301.5 live loads and RCO R301.7 deflection: the joist and truss submittals
# are designed to these. Dead loads are this set's assemblies (A-601).
LIVE_LOADS = [("SLEEPING AREAS", 30), ("ALL OTHER FLOOR AREAS", 40), ("STAIRS", 40)]
GUARD_LOAD = 200                    # lb, concentrated, any direction
DEAD_LOADS = [("F1, THE RATED CEILING INCLUDED", 15), ("F2", 12)]

# F1's listing, UL Design L528 (levels.py has the build-up). What the framing answers to:
# trusses at 24" o.c. at most and 12" deep at least; channels at 16" o.c. at most; ONE 5/8"
# Type C layer; NO INSULATION in the cavity (the listing has no insulation item -- pipes and
# line sets still run through the open webs, A-601 F1 item B). Two things the design does NOT
# give this floor, which is why Unit 2's bath fan hangs in a soffit below the membrane:
#   * a ceiling damper (Items 9, 9A...) needs 18" trusses AND is "not for use with flooring
#     system 1", the plain subfloor — it would force a gypsum topping over the whole floor;
#   * no item lists a recessed luminaire.
F1_MAX_JOIST_OC = IN(24)
F1_MIN_TRUSS_DEPTH = IN(12)
F1_MAX_CHANNEL_OC = IN(16)
F1_MIN_CHORD_W = IN(3.5)        # nominal 2x4
F1_CAVITY_INSULATION = None     # the base design has none; A-601 item B
BATH_CEILING_MIN = 6.0+8.0/12.0  # RCO 305.1, bathrooms


def f1_listing_violations(joist_oc=None, depth=None, chord_w=None, layers=None, layer=None,
                          board=None, channel_oc=None, insulation=None, ceiling_devices=None):
    """Every way the F1 framing and build-up leave UL Design L528. Arguments override the
       model, so a test can ask what a change would do. `ceiling_devices` are the kinds of
       electrical device in Unit 2's ceiling."""
    joist_oc = JOIST_OC if joist_oc is None else joist_oc
    depth = F1_JOIST if depth is None else depth
    chord_w = levels.F1_CHORD_W if chord_w is None else chord_w
    layers = levels.F1_LAYERS if layers is None else layers
    layer = levels.F1_LAYER if layer is None else layer
    board = levels.F1_BOARD if board is None else board
    channel_oc = levels.F1_CHANNEL_OC if channel_oc is None else channel_oc
    insulation = F1_CAVITY_INSULATION if insulation is None else insulation
    if ceiling_devices is None:
        from src import electrical as E
        from arkitect.codes.nec import dwelling as nec_dwelling
        from src.building2 import U2_SOFFIT_ROOMS
        # what hangs in the bath's soffit is below the membrane, not in it
        ceiling_devices = [d.kind for d in E.LEVEL_U2.devices
                           if d.mount == 'c' and nec_dwelling._room_at((d.x, d.y), E.LEVEL_U2) not in U2_SOFFIT_ROOMS]
    i = lambda v: '%g"' % round(v*12, 4)
    v = []
    if joist_oc > F1_MAX_JOIST_OC+1e-9:
        v.append('F1 trusses at %s o.c. exceed the %s of %s' % (i(joist_oc), i(F1_MAX_JOIST_OC), levels.F1_LISTING))
    if depth < F1_MIN_TRUSS_DEPTH-1e-9:
        v.append('F1 trusses %s deep are under the %s of %s' % (i(depth), i(F1_MIN_TRUSS_DEPTH), levels.F1_LISTING))
    if chord_w < F1_MIN_CHORD_W-1e-9:
        v.append('F1 truss chords %s are under the nominal 2x4 (%s) %s tests' % (i(chord_w), i(F1_MIN_CHORD_W), levels.F1_LISTING))
    if layers != 1 or abs(layer-IN(.625)) > 1e-9:
        v.append('F1 membrane %d x %s is not the one 5/8" layer of %s' % (layers, i(layer), levels.F1_LISTING))
    if board != 'TYPE C':
        v.append('F1 board %s is not a Type C %s lists; Type X is not an alternate' % (board, levels.F1_LISTING))
    if channel_oc > F1_MAX_CHANNEL_OC+1e-9:
        v.append('F1 channels at %s o.c. exceed the %s of %s' % (i(channel_oc), i(F1_MAX_CHANNEL_OC), levels.F1_LISTING))
    if insulation:
        v.append('F1 cavity insulation %r: the base design of %s has none' % (insulation, levels.F1_LISTING))
    from src.building2 import U2_SOFFIT_DROP
    soffit = levels.F1_CEILING-U2_SOFFIT_DROP-levels.FF1
    if soffit < BATH_CEILING_MIN-1e-9:
        v.append("Unit 2's bath soffit leaves %s, under RCO 305.1's %s" % (fmt(soffit), fmt(BATH_CEILING_MIN)))
    for k in ceiling_devices:
        if k == 'rec':
            v.append("a recessed luminaire in Unit 2's ceiling: %s lists none" % levels.F1_LISTING)
        if k in ('fan', 'fanc'):
            v.append("a fan in Unit 2's rated ceiling: %s gives a ceiling damper only with 18\" trusses and a floor topping; hang it in the bath's soffit" % levels.F1_LISTING)
    return v
DEFLECTION = "L/480 LIVE LOAD"
from src.criteria import GROUND_SNOW   # RCO Table 301.2(1); S-102 and S-103 print it

# ---------------- the floors ----------------
Bay = namedtuple('Bay', 'name x0 y0 x1 y1 run joist bearing')     # run 'h': joists run in x
Well = namedtuple('Well', 'x0 y0 x1 y1 header_x0 header_x1')
Floor = namedtuple('Floor', 'name W D bays wells rated_rims outline_sf', defaults=(None,))
# rated_rims: (x0, y0, x1, y1, label) — a floor edge along a wall PARALLEL to the joists
# that carries a wall above; the rim board or full-depth blocking there is rated by the
# manufacturer for that wall's load (Building 2's side walls carry its roof).
# outline_sf: the floor's own Level 2 plate outline, SF, for the tile check below to
# compare against — None falls back to the exterior-stud rectangle from W and D.

# The house: one bay, side wall to side wall, and the well over the flight at the north
# wall. The stair wall stands under the well's long side and carries its header; the tail
# joists hang from it. The well runs from the top riser to the guard wall at its far end.
B1_FLOOR = Floor("BUILDING 1", B1_W, B1_D,
    bays=[Bay('UNIT 1 F2', EXT_STUD, EXT_STUD, B1_W-EXT_STUD, B1_D-EXT_STUD, 'h', F2_JOIST,
              ('NORTH WALL', 'SOUTH WALL'))],
    wells=[Well(EXT_STUD, PLAN_B1_L2.y(Y_TOP_RISER), STAIR_WALL[0], PLAN_B1_L2.y(Y_WELL-PARTITION),
                STAIR_WALL[0], STAIR_WALL[2])],
    rated_rims=[])     # the front and rear walls, parallel to the joists, carry gables only

# Building 2: two F1 bays, courtyard to rear, meeting on the bearing wall; the side walls,
# parallel to the joists, carry the roof.
_uw = U45_BEARING_WALL
_B2_OUTLINE_SF = (B2_W-2*EXT_STUD)*(B2_D-2*EXT_STUD) - (B2_W-2*EXT_STUD)*(_uw[3]-_uw[1])
B2_FLOOR = Floor("BUILDING 2", B2_W, B2_D,
    bays=[Bay('UNITS 2 / 3 F1, COURTYARD BAY', EXT_STUD, EXT_STUD, B2_W-EXT_STUD, _uw[1], 'v', F1_JOIST,
              ('COURTYARD WALL', 'BEARING WALL')),
          Bay('UNITS 2 / 3 F1, REAR BAY', EXT_STUD, _uw[3], B2_W-EXT_STUD, B2_D-EXT_STUD, 'v', F1_JOIST,
              ('BEARING WALL', 'REAR WALL'))],
    wells=[],
    rated_rims=[(EXT_STUD, EXT_STUD, EXT_STUD, B2_D-EXT_STUD, 'END TRUSS DESIGNED FOR THE ROOF-BEARING WALL ABOVE'),
                (B2_W-EXT_STUD, EXT_STUD, B2_W-EXT_STUD, B2_D-EXT_STUD, 'END TRUSS DESIGNED FOR THE ROOF-BEARING WALL ABOVE')],
    outline_sf=_B2_OUTLINE_SF)

FLOORS = (B1_FLOOR, B2_FLOOR)




# ---------------- the checks ----------------
def _bearing_lines(floor):
    """The lines a joist may end on: the exterior stud faces, and the strips S-101 casts."""
    from src.foundation import B1, B2
    b = B1 if floor.name == "BUILDING 1" else B2
    lines = [(EXT_STUD, 0.0, EXT_STUD, floor.D, 'NORTH WALL'), (floor.W-EXT_STUD, 0.0, floor.W-EXT_STUD, floor.D, 'SOUTH WALL'),
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
        if h.wall in (B1_STAIR_WALL, B2_BEARING_WALL):
            if h.wall not in strip_names:
                v.append('%s: bearing wall %s has no strip in foundation.py' % (h.tag, h.wall))
    return v


def check_framing():
    for fl in FLOORS:
        for b in fl.bays:
            print("FRAMING %-10s %-30s %s FLOOR TRUSSES AT %s O.C., %s CLEAR SPAN, %s TO %s"
                  % (fl.name, b.name, fmt(b.joist), fmt(JOIST_OC), fmt(bay_span(b)), b.bearing[0], b.bearing[1]))
        for w in fl.wells:
            print("FRAMING %-10s well %s x %s, header on the stair wall at x %s" % (fl.name, fmt(w.x1-w.x0), fmt(w.y1-w.y0), fmt(w.header_x0)))
    for h in HEADERS:
        print("FRAMING %-4s %-10s L%d %-28s %-45s %s: %s, %d JACK, %d FULL-HEIGHT — %s"
              % (h.tag, h.building, h.level, h.wall, h.load_case, fmt(h.width), h.size, h.jacks, h.full_height_studs, h.row))
    print("FRAMING loads: live %s; dead %s; guards %d lb concentrated; deflection %s; ground snow %d psf"
          % (", ".join("%s %d psf" % l for l in LIVE_LOADS), ", ".join("%s %d psf" % d for d in DEAD_LOADS), GUARD_LOAD, DEFLECTION, GROUND_SNOW))
    _i = lambda v: inches(v)[2:] if inches(v).startswith('0-') else inches(v)
    print("FRAMING F1 %s: %s OPEN-WEB TRUSSES AT %s O.C., %s CHORDS, NO CAVITY INSULATION, CHANNELS AT %s O.C., %d LAYER %s %s"
          % (levels.F1_LISTING, _i(F1_JOIST), _i(JOIST_OC), _i(levels.F1_CHORD_W),
             _i(levels.F1_CHANNEL_OC), levels.F1_LAYERS, _i(levels.F1_LAYER), levels.F1_BOARD))
    bad = framing_violations() + f1_listing_violations()
    assert not bad, "framing:\n  " + "\n  ".join(bad)


# ---------------- headers ----------------
# RCO Tables 602.7(1), (2) and 602.7.5 are arkitect/codes/ohio/rco/headers.py: one transcription, one pin.
from arkitect.codes.ohio.rco.headers import header_for, full_height_studs


Header = namedtuple('Header', 'tag building level wall load_case width size jacks full_height_studs row openings unit room table_size',
                    defaults=(None, None))
# room: the height between the opening's head and the underside of the double top plate — what a
# header has to fit in; table_size: the table's header, where it did not fit and an LVL stands in
# openings: the (x, y, ln, o) raw openings this condition covers, in the model feet of the
# plan that draws them — Level 1's are tagged on the framing plan; unit: whose wall it is.

# What each wall carries, by story. The roof trusses bear on the side walls of both
# buildings. The house's Level 2 floor clear-spans side wall to side wall; its front and
# rear walls carry gables only; the stair wall carries the well header at Level 1.
# Building 2's courtyard and rear walls carry its center-bearing floor at Level 1 and
# nothing at Level 2; its bearing wall carries one floor at Level 1, and the wall above
# it is a partition.
LOAD_CASE = {
    ('BUILDING 1', 'UNIT 1', 'SIDE', 1): 'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR',
    ('BUILDING 1', 'UNIT 1', 'SIDE', 2): 'ROOF AND CEILING',
    ('BUILDING 1', 'UNIT 1', 'END', 1): 'NON-BEARING', ('BUILDING 1', 'UNIT 1', 'END', 2): 'NON-BEARING',
    ('BUILDING 1', 'UNIT 1', 'BEARING', 1): 'ONE FLOOR ONLY', ('BUILDING 1', 'UNIT 1', 'BEARING', 2): 'NON-BEARING',
    ('BUILDING 2', 'ANY', 'SIDE', 1): 'ROOF AND CEILING', ('BUILDING 2', 'ANY', 'SIDE', 2): 'ROOF AND CEILING',
    ('BUILDING 2', 'ANY', 'END', 1): 'ROOF, CEILING AND ONE CENTER-BEARING FLOOR', ('BUILDING 2', 'ANY', 'END', 2): 'NON-BEARING',
    ('BUILDING 2', 'ANY', 'BEARING', 1): 'ONE FLOOR ONLY', ('BUILDING 2', 'ANY', 'BEARING', 2): 'NON-BEARING',
}
B1_STAIR_WALL = 'UNIT 1 STAIR WALL'             # the names foundation.py gives their strips
B2_BEARING_WALL = 'UNITS 2 AND 3 BEARING WALL'


# ---------------- does the header FIT? ----------------
# A header stands between the opening's head and the double top plate. The window heads are at
# 8'-0" and the Level 1 plate is SUBFLOOR_TOP less the floor's depth, so that room is 6" on Level 1
# and 9" on Level 2 — and Table 602.7's answer for a loaded 5'-0" opening is 9-1/4" or 11-1/4" deep.
# Found 2026-09-18 after three such headers had been scheduled for a day. Where the table's header
# does not fit, the schedule takes an LVL of the 2x6's depth instead, so every header in the set is
# ONE depth (the designer: "do lvl and add the checks so we don't miss this again").
# The measuring is arkitect/lib/model/fit.py's, shared with every project; what is this project's is the
# heads, the plates, the loads and the choice of an LVL.
TOP_PLATES = fit.TOP_PLATES          # the double top plate over every header
NONBEARING_HEADER = fit.FLAT_2X4     # RCO 602.7.4: a single flat 2x4
LUMBER_DEPTH = fit.LUMBER_DEPTH
LVL = 'LVL 2-PLY 5-1/2"'
LVL_PLIES, LVL_PLY, LVL_DEPTH = 2, IN(1.75), IN(5.5)
# 2.0E LVL, the grade every maker's header table starts at; allowable stresses, psi
LVL_FB, LVL_FV, LVL_E = 2600.0, 285.0, 2.0e6
LVL_DEFLECTION = 360                 # total load, L over this
WALL_PSF = 10.0                      # a framed, sheathed and sided wall, per SF of its face
BEARING_EACH_END = IN(1.5)           # the design span is the opening plus this at each end


def header_depth(size):
    if size == LVL: return LVL_DEPTH
    return fit.lumber_depth(size)


_HEAD = {}                           # (building, level, x, y, o) -> the opening's head above its floor, feet


def _key(building, level, raw):
    return (building, level, round(raw[0], 4), round(raw[1], 4), raw[3])


def header_room(building, level, openings):
    """The least height between an opening's head and the underside of the double top plate,
       among the openings a condition covers."""
    from src.levels import F1_PLATE, FF1, FF2, ROOF_PLATE
    top = (F1_PLATE-FF1) if level == 1 else (ROOF_PLATE-FF2)
    return fit.header_room(top, [_HEAD[_key(building, level, raw)] for raw in openings], TOP_PLATES)


def _line_load(case, building):
    """Pounds per foot on a header, from this set's own loads: what lvl_violations() checks the
       LVL against. A PLAUSIBILITY check — the LVL maker's header table sizes it, S-102 note 4a."""
    from src.criteria import GROUND_SNOW as snow
    from src.roof import EAVE_OVERHANG
    W = B1_W if building == 'BUILDING 1' else B2_W
    floor = B1_FLOOR if building == 'BUILDING 1' else B2_FLOOR
    live = max(v for _n, v in LIVE_LOADS); dead = max(v for _n, v in DEAD_LOADS)
    roof = (max(snow, 20)+10+10)*(W/2.0+EAVE_OVERHANG)          # live or snow, top and bottom chord dead
    wall = WALL_PSF*9.0
    spans = [bay_span(b) for b in floor.bays]
    return {'ROOF AND CEILING': roof+wall,
            'ROOF, CEILING AND ONE CLEAR-SPAN FLOOR': roof+wall+(live+dead)*W/2.0,
            'ROOF, CEILING AND ONE CENTER-BEARING FLOOR': roof+wall+(live+dead)*max(spans)/2.0,
            'ONE FLOOR ONLY': (live+dead)*sum(spans)/2.0}[case]


def lvl_violations(case, building, width):
    """Bending, shear and deflection of the scheduled LVL under _line_load()."""
    return fit.lvl_violations(_line_load(case, building), width, LVL_PLIES*LVL_PLY, LVL_DEPTH,
                              LVL_FB, LVL_FV, LVL_E, LVL_DEFLECTION, BEARING_EACH_END)


def _make(tag, building, level, wall, unit, kind, width, openings):
    case = _load_case(building, unit, kind, level)
    room = header_room(building, level, openings)
    if case == 'NON-BEARING':
        return Header(tag, building, level, wall, case, width, 'PER 602.7.4', 0, 0, '602.7.4', openings, unit, room)
    size, jacks, row, _fs = header_for(case, width)
    fh = full_height_studs(width) if kind != 'BEARING' else 0
    table_size = None
    if header_depth(size) > room+1e-9:              # the table's header does not fit over this opening
        table_size, size, row = size, LVL, "LVL MANUFACTURER'S TABLE, %s" % case
    if is_portal(building, level, wall, width) and header_depth(portal_header_size()) > header_depth(size):
        table_size, size, row = size, portal_header_size(), '602.10.6.4'
    return Header(tag, building, level, wall, case, width, size, jacks, fh, row, openings, unit, room, table_size)


def _merge(ops):
    """Openings side by side on one wall line — the leaves of a pair — as one opening."""
    out = []
    for x, y, ln, o in sorted(ops, key=lambda r: (r[3], r[1] if r[3] == 'h' else r[0], r[0] if r[3] == 'h' else r[1])):
        if out:
            px, py, pl, po = out[-1]
            if o == po == 'h' and abs(y-py) < 1e-6 and abs(px+pl-x) < 1e-6:
                out[-1] = (px, py, pl+ln, po); continue
            if o == po == 'v' and abs(x-px) < 1e-6 and abs(py+pl-y) < 1e-6:
                out[-1] = (px, py, pl+ln, po); continue
        out.append((x, y, ln, o))
    return out


def _openings():
    """(building, level, wall, unit, kind, width, sort key, raw opening) for every window
       and door in an exterior or bearing wall, read from the opening lists the plans
       draw. Interior doors in partitions are skipped."""
    from src.building1 import LEVEL as B1_LEVEL
    from src.building2 import B2doors, B2op, b2_wins
    out = []
    for level in (1, 2):
        m = B1_LEVEL[level]
        for w in m['wins']: _HEAD[_key('BUILDING 1', level, w)] = WIN_HEAD[w[4]]
        for d in m['doors']: _HEAD[_key('BUILDING 1', level, d)] = DOOR_H
        ops = [w[:4] for w in m['wins']]
        ops += [d[:4] for d in m['doors'] if 'ext' in d[5:] or _b1_on_stair_wall(d[0], d[3])]
        for x, y, ln, o in _merge(ops):
            wall, kind = _b1_wall(x, y, o)
            out.append(('BUILDING 1', level, wall, 'UNIT 1', kind, ln, (level, 1, wall, x, y), (x, y, ln, o)))
        for w in b2_wins(level): _HEAD[_key('BUILDING 2', level, w)] = WIN_HEAD[w[4]]
        for d in list(B2doors)+list(B2op): _HEAD[_key('BUILDING 2', level, d)] = DOOR_H
        ops = [w[:4] for w in b2_wins(level)]
        ops += [d[:4] for d in list(B2doors)+list(B2op) if _b2_scheduled(*d[:2], d[3])]
        for x, y, ln, o in _merge(ops):
            wall, kind = _b2_wall(x, y, o)
            out.append(('BUILDING 2', level, wall, 'ANY', kind, ln, (level, 2, wall, x, y), (x, y, ln, o)))
    return sorted(out, key=lambda r: (r[0], r[6]))


def _b1_on_stair_wall(x, o):
    from src.building1 import X_SW
    return o == 'v' and abs(x-(X_SW+PARTITION/2.0)) < 0.1


# Model feet, before the mirror: x 0.5 is the south wall, B1_W - 0.5 the north.
def _b1_wall(x, y, o):
    if o == 'v' and x < 1: return 'SOUTH WALL', 'SIDE'
    if o == 'v' and x > B1_W-1: return 'NORTH WALL', 'SIDE'
    if _b1_on_stair_wall(x, o): return B1_STAIR_WALL, 'BEARING'
    if o == 'h' and y < 1: return 'FRONT WALL', 'END'
    if o == 'h' and y > B1_D-1.5: return 'REAR WALL', 'END'
    raise ValueError('an opening on no wall: %r' % ((x, y, o),))


def _b2_wall(x, y, o):
    if o == 'v' and x < B2_W/2.0: return 'SOUTH WALL', 'SIDE'
    if o == 'v': return 'NORTH WALL', 'SIDE'
    if y < 1: return 'COURTYARD WALL', 'END'
    if y > B2_D-1.5: return 'REAR WALL', 'END'
    return B2_BEARING_WALL, 'BEARING'


def _b2_scheduled(x, y, o):
    """Is this Building 2 door or opening in an exterior wall or the bearing wall? An
       ordinary partition opening is not scheduled."""
    if o == 'v': return abs(x-0.5) < 0.6 or abs(x-(B2_W-0.5)) < 0.6
    if o == 'h': return abs(y-0.5) < 0.6 or abs(y-(B2_D-0.5)) < 0.6 or abs(y-(Y_BEAR+PARTITION/2.0)) < 0.6
    return False


def _load_case(building, unit, kind, level):
    key = (building, unit, kind, level)
    return LOAD_CASE[key] if key in LOAD_CASE else LOAD_CASE[(building, 'ANY', kind, level)]


def _conditions():
    """The distinct (building, level, wall, load case, width) among the openings, each
       with the openings it covers, in the order the openings sort — NON-BEARING
       included, keyed by width."""
    out = []; seen = {}
    for b, lv, wall, unit, kind, w, key, raw in _openings():
        case = _load_case(b, unit, kind, lv)
        k = (b, lv, wall, case, round(w, 3))
        if k not in seen:
            seen[k] = len(out); out.append([b, lv, wall, unit, kind, w, []])
        out[seen[k]][6].append(raw)
    return out


def _portal_keys():
    """(building, level, wall, width) of every opening a CS-PF portal frame stands beside.
       Figure 602.10.6.4 wants a header over the opening AND the portal leg, deeper than
       the gravity table's answer, so the schedule has to print the portal's or a framer
       reading S-102 alone builds the shallower one. Matched on the same four fields
       src/bracing.py's schedule_header() matches back on. Imported inside the function:
       src/bracing.py reads HEADERS the same way, lazily, and neither module may import
       the other while it is still being defined."""
    from src.bracing import LINES, portal_openings
    return {(ln.building, ln.level, ln.wall, round(o.b-o.a, 3))
            for ln in LINES for _p, o in portal_openings(ln) if o is not None}


_PORTALS = _portal_keys()


def is_portal(building, level, wall, width):
    """Does a CS-PF portal frame stand beside this condition's opening? S-104 note 9."""
    return (building, level, wall, round(width, 3)) in _PORTALS


HEADERS = [_make('H%d' % (i+1), b, lv, wall, unit, kind, w, opens) for i, (b, lv, wall, unit, kind, w, opens) in enumerate(_conditions())]


def header_violations(headers=None):
    """A scheduled header is the table's, or an LVL where the table's does not fit — and whichever it
       is FITS between its opening's head and the double top plate."""
    v = []
    for h in (HEADERS if headers is None else headers):
        room = header_room(h.building, h.level, h.openings)
        if h.load_case == 'NON-BEARING':                    # 602.7.4: a flat 2x4 still has to fit
            if room < NONBEARING_HEADER-1e-9:
                v.append('%s, %s L%d %s: %s over the opening, under the %s a 602.7.4 header takes' % (h.tag, h.building, h.level, h.wall, inches(room), inches(NONBEARING_HEADER)))
            continue
        if not fit.header_fit(header_depth(h.size), room):
            v.append('%s, %s L%d %s: a %s header is %s deep and only %s stands between the opening\'s head and the double top plate'
                     % (h.tag, h.building, h.level, h.wall, h.size, inches(header_depth(h.size)), inches(room)))
        size, jacks, row, _fs = header_for(h.load_case, h.width)
        if h.size == LVL:
            if header_depth(size) <= room+1e-9:
                v.append('%s: an LVL scheduled where the table\'s %s fits' % (h.tag, size))
            v += ['%s: the LVL under %s at %s: %s' % (h.tag, h.load_case, fmt(h.width), t)
                  for t in lvl_violations(h.load_case, h.building, h.width)]
        elif is_portal(h.building, h.level, h.wall, h.width):
            # 602.10.6.4 governs over the gravity table here, so the scheduled header is
            # deeper than Table 602.7 asks. It still may not fall short of EITHER.
            need = max(header_depth(size), PORTAL_HEADER[1])
            if header_depth(h.size) < need-1e-9:
                v.append('%s: %s scheduled over a CS-PF portal, under the %s the portal and the table need'
                         % (h.tag, h.size, inches(need)))
        elif size != h.size:
            v.append('%s: %s scheduled, table says %s' % (h.tag, h.size, size))
    return v


def header_positions(building):
    """[(tag, x, y)] in PAGE feet: every Level 1 opening of a building, tagged with its
       condition, at the opening's center on its wall, through the same regrid and
       mirror as the plan that draws it. Several openings share a tag."""
    from src.building1 import PLAN_B1_L1
    from src.building2 import PLAN_B2
    P, W = (PLAN_B1_L1, B1_W) if building == 'BUILDING 1' else (PLAN_B2, B2_W)
    out = []
    for h in HEADERS:
        if h.building != building or h.level != 1: continue
        for x, y, ln, o in h.openings:
            cx, cy = (x+ln/2.0, y) if o == 'h' else (x, y+ln/2.0)
            out.append((h.tag, W-P.x(cx, cy), P.y(cy)))
    return out

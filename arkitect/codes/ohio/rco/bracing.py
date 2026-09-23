"""RCO 602.10 wall bracing, transcribed: Tables 602.10.3(1) and (2), 602.10.5, 602.10.6.4,
602.3(3)'s sheathing nailing, the CS-PF portal frame's limits and the end conditions' figures.

One transcription for every project, from the 2019 Residential Code of Ohio text (2018 IRC
base), checked cell by cell against the 2018 IRC print and pinned by
arkitect/codes/verify/test_bracing_tables.py. It lived word for word in each project's bracing model
until 2026-09-18.

EVERY TABLE HERE IS ONE COLUMN: Vult <= 115 mph, Exposure B. The speed is not a lookup key,
it is the reason these rows are the rows — so a project calls require_column() with its own
design criteria before it reads a figure, and a lot in another column stops there.
"""
from collections import namedtuple
from arkitect.lib.units import IN, fmt

TABLE_VULT_MAX, TABLE_EXPOSURE = 115, 'B'


def require_column(vult, exposure, label):
    assert vult <= TABLE_VULT_MAX and exposure == TABLE_EXPOSURE, (
        "the bracing tables in this module are the Vult <= 115 mph, Exposure B columns of "
        "Table 602.10.3(1) and Table 602.10.6.4. Design criteria are now %s: transcribe the "
        "columns that apply before changing them." % label)


# ---------------- RCO R602.10, transcribed ----------------
# From the 2019 Residential Code of Ohio text (2018 IRC base), checked cell by cell
# against the 2018 IRC print, and pinned by arkitect/lib/verify/test_bracing.py. Seismic Design
# Category B (G-001): R602.10.3 item 1 sends both buildings to Table R602.10.3(1) with
# Table R602.10.3(2), so wind governs and there is no seismic length.
ROOF_ONLY, ROOF_AND_FLOOR = 'ROOF ONLY', 'ROOF + 1 FLOOR'
STORY = {2: ROOF_ONLY, 1: ROOF_AND_FLOOR}          # what each level's walls support
SDC = 'B'
METHOD = 'CS-WSP'

# Table R602.10.3(1), Vult <= 115 mph (Exposure B, 30 ft mean roof height, 10 ft wall
# height, two braced wall lines): the column for Methods CS-WSP, CS-G and CS-PF, feet of
# braced wall panel along each braced wall line by braced wall line spacing. Footnote a:
# linear interpolation permitted.
REQ_LENGTH = {
    ROOF_ONLY:      ((10, 2.0), (20, 3.5), (30, 4.5), (40, 6.0), (50, 7.5), (60, 9.0)),
    ROOF_AND_FLOOR: ((10, 3.5), (20, 6.5), (30, 9.0), (40, 11.5), (50, 14.0), (60, 17.0)),
}
MAX_SPACING = 60.0          # Table R602.10.1.3, wind bracing, 100 to < 140 mph

# Table R602.10.3(2). Footnote a, interpolation; footnote b, the factor is the product.
EXPOSURE = 'B'
F_EXPOSURE = {'B': 1.00, 'C': 1.30, 'D': 1.60}                          # item 1, two-story structure
F_EAVE_RIDGE = {ROOF_ONLY:      ((5, 0.70), (10, 1.00), (15, 1.30), (20, 1.60)),
                ROOF_AND_FLOOR: ((5, 0.85), (10, 1.00), (15, 1.15), (20, 1.30))}   # item 2; <= 5 ft reads 5
F_STORY_HEIGHT = ((8, 0.90), (9, 0.95), (10, 1.00), (11, 1.05), (12, 1.10))        # item 3
F_LINES = ((2, 1.00), (3, 1.30), (4, 1.45), (5, 1.60))                              # item 4; >= 5 reads 1.60
# Items 5 to 8 do not apply: no hold-down factor is taken, the gypsum inside is present
# (R602.10.4.3), no GB method, and horizontal joints are blocked (R602.10.4.4).

# Table R602.10.5, Methods CS-WSP and CS-SFB: minimum panel length, inches, by adjacent
# clear opening height (inches; the first row is "<= 64") and wall height (8, 9, 10, 11,
# 12 ft). None where the table prints no value. Footnote b: a panel contributes its
# actual length.
WALL_HEIGHTS = (8, 9, 10, 11, 12)
_CS_ROWS = ((64, 24, 27, 30, 33, 36), (68, 26, 27, 30, 33, 36), (72, 27, 27, 30, 33, 36),
            (76, 30, 29, 30, 33, 36), (80, 32, 30, 30, 33, 36), (84, 35, 32, 32, 33, 36),
            (88, 38, 35, 33, 33, 36), (92, 43, 37, 35, 35, 36), (96, 48, 41, 38, 36, 36),
            (100, None, 44, 40, 38, 38), (104, None, 49, 43, 40, 39), (108, None, 54, 46, 43, 41),
            (112, None, None, 50, 45, 43), (116, None, None, 55, 48, 45), (120, None, None, 60, 52, 48),
            (124, None, None, None, 56, 51), (128, None, None, None, 61, 54), (132, None, None, None, 66, 58),
            (136, None, None, None, None, 62), (140, None, None, None, None, 66), (144, None, None, None, None, 72))
CS_WSP_MIN = {h: tuple((row[0], row[1+i]) for row in _CS_ROWS if row[1+i] is not None)
              for i, h in enumerate(WALL_HEIGHTS)}
# Method CS-PF, SDC A, B and C: 16, 18, 20 inches at 8, 9, 10 ft; contributes 1.5 x actual.
CS_PF_MIN = ((8, 16), (9, 18), (10, 20))
CS_PF_CREDIT = 1.5

# R602.10.6.4, Figure R602.10.6.4 and Table R602.10.6.4. A CS-PF panel stands beside an
# opening 2'-0" to 18'-0" wide, its header not more than 10'-0" above the bottom of the
# wall, the header 3" x 11-1/4" net minimum, its sheathing nailed at 3" o.c. to all its
# framing, a header-to-jack-stud tension strap each side of the opening, and not more
# than four in one braced wall line. Over a wood floor, two framing anchors of 670 lb
# across the sheathing joint at the rim, or the sheathing lapped 9-1/4" over the rim.
PORTAL_MAX_PER_LINE = 4
PORTAL_OPENING = (2.0, 18.0)
PORTAL_MAX_HEADER_HEIGHT = 10.0
PORTAL_HEADER = (IN(3), IN(11.25))          # net width, depth: minimum
PORTAL_NAIL_OC = IN(3)
PORTAL_ANCHOR_LB = 670
PORTAL_LAP = IN(9.25)
PORTAL_PONY = 0.0                           # the header is set directly under the double top plate
# Table R602.10.6.4, the Exposure B, 115 mph column: (stud, maximum pony wall height,
# maximum total wall height, maximum opening width, strap capacity lb). The other cells
# of those rows in the 115 mph Exposure B column are "DR", design required.
STRAP_B115 = (('2x4 NO. 2', 0, 10, 18, 1000),
              ('2x4 NO. 2', 1, 10, 9, 1000), ('2x4 NO. 2', 1, 10, 16, 1025), ('2x4 NO. 2', 1, 10, 18, 1275),
              ('2x4 NO. 2', 2, 10, 9, 1000), ('2x4 NO. 2', 2, 10, 16, 2175), ('2x4 NO. 2', 2, 10, 18, 2500),
              ('2x4 NO. 2', 2, 12, 9, 1500), ('2x4 NO. 2', 2, 12, 16, 3375), ('2x4 NO. 2', 2, 12, 18, 3975),
              ('2x4 NO. 2', 4, 12, 9, 2750), ('2x4 NO. 2', 4, 12, 12, 3775),
              ('2x6 STUD', 2, 12, 9, 1000), ('2x6 STUD', 2, 12, 16, 2150), ('2x6 STUD', 2, 12, 18, 2550),
              ('2x6 STUD', 4, 12, 9, 1750), ('2x6 STUD', 4, 12, 16, 2400), ('2x6 STUD', 4, 12, 18, 3800))
PORTAL_STUD = '2x4 NO. 2'                   # the minimum the table's first rows name; the walls are 2x6


def strap_lb(wall_height, width, pony=PORTAL_PONY, stud=PORTAL_STUD):
    """Table 602.10.6.4, Exposure B, 115 mph: the first row whose limits cover the
       portal. ValueError where the table gives no row — design required."""
    rows = [r for r in STRAP_B115 if r[0] == stud and pony <= r[1]+1e-9 and wall_height <= r[2]+1e-9 and width <= r[3]+1e-9]
    if not rows:
        raise ValueError('a %s portal in a %s wall is outside Table 602.10.6.4' % (fmt(width), fmt(wall_height)))
    return min(rows, key=lambda r: (r[1], r[2], r[3]))[4]

# R602.10.2.2, R602.10.2.3 and Figure R602.10.7's requirements box, for wood structural
# panel sheathing.
FIRST_PANEL_MAX = 10.0      # a panel begins within this of each end of the line
PANEL_GAP_MAX = 20.0        # between adjacent panel edges
TWO_PANEL_LINE = 16.0       # a longer line has two panels; a shorter one two, or one of 48"
ONE_PANEL_MIN = IN(48)
RETURN_MIN = IN(24)         # return panel, end conditions 1 and 4
CORNER_D_MIN = IN(24)       # distance D, corner to the opening, end condition 4
END_PANEL_ALONE = IN(48)    # end condition 3
HOLD_DOWN_LB = 800          # end conditions 2 and 5
# R602.10.8.2: top of the braced wall panel to the top of the trusses. At or under the
# first no blocking; to the second, blocking per Figure R602.10.8.2(1); over it, item 3.
HEEL_NO_BLOCKING = IN(9.25)
HEEL_BLOCKING_MAX = IN(15.25)

# Table R602.3(3): 7/16" OSB, 24/16, studs at 16" o.c., 8d common at 6" edges / 12"
# field, 1-3/4" into the framing, good to 170 mph in Exposure B. Over the 5/8" exterior
# gypsum of W1R the 8d common does not reach 1-3/4", so those walls take a 10d common.
SHEATHING = '7/16" OSB, 24/16'
SHEATHING_T = IN(7/16.0)
GYP_SHEATHING_T = IN(5/8.0)
NAIL = '8d COMMON (2-1/2" x 0.131")'
NAIL_W1R = '10d COMMON (3" x 0.148")'
NAIL_LENGTH = {NAIL: IN(2.5), NAIL_W1R: IN(3.0)}
NAIL_EDGE, NAIL_FIELD = IN(6), IN(12)
NAIL_PENETRATION = IN(1.75)


def interp(pairs, v):
    """Linear interpolation in ((x, y), ...); at or below the first x reads the first
       row, past the last x is an error, not an extrapolation."""
    if v <= pairs[0][0]+1e-9:
        return pairs[0][1]
    for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
        if v <= x1+1e-9:
            return y0+(v-x0)/(x1-x0)*(y1-y0)
    raise ValueError('%.3f is past the last row of the table, %s' % (v, pairs[-1][0]))


def _column(height, columns):
    """The table column at or above a wall height, feet."""
    for h in columns:
        if height <= h+1e-9:
            return h
    raise ValueError('a %s wall is past the last column, %s ft' % (fmt(height), columns[-1]))


def cs_wsp_min(wall_height, opening_height):
    """Table 602.10.5, feet: the wall-height column at or above the wall, the opening
       row at or above the taller adjacent clear opening. No interpolation is taken."""
    rows = CS_WSP_MIN[_column(wall_height, WALL_HEIGHTS)]
    oh = opening_height*12.0
    for row, length in rows:
        if oh <= row+1e-6:
            return IN(length)
    raise ValueError('a %s opening is past Table 602.10.5 for a %s wall' % (fmt(opening_height), fmt(wall_height)))


def cs_pf_min(wall_height):
    return IN(dict(CS_PF_MIN)[_column(wall_height, tuple(h for h, _ in CS_PF_MIN))])


Segment = namedtuple('Segment', 'a b left right')        # left / right: the adjacent Opening, None at a corner


End = namedtuple('End', 'side condition hold_down')      # side 'lo' (the wall's 0) or 'hi'; hold_down: page feet along the wall, or None


def segments(run):
    """The full-height wall between openings, and from each corner to its first opening."""
    out = []; a = 0.0; left = None
    for o in run.openings:
        if o.a-a > 1e-6:
            out.append(Segment(a, o.a, left, o))
        a, left = o.b, o
    if run.length-a > 1e-6:
        out.append(Segment(a, run.length, left, None))
    return out


def corner_segment(run, side):
    """The full-height wall from the corner at `side` to the first opening; 0 where an
       opening starts at the corner."""
    segs = segments(run)
    if side == 'lo':
        return segs[0].b if segs and segs[0].a < 1e-9 else 0.0
    return run.length-segs[-1].a if segs and segs[-1].b > run.length-1e-9 else 0.0


def end_condition(run, side, ps, return_len):
    """Figure 602.10.7, taken in the order that needs the least hardware: 1, 3, 4, 2, 5.
       None where no condition holds."""
    first = ps[0] if side == 'lo' else ps[-1]
    at_corner = first.a < 1e-9 if side == 'lo' else first.b > run.length-1e-9
    edge = first.a if side == 'lo' else first.b
    if at_corner:
        if return_len >= RETURN_MIN-1e-9:
            return End(side, 1, None)
        if first.b-first.a >= END_PANEL_ALONE-1e-9:
            return End(side, 3, None)
        return End(side, 2, edge)
    if (edge if side == 'lo' else run.length-edge) > FIRST_PANEL_MAX+1e-9:
        return End(side, None, None)
    if return_len >= RETURN_MIN-1e-9 and corner_segment(run, side) >= CORNER_D_MIN-1e-9:
        return End(side, 4, None)
    return End(side, 5, edge)


def provided(line):
    return sum(p.credit for p in line.panels)


def factor(line):
    f = 1.0
    for _nm, v in line.factors:
        f *= v
    return f


def roof_connection(*, heel_nom):
    """602.10.8.2 item for the walls the trusses are perpendicular to."""
    if heel_nom <= HEEL_NO_BLOCKING+1e-9:
        return 'NONE'
    if heel_nom <= HEEL_BLOCKING_MAX+1e-9:
        return 'ITEM 1'
    return 'ITEM 3'


def header_depth(size):
    """The actual depth, feet, of a sawn header size such as '2-2x10' — 1/2" under the
       nominal to a 2x6, 3/4" above; 0 for a size the schedule words, 'PER 602.7.4'."""
    if not size[:1].isdigit():
        return 0.0
    nominal = int(size.split('x')[1])
    return IN(nominal-(0.5 if nominal <= 6 else 0.75))


def portal_header_size():
    """The shallowest sawn header meeting PORTAL_HEADER, Figure 602.10.6.4's net minimum
       over the opening and the portal leg: the plies that make its net width and the
       nominal depth whose dressed size makes its depth. '2-2x12' at today's figures, and
       it follows PORTAL_HEADER rather than being typed beside it."""
    plies = int(round(PORTAL_HEADER[0]/IN(1.5)))
    for nominal in (4, 6, 8, 10, 12, 14, 16):
        size = '%d-2x%d' % (plies, nominal)
        if header_depth(size) >= PORTAL_HEADER[1]-1e-9:
            return size
    raise ValueError('no sawn header meets the %s portal minimum' % fmt(PORTAL_HEADER[1]))

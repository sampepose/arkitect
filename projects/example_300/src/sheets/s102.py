"""S-102 — floor framing plans: each building's Level 2 floor over its greyed Level 1
plan, from src/framing.py; the header schedule, the design loads and the notes."""
import re as _re

from lib.draw.page import LAY, Sheet, end_plans
from lib.draw.sheets import draw_joist_span, draw_level
from lib.draw.text import wrap_notes
from lib.units import fmt, inches
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.building1 import _b1_level
from src.building2 import B2_W, b2_level
from src.framing import (B1_FLOOR, B2_FLOOR, DEAD_LOADS, DEFLECTION, F1_JOIST, F2_JOIST, GROUND_SNOW,
                         GUARD_LOAD, HEADERS, JOIST_OC, LIVE_LOADS, SUBFLOOR, LVL, LVL_DEPTH, LVL_PLIES,
                         LVL_PLY, header_positions)
from codes.ohio.rco.floor_checks import joist_lines
from codes.ohio.rco.floor_checks import bay_span
from codes.ohio.rco.headers import HEADER_BRACING, UNBRACED_FACTOR, _factor, header_for
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from lib.draw.kit import _fits, title
from src.sheets.plans import B1_DRAWING, draw_u5_stair
from lib.draw.framing_kit import _CARRIES_ABBR, _SCHED_COLS, _cut, _hanger, _in0, _sched_cols, _typical
from lib.draw.framing_kit import _header_tags


def _framing(p, floor):
    """The joists, rims, the well and the bearing lines of one floor on PlanDraw p."""
    cc = p.c
    for b in floor.bays:
        LAY('S-FRAM')
        cc.setStrokeColor(black); cc.setLineWidth(0.35)
        for x0, y0, x1, y1 in joist_lines(b, joist_oc=JOIST_OC):
            seg = _cut(floor, b, x0, y0, x1, y1)
            for sx0, sy0, sx1, sy1 in seg:
                cc.line(p.X(sx0), p.Y(sy0), p.X(sx1), p.Y(sy1))
        cc.setLineWidth(1.1)                                   # the rims, along the bearing ends
        if b.run == 'h':
            cc.line(p.X(b.x0), p.Y(b.y0), p.X(b.x0), p.Y(b.y1)); cc.line(p.X(b.x1), p.Y(b.y0), p.X(b.x1), p.Y(b.y1))
        else:
            cc.line(p.X(b.x0), p.Y(b.y0), p.X(b.x1), p.Y(b.y0)); cc.line(p.X(b.x0), p.Y(b.y1), p.X(b.x1), p.Y(b.y1))
        label = '%s I-JOISTS AT %s O.C.  ·  %s CLEAR SPAN' % (inches(b.joist), inches(JOIST_OC), fmt(bay_span(b)))
        LAY('S-ANNO-TEXT')
        if b.run == 'h':
            draw_joist_span(p, b.x0, (b.y0+b.y1)/2.0, b.x1, label, o='h')
        else:
            draw_joist_span(p, b.y0, (b.x0+b.x1)/2.0, b.y1, label, o='v')
        _typical(p, b)
    # walls parallel to the joists that carry a wall above: the rated rim, drawn heavier
    LAY('S-FRAM')
    for x0, y0, x1, y1, nm in floor.rated_rims:
        cc.setStrokeColor(black); cc.setLineWidth(1.8); cc.line(p.X(x0), p.Y(y0), p.X(x1), p.Y(y1))
        LAY('S-ANNO-TEXT'); cc.setFillColor(black); cc.setFont('Helvetica', 4.6)
        # Centred on the whole rim, the left label prints over the mechanical closet's
        # greyed panel and water-heater clearance boxes in the courtyard bay; shift it
        # down the wall to the bedroom side, clear of them. The right rim has no such
        # conflict and stays centred.
        ly = y0+0.75*(y1-y0) if x0 < 1 else (y0+y1)/2.0
        cc.saveState(); cc.translate(p.X(x0)+(6 if x0 < 1 else -6), p.Y(ly)); cc.rotate(90)
        cc.drawCentredString(0, -1.5 if x0 < 1 else 3.5, nm); cc.restoreState(); LAY('S-FRAM')
    for w in floor.wells:
        LAY('S-FRAM')
        cc.setLineWidth(1.4)
        for y in (w.y0, w.y1):                                  # the trimmers, doubled
            cc.line(p.X(w.x0), p.Y(y), p.X(w.header_x0), p.Y(y)); cc.line(p.X(w.x0), p.Y(y)+2.2, p.X(w.header_x0), p.Y(y)+2.2)
        for x in (w.header_x0, w.header_x1):                    # the header, doubled, on the stair wall
            cc.line(p.X(x), p.Y(w.y0), p.X(x), p.Y(w.y1))
        for y in (w.y0, w.y1):                                  # hangers where the trimmers meet the header
            _hanger(p, w.header_x0, y)
        for x0, y0, x1, y1 in joist_lines(floor.bays[0], joist_oc=JOIST_OC):       # the tail joists' hangers
            if w.y0 < y0 < w.y1: _hanger(p, w.header_x1, y0)
        # Printed above the well, in the open room past the header, rather than beside
        # it: beside it runs the label into the greyed panel and water-heater clearance
        # boxes below Level 1's mechanical room.
        LAY('S-ANNO-TEXT'); cc.setFillColor(black); cc.setFont('Helvetica', 4.6)
        cc.drawString(p.X(w.header_x1)+4, p.Y(w.y0-1.0)+3, 'DOUBLE %s I-JOIST HEADER ON THE STAIR WALL' % inches(floor.bays[0].joist))
        cc.drawString(p.X(w.header_x1)+4, p.Y(w.y0-1.0)-3, 'TAIL JOISTS ON HANGERS; DOUBLE TRIMMERS AT THE WELL\'S SIDES')
        cc.drawCentredString(p.X((w.x0+w.x1)/2.0), p.Y((w.y0+w.y1)/2.0), 'WELL %s x %s' % (fmt(w.x1-w.x0), fmt(w.y1-w.y0)))




# ---------------- the right column: header schedule, design loads, notes ----------------
# WALL and WALL CARRIES print abbreviated — the 3.5 in column has no room for
# "ADJACENT-PARCEL WALL" or "ROOF, CEILING AND ONE CENTER-BEARING FLOOR" at 26 rows — and
# the abbreviations are spelled out in _SCHED_KEY, printed under the schedule.
_WALL_ABBR = {
    'ADJACENT-PARCEL WALL': 'PARCEL',
    'SAGE WALL': 'SAGE',
    'S ELM WALL': 'S ELM',
    'REAR WALL': 'REAR',
    'COURTYARD WALL': 'CTYD',
    'UNITS 2 AND 3 BEARING WALL': 'U2/3 BRG',
    'UNITS 4 AND 5 BEARING WALL': 'U4/5 BRG',
}
_SCHED_KEY = ('ABBREVIATIONS: B/L = BUILDING / LEVEL; WD = WIDTH; J/F = JACK STUDS / FULL-HEIGHT '
              'STUDS; OPEN. = OPENINGS COVERED (COUNT; LEVEL 2 ROWS LOCATED BY SHEET); CTYD = '
              'COURTYARD WALL; U2/3 BRG = UNITS 2 AND 3 BEARING WALL; U4/5 BRG = UNITS 4 AND 5 '
              'BEARING WALL; R = ROOF; C = CEILING; CS = CLEAR-SPAN FLOOR; '
              'CB = CENTER-BEARING FLOOR; 1 FLR = ONE FLOOR ONLY; '
              '* THE WALL ABOVE IS A PARTITION, NOT LOAD-BEARING. '
              'BUILDING 2\'S COURTYARD AND REAR WALLS CARRY ONE CENTER-BEARING FLOOR AND NO ROOF: '
              'R+C+1CB ROW USED (CONSERVATIVE).')


def _sched_row(h):
    """The header schedule's ten columns for one HEADERS condition, as strings. A
       non-bearing condition prints PER 602.7.4 under HEADER and — under J/F and SPAN,
       since neither a stud count nor a table span applies to it."""
    if h.load_case == 'NON-BEARING':
        carries = 'NOTHING *' if 'BEARING' in h.wall else 'NOTHING'
        jf, span = '—/—', '—'
    else:
        carries = _CARRIES_ABBR[h.load_case]
        jf = '%d/%d' % (h.jacks, h.full_height_studs)
        size, _jacks, _row, factored = header_for(h.load_case, h.width)
        factor = _factor(size)
        tab = factored/factor
        span = ('%sx%s=%s' % (fmt(tab), ('%.2f' % factor).lstrip('0'), fmt(factored))) if factor < 1.0 else fmt(tab)
        if h.size == LVL: span = '%s ROOM' % inches(h.room)      # why it is an LVL: what the table's header had to fit in
    table = 'NOTE 4a' if h.size == LVL else h.row.split(',')[0].replace('TABLE ', '').strip()
    n = len(h.openings)
    if h.level == 2:
        openings = '%d  %s' % (n, 'A-102 LEVEL 2' if h.building == 'BUILDING 1' else 'A-103 LEVEL 2')
    else:
        openings = str(n)
    return (h.tag, '%s/%d' % (h.building[-1], h.level), _WALL_ABBR[h.wall], carries,
            fmt(h.width), h.size, jf, span, table, openings)


def _header_schedule(x, y, width):
    """HEADER SCHEDULE: one row per src.framing.HEADERS condition, grouped by building,
       above it the bracing/species note built from HEADER_BRACING, below it the
       abbreviation key. Returns the y it ended at."""
    S, LEAD = 5.2, 6.4
    rows = [_sched_row(h) for h in HEADERS]
    offsets, widths = _sched_cols(S, rows)
    assert offsets[-1]+widths[-1] <= width, 'header schedule runs out of its column'
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, 'HEADER SCHEDULE'); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= LEAD+2
    brace = ('SPANS ARE ROUGH-OPENING WIDTHS AS DRAWN. TWO-PLY HEADERS, NO. 2 DF-L / HEM-FIR / SP / SPF, '
             'TABLE 602.7(1)/(2) 30 PSF / 36 FT COLUMNS, EACH ' + HEADER_BRACING +
             '; FULL-HEIGHT STUDS TABLE 602.7.5, 115 MPH EXPOSURE B, G-001.')
    c.setFont('Helvetica', 5.0)
    for t in wrap_notes([brace], width, 5.0):
        _fits(t, 'Helvetica', 5.0, width, 'header schedule note'); c.drawString(x, y, t); y -= 6.2
    y -= 2
    c.setFont('Helvetica-Bold', S)
    for t, off in zip(_SCHED_COLS, offsets):
        c.drawString(x+off, y, t)
    y -= 2
    c.setLineWidth(0.4); c.line(x, y, x+width, y); y -= LEAD
    c.setFont('Helvetica', S)
    building = None
    for h, row in zip(HEADERS, rows):
        if h.building != building:
            if building is not None: y -= 1.5
            building = h.building
            c.setFont('Helvetica-Bold', S); c.drawString(x, y, building); y -= LEAD
            c.setFont('Helvetica', S)
        for t, off, w in zip(row, offsets, widths):
            _fits(t, 'Helvetica', S, w, 'header schedule cell'); c.drawString(x+off, y, t)
        y -= LEAD
    y -= 2
    c.setFont('Helvetica', 5.0)
    for t in wrap_notes([_SCHED_KEY], width, 5.0):
        _fits(t, 'Helvetica', 5.0, width, 'header schedule key'); c.drawString(x, y, t); y -= 6.2
    return y-4


def _design_loads(x, y, width):
    """DESIGN LOADS: one row per src.framing.LIVE_LOADS, the guard load, DEAD_LOADS,
       DEFLECTION and GROUND_SNOW — every figure read from the model, none typed."""
    S, LEAD = 5.6, 7.4
    heading = 'DESIGN LOADS — RCO TABLE 301.5, 301.7, G-001'
    _fits(heading, 'Helvetica-Bold', 7.2, width, 'design loads heading')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= LEAD+2
    c.setFont('Helvetica', S)
    rows = [(nm, '%d PSF' % v) for nm, v in LIVE_LOADS]
    rows.append(('GUARDS, CONCENTRATED, ANY DIRECTION', '%d LB' % GUARD_LOAD))
    rows += [('DEAD LOAD, %s' % nm, '%d PSF' % v) for nm, v in DEAD_LOADS]
    rows.append(('DEFLECTION, LIVE LOAD ON FLOORS', DEFLECTION))
    rows.append(('GROUND SNOW, ROOF', '%d PSF' % GROUND_SNOW))
    for lab, val in rows:
        vw = pdfmetrics.stringWidth(val, 'Helvetica', S)
        _fits(lab, 'Helvetica', S, width-vw-6, 'design loads label')
        c.drawString(x, y, lab); c.drawRightString(x+width, y, val); y -= LEAD
    return y-6


# The Unit 1 F2 bay, so note 1 states the span it actually carries rather than a copy
# of it: the side walls' stud faces set this, and the note is the supplier's instruction.
_F2_BAY = next(b for b in B1_FLOOR.bays if b.name == 'UNIT 1 F2')

# Upper-cased for the sheet, but a cross-reference keeps its sub-letter lower case,
# as every other sheet prints it: A-001 NOTE 4a, not 4A.
_NOTES = [_re.sub(r'(NOTES? \d+)([A-Z])\b', lambda m: m.group(1)+m.group(2).lower(), n.upper()) for n in (
    f'1. Floor framing: prefabricated I-joists at {inches(JOIST_OC)} o.c., F1 {inches(F1_JOIST)} and '
    f'F2 {inches(F2_JOIST)} per A-601, in the '
    f'bays and directions drawn; {_in0(SUBFLOOR)} T&G subfloor glued and screwed. The joists drawn are the typical '
    'layout; the joist manufacturer\'s engineered layout governs joist positions, and its series, rim, '
    'hangers, stiffeners and blocking are designed to the loads tabulated and submitted before framing. '
    f'F2 clear-spans {fmt(bay_span(_F2_BAY))} plate to plate: submit the '
    'F2 series, depth and deflection for that span, and its bearing length at each side wall, before '
    'fabrication.',

    '2. Bearing: joists bear on the exterior wall plates and the interior bearing walls drawn; those '
    'walls stand on the S-101 strips. Supporting construction of the F1 floor is rated: interior '
    'bearing walls type W3, exterior walls under it type W1R, RCO 302.3.1. Blocking at every bearing '
    'line; squash blocks under the well header and at every header end. Where a wall parallel to the '
    'joists carries a wall above (Building 2\'s side walls, under the roof-bearing walls of Level 2), '
    'the rim board or full-depth blocking at the floor edge is rated by the manufacturer for that '
    'wall\'s load and carries it plate to plate.',

    '3. The Unit 1 well: double header on the stair wall, double trimmers at the well\'s sides, tail '
    'joists on hangers; the stair wall framed as bearing with a load path to its strip (A-001 note '
    '13). Headroom and header-face limits per A-001 note 13; no dropped member below them.',

    f'4. Headers as scheduled, No. 2 Douglas fir-larch, hem-fir, southern pine or spruce-pine-fir, '
    f'sized with Table 602.7(1) footnote f\'s {UNBRACED_FACTOR:.2f} factor on every 2x8, 2x10 and 2x12 header, so '
    'cripples may bear on them; jack studs and full-height studs per Tables 602.7(1), (2) and '
    '602.7.5; non-bearing openings per 602.7.4.',

    f'4a. Headers scheduled LVL: {LVL_PLIES} plies of {_in0(LVL_PLY)} x {_in0(LVL_DEPTH)} laminated veneer lumber, 2.0E, where the '
    f'table\'s header is deeper than the room between the opening\'s head and the double top plate, tabulated under SPAN. '
    'Its depth is a 2x6 header\'s. Confirm the size from the LVL manufacturer\'s header table for the loads tabulated and '
    'submit it with the joist package; fasten the plies as that table requires; jack and full-height studs as scheduled.',

    '5. W4 is two walls, W4A and W4B, and each unit frames its own floor on its own '
    'wall — its rim nailed to that wall\'s top plate, nothing reaching the other unit\'s wall, RCO 302.2.6 '
    '(A-601, A-603). Each wall continues to the roof deck. Their joists run parallel to W4, '
    'Sage to the adjacent parcel, and no joist, rim, blocking or strap bridges it.',

    '6. F1 is a rated floor, ICC-ES ESR-1153 Assembly F (A-601): ceiling membrane per that report, boxes and penetrations per A-001 note 4a; '
    'firestop the one stack crossing per unit (P-601).',

    '7. Holes and notches in I-joists only where the manufacturer\'s chart allows; never a flange '
    '(P-601 note 1aa).',

    '8. Roof trusses at 24" o.c. bear on the side walls; layout and design by the truss manufacturer '
    '(A-202, A-601). No roof load on the interior bearing walls.',

    '9. Guards: posts anchored to header or blocking, not the subfloor alone (A-001 note 13).',
)]


def _notes(x, y, width, size=5.6, lead=7.4):
    """The nine notes of the design spec, verbatim and uppercased, wrap_notes-flowed into
       one column. Returns the y it ended at."""
    LAY('S-ANNO-TEXT')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, 'FLOOR FRAMING NOTES'); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= lead+2
    c.setFont('Helvetica', size)
    for t in wrap_notes(_NOTES, width, size):
        _fits(t, 'Helvetica', size, width, 'floor framing note'); c.drawString(x, y, t); y -= lead
    return y


def sheet_s102():
    sh = Sheet(c, "S-102", "Floor framing plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-48*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+26*Q+1.0*inch
    lv = _b1_level(1, [], [], [], units=[], u3stair=True, annotate=False, **B1_DRAWING)
    lv.overlay = lambda p: (_framing(p, B1_FLOOR), _header_tags(p, 'BUILDING 1', header_positions=header_positions),
                            grey_context(p, 26, 48, 'S ELM AVENUE', 'REAR YARD', 'SAGE AVENUE', 'ADJACENT PARCEL'))
    draw_level(c, lv, ox1, oy)
    lv2 = b2_level(1)
    lv2.over_plan = lambda pp: draw_u5_stair(pp, B2_W, above=True)
    lv2.overlay = lambda p: (_framing(p, B2_FLOOR), _header_tags(p, 'BUILDING 2', header_positions=header_positions),
                             grey_context(p, B2_W, 28, 'COURTYARD', 'PARKING AND ALLEY', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=5.6))
    draw_level(c, lv2, ox2, Y1-0.55*inch-1.35*inch-28*Q)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 2 FLOOR FRAMING  ·  LEVEL 1 WALLS BELOW, GRAY')
    title(ox2, Y1-0.55*inch-1.35*inch-28*Q, 'BUILDING 2 — LEVEL 2 FLOOR FRAMING  ·  LEVEL 1 WALLS BELOW, GRAY')
    # the right column: the header schedule, the design loads, the notes — Building 2's
    # plan is 7 in tall at the right, so the column is the only thing to its right
    rx = ox2+26*Q+0.45*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = _header_schedule(rx, ry, rw)-8
    ry = _design_loads(rx, ry, rw)-10
    ry = _notes(rx, ry, rw)
    assert ry > Y0, 'S-102 right column runs past the frame: ends at %.2f, frame bottom %.2f' % (ry, Y0)
    c.showPage()

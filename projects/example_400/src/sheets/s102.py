"""S-102 — floor framing plans: each building's Level 2 floor over its greyed Level 1
plan, from src/framing.py; the header schedule, the design loads and the notes."""
from arkitect.lib.draw.page import LAY, Sheet, end_plans
from arkitect.lib.draw.sheets import draw_joist_span, draw_level
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import levels
from src.building1 import B1_D, B1_W
from src.building2 import B2_D, B2_W, b2_level
from src.framing import (B1_FLOOR, B2_FLOOR, DEAD_LOADS, DEFLECTION, F1_MAX_JOIST_OC, F1_MIN_TRUSS_DEPTH,
                         F2_JOIST, GROUND_SNOW, GUARD_LOAD, HEADERS, JOIST_OC, LIVE_LOADS, SUBFLOOR,
                         TRUSS_OC, LVL, LVL_DEPTH, LVL_PLIES, LVL_PLY, header_positions)
from arkitect.codes.ohio.rco.floor_checks import joist_lines
from arkitect.codes.ohio.rco.floor_checks import bay_span
from arkitect.codes.ohio.rco.headers import HEADER_BRACING, UNBRACED_FACTOR, _factor, header_for
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from arkitect.lib.draw.kit import _fits, title
from src.sheets.a101 import b1_trade_level
from src.sheets.a102 import draw_u5_stair
from arkitect.lib.draw.framing_kit import _CARRIES_ABBR, _SCHED_COLS, _cut, _in0, _sched_cols, _typical
from arkitect.lib.draw.framing_kit import _header_tags


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
        label = '%s FLOOR TRUSSES AT %s O.C.  ·  %s CLEAR SPAN' % (inches(b.joist), inches(JOIST_OC), fmt(bay_span(b)))
        LAY('S-ANNO-TEXT')
        if b.run == 'h':      # a third of the way down: between the house's room labels
            draw_joist_span(p, b.x0, b.y0+0.35*(b.y1-b.y0), b.x1, label, o='h')
        else:
            draw_joist_span(p, b.y0, (b.x0+b.x1)/2.0, b.y1, label, o='v')
        _typical(p, b)
    # walls parallel to the joists that carry a wall above: the rated rim, drawn heavier
    LAY('S-FRAM')
    for x0, y0, x1, y1, nm in floor.rated_rims:
        cc.setStrokeColor(black); cc.setLineWidth(1.8); cc.line(p.X(x0), p.Y(y0), p.X(x1), p.Y(y1))
        LAY('S-ANNO-TEXT'); cc.setFillColor(black); cc.setFont('Helvetica', 4.6)
        # The left label a third of the way down, clear of the greyed panel and heater
        # clearances in the mechanical room and the tags at the bedroom window; the
        # right one centred.
        ly = y0+0.35*(y1-y0) if x0 < 1 else (y0+y1)/2.0
        cc.saveState(); cc.translate(p.X(x0)+(6 if x0 < 1 else -6), p.Y(ly)); cc.rotate(90)
        cc.drawCentredString(0, -1.5 if x0 < 1 else 3.5, nm); cc.restoreState(); LAY('S-FRAM')
    for w in floor.wells:
        LAY('S-FRAM')
        cc.setLineWidth(1.4)
        for y in (w.y0, w.y1):                                  # the trimmers, doubled
            cc.line(p.X(w.x0), p.Y(y), p.X(w.header_x0), p.Y(y)); cc.line(p.X(w.x0), p.Y(y)+2.2, p.X(w.header_x0), p.Y(y)+2.2)
        for x in (w.header_x0, w.header_x1):                    # the header, doubled, on the stair wall
            cc.line(p.X(x), p.Y(w.y0), p.X(x), p.Y(w.y1))
        # no hangers: the stair wall runs the well's whole length and the tail trusses bear on its plate
        # Printed above the well, in the open room past the header, rather than beside
        # it: beside it runs the label into the greyed panel and water-heater clearance
        # boxes below Level 1's mechanical room.
        LAY('S-ANNO-TEXT'); cc.setFillColor(black); cc.setFont('Helvetica', 4.6)
        cc.drawString(p.X(w.header_x1)+4, p.Y(w.y0-1.0)+3, 'TAIL TRUSSES BEAR ON THE STAIR WALL\'S PLATE, %s DEEP' % inches(floor.bays[0].joist))
        cc.drawString(p.X(w.header_x1)+4, p.Y(w.y0-1.0)-3, 'A GIRDER TRUSS AT EACH SIDE OF THE WELL, BY THE TRUSS DESIGN')
        cc.drawCentredString(p.X((w.x0+w.x1)/2.0), p.Y((w.y0+w.y1)/2.0), 'WELL %s x %s' % (fmt(w.x1-w.x0), fmt(w.y1-w.y0)))




# ---------------- the right column: header schedule, design loads ----------------
# WALL and WALL CARRIES print abbreviated, spelled out in _SCHED_KEY under the schedule.
_WALL_ABBR = {
    'NORTH WALL': 'NORTH',
    'SOUTH WALL': 'SOUTH',
    'FRONT WALL': 'FRONT',
    'REAR WALL': 'REAR',
    'COURTYARD WALL': 'CTYD',
    'UNIT 1 STAIR WALL': 'STAIR',
    'UNITS 2 AND 3 BEARING WALL': 'U2/3 BRG',
}
_SCHED_KEY = ('ABBREVIATIONS: B/L = BUILDING / LEVEL; WD = WIDTH; J/F = JACK STUDS / FULL-HEIGHT '
              'STUDS; OPEN. = OPENINGS COVERED (COUNT; LEVEL 2 ROWS LOCATED BY SHEET); FRONT = '
              'THE OAK AVENUE WALL; CTYD = COURTYARD WALL; STAIR = UNIT 1 STAIR WALL; U2/3 BRG = '
              'UNITS 2 AND 3 BEARING WALL; R = ROOF; C = CEILING; CS = CLEAR-SPAN FLOOR; '
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
        openings = '%d  %s' % (n, 'A-101 LEVEL 2' if h.building == 'BUILDING 1' else 'A-102 LEVEL 2')
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
             '; FULL-HEIGHT STUDS TABLE 602.7.5, 115 MPH EXPOSURE B.')
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
    heading = 'DESIGN LOADS — RCO TABLE 301.5, 301.7'
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


_F2_BAY = B1_FLOOR.bays[0]
_REAR_BAY = max(B2_FLOOR.bays, key=bay_span)

# Upper-cased for the sheet.
_NOTES = [n.upper() for n in (
    f'1. Floor framing: prefabricated open-web wood floor trusses, parallel chord, {inches(F2_JOIST)} deep at '
    f'{inches(JOIST_OC)} o.c. in both buildings, in the bays and directions drawn, from the roof trusses\' '
    f'manufacturer; {_in0(SUBFLOOR)} T&G subfloor, span rated for that spacing, glued and nailed. The trusses '
    f'drawn are the typical layout; the '
    'manufacturer\'s engineered layout and sealed truss design drawings govern, designed to the loads and the '
    f'{DEFLECTION.lower()} deflection tabulated and submitted before fabrication. The house clear-spans '
    f'{fmt(bay_span(_F2_BAY))} side wall to side wall and Building 2\'s rear bay {fmt(bay_span(_REAR_BAY))}. '
    f'{inches(F1_MAX_JOIST_OC)} o.c. is the maximum, {levels.F1_LISTING} and this sheet: a closer spacing is '
    'permitted on the manufacturer\'s design, a wider is not.',

    '2. Bearing: trusses bear on the exterior wall plates and the interior bearing walls drawn, which '
    'stand on the S-101 strips. A ribbon board or blocking at every bearing line as the truss design '
    'details it. Building 2\'s side walls, parallel to the trusses, carry the roof-bearing walls of '
    'Level 2: the end truss or ladder framing there is designed for that load and carries it plate to plate.',

    '3. The house\'s well: the stair wall framed as bearing, on its S-101 strip, runs the well\'s length; the tail '
    'trusses bear on its plate and a girder truss stands at each side of the well, by the truss design. No member '
    'below the well\'s edges within the stair headroom, RCO 311.7.2.',

    f'4. Headers as scheduled, No. 2 Douglas fir-larch, hem-fir, southern pine or spruce-pine-fir, '
    f'sized with Table 602.7(1) footnote f\'s {UNBRACED_FACTOR:.2f} factor on every 2x8, 2x10 and 2x12 header, so '
    'cripples may bear on them; jack studs and full-height studs per Tables 602.7(1), (2) and '
    '602.7.5; non-bearing openings per 602.7.4.',

    f'4a. Headers scheduled LVL: {LVL_PLIES} plies of {_in0(LVL_PLY)} x {_in0(LVL_DEPTH)} laminated veneer lumber, 2.0E, where the '
    f'table\'s header is deeper than the room between the opening\'s head and the double top plate, tabulated under SPAN. '
    'Its depth is a 2x6 header\'s, so every header in both buildings frames alike. Confirm the size from the LVL '
    'manufacturer\'s header table for the loads tabulated and submit it with the truss package; fasten the plies as that '
    'table requires; jack and full-height studs as scheduled.',

    f'5. Building 2\'s Level 2 floor separates Units 2 and 3: a 1-hour floor-ceiling, RCO 302.3, '
    f'{levels.F1_LISTING} — open-web trusses of nominal 2x4 lumber, {_in0(F1_MIN_TRUSS_DEPTH)} deep or more, at '
    f'{_in0(F1_MAX_JOIST_OC)} o.c. or less; resilient channels at {_in0(levels.F1_CHANNEL_OC)} o.c.; one layer of '
    f'{_in0(levels.F1_LAYER)} Type C; no insulation in the cavity. A-601 has the listing in full. The walls '
    'under it are 1-hour, RCO 302.3.1. Penetrations per RCO 302.4.',

    '6. Pipes, ducts, line sets and cables pass through the trusses\' open webs. Never cut, notch or drill a '
    'chord, a web or a plate; a truss damaged or altered is repaired only to the manufacturer\'s sealed detail.',

    f'7. Roof trusses at {inches(TRUSS_OC)} o.c. bear on the side walls of both buildings; layout and design by the truss '
    'manufacturer. No roof load on the interior bearing walls.',

    '8. Guards: posts anchored to header or blocking, not the subfloor alone.',
)]


def _notes(x, y, width, size=5.6, lead=7.4):
    """The notes, uppercased, wrap_notes-flowed into one column. Returns the y it ended at."""
    LAY('S-ANNO-TEXT')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, 'FLOOR FRAMING NOTES'); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= lead+2
    c.setFont('Helvetica', size)
    for t in wrap_notes(_NOTES, width, size):
        _fits(t, 'Helvetica', size, width, 'floor framing note'); c.drawString(x, y, t); y -= lead
    return y


def sheet_s102():
    sh = Sheet(c, "S-102", "Floor framing plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-1.45*inch-B2_D*Q          # as E-102: room above for the Unit 3 stair
    ox1 = X0+1.0*inch
    ox2 = ox1+B1_W*Q+1.2*inch
    lv = b1_trade_level(1)
    lv.overlay = lambda p: (_framing(p, B1_FLOOR), _header_tags(p, 'BUILDING 1', header_positions=header_positions),
                            grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'BUILDING 2 AND THE ALLEY BEYOND',
                                         '396 OAK AVE', '404 OAK AVE'))
    draw_level(c, lv, ox1, oy)
    lv2 = b2_level(1)
    lv2.over_plan = lambda pp: draw_u5_stair(pp, B2_W, above=True)
    lv2.overlay = lambda p: (_framing(p, B2_FLOOR), _header_tags(p, 'BUILDING 2', header_positions=header_positions),
                             grey_context(p, B2_W, B2_D, 'COURTYARD', 'PARKING AND ALLEY',
                                          '396 OAK AVE', '404 OAK AVE', top_off=5.6))
    draw_level(c, lv2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 2 FLOOR FRAMING  ·  LEVEL 1 BELOW, GRAY')
    title(ox2, oy, 'BUILDING 2 — LEVEL 2 FLOOR FRAMING  ·  LEVEL 1 BELOW, GRAY')
    rx = ox2+B2_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = _header_schedule(rx, ry, rw)-8
    ry = _design_loads(rx, ry, rw)
    ny = _notes(ox1, oy-1.10*inch, rx-0.3*inch-ox1)
    assert ry > Y0, 'S-102 right column runs past the frame: ends at %.2f, frame bottom %.2f' % (ry, Y0)
    assert ny > Y0, 'S-102 notes run past the frame: end at %.2f, frame bottom %.2f' % (ny, Y0)
    c.showPage()

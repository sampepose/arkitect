"""What P-102 and P-103 share: putting a building's water supply on its greyed plans,
the legend, the fixture-unit and pipe-size table, the supply diagram and the notes.
Every figure printed here is read from src/plumbing.py, which check_model() has
already passed."""
from lib.draw.page import LAY
from lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src import drainage as dr
from src import plumbing as pm
from codes.ohio.opc_service_entry import entry_for as _entry_for
from lib.model import water as water
from lib.draw.kit import c
from lib.draw.kit import _fits
from lib.draw.plumbing_kit import (_P, _text, cold_line, hot_line, manifold, meter, riser, run_label,
                                   under_line, valve)
from lib.draw.kit import notes_block
from lib.draw.plumbing_kit import fixture_end

S = 5.6                                  # the text size the legend, table and notes share

# The service entry both buildings take, for the figures the plan and the notes print.
_SE = _entry_for(dr.BUILDING_1, dr.GROUND)


# ---------------- the symbols, at page points ----------------


# ---------------- a unit's supply on its plan ----------------






def draw_service(p, b, s):
    """The service into the building, its meter and valve, and the trunk to each unit,
       on the Level 1 plan."""
    cc = p.c
    E, R = _P(p, b.entry), _P(p, b.riser)
    under_line(cc, [E, R])
    # the building valve and the DPU meter, on the wall side of the riser
    valve(cc, R[0]-12, R[1]); meter(cc, R[0]-22, R[1])
    W = _P(p, (0.0, b.entry[1]))
    _text(cc, W[0]-3, W[1]+5.5, '%s" WATER SERVICE' % s['service'], 4.0, bold=True, anchor='r')
    _text(cc, W[0]-3, W[1]-7.0, 'FROM THE PUBLIC MAIN, %s TO THE WALL ASSUMED' % fmt(pm.MAIN_TO_WALL), 3.4, anchor='r')
    _text(cc, W[0]-3, W[1]-12.0, '%s DOWN, THROUGH THE FOOTING IN A SLEEVE, P-601' % inches(_SE.bury), 3.4, anchor='r')
    ss = dr.service_sleeve(dr.BUILDINGS[b.number-1])
    if ss is not None:
        _text(cc, W[0]-3, W[1]-17.0, 'SLEEVE FROM %s OUT, P-101 NOTE 9' % fmt(ss[0]), 3.4, anchor='r')
    # a riser point is tagged with what rises there: the service, and any Level 2
    # unit fed from it
    def tag_at(pt):
        up = [u.name for u in b.units if u.riser == pt]
        parts = (['SERVICE UP'] if pt == b.riser else [])+['UP TO %s' % n for n in up]
        return ', '.join(parts)
    riser(cc, R[0], R[1], tag_at(b.riser))
    for names, path, under in b.trunks:
        if len(path) < 2: continue
        pts = [_P(p, q) for q in path]
        if under: under_line(cc, pts)
        else: cold_line(cc, pts, width=1.0)
        who = ' AND '.join(names) if len(names) == 1 else 'UNITS '+' AND '.join(n.split()[-1] for n in names)
        run_label(cc, pts, '%s" TRUNK TO %s%s' % (s['trunks'][names[0]], who, ', BELOW THE SLAB, SLEEVED' if under else ''), always=True)
        if path[-1] != b.riser and tag_at(path[-1]):
            riser(cc, pts[-1][0], pts[-1][1], tag_at(path[-1]))


# ---------------- the legend ----------------
LEGEND = [
    ('cold',   'COLD WATER, PEX; THE HOME RUNS %s"' % pm.HOME_RUN),
    ('hot',    'HOT WATER, PEX, DRAWN BESIDE ITS COLD LINE'),
    ('under',  'SERVICE OR TRUNK BELOW THE SLAB, IN A SLEEVE, NO JOINT'),
    ('riser',  'PIPE RISING TO THE LEVEL ABOVE, OR ARRIVING FROM BELOW'),
    ('valve',  'FULL-OPEN VALVE, OPC 606.1'),
    ('meter',  'WM THE DPU METER; SM A UNIT SUBMETER, P-601 NOTE 5'),
    ('man',    'COLD AND HOT MANIFOLDS, OPC 604.10; EVERY PORT VALVED AND LABELED'),
    ('fix',    'FIXTURE CONNECTION; KS SINK, DW DISHWASHER, CW WASHER, WH HEATER'),
    ('label',  'RUN LABEL: THE GROUP, ITS COLD AND HOT LINE COUNTS AND THEIR SIZE'),
]


def legend(x, y, width, lead=13.0):
    cc = c
    cc.setFillColor(black); cc.setFont('Helvetica-Bold', S+2.4); cc.drawString(x, y, 'WATER SUPPLY LEGEND'); y -= lead+3
    for k, t in LEGEND:
        _fits(t, 'Helvetica', S, width-24, 'legend line')
        X, Y = x+2, y+S*0.36
        if k == 'cold': cold_line(cc, [(X, Y), (X+16, Y)])
        elif k == 'hot': cold_line(cc, [(X, Y-1), (X+16, Y-1)]); hot_line(cc, [(X, Y-1), (X+16, Y-1)])
        elif k == 'under': under_line(cc, [(X, Y), (X+16, Y)])
        elif k == 'riser': riser(cc, X+8, Y)
        elif k == 'valve': cold_line(cc, [(X, Y), (X+16, Y)]); valve(cc, X+8, Y)
        elif k == 'meter': meter(cc, X+8, Y)
        elif k == 'man': manifold(cc, X+2, Y-3, 12, 6)
        elif k == 'fix': cold_line(cc, [(X, Y), (X+8, Y)]); fixture_end(cc, X+8, Y, 'lav')
        elif k == 'label': cold_line(cc, [(X-2, Y-3), (X+18, Y-3)]); run_label(cc, [(X-2, Y-3), (X+18, Y-3)], 'BATH: 3C + 2H', 3.0)
        cc.setFillColor(black); cc.setFont('Helvetica', S); cc.drawString(x+24, y, t)
        y -= lead
    return y


# ---------------- the fixture-unit and pipe-size table ----------------
def wsfu_table(x, y, b, width):
    """Per dwelling, its fixtures and their WSFU by Table E103.3(2); then the building's
       total, developed length, the assumptions, and the sizes Table E201.1 gives."""
    LEAD = 7.6
    s = pm.sizes(b)
    cols = (width-1.55*inch, width-1.05*inch, width-0.55*inch, width)
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2)
    c.drawString(x, y, 'WATER SUPPLY FIXTURE UNITS — TABLE E103.3(2), PRIVATE'); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= LEAD+1
    c.setFont('Helvetica-Bold', S); c.drawString(x, y, 'FIXTURE')
    for t, cx in zip(('QTY', 'COLD', 'HOT', 'TOTAL'), cols): c.drawRightString(x+cx, y, t)
    y -= LEAD
    for n in water.unit_names(b):
        cold, hot, tot, rows = pm.unit_wsfu(b, n)
        c.setFont('Helvetica-Bold', S); c.drawString(x, y, n); y -= LEAD
        c.setFont('Helvetica', S)
        for label, q, cc_, hh, tt in rows:
            _fits(label, 'Helvetica', S, cols[0]-0.3*inch, 'table row')
            c.drawString(x+6, y, label)
            for v, cx in zip((str(q), '%.1f' % cc_, '%.1f' % hh, '%.1f' % tt), cols): c.drawRightString(x+cx, y, v)
            y -= LEAD
        c.setFont('Helvetica-Bold', S); c.drawString(x+6, y, '%s, WSFU' % n)
        for v, cx in zip(('%.1f' % cold, '%.1f' % hot, '%.1f' % tot), cols[1:]): c.drawRightString(x+cx, y, v)
        y -= LEAD+2
    c.setLineWidth(0.3); c.line(x, y+LEAD-2, x+width, y+LEAD-2)
    c.setFont('Helvetica-Bold', S); c.drawString(x, y, '%s — SIZES, TABLE E201.1' % b.name); y -= LEAD
    c.setFont('Helvetica', S)
    lines = [('TOTAL, WSFU', '%.1f' % s['total']),
             ('DEVELOPED LENGTH TO THE MOST REMOTE OUTLET', fmt(s['length'])),
             ('   OF WHICH MAIN TO WALL, ASSUMED', fmt(pm.MAIN_TO_WALL)),
             ('STATIC PRESSURE AT THE MAIN, ASSUMED', '%s PSI' % pm.PRESSURE),
             ('SERVICE', '%s"' % s['service']), ('METER', '%s"' % s['meter'])]
    for n in water.unit_names(b):
        lines.append(('TRUNK TO %s, %s DEVELOPED' % (n, fmt(pm.developed_length(b, n))), '%s"' % s['trunks'][n]))
    lines += [('HEATER CONNECTIONS, COLD AND HOT', '%s"' % pm.HEATER_CONN), ('HOME RUNS, EVERY FIXTURE', '%s"' % pm.HOME_RUN)]
    for lab, val in lines:
        _fits(lab, 'Helvetica', S, width-0.5*inch, 'table row')
        c.drawString(x, y, lab); c.drawRightString(x+width, y, val); y -= LEAD
    c.setFont('Helvetica', 4.8)
    for t in ('IF DPU STATES A STATIC PRESSURE UNDER 50 PSI, OR THE MAIN IS FARTHER THAN ASSUMED, RESIZE',
              'BY TABLE E201.1 BEFORE ROUGH-IN. THE UNIT TRUNKS ARE SIZED ON THE BUILDING\'S METER.'):
        _fits(t, 'Helvetica', 4.8, width, 'table foot')
        c.drawString(x, y, t); y -= 6.2
    return y-4


# ---------------- the supply diagram ----------------
def supply_diagram(x, y, b, width):
    """The building's water supply, drawn: the main, the service, the building valve and
       meter, the split, and per unit its valve and submeter, trunk, manifolds and heater."""
    s = pm.sizes(b)
    names = water.unit_names(b)
    LAY('P-ANNO-TEXT'); c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2)
    c.drawString(x, y, 'WATER SUPPLY DIAGRAM — %s' % b.name); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= 0.14*inch
    dx = x+0.28*inch
    ss = dr.service_sleeve(dr.BUILDINGS[b.number-1])
    lines = ['PUBLIC MAIN — LOCATION, TAP AND METER SETTING PER COLUMBUS DPU, P-601 NOTE 5',
             'CURB STOP; %s" SERVICE, %s TO THE WALL ASSUMED, BELOW FROST, %s'
             % (s['service'], fmt(pm.MAIN_TO_WALL),
                'THROUGH THE FOOTING IN A SLEEVE, P-601, 5\'-0" CLEAR OF THE SEWER' if ss is None
                else 'SLEEVED FROM %s OUT, PAST THE SEWER, THROUGH THE FOOTING' % fmt(ss[0])),
             'BUILDING VALVE, THE %s" DPU METER, METER VALVE — AT THE SERVICE RISER, OPC 606.1' % s['meter']]
    for t in lines: _fits(t, 'Helvetica', S, width-(dx-x)-8, 'diagram line')
    c.setFont('Helvetica', S)
    c.drawString(dx+8, y-2, lines[0])
    under_line(c, [(dx, y), (dx, y-0.24*inch)]); valve(c, dx, y-0.12*inch, along='v'); y -= 0.24*inch
    c.setFillColor(black); c.setFont('Helvetica', S)
    c.drawString(dx+8, y-2, lines[1])
    under_line(c, [(dx, y), (dx, y-0.24*inch)]); y -= 0.24*inch
    c.setFillColor(black); c.setFont('Helvetica', S)
    c.drawString(dx+8, y-2, lines[2])
    cold_line(c, [(dx, y), (dx, y-0.30*inch)], 1.0); valve(c, dx, y-0.07*inch, along='v'); meter(c, dx, y-0.17*inch); valve(c, dx, y-0.27*inch, along='v')
    y -= 0.30*inch
    n = len(names); colw = min(2.3*inch, (width-0.1*inch)/n)
    cold_line(c, [(dx, y), (x+0.05*inch+(n-1)*colw+colw/2.0, y)], 1.0)
    c.setFillColor(black)
    for i, name in enumerate(names):
        cx = x+0.05*inch+i*colw+colw/2.0
        cold_line(c, [(cx, y), (cx, y-0.30*inch)], 1.0)
        valve(c, cx, y-0.08*inch, along='v'); meter(c, cx, y-0.20*inch, 'SM')
        c.setFont('Helvetica', 4.8); c.setFillColor(black)
        # beside the stem: to its right, or to its left in the last column so the text
        # stays inside the diagram's width
        last = (i == n-1)
        for j, t in enumerate(('%s" TRUNK, %s' % (s['trunks'][name], fmt(pm.developed_length(b, name))),
                               'VALVE + SUBMETER')):
            _fits(t, 'Helvetica', 4.8, colw/2.0-8, 'diagram column line')
            if last: c.drawRightString(cx-6, y-0.06*inch-6*j, t)
            else: c.drawString(cx+6, y-0.06*inch-6*j, t)
        by = y-0.30*inch
        c.setLineWidth(0.6); c.setFillColor(white); c.rect(cx-colw/2.0+0.06*inch, by-0.24*inch, colw-0.12*inch, 0.24*inch, fill=1, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5.2); c.drawCentredString(cx, by-0.10*inch, 'COLD MANIFOLD, %s' % name)
        cold_, hot_, tot, rows = pm.unit_wsfu(b, name)
        c.setFont('Helvetica', 4.8); c.drawCentredString(cx, by-0.19*inch, '%.1f WSFU: %.1f COLD, %.1f HOT' % (tot, cold_, hot_))
        hy = by-0.24*inch
        cold_line(c, [(cx, hy), (cx, hy-0.20*inch)], 0.8); valve(c, cx, hy-0.10*inch, along='v')
        c.setFillColor(white); c.rect(cx-colw/2.0+0.06*inch, hy-0.20*inch-0.22*inch, colw-0.12*inch, 0.22*inch, fill=1, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5.2); c.drawCentredString(cx, hy-0.30*inch, 'STORAGE HEATER, %s" C IN / %s" H OUT' % (pm.HEATER_CONN, pm.HEATER_CONN))
        c.setFont('Helvetica', 4.8); c.drawCentredString(cx, hy-0.38*inch, '%s MIXING VALVE, %s F STORED / %s F OUT, P-601 NOTE 6a' % (pm.WH_TMV_STD, pm.WH_STORE_F, pm.WH_DELIVER_F))
        my = hy-0.42*inch
        hot_line(c, [(cx-1.4, my-1.4), (cx-1.4, my-0.20*inch-1.4)])
        c.setFillColor(white); c.rect(cx-colw/2.0+0.06*inch, my-0.20*inch-0.20*inch, colw-0.12*inch, 0.20*inch, fill=1, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5.2); c.drawCentredString(cx, my-0.20*inch-0.13*inch, 'HOT MANIFOLD, %s' % name)
        ry = my-0.40*inch-0.06*inch
        c.setFont('Helvetica', 4.6)
        units = [u for u in b.units if u.name == name]
        for u in units:
            for r in u.runs:
                if r.fixtures == ('wh',): continue
                cd, ht = water.run_lines(r, u.fixtures)
                t = '%s%s: %dC + %dH %s"' % (r.group, ' (L%d)' % u.level if len(units) > 1 else '', cd, ht, pm.HOME_RUN)
                _fits(t, 'Helvetica', 4.6, colw-0.12*inch, 'diagram run line')
                c.drawCentredString(cx, ry, t); ry -= 5.6
    return y


# ---------------- the notes ----------------
NOTES = [
    "1.  SCOPE — DOMESTIC WATER ONLY: THE SERVICE, THE METER, THE TRUNK TO EACH UNIT'S MANIFOLDS, THE HEATER CONNECTIONS AND THE HOME RUNS TO EVERY FIXTURE. DRAINAGE, VENTS AND THE SIX STACKS ARE ON P-601; EVERYTHING BELOW EITHER SLAB — THE BUILDING DRAINS, THE STACK FEET AND EVERY SLAB PENETRATION — IS ON P-101, WHICH DRAWS THE SERVICE AND THE TRUNK BELOW THE SLAB IN GRAY FOR COORDINATION.",
    "2.  SERVICE — ONE PER BUILDING, FROM THE PUBLIC MAIN, UNDER THE SAGE WALL WHERE DRAWN. THE MAIN'S LOCATION, THE TAP AND THE METER SETTING ARE COLUMBUS DPU'S, P-601 NOTE 5; %s FROM THE MAIN TO THE WALL IS ASSUMED. BURY IT %s BELOW FINISHED GRADE, WHICH IS %s UNDER THE %s FROST LINE OF G-001 AND NOT LESS THAN 12\" DOWN, OPC 305.4, AND CARRY IT THROUGH THE FOOTING IN A SLEEVE, RISING INSIDE THE FOUNDATION WALL — SEE P-601, WATER SERVICE ENTRY, AND S-101 NOTE 8. KEEP 5'-0\" HORIZONTALLY CLEAR OF THE BUILDING SEWER; WHERE THE TWO CROSS, 12\" ABOVE IT, OR SLEEVED TO 5'-0\" EACH SIDE OF ITS CENTERLINE WHERE IT PASSES BELOW, OPC 603.2, P-101 NOTE 9." % (fmt(pm.MAIN_TO_WALL), inches(_SE.bury), inches(_SE.bury-_SE.frost), inches(_SE.frost)),
    "3.  METERING — BASIS SHOWN: THE DPU METER AND THE BUILDING VALVE AT THE ENTRY; A SUBMETER AND A FULL-OPEN VALVE AT EACH UNIT'S MANIFOLDS, IN ITS OWN CLOSET. FINAL TAP / METER CONFIGURATION PER COLUMBUS DPU, P-601 NOTE 5.",
    "4.  VALVES — FULL-OPEN AT THE CURB, AT THE ENTRY, ON THE METER'S DISCHARGE, AT EACH DWELLING UNIT AND ON EACH HEATER'S SUPPLY, OPC 606.1; A STOP AT EVERY FIXTURE BUT THE TUB, 606.2; EVERY MANIFOLD PORT VALVED AND LABELED WITH ITS FIXTURE, 604.10.",
    "5.  SIZING — WATER SUPPLY FIXTURE UNITS FROM TABLE E103.3(2), PRIVATE, TABULATED AT THE RIGHT; THE SERVICE, THE METER AND EACH TRUNK FROM TABLE E201.1 AT %s PSI STATIC AND THE DEVELOPED LENGTH TABULATED — IPC APPENDIX E, THE ACCEPTED PRACTICE OF OPC 604.1. IF DPU STATES A LOWER STATIC PRESSURE OR THE MAIN IS FARTHER THAN ASSUMED, RESIZE BY THE SAME TABLE BEFORE ROUGH-IN." % pm.PRESSURE,
    "6.  MATERIALS — PEX, ASTM F876 / F877, WITH FITTINGS TO ASTM F1807, F1960 OR F2080. THE UNDER-SLAB SERVICE AND TRUNK ONE CONTINUOUS LENGTH EACH, IN A SLEEVE, WITH NO JOINT BELOW THE SLAB. COPPER OR BRASS STUB-OUTS AT THE FIXTURES. KEEP PEX CLEAR OF EACH HEATER AS ITS MANUFACTURER REQUIRES.",
    "7.  ROUTING — NOTHING IN ANY MEMBRANE OF W4A OR W4B, P-601 NOTE 2: THE UNITS 2 AND 3 TRUNK CROSSES THE SEPARATION LINE BELOW THE SLAB, IN ITS SLEEVE. THE UNIT 3 AND UNIT 5 RISERS ARE IN THE STACKED MECHANICAL CLOSETS AND CROSS THE F1 FLOOR ONCE EACH, FIRESTOPPED PER A-001 NOTE 4a. HOME RUNS ARE IN THE UNIT'S OWN WALLS AND IN THE FLOOR-CEILING SPACE ABOVE A LEVEL 1 UNIT OR BELOW A LEVEL 2 UNIT: NONE IN THE ATTIC, NONE IN AN EXTERIOR WALL, NONE THROUGH A PANEL'S WORKING SPACE, NEC 110.26(E).",
    "8.  WATER HEATERS — THE FLOOR-STANDING ELECTRIC STORAGE HEATER OF P-601 NOTES 6 AND 6a IN EACH UNIT, %s\" COLD IN AND %s\" HOT OUT, WITH FULL-PORT ISOLATION VALVES ON BOTH AND A COLD-SIDE EXPANSION TANK. TEMPERATURE AND PRESSURE RELIEF, AND THE DRAIN PANS UNITS %s TAKE, PER P-601 NOTE 7. NO VENT AND NO CONDENSATE." % (pm.HEATER_CONN, pm.HEATER_CONN, " AND ".join(u.split()[-1] for u in pm.WH_PAN_UNITS)),
    "9.  HOT WATER — TUB AND SHOWER VALVES PRESSURE-BALANCING OR THERMOSTATIC, LIMITED TO 120 F, OPC 424.3. HOT-WATER PIPING INSULATED TO R-3 WHERE RCO N1103.5.3 REQUIRES IT: EVERY 3/4\" LINE, THE HEATER-TO-MANIFOLD LINES AND THE RUNS TO THE KITCHENS.",
    "10. WATER HAMMER — ARRESTORS TO ASSE 1010 AT EACH CLOTHES WASHER AND DISHWASHER, OPC 604.9.",
    "11. TESTING — THE SYSTEM TESTED PER OPC 312.5 BEFORE ANY OF IT IS CONCEALED.",
    "12. ALL WORK BY A CONTRACTOR HOLDING AN OHIO OCILB PLUMBING LICENSE AND REGISTERED WITH THE CITY OF COLUMBUS, UNDER THE SEPARATE TRADE PERMIT OF P-601 NOTE 9.",
]


def notes(x, y, width, cols=2, size=S, lead=7.4, see=None):
    """The twelve notes, re-flowed into `cols` columns of the given total width."""
    return notes_block(x, y, width, NOTES, 'WATER SUPPLY NOTES', 'P-ANNO-TEXT', 'water supply note', cols, size, lead, 0.18*inch, see)

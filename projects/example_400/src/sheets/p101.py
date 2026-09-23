"""P-101 — sanitary / under-slab plumbing plans: both Level 1 plans greyed, S-101's
strips and the water below the slab in grey, and on them every drain below either
slab, the feet of the stacks, every slab penetration with its mark, the tub
box-outs, the floor cleanouts and the two exits; the legend, the drainage fixture-unit
and pipe-size table, the slab penetration schedules, the invert table and the notes.
Every figure printed here is read from src/drainage.py, which check_model() has
already passed."""
import math
from lib.draw.page import GREY, LAY, LGREY, Sheet, end_plans
from lib.draw.sheets import draw_level
from lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src import drainage as dr
from lib.model import drains as drains
from codes.ohio import opc_drainage as opc_drainage
from lib.model import runs as runs
from src import levels
from src import radon as RN
from src.building1 import B1_D, B1_W, b1_level
from src.building2 import B2_D, B2_W, b2_level
from src.sheets.a101 import draw_b1_stair
from src.sheets.a102 import draw_u5_stair
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from lib.draw.kit import _fits, title
from lib.draw.plumbing_kit import run_label
from lib.draw.drainage_kit import (WIDTH, _P, _at, _between, _dim, _text, box_out, cleanout, drain_line,
                                   flow_arrow, junction, pen_mark, sleeve_line, stack_tag, strip_band)
from codes.ohio import opc_separation
from lib.draw.drainage_kit import S, notes
from functools import partial
from lib.draw.drainage_kit import _serves_text as _shared_serves_text
from lib.draw.drainage_kit import water_line

KIND = {'stack': 'STACK FOOT', 'wc': 'CLOSET FLANGE', 'tub': 'TUB TRAP, BOX-OUT', 'drop': 'DRAIN DROP',
        'co': 'FLOOR CLEANOUT', 'exit': 'EXIT, SLEEVED'}
FIX = {'sink': 'KITCHEN SINK', 'wc': 'WATER CLOSET', 'tub': 'TUB', 'shower': 'SHOWER', 'lav': 'LAVATORY', 'wd': 'WASHER STANDPIPE'}


# ---------------- the symbols, at page points ----------------


def radon_mark(cc, X, Y):
    """A radon riser's tee, S-101: a grey ringed dot, drawn here for clearance only."""
    LAY('S-FNDN-RADN'); cc.setStrokeColor(GREY); cc.setFillColor(white); cc.setLineWidth(0.7)
    cc.circle(X, Y, 3.0, fill=1, stroke=1)
    cc.setFillColor(GREY); cc.circle(X, Y, 1.1, fill=1, stroke=0)
    cc.setStrokeColor(black); cc.setFillColor(black)


# ---------------- a building's drainage on its plan ----------------
def _label_for(b, run):
    return '%s" @ 1/%d" PER FT' % (run.size, round(1/dr.slope_of(run)))


def draw_building(p, b, water_note):
    cc = p.c
    for rect, nm in dr.strips(b):
        strip_band(p, rect, '%s STRIP, S-101' % nm)
    for a, bb in dr.water_below(b):
        water_line(cc, [_P(p, a), _P(p, bb)])
    _text(cc, *water_note[0], water_note[1], 3.4, anchor='l', col=GREY)
    # each sleeve, drawn as far as SEWER_SEP past the crossings on this plan, with its
    # reach either side of them; where it runs on past that, the label says how far
    lines = dict(dr.water_lines(b))
    here = [(nm, runs.along(lines[nm], x)) for _r, nm, x, kind in opc_separation.water_crossings(b, dr.GROUND) if kind == 'sleeved']
    for nm, lo, hi in opc_separation.sleeves(b, dr.GROUND):
        ts = [t for n, t in here if n == nm and lo-1e-6 <= t <= hi+1e-6]
        if not ts: continue
        dlo = max(lo, min(ts)-opc_separation.SEWER_SEP)
        pts = [_P(p, q) for q in _between(lines[nm], dlo, hi)]
        water_line(cc, pts); sleeve_line(cc, pts)
        for t in ts:
            C, L0, L1 = _P(p, _at(lines[nm], t)), _P(p, _at(lines[nm], max(dlo, t-opc_separation.SEWER_SEP))), _P(p, _at(lines[nm], min(hi, t+opc_separation.SEWER_SEP)))
            _dim(cc, L0[0], C[0], C[1]+8.0, fmt(t-max(dlo, t-opc_separation.SEWER_SEP)))
            _dim(cc, C[0], L1[0], C[1]+8.0, fmt(min(hi, t+opc_separation.SEWER_SEP)-t))
        ss = dr.service_sleeve(b) if nm == 'SERVICE' else None
        if ss is not None:
            _text(cc, water_note[0][0], water_note[0][1]+4.6,
                  'SLEEVED FROM %s OUTSIDE THE WALL, %s PAST THE BUILDING SEWER, TO THE RISER, NOTE 9' % (fmt(ss[0]), fmt(opc_separation.SEWER_SEP)),
                  3.4, anchor='l', col=GREY)
    # the runs: heaviest first so a branch's end sits on its drain
    for r in sorted(b.runs, key=lambda r: -opc_drainage.SIZE_IN[r.size]):
        pts = [_P(p, q) for q in r.path]
        drain_line(cc, pts, r.size)
        a, bb = max(zip(pts, pts[1:]), key=lambda s: math.hypot(s[1][0]-s[0][0], s[1][1]-s[0][1]))
        if math.hypot(bb[0]-a[0], bb[1]-a[1]) >= 30: flow_arrow(cc, a, bb)
        run_label(cc, pts, _label_for(b, r), size=3.6)
        rec = drains.receiver(b, r)
        if rec not in (None, 'exit', 'ambiguous'): junction(cc, *pts[-1])
    for nm, pt in ((nm, pt) for _r, nm, pt in opc_separation.strip_crossings(b, dr.GROUND)):
        X, Y = _P(p, pt)
        _text(cc, X+4, Y-1.2, 'BELOW THE STRIP, SLEEVED', 3.0, anchor='l')
    for _r, _nm, pt, kind in opc_separation.water_crossings(b, dr.GROUND):
        X, Y = _P(p, pt)
        if kind == 'above':
            _text(cc, X+4, Y+9.6, 'WATER ABOVE THE DRAIN,', 3.0, anchor='l', col=GREY)
            _text(cc, X+4, Y+6.0, '%s MIN. VERTICAL' % inches(opc_separation.VERT_CLEAR), 3.0, anchor='l', col=GREY)
            _text(cc, X+4, Y+2.4, 'CLEARANCE, OPC 603.2', 3.0, anchor='l', col=GREY)
        else:
            _text(cc, X+4, Y-6.4, 'WATER BELOW IN ITS SLEEVE, OPC 603.2', 3.0, anchor='l', col=GREY)
    for r in [r for r in RN.RISERS if r.building == b.name]:      # the radon risers, S-101's, for clearance
        for l in r.laterals:
            pts = [_P(p, q) for q in l.path]
            LAY('S-FNDN-RADN'); cc.setStrokeColor(GREY); cc.setLineWidth(0.7); cc.setDash(3, 2)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]): cc.line(x0, y0, x1, y1)
            cc.setDash(); cc.setStrokeColor(black)
        X, Y = _P(p, r.pos)
        radon_mark(cc, X, Y)
        left = r.pos[0] > b.W/2.0
        _text(cc, X+(-4.5 if left else 4.5), Y+3.4, '%s RADON, S-101' % r.mark, 3.0, anchor='r' if left else 'l', col=GREY)
    for s in b.stacks:
        X, Y = _P(p, s.pos)
        if s.foot is not None:
            foot = next(pn for pn in b.pens if pn.mark == s.foot)
            if not runs.same_point(foot.pos, s.pos):
                FX, FY = _P(p, foot.pos)
                LAY('P-SANR-UNDR'); cc.setStrokeColor(black); cc.setLineWidth(WIDTH[s.size]); cc.setDash(); cc.line(X, Y, FX, FY)
        stack_tag(cc, X, Y, s.name)
        # its label above the hexagon, toward the middle of the plan, clear of the marks beside it
        side = -1 if s.pos[0] > b.W/2.0 else 1
        t = '%s" %s %s' % (s.size, 'VENT' if s.foot is None else 'STACK', s.name)
        _text(cc, X+1*side, Y+7.0, t, 3.4, bold=True, anchor='l' if side > 0 else 'r')
    for pn in b.pens:
        X, Y = _P(p, pn.pos)
        if pn.box is not None:
            bx, by, bw, bh = pn.box
            box_out(cc, p.X(bx), p.Y(by+bh), bw*p.sc, bh*p.sc)
        if pn.kind == 'exit':
            out = (-1, 0) if pn.pos[0] < 1e-6 else (1, 0) if pn.pos[0] > b.W-1e-6 else (0, 1) if pn.pos[1] > b.D-1e-6 else (0, -1)
            LAY('P-SANR-UNDR'); cc.setStrokeColor(black); cc.setLineWidth(WIDTH[pn.size]); cc.setDash()
            E = (X+out[0]*0.9*p.sc, Y-out[1]*0.9*p.sc)
            cc.line(X, Y, E[0], E[1]); flow_arrow(cc, (X, Y), E, at=0.7)
            if out == (0, 1):
                _text(cc, X+6, Y-9, '%s" TO THE BUILDING SEWER, C-101' % pn.size, 3.4, bold=True, anchor='l')
                _text(cc, X+6, Y-14, 'SLEEVED THROUGH THE FOUNDATION WALL, NOTE 6', 3.0, anchor='l')
            else:
                # outside the wall, past the arrow: short lines, the next plan or the legend is close
                side, tx = ('l', E[0]+3) if out[0] > 0 else ('r', E[0]-3)
                _text(cc, tx, Y+5.5, '%s" TO THE SEWER, C-101' % pn.size, 3.4, bold=True, anchor=side)
                _text(cc, tx, Y-8.5, 'SLEEVED, NOTE 6', 3.0, anchor=side)
            continue
        if pn.kind == 'co':
            cleanout(cc, X, Y)
            pen_mark(cc, X+8, Y+6, pn.mark)
            continue
        if pn.kind == 'stack':
            side = 1 if pn.pos[0] < 3.0 or pn.pos[0] > b.W/2.0 else -1
            pen_mark(cc, X+11*side, Y, pn.mark)
            continue
        if pn.box is not None:
            # the mark at the box-out's centre, off the drain and the stack foot beside it
            pen_mark(cc, p.X(pn.box[0]+pn.box[2]/2.0), p.Y(pn.box[1]+pn.box[3]/2.0), pn.mark)
            continue
        pen_mark(cc, X, Y, pn.mark)


# ---------------- the legend ----------------
LEGEND = [
    ('drain', 'DRAIN BELOW THE SLAB, SIZE AND SLOPE LABELED; THE ARROW FALLS'),
    ('water', 'WATER BELOW THE SLAB, P-102 / P-103; KEEP 12" CLEAR, NOTE 9'),
    ('sleeve', 'WATER IN ITS SLEEVE WHERE IT PASSES BELOW A DRAIN, OPC 603.2, NOTE 9'),
    ('strip', 'THICKENED BEARING STRIP, S-101; CROSS BELOW IT, NOTE 6'),
    ('stack', 'STACK IN ITS WALL, P-601; A LINE TO ITS FOOT IS THE OFFSET, NOTE 8'),
    ('pen',   'SLAB PENETRATION, NUMBERED IN THE SCHEDULE UNDER ITS PLAN'),
    ('box',   'TUB TRAP BOX-OUT, 12" x 12" IN THE SLAB'),
    ('radon', 'RADON RISER TEE AND LATERAL, S-101, IN THE AGGREGATE OVER THE DRAINS'),
    ('exit',  'THE BUILDING DRAIN OUT THROUGH THE WALL TO THE SEWER, C-101'),
    ('junc',  'A BRANCH ENTERING ITS DRAIN: WYE AND EIGHTH BEND'),
]


def legend(x, y, width, lead=13.0):
    cc = c
    _text(cc, x, y, 'SANITARY LEGEND', S+2.4, bold=True, anchor='l'); y -= lead+3
    for k, t in LEGEND:
        _fits(t, 'Helvetica', S, width-26, 'legend line')
        X, Y = x+2, y+S*0.36
        if k == 'drain': drain_line(cc, [(X, Y), (X+18, Y)], '3'); flow_arrow(cc, (X, Y), (X+18, Y), size=3.4)
        elif k == 'water': water_line(cc, [(X, Y), (X+18, Y)])
        elif k == 'sleeve': water_line(cc, [(X, Y), (X+18, Y)]); sleeve_line(cc, [(X, Y), (X+18, Y)])
        elif k == 'strip':
            LAY('S-FNDN'); cc.setFillColor(LGREY); cc.setStrokeColor(GREY); cc.setLineWidth(0.5); cc.setDash(3, 2)
            cc.rect(X, Y-3, 18, 6, fill=1, stroke=1); cc.setDash(); cc.setStrokeColor(black); cc.setFillColor(black)
        elif k == 'stack': stack_tag(cc, X+9, Y, 'B')
        elif k == 'pen': pen_mark(cc, X+9, Y, 1)
        elif k == 'box': box_out(cc, X+3, Y-5, 12, 10)
        elif k == 'radon': radon_mark(cc, X+9, Y)
        _text(cc, x+26, y, t, S, anchor='l')
        y -= lead
    return y


# ---------------- the fixture-unit and pipe-size table ----------------
def dfu_table(x, y, width):
    """Per dwelling, its fixtures and their DFU by Table 709.1; the building totals;
       then what each stack and each building drain carries against its table."""
    LEAD = 7.6
    cols = (width-1.0*inch, width-0.5*inch, width)
    _text(c, x, y, 'DRAINAGE FIXTURE UNITS — OPC TABLE 709.1, 1.6 GPF WATER CLOSETS', 7.2, bold=True, anchor='l'); y -= 3
    c.setLineWidth(0.6); c.setStrokeColor(black); c.line(x, y, x+width, y); y -= LEAD+1
    c.setFillColor(black); c.setFont('Helvetica-Bold', S); c.drawString(x, y, 'FIXTURE')
    for t, cx in zip(('QTY', 'DFU'), cols[1:]): c.drawRightString(x+cx, y, t)
    y -= LEAD
    for b in dr.BUILDINGS:
        for n in dr.unit_names(b):
            tot, rows = opc_drainage.unit_dfu(dr._pm(b), n)
            c.setFont('Helvetica-Bold', S); c.drawString(x, y, n); y -= LEAD
            c.setFont('Helvetica', S)
            for label, q, v in rows:
                _fits(label, 'Helvetica', S, cols[0], 'table row')
                c.drawString(x+6, y, label)
                c.drawRightString(x+cols[1], y, str(q)); c.drawRightString(x+cols[2], y, str(v)); y -= LEAD
            c.setFont('Helvetica-Bold', S); c.drawString(x+6, y, '%s, DFU' % n); c.drawRightString(x+cols[2], y, str(tot)); y -= LEAD+1
        c.setLineWidth(0.3); c.line(x, y+LEAD-2, x+width, y+LEAD-2)
        c.setFont('Helvetica-Bold', S); c.drawString(x, y, '%s, DFU' % b.name); c.drawRightString(x+cols[2], y, str(dr.building_dfu(b))); y -= LEAD+2
    c.setFont('Helvetica-Bold', S); c.drawString(x, y, 'BOTH BUILDINGS, DFU'); c.drawRightString(x+cols[2], y, str(dr.total_dfu())); y -= LEAD+3
    # sizes
    c.setLineWidth(0.3); c.line(x, y+LEAD-2, x+width, y+LEAD-2)
    _text(c, x, y, 'SIZES — PIPES CARRY THE FIXTURES ON THEM, THE GROUP VALUE WHERE WHOLE', S, bold=True, anchor='l'); y -= LEAD
    c.setFont('Helvetica', S)
    for b in dr.BUILDINGS:
        for s in b.stacks:
            if s.foot is None:
                lines = [('%s" VENT %s — %s' % (s.size, s.name, 'NO DRAINAGE LOAD; BATH 1 AND THE LAUNDRY VENT INTO IT, P-601'), '')]
            else:
                per = max(opc_drainage.interval_dfu(k) for _u, _l, k in s.serves)
                lines = [('%s" STACK %s — %d DFU OF %d, TABLE 710.1(2); %d IN ONE INTERVAL OF %d'
                          % (s.size, s.name, opc_drainage.stack_dfu(s), opc_drainage.T710_1_2[s.size][2], per, opc_drainage.T710_1_2[s.size][1]), '')]
            for lab, val in lines:
                _fits(lab, 'Helvetica', S, width, 'sizes row'); c.drawString(x, y, lab); y -= LEAD
        xr = drains.exit_run(b)
        col = opc_drainage.SLOPES.index(dr.slope_of(xr))
        lab = '%s BUILDING DRAIN — %s" AT 1/%d" PER FT, %d DFU OF %d, TABLE 710.1(1)' % (
            b.name, xr.size, round(1/dr.slope_of(xr)), opc_drainage.run_dfu(b, xr), opc_drainage.T710_1_1[xr.size][col])
        _fits(lab, 'Helvetica', S, width, 'sizes row'); c.setFont('Helvetica-Bold', S); c.drawString(x, y, lab); c.setFont('Helvetica', S); y -= LEAD
    for lab in ('EVERY BRANCH IS SIZED THE SAME WAY; 2" AT 1/4" PER FT CARRIES 21 DFU.',
                'NO 2" DRAIN CARRIES A WATER CLOSET. A DISHWASHER DISCHARGES THROUGH',
                'ITS SINK\'S TRAP ARM AND IS COUNTED IN THE SINK\'S ROW.'):
        _fits(lab, 'Helvetica', 4.8, width, 'table foot'); c.setFont('Helvetica', 4.8); c.drawString(x, y, lab); y -= 6.2
    return y-4


# ---------------- the slab penetration schedule ----------------


_serves_text = partial(_shared_serves_text, fix=FIX)


def _face_text(b, pn):
    """The exit is on a face, said in words rather than as a coordinate on it."""
    if pn.kind != 'exit': return None
    if pn.pos[0] < 1e-6: return 'NORTH FACE'
    if pn.pos[1] > b.D-1e-6: return 'REAR FACE'
    if pn.pos[0] > b.W-1e-6: return 'SOUTH FACE'
    return 'FRONT FACE'


def pen_schedule(x, y, b, width, front):
    """Every hole through this building's slab: what it is, what it serves, its size,
       and its two coordinates from the outside faces, so the crew can lay it out."""
    LEAD = 7.4
    cols = (0.28*inch, 1.25*inch, 3.05*inch, 3.55*inch, 4.35*inch)   # KIND, SERVES, SIZE, X, Y starts
    assert cols[-1]+0.85*inch <= width, 'P-101 schedule is wider than its column'
    _text(c, x, y, '%s — SLAB PENETRATIONS' % b.name, 7.2, bold=True, anchor='l'); y -= 3
    c.setLineWidth(0.6); c.setStrokeColor(black); c.line(x, y, x+width, y); y -= LEAD+1
    c.setFillColor(black); c.setFont('Helvetica-Bold', S)
    for t, cx in zip(('NO.', 'WHAT', 'SERVES', 'SIZE', 'FROM NORTH', 'FROM %s' % front), (0,)+cols):
        c.drawString(x+cx, y, t)
    y -= LEAD
    c.setFont('Helvetica', S)
    for pn in b.pens:
        face = _face_text(b, pn)
        what = KIND[pn.kind]
        serves = _serves_text(b, pn)
        xs = fmt(pn.pos[0]) if face not in ('NORTH FACE', 'SOUTH FACE') else face
        ys = fmt(pn.pos[1]) if face not in ('REAR FACE', 'FRONT FACE') else face
        for t, cx, lim in ((str(pn.mark), 0, cols[0]), (what, cols[0], cols[1]-cols[0]), (serves, cols[1], cols[2]-cols[1]),
                           ('%s"' % pn.size, cols[2], cols[3]-cols[2]), (xs, cols[3], cols[4]-cols[3]), (ys, cols[4], width-cols[4])):
            _fits(t, 'Helvetica', S, lim-3, 'schedule cell')
            c.drawString(x+cx, y, t)
        y -= LEAD
    c.setFont('Helvetica', 4.8)
    for t in ('COORDINATES ARE TO THE PIPE\'S CENTER FROM THE OUTSIDE FACE OF THE FOUNDATION WALL. A CLOSET FLANGE IS 12" OFF ITS FINISHED WALL;',
              'A TUB OR SHOWER TRAP IS AT THE FIXTURE\'S DRAIN. VERIFY EACH AGAINST THE SELECTED FIXTURE BEFORE THE POUR, NOTE 5.'):
        _fits(t, 'Helvetica', 4.8, width, 'schedule foot'); c.drawString(x, y, t); y -= 6.2
    return y-4


# ---------------- the invert table ----------------
def invert_table(x, y, width):
    LEAD = 7.6
    s = dr.sewer()
    _text(c, x, y, 'INVERTS — FROM %s OF COVER OVER THE HIGHEST PIPE' % inches(dr.COVER), 7.2, bold=True, anchor='l'); y -= 3
    c.setLineWidth(0.6); c.setStrokeColor(black); c.line(x, y, x+width, y); y -= LEAD+1
    c.setFont('Helvetica', S); c.setFillColor(black)
    rows = [('SLAB TOP ABOVE FINISHED GRADE', inches(levels.SLAB_TOP)),
            ('FOOTING TOP BELOW FINISHED GRADE, S-101', inches(-dr.FOOTING_TOP))]
    for b in dr.BUILDINGS:
        rows.append(('%s EXIT INVERT BELOW SLAB TOP' % b.name, inches(-opc_drainage.exit_invert(b, cover=dr.COVER))))
        rows.append(('   THE SAME, BELOW FINISHED GRADE — THROUGH THE WALL, ABOVE THE FOOTING', inches(-dr.below_grade(opc_drainage.exit_invert(b, cover=dr.COVER)))))
    rows += [('BUILDING SEWER ON THE LOT, C-101, AT 1/%d" PER FT' % round(1/dr.SEWER_SLOPE), fmt(s['on_lot'])),
             ('   TO A MAIN TAKEN %s PAST THE OAK AVENUE LOT LINE' % fmt(dr.MAIN_TO_LOT), fmt(s['to_main'])),
             ('   FALL TO THE MAIN', inches(s['fall'])),
             ('BUILDING 1 LATERAL, %s TO THE SEWER: FALL AVAILABLE' % fmt(runs.length(s['lateral'])), inches(s['lateral_fall'])),
             ('THE OAK AVENUE MAIN\'S INVERT, AT OR BELOW, BELOW FINISHED GRADE', inches(-s['main_max']))]
    for lab, val in rows:
        bold = lab.startswith('THE OAK')
        c.setFont('Helvetica-Bold' if bold else 'Helvetica', S)
        _fits(lab, 'Helvetica-Bold' if bold else 'Helvetica', S, width-0.6*inch, 'invert row')
        c.drawString(x, y, lab); c.drawRightString(x+width, y, val); y -= LEAD
    c.setFont('Helvetica', 4.8)
    for t in ('VERIFY THE MAIN INVERT AT OR BELOW %s BELOW FINISHED GRADE BEFORE EITHER SLAB IS POURED;' % inches(-dr.sewer()['main_max']),
              'NOTIFY THE DESIGNER IF HIGHER. SIZE INCREASES ARE CROWN TO CROWN.'):
        _fits(t, 'Helvetica', 4.8, width, 'invert foot'); c.drawString(x, y, t); y -= 6.2
    return y-4


# ---------------- the notes ----------------
def notes_text():
    s = dr.sewer()
    return [
        "1.  SCOPE — EVERYTHING BELOW EITHER SLAB: THE BUILDING DRAINS, THEIR BRANCHES, THE FEET OF THE STACKS AND EVERY PLUMBING PENETRATION OF THE SLAB. THE RADON RISERS AND THE LATERAL, GRAY, LIE IN THE AGGREGATE OVER THE DRAINS: SEE S-101. THE STACKS, THE VENTS AND WHAT EACH FIXTURE IS ON: SEE P-601. THE WATER BELOW THE SLAB, SHOWN GRAY: SEE P-102 AND P-103. THE BUILDING SEWER FROM THE WALLS TO THE OAK AVENUE MAIN: SEE C-101.",
        "2.  MATERIAL — PVC DWV SCHEDULE 40, ASTM D2665, SOLVENT-CEMENTED TO ASTM D2564 WITH PRIMER; FITTINGS DWV PATTERN, LONG-SWEEP WHERE A STACK TURNS HORIZONTAL. BEDDED ON AND COVERED BY 4\" OF COMPACTED GRANULAR MATERIAL, OPC 306.2 AND 306.3; NO PIPE CAST IN CONCRETE; NO PIPE BEARS ON A ROCK OR A FITTING.",
        "3.  SLOPE — 2\" AT 1/4\" PER FOOT, 3\" AND LARGER AT 1/8\", OPC 704.1, UNIFORM BETWEEN FITTINGS. STEEPER IS PERMITTED WHERE THE MAIN'S INVERT ALLOWS IT; FLATTER IS NOT.",
        "4.  INVERTS — TABULATED FROM %s OF COVER OVER THE TOP OF THE HIGHEST PIPE, THE DRAWN LENGTHS AND THE SLOPES, WITH SIZE INCREASES CROWN TO CROWN. THE EXITS ARE %s AND %s BELOW FINISHED GRADE, THROUGH THE FOUNDATION WALL ABOVE THE FOOTING. THE MAIN'S INVERT: SEE THE INVERT TABLE." % (
            inches(dr.COVER), inches(-s['exit1']), inches(-s['exit2'])),
        "5.  PENETRATIONS — LOCATED IN THE SCHEDULES FROM THE OUTSIDE FACES OF THE FOUNDATION WALLS. SLEEVE EVERY PIPE THROUGH THE SLAB, OPC 305.4; BOX OUT THE SLAB 12\" x 12\" AT THE TUB AND SHOWER TRAPS; CLOSET FLANGES 12\" OFF THE FINISHED WALL, SET AFTER THE POUR ON THE STUBBED RISER. VERIFY EVERY LOCATION AGAINST THE SELECTED FIXTURES' ROUGH-IN DIMENSIONS BEFORE THE POUR.",
        "6.  STRIPS AND WALLS — WHERE A DRAIN PASSES A THICKENED STRIP OF S-101 IT CROSSES AT A RIGHT ANGLE, BELOW THE STRIP, IN A SLEEVE TWO PIPE SIZES LARGER, THE CONCRETE NOT BEARING ON THE PIPE, OPC 305.3; NOTHING RUNS ALONG A STRIP. THE EXITS ARE SLEEVED THROUGH THE FOUNDATION WALL, 6\" SLEEVE ON THE 4\", THE ANNULUS SEALED.",
        "7.  CLEANOUTS — AT THE BASE OF EVERY STACK, IN THE STACK ABOVE THE SLAB, OPC 708.1.4; A TWO-WAY EXTERIOR CLEANOUT WHERE EACH BUILDING DRAIN MEETS THE SEWER AND ONE INSIDE THE OAK LOT LINE, C-101, 708.1.3. TRAP ARMS ARE CLEANED THROUGH THEIR TRAPS, 708.1.10.",
        _stack_feet_note(),
        _water_note(),
        "10. TESTING — WATER TEST TO OPC 312.2, 10 FT HEAD FOR 15 MINUTES, ON ALL PIPING BELOW THE SLAB BEFORE BACKFILL AND AGAIN BEFORE THE POUR; INSPECTION BEFORE EITHER. CAP EVERY STUB ABOVE THE SLAB.",
        "11. ALL WORK BY A CONTRACTOR HOLDING AN OHIO OCILB PLUMBING LICENSE AND REGISTERED WITH THE CITY OF COLUMBUS, UNDER THE SEPARATE TRADE PERMIT OF P-601 NOTE 9.",
    ]


def _stack_feet_note():
    """Note 8. The offset each stack makes to its foot is DRAWN here, so the figures are read
       from the model; the rule that lets stacks E and F make one -- 913.2 permits no offset
       between a waste stack vent's lowest and highest fixture connection, and these are made
       at the slab, under both -- has its home on P-601."""
    off = {}
    for b in dr.BUILDINGS:
        for st in b.stacks:
            if st.foot is None:
                continue
            foot = next(p for p in b.pens if p.mark == st.foot)
            d = abs(foot.pos[0]-st.pos[0])+abs(foot.pos[1]-st.pos[1])
            if d > 1e-6:
                off[st.name] = inches(d)
    return ("8.  STACK FEET — EACH STACK TURNS HORIZONTAL BELOW THE SLAB WITH A LONG-SWEEP BEND OR TWO EIGHTH BENDS "
            "AND PASSES THROUGH THE SLAB AT THE FOOT DRAWN. STACK A STANDS IN THE FURRED CHASE DRAWN ON A-101 AT THE "
            "FRONT END OF THE KITCHEN RUN AND OFFSETS %s TO ITS FOOT. STACK E STANDS IN THE CHASE DRAWN ON A-102 AT "
            "THE BACK OF THE KITCHEN COUNTER, PAST THE WINDOW, AND OFFSETS %s; STACK F STANDS AT THE NORTH WALL "
            "BEHIND THE WASHER, INSIDE THE WALL'S INSULATION AND OVER THE 8\" FOUNDATION WALL, AND OFFSETS %s, CLEAR "
            "OF THE WALL AND ITS FOOTING. EVERY OFFSET IS MADE AT THE SLAB; ON THE WASTE STACK VENTS OF P-601 NOTE 1z "
            "THAT IS BELOW THE LOWEST FIXTURE CONNECTION, CLEAR OF THE SPAN 913.2 ALLOWS NO OFFSET IN. B IS A VENT."
            % (off['A'], off['E'], off['F']))


def _water_note():
    """Note 9, read from the crossings. The sentence is written for a lot whose water and
       sewer never meet; if a crossing appears, the build stops here rather than print a
       note that no longer holds."""
    for b in dr.BUILDINGS:
        assert not opc_separation.water_crossings(b, dr.GROUND) and not opc_separation.site_crossings(b, dr.GROUND) and dr.service_sleeve(b) is None, \
            'P-101 note 9 no longer describes the crossings: %s has one' % b.name
    keeps = min(dr.service_to_sewer(b) for b in dr.BUILDINGS)
    assert keeps >= opc_separation.SEWER_SEP, 'P-101 note 9: the water is within %s of the sewer' % fmt(opc_separation.SEWER_SEP)
    return ("9.  WATER — EACH BUILDING'S SUPPLY BELOW ITS SLAB IS DRAWN GRAY FROM P-102 / P-103. THE WATER COMES DOWN THE NORTH SIDE "
            "YARD AND THE SEWER GOES OUT DOWN THE SOUTH: NO DRAIN CROSSES THE WATER BELOW EITHER SLAB OR ON THE LOT, NONE RUNS WITHIN "
            "12\" OF IT, AND THE TWO KEEP %s OR MORE APART OUTSIDE THE WALLS, OPC 603.2. A CROSSING MADE IN THE FIELD PUTS THE WATER "
            "%s ABOVE THE DRAIN OR SLEEVES IT %s EACH SIDE. EACH SUPPLY PASSES THROUGH ITS FOOTING IN A SLEEVE, NOT THROUGH THE "
            "WALL, AND RISES INSIDE — SEE P-601, WATER SERVICE ENTRY." % (fmt(math.floor(keeps)), inches(opc_separation.VERT_CLEAR), fmt(opc_separation.SEWER_SEP)))




# ---------------- the sheet ----------------
def _level_b1(ox, oy):
    lv = b1_level(1)
    lv.over_plan = lambda pp: draw_b1_stair(pp, 1)
    def sanitary(p):
        draw_building(p, dr.BUILDING_1, ((p.X(0.9), p.Y(25.1)), 'WATER SUPPLY BELOW THE SLAB, P-102'))
        grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'BUILDING 2 AND THE ALLEY BEYOND', '396 OAK AVE', '404 OAK AVE')
    lv.overlay = sanitary
    return draw_level(c, lv, ox, oy)


def _level_b2(ox, oy):
    lv = b2_level(1)
    lv.over_plan = lambda pp: draw_u5_stair(pp, B2_W, above=True)
    def sanitary(p):
        draw_building(p, dr.BUILDING_2, ((p.X(0.9), p.Y(19.5)), 'WATER SUPPLY BELOW THE SLAB, P-103'))
        grey_context(p, B2_W, B2_D, 'COURTYARD  ·  FACES BUILDING 1  ·  OAK AVENUE BEYOND',
                     'PARKING AND ALLEY', '396 OAK AVE', '404 OAK AVE', top_off=5.6)
    lv.overlay = sanitary
    return draw_level(c, lv, ox, oy)


def sheet_p101():
    sh = Sheet(c, "P-101", "Sanitary / under-slab plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-0.9*inch-B2_D*Q             # the Unit 3 stair stands above Building 2's courtyard face
    ox1 = X0+1.0*inch
    ox2 = ox1+B1_W*Q+1.6*inch
    _level_b1(ox1, oy)
    _level_b2(ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — SANITARY BELOW THE SLAB  ·  UNIT 1')
    title(ox2, oy, 'BUILDING 2 — SANITARY BELOW THE SLAB  ·  UNIT 2; UNIT 3\'S STACKS')
    # the right column: legend, the fixture units and sizes, the inverts
    rx = ox2+B2_W*Q+0.9*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(rx, ry, rw)-6
    ry = dfu_table(rx, ry, rw)
    low = invert_table(rx, ry-4, rw)
    assert low >= Y0, "P-101 right column runs off the sheet by %.2f in" % ((Y0-low)/inch)
    # under each plan its penetration schedule, then the notes across both
    sw = B1_W*Q+1.3*inch
    by = oy-1.22*inch
    l1 = pen_schedule(ox1, by, dr.BUILDING_1, sw, 'FRONT')
    l2 = pen_schedule(ox2, by, dr.BUILDING_2, sw, 'COURTYARD')
    low = notes(ox1, min(l1, l2)-6, rx-0.4*inch-ox1, cols=3, notes_text=notes_text)
    assert low >= Y0, "P-101 notes run off the sheet by %.2f in" % ((Y0-low)/inch)
    c.showPage()

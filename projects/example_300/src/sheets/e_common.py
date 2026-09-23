"""What E-101 and E-102 share: putting a unit's devices on a greyed plan, the panel
schedules, the one-line diagram and the notes. Every figure printed here is read from
src/electrical.py, which check_model() has already passed."""
from arkitect.lib.draw.page import LAY, GREY
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.symbols import electrical as es
from arkitect.lib.units import inches
from arkitect.codes.columbus.legends import DEVICE_KINDS
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.electrical import CIRCUITS_HOUSE, CIRCUITS_U1, CIRCUITS_U23, CIRCUITS_U45, HOUSE_VA, NEC_UNITS
from arkitect.codes.nec.load import GEC_CEE, feeders, service_loads
from arkitect.codes.nec.load import nec220_82
from arkitect.codes.nec.dwelling import panel_spaces
from arkitect.lib.draw.kit import c
from arkitect.lib.draw.kit import _fits, title
from arkitect.lib.draw.kit import notes_block

def legend(p, x, y, devs, width):
    kinds = [k for k in DEVICE_KINDS if any(d.kind == k for d in devs)]
    for k in kinds:
        w = pdfmetrics.stringWidth(DEVICE_KINDS[k], 'Helvetica', 5.6)
        assert 20+w <= width, 'legend line runs out of its column: %r' % DEVICE_KINDS[k]
    return es.legend(p, x, y, kinds, DEVICE_KINDS)


def schedule(x, y, title, circuits, devices, width, nec_row=None, panel_a=None):
    """A panel schedule: circuit, description, breaker, wire, protection and how many of
       the unit's devices are on it; under it the 220.82 load the panel is sized to."""
    S, LEAD = 5.6, 7.6
    cols = (0, 0.24*inch, 2.44*inch, 2.78*inch, 2.95*inch, width-0.02*inch)
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, title); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= LEAD+1
    c.setFont('Helvetica-Bold', S)
    for t, cx in zip(('CKT', 'DESCRIPTION', 'BKR', 'WIRE', ' PROT.'), cols):
        c.drawString(x+cx, y, t)
    c.drawRightString(x+cols[5], y, 'DEV.'); y -= LEAD
    c.setFont('Helvetica', S)
    count = {}
    for d in devices:
        count[d.circuit] = count.get(d.circuit, 0)+1
    for ck in circuits:
        _fits(ck.desc, 'Helvetica', S, cols[2]-cols[1]-4, 'schedule description')
        row = (str(ck.n), ck.desc, '%d A / %dP' % (ck.amps, ck.poles), ck.wire, ck.prot)
        for t, cx in zip(row, cols):
            c.drawString(x+cx, y, t)
        c.drawRightString(x+cols[5], y, str(count.get(ck.n, 0)))
        y -= LEAD
    if nec_row is not None:
        r = nec220_82(*nec_row[1:7]); y -= 2
        c.setLineWidth(0.3); c.line(x, y+LEAD-2, x+width, y+LEAD-2)
        c.setFont('Helvetica-Bold', S); c.drawString(x, y, 'LOAD, NEC 220.82'); y -= LEAD
        c.setFont('Helvetica', S)
        for lab, val in (('GENERAL LIGHTING AND RECEPTACLES, 3 VA/SF x %d SF' % nec_row[1], r['gen']),
                         ('SMALL APPLIANCE, TWO CIRCUITS AT 1,500 VA', r['sa']),
                         ('LAUNDRY', r['ldy']), ('RANGE', r['rng']), ('DRYER', r['dry']),
                         ('DISHWASHER', r['dw']), ('WATER HEATER', r['wh']),
                         ('FIRST 10 KVA AT 100 %, REMAINDER AT 40 %', r['first']+r['rem']),
                         ('HEAT PUMP AT ITS MCA, 100 %', r['hp']),
                         ('CALCULATED LOAD, VA', r['tot'])):
            if val == 0 and lab == 'DISHWASHER':
                c.drawString(x, y, lab); c.drawRightString(x+cols[5], y, 'NONE'); y -= LEAD; continue
            c.drawString(x, y, lab); c.drawRightString(x+cols[5], y, '{:,.0f}'.format(val)); y -= LEAD
        c.setFont('Helvetica-Bold', S)
        c.drawString(x, y, 'AT 240 V'); c.drawRightString(x+cols[5], y, '%.0f A ON A %d A PANEL' % (r['amps'], panel_a)); y -= LEAD
    return y-4


_CKTS = {'U1': CIRCUITS_U1, 'U2': CIRCUITS_U23, 'U3': CIRCUITS_U23, 'U4': CIRCUITS_U45, 'U5': CIRCUITS_U45,
         'H': CIRCUITS_HOUSE}


def one_line(x, y, s, width):
    """The building's service, drawn: the drop, the entrance conductors, the meter bank
       with a position per meter, each position's breaker, the feeder to each panel."""
    std, opt, gov, size = service_loads(s)
    fd = feeders(s); svc = fd[-1]; pos = fd[:-1]
    S = 5.6
    LAY('E-ANNO-TEXT'); c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2)
    c.drawString(x, y, 'ONE-LINE DIAGRAM — BUILDING %d, METER BANK %s' % (s['building'], s['mark'])); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= 0.14*inch
    # the drop, down the left edge, into the bank
    dx = x+0.28*inch
    c.setFont('Helvetica', S)
    c.drawString(dx+6, y-2, 'AEP OHIO OVERHEAD DROP, 120 / 240 V, 1-PHASE, 3-WIRE'); c.setLineWidth(0.9)
    c.line(dx, y, dx, y-0.22*inch); y -= 0.22*inch
    c.setFont('Helvetica', S)
    c.drawString(dx+6, y-2, 'SERVICE ENTRANCE %d A: 3 x %s CU, TABLE 310.16, IN CONDUIT TO THE BANK' % (size, svc[3]))
    c.line(dx, y, dx, y-0.22*inch); y -= 0.22*inch
    # the bank
    n = len(pos); colw = min(1.55*inch, (width-0.1*inch)/n)
    bx, bh = x, 0.72*inch
    c.setLineWidth(0.8); c.setStrokeColor(black); c.setFillColor(white)
    c.rect(bx, y-bh, colw*n+0.1*inch, bh, fill=1, stroke=1)
    c.setFillColor(black); c.setFont('Helvetica-Bold', S)
    c.drawString(bx+4, y-8, 'METER BANK %s, %d POSITIONS, ON THE ADJACENT-PARCEL WALL, C-101' % (s['mark'], n))
    c.setFont('Helvetica', S)
    for j, t in enumerate(('EACH POSITION: THE METER, THEN ITS BREAKER IN ITS OWN COMPARTMENT — THAT METER\'S SERVICE DISCONNECT.',
                           'THE BREAKERS ARE MARKED "%s".' % s['marking'])):
        _fits(t, 'Helvetica', S, colw*n+0.1*inch-8, 'one-line bank line')
        c.drawString(bx+4, y-8-(S+1)*(j+1), t)
    hp = {'U1': 'HP-1', 'U2': 'HP-2', 'U3': 'HP-3', 'U4': 'HP-4', 'U5': 'HP-5'}
    for i, (code, name, a, wire, wires, neutral, egc) in enumerate(pos):
        cx = bx+0.05*inch+i*colw+colw/2.0
        my = y-bh+0.20*inch
        c.setLineWidth(0.6); c.setFillColor(white); c.circle(cx-0.30*inch, my, 6, fill=1, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5); c.drawCentredString(cx-0.30*inch, my-1.8, 'M')
        c.setLineWidth(0.6); c.line(cx-0.30*inch+6, my, cx-0.12*inch, my)
        c.setFillColor(white); c.rect(cx-0.12*inch, my-6, 0.42*inch, 12, fill=1, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5); c.drawCentredString(cx+0.09*inch, my-1.8, '%d A / 2P' % a)
        c.setFont('Helvetica', 4.8); c.drawCentredString(cx, y-bh+0.06*inch, name)
        # the feeder down to the panel
        py = y-bh-0.55*inch
        c.setLineWidth(0.7); c.line(cx, y-bh, cx, py)
        c.setFont('Helvetica', 4.8)
        c.drawString(cx+3, y-bh-0.16*inch, '%s CU, %d-WIRE' % (wire, wires))
        c.drawString(cx+3, y-bh-0.16*inch-6, 'EGC %s' % egc)
        c.drawString(cx+3, y-bh-0.16*inch-12, 'NEUTRAL ISOLATED')
        c.setFillColor(white); c.rect(cx-colw/2.0+0.06*inch, py-0.26*inch, colw-0.12*inch, 0.26*inch, fill=1, stroke=1)
        c.setFillColor(black); c.setFont('Helvetica-Bold', 5.2)
        c.drawCentredString(cx, py-0.10*inch, 'PANEL %s, %d A, MLO' % (code, a))
        c.setFont('Helvetica', 4.8)
        c.drawCentredString(cx, py-0.19*inch, '%d CIRCUITS, SEE THE SCHEDULE' % len(_CKTS[code]))
        if code in hp:
            c.drawCentredString(cx, py-0.26*inch-7, '%s: DISCONNECT AT THE UNIT, C-101' % hp[code])
    y = y-bh-0.55*inch-0.26*inch-0.22*inch
    c.setFont('Helvetica', S); c.setFillColor(black)
    lines = [
        'GROUNDING ELECTRODE: THE FOOTING\'S TWO #4 BARS, S-101 NOTE 1, ENCASED AT LEAST 2" IN CONCRETE IN CONTACT WITH EARTH; GEC %s CU, NEC 250.66(B); A #4 CU STUB LEFT UP AT THE BANK.' % GEC_CEE,
        'MAIN BONDING JUMPER AT THE SERVICE DISCONNECTS ONLY; INTERSYSTEM BONDING TERMINATION AT THE BANK.',
        'SERVICE LOAD, HOUSE LOAD %s VA INCLUDED: %s = %.0f A; %s = %.0f A. THE LESSER GOVERNS: %d A.'
        % ('{:,}'.format(HOUSE_VA), std['method'], std['amps'], opt['method'], opt['amps'], size),
        'THE BANK\'S LOCATION, RATING AND EQUIPMENT ARE SUBJECT TO AEP OHIO\'S APPROVAL BEFORE ROUGH-IN.',
    ]
    for t in wrap_notes(lines, width, S, indent='   '):
        _fits(t, 'Helvetica', S, width, 'one-line note')
        c.drawString(x, y, t); y -= 7.0
    return y


def _panel_note():
    """The minimum spaces each dwelling panel must have, derived from its own schedule
       so the note cannot promise a panel the circuits will not fit into."""
    out = []
    for nm, ckts, amps in (('UNIT 1', CIRCUITS_U1, NEC_UNITS[0][7]),
                           ('UNITS 2 AND 3', CIRCUITS_U23, NEC_UNITS[1][7]),
                           ('UNITS 4 AND 5', CIRCUITS_U45, NEC_UNITS[2][7])):
        used, spaces = panel_spaces(ckts)
        out.append('%s %d A, %d SPACES MINIMUM (%d POLES USED)' % (nm, amps, spaces, used))
    return '; '.join(out)


NOTES = [
    "1.  SERVICE AND METERING — ONE UTILITY SERVICE PER BUILDING INTO ITS METER BANK, AS C-101 MARKS AND THE ONE-LINE DIAGRAM SHOWS. NOTHING ELECTRICAL RUNS BETWEEN THE BUILDINGS.",
    "2.  PROTECTION — AFCI AND GFCI AS THE SCHEDULES SHOW, NEC 210.12 AND 210.8 AS RCO 3401.1 MODIFIES THEM. A RECEPTACLE MARKED GFCI IS PROTECTED AT THE DEVICE OR BY ITS BREAKER; EVERY 125 V, 15 AND 20 A KITCHEN, BATH, LAUNDRY AND EXTERIOR RECEPTACLE IS PROTECTED.",
    "3.  ALARMS — HARDWIRED, INTERCONNECTED WITHIN EACH UNIT ONLY, WITH BATTERY BACKUP. SMOKE ALARMS DUAL SENSOR, RCO 314.1.2. THE CARBON MONOXIDE ALARMS ARE VOLUNTARY, G-001 NOTE 10, AND SHALL BE INSTALLED PER RCO 315.2.2.",
    "4.  HEAT PUMPS — 2-POLE BREAKER AT THE NAMEPLATE MOCP, CONDUCTORS AT THE NAMEPLATE MCA, BOTH RESIZED TO THE UNIT SELECTED; DISCONNECT AT THE OUTDOOR UNIT, WITHIN SIGHT; INDOOR HEADS ON THE SAME CIRCUIT. NO ELECTRIC RESISTANCE HEAT.",
    "5.  ENTRY AND STAIR LIGHTING — EACH UNIT'S ENTRY LUMINAIRE IS ON THAT UNIT'S PANEL AND SWITCHED FROM INSIDE THE UNIT, NEC 210.70(A)(2)(b). COMMON SITE LIGHTING IS ON THE HOUSE METER OF ITS BUILDING, PHOTOCELL CONTROLLED, UNSWITCHED.",
    "6.  W4 — A-001 NOTE 4. DEVICES DRAWN ALONG THAT LINE ARE IN THE W5 FURRED CHASE ON THE UNIT SIDE. BOXES IN THE F1 CEILING PER A-001 NOTE 4a.",
    "7.  PANELS — WORKING SPACE AS A-101 AND A-103 DIMENSION IT, NEC 110.26(A); NOTHING PIPED THROUGH IT, 110.26(E). EVERY PANEL IS A SUBPANEL: MAIN LUGS ONLY, NEUTRAL ISOLATED FROM GROUND.",
    "8.  RECEPTACLES — SPACED PER NEC 210.52 AS DRAWN; KITCHEN COUNTERS PER 210.52(C); TAMPER RESISTANT THROUGHOUT, 406.12; EXTERIOR RECEPTACLES WEATHER RESISTANT WITH IN-USE COVERS, 406.9.",
    "9.  BATH FANS — THE ONE FAN PER UNIT MARKED C IS THE WHOLE-DWELLING VENTILATION FAN OF M-101 NOTE 4: CONTINUOUS DUTY, RUNNING CONTINUOUSLY AT THE TABLE M1505.4.3(1) RATE, UNSWITCHED, WITH THE WALL SWITCH DRAWN BOOSTING IT. EVERY OTHER BATH FAN IS AN ORDINARY SWITCHED EXHAUST FAN. NO FAN IS ON A TIMER.",
    "10. SERVICE — AS THE ONE-LINE DIAGRAM; LOADS AS TABULATED THERE. EVERY DWELLING IS ALL-ELECTRIC, A-001 NOTE 10. THE STORAGE WATER HEATER OF P-601 NOTE 6 IS IN EVERY LOAD CALCULATION AT ITS NAMEPLATE. THE METER BANK'S LOCATION, RATING AND EQUIPMENT CONFIGURATION ARE COORDINATED WITH AND APPROVED BY AEP OHIO BEFORE ROUGH-IN.",
    "11. FEEDERS — AS THE ONE-LINE SIZES THEM: UNIT FEEDERS PER NEC 310.12, THE HOUSE FEEDERS AND THE SERVICE-ENTRANCE CONDUCTORS PER TABLE 310.16. EVERY FEEDER FROM THE BANK IS 4-WIRE WITH AN EQUIPMENT GROUNDING CONDUCTOR PER TABLE 250.122; THE BONDING JUMPER IS AT THE SERVICE DISCONNECT ONLY. GROUNDING ELECTRODE PER THE ONE-LINE.",
    "12. SERVICE DISCONNECTS — THE POSITION BREAKERS IN THE METER BANK, ONE PER COMPARTMENT. BUILDING 2'S METER-BANK POSITION BREAKERS SHALL BE MARKED EMERGENCY DISCONNECT AND SERVICE DISCONNECT PER NEC 230.85. BUILDING 1'S SERVICE DISCONNECTS PER NEC 230.70(B).",
    "13. UNIT PANELBOARDS — %s. PROVIDE A COPPER GROUND BAR AND, IN EVERY PANEL, A DIRECTORY FILLED IN AT COMPLETION, NEC 408.4(A)." % _panel_note(),
]


def notes(x, y, width, cols=2, size=5.6, lead=7.4, see=None):
    """The thirteen notes, re-flowed into `cols` columns of the given total width."""
    return notes_block(x, y, width, NOTES, 'ELECTRICAL NOTES', 'E-ANNO-TEXT', 'electrical note', cols, size, lead, 0.18*inch, see)


def grey_context(p, W, D, top, bottom, left, right, top_off=0.9):
    """The four context strings, small and grey, so the plan reads the same way up as
       its architectural sheet without the bulk of that sheet's surround.

       A-ANNO-TEXT, not E-ANNO-TEXT. These name the streets and the neighbouring parcel:
       the same architectural content C-101 draws, and identical on every sheet that
       shows a plan. This helper lives in the electrical module but M-101, M-102, P-101,
       P-102, P-103, S-102, S-103 and S-104 all call it, so the E layer filed SAGE
       AVENUE as electrical text twenty-two times against C-101's one architectural one.
       One layer means a drafter can freeze the context on every sheet at once, which is
       what the layer is for."""
    LAY('A-ANNO-TEXT'); cc = p.c; cc.setFillColor(GREY); cc.setFont('Helvetica', 5.6)
    cc.drawCentredString(p.X(W/2.0), p.Y(-top_off), top)
    cc.drawCentredString(p.X(W/2.0), p.Y(D+1.4), bottom)
    for X, t in ((p.X(-1.0), left), (p.X(W+1.0), right)):
        cc.saveState(); cc.translate(X, p.Y(D/2.0)); cc.rotate(90); cc.drawCentredString(0, 0, t); cc.restoreState()
    cc.setFillColor(black)


__all__ = ['legend', 'schedule', 'one_line', 'notes', 'title', 'grey_context', 'inches']

"""What M-101 and M-102 share: a unit's mechanical work on a greyed plan, the three
schedules and the notes. Every figure printed here is read from src/mechanical.py,
which check_model() has already passed."""
from arkitect.lib.draw.page import LAY
from arkitect.lib.symbols import mechanical as ms
from arkitect.lib.units import fmt
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.mechanical import (DRYER_OUT_Z, DRYER_PHYS_MAX, EXH_CLR, LOCAL_CFM, ODU_TERM_CLR, W4_ROOF_BAND,
                            WALLS, outdoor_units, ventilation, LEVELS)
from arkitect.codes.ohio.rco.mechanical import terminations
from arkitect.codes.ohio.rco.mechanical import DRYER_ELBOW, DRYER_MAX
from src.sheets.e_common import grey_context
from arkitect.lib.draw.kit import title
from arkitect.lib.draw.mechanical_kit import S, _head, _para, _room, _row
from arkitect.lib.draw.kit import notes_block

# Neither building is ducted: the legend leaves out the air handler and its registers.
DUCTLESS = [k for k, _t in ms.KINDS if k not in ('ahu', 'reg')]

def place(p, m):
    """One MLevel's mechanical work on PlanDraw p: the outdoor unit outside the wall
       first, then the runs, the equipment over them, and the caps on the wall line."""
    if not (m.unit == 1 and m.level == 2):        # HP-1 is on the Level 1 plan; the drop is here
        ms.draw_odu(p, m.hp_box, m.hp)
    for ls in m.linesets:
        ms.draw_duct(p, ls, 'ls')
    for d in m.ducts:
        ms.draw_duct(p, d.pts, 'duct', d.size)
    for x, y, mt, room in m.heads:
        ms.draw_head(p, x, y, mt)
    for d in m.elec.devices:                       # the system's wall control, E-101 places it
        if d.kind == 'tstat':
            tx, ty = m.pg(d.x, d.y)
            ms.draw_tstat(p, tx, ty)
    for x, y, kind, room, tag in m.fans:
        mark = next((d.term.mark for d in m.ducts if abs(d.pts[0][0]-x) < 1e-6 and abs(d.pts[0][1]-y) < 1e-6), '')
        ms.draw_fan(p, x, y, kind == 'fanc', mark)
    for t in m.terms:
        if t.wall == 'ROOF':
            ms.draw_roofcap(p, t.along[0], t.along[1], t.mark)
        else:
            wall = WALLS[m.bldg][t.wall]
            x, y = (wall.at, t.along) if wall.orient == 'v' else (t.along, wall.at)
            ms.draw_cap(p, x, y, wall.orient, t.mark)
    if m.unit == 1 and m.level == 2:
        ms.draw_sleeve(p, m.drop[0], m.drop[1], 'LINE SETS DOWN TO HP-1')
    else:
        ms.draw_sleeve(p, m.sleeve[0], m.sleeve[1], 'SLEEVE' if m.level == 1 else 'SLEEVE, DROP OUTSIDE TO %s' % m.hp)
        if m.unit == 1:
            ms.draw_sleeve(p, m.drop[0], m.drop[1], 'FROM LEVEL 2', below=True)


def outdoor_schedule(x, y, width, bldg):
    """The outdoor units of one building: what each serves, where it stands, the
       nameplate envelope E-101 was sized on, and its heads."""
    LAY('M-ANNO-TEXT')
    y = _head(x, y, 'OUTDOOR UNIT SCHEDULE — BUILDING %d' % bldg, width)
    cols = (0, 20, 48, 80, 120)              # points, measured: the widest cell of each column plus 3
    y = _row(x, y, cols, ('MARK', 'SERVES', 'WALL', 'MCA / MOCP', 'HEADS'), width, bold=True)
    for r in outdoor_units():
        if (r['unit'] <= 3) != (bldg == 1): continue
        y = _row(x, y, cols, (r['mark'], 'UNIT %d' % r['unit'], r['wall'].replace('ADJACENT ', ''), '%d A / %d A' % (r['mca'], r['mocp']),
                              ', '.join(_room(h) for h in r['heads'])), width)
    y = _para(x, y, 'COLD-CLIMATE DUCTLESS HEAT PUMP, RATED AT THE 0 F WINTER DESIGN CONDITION OF CIC-09. CAPACITY BY '
              'ACCA MANUAL J AND S, RCO M1401.3, SUBMITTED WITH THE MECHANICAL TRADE PERMIT. A SELECTED UNIT WHOSE '
              'NAMEPLATE EXCEEDS THE MCA RE-RUNS THE NEC 220.82 CALCULATION OF E-101 / E-102.', width)
    return y-4


def ventilation_schedule(x, y, width, bldg):
    LAY('M-ANNO-TEXT')
    y = _head(x, y, 'VENTILATION SCHEDULE — RCO 303.4 AND TABLE M1505.4.3(1)', width)
    cols = (0, 36, 48, 68, 116, 160)
    y = _row(x, y, cols, ('UNIT', 'BR', 'SF', 'WHOLE-HOUSE', 'CONTINUOUS', 'BOOST'), width, bold=True)
    for r in ventilation():
        if (r['name'] != 'UNITS 4 / 5') != (bldg == 1): continue
        y = _row(x, y, cols, (r['name'], str(r['bedrooms']), '{:,}'.format(r['area']), '%d CFM REQ\'D' % r['required'],
                              '%d CFM' % r['continuous'], '%d CFM' % r['boost']), width)
    y = _para(x, y, 'THE FAN MARKED C RUNS CONTINUOUSLY AT THE WHOLE-HOUSE RATE, UNSWITCHED, AND ITS WALL SWITCH BOOSTS '
              'IT. EVERY OTHER BATH FAN IS %d CFM INTERMITTENT, SWITCHED, TABLE M1505.4.4. E-101 / E-102 CIRCUIT THEM.'
              % LOCAL_CFM['BATH'][0], width)
    return y-4


def termination_schedule(x, y, width, bldg):
    """Every cap of one building, with the clearance check_mechanical() measured and,
       for a dryer, the duct length against M1502.4.5.1."""
    LAY('M-ANNO-TEXT')
    y = _head(x, y, 'TERMINATION SCHEDULE — BUILDING %d' % bldg, width)
    cols = (0, 22, 76, 126, 156)
    y = _row(x, y, cols, ('MARK', 'WHAT', 'WALL', 'HEIGHT', 'CLEAR TO NEAREST OPENING'), width, bold=True)
    dryers = []
    for r in terminations(levels=LEVELS, walls=WALLS):
        if r['bldg'] != bldg: continue
        t = r['term']
        if t.wall == 'ROOF':
            cells = (t.mark, t.what, 'ROOF', '—', 'ROOF CAP, %s CLEAR OF W4' % fmt(W4_ROOF_BAND) if bldg == 1 else 'ROOF CAP')
        else:
            cells = (t.mark, t.what, t.wall.replace('ADJACENT-PARCEL', 'PARCEL'), fmt(t.z), '%s, %s' % (fmt(r['clr']), r['near']))
        y = _row(x, y, cols, cells, width)
        if t.what == 'DRYER EXHAUST':
            dryers.append('%s: %s OF DUCT, %d ELBOWS, %s EQUIVALENT' % (t.mark, fmt(r['length']), r['elbows'], fmt(r['equiv'])))
    y = _para(x, y, 'HEIGHTS ABOVE GRADE. EXHAUST AND DRYER CAPS %s FROM EVERY OPENING IN ANY DIRECTION, RCO M1504.3 '
              'AND M1502.3. DRYER DUCTS AGAINST %s LESS %s PER 90-DEGREE ELBOW, TABLE M1502.4.5.1:'
              % (fmt(EXH_CLR), fmt(DRYER_MAX), fmt(DRYER_ELBOW)), width)
    for d in dryers:
        y = _para(x, y, '   '+d, width)
    return y-4


NOTES = [
    "1.  SYSTEM — DUCTLESS AIR-SOURCE HEAT PUMP, ONE OUTDOOR UNIT PER DWELLING AS C-101 PLACES IT, WALL HEADS AS DRAWN, A-001 NOTE 18. COLD-CLIMATE EQUIPMENT RATED AT THE 0 F WINTER DESIGN CONDITION OF CIC-09, NOT THE NOMINAL 47 F RATING; CAPACITY AND HEAD SIZES BY ACCA MANUAL J AND S, RCO M1401.3, SUBMITTED WITH THE MECHANICAL TRADE PERMIT. NO ELECTRIC RESISTANCE HEAT, E-101 NOTE 4.",
    "1a. CONTROLS — ONE WALL CONTROL PER SYSTEM, RCO 1103.1, AS DRAWN: THE MANUFACTURER'S WIRED CONTROL IN THE DWELLING'S LIVING SPACE, 48\" TO THE TOP, ON AN INTERIOR WALL, CLEAR OF SUNLIGHT AND A DOOR SWING, WITH LOW-VOLTAGE CABLE TO ITS OWN EQUIPMENT. A HANDHELD REMOTE DOES NOT STAND IN FOR IT.",
    "2.  LINE SETS — EACH HEAD'S INSULATED REFRIGERANT PAIR AND ITS CONDENSATE DRAIN RUN CONCEALED IN THE UNIT'S OWN WALL AND FLOOR CAVITIES TO ONE SEALED SLEEVE ABOVE ITS OUTDOOR UNIT, DRAWN DIAGRAMMATICALLY. W4 AND F1: A-001 NOTES 4 AND 19; PENETRATIONS OF F1 PER A-001 NOTE 4a; HOLES IN I-JOIST WEBS PER THE HOLE CHART, P-601 NOTE 1aa. A LEVEL 2 UNIT'S LINE SETS LEAVE AT LEVEL 2 AND DROP OUTSIDE IN A LINE-SET COVER TO THE OUTDOOR UNIT AT GRADE; UNIT 1'S LEVEL 2 SETS DROP IN THE SAGE WALL AT THE STAIR TO THE LEVEL 1 SLEEVE. LENGTH AND LIFT WITHIN THE SELECTED EQUIPMENT'S LIMITS.",
    "3.  CONDENSATE — BY GRAVITY TO DAYLIGHT THROUGH THE WALL BEHIND EACH HEAD, 6\" ABOVE GRADE, NEVER OVER A WALK OR A DOOR LANDING, RCO M1411.3. THE UNITS 2 AND 3 LIVING-ROOM HEADS STAND ON THE SAGE WALL OVER THE PUBLIC SIDEWALK AND DRAIN INSTEAD TO THE KITCHEN SINK TAILPIECE THROUGH AN AIR GAP. INSULATE EVERY DRAIN IN AN UNCONDITIONED SPACE.",
    "4.  WHOLE-HOUSE VENTILATION — RCO 303.4, RATES AS THE VENTILATION SCHEDULE. THE BATH FAN MARKED C IN EACH DWELLING, LISTED FOR CONTINUOUS DUTY, RUNS CONTINUOUSLY AT THE RATE SCHEDULED, UNSWITCHED, AND ITS WALL SWITCH BOOSTS IT; EVERY OTHER BATH FAN IS INTERMITTENT AND SWITCHED. FAN EFFICACY PER RCO TABLE N1103.6.1. FANS IN THE UNIT 2 AND UNIT 4 CEILINGS ARE LISTED FOR THE F1 CEILING AND CARRY A CEILING RADIATION DAMPER, A-001 NOTE 4a.",
    "5.  EXHAUST DUCTS — 4\" SMOOTH RIGID METAL, JOINTS SEALED, AS DRAWN: A LEVEL 1 BATH DUCTS THROUGH THE FLOOR CAVITY ABOVE IT TO THE WALL CAP SCHEDULED, A LEVEL 2 BATH RISES INTO THE ATTIC TO A ROOF CAP. DUCTS IN THE ATTIC ARE INSULATED. EVERY CAP CARRIES A BACKDRAFT DAMPER AND STANDS %s FROM EVERY OPENING INTO THE BUILDING IN ANY DIRECTION, RCO M1504.3, AND %s FROM THE LOT LINE; NO EXHAUST IS DIRECTED ONTO A WALKWAY, RCO 303.5.2. NO ROOF OPENING WITHIN %s OF W4, RCO 302.2.4 EXCEPTION." % (fmt(EXH_CLR), fmt(EXH_CLR), fmt(W4_ROOF_BAND)),
    "6.  DRYER EXHAUST — RCO M1502. 4\" SMOOTH METAL DUCT WITH NO FASTENER INTO THE AIRSTREAM AND NO SCREEN AT THE CAP; A LISTED TRANSITION DUCT NOT OVER 8'-0\" AT THE APPLIANCE, M1502.4.3; THE OUTLET OF THE STACKED DRYER TAKEN %s ABOVE ITS FLOOR. LENGTH AS SCHEDULED AGAINST %s LESS %s PER 90-DEGREE ELBOW, TABLE M1502.4.5.1, AND UNDER %s OF DUCT IN EVERY UNIT; SURFACE-MOUNTED, NEVER IN A W1R WALL CAVITY, NO RUN SLOPING DOWNWARD; ROUTES PER A-001 NOTE 16. CAPS %s FROM EVERY OPENING, M1502.3. MAKE-UP AIR THROUGH THE LOUVERED CLOSET DOORS, A-001 NOTE 10. NO DAMPER IN THE DUCT WHERE IT PASSES W1R, A-001 NOTE 2a." % (fmt(DRYER_OUT_Z), fmt(DRYER_MAX), fmt(DRYER_ELBOW), fmt(DRYER_PHYS_MAX), fmt(EXH_CLR)),
    "7.  RANGE HOODS — UNIT 1: A DUCTED HOOD, 6\" SMOOTH METAL STRAIGHT THROUGH THE ADJACENT-PARCEL WALL BEHIND THE RANGE TO RH-1, BACKDRAFT DAMPER, NOT OVER 400 CFM FOR THE 6\" DUCT. NO MAKE-UP AIR IS REQUIRED, RCO M1503.6, A-001 NOTE 10. UNITS 2, 3, 4 AND 5: LISTED DUCTLESS RECIRCULATING HOODS, M1503.3 EXCEPTION, EACH KITCHEN OPEN TO THE LIVING SPACE THE NOTE 4 FAN VENTILATES; A DUCTED HOOD SUBSTITUTED SHALL DISCHARGE OUTDOORS, CAP PER NOTE 5.",
    "8.  ACCESS AND CLEARANCES — 30\" x 30\" WORKING SPACE AT EACH WATER HEATER, RCO M1305.1, DIMENSIONED ON A-101, A-102 AND A-103; THE OUTDOOR UNITS' DISCONNECTS WITHIN SIGHT, E-101 / E-102; OUTDOOR UNITS AT THE MANUFACTURER'S CLEARANCES FROM WALLS AND EACH OTHER. MAINTAIN %s MINIMUM ALONG THE WALL BETWEEN DRYER TERMINATIONS AND OUTDOOR UNITS, OR THE GREATER MANUFACTURER-REQUIRED CLEARANCE." % fmt(ODU_TERM_CLR),
    "9.  TRADE PERMIT — ALL WORK BY A CONTRACTOR HOLDING AN OHIO OCILB HVAC LICENSE AND REGISTERED WITH THE CITY OF COLUMBUS; THE MECHANICAL PERMIT IS OBTAINED SEPARATELY AFTER THE BUILDING PERMIT, G-001 NOTE 14, WITH THE MANUAL J AND S CALCULATIONS AND THE EQUIPMENT SUBMITTALS.",
]


def notes(x, y, width, cols=3, size=S, lead=7.4, see=None):
    """The notes, re-flowed into `cols` columns of the given total width."""
    return notes_block(x, y, width, NOTES, 'MECHANICAL NOTES', 'M-ANNO-TEXT', 'mechanical note', cols, size, lead, 0.22*inch, see)


__all__ = ['place', 'outdoor_schedule', 'ventilation_schedule', 'termination_schedule', 'notes',
           'title', 'grey_context', 'pdfmetrics']

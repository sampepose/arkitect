"""What M-101 and M-102 share: a unit's mechanical work on a greyed plan, the three
schedules and the notes. Every figure printed here is read from src/mechanical.py,
which check_model() has already passed."""
from arkitect.lib.draw.page import LAY
from arkitect.lib.symbols import mechanical as ms
from arkitect.lib.units import fmt
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src.mechanical import (B2_DR_CAP_Z, DRYER_OUT_Z, EXH_CLR, LOCAL_CFM, ODU_TERM_CLR, WALLS,
                            outdoor_units, ventilation, LEVELS)
from arkitect.codes.ohio.rco.mechanical import terminations
from arkitect.codes.ohio.rco.mechanical import DRYER_ELBOW, DRYER_MAX
from src.sheets.e_common import grey_context
from arkitect.lib.draw.kit import title
from arkitect.lib.draw.mechanical_kit import S, _head, _para, _room, _row
from arkitect.lib.draw.kit import notes_block
from src.mechanical import AHU_MARK

def legend_kinds(bldg):
    """What this building's plans draw: Unit 1 is ducted in two zones and shows an air
       handler and its registers, Building 2 is ductless and shows wall heads."""
    drop = ('ahu', 'reg') if bldg == 2 else ('head',)
    return [k for k, _t in ms.KINDS if k not in drop]


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
    for x, y, room in m.ahus:
        # the supply runs, diagrammatic: the air handler to each register of its level
        for rx, ry, _rm, mark in m.regs:
            if not mark:
                ms.draw_duct(p, [(x, y), (rx, y), (rx, ry)], 'duct', '')
        ms.draw_ahu(p, x, y, AHU_MARK.get((m.unit, m.level), ''))
    for rx, ry, _rm, mark in m.regs:
        ms.draw_register(p, rx, ry, mark)
    for d in m.elec.devices:                       # the system's thermostat, E-101 places it
        if d.kind == 'tstat':
            tx, ty = m.pg(d.x, d.y)
            ms.draw_tstat(p, tx, ty)
    for x, y, kind, room, tag in m.fans:
        mark = next((d.term.mark for d in m.ducts if abs(d.pts[0][0]-x) < 1e-6 and abs(d.pts[0][1]-y) < 1e-6 and d.term.wall != 'ROOF'), '')
        ms.draw_fan(p, x, y, kind == 'fanc', mark)
    for t in m.terms:
        if t.wall == 'ROOF':
            ms.draw_roofcap(p, t.along[0], t.along[1], t.mark)
        else:
            wall = WALLS[m.bldg][t.wall]
            x, y = (wall.at, t.along) if wall.orient == 'v' else (t.along, wall.at)
            ms.draw_cap(p, x, y, wall.orient, t.mark)
    if m.unit == 1 and m.level == 2:
        ms.draw_sleeve(p, m.drop[0], m.drop[1], 'LINE SETS DOWN TO HP-1', below=True)
    else:
        # the legend names the sleeve; only a Level 2 one says where it goes, under the dot and clear of the run
        ms.draw_sleeve(p, m.sleeve[0], m.sleeve[1], '' if m.level == 1 else 'DROP OUTSIDE TO %s' % m.hp, below=True)
        if m.unit == 1:
            ms.draw_sleeve(p, m.drop[0], m.drop[1], 'FROM LEVEL 2', below=True)


def outdoor_schedule(x, y, width, bldg):
    """The outdoor units of one building: what each serves, where it stands, the
       nameplate envelope E-101 was sized on, and its heads."""
    LAY('M-ANNO-TEXT')
    y = _head(x, y, 'OUTDOOR UNIT SCHEDULE — BUILDING %d' % bldg, width)
    cols = (0, 20, 48, 80, 120)              # points, measured: the widest cell of each column plus 3
    y = _row(x, y, cols, ('MARK', 'SERVES', 'WALL', 'MCA / MOCP', 'INDOOR UNITS'), width, bold=True)
    for r in outdoor_units():
        if (r['unit'] == 1) != (bldg == 1): continue
        y = _row(x, y, cols, (r['mark'], 'UNIT %d' % r['unit'], r['wall'], '%d A / %d A' % (r['mca'], r['mocp']),
                              ', '.join(h if h.startswith('AHU') else _room(h) for h in r['heads'])), width)
    y = _para(x, y, 'COLD-CLIMATE HEAT PUMP, RATED AT THE 0 F WINTER DESIGN CONDITION OF CIC-09. CAPACITY BY '
              'ACCA MANUAL J AND S, RCO M1401.3, SUBMITTED WITH THE MECHANICAL TRADE PERMIT. A SELECTED UNIT WHOSE '
              'NAMEPLATE EXCEEDS THE MCA RE-RUNS THE NEC 220.82 CALCULATION OF E-101 / E-102.', width)
    return y-4


def ventilation_schedule(x, y, width, bldg):
    LAY('M-ANNO-TEXT')
    y = _head(x, y, 'VENTILATION SCHEDULE — RCO 303.4 AND TABLE M1505.4.3(1)', width)
    cols = (0, 36, 48, 68, 116, 160)
    y = _row(x, y, cols, ('UNIT', 'BR', 'SF', 'WHOLE-HOUSE', 'CONTINUOUS', 'BOOST'), width, bold=True)
    for r in ventilation():
        if (r['name'] == 'UNIT 1') != (bldg == 1): continue
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
            cells = (t.mark, t.what, 'ROOF', '—', 'ROOF CAP OVER THE FAN, S-103')
        else:
            cells = (t.mark, t.what, t.wall, fmt(t.z), '%s, %s' % (fmt(r['clr']), r['near']))
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
    "1.  SYSTEM — AIR-SOURCE HEAT PUMP, ONE OUTDOOR UNIT PER DWELLING ON A WALL BRACKET AS C-101 AND THE ELEVATIONS PLACE IT. UNIT 1 IS DUCTED IN TWO ZONES, AN AIR HANDLER PER LEVEL CONCEALED IN THAT LEVEL'S HALL SOFFIT AS DRAWN; UNITS 2 AND 3 TAKE WALL HEADS AS DRAWN. COLD-CLIMATE EQUIPMENT RATED AT THE 0 F WINTER DESIGN CONDITION OF CIC-09, NOT THE NOMINAL 47 F RATING; CAPACITY, AIR HANDLER AND HEAD SIZES BY ACCA MANUAL J AND S, RCO M1401.3, SUBMITTED WITH THE MECHANICAL TRADE PERMIT. NO ELECTRIC RESISTANCE HEAT.",
    "1a. CONTROLS — ONE THERMOSTAT PER SYSTEM, RCO 1103.1, AS DRAWN. UNIT 1'S TWO ZONES TAKE A PROGRAMMABLE THERMOSTAT EACH, RCO 1103.1.1; UNITS 2 AND 3 TAKE THE MANUFACTURER'S WIRED WALL CONTROL IN THE LIVING SPACE. SET EACH 48\" TO THE TOP, ON AN INTERIOR WALL OF THE SPACE IT SERVES, CLEAR OF SUPPLY AIR, SUNLIGHT AND A DOOR SWING; LOW-VOLTAGE CABLE TO ITS OWN EQUIPMENT. A HEAT PUMP'S CONTROL SHALL NOT BRING ON SUPPLEMENTARY HEAT WHEN THE PUMP CAN MEET THE LOAD, RCO 1103.1.2 — THIS SET HAS NONE.",
    "2.  LINE SETS — EACH INDOOR UNIT'S INSULATED REFRIGERANT PAIR AND ITS CONDENSATE DRAIN RUN CONCEALED IN THE UNIT'S OWN WALL AND FLOOR CAVITIES TO ONE SEALED SLEEVE ABOVE ITS OUTDOOR UNIT, DRAWN DIAGRAMMATICALLY. PENETRATIONS OF W1R, W3 AND THE F1 CEILING: A-601. THROUGH THE FLOOR TRUSSES' OPEN WEBS, NEVER THROUGH A CHORD, S-102 NOTE 6. UNIT 3'S LINE SETS LEAVE AT LEVEL 2 AND DROP OUTSIDE IN A LINE-SET COVER TO HP-3; UNIT 1'S LEVEL 2 SETS DROP INSIDE THE NORTH WALL TO THE LEVEL 1 SLEEVE. LENGTH AND LIFT WITHIN THE SELECTED EQUIPMENT'S LIMITS.",
    "3.  CONDENSATE — BY GRAVITY TO DAYLIGHT, 6\" ABOVE GRADE, NEVER OVER A WALK, A LANDING OR A DOOR, RCO M1411.3: A HEAD ON AN EXTERIOR WALL THROUGH THE WALL BEHIND IT, A HEAD ON A PARTITION WITH ITS LINE SET TO THE OUTDOOR UNIT'S WALL. EACH CONCEALED AIR HANDLER STANDS OVER A FINISHED CEILING: FIT THE AUXILIARY PAN AND ITS OWN DRAIN OF RCO M1411.3.1, DISCHARGING WHERE IT WILL BE SEEN. NO CONDENSATE PUMP. INSULATE EVERY DRAIN IN AN UNCONDITIONED SPACE.",
    "4.  WHOLE-HOUSE VENTILATION — RCO 303.4, RATES AS THE VENTILATION SCHEDULE. THE BATH FAN MARKED C IN EACH DWELLING, LISTED FOR CONTINUOUS DUTY, RUNS CONTINUOUSLY AT THE RATE SCHEDULED, UNSWITCHED, AND ITS WALL SWITCH BOOSTS IT; UNIT 1'S OTHER BATH FAN IS INTERMITTENT AND SWITCHED. FAN EFFICACY PER RCO TABLE N1103.6.1. UNIT 2'S FAN AND ITS DUCT HANG IN THE BATH'S SOFFIT, BELOW THE RATED F1 CEILING, WHICH THEY DO NOT PIERCE: A-601 F1 ITEM C.",
    "5.  EXHAUST DUCTS — 4\" SMOOTH RIGID METAL, JOINTS SEALED, AS DRAWN: UNIT 1'S LEVEL 1 BATH DUCTS THROUGH THE FLOOR TRUSSES ABOVE IT AND UNIT 2'S THROUGH ITS SOFFIT TO THE WALL CAP SCHEDULED, A LEVEL 2 BATH RISES THROUGH THE ATTIC TO A ROOF CAP OVER THE FAN, S-103. DUCTS IN THE ATTIC ARE INSULATED. EVERY CAP CARRIES A BACKDRAFT DAMPER AND STANDS %s FROM EVERY OPENING INTO THE BUILDING IN ANY DIRECTION AND %s FROM THE LOT LINE, RCO M1504.3; NO EXHAUST IS DIRECTED ONTO A WALK." % (fmt(EXH_CLR), fmt(EXH_CLR)),
    "6.  DRYER EXHAUST — RCO M1502. 4\" SMOOTH METAL DUCT WITH NO FASTENER INTO THE AIRSTREAM AND NO SCREEN AT THE CAP; A LISTED TRANSITION DUCT NOT OVER 8'-0\" AT THE APPLIANCE, M1502.4.3; THE OUTLET OF THE STACKED DRYER TAKEN %s ABOVE ITS FLOOR. LENGTH AS SCHEDULED AGAINST %s LESS %s PER 90-DEGREE ELBOW, TABLE M1502.4.5.1; SURFACE-MOUNTED IN THE ROOM, NEVER IN A W1R WALL CAVITY, NO RUN SLOPING DOWNWARD. CAPS %s FROM EVERY OPENING, M1502.3; DR-2 AND DR-3 %s ABOVE THEIR FLOORS, OVER THE PARKING WALK. MAKEUP AIR THROUGH THE LOUVERED DOORS, A-001 NOTE 11a. NO FIRE DAMPER IN A DRYER DUCT, A-601." % (fmt(DRYER_OUT_Z), fmt(DRYER_MAX), fmt(DRYER_ELBOW), fmt(EXH_CLR), fmt(B2_DR_CAP_Z)),
    "6a. SUPPLY DUCTS, UNIT 1 — SIZED AND LAID OUT BY ACCA MANUAL D WITH THE MECHANICAL TRADE PERMIT; THE RUNS DRAWN ARE DIAGRAMMATIC. EVERY DUCT, PLENUM AND AIR HANDLER STANDS INSIDE THE THERMAL ENVELOPE, IN A HALL SOFFIT OR THE FLOOR TRUSSES, AND NONE IS IN THE ATTIC: A-602. SHEET METAL OR LISTED FLEXIBLE DUCT TO RCO M1601, JOINTS SEALED, SUPPORTED PER M1601.4.3; A BALANCING DAMPER AT EACH TAKEOFF, REACHED FROM THE REGISTER OR AN ACCESS PANEL. ONE FILTER AT EACH RETURN GRILLE, REACHED WITHOUT TOOLS, RCO M1601.4.7; A TRANSFER GRILLE OR A 1\" DOOR UNDERCUT RETURNS EVERY ROOM'S AIR TO IT.",
    "7.  RANGE HOODS — A LISTED DUCTLESS RECIRCULATING HOOD OVER EVERY RANGE, RCO M1503.3 EXCEPTION, EACH KITCHEN OPEN TO THE LIVING SPACE THE NOTE 4 FAN VENTILATES. A DUCTED HOOD SUBSTITUTED DISCHARGES OUTDOORS THROUGH A CAP PER NOTE 5 AND NEEDS AN APPROVED REVISION: THE WALL BEHIND UNIT 1'S RANGE STANDS OVER THE UNITS 2 AND 3 WALK.",
    "8.  ACCESS AND CLEARANCES — 30\" x 30\" WORKING SPACE AT EACH WATER HEATER, RCO M1305.1, DRAWN ON A-101 AND A-102; THE OUTDOOR UNITS' DISCONNECTS WITHIN SIGHT, E-101 / E-102; OUTDOOR UNITS AT THE MANUFACTURER'S CLEARANCES FROM WALLS AND EACH OTHER. MAINTAIN %s MINIMUM ALONG THE WALL BETWEEN A DRYER TERMINATION AND AN OUTDOOR UNIT, OR THE GREATER MANUFACTURER-REQUIRED CLEARANCE." % fmt(ODU_TERM_CLR),
    "9.  TRADE PERMIT — ALL WORK BY A CONTRACTOR HOLDING AN OHIO OCILB HVAC LICENSE AND REGISTERED WITH THE CITY OF COLUMBUS; THE MECHANICAL PERMIT IS OBTAINED SEPARATELY AFTER THE BUILDING PERMIT, G-001 NOTE 14, WITH THE MANUAL J AND S CALCULATIONS AND THE EQUIPMENT SUBMITTALS.",
]


def notes(x, y, width, cols=3, size=S, lead=7.4, see=None):
    """The notes, re-flowed into `cols` columns of the given total width."""
    return notes_block(x, y, width, NOTES, 'MECHANICAL NOTES', 'M-ANNO-TEXT', 'mechanical note', cols, size, lead, 0.22*inch, see)


__all__ = ['place', 'outdoor_schedule', 'ventilation_schedule', 'termination_schedule', 'notes',
           'title', 'grey_context', 'pdfmetrics']

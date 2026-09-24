"""A-001 — the general plan notes, on their own sheet.

Architectural only: layout, glazing, escape, stairs, the mechanical / laundry rooms and the
exhausts' routes. Every other rule has ONE home sheet and this sheet points there — the
assemblies and fire separation on A-601, the schedules and life safety on A-602, the stair
on A-603, grading on C-103, framing, roof and bracing on the S sheets, devices on the E
sheets. A figure quoted here is read from the model that checks it, which is why the list
lives beside the sheet that prints it.
"""
from arkitect.lib.draw.text import textsheet
from arkitect.lib.model.dimensions import wc_clearances
from arkitect.lib.units import fmt, inches
from reportlab.lib.units import inch
from src import clearances as CL
from src.building1 import DR_CLR_MIN, b1_dryer, b1_glazing
from src.building2 import B2_DR_TERM_CLR, GL_U45
from src.finishes import BOARD
from src.openings import WIN_GEOM, WIN_HEAD, WIN_W
from src.schedules import LOUVERED
from src.services import EQUIPMENT
from arkitect.lib.draw.kit import c
from src.stairs import B1_STAIR

GLAZING_MIN, OPENABLE_MIN = 8.0, 4.0          # percent of the floor area, RCO 303.1


def _glazing():
    """(least percent in the house, least in Units 2 / 3), from the checks' own figures."""
    u1 = min(100.0*g/a for g, a, _m in b1_glazing().values())
    return u1, min(GL_U45.values())


def _wc_side():
    """The least clearance from a water closet's centerline to a side obstruction that any
       plan dimensions: the measurement A-101 and A-102 draw and check_clearances() holds.
       To the FINISHED face of a wall, which is why BOARD is passed."""
    return min(min(m['cl']-m['lo'], m['hi']-m['cl'])
               for _lab, r, po, fu in CL.project_plans()
               for m in wc_clearances(r, po, fu, BOARD))


def plan_notes():
    u1, u23 = _glazing()
    assert min(u1, u23) >= GLAZING_MIN, "A-001 note 4 states every habitable room over %g%%" % GLAZING_MIN
    dryer1 = min(d for _nm, d in b1_dryer())
    assert min(dryer1, B2_DR_TERM_CLR) >= DR_CLR_MIN, "A-001 note 12 sends both dryer caps through walls that keep them clear of every opening"
    hp = [b.mark for b in EQUIPMENT if b.kind == "odu"]
    return [
        "1.  DIMENSIONS ARE TO FACE OF STUD. VERIFY ALL DIMENSIONS IN THE FIELD. DO NOT SCALE THE DRAWINGS.",
        "1a. INTERIOR DIMENSION STRINGS ARE CLEAR DIMENSIONS, FACE OF STUD TO FACE OF STUD; PARTITION THICKNESS IS NOT INCLUDED IN THEM. "
        "THE WATER CLOSET CLEARANCES OF NOTE 7 ARE THE EXCEPTION: THEY ARE DIMENSIONED TO FINISHED SURFACES.",
        "2.  WALL TYPES, A-601: EXTERIOR WALLS W1; BUILDING 2'S LEVEL 1 EXTERIOR WALLS W1R AND ITS BEARING WALL W3, TAGGED ON A-102, BOTH 1 HOUR; "
        "EVERY OTHER PARTITION W2.",
        "2a. PENETRATIONS OF W1R, W3 AND THE F1 CEILING: A-601. NOTHING IS CUT INTO A RATED WALL OR CEILING THAT A-601 DOES NOT PROVIDE FOR.",
        "3.  KITCHENS ARE OPEN TO THE LIVING / DINING SPACE, WITH NO PARTITION BETWEEN THEM. THE HALL OF UNITS 2 AND 3 OPENS FROM THE KITCHEN "
        "THROUGH A CASED OPENING, WITHOUT A DOOR.",
        "4.  NATURAL LIGHT AND VENTILATION, RCO 303.1: EVERY HABITABLE ROOM HAS GLAZING OF NOT LESS THAN %g%% OF ITS FLOOR AREA AND OPENABLE "
        "AREA OF %g%%. THE LEAST AS DRAWN IS %.0f%% IN UNIT 1 AND %.0f%% IN UNITS 2 AND 3, THE OPEN LIVING SPACES. DO NOT REMOVE OR REDUCE A "
        "WINDOW." % (GLAZING_MIN, OPENABLE_MIN, u1, u23),
        "5.  EMERGENCY ESCAPE, RCO 310: EVERY SLEEPING ROOM HAS A W-A, %s x %s, SILL %s, HEAD %s. ITS NET CLEAR OPENING IS A PRODUCT "
        "REQUIREMENT: A-602 AND G-001 NOTE 8a." % (fmt(WIN_W['A']), fmt(WIN_GEOM['A'][1]), fmt(WIN_GEOM['A'][0]), fmt(WIN_HEAD['A'])),
        "5a. IN UNITS 2 AND 3 EACH BEDROOM'S ESCAPE OPENING IS THE W-A IN ITS SIDE WALL, AHEAD OF THE FOOT OF THE BED. KEEP IT CLEAR OF FURNITURE.",
        "5b. UNIT 2'S COURTYARD WALL TAKES NO WINDOW: IT STANDS UNDER THE UNIT 3 STAIR'S FLIGHT AND LANDING. UNIT 3'S KITCHEN W-B IS ABOVE THEM.",
        "5c. SAFETY GLAZING, RCO 308.4: THE UNIT 1 LANDING W-A AT THE HEAD OF THE STAIR AND THE GLAZING IN EVERY DOOR. W-D, OVER THE UNIT 1 "
        "STAIR, IS FIXED.",
        "6.  SMOKE AND CARBON MONOXIDE ALARMS: G-001 NOTES 9 AND 10; LOCATIONS ON E-101 AND E-102.",
        "7.  BATHROOMS, RCO 307.1: NOT LESS THAN 15\" FROM THE CENTERLINE OF EVERY WATER CLOSET TO A WALL OR FIXTURE EACH SIDE AND 21\" CLEAR IN "
        "FRONT. THE LEAST SIDE CLEARANCE DRAWN IS %s; THE PLANS DIMENSION EACH." % inches(_wc_side()),
        "7a. EVERY BATHROOM IS INTERIOR AND IS LIT AND MECHANICALLY VENTILATED UNDER RCO 303.3'S EXCEPTION, A-602. CEMENT BOARD AT TUBS AND "
        "SHOWERS, A-601 W2.",
        "8.  UNIT 1 STAIR: %d RISERS AT %s, %d TREADS AT %s, RISING TO THE OAK WALL; A-101 FOR ITS PLAN, A-301 FOR ITS SECTION AND HEADROOM, "
        "S-102 FOR THE WELL'S FRAMING. 36\" GUARD AT THE WELL; HANDRAIL 34\" TO 38\" ABOVE THE NOSINGS, ONE SIDE, RCO 311.7.8."
        % (B1_STAIR.risers, inches(B1_STAIR.riser), B1_STAIR.treads, inches(B1_STAIR.tread)),
        "8a. THE COAT CLOSET UNDER THE STAIR: 1/2\" GYPSUM ON ITS WALLS AND SOFFIT, RCO 302.7, A-601 FB-3.",
        "9.  UNIT 3 EXTERIOR STAIR: A-603. LANDINGS, THE STOOP AND THE STEP OFF EACH: C-103. THE BACK DOOR OF UNIT 1 IS NOT ITS REQUIRED "
        "EGRESS DOOR, A-602.",
        "10. THE PROJECT IS ALL-ELECTRIC. NO FUEL-FIRED APPLIANCE, NO FUEL GAS PIPING AND NO COMBUSTION AIR OPENING IN ANY UNIT.",
        "11. MECHANICAL / LAUNDRY ROOMS: WASHER, DRYER, ELECTRIC WATER HEATER AND THE UNIT PANEL AS DRAWN. KEEP THE WORKING SPACES DRAWN CLEAR: "
        "30\" x 36\" IN FRONT OF THE PANEL, NEC 110.26(A), AND 30\" x 30\" AT THE WATER HEATER, RCO M1305.1. NO STORAGE IN EITHER.",
        "11a. THEIR DOORS, %s, ARE LOUVERED FOR THE DRYER'S MAKEUP AIR: A-602." % " AND ".join(LOUVERED),
        "12. DRYER EXHAUST: UNIT 1 THROUGH THE REAR WALL OVER THE DRYER; UNITS 2 AND 3 THROUGH THE NORTH WALL OVER THE DRYER. DUCT, LENGTHS, "
        "CAPS AND THEIR CLEARANCES: M-101 NOTE 6 AND THE TERMINATION SCHEDULES ON M-101 AND M-102. NO FIRE DAMPER IN A DRYER DUCT, A-601.",
        "13. BATH EXHAUST: A LEVEL 1 FAN DISCHARGES THROUGH A SIDE WALL, A LEVEL 2 FAN THROUGH THE ROOF; CAPS, RATES AND THE WHOLE-HOUSE "
        "VENTILATION FAN: M-101 AND M-102. UNIT 2'S BATH CEILING IS A SOFFIT BELOW THE RATED F1 CEILING; ITS FAN AND DUCT HANG IN IT: A-601 F1 ITEM C.",
        "14. RANGE HOODS: LISTED RECIRCULATING HOODS OVER EVERY RANGE, M-101 NOTE 7.",
        "15. HEATING AND COOLING: ONE HEAT PUMP PER DWELLING — UNIT 1 DUCTED IN TWO ZONES, AN AIR HANDLER CONCEALED IN EACH LEVEL'S HALL SOFFIT; "
        "UNITS 2 AND 3 DUCTLESS. OUTDOOR UNITS %s, THE METERS AND THE TELECOM BOXES ARE ON THE SIDE WALLS, "
        "A-201, A-202 AND C-101. INDOOR UNITS, REGISTERS AND LINE SETS: M-101 AND M-102." % ", ".join(hp),
        "16. ATTIC ACCESS: ONE HATCH IN EACH ATTIC, IN THE LEVEL 2 HALL OF UNIT 1 AND OF UNIT 3, DRAWN; S-103 NOTE 7.",
        "17. PREMISES IDENTIFICATION, RCO 319: ADDRESS NUMBERS NOT LESS THAN 4\" HIGH, CONTRASTING, ON BUILDING 1 FACING OAK AVENUE. UNITS 2 "
        "AND 3 ARE NOT SEEN FROM OAK: POST THEIR NUMBERS AT THE HEAD OF THEIR WALK ON OAK AND AT EACH ENTRY.",
        "18. DOORS, WINDOWS AND FINISHES: A-602. TRIM AND WINDOW COLOR: A-201 NOTES 4 AND 5.",
        "19. SITE, WALKS AND PARKING: C-101. GRADING, SWALES AND DOWNSPOUTS: C-103. FOUNDATIONS: S-101. FRAMING, ROOF AND BRACING: S-102 TO S-104.",
    ]


def sheet_a001():
    textsheet(c, "A-001", "Floor plan general notes",
              "GENERAL PLAN NOTES — APPLY TO A-101 AND A-102", plan_notes(), cols=1, fill=True,
              measure=12.5*inch)          # one column (the designer, 2026-09-18): nineteen notes do not need two

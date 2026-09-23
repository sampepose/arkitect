"""G-001 — the cover: project data, the codes, the design criteria, the area tabulation,
the general notes, the scope of work and the sheet index. Every figure is read from the
model the other sheets are drawn from.

300 S Elm's G-001, which this replaces, carried five units, a corner lot and a variance
table; its original stays in projects/example_300.
"""
import re

from lib.draw.page import ARCH_C, Sheet
from lib.draw.text import table
from lib.units import fmt, inches
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import criteria as crit, levels, stairs
from src.building1 import LEVELS as B1_LEVELS
from src.electrical import CIRCUITS_U1, CIRCUITS_U23, SERVICES
from codes.nec.load import service_loads
from src.foundation import (FROST_DEPTH, FTG_T, FTG_W, STRIP_D, STRIP_W, TERMITE,
                            TERMITE_TREATMENT, WALL_T, WEATHERING)
from src.framing import F1_JOIST, F2_JOIST, JOIST_OC, TRUSS_OC
from src.openings import WIN_GEOM, WIN_HEAD, WIN_W
from codes.ohio.rco.egress import EGRESS_MIN_H, EGRESS_MIN_SF, EGRESS_MIN_W
from lib.draw.kit import X0, X1, Y1, c
from src.sitework import (ADU_SF, COVERAGE, COVERAGE_MAX, LOT_AREA, PARK_N, PARK_REQ,
                          PRINCIPAL_SF, SITE_BLDG, SITE_D, SITE_W)

ADDRESS_LINE = "400 OAK AVENUE — NEW CONSTRUCTION"

# (unit, building, location, bedrooms / baths, stories, net SF, entry, separation)
UNITS = [
    ("1", "1", "LEVELS 1 AND 2", "3BR / 2BA", len(B1_LEVELS), PRINCIPAL_SF,
     "OWN DOOR, OAK AVENUE", "DETACHED"),
    ("2", "2", "LEVEL 1", "2BR / 1BA", 1, ADU_SF, "OWN DOOR AT GRADE, COURTYARD", "1-HR FLOOR ABOVE, S-102 NOTE 5"),
    ("3", "2", "LEVEL 2", "2BR / 1BA", 1, ADU_SF, "EXTERIOR STAIR, COURTYARD", "1-HR FLOOR BELOW, S-102 NOTE 5"),
]
STORIES = 2                                   # both buildings
_B = {b[4]: b for b in SITE_BLDG}
BUILDING_SF = {"1": _B["BUILDING 1"][2]*_B["BUILDING 1"][3], "2": _B["BUILDING 2"][2]*_B["BUILDING 2"][3]}


def gross_sf(u):
    """A unit's gross floor area: its building's footprint on each of its stories."""
    return BUILDING_SF[u[1]]*u[4]


GROSS_SF = sum(gross_sf(u) for u in UNITS)
BEDROOMS = sum(int(u[3].split("BR")[0]) for u in UNITS)


def _heat_pumps():
    """The heat-pump marks, one per dwelling, read from the panel schedules."""
    marks = []
    for cks in (CIRCUITS_U1, CIRCUITS_U23):
        hp = [k for k in cks if k.kind == 'hp']
        assert len(hp) == 1, "G-001 scope of work says one heat pump per dwelling"
        marks += re.findall(r"HP-\d", hp[0].desc)
    assert len(marks) == len(UNITS), marks
    return marks


def _one(cks, kind):
    return sum(1 for k in cks if k.kind == kind)


# ============================= scope of work =============================
def scope_of_work():
    """(trade, where it is drawn, items): the scope the City of Columbus asks for, in its
       four trades. A trade with no sheet in this set is done under its trade permit."""
    joists = sorted({F1_JOIST, F2_JOIST})
    structural = [
        "NEW WOOD-FRAME CONSTRUCTION: TWO DETACHED BUILDINGS, %d STORIES EACH." % STORIES,
        f"FOUNDATIONS: SLAB ON GRADE ON {inches(FTG_W)} x {inches(FTG_T)} CONTINUOUS CONCRETE FOOTINGS, BOTTOM "
        f"{inches(FROST_DEPTH)} MIN BELOW FINISHED GRADE, {inches(WALL_T)} FOUNDATION WALLS, AND {inches(STRIP_W)} WIDE "
        f"x {inches(STRIP_D)} THICKENED BEARING STRIPS UNDER THE HOUSE'S STAIR WALL AND BUILDING 2'S BEARING WALL.",
        "FIRE SEPARATION: THE 1-HOUR FLOOR-CEILING BETWEEN UNITS 2 AND 3 AND THE WALLS UNDER IT, S-102 NOTE 5.",
        "FLOORS: LEVEL 2 ON %s OPEN-WEB WOOD FLOOR TRUSSES AT %s O.C." % (" AND ".join(inches(j) for j in joists), inches(JOIST_OC)),
        "ROOFS: %d:12 GABLES ON PREFABRICATED WOOD TRUSSES AT %s O.C., BEARING ON THE SIDE WALLS."
        % (round(levels.ROOF_PITCH*12), inches(TRUSS_OC)),
        "EXTERIOR STAIR: ONE %s STAIR TO UNIT 3, FRAMED %s TO %s, ON PIERS, S-101."
        % (stairs.MATERIAL, stairs.DESIGN, stairs.CODE),
        "RADON: A PASSIVE SUB-SLAB RISER IN EACH BUILDING, VOLUNTARY, S-101 AND S-103.",
        "SUBMITTALS: THE FLOOR AND ROOF TRUSS DESIGNS, THE LVL HEADERS, AND A %s FOR THE UNIT 3 STAIR." % stairs.SUBMITTAL,
    ]
    panels = {}
    for s in SERVICES:
        for _pos, amps, name in s['positions']:
            panels.setdefault(amps, []).append(name.split()[-1])
    electrical = [
        "SERVICES, NEC 2023: "+"; ".join("%s, %d A AT %s %s" % (s['name'], service_loads(s)[3],
                                          "METER BANK" if len(s['positions']) > 1 else "METER", s['mark'])
                                          for s in SERVICES)+".",
        "PANELS: "+"; ".join("%s %s %d A" % ("UNIT" if len(u) == 1 else "UNITS", " AND ".join(u), a)
                              for a, u in sorted(panels.items(), reverse=True))+".",
        "BRANCH CIRCUITS, RECEPTACLES AND LIGHTING IN EVERY DWELLING, AFCI AND GFCI PROTECTED; HARDWIRED, "
        "INTERCONNECTED SMOKE AND CARBON MONOXIDE ALARMS.",
        "CIRCUITS FOR THE HEAT PUMPS, THE ELECTRIC RANGES AND DRYERS, THE FANS AND THE WATER HEATERS.",
    ]
    hps = _heat_pumps()
    mechanical = [
        "HEATING AND COOLING: ONE AIR-SOURCE HEAT PUMP PER DWELLING, %s TO %s; UNIT 1 DUCTED IN TWO ZONES, THE ADUs DUCTLESS. NO FUEL-FIRED APPLIANCE."
        % (hps[0], hps[-1]),
        "EXHAUST: BATH FANS AND DRYER DUCTS TO THE EXTERIOR; RECIRCULATING RANGE HOODS.",
        "MANUAL J AND S CALCULATIONS AND THE EQUIPMENT SUBMITTALS WITH THE MECHANICAL TRADE PERMIT.",
    ]
    heaters = _one(CIRCUITS_U1, 'wh') + 2*_one(CIRCUITS_U23, 'wh')
    assert heaters == len(UNITS), "G-001 scope of work says one water heater per dwelling"
    plumbing = [
        "WATER HEATING: %d ELECTRIC WATER HEATERS, ONE PER DWELLING." % heaters,
        "WATER SUPPLY, DRAINAGE AND VENT PIPING TO EVERY FIXTURE.",
        "ONE WATER SERVICE AND ONE 4\" BUILDING SEWER TO OAK AVENUE, PER COLUMBUS DPU, C-101 NOTE 8.",
    ]
    return [("STRUCTURAL", "S-101 TO S-104", structural),
            ("ELECTRICAL", "E-101, E-102", electrical),
            ("MECHANICAL", "M-101, M-102", mechanical),
            ("PLUMBING", "P-101 TO P-601", plumbing)]


# ============================= the sheet index =============================
# What the set binds, in order; build.py asserts its own order against this.
SHEET_INDEX = [
    ("G-001", "COVER, CODE DATA, AREA TABULATION, GENERAL NOTES, SCOPE OF WORK"),
    ("C-101", "SITE PLAN"),
    ("C-102", "ZONING SITE PLAN — 11 x 17, ISSUED SEPARATELY"),
    ("C-103", "GRADING AND DRAINAGE PLAN"),
    ("A-001", "FLOOR PLAN GENERAL NOTES"),
    ("A-101", "BUILDING 1 — LEVEL 1 AND LEVEL 2 FLOOR PLANS"),
    ("A-102", "BUILDING 2 — LEVEL 1 AND LEVEL 2 FLOOR PLANS"),
    ("A-201", "BUILDING 1 — EXTERIOR ELEVATIONS"),
    ("A-202", "BUILDING 2 — EXTERIOR ELEVATIONS"),
    ("A-301", "BUILDING SECTIONS, UNIT STACKING, HEIGHT SCHEDULE"),
    ("A-601", "ASSEMBLIES, FIRE SEPARATION SCHEDULE, FIREBLOCKING"),
    ("A-602", "WINDOW, DOOR AND FINISH SCHEDULES, ENERGY COMPLIANCE, LIFE SAFETY"),
    ("A-603", "UNIT 3 EXTERIOR STAIR — SECTION AND DETAILS"),
    ("S-101", "FOUNDATION PLANS — BOTH BUILDINGS"),
    ("S-102", "FLOOR FRAMING PLANS — BOTH BUILDINGS"),
    ("S-103", "ROOF FRAMING PLANS AND DETAILS — BOTH BUILDINGS"),
    ("S-104", "WALL BRACING PLANS AND DETAILS — BOTH BUILDINGS"),
    ("M-101", "BUILDING 1 — MECHANICAL PLANS"),
    ("M-102", "BUILDING 2 — MECHANICAL PLANS"),
    ("E-101", "BUILDING 1 — ELECTRICAL PLANS"),
    ("E-102", "BUILDING 2 — ELECTRICAL PLANS"),
    ("P-101", "SANITARY / UNDER-SLAB PLANS — BOTH BUILDINGS"),
    ("P-102", "BUILDING 1 — WATER SUPPLY PLANS"),
    ("P-103", "BUILDING 2 — WATER SUPPLY PLANS"),
    ("P-601", "PLUMBING RISER DIAGRAM AND NOTES"),
]
SEPARATE = ("C-102",)


def notes():
    """The general notes, one printed line each."""
    return [
        "1.  ALL WORK SHALL COMPLY WITH THE RESIDENTIAL CODE OF OHIO 2019 (OAC 4101:8) AND THE CITY OF COLUMBUS ZONING CODE, TITLE 33.",
        "2.  EVERY DWELLING UNIT HAS AN INDEPENDENT EXTERIOR ENTRANCE; NO SHARED EXITS, COMMON CORRIDORS OR COMMON INTERIOR STAIRS.",
        "3.  NO AUTOMATIC SPRINKLER SYSTEM IS REQUIRED. OHIO HAS NOT ADOPTED IRC R313 AS A MANDATE.",
        "4.  CONTRACTOR SHALL VERIFY ALL DIMENSIONS AND EXISTING CONDITIONS IN THE FIELD BEFORE COMMENCING WORK AND SHALL REPORT ANY DISCREPANCY.",
        "5.  DIMENSIONS ARE TO FACE OF STUD UNLESS NOTED OTHERWISE. DO NOT SCALE DRAWINGS.",
        "6.  ALL HABITABLE ROOMS COMPLY WITH RCO 304.1 (70 SF MINIMUM FLOOR AREA) AND RCO 304.2 (7'-0\" MINIMUM HORIZONTAL DIMENSION).",
        f"7.  FINISHED CEILING HEIGHTS: UNIT 1 LEVEL 1 {fmt(levels.F2_CEILING-levels.FF1)}; UNIT 2 {fmt(levels.F1_CEILING-levels.FF1)}; "
        f"ALL LEVEL 2 {fmt(levels.UPPER_CEILING-levels.FF2)}. RCO 305.1 MINIMUMS:",
        "     HABITABLE SPACE 7'-0\"; BATHROOMS 6'-8\".",
        "8.  EVERY SLEEPING ROOM HAS AN EMERGENCY ESCAPE AND RESCUE OPENING COMPLYING WITH RCO 310.2: 5.7 SF NET CLEAR OPENING (5.0 SF AT GRADE",
        "     FLOOR), 24\" MINIMUM NET CLEAR HEIGHT, 20\" MINIMUM NET CLEAR WIDTH, SILL NOT MORE THAN 44\" ABOVE THE FINISHED FLOOR.",
        f"8a. TYPE W-A IS {fmt(WIN_W['A'])} x {fmt(WIN_GEOM['A'][1])}, SILL {fmt(WIN_GEOM['A'][0])}, HEAD {fmt(WIN_HEAD['A'])}. EVERY W-A SHALL GIVE A NET CLEAR OPENING OF NOT LESS THAN"
        f" {EGRESS_MIN_SF} SF, {inches(EGRESS_MIN_W)} WIDE AND {inches(EGRESS_MIN_H)} HIGH,",
        "     GRADE FLOOR INCLUDED, AS SHOWN BY THE MANUFACTURER'S PRODUCT DATA, SUBMITTED BEFORE ORDERING AND KEPT ON SITE FOR FRAMING INSPECTION.",
        "9.  SMOKE ALARMS PER RCO 314. NOTE RCO 314.1.2: ON EACH LEVEL WITHIN EACH DWELLING UNIT, SMOKE ALARMS UTILIZING BOTH PHOTOELECTRIC AND IONIZATION",
        "     TECHNOLOGIES SHALL BE INSTALLED. HARDWIRED, INTERCONNECTED, WITH BATTERY BACKUP. NOT LESS THAN 3 FT FROM ANY BATHROOM DOOR.",
        "10. CARBON MONOXIDE ALARMS — NOT REQUIRED BY RCO 315, NO FUEL-FIRED APPLIANCE AND NO GARAGE; PROVIDED VOLUNTARILY, E-101 / E-102.",
        "11. STAIRS PER RCO 311.7: MAXIMUM RISER 8-1/4\", MINIMUM TREAD 9\", MINIMUM WIDTH 36\" CLEAR, HEADROOM 6'-8\". HANDRAIL 34\" TO 38\" WHERE 4 OR MORE RISERS.",
        "     GUARDS 36\" MINIMUM WITH 4\" SPHERE LIMITATION PER RCO 312.",
        f"12. FOOTINGS BEAR NOT LESS THAN {inches(FROST_DEPTH)} BELOW FINISHED GRADE PER COLUMBUS CIC-09 AND RCO 403.1.4.1, AND NOT ON FROZEN SOIL — SHEET S-101.",
        "     BOTH BUILDINGS ARE SLAB ON GRADE INSIDE A CONCRETE FOUNDATION WALL. NO BASEMENT IS PROVIDED OR INTENDED; MECHANICAL EQUIPMENT IS",
        "     HOUSED IN A ROOM OR CLOSET WITHIN EACH DWELLING UNIT.",
        f"12a. WIND DESIGN SPEED Vult = {crit.WIND_VULT} MPH (ULTIMATE), RCO TABLE 301.2(1); THE 90 MPH OF COLUMBUS CIC-09 IS ITS NOMINAL (ASD) EQUIVALENT.",
        "13. ENERGY COMPLIANCE BY THE PRESCRIPTIVE PATH, RCO TABLE 1102.1.2, CLIMATE ZONE 5, WITH ONE WALL-BAY EXCEPTION: A-602. BLOWER DOOR TEST REQUIRED",
        "     FOR EACH DWELLING UNIT, 5 ACH50 MAXIMUM.",
        "14. TRADE PERMITS FOR ELECTRICAL, PLUMBING AND MECHANICAL WORK SHALL BE OBTAINED SEPARATELY BY CONTRACTORS REGISTERED WITH THE CITY OF COLUMBUS",
        "     AFTER ISSUANCE OF THE BUILDING PERMIT. THE CITY DOES NOT ISSUE BLANKET PERMITS.",
        "15. SHEET C-102, THE ZONING SITE PLAN, IS ISSUED WITH THIS SET AS A SEPARATE 11\" x 17\" DOCUMENT. IT CARRIES THE ZONING TABULATION OF C-101 AND",
        "     NO CONSTRUCTION INFORMATION. NO ZONING RELIEF IS REQUESTED. C-101 GOVERNS THE WORK.",
    ]


def project_rows():
    return [
        ("Zoning district", "R-4 RESIDENTIAL, H-35"),
        ("Lot area", "{:,.0f} SF  ({} x {})".format(LOT_AREA, fmt(SITE_W), fmt(SITE_D))),
        ("Lot type", "INTERIOR — OAK AVE, ALLEY AT REAR"),
        ("Buildings", "2 DETACHED"),
        ("Dwelling units", "%d — ONE DWELLING AND TWO ADUs" % len(UNITS)),
        ("Bedrooms", str(BEDROOMS)),
        ("Gross floor area", "{:,.0f} SF".format(GROSS_SF)),
        ("Lot coverage", "{:,.0f} SF  =  {:.1f}%  INCL. THE EXTERIOR STAIR".format(COVERAGE, 100*COVERAGE/LOT_AREA)),
        ("Coverage permitted", "{:.0f}% WITH ADU".format(100*COVERAGE_MAX)),
        ("Parking required", "%d, C.C. 3312.49  (ADUs EXEMPT)" % PARK_REQ),
        ("Parking provided", str(PARK_N)),
        ("Zoning relief", "NONE REQUESTED"),
        ("Construction", "WOOD FRAME"),
        ("Foundation", "SLAB ON GRADE; %s x %s CONT. FTG, %s MIN; S-101" % (inches(FTG_W), inches(FTG_T), inches(FROST_DEPTH))),
        ("Stories", "%d EACH BUILDING" % STORIES),
        ("Sprinklers", "NOT REQUIRED"),
    ]


def sheet_g001():
    sh = Sheet(c, "G-001", "Cover, code data, tabulation", "AS NOTED"); sh.frame()
    x = X0; y = Y1-0.4*inch
    c.setFont("Helvetica-Bold", 22); c.drawString(x, y, ADDRESS_LINE)
    y -= 0.30*inch; c.setFont("Helvetica", 12)
    c.drawString(x, y, "TWO DETACHED RESIDENTIAL BUILDINGS · %s DWELLING UNITS · {:,.0f} GROSS SQUARE FEET"
                 .format(GROSS_SF) % ("THREE" if len(UNITS) == 3 else str(len(UNITS))))
    y -= 0.45*inch
    block = lambda title, rows, xx, yy, w=5.9*inch, lh=0.19*inch: table(
        c, xx, yy, title, rows, w, size=8.8, lead=lh, title_size=10, gap=0.24*inch)
    ytop = y
    y1 = block("PROJECT DATA", project_rows(), x, ytop)
    y2 = block("APPLICABLE CODES", [
        ("Building", "RESIDENTIAL CODE OF OHIO 2019"), ("Citation", "OAC 4101:8, EFF. 7-1-2019"),
        ("Amendments", "CH. 4 EFF. 3-1-2024; CH. 34, 44 EFF. 4-15-2024"),
        ("Base code", "2018 IRC, FIRST PRINTING"), ("Scope", "RCO 101.2 — ONE AND TWO FAMILY"),
        ("Electrical", "NFPA 70, 2023 NEC, RCO CH. 34"), ("Energy", "RCO CHAPTER 11, OAC 4101:8-11-01"),
        ("Climate zone", "5A"), ("Zoning", "COLUMBUS C.C. TITLE 33, CH. 3332"),
        ("Design criteria", "COLUMBUS CIC-09, REV. 4-3-2026"),
        ("Design professional", "SEAL NOT REQUIRED, ORC 3791.04(A)(2)(b)"),
        ("Trade permits", "SEPARATE, BY LICENSED SUBS")], x+6.6*inch, ytop)
    y3 = block("DESIGN CRITERIA — TABLE 301.2(1)", [
        ("Ground snow load", crit.psf(crit.GROUND_SNOW)),
        ("Wind speed", "%d MPH ULTIMATE  (Vult)" % crit.WIND_VULT),
        ("Wind exposure", "%s — %s" % (crit.WIND_EXPOSURE, crit.WIND_EXPOSURE_BASIS)),
        ("Seismic design category", "B"), ("Frost line depth", inches(FROST_DEPTH).replace('"', ' IN')),
        ("Weathering", WEATHERING), ("Termite", "%s — %s, S-101" % (TERMITE, TERMITE_TREATMENT)),
        ("Winter design temp", "0 TO 10 F"), ("Ice barrier", "REQUIRED"),
        ("Presumed soil bearing", crit.psf(crit.SOIL_BEARING)), ("Air freezing index", "1048")],
        x+13.2*inch, ytop)
    assert x+13.2*inch+5.9*inch <= X1+1e-6, "G-001's third table runs past the drawing area"
    y = min(y1, y2, y3)-0.25*inch

    # ---- the area tabulation ----
    W = X1-x
    c.setFont("Helvetica-Bold", 10); c.drawString(x, y, "AREA TABULATION"); c.setLineWidth(0.7); c.line(x, y-4, x+W, y-4)
    y -= 0.26*inch
    hdr = ["UNIT", "BUILDING", "LOCATION", "TYPE", "GROSS SF", "NET SF *", "ENTRY", "SEPARATION FROM ADJACENT UNIT"]
    cw = [0.8, 1.1, 2.6, 1.4, 1.2, 1.2, 4.2, 4.4]
    assert sum(cw)*inch <= W, "G-001 area tabulation is wider than the sheet"
    c.setFont("Helvetica-Bold", 8.4); xx = x
    for h, w in zip(hdr, cw): c.drawString(xx, y, h); xx += w*inch
    y -= 0.18*inch
    rows = [(u[0], u[1], u[2], u[3], "{:,.0f}".format(gross_sf(u)), "{:,.0f}".format(u[5]), u[6], u[7]) for u in UNITS]
    rows.append(("", "", "TOTAL — %d UNITS, %d BEDROOMS" % (len(UNITS), BEDROOMS), "", "{:,.0f}".format(GROSS_SF),
                 "{:,.0f}".format(sum(u[5] for u in UNITS)), "%d INDEPENDENT ENTRIES" % len(UNITS), "NO SHARED EXITS"))
    font = "Helvetica"
    for i, r in enumerate(rows):
        if i == len(rows)-1:
            c.setLineWidth(0.5); c.line(x, y+0.12*inch, x+W, y+0.12*inch); font = "Helvetica-Bold"
        c.setFont(font, 8.6); xx = x
        for v, w in zip(r, cw):
            assert pdfmetrics.stringWidth(v, font, 8.6) <= w*inch-4, "G-001 area cell runs over: %r" % v
            c.drawString(xx, y, v); xx += w*inch
        y -= 0.175*inch
    c.setFont("Helvetica", 7.6)
    c.drawString(x, y, "* NET SF STUD FACE TO STUD FACE ON EVERY FLOOR; UNIT 1 LESS ITS STAIR WELL AT LEVEL 2. THE SAME FIGURES AS C-101 AND C-102.")
    y -= 0.34*inch

    # ---- the general notes, the scope of work beside them, the sheet index under ----
    ynotes = y
    NW = 11.2*inch
    c.setFont("Helvetica-Bold", 10); c.drawString(x, y, "GENERAL NOTES"); c.setLineWidth(0.7); c.line(x, y-4, x+NW, y-4)
    y -= 0.26*inch; c.setFont("Helvetica", 8.6)
    ns = notes()
    _nw = max(pdfmetrics.stringWidth(n, "Helvetica", 8.6) for n in ns)
    assert _nw <= NW, "G-001 general notes run %.2f in past their column" % ((_nw-NW)/inch)
    for n in ns:
        c.drawString(x, y, n); y -= 0.15*inch
    y -= 0.22*inch
    c.setFont("Helvetica-Bold", 10); c.drawString(x, y, "SHEET INDEX"); c.setLineWidth(0.7); c.line(x, y-4, x+6.0*inch, y-4)
    y -= 0.26*inch; c.setFont("Helvetica", 8.6)
    for a, b in SHEET_INDEX:
        c.drawString(x, y, a); c.drawString(x+0.9*inch, y, b); last = y; y -= 0.15*inch
    assert last >= ARCH_C.MARG+8, "G-001's sheet index runs into the sheet frame"

    # SCOPE OF WORK: the four trades the City of Columbus asks for, two by two, beside
    # the notes.
    sx = x+NW+0.35*inch; sw = X1-sx
    pad, dash, hd = 0.10*inch, 0.13*inch, 0.20*inch
    cw2 = sw/2.0; tw = cw2-2*pad-dash
    size, slead, gap = 8.0, 0.135*inch, 0.04*inch

    def _wrap(t):
        out = [""]
        for w in t.split():
            trial = (out[-1]+" "+w).strip()
            if out[-1] and pdfmetrics.stringWidth(trial, "Helvetica", size) > tw: out.append(w)
            else: out[-1] = trial
        assert all(pdfmetrics.stringWidth(ln, "Helvetica", size) <= tw for ln in out), \
            "G-001 scope of work: a word wider than its cell in %r" % t
        return out
    cells = []
    for trade, where, items in scope_of_work():
        head = "%s — %s" % (trade, where)
        assert pdfmetrics.stringWidth(head, "Helvetica-Bold", 8.6) <= cw2-2*pad, head
        cells.append((head, [_wrap(t) for t in items]))
    cell_h = lambda cl: 2*pad+hd+sum(len(i)*slead for i in cl[1])+gap*(len(cl[1])-1)
    srows = [cells[0:2], cells[2:4]]
    heights = [max(cell_h(cl) for cl in r) for r in srows]
    c.setFont("Helvetica-Bold", 10); c.drawString(sx, ynotes, "SCOPE OF WORK")
    c.setLineWidth(0.7); c.line(sx, ynotes-4, sx+sw, ynotes-4)
    stop = ynotes-0.12*inch; sbot = stop-sum(heights)
    assert sbot >= ARCH_C.MARG+8, "G-001 scope of work runs into the sheet frame"
    c.setLineWidth(0.5); c.rect(sx, sbot, sw, stop-sbot, stroke=1, fill=0)
    c.line(sx+cw2, sbot, sx+cw2, stop); c.line(sx, stop-heights[0], sx+sw, stop-heights[0])
    yrow = stop
    for r, hgt in zip(srows, heights):
        for i, (head, items) in enumerate(r):
            cx = sx+i*cw2+pad; cy = yrow-pad-0.11*inch
            c.setFont("Helvetica-Bold", 8.6); c.drawString(cx, cy, head)
            cy -= hd; c.setFont("Helvetica", size)
            for lines in items:
                c.drawString(cx, cy, "–")
                for ln in lines:
                    c.drawString(cx+dash, cy, ln); cy -= slead
                cy -= gap
        yrow -= hgt
    c.showPage()

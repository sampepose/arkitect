"""G-001 — the cover: code data, the area tabulation, the general notes, the scope of
   work, the sheet index and the zoning variance table."""
from arkitect.lib.draw.page import Sheet
from arkitect.lib.draw.text import table
from arkitect.lib.units import fmt, inches
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import bracing, drainage, levels, plumbing, stairs
from arkitect.codes.ohio.columbus import criteria as crit
from arkitect.codes.ohio.rco import bracing as rco_bracing
from src.building1 import U2_ENTRY
from src.electrical import SERVICES
from arkitect.codes.nec.load import service_loads
from src.foundation import FROST_DEPTH, FTG_T, FTG_W, STRIP_D, STRIP_W, WALL_T, TERMITE, TERMITE_TREATMENT, WEATHERING
from src.framing import F1_JOIST, F2_JOIST, JOIST_OC
from src.mechanical import outdoor_units
from src.mirror import LIVE_SIDE
from src.openings import WIN_GEOM, WIN_HEAD, WIN_W
from arkitect.codes.ohio.rco.egress import EGRESS_MIN_H, EGRESS_MIN_SF, EGRESS_MIN_W
from src.roof import B1_ROOF, EAVE_OVERHANG, RAKE_OVERHANG, ROOF_PITCH, TRUSS_OC, rake
from src.sitework import COVERAGE, LOT_AREA, MANEUVER, MANEUVER_HAVE, NET_SF, PARK_D, PARK_N, PARK_PITCH, SIDE_YARD_TEXT, VARIANCES, VARIANCE_WORD, VISION_ST, VISION_ST_CLR
from arkitect.lib.draw.page import ARCH_C
from arkitect.lib.draw.kit import X0, X1, Y1, c


def note_8a():
    """W-A's size and the net clear minimums every W-A product must give, A-602's; two
       lines, because G-001 has no vertical room."""
    return [
     f"8a. TYPE W-A IS {fmt(WIN_W['A'])} x {fmt(WIN_GEOM['A'][1])}, SILL {fmt(WIN_GEOM['A'][0])}, HEAD {fmt(WIN_HEAD['A'])}. EVERY W-A SHALL GIVE A NET CLEAR OPENING OF NOT LESS THAN"
     f" {EGRESS_MIN_SF} SF, {inches(EGRESS_MIN_W)} WIDE AND {inches(EGRESS_MIN_H)} HIGH,",
     "     GRADE FLOOR INCLUDED, AS SHOWN BY THE MANUFACTURER'S PRODUCT DATA, SUBMITTED BEFORE ORDERING AND KEPT ON SITE FOR FRAMING INSPECTION. A-602."]


def _and(names):
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1])+" AND "+names[-1]


def _count(n, noun):
    """'1 CS-PF PORTAL FRAME', '2 CS-PF PORTAL FRAMES': a derived count reads right at one."""
    return "%d %s%s" % (n, noun, "" if n == 1 else "S")


# ============================= scope of work =============================
def scope_of_work():
    """The scope of work the City of Columbus asks for, in its four trades, as
       (trade, the sheets it is drawn on, items). Every figure is read from the model the
       trade's own sheets are drawn from, so a service, a heat pump or a stack that
       changes there changes here; arkitect/lib/verify/test_g001.py holds each one to its source."""
    dwellings = len(NET_SF)
    assert EAVE_OVERHANG == RAKE_OVERHANG, "G-001 scope of work gives the eaves and rakes one overhang"
    structural = [
        "NEW WOOD-FRAME CONSTRUCTION: BOTH BUILDINGS, TWO STORIES EACH.",
        f"FOUNDATIONS: SLAB ON GRADE ON {inches(FTG_W)} x {inches(FTG_T)} CONTINUOUS CONCRETE FOOTINGS, BOTTOM "
        f"{inches(FROST_DEPTH)} MIN BELOW FINISHED GRADE, {inches(WALL_T)} FOUNDATION WALLS, AND {inches(STRIP_W)} WIDE x {inches(STRIP_D)} THICKENED BEARING STRIPS UNDER W4 AND THE "
        "INTERIOR BEARING WALLS.",
        "FIRE SEPARATION: THE TWO 1-HOUR W4 WALLS, W4A AND W4B, AND THE 1-HOUR FLOORS BETWEEN STACKED UNITS, AS A-601 LISTS THEM.",
        f"FLOORS: LEVEL 2 ON {inches(F1_JOIST)} AND {inches(F2_JOIST)} I-JOISTS AT {inches(JOIST_OC)} O.C.",
        f"ROOFS: {round(ROOF_PITCH*12):d}:12 GABLES ON PREFABRICATED WOOD TRUSSES AT {inches(TRUSS_OC)} O.C., "
        f"{inches(EAVE_OVERHANG)} OVERHANG AT EAVES AND RAKES, {inches(rake(B1_ROOF, 'REAR'))} AT BUILDING 1'S REAR RAKE, S-103 NOTE 5.",
        "EXTERIOR STAIRS: TWO %s STAIRS, ONE PER BUILDING, FRAMED %s TO %s. A-001 NOTES 13a AND 13b, DETAILS ON A-604."
        % (stairs.MATERIAL, stairs.DESIGN, stairs.CODE),
        "SUBMITTALS: THE I-JOIST AND TRUSS DESIGNS, THE LVL HEADERS, AND A %s FOR BOTH EXTERIOR STAIRS AND THEIR PIERS, A-001 NOTE 13a."
        % stairs.SUBMITTAL,
        "WALL BRACING, RCO 602.10: METHOD %s ON EVERY EXTERIOR WALL, %s AND %d HOLD-DOWNS, S-104."
        % (rco_bracing.METHOD, _count(sum(len(bracing.portal_openings(ln)) for ln in bracing.LINES), "CS-PF PORTAL FRAME"),
           sum(1 for ln in bracing.LINES for e in ln.ends if e.hold_down is not None)),
    ]

    panels = {}
    for s in SERVICES:
        for pos, amps, name in s['positions']:
            if pos.startswith('U'):
                panels.setdefault(amps, []).append(name.split()[-1])
    house = [amps for s in SERVICES for pos, amps, _n in s['positions'] if not pos.startswith('U')]
    assert len(house) == len(SERVICES) and len(set(house)) == 1, \
        "G-001 scope of work says one house panel of one rating in each building: %r" % house
    electrical = [
        "SERVICES, NEC 2023: "+"; ".join("%s, %d A AT METER BANK %s" % (s['name'], service_loads(s)[3], s['mark'])
                                          for s in SERVICES)+". NOTHING ELECTRICAL RUNS BETWEEN THE BUILDINGS.",
        "PANELS: "+"; ".join("%s %s %d A" % ("UNIT" if len(u) == 1 else "UNITS", _and(u), a)
                              for a, u in sorted(panels.items(), reverse=True))
        + "; A %d A HOUSE PANEL IN EACH BUILDING FOR SITE LIGHTING AND THE METER-BANK RECEPTACLE." % house[0],
        "BRANCH CIRCUITS, RECEPTACLES AND LIGHTING IN EVERY DWELLING, AFCI AND GFCI PROTECTED; HARDWIRED, "
        "INTERCONNECTED SMOKE AND CARBON MONOXIDE ALARMS.",
        "CIRCUITS FOR THE HEAT PUMPS WITH THEIR DISCONNECTS, THE ELECTRIC RANGES AND DRYERS, THE FANS AND THE "
        "WATER HEATERS.",
    ]

    hps = outdoor_units()
    assert len(hps) == dwellings, "G-001 scope of work says one heat pump per dwelling"
    mechanical = [
        "HEATING AND COOLING: ONE DUCTLESS AIR-SOURCE HEAT PUMP PER DWELLING, %s TO %s, WITH %d WALL HEADS IN ALL. "
        "NO DUCTWORK, FURNACE OR ELECTRIC RESISTANCE HEAT."
        % (hps[0]['mark'], hps[-1]['mark'], sum(len(r['heads']) for r in hps)),
        "VENTILATION: A CONTINUOUS BATH FAN IN EACH DWELLING FOR RCO 303.4 WHOLE-HOUSE VENTILATION; SWITCHED "
        "EXHAUST FANS IN THE OTHER BATHS.",
        "EXHAUST: DRYER DUCTS; A DUCTED RANGE HOOD IN UNIT 1 AND RECIRCULATING HOODS IN UNITS 2 TO 5.",
        "MANUAL J AND S CALCULATIONS AND THE EQUIPMENT SUBMITTALS WITH THE MECHANICAL TRADE PERMIT.",
    ]

    svc = [(b.name, plumbing.sizes(b)['service']) for b in plumbing.BUILDINGS]
    water = ('ONE %s" SERVICE PER BUILDING' % svc[0][1] if len({s for _b, s in svc}) == 1 else
             "; ".join('%s, A %s" SERVICE' % bs for bs in svc))
    heaters = sum(1 for b in plumbing.BUILDINGS for u in b.units for f in u.fixtures if f.kind == 'wh')
    assert heaters == dwellings, "G-001 scope of work says one water heater per dwelling"
    plumbing_items = [
        "WATER — BASIS SHOWN: %s WITH A SUBMETER FOR EACH DWELLING, MANIFOLDS AND HOME RUNS TO EVERY FIXTURE. FINAL TAP / METER ARRANGEMENT PER COLUMBUS DPU." % water,
        "WATER HEATING: %d ELECTRIC STORAGE WATER HEATERS, ONE PER DWELLING." % heaters,
        "SANITARY: DRAINAGE, VENTS AND %d STACKS; THE BUILDING DRAINS BELOW BOTH SLABS; %s OF BUILDING SEWER ON "
        "THE LOT TO THE ALLEY MAIN, C-101."
        % (sum(len(b.stacks) for b in drainage.BUILDINGS), fmt(drainage.sewer()['on_lot'])),
    ]
    return [("STRUCTURAL", ("S-101", "S-102", "S-103", "S-104", "A-601"), structural),
            ("ELECTRICAL", ("E-101", "E-102"), electrical),
            ("MECHANICAL", ("M-101", "M-102"), mechanical),
            ("PLUMBING", ("P-101", "P-102", "P-103", "P-601"), plumbing_items)]


# ============================= G-001 =============================
# The sheet index, as a module constant so that the thing which decides what the set
# CONTAINS and the thing which checks what it BOUND can read the same list.
# arkitect/lib/verify/test_trace.py compares build_set()'s order against this.
SHEET_INDEX = [("G-001","COVER, CODE DATA, AREA TABULATION, GENERAL NOTES, SCOPE OF WORK"),("C-101","SITE PLAN"),
    ("C-102","ZONING SITE PLAN — 11 x 17, ISSUED SEPARATELY"),("C-103","GRADING AND DRAINAGE PLAN"),
    ("A-001","FLOOR PLAN GENERAL NOTES"),
    ("A-101","BUILDING 1 — LEVEL 1 FLOOR PLAN"),
    ("A-102","BUILDING 1 — LEVEL 2 FLOOR PLAN"),("A-103","BUILDING 2 — LEVEL 1 AND LEVEL 2 FLOOR PLANS"),
    ("A-201","EXTERIOR ELEVATIONS — BUILDING 1, S ELM / SAGE / REAR"),
    ("A-202","EXTERIOR ELEVATIONS — BUILDING 1, ADJACENT PARCEL; ELEVATION NOTES"),
    ("A-203","EXTERIOR ELEVATIONS — BUILDING 2, SAGE / PARCEL / REAR / COURTYARD"),
    ("A-301","BUILDING SECTIONS AND UNIT STACKING DIAGRAM"),
    ("A-601","ASSEMBLIES, FIRE SEPARATION SCHEDULE"),
    ("A-602","DOOR AND WINDOW SCHEDULES, ENERGY COMPLIANCE"),
    ("A-603","W4 SEPARATION SECTIONS — FLOOR LINES, BASE, FIREBLOCKING"),
    ("A-604","EXTERIOR STAIR SECTIONS AND DETAILS — BOTH BUILDINGS"),
    ("S-101","FOUNDATION PLANS — BOTH BUILDINGS"),
    ("S-102","FLOOR FRAMING PLANS — BOTH BUILDINGS"),
    ("S-103","ROOF FRAMING PLANS, STRUCTURAL DETAILS — BOTH BUILDINGS"),
    ("S-104","WALL BRACING PLANS AND DETAILS — BOTH BUILDINGS"),
    ("M-101","BUILDING 1 — MECHANICAL PLANS"),("M-102","BUILDING 2 — MECHANICAL PLANS"),
    ("E-101","BUILDING 1 — ELECTRICAL PLANS"),("E-102","BUILDING 2 — ELECTRICAL PLANS"),
    ("P-101","SANITARY / UNDER-SLAB PLUMBING PLANS — BOTH BUILDINGS"),
    ("P-102","BUILDING 1 — WATER SUPPLY PLANS"),("P-103","BUILDING 2 — WATER SUPPLY PLANS"),
    ("P-601","PLUMBING RISER DIAGRAM")]


def sheet_g001():
    sh=Sheet(c,"G-001","Cover, code data, tabulation","AS NOTED"); sh.frame()
    x=X0; y=Y1-0.4*inch
    c.setFont("Helvetica-Bold",22); c.drawString(x,y,"300 S ELM AVENUE — NEW CONSTRUCTION")
    y-=0.30*inch; c.setFont("Helvetica",12)
    c.drawString(x,y,"TWO DETACHED RESIDENTIAL BUILDINGS · FIVE DWELLING UNITS · 3,952 GROSS SQUARE FEET")
    # The gaps down this sheet were 0.45, 0.30 and 0.22 in; the seven-row variance table
    # took them to 0.36, 0.22 and 0.16.
    y-=0.36*inch
    block=lambda title,rows,xx,yy,w=4.6*inch,lh=0.185*inch: table(
        c,xx,yy,title,rows,w,size=8.6,lead=lh,title_size=10,gap=0.22*inch)
    ytop=y
    y1=block("PROJECT DATA",[("Zoning district","R-4 RESIDENTIAL"),("Lot area","5,040 SF  (40.0' x 126.0')"),
     ("Lot width","40'-0\" EXISTING  —  50'-0\" REQ'D"),("Zoning relief","%d ITEMS — NONE GRANTED, SEE BELOW"%len(VARIANCES)),
     ("Lot type","CORNER — SAGE AVE, ALLEY AT REAR"),("Buildings","2 DETACHED"),("Dwelling units","5"),
     ("Bedrooms","12"),("Gross floor area","3,952 SF"),("Lot coverage","{:,.0f} SF  =  {:.1f}%  INCL. BOTH EXTERIOR STAIRS".format(COVERAGE,100*COVERAGE/LOT_AREA)),
     ("Coverage permitted","65% WITH ADU"),("Parking required","6, C.C. 3312.49  (ADUs EXEMPT)"),
     ("Parking provided","%d — VARIANCE REQUESTED"%PARK_N),("Construction","WOOD FRAME"),("Foundation","SLAB ON GRADE; %s x %s CONT. FTG, %s MIN; S-101"%(inches(FTG_W),inches(FTG_T),inches(FROST_DEPTH))),
     ("Stories","2 EACH BUILDING"),("Sprinklers","NOT REQUIRED")],x,ytop)
    y2=block("APPLICABLE CODES",[("Building","RESIDENTIAL CODE OF OHIO 2019"),("Citation","OAC 4101:8, EFF. 7-1-2019"),
     ("Amendments","CH. 4 EFF. 3-1-2024; CH. 34, 44 EFF. 4-15-2024"),
     ("Base code","2018 IRC, FIRST PRINTING"),("Scope","RCO 101.2 — ONE, TWO, THREE FAMILY"),
     ("Electrical","NFPA 70, 2023 NEC, RCO CH. 34"),("Energy","RCO CHAPTER 11, OAC 4101:8-11-01"),("Climate zone","5A"),
     ("Zoning","COLUMBUS C.C. TITLE 33, CH. 3332"),("Design criteria","COLUMBUS CIC-09, REV. 4-3-2026"),
     ("Design professional","SEAL NOT REQUIRED, ORC 3791.04(A)(2)(b)"),("Trade permits","SEPARATE, BY LICENSED SUBS")],x+5.4*inch,ytop)
    y3=block("DESIGN CRITERIA — TABLE 301.2(1)",[("Ground snow load",crit.psf(crit.GROUND_SNOW)),
     ("Wind speed","%d MPH ULTIMATE  (Vult)"%crit.WIND_VULT),
     ("Wind exposure","%s — %s"%(crit.WIND_EXPOSURE,crit.WIND_EXPOSURE_BASIS)),
     ("Seismic design category","B"),("Frost line depth","32 IN"),("Weathering",WEATHERING),
     ("Termite","%s — %s, S-101"%(TERMITE,TERMITE_TREATMENT)),("Winter design temp","0 TO 10 F"),("Ice barrier","REQUIRED"),
     ("Presumed soil bearing",crit.psf(crit.SOIL_BEARING)),("Air freezing index","1048")],x+10.8*inch,ytop)
    y=min(y1,y2,y3)-0.22*inch

    c.setFont("Helvetica-Bold",10); c.drawString(x,y,"AREA TABULATION"); c.setLineWidth(0.7); c.line(x,y-4,x+15.4*inch,y-4)
    y-=0.24*inch
    hdr=["UNIT","BUILDING","LOCATION","TYPE","GROSS SF","NET SF","ENTRY","SEPARATION FROM ADJACENT UNIT"]
    cw=[0.7,1.0,3.3,1.3,1.0,0.9,2.9,4.3]
    c.setFont("Helvetica-Bold",8.2); xx=x
    for h,w in zip(hdr,cw): c.drawString(xx,y,h); xx+=w*inch
    y-=0.16*inch
    # NET SF is src/sitework.py NET_SF: the zoning table divides the same figures for
    # C.C. 3332.355(B)(3), so the cover and the site plan cannot state different ones.
    net=lambda u: "{:,}".format(NET_SF[u])
    rows=[("1","1","FRONT PORTION, LEVELS 1-2","4BR / 2BA","1,248",net(1),"OWN DOOR, PRIMARY ST.","TWO 1-HR WALLS, RCO 302.2"),
          # name the face each rear-unit entry is actually in, taken from the opening itself
          ("2","1","REAR PORTION, LEVEL 1","2BR / 1BA","624",net(2),
           "OWN DOOR AT GRADE, %s"%("REAR" if U2_ENTRY[3]=='h' else LIVE_SIDE),"1-HR FLOOR ABOVE"),
          ("3","1","REAR PORTION, LEVEL 2","2BR / 1BA","624",net(3),"EXTERIOR STAIR, %s"%LIVE_SIDE,"1-HR FLOOR BELOW"),
          ("4","2","LEVEL 1","2BR / 1BA","728",net(4),"OWN DOOR AT GRADE","1-HR FLOOR ABOVE, RCO 302.3"),
          ("5","2","LEVEL 2","2BR / 1BA","728",net(5),"EXTERIOR STAIR","1-HR FLOOR BELOW, RCO 302.3"),
          ("","","TOTAL — 5 UNITS, 12 BEDROOMS","","3,952","{:,}".format(sum(NET_SF.values())),
           "5 INDEPENDENT ENTRIES","NO SHARED EXITS")]
    c.setFont("Helvetica",8.4)
    for i,r in enumerate(rows):
        if i==len(rows)-1:
            c.setLineWidth(0.5); c.line(x,y+0.11*inch,x+15.4*inch,y+0.11*inch); c.setFont("Helvetica-Bold",8.4)
        xx=x
        for v,w in zip(r,cw): c.drawString(xx,y,v); xx+=w*inch
        y-=0.165*inch
    y-=0.16*inch

    # The scope of work stands beside the notes, from this heading down; the rule stops
    # short of its column so the two headings read as two blocks.
    ynotes=y
    c.setFont("Helvetica-Bold",10); c.drawString(x,y,"GENERAL NOTES"); c.setLineWidth(0.7); c.line(x,y-4,x+10.5*inch,y-4)
    y-=0.24*inch; c.setFont("Helvetica",8.6)
    notes=[
    "1.  ALL WORK SHALL COMPLY WITH THE RESIDENTIAL CODE OF OHIO 2019 (OAC 4101:8) AND THE CITY OF COLUMBUS ZONING CODE, TITLE 33.",
    "2.  EVERY DWELLING UNIT HAS AN INDEPENDENT EXTERIOR ENTRANCE; NO SHARED EXITS, COMMON CORRIDORS OR COMMON INTERIOR STAIRS, RCO 101.2 EXCEPTION 4.",
    "3.  NO AUTOMATIC SPRINKLER SYSTEM IS REQUIRED. OHIO HAS NOT ADOPTED IRC R313 AS A MANDATE.",
    "4.  CONTRACTOR SHALL VERIFY ALL DIMENSIONS AND EXISTING CONDITIONS IN THE FIELD BEFORE COMMENCING WORK AND SHALL REPORT ANY DISCREPANCY.",
    "5.  DIMENSIONS ARE TO FACE OF STUD UNLESS NOTED OTHERWISE. DO NOT SCALE DRAWINGS.",
    "6.  ALL HABITABLE ROOMS COMPLY WITH RCO 304.1 (70 SF MINIMUM FLOOR AREA) AND RCO 304.2 (7'-0\" MINIMUM HORIZONTAL DIMENSION).",
    f"7.  FINISHED CEILING HEIGHTS: UNIT 1 L1 {fmt((levels.F2_CEILING-levels.FF1))}; UNITS 2 / 4 {fmt((levels.F1_CEILING-levels.FF1))}; ALL L2 {fmt((levels.UPPER_CEILING-levels.FF2))}. SEE A-301 HEIGHT SCHEDULE.",
    "     RCO 305.1 MINIMUMS: HABITABLE SPACE 7'-0\"; BATHROOMS 6'-8\". ASSEMBLY DEPTHS / FINISH ALLOWANCES PER A-601.",
    "8.  EVERY SLEEPING ROOM IS PROVIDED WITH AN EMERGENCY ESCAPE AND RESCUE OPENING COMPLYING WITH RCO 310.2: 5.7 SF NET CLEAR OPENING (5.0 SF AT GRADE",
    "     FLOOR), 24\" MINIMUM NET CLEAR HEIGHT, 20\" MINIMUM NET CLEAR WIDTH, SILL NOT MORE THAN 44\" ABOVE THE FINISHED FLOOR. SEE WINDOW SCHEDULE, A-602.",
    *note_8a(),
    "9.  SMOKE ALARMS PER RCO 314. NOTE RCO 314.1.2: ON EACH LEVEL WITHIN EACH DWELLING UNIT, SMOKE ALARMS UTILIZING BOTH PHOTOELECTRIC AND IONIZATION",
    "     TECHNOLOGIES SHALL BE INSTALLED. HARDWIRED, INTERCONNECTED, WITH BATTERY BACKUP. NOT LESS THAN 3 FT FROM ANY BATHROOM DOOR.",
    "10. CARBON MONOXIDE ALARMS — NOT REQUIRED BY RCO 315, NO FUEL-FIRED APPLIANCE AND NO GARAGE; PROVIDED VOLUNTARILY, E-101 / E-102.",
    "11. STAIRS PER RCO 311.7: MAXIMUM RISER 8-1/4\", MINIMUM TREAD 9\", MINIMUM WIDTH 36\" CLEAR, HEADROOM 6'-8\". HANDRAIL 34\" TO 38\" WHERE 4 OR MORE RISERS.",
    "     GUARDS 36\" MINIMUM WITH 4\" SPHERE LIMITATION PER RCO 312.",
    f"12. FOOTINGS BEAR NOT LESS THAN {inches(FROST_DEPTH)} BELOW FINISHED GRADE PER COLUMBUS CIC-09 AND RCO 403.1.4.1, AND NOT ON FROZEN SOIL — SHEET S-101.",
    "     BOTH BUILDINGS ARE SLAB ON GRADE INSIDE A CONCRETE FOUNDATION WALL. NO BASEMENT IS PROVIDED OR INTENDED; MECHANICAL EQUIPMENT IS",
    "     HOUSED IN A CLOSET WITHIN EACH DWELLING UNIT.",
    f"12a. WIND DESIGN SPEED Vult = {crit.WIND_VULT} MPH (ULTIMATE), RCO TABLE 301.2(1); THE 90 MPH OF COLUMBUS CIC-09 IS ITS NOMINAL (ASD) EQUIVALENT.",
    "13. ENERGY COMPLIANCE BY THE PRESCRIPTIVE PATH, RCO TABLE 1102.1.2, CLIMATE ZONE 5. BLOWER DOOR TEST REQUIRED FOR EACH DWELLING UNIT, 5 ACH50 MAXIMUM.",
    "14. TRADE PERMITS FOR ELECTRICAL, PLUMBING AND MECHANICAL WORK SHALL BE OBTAINED SEPARATELY BY CONTRACTORS REGISTERED WITH THE CITY OF COLUMBUS",
    "     AFTER ISSUANCE OF THE BUILDING PERMIT. THE CITY DOES NOT ISSUE BLANKET PERMITS.",
    "15. SHEET C-102, THE ZONING SITE PLAN, IS ISSUED WITH THIS SET AS A SEPARATE 11\" x 17\" DOCUMENT. IT CARRIES THE ZONING TABULATION OF C-101 AND",
    f"     ALL {VARIANCE_WORD} REQUESTED VARIANCES AND NO CONSTRUCTION INFORMATION. ALL ZONING RELIEF SHOWN IS REQUESTED AND NOT YET GRANTED. C-101 GOVERNS THE WORK.",
    ]
    # Orientation is stated once, on C-101 beside the site plan title (C-103 points there).
    # 0.134 in, not 0.155: the rows for requests 4 to 7 took the room the variance block
    # had left under the notes, and S-102's index row took a little more.
    for n in notes:
        c.drawString(x,y,n); y-=0.134*inch
    y-=0.14*inch
    # The scope of work box stands beside the notes (drawn last, below) and the sheet
    # index and the variance block start under both. The notes were once long enough
    # that the index always began below the box; they are not now, so the box is
    # measured here and the index is held down to its bottom.
    sx=x+10.9*inch; sw=X1-sx
    _pad,_dash,_hd = 0.10*inch,0.13*inch,0.20*inch
    _cw=sw/2.0; _tw=_cw-2*_pad-_dash
    _size,_slead,_gap = 8.0,0.132*inch,0.035*inch
    def _wrap(t):
        out=[""]
        for w in t.split():
            trial=(out[-1]+" "+w).strip()
            if out[-1] and pdfmetrics.stringWidth(trial,"Helvetica",_size)>_tw: out.append(w)
            else: out[-1]=trial
        assert all(pdfmetrics.stringWidth(ln,"Helvetica",_size)<=_tw for ln in out), \
            "G-001 scope of work: a word wider than its cell in %r"%t
        return out
    cells=[]
    for trade,sheets,items in scope_of_work():
        head="%s — %s"%(trade,", ".join(sheets))
        assert pdfmetrics.stringWidth(head,"Helvetica-Bold",8.6) <= _cw-2*_pad, \
            "G-001 scope of work heading wider than its cell: %r"%head
        cells.append((head,[_wrap(t) for t in items]))
    _cell_h=lambda cl: 2*_pad+_hd+sum(len(i)*_slead for i in cl[1])+_gap*(len(cl[1])-1)
    srows=[cells[0:2],cells[2:4]]
    heights=[max(_cell_h(cl) for cl in r) for r in srows]
    stop=ynotes-0.12*inch; sbot=stop-sum(heights)
    yidx=min(y, sbot-0.30*inch)
    c.setFont("Helvetica-Bold",10); c.drawString(x,y,"SHEET INDEX"); c.setLineWidth(0.7); c.line(x,y-4,x+6.0*inch,y-4)
    y-=0.24*inch; c.setFont("Helvetica",8.6)
    for a,b in SHEET_INDEX:
        # The pitch has been retuned by hand four times — S-104's row took it from 0.155
        # to 0.148, A-603's to 0.142, A-604's to 0.137, A-203's to 0.134 — and nothing ever checked the
        # result, so the assert below now does. The index may not run under the drawing
        # area, and the next sheet added to the set will say so instead of printing off
        # the bottom of G-001.
        c.drawString(x,y,a); c.drawString(x+0.9*inch,y,b); _last_row=y; y-=0.134*inch
    # The index is the one block on this sheet that runs BELOW Y0, down into the margin
    # band, so the drawing area is not its floor — the sheet frame is. It has been
    # retuned by hand three times without anything checking the result.
    assert _last_row >= ARCH_C.MARG+8, \
        "G-001's sheet index runs into the sheet frame; tighten its row pitch"

    vx,vy,vw=x+7.0*inch,yidx,9.6*inch
    c.setFont("Helvetica-Bold",10)
    c.drawString(vx,vy,"ZONING VARIANCES  —  REQUESTED.  NEW BZA APPLICATION; NONE OF THESE IS GRANTED TO THIS PROJECT")
    c.setLineWidth(0.7); c.line(vx,vy-4,vx+vw,vy-4); vy-=0.24*inch
    vcol=[0,1.5,4.5,5.9]
    c.setFont("Helvetica-Bold",8.2)
    vcol=[0,1.4,3.7,4.9,8.0]
    for pos,h in zip(vcol,("CODE SECTION","STANDARD","REQUIRED","PROVIDED / EXISTING","STATUS")):
        c.drawString(vx+pos*inch,vy,h)
    vy-=0.17*inch; c.setFont("Helvetica",8.4)
    _vrows = ([("C.C. 3332.05","AREA DISTRICT LOT WIDTH","50'-0\"","40'-0\" EXISTING PLATTED WIDTH","REQUESTED"),
               ("C.C. 3312.49","MINIMUM PARKING  (ADUs EXEMPT)","6","%d @ %s x %s, REAR YARD, C-101"
                %(PARK_N,fmt(PARK_PITCH),fmt(PARK_D)),"REQUESTED")]
              +[("C.C. 3332.22(a)(1)","SIDE STREET BUILDING LINE","8'-0\" CLEAR",
                  SIDE_YARD_TEXT,"REQUESTED")]
              +[("C.C. 3312.25","MANEUVERING INTO THE STALLS",fmt(MANEUVER),
                 "%s — THE ALLEY RIGHT-OF-WAY, C-101"%fmt(MANEUVER_HAVE),"REQUESTED"),
                ("C.C. 3321.05(B)(2)","CLEAR VISION, S ELM / SAGE","%s x %s"%(fmt(VISION_ST),fmt(VISION_ST)),
                 "%s x %s CLEAR OF BUILDING 1, C-101"%(fmt(VISION_ST_CLR),fmt(VISION_ST_CLR)),"REQUESTED")])
    # One row per request, in the order the relief block numbers them.
    assert [r[0] for r in _vrows]==[s for s,_n in VARIANCES], [r[0] for r in _vrows]
    for r in _vrows:
        # A cell that runs into the next column prints through it; nothing measured these
        # until the rows for 3312.27 and 3321.05(B)(1) were added.
        for (pos,nxt),v in zip(zip(vcol,vcol[1:]+[vw/inch]),r):
            assert pdfmetrics.stringWidth(v,"Helvetica",8.4) <= (nxt-pos)*inch-4, \
                "G-001 variance cell runs into the next column: %r"%v
        for pos,v in zip(vcol,r): c.drawString(vx+pos*inch,vy,v)
        vy-=0.15*inch
    vy-=0.10*inch
    c.setFont("Helvetica-Bold",8.2)
    c.drawString(vx,vy,"NO VARIANCE IS IN PLACE FOR THIS PROJECT. THE BUILDING PERMIT CANNOT ISSUE UNTIL THE BOARD ACTS ON THE APPLICATION ABOVE.")
    # The statement of hardship is not on this sheet: the permit set goes to Building and
    # Zoning Services and only C-102 is filed with the BZA application (the designer, 2026-09-16).

    # SCOPE OF WORK. The City of Columbus asks for the work divided into Structural,
    # Electrical, Mechanical and Plumbing. The sheet has no vertical room left, but the
    # general notes stop about 10.3 in across a 19.1 in drawing area, so the box stands
    # in the column beside them, from their heading down towards the sheet index. It is
    # drawn last so every record above keeps its place in the trace; its size was taken
    # above, where the index was placed under it. A note long enough to run under it
    # fails the build instead of printing through.
    _nw=max(pdfmetrics.stringWidth(n,"Helvetica",8.6) for n in notes)
    assert x+_nw+0.3*inch <= sx, (
        "G-001 general notes run under the scope of work: the widest is %.2f in of %.2f"
        %(_nw/inch,(sx-x-0.3*inch)/inch))
    c.setFont("Helvetica-Bold",10); c.drawString(sx,ynotes,"SCOPE OF WORK")
    c.setLineWidth(0.7); c.line(sx,ynotes-4,sx+sw,ynotes-4)
    assert sbot >= yidx+0.30*inch, (
        "G-001 scope of work runs into the sheet index: it needs %.2f in and has %.2f in"
        %(sum(heights)/inch,(stop-yidx-0.30*inch)/inch))
    c.setLineWidth(0.5); c.rect(sx,sbot,sw,stop-sbot,stroke=1,fill=0)
    c.line(sx+_cw,sbot,sx+_cw,stop); c.line(sx,stop-heights[0],sx+sw,stop-heights[0])
    yrow=stop
    for r,hgt in zip(srows,heights):
        for i,(head,items) in enumerate(r):
            cx=sx+i*_cw+_pad; cy=yrow-_pad-0.11*inch
            c.setFont("Helvetica-Bold",8.6); c.drawString(cx,cy,head)
            cy-=_hd; c.setFont("Helvetica",_size)
            for lines in items:
                c.drawString(cx,cy,"–")
                for ln in lines:
                    c.drawString(cx+_dash,cy,ln); cy-=_slead
                cy-=_gap
        yrow-=hgt
    c.showPage()

"""A-601 — assemblies and the fire-separation schedule."""
from lib.draw.page import POCHE, Sheet
from lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src.building1 import U3_STAIR_CLR, U3_STAIR_RATED
from src.building2 import U5_STAIR_CLR, U5_STAIR_LINE, U5_STAIR_RATED
from src import fsd
from codes.ohio.rco import fire_separation as rco_fsd
from src.mirror import B1_W
from src.sitework import L2_STOREY, REAR_OPEN_PCT
from src.foundation import EDGE_INSUL_RUN, FROST_DEPTH, FTG_T, FTG_W, GRAVEL_T, INSUL_R_NOM, RETARDER_MIL, SLAB_T, STRIP_D, STRIP_W, WALL_T
from lib.draw.kit import X0, X1, Y0, Y1, c
from src import levels
from src.framing import F1_JOIST, F1_MAX_JOIST_OC, JOIST_OC
from lib.draw.text import wrap_notes
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import Color
from src import fireblocking as fb
from src.roof import B1_ROOF, EAVE_OVERHANG, EAVE_FIREBLOCKED, gable_vented, rake
from src.sitework import LOT_W, PARCEL_WALL_X

PARCEL_YARD = LOT_W-PARCEL_WALL_X
from src.envelope import CLIMATE_ZONE, EXTERIOR_FRAME_WALLS, VR_CLASS, check_wall_rows, perm_text, vr_layer


ASM_WIDTHS = [0.8,9.0,1.7,3.9]      # TYPE, ASSEMBLY, RATING, PERFORMANCE, inches


def wall_rows():
    """The exterior frame walls' ASSEMBLY cells, outside in, each ending with the interior
       vapor retarder of RCO 702.7."""
    vr = ' / ' + vr_layer()
    return {'W1':  'VINYL SIDING / HOUSE WRAP / 7/16" OSB / 2x6 STUDS AT 16" O.C. / R-21 BATT / 1/2" GYPSUM BOARD' + vr,
            'W1R': 'VINYL / WRB / 7/16" OSB / 5/8" TYPE X EXT. GYP. SHEATHING / 2x6 @ 16" O.C. / R-21 / 5/8" TYPE X GYP. INT.' + vr}


def vr_note():
    """The one line under FIRE SEPARATION that says what the rows' last layer is."""
    s = ("VAPOR RETARDER, %s: CLASS %s, RCO 702.7, CLIMATE ZONE %d. PRIMER RATED %s OR LESS, ASTM E96 PROCEDURE A, ON THE INTERIOR GYPSUM AT ITS"
         " RATED COVERAGE, UNDER THE FINISH PAINT. SUBMIT ITS CERTIFIED TEST DATA, 702.7.2, BEFORE HANGING GYPSUM."
         % (' / '.join(EXTERIOR_FRAME_WALLS), VR_CLASS, CLIMATE_ZONE, perm_text()))
    assert pdfmetrics.stringWidth(s, "Helvetica", 7.4) <= 15.4*inch, "A-601 vapor retarder note overruns the schedule rule"
    return s


def _in(v):
    """Inches as the sheets write them: 5/8", 16", 11-7/8" — inches() without its "0-"."""
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


BATT_T = levels.F1_INSUL_T*12   # the mineral wool blanket, inches — drawn only


def _f1_notes():
    """ICC-ES ESR-1153 Figure 3F, Assembly F, top down. The numbers match the tags on the
       section. Every clause is the report's; nothing here is a summary of it."""
    return [
     "1.  FLOOR FINISH, %s ALLOWANCE. NOT PART OF THE LISTING." % _in(levels.FLOOR_FINISH),
     "2.  48/24 SPAN-RATED T&G SHEATHING, EXPOSURE 1, %s NOMINAL, GLUED TO THE TOP FLANGE (ASTM D3498) AND NAILED 8d COMMON AT 6\" O.C. EDGES, 12\" O.C. FIELD. BUTT JOINTS OVER FRAMING." % _in(levels.SUBFLOOR),
     "3.  TJI JOISTS, %s, AT %s O.C., NOMINAL 2x4 OR WIDER FLANGES (%s) — THE MINIMUM TESTED. THE LISTING ALLOWS %s O.C. MAXIMUM. WEB HOLES PER ESR-1153 FIGURE 2 ONLY, P-601 NOTE 1aa." % (_in(F1_JOIST), _in(JOIST_OC), _in(levels.F1_FLANGE_W), _in(F1_MAX_JOIST_OC)),
     "4.  MINERAL WOOL BLANKET, %s, %g PCF MINIMUM, BETWEEN THE BOTTOM FLANGES, FRICTION-FITTED ON TOP OF THE CHANNELS AND SUPPORTED BY THEM." % (_in(levels.F1_INSUL_T), levels.F1_INSUL_PCF),
     "5.  RC-1 RESILIENT CHANNELS AT %s O.C., PERPENDICULAR TO THE JOISTS, 1-5/8\" TYPE S SCREWS AT EACH JOIST. TWO CHANNELS AT EACH BOARD BUTT JOINT, RUN TO THE NEXT JOIST." % _in(levels.F1_CHANNEL_OC),
     "6.  ONE LAYER %s %s GYPSUM BOARD ON THE CHANNELS, 1\" TYPE S SCREWS AT 12\" O.C. IN THE FIELD AND 8\" O.C. AT BUTT JOINTS. TAPE AND FINISH." % (_in(levels.F1_LAYER), levels.F1_BOARD),
     "",
     "A.  BOARD: USG SHEETROCK FIRECODE C OR CERTAINTEED PROROC %s. %s TYPE X TO ASTM C1396 IS NOT AN ALTERNATE." % (levels.F1_BOARD, _in(levels.F1_LAYER)),
     "B.  MEMBRANE TIGHT TO THE EXTERIOR WALLS, RCO 302.3; SUPPORTED BY W3 AND W1R, 302.3.1. S-103 DETAILS 3 AND 4.",
     "C.  THE LISTING TESTS AN UNPIERCED MEMBRANE. BOXES, LUMINAIRES, FANS, PIPES AND DUCTS ARE PROTECTED UNDER RCO 302.4: A-001 NOTE 4a.",
     "D.  FINISHED FLOOR TO CEILING %s; UNITS 2 AND 4 CLEAR CEILING %s, A-301." % (_in(levels.FF2-levels.F1_CEILING), fmt(levels.F1_CEILING-levels.FF1)),
     "E.  SUBMIT BEFORE FRAMING: ESR-1153; JOIST DATA SHOWING THE FLANGE WIDTH; CHANNEL, %s BOARD AND MINERAL WOOL DATA; AND EACH ITEM A-001 NOTE 4a CALLS FOR." % levels.F1_BOARD,
    ]


def _f1_block(x, top, right):
    """F1's listed build-up in the column right of the schedules: a section at
       1-1/2" = 1'-0" with a tag on each layer, then the listing's items."""
    width = right - x
    y = top
    c.setFillColor(black); c.setStrokeColor(black)
    c.setFont("Helvetica-Bold", 11)
    head = "F1 — %s" % levels.F1_LISTING
    assert pdfmetrics.stringWidth(head, "Helvetica-Bold", 11) <= width, "A-601 F1 heading overruns its column"
    c.drawString(x, y, head); y -= 0.10*inch
    c.setLineWidth(0.9); c.line(x, y, right, y); y -= 0.22*inch
    c.setFont("Helvetica", 7.4)
    for t in wrap_notes(["1-HOUR FLOOR-CEILING BETWEEN UNITS 2 AND 3 AND BETWEEN UNITS 4 AND 5, RCO 302.3. ICC-ES ESR-1153 SECTION 4.17 AND FIGURE 3F, TJI JOISTS, SINGLE-LAYER RESILIENT-CHANNEL ASSEMBLY; RATED FROM ASTM E119 TESTS."],
                        width, 7.4, indent=""):
        c.drawString(x, y, t); y -= 0.135*inch
    # --- the section, in real inches from the underside of the face layer
    s = 0.125*inch                                        # 1-1/2" = 1'-0": points per real inch
    gyp, ch = levels.F1_LAYER*12, levels.F1_CHANNEL*12
    joist, sub, fin = F1_JOIST*12, levels.SUBFLOOR*12, levels.FLOOR_FINISH*12
    fw, ft = levels.F1_FLANGE_W*12, levels.F1_FLANGE_T*12   # nominal 2x4 flange, Assembly F
    z_j = levels.F1_LAYERS*gyp + ch                       # joist underside
    z_s = z_j + joist; z_f = z_s + sub; z_t = z_f + fin
    sw = 2.70*inch; span = sw/s                           # real inches shown: two joists
    y0 = y - 0.12*inch - z_t*s
    X = lambda v: x + v*s; Yz = lambda z: y0 + z*s
    c.setLineWidth(0.5); c.setFillColor(white)
    for z0, z1 in ((0, gyp), (z_s, z_f), (z_f, z_t)):
        c.rect(X(0), Yz(z0), sw, (z1-z0)*s, fill=1, stroke=1)
    c.setDash(2, 1.5); c.line(X(0), Yz(gyp+ch/2), X(span), Yz(gyp+ch/2)); c.setDash()
    grey = Color(0.55, 0.55, 0.55)
    joists = [JOIST_OC*12*k + 0.75 for k in range(3) if JOIST_OC*12*k + 0.75 + fw <= span]
    assert len(joists) >= 2, "A-601 F1 section shows fewer than two joists"
    for jx in joists:                                     # I-joist: flanges and web
        c.setFillColor(white)
        c.rect(X(jx), Yz(z_j), fw*s, ft*s, fill=1, stroke=1)
        c.rect(X(jx), Yz(z_s-ft), fw*s, ft*s, fill=1, stroke=1)
        c.rect(X(jx+fw/2-0.1875), Yz(z_j+ft), 0.375*s, (joist-2*ft)*s, fill=1, stroke=1)
    c.setStrokeColor(grey); c.setLineWidth(0.4)
    bays = [(a+fw, b) for a, b in zip(joists, joists[1:])]
    for a, b in bays:                                     # batt, zigzag on the channels
        n = int((b-a)/1.2); pts = []
        for k in range(n+1):
            pts.append((X(a+k*(b-a)/n), Yz(z_j + (BATT_T if k % 2 else 0.0))))
        for p0, p1 in zip(pts, pts[1:]): c.line(p0[0], p0[1], p1[0], p1[1])
    c.setStrokeColor(black); c.setFillColor(black)
    # tags, bottom to top so the leaders never cross
    mids = [(6, gyp/2), (5, gyp+ch/2), (4, z_j+BATT_T/2),
            (3, z_j+joist*0.75), (2, z_s+sub/2), (1, z_f+fin/2)]
    tx = X(span) + 0.28*inch; ty0 = y0 - 0.05*inch; ty1 = Yz(z_t) + 0.05*inch
    c.setFont("Helvetica-Bold", 7); c.setLineWidth(0.35)
    a, b = bays[-1]
    at = {3: X(joists[-1]+fw/2), 4: X(a+(b-a)*0.75)}            # the web, and the blanket
    for k, (n, z) in enumerate(mids):
        ty = ty0 + k*(ty1-ty0)/(len(mids)-1)
        c.line(at.get(n, X(span) - 0.05*inch), Yz(z), tx - 3, ty + 2.5)
        c.drawString(tx, ty, str(n))
    c.setFont("Helvetica-Bold", 8)
    y = y0 - 0.26*inch
    c.drawString(x, y, "F1 SECTION — 1-1/2\" = 1'-0\""); y -= 0.24*inch
    c.setFont("Helvetica", 7.4)
    for t in wrap_notes(_f1_notes(), width, 7.4):
        if t: c.drawString(x, y, t)
        y -= 0.135*inch if t else 0.07*inch
        assert pdfmetrics.stringWidth(t, "Helvetica", 7.4) <= width + 0.5, "A-601 F1 line overruns: " + t
    assert y > Y0 + 0.05*inch, "A-601 F1 block runs off the sheet"
    return y


def _fireblocking_notes():
    """RCO 302.11 and 302.12 under the ids src/fireblocking.py fixes; other sheets cite them.
       Every figure is the model's."""
    F = fb.FB
    zones = fb.W4_BLOCK_ZONES
    hi = max(h for _lo, h in zones.values())
    run = max(r for _, r in fb.W5_RUNS)
    n = fb.w5_blocks(run)[0]
    largest = max(fb.floor_areas().values())
    assert EAVE_OVERHANG > 0.0, "A-601 FB-7 describes the overhanging cornice"
    cornice = ("%s CORNICES: EVERY EAVE FIREBLOCKED ON ITS WALL LINE, TOP PLATE TO ROOF SHEATHING, RCO TABLE 302.1(1) FOOTNOTE a; AT THE W4 LINE ALSO ACROSS THE OVERHANG, SOFFIT TO DECK, ITEM 6. NO EAVE VENT IN THE W4 BAND, S-103." % F['CORNICE'])
    return [
     "%s EACH W4 WALL'S STUD CAVITY IS CLOSED AT ITS OWN FLOOR LINE — %s — BY ITS DOUBLE TOP PLATE, ITS FLOOR'S RIM AND ITS LEVEL 2 SOLE PLATE, AND AGAIN AT THE LEVEL 2 CEILING LINE. THE TWO WALLS TOUCH, SO NO CONCEALED SPACE LIES BETWEEN THEM. ITEM 1.1."
     % (F['W4'], ", ".join("%s FROM +%s" % (nm, fmt(lo)) for nm, (lo, _h) in zones.items())+" TO +%s" % fmt(hi)),
     "%s W5 CHASES, ON W4A'S UNIT 1 FACE AND W4B'S UNITS 2 / 3 FACE, EACH STORY: SOLE PLATE AT THE FLOOR, DOUBLE TOP PLATE AT THE CEILING, ITEM 1.1; STUDS TIGHT TO ITS WALL'S FACE LAYER. WHERE STUDS ARE HELD OFF THAT WALL OR CUT FOR PIPING, FULL-DEPTH 2x BLOCKS AT %s MAXIMUM, ITEM 1.2 — %d IN A %s RUN." % (F['W5'], fmt(fb.W5_BLOCK_MAX), n, fmt(run)),
     "%s FLOOR AND CEILING LINES: WHERE A WALL CAVITY OR CHASE OPENS INTO A FLOOR OR CEILING CAVITY — A PLATE OR RIM CUT OR LEFT OUT, A CHASE CARRIED PAST A FLOOR — CLOSE IT WITH 2x BLOCKING OR 1/2\" GYPSUM. ITEM 2." % F['LINES'],
     "%s PENETRATIONS: FILL THE ANNULAR SPACE AROUND EVERY PIPE, VENT, DUCT, CABLE AND WIRE THROUGH A PLATE WITH FIRE-RATED SEALANT OR MINERAL WOOL, ITEM 4. THROUGH THE F1 CEILING: A-001 NOTE 4a." % F['PENETRATIONS'],
     "%s UNIT 1 STAIR: 2x BLOCKING, FULL STRINGER DEPTH, BETWEEN THE STRINGERS AT THE TOP AND BOTTOM OF THE RUN, ITEM 3. UNDER-STAIR CLOSET: 1/2\" GYPSUM, RCO 302.7, A-001 NOTE 8b." % F['STAIR'],
     "%s SOFFITS AND DROPPED CEILINGS WHEREVER FRAMED, INCLUDING A HALL SOFFIT PER P-601 NOTE 1aa AND ANY PIPE OR VENT BOX: FIREBLOCK WHERE ITS SPACE MEETS A WALL CAVITY AND A FLOOR OR CEILING CAVITY. ITEM 2." % F['SOFFITS'],
     cornice,
     "%s MATERIALS, 302.11.1: 2\" NOMINAL LUMBER; TWO 1\" NOMINAL, JOINTS BROKEN AND LAPPED; 23/32\" WOOD STRUCTURAL PANEL OR 3/4\" PARTICLEBOARD, JOINTS BACKED; 1/2\" GYPSUM; 1/4\" CEMENT MILLBOARD; MINERAL WOOL OR GLASS FIBER BATTS HELD IN PLACE, UNFACED GLASS FIBER FILLING THE CAVITY %s HIGH, 302.11.1.2. NO LOOSE FILL. KEEP EVERY FIREBLOCK WHOLE, 302.11.2." % (F['MATERIALS'], _in(fb.BATT_BLOCK_H)),
     "%s NO DRAFTSTOPPING: THE LARGEST CONCEALED FLOOR-CEILING SPACE IS %s SF, UNDER %s SF; NO CEILING IS SUSPENDED AND NO JOIST IS OPEN-WEB. RCO 302.12." % (F['DRAFTSTOP'], '{:,.0f}'.format(largest), '{:,.0f}'.format(fb.DRAFTSTOP_SF)),
    ]


def _fireblocking_block(x, top, right):
    """The fireblocking notes under F1's, in the same column and setting."""
    width = right - x
    y = top
    c.setFillColor(black); c.setStrokeColor(black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "FIREBLOCKING — RCO 302.11"); y -= 0.10*inch
    c.setLineWidth(0.9); c.line(x, y, right, y); y -= 0.22*inch
    c.setFont("Helvetica", 7.4)
    for t in wrap_notes(["WOOD-FRAMED CONSTRUCTION, BOTH BUILDINGS. ITEMS ARE RCO 302.11'S. THE W4 PLAN DETAIL SHOWS %s AND %s." % (fb.FB['W4'], fb.FB['W5'])]
                        + _fireblocking_notes(), width, 7.4):
        c.drawString(x, y, t); y -= 0.135*inch
        assert pdfmetrics.stringWidth(t, "Helvetica", 7.4) <= width + 0.5, "A-601 fireblocking line overruns: " + t
    assert y > Y0 + 0.05*inch, "A-601 fireblocking notes run off the sheet"



# ============================= A-601 ASSEMBLIES =============================
def sheet_a601():
    sh=Sheet(c,"A-601","Assemblies and fire separation","AS NOTED"); sh.frame()
    x=X0; y=Y1-0.4*inch
    c.setFont("Helvetica-Bold",14); c.drawString(x,y,"ASSEMBLY SCHEDULE"); y-=0.10*inch
    c.setLineWidth(0.9); c.line(x,y,x+15.4*inch,y); y-=0.28*inch
    c.setFont("Helvetica-Bold",8.4)
    for h,w in zip(["TYPE","ASSEMBLY","RATING","PERFORMANCE"],[0.8,9.0,1.7,3.9]):
        c.drawString(x+sum([0.8,9.0,1.7][:0]) if False else x,y,"") 
    xx=x
    for h,w in zip(["TYPE","ASSEMBLY","RATING","PERFORMANCE"],ASM_WIDTHS):
        c.drawString(xx,y,h); xx+=w*inch
    y-=0.17*inch; c.setFont("Helvetica",8.4)
    walls=wall_rows(); check_wall_rows(walls)
    for t,v in walls.items():
        assert pdfmetrics.stringWidth(v,"Helvetica",8.4) <= (ASM_WIDTHS[1]-0.25)*inch, "A-601 %s row overruns its column" % t
    asm=[("W1",walls["W1"],"NONE","R-20 WALL, CZ5"),
     ("W1R",walls["W1R"],"1 HOUR","UL U305 + UL BXUV OSB ADDITION; RCO 302.3.1"),
     ("W6","2x6 INTERIOR WET WALL / 1/2\" GYPSUM EACH FACE; CEMENT BOARD AT TUB","NONE","UNIT 1 BATHROOM STACK B"),
     ("W2","2x4 STUDS AT 16\" O.C. / 1/2\" GYPSUM BOARD BOTH FACES","NONE","INTERIOR PARTITION"),
     ("W3","2x4 STUDS AT 16\" O.C. / ONE 5/8\" UL TYPE SCX GYPSUM LAYER EACH FACE / R-13 BATT","1 HOUR","UL DESIGN U305 — LISTED; RCO 302.3.1"),
     ("W4A","UNIT 1'S SEPARATION WALL: 2x4 @ 16\" O.C. / ONE 5/8\" UL TYPE SCX GYPSUM LAYER EACH FACE / 3-1/2\" EcoBatt","1 HOUR","UL DESIGN U305 — LISTED; 4-3/4\"; DETAILS BELOW AND A-603"),
     ("W4B","UNITS 2 / 3' SEPARATION WALL: THE SAME, BACK TO BACK WITH W4A, INNER LAYERS TOUCHING","1 HOUR","UL DESIGN U305 — LISTED; 9-1/2\" THE PAIR, RCO 302.2"),
     ("W5","2x6 WET WALL, FURRED ON UNIT SIDE OF W4 / 1/2\" GYPSUM — CARRIES ALL SUPPLY, WASTE AND VENT","NONE","PLUMBING CHASE, SEE P-601; FIREBLOCK %s"%fb.FB['W5']),
     ("MC","MECHANICAL ROOMS / CLOSETS — EQUIPMENT AND WORKING SPACE AS DRAWN","NONE","SEE A-001 NOTES 8b, 15 AND 16"),
     ("F1","1/4\" FINISH / 48/24 T&G SUBFLOOR / %s TJI JOISTS @ %s, 2x4 FLANGES / %s MINERAL WOOL / RC-1 @ %s / %d LAYER %s %s"
      %(_in(F1_JOIST),_in(JOIST_OC),_in(levels.F1_INSUL_T),_in(levels.F1_CHANNEL_OC),levels.F1_LAYERS,_in(levels.F1_LAYER),levels.F1_BOARD),
      "1 HOUR","%s — AT RIGHT"%levels.F1_LISTING),
     ("F2","1/4\" FINISH / 3/4\" T&G SUBFLOOR / 14\" I-JOISTS AT 16\" O.C. / 1/2\" GYPSUM CEILING","NONE","14-3/4\" JOIST + SUBFLOOR; SEE A-301"),
     ("R1","ARCH. SHINGLE / ICE BARRIER AT EAVES / 7/16\" OSB / TRUSSES AT 24\" O.C. / R-49 BLOWN / 5/8\" GYPSUM","NONE","R-49; FRT SHEATHING AT W4, SEE BELOW"),
     ("S1","%s CONCRETE SLAB / %d-MIL VAPOR RETARDER / %s CLEAN AGGREGATE / R-%d RIGID AT SLAB EDGE, %s RUN"%(_in(SLAB_T),RETARDER_MIL,_in(GRAVEL_T),int(INSUL_R_NOM),fmt(EDGE_INSUL_RUN)),"--","RCO TABLE 1102.1.2 — SEE S-101"),
     ("FTG","%s x %s CONTINUOUS CONCRETE FOOTING, BOTTOM %s MINIMUM BELOW FINISHED GRADE / %s POURED CONCRETE FOUNDATION WALL"%(inches(FTG_W),inches(FTG_T),inches(FROST_DEPTH),inches(WALL_T)),"--","CIC-09, RCO 403.1.4.1 — SEE S-101"),
     ("FS","INTERIOR BEARING STRIP, %s x %s, UNDER W4, THE UNITS 2 / 3 AND UNITS 4 / 5 BEARING WALLS AND THE UNIT 1 STAIR WALL"%(inches(STRIP_W),inches(STRIP_D)),"--","SEE S-101")]
    for r in asm:
        xx=x
        for v,w in zip(r,ASM_WIDTHS): c.drawString(xx,y,v); xx+=w*inch
        y-=0.175*inch
    y-=0.30*inch
    c.setFont("Helvetica-Bold",14); c.drawString(x,y,"FIRE SEPARATION"); y-=0.10*inch
    c.setLineWidth(0.9); c.line(x,y,x+15.4*inch,y); y-=0.28*inch
    c.setFont("Helvetica-Bold",8.4); xx=x
    for h,w in zip(["LOCATION","CODE SECTION","REQUIRED","ASSEMBLY"],[5.0,2.6,4.4,3.4]):
        c.drawString(xx,y,h); xx+=w*inch
    y-=0.17*inch; c.setFont("Helvetica",8.4)
    # Both stair rows below state "none" outright rather than choosing a branch. The set
    # carries no rated-underside assembly any more, so a branch that could ask for one
    # would be asking for a type the schedule above does not list. check_fsd() is what
    # keeps that true; this is what stops the sheet printing before it is.
    assert not (U3_STAIR_RATED or U5_STAIR_RATED), \
        "A-601 states both stair undersides unrated, and the model now rates one of them"
    # The two roof-edge rows state 0 hours outright, on the footnotes check_fsd() applies.
    assert EAVE_FIREBLOCKED and not gable_vented(B1_ROOF,'REAR'), \
        "A-601 states the rear rake and the parcel eaves at 0 hours under footnotes b and a"
    for r in [("BLDG 1 — UNIT 1 TO UNITS 2 / 3","RCO 302.2","TWO 1-HOUR WALL ASSEMBLIES","W4A / W4B — UL U305 EACH"),
     ("BLDG 1 — UNIT 2 TO UNIT 3","RCO 302.2","1 HOUR, WITHIN A GROUPING","TYPE F1 — ESR-1153 ASSY F"),
     ("BLDG 2 — UNIT 4 TO UNIT 5","RCO 302.3","1 HOUR","TYPE F1 — ESR-1153 ASSY F"),
     ("SUPPORTING CONSTRUCTION","RCO 302.3.1","EQUAL OR GREATER RATING","F1 ON W3 / W1R — UL U305"),
     ("EXTERIOR WALLS, ALL OTHER FACES","RCO TABLE 302.1(1)","NONE — EVERY OTHER FACE OVER 5'-0\"","TYPE W1, UNLIMITED OPENINGS"),
     ("BLDG 1 REAR WALL, BOTH STORIES AND GABLE","RCO 302.1 / TABLE 302.1(1)",
      "%s AT %s FSD TO THE IMAGINARY LINE"%(rco_fsd.wall_rating(fsd.OFF_B1),fmt(fsd.OFF_B1)),
      "W1R; OPENINGS %g / %g SF = %.0f%% (%.0f%% MAX)"
      %(fsd.REAR_OPEN_SF,fsd.rear_wall_sf(B1_W,L2_STOREY),100*REAR_OPEN_PCT,100*rco_fsd.opening_max(fsd.OFF_B1))),
     ("BLDG 1 REAR RAKE","RCO TABLE 302.1(1) NOTE b",
      "0 HOURS AT %s — NO GABLE VENT"%fmt(fsd.OFF_B1-rake(B1_ROOF,'REAR')),
      "%s MAXIMUM, S-103 NOTE 5"%inches(rake(B1_ROOF,'REAR'))),
     ("EAVES, ADJACENT-PARCEL FACES","RCO TABLE 302.1(1) NOTE a",
      "0 HOURS — FIREBLOCKED, PLATE TO DECK",
      "%s MAXIMUM, %s TO THE LOT LINE"%(inches(EAVE_OVERHANG),fmt(PARCEL_YARD-EAVE_OVERHANG))),
     ("UNIT 3 STAIR / LANDING UNDERSIDE","RCO 202 / TABLE 302.1(1)",
      "NONE — FSD %s TO STREET CENTERLINE"%fmt(U3_STAIR_CLR),
      "UNRATED; ALL OF IT FORWARD OF THE REAR WALL"),
     ("UNIT 5 STAIR / LANDING UNDERSIDE","RCO 302.1 / TABLE 302.1(1)",
      "NONE — FSD %s, OVER THE %s OF THE TABLE"%(fmt(U5_STAIR_CLR),fmt(rco_fsd.PROJ_FREE)),
      "UNRATED; %s TO THE %s"%(fmt(U5_STAIR_CLR),U5_STAIR_LINE))]:
        assert "SPRINKLER" not in r[2], \
            "A-601 states the rating this set is built to; it is not sprinklered, G-001 note 3"
        xx=x
        for v,w in zip(r,[5.0,2.6,4.4,3.4]): c.drawString(xx,y,v); xx+=w*inch
        y-=0.175*inch
    y-=0.08*inch
    c.setFont("Helvetica",7.4)
    for t in ["W1R APPLIES WHERE W1 SUPPORTS F1: UNIT 2 EXTERIOR WALLS AND UNIT 4 EXTERIOR WALLS. W3, THE INTERIOR BEARING WALL UNDER F1, IS U305 AS LISTED. FOLLOW UL DESIGN U305 IN FULL FOR BOTH.",
              "W1R ALSO APPLIES TO THE WHOLE OF BUILDING 1'S REAR WALL, BOTH STORIES AND THE GABLE, FOR ITS FIRE SEPARATION DISTANCE: THE SCHEDULE ABOVE. C-101 DIMENSIONS THE LINE.",
              "2x6 STUDS ARE PERMITTED AS LARGER-THAN-LISTED STUDS. ADD 7/16\" OSB OVER THE EXTERIOR TYPE X LAYER PER UL BXUV GUIDANCE;",
              "STAGGER OSB JOINTS FROM GYPSUM JOINTS AND INCREASE OUTERMOST-LAYER FASTENER LENGTH FOR REQUIRED FRAMING PENETRATION.",
              "PENETRATIONS OF W1R: PROTECT PER RCO 302.4 WITH A LISTED THROUGH-PENETRATION SYSTEM OR ANNULAR-SPACE FILL PER THE ASSEMBLY LISTING.",
              "NO DAMPER IN THE DRYER DUCT. SEE A-001 NOTE 2a.",
              vr_note(),
              "FLOOR DEPTHS: F1 = %s FINISHED FLOOR TO CEILING; F2 = %s. EACH INCLUDES %s TOTAL FLOOR-FINISH ALLOWANCE."
              %(_in(levels.FF2-levels.F1_CEILING),_in(levels.FF2-levels.F2_CEILING),_in(levels.FLOOR_FINISH)),
              "BUILD F1 AS %s IN FULL: SUBFLOOR, JOISTS, MINERAL WOOL, CHANNELS, THE %s BOARD AND ITS FASTENING, AT RIGHT."%(levels.F1_LISTING,levels.F1_BOARD),
              "SUBMIT ANY OTHER F1 DESIGN BEFORE FRAMING. A CHANGED CEILING BUILD-UP REVISES A-301 AND S-103; FINISHED FLOOR LEVELS STAY.",
              f"SLAB TOP +{fmt(levels.SLAB_TOP)}; SUBFLOOR TOP +{fmt(levels.SUBFLOOR_TOP)}. FINISH / UNDERLAYMENT TOTAL {inches(levels.FLOOR_FINISH)}; COORDINATE PRODUCT / WET-AREA RECESSES.",
              "ROOF PLATE / TRUSS BOTTOM-CHORD UNDERSIDE +19'-6\"; 5/8\" BOARD BELOW. HEEL / ROOF BUILD-UP TO BE COORDINATED WITH TRUSS DESIGN."]:
        c.drawString(x,y,t); y-=0.145*inch
    y-=0.30*inch
    # The paragraph that explained why Building 1 is split front to back (the rejected
    # floor separation and its 2-hour assembly) came off the sheet on 2026-09-16; the
    # sheet keeps only the instruction. The reasoning is CLAUDE.md's "Building 1 is
    # split front to back" constraint.
    c.setFont("Helvetica-Bold",8.6)
    c.drawString(x,y,"DO NOT ALTER THE UNIT STACKING OR THE W4 SEPARATION WITHOUT REVISED CODE REVIEW, RCO 302.2."); y-=0.165*inch
    y-=0.30*inch
    c.setFont("Helvetica-Bold",12); c.drawString(x,y,"W4A / W4B — TWO UL U305 WALLS / ROOF JUNCTION"); y-=0.24*inch
    c.setFont("Helvetica",8.2)
    for t in [
     "W4A CARRIES UNIT 1'S FLOORS AND CEILINGS, W4B CARRIES UNITS 2 / 3'. EACH IS UL DESIGN",
     "U305, 1 HOUR, LOAD-BEARING: 2x4 STUDS AT 16\" O.C., ONE 5/8\" USG SHEETROCK FIRECODE X (UL TYPE SCX) LAYER ON EACH FACE, 3-1/2\" KNAUF",
     "EcoBatt IN THE CAVITY. THE TWO STAND BACK TO BACK WITH THEIR INNER LAYERS TOUCHING; FINISHED THICKNESS 9-1/2\".",
     "W4A / W4B USE THE RCO 302.2 TWO-WALL OPTION. EACH DWELLING UNIT SHALL REMAIN STRUCTURALLY INDEPENDENT PER RCO 302.2.6.",
     "COMMON-WALL SUBSTITUTION REQUIRES REVISED DRAWINGS AND CODE REVIEW.",
     "FOLLOW THE COMPLETE U305 LISTING FOR BOARD ORIENTATION, JOINT STAGGER, FASTENERS, JOINT TREATMENT AND LOAD LIMITS; SUBMIT BEFORE FRAMING.",
     "EACH WALL'S LAYERS CONTINUE PAST ITS OWN FLOOR EDGES AND THROUGH THE ATTIC TIGHT TO THE ROOF SHEATHING. DO NOT INTERRUPT WITH F2 / F1.",
     "PLATFORM TIERS, FLOOR LINES, BASE AND W4'S FIREBLOCKING AT EACH LEVEL: A-603. SERVICES: A-001 NOTE 4.",
     "NO-PARAPET ROOF CONDITION, RCO 302.2.4 EXCEPTION: FIRE-RETARDANT-TREATED ROOF SHEATHING FOR AT LEAST 4'-0\" EACH SIDE OF W4 WITH A",
     "MINIMUM CLASS C ROOF COVERING (ASTM E108 / UL 790). SIZE SHEATHING AND FASTENERS FOR FRT PRODUCT DESIGN VALUES; FRT WOOD PER RCO 802.1.5 /",
     "803.2.1.2; SUBMIT THE FRT PRODUCT LISTING WITH THE TRUSS PACKAGE. BASE DESIGN: FRT SHEATHING AS SHOWN;",
     "AN ALTERNATE ASSEMBLY REQUIRES AN APPROVED REVISION.",
     "THE W4 MEMBRANES CONTINUE TO THE ROOF SHEATHING PER RCO 302.2.3 AND NO OPENING OR PENETRATION FALLS IN THE 4'-0\" BANDS.",
     "NO OPENINGS / PENETRATIONS IN THE 4'-0\" BANDS: OMIT RIDGE VENT CUTS THERE; OFFSET STACK B / C VENTS IN THEIR OWN ATTICS, NOT THROUGH W4."]:
        c.drawString(x,y,t); y-=0.16*inch

    # Enlarged plan detail: every gypsum layer is visible; plans remain stud-to-stud. The W5
    # chase on each unit face is drawn with its fireblocking, FB-1 / FB-2 in the notes.
    wy0=y-1.65*inch                                  # the roof junction keeps this datum
    us=6.0; wall_len=32*us; wx=x+0.4*inch
    w5, w5g = 5.5, 0.5                               # 2x6 studs, 1/2" gypsum
    zw=w5g+w5                                        # W4A's Unit 1 face
    zt=zw+9.5                                        # W4B's Units 2 / 3 face: the pair is 9-1/2"
    wy=wy0+3*us-(zt+w5+w5g)/2*us                     # centred where the 6" wall used to be
    c.setStrokeColor(black); c.setFillColor(white); c.setLineWidth(.6)
    # each wall's unit-face layer and its inner layer; the two inner layers touch at zw+4.75
    for gz,t in ((0,w5g),(zw,.625),(zw+4.125,.625),(zw+4.75,.625),(zw+8.875,.625),(zt+w5,w5g)):
        c.rect(wx,wy+gz*us,wall_len,t*us,fill=1,stroke=1)
    c.setFillColor(POCHE)
    for zs in (zw+.625,zw+5.375):                    # W4A's studs, then W4B's
        for sx in (0,16): c.rect(wx+sx*us,wy+zs*us,1.5*us,3.5*us,fill=1,stroke=1)
    for z in (w5g,zt):                               # W5 studs tight to W4's face layer
        for sx in (8,24): c.rect(wx+sx*us,wy+z*us,1.5*us,w5*us,fill=1,stroke=1)
    bx=29.0; c.setFillColor(white)                   # a full-depth block, crossed
    c.rect(wx+bx*us,wy+zt*us,1.5*us,w5*us,fill=1,stroke=1)
    c.line(wx+bx*us,wy+zt*us,wx+(bx+1.5)*us,wy+(zt+w5)*us)
    c.line(wx+bx*us,wy+(zt+w5)*us,wx+(bx+1.5)*us,wy+zt*us)
    F=fb.FB
    tags=[((wx+16.75*us,wy+(zt+w5*.65)*us),["W5 CHASE, UNITS 2 / 3 FACE — %s"%F['W5']]),
          ((wx+(bx+.75)*us,wy+(zt+w5*.8)*us),["FULL-DEPTH 2x BLOCK WHERE STUDS ARE HELD OFF ITS WALL",
                                              "OR CUT FOR PIPING, %s MAX — %s"%(fmt(fb.W5_BLOCK_MAX),F['W5'])]),
          ((wx+wall_len-4,wy+(zw+.9)*us),["W4A AND W4B — UL U305 EACH, 1 HOUR: 2x4 @ 16\" O.C.,",
                                          "ONE 5/8\" SCX LAYER EACH FACE, 3-1/2\" EcoBatt; BACK TO",
                                          "BACK, INNER LAYERS TOUCHING, 9-1/2\" FINISHED"]),
          ((wx+9.0*us,wy+(zw+3.0)*us),["EACH WALL'S CAVITY SOLID AT ITS OWN FLOOR AND CEILING LINES — %s"%F['W4']]),
          ((wx+wall_len-4,wy+(w5g+w5/2)*us),["W5 CHASE, UNIT 1 FACE: 2x6 STUDS TIGHT TO W4A,",
                                             "1/2\" GYPSUM, PLATES AT FLOOR AND CEILING — %s"%F['W5']])]
    lx=wx+wall_len+26; ty=wy+(zt+w5+w5g)*us-2; lead=8.6
    c.setFillColor(black); c.setFont("Helvetica",7); c.setLineWidth(.35)
    roof_x=x+9.6*inch-5.25*30.0                      # where the roof junction's deck line starts
    for (ax,ay),lines in tags:
        c.line(ax,ay,lx-3,ty+2.5)
        for t in lines:
            assert lx+pdfmetrics.stringWidth(t,"Helvetica",7) < roof_x-6, "A-601 W4 detail tag runs into the roof junction: "+t
            c.drawString(lx,ty,t); ty-=lead
        ty-=4
    assert ty > wy-6, "A-601 W4 detail tags run below the detail"
    c.setFont("Helvetica-Bold",9); c.drawString(wx,wy-20,"W4 PLAN DETAIL — NOT TO SCALE")
    assert wy-20 > Y0+0.05*inch, "A-601 W4 plan detail runs off the sheet"

    # Longitudinal roof cut: protection measured from the outer finished wall faces.
    rcx=x+9.6*inch; ry=wy0+6*10.0; rs=30.0
    left=rcx-.25*rs; right=rcx+.25*rs
    c.setFillColor(POCHE); c.setLineWidth(.6)
    c.rect(left,ry-85,.5*rs,85,fill=1,stroke=1)
    c.setFillColor(white)
    for dx in (-.25,-.25+.625/12,.25-1.25/12,.25-.625/12):
        c.rect(rcx+dx*rs,ry-85,.625/12*rs,85,fill=1,stroke=1)
    c.line(left-5*rs,ry,right+5*rs,ry)
    c.setLineWidth(4); c.line(left-4*rs,ry+2,right+4*rs,ry+2)
    c.setLineWidth(.5); c.setFont("Helvetica",8); c.setFillColor(black)
    for a,b in ((left-4*rs,left),(right,right+4*rs)):
        c.line(a,ry+21,b,ry+21)
        for xx in (a,b): c.line(xx,ry+16,xx,ry+26)
        c.drawCentredString((a+b)/2,ry+29,"4'-0\" MINIMUM")
    c.setFillColor(black)
    c.drawCentredString(rcx,ry+49,"FRT ROOF SHEATHING / CLASS C MINIMUM COVERING")
    c.drawString(right+14,ry-27,"W4A AND W4B EACH CONTINUOUS TO DECK")
    c.drawString(right+14,ry-41,"NO OPENINGS IN PROTECTED BAND")
    c.setFont("Helvetica-Bold",9)
    c.drawCentredString(rcx,ry-96,"W4 ROOF JUNCTION — NOT TO SCALE")
    _fireblocking_block(X0+16.1*inch, _f1_block(X0+16.1*inch, Y1-0.4*inch, X1)-0.30*inch, X1)
    c.showPage()

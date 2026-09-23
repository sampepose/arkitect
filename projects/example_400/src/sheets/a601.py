"""A-601 — assemblies, the fire-separation schedule, F1's listing, the floor line at a
rated wall, and fireblocking.

400 Oak has one separation: the floor-ceiling between Units 2 and 3, RCO 302.3, and the
Level 1 walls of Building 2 that hold it up, 302.3.1. The house is a detached one-family
dwelling and separates from nothing. Everything else on this sheet is Table 302.1(1)
measured to the side lot lines and to the imaginary line in the courtyard (src/fsd.py).
"""
from arkitect.lib.draw.page import POCHE, Sheet
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import IN, fmt, inches
from reportlab.lib.colors import Color, black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import fsd, levels
from arkitect.codes.ohio.rco import fire_separation as rco_fsd
from src.building1 import B1_D, B1_W
from src.building2 import B2_D, B2_W, U5_STAIR_RATED
from arkitect.codes import ul_u305 as u305
from arkitect.codes.ohio.pipe_in_wall_draw import stack_in_cavity
from src import envelope
from src.envelope import (CAVITY_BATT_R, CLIMATE_ZONE, EXTERIOR_FRAME_WALLS, VR_CLASS,
                          check_wall_rows, perm_text, stack_bay_text, vr_layer)
from src.foundation import (EDGE_INSUL_RUN, FROST_DEPTH, FTG_T, FTG_W, GRAVEL_T, INSUL_R_NOM, RETARDER_MIL,
                            ROOF_OVERHANG, SLAB_T, STRIP_D, STRIP_W, WALL_T)
from src.building2 import U2_SOFFIT_DROP
from src.framing import F1_JOIST, F1_MAX_JOIST_OC, F1_MIN_TRUSS_DEPTH, F2_JOIST, FRAMING, JOIST_OC, TRUSS_OC
from arkitect.lib.draw.kit import X0, X1, Y0, Y1, c
from src.sitework import EAVE_FIREBLOCKED, SIDE_YARD, rear_storeys

DRAFTSTOP_SF = 1000.0          # RCO 302.12: the largest concealed floor-ceiling space without draftstopping
BATT_BLOCK_H = IN(16)          # 302.11.1.2: unfaced glass fiber as a fireblock, its least height
BLOCK_MAX = 10.0               # 302.11 item 1.2: horizontal fireblocking in a furred or double-stud space
STACK_BAY_W = 4.55*inch        # the stack-bay detail's column: its keys and its notes both


ASM_WIDTHS = [0.8,9.0,1.7,3.9]      # TYPE, ASSEMBLY, RATING, PERFORMANCE, inches


def wall_rows():
    """The exterior frame walls' ASSEMBLY cells, outside in, each ending with the interior
       vapor retarder of RCO 702.7."""
    vr = ' / ' + vr_layer()
    r = CAVITY_BATT_R                    # the batt fit.cavity_violations() measures, one figure
    oc = _in(envelope.STUD_OC)           # one definition; A-602's bay area reads the same
    return {'W1':  'VINYL SIDING / HOUSE WRAP / 7/16" OSB / 2x6 STUDS AT %s O.C. / R-%d BATT / 1/2" GYPSUM BOARD' % (oc, r) + vr,
            'W1R': 'VINYL / WRB / 7/16" OSB / 5/8" TYPE X EXT. GYP. SHEATHING / 2x6 @ %s O.C. / R-%d / 5/8" TYPE X GYP. INT.' % (oc, r) + vr}


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


def _f1_notes():
    """UL Design L528, top down, from UL Product iQ's text of 2025-06-30. The numbers match
       the tags on the section. Every clause is the design's; nothing here is a summary of it."""
    return [
     "1.  FLOOR FINISH, %s ALLOWANCE. NOT PART OF THE LISTING." % _in(levels.FLOOR_FINISH),
     "2.  FLOORING SYSTEM NO. 1: %s NOMINAL (23/32\") T&G WOOD STRUCTURAL PANELS, UNDERLAYMENT OR SINGLE-FLOOR GRADE, STRENGTH AXIS ACROSS THE TRUSSES, END JOINTS STAGGERED 4'-0\"; CONSTRUCTION ADHESIVE AND 6d RING-SHANK NAILS AT 12\" O.C. ALONG EACH TRUSS." % _in(levels.SUBFLOOR),
     "3.  PARALLEL-CHORD WOOD TRUSSES OF NOMINAL 2x4 LUMBER, %s DEEP AT %s O.C. (THE DESIGN: %s MINIMUM, %s O.C. MAXIMUM), NO. 20 MSG GALVANIZED STEEL PLATES. S-102." % (_in(F1_JOIST), _in(JOIST_OC), _in(F1_MIN_TRUSS_DEPTH), _in(F1_MAX_JOIST_OC)),
     "4.  ITEM 3A RESILIENT CHANNELS, NO. 26 MSG GALVANIZED STEEL, AT %s O.C., PERPENDICULAR TO THE TRUSSES, A 1-1/4\" TYPE S SCREW AT EACH TRUSS; SPLICES LAPPED 4\". TWO CHANNELS AT EACH BOARD END JOINT, 6\" PAST BOTH EDGES OF THE BOARD." % _in(levels.F1_CHANNEL_OC),
     "5.  ITEM 4: ONE LAYER %s %s GYPSUM BOARD, 4'-0\" WIDE, LONG DIMENSION ACROSS THE CHANNELS, 1\" TYPE S SCREWS AT 12\" O.C., 1-1/2\" FROM SIDE AND END JOINTS. TAPE AND TWO COATS." % (_in(levels.F1_LAYER), levels.F1_BOARD),
     "",
     "A.  BOARD: %s %s BEARING THE UL MARK, OF A TYPE ITEM 4 LISTS: USG C, CERTAINTEED C, NATIONAL GYPSUM FSW-C AND OTHERS. TYPE X IS NOT AN ALTERNATE." % (_in(levels.F1_LAYER), levels.F1_BOARD),
     "B.  NO INSULATION IN THE CAVITY: NO BATTS OR BLOWN FIBER BETWEEN THE TRUSSES. PIPES, CABLES AND LINE SETS PASS THROUGH THE OPEN WEBS WITHOUT PIERCING THE MEMBRANE, S-102 NOTE 6; A PENETRATION OF THE MEMBRANE IS ITEM C.",
     "C.  NO FAN, DUCT OR RECESSED LUMINAIRE PIERCES THE MEMBRANE. UNIT 2'S BATH CEILING IS A SOFFIT %s BELOW IT, A-102: THE FAN, ITS DUCT AND THE LIGHT HANG IN THE SOFFIT. ELSEWHERE IN UNIT 2: SURFACE LUMINAIRES ON STEEL BOXES NOT OVER 16 SQ IN, RCO 302.4.2; PIPES THROUGH LISTED FIRESTOP SYSTEMS." % _in(U2_SOFFIT_DROP),
     "D.  MEMBRANE TIGHT TO THE EXTERIOR WALLS, RCO 302.3; SUPPORTED BY W3 AND W1R, 302.3.1. DETAIL BELOW THE SCHEDULES.",
     "E.  FINISHED FLOOR TO CEILING %s; UNIT 2 CLEAR CEILING %s, %s UNDER THE BATH'S SOFFIT." % (_in(levels.FF2-levels.F1_CEILING), fmt(levels.F1_CEILING-levels.FF1), fmt(levels.F1_CEILING-U2_SOFFIT_DROP-levels.FF1)),
     "F.  SUBMIT BEFORE FABRICATION: UL DESIGN L528, THE SEALED TRUSS DESIGN DRAWINGS, AND THE CHANNEL AND BOARD DATA.",
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
    for t in wrap_notes(["1-HOUR FLOOR-CEILING BETWEEN UNITS 2 AND 3, BUILDING 2, RCO 302.3. UL DESIGN L528, UNRESTRAINED ASSEMBLY RATING 1 HR: OPEN-WEB WOOD FLOOR TRUSSES, ONE LAYER ON RESILIENT CHANNELS; ANSI/UL 263."],
                        width, 7.4, indent=""):
        c.drawString(x, y, t); y -= 0.135*inch
    # --- the section, in real inches from the underside of the face layer
    gyp, ch = levels.F1_LAYER*12, levels.F1_CHANNEL*12
    joist, sub, fin = F1_JOIST*12, levels.SUBFLOOR*12, levels.FLOOR_FINISH*12
    fw, ft = levels.F1_CHORD_W*12, levels.F1_CHORD_T*12     # nominal 2x4 chords, flat, L528 Item 2
    z_j = levels.F1_LAYERS*gyp + ch                       # joist underside
    z_s = z_j + joist; z_f = z_s + sub; z_t = z_f + fin
    span = 0.75 + JOIST_OC*12 + fw + 0.75                 # real inches shown: two trusses at JOIST_OC
    # The largest standard scale at which those two trusses and their tags fit the column.
    TAGS = 0.38*inch
    s, scale = next((v/12.0*inch, t) for v, t in ((1.5, '1-1/2" = 1\'-0"'), (1.0, '1" = 1\'-0"'), (0.75, '3/4" = 1\'-0"'))
                    if span*(v/12.0*inch) + TAGS <= width)
    sw = span*s
    y0 = y - 0.12*inch - z_t*s
    X = lambda v: x + v*s; Yz = lambda z: y0 + z*s
    c.setLineWidth(0.5); c.setFillColor(white)
    for z0, z1 in ((0, gyp), (z_s, z_f), (z_f, z_t)):
        c.rect(X(0), Yz(z0), sw, (z1-z0)*s, fill=1, stroke=1)
    c.setDash(2, 1.5); c.line(X(0), Yz(gyp+ch/2), X(span), Yz(gyp+ch/2)); c.setDash()
    grey = Color(0.55, 0.55, 0.55)
    joists = [JOIST_OC*12*k + 0.75 for k in range(3) if JOIST_OC*12*k + 0.75 + fw <= span]
    assert len(joists) >= 2, "A-601 F1 section shows fewer than two joists"
    for jx in joists:                                     # a truss end-on: its two chords, a web between them
        c.setFillColor(white)
        c.rect(X(jx), Yz(z_j), fw*s, ft*s, fill=1, stroke=1)
        c.rect(X(jx), Yz(z_s-ft), fw*s, ft*s, fill=1, stroke=1)
        c.setDash(2, 1.5); c.setStrokeColor(grey)
        c.line(X(jx), Yz(z_j+ft), X(jx+fw), Yz(z_s-ft)); c.line(X(jx+fw), Yz(z_j+ft), X(jx), Yz(z_s-ft))
        c.setDash(); c.setStrokeColor(black)
    c.setStrokeColor(black); c.setFillColor(black)
    # tags, bottom to top so the leaders never cross
    mids = [(5, gyp/2), (4, gyp+ch/2),
            (3, z_j+joist*0.75), (2, z_s+sub/2), (1, z_f+fin/2)]
    tx = X(span) + 0.28*inch; ty0 = y0 - 0.05*inch; ty1 = Yz(z_t) + 0.05*inch
    assert tx + 6 <= right, "A-601 F1 section and its tags run past the column"
    c.setFont("Helvetica-Bold", 7); c.setLineWidth(0.35)
    at = {3: X(joists[-1]+fw/2)}                                # the truss
    for k, (n, z) in enumerate(mids):
        ty = ty0 + k*(ty1-ty0)/(len(mids)-1)
        c.line(at.get(n, X(span) - 0.05*inch), Yz(z), tx - 3, ty + 2.5)
        c.drawString(tx, ty, str(n))
    c.setFont("Helvetica-Bold", 8)
    y = y0 - 0.26*inch
    c.drawString(x, y, "F1 SECTION — %s" % scale); y -= 0.24*inch
    c.setFont("Helvetica", 7.4)
    for t in wrap_notes(_f1_notes(), width, 7.4):
        if t: c.drawString(x, y, t)
        y -= 0.135*inch if t else 0.07*inch
        assert pdfmetrics.stringWidth(t, "Helvetica", 7.4) <= width + 0.5, "A-601 F1 line overruns: " + t
    assert y > Y0 + 0.05*inch, "A-601 F1 block runs off the sheet"
    return y


def floor_areas():
    """Each framed floor's concealed space, SF, stud face to stud face: RCO 302.12."""
    return {"BUILDING 1 F2": (B1_W-2*EXT_STUD)*(B1_D-2*EXT_STUD), "BUILDING 2 F1": (B2_W-2*EXT_STUD)*(B2_D-2*EXT_STUD)}


FB = {k: "FB-%d" % (i+1) for i, k in enumerate(("LINES", "SOFFITS", "STAIR", "PENETRATIONS", "EAVES", "MATERIALS", "DRAFTSTOP"))}


def _fireblocking_notes():
    """RCO 302.11 and 302.12. Every figure is the model's."""
    largest = max(floor_areas().values())
    assert largest <= DRAFTSTOP_SF, "a floor-ceiling's concealed space passes RCO 302.12's %d SF" % DRAFTSTOP_SF
    assert EAVE_FIREBLOCKED, "A-601 FB-5 states every eave fireblocked"
    return [
     "%s FLOOR AND CEILING LINES: EVERY STUD CAVITY IS CLOSED AT EACH FLOOR AND CEILING LINE BY ITS PLATES AND, AT LEVEL 2, THE FLOOR'S RIM OR FULL-DEPTH BLOCKING, ITEM 1.1; A FURRED OR DOUBLE-STUD SPACE ALSO AT %s MAXIMUM HORIZONTALLY, ITEM 1.2. THE DETAIL SHOWS THE LINE AT A RATED WALL." % (FB['LINES'], fmt(BLOCK_MAX)),
     "%s SOFFITS, DROPPED CEILINGS AND CHASES WHEREVER FRAMED: FIREBLOCK WHERE THE SPACE MEETS A WALL CAVITY AND A FLOOR OR CEILING CAVITY, ITEM 2." % FB['SOFFITS'],
     "%s UNIT 1 STAIR: 2x BLOCKING, FULL STRINGER DEPTH, BETWEEN THE STRINGERS AT THE TOP AND BOTTOM OF THE RUN, ITEM 3. THE CLOSET UNDER IT: 1/2\" GYPSUM ON ITS WALLS AND SOFFIT, RCO 302.7." % FB['STAIR'],
     "%s PENETRATIONS: FILL THE ANNULAR SPACE AROUND EVERY PIPE, VENT, DUCT, CABLE AND WIRE THROUGH A PLATE WITH FIRE-RATED SEALANT OR MINERAL WOOL, ITEM 4. THROUGH THE F1 CEILING OR W1R / W3: F1 ITEM C AND RCO 302.4." % FB['PENETRATIONS'],
     "%s EAVES, BOTH BUILDINGS, %s FROM THE SIDE LOT LINES: FIREBLOCKED ON THE WALL LINE, TOP PLATE TO ROOF SHEATHING, RCO TABLE 302.1(1) FOOTNOTE a. SOFFITS SOLID; ATTIC INTAKE BY SHINGLE-OVER EAVE VENTS INBOARD OF THE BLOCK, S-103 NOTE 6." % (FB['EAVES'], fmt(SIDE_YARD-ROOF_OVERHANG)),
     "%s MATERIALS, 302.11.1: 2\" NOMINAL LUMBER; TWO 1\" NOMINAL, JOINTS BROKEN AND LAPPED; 23/32\" WOOD STRUCTURAL PANEL OR 3/4\" PARTICLEBOARD, JOINTS BACKED; 1/2\" GYPSUM; 1/4\" CEMENT MILLBOARD; MINERAL WOOL OR GLASS FIBER BATTS HELD IN PLACE, UNFACED GLASS FIBER FILLING THE CAVITY %s HIGH, 302.11.1.2. NO LOOSE FILL. KEEP EVERY FIREBLOCK WHOLE, 302.11.2." % (FB['MATERIALS'], _in(BATT_BLOCK_H)),
     "%s NO DRAFTSTOPPING: THE FLOORS ARE %s, AND THE LARGEST CONCEALED FLOOR-CEILING SPACE IS %s SF, UNDER THE %s SF OF RCO 302.12." % (FB['DRAFTSTOP'], FRAMING, '{:,.0f}'.format(largest), '{:,.0f}'.format(DRAFTSTOP_SF)),
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
    for t in wrap_notes(["WOOD-FRAMED CONSTRUCTION, BOTH BUILDINGS. ITEMS ARE RCO 302.11'S."] + _fireblocking_notes(), width, 7.4):
        c.drawString(x, y, t); y -= 0.135*inch
        assert pdfmetrics.stringWidth(t, "Helvetica", 7.4) <= width + 0.5, "A-601 fireblocking line overruns: " + t
    assert y > Y0 + 0.05*inch, "A-601 fireblocking notes run off the sheet"


def _floor_line(x, ytop):
    """F1's floor line at a Level 1 wall that bears it, 1-1/2" = 1'-0": the rated wall below,
       the rim, the ceiling membrane tight to the wall board. Real inches; x from the stud's
       outside face inward, z from the top of the Level 1 plate."""
    s = 0.125*inch
    J, SUB = F1_JOIST*12, levels.SUBFLOOR*12
    CH, GY = levels.F1_CHANNEL*12, levels.F1_LAYER*12
    ST, X58, OSB, RIM = EXT_STUD*12, 0.625, 0.4375, 1.25
    zlo, zhi, xin = -13.0, J+SUB+11.0, 27.0
    ox = x+0.35*inch+(OSB+X58)*s; oy = ytop-(zhi)*s
    Xp = lambda v: ox+v*s; Zp = lambda v: oy+v*s
    c.setStrokeColor(black); c.setLineWidth(0.5)
    def box(x0, z0, x1, z1, fill=white):
        c.setFillColor(fill); c.rect(Xp(x0), Zp(z0), (x1-x0)*s, (z1-z0)*s, fill=1, stroke=1)
    box(0, zlo, ST, -3.0)                                   # the Level 1 stud
    box(0, -3.0, ST, -1.5, POCHE); box(0, -1.5, ST, 0.0, POCHE)     # double top plate
    box(-X58, zlo, 0, J+SUB)                                # exterior Type X, up the rim
    box(-X58-OSB, zlo, -X58, zhi)                           # OSB
    box(ST, zlo, ST+X58, -CH-GY)                            # interior Type X, to the ceiling board
    box(0, 0, RIM, J, POCHE)                                # rim board
    box(RIM, 0, xin, 1.5); box(RIM, J-1.5, xin, J)          # the truss beyond: its chords
    c.setLineWidth(0.3)                                     # and its open webs
    for _a, _b in ((ST+2, xin-6), (xin-6, xin)):
        c.line(Xp(_a), Zp(1.5), Xp((_a+_b)/2.0), Zp(J-1.5)); c.line(Xp((_a+_b)/2.0), Zp(J-1.5), Xp(_b), Zp(1.5))
    c.setLineWidth(0.5)
    c.setDash(2, 1.5); c.rect(Xp(RIM), Zp(0), ST*s-RIM*s, J*s, fill=0, stroke=1); c.setDash()   # blocking at the bearing
    box(-X58, J, xin, J+SUB)                                # subfloor
    box(0, J+SUB, ST, J+SUB+1.5, POCHE)                     # Level 2 sole plate
    box(0, J+SUB+1.5, ST, zhi)                              # Level 2 stud
    box(ST, J+SUB+levels.FLOOR_FINISH*12, ST+0.5, zhi)      # Level 2 interior gypsum
    c.setDash(2, 1.5); c.line(Xp(ST+X58), Zp(-CH/2.0), Xp(xin), Zp(-CH/2.0)); c.setDash()       # RC-1
    box(ST+X58, -CH-GY, xin, -CH)                           # the ceiling board, tight to the wall board
    # tags
    tx = Xp(xin)+0.30*inch
    tags = [((ST/2, zhi-4), "W1 ABOVE, LEVEL 2 — UNRATED"),
            ((12, J+SUB/2), "%s T&G SUBFLOOR" % _in(levels.SUBFLOOR)),
            ((RIM/2, J*0.62), "RIM BOARD, FULL DEPTH, NAILED TO THE PLATE: WITH THE PLATES, THE FIREBLOCK AT THE FLOOR LINE — %s" % FB['LINES']),
            ((15, J-0.75), "F1 %s FLOOR TRUSSES; SOLID FULL-DEPTH BLOCKING PANELS BETWEEN THEM AT THE BEARING, CLOSING THE OPEN WEBS" % _in(F1_JOIST)),
            ((-X58/2, J*0.25), "EXTERIOR 5/8\" TYPE X CARRIED UP THE RIM TO THE SUBFLOOR"),
            ((ST/2, -1.5), "DOUBLE TOP PLATE"),
            ((14, -CH-GY/2), "RESILIENT CHANNELS AND %s %s CEILING, TIGHT TO THE WALL BOARD; JOINT TAPED AND SEALED, RCO 302.3" % (_in(levels.F1_LAYER), levels.F1_BOARD)),
            ((ST+X58/2, zlo+3), "W1R BELOW — 5/8\" TYPE X EACH FACE, UL U305, 1 HOUR: RCO 302.3.1")]
    c.setFont("Helvetica", 6.6); c.setLineWidth(0.35)
    ty1, ty0 = Zp(zhi)-6, Zp(zlo)+2
    for k, ((px, pz), t) in enumerate(sorted(tags, key=lambda q: -q[0][1])):      # top down, so no leaders cross
        ty = ty1-k*(ty1-ty0)/(len(tags)-1)
        c.setStrokeColor(black); c.line(Xp(px), Zp(pz), tx-3, ty+2.2)
        c.setFillColor(black); c.drawString(tx, ty, t)
    c.setFillColor(black); c.setFont("Helvetica-Bold", 9)
    c.drawString(x, Zp(zlo)-0.22*inch, "F1 AT A BEARING WALL — BUILDING 2'S COURTYARD AND REAR WALLS  ·  1-1/2\" = 1'-0\"")
    c.setFont("Helvetica", 7.4)
    c.drawString(x, Zp(zlo)-0.38*inch, "AT THE SIDE WALLS THE JOISTS RUN PARALLEL: THE RIM OR FULL-DEPTH BLOCKING THERE IS RATED FOR THE WALL ABOVE, S-102 NOTE 2. W3, THE BEARING WALL, TAKES BOTH BAYS ON ITS PLATE THE SAME WAY.")
    return Zp(zlo)-0.38*inch


# ============================= A-601 ASSEMBLIES =============================
def fire_separation_rows():
    """The FIRE SEPARATION schedule: LOCATION, CODE SECTION, REQUIRED, ASSEMBLY.
       Every distance is read from src/fsd.py. The stair's last two cells are two
       different conditions of the same face — the maximum projection the rating is
       read at, and the stair as drawn — so neither may carry the other's clearance:
       at 8'-9" a 3'-9" projection leaves 5'-0" and the 3'-6" drawn leaves 5'-3"."""
    assert not U5_STAIR_RATED, "A-601 states the Unit 3 stair's underside unrated, and the model now rates it"
    assert rco_fsd.wall_rating(fsd.OFF_B1) == 'NONE' and rco_fsd.wall_rating(SIDE_YARD) == 'NONE', "A-601 states every exterior wall unrated by distance"
    assert fsd.OFF_B1-ROOF_OVERHANG >= rco_fsd.PROJ_FREE, "A-601 states the rear rake at 0 hours by distance"
    assert fsd.STAIR_W <= fsd.PROJ_MAX and abs(fsd.stair_clear()+fsd.STAIR_W-fsd.OFF_B2) < 1e-9, \
        "A-601 states the stair drawn and the stair permitted as one condition each"
    st = rear_storeys()
    return [("BUILDING 2 — UNIT 2 TO UNIT 3","RCO 302.3","1 HOUR","TYPE F1 — UL DESIGN L528"),
     ("BUILDING 2 LEVEL 1 — SUPPORTING CONSTRUCTION","RCO 302.3.1","EQUAL OR GREATER RATING","F1 ON W3 / W1R — UL U305"),
     ("BUILDING 1 — UNIT 1","RCO 302.2 / 302.3","NONE — A DETACHED ONE-FAMILY DWELLING","W1, W2, F2"),
     ("SIDE WALLS, BOTH BUILDINGS","RCO TABLE 302.1(1)","0 HOURS AT %s TO THE LOT LINE; OPENINGS UNLIMITED"%fmt(SIDE_YARD),"W1; W1R AT BLDG 2 LEVEL 1"),
     ("EAVES, SIDE WALLS","RCO TABLE 302.1(1) NOTE a","0 HOURS AT %s — FIREBLOCKED, PLATE TO DECK"%fmt(SIDE_YARD-ROOF_OVERHANG),"%s MAXIMUM OVERHANG; %s"%(inches(ROOF_OVERHANG),FB['EAVES'])),
     ("BUILDING 1 REAR WALL AND RAKE","RCO 302.1 / TABLE 302.1(1)","0 HOURS AT %s AND %s TO THE IMAGINARY LINE"%(fmt(fsd.OFF_B1),fmt(fsd.OFF_B1-ROOF_OVERHANG)),
      "W1; OPENINGS %.0f%% OF A STORY, UNLIMITED"%(100*fsd.rear_open_ratio(st))),
     ("BUILDING 2 COURTYARD WALL AND RAKE","RCO 302.1 / TABLE 302.1(1)","0 HOURS AT %s AND %s TO THE IMAGINARY LINE"%(fmt(fsd.OFF_B2),fmt(fsd.OFF_B2-ROOF_OVERHANG)),"W1R / W1"),
     ("UNIT 3 STAIR AND LANDING UNDERSIDE","RCO 302.1 / TABLE 302.1(1)",
      "NONE AT %s AND OVER — %s MAXIMUM PROJECTION LEAVES %s"
      %(fmt(rco_fsd.PROJ_FREE),fmt(fsd.PROJ_MAX),fmt(fsd.OFF_B2-fsd.PROJ_MAX)),
      "UNRATED; %s DRAWN LEAVES %s"%(fmt(fsd.STAIR_W),fmt(fsd.stair_clear()))),
     ("OAK AVENUE AND ALLEY FACES","RCO 202","NONE — MEASURED TO THE CENTERLINE OF THE PUBLIC WAY","W1; W1R AT BLDG 2 LEVEL 1")]


def _stack_bay(x, y):
    """The bay stack F stands in, in plan section, and what protects it at the framing.

       A-601's W1 / W1R rows fill the cavity with a batt as deep as the cavity; P-601 note
       1aa stands a 3" drain in one of those cavities. Both were true and they did not fit:
       a 3" DWV pipe is 3-1/2" across, so 2" is left. This is the bay that reconciles them,
       and every figure on it is the same one arkitect/lib/model/fit.py checks."""
    from src import drainage as dr
    run = next(r for r in dr.cavity_runs() if r.name.endswith('F'))
    dims = {'cavity': inches(run.depth), 'added': inches(run.added),
            'fitting': '%s FITTING' % inches(run.fitting), 'fill': inches(run.fill)}
    return stack_in_cavity(
        x, y, STACK_BAY_W,
        (IN(7.0/16), IN(5.0/8), run.depth, run.added, IN(5.0/8)),
        (run.od, run.fitting,
         'THE WASHER CONNECTION: A SANITARY TEE, %s OVER A %s STACK (DASHED)'
         % (inches(run.fitting), inches(run.od))),
        (run.fill, '%s, R-%d MIN — %s ITEM %s, THE PARTIAL FILL'
         % (run.fill_name, envelope.STACK_BAY_R, u305.DESIGN, envelope.STACK_BAY_FILL_ITEM)),
        dims, 3.30*inch,
        "STACK F AT A WASHER CONNECTION — PLAN SECTION  ·  3\" = 1'-0\"",
        "CUT THROUGH THE FITTING, NOT THE PIPE: P-601 NOTES 1aa AND 2",
        extra_label="5/8\" TYPE X EXTERIOR LAYER — W1R, BUILDING 2 LEVEL 1; W1 ABOVE HAS NONE",
        added_label="%s STUDS AT THIS BAY, PLATE TO PLATE; THE BOARD FASTENS TO THEM"
                    % envelope.STACK_BAY_STUD,
        notes=wrap_notes([
            "%s. SET THE STACK SO ITS FITTINGS, NOT ITS PIPE, CLEAR THE FILL." % stack_bay_text(),
            "SUBMIT THE BATT'S INSTALLED R AND ITS %s LISTING WITH THE WALL ASSEMBLY ALREADY REQUIRED ABOVE, AND "
            "CARRY THIS BAY IN THE ENERGY COMPLIANCE DOCUMENTATION: ONE BAY AT R-%d IN A WALL SCHEDULED R-%d, A-602."
            % (u305.DESIGN, envelope.STACK_BAY_R, CAVITY_BATT_R),
            "BORE EACH PLATE THE STACK PASSES ON ITS CENTERLINE AND STRAP IT ACROSS THE HOLE, RCO 602.6.1. FIREBLOCK "
            "THE CAVITY AT EVERY FLOOR AND CEILING LINE, %s. WHERE THE WALL IS W1R, PROTECT THE PENETRATION PER "
            "RCO 302.4 AS THE NOTES ABOVE REQUIRE." % FB['LINES'],
            "PROTECT THE LINE WITH A STEEL PLATE AT EVERY PLATE AND STUD IT PASSES WITHIN 1-1/4\" OF A FACE, RCO "
            "P2603.2.1. NO WATER PIPING IN THIS OR ANY OTHER EXTERIOR WALL CAVITY, P-601 NOTE 2. THE BAY PROJECTS "
            "%s INTO THE ROOM; A-102 DIMENSIONS IT." % inches(run.added),
        ], STACK_BAY_W, 5.8, indent=""),
        plate_note="AT EVERY PLATE AND FLOOR LINE")


def sheet_a601():
    sh=Sheet(c,"A-601","Assemblies and fire separation","AS NOTED"); sh.frame()
    x=X0; y=Y1-0.4*inch
    c.setFont("Helvetica-Bold",14); c.drawString(x,y,"ASSEMBLY SCHEDULE"); y-=0.10*inch
    c.setLineWidth(0.9); c.line(x,y,x+15.4*inch,y); y-=0.28*inch
    c.setFont("Helvetica-Bold",8.4); xx=x
    for h,w in zip(["TYPE","ASSEMBLY","RATING","PERFORMANCE"],ASM_WIDTHS):
        c.drawString(xx,y,h); xx+=w*inch
    y-=0.17*inch; c.setFont("Helvetica",8.4)
    walls=wall_rows(); check_wall_rows(walls)
    asm=[("W1",walls["W1"],"NONE","R-20 WALL, CZ5 — EVERY EXTERIOR WALL NOT W1R"),
     ("W1R",walls["W1R"],"1 HOUR","UL U305 + UL BXUV OSB ADDITION; RCO 302.3.1"),
     ("W2","2x4 STUDS AT 16\" O.C. / 1/2\" GYPSUM BOARD BOTH FACES; 2x6 AT PLUMBING WALLS; CEMENT BOARD AT TUBS AND SHOWERS","NONE","INTERIOR PARTITION"),
     ("W3","2x4 STUDS AT 16\" O.C. / ONE 5/8\" UL TYPE SCX GYPSUM LAYER EACH FACE / R-13 BATT","1 HOUR","UL DESIGN U305 — LISTED; RCO 302.3.1"),
     ("F1","1/4\" FINISH / %s T&G SUBFLOOR / %s OPEN-WEB WOOD FLOOR TRUSSES @ %s, 2x4 CHORDS / RESILIENT CHANNELS @ %s / %d LAYER %s %s"
      %(_in(levels.SUBFLOOR),_in(F1_JOIST),_in(JOIST_OC),_in(levels.F1_CHANNEL_OC),levels.F1_LAYERS,_in(levels.F1_LAYER),levels.F1_BOARD),
      "1 HOUR","%s — AT RIGHT"%levels.F1_LISTING),
     ("F2","1/4\" FINISH / %s T&G SUBFLOOR / %s OPEN-WEB WOOD FLOOR TRUSSES AT %s O.C. / %s GYPSUM CEILING"%(_in(levels.SUBFLOOR),_in(F2_JOIST),_in(JOIST_OC),_in(levels.F2_GYPSUM)),"NONE","UNIT 1'S LEVEL 2 FLOOR; S-102"),
     ("R1","ARCH. SHINGLE, CLASS A / ICE BARRIER AT EAVES / 7/16\" OSB / TRUSSES AT %s O.C. / R-49 BLOWN / 5/8\" GYPSUM"%_in(TRUSS_OC),"NONE","R-49; EAVES FIREBLOCKED, %s"%FB['EAVES']),
     ("S1","%s CONCRETE SLAB / %d-MIL VAPOR RETARDER / %s CLEAN AGGREGATE / R-%d RIGID AT SLAB EDGE, %s RUN"%(_in(SLAB_T),RETARDER_MIL,_in(GRAVEL_T),int(INSUL_R_NOM),fmt(EDGE_INSUL_RUN)),"--","RCO TABLE 1102.1.2 — SEE S-101"),
     ("FTG","%s x %s CONTINUOUS CONCRETE FOOTING, BOTTOM %s MINIMUM BELOW FINISHED GRADE / %s POURED CONCRETE FOUNDATION WALL"%(inches(FTG_W),inches(FTG_T),inches(FROST_DEPTH),inches(WALL_T)),"--","CIC-09, RCO 403.1.4.1 — SEE S-101"),
     ("FS","INTERIOR BEARING STRIP, %s x %s, UNDER THE UNIT 1 STAIR WALL AND THE UNITS 2 AND 3 BEARING WALL"%(inches(STRIP_W),inches(STRIP_D)),"--","SEE S-101")]
    for r in asm:
        assert pdfmetrics.stringWidth(r[1],"Helvetica",8.4) <= (ASM_WIDTHS[1]-0.15)*inch, "A-601 %s row overruns its column" % r[0]
        assert pdfmetrics.stringWidth(r[3],"Helvetica",8.4) <= ASM_WIDTHS[3]*inch, "A-601 %s performance overruns" % r[0]
        xx=x
        for v,w in zip(r,ASM_WIDTHS): c.drawString(xx,y,v); xx+=w*inch
        y-=0.175*inch
    y-=0.30*inch
    c.setFont("Helvetica-Bold",14); c.drawString(x,y,"FIRE SEPARATION"); y-=0.10*inch
    c.setLineWidth(0.9); c.line(x,y,x+15.4*inch,y); y-=0.28*inch
    FS_W=[4.6,2.7,4.7,3.4]
    c.setFont("Helvetica-Bold",8.4); xx=x
    for h,w in zip(["LOCATION","CODE SECTION","REQUIRED","ASSEMBLY"],FS_W):
        c.drawString(xx,y,h); xx+=w*inch
    y-=0.17*inch; c.setFont("Helvetica",8.4)
    rows=fire_separation_rows()
    for r in rows:
        assert "SPRINKLER" not in r[2], \
            "A-601 states the rating this set is built to; it is not sprinklered, G-001 note 3"
        xx=x
        for v,w in zip(r,FS_W):
            assert pdfmetrics.stringWidth(v,"Helvetica",8.4) <= w*inch-3, "A-601 fire separation cell overruns: %r" % v
            c.drawString(xx,y,v); xx+=w*inch
        y-=0.175*inch
    y-=0.08*inch
    c.setFont("Helvetica",7.4)
    notes=["W1R IS EVERY LEVEL 1 EXTERIOR WALL OF BUILDING 2, AND W3 ITS INTERIOR BEARING WALL: THE CONSTRUCTION SUPPORTING F1. FOLLOW UL DESIGN U305 IN FULL FOR BOTH; SUBMIT BEFORE FRAMING.",
           "2x6 STUDS ARE PERMITTED AS LARGER-THAN-LISTED STUDS. ADD 7/16\" OSB OVER THE EXTERIOR TYPE X LAYER PER UL BXUV GUIDANCE; STAGGER OSB JOINTS FROM GYPSUM JOINTS AND",
           "INCREASE OUTERMOST-LAYER FASTENER LENGTH FOR THE REQUIRED FRAMING PENETRATION. WALL BRACING NAILING THROUGH THE GYPSUM LAYER PER THE BRACING DESIGN.",
           "PENETRATIONS OF W1R AND W3: PROTECT PER RCO 302.4 WITH A LISTED THROUGH-PENETRATION SYSTEM OR ANNULAR-SPACE FILL PER THE ASSEMBLY LISTING. NO DAMPER IN A DRYER DUCT.",
           vr_note(),
           "FLOOR DEPTHS: F1 = %s FINISHED FLOOR TO CEILING; F2 = %s. EACH INCLUDES %s TOTAL FLOOR-FINISH ALLOWANCE."
           %(_in(levels.FF2-levels.F1_CEILING),_in(levels.FF2-levels.F2_CEILING),_in(levels.FLOOR_FINISH)),
           "BUILD F1 AS %s IN FULL: SUBFLOOR, TRUSSES, CHANNELS, THE %s BOARD AND ITS FASTENING, AND NO INSULATION IN THE CAVITY, AT RIGHT. SUBMIT ANY OTHER F1 DESIGN BEFORE FABRICATION."%(levels.F1_LISTING,levels.F1_BOARD),
           "SLAB TOP +%s; LEVEL 1 PLATE +%s; SUBFLOOR TOP +%s; ROOF PLATE +%s; EAVE, TOP OF HEEL +%s. A-201 / A-202."
           %(fmt(levels.SLAB_TOP),fmt(levels.F1_PLATE),fmt(levels.SUBFLOOR_TOP),fmt(levels.ROOF_PLATE),fmt(levels.EAVE))]
    for t in notes:
        assert pdfmetrics.stringWidth(t,"Helvetica",7.4) <= 15.4*inch, "A-601 note overruns the schedule rule: %r" % t[:50]
        c.drawString(x,y,t); y-=0.145*inch
    y-=0.22*inch
    c.setFont("Helvetica-Bold",8.6)
    c.drawString(x,y,"DO NOT ALTER F1, THE WALLS UNDER IT OR THE UNIT STACKING WITHOUT REVISED CODE REVIEW, RCO 302.3."); y-=0.40*inch
    yd=_floor_line(x,y)
    assert yd > Y0+0.05*inch, "A-601 floor-line detail runs off the sheet by %.2f in" % ((Y0-yd)/inch)
    ys=_stack_bay(X0+11.3*inch,y)
    assert ys > Y0+0.05*inch, "A-601 stack-bay detail runs off the sheet by %.2f in" % ((Y0-ys)/inch)
    _fireblocking_block(X0+16.1*inch, _f1_block(X0+16.1*inch, Y1-0.4*inch, X1)-0.30*inch, X1)
    c.showPage()

"""A-604 — the two exterior stairs in section and detail.

Both stairs are the same stair (src/stairs.py), and both are prescriptive wood: RCO
311.7 gives the flight, and the 507 deck provisions give everything that holds it up —
the stringers, the ledger and its flashing, the posts, the footings and the guard post
attachment. There is no fabricator's design behind them any more, so the things a
fabricator used to work out have to be drawn, and this is where they are drawn.

Four details, in the order src/stairs.py lists them: the flight in section, the guard
post attachment, the ledger and flashing where the stair meets a W1R wall, and the pier
connection. Every figure is the model's — the riser, the tread, the width and the
landing framing from src/stairs.py, the piers from src/foundation.py, the fire
separation from src/fsd.py.
"""
from arkitect.lib.draw.page import GREY, Sheet
from arkitect.lib.draw.text import wrap_notes
import math
from arkitect.lib.units import IN, fmt, inches, inches16
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import fsd, stairs
from src.framing import GROUND_SNOW
from src.building1 import U3_STAIR
from src.foundation import FROST_DEPTH
from arkitect.lib.draw.detail import _Det, _title
from arkitect.lib.draw.kit import X0, X1, Y0, Y1, c
from arkitect.lib.draw.detail import _break

FLIGHT_SC = 1.5*72.0       # 1-1/2" = 1'-0", as A-603's sections
BIG = 3.0*72.0             # 3" = 1'-0", for the two connection details

RISER = U3_STAIR.riser     # 8-1/16": 121" over 15, the stoop 1" under a threshold
TREAD = U3_STAIR.tread     # 9-1/4"
WIDTH = U3_STAIR.width     # 3'-6" overall
CLEAR = 3.0                # 3'-0" minimum clear between guards, RCO 311.7.1
GUARD_H = 3.0              # 36" guard, RCO 312.1.2
RAIL_LO, RAIL_HI = IN(34), IN(38)
SPHERE = IN(4)             # RCO 312.1.3, the sphere a guard's openings may not pass

STRINGER = IN(11.25)       # a 2x12 stringer, actual
LEDGER = IN(9.25)          # a 2x10 ledger, actual
JOIST = IN(7.25)           # a 2x8 landing joist, actual
DECKING = IN(1.0)          # composite tread / decking, nominal
POST = IN(3.5)             # a 4x4 guard post, actual
PIER = IN(12)              # the pier, S-101 note 5


def _in(v):
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


# ---------------------------------------------------------------- detail 1
def _flight(cx, top, left, right):
    """Three treads of the flight in section, cut through a stringer. Local coordinates:
       x runs along the flight from a re-entrant corner of the cut, z is height above it,
       so the drawing says nothing about where in the flight it is taken.

       The stringer is a 2x12 on a slope, so its underside is a line PARALLEL to the
       pitch line and 11-1/4" below it on the perpendicular — not a flat soffit. Drawn
       flat it would be a member 5" deep at one end and over two feet at the other."""
    n = 3
    L = math.hypot(TREAD, RISER)
    # A 2x12 is 11-1/4" measured PERPENDICULAR to its length. On this pitch that is
    # VDEPTH measured vertically, which is what a section drawn in plan-true x and z has
    # to use: the ends of the member are cut vertically, as a section cuts them, and only
    # its underside runs parallel to the pitch line.
    VDEPTH = STRINGER*L/TREAD
    gz = 2*RISER + 1.15                         # the post, broken off short of its 3'-0"
    d = _Det(cx, top, FLIGHT_SC, 1.55, -VDEPTH-0.18, gz+0.28, left, right, size=5.4, gap=12.0, sheet='A-604')
    cut = []
    for i in range(n):
        cut += [(i*TREAD, i*RISER), (i*TREAD, (i+1)*RISER), ((i+1)*TREAD, (i+1)*RISER)]
    d.poly(cut + [(n*TREAD, n*RISER-VDEPTH), (0.0, -VDEPTH)], fill=white)
    d.lab(1.45*TREAD, 1.45*RISER-VDEPTH*0.55, 'L',
          ('PT 2x12 STRINGER, SAWN;', 'AT LEAST %s OF DEPTH LEFT' % _in(IN(5)), 'BELOW THE CUT, RCO 507.5.1'))
    # Treads and risers laid on the cut.
    for i in range(n):
        x0, z0 = i*TREAD, (i+1)*RISER
        d.rect(x0-IN(1), z0, x0+TREAD, z0+DECKING)
        d.rect(x0+TREAD, z0+DECKING, x0+TREAD+IN(1), z0+RISER)
    d.lab(0.5*TREAD, RISER+DECKING/2, 'L',
          ('%s, %s GOING,' % (stairs.TREADS, _in(TREAD)), '%s NOSING, RCO 311.7.5' % _in(IN(1))))
    d.lab(TREAD+IN(0.5), RISER+RISER/2, 'R',
          ('%s RISER, 15 EQUAL;' % inches16(RISER), 'RCO 311.7.5.1 PERMITS %s' % _in(IN(8.25))))
    # The guard post, broken: detail 2 is the connection, this only says it is here.
    gx = 1.62*TREAD
    d.rect(gx, 2*RISER-IN(9), gx+POST, gz, fill=white, lw=0.9)
    _break(d, gx, gx+POST, gz-0.18)
    d.lab(gx+POST/2, gz-0.55, 'R',
          ('%s PT GUARD POST AT %s' % (_in(POST), fmt(GUARD_H)), 'OVER THE NOSINGS, RCO 312.1.2;',
           'OPENINGS PASS NO %s SPHERE,' % _in(SPHERE), 'RCO 312.1.3. DETAIL 2.'))
    c.setStrokeColor(GREY); c.setLineWidth(0.6)
    c.circle(d.X(gx-0.32), d.Y(2*RISER+IN(9)), 0.05*FLIGHT_SC, fill=0, stroke=1)
    c.setStrokeColor(black)
    d.lab(gx-0.32, 2*RISER+IN(9), 'L',
          ('CONTINUOUS GRASPABLE HANDRAIL', '%s TO %s OVER THE NOSINGS,' % (_in(RAIL_LO), _in(RAIL_HI)),
           'RCO 311.7.8'))
    lo = d.flush('detail 1')
    _title(left, lo-0.30*inch, 1, stairs.DETAILS[0], '1-1/2" = 1\'-0"')
    return lo-0.62*inch


# ---------------------------------------------------------------- detail 2
def _guardpost(cx, top, left, right):
    """A guard post at the landing rim: the 507.9.2 connection, which is the one a
       fabricator used to draw and nobody else."""
    d = _Det(cx, top, BIG, 0.62, -0.75, 0.80, left, right, size=5.4, gap=12.0, sheet='A-604')
    d.rect(-0.62, -0.10, 0.62, 0.0)                              # decking
    d.rect(-0.62, -0.10-JOIST, 0.62, -0.10, fill=white)          # rim / outer joist
    d.hatch(-0.62, -0.10-JOIST, -0.30, -0.10)
    d.rect(-POST/2, 0.0, POST/2, 0.80, fill=white, lw=0.9)       # the post itself
    d.line(-POST/2, -0.10-JOIST, -POST/2, 0.0, lw=0.9)
    d.line(POST/2, -0.10-JOIST, POST/2, 0.0, lw=0.9)
    for z in (-0.10-IN(1.5), -0.10-JOIST+IN(1.5)):               # two bolts through
        d.line(-0.55, z, 0.55, z, lw=0.8)
        c.setFillColor(black)
        for x in (-0.50, 0.50): c.circle(d.X(x), d.Y(z), 1.5, fill=1, stroke=0)
    _break(d, -POST/2, POST/2, 0.66)
    d.lab(0.0, 0.42, 'R', ('%s PT POST, GUARD BEYOND;' % _in(POST), '%s ABOVE THE DECK, DETAIL 1' % fmt(GUARD_H)))
    d.lab(0.40, -0.10-IN(1.5), 'R',
          ('TWO %s THROUGH-BOLTS WITH' % _in(IN(0.5)), 'WASHERS EACH FACE, VERTICALLY',
           'SEPARATED, RCO 507.9.2'))
    d.lab(-0.45, -0.10-JOIST/2, 'L', ('PT RIM / OUTER LANDING JOIST', '— HOLD-DOWN TENSION DEVICE AT',
                                      'EACH POST WHERE 507.9.2 REQUIRES'))
    d.lab(0.0, -0.05, 'L', ('%s OVER PT FRAMING' % stairs.TREADS,))
    lo = d.flush('detail 2')
    _title(left, lo-0.30*inch, 2, stairs.DETAILS[1], '3" = 1\'-0"')
    return lo-0.62*inch


# ---------------------------------------------------------------- detail 3
def _ledger(cx, top, left, right):
    """The landing ledger where it meets a W1R wall. Two things happen here that do not
       happen at an unrated wall: the flashing runs over a rated sheathing layer, and
       every bolt is a penetration of a 1-hour assembly."""
    d = _Det(cx, top, BIG, 0.72, -0.85, 0.75, left, right, size=5.4, gap=12.0, sheet='A-604')
    # The wall, outside face at x 0: gypsum sheathing, OSB, then the ledger on it.
    d.rect(-0.72, -0.85, -IN(1.125), 0.75, fill=white)           # studs beyond
    d.hatch(-0.72, -0.85, -IN(1.125), 0.75, step=4.0)
    d.rect(-IN(1.125), -0.85, -IN(0.4375), 0.75)                 # 5/8" Type X sheathing
    d.rect(-IN(0.4375), -0.85, 0.0, 0.75)                        # 7/16" OSB
    d.rect(0.0, -0.10-LEDGER, IN(1.5), -0.10, fill=white, lw=0.9)   # the ledger
    d.rect(0.0, -0.10, 0.72, 0.0)                                # decking over it
    d.line(0.0, 0.0, 0.0, 0.32, lw=1.1)                          # flashing up the wall
    d.line(0.0, 0.32, -IN(1.125), 0.32, lw=1.1)
    d.line(0.0, 0.0, IN(2.2), -IN(0.6), lw=1.1)                  # and out over the deck
    for z in (-0.10-IN(2), -0.10-LEDGER+IN(2)):
        c.setFillColor(black)
        c.circle(d.X(IN(0.75)), d.Y(z), 1.6, fill=1, stroke=0)
        d.line(-0.72, z, IN(1.5), z, lw=0.8)
    d.lab(IN(0.75), -0.10-IN(2), 'R',
          ('%s THROUGH-BOLTS OR LAG SCREWS' % _in(IN(0.5)), 'TO THE WALL FRAMING AT 507.9.1.3',
           'SPACING — NOT TO SHEATHING ALONE'))
    d.lab(0.0, 0.20, 'R', ('CORROSION-RESISTANT FLASHING', 'BEHIND THE WRB AND OVER THE',
                           'LEDGER, RCO 507.2.4'))
    d.lab(-IN(0.78), -0.55, 'L', ('W1R: %s TYPE X EXTERIOR' % _in(IN(0.625)), 'GYPSUM SHEATHING UNDER THE',
                                  'OSB — 1 HOUR, A-601'))
    d.lab(IN(0.75), -0.10-LEDGER+IN(2), 'L',
          ('PROTECT EVERY BOLT PENETRATION', 'OF W1R PER RCO 302.4,', 'A-001 NOTE 2a'))
    d.lab(IN(0.5), -0.05, 'R', ('PT LEDGER, %s' % _in(LEDGER),))
    lo = d.flush('detail 3')
    _title(left, lo-0.30*inch, 3, stairs.DETAILS[2], '3" = 1\'-0"')
    return lo-0.62*inch


# ---------------------------------------------------------------- detail 4
def _pier(cx, top, left, right):
    """The foot of a stringer on its pier. The footings are not in the model — A-001
       13a and S-101 note 5 — so this draws the connection and sends the size there."""
    d = _Det(cx, top, BIG, 0.72, -1.15, 0.78, left, right, size=5.4, gap=12.0, sheet='A-604')
    d.rect(-PIER/2, -1.15, PIER/2, -0.10, fill=white, lw=0.9)    # the pier
    d.hatch(-PIER/2, -1.15, PIER/2, -0.10, step=4.5)
    d.line(-0.72, -0.10, 0.72, -0.10, lw=0.7, dash=(3, 2))       # finished grade
    d.rect(-IN(0.75), -0.10, IN(0.75), 0.0, fill=white)          # the post base
    d.rect(-IN(0.75), 0.0, IN(0.75), 0.78, fill=white, lw=0.9)   # stringer / post above
    _break(d, -IN(0.75), IN(0.75), 0.64)
    c.setFillColor(black)
    c.circle(d.X(0.0), d.Y(-0.05), 1.6, fill=1, stroke=0)
    d.lab(0.0, -0.05, 'R', ('GALVANIZED POST BASE, ANCHORED', 'TO THE PIER AND RAISING THE WOOD',
                            '%s CLEAR OF THE CONCRETE,' % _in(IN(1)), 'RCO 507.8.2 / 317.1.4'))
    d.lab(0.0, 0.35, 'L', ('%s BEARING ON ITS PIER' % stairs.STRINGERS,))
    d.lab(0.0, -0.75, 'L', ('PIER AND FOOTING PER S-101 NOTE 5;', 'FOOTING BOTTOM %s MIN' % inches(FROST_DEPTH),
                            'BELOW FINISHED GRADE'))
    d.lab(-0.30, -0.10, 'R', ('FINISHED GRADE — C-103',))
    lo = d.flush('detail 4')
    _title(left, lo-0.30*inch, 4, stairs.DETAILS[3], '3" = 1\'-0"')
    return lo-0.62*inch


NOTES = [
    "1.  BOTH EXTERIOR STAIRS ARE THE SAME STAIR: %s, FRAMED %s TO %s. PLACEMENT, RUN AND LANDINGS: A-001 NOTES "
    "13a AND 13b. CONSTRUCTION DETAILS THIS SHEET." % (stairs.MATERIAL, stairs.DESIGN, stairs.CODE),
    "2.  15 EQUAL RISERS AT %s AND 14 TREADS AT %s, HORIZONTAL RUN %s, FROM A %s CONCRETE STOOP TO THE LEVEL 2 FLOOR. "
    "EVERY RISER EQUAL AT BOTH STRINGERS, RCO 311.7.7; THE GREATEST AND LEAST SHALL NOT DIFFER BY MORE THAN %s, "
    "RCO 311.7.5.1." % (inches16(RISER), _in(TREAD), fmt(U3_STAIR.run), _in(IN(6)), _in(IN(0.375))),
    "3.  %s OVERALL WITH %s MINIMUM CLEAR BETWEEN THE GUARDS, RCO 311.7.1. PITCH EVERY TREAD AND LANDING %.0f%% AWAY "
    "FROM THE WALL, AS THE STOOP DOES." % (fmt(WIDTH), fmt(CLEAR), 100*U3_STAIR.pitch),
    "4.  ALL FRAMING IN CONTACT WITH CONCRETE, EXPOSED TO WEATHER OR SUPPORTING A WALKING SURFACE OUTDOORS SHALL BE "
    "PRESERVATIVE-TREATED, RCO 317.1. ALL FASTENERS AND CONNECTORS IN PRESERVATIVE-TREATED WOOD SHALL BE HOT-DIPPED "
    "GALVANIZED OR STAINLESS, RCO 317.3.",
    "5.  COMPOSITE TREADS AND DECKING SHALL BE INSTALLED TO THE MANUFACTURER'S SPAN AND FASTENING INSTRUCTIONS. "
    "SUBMIT THE PRODUCT DATA WITH THE SHOP DRAWING.",
    "6.  LIGHT THE TOP AND THE BOTTOM OF EACH FLIGHT, RCO 303.7 AND 311.7.9, SWITCHED FROM INSIDE THE UNIT THE STAIR "
    "SERVES. E-101 AND E-102.",
    "7.  CANOPY OVER EACH DOOR AND THE WHOLE TOP LANDING, BOTH STAIRS: PT 2x6 RAFTERS AT 16\" O.C. ON A PT "
    "LEDGER FLASHED AS DETAIL 3, PITCHED AWAY FROM THE WALL, AT THE %g PSF GROUND SNOW OF G-001. SHEATHING, "
    "UNDERLAYMENT, SHINGLE AND HEADWALL FLASHING PER S-103 NOTES 4 TO 4d; FRAMING, BRACING AND BEARING PER THE "
    "NOTE 9 SHOP DRAWING. NO PART OF THE UNIT 5 STAIR, CANOPY OR GUARD SHALL PROJECT MORE THAN %s FROM BUILDING "
    "2'S COURTYARD FACE; MAINTAIN %s TO THE RCO 302.1 IMAGINARY LINE, RCO TABLE 302.1(1) AND C-101 NOTE 5e."
    % (GROUND_SNOW, fmt(fsd.PROJ_MAX), fmt(fsd.U5_CLEAR)),
    "8.  NEITHER STAIR HAS A RATED UNDERSIDE AND NEITHER CARRIES A LISTED ASSEMBLY. A-601 SCHEDULES BOTH.",
    "9.  SUBMIT A %s BEFORE FABRICATION: STRINGER LAYOUT AND THE THREE CONNECTIONS ON THIS SHEET. FOOTINGS AND PIERS "
    "ARE S-101 NOTE 5." % stairs.SUBMITTAL,
]


def sheet_a604():
    # Comma rather than "and": 35 characters does not fit the title block's 2.96 in
    # column, and this is the form S-103 already uses ("Roof framing, structural
    # details"). G-001's index keeps the long name; the block has always carried the
    # short one.
    sh = Sheet(c, "A-604", "Exterior stair sections, details", "AS NOTED"); sh.frame()
    # Two columns of two details. The label columns are what set the widths: each _Det
    # writes outboard of its section on both sides, and flush() asserts it stays inside.
    LW = (X1-X0)/2.0 - 0.45*inch
    LC, RC = X0+LW*0.52, X0+LW+0.9*inch+LW*0.52
    top = Y1-0.75*inch
    y1 = _flight(LC, top, X0, X0+LW)
    y2 = _guardpost(RC, top, X0+LW+0.9*inch, X1)
    y3 = _ledger(LC, min(y1, y2)-0.15*inch, X0, X0+LW)
    y4 = _pier(RC, min(y1, y2)-0.15*inch, X0+LW+0.9*inch, X1)

    y = min(y3, y4)-0.30*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 11)
    c.drawString(X0, y, "EXTERIOR STAIR NOTES"); y -= 0.10*inch
    c.setLineWidth(0.9); c.line(X0, y, X1, y); y -= 0.22*inch
    c.setFont("Helvetica", 7.6)
    for t in wrap_notes(NOTES, X1-X0, 7.6):
        c.drawString(X0, y, t); y -= 0.142*inch
        assert pdfmetrics.stringWidth(t, "Helvetica", 7.6) <= (X1-X0)+0.5, "A-604 note line overruns: " + t
    assert y > Y0, "A-604's notes run off the bottom of the sheet"
    c.showPage()

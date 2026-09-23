"""C-102 — 400 Oak's zoning site plan, its own 11 x 17 document.

Drawn from src/sitework.py's site and zoning_rows(), turned so true north is up the sheet
as a zoning site plan is read: the alley on the left, Oak Avenue on the right, 396 Oak
above and 404 Oak below. It carries no construction information.

300 S Elm's C-102, which this replaces, was a corner lot with vision triangles, a side
street yard and five variance requests. This lot is interior and requests nothing, so
none of that is here; its original stays in projects/example_300.
"""
from arkitect.lib import assets
from arkitect.lib.draw import page
from arkitect.lib.draw.page import Sheet
from arkitect.lib.draw.text import table
from arkitect.lib.units import fmt
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from arkitect.lib.draw.kit import draw_runs
from arkitect.lib.draw.kit import c
from src.sheets.site import TURN, draw_site, frame
from src.sitework import ALLEY_W, COURT, PARCEL, PARK_D, PARK_N, PARK_PITCH, STAIR, zoning_rows

# How far the street, the alley and the parcels beside the lot are drawn before they are
# broken off. Nothing past the lot is measured except the alley, whose width C.C. 3312.25
# counts.
CONTEXT = 10.0

SC = 4.5                                     # 1/16" = 1'-0"

NOTES = [
    "1.  LOT DIMENSIONS ARE FROM THE FRANKLIN COUNTY AUDITOR'S GIS.",
    "     NO SURVEY HAS BEEN MADE; A BOUNDARY SURVEY WILL REPLACE THEM.",
    "2.  THE LOT IS SPLIT FROM PARCEL %s; ITS OWN PARCEL" % PARCEL,
    "     NUMBER IS NOT YET ASSIGNED. TRUE NORTH IS APPROXIMATE.",
    "3.  EVERY DWELLING UNIT HAS A WALK TO OAK AVENUE: UNIT 1 AT ITS",
    "     ENTRY, UNITS 2 AND 3 DOWN THE SOUTH SIDE YARD. A WALK ALONG",
    "     BUILDING 2 JOINS THE PARKING TO THEIR ENTRANCES.",
    "4.  THE UNIT 3 STAIR PROJECTS %s INTO THE %s COURTYARD"
    % (fmt(STAIR[3]-STAIR[1]), fmt(COURT)),
    "     BETWEEN THE BUILDINGS, WHICH IS NOT A REQUIRED YARD.",
    "5.  %d PARKING SPACES @ %s x %s, BACKING TO THE %s PUBLIC ALLEY."
    % (PARK_N, fmt(PARK_PITCH), fmt(PARK_D), fmt(ALLEY_W)),
    "6.  NO ZONING RELIEF IS REQUESTED.",
]
NOTES_W = 3.55*inch


def sheet_c102():
    PG = page.ANSI_B
    sh = Sheet(c, "C-102", "Zoning site plan", "1/16\" = 1'-0\"", page=PG); sh.frame()
    ZX0, ZY0, ZX1, ZY1 = PG.DA
    sc = SC

    # ---- the frame: site feet -> the turned plan -> page points ----
    BAND_TOP = ZY0+2.95*inch                 # the tabulation band under the plan
    p, CX, CY, _ext = frame(sc, CONTEXT, ZX0, BAND_TOP, ZX1, ZY1, "C-102")
    c.saveState(); c.translate(CX, CY); c.rotate(TURN)
    draw_site(p, sc, CONTEXT)
    c.restoreState()

    # True north up the sheet, the compass art's own orientation, top right.
    _cs = 0.60*inch
    c.drawImage(assets.image("compass.png"), ZX1-_cs, ZY1-_cs, width=_cs, height=_cs,
                mask="auto", preserveAspectRatio=True)
    assert max(q[0] for q in _ext) <= ZX1-_cs or min(q[1] for q in _ext) >= ZY1-_cs \
        or max(q[1] for q in _ext) <= ZY1-_cs, "C-102 compass stands on the plan"

    # ---- the zoning tabulation in two columns, then the notes and the title ----
    TW, GAP = 3.3*inch, 0.30*inch
    t1x = ZX0; t2x = t1x+TW+GAP; nx = t2x+TW+GAP
    assert nx+NOTES_W <= ZX1, "C-102 notes run %.2f in past the drawing area" % ((nx+NOTES_W-ZX1)/inch)
    rows = zoning_rows()
    half = (len(rows)+1)//2
    while half < len(rows) and rows[half][0].startswith(" "): half += 1
    TOP = BAND_TOP-0.12*inch
    c.setFillColor(black)
    _kw = dict(size=6.4, lead=0.138*inch, title_size=8.0, gap=0.20*inch)
    y1 = table(c, t1x, TOP, "ZONING COMPLIANCE — COLUMBUS R-4, H-35", rows[:half], TW, **_kw)
    y2 = table(c, t2x, TOP, "ZONING COMPLIANCE — CONTINUED", rows[half:], TW, **_kw)
    for _y, _n in ((y1, "first"), (y2, "second")):
        assert _y >= ZY0, "C-102 zoning table's %s column overruns the sheet by %.2f in" % (_n, (ZY0-_y)/inch)
    ny = table(c, nx, TOP, "NOTES", (), NOTES_W, size=6.0, lead=0.112*inch, title_size=8.0, gap=0.20*inch)
    ny = draw_runs(nx, ny, [[(t, False)] for t in NOTES], 6.0, 0.112*inch, NOTES_W, "C-102 notes")
    TTY = ZY0+0.10*inch
    assert ny >= TTY+0.55*inch, "C-102 notes run %.2f in into the drawing title" % ((TTY+0.55*inch-ny)/inch)

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9.5); c.drawString(nx, TTY+0.26*inch, "ZONING SITE PLAN")
    c.setFont("Helvetica", 6.0); c.drawString(nx, TTY+0.13*inch, "SCALE: 1/16\" = 1'-0\"")
    _gx, _gy, _gh = nx+1.55*inch, TTY+0.28*inch, 3.0
    c.setLineWidth(0.5); c.setStrokeColor(black)
    for (a, b, fill) in ((0, 8, 1), (8, 16, 0), (16, 32, 1)):
        c.setFillColor(black if fill else white)
        c.rect(_gx+a*sc, _gy, (b-a)*sc, _gh, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Helvetica", 4.6)
    for v in (0, 8, 16, 32):
        c.drawCentredString(_gx+v*sc, _gy+_gh+1.8, "%d'" % v)
    assert _gx+32*sc <= ZX1, "C-102 graphic scale runs past the drawing area"
    c.showPage()

"""C-101 — the site plan: the lot, both buildings, their landings, the Unit 3 stair, the
walks and the parking pad, drawn by sheets/site.py as C-102 draws them, with what C-102
leaves out — the pads and piers, the RCO 302.1 imaginary line, the floor datum and the
construction notes — and the zoning tabulation. Turned so true north is up the sheet."""
from arkitect.lib import assets
from arkitect.lib.draw.page import GREY, Sheet
from arkitect.lib.draw.text import table
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src import drainage, fsd, levels, plumbing, services, stairs
from src.foundation import B1, B2, FLATWORK
from arkitect.lib.draw.kit import draw_runs
from arkitect.lib.draw.kit import X0, X1, Y0, Y1, c
from src.sheets.site import TURN, draw_site, frame
from src.sitework import (ALLEY_W, B1_X, B1_Y, B2_X, B2_Y, FSD_LINE_Y, PARK_D, PARK_N,
                          PARK_PITCH, PARK_T, SITE_BLDG, SITE_W, WALK_T, WALK_W, WALKS, zoning_rows)

SC = 7.2                    # 1" = 10'-0"
CONTEXT = 8.0
K = 1.45                    # the lettering, against C-102's 1/16"

_ff = inches(levels.FF1-levels.GRADE)
NOTES = [
    "1.  LOT DIMENSIONS ARE FROM THE FRANKLIN COUNTY AUDITOR'S GIS AND TRUE NORTH IS",
    "     APPROXIMATE. LAY OUT BOTH BUILDINGS FROM A BOUNDARY SURVEY; REPORT ANY",
    "     DIFFERENCE FROM THIS SHEET BEFORE FORMING.",
    "2.  FINISHED FLOOR %s ABOVE FINISHED GRADE AT THE WALL, BOTH BUILDINGS. GRADING, THE"
    % _ff,
    "     SWALES AND THE ROOF LEADERS PER C-103.",
    "3.  WALKS %s WIDE x %s, PARKING PAD %s, BOTH ON COMPACTED GRANULAR BASE: %s PSI"
    % (fmt(WALK_W), inches(WALK_T), inches(PARK_T), format(FLATWORK.psi, ',')),
    "     AIR-ENTRAINED CONCRETE, S-101 CONCRETE SCHEDULE. SLOPES PER C-103.",
    "4.  LANDINGS AND THE UNIT 3 STOOP: FLOATING PADS PER S-101 NOTE 5.",
    "5.  UNIT 3 STAIR: %s, FRAMED %s TO %s," % (stairs.MATERIAL, stairs.DESIGN, stairs.CODE),
    "     ON PIERS P1 TO P4, S-101. %s BEFORE FABRICATION." % stairs.SUBMITTAL,
    "6.  THE RCO 302.1 IMAGINARY LINE STANDS %s OFF BUILDING 1 AND %s OFF BUILDING 2."
    % (fmt(fsd.OFF_B1), fmt(fsd.OFF_B2)),
    "7.  %d PARKING SPACES @ %s x %s, BACKING TO THE %s PUBLIC ALLEY."
    % (PARK_N, fmt(PARK_PITCH), fmt(PARK_D), fmt(ALLEY_W)),
    "8.  ONE %s\" WATER SERVICE DOWN THE NORTH SIDE YARD, P-102, AND ONE 4\" BUILDING SEWER DOWN THE"
    % plumbing.service()['service'],
    "     SOUTH, P-101, BOTH TO OAK AVENUE. CO: EXTERIOR CLEANOUT. TAPS, THE METER PIT AND THE",
    "     MAINS' LOCATIONS PER COLUMBUS DPU. ELECTRIC SERVICE PER AEP OHIO. CALL OHIO811.",
    "9.  ZONING IS TABULATED HERE AND ON C-102. NO ZONING RELIEF IS REQUESTED.",
    "10. SERVICE EQUIPMENT ON THE BUILDINGS' SIDE WALLS: METERS EM-1 AND EM-2, HEAT PUMPS HP-1",
    "     TO HP-3 ON WALL BRACKETS, TELECOM TC-1 AND TC-2. HEIGHTS ON A-201 AND A-202.",
]


def _construction(p):
    """What C-101 adds inside the turned frame: the landing pads and the stoop, dashed
       (note 4 says what they are), the stair piers, the walks' widths and the imaginary
       line."""
    k = K
    c.setStrokeColor(black); c.setLineWidth(0.5); c.setDash(2, 1.5)
    for (bx, by, b) in ((B1_X, B1_Y, B1), (B2_X, B2_Y, B2)):
        for x0, y0, x1, y1, nm in b.pads:
            c.rect(p.X(bx+x0), p.Y(by+y1), (x1-x0)*SC, (y1-y0)*SC, fill=0, stroke=1)
    c.setDash()
    for x, y, dia, mark in B2.piers:
        c.setFillColor(white); c.circle(p.X(B2_X+x), p.Y(B2_Y+y), dia/2.0*SC, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold", 2.6*k)
        c.drawCentredString(p.X(B2_X+x), p.Y(B2_Y+y)-0.9*k, mark)
    for (x0, y0, x1, y1) in WALKS:                       # each walk's width, along it
        long_y = (y1-y0) > (x1-x0)
        t = "%s WALK" % fmt(WALK_W)
        c.saveState(); c.translate(p.X((x0+x1)/2.0), p.Y(y0+0.35*(y1-y0) if long_y else (y0+y1)/2.0))
        if long_y: c.rotate(90)
        c.setFillColor(white); w = c.stringWidth(t, "Helvetica", 3.2*k)
        c.rect(-w/2-1, -1.2*k, w+2, 3.6*k, fill=1, stroke=0)
        c.setFillColor(black); c.setFont("Helvetica", 3.2*k); c.drawCentredString(0, -0.3*k, t)
        c.restoreState()
    # service equipment on Building 1's north wall, out from the wall by its depth
    c.setStrokeColor(black); c.setLineWidth(0.5)
    for b in services.EQUIPMENT:
        bx, by, bw = next((q[0], q[1], q[2]) for q in SITE_BLDG if q[4] == "BUILDING %d" % b.building)
        x0 = bx-b.depth if b.wall == "NORTH" else bx+bw
        c.setFillColor(white)
        c.rect(p.X(x0), p.Y(by+b.along1), b.depth*SC, (b.along1-b.along0)*SC, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold", 2.6*k)
        c.saveState(); c.translate(p.X(x0)-1.5 if b.wall == "NORTH" else p.X(x0+b.depth)+1.5+2.6*k*0.72, p.Y(by+(b.along0+b.along1)/2.0)); c.rotate(90)
        c.drawCentredString(0, 0, b.mark); c.restoreState()
    _utilities(p)
    c.setStrokeColor(GREY); c.setLineWidth(0.6); c.setDash([8, 2, 2, 2])
    c.line(p.X(0), p.Y(FSD_LINE_Y), p.X(SITE_W), p.Y(FSD_LINE_Y))
    c.setDash(); c.setFillColor(GREY); c.setFont("Helvetica", 3.0*k)
    c.drawString(p.X(0.4), p.Y(FSD_LINE_Y)+1.5, "RCO 302.1 IMAGINARY LINE")
    c.setFillColor(black); c.setStrokeColor(black)


def _along_label(p, x, y, t, k):
    """A label reading along the lot's length, on white, centred on site point (x, y)."""
    c.saveState(); c.translate(p.X(x), p.Y(y)); c.rotate(90)
    w = c.stringWidth(t, "Helvetica", 3.0*k)
    c.setFillColor(white); c.rect(-w/2-1, -1.1*k, w+2, 3.4*k, fill=1, stroke=0)
    c.setFillColor(black); c.setFont("Helvetica", 3.0*k); c.drawCentredString(0, -0.2*k, t)
    c.restoreState()


def _utilities(p):
    """The building sewer and its cleanouts from src/drainage.py, the water service, its
       supplies and the meter pit from src/plumbing.py: the routes P-101 to P-103 size."""
    k = K
    s = drainage.sewer()
    c.setStrokeColor(black); c.setLineWidth(0.9); c.setDash(6, 2)
    for path in (s['route']+[(drainage.SEWER_X, -CONTEXT)], s['lateral']):
        for a, b in zip(path, path[1:]): c.line(p.X(a[0]), p.Y(a[1]), p.X(b[0]), p.Y(b[1]))
    c.setDash(); c.setLineWidth(0.5)
    for x, y in drainage.cleanouts():
        c.setFillColor(white); c.circle(p.X(x), p.Y(y), 0.55*SC, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold", 1.9*k); c.drawCentredString(p.X(x), p.Y(y)-0.65*k, "CO")
    _along_label(p, drainage.SEWER_X, (B1_Y+B1.D+B2_Y)/2.0, '4" SAN., 1/%d" PER FT, P-101' % round(1/drainage.SEWER_SLOPE), k)
    w = plumbing.site_water()
    c.setStrokeColor(black); c.setLineWidth(0.7); c.setDash([7, 2, 1.5, 2])
    for path in [[(w['service'][0][0], -CONTEXT)]+w['service']]+w['supplies']:
        for a, b in zip(path, path[1:]): c.line(p.X(a[0]), p.Y(a[1]), p.X(b[0]), p.Y(b[1]))
    c.setDash(); c.setLineWidth(0.5); c.setFillColor(white)
    px, py = w['pit']
    c.rect(p.X(px-0.75), p.Y(py+0.75), 1.5*SC, 1.5*SC, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Helvetica-Bold", 1.9*k); c.drawCentredString(p.X(px), p.Y(py)-0.65*k, "WM")
    _along_label(p, px, (B1_Y+B1.D+B2_Y)/2.0, '%s" WATER, P-102' % plumbing.service()['service'], k)


def sheet_c101():
    sh = Sheet(c, "C-101", "Site plan", "1\" = 10'-0\""); sh.frame()
    BAND_TOP = Y0+4.1*inch
    p, CX, CY, ext = frame(SC, CONTEXT, X0, BAND_TOP, X1, Y1, "C-101")
    c.saveState(); c.translate(CX, CY); c.rotate(TURN)
    draw_site(p, SC, CONTEXT, k=K,
              labels=lambda nm: ["FIN. FLOOR %s ABOVE FIN. GRADE" % _ff],
              extra=_construction)
    c.restoreState()

    _cs = 0.80*inch
    c.drawImage(assets.image("compass.png"), X1-_cs, Y1-_cs, width=_cs, height=_cs,
                mask="auto", preserveAspectRatio=True)
    assert max(q[0] for q in ext) <= X1-_cs or max(q[1] for q in ext) <= Y1-_cs, \
        "C-101 compass stands on the plan"

    # ---- under the plan: the zoning tabulation in two columns, the notes, the title ----
    TW, GAP = 4.3*inch, 0.35*inch
    t1x = X0; t2x = t1x+TW+GAP; nx = t2x+TW+GAP
    NOTES_W = X1-nx
    rows = zoning_rows()
    half = (len(rows)+1)//2
    while half < len(rows) and rows[half][0].startswith(" "): half += 1
    TOP = BAND_TOP-0.15*inch
    c.setFillColor(black)
    _kw = dict(size=7.6, lead=0.165*inch, title_size=9.5, gap=0.24*inch)
    y1 = table(c, t1x, TOP, "ZONING COMPLIANCE — COLUMBUS R-4, H-35", rows[:half], TW, **_kw)
    y2 = table(c, t2x, TOP, "ZONING COMPLIANCE — CONTINUED", rows[half:], TW, **_kw)
    for _y, _n in ((y1, "first"), (y2, "second")):
        assert _y >= Y0, "C-101 zoning table's %s column overruns the sheet by %.2f in" % (_n, (Y0-_y)/inch)
    ny = table(c, nx, TOP, "SITE NOTES", (), NOTES_W, size=7.2, lead=0.14*inch, title_size=9.5, gap=0.24*inch)
    ny = draw_runs(nx, ny, [[(t, False)] for t in NOTES], 7.2, 0.14*inch, NOTES_W, "C-101 notes")
    TTY = Y0+0.05*inch
    assert ny >= TTY+0.60*inch, "C-101 notes run %.2f in into the drawing title" % ((TTY+0.60*inch-ny)/inch)

    tx = t2x
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12); c.drawString(tx, TTY+0.28*inch, "SITE PLAN")
    c.setFont("Helvetica", 8); c.drawString(tx, TTY+0.12*inch, "SCALE: 1\" = 10'-0\"")
    _gx, _gy, _gh = tx+1.6*inch, TTY+0.30*inch, 4.0
    c.setLineWidth(0.5); c.setStrokeColor(black)
    for (a, b, fill) in ((0, 5, 1), (5, 10, 0), (10, 20, 1)):
        c.setFillColor(black if fill else white)
        c.rect(_gx+a*SC, _gy, (b-a)*SC, _gh, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Helvetica", 6.0)
    for v in (0, 5, 10, 20):
        c.drawCentredString(_gx+v*SC, _gy+_gh+2.2, "%d'" % v)
    assert min(y1, y2) >= TTY+0.60*inch or tx > t1x, "C-101 title runs into the zoning table"
    c.showPage()

"""C-103 — the grading and drainage plan.

   Drawn at 1/8" = 1'-0" with Oak Avenue at the top, as the floor plans are, from
   src/grading.py: every band, section, flowline and grade on this sheet is the model's,
   and check_grading() has held each to RCO 401.3 before a line is drawn. Nothing here
   computes a grade; it places the ones the model has."""
from arkitect.lib.draw.context import LAY
from arkitect.lib.draw.page import GREY, PlanDraw, Sheet
from arkitect.lib.units import IN, fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import levels
from src import grading as G
from arkitect.lib.model import grade as grade
from src.foundation import FLATWORK
from arkitect.codes.ohio.rco.concrete import psi
from src.sitework import NORTH_NEIGHBOUR, SITE_D, SITE_W, SOUTH_NEIGHBOUR
from arkitect.lib.draw.kit import DH, E, X0, X1, Y0, Y1, c
from arkitect.lib.draw.civil_kit import _Swatch, _arrow, _pct
from arkitect.lib.draw.civil_kit import _band_arrows
from arkitect.lib.draw.civil_kit import _spot as _shared_spot
from arkitect.lib.draw.civil_kit import _walk_slope
from functools import partial
from arkitect.codes.ohio.rco import site_steps

MIN_ARROW = 1.5          # a surface shorter than this, in feet, takes no arrow of its own

# What each flowline is, in words. The figures beside it are the model's.
GUTTER_RUNS = {"S-1": "BUILDING 2, NORTH SIDE YARD",
               "S-2": "BETWEEN THE BUILDINGS",
               "S-3": "BUILDING 1, NORTH SIDE, TO OAK",
               "W-1": "WALK EDGE, SOUTH OF BUILDING 1",
               "W-1 FRONT": "WALK EDGE, FRONT YARD",
               "S-4": "BUILDING 2, SOUTH SIDE YARD"}
KIND_WORD = {"gutter": "CONCRETE", "walk": "WALK EDGE", "swale": "GRASS SWALE"}


_spot = partial(_shared_spot, g=G)






def sheet_c103():
    sh = Sheet(c, "C-103", "Grading and drainage plan", "1/8\" = 1'-0\""); sh.frame()
    sc = E; W, D = SITE_W, SITE_D
    ox = X0+1.9*inch; oy = Y0+(DH-D*sc)/2-0.2*inch
    p = PlanDraw(c, ox, oy, sc, W, D)
    LAY("A-WALL")
    c.setStrokeColor(black); c.setLineWidth(1.6); c.setFillColor(white)
    c.rect(p.X(0), p.Y(D), W*sc, D*sc, fill=1, stroke=1)
    # Buildings, with the floor above the datum.
    for (bx, by, bw, bd, nm, _sub, _kind) in [G.B1, G.B2]:
        c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.2)
        c.rect(p.X(bx), p.Y(by+bd), bw*sc, bd*sc, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(p.X(bx+bw/2), p.Y(by+bd/2)+3, nm)
        c.setFont("Helvetica", 7)
        c.drawCentredString(p.X(bx+bw/2), p.Y(by+bd/2)-7, "FINISHED FLOOR %s" % grade.signed(levels.FF1))
        # the four corners at the datum, labelled inside the footprint
        for cx, cy in ((bx, by), (bx+bw, by), (bx, by+bd), (bx+bw, by+bd)):
            right = cx < bx+bw/2
            _spot(p, cx, cy, G.G0, dx=3.0 if right else -3.0, dy=-6.5 if cy < by+bd/2 else 3.0,
                  anchor="l" if right else "r")
    # Paving: walks and the pad grey, landings and stoops black.
    # Landings and stoops last: the Units 4 / 5 walk runs under the Unit 5 stoop.
    for r in sorted(G.PAVED, key=lambda r: r.kind in ("landing", "stoop")):
        firm = r.kind in ("landing", "stoop")
        c.setStrokeColor(black if firm else GREY); c.setLineWidth(0.9 if firm else 0.7); c.setFillColor(white)
        c.rect(p.X(r.x0), p.Y(r.y1), (r.x1-r.x0)*sc, (r.y1-r.y0)*sc, fill=1, stroke=1)
    # The Unit 3 flight over the courtyard, dashed: nothing is paved under it.
    c.setStrokeColor(GREY); c.setLineWidth(0.5); c.setDash(2, 1.5); c.setFillColor(black)
    for nm, fx0, fy0, fx1, fy1 in G.FLIGHTS:
        c.rect(p.X(fx0), p.Y(fy1), (fx1-fx0)*sc, (fy1-fy0)*sc, fill=0, stroke=1)
        c.setFont("Helvetica", 4.0); c.drawCentredString(p.X((fx0+fx1)/2.0), p.Y(fy1)+2.0, "UNIT 3 STAIR OVER")
    c.setDash(); c.setStrokeColor(black)
    for r in G.PAVED:
        if r.kind in ("landing", "stoop"):
            top = G.LANDING_TOP if r.kind == "landing" else G.STOOP_TOP
            _spot(p, (r.x0+r.x1)/2.0, (r.y0+r.y1)/2.0+0.6, top, dx=0.0, dy=-6.0, anchor="c")
    # The grade held at the foot of each one's step, where its walk leaves it.
    for _n, _t, _no, _f, _st, (wx, wy, wg, side) in site_steps.step_summary(G.STEPS, G.BANDS, G.STOOP_STEP):
        ox_, oy_, kw = {"x0": (-0.9, 0.0, dict(dx=-3.0, anchor="r")), "x1": (0.9, 0.0, dict(dx=3.0, anchor="l")),
                        "y0": (0.8, -0.9, dict(dx=3.0, dy=-1.6, anchor="l")),      # beside its walk's arrow
                        "y1": (0.0, 0.9, dict(dx=0.0, dy=-6.5, anchor="c"))}[side]
        _spot(p, wx+ox_, wy+oy_, wg, **kw)
    # Flowlines: the swales and the walk's edge, flow arrows and the mark.
    LAY("A-ANNO-TEXT")
    for g in G.GUTTERS:
        x0, y0, x1, y1 = g.box()
        c.setStrokeColor(black); c.setLineWidth(0.5); c.setFillColor(white)
        if g.kind == "gutter":
            c.rect(p.X(x0), p.Y(y1), (x1-x0)*sc, (y1-y0)*sc, fill=0, stroke=1)
        c.setLineWidth(0.7); c.setDash([4, 1.5, 1, 1.5])
        c.line(p.X(g.a[0]), p.Y(g.a[1]), p.X(g.b[0]), p.Y(g.b[1])); c.setDash()
        n = max(2, int(g.length//12.0))
        for i in range(n):
            f0 = (i+0.5)/n
            ux, uy = (g.b[0]-g.a[0])/g.length, (g.b[1]-g.a[1])/g.length
            m = (g.a[0]+ux*g.length*f0, g.a[1]+uy*g.length*f0)
            _arrow(p, (m[0]-ux*1.2, m[1]-uy*1.2), (m[0]+ux*1.2, m[1]+uy*1.2))
    c.setFillColor(black); c.setFont("Helvetica-Bold", 4.8)
    for g in G.GUTTERS:
        if g.mark == "W-1 FRONT": continue                     # one walk edge, labeled once
        lab = "%s  %s MIN" % (g.mark, _pct(g.slope))
        if g.a[0] == g.b[0]:
            my = (g.a[1]+g.b[1])/2.0
            north = g.a[0] < SITE_W/2.0
            c.saveState(); c.translate(p.X(0)-3.0 if north else p.X(SITE_W)+2.0+4.8*0.72, p.Y(my)); c.rotate(90)
            c.drawCentredString(0, 0, lab); c.restoreState()
        else:
            c.drawCentredString(p.X(g.a[0]+(g.b[0]-g.a[0])*0.72), p.Y(g.a[1]-g.w/2.0-0.5), lab)

    # Downspouts: each leader, its splash block and its mark.
    for ld in G.LEADERS:
        x0, y0, x1, y1 = ld.block
        c.setStrokeColor(black); c.setLineWidth(0.5); c.setFillColor(white)
        c.rect(p.X(x0), p.Y(y1), (x1-x0)*sc, (y1-y0)*sc, fill=1, stroke=1)
        c.setFillColor(black); c.circle(p.X(ld.x), p.Y(ld.y), 1.6, fill=1, stroke=0)
        inside_x = ld.x+(1.2 if ld.x <= G.B1X0+1e-6 else -1.2 if ld.x >= G.B1X1-1e-6 else 0.0)
        inside_y = ld.y+(0.0 if inside_x != ld.x else -1.2)
        c.setFont("Helvetica-Bold", 4.4); c.drawCentredString(p.X(inside_x)+(6 if inside_x > ld.x else -6 if inside_x < ld.x else 0), p.Y(inside_y)-1.5, ld.mark)

    # Drainage arrows, one per surface of every band long enough to carry one.
    for b in G.BANDS:
        if b.s1-b.s0 >= 4.0-1e-9:
            _band_arrows(p, b, min_arrow=MIN_ARROW, g=G)
    # The walks that run out from their landings.
    _u1c = (G.U1_WALK.x0+G.U1_WALK.x1)/2.0
    _arrow(p, (_u1c, G.U1_WALK.y1-0.6), (_u1c, G.U1_WALK.y0+0.6), _pct(_walk_slope(G.F_B1_FRONT, G.U1_LANDING.x0, g=G)))
    # Spot grades on the lot lines, the 10'-0" line and every flowline's ends.
    _spot(p, 7.0, 0.0, G.FRONT_LOT, dy=-6.5)
    _spot(p, 17.0, 0.0, G.FRONT_LOT, dy=-6.5)
    _spot(p, 17.0, G.FRONT_OPEN-G.FALL_RUN, G.G0-G.FALL)
    _padb = next(b for b in G.BANDS if b.face == G.F_B2_REAR)
    _spot(p, 13.0, SITE_D, _padb.section(13.0)[-1][1], dx=0.0, dy=3.0, anchor="c")
    for g, (x, y) in ((G.S1, G.S1.a), (G.S3, G.S3.a), (G.S3, (G.GX, G.B1Y0)), (G.S3, G.S3.b)):
        _spot(p, x, y, g.grade_at(x, y), dx=-(x*sc+2.0), dy=-6.5 if y < 1 else -1.6, anchor="r")
    _spot(p, G.S2.a[0], G.S2.a[1], G.S2.start, dx=-3.0, dy=3.5, anchor="r")
    for g, (x, y) in ((G.W1A, G.W1A.a), (G.W1A, G.W1A.b), (G.S4, G.S4.a), (G.S4, G.S4.b)):
        _spot(p, x, y, g.grade_at(x, y), dx=(SITE_W-x)*sc+1.5, dy=3.0 if y > SITE_D-1 else -1.6)

    # What lies around the lot.
    p.note(SITE_W/2.0, -3.6, "OAK AVENUE", 9.5, bold=True)
    p.vnote(-8.5, 62, NORTH_NEIGHBOUR[0], "RECEIVES NO WATER", 8.5)
    p.vnote(SITE_W+8.5, 62, SOUTH_NEIGHBOUR[0], "RECEIVES NO WATER", 8.5)
    p.note(SITE_W/2.0, SITE_D+3.4, "PUBLIC ALLEY", 7.5, bold=True)

    # ---------------- title, legend ----------------
    TTX, TTY = X0+7.6*inch, Y1-0.9*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 12); c.drawString(TTX, TTY, "GRADING AND DRAINAGE PLAN")
    c.setFont("Helvetica", 9); c.drawString(TTX, TTY-0.18*inch, "SCALE: 1/8\" = 1'-0\"")
    c.setStrokeColor(black); c.setLineWidth(1.2); c.line(TTX, TTY+0.20*inch, TTX+2.6*inch, TTY+0.20*inch)
    c.setFont("Helvetica", 7.2)
    c.drawString(TTX, TTY-0.44*inch, "OAK AVENUE AT THE TOP OF THE SHEET, AS THE FLOOR PLANS; TRUE NORTH PER C-101.")
    c.drawString(TTX, TTY-0.60*inch, "GRADES ARE INCHES FROM 0\" = FINISHED GRADE AT THE FOUNDATION WALLS — NOTE 1.")
    lx, ly = TTX, TTY-0.95*inch
    c.setFont("Helvetica-Bold", 8); c.drawString(lx, ly, "LEGEND"); ly -= 0.20*inch
    lp = _Swatch(lx, ly-4.0*sc, sc, 4.0)
    _spot(lp, 0.4, 2.0, -G.FALL)
    c.setFont("Helvetica", 6.6); c.drawString(lx+0.7*inch, ly-2.0*sc-2.0, "SPOT GRADE, INCHES FROM THE DATUM")
    ly -= 0.20*inch
    lp = _Swatch(lx, ly-4.0*sc, sc, 4.0)
    _arrow(lp, (0.0, 2.0), (4.5, 2.0), _pct(G.FALL/G.FALL_RUN))
    c.setFont("Helvetica", 6.6); c.drawString(lx+0.7*inch, ly-2.0*sc-2.0, "SURFACE DRAINAGE AND ITS SLOPE, AWAY FROM THE BUILDING")
    ly -= 0.22*inch
    c.setStrokeColor(black); c.setLineWidth(0.7); c.setDash([4, 1.5, 1, 1.5]); c.line(lx, ly-2.0*sc, lx+4.5*sc, ly-2.0*sc); c.setDash()
    c.setFont("Helvetica", 6.6); c.drawString(lx+0.7*inch, ly-2.0*sc-2.0, "FLOWLINE: GRASS SWALE S-1 TO S-4, WALK EDGE W-1")
    ly -= 0.22*inch
    c.setStrokeColor(GREY); c.setLineWidth(0.7); c.rect(lx, ly-2.0*sc-1.0*sc, 4.5*sc, 2.0*sc, fill=0, stroke=1)
    c.setFillColor(black); c.setFont("Helvetica", 6.6)
    c.drawString(lx+0.7*inch, ly-2.0*sc-2.0, "WALK OR PAD (GRAY), LANDING OR STOOP (BLACK), NOTE 5")

    # ---------------- notes ----------------
    snx, sny = TTX, ly-0.65*inch
    SNW = 6.4*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 9.5); c.drawString(snx, sny, "GRADING AND DRAINAGE NOTES")
    c.setStrokeColor(black); c.setLineWidth(0.7); c.line(snx, sny-4, snx+SNW, sny-4); sny -= 0.24*inch
    NOTES = [
     f"1.  DATUM — 0\" IS FINISHED GRADE AT THE FOUNDATION WALLS OF BOTH BUILDINGS; FINISHED FLOOR IS {grade.signed(levels.FF1)}. SPOT",
     "     GRADES ARE INCHES ABOVE (+) OR BELOW (-) IT. THE FOOTING DEPTH ON S-101 IS MEASURED FROM 0\": PLACE NO",
     "     FINISHED GRADE AT A FOUNDATION WALL BELOW IT.",
     "2.  SET THE DATUM FROM A SURVEY OF THE OAK SIDEWALK AND THE ALLEY BEFORE EITHER SLAB IS FORMED, SO THAT",
     f"     EVERY LOT-LINE GRADE ON THIS SHEET STANDS AT OR ABOVE THE PAVEMENT BEYOND IT: {grade.signed(G.FRONT_LOT)} AT OAK.",
     f"3.  RCO 401.3 — FINISHED GRADE FALLS {inches(G.FALL)} WITHIN THE FIRST {fmt(G.FALL_RUN)} OF A FOUNDATION WHERE {fmt(G.FALL_RUN)} IS AVAILABLE:",
     f"     BUILDING 1'S OAK FACE ({fmt(G.FRONT_OPEN)}). IMPERVIOUS SURFACES WITHIN {fmt(G.FALL_RUN)} FALL {_pct(G.IMPERVIOUS_MIN)} MINIMUM AWAY FROM",
     "     THE BUILDING. THE SCHEDULE GIVES EVERY FACE.",
     f"3a. SIDE YARDS ({fmt(G.NORTH_OPEN)}) AND THE FACES BETWEEN THE BUILDINGS ({fmt(G.COURT_OPEN)}) — THE 401.3 EXCEPTION: THE GROUND FALLS",
     f"     {_pct(G.EXC_RATE)} MINIMUM FROM THE WALL TO A SWALE. SOUTH OF BUILDING 1 THE LAWN STRIP AND THE UNITS 2 AND 3 WALK",
     f"     FALL TO W-1, THE WALK'S OUTER EDGE, WHICH FALLS {_pct(G.W1A.slope)} MINIMUM TO THE OAK SIDEWALK.",
     "3b. NO WATER IS DIRECTED ONTO EITHER ADJACENT PARCEL. MEET EXISTING GRADE AT BOTH SIDE LOT LINES; DO NOT FILL",
     "     AGAINST THEM.",
     f"4.  SWALES S-1 TO S-4 — GRADED AND SEEDED LAWN, FLOWLINE {fmt(G.GX)} OFF THE SIDE LOT LINE (S-2: {fmt(G.COURT_Y-G.B1Y1)} OFF BUILDING 1),",
     f"     FALLING {_pct(G.SWALE_SLOPE)} MINIMUM WITH THE ARROWS AT THE SPOT GRADES SHOWN. S-1 AND S-2 MEET AT THE HEAD OF S-3. S-3",
     "     AND S-4 WIDEN TO THE FULL SIDE YARD OVER THEIR LAST 10'-0\" AND MEET THE SIDEWALK AND THE ALLEY AT GRADE.",
     "5.  PAVING — A LANDING STANDS AT EVERY EXTERIOR DOOR, RCO 311.3, SCHEDULED BELOW.",
     f"     WALKS FALL {_pct(G.IMPERVIOUS_MIN)} TO {_pct(G.WALK_MAX)} AWAY FROM THE BUILDINGS; LANDINGS AND THE STOOP FALL {_pct(grade.LANDING_MAX)},",
     f"     WITH TOPS AT {grade.signed(G.LANDING_TOP)}. HOLD FINISHED GRADE AT THE FOOT OF EACH AT ITS SPOT GRADES: ONE STEP, NOT OVER",
     f"     {inches(G.RISER_MAX)}, 311.7.5.1. THE PARKING PAD FALLS {_pct(G.IMPERVIOUS_MIN)} TO THE ALLEY. ALL PAVING {psi(FLATWORK.psi)} AIR-ENTRAINED",
     "     CONCRETE, S-101.",
    ]
    over = [t for t in NOTES if pdfmetrics.stringWidth(t, "Helvetica", 7.0) > SNW]
    assert not over, "C-103 note line overruns its column: %r" % over[:1]
    c.setFont("Helvetica", 7.0)
    for t in NOTES:
        c.drawString(snx, sny, t); sny -= 0.135*inch
    assert sny >= Y0+0.10*inch, "C-103 notes overrun the sheet by %.2f in" % ((Y0+0.10*inch-sny)/inch)

    # ---------------- roof drainage ----------------
    sny -= 0.22*inch
    c.setFont("Helvetica-Bold", 9.5); c.drawString(snx, sny, "ROOF DRAINAGE — DOWNSPOUTS")
    c.setLineWidth(0.7); c.line(snx, sny-4, snx+SNW, sny-4); sny -= 0.24*inch
    for ld in G.LEADERS:
        l1 = "%s  %s" % (ld.mark, ld.eave)
        r1 = "%.0f SF, %.1f GPM   ·   TO %s" % (G.eave_area(ld), G.leader_gpm(ld), ld.to)
        w = pdfmetrics.stringWidth(l1, "Helvetica-Bold", 6.8)+pdfmetrics.stringWidth(r1, "Helvetica", 6.8)+6
        assert w <= SNW, "C-103 downspout row overruns: %r" % l1
        c.setFont("Helvetica-Bold", 6.8); c.drawString(snx, sny, l1)
        c.setFont("Helvetica", 6.8); c.drawRightString(snx+SNW, sny, r1); sny -= 0.16*inch
    sny -= 0.06*inch
    ROOF = [
     "6.  EACH EAVE GUTTER FALLS TO THE ONE LEADER SCHEDULED FOR IT. EACH LEADER DISCHARGES THROUGH AN ELBOW ONTO A",
     f"     PRECAST {inches(G.SPLASH_W)} x {inches(G.SPLASH_L)} SPLASH BLOCK ON THE LAWN, OPC 1101.2, WHICH FALLS TO THE RECEIVER SCHEDULED. DS-2",
     "     TURNS BUILDING 1'S REAR CORNER ONTO ITS REAR FACE; %s RUNS UNDER THE PARKING WALK IN A 4\" PVC SLEEVE" % " AND ".join(G.SLEEVED),
     "     TO ITS BLOCK. NO LEADER CONNECTS TO THE BUILDING SEWER, C.C. 1145.84.",
     "6a. KEEP EVERY SPLASH BLOCK OFF EVERY WALK, LANDING, THE STOOP AND THE PARKING PAD.",
     f"6b. SIZE, OPC 1106 — GUTTERS {G.EAVE_GUTTER} SEMICIRCULAR SECTION MINIMUM AT 1/8\" PER FOOT, {G.EAVE_GUTTER_GPM} GPM, TABLE 1106.6; LEADERS",
     f"     {G.LEADER}\", TAKEN AT TABLE 1106.3'S 2 x 2 ROW, {G.LEADER_GPM} GPM; {max(G.leader_gpm(l) for l in G.LEADERS):.1f} GPM MAXIMUM AT {G.RAIN_LEADER:g} IN/H.",
    ]
    over = [t for t in ROOF if pdfmetrics.stringWidth(t, "Helvetica", 7.0) > SNW]
    assert not over, "C-103 roof drainage note overruns its column: %r" % over[:1]
    c.setFont("Helvetica", 7.0)
    for t in ROOF:
        c.drawString(snx, sny, t); sny -= 0.135*inch
    assert sny >= Y0+0.10*inch, "C-103 roof drainage overruns the sheet by %.2f in" % ((Y0+0.10*inch-sny)/inch)

    # ---------------- schedules ----------------
    tx, ty, TW = X1-4.9*inch, Y1-0.9*inch, 4.6*inch
    c.setFont("Helvetica-Bold", 9.5); c.drawString(tx, ty, "FINISHED GRADE BY FACE — RCO 401.3")
    c.setLineWidth(0.7); c.line(tx, ty-4, tx+TW, ty-4); ty -= 0.24*inch
    for f in G.FACES:
        room, fall, method = G.face_summary(f)
        l1 = "%s — %s" % (f.building, f.side)
        r1 = "%s TO %s" % (room, f.side[len("FACE TO "):] if f.side.startswith("FACE TO ") else "LOT LINE")
        l2 = "     %s   ·   %s" % (fall, method)
        w1 = pdfmetrics.stringWidth(l1, "Helvetica-Bold", 6.8)+pdfmetrics.stringWidth(r1, "Helvetica", 6.8)+6
        assert w1 <= TW and pdfmetrics.stringWidth(l2, "Helvetica", 6.6) <= TW, "C-103 schedule row overruns: %r" % l1
        c.setFont("Helvetica-Bold", 6.8); c.drawString(tx, ty, l1)
        c.setFont("Helvetica", 6.8); c.drawRightString(tx+TW, ty, r1); ty -= 0.125*inch
        c.setFont("Helvetica", 6.6); c.drawString(tx, ty, l2); ty -= 0.17*inch
    ty -= 0.12*inch
    assert set(GUTTER_RUNS) == {g.mark for g in G.GUTTERS}, "C-103 names a flowline the model does not have"
    c.setFont("Helvetica-Bold", 9.5); c.drawString(tx, ty, "FLOWLINES — NOTES 3a AND 4")
    c.setLineWidth(0.7); c.line(tx, ty-4, tx+TW, ty-4); ty -= 0.24*inch
    for g in G.GUTTERS:
        l1 = "%s  %s" % (g.mark, GUTTER_RUNS[g.mark])
        r1 = "%s, %s AT %s MIN" % (("%s WIDE" % fmt(g.w)) if g.w else KIND_WORD[g.kind], fmt(g.length), _pct(g.slope))
        l2 = "     FLOWLINE %s TO %s   ·   TO %s" % (grade.signed(g.start), grade.signed(g.end),
                                                   {"OAK": "THE OAK SIDEWALK", "ALLEY": "THE ALLEY"}.get(g.to, g.to))
        w = pdfmetrics.stringWidth(l1, "Helvetica-Bold", 6.8)+pdfmetrics.stringWidth(r1, "Helvetica", 6.8)+6
        assert w <= TW and pdfmetrics.stringWidth(l2, "Helvetica", 6.6) <= TW, "C-103 gutter row overruns: %r" % l1
        c.setFont("Helvetica-Bold", 6.8); c.drawString(tx, ty, l1)
        c.setFont("Helvetica", 6.8); c.drawRightString(tx+TW, ty, r1); ty -= 0.125*inch
        c.setFont("Helvetica", 6.6); c.drawString(tx, ty, l2); ty -= 0.17*inch
    ty -= 0.12*inch
    rng = lambda r, f: f(r[0]) if abs(r[1]-r[0]) < IN(1)/16.0 else "%s TO %s" % (f(r[0]), f(r[1]))
    c.setFont("Helvetica-Bold", 9.5); c.drawString(tx, ty, "LANDINGS AND STOOPS — ONE STEP, NOTE 5")
    c.setLineWidth(0.7); c.line(tx, ty-4, tx+TW, ty-4); ty -= 0.24*inch
    for name, top, nose, foot, step, walk in site_steps.step_summary(G.STEPS, G.BANDS, G.STOOP_STEP):
        r1 = "STEP %s, %s MAX" % (rng(step, inches), inches(G.RISER_MAX))
        l2 = "     TOP %s AT THE WALL   ·   NOSING %s   ·   FOOT %s, %s AT ITS WALK" % (
            grade.signed(top), rng(nose, grade.signed), rng(foot, grade.signed), grade.signed(walk[2]))
        w = pdfmetrics.stringWidth(name, "Helvetica-Bold", 6.8)+pdfmetrics.stringWidth(r1, "Helvetica", 6.8)+6
        assert w <= TW and pdfmetrics.stringWidth(l2, "Helvetica", 6.6) <= TW, "C-103 step row overruns: %r" % name
        c.setFont("Helvetica-Bold", 6.8); c.drawString(tx, ty, name)
        c.setFont("Helvetica", 6.8); c.drawRightString(tx+TW, ty, r1); ty -= 0.125*inch
        c.setFont("Helvetica", 6.6); c.drawString(tx, ty, l2); ty -= 0.17*inch
    assert ty >= Y0+0.10*inch, "C-103 schedules overrun the sheet"
    c.showPage()

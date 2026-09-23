"""C-103 — the grading and drainage plan.

   Drawn at 1/8" = 1'-0" on C-101's plan origin, from src/grading.py: every band,
   section, gutter and grade on this sheet is the model's, and check_grading() has held
   each to RCO 401.3 before a line is drawn. Nothing here computes a grade; it places
   the ones the model has. The walks, landings, stoops and pad are drawn from the same
   rectangles the model bands its faces by, so an arrow cannot cross paving the model
   does not know about."""
from arkitect.lib.draw.context import LAY
from arkitect.lib.draw.page import GREY, PlanDraw, Sheet
from arkitect.lib.units import IN, fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import levels
from src import downspouts as DS
from src import grading as G
from arkitect.lib.model import grade as grade
from src.foundation import FLATWORK
from arkitect.codes.ohio.rco.concrete import psi
from src.sitework import NUM_WORD, SITE_D, SITE_W, SITE_WALK, TREE_R, TREE_X, TREE_Y
from src.sheets import roofdrain
from arkitect.lib.draw.kit import DH, E, X0, X1, Y0, Y1, c
from arkitect.lib.draw.civil_kit import _Swatch, _arrow, _pct
from arkitect.lib.draw.civil_kit import _band_arrows
from arkitect.lib.draw.civil_kit import _spot as _shared_spot
from arkitect.lib.draw.civil_kit import _walk_slope
from functools import partial
from arkitect.codes.ohio.rco import site_steps

MIN_ARROW = 1.5          # a surface shorter than this, in feet, takes no arrow of its own: the 1'-9"
                         # of lawn either side of G-1 takes one

# What each gutter is, in words. The figures beside it are the model's.
GUTTER_RUNS = {"G-1": "BETWEEN THE BUILDINGS",
               "G-2": "BUILDING 2, ADJACENT-PARCEL SIDE",
               "G-3": "BUILDING 1, ADJACENT-PARCEL SIDE"}


_spot = partial(_shared_spot, g=G)






def _tops():
    """The landings' and stoops' tops, once where they are one height."""
    a, b = grade.signed(G.LANDING_TOP), grade.signed(G.STOOP_TOP)
    return a if a == b else "%s AND %s" % (a, b)


def sheet_c103():
    sh = Sheet(c, "C-103", "Grading and drainage plan", "1/8\" = 1'-0\""); sh.frame()
    sc = E; W, D = SITE_W, SITE_D
    ox = X0+1.7*inch; oy = Y0+(DH-D*sc)/2-0.2*inch            # C-101's plan origin
    p = PlanDraw(c, ox, oy, sc, W, D)
    LAY("A-WALL")
    c.setStrokeColor(black); c.setLineWidth(1.6); c.setFillColor(white)
    c.rect(p.X(0), p.Y(D), W*sc, D*sc, fill=1, stroke=1)
    # The new public sidewalk: what the Sage faces drain across, C-101 note 1.
    c.setStrokeColor(GREY); c.setLineWidth(0.7)
    c.rect(p.X(-SITE_WALK), p.Y(D), SITE_WALK*sc, D*sc, fill=0, stroke=1)
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
    # The tree, so the gutter is seen to clear it.
    c.setStrokeColor(GREY); c.setLineWidth(0.6)
    c.circle(p.X(TREE_X), p.Y(TREE_Y), TREE_R*sc, fill=0, stroke=1)

    # Gutters: the concrete width, the flowline, flow arrows and the mark.
    LAY("A-ANNO-TEXT")
    for g in G.GUTTERS:
        x0, y0, x1, y1 = g.box()
        c.setStrokeColor(black); c.setLineWidth(0.5); c.setFillColor(white)
        c.rect(p.X(x0), p.Y(y1), (x1-x0)*sc, (y1-y0)*sc, fill=0, stroke=1)
        c.setLineWidth(0.7); c.setDash([4, 1.5, 1, 1.5])
        c.line(p.X(g.a[0]), p.Y(g.a[1]), p.X(g.b[0]), p.Y(g.b[1])); c.setDash()
        n = max(2, int(g.length//12.0))
        for i in range(n):
            f0 = (i+0.5)/n
            ux, uy = (g.b[0]-g.a[0])/g.length, (g.b[1]-g.a[1])/g.length
            m = (g.a[0]+ux*g.length*f0, g.a[1]+uy*g.length*f0)
            _arrow(p, (m[0]-ux*1.2, m[1]-uy*1.2), (m[0]+ux*1.2, m[1]+uy*1.2))
    # The inlet the gutters end at: its grate, crossed, and its mark beside it.
    for i in G.INLETS:
        x0, y0, x1, y1 = G.inlet_box(i)
        c.setStrokeColor(black); c.setLineWidth(0.8); c.setFillColor(white)
        c.rect(p.X(x0), p.Y(y1), (x1-x0)*sc, (y1-y0)*sc, fill=1, stroke=1)
        c.setLineWidth(0.5)
        c.line(p.X(x0), p.Y(y0), p.X(x1), p.Y(y1)); c.line(p.X(x0), p.Y(y1), p.X(x1), p.Y(y0))
        c.setFillColor(black); c.setFont("Helvetica-Bold", 4.8)
        c.drawRightString(p.X(x0)-2.0, p.Y(i.at[1])-1.6, i.mark)
    # Its pipe roof drains, out across the S Elm lot line toward the curb.
    _o = G.outlet()
    c.setStrokeColor(black); c.setLineWidth(0.6); c.setDash([2.5, 1.5])
    for k in range(_o["pipes"]):
        px = G.INLET.at[0]+(k-(_o["pipes"]-1)/2.0)*0.4
        c.line(p.X(px), p.Y(G.INLET.at[1]-G.INLET.size/2.0), p.X(px), p.Y(-3.0))
    c.setDash()
    c.setFillColor(black); c.setFont("Helvetica-Bold", 4.8)
    c.drawRightString(p.X(G.INLET.at[0]-1.4), p.Y(-1.5)-1.6,
                      "%s %s PVC ROOF-DRAIN LATERALS TO THE S ELM CURB — NOTE 4a" % (NUM_WORD[_o["pipes"]], inches(G.STD2320_D)))
    c.setFillColor(black); c.setFont("Helvetica-Bold", 4.8)
    for g in G.GUTTERS:
        lab = "%s  %s MIN" % (g.mark, _pct(g.slope))
        if g.a[0] == g.b[0]:
            my = (g.a[1]+g.b[1])/2.0
            c.saveState(); c.translate(p.X(SITE_W)+2.0+4.8*0.72, p.Y(my)); c.rotate(90)
            c.drawCentredString(0, 0, lab); c.restoreState()
        else:
            c.drawCentredString(p.X(g.a[0]+(g.b[0]-g.a[0])*0.65), p.Y(g.a[1]+g.w/2.0+0.9), lab)

    # Downspouts: each leader, its splash block and the way its water goes.
    roofdrain.plan(p, sc)

    # Drainage arrows, one per surface of every band long enough to carry one.
    for b in G.BANDS:
        if b.s1-b.s0 >= 4.0-1e-9:
            _band_arrows(p, b, min_arrow=MIN_ARROW, g=G)
    # The walks that run out from their landings.
    _u1c = (G.U1_WALK.x0+G.U1_WALK.x1)/2.0
    _arrow(p, (_u1c, G.U1_WALK.y1-0.6), (_u1c, G.U1_WALK.y0+0.6), _pct(_walk_slope(G.F_B1_FRONT, G.U1_LANDING.x0, g=G)))
    _u2c = (G.U2_WALK.y0+G.U2_WALK.y1)/2.0
    _arrow(p, (G.U2_WALK.x1-0.4, _u2c), (G.U2_WALK.x0+0.4, _u2c), _pct(_walk_slope(G.F_B1_SAFF, G.U2_LANDING.y0, g=G)))

    # Spot grades on the lot lines, the 10'-0" line and every gutter node.
    _spot(p, 4.0, 0.0, G.FRONT_LOT, dy=-6.5)
    _spot(p, 16.0, 0.0, G.FRONT_LOT, dy=-6.5)
    _spot(p, 16.0, G.FRONT_OPEN-G.FALL_RUN, G.G0-G.FALL)
    _spot(p, 0.0, 28.0, G.SAFFORD_LOT)
    _spot(p, 0.0, _u2c, G.U2_WALK_END, dy=-7.5)
    _spot(p, 0.0, 86.0, G.SAFFORD_LOT)
    _spot(p, 5.0, SITE_D, G.ALLEY_LAWN, dx=0.0, dy=3.0, anchor="c")
    _pad = next(b for b in G.BANDS if b.face == G.F_B2_REAR and b.to == "ALLEY" and abs(b.s0-G.PAD.x0) < 1e-9)
    _spot(p, G.PAD.x0+3.0, SITE_D, _pad.section(G.PAD.x0+3.0)[-1][1], dx=0.0, dy=3.0, anchor="c")
    _spot(p, G.G1.a[0], G.G1.a[1], G.G1.start, dx=3.0, dy=2.5)
    for g, y in ((G.G2, G.G2.a[1]), (G.G3, G.G3.a[1]), (G.G3, G.B1Y0), (G.G3, G.G3.b[1])):
        _spot(p, G.GX, y, g.grade_at(G.GX, y), dx=(SITE_W-G.GX)*sc+1.5, dy=-1.6 if y > 0 else -6.5)

    # The streets, as C-101 names them.
    p.note(20, -3.4, "S ELM AVENUE", 9.5, bold=True)
    p.vnote(-7.2, 63, "SAGE AVENUE", "SIDE STREET", 9.5)
    p.vnote(45.2, 63, "ADJACENT PARCEL", "RECEIVES NO WATER", 9.5)
    p.note(41.0, 126.95, "PUBLIC ALLEY  —  REAR", 7.5, anchor="l", bold=True)

    # ---------------- title, legend ----------------
    TTX, TTY = X0+7.6*inch, Y1-0.9*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 12); c.drawString(TTX, TTY, "GRADING AND DRAINAGE PLAN")
    c.setFont("Helvetica", 9); c.drawString(TTX, TTY-0.18*inch, "SCALE: 1/8\" = 1'-0\"")
    c.setStrokeColor(black); c.setLineWidth(1.2); c.line(TTX, TTY+0.20*inch, TTX+2.6*inch, TTY+0.20*inch)
    c.setFont("Helvetica", 7.2)
    c.drawString(TTX, TTY-0.44*inch, "ORIENTATION AS C-101: S ELM AT THE TOP OF THE SHEET, SAGE ON THE LEFT.")
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
    c.setStrokeColor(black); c.setLineWidth(0.5); c.rect(lx, ly-2.0*sc-G.GUTTER_W*sc/2, 4.5*sc, G.GUTTER_W*sc, fill=0, stroke=1)
    c.setLineWidth(0.7); c.setDash([4, 1.5, 1, 1.5]); c.line(lx, ly-2.0*sc, lx+4.5*sc, ly-2.0*sc); c.setDash()
    c.setFont("Helvetica", 6.6); c.drawString(lx+0.7*inch, ly-2.0*sc-2.0, "CONCRETE VALLEY GUTTER AND FLOWLINE, NOTE 4")
    ly -= 0.22*inch
    c.setStrokeColor(GREY); c.setLineWidth(0.7); c.rect(lx, ly-2.0*sc-1.0*sc, 4.5*sc, 2.0*sc, fill=0, stroke=1)
    c.setFillColor(black); c.setFont("Helvetica", 6.6)
    c.drawString(lx+0.7*inch, ly-2.0*sc-2.0, "WALK OR PAD (GRAY), LANDING OR STOOP (BLACK), NOTE 5")

    # ---------------- notes ----------------
    snx, sny = TTX, ly-0.65*inch
    SNW = 6.4*inch
    c.setFillColor(black); c.setFont("Helvetica-Bold", 9.5); c.drawString(snx, sny, "GRADING AND DRAINAGE NOTES")
    c.setStrokeColor(black); c.setLineWidth(0.7); c.line(snx, sny-4, snx+SNW, sny-4); sny -= 0.24*inch
    xing = G.sewer_crossings()
    assert len(xing) == 1, "C-103 note 6 describes one sewer crossing; the model has %d" % len(xing)
    _xm, (_xx, _xy), _xf, _xc = xing[0]
    NOTES = [
     f"1.  DATUM — 0\" IS FINISHED GRADE AT THE FOUNDATION WALLS OF BOTH BUILDINGS; FINISHED FLOOR IS {grade.signed(levels.FF1)}. SPOT",
     "     GRADES ARE INCHES ABOVE (+) OR BELOW (-) IT. THE FOOTING DEPTH ON S-101 IS MEASURED FROM 0\": PLACE NO",
     "     FINISHED GRADE AT A FOUNDATION WALL BELOW IT.",
     "2.  SET THE DATUM FROM A SURVEY OF THE S ELM SIDEWALK AND CURB, THE SAGE CURB AND THE ALLEY BEFORE",
     "     EITHER SLAB IS FORMED, SO THAT EVERY LOT-LINE GRADE ON THIS SHEET STANDS AT OR ABOVE THE PAVEMENT BEYOND IT.",
     f"3.  RCO 401.3 — FINISHED GRADE FALLS {inches(G.FALL)} WITHIN THE FIRST {fmt(G.FALL_RUN)} OF EACH FOUNDATION WHERE {fmt(G.FALL_RUN)} HORIZONTAL",
     f"     DISTANCE IS AVAILABLE: THE S ELM FACE ({fmt(G.FRONT_OPEN)}) AND THE LAWN BEHIND BUILDING 2. IMPERVIOUS SURFACES WITHIN",
     f"     {fmt(G.FALL_RUN)} FALL {_pct(G.IMPERVIOUS_MIN)} MINIMUM AWAY FROM THE BUILDING. THE SCHEDULE GIVES EVERY FACE.",
     f"3a. SAGE FACES — {fmt(G.SAFF_OPEN)} TO THE RIGHT-OF-WAY. THE WHOLE {inches(G.FALL)} IS TAKEN ON THE LOT, TO {grade.signed(G.SAFFORD_LOT)} AT THE",
     "     LOT LINE; THE NEW PUBLIC SIDEWALK, C-101 NOTE 1, CARRIES THE SURFACE ON AT ITS CROSS SLOPE TO THE CURB.",
     "     SET ITS BACK EDGE AT OR BELOW THE LOT-LINE GRADES.",
     f"3b. ADJACENT-PARCEL FACES ({fmt(G.PARCEL_OPEN)}) AND THE FACES BETWEEN THE BUILDINGS ({fmt(G.COURT_OPEN)}; G-1 {fmt(G.COURT_Y-G.B1Y1)} OFF BUILDING 1) — WITHOUT",
     f"     {fmt(G.FALL_RUN)} THEY DRAIN UNDER THE 401.3 EXCEPTION: {inches(G.FALL)} MINIMUM FROM THE WALL TO THE FLOWLINE OF A",
     "     CONCRETE GUTTER. NO WATER IS DIRECTED ONTO THE ADJACENT PARCEL; DO NOT FILL AGAINST ITS LOT LINE.",
     f"4.  GUTTERS G-1 TO G-3 — {fmt(G.GUTTER_W)} WIDE CONCRETE VALLEY GUTTER ({fmt(G.G1.w)} AT G-1, BETWEEN THE BUILDINGS), {inches(G.GUTTER_T)} THICK",
     f"     ON COMPACTED SUBGRADE, {inches(G.GUTTER_DEPTH)}",
     f"     DEEP AT THE FLOWLINE, FALLING {_pct(G.GUTTER_SLOPE)} MINIMUM WITH THE ARROWS. G-1 AND G-2 MEET AT THE HEAD OF G-3, WHICH",
     f"     ENDS AT INLET {G.INLET.mark}, {fmt(G.INLET.at[1])} INSIDE THE S ELM LOT LINE. ITS FAR EDGE STANDS {fmt(G.GUTTER_LOT_CLR)} OFF THE ADJACENT-PARCEL LOT LINE.",
     f"4a. INLET {G.INLET.mark} — {fmt(G.INLET_W)} SQUARE GRATED CATCH BASIN, RIM {grade.signed(G.INLET.rim)} AT G-3'S FLOWLINE. THE LAWN RISES {inches(G.FRONT_LOT-G.INLET.rim)}",
     "     FROM IT TO THE S ELM LOT LINE: NO GUTTER DISCHARGES ONTO A SIDEWALK, A STREET OR THE ALLEY. FROM IT,",
     f"     {NUM_WORD[_o['pipes']]} {inches(G.STD2320_D)} PVC ROOF-DRAIN LATERALS, COLUMBUS STANDARD DRAWING 2320, AT {100*G.STD2320_SLOPE:.2f}% UNDER THE S ELM SIDEWALK",
     f"     TO CORE-DRILLED OPENINGS IN THE CURB, INVERT {grade.signed(_o['invert_inlet'])} AT {G.INLET.mark}: {_o['flow']:.2f} CFS, THE {G.RAIN_I:.2f} IN/HR 10-YEAR",
     f"     5-MINUTE RAIN ON {_o['area']:,.0f} SF OF BOTH ROOFS AND THE YARDS THE GUTTERS DRAIN. THE SURVEY OF NOTE 2 PLACES",
     f"     THE S ELM GUTTER FLOWLINE AT THE OUTLETS AT OR BELOW {grade.signed(_o['invert_curb'])}, THE CURB FACE TAKEN {fmt(G.CURB_OUT)} PAST THE LOT LINE.",
     "     RIGHT-OF-WAY PERMIT, C.C. CHAPTER 910.",
     f"5.  PAVING — WALKS FALL {_pct(G.IMPERVIOUS_MIN)} TO {_pct(G.WALK_MAX)} AWAY FROM THE BUILDINGS; LANDINGS AND STOOPS FALL {_pct(grade.LANDING_MAX)}, RCO 311.3,",
     f"     WITH TOPS AT {_tops()}. HOLD FINISHED GRADE AT THE FOOT OF EACH AT ITS SPOT GRADES: ONE STEP,",
     f"     NOT OVER {inches(G.RISER_MAX)}, 311.7.5.1; {inches(G.STOOP_STEP)} OFF A STOOP. THE PARKING PAD FALLS {_pct(G.IMPERVIOUS_MIN)} TO THE ALLEY.",
     f"     ALL PAVING {psi(FLATWORK.psi)} AIR-ENTRAINED CONCRETE, S-101.",
     f"6.  BUILDING SEWER — {_xm} CROSSES IT {fmt(_xx)} OFF THE SAGE LOT LINE WITH {inches(_xc)} FROM THE FLOWLINE TO THE CROWN.",
     "     PLACE THE GUTTER AFTER THE TRENCH IS BACKFILLED AND COMPACTED, C-101 NOTE 4d.",
    ]
    over = [t for t in NOTES if pdfmetrics.stringWidth(t, "Helvetica", 7.0) > SNW]
    assert not over, "C-103 note line overruns its column: %r" % over[:1]
    c.setFont("Helvetica", 7.0)
    for t in NOTES:
        c.drawString(snx, sny, t); sny -= 0.135*inch
    assert sny >= Y0+0.10*inch, "C-103 notes overrun the sheet by %.2f in" % ((Y0+0.10*inch-sny)/inch)

    # ---------------- roof drainage ----------------
    # Under the notes, in the left column: the right column is the schedules'.
    sny -= 0.22*inch
    c.setFont("Helvetica-Bold", 9.5); c.drawString(snx, sny, "ROOF DRAINAGE — DOWNSPOUTS")
    c.setLineWidth(0.7); c.line(snx, sny-4, snx+SNW, sny-4); sny -= 0.24*inch
    for l1, r1, l2 in roofdrain.schedule_rows():
        w = pdfmetrics.stringWidth(l1, "Helvetica-Bold", 6.8)+pdfmetrics.stringWidth(r1, "Helvetica", 6.8)+6
        assert w <= SNW and pdfmetrics.stringWidth(l2, "Helvetica", 6.6) <= SNW, "C-103 downspout row overruns: %r" % l1
        c.setFont("Helvetica-Bold", 6.8); c.drawString(snx, sny, l1)
        c.setFont("Helvetica", 6.8); c.drawRightString(snx+SNW, sny, r1); sny -= 0.125*inch
        c.setFont("Helvetica", 6.6); c.drawString(snx, sny, l2); sny -= 0.17*inch
    ROOF = [
     "7.  EACH EAVE GUTTER, S-103 NOTE 5, FALLS TO THE ONE LEADER SCHEDULED FOR IT, AT ITS REAR CORNER. EACH LEADER",
     f"     DISCHARGES THROUGH AN ELBOW ONTO A PRECAST {inches(DS.SPLASH_W)} x {inches(DS.SPLASH_L)} SPLASH BLOCK ON THE LAWN, OPC 1101.2; SHORTEN THE",
     "     SPLASH BLOCK AS REQUIRED WHERE THE RECEIVER GUTTER IS CLOSER. IT FALLS WITH THE ARROW TO THE RECEIVER",
     "     SCHEDULED. NO LEADER CONNECTS TO THE BUILDING",
     "     SEWER, C.C. 1145.84.",
     f"7a. KEEP EVERY SPLASH BLOCK {fmt(DS.TRENCH_CLR)} CLEAR OF THE BUILDING SEWER, THE BUILDING 2 LATERAL AND BOTH WATER SERVICES,",
     "     AND OFF EVERY WALK, LANDING, STOOP AND THE PARKING PAD.",
     f"7b. SIZE, OPC 1106 — GUTTERS {DS.GUTTER_IN}\" SEMICIRCULAR SECTION MINIMUM AT 1/8\" PER FOOT, {DS.T1106_6[(DS.GUTTER_IN, DS.GUTTER_PITCH)]} GPM, TABLE 1106.6;",
     f"     LEADERS {DS.LEADER}\", TAKEN AT TABLE 1106.3'S {DS.LEADER_ROW} ROW, {DS.T1106_3[DS.LEADER_ROW]} GPM; {max(DS.flow(e.area) for e in DS.EAVES):.1f} GPM MAXIMUM AT {DS.RAIN:g} IN/H.",
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
    assert set(GUTTER_RUNS) == {g.mark for g in G.GUTTERS}, "C-103 names a gutter the model does not have"
    c.setFont("Helvetica-Bold", 9.5); c.drawString(tx, ty, "GUTTERS — NOTE 4")
    c.setLineWidth(0.7); c.line(tx, ty-4, tx+TW, ty-4); ty -= 0.24*inch
    for g in G.GUTTERS:
        l1 = "%s  %s" % (g.mark, GUTTER_RUNS[g.mark])
        r1 = "%s WIDE, %s AT %s MIN" % (fmt(g.w), fmt(g.length), _pct(g.slope))
        l2 = "     FLOWLINE %s TO %s   ·   TO %s" % (grade.signed(g.start), grade.signed(g.end),
                                                   "THE S ELM LOT LINE" if g.to == "S ELM" else g.to)
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

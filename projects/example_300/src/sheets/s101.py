"""S-101 — foundation plans of both buildings: trench footing, foundation wall, slab.

Draws src/foundation.py and nothing it does not hold. The plans are in final sheet
coordinates already (see that module), so PlanDraw takes them straight: no mirror.
"""
from lib.draw.page import GREY, LAY, Sheet
from lib.draw.plan import PlanDraw
from lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import criteria as crit
from src import levels
from src import radon as RN
from lib.draw.text import wrap_notes
from src.foundation import (B1, B2, BAR_COVER, CONCRETE, EDGE_INSUL_RUN, ENERGY_R, FLATWORK, FROST_DEPTH, FTG_BAR, GRAVEL_T,
                            RETARDER_MIL, FTG_PROJ, FTG_T, FTG_W, INSUL_NAME, INSUL_R_NOM, INSUL_T,
                            PAD_EDGE, PAD_T, SLAB, SLAB_T, STRIP_D, STRIP_W, TERMITE, TERMITE_METHOD,
                            TERMITE_METHODS, TERMITE_TREATMENT, WALL_T, WEATHERING)
from codes.ohio.rco.concrete import ACI_DEICING, AIR_MAX, AIR_MIN, psi
from src.building1 import Y_SEP_TOP
from src.grading import FALL, FALL_RUN, IMPERVIOUS_MIN
from src import drainage as _dr
from codes.ohio.opc_service_entry import entry_for
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from lib.draw.foundation_kit import _band

TERMITE_SIZE = 6.6
TERMITE_LEAD = 0.112*inch


def termite_notes(width):
    """The TERMITE PROTECTION block, RCO 318, re-set to the width under the Building 1 plan.
       It cites the foundation notes by number and adds none of its own."""
    return wrap_notes([
     "T1. TABLE 301.2(1) READS %s, G-001. PROTECT BOTH BUILDINGS BY RCO 318.1 ITEM %d, %s, AS %s."
     % (TERMITE, TERMITE_METHOD, TERMITE_METHODS[TERMITE_METHOD], TERMITE_TREATMENT),
     "T2. APPLICATOR — A COMMERCIAL PESTICIDE APPLICATOR LICENSED BY THE OHIO DEPARTMENT OF AGRICULTURE FOR TERMITE CONTROL. TERMITICIDE,"
     " CONCENTRATION, RATE OF APPLICATION AND METHOD OF TREATMENT IN STRICT ACCORDANCE WITH THE TERMITICIDE LABEL, 318.2.",
     "T3. SEQUENCE — UNDER EACH SLAB AND BEARING STRIP, NOTES 2 AND 4, ONCE THE GRAVEL IS COMPACTED AND THE UNDER-SLAB PIPING OF NOTE 8 IS"
     " TESTED AND BACKFILLED, BEFORE THE VAPOR RETARDER IS LAID; AROUND EVERY SLAB PENETRATION, P-101; UNDER EACH PAD, NOTE 5, BEFORE IT IS"
     " POURED; ALONG THE OUTSIDE FACE OF THE FOUNDATION WALL AFTER FINISHED GRADING, C-103. RETREAT SOIL DISTURBED AFTER TREATMENT BEFORE"
     " IT IS COVERED.",
     "T4. CERTIFICATE — THE APPLICATOR'S CERTIFICATE OF TREATMENT, NAMING THE TERMITICIDE, ITS EPA REGISTRATION NUMBER, THE CONCENTRATION,"
     " VOLUME AND AREAS TREATED AND THE DATE, TO THE BUILDING OFFICIAL BEFORE EACH SLAB IS POURED, AND FOR THE OUTSIDE TREATMENT BEFORE"
     " FINAL INSPECTION. THE TREATED SILL PLATES OF NOTE 6 ARE IN ADDITION.",
    ], width, TERMITE_SIZE)


def _plan(b, ox, oy):
    """One building's foundation plan at Q, origin at the sheet point (ox, oy)."""
    p = PlanDraw(c, ox, oy, Q, b.W, b.D)
    LAY("S-FNDN")
    # the slab, then the foundation wall as a band just inside its outline
    c.setStrokeColor(black); c.setLineWidth(1.4); c.setFillColor(white)
    c.rect(p.X(0), p.Y(b.D), b.W*Q, b.D*Q, fill=1, stroke=1)
    for x0, y0, x1, y1 in ((0, 0, b.W, WALL_T), (0, b.D-WALL_T, b.W, b.D),
                           (0, 0, WALL_T, b.D), (b.W-WALL_T, 0, b.W, b.D)):
        _band(p, x0, y0, x1, y1)
    # the footing under the wall, projecting FTG_PROJ past each face: dashed, both edges
    c.setStrokeColor(GREY); c.setLineWidth(0.6); c.setDash(3, 2)
    c.rect(p.X(-FTG_PROJ), p.Y(b.D+FTG_PROJ), (b.W+2*FTG_PROJ)*Q, (b.D+2*FTG_PROJ)*Q, fill=0, stroke=1)
    _i = WALL_T+FTG_PROJ
    c.rect(p.X(_i), p.Y(b.D-_i), (b.W-2*_i)*Q, (b.D-2*_i)*Q, fill=0, stroke=1)
    c.setDash(); c.setStrokeColor(black)
    for x0, y0, x1, y1, nm in b.strips:
        _band(p, x0, y0, x1, y1, "W4 ABOVE — SEE A-601" if nm == "W4" else nm)
    for x0, y0, x1, y1, nm in b.pads:
        _band(p, x0, y0, x1, y1, nm, size=4.0)
    # The stairs' own footings come with the stair shop drawings and are not drawn: say
    # so at the foot of each flight, where a reviewer will look for them.
    for x0, y0, x1, y1, nm in b.pads:
        if nm.endswith("STOOP"):
            LAY("S-ANNO-TEXT")
            c.setStrokeColor(black); c.setLineWidth(0.4); c.setFillColor(black); c.setFont("Helvetica", 4.2)
            if abs(x1) < 1e-9:      # Sage-face stoop: label below it, where the sheet has room
                c.line(p.X((x0+x1)/2.0), p.Y(y1), p.X((x0+x1)/2.0), p.Y(y1)-8)
                c.drawCentredString(p.X((x0+x1)/2.0), p.Y(y1)-14, "STAIR FOOTINGS PER STAIR SHOP DRAWINGS, NOTE 5")
            else:                   # courtyard stoop: label above
                c.line(p.X((x0+x1)/2.0), p.Y(y0), p.X((x0+x1)/2.0), p.Y(y0)+10)
                c.drawCentredString(p.X((x0+x1)/2.0), p.Y(y0)+12, "STAIR FOOTINGS PER STAIR SHOP DRAWINGS, NOTE 5")
    _radon(p, b)
    # W4's stud line through its strip; the strip's own label names the wall
    if b is B1:
        LAY("S-FNDN")
        c.setStrokeColor(GREY); c.setLineWidth(0.6); c.setDash(3, 2)
        c.line(p.X(0), p.Y(Y_SEP_TOP), p.X(b.W), p.Y(Y_SEP_TOP))
        c.setDash()
    LAY("S-ANNO-DIMS")
    return p


def _radon(p, b):
    """src/radon.py's risers and laterals under this slab: each lateral dashed through the
       sleeve cast in its strip, each riser's tee a ringed dot with its mark."""
    cc = p.c
    for r in [r for r in RN.RISERS if r.building == b.name]:
        LAY("S-FNDN-RADN")
        for l in r.laterals:
            cc.setStrokeColor(black); cc.setLineWidth(1.0); cc.setDash(4, 2)
            pts = [(p.X(x), p.Y(y)) for x, y in l.path]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cc.line(x0, y0, x1, y1)
            cc.setDash()
            sx0, sy0, sx1, sy1 = [st for st in b.strips if st[4] == l.strip][0][:4]
            for (ax, ay), (bx, by) in zip(l.path, l.path[1:]):
                h = RN.SLEEVE/2.0
                if abs(ay-by) < 1e-9 and min(ax, bx) < sx0 and max(ax, bx) > sx1:       # along x through the strip
                    cc.setLineWidth(0.6); cc.setFillColor(white)
                    cc.rect(p.X(sx0), p.Y(ay+h), (sx1-sx0)*p.sc, 2*h*p.sc, fill=1, stroke=1)
                    cc.setLineWidth(1.0); cc.setDash(4, 2); cc.line(p.X(sx0), p.Y(ay), p.X(sx1), p.Y(ay)); cc.setDash()
                if abs(ax-bx) < 1e-9 and min(ay, by) < sy0 and max(ay, by) > sy1:       # along y through the strip
                    cc.setLineWidth(0.6); cc.setFillColor(white)
                    cc.rect(p.X(ax-h), p.Y(sy1), 2*h*p.sc, (sy1-sy0)*p.sc, fill=1, stroke=1)
                    cc.setLineWidth(1.0); cc.setDash(4, 2); cc.line(p.X(ax), p.Y(sy0), p.X(ax), p.Y(sy1)); cc.setDash()
            ex, ey = pts[-1]
            cc.setLineWidth(0.8); cc.circle(ex, ey, 1.6, fill=0, stroke=1)                  # the open end
            (ax, ay), (bx, by) = l.path[-2], l.path[-1]
            LAY("S-ANNO-TEXT"); cc.setFillColor(black); cc.setFont("Helvetica", 4.2)
            if abs(ax-bx) < 1e-9:
                cc.drawString(ex+4, ey+(3 if by < ay else -5), "%s\" LATERAL, OPEN END, NOTE 10" % RN.PIPE)
                cc.drawString(ex+4, ey+(3 if by < ay else -5)-5, "%s SLEEVE IN THE STRIP" % inches(RN.SLEEVE))
            else:
                cc.drawString(ex-2, ey+4, "%s\" LATERAL, OPEN END, NOTE 10" % RN.PIPE)
                cc.drawString(ex-2, ey-7, "%s SLEEVE IN THE STRIP" % inches(RN.SLEEVE))
            LAY("S-FNDN-RADN")
        X, Y = p.X(r.pos[0]), p.Y(r.pos[1])
        cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.8)
        cc.circle(X, Y, 3.4, fill=1, stroke=1)
        cc.setFillColor(black); cc.circle(X, Y, 1.3, fill=1, stroke=0)
        # the mark on the side no lateral leaves from
        east = any(l.path[1][0] > r.pos[0]+1e-9 for l in r.laterals)
        put = cc.drawRightString if east else cc.drawString
        tx = X-5 if east else X+5
        LAY("S-ANNO-TEXT"); cc.setFont("Helvetica-Bold", 4.6)
        put(tx, Y+2, "%s RADON RISER, NOTE 10" % r.mark)
        cc.setFont("Helvetica", 4.2)
        put(tx, Y-4, "%s\" TEE IN THE AGGREGATE, %s BESIDE STACK %s" % (RN.PIPE, inches(RN.RISER_OFF), r.stack))
    cc.setDash(); cc.setStrokeColor(black); cc.setFillColor(black)
    LAY("S-FNDN")


def _dims(p, b):
    """Overall both ways; each strip and pad located from the nearest corner.

    Strings above the plan take one row each, pads nearest the plan, then the strips,
    then the overall — two strings from the same corner on one row read as one."""
    p.dim(0, b.D, 'v', b.W+2.4)
    row = 3.6                                            # feet above the front face
    for x0, y0, x1, y1, nm in b.pads:
        if abs(y1) < 1e-9:                               # on the front / courtyard face: locate from Sage
            if x0 > 1e-9:
                p.dim(0, x0, 'h', -row); row += 1.0
        elif abs(x1) < 1e-9:                             # on the Sage face
            if y1 > b.D+1e-9: p.dim(b.D, y1, 'v', -4.0)     # the Unit 3 stoop passes the rear wall
            else:             p.dim(0, y0, 'v', -4.0)
    for x0, y0, x1, y1, nm in b.strips:
        if abs(x1-x0-(b.W)) < 1e-9:                     # full-width, horizontal: locate its centre from the front
            p.dim(0, (y0+y1)/2.0, 'v', b.W+1.2)
        else:                                            # vertical: centre from Sage; its run beside the
            cx = (x0+x1)/2.0                             # nearer side, clear of the pads on the Sage face
            p.dim(0, cx, 'h', -row); row += 1.0
            p.dim(y0, y1, 'v', -1.2 if cx < b.W/2.0 else b.W+1.2)
    p.dim(0, b.W, 'h', -row)


def _wall_detail(ox, oy):
    """TYPICAL FOUNDATION WALL, 3/4" = 1'-0": footing, wall, slab, insulation inside, plate.
       (ox, oy) is the sheet point of the wall's outside face at finished grade."""
    sc = 54.0
    Xp = lambda v: ox+v*sc; Yp = lambda v: oy+v*sc
    gr, st = levels.GRADE, levels.SLAB_TOP
    bot, ftop = -FROST_DEPTH, -(FROST_DEPTH-FTG_T)
    LAY("S-DETL")
    c.setStrokeColor(black); c.setLineWidth(1.0); c.setFillColor(white)
    c.rect(Xp(-FTG_PROJ), Yp(bot), FTG_W*sc, FTG_T*sc, fill=1, stroke=1)          # footing
    c.rect(Xp(0), Yp(ftop), WALL_T*sc, (st-ftop)*sc, fill=1, stroke=1)           # wall to slab top
    c.rect(Xp(WALL_T+INSUL_T), Yp(st-SLAB_T), 2.0*sc, SLAB_T*sc, fill=1, stroke=1)  # slab, inside the insulation
    # insulation on the interior face, slab top down the run
    c.setFillColor(GREY)
    c.rect(Xp(WALL_T), Yp(st-EDGE_INSUL_RUN), INSUL_T*sc, EDGE_INSUL_RUN*sc, fill=1, stroke=1)
    # the two bottom bars at their cover to earth. The dot is schematic -- 2 pt is a
    # wider bar than a #4 at this scale -- and sits ON the cover line, not a half
    # diameter above it, which is where the model puts the bar's underside.
    c.setFillColor(black)
    for _bx in (-FTG_PROJ+BAR_COVER, WALL_T+FTG_PROJ-BAR_COVER):
        c.circle(Xp(_bx), Yp(bot+BAR_COVER), 2.0, fill=1, stroke=0)
    # plate and anchor bolt, grade line
    c.setFillColor(white); c.rect(Xp(WALL_T-5.5/12.0), Yp(st), (5.5/12.0)*sc, (1.5/12.0)*sc, fill=1, stroke=1)
    c.setLineWidth(0.9); c.line(Xp(WALL_T/2.0), Yp(st+1.5/12.0), Xp(WALL_T/2.0), Yp(st-7.0/12.0))
    c.setLineWidth(1.6); c.line(Xp(-1.0), Yp(gr), Xp(0), Yp(gr))
    # labels
    c.setFillColor(black); c.setFont("Helvetica", 5.6)
    L = [(Xp(WALL_T+INSUL_T+0.05), Yp(st)-3, "%s SLAB, A-601 S1 — TOP +%s" % (inches(SLAB_T), fmt(st))),
         (Xp(WALL_T+INSUL_T+0.05), Yp(st-EDGE_INSUL_RUN)+2, "%s %s, R-%d, INTERIOR FACE, SLAB TOP DOWN %s — TABLE 1102.1.2" % (inches(INSUL_T), INSUL_NAME, int(INSUL_R_NOM), fmt(EDGE_INSUL_RUN))),
         (Xp(WALL_T+FTG_PROJ)+4, Yp(ftop)+3, "%s POURED CONCRETE WALL, RCO 404" % inches(WALL_T)),
         (Xp(WALL_T+FTG_PROJ)+4, Yp(bot)+10, "%s x %s FOOTING, BOTTOM %s BELOW FINISHED GRADE — CIC-09, 403.1.4.1" % (inches(FTG_W), inches(FTG_T), inches(FROST_DEPTH))),
         (Xp(WALL_T+FTG_PROJ)+4, Yp(bot)+2, "2-%s CONT. AT THE BOTTOM, %s CLEAR TO EARTH; ON UNDISTURBED SOIL" % (FTG_BAR, inches(BAR_COVER))),
         (Xp(-1.0), Yp(gr)+3, "FIN. GRADE 0'-0\""),
         (Xp(-1.0), Yp(st)+12, "TREATED 2x6 SILL, 1/2\" A.B. @ 6'-0\" O.C., 7\" EMBEDMENT, 3-1/2\" TO 12\" FROM PLATE ENDS")]
    for x, y, t in L:
        c.drawString(x, y, t)
    c.setFont("Helvetica-Bold", 8.0); c.drawString(Xp(-1.0), Yp(bot)-13, "TYPICAL FOUNDATION WALL")
    c.setFont("Helvetica", 6.4); c.drawString(Xp(-1.0), Yp(bot)-22, "SCALE: 3/4\" = 1'-0\"")
    # What sits beside the detail needs its extent: the right end of its widest label, its
    # highest label's baseline and its scale line's.
    right = max(x+pdfmetrics.stringWidth(t, "Helvetica", 5.6) for x, _y, t in L)
    return right, max(y for _x, y, _t in L), Yp(bot)-22


def _concrete_schedule(x, x1, ytop, ylow):
    """RCO Table 402.2, as src/foundation.py specifies it: one row per element, its
       strength and air, then the footnotes it relies on. Drawn between x and x1 from
       ytop down, and held above ylow, the wall detail's scale line."""
    W = x1-x
    LAY("S-ANNO-TEXT")
    c.setFillColor(black); c.setStrokeColor(black)
    c.setFont("Helvetica-Bold", 7.0); c.drawString(x, ytop, "CONCRETE — RCO TABLE 402.2")
    c.setLineWidth(0.6); c.line(x, ytop-3, x1, ytop-3)
    y = ytop-11
    c.setFont("Helvetica", 5.6); c.drawString(x, y, "28-DAY STRENGTH, %s WEATHERING (G-001)" % WEATHERING)
    y -= 9
    for e in CONCRETE:
        right = "%s, %s" % (psi(e.psi), "AIR-ENTRAINED" if e.air == "AE" else "NOTE c")
        assert pdfmetrics.stringWidth(e.element, "Helvetica-Bold", 5.6)+pdfmetrics.stringWidth(right, "Helvetica", 5.6)+6 <= W, \
            "S-101 concrete schedule row overruns: %r" % e.element
        c.setFont("Helvetica-Bold", 5.6); c.drawString(x, y, e.element)
        c.setFont("Helvetica", 5.6); c.drawRightString(x1, y, right)
        y -= 8
    notes = [
        "AIR-ENTRAINED: %d%% TO %d%% TOTAL AIR BY VOLUME, TABLE 402.2 NOTE d." % (round(AIR_MIN*100), round(AIR_MAX*100)),
        "NOTE c: AIR-ENTRAIN WHERE THE CONCRETE IS SUBJECT TO FREEZING AND THAWING DURING CONSTRUCTION.",
        "STOOPS AND LANDINGS, NOTE 5 AND C-101; WALKS AND PARKING PAD, C-101; GUTTERS G-1 TO G-3, C-103. IN THE "
        "%s MIX, FLY ASH, OTHER POZZOLANS, SILICA FUME, SLAG AND BLENDED CEMENTS NOT OVER THE LIMITS OF %s, "
        "RCO 402.2." % (psi(FLATWORK.psi), ACI_DEICING),
    ]
    y -= 2
    c.setFont("Helvetica", 5.2)
    for n in notes:
        line = ""
        for word in n.split(" "):
            trial = (line+" "+word).strip()
            if line and pdfmetrics.stringWidth(trial, "Helvetica", 5.2) > W:
                c.drawString(x, y, line); y -= 7; line = word
            else:
                line = trial
        c.drawString(x, y, line); y -= 7
    assert y+7 >= ylow, "S-101 concrete schedule runs below the wall detail by %.2f in" % ((ylow-y-7)/inch)
    LAY("S-DETL")       # the layer the detail left current: the next sheet's frame draws on it


def sheet_s101():
    sh = Sheet(c, "S-101", "Foundation plans", "1/4\" = 1'-0\""); sh.frame()
    # check_foundation() has already run, from build.check_model(); not repeated here.
    top = Y1-1.9*inch
    # Building 1 at the left, Building 2 to its right, same top.
    p1 = _plan(B1, X0+1.1*inch, top-B1.D*Q); _dims(p1, B1)
    p2 = _plan(B2, X0+1.1*inch+B1.W*Q+2.3*inch, top-B2.D*Q); _dims(p2, B2)
    c.setFillColor(black)
    for p, b in ((p1, B1), (p2, B2)):
        c.setFont("Helvetica-Bold", 12); c.drawString(p.ox, p.oy-1.05*inch, "%s — FOUNDATION PLAN" % b.name)
        c.setFont("Helvetica", 9);       c.drawString(p.ox, p.oy-1.23*inch, "SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(p.ox, p.oy-0.78*inch, p.ox+2.6*inch, p.oy-0.78*inch)
    # Termite protection under the Building 1 plan's title and scale, the sheet's empty
    # lower left, as wide as the gap to Building 2's column; the notes column is full.
    tx, ty = p1.ox, p1.oy-1.48*inch
    TW = p2.ox-0.3*inch-tx
    c.setFillColor(black); c.setFont("Helvetica-Bold", 8.0); c.drawString(tx, ty, "TERMITE PROTECTION — RCO 318")
    c.setLineWidth(0.7); c.line(tx, ty-4, tx+TW, ty-4); ty -= 0.18*inch
    c.setFont("Helvetica", TERMITE_SIZE)
    TERMITE_LINES = termite_notes(TW)
    _last = ty-(len(TERMITE_LINES)-1)*TERMITE_LEAD
    assert _last >= Y0, "S-101 termite block runs off the sheet by %.2f in" % ((Y0-_last)/inch)
    for t in TERMITE_LINES:
        c.drawString(tx, ty, t); ty -= TERMITE_LEAD
    # Notes under Building 2, the full width to the title block; the detail under them.
    nx, ny = p2.ox, p2.oy-1.55*inch
    NW = X1-0.2*inch-nx
    c.setFillColor(black); c.setFont("Helvetica-Bold", 9.5); c.drawString(nx, ny, "FOUNDATION NOTES")
    c.setLineWidth(0.7); c.line(nx, ny-4, nx+NW, ny-4); ny -= 0.22*inch
    c.setFont("Helvetica", 6.6)
    _SE = entry_for(_dr.BUILDING_1, _dr.GROUND)
    NOTES = [
     f"1.  FOUNDATION — {inches(FTG_W)} x {inches(FTG_T)} CONTINUOUS CONCRETE FOOTING, BOTTOM {inches(FROST_DEPTH)} MINIMUM BELOW FINISHED GRADE, COLUMBUS CIC-09 AND RCO",
     f"     403.1.4.1, ON UNDISTURBED SOIL; {inches(WALL_T)} POURED CONCRETE FOUNDATION WALL ON IT, RCO 404, TOP AT SLAB TOP. TWO {FTG_BAR} CONTINUOUS IN THE",
     f"     FOOTING, {inches(BAR_COVER)} CLEAR TO EARTH. RCO TABLE 403.1(1), TWO-STORY, {crit.psf(crit.SOIL_BEARING)}.",
     f"2.  SLAB — {inches(SLAB_T)} {psi(SLAB.psi)} CONCRETE, 6x6 W1.4 WWM OR FIBERS, {RETARDER_MIL}-MIL VAPOR RETARDER, {inches(GRAVEL_T)} CLEAN AGGREGATE, NOTE 10, POURED INSIDE",
     "     THE WALL. A-601 S1.",
     f"3.  SLAB-EDGE INSULATION — {inches(INSUL_T)} {INSUL_NAME}, R-{int(INSUL_R_NOM)} NOMINAL, ON THE INTERIOR FACE OF THE FOUNDATION WALL FROM SLAB TOP",
     f"     DOWN {fmt(EDGE_INSUL_RUN)}, RCO TABLE 1102.1.2 (R-{ENERGY_R}, 2 FT). NONE IS EXPOSED AND NONE LIES UNDER CONCRETE.",
     f"4.  INTERIOR BEARING STRIPS — {inches(STRIP_W)} x {inches(STRIP_D)} THICKENED IN THE SLAB UNDER W4, UNDER THE UNITS 2 AND 3 AND UNITS 4 AND 5 BEARING WALLS (S-102)",
     f"     AND UNDER THE UNIT 1 STAIR WALL. TWO {FTG_BAR} CONTINUOUS AT THE BOTTOM, {inches(BAR_COVER)} CLEAR.",
     f"5.  PADS — FLOATING, {inches(PAD_T)} THICK WITH A {inches(PAD_EDGE)} THICKENED EDGE, 1/2\" EXPANSION JOINT AT THE BUILDING, TOPS PER C-101 NOTE 5a.",
     f"     THE STRINGERS OF THE UNIT 3 AND UNIT 5 STAIRS BEAR ON THEIR OWN FOOTINGS, BOTTOM {inches(FROST_DEPTH)} MINIMUM BELOW FINISHED",
     "     GRADE LIKE THE BUILDING'S, RCO 403.1.4.1 AND CIC-09, LOCATED AND SIZED PER THE APPROVED STAIR SHOP DRAWINGS, A-001",
     "     NOTES 13a AND 13b; NOT DRAWN HERE.",
     "6.  ANCHOR BOLTS — 1/2\" DIAMETER, 7\" EMBEDMENT, 6'-0\" O.C. MAXIMUM, AT LEAST TWO PER PLATE, AND FROM EACH PLATE END NOT MORE THAN 12\"",
     "     NOR LESS THAN 3-1/2\" (SEVEN BOLT DIAMETERS), RCO 403.1.6. SILL PLATES PRESERVATIVE TREATED, 317.1.",
     f"7.  DRAINAGE — FINISHED GRADING PER C-103, RCO 401.3: {inches(FALL)} OF FALL WITHIN {fmt(FALL_RUN)} WHERE {fmt(FALL_RUN)} HORIZONTAL DISTANCE IS AVAILABLE, THE WHOLE",
     f"     {inches(FALL)} TO THE LOT LINE ON THE SAGE FACES, AND {inches(FALL)} TO A CONCRETE GUTTER UNDER THE 401.3 EXCEPTION ON THE ADJACENT-",
     f"     PARCEL FACES AND BETWEEN THE BUILDINGS; PAVING {int(round(100*IMPERVIOUS_MIN))}% AWAY. NO FOUNDATION DRAIN: THE WALLS RETAIN NO EARTH",
     "     AGAINST HABITABLE SPACE, 405.1.",
     "8.  UNDER-SLAB PLUMBING — THE BUILDING DRAINS, THEIR BRANCHES, EVERY SLAB PENETRATION, THE SLEEVES THROUGH THE WALL AND THE INVERTS",
     "     PER P-101; THE WATER SERVICES AND THE UNITS 2 / 3 TRUNK PER P-102 AND P-103. NO PLUMBING UNDER THE SLAB IS DRAWN HERE.",
     f"     EACH WATER SERVICE PASSES THROUGH THIS FOOTING IN A SLEEVE, NOT THROUGH THE WALL: THICKEN IT TO {inches(_SE.thick)} AT THE CROSSING ON UNDISTURBED SOIL, RCO 403.1.5 — SEE P-601.",
     f"9.  BEARING — {crit.psf(crit.SOIL_BEARING)} PRESUMED (G-001). VERIFY AT EXCAVATION. NO FOOTING ON FROZEN, ORGANIC OR DISTURBED SOIL.",
     f"10. RADON — PASSIVE SUB-SLAB RISERS {RN.RISERS[0].mark} TO {RN.RISERS[-1].mark} AND THEIR LATERALS, DRAWN; A {inches(RN.SLEEVE)} SLEEVE CAST IN THE STRIP AT EACH",
     "     LATERAL, ABOVE THE BARS. THE AGGREGATE, RETARDER, SEALING, RISERS AND ROOF EXITS PER S-103 RADON NOTES.",
    ]
    NOTE_LEAD = 0.1035*inch
    over = [t for t in NOTES if pdfmetrics.stringWidth(t, "Helvetica", 6.6) > NW]
    assert not over, "S-101 note line overruns its column: %r" % over[:1]
    for t in NOTES:
        c.drawString(nx, ny, t); ny -= NOTE_LEAD
    # The detail: its grade datum sits 0.55 in under the last note line (its highest
    # label is 0.5 in above that datum); its lowest line, the scale under the footing,
    # is derived from the model's frost depth and held above the drawing area.
    # the slab stands 8" out of grade: the sill's label is that much higher over the detail's datum,
    # and used to print on the last note line (lib/verify/sheet_text.py found it)
    _dy = ny-0.55*inch-(levels.SLAB_TOP-levels.GRADE)*54.0+0.12*inch
    _low = _dy-FROST_DEPTH*54.0-22
    assert _low >= Y0, "S-101 wall detail runs off the sheet by %.2f in" % ((Y0-_low)/inch)
    _right, _top, _scale = _wall_detail(nx+1.1*inch, _dy)
    # The concrete schedule stands right of the detail, clear of its widest label, and ends
    # above its scale line: it takes no height from the notes column.
    _concrete_schedule(_right+0.3*inch, nx+NW, _top, _scale)
    c.showPage()

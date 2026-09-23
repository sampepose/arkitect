"""S-101 — foundation plans of both buildings: trench footing, foundation wall, slab.

Draws src/foundation.py and nothing it does not hold. The plans are in final sheet
coordinates already (see that module), so PlanDraw takes them straight: no mirror.
"""
from arkitect.lib.draw.page import GREY, LAY, Sheet
from arkitect.lib.draw.plan import PlanDraw
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import radon as RN
from arkitect.codes.ohio.opc_service_entry import entry_for
from src import criteria as crit
from src import drainage as _dr
from src import levels
from arkitect.lib.draw.text import wrap_notes
from src.foundation import (B1, B2, BAR_COVER, CONCRETE, EDGE_INSUL_RUN, ENERGY_R, FLATWORK, FTG_BAR, PIER_DIA, POST_IN,
                            FROST_DEPTH, GRAVEL_T, RETARDER_MIL, FTG_PROJ, FTG_T, FTG_W, INSUL_NAME,
                            INSUL_R_NOM, INSUL_T, PAD_EDGE, PAD_T, SLAB, SLAB_T, STRIP_D, STRIP_W, TERMITE,
                            TERMITE_METHOD, TERMITE_METHODS, TERMITE_TREATMENT, WALL_T, WEATHERING)
from arkitect.codes.ohio.rco.concrete import ACI_DEICING, AIR_MAX, AIR_MIN, psi
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c
from arkitect.lib.draw.foundation_kit import _band

TERMITE_SIZE = 6.6
TERMITE_LEAD = 0.112*inch


def termite_notes(width):
    """The TERMITE PROTECTION block, RCO 318, re-set to the width under the Building 1 plan.
       It cites the foundation notes by number and adds none of its own."""
    return wrap_notes([
     "T1. TABLE 301.2(1) READS %s. PROTECT BOTH BUILDINGS BY RCO 318.1 ITEM %d, %s, AS %s."
     % (TERMITE, TERMITE_METHOD, TERMITE_METHODS[TERMITE_METHOD], TERMITE_TREATMENT),
     "T2. APPLICATOR — A COMMERCIAL PESTICIDE APPLICATOR LICENSED BY THE OHIO DEPARTMENT OF AGRICULTURE FOR TERMITE CONTROL. TERMITICIDE,"
     " CONCENTRATION, RATE OF APPLICATION AND METHOD OF TREATMENT IN STRICT ACCORDANCE WITH THE TERMITICIDE LABEL, 318.2.",
     "T3. SEQUENCE — UNDER EACH SLAB AND BEARING STRIP, NOTES 2 AND 4, ONCE THE GRAVEL IS COMPACTED AND THE UNDER-SLAB PIPING OF NOTE 8 IS"
     " TESTED AND BACKFILLED, BEFORE THE VAPOR RETARDER IS LAID; AROUND EVERY SLAB PENETRATION; UNDER EACH PAD, NOTE 5, BEFORE IT IS"
     " POURED; ALONG THE OUTSIDE FACE OF THE FOUNDATION WALL AFTER FINISHED GRADING, NOTE 7. RETREAT SOIL DISTURBED AFTER TREATMENT BEFORE"
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
        _band(p, x0, y0, x1, y1, nm)
    for x0, y0, x1, y1, nm in b.pads:
        _band(p, x0, y0, x1, y1, nm, size=4.0)
    # The Unit 3 stair's piers: below grade, so dashed, each with its mark.
    for x, y, d, mk in b.piers:
        LAY("S-FNDN")
        c.setStrokeColor(black); c.setLineWidth(0.8); c.setDash(3, 2); c.setFillColor(white)
        c.circle(p.X(x), p.Y(y), d/2.0*Q, fill=0, stroke=1)
        c.setDash()
        c.setLineWidth(0.5); c.line(p.X(x)-2, p.Y(y), p.X(x)+2, p.Y(y)); c.line(p.X(x), p.Y(y)-2, p.X(x), p.Y(y)+2)
        LAY("S-ANNO-TEXT"); c.setFillColor(black); c.setFont("Helvetica-Bold", 5.0)
        c.drawString(p.X(x)+d/2.0*Q+1.5, p.Y(y)+1.5, mk)
    _radon(p, b)
    _thickened(p, b)
    LAY("S-ANNO-DIMS")
    return p


HATCH = 0.5                                        # feet between the thickened footing's hatch lines


def _thickened(p, b):
    """The footing thickened for the water service, P-601 details 1 and 2: hatched over the
       footing's width along its centreline, around a corner where the return reaches one,
       the crossing ticked and located, and a label saying what and how long."""
    db = next(x for x in _dr.BUILDINGS if x.name == b.name)
    z = _dr.thickened_footing(db)
    cc = p.c
    LAY("S-FNDN")
    cc.setStrokeColor(black); cc.setLineWidth(0.35)
    h = FTG_W/2.0
    pts = z.path
    for i, (a, bb) in enumerate(zip(pts, pts[1:])):
        # each leg reaches past a corner it turns by half the footing, so the corner square is hatched once
        ext0 = h if i > 0 else 0.0
        ext1 = h if i < len(pts)-2 else 0.0
        if abs(a[1]-bb[1]) < 1e-9:                                     # along x
            x0, x1 = sorted((a[0], bb[0])); x0 -= ext0 if a[0] < bb[0] else ext1; x1 += ext1 if a[0] < bb[0] else ext0
            y0, y1 = a[1]-h, a[1]+h
        else:                                                          # along y
            y0, y1 = sorted((a[1], bb[1])); y0 -= ext0 if a[1] < bb[1] else ext1; y1 += ext1 if a[1] < bb[1] else ext0
            x0, x1 = a[0]-h, a[0]+h
        if i > 0:
            if abs(a[1]-bb[1]) < 1e-9: x0, x1 = (max(x0, a[0]+h), x1) if bb[0] > a[0] else (x0, min(x1, a[0]-h))
            else: y0, y1 = (max(y0, a[1]+h), y1) if bb[1] > a[1] else (y0, min(y1, a[1]-h))
        # 45-degree hatch clipped to the rectangle by arithmetic: lines x - y = k
        k = x0-y1
        while k < x1-y0:
            ax, ay = max(x0, y0+k), max(x0, y0+k)-k
            bx, by = min(x1, y1+k), min(x1, y1+k)-k
            if bx > ax:
                cc.line(p.X(ax), p.Y(ay), p.X(bx), p.Y(by))
            k += HATCH
        cc.setLineWidth(0.7); cc.rect(p.X(x0), p.Y(y1), (x1-x0)*p.sc, (y1-y0)*p.sc, fill=0, stroke=1); cc.setLineWidth(0.35)
    # the crossing: a heavy tick across the footing
    (cx, cy) = z.crossing
    cc.setLineWidth(1.4)
    leg = next((a, bb) for a, bb in zip(pts, pts[1:])
               if min(a[0], bb[0])-1e-9 <= cx <= max(a[0], bb[0])+1e-9 and min(a[1], bb[1])-1e-9 <= cy <= max(a[1], bb[1])+1e-9)
    if abs(leg[0][0]-leg[1][0]) < 1e-9:                # a leg along y: the tick runs across it in x
        cc.line(p.X(cx-h-0.3), p.Y(cy), p.X(cx+h+0.3), p.Y(cy))
    else:
        cc.line(p.X(cx), p.Y(cy-h-0.3), p.X(cx), p.Y(cy+h+0.3))
    cc.setLineWidth(0.5)
    LAY("S-ANNO-TEXT"); cc.setFillColor(black)
    lx, ly = p.X(cx+h+0.6), p.Y(cy)
    cc.setFont("Helvetica-Bold", 4.6)
    cc.drawString(lx, ly+2, "WATER SERVICE THROUGH THE FOOTING, P-601 DETAIL 1")
    cc.setFont("Helvetica", 4.2)
    e = entry_for(db, _dr.GROUND)
    what = ("THICKENED %s, BOTTOM %s LOWER AT THE CROSSING, RETURNING 1 IN 10 OVER %s EACH SIDE"
            % (inches(e.thick), inches(e.drop), fmt(e.run)))
    cc.drawString(lx, ly-4, what)
    cc.drawString(lx, ly-9, ("ON THE FOOTING CENTERLINE, AROUND THE CORNER %s — HATCHED; NOTE 8, P-601 DETAIL 2"
                             % fmt(min(z.legs[0], z.legs[-1]))) if z.corners else
                  "ON THE FOOTING CENTERLINE — HATCHED; NOTE 8, P-601 DETAIL 2")
    cc.setStrokeColor(black)
    # the crossing located from the nearer end of its wall, on the outside, clear of the strips' strings
    vert = abs(leg[0][0]-leg[1][0]) < 1e-9
    near = b.D if vert and cy > b.D/2.0 else (0.0 if vert else (b.W if cx > b.W/2.0 else 0.0))
    if vert:
        p.dim(min(cy, near), max(cy, near), 'v', -1.2 if cx < b.W/2.0 else b.W+1.2)
    else:
        p.dim(min(cx, near), max(cx, near), 'h', -1.2 if cy < b.D/2.0 else b.D+1.2)


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
                cc.drawString(ex+4, ey+(3 if by < ay else -5), "%s\" LATERAL, OPEN END, S-103 R5" % RN.PIPE)
                cc.drawString(ex+4, ey+(3 if by < ay else -5)-5, "%s SLEEVE IN THE STRIP" % inches(RN.SLEEVE))
            else:
                cc.drawString(ex-2, ey+4, "%s\" LATERAL, OPEN END, S-103 R5" % RN.PIPE)
                cc.drawString(ex-2, ey-7, "%s SLEEVE IN THE STRIP" % inches(RN.SLEEVE))
            LAY("S-FNDN-RADN")
        X, Y = p.X(r.pos[0]), p.Y(r.pos[1])
        cc.setStrokeColor(black); cc.setFillColor(white); cc.setLineWidth(0.8)
        cc.circle(X, Y, 3.4, fill=1, stroke=1)
        cc.setFillColor(black); cc.circle(X, Y, 1.3, fill=1, stroke=0)
        east = r.pos[0] > b.W/2.0                          # the mark toward the middle of the plan
        put = cc.drawRightString if east else cc.drawString
        tx = X-5 if east else X+5
        LAY("S-ANNO-TEXT"); cc.setFont("Helvetica-Bold", 4.6)
        put(tx, Y+2, "%s RADON RISER, S-103 RADON NOTES" % r.mark)
        cc.setFont("Helvetica", 4.2)
        put(tx, Y-4, "%s\" TEE IN THE AGGREGATE, UNDER THE %s" % (RN.PIPE, r.where))
    cc.setDash(); cc.setStrokeColor(black); cc.setFillColor(black)
    LAY("S-FNDN")


def _dims(p, b):
    """Overall both ways; each strip and pad located from the nearest corner.

    Strings above the plan take one row each, pads nearest the plan, then the strips,
    then the overall — two strings from the same corner on one row read as one."""
    p.dim(0, b.D, 'v', b.W+2.4)
    row = 4.3                                            # feet above the front face, clear of the stair piers
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
    # the two #4 bars at the bottom of the footing, 3" clear to earth
    c.setFillColor(black)
    for _bx in (-FTG_PROJ+BAR_COVER, WALL_T+FTG_PROJ-BAR_COVER):
        c.circle(Xp(_bx), Yp(bot+BAR_COVER), 2.0, fill=1, stroke=0)
    # plate and anchor bolt, grade line
    c.setFillColor(white); c.rect(Xp(WALL_T-5.5/12.0), Yp(st), (5.5/12.0)*sc, (1.5/12.0)*sc, fill=1, stroke=1)
    c.setLineWidth(0.9); c.line(Xp(WALL_T/2.0), Yp(st+1.5/12.0), Xp(WALL_T/2.0), Yp(st-7.0/12.0))
    c.setLineWidth(1.6); c.line(Xp(-1.0), Yp(gr), Xp(0), Yp(gr))
    # labels
    c.setFillColor(black); c.setFont("Helvetica", 5.6)
    L = [(Xp(WALL_T+INSUL_T+0.05), Yp(st)-11, "%s SLAB, NOTE 2 — TOP +%s" % (inches(SLAB_T), fmt(st))),
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
    c.setFont("Helvetica", 5.6); c.drawString(x, y, "28-DAY STRENGTH, %s WEATHERING, TABLE 301.2(1)" % WEATHERING)
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
        "STOOPS AND LANDINGS, NOTE 5. IN THE "
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
    top = Y1-1.6*inch
    # Building 1 at the left, Building 2 to its right, same top.
    p1 = _plan(B1, X0+1.1*inch, top-B1.D*Q); _dims(p1, B1)
    p2 = _plan(B2, X0+1.1*inch+B1.W*Q+2.3*inch, top-B2.D*Q); _dims(p2, B2)
    c.setFillColor(black)
    # a pad that stands out past the rear wall (Unit 1's rear landing) pushes its plan's title down
    drop = {b.name: max([0.0]+[y1-b.D for _x0, _y0, _x1, y1, _nm in b.pads])*Q for b in (B1, B2)}
    for p, b in ((p1, B1), (p2, B2)):
        ty0 = p.oy-drop[b.name]
        c.setFont("Helvetica-Bold", 12); c.drawString(p.ox, ty0-0.85*inch, "%s — FOUNDATION PLAN" % b.name)
        c.setFont("Helvetica", 9);       c.drawString(p.ox, ty0-1.03*inch, "SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(p.ox, ty0-0.58*inch, p.ox+2.6*inch, ty0-0.58*inch)
    # Termite protection under the Building 1 plan's title and scale, the sheet's empty
    # lower left, as wide as the gap to Building 2's column; the notes column is full.
    tx, ty = p1.ox, p1.oy-drop[B1.name]-1.28*inch
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
    nx, ny = p2.ox, p2.oy-1.20*inch
    NW = X1-0.2*inch-nx
    c.setFillColor(black); c.setFont("Helvetica-Bold", 9.5); c.drawString(nx, ny, "FOUNDATION NOTES")
    c.setLineWidth(0.7); c.line(nx, ny-4, nx+NW, ny-4); ny -= 0.22*inch
    c.setFont("Helvetica", 6.6)
    _SE = entry_for(_dr.BUILDING_1, _dr.GROUND)
    NOTES = [
     f"1.  FOUNDATION — {inches(FTG_W)} x {inches(FTG_T)} CONTINUOUS CONCRETE FOOTING, BOTTOM {inches(FROST_DEPTH)} MINIMUM BELOW FINISHED GRADE, COLUMBUS CIC-09 AND RCO",
     f"     403.1.4.1, ON UNDISTURBED SOIL; {inches(WALL_T)} POURED CONCRETE FOUNDATION WALL ON IT, RCO 404, TOP AT SLAB TOP. TWO {FTG_BAR} CONTINUOUS IN THE",
     f"     FOOTING, {inches(BAR_COVER)} CLEAR TO EARTH. RCO TABLE 403.1(1), TWO-STORY, {crit.psf(crit.SOIL_BEARING)}.",
     f"2.  SLAB — {inches(SLAB_T)} {psi(SLAB.psi)} CONCRETE, 6x6 W1.4 WWM OR FIBERS, {RETARDER_MIL}-MIL VAPOR RETARDER, {inches(GRAVEL_T)} CLEAN AGGREGATE, POURED INSIDE",
     "     THE WALL.",
     f"3.  SLAB-EDGE INSULATION — {inches(INSUL_T)} {INSUL_NAME}, R-{int(INSUL_R_NOM)} NOMINAL, ON THE INTERIOR FACE OF THE FOUNDATION WALL FROM SLAB TOP",
     f"     DOWN {fmt(EDGE_INSUL_RUN)}, RCO TABLE 1102.1.2 (R-{ENERGY_R}, 2 FT). NONE IS EXPOSED AND NONE LIES UNDER CONCRETE.",
     f"4.  INTERIOR BEARING STRIPS — {inches(STRIP_W)} x {inches(STRIP_D)} THICKENED IN THE SLAB UNDER THE UNIT 1 STAIR WALL, WHICH CARRIES THE TRIMMER AT",
     f"     THE LEVEL 2 WELL (THE LEVEL 2 FLOOR SPANS SIDE WALL TO SIDE WALL), AND UNDER THE UNITS 2 AND 3 BEARING WALL. TWO {FTG_BAR} CONTINUOUS",
     f"     AT THE BOTTOM, {inches(BAR_COVER)} CLEAR.",
     f"5.  PADS — FLOATING, {inches(PAD_T)} THICK WITH A {inches(PAD_EDGE)} THICKENED EDGE, 1/2\" EXPANSION JOINT AT THE BUILDING, TOPS 1/2\" MAX BELOW THE",
     f"     THRESHOLD. UNIT 3 STAIR: LANDING LEDGERED TO BUILDING 2; OUTER POSTS AND STRINGER FEET ON {inches(PIER_DIA)} DIA. PIERS P1 TO P4, BOTTOM",
     f"     {inches(FROST_DEPTH)} BELOW GRADE (403.1.4.1, CIC-09), CENTERED ON THE POSTS {inches(POST_IN)} IN FROM THE STAIR'S EDGES; PADS POURED AROUND THEM, ISOLATED.",
     "6.  ANCHOR BOLTS — 1/2\" DIAMETER, 7\" EMBEDMENT, 6'-0\" O.C. MAXIMUM, AT LEAST TWO PER PLATE, AND FROM EACH PLATE END NOT MORE THAN 12\"",
     "     NOR LESS THAN 3-1/2\" (SEVEN BOLT DIAMETERS), RCO 403.1.6. SILL PLATES PRESERVATIVE TREATED, 317.1.",
     "7.  DRAINAGE — FINISHED GRADING, THE SWALES AND THE ROOF LEADERS PER C-103. NO FOUNDATION DRAIN: THE WALLS RETAIN NO EARTH AGAINST",
     "     HABITABLE SPACE, 405.1.",
     "8.  UNDER-SLAB PLUMBING — BUILDING DRAINS, BRANCHES, SLAB PENETRATIONS AND WALL SLEEVES PER THE PLUMBING SHEETS; NONE IS DRAWN HERE.",
     f"     EACH WATER SUPPLY PASSES THROUGH THIS FOOTING IN A SLEEVE: THICKEN IT TO {inches(_SE.thick)} OVER THE LENGTH HATCHED, AROUND A CORNER WHERE DRAWN, ON UNDISTURBED SOIL, RCO 403.1.5 — P-601.",
     f"9.  BEARING — {crit.psf(crit.SOIL_BEARING)} PRESUMED. VERIFY AT EXCAVATION. NO FOOTING ON FROZEN, ORGANIC OR DISTURBED SOIL.",
    ]
    over = [t for t in NOTES if pdfmetrics.stringWidth(t, "Helvetica", 6.6) > NW]
    assert not over, "S-101 note line overruns its column: %r" % over[:1]
    for t in NOTES:
        c.drawString(nx, ny, t); ny -= 0.102*inch
    # The detail: its grade datum sits 0.50 in under the last note line (its highest
    # label is 0.5 in above that datum, so the two are all but touching -- the sweep in
    # arkitect/lib/verify/sheet_text.py is what proves they do not); its lowest line, the scale
    # under the footing, is derived from the model's frost depth and held above the
    # drawing area. The gap and the 0.102 in note leading above it both came in to buy
    # note 8 the line the water service entry needed.
    # the slab stands 8" out of grade now: the sill's label is that much higher over the datum
    _dy = ny-0.50*inch-(levels.SLAB_TOP-levels.GRADE)*54.0+0.12*inch
    _low = _dy-FROST_DEPTH*54.0-22
    assert _low >= Y0, "S-101 wall detail runs off the sheet by %.2f in" % ((Y0-_low)/inch)
    _right, _top, _scale = _wall_detail(nx+1.1*inch, _dy)
    # The concrete schedule stands right of the detail, clear of its widest label, and ends
    # above its scale line: it takes no height from the notes column.
    _concrete_schedule(_right+0.3*inch, nx+NW, _top, _scale)
    c.showPage()

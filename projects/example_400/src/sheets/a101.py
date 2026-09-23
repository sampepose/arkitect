"""A-101 — Building 1's floor plans: Unit 1, the single-family house, both levels.

Laid out like A-102, with the street at the top of the sheet. The interior stair is drawn
here, over each level's plan, from src/stairs.py's B1_STAIR at the positions
src/building1.py pins it to.
"""
from lib.draw.page import GREY, LAY, Sheet
from lib.draw.sheets import draw_level
from lib.model.regrid import EXT_STUD
from lib.units import fmt, inches
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from lib.model.regrid import PARTITION
from src.building1 import (B1_W, LEVEL, LEVELS, PLAN_B1_L1, PLAN_B1_L2, Y_CL, Y_FOOT_RISER,
                             Y_TOP_RISER, Y_WELL, b1_level)
from src.schedules import door_tags
from src.sheets.common import draw_attic_hatch, draw_door_tags
from lib.draw.kit import Q, X0, Y1, c
from src.stairs import B1_STAIR
from src.mechanical import soffit_clear

# The cut line on Level 1, as a tread count from the foot: treads past it are above the
# cut plane and drawn dashed.
BREAK_TREAD = 7
BREAK_SLOPE = 0.58      # the cut line's fall across the column, plan feet per foot (~30 deg)


def draw_b1_stair(p, level):
    """The house's stair in page feet: a column against the left wall, rising toward the
       front wall — its top riser at Y_TOP_RISER, off the Level 2 landing, and its foot at
       Y_FOOT_RISER, in the kitchen.

       Level 1 cuts the flight: treads from the foot to the cut solid, those above it dashed
       as far as the coat closet under the high end, and the arrow UP from the foot. Level 2
       looks down the well at the flight to the guard wall at its far end, the arrow DN
       from the landing."""
    LAY("A-FLOR-STRS")
    cc = p.c
    x0, x1 = EXT_STUD, EXT_STUD + B1_STAIR.stud_width
    xm = (x0 + x1)/2.0
    risers = [Y_TOP_RISER + i*B1_STAIR.tread for i in range(B1_STAIR.treads + 1)]
    ybreak = Y_FOOT_RISER - (BREAK_TREAD + 0.5)*B1_STAIR.tread
    y_closet = PLAN_B1_L1.y(Y_CL + PARTITION)            # Level 1: the closet's back wall
    y_guard = PLAN_B1_L2.y(Y_WELL - PARTITION)          # Level 2: the guard wall at the far end

    def cut(x):
        """The cut line's plan y at x: a diagonal across the column, about 30 degrees."""
        return ybreak + (x - xm)*BREAK_SLOPE

    def seg(xa, xb, y, dashed):
        if xb - xa < 1e-6:
            return
        if dashed: cc.setStrokeColor(GREY); cc.setDash(3, 2)
        cc.line(p.X(xa), p.Y(y), p.X(xb), p.Y(y))
        if dashed: cc.setDash(); cc.setStrokeColor(black)

    cc.saveState(); cc.setStrokeColor(black); cc.setLineWidth(0.6)
    xr = x0 + 0.25                                        # the handrail, on the wall side
    if level == 1:
        for y in risers:
            if y < y_closet - 1e-6:
                continue
            # solid where the riser is still on the foot's side of the cut (y > cut(x),
            # which is x short of xc since the cut falls toward x1), dashed beyond it
            xc = min(max(xm + (y - ybreak)/BREAK_SLOPE, x0), x1)
            seg(x0, xc, y, False)
            seg(xc, x1, y, True)
        cc.setLineWidth(0.5)
        yc = cut(xr)
        cc.line(p.X(xr), p.Y(Y_FOOT_RISER), p.X(xr), p.Y(yc))
        cc.setStrokeColor(GREY); cc.setDash(3, 2)
        cc.line(p.X(xr), p.Y(yc), p.X(xr), p.Y(y_closet))
        cc.setDash(); cc.setStrokeColor(black)
        # the cut line, with a Z at its middle
        cc.setLineWidth(0.7)
        z, h = 0.22, 0.45
        pts = [(x0, cut(x0)), (xm - z, cut(xm - z)), (xm - z/3, cut(xm) - h),
               (xm + z/3, cut(xm) + h), (xm + z, cut(xm + z)), (x1, cut(x1))]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cc.line(p.X(ax), p.Y(ay), p.X(bx), p.Y(by))
    else:
        for y in risers:
            if y <= y_guard + 1e-6:
                seg(x0, x1, y, False)
        cc.setLineWidth(0.5)
        cc.line(p.X(xr), p.Y(Y_TOP_RISER), p.X(xr), p.Y(y_guard))
    # the direction arrow, down the middle of the column, its head back toward the tail
    xa = xm + 0.35
    ya, yb = ((Y_FOOT_RISER + 1.2, cut(xa) + 0.35) if level == 1
              else (Y_TOP_RISER - 1.2, y_guard - 0.8))
    cc.setLineWidth(0.9)
    cc.line(p.X(xa), p.Y(ya), p.X(xa), p.Y(yb))
    back = 5 if yb > ya else -5                   # page points: plan y runs down the page
    cc.line(p.X(xa), p.Y(yb), p.X(xa) - 3.2, p.Y(yb) + back)
    cc.line(p.X(xa), p.Y(yb), p.X(xa) + 3.2, p.Y(yb) + back)
    cc.setFillColor(black); cc.setFont("Helvetica-Bold", 5.8)
    cc.drawCentredString(p.X(xa), p.Y(ya) + (-8 if level == 1 else 4), "UP" if level == 1 else "DN")
    cc.restoreState()


def stair_line():
    """The stair in one line, from the spec: A-101's note under the plans."""
    s = B1_STAIR
    return ("STAIR: %dR @ %s / %dT @ %s  \u00b7  RUN %s, RISING TO THE FRONT  \u00b7  LANDINGS %s TOP, "
            "%s FOOT  \u00b7  RCO 311.7"
            % (s.risers, inches(s.riser), s.treads, inches(s.tread), fmt(s.run),
               fmt(s.top_landing), fmt(s.foot_landing)))


def sheet_a101():
    sh=Sheet(c,"A-101","Building 1 — floor plans","1/4\" = 1'-0\""); sh.frame()
    for level, oxx in zip(LEVELS, (X0+1.9*inch, X0+11.3*inch)):
        oy=Y1-28*Q-4.30*inch
        lv=b1_level(level)
        lv.over_plan=lambda pp, level=level: draw_b1_stair(pp, level)
        p=draw_level(c,lv,oxx,oy)
        draw_door_tags(p, LEVEL[level]['plan'], B1_W, door_tags(1, level))          # the marks A-602 schedules
        if level == 2:
            from src.roof import B1_ROOF            # the attic hatch S-103 places, RCO 807.1
            for h in B1_ROOF.hatches: draw_attic_hatch(p, h)
        p.note(B1_W/2.0,PLAN_B1_L1.y(-6.6),"OAK AVENUE  ·  25'-0\" FRONT SETBACK",6.6)
        p.note(B1_W/2.0,PLAN_B1_L1.y(35.3),"BUILDING 2 AND THE ALLEY TO THE REAR",6.0)
        p.note(B1_W/2.0,PLAN_B1_L1.y(36.4),"5'-0\" SIDE YARD EACH SIDE",6.0)
        if level == 1:
            p.unitbox(9.5,PLAN_B1_L1.y(9.6),"UNIT 1","3 BR / 2 BA",1.75,0.42)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12)
        c.drawString(oxx,oy-1.50*inch,"LEVEL %d — UNIT 1" % level)
        c.setFont("Helvetica",9); c.drawString(oxx,oy-1.68*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(oxx,oy-1.22*inch,oxx+2.6*inch,oy-1.22*inch)
    c.setFont("Helvetica",8.4); c.setFillColor(black)
    for i,t in enumerate([
            "UNIT 1: SINGLE-FAMILY HOUSE, 3 BR / 2 BA, TWO STORIES.",
            stair_line(),
            "LEVEL 2 LANDING W-A, AT THE HEAD OF THE STAIR: SAFETY GLAZING, RCO 308.4.",
            "EACH HALL CEILING IS A SOFFIT — LEVEL 1 %s, LEVEL 2 %s — HIDING THAT LEVEL'S AIR HANDLER AND ITS DUCTS: M-101."
            % (fmt(soffit_clear(1)), fmt(soffit_clear(2)))]):
        c.drawString(X0,oy-(2.15+0.16*i)*inch,t)
    c.showPage()

"""A-101 — Building 1's floor plans: Unit 1, the single-family house, both levels.

Laid out like A-102, with the street at the top of the sheet. The interior stair is drawn
here, over each level's plan, from src/stairs.py's B1_STAIR at the positions
src/building1.py pins it to.
"""
from arkitect.lib import assets
from arkitect.lib.draw.page import GREY, LAY, Sheet
from arkitect.lib.draw.sheets import draw_level
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from arkitect.lib.model.regrid import PARTITION
from src.building1 import (B1_W, LEVEL, LEVELS, PLAN_B1_L1, PLAN_B1_L2, X_HALL1, Y_CL, Y_FOOT_RISER,
                             Y_TOP_RISER, Y_WELL, b1_level)
from src.schedules import TAG_OFF, door_tags, is_closet
from src.sheets.common import draw_attic_hatch, draw_door_tags, draw_landings, draw_soffit, tag_half_width
from arkitect.lib.draw.kit import Q, X0, Y1, c, knockout
from src.stairs import B1_STAIR
from src.mechanical import soffit_clear
from src.foundation import B1 as B1_FOUNDATION
from src.sheets.site import TURN

# The cut line on Level 1, as a tread count from the foot: treads past it are above the
# cut plane and drawn dashed.
BREAK_TREAD = 7
BREAK_SLOPE = 0.58      # the cut line's fall across the column, plan feet per foot (~30 deg)


def _stair_window_mark(p):
    """The page-point box (x0, y0, x1, y1) of W-D's mark, the window over the well, as
       PlanDraw.window() sets a mark beside a window in a side wall: the regridded opening,
       mirrored, the mark 2 pt in from the wall's middle and on the opening's centerline.
       The flight is drawn over the plan, so its lines are broken there."""
    w = next(w for w in LEVEL[2]['wins'] if w[4] == "D")
    x, y, ln = PLAN_B1_L2.span(w)[:3]
    x = B1_W-x                                          # the sheet mirror, a window in a side wall
    t = x if x < B1_W/2.0 else B1_W-x                   # the wall's thickness to the face
    cx = t/2.0 if x < B1_W/2.0 else B1_W-t/2.0
    X0 = p.X(cx)+t*p.sc/2.0+2
    Yb = p.Y(y+ln/2.0)
    pad = 1.2
    return (X0-pad, Yb-1.5-pad, X0+c.stringWidth("W-"+w[4], "Helvetica", 5.2)+pad, Yb+5.2*0.72+pad)


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
        bx0, by0, bx1, by1 = _stair_window_mark(p)
        for y in risers:
            if y <= y_guard + 1e-6:
                Xa, Xb, Y = p.X(x0), p.X(x1), p.Y(y)
                if by0 <= Y <= by1 and Xa < bx1 and bx0 < Xb:        # stop short of W-D's mark
                    if Xa < bx0: cc.line(Xa, Y, bx0, Y)
                    if bx1 < Xb: cc.line(bx1, Y, Xb, Y)
                else:
                    cc.line(Xa, Y, Xb, Y)
        cc.setLineWidth(0.5)
        X, Ya, Yb = p.X(xr), p.Y(Y_TOP_RISER), p.Y(y_guard)          # Ya is the higher on the page
        if bx0 <= X <= bx1 and Yb < by1 and by0 < Ya:
            if by1 < Ya: cc.line(X, Ya, X, by1)
            if Yb < by0: cc.line(X, by0, X, Yb)
        else:
            cc.line(X, Ya, X, Yb)
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


COMPASS = 0.70*inch


def draw_north(cx, cy):
    """True north for a plan drawn plan-north up: C-101 and C-102 turn the site by TURN to
       put true north up the sheet, so here the compass is turned back the other way, its
       N toward 396 Oak, the NORTH elevation's face."""
    c.saveState(); c.translate(cx, cy); c.rotate(-TURN)
    c.drawImage(assets.image("compass.png"), -COMPASS/2.0, -COMPASS/2.0, width=COMPASS, height=COMPASS,
                mask="auto", preserveAspectRatio=True)
    c.restoreState()


MECH = "MECH / LAUNDRY"


def _fitting(kind):
    """A Level 1 fitting's page rectangle (x0, y0, x1, y1): a fitting keeps its size and
       only its origin goes through the regrid, then the sheet mirror."""
    f = next(f for f in LEVEL[1]['furn'] if f[4] == kind)
    x0 = B1_W-PLAN_B1_L1.x(f[0], f[1])-f[2]
    y0 = PLAN_B1_L1.y(f[1])
    return x0, y0, x0+f[2], y0+f[3]


def draw_mech_label(p, tag=True):
    """The mechanical / laundry room's name and size, and -- on A-101, `tag` -- the W/D's
       tag.

       The panel's working space, the heater's and the door's swing leave one open patch
       in that room: right of the heater's space, between the panel's and the W/D. The
       plan's own centred label struck through the panel's box, so A-101 sets it there,
       in two lines, a size under the plan's compact type so the name fits. The trade
       sheets set it there too (b1_trade_level), in their grey, through p.c."""
    cc = p.c
    room = next(r for r in LEVEL[1]['rooms'] if r[4] == MECH)
    rx, ry, rw, rh = PLAN_B1_L1.rect(room)[:4]
    x0 = _fitting('whclear')[2]; x1 = B1_W-rx               # the heater's space to the wall
    y0 = _fitting('clear')[3]; y1 = _fitting('wd')[1]       # the panel's space to the W/D
    LAY("A-ANNO-IDEN"); cc.setFillColor(black)
    cx, cy = p.X((x0+x1)/2.0), p.Y((y0+y1)/2.0)
    name, size = MECH, "%s x %s" % (fmt(rw), fmt(rh))
    for t, f, z in ((name, "Helvetica-Bold", 5.0), (size, "Helvetica", 4.8)):
        assert cc.stringWidth(t, f, z) < (x1-x0)*p.sc-2, "A-101: %r overruns the mechanical room's open patch" % t
    assert (y1-y0)*p.sc >= 13.0, "A-101: the mechanical room's open patch is too shallow for its label"
    cc.setFont("Helvetica-Bold", 5.0); cc.drawCentredString(cx, cy+0.8, name)
    cc.setFont("Helvetica", 4.8); cc.drawCentredString(cx, cy-5.4, size)
    if tag:
        wx0, wy0, wx1, _wy1 = _fitting('wd')                # the machine's tag, inside its outline
        cc.setFont("Helvetica-Bold", 5.0); cc.drawCentredString(p.X((wx0+wx1)/2.0), p.Y(wy0+0.42), "W/D")


def mech_patch():
    """The open patch draw_mech_label() sets the mechanical room's label in, page feet
       (x0, y0, x1, y1): a sheet that draws over that room keeps its own work out of it."""
    room = next(r for r in LEVEL[1]['rooms'] if r[4] == MECH)
    rx = PLAN_B1_L1.rect(room)[0]
    return _fitting('whclear')[2], _fitting('clear')[3], B1_W-rx, _fitting('wd')[1]


def b1_trade_level(level):
    """A level of the house as a trade sheet's grey background: the stair over it and, on
       Level 1, the mechanical room's label where A-101 sets it, clear of the panel's
       working space and the door's swing (the plan's own centred label struck through
       the working space's outline)."""
    lv = b1_level(level)
    if level == 1:
        lv.rooms = [r[:6]+r[6:]+("nolabel",) if r[4] == MECH else r for r in lv.rooms]
    lv.over_plan = lambda pp: (draw_b1_stair(pp, level), level == 1 and draw_mech_label(pp, tag=False))
    return lv


def _hall_label_at(p):
    """The page point Level 1's hall label is centred on, as the plan sets a room's label."""
    room = next(r for r in LEVEL[1]['rooms'] if r[4] == "HALL")
    rx, ry, rw, rh = PLAN_B1_L1.rect(room)[:4]
    return p.X(B1_W-(rx+rw/2.0)), p.Y(ry+rh/2.0), rw, rh


def _hall_mark_y(p):
    """AHU-1's mark: midway between the hall label's last line and the rear door's tag."""
    _cx, cy, _rw, _rh = _hall_label_at(p)
    d2 = next(t for t in door_tags(1, 1) if t[2] == "D-2")
    return ((cy-11-1.5) + (p.Y(PLAN_B1_L1.y(d2[1]))+4.2))/2.0


def draw_hall_label(p):
    """Level 1's hall label where the plan sets it, over AHU-1's dashed cabinet, which fills
       most of the hall: on a white ground, so the dash does not run through it."""
    cx, cy, rw, rh = _hall_label_at(p)
    LAY("A-ANNO-IDEN"); c.setFillColor(black)
    for dy, font, size, t in ((5, "Helvetica-Bold", 7.2, "HALL"),
                              (-3.5, "Helvetica", 6.2, "%s x %s" % (fmt(rw), fmt(rh))),
                              (-11, "Helvetica", 6.2, "%.0f SF" % (rw*rh))):
        knockout(cx, cy+dy, t, font, size, align="c")


def bath1_label(room):
    """Bath 1's room tuple with its label in the one clear patch the room has on A-101:
       beside the shower, past the door's swing and ahead of the pan. The trade sheets keep
       the plan's own place, where their devices and runs are drawn around it. Worked on
       the page and handed back as the offset a room label takes, in model sense, so the
       sheet mirror flips its x back."""
    rx, ry, rw, rh = PLAN_B1_L1.rect(room)[:4]
    sx0, _sy0, sx1, _sy1 = _fitting('shower')
    _wx0, wy0, _wx1, _wy1 = _fitting('wc')
    door = next(d for d in LEVEL[1]['doors'] if d[3] == 'v' and abs(d[0]-(X_HALL1+PARTITION/2.0)) < 1e-6)
    swing = PLAN_B1_L1.y(door[1])+door[2]              # the leaf's reach along the hall wall
    cx, cy = (sx1+B1_W-rx)/2.0, (swing+wy0)/2.0         # the shower's edge to the hall wall
    return room[:5]+((-(cx-(B1_W-(rx+rw/2.0))), cy-(ry+rh/2.0)),)+room[6:]


CLOSET_TAG_DROP = 6.0      # page points: the D-5 oval off the room's string, beside the closet's figure


def _closet_tag_nudge(p, level):
    """A closet that opens toward the front -- Bedroom 2's -- has two strings in front of
       its doors a tag's height apart: the closet's own width, and past it the room's. The
       D-5 oval printed on the first. Here it slides along the doors' line, past the jamb
       toward the room, and down level with the closet's figure, clear of the room's
       string."""
    plan = LEVEL[level]['plan']
    rooms = LEVEL[level]['rooms']
    fronts = {}
    for op in LEVEL[level]['openings']:
        x, y, w, o = op[:4]
        cl = [r for r in rooms if str(r[4]).startswith("CL.") and is_closet(op, [r])]
        if o == 'h' and cl and abs(y-cl[0][1]) < 1e-6:          # the doors in the closet's front face
            fronts[(x+w/2.0, y-TAG_OFF)] = max(B1_W-plan.x(x, y), B1_W-plan.x(x+w, y))

    def nudge(tag, X, Y):
        end = fronts.get(tag[:2]) if tag[2] == "D-5" else None
        if end is None:
            return X, Y
        return p.X(end) + 3.0 + tag_half_width(tag[2]), Y - CLOSET_TAG_DROP
    return nudge


_REAR_PAD = max(y1 for _x0, _y0, _x1, y1, _nm in B1_FOUNDATION.pads)   # page feet


def sheet_a101():
    sh=Sheet(c,"A-101","Building 1 — floor plans","1/4\" = 1'-0\""); sh.frame()
    for level, oxx in zip(LEVELS, (X0+1.9*inch, X0+11.3*inch)):
        oy=Y1-28*Q-4.30*inch
        lv=b1_level(level)
        lv.over_plan=lambda pp, level=level: draw_b1_stair(pp, level)
        if level == 1:                          # A-101 sets this room's label itself
            lv.rooms = [r+("nolabel",) if r[4] == MECH else bath1_label(r) if r[4] == "BATH 1" else r
                        for r in lv.rooms]
        if level == 1:                          # and the hall's, over the air handler it hides
            lv.rooms = [(r+((0.0, 0.0),))[:6]+r[6:]+("nolabel",) if r[4] == "HALL" else r for r in lv.rooms]
        p=draw_level(c,lv,oxx,oy)
        # the soffit and the air handler it hides, M-101; on Level 1 the hall's label is
        # over the cabinet, and its mark stands between that and the rear door's tag
        draw_soffit(p, level, mark_y=_hall_mark_y(p) if level == 1 else None)
        if level == 1:
            draw_hall_label(p)
        draw_door_tags(p, LEVEL[level]['plan'], B1_W, door_tags(1, level),     # the marks A-602 schedules
                       nudge=_closet_tag_nudge(p, level))
        if level == 1:
            draw_landings(p, B1_FOUNDATION.pads, "A-101")
            draw_mech_label(p)
        if level == 2:
            from src.roof import B1_ROOF            # the attic hatch S-103 places, RCO 807.1
            for h in B1_ROOF.hatches: draw_attic_hatch(p, h)
        p.note(B1_W/2.0,PLAN_B1_L1.y(-6.6),"OAK AVENUE  ·  25'-0\" FRONT SETBACK",6.6)
        # the rear notes stand past the back door's landing, on both levels alike
        p.note(B1_W/2.0,_REAR_PAD+1.0,"BUILDING 2 AND THE ALLEY TO THE REAR  \u00b7  5'-0\" SIDE YARD EACH SIDE",6.0)
        if level == 1:
            p.unitbox(9.5,PLAN_B1_L1.y(9.6),"UNIT 1","3 BR / 2 BA",1.75,0.42)
        c.setFillColor(black); c.setFont("Helvetica-Bold",12)
        c.drawString(oxx,oy-1.50*inch,"LEVEL %d — UNIT 1" % level)
        c.setFont("Helvetica",9); c.drawString(oxx,oy-1.68*inch,"SCALE: 1/4\" = 1'-0\"")
        c.setLineWidth(1.2); c.line(oxx,oy-1.22*inch,oxx+2.6*inch,oy-1.22*inch)
        draw_north(oxx+3.4*inch, oy-1.45*inch)                    # beside the plan's title
    c.setFont("Helvetica",8.4); c.setFillColor(black)
    for i,t in enumerate([
            "UNIT 1: SINGLE-FAMILY HOUSE, 3 BR / 2 BA, TWO STORIES.",
            stair_line(),
            "LEVEL 2 LANDING W-A, AT THE HEAD OF THE STAIR: SAFETY GLAZING, RCO 308.4.",
            "EACH LEVEL'S HALL SOFFIT, DASHED — %s CLEAR ON LEVEL 1, %s ON LEVEL 2 — HIDES ITS AIR HANDLER AND DUCTS: M-101."
            % (fmt(soffit_clear(1)), fmt(soffit_clear(2)))]):
        c.drawString(X0,oy-(2.15+0.16*i)*inch,t)
    c.showPage()

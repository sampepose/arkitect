"""P-102 — Building 1 water supply plans: Unit 1's two levels side by side, greyed, with
the supply, the trunk, the manifolds and every home run on them; the legend, the
fixture-unit and pipe-size table, the supply diagram and the notes."""
from arkitect.lib.draw.page import Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import B1_D, B1_W
from src.plumbing import BUILDING_1, sizes
from src.sheets.a101 import b1_trade_level
from arkitect.lib.draw.kit import Q, X0, X1, Y0, Y1, c, knockout
from src.sheets.e_common import grey_context
from arkitect.lib.draw.kit import title
from src.sheets.p_common import draw_service, legend, notes, supply_diagram, wsfu_table, pm
from arkitect.lib.draw.plumbing_kit import draw_unit
from arkitect.lib.draw.page import GREY, LAY
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.units import fmt, inches
from reportlab.lib.colors import black, white
from src import building1 as B1M
from src import drainage as dr
from src import levels as LV


BATH2_SC = 0.375*inch                  # 3/8" = 1'-0"
# Every annotation on the enlargement, one size. It was 5.2 and 5.6 pt: "difficult to use in
# the field" (a reviewer through the designer, 2026-09-20), which is the only test a note has to pass.
ANNO = 7.0



def _where_up(vents):
    """Where each lavatory's vent goes, from the model: the roof, or the vent it joins."""
    out = []
    for v in vents:
        t = dr.tie_target(v)
        out.append('%s TO THE ROOF' % v.mark if t is None else
                   '%s INTO %s' % (v.mark, t[1].mark if t[0] == 'vent' else 'STACK '+t[1].name))
    return ', '.join(out)

def _bath2(x, y, width):
    """ENLARGED PLAN -- BATH 2, DRAIN, WASTE AND VENT: the stack, the lavatories' routes and
       the chase question P-601 note 1a answers, drawn from src/drainage.py's branch. Page
       feet, as the plans; returns the lowest point drawn."""
    room = next(dr.water._mirror(B1M.PLAN_B1_L2.rect(r), B1_W)[:4] for r in B1M.L2_ROOMS if r[4] == 'BATH 2')
    rx0, ry0, rw, rh = room
    wall = B1M.PARTITION
    x_lo, y_lo = rx0-wall-0.3, min(ry0, dr.V_E_POS[1])-wall-0.3
    x_hi, y_hi = rx0+rw+wall+0.3, max(ry0+rh, dr.A_POS[1])+wall+0.3
    assert (x_hi-x_lo)*BATH2_SC <= width, 'P-102: the Bath 2 enlargement is wider than its column'
    c.setFillColor(black); c.setFont("Helvetica-Bold", 8.0)
    c.drawString(x, y, "ENLARGED PLAN — BATH 2, UNIT 1 LEVEL 2: DRAIN, WASTE AND VENT")
    c.setFont("Helvetica", 6.4); c.drawString(x, y-9.0, "SCALE: 3/8\" = 1'-0\"  ·  P-601 NOTES 1a AND 1x")
    top = y-0.44*inch
    X = lambda v: x+(v-x_lo)*BATH2_SC
    Y = lambda v: top-(v-y_lo)*BATH2_SC
    # the walls, stud face and far face
    LAY("A-WALL"); c.setStrokeColor(black); c.setLineWidth(0.9); c.setFillColor(white)
    c.rect(X(rx0), Y(ry0+rh), rw*BATH2_SC, rh*BATH2_SC, fill=0, stroke=1)
    c.setLineWidth(0.5)
    c.rect(X(rx0-wall), Y(ry0+rh+wall), (rw+2*wall)*BATH2_SC, (rh+2*wall)*BATH2_SC, fill=0, stroke=1)
    # the fixtures, grey
    LAY("P-SANR-FIXT"); c.setStrokeColor(GREY); c.setLineWidth(0.6)
    fx = {'lav': list(dr._LAVS2), 'wc': [dr._WC2], 'tub': [dr._TUB2]}
    names = {'lav': 'LAV', 'wc': 'WC', 'tub': 'TUB'}
    for k, fs in fx.items():
        for f in fs:
            c.rect(X(f.x), Y(f.y+f.h), f.w*BATH2_SC, f.h*BATH2_SC, fill=0, stroke=1)
            c.setFillColor(GREY); c.setFont("Helvetica", ANNO)
            c.drawCentredString(X(f.x+f.w/2.0), Y(f.y+f.h)+3.0, names[k])
    # the branch, in the floor: dashed, heavy where it is 3"
    LAY("P-SANR-UNDR"); c.setStrokeColor(black)
    pts = dr.BATH2_BRANCH
    wc_at = dr._branch_along(dr.BATH2_CONNS[2][1])
    run = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = abs(b[0]-a[0])+abs(b[1]-a[1])
        c.setLineWidth(2.0 if run+1e-9 >= wc_at else 1.2); c.setDash(5, 2)
        if run < wc_at < run+seg-1e-9:                       # the size changes at the closet
            t = (wc_at-run)/seg; m = (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
            c.setLineWidth(1.2); c.line(X(a[0]), Y(a[1]), X(m[0]), Y(m[1]))
            c.setLineWidth(2.0); c.line(X(m[0]), Y(m[1]), X(b[0]), Y(b[1]))
        else:
            c.line(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]))
        run += seg
    c.setDash()
    for _k, at, _size in dr.BATH2_CONNS:
        c.setFillColor(black); c.circle(X(at[0]), Y(at[1]), 1.8, fill=1, stroke=0)
    # the stack, and the dry vent standing behind each lavatory -- 909.2: a trap over this
    # floor cannot be vented by the branch inside it
    marks = [dr.BATH2_VENTS[i] for i in sorted(dr.BATH2_VENTS)]
    vents = [next(d for d in dr.DRY_VENTS if d.mark == m) for m in marks]
    # each lavatory drops at its own vent and runs to the branch from there; where the vent
    # does not stand on the branch, that leg is what carries it. Drawn under the marks.
    c.setStrokeColor(black); c.setLineWidth(1.2); c.setDash(5, 2)    # in the floor, as the branch is
    for i, v in zip(sorted(dr.BATH2_VENTS), vents):
        at = dr.BATH2_CONNS[i][1]
        if abs(at[0]-v.at[0]) > 1e-9 or abs(at[1]-v.at[1]) > 1e-9:
            c.line(X(v.at[0]), Y(v.at[1]), X(at[0]), Y(at[1]))
    c.setDash()
    c.setLineWidth(0.9); c.setFillColor(white)
    for pos, r in [(dr.A_POS, 1.75)]+[(v.at, 1.2) for v in vents]:
        c.circle(X(pos[0]), Y(pos[1]), r/12.0*BATH2_SC, fill=1, stroke=1)
    LAY("P-ANNO-TEXT"); c.setFillColor(black)
    c.setStrokeColor(black); c.setLineWidth(0.4)
    # leader past the wet wall, on whichever side of the room it is, to the one label
    below = vents[0].at[1] > ry0+rh/2.0
    for v in vents:
        if below: c.line(X(v.at[0]), Y(v.at[1])-2.0, X(v.at[0]), Y(y_hi)-2.0)
        else:     c.line(X(v.at[0]), Y(v.at[1])+2.0, X(v.at[0]), Y(y_lo)+2.0)
    knockout(X(vents[0].at[0])-2.0, Y(y_hi)-2.0-ANNO if below else Y(y_lo)+4.0,
             "%s — ONE PER LAVATORY, IN THE WALL: %s"
             % (", ".join('%s %s"' % (v.mark, v.size) for v in vents), _where_up(vents)), "Helvetica-Bold", ANNO)
    knockout(X(dr.A_POS[0])-6.0, Y(dr.A_POS[1])-2.0, "STACK A 3\" — ITS TOP, UNDER THE TUB",
             "Helvetica-Bold", ANNO, align="r")
    secs = dr.floor_branch_sections()
    two = sum(l for z, l in secs if z == '2'); three = sum(l for z, l in secs if z == '3')
    knockout(X(dr.BATH2_BRANCH[1][0])+3.0, Y(dr.BATH2_BR_Y)-9.0, "2\" AT 1/4\"/FT, %s" % fmt(two), "Helvetica", ANNO)
    knockout(X(dr.BATH2_CONNS[2][1][0])+3.0, Y(dr.BATH2_BR_Y)-9.0, "3\" AT 1/8\"/FT, %s" % fmt(three), "Helvetica", ANNO)
    # what the drawing says, under it
    ny = Y(y_hi)-0.16*inch-(ANNO*1.32 if below else 0.0)
    lines = wrap_notes([
        "THE BRANCH (DASHED) RUNS IN THE LEVEL 2 FLOOR THROUGH THE TRUSSES' OPEN WEBS, S-102: ITS CROWN %s UNDER THE "
        "SUBFLOOR AT THE HEAD, TIGHT UNDER THE TOP CHORD, AND ITS BOTTOM %s UNDER IT AT STACK A — %s OF THE %s BETWEEN "
        "THE CHORDS. EACH FIXTURE DRAIN DROPS THROUGH THE FLOOR AND CONNECTS HORIZONTALLY TO THE BRANCH (DOTS), IN "
        "THE ORDER LAV, LAV, WC, TUB: A HORIZONTAL WET VENT, OPC 912.1. FOR HOW EACH TRAP IS VENTED AND FOR EVERY "
        "FITTING, SEE P-601 NOTE 1a AND THE ISOMETRIC BESIDE IT."
        % (inches(LV.SUBFLOOR+dr.BRANCH_TOP), inches(dr.floor_branch_bottom()),
           inches(dr.floor_branch_bottom()-LV.SUBFLOOR-dr.BRANCH_TOP), inches(dr.web_clear()))],
        width, ANNO, indent="")
    c.setFont("Helvetica", ANNO)
    for ln in lines:
        if ln:
            c.drawString(x, ny, ln); ny -= ANNO*1.32
    c.setStrokeColor(black); c.setFillColor(black)
    return ny


def _level(k, ox, oy):
    """One level of the house as a supply background, its water on it."""
    lv = b1_trade_level(k)
    def water(p):
        if k == 1: draw_service(p, BUILDING_1, sizes(BUILDING_1))
        for u in BUILDING_1.units:
            if u.level == k: draw_unit(p, u, tag_riser='FROM THE MANIFOLDS BELOW', riser_side=-1, pm=pm)
        grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'BUILDING 2 AND THE ALLEY BEYOND', '396 OAK AVE', '404 OAK AVE',
                     side_at=(8.0, None))
    lv.overlay = water
    return draw_level(c, lv, ox, oy)


def sheet_p102():
    sh = Sheet(c, "P-102", "Building 1 — water supply plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.75*inch-B1_D*Q
    ox1 = X0+1.4*inch
    ox2 = ox1+B1_W*Q+1.2*inch
    _level(1, ox1, oy)
    _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 1 — WATER SUPPLY PLAN  ·  UNIT 1')
    title(ox2, oy, 'BUILDING 1 — LEVEL 2 — WATER SUPPLY PLAN  ·  UNIT 1')
    # the right column: legend, then the table
    rx = ox2+B1_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(rx, ry, rw)-6
    low = wsfu_table(rx, ry, BUILDING_1, rw)
    low = _bath2(rx, low-0.35*inch, rw)
    assert low >= Y0, "P-102 right column runs off the sheet"
    # under the plans: the diagram at the left, the notes at the right
    by = oy-1.22*inch
    lw = 5.6*inch
    supply_diagram(ox1, by, BUILDING_1, lw)
    nx = ox1+lw+0.3*inch
    low = notes(nx, by, rx-0.3*inch-nx)
    assert low >= Y0, "P-102 notes run off the sheet by %.2f in" % ((Y0-low)/inch)
    c.showPage()

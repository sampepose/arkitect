"""P-103 — Building 2 water supply plans: Unit 4 and Unit 5 side by side, greyed, with
the service, the meter, the riser, the manifolds and every home run on them; the
legend, the fixture-unit and pipe-size table, the supply diagram and the notes."""
from lib.draw.page import Sheet, end_plans
from lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building2 import B2_W, b2_level
from src.plumbing import BUILDING_2, sizes
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from lib.draw.kit import title
from src.sheets.p_common import draw_service, legend, notes, supply_diagram, wsfu_table, pm
from lib.draw.plumbing_kit import draw_unit
from src.sheets.plans import draw_u5_stair


def _level(k, ox, oy):
    """One Building 2 level as a supply background, its water on it. k is 0 for Unit 4
       at grade, 1 for Unit 5 above; the Unit 5 stair is drawn on both as A-103 draws it."""
    lv = b2_level(k+1)
    lv.over_plan = lambda pp, above=(k == 0): draw_u5_stair(pp, B2_W, above=above)
    def water(p):
        s = sizes(BUILDING_2)
        if k == 0: draw_service(p, BUILDING_2, s)
        for u in BUILDING_2.units:
            if u.level == k+1: draw_unit(p, u, tag_riser='FROM UNIT 4 BELOW', pm=pm)
        grey_context(p, B2_W, 28, 'COURTYARD  ·  FACES BUILDING 1  ·  S ELM AVENUE BEYOND',
                     'PARKING AND ALLEY', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=5.6)
    lv.overlay = water
    return draw_level(c, lv, ox, oy)


def sheet_p103():
    sh = Sheet(c, "P-103", "Building 2 — water supply plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-1.35*inch-28*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+26*Q+1.0*inch
    _level(0, ox1, oy)
    _level(1, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 2 — LEVEL 1 — WATER SUPPLY PLAN  ·  UNIT 4')
    title(ox2, oy, 'BUILDING 2 — LEVEL 2 — WATER SUPPLY PLAN  ·  UNIT 5')
    rx = ox2+26*Q+0.45*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(rx, ry, rw)-6
    wsfu_table(rx, ry, BUILDING_2, rw)
    by = oy-1.22*inch
    lw = 6.0*inch          # as P-102, so the two sheets read alike
    supply_diagram(ox1, by, BUILDING_2, lw)
    nx = ox1+lw+0.3*inch
    low = notes(nx, by, rx-0.3*inch-nx, see='P-102')
    assert low >= Y0, "P-103 notes run off the sheet by %.2f in" % ((Y0-low)/inch)
    c.showPage()

"""P-103 — Building 2 water supply plans: Unit 2 and Unit 3 side by side, greyed, with
the supply, the manifolds and every home run on them; the legend, the fixture-unit and
pipe-size table and the supply diagram. The notes are P-102's."""
from lib.draw.page import Sheet, end_plans
from lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building2 import B2_D, B2_W, b2_level
from src.plumbing import BUILDING_2, sizes
from src.sheets.a102 import draw_u5_stair
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from lib.draw.kit import title
from src.sheets.p_common import draw_service, legend, notes, supply_diagram, wsfu_table, pm
from lib.draw.plumbing_kit import draw_unit


def _level(k, ox, oy):
    """One Building 2 level as a supply background, its water on it. k is 1 for Unit 2 at
       grade, 2 for Unit 3 above; the Unit 3 stair is drawn on both as A-102 draws it."""
    lv = b2_level(k)
    lv.over_plan = lambda pp, above=(k == 1): draw_u5_stair(pp, B2_W, above=above)
    def water(p):
        if k == 1: draw_service(p, BUILDING_2, sizes(BUILDING_2))
        for u in BUILDING_2.units:
            if u.level == k: draw_unit(p, u, tag_riser='FROM UNIT 2 BELOW', riser_side=1, pm=pm)
        grey_context(p, B2_W, B2_D, 'COURTYARD  ·  FACES BUILDING 1  ·  OAK AVENUE BEYOND',
                     'PARKING AND ALLEY', '396 OAK AVE', '404 OAK AVE', top_off=5.6, side_at=(25.0, None))
    lv.overlay = water
    return draw_level(c, lv, ox, oy)


def sheet_p103():
    sh = Sheet(c, "P-103", "Building 2 — water supply plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-0.9*inch-B2_D*Q
    ox1 = X0+1.4*inch
    ox2 = ox1+B2_W*Q+1.2*inch
    _level(1, ox1, oy)
    _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 2 — LEVEL 1 — WATER SUPPLY PLAN  ·  UNIT 2')
    title(ox2, oy, 'BUILDING 2 — LEVEL 2 — WATER SUPPLY PLAN  ·  UNIT 3')
    rx = ox2+B2_W*Q+0.6*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(rx, ry, rw)-6
    low = wsfu_table(rx, ry, BUILDING_2, rw)
    assert low >= Y0, "P-103 right column runs off the sheet"
    by = oy-1.22*inch
    lw = 5.6*inch
    supply_diagram(ox1, by, BUILDING_2, lw)
    nx = ox1+lw+0.3*inch
    low = notes(nx, by, rx-0.3*inch-nx, see='P-102')
    assert low >= Y0, "P-103 notes run off the sheet"
    c.showPage()

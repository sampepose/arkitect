"""P-102 — Building 1 water supply plans: Level 1 and Level 2 side by side, greyed, with
the service, the meter, the trunks, the manifolds and every home run on them; the
legend, the fixture-unit and pipe-size table, the supply diagram and the notes."""
from lib.draw.page import Sheet, end_plans
from lib.draw.sheets import draw_level
from reportlab.lib.units import inch
from src.building1 import _b1_level
from src.plumbing import BUILDING_1, sizes
from lib.draw.kit import Q, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from lib.draw.kit import title
from src.sheets.p_common import draw_service, legend, notes, supply_diagram, wsfu_table, pm
from lib.draw.plumbing_kit import draw_unit
from src.sheets.plans import B1_DRAWING


def _level(k, ox, oy):
    """One Building 1 level as a supply background, its water on it."""
    lv = _b1_level(k, [], [], [], units=[], u3stair=(k == 1), annotate=False, **B1_DRAWING)
    def water(p):
        s = sizes(BUILDING_1)
        if k == 1: draw_service(p, BUILDING_1, s)
        for u in BUILDING_1.units:
            if u.level == k:
                draw_unit(p, u, tag_riser='FROM THE MANIFOLDS BELOW' if u.name == 'UNIT 1' else 'FROM UNIT 2 BELOW',
                          riser_side=-1, pm=pm)
        grey_context(p, 26, 48, 'S ELM AVENUE', 'REAR YARD  ·  BUILDING 2 BEYOND',
                     'SAGE AVENUE', 'ADJACENT PARCEL')
    lv.overlay = water
    return draw_level(c, lv, ox, oy)


def sheet_p102():
    sh = Sheet(c, "P-102", "Building 1 — water supply plans", "1/4\" = 1'-0\""); sh.frame()
    oy = Y1-0.55*inch-48*Q
    ox1 = X0+1.0*inch
    ox2 = ox1+26*Q+1.0*inch
    _level(1, ox1, oy)
    _level(2, ox2, oy)
    end_plans()
    title(ox1, oy, 'BUILDING 1 — LEVEL 1 — WATER SUPPLY PLAN  ·  UNIT 1 BELOW, UNIT 2')
    title(ox2, oy, 'BUILDING 1 — LEVEL 2 — WATER SUPPLY PLAN  ·  UNIT 1 ABOVE, UNIT 3')
    # the right column: legend, then the table
    rx = ox2+26*Q+0.45*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = legend(rx, ry, rw)-6
    wsfu_table(rx, ry, BUILDING_1, rw)
    # under the plans: the diagram at the left, the notes at the right
    by = oy-1.22*inch
    lw = 6.0*inch          # the diagram's three columns; the notes take the rest
    supply_diagram(ox1, by, BUILDING_1, lw)
    nx = ox1+lw+0.3*inch
    low = notes(nx, by, rx-0.3*inch-nx)
    assert low >= Y0, "P-102 notes run off the sheet by %.2f in" % ((Y0-low)/inch)
    c.showPage()

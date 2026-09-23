"""S-104 — wall bracing plans and details: each building's braced wall lines at both
levels over the greyed plans, from src/bracing.py; the bracing schedule, the design
basis, four details and the notes. Every figure printed is the model's."""
from arkitect.lib.draw.page import GREY, LAY, Sheet, end_plans
from arkitect.lib.draw.sheets import draw_level
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import fmt, inches, IN
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from src import bracing as br
from arkitect.codes.ohio.rco import bracing as rco_bracing
from src.fireblocking import FB
from src import levels
from src.building1 import _b1_level
from src.building2 import B2_W, b2_level
from src.openings import WIN_GEOM
from src.roof import HEEL_NOM, ROOF_PITCH, TRUSS_OC
from arkitect.lib.draw.kit import E, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from arkitect.lib.draw.kit import _fits
from src.sheets.plans import B1_DRAWING, draw_u5_stair
from arkitect.lib.draw.detail import _D, _detail_title, _hatch_band
from arkitect.codes.ohio.rco.bracing_draw import _PORTAL_ANCHOR, _bracing, _dim_h, _dim_v, _heading, _plan_title
from arkitect.codes.ohio.rco.bracing_draw import _schedule
from arkitect.codes.ohio.rco.bracing_draw import _portal_levels
from arkitect.codes.ohio.rco.bracing_draw import _lines
from arkitect.codes.ohio.rco.bracing_draw import _notes
from arkitect.codes.ohio.rco import bracing as bracing_shared

SH = IN(0.5)         # sheathing, drawn
PL = IN(1.5)         # one plate
GYP = IN(0.625)




# ================================ the plans ================================


def _plans():
    """The four plans, two columns of Building 1 over two of Building 2. Returns the
       page y under the lowest title and the page x right of the plans."""
    top = Y1-0.75*inch
    ox = (X0+0.95*inch, X0+0.95*inch+26*E+1.75*inch)
    oy1 = top-48*E
    oy2 = oy1-0.97*inch-1.1*inch-28*E
    for i, level in enumerate((1, 2)):
        lv = _b1_level(level, [], [], [], units=[], u3stair=(level == 1), annotate=False, **B1_DRAWING)
        lv.overlay = (lambda lines: lambda p: (_bracing(p, lines),
                      grey_context(p, 26, 48, 'S ELM AVENUE', 'REAR YARD', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=4.4)))(_lines('BUILDING 1', level, br=br))
        draw_level(c, lv, ox[i], oy1, sc=E)
        lv2 = b2_level(level)
        lv2.over_plan = (lambda above: lambda pp: draw_u5_stair(pp, B2_W, above=above))(level == 1)
        lv2.overlay = (lambda lines: lambda p: (_bracing(p, lines),
                       grey_context(p, B2_W, 28, 'COURTYARD', 'PARKING AND ALLEY', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=8.2)))(_lines('BUILDING 2', level, br=br))
        draw_level(c, lv2, ox[i], oy2, sc=E)
    end_plans()
    for i, level in enumerate((1, 2)):
        _plan_title(ox[i], oy1, 'BUILDING 1 — LEVEL %d WALL BRACING' % level)
        _plan_title(ox[i], oy2, 'BUILDING 2 — LEVEL %d WALL BRACING' % level)
    return oy2-1.05*inch, ox[1]+26*E+1.45*inch


# ================================ the tables ================================




def _basis(x, y, width):
    S, LEAD = 5.6, 7.3
    LAY('S-ANNO-TEXT')
    y = _heading(x, y, width, 'DESIGN BASIS')
    rows = [('CODE', 'RCO 602.10, 2018 IRC BASE; PRESCRIPTIVE'),
            ('WIND', '%s, G-001' % br.WIND),
            ('SEISMIC DESIGN CATEGORY', '%s — WIND GOVERNS, 602.10.3 ITEM 1' % rco_bracing.SDC),
            ('METHOD', '%s, ALL EXTERIOR WALLS, BOTH LEVELS' % rco_bracing.METHOD),
            ('', 'CS-PF BESIDE THE BUILDING 2 COURTYARD D-1S'),
            ('BRACED WALL LINES', 'THE EXTERIOR WALLS, TWO EACH WAY'),
            ('SPACING', 'OUT TO OUT, NOT OVER %s, TABLE 602.10.1.3' % fmt(rco_bracing.MAX_SPACING)),
            ('SHEATHING', '%s, TABLE 602.3(3)' % rco_bracing.SHEATHING),
            ('NAILING', '%s AT %s EDGES / %s FIELD' % (rco_bracing.NAIL, inches(rco_bracing.NAIL_EDGE), inches(rco_bracing.NAIL_FIELD))),
            ('', 'W1R WALLS: %s, SAME SPACING' % rco_bracing.NAIL_W1R),
            ('', 'BLDG 1 REAR WALL W1R BOTH LEVELS — %s' % br.fsd_rated_text()),
            ('ROOF CONNECTION', '602.10.8.2 %s, WALLS A AND B' % bracing_shared.roof_connection(heel_nom=br.HEEL_NOM)),
            ('HOLD-DOWNS', '%d LB CAPACITY WHERE DRAWN' % rco_bracing.HOLD_DOWN_LB)]
    c.setFillColor(black)
    for k, v in rows:
        _fits(v, 'Helvetica', S, width-1.25*inch, 'S-104 basis')
        c.setFont('Helvetica-Bold', S); c.drawString(x, y, k)
        c.setFont('Helvetica', S); c.drawRightString(x+width, y, v); y -= LEAD
    return y




def _notes_text():
    b1_perp = ', '.join(sorted({ln.tag for ln in br.LINES if ln.building == 'BUILDING 1' and br.floor_connection(ln) == 1}))
    b2_perp = ', '.join(sorted({ln.tag for ln in br.LINES if ln.building == 'BUILDING 2' and br.floor_connection(ln) == 1}))
    truss_walls = ' AND '.join(sorted({ln.tag for ln in br.LINES if br.truss_perpendicular(ln)}))
    (pf,) = {(ln.building, ln.wall) for ln in br.LINES for _p, _o in br.portal_openings(ln)}
    (strap,) = {rco_bracing.strap_lb(ln.wall_height, o.b-o.a) for ln in br.LINES for _p, o in br.portal_openings(ln)}
    pf_where = 'at both levels' if _portal_levels(br=br) == [1, 2] else 'at Level %d' % _portal_levels(br=br)[0]
    pf_anchor = ' '.join(_PORTAL_ANCHOR[lv] for lv in _portal_levels(br=br))
    return [n.upper() for n in (
        '1. Braced wall lines are the exterior walls of each building, tagged 1 at the front wall, 2 at the rear wall, A at '
        'the Sage wall and B at the adjacent-parcel wall, the same at both levels. W4, the interior bearing walls and the '
        'partitions are not braced wall lines; fasten no bracing to W4.',

        f'2. Method {rco_bracing.METHOD}, 602.10.4.2: sheath every framed portion of every exterior wall at both levels with '
        f'{rco_bracing.SHEATHING}, including above and below every opening and the gable end walls to the roof sheathing. Vertical joints '
        'on common studs; horizontal joints on 2x blocking, 602.10.4.4. Gypsum board inside every braced wall panel, 602.10.4.3, A-601.',

        f'3. Fastening, Table 602.3(3): {rco_bracing.NAIL} at {inches(rco_bracing.NAIL_EDGE)} o.c. at panel edges and {inches(rco_bracing.NAIL_FIELD)} '
        f'in the field, {inches(rco_bracing.NAIL_PENETRATION)} into the framing. At W1R walls, where the OSB is over 5/8" Type X '
        f'exterior gypsum, A-601, {rco_bracing.NAIL_W1R} at the same spacing. On Building 1 this includes the rear wall, '
        f'{br.fsd_rated_text()}, W1R for its full height, gable included: see A-601.',

        '4. Braced wall panels are the full-height segments drawn, at the lengths drawn, each not less than Table 602.10.5 for '
        'the taller adjacent clear opening. The schedule gives each line\'s required and provided length. An opening added, '
        'widened or moved in an exterior wall revises this sheet.',

        f'5. Ends, 602.10.7: the end conditions scheduled. Hold-downs, HD: {rco_bracing.HOLD_DOWN_LB} lb capacity, fastened to the '
        'panel edge stud nearest the corner and to the foundation at Level 1, to the framing below at Level 2, '
        'installed per the manufacturer.',

        '6. Foundation, 403.1.6: sole plates anchored per S-101 note 6.',

        f'7. Floors, 602.10.8: where the joists are perpendicular to a braced wall panel — Building 1 walls {b1_perp}, '
        f'Building 2 walls {b2_perp} — a rim along the whole panel; where parallel, a rim or end joist directly above and below '
        'the panel, or full-depth blocking at 16" o.c. between the joists each side of it. Level 2 bottom plate to rim or '
        'blocking, Table 602.3(1) item 15: 3-16d box at 16" o.c.; rim or blocking to the Level 1 top plate, item 22: 8d '
        'common toe nails at 6" o.c. Detail 3.',

        f'8. Roof, 602.10.8.2 {bracing_shared.roof_connection(heel_nom=br.HEEL_NOM)}: the raised heel sets the top of the trusses more than '
        f'{inches(rco_bracing.HEEL_BLOCKING_MAX)} above the top plate. Over every braced wall panel of walls {truss_walls}, where the '
        f'trusses at {inches(TRUSS_OC)} o.c. cross the wall, vertical blocking panels between the trusses, detail 2, per '
        'Figure 602.10.8.2(3), or blocking panels by the truss manufacturer, 802. Every one of them is solid from the top '
        f'plate to the roof sheathing with no vent opening: it is the eave fireblock of S-103 detail 1, A-601 {FB["CORNICE"]}. '
        'Attic intake is inboard of it, S-103 note 7. Walls 1 and 2 are gable ends: sheathing continuous to the roof sheathing as S-103 detail 2 draws it.',

        f'9. Portal frame, Method CS-PF, 602.10.6.4, {pf[0]} {pf[1]}, beside the D-1 {pf_where}: a '
        f'{inches(rco_bracing.PORTAL_HEADER[0])} x {inches(rco_bracing.PORTAL_HEADER[1])} net header, not less than the S-102 header, directly '
        'under the double top plate and over the opening and the portal leg; top plate to header two rows of 16d sinkers at 3" o.c.; '
        'king stud to header 6-16d sinkers; double 2x king and jack studs at least, No. 2 or better; sheathing '
        f'nailed at {inches(rco_bracing.PORTAL_NAIL_OC)} o.c. to all portal framing and in a 3" grid to the header; a {strap:,} lb '
        f'tension strap, Table 602.10.6.4, header to jack stud each side of the opening on the inside face. {pf_anchor} Detail 4.',

        '10. Uplift, 602.10.2.1: the bracing lengths rely on the uplift load path of 602.3.5; truss connectors per S-103 note 2.',
    )]




# ================================ the details ================================


def _d1(ox, oy, slot_w):
    """CONTINUOUSLY SHEATHED BRACED WALL LINE, ELEVATION. A typical run of wall: an end
       panel, a W-A, a panel, a D-1, a panel — the opening sizes and the wall height are
       the model's; the run is illustrative."""
    sc = 13.5                                                             # 3/16" = 1'-0"
    d = _D(ox, oy, sc, slot_w); LAY('S-DETL')
    H = br.WALL_HEIGHT[('BUILDING 2', 1)]
    wa_w, (wa_sill, wa_h) = 3.0, WIN_GEOM['A']
    L = 16.0
    win = (2.5, 2.5+wa_w); door = (10.0, 13.0)
    c.setStrokeColor(GREY); c.setLineWidth(0.3)
    _hatch_band(c, d.X(0), d.Y(0), d.X(L), d.Y(H), step=4.0)
    c.setStrokeColor(black); c.setLineWidth(0.8); c.rect(d.X(0), d.Y(0), L*sc, H*sc, fill=0, stroke=1)
    d.rect(win[0], wa_sill, win[1], wa_sill+wa_h, fill=white, lw=0.6)
    d.rect(door[0], 0.0, door[1], br.D1_HEIGHT, fill=white, lw=0.6)
    for x in (4.0, 8.0, 12.0):                                            # vertical joints on common studs
        d.line(x, 0.0, x, H, lw=0.3, dash=(2, 1.5))
    d.line(0.0, 8.0, L, 8.0, lw=0.5, dash=(4, 1.5))                       # horizontal joint on blocking
    for a, b in ((0.0, win[0]), (win[1], door[0]), (door[1], L)):         # the braced wall panels
        d.line(a, 0.0, b, H, lw=0.35); d.line(a, H, b, 0.0, lw=0.35)
        _dim_h(d, a, b, -0.7, 'PANEL LENGTH')
    _dim_v(d, win[0]+0.6, wa_sill, wa_sill+wa_h, 'CLEAR OPENING HEIGHT')
    _dim_v(d, door[0]+0.6, 0.0, br.D1_HEIGHT, 'CLEAR OPENING HEIGHT')
    c.setFillColor(black); c.rect(d.X(0.05), d.Y(0.1), 3.6, 7.0, fill=1, stroke=0)   # a hold-down at the end panel
    R = L+0.9
    d.lab(6.5, H-0.4, R, H+0.2, ('%s ON EVERY FRAMED SURFACE, ABOVE AND' % rco_bracing.SHEATHING, 'BELOW EVERY OPENING, 602.10.4.2'))
    d.lab(8.0, 8.0, R, 7.3, ('HORIZONTAL JOINTS ON 2x BLOCKING, 602.10.4.4',))
    d.lab(12.0, 5.5, R, 5.7, ('VERTICAL JOINTS ON COMMON STUDS',))
    # The detail's slot is narrow; the reason lives in note 3 and the schedule row, and
    # what the detail has to carry is WHICH walls, not why.
    d.lab(14.5, 3.5, R, 4.3, ('%s AT %s EDGES / %s FIELD;' % (rco_bracing.NAIL, inches(rco_bracing.NAIL_EDGE), inches(rco_bracing.NAIL_FIELD)),
                              'W1R WALLS %s' % rco_bracing.NAIL_W1R,
                              'BLDG 1 REAR WALL, %s' % br.fsd_rated_text()))
    d.lab(15.0, 1.2, R, 2.6, ('BRACED WALL PANEL: FULL HEIGHT, NOT LESS THAN', 'TABLE 602.10.5 FOR THE TALLER ADJACENT', 'CLEAR OPENING HEIGHT'))
    d.lab(0.2, 0.6, R, 0.9, ('HD WHERE SCHEDULED, END CONDITION 2 OR 5:', '%d LB, EDGE STUD NEAREST THE CORNER' % rco_bracing.HOLD_DOWN_LB))
    d.flush('S-104 detail 1')
    return min(d.lo, d.Y(-0.7)-6)


def _d2(ox, oy, slot_w):
    """ROOF CONNECTION OVER A BRACED WALL PANEL WHERE THE TRUSSES CROSS THE WALL. A
       section between two trusses: the wall, the 2x blocking on the plate, the vertical
       blocking panel in the plane of the wall, the truss beyond. Origin: the outside
       face of the wall sheathing at the top of the plate."""
    d = _D(ox, oy, 36.0, slot_w); LAY('S-DETL')
    wx0 = SH; wx1 = SH+EXT_STUD; run = 3.2
    d.rect(wx0, -1.6, wx1, -2*PL); d.insul(wx0, -1.6, wx1, -2*PL)
    d.rect(wx0, -2*PL, wx1, -PL); d.rect(wx0, -PL, wx1, 0.0)                    # double top plate
    d.rect(0.0, -1.6, SH, 0.0, fill=GREY)                                          # the braced wall panel's sheathing
    d.rect(wx1, -1.6, wx1+GYP, -GYP)
    d.rect(wx0, 0.0, wx1, PL)                                                      # 2x blocking on the plate
    top = HEEL_NOM                                                                 # the truss at the wall line, beyond
    d.line(wx0, PL, wx0, top, lw=0.5, dash=(3, 2)); d.line(wx0, 0.0, run, 0.0, lw=0.5, dash=(3, 2))
    d.line(wx0, top, run, top+(run-wx0)*ROOF_PITCH, lw=0.5, dash=(3, 2))
    # The panel is SOLID to the sheathing: it stands on the wall line between the same
    # trusses as S-103 detail 1's eave fireblock and is that fireblock, so it takes no
    # vent opening. Nothing is lost: the soffit is solid and the attic's intake is the
    # shingle-over vent inboard of the block, over the baffle, S-103 note 7.
    deck = lambda x: top+IN(1)+x*ROOF_PITCH                                        # the underside of the roof sheathing
    d.poly([(SH, PL), (SH+IN(0.5), PL), (SH+IN(0.5), deck(SH+IN(0.5))), (SH, deck(SH))], fill=GREY)   # the vertical blocking panel
    d.poly([(SH+IN(0.5), PL), (SH+IN(2.0), PL), (SH+IN(2.0), deck(SH+IN(2.0))), (SH+IN(0.5), deck(SH+IN(0.5)))])   # its 2x framing
    d.poly([(0.0, top+IN(1)), (run, top+IN(1)+(run)*ROOF_PITCH), (run, top+IN(1)+run*ROOF_PITCH+SH), (0.0, top+IN(1)+SH)])
    _dim_v(d, -0.35, 0.0, top, 'OVER %s' % inches(rco_bracing.HEEL_BLOCKING_MAX))
    R = run+0.4
    d.lab(1.8, top+IN(1)+1.8*ROOF_PITCH+SH/2.0, R, top+0.55, ('ROOF SHEATHING, S-103; EDGE NAILING', 'PER TABLE 602.3(1)'))
    d.lab(SH+IN(1.0), top*0.9, R, top-0.1, ('SOLID, TOP PLATE TO ROOF SHEATHING, NO VENT',
                                            'OPENING: THE EAVE FIREBLOCK, S-103 DETAIL 1',
                                            'AND A-601 %s. INTAKE INBOARD, S-103 NOTE 7' % FB['CORNICE']))
    d.lab(SH+IN(0.25), top*0.45, R, top*0.45-0.1, ('VERTICAL BLOCKING PANEL BETWEEN TRUSSES,', 'FIGURE 602.10.8.2(3), OR THE TRUSS', 'MANUFACTURER\'S BLOCKING PANEL, 802'))
    d.lab(wx0+EXT_STUD/2.0, PL/2.0, R, -0.25, ('2x BLOCKING ON THE PLATE, NAILED PER', 'TABLE 602.3(1); TRUSS CONNECTORS, S-103'))
    d.lab(2.2, top+(2.2-wx0)*ROOF_PITCH, R, top+(2.2-wx0)*ROOF_PITCH+0.95, ('TRUSS BEYOND, AT %s O.C.' % inches(TRUSS_OC),))
    d.lab(SH/2.0, -1.0, R, -1.05, ('BRACED WALL PANEL, WALL A OR B,', 'DOUBLE TOP PLATE'))
    d.flush('S-104 detail 2')
    return d.lo


def _ijoist(d, x, y0, depth, lw=0.5):
    """An I-joist in section: flanges and web, centered on x."""
    fw, ft, web = IN(2.5), IN(1.5), IN(0.4375)
    d.rect(x-fw/2.0, y0, x+fw/2.0, y0+ft, lw=lw); d.rect(x-fw/2.0, y0+depth-ft, x+fw/2.0, y0+depth, lw=lw)
    d.rect(x-web/2.0, y0+ft, x+web/2.0, y0+depth-ft, lw=lw)


def _d3(ox, oy, slot_w):
    """FLOOR CONNECTIONS AT BRACED WALL PANELS. Two sections through the Level 1 top
       plate and the Level 2 sole plate: the joists perpendicular to the wall (they end on
       a rim) and parallel (an end joist over the wall, blocking to the next)."""
    d = _D(ox, oy, 36.0, slot_w); LAY('S-DETL')                          # 1/2" = 1'-0"
    J = levels.F1_JOIST; SUB = levels.SUBFLOOR
    for x0, parallel in ((0.0, False), (1.95, True)):
        wx0 = x0+SH; wx1 = wx0+EXT_STUD
        d.rect(wx0, -1.2, wx1, -2*PL); d.rect(wx0, -2*PL, wx1, -PL); d.rect(wx0, -PL, wx1, 0.0)
        d.rect(x0, -1.2, x0+SH, J+SUB+PL+1.0, fill=GREY)                           # sheathing across the floor
        if parallel:
            _ijoist(d, wx0+EXT_STUD/2.0, 0.0, J)                                       # the end joist, over the wall
            d.rect(wx1, IN(1.5), wx1+0.8, J-IN(1.5), dash=(2, 1.5))                    # blocking to the next joist
            _ijoist(d, wx1+0.8+IN(1.25), 0.0, J, lw=0.4)
            reach = wx1+0.8+IN(2.5)
        else:
            d.rect(wx0, 0.0, wx0+IN(1.25), J)                                         # the rim
            d.rect(wx0+IN(1.25), IN(1.5), wx0+1.0, J-IN(1.5), dash=(2, 1.5))           # the joist, beyond
            reach = wx0+1.0
        d.rect(wx0, J, reach, J+SUB)                                                  # subfloor
        d.rect(wx0, J+SUB, wx1, J+SUB+PL)                                             # Level 2 sole plate
        d.rect(wx0, J+SUB+PL, wx1, J+SUB+PL+1.0)                                      # Level 2 studs
    R = 3.85
    d.lab(SH+EXT_STUD/2.0, J+SUB+PL/2.0, R, J+SUB+1.1, ('LEVEL 2 BOTTOM PLATE TO RIM OR', 'BLOCKING: 3-16d BOX AT 16" O.C.,', 'TABLE 602.3(1) ITEM 15'))
    d.lab(SH+IN(0.6), J*0.6, R, J*0.66, ('JOISTS PERPENDICULAR: RIM ALONG', 'THE WHOLE PANEL, 602.10.8 ITEM 1'))
    d.lab(1.95+SH+EXT_STUD/2.0, J*0.35, R, J*0.2, ('JOISTS PARALLEL: END JOIST OVER THE', 'WALL, OR FULL-DEPTH BLOCKING AT', '16" O.C. TO THE NEXT JOISTS, ITEM 2'))
    d.lab(SH+EXT_STUD*0.8, 0.0, R, -0.5, ('RIM OR BLOCKING TO LEVEL 1 TOP PLATE:', '8d COMMON TOE NAILS AT 6" O.C., ITEM 22'))
    d.lab(SH/2.0, -0.9, R, -1.15, ('WALL SHEATHING CONTINUOUS PAST THE', 'FLOOR; %s I-JOISTS AND RIM, S-102' % inches(J)))
    d.flush('S-104 detail 3')
    return d.lo


def _d4(ox, oy, slot_w):
    """PORTAL FRAME, BUILDING 2 COURTYARD WALL, ELEVATION. The door, the portal leg at the
       corner and the header over both, at the model's widths and wall height; drawn from
       inside, so the straps show."""
    ((ln, pn, door),) = [(ln, p, o) for ln in br.LINES if ln.level == 1 for p, o in br.portal_openings(ln)]
    sc = 13.5                                                             # 3/16" = 1'-0"
    d = _D(ox, oy, sc, slot_w); LAY('S-DETL')
    H = ln.wall_height; left = 1.2
    dw = door.b-door.a; leg = pn.b-pn.a
    x_door = left; x_leg = left+dw; L = left+dw+leg
    hdr_top = H-2*PL; hdr_bot = hdr_top-rco_bracing.PORTAL_HEADER[1]
    c.setStrokeColor(GREY); c.setLineWidth(0.3)
    _hatch_band(c, d.X(0), d.Y(0), d.X(L), d.Y(H), step=4.0)
    c.setStrokeColor(black); c.setLineWidth(0.8); c.rect(d.X(0), d.Y(0), L*sc, H*sc, fill=0, stroke=1)
    d.rect(x_door, 0.0, x_leg, br.D1_HEIGHT, fill=white)                             # the opening
    d.rect(x_door-2*PL, hdr_bot, L, hdr_top, lw=0.9)                                  # the header, over the leg
    d.rect(0.0, H-2*PL, L, H-PL); d.rect(0.0, H-PL, L, H)                             # double top plate
    d.rect(0.0, 0.0, L, PL)                                                            # sole plate
    for x in (x_door-2*PL, x_door-PL, x_leg, x_leg+PL, L-2*PL, L-PL):                 # king and jack studs, the leg's
        d.line(x, PL, x, hdr_bot if x_door-2*PL < x < L-2*PL-1e-9 else hdr_top, lw=0.35)
    c.setStrokeColor(black); c.setLineWidth(1.6)
    for x in (x_door-PL*0.5, x_leg+PL*0.5):                                           # the tension straps
        c.line(d.X(x), d.Y(hdr_bot+0.3), d.X(x), d.Y(hdr_bot-1.4))
    c.setLineWidth(0.5); c.setDash(0.5, 1.6)
    for x in (x_leg+PL, L-PL):                                                        # nailing at 3" o.c. down the leg
        c.line(d.X(x), d.Y(PL), d.X(x), d.Y(hdr_top))
    c.setDash()
    for x in (x_leg+leg*0.3, x_leg+leg*0.7):                                          # the two anchor bolts
        d.line(x, -0.35, x, PL*0.8, lw=0.9)
    d.line(-0.3, 0.0, L+0.3, 0.0, lw=1.0)
    _dim_h(d, x_leg, L, -0.8, '%s LEG' % fmt(leg))
    _dim_h(d, x_door, x_leg, -0.8, '%s D-1' % fmt(dw))
    R = L+0.7
    d.lab(L-0.3, H-PL, R, H+0.1, ('DOUBLE TOP PLATE TO HEADER: TWO ROWS 16d', 'SINKERS AT 3" O.C.'))
    d.lab(x_leg-0.5, (hdr_top+hdr_bot)/2.0, R, hdr_bot+0.3, ('HEADER %s x %s NET MINIMUM, OVER THE' % (inches(rco_bracing.PORTAL_HEADER[0]), inches(rco_bracing.PORTAL_HEADER[1])), 'OPENING AND THE LEG; KING STUD TO HEADER', '6-16d SINKERS'))
    d.lab(x_leg+PL*0.5, hdr_bot-1.0, R, hdr_bot-1.2, ('TENSION STRAP, %s LB, TABLE 602.10.6.4,' % '{:,}'.format(rco_bracing.strap_lb(H, dw)), 'HEADER TO JACK STUD, EACH SIDE'))
    d.lab(L-PL, H*0.45, R, H*0.42, ('SHEATHING NAILED AT %s O.C. TO ALL PORTAL' % inches(rco_bracing.PORTAL_NAIL_OC), 'FRAMING, 3" GRID TO THE HEADER'))
    if _portal_levels(br=br) == [1]:
        d.lab(x_leg+leg*0.7, PL*0.5, R, 1.4, ('TWO 1/2" ANCHOR BOLTS, 2" x 2" x 3/16"', 'PLATE WASHERS, IN THE LEG'))
    else:
        d.lab(x_leg+leg*0.7, PL*0.5, R, 1.4, ('LEVEL 1: TWO 1/2" ANCHOR BOLTS, 2" x 2" x 3/16"', 'PLATE WASHERS; LEVEL 2: TWO %d LB FRAMING' % rco_bracing.PORTAL_ANCHOR_LB, 'ANCHORS AT THE RIM, OR SHEATHING LAPPED %s' % inches(rco_bracing.PORTAL_LAP)))
    d.flush('S-104 detail 4')
    return min(d.lo, d.Y(-0.8)-6)


# ================================ the sheet ================================
def sheet_s104():
    sh = Sheet(c, "S-104", "Wall bracing plans, details", "AS NOTED"); sh.frame()
    plans_bottom, rx = _plans()
    rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    ry = _schedule(rx, ry, rw, br=br)-8
    half = (rw-0.3*inch)/2.0
    y_b = _basis(rx, ry, half)
    ry = _notes(rx+half+0.3*inch, ry, half, cols=1, _notes_text=_notes_text)
    ry = min(ry, y_b)-10
    # the details: 2 and 3 under the notes at the right; 1 and 4 under the plans
    lows = {}
    for n, fn, name, scale, sx, top, sw in (
            (2, _d2, 'ROOF CONNECTION, WALLS A AND B', '1/2" = 1\'-0"', rx, ry-1.45*inch, half),
            (3, _d3, 'FLOOR CONNECTIONS AT BRACED WALL PANELS', '1/2" = 1\'-0"', rx+half+0.3*inch, ry-1.45*inch, half),
            (1, _d1, 'CONTINUOUSLY SHEATHED BRACED WALL LINE', '3/16" = 1\'-0"', X0+0.15*inch, plans_bottom-1.85*inch, None),
            (4, _d4, 'PORTAL FRAME, BUILDING 2 COURTYARD WALL', '3/16" = 1\'-0"', None, plans_bottom-1.85*inch, None)):
        if n == 1:
            sw = (rx-0.5*inch-X0)*0.55
            lo = fn(sx+0.35*inch, top, sx+sw)
        elif n == 4:
            sx = X0+0.15*inch+(rx-0.5*inch-X0)*0.55+0.25*inch
            sw = rx-0.5*inch-sx
            lo = fn(sx+0.35*inch, top, sx+sw)
        else:
            lo = fn(sx+(0.5 if n == 2 else 0.3)*inch, top, sx+sw)
        lows[n] = lo
        _detail_title(sx, lo-0.28*inch, n, name, scale)
        assert lo-0.28*inch-10 > Y0, 'S-104 detail %d runs off the sheet: %.1f' % (n, lo)
    c.showPage()

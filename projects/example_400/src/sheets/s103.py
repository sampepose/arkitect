"""S-103 — roof framing plans and details: each building's roof over its greyed Level 2
plan, from src/roof.py; the truss bearing and gable end details; the roof design loads,
the RCO 806 attic ventilation and the notes. Every figure printed is the model's."""
import re
from arkitect.lib.draw.page import GREY, LAY, Sheet, end_plans
from arkitect.lib.draw.sheets import draw_joist_span, draw_level
from arkitect.lib.draw.text import wrap_notes
from arkitect.lib.model.regrid import EXT_STUD
from arkitect.lib.units import fmt, inches, IN
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import radon as RN
from src.sheets.a601 import FB
from src import levels
from src.building1 import B1_D, B1_W, b1_level
from src.building2 import B2_D, B2_W, b2_level
from src.criteria import WIND
from src.framing import GROUND_SNOW
from src.roof import (BC_DEAD, B1_ROOF, B2_ROOF, EAVE_OVERHANG, HEEL_NOM, INSUL_DEPTH, RAKE_OVERHANG,
                      ROOFS, ROOF_DEFLECTION, ROOF_LIVE, ROOF_PITCH, TC_DEAD, TRUSS_OC, dripline,
                      penetrations)
from arkitect.codes.ohio.rco.roof_checks import truss_lines
from arkitect.codes.ohio.rco.roof_checks import HATCH_L, HATCH_W, truss_span
from arkitect.codes.ohio.rco.attic_ventilation import EAVE_NFA, RIDGE_NFA, SLOT_STOP, VENT_CLR, VENT_RATIO, vent_runs
from src.sheets.a101 import draw_b1_stair
from src.sheets.a102 import draw_u5_stair
from src.sheets.common import draw_attic_hatch
from arkitect.lib.draw.kit import E, X0, X1, Y0, Y1, c
from arkitect.lib.draw.detail import _D, _detail_title, _hatch_band
from src.sheets.e_common import grey_context
from arkitect.lib.draw.kit import _fits
from arkitect.lib.model.geom import sloped_area
from src.roof import plan_area
from arkitect.codes.ohio.rco.roof_draw import _ventilation
from arkitect.codes.ohio.rco.roof_draw import _loads
from arkitect.lib.draw.kit import notes_block
from arkitect.lib.draw.framing_kit import _plan_title

SH  = IN(0.5)        # wall and roof sheathing, drawn
GYP = IN(0.625)      # 5/8" gypsum
PL  = IN(1.5)        # one plate
CH  = IN(3.5)        # a 2x4 truss chord, on edge in section
EAVE_INSET = EXT_STUD+IN(10)    # where an eave vent run is drawn: inside the wall, clear of the bearing label


def _roof(p, roof):
    """The trusses, gable-end trusses, bearing walls, ridge, the W4 band, the eave and
       ridge vent runs, the penetrations and the hatches of one roof on PlanDraw p,
       which is drawing at 1/8"."""
    cc = p.c
    (bay,) = roof.bays
    LAY('S-FRAM')
    cc.setStrokeColor(black); cc.setLineWidth(0.3)
    for x0, y, x1, _y in truss_lines(bay, truss_oc=TRUSS_OC):
        cc.line(p.X(x0), p.Y(y), p.X(x1), p.Y(y))
    cc.setLineWidth(1.3)                                        # the gable-end trusses, on the end walls
    for y, _nm in roof.gables:
        yy = EXT_STUD/2.0 if y < 1e-9 else y-EXT_STUD/2.0
        cc.line(p.X(bay.x0), p.Y(yy), p.X(bay.x1), p.Y(yy))
    cc.setLineWidth(1.8)                                        # the bearing walls, both side walls
    for x0, y0, x1, y1, _nm in roof.bearing:
        cc.line(p.X((x0+x1)/2.0), p.Y(y0), p.X((x0+x1)/2.0), p.Y(y1))
    dx0, dy0, dx1, dy1 = dripline(roof)                         # the roof edge, note 5
    cc.setLineWidth(0.5); cc.setDash(3, 2)
    cc.rect(p.X(dx0), p.Y(dy1), p.X(dx1)-p.X(dx0), p.Y(dy0)-p.Y(dy1), fill=0, stroke=1)
    cc.setLineWidth(0.9); cc.setDash(6, 3)                       # the ridge
    cc.line(p.X(roof.ridge_x), p.Y(0.0), p.X(roof.ridge_x), p.Y(roof.D))
    cc.setDash()
    if roof.w4_band:
        lo, hi = roof.w4_band
        LAY('S-FRAM'); cc.setStrokeColor(GREY); cc.setLineWidth(0.3)
        _hatch_band(cc, p.X(0.0), p.Y(hi), p.X(roof.W), p.Y(lo))
        cc.setStrokeColor(black); cc.setLineWidth(0.5); cc.setDash(2, 2)
        for y in (lo, hi): cc.line(p.X(0.0), p.Y(y), p.X(roof.W), p.Y(y))
        cc.setDash()
    pens = penetrations(roof)
    runs = vent_runs(roof, pens)
    run_x = lambda u: u.x if u.kind == 'RIDGE' else EAVE_INSET if u.x < 1e-9 else roof.W-EAVE_INSET
    LAY('S-FRAM'); cc.setStrokeColor(black)
    for u in runs:                                              # the eave and ridge vent runs, ticked at their stops
        X = p.X(run_x(u))
        cc.setLineWidth(2.0); cc.line(X, p.Y(u.y0), X, p.Y(u.y1))
        cc.setLineWidth(0.6)
        for y in (u.y0, u.y1): cc.line(X-2.5, p.Y(y), X+2.5, p.Y(y))
    LAY('S-ANNO-TEXT'); cc.setFillColor(black)
    # the span arrow across the middle, clear of the band
    at = roof.D/2.0
    if roof.w4_band and roof.w4_band[0] < at < roof.w4_band[1]: at = roof.w4_band[1]+4.0
    for h in roof.hatches:                          # and clear of an attic hatch and the label over it
        if h.page[1]-2.0 < at < h.page[3]+1.0: at = h.page[3]+2.0
    draw_joist_span(p, bay.x0, at, bay.x1,
                    'TRUSSES AT %s O.C.  ·  %s OUT TO OUT OF BEARING' % (inches(TRUSS_OC), fmt(roof.W)), o='h')
    cc.setFillColor(black); cc.setFont('Helvetica', 4.6)
    cc.drawString(p.X(bay.x0)+3, p.Y(2.3)-4, "TYPICAL LAYOUT — THE MANUFACTURER'S LAYOUT GOVERNS")
    cc.saveState(); cc.translate(p.X(roof.ridge_x)+4.5, p.Y(roof.D*0.2)); cc.rotate(90)
    cc.drawCentredString(0, 0, 'RIDGE  +%s NOMINAL' % fmt(levels.ridge(roof.W))); cc.restoreState()
    for x0, y0, x1, y1, nm in roof.bearing:
        cc.saveState(); cc.translate(p.X(x1 if x0 < 1 else x0)+(4.5 if x0 < 1 else -2.0), p.Y(roof.D*0.78)); cc.rotate(90)
        cc.drawCentredString(0, 0, '%s — TRUSS BEARING, 2x6, DOUBLE TOP PLATE' % nm); cc.restoreState()
    for y, nm in roof.gables:
        cc.drawCentredString(p.X(roof.W/2.0 if y < 1e-9 else roof.W*0.28), p.Y(1.3 if y < 1e-9 else y-1.2)-1.5, 'GABLE-END TRUSS — DETAIL 2')
    if roof.w4_band:
        lo, hi = roof.w4_band
        cc.setFont('Helvetica-Bold', 4.6)
        cc.drawCentredString(p.X(roof.W/2.0), p.Y((lo+hi)/2.0)+1.0,
                             'FRT ROOF SHEATHING')
        cc.setFont('Helvetica', 4.6)
        cc.drawCentredString(p.X(roof.W/2.0), p.Y((lo+hi)/2.0)-5.0, 'W4 CONTINUES TO THE ROOF DECK; NO RIDGE OR EAVE VENT IN THIS BAND')
    cc.setFont('Helvetica', 4.6)
    # the eave label toward the gable end of its run, clear of the bearing label; the ridge label at mid-run
    for kind, text, dx in (('EAVE', 'EAVE INTAKE VENT, NOTE 6', 4.5), ('RIDGE', 'RIDGE VENT, NOTE 6', -2.5)):
        u = min((u for u in runs if u.kind == kind and u.x < roof.W-1e-9), key=lambda u: u.y0)
        at = u.y0+5.5 if kind == 'EAVE' else (u.y0+u.y1)/2.0
        cc.saveState(); cc.translate(p.X(run_x(u))+dx, p.Y(at)); cc.rotate(90)
        cc.drawCentredString(0, 0, text); cc.restoreState()
    radon = RN.roof_exits(roof.name)
    for x, y, nm in radon:                                      # the radon risers, S-103 radon notes
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.6)
        cc.rect(p.X(x)-2.6, p.Y(y)-2.6, 5.2, 5.2, fill=1, stroke=1)
        cc.setFillColor(black); cc.circle(p.X(x), p.Y(y), 1.0, fill=1, stroke=0)
        cc.setFont('Helvetica', 4.2); cc.drawString(p.X(x)+4, p.Y(y)+3.5, '%s, R6' % nm)
    for x, y, nm in [q for q in pens if q not in roof.vents and q not in radon]:       # the Level 2 bath exhaust caps
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.6)
        cc.circle(p.X(x), p.Y(y), 2.2, fill=1, stroke=1)
        cc.setFillColor(black); cc.setFont('Helvetica', 4.2)
        cc.drawString(p.X(x)+3.5, p.Y(y)-6.0, '%s, NOTE 9' % nm)
    for x, y, nm in roof.vents:
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.6)
        cc.circle(p.X(x), p.Y(y), 3.0, fill=1, stroke=1); cc.circle(p.X(x), p.Y(y), 1.0, fill=1, stroke=1)
        cc.setFillColor(black); cc.setFont('Helvetica', 4.2)
        cc.drawString(p.X(x)+4, p.Y(y)+3.5, nm)
    for h in roof.hatches:
        draw_attic_hatch(p, h)


# ================================ the details ================================
def _d1(ox, oy, slot_w):
    """TRUSS BEARING AT EXTERIOR WALL. Origin: the outside face of the wall sheathing at
       the top of the plate. Everything is the model's: EXT_STUD, HEEL_NOM, INSUL_DEPTH,
       ROOF_PITCH, EAVE_OVERHANG."""
    d = _D(ox, oy, 36.0, slot_w); LAY('S-DETL')
    wall_x0 = SH; wall_x1 = SH+EXT_STUD
    d.rect(wall_x0, -2.4, wall_x1, -2*PL)                       # studs, cut
    d.rect(wall_x0, -2*PL, wall_x1, -PL); d.rect(wall_x0, -PL, wall_x1, 0.0)      # double top plate
    d.insul(wall_x0, -2.4, wall_x1, -2*PL)
    d.rect(0.0, -2.4, SH, HEEL_NOM+CH*0.0)                        # wall sheathing, up the heel
    d.rect(wall_x1, -2.4, wall_x1+GYP, -GYP)                      # interior gypsum to the ceiling
    d.rect(wall_x1+GYP, -GYP, 4.2, 0.0)                           # ceiling gypsum under the bottom chord
    d.rect(wall_x0, 0.0, 4.2, CH)                                  # bottom chord
    d.rect(wall_x0, CH, wall_x0+CH, HEEL_NOM)                      # the heel's vertical
    h0 = HEEL_NOM; rise = (4.2-wall_x0)*ROOF_PITCH
    EO = EAVE_OVERHANG; TRIM = IN(0.75)
    chord = lambda x: h0+(x-wall_x0)*ROOF_PITCH                  # the top chord's underside at page x
    deck = lambda x: chord(x)+CH*1.05                              # its top, the underside of the sheathing
    tail = -EO+TRIM+PL                                               # the tail's cut end, behind the subfascia
    d.poly([(tail, chord(tail)), (4.2, h0+rise), (4.2, h0+rise+CH*1.05), (tail, deck(tail))])   # top chord and its tail
    d.poly([(-EO+TRIM, deck(-EO+TRIM)), (4.2, deck(4.2)), (4.2, deck(4.2)+SH), (-EO+TRIM, deck(-EO+TRIM)+SH)])  # roof sheathing
    soffit = chord(tail)
    d.rect(-EO+TRIM, soffit-IN(0.5), 0.0, soffit)                    # solid soffit, fascia to the wall sheathing
    d.rect(-EO+TRIM, soffit-IN(0.5), tail, deck(-EO+TRIM)+SH)        # 2x subfascia on the tails
    d.rect(-EO, soffit-IN(1.25), -EO+TRIM, deck(-EO)+SH+IN(0.5))     # fascia trim and drip edge: the overhang's outside face
    d.rect(-EO-IN(5), deck(-EO)-IN(5), -EO, deck(-EO)-IN(0.5))       # the gutter, not counted in the overhang
    d.line(-EO, deck(-EO)+SH+IN(0.5), 4.2, deck(4.2)+SH+IN(0.5), lw=1.4)   # shingles
    blk0 = wall_x0+CH; blk1 = blk0+PL
    d.rect(blk0, 0.0, blk1, deck(blk1), dash=(2, 2))                 # the fireblock beyond: plate to sheathing, between trusses
    d.insul(blk1, CH, 4.2, CH+INSUL_DEPTH)                          # R-49 over the ceiling, inside the fireblock
    d.line(blk1, CH+INSUL_DEPTH+IN(1), 1.6, CH+INSUL_DEPTH+IN(1)+(1.6-blk1)*ROOF_PITCH, lw=0.5, dash=(2, 1.5))   # baffle
    d.line(wall_x1, -PL, wall_x1+IN(1.5), CH+IN(1), lw=1.2)        # the connector, heel to plate
    vx = blk1+IN(3)
    d.rect(vx, deck(vx)+SH+IN(0.5), vx+IN(4), deck(vx+IN(4))+SH+IN(1.5))   # shingle-over intake vent over its slot, inboard of the fireblock
    R = 4.3
    d.lab(vx+IN(2), deck(vx+IN(2))+SH+IN(1.5), R, 3.278, ('SHINGLE-OVER INTAKE VENT, ITS SLOT', 'CUT INBOARD OF THE FIREBLOCK AND', 'OVER THE BAFFLE, NOTE 6'))
    d.lab(2.6, deck(2.6), R, 2.444, ('7/16" OSB, 8d AT 6" EDGES / 12" FIELD;', 'ICE BARRIER FROM THE EAVE TO 24" INSIDE', 'THE WALL LINE, 905.1.2; ARCH. SHINGLES'))
    d.lab(3.6, h0+(3.6-wall_x0)*ROOF_PITCH+IN(1.5), R, 1.833, ('ENERGY-HEEL TRUSS AT %s O.C.,' % inches(TRUSS_OC), 'DESIGN BY THE TRUSS MANUFACTURER'))
    d.lab(wall_x0+CH/2.0, HEEL_NOM*0.6, R, 1.333, ('RAISED HEEL, %s NOMINAL: HEIGHT BY THE' % inches(HEEL_NOM), 'TRUSS DESIGN FOR FULL-DEPTH R-49 OVER', 'THE PLATE AND A 1" BAFFLE, 806.3'))
    d.lab(3.0, CH+INSUL_DEPTH*0.6, R, 0.833, ('R-49 BLOWN, %s NOMINAL, A-602;' % inches(INSUL_DEPTH), '5/8" GYPSUM CEILING, A-601 R1'))
    d.lab(wall_x1+IN(1), CH*0.5, R, 0.333, ('CONNECTOR EACH TRUSS FOR THE DESIGN', 'UPLIFT, H2.5A MINIMUM, 802.11'))
    d.lab(blk0+PL/2.0, HEEL_NOM*0.35, R, -0.056, ('FIREBLOCK ON THE WALL LINE, EVERY EAVE:', '2x BETWEEN TRUSSES, TOP PLATE TO ROOF', 'SHEATHING, 302.1(1) NOTE a, A-601 FB-5'))
    d.lab(wall_x1/2.0, -1.4, R, -0.722, ('2x6 WALL, W1 / W1R, A-601,', 'DOUBLE TOP PLATE'))
    d.lab(-EO/2.0, soffit-IN(0.5), -1.3, -2.75, ('%s EAVE TO THE OUTSIDE OF THE TRIM, NOTE 5:' % inches(EO),
                                                 '2x SUBFASCIA, FASCIA TRIM, DRIP EDGE, GUTTER;', 'SOLID SOFFIT, NO SOFFIT VENT'))
    d.flush('detail 1 label')
    return d.lo


def _d2(ox, oy, slot_w):
    """GABLE END. A section through the end wall looking along the ridge: the gable-end
       truss on the plate, its webs, the brace back to the common trusses beyond."""
    d = _D(ox, oy, 36.0, slot_w); LAY('S-DETL')
    wx0 = SH; wx1 = SH+EXT_STUD; top = 3.0
    d.rect(wx0, -2.4, wx1, -2*PL); d.insul(wx0, -2.4, wx1, -2*PL)
    d.rect(wx0, -2*PL, wx1, -PL); d.rect(wx0, -PL, wx1, 0.0)
    d.rect(0.0, -2.4, SH, top)                                     # wall sheathing continuous to the roof
    d.rect(wx1, -2.4, wx1+GYP, -GYP); d.rect(wx1+GYP, -GYP, 4.4, 0.0)
    for x in (wx0, wx0+2.0, wx0+4.0):                               # the bottom chords, cut: gable then commons
        d.rect(x, 0.0, x+PL, CH)
        d.rect(x, top-CH, x+PL, top)                                 # and the top chords under the sheathing
    d.rect(wx0, CH, wx0+PL, top-CH)                                 # the gable-end vertical web
    d.rect(wx0+PL, 0.6, wx0+PL+CH, top-CH-0.2)                      # L-brace on the web, flat
    d.poly([(wx0+PL, top-CH-0.3), (wx0+PL+PL, top-CH-0.3), (wx0+4.0, CH+PL), (wx0+4.0-PL, CH+PL)])   # diagonal brace
    d.rect(wx0+2.0+PL, 0.0, wx0+4.0, CH, dash=(2, 2))               # blocking between the chords, beyond
    RO = RAKE_OVERHANG; TRIM = IN(0.75)
    d.rect(-RO+TRIM, top, 4.4, top+SH)                               # roof sheathing, out over the ladder
    d.rect(-PL, top-CH, 0.0, top)                                     # 2x4 ladder nailer over the wall sheathing
    d.rect(-RO+TRIM+PL, top-PL, -PL, top)                             # a flat 2x4 rung
    d.rect(-RO+TRIM, top-CH, -RO+TRIM+PL, top)                        # 2x rake board
    d.rect(-RO+TRIM, top-CH-IN(0.5), -PL, top-CH)                     # solid soffit
    d.rect(-RO, top-CH-IN(1.25), -RO+TRIM, top+SH+IN(0.5))            # rake trim and drip edge: the overhang's outside face
    d.line(-RO, top+SH+IN(0.5), 4.4, top+SH+IN(0.5), lw=1.4)
    d.insul(wx0+PL, CH, 4.4, CH+INSUL_DEPTH*0.7)
    R = 4.5
    d.lab(-RO/2.0, top+SH/2.0, R, 4.278, ('7/16" OSB; %s RAKE TO THE OUTSIDE OF' % inches(RO),
                                          'THE TRIM, NOTE 5: 2x4 LADDER AT 24" O.C. ON A 2x4',
                                          'NAILER THROUGH THE SHEATHING TO THE', 'GABLE TRUSS; 2x RAKE BOARD, TRIM,',
                                          'DRIP EDGE, SOLID SOFFIT'))
    d.lab(wx0+PL/2.0, top-CH-0.6, R, 2.722, ('GABLE-END TRUSS ON THE END-WALL PLATE,', 'VERTICAL WEBS AT 24" O.C.; WALL SHEATHING', 'CONTINUOUS TO THE TOP CHORD, NAILED TO IT'))
    d.lab(wx0+2.2, CH+PL+0.6, R, 2.056, ('2x4 DIAGONAL BRACES, WEB TO THE CEILING', 'DIAPHRAGM, AT 6\'-0" O.C. ALONG THE GABLE,', 'WITH 2x4 BLOCKING BETWEEN THE FIRST', 'TWO TRUSSES — BCSI-B3'))
    d.lab(wx0+PL+CH/2.0, 1.3, R, 1.222, ('2x4 L-BRACE ON WEBS OVER 4\'-0" TALL',))
    d.lab(wx0+3.0, CH/2.0, R, 0.222, ('COMMON TRUSSES AT %s O.C. BEYOND' % inches(TRUSS_OC),))
    d.lab(wx1/2.0, -1.6, R, -0.278, ('2x6 END WALL, W1 / W1R, A-601',))
    d.flush('detail 2 label')
    return d.lo






def _notes_text():
    span = truss_span(B1_ROOF.bays[0])
    caps = ' AND '.join(nm.replace(' ROOF CAP', '') for r in ROOFS for _x, _y, nm in penetrations(r) if 'ROOF CAP' in nm)
    _sub = lambda t: re.sub(r'^(\d+)([A-Z])\.', lambda m: m.group(1)+m.group(2).lower()+'.', t, count=1)
    return [_sub(n.upper()) for n in (
        f'1. Roof framing: prefabricated metal-plate-connected wood trusses at {inches(TRUSS_OC)} o.c. spanning the '
        f'north wall to the south wall, {fmt(B1_ROOF.W)} out to out of bearing and {fmt(span)} clear in both '
        f'buildings, {round(ROOF_PITCH*12)}:12, ridge front to back, raised heel. The trusses drawn are the typical layout. The manufacturer\'s '
        'engineered layout and sealed truss design drawings, RCO 802.10.1, are submitted before fabrication and govern '
        'truss positions, webs, plates, heel height, bearing, uplift and bracing; designed to the loads tabulated.',

        '2. Bearing: trusses bear on the double top plates of the two 2x6 side walls only. No roof load on the house\'s '
        'stair wall, on Building 2\'s bearing wall or on any partition: hold every interior wall clear of the bottom chord '
        'with a slip clip. Connector at each truss end for the design uplift, H2.5A minimum, RCO 802.11; 2x blocking '
        'between trusses on the plate, S-104 detail 2.',

        '3. Bracing: temporary and permanent bracing per BCSI-B1, B2 and B3 and the truss design; gable ends braced to '
        'the ceiling diaphragm, detail 2; continuous lateral bracing of webs where the design calls for it.',

        '4. Sheathing and covering: 7/16" OSB, 8d common at 6" edges / 12" field, H-clips; ice barrier from the eave to '
        '24" inside the exterior wall line, 905.1.2; Class A architectural shingles, A-601 R1.',

        '4a. Underlayment, RCO 905.1.1: one layer of ASTM D226 Type I felt, or a synthetic underlayment '
        'listed for the shingle, lapped 2" at horizontal joints and 4" at ends, fastened as its maker '
        'requires. The ice barrier of note 4 comes first at the eaves.',

        '4b. Wind, RCO 905.2.4 and 905.2.6: shingles listed to ASTM D7158 Class H (or D3161 Class F) for the '
        'Vult 115 mph, exposure B of G-001, laid to the maker\'s high-wind instructions -- six fasteners per '
        'shingle, corrosion-resistant roofing nails long enough to go 3/4" into or through the sheathing. Hand '
        'seal every shingle the maker asks be sealed.',

        '4c. Starter, caps and penetrations: the maker\'s starter strip at every eave and rake; the maker\'s '
        'ridge cap over the note 6 ridge vent, of the same line as the field shingle. Flash every penetration of '
        'note 9 with its own listed flashing and shingle it in. The Unit 3 stair canopy takes the same '
        'underlayment and field shingle, headwall flashed to its wall: A-603 note 7.',

        '4d. Drip edge, RCO 905.2.8.5: corrosion-resistant metal at every eave and rake, 2" onto the deck and '
        '1/4" below the sheathing, segments lapped 2", fastened at 12" o.c.; at the eave it lies UNDER the '
        'underlayment, at the rake OVER it.',

        f'5. Roof edges: {inches(EAVE_OVERHANG)} max at every eave and {inches(RAKE_OVERHANG)} max at every rake, measured to the '
        'outside face of the trim, drip edge included: RCO Table 302.1(1), A-601. Eaves: 2x subfascia on the truss tails, '
        'fascia trim, drip edge, solid soffit; every eave fireblocked on its wall line from the top plate to the roof '
        'sheathing, A-601 FB-5. Rakes: 2x4 ladder at 24" o.c. on a 2x4 nailer fastened through the wall sheathing to the '
        'gable-end truss, 2x rake board, trim, drip edge, solid soffit. Gutters on all four eaves, each falling to one '
        'downspout on a splash block, DS-1 to DS-4, C-103.',

        f'6. Ventilation, RCO 806: net free area per attic as tabulated, not less than 1/{VENT_RATIO} of the attic floor. '
        f'Intake is a shingle-over eave vent on both eaves, its slot cut inboard of the note 5 fireblock, rated not less than {EAVE_NFA:g} sq in '
        f'per lineal foot, and exhaust is a ridge vent rated not less than {RIDGE_NFA:g} sq in per lineal foot. Both run as '
        f'drawn: {round(SLOT_STOP*12)}" short of each gable end, and broken {round(VENT_CLR*12)}" either side of a roof penetration '
        f'within {round(VENT_CLR*12)}" of the vent line. The tabulated area is the eave and ridge vents, the attic\'s only vents: no '
        'gable vent, which would short-circuit the ridge vent. Soffits are not vented. Baffles at every truss space hold 1" clear above the '
        'insulation, 806.3. Submit the vent products\' net free areas with the roofing.',

        f'7. Attic access, RCO 807.1: one {inches(HATCH_W)} x {inches(HATCH_L)} rough opening with 30" headroom in each attic, '
        'drawn: Unit 1 and Unit 3, each in its Level 2 hall. Between two trusses, '
        f'the {inches(HATCH_W)} across them; 2x4 headers, an insulation dam, a weatherstripped and insulated cover, RCO 1102.2.4.',

        f'8. Insulation: R-49 blown over the ceiling, {inches(INSUL_DEPTH)} nominal, full depth over the plates on the '
        'raised heel, A-602; 5/8" gypsum ceiling, A-601 R1.',

        f'9. Roof penetrations: the Level 2 bath exhaust caps {caps}, drawn, each over its fan, M-101 and M-102; radon risers {RN.RISERS[0].mark} and {RN.RISERS[-1].mark}, drawn, radon notes. Plumbing vents through '
        f'the roof are located by the plumber, not less than {round(VENT_CLR*12)}" from the ridge and eave vent lines and from the '
        'attic hatches, never through a truss member. All flashed.',
    )]


def _radon_block(x, y, width, ylow, size=5.6, lead=7.4):
    """RADON: src/radon.py's risers, one schedule row each, then its notes R1 to R9."""
    LAY('S-ANNO-TEXT')
    heading = 'RADON — PASSIVE SUB-SLAB DEPRESSURIZATION, %s' % RN.BASIS
    _fits(heading, 'Helvetica-Bold', 7.2, width, 'radon heading')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
    c.setLineWidth(0.6); c.setStrokeColor(black); c.line(x, y, x+width, y); y -= lead+2
    cols = (0.0, 0.42, 1.25, 3.0, 4.1)          # inches from x: mark, serves, beside, riser, exit; top at the right
    head = ('RISER', 'SERVES', 'IN THE', 'TEE, X / Y', 'ROOF EXIT, X / Y', 'TOP')
    c.setFont('Helvetica-Bold', size)
    for k, t in enumerate(head[:-1]):
        nxt = cols[k+1]*inch if k+1 < len(cols) else width-pdfmetrics.stringWidth(head[-1], 'Helvetica-Bold', size)-4
        _fits(t, 'Helvetica-Bold', size, nxt-cols[k]*inch-3, 'radon schedule head')
        c.drawString(x+cols[k]*inch, y, t)
    c.drawRightString(x+width, y, head[-1]); y -= lead
    c.setFont('Helvetica', size)
    for row in RN.schedule_rows():
        for k, t in enumerate(row[:-1]):
            nxt = cols[k+1]*inch if k+1 < len(cols) else width-pdfmetrics.stringWidth(row[-1], 'Helvetica', size)-4
            _fits(t, 'Helvetica', size, nxt-cols[k]*inch-3, 'radon schedule cell')
            c.drawString(x+cols[k]*inch, y, t)
        c.drawRightString(x+width, y, row[-1]); y -= lead
    foot = 'X FROM THE NORTH FACE, Y FROM THE FRONT FACE, S-101; TOP OF THE PIPE ABOVE FINISHED GRADE'
    _fits(foot, 'Helvetica', size, width, 'radon schedule foot')
    c.drawString(x, y, foot); y -= lead+3
    for t in wrap_notes(RN.notes_text(FB), width, size):
        _fits(t, 'Helvetica', size, width, 'radon note')
        c.drawString(x, y, t); y -= lead
    assert y+lead >= ylow, 'S-103 radon block runs off the sheet by %.2f in' % ((ylow-y-lead)/inch)
    return y



# ================================ the sheet ================================
def sheet_s103():
    sh = Sheet(c, "S-103", "Roof framing plans, details", "AS NOTED"); sh.frame()
    top = Y1-0.8*inch
    ox1 = X0+1.6*inch; oy = top-B1_D*E
    ox2 = ox1+B1_W*E+2.9*inch
    lv = b1_level(2)
    lv.over_plan = lambda pp: draw_b1_stair(pp, 2)
    lv.overlay = lambda p: (_roof(p, B1_ROOF),
                            grey_context(p, B1_W, B1_D, 'OAK AVENUE', 'COURTYARD', '396 OAK AVE', '404 OAK AVE', top_off=1.6))
    draw_level(c, lv, ox1, oy, sc=E)
    lv2 = b2_level(2)
    lv2.over_plan = lambda pp: draw_u5_stair(pp, B2_W, above=False)
    lv2.overlay = lambda p: (_roof(p, B2_ROOF),
                             grey_context(p, B2_W, B2_D, 'COURTYARD', 'PARKING AND ALLEY', '396 OAK AVE', '404 OAK AVE', top_off=4.6))
    draw_level(c, lv2, ox2, oy, sc=E)
    end_plans()
    _plan_title(ox1, oy, 'BUILDING 1 — ROOF FRAMING  ·  LEVEL 2 BELOW, GRAY')
    _plan_title(ox2, oy, 'BUILDING 2 — ROOF FRAMING  ·  LEVEL 2 BELOW, GRAY')
    # the right column: loads and ventilation side by side, the notes under them
    rx = ox2+B2_W*E+1.7*inch; rw = X1-0.15*inch-rx      # 11.2 in: the details under the plans need 5 in each
    ry = Y1-0.35*inch
    half = (rw-0.3*inch)/2.0
    y_a = _loads(rx, ry, half, bc_dead=BC_DEAD, ground_snow=GROUND_SNOW, roof_deflection=ROOF_DEFLECTION, roof_live=ROOF_LIVE, tc_dead=TC_DEAD, wind=WIND)
    y_b = _ventilation(rx+half+0.3*inch, ry, half, roofs=ROOFS, penetrations=penetrations,
                       roof_areas=lambda r: (plan_area(r), sloped_area(plan_area(r), ROOF_PITCH)))
    ry = notes_block(rx, min(y_a, y_b)-8, rw, _notes_text(), 'ROOF FRAMING NOTES', 'S-ANNO-TEXT', 'roof framing note')
    assert ry > Y0, 'S-103 notes run off the sheet'
    _radon_block(rx, ry-14, rw, Y0+0.1*inch)
    # the two details under the plans, each with its title directly beneath it
    rowB = oy-1.25*inch
    left_w = (rx-0.5*inch-X0-0.3*inch)/2.0
    for n, fn, name, sx, dx in ((1, _d1, 'TRUSS BEARING AT EXTERIOR WALL', X0+0.15*inch, 0.75),
                                (2, _d2, 'GABLE END', X0+0.15*inch+left_w+0.3*inch, 0.7)):
        lo = fn(sx+dx*inch, rowB-2.55*inch, sx+left_w)
        _detail_title(sx, lo-0.28*inch, n, name, '1/2" = 1\'-0"')
        assert lo-0.28*inch-10 > Y0, 'S-103 detail %d runs off the sheet: %.1f' % (n, lo)
    c.showPage()

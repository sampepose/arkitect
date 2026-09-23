"""S-103 — roof framing plans and structural details: each building's roof over its
greyed Level 2 plan, from src/roof.py; five details; the roof design loads, the RCO
806 attic ventilation and the notes. Every figure printed is the model's."""
import re
from lib.draw.page import GREY, LAY, Sheet, end_plans
from lib.draw.sheets import draw_joist_span, draw_level
from lib.draw.text import wrap_notes
from lib.model.regrid import EXT_STUD, PART_STUD
from lib.units import fmt, inches, IN
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import levels
from src import downspouts as DS
from src import radon as RN
from src.fireblocking import FB
from src.building1 import _b1_level, U1_STAIR_WALL
from src.building2 import B2_W, b2_level
from src.foundation import STRIP_D, STRIP_W
from src.framing import B1_FLOOR, F1_JOIST, GROUND_SNOW, JOIST_OC, SUBFLOOR
from src.criteria import WIND
from src.roof import (BC_DEAD, B1_ROOF, B2_ROOF, HEEL_NOM, INSUL_DEPTH, EAVE_OVERHANG, RAKE_OVERHANG,
                      dripline, rake, ROOFS, ROOF_DEFLECTION, ROOF_LIVE, ROOF_PITCH, TC_DEAD, TRUSS_OC,
                      W4_BAND, penetrations)
from codes.ohio.rco.roof_checks import truss_lines
from codes.ohio.rco.roof_checks import HATCH_L, HATCH_W, truss_span
from codes.ohio.rco.attic_ventilation import EAVE_NFA, RIDGE_NFA, SLOT_STOP, VENT_CLR, VENT_RATIO, vent_runs
from src.sheets.common import draw_attic_hatch
from lib.draw.kit import E, X0, X1, Y0, Y1, c
from src.sheets.e_common import grey_context
from lib.draw.kit import _fits
from src.sheets.plans import B1_DRAWING, draw_u5_stair
from lib.draw.detail import _D, _detail_title, _hatch_band
from lib.draw.framing_kit import _in0
from lib.model.geom import sloped_area
from src.roof import plan_area
from codes.ohio.rco.roof_draw import _ventilation
from codes.ohio.rco.roof_draw import _loads
from lib.draw.kit import notes_block
from lib.draw.framing_kit import _plan_title

SH  = IN(0.5)        # wall and roof sheathing, drawn
GYP = IN(0.625)      # 5/8" gypsum
PL  = IN(1.5)        # one plate
CH  = IN(3.5)        # a 2x4 truss chord, on edge in section


# which side of its symbol each radon exit's label sits, off the bath cap labels near it
RADON_LABEL = {'RR-1': ('r', -8.0), 'RR-2': ('l', 3.5)}

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
                             'FRT ROOF SHEATHING %s EACH SIDE OF W4 — NO OPENING OR PENETRATION, A-601' % fmt(W4_BAND))
        cc.setFont('Helvetica', 4.6)
        cc.drawCentredString(p.X(roof.W/2.0), p.Y((lo+hi)/2.0)-5.0, 'W4 CONTINUES TO THE ROOF DECK; NO RIDGE OR EAVE VENT IN THIS BAND')
    cc.setFont('Helvetica', 4.6)
    # the eave label toward the gable end of its run, clear of the bearing label; the ridge label at mid-run
    for kind, text, dx in (('EAVE', 'EAVE INTAKE VENT, NOTE 7', 4.5), ('RIDGE', 'RIDGE VENT, NOTE 7', -2.5)):
        u = min((u for u in runs if u.kind == kind and u.x < roof.W-1e-9), key=lambda u: u.y0)
        at = u.y0+5.5 if kind == 'EAVE' else (u.y0+u.y1)/2.0
        cc.saveState(); cc.translate(p.X(run_x(u))+dx, p.Y(at)); cc.rotate(90)
        cc.drawCentredString(0, 0, text); cc.restoreState()
    radon = RN.roof_exits(roof.name)
    for x, y, nm in radon:                                      # the radon risers, S-103 radon notes
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.6)
        cc.rect(p.X(x)-2.6, p.Y(y)-2.6, 5.2, 5.2, fill=1, stroke=1)
        cc.setFillColor(black); cc.circle(p.X(x), p.Y(y), 1.0, fill=1, stroke=0)
        cc.setFont('Helvetica', 4.2)
        side, dy = RADON_LABEL.get(nm.split()[0], ('r', 3.5))          # clear of the bath caps' labels beside them
        (cc.drawString if side == 'r' else cc.drawRightString)(p.X(x)+(4 if side == 'r' else -4), p.Y(y)+dy, '%s, R6' % nm)
    for x, y, nm in [q for q in pens if q not in roof.vents and q not in radon]:  # the Level 2 bath exhaust caps
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.6)
        cc.circle(p.X(x), p.Y(y), 2.2, fill=1, stroke=1)
        cc.setFillColor(black); cc.setFont('Helvetica', 4.2)
        cc.drawString(p.X(x)+3.5, p.Y(y)-6.0, '%s, %s' % (nm, 'M-101' if roof is B1_ROOF else 'M-102'))
    for x, y, nm in roof.vents:
        cc.setFillColor(white); cc.setStrokeColor(black); cc.setLineWidth(0.6)
        cc.circle(p.X(x), p.Y(y), 3.0, fill=1, stroke=1); cc.circle(p.X(x), p.Y(y), 1.0, fill=1, stroke=1)
        cc.setFillColor(black); cc.setFont('Helvetica', 4.2)
        cc.drawString(p.X(x)+4, p.Y(y)+3.5, nm)
    for h in roof.hatches:
        draw_attic_hatch(p, h)


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
    d.lab(vx+IN(2), deck(vx+IN(2))+SH+IN(1.5), R, 3.278, ('SHINGLE-OVER INTAKE VENT, ITS SLOT', 'CUT INBOARD OF THE FIREBLOCK AND', 'OVER THE BAFFLE, NOTE 7'))
    d.lab(2.6, deck(2.6), R, 2.444, ('7/16" OSB, 8d AT 6" EDGES / 12" FIELD;', 'ICE BARRIER FROM THE EAVE TO 24" INSIDE', 'THE WALL LINE, 905.1.2; ARCH. SHINGLES'))
    d.lab(3.6, h0+(3.6-wall_x0)*ROOF_PITCH+IN(1.5), R, 1.833, ('ENERGY-HEEL TRUSS AT %s O.C.,' % inches(TRUSS_OC), 'DESIGN BY THE TRUSS MANUFACTURER'))
    d.lab(wall_x0+CH/2.0, HEEL_NOM*0.6, R, 1.333, ('RAISED HEEL, %s NOMINAL: HEIGHT BY THE' % inches(HEEL_NOM), 'TRUSS DESIGN FOR FULL-DEPTH R-49 OVER', 'THE PLATE AND A 1" BAFFLE, 806.3'))
    d.lab(3.0, CH+INSUL_DEPTH*0.6, R, 0.833, ('R-49 BLOWN, %s NOMINAL, A-602;' % inches(INSUL_DEPTH), '5/8" GYPSUM CEILING, A-601 R1'))
    d.lab(wall_x1+IN(1), CH*0.5, R, 0.333, ('CONNECTOR EACH TRUSS FOR THE DESIGN', 'UPLIFT, H2.5A MINIMUM, 802.11'))
    d.lab(blk0+PL/2.0, HEEL_NOM*0.35, R, -0.056, ('FIREBLOCK ON THE WALL LINE, EVERY EAVE:', '2x BETWEEN TRUSSES, TOP PLATE TO ROOF', 'SHEATHING, 302.1(1) NOTE a, A-601 FB-7'))
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
    rear = rake(B1_ROOF, 'REAR')
    d.lab(-RO/2.0, top+SH/2.0, R, 4.278, ('7/16" OSB; %s RAKE TO THE OUTSIDE OF' % inches(RO),
                                          'THE TRIM, %s AT BUILDING 1\'S REAR GABLE,' % inches(rear),
                                          'NOTE 5: 2x4 LADDER AT 24" O.C. ON A 2x4',
                                          'NAILER THROUGH THE SHEATHING TO THE', 'GABLE TRUSS; 2x RAKE BOARD, TRIM,',
                                          'DRIP EDGE, SOLID SOFFIT'))
    d.lab(wx0+PL/2.0, top-CH-0.6, R, 2.722, ('GABLE-END TRUSS ON THE END-WALL PLATE,', 'VERTICAL WEBS AT 24" O.C.; WALL SHEATHING', 'CONTINUOUS TO THE TOP CHORD, NAILED TO IT'))
    d.lab(wx0+2.2, CH+PL+0.6, R, 2.056, ('2x4 DIAGONAL BRACES, WEB TO THE CEILING', 'DIAPHRAGM, AT 6\'-0" O.C. ALONG THE GABLE,', 'WITH 2x4 BLOCKING BETWEEN THE FIRST', 'TWO TRUSSES — BCSI-B3'))
    d.lab(wx0+PL+CH/2.0, 1.3, R, 1.222, ('2x4 L-BRACE ON WEBS OVER 4\'-0" TALL',))
    d.lab(wx0+3.0, CH/2.0, R, 0.222, ('COMMON TRUSSES AT %s O.C. BEYOND' % inches(TRUSS_OC),))
    d.lab(wx1/2.0, -1.6, R, -0.278, ('2x6 END WALL, W1 / W1R, A-601',))
    d.flush('detail 2 label')
    return d.lo


def _d3(ox, oy, slot_w):
    """INTERIOR BEARING WALL W3 AT F1. Origin: the wall's centerline at the top of its
       plate, F1_PLATE. The two F1 bays meet on it; the wall above is a partition."""
    d = _D(ox, oy, 36.0, slot_w); LAY('S-DETL')
    hw = PART_STUD/2.0
    d.rect(-hw, -2.4, hw, -2*PL); d.insul(-hw, -2.4, hw, -2*PL)
    d.rect(-hw, -2*PL, hw, -PL); d.rect(-hw, -PL, hw, 0.0)
    rc = levels.F1_PLATE-levels.F1_CEILING-levels.F1_GYPSUM         # the RC-1 channel
    for sgn in (-1, 1):
        d.rect(sgn*hw, -2.4, sgn*(hw+GYP), -rc-levels.F1_GYPSUM)     # W3's 5/8" both faces, to the ceiling
        d.rect(sgn*(hw+GYP), -rc-levels.F1_GYPSUM, sgn*1.8, -rc)     # the rated ceiling, one layer
        d.line(sgn*(hw+GYP), -rc/2.0, sgn*1.8, -rc/2.0, lw=0.4, dash=(2, 1.5))   # resilient channel allowance
        x0, x1 = (sgn*IN(0.25), sgn*1.8)
        d.rect(x0, 0.0, x1, F1_JOIST)                                # the I-joist, bearing from its side
        d.rect(x0, 0.0, x1, IN(1.5)); d.rect(x0, F1_JOIST-IN(1.5), x1, F1_JOIST)   # flanges
    d.rect(-hw, 0.0, hw, F1_JOIST, dash=(2, 2))                       # squash blocks, beyond
    d.rect(-1.8, F1_JOIST, 1.8, F1_JOIST+SUBFLOOR)                    # subfloor
    top = F1_JOIST+SUBFLOOR
    d.rect(-hw, top, hw, top+PL); d.rect(-hw, top+PL, hw, top+1.2)    # the partition above, sill and studs
    R = 1.95
    d.lab(1.2, F1_JOIST/2.0, R, 1.444, ('F1 %s I-JOISTS FROM BOTH BAYS, %s' % (inches(F1_JOIST), inches(IN(1.75))), 'BEARING MINIMUM EACH, BLOCKING AT THE', 'BEARING; %s T&G SUBFLOOR' % _in0(SUBFLOOR)))
    d.lab(0.0, F1_JOIST*0.6, R, 0.833, ('SQUASH BLOCKS UNDER EVERY POINT LOAD,', 'PLATE TO SUBFLOOR'))
    d.lab(0.0, top+0.8, R, 2.056, ('PARTITION ABOVE, NOT BEARING',))
    d.lab(hw+GYP/2.0, -1.2, R, -0.167, ('W3, UL U305: 2x4 AT 16" O.C., ONE 5/8"', 'UL TYPE SCX LAYER EACH FACE, CONTINUOUS', 'TO THE RATED CEILING, A-601, RCO 302.3.1'))
    d.lab(1.5, -rc-levels.F1_GYPSUM/2.0, R, -0.944, ('RATED CEILING: RC-1 AND %d x %s %s,' % (levels.F1_LAYERS, _in0(levels.F1_LAYER), levels.F1_BOARD), '%s — A-601' % levels.F1_LISTING))
    d.lab(0.0, -2.3, R, -1.556, ('WALL TO ITS %s x %s STRIP — S-101' % (inches(STRIP_W), inches(STRIP_D)),))
    d.flush('detail 3 label')
    return d.lo


def _d4(ox, oy, slot_w):
    """EXTERIOR WALL AT THE F1 FLOOR EDGE, joists parallel: Building 2's side walls,
       whose rim carries the roof-bearing wall above. Origin: outside face of the wall
       sheathing at F1_PLATE."""
    d = _D(ox, oy, 36.0, slot_w); LAY('S-DETL')
    wx0 = SH; wx1 = SH+EXT_STUD; rim = IN(1.25)
    d.rect(wx0, -2.4, wx1, -2*PL); d.insul(wx0, -2.4, wx1, -2*PL)
    d.rect(wx0, -2*PL, wx1, -PL); d.rect(wx0, -PL, wx1, 0.0)
    rc = levels.F1_PLATE-levels.F1_CEILING-levels.F1_GYPSUM
    d.rect(wx1, -2.4, wx1+GYP, -rc-levels.F1_GYPSUM)
    d.rect(wx1+GYP, -rc-levels.F1_GYPSUM, 2.6, -rc)
    d.line(wx1+GYP, -rc/2.0, 2.6, -rc/2.0, lw=0.4, dash=(2, 1.5))
    d.rect(wx0, 0.0, wx0+rim, F1_JOIST)                               # the rim board
    jx = wx0+JOIST_OC                                                  # the first joist, parallel, cut
    d.rect(jx-IN(1.25), 0.0, jx+IN(1.25), IN(1.5)); d.rect(jx-IN(1.25), F1_JOIST-IN(1.5), jx+IN(1.25), F1_JOIST)
    d.rect(jx-IN(0.22), IN(1.5), jx+IN(0.22), F1_JOIST-IN(1.5))
    d.rect(wx0+rim, 0.0, jx-IN(1.25), F1_JOIST, dash=(2, 2))          # full-depth blocking, beyond
    d.insul(wx0+rim, IN(1.5), wx0+rim+EXT_STUD, F1_JOIST-IN(1.5))     # floor-edge insulation
    d.rect(wx0, F1_JOIST, 2.6, F1_JOIST+SUBFLOOR)                     # subfloor
    top = F1_JOIST+SUBFLOOR
    d.rect(wx0, top, wx1, top+PL); d.rect(wx0, top+PL, wx1, top+1.3); d.insul(wx0, top+PL, wx1, top+1.3)
    d.rect(0.0, -2.4, SH, top+1.3)                                      # sheathing continuous across the rim
    d.rect(wx1, top+PL, wx1+GYP, top+1.3)
    R = 2.7
    d.lab(wx0+rim/2.0, F1_JOIST*0.55, R, 1.111, ('RIM BOARD, OR FULL-DEPTH BLOCKING, RATED', 'BY THE MANUFACTURER FOR THE ROOF-BEARING', 'WALL ABOVE: BUILDING 2\'S SIDE WALLS, S-102'))
    d.lab(jx, F1_JOIST/2.0, R, 0.444, ('F1 I-JOISTS PARALLEL TO THE WALL, FIRST AT', '%s; FULL-DEPTH BLOCKING AT 24" O.C.' % inches(JOIST_OC)))
    d.lab(wx0+rim+EXT_STUD/2.0, F1_JOIST*0.3, R, -0.111, ('FLOOR EDGE INSULATED AND AIR-SEALED,', 'RCO 1102.2.8; %s T&G SUBFLOOR' % _in0(SUBFLOOR)))
    d.lab(wx1/2.0, top+0.8, R, 1.833, ('2x6 WALL ABOVE, W1 / W1R, R-21; SHEATHING', 'CONTINUOUS ACROSS THE RIM, NAILED TO', 'BOTH PLATES AND THE RIM'))
    d.lab(wx1/2.0, -1.5, R, -0.833, ('2x6 WALL BELOW, W1R, DOUBLE TOP PLATE',))
    d.lab(1.6, -rc-levels.F1_GYPSUM/2.0, R, -1.389, ('F1 CEILING, %s' % levels.F1_LISTING.replace('ICC-ES ', ''),))
    d.flush('detail 4 label')
    return d.lo


def _d5(ox, oy, slot_w):
    """UNIT 1 STAIR WELL FRAMING, in plan, from src/framing.py's well and the stair wall:
       the double header on the wall, the trimmers, the hangers, the guard posts."""
    (w,) = B1_FLOOR.wells
    bay = B1_FLOOR.bays[0]
    sc = 27.0
    x0, y0, y1 = w.x0, w.y0, w.y1
    ext = 2.4                                                          # feet of floor shown past the well
    # a plan: y increases DOWN the page, so the origin is the well's top-left and Y flips
    oy = oy-(y1-y0+2*ext)*sc-0.15*inch                                  # oy came in as the plan's TOP
    d = _D(ox, oy, sc, slot_w); LAY('S-DETL')
    d.Y = lambda v, oy=oy, sc=sc, y1=y1+ext: oy+(y1-v)*sc
    def wall(wx0, wy0, wx1, wy1):
        c.setFillColor(GREY); c.setStrokeColor(black); c.setLineWidth(0.6)
        c.rect(d.X(wx0), d.Y(wy1), (wx1-wx0)*sc, (wy1-wy0)*sc, fill=1, stroke=1)
    wall(0.0, y0-ext, x0, y1+ext)                                       # the Sage wall
    wall(U1_STAIR_WALL[0], max(U1_STAIR_WALL[1], y0-ext), U1_STAIR_WALL[2], y1+ext)  # the stair wall, L1 bearing, to the plan edge
    c.setStrokeColor(black); c.setLineWidth(0.3)
    n = 1
    while y0-ext+n*JOIST_OC < y1+ext:                                   # the joists, running in x
        y = y0-ext+n*JOIST_OC
        if y0 < y < y1: d.line(w.header_x1, y, x0+ext+3.2, y, lw=0.35)   # tails, from the header
        else:           d.line(x0, y, x0+ext+3.2, y, lw=0.35)
        n += 1
    for y in (y0, y1):                                                  # double trimmers
        d.line(x0, y, w.header_x0, y, lw=1.2); d.line(x0, y+IN(1.75)*(1 if y == y0 else -1), w.header_x0, y+IN(1.75)*(1 if y == y0 else -1), lw=1.2)
    for x in (w.header_x0, w.header_x1):                                # double header on the stair wall
        d.line(x, y0, x, y1, lw=1.3)
    c.setFillColor(white)
    for y in (y0, y1):                                                  # hangers, trimmer to header
        c.rect(d.X(w.header_x0)-1.8, d.Y(y)-1.8, 3.6, 3.6, fill=1, stroke=1)
    n = 1
    while y0-ext+n*JOIST_OC < y1+ext:                                   # hangers, tails to header
        y = y0-ext+n*JOIST_OC
        if y0 < y < y1: c.rect(d.X(w.header_x1)-1.8, d.Y(y)-1.8, 3.6, 3.6, fill=1, stroke=1)
        n += 1
    c.setStrokeColor(black); c.setLineWidth(0.5); c.setDash(3, 2)
    c.rect(d.X(x0), d.Y(y1), (w.header_x0-x0)*sc, (y1-y0)*sc, fill=0, stroke=1); c.setDash()
    for y in (y0+0.3, (y0+y1)/2.0, y1-0.3):                             # guard posts along the open edge
        c.setFillColor(black); c.rect(d.X(w.header_x1)+1.5, d.Y(y)-2.2, 4.4, 4.4, fill=1, stroke=1)
    c.setFillColor(black); c.setFont('Helvetica', 4.6)
    c.drawCentredString(d.X((x0+w.header_x0)/2.0), d.Y((y0+y1)/2.0), 'WELL %s x %s' % (fmt(w.header_x0-x0), fmt(y1-y0)))
    c.drawCentredString(d.X((x0+w.header_x0)/2.0), d.Y((y0+y1)/2.0)-6, 'OPEN TO LEVEL 1')
    R = w.header_x1+1.4
    d.lab(w.header_x0+IN(1.75), y0+0.8, R, y0+0.15, ('DOUBLE %s I-JOIST HEADER ON THE STAIR' % inches(bay.joist), 'WALL, FACE-MOUNT HANGERS EACH END'))
    d.lab(x0+1.0, y0+IN(1.0), R, y0+1.1, ('DOUBLE TRIMMERS AT THE WELL\'S SIDES',))
    d.lab(w.header_x1+0.8, y0+JOIST_OC*2, R, y0+2.0, ('TAIL JOISTS ON FACE-MOUNT HANGERS;', 'JOISTS AT %s O.C., THE TYPICAL LAYOUT' % inches(JOIST_OC)))
    d.lab(w.header_x1+IN(2), (y0+y1)/2.0, R, (y0+y1)/2.0+0.3, ('GUARD POSTS: 4x4 THROUGH-BOLTED TO THE', 'HEADER WITH 2x BLOCKING, NOT THE SUBFLOOR', 'ALONE — A-001 NOTE 13'))
    d.lab((U1_STAIR_WALL[0]+U1_STAIR_WALL[2])/2.0, y1+1.2, R, y1+1.35, ('STAIR WALL, BEARING, TO ITS STRIP — S-101',))
    d.lab(x0/2.0, y1+1.8, R, y1+2.1, ('SAGE WALL, W1',))
    d.flush('detail 5 label')
    return min(d.lo, d.Y(y1+ext))


# ================================ the right column ================================






def _radon_block(x, y, width, ylow, size=5.6, lead=7.4):
    """RADON: src/radon.py's risers, one schedule row each, then its notes R1 to R9."""
    LAY('S-ANNO-TEXT')
    heading = 'RADON — PASSIVE SUB-SLAB DEPRESSURIZATION, %s' % RN.BASIS
    _fits(heading, 'Helvetica-Bold', 7.2, width, 'radon heading')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
    c.setLineWidth(0.6); c.setStrokeColor(black); c.line(x, y, x+width, y); y -= lead+2
    cols = (0.0, 0.42, 1.25, 1.75, 2.85)          # inches from x: mark, serves, beside, riser, exit; top at the right
    head = ('RISER', 'SERVES', 'BESIDE', 'TEE, X / Y', 'ROOF EXIT, X / Y', 'TOP')
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
    foot = 'X FROM THE SAGE FACE, Y FROM THE FRONT FACE, S-101; TOP OF THE PIPE ABOVE FINISHED GRADE'
    _fits(foot, 'Helvetica', size, width, 'radon schedule foot')
    c.drawString(x, y, foot); y -= lead+3
    for t in wrap_notes(RN.notes_text(FB, W4_BAND), width, size):
        _fits(t, 'Helvetica', size, width, 'radon note')
        c.drawString(x, y, t); y -= lead
    assert y+lead >= ylow, 'S-103 radon block runs off the sheet by %.2f in' % ((ylow-y-lead)/inch)
    return y


def _notes_text():
    span = truss_span(B1_ROOF.bays[0])
    _sub = lambda t: re.sub(r'^(\d+)([A-Z])\.', lambda m: m.group(1)+m.group(2).lower()+'.', t, count=1)
    return [_sub(n.upper()) for n in (
        f'1. Roof framing: prefabricated metal-plate-connected wood trusses at {inches(TRUSS_OC)} o.c. spanning the '
        f'Sage wall to the adjacent-parcel wall, {fmt(B1_ROOF.W)} out to out of bearing and {fmt(span)} clear in both '
        'buildings, 4:12, ridge front to back, raised heel. The trusses drawn are the typical layout. The manufacturer\'s '
        'engineered layout and sealed truss design drawings, RCO 802.10.1, are submitted before fabrication and govern '
        'truss positions, webs, plates, heel height, bearing, uplift and bracing; designed to the loads tabulated.',

        '2. Bearing: trusses bear on the double top plates of the two 2x6 side walls only. No roof load on W4, on the '
        'Units 2/3 or Units 4/5 bearing walls or on any partition: hold every interior wall clear of the bottom chord '
        'with a slip clip. Connector at each truss end for the design uplift, H2.5A minimum, RCO 802.11; 2x blocking '
        'between trusses on the plate.',

        '3. Bracing: temporary and permanent bracing per BCSI-B1, B2 and B3 and the truss design; gable ends braced to '
        'the ceiling diaphragm, detail 2; continuous lateral bracing of webs where the design calls for it.',

        f'4. Sheathing and covering: 7/16" OSB, 8d common at 6" edges / 12" field, H-clips; fire-retardant-treated '
        f'sheathing for {fmt(W4_BAND)} each side of W4 with fasteners sized for FRT values and a Class C minimum covering '
        'there, A-601; ice barrier from the eave to 24" inside the exterior wall line, 905.1.2; architectural '
        'shingles, A-202.',

        '4a. Underlayment, RCO 905.1.1: one layer of ASTM D226 Type I felt, or a synthetic underlayment '
        'listed for the shingle, lapped 2" at horizontal joints and 4" at ends, fastened as its maker '
        'requires. The ice barrier of note 4 comes first at the eaves.',

        '4b. Wind, RCO 905.2.4 and 905.2.6: shingles listed to ASTM D7158 Class H (or D3161 Class F) for the '
        'Vult 115 mph, exposure B of G-001, laid to the maker\'s high-wind instructions -- six fasteners per '
        'shingle, corrosion-resistant roofing nails long enough to go 3/4" into or through the sheathing. Hand '
        'seal every shingle the maker asks be sealed. The covering over the note 4 band is Class C at least.',

        '4c. Starter, caps and penetrations: the maker\'s starter strip at every eave and rake; the maker\'s '
        'ridge cap over the note 7 ridge vent, of the same line as the field shingle. Flash every penetration of '
        'note 9 with its own listed flashing and shingle it in. Each stair canopy takes the same underlayment '
        'and field shingle, headwall flashed to its wall: A-604 note 7.',

        '4d. Drip edge, RCO 905.2.8.5: corrosion-resistant metal at every eave and rake, 2" onto the deck and '
        '1/4" below the sheathing, segments lapped 2", fastened at 12" o.c.; at the eave it lies UNDER the '
        'underlayment, at the rake OVER it.',

        f'5. Roof edges: {inches(EAVE_OVERHANG)} max at every eave and {inches(RAKE_OVERHANG)} max at every rake, {inches(rake(B1_ROOF, "REAR"))} max at Building 1\'s rear '
        'rake, measured to the outside face of the trim, drip edge included (RCO Table 302.1(1), C-101). '
        'Eaves: 2x subfascia on the truss tails, fascia trim, drip edge, solid soffit; every eave fireblocked on its wall line from '
        'the top plate to the roof sheathing, A-601 FB-7. Rakes: 2x4 ladder at 24" o.c. on a 2x4 nailer fastened through the wall '
        'sheathing to the gable-end truss, 2x rake board, trim, drip edge, solid soffit; at Building 1\'s rear gable the W1R '
        'exterior Type X runs unbroken to the roof sheathing behind the nailer. Gutters on both eaves, each falling to one '
        'downspout on a splash block, DS-1 to DS-4, C-101 and C-103. Gutter guards the full length of all '
        f'{len(DS.GUARDED)} gutters, per the specifications; never under the shingles or the note 7 intake vent.',

        '6. W4 is two walls, W4A and W4B; each attic\'s trusses bear on its own unit\'s '
        'walls and are nailed to its own W4 wall, never the other\'s (RCO 302.2.6); each wall '
        'continues to the roof deck, A-601. No roof opening, penetration or ridge- or eave-vent cut in the band drawn.',

        f'7. Ventilation, RCO 806: net free area per attic as tabulated, not less than 1/{VENT_RATIO} of the attic floor. '
        f'Intake is a shingle-over eave vent on both eaves, its slot cut inboard of the note 5 fireblock, rated not less than {EAVE_NFA:g} sq in '
        f'per lineal foot, and exhaust is a ridge vent rated not less than {RIDGE_NFA:g} sq in per lineal foot. Both run as '
        f'drawn: {round(SLOT_STOP*12)}" short of each gable end, stopped at the edge of each W4 band, and broken '
        f'{round(VENT_CLR*12)}" either side of a roof penetration within {round(VENT_CLR*12)}" of the vent line. The tabulated '
        'area is the eave and ridge vents, the attic\'s only vents: no gable vent, which would short-circuit the ridge vent. Soffits are not vented. Baffles at every truss '
        'space hold 1" clear above the insulation, 806.3. Submit the vent products\' net free areas with the roofing.',

        f'8. Attic access, RCO 807.1: one {inches(HATCH_W)} x {inches(HATCH_L)} rough opening with 30" headroom in each attic, '
        'drawn: Unit 1 in its Level 2 hall, A-102; Unit 3 and Unit 5 in the living room ceiling, A-102 and A-103. '
        f'Between trusses, the {inches(HATCH_W)} across them; 2x4 headers, an insulation dam, a weatherstripped and insulated '
        'cover, RCO 1102.2.4.',

        f'9. Roof penetrations: stack E through the roof at the rear wall, drawn, P-601 1d; the Level 2 bath exhaust '
        f'caps, drawn, M-101 and M-102; radon risers {RN.RISERS[0].mark} to {RN.RISERS[-1].mark}, drawn, radon notes; stacks B and C offset in their '
        f'own attics at least {fmt(W4_BAND)} from W4, P-601 2a, located by the plumber outside the band; all flashed.',

        f'10. Insulation: R-49 blown over the ceiling, {inches(INSUL_DEPTH)} nominal, full depth over the plates on the '
        'raised heel, A-602; 5/8" gypsum ceiling, A-601 R1.',

    )]


# ================================ the sheet ================================
def sheet_s103():
    sh = Sheet(c, "S-103", "Roof framing, structural details", "AS NOTED"); sh.frame()
    top = Y1-0.8*inch
    ox1 = X0+0.95*inch; oy1 = top-48*E
    ox2 = ox1+26*E+1.35*inch; oy2 = top-28*E
    lv = _b1_level(2, [], [], [], units=[], annotate=False, **B1_DRAWING)
    lv.overlay = lambda p: (_roof(p, B1_ROOF),
                            grey_context(p, 26, 48, 'S ELM AVENUE', 'REAR YARD', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=1.6))
    draw_level(c, lv, ox1, oy1, sc=E)
    lv2 = b2_level(2)
    lv2.over_plan = lambda pp: draw_u5_stair(pp, B2_W, above=False)
    lv2.overlay = lambda p: (_roof(p, B2_ROOF),
                             grey_context(p, B2_W, 28, 'COURTYARD', 'PARKING AND ALLEY', 'SAGE AVENUE', 'ADJACENT PARCEL', top_off=7.5))
    draw_level(c, lv2, ox2, oy2, sc=E)
    end_plans()
    _plan_title(ox1, oy1, 'BUILDING 1 — ROOF FRAMING  ·  LEVEL 2 WALLS BELOW, GRAY')
    _plan_title(ox2, oy2, 'BUILDING 2 — ROOF FRAMING  ·  LEVEL 2 WALLS BELOW, GRAY')
    # the right column: loads and ventilation side by side, the notes under them
    rx = ox2+26*E+0.9*inch; rw = X1-0.15*inch-rx
    ry = Y1-0.35*inch
    half = (rw-0.3*inch)/2.0
    y_a = _loads(rx, ry, half, bc_dead=BC_DEAD, ground_snow=GROUND_SNOW, roof_deflection=ROOF_DEFLECTION, roof_live=ROOF_LIVE, tc_dead=TC_DEAD, wind=WIND)
    y_b = _ventilation(rx+half+0.3*inch, ry, half, roofs=ROOFS, penetrations=penetrations,
                       roof_areas=lambda r: (plan_area(r), sloped_area(plan_area(r), ROOF_PITCH)))
    ry = min(y_a, y_b)-8
    ry = notes_block(rx, ry, rw, _notes_text(), 'ROOF FRAMING NOTES', 'S-ANNO-TEXT', 'roof framing note')
    plan_bottom = oy1-0.95*inch
    # the details: 1 and 2 under the notes at the right, 3 and 4 under the plans, 5
    # under 1 and 2 — each with its title directly beneath it
    half = (rw-0.35*inch)/2.0
    rowA = ry-0.45*inch
    rowB = plan_bottom-0.35*inch
    left_w = (rx-0.6*inch-X0-0.15*inch-0.3*inch)/2.0
    lows = {}
    for n, fn, name, scale, sx, top, dy, dx, sw in (
            (1, _d1, 'TRUSS BEARING AT EXTERIOR WALL', '1/2" = 1\'-0"', rx, rowA, 2.55, 0.62, half),
            (2, _d2, 'GABLE END', '1/2" = 1\'-0"', rx+half+0.35*inch, rowA, 2.55, 0.55, half),
            (3, _d3, 'INTERIOR BEARING WALL W3 AT F1', '1/2" = 1\'-0"', X0+0.15*inch, rowB, 2.35, 1.5, left_w),
            (4, _d4, 'EXTERIOR WALL AT THE F1 FLOOR EDGE', '1/2" = 1\'-0"', X0+0.15*inch+left_w+0.3*inch, rowB, 2.35, 0.5, left_w),
            (5, _d5, 'UNIT 1 STAIR WELL FRAMING, PLAN', '3/8" = 1\'-0"', rx, None, 0.0, 0.45, half)):
        if top is None:
            top = min(lows[1], lows[2])-0.55*inch
            lo = fn(sx+dx*inch, top, sx+sw)
        else:
            lo = fn(sx+dx*inch, top-dy*inch, sx+sw)
        lows[n] = lo
        _detail_title(sx, lo-0.28*inch, n, name, scale)
        assert lo-0.28*inch-10 > Y0, 'S-103 detail %d runs off the sheet: %.1f' % (n, lo)
    # the radon block: right of detail 5, under detail 2, down to the frame
    _radon_block(rx+half+0.35*inch, lows[2]-0.28*inch-9-0.4*inch, half, Y0+0.1*inch)
    c.showPage()

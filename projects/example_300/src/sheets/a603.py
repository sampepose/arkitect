"""A-603 — the grouping separation in section: W4A and W4B, two UL U305 walls back to
back, from the slab to the deck at the ridge, then the ceiling line, the floor line and
the base at 1-1/2" = 1'-0", and the notes. Every height is src/separation.py's, read from
src/levels.py; the fireblock tags are the fireblocking model's."""
from lib.draw.page import LGREY, POCHE, Sheet
from lib.draw.text import wrap_notes
from lib.units import IN, fmt, inches
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from src import levels
from src import separation as w4
from src.foundation import GRAVEL_T, RETARDER_MIL, SLAB_T, STRIP_D, STRIP_W
from src.framing import JOIST_OC
from src.roof import TRUSS_OC
from lib.draw.kit import X0, X1, Y0, Y1, c
from lib.draw.detail import _Det, _title

DETAIL = 1.5*72.0         # 1-1/2" = 1'-0": points per foot
KEY = 0.375*72.0          # 3/8" = 1'-0"
P = w4.PLATE


def _in(v):
    """Inches as the sheets write them: 5/8", 14" — inches() without its "0-"."""
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


def _z(v):
    return '+%s' % fmt(v)


def _walls(d, z0, z1, batt=True):
    """Both walls over z0..z1: each one's inner 5/8" layer at the joint, its 2x4 studs,
       its own unit-face layer. The inner layers touch, so nothing lies between them."""
    for w in w4.WALLS:
        s = w.side
        d.rect(0, z0, s*w4.CORE, z1)
        d.rect(s*w4.CORE, z0, s*(w4.CORE+w4.STUD), z1)
        if batt: d.hatch(s*w4.CORE, z0, s*(w4.CORE+w4.STUD), z1)
        d.rect(s*(w4.CORE+w4.STUD), z0, s*w4.FACE, z1)


def _plate(d, w, z0, n=1):
    for k in range(n):
        d.rect(w.side*w4.CORE, z0+k*P, w.side*(w4.CORE+w4.STUD), z0+(k+1)*P)


def _ijoist(d, cx, z0, depth):
    fw = IN(0.875)
    d.rect(cx-fw, z0, cx+fw, z0+IN(1.5)); d.rect(cx-fw, z0+depth-IN(1.5), cx+fw, z0+depth)
    d.rect(cx-IN(0.1875), z0+IN(1.5), cx+IN(0.1875), z0+depth-IN(1.5))


def _w5(d, s, z0, z1):
    d.rect(s*w4.FACE, z0, s*(w4.FACE+w4.W5_T), z1, fill=None, lw=0.4, dash=(3, 2))


# ============================== 1  the key section ==============================
def _key(cx, top, left, right):
    xw = 3.0
    S, sb, kb, hw = w4.SLAB, w4.SLAB-SLAB_T, w4.SLAB-STRIP_D, STRIP_W/2.0
    d = _Det(cx, top, KEY, xw, kb-IN(4), w4.DECK+IN(10), left, right, size=5.0, gap=8.0, sheet='A-603')
    d.poly([(-xw, S), (xw, S), (xw, sb), (hw, sb), (hw, kb), (-hw, kb), (-hw, sb), (-xw, sb)], fill=POCHE)
    for w in w4.WALLS:
        s = w.side
        d.rect(s*w4.FACE, w.plate, s*xw, levels.SUBFLOOR_TOP, fill=LGREY, lw=0.4)     # its floor
        d.rect(s*w4.FACE, w.ceiling, s*xw, w.plate, lw=0.3)                          # its ceiling
        d.rect(s*w4.FACE, levels.UPPER_CEILING, s*xw, w4.L2_TOP, lw=0.3)             # its upper ceiling
    d.rect(-xw, w4.DECK, xw, w4.DECK+IN(0.5), fill=LGREY, lw=0.4)
    d.line(-xw, w4.DECK+IN(1.5), xw, w4.DECK+IN(1.5), lw=1.2)
    _walls(d, S, w4.DECK, batt=False)
    for w in w4.WALLS:
        d.hatch(w.side*w4.CORE, S, w.side*(w4.CORE+w4.STUD), w4.DECK, step=2.4)
        for _nm, z0, z1 in w4.fireblocks(w):
            d.rect(w.side*w4.CORE, z0, w.side*(w4.CORE+w4.STUD), z1, fill=POCHE, lw=0.3)
    c.setFillColor(black)
    for s, z, t in ((-1, (S+levels.F2_CEILING)/2, 'UNIT 1'), (-1, (levels.FF2+levels.UPPER_CEILING)/2, 'UNIT 1'),
                    (1, (S+levels.F1_CEILING)/2, 'UNIT 2'), (1, (levels.FF2+levels.UPPER_CEILING)/2, 'UNIT 3'),
                    (-1, (w4.L2_TOP+w4.DECK)/2, 'UNIT 1 ATTIC'), (1, (w4.L2_TOP+w4.DECK)/2, 'UNITS 2 / 3 ATTIC')):
        c.setFont('Helvetica-Bold', 5.6); c.drawCentredString(d.X(s*(xw+w4.FACE)/2), d.Y(z), t)
    c.setFont('Helvetica', 5.0); c.setStrokeColor(black); c.setLineWidth(0.4)
    def dim(x, z0, z1, text):
        d.line(x, z0, x, z1, lw=0.4)
        for z in (z0, z1): d.line(x-0.12, z-0.12, x+0.12, z+0.12, lw=0.6)
        c.saveState(); c.translate(d.X(x)-3, d.Y((z0+z1)/2)); c.rotate(90)
        c.setFillColor(black); c.drawCentredString(0, 0, text); c.restoreState()
    for t, h in w4.unsupported(w4.WALLS[0]):
        dim(-xw-0.45, t.z0, t.z1, '%s %s' % (t.name, fmt(h)))
    dim(-xw-1.35, w4.SLAB, w4.DECK, 'EACH WALL SLAB TO DECK %s — PLATFORM-FRAMED, NO TIER OVER %s'
        % (fmt(w4.DECK-w4.SLAB), fmt(w4.STUD_MAX)))
    assert d.X(-xw-1.35)-8 >= left, "A-603 key section dimensions run off the sheet"
    d.lab(0, w4.DECK-P, 'R', ('ROOF DECK %s AT THE RIDGE: FRT SHEATHING NAILED' % _z(w4.DECK),
                              'TO BOTH RAKED TOP PLATES — A-601'))
    d.lab(w4.WALLS[1].side*w4.CORE/2, w4.L2_TOP, 'R', ('FIREBLOCK, CEILING LINE: EACH WALL\'S TOP PLATES',
                                                       'AND ITS ATTIC SOLE — DETAIL 2'))
    d.lab(0, (w4.WALLS[1].plate+levels.SUBFLOOR_TOP)/2, 'R',
          ('FIREBLOCK, FLOOR LINE: EACH WALL CLOSED AT ITS OWN',
           'PLATE, W4A %s, W4B %s — DETAIL 3' % (_z(w4.WALLS[0].plate), _z(w4.WALLS[1].plate))))
    d.lab(0, (w4.SLAB+w4.WALLS[0].plate)/2, 'R', ('W4A AND W4B, %s U305 WALLS BACK TO BACK,' % w4.RATING,
                                                  '%s FINISHED; INNER LAYERS TOUCH' % _in(w4.FINISHED)))
    d.lab(0, S+P/2, 'R', ('FIREBLOCK, BASE: BOTH SOLE PLATES ON THE ONE', 'FS STRIP, %s — DETAIL 4' % _z(S)))
    return d.flush('key section')


# ============================== 2  the ceiling line ==============================
def _ceiling(cx, top, left, right):
    ids, tags, _zones = w4.fireblock_model()
    xw = IN(20); L = w4.L2_TOP
    d = _Det(cx, top, DETAIL, xw, levels.UPPER_CEILING-IN(12), L+IN(18), left, right, sheet='A-603')
    _walls(d, d.zlo, d.zhi)
    for w in w4.WALLS:
        s = w.side
        _plate(d, w, L-2*P, 2); _plate(d, w, L)                       # double top plate, attic sole
        d.rect(s*w4.FACE, levels.UPPER_CEILING, s*xw, L)              # its 5/8" ceiling
        d.rect(s*w4.FACE, L, s*(w4.FACE+P), L+IN(3.5))                # its first truss bottom chord
        d.hatch(s*(w4.FACE+P), L, s*xw, d.zhi, step=4.0)              # R-49
        _w5(d, s, d.zlo, levels.UPPER_CEILING)
    d.lab(-(w4.FACE+P/2), L+IN(1.75), 'L', ('UNIT 1\'S FIRST TRUSS, ITS BOTTOM CHORD NAILED TO W4A\'S',
                                            'TOP PLATES; TRUSSES AT %s O.C. BEYOND, S-103. NOTHING' % _in(TRUSS_OC),
                                            'OF UNIT 1 REACHES W4B, RCO 302.2.6'))
    d.lab(-xw*0.55, L+IN(9), 'L', ('R-49 BLOWN, A-602',))
    d.lab(-xw*0.75, levels.UPPER_CEILING+levels.UPPER_GYPSUM/2, 'L',
          ('%s GYPSUM CEILING, A-601 R1, %s, TIGHT TO W4A' % (_in(levels.UPPER_GYPSUM), _z(levels.UPPER_CEILING)),))
    d.lab(-(w4.FACE+w4.W5_T/2), d.zlo+IN(4), 'L', ('W5 WHERE OCCURS, TO ITS OWN DOUBLE TOP PLATE;', tags['W5_PLATES']))
    d.lab(0, d.zhi-IN(3), 'R', ('BOTH ATTIC TIERS, 2x4 AT 16" O.C., EACH TO ITS RAKED DOUBLE TOP PLATE; THE ROOF',
                               'SHEATHING IS NAILED TO BOTH, RCO 302.2.6 EXCEPTION 2 — A-601 ROOF JUNCTION'))
    d.lab(w4.CORE/2, d.zhi-IN(9), 'R', ('THE TWO INNER 5/8" LAYERS TOUCH: EACH WALL IS CONTINUOUS TO THE ROOF',
                                        'SHEATHING, RCO 302.2.3, AND NO SPACE LIES BETWEEN THEM'))
    d.lab(w4.CORE+w4.STUD/2, L+P, 'R', ('EACH WALL\'S ATTIC SOLE PLATE ON ITS OWN DOUBLE TOP PLATE, %s;' % _z(L),
                                        tags['W4_CEILING']))
    d.lab(w4.FACE+P/2, L+IN(1.75), 'R', ('UNITS 2 / 3\' FIRST TRUSS ON W4B: THE SAME',))
    d.lab(w4.CORE+w4.STUD/2, d.zlo+IN(4), 'R', ('LEVEL 2 TIERS, %s TO %s' % (_z(levels.SUBFLOOR_TOP), _z(L)),))
    return d.flush('ceiling line')


# ============================== 3  the floor line ==============================
def _floor(cx, top, left, right):
    ids, tags, _zones = w4.fireblock_model()
    xw = IN(20)
    a, b = w4.WALLS
    d = _Det(cx, top, DETAIL, xw, levels.F2_CEILING-IN(9), levels.FF2+IN(9), left, right, gap=(10.0, 0.55*inch), sheet='A-603')
    _walls(d, d.zlo, d.zhi)
    for w in w4.WALLS:
        s = w.side
        jcx = s*(w4.CORE+w4.STUD+JOIST_OC)
        if w.floor == 'F1':
            g = levels.F1_LAYER
            d.hatch(s*(w4.CORE+w4.RIM_T), w.plate, jcx-s*IN(0.875), w.plate+IN(6.25))
            d.rect(s*w4.FACE, w.ceiling, s*xw, w.ceiling+g); d.rect(s*w4.FACE, w.ceiling+g, s*xw, w.ceiling+2*g)
            d.line(s*w4.FACE, w.plate-levels.F1_CHANNEL/2, s*xw, w.plate-levels.F1_CHANNEL/2, lw=0.4, dash=(2, 1.5))
        else:
            d.rect(s*w4.FACE, w.ceiling, s*xw, w.plate)
        _plate(d, w, w.plate-2*P, 2)                                   # its double top plate
        x0, x1, z0, z1 = w4.rim(w)
        d.rect(x0, z0, x1, z1)                                         # its rim, on its own plate
        d.rect(x1, z0+IN(1.5), jcx-s*IN(0.875), z1-IN(1.5), fill=None, lw=0.4, dash=(2, 2))
        _ijoist(d, jcx, z0, w.joist)
        d.rect(s*w4.CORE, z1, s*xw, levels.SUBFLOOR_TOP)               # its subfloor
        _plate(d, w, levels.SUBFLOOR_TOP)                              # its Level 2 sole plate
        d.rect(s*w4.FACE, levels.SUBFLOOR_TOP, s*xw, levels.FF2, lw=0.3)
        _w5(d, s, d.zlo, w.ceiling); _w5(d, s, levels.FF2, d.zhi)
    xr = xw+IN(2)
    d.line(-(w4.CORE+w4.RIM_T), a.plate, xr, a.plate, lw=0.3, dash=(1.5, 1.5))
    d.line(w4.CORE, b.plate, xr, b.plate, lw=0.3, dash=(1.5, 1.5))
    d.line(xr, a.plate-IN(1), xr, b.plate+IN(1), lw=0.5)
    for z in (a.plate, b.plate): d.line(xr-IN(0.5), z-IN(0.5), xr+IN(0.5), z+IN(0.5), lw=0.8)
    d.lab(-(w4.FACE+w4.W5_T/2), d.zlo+IN(3), 'L', ('W5 WHERE OCCURS: PER STORY, OWN PLATES, STUDS',
                                                   'AGAINST W4A\'S FACE LAYER, THE FLOOR OVER IT;', tags['W5_PLATES']))
    d.lab(-xw*0.75, a.ceiling+levels.F2_GYPSUM/2, 'L', ('F2 CEILING, %s GYPSUM, %s, TIGHT TO W4A' % (_in(levels.F2_GYPSUM), _z(a.ceiling)),))
    d.lab(-(w4.CORE+w4.RIM_T/2), (a.plate+a.plate+a.joist)/2, 'L',
          ('F2 RIM, UNIT 1: 1-1/4" LSL, %s DEEP, NAILED ON W4A\'S OWN' % _in(a.joist),
           'DOUBLE TOP PLATE, %s; W4A\'S INNER 5/8" LAYER RUNS UP' % _z(a.plate),
           'ITS FACE, SO THAT WALL STAYS CONTINUOUS;', tags['RIM']))
    d.lab(-(w4.CORE+w4.STUD+JOIST_OC), a.plate+a.joist*0.3, 'L', ('F2 %s I-JOISTS PARALLEL TO THE WALL, S-102;' % _in(a.joist),
                                                                  'FULL-DEPTH BLOCKING, RIM TO FIRST JOIST, AT 24" O.C.'))
    d.lab(-xw*0.8, levels.SUBFLOOR_TOP-levels.SUBFLOOR/2, 'L', ('%s T&G SUBFLOOR; UNIT 1\'S LEVEL 2 SOLE PLATE' % _in(levels.SUBFLOOR),
                                                               'STANDS ON IT. FINISHED FLOOR L2 %s' % _z(levels.FF2)))
    d.lab(w4.CORE/2, d.zhi-IN(3), 'R', ('THE TWO INNER 5/8" LAYERS TOUCH AND EACH RUNS PAST ITS OWN FLOOR:',
                                       'NOTHING OF EITHER UNIT CROSSES THE JOINT, RCO 302.2.6'))
    d.lab(w4.CORE+w4.STUD/2, levels.SUBFLOOR_TOP+P/2, 'R', ('EACH WALL\'S LEVEL 2 SOLE PLATE ON ITS OWN SUBFLOOR, %s' % _z(levels.SUBFLOOR_TOP),))
    d.lab(w4.CORE+w4.STUD/2, b.plate-P, 'R', ('W4B\'S DOUBLE TOP PLATE, %s, AT THE F1 PLATE; W4A\'S IS %s;' % (_z(b.plate), _z(a.plate)),
                                              tags['W4_FLOOR']))
    d.lab(w4.CORE+w4.RIM_T/2, (b.plate+b.plate+b.joist)/2, 'R',
          ('F1 RIM, UNITS 2 / 3: 1-1/4" LSL, %s DEEP, NAILED ON W4B\'S OWN DOUBLE TOP' % _in(b.joist),
           'PLATE; W4B\'S INNER LAYER RUNS UP ITS FACE'))
    d.lab(xr, (a.plate+b.plate)/2, 'R', ('%s PLATE STEP: W4A CARRIES F2 FROM %s, W4B CARRIES F1 FROM %s;' % (_in(w4.PLATE_STEP), _z(a.plate), _z(b.plate)),
                                         'ONE FINISHED FLOOR, %s, A-301' % _z(levels.FF2)))
    d.lab(xw*0.75, b.ceiling+levels.F1_LAYER, 'R', ('F1 CEILING, %s: %s MINERAL WOOL, RC-1, %d LAYER %s %s,' % (levels.F1_LISTING, _in(levels.F1_INSUL_T), levels.F1_LAYERS, _in(levels.F1_LAYER), levels.F1_BOARD),
                                                    'TIGHT TO W4B\'S FACE LAYER — A-601'))
    return d.flush('floor line')


# ============================== 4  the base ==============================
def _base(cx, top, left, right):
    ids, tags, _zones = w4.fireblock_model()
    xw = IN(20)
    S, sb, kb, hw = w4.SLAB, w4.SLAB-SLAB_T, w4.SLAB-STRIP_D, STRIP_W/2.0
    d = _Det(cx, top, DETAIL, xw, kb-IN(6), S+IN(18), left, right, sheet='A-603')
    for s in (-1, 1):
        d.rect(s*hw, sb-GRAVEL_T, s*xw, sb, lw=0.3)
        d.hatch(s*hw, sb-GRAVEL_T, s*xw, sb, step=2.2)
    d.poly([(-xw, S), (xw, S), (xw, sb), (hw, sb), (hw, kb), (-hw, kb), (-hw, sb), (-xw, sb)], fill=POCHE)
    vr = IN(0.35)
    for a_, b_ in (((xw, sb-vr), (hw+vr, sb-vr)), ((hw+vr, sb-vr), (hw+vr, kb-vr)), ((hw+vr, kb-vr), (-hw-vr, kb-vr)),
                   ((-hw-vr, kb-vr), (-hw-vr, sb-vr)), ((-hw-vr, sb-vr), (-xw, sb-vr))):
        d.line(a_[0], a_[1], b_[0], b_[1], lw=0.7, dash=(3, 1.5))
    for s in (-1, 1):
        d.circle(s*(hw-IN(3.25)), kb+IN(3.25), IN(0.25))
        d.rect(s*w4.FACE, S, s*xw, levels.FF1, lw=0.3)
    _walls(d, S, d.zhi)
    for w in w4.WALLS:
        s = w.side
        _plate(d, w, S)                                                  # its PT sole plate
        bx = s*(w4.CORE+w4.STUD/2)
        d.line(bx, S-IN(7), bx, S+P+IN(0.75), lw=1.2)                    # its anchor bolt
        d.line(bx, S-IN(7), bx+s*IN(1.5), S-IN(7), lw=1.2)
        d.rect(bx-IN(1), S+P, bx+IN(1), S+P+IN(0.25), lw=0.4)
        _w5(d, s, levels.FF1, d.zhi)
    d.lab(-(w4.FACE+w4.W5_T/2), d.zhi-IN(4), 'L', ('W5 WHERE OCCURS: SOLE PLATE ON THE SLAB;', tags['W5_PLATES']))
    d.lab(-xw*0.6, S+levels.FLOOR_FINISH/2, 'L', ('FLOOR FINISH TO W4A\'S FACE LAYER;', 'FINISHED FLOOR L1 %s' % _z(levels.FF1)))
    d.lab(-xw*0.8, S-SLAB_T/2, 'L', ('S1, A-601: %s SLAB ON A %d-MIL VAPOR RETARDER,' % (_in(SLAB_T), RETARDER_MIL),
                                     'LAPPED UNDER THE STRIP — S-101 NOTE 2'))
    d.lab(-xw*0.85, sb-GRAVEL_T/2, 'L', ('%s CLEAN AGGREGATE' % _in(GRAVEL_T),))
    d.lab(w4.CORE+w4.STUD/2, d.zhi-IN(4), 'R', ('LEVEL 1 TIERS: 2x4 AT 16" O.C., 3-1/2" EcoBatt, %s TO EACH WALL\'S OWN PLATE' % _z(S),))
    d.lab(w4.CORE/2, d.zhi-IN(9), 'R', ('BOTH INNER 5/8" LAYERS RUN TO THE SLAB: EACH WALL IS CONTINUOUS FROM',
                                        'THE FOUNDATION, RCO 302.2.3'))
    d.lab(w4.CORE+w4.STUD/2, S+P/2, 'R', ('PRESERVATIVE-TREATED 2x4 SOLE PLATE TO EACH WALL, RCO 317.1;',
                                          'FIREBLOCK — EACH W4 SOLE PLATE, A-601 %s' % ids['W4']))
    d.lab(w4.CORE+w4.STUD/2, S-IN(4), 'R', ('1/2" ANCHOR BOLTS TO EACH PLATE, 7" INTO THE STRIP, 6\'-0" O.C. MAXIMUM, TWO PER',
                                            'PLATE, 12" MAXIMUM FROM EACH END — S-101 NOTE 6, RCO 403.1.6'))
    d.lab(hw*0.5, kb+IN(3.25), 'R', ('ONE FS STRIP UNDER BOTH WALLS, %s x %s, TWO #4 CONTINUOUS AT THE BOTTOM, 3" CLEAR' % (_in(STRIP_W), _in(STRIP_D)),
                                     '— S-101 NOTE 4; A SHARED FOUNDATION IS RCO 302.2.6 EXCEPTION 1. A BUILDING DRAIN',
                                     'CROSSING BELOW IT IS SLEEVED, P-101 NOTE 6'))
    return d.flush('base')


# ============================== the notes ==============================
def notes():
    ids, _tags, zones = w4.fireblock_model()
    a, b = w4.WALLS
    (t1, h1), (t2, h2), (t3, h3) = w4.unsupported(b)
    return [
     "1.  W4A CARRIES UNIT 1'S FLOORS AND CEILINGS, W4B CARRIES UNITS 2 / 3'. EACH IS %s, %s, SLAB TO ROOF SHEATHING; %s FINISHED "
     "BACK TO BACK. ASSEMBLY AND LISTING: A-601 AND A-001 NOTE 4b."
     % (w4.LISTING, w4.RATING, _in(w4.FINISHED)),
     "2.  STRUCTURAL INDEPENDENCE, RCO 302.2.6 — EACH DWELLING UNIT IS STRUCTURALLY INDEPENDENT. NO JOIST, RIM, BLOCKING, HANGER, LEDGER, "
     "STRAP, TRUSS OR FASTENER OF ONE UNIT TOUCHES THE OTHER UNIT'S WALL. THE TWO WALLS SHARE ONLY THE FS STRIP (EXCEPTION 1), THE ROOF "
     "SHEATHING NAILED TO BOTH RAKED TOP PLATES (EXCEPTION 2) AND THE FLASHING (EXCEPTION 4).",
     "3.  PLATFORM FRAMING — THREE TIERS ON EACH WALL'S OWN PLATES, DETAIL 1; NO TIER PASSES THE %s OF RCO TABLE 602.3(5)."
     % fmt(w4.STUD_MAX),
     "4.  FLOOR LINE — EACH UNIT'S RIM, SUBFLOOR AND LEVEL 2 SOLE PLATE ON ITS OWN WALL, THE INNER LAYER CONTINUOUS PAST THE FLOOR, "
     "DETAIL 3. THE PLATES STEP %s; THE FINISHED FLOOR DOES NOT, A-301." % _in(w4.PLATE_STEP),
     "5.  FIREBLOCKING — AS TAGGED ON DETAILS 1 TO 3; A-601 FIREBLOCKING, FROM %s." % ids['W4'],
     "6.  BASE — A PRESERVATIVE-TREATED SOLE PLATE TO EACH WALL, RCO 317.1, BOTH ANCHORED TO THE ONE FS STRIP PER S-101 NOTE 6, RCO "
     "403.1.6 (DETAIL 4). NEITHER CAVITY HOLDS PLUMBING, MECHANICAL EQUIPMENT, DUCT OR VENT; SERVICES RUN IN THE W5 CHASE ON EACH UNIT FACE.",
    ]


# ============================== A-603 ==============================
def sheet_a603():
    sh = Sheet(c, "A-603", "W4 separation sections", "AS NOTED"); sh.frame()
    col = X0+5.55*inch                  # the key section and the notes left of it, the details right
    ty = Y1-0.25*inch
    _title(X0, ty, 1, 'W4A / W4B — SLAB TO DECK AT THE RIDGE', '3/8" = 1\'-0"')
    lo = _key(X0+2.05*inch, ty-0.55*inch, X0, col-0.1*inch)
    y = lo-0.35*inch
    width = col-X0-0.2*inch
    c.setFillColor(black); c.setFont('Helvetica-Bold', 9); c.drawString(X0, y, 'W4A / W4B NOTES')
    c.setLineWidth(0.7); c.line(X0, y-4, X0+width, y-4); y -= 0.22*inch
    c.setFont('Helvetica', 6.4)
    for t in wrap_notes(notes(), width, 6.4):
        assert pdfmetrics.stringWidth(t, 'Helvetica', 6.4) <= width+0.5, "A-603 note overruns: " + t
        c.drawString(X0, y, t); y -= 8.4
    assert y > Y0, "A-603 notes run off the sheet by %.2f in" % ((Y0-y)/inch)
    dx = col+0.2*inch
    cx = col+0.2*inch+2.7*inch+IN(20)*DETAIL
    top = Y1-0.25*inch
    for n, name, fn in ((2, 'CEILING LINE — BOTH WALLS AT THE ROOF PLATE', _ceiling),
                        (3, 'FLOOR LINE — EACH RIM ON ITS OWN WALL', _floor),
                        (4, 'BASE — BOTH WALLS ON THE FS STRIP', _base)):
        _title(dx, top, n, name, '1-1/2" = 1\'-0"')
        lo = fn(cx, top-0.5*inch, dx, X1-0.1*inch)
        top = lo-0.4*inch
    assert lo > Y0, "A-603 details run off the sheet by %.2f in" % ((Y0-lo)/inch)
    c.showPage()

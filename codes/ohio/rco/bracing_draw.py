"""The wall-bracing sheet's drawing vocabulary: a braced wall line with its panels, ends and hold-downs, masked labels, dimensions, plan titles and headings.

Plan feet in, page points out, through the PlanDraw or the canvas stand-in it is handed; what is
drawn where is the project's. It was word for word in each project's copy of the sheet.
"""
from reportlab.lib.colors import black, white
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from lib.draw.text import wrap_notes
from lib.draw.page import LAY, GREY
from lib.draw.kit import c, _fits
from lib.units import fmt, inches
from lib.model.regrid import EXT_STUD
from codes.ohio.rco import bracing as rco_bracing


BAR_IN = 0.25        # ft: a panel bar is drawn this far inside the outside face


LBL_OUT = 2.2        # ft: its length label this far outside


BUBBLE = 3.4         # ft: the tag bubble this far past the line's far end


def _pt(ln, s, off):
    """The page-feet point `s` along the line's wall and `off` inside its outside face
       (negative: outside the building)."""
    inward = off if ln.at < 1e-9 else ln.at-off
    return (s, inward) if ln.o == 'x' else (inward, s)


def _masked(cc, X, Y, text, size, rot=0, bold=False):
    """Centered text on a white ground, so it reads over the grey plan and the stairs."""
    font = 'Helvetica-Bold' if bold else 'Helvetica'
    w = pdfmetrics.stringWidth(text, font, size)
    cc.saveState(); cc.translate(X, Y); cc.rotate(rot)
    cc.setFillColor(white); cc.rect(-w/2.0-1.2, -size*0.5-1.0, w+2.4, size+1.6, fill=1, stroke=0)
    cc.setFillColor(black); cc.setFont(font, size); cc.drawCentredString(0, -size*0.35, text)
    cc.restoreState()


def _bracing(p, lines):
    """Each braced wall line of one level on PlanDraw p, drawing at 1/8": the line and
       its tag, every panel as a bar with its length, the portal frames and the
       hold-downs."""
    cc = p.c
    for ln in lines:
        rot = 0 if ln.o == 'x' else 90
        LAY('S-FRAM'); cc.setStrokeColor(black); cc.setLineWidth(0.45); cc.setDash([6, 2, 1, 2], 0)
        a = _pt(ln, -1.4, EXT_STUD/2.0); b = _pt(ln, ln.length+BUBBLE-0.6, EXT_STUD/2.0)
        cc.line(p.X(a[0]), p.Y(a[1]), p.X(b[0]), p.Y(b[1])); cc.setDash()
        bx, by = _pt(ln, ln.length+BUBBLE, EXT_STUD/2.0)
        cc.setFillColor(white); cc.setLineWidth(0.7); cc.circle(p.X(bx), p.Y(by), 5.4, fill=1, stroke=1)
        LAY('S-ANNO-TEXT'); cc.setFillColor(black); cc.setFont('Helvetica-Bold', 6.0)
        cc.drawCentredString(p.X(bx), p.Y(by)-2.1, ln.tag)
        for pn in ln.panels:
            LAY('S-FRAM'); cc.setStrokeColor(black)
            if pn.method == 'CS-PF':
                cc.setLineWidth(0.7)
                for d in (BAR_IN-0.12, BAR_IN+0.12):
                    u = _pt(ln, pn.a, d); v = _pt(ln, pn.b, d)
                    cc.line(p.X(u[0]), p.Y(u[1]), p.X(v[0]), p.Y(v[1]))
            else:
                cc.setLineWidth(2.6)
                u = _pt(ln, pn.a, BAR_IN); v = _pt(ln, pn.b, BAR_IN)
                cc.line(p.X(u[0]), p.Y(u[1]), p.X(v[0]), p.Y(v[1]))
            cc.setLineWidth(0.5)
            for s in (pn.a, pn.b):                              # a tick at each end of the panel
                u = _pt(ln, s, -0.5); v = _pt(ln, s, 0.9)
                cc.line(p.X(u[0]), p.Y(u[1]), p.X(v[0]), p.Y(v[1]))
            LAY('S-ANNO-TEXT')
            m = _pt(ln, (pn.a+pn.b)/2.0, -LBL_OUT)
            _masked(cc, p.X(m[0]), p.Y(m[1]), fmt(pn.b-pn.a)+(' CS-PF, DETAIL 4' if pn.method == 'CS-PF' else ''), 4.4, rot)
        for e in ln.ends:
            if e.hold_down is None:
                continue
            LAY('S-FRAM')
            h = _pt(ln, e.hold_down+(0.25 if e.side == 'lo' else -0.25), BAR_IN)
            cc.setFillColor(black); cc.rect(p.X(h[0])-2.4, p.Y(h[1])-2.4, 4.8, 4.8, fill=1, stroke=0)
            LAY('S-ANNO-TEXT')
            q = _pt(ln, e.hold_down+(2.2 if e.side == 'lo' else -2.2), 1.9)
            cc.setStrokeColor(black); cc.setLineWidth(0.3); cc.line(p.X(h[0]), p.Y(h[1]), p.X(q[0]), p.Y(q[1]))
            _masked(cc, p.X(q[0]), p.Y(q[1]), 'HD, %d LB' % rco_bracing.HOLD_DOWN_LB, 4.2, rot, bold=True)


def _plan_title(ox, oy, text):
    LAY('S-ANNO-TEXT')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 9.0); c.drawString(ox, oy-0.72*inch, text)
    c.setFont('Helvetica', 7.2); c.drawString(ox, oy-0.87*inch, 'SCALE: 1/8" = 1\'-0"')
    c.setLineWidth(1.0); c.setStrokeColor(black); c.line(ox, oy-0.56*inch, ox+2.2*inch, oy-0.56*inch)


def _heading(x, y, width, text):
    _fits(text, 'Helvetica-Bold', 7.2, width, 'S-104 heading')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, text); y -= 3
    c.setStrokeColor(black); c.setLineWidth(0.6); c.line(x, y, x+width, y)
    return y-9.4


def _ends_text(ln):
    return ' / '.join('%s%s' % (e.condition, ' HD' if e.hold_down is not None else '') for e in ln.ends)


# How a portal leg is held down, by level, for note 9 and detail 4.
_PORTAL_ANCHOR = {
    1: 'Level 1: two 1/2" anchor bolts with 2" x 2" x 3/16" plate washers in the leg.',
    2: (f'Level 2: two {rco_bracing.PORTAL_ANCHOR_LB} lb framing anchors across the sheathing joint at the rim, or the sheathing '
        f'lapped {inches(rco_bracing.PORTAL_LAP)} over the rim and nailed 8d common at 3" o.c. top and bottom.'),
}


def _dim_h(d, x0, x1, y, text, size=4.2):
    d.line(x0, y, x1, y, lw=0.35)
    for x in (x0, x1):
        d.line(x, y-0.12, x, y+0.12, lw=0.35)
    LAY('S-ANNO-TEXT'); c.setFillColor(black); c.setFont('Helvetica', size)
    c.drawCentredString(d.X((x0+x1)/2.0), d.Y(y)+1.6, text); LAY('S-DETL')


def _dim_v(d, x, y0, y1, text, size=4.2):
    d.line(x, y0, x, y1, lw=0.35)
    for y in (y0, y1):
        d.line(x-0.12, y, x+0.12, y, lw=0.35)
    LAY('S-ANNO-TEXT'); c.setFillColor(black); c.setFont('Helvetica', size)
    c.saveState(); c.translate(d.X(x)-1.6, d.Y((y0+y1)/2.0)); c.rotate(90); c.drawCentredString(0, 0, text); c.restoreState()
    LAY('S-DETL')


def _schedule(x, y, width, *, br):
    S, LEAD = 5.4, 7.0
    LAY('S-ANNO-TEXT')
    y = _heading(x, y, width, 'BRACING SCHEDULE — RCO 602.10, EVERY BRACED WALL LINE AT EACH LEVEL')
    W = width/inch
    cols = (('BLDG', 0.0, 'l'), ('LEVEL', 0.36, 'l'), ('BWL', 0.72, 'l'), ('WALL', 0.98, 'l'),
            ('SPACING', 2.62, 'r'), ('TABLE', 3.06, 'r'), ('FACTOR', 3.50, 'r'), ('REQUIRED', 4.02, 'r'),
            ('PANELS PROVIDED', 4.20, 'l'), ('PROVIDED', W-0.62, 'r'), ('ENDS', W, 'r'))
    def row(vals, font):
        c.setFont(font, S)
        for (nm, at, al), v in zip(cols, vals):
            (c.drawString if al == 'l' else c.drawRightString)(x+at*inch, y, v)
    c.setFillColor(black)
    row([nm for nm, _a, _l in cols], 'Helvetica-Bold'); y -= LEAD
    panel_w = (W-0.62-0.52-4.20)*inch
    last = None
    for ln in br.LINES:
        if last and (ln.building, ln.level) != last:
            c.setStrokeColor(GREY); c.setLineWidth(0.3); c.line(x, y+LEAD-2.2, x+width, y+LEAD-2.2)
        last = (ln.building, ln.level)
        panels = ', '.join(fmt(p.b-p.a)+(' CS-PF' if p.method == 'CS-PF' else '') for p in ln.panels)
        _fits(panels, 'Helvetica', S, panel_w, 'S-104 schedule panels')
        _fits(ln.wall, 'Helvetica', S, (2.62-0.98-0.42)*inch, 'S-104 schedule wall')
        row(['B%s' % ln.building[-1], 'L%d' % ln.level, ln.tag, ln.wall, fmt(ln.spacing), '%.2f FT' % ln.base,
             '%.3f' % rco_bracing.factor(ln), '%.2f FT' % ln.required, panels, '%.2f FT' % rco_bracing.provided(ln), _ends_text(ln)], 'Helvetica')
        y -= LEAD
    y -= 2
    c.setFont('Helvetica', S)
    for level in (1, 2):
        fs = {tuple(ln.factors) for ln in br.LINES if ln.level == level}
        assert len(fs) == 1, 'S-104: the Level %d lines do not share one factor' % level
        (factors,) = fs
        t = ('LEVEL %d, %s: TABLE 602.10.3(1) CS-WSP COLUMN AT THE SPACING x ' % (level, rco_bracing.STORY[level])
             + ' x '.join('%s %.3f' % (nm, v) for nm, v in factors)
             + ', TABLE 602.10.3(2)')
        _fits(t, 'Helvetica', S, width, 'S-104 factor line'); c.drawString(x, y, t); y -= LEAD
    for t in ('PANELS PROVIDED: FULL-HEIGHT SEGMENTS, EACH NOT LESS THAN TABLE 602.10.5 FOR ITS TALLER ADJACENT OPENING; CS-PF CONTRIBUTES %.1f x ITS LENGTH.' % rco_bracing.CS_PF_CREDIT,
              'ENDS, FIGURE 602.10.7, START / END OF THE LINE: 1 END PANEL AND %s RETURN PANEL; 2 END PANEL AND HOLD-DOWN; 3 END PANEL %s OR LONGER;'
              % (inches(rco_bracing.RETURN_MIN), inches(rco_bracing.END_PANEL_ALONE)),
              '     4 FIRST PANEL WITHIN %s, %s RETURN PANEL AND %s CORNER TO OPENING; 5 FIRST PANEL WITHIN %s AND HOLD-DOWN. HD = %d LB HOLD-DOWN, DRAWN.'
              % (fmt(rco_bracing.FIRST_PANEL_MAX), inches(rco_bracing.RETURN_MIN), inches(rco_bracing.CORNER_D_MIN), fmt(rco_bracing.FIRST_PANEL_MAX), rco_bracing.HOLD_DOWN_LB)):
        _fits(t, 'Helvetica', S, width, 'S-104 legend'); c.drawString(x, y, t); y -= LEAD
    return y


def _portal_levels(*, br):
    """The levels a portal frame stands at, read from the bracing model. Unit 5's kitchen
       window took Level 2's: its courtyard wall now holds two CS-WSP panels without one."""
    return sorted({ln.level for ln in br.LINES for _p, _o in br.portal_openings(ln)})


def _lines(building, level, *, br):
    return [ln for ln in br.LINES if ln.building == building and ln.level == level]


def _notes(x, y, width, cols=2, size=5.6, lead=7.3, *, _notes_text):
    LAY('S-ANNO-TEXT')
    y = _heading(x, y, width, 'WALL BRACING NOTES')
    gap = 0.18*inch
    cw = (width-gap*(cols-1))/cols
    lines = wrap_notes(_notes_text(), cw, size)
    per = -(-len(lines)//cols)
    c.setFillColor(black); c.setFont('Helvetica', size)
    for k in range(cols):
        yy = y
        for t in lines[k*per:(k+1)*per]:
            _fits(t, 'Helvetica', size, cw, 'S-104 note')
            c.drawString(x+k*(cw+gap), yy, t); yy -= lead
    return y-per*lead

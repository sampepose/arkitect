"""The two sheets a new address draws on its first day, from its massing alone, in any
jurisdiction: G-001, the cover, and C-102, the zoning site plan on its own 11 x 17 sheet.

Both print the jurisdiction's fit rows -- the one the intake names in `"jurisdiction"`
(arkitect/codes/jurisdiction.py) -- which is why they are here and not in arkitect/lib/:
every row carries a section. Every word that belongs to a place (its city, its zoning code's
citation prefix, where an unsurveyed lot's dimensions come from) is the jurisdiction's. They draw what the intake knows and nothing it does not -- no
north arrow before a true north is given, no height before the roof is modelled -- and a
rule that cannot be checked yet prints PENDING DESIGN rather than a figure.

A project's own G-001 or C-102 replaces these when it has more to say (the first two
projects' did). Until then they are the set, and arkitect/harness/progress.py lists them as drawn, not done.
"""
from reportlab.lib.colors import Color, black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics

from arkitect.codes import jurisdiction
from arkitect.codes import massing as M
from arkitect.lib.draw import page
from arkitect.lib.draw.kit import c
from arkitect.lib.draw.page import Sheet
from arkitect.lib.draw.text import table
from arkitect.lib.units import fmt

SHADE = Color(.85, .85, .85)
# Standard engineering and architectural scales, points per foot, largest first.
SCALES = ((9.0, '1/8" = 1\'-0"'), (6.75, '3/32" = 1\'-0"'), (4.5, '1/16" = 1\'-0"'),
          (3.6, '1" = 20\'-0"'), (2.4, '1" = 30\'-0"'))


def _value(r):
    """What a zoning row prints: the figure, and what stands behind it if it is not met."""
    if r.status == M.NOT_CHECKED:
        return 'PENDING DESIGN'
    if r.status == M.RELIEF:
        return '%s — %s' % (r.provided, r.note.split(';')[0])
    if r.status == M.FAILS:
        return '%s — DOES NOT MEET %s' % (r.provided, r.required)
    return '%s  (%s)' % (r.provided, r.required)


def zoning_rows(rows, jur):
    """(label, value) for a table: the rule with its section, and what the massing gives.
       `jur` is the jurisdiction package; its zoning code's prefix is left off each section."""
    unverified = jurisdiction.fit(jur.__name__.rsplit('.', 1)[1]).CITE.get('density')
    out = []
    for r in rows:
        cite = '' if r.citation == unverified else ', ' + r.citation.replace(jur.ZONING_CODE + ' ', '')
        out.append((r.label + cite, _value(r)))
    return out


def _fits(text, font, size, width, where):
    w = pdfmetrics.stringWidth(text, font, size)
    assert w <= width, '%s: %r needs %.2f in of %.2f in' % (where, text, w/inch, width/inch)


def project_rows(d, m, jur):
    """(label, value) for the PROJECT DATA block, from the intake."""
    lot = d['lot']
    rows = [('Address', d['address']), ('Parcel', d['parcel']),
            ('Zoning district', d['district']),
            ('Lot', '%s x %s = {:,.0f} SF'.format(m.area) % (fmt(m.W), fmt(m.D))),
            ('Lot dimensions', 'BOUNDARY SURVEY' if lot.get('survey') else jur.LOT_SOURCE_SHORT.upper() + ', NO SURVEY'),
            ('Lot type', ('CORNER' if lot.get('corner') else 'INTERIOR')
             + (', %s ALLEY' % fmt(lot['alley_width']) if lot.get('alley') else ''))]
    for b in m.buildings:
        units = '; '.join('%s, %d BR' % (u['name'], u['bedrooms']) for u in b['dwellings'])
        rows.append((b['name'], '%s x %s, %d STOR%s, %s' % (
            fmt(b['width']), fmt(b['depth']), b['storeys'], 'Y' if b['storeys'] == 1 else 'IES',
            'PRINCIPAL' if b['role'] == 'principal' else 'ADU')))
        rows.append(('', units))
    if m.parking:
        rows.append(('Parking', '%d STALLS' % m.parking['stalls']))
    return rows


def cover_sheet(d, massing, index):
    """G-001: project data, applicable codes, the zoning fit, and the sheet index.
       `index` is [(sheet number, title)] of the sheets the set binds, this one included."""
    jur = jurisdiction.load(d['jurisdiction'])
    F = jurisdiction.fit(d['jurisdiction'])

    def sheet_g001():
        sh = Sheet(c, 'G-001', 'Cover sheet', 'N/A')
        sh.frame()
        x0, y0, x1, y1 = page.DA
        colw = (x1-x0-0.8*inch)/3.0
        top = y1-0.35*inch
        c.setFillColor(black)
        c.setFont('Helvetica-Bold', 16)
        c.drawString(x0, top, d['address'])
        c.setFont('Helvetica', 10)
        c.drawString(x0, top-0.24*inch, d['city_line'])
        ty = top-0.75*inch
        kw = dict(width=colw, size=8, lead=0.17*inch, title_size=10, gap=0.24*inch)
        rows = project_rows(d, massing, jur)
        for a, b in rows:
            _fits(b, 'Helvetica', 8, colw-pdfmetrics.stringWidth(a, 'Helvetica', 8)-6, 'G-001 project data')
        ya = table(c, x0, ty, 'PROJECT DATA', rows, **kw)
        codes = [('', t.upper()) for t in jur.CODES]
        ya = table(c, x0, ya-0.2*inch, 'APPLICABLE CODES', codes, **kw)
        assert ya >= y0, 'G-001 first column overruns the sheet'
        zr = zoning_rows(F.fit(massing), jur)
        for a, b in zr:
            _fits(a+'   '+b, 'Helvetica', 7.2, colw, 'G-001 zoning')
        yb = table(c, x0+colw+0.4*inch, ty, 'ZONING — %s' % d['district'], zr,
                   width=colw, size=7.2, lead=0.155*inch, title_size=10, gap=0.24*inch)
        assert yb >= y0, 'G-001 zoning column overruns the sheet'
        yc = table(c, x0+2*colw+0.8*inch, ty, 'SHEET INDEX', index, **kw)
        assert yc >= y0, 'G-001 sheet index overruns the sheet'
        c.showPage()
    return sheet_g001


def _scale(w_ft, h_ft, box_w, box_h):
    for pts, label in SCALES:
        if w_ft*pts <= box_w and h_ft*pts <= box_h:
            return pts, label
    raise AssertionError('C-102: the lot does not fit the plan area at any listed scale')


def zoning_site_plan(d, massing):
    """C-102: the lot, the footprints, the pad and the yards, with the zoning table, on
       11 x 17. The front street is at the bottom of the plan."""
    m = massing
    lot = d['lot']
    jur = jurisdiction.load(d['jurisdiction'])
    F = jurisdiction.fit(d['jurisdiction'])

    def sheet_c102():
        PG = page.ANSI_B
        sc_label = None
        x0, y0, x1, y1 = PG.DA
        plan_w = 3.9*inch
        street_band = 0.55*inch
        rear_band = 0.45*inch if lot.get('alley') else 0.2*inch
        pts, sc_label = _scale(m.W, m.D, plan_w-0.9*inch, y1-y0-street_band-rear_band-0.3*inch)
        sh = Sheet(c, 'C-102', 'Zoning site plan', sc_label, page=PG)
        sh.frame()
        ox = x0+0.55*inch+(plan_w-0.9*inch-m.W*pts)/2.0
        oy = y0+street_band+0.25*inch
        X = lambda v: ox+v*pts
        Y = lambda v: oy+v*pts          # y from the front lot line, up the sheet

        c.setStrokeColor(black); c.setFillColor(black)
        # the lot
        c.setLineWidth(1.6); c.setDash(8, 3)
        c.rect(X(0), Y(0), m.W*pts, m.D*pts, stroke=1, fill=0)
        c.setDash()
        # the parking pad, dashed, with its stalls
        if m.parking:
            pk = m.parking
            c.setLineWidth(0.6); c.setDash(3, 2)
            c.rect(X(pk['x0']), Y(m.D-pk['depth']), pk['width']*pts, pk['depth']*pts, stroke=1, fill=0)
            c.setDash()
            pitch = pk['width']/pk['stalls']
            for i in range(1, pk['stalls']):
                c.line(X(pk['x0']+i*pitch), Y(m.D-pk['depth']), X(pk['x0']+i*pitch), Y(m.D))
            # under the pad, where no stall line crosses it
            c.setFont('Helvetica', 5.5)
            c.drawCentredString(X(pk['x0']+pk['width']/2), Y(m.D-pk['depth'])-8,
                                '%d STALLS, %s x %s' % (pk['stalls'], fmt(pitch), fmt(pk['depth'])))
        # structures, then buildings over them
        c.setLineWidth(0.5)
        for t in m.structures:
            c.rect(X(t['x']), Y(t['y']), t['width']*pts, t['depth']*pts, stroke=1, fill=0)
        for b in m.buildings:
            c.setFillColor(SHADE); c.setLineWidth(1.2)
            c.rect(X(b['x']), Y(b['y']), b['width']*pts, b['depth']*pts, stroke=1, fill=1)
            c.setFillColor(black)
            cx, cy = X(b['x']+b['width']/2), Y(b['y']+b['depth']/2)
            c.setFont('Helvetica-Bold', 6.5); c.drawCentredString(cx, cy+4, b['name'])
            c.setFont('Helvetica', 5.5)
            c.drawCentredString(cx, cy-4, '%s x %s' % (fmt(b['width']), fmt(b['depth'])))
        # lot dimensions, the front yard and the rear yard
        c.setFont('Helvetica', 6)
        c.drawCentredString(X(m.W/2), Y(0)-10, fmt(m.W))
        c.saveState(); c.translate(X(0)-6, Y(m.D/2)); c.rotate(90)
        c.drawCentredString(0, 0, fmt(m.D)); c.restoreState()
        py = m.P['y']
        c.setLineWidth(0.4)
        c.line(X(m.P['x']+m.P['width']+1.5), Y(0), X(m.P['x']+m.P['width']+1.5), Y(py))
        c.saveState(); c.translate(X(m.P['x']+m.P['width']+1.5)+7, Y(py/2)); c.rotate(90)
        c.drawCentredString(0, 0, fmt(py)); c.restoreState()
        # the rights-of-way
        c.setFont('Helvetica-Bold', 7)
        c.drawCentredString(X(m.W/2), Y(0)-street_band+0.12*inch, d['street'])
        if lot.get('alley'):
            c.setFont('Helvetica', 6)
            c.drawCentredString(X(m.W/2), Y(m.D)+0.18*inch,
                                'PUBLIC ALLEY, %s RIGHT-OF-WAY' % fmt(lot['alley_width']))
        if lot.get('corner'):
            side_x = X(0)-0.35*inch if lot['side_street'] == 'left' else X(m.W)+0.35*inch
            c.saveState(); c.translate(side_x, Y(m.D/2)); c.rotate(90)
            c.setFont('Helvetica-Bold', 7); c.drawCentredString(0, 0, d['side_street_name'])
            c.restoreState()

        # the zoning table and the notes, right of the plan
        tx = x0+plan_w
        tw = (x1-tx-0.3*inch)/2.0
        zr = zoning_rows(F.fit(m), jur)
        for a, b in zr:
            _fits(a+'   '+b, 'Helvetica', 6.2, tw, 'C-102 zoning')
        half = (len(zr)+1)//2
        kw = dict(width=tw, size=6.2, lead=0.135*inch, title_size=8, gap=0.2*inch)
        ya = table(c, tx, y1-0.2*inch, 'ZONING — %s %s' % (jur.CITY, d['district']), zr[:half], **kw)
        yb = table(c, tx+tw+0.3*inch, y1-0.2*inch, 'ZONING — CONTINUED', zr[half:], **kw)
        notes = ['1.  LOT DIMENSIONS ARE FROM %s.' % ('A BOUNDARY SURVEY' if lot.get('survey')
                                                      else jur.LOT_SOURCE.upper() + '; NO SURVEY HAS BEEN MADE'),
                 '2.  DIMENSIONS ARE TO THE FACE OF STUD.']
        relief = [r for r in F.fit(m) if r.status == M.RELIEF]
        for r in relief:
            notes.append('%d.  %s, %s: %s.' % (len(notes)+1, r.label.upper(), r.citation,
                                                r.note.split(';')[0]))
        yn = table(c, tx, min(ya, yb)-0.25*inch, 'NOTES', [], width=2*tw+0.3*inch, size=6.2,
                   title_size=8, gap=0.2*inch)
        c.setFont('Helvetica', 6.2)
        for t in notes:
            _fits(t, 'Helvetica', 6.2, 2*tw+0.3*inch, 'C-102 notes')
            c.drawString(tx, yn, t); yn -= 0.135*inch
        assert yn >= y0, 'C-102 notes overrun the sheet'
        c.setFont('Helvetica-Bold', 9.5); c.drawString(tx, y0+0.26*inch, 'ZONING SITE PLAN')
        c.setFont('Helvetica', 6.0); c.drawString(tx, y0+0.13*inch, 'SCALE: ' + sc_label)
        c.showPage()
    return sheet_c102

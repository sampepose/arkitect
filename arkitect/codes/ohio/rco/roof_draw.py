"""What the roof framing sheet prints from the roof model: the attic ventilation table
against RCO 806.2 and the truss design loads.

A project hands these its own roofs, penetrations and design criteria.
"""
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from arkitect.lib.draw.kit import c, _fits
from arkitect.codes.ohio.rco.attic_ventilation import EAVE_NFA, RIDGE_NFA, VENT_RATIO, attic_vents


def _ventilation(x, y, width, *, roofs, penetrations, roof_areas=None):
    """ATTIC VENTILATION: one row per attic of src.roof, area and required net free area,
       and under it the eave and ridge runs the plans draw and the area they provide at
       note 7's minimum ratings. Each length prints rounded down to a tenth of a foot and
       each area is computed from the printed length and rounded down, so the row's
       arithmetic checks on the sheet and never overstates the model's figure.

       `roof_areas`, a roof -> (plan SF, sloped SF), adds the takeoff a roofer bids from."""
    S, LEAD = 5.6, 7.4
    heading = 'ATTIC VENTILATION — RCO 806, 1/%d OF THE ATTIC FLOOR' % VENT_RATIO
    _fits(heading, 'Helvetica-Bold', 7.2, width, 'ventilation heading')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= LEAD+2
    c.setFont('Helvetica-Bold', S); c.drawString(x, y, 'ATTIC'); c.drawRightString(x+width-0.95*inch, y, 'AREA'); c.drawRightString(x+width, y, 'NET FREE AREA REQ\'D'); y -= LEAD
    c.setFont('Helvetica', S)
    for r in roofs:
        for av in attic_vents(r, penetrations(r)):
            a = av.attic
            nfa = '%.1f SF  (%d SQ IN)' % (a.nfa, round(a.nfa*144))
            _fits(a.name, 'Helvetica', S, width-1.9*inch, 'ventilation row')
            c.drawString(x, y, a.name); c.drawRightString(x+width-0.95*inch, y, '%d SF' % round(a.area)); c.drawRightString(x+width, y, nfa); y -= LEAD
            eave, ridge = int(av.eave_lf*10+1e-9)/10.0, int(av.ridge_lf*10+1e-9)/10.0
            intake, exhaust = int(eave*EAVE_NFA+1e-9), int(ridge*RIDGE_NFA+1e-9)
            runs = 'EAVE %.1f LF AT %g = %d  ·  RIDGE %.1f LF AT %g = %d' % (eave, EAVE_NFA, intake, ridge, RIDGE_NFA, exhaust)
            prov = 'PROVIDED %d SQ IN' % (intake+exhaust)
            _fits(runs, 'Helvetica', S, width-6-pdfmetrics.stringWidth(prov, 'Helvetica', S)-8, 'ventilation runs')
            c.drawString(x+6, y, runs); c.drawRightString(x+width, y, prov); y -= LEAD
    tail = 'VENT RUNS AS DRAWN, AT THE MINIMUM RATINGS OF NOTE 7 IN SQ IN PER LF'
    _fits(tail, 'Helvetica', S, width, 'ventilation tail')
    c.drawString(x, y, tail); y -= LEAD
    if roof_areas is not None:
        y -= 2
        c.setFont('Helvetica-Bold', S); c.drawString(x, y, 'ROOF AREA TO THE DRIPLINE'); y -= LEAD
        c.setFont('Helvetica', S)
        for r in roofs:
            plan, slope = roof_areas(r)
            row = '%s: %s SF IN PLAN, %s SF ON THE SLOPE  (%.1f SQUARES)' % (
                r.name, '{:,}'.format(int(round(plan))), '{:,}'.format(int(round(slope))), slope/100.0)
            _fits(row, 'Helvetica', S, width, 'roof area row')
            c.drawString(x, y, row); y -= LEAD
    return y-4


def _loads(x, y, width, *, bc_dead, ground_snow, roof_deflection, roof_live, tc_dead, wind):
    """ROOF DESIGN LOADS: every figure from src.roof / src.framing."""
    S, LEAD = 5.6, 7.4
    heading = 'ROOF DESIGN LOADS — RCO TABLE 301.6, 301.7, G-001'
    _fits(heading, 'Helvetica-Bold', 7.2, width, 'roof loads heading')
    c.setFillColor(black); c.setFont('Helvetica-Bold', 7.2); c.drawString(x, y, heading); y -= 3
    c.setLineWidth(0.6); c.line(x, y, x+width, y); y -= LEAD+2
    c.setFont('Helvetica', S)
    rows = [('ROOF LIVE LOAD', '%d PSF' % roof_live), ('GROUND SNOW LOAD', '%d PSF' % ground_snow),
            ('DEAD LOAD, TOP CHORD', '%d PSF' % tc_dead), ('DEAD LOAD, BOTTOM CHORD', '%d PSF' % bc_dead),
            ('WIND', wind), ('DEFLECTION', roof_deflection), ('UPLIFT AND BEARING REACTIONS', 'PER THE TRUSS DESIGN')]
    for lab, val in rows:
        vw = pdfmetrics.stringWidth(val, 'Helvetica', S)
        _fits(lab, 'Helvetica', S, width-vw-6, 'roof loads label')
        c.drawString(x, y, lab); c.drawRightString(x+width, y, val); y -= LEAD
    return y-4

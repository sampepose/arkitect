"""The WATER SERVICE ENTRY section both projects' P-601 draws, beside the rule it draws.

It lives here rather than in arkitect/lib/draw because every label and note on it names a code
section -- OPC 305.3, OPC 305.4.1, RCO 403.1.5 -- and arkitect/lib/ is code-neutral
(arkitect/lib/verify/test_neutrality.py). arkitect/codes/ohio/rco/roof_draw.py and bracing_draw.py are the
same shape: a drawing that can only be read with its citations on it.

opc_service_entry.py works out the geometry; nothing here decides anything. A project
hands in its own foundation figures and its own sheet names, so neither project carries a
copy of the drawing.
"""
from reportlab.lib.units import inch
from arkitect.lib.draw.detail import _Det, _title
from arkitect.lib.draw.kit import c, notes_block
from arkitect.lib.draw.page import GREY
from arkitect.codes.ohio.opc_service_entry import MIN_COVER
from arkitect.lib.units import IN, fmt, inches
from reportlab.lib.colors import black

# Architectural scales, points per foot, largest first, with what a title block calls them.
# Detail 2's width follows the 1-in-10 return, which follows the burial depth: when the
# service went 6 in deeper the run went from 3'-6" to 8'-9" and the drawing outgrew its
# column. It picks its own scale now rather than carrying one that was right once.
SCALES = ((108.0, '1-1/2" = 1\'-0"'), (72.0, '1" = 1\'-0"'), (54.0, '3/4" = 1\'-0"'),
          (36.0, '1/2" = 1\'-0"'), (27.0, '3/8" = 1\'-0"'), (18.0, '1/4" = 1\'-0"'),
          (13.5, '3/16" = 1\'-0"'), (9.0, '1/8" = 1\'-0"'))


LABEL_COL = 95.0          # points a label column needs beside detail 2


# What the pipe through the footing is called. 'SERVICE': each building has its own service
# from the main. 'SUPPLY': the lot has one service and each building a supply off it, so the
# pipe here is that building's supply. The project passes the one it has, as `line`.
_WORDS = {'SERVICE': {'noun': 'SERVICE', 'one': 'ONE SERVICE PER BUILDING', 'from': 'THE CURB STOP'},
          'SUPPLY':  {'noun': 'SUPPLY', 'one': "ONE SUPPLY TO EACH BUILDING, OFF THE LOT'S ONE SERVICE",
                      'from': 'ITS TEE OFF THE SERVICE'}}


def _fit_scale(avail, span, labels, max_h=None, tall=None, what='elevation'):
    """The largest standard scale at which `span` feet and a label column each side fit in
       `avail` points -- and, where `max_h` is given, at which `tall` feet also fit it."""
    for sc, name in SCALES:
        if span*sc+2*labels <= avail and (max_h is None or tall*sc <= max_h):
            return sc, name
    raise AssertionError('the service entry %s does not fit at any scale: %.2f ft wide in '
                         '%.0f pt%s' % (what, span, avail,
                                        '' if max_h is None else ', %.2f ft tall in %.0f pt' % (tall, max_h)))


# The section P-102 / P-103 note 2 and S-101 note 8 point at. It is here, not on S-101,
# because S-101 has no room left under its wall detail and P-601 is the plumbing sheet
# with an empty column; it is drawn once because both buildings take the same service.
#
# What it settles: the set buries the service below the 32" frost line and the footing's
# BOTTOM is that same 32", so the foundation wall standing on it starts a footing
# thickness HIGHER than the pipe. "Sleeve it through the foundation wall" described a
# building this is not. The service goes UNDER the footing, and the footing is deepened
# to carry it rather than trenched beneath.
def service_entry_section(top, left, right, e, wall_t, ftg_proj, insul_t, edge_insul_run,
                          slab_t, bar_cover, bar_dia, bar, gravel_t, slab_top, grade,
                          water_sheets, sheet, max_h, *, line):
    """Detail 1: the section across the wall, cut along the service."""
    pipe = e.pipe_od
    ctr = (e.pipe_top+e.pipe_bot)/2.0
    rise = wall_t+ftg_proj+e.past+IN(2)                 # the elbow, clear of the sleeve's end
    # centred in whatever column the sheet gives it: the label room each side is what is
    # left over, and a hand-tuned offset went wrong the moment a project used a narrower one
    xw, origin = 1.5, 0.5
    zlo, zhi = e.deep_bot-IN(4), slab_top+IN(4)
    sc, _name = _fit_scale(right-left, 2*xw, LABEL_COL, max_h, zhi-zlo, 'section')
    cx = left+(right-left-2*xw*sc)/2.0+xw*sc
    d = _Det(cx, top, sc, xw, zlo, zhi, left, right,
             size=5.0, gap=9.0, sheet=sheet, origin=origin)
    d.hatch(wall_t, e.bed, 2.0, slab_top-slab_t, step=2.6)       # the clean aggregate
    d.rect(-ftg_proj, e.deep_bot, wall_t+ftg_proj, e.ftg_top)           # the deepened footing
    d.rect(0.0, e.ftg_top, wall_t, slab_top)                     # the wall on it
    d.rect(wall_t+insul_t, slab_top-slab_t, 2.0, slab_top)
    d.rect(wall_t, slab_top-edge_insul_run, wall_t+insul_t, slab_top, fill=GREY)
    d.line(-1.0, grade, 0.0, grade, lw=1.4)
    # the two bottom bars, straight through at their own elevation
    c.setFillColor(black)
    for bx in (-ftg_proj+bar_cover+bar_dia/2.0, wall_t+ftg_proj-bar_cover-bar_dia/2.0):
        c.circle(d.X(bx), d.Y(e.bar_bot+bar_dia/2.0), 1.5, fill=1, stroke=0)
    # the sleeve, cast through the footing and past each face
    for z in (e.sleeve_top, e.sleeve_bot):
        d.line(-ftg_proj-e.past, z, wall_t+ftg_proj+e.past, z, lw=0.5)
    for x in (-ftg_proj-e.past, wall_t+ftg_proj+e.past):
        d.line(x, e.sleeve_top, x, e.sleeve_bot, lw=0.5)
    # the service: in from the main below frost, under the footing, up inside the wall
    # into the aggregate, and away to its riser
    d.line(-1.0, e.pipe_top, rise-pipe/2.0, e.pipe_top, lw=1.0)
    d.line(-1.0, e.pipe_bot, rise+pipe/2.0, e.pipe_bot, lw=1.0)
    d.line(rise-pipe/2.0, e.pipe_top, rise-pipe/2.0, e.bed+pipe, lw=1.0)
    d.line(rise+pipe/2.0, e.pipe_bot, rise+pipe/2.0, e.bed, lw=1.0)
    d.line(rise-pipe/2.0, e.bed+pipe, 2.0, e.bed+pipe, lw=1.0)
    d.line(rise+pipe/2.0, e.bed, 2.0, e.bed, lw=1.0)
    d.lab(-0.75, grade, 'L', ('FINISHED GRADE 0\'-0"',))
    d.lab(-0.75, ctr, 'L',
          ('%s" WATER %s, TOP %s BELOW' % (e.service, _WORDS[line]['noun'], inches(e.bury)),
           'FINISHED GRADE — %s UNDER THE %s' % (inches(e.bury-e.frost), inches(e.frost)),
           'FROST LINE, OPC 305.4. THE FOOTING',
           'BEARS AT THE FROST LINE, S-101,',
           'SO THE PIPE RUNS BELOW IT. NOTE SE1.'))
    d.lab(-ftg_proj, e.deep_bot, 'L',
          ('FOOTING THICKENED TO %s HERE,' % inches(e.thick),
           'BOTTOM %s DOWN, ON UNDISTURBED' % inches(-e.deep_bot),
           'SOIL — DETAIL 2'))
    d.lab(wall_t/2.0, (e.ftg_top+slab_top)/2.0, 'R',
          ('%s FOUNDATION WALL, BOTTOM %s' % (inches(wall_t), inches(-e.ftg_top)),
           'BELOW FINISHED GRADE: NO PIPE',
           'PASSES THROUGH IT'))
    d.lab(wall_t+ftg_proj, ctr, 'R',
          ('%s" SLEEVE, %s OUTSIDE — TWO PIPE' % (e.sleeve, inches(e.sleeve_od)),
           'SIZES LARGER, CAST THROUGH THE',
           'FOOTING AND %s PAST EACH FACE,' % inches(e.past),
           'ANNULUS SEALED — OPC 305.3'))
    d.lab(wall_t+ftg_proj-bar_cover, e.bar_bot, 'R',
          ('2-%s CONT. AT THEIR TYPICAL' % bar, 'DEPTH, %s CLEAR OVER THE SLEEVE' % inches(e.bar_clear)))
    d.lab(1.9, e.bed+pipe/2.0, 'R',
          ('THE %s RISES INSIDE THE WALL' % _WORDS[line]['noun'],
           'INTO THE %s AGGREGATE AND RUNS' % inches(gravel_t),
           'TO ITS RISER, %s' % water_sheets))
    lo = d.flush('detail 1')
    _title(left, lo-0.26*inch, 1, 'WATER %s THROUGH THE THICKENED FOOTING' % _WORDS[line]['noun'], _name)
    return lo-0.58*inch


def service_entry_elevation(top, left, right, e, ftg_w, bar, sheet, *, line):
    """Detail 2: the same footing seen along the wall — what carries the building over
       the crossing."""
    pipe = e.pipe_od
    ctr = (e.pipe_top+e.pipe_bot)/2.0
    half, xw = ftg_w/2.0, ftg_w/2.0+e.run+0.6
    stub = IN(6)                                        # the wall over the footing, broken off
    sc, scale_name = _fit_scale(right-left, 2*xw, LABEL_COL)
    cx = left+(right-left)/2.0
    d = _Det(cx, top, sc, xw, e.deep_bot-IN(5), e.ftg_top+stub, left, right,
             size=5.0, gap=9.0, sheet=sheet)
    for x in (-xw, xw):                                 # the wall over, open at the top
        d.line(x, e.ftg_top, x, e.ftg_top+stub)
    d.poly([(-xw, e.ftg_top), (xw, e.ftg_top), (xw, e.ftg_bot), (half+e.run, e.ftg_bot),
            (half, e.deep_bot), (-half, e.deep_bot), (-half-e.run, e.ftg_bot), (-xw, e.ftg_bot)])
    d.line(-xw, e.ftg_bot, xw, e.ftg_bot, lw=0.4, dash=(3, 2))   # the typical bottom it leaves
    for z in (e.bar_bot, e.bar_top):
        d.line(-xw, z, xw, z, lw=0.4)
    d.circle(0.0, ctr, e.sleeve_od/2.0)
    d.circle(0.0, ctr, pipe/2.0)
    d.lab(-xw, e.ftg_top+stub/2.0, 'L', ('THE FOUNDATION WALL', 'OVER — DETAIL 1'))
    d.lab(-half-e.run/2.0, (e.ftg_bot+e.deep_bot)/2.0, 'L',
          ('THE BOTTOM RETURNS AT', '1 IN 10, RCO 403.1.5:', '%s EACH SIDE' % fmt(e.run)))
    d.lab(-half, e.deep_bot, 'L', ('%s LOWER, %s THICK' % (inches(e.drop), inches(e.thick)),))
    d.lab(xw-0.4, e.ftg_bot, 'R', ('TYPICAL FOOTING BOTTOM,', '%s BELOW FINISHED GRADE' % inches(-e.ftg_bot)))
    d.lab(0.0, ctr, 'R', ('THE SLEEVE AND THE', '%s — DETAIL 1' % _WORDS[line]['noun']))
    d.lab(half+e.run/2.0, e.bar_bot, 'R', ('2-%s CONT., STRAIGHT' % bar, 'THROUGH — NOTE SE4'))
    lo = d.flush('detail 2')
    _title(left, lo-0.26*inch, 2, 'THE THICKENED FOOTING ALONG THE WALL', scale_name)
    return lo-0.58*inch


def service_entry_notes(x, y, width, e, gravel_t, bar, water_sheets, layer, *, water_utility, line, cols=1,
                        located=None, notes_sheet=None):
    """SE1 to SE6: what a builder does, in the order it is built. `water_utility` is the
       jurisdiction's (its WATER_UTILITY), whose own depth may govern the service. `cols` is 1 in a tall
       narrow column and 2 in a short wide band -- the sheet knows which it has. `located`
       names the sheet that locates each thickened length on plan (thickened_zone()), where
       a set draws one; SE3 then says the return is measured along the footing and turns a
       corner it reaches."""
    W = _WORDS[line]
    return notes_block(x, y, width, [
        'SE1. BURIAL — %s, LOCATED ON %s. ITS TOP RUNS %s BELOW FINISHED GRADE FROM %s TO THE '
        'FOOTING: %s UNDER THE %s FROST LINE OF G-001, AND NOT LESS THAN %s BELOW GRADE, OPC 305.4. GO DEEPER IF %s '
        'REQUIRES IT. THE %s RISES ONLY INSIDE THE FOUNDATION WALL; NO PART OF IT RISES IN OUTSIDE GROUND.'
        % (W['one'], water_sheets, inches(e.bury), W['from'], inches(e.bury-e.frost), inches(e.frost), inches(MIN_COVER),
           water_utility, W['noun']),
        'SE2. SLEEVE — %s" NON-METALLIC, %s OUTSIDE, TWO PIPE SIZES LARGER THAN THE %s, OPC 305.3, SET IN THE FOOTING TRENCH '
        'BEFORE THE FOOTING IS POURED AND RUNNING %s PAST EACH FACE. SEAL THE ANNULUS BOTH ENDS. NO CONCRETE BEARS ON THE %s '
        'AND NO JOINT OCCURS INSIDE THE FOOTING, OPC 305.2 AND 305.3.' % (e.sleeve, inches(e.sleeve_od), W['noun'], inches(e.past), W['noun']),
        'SE3. FOOTING — THE %s PASSES THROUGH THE FOOTING, NOT UNDER IT: AT THE CROSSING THE FOOTING IS THICKENED TO %s, ITS '
        'BOTTOM %s LOWER THAN THE TYPICAL %s OF S-101 NOTE 1, WHICH LEAVES %s OF CONCRETE UNDER THE SLEEVE. THE BOTTOM RETURNS TO '
        'ITS TYPICAL DEPTH AT ONE UNIT IN TEN OVER %s EACH SIDE, RCO 403.1.5, AND THE TOP STAYS LEVEL.'
        % (W['noun'], inches(e.thick), inches(e.drop), inches(-e.ftg_bot), inches(e.sleeve_bot-e.deep_bot), fmt(e.run))
        + ((' THAT LENGTH IS MEASURED ALONG THE FOOTING\'S CENTERLINE; WHERE IT REACHES A CORNER THE SLOPED BOTTOM CONTINUES '
            'AROUND IT ALONG THE ADJOINING FOOTING. %s LOCATES EACH THICKENED LENGTH.' % located) if located else ''),
        'SE4. BEARING — THE THICKENED FOOTING BEARS ON UNDISTURBED SOIL FOR ITS WHOLE LENGTH, S-101 NOTE 9. DO NOT TRENCH UNDER A '
        'POURED FOOTING AND DO NOT BACKFILL UNDER ONE. THE TWO %s BOTTOM BARS RUN THROUGH STRAIGHT AT THEIR TYPICAL DEPTH, %s CLEAR '
        'OVER THE SLEEVE; THE CONCRETE BELOW THEM IS PLAIN.' % (bar, inches(e.bar_clear)),
        'SE5. INSIDE — THE %s RISES WITHIN THE FOUNDATION WALL AND ITS SLAB-EDGE INSULATION INTO THE %s CLEAN AGGREGATE UNDER THE '
        'SLAB, S-101 NOTE 2, AND RUNS TO ITS RISER IN ONE CONTINUOUS LENGTH WITH NO JOINT BELOW THE SLAB, %s NOTE 6.'
        % (W['noun'], inches(gravel_t), notes_sheet or water_sheets),
        'SE6. WHERE P-101 NOTE 9 CALLS FOR A CONTINUOUS SLEEVE PAST A SEWER CROSSING, OPC 603.2, THAT SLEEVE IS CARRIED THROUGH THE '
        'FOOTING AS THIS DETAIL DRAWS IT; THERE IS NOT A SECOND ONE.',
    ], 'WATER %s ENTRY NOTES' % W['noun'], layer, 'service entry note', cols, 5.2, 7.0)

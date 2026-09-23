"""How a water service gets from below the frost line, outside a building, to the
aggregate under its slab — OPC 305.2, 305.3 and 305.4 with RCO 403.1.5.

A slab-on-grade house has no wall down there to come through. **OPC 305.4, Freezing**, is
the burial rule: exterior water supply piping is installed "not less than 6 inches below
the frost line and not less than 12 inches below grade". RCO 403.1.4.1 puts the footing's
BOTTOM at the frost line itself, so the service runs BELOW_FROST lower than the footing
bears and the foundation wall standing on that footing begins a footing thickness higher
again. "Sleeve it through the foundation wall" describes a basement; on a slab it
describes nothing.

**Read 305.4, not 305.4.1.** Ohio DELETES 305.4.1, which was the sewer-depth provision and
never governed a water service; an earlier version of this module cited it and buried the
service at the frost line instead of 6 inches under it. Both were wrong and a review
caught them.

**OPC 305.3** gives the two ways through foundation concrete: a relieving arch, or a pipe
sleeve two pipe sizes greater built into it. This module takes the sleeve and keeps the
bearing by THICKENING the footing at the crossing rather than trenching beneath it: the
footing's TOP stays level, its bottom drops far enough to carry the sleeve with cover
under it, and RCO 403.1.5 lets that bottom slope back to its typical depth at one unit in
ten without a step. So the service passes THROUGH the footing, inside concrete, not under
it -- nothing is excavated below a bearing surface and nothing is backfilled under one,
the footing simply bears lower where the pipe goes through, on the same undisturbed soil,
and the bottom bars run through straight at their own elevation well above the sleeve.
**OPC 305.2** is why no concrete bears on the pipe: piping is installed so as to prevent
strains and stresses beyond the structural strength of the pipe.

Sizes are names, not dimensions: the cover under the sleeve and the clearance over it to
the bars are taken off arkitect/lib/model/pipe.py's OUTSIDE diameters, because a 1-1/2 in sleeve is
1.900 in across. Every figure a project prints comes back from entry(); the project
supplies its own foundation, its own frost depth and its own service size.
"""
from collections import namedtuple
from arkitect.lib.units import IN
from arkitect.lib.model.pipe import od

# The nominal water-pipe sizes a service and its sleeve are made in, in order. OPC 305.3
# asks for a sleeve "two pipe sizes greater than the pipe passing through", which is two
# steps along this ladder.
NOMINAL = ('1/2', '3/4', '1', '1-1/4', '1-1/2', '2', '2-1/2', '3', '4')
SLEEVE_STEPS = 2            # OPC 305.3
BELOW_FROST = IN(6)         # OPC 305.4: the service's top under the frost line
MIN_COVER = IN(12)          # OPC 305.4: and never less than this below grade
BOTTOM_SLOPE = 0.10         # RCO 403.1.5: one unit vertical in ten horizontal, un-stepped
BAR_CLEAR = IN(1)           # the sleeve passes clear of the footing's bottom bars
SLEEVE_PAST = IN(6)         # how far the sleeve runs past each face of the concrete it is cast in

# entry() answers in feet, as ELEVATIONS relative to finished grade, negative down --
# the datum every section in a set of these drawings is dimensioned from.
#   service, sleeve        nominal sizes, '1' and '1-1/2'
#   pipe_top/_bot          the service where it crosses under the footing
#   sleeve_top/_bot        the sleeve around it, concentric
#   bar_top/_bot           the footing's bottom bars, at their typical elevation
#   ftg_top                the footing's top, which the wall stands on and which does not move
#   ftg_bot                the typical footing bottom, RCO 403.1.4.1's frost depth
#   deep_bot               the footing's bottom AT the crossing
#   drop                   how much lower that is than the typical bottom
#   run                    how far each side of the crossing the bottom takes to come back
#   thick                  the footing's thickness at the crossing
#   bar_clear              concrete between the sleeve's top and the bars
#   bury                   how far below grade the exterior service's TOP runs, OPC 305.4
#   frost                  the frost line it is measured under, RCO 403.1.4.1 / CIC-09
#   pipe_od, sleeve_od     what they actually measure across, arkitect/lib/model/pipe.py
#   past                   how far the sleeve runs past each face of the footing
#   bed                    the bottom of the aggregate the service rises into inside
Entry = namedtuple('Entry', 'service sleeve pipe_top pipe_bot sleeve_top sleeve_bot bar_top bar_bot '
                            'ftg_top ftg_bot deep_bot drop run thick bar_clear past bed bury frost pipe_od sleeve_od')


def bury_depth(frost_depth, below_frost=BELOW_FROST, min_cover=MIN_COVER):
    """How far below finished grade the top of the exterior service runs, OPC 305.4.
       A project states this once and hands it to everything that needs it."""
    return max(frost_depth+below_frost, min_cover)


def sleeve_size(service, steps=SLEEVE_STEPS, ladder=NOMINAL):
    """The sleeve OPC 305.3 asks for around `service`: `steps` sizes larger."""
    assert service in ladder, 'service size %r is not a nominal pipe size' % (service,)
    i = ladder.index(service)
    assert i+steps < len(ladder), 'no pipe size %d larger than %s' % (steps, service)
    return ladder[i+steps]


def entry(service, bury, frost_depth, ftg_t, bar_dia, bar_cover, cover, slab_top, water_bed,
          ftg_bot=None, past=SLEEVE_PAST, slope=BOTTOM_SLOPE, steps=SLEEVE_STEPS,
          series='CTS', sleeve_series='IPS'):
    """The service entry, as the section draws it.

       `cover` is the concrete the project wants under the sleeve, `bar_cover` the cover
       its bottom bars already have to earth, and `water_bed` how far below slab top the
       aggregate the service rises into reaches. `ftg_bot` is the footing's typical
       bottom, which RCO 403.1.4.1 puts at the frost depth and which a project founding
       deeper than frost states for itself -- a footing deep enough to reach below the
       service is a different detail, and entry_violations() says so."""
    sleeve = sleeve_size(service, steps)
    pipe = od(service, series)                    # what it MEASURES, not what it is called
    sleeve_od = od(sleeve, sleeve_series)
    pipe_top = -bury                              # OPC 305.4, under the frost line
    pipe_bot = pipe_top-pipe
    ctr = pipe_top-pipe/2.0                       # the sleeve is concentric about the pipe
    half = sleeve_od/2.0
    sleeve_top, sleeve_bot = ctr+half, ctr-half
    if ftg_bot is None:
        ftg_bot = -frost_depth                    # RCO 403.1.4.1: the bottom at the frost depth
    ftg_top = ftg_bot+ftg_t
    bar_bot = ftg_bot+bar_cover                   # the bars do not follow the deepened bottom
    bar_top = bar_bot+bar_dia
    deep_bot = sleeve_bot-cover
    drop = ftg_bot-deep_bot
    return Entry(service=service, sleeve=sleeve, pipe_top=pipe_top, pipe_bot=pipe_bot,
                 sleeve_top=sleeve_top, sleeve_bot=sleeve_bot, bar_top=bar_top, bar_bot=bar_bot,
                 ftg_top=ftg_top, ftg_bot=ftg_bot, deep_bot=deep_bot, drop=drop,
                 run=drop/slope, thick=ftg_top-deep_bot, bar_clear=bar_bot-sleeve_top,
                 past=past, bed=slab_top-water_bed, bury=bury, frost=frost_depth, pipe_od=pipe,
                 sleeve_od=sleeve_od)


def entry_violations(e, frost_depth, slope=BOTTOM_SLOPE, bar_clear=BAR_CLEAR, cover=None,
                     steps=SLEEVE_STEPS, below_frost=BELOW_FROST, min_cover=MIN_COVER):
    """What would make the drawn entry wrong. `cover` is the concrete the project wants
       under the sleeve; None takes whatever entry() was given."""
    v = []
    if e.bury < frost_depth+below_frost-1e-9:
        v.append('the service runs %s below finished grade, not the %s that is %s under the %s '
                 'frost line, OPC 305.4'
                 % (_i(e.bury), _i(frost_depth+below_frost), _i(below_frost), _i(frost_depth)))
    if e.bury < min_cover-1e-9:
        v.append('the service runs %s below finished grade, under the %s OPC 305.4 asks for in any case'
                 % (_i(e.bury), _i(min_cover)))
    if abs(e.pipe_top+e.bury) > 1e-9:
        v.append('the drawn service does not sit at the stated burial depth')
    if e.sleeve != sleeve_size(e.service, steps):
        v.append('the sleeve is %s" on a %s" service, not the %s" of OPC 305.3'
                 % (e.sleeve, e.service, sleeve_size(e.service, steps)))
    if e.sleeve_top > e.ftg_top-1e-9:
        v.append('the service reaches the top of the footing: it no longer passes under it')
    if e.ftg_bot < e.sleeve_bot+1e-9:
        v.append('the footing already bears %s below the sleeve, so the service goes THROUGH the wall '
                 'and needs no deepening: this is not that detail' % _i(e.sleeve_bot-e.ftg_bot))
    if e.deep_bot > e.sleeve_bot-1e-9:
        v.append('the footing bottom is not below the sleeve at the crossing')
    if cover is not None and e.sleeve_bot-e.deep_bot < cover-1e-9:
        v.append('only %s of concrete under the sleeve, against %s' % (_i(e.sleeve_bot-e.deep_bot), _i(cover)))
    if e.bar_clear < bar_clear-1e-9:
        v.append('the sleeve comes within %s of the footing\'s bottom bars' % _i(max(0.0, e.bar_clear)))
    if e.drop <= 0.0:
        v.append('the footing is not deepened at the crossing')
    if e.run < e.drop/slope-1e-9:
        v.append('the footing bottom rises 1 in %.1f back to its typical depth, steeper than RCO 403.1.5\'s 1 in %.0f'
                 % (e.run/e.drop if e.drop else 0.0, 1.0/slope))
    if e.bed <= e.pipe_top:
        v.append('the aggregate the service rises into is no higher than the service under the footing')
    return v


def entry_for(b, g):
    """One building's entry, from the Ground its project already states
       (arkitect/codes/ohio/opc_separation.py). The concrete under the sleeve takes the cover the
       bars take: both are cast against earth."""
    return entry(service=g.service_size(b), bury=g.bury, frost_depth=g.frost_depth, ftg_t=g.ftg_t,
                 bar_dia=g.bar_dia, bar_cover=g.bar_cover, cover=g.bar_cover,
                 slab_top=g.slab_top, water_bed=g.water_bed, series=g.service_series)


def entries_violations(buildings, g):
    """Every building's entry, named. A project calls this from its own check."""
    return ['%s: %s' % (b.name, t) for b in buildings
            for t in entry_violations(entry_for(b, g), frost_depth=g.frost_depth, cover=g.bar_cover)]


def _i(v):
    from arkitect.lib.units import inches
    return inches(v)


# ---------------- where the thickening lies on the footing ----------------
# RCO 403.1.5's one in ten is a slope of the footing's BOTTOM along the footing, so the
# return is measured on the footing's centreline, and where it reaches a corner before it
# is done it carries on around that corner along the adjoining footing at the same slope.
# A footing is one continuous beam of concrete; its bottom does not stop at a corner.
Zone = namedtuple('Zone', 'crossing path corners legs')


def _perimeter(loop):
    pts = list(loop)+[loop[0]]
    out, s = [], 0.0
    for a, b in zip(pts, pts[1:]):
        L = abs(b[0]-a[0])+abs(b[1]-a[1])            # the centreline is square
        out.append((a, b, s, L)); s += L
    return out, s


def _at(segs, total, s):
    s %= total
    for a, b, s0, L in segs:
        if s0-1e-9 <= s <= s0+L+1e-9:
            t = (s-s0)/L if L else 0.0
            return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
    return segs[-1][1]


def thickened_zone(e, centreline, crossing):
    """The stretch of footing thickened for one crossing: `centreline` is the footing's
       centreline as a closed, square loop of plan points, `crossing` where the service
       crosses it. Returns Zone(crossing, the centreline path from one end of the
       thickening to the other, the corners it turns, and the length on each side of every
       corner in order along the path)."""
    segs, total = _perimeter(centreline)
    s = None
    for a, b, s0, L in segs:
        if abs(crossing[0]-a[0]) < 1e-9 and abs(crossing[0]-b[0]) < 1e-9 and min(a[1], b[1])-1e-9 <= crossing[1] <= max(a[1], b[1])+1e-9:
            s = s0+abs(crossing[1]-a[1])
        elif abs(crossing[1]-a[1]) < 1e-9 and abs(crossing[1]-b[1]) < 1e-9 and min(a[0], b[0])-1e-9 <= crossing[0] <= max(a[0], b[0])+1e-9:
            s = s0+abs(crossing[0]-a[0])
        if s is not None:
            break
    if s is None:
        raise ValueError('the crossing %r is not on the footing centreline' % (crossing,))
    lo, hi = s-e.run, s+e.run
    corners = [s0+k*total for _a, _b, s0, _L in segs for k in (-1, 0, 1) if lo+1e-9 < s0+k*total < hi-1e-9]
    marks = [lo]+sorted(corners)+[hi]
    path = [_at(segs, total, m) for m in marks]
    return Zone(crossing=crossing, path=path, corners=[_at(segs, total, m) for m in sorted(corners)],
                legs=[b-a for a, b in zip(marks, marks[1:])])


def zone_violations(e, centreline, zone):
    """What would make the located thickening wrong: a return long enough to meet itself
       around the building, or one that turns two corners on one side of the crossing."""
    v = []
    _segs, total = _perimeter(centreline)
    if 2*e.run >= total-1e-9:
        v.append('the thickened footing returns %s each side, which meets itself around a %s footing'
                 % (_i(e.run), _i(total)))
    if len(zone.corners) > 2:
        v.append('the thickened footing turns %d corners' % len(zone.corners))
    if abs(sum(zone.legs)-2*e.run) > 1e-6:
        v.append('the located thickening is %s long, not the %s the return asks' % (_i(sum(zone.legs)), _i(2*e.run)))
    return v

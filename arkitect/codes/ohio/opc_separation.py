"""OPC 603.2, water and building-sewer separation, and what else a drain meets below a slab.

Where a drain crosses the water below the slab or in the ground, the water lies ABOVE it
with VERT_CLEAR to spare, inside the wall, or it is SLEEVED for SEWER_SEP either side; where
a run passes below a thickened bearing strip is reported for the sheet.

A project hands every function its drainage building `b` (arkitect/lib/model/drains.py) and ONE
Ground record: the figures it states and the functions that say where its water, strips and
sewers are. Nothing here knows a lot.
"""
import math
from collections import namedtuple
from arkitect.lib.units import IN
from arkitect.lib.model.runs import (TOL, along as _along, crossing as _crossing, in_rect as _inside, length as _len,
                            points as _points, seg_rect_dist as _seg_rect_dist)
from arkitect.lib.model.drains import _to_site
from arkitect.lib.model.pipe import od
from arkitect.codes.ohio.opc_drainage import SIZE_IN, invert_at

SEWER_SEP = 5.0            # feet either side of a crossing, 603.2
VERT_CLEAR = IN(12)        # the water's bottom over the drain's top

# cover        feet over the top of the highest pipe below the slab
# wall_t       the foundation wall's thickness
# water_bed    how far below slab top the water can lie in the aggregate
# frost_depth  the frost line the footing bears at, RCO 403.1.4.1
# bury         how far below grade the TOP of the exterior service runs, OPC 305.4 --
#              6 in under the frost line, not the frost line itself
# service_series  'CTS' for copper tube or PEX, 'IPS' for iron pipe size
# water_below(b)  [(a, b)] segments of water below the slab
# water_lines(b)  [(name, polyline)] every water line in the ground, the service first
# strips(b)       [((x, y, w, h), name)] the thickened strips
# sewers()        [(name, site path, invert below grade at a distance along it, size)]
# service_size(b) the service's nominal size, '1-1/4'
# ftg_t        the footing's thickness, so its top -- where the wall starts -- is known
# bar_dia, bar_cover  its bottom bars and their cover to earth
# slab_top     the slab's top over finished grade
# These last four are read only by arkitect/codes/ohio/opc_service_entry.py, which needs the
# same ground a project already states here rather than a second record of it.
Ground = namedtuple('Ground', 'cover wall_t water_bed frost_depth water_below water_lines strips sewers '
                              'service_size ftg_t bar_dia bar_cover slab_top bury service_series')


def crossings(b, g):
    """Where a drain crosses the water below the slab: (run, point)."""
    out = []
    for r in b.runs:
        for a, bb in zip(r.path, r.path[1:]):
            for c, d in g.water_below(b):
                x = _crossing(a, bb, c, d)
                if x is not None: out.append((r, x))
    return out


def strip_crossings(b, g):
    """Where a run passes below a thickened strip: (run, strip name, point)."""
    out = []
    for r in b.runs:
        for a, bb in zip(r.path, r.path[1:]):
            for rect, nm in g.strips(b):
                if _seg_rect_dist(a, bb, rect) < TOL and not _inside(a, rect) and not _inside(bb, rect):
                    if abs(a[0]-bb[0]) < TOL: out.append((r, nm, (a[0], rect[1]+rect[3]/2.0)))
                    else: out.append((r, nm, (rect[0]+rect[2]/2.0, a[1])))
    return out


def highest_top_near(b, run, p, g, reach=SEWER_SEP):
    """The highest point of the run's top within `reach` of p: feet below slab top, negative."""
    return max(invert_at(b, run, q, cover=g.cover)+IN(SIZE_IN[run.size]) for q in _points(run.path)
               if math.hypot(q[0]-p[0], q[1]-p[1]) <= reach+TOL)


def water_crossings(b, g):
    """Where a drain crosses the water in the ground: (run, water name, point, kind). The
       kind is 'above' where the water within SEWER_SEP of the crossing is all inside the
       foundation wall, so it can lie in the gravel under the slab, and the drain's top
       stays VERT_CLEAR below g.water_bed there; otherwise 'sleeved'."""
    inner = (g.wall_t, g.wall_t, b.W-2*g.wall_t, b.D-2*g.wall_t)
    out = []
    for r in b.runs:
        for a, bb in zip(r.path, r.path[1:]):
            for nm, line in g.water_lines(b):
                for c, d in zip(line, line[1:]):
                    x = _crossing(a, bb, c, d)
                    if x is None: continue
                    near = [q for q in _points(line) if math.hypot(q[0]-x[0], q[1]-x[1]) <= SEWER_SEP+TOL]
                    above = (all(_inside(q, inner) for q in near) and
                             -highest_top_near(b, r, x, g) >= g.water_bed+VERT_CLEAR-TOL)
                    out.append((r, nm, x, 'above' if above else 'sleeved'))
    return out


def site_crossings(b, g):
    """Where the building's service crosses the building sewer or the lateral on C-101:
       (sewer name, site point, the sewer's top below grade, kind). The service is at its
       burial depth there, so it is 'above' only if its bottom clears the sewer's top by
       VERT_CLEAR; otherwise 'sleeved'."""
    line = [_to_site(b, p) for p in g.water_lines(b)[0][1]]
    # the service's own bottom: its burial depth, OPC 305.4, plus what it measures across
    bottom = -(g.bury+od(g.service_size(b), g.service_series))
    out = []
    for nm, path, inv, size in g.sewers():
        for a, bb in zip(path, path[1:]):
            for c, d in zip(line, line[1:]):
                x = _crossing(a, bb, c, d)
                if x is None: continue
                top = inv(_along(path, x))+IN(SIZE_IN[size])
                out.append((nm, x, top, 'above' if bottom >= top+VERT_CLEAR-TOL else 'sleeved'))
    return out


def sleeves(b, g):
    """Each water line's sleeve where a crossing needs one: (water name, from, to), feet
       along the line from its first point, SEWER_SEP either side of every sleeved
       crossing, merged. A sleeve stops short only at a riser, where it rises through the
       slab with the pipe: the far end of the service, both ends of a trunk. Where it would
       run past the service's main, `from` is negative and the build stops."""
    lines = dict(g.water_lines(b))
    at = {}
    for _r, nm, x, kind in water_crossings(b, g):
        if kind == 'sleeved': at.setdefault(nm, []).append(_along(lines[nm], x))
    for _nm, x, _top, kind in site_crossings(b, g):
        if kind == 'sleeved': at.setdefault('SERVICE', []).append(_along(lines['SERVICE'], (x[0]-b.site[0], x[1]-b.site[1])))
    out = []
    for nm in sorted(at):
        L = _len(lines[nm])
        spans = sorted((t-SEWER_SEP if nm == 'SERVICE' else max(0.0, t-SEWER_SEP), min(L, t+SEWER_SEP)) for t in at[nm])
        merged = [list(spans[0])]
        for lo, hi in spans[1:]:
            if lo <= merged[-1][1]+TOL: merged[-1][1] = max(merged[-1][1], hi)
            else: merged.append([lo, hi])
        out += [(nm, lo, hi) for lo, hi in merged]
    return out

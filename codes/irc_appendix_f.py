"""IRC Appendix F, passive radon control, as a model checks it (voluntary in Ohio: the RCO
adopts no appendix). The gas-permeable layer is divided into areas by whatever cuts it;
each area takes exactly one vent pipe, a lateral may join two through a sleeve, and a tee
or a lateral keeps clear of every pipe below the slab.

A project hands these its own slabs, strips, drains, water lines and risers.
"""
import math
from lib.units import IN
from lib.model import runs
from collections import namedtuple


TOL = 1e-6


PIPE_OD = IN(3.5)


def _spans(strip, region):
    """A strip divides a region when it crosses it wall to wall: returns the two halves."""
    sx0, sy0, sx1, sy1 = strip[:4]
    x0, y0, x1, y1 = region
    if sx0 <= x0+TOL and sx1 >= x1-TOL and y0+TOL < sy0 and sy1 < y1-TOL:
        return (x0, y0, x1, sy0), (x0, sy1, x1, y1)
    if sy0 <= y0+TOL and sy1 >= y1-TOL and x0+TOL < sx0 and sx1 < x1-TOL:
        return (x0, y0, sx0, y1), (sx1, y0, x1, y1)
    return None


def _strip(b, name):
    return [s for s in b.strips if s[4] == name][0]


def _seg_dist(p, a, b):
    return runs.pt_seg_dist(p, a, b)


def _segs_cross(a, b, c, d):
    """Proper or touching intersection of segments ab and cd, in plan."""
    def orient(p, q, r):
        v = (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
        return 0 if abs(v) < TOL else (1 if v > 0 else -1)
    def on(p, q, r):
        return min(p[0], r[0])-TOL <= q[0] <= max(p[0], r[0])+TOL and min(p[1], r[1])-TOL <= q[1] <= max(p[1], r[1])+TOL
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4: return True
    return (o1 == 0 and on(a, c, b)) or (o2 == 0 and on(a, d, b)) or (o3 == 0 and on(c, a, d)) or (o4 == 0 and on(c, b, d))


def _clear(p, what):
    """Edge-to-edge clearance from point p (a 3" pipe) to a polyline of diameter od."""
    name, path, od = what
    if len(path) == 1:
        d = math.hypot(p[0]-path[0][0], p[1]-path[0][1])
    else:
        d = min(_seg_dist(p, a, c) for a, c in zip(path, path[1:]))
    return d - PIPE_OD/2.0 - od/2.0


def _rect_edges(s):
    x0, y0, x1, y1 = s[:4]
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]


def _attic_of(roof, x, y):
    for a in roof.attics:
        if a.y0-TOL <= y <= a.y1+TOL:
            return a.name
    return None


def _in(v):
    """A size in whole inches: 21\", 36\"."""
    return '%d"' % round(v*12)


Area    = namedtuple('Area', 'building x0 y0 x1 y1')


def areas(b, *, f):
    """The separate gravel areas under building b's slab: inside the foundation wall,
       divided by every strip that runs wall to wall."""
    regions = [(f.WALL_T, f.WALL_T, b.W-f.WALL_T, b.D-f.WALL_T)]
    changed = True
    while changed:
        changed = False
        for s in b.strips:
            for i, r in enumerate(regions):
                h = _spans(s, r)
                if h:
                    regions[i:i+1] = list(h); changed = True; break
            if changed: break
    return [Area(b.name, *r) for r in regions]

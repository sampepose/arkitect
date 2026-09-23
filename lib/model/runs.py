"""Runs and rectangles in plan feet: the arithmetic a pipe, a duct or a conduit model needs.

A run is a polyline of axis-aligned segments, [(x, y), ...]; a rectangle is (x, y, w, h).
How far along a run a point lies, where two runs cross, whether they lie side by side and
how far apart, how near a run passes a rectangle. Pure geometry: no pipe size, no code
section, no project. It lived word for word in each project's drainage model until
2026-09-18, and its tests with one of them.
"""
import math

TOL = 1e-6


def length(path):
    return sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(path, path[1:]))


def same_point(p, q):
    return abs(p[0]-q[0]) < TOL and abs(p[1]-q[1]) < TOL


def on_segment(p, a, b):
    if abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])) > 1e-4: return False
    return (min(a[0], b[0])-TOL <= p[0] <= max(a[0], b[0])+TOL and
            min(a[1], b[1])-TOL <= p[1] <= max(a[1], b[1])+TOL)


def on_path(p, path):
    return any(on_segment(p, a, b) for a, b in zip(path, path[1:]))


def along(path, p):
    """Distance from the head of `path` to a point on it."""
    d = 0.0
    for a, b in zip(path, path[1:]):
        if on_segment(p, a, b): return d+math.hypot(p[0]-a[0], p[1]-a[1])
        d += math.hypot(b[0]-a[0], b[1]-a[1])
    raise ValueError('point is not on the path')


def pt_rect_dist(p, r):
    """Distance from a point to a rectangle (x, y, w, h); zero inside."""
    dx = max(r[0]-p[0], 0.0, p[0]-(r[0]+r[2])); dy = max(r[1]-p[1], 0.0, p[1]-(r[1]+r[3]))
    return math.hypot(dx, dy)


def seg_rect_dist(a, b, r):
    """Distance from an axis-aligned segment to a rectangle; zero if they touch."""
    if abs(a[0]-b[0]) < TOL:      # vertical
        x = a[0]; y0, y1 = sorted((a[1], b[1]))
        dx = max(r[0]-x, 0.0, x-(r[0]+r[2])); dy = max(r[1]-y1, 0.0, y0-(r[1]+r[3]))
    else:
        y = a[1]; x0, x1 = sorted((a[0], b[0]))
        dy = max(r[1]-y, 0.0, y-(r[1]+r[3])); dx = max(r[0]-x1, 0.0, x0-(r[0]+r[2]))
    return math.hypot(dx, dy)


def in_rect(p, r, tol=TOL):
    return r[0]-tol <= p[0] <= r[0]+r[2]+tol and r[1]-tol <= p[1] <= r[1]+r[3]+tol


def rects_overlap(a, b):
    return a[0] < b[0]+b[2]-TOL and b[0] < a[0]+a[2]-TOL and a[1] < b[1]+b[3]-TOL and b[1] < a[1]+a[3]-TOL


def grow(r, d):
    return (r[0]-d, r[1]-d, r[2]+2*d, r[3]+2*d)


def parallel(a, b, c, d):
    """Two axis-aligned segments run the same way and overlap in that direction:
       (True, perpendicular distance) or (False, None). A segment that is a point
       is neither."""
    va, vc = abs(a[0]-b[0]) < TOL, abs(c[0]-d[0]) < TOL
    if same_point(a, b) or same_point(c, d) or va != vc: return False, None
    if va:
        lo = max(min(a[1], b[1]), min(c[1], d[1])); hi = min(max(a[1], b[1]), max(c[1], d[1]))
        return (lo < hi-TOL), abs(a[0]-c[0])
    lo = max(min(a[0], b[0]), min(c[0], d[0])); hi = min(max(a[0], b[0]), max(c[0], d[0]))
    return (lo < hi-TOL), abs(a[1]-c[1])


def crossing(a, b, c, d):
    """Where two axis-aligned segments cross, or None."""
    va, vc = abs(a[0]-b[0]) < TOL, abs(c[0]-d[0]) < TOL
    if va == vc: return None
    if not va: a, b, c, d = c, d, a, b
    x, y = a[0], c[1]
    if (min(a[1], b[1])-TOL <= y <= max(a[1], b[1])+TOL and
            min(c[0], d[0])-TOL <= x <= max(c[0], d[0])+TOL):
        return (x, y)
    return None


def pt_seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay
    L2 = dx*dx+dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(ax+t*dx-px, ay+t*dy-py)


def points(path, step=0.05):
    """Points along a polyline, every `step` feet or closer, both ends included."""
    for a, b in zip(path, path[1:]):
        n = max(1, int(math.ceil(math.hypot(b[0]-a[0], b[1]-a[1])/step)))
        for k in range(n+1):
            yield (a[0]+(b[0]-a[0])*k/n, a[1]+(b[1]-a[1])*k/n)

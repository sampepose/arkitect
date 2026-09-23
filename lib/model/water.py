"""A dwelling's water supply as a model holds it: fixtures, the runs from a manifold to them,
a unit on a level, a building with its service and trunks — and the small geometry the checks
ask of them. Records and accessors only: sizing is codes/ohio/water_supply.py's, and where the
pipes are is the project's.
"""
import math


def _mirror(r, W):
    return (W-(r[0]+r[2]), r[1], r[2], r[3])+tuple(r[4:])


def _rects(items, plan, W, kinds):
    return [_mirror(plan.rect(f), W)[:4] for f in items if f[4] in kinds]


def _one(items, plan, W, kind):
    return _rects(items, plan, W, (kind,))[0]


def _length(path):
    return sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(path, path[1:]))


def _nearest_on_segment(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay
    L2 = dx*dx+dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/L2))
    return ax+t*dx, ay+t*dy


def _rect_point(r, p):
    """The point of rectangle r nearest p — on its edge when p is outside."""
    x, y, w, h = r[:4]
    return min(max(p[0], x), x+w), min(max(p[1], y), y+h)


def stub(run, fixture, where=False):
    """Where a fixture leaves its run: (the point on the path, the point on the fixture).
       The path is searched for the point nearest the fixture's center; the fixture end
       is the edge of its rectangle nearest that point. With `where`, the index of the
       segment the point is on comes too."""
    c = (fixture.x+fixture.w/2.0, fixture.y+fixture.h/2.0)
    best = None
    for i, (a, b) in enumerate(zip(run.path, run.path[1:])):
        q = _nearest_on_segment(c, a, b)
        d = math.hypot(q[0]-c[0], q[1]-c[1])
        if best is None or d < best[0]: best = (d, q, i)
    _d, q, i = best
    e = _rect_point(fixture, q)
    return (q, e, i) if where else (q, e)


def run_lines(run, fixtures):
    """(cold, hot): how many 1/2" lines the bundle carries — a cold to every fixture in
       it, a hot to all but the water closet. The heater's run is its 3/4" pair."""
    ks = [f.kind for f in fixtures if f.kind in run.fixtures]
    if ks == ['wh']: return 1, 1
    return len(ks), len([k for k in ks if k != 'wc'])


def run_fixtures(run, unit):
    return [f for f in unit.fixtures if f.kind in run.fixtures]


def _overlap_box(a, b):
    """(w, h) of the overlap of two (x, y, w, h) rectangles; zeros when they miss."""
    w = min(a[0]+a[2], b[0]+b[2]) - max(a[0], b[0])
    h = min(a[1]+a[3], b[1]+b[3]) - max(a[1], b[1])
    return (w, h) if w > 1e-9 and h > 1e-9 else (0.0, 0.0)


def unit_names(b):
    out = []
    for u in b.units:
        if u.name not in out: out.append(u.name)
    return out


def _inside_any(pt, rects, tol=1e-6):
    return any(r[0]-tol <= pt[0] <= r[0]+r[2]+tol and r[1]-tol <= pt[1] <= r[1]+r[3]+tol for r in rects)


def _overlap(a, b):
    return a[0] < b[0]+b[2] and b[0] < a[0]+a[2] and a[1] < b[1]+b[3] and b[1] < a[1]+a[3]

"""Polygon arithmetic shared by the two buildings.

Both open-plan areas are one polygon carrying two labels, and both have to say how many
square feet fall each side of the line between kitchen and living. Building 2 worked
that out from its own copy of these two functions; Building 1 typed the answer and went
stale by a square foot each. One copy, so the two buildings cannot drift apart in how
they measure the same thing.

These take REGRIDDED, page-space points — whatever `Plan.poly()` returns — because that
is the polygon the sheet actually draws, and it is a fraction of a foot off the authored
one. `inside` works in any one space; `beyond` is the exception, and checks the MODEL.
"""
import math



def area(pts):
    """The shoelace area of a closed polygon, in whatever unit its points are in."""
    n = len(pts)
    return abs(sum(pts[i][0]*pts[(i+1) % n][1] - pts[(i+1) % n][0]*pts[i][1]
                   for i in range(n))) / 2.0


def clip_x(pts, lo, hi):
    """The part of a RECTILINEAR polygon between x = lo and x = hi.

    Clamping every vertex works because the polygon is rectilinear: an edge crossing the
    cut is horizontal or vertical, so the clamped outline still traces the same region
    and the degenerate edges it leaves contribute nothing to the shoelace sum. It is not
    a general polygon clip and must not be used as one.
    """
    return [(min(max(x, lo), hi), y) for (x, y) in pts]


def clip_y(pts, lo, hi):
    """The part of a rectilinear polygon between y = lo and y = hi. See clip_x."""
    return [(x, min(max(y, lo), hi)) for (x, y) in pts]


def split(pts, at, axis='x'):
    """(area below `at`, area above `at`) for a rectilinear polygon cut on one axis.

    Returns both halves together so a caller cannot take one and forget that the other
    has to be measured the same way. The two always sum to area(pts).
    """
    vals = [p[0 if axis == 'x' else 1] for p in pts]
    lo, hi = min(vals), max(vals)
    cut = clip_x if axis == 'x' else clip_y
    return area(cut(pts, lo, at)), area(cut(pts, at, hi))


def inside(pt, pts):
    """True if a point lies inside a closed polygon (ray casting). A point exactly on an
       edge may fall either way, so a caller asking which room an opening serves moves
       it off the wall into the room first."""
    x, y = pt
    n, hit = len(pts), False
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i+1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0)*(x1 - x0)/(y1 - y0):
            hit = not hit
    return hit


def beyond(rooms, polys, furn, x_lo, x_hi, y_lo, y_hi):
    """The names of the rooms, open areas and fittings that reach past a building's
       inside faces, in whatever space the bounds are given in. In MODEL feet (Building
       2's use) it catches the case that made it necessary: the regrid remaps only
       coordinates inside the walls and passes anything past them through untouched, so
       something authored for a wider building draws straight through the wall while
       every other check passes. That is what the first squeeze of a project's Building 2
       did."""
    def out(pts):
        return any(x < x_lo-1e-6 or x > x_hi+1e-6 or y < y_lo-1e-6 or y > y_hi+1e-6
                   for x, y in pts)
    def rect(x, y, w, h):
        return [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
    bad  = [r[4] for r in rooms if out(rect(*r[:4]))]
    bad += [labels[0][2] if labels else 'open area' for poly, labels in polys if out(poly)]
    bad += [f[4] for f in furn if out(rect(*f[:4]))]
    return bad


def sloped_area(plan_sf, pitch):
    """The surface of a pitched roof whose PLAN area is plan_sf, `pitch` as rise over run
       (4:12 is 4/12). A roofer bids this, not the plan area: at 4:12 it is 5.4% more."""
    return plan_sf * math.hypot(1.0, pitch)

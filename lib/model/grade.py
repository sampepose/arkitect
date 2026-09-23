"""Finished grade as sections and bands: a section's grade at a distance from its wall, the
points along a band's edge, the stations a check samples, and splitting a face into bands
by what stands in front of it. Geometry only; the falls a code asks for are not here.
"""
import math
from collections import namedtuple
from lib.units import IN, inches


TOL = 1e-6


LANDING_MAX    = 0.02                 # R311.3: a landing at an exterior door, 1/4" per foot


Band = namedtuple("Band", "face s0 s1 section to")


def point(face, s, d):
    """The site point `d` feet out from the face at station `s` along it."""
    return (s, face.at+face.sign*d) if face.axis == "x" else (face.at+face.sign*d, s)


def _split(face, a, b, lo, hi, plain, shelf, receiver):
    """The bands of a lawn run from a to b along a face, shelved from lo to hi."""
    out = []
    for s0, s1, sec in ((a, lo, plain), (lo, hi, shelf), (hi, b, plain)):
        s0, s1 = max(s0, a), min(s1, b)
        if s1-s0 > TOL:
            out.append(Band(face, s0, s1, sec, receiver))
    return out


def stations(band):
    """Both ends and every foot between."""
    n = max(1, int(math.ceil((band.s1-band.s0)-TOL)))
    return [band.s0+(band.s1-band.s0)*i/n for i in range(n+1)]


def grade_along(pts, d):
    """The grade `d` out along a section; at a step or an edge, the foot of it."""
    foot = None
    for (d0, _g0, _a), (d1, g1, _b) in zip(pts, pts[1:]):
        if d1 <= d0+TOL and abs(d0-d) <= TOL: foot = g1
    if foot is not None:
        return foot
    for (d0, g0, _a), (d1, g1, _b) in zip(pts, pts[1:]):
        if d1 > d0+TOL and d0-TOL <= d <= d1+TOL:
            return g0+(g1-g0)*(min(max(d, d0), d1)-d0)/(d1-d0)
    return pts[-1][1] if d > pts[-1][0] else pts[0][1]


EDGE_EPS = 0.01                       # 1/8": the foot is read just outside, the corners just inside


def top_at(step, x, y):
    """The surface of a landing or stoop at a site point: its top at its face, falling 2%."""
    f = step.face
    return step.top-((y if f.axis == "x" else x)-f.at)*f.sign*LANDING_MAX


def edge_points(rect, side, lo=None, hi=None):
    """(nosing x, y, foot x, y) along one side of a rectangle, both ends and every foot."""
    a0, a1 = (rect.y0, rect.y1) if side[0] == "x" else (rect.x0, rect.x1)
    a0 = a0 if lo is None else max(a0, lo); a1 = a1 if hi is None else min(a1, hi)
    a0, a1 = a0+EDGE_EPS, a1-EDGE_EPS
    n = max(1, int(math.ceil((a1-a0)-TOL)))
    fixed = getattr(rect, side); out = 1.0 if side[1] == "1" else -1.0
    for i in range(n+1):
        t = a0+(a1-a0)*i/n
        if side[0] == "x": yield fixed, t, fixed+out*EDGE_EPS, t
        else:              yield t, fixed, t, fixed+out*EDGE_EPS


def _overlaps(a, b):
    return a[0] < b[2]-TOL and b[0] < a[2]-TOL and a[1] < b[3]-TOL and b[1] < a[3]-TOL


def _touch(a, b):
    """The length along which rectangles a and b share an edge; 0.0 where they do not."""
    if abs(a.x1-b.x0) < TOL or abs(b.x1-a.x0) < TOL:
        return max(0.0, min(a.y1, b.y1)-max(a.y0, b.y0))
    if abs(a.y1-b.y0) < TOL or abs(b.y1-a.y0) < TOL:
        return max(0.0, min(a.x1, b.x1)-max(a.x0, b.x0))
    return 0.0


def signed(v):
    """A grade in inches with its sign: +5-1/2", 0", -6"."""
    if abs(v) < IN(1)/16.0: return '0"'
    s = inches(abs(v))
    return ("+" if v > 0 else "-")+(s[2:] if s.startswith("0-") else s)      # -3/8", not -0-3/8"


def grade_at(x, y, bands):
    """Finished grade at a site point, from the band whose strip holds it; None outside every one."""
    for b in bands:
        f = b.face
        s, d = (x, (y-f.at)*f.sign) if f.axis == "x" else (y, (x-f.at)*f.sign)
        if b.s0-TOL <= s <= b.s1+TOL and d > TOL:
            pts = b.section(s)
            if d <= pts[-1][0]+TOL:
                return grade_along(pts, d)
    return None

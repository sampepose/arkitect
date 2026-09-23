"""A framed floor as a model checks it: every bay ends on a bearing line, spans no more than
its joist or truss depth allows, and the bays tile the floor's outline.

A project hands floor_violations() its own Floor records, its span limits and the function
that gives a floor's bearing lines.
"""
from lib.units import fmt
from lib.model.regrid import EXT_STUD


def bay_span(b):
    return (b.x1-b.x0) if b.run == 'h' else (b.y1-b.y0)


def _on_line(v, o, lines, tol=0.02):
    """Is the bay edge at coordinate v (an x if o == 'x', else a y) on a bearing line —
       either a vertical/horizontal line at v, or within a strip's width?"""
    for x0, y0, x1, y1, nm in lines:
        if o == 'x' and x0-tol <= v <= x1+tol and (x1-x0) < 2.0: return True
        if o == 'y' and y0-tol <= v <= y1+tol and (y1-y0) < 2.0: return True
    return False


def floor_violations(floor, bearing_lines=None, *, max_span, _bearing_lines):
    lines = bearing_lines if bearing_lines is not None else _bearing_lines(floor)
    v = []
    for b in floor.bays:
        ends = ((b.x0, 'x'), (b.x1, 'x')) if b.run == 'h' else ((b.y0, 'y'), (b.y1, 'y'))
        for val, o in ends:
            if not _on_line(val, o, lines):
                v.append('%s %s: the edge at %s %s does not end on a bearing line' % (floor.name, b.name, o, fmt(val)))
        if bay_span(b) > max_span.get(b.joist, 26.0)+1e-9:
            v.append('%s %s: %s span past the %s limit for %s joists' % (floor.name, b.name, fmt(bay_span(b)), fmt(max_span.get(b.joist, 26.0)), fmt(b.joist)))
    # the bays tile the floor: within each floor's outline, the union of the bays and the
    # walls between them is the whole area. Checked as: bays do not overlap, and the area
    # of bays plus the bearing-wall slivers between them equals the outline's.
    area = 0.0
    for b in floor.bays:
        area += (b.x1-b.x0)*(b.y1-b.y0)
        for c in floor.bays:
            if c is not b and b.x0 < c.x1-1e-9 and c.x0 < b.x1-1e-9 and b.y0 < c.y1-1e-9 and c.y0 < b.y1-1e-9:
                v.append('%s: bays %s and %s overlap' % (floor.name, b.name, c.name))
    outline = _outline_area(floor)
    if abs(area-outline) > 0.5:
        v.append('%s: the floor does not tile: %.1f SF of bays in a %.1f SF outline' % (floor.name, area, outline))
    for w in floor.wells:
        host = [b for b in floor.bays if b.x0-1e-9 <= w.x0 and w.x1 <= b.x1+1e-9 and b.y0-1e-9 <= w.y0 and w.y1 <= b.y1+1e-9]
        if not host:
            v.append('%s: the well at (%s, %s) is outside every bay' % (floor.name, fmt(w.x0), fmt(w.y0)))
        if not _on_line(w.header_x0, 'x', lines) and not _on_line((w.header_x0+w.header_x1)/2.0, 'x', lines):
            v.append('%s: the well header at x %s is not on a bearing line' % (floor.name, fmt(w.header_x0)))
    return v


def _outline_area(floor):
    """The floor's own Level 2 plate outline, SF: the real buildings carry theirs as
       outline_sf; a synthetic test floor with none falls back to the generic exterior-
       stud rectangle, so the tile check compares against THIS floor, not a building's
       name."""
    if floor.outline_sf is not None:
        return floor.outline_sf
    return (floor.W-2*EXT_STUD)*(floor.D-2*EXT_STUD)


def joist_lines(b, *, joist_oc):
    """Every joist inside the bay at JOIST_OC from its first bearing edge; the rims at the
       edges are drawn separately."""
    out = []
    if b.run == 'h':
        y = b.y0+joist_oc
        while y < b.y1-1e-9:
            out.append((b.x0, y, b.x1, y)); y += joist_oc
    else:
        x = b.x0+joist_oc
        while x < b.x1-1e-9:
            out.append((x, b.y0, x, b.y1)); x += joist_oc
    return out

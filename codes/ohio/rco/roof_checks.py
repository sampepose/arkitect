"""A trussed gable roof as a model checks it: where the trusses stand, and what a roof and
the attic hatches under it must satisfy (RCO 807.1's hatch, a hatch's room, the ceiling
devices near it, the band where nothing may be cut, 806.2's ventilation).

A project hands these its own Roof records, rooms, devices, penetrations and truss spacing.
"""
from lib.units import IN
from codes.ohio.rco.attic_ventilation import attic_vents


MAX_SPAN   = 40.0           # a truss bay wider than this fails the build; not a sizing


# RCO R807.1: 22" x 30" minimum rough opening, 30" headroom. The 22" runs ACROSS the
# trusses, inside the 22-1/2" clear between them at 24" o.c.; the 30" runs along them.
HATCH_L   = IN(30)          # along the trusses, page x


HATCH_W   = IN(22)          # across them, page y


HATCH_CLR = IN(6)           # a hatch keeps this clear of any ceiling device


def truss_span(b):
    return b.x1-b.x0


def _inside(pt, poly):
    x, y = pt; n = len(poly); c = False
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i+1) % n]
        if (y0 > y) != (y1 > y) and x < (x1-x0)*(y-y0)/(y1-y0)+x0:
            c = not c
    return c


def roof_violations(roof, rooms, devices, pens=None, *, truss_oc):
    """Everything that would put a line on S-103 the plans contradict.

    rooms:   {unit: polygon} in the hatch's own frame — the ceiling the hatch is in.
    devices: {unit: [(x, y), ...]} the ceiling devices in that frame.
    pens:    [(x, y, name), ...] every penetration of this roof; the roof's own vents
             when omitted."""
    v = []; tol = 1e-6
    pens = list(roof.vents) if pens is None else pens
    for b in roof.bays:
        for x in (b.x0, b.x1):
            if not any(abs(x-bx0) < tol or abs(x-bx1) < tol for bx0, _y0, bx1, _y1, _n in roof.bearing):
                v.append('%s: truss bay does not end on a bearing line at x %.3f' % (roof.name, x))
        if truss_span(b) > MAX_SPAN:
            v.append('%s: truss span %.2f ft over %.0f' % (roof.name, truss_span(b), MAX_SPAN))
        if abs(b.y0) > tol or abs(b.y1-roof.D) > tol:
            v.append('%s: truss bay does not run gable to gable' % roof.name)
    if roof.w4_band:
        lo, hi = roof.w4_band
        if lo < 0 or hi > roof.D:
            v.append('%s: the W4 band leaves the roof' % roof.name)
        for x, y, nm in roof.vents:
            if lo-tol < y < hi+tol:
                v.append('%s: %s penetrates the W4 band' % (roof.name, nm))
    for av in attic_vents(roof, pens):
        if av.provided < av.required-tol:
            v.append('%s: net free area %d sq in, under the %d sq in of 806.2' % (av.attic.name, round(av.provided), round(av.required)))
    for x, y, nm in roof.vents:
        if not (0 < x < roof.W and 0 < y < roof.D):
            v.append('%s: %s is off the roof' % (roof.name, nm))
    hx, hy = HATCH_L/2.0, HATCH_W/2.0
    for h in roof.hatches:
        x0, y0, x1, y1 = h.page
        if x1-x0 < HATCH_L-tol or y1-y0 < HATCH_W-tol:
            v.append('%s: hatch under 22 x 30' % h.unit)
        if y1-y0 > truss_oc-IN(1.5)+tol:
            v.append('%s: hatch wider across the trusses than the space between them' % h.unit)
        if not (0 < x0 and x1 < roof.W and 0 < y0 and y1 < roof.D):
            v.append('%s: hatch off the roof' % h.unit)
        # a ceiling hatch is not a roof opening, so the FRT band does not bar it; W4
        # itself does — the hatch has to be wholly inside one attic
        if roof.w4 and not (y1 < roof.w4[0] or y0 > roof.w4[1]):
            v.append('%s: hatch across W4' % h.unit)
        poly = rooms.get(h.unit)
        if poly is None:
            v.append('%s: no room polygon to check the hatch against' % h.unit); continue
        for cx, cy in ((h.cx-hx, h.cy-hy), (h.cx+hx, h.cy-hy), (h.cx+hx, h.cy+hy), (h.cx-hx, h.cy+hy)):
            if not _inside((cx, cy), poly):
                v.append('%s: hatch corner (%.2f, %.2f) outside %s' % (h.unit, cx, cy, h.room)); break
        for dx, dy in devices.get(h.unit, ()):
            ddx = max(h.cx-hx-dx, dx-(h.cx+hx), 0.0); ddy = max(h.cy-hy-dy, dy-(h.cy+hy), 0.0)
            if (ddx*ddx+ddy*ddy) ** 0.5 < HATCH_CLR-tol:
                v.append('%s: hatch within %.0f" of the ceiling device at (%.2f, %.2f)' % (h.unit, HATCH_CLR*12, dx, dy))
    return v


def truss_lines(b, *, truss_oc):
    """Every common truss in the bay at TRUSS_OC from its first gable end, as
       (x0, y, x1, y); the gable-end trusses stand on the end walls and the sheet draws
       them there. The typical layout — the manufacturer's governs."""
    out = []; n = 1
    while b.y0+n*truss_oc < b.y1-1e-9:
        y = b.y0+n*truss_oc
        out.append((b.x0, y, b.x1, y)); n += 1
    return out

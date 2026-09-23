"""NEC 2023 walked over one dwelling's rooms: the device, circuit and unit records, and the
checks a dwelling's electrical plan is held to before anything draws.

Receptacle spacing along every wall line (210.52(A)), counters, lavatories, laundry, halls,
switched lighting outlets (210.70), smoke and CO alarms, GFCI and AFCI by circuit (210.8,
210.12), individual branch circuits, MCA and MOCP, conductor sizes, panel spaces.

A project hands check_unit() a UnitType of Levels built from ITS room polygons, doors,
openings and device lists; nothing here knows a lot. It lived word for word in each
project's electrical model until 2026-09-18.
"""
# ================================ the types ================================
import math
from collections import namedtuple
from lib.units import fmt
from lib.symbols.electrical import LAYER, stand_off

# (x, y) in the unit's own plan feet; kind from lib/symbols/electrical.py LAYER; mount
# is which side the wall is on ('n' 's' 'e' 'w'), 'c' for a ceiling device, or 'w5'
# for the furred chase face at Building 1's separation; tag pairs a switch with what it
# controls; circuit is the schedule number.
Device = namedtuple('Device', 'x y kind mount circuit tag')

# n is the schedule number; amps and poles the breaker; wire the copper conductor;
# prot the protection printed ('AFCI', 'GFCI', 'AFCI/GFCI' or '—'); kind is the rule
# the circuit answers to: ltg rcpt sa bath laundry dw range dryer wh hp house spare.
# mca and mocp are a heat pump's nameplate, and the only sizing rule it has.
Circuit = namedtuple('Circuit', 'n desc amps poles wire prot kind mca mocp')

# stacked: each level is a separate dwelling (Units 2/3, 4/5), so the per-unit rules
# run per level; Unit 1's two levels are one dwelling.
UnitType = namedtuple('UnitType', 'name panel_a levels circuits stacked', defaults=(False,))


class Level:
    """One level of one unit type, in the unit's own coordinates.

    devices    the Device list
    rooms      rectangles (x, y, w, h, name[, ...]): the model's room rects
    polys      (points, name): the model's open areas and the rooms authored as polygons
    doors      (x, y, len, o) door and cased openings, the cuts in the wall line
    ext_req    (x, y, why): the points an exterior receptacle must serve, 210.52(E)
    counters   kitchen counter rects, 210.52(C); dividers the range and sink rects that
               split them into separate spaces
    kitchens   the kitchen's extent inside an open plan, for 210.8 and 210.11(C)
    lavs, wds, sinks   the rects the 3', 6' and 6' rules are measured from
    sep_y      the y of the W4 separation line, or None
    """
    def __init__(s, name, devices, rooms=(), polys=(), doors=(), ext_req=(), counters=(),
                 dividers=(), kitchens=(), lavs=(), wds=(), sinks=(), sep_y=None):
        s.name, s.devices = name, list(devices)
        s.rooms, s.polys, s.doors = list(rooms), list(polys), list(doors)
        s.ext_req, s.counters, s.dividers = list(ext_req), list(counters), list(dividers)
        s.kitchens = list(kitchens)
        s.lavs, s.wds, s.sinks, s.sep_y = list(lavs), list(wds), list(sinks), sep_y


def dev(x, y, kind, mount, circuit=None, tag=''):
    assert kind in LAYER, "no such device kind %r" % kind
    assert circuit is not None or kind == 'panel', "%s at (%s, %s) has no circuit" % (kind, x, y)
    return Device(float(x), float(y), kind, mount, circuit, tag)


def ckt(n, desc, amps, poles, wire, prot, kind, mca=None, mocp=None):
    return Circuit(n, desc, amps, poles, wire, prot, kind, mca, mocp)


# ================================ the rules ================================
RCPT = ('dup', 'gfci', 'fridge')           # what counts along the wall line, 210.52(A)
GENERAL = ('dup', 'gfci', 'wp')            # what a general-purpose circuit may carry
GFCI_KINDS = ('gfci', 'wp')                # protected at the device
LUM = ('lt', 'rec')
HABITABLE = ('LIVING', 'DINING', 'KITCHEN', 'BEDROOM')
NOT_LIT = ('CL.', 'CLOSET', 'STORAGE', 'LINEN', 'PANTRY', 'STOR.')
WET = ('KITCHEN', 'BATH', 'LAUNDRY', 'MECH')   # every mechanical closet here holds the laundry
# 210.8(A) as RCO 3401.1 modifies it: 125 V single-phase 15 and 20 A receptacles only, so the
# 240 V range and dryer receptacles are outside it and the hardwired water heater never was in.
PROTECT = GENERAL+('dw', 'fridge')
OUTLETS = PROTECT+('wh', 'range', 'dryer')   # what a unit's receptacle count counts
INDIVIDUAL = {'range': ('range',), 'dryer': ('dryer',), 'dw': ('dw', 'fridge'), 'wh': ('wh',),
              'hp': ('head', 'ahu', 'tstat')}
# copper, 240.4(D) for #14–#10, the 75 °C column of Table 310.16 above
WIRE_AMPS = {'#14': 15, '#12': 20, '#10': 30, '#8': 50, '#6': 65, '#4': 85, '#3': 100, '#2': 115,
             '#1': 130, '#1/0': 150, '#2/0': 175, '#3/0': 200, '#4/0': 230}
STD_RATINGS = (100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400)   # 240.6(A)
# Panelboard sizes a load centre is actually made in. A unit panel is specified by the
# spaces it must have, not by the spaces its schedule happens to fill: the water heater
# added a 2-pole circuit to every dwelling, so the count is derived and printed rather
# than typed on a sheet where it could go stale.
PANEL_SIZES = (20, 24, 30, 40, 42)
PANEL_MIN = 20              # no unit panel smaller than this, whatever its pole count
PANEL_SPARE = 2             # spaces left open for future circuits


def panel_spaces(circuits):
    """(poles used, spaces specified) for a unit panel: every pole its schedule needs,
       plus PANEL_SPARE, rounded up to a size panelboards are made in and never under
       PANEL_MIN."""
    used = sum(c.poles for c in circuits)
    want = max(PANEL_MIN, used+PANEL_SPARE)
    for n in PANEL_SIZES:
        if n >= want: return used, n
    raise ValueError('no panelboard carries %d spaces' % want)
EGC_TABLE_250_122 = [(15, '#14'), (20, '#12'), (60, '#10'), (100, '#8'), (200, '#6'), (300, '#4')]


def wire_ok(wire, amps):
    return WIRE_AMPS[wire] >= amps


def egc_min(ocpd):
    """Table 250.122, copper."""
    for a, w in EGC_TABLE_250_122:
        if ocpd <= a: return w
    return '#3'


def hp_violations(ck):
    """440: the breaker is the nameplate MOCP and the conductor carries the MCA. The
       breaker-to-wire lookup for general circuits does not apply. No GFCI is asked of it:
       RCO 3401.1 adds 210.8(F) Exception No. 2, "GFCI protection is not required for listed
       HVAC equipment", with no expiry."""
    if ck.mca is None or ck.mocp is None:
        return ['heat-pump circuit %s has no nameplate MCA / MOCP' % ck.n]
    out = []
    if ck.amps != ck.mocp:
        out.append('heat-pump circuit %s breaker %s A is not its MOCP %s A' % (ck.n, ck.amps, ck.mocp))
    if WIRE_AMPS[ck.wire] < ck.mca:
        out.append('heat-pump circuit %s wire %s carries less than its MCA %s A' % (ck.n, ck.wire, ck.mca))
    return out


# ---- geometry: the wall line, and what is where ----
def _inside(pt, poly):
    x, y = pt; n = len(poly); inside = False
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i+1) % n]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y-y0)*(x1-x0)/(y1-y0)
            if x < xi: inside = not inside
    return inside


def _rect_poly(r):
    x, y, w, h = r[:4]
    return [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]


def _room_at(pt, lv):
    """The name of the space a point is in, or None."""
    for pts, nm in lv.polys:
        if _inside(pt, pts): return nm
    for r in lv.rooms:
        if _inside(pt, _rect_poly(r)): return r[4]
    return None


def _room_of(d, lv):
    """The name of the space a device is in, its wall stand-off taken into the room."""
    return _room_at(stand_off(d.x, d.y, d.mount), lv)


# The mechanical model asks the same question of a head or a fan, so the lookup is
# public under its own name.
room_of = _room_of


def _edges(poly):
    """[(a, b, s0, s1)]: each edge with its start and end distance along the loop."""
    out = []; s = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i+1) % len(poly)]
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        out.append((a, b, s, s+L)); s += L
    return out, s


def _along(pt, edges, tol):
    """Distance along the loop of a point within tol of an edge, or None."""
    x, y = pt
    for a, b, s0, s1 in edges:
        if abs(a[1]-b[1]) < 1e-9 and abs(y-a[1]) <= tol and min(a[0], b[0])-tol <= x <= max(a[0], b[0])+tol:
            return s0 + min(max(abs(x-a[0]), 0.0), s1-s0)
        if abs(a[0]-b[0]) < 1e-9 and abs(x-a[0]) <= tol and min(a[1], b[1])-tol <= y <= max(a[1], b[1])+tol:
            return s0 + min(max(abs(y-a[1]), 0.0), s1-s0)
    return None


def _overlap(seg, edge, tol):
    """The (s0, s1) of the loop covered by a segment lying along an edge within tol, or None."""
    (p0, p1), (a, b, s0) = seg, edge[:3]
    horiz = abs(a[1]-b[1]) < 1e-9
    i, j = (0, 1) if horiz else (1, 0)         # along the edge, and across it
    if abs(p0[j]-p1[j]) > 1e-9 or abs(p0[j]-a[j]) > tol: return None
    lo = max(min(p0[i], p1[i]), min(a[i], b[i])); hi = min(max(p0[i], p1[i]), max(a[i], b[i]))
    if hi-lo <= 1e-6: return None
    c0, c1 = s0+abs(lo-a[i]), s0+abs(hi-a[i])
    return (min(c0, c1), max(c0, c1))


def _cuts(edges, doors, rects):
    """The (s0, s1) intervals of the loop that are not wall space: doorways and cased
       openings (authored on either face of the wall, so within half a foot), the wall
       behind kitchen counters and ranges, which 210.52(C) covers, and any edge the
       polygon doubles back along — a closet notch drawn as a spike has no wall there."""
    segs = []
    for (x, y, ln, o) in doors:
        segs.append((((x, y), (x+ln, y)) if o == 'h' else ((x, y), (x, y+ln)), 0.5))
    for r in rects:
        x, y, w, h = r[:4]
        segs += [(s, 0.06) for s in (((x, y), (x+w, y)), ((x, y+h), (x+w, y+h)),
                                     ((x, y), (x, y+h)), ((x+w, y), (x+w, y+h)))]
    cuts = []
    for seg, tol in segs:
        for e in edges:
            c = _overlap(seg, e, tol)
            if c: cuts.append(c)
    for i, e in enumerate(edges):
        for j, f in enumerate(edges):
            if i != j:
                c = _overlap((e[0], e[1]), f, 1e-6)
                if c: cuts.append(c)
    cuts = sorted(cuts)
    merged = []
    for c0, c1 in cuts:
        if merged and c0 <= merged[-1][1]+1e-9: merged[-1] = (merged[-1][0], max(merged[-1][1], c1))
        else: merged.append((c0, c1))
    return merged


def _runs(total, cuts):
    """The wall-space runs between cuts, as (start, end) along the loop; the last one
       wraps past `total` back to the first cut."""
    if not cuts: return [(0.0, total)]
    runs = []
    for (a0, a1), (b0, b1) in zip(cuts, cuts[1:]):
        if b0-a1 > 1e-9: runs.append((a1, b0))
    tail = cuts[0][0] + total - cuts[-1][1]
    if tail > 1e-9: runs.append((cuts[-1][1], cuts[-1][1]+tail))
    return runs


def _walk(poly, doors, rects, rcpt_pts):
    """210.52(A)(1): within each run of wall space no point is more than 6' from a
       receptacle; a run under 2' needs none. Returns (run length, why) per failure."""
    edges, total = _edges(poly)
    cuts = _cuts(edges, doors, rects)
    ss = [s for s in (_along(pt, edges, 0.1) for pt in rcpt_pts) if s is not None]   # on this wall, not the far side of it
    bad = []
    for r0, r1 in _runs(total, cuts):
        L = r1-r0
        if L < 2.0-1e-9: continue
        pts = sorted(t for s in ss for t in (s-r0, s+total-r0) if -1e-9 <= t <= L+1e-9)
        if not pts: bad.append((L, 'a %s run with no receptacle' % fmt(L))); continue
        if pts[0] > 6.0+1e-9: bad.append((L, 'first receptacle %s from the run start' % fmt(pts[0])))
        if L-pts[-1] > 6.0+1e-9: bad.append((L, 'last receptacle %s from the run end' % fmt(L-pts[-1])))
        for a, b in zip(pts, pts[1:]):
            if b-a > 12.0+1e-9: bad.append((L, '%s between receptacles' % fmt(b-a)))
    return bad


def _near_rect(pt, r, d):
    x, y = pt; x0, y0, w, h = r[:4]
    dx = max(x0-x, 0.0, x-(x0+w)); dy = max(y0-y, 0.0, y-(y0+h))
    return math.hypot(dx, dy) <= d+1e-9


def _counter_spaces(counter, dividers):
    """(lo, hi) along the counter's long axis, split wherever a range or sink lies in it."""
    x0, y0, w, h = counter[:4]
    horiz = w >= h
    lo, hi = (x0, x0+w) if horiz else (y0, y0+h)
    spans = [(lo, hi)]
    for r in dividers:
        rx, ry, rw, rh = r[:4]
        if not (rx < x0+w-1e-9 and rx+rw > x0+1e-9 and ry < y0+h-1e-9 and ry+rh > y0+1e-9): continue
        d0, d1 = (rx, rx+rw) if horiz else (ry, ry+rh)
        nxt = []
        for a, b in spans:
            if d0 > a+1e-9: nxt.append((a, min(b, d0)))
            if d1 < b-1e-9: nxt.append((max(a, d1), b))
        spans = nxt
    return horiz, spans


def _f(v):
    return fmt(v)


def check_level(lv, cks, allsw):
    """Every per-level rule. `cks` is the unit's circuits by number; `allsw` its switches
       on every level, because a stair is switched from both."""
    v = []
    devs = lv.devices
    def protected(d):
        c = cks.get(d.circuit)
        return d.kind in GFCI_KINDS or (c is not None and 'GFCI' in c.prot)
    def switched(tag):
        return [s for s in allsw if s.tag == tag]
    spaces = [(pts, nm) for pts, nm in lv.polys] + [(_rect_poly(r), r[4]) for r in lv.rooms]
    rcpt_pts = [(d.x, d.y) for d in devs if d.kind in RCPT]
    counter_walls = list(lv.counters)+list(lv.dividers)
    # 210.52(A): the wall line of every habitable room
    for pts, nm in lv.polys:
        if not any(k in nm.upper() for k in HABITABLE): continue
        for L, why in _walk(pts, lv.doors, counter_walls, rcpt_pts):
            v.append('%s %s: 210.52(A) %s' % (lv.name, nm, why))
    # 210.52(H): a hall 10' or longer has one
    for pts, nm in spaces:
        if 'HALL' not in nm.upper(): continue
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        length = max(max(xs)-min(xs), max(ys)-min(ys))
        if length >= 10.0-1e-9 and not any(d.kind in RCPT and _room_of(d, lv) == nm for d in devs):
            v.append('%s %s: 210.52(H) a hall %s long has no receptacle' % (lv.name, nm, _f(length)))
    # 210.52(C): countertop spaces 12" or wider, a receptacle within 24" of every point
    for r in lv.counters:
        horiz, spans = _counter_spaces(r, lv.dividers)
        for lo, hi in spans:
            if hi-lo < 1.0-1e-9: continue
            along = sorted((d.x if horiz else d.y) for d in devs
                           if d.kind == 'gfci' and _near_rect((d.x, d.y), r, 0.8) and lo-0.05 <= (d.x if horiz else d.y) <= hi+0.05)
            ok = bool(along) and along[0]-lo <= 2.0+1e-9 and hi-along[-1] <= 2.0+1e-9 \
                 and all(b-a <= 4.0+1e-9 for a, b in zip(along, along[1:]))
            if not ok:
                v.append('%s: 210.52(C) the counter space %s to %s along (%s, %s) is not served within 24"'
                         % (lv.name, _f(lo), _f(hi), _f(r[0]), _f(r[1])))
    # 210.52(D): within 3' of each lavatory
    for r in lv.lavs:
        if not any(d.kind == 'gfci' and _near_rect((d.x, d.y), r, 3.0) for d in devs):
            v.append('%s: 210.52(D) no GFCI receptacle within 3\'-0" of the lavatory at (%s, %s)' % (lv.name, _f(r[0]), _f(r[1])))
    # 210.52(E): an exterior receptacle at each point the unit is required one
    for (x, y, why) in lv.ext_req:
        if not any(d.kind == 'wp' and math.hypot(d.x-x, d.y-y) <= 8.0 for d in devs):
            v.append('%s: 210.52(E) no exterior receptacle within 8\'-0" of %s at (%s, %s)' % (lv.name, why, _f(x), _f(y)))
    # 210.52(F): a laundry-circuit receptacle within 6' of the washer
    for r in lv.wds:
        if not any(d.kind in ('dup', 'gfci') and _near_rect((d.x, d.y), r, 6.0)
                   and cks.get(d.circuit) is not None and cks[d.circuit].kind == 'laundry' for d in devs):
            v.append('%s: 210.52(F) no laundry-circuit receptacle within 6\'-0" of the washer at (%s, %s)' % (lv.name, _f(r[0]), _f(r[1])))
    # 210.70: a switched luminaire in every space but the closets; a stair from both levels
    for pts, nm in spaces:
        up = nm.upper()
        if any(k in up for k in NOT_LIT): continue
        lums = [d for d in devs if d.kind in LUM and _room_of(d, lv) == nm]
        if not lums:
            v.append('%s %s: 210.70 no luminaire' % (lv.name, nm)); continue
        for d in lums:
            sw = switched(d.tag)
            if not sw:
                v.append('%s %s: 210.70 luminaire %r has no switch' % (lv.name, nm, d.tag))
            elif 'STAIR' in up and (len(sw) < 2 or any(s.kind != 'sw3' for s in sw)):
                v.append('%s %s: 210.70(A)(2)(c) the stair luminaire %r is not switched at both levels' % (lv.name, nm, d.tag))
    for (x, y, why) in lv.ext_req:
        if 'door' not in why: continue
        exts = [d for d in devs if d.kind == 'ext' and math.hypot(d.x-x, d.y-y) <= 5.0]
        if not exts:
            v.append('%s: 210.70(A)(2)(b) no exterior luminaire at %s at (%s, %s)' % (lv.name, why, _f(x), _f(y)))
        for d in exts:
            if not switched(d.tag):
                v.append('%s: 210.70(A)(2)(b) exterior luminaire %r has no switch inside' % (lv.name, d.tag))
    # RCO R314 / R315: alarms in every sleeping room and outside them on every level
    beds = [nm for _p, nm in spaces if 'BED' in nm.upper()]
    if not spaces:                       # a house list: exterior devices on a building's walls
        for d in devs:
            if d.kind not in ('ext', 'wp'):
                v.append('%s: %s at (%s, %s) — a house list carries only exterior luminaires and receptacles' % (lv.name, d.kind, _f(d.x), _f(d.y)))
        return v
    for nm in beds:
        if not any(d.kind == 'sd' and _room_of(d, lv) == nm for d in devs):
            v.append('%s %s: RCO 314 no smoke alarm in the sleeping room' % (lv.name, nm))
    if not any(d.kind == 'sd' and _room_of(d, lv) not in beds for d in devs):
        v.append('%s: RCO 314 no smoke alarm outside the sleeping rooms on this level' % lv.name)
    if not any(d.kind == 'co' and _room_of(d, lv) not in beds for d in devs):
        v.append('%s: RCO 315 no carbon monoxide alarm outside the sleeping rooms on this level' % lv.name)
    # W4: nothing in the separation; the chase-face devices are mounted 'w5'
    if lv.sep_y is not None:
        for d in devs:
            if abs(d.y-lv.sep_y) < 0.05 and d.mount not in ('w5', 'w5s'):
                v.append('%s: W4 — %s at (%s, %s) is on the separation line; mount it on the W5 chase' % (lv.name, d.kind, _f(d.x), _f(d.y)))
    # bath fans: each bath has one, on its own switch, shared with no luminaire
    for pts, nm in spaces:
        if 'BATH' in nm.upper() and not any(d.kind in ('fanc', 'fan') and _room_of(d, lv) == nm for d in devs):
            v.append('%s %s: no exhaust fan' % (lv.name, nm))
    for d in devs:
        if d.kind in ('fanc', 'fan'):
            if not switched(d.tag):
                v.append('%s: fan %r has no switch' % (lv.name, d.tag))
            if any(l.kind in LUM and l.tag == d.tag for l in devs):
                v.append('%s: fan %r shares its switch with a light' % (lv.name, d.tag))
    # 210.8: receptacles in the wet rooms, within 6' of a sink, and outdoors are protected
    def in_kitchen(d):
        x, y = stand_off(d.x, d.y, d.mount)
        return any(r[0] < x < r[0]+r[2] and r[1] < y < r[1]+r[3] for r in lv.kitchens)
    def wet_room(nm):
        up = nm.upper()
        return up == 'KITCHEN' or up.startswith(WET[1:])
    for d in devs:
        if d.kind not in PROTECT: continue
        room = _room_of(d, lv) or ''
        # the 6' is measured in the room the sink is in, not through its wall
        near = any(_near_rect((d.x, d.y), r, 6.0) and _room_at((r[0]+r[2]/2.0, r[1]+r[3]/2.0), lv) == room
                   for r in list(lv.sinks)+list(lv.lavs))
        wet = wet_room(room) or in_kitchen(d)
        if (wet or near or d.kind == 'wp') and not protected(d):
            v.append('%s: 210.8 %s at (%s, %s) in %s%s is not GFCI protected'
                     % (lv.name, d.kind, _f(d.x), _f(d.y), room or 'the open', ", within 6'-0\" of a sink" if near and not wet else ''))
    # 210.11(C): what the small-appliance, laundry and bathroom circuits may carry
    for d in devs:
        c = cks.get(d.circuit)
        if c is None: continue
        room = (_room_of(d, lv) or '').upper()
        if c.kind == 'sa' and not (d.kind in ('dup', 'gfci') and ('KITCHEN' in room or 'DINING' in room or in_kitchen(d))):
            v.append('%s: 210.11(C)(1) %s in %s on small-appliance circuit %s' % (lv.name, d.kind, room or 'the open', c.n))
        if c.kind == 'laundry' and d.kind not in ('dup', 'gfci'):
            v.append('%s: 210.11(C)(2) %s on laundry circuit %s' % (lv.name, d.kind, c.n))
        if c.kind == 'bath' and 'BATH' not in room:
            v.append('%s: 210.11(C)(3) %s in %s on bathroom circuit %s' % (lv.name, d.kind, room or 'the open', c.n))
        if c.kind in INDIVIDUAL and d.kind not in INDIVIDUAL[c.kind]:
            v.append('%s: %s on individual circuit %s (%s)' % (lv.name, d.kind, c.n, c.desc))
    for d in devs:
        if d.kind != 'panel' and d.circuit not in cks:
            v.append('%s: %s at (%s, %s) is on circuit %s, which does not exist' % (lv.name, d.kind, _f(d.x), _f(d.y), d.circuit))
    return v


def check_unit(ut):
    """Every rule the spec names, on one unit type. Returns the violations, empty when clean."""
    cks = {c.n: c for c in ut.circuits}
    allsw = [d for lv in ut.levels for d in lv.devices if d.kind in ('sw', 'sw3')]
    v = []
    for lv in ut.levels:
        v += check_level(lv, cks, allsw)
    groups = [[lv] for lv in ut.levels] if ut.stacked else [ut.levels]
    groups = [g for g in groups if any(lv.rooms or lv.polys for lv in g)]   # a house list has no bath
    for lvs in groups:
        fancs = sum(1 for lv in lvs for d in lv.devices if d.kind == 'fanc')
        if fancs != 1:
            v.append('%s: %d continuous-duty fans; exactly one per unit' % (lvs[0].name, fancs))
    used = {d.circuit for lv in ut.levels for d in lv.devices}
    for c in ut.circuits:
        if c.kind != 'spare' and c.n not in used:
            v.append('%s: circuit %s (%s) has no device' % (ut.name, c.n, c.desc))
        if c.kind == 'hp':
            v.extend(hp_violations(c))
        elif not wire_ok(c.wire, c.amps):
            v.append('%s: circuit %s at %s A on %s' % (ut.name, c.n, c.amps, c.wire))
    return v

"""Radon-resistant construction: a passive sub-slab depressurization system in both
buildings, as S-101 locates it and S-103 specifies and roofs it (the designer, 2026-09-18: "add it
for oak too").

Franklin County is EPA radon Zone 1. The Residential Code of Ohio does not adopt IRC
Appendix F, so nothing here is required; it is built to Appendix F's passive system
because the rough-in costs little at the pour and a great deal after it. A fan is not
installed: the riser is sized, routed and wired so one can be.

The slab already carries most of it — 4" of clean aggregate, a 10-mil retarder, sealed
penetrations (S-101 note 2, P-101). What this module adds is where the gravel is cut:
a bearing strip is deeper than the slab and its gravel, so every strip that runs wall to
wall divides the gravel below the slab into separate AREAS, and Appendix F wants each one
on a vent pipe. They are derived from src/foundation.py's strips, not typed: move a strip
and an area appears or goes. Building 1's stair-wall strip stops short of the rear and
divides nothing; Building 2's bearing strip makes two.

One RISER per building, in a partition that stands on both levels so it climbs straight:
Building 1's in the hall / mechanical room partition and on up the bedrooms' partition
over it, Building 2's in the bath's rear partition beside stack D, the wall the plumber is
already opening. Building 2's front area is joined to its riser by a LATERAL: solid pipe
in the gravel from the riser's tee through a sleeve cast in the strip, ending open in the
far area. The lateral lies in the 4" of aggregate directly under the slab and the drains
are COVER below it (src/drainage.py), so it passes over them; what it must clear in plan
is what comes UP through the slab, and the water.

Coordinates: page feet per building (x from the north face, y from the front face), the
frame src/drainage.py places the stacks in. Heights in feet above grade.
"""
import math
from collections import namedtuple
from lib.units import IN, fmt, inches
from src import levels
from src import drainage as dr
from lib.model import drains as drains
from codes.ohio import opc_drainage as opc_drainage
from lib.model import runs as runs
from src import foundation as F
from src.openings import WIN_HEAD
from src.sitework import SITE_BLDG, SITE_W
from codes.irc_appendix_f import PIPE_OD, TOL, _attic_of, _clear, _in, _rect_edges, _segs_cross, _strip
from codes.ohio import opc_drainage as opc_drainage_shared
from functools import partial
from codes.irc_appendix_f import areas as _shared_areas

# ---------------- basis ----------------
ZONE = 1                          # EPA Map of Radon Zones, Franklin County, Ohio
BASIS = 'IRC APPENDIX F'          # not adopted by Ohio; voluntary
PIPE = '3'                        # nominal, Schedule 40 PVC or ABS
RISER_OFF = IN(8)                 # center to center beside a stack, along their wall
STRIP_CLR = 1.0                   # a tee or a lateral's open end from the edge of its area
PIPE_CLR = IN(2)                  # clear, edge to edge, from a drain, a water line or a penetration
HATCH_CLR = IN(2)                 # clear of an attic hatch's rough opening, riser and roof exit
SLEEVE = IN(4)                    # the sleeve cast in a strip for a 3" lateral
LATERAL_PAST = 2.0                # a lateral runs this far into its area past the strip
ROOF_ABOVE = 1.0                  # the termination above the roof surface
OPENING_BELOW = 2.0               # an opening less than this below the exhaust point ...
OPENING_R = 10.0                  # ... is at least this far from it; so is any other building
ATTIC_OFFSET_MAX = 4.0            # horizontal offset in the attic, riser to roof exit
FAN_HEAD = 3.0                    # the roof deck above the top plate at the riser: CCAH 701.1's 36" fan space
FAN_SPACE_D = IN(21)              # and its diameter
JBOX_REACH = 6.0                  # the attic junction box from the riser
RETARDER_MIL_MIN = 6              # polyethylene soil-gas retarder, Appendix F

Lateral = namedtuple('Lateral', 'path strip')              # path from the riser's tee; strip crossed, by name
# pos: the tee and the Level 1 riser; up: where it climbs Level 2 (the same point unless the
# walls step); where: the wall it stands in, as the sheets say it
Riser   = namedtuple('Riser', 'mark building serves where pos up exit laterals attic')


def _od(size):
    """A drain or water line's outside diameter in feet, from its nominal size."""
    n = drains._nominal(size)
    return IN({1.5: 1.9, 2.0: 2.375, 3.0: 3.5, 4.0: 4.5}.get(n, n+0.375))


# ---------------- the areas ----------------


areas = partial(_shared_areas, f=F)


def _inside(p, a, clr=0.0):
    return a.x0+clr-TOL <= p[0] <= a.x1-clr+TOL and a.y0+clr-TOL <= p[1] <= a.y1-clr+TOL


# ---------------- the risers ----------------


_B1, _B2 = dr.BUILDINGS
_FB1, _FB2 = F.B1, F.B2
EXIT_OFF_RIDGE = 1.5              # a roof exit this far off the ridge, clear of the ridge vent's run


def _partition_x(rooms, plan, W, left, right):
    """The center of the partition between two named rooms that stand side by side, page x."""
    from lib.model import water as water
    r = {q[4]: water._mirror(plan.rect(q), W) for q in rooms if q[4] in (left, right)}
    return (r[left][0]+r[left][2]+r[right][0])/2.0


def _risers():
    from src import building1 as B1M
    P1 = B1M.LEVEL[1]['plan']
    # Building 1: the hall / mechanical room partition, past the room's door and ahead of the
    # rear collector. Over it the bedrooms' partition stands a few inches south; the riser
    # steps to it in the floor framing. Its exit is off the ridge, toward the south eave.
    x1 = _partition_x(B1M.L1_ROOMS, P1, _B1.W, 'HALL', 'MECH / LAUNDRY')
    door = max(P1.y(d[1])+d[2] for d in B1M.L1_DOORS if d[3] == 'v' and abs((_B1.W-P1.x(d[0], d[1]))-x1) < 0.5)
    u1 = (x1, door+IN(8))
    up1 = (_B1.W/2.0, u1[1])                        # the bedrooms' partition is on the building's centerline
    ex1 = (_B1.W/2.0+EXIT_OFF_RIDGE, u1[1])
    # Building 2: RISER_OFF beside stack D in the bath's rear partition, toward the tub. The
    # lateral runs forward along the riser's line, through the bearing strip, into the front area.
    d = drains.stack_by_name(_B2, 'D').pos
    u2 = (d[0]+RISER_OFF, d[1])
    bw = _strip(_FB2, 'UNITS 2 AND 3 BEARING WALL')
    ex2 = (u2[0]-(ATTIC_OFFSET_MAX-1.5), u2[1])     # toward the ridge, for the fan's headroom under the deck
    return [
        Riser('RR-1', 'BUILDING 1', 'UNIT 1', 'HALL / MECH. ROOM PARTITION', u1, up1, ex1, [], 'BUILDING 1 ATTIC'),
        Riser('RR-2', 'BUILDING 2', 'UNITS 2 AND 3', 'BATH PARTITION, BESIDE STACK D', u2, u2, ex2,
              [Lateral([u2, (u2[0], bw[1]-LATERAL_PAST)], bw[4])], 'BUILDING 2 ATTIC'),
    ]


RISERS = _risers()


def _bldg(name):
    return {'BUILDING 1': (_B1, _FB1), 'BUILDING 2': (_B2, _FB2)}[name]


def roof_z(roof, x):
    """The top of the roof over page x inside the walls: the eave at the wall line, up the pitch."""
    return levels.EAVE + levels.ROOF_PITCH*min(x, roof.W-x)


def _roof(name):
    from src.roof import B1_ROOF, B2_ROOF
    return B1_ROOF if name == 'BUILDING 1' else B2_ROOF


def termination(r):
    """The exhaust point's height above grade."""
    return roof_z(_roof(r.building), r.exit[0]) + ROOF_ABOVE


def roof_exits(roof_name):
    """(x, y, name) for src/roof.penetrations: each riser's roof exit on that roof."""
    return [(r.exit[0], r.exit[1], '%s RADON VENT' % r.mark) for r in RISERS if r.building == roof_name]


def _below_slab(b):
    """Everything already in the gravel or under it: (name, polyline, outside diameter)."""
    out = []
    for p in b.pens:
        if p.kind != 'exit': out.append(('PENETRATION %d' % p.mark, [p.pos], _od(p.size)))
    for run in b.runs:
        # a drain whose top is below the aggregate by PIPE_CLR is under the radon pipes, not beside them
        top = max(opc_drainage_shared.invert_at(b, run, q, cover=dr.COVER)+IN(opc_drainage.SIZE_IN[run.size]) for q in run.path)
        if -top < F.SLAB_T+F.GRAVEL_T+PIPE_CLR-TOL:
            out.append(('%s" DRAIN' % run.size, run.path, _od(run.size)))
    for a, c in dr.water_below(b):
        out.append(('WATER', [a, c], IN(1.5)))
    return out


def _points(path, step=0.05):
    return runs.points(path, step)


def radon_violations(risers=None):
    risers = RISERS if risers is None else risers
    from src.roof import ROOFS, penetrations
    from codes.ohio.rco.attic_ventilation import VENT_CLR
    v = []
    for bname in ('BUILDING 1', 'BUILDING 2'):
        b, fb = _bldg(bname)
        mine = [r for r in risers if r.building == bname]
        # 1. every area on exactly one riser, through its tee or a lateral's open end
        for a in areas(fb):
            n = sum(1 for r in mine if _inside(r.pos, a, STRIP_CLR)) + \
                sum(1 for r in mine for l in r.laterals if _inside(l.path[-1], a, STRIP_CLR))
            if n != 1:
                v.append('%s area x %s..%s y %s..%s: on %d vent pipes, not one'
                         % (bname, fmt(a.x0), fmt(a.x1), fmt(a.y0), fmt(a.y1), n))
        below = _below_slab(b)
        for r in mine:
            if not any(_inside(r.pos, a, STRIP_CLR) for a in areas(fb)):
                v.append('%s: its tee is not %s inside a gravel area' % (r.mark, fmt(STRIP_CLR)))
            for lvl, pt in ((1, r.pos), (2, r.up)):
                room = _room_at(bname, lvl, pt)
                if room is not None:
                    v.append('%s: on Level %d it stands in %s, not in a wall' % (r.mark, lvl, room or 'a room'))
            if math.hypot(r.up[0]-r.pos[0], r.up[1]-r.pos[1]) > STEP_MAX+TOL:
                v.append('%s: steps %s between the levels, over %s' % (r.mark, inches(math.hypot(r.up[0]-r.pos[0], r.up[1]-r.pos[1])), inches(STEP_MAX)))
            # 2. the tee and every lateral clear of what is below the slab
            for w in below:
                if _clear(r.pos, w) < PIPE_CLR-TOL:
                    v.append('%s: its tee is %.1f" from %s' % (r.mark, max(_clear(r.pos, w), 0)*12, w[0]))
            for l in r.laterals:
                strip = [s for s in fb.strips if s[4] == l.strip]
                if not strip or not any(_segs_cross(a, c, *e) for a, c in zip(l.path, l.path[1:])
                                        for e in _rect_edges(strip[0])):
                    v.append('%s: its lateral does not cross the %s strip' % (r.mark, l.strip))
                for s in fb.strips:
                    if s[4] != l.strip and any(_segs_cross(a, c, *e) for a, c in zip(l.path, l.path[1:]) for e in _rect_edges(s)):
                        v.append('%s: its lateral crosses the %s strip too' % (r.mark, s[4]))
                for w in below:
                    if len(w[1]) > 1 and any(_segs_cross(a, c, p, q) for a, c in zip(l.path, l.path[1:])
                                             for p, q in zip(w[1], w[1][1:])):
                        v.append('%s: its lateral crosses the %s' % (r.mark, w[0])); continue
                    worst = min(_clear(p, w) for p in _points(l.path))
                    if worst < PIPE_CLR-TOL:
                        v.append('%s: its lateral is %.1f" from %s' % (r.mark, max(worst, 0)*12, w[0]))
        # 3. the roof: out of the W4 band, near the riser, above the roof and clear of openings
        roof = [x for x in ROOFS if x.name == bname][0]
        pens = penetrations(roof)
        for r in mine:
            x, y = r.exit
            if not (0 < x < roof.W and 0 < y < roof.D):
                v.append('%s: its roof exit is off the roof' % r.mark)
            if abs(x-roof.ridge_x) < EXIT_OFF_RIDGE-TOL:
                v.append('%s: its roof exit is %s off the ridge, in the ridge vent' % (r.mark, fmt(abs(x-roof.ridge_x))))
            if math.hypot(x-r.up[0], y-r.up[1]) > ATTIC_OFFSET_MAX+TOL:
                v.append('%s: offset %s in the attic, over %s' % (r.mark, fmt(math.hypot(x-r.up[0], y-r.up[1])), fmt(ATTIC_OFFSET_MAX)))
            for px, py, nm in pens:
                if nm.startswith(r.mark): continue
                if math.hypot(px-x, py-y) < VENT_CLR-TOL:
                    v.append('%s: its roof exit is within %s of %s' % (r.mark, fmt(VENT_CLR), nm))
            # every window or door head in the set is WIN_HEAD above its floor; the highest
            # floor is Level 2
            head = levels.FF2 + max(WIN_HEAD.values())
            if head > termination(r) - OPENING_BELOW + TOL:
                v.append('%s: an opening head at +%s is less than %s below the exhaust point'
                         % (r.mark, fmt(head), fmt(OPENING_BELOW)))
            if termination(r) - levels.GRADE < ABOVE_GRADE_MIN-TOL:
                v.append('%s: discharge +%s, under %s above grade' % (r.mark, fmt(termination(r)), fmt(ABOVE_GRADE_MIN)))
            if roof_z(roof, x) - levels.ROOF_PLATE < FAN_HEAD-TOL:
                v.append('%s: %s under the roof deck at the riser, under %s for a fan'
                         % (r.mark, fmt(roof_z(roof, x)-levels.ROOF_PLATE), fmt(FAN_HEAD)))
            sx, sy = _site(bname, (x, y))
            if min(sx, SITE_W-sx) < OPENING_R-TOL:
                v.append('%s: %s from an adjacent parcel, under %s' % (r.mark, fmt(min(sx, SITE_W-sx)), fmt(OPENING_R)))
            for ob in SITE_BLDG:
                if ob[4] == bname: continue
                bx0, by0, bw, bd = ob[:4]
                d = math.hypot(max(bx0-sx, 0.0, sx-(bx0+bw)), max(by0-sy, 0.0, sy-(by0+bd)))
                if d < OPENING_R-TOL:
                    v.append('%s: %s from %s, under %s' % (r.mark, fmt(d), ob[4], fmt(OPENING_R)))
            for h in roof.hatches:
                gap = min(runs.pt_rect_dist(q, (h.page[0], h.page[1], h.page[2]-h.page[0], h.page[3]-h.page[1]))
                          for q in _points([r.up, r.exit] if r.up != r.exit else [r.up, r.up]))
                if gap - PIPE_OD/2.0 < HATCH_CLR-TOL:
                    v.append('%s: %.1f" from the %s attic hatch' % (r.mark, max(gap-PIPE_OD/2.0, 0)*12, h.unit))
            if not any(h for h in roof.hatches if _attic_of(roof, (h.page[0]+h.page[2])/2.0, (h.page[1]+h.page[3])/2.0) == r.attic):
                v.append('%s: no attic access in %s for a future fan' % (r.mark, r.attic))
            if _attic_of(roof, x, y) != r.attic or _attic_of(roof, *r.up) != r.attic:
                v.append('%s: not in %s' % (r.mark, r.attic))
    # the attic junction box of R7, from the electrical model: one per riser, within reach of it
    from src import building1 as B1M, building2 as B2M, electrical as E
    for r, lv, P, W in zip(risers, (E.LEVEL_U1_L2, E.LEVEL_U3), (B1M.LEVEL[2]['plan'], B2M.PLAN_B2), (B1M.B1_W, B2M.B2_W)):
        boxes = [(W-P.x(d.x, d.y), P.y(d.y)) for d in lv.devices if d.kind == 'jbox']
        if len(boxes) != 1:
            v.append('%s: %d attic junction boxes on %s, not one' % (r.mark, len(boxes), lv.name))
        elif math.hypot(boxes[0][0]-r.up[0], boxes[0][1]-r.up[1]) > JBOX_REACH+TOL:
            v.append('%s: its attic junction box is %s from the riser, over %s' % (r.mark, fmt(math.hypot(boxes[0][0]-r.up[0], boxes[0][1]-r.up[1])), fmt(JBOX_REACH)))
    if F.RETARDER_MIL < RETARDER_MIL_MIN:
        v.append('the slab retarder is %d-mil, under Appendix F\'s %d' % (F.RETARDER_MIL, RETARDER_MIL_MIN))
    return v


STEP_MAX = IN(6)                  # the riser's step in the floor framing between two partitions


def _room_at(bname, level, pt):
    """The room a page point stands in on that level, from the electrical model's rooms and
       polygons, or None when it is in a wall."""
    from src import building1 as B1M, building2 as B2M, electrical as E
    from codes.nec import dwelling as nec_dwelling
    if bname == 'BUILDING 1':
        P, W, lv = B1M.LEVEL[level]['plan'], B1M.B1_W, (E.LEVEL_U1_L1, E.LEVEL_U1_L2)[level-1]
    else:
        P, W, lv = B2M.PLAN_B2, B2M.B2_W, (E.LEVEL_U2, E.LEVEL_U3)[level-1]
    y = P.inv_y(pt[1]); x = P.inv_x(W-pt[0], y)
    return nec_dwelling._room_at((x, y), lv)


def _site(bname, p):
    ob = [b for b in SITE_BLDG if b[4] == bname][0]
    return (ob[0]+p[0], ob[1]+p[1])


def check_radon():
    """Every gravel area on one riser, every riser and lateral clear of what is under the
       slab, and every roof exit off the ridge vent and clear of the openings."""
    print('RADON — EPA ZONE %d, %s PASSIVE SUB-SLAB DEPRESSURIZATION (VOLUNTARY), %s" RISERS:' % (ZONE, BASIS, PIPE))
    for r in RISERS:
        print('   %s  %-13s %s, %s, at x %s y %s; roof exit x %s y %s, top +%s; %d lateral%s'
              % (r.mark, r.serves, r.building, r.where, fmt(r.pos[0]), fmt(r.pos[1]), fmt(r.exit[0]), fmt(r.exit[1]),
                 fmt(termination(r)), len(r.laterals), '' if len(r.laterals) == 1 else 's'))
    v = radon_violations()
    assert not v, 'radon: %s' % v[:6]


# ---------------- what S-103 prints ----------------
# 2018 IRC Appendix F by what each section governs (AF103.5 is the crawl-space system and
# does not apply to a slab), and ANSI/AARST CCAH-2020 where Appendix F gives no figure.
AF = {'AGGREGATE': 'AF103.2', 'RETARDER': 'AF103.3', 'ENTRY': 'AF103.4.1 AND AF103.4.2',
      'VENT': 'AF103.6.1', 'MULTIPLE': 'AF103.6.2', 'DRAINAGE': 'AF103.7', 'ACCESS': 'AF103.8',
      'LABEL': 'AF103.9', 'POWER': 'AF103.12'}
CCAH = 'ANSI/AARST CCAH-2020'
CCAH_SEC = {'SLOPE': '501.5', 'FAN_SPACE': '701.1', 'OUTLET': '701.4', 'DISCHARGE': '601.2'}
AGGREGATE = 'CLEAN AGGREGATE, ALL PASSING A 2" SIEVE AND RETAINED ON A 1/4" SIEVE'
LABEL = 'RADON REDUCTION SYSTEM'
ABOVE_GRADE_MIN = 10.0           # CCAH 601.2, the discharge above grade
ACTION = 4.0                     # pCi/L, EPA's action level, for the post-occupancy test


def schedule_rows():
    """(mark, serves, beside, riser x / y, roof exit x / y, top) as S-103 tabulates them."""
    return [(r.mark, r.serves, r.where, '%s / %s' % (fmt(r.pos[0]), fmt(r.pos[1])),
             '%s / %s' % (fmt(r.exit[0]), fmt(r.exit[1])), '+%s' % fmt(termination(r))) for r in RISERS]


def notes_text(FB):
    """The RADON block's notes. FB: A-601's fireblocking note ids."""
    m0, m1 = RISERS[0].mark, RISERS[-1].mark
    lat = [r.mark for r in RISERS if r.laterals]
    f1 = [r.mark for r in RISERS if r.building == 'BUILDING 2']
    step = [r.mark for r in RISERS if math.hypot(r.up[0]-r.pos[0], r.up[1]-r.pos[1]) > TOL]
    assert lat and f1 and step, "S-103's radon notes name a lateral, a riser through F1 and a riser that steps"
    return [
        'R1. VOLUNTARY — THE RCO DOES NOT ADOPT %s. PASSIVE SUB-SLAB DEPRESSURIZATION BUILT TO %s AND, WHERE NOTED, %s; '
        'FRANKLIN COUNTY IS EPA RADON ZONE %d. NO FAN IS INSTALLED.'
        % (BASIS, BASIS, CCAH, ZONE),
        'R2. BELOW THE SLAB — %s OF %s, UNDER THE WHOLE OF EACH SLAB, %s; ON IT THE %d-MIL POLYETHYLENE RETARDER OVER THE '
        'WHOLE FLOOR, LAPPED 12", FITTED CLOSELY AT EVERY PIPE, EVERY TEAR OR PUNCTURE SEALED, %s. S-101 NOTE 2, A-601 S1.'
        % (inches(F.GRAVEL_T), AGGREGATE, AF['AGGREGATE'], F.RETARDER_MIL, AF['RETARDER']),
        'R3. SEALING — EVERY SLAB PENETRATION, EVERY CONTROL, ISOLATION AND CONSTRUCTION JOINT, AND THE JOINT BETWEEN THE SLAB '
        'AND THE FOUNDATION WALL AT THE EDGE INSULATION: POLYURETHANE CAULK OR AN EQUIVALENT ELASTOMERIC SEALANT, %s.' % AF['ENTRY'],
        'R4. RISERS %s AND %s — %s" SCHEDULE 40 PVC OR ABS, GAS-TIGHT. A %s" TEE EMBEDDED IN THE AGGREGATE BEFORE THE POUR, '
        'BOTH RUNS OPEN IN IT; UP IN THE PARTITION SCHEDULED AND THROUGH EVERY FLOOR TO THE ROOF, %s. %s STEPS NOT OVER %s IN '
        'THE LEVEL 2 FLOOR FRAMING TO THE BEDROOMS\' PARTITION OVER IT. NOT JOINED TO ANY PLUMBING VENT, DUCT OR FLUE. %s '
        'PASSES THE F1 CEILING: FIRESTOP PER A-601. EVERY PLATE PER A-601 %s.'
        % (m0, m1, PIPE, PIPE, AF['VENT'], ' AND '.join(step), inches(STEP_MAX), ' AND '.join(f1), FB['PENETRATIONS']),
        'R5. LATERAL — %s: %s" SOLID PIPE IN THE AGGREGATE FROM THE TEE, THROUGH A %s SLEEVE CAST IN THE BEARING STRIP ABOVE '
        'ITS BARS, TO AN OPEN END %s PAST THE STRIP, SO THAT BOTH AREAS THE STRIP DIVIDES ARE ON THE ONE RISER, %s. IT LIES IN '
        'THE AGGREGATE, OVER THE DRAINS OF P-101. THE RETARDER, LAPPED UNDER THE STRIP, FITTED AND TAPED AT THE SLEEVE. DRAWN '
        'ON S-101.' % (' AND '.join(lat), PIPE, inches(SLEEVE), fmt(LATERAL_PAST), AF['MULTIPLE']),
        'R6. ROOF — EACH RISER THROUGH THE ROOF AT THE EXIT SCHEDULED, NOT LESS THAN %s" ABOVE THE ROOF AND %s ABOVE GRADE, '
        'FLASHED; %s FROM ANY OPENING LESS THAN %s BELOW IT AND FROM ANY OTHER BUILDING, %s; %s OFF THE RIDGE, CLEAR OF THE '
        'RIDGE VENT, NOTE 6. OFFSET IN THE ATTIC AT NOT LESS THAN 1/8" PER FOOT BACK TO THE RISER, %s; %s %s AND %s. NO CAP '
        'THAT RESTRICTS THE OPENING.'
        % (int(ROOF_ABOVE*12), fmt(ABOVE_GRADE_MIN), fmt(OPENING_R), fmt(OPENING_BELOW), AF['VENT'], fmt(EXIT_OFF_RIDGE),
           AF['DRAINAGE'], CCAH, CCAH_SEC['SLOPE'], CCAH_SEC['DISCHARGE']),
        'R7. FOR A FAN — EACH RISER\'S ATTIC RUN REACHED FROM ITS ATTIC\'S HATCH, NOTE 7, %s, WITH A %s x %s CLEAR SPACE '
        'BESIDE IT, %s %s; A 120 V JUNCTION BOX IN THE ATTIC, %s, WITHIN %s OF THE RISER, %s %s, ON A LIGHTING CIRCUIT OF '
        'THE UNIT WHOSE HATCH IT IS, DRAWN ON E-101 AND E-102.' % (AF['ACCESS'], _in(FAN_SPACE_D), _in(FAN_HEAD), CCAH, CCAH_SEC['FAN_SPACE'], AF['POWER'], fmt(JBOX_REACH), CCAH,
                                        CCAH_SEC['OUTLET']),
        'R8. LABEL — "%s" ON EACH RISER ON EVERY FLOOR WHERE IT IS EXPOSED OR VISIBLE, AND IN THE ATTIC, %s.' % (LABEL, AF['LABEL']),
        'R9. TEST — A LONG-TERM RADON TEST IN THE LOWEST DWELLING UNIT ON EACH RISER AFTER OCCUPANCY; AT %g PCI/L OR MORE, '
        'A FAN IN THE ATTIC ON THAT RISER.' % ACTION,
    ]

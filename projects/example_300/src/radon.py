"""Radon-resistant construction: a passive sub-slab depressurization system in both
buildings, as S-101 locates it and S-103 specifies and roofs it.

Franklin County is EPA radon Zone 1. The Residential Code of Ohio does not adopt IRC
Appendix F, so nothing here is required; it is built to Appendix F's passive system
because the rough-in costs little at the pour and a great deal after it. A fan is not
installed: the riser is sized, routed and wired so one can be.

The slab already carries most of it — 4" of aggregate, a 10-mil retarder, sealed
penetrations (S-101 note 2, P-101). What this module adds is where the gravel is cut:
a 16" x 12" bearing strip is deeper than the slab and its gravel, so every strip that
runs wall to wall divides the gravel below the slab into separate AREAS, and Appendix F
wants each one on a vent pipe. They are derived from src/foundation.py's strips, not
typed: move a strip and an area appears or goes.

One RISER per dwelling side of W4 — Unit 1; Units 2 / 3; Units 4 / 5 — each 8" beside the
3" stack already rising in its wet wall, so the riser climbs the chase the plumber is
building anyway and pierces F1 beside it, firestopped like it (A-001 note 4a). An area a
riser does not stand in is joined to it by a LATERAL: solid pipe in the gravel from the
riser's tee through a sleeve cast in the strip, ending open in the far area. No lateral
crosses W4's strip; each side of the separation keeps its own system.

Coordinates: page feet per building, S-101's (x from the Sage face, y from the front
face), the frame src/drainage.py places the stacks in. Heights in feet above grade.
"""
from arkitect.codes.ohio.columbus import criteria as JUR_CRIT
import math
from collections import namedtuple
from arkitect.lib.units import IN, fmt, inches
from src import levels
from src import drainage as dr
from arkitect.lib.model import drains as drains
from arkitect.lib.model import runs as runs
from src import foundation as F
from src.openings import WIN_HEAD
from src.sitework import SITE_BLDG, SITE_W
from arkitect.codes.irc_appendix_f import PIPE_OD, TOL, _attic_of, _clear, _in, _rect_edges, _segs_cross, _strip
from arkitect.codes.irc_appendix_f import areas

# ---------------- basis ----------------
ZONE = JUR_CRIT.RADON_ZONE        # EPA Map of Radon Zones: the jurisdiction's
BASIS = 'IRC APPENDIX F'          # not adopted by Ohio; voluntary
PIPE = '3'                        # nominal, Schedule 40 PVC or ABS
RISER_OFF = IN(8)                 # centre to centre beside its stack, along the wall
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
Riser   = namedtuple('Riser', 'mark building serves stack pos exit laterals attic')


def _od(size):
    """A drain or water line's outside diameter in feet, from its nominal size."""
    n = drains._nominal(size)
    return IN({1.5: 1.9, 2.0: 2.375, 3.0: 3.5, 4.0: 4.5}.get(n, n+0.375))


# ---------------- the areas ----------------




def _inside(p, a, clr=0.0):
    return a.x0+clr-TOL <= p[0] <= a.x1-clr+TOL and a.y0+clr-TOL <= p[1] <= a.y1-clr+TOL


# ---------------- the risers ----------------
def _stack(b, name):
    return drains.stack_by_name(b, name)


def _beside(b, name, sign):
    """A point RISER_OFF along the stack's wall — every stack used runs in a wall along y."""
    x, y = _stack(b, name).pos
    return (x, y+sign*RISER_OFF)


_B1, _B2 = dr.BUILDINGS
_FB1, _FB2 = F.B1, F.B2
# Unit 1: toward the water closet, away from W4; the roof exit steps out of the FRT band.
_u1 = _beside(_B1, 'B', -1)
# Units 2 / 3: away from W4; the Units 2 / 3 bearing strip divides their gravel, so a
# lateral runs along the riser's line to the far side of it.
_u23 = _beside(_B1, 'C', +1)
_bw = _strip(_FB1, 'UNITS 2 AND 3 BEARING WALL')
# Units 4 / 5: toward the tub, the rear side of Building 2's strip; the lateral steps east
# of the tub's collector before it turns for the strip, so it crosses no drain.
_u45 = _beside(_B2, 'D', -1)
_b2s = _strip(_FB2, 'UNITS 4 AND 5 BEARING WALL')
_L45_X = 17.0


def _exit_clear_of_band(p, band, clr):
    """The roof exit straight over the riser, or stepped along y just clear of the band."""
    if band is None: return p
    lo, hi = band
    x, y = p
    if lo-clr < y < hi+clr:
        y = lo-clr if (y-(lo-clr)) < ((hi+clr)-y) else hi+clr
    return (x, y)


def _risers():
    from src.roof import B1_ROOF
    from arkitect.codes.ohio.rco.attic_ventilation import VENT_CLR
    band = B1_ROOF.w4_band
    return [
        Riser('RR-1', 'BUILDING 1', 'UNIT 1', 'B', _u1, _exit_clear_of_band(_u1, band, VENT_CLR), [],
              'UNIT 1 ATTIC, S ELM SIDE OF W4'),
        Riser('RR-2', 'BUILDING 1', 'UNITS 2 AND 3', 'C', _u23, _exit_clear_of_band(_u23, band, VENT_CLR),
              [Lateral([_u23, (_bw[2]+LATERAL_PAST, _u23[1])], _bw[4])],
              'UNITS 2 / 3 ATTIC, REAR SIDE OF W4'),
        Riser('RR-3', 'BUILDING 2', 'UNITS 4 AND 5', 'D', _u45, _u45,
              [Lateral([_u45, (_L45_X, _u45[1]), (_L45_X, _b2s[1]-LATERAL_PAST)], _b2s[4])],
              'BUILDING 2 ATTIC'),
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
        out.append(('PENETRATION %d' % p.mark, [p.pos], _od(p.size)))
    for run in b.runs:
        out.append(('%s" DRAIN' % run.size, run.path, _od(run.size)))
    for a, c in dr.water_below(b):
        out.append(('WATER', [a, c], IN(1.5)))
    return out


def _points(path, step=0.05):
    return runs.points(path, step)


def radon_violations(risers=None):
    risers = RISERS if risers is None else risers
    from src.roof import ROOFS, penetrations
    from arkitect.codes.ohio.rco.attic_ventilation import VENT_CLR
    v = []
    for bname in ('BUILDING 1', 'BUILDING 2'):
        b, fb = _bldg(bname)
        mine = [r for r in risers if r.building == bname]
        # 1. every area on exactly one riser, through its tee or a lateral's open end
        for a in areas(fb, f=F):
            n = sum(1 for r in mine if _inside(r.pos, a, STRIP_CLR)) + \
                sum(1 for r in mine for l in r.laterals if _inside(l.path[-1], a, STRIP_CLR))
            if n != 1:
                v.append('%s area x %s..%s y %s..%s: on %d vent pipes, not one'
                         % (bname, fmt(a.x0), fmt(a.x1), fmt(a.y0), fmt(a.y1), n))
        below = _below_slab(b)
        for r in mine:
            if not any(_inside(r.pos, a, STRIP_CLR) for a in areas(fb, f=F)):
                v.append('%s: its tee is not %s inside a gravel area' % (r.mark, fmt(STRIP_CLR)))
            st = _stack(b, r.stack)
            if abs(math.hypot(r.pos[0]-st.pos[0], r.pos[1]-st.pos[1]) - RISER_OFF) > TOL or abs(r.pos[0]-st.pos[0]) > TOL:
                v.append('%s: not %s beside stack %s in its wall' % (r.mark, fmt(RISER_OFF), r.stack))
            # 2. the tee and every lateral clear of what is below the slab
            for w in below:
                if _clear(r.pos, w) < PIPE_CLR-TOL:
                    v.append('%s: its tee is %.1f" from %s' % (r.mark, max(_clear(r.pos, w), 0)*12, w[0]))
            for l in r.laterals:
                if l.strip == 'W4':
                    v.append('%s: a lateral crosses W4' % r.mark)
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
            if roof.w4_band and roof.w4_band[0]-VENT_CLR+TOL < y < roof.w4_band[1]+VENT_CLR-TOL:
                v.append('%s: its roof exit is within %s of the W4 band' % (r.mark, fmt(VENT_CLR)))
            if math.hypot(x-r.pos[0], y-r.pos[1]) > ATTIC_OFFSET_MAX+TOL:
                v.append('%s: offset %s in the attic, over %s' % (r.mark, fmt(math.hypot(x-r.pos[0], y-r.pos[1])), fmt(ATTIC_OFFSET_MAX)))
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
            if SITE_W - sx < OPENING_R-TOL:
                v.append('%s: %s from the adjacent parcel, under %s' % (r.mark, fmt(SITE_W-sx), fmt(OPENING_R)))
            for ob in SITE_BLDG:
                if ob[4] == bname: continue
                bx0, by0, bw, bd = ob[:4]
                d = math.hypot(max(bx0-sx, 0.0, sx-(bx0+bw)), max(by0-sy, 0.0, sy-(by0+bd)))
                if d < OPENING_R-TOL:
                    v.append('%s: %s from %s, under %s' % (r.mark, fmt(d), ob[4], fmt(OPENING_R)))
            for h in roof.hatches:
                gap = min(runs.pt_rect_dist(q, (h.page[0], h.page[1], h.page[2]-h.page[0], h.page[3]-h.page[1]))
                          for q in _points([r.pos, r.exit] if r.pos != r.exit else [r.pos, r.pos]))
                if gap - PIPE_OD/2.0 < HATCH_CLR-TOL:
                    v.append('%s: %.1f" from the %s attic hatch' % (r.mark, max(gap-PIPE_OD/2.0, 0)*12, h.unit))
            if not any(h for h in roof.hatches if _attic_of(roof, (h.page[0]+h.page[2])/2.0, (h.page[1]+h.page[3])/2.0) == r.attic):
                v.append('%s: no attic access in %s for a future fan' % (r.mark, r.attic))
            if _attic_of(roof, x, y) != r.attic or _attic_of(roof, *r.pos) != r.attic:
                v.append('%s: not in %s' % (r.mark, r.attic))
    if F.RETARDER_MIL < RETARDER_MIL_MIN:
        v.append('the slab retarder is %d-mil, under Appendix F\'s %d' % (F.RETARDER_MIL, RETARDER_MIL_MIN))
    return v


def _site(bname, p):
    ob = [b for b in SITE_BLDG if b[4] == bname][0]
    return (ob[0]+p[0], ob[1]+p[1])


def check_radon():
    """Every gravel area on one riser, every riser and lateral clear of what is under the
       slab, and every roof exit out of the W4 band and clear of the openings."""
    print('RADON — EPA ZONE %d, %s PASSIVE SUB-SLAB DEPRESSURIZATION (VOLUNTARY), %s" RISERS:' % (ZONE, BASIS, PIPE))
    for r in RISERS:
        print('   %s  %-13s %s beside stack %s at x %s y %s; roof exit x %s y %s, top +%s; %d lateral%s'
              % (r.mark, r.serves, r.building, r.stack, fmt(r.pos[0]), fmt(r.pos[1]), fmt(r.exit[0]), fmt(r.exit[1]),
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
    return [(r.mark, r.serves, 'STACK %s' % r.stack, '%s / %s' % (fmt(r.pos[0]), fmt(r.pos[1])),
             '%s / %s' % (fmt(r.exit[0]), fmt(r.exit[1])), '+%s' % fmt(termination(r))) for r in RISERS]


def notes_text(FB, band):
    """The RADON block's notes. FB: src/fireblocking.FB. band: the W4 FRT band width."""
    m0, m1 = RISERS[0].mark, RISERS[-1].mark
    lat = [r.mark for r in RISERS if r.laterals]
    f1 = [r.mark for r in RISERS if r.serves != 'UNIT 1']
    offset = [r.mark for r in RISERS if math.hypot(r.exit[0]-r.pos[0], r.exit[1]-r.pos[1]) > TOL]
    return [
        'R1. VOLUNTARY — THE RCO DOES NOT ADOPT %s. PASSIVE SUB-SLAB DEPRESSURIZATION BUILT TO %s AND, WHERE NOTED, %s; '
        'FRANKLIN COUNTY IS EPA RADON ZONE %d. NO FAN IS INSTALLED.'
        % (BASIS, BASIS, CCAH, ZONE),
        'R2. BELOW THE SLAB — %s OF %s, UNDER THE WHOLE OF EACH SLAB, %s; ON IT THE %d-MIL POLYETHYLENE RETARDER OVER THE '
        'WHOLE FLOOR, LAPPED 12", FITTED CLOSELY AT EVERY PIPE, EVERY TEAR OR PUNCTURE SEALED, %s. S-101 NOTE 2, A-601 S1.'
        % (inches(F.GRAVEL_T), AGGREGATE, AF['AGGREGATE'], F.RETARDER_MIL, AF['RETARDER']),
        'R3. SEALING — EVERY SLAB PENETRATION, EVERY CONTROL, ISOLATION AND CONSTRUCTION JOINT, AND THE JOINT BETWEEN THE SLAB '
        'AND THE FOUNDATION WALL AT THE EDGE INSULATION: POLYURETHANE CAULK OR AN EQUIVALENT ELASTOMERIC SEALANT, %s.' % AF['ENTRY'],
        'R4. RISERS %s TO %s — %s" SCHEDULE 40 PVC OR ABS, GAS-TIGHT. A %s" TEE EMBEDDED IN THE AGGREGATE BEFORE THE POUR, '
        'BOTH RUNS OPEN IN IT; UP IN THE WET WALL %s BESIDE THE STACK SCHEDULED AND THROUGH EVERY FLOOR TO THE ROOF, %s. '
        'NOT JOINED TO ANY PLUMBING VENT, DUCT OR FLUE. %s PASS THE F1 CEILING: FIRESTOP PER A-001 NOTE 4a. EVERY PLATE '
        'PER A-601 %s.' % (m0, m1, PIPE, PIPE, inches(RISER_OFF), AF['VENT'], ' AND '.join(f1), FB['PENETRATIONS']),
        'R5. LATERALS — %s: %s" SOLID PIPE IN THE AGGREGATE FROM THE TEE, THROUGH A %s SLEEVE CAST IN THE BEARING STRIP ABOVE '
        'ITS BARS, TO AN OPEN END %s PAST THE STRIP, SO THAT EVERY AREA A STRIP DIVIDES IS ON ONE RISER, %s. THE RETARDER, '
        'LAPPED UNDER THE STRIP, FITTED AND TAPED AT EACH SLEEVE. DRAWN ON S-101.' % (' AND '.join(lat), PIPE, inches(SLEEVE), fmt(LATERAL_PAST), AF['MULTIPLE']),
        'R6. ROOF — EACH RISER THROUGH THE ROOF AT THE EXIT SCHEDULED, NOT LESS THAN %s" ABOVE THE ROOF AND %s ABOVE GRADE, '
        'FLASHED; %s FROM ANY OPENING LESS THAN %s BELOW IT AND FROM ANY OTHER BUILDING, %s; OUTSIDE THE W4 BAND BY %s, '
        'NOTE 6. %s OFFSET IN THE ATTIC AT NOT LESS THAN 1/8" PER FOOT BACK TO THE RISER, %s; %s %s AND %s. NO CAP THAT '
        'RESTRICTS THE OPENING.'
        % (int(ROOF_ABOVE*12), fmt(ABOVE_GRADE_MIN), fmt(OPENING_R), fmt(OPENING_BELOW), AF['VENT'], inches(IN(12)),
           ' AND '.join(offset), AF['DRAINAGE'], CCAH, CCAH_SEC['SLOPE'], CCAH_SEC['DISCHARGE']),
        'R7. FOR A FAN — EACH RISER\'S ATTIC RUN REACHED FROM THAT ATTIC\'S HATCH, NOTE 8, %s, WITH A %s x %s CLEAR SPACE '
        'BESIDE IT, %s %s; A 120 V JUNCTION BOX IN THE ATTIC, %s, WITHIN %s OF THE RISER, %s %s, ON A LIGHTING CIRCUIT OF '
        'THE UNIT WHOSE HATCH IT IS.' % (AF['ACCESS'], _in(FAN_SPACE_D), _in(FAN_HEAD), CCAH, CCAH_SEC['FAN_SPACE'], AF['POWER'], fmt(JBOX_REACH), CCAH,
                                        CCAH_SEC['OUTLET']),
        'R8. LABEL — "%s" ON EACH RISER ON EVERY FLOOR WHERE IT IS EXPOSED OR VISIBLE, AND IN THE ATTIC, %s.' % (LABEL, AF['LABEL']),
        'R9. TEST — A LONG-TERM RADON TEST IN THE LOWEST DWELLING UNIT ON EACH RISER AFTER OCCUPANCY; AT %g PCI/L OR MORE, '
        'A FAN IN THE ATTIC ON THAT RISER.' % ACTION,
    ]

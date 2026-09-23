"""Does a program FIT a Columbus lot? The zoning check a new address runs before a line
is drawn, and the one both existing projects' zoning tables are held to.

It reads a MASSING: the lot, each building's footprint and where it stands, the dwellings
in each, the parking pad and any other structure on the ground. It answers with one Row
per rule -- what is required, what the massing provides, whether it meets it, and the
section. Nothing here draws or prints; a sheet or the new-address tools print the rows.

EVERY FIGURE HAS A SOURCE. A section beside a rule is one a permit set in this repository
already prints for it (the line is named beside each rule below). A figure whose section
nobody has established prints SECTION UNVERIFIED, from zoning.py, rather than a plausible
number. A rule that needs what a massing does not have yet -- a height before the roof is
modelled -- is NOT CHECKED, never assumed to pass.

RELIEF IS STATED, NOT GRANTED. A rule the massing does not meet can carry the words the
project uses for it -- "VARIANCE REQUESTED", or a lot split's "BY THE LOT SPLIT OF
<parcel number>" -- and is then RELIEF STATED. It still does not meet the rule; the row says
on what basis the project proceeds anyway, and a person decides whether that basis holds.

COORDINATES, in feet, as both projects' sitework.py take them: x across the lot from the
LEFT side lot line looking from the street, y from the front lot line toward the rear.
A corner lot names which side the side street is on.
"""
from arkitect.codes.columbus import zoning as Z
from arkitect.codes.ohio.rco import fire_separation as rco_fsd

# the shape every jurisdiction's fit answers in, and the lot it reads (arkitect/codes/massing.py)
from arkitect.codes.massing import MEETS, FAILS, RELIEF, NOT_CHECKED, Row
from arkitect.codes import massing as _massing

Massing = _massing.Massing      # where every caller has always found it

# ---------------- the figures, each with the line that sources it ----------------
LOT_WIDTH_MIN = 50.0            # C.C. 3332.05; a set's G-001 / C-102: "Lot width req'd 50'-0\""
UNITS_MAX = 5                   # C.C. 3332.355(B)(2); a set's C-102: "TWO ADUs, 5 UNITS MAX"
ADUS_MAX = 2                    # the same row
DENSITY_SF_PER_UNIT = 1500.0    # a set's C-102: "Lot area req'd, 3-unit 4,500 SF @ 1,500/UNIT"
ADU_REAR_ONE = 0.45             # C.C. 3332.355(C)(3): one detached ADU
ADU_REAR_TWO = 0.55             # two separate or adjoining detached ADUs
ADU_AREA_FLOOR = 1000.0         # C.C. 3332.355(B)(3)(a): "... or 1,000 square feet, whichever is greater"
HEIGHT_MAX = 35.0               # C.C. 3332.29, R-4 / H-35
ADU_HEIGHT_MAX = 25.0           # C.C. 3332.355(B)(3)(b)
PARK_PER_PRINCIPAL = 2          # C.C. 3312.49: 6 for 3 principal units,
                                # 2 for 1; "ADUs EXEMPT"
PARK_SETBACK = 8.0              # C.C. 3312.27; a set's C-102 "(8'-0\" MIN)", corner lots
ALLEY_VISION = 10.0             # C.C. 3321.05(B)(1); a project's sitework.VISION

CITE = {
    'lot_width': 'C.C. 3332.05',
    'units': 'C.C. 3332.355(B)(2)',
    'density': Z.SECTION_UNVERIFIED,     # a set prints 3332.18(C) for the density AREA, not the rate
    'front_yard': 'C.C. 3332.21',
    'side_street': 'C.C. 3332.22(a)(1)',
    'side_yard': Z.SECTION_UNVERIFIED,   # zoning.SIDE_YARD_UNVERIFIED: 3332.26, text not obtained
    'side_combined': Z.SECTION_UNVERIFIED,
    'fire_separation': rco_fsd.SECTION,
    'coverage': Z.citation('COVERAGE_MAX'),
    'rear_yard': Z.citation('REAR_YARD_MIN'),
    'adu_in_rear': 'C.C. 3332.355(C)(1)',
    'adu_share': 'C.C. 3332.355(C)(3)',
    'adu_area': 'C.C. 3332.355(B)(3)(a)',
    'height': 'C.C. 3332.29',
    'adu_height': 'C.C. 3332.355(B)(3)(b)',
    'parking': 'C.C. 3312.49',
    'stall_depth': Z.citation('STALL_D'),
    'maneuvering': Z.citation('MANEUVER_MIN'),
    'parking_setback': 'C.C. 3312.27',
    'alley_vision': 'C.C. 3321.05(B)(1)',
    'street_vision': Z.citation('VISION_TRIANGLE_ST'),
}


def _ft(v):
    """Feet and inches, to the nearest 1/8", as the sets print them."""
    from arkitect.lib.units import fmt
    return fmt(v)


def _sf(v):
    return '{:,.0f} SF'.format(v)


def _row(m, rule, label, required, provided, ok, note=''):
    status = NOT_CHECKED if ok is None else MEETS if ok else FAILS
    if ok is False and rule in m.relief:
        status = RELIEF
        note = (m.relief[rule]+('; '+note if note else ''))
    return Row(rule, label, required, provided, ok, status, CITE[rule], note)


def fit(massing):
    """[Row] for every rule, in the order a zoning table prints them."""
    m = massing
    lot = m.lot
    rows = []
    add = rows.append
    corner = bool(lot.get('corner'))
    street_side = lot.get('side_street') if corner else None       # 'left' or 'right'
    narrow = m.W <= 40.0+1e-9
    su = Z.SIDE_YARD_UNVERIFIED

    # --- the lot and the program
    add(_row(m, 'lot_width', 'Lot width', _ft(LOT_WIDTH_MIN), _ft(m.W), m.W >= LOT_WIDTH_MIN-1e-9))
    n_p, n_a = m.principal_dwellings(), m.adu_dwellings()
    add(_row(m, 'units', 'Dwelling units', '%d MAX, %d ADUs MAX' % (UNITS_MAX, ADUS_MAX),
             '%d (%d PRINCIPAL, %d ADU)' % (n_p+n_a, n_p, n_a),
             n_p+n_a <= UNITS_MAX and n_a <= ADUS_MAX))
    need = DENSITY_SF_PER_UNIT*n_p
    add(_row(m, 'density', 'Lot area per principal unit', _sf(need), _sf(m.area), m.area >= need-1e-9,
             'lot area used; the density area of 3332.18(C) is not derived'))

    # --- yards
    front = lot.get('front_line')
    add(_row(m, 'front_yard', 'Front building line', _ft(front) if front is not None else '—',
             _ft(m.P['y']), None if front is None else m.P['y'] >= front-1e-9,
             '' if front is not None else 'the front building line for this street is not in the intake'))
    ssl = lot.get('side_street_line')
    if corner:
        things = m.buildings+m.structures
        least = min(things, key=lambda r: m.side_distance(r, street_side))
        have = m.side_distance(least, street_side)
        add(_row(m, 'side_street', 'Side street yard', _ft(ssl) if ssl is not None else '—',
                 '%s (%s)' % (_ft(have), least['name']),
                 None if ssl is None else have >= ssl-1e-9,
                 '' if ssl is not None else 'the side street building line is not in the intake'))
    side_min = su['NARROW_LOT_MIN'] if narrow else su['WIDE_LOT_MIN']
    interior = [sd for sd in ('left', 'right') if sd != street_side]
    for sd in interior:
        least = min(m.buildings, key=lambda b: m.side_distance(b, sd))
        have = m.side_distance(least, sd)
        add(_row(m, 'side_yard', 'Side yard, %s' % sd, _ft(side_min),
                 '%s (%s)' % (_ft(have), least['name']), have >= side_min-1e-9,
                 'framing dimension; a yard is measured to %s' % Z.YARD_MEASURED_TO))
    comb_need = min(su['COMBINED_PCT']*m.W, su['COMBINED_CAP_NARROW']) if narrow else su['COMBINED_PCT']*m.W
    comb = sum(min(m.side_distance(b, sd) for b in m.buildings) for sd in ('left', 'right'))
    add(_row(m, 'side_combined', 'Side yards combined', _ft(comb_need), _ft(comb), comb >= comb_need-1e-9))
    near = min(min(m.side_distance(b, sd) for b in m.buildings) for sd in interior)
    add(_row(m, 'fire_separation', 'Wall to an interior lot line', _ft(rco_fsd.RATED_MAX), _ft(near),
             near >= rco_fsd.RATED_MAX-1e-9,
             'building code, not zoning: under this the wall is rated and its openings limited'))

    # --- coverage and the rear yard
    cov = sum(b['width']*b['depth'] for b in m.buildings)+sum(t['width']*t['depth'] for t in m.structures)
    add(_row(m, 'coverage', 'Lot coverage', '%.0f%%' % (100*Z.COVERAGE_MAX),
             '%s = %.1f%%' % (_sf(cov), 100*cov/m.area), cov <= Z.COVERAGE_MAX*m.area+1e-9))
    rear_need, rear = Z.REAR_YARD_MIN*m.area, m.rear_yard()
    add(_row(m, 'rear_yard', 'Rear yard', '%s (%.0f%% OF LOT)' % (_sf(rear_need), 100*Z.REAR_YARD_MIN),
             _sf(rear), rear >= rear_need-1e-9))
    if m.adus:
        behind = all(b['y'] >= m.rear_line()-1e-9 for b in m.adus)
        add(_row(m, 'adu_in_rear', 'ADU in the rear yard', 'BEHIND THE PRINCIPAL BUILDING',
                 'YES' if behind else 'NO', behind))
        share_max = ADU_REAR_ONE if n_a == 1 else ADU_REAR_TWO
        adu_fp = sum(b['width']*b['depth'] for b in m.adus)
        share = adu_fp/rear if rear > 0 else float('inf')
        add(_row(m, 'adu_share', 'ADU share of the rear yard', '%.0f%% MAX' % (100*share_max),
                 '%s = %.1f%%' % (_sf(adu_fp), 100*share), share <= share_max+1e-9))
        p_area, p_est = 0.0, False
        for d in m.P['dwellings']:
            a, e = m.dwelling_area(m.P, d)
            p_area += a
            p_est = p_est or e
        cap = max(Z.ADU_PCT_MAX*p_area, ADU_AREA_FLOOR)
        worst, w_est = max(((m.dwelling_area(b, d)) for b in m.adus for d in b['dwellings']),
                           key=lambda t: t[0])
        add(_row(m, 'adu_area', 'ADU area, largest', '%s MAX, NOT OVER %s' % (_sf(min(cap, p_area)), _sf(p_area)),
                 _sf(worst), worst <= min(cap, p_area)+1e-9,
                 'ESTIMATE from gross floor area' if (p_est or w_est) else ''))

    # --- height
    ph = m.P.get('height')
    add(_row(m, 'height', 'Building height', _ft(HEIGHT_MAX), _ft(ph) if ph else '—',
             None if ph is None else ph < HEIGHT_MAX,
             '' if ph else 'derived once the roof is modelled'))
    if m.adus:
        hs = [b.get('height') for b in m.adus]
        known = None not in hs and ph is not None
        add(_row(m, 'adu_height', 'ADU height', '%s, NOT OVER THE PRINCIPAL' % _ft(ADU_HEIGHT_MAX),
                 _ft(max(hs)) if known else '—',
                 None if not known else max(hs) <= min(ADU_HEIGHT_MAX, ph)+1e-9,
                 '' if known else 'derived once the roofs are modelled'))

    # --- parking
    pk = m.parking
    need = PARK_PER_PRINCIPAL*n_p
    stalls = pk['stalls'] if pk else 0
    add(_row(m, 'parking', 'Parking', '%d (ADUs EXEMPT)' % need, '%d' % stalls, stalls >= need))
    if pk:
        depth = pk.get('depth', Z.STALL_D)
        behind = max(b['y']+b['depth'] for b in m.buildings)
        room = m.D-behind
        add(_row(m, 'stall_depth', 'Stall depth', _ft(Z.STALL_D),
                 '%s (%s BEHIND THE BUILDINGS)' % (_ft(depth), _ft(room)),
                 depth >= Z.STALL_D-1e-9 and room >= depth-1e-9))
        if lot.get('alley'):
            have = lot.get('alley_width', 0.0)+(depth-Z.STALL_D)
            add(_row(m, 'maneuvering', 'Maneuvering', _ft(Z.MANEUVER_MIN), _ft(have),
                     have >= Z.MANEUVER_MIN-1e-9, 'the alley right-of-way plus any pad past the stall'))
        if corner:
            off = pk['x0'] if street_side == 'left' else m.W-pk['x0']-pk['width']
            add(_row(m, 'parking_setback', 'Parking setback', _ft(PARK_SETBACK), _ft(off),
                     off >= PARK_SETBACK-1e-9))
            if lot.get('alley'):
                add(_row(m, 'alley_vision', 'Alley clear vision triangle', '%s x %s' % (_ft(ALLEY_VISION), _ft(ALLEY_VISION)),
                         '%s CLEAR' % _ft(min(off, ALLEY_VISION)), off >= ALLEY_VISION-1e-9))
    if corner:
        leg = Z.VISION_TRIANGLE_ST
        # a rectangle clears the triangle when its nearest corner is on or past the
        # hypotenuse: distance from the side street plus distance from the front >= leg
        worst = min(m.buildings+m.structures, key=lambda r: m.side_distance(r, street_side)+r['y'])
        s = m.side_distance(worst, street_side)+worst['y']
        add(_row(m, 'street_vision', 'Street corner clear vision triangle', '%s x %s' % (_ft(leg), _ft(leg)),
                 '%s (%s)' % (_ft(s), worst['name']), s >= leg-1e-9,
                 '' if s >= leg-1e-9 else '%s inside the hypotenuse' % _ft(leg-s)))
    return rows


failing = _massing.failing      # the rules not met with no relief stated
summary = _massing.summary      # one rule per line, for a person or an agent


def check(massing):
    """A build's zoning check: print every row, and stop on a rule not met that states no
       relief. The relief a project proceeds on is its intake's `relief`, which is the owner's
       call -- never a way to make this pass."""
    rows = fit(massing)
    print('ZONING FIT:')
    for line in summary(rows).split('\n'):
        print('   ' + line)
    bad = failing(rows)
    assert not bad, ('the massing does not meet %s and states no relief: redesign it, or record '
                     'the basis the designer chooses in intake.json "relief"' % ', '.join(r.rule for r in bad))
    return rows

"""What a drawing cannot be started without, as a schema the agent fills and this checks.

    python3 -m arkitect.harness.intake projects/<slug>/intake.json          # validate, then the fit
    python3 -m arkitect.harness.intake projects/<slug>/intake.json --json   # the same, for a tool

Exit status: 0 the intake is valid and every zoning rule it does not meet states its
relief; 1 the intake is invalid (every problem is listed); 2 valid, but the program does not
fit -- rules not met with no relief stated. A 2 is a conversation with the designer, not a bug:
redesign the massing, or record the relief the designer chooses in `relief`.

QUESTIONS is the one list of what to ask. The `new-address` skill asks from it, so a
question added here is asked of the next address without anyone editing the skill.

Coordinates are arkitect/codes/columbus/fit.py's: feet, x across the lot from the LEFT side lot line
looking from the street, y from the front lot line toward the rear.
"""
import json
import keyword
import re
import sys

JURISDICTIONS = ('columbus',)

# (path, question, why it is needed). `buildings[]` questions are asked once per building.
QUESTIONS = (
    ('address', 'Street address, as the title block prints it (e.g. "42 OAK ST")?', 'every sheet'),
    ('city_line', 'City, state and ZIP line (e.g. "COLUMBUS, OHIO 43205")?', 'the title block'),
    ('parcel', 'Franklin County parcel number, or TBD?', 'the title block and C-102'),
    ('street', 'Name of the street the lot fronts?', 'C-102 labels the right-of-way'),
    ('district', 'Zoning district (e.g. R-4)?', 'which rules apply'),
    ('lot.width', 'Lot width along the street, in feet?', 'lot width, side yards, coverage'),
    ('lot.depth', 'Lot depth, in feet?', 'rear yard, coverage, parking'),
    ('lot.survey', 'Is there a boundary survey, or are the dimensions from the Auditor\'s GIS?',
     'C-102 says which'),
    ('lot.corner', 'Corner lot? If so, which side is the side street on (left or right, facing the lot '
     'from the front street), and its name?', 'side street yard, vision triangles'),
    ('lot.alley', 'Is there an alley at the rear? If so, its right-of-way width?', 'parking, maneuvering'),
    ('lot.front_line', 'Front building line for this street, in feet (C.C. 3332.21; the line '
     'established for this street, which differs street to street -- ask, do not assume)?', 'the front yard'),
    ('buildings[]', 'How many buildings, and for each: principal or ADU, footprint width x depth, '
     'storeys, where it stands (x from the left lot line, y from the front), and its dwellings '
     'with bedrooms each?', 'every rule and every sheet'),
    ('parking', 'Parking stalls: how many, and where (x of the pad from the left lot line; depth)?',
     'parking count, stall depth, maneuvering'),
    ('owner', 'Owner block for the title block (name, street, city, phone)?', 'the title block'),
)

SLUG = re.compile(r'^[a-z][a-z0-9_]*$')


def slug_for(address):
    """'42 N OAK ST' -> 'oak_42', '7 ELM AVE' -> 'elm_7': the street's first
       word that is not a direction, then the number."""
    words = address.lower().replace('.', '').split()
    num = next((w for w in words if w.isdigit()), '')
    rest = [w for w in words if not w.isdigit() and w not in ('n', 's', 'e', 'w', 'north', 'south',
                                                               'east', 'west')]
    name = re.sub(r'[^a-z0-9]', '', rest[0]) if rest else 'site'
    return '%s_%s' % (name, num) if num else name


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _rect(r):
    return (r['x'], r['y'], r['x']+r['width'], r['y']+r['depth'])


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _rect(a)
    bx0, by0, bx1, by1 = _rect(b)
    return min(ax1, bx1)-max(ax0, bx0) > 1e-9 and min(ay1, by1)-max(ay0, by0) > 1e-9


def validate(d):
    """Every problem with an intake, as sentences. [] means it can be scaffolded."""
    bad = []
    for k in ('address', 'city_line', 'parcel', 'street', 'district'):
        if not isinstance(d.get(k), str) or not d[k].strip():
            bad.append('%s is missing' % k)
    slug = d.get('slug')
    if not slug or not SLUG.match(slug) or keyword.iskeyword(slug):
        bad.append('slug %r must be a lowercase Python identifier (test discovery imports it); '
                   'arkitect.harness.intake.slug_for(address) gives one' % slug)
    if d.get('jurisdiction') not in JURISDICTIONS:
        bad.append('jurisdiction %r is not encoded: %s only. A new city is a code-research '
                   'deliverable (arkitect/codes/columbus/__init__.py records what that means), not a flag'
                   % (d.get('jurisdiction'), ', '.join(JURISDICTIONS)))
    lot = d.get('lot')
    if not isinstance(lot, dict):
        return bad+['lot is missing']
    for k in ('width', 'depth'):
        if not _num(lot.get(k)) or lot[k] <= 0:
            bad.append('lot.%s must be a positive number of feet' % k)
    if bad:
        return bad
    if lot.get('corner'):
        if lot.get('side_street') not in ('left', 'right'):
            bad.append('a corner lot needs lot.side_street: "left" or "right"')
        if not d.get('side_street_name'):
            bad.append('a corner lot needs side_street_name, the side street\'s name')
    if lot.get('alley') and not _num(lot.get('alley_width')):
        bad.append('an alley needs lot.alley_width, its right-of-way in feet')
    if lot.get('front_line') is not None and not _num(lot['front_line']):
        bad.append('lot.front_line must be feet, or null if unknown')

    things = []
    bs = d.get('buildings') or []
    if not bs:
        bad.append('buildings is missing')
    roles = [b.get('role') for b in bs]
    if roles.count('principal') != 1:
        bad.append('exactly one building is the principal building (role "principal"); found %d'
                   % roles.count('principal'))
    for i, b in enumerate(bs):
        tag = b.get('name') or 'buildings[%d]' % i
        if b.get('role') not in ('principal', 'adu'):
            bad.append('%s: role must be "principal" or "adu"' % tag)
        for k in ('x', 'y', 'width', 'depth'):
            if not _num(b.get(k)):
                bad.append('%s: %s must be feet' % (tag, k))
        if not isinstance(b.get('storeys'), int) or not 1 <= b['storeys'] <= 3:
            bad.append('%s: storeys must be 1, 2 or 3' % tag)
        ds = b.get('dwellings') or []
        if not ds:
            bad.append('%s has no dwellings' % tag)
        for dw in ds:
            if not dw.get('name'):
                bad.append('%s: every dwelling needs a name' % tag)
            if not isinstance(dw.get('bedrooms'), int) or dw['bedrooms'] < 0:
                bad.append('%s: %s needs bedrooms, a whole number' % (tag, dw.get('name', '?')))
        things.append((tag, b))
    for i, t in enumerate(d.get('structures') or []):
        tag = t.get('name') or 'structures[%d]' % i
        for k in ('x', 'y', 'width', 'depth'):
            if not _num(t.get(k)):
                bad.append('%s: %s must be feet' % (tag, k))
        things.append((tag, t))
    pk = d.get('parking')
    if pk:
        for k in ('stalls', 'x0', 'width', 'depth'):
            if not _num(pk.get(k)):
                bad.append('parking.%s must be a number' % k)
        if not bad:
            things.append(('the parking pad', {'x': pk['x0'], 'y': lot['depth']-pk['depth'],
                                               'width': pk['width'], 'depth': pk['depth']}))
    if bad:
        return bad
    for tag, r in things:
        x0, y0, x1, y1 = _rect(r)
        if x0 < -1e-9 or y0 < -1e-9 or x1 > lot['width']+1e-9 or y1 > lot['depth']+1e-9:
            bad.append('%s leaves the lot' % tag)
    for i, (ta, a) in enumerate(things):
        for tb, b in things[i+1:]:
            if _overlap(a, b):
                bad.append('%s and %s overlap' % (ta, tb))
    for k in (d.get('relief') or {}):
        from arkitect.codes.columbus.fit import CITE
        if k not in CITE:
            bad.append('relief names %r, which is not a rule: one of %s' % (k, ', '.join(sorted(CITE))))
    return bad


def massing(d):
    """The intake as arkitect/codes/columbus/fit.py's Massing."""
    from arkitect.codes.columbus.fit import Massing
    return Massing.from_intake(d)


def load(path):
    with open(path) as fh:
        return json.load(fh)


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    d = load(argv[0])
    as_json = '--json' in argv
    bad = validate(d)
    if bad:
        if as_json:
            print(json.dumps({'valid': False, 'problems': bad}, indent=1))
        else:
            print('INTAKE INVALID:\n  - ' + '\n  - '.join(bad))
        return 1
    from arkitect.codes.columbus import fit
    rows = fit.fit(massing(d))
    unmet = fit.failing(rows)
    if as_json:
        print(json.dumps({'valid': True, 'slug': d['slug'],
                          'fit': [r._asdict() for r in rows],
                          'unmet': [r.rule for r in unmet]}, indent=1))
    else:
        print('INTAKE VALID: %s (%s)\n' % (d['address'], d['slug']))
        print(fit.summary(rows))
        if unmet:
            print('\nDOES NOT FIT: %s. Redesign the massing, or record the relief the designer chooses in '
                  '"relief".' % ', '.join(r.rule for r in unmet))
    return 2 if unmet else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

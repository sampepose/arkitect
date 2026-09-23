"""W4, the grouping separation, in section: what A-603 draws.

W4 is not one wall. RCO 302.2's first option separates a grouping with "two wall
assemblies, each having a fire resistance rating of one hour", and 302.2.6 makes each
dwelling unit structurally independent, with no exception for floor framing. So the
separation is TWO walls back to back, each UL U305 — 2x4 studs at 16" o.c., one 5/8" UL
Type SCX layer on each face, 4-3/4" — with their inner layers touching:

    W4A   Unit 1's, its floors and ceilings framed on it
    W4B   Units 2 / 3', theirs framed on it

9-1/2" finished, 8-1/4" stud face to stud face (lib/model/regrid.py). Nothing of either
unit touches the other's wall, so each is ordinary platform framing: a tier per story on
its own sole plate under its own top plate, with its own floor's rim NAILED to it. That
is what makes the height prescriptive — RCO Table 602.3(5) stops a 2x4 at 10'-0" between
points of lateral support, and every tier here is braced by that unit's own floor or
ceiling diaphragm.

Each wall's inner 5/8" layer runs past its own floor line on the face of that rim, so the
rated membrane is continuous from the foundation to the roof sheathing (302.2.3). The
plates close each wall's stud cavity at every floor and ceiling line (302.11 item 1.1);
with no air space between the walls no concealed space forms between them. The two walls
share only the FS strip (302.2.6 exception 1), the roof sheathing nailed to both raked
plates (exception 2) and the flashing (exception 4).

Heights in FEET above finished grade, from src/levels.py. Horizontal offsets in feet from
the joint between the two inner layers, + toward Units 2 / 3.
"""
from collections import namedtuple
from src.partywall import SEP_STUD, W4_CORE, W4_FACE, W4_STUD
from lib.units import IN, fmt, inches
from src import fireblocking, levels
from src.mirror import B1_W

PLATE = IN(1.5)              # one 2x plate
STUD = W4_STUD               # one wall's 2x4 stud row
LAYER = W4_FACE              # one 5/8" UL Type SCX layer, the unit face
CORE = W4_CORE/2.0           # one wall's inner layer; the two touch at x 0
FACE = CORE+STUD+LAYER       # a wall's finished half-thickness, 4-3/4"
FINISHED = 2*FACE            # 9-1/2"
RIM_T = IN(1.25)             # 1-1/4" LSL rim board, full joist depth, on its own wall
LISTING = 'UL DESIGN U305'
RATING = '1 HOUR'
STUD_MAX = 10.0              # RCO Table 602.3(5), 2x4, laterally unsupported height
FIREBLOCK_MAX = 10.0         # RCO 302.11 item 1.2
W5_T = IN(5.5)               # W5, a 2x6 furred chase on each unit face (A-601)

SLAB = levels.SLAB_TOP
L2_SOLE = levels.SUBFLOOR_TOP             # both units' Level 2 sole plates, on their own subfloor
L2_TOP = levels.ROOF_PLATE
DECK = levels.ridge(B1_W)                 # the deck over the walls at the ridge, nominal profile

# ---------------- the two walls ----------------
# side: -1 is W4A, Unit 1's, on the S Elm side; +1 is W4B, Units 2 / 3'.
Wall = namedtuple('Wall', 'name unit side floor bears plate joist ceiling')
WALLS = (Wall('W4A', 'UNIT 1', -1, 'F2', 'W1', levels.F2_PLATE, levels.F2_JOIST, levels.F2_CEILING),
         Wall('W4B', 'UNITS 2 / 3', +1, 'F1', 'W1R / W3', levels.F1_PLATE, levels.F1_JOIST, levels.F1_CEILING))
PLATE_STEP = levels.F1_PLATE - levels.F2_PLATE

Tier = namedtuple('Tier', 'name z0 z1 plates')


def tiers(w):
    """The three platform-framed tiers of one wall, each between its own lines of lateral
       support: its slab, its floor diaphragm, its ceiling diaphragm, the roof deck."""
    return (Tier('LEVEL 1', SLAB, w.plate, 'SOLE PLATE, DOUBLE TOP PLATE'),
            Tier('LEVEL 2', L2_SOLE, L2_TOP, 'SOLE PLATE, DOUBLE TOP PLATE'),
            Tier('ATTIC', L2_TOP, DECK, 'SOLE PLATE, RAKED DOUBLE TOP PLATE'))


def fireblocks(w):
    """Solid wood across this wall's stud space, (name, z0, z1). The floor line is its
       double top plate under its own floor and its Level 2 sole plate over it."""
    return (('BASE', SLAB, SLAB+PLATE),
            ('FLOOR LINE', w.plate-2*PLATE, L2_SOLE+PLATE),
            ('CEILING LINE', L2_TOP-2*PLATE, L2_TOP+PLATE),
            ('ROOF DECK', DECK-2*PLATE, DECK))


def rim(w):
    """(x0, x1, z0, z1) of this wall's rim board, on its own side: its inner face flush
       with the stud face, so the wall's inner layer runs up the rim's face past the
       floor and stays continuous."""
    return (w.side*CORE, w.side*(CORE+RIM_T), w.plate, w.plate+w.joist)


def unsupported(w):
    """[(tier, height)]: plates included, so the figure is never short."""
    t1, t2, t3 = tiers(w)
    return [(t1, t1.z1-t1.z0), (t2, t2.z1-t2.z0), (t3, t3.z1-t3.z0)]


def cavities(w):
    """[(below, above, height)]: this wall's stud space between consecutive fireblocks."""
    fb = fireblocks(w)
    return [(a[0], b[0], b[1]-a[2]) for a, b in zip(fb, fb[1:])]


# The fireblock tags and topics A-603 prints, by their keys in src/fireblocking.py.
A603_TAGS = ('W4_FLOOR', 'W4_CEILING', 'W5_PLATES', 'RIM')
A603_IDS = ('W4',)


def fireblock_model():
    """(FB ids by topic, tag text by key, each wall's required solid zone): the
       fireblocking model's, A-601 FB-1..FB-9. A-603 reads its tags here, never its own."""
    return fireblocking.FB, fireblocking.TAGS, fireblocking.W4_BLOCK_ZONES


def _in(v):
    s = inches(v)
    return s[2:] if s.startswith('0-') else s


def w4_violations(walls=None, fb=None, finished=None):
    """Every way the separation leaves the rules it is drawn to. Arguments override the
       model, so a test can ask what a change would do."""
    walls = WALLS if walls is None else walls
    ids, tags, zones = fb if fb is not None else fireblock_model()
    v = []
    if abs((FINISHED if finished is None else finished) - (SEP_STUD+2*W4_FACE)) > 1e-9:
        v.append('W4: the two walls finish %s, against the %s the plans are drawn to'
                 % (_in(FINISHED if finished is None else finished), _in(SEP_STUD+2*W4_FACE)))
    for w in walls:
        for t, h in unsupported(w):
            if h > STUD_MAX+1e-9:
                v.append('%s %s: %s between lateral supports, past the %s of RCO Table 602.3(5)'
                         % (w.name, t.name, fmt(h), fmt(STUD_MAX)))
        x0, x1, _z0, _z1 = rim(w)
        if min(x0*w.side, x1*w.side) < CORE-1e-9:
            v.append('%s: its rim crosses into the other unit\'s wall, RCO 302.2.6' % w.name)
        fl = [f for f in fireblocks(w) if f[0] == 'FLOOR LINE']
        if not any(f[1] <= w.ceiling+1e-9 and f[2] >= levels.SUBFLOOR_TOP-1e-9 for f in fl):
            v.append('%s: no fireblock spans its %s floor-ceiling, %s to %s, RCO 302.11'
                     % (w.name, w.floor, fmt(w.ceiling), fmt(levels.SUBFLOOR_TOP)))
        if not any(f[1] <= levels.UPPER_CEILING+1e-9 and f[2] >= L2_TOP-1e-9
                   for f in fireblocks(w) if f[0] == 'CEILING LINE'):
            v.append('%s: no fireblock at its Level 2 ceiling line, RCO 302.11' % w.name)
        for a, b, h in cavities(w):
            if h > FIREBLOCK_MAX+1e-9:
                v.append('%s: %s of stud space between the %s and %s fireblocks, past RCO 302.11\'s %s'
                         % (w.name, fmt(h), a, b, fmt(FIREBLOCK_MAX)))
        if w.name not in zones:
            v.append('%s: the fireblocking model defines no solid zone for it' % w.name)
        else:
            lo, hi = zones[w.name]
            if not any(f[1] <= lo+1e-9 and f[2] >= hi-1e-9 for f in fl):
                v.append('%s: its floor line does not cover the fireblocking model\'s solid zone %s to %s'
                         % (w.name, fmt(lo), fmt(hi)))
    for k in A603_TAGS:
        if k not in tags:
            v.append('W4: A-603 prints fireblock tag %s, which the fireblocking model does not define' % k)
    for k in A603_IDS:
        if k not in ids:
            v.append('W4: A-603 cites fireblock topic %s, which the fireblocking model does not define' % k)
    return v


def check_w4():
    print('W4 SEPARATION — %s AND %s, TWO %s WALLS BACK TO BACK, %s EACH, %s FINISHED; RCO 302.2 AND 302.2.6; PLATES STEP %s'
          % (WALLS[0].name, WALLS[1].name, LISTING, RATING, _in(FINISHED), _in(PLATE_STEP)))
    for w in WALLS:
        print('   %-4s %-11s carries %s, rim on its own plate %s; tiers %s'
              % (w.name, w.unit, w.floor, fmt(w.plate),
                 ', '.join('%s %s' % (t.name.split()[-1], fmt(h)) for t, h in unsupported(w))))
    bad = w4_violations()
    assert not bad, 'W4 separation:\n  ' + '\n  '.join(bad)

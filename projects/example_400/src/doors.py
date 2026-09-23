"""Every door leaf on the set against what stands on the floor it swings over.

The geometry is `arkitect/lib/model/fit.py`'s (`leaf_quadrant`, `door_swing_violations`); this module
only hands it the set's own doors and furniture, in the coordinates the PLANS draw them in.
That is the point: a swing that clears in model feet can foul once the stud grid has stretched
a band, and a check reading the authored numbers would not see it.

It was written after the mechanical / laundry pair in Units 2 and 3 was found swinging into
its own room, over the washer that stands across the last 9-1/2" of the opening (2026-09-21).
A working space is left out of the obstructions: NEC 110.26 and RCO M1305.1 are about reaching
equipment, and an open door is not what they bar.
"""
from arkitect.lib.model import fit
from arkitect.lib.model.mirror import mdoors, mfurn
from src import building1, building2

SKIP = ('clear',)              # any kind whose name carries this is a working space, not an object


def _leaves(name, plan, doors, W):
    out = []
    for d in mdoors([plan.span(x) for x in doors], W):
        x, y, ln, o, sw = d[0], d[1], d[2], d[3], d[4]
        leaf = fit.leaf_quadrant(x, y, ln, o, sw, 'far' in d[5:])
        out.append(leaf._replace(name='%s: the leaf at %s %s' % (name, _at(x, y), o)))
    return out


def _at(x, y):
    return '(%.2f, %.2f)' % (x, y)


def _obstructions(name, plan, furn, W):
    return [fit.Obstruction('%s: the %s' % (name, str(f[4]).upper()),
                            f[0], f[1], f[0]+f[2], f[1]+f[3])
            for f in mfurn([plan.keep(x) for x in furn], W, on=True)
            if not any(s in str(f[4]) for s in SKIP)]


def _levels():
    """(label, plan, doors, furn, W) for every plan the set draws."""
    for lv in (1, 2):
        m = building1.LEVEL[lv]
        yield ('UNIT 1 LEVEL %d' % lv, m['plan'], m['doors'], m['furn'], building1.B1_W)
    for lv, unit in ((1, 2), (2, 3)):
        yield ('UNIT %d' % unit, building2.PLAN_B2, building2.B2doors,
               building2.F_B2, building2.B2_W)


def swing_violations():
    v = []
    for name, plan, doors, furn, W in _levels():
        v += fit.door_swing_violations(_leaves(name, plan, doors, W),
                                       _obstructions(name, plan, furn, W))
    return v


def check_door_swings():
    """Prints one line; fails the build on a leaf that cannot open."""
    v = swing_violations()
    assert not v, '; '.join(v)
    n = sum(len(_leaves(name, plan, doors, W)) for name, plan, doors, furn, W in _levels())
    print('DOOR SWINGS  %d leaves on %d plans, each clear of everything standing in its arc'
          % (n, len(list(_levels()))))

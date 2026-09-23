"""An under-slab drainage system as a graph: stacks, slab penetrations and runs in a building,
and the questions every check and every sheet asks of it — what a penetration drains, which
runs feed a run, what a run carries, where it discharges, which run is the building drain.

Records and accessors only. Fixture units, sizes and slopes are the plumbing code's
(codes/ohio/opc_drainage.py); where the pipes ARE is the project's.
"""
from collections import namedtuple
from lib.model.runs import on_path as _on_path, same_point as _same


# A stack in its wall: `serves` are its branch intervals as (unit, level, kinds); `foot`
# is the mark of the penetration where it comes through the slab, or None for a stack
# that is a vent only.
Stack = namedtuple('Stack', 'name pos size serves foot')


# A hole through the slab: kind 'stack' (a stack's foot; `serves` is the stack's name),
# 'wc' (a closet flange), 'tub' (a trap in a box-out; `box` is the box), 'drop' (a sink
# or standpipe drain dropping below the slab), 'co' (a floor cleanout), 'exit' (the
# building drain through the foundation wall). For a fixture penetration `serves` is
# ((unit, level, kinds),).
Pen = namedtuple('Pen', 'mark kind pos size serves box')


# A horizontal drain below the slab, head to tail; the tail lies on another run or at
# the exit.
Run = namedtuple('Run', 'size path')


# `site` is where C-101 draws the building, so an exit maps onto the site plan.
Building = namedtuple('Building', 'name number W D stacks pens runs site')


def _strip_rect(s):
    x0, y0, x1, y1, _nm = s
    return (x0, y0, x1-x0, y1-y0)


def fixture(pb, unit, level, kind):
    """The one fixture of that kind on that level of that unit, or None."""
    for u in pb.units:
        if u.name == unit and u.level == level:
            fs = [f for f in u.fixtures if f.kind == kind]
            return fs[0] if len(fs) == 1 else None
    return None


def _need(pb, unit, level, kind):
    f = fixture(pb, unit, level, kind)
    assert f is not None, '%s level %d has no single %s' % (unit, level, kind)
    return f


def _cy(f):
    return f.y+f.h/2.0


def stack_by_name(b, name):
    for s in b.stacks:
        if s.name == name: return s
    raise KeyError(name)


def pen_kinds(b, pen):
    """Every fixture kind a penetration drains, the stack's included."""
    if pen.kind == 'stack': return [k for _u, _l, kinds in stack_by_name(b, pen.serves).serves for k in kinds]
    if pen.kind in ('co', 'exit'): return []
    return [k for _u, _l, kinds in pen.serves for k in kinds]


def exit_pen(b):
    ex = [p for p in b.pens if p.kind == 'exit']
    return ex[0] if len(ex) == 1 else None


def pens_on(b, run):
    """The penetrations a run carries: on its path, not at its tail."""
    return [p for p in b.pens if p.kind != 'exit' and _on_path(p.pos, run.path) and not _same(p.pos, run.path[-1])]


def feeds(b, run):
    """The runs whose tails are on this run's path, not at its tail."""
    return [r for r in b.runs if r is not run and _on_path(r.path[-1], run.path) and not _same(r.path[-1], run.path[-1])]


def pen_serves(b, pen):
    """The (unit, level, kinds) a penetration drains, the stack's intervals included."""
    if pen.kind == 'stack': return tuple(stack_by_name(b, pen.serves).serves)
    if pen.kind in ('co', 'exit'): return ()
    return tuple(pen.serves)


def run_serves(b, run):
    return [x for p in pens_on(b, run) for x in pen_serves(b, p)]+[x for r in feeds(b, run) for x in run_serves(b, r)]


def run_kinds(b, run):
    return [k for p in pens_on(b, run) for k in pen_kinds(b, p)]+[k for r in feeds(b, run) for k in run_kinds(b, r)]


def receiver(b, run):
    """The run this one's tail is on, or 'exit', or None / 'ambiguous'."""
    ex = exit_pen(b)
    at = [r for r in b.runs if r is not run and _on_path(run.path[-1], r.path) and not _same(run.path[-1], r.path[-1])]
    if ex is not None and _same(run.path[-1], ex.pos): at.append('exit')
    if len(at) == 1: return at[0]
    return None if not at else 'ambiguous'


def exit_run(b):
    ex = exit_pen(b)
    rs = [r for r in b.runs if ex is not None and _same(r.path[-1], ex.pos)]
    return rs[0] if len(rs) == 1 else None


def exit_site(b):
    """The exit on C-101's site plan, in site feet."""
    ex = exit_pen(b)
    return (b.site[0]+ex.pos[0], b.site[1]+ex.pos[1])


def _nominal(size):
    """A water pipe's nominal size in inches: '3/4' 0.75, '1-1/4' 1.25."""
    n = 0.0
    for part in size.split('-'):
        a, _, d = part.partition('/')
        n += float(a)/float(d) if d else float(a)
    return n


def _to_site(b, p):
    return (b.site[0]+p[0], b.site[1]+p[1])


def drain_name(b, run):
    if run is exit_run(b): return 'BUILDING DRAIN'
    head = [p for p in b.pens if p.kind == 'stack' and _same(p.pos, run.path[0])]
    return 'STACK %s BRANCH' % head[0].serves if head else 'BRANCH'

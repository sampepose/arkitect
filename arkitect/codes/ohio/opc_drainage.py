"""The Ohio Plumbing Code's sanitary drainage tables: Table 709.1 (drainage fixture units
and trap sizes), 704.1 (slope by size) and Tables 710.1(1) and 710.1(2) (what a building
drain, a horizontal branch and a stack may carry), with the footnote on water closets.

One transcription for every project, pinned by arkitect/codes/verify/test_drainage_tables.py. The
rows are the ones a dwelling uses; a project with another fixture adds its row HERE.
"""
from arkitect.lib.units import IN
from arkitect.lib.model.runs import along, length, same_point
from arkitect.lib.model.drains import exit_run, feeds, receiver, run_serves, stack_by_name

# ================================ the tables ================================
# Table 709.1, DRAINAGE FIXTURE UNITS FOR FIXTURES AND GROUPS: the rows this project
# has. Transcribed from the table's text and pinned by arkitect/codes/verify/test_drainage_tables.py;
# never retype them from a summary. A dishwasher discharges through the kitchen sink's
# trap arm and is in the sink's row ("with food waste grinder and/or dishwasher").
DFU = {
    'wc':   3,     # water closet, private, 1.6 gpf
    'lav':  1,     # lavatory
    'tub':  2,     # bathtub, with or without overhead shower
    'shower': 2,   # shower, 5.7 gpm or less
    'sink': 2,     # kitchen sink, domestic, with or without dishwasher
    'wd':   2,     # automatic clothes washer, residential
}
BATH_GROUP = 5                     # bathroom group as defined in Section 202, 1.6 gpf water closet
GROUP = ('wc', 'lav', 'tub')       # what makes a group; a shower stands for the tub
DRAIN_KINDS = tuple(DFU)           # what drains; 'dw' rides on the sink
# minimum trap sizes, Table 709.1, inches
TRAP = {'wc': '3', 'lav': '1-1/4', 'tub': '1-1/2', 'shower': '2', 'sink': '1-1/2', 'wd': '2'}

SIZES = ('1-1/2', '2', '3', '4')
SIZE_IN = {'1-1/2': 1.5, '2': 2.0, '3': 3.0, '4': 4.0}
# 704.1: 2-1/2" and smaller at 1/4" per foot, 3" to 6" at 1/8". Inches per foot.
SLOPE = {'1-1/2': 0.25, '2': 0.25, '3': 0.125, '4': 0.125}
SLOPES = (1/16.0, 1/8.0, 1/4.0, 1/2.0)          # Table 710.1(1)'s columns
# Table 710.1(1), BUILDING DRAINS AND SEWERS: maximum DFU at each slope, or None where
# the table gives no value at that slope.
T710_1_1 = {
    '1-1/2': (None, None, 3, 3),
    '2':     (None, None, 21, 26),
    '3':     (None, 36, 42, 50),
    '4':     (None, 180, 216, 250),
}
# Table 710.1(2), HORIZONTAL FIXTURE BRANCHES AND STACKS: (total for a horizontal
# branch, total discharge into one branch interval, total for a stack of three branch
# intervals or less, total for a stack greater than three branch intervals).
T710_1_2 = {
    '1-1/2': (3, 2, 4, 8),
    '2':     (6, 6, 10, 24),
    '3':     (20, 20, 48, 72),
    '4':     (160, 90, 240, 500),
}
# the footnote to the 3" rows: not more than two water closets or bathroom groups
# within each branch interval nor more than six on the stack
WC_PER_INTERVAL_3, WC_PER_STACK_3 = 2, 6
WC_MIN = '3'                      # no drain carrying a water closet is smaller


# ---------------- inverts ----------------
# Every invert follows from ONE figure a project states: the cover over the top of the highest
# pipe below the slab. Feet below slab top, negative.
def slope_of(run):
    return SLOPE[run.size]


def fall(run):
    """Feet of fall along a run at its slope."""
    return slope_of(run)/12.0*length(run.path)


def head_invert(b, run, _memo=None, *, cover):
    """The run's invert at its head, FEET below slab top (negative): `cover` over its own
       top, or lower where a run ends at its head and the crowns must line up."""
    memo = _memo if _memo is not None else {}
    key = id(run)
    if key in memo: return memo[key]
    inv = -(cover+IN(SIZE_IN[run.size]))
    for r in feeds(b, run):
        if same_point(r.path[-1], run.path[0]):
            inv = min(inv, tail_invert(b, r, memo, cover=cover)-max(0.0, IN(SIZE_IN[run.size])-IN(SIZE_IN[r.size])))
    memo[key] = inv
    return inv


def tail_invert(b, run, _memo=None, *, cover):
    return head_invert(b, run, _memo, cover=cover)-fall(run)


def invert_at(b, run, p, _memo=None, *, cover):
    return head_invert(b, run, _memo, cover=cover)-slope_of(run)/12.0*along(run.path, p)


def exit_invert(b, *, cover):
    """Feet below slab top at the exit."""
    r = exit_run(b)
    return tail_invert(b, r, cover=cover) if r is not None else None


def _g(k):
    """A shower makes a bathroom group as a bathtub does, and carries the same 2 DFU."""
    return 'tub' if k == 'shower' else k


def interval_dfu(kinds):
    """The load of one set of fixtures on one level: the group value when a water
       closet, a lavatory and a bathtub or shower are all in it, the fixtures singly
       otherwise."""
    ks = [_g(k) for k in kinds]
    total = 0
    if all(k in ks for k in GROUP):
        total += BATH_GROUP
        for k in GROUP: ks.remove(k)
    return total+sum(DFU[k] for k in ks)


def stack_dfu(s):
    return sum(interval_dfu(kinds) for _u, _l, kinds in s.serves)


def pen_dfu(b, pen):
    if pen.kind == 'stack': return stack_dfu(stack_by_name(b, pen.serves))
    if pen.kind in ('co', 'exit'): return 0
    return sum(interval_dfu(kinds) for _u, _l, kinds in pen.serves)


def load_dfu(serves):
    """What a pipe carries: its fixtures gathered by dwelling and level first, so a
       bathroom split between a stack and slab branches is one group again wherever a
       pipe carries all of it, and singly where it carries part. The same rule as
       unit_dfu, so a building drain carries exactly its building's tally."""
    by = {}
    for unit, level, kinds in serves: by.setdefault((unit, level), []).extend(_g(k) for k in kinds)
    total = 0
    for ks in by.values():
        groups = min(ks.count(k) for k in GROUP)
        total += BATH_GROUP*groups+sum(DFU[k]*(ks.count(k)-(groups if k in GROUP else 0)) for k in set(ks))
    return total


def run_dfu(b, run):
    return load_dfu(run_serves(b, run))


def unit_dfu(pb, name):
    """(total, rows) for one dwelling of a water-model building `pb` across its levels, by groups where it has them:
       rows are (label, count, dfu). The table on the sheet."""
    fx = [f for u in pb.units if u.name == name for f in u.fixtures if f.kind in DRAIN_KINDS]
    has_dw = any(f.kind == 'dw' for u in pb.units if u.name == name for f in u.fixtures)
    n = {}
    for f in fx: n[_g(f.kind)] = n.get(_g(f.kind), 0)+1
    groups = min(n.get(k, 0) for k in GROUP)
    rows = []
    if groups:
        rows.append(('BATHROOM GROUP, 1.6 GPF WC', groups, BATH_GROUP*groups))
        for k in GROUP: n[k] -= groups
    labels = (('wc', 'WATER CLOSET, PRIVATE, 1.6 GPF'), ('lav', 'LAVATORY'), ('tub', 'BATHTUB'),
              ('sink', 'KITCHEN SINK WITH DISHWASHER' if has_dw else 'KITCHEN SINK, DOMESTIC'),
              ('wd', 'CLOTHES WASHER, RESIDENTIAL'))
    for k, label in labels:
        if n.get(k, 0): rows.append((label, n[k], DFU[k]*n[k]))
    return sum(r[2] for r in rows), rows


# ---------------- 406.2, where a clothes washer's drain may go ----------------
# OPC 406.2 (IPC 2021 Chapter 4, which OAC 4101:3-4-01 eff. 10-15-2025 adopts with no change
# to Section 406): "The trap and fixture drain for an automatic clothes washer standpipe shall
# be not less than 2 inches (51 mm) in diameter. The fixture drain for the standpipe serving an
# automatic clothes washer shall connect to a 3-inch (76 mm) or larger diameter fixture branch
# or stack." A stack that Table 913.4 lets carry a washer at 2" is still too small to take it:
# 406.2 governs what the washer drains INTO, 913 what the stack vents.
WASHER_DRAIN_MIN = '2'
WASHER_RECEIVER_MIN = '3'
WASHER_SECTION = 'OPC 406.2'


def washer_connections(buildings):
    """Every clothes washer's fixture drain and what it connects to, from a drain model:
       (building, unit, level, the fixture drain's size, what receives it, that one's size).
       A washer on a stack drains into the stack; one dropping through the slab drains into
       the run its own fixture drain lands on."""
    out = []
    for b in buildings:
        for s in b.stacks:
            for u, l, ks in s.serves:
                out += [(b.name, u, l, TRAP['wd'], 'stack %s' % s.name, s.size) for k in ks if k == 'wd']
        for p in b.pens:
            if p.kind in ('stack', 'exit'):
                continue
            for u, l, ks in p.serves:
                if 'wd' not in ks:
                    continue
                own = [r for r in b.runs if same_point(r.path[0], p.pos)]
                rec = receiver(b, own[0]) if len(own) == 1 else None
                out.append((b.name, u, l, own[0].size if len(own) == 1 else None,
                            'the %s" drain it joins' % rec.size if hasattr(rec, 'size') else str(rec),
                            rec.size if hasattr(rec, 'size') else None))
    return out


def washer_violations(buildings, drain_min=WASHER_DRAIN_MIN, receiver_min=WASHER_RECEIVER_MIN):
    """406.2 on every clothes washer in a drain model."""
    v = []
    for bn, u, l, own, into, size in washer_connections(buildings):
        who = '%s: %s Level %d washer' % (bn, u, l)
        if own is None or SIZES.index(own) < SIZES.index(drain_min):
            v.append('%s: its fixture drain is %s", under the %s" %s asks' % (who, own, drain_min, WASHER_SECTION))
        if size is None or SIZES.index(size) < SIZES.index(receiver_min):
            v.append('%s connects to %s, %s" -- %s asks a %s" or larger branch or stack'
                     % (who, into, size, WASHER_SECTION, receiver_min))
    return v

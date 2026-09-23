"""Venting, OPC Chapter 9 (the Ohio Plumbing Code's text of the IPC): what a vent has to
reach before it joins anything, how far a trap may sit from it, and the two arrangements
that let one pipe vent more than one fixture.

The rules a set of drawings can get wrong quietly, which is why they are here:

  * 905.4 -- every DRY vent rises to not less than 6" above the flood level rim of the
    highest trap or trapped fixture it vents, before it runs horizontally or joins another
    vent. A pipe that carries drainage from above the point where a lower fixture's vent
    meets it is not that fixture's vent; it is a drain past its opening.
  * Table 909.1 -- the trap arm: how far a trap may stand from its vent, by trap size.
  * 909.2 -- the vent connection is not below the weir of the trap it vents, water closets
    excepted, and a fixture drain falls no further than its own diameter reaching it. A
    lavatory that stands on a floor and drops into a branch WITHIN that floor is vented from
    two feet under its weir, and the trap arm check cannot see it: a drop is not a horizontal
    run, so its plan length passes Table 909.1 with room to spare.
  * 912 -- wet venting is "any combination of fixtures within two bathroom groups located
    on the SAME FLOOR LEVEL". It does not reach between stories.
  * 913 -- a waste stack may be the vent for everything on it (the arrangement that DOES
    serve several floors), but it takes no water closet and no urinal, and no offset
    between its lowest and highest fixture connection.
  * 903.2, frost closure -- where the 97.5-percent outdoor design temperature is 0 F or
    less, a vent through a roof or wall is not less than 3", and the INCREASE is made not
    less than 1 ft inside the thermal envelope, where the pipe is still warm. A 2" stack
    labelled 2" at the roof in that climate is either undersized or silently increased
    somewhere nobody drew.

So a lower floor's fixtures, on a stack that carries a water closet above them, keep their
own dry vent up to 905.4's height. `stack_vent_violations()` is that sentence as a check.
"""
from collections import namedtuple

from codes.ohio.opc_drainage import SIZE_IN, WC_MIN

SECTION = 'OPC 905.4'
DRY_VENT_RISE = 0.5              # ft: 6" above the flood level rim, 905.4

# 903.2, frost closure. The trigger is a design temperature, so a project states its own.
FROST_CLOSURE_F = 0              # the 97.5-percent outdoor design temperature, F, at or under
FROST_CLOSURE_SIZE = '3'         # which a roof or wall vent is at least this nominal size
INCREASE_INSIDE = 1.0            # ft: the increase is made this far inside the thermal envelope
WET_VENT_SAME_FLOOR = True       # 912: two bathroom groups, one floor level
WASTE_STACK_TAKES_WC = False     # 913: no water closet on a waste stack vent

# Table 909.1, the trap arm: trap size (in) -> (slope in/ft, maximum developed length ft).
# 1-1/4 and 1-1/2 fall at 1/4 in/ft, 3 and 4 at 1/8.
TRAP_ARM = {1.25: (0.25, 5.0), 1.5: (0.25, 6.0), 2.0: (0.25, 8.0), 3.0: (0.125, 12.0), 4.0: (0.125, 16.0)}

# What a fixture's flood level rim stands above its floor, for 905.4. A standpipe's rim is
# its own top, not the washer's; OPC 802.4 puts that between 18" and 42".
FLOOD_RIM = {'wc': 15.0/12, 'tub': 20.0/12, 'shower': 20.0/12, 'lav': 31.0/12,
             'sink': 36.0/12, 'wd': 42.0/12}

Arm = namedtuple('Arm', 'name size length')          # inches, feet

# 909.2, Venting of fixture drains, both clauses: "The total fall in a fixture drain due to
# pipe slope shall not exceed the diameter of the fixture drain, nor shall the vent
# connection to a fixture drain, except for water closets, be below the weir of the trap."
# They work together and the pair is one limit: the fall from the trap's weir DOWN to the
# vent connection may not exceed that drain's own diameter, which is what keeps the vent's
# opening above the water the trap holds. Table 909.1 is built to it -- every row's slope
# times its maximum length lands at or under the trap's size, which `table_909_1_fall()`
# states -- so an arm inside the table satisfies 909.2 by itself.
#
# What does NOT is a DROP. A fixture standing on one floor whose drain falls into a branch
# in the floor below it has its vent connection a whole floor under its weir, and no length
# check can see that, because the drop is not a horizontal run: `trap_arm_violations()`
# measures the plan distance and passes it. A wet vent is a vent, so this reaches a
# wet-vented fixture too -- 912 says which pipe is the vent, never that it may be below the
# weir of a trap it vents.
FIXTURE_DRAIN_SECTION = 'OPC 909.2'
WEIR_EXEMPT = ('wc',)                # 909.2: "except for water closets"

# What a fixture's trap WEIR stands above the floor its fixture sits on, feet -- for the
# fixtures whose trap stands ABOVE that floor, where the height is the fixture's own rough-in
# and a drain reaching a branch below the floor has to fall the whole floor to get there.
# A tub, a shower and a water closet have NO entry on purpose: their trap or closet bend
# hangs IN the floor structure and is set to the pipe it drains to, so the fall is the trap's
# own and not a datum a drawing can get wrong. `weir_violations()` says which it skipped.
TRAP_WEIR = {'lav': 18.0/12, 'sink': 18.0/12, 'wd': 18.0/12}

# A trapped fixture against 909.2: `weir` and `vent_at` are heights in FEET on one datum,
# positive up, and `size` is the fixture drain in inches, as Table 909.1 keys it.
Weir = namedtuple('Weir', 'name kind size weir vent_at')


def table_909_1_fall(size_in):
    """The fall a trap arm of this size takes at Table 909.1's slope over its maximum length.
       It is at or under the trap's own size on every row, which is why an arm inside the
       table needs no separate 909.2 fall check."""
    slope, length = TRAP_ARM[size_in]
    return slope*length


def weir_fall_max(size_in):
    """909.2: the most a fixture drain may fall from its trap's weir to its vent connection --
       the drain's own diameter, in feet."""
    return size_in/12.0


def weir_violations(weirs, exempt=WEIR_EXEMPT):
    """909.2 on each trapped fixture whose trap stands above its floor: the vent connection
       may not lie more than the drain's diameter below the trap's weir. Water closets are
       excepted by the section itself, and a fixture whose kind is not in TRAP_WEIR has its
       trap set to the pipe (see there) and is not measured here."""
    v = []
    for w in weirs:
        if w.kind in exempt or w.kind not in TRAP_WEIR:
            continue
        drop = w.weir-w.vent_at
        lim = weir_fall_max(w.size)
        if drop > lim+1e-9:
            v.append('%s: its vent connects %.2f ft under the weir of its trap, over the %g" '
                     'the drain itself is; %s wants the vent above the weir'
                     % (w.name, drop, w.size, FIXTURE_DRAIN_SECTION))
    return v


def frost_closure(design_f, temp=FROST_CLOSURE_F):
    """Does OPC 903.2 bind at this outdoor design temperature?"""
    return design_f <= temp


def roof_size(size, design_f, least=FROST_CLOSURE_SIZE, temp=FROST_CLOSURE_F, order=('1-1/4', '1-1/2', '2', '3', '4')):
    """The nominal size a vent takes where it goes through the roof, OPC 903.2."""
    if not frost_closure(design_f, temp):
        return size
    assert size in order and least in order, 'vent size %r is not one this rule knows' % (size,)
    return size if order.index(size) >= order.index(least) else least


def roof_vents(buildings, ties, design_f, least=FROST_CLOSURE_SIZE, temp=FROST_CLOSURE_F):
    """What goes through a roof, as (mark, size at the roof, size of the pipe below): one
       penetration per stack, less any stack `ties` records as joining another in the attic.
       A project states its own ties; the sizes come back from 903.2."""
    return [('%s stack %s' % (b.name, st.name), roof_size(st.size, design_f, least, temp), st.size)
            for b in buildings for st in b.stacks if st.name not in ties]


def roof_vent_violations(vents, design_f, least=FROST_CLOSURE_SIZE, temp=FROST_CLOSURE_F):
    """`vents` is (mark, size at the roof as drawn, size of the pipe below). Every vent
       that reaches a roof is at least `least` where 903.2 binds."""
    v = []
    for mark, at_roof, below in vents:
        want = roof_size(below, design_f, least, temp)
        if at_roof != want:
            v.append('%s goes through the roof at %s" on a %s" pipe, not the %s" OPC 903.2 asks '
                     'at a %d F design temperature' % (mark, at_roof, below, want, design_f))
    return v


def trap_arm_max(size_in):
    """Table 909.1's maximum developed length for a trap of this size."""
    for s in sorted(TRAP_ARM):
        if abs(s-size_in) < 1e-9:
            return TRAP_ARM[s][1]
    raise KeyError('no Table 909.1 row for a %g" trap' % size_in)


def trap_arm_violations(arms):
    """Each Arm against Table 909.1."""
    v = []
    for a in arms:
        lim = trap_arm_max(a.size)
        if a.length > lim+1e-9:
            v.append('%s: its trap arm runs %.1f ft, over Table 909.1\'s %.0f ft for a %g" trap'
                     % (a.name, a.length, lim, a.size))
    return v


def dry_vent_rise_violations(vents):
    """905.4 on each dry vent: (name, the height it turns or joins at, the highest flood
       level rim it vents), all measured from the same datum, in feet."""
    v = []
    for name, tie_z, rim_z in vents:
        if tie_z < rim_z+DRY_VENT_RISE-1e-9:
            v.append('%s: its vent turns %.2f ft over the flood rim it vents, under %s\'s %g"'
                     % (name, tie_z-rim_z, SECTION, DRY_VENT_RISE*12))
    return v


def stack_vent_violations(stacks, claimed_913=()):
    """The rule the two arrangements leave: a stack that carries drainage from a level ABOVE
       a fixture cannot be that fixture's vent. Each stack is
       (name, carries_water_closet, [(fixture name, its level)], [(vented fixture, its level)]).
       A fixture vented by the stack passes only where nothing drains into it from higher up
       -- 912's wet vent is one floor, and 913's waste stack vent takes no water closet.

       `claimed_913` names the stacks a set claims as waste stack vents, which DO vent every
       fixture on them; pass them here and `waste_stack_violations()` the same names, so
       that dropping the claim brings this rule back."""
    v = []
    for name, wc, drains, vented in stacks:
        if name in claimed_913:
            continue
        for fx, lv in vented:
            above = [d for d, dl in drains if dl > lv]
            if not above:
                continue
            if wc:
                v.append('%s: %s is vented by a stack that drains %s from above it; 912 wet vents '
                         'one floor and 913 takes no water closet' % (name, fx, ', '.join(above)))
            else:
                v.append('%s: %s is vented by a stack that drains %s from above it; only a 913 '
                         'waste stack vent may do that, and its conditions are not stated'
                         % (name, fx, ', '.join(above)))
    return v


# ---------------- 913, the waste stack vent ----------------
# The one arrangement that vents fixtures on SEVERAL floors from one pipe: 913.1 makes the
# waste stack itself their vent. It is not free. 913.2 forbids any offset, horizontal or
# vertical, between the lowest and the highest fixture drain connection; the stack takes no
# water closet and no urinal; 913.3 carries a stack vent of the stack's own size through the
# roof; and Table 913.4 caps the load. Claim it on a sheet or do not rely on it -- an
# unstated claim is the defect, not the arrangement.
# Table 913.4: stack size (in) -> (DFU at ONE branch interval, DFU total on the stack).
WASTE_STACK = {1.5: (1, 2), 2.0: (2, 4), 2.5: (None, 8), 3.0: (None, 24),
               4.0: (None, 50), 5.0: (None, 75), 6.0: (None, 100)}
WASTE_STACK_SECTION = 'OPC 913'


def waste_stack_text(stacks):
    """The sentence a sheet prints to show each waste stack vent inside Table 913.4 --
       the claim 913 asks for, in the figures the model measures. `stacks` is what
       `waste_stack_violations()` takes."""
    out = []
    for name, size, _wc, by_interval, total, _offset in stacks:
        per, cap = WASTE_STACK[size]
        out.append('%s %g" CARRIES %d DFU AT A BRANCH INTERVAL OF %s AND %d IN ALL OF %d'
                   % (name, size, max(by_interval), 'NO LIMIT' if per is None else str(per),
                      total, cap))
    return '; '.join(out)


def waste_stack_violations(stacks):
    """913 on every stack a set claims as a waste stack vent. Each stack is
         (name, size in inches, takes a water closet, [DFU at each branch interval],
          total DFU, offset between the lowest and highest fixture connection)."""
    v = []
    for name, size, wc, by_interval, total, offset in stacks:
        if size not in WASTE_STACK:
            v.append('%s: no Table 913.4 row for a %g" stack' % (name, size))
            continue
        per, cap = WASTE_STACK[size]
        if wc:
            v.append('%s: a waste stack vent takes no water closet, %s' % (name, WASTE_STACK_SECTION))
        if offset:
            v.append('%s: 913.2 forbids an offset between its lowest and highest fixture connection' % name)
        if per is not None and by_interval and max(by_interval) > per:
            v.append("%s: %d DFU at one branch interval, over Table 913.4's %d for a %g\" stack"
                     % (name, max(by_interval), per, size))
        if total > cap:
            v.append("%s: %d DFU in all, over Table 913.4's %d for a %g\" stack" % (name, total, cap, size))
    return v


# ---------------- 912, the two wet vents ----------------
# The arrangement that vents a bathroom group from its own drain. There are TWO of them
# and they are not interchangeable, which is what a riser diagram has to show:
#
#   912.1 HORIZONTAL wet vent -- the wet vent is the horizontal branch drain, and runs
#     from the dry vent's connection ALONG THE DIRECTION OF FLOW to the most downstream
#     fixture drain connection. Each wet-vented fixture drain connects independently to
#     it; only fixtures of the bathroom groups connect to it; any additional fixture
#     discharges downstream of it. 912.2.1: the dry vent is an individual or common vent
#     for any bathroom group fixture (where it connects to a water closet's drain, that
#     drain connects horizontally), and NOT MORE THAN ONE wet-vented fixture drain may
#     discharge upstream of the dry-vented fixture's connection.
#
#   912.1.1 VERTICAL wet vent -- the wet vent is the vertical pipe, and runs from the dry
#     vent's connection DOWN to the lowest fixture drain connection. Each wet-vented
#     fixture connects independently; the water closet drains connect at ONE elevation and
#     every other fixture drain connects at or above them. 912.2.2: the dry vent is an
#     individual or common vent for the MOST UPSTREAM fixture drain -- on a vertical wet
#     vent, the highest one. A stack carried full size above that connection IS that vent.
#
#   912.3 -- the wet vent is sized from Table 912.3 on the fixture units discharging to
#     it, and the dry vent on the largest pipe in the system it serves.
#
# Both are limited to "any combination of fixtures within two bathroom groups located on
# the same floor level", which is why neither can reach between stories and why a Level 1
# group under a stack that carries Level 2 keeps a dry vent of its own.
WET_VENT = {1.5: 1, 2.0: 4, 2.5: 6, 3.0: 12}      # Table 912.3: size (in) -> DFU to the wet vent
WET_VENT_SECTION = 'OPC 912'
BATHROOM_GROUP = ('wc', 'lav', 'tub', 'shower', 'bidet')      # Section 202, what may be on a wet vent
WC_DRAIN_MIN = SIZE_IN[WC_MIN]                    # 709.1: no drain carrying a water closet is smaller

# A fixture's connection to a wet vent. `at` is WHERE it is made, in feet: on a vertical
# wet vent the height over that level's finished floor, positive up; on a horizontal one
# the distance along the direction of flow from the head of the branch. `size` is the pipe
# the wet vent is in at that connection -- for a horizontal wet vent, the section
# immediately DOWNSTREAM of it, which is what Table 912.3 sizes.
Conn = namedtuple('Conn', 'name kind dfu at size')


def wet_vent_min_size(dfu):
    """Table 912.3: the smallest wet vent that takes this many fixture units."""
    for s in sorted(WET_VENT):
        if dfu <= WET_VENT[s]:
            return s
    raise ValueError('%d DFU is past the last row of Table 912.3' % dfu)


def _not_a_group_fixture(name, conns):
    return ['%s: %s is not a bathroom group fixture and may not be on a wet vent, %s'
            % (name, c.name, WET_VENT_SECTION) for c in conns if c.kind not in BATHROOM_GROUP]


def vertical_wet_violations(groups):
    """912.1.1 on each vertical wet vent. A group is
         (name, the pipe's size in inches, [Conn] on it, the height from which the pipe over
          it carries no drainage -- where the stack becomes the dry vent, 912.2.2)."""
    v = []
    for name, size, conns, dry_at in groups:
        if not conns:
            continue
        v += _not_a_group_fixture(name, conns)
        wcs = [c for c in conns if c.kind == 'wc']
        others = [c for c in conns if c.kind != 'wc']
        seen = {}
        for c in conns:
            key = round(c.at, 6)
            if key in seen and not (c.kind == 'wc' and seen[key] == 'wc'):
                v.append('%s: %s connects at the same elevation as another fixture; 912.1.1 wants '
                         'each one connected independently' % (name, c.name))
            seen[key] = c.kind
        if wcs:
            if len({round(c.at, 6) for c in wcs}) > 1:
                v.append('%s: its water closet drains connect at more than one elevation, 912.1.1' % name)
            wz = min(c.at for c in wcs)
            for c in others:
                if c.at < wz-1e-9:
                    v.append('%s: %s connects below the water closet drain; 912.1.1 wants every other '
                             'fixture drain at or above it' % (name, c.name))
        # 912.2.2: the dry vent serves the MOST UPSTREAM fixture drain, which on a vertical
        # wet vent is the highest. Below it, the fixtures over the connection have no vent;
        # above it, something else drains into the pipe and the pipe over the group is a
        # drain, not a vent. Either way the arrangement is not this one.
        top = max(c.at for c in conns)
        upstream = max(conns, key=lambda c: c.at).name
        if abs(dry_at-top) > 1e-9:
            v.append('%s: its dry vent connects %s %s, the most upstream fixture drain; 912.2.2 '
                     'wants it AT that drain' % (name, 'over' if dry_at > top else 'below', upstream))
        total = sum(c.dfu for c in conns)
        if size not in WET_VENT:
            v.append('%s: no Table 912.3 row for a %g" wet vent' % (name, size))
        elif total > WET_VENT[size]:
            v.append('%s: a %g" vertical wet vent carries %d DFU, over Table 912.3\'s %d'
                     % (name, size, total, WET_VENT[size]))
        if wcs and size < WC_DRAIN_MIN-1e-9:
            v.append('%s: a wet vent carrying a water closet is %g", under %g"' % (name, size, WC_DRAIN_MIN))
    return v


def horizontal_wet_violations(groups):
    """912.1 / 912.2.1 on each horizontal wet vent. A group is
         (name, [Conn] IN THE DIRECTION OF FLOW, the name of the fixture the dry vent
          connects at, [(name, at)] of anything else that connects to the same branch).
       Each Conn's `size` is the branch section immediately downstream of it."""
    v = []
    for name, conns, dry_at, extras in groups:
        if not conns:
            continue
        v += _not_a_group_fixture(name, conns)
        if [c.at for c in conns] != sorted(c.at for c in conns):
            v.append('%s: its fixtures are not listed in the direction of flow' % name)
        if len({round(c.at, 6) for c in conns}) != len(conns):
            v.append('%s: two fixtures connect at one point; 912.1 wants each wet-vented fixture '
                     'drain connected independently' % name)
        names = [c.name for c in conns]
        if dry_at not in names:
            v.append('%s: its dry vent connects at %s, which is not on the branch' % (name, dry_at))
        else:
            i = names.index(dry_at)
            if i > 1:
                v.append('%s: %d fixture drains discharge upstream of %s, where the dry vent connects; '
                         '912.2.1 allows one' % (name, i, dry_at))
            if conns[i].kind == 'wc':
                v.append('%s: its dry vent connects at a water closet, %s' % (name, dry_at))
        last = max(c.at for c in conns)
        for nm, at in extras:
            if at <= last+1e-9:
                v.append('%s: %s discharges into the wet vent; 912.1 takes only the bathroom groups, '
                         'and anything else downstream of it' % (name, nm))
        carried, wc_yet = 0, False
        for c in conns:
            carried += c.dfu
            wc_yet = wc_yet or c.kind == 'wc'
            if c.size not in WET_VENT:
                v.append('%s: no Table 912.3 row for the %g" section below %s' % (name, c.size, c.name))
                continue
            if carried > WET_VENT[c.size]:
                v.append('%s: the %g" section below %s carries %d DFU, over Table 912.3\'s %d'
                         % (name, c.size, c.name, carried, WET_VENT[c.size]))
            if wc_yet and c.size < WC_DRAIN_MIN-1e-9:
                v.append('%s: the section below %s carries a water closet at %g"' % (name, c.name, c.size))
    return v

"""Required clearances, stated once, beside the kind of thing that requires them.

A clearance is a property of the EQUIPMENT, not of the sheet it happens to be drawn on.
A water closet needs its 15 inches wherever it stands; a water heater needs its 30-inch
working space in every closet in the project. Before this module those rules lived in
three different shapes and only one of them ran:

  - `lib/symbols/plumbing.py`'s WaterCloset docstring stated RCO 307.1's 15 and 21
    inches and said "those are checked in build.py, not drawn here". Nothing in build.py
    checked them. There was no constant, no assertion, and no test -- the rule existed
    only as prose, and the prose reassured the next reader that someone else had it.
  - `lib/model/dimensions.py`'s wc_dims() measured the real clearance and printed it on
    A-101 and A-102, and never compared it to the minimum it was answering.
  - `src/plumbing.py`'s check_working_spaces() did it properly for the heaters: a named
    constant, a generic check over all three cases, the one place the minimum genuinely
    cannot be met recorded as data rather than fudged, and the grid's slack named. Good
    work, built by hand, for heaters only.

So the codebase already proved the pattern both ways. This is the generalization: the
RULE lives here, keyed by the `kind` string the plan items and the symbol registry
already share, and the number a sheet prints and the number a check asserts come from
the same record.

WHY THE RULE AND NOT THE RECTANGLE. The geometry stays in the model. `lib/symbols` draws
in page points after the mirror and knows nothing of its neighbours, and the working-space
rectangles in `src/building1.py` are SOLVED against the stud grid rather than derived --
the file says so. What co-locates is the requirement; the symbol's tie to it is the kind
string it already declares.
"""
from lib.units import fmt, inches


# class Clear:: shared, see codes/clearances.py
from codes.clearances import WC_SIDE, wc_violations


def check_clearances(plans, finish):
    """From build.check_model(): every placed fixture whose kind carries a clearance
       rule keeps it, or the build stops.

       `finish` is the board on a stud face, src/finishes.py's BOARD. It is an argument
       rather than an import because the measurement it feeds is shared code: 307.1
       measures to a wall, the plans are dimensioned to stud faces, and the project is
       what knows the difference. Every pan in this set is bounded by a tub and a vanity,
       so no figure here moves by it."""
    bad, seen = wc_violations(plans, finish)
    print('CLEARANCES — %s, %s EACH SIDE OF A WATER CLOSET CENTERLINE:'
          % (WC_SIDE.citation, inches(WC_SIDE.minimum)))
    if not seen:
        print('   NO WATER CLOSET REACHED THE CHECK')
    for label, got in seen:
        print('   %-26s %s' % (label, fmt(got)))
    # Unit 1's water closets are drawn by src/sheets/plans.py in inch space and never
    # enter a furniture list, so nothing here sees them and nothing dimensions them on
    # A-101 or A-102 either. Said out loud rather than left as a silent zero.
    print('   UNIT 1 IS NOT IN THIS CHECK: its fixtures are drawn outside the model')
    assert not bad, 'CLEARANCES:\n  '+'\n  '.join(bad)


def project_plans():
    """The plan levels that carry a water closet IN THE MODEL, regridded, as the check
       wants them. Imported lazily: this module states rules and must stay importable by
       anything, including the modules it reads here."""
    from src.building1 import U23, OA_U23, F_U23, PLAN_L1
    from src.building2 import B2U, OA_B2, F_B2, PLAN_B2
    return [('BUILDING 1 UNITS 2 / 3',
             [PLAN_L1.rect(r) for r in U23], PLAN_L1.poly(OA_U23),
             [PLAN_L1.keep(f) for f in F_U23]),
            ('BUILDING 2 UNITS 4 / 5',
             [PLAN_B2.rect(r) for r in B2U], PLAN_B2.poly(OA_B2),
             [PLAN_B2.keep(f) for f in F_B2])]

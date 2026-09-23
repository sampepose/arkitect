"""Required clearances, stated once, beside the kind of thing that requires them.

A clearance is a property of the EQUIPMENT, not of the sheet it is drawn on or the lot it
stands on: a water closet needs RCO 307.1's 15 inches wherever it stands, a water heater
M1305.1's 30-inch working space in every closet, a panel NEC 110.26(A)'s 36. The RULE lives
here, keyed by the `kind` string the plan items and the symbol registry share, so the
number a sheet prints and the number a check asserts come from one record. The geometry —
which rooms, which fixtures — is the project's, handed to wc_violations().
"""
from lib.units import IN, fmt, inches


class Clear:
    """One code-required clearance: what requires it, how much, and who says so."""

    def __init__(s, kind, citation, minimum, measured, checked_by=None, note=""):
        s.kind, s.citation, s.minimum = kind, citation, minimum
        s.measured, s.checked_by, s.note = measured, checked_by, note

    def __repr__(s):
        return "<Clear %s %s %s>" % (s.kind, s.citation, inches(s.minimum))


# Keyed by the `kind` string in a plan item, which is the same key lib/symbols registers
# its drawing under. A kind with no entry has no clearance rule; a kind with one is
# checked wherever it is placed.
RULES = {
    'wc': [
        Clear('wc', 'RCO 307.1', IN(15),
              'centerline of the pan to any wall or fixture, each side',
              checked_by='check_clearances'),
        Clear('wc', 'RCO 307.1', IN(21),
              'clear in front of the bowl',
              note='NOT CHECKED HERE: the model carries no obstruction in front of a '
                   'pan, so there is nothing to measure against. A-001 note 11a states '
                   'the dimension. Naming it keeps the gap visible rather than absent.'),
    ],
    'wh': [
        Clear('wh', 'RCO M1305.1', IN(30),
              '30 x 30 at the control side, reaching the appliance',
              checked_by='src/plumbing.py check_working_spaces'),
    ],
    'panel': [
        Clear('panel', 'NEC 110.26(A)', IN(36),
              'depth from the face of the panel',
              checked_by='src/plumbing.py check_working_spaces'),
        Clear('panel', 'NEC 110.26(A)(2)', IN(30),
              'width, or the equipment, whichever is greater',
              checked_by='src/plumbing.py check_working_spaces'),
    ],
}

# The one the sheets quote. A-001 note 11a prints this rather than typing 15 again.
WC_SIDE = RULES['wc'][0]
WC_FRONT = RULES['wc'][1]


def wc_violations(plans, finish=0.0):
    """Every water closet in `plans` keeps WC_SIDE.minimum each side of its centerline.

       `plans` is (label, rects, polys, furn) per plan level. The measurement is
       wc_clearances(), which is the same one that draws the dimension on A-101 and
       A-102 -- so the figure printed on the sheet and the figure checked here cannot
       disagree, which is the whole point of doing it this way.

       `finish` is the project's wall finish thickness, passed to that measurement so
       both readers answer to a FINISHED surface. 307.1 says "wall", and a room
       rectangle in these models is a stud face; the two differ by the drywall, which
       is a quarter of the slack the rule leaves at its minimum.
    """
    from lib.model.dimensions import wc_clearances
    bad, seen = [], []
    for (label, rects, polys, furn) in plans:
        for m in wc_clearances(rects, polys, furn, finish):
            for side, got in (('one side', m['cl']-m['lo']), ('the other', m['hi']-m['cl'])):
                seen.append((label, got))
                if got < WC_SIDE.minimum - 1e-9:
                    bad.append('%s: a water closet has %s on %s, against %s of %s'
                               % (label, fmt(got), side, WC_SIDE.citation,
                                  inches(WC_SIDE.minimum)))
    return bad, seen
